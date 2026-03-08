"""Unit tests for Phase 7: password hashing, JWT, and auth use cases."""

from __future__ import annotations

import time
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.src.infrastructure.auth.password import hash_password, verify_password
from backend.src.infrastructure.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.src.use_cases.register_user import RegisterUserUseCase
from backend.src.use_cases.login_user import LoginUserUseCase
from backend.src.domain.entities.user_profile import UserProfile


# ===========================================================================
# Password hashing
# ===========================================================================


class TestPasswordHashing:
    def test_hash_returns_non_empty_string(self):
        hashed = hash_password("secret123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_does_not_equal_plaintext(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"

    def test_verify_correct_password(self):
        plain = "correct-horse-battery-staple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("rightpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt generates a unique salt each time."""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1)
        assert verify_password("same", h2)


# ===========================================================================
# JWT
# ===========================================================================


class TestJWT:
    def test_create_and_decode_access_token(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_access_and_refresh_tokens_differ(self):
        user_id = uuid.uuid4()
        assert create_access_token(user_id) != create_refresh_token(user_id)

    def test_expired_token_raises(self):
        """Override settings to produce an already-expired token."""
        from jose import jwt as _jwt
        from backend.src.core.config.settings import get_settings
        from datetime import datetime, timezone

        settings = get_settings()
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=1),
            "iat": datetime.now(tz=timezone.utc) - timedelta(seconds=60),
        }
        expired_token = _jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        from jose import JWTError
        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_tampered_token_raises(self):
        from jose import JWTError
        token = create_access_token(uuid.uuid4())
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)


# ===========================================================================
# RegisterUserUseCase
# ===========================================================================


def _make_user(email: str) -> UserProfile:
    return UserProfile(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password("pass"),
        display_name="",
        is_active=True,
    )


class TestRegisterUserUseCase:
    @pytest.mark.asyncio
    async def test_register_new_user_returns_profile(self):
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=None)
        repo.create = AsyncMock(return_value=_make_user("new@example.com"))

        uc = RegisterUserUseCase(repo)
        profile = await uc.execute("new@example.com", "password123")

        assert profile.email == "new@example.com"
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self):
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=_make_user("exists@example.com"))

        uc = RegisterUserUseCase(repo)
        with pytest.raises(ValueError, match="email_already_registered"):
            await uc.execute("exists@example.com", "password123")

    @pytest.mark.asyncio
    async def test_register_hashes_password(self):
        """The stored password must NOT be plain text."""
        stored_hashed: list[str] = []

        async def fake_create(email, hashed_password, display_name=""):
            stored_hashed.append(hashed_password)
            return _make_user(email)

        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=None)
        repo.create = fake_create

        uc = RegisterUserUseCase(repo)
        await uc.execute("a@b.com", "plaintext")

        assert stored_hashed[0] != "plaintext"
        assert verify_password("plaintext", stored_hashed[0])


# ===========================================================================
# LoginUserUseCase
# ===========================================================================


class TestLoginUserUseCase:
    @pytest.mark.asyncio
    async def test_login_success_returns_tokens(self):
        user = _make_user("ok@example.com")
        # Override hashed_password to a real bcrypt hash of "password"
        user = UserProfile(
            id=user.id,
            email=user.email,
            hashed_password=hash_password("password"),
            display_name=user.display_name,
            is_active=True,
        )
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=user)

        uc = LoginUserUseCase(repo)
        result = await uc.execute("ok@example.com", "password")

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self):
        user = UserProfile(
            id=uuid.uuid4(),
            email="user@example.com",
            hashed_password=hash_password("correct"),
            is_active=True,
        )
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=user)

        uc = LoginUserUseCase(repo)
        with pytest.raises(ValueError, match="invalid_credentials"):
            await uc.execute("user@example.com", "wrong")

    @pytest.mark.asyncio
    async def test_login_unknown_email_raises(self):
        repo = MagicMock()
        repo.get_by_email = AsyncMock(return_value=None)

        uc = LoginUserUseCase(repo)
        with pytest.raises(ValueError, match="invalid_credentials"):
            await uc.execute("ghost@example.com", "any")
