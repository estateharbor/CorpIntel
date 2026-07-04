"""Payments router: Razorpay order checkout + verification."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from auth_utils import get_current_user
from db import db
from models import CheckoutRequest, CheckoutResponse, PaymentVerifyRequest
from services.razorpay_service import (PLANS, create_order, public_key_id,
                                       razorpay_configured,
                                       verify_payment_signature)

logger = logging.getLogger("corpintel.payments")
router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/plans")
async def plans():
    return {"plans": PLANS, "configured": razorpay_configured(), "key_id": public_key_id()}


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(payload: CheckoutRequest, user: dict = Depends(get_current_user)):
    if payload.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    if not razorpay_configured():
        raise HTTPException(status_code=503,
                            detail="Payments are not configured yet. Add Razorpay keys.")
    try:
        result = await create_order(plan_id=payload.plan_id, user=user)
    except Exception as e:  # noqa: BLE001
        logger.exception("checkout failed")
        raise HTTPException(status_code=502, detail=f"Razorpay error: {e}")
    await db.payment_transactions.insert_one({
        "order_id": result["order_id"], "provider": "razorpay", "user_id": user["user_id"],
        "email": user["email"], "plan_id": payload.plan_id, "plan": result["plan"],
        "amount": result["amount"], "amount_paise": result["amount_paise"], "currency": result["currency"],
        "payment_status": "initiated", "status": "initiated",
        "created_at": datetime.now(timezone.utc),
    })
    return result


async def _apply_paid(order_id: str, metadata: dict, *, payment_id: str | None = None):
    """Idempotently upgrade the user's plan after a confirmed payment."""
    txn = await db.payment_transactions.find_one({"order_id": order_id}, {"_id": 0})
    if txn and txn.get("payment_status") == "paid":
        return  # already processed
    plan = (metadata or {}).get("plan") or (txn or {}).get("plan")
    user_id = (metadata or {}).get("user_id") or (txn or {}).get("user_id")
    await db.payment_transactions.update_one(
        {"order_id": order_id},
        {"$set": {"payment_status": "paid", "status": "complete",
                  "payment_id": payment_id, "completed_at": datetime.now(timezone.utc)}})
    if user_id and plan:
        await db.users.update_one({"user_id": user_id}, {"$set": {"plan": plan}})
        logger.info("Upgraded user %s -> plan %s", user_id, plan)


async def _mark_payment_status(order_id: str, status: str, *, payment_id: str | None = None):
    await db.payment_transactions.update_one(
        {"order_id": order_id},
        {"$set": {"status": status, "payment_status": status, "payment_id": payment_id,
                  "updated_at": datetime.now(timezone.utc)}})


async def _apply_cancelled(order_id: str | None, metadata: dict):
    user_id = (metadata or {}).get("user_id")
    if not user_id and order_id:
        txn = await db.payment_transactions.find_one({"order_id": order_id}, {"_id": 0})
        user_id = (txn or {}).get("user_id")
    if user_id:
        await db.users.update_one({"user_id": user_id}, {"$set": {"plan": "free"}})
        logger.info("Downgraded user %s -> free after Razorpay cancellation", user_id)


@router.post("/verify")
async def verify_payment(payload: PaymentVerifyRequest):
    if not razorpay_configured():
        raise HTTPException(status_code=503, detail="Payments not configured")
    try:
        result = await verify_payment_signature(
            order_id=payload.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            signature=payload.razorpay_signature,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Razorpay payment verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Payment verification failed")
    if result.get("payment_status") == "paid":
        await _apply_paid(payload.razorpay_order_id, result.get("metadata", {}),
                          payment_id=payload.razorpay_payment_id)
    else:
        await _mark_payment_status(payload.razorpay_order_id, result.get("payment_status", "authorized"),
                                   payment_id=payload.razorpay_payment_id)
    return result
