"""SQLAlchemy implementation of SourceRepository port."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.source import Source, SourceType
from backend.src.infrastructure.database.models.source import SourceModel


def _model_to_entity(m: SourceModel) -> Source:
    return Source(
        id=m.id,
        user_id=m.user_id,
        name=m.name,
        url=m.url,
        feed_url=m.feed_url or "",
        source_type=SourceType(m.source_type) if m.source_type else SourceType.RSS,
        language=m.language or "en",
        fetch_interval=m.fetch_interval,
        is_active=m.is_active,
        last_fetched_at=m.last_fetched_at,
        error_count=m.error_count,
        last_error=m.last_error,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _entity_to_model(s: Source) -> SourceModel:
    return SourceModel(
        id=s.id,
        user_id=s.user_id,
        name=s.name,
        url=s.url,
        feed_url=s.feed_url or None,
        source_type=s.source_type.value if isinstance(s.source_type, SourceType) else s.source_type,
        language=s.language,
        fetch_interval=s.fetch_interval,
        is_active=s.is_active,
        last_fetched_at=s.last_fetched_at,
        error_count=s.error_count,
        last_error=s.last_error,
    )


class SQLSourceRepository:
    """Concrete SQLAlchemy implementation of SourceRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, source: Source) -> Source:
        model = _entity_to_model(source)
        self._session.add(model)
        await self._session.flush()
        return _model_to_entity(model)

    async def update(self, source: Source) -> Source:
        model = await self._session.get(SourceModel, source.id)
        if model is None:
            raise ValueError(f"Source not found: {source.id}")
        model.name = source.name
        model.url = source.url
        model.feed_url = source.feed_url or None
        model.source_type = source.source_type.value if isinstance(source.source_type, SourceType) else source.source_type
        model.language = source.language
        model.fetch_interval = source.fetch_interval
        model.is_active = source.is_active
        await self._session.flush()
        return _model_to_entity(model)

    async def delete(self, source_id: uuid.UUID) -> None:
        model = await self._session.get(SourceModel, source_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, source_id: uuid.UUID) -> Source | None:
        model = await self._session.get(SourceModel, source_id)
        return _model_to_entity(model) if model else None

    async def list_active(self) -> list[Source]:
        result = await self._session.execute(
            select(SourceModel).where(SourceModel.is_active.is_(True))
        )
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_all(self, user_id: uuid.UUID | None = None) -> list[Source]:
        q = select(SourceModel)
        if user_id is not None:
            q = q.where(SourceModel.user_id == user_id)
        result = await self._session.execute(q)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def update_last_fetched(self, source_id: uuid.UUID) -> None:
        from datetime import datetime, timezone
        model = await self._session.get(SourceModel, source_id)
        if model:
            model.last_fetched_at = datetime.now(timezone.utc)
            model.error_count = 0
            model.last_error = None
            await self._session.flush()

    async def increment_error_count(self, source_id: uuid.UUID, error: str) -> None:
        model = await self._session.get(SourceModel, source_id)
        if model:
            model.error_count = (model.error_count or 0) + 1
            model.last_error = error
            # Auto-disable after 5 consecutive errors
            if model.error_count >= 5:
                model.is_active = False
            await self._session.flush()
