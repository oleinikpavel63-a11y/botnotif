"""Real audio player: drives mpv over JSON IPC.

Fades run as non-blocking asyncio tasks that step the volume — they never block
the event loop. If mpv or the audio device is unavailable, methods raise
:class:`AudioError` with a clear message rather than failing silently.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import sys

from lw_contracts import PlayerState

from ..logging import get_logger
from .base import AudioError, PlayerSnapshot
from .ipc import IpcTransport, make_transport

log = get_logger("mpv")

_FADE_STEP_SECONDS = 0.1


class MpvPlayer:
    def __init__(
        self,
        *,
        mpv_binary: str,
        ipc_socket: str,
        audio_device: str = "",
        default_volume: int = 60,
    ) -> None:
        self._binary = mpv_binary
        self._socket = ipc_socket
        self._audio_device = audio_device
        self._proc: asyncio.subprocess.Process | None = None
        self._transport: IpcTransport | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._reqid = 0
        self._state = PlayerState.IDLE
        self._volume = default_volume
        self._track_id: str | None = None
        self._fade_task: asyncio.Task | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        if shutil.which(self._binary) is None and not os.path.exists(self._binary):
            raise AudioError(
                f"mpv не найден ({self._binary}). Установите mpv и укажите MPV_EXECUTABLE_PATH."
            )
        self._cleanup_socket()
        args = [
            self._binary,
            "--idle=yes",
            "--no-video",
            "--no-terminal",
            "--force-window=no",
            f"--input-ipc-server={self._socket}",
            f"--volume={self._volume}",
        ]
        if self._audio_device:
            args.append(f"--audio-device={self._audio_device}")
        log.info("mpv_launch", socket=self._socket, device=self._audio_device or "default")
        self._proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await self._connect_with_retry()
        self._reader_task = asyncio.create_task(self._read_loop())

    async def _connect_with_retry(self, attempts: int = 30) -> None:
        last: Exception | None = None
        for _ in range(attempts):
            if self._proc is not None and self._proc.returncode is not None:
                raise AudioError("mpv завершился при запуске.")
            try:
                self._transport = make_transport(self._socket)
                await self._transport.connect()
                return
            except (FileNotFoundError, ConnectionRefusedError, OSError) as exc:
                last = exc
                await asyncio.sleep(0.2)
        raise AudioError(f"Не удалось подключиться к mpv IPC: {last}")

    def _cleanup_socket(self) -> None:
        if sys.platform != "win32" and os.path.exists(self._socket):
            with contextlib.suppress(OSError):
                os.unlink(self._socket)

    async def is_available(self) -> bool:
        if self._proc is None or self._proc.returncode is not None:
            return False
        try:
            await self._get_property("idle-active")
            return True
        except AudioError:
            return False

    # ── IPC plumbing ─────────────────────────────────────────────────────────

    async def _read_loop(self) -> None:
        assert self._transport is not None
        try:
            while True:
                line = await self._transport.read_line()
                if line is None:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                rid = msg.get("request_id")
                if rid is not None and rid in self._pending:
                    fut = self._pending.pop(rid)
                    if not fut.done():
                        fut.set_result(msg)
        except asyncio.CancelledError:  # pragma: no cover
            pass
        except Exception as exc:  # pragma: no cover - transport died
            log.warning("mpv_read_loop_ended", error=str(exc))

    async def _command(self, command: list) -> object:
        if self._transport is None:
            raise AudioError("mpv IPC не подключён.")
        self._reqid += 1
        rid = self._reqid
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[rid] = fut
        payload = json.dumps({"command": command, "request_id": rid}).encode() + b"\n"
        try:
            await self._transport.send_line(payload)
            msg = await asyncio.wait_for(fut, timeout=5)
        except (TimeoutError, OSError) as exc:
            self._pending.pop(rid, None)
            raise AudioError(f"mpv не ответил: {exc}") from exc
        if msg.get("error") not in (None, "success"):
            raise AudioError(f"mpv error: {msg.get('error')}")
        return msg.get("data")

    async def _set_property(self, name: str, value) -> None:
        await self._command(["set_property", name, value])

    async def _get_property(self, name: str) -> object:
        return await self._command(["get_property", name])

    # ── Playback controls ────────────────────────────────────────────────────

    async def play(self, path, *, track_id, volume, fade_in_seconds=0.0) -> None:
        async with self._lock:
            await self._cancel_fade()
            self._track_id = track_id
            start_vol = 0 if fade_in_seconds > 0 else volume
            await self._set_property("volume", start_vol)
            await self._command(["loadfile", path, "replace"])
            await self._set_property("pause", False)
            self._state = PlayerState.PLAYING
            self._last_error = None
            if fade_in_seconds > 0:
                self._start_fade(start_vol, volume, fade_in_seconds)
            else:
                self._volume = volume

    async def pause(self) -> None:
        async with self._lock:
            await self._set_property("pause", True)
            if self._state == PlayerState.PLAYING:
                self._state = PlayerState.PAUSED

    async def resume(self) -> None:
        async with self._lock:
            await self._set_property("pause", False)
            if self._state == PlayerState.PAUSED:
                self._state = PlayerState.PLAYING

    async def stop(self, *, fade_out_seconds=0.0) -> None:
        async with self._lock:
            await self._cancel_fade()
            if fade_out_seconds > 0 and self._state == PlayerState.PLAYING:
                await self._fade(self._volume, 0, fade_out_seconds)
            await self._command(["stop"])
            self._state = PlayerState.STOPPED
            self._track_id = None

    async def set_volume(self, volume, *, fade_seconds=0.0) -> None:
        async with self._lock:
            await self._cancel_fade()
            if fade_seconds > 0:
                self._start_fade(self._volume, volume, fade_seconds)
            else:
                await self._set_property("volume", volume)
                self._volume = volume

    # ── Fades (non-blocking) ─────────────────────────────────────────────────

    def _start_fade(self, start: int, end: int, seconds: float) -> None:
        self._fade_task = asyncio.create_task(self._fade(start, end, seconds))

    async def _fade(self, start: int, end: int, seconds: float) -> None:
        steps = max(1, int(seconds / _FADE_STEP_SECONDS))
        try:
            for i in range(1, steps + 1):
                vol = round(start + (end - start) * i / steps)
                await self._set_property("volume", vol)
                self._volume = vol
                await asyncio.sleep(_FADE_STEP_SECONDS)
        except asyncio.CancelledError:  # pragma: no cover
            raise
        except AudioError as exc:  # pragma: no cover
            self._last_error = str(exc)

    async def _cancel_fade(self) -> None:
        if self._fade_task and not self._fade_task.done():
            self._fade_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._fade_task
        self._fade_task = None

    # ── Status ───────────────────────────────────────────────────────────────

    async def snapshot(self) -> PlayerSnapshot:
        position: float | None = None
        duration: float | None = None
        try:
            if self._state in (PlayerState.PLAYING, PlayerState.PAUSED):
                raw_pos = await self._get_property("time-pos")
                raw_dur = await self._get_property("duration")
                position = float(raw_pos) if isinstance(raw_pos, (int, float)) else None
                duration = float(raw_dur) if isinstance(raw_dur, (int, float)) else None
        except AudioError:
            position = duration = None
        return PlayerSnapshot(
            player_state=self._state,
            volume=self._volume,
            position_seconds=position,
            duration_seconds=duration,
            track_id=self._track_id,
            last_error=self._last_error,
        )

    async def close(self) -> None:
        await self._cancel_fade()
        if self._reader_task:
            self._reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader_task
        if self._transport is not None:
            await self._transport.close()
        if self._proc is not None and self._proc.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                self._proc.terminate()
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._proc.wait(), timeout=3)
        self._cleanup_socket()
