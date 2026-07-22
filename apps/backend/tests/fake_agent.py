"""A fake Player Agent connected through the hub, for integration tests.

It behaves like a real agent's WebSocket: on receiving a command frame it replies
with a command_update through the *real* server-side handler, which updates the DB
and resolves the pending future the caller is awaiting.
"""

from __future__ import annotations

import asyncio

from app.websocket import agent as ws_agent
from app.websocket.hub import hub
from lw_contracts import AgentCommandUpdate, CommandStatus, DeviceState, PlayerState


class FakeAgent:
    def __init__(
        self,
        code: str,
        *,
        respond: CommandStatus = CommandStatus.STARTED,
        error: str | None = None,
    ) -> None:
        self.code = code
        self.respond = respond
        self.error = error
        self.received: list[dict] = []
        self._volume = 60
        self._player_state = PlayerState.IDLE
        self._track_id: str | None = None

    def connect(self) -> None:
        hub.register(self.code, self)
        hub.update_state(self.code, self._state())

    def _state(self) -> DeviceState:
        return DeviceState(
            device_id=self.code,
            online=True,
            player_state=self._player_state,
            track_id=self._track_id,
            volume=self._volume,
        )

    async def send_json(self, payload: dict) -> None:  # matches WebSocket.send_json
        self.received.append(payload)
        if payload.get("kind") != "command":
            return
        cmd = payload["command"]
        # Reflect the command into our local state for a realistic reply.
        ctype = cmd["type"]
        if ctype == "PLAY_TRACK":
            self._player_state = PlayerState.PLAYING
            self._track_id = cmd["payload"]["track"]["track_id"]
            self._volume = cmd["payload"].get("volume", self._volume)
        elif ctype in ("STOP", "STOP_IMMEDIATE", "EMERGENCY_STOP"):
            self._player_state = PlayerState.STOPPED
            self._track_id = None
        elif ctype == "PAUSE":
            self._player_state = PlayerState.PAUSED
        elif ctype == "RESUME":
            self._player_state = PlayerState.PLAYING
        elif ctype == "SET_VOLUME":
            self._volume = cmd["payload"].get("volume", self._volume)

        update = AgentCommandUpdate(
            command_id=cmd["command_id"],
            status=self.respond,
            error=self.error,
            state=self._state(),
        )
        # Reply asynchronously, like a real socket round-trip.
        asyncio.create_task(ws_agent._handle_command_update(self.code, update))
