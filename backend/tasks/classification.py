"""Celery tasks for company classification."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery_app import celery_app
from db import db
from services.classifier import classify_company
from tasks.common import run_async

logger = logging.getLogger("corpintel.tasks.classification")


async def _run_classification_batch(limit: int = 50):
    logger.info("[TASK classification] starting batch; auto MCA enrichment disabled")
    processed = 0
    cursor = db.companies.find({"classified": {"$ne": True}}, {"_id": 0}).limit(limit)
    async for company in cursor:
        result = await classify_company(
            db,
            company.get("principal_activity", ""),
            company.get("name", ""),
        )
        await db.companies.update_one({"cin": company["cin"]}, {"$set": {
            "sector": result.get("sector"),
            "sub_sector": result.get("sub_sector"),
            "b2b_or_b2c": result.get("b2b_or_b2c"),
            "interesting_flag": result.get("interesting_flag"),
            "interesting_reason": result.get("interesting_reason"),
            "classified": True,
        }})
        processed += 1

    await db.job_runs.insert_one({
        "job": "classification_batch",
        "ran_at": datetime.now(timezone.utc),
        "status": "ok",
        "classified": processed,
        "enrich_attempts": 0,
        "note": "auto MCA enrichment disabled (manual loop only)",
    })
    logger.info("[TASK classification] classified=%s", processed)
    return {"status": "ok", "classified": processed}


@celery_app.task(
    name="tasks.classification.run_classification_batch",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    soft_time_limit=1200,
    time_limit=1500,
)
def run_classification_batch(self, limit: int = 50):
    return run_async(_run_classification_batch(limit=limit))
