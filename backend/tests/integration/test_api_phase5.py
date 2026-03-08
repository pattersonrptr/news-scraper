"""Integration tests for Phase 5 API endpoints:
- GET /alerts, POST /alerts, DELETE /alerts/{id}
- GET /trends
- GET /digest/preview
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.src.domain.entities.article import Article
from backend.src.infrastructure.database.repositories.article_repo import (
    SQLArticleRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_article(
    *,
    title: str = "Test Article",
    category: str | None = "technology",
    sentiment: int = 0,
) -> Article:
    return Article(
        url=f"https://example.com/{uuid.uuid4()}",
        url_hash=str(uuid.uuid4()),
        content_hash=str(uuid.uuid4()),
        title=title,
        body="body",
        language="en",
        sentiment=sentiment,
        category=category,
        collected_at=datetime.now(timezone.utc),
        is_processed=True,
    )


# ===========================================================================
# Alert CRUD
# ===========================================================================


@pytest.mark.asyncio
async def test_list_alerts_empty(api_client: AsyncClient) -> None:
    """GET /alerts returns empty list when no alerts exist."""
    resp = await api_client.get("/api/v1/alerts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_alert(api_client: AsyncClient) -> None:
    """POST /alerts creates and returns an alert log entry."""
    payload = {"trigger_keyword": "python", "channel": "email"}
    resp = await api_client.post("/api/v1/alerts", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["trigger_keyword"] == "python"
    assert data["channel"] == "email"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_alerts_after_create(api_client: AsyncClient) -> None:
    """GET /alerts returns created entries."""
    await api_client.post("/api/v1/alerts", json={"trigger_keyword": "ai"})
    resp = await api_client.get("/api/v1/alerts")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["trigger_keyword"] == "ai"


@pytest.mark.asyncio
async def test_delete_alert(api_client: AsyncClient) -> None:
    """DELETE /alerts/{id} removes the entry and returns 204."""
    create_resp = await api_client.post(
        "/api/v1/alerts", json={"trigger_keyword": "delete-me"}
    )
    alert_id = create_resp.json()["id"]

    del_resp = await api_client.delete(f"/api/v1/alerts/{alert_id}")
    assert del_resp.status_code == 204

    list_resp = await api_client.get("/api/v1/alerts")
    assert list_resp.json() == []


@pytest.mark.asyncio
async def test_delete_nonexistent_alert_returns_404(api_client: AsyncClient) -> None:
    """DELETE /alerts/{id} returns 404 for unknown IDs."""
    fake_id = uuid.uuid4()
    resp = await api_client.delete(f"/api/v1/alerts/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_alert_invalid_channel(api_client: AsyncClient) -> None:
    """POST /alerts rejects invalid channel values."""
    payload = {"trigger_keyword": "test", "channel": "sms"}
    resp = await api_client.post("/api/v1/alerts", json=payload)
    assert resp.status_code == 422


# ===========================================================================
# GET /trends
# ===========================================================================


@pytest.mark.asyncio
async def test_get_trends_empty_db(api_client: AsyncClient) -> None:
    """GET /trends returns empty results when no articles exist."""
    resp = await api_client.get("/api/v1/trends")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_articles"] == 0
    assert data["top_categories"] == []
    assert data["top_keywords"] == []


@pytest.mark.asyncio
async def test_get_trends_with_articles(
    api_client: AsyncClient, db_session
) -> None:
    """GET /trends aggregates data from recently saved articles."""
    repo = SQLArticleRepository(db_session)
    await repo.save(_make_article(title="Python AI framework released", category="technology"))
    await repo.save(_make_article(title="Python tops survey again", category="technology"))
    await db_session.commit()

    resp = await api_client.get("/api/v1/trends?hours=24")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_articles"] == 2
    categories = dict(data["top_categories"])
    assert categories.get("technology", 0) == 2


# ===========================================================================
# GET /digest/preview
# ===========================================================================


@pytest.mark.asyncio
async def test_get_digest_preview_empty(api_client: AsyncClient) -> None:
    """GET /digest/preview returns valid structure with empty sections."""
    resp = await api_client.get("/api/v1/digest/preview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_articles"] == 0
    assert data["sections"] == {}


@pytest.mark.asyncio
async def test_get_digest_preview_with_articles(
    api_client: AsyncClient, db_session
) -> None:
    """GET /digest/preview groups articles by category."""
    repo = SQLArticleRepository(db_session)
    await repo.save(_make_article(title="Tech story 1", category="technology"))
    await repo.save(_make_article(title="Sports story", category="sports"))
    await db_session.commit()

    resp = await api_client.get("/api/v1/digest/preview?hours=24")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_articles"] == 2
    assert "technology" in data["sections"]
    assert "sports" in data["sections"]
    tech_articles = data["sections"]["technology"]
    assert len(tech_articles) == 1
    assert tech_articles[0]["title"] == "Tech story 1"
