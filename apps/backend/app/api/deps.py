from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import AuthError, PermissionDenied
from ..core.rbac import Permission, has_permission
from ..core.security import decode_access_token
from ..db.session import get_session
from ..models import User
from ..repositories import UserRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("Требуется авторизация.")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    telegram_id = int(payload["sub"])
    user = await UserRepository(session).get_by_telegram_id(telegram_id)
    if user is None or not user.is_active:
        raise AuthError("Пользователь не найден или отключён.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission: Permission):
    """Dependency factory enforcing a permission on the backend (never trust UI)."""

    async def _dep(user: CurrentUser) -> User:
        if not has_permission(user.role_enum, permission):
            raise PermissionDenied("Недостаточно прав для этого действия.")
        return user

    return _dep
