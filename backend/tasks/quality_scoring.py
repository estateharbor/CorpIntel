"""Celery tasks for data quality scoring."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery_app import celery_app
from db import db
from tasks.common import run_async

logger = logging.getLogger("corpintel.tasks.quality_scoring")


async def _run_quality_scoring():
    logger.info("[TASK quality_scoring] starting")
    updated = 0
    async for company in db.companies.find({}, {"_id": 0}):
        enrichment = await db.enrichment.find_one({"cin": company["cin"]}, {"_id": 0}) or {}
        director_count = await db.directors.count_documents({"cin": company["cin"]})
        score = 0
        if enrichment.get("phone"):
            score += 10
        if enrichment.get("email"):
            score += 10
        if enrichment.get("gstin"):
            score += 15
        if director_count > 0:
            score += 15
        if enrichment.get("filings"):
            score += 15
        if company.get("sector"):
            score += 20
        if company.get("pin_code"):
            score += 15
        await db.companies.update_one(
            {"cin": company["cin"]},
            {"$set": {"data_quality_score": score}},
        )
        updated += 1

    await db.job_runs.insert_one({
        "job": "quality_scoring",
        "ran_at": datetime.now(timezone.utc),
        "status": "ok",
        "updated": updated,
    })
    logger.info("[TASK quality_scoring] updated=%s", updated)
    return {"status": "ok", "updated": updated}


@celery_app.task(
    name="tasks.quality_scoring.run_quality_scoring",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    soft_time_limit=7200,
    time_limit=10800,
)
def run_quality_scoring(self):
    return run_async(_run_quality_scoring())
