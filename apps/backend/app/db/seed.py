"""Idempotent seeding: initial OWNER, default device, camp scenarios, settings.

Safe to run repeatedly (on startup and via ``python -m app.cli seed``).
"""

from __future__ import annotations

import json

from lw_contracts import Priority
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.logging import get_logger
from ..core.rbac import Role
from ..core.security import generate_device_token, hash_token
from ..models import CampScenario, Device, Setting, User
from ..repositories import DeviceRepository, ScenarioRepository, UserRepository

log = get_logger("seed")

DEFAULT_SCENARIOS = [
    ("general_gathering", "Общий сбор", "🏕", 65, Priority.ANNOUNCEMENT, True, "#2F6B4F"),
    ("wake_up", "Подъём", "🌅", 60, Priority.SCHEDULED_EVENT, True, "#E9A93B"),
    ("breakfast", "Завтрак", "🍽", 55, Priority.SCHEDULED_EVENT, False, "#E9A93B"),
    ("lunch", "Обед", "🍲", 55, Priority.SCHEDULED_EVENT, False, "#E9A93B"),
    ("dinner", "Ужин", "🌇", 55, Priority.SCHEDULED_EVENT, False, "#E9A93B"),
    ("games", "Начало игр", "⚽", 60, Priority.MANUAL, False, "#3A8A5B"),
    ("creative", "Творческий режим", "🎨", 45, Priority.BACKGROUND, False, "#3A8A5B"),
    ("evening_service", "Вечернее служение", "🙏", 60, Priority.ANNOUNCEMENT, True, "#2F6B4F"),
    ("background", "Фоновая музыка", "🎶", 35, Priority.BACKGROUND, False, "#3A8A5B"),
    ("lights_out", "Отбой", "🌙", 40, Priority.SCHEDULED_EVENT, True, "#1F2A24"),
    ("urgent_announcement", "Срочное объявление", "📣", 75, Priority.EMERGENCY, True, "#C94B45"),
]

DEFAULT_SETTINGS = {
    "default_volume": str(settings.default_volume),
    "max_safe_volume": str(settings.max_safe_volume),
    "absolute_max_volume": str(settings.absolute_max_volume),
}


async def ensure_owner(session: AsyncSession) -> None:
    if not settings.initial_owner_telegram_id:
        return
    repo = UserRepository(session)
    existing = await repo.get_by_telegram_id(settings.initial_owner_telegram_id)
    if existing is None:
        repo.add(
            User(
                telegram_user_id=settings.initial_owner_telegram_id,
                role=Role.OWNER.value,
                first_name="Владелец",
                is_active=True,
            )
        )
        log.info("seed_owner", telegram_id=settings.initial_owner_telegram_id)


async def ensure_default_device(session: AsyncSession) -> str | None:
    repo = DeviceRepository(session)
    existing = await repo.get_by_code(settings.agent_device_id)
    if existing is not None:
        return None
    raw_token = settings.agent_device_token or generate_device_token()
    repo.add(
        Device(
            code=settings.agent_device_id,
            name="Главный ноутбук",
            zone="Весь лагерь",
            token_hash=hash_token(raw_token),
            default_volume=settings.default_volume,
            max_volume=settings.max_safe_volume,
        )
    )
    log.info("seed_device", code=settings.agent_device_id)
    # Return the token only if we generated it (so the operator can configure it).
    return None if settings.agent_device_token else raw_token


async def ensure_scenarios(session: AsyncSession) -> None:
    repo = ScenarioRepository(session)
    for code, name, icon, volume, priority, confirm, color in DEFAULT_SCENARIOS:
        if await repo.get_by_code(code) is not None:
            continue
        repo.add(
            CampScenario(
                code=code,
                name=name,
                icon=icon,
                volume=volume,
                priority=priority.value,
                confirmation_required=confirm,
                fade_in_seconds=2.0,
                fade_out_seconds=2.0,
                color=color,
                allowed_roles=json.dumps([Role.OWNER.value, Role.ADMIN.value, Role.OPERATOR.value]),
            )
        )
    log.info("seed_scenarios")


async def ensure_settings(session: AsyncSession) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        if await session.get(Setting, key) is None:
            session.add(Setting(key=key, value=value))


async def seed_all(session: AsyncSession) -> str | None:
    await ensure_owner(session)
    generated_token = await ensure_default_device(session)
    await ensure_scenarios(session)
    await ensure_settings(session)
    return generated_token
