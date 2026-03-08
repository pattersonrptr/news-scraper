"""JWT creation and decoding using python-jose.

Tokens are HS256-signed with the jwt_secret_key from Settings.

Token payload schema
--------------------
{
    "sub": "<user_id as str>",
    "type": "access" | "refresh",
    "exp": <unix timestamp>
}
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from backend.src.core.config.settings import get_settings

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "JWTError",
]

_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _build_token(user_id: uuid.UUID, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": _now_utc() + expires_delta,
        "iat": _now_utc(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    """Return a short-lived access JWT for *user_id*."""
    settings = get_settings()
    delta = timedelta(minutes=settings.access_token_expire_minutes)
    return _build_token(user_id, _TOKEN_TYPE_ACCESS, delta)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Return a long-lived refresh JWT for *user_id*."""
    settings = get_settings()
    delta = timedelta(days=settings.refresh_token_expire_days)
    return _build_token(user_id, _TOKEN_TYPE_REFRESH, delta)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.

    Returns the payload dict on success.
    Raises :class:`jose.JWTError` on invalid / expired tokens.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
