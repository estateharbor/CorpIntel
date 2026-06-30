"""CorpIntel India - FastAPI application entrypoint."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from auth_utils import hash_password, new_api_key, new_user_id  # noqa: E402
from db import client, db  # noqa: E402
from routers import (admin, alerts, analytics, auth, companies, export,  # noqa: E402
                     payments, search)
from services.ingestion import (DataGovInClient, ensure_indexes,  # noqa: E402
                                 seed_from_datagovin, seed_from_sample)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("corpintel")

app = FastAPI(title="CorpIntel India API", version="1.0.0")

API_V1 = "/api/v1"

# Health / meta routers (kept under /api)
meta_router = APIRouter(prefix="/api")


@meta_router.get("/")
async def root():
    return {"message": "CorpIntel India API", "status": "ok"}


@meta_router.get("/health")
async def health():
    total = await db.companies.count_documents({})
    sources = {}
    async for d in db.companies.aggregate([{"$group": {"_id": "$data_source", "n": {"$sum": 1}}}]):
        sources[d["_id"] or "unknown"] = d["n"]
    sample_mode = sources.get("sample", 0) > 0 and sources.get("data.gov.in", 0) == 0
    return {
        "status": "ok",
        "companies": total,
        "sample_mode": sample_mode,
        "datagovin_configured": DataGovInClient().configured,
        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")),
    }


# Stripe webhook MUST live at exactly /api/webhook/stripe
webhook_router = APIRouter(prefix="/api")


@webhook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    from services.stripe_service import handle_webhook_event
    from routers.payments import _apply_paid, _webhook_url
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = await handle_webhook_event(body=body, signature=signature,
                                           webhook_url=_webhook_url(request))
    except Exception as e:  # noqa: BLE001
        logger.warning("Stripe webhook error: %s", e)
        return {"received": False, "error": str(e)}
    if event.get("payment_status") == "paid" and event.get("session_id"):
        await _apply_paid(event["session_id"], event.get("metadata", {}))
    return {"received": True, "event_type": event.get("event_type")}


# Mount routers
app.include_router(meta_router)
app.include_router(webhook_router)
app.include_router(auth.router, prefix=API_V1)
app.include_router(companies.router, prefix=API_V1)
app.include_router(analytics.router, prefix=API_V1)
app.include_router(search.router, prefix=API_V1)
app.include_router(export.router, prefix=API_V1)
app.include_router(alerts.router, prefix=API_V1)
app.include_router(admin.router, prefix=API_V1)
app.include_router(payments.router, prefix=API_V1)

# CORS (credentials enabled for cookie-based Google auth; regex reflects origin)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _ensure_demo_user():
    existing = await db.users.find_one({"email": "demo@corpintel.in"})
    if existing:
        return
    await db.users.insert_one({
        "user_id": new_user_id(), "email": "demo@corpintel.in", "name": "Demo User",
        "plan": "pro", "searches_used": 0, "exports_used": 0,
        "saved_searches": [], "alerts": [], "auth_provider": "demo",
        "password_hash": hash_password("Demo@1234"), "api_key": new_api_key(),
        "picture": None, "created_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc),
    })
    logger.info("Seeded demo user demo@corpintel.in (plan=pro)")


@app.on_event("startup")
async def on_startup():
    await ensure_indexes(db)
    cfg = await db.system_config.find_one({"_id": "ingest"}) or {}
    seeding_disabled = bool(cfg.get("sample_seed_disabled"))
    count = await db.companies.count_documents({})
    if seeding_disabled:
        logger.info("Sample auto-seed DISABLED by admin marker; skipping (companies=%s).", count)
    elif count < 600:
        client_dg = DataGovInClient()
        if client_dg.configured:
            logger.info("DATA_GOV_API_KEY set -> seeding from data.gov.in")
            res = await seed_from_datagovin(db, max_records=2000)
            if not res.get("ok") or res.get("total", 0) == 0:
                logger.warning("data.gov.in seed failed (%s) -> sample fallback", res.get("message"))
                await seed_from_sample(db, count=600)
        else:
            logger.info("No DATA_GOV_API_KEY -> seeding labeled SAMPLE dataset")
            await seed_from_sample(db, count=600)
    await _ensure_demo_user()
    try:
        from services.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:  # noqa: BLE001
        logger.warning("Scheduler failed to start: %s", e)
    logger.info("CorpIntel India API startup complete.")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
