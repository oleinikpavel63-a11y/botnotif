"""Execute commands from the backend on the local player.

Guarantees:
* expired immediate commands are never executed (EXPIRED),
* each ``command_id`` runs at most once (idempotency, persisted),
* a missing/corrupt file never starts playback (FAILED with a clear reason),
* MAINTENANCE mode blocks playback but never blocks an emergency stop.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from lw_contracts import (
    AgentCommandUpdate,
    CommandEnvelope,
    CommandStatus,
    CommandType,
    DeviceState,
    TrackRef,
)

from ..audio.base import AudioError, Player
from ..cache.store import CacheStore
from ..logging import get_logger

log = get_logger("commands")

UpdateSink = Callable[[AgentCommandUpdate], Awaitable[None]]


class CommandHandler:
    def __init__(
        self,
        *,
        device_id: str,
        player: Player,
        cache: CacheStore,
        downloader,
        send_update: UpdateSink,
        absolute_max_volume: int = 100,
    ) -> None:
        self.device_id = device_id
        self.player = player
        self.cache = cache
        self.downloader = downloader
        self.send_update = send_update
        self.absolute_max_volume = absolute_max_volume
        self.maintenance = False
        self.emergency_latched = False  # blocks auto-resume after an emergency stop

    async def build_state(self, *, error: str | None = None) -> DeviceState:
        snap = await self.player.snapshot()
        return DeviceState(
            device_id=self.device_id,
            online=True,
            player_state=snap.player_state,
            track_id=snap.track_id,
            position_seconds=snap.position_seconds,
            duration_seconds=snap.duration_seconds,
            volume=snap.volume,
            last_error=error or snap.last_error,
        )

    async def _update(
        self, command_id: str, status: CommandStatus, error: str | None = None
    ) -> None:
        state = await self.build_state(error=error)
        await self.send_update(
            AgentCommandUpdate(command_id=command_id, status=status, error=error, state=state)
        )

    def _clamp(self, volume: int) -> int:
        return max(0, min(int(volume), self.absolute_max_volume))

    async def handle(self, cmd: CommandEnvelope) -> None:
        cid = cmd.command_id

        # Idempotency: never run the same command twice (survives reconnect).
        if self.cache.is_processed(cid):
            log.info("command_duplicate_ignored", command_id=cid, type=cmd.type.value)
            return

        await self._update(cid, CommandStatus.RECEIVED)

        # TTL: reject stale immediate commands (no replay after reconnect).
        if cmd.expires_at < datetime.now(UTC):
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.EXPIRED, "Команда устарела.")
            log.info("command_expired", command_id=cid, type=cmd.type.value)
            return

        try:
            await self._dispatch(cmd)
        except AudioError as exc:
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.FAILED, str(exc))
            log.warning("command_failed", command_id=cid, error=str(exc))
        except Exception as exc:
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.FAILED, f"Ошибка: {exc}")
            log.warning("command_error", command_id=cid, error=str(exc))

    async def _dispatch(self, cmd: CommandEnvelope) -> None:
        cid = cmd.command_id
        ctype = cmd.type

        if ctype in (CommandType.EMERGENCY_STOP, CommandType.STOP_IMMEDIATE):
            await self._stop(cid, immediate=True, emergency=ctype == CommandType.EMERGENCY_STOP)
            return

        if self.maintenance and ctype in (CommandType.PLAY_TRACK, CommandType.RESUME):
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.REJECTED, "Устройство в режиме обслуживания.")
            return

        if ctype == CommandType.PLAY_TRACK:
            await self._play(cmd)
        elif ctype == CommandType.PAUSE:
            await self._simple(cid, self.player.pause)
        elif ctype == CommandType.RESUME:
            await self._simple(cid, self.player.resume)
        elif ctype == CommandType.STOP:
            await self._stop(cid, immediate=False, emergency=False)
        elif ctype == CommandType.SET_VOLUME:
            await self._set_volume(cmd)
        elif ctype == CommandType.SYNC_TRACK:
            await self._sync(cmd)
        elif ctype == CommandType.SET_MAINTENANCE:
            self.maintenance = bool(cmd.payload.get("enabled", True))
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.COMPLETED)
        else:  # pragma: no cover - unknown type
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.REJECTED, f"Неизвестная команда: {ctype}")

    async def _play(self, cmd: CommandEnvelope) -> None:
        cid = cmd.command_id
        await self._update(cid, CommandStatus.ACCEPTED)
        ref = TrackRef.model_validate(cmd.payload["track"])
        volume = self._clamp(cmd.payload.get("volume", 60))
        fade_in = float(cmd.payload.get("fade_in_seconds", 0) or 0)

        # Ensure the file is present & verified BEFORE playing.
        try:
            path = await self.cache.ensure(ref, self.downloader)
        except RuntimeError as exc:
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.FAILED, f"sync: {exc}")
            return

        self.emergency_latched = False
        await self.player.play(
            str(path), track_id=ref.track_id, volume=volume, fade_in_seconds=fade_in
        )
        self.cache.mark_processed(cid)
        await self._update(cid, CommandStatus.STARTED)
        log.info("playing", track_id=ref.track_id, volume=volume)

    async def _simple(self, cid: str, action) -> None:
        await self._update(cid, CommandStatus.ACCEPTED)
        await action()
        self.cache.mark_processed(cid)
        await self._update(cid, CommandStatus.COMPLETED)

    async def _stop(self, cid: str, *, immediate: bool, emergency: bool) -> None:
        await self._update(cid, CommandStatus.ACCEPTED)
        fade_out = 0.0 if immediate else 1.5
        await self.player.stop(fade_out_seconds=fade_out)
        if emergency:
            self.emergency_latched = True
        self.cache.mark_processed(cid)
        await self._update(cid, CommandStatus.COMPLETED)

    async def _set_volume(self, cmd: CommandEnvelope) -> None:
        cid = cmd.command_id
        await self._update(cid, CommandStatus.ACCEPTED)
        volume = self._clamp(cmd.payload.get("volume", 60))
        await self.player.set_volume(volume)
        self.cache.mark_processed(cid)
        await self._update(cid, CommandStatus.COMPLETED)

    async def _sync(self, cmd: CommandEnvelope) -> None:
        cid = cmd.command_id
        await self._update(cid, CommandStatus.ACCEPTED)
        ref = TrackRef.model_validate(cmd.payload["track"])
        try:
            await self.cache.ensure(ref, self.downloader)
        except RuntimeError as exc:
            self.cache.mark_processed(cid)
            await self._update(cid, CommandStatus.FAILED, str(exc))
            return
        self.cache.mark_processed(cid)
        await self._update(cid, CommandStatus.COMPLETED)

    async def local_emergency_stop(self) -> None:
        """Stop immediately without a backend command (stop-file / CLI / hotkey)."""
        try:
            await self.player.stop(fade_out_seconds=0.0)
            self.emergency_latched = True
            log.warning("local_emergency_stop")
        except AudioError as exc:  # pragma: no cover
            log.warning("local_emergency_stop_failed", error=str(exc))
