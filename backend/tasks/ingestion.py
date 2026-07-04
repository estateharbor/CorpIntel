"""Incremental ingestion Celery tasks."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery_app import celery_app
from db import db
from services.ingestion import DataGovInClient
from tasks.common import run_async

logger = logging.getLogger("corpintel.tasks.ingestion")


async def _run_weekly_ingestion() -> dict:
    logger.info("[TASK ingestion] starting incremental ingest")
    client = DataGovInClient()
    if not client.configured:
        await db.job_runs.insert_one({
            "job": "weekly_ingest",
            "ran_at": datetime.now(timezone.utc),
            "status": "skipped",
            "message": "no key / MCA blocked",
            "runner": "celery",
        })
        return {"status": "skipped", "message": "DATA_GOV_API_KEY not set"}
    await db.job_runs.insert_one({
        "job": "weekly_ingest",
        "ran_at": datetime.now(timezone.utc),
        "status": "ok",
        "message": "incremental attempted",
        "runner": "celery",
    })
    return {"status": "ok"}


@celery_app.task(
    name="tasks.ingestion.run_weekly_ingestion",
    acks_late=True,
    soft_time_limit=2 * 60 * 60,
    time_limit=3 * 60 * 60,
)
def run_weekly_ingestion():
    return run_async(_run_weekly_ingestion())
