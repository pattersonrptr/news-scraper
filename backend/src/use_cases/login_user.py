"""Use case: LoginUser.

Verifies the user's credentials and returns a pair of JWT tokens.

Returns a dict with keys: access_token, refresh_token, token_type.
Raises ValueError("invalid_credentials") on any failure so callers
don't learn whether the e-mail exists or the password is wrong.
"""

from __future__ import annotations

from backend.src.infrastructure.auth.jwt import create_access_token, create_refresh_token
from backend.src.infrastructure.auth.password import verify_password
from backend.src.infrastructure.database.repositories.user_repo import SQLUserRepository


class LoginUserUseCase:
    def __init__(self, user_repo: SQLUserRepository) -> None:
        self._repo = user_repo

    async def execute(self, email: str, password: str) -> dict[str, str]:
        """Authenticate *email* / *password* and return JWT tokens.

        Returns
        -------
        dict
            ``{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}``

        Raises
        ------
        ValueError
            With message ``"invalid_credentials"`` when the e-mail does not
            exist or the password is wrong.
        """
        user = await self._repo.get_by_email(email)
        if user is None or not user.is_active:
            raise ValueError("invalid_credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("invalid_credentials")

        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }
