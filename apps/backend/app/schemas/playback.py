from __future__ import annotations

from lw_contracts import CommandStatus, DeviceState
from pydantic import BaseModel, Field


class PlayRequest(BaseModel):
    track_id: str | None = None
    scenario_code: str | None = None
    volume: int | None = Field(default=None, ge=0, le=100)
    confirm_high: bool = False


class CommandResultOut(BaseModel):
    command_id: str
    status: CommandStatus
    volume: int | None = None
    track_title: str | None = None
    state: DeviceState | None = None
    message: str | None = None
