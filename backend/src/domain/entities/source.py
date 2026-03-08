"""Domain entity: Source."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Supported collector types."""

    RSS = "rss"
    SCRAPER_BS4 = "scraper_bs4"
    SCRAPER_SCRAPY = "scraper_scrapy"
    SCRAPER_SELENIUM = "scraper_selenium"


@dataclass
class Source:
    """Represents a configured news source."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID | None = None

    name: str = ""
    url: str = ""           # canonical site URL
    feed_url: str = ""      # RSS/Atom feed URL
    source_type: SourceType = SourceType.RSS
    language: str = "en"

    # Scheduling
    fetch_interval: int = 60    # minutes
    is_active: bool = True

    # State
    last_fetched_at: datetime | None = None
    error_count: int = 0
    last_error: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
