from __future__ import annotations

from fastapi import APIRouter

from ...core.errors import NotFound, ValidationError
from ...schemas import CommandResultOut, DeviceOut, PlayRequest, VolumeUpdate
from ...services.devices import DeviceService
from ...services.playback import CommandResult, PlaybackService
from ...services.scenarios import ScenarioService
from ..deps import CurrentUser, SessionDep
from ..serializers import device_out

router = APIRouter(tags=["devices"])


def _result_out(result: CommandResult) -> CommandResultOut:
    return CommandResultOut(
        command_id=result.command_id,
        status=result.status,
        volume=result.volume,
        track_title=result.track_title,
        state=result.state,
    )


async def _get_device(session, device_id: str):
    svc = DeviceService(session)
    device = await svc.repo.get(device_id)
    if device is None:
        raise NotFound("Устройство не найдено.")
    return device, svc


@router.get("/devices", response_model=list[DeviceOut])
async def list_devices(session: SessionDep, _: CurrentUser) -> list[DeviceOut]:
    svc = DeviceService(session)
    return [device_out(d, svc) for d in await svc.list()]


@router.get("/devices/{device_id}", response_model=DeviceOut)
async def get_device(device_id: str, session: SessionDep, _: CurrentUser) -> DeviceOut:
    device, svc = await _get_device(session, device_id)
    return device_out(device, svc)


@router.post("/devices/{device_id}/play", response_model=CommandResultOut)
async def play(
    device_id: str, payload: PlayRequest, session: SessionDep, user: CurrentUser
) -> CommandResultOut:
    device, _ = await _get_device(session, device_id)
    playback = PlaybackService(session)
    if payload.scenario_code:
        scenario = await ScenarioService(session).get_by_code(payload.scenario_code)
        if scenario is None:
            raise NotFound("Сценарий не найден.")
        result = await playback.play_scenario(
            user, device, scenario, interface="api", high_confirmed=payload.confirm_high
        )
    elif payload.track_id:
        track = await playback.tracks.get(payload.track_id)
        if track is None:
            raise NotFound("Трек не найден.")
        result = await playback.play_track(
            user,
            device,
            track,
            volume=payload.volume,
            interface="api",
            high_confirmed=payload.confirm_high,
        )
    else:
        raise ValidationError("Укажите track_id или scenario_code.")
    return _result_out(result)


@router.post("/devices/{device_id}/pause", response_model=CommandResultOut)
async def pause(device_id: str, session: SessionDep, user: CurrentUser) -> CommandResultOut:
    device, _ = await _get_device(session, device_id)
    return _result_out(await PlaybackService(session).pause(user, device, interface="api"))


@router.post("/devices/{device_id}/resume", response_model=CommandResultOut)
async def resume(device_id: str, session: SessionDep, user: CurrentUser) -> CommandResultOut:
    device, _ = await _get_device(session, device_id)
    return _result_out(await PlaybackService(session).resume(user, device, interface="api"))


@router.post("/devices/{device_id}/stop", response_model=CommandResultOut)
async def stop(
    device_id: str,
    session: SessionDep,
    user: CurrentUser,
    immediate: bool = False,
    emergency: bool = False,
) -> CommandResultOut:
    device, _ = await _get_device(session, device_id)
    result = await PlaybackService(session).stop(
        user, device, immediate=immediate, emergency=emergency, interface="api"
    )
    return _result_out(result)


@router.patch("/devices/{device_id}/volume", response_model=CommandResultOut)
async def set_volume(
    device_id: str, payload: VolumeUpdate, session: SessionDep, user: CurrentUser
) -> CommandResultOut:
    device, _ = await _get_device(session, device_id)
    result = await PlaybackService(session).set_volume(
        user, device, payload.volume, interface="api", high_confirmed=payload.confirm_high
    )
    return _result_out(result)
