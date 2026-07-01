# CorpIntel India

**India's most complete company intelligence platform** for the Mumbai Metropolitan Region (Mumbai · Navi Mumbai · Thane) — discover, analyze, track and export registered-company intelligence. Think *Zaubacorp meets Crunchbase meets a Bloomberg terminal* for Indian SME intelligence.

> Built on **React + FastAPI + MongoDB** (shadcn/ui, Tailwind, Recharts, TanStack Query). AI sector classification via **Anthropic Claude**. Subscriptions via **Stripe**. Auth via **Email/Password (JWT)**.

---

## Features

- **Data ingestion engine** — real `data.gov.in` Company Master Data (activates with `DATA_GOV_API_KEY`) + honest MCA / GST / JustDial / IndiaMart scraper modules (rate-limit, retry, IP-block detection). A clearly-labeled **SAMPLE MMR dataset** (600 companies) powers the app out-of-the-box.
- **City tagger** — classifies every address into Mumbai / Navi Mumbai / Thane / Other-Maharashtra (exact MMR locality lists).
- **AI sector classification** — Claude (`claude-sonnet-4-6`) with strict JSON tool-use; deterministic rule-based fallback; results cached per activity.
- **Search** — full-text + multi-filter (city, sector, status, class, date range, paid-up capital), sort, pagination, save searches.
- **Company profiles** — Overview, Directors, Charges, Filings, Contact (Pro-gated), Similar companies.
- **Analytics** — registration trends, city distribution, top sectors, capital distribution, area-density heatmap, sector table; per-city tabs.
- **Alerts** — track new companies by city + sector + min capital (daily/weekly).
- **Exports** — real **CSV**, **Excel** (sheet per city), **PDF** report files.
- **Subscriptions** — Free / Starter (₹999) / Pro (₹2499) / Enterprise with plan-based access control + Stripe checkout & webhook.
- **Background jobs (APScheduler, IST)** — weekly ingest, enrichment worker (every 15 min), daily alert checker (08:00), weekly data-quality scorer.
- **Polished UI** — navy `#1E3A5F` + saffron `#F4A620`, Inter + Sora, full **dark mode**, mobile-first, skeletons, toasts.

---

## Project structure

```
backend/
  server.py                # FastAPI app + startup (indexes, seed, scheduler)
  models.py  db.py  auth_utils.py  common.py
  routers/                 # auth, companies, analytics, search, export, alerts, admin, payments
  services/                # city_tagger, sample_data, ingestion, classifier, enrichment, scheduler, stripe_service
  scripts/test_core.py     # POC test for the core pipeline
frontend/src/
  pages/                   # Landing, Login, Dashboard, Search, CompanyDetail, Analytics, Alerts, Export, Pricing, Settings
  components/              # CompanyCard, FilterSidebar, charts/, layout/, ...
  lib/api.js  context/AuthContext.js
scripts/seed.py            # one-shot seed (data.gov.in or sample)
docker-compose.yml  .env.example  deploy/nginx.conf
```

---

## Run

### Local / self-hosted (Docker)
```bash
cp .env.example .env        # fill values
docker compose up --build   # frontend:3000, backend:8001, mongo, redis, nginx:80
```

### Seed the database (one-shot)
```bash
python scripts/seed.py        # run from repo root
# Uses data.gov.in if DATA_GOV_API_KEY is set, else the labeled sample dataset.
# Prints a summary with Mumbai / Navi Mumbai / Thane counts.
```

### Validate the core pipeline (POC)
```bash
cd backend && python -m scripts.test_core   # exit 0 = all core checks pass
```

---

## Environment variables

| Variable | Purpose |
|---|---|
| `MONGO_URL`, `DB_NAME` | MongoDB connection |
| `REACT_APP_BACKEND_URL` | Frontend → backend base (no trailing `/api`) |
| `JWT_SECRET` | JWT signing |
| `ALLOW_TEST_BYPASS` | Enables `/auth/demo-login` (set `false` in prod) |
| `ANTHROPIC_API_KEY` | Claude classification (fallback used if empty) |
| `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_WEBHOOK_SECRET` | Stripe (test/live) |
| `DATA_GOV_API_KEY` | Live data.gov.in ingestion |

All variables are read via `os.getenv` (backend) / `process.env` (frontend). **No secrets are hardcoded.**

---

## Auth & testing

- **Demo login (test bypass):** `POST /api/v1/auth/demo-login` → Pro JWT, or the *“Try the Demo”* button on `/login`. Disable with `ALLOW_TEST_BYPASS=false` before production.
- **Email/Password:** `/api/v1/auth/register`, `/api/v1/auth/login`.

See `auth_testing.md` for detailed test instructions.

---

## Data sources & honesty

- **data.gov.in** Company Master Data is the legitimate, open-government seed source (resource `4dbe5667-7b6b-41d7-82af-211562424d9a`). Requires a free registered API key.
- **MCA / GST / JustDial / IndiaMart** live scraping is CAPTCHA & IP-block protected (MCA returns HTTP 403). The scraper modules are fully implemented with rate-limiting, retries, exponential backoff and IP-block detection, but report `blocked` status where network access is restricted.
- Until `DATA_GOV_API_KEY` is injected, the app serves a **clearly-labeled SAMPLE dataset** (a top banner indicates *Sample Data Mode*).

---

## API (base `/api/v1`)

`auth/*` · `companies` (+`/{cin}`, `/directors`, `/charges`, `/filings`, `/contact`, `/similar`) · `analytics/{summary,trends,sectors,capital,heatmap}` · `search` (+`/advanced`, `/save`, `/saved`) · `export/{csv,excel,pdf}` · `alerts` · `admin/{stats,ingest/seed,ingest/incremental,enrich/{cin}}` · `payments/{plans,checkout,status}` · webhook at `/api/webhook/stripe`.

---

© CorpIntel India — built for Mumbai, Navi Mumbai & Thane.
