"""Analytics router."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query

from db import db

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _city_match(city: Optional[str]):
    if city and city.lower() != "all":
        return {"city": city}
    return {}


@router.get("/summary")
async def summary(city: Optional[str] = Query(None)):
    match = _city_match(city)
    total = await db.companies.count_documents(match)
    # by city
    by_city = {}
    async for d in db.companies.aggregate([{"$group": {"_id": "$city", "n": {"$sum": 1}}}]):
        by_city[d["_id"] or "Unknown"] = d["n"]
    # by status
    by_status = {}
    async for d in db.companies.aggregate([{"$match": match}, {"$group": {"_id": "$status", "n": {"$sum": 1}}}]):
        by_status[d["_id"] or "Unknown"] = d["n"]
    # new this week
    since = datetime.now(timezone.utc) - timedelta(days=7)
    new_week = await db.companies.count_documents({**match, "date_of_incorporation": {"$gte": since}})
    # top sector
    top_sector = None
    async for d in db.companies.aggregate([{"$match": match}, {"$group": {"_id": "$sector", "n": {"$sum": 1}}},
                                           {"$sort": {"n": -1}}, {"$limit": 1}]):
        top_sector = {"sector": d["_id"], "count": d["n"]}
    active = by_status.get("Active", 0)
    struck = by_status.get("Struck Off", 0)
    enriched = await db.companies.count_documents({**match, "enriched": True})
    # by entity type (Company vs LLP)
    by_entity_type = {}
    async for d in db.companies.aggregate([{"$match": match},
                                           {"$group": {"_id": "$entity_type", "n": {"$sum": 1}}}]):
        by_entity_type[d["_id"] or "Company"] = d["n"]
    return {
        "total": total, "by_city": by_city, "by_status": by_status,
        "by_entity_type": by_entity_type,
        "companies_count": by_entity_type.get("Company", 0),
        "llps_count": by_entity_type.get("LLP", 0),
        "new_this_week": new_week, "top_sector": top_sector,
        "active": active, "struck_off": struck,
        "active_ratio": round(active / total * 100, 1) if total else 0,
        "enriched": enriched,
        "enriched_ratio": round(enriched / total * 100, 1) if total else 0,
    }


@router.get("/trends")
async def trends(city: Optional[str] = Query(None), months: int = Query(24, ge=1, le=60)):
    match = _city_match(city)
    since = datetime.now(timezone.utc) - timedelta(days=31 * months)
    match["date_of_incorporation"] = {"$gte": since}
    pipeline = [
        {"$match": match},
        {"$group": {"_id": {"y": {"$year": "$date_of_incorporation"},
                              "m": {"$month": "$date_of_incorporation"}},
                    "n": {"$sum": 1}}},
        {"$sort": {"_id.y": 1, "_id.m": 1}},
    ]
    out = []
    async for d in db.companies.aggregate(pipeline):
        y, m = d["_id"]["y"], d["_id"]["m"]
        out.append({"period": f"{y}-{m:02d}",
                    "label": datetime(y, m, 1).strftime("%b %Y"), "count": d["n"]})
    return {"trends": out}


@router.get("/sectors")
async def sectors(city: Optional[str] = Query(None), limit: int = Query(20, ge=1, le=50)):
    match = _city_match(city)
    pipeline = [{"$match": match}, {"$group": {"_id": "$sector", "n": {"$sum": 1},
                                               "avg_capital": {"$avg": "$paid_up_capital"}}},
                {"$sort": {"n": -1}}, {"$limit": limit}]
    out = []
    async for d in db.companies.aggregate(pipeline):
        out.append({"sector": d["_id"] or "Unclassified", "count": d["n"],
                    "avg_capital": round(d.get("avg_capital") or 0, 0)})
    return {"sectors": out}


@router.get("/capital")
async def capital(city: Optional[str] = Query(None)):
    match = _city_match(city)
    buckets = [
        ("< ₹1L", 0, 100000), ("₹1L - ₹10L", 100000, 1000000),
        ("₹10L - ₹50L", 1000000, 5000000), ("₹50L - ₹1Cr", 5000000, 10000000),
        ("₹1Cr - ₹5Cr", 10000000, 50000000), ("> ₹5Cr", 50000000, 10 ** 15),
    ]
    out = []
    for label, lo, hi in buckets:
        n = await db.companies.count_documents({**match, "paid_up_capital": {"$gte": lo, "$lt": hi}})
        out.append({"range": label, "count": n})
    return {"distribution": out}


@router.get("/heatmap")
async def heatmap(city: Optional[str] = Query(None)):
    match = _city_match(city)
    pipeline = [{"$match": match},
                {"$group": {"_id": {"city": "$city", "area": "$area"}, "n": {"$sum": 1},
                            "avg_capital": {"$avg": "$paid_up_capital"}}},
                {"$sort": {"n": -1}}, {"$limit": 60}]
    out = []
    async for d in db.companies.aggregate(pipeline):
        if not d["_id"].get("area"):
            continue
        out.append({"city": d["_id"]["city"], "area": d["_id"]["area"],
                    "count": d["n"], "avg_capital": round(d.get("avg_capital") or 0, 0)})
    return {"heatmap": out}
