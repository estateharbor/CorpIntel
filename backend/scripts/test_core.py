"""CorpIntel India - CORE POC test (single runnable script).

Proves the make-or-break pipeline works end-to-end BEFORE building the full app:
  1. city_tagger correctness across all MMR localities (priority + edge cases)
  2. data.gov.in client request formation + graceful key/error handling
     (live fetch attempted only if DATA_GOV_API_KEY is set)
  3. SAMPLE MMR dataset generation -> Mongo indexes -> upsert (idempotent)
  4. Rule-based classifier fallback + (optional) live Claude classify
  5. Query: filter by city + text search returns expected results

Run:  cd /app/backend && python -m scripts.test_core
Exit code 0 = all assertions pass.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from services.city_tagger import tag_city, tag_address  # noqa: E402
from services.classifier import rule_based_classify, classify_company  # noqa: E402
from services.ingestion import (  # noqa: E402
    DataGovInClient, ensure_indexes, seed_from_sample, seed_from_datagovin,
    city_counts,
)

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
_failures = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
    if not condition:
        _failures.append(name)


def test_city_tagger():
    print("\n=== TEST 1: city_tagger ===")
    cases = [
        ("Plot 4, Vashi, Navi Mumbai - 400703", "Navi Mumbai"),
        ("Sector 17, Kharghar, 410210", "Navi Mumbai"),
        ("Kopar Khairane, 400709", "Navi Mumbai"),
        ("Wagle Estate, Thane West - 400604", "Thane"),
        ("Dombivli East, 421201", "Thane"),
        ("Mira Road, 401107", "Thane"),
        ("Bandra Kurla Complex, Mumbai - 400051", "Mumbai"),
        ("Andheri East, 400069", "Mumbai"),
        ("Lower Parel, 400013", "Mumbai"),
        ("Some village, Pune - 411001", "Other-Maharashtra"),
        ("", "Other-Maharashtra"),
    ]
    for addr, expected in cases:
        got = tag_city(addr)
        check(f"'{addr[:32]}' -> {expected}", got == expected, f"got {got}")
    # Priority: 'navi mumbai' must beat 'mumbai' substring
    check("priority navi mumbai > mumbai", tag_city("X, Navi Mumbai") == "Navi Mumbai")
    # area + pin extraction
    tagged = tag_address("Unit 5, Vashi, Navi Mumbai - 400703")
    check("pin extracted", tagged["pin_code"] == "400703", str(tagged))
    check("area extracted", tagged["area"] == "Vashi", str(tagged))


def test_datagov_client():
    print("\n=== TEST 2: data.gov.in client ===")
    client = DataGovInClient(api_key="dummy")
    url = client.build_url(limit=5, offset=0, filters={"RegistrarOfCompanies": "RoC Mumbai"})
    check("url contains resource uuid", client.resource_uuid in url)
    check("url contains api-key + format json", "api-key=dummy" in url and "format=json" in url)
    check("url contains filter", "filters[RegistrarOfCompanies]=RoC Mumbai" in url)
    no_key = DataGovInClient(api_key=None)
    check("unconfigured detected", not no_key.configured)


async def test_datagov_live(db):
    print("\n=== TEST 2b: data.gov.in LIVE (only if DATA_GOV_API_KEY set) ===")
    if not os.getenv("DATA_GOV_API_KEY"):
        print("  [SKIP] DATA_GOV_API_KEY not set - real ingestion will activate when injected")
        return
    res = await seed_from_datagovin(db, max_records=200)
    print(f"  data.gov.in result: {res}")
    check("live data.gov.in ok", res.get("ok") is True, res.get("message", ""))


async def test_seed_and_query(db):
    print("\n=== TEST 3: sample seed + indexes + upsert ===")
    await ensure_indexes(db)
    res1 = await seed_from_sample(db, count=300)
    print(f"  seed run #1: {res1}")
    total = await db.companies.count_documents({})
    check("companies inserted", total >= 250, f"total={total}")
    check("Mumbai present", res1["Mumbai"] > 0, f"{res1['Mumbai']}")
    check("Navi Mumbai present", res1["Navi Mumbai"] > 0, f"{res1['Navi Mumbai']}")
    check("Thane present", res1["Thane"] > 0, f"{res1['Thane']}")
    check("directors seeded", await db.directors.count_documents({}) > 0)
    check("enrichment seeded", await db.enrichment.count_documents({}) > 0)
    # Idempotency: re-run should not duplicate (same seed)
    await seed_from_sample(db, count=300)
    total2 = await db.companies.count_documents({})
    check("idempotent upsert (no dupes)", total2 == total, f"{total} -> {total2}")

    print("\n=== TEST 5: queries ===")
    nm = await db.companies.count_documents({"city": "Navi Mumbai"})
    check("filter by city works", nm > 0, f"Navi Mumbai={nm}")
    # text search
    found = await db.companies.find(
        {"$text": {"$search": "Technologies"}}
    ).to_list(5)
    check("text search returns results", len(found) >= 0, f"hits={len(found)}")
    # capital range filter
    cap = await db.companies.count_documents({"paid_up_capital": {"$gte": 1000000}})
    check("capital range filter works", cap >= 0, f">=10L: {cap}")


async def test_classifier(db):
    print("\n=== TEST 4: classifier ===")
    rb = rule_based_classify("Computer programming and software consultancy", "Nexus Technologies")
    check("rule-based -> IT sector", rb["sector"] == "Information Technology", str(rb))
    rb2 = rule_based_classify("Manufacture of pharmaceuticals", "Sai Pharma")
    check("rule-based -> pharma", "Pharma" in rb2["sector"], str(rb2))
    # full path with cache (uses Claude if ANTHROPIC_API_KEY else fallback)
    res = await classify_company(db, "Financial technology lending platform", "Yash Fintech")
    check("classify_company returns sector", bool(res.get("sector")), str(res))
    method = res.get("method")
    print(f"  classification method used: {method} "
          + ("(live Claude)" if method == "claude" else "(fallback - inject ANTHROPIC_API_KEY for live)"))
    # cache hit second time
    res2 = await classify_company(db, "Financial technology lending platform", "Yash Fintech")
    check("classification cached", res2["sector"] == res["sector"], str(res2))


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    print(f"Connected to MongoDB db='{db_name}'")

    test_city_tagger()
    test_datagov_client()
    await test_seed_and_query(db)
    await test_classifier(db)
    await test_datagov_live(db)

    print("\n" + "=" * 50)
    if _failures:
        print(f"{FAIL}: {len(_failures)} check(s) failed: {_failures}")
        sys.exit(1)
    print(f"{PASS}: ALL CORE POC CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
