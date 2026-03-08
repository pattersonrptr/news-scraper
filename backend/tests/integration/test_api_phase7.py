"""Integration tests for Phase 7: /auth API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


# ===========================================================================
# Register
# ===========================================================================


class TestRegisterEndpoint:
    @pytest.mark.asyncio
    async def test_register_new_user_returns_201(self, api_client: AsyncClient):
        res = await api_client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@example.com", "password": "password123"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, api_client: AsyncClient):
        payload = {"email": "dup@example.com", "password": "password123"}
        await api_client.post("/api/v1/auth/register", json=payload)
        res = await api_client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 409


# ===========================================================================
# Login
# ===========================================================================


class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self, api_client: AsyncClient):
        # Register first
        await api_client.post(
            "/api/v1/auth/register",
            json={"email": "loginuser@example.com", "password": "mypassword"},
        )
        # Login
        res = await api_client.post(
            "/api/v1/auth/login",
            data={"username": "loginuser@example.com", "password": "mypassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, api_client: AsyncClient):
        await api_client.post(
            "/api/v1/auth/register",
            json={"email": "wrongpw@example.com", "password": "correct"},
        )
        res = await api_client.post(
            "/api/v1/auth/login",
            data={"username": "wrongpw@example.com", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_email_returns_401(self, api_client: AsyncClient):
        res = await api_client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "anything"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401


# ===========================================================================
# Refresh
# ===========================================================================


class TestRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_refresh_returns_new_access_token(self, api_client: AsyncClient):
        # Register + login to get tokens
        await api_client.post(
            "/api/v1/auth/register",
            json={"email": "refresh@example.com", "password": "pass1234"},
        )
        login_res = await api_client.post(
            "/api/v1/auth/login",
            data={"username": "refresh@example.com", "password": "pass1234"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        tokens = login_res.json()

        res = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert res.status_code == 200
        new_tokens = res.json()
        assert "access_token" in new_tokens

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token_returns_401(self, api_client: AsyncClient):
        res = await api_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.token"},
        )
        assert res.status_code == 401


# ===========================================================================
# Protected endpoints (via conftest.py get_current_user override)
# ===========================================================================


class TestProtectedEndpoints:
    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, api_client: AsyncClient):
        """The api_client fixture overrides get_current_user → _TEST_USER."""
        res = await api_client.get("/api/v1/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_profile_endpoint_requires_auth(self):
        """Without the fixture override no Bearer token → 401."""
        from httpx import ASGITransport, AsyncClient as _Client
        from backend.src.interfaces.api.main import app as _app

        async with _Client(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as raw_client:
            res = await raw_client.get("/api/v1/profile")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_alerts_endpoint_requires_auth(self):
        """Without the fixture override no Bearer token → 401."""
        from httpx import ASGITransport, AsyncClient as _Client
        from backend.src.interfaces.api.main import app as _app

        async with _Client(
            transport=ASGITransport(app=_app), base_url="http://test"
        ) as raw_client:
            res = await raw_client.get("/api/v1/alerts")
        assert res.status_code == 401
