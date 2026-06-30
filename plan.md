# CorpIntel India — MCA Enrichment Batch Runner (Human-in-the-loop) + LLP Support Plan (UPDATED)

## Objectives
- Deliver a **manual, resumable, session-aware** MCA enrichment runner that **never auto-loops** and enforces guardrails (**3 sessions/day**, **≥3h gap**, **≤110m budget**, circuit breakers for **CAPTCHA/session expiry**).
- Provide an **Admin Enrichment Dashboard** to monitor queue progress and guide the operator with **copy/paste terminal commands**.
- Ensure **all background/scheduled MCA enrichment is disabled** (prevents bans and preserves queue accuracy). Background jobs may continue for **classification only**.
- Extend the platform to support **LLPs alongside Companies** via a generic identifier model (CIN/LLPIN), including:
  - **Phase 1**: CSV upload + entity schema
  - **Phase 2**: entity-aware search, detail pages (partners), analytics, and enrichment plumbing
- Provide a **production-safe, memory-safe, timeout-safe** CSV upload pipeline that supports **large master-data CSVs (3–5 lakh rows)** without **Cloudflare/origin timeouts** or **pod OOM**.
- Maintain backward compatibility: existing “company” flows that query by `cin` continue to work for Company docs.

**Current status:**
- ✅ **MCA human-in-the-loop enrichment runner**: complete, tested, production-ready.
- ✅ **Admin Enrichment Dashboard**: complete, tested.
- ✅ **Auto MCA enrichment disabled** in APScheduler: complete, verified.
- ✅ **LLP Support — Phase 1 (CSV upload + entity data model)**: complete, tested.
- ✅ **Sample data fully removed + auto-reseed disabled**: complete, verified.
- ✅ **Upload size support**: increased to **150MB**; nginx `client_max_body_size` set to **160m**.
- ✅ **OOM during large CSV upload**: resolved via **streaming + batched bulk_write**.
- ✅ **Cloudflare 520 / timeout on large CSV uploads**: resolved via **async background-job upload pattern** (job_id + polling). Verified by `testing_agent_v3`.
- ✅ **LLP Support — Phase 2 (entity-aware enrichment + frontend & API updates)**: **complete, tested (29/29 pass, zero bugs)**.

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

#### C) Backend CSV upload service core logic
- `/app/backend/services/csv_upload.py`:
  - Flexible header aliasing (case/space-insensitive)
  - Dual CIN/LLPIN validation per spec
  - Upsert by `identifier`
  - LLP `total_contribution` → `paid_up_capital` mapping for cohort filtering + keep original `total_contribution`
  - Preserves enrichment/classification state via `$setOnInsert`
  - Batch upserts via **unordered `bulk_write`** with `UpdateOne(..., upsert=True)` in batches of **1000**

#### D) Sample-data purge + reseed guard
- Added `POST /api/v1/admin/purge-sample`:
  - Deletes all docs labeled `data_source="sample"` + related directors/enrichment/alerts
  - Sets persistent marker `system_config.ingest.sample_seed_disabled=true`
- Updated backend startup (`server.py`) to respect the marker and **skip any auto sample reseeding**

#### E) Deployment request-body limit
- Updated `deploy/nginx.conf`: `client_max_body_size 160m`

### Verification (executed)
- Curl tests: insert/update/reject behavior; LLP mapping verified; indexes verified.
- UI tests: upload + summary rendering.
- `testing_agent_v3` iteration_3:
  - Frontend: 100%
  - Backend: passed after tightening non-CSV validation

**Exit criteria (met)**
- ✅ Platform stores Company + LLP rows safely with correct uniqueness constraints.
- ✅ Admin can upload CSV and see a clear summary + rejected rows.
- ✅ No regressions to existing Company/CIN flows.

---

## FIX — Large CSV Upload Cloudflare 520 / Timeout (Background Job Pattern)
**Problem:** Uploading large master-data CSVs (3–5 lakh rows) caused Cloudflare 520 due to synchronous parsing/upsert inside one request.

### What changed (implemented + tested)
#### A) New collection: `upload_jobs`
- Stores upload job lifecycle + progress:
  - `job_id` (unique, indexed)
  - `filename`
  - `status`: `queued | processing | completed | failed`
  - `total_rows`, `processed_rows`
  - `inserted_count`, `updated_count`
  - `rejected_count`, `rejected_rows`
  - `duplicate_within_file_count`
  - Breakdown: `companies_inserted/updated`, `llps_inserted/updated`
  - `error_message`, `created_at`, `started_at`, `completed_at`

#### B) Non-blocking submit endpoint
- `POST /api/v1/admin/upload-csv` now:
  - streams file to temp disk in **1MB chunks** (150MB cap)
  - inserts an `upload_jobs` record with `status="queued"`
  - launches an asyncio background task
  - **returns immediately** with `{job_id, status:"queued"}` (no parsing in request)

