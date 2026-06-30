# CorpIntel India — MCA Enrichment Batch Runner (Human-in-the-loop) Plan (UPDATED)

## Objectives
- Deliver a **manual, resumable, session-aware** MCA enrichment runner that **never auto-loops** and enforces guardrails (**3 sessions/day**, **≥3h gap**, **≤110m budget**, circuit breakers for **CAPTCHA/session expiry**).
- Provide an **Admin Enrichment Dashboard** to monitor queue progress and guide the operator with **copy/paste terminal commands**.
- Ensure **all background/scheduled MCA enrichment is disabled** (prevents bans and preserves queue accuracy). Background jobs may continue for **classification only**.
- Validate guardrails and UI end-to-end; ship a production-ready feature set.

**Current status:** ✅ **ALL PHASES COMPLETED** (backend + frontend wired, manual guardrails verified, full regression tests passed).

---

## Phase 1 — Core Guardrail POC (Isolation)
**User stories (core):**
1. As an operator, I want the session runner to **STOP** if `MCA_SESSION_COOKIE` is missing so I don’t accidentally trigger block behavior.
2. As an operator, I want the runner to **STOP** after 3 sessions/day so I stay within safe limits.
3. As an operator, I want the runner to **STOP** if the last session was <3 hours ago so I don’t run sessions too close together.
4. As an operator, I want the runner to **STOP** on CAPTCHA/session-expired signals so it never brute-forces through blocks.
5. As an operator, I want every session start/end to be logged so I can resume confidently and audit behavior.

**Steps (implemented + verified)**
1. **POC: verify script-level guardrails via terminal (no real scraping)**
   - Ran `python /app/backend/services/run_enrichment_session.py` with **no cookie** → ✅ `STOP: No session cookie set...`.
   - Inserted **dummy cookie** and simulated session limits via temporary DB writes:
     - Created **3** `enrichment_sessions` records in IST “today” → ✅ daily-cap STOP.
     - Created a “recent” session **1 hour ago** → ✅ min-gap STOP.
   - Verified `session_tracker.next_session_available_at()` returned correct UTC timestamp.
2. **Retry runner guardrails**
   - Ran `python /app/backend/services/retry_failed_enrichment.py` with **no cookie** → ✅ STOP.
3. **Cleanup**
   - Removed all temporary test session records after verification.

**Exit criteria (met)**
- ✅ Deterministic STOP outputs for: missing cookie, daily cap, min-gap.
- ✅ Session governance logic validated (including next-available time computation).

---

## Phase 2 — V1 App Development (Backend + Frontend)
**User stories (dashboard + ops):**
1. As an admin, I want to see **overall queue progress** (total/remaining/enriched/failed) so I know how much work is left.
2. As an admin, I want to see **session governance status** (sessions today, next allowed start time) so I don’t violate rules.
3. As an admin, I want a **copy-command helper** so I can run the correct script safely without mistakes.
4. As an admin, I want to see **recent sessions** and stop reasons so I can react to CAPTCHA/expiry.
5. As an admin, I want the system to **never auto-run MCA enrichment** so manual control is guaranteed.

### 2A. Backend
**Implemented**
1. **Added `GET /api/v1/admin/enrichment-progress`** in `backend/routers/admin.py`:
   - Returns:
     - Priority cohort totals: `total`, `enriched`, `remaining`, `not_yet_attempted`, `attempted_failed`, `permanently_failed`, `progress_pct`
     - Governance: `sessions_today`, `max_sessions_per_day=3`, `min_gap_hours=3`, `batch_size=400`, `time_budget_minutes=110`, `max_consecutive_failures=5`, `max_attempts_per_company=3`, `can_start_now`, `next_available_at`, `next_available_ist`, `auto_enrichment_disabled=true`
     - `last_session`, `recent_sessions`, `cohort_description`
     - Exact operator commands:
       - `cd /app/backend/services && python run_enrichment_session.py`
       - `cd /app/backend/services && python retry_failed_enrichment.py`
       - `export MCA_SESSION_COOKIE='<paste-your-fresh-mca-session-cookie-here>'`
2. **Disabled automatic MCA enrichment in `services/scheduler.py`**:
   - Removed background calls to `enrich_company()`.
   - `enrichment_worker` is now **classification-only**.
   - Confirmed via a fresh job run entry: `enrich_attempts=0` with note `auto MCA enrichment disabled (manual loop only)`.
   - Removed the unused `enrich_company` import.

