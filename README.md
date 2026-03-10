# News Scraper & AI Analyzer

A personal news aggregation platform with AI-powered analysis. Collects articles from RSS/Atom feeds, normalizes and deduplicates them, runs an AI pipeline (summarization, sentiment, classification, entity extraction, personalized relevance scoring), and delivers alerts and daily digests.

> **Language policy:** All code, comments, variable names, documentation, and `.md` files are written in English.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Celery 5, Redis |
| AI | Google Gemini API (free tier) + Ollama (local fallback) |
| Database | PostgreSQL 16 (SQLite for local dev) |
| Frontend | Next.js 15, TypeScript, Tailwind CSS v4, shadcn/ui |
| Package manager | Poetry |
| Containers | Docker + docker-compose |
| Architecture | Clean Architecture with Hexagonal inspiration |

---

## Project Structure

```
news-scraper/
├── backend/
│   └── src/
│       ├── domain/          # Entities, value objects, repository interfaces
│       ├── use_cases/       # Application orchestration
│       ├── infrastructure/  # DB, collectors, AI providers, cache, email
│       ├── interfaces/      # FastAPI app, CLI
│       └── core/            # Config, logging, exceptions
├── frontend/                # Next.js 15 app
├── docs/
│   └── SPEC.md              # Full project specification
├── .github/
│   ├── copilot/             # AI context and ADR docs
│   └── workflows/           # GitHub Actions CI/CD
├── TODO.md                  # Phased task board
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Prerequisites

- Docker & docker-compose
- Ollama (for local AI) — see `.github/copilot/ollama-setup.md`
- Python 3.12+ and Poetry (only for local development without Docker)
- Node.js 20+ (only for local frontend development without Docker)

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd news-scraper

# 2. Copy and configure environment
cp .env.example .env
# Edit .env: set APP_SECRET_KEY, JWT_SECRET_KEY (and GEMINI_API_KEY if using Gemini)

# 3. Install and start Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh
# Allow connections from Docker containers:
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment="OLLAMA_HOST=0.0.0.0"\n' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload && sudo systemctl restart ollama
# Pull the model (requires ~5 GB RAM; see ollama-setup.md for lighter options)
ollama pull llama3.1:8b

# 4. Start all 8 services (migrations + seed run automatically)
docker compose up -d

# 5. Access the app
# Frontend:              http://localhost:3000
# API docs (Swagger):    http://localhost:8000/docs
# Flower (task monitor): http://localhost:5555

# 6. Create your account at http://localhost:3000/register
#    or use the test account: admin@news.com / admin123

# 7. (Optional) Trigger tasks manually instead of waiting for the schedule
docker compose exec backend python -m backend.src.interfaces.cli.manage collect-feeds
docker compose exec backend python -m backend.src.interfaces.cli.manage run-ai-pipeline --batch-size 50
docker compose exec backend python -m backend.src.interfaces.cli.manage compute-trends --hours 24
```

> **Port mapping:** PostgreSQL is exposed on `5434` (not 5432) and Redis on `6380` (not 6379) to avoid conflicts with local installs.

> **After adding new npm packages:** The frontend container uses an anonymous Docker volume to hold `node_modules`. If you add a package to `frontend/package.json` and rebuild the image, you must recreate the anonymous volume so the container picks up the new packages:
> ```bash
> docker compose down --volumes   # removes anonymous volumes; named volumes (db, redis) are preserved
> docker compose up -d
> ```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Copy env file and adjust URLs to localhost
cp ../.env.example ../.env

# Run migrations
alembic upgrade head

# Seed default sources
python -m backend.src.interfaces.cli.seed_sources

# Start API server
uvicorn backend.src.interfaces.api.main:app --reload

# Start Celery worker (separate terminal)
celery -A backend.src.infrastructure.messaging.celery_app worker --loglevel=info

# Start Celery Beat scheduler (separate terminal)
celery -A backend.src.infrastructure.messaging.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Management CLI (`manage.py`)

Inspired by Django's `manage.py`. A single entry point to trigger any Celery task synchronously (in-process, no broker required) and run maintenance operations. Useful for debugging, one-off runs, and scripting.

```bash
# Inside Docker (recommended):
docker compose exec backend python -m backend.src.interfaces.cli.manage <command> [options]

# Or with Poetry (local dev):
poetry run manage <command> [options]
```

### Available Commands

