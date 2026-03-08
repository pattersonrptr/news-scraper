"""Use case: RegisterUser.

Validates that the e-mail is not already taken, hashes the password,
and persists the new account via SQLUserRepository.

Returns the created UserProfile on success.
Raises ValueError("email_already_registered") if the e-mail is taken.
"""

from __future__ import annotations

from backend.src.domain.entities.user_profile import UserProfile
from backend.src.infrastructure.auth.password import hash_password
from backend.src.infrastructure.database.repositories.user_repo import SQLUserRepository


class RegisterUserUseCase:
    def __init__(self, user_repo: SQLUserRepository) -> None:
        self._repo = user_repo

    async def execute(
        self,
        email: str,
        password: str,
        display_name: str = "",
    ) -> UserProfile:
        """Register a new user account.

        Parameters
        ----------
        email:
            Unique e-mail address (case-sensitive as stored).
        password:
            Plain-text password — will be hashed before storage.
        display_name:
            Optional human-readable name shown in the UI.

        Raises
        ------
        ValueError
            With message ``"email_already_registered"`` when *email* is taken.
        """
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise ValueError("email_already_registered")

        hashed = hash_password(password)
        return await self._repo.create(
            email=email,
            hashed_password=hashed,
            display_name=display_name,
        )
