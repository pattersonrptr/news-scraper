"""SQLAlchemy implementation of AlertRepository port."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.entities.alert import Alert, NotificationChannel
from backend.src.infrastructure.database.models.alert import AlertModel


def _model_to_entity(m: AlertModel) -> Alert:
    return Alert(
        id=m.id,
        user_id=m.user_id,
        article_id=m.article_id,
        trigger_keyword=m.trigger_keyword,
        channel=NotificationChannel(m.channel),
        sent_at=m.sent_at,
    )


def _entity_to_model(a: Alert) -> AlertModel:
    return AlertModel(
        id=a.id,
        user_id=a.user_id,
        article_id=a.article_id,
        trigger_keyword=a.trigger_keyword,
        channel=a.channel.value,
        sent_at=a.sent_at,
    )


class SQLAlertRepository:
    """Concrete SQLAlchemy implementation of AlertRepository port."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, alert: Alert) -> Alert:
        model = _entity_to_model(alert)
        self._session.add(model)
        await self._session.flush()
        return _model_to_entity(model)

    async def get_by_id(self, alert_id: uuid.UUID) -> Alert | None:
        model = await self._session.get(AlertModel, alert_id)
        return _model_to_entity(model) if model else None

    async def list_by_user(self, user_id: uuid.UUID, limit: int = 100) -> list[Alert]:
        result = await self._session.execute(
            select(AlertModel)
            .where(AlertModel.user_id == user_id)
            .order_by(AlertModel.created_at.desc())
            .limit(limit)
        )
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_recent_by_keyword(
        self,
        keyword: str,
        user_id: uuid.UUID | None,
        since: datetime,
    ) -> list[Alert]:
        """Return alerts fired for a keyword since a given datetime (for rate-limiting)."""
        q = (
            select(AlertModel)
            .where(AlertModel.trigger_keyword == keyword)
            .where(AlertModel.sent_at >= since)
        )
        if user_id is not None:
            q = q.where(AlertModel.user_id == user_id)
        result = await self._session.execute(q)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def delete(self, alert_id: uuid.UUID) -> None:
        model = await self._session.get(AlertModel, alert_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()
