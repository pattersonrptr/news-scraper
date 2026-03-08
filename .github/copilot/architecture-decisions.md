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

# ADR-006: Commit Convention — Conventional Commits

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
