"""In-memory player for tests and audio-less environments."""

from __future__ import annotations

import asyncio

from lw_contracts import PlayerState

from .base import PlayerSnapshot


class MockPlayer:
    def __init__(self, *, duration: float = 180.0, available: bool = True) -> None:
        self._state = PlayerState.IDLE
        self._volume = 60
        self._position = 0.0
        self._duration = duration
        self._track_id: str | None = None
        self._available = available
        self.calls: list[tuple] = []
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self.calls.append(("start",))

    async def is_available(self) -> bool:
        return self._available

    async def play(self, path, *, track_id, volume, fade_in_seconds=0.0) -> None:
        async with self._lock:
            self.calls.append(("play", path, track_id, volume, fade_in_seconds))
            self._state = PlayerState.PLAYING
            self._track_id = track_id
            self._volume = volume
            self._position = 0.0

    async def pause(self) -> None:
        async with self._lock:
            self.calls.append(("pause",))
            if self._state == PlayerState.PLAYING:
                self._state = PlayerState.PAUSED

    async def resume(self) -> None:
        async with self._lock:
            self.calls.append(("resume",))
            if self._state == PlayerState.PAUSED:
                self._state = PlayerState.PLAYING

    async def stop(self, *, fade_out_seconds=0.0) -> None:
        async with self._lock:
            self.calls.append(("stop", fade_out_seconds))
            self._state = PlayerState.STOPPED
            self._track_id = None
            self._position = 0.0

    async def set_volume(self, volume, *, fade_seconds=0.0) -> None:
        async with self._lock:
            self.calls.append(("set_volume", volume, fade_seconds))
            self._volume = volume

    async def snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(
            player_state=self._state,
            volume=self._volume,
            position_seconds=self._position if self._state != PlayerState.IDLE else None,
            duration_seconds=self._duration if self._state != PlayerState.IDLE else None,
            track_id=self._track_id,
        )

    async def close(self) -> None:
        self.calls.append(("close",))
