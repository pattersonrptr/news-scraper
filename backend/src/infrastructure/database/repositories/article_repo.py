"""SQLAlchemy implementation of ArticleRepository port."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.article import Article
from backend.src.domain.repositories import ArticleRepository
from backend.src.infrastructure.database.models.article import ArticleModel, Base


def _model_to_entity(m: ArticleModel) -> Article:
    return Article(
        id=m.id,
        user_id=m.user_id,
        source_id=m.source_id,
        url=m.url,
        url_hash=m.url_hash,
        content_hash=m.content_hash,
        title=m.title,
        body=m.body_compressed or "",
        summary=m.summary,
        published_at=m.published_at,
        collected_at=m.collected_at,
        language=m.language,
        sentiment=m.sentiment,
        sentiment_score=m.sentiment_score,
        category=m.category,
        entities=m.entities or {},
        relevance_score=m.relevance_score,
        is_processed=m.is_processed,
        is_read=m.is_read,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _entity_to_model(a: Article) -> ArticleModel:
    return ArticleModel(
        id=a.id,
        user_id=a.user_id,
        source_id=a.source_id,
        url=a.url,
        url_hash=a.url_hash,
        content_hash=a.content_hash,
        title=a.title,
        body_compressed=a.body or None,
        summary=a.summary,
        published_at=a.published_at,
        collected_at=a.collected_at,
        language=a.language,
        sentiment=a.sentiment,
        sentiment_score=a.sentiment_score,
        category=a.category,
        entities=a.entities,
        relevance_score=a.relevance_score,
        is_processed=a.is_processed,
        is_read=a.is_read,
    )


class SQLArticleRepository:
    """Concrete SQLAlchemy implementation of ArticleRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, article: Article) -> Article:
        model = _entity_to_model(article)
        self._session.add(model)
        await self._session.flush()
        return _model_to_entity(model)

    async def update(self, article: Article) -> Article:
        model = await self._session.get(ArticleModel, article.id)
        if model is None:
            raise ValueError(f"Article not found: {article.id}")
        model.summary = article.summary
        model.sentiment = article.sentiment
        model.sentiment_score = article.sentiment_score
        model.category = article.category
        model.entities = article.entities
        model.relevance_score = article.relevance_score
        model.is_processed = article.is_processed
        model.is_read = article.is_read
        await self._session.flush()
        return _model_to_entity(model)

    async def get_by_id(self, article_id: uuid.UUID) -> Article | None:
        model = await self._session.get(ArticleModel, article_id)
        return _model_to_entity(model) if model else None

    async def get_by_url_hash(self, url_hash: str) -> Article | None:
        result = await self._session.execute(
            select(ArticleModel).where(ArticleModel.url_hash == url_hash).limit(1)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_content_hash(self, content_hash: str) -> Article | None:
        result = await self._session.execute(
            select(ArticleModel).where(ArticleModel.content_hash == content_hash).limit(1)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def list_unprocessed(self, limit: int = 20) -> list[Article]:
        result = await self._session.execute(
            select(ArticleModel)
            .where(ArticleModel.is_processed.is_(False))
            .order_by(ArticleModel.collected_at.asc())
            .limit(limit)
        )
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list(
        self,
        *,
        user_id: uuid.UUID | None = None,
        source_id: uuid.UUID | None = None,
        category: str | None = None,
        sentiment: int | None = None,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Article]:
        q = select(ArticleModel)
        if user_id is not None:
            q = q.where(ArticleModel.user_id == user_id)
        if source_id is not None:
            q = q.where(ArticleModel.source_id == source_id)
        if category is not None:
            q = q.where(ArticleModel.category == category)
        if sentiment is not None:
            q = q.where(ArticleModel.sentiment == sentiment)
        if is_read is not None:
            q = q.where(ArticleModel.is_read == is_read)
        q = q.order_by(ArticleModel.collected_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(q)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def mark_as_read(self, article_id: uuid.UUID) -> None:
        model = await self._session.get(ArticleModel, article_id)
        if model:
            model.is_read = True
            await self._session.flush()
