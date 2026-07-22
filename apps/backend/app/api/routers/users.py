from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.rbac import Permission
from ...models import User
from ...schemas import RoleUpdate, UserCreate, UserOut
from ...services.users import UserService
from ..deps import CurrentUser, SessionDep, require_permission
from ..serializers import user_out

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    session: SessionDep,
    user: User = Depends(require_permission(Permission.USER_VIEW)),
) -> list[UserOut]:
    return [user_out(u) for u in await UserService(session).list_users(user)]


@router.post("/users", response_model=UserOut)
async def add_user(payload: UserCreate, session: SessionDep, user: CurrentUser) -> UserOut:
    created = await UserService(session).add_user(
        user,
        telegram_user_id=payload.telegram_user_id,
        role=payload.role,
        first_name=payload.first_name,
        username=payload.username,
        interface="api",
    )
    return user_out(created)


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def change_role(
    user_id: str, payload: RoleUpdate, session: SessionDep, user: CurrentUser
) -> UserOut:
    updated = await UserService(session).change_role(user, user_id, payload.role, interface="api")
    return user_out(updated)
