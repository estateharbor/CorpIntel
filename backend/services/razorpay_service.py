"""Razorpay order and webhook helpers."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, Optional

import razorpay

logger = logging.getLogger("corpintel.razorpay")

# Server-side plan catalogue (INR). Enterprise is contact-sales (no checkout).
PLANS: Dict[str, Dict] = {
    "starter": {"name": "Starter", "amount": 999.0, "currency": "INR", "plan": "starter"},
    "pro": {"name": "Pro", "amount": 2499.0, "currency": "INR", "plan": "pro"},
}


def _key_id() -> Optional[str]:
    return os.getenv("RAZORPAY_KEY_ID")


def _key_secret() -> Optional[str]:
    return os.getenv("RAZORPAY_KEY_SECRET")


def _webhook_secret() -> Optional[str]:
    return os.getenv("RAZORPAY_WEBHOOK_SECRET")


def razorpay_configured() -> bool:
    return bool(_key_id() and _key_secret())


def public_key_id() -> Optional[str]:
    return _key_id()


def _client():
    key_id = _key_id()
    key_secret = _key_secret()
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)")
    return razorpay.Client(auth=(key_id, key_secret))


def amount_to_paise(amount: float) -> int:
    return int(round(amount * 100))


async def create_order(*, plan_id: str, user: dict) -> Dict:
    if plan_id not in PLANS:
        raise ValueError("Invalid plan")
    plan = PLANS[plan_id]
    client = _client()
    receipt = f"{user['user_id']}_{plan_id}"[:40]
    notes = {
        "user_id": user["user_id"],
        "email": user["email"],
        "plan_id": plan_id,
        "plan": plan["plan"],
        "source": "corpintel_subscription",
    }
    order = await asyncio.to_thread(
        client.order.create,
        data={
            "amount": amount_to_paise(plan["amount"]),
            "currency": plan["currency"],
            "receipt": receipt,
            "payment_capture": 1,
            "notes": notes,
        },
    )
    return {
        "order_id": order["id"],
        "amount": plan["amount"],
        "amount_paise": amount_to_paise(plan["amount"]),
        "currency": plan["currency"],
        "plan": plan["plan"],
        "key_id": public_key_id(),
        "name": plan["name"],
        "description": f"CorpIntel India {plan['name']}",
        "prefill": {"name": user.get("name", ""), "email": user.get("email", "")},
        "metadata": notes,
    }


async def verify_payment_signature(*, order_id: str, payment_id: str, signature: str) -> Dict:
    client = _client()
    payload = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }
    await asyncio.to_thread(client.utility.verify_payment_signature, payload)
    payment = await asyncio.to_thread(client.payment.fetch, payment_id)
    return {
        "order_id": order_id,
        "payment_id": payment_id,
        "status": payment.get("status"),
        "payment_status": "paid" if payment.get("status") == "captured" else payment.get("status"),
        "amount_total": payment.get("amount"),
        "currency": payment.get("currency"),
        "metadata": dict(payment.get("notes") or {}),
    }


def verify_webhook_signature(*, body: bytes, signature: str) -> None:
    webhook_secret = _webhook_secret()
    if not webhook_secret:
        raise RuntimeError("Razorpay webhook not configured (set RAZORPAY_WEBHOOK_SECRET)")
    client = _client()
    payload = body.decode("utf-8")
    client.utility.verify_webhook_signature(payload, signature, webhook_secret)


def normalize_webhook_event(event: dict) -> Dict:
    event_type = event.get("event", "")
    payload = event.get("payload") or {}
    payment_entity = ((payload.get("payment") or {}).get("entity") or {})
    subscription_entity = ((payload.get("subscription") or {}).get("entity") or {})
    entity = payment_entity or subscription_entity
    notes = dict(entity.get("notes") or {})
    order_id = entity.get("order_id") or notes.get("order_id")
    payment_status = entity.get("status")
    if event_type in {"payment.captured", "order.paid", "subscription.charged"}:
        payment_status = "paid"
    elif event_type == "payment.failed":
        payment_status = "failed"
    elif event_type == "subscription.cancelled":
        payment_status = "cancelled"
    elif event_type == "subscription.halted":
        payment_status = "halted"
    return {
        "event_type": event_type,
        "event_id": event.get("id") or entity.get("id"),
        "order_id": order_id,
        "payment_id": payment_entity.get("id"),
        "subscription_id": subscription_entity.get("id"),
        "payment_status": payment_status,
        "metadata": notes,
        "raw": event,
    }
