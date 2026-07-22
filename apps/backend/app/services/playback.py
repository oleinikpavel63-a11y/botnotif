"""Playback orchestration: turn a user intent into a verified command to the
agent, enforcing RBAC, volume policy, offline checks, TTL and idempotency.

Every mutating entry point re-checks permissions on the backend — the UI hiding
a button is never trusted.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from lw_contracts import (
    FAILURE_STATUSES,
    CommandEnvelope,
    CommandStatus,
    CommandType,
    DeviceState,
    IssuedBy,
    Priority,
    ServerCommand,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import (
    CommandExpired,
    DeviceOffline,
    HighVolumeConfirmationRequired,
    PlaybackFailed,
    TrackNotSynced,
    ValidationError,
)
from ..core.logging import get_logger
from ..core.rbac import Permission, require
from ..core.time import fmt_time, utcnow
from ..models import CampScenario, Device, PlaybackCommand, Track, User
from ..repositories import CommandRepository, SessionRepository, TrackRepository
from ..websocket.hub import hub
from .audit import AuditService
from .devices import DeviceService
from .volume import resolve_volume

log = get_logger("playback")


@dataclass
class CommandResult:
    command_id: str
    status: CommandStatus
    state: DeviceState | None = None
    error: str | None = None
    volume: int | None = None
    track_title: str | None = None


class PlaybackService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.commands = CommandRepository(session)
        self.tracks = TrackRepository(session)
        self.sessions = SessionRepository(session)
        self.devices = DeviceService(session)
        self.audit = AuditService(session)

    # ── Public intents ───────────────────────────────────────────────────────

    async def play_track(
        self,
        actor: User,
        device: Device,
        track: Track,
        *,
        volume: int | None = None,
        fade_in: float | None = None,
        fade_out: float | None = None,
        scenario: CampScenario | None = None,
        priority: Priority = Priority.MANUAL,
        interface: str = "bot",
        high_confirmed: bool = False,
    ) -> CommandResult:
        require(actor.role_enum, Permission.PLAYBACK_CONTROL)

        if not track.is_active:
            raise ValidationError("Трек отключён.")
        if not track.sha256 or not track.storage_path or not Path(track.storage_path).exists():
            raise TrackNotSynced(
                "⚠️ Трек ещё не готов на сервере. Синхронизируйте музыку перед запуском."
            )

        vol = volume if volume is not None else track.recommended_volume
        decision = resolve_volume(
            vol, role=actor.role_enum, device=device, high_confirmed=high_confirmed
        )
        if decision.requires_high_confirmation:
            raise HighVolumeConfirmationRequired(
                f"🔊 Громкость {decision.volume}% выше безопасного порога "
                f"{settings.max_safe_volume}%. Требуется подтверждение."
            )

        payload = {
            "track": {
                "track_id": str(track.id),
                "filename": Path(track.storage_path).name,
                "sha256": track.sha256,
                "size": track.size or 0,
                "download_url": f"/api/agent/download/{track.id}",
            },
            "volume": decision.volume,
            "fade_in_seconds": fade_in if fade_in is not None else track.fade_in_seconds,
            "fade_out_seconds": fade_out if fade_out is not None else track.fade_out_seconds,
            "title": track.title,
            "priority": priority.value,
        }
        result = await self._dispatch(
            actor, device, CommandType.PLAY_TRACK, payload, interface=interface
        )
        result.volume = decision.volume
        result.track_title = track.title
        await self._open_session(
            device, track=track, scenario=scenario, actor=actor, volume=decision.volume
        )
        await self.audit.log(
            action="playback.play",
            user=actor,
            entity_type="device",
            entity_id=str(device.id),
            interface=interface,
            meta={
                "track": track.title,
                "volume": decision.volume,
                "scenario": scenario.code if scenario else None,
                "command_id": result.command_id,
                "at": fmt_time(utcnow()),
            },
        )
        return result

    async def play_scenario(
        self,
        actor: User,
        device: Device,
        scenario: CampScenario,
        *,
        interface: str = "bot",
        high_confirmed: bool = False,
    ) -> CommandResult:
        from .scenarios import ScenarioService

        if not ScenarioService(self.session).can_run(scenario, actor.role_enum):
            require(actor.role_enum, Permission.PLAYBACK_EMERGENCY)  # will raise
        if scenario.track_id is None:
            raise ValidationError(
                f"К сценарию «{scenario.name}» не привязан трек. "
                "Добавьте трек в настройках сценария."
            )
        track = await self.tracks.get_or_404(scenario.track_id)
        return await self.play_track(
            actor,
            device,
            track,
            volume=scenario.volume,
            fade_in=scenario.fade_in_seconds,
            fade_out=scenario.fade_out_seconds,
            scenario=scenario,
            priority=Priority(scenario.priority),
            interface=interface,
            high_confirmed=high_confirmed,
        )

    async def pause(self, actor: User, device: Device, *, interface: str = "bot") -> CommandResult:
        require(actor.role_enum, Permission.PLAYBACK_CONTROL)
        result = await self._dispatch(actor, device, CommandType.PAUSE, {}, interface=interface)
        await self.audit.log(
            action="playback.pause",
            user=actor,
            entity_type="device",
            entity_id=str(device.id),
            interface=interface,
            meta={"command_id": result.command_id},
        )
        return result

    async def resume(self, actor: User, device: Device, *, interface: str = "bot") -> CommandResult:
        require(actor.role_enum, Permission.PLAYBACK_CONTROL)
        result = await self._dispatch(actor, device, CommandType.RESUME, {}, interface=interface)
        await self.audit.log(
            action="playback.resume",
            user=actor,
            entity_type="device",
            entity_id=str(device.id),
            interface=interface,
            meta={"command_id": result.command_id},
        )
        return result

    async def stop(
        self,
        actor: User,
        device: Device,
        *,
        immediate: bool = False,
        emergency: bool = False,
        interface: str = "bot",
    ) -> CommandResult:
        require(actor.role_enum, Permission.PLAYBACK_CONTROL)
        ctype = (
            CommandType.EMERGENCY_STOP
            if emergency
            else CommandType.STOP_IMMEDIATE
            if immediate
            else CommandType.STOP
        )
        result = await self._dispatch(actor, device, ctype, {}, interface=interface)
        await self._close_session(device, reason="emergency" if emergency else "manual")
        await self.audit.log(
            action="playback.stop",
            user=actor,
            entity_type="device",
            entity_id=str(device.id),
            interface=interface,
            meta={"command_id": result.command_id, "immediate": immediate, "emergency": emergency},
        )
        return result

    async def set_volume(
        self,
        actor: User,
        device: Device,
        volume: int,
        *,
        interface: str = "bot",
        high_confirmed: bool = False,
    ) -> CommandResult:
        require(actor.role_enum, Permission.PLAYBACK_VOLUME)
        decision = resolve_volume(
            volume, role=actor.role_enum, device=device, high_confirmed=high_confirmed
        )
        if decision.requires_high_confirmation:
            raise HighVolumeConfirmationRequired(
                f"🔊 Громкость {decision.volume}% выше безопасного порога "
                f"{settings.max_safe_volume}%. Требуется подтверждение."
            )
        result = await self._dispatch(
            actor, device, CommandType.SET_VOLUME, {"volume": decision.volume}, interface=interface
        )
        result.volume = decision.volume
        await self.audit.log(
            action="playback.volume",
            user=actor,
            entity_type="device",
            entity_id=str(device.id),
            interface=interface,
            meta={"volume": decision.volume, "command_id": result.command_id},
        )
        return result

    # ── Dispatch machinery ───────────────────────────────────────────────────

    async def _dispatch(
        self,
        actor: User,
        device: Device,
        ctype: CommandType,
        payload: dict,
        *,
        interface: str,
        wait: bool = True,
    ) -> CommandResult:
        if not self.devices.is_online(device):
            last = hub.last_heartbeat(device.code)
            when = fmt_time(last) if last else "—"
            raise DeviceOffline(
                f"🔴 Рупор сейчас недоступен.\nПоследняя связь: {when}\n"
                f"Устройство: {device.name}\nКоманда не была выполнена."
            )

        now = utcnow()
        ttl = settings.command_ttl_seconds
        issued_by = {
            "telegram_user_id": actor.telegram_user_id,
            "display_name": actor.display_name,
        }
        cmd = PlaybackCommand(
            command_id=uuid.uuid4(),
            device_id=device.id,
            type=ctype.value,
            payload=payload,
            status=CommandStatus.RECEIVED.value,
            issued_by=issued_by,
            expires_at=now + timedelta(seconds=ttl),
        )
        self.session.add(cmd)
        await self.session.flush()
        # Commit so the WebSocket handler (separate session) can update this row.
        await self.session.commit()

        command_id = str(cmd.command_id)
        envelope = CommandEnvelope(
            command_id=command_id,
            type=ctype,
            device_id=device.code,
            payload=payload,
            issued_by=IssuedBy(**issued_by),
            created_at=now,
            expires_at=cmd.expires_at,
        )
        fut = hub.create_pending(command_id)
        sent = await hub.send(device.code, ServerCommand(command=envelope))
        if not sent:
            hub.cancel_pending(command_id)
            cmd.status = CommandStatus.REJECTED.value
            cmd.error_message = "device_offline"
            await self.session.commit()
            raise DeviceOffline(f"🔴 Рупор {device.name} отключился. Команда не была выполнена.")

        if not wait:
            return CommandResult(command_id, CommandStatus.ACCEPTED)

        try:
            update = await asyncio.wait_for(fut, timeout=ttl + 5)
        except TimeoutError:
            hub.cancel_pending(command_id)
            log.warning("command_timeout", command_id=command_id, device=device.code)
            raise DeviceOffline(
                f"⏳ Рупор {device.name} не ответил вовремя. Проверьте устройство."
            ) from None

        if update.status in FAILURE_STATUSES:
            self._raise_for_failure(update.status, update.error or "Команда не выполнена.")
        return CommandResult(command_id, update.status, update.state, update.error)

    @staticmethod
    def _raise_for_failure(status: CommandStatus, error: str) -> None:
        if status == CommandStatus.EXPIRED:
            raise CommandExpired("⏳ Команда устарела. Откройте панель и повторите действие.")
        if "sync" in error.lower() or "not found" in error.lower():
            raise TrackNotSynced("⚠️ Трек ещё не загружен на устройство. Синхронизируйте музыку.")
        raise PlaybackFailed(error)

    # ── Playback session bookkeeping ─────────────────────────────────────────

    async def _open_session(
        self, device: Device, *, track: Track, scenario, actor: User, volume: int
    ) -> None:
        active = await self.sessions.active_for_device(device.id)
        if active is not None:
            active.stopped_at = utcnow()
            active.stop_reason = "superseded"
            active.final_status = "superseded"
        from ..models import PlaybackSession

        self.session.add(
            PlaybackSession(
                device_id=device.id,
                track_id=track.id,
                scenario_id=scenario.id if scenario else None,
                started_by=actor.id,
                started_by_name=actor.display_name,
                started_at=utcnow(),
                initial_volume=volume,
            )
        )

    async def _close_session(self, device: Device, *, reason: str) -> None:
        active = await self.sessions.active_for_device(device.id)
        if active is not None:
            active.stopped_at = utcnow()
            active.stop_reason = reason
            active.final_status = "stopped"
