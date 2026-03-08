"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.core.config import get_settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.interfaces.api.dependencies import get_article_repo
from backend.src.infrastructure.database.repositories.article_repo import SQLArticleRepository
from backend.src.use_cases.compute_trends import ComputeTrendsUseCase
from backend.src.use_cases.compile_digest import CompileDigestUseCase
from backend.src.interfaces.api.routers import (
    alerts_router,
    articles_router,
    profile_router,
    sources_router,
)

setup_logging()
log = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    log.info("application_startup", env=settings.app_env, ai_provider=settings.ai_provider)
    yield
    log.info("application_shutdown")


app = FastAPI(
    title="News Scraper & AI Analyzer",
    description="Personal news aggregation platform with AI-powered analysis.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
_API_PREFIX = "/api/v1"

app.include_router(articles_router, prefix=_API_PREFIX)
app.include_router(sources_router, prefix=_API_PREFIX)
app.include_router(profile_router, prefix=_API_PREFIX)
app.include_router(alerts_router, prefix=_API_PREFIX)


@app.get("/api/v1/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/trends", tags=["trends"])
async def get_trends(
    hours: int = 24,
    repo: SQLArticleRepository = Depends(get_article_repo),
) -> dict:
    """Return trending topics, keywords, and sentiment distribution.

    Computes live from articles collected in the last *hours* hours.
    """
    articles = await repo.list_recent(hours=hours)
    return ComputeTrendsUseCase(articles=articles).execute()


@app.get("/api/v1/digest/preview", tags=["digest"])
async def get_digest_preview(
    hours: int = 24,
    repo: SQLArticleRepository = Depends(get_article_repo),
) -> dict:
    """Return a preview of the daily digest (not sent by email).

    Aggregates the top articles from the last *hours* hours grouped by category.
    """
    use_case = CompileDigestUseCase(article_repo=repo, hours=hours)
    context = await use_case.execute()
    # Replace Article objects with dicts for JSON serialisation
    context["sections"] = {
        cat: [
            {
                "id": str(a.id),
                "title": a.title,
                "url": a.url,
                "summary": a.summary,
                "sentiment": a.sentiment,
                "category": a.category,
                "relevance_score": a.relevance_score,
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in arts
        ]
        for cat, arts in context["sections"].items()
    }
    return context
