"""Pydantic models for every message on the agent<->server WebSocket."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from .enums import (
    AGENT_MSG,
    SERVER_MSG,
    CommandStatus,
    CommandType,
    PlayerState,
    SyncState,
)


class IssuedBy(BaseModel):
    """Who issued a command (for audit / status display)."""

    telegram_user_id: int
    display_name: str


class TrackRef(BaseModel):
    """Everything the agent needs to fetch & verify a track file."""

    track_id: str
    filename: str
    sha256: str
    size: int
    download_url: str


class CommandEnvelope(BaseModel):
    """A command as delivered to the agent. Mirrors the ``PlaybackCommand`` model."""

    command_id: str
    type: CommandType
    device_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    issued_by: IssuedBy
    created_at: datetime
    expires_at: datetime


class DeviceState(BaseModel):
    """Snapshot of a device/player, sent in heartbeats and status updates."""

    device_id: str
    online: bool = True
    player_state: PlayerState = PlayerState.IDLE
    track_id: str | None = None
    position_seconds: float | None = None
    duration_seconds: float | None = None
    volume: int = 60
    audio_device: str | None = None
    app_version: str | None = None
    last_error: str | None = None


# ── Agent -> Server ──────────────────────────────────────────────────────────


class AgentAuth(BaseModel):
    kind: Literal[AGENT_MSG.AUTH] = AGENT_MSG.AUTH
    device_id: str
    token: str
    app_version: str
    audio_device: str | None = None


class AgentHeartbeat(BaseModel):
    kind: Literal[AGENT_MSG.HEARTBEAT] = AGENT_MSG.HEARTBEAT
    state: DeviceState


class AgentStatus(BaseModel):
    kind: Literal[AGENT_MSG.STATUS] = AGENT_MSG.STATUS
    state: DeviceState


class AgentCommandUpdate(BaseModel):
    kind: Literal[AGENT_MSG.COMMAND_UPDATE] = AGENT_MSG.COMMAND_UPDATE
    command_id: str
    status: CommandStatus
    error: str | None = None
    state: DeviceState | None = None


class AgentSyncStatus(BaseModel):
    kind: Literal[AGENT_MSG.SYNC_STATUS] = AGENT_MSG.SYNC_STATUS
    track_id: str
    state: SyncState
    sha256: str | None = None
    size: int | None = None
    error: str | None = None


class AgentPong(BaseModel):
    kind: Literal[AGENT_MSG.PONG] = AGENT_MSG.PONG


AgentMessage = Annotated[
    AgentAuth | AgentHeartbeat | AgentStatus | AgentCommandUpdate | AgentSyncStatus | AgentPong,
    Field(discriminator="kind"),
]


# ── Server -> Agent ──────────────────────────────────────────────────────────


class ServerAuthOk(BaseModel):
    kind: Literal[SERVER_MSG.AUTH_OK] = SERVER_MSG.AUTH_OK
    device_id: str
    server_time: datetime
    heartbeat_interval_seconds: int = 5


class ServerAuthError(BaseModel):
    kind: Literal[SERVER_MSG.AUTH_ERROR] = SERVER_MSG.AUTH_ERROR
    reason: str


class ServerCommand(BaseModel):
    kind: Literal[SERVER_MSG.COMMAND] = SERVER_MSG.COMMAND
    command: CommandEnvelope


class ServerSync(BaseModel):
    kind: Literal[SERVER_MSG.SYNC] = SERVER_MSG.SYNC
    track: TrackRef


class ServerPing(BaseModel):
    kind: Literal[SERVER_MSG.PING] = SERVER_MSG.PING


ServerMessage = Annotated[
    ServerAuthOk | ServerAuthError | ServerCommand | ServerSync | ServerPing,
    Field(discriminator="kind"),
]


# ── Parsing helpers ──────────────────────────────────────────────────────────

from pydantic import TypeAdapter  # noqa: E402

_agent_adapter: TypeAdapter[AgentMessage] = TypeAdapter(AgentMessage)
_server_adapter: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)


def parse_agent_message(data: dict[str, Any]) -> AgentMessage:
    """Validate a raw dict into a typed Agent->Server message."""
    return _agent_adapter.validate_python(data)


def parse_server_message(data: dict[str, Any]) -> ServerMessage:
    """Validate a raw dict into a typed Server->Agent message."""
    return _server_adapter.validate_python(data)
