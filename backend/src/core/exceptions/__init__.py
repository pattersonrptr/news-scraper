"""Custom exception hierarchy for the application.

Usage:
    raise ArticleNotFoundError(article_id)
    raise SourceFetchError(source_url, cause=e)
    raise DuplicateArticleError(url_hash)
"""

from __future__ import annotations

import uuid


class NewsScrapeBaseError(Exception):
    """Base class for all application exceptions."""


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------

class DuplicateArticleError(NewsScrapeBaseError):
    """Raised when an article already exists (deduplication check)."""

    def __init__(self, hash_value: str, hash_type: str = "url") -> None:
        self.hash_value = hash_value
        self.hash_type = hash_type
        super().__init__(f"Duplicate article detected via {hash_type} hash: {hash_value}")


class ArticleNotFoundError(NewsScrapeBaseError):
    """Raised when an article cannot be found."""

    def __init__(self, article_id: uuid.UUID) -> None:
        self.article_id = article_id
        super().__init__(f"Article not found: {article_id}")


class SourceNotFoundError(NewsScrapeBaseError):
    """Raised when a source cannot be found."""

    def __init__(self, source_id: uuid.UUID) -> None:
        self.source_id = source_id
        super().__init__(f"Source not found: {source_id}")


# ---------------------------------------------------------------------------
# Infrastructure exceptions
# ---------------------------------------------------------------------------

class SourceFetchError(NewsScrapeBaseError):
    """Raised when a feed/scraper fails to fetch a source."""

    def __init__(self, source_url: str, cause: Exception | None = None) -> None:
        self.source_url = source_url
        self.cause = cause
        msg = f"Failed to fetch source: {source_url}"
        if cause:
            msg += f" — {cause}"
        super().__init__(msg)


class AIProviderError(NewsScrapeBaseError):
    """Raised when the AI provider returns an error or is unavailable."""

    def __init__(self, provider: str, cause: Exception | None = None) -> None:
        self.provider = provider
        self.cause = cause
        msg = f"AI provider '{provider}' failed"
        if cause:
            msg += f": {cause}"
        super().__init__(msg)


class AIRateLimitError(AIProviderError):
    """Raised when the AI provider rate limit is exceeded."""

    def __init__(self, provider: str) -> None:
        super().__init__(provider)
        self.args = (f"AI provider '{provider}' rate limit exceeded",)


class EmailDeliveryError(NewsScrapeBaseError):
    """Raised when an email fails to send."""

    def __init__(self, recipient: str, cause: Exception | None = None) -> None:
        self.recipient = recipient
        msg = f"Failed to deliver email to {recipient}"
        if cause:
            msg += f": {cause}"
        super().__init__(msg)


class CacheError(NewsScrapeBaseError):
    """Raised on cache read/write failures (non-fatal, should be caught and logged)."""
