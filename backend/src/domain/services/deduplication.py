"""Deduplication domain service.

Pure business logic — no framework or DB imports.
"""

from __future__ import annotations

from backend.src.domain.repositories import ArticleRepository
from backend.src.domain.value_objects import ArticleHash
from backend.src.core.logging import get_logger

log = get_logger(__name__)


class DeduplicationService:
    """Checks whether an article already exists before storing it."""

    def __init__(self, article_repo: ArticleRepository) -> None:
        self._repo = article_repo

    async def is_duplicate(self, url: str, title: str, body: str) -> bool:
        """Return True if an article with the same URL or content hash already exists."""
        hashes = ArticleHash.from_article_data(url=url, title=title, body=body)

        by_url = await self._repo.get_by_url_hash(hashes.url_hash)
        if by_url is not None:
            log.debug("duplicate_by_url", url=url, url_hash=hashes.url_hash)
            return True

        by_content = await self._repo.get_by_content_hash(hashes.content_hash)
        if by_content is not None:
            log.debug("duplicate_by_content", url=url, content_hash=hashes.content_hash)
            return True

        return False

    def compute_hashes(self, url: str, title: str, body: str) -> ArticleHash:
        """Compute and return the ArticleHash for an article."""
        return ArticleHash.from_article_data(url=url, title=title, body=body)
