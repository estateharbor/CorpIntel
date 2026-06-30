# CorpIntel India — MCA Enrichment Batch Runner (Human-in-the-loop) + LLP Support Plan (UPDATED)

## Objectives
- Deliver a **manual, resumable, session-aware** MCA enrichment runner that **never auto-loops** and enforces guardrails (**3 sessions/day**, **≥3h gap**, **≤110m budget**, circuit breakers for **CAPTCHA/session expiry**).
- Provide an **Admin Enrichment Dashboard** to monitor queue progress and guide the operator with **copy/paste terminal commands**.
- Ensure **all background/scheduled MCA enrichment is disabled** (prevents bans and preserves queue accuracy). Background jobs may continue for **classification only**.
- Extend the platform to support **LLPs alongside Companies** via a generic identifier model (CIN/LLPIN), starting with **Phase 1: CSV upload + entity schema**.
- Maintain backward compatibility: existing “company” flows that query by `cin` continue to work for Company docs.

**Current status:**
- ✅ **MCA human-in-the-loop enrichment runner**: complete, tested, production-ready.
- ✅ **LLP Support — Phase 1 (CSV upload + entity data model)**: complete, tested.
- ⏳ **LLP Support — Phase 2 (entity-aware enrichment + frontend & API updates)**: pending **user review/go-ahead**.

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
   - Clipboard copy wrapped with **try/catch + fallback** to avoid runtime overlays.
   - 5-step instruction panel.
   - Recent sessions table + stop-reason badges.
   - Hard-stop banner for `captcha`, `session_expired`, `consecutive_failures`.
2. **Added API helper** in `frontend/src/lib/api.js`:
   - `getEnrichmentProgress()` → calls `/api/v1/admin/enrichment-progress`.
3. **Wired routing + nav**:
   - Protected route: `/admin/enrichment` in `App.js`.
   - Sidebar nav item: `nav-admin-enrichment` in `lib/nav.js`.
   - Added testId registry: `constants/testIds/adminEnrichment.js` and re-exported in `constants/testIds/index.js`.

**Verification**
- Build check (esbuild) ✅
- Visual verification (screenshot) ✅
- `testing_agent_v3` iteration_2 ✅ (backend + frontend 100%)

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
     - Backend: **100% (36/36)**.
     - Frontend: **100%**.

**Exit criteria (met)**
- ✅ All guardrail tests pass.
- ✅ Full platform regression passes.

---

## LLP SUPPORT — Phase 1 (CSV Upload + Entity Data Model)
**Goal:** Support importing and storing LLPs alongside Companies without breaking existing CIN-based behavior.

### What changed (implemented + tested)
#### A) Schema additions (companies collection, backward compatible)
- Added fields (all docs):
  - `entity_type`: "Company" | "LLP"
  - `identifier`: CIN or LLPIN (new primary key)
  - `identifier_type`: "CIN" | "LLPIN"
  - `llpin` (for LLP rows)
  - `total_contribution` (LLP-specific)
- Kept existing `cin` field populated for Company docs.
- LLP docs have `cin=null` and are keyed by `identifier` (LLPIN).

#### B) Index + migration strategy (critical)
- Backfilled all legacy documents (600) to:
  - `entity_type="Company"`, `identifier=cin`, `identifier_type="CIN"`
- Converted `cin` unique index to **partial unique**:
  - unique on `cin` only where `entity_type == "Company"`
  - prevents collision on LLP docs with `cin=null`
- Added indexes:
  - `companies.identifier` unique
  - `companies.entity_type`
  - `companies.llpin` (sparse)
- Added new collection `partners`:
  - `partners.dpin` unique
  - `partners.llpin`

#### C) Backend CSV upload service
- Added `/app/backend/services/csv_upload.py`:
  - Flexible header aliasing (case/space-insensitive)
  - Dual CIN/LLPIN validation per spec
  - Upsert by `identifier`
  - LLP `total_contribution` → `paid_up_capital` mapping for cohort filtering + store original `total_contribution`
  - Preserves enrichment/classification state via `$setOnInsert`
  - Returns summary broken down by entity type:
    - `companies_inserted`, `companies_updated`, `llps_inserted`, `llps_updated`, `rejected_count`, `rejected_rows` (row numbers + reasons)

#### D) Backend API endpoint
- Added `POST /api/v1/admin/upload-csv` (multipart form `file`):
  - 25MB cap
  - Strictly rejects non-CSV uploads with `400`

#### E) Frontend UI
- Added a **Data Upload card** to the Admin MCA Enrichment page:
  - Drag/drop + file picker
  - Upload action + toast notifications
  - Result panel with stat pills + rejected-rows table
  - “CSV template” download
  - Test IDs added for automation

### Verification (executed)
- Curl tests: insert/update/reject behavior; LLP mapping verified; indexes verified.
- UI tests: `set_input_files` + upload + result panel rendering.
- `testing_agent_v3` iteration_3:
  - Frontend: 100%
  - Backend: originally 7/8 due to a LOW validation issue, then ✅ fixed and re-verified (`text/plain` now returns 400).
