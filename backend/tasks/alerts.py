"""Alert-checking Celery tasks."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from celery_app import celery_app
from db import db
from tasks.common import run_async

logger = logging.getLogger("corpintel.tasks.alerts")


async def _run_alert_checks() -> dict:
    logger.info("[TASK alerts] starting")
    since = datetime.now(timezone.utc) - timedelta(days=7)
    total_matches = 0
    async for user in db.users.find({"alerts": {"$exists": True, "$ne": []}}, {"_id": 0}):
        for alert in user.get("alerts", []):
            query = {"date_of_incorporation": {"$gte": since}}
            if alert.get("cities"):
                query["city"] = {"$in": alert["cities"]}
            if alert.get("sectors"):
                query["sector"] = {"$in": alert["sectors"]}
            if alert.get("min_capital"):
                query["paid_up_capital"] = {"$gte": alert["min_capital"]}
            matches = await db.companies.find(query, {"_id": 0}).to_list(100)
            if matches:
                total_matches += len(matches)
                for m in matches:
                    await db.alerts_log.update_one(
                        {"cin": m["cin"], "alert_id": alert.get("id")},
                        {"$setOnInsert": {
                            "cin": m["cin"],
                            "company_name": m["name"],
                            "city": m.get("city"),
                            "sector": m.get("sector"),
                            "alert_id": alert.get("id"),
                            "user_id": user["user_id"],
                            "alert_type": "new_company",
                            "date_of_incorporation": m.get("date_of_incorporation"),
                            "triggered_at": datetime.now(timezone.utc),
                        }},
                        upsert=True,
                    )
                logger.info("[TASK alerts] would email %s: %s matches for '%s'",
                            user["email"], len(matches), alert.get("name"))
    await db.job_runs.insert_one({
        "job": "alert_checker",
        "ran_at": datetime.now(timezone.utc),
        "status": "ok",
        "matches": total_matches,
        "runner": "celery",
    })
    return {"matches": total_matches}


@celery_app.task(name="tasks.alerts.run_alert_checks")
def run_alert_checks():
    return run_async(_run_alert_checks())
