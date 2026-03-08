"""Pydantic v2 schemas for Source endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.src.domain.entities.source import SourceType


class SourceResponse(BaseModel):
    """Source representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    feed_url: str
    source_type: SourceType
    language: str
    fetch_interval: int
    is_active: bool
    last_fetched_at: datetime | None = None
    error_count: int
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SourceCreateRequest(BaseModel):
    """Payload for creating a new source."""

    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1)
    feed_url: str = Field(..., min_length=1)
    source_type: SourceType = SourceType.RSS
    language: str = Field(default="en", min_length=2, max_length=10)
    fetch_interval: int = Field(default=60, ge=5, le=1440)   # 5 min – 24 h

    @field_validator("feed_url", "url")
    @classmethod
    def must_start_with_http(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("must be a valid HTTP/HTTPS URL")
        return v


class SourceUpdateRequest(BaseModel):
    """Payload for updating an existing source (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    url: str | None = None
    feed_url: str | None = None
    source_type: SourceType | None = None
    language: str | None = Field(default=None, min_length=2, max_length=10)
    fetch_interval: int | None = Field(default=None, ge=5, le=1440)
    is_active: bool | None = None

    @field_validator("feed_url", "url")
    @classmethod
    def must_start_with_http(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("must be a valid HTTP/HTTPS URL")
        return v
