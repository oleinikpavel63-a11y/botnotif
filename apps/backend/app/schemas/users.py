from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..core.rbac import Role


class UserOut(BaseModel):
    id: str
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: Role
    is_active: bool
    last_seen_at: datetime | None = None


class UserCreate(BaseModel):
    telegram_user_id: int
    role: Role = Role.OPERATOR
    first_name: str | None = None
    username: str | None = None


class RoleUpdate(BaseModel):
    role: Role
