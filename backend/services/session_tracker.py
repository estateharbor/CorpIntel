"""Session tracker: daily cap + minimum-gap enforcement + session logging.

All session timestamps are stored in UTC in the `enrichment_sessions`
collection. "Today" and "tomorrow" boundaries are computed in IST
(Asia/Kolkata) as required. Constants are clamped so they can NEVER be
overridden to unsafe values via env.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytz

from enrichment_queue import get_db

IST = pytz.timezone("Asia/Kolkata")

# --- Clamped safety constants (cannot be overridden to be unsafe) ---
# Hard daily cap: never more than 3, even if env requests more.
MAX_SESSIONS_PER_DAY = min(int(os.getenv("MAX_SESSIONS_PER_DAY", "3")), 3)
# Minimum spacing: never less than 3 hours, even if env requests less.
MIN_GAP_BETWEEN_SESSIONS_HOURS = max(float(os.getenv("MIN_GAP_BETWEEN_SESSIONS_HOURS", "3")), 3)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def ist_today_start_utc() -> datetime:
    now_ist = datetime.now(IST)
    start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_ist.astimezone(timezone.utc)


def ist_tomorrow_start_utc() -> datetime:
    return ist_today_start_utc() + timedelta(days=1)


def count_sessions_today() -> int:
    return get_db().enrichment_sessions.count_documents(
        {"started_at": {"$gte": ist_today_start_utc()}}
    )


def get_last_session() -> Optional[dict]:
    return get_db().enrichment_sessions.find_one(sort=[("started_at", -1)])


def get_last_session_timestamp() -> Optional[datetime]:
    s = get_last_session()
    return _aware(s["started_at"]) if s and s.get("started_at") else None


def hours_since_last_session() -> Optional[float]:
    last = get_last_session_timestamp()
    if not last:
        return None
    return (_now_utc() - last).total_seconds() / 3600


def next_session_available_at() -> Optional[datetime]:
    """Return when the next session may start, or None if available now."""
    if count_sessions_today() >= MAX_SESSIONS_PER_DAY:
        return ist_tomorrow_start_utc()
    last = get_last_session_timestamp()
    if last:
        gap_end = last + timedelta(hours=MIN_GAP_BETWEEN_SESSIONS_HOURS)
        if gap_end > _now_utc():
            return gap_end
    return None


def log_session_start(session_type: str = "enrichment") -> str:
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    get_db().enrichment_sessions.insert_one({
        "session_id": session_id,
        "type": session_type,
        "started_at": _now_utc(),
        "status": "running",
        "enriched_count": 0,
        "failed_count": 0,
        "elapsed_minutes": 0,
        "stop_reason": None,
    })
    return session_id


def log_session_end(session_id: str, enriched_count: int, failed_count: int,
                    elapsed_minutes: float, stop_reason: str) -> None:
    get_db().enrichment_sessions.update_one(
        {"session_id": session_id},
        {"$set": {
            "ended_at": _now_utc(),
            "enriched_count": enriched_count,
            "failed_count": failed_count,
            "elapsed_minutes": round(elapsed_minutes, 1),
            "stop_reason": stop_reason,
            "status": "completed",
        }},
    )
