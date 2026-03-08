# News Scraper & AI Analyzer — Full Project Specification

> **Language policy:** All code, comments, variable names, documentation, and `.md` files must be written in English.
> **Date:** 2026-03-07 | **Status:** Living document — update before every commit.

---

## 1. Vision

A personal (initially) news aggregation platform that:
- Collects articles from multiple configurable sources (RSS/Atom feeds now; HTML scrapers later).
- Normalizes, deduplicates, and stores them efficiently.
- Runs an AI pipeline to summarize, classify, score sentiment, extract entities, and compute personalized relevance.
- Delivers alerts, daily digests, and trend reports.
- Exposes a REST API and a modern web UI.
- Is designed from day one to scale to multi-user, multi-provider, and multi-collector scenarios.

---

## 2. System Contract

| Aspect | Decision |
|---|---|
| **Input** | Configured source list (RSS URLs) + APScheduler/Celery cron |
| **Output** | Normalized articles + AI metadata + alerts + digest |
| **Language** | English (all artifacts) |
| **Primary users** | Single user (MVP), multi-user (Phase 4+) |
| **Deployment** | Local Docker (MVP), cloud VPS/Railway (future) |

---

## 3. Architecture

### 3.1 Pattern: Clean Architecture with Hexagonal Inspiration

```
┌──────────────────────────────────────────────────────────────┐
│                        Interfaces Layer                      │
│         FastAPI routes │ CLI commands │ Celery tasks         │
├──────────────────────────────────────────────────────────────┤
│                       Use Cases Layer                        │
│   CollectFeeds │ ProcessArticle │ RunAIPipeline │ SendAlert  │
├──────────────────────────────────────────────────────────────┤
│                        Domain Layer                          │
│    Article │ Source │ UserProfile │ Alert │ Trend entities   │
├──────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  DB (SQLAlchemy) │ Collectors │ AI Providers │ Email │ Cache │
└──────────────────────────────────────────────────────────────┘
```

**Key principle:** The domain and use-cases layers have zero knowledge of frameworks, databases, or external APIs. All I/O is injected via repository/port interfaces.

### 3.2 Module Map

```
backend/src/
├── domain/
│   ├── entities/          # Article, Source, UserProfile, Alert, Trend
│   ├── value_objects/     # ArticleHash, Sentiment, RelevanceScore
│   ├── repositories/      # Abstract interfaces (ports)
│   └── services/          # Pure domain services (dedup logic, scoring)
├── use_cases/             # Application-level orchestration
├── infrastructure/
│   ├── database/
│   │   ├── models/        # SQLAlchemy ORM models
│   │   └── migrations/    # Alembic migrations
│   ├── collectors/
│   │   ├── rss/           # feedparser-based collector (Phase 1)
│   │   └── scraper/       # BeautifulSoup/Scrapy/Selenium (Phase 5+)
│   ├── ai/
│   │   ├── gemini/        # Google Gemini adapter
│   │   └── ollama/        # Ollama local model adapter
│   ├── cache/             # Redis cache adapter
│   ├── messaging/         # Celery task definitions
│   └── notifications/
│       └── email/         # SMTP email adapter
├── interfaces/
│   ├── api/               # FastAPI app, routers, schemas, deps
│   └── cli/               # Management CLI commands
└── core/
    ├── config/            # Settings (pydantic-settings, .env)
    ├── logging/           # Structured logging setup
    └── exceptions/        # Custom exception hierarchy
```

### 3.3 Data Flow

```
[Celery Beat] ──► [CollectFeedsTask]
                        │
                  [RSS Collector] ──► [RawArticle]
                        │
                  [NormalizeUseCase]
                        │
                  [DeduplicationService] ──► skip if duplicate
                        │
                  [ArticleRepository.save()]
                        │
                  [AIProcessingTask (batch, hourly)]
                        │
                  [AI Pipeline] ── summary ── sentiment ── classification
                                ── entity extraction ── relevance score
                        │
                  [ArticleRepository.update()]
                        │
                  [AlertService] ──► check keyword triggers
                        │
                  [EmailAdapter] ──► send alert / daily digest
```

---

## 4. Tech Stack

### Backend
| Concern | Tool | Notes |
|---|---|---|
| Language | Python 3.12 | |
| Package manager | Poetry | Both local `.venv` and Docker |
| Web framework | FastAPI | Async, Pydantic v2, auto-docs |
| ORM | SQLAlchemy 2.x | Async-compatible |
| Migrations | Alembic | |
| Task queue | Celery 5 + Redis | |
| Scheduler | Celery Beat | Configurable per-source interval |
| Feed parsing | feedparser | RSS/Atom |
| HTTP client | httpx | Async |
| AI — primary | Google Gemini API | Free tier: 1,500 req/day |
| AI — local | Ollama (LLaMA 3.1 / Mistral) | Fallback / no-cost option |
| AI abstraction | Custom provider interface | Pluggable: OpenAI, Anthropic, etc. |
| Caching | Redis | Dedup bloom filter + response cache |
| Config | pydantic-settings | `.env` based |
| Linter/formatter | ruff | Replaces flake8 + black + isort |
| Type checker | mypy | Strict mode |
| Testing | pytest + pytest-asyncio + httpx | |
| Coverage | pytest-cov | |
| Pre-commit | pre-commit | ruff, mypy, conventional commits |
| Containerization | Docker + docker-compose | |

