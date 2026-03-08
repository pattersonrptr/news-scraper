"""Pydantic v2 schemas for Article endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ArticleResponse(BaseModel):
    """Full article representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID | None = None
    url: str
    title: str
    body: str
    summary: str | None = None
    language: str
    author: str | None = None
    image_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    category: str | None = None
    sentiment: int
    sentiment_score: float
    relevance_score: float
    is_read: bool
    is_processed: bool
    is_partial: bool
    entities: dict[str, list[str]] = Field(default_factory=dict)
    published_at: datetime | None = None
    collected_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ArticleSummaryResponse(BaseModel):
    """Lightweight article representation for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID | None = None
    url: str
    title: str
    summary: str | None = None
    language: str
    author: str | None = None
    image_url: str | None = None
    category: str | None = None
    sentiment: int
    relevance_score: float
    is_read: bool
    is_partial: bool
    published_at: datetime | None = None
    collected_at: datetime | None = None
