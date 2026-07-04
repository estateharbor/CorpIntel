"""Data-quality scoring Celery tasks."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery_app import celery_app
from db import db
from tasks.common import run_async

logger = logging.getLogger("corpintel.tasks.quality_scoring")


async def _run_quality_scoring() -> dict:
    logger.info("[TASK quality_scoring] starting")
    updated = 0
    async for c in db.companies.find({}, {"_id": 0}):
        enr = await db.enrichment.find_one({"cin": c["cin"]}, {"_id": 0}) or {}
        ndir = await db.directors.count_documents({"cin": c["cin"]})
        score = 0
        if enr.get("phone"):
            score += 10
        if enr.get("email"):
            score += 10
        if enr.get("gstin"):
            score += 15
        if ndir > 0:
            score += 15
        if enr.get("filings"):
            score += 15
        if c.get("sector"):
            score += 20
        if c.get("pin_code"):
            score += 15
        await db.companies.update_one({"cin": c["cin"]}, {"$set": {"data_quality_score": score}})
        updated += 1
    await db.job_runs.insert_one({
        "job": "data_quality_scorer",
        "ran_at": datetime.now(timezone.utc),
        "status": "ok",
        "updated": updated,
        "runner": "celery",
    })
    logger.info("[TASK quality_scoring] updated=%s", updated)
    return {"updated": updated}


@celery_app.task(name="tasks.quality_scoring.run_quality_scoring")
def run_quality_scoring():
    return run_async(_run_quality_scoring())
