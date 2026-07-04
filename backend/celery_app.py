"""Celery application for CorpIntel background jobs."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from celery import Celery, signals
from celery.schedules import crontab


def _redis_url_for_db(url: str, db_index: int) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{db_index}", parts.query, parts.fragment))


def _default_broker_url() -> str:
    return _redis_url_for_db(os.getenv("REDIS_URL", "redis://localhost:6379/0"), 1)


celery_app = Celery(
    "corpintel",
    broker=os.getenv("CELERY_BROKER_URL", _default_broker_url()),
    backend=os.getenv("CELERY_RESULT_BACKEND") or os.getenv("CELERY_BROKER_URL", _default_broker_url()),
    include=[
        "tasks.ingestion",
        "tasks.classification",
        "tasks.alerts",
        "tasks.enrichment",
        "tasks.quality_scoring",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.ingestion.*": {"queue": "ingestion"},
        "tasks.classification.*": {"queue": "classification"},
        "tasks.alerts.*": {"queue": "alerts"},
        "tasks.enrichment.*": {"queue": "enrichment"},
        "tasks.quality_scoring.*": {"queue": "quality_scoring"},
    },
    beat_schedule={
        "weekly-ingestion": {
            "task": "tasks.ingestion.run_weekly_ingestion",
            "schedule": crontab(day_of_week="mon", hour=9, minute=0),
        },
        "classification-every-15-minutes": {
            "task": "tasks.classification.run_classification_batch",
            "schedule": crontab(minute="*/15"),
        },
        "daily-alerts": {
            "task": "tasks.alerts.run_alert_checks",
            "schedule": crontab(hour=8, minute=0),
        },
        "weekly-quality-scoring": {
            "task": "tasks.quality_scoring.run_quality_scoring",
            "schedule": crontab(day_of_week="sun", hour=0, minute=0),
        },
    },
)


@signals.task_failure.connect
def record_failed_task(sender=None, task_id=None, exception=None, args=None, kwargs=None,
                       traceback=None, einfo=None, **_):
    """Persist failed Celery task metadata so failures are visible outside logs."""
    try:
        from pymongo import MongoClient

        mongo_url = os.environ["MONGO_URL"]
        db_name = os.environ.get("DB_NAME", "corpintel")
        client = MongoClient(mongo_url)
        client[db_name].failed_jobs.insert_one({
            "task_id": task_id,
            "task_name": getattr(sender, "name", str(sender)),
            "args": list(args or []),
            "kwargs": dict(kwargs or {}),
            "error": repr(exception),
            "failed_at": datetime.now(timezone.utc),
        })
        client.close()
    except Exception:
        # The worker log still carries the original failure. Avoid masking it if
        # failure tracking itself cannot reach MongoDB.
        return
