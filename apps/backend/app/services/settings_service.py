from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import SettingRepository


class SettingsService:
    """Runtime settings stored in DB (overriding env defaults where relevant)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SettingRepository(session)

    async def get(self, key: str, default: str | None = None) -> str | None:
        return await self.repo.get_value(key, default)

    async def get_int(self, key: str, default: int) -> int:
        raw = await self.repo.get_value(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    async def set(self, key: str, value: str, updated_by=None) -> None:
        obj = await self.repo.set_value(key, value)
        obj.updated_by = updated_by

    async def all(self) -> dict[str, str]:
        return await self.repo.all_settings()
