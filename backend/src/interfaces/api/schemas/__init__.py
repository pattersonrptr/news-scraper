"""API schemas package."""

from backend.src.interfaces.api.schemas.alert import (
    AlertCreateRequest,
    AlertResponse,
)
from backend.src.interfaces.api.schemas.article import (
    ArticleResponse,
    ArticleSummaryResponse,
)
from backend.src.interfaces.api.schemas.common import PaginatedResponse
from backend.src.interfaces.api.schemas.profile import (
    ProfileResponse,
    UpdateInterestsRequest,
)
from backend.src.interfaces.api.schemas.source import (
    SourceCreateRequest,
    SourceResponse,
    SourceUpdateRequest,
)

__all__ = [
    "AlertCreateRequest",
    "AlertResponse",
    "ArticleResponse",
    "ArticleSummaryResponse",
    "PaginatedResponse",
    "ProfileResponse",
    "SourceCreateRequest",
    "SourceResponse",
    "SourceUpdateRequest",
    "UpdateInterestsRequest",
]
