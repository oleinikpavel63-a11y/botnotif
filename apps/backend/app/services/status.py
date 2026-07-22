from __future__ import annotations

from dataclasses import dataclass

from lw_contracts import DeviceState, DeviceStatus, PlayerState
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Device
from ..repositories import ScenarioRepository, SessionRepository, TrackRepository
from ..websocket.hub import hub
from .devices import DeviceService


@dataclass
class NowPlaying:
    device_name: str
    zone: str
    status: DeviceStatus
    online: bool
    player_state: PlayerState
    volume: int
    track_title: str | None = None
    scenario_name: str | None = None
    position_seconds: float | None = None
    duration_seconds: float | None = None
    started_by: str | None = None
    audio_device: str | None = None


class StatusService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.devices = DeviceService(session)
        self.sessions = SessionRepository(session)
        self.tracks = TrackRepository(session)
        self.scenarios = ScenarioRepository(session)

    async def now_playing(self, device: Device) -> NowPlaying:
        state: DeviceState | None = self.devices.live_state(device)
        status = self.devices.status_of(device)
        online = self.devices.is_online(device)

        track_title = None
        scenario_name = None
        started_by = None
        active = await self.sessions.active_for_device(device.id)
        if active is not None:
            if active.track_id:
                track = await self.tracks.get(active.track_id)
                track_title = track.title if track else None
            if active.scenario_id:
                scenario = await self.scenarios.get(active.scenario_id)
                scenario_name = scenario.name if scenario else None
            started_by = active.started_by_name

        player_state = state.player_state if state else PlayerState.IDLE
        # If the live player is idle/stopped, there is nothing playing.
        if player_state in (PlayerState.IDLE, PlayerState.STOPPED):
            track_title = None if not (state and state.track_id) else track_title

        return NowPlaying(
            device_name=device.name,
            zone=device.zone,
            status=status,
            online=online,
            player_state=player_state,
            volume=state.volume if state else device.default_volume,
            track_title=track_title,
            scenario_name=scenario_name,
            position_seconds=state.position_seconds if state else None,
            duration_seconds=state.duration_seconds if state else None,
            started_by=started_by,
            audio_device=(state.audio_device if state else device.audio_device_name),
        )

    async def system_status(self) -> dict:
        devices = await self.devices.list()
        online = [d for d in devices if self.devices.is_online(d)]
        return {
            "devices_total": len(devices),
            "devices_online": len(online),
            "agents_connected": len(hub.online_codes()),
        }
