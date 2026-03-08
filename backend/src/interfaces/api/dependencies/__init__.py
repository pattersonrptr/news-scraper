"""FastAPI dependency injection providers.

These functions are used with `Depends()` in route handlers to inject
repository instances backed by a request-scoped async DB session.
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.database.engine import AsyncSessionFactory
from backend.src.infrastructure.database.repositories.article_repo import (
    SQLArticleRepository,
)
from backend.src.infrastructure.database.repositories.source_repo import (
    SQLSourceRepository,
)
from backend.src.infrastructure.database.repositories.alert_repo import (
    SQLAlertRepository,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session."""
    async with AsyncSessionFactory() as session:
        yield session


async def get_article_repo(
    session: AsyncSession = Depends(get_session),
) -> SQLArticleRepository:
    """Inject a SQLArticleRepository into a route handler."""
    return SQLArticleRepository(session)


async def get_source_repo(
    session: AsyncSession = Depends(get_session),
) -> SQLSourceRepository:
    """Inject a SQLSourceRepository into a route handler."""
    return SQLSourceRepository(session)


async def get_alert_repo(
    session: AsyncSession = Depends(get_session),
) -> SQLAlertRepository:
    """Inject a SQLAlertRepository into a route handler."""
    return SQLAlertRepository(session)
