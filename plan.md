# CorpIntel India — plan.md (UPDATED)

## 1) Objectives
- Confirm the platform is **complete, working, and production-ready as a v1**: data ingestion (seed), city tagging, MongoDB storage/indexing, AI classification (Claude + fallback), search/analytics, exports, alerts, auth, and payments.
- Ensure **all integrations are env-var only** (no hardcoded secrets) using:
  - `ANTHROPIC_API_KEY` (Claude sector classification)
  - `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` (Stripe)
  - `DATA_GOV_API_KEY` (data.gov.in ingestion)
  - plus existing `MONGO_URL`, `DB_NAME`, `REACT_APP_BACKEND_URL`
- Provide **honest scraper modules** (MCA/GST/JustDial/IndiaMart) that implement the contract (rate-limit/retry/backoff/block detection) and **report blocked status** in CAPTCHA/IP-block environments.
- Deliver a **polished UI** (Inter + Sora, navy `#1E3A5F`, saffron `#F4A620`, mobile-first, dark mode) with all specified pages and data-dense dashboard experiences.
- Provide delivery artifacts for portability: `docker-compose.yml`, `.env.example`, Dockerfiles, nginx config, seed script, and README.

**Current status:** ALL PHASES COMPLETE; full app built, verified, and tested.

---

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation) (✅ COMPLETE)
**Core = ingest → city-tag → MongoDB upsert/index → sector classification → query.**

**Web research / validation (✅ COMPLETE)**
- Confirmed data.gov.in API patterns and located resource UUID:
  - `4dbe5667-7b6b-41d7-82af-211562424d9a` (requires registered key; public sample key not authorized).
- Confirmed real-world scraping constraints:
  - `mca.gov.in` returns HTTP 403 in this environment → validates CAPTCHA/anti-bot reality and need for blocked-flag design.
- Confirmed Anthropic model/tool-use approach and integrated via official SDK (env-var key).

**POC build — `backend/scripts/test_core.py` (✅ COMPLETE)**
- Implemented `city_tagger` with exact MMR locality lists + priority order.
- Implemented `DataGovInClient`:
  - Correct request formation for the UUID with `DATA_GOV_API_KEY`
  - Graceful handling for missing/unauthorized key.
- Implemented labeled SAMPLE dataset fallback (deterministic generator) + idempotent upsert.
- Created MongoDB collections + required indexes (unique CIN, text index, city/date/activity indexes).
- Implemented classification:
  - Claude Tool-Use JSON classification when `ANTHROPIC_API_KEY` is set
  - Deterministic keyword fallback when key missing/fails
  - `classification_cache` keyed by principal activity.
- POC assertions verified:
  - Inserts companies; city counts present for Mumbai/Navi Mumbai/Thane
  - Query filters + search work
  - Classification returns valid sector + cached

**Exit criteria met:** `python -m scripts.test_core` passes.

**User stories (✅ fulfilled)**
1. Admin can seed without `DATA_GOV_API_KEY` (sample fallback).
2. City tagging supports Mumbai/Navi Mumbai/Thane reliably.
3. Classification works without Claude.
4. Duplicate CINs upsert cleanly.
5. Clear logs for missing/unauthorized keys.

---

### Phase 2 — V1 App Development (✅ COMPLETE)

#### Backend (FastAPI `/api` + `/api/v1`) (✅ COMPLETE & VERIFIED)
**Implemented project structure**
- `db.py`, `models.py`, `auth_utils.py`, `common.py`
- Routers: `auth`, `companies`, `analytics`, `search`, `export`, `alerts`, `admin`, `payments`
- Services: `city_tagger`, `sample_data`, `ingestion`, `classifier`, `enrichment`, `scheduler`, `stripe_service`

**Implemented endpoints (✅ COMPLETE)**
- Auth:
  - `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/magic-link`
  - `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`
  - Emergent Google session exchange: `POST /api/v1/auth/google/session`
  - Demo bypass (dev-only): `POST /api/v1/auth/demo-login` (controlled by `ALLOW_TEST_BYPASS`)
- Companies:
  - `GET /api/v1/companies` (filters, sort, pagination)
  - `GET /api/v1/companies/{cin}`
  - `/{cin}/directors`, `/{cin}/charges`, `/{cin}/filings`, `/{cin}/similar`, `/{cin}/contact`
- Analytics:
  - `GET /api/v1/analytics/summary`, `/trends`, `/sectors`, `/capital`, `/heatmap`
- Search:
  - `GET /api/v1/search`, `POST /api/v1/search/advanced`
  - `POST /api/v1/search/save`, `GET /api/v1/search/saved`, `DELETE /api/v1/search/saved/{id}`
- Export (real downloadable files):
  - `POST /api/v1/export/csv`, `/excel`, `/pdf`
- Alerts:
  - `POST /api/v1/alerts`, `GET /api/v1/alerts`, `PATCH /api/v1/alerts/{id}/toggle`, `DELETE /api/v1/alerts/{id}`, `GET /api/v1/alerts/log`
- Admin:
  - `GET /api/v1/admin/stats`, `POST /api/v1/admin/ingest/seed`, `POST /api/v1/admin/ingest/incremental`, `POST /api/v1/admin/enrich/{cin}`
- Payments:
  - `GET /api/v1/payments/plans`, `POST /api/v1/payments/checkout`, `GET /api/v1/payments/status/{session_id}`
  - Stripe webhook: `POST /api/webhook/stripe` (exact path required)

