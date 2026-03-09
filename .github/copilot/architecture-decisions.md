# ADR-001: Architecture Pattern — Clean Architecture with Hexagonal Inspiration

**Date:** 2026-03-07
**Status:** Accepted

## Context

The news scraper needs to:
- Support multiple interchangeable collectors (RSS now, scrapers later).
- Support multiple interchangeable AI providers (Gemini, Ollama, future paid APIs).
- Support multiple notification channels (email now, Telegram/Discord later).
- Be testable without requiring a real database, real AI API, or real email server.
- Scale from single-user to multi-user without rearchitecting.

## Decision

Adopt **Clean Architecture** with **Ports & Adapters (Hexagonal)** influence:

- **Domain layer**: pure Python entities and interfaces. Zero external dependencies.
- **Use Cases layer**: application logic. Depends only on domain interfaces (ports).
- **Infrastructure layer**: concrete adapters for DB, AI, HTTP, email, cache.
- **Interfaces layer**: FastAPI, Celery tasks, CLI — thin layer that calls use cases.

## Consequences

- More boilerplate upfront (interfaces, dependency injection).
- AI provider, database, and notification channel can be swapped with zero domain changes.
- All use cases are unit-testable with mocked ports.
- Onboarding is straightforward once the pattern is understood.

---

# ADR-002: Task Queue — Celery + Redis

**Date:** 2026-03-07
**Status:** Accepted

## Context

Feed collection, AI processing, alert sending, and digest generation are background operations that must run on a schedule, independently of HTTP requests.

## Decision

Use **Celery 5** with **Redis** as both broker and result backend. Use **Celery Beat** for scheduled tasks (replaces cron).

## Rationale

- Team has prior experience with Celery.
- Redis is already required for caching — no extra infra.
- Celery Beat provides per-task configurable intervals (matches requirement for per-source fetch interval).
- Easy to scale horizontally with multiple workers.

---

# ADR-003: AI Provider Strategy — Gemini + Ollama with Pluggable Interface

**Date:** 2026-03-07
**Status:** Accepted

## Decision

- Primary: **Google Gemini 1.5 Flash** (free tier: 1,500 req/day).
- Fallback: **Ollama** (local, zero cost, requires local install).
- Interface: `AIProviderPort` Python Protocol — all providers implement the same `analyze()` method.
- Switch via `AI_PROVIDER=gemini|ollama` environment variable.
- On Gemini rate-limit error (429), automatically fall back to Ollama if configured.

## Future

Paid providers (OpenAI GPT-4o, Anthropic Claude) can be added as new adapters with zero changes to use cases.

---

# ADR-004: Database Strategy — SQLAlchemy 2 + Alembic + PostgreSQL

**Date:** 2026-03-07
**Status:** Accepted

## Decision

- ORM: **SQLAlchemy 2.x** (async) with full type annotations.
- Migrations: **Alembic** — all schema changes via migration scripts.
- Development: **SQLite** (zero config).
- Production: **PostgreSQL 16**.
- Article body stored compressed (`zlib`) via a custom `TypeDecorator`.

---

# ADR-005: Frontend Stack — Next.js 15 + TypeScript + Tailwind + shadcn/ui

**Date:** 2026-03-07
**Status:** Accepted

## Decision

| Concern | Choice | Rationale |
|---|---|---|
| Framework | Next.js 15 (App Router) | SSR/SSG, mature ecosystem, React 19 |
| Language | TypeScript strict | Type safety, better DX |
| Styling | Tailwind CSS v4 | Utility-first, industry standard |
| Components | shadcn/ui | Built on Radix (accessible), owns the code, no heavy deps |
| State | Zustand | Lightweight, no boilerplate |
| Server state | TanStack Query v5 | Caching, background refetch, pagination |
| Forms | React Hook Form + Zod | Type-safe, performant |
| Charts | Recharts | Simple, Composable, React-native |

---

# ADR-008: Docker Stack — 8 Services with Auto-migration

**Date:** 2026-03-08
**Status:** Accepted

## Context

Running `docker compose up` should work from a cold start with zero manual steps.

## Decision

The Docker stack runs 8 services:

| Service | Image | External Port |
|---|---|---|
| `db` | postgres:16-alpine | 5434 (avoids conflict with local PostgreSQL) |
| `redis` | redis:7-alpine | 6380 (avoids conflict with local Redis) |
| `backend` | project Dockerfile | 8000 |
| `celery_worker` | project Dockerfile | — |
| `celery_beat` | project Dockerfile | — |
| `flower` | project Dockerfile | 5555 |
| `frontend` | frontend Dockerfile | 3000 |

`entrypoint.sh` runs `alembic upgrade head` and `python -m backend.src.interfaces.cli.seed_sources` automatically before starting `uvicorn`, so no manual migration or seed step is needed.

All backend services use `extra_hosts: ["host.docker.internal:host-gateway"]` for Linux compatibility (Docker Desktop sets this automatically on macOS/Windows).

## Key fixes applied during Docker bringup

- `render_as_batch=False` in `alembic/env.py` (was `True` — SQLite-only setting, breaks PostgreSQL).
- `get_session()` dependency now commits on success and rolls back on exception (was missing `commit`).
- `BACKEND_URL=http://backend:8000` injected in the frontend service for Next.js SSR rewrites.
- `OLLAMA_BASE_URL=http://host.docker.internal:11434` in backend/worker services.

---

# ADR-009: Authentication — JWT HS256 + Refresh Tokens

**Date:** 2026-03-08
**Status:** Accepted

## Decision