#### C) Background worker (chunked + progress updates)
- `services/csv_upload.process_upload_job(db, job_id, temp_path)`:
  - line-by-line CSV parsing
  - validation: CIN/LLPIN, required fields
  - **duplicate-within-file** detection (`seen` set)
  - batched unordered `bulk_write` (1000/batch)
  - updates `upload_jobs` after each batch so UI can poll real-time
  - sets `status="completed"` with full summary or `status="failed"` with `error_message`
  - deletes the temp file in `finally`

#### D) Progress polling endpoint
- `GET /api/v1/admin/upload-csv/{job_id}/status`:
  - returns the job doc
  - `404` for unknown job_id

#### E) Index updates
- `ensure_indexes` now adds:
  - `upload_jobs.job_id` unique
  - `upload_jobs.created_at`

#### F) Frontend (Admin Enrichment → Data Upload card)
- Submit now:
  - calls POST `/admin/upload-csv`
  - immediately shows a **progress panel** (non-blocking) with progress bar + running counts
  - polls status every **2.5s** via `getUploadStatus(jobId)`
  - on `completed`: shows full summary panel + stops polling
  - on `failed`: shows error + retry

### Verification (required + completed)
- ✅ `testing_agent_v3` iteration_4: Backend **100% (11/11)**, Frontend **100%**
  - Large CSV (100k rows): submit returned in **0.67s**, job completed in **10.4s** via polling
  - Validation counts correct (CIN/LLPIN/duplicate/rejected)
  - Re-upload → updates
  - Non-CSV → 400, unknown job → 404
  - No frontend runtime errors; dashboard regression OK

### Cleanup notes
- Removed **102,008** synthetic test records (identifier patterns: `^U00000`, `MH2099PTC`, `^ZZT-`), with **0 leftovers**.
- User real dataset left intact: **399,248** entities (data_source=`csv_upload`).

**Exit criteria (met)**
- ✅ Upload submit returns quickly (timeout-safe).
- ✅ Background processing provides real-time progress.
- ✅ Large uploads complete without Cloudflare 520.

---

## LLP SUPPORT — Phase 2 (Entity-aware Product Behavior)
**Goal:** Make the platform fully entity-aware (search, detail pages, enrichment, analytics) while maintaining backward compatibility.

### 2A) Backend (Implemented + Tested)
1. **Entity-aware query building** (`/app/backend/common.py`)
   - `build_company_query()` now supports `entity_type` filtering.
   - Search `$or` now includes `identifier` (supports CIN + LLPIN).
   - `attach_director_counts()` is entity-aware:
     - Companies → counts `directors` by CIN
     - LLPs → counts `partners` by LLPIN
     - null-cin safe.

2. **Companies router adjustments** (`/app/backend/routers/companies.py`)
   - Entity lookup resolves by **identifier OR cin** (`_find_entity` uses `$or`).
   - `GET /companies/{identifier}` works for CIN or LLPIN.
   - Added: `GET /companies/{llpin}/partners` returning `{llpin, count, partners}`.
   - List endpoint supports `entity_type` query param.
   - Similar entities works for both Company/LLP (identifier-based; no crash on null CIN).

3. **Entity-aware enrichment queue + persistence** (`/app/backend/services/enrichment_queue.py`)
   - `get_next_batch(limit=400, entity_type=None)` and `get_failed_batch(..., entity_type=None)`.
   - `mark_enriched` / `mark_failed` keyed by `identifier`.
   - `save_enrichment_data(identifier, data, entity_type)`:
     - Companies → upsert `directors` by DIN + CIN.
     - LLPs → upsert `partners` by DPIN + LLPIN.

4. **Entity-aware MCA scraping** (`/app/backend/services/mca_scraper.py`)
   - Added LLP endpoint constant + `_parse_llp_page()`.
   - Implemented `scrape_llp(llpin)` (parses Designated Partners) + `scrape_entity(identifier, entity_type, cookie)` router.
   - Maintains honest blocked behavior (CAPTCHA/session expiry stop semantics).

5. **Session runner updated** (`/app/backend/services/run_enrichment_session.py`)
   - Uses `scrape_entity()` and persists data entity-aware.
   - Batch can contain mixed Companies + LLPs.

6. **Analytics + models + search suggestions updated**
   - `analytics.py`: `by_entity_type`, `companies_count`, `llps_count` (honors city filter).
   - `models.py`: `AdvancedSearchRequest.entity_type`, `ExportRequest.entity_type`.
   - `search.py`: suggestions include `entity_type` and expose the generic identifier in the `cin` field for compatibility.

### 2B) Frontend (Implemented + Tested)
1. **Entity type badge**
   - Added `EntityBadge` component:
     - Company = blue
     - LLP = purple

2. **Search page** (`/frontend/src/pages/Search.js`)
   - Added entity-type filter select: All / Companies / LLPs.
   - Company cards now render entity badge.

3. **Cards + routing**
   - `CompanyCard` links by `identifier || cin` to avoid LLP null-cin broken links.
   - Card labels adapt: “directors” vs “partners”; LLP uses `total_contribution`.

4. **Entity-aware detail page** (`/frontend/src/pages/CompanyDetail.js`)
   - Route param is treated as a generic identifier (CIN or LLPIN).
   - If LLP:
     - “Directors” tab relabels to “Designated Partners”
     - Fetches partners via `/companies/{llpin}/partners`
     - Overview uses “LLPIN” and “Total contribution” (hides authorized/paid-up)
   - If Company:
     - Standard Directors flow
     - Overview includes Authorized/Paid-up capital

5. **Analytics** (`/frontend/src/pages/Analytics.js`)
   - Added “Company vs LLP” breakdown card (tiles + split bar) using `/analytics/summary`.

### Verification (required + completed)
- ✅ `testing_agent_v3` iteration_5: **100% overall (29/29)**
  - Backend: **100% (19/19)**
  - Frontend: **100% (10/10)**
  - Confirmed real dataset counts intact: **306,045 Companies + 93,203 LLPs**.
  - No regressions across dashboard/export/enrichment.

**Exit criteria (met)**
- ✅ LLPs are searchable and filterable.
- ✅ LLP detail pages render correctly (Partners + Total contribution).
- ✅ Analytics supports company-vs-LLP breakdown.
- ✅ Manual enrichment runner supports both Companies + LLPs (same guardrails).

---

## Next Actions (Optional Enhancements)
1. **Date normalization on import (optional; out-of-scope observation)**
   - Registration trend chart may appear sparse if uploaded `date_of_incorporation` formats were inconsistent.
   - Potential improvement: enhance CSV date parser, log date-parse rejects, and optionally backfill/normalize.
2. **Upload-job operations hardening (optional)**
   - Job cancellation endpoint
   - Retention/cleanup policy for `upload_jobs`
   - Concurrency limiting (e.g., one job at a time)

---

## Success Criteria
### Enrichment runner
- ✅ **No automatic MCA scraping** runs in APScheduler; classification continues.
- ✅ Manual scripts enforce: **cookie required**, **3/day cap**, **≥3h gap**, **≤110m budget**, stop on CAPTCHA/session expiry.
- ✅ Admin dashboard provides **clear progress + safe operating instructions + copy commands**.
- ✅ Full regression tests pass.

### LLP support
- ✅ Phase 1: import + schema + indexes + upload UI complete.
- ✅ Large uploads are both **memory-safe** and **timeout-safe** (job_id + polling).
- ✅ Phase 2: end-to-end entity-aware product behavior (search/detail/analytics/enrichment).

---

## Notes / Artifacts
- Backend progress endpoint: `GET /api/v1/admin/enrichment-progress`
- CSV upload submit endpoint: `POST /api/v1/admin/upload-csv` (multipart: `file`, returns `{job_id}`; max 150MB)
- CSV upload status endpoint: `GET /api/v1/admin/upload-csv/{job_id}/status`
- Purge sample endpoint: `POST /api/v1/admin/purge-sample`
- Dashboard route: `/admin/enrichment` (protected)

### Key new/updated files (high signal)
- `/app/backend/common.py` (entity_type filtering + entity-aware people counts)
- `/app/backend/routers/companies.py` (identifier-based lookup + /partners)
- `/app/backend/routers/analytics.py` (entity-type breakdown)
- `/app/backend/routers/search.py` (suggestion payload includes entity_type)
- `/app/backend/services/enrichment_queue.py` (identifier-keyed + partners persistence)
- `/app/backend/services/mca_scraper.py` (scrape_llp + scrape_entity)
- `/app/backend/services/run_enrichment_session.py` (entity-aware scraping + persistence)
- `/app/backend/services/csv_upload.py` (background job worker)
- `/app/backend/services/ingestion.py` (upload_jobs indexes)
- `/app/backend/routers/admin.py` (async upload submit + status endpoint)
- `/app/frontend/src/components/EntityBadge.js`
- `/app/frontend/src/components/CompanyCard.js`
- `/app/frontend/src/pages/Search.js`
- `/app/frontend/src/pages/CompanyDetail.js`
- `/app/frontend/src/pages/Analytics.js`

### Test reports
- `/app/test_reports/iteration_2.json` (enrichment runner/dashboard)
- `/app/test_reports/iteration_3.json` (CSV upload + LLP Phase 1)
- `/app/test_reports/iteration_4.json` (Cloudflare 520 fix verification)
- `/app/test_reports/iteration_5.json` (**LLP Phase 2 verification: 29/29 pass**)

**Implementation note:** The original LLP addendum referenced Next.js/TS paths; implementation was correctly adapted to this project’s actual **React SPA (JS)** structure and backend `db.py`/`services/ingestion.py` indexing system.
