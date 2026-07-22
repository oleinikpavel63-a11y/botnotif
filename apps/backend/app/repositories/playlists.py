from __future__ import annotations

import uuid

from sqlalchemy import select

from ..models import Playlist, PlaylistTrack
from .base import BaseRepository


class PlaylistRepository(BaseRepository[Playlist]):
    model = Playlist

    async def list_active(self) -> list[Playlist]:
        result = await self.session.execute(
            select(Playlist).where(Playlist.is_active).order_by(Playlist.name)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Playlist]:
        result = await self.session.execute(select(Playlist).order_by(Playlist.name))
        return list(result.scalars().all())

    async def tracks_for(self, playlist_id: uuid.UUID) -> list[PlaylistTrack]:
        result = await self.session.execute(
            select(PlaylistTrack)
            .where(PlaylistTrack.playlist_id == playlist_id)
            .order_by(PlaylistTrack.position)
        )
        return list(result.scalars().all())
