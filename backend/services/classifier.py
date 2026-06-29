"""AI sector classification engine.

Uses Anthropic Claude (model `claude-sonnet-4-6`) via the official SDK with
Tool-Use to force a strict JSON schema. When `ANTHROPIC_API_KEY` is not present
(or the API errors), a deterministic keyword-based fallback classifier is used
so the product degrades gracefully and is always functional.

Results are cached in the `classification_cache` collection keyed by the raw
principal-activity string so the same activity is never re-classified.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("corpintel.classifier")

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

_CLASSIFY_TOOL = {
    "name": "record_classification",
    "description": "Record the sector classification for an Indian company.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sector": {"type": "string", "description": "Broad industry sector"},
            "sub_sector": {"type": "string", "description": "Specific sub-sector"},
            "b2b_or_b2c": {"type": "string", "enum": ["B2B", "B2C", "Both"]},
            "interesting_flag": {"type": "boolean"},
            "interesting_reason": {"type": "string"},
        },
        "required": ["sector", "sub_sector", "b2b_or_b2c", "interesting_flag", "interesting_reason"],
    },
}

# --- Rule-based fallback keyword map ---------------------------------------
_KEYWORD_SECTORS = [
    (("software", "computer", "programming", "it ", "information technology", "saas", "app"),
     ("Information Technology", "Software & IT Services", "B2B")),
    (("financ", "fintech", "lending", "credit", "nbfc", "investment", "securities", "insurance"),
     ("Financial Services", "Finance & FinTech", "B2C")),
    (("pharma", "drug", "medicin", "medical", "clinic", "hospital", "health", "diagnostic"),
     ("Healthcare & Pharma", "Healthcare Services", "B2C")),
    (("manufactur", "machinery", "equipment", "engineering", "industrial", "fabricat"),
     ("Manufacturing", "Engineering & Machinery", "B2B")),
    (("chemical", "polymer", "plastic", "paint"),
     ("Chemicals", "Chemicals & Materials", "B2B")),
    (("textile", "apparel", "garment", "fabric", "clothing"),
     ("Textiles & Apparel", "Garments & Textiles", "B2C")),
    (("logistic", "transport", "warehous", "freight", "shipping", "courier"),
     ("Logistics & Supply Chain", "Freight & Warehousing", "B2B")),
    (("construct", "real estate", "realty", "building", "infrastructure", "developer"),
     ("Real Estate", "Construction & Development", "B2C")),
    (("wholesale", "trading", "trade", "distribut", "import", "export"),
     ("Trading", "Wholesale & Distribution", "B2B")),
    (("retail", "e-commerce", "ecommerce", "internet", "online", "store"),
     ("Retail & E-commerce", "Retail & Online", "B2C")),
    (("food", "beverage", "restaurant", "dairy", "agro", "agri"),
     ("Food & Beverages", "Food Processing", "B2C")),
    (("media", "film", "video", "television", "content", "advertis", "entertain"),
     ("Media & Entertainment", "Digital Media", "B2C")),
    (("educat", "training", "school", "learning", "edtech"),
     ("Education", "EdTech & Training", "B2C")),
    (("consult", "advisory", "management"),
     ("Consulting", "Advisory & Consulting", "B2B")),
    (("hotel", "travel", "tourism", "hospitality", "accommodation"),
     ("Hospitality & Tourism", "Hotels & Travel", "B2C")),
    (("energy", "power", "solar", "renewable", "electric"),
     ("Energy", "Power & Renewables", "B2B")),
    (("motor", "automobile", "vehicle", "auto "),
     ("Automotive", "Auto & Components", "B2B")),
]

_INTERESTING_HINTS = ("software", "fintech", "saas", "renewable", "solar", "ai",
                      "edtech", "e-commerce", "ecommerce", "biotech", "pharma")


def rule_based_classify(activity: Optional[str], name: str = "") -> Dict:
    """Deterministic fallback classification."""
    text = f"{activity or ''} {name or ''}".lower()
    sector, sub, b2b = ("Other Services", "General Business", "B2B")
    for keywords, (s, ss, bb) in _KEYWORD_SECTORS:
        if any(k in text for k in keywords):
            sector, sub, b2b = s, ss, bb
            break
    interesting = any(h in text for h in _INTERESTING_HINTS)
    reason = (
        f"Operates in a high-growth {sector.lower()} space." if interesting
        else f"Standard {sector.lower()} business activity."
    )
    return {
        "sector": sector,
        "sub_sector": sub,
        "b2b_or_b2c": b2b,
        "interesting_flag": interesting,
        "interesting_reason": reason,
        "method": "rule_based",
    }


async def claude_classify(activity: str, name: str = "") -> Optional[Dict]:
    """Classify via Claude. Returns None on any failure (caller falls back)."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=512,
            tools=[_CLASSIFY_TOOL],
            tool_choice={"type": "tool", "name": "record_classification"},
            messages=[{
                "role": "user",
                "content": (
                    "Classify this Indian company. "
                    f"Principal activity: '{activity}'. Company name: '{name}'. "
                    "Return the classification using the tool."
                ),
            }],
        )
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                data = dict(block.input)
                data["method"] = "claude"
                return data
        logger.warning("Claude returned no tool_use block for activity=%s", activity)
        return None
    except Exception as e:  # noqa: BLE001 - degrade gracefully
        logger.warning("Claude classification failed (%s); using fallback.", e)
        return None


async def classify_company(db, activity: Optional[str], name: str = "") -> Dict:
    """Classify with cache. db may be None (skips cache).

    Order: cache -> Claude -> rule-based fallback. Result cached by activity.
    """
    activity = (activity or "").strip()
    cache_key = activity.lower() or "__empty__"

    if db is not None:
        cached = await db.classification_cache.find_one({"_id": cache_key}, {"_id": 0})
        if cached and cached.get("result"):
            return cached["result"]

    result = await claude_classify(activity, name) if activity else None
    if result is None:
        result = rule_based_classify(activity, name)

    if db is not None and activity:
        try:
            await db.classification_cache.update_one(
                {"_id": cache_key},
                {"$set": {"_id": cache_key, "activity": activity, "result": result}},
                upsert=True,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed to cache classification: %s", e)
    return result