### Frontend
| Concern | Tool | Notes |
|---|---|---|
| Framework | Next.js 15 (App Router) | React 19, SSR/SSG, SEO-ready |
| Language | TypeScript | Strict mode |
| Styling | Tailwind CSS v4 | Utility-first |
| Components | shadcn/ui | Built on Radix + Tailwind |
| State | Zustand | Lightweight, replaces Redux |
| Data fetching | TanStack Query v5 | Server state, caching |
| Forms | React Hook Form + Zod | Type-safe validation |
| Charts | Recharts | Trends, sentiment visualization |
| Icons | Lucide React | |

### Infrastructure
| Concern | Tool |
|---|---|
| Database | PostgreSQL 16 (SQLite for local dev) |
| Cache / Queue | Redis 7 |
| Reverse proxy | Nginx (production) |
| CI/CD | GitHub Actions |
| Secrets | `.env` + Docker secrets |

---

## 5. Data Model (Core Entities)

### Article
```
id              UUID PK
user_id         UUID FK (null = global, for future multi-user)
source_id       UUID FK
url             TEXT UNIQUE
url_hash        CHAR(64)    -- SHA-256 of canonical URL
content_hash    CHAR(64)    -- SHA-256 of title+body for dedup
title           TEXT
body_compressed BYTEA       -- zlib-compressed body
summary         TEXT        -- AI-generated
published_at    TIMESTAMPTZ
collected_at    TIMESTAMPTZ
language        CHAR(5)     -- 'en', 'pt-BR', etc.
sentiment       SMALLINT    -- -1 negative, 0 neutral, 1 positive
sentiment_score FLOAT
category        TEXT        -- AI classification
entities        JSONB       -- {persons, orgs, places}
relevance_score FLOAT       -- personalized score
is_processed    BOOLEAN
is_read         BOOLEAN
created_at      TIMESTAMPTZ
updated_at      TIMESTAMPTZ
```

### Source
```
id              UUID PK
user_id         UUID FK
name            TEXT
url             TEXT UNIQUE
feed_url        TEXT
source_type     ENUM(rss, scraper)
language        CHAR(5)
fetch_interval  INTEGER     -- minutes, default 60
is_active       BOOLEAN
last_fetched_at TIMESTAMPTZ
created_at      TIMESTAMPTZ
```

### UserProfile
```
id              UUID PK
email           TEXT UNIQUE
hashed_password TEXT
display_name    TEXT
explicit_interests  JSONB   -- ["tech", "economy", "football"]
implicit_weights    JSONB   -- {"tech": 0.85, "economy": 0.42} (learned)
alert_keywords  JSONB       -- ["Pix", "IPCA"]
digest_time     TIME        -- daily digest send time
notification_email TEXT
is_active       BOOLEAN
created_at      TIMESTAMPTZ
```

### Alert
```
id              UUID PK
user_id         UUID FK
article_id      UUID FK
trigger_keyword TEXT
sent_at         TIMESTAMPTZ
channel         ENUM(email, telegram, webhook)
```

---

## 6. AI Pipeline (Batch, per article)

Each unprocessed article runs through:

1. **Language detection** (langdetect) — determines prompt language.
2. **Summarization** — 3–5 sentences, factual tone.
3. **Sentiment analysis** — score [-1, 1] + label.
4. **Thematic classification** — top 2 categories from a fixed taxonomy.
5. **Entity extraction** — persons, organizations, places as JSON.
6. **Relevance scoring** — combines:
   - Category match vs. `explicit_interests` (weight: 0.5)
   - Implicit learned weight (weight: 0.3)
   - Keyword overlap (weight: 0.2)

### AI Provider Interface (Port)
```python
class AIProviderPort(Protocol):
    async def analyze(self, text: str, user_profile: UserProfile) -> AIAnalysisResult: ...
```
Adapters: `GeminiAdapter`, `OllamaAdapter`. Configured via `AI_PROVIDER=gemini|ollama` env var.

---

## 7. Initial Sources (Phase 1)

| # | Name | Feed URL | Language | Category |
|---|---|---|---|---|
| 1 | Hacker News (top) | `https://hnrss.org/frontpage` | en | Tech |
| 2 | TechCrunch | `https://techcrunch.com/feed/` | en | Tech |
| 3 | BBC News World | `http://feeds.bbci.co.uk/news/world/rss.xml` | en | World |
| 4 | G1 Tecnologia | `https://g1.globo.com/rss/g1/tecnologia/` | pt-BR | Tech |
| 5 | InfoMoney | `https://www.infomoney.com.br/feed/` | pt-BR | Economy |

> These are the defaults. Users can add/remove sources via UI or API.

---

## 8. API Contract (RESTful, FastAPI)

