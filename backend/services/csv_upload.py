"""CSV upload service — bulk import of Companies AND LLPs.

Flexible, defensive CSV parser used by the Admin "Data Upload" feature. It:
  * accepts common header variants (alias-mapped, case/space-insensitive)
  * validates each row's identifier as a CIN (Company) or LLPIN (LLP)
  * upserts by the generic `identifier` (CIN or LLPIN), backward compatible
    with all existing code that queries by `cin`
  * maps LLP `total_contribution` -> `paid_up_capital` for filtering
    consistency while preserving the original under `total_contribution`
  * preserves enrichment/classification state across re-uploads
    (via $setOnInsert) and returns an entity-type breakdown summary

Genuinely malformed rows (identifier is neither a valid CIN nor LLPIN, or no
name) are rejected and reported back to the operator.
"""
from __future__ import annotations

import asyncio
import csv
import io
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from services.city_tagger import extract_area, extract_pin, tag_city

logger = logging.getLogger("corpintel.csv_upload")

# Official-style identifier patterns (provided by product spec).
CIN_PATTERN = re.compile(r"^[UL][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$")
LLPIN_PATTERN = re.compile(r"^[A-Z]{3}-[0-9]{4}$")

# --- Flexible header aliases (normalised: lowercased, non-alnum -> "_") ------
_COLUMN_ALIASES: Dict[str, List[str]] = {
    "identifier": ["identifier", "cin_llpin", "cin/llpin", "registration_number",
                   "reg_no", "id"],
    "cin": ["cin", "corporate_identification_number", "company_cin"],
    "llpin": ["llpin", "llp_identification_number", "llp_in"],
    "name": ["name", "company_name", "companyname", "name_of_company",
             "llp_name", "entity_name"],
    "entity_type": ["entity_type", "type", "entitytype"],
    "status": ["status", "company_status", "llp_status", "companystatus"],
    "company_class": ["company_class", "class", "companyclass"],
    "category": ["category", "company_category"],
    "date_of_incorporation": ["date_of_incorporation", "date_of_registration",
                              "registration_date", "incorporation_date",
                              "doi", "dateofregistration"],
    "principal_activity": ["principal_activity", "principal_business_activity",
                           "nic_code", "activity", "business_activity"],
    "authorized_capital": ["authorized_capital", "authorised_capital",
                           "authorized_cap"],
    "paid_up_capital": ["paid_up_capital", "paidup_capital", "paidupcapital"],
    "total_contribution": ["total_contribution", "contribution",
                           "total_obligation_of_contribution",
                           "obligation_of_contribution"],
    "roc": ["roc", "registrar_of_companies", "roc_code"],
    "address": ["address", "registered_office_address", "registered_office",
                "company_registered_office_address", "registered_address"],
    "city": ["city", "company_city"],
    "pin_code": ["pin_code", "pincode", "pin", "postal_code"],
    "registered_state": ["registered_state", "state", "company_state"],
}


def _norm_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (key or "").strip().lower()).strip("_")


def validate_identifier(value: str) -> dict:
    """Classify an identifier string as CIN (Company) or LLPIN (LLP)."""
    if value is None:
        return {"valid": False, "type": None, "entity_type": None, "value": None}
    value = str(value).strip().upper()
    if CIN_PATTERN.match(value):
        return {"valid": True, "type": "CIN", "entity_type": "Company", "value": value}
    if LLPIN_PATTERN.match(value):
        return {"valid": True, "type": "LLPIN", "entity_type": "LLP", "value": value}
    return {"valid": False, "type": None, "entity_type": None, "value": value}


def _first(norm_row: dict, field: str) -> Optional[str]:
    for alias in _COLUMN_ALIASES.get(field, [field]):
        v = norm_row.get(alias)
        if v not in (None, "", "NA", "N/A", "-"):
            return str(v).strip()
    return None


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value[:11].strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _to_float(value: Optional[str]) -> float:
    if value is None:
        return 0.0
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(value)) or 0)
    except (ValueError, TypeError):
        return 0.0


def _decode(file_bytes: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="ignore")


