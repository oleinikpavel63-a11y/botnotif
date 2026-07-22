from __future__ import annotations

import uuid

from sqlalchemy import select

from ..models import PlaybackSession
from .base import BaseRepository


class SessionRepository(BaseRepository[PlaybackSession]):
    model = PlaybackSession

    async def active_for_device(self, device_id: uuid.UUID) -> PlaybackSession | None:
        result = await self.session.execute(
            select(PlaybackSession)
            .where(
                PlaybackSession.device_id == device_id,
                PlaybackSession.stopped_at.is_(None),
            )
            .order_by(PlaybackSession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
