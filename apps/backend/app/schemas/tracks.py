from __future__ import annotations

from pydantic import BaseModel, Field


class TrackOut(BaseModel):
    id: str
    title: str
    category: str | None = None
    duration: float | None = None
    size: int | None = None
    sha256: str | None = None
    recommended_volume: int
    fade_in_seconds: float
    fade_out_seconds: float
    is_announcement: bool
    is_active: bool


class TrackUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    recommended_volume: int | None = Field(default=None, ge=0, le=100)
    fade_in_seconds: float | None = Field(default=None, ge=0)
    fade_out_seconds: float | None = Field(default=None, ge=0)
    is_announcement: bool | None = None
    is_active: bool | None = None
