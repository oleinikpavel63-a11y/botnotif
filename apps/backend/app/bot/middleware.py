"""Bot middleware: per-update DB session + whitelist authentication.

Unknown / inactive users are rejected here — no handler ever runs for them.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from ..core.logging import get_logger
from ..db.session import SessionLocal
from ..services.auth import AuthService

log = get_logger("bot.mw")

_DENIED = (
    "⛔️ Доступ запрещён.\n"
    "Эта система управляет звуком лагеря «Живая вода».\n"
    "Если вы сотрудник — попросите администратора добавить вас."
)


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = getattr(event, "from_user", None)
        if tg_user is None:
            return None

        async with SessionLocal() as session:
            user = await AuthService(session).resolve_user(
                tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
            )
            if user is None:
                await session.commit()
                await self._deny(event)
                log.info("bot_access_denied", telegram_id=tg_user.id)
                return None

            data["session"] = session
            data["user"] = user
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    async def _deny(event: TelegramObject) -> None:
        if isinstance(event, Message):
            await event.answer(_DENIED)
        elif isinstance(event, CallbackQuery):
            await event.answer(_DENIED, show_alert=True)
