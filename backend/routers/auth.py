"""Auth router: Email/Password JWT + demo bypass."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from auth_utils import (create_access_token, get_current_user, hash_password,
                        new_api_key, new_user_id, verify_password)
from db import db
from models import (LoginRequest, MagicLinkRequest, RegisterRequest,
                    TokenResponse, UserPublic)

logger = logging.getLogger("corpintel.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

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
