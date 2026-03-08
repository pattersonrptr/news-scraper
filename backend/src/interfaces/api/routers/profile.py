"""Profile router — /api/v1/profile

All endpoints require a valid Bearer token.
Data is persisted to the `users` table via SQLUserRepository.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.src.domain.entities.user_profile import UserProfile
from backend.src.infrastructure.database.repositories.user_repo import SQLUserRepository
from backend.src.interfaces.api.dependencies import get_current_user, get_user_repo
from backend.src.interfaces.api.schemas.profile import (
    ProfileResponse,
    UpdateInterestsRequest,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _entity_to_response(profile: UserProfile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        explicit_interests=profile.explicit_interests,
        implicit_weights=profile.implicit_weights,
        alert_keywords=profile.alert_keywords,
        digest_time=profile.digest_time,
        notification_email=profile.notification_email,
        is_active=profile.is_active,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: UserProfile = Depends(get_current_user),
) -> ProfileResponse:
    """Return the authenticated user's profile."""
    return _entity_to_response(current_user)


@router.put("/interests", response_model=ProfileResponse)
async def update_interests(
    body: UpdateInterestsRequest,
    current_user: UserProfile = Depends(get_current_user),
    user_repo: SQLUserRepository = Depends(get_user_repo),
) -> ProfileResponse:
    """Update explicit interests, alert keywords, digest time, and notification email."""
    updated = UserProfile(
        id=current_user.id,
        email=current_user.email,
        hashed_password=current_user.hashed_password,
        display_name=current_user.display_name,
        explicit_interests=body.explicit_interests,
        implicit_weights=current_user.implicit_weights,
        alert_keywords=body.alert_keywords,
        digest_time=(
            body.digest_time if body.digest_time is not None else current_user.digest_time
        ),
        notification_email=(
            body.notification_email
            if body.notification_email is not None
            else current_user.notification_email
        ),
        is_active=current_user.is_active,
    )
    saved = await user_repo.update_profile(updated)
    return _entity_to_response(saved)

