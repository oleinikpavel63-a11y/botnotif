from __future__ import annotations

import uuid

from sqlalchemy import select

from ..models import PlaybackCommand
from .base import BaseRepository


class CommandRepository(BaseRepository[PlaybackCommand]):
    model = PlaybackCommand

    async def get_by_command_id(self, command_id: uuid.UUID | str) -> PlaybackCommand | None:
        if isinstance(command_id, str):
            try:
                command_id = uuid.UUID(command_id)
            except ValueError:
                return None  # non-UUID ids (e.g. internal sync-*) never match a row
        result = await self.session.execute(
            select(PlaybackCommand).where(PlaybackCommand.command_id == command_id)
        )
        return result.scalar_one_or_none()

    async def recent_for_device(
        self, device_id: uuid.UUID, limit: int = 20
    ) -> list[PlaybackCommand]:
        result = await self.session.execute(
            select(PlaybackCommand)
            .where(PlaybackCommand.device_id == device_id)
            .order_by(PlaybackCommand.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
