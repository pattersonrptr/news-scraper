"""Domain entity: Article."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Article:
    """Represents a collected and (optionally) AI-analyzed news article."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID | None = None
    source_id: uuid.UUID | None = None

    # Content
    url: str = ""
    url_hash: str = ""
    content_hash: str = ""
    title: str = ""
    body: str = ""  # decompressed at runtime; stored compressed in DB
    summary: str | None = None
    language: str = "en"

    # Timestamps
    published_at: datetime | None = None
    collected_at: datetime | None = None

    # AI analysis
    sentiment: int = 0          # -1 negative | 0 neutral | 1 positive
    sentiment_score: float = 0.0
    category: str | None = None
    entities: dict[str, list[str]] = field(default_factory=dict)
    relevance_score: float = 0.0

    # State flags
    is_processed: bool = False
    is_read: bool = False
    is_partial: bool = False    # paywall / incomplete content

    # Metadata
    author: str | None = None
    image_url: str | None = None
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
