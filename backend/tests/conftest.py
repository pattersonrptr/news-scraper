"""Test configuration and shared fixtures."""

from __future__ import annotations

import pytest
import pytest_asyncio  # noqa: F401 — ensures asyncio mode is active
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.database.models.article import Base as ArticleBase
from backend.src.infrastructure.database.models.alert import Base as AlertBase
from backend.src.infrastructure.database.models.source import Base as SourceBase
from backend.src.infrastructure.database.repositories.article_repo import (
    SQLArticleRepository,
)
from backend.src.infrastructure.database.repositories.source_repo import (
    SQLSourceRepository,
)
from backend.src.infrastructure.database.repositories.alert_repo import (
    SQLAlertRepository,
)
from backend.src.interfaces.api.dependencies import get_article_repo, get_session, get_source_repo, get_alert_repo
from backend.src.interfaces.api.main import app

# ---------------------------------------------------------------------------
# Celery — always-eager mode (no broker needed in tests)
# ---------------------------------------------------------------------------

from backend.src.infrastructure.messaging.celery_app import celery_app

celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,  # propagate exceptions so tests can catch them
)

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture()
async def db_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AlertBase.metadata.create_all)
        await conn.run_sync(ArticleBase.metadata.create_all)
        await conn.run_sync(SourceBase.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(db_engine):
    """Provide a test-scoped async session."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture()
async def api_client(db_session: AsyncSession):
    """AsyncClient with dependency overrides pointing to the in-memory DB."""

    async def _override_session():
        yield db_session

    async def _override_article_repo():
        return SQLArticleRepository(db_session)

    async def _override_source_repo():
        return SQLSourceRepository(db_session)

    async def _override_alert_repo():
        return SQLAlertRepository(db_session)

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_article_repo] = _override_article_repo
    app.dependency_overrides[get_source_repo] = _override_source_repo
    app.dependency_overrides[get_alert_repo] = _override_alert_repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Domain entity factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_article_data() -> dict:
    """Minimal raw article data dict for testing."""
    return {
        "url": "https://example.com/article/1",
        "title": "Python 3.13 Released",
        "body": "Python 3.13 brings many improvements to the language including...",
        "language": "en",
    }