| Command | When / Why to use it |
|---|---|
| `collect-feeds` | Pull new articles from all active RSS sources right now, without waiting for the 60-minute schedule. Use after adding a new source or when you want fresh data immediately. |
| `run-ai-pipeline` | Process the backlog of unanalyzed articles (summary, sentiment, category, entities, relevance). Run after a fresh install, after Ollama was offline, or to catch up a large backlog. |
| `send-alerts` | Check the last hour of articles against user keyword rules and fire any pending email alerts. Run to verify alert delivery without waiting for the 15-minute schedule. |
| `send-digest` | Compile and send the daily digest email to all active users. Run to preview/test digest delivery at any time of day. |
| `update-weights` | Recalculate implicit interest weights from the full article read history. Run after bulk-importing articles or to force a profile recalculation outside the daily schedule. |
| `compute-trends` | Aggregate trending keywords and sentiment across recent articles and persist the snapshot. Run to refresh the Trends page data without waiting for the hourly schedule. |
| `seed` | Idempotent seed: creates default RSS sources and the `admin@news.com` admin user. Safe to run multiple times. Run on a fresh database or after wiping data. |

### Options

| Command | Option | Default | Description |
|---|---|---|---|
| `run-ai-pipeline` | `--batch-size N` | `20` | Articles processed per run |
| `compute-trends` | `--hours N` | `24` | Look-back window for article aggregation |

### Examples

```bash
# Collect new articles right now
docker compose exec backend python -m backend.src.interfaces.cli.manage collect-feeds

# Process 50 articles through the AI pipeline in one shot
docker compose exec backend python -m backend.src.interfaces.cli.manage run-ai-pipeline --batch-size 50

# Refresh the Trends page with the last 48 hours of data
docker compose exec backend python -m backend.src.interfaces.cli.manage compute-trends --hours 48

# Verify that keyword alerts are firing correctly
docker compose exec backend python -m backend.src.interfaces.cli.manage send-alerts

# Rebuild a clean database from scratch
docker compose exec backend python -m backend.src.interfaces.cli.manage seed
```

> **How it works:** each command calls the corresponding Celery task via `.apply()`, which runs it synchronously in the same process — no broker, no worker, no queue needed. The full task output (collected, processed, matched, etc.) is printed to stdout.

---

```bash
# Run tests
cd backend && poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src --cov-report=term-missing

# Lint & format
poetry run ruff check .
poetry run ruff format .

# Type check
poetry run mypy src/

# Pre-commit hooks (runs automatically on git commit)
pre-commit install    # run once after cloning
pre-commit run --all-files  # run manually
```

---

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add RSS collector for Hacker News
fix: handle missing publish date in feed entry
docs: update SPEC.md with compression strategy
chore: bump feedparser to 6.0.11
test: add unit tests for deduplication service
refactor: extract ArticleHash to value object
```

---

## Branches

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code |
| `dev` | Active development, merged to main via PR |

---

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description | Default |
|---|---|---|
| `APP_SECRET_KEY` | Application secret (generate with `openssl rand -hex 32`) | — |
| `JWT_SECRET_KEY` | JWT signing secret (generate with `openssl rand -hex 32`) | — |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://newsuser:newspass@db:5432/newsdb` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `AI_PROVIDER` | `gemini` or `ollama` | `ollama` |
| `GEMINI_API_KEY` | Google Gemini API key (only if `AI_PROVIDER=gemini`) | — |
| `OLLAMA_BASE_URL` | Ollama API URL (Docker: use `host.docker.internal`) | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | Ollama model to use | `llama3.1:8b` |
| `OLLAMA_FALLBACK` | Fall back to Ollama when Gemini hits rate limit | `true` |
| `SMTP_HOST` | Email SMTP host (leave blank to disable alerts) | — |
| `SMTP_PORT` | Email SMTP port | `587` |
| `SMTP_USER` | Email username | — |
| `SMTP_PASSWORD` | Email password | — |
| `ALERT_EMAIL` | Recipient email for alerts | — |
| `DEFAULT_FETCH_INTERVAL` | Feed fetch interval in minutes | `60` |

---

## Documentation

- [`docs/SPEC.md`](docs/SPEC.md) — Full project specification, architecture, data model, API contract
- [`TODO.md`](TODO.md) — Phased task board
- [`.github/copilot/`](.github/copilot/) — Architecture decisions and AI context docs

---

## License

MIT
