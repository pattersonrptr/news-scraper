"""Abstract repository interfaces (ports) for the domain layer.

These are the only contracts between use cases and infrastructure.
Concrete implementations live in infrastructure/database/.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
import uuid

from backend.src.domain.entities import Article, Source, UserProfile


@runtime_checkable
class ArticleRepository(Protocol):
    """Port: persistence operations for Article."""

    async def save(self, article: Article) -> Article:
        """Persist a new article. Returns the saved entity."""
        ...

    async def update(self, article: Article) -> Article:
        """Update an existing article."""
        ...

    async def get_by_id(self, article_id: uuid.UUID) -> Article | None:
        """Fetch article by primary key."""
        ...

    async def get_by_url_hash(self, url_hash: str) -> Article | None:
        """Fetch article by URL hash (deduplication check)."""
        ...

    async def get_by_content_hash(self, content_hash: str) -> Article | None:
        """Fetch article by content hash (deduplication check)."""
        ...

    async def list_unprocessed(self, limit: int = 20) -> list[Article]:
        """Return articles not yet processed by the AI pipeline."""
        ...

    async def list(
        self,
        *,
        user_id: uuid.UUID | None = None,
        source_id: uuid.UUID | None = None,
        category: str | None = None,
        sentiment: int | None = None,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Article]:
        """Return a filtered, paginated list of articles."""
        ...

    async def mark_as_read(self, article_id: uuid.UUID) -> None:
        """Mark article as read (triggers implicit interest update)."""
        ...

    async def list_recent(self, hours: int = 24, limit: int = 500) -> list[Article]:
        """Return articles collected in the last N hours (for trend computation)."""
        ...


@runtime_checkable
class SourceRepository(Protocol):
    """Port: persistence operations for Source."""

    async def save(self, source: Source) -> Source:
        ...

    async def update(self, source: Source) -> Source:
        ...

    async def delete(self, source_id: uuid.UUID) -> None:
        ...

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        ...

    async def list_active(self) -> list[Source]:
        """Return all active sources for the scheduler."""
        ...

    async def list_all(self, user_id: uuid.UUID | None = None) -> list[Source]:
        ...

    async def update_last_fetched(self, source_id: uuid.UUID) -> None:
        ...

    async def increment_error_count(self, source_id: uuid.UUID, error: str) -> None:
        ...


@runtime_checkable
class UserProfileRepository(Protocol):
    """Port: persistence operations for UserProfile."""

    async def get(self, user_id: uuid.UUID) -> UserProfile | None:
        ...

    async def get_default(self) -> UserProfile | None:
        """Return the single user profile (MVP single-user mode)."""
        ...

    async def save(self, profile: UserProfile) -> UserProfile:
        ...

    async def update_implicit_weights(
        self, user_id: uuid.UUID, weights: dict[str, float]
    ) -> None:
        ...
