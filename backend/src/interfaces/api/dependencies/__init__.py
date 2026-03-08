"""FastAPI dependency injection providers.

These functions are used with `Depends()` in route handlers to inject
repository instances backed by a request-scoped async DB session.
"""

from __future__ import annotations

import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.user_profile import UserProfile
from backend.src.infrastructure.auth.jwt import decode_token
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
from backend.src.infrastructure.database.repositories.user_repo import (
    SQLUserRepository,
)

# OAuth2 scheme — looks for `Authorization: Bearer <token>` header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session.

    Commits on clean exit, rolls back on exception.
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


async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> SQLUserRepository:
    """Inject a SQLUserRepository into a route handler."""
    return SQLUserRepository(session)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: SQLUserRepository = Depends(get_user_repo),
) -> UserProfile:
    """Decode the Bearer JWT and return the authenticated UserProfile.

    Raises HTTP 401 if the token is missing, invalid, expired, or the
    user no longer exists / is inactive.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id_str is None or token_type != "access":
            raise credentials_exc
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exc

    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exc

    return user

