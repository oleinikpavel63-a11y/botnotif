from __future__ import annotations

from sqlalchemy import select

from ..models import CampScenario
from .base import BaseRepository


class ScenarioRepository(BaseRepository[CampScenario]):
    model = CampScenario

    async def get_by_code(self, code: str) -> CampScenario | None:
        result = await self.session.execute(select(CampScenario).where(CampScenario.code == code))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[CampScenario]:
        result = await self.session.execute(
            select(CampScenario).where(CampScenario.is_active).order_by(CampScenario.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[CampScenario]:
        result = await self.session.execute(select(CampScenario).order_by(CampScenario.name))
        return list(result.scalars().all())
