"""Stripe subscription service using the official Stripe SDK.

Plans are defined server-side; amounts are never trusted from the frontend.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, Optional

import stripe

logger = logging.getLogger("corpintel.stripe")

# Server-side plan catalogue (INR). Enterprise is contact-sales (no checkout).
PLANS: Dict[str, Dict] = {
    "starter": {"name": "Starter", "amount": 999.0, "currency": "inr", "plan": "starter"},
    "pro": {"name": "Pro", "amount": 2499.0, "currency": "inr", "plan": "pro"},
}


def _api_key() -> Optional[str]:
    return os.getenv("STRIPE_SECRET_KEY")


def stripe_configured() -> bool:
    return bool(_api_key())


def _webhook_secret() -> Optional[str]:
    return os.getenv("STRIPE_WEBHOOK_SECRET")


def _configure_stripe():
    api_key = _api_key()
    if not api_key:
        raise RuntimeError("Stripe not configured (set STRIPE_SECRET_KEY)")
    stripe.api_key = api_key


async def create_subscription_checkout(*, plan_id: str, origin_url: str,
                                       webhook_url: str, user: dict) -> Dict:
    if plan_id not in PLANS:
        raise ValueError("Invalid plan")
    if not stripe_configured():
        raise RuntimeError("Stripe not configured (set STRIPE_SECRET_KEY)")
    plan = PLANS[plan_id]
    success_url = f"{origin_url}/settings?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"
    _configure_stripe()
    metadata = {
        "user_id": user["user_id"],
        "email": user["email"],
        "plan_id": plan_id,
        "plan": plan["plan"],
        "source": "corpintel_subscription",
    }
    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=user["email"],
        client_reference_id=user["user_id"],
        metadata=metadata,
        payment_intent_data={"metadata": metadata},
        line_items=[{
            "quantity": 1,
            "price_data": {
                "currency": plan["currency"],
                "unit_amount": int(plan["amount"] * 100),
                "product_data": {"name": f"CorpIntel India {plan['name']}"},
            },
        }],
    )
    return {"url": session.url, "session_id": session.id,
            "amount": plan["amount"], "currency": plan["currency"], "plan": plan["plan"]}


async def get_checkout_status(*, session_id: str, webhook_url: str) -> Dict:
    _configure_stripe()
    session = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
    return {
        "status": session.status,
        "payment_status": session.payment_status,
        "amount_total": session.amount_total,
        "currency": session.currency,
        "metadata": dict(session.metadata or {}),
    }


async def handle_webhook_event(*, body: bytes, signature: str, webhook_url: str) -> Dict:
    webhook_secret = _webhook_secret()
    if not webhook_secret:
        raise RuntimeError("Stripe webhook not configured (set STRIPE_WEBHOOK_SECRET)")
    event = stripe.Webhook.construct_event(body, signature, webhook_secret)
    session = event["data"]["object"]
    return {
        "event_type": event["type"],
        "event_id": event["id"],
        "session_id": session.get("id"),
        "payment_status": session.get("payment_status"),
        "metadata": dict(session.get("metadata") or {}),
    }
