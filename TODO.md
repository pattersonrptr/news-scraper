# News Scraper & AI Analyzer — Task Board

> **Language policy:** All entries in English.
> Update this file before every commit. Reference the full spec in `docs/SPEC.md`.

---

## Phase 1 — Foundation & RSS Collector (MVP Core)

- [ ] Initialize Poetry project (`pyproject.toml`)
- [ ] Configure `ruff`, `mypy`, `pytest`, `pre-commit`
- [ ] Set up GitHub Actions CI (lint + test)
- [ ] Scaffold Clean Architecture directory structure with `__init__.py` stubs
- [ ] Define domain entities: `Article`, `Source`, `UserProfile`, `Alert`
- [ ] Define repository interfaces (ports): `ArticleRepository`, `SourceRepository`, `UserProfileRepository`
- [ ] Implement `core/config` (pydantic-settings, `.env` loading)
- [ ] Implement `core/logging` (structured JSON logging)
- [ ] Implement `core/exceptions` (custom exception hierarchy)
- [ ] Implement SQLAlchemy models for `articles`, `sources`, `user_profiles`
- [ ] Set up Alembic with initial migration
- [ ] Implement `CompressedText` SQLAlchemy `TypeDecorator` (zlib body storage)
- [ ] Implement `RSSCollector` adapter (feedparser + httpx)
- [ ] Implement deduplication service (URL hash + content hash)
- [ ] Implement `CollectFeedsUseCase`
- [ ] Add 5 initial default sources (see `docs/SPEC.md` §7)
- [ ] Write unit tests for deduplication service
- [ ] Write integration test for RSS collector (mock HTTP)
- [ ] Write Dockerfile for backend
- [ ] Write `docker-compose.yml` (backend + PostgreSQL + Redis)
- [ ] Confirm RSS collection works end-to-end in Docker

---

## Phase 2 — REST API

- [ ] Bootstrap FastAPI app with versioned router (`/api/v1`)
- [ ] Implement Pydantic v2 schemas for all API models
- [ ] Implement `GET /articles` with filters (source, category, date, sentiment)
- [ ] Implement `GET /articles/{id}`
- [ ] Implement `PATCH /articles/{id}/read`
- [ ] Implement CRUD for `/sources`
- [ ] Implement `GET /profile` and `PUT /profile/interests`
- [ ] Implement `GET /health`
- [ ] Add pagination to list endpoints
- [ ] Write API integration tests (pytest + httpx AsyncClient)
- [ ] Verify Swagger/ReDoc docs auto-generated correctly

---

## Phase 3 — Celery Task Queue & Scheduler

- [ ] Configure Celery with Redis broker + result backend
- [ ] Configure Celery Beat for periodic tasks
- [ ] Implement `collect_feeds` Celery task (per-source interval)
- [ ] Implement `compute_trends` task (hourly)
- [ ] Add Celery worker and Beat containers to docker-compose
- [ ] Write task integration tests

---

## Phase 4 — AI Pipeline

- [ ] Install Ollama locally (guide in `.github/copilot/ollama-setup.md`)
- [ ] Define `AIProviderPort` protocol
- [ ] Implement `OllamaAdapter` (local, no cost)
- [ ] Implement `GeminiAdapter` (Google free tier)
- [ ] Implement AI pipeline use case: summarize, sentiment, classify, extract entities
- [ ] Implement relevance scoring (explicit interests + implicit weights)
- [ ] Implement `run_ai_pipeline` Celery batch task (runs hourly, batch of 20)
- [ ] Expose `AI_PROVIDER` env var to switch between providers
- [ ] Add Gemini → Ollama automatic fallback on rate limit
- [ ] Write unit tests for relevance scoring
- [ ] Write integration tests for AI adapters (mock responses)

---

## Phase 5 — Alerts & Digest

- [ ] Implement `AlertService` (keyword matching on new articles)
- [ ] Implement SMTP email adapter
- [ ] Implement `send_alerts` Celery task (every 15min, rate-limited 1/keyword/hour)
- [ ] Implement daily digest compilation use case
- [ ] Implement HTML email template for digest
- [ ] Implement `send_daily_digest` Celery task
- [ ] Implement `update_implicit_weights` daily task
- [ ] Implement Alert CRUD API (`/alerts`)
- [ ] Implement `GET /trends` and `GET /digest/preview`
- [ ] Write tests for alert service

---

## Phase 6 — Frontend (Next.js 15 + TypeScript + Tailwind + shadcn/ui)

- [ ] Initialize Next.js 15 project (TypeScript, App Router)
- [ ] Configure Tailwind CSS v4
- [ ] Install and configure shadcn/ui
- [ ] Install Zustand, TanStack Query v5, React Hook Form, Zod, Recharts, Lucide
- [ ] Add frontend service to docker-compose
- [ ] Implement layout (sidebar + topbar + main content)
- [ ] Build article feed page (list + filters + pagination)
- [ ] Build article detail modal/page
- [ ] Build sources management page
- [ ] Build user profile + interests settings page
- [ ] Build alerts management page
- [ ] Build trends dashboard (charts)
- [ ] Ensure fully responsive (mobile + tablet + desktop)

---

## Phase 7 — Multi-user Auth (Future)

- [ ] Add `users` table and FK constraints
- [ ] Implement JWT authentication (login, refresh, logout)
- [ ] Implement registration flow
- [ ] Add auth middleware to FastAPI
- [ ] Add auth pages to frontend (login, register)
- [ ] Enable row-level data isolation

---

## Phase 8 — HTML Scrapers (Future)

- [ ] Implement `BeautifulSoupScraper` adapter
- [ ] Implement `ScrapyScraper` adapter
- [ ] Implement `SeleniumScraper` adapter (JS-heavy sites)
- [ ] Add `robots.txt` checker utility
- [ ] Add per-scraper rate limiter with jitter

---

## Phase 9 — Cloud Deployment (Future)

- [ ] Choose cloud provider (Railway / Fly.io / VPS)
- [ ] Write production docker-compose (with Nginx reverse proxy)
- [ ] Configure environment secrets for production
- [ ] Set up domain + SSL (Let's Encrypt)
- [ ] Write deployment runbook

---

## Maintenance (Ongoing)

- [ ] Review and update `docs/SPEC.md` before each commit
- [ ] Update `README.md` with any new setup steps
- [ ] Keep `CHANGELOG.md` updated (Conventional Commits)
- [ ] Monitor Gemini free tier usage
- [ ] Review and rotate API keys periodically
