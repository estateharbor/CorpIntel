"""Companies router."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth_utils import consume_search, get_optional_user, plan_limits
from common import attach_director_counts, run_company_query
from db import db
from models import CompanyDetail, ContactInfo, PaginatedCompanies

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PaginatedCompanies)
async def list_companies(
    city: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    company_class: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    min_capital: Optional[float] = Query(None),
    max_capital: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("date_of_incorporation"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_optional_user),
):
    # Enforce free-tier daily search limit (only when a search/filter is active)
    if search:
        usage = await consume_search(user)
        if not usage["allowed"]:
            raise HTTPException(status_code=429,
                                detail=f"Daily search limit reached ({usage['limit']}/day). Upgrade your plan.")
    params = {"city": city.split(",") if city else None,
              "sector": sector.split(",") if sector else None,
              "status": status, "company_class": company_class,
              "date_from": date_from, "date_to": date_to,
              "min_capital": min_capital, "max_capital": max_capital,
              "search": search}
    return await run_company_query(db, params, page=page, limit=limit,
                                   sort_by=sort_by, order=order)


@router.get("/{cin}", response_model=CompanyDetail)
async def get_company(cin: str):
    company = await db.companies.find_one({"cin": cin}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await attach_director_counts(db, [company])
    return company


@router.get("/{cin}/directors")
async def get_directors(cin: str):
    directors = await db.directors.find({"cin": cin}, {"_id": 0}).to_list(100)
    return {"cin": cin, "count": len(directors), "directors": directors}


@router.get("/{cin}/charges")
async def get_charges(cin: str):
    enr = await db.enrichment.find_one({"cin": cin}, {"_id": 0}) or {}
    return {"cin": cin, "charges": enr.get("charges", [])}


@router.get("/{cin}/filings")
async def get_filings(cin: str):
    enr = await db.enrichment.find_one({"cin": cin}, {"_id": 0}) or {}
    return {"cin": cin, "filings": enr.get("filings", [])}


@router.get("/{cin}/contact", response_model=ContactInfo)
async def get_contact(cin: str, user: dict = Depends(get_optional_user)):
    """Contact data is gated to Pro+ plans."""
    allowed = bool(user) and plan_limits(user.get("plan", "free"))["contact_data"]
    if not allowed:
        return {"cin": cin, "locked": True,
                "message": "Contact data is available on the Pro plan. Upgrade to unlock."}
    enr = await db.enrichment.find_one({"cin": cin}, {"_id": 0}) or {}
    return {"cin": cin, "locked": False, "gstin": enr.get("gstin"),
            "email": enr.get("email"), "phone": enr.get("phone"),
            "website": enr.get("website"), "linkedin_url": enr.get("linkedin_url")}


@router.get("/{cin}/similar", response_model=PaginatedCompanies)
async def similar_companies(cin: str, limit: int = Query(6, ge=1, le=20)):
    company = await db.companies.find_one({"cin": cin}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    query = {"cin": {"$ne": cin}}
    ors = []
    if company.get("sector"):
        ors.append({"sector": company["sector"]})
    if company.get("city"):
        ors.append({"city": company["city"]})
    if ors:
        query["$and"] = [{"$or": ors}]
    # Prefer same sector AND city first
    primary = await db.companies.find(
        {"cin": {"$ne": cin}, "sector": company.get("sector"), "city": company.get("city")},
        {"_id": 0}).limit(limit).to_list(limit)
    results = primary
    if len(results) < limit:
        extra = await db.companies.find(query, {"_id": 0}).limit(limit * 2).to_list(limit * 2)
        seen = {c["cin"] for c in results}
        for e in extra:
            if e["cin"] not in seen:
                results.append(e)
                seen.add(e["cin"])
            if len(results) >= limit:
                break
    results = results[:limit]
    await attach_director_counts(db, results)
    return {"total": len(results), "page": 1, "limit": limit, "pages": 1, "results": results}
