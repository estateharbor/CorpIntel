"""City tagging service for the Mumbai Metropolitan Region (MMR).

Classifies a raw registered-office address string into one of:
  - Navi Mumbai
  - Thane
  - Mumbai
  - Other-Maharashtra

Also extracts a best-effort `area` (locality) and 6-digit `pin_code`.
The locality keyword lists are taken verbatim from the product spec.
"""
from __future__ import annotations

import re
from typing import Dict, Optional

# --- Exact locality keyword lists (per spec) -------------------------------
NAVI_MUMBAI = [
    "vashi", "navi mumbai", "belapur", "kharghar", "airoli", "nerul",
    "panvel", "kamothe", "ghansoli", "kopar khairane", "sanpada",
    "turbhe", "seawoods",
]
THANE = [
    "thane", "kalyan", "dombivli", "ulhasnagar", "ambernath", "badlapur",
    "bhiwandi", "mira road", "vasai", "virar", "nalasopara", "naigaon",
    "shahapur",
]
MUMBAI = [
    "mumbai", "bandra", "andheri", "borivali", "dadar", "kurla",
    "ghatkopar", "malad", "kandivali", "worli", "powai", "vikhroli",
    "mulund", "chembur", "colaba", "lower parel", "goregaon",
    "jogeshwari", "santacruz", "vile parle", "dharavi", "sion",
    "matunga", "wadala",
]

# Priority order matters: Navi Mumbai is checked before Thane before Mumbai
# because "mumbai" is a substring of "navi mumbai".
_PIN_RE = re.compile(r"\b(\d{6})\b")


def tag_city(address: Optional[str]) -> str:
    """Return the MMR city for an address (verbatim spec logic)."""
    if not address:
        return "Other-Maharashtra"
    a = address.lower()
    if any(k in a for k in NAVI_MUMBAI):
        return "Navi Mumbai"
    elif any(k in a for k in THANE):
        return "Thane"
    elif any(k in a for k in MUMBAI):
        return "Mumbai"
    return "Other-Maharashtra"


def extract_pin(address: Optional[str]) -> Optional[str]:
    """Extract a 6-digit Indian PIN code from an address string."""
    if not address:
        return None
    m = _PIN_RE.search(address)
    return m.group(1) if m else None


def extract_area(address: Optional[str], city: Optional[str] = None) -> Optional[str]:
    """Best-effort locality (area) extraction from the address.

    Returns the matched locality keyword in Title Case. Prefers the most
    specific (longest) matching keyword so e.g. "kopar khairane" wins over
    a generic city token.
    """
    if not address:
        return None
    a = address.lower()
    candidates = NAVI_MUMBAI + THANE + MUMBAI
    # Exclude the generic city words so we get a *locality* not the city
    generic = {"mumbai", "navi mumbai", "thane"}
    matches = [k for k in candidates if k in a and k not in generic]
    if not matches:
        # fall back to generic tokens
        matches = [k for k in candidates if k in a]
    if not matches:
        return None
    best = max(matches, key=len)
    return best.title()


def tag_address(address: Optional[str]) -> Dict[str, Optional[str]]:
    """Convenience: return {city, area, pin_code} for an address."""
    city = tag_city(address)
    return {
        "city": city,
        "area": extract_area(address, city),
        "pin_code": extract_pin(address),
    }
