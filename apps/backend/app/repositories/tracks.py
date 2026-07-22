from __future__ import annotations

from sqlalchemy import select

from ..models import Track
from .base import BaseRepository


class TrackRepository(BaseRepository[Track]):
    model = Track

    async def get_by_sha256(self, sha256: str) -> Track | None:
        result = await self.session.execute(select(Track).where(Track.sha256 == sha256))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Track]:
        result = await self.session.execute(
            select(Track).where(Track.is_active).order_by(Track.title)
        )
        return list(result.scalars().all())

    async def list_by_category(self, category: str) -> list[Track]:
        result = await self.session.execute(
            select(Track).where(Track.is_active, Track.category == category).order_by(Track.title)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Track]:
        result = await self.session.execute(select(Track).order_by(Track.title))
        return list(result.scalars().all())
