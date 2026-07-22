from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import PermissionDenied, ValidationError
from ..core.rbac import Permission, Role, require
from ..models import User
from ..repositories import UserRepository
from .audit import AuditService


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.audit = AuditService(session)

    async def list_users(self, actor: User) -> list[User]:
        require(actor.role_enum, Permission.USER_VIEW)
        return await self.repo.list_all()

    async def add_user(
        self,
        actor: User,
        *,
        telegram_user_id: int,
        role: Role,
        first_name: str | None = None,
        username: str | None = None,
        interface: str = "api",
    ) -> User:
        self._assert_can_manage_role(actor, role)
        existing = await self.repo.get_by_telegram_id(telegram_user_id)
        if existing is not None:
            raise ValidationError("Пользователь уже существует.")
        user = User(
            telegram_user_id=telegram_user_id,
            role=role.value,
            first_name=first_name,
            username=username,
            is_active=True,
        )
        self.repo.add(user)
        await self.repo.flush()
        await self.audit.log(
            action="user.add",
            user=actor,
            entity_type="user",
            entity_id=str(user.id),
            interface=interface,
            meta={"telegram_user_id": telegram_user_id, "role": role.value},
        )
        return user

    async def change_role(
        self, actor: User, target_id, new_role: Role, *, interface: str = "api"
    ) -> User:
        target = await self.repo.get_or_404(target_id)
        # Need permission for BOTH the old and the new role level.
        self._assert_can_manage_role(actor, new_role)
        self._assert_can_manage_role(actor, target.role_enum)
        if target.id == actor.id and new_role != actor.role_enum:
            raise PermissionDenied("Нельзя менять собственную роль.")
        old = target.role
        target.role = new_role.value
        await self.audit.log(
            action="user.change_role",
            user=actor,
            entity_type="user",
            entity_id=str(target.id),
            interface=interface,
            meta={"from": old, "to": new_role.value},
        )
        return target

    async def set_active(
        self, actor: User, target_id, is_active: bool, *, interface: str = "api"
    ) -> User:
        target = await self.repo.get_or_404(target_id)
        self._assert_can_manage_role(actor, target.role_enum)
        target.is_active = is_active
        await self.audit.log(
            action="user.set_active",
            user=actor,
            entity_type="user",
            entity_id=str(target.id),
            interface=interface,
            meta={"is_active": is_active},
        )
        return target

    @staticmethod
    def _assert_can_manage_role(actor: User, role: Role) -> None:
        """OWNER manages everyone; ADMIN may only manage OPERATOR/VIEWER."""
        if role in (Role.OWNER, Role.ADMIN):
            require(actor.role_enum, Permission.USER_MANAGE_ADMINS)
        else:
            require(actor.role_enum, Permission.USER_MANAGE_OPERATORS)
