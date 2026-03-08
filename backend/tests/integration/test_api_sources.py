"""Integration tests for the Sources REST API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_sources_empty(api_client: AsyncClient) -> None:
    """GET /sources returns empty list when no sources exist."""
    resp = await api_client.get("/api/v1/sources")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_source(api_client: AsyncClient) -> None:
    """POST /sources creates a source and returns 201 with the new resource."""
    payload = {
        "name": "Test Feed",
        "url": "https://example.com",
        "feed_url": "https://example.com/feed.rss",
        "source_type": "rss",
        "language": "en",
        "fetch_interval": 60,
    }
    resp = await api_client.post("/api/v1/sources", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Feed"
    assert data["feed_url"] == "https://example.com/feed.rss"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sources_returns_created(api_client: AsyncClient) -> None:
    """GET /sources lists the source that was just created."""
    await api_client.post("/api/v1/sources", json={
        "name": "My Feed",
        "url": "https://myfeed.com",
        "feed_url": "https://myfeed.com/rss",
        "language": "en",
    })
    resp = await api_client.get("/api/v1/sources")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "My Feed"


@pytest.mark.asyncio
async def test_get_source_by_id(api_client: AsyncClient) -> None:
    """GET /sources/{id} returns the correct source."""
    create_resp = await api_client.post("/api/v1/sources", json={
        "name": "BBC World",
        "url": "https://bbc.com",
        "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "language": "en",
    })
    source_id = create_resp.json()["id"]

    resp = await api_client.get(f"/api/v1/sources/{source_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == source_id
    assert resp.json()["name"] == "BBC World"


@pytest.mark.asyncio
async def test_get_source_not_found(api_client: AsyncClient) -> None:
    """GET /sources/{id} returns 404 for an unknown UUID."""
    resp = await api_client.get("/api/v1/sources/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_source(api_client: AsyncClient) -> None:
    """PUT /sources/{id} updates the source fields."""
    create_resp = await api_client.post("/api/v1/sources", json={
        "name": "Old Name",
        "url": "https://example.com",
        "feed_url": "https://example.com/feed.rss",
        "language": "en",
    })
    source_id = create_resp.json()["id"]

    update_resp = await api_client.put(f"/api/v1/sources/{source_id}", json={
        "name": "New Name",
        "is_active": False,
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "New Name"
    assert update_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_source(api_client: AsyncClient) -> None:
    """DELETE /sources/{id} removes the source and returns 204."""
    create_resp = await api_client.post("/api/v1/sources", json={
        "name": "To Delete",
        "url": "https://delete.me",
        "feed_url": "https://delete.me/feed.rss",
        "language": "en",
    })
    source_id = create_resp.json()["id"]

    del_resp = await api_client.delete(f"/api/v1/sources/{source_id}")
    assert del_resp.status_code == 204

    # Verify it's gone
    get_resp = await api_client.get(f"/api/v1/sources/{source_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_source_not_found(api_client: AsyncClient) -> None:
    """DELETE /sources/{id} returns 404 for unknown UUID."""
    resp = await api_client.delete("/api/v1/sources/00000000-0000-0000-0000-000000000099")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_source_invalid_url(api_client: AsyncClient) -> None:
    """POST /sources rejects feed_url that doesn't start with http(s)://"""
    resp = await api_client.post("/api/v1/sources", json={
        "name": "Bad URL",
        "url": "https://example.com",
        "feed_url": "ftp://not-http.com/feed",
        "language": "en",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_sources_active_only_filter(api_client: AsyncClient) -> None:
    """GET /sources?active_only=true returns only active sources."""
    # Create active source
    await api_client.post("/api/v1/sources", json={
        "name": "Active Feed",
        "url": "https://active.com",
        "feed_url": "https://active.com/rss",
        "language": "en",
    })
    # Create then disable a source
    resp = await api_client.post("/api/v1/sources", json={
        "name": "Inactive Feed",
        "url": "https://inactive.com",
        "feed_url": "https://inactive.com/rss",
        "language": "en",
    })
    source_id = resp.json()["id"]
    await api_client.put(f"/api/v1/sources/{source_id}", json={"is_active": False})

    active_resp = await api_client.get("/api/v1/sources?active_only=true")
    assert active_resp.status_code == 200
    assert len(active_resp.json()) == 1
    assert active_resp.json()[0]["name"] == "Active Feed"