**Exit criteria (met)**
- ✅ Endpoint exists and returns required JSON.
- ✅ Scheduler no longer performs MCA enrichment attempts.

### 2B. Frontend
**Implemented**
1. **Created `/frontend/src/pages/AdminEnrichment.js`** (shadcn UI + required test IDs):
   - KPI cards: remaining, enriched, failed (retryable), sessions today.
   - Progress bar for priority cohort.
   - Governance panel with **Ready** / **Cooldown** states.
   - Copy-command helper (cookie export, run session, retry failed).
   - Clipboard copy is wrapped with **try/catch + fallback** to avoid runtime overlays in restricted clipboard contexts.
   - 5-step instruction panel for safe operation.
   - Recent sessions table + stop-reason badges.
   - Hard-stop banner for `captcha`, `session_expired`, `consecutive_failures`.
2. **Added API helper** in `frontend/src/lib/api.js`:
   - `getEnrichmentProgress()` → calls `/api/v1/admin/enrichment-progress`.
3. **Wired routing + nav**:
   - Protected route: `/admin/enrichment` in `App.js`.
   - Sidebar nav item: `nav-admin-enrichment` in `lib/nav.js`.
   - Added testId registry: `constants/testIds/adminEnrichment.js` and re-exported in `constants/testIds/index.js`.
4. **Verification**
   - Build check (esbuild) ✅
   - Visual verification (screenshot) ✅

**Exit criteria (met)**
- ✅ Admin dashboard loads, renders progress and governance, provides copy commands, and shows instruction panel.

---

## Phase 3 — Testing & Validation
**User stories (quality/regression):**
1. As an operator, I want backend STOP behavior tests so I’m confident the runner won’t run unsafely.
2. As an admin, I want the dashboard to show accurate counts so I can make decisions.
3. As a developer, I want automated end-to-end tests to catch regressions in core SaaS flows.
4. As an operator, I want the UI to remain usable on mobile so I can monitor sessions anywhere.
5. As a maintainer, I want failures to be observable (stop reasons, failed counts) so debugging is fast.

**Steps (executed)**
1. **Manual terminal tests (no real MCA scraping)**
   - ✅ Missing cookie STOP.
   - ✅ Daily cap STOP.
   - ✅ Min-gap STOP.
   - ✅ Retry script guardrail STOP.
2. **Testing agent run (full regression)**
   - ✅ `testing_agent_v3` results in `/app/test_reports/iteration_2.json`:
     - Backend: **100% (36/36)** including new endpoint + regressions.
     - Frontend: **100%** (13/13 required dashboard test IDs + 7/7 regression pages).
     - Confirmed: copy buttons do not trigger runtime error overlays.

**Exit criteria (met)**
- ✅ All guardrail tests pass.
- ✅ Full platform regression passes (no MVP breakage).

---

## Next Actions (Immediate)
**None required for implementation. Feature is production-ready.**

Recommended operational next steps (human/admin):
1. Run enrichment sessions **manually** only when you have a fresh `MCA_SESSION_COOKIE`.
2. Use the **Admin → MCA Enrichment** dashboard for:
   - remaining count
   - next allowed session time
   - copy/paste commands
   - recent session stop reasons

---

## Success Criteria
- ✅ **No automatic MCA scraping** runs in APScheduler; classification continues.
- ✅ Manual scripts enforce: **cookie required**, **3/day cap**, **≥3h gap**, **≤110m budget**, stop on CAPTCHA/session expiry.
- ✅ Admin dashboard provides **clear progress + safe operating instructions + copy commands**.
- ✅ Full regression tests pass (backend + frontend).

---

## Notes / Artifacts
- Backend progress endpoint: `GET /api/v1/admin/enrichment-progress`
- Dashboard route: `/admin/enrichment` (protected)
- Key files:
  - `/app/backend/services/run_enrichment_session.py`
  - `/app/backend/services/retry_failed_enrichment.py`
  - `/app/backend/services/session_tracker.py`
  - `/app/backend/services/enrichment_queue.py`
  - `/app/backend/services/scheduler.py`
  - `/app/backend/routers/admin.py`
  - `/app/frontend/src/pages/AdminEnrichment.js`
  - `/app/frontend/src/lib/api.js`
  - `/app/frontend/src/lib/nav.js`
- Test report: `/app/test_reports/iteration_2.json`
- Note: testing agent updated `backend_test.py` (test harness only).