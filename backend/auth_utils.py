"""Auth utilities: JWT, password hashing, session lookup, plan limits.

Supports BOTH:
  - Email/Password JWT auth
  - Emergent managed Google Auth (session_token cookie / bearer)

REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS,
THIS BREAKS THE AUTH (applies to the Emergent OAuth redirect in the frontend).
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

from db import db

JWT_SECRET = os.getenv("JWT_SECRET", "corpintel-dev-secret")
JWT_ALGO = "HS256"
JWT_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Plan limits (per spec)
PLAN_LIMITS = {
    "free": {"searches_per_day": 20, "exports_per_month": 0, "contact_data": False, "api_access": False},
    "starter": {"searches_per_day": -1, "exports_per_month": 50, "contact_data": False, "api_access": False},
    "pro": {"searches_per_day": -1, "exports_per_month": -1, "contact_data": True, "api_access": True},
    "enterprise": {"searches_per_day": -1, "exports_per_month": -1, "contact_data": True, "api_access": True},
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(password, hashed)
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "type": "jwt"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def new_user_id() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


def new_api_key() -> str:
    return f"ci_live_{uuid.uuid4().hex}"


async def _user_from_token(token: str) -> Optional[dict]:
    """Resolve a user from a JWT or an Emergent session_token."""
    if not token:
        return None
    # 1) Try JWT
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id = payload.get("sub")
        if user_id:
            user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
            if user:
                return user
    except JWTError:
        pass
    # 2) Try Emergent session token
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if session:
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at < datetime.now(timezone.utc):
            return None
        return await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return None


def _extract_token(authorization: Optional[str], session_token: Optional[str],
                   x_api_key: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if session_token:
        return session_token
    return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    # API key auth (Pro+)
    if x_api_key:
        user = await db.users.find_one({"api_key": x_api_key}, {"_id": 0})
        if user:
            return user
    token = _extract_token(authorization, session_token, x_api_key)
    user = await _user_from_token(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
    x_api_key: Optional[str] = Header(None),
) -> Optional[dict]:
    if x_api_key:
        user = await db.users.find_one({"api_key": x_api_key}, {"_id": 0})
        if user:
            return user
    token = _extract_token(authorization, session_token, x_api_key)
    if not token:
        return None
    return await _user_from_token(token)


def plan_limits(plan: str) -> dict:
    return PLAN_LIMITS.get(plan or "free", PLAN_LIMITS["free"])


async def consume_search(user: Optional[dict]) -> dict:
    """Increment a user's daily search counter, enforcing free-tier limits.

    Returns {allowed: bool, used: int, limit: int}. Anonymous users get the
    free limit tracked loosely (not blocked) for demo purposes.
    """
    if not user:
        return {"allowed": True, "used": 0, "limit": PLAN_LIMITS["free"]["searches_per_day"]}
    limits = plan_limits(user.get("plan", "free"))
    per_day = limits["searches_per_day"]
    today = datetime.now(timezone.utc).date().isoformat()
    reset = user.get("search_reset_date")
    used = user.get("searches_used", 0)
    if reset != today:
        used = 0
    if per_day != -1 and used >= per_day:
        return {"allowed": False, "used": used, "limit": per_day}
    used += 1
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"searches_used": used, "search_reset_date": today}},
    )
    return {"allowed": True, "used": used, "limit": per_day}


async def consume_export(user: dict) -> dict:
    limits = plan_limits(user.get("plan", "free"))
    per_month = limits["exports_per_month"]
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    reset = user.get("export_reset_month")
    used = user.get("exports_used", 0)
    if reset != month:
        used = 0
    if per_month == 0:
        return {"allowed": False, "used": used, "limit": 0,
                "message": "Your plan does not include exports. Upgrade to Starter or Pro."}
    if per_month != -1 and used >= per_month:
        return {"allowed": False, "used": used, "limit": per_month,
                "message": "Monthly export limit reached. Upgrade your plan."}
    used += 1
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"exports_used": used, "export_reset_month": month}},
    )
    return {"allowed": True, "used": used, "limit": per_month}