def _build_entity(norm_row: dict, ident: dict) -> dict:
    """Construct the descriptive ($set) part of a company/LLP document."""
    entity_type = ident["entity_type"]
    identifier = ident["value"]
    address = _first(norm_row, "address") or ""
    city = _first(norm_row, "city") or tag_city(address) or None
    pin = _first(norm_row, "pin_code") or extract_pin(address)

    paid = _to_float(_first(norm_row, "paid_up_capital"))
    contribution = _to_float(_first(norm_row, "total_contribution"))

    doc = {
        "identifier": identifier,
        "identifier_type": ident["type"],
        "entity_type": entity_type,
        "name": _first(norm_row, "name"),
        "status": _first(norm_row, "status") or "Active",
        "company_class": _first(norm_row, "company_class"),
        "category": _first(norm_row, "category"),
        "date_of_incorporation": _parse_date(_first(norm_row, "date_of_incorporation")),
        "principal_activity": _first(norm_row, "principal_activity") or "",
        "authorized_capital": _to_float(_first(norm_row, "authorized_capital")),
        "roc": _first(norm_row, "roc") or "RoC-Mumbai",
        "address": address,
        "city": city,
        "pin_code": pin,
        "area": extract_area(address),
        "registered_state": _first(norm_row, "registered_state") or "Maharashtra",
        "last_updated": datetime.now(timezone.utc),
        "data_source": "csv_upload",
    }

    if entity_type == "LLP":
        # LLPs have no paid-up capital; map contribution -> paid_up_capital for
        # filtering consistency, keep the original under total_contribution.
        total_contribution = contribution or paid
        doc["total_contribution"] = total_contribution
        doc["paid_up_capital"] = total_contribution
        doc["llpin"] = identifier
        doc["cin"] = None
        if not doc["company_class"]:
            doc["company_class"] = "LLP"
    else:
        doc["paid_up_capital"] = paid
        doc["total_contribution"] = None
        doc["cin"] = identifier
        if not doc["company_class"]:
            doc["company_class"] = "Private"
        if not doc["category"]:
            doc["category"] = "Company limited by Shares"

    return doc


_EMPTY_SUMMARY = {
    "total_rows": 0, "processed": 0,
    "companies_inserted": 0, "companies_updated": 0,
    "llps_inserted": 0, "llps_updated": 0,
    "rejected_count": 0, "rejected_rows": [],
}

_BATCH_SIZE = 1000


