"""Real MCA scraper interface for the human-in-the-loop enrichment runner.

Provides the exact contract the session runner relies on:
  - ENRICHMENT_ENABLED          (env flag)
  - MANUAL_SESSION_COOKIE       (env convenience; per-call cookie still preferred)
  - ScrapeResult(success, data, error)
  - CaptchaDetectedException / SessionExpiredException
  - scrape_company(cin, cookie) -> ScrapeResult

HONEST NOTE: mca.gov.in is CAPTCHA + IP-block protected and returns HTTP 403
without a valid interactive browser session. With a FRESH, manually-injected
MCA session cookie this module attempts REAL requests and parses directors /
charges / filings. If the cookie is missing/expired or MCA challenges the
request, it raises SessionExpiredException / CaptchaDetectedException so the
runner stops cleanly (it must NOT push through a block).
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("corpintel.mca_scraper")

# Feature flag + manual cookie convenience (per-call cookie takes priority).
ENRICHMENT_ENABLED = os.getenv("ENRICHMENT_ENABLED", "true").lower() == "true"
MANUAL_SESSION_COOKIE = os.getenv("MCA_SESSION_COOKIE")

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# MCA company master / signatory endpoints (best-effort; real flow is POST-based)
MCA_MASTER_URL = "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do"
MCA_SIGNATORY_URL = "https://www.mca.gov.in/mcafoportal/viewSignatoryDetails.do"
# LLP master data has a distinct portal endpoint + page structure (Designated
# Partners instead of Directors).
MCA_LLP_MASTER_URL = "https://www.mca.gov.in/mcafoportal/viewLLPMasterData.do"

_CAPTCHA_MARKERS = ("captcha", "recaptcha", "enter the characters",
                    "verification code", "are you human", "g-recaptcha")
_LOGIN_MARKERS = ("please login", "login to mca", "session expired",
                  "user login", "sign in to continue", "your session has timed out")
_GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z\d]Z[A-Z\d]\b")


class CaptchaDetectedException(Exception):
    """Raised when MCA challenges the request with a CAPTCHA / hard block."""


class SessionExpiredException(Exception):
    """Raised when the MCA session cookie is missing, invalid or expired."""


@dataclass
class ScrapeResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: Optional[str] = None


def _num(value: Optional[str]):
    if not value:
        return None
    try:
        return float(re.sub(r"[^0-9.]", "", value))
    except (ValueError, TypeError):
        return None


def _parse_company_page(html: str, cin: str) -> Optional[dict]:
    """Best-effort parse of an MCA company page into structured enrichment data."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    data = {"directors": [], "charges": [], "filings": []}

    m = _GSTIN_RE.search(text)
    if m:
        data["gstin"] = m.group(0)

    for table in soup.find_all("table"):
        headers = " ".join(th.get_text(strip=True).lower() for th in table.find_all("th"))
        rows = table.find_all("tr")
        if "din" in headers or "director" in headers or "signatory" in headers:
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2 and re.match(r"^\d{6,8}$", (cells[0] or "").strip()):
                    data["directors"].append({
                        "din": cells[0].strip(),
                        "name": cells[1] if len(cells) > 1 else None,
                        "designation": cells[2] if len(cells) > 2 else "Director",
                        "is_active": True,
                    })
        elif "charge" in headers:
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2 and cells[0]:
                    data["charges"].append({
                        "charge_id": cells[0],
                        "amount": _num(cells[1]) if len(cells) > 1 else None,
                        "holder": cells[2] if len(cells) > 2 else None,
                        "created": cells[3] if len(cells) > 3 else None,
                    })
        elif "form" in headers or "filing" in headers:
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2 and cells[0]:
                    data["filings"].append({
                        "form_type": cells[0],
                        "filing_date": cells[1] if len(cells) > 1 else None,
                        "status": cells[2] if len(cells) > 2 else "Filed",
                    })

    if not (data["directors"] or data["charges"] or data["filings"] or data.get("gstin")):
        return None
    return data


def _check_block(status_code: int, body_lower: str):
    """Inspect a response and raise the appropriate stop signal if blocked."""
    if status_code == 401 or any(k in body_lower for k in _LOGIN_MARKERS):
        raise SessionExpiredException(f"Session expired / login required (HTTP {status_code})")
    if any(k in body_lower for k in _CAPTCHA_MARKERS):
        raise CaptchaDetectedException("CAPTCHA challenge detected on MCA page")
    if status_code in (403, 429, 503):
        # Hard anti-bot block. Treat as a CAPTCHA-class stop so the runner halts
        # immediately rather than hammering MCA with the same (now suspect) cookie.
        raise CaptchaDetectedException(f"MCA hard block (HTTP {status_code})")


