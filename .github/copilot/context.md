# GitHub Copilot Context — News Scraper & AI Analyzer

This document provides context for AI assistants (GitHub Copilot, etc.) working in this codebase.

---

## Project Summary

A Python + Next.js news aggregation platform. Collects RSS/Atom feeds, runs AI analysis (summary, sentiment, classification, entity extraction, relevance scoring), and delivers personalized alerts and daily digests.

## Language Policy

**ALL code, comments, variable names, docstrings, commit messages, and documentation must be in English.**

## Architecture: Clean Architecture + Hexagonal Ports & Adapters

```
domain → use_cases → interfaces (FastAPI/CLI/Celery)
              ↑
        infrastructure (DB, collectors, AI, cache, email)
```

- `domain/` has **zero** framework or infrastructure imports.
- `use_cases/` orchestrates domain logic; depends only on domain + port interfaces.
- `infrastructure/` contains all concrete adapters (SQLAlchemy, feedparser, Gemini, Ollama, Redis, SMTP).
- `interfaces/` contains FastAPI routers, Celery task definitions, CLI commands.
- `core/` contains cross-cutting concerns: config (pydantic-settings), logging, exceptions.

## Key Design Decisions

- **SQLAlchemy 2.x async** for all DB access.
- **Alembic** for migrations — never modify DB schema manually.
- **Celery + Redis** for task queue and scheduling.
- **Pydantic v2** for all data validation (API schemas, config, AI results).
- **Repository pattern**: domain defines abstract interfaces; infrastructure implements them.
- **Provider pattern for AI**: `AIProviderPort` protocol, implemented by `GeminiAdapter` and `OllamaAdapter`. Switch via `AI_PROVIDER` env var.
- **zlib compression** for article body storage (`CompressedText` TypeDecorator).
- **SHA-256 hashing** for deduplication (URL hash + content hash), NOT for encryption.
- All timestamps stored as **UTC** in the database.
- `user_id UUID` present in all tables from day 1 (nullable in MVP, enforced in Phase 7 multi-user).
- **JWT Auth (Phase 7)**: HS256 access tokens (30 min) + refresh tokens (7 days). `get_current_user` FastAPI dependency decodes Bearer token. All user-scoped endpoints require authentication.
- **Docker stack**: 8 services — `db` (PostgreSQL, port 5434), `redis` (port 6380), `backend`, `celery_worker`, `celery_beat`, `flower` (port 5555), `frontend` (port 3000). Migrations and seed run automatically via `entrypoint.sh`.
- **Ollama in Docker**: Ollama runs on the host machine. Containers reach it via `host.docker.internal:11434`. Requires `OLLAMA_HOST=0.0.0.0` in the systemd service override (`/etc/systemd/system/ollama.service.d/override.conf`) so it listens on all interfaces, not just `127.0.0.1`.
- **AI pipeline per-article commit**: `RunAIPipelineUseCase.execute()` accepts an optional `commit_fn` so the Celery task can commit after each article, making progress visible in real time.
- **Alert keyword monitoring vs. alert log**: The `alerts` DB table is a **history log** of fired notifications. The keyword watch rules are stored on the user profile (`users.alert_keywords`), managed via `PUT /profile/interests`. The frontend `POST /alerts` currently writes to the log, not the profile — this is a known UX gap tracked in Phase 10.
- **`send_alerts` task reads from DB**: All three background tasks (`send_alerts`, `send_daily_digest`, `update_implicit_weights`) now use `SQLUserRepository` to load the real user profile. The old `InMemoryUserProfileRepository` stub has been replaced. `SQLUserRepository.get_default()` fetches the first active user.
- **Top Keywords filtering**: `ComputeTrendsUseCase` uses an expanded stopword list covering both English and Portuguese (pt-BR) functional words. Minimum word length is 4 characters. Keywords are extracted from both `title` and `summary` fields.
- **Management CLI (`manage.py`)**: `backend/src/interfaces/cli/manage.py` is a Django-inspired single entry point for running Celery tasks and maintenance operations manually. Each subcommand calls the corresponding Celery task via `.apply()` (synchronous, in-process — no broker needed). Registered as `manage` in `[tool.poetry.scripts]`. Run with `docker compose exec backend python -m backend.src.interfaces.cli.manage <command>` or `poetry run manage <command>`. Available commands: `collect-feeds`, `run-ai-pipeline` (`--batch-size N`), `send-alerts`, `send-digest`, `update-weights`, `compute-trends` (`--hours N`), `seed`.

## Code Style

- `ruff` for linting and formatting (configured in `pyproject.toml`).
- `mypy --strict` for type checking.
- All functions and classes must have type annotations.
- All public functions/methods must have docstrings.
- Conventional Commits for all commit messages.

## Testing

- `pytest` + `pytest-asyncio` for async tests.
- Unit tests go in `backend/tests/unit/`.
- Integration tests go in `backend/tests/integration/`.
- Mock all external HTTP calls (httpx, Gemini API, SMTP).
- Target: 80%+ coverage.

## Important Files

| File | Purpose |
|---|---|
| `docs/SPEC.md` | Full specification — read this first |
| `TODO.md` | Phased task board |
| `backend/src/core/config/settings.py` | All environment variables and defaults |
| `backend/src/domain/entities/` | Core business entities |
| `backend/src/domain/repositories/` | Abstract port interfaces |
| `backend/src/infrastructure/ai/` | AI provider adapters |
| `backend/src/interfaces/api/main.py` | FastAPI application entrypoint |
| `backend/src/interfaces/cli/manage.py` | Management CLI — manually trigger any Celery task or maintenance operation |

## Default Sources (Phase 1)

1. Hacker News — `https://hnrss.org/frontpage` (en, tech)
2. TechCrunch — `https://techcrunch.com/feed/` (en, tech)
3. BBC News World — `http://feeds.bbci.co.uk/news/world/rss.xml` (en, world)
4. G1 Tecnologia — `https://g1.globo.com/rss/g1/tecnologia/` (pt-BR, tech)
5. InfoMoney — `https://www.infomoney.com.br/feed/` (pt-BR, economy)

## Do NOT

- Import infrastructure in domain or use_cases.
- Use `datetime.now()` — always use `datetime.now(UTC)`.
- Bypass the repository interface — never query DB directly in use cases.
- Hardcode API keys — always use `settings` from `core/config`.
- Store uncompressed article body text in DB.
