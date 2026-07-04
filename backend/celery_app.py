"""Celery application and beat schedule for CorpIntel background jobs."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure
from pymongo import MongoClient

broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery(
    "corpintel",
    broker=broker_url,
    backend=result_backend,
    include=[
        "tasks.ingestion",
        "tasks.classification",
        "tasks.alerts",
        "tasks.quality_scoring",
        "tasks.enrichment",
    ],
)

celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="default",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_routes={
        "tasks.ingestion.*": {"queue": "ingestion"},
        "tasks.classification.*": {"queue": "classification"},
        "tasks.alerts.*": {"queue": "alerts"},
        "tasks.quality_scoring.*": {"queue": "quality_scoring"},
        "tasks.enrichment.*": {"queue": "enrichment"},
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


@task_failure.connect
def record_failed_job(sender=None, task_id=None, exception=None, args=None, kwargs=None, **_extra):
    """Persist failed Celery task metadata without affecting Celery failure handling."""
    client = None
    try:
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DB_NAME", "corpintel")
        client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        client[db_name].failed_jobs.insert_one({
            "task": getattr(sender, "name", str(sender)),
            "task_id": task_id,
            "args": list(args or []),
            "kwargs": kwargs or {},
            "error": repr(exception),
            "failed_at": datetime.now(timezone.utc),
        })
    except Exception:
        pass
    finally:
        if client is not None:
            client.close()
