"""Articles router — /api/v1/articles"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.src.interfaces.api.dependencies import (
    get_article_repo,
    get_current_user,
    get_user_repo,
)
from backend.src.interfaces.api.schemas.article import (
    ArticleResponse,
    ArticleSummaryResponse,
)
from backend.src.interfaces.api.schemas.common import PaginatedResponse
from backend.src.infrastructure.database.repositories.article_repo import (
    SQLArticleRepository,
)
from backend.src.infrastructure.database.repositories.user_repo import (
    SQLUserRepository,
)
from backend.src.domain.entities.user_profile import UserProfile

router = APIRouter(prefix="/articles", tags=["articles"])

# Weight increment applied to a category each time the user reads an article.
_READ_WEIGHT_INCREMENT = 0.05


@router.get("", response_model=PaginatedResponse[ArticleSummaryResponse])
async def list_articles(
    source_id: uuid.UUID | None = Query(default=None, description="Filter by source UUID"),
    category: str | None = Query(default=None, description="Filter by category"),
    sentiment: int | None = Query(default=None, ge=-1, le=1, description="-1 negative | 0 neutral | 1 positive"),
    is_read: bool | None = Query(default=None, description="Filter by read status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repo: SQLArticleRepository = Depends(get_article_repo),
) -> PaginatedResponse[ArticleSummaryResponse]:
    """List articles with optional filters and pagination."""
    articles = await repo.list(
        source_id=source_id,
        category=category,
        sentiment=sentiment,
        is_read=is_read,
        limit=limit,
        offset=offset,
    )
    # Count total for the same filters (no pagination)
    total_articles = await repo.list(
        source_id=source_id,
        category=category,
        sentiment=sentiment,
        is_read=is_read,
        limit=10_000,
        offset=0,
    )
    return PaginatedResponse(
        items=[ArticleSummaryResponse.model_validate(a.__dict__) for a in articles],
        total=len(total_articles),
        limit=limit,
        offset=offset,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: uuid.UUID,
    repo: SQLArticleRepository = Depends(get_article_repo),
) -> ArticleResponse:
    """Retrieve a single article by UUID."""
    article = await repo.get_by_id(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return ArticleResponse.model_validate(article.__dict__)


@router.patch("/{article_id}/read", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def mark_article_read(
    article_id: uuid.UUID,
    repo: SQLArticleRepository = Depends(get_article_repo),
    current_user: UserProfile = Depends(get_current_user),
    user_repo: SQLUserRepository = Depends(get_user_repo),
) -> None:
    """Mark an article as read and immediately increment the user's implicit weight
    for that article's category by _READ_WEIGHT_INCREMENT.
    """
    article = await repo.get_by_id(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    await repo.mark_as_read(article_id)
    if article.category:
        await user_repo.increment_implicit_weight(
            user_id=current_user.id,
            category=article.category,
            increment=_READ_WEIGHT_INCREMENT,
        )
