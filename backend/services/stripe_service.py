"""Stripe subscription service (TEST mode) via emergentintegrations.

Plans are defined server-side (amounts never trusted from frontend). Uses the
user-injected STRIPE_SECRET_KEY when present, else falls back to the Emergent
test key (STRIPE_API_KEY=sk_test_emergent) so checkout is testable immediately.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("corpintel.stripe")

# Server-side plan catalogue (INR). Enterprise is contact-sales (no checkout).
PLANS: Dict[str, Dict] = {
    "starter": {"name": "Starter", "amount": 999.0, "currency": "inr", "plan": "starter"},
    "pro": {"name": "Pro", "amount": 2499.0, "currency": "inr", "plan": "pro"},
}


def _api_key() -> Optional[str]:
    return os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")


def stripe_configured() -> bool:
    return bool(_api_key())


def _checkout(webhook_url: str):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    return StripeCheckout(api_key=_api_key(), webhook_url=webhook_url)


async def create_subscription_checkout(*, plan_id: str, origin_url: str,
                                       webhook_url: str, user: dict) -> Dict:
    if plan_id not in PLANS:
        raise ValueError("Invalid plan")
    if not stripe_configured():
        raise RuntimeError("Stripe not configured (set STRIPE_SECRET_KEY)")
    plan = PLANS[plan_id]
    from emergentintegrations.payments.stripe.checkout import CheckoutSessionRequest
    success_url = f"{origin_url}/settings?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"
    checkout = _checkout(webhook_url)
    req = CheckoutSessionRequest(
        amount=plan["amount"], currency=plan["currency"],
        success_url=success_url, cancel_url=cancel_url,
        metadata={"user_id": user["user_id"], "email": user["email"],
                  "plan_id": plan_id, "plan": plan["plan"], "source": "corpintel_subscription"},
    )
    session = await checkout.create_checkout_session(req)
    return {"url": session.url, "session_id": session.session_id,
            "amount": plan["amount"], "currency": plan["currency"], "plan": plan["plan"]}


async def get_checkout_status(*, session_id: str, webhook_url: str) -> Dict:
    checkout = _checkout(webhook_url)
    status = await checkout.get_checkout_status(session_id)
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency,
        "metadata": status.metadata,
    }


async def handle_webhook_event(*, body: bytes, signature: str, webhook_url: str) -> Dict:
    checkout = _checkout(webhook_url)
    resp = await checkout.handle_webhook(body, signature)
    return {
        "event_type": resp.event_type,
        "event_id": resp.event_id,
        "session_id": resp.session_id,
        "payment_status": resp.payment_status,
        "metadata": resp.metadata,
    }
