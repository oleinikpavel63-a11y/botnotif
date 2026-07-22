from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class Track(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tracks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_file_unique_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    recommended_volume: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    fade_in_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fade_out_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_announcement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
