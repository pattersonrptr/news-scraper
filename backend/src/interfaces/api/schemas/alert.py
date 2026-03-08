"""Pydantic schemas for Alert responses and requests."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AlertResponse(BaseModel):
    """Schema returned by GET /alerts and POST /alerts."""

    id: uuid.UUID
    user_id: uuid.UUID | None = None
    article_id: uuid.UUID | None = None
    trigger_keyword: str
    channel: str
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}


class AlertCreateRequest(BaseModel):
    """Schema accepted by POST /alerts (manually log an alert)."""

    trigger_keyword: str = Field(..., min_length=1, max_length=200)
    article_id: uuid.UUID | None = None
    channel: str = Field(default="email", pattern=r"^(email|telegram|webhook)$")