### Base URL: `/api/v1`

| Method | Path | Description |
|---|---|---|
| GET | `/articles` | List articles (filters: source, category, date, sentiment) |
| GET | `/articles/{id}` | Article detail |
| PATCH | `/articles/{id}/read` | Mark as read (implicit interest tracking) |
| GET | `/sources` | List configured sources |
| POST | `/sources` | Add new source |
| PUT | `/sources/{id}` | Update source |
| DELETE | `/sources/{id}` | Remove source |
| GET | `/profile` | Get user profile + interests |
| PUT | `/profile/interests` | Update explicit interests |
| GET | `/alerts` | List alerts |
| POST | `/alerts/keywords` | Add alert keyword |
| DELETE | `/alerts/keywords/{keyword}` | Remove alert keyword |
| GET | `/trends` | Top trending keywords last 24h |
| GET | `/digest/preview` | Preview today's digest |
| POST | `/digest/send` | Manually trigger digest email |
| GET | `/health` | Health check |

---

## 9. Scheduler & Tasks

| Task | Schedule | Description |
|---|---|---|
| `collect_feeds` | Per-source interval (default 60min) | Fetch + normalize + dedup + store |
| `run_ai_pipeline` | Every 60min | Process unanalyzed articles in batches of 20 |
| `send_alerts` | Every 15min | Check new articles for keyword matches |
| `send_daily_digest` | Daily at user's `digest_time` | Compile and send digest email |
| `compute_trends` | Every hour | Aggregate keyword frequency last 24h |
| `update_implicit_weights` | Daily | Recompute implicit interest weights from read history |

---

## 10. Alerting & Digest

- **Keyword alerts**: triggered per article, sent via email (SMTP), rate-limited to max 1 email per keyword per hour.
- **Daily digest**: top N articles by relevance score, grouped by category, rendered as HTML email.
- **Future channels**: Telegram bot, Discord webhook, browser push — pluggable via `NotificationPort`.

---

## 11. Deduplication Strategy

1. **URL normalization**: strip UTM params, trailing slashes, `www`.
2. **URL hash**: SHA-256 of normalized URL → fast DB index lookup.
3. **Content hash**: SHA-256 of `(title + first 500 chars of body)` → catches reposts.
4. Rule: reject if either hash already exists in DB.

---

## 12. Compression Strategy

- Article `body` is stored as `zlib.compress(body.encode())` → `BYTEA` column.
- Decompressed on read via SQLAlchemy `TypeDecorator`.
- Estimated 60–70% size reduction for typical news text.

---

## 13. Caching Strategy

- **Feed response cache**: Redis, TTL = source fetch interval. Avoids refetching unchanged feeds.
- **AI result cache**: Redis, TTL = 24h. Avoids re-analyzing duplicate content that slipped through.
- **Article list cache**: Redis, TTL = 5min. For frequent API reads.

---

## 14. Edge Cases to Handle

| Case | Strategy |
|---|---|
| Article without publish date | Use `collected_at` as fallback |
| Article without author | Store `None`, display "Unknown" |
| Partial paywall content | Store what's available, flag `is_partial = True` |
| Near-duplicate articles (repost) | Content hash catches same title+body; fuzzy matching (future) |
| Mixed timezones in feeds | Normalize all timestamps to UTC on ingestion |
| Feed URL changes | Last fetch error increments `error_count`; disable after 5 |
| AI provider rate limit | Exponential backoff + fallback to Ollama |
| Gemini free tier exhausted | Auto-fallback to Ollama if configured |
| Empty feed | Log + skip silently |
| Malformed XML/RSS | feedparser handles most; wrap in try/except, log error |

---

## 15. Quality & Developer Experience

- `ruff` — linting + formatting (replaces flake8, black, isort)
- `mypy --strict` — static type checking
- `pytest` + `pytest-asyncio` + `httpx` — unit + integration + e2e tests
- `pytest-cov` — coverage reports (target: 80%+)
- `pre-commit` — runs ruff + mypy on every commit
- **Conventional Commits** — `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`
- GitHub Actions — lint + test on every push to `main` and `dev`

---

## 16. Multi-User Readiness (Phase 4+)

From day 1:
- All DB tables include `user_id UUID` (nullable in MVP, FK to `users` table later).
- JWT-based auth skeleton in place but not enforced in Phase 1 (single hardcoded user).
- Row-level security can be added to PostgreSQL queries later without schema changes.

---

## 17. Future Roadmap (Post-MVP)

- [ ] HTML scrapers: BeautifulSoup → Scrapy → Selenium (in that order of complexity)
- [ ] Multi-user auth (JWT + refresh tokens)
- [ ] Telegram / Discord alert channels
- [ ] Fuzzy deduplication (MinHash / SimHash)
- [ ] Full-text search (PostgreSQL `tsvector` or Elasticsearch)
- [ ] Mobile PWA
- [ ] Cloud deployment guide (Railway / Fly.io / VPS)
- [ ] Paid AI provider support (OpenAI, Anthropic)
- [ ] Export: PDF digest, OPML source list