async def process_upload(db, text_stream) -> dict:
    """Stream-parse a CSV text stream and upsert entities in batches.

    Memory-safe for very large files: rows are read lazily from the stream and
    flushed to MongoDB via unordered ``bulk_write`` every ``_BATCH_SIZE`` rows,
    so peak memory stays bounded regardless of file size. Returns an
    entity-type breakdown (Companies vs LLPs, inserted vs updated) plus a
    capped sample of rejected rows.
    """
    try:
        reader = csv.DictReader(text_stream)
        fieldnames = reader.fieldnames
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "message": f"Could not parse CSV: {e}", **_EMPTY_SUMMARY}

    if not fieldnames:
        return {"ok": False, "message": "CSV has no header row.", **_EMPTY_SUMMARY}

    summary = {
        "ok": True, "total_rows": 0, "processed": 0,
        "companies_inserted": 0, "companies_updated": 0,
        "llps_inserted": 0, "llps_updated": 0,
        "rejected_count": 0, "rejected_rows": [],
    }
    now = datetime.now(timezone.utc)

    ops: List[UpdateOne] = []
    metas: List[dict] = []  # parallel to ops: {entity_type, row_number, identifier}

    def _reject(row_number: int, identifier, reason: str):
        summary["rejected_count"] += 1
        if len(summary["rejected_rows"]) < 50:
            summary["rejected_rows"].append({
                "row_number": row_number, "identifier": identifier, "reason": reason})

    async def _flush():
        if not ops:
            return
        upserted_idx, error_idx = set(), {}
        try:
            result = await db.companies.bulk_write(ops, ordered=False)
            upserted_idx = set((result.upserted_ids or {}).keys())
        except BulkWriteError as bwe:
            details = bwe.details or {}
            upserted_idx = {u["index"] for u in details.get("upserted", [])}
            error_idx = {e["index"]: e.get("errmsg", "write error")
                         for e in details.get("writeErrors", [])}
        except Exception as e:  # noqa: BLE001
            for m in metas:
                _reject(m["row_number"], m["identifier"], f"DB error: {e}")
            ops.clear()
            metas.clear()
            return

        for idx, m in enumerate(metas):
            if idx in error_idx:
                _reject(m["row_number"], m["identifier"], "Duplicate/invalid (skipped)")
                continue
            summary["processed"] += 1
            inserted = idx in upserted_idx
            et = m["entity_type"]
            if et == "LLP":
                summary["llps_inserted" if inserted else "llps_updated"] += 1
            else:
                summary["companies_inserted" if inserted else "companies_updated"] += 1
        ops.clear()
        metas.clear()

    for i, raw in enumerate(reader, start=2):  # row 1 is the header
        summary["total_rows"] += 1
        norm = {_norm_key(k): (v.strip() if isinstance(v, str) else v)
                for k, v in raw.items() if k is not None}

        raw_ident = (_first(norm, "identifier") or _first(norm, "cin")
                     or _first(norm, "llpin"))
        ident = validate_identifier(raw_ident)
        if not ident["valid"]:
            _reject(i, raw_ident, "Identifier is neither a valid CIN nor LLPIN")
            continue
        if not _first(norm, "name"):
            _reject(i, ident["value"], "Missing required field: name")
            continue

        doc = _build_entity(norm, ident)
        ops.append(UpdateOne(
            {"identifier": ident["value"]},
            {"$set": doc, "$setOnInsert": {
                "enriched": False, "enrichment_attempted": False,
                "classified": False, "data_quality_score": 0,
                "sector": None, "sub_sector": None, "created_at": now,
            }},
            upsert=True,
        ))
        metas.append({"entity_type": ident["entity_type"], "row_number": i,
                      "identifier": ident["value"]})

        if len(ops) >= _BATCH_SIZE:
            await _flush()

    await _flush()

    total_new = summary["companies_inserted"] + summary["llps_inserted"]
    total_upd = summary["companies_updated"] + summary["llps_updated"]
    summary["message"] = (
        f"Processed {summary['processed']} rows: {total_new} inserted, "
        f"{total_upd} updated, {summary['rejected_count']} rejected.")
    logger.info("[csv_upload] %s (total_rows=%s)", summary["message"], summary["total_rows"])
    return summary



# =====================================================================
# Async background-job pattern (for very large files / Cloudflare-safe)
# =====================================================================

def _count_data_rows(path: str) -> int:
    """Fast newline-based row estimate (minus header) for the progress bar."""
    n = 0
    with open(path, "rb") as f:
        for _ in f:
            n += 1
    return max(n - 1, 0)


def _progress_set(c: dict) -> dict:
    return {
        "processed_rows": c["processed_rows"],
        "inserted_count": c["inserted_count"],
        "updated_count": c["updated_count"],
        "rejected_count": c["rejected_count"],
        "duplicate_within_file_count": c["duplicate_within_file_count"],
        "companies_inserted": c["companies_inserted"],
        "companies_updated": c["companies_updated"],
        "llps_inserted": c["llps_inserted"],
        "llps_updated": c["llps_updated"],
    }


