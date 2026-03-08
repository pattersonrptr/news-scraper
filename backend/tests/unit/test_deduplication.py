"""Unit tests for DeduplicationService and ArticleHash value object."""

from __future__ import annotations

import pytest

from backend.src.domain.value_objects import ArticleHash


class TestArticleHashNormalization:
    """Test URL normalization and hash generation."""

    def test_strips_utm_params(self) -> None:
        url1 = "https://example.com/article?utm_source=twitter&utm_medium=social"
        url2 = "https://example.com/article"
        h1 = ArticleHash.from_article_data(url1, "Title", "Body")
        h2 = ArticleHash.from_article_data(url2, "Title", "Body")
        assert h1.url_hash == h2.url_hash

    def test_strips_www(self) -> None:
        url1 = "https://www.example.com/article"
        url2 = "https://example.com/article"
        h1 = ArticleHash.from_article_data(url1, "Title", "Body")
        h2 = ArticleHash.from_article_data(url2, "Title", "Body")
        assert h1.url_hash == h2.url_hash

    def test_strips_trailing_slash(self) -> None:
        url1 = "https://example.com/article/"
        url2 = "https://example.com/article"
        h1 = ArticleHash.from_article_data(url1, "Title", "Body")
        h2 = ArticleHash.from_article_data(url2, "Title", "Body")
        assert h1.url_hash == h2.url_hash

    def test_different_urls_produce_different_hashes(self) -> None:
        h1 = ArticleHash.from_article_data("https://example.com/a", "T", "B")
        h2 = ArticleHash.from_article_data("https://example.com/b", "T", "B")
        assert h1.url_hash != h2.url_hash

    def test_content_hash_uses_title_and_body_prefix(self) -> None:
        h1 = ArticleHash.from_article_data("https://a.com", "Same Title", "Same body")
        h2 = ArticleHash.from_article_data("https://b.com", "Same Title", "Same body")
        # Different URLs but same content → same content_hash (repost detection)
        assert h1.content_hash == h2.content_hash

    def test_content_hash_differs_on_different_content(self) -> None:
        h1 = ArticleHash.from_article_data("https://a.com", "Title A", "Body A")
        h2 = ArticleHash.from_article_data("https://a.com", "Title B", "Body B")
        assert h1.content_hash != h2.content_hash

    def test_hash_is_64_char_hex(self) -> None:
        h = ArticleHash.from_article_data("https://example.com", "T", "B")
        assert len(h.url_hash) == 64
        assert len(h.content_hash) == 64
        assert all(c in "0123456789abcdef" for c in h.url_hash)


class TestDeduplicationService:
    """Test DeduplicationService with a mock repository."""

    @pytest.mark.asyncio
    async def test_returns_false_when_article_is_new(self) -> None:
        from unittest.mock import AsyncMock
        from backend.src.domain.services.deduplication import DeduplicationService

        repo = AsyncMock()
        repo.get_by_url_hash.return_value = None
        repo.get_by_content_hash.return_value = None

        service = DeduplicationService(article_repo=repo)
        result = await service.is_duplicate(
            url="https://example.com/new-article",
            title="New Article",
            body="Some content here",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_on_url_hash_match(self) -> None:
        from unittest.mock import AsyncMock
        from backend.src.domain.entities import Article
        from backend.src.domain.services.deduplication import DeduplicationService

        repo = AsyncMock()
        repo.get_by_url_hash.return_value = Article()  # any truthy value
        repo.get_by_content_hash.return_value = None

        service = DeduplicationService(article_repo=repo)
        result = await service.is_duplicate(
            url="https://example.com/existing",
            title="Existing Article",
            body="Some content",
        )
        assert result is True
        repo.get_by_content_hash.assert_not_called()  # short-circuit

    @pytest.mark.asyncio
    async def test_returns_true_on_content_hash_match(self) -> None:
        from unittest.mock import AsyncMock
        from backend.src.domain.entities import Article
        from backend.src.domain.services.deduplication import DeduplicationService

        repo = AsyncMock()
        repo.get_by_url_hash.return_value = None
        repo.get_by_content_hash.return_value = Article()

        service = DeduplicationService(article_repo=repo)
        result = await service.is_duplicate(
            url="https://repost-site.com/same-article",
            title="Reposted Article",
            body="Same content as another site",
        )
        assert result is True
