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

- Python 3.12+
- Poetry (`pip install poetry`)
- Docker & docker-compose
- Node.js 20+ (for frontend)
- Ollama (optional, for local AI) — see `.github/copilot/ollama-setup.md`

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd news-scraper

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your values (GEMINI_API_KEY, SMTP settings, etc.)

# 3. Start all services
docker-compose up -d

# 4. Run initial migrations
docker-compose exec backend alembic upgrade head

# 5. Load default sources
docker-compose exec backend python -m src.interfaces.cli.seed_sources

# 6. Access the app
# API docs:   http://localhost:8000/docs
# Frontend:   http://localhost:3000
# Flower (Celery monitor): http://localhost:5555
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Install dependencies (creates .venv automatically)
poetry install

# Activate virtual environment
poetry shell

# Copy env file
cp ../.env.example ../.env

# Run migrations
alembic upgrade head

# Start API server
uvicorn src.interfaces.api.main:app --reload

# Start Celery worker (separate terminal)
celery -A src.infrastructure.messaging.celery_app worker --loglevel=info

# Start Celery Beat scheduler (separate terminal)
celery -A src.infrastructure.messaging.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Development Workflow

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
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./news.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `AI_PROVIDER` | `gemini` or `ollama` | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |
| `SMTP_HOST` | Email SMTP host | — |
| `SMTP_PORT` | Email SMTP port | `587` |
| `SMTP_USER` | Email username | — |
| `SMTP_PASSWORD` | Email password | — |
| `ALERT_EMAIL` | Recipient email for alerts | — |
| `DEFAULT_FETCH_INTERVAL` | Default feed fetch interval (min) | `60` |

---

## Documentation

- [`docs/SPEC.md`](docs/SPEC.md) — Full project specification, architecture, data model, API contract
- [`TODO.md`](TODO.md) — Phased task board
- [`.github/copilot/`](.github/copilot/) — Architecture decisions and AI context docs

---

## License

MIT
