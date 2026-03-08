"""Auth router — /api/v1/auth

Endpoints
---------
POST /auth/register   — create a new account
POST /auth/login      — OAuth2 password flow → access + refresh tokens
POST /auth/refresh    — exchange a refresh token for a new access token
POST /auth/logout     — client-side only (stateless JWT); returns 204
GET  /auth/me         — return the currently authenticated user's profile
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from pydantic import BaseModel, EmailStr

from backend.src.domain.entities.user_profile import UserProfile
from backend.src.infrastructure.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.src.infrastructure.database.repositories.user_repo import SQLUserRepository
from backend.src.interfaces.api.dependencies import get_current_user, get_user_repo
from backend.src.use_cases.login_user import LoginUserUseCase
from backend.src.use_cases.register_user import RegisterUserUseCase

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Pydantic schemas (auth-only; not shared with other modules)
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserMeResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    is_active: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    user_repo: SQLUserRepository = Depends(get_user_repo),
) -> UserMeResponse:
    """Create a new user account."""
    use_case = RegisterUserUseCase(user_repo)
    try:
        profile: UserProfile = await use_case.execute(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
        )
    except ValueError as exc:
        if "email_already_registered" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this e-mail already exists.",
            )
        raise
    return UserMeResponse(
        id=profile.id,
        email=profile.email,
        display_name=profile.display_name,
        is_active=profile.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    user_repo: SQLUserRepository = Depends(get_user_repo),
) -> TokenResponse:
    """Authenticate with e-mail + password and receive JWT tokens.

    Uses OAuth2 password flow so Swagger UI's "Authorize" button works.
    ``username`` field carries the e-mail address.
    """
    use_case = LoginUserUseCase(user_repo)
    try:
        tokens = await use_case.execute(email=form.username, password=form.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect e-mail or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    user_repo: SQLUserRepository = Depends(get_user_repo),
) -> TokenResponse:
    """Issue a new access token from a valid refresh token."""
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise invalid_exc
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise invalid_exc

    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise invalid_exc

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", response_model=None, status_code=status.HTTP_200_OK)
async def logout() -> dict:
    """Stateless logout — the client should discard its tokens.

    A future enhancement could add the refresh token to a Redis blocklist here.
    """
    return {"detail": "logged out"}


@router.get("/me", response_model=UserMeResponse)
async def me(
    current_user: UserProfile = Depends(get_current_user),
) -> UserMeResponse:
    """Return the currently authenticated user's basic profile."""
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
    )