**Data + jobs (✅ COMPLETE)**
- Mongo indexes ensured on startup.
- Seed behavior:
  - If `DATA_GOV_API_KEY` set → ingest from data.gov.in
  - Else → seed clearly-labeled SAMPLE dataset (banner-driven sample_mode)
- APScheduler started with 4 IST jobs:
  - weekly_ingest (Mon 09:00 IST)
  - enrichment_worker (every 15 minutes)
  - alert_checker (08:00 IST daily)
  - data_quality_scorer (Sun 00:00 IST)

**Access control (✅ COMPLETE)**
- Free-tier search/day enforced (when search applied)
- Export limits enforced by plan
- Contact data gated to Pro+
- API key access gated to Pro+

#### Frontend (React + Tailwind + shadcn/ui + Recharts + React Query) (✅ COMPLETE)
- Implemented design system from `/app/design_guidelines.md`:
  - Tokens in `index.css` for light/dark, fonts (Inter body, Sora headings)
  - Palette: navy `#1E3A5F`, saffron `#F4A620`.
- App shell:
  - Sidebar + Topbar + QuickSearch command palette (Cmd+K)
  - Dark mode toggle
  - Sample Data Mode banner
- Pages/routes (✅ COMPLETE)
  - Landing `/`
  - Login `/login` + OAuth callback handling
  - Dashboard `/dashboard`
  - Search `/search`
  - Company Detail `/company/:cin` (5 tabs)
  - Analytics `/analytics`
  - Alerts `/alerts` (protected)
  - Export `/export` (protected)
  - Pricing `/pricing`
  - Settings `/settings` (protected)
- Components:
  - CompanyCard, FilterSidebar, StatusBadge/CityTag chips
  - Charts: RegistrationTrend, CityDistribution, SectorBreakdown, CapitalDistribution
  - Skeletons + toasts

**Bugfixes completed**
- Fixed JSX unicode escape rendering issue across 16 files (replaced `\u00b7`-style literals with actual characters).

**Testing (✅ COMPLETE)**
- `testing_agent_v3` iteration 1:
  - Backend: **100% pass (35/35)**
  - Frontend: **~95%** with **13/13 major flows working**
  - **Zero** critical/UI/integration/design bugs.

---

### Phase 3 — Auth + Subscriptions + Access Control (✅ COMPLETE & VERIFIED)

**Auth (✅ COMPLETE)**
- Email/Password JWT auth: register/login/me/logout.
- Magic link endpoint (dev mode: token returned/logged).
- Emergent managed Google Auth session exchange endpoint + frontend flow.
- Demo login bypass (`ALLOW_TEST_BYPASS=true`) for evaluation/testing.

**Stripe (✅ COMPLETE)**
- Test-mode checkout sessions via emergentintegrations.
- Plans configured server-side:
  - Starter ₹999/mo
  - Pro ₹2499/mo
  - Enterprise is contact-sales (no checkout)
- Webhook handler at `/api/webhook/stripe` updates user plan idempotently.
- Checkout status polling implemented in Settings (`session_id` handling).

**Enforcement middleware (✅ COMPLETE)**
- Search limits, export limits, Pro-gated contact data and API access.

**Verification completed**
- Checkout session creation returns URL/session_id (works with `sk_test_emergent` fallback).
- Exports blocked for Free, allowed for Pro demo.
- Contact endpoint locked/unlocked based on plan.

---

### Phase 4 — Hardening, Data Ops, and Delivery Artifacts (✅ COMPLETE)

**Portability artifacts delivered (✅ COMPLETE)**
- `docker-compose.yml` (frontend/backend/mongodb/redis/nginx)
- `.env.example` (all required variables)
- Dockerfiles:
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
- `deploy/nginx.conf` (routes `/api/*` to backend, rest to frontend)
- `scripts/seed.py`:
  - Seeds from data.gov.in when `DATA_GOV_API_KEY` is set, else sample
  - Prints city counts (verified: Mumbai 267, Navi Mumbai 174, Thane 159)
- `README.md` updated with run, env, testing, and data-source honesty notes.

**Honesty flags (✅ COMPLETE)**
- Sample dataset active until `DATA_GOV_API_KEY` injected; banner surfaces this.
- MCA/GST/JustDial/IndiaMart enrichment scrapers report blocked state under CAPTCHA/IP restrictions.

---

## 3) Next Actions
1. **Inject env vars via Secrets panel** (no changes required in code):
   - `DATA_GOV_API_KEY` to enable real data.gov.in ingestion
   - `ANTHROPIC_API_KEY` to enable live Claude classification
   - `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` to switch from test fallback to your Stripe account
2. Disable demo bypass for production:
   - Set `ALLOW_TEST_BYPASS=false`
3. (Optional) Expand beyond MMR:
   - Add additional city keyword lists and ingestion filters
4. (Optional) Email delivery integration:
   - Wire an email provider for magic links + alert digests (currently logged)

---

## 4) Success Criteria
- ✅ Core POC passes (ingest → tag → upsert/index → classify → query).
- ✅ V1 app: all pages, endpoints, exports, alerts, analytics, and company profiles working.
- ✅ Integrations activate solely via env vars; graceful fallback when missing.
- ✅ Scheduler jobs run without crashes and log results.
- ✅ End-to-end tests passed (Backend 35/35; Frontend flows verified).
- ✅ Delivery artifacts provided for self-hosted deployment.
