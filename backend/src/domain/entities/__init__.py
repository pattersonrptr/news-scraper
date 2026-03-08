"""Domain entities package."""

from .alert import Alert, NotificationChannel
from .article import Article
from .source import Source, SourceType
from .user_profile import UserProfile

__all__ = [
    "Alert",
    "Article",
    "NotificationChannel",
    "Source",
    "SourceType",
    "UserProfile",
]
