"""Auth router: Email/Password JWT + Emergent Google Auth + demo bypass."""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Body, Cookie, Depends, Header, HTTPException, Response

from auth_utils import (create_access_token, get_current_user, hash_password,
                        new_api_key, new_user_id, verify_password)
from db import db
from models import (LoginRequest, MagicLinkRequest, RegisterRequest,
                    TokenResponse, UserPublic)

logger = logging.getLogger("corpintel.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
ALLOW_TEST_BYPASS = os.getenv("ALLOW_TEST_BYPASS", "false").lower() == "true"


def _public(user: dict) -> dict:
    return {
        "user_id": user["user_id"], "email": user["email"], "name": user.get("name", ""),
        "plan": user.get("plan", "free"), "picture": user.get("picture"),
        "searches_used": user.get("searches_used", 0),
        "exports_used": user.get("exports_used", 0),
        "api_key": user.get("api_key"), "auth_provider": user.get("auth_provider", "email"),
        "created_at": user.get("created_at"),
    }


async def _new_user(email: str, name: str, *, provider: str, password: str | None = None,
                    picture: str | None = None) -> dict:
    user = {
        "user_id": new_user_id(), "email": email.lower(), "name": name,
        "plan": "free", "searches_used": 0, "exports_used": 0,
        "saved_searches": [], "alerts": [], "auth_provider": provider,
        "picture": picture, "api_key": None,
        "created_at": datetime.now(timezone.utc),
    }
    if password:
        user["password_hash"] = hash_password(password)
    await db.users.insert_one(dict(user))
    return user


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await _new_user(payload.email, payload.name, provider="email", password=payload.password)
    token = create_access_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": _public(user)}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if not user or not user.get("password_hash") or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": _public(user)}


@router.post("/magic-link")
async def magic_link(payload: MagicLinkRequest):
    """Issue a magic-link token. No email provider wired in v1 -> token returned
    in response and logged (dev). In prod this would be emailed."""
    user = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if not user:
        user = await _new_user(payload.email, payload.email.split("@")[0], provider="magic")
    token = create_access_token(user["user_id"])
    logger.info("[magic-link] %s -> token issued", payload.email)
    return {"message": "Magic link generated (dev mode: token returned).",
            "magic_token": token, "email": payload.email}


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login():
    """Test bypass: returns a JWT for a seeded Pro demo user.

    REMOVE / disable (set ALLOW_TEST_BYPASS=false) before production.
    """
    if not ALLOW_TEST_BYPASS:
        raise HTTPException(status_code=403, detail="Demo login disabled")
    user = await db.users.find_one({"email": "demo@corpintel.in"}, {"_id": 0})
    if not user:
        user = await _new_user("demo@corpintel.in", "Demo User", provider="demo", password="Demo@1234")
        await db.users.update_one({"user_id": user["user_id"]},
                                  {"$set": {"plan": "pro", "api_key": new_api_key()}})
        user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    token = create_access_token(user["user_id"])
    return {"access_token": token, "token_type": "bearer", "user": _public(user)}


@router.post("/google/session")
async def google_session(response: Response, x_session_id: str = Header(None),
                         session_id: str = Body(None, embed=True)):
    """Exchange an Emergent Google session_id for an app session.

    Frontend sends the session_id (from URL fragment) here; backend calls the
    Emergent session-data endpoint (never the frontend).
    """
    sid = x_session_id or session_id
    if not sid:
        raise HTTPException(status_code=400, detail="Missing session_id")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": sid})
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        data = r.json()
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Auth provider error: {e}")

    email = data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="No email from provider")
    user = await db.users.find_one({"email": email.lower()}, {"_id": 0})
    if not user:
        user = await _new_user(email, data.get("name", email.split("@")[0]),
                               provider="google", picture=data.get("picture"))
    session_token = data.get("session_token") or f"sess_{uuid.uuid4().hex}"
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {"session_token": session_token, "user_id": user["user_id"],
                  "expires_at": expires, "created_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    response.set_cookie(key="session_token", value=session_token, httponly=True,
                        secure=True, samesite="none", path="/",
                        max_age=7 * 24 * 3600)
    return {"user": _public(user), "session_token": session_token}


@router.get("/me", response_model=UserPublic)
async def me(user: dict = Depends(get_current_user)):
    return _public(user)


@router.post("/logout")
async def logout(response: Response, session_token: str = Cookie(None)):
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/")
    return {"message": "logged out"}


@router.post("/api-key")
async def regenerate_api_key(user: dict = Depends(get_current_user)):
    from auth_utils import plan_limits
    if not plan_limits(user.get("plan", "free"))["api_access"]:
        raise HTTPException(status_code=403, detail="API access requires the Pro plan.")
    key = new_api_key()
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"api_key": key}})
    return {"api_key": key}
