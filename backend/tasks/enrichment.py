"""Manual enrichment Celery tasks.

This task is intentionally not scheduled by Celery Beat. It exists so an
operator can run the existing human-in-the-loop session runner through the
enrichment queue while preserving one-session-at-a-time guardrails.
"""
from __future__ import annotations

import os

import redis

from celery_app import celery_app

LOCK_KEY = "enrichment_lock:manual_session"
LOCK_TTL_SECONDS = 130 * 60


def _redis_client():
    return redis.Redis.from_url(os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0")))


@celery_app.task(
    name="tasks.enrichment.run_manual_enrichment_session",
    autoretry_for=(),
    soft_time_limit=120 * 60,
    time_limit=130 * 60,
)
def run_manual_enrichment_session(session_type: str = "enrichment"):
    client = _redis_client()
    acquired = client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL_SECONDS)
    if not acquired:
        return {"status": "skipped", "reason": "enrichment session already running"}
    try:
        from services.run_enrichment_session import run_session

        run_session(session_type=session_type)
        return {"status": "completed"}
    finally:
        client.delete(LOCK_KEY)
