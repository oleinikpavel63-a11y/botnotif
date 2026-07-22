from __future__ import annotations

import uuid

from lw_contracts import Priority
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin, UUIDMixin


class CampScenario(UUIDMixin, TimestampMixin, Base):
    """A quick "camp scenario" / preset (Сбор, Подъём, Отбой, ...)."""

    __tablename__ = "scenarios"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    icon: Mapped[str] = mapped_column(String(16), default="🎵", nullable=False)
    track_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tracks.id", ondelete="SET NULL"), nullable=True
    )
    playlist_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("playlists.id", ondelete="SET NULL"), nullable=True
    )
    volume: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    fade_in_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fade_out_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confirmation_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default=Priority.MANUAL.value, nullable=False)
    max_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # JSON-encoded list of allowed role names.
    allowed_roles: Mapped[str] = mapped_column(
        String(255), default='["OWNER","ADMIN","OPERATOR"]', nullable=False
    )
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    schedulable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