- **Access token**: HS256 JWT, 30-minute expiry, signed with `JWT_SECRET_KEY`.
- **Refresh token**: HS256 JWT, 7-day expiry, stored client-side in localStorage.
- **FastAPI dependency**: `get_current_user` decodes `Authorization: Bearer <token>` header; raises 401 on invalid/expired tokens.
- **Password hashing**: bcrypt via `passlib[bcrypt]` (pinned to `bcrypt==4.0.1` for compatibility).
- **Endpoints**: `POST /auth/register`, `POST /auth/login` (OAuth2 form), `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`.
- **Frontend**: Zustand `authStore` persisted in `localStorage`; all API calls attach `Authorization` header automatically.

## Rationale

- Stateless tokens avoid session store; Redis is used only for Celery, not session management.
- Refresh tokens allow long-lived sessions without issuing long-lived access tokens.
- `user_id` was already on all DB tables from Phase 1, so adding auth required zero schema changes.


**Date:** 2026-03-07
**Status:** Accepted

## Decision

All commits follow [Conventional Commits](https://www.conventionalcommits.org/) spec:

```
<type>[optional scope]: <description>

Types: feat, fix, docs, chore, test, refactor, perf, ci, build
```

Enforced via `commitlint` + `pre-commit` hook.

---

# ADR-007: Multi-user Readiness from Day 1

**Date:** 2026-03-07
**Status:** Accepted

## Decision

- All domain entities carry a `user_id: UUID | None` field.
- All DB tables have a `user_id` column (nullable in Phase 1).
- No multi-user auth enforced in MVP (single hardcoded user).
- Auth (JWT) will be added in Phase 7 with zero schema changes required.

---

# ADR-010: Alert Architecture — Keyword Watch vs. Alert Log

**Date:** 2026-03-08
**Status:** Accepted

## Context

During manual testing it was discovered that `POST /alerts` and the `send_alerts_task` serve different purposes that were conflated.

## Decision

Two separate concerns:

1. **Keyword watch rules** (`users.alert_keywords` column, managed via `PUT /profile/interests`): the list of words the background task monitors. Set by the user via the profile page.
2. **Alert history log** (`alerts` table, `GET/POST/DELETE /alerts`): a record of every notification that was fired, with timestamp and matched article reference.

The `send_alerts_task` reads keywords from the user profile (via `SQLUserRepository.get_default()`), scans recent articles, and writes to the alert log when a match is found and the email is sent.

## Known UX Gap (Phase 10)

The frontend "Alerts" page currently uses `POST /alerts` to create log entries, which gives users the impression they are setting up keyword monitoring. This will be redesigned in Phase 10: the page will manage `alert_keywords` on the profile and display the alert log separately.

## Rate Limiting

One email per keyword per hour (`_RATE_LIMIT_HOURS = 1` in `SendAlertsUseCase`). Checked by querying `alerts.list_recent_by_keyword()` before sending.

---

# ADR-011: Management CLI — Django-style `manage.py`

**Date:** 2026-03-09
**Status:** Accepted

## Context

Celery tasks are scheduled automatically via Celery Beat, but there is no way to trigger them manually without knowing the internal Celery CLI syntax (`celery -A ... call ... --kwargs='...'`). Developers need to:

- Trigger a specific task on demand (e.g. after adding a new source, after fixing a bug, during debugging).
- Run maintenance operations (seed, re-process articles) without memorising long commands.
- Verify that tasks produce the expected output in isolation.

## Decision

Implement a single CLI entry point at `backend/src/interfaces/cli/manage.py`, inspired by Django's `manage.py`. Each subcommand maps to a handler function that calls the corresponding Celery task via `.apply()`.

```
python -m backend.src.interfaces.cli.manage <command> [options]
poetry run manage <command> [options]
```

Available commands: `collect-feeds`, `run-ai-pipeline`, `send-alerts`, `send-digest`, `update-weights`, `compute-trends`, `seed`.

Registered as a Poetry script (`manage`) in `pyproject.toml` `[tool.poetry.scripts]`.

## Key Design Choice — `.apply()` over `.delay()`

Tasks are invoked with `.apply()` (synchronous, in-process execution) rather than `.delay()` (asynchronous, broker-dispatched). Rationale:

- **No broker dependency**: works without a running Redis/RabbitMQ — runs standalone in any shell.
- **Immediate feedback**: stdout from the task appears directly in the terminal; no need to watch Flower or worker logs.
- **Deterministic**: the developer sees the exact result of that run before the shell returns.
- **Trade-off**: runs in the calling process, so heavy tasks (large AI batches) block the terminal for their duration. Acceptable for a CLI tool used intentionally.

## Structure

```
interfaces/cli/
├── manage.py          # Entry point — argparse + _COMMANDS dispatch table
└── seed_sources.py    # Async seed function, also callable from manage seed
```

Each handler follows the same pattern:
1. Import the task lazily (inside the function) to avoid circular imports at module load time.
2. Call `task.apply(kwargs={...})`.
3. Call `.get()` on the result to block until done.
4. Print a `✔  Done — key=value` summary line to stdout.

## Consequences

- Any new Celery task can be exposed as a CLI command by adding a `cmd_<name>` function and one entry to `_COMMANDS`.
- The `seed` command re-uses the existing `_seed()` coroutine from `seed_sources.py` via `asyncio.run()`, keeping a single source of truth for seed logic.
- Error handling: `KeyboardInterrupt` prints `⚠  Interrupted.`; all other exceptions print `✖  Error: <msg>` and exit with code 1.

