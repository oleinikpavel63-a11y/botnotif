from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ScheduleConfig(BaseModel):
    time: str = Field(examples=["07:30"])
    days: list[int] | None = None  # 0=Mon..6=Sun (weekly)
    date: str | None = None  # YYYY-MM-DD (once)


class ScheduleCreate(BaseModel):
    name: str
    scenario_id: str
    device_id: str
    recurrence_type: Literal["once", "daily", "weekly"] = "daily"
    config: ScheduleConfig
    grace_period_seconds: int | None = None
    allow_conflict: bool = False


class ScheduleOut(BaseModel):
    id: str
    name: str
    scenario_id: str
    device_id: str
    recurrence_type: str
    recurrence_config: str
    timezone: str
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    grace_period_seconds: int
    priority: str
    is_enabled: bool
