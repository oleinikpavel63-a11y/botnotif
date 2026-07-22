from __future__ import annotations

import uuid
from datetime import datetime

from lw_contracts import Priority
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class Schedule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "schedules"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    # once | daily | weekly
    recurrence_type: Mapped[str] = mapped_column(String(16), default="daily", nullable=False)
    # JSON string: {"time": "07:30", "days": [0,1,..6], "date": "2026-07-01"}
    recurrence_config: Mapped[str] = mapped_column(String(512), default="{}", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Chisinau", nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), default=Priority.SCHEDULED_EVENT.value, nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
