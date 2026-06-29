# CorpIntel India — plan.md

## 1) Objectives
- Prove the **core intelligence pipeline** works end-to-end: ingest → city-tag → store/index → classify sector → query/analytics.
- Deliver a full v1 SaaS app (React + FastAPI + MongoDB) with **all 9 routes**, exports, alerts, admin ingestion/enrichment jobs, and Stripe test subscriptions.
- Keep all integrations **env-var only** (no hardcoded secrets) using: `ANTHROPIC_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `DATA_GOV_API_KEY` (+ existing `MONGO_URL`, `DB_NAME`, `REACT_APP_BACKEND_URL`).
- Provide honest scraper modules (MCA/GST/JustDial/IndiaMart) with **CAPTCHA/IP-block flags** + resilient retry/rate-limit behavior.

## 2) Implementation Steps

### Phase 1 — Core POC (Isolation) (do not proceed until green)
**Core = real ingestion + city tagging + MongoDB upsert/index + sector classification (Claude/fallback) + query.**

**Web research (best practices / API shape validation)**
- Confirm data.gov.in API query patterns (resource UUID, filters, pagination) + typical error modes.
- Confirm Anthropic SDK usage + JSON-mode prompting patterns.

**POC build (single runnable test) — `backend/scripts/test_core.py`**
- Implement `city_tagger(address: str) -> {city, area, pin_code?}` with exact MMR locality lists + priority.
- Implement data.gov.in client:
  - Request formation for resource UUID `4dbe5667-7b6b-41d7-82af-211562424d9a` using `DATA_GOV_API_KEY`.
  - Graceful handling of missing/invalid key (“Key not authorised”) with clear logs.
- Implement fallback seed: load **clearly-labeled SAMPLE MMR dataset** (CSV/JSON in repo) and upsert.
- MongoDB setup:
  - Create collections + required indexes (cin unique, name text, city/date/activity indexes).
  - Upsert logic with dedupe, `last_updated`, `data_quality_score` default.
- Classification:
  - Anthropic classify call (if `ANTHROPIC_API_KEY` set) → strict JSON parse.
  - Rule-based keyword fallback (deterministic) when key missing/fails.
  - `classification_cache` keyed by principal activity (no reclass).
- POC assertions:
  - Inserts >0 companies; city counts for Mumbai/Navi Mumbai/Thane present from sample.
  - Query: filter by city + search term returns expected.
  - Classification returns sector for at least N records.

**Exit criteria (Phase 1)**
- `python backend/scripts/test_core.py` succeeds locally; logs show ingestion path works with/without `DATA_GOV_API_KEY`.

**User stories (Phase 1)**
1. As an admin, I want to seed companies even without a data.gov.in key so the app is demonstrable immediately.
2. As a user, I want companies auto-tagged as Mumbai/Navi Mumbai/Thane based on address so filters work.
3. As a user, I want sector classification to work even when Claude is unavailable so the product degrades gracefully.
4. As an admin, I want duplicate CINs to upsert cleanly so repeated ingests don’t corrupt data.
5. As a developer, I want clear logs for “key not authorised” so I can fix env setup quickly.

---

### Phase 2 — V1 App Development (core-first app, **auth/payments delayed**)
**Backend (FastAPI /api/v1 mounted under /api)**
- Project structure: `api/routers/*`, `services/*`, `models/*`, `db.py`, `scheduler.py`.
- Implement Pydantic models for all entities.
- Implement endpoints (MVP-complete):
  - Companies: list w/ filters + pagination, detail, directors/charges/filings, similar.
  - Analytics: summary, trends, sectors, capital, heatmap.
  - Search: simple + advanced + save/list saved searches.
  - Export: CSV/Excel/PDF generation as real downloadable files.
  - Alerts: CRUD + logs.
  - Admin: seed (data.gov.in if key else sample), incremental ingest trigger, enrich CIN trigger, stats.
- Implement background “queue” using MongoDB collection (e.g., `tasks`) for enrichment/classification work.
- Implement APScheduler jobs (run even if scraper sources blocked; log + skip gracefully):
  - weekly_ingest (Mon 9AM IST)
  - enrichment_worker (15 min, 50 CINs)
  - alert_checker (daily 8AM IST; store digest events; email sending can be stubbed to log for v1)
  - data_quality_scorer (Sun 00:00)
- Scraper modules:
  - Implement interfaces + rate-limit/retry/backoff/block detection.
  - Mark MCA/GST as “CAPTCHA/IP-block likely” and auto-disable unless explicitly enabled.

**Frontend (React CRA + Tailwind + shadcn/ui + Recharts + TanStack Query)**
- App shell: sidebar/topbar, dark mode toggle, responsive.
- Routes/pages:
  - Landing (/)
  - Dashboard (/dashboard)
  - Search (/search)
  - Company Detail (/company/:cin) with 5 tabs
  - Analytics (/analytics)
  - Alerts (/alerts)
  - Export (/export)
  - Pricing (/pricing)
  - Settings (/settings)
- Central API client using `REACT_APP_BACKEND_URL`.
- State handling: loading skeletons, error boundaries, toasts.
- Show “Sample Data Mode” banner when seeded from fallback (server-provided flag).

**Testing (end of Phase 2)**
- Run testing_agent_v3: landing → search → company detail tabs → analytics charts → create alert → export file.

**User stories (Phase 2)**
1. As a user, I want to search companies by name/CIN and filter by city/sector/status/date.
2. As a user, I want a company detail view with directors/charges/filings so I can evaluate credibility.
3. As a user, I want analytics charts for new registrations and sector mix so I can spot trends.
4. As a user, I want to create alerts for “new companies in Navi Mumbai in FinTech” so I don’t miss leads.
5. As a user, I want to export my filtered results to CSV/Excel/PDF so I can share internally.

---

### Phase 3 — Auth + Subscriptions + Access Control (Google + Email/Password + Stripe)
**Auth (backend + frontend)**
- Email/Password JWT: register/login/me.
- Magic link endpoint (MVP: token-based link; delivery can be log-only if no email provider).
- Emergent managed Google Auth session endpoints + frontend sign-in.
- Secure test-bypass user:
  - Enable only when `ENV=development` or explicit `ALLOW_TEST_BYPASS=true`.
  - Adds a “Demo login” button for agent testing.

**Stripe (test mode)**
- Plans mapping (Free/Starter/Pro/Enterprise) + limits.
- Checkout session creation endpoint + success/cancel routes.
- Webhook handler verifying `STRIPE_WEBHOOK_SECRET`; update `users.plan`, `stripe_customer_id`.
- Billing portal endpoint from Settings.

**Enforcement middleware**
- Apply per-plan limits: searches/day, exports/month, contact visibility, API access.

**Testing (end of Phase 3)**
- testing_agent_v3: demo login → subscribe test → webhook simulated → plan changes reflected → limits enforced.

**User stories (Phase 3)**
1. As a user, I want to sign up with email/password so I can access saved searches and alerts.
2. As a user, I want Google login so I can onboard in one click.
3. As a user, I want to upgrade to Pro via Stripe so I can unlock contact data and exports.
4. As a user, I want my plan limits enforced clearly with upgrade prompts so I understand what to do.
5. As an admin, I want webhook-driven plan updates so billing status stays accurate.

---

### Phase 4 — Hardening, Data Ops, and Delivery Artifacts
- Improve ingestion controls: filters for ROC Mumbai, partial refresh, idempotent runs, metrics.
- Similar companies: hybrid matching (sector + activity keywords + city + capital band).
- Export polish: column templates, PDF styling.
- Add `scripts/seed.py` (data.gov.in + fallback) with summary output.
- Add portability artifacts: `docker-compose.yml`, `.env.example`, README.
- Final testing pass with testing_agent_v3 across all routes and critical flows.

**User stories (Phase 4)**
1. As an admin, I want repeatable seed scripts so I can refresh the dataset safely.
2. As a user, I want similar companies so I can discover more leads faster.
3. As a user, I want exports to be consistently formatted so stakeholders can read them.
4. As a developer, I want docker-compose + env examples so I can run it outside Emergent.
5. As a user, I want the app to remain usable even when external scrapers are blocked.

## 3) Next Actions
1. Implement Phase 1 `backend/scripts/test_core.py` + sample MMR dataset + Mongo indexes.
2. Run POC until all assertions pass (with and without `DATA_GOV_API_KEY`).
3. Build Phase 2 backend routes + frontend pages in one integrated pass; seed sample data by default.
4. Execute testing_agent_v3 on v1.
5. Add Phase 3 auth + Stripe + access control; re-run testing.

## 4) Success Criteria
- POC script passes and demonstrates: ingest → city tagging → Mongo upsert/index → sector classification → query.
- V1 app: all 9 routes functional; search/filters fast; company detail tabs populated; analytics charts render; alerts + exports work.
- Integrations: Anthropic/Stripe/data.gov.in activate solely via env vars; app behaves gracefully when vars missing.
- Scheduler jobs run without crashing and produce observable logs/results.
- End-to-end tests pass after each phase without regressions.
