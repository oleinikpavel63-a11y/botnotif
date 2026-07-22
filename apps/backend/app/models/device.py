from __future__ import annotations

from datetime import datetime

from lw_contracts import DeviceStatus
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class Device(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "devices"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    zone: Mapped[str] = mapped_column(String(128), default="Весь лагерь", nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=DeviceStatus.OFFLINE.value, nullable=False
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    audio_device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_volume: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_volume: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
