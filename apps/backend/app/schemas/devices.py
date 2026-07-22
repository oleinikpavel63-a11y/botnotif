from __future__ import annotations

from datetime import datetime

from lw_contracts import DeviceState, DeviceStatus
from pydantic import BaseModel, Field


class DeviceOut(BaseModel):
    id: str
    code: str
    name: str
    zone: str
    status: DeviceStatus
    online: bool
    last_seen_at: datetime | None = None
    audio_device_name: str | None = None
    default_volume: int
    max_volume: int
    app_version: str | None = None
    is_active: bool
    live: DeviceState | None = None


class VolumeUpdate(BaseModel):
    volume: int = Field(ge=0, le=100)
    confirm_high: bool = False
