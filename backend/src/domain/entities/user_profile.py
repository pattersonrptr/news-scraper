"""Domain entity: UserProfile."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import time


@dataclass
class UserProfile:
    """Represents a user's profile, preferences, and personalization data."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str = ""
    hashed_password: str = ""
    display_name: str = ""

    # Personalization
    explicit_interests: list[str] = field(default_factory=list)
    # e.g. {"tech": 0.85, "economy": 0.42} — learned from read history
    implicit_weights: dict[str, float] = field(default_factory=dict)

    # Alerts
    alert_keywords: list[str] = field(default_factory=list)

    # Notifications
    digest_time: time = field(default_factory=lambda: time(8, 0))   # 08:00 UTC
    notification_email: str = ""

    is_active: bool = True
