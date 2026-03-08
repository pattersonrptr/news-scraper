"""Profile router — /api/v1/profile

MVP: single-user stub. Returns a hard-coded default profile until
multi-user auth is implemented in a later phase.
"""

from __future__ import annotations

import uuid
from datetime import time

from fastapi import APIRouter, status

from backend.src.interfaces.api.schemas.profile import (
    ProfileResponse,
    UpdateInterestsRequest,
)

router = APIRouter(prefix="/profile", tags=["profile"])

# ---------------------------------------------------------------------------
# MVP stub: single in-memory profile (replaced by DB in Phase 6 — multi-user)
# ---------------------------------------------------------------------------
_DEFAULT_PROFILE = ProfileResponse(
    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    display_name="Default User",
    explicit_interests=[],
    implicit_weights={},
    alert_keywords=[],
    digest_time=time(8, 0),
    notification_email="",
    is_active=True,
)

_profile = _DEFAULT_PROFILE.model_copy()


@router.get("", response_model=ProfileResponse)
async def get_profile() -> ProfileResponse:
    """Return the current user profile."""
    return _profile


@router.put("/interests", response_model=ProfileResponse)
async def update_interests(body: UpdateInterestsRequest) -> ProfileResponse:
    """Update explicit interests, alert keywords, digest time, and notification email."""
    global _profile  # noqa: PLW0603 — intentional MVP stub

    updates: dict = {}
    updates["explicit_interests"] = body.explicit_interests
    updates["alert_keywords"] = body.alert_keywords
    if body.digest_time is not None:
        updates["digest_time"] = body.digest_time
    if body.notification_email is not None:
        updates["notification_email"] = body.notification_email

    _profile = _profile.model_copy(update=updates)
    return _profile
