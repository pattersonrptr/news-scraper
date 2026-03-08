"""Pydantic v2 schemas for UserProfile endpoints."""

from __future__ import annotations

import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class ProfileResponse(BaseModel):
    """User profile representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    explicit_interests: list[str]
    implicit_weights: dict[str, float]
    alert_keywords: list[str]
    digest_time: time
    notification_email: str
    is_active: bool


class UpdateInterestsRequest(BaseModel):
    """Payload for updating explicit interests and alert keywords."""

    explicit_interests: list[str] = Field(default_factory=list)
    alert_keywords: list[str] = Field(default_factory=list)
    digest_time: time | None = None
    notification_email: str | None = None
