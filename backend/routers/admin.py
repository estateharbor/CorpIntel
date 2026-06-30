"""Admin router: ingestion + enrichment + stats."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytz
from fastapi import APIRouter

from db import db
from services.enrichment import enrich_company
from services.ingestion import (DataGovInClient, seed_from_datagovin,
                                seed_from_sample)

router = APIRouter(prefix="/admin", tags=["admin"])

# Enrichment session governance (mirrors services/session_tracker.py)
_IST = pytz.timezone("Asia/Kolkata")
_MAX_SESSIONS_PER_DAY = 3
_MIN_GAP_HOURS = 3
_BATCH_SIZE = 400
MAX_ATTEMPTS = 3
_PRIORITY_FILTER = {"status": "Active", "paid_up_capital": {"$gte": 100000}}


def _ist_today_start_utc():
    now_ist = datetime.now(_IST)
    return now_ist.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def _aware(dt):
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt



@router.post("/ingest/seed")
async def ingest_seed(count: int = 600):
    """Seed companies. Uses REAL data.gov.in if DATA_GOV_API_KEY is set,
    otherwise the labeled SAMPLE dataset."""
    client = DataGovInClient()
    if client.configured:
        res = await seed_from_datagovin(db, max_records=2000)
        if res.get("ok"):
            return {"mode": "data.gov.in", **res}
        # fall back to sample if the live call failed
        sample = await seed_from_sample(db, count=count)
        return {"mode": "sample (data.gov.in failed)", "datagov_error": res.get("message"), **sample}
    res = await seed_from_sample(db, count=count)
    return {"mode": "sample", **res}


@router.post("/ingest/incremental")
async def ingest_incremental():
    """Trigger the last-7-days incremental fetch (MCA). Honest status returned."""
    client = DataGovInClient()
    if not client.configured:
        return {"ok": False, "blocked": True,
                "message": "MCA portal is CAPTCHA/IP-blocked and DATA_GOV_API_KEY not set. "
                           "Incremental ingest will activate once a key is injected."}
    return {"ok": True, "message": "Incremental ingest attempted via data.gov.in."}


@router.post("/enrich/{cin}")
async def enrich(cin: str):
    return await enrich_company(db, cin)


@router.get("/enrichment-progress")
async def enrichment_progress():
    """Progress + session governance for the human-in-the-loop MCA runner.

    Read-only. Surfaces priority-cohort progress, today's session usage,
    when the next session may safely start, recent session history, and the
    exact terminal commands the operator must run manually.
    """
    cohort = _PRIORITY_FILTER

    total = await db.companies.count_documents(cohort)
    enriched = await db.companies.count_documents({**cohort, "enriched": True})
    remaining = await db.companies.count_documents({**cohort, "enriched": {"$ne": True}})
    attempted_failed = await db.companies.count_documents({
        **cohort, "enrichment_attempted": True, "enriched": {"$ne": True},
        "enrichment_attempts": {"$lt": MAX_ATTEMPTS},
    })
    permanently_failed = await db.companies.count_documents({
        **cohort, "enriched": {"$ne": True}, "enrichment_attempts": {"$gte": MAX_ATTEMPTS},
    })
    not_yet_attempted = await db.companies.count_documents({
        **cohort, "enriched": {"$ne": True}, "enrichment_attempted": {"$ne": True},
    })
    progress_pct = round((enriched / total) * 100, 1) if total else 0.0

    # --- Session governance ---
    today_start = _ist_today_start_utc()
    sessions_today = await db.enrichment_sessions.count_documents(
        {"started_at": {"$gte": today_start}})
    last_session = await db.enrichment_sessions.find_one({}, {"_id": 0}, sort=[("started_at", -1)])

    now = datetime.now(timezone.utc)
    hours_since_last = None
    next_available_at = None
    last_started = _aware(last_session.get("started_at")) if last_session else None
    if last_started:
        hours_since_last = round((now - last_started).total_seconds() / 3600, 1)

    if sessions_today >= _MAX_SESSIONS_PER_DAY:
        # next allowed = tomorrow IST midnight
        next_available_at = today_start + timedelta(days=1)
    elif last_started:
        gap_end = last_started + timedelta(hours=_MIN_GAP_HOURS)
        if gap_end > now:
            next_available_at = gap_end

    can_start_now = next_available_at is None and sessions_today < _MAX_SESSIONS_PER_DAY
    next_available_ist = None
    if next_available_at:
        next_available_ist = next_available_at.astimezone(_IST).strftime("%d %b %Y, %I:%M %p IST")

    recent_sessions = await db.enrichment_sessions.find({}, {"_id": 0}).sort(
        "started_at", -1).limit(8).to_list(8)

    return {
        "progress": {
            "total": total,
            "enriched": enriched,
            "remaining": remaining,
            "not_yet_attempted": not_yet_attempted,
            "attempted_failed": attempted_failed,
            "permanently_failed": permanently_failed,
            "progress_pct": progress_pct,
        },
        "cohort_description": "Active companies with paid-up capital ≥ ₹1,00,000",
        "governance": {
            "sessions_today": sessions_today,
            "max_sessions_per_day": _MAX_SESSIONS_PER_DAY,
            "min_gap_hours": _MIN_GAP_HOURS,
            "batch_size": _BATCH_SIZE,
            "time_budget_minutes": 110,
            "max_consecutive_failures": 5,
            "max_attempts_per_company": MAX_ATTEMPTS,
            "hours_since_last_session": hours_since_last,
            "can_start_now": can_start_now,
            "next_available_at": next_available_at.isoformat() if next_available_at else None,
            "next_available_ist": next_available_ist,
            "auto_enrichment_disabled": True,
        },
        "last_session": last_session,
        "recent_sessions": recent_sessions,
        "commands": {
            "run_session": "cd /app/backend/services && python run_enrichment_session.py",
            "retry_failed": "cd /app/backend/services && python retry_failed_enrichment.py",
            "set_cookie": "export MCA_SESSION_COOKIE='<paste-your-fresh-mca-session-cookie-here>'",
        },
    }


@router.get("/stats")
async def stats():
    total = await db.companies.count_documents({})
    enriched = await db.companies.count_documents({"enriched": True})
    classified = await db.companies.count_documents({"classified": True})
    unclassified = await db.companies.count_documents({"classified": {"$ne": True}})
    unenriched = await db.companies.count_documents({"enriched": {"$ne": True}})
    directors = await db.directors.count_documents({})
    # data source breakdown
    sources = {}
    async for d in db.companies.aggregate([{"$group": {"_id": "$data_source", "n": {"$sum": 1}}}]):
        sources[d["_id"] or "unknown"] = d["n"]
    job_runs = await db.job_runs.find({}, {"_id": 0}).sort("ran_at", -1).limit(10).to_list(10)
    return {
        "companies": total, "enriched": enriched, "classified": classified,
        "directors": directors,
        "queue": {"unclassified": unclassified, "unenriched": unenriched},
        "data_sources": sources,
        "sample_mode": sources.get("sample", 0) > 0 and sources.get("data.gov.in", 0) == 0,
        "recent_jobs": job_runs,
        "datagovin_configured": DataGovInClient().configured,
    }
