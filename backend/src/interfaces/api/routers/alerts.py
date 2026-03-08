"""Alerts router — /api/v1/alerts

Provides CRUD for the alert notification log.
Alert rules (keywords) are managed via PUT /profile/interests.
All endpoints require a valid Bearer token and are scoped to the
authenticated user.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from backend.src.domain.entities.alert import Alert, NotificationChannel
from backend.src.domain.entities.user_profile import UserProfile
from backend.src.interfaces.api.dependencies import (
    get_alert_repo,
    get_current_user,
)
from backend.src.interfaces.api.schemas.alert import AlertCreateRequest, AlertResponse
from backend.src.infrastructure.database.repositories.alert_repo import SQLAlertRepository

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _to_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        article_id=alert.article_id,
        trigger_keyword=alert.trigger_keyword,
        channel=alert.channel.value,
        sent_at=alert.sent_at,
    )


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    limit: int = 50,
    repo: SQLAlertRepository = Depends(get_alert_repo),
    current_user: UserProfile = Depends(get_current_user),
) -> list[AlertResponse]:
    """Return the most recent alerts for the authenticated user."""
    alerts = await repo.list_by_user(user_id=current_user.id, limit=limit)
    return [_to_response(a) for a in alerts]


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreateRequest,
    repo: SQLAlertRepository = Depends(get_alert_repo),
    current_user: UserProfile = Depends(get_current_user),
) -> AlertResponse:
    """Manually log an alert entry (useful for testing)."""
    alert = Alert(
        user_id=current_user.id,
        article_id=body.article_id,
        trigger_keyword=body.trigger_keyword,
        channel=NotificationChannel(body.channel),
    )
    saved = await repo.save(alert)
    return _to_response(saved)


@router.delete("/{alert_id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: uuid.UUID,
    repo: SQLAlertRepository = Depends(get_alert_repo),
    current_user: UserProfile = Depends(get_current_user),
) -> None:
    """Delete an alert log entry by ID (must belong to the authenticated user)."""
    existing = await repo.get_by_id(alert_id)
    if existing is None or existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await repo.delete(alert_id)
