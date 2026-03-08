"""In-memory stub implementation of UserProfileRepository.

Used by use cases and tasks in MVP single-user mode.
The singleton profile is populated from the API router's in-memory state
or falls back to a safe default.

This will be replaced by a SQLAlchemy implementation in Phase 7 (multi-user auth).
"""

from __future__ import annotations

import uuid
from datetime import time

from backend.src.domain.entities.user_profile import UserProfile

# ---------------------------------------------------------------------------
# Singleton MVP profile — shared across the process
# ---------------------------------------------------------------------------

_DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

_profile: UserProfile = UserProfile(
    id=_DEFAULT_USER_ID,
    display_name="Default User",
    explicit_interests=[],
    implicit_weights={},
    alert_keywords=[],
    digest_time=time(8, 0),
    notification_email="",
    is_active=True,
)


def get_singleton_profile() -> UserProfile:
    return _profile


def set_singleton_profile(profile: UserProfile) -> None:
    global _profile  # noqa: PLW0603
    _profile = profile


class InMemoryUserProfileRepository:
    """Minimal in-memory UserProfileRepository for MVP single-user mode."""

    async def get(self, user_id: uuid.UUID) -> UserProfile | None:
        if user_id == _profile.id:
            return _profile
        return None

    async def get_default(self) -> UserProfile | None:
        return _profile

    async def save(self, profile: UserProfile) -> UserProfile:
        set_singleton_profile(profile)
        return _profile

    async def update_implicit_weights(
        self, user_id: uuid.UUID, weights: dict[str, float]
    ) -> None:
        if user_id == _profile.id:
            merged = {**_profile.implicit_weights, **weights}
            set_singleton_profile(
                UserProfile(
                    id=_profile.id,
                    email=_profile.email,
                    hashed_password=_profile.hashed_password,
                    display_name=_profile.display_name,
                    explicit_interests=_profile.explicit_interests,
                    implicit_weights=merged,
                    alert_keywords=_profile.alert_keywords,
                    digest_time=_profile.digest_time,
                    notification_email=_profile.notification_email,
                    is_active=_profile.is_active,
                )
            )
