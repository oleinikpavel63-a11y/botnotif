from __future__ import annotations

from sqlalchemy import select

from ..models import Device
from .base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    model = Device

    async def get_by_code(self, code: str) -> Device | None:
        result = await self.session.execute(select(Device).where(Device.code == code))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Device]:
        result = await self.session.execute(
            select(Device).where(Device.is_active).order_by(Device.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Device]:
        result = await self.session.execute(select(Device).order_by(Device.name))
        return list(result.scalars().all())
