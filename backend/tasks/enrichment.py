"""Manual-only Celery task for MCA enrichment sessions."""
from __future__ import annotations

import logging
import os

from celery_app import celery_app

logger = logging.getLogger("corpintel.tasks.enrichment")

LOCK_KEY = "enrichment_lock:manual_session"
LOCK_TTL_SECONDS = 130 * 60


def _redis_client():
    import redis

    return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))


@celery_app.task(
    name="tasks.enrichment.run_manual_enrichment_session",
    bind=True,
    soft_time_limit=120 * 60,
    time_limit=130 * 60,
)
def run_manual_enrichment_session(self):
    """Run a guarded human-in-the-loop MCA session; intentionally not scheduled by beat."""
    redis_client = _redis_client()
    acquired = redis_client.set(LOCK_KEY, self.request.id, nx=True, ex=LOCK_TTL_SECONDS)
    if not acquired:
        logger.info("[TASK enrichment] skipped; another manual session is already running")
        return {"status": "skipped", "message": "manual enrichment already running"}

    try:
        from services.run_enrichment_session import run_session

        result = run_session()
        return {"status": "ok", "result": result}
    finally:
        owner = redis_client.get(LOCK_KEY)
        if owner and owner.decode("utf-8") == self.request.id:
            redis_client.delete(LOCK_KEY)
