from __future__ import annotations

from sqlalchemy import select

from ..models import Setting
from .base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    model = Setting

    async def get_value(self, key: str, default: str | None = None) -> str | None:
        obj = await self.session.get(Setting, key)
        return obj.value if obj else default

    async def set_value(self, key: str, value: str) -> Setting:
        obj = await self.session.get(Setting, key)
        if obj is None:
            obj = Setting(key=key, value=value)
            self.session.add(obj)
        else:
            obj.value = value
        return obj

    async def all_settings(self) -> dict[str, str]:
        result = await self.session.execute(select(Setting))
        return {s.key: s.value for s in result.scalars().all()}
