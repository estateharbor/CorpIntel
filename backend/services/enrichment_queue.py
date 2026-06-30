"""Enrichment selection queue + persistence (SYNC / pymongo).

Used by the standalone, manually-triggered batch runners. Keeps a single
synchronous Mongo client so the CLI scripts can sleep/block freely without an
async event loop. The FastAPI app continues to use motor independently.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env")

logger = logging.getLogger("corpintel.enrichment_queue")

_client = MongoClient(os.environ["MONGO_URL"])
_db = _client[os.environ.get("DB_NAME", "test_database")]

# Priority cohort: Active companies with paid-up capital >= Rs 1,00,000.
PRIORITY_FILTER = {"status": "Active", "paid_up_capital": {"$gte": 100000}}
# Companies with this many failed attempts are considered permanently failed
# and are NOT retried (prevents wasting session budget on bad records).
MAX_ATTEMPTS = 3


def get_db():
    return _db


def get_next_batch(limit: int = 400, entity_type: str | None = None):
    """Newest-first priority batch of un-enriched, not-yet-attempted entities.

    Pass entity_type="Company" or "LLP" to restrict the cohort; default returns
    both (Companies and LLPs share the paid_up_capital filter — for LLPs,
    total_contribution was mapped into paid_up_capital at upload time).
    """
    query = {
        **PRIORITY_FILTER,
        "enriched": {"$ne": True},
        "enrichment_attempted": {"$ne": True},
    }
    if entity_type:
        query["entity_type"] = entity_type
    cursor = (_db.companies.find(query).sort("date_of_incorporation", -1).limit(int(limit)))
    return list(cursor)


def get_failed_batch(limit: int = 400, entity_type: str | None = None):
    """Previously-attempted-but-failed entities, excluding permanently-failed."""
    query = {
        **PRIORITY_FILTER,
        "enrichment_attempted": True,
        "enriched": {"$ne": True},
        "enrichment_attempts": {"$lt": MAX_ATTEMPTS},
    }
    if entity_type:
        query["entity_type"] = entity_type
    cursor = (_db.companies.find(query).sort("date_of_incorporation", -1).limit(int(limit)))
    return list(cursor)


def count_remaining() -> int:
    return _db.companies.count_documents({**PRIORITY_FILTER, "enriched": {"$ne": True}})


def mark_enriched(identifier: str) -> None:
    _db.companies.update_one(
        {"identifier": identifier},
        {"$set": {
            "enriched": True,
            "enrichment_attempted": True,
            "enriched_at": datetime.now(timezone.utc),
            "data_is_demo": False,
            "data_source": "mca",
        }},
    )


def mark_failed(identifier: str, error: str) -> None:
    _db.companies.update_one(
        {"identifier": identifier},
        {
            "$set": {
                "enrichment_attempted": True,
                "enrichment_last_error": str(error)[:500],
                "enrichment_failed_at": datetime.now(timezone.utc),
            },
            "$inc": {"enrichment_attempts": 1},
        },
    )


def save_enrichment_data(identifier: str, data: dict, entity_type: str = "Company") -> None:
    """Persist scraped data. Companies -> directors + enrichment (keyed by CIN);
    LLPs -> designated partners (keyed by LLPIN/DPIN) + enrichment."""
    if entity_type == "LLP":
        for p in (data.get("partners") or []):
            dpin = p.get("dpin") or p.get("din")
            if not dpin:
                continue
            _db.partners.update_one(
                {"dpin": dpin},
                {"$set": {
                    "dpin": dpin, "name": p.get("name"), "llpin": identifier,
                    "designation": p.get("designation", "Designated Partner"),
                    "date_of_appointment": p.get("date_of_appointment"),
                    "is_active": p.get("is_active", True),
                }},
                upsert=True,
            )
    else:
        for d in (data.get("directors") or []):
            din = d.get("din")
            if not din:
                continue
            _db.directors.update_one(
                {"din": din},
                {"$set": {
                    "din": din, "name": d.get("name"), "cin": identifier,
                    "designation": d.get("designation", "Director"),
                    "date_of_appointment": d.get("date_of_appointment"),
                    "is_active": d.get("is_active", True),
                }},
                upsert=True,
            )
    enr = {
        "cin": identifier,
        "charges": data.get("charges", []),
        "filings": data.get("filings", []),
        "source": "mca",
        "enriched_at": datetime.now(timezone.utc),
    }
    for k in ("gstin", "email", "phone", "website", "linkedin_url"):
        if data.get(k):
            enr[k] = data[k]
    _db.enrichment.update_one({"cin": identifier}, {"$set": enr}, upsert=True)
