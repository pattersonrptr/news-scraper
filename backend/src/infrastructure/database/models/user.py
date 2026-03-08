"""SQLAlchemy model for users."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    # Personalization (stored as JSON-serialised text for portability)
    explicit_interests: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    implicit_weights: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}"
    )
    alert_keywords: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )

    notification_email: Mapped[str] = mapped_column(String(320), nullable=False, default="")
    digest_hour: Mapped[int] = mapped_column(nullable=False, default=8)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
