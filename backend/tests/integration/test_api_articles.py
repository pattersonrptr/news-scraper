"""Integration tests for the Articles REST API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from httpx import AsyncClient

from backend.src.domain.entities.article import Article
from backend.src.infrastructure.database.repositories.article_repo import (
    SQLArticleRepository,
)


def _make_article(
    url: str = "https://example.com/article-1",
    title: str = "Test Article",
    body: str = "Article body content.",
    language: str = "en",
    sentiment: int = 0,
    sentiment_score: float = 0.0,
    relevance_score: float = 0.5,
    is_processed: bool = False,
    is_read: bool = False,
    is_partial: bool = False,
    category: str | None = None,
    url_hash: str | None = None,
    content_hash: str | None = None,
    **_: Any,
) -> Article:
    """Helper to build a minimal Article entity."""
    return Article(
        url=url,
        url_hash=url_hash or str(uuid.uuid4()),
        content_hash=content_hash or str(uuid.uuid4()),
        title=title,
        body=body,
        language=language,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        relevance_score=relevance_score,
        is_processed=is_processed,
        is_read=is_read,
        is_partial=is_partial,
        category=category,
        collected_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_list_articles_empty(api_client: AsyncClient) -> None:
    """GET /articles returns paginated empty response."""
    resp = await api_client.get("/api/v1/articles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_articles_returns_saved_article(
    api_client: AsyncClient,
    db_session,
) -> None:
    """GET /articles lists articles saved to the DB."""
    repo = SQLArticleRepository(db_session)
    article = _make_article(title="My Test Article")
    await repo.save(article)
    await db_session.commit()

    resp = await api_client.get("/api/v1/articles")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "My Test Article"


@pytest.mark.asyncio
async def test_get_article_by_id(
    api_client: AsyncClient,
    db_session,
) -> None:
    """GET /articles/{id} returns the correct article."""
    repo = SQLArticleRepository(db_session)
    article = _make_article(title="Specific Article")
    saved = await repo.save(article)
    await db_session.commit()

    resp = await api_client.get(f"/api/v1/articles/{saved.id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Specific Article"
    assert resp.json()["id"] == str(saved.id)


@pytest.mark.asyncio
async def test_get_article_not_found(api_client: AsyncClient) -> None:
    """GET /articles/{id} returns 404 for an unknown UUID."""
    resp = await api_client.get("/api/v1/articles/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_article_read(
    api_client: AsyncClient,
    db_session,
) -> None:
    """PATCH /articles/{id}/read sets is_read=True."""
    repo = SQLArticleRepository(db_session)
    article = _make_article(is_read=False)
    saved = await repo.save(article)
    await db_session.commit()

    resp = await api_client.patch(f"/api/v1/articles/{saved.id}/read")
    assert resp.status_code == 204

    # Verify state in DB
    updated = await repo.get_by_id(saved.id)
    assert updated is not None
    assert updated.is_read is True


@pytest.mark.asyncio
async def test_mark_article_read_not_found(api_client: AsyncClient) -> None:
    """PATCH /articles/{id}/read returns 404 for an unknown UUID."""
    resp = await api_client.patch("/api/v1/articles/00000000-0000-0000-0000-000000000099/read")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_articles_pagination(
    api_client: AsyncClient,
    db_session,
) -> None:
    """GET /articles honours limit and offset query params."""
    repo = SQLArticleRepository(db_session)
    for i in range(5):
        await repo.save(_make_article(
            url=f"https://example.com/article-{i}",
            url_hash=str(uuid.uuid4()),
            content_hash=str(uuid.uuid4()),
            title=f"Article {i}",
        ))
    await db_session.commit()

    resp = await api_client.get("/api/v1/articles?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_articles_filter_by_sentiment(
    api_client: AsyncClient,
    db_session,
) -> None:
    """GET /articles?sentiment=1 returns only positive articles."""
    repo = SQLArticleRepository(db_session)
    await repo.save(_make_article(
        url="https://example.com/pos",
        url_hash=str(uuid.uuid4()),
        content_hash=str(uuid.uuid4()),
        title="Positive",
        sentiment=1,
    ))
    await repo.save(_make_article(
        url="https://example.com/neg",
        url_hash=str(uuid.uuid4()),
        content_hash=str(uuid.uuid4()),
        title="Negative",
        sentiment=-1,
    ))
    await db_session.commit()

    resp = await api_client.get("/api/v1/articles?sentiment=1")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Positive"


@pytest.mark.asyncio
async def test_list_articles_filter_is_read(
    api_client: AsyncClient,
    db_session,
) -> None:
    """GET /articles?is_read=false returns only unread articles."""
    repo = SQLArticleRepository(db_session)
    await repo.save(_make_article(
        url="https://example.com/read",
        url_hash=str(uuid.uuid4()),
        content_hash=str(uuid.uuid4()),
        title="Read Article",
        is_read=True,
    ))
    await repo.save(_make_article(
        url="https://example.com/unread",
        url_hash=str(uuid.uuid4()),
        content_hash=str(uuid.uuid4()),
        title="Unread Article",
        is_read=False,
    ))
    await db_session.commit()

    resp = await api_client.get("/api/v1/articles?is_read=false")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Unread Article"
