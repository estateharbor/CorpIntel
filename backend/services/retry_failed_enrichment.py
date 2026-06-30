"""Manually-triggered retry runner for previously-FAILED enrichments.

Processes only companies where enrichment_attempted=True AND enriched=False
(and fewer than 3 attempts \u2014 permanently-failed records are skipped). It reuses
the EXACT session-cap, gap-check, time-budget and circuit-breaker logic of the
normal runner and COUNTS as one of the 3 daily sessions.

NEVER chain this automatically after a normal session. Run it on purpose, with
a fresh MCA_SESSION_COOKIE injected.

Run:  cd /app/backend/services && python retry_failed_enrichment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
for _p in (str(_HERE), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
load_dotenv(_BACKEND / ".env")

from enrichment_queue import get_failed_batch
from run_enrichment_session import run_session


if __name__ == "__main__":
    print("RETRY MODE: processing previously-failed enrichments only "
          "(counts as one of today's 3 sessions).")
    run_session(session_type="retry", batch_fn=get_failed_batch)
