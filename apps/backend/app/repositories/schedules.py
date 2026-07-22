from __future__ import annotations

from sqlalchemy import select

from ..models import Schedule
from .base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule]):
    model = Schedule

    async def list_enabled(self) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule).where(Schedule.is_enabled).order_by(Schedule.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Schedule]:
        result = await self.session.execute(select(Schedule).order_by(Schedule.name))
        return list(result.scalars().all())
