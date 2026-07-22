from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import AuthError
from ..core.rbac import Role
from ..core.security import validate_init_data
from ..core.time import utcnow
from ..models import User
from ..repositories import UserRepository


class AuthService:
    """Identity + whitelist. Only users present and active may act."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def resolve_user(
        self,
        telegram_user_id: int,
        *,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        touch: bool = True,
    ) -> User | None:
        """Return the whitelisted user for this Telegram id, or ``None`` if denied.

        The configured ``INITIAL_OWNER_TELEGRAM_ID`` is auto-provisioned as OWNER
        the first time they appear (so the very first admin can bootstrap).
        """
        user = await self.repo.get_by_telegram_id(telegram_user_id)
        if user is None:
            if (
                settings.initial_owner_telegram_id
                and telegram_user_id == settings.initial_owner_telegram_id
            ):
                user = User(
                    telegram_user_id=telegram_user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    role=Role.OWNER.value,
                    is_active=True,
                )
                self.repo.add(user)
                await self.repo.flush()
            else:
                return None

        if not user.is_active:
            return None

        # Refresh lightweight profile info + last-seen.
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        if last_name and user.last_name != last_name:
            user.last_name = last_name
        if touch:
            user.last_seen_at = utcnow()
        return user

    async def authenticate_init_data(self, init_data: str) -> User:
        """Validate Telegram Mini App ``initData`` and return the whitelisted user."""
        fields = validate_init_data(
            init_data,
            settings.telegram_bot_token,
            max_age_seconds=settings.initdata_max_age_seconds,
        )
        raw_user = fields.get("user")
        if not raw_user:
            raise AuthError("Данные пользователя отсутствуют.")
        try:
            tg_user = json.loads(raw_user)
        except json.JSONDecodeError as exc:
            raise AuthError("Некорректные данные пользователя.") from exc

        user = await self.resolve_user(
            int(tg_user["id"]),
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            last_name=tg_user.get("last_name"),
        )
        if user is None:
            raise AuthError("Доступ запрещён. Обратитесь к администратору лагеря.")
        return user
