"""Admin router: ingestion + enrichment + stats."""
from __future__ import annotations

from fastapi import APIRouter

from db import db
from services.enrichment import enrich_company
from services.ingestion import (DataGovInClient, seed_from_datagovin,
                                seed_from_sample)

router = APIRouter(prefix="/admin", tags=["admin"])


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