- All test-uploaded records cleaned (DB returned to 600 baseline).

**Exit criteria (met)**
- ✅ Platform stores Company + LLP rows safely with correct uniqueness constraints.
- ✅ Admin can upload CSV and see a clear summary + rejected rows.
- ✅ No regressions to existing Company/CIN flows.

---

## LLP SUPPORT — Phase 2 (Pending — awaiting user go-ahead)
**Goal:** Make the entire platform entity-aware (search, detail pages, enrichment, analytics) while maintaining backward compatibility.

### Backend
1. **Entity-aware enrichment queue**
   - Update `services/enrichment_queue.py`:
     - `get_next_batch(limit=400, entity_type=None)`
     - `get_failed_batch(limit=400, entity_type=None)`
     - Include `entity_type` filtering when requested.

2. **Entity-aware MCA scraper**
   - Update `services/mca_scraper.py`:
     - Introduce `scrape_entity(identifier, entity_type, cookie)` router.
     - Keep existing `scrape_company_cin()` logic.
     - Implement new `scrape_llp(llpin)`:
       - Research MCA LLP master-data URL/page structure
       - Parse “Designated Partners”
       - Save partners to `partners` collection (dpin unique, llpin indexed)
     - Maintain honest blocked behavior in this environment (stop on CAPTCHA/session expiry).

3. **Companies router adjustments**
   - Ensure detail lookup can resolve by `identifier` (not only `cin`) so LLP detail pages work.
   - Add endpoint: `GET /companies/{identifier}/partners`.
   - Add `entity_type` filter support to list/search endpoints:
     - `/companies?entity_type=Company|LLP|Both`
     - advanced search body includes entity_type.

### Frontend (React SPA)
1. **Search page (`/frontend/src/pages/Search.js`)**
   - Add entity-type filter: Company | LLP | Both (default Both).
   - Add entity type badge on result cards:
     - Company = blue
     - LLP = purple

2. **Detail page (`/frontend/src/pages/CompanyDetail.js`)**
   - Route continues as `/company/:cin` but treats param as **identifier**.
   - If entity is LLP:
     - Directors tab relabel → “Designated Partners”
     - Fetch from partners endpoint
     - Overview shows “Total contribution” instead of paid-up/authorized capital

3. **Analytics (`/frontend/src/pages/Analytics.js`)**
   - Add Company vs LLP breakdown as a dimension/filter in charts and/or KPI modules.

**Exit criteria (Phase 2)**
- LLPs are searchable, viewable in detail pages, and display partners.
- Enrichment runner can enrich both Companies and LLPs (manual cookie + same guardrails).
- Analytics supports entity-type breakdown.

---

## Next Actions (Immediate)
1. **User review** of Phase 1 LLP upload + schema changes.
2. If approved: start **LLP Phase 2** (entity-aware enrichment + API + frontend).

---

## Success Criteria
### Enrichment runner
- ✅ **No automatic MCA scraping** runs in APScheduler; classification continues.
- ✅ Manual scripts enforce: **cookie required**, **3/day cap**, **≥3h gap**, **≤110m budget**, stop on CAPTCHA/session expiry.
- ✅ Admin dashboard provides **clear progress + safe operating instructions + copy commands**.
- ✅ Full regression tests pass.

### LLP support
- ✅ Phase 1: import + schema + indexes + UI upload complete and safe.
- ⏳ Phase 2: end-to-end entity-aware product behavior (search/detail/analytics/enrichment).

---

## Notes / Artifacts
- Backend progress endpoint: `GET /api/v1/admin/enrichment-progress`
- CSV upload endpoint: `POST /api/v1/admin/upload-csv` (multipart form-data: `file`)
- Dashboard route: `/admin/enrichment` (protected)
- Key new/updated files:
  - `/app/backend/services/csv_upload.py`
  - `/app/backend/services/ingestion.py` (ensure_indexes migration + entity-aware indexes)
  - `/app/backend/routers/admin.py` (upload endpoint)
  - `/app/backend/models.py` (Partner + upload models)
  - `/app/frontend/src/components/admin/DataUploadCard.js`
  - `/app/frontend/src/pages/AdminEnrichment.js` (upload card embedded)
  - `/app/frontend/src/lib/api.js` (uploadCsv helper)
  - `/app/frontend/src/constants/testIds/adminEnrichment.js` (DATA_UPLOAD test IDs)
- Test reports:
  - `/app/test_reports/iteration_2.json` (enrichment runner/dashboard)
  - `/app/test_reports/iteration_3.json` (CSV upload + LLP Phase 1; low-priority bug fixed afterward)

**Implementation note:** The original LLP addendum referenced Next.js/TS paths; implementation was correctly adapted to this project’s actual **React SPA (JS)** structure and backend `db.py`/`services/ingestion.py` indexing system.
