"""Search router."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth_utils import consume_search, get_current_user, get_optional_user
from common import run_company_query
from db import db
from models import AdvancedSearchRequest, SaveSearchRequest

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def quick_search(q: str = Query("", description="search text"),
                       limit: int = Query(10, ge=1, le=50),
                       user: dict = Depends(get_optional_user)):
    """Full text quick search with suggestions."""
    if q:
        usage = await consume_search(user)
        if not usage["allowed"]:
            raise HTTPException(status_code=429,
                                detail=f"Daily search limit reached ({usage['limit']}/day).")
    if not q:
        return {"results": [], "suggestions": []}
    res = await run_company_query(db, {"search": q}, page=1, limit=limit)
    suggestions = [{"cin": c.get("identifier") or c.get("cin"), "name": c["name"],
                    "entity_type": c.get("entity_type", "Company"),
                    "city": c.get("city"), "sector": c.get("sector")}
                   for c in res["results"]]
    return {"results": res["results"], "suggestions": suggestions, "total": res["total"]}


@router.post("/advanced")
async def advanced_search(payload: AdvancedSearchRequest,
                          user: dict = Depends(get_optional_user)):
    params = payload.model_dump()
    if payload.search:
        usage = await consume_search(user)
        if not usage["allowed"]:
            raise HTTPException(status_code=429,
                                detail=f"Daily search limit reached ({usage['limit']}/day).")
    return await run_company_query(db, params, page=payload.page, limit=payload.limit,
                                   sort_by=payload.sort_by, order=payload.order)


@router.post("/save")
async def save_search(payload: SaveSearchRequest, user: dict = Depends(get_current_user)):
    saved = {"id": uuid.uuid4().hex[:10], "name": payload.name,
             "criteria": payload.criteria, "created_at": datetime.now(timezone.utc)}
    await db.users.update_one({"user_id": user["user_id"]},
                              {"$push": {"saved_searches": saved}})
    return {"message": "Search saved", "saved": saved}


@router.get("/saved")
async def list_saved(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "saved_searches": 1})
    return {"saved_searches": (u or {}).get("saved_searches", [])}


@router.delete("/saved/{search_id}")
async def delete_saved(search_id: str, user: dict = Depends(get_current_user)):
    await db.users.update_one({"user_id": user["user_id"]},
                              {"$pull": {"saved_searches": {"id": search_id}}})
    return {"message": "deleted"}
