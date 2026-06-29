"""Payments router: Stripe subscription checkout + status + webhook."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from auth_utils import get_current_user
from db import db
from models import CheckoutRequest, CheckoutResponse
from services.stripe_service import (PLANS, create_subscription_checkout,
                                     get_checkout_status,
                                     handle_webhook_event, stripe_configured)

logger = logging.getLogger("corpintel.payments")
router = APIRouter(prefix="/payments", tags=["payments"])


def _webhook_url(request: Request) -> str:
    base = str(request.base_url)
    if not base.endswith("/"):
        base += "/"
    return f"{base}api/webhook/stripe"


@router.get("/plans")
async def plans():
    return {"plans": PLANS, "configured": stripe_configured()}


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(payload: CheckoutRequest, request: Request,
                   user: dict = Depends(get_current_user)):
    if payload.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    if not stripe_configured():
        raise HTTPException(status_code=503,
                            detail="Payments are not configured yet. Add STRIPE_SECRET_KEY.")
    try:
        result = await create_subscription_checkout(
            plan_id=payload.plan_id, origin_url=payload.origin_url.rstrip("/"),
            webhook_url=_webhook_url(request), user=user)
    except Exception as e:  # noqa: BLE001
        logger.exception("checkout failed")
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")
    await db.payment_transactions.insert_one({
        "session_id": result["session_id"], "user_id": user["user_id"],
        "email": user["email"], "plan_id": payload.plan_id, "plan": result["plan"],
        "amount": result["amount"], "currency": result["currency"],
        "payment_status": "initiated", "status": "initiated",
        "created_at": datetime.now(timezone.utc),
    })
    return {"url": result["url"], "session_id": result["session_id"]}


async def _apply_paid(session_id: str, metadata: dict):
    """Idempotently upgrade the user's plan after a confirmed payment."""
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if txn and txn.get("payment_status") == "paid":
        return  # already processed
    plan = (metadata or {}).get("plan") or (txn or {}).get("plan")
    user_id = (metadata or {}).get("user_id") or (txn or {}).get("user_id")
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"payment_status": "paid", "status": "complete",
                  "completed_at": datetime.now(timezone.utc)}})
    if user_id and plan:
        await db.users.update_one({"user_id": user_id}, {"$set": {"plan": plan}})
        logger.info("Upgraded user %s -> plan %s", user_id, plan)


@router.get("/status/{session_id}")
async def status(session_id: str, request: Request):
    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Payments not configured")
    try:
        result = await get_checkout_status(session_id=session_id, webhook_url=_webhook_url(request))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")
    if result.get("payment_status") == "paid":
        await _apply_paid(session_id, result.get("metadata", {}))
    else:
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": result.get("status"), "payment_status": result.get("payment_status")}})
    return result
