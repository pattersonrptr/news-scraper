"""SQLAlchemy async engine and session factory.

Usage:
    from backend.src.infrastructure.database.engine import get_session

    async with get_session() as session:
        result = await session.execute(select(ArticleModel))
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.src.core.config import get_settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# Created once at import time; reused across all requests.
# echo=True only in development to log SQL statements.
def _build_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.app_debug,
        pool_pre_ping=True,
        # SQLite does not support pool size options
        **({} if "sqlite" in settings.database_url else {"pool_size": 5, "max_overflow": 10}),
    )


engine = _build_engine()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async database session.

    Commits on successful exit, rolls back on exception.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
