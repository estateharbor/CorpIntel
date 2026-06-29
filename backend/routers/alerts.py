"""Alerts router."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from auth_utils import get_current_user
from db import db
from models import AlertRequest

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("")
async def create_alert(payload: AlertRequest, user: dict = Depends(get_current_user)):
    alert = {"id": uuid.uuid4().hex[:10], "name": payload.name,
             "cities": payload.cities, "sectors": payload.sectors,
             "min_capital": payload.min_capital, "frequency": payload.frequency,
             "active": True, "last_triggered": None, "match_count": 0,
             "created_at": datetime.now(timezone.utc)}
    await db.users.update_one({"user_id": user["user_id"]}, {"$push": {"alerts": alert}})
    return {"message": "Alert created", "alert": alert}


@router.get("")
async def list_alerts(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "alerts": 1})
    alerts = (u or {}).get("alerts", [])
    # attach recent triggered count from alerts_log
    for a in alerts:
        a["match_count"] = await db.alerts_log.count_documents({"alert_id": a["id"]})
    return {"alerts": alerts}


@router.get("/log")
async def alert_log(user: dict = Depends(get_current_user), limit: int = 50):
    logs = await db.alerts_log.find({"user_id": user["user_id"]}, {"_id": 0}) \
        .sort("triggered_at", -1).limit(limit).to_list(limit)
    return {"logs": logs}


@router.patch("/{alert_id}/toggle")
async def toggle_alert(alert_id: str, user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "alerts": 1})
    alerts = (u or {}).get("alerts", [])
    for a in alerts:
        if a["id"] == alert_id:
            a["active"] = not a.get("active", True)
    await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"alerts": alerts}})
    return {"message": "toggled", "alerts": alerts}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, user: dict = Depends(get_current_user)):
    await db.users.update_one({"user_id": user["user_id"]},
                              {"$pull": {"alerts": {"id": alert_id}}})
    return {"message": "deleted"}
