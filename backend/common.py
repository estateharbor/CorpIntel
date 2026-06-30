"""Shared query/serialization helpers for company endpoints."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SORT_FIELDS = {
    "date_of_incorporation", "paid_up_capital", "authorized_capital",
    "name", "data_quality_score",
}


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value[:10], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _norm_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [v.strip() for v in value.split(",") if v.strip()]
    return [v for v in value if v and str(v).lower() != "all"]


def build_company_query(p: Dict[str, Any]) -> Dict[str, Any]:
    q: Dict[str, Any] = {}
    et = p.get("entity_type")
    if et and str(et).lower() not in ("all", "both"):
        # Normalise to canonical casing used in storage ("Company" | "LLP").
        canon = "LLP" if str(et).upper() == "LLP" else "Company"
        q["entity_type"] = canon
    cities = _norm_list(p.get("city"))
    if cities:
        q["city"] = {"$in": cities}
    sectors = _norm_list(p.get("sector"))
    if sectors:
        q["sector"] = {"$in": sectors}
    status = p.get("status")
    if status and str(status).lower() != "all":
        q["status"] = status
    cc = p.get("company_class")
    if cc and str(cc).lower() != "all":
        q["company_class"] = cc
    dfrom = _parse_date(p.get("date_from"))
    dto = _parse_date(p.get("date_to"))
    if dfrom or dto:
        dr: Dict[str, Any] = {}
        if dfrom:
            dr["$gte"] = dfrom
        if dto:
            dr["$lte"] = dto
        q["date_of_incorporation"] = dr
    mn = p.get("min_capital")
    mx = p.get("max_capital")
    if mn not in (None, "") or mx not in (None, ""):
        cr: Dict[str, Any] = {}
        if mn not in (None, ""):
            cr["$gte"] = float(mn)
        if mx not in (None, ""):
            cr["$lte"] = float(mx)
        if cr:
            q["paid_up_capital"] = cr
    s = p.get("search")
    if s:
        rx = {"$regex": re.escape(str(s)), "$options": "i"}
        q["$or"] = [{"name": rx}, {"cin": rx}, {"identifier": rx},
                    {"principal_activity": rx}, {"sector": rx}]
    return q


async def attach_director_counts(db, companies: List[dict]) -> List[dict]:
    """Attach a head-count to each entity.

    For Companies this is the director count (keyed by CIN); for LLPs it is the
    designated-partner count (keyed by LLPIN/identifier). Stored on the shared
    ``director_count`` field so existing UI keeps working (label is adjusted
    per entity type on the frontend).
    """
    company_cins = [c["cin"] for c in companies
                    if c.get("entity_type") != "LLP" and c.get("cin")]
    llp_ids = [c["identifier"] for c in companies
               if c.get("entity_type") == "LLP" and c.get("identifier")]

    dcounts: Dict[str, int] = {}
    if company_cins:
        pipeline = [{"$match": {"cin": {"$in": company_cins}}},
                    {"$group": {"_id": "$cin", "n": {"$sum": 1}}}]
        async for d in db.directors.aggregate(pipeline):
            dcounts[d["_id"]] = d["n"]

    pcounts: Dict[str, int] = {}
    if llp_ids:
        pipeline = [{"$match": {"llpin": {"$in": llp_ids}}},
                    {"$group": {"_id": "$llpin", "n": {"$sum": 1}}}]
        async for d in db.partners.aggregate(pipeline):
            pcounts[d["_id"]] = d["n"]

    for c in companies:
        if c.get("entity_type") == "LLP":
            c["director_count"] = pcounts.get(c.get("identifier"), 0)
        else:
            c["director_count"] = dcounts.get(c.get("cin"), 0)
    return companies


async def run_company_query(db, params: Dict[str, Any], *, page: int = 1,
                           limit: int = 50, sort_by: str = "date_of_incorporation",
                           order: str = "desc") -> Dict[str, Any]:
    query = build_company_query(params)
    if sort_by not in SORT_FIELDS:
        sort_by = "date_of_incorporation"
    direction = -1 if str(order).lower() == "desc" else 1
    limit = max(1, min(int(limit), 200))
    page = max(1, int(page))
    skip = (page - 1) * limit
    total = await db.companies.count_documents(query)
    cursor = (db.companies.find(query, {"_id": 0})
              .sort(sort_by, direction).skip(skip).limit(limit))
    results = await cursor.to_list(limit)
    await attach_director_counts(db, results)
    pages = (total + limit - 1) // limit if limit else 1
    return {"total": total, "page": page, "limit": limit, "pages": pages,
            "results": results}


async def fetch_for_export(db, params: Dict[str, Any], limit: int = 5000) -> List[dict]:
    query = build_company_query(params)
    cursor = db.companies.find(query, {"_id": 0}).limit(int(limit))
    rows = await cursor.to_list(int(limit))
    await attach_director_counts(db, rows)
    return rows