def scrape_company(cin: str, cookie: Optional[str] = None) -> ScrapeResult:
    """Attempt to enrich a single CIN from MCA using an injected session cookie.

    Returns ScrapeResult(success, data, error). Raises CaptchaDetectedException
    or SessionExpiredException on block/expiry (caller must stop the session).
    """
    if not ENRICHMENT_ENABLED:
        return ScrapeResult(False, error="ENRICHMENT_ENABLED is false")

    cookie = cookie or MANUAL_SESSION_COOKIE
    if not cookie:
        raise SessionExpiredException("No MCA session cookie provided")

    headers = {
        "User-Agent": _USER_AGENT,
        "Cookie": cookie,
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://www.mca.gov.in/",
    }
    url = f"{MCA_MASTER_URL}?companyID={cin}"
    try:
        with httpx.Client(timeout=25, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
    except httpx.RequestError as e:
        return ScrapeResult(False, error=f"request error: {e}")

    body_lower = (resp.text or "").lower()
    # Raises CaptchaDetectedException / SessionExpiredException as appropriate.
    _check_block(resp.status_code, body_lower)

    if resp.status_code != 200:
        return ScrapeResult(False, error=f"HTTP {resp.status_code}")

    try:
        data = _parse_company_page(resp.text, cin)
    except Exception as e:  # noqa: BLE001
        return ScrapeResult(False, error=f"parse error: {e}")

    if not data:
        return ScrapeResult(False, error="no parsable enrichment data on page")
    return ScrapeResult(True, data=data)



def _parse_llp_page(html: str, llpin: str) -> Optional[dict]:
    """Parse an MCA LLP master-data page into partners / charges / filings.

    LLP pages expose 'Designated Partners' (DPIN) rather than company
    'Directors' (DIN); the table structure otherwise mirrors the company flow.
    """
    soup = BeautifulSoup(html, "html.parser")
    data: dict = {"partners": [], "charges": [], "filings": []}

    for table in soup.find_all("table"):
        headers = " ".join(th.get_text(strip=True).lower()
                            for th in table.find_all("th"))
        rows = table.find_all("tr")
        if ("designated partner" in headers or "dpin" in headers
                or ("partner" in headers and "name" in headers)):
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2 and cells[0] and cells[0].lower() != "dpin":
                    designation = cells[2] if len(cells) > 2 else "Designated Partner"
                    data["partners"].append({
                        "dpin": cells[0],
                        "name": cells[1],
                        "designation": designation or "Designated Partner",
                        "is_active": True,
                    })
        elif "charge" in headers:
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2 and cells[0]:
                    data["charges"].append({
                        "charge_id": cells[0],
                        "amount": _num(cells[1]) if len(cells) > 1 else None,
                        "holder": cells[2] if len(cells) > 2 else None,
                        "created": cells[3] if len(cells) > 3 else None,
                    })
        elif "form" in headers or "filing" in headers:
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) >= 2 and cells[0]:
                    data["filings"].append({
                        "form_type": cells[0],
                        "filing_date": cells[1] if len(cells) > 1 else None,
                        "status": cells[2] if len(cells) > 2 else "Filed",
                    })

    if not (data["partners"] or data["charges"] or data["filings"]):
        return None
    return data


def scrape_llp(llpin: str, cookie: Optional[str] = None) -> ScrapeResult:
    """Attempt to enrich a single LLPIN from MCA's LLP master-data view.

    Parallel to scrape_company but targets the LLP portal endpoint and parses
    Designated Partners. Same block/expiry semantics (raises Captcha/Session
    exceptions so the session runner halts).
    """
    if not ENRICHMENT_ENABLED:
        return ScrapeResult(False, error="ENRICHMENT_ENABLED is false")

    cookie = cookie or MANUAL_SESSION_COOKIE
    if not cookie:
        raise SessionExpiredException("No MCA session cookie provided")

    headers = {
        "User-Agent": _USER_AGENT,
        "Cookie": cookie,
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://www.mca.gov.in/",
    }
    url = f"{MCA_LLP_MASTER_URL}?llpID={llpin}"
    try:
        with httpx.Client(timeout=25, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
    except httpx.RequestError as e:
        return ScrapeResult(False, error=f"request error: {e}")

    body_lower = (resp.text or "").lower()
    _check_block(resp.status_code, body_lower)

    if resp.status_code != 200:
        return ScrapeResult(False, error=f"HTTP {resp.status_code}")

    try:
        data = _parse_llp_page(resp.text, llpin)
    except Exception as e:  # noqa: BLE001
        return ScrapeResult(False, error=f"parse error: {e}")

    if not data:
        return ScrapeResult(False, error="no parsable LLP enrichment data on page")
    return ScrapeResult(True, data=data)


def scrape_entity(identifier: str, entity_type: str = "Company",
                  cookie: Optional[str] = None) -> ScrapeResult:
    """Entity-type-aware scrape router: Companies -> CIN flow, LLPs -> LLP flow."""
    if (entity_type or "Company") == "LLP":
        return scrape_llp(identifier, cookie)
    return scrape_company(identifier, cookie)
