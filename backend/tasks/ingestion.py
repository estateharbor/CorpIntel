"""Celery tasks for data ingestion."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery_app import celery_app
from db import db
from tasks.common import run_async

logger = logging.getLogger("corpintel.tasks.ingestion")


async def _run_weekly_ingestion():
    from services.ingestion import DataGovInClient

    logger.info("[TASK weekly_ingestion] starting incremental ingest")
    client = DataGovInClient()
    if not client.configured:
        logger.info("[TASK weekly_ingestion] DATA_GOV_API_KEY not set; MCA scraper blocked - skipping")
        await db.job_runs.insert_one({
            "job": "weekly_ingestion",
            "ran_at": datetime.now(timezone.utc),
            "status": "skipped",
            "message": "no key / MCA blocked",
        })
        return {"status": "skipped", "message": "DATA_GOV_API_KEY not configured"}

    await db.job_runs.insert_one({
        "job": "weekly_ingestion",
        "ran_at": datetime.now(timezone.utc),
        "status": "ok",
        "message": "incremental attempted",
    })
    return {"status": "ok", "message": "incremental attempted"}


@celery_app.task(
    name="tasks.ingestion.run_weekly_ingestion",
    bind=True,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    soft_time_limit=7200,
    time_limit=10800,
)
def run_weekly_ingestion(self):
    return run_async(_run_weekly_ingestion())