async def process_upload_job(db, job_id: str, temp_path: str) -> None:
    """Background worker: chunked, memory-safe CSV ingest with live progress.

    Reads the temp CSV line-by-line, validates each row (CIN/LLPIN + required
    fields + duplicate-within-file), upserts valid rows via unordered
    ``bulk_write`` in batches, and updates the ``upload_jobs`` document after
    every batch so the frontend can poll real-time progress. Sets status
    ``completed`` (with full summary) or ``failed`` (with error_message).
    """
    import os

    c = {
        "processed_rows": 0, "inserted_count": 0, "updated_count": 0,
        "rejected_count": 0, "duplicate_within_file_count": 0,
        "companies_inserted": 0, "companies_updated": 0,
        "llps_inserted": 0, "llps_updated": 0,
    }
    rejected_rows: List[dict] = []
    seen = set()
    now = datetime.now(timezone.utc)

    try:
        total_est = _count_data_rows(temp_path)
        await db.upload_jobs.update_one({"job_id": job_id}, {"$set": {
            "status": "processing", "started_at": now, "total_rows": total_est}})

        ops: List[UpdateOne] = []
        metas: List[dict] = []

        async def flush():
            if not ops:
                return
            upserted_idx, error_idx = set(), set()
            try:
                res = await db.companies.bulk_write(ops, ordered=False)
                upserted_idx = set((res.upserted_ids or {}).keys())
            except BulkWriteError as bwe:
                details = bwe.details or {}
                upserted_idx = {u["index"] for u in details.get("upserted", [])}
                error_idx = {e["index"] for e in details.get("writeErrors", [])}
            for idx, m in enumerate(metas):
                if idx in error_idx:
                    c["rejected_count"] += 1
                    if len(rejected_rows) < 50:
                        rejected_rows.append({"row_number": m["row_number"],
                                              "identifier": m["identifier"],
                                              "reason": "Database write error (skipped)"})
                    continue
                inserted = idx in upserted_idx
                et = m["entity_type"]
                if et == "LLP":
                    c["llps_inserted" if inserted else "llps_updated"] += 1
                else:
                    c["companies_inserted" if inserted else "companies_updated"] += 1
                c["inserted_count" if inserted else "updated_count"] += 1
            ops.clear()
            metas.clear()

        with open(temp_path, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames:
                raise ValueError("CSV has no header row")

            for i, raw in enumerate(reader, start=2):
                c["processed_rows"] += 1
                norm = {_norm_key(k): (v.strip() if isinstance(v, str) else v)
                        for k, v in raw.items() if k is not None}

                raw_ident = (_first(norm, "identifier") or _first(norm, "cin")
                             or _first(norm, "llpin"))
                ident = validate_identifier(raw_ident)
                if not ident["valid"]:
                    c["rejected_count"] += 1
                    if len(rejected_rows) < 50:
                        rejected_rows.append({"row_number": i, "identifier": raw_ident,
                                              "reason": "Identifier is neither a valid CIN nor LLPIN"})
                    continue
                if not _first(norm, "name"):
                    c["rejected_count"] += 1
                    if len(rejected_rows) < 50:
                        rejected_rows.append({"row_number": i, "identifier": ident["value"],
                                              "reason": "Missing required field: name"})
                    continue
                if ident["value"] in seen:
                    c["duplicate_within_file_count"] += 1
                    continue
                seen.add(ident["value"])

                doc = _build_entity(norm, ident)
                ops.append(UpdateOne(
                    {"identifier": ident["value"]},
                    {"$set": doc, "$setOnInsert": {
                        "enriched": False, "enrichment_attempted": False,
                        "classified": False, "data_quality_score": 0,
                        "sector": None, "sub_sector": None, "created_at": now,
                    }},
                    upsert=True,
                ))
                metas.append({"entity_type": ident["entity_type"], "row_number": i,
                              "identifier": ident["value"]})

                if len(ops) >= _BATCH_SIZE:
                    await flush()
                    await db.upload_jobs.update_one({"job_id": job_id},
                                                    {"$set": _progress_set(c)})
                    await asyncio.sleep(0)  # yield to the event loop

            await flush()

        msg = (f"Processed {c['processed_rows']} rows: {c['inserted_count']} inserted, "
               f"{c['updated_count']} updated, {c['rejected_count']} rejected, "
               f"{c['duplicate_within_file_count']} duplicate-in-file.")
        await db.upload_jobs.update_one({"job_id": job_id}, {"$set": {
            "status": "completed", "completed_at": datetime.now(timezone.utc),
            "total_rows": c["processed_rows"], **_progress_set(c),
            "rejected_rows": rejected_rows, "message": msg}})
        logger.info("[csv_upload_job %s] %s", job_id, msg)

    except Exception as e:  # noqa: BLE001
        logger.exception("[csv_upload_job %s] FAILED", job_id)
        await db.upload_jobs.update_one({"job_id": job_id}, {"$set": {
            "status": "failed", "error_message": str(e),
            "completed_at": datetime.now(timezone.utc),
            **_progress_set(c), "rejected_rows": rejected_rows}})
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
