"""Domain entity: Alert."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NotificationChannel(str, Enum):
    """Supported notification channels."""

    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """Represents a triggered keyword alert for a user."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID | None = None
    article_id: uuid.UUID | None = None

    trigger_keyword: str = ""
    channel: NotificationChannel = NotificationChannel.EMAIL
    sent_at: datetime | None = None
