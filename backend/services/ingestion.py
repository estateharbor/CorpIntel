"""Data ingestion engine.

Three sources (per spec):
  - SOURCE A: data.gov.in Company Master Data (real, requires DATA_GOV_API_KEY)
  - SOURCE B: MCA incremental scraper (honest module, blocked by CAPTCHA/IP)
  - SOURCE C: per-CIN enrichment scraper (see enrichment.py)

A clearly-labeled SAMPLE dataset is used as a fallback so the product is fully
functional before a real key is injected. All upserts are keyed on CIN.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import httpx

from services.city_tagger import tag_city, extract_area, extract_pin
from services.sample_data import generate_sample_dataset

logger = logging.getLogger("corpintel.ingestion")

# Resource UUID discovered for "Registrars of Companies (ROC)-wise Company
# Master Data" on data.gov.in.
DATA_GOV_RESOURCE_UUID = os.getenv(
    "DATA_GOV_RESOURCE_UUID", "4dbe5667-7b6b-41d7-82af-211562424d9a"
)
DATA_GOV_BASE = "https://api.data.gov.in/resource"

# Mapping of likely data.gov.in column names -> our canonical fields. The
# catalog uses verbose human-readable headers; we normalise defensively.
_COLUMN_ALIASES = {
    "cin": ["cin", "corporate_identification_number", "company_cin"],
    "name": ["company_name", "companyname", "name_of_company", "name"],
    "status": ["company_status", "status", "companystatus"],
    "company_class": ["company_class", "class", "companyclass"],
    "category": ["company_category", "category", "companycategory"],
    "date_of_incorporation": ["date_of_registration", "date_of_incorporation",
                              "registration_date", "dateofregistration"],
    "principal_activity": ["principal_business_activity", "company_indian_principal_business_activity",
                           "principal_business_activity_as_per_cin", "nic_code"],
    "authorized_capital": ["authorized_capital", "authorised_capital", "authorized_cap"],
    "paid_up_capital": ["paidup_capital", "paid_up_capital", "paidupcapital"],
    "roc": ["registrar_of_companies", "roc", "roc_code"],
    "address": ["registered_office_address", "registered_office", "address",
                "company_registered_office_address"],
    "registered_state": ["registered_state", "company_state", "state"],
}


def _first(row: dict, keys: List[str]) -> Optional[str]:
    lower = {k.lower(): v for k, v in row.items()}
    for k in keys:
        if k in lower and lower[k] not in (None, "", "NA", "-"):
            return str(lower[k]).strip()
    return None


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value[:10], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _to_float(value: Optional[str]) -> float:
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def normalize_row(row: dict) -> Optional[dict]:
    """Normalise a raw data.gov.in row into our canonical company document."""
    cin = _first(row, _COLUMN_ALIASES["cin"])
    name = _first(row, _COLUMN_ALIASES["name"])
    if not cin or not name:
        return None
    address = _first(row, _COLUMN_ALIASES["address"]) or ""
    city = tag_city(address)
    doi = _parse_date(_first(row, _COLUMN_ALIASES["date_of_incorporation"]))
    return {
        "cin": cin,
        "name": name,
        "status": _first(row, _COLUMN_ALIASES["status"]) or "Active",
        "company_class": _first(row, _COLUMN_ALIASES["company_class"]) or "Private",
        "category": _first(row, _COLUMN_ALIASES["category"]) or "Company limited by Shares",
        "date_of_incorporation": doi,
        "principal_activity": _first(row, _COLUMN_ALIASES["principal_activity"]) or "",
        "sector": None,
        "sub_sector": None,
        "authorized_capital": _to_float(_first(row, _COLUMN_ALIASES["authorized_capital"])),
        "paid_up_capital": _to_float(_first(row, _COLUMN_ALIASES["paid_up_capital"])),
        "roc": _first(row, _COLUMN_ALIASES["roc"]) or "RoC-Mumbai",
        "address": address,
        "city": city,
        "pin_code": extract_pin(address),
        "area": extract_area(address),
        "registered_state": _first(row, _COLUMN_ALIASES["registered_state"]) or "Maharashtra",
        "last_updated": datetime.now(timezone.utc),
        "enriched": False,
        "classified": False,
        "data_source": "data.gov.in",
        "data_quality_score": 0,
    }


class DataGovInClient:
    """Thin client for the data.gov.in resource API."""

    def __init__(self, api_key: Optional[str] = None, resource_uuid: Optional[str] = None):
        self.api_key = api_key or os.getenv("DATA_GOV_API_KEY")
        self.resource_uuid = resource_uuid or DATA_GOV_RESOURCE_UUID

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def build_url(self, limit: int = 100, offset: int = 0,
                  filters: Optional[Dict[str, str]] = None) -> str:
        url = f"{DATA_GOV_BASE}/{self.resource_uuid}?api-key={self.api_key}&format=json&limit={limit}&offset={offset}"
        if filters:
            for k, v in filters.items():
                url += f"&filters[{k}]={v}"
        return url

    async def fetch_page(self, limit: int = 100, offset: int = 0,
                         filters: Optional[Dict[str, str]] = None) -> Tuple[bool, List[dict], str]:
        """Fetch a page. Returns (ok, records, message)."""
        if not self.configured:
            return False, [], "DATA_GOV_API_KEY not configured"
        url = self.build_url(limit=limit, offset=offset, filters=filters)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
            if resp.status_code == 403:
                return False, [], "Key not authorised (HTTP 403) - check DATA_GOV_API_KEY / resource access"
            if resp.status_code != 200:
                return False, [], f"HTTP {resp.status_code}"
            payload = resp.json()
            records = payload.get("records", []) or payload.get("data", [])
            return True, records, f"fetched {len(records)} records"
        except Exception as e:  # noqa: BLE001
            logger.warning("data.gov.in fetch failed: %s", e)
            return False, [], str(e)


async def ensure_indexes(db) -> None:
    """Create all required MongoDB indexes (idempotent) + entity migration.

    Backward-compatible LLP support: legacy company docs are backfilled with
    entity_type/identifier/identifier_type so the unique `cin` index can be
    converted to a PARTIAL unique index (Companies only). LLP docs carry
    cin=null and are keyed by the generic `identifier` (LLPIN) instead.
    """
    # --- Migration: backfill entity fields on legacy company docs (idempotent) ---
    await db.companies.update_many(
        {"identifier": {"$exists": False}},
        [{"$set": {
            "identifier": "$cin",
            "identifier_type": "CIN",
            "entity_type": "Company",
        }}],
    )

    # --- Convert legacy `cin_1` unique index -> partial-unique (Company only) ---
    try:
        info = await db.companies.index_information()
    except Exception:  # noqa: BLE001
        info = {}
    cin_idx = info.get("cin_1")
    if cin_idx is not None and "partialFilterExpression" not in cin_idx:
        try:
            await db.companies.drop_index("cin_1")
            cin_idx = None
        except Exception as e:  # noqa: BLE001
            logger.warning("could not drop legacy cin index: %s", e)
    if cin_idx is None:
        await db.companies.create_index(
            "cin", unique=True, name="cin_1",
            partialFilterExpression={"entity_type": "Company"})

    # --- Generic entity identifier is the new primary unique key ---
    await db.companies.create_index("identifier", unique=True)
    await db.companies.create_index("entity_type")
    await db.companies.create_index("llpin", sparse=True)

    await db.companies.create_index("city")
    await db.companies.create_index("sector")
    await db.companies.create_index("status")
    await db.companies.create_index("date_of_incorporation")
    await db.companies.create_index("principal_activity")
    await db.companies.create_index([("name", "text"), ("principal_activity", "text")],
                                    name="company_text_idx")
    await db.directors.create_index("din", unique=True)
    await db.directors.create_index("cin")
    # LLP designated partners (parallel to directors)
    await db.partners.create_index("dpin", unique=True)
    await db.partners.create_index("llpin")
    await db.enrichment.create_index("cin", unique=True)
    await db.users.create_index("email", unique=True)
    await db.user_sessions.create_index("session_token")
    await db.alerts_log.create_index("cin")
    await db.upload_jobs.create_index("job_id", unique=True)
    await db.upload_jobs.create_index("created_at")
    logger.info("MongoDB indexes ensured (entity-aware: Companies + LLPs).")


async def upsert_companies(db, companies: List[dict]) -> Dict[str, int]:
    """Upsert company docs keyed on CIN. Returns counts."""
    inserted = updated = errors = 0
    for c in companies:
        try:
            res = await db.companies.update_one(
                {"cin": c["cin"]}, {"$set": c}, upsert=True
            )
            if res.upserted_id is not None:
                inserted += 1
            elif res.modified_count:
                updated += 1
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning("Upsert failed for %s: %s", c.get("cin"), e)
    return {"inserted": inserted, "updated": updated, "errors": errors}


async def seed_from_sample(db, count: int = 600) -> Dict[str, int]:
    """Seed DB from the labeled SAMPLE dataset (companies+directors+enrichment)."""
    data = generate_sample_dataset(count=count)
    comp_result = await upsert_companies(db, data["companies"])
    for d in data["directors"]:
        try:
            await db.directors.update_one({"din": d["din"]}, {"$set": d}, upsert=True)
        except Exception as e:  # noqa: BLE001
            logger.warning("director upsert failed: %s", e)
    for e in data["enrichment"]:
        try:
            await db.enrichment.update_one({"cin": e["cin"]}, {"$set": e}, upsert=True)
        except Exception as ex:  # noqa: BLE001
            logger.warning("enrichment upsert failed: %s", ex)
    counts = await city_counts(db)
    return {
        "source": "sample",
        "total": len(data["companies"]),
        **comp_result,
        "directors": len(data["directors"]),
        "enrichment": len(data["enrichment"]),
        **counts,
    }


async def seed_from_datagovin(db, max_records: int = 2000,
                              roc_filter: Optional[str] = None) -> Dict[str, int]:
    """Seed from the REAL data.gov.in API. Falls back caller-side if not configured."""
    client = DataGovInClient()
    if not client.configured:
        return {"source": "data.gov.in", "ok": False,
                "message": "DATA_GOV_API_KEY not configured", "total": 0}
    all_norm: List[dict] = []
    offset, page = 0, 100
    last_msg = ""
    while offset < max_records:
        ok, records, msg = await client.fetch_page(limit=page, offset=offset)
        last_msg = msg
        if not ok:
            return {"source": "data.gov.in", "ok": False, "message": msg,
                    "total": len(all_norm)}
        if not records:
            break
        for row in records:
            norm = normalize_row(row)
            if norm:
                # keep only Maharashtra / MMR-relevant; tag handles the rest
                all_norm.append(norm)
        offset += page
        if len(records) < page:
            break
    comp_result = await upsert_companies(db, all_norm)
    counts = await city_counts(db)
    return {"source": "data.gov.in", "ok": True, "message": last_msg,
            "total": len(all_norm), **comp_result, **counts}


async def city_counts(db) -> Dict[str, int]:
    pipeline = [{"$group": {"_id": "$city", "count": {"$sum": 1}}}]
    counts = {"Mumbai": 0, "Navi Mumbai": 0, "Thane": 0, "Other-Maharashtra": 0}
    async for doc in db.companies.aggregate(pipeline):
        counts[doc["_id"]] = doc["count"]
    return counts
