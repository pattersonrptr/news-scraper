"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.core.config import get_settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.interfaces.api.routers import (
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


@app.get("/api/v1/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
