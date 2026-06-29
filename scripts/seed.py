"""CorpIntel India - one-shot seed script (Section 9).

Downloads/parses data.gov.in Company Master Data when DATA_GOV_API_KEY is set,
otherwise seeds a clearly-labeled SAMPLE MMR dataset. Prints a summary with
per-city counts.

Run:  cd /app/backend && python -m scripts.seed
      (or from repo root: python backend/scripts/seed.py)
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(BACKEND_DIR / ".env")

from services.ingestion import (  # noqa: E402
    DataGovInClient, ensure_indexes, seed_from_datagovin, seed_from_sample,
    city_counts,
)


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME", "corpintel")
    db = AsyncIOMotorClient(mongo_url)[db_name]
    print(f"[seed] Connected to MongoDB db='{db_name}'")

    await ensure_indexes(db)
    client = DataGovInClient()

    if client.configured:
        print("[seed] DATA_GOV_API_KEY found -> ingesting REAL data.gov.in Company Master Data...")
        res = await seed_from_datagovin(db, max_records=int(os.environ.get("SEED_MAX", "5000")))
        if not res.get("ok") or res.get("total", 0) == 0:
            print(f"[seed] data.gov.in ingest failed ({res.get('message')}). Falling back to SAMPLE dataset.")
            res = await seed_from_sample(db, count=int(os.environ.get("SEED_COUNT", "600")))
    else:
        print("[seed] No DATA_GOV_API_KEY -> seeding labeled SAMPLE MMR dataset.")
        res = await seed_from_sample(db, count=int(os.environ.get("SEED_COUNT", "600")))

    counts = await city_counts(db)
    total = await db.companies.count_documents({})
    print("\n========== SEED SUMMARY ==========")
    print(f"  Source            : {res.get('source')}")
    print(f"  Total in DB       : {total}")
    print(f"  Inserted (run)    : {res.get('inserted', res.get('total'))}")
    print(f"  Updated (run)     : {res.get('updated', 0)}")
    print(f"  Errors            : {res.get('errors', 0)}")
    print(f"  Mumbai            : {counts.get('Mumbai', 0)}")
    print(f"  Navi Mumbai       : {counts.get('Navi Mumbai', 0)}")
    print(f"  Thane             : {counts.get('Thane', 0)}")
    print(f"  Other-Maharashtra : {counts.get('Other-Maharashtra', 0)}")
    print("==================================")


if __name__ == "__main__":
    asyncio.run(main())
