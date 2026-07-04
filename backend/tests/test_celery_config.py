from celery_app import celery_app
from tasks.enrichment import LOCK_KEY, LOCK_TTL_SECONDS


def test_celery_beat_schedule_contains_expected_tasks():
    scheduled_tasks = {
        entry["task"]
        for entry in celery_app.conf.beat_schedule.values()
    }
    assert scheduled_tasks == {
        "tasks.ingestion.run_weekly_ingestion",
        "tasks.classification.run_classification_batch",
        "tasks.alerts.run_alert_checks",
        "tasks.quality_scoring.run_quality_scoring",
    }


def test_enrichment_task_is_manual_only():
    scheduled_tasks = {
        entry["task"]
        for entry in celery_app.conf.beat_schedule.values()
    }
    assert "tasks.enrichment.run_manual_enrichment_session" not in scheduled_tasks
    assert LOCK_KEY == "enrichment_lock:manual_session"
    assert LOCK_TTL_SECONDS == 130 * 60


def test_task_routes_use_dedicated_queues():
    routes = celery_app.conf.task_routes
    assert routes["tasks.ingestion.*"]["queue"] == "ingestion"
    assert routes["tasks.classification.*"]["queue"] == "classification"
    assert routes["tasks.alerts.*"]["queue"] == "alerts"
    assert routes["tasks.quality_scoring.*"]["queue"] == "quality_scoring"
    assert routes["tasks.enrichment.*"]["queue"] == "enrichment"
