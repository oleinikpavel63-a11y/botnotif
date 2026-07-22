"""Abstract audio player interface.

Two implementations exist: :class:`~agent.audio.mpv_player.MpvPlayer` (real) and
:class:`~agent.audio.mock_player.MockPlayer` (tests / no-audio environments).
The command handler depends only on this interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from lw_contracts import PlayerState


class AudioError(Exception):
    """Raised on any audio-device / player failure."""


@dataclass
class PlayerSnapshot:
    player_state: PlayerState
    volume: int
    position_seconds: float | None = None
    duration_seconds: float | None = None
    track_id: str | None = None
    last_error: str | None = None


@runtime_checkable
class Player(Protocol):
    async def start(self) -> None:
        """Initialise the backend (launch mpv, etc.)."""

    async def is_available(self) -> bool:
        """Whether the audio backend is usable right now."""

    async def play(
        self,
        path: str,
        *,
        track_id: str,
        volume: int,
        fade_in_seconds: float = 0.0,
    ) -> None: ...

    async def pause(self) -> None: ...

    async def resume(self) -> None: ...

    async def stop(self, *, fade_out_seconds: float = 0.0) -> None: ...

    async def set_volume(self, volume: int, *, fade_seconds: float = 0.0) -> None: ...

    async def snapshot(self) -> PlayerSnapshot: ...

    async def close(self) -> None: ...
