from __future__ import annotations

from lw_contracts import Priority
from pydantic import BaseModel, Field

from ..core.rbac import Role


class ScenarioOut(BaseModel):
    id: str
    code: str
    name: str
    icon: str
    track_id: str | None = None
    playlist_id: str | None = None
    volume: int
    fade_in_seconds: float
    fade_out_seconds: float
    confirmation_required: bool
    priority: Priority
    color: str | None = None
    allowed_roles: list[Role]
    is_active: bool


class ScenarioUpsert(BaseModel):
    code: str
    name: str
    icon: str = "🎵"
    volume: int = Field(default=60, ge=0, le=100)
    fade_in_seconds: float = Field(default=0, ge=0)
    fade_out_seconds: float = Field(default=0, ge=0)
    confirmation_required: bool = True
    track_id: str | None = None
    allowed_roles: list[Role] = [Role.OWNER, Role.ADMIN, Role.OPERATOR]
    color: str | None = None
