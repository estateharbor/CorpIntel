"""Session-aware, resumable MCA enrichment batch processor.

HUMAN-IN-THE-LOOP TOOL — runs ONE bounded session per invocation:
  * Prioritized batch (newest-first, paid_up_capital >= Rs 1,00,000, Active)
  * Hard daily cap (3 sessions/day, IST) + minimum 3h spacing between sessions
  * Requires a freshly injected MCA_SESSION_COOKIE per run
  * Stops cleanly on: time budget (110 min), consecutive failures (circuit
    breaker), CAPTCHA, session expiry, daily cap, or empty queue

SAFETY: This script must NEVER be looped/scheduled automatically. Run it
manually after injecting a fresh cookie. The constants below are CLAMPED so
they cannot be overridden to unsafe values.

Run:  cd /app/backend/services && python run_enrichment_session.py
"""
from __future__ import annotations

import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# --- path + env bootstrap (supports direct execution) ---
_HERE = Path(__file__).resolve().parent          # .../backend/services
_BACKEND = _HERE.parent                            # .../backend
for _p in (str(_HERE), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv(_BACKEND / ".env")

from enrichment_queue import (count_remaining, get_next_batch, mark_enriched,
                              mark_failed, save_enrichment_data)
from mca_scraper import (CaptchaDetectedException, ScrapeResult,
                         SessionExpiredException, scrape_entity)
import session_tracker as st

# ===================== CLAMPED CONFIG (safety guardrails) =====================
# BATCH_SIZE: never higher than 400 even if env requests more.
BATCH_SIZE = min(int(os.getenv("BATCH_SIZE", "400")), 400)
# MIN_DELAY_SECONDS: never below 5 (randomized jitter is mandatory).
MIN_DELAY_SECONDS = max(float(os.getenv("MIN_DELAY_SECONDS", "5")), 5)
MAX_DELAY_SECONDS = max(float(os.getenv("MAX_DELAY_SECONDS", "8")), MIN_DELAY_SECONDS)
# SESSION_TIME_BUDGET_MIN: never above 110 (buffer before likely MCA timeout).
SESSION_TIME_BUDGET_MIN = min(int(os.getenv("SESSION_TIME_BUDGET_MIN", "110")), 110)
# Circuit breaker: stop after this many consecutive failures.
MAX_CONSECUTIVE_FAILURES = int(os.getenv("MAX_CONSECUTIVE_FAILURES", "5"))
COOKIE_ENV = "MCA_SESSION_COOKIE"
# ============================================================================


def print_remaining_count():
    print(f"Remaining companies in priority queue: {count_remaining()}")


def _preflight_checks() -> bool:
    """Daily-cap, minimum-gap and cookie checks. Returns True if OK to start."""
    # --- Daily session cap ---
    sessions_today = st.count_sessions_today()
    if sessions_today >= st.MAX_SESSIONS_PER_DAY:
        print(f"STOP: Already ran {sessions_today}/{st.MAX_SESSIONS_PER_DAY} "
              f"sessions today. Resume tomorrow.")
        return False

    # --- Minimum gap between sessions ---
    hours_since_last = st.hours_since_last_session()
    if hours_since_last is not None and hours_since_last < st.MIN_GAP_BETWEEN_SESSIONS_HOURS:
        wait_needed = st.MIN_GAP_BETWEEN_SESSIONS_HOURS - hours_since_last
        print(f"STOP: Only {hours_since_last:.1f}h since last session. "
              f"Wait {wait_needed:.1f}h more before starting a new session \u2014 "
              f"running sessions too close together increases block risk.")
        return False

    # --- Cookie check ---
    if not os.getenv(COOKIE_ENV):
        print("STOP: No session cookie set. Log into MCA manually, copy the "
              "session cookie, set MCA_SESSION_COOKIE, then re-run.")
        return False
    return True


def run_session(session_type: str = "enrichment", batch_fn=get_next_batch) -> None:
    """Run a single bounded enrichment session."""
    if not _preflight_checks():
        return

    cookie = os.getenv(COOKIE_ENV)
    session_start = time.time()
    session_id = st.log_session_start(session_type=session_type)
    print(f"SESSION START [{session_type}] id={session_id} at "
          f"{datetime.now(timezone.utc).isoformat()} "
          f"(budget {SESSION_TIME_BUDGET_MIN} min, batch {BATCH_SIZE})")

    batch = batch_fn(limit=BATCH_SIZE)
    print(f"Loaded {len(batch)} entities (Companies + LLPs) into this session's batch.")

    consecutive_failures = 0
    enriched_count = 0
    failed_count = 0
    elapsed_minutes = 0.0
    stop_reason = "completed"

    if not batch:
        stop_reason = "empty_queue"
        print("Queue is empty \u2014 nothing to enrich for this cohort. "
              "Great, you're caught up!")

    for company in batch:
        elapsed_minutes = (time.time() - session_start) / 60

        # --- Hard stop before session likely expires ---
        if elapsed_minutes >= SESSION_TIME_BUDGET_MIN:
            stop_reason = "time_budget_reached"
            print(f"SESSION TIME LIMIT REACHED. Enriched {enriched_count} "
                  f"companies this session. Re-run with a fresh cookie to "
                  f"continue from where this left off.")
            break

        # --- Circuit breaker: MCA is actively blocking us ---
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            stop_reason = "consecutive_failures"
            print(f"STOP: {MAX_CONSECUTIVE_FAILURES} consecutive failures \u2014 "
                  f"likely CAPTCHA re-triggered or session expired. Enriched "
                  f"{enriched_count} before this happened. Get a fresh cookie "
                  f"before re-running.")
            break

        ident = company.get("identifier") or company.get("cin")
        entity_type = company.get("entity_type", "Company")
        kind = "LLP" if entity_type == "LLP" else "Company"
        try:
            result: ScrapeResult = scrape_entity(ident, entity_type, cookie=cookie)

            if result.success:
                save_enrichment_data(ident, result.data, entity_type)
                mark_enriched(ident)
                enriched_count += 1
                consecutive_failures = 0
                if entity_type == "LLP":
                    print(f"  [OK]   {ident} ({kind}) enriched "
                          f"(partners={len(result.data.get('partners', []))}, "
                          f"charges={len(result.data.get('charges', []))})")
                else:
                    print(f"  [OK]   {ident} ({kind}) enriched "
                          f"(directors={len(result.data.get('directors', []))}, "
                          f"charges={len(result.data.get('charges', []))})")
            else:
                mark_failed(ident, result.error or "unknown error")
                failed_count += 1
                consecutive_failures += 1
                print(f"  [FAIL] {ident} ({kind}): {result.error}")

        except CaptchaDetectedException as e:
            stop_reason = "captcha"
            print(f"CAPTCHA re-triggered ({e}). Stopping session immediately. "
                  f"Enriched {enriched_count} entities before this.")
            break
        except SessionExpiredException as e:
            stop_reason = "session_expired"
            print(f"Session expired ({e}). Stopping session immediately. "
                  f"Enriched {enriched_count} entities before this.")
            break

        # --- Human-like randomized delay between requests ---
        time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))
    else:
        if batch:
            stop_reason = "batch_complete"

    elapsed_minutes = (time.time() - session_start) / 60
    st.log_session_end(session_id, enriched_count=enriched_count,
                       failed_count=failed_count, elapsed_minutes=elapsed_minutes,
                       stop_reason=stop_reason)

    print(f"SESSION COMPLETE [{session_type}]: {enriched_count} enriched, "
          f"{failed_count} failed, {elapsed_minutes:.1f} minutes elapsed. "
          f"(stop reason: {stop_reason})")
    print_remaining_count()


if __name__ == "__main__":
    run_session()
