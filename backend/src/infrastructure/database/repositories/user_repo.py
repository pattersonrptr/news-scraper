"""SQLAlchemy implementation of UserRepository.

Replaces the InMemoryUserProfileRepository MVP stub.
Stores all auth + profile data in the `users` table via UserModel.
"""

from __future__ import annotations

import json
import uuid
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.user_profile import UserProfile
from backend.src.infrastructure.database.models.user import UserModel


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _model_to_entity(m: UserModel) -> UserProfile:
    """Convert a UserModel row to a UserProfile domain entity."""
    return UserProfile(
        id=m.id,
        email=m.email,
        hashed_password=m.hashed_password,
        display_name=m.display_name,
        explicit_interests=json.loads(m.explicit_interests),
        implicit_weights=json.loads(m.implicit_weights),
        alert_keywords=json.loads(m.alert_keywords),
        notification_email=m.notification_email,
        digest_time=time(m.digest_hour, 0),
        is_active=m.is_active,
    )


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class SQLUserRepository:
    """Async SQLAlchemy repository for user accounts and their profile data."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create(
        self,
        email: str,
        hashed_password: str,
        display_name: str = "",
    ) -> UserProfile:
        """Insert a new user row and return the created entity."""
        model = UserModel(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            display_name=display_name,
        )
        self._session.add(model)
        await self._session.flush()   # get DB-generated defaults without committing
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def update_profile(self, profile: UserProfile) -> UserProfile:
        """Persist profile changes back to the database."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == profile.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User {profile.id} not found")

        model.display_name = profile.display_name
        model.explicit_interests = json.dumps(profile.explicit_interests)
        model.implicit_weights = json.dumps(profile.implicit_weights)
        model.alert_keywords = json.dumps(profile.alert_keywords)
        model.notification_email = profile.notification_email
        model.digest_hour = profile.digest_time.hour
        model.is_active = profile.is_active

        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def update_implicit_weights(
        self, user_id: uuid.UUID, weights: dict[str, float]
    ) -> None:
        """Merge new weights into the user's implicit_weights map (overwrites existing keys)."""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return
        current: dict[str, float] = json.loads(model.implicit_weights)
        current.update(weights)
        model.implicit_weights = json.dumps(current)
        await self._session.flush()

    async def increment_implicit_weight(
        self, user_id: uuid.UUID, category: str, increment: float = 0.05
    ) -> None:
        """Add `increment` to the user's implicit weight for `category`.

        Creates the category entry if it does not yet exist.
        Caps individual category weights at 1.0 to avoid unbounded growth.
        """
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return
        current: dict[str, float] = json.loads(model.implicit_weights)
        current[category] = min(1.0, current.get(category, 0.0) + increment)
        model.implicit_weights = json.dumps(current)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_by_id(self, user_id: uuid.UUID) -> UserProfile | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_email(self, email: str) -> UserProfile | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_default(self) -> UserProfile | None:
        """Return the first active user — used by single-user tasks (alerts, digest).

        Replaces InMemoryUserProfileRepository.get_default() so that tasks
        read real alert_keywords / notification_email from the database.
        """
        result = await self._session.execute(
            select(UserModel).where(UserModel.is_active.is_(True)).limit(1)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    # ------------------------------------------------------------------
    # Compatibility helpers for old InMemoryUserProfileRepository callers
    # ------------------------------------------------------------------

    async def get(self, user_id: uuid.UUID) -> UserProfile | None:
        """Alias for get_by_id — matches InMemoryUserProfileRepository interface."""
        return await self.get_by_id(user_id)

    async def save(self, profile: UserProfile) -> UserProfile:
        """Alias for update_profile — matches InMemoryUserProfileRepository interface."""
        return await self.update_profile(profile)
