from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ...core.errors import ValidationError
from ...core.rbac import Permission
from ...models import User
from ...schemas import OkResponse, TrackOut, TrackUpdate
from ...services.tracks import TrackService
from ..deps import CurrentUser, SessionDep, require_permission
from ..serializers import track_out

router = APIRouter(tags=["tracks"])


@router.get("/tracks", response_model=list[TrackOut])
async def list_tracks(session: SessionDep, _: CurrentUser) -> list[TrackOut]:
    return [track_out(t) for t in await TrackService(session).list_all()]


@router.post("/tracks", response_model=TrackOut)
async def upload_track(
    session: SessionDep,
    user: User = Depends(require_permission(Permission.TRACK_MANAGE)),
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    category: str | None = Form(default=None),
    is_announcement: bool = Form(default=False),
) -> TrackOut:
    data = await file.read()
    if not data:
        raise ValidationError("Пустой файл.")
    svc = TrackService(session)
    track = await svc.create_from_bytes(
        data,
        filename=file.filename or "audio.mp3",
        title=title,
        category=category,
        creator=user,
        is_announcement=is_announcement,
        interface="api",
    )
    return track_out(track)


@router.patch("/tracks/{track_id}", response_model=TrackOut)
async def update_track(
    track_id: str,
    payload: TrackUpdate,
    session: SessionDep,
    _: User = Depends(require_permission(Permission.TRACK_MANAGE)),
) -> TrackOut:
    svc = TrackService(session)
    track = await svc.repo.get_or_404(track_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(track, field, value)
    return track_out(track)


@router.delete("/tracks/{track_id}", response_model=OkResponse)
async def delete_track(
    track_id: str,
    session: SessionDep,
    user: User = Depends(require_permission(Permission.TRACK_MANAGE)),
) -> OkResponse:
    await TrackService(session).delete(user, track_id, interface="api")
    return OkResponse(message="Трек удалён.")
