"""Bot/Dispatcher construction and lifecycle (long polling or webhook)."""

from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from ..core.config import settings
from ..core.logging import get_logger
from .handlers import router
from .middleware import AuthMiddleware

log = get_logger("bot.setup")

_COMMANDS = [
    BotCommand(command="start", description="Открыть панель управления"),
    BotCommand(command="panel", description="Панель управления"),
    BotCommand(command="play", description="Выбрать и включить музыку"),
    BotCommand(command="now", description="Что сейчас играет"),
    BotCommand(command="pause", description="Пауза"),
    BotCommand(command="resume", description="Продолжить"),
    BotCommand(command="stop", description="Остановить"),
    BotCommand(command="volume", description="Громкость (например /volume 60)"),
    BotCommand(command="scenarios", description="Быстрые сценарии"),
    BotCommand(command="devices", description="Состояние рупоров"),
    BotCommand(command="schedule", description="Расписание"),
    BotCommand(command="help", description="Помощь"),
]


def build_bot() -> Bot:
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    mw = AuthMiddleware()
    dp.message.middleware(mw)
    dp.callback_query.middleware(mw)
    dp.include_router(router)
    return dp


class BotRuntime:
    """Owns the bot + dispatcher and the polling task (LOCAL_MVP)."""

    def __init__(self) -> None:
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self._polling_task: asyncio.Task | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.telegram_bot_token)

    async def start(self) -> None:
        if not self.enabled:
            log.warning("bot_disabled", reason="TELEGRAM_BOT_TOKEN is empty")
            return
        self.bot = build_bot()
        self.dp = build_dispatcher()
        await self.bot.set_my_commands(_COMMANDS)

        if settings.telegram_use_webhook and settings.public_base_url:
            url = f"{settings.public_base_url.rstrip('/')}/telegram/webhook"
            await self.bot.set_webhook(
                url,
                secret_token=settings.telegram_webhook_secret or None,
                drop_pending_updates=True,
            )
            log.info("bot_webhook_set", url=url)
        else:
            await self.bot.delete_webhook(drop_pending_updates=True)
            self._polling_task = asyncio.create_task(self._poll())
            log.info("bot_polling_started")

    async def _poll(self) -> None:
        assert self.bot and self.dp
        try:
            await self.dp.start_polling(self.bot, handle_signals=False)
        except asyncio.CancelledError:  # pragma: no cover - shutdown
            pass

    async def stop(self) -> None:
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        if self.dp:
            await self.dp.stop_polling()
        if self.bot:
            await self.bot.session.close()


bot_runtime = BotRuntime()
