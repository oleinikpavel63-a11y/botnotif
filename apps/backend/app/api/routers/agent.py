"""Agent-facing HTTP: authenticated download of track files into the local cache.

Authorised with the device token header (the same secret used for the WS auth),
not a user session. The file path is server-controlled, so there is no
path-traversal surface here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Header
from fastapi.responses import FileResponse
from sqlalchemy import select

from ...core.errors import AuthError, NotFound
from ...core.security import verify_token
from ...models import Device, Track
from ..deps import SessionDep

router = APIRouter(tags=["agent"])


async def _authorise_device(session, token: str | None) -> Device:
    if not token:
        raise AuthError("Требуется токен устройства.")
    result = await session.execute(select(Device).where(Device.is_active))
    for device in result.scalars().all():
        if verify_token(token, device.token_hash):
            return device
    raise AuthError("Недействительный токен устройства.")


@router.get("/agent/download/{track_id}")
async def download_track(
    track_id: str,
    session: SessionDep,
    x_device_token: Annotated[str | None, Header()] = None,
) -> FileResponse:
    await _authorise_device(session, x_device_token)
    from ...repositories.base import coerce_uuid

    track = await session.get(Track, coerce_uuid(track_id))
    if track is None or not track.storage_path:
        raise NotFound("Трек не найден.")
    path = Path(track.storage_path)
    if not path.exists():
        raise NotFound("Файл трека отсутствует на сервере.")
    return FileResponse(
        path,
        media_type=track.mime_type or "application/octet-stream",
        filename=path.name,
    )
