# CorpIntel India — MCA Enrichment Batch Runner (Human-in-the-loop) Plan

## Objectives
- Deliver a **manual, resumable, session-aware** MCA enrichment runner that **never auto-loops** and enforces guardrails (3 sessions/day, 3h min gap, 110m budget, CAPTCHA/session-expiry circuit breakers).
- Provide an **Admin Enrichment Dashboard** to monitor progress and guide the operator with copy-paste commands.
- Remove all background/scheduled MCA enrichment to prevent bans and to keep the manual queue accurate.
- Validate core guardrails in isolation (POC), then ship the V1 UI + API, then run full regression tests.

---

## Phase 1 — Core Guardrail POC (Isolation)
**User stories (core):**
1. As an operator, I want the session runner to **STOP** if `MCA_SESSION_COOKIE` is missing so I don’t accidentally trigger block behavior.
2. As an operator, I want the runner to **STOP** after 3 sessions/day so I stay within safe limits.
3. As an operator, I want the runner to **STOP** if the last session was <3 hours ago so I don’t run sessions too close together.
4. As an operator, I want the runner to **STOP** on CAPTCHA/session-expired signals so it never brute-forces through blocks.
5. As an operator, I want every session start/end to be logged so I can resume confidently and audit behavior.

**Steps**
1. **Web search (best practices)**
   - Quick research: “human-in-the-loop scraper guardrails session budgeting circuit breaker best practices”
   - Confirm recommended patterns: strict caps, explicit operator action, stop-on-challenge.
2. **POC: verify script-level guardrails via terminal (no real scraping)**
   - Run `python backend/services/run_enrichment_session.py` with no cookie → expect `STOP: No session cookie set...`.
   - Insert a dummy cookie and simulate session limits via DB writes:
     - Create 3 `enrichment_sessions` records with today’s IST start times → expect daily-cap STOP.
     - Create 1 “recent” session <3 hours ago → expect min-gap STOP.
   - Verify `session_tracker.next_session_available_at()` produces correct UTC timestamp.
3. **Document expected STOP messages** (for testing agent + operator clarity).

**Exit criteria**
- Guardrails produce deterministic STOP outputs for: missing cookie, daily cap, min-gap.
- Session logs are written to `enrichment_sessions` as expected.

---

## Phase 2 — V1 App Development (Backend + Frontend)
**User stories (dashboard + ops):**
1. As an admin, I want to see **overall queue progress** (total/remaining/enriched/failed) so I know how much work is left.
2. As an admin, I want to see **session governance status** (sessions today, next allowed start time) so I don’t violate rules.
3. As an admin, I want a **copy-command helper** so I can run the correct script safely without mistakes.
4. As an admin, I want to see **recent sessions** and stop reasons so I can react to CAPTCHA/expiry.
5. As an admin, I want the system to **never auto-run MCA enrichment** so manual control is guaranteed.

### 2A. Backend
1. **Add `GET /api/v1/admin/enrichment-progress`** in `backend/routers/admin.py`:
   - Return:
     - Priority cohort totals: total, enriched, remaining, attempted_failed, permanently_failed (attempts>=3)
     - Sessions today count, max/day, min-gap, batch size, time budget
     - Last session summary (type, started_at, ended_at, stop_reason, enriched_count, failed_count)
     - `next_session_available_at` (UTC ISO) + human-readable IST string
     - Recommended terminal commands (exact strings):
       - `cd /app/backend/services && python run_enrichment_session.py`
       - `cd /app/backend/services && python retry_failed_enrichment.py`
     - Safety note flags: `auto_enrichment_disabled: true`
2. **Disable automatic MCA enrichment in `services/scheduler.py`**:
   - Remove/disable the part that calls `enrich_company()`.
   - Keep only the classification loop.
   - Ensure job_runs logging reflects classification counts only.
3. **Restart backend and verify via curl**:
   - `curl /api/v1/admin/enrichment-progress` returns expected JSON.

### 2B. Frontend
1. **Create `/frontend/src/pages/AdminEnrichment.js`** (shadcn UI, data-testid everywhere):
   - KPI cards: remaining, enriched, failed, sessions today.
   - Progress bar: `enriched / total` for priority cohort.
   - Governance panel:
     - Next session allowed time
     - Min-gap and daily cap reminders
     - Last stop reason banner (warning styling if captcha/session_expired/consecutive_failures)
   - Instruction panel (step-by-step):
     - How to obtain cookie manually
     - Where to export `MCA_SESSION_COOKIE`
     - What STOP messages mean
   - **Copy command helper** buttons (copy to clipboard + toast):
     - Run enrichment session
     - Retry failed session
   - Recent sessions table.
2. **Add API helper** in `frontend/src/lib/api.js`:
   - `export const getEnrichmentProgress = () => api.get('/admin/enrichment-progress').then(r=>r.data)`
3. **Wire routing + nav**:
   - Add route in `App.js` (under AppShell): `/admin/enrichment`.
   - Add nav item in `lib/nav.js` (label: “Admin · Enrichment”).
   - (If needed) keep it visible; optionally gate via presence of user plan/admin later.
4. **Frontend verification**
   - Build/console check for lint/runtime errors.
   - Provide screenshot-based visual confirmation.

**Exit criteria**
- Endpoint exists and returns correct progress/session metadata.
- Scheduler no longer performs any MCA enrichment attempts.
- Admin dashboard loads, renders progress, and copy-command buttons work.

---

## Phase 3 — Testing & Validation
**User stories (quality/regression):**
1. As an operator, I want a backend STOP behavior test so I’m confident the runner won’t run unsafely.
2. As an admin, I want the dashboard to show accurate counts so I can make decisions.
3. As a developer, I want automated end-to-end tests to catch regressions in core SaaS flows.
4. As an operator, I want the UI to remain usable on mobile so I can monitor sessions anywhere.
5. As a maintainer, I want failures to be observable (stop reasons, failed counts) so debugging is fast.

**Steps**
1. **Manual terminal tests (no real MCA scraping):**
   - Missing cookie STOP.
   - Daily cap STOP (pre-create session logs).
   - Min-gap STOP.
2. **Testing agent run (full regression):**
   - Run `testing_agent_v3` to verify:
     - New route navigable
     - Dashboard renders without errors
     - API endpoint responds
     - Existing MVP pages still pass.
3. **Fix loop**
   - Address any issues reported by the testing agent, re-run once.

**Exit criteria**
- All guardrail tests pass.
- Testing agent passes without breaking existing MVP.

---

## Next Actions (Immediate)
1. Implement `GET /api/v1/admin/enrichment-progress` in `backend/routers/admin.py`.
2. Update `backend/services/scheduler.py` to remove auto `enrich_company()` calls.
3. Add `getEnrichmentProgress()` to `frontend/src/lib/api.js`.
4. Build `frontend/src/pages/AdminEnrichment.js` + route + nav.
5. Run terminal guardrail checks + `testing_agent_v3`.

---

## Success Criteria
- **No automatic MCA scraping** runs in APScheduler; only classification continues.
- Manual scripts enforce: **cookie required**, **3/day cap**, **3h gap**, **110m budget**, and stop on CAPTCHA/session expiry.
- Admin dashboard provides **clear progress + safe operating instructions + copy commands**.
- Full platform regression tests pass (no MVP breakage).