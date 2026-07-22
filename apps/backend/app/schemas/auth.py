from __future__ import annotations

from pydantic import BaseModel

from ..core.rbac import Role


class TelegramAuthRequest(BaseModel):
    init_data: str


class CurrentUserOut(BaseModel):
    id: str
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    role: Role
    is_active: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: CurrentUserOut
