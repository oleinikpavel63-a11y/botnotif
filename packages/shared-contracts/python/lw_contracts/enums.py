"""Enumerations shared across the whole system."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """String enum that serialises to its value (3.11-compatible)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.value)


class CommandType(StrEnum):
    """Types of commands the backend can issue to a Player Agent."""

    PLAY_TRACK = "PLAY_TRACK"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    STOP = "STOP"  # graceful (with fade-out)
    STOP_IMMEDIATE = "STOP_IMMEDIATE"  # emergency, no fade
    SET_VOLUME = "SET_VOLUME"
    SYNC_TRACK = "SYNC_TRACK"  # pre-download a file
    EMERGENCY_STOP = "EMERGENCY_STOP"
    SET_MAINTENANCE = "SET_MAINTENANCE"


#: Immediate-control commands carry a short TTL and must not run after reconnect.
IMMEDIATE_COMMANDS: frozenset[CommandType] = frozenset(
    {
        CommandType.PLAY_TRACK,
        CommandType.PAUSE,
        CommandType.RESUME,
        CommandType.STOP,
        CommandType.STOP_IMMEDIATE,
        CommandType.SET_VOLUME,
        CommandType.EMERGENCY_STOP,
    }
)


class CommandStatus(StrEnum):
    """Lifecycle of a single command."""

    RECEIVED = "RECEIVED"
    ACCEPTED = "ACCEPTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


#: Statuses that resolve a pending command future (terminal for the caller).
RESOLVING_STATUSES: frozenset[CommandStatus] = frozenset(
    {
        CommandStatus.STARTED,
        CommandStatus.COMPLETED,
        CommandStatus.REJECTED,
        CommandStatus.FAILED,
        CommandStatus.EXPIRED,
    }
)

#: Statuses meaning the command failed.
FAILURE_STATUSES: frozenset[CommandStatus] = frozenset(
    {CommandStatus.REJECTED, CommandStatus.FAILED, CommandStatus.EXPIRED}
)


class PlayerState(StrEnum):
    """State of the audio player on a device."""

    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class DeviceStatus(StrEnum):
    """Coarse device health as tracked by the backend."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    SYNCING = "SYNCING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class SyncState(StrEnum):
    """Local cache state of a track on a device."""

    READY = "READY"
    DOWNLOADING = "DOWNLOADING"
    NOT_SYNCED = "NOT_SYNCED"
    ERROR = "ERROR"


class Priority(StrEnum):
    """Playback priority (higher can interrupt lower)."""

    EMERGENCY = "EMERGENCY"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    SCHEDULED_EVENT = "SCHEDULED_EVENT"
    MANUAL = "MANUAL"
    BACKGROUND = "BACKGROUND"


PRIORITY_ORDER: dict[Priority, int] = {
    Priority.EMERGENCY: 100,
    Priority.ANNOUNCEMENT: 80,
    Priority.SCHEDULED_EVENT: 60,
    Priority.MANUAL: 40,
    Priority.BACKGROUND: 20,
}


class AGENT_MSG(StrEnum):  # noqa: N801 - message-kind namespace
    """``kind`` values for messages Agent -> Server."""

    AUTH = "auth"
    HEARTBEAT = "heartbeat"
    STATUS = "status"
    COMMAND_UPDATE = "command_update"
    SYNC_STATUS = "sync_status"
    PONG = "pong"


class SERVER_MSG(StrEnum):  # noqa: N801 - message-kind namespace
    """``kind`` values for messages Server -> Agent."""

    AUTH_OK = "auth_ok"
    AUTH_ERROR = "auth_error"
    COMMAND = "command"
    SYNC = "sync"
    PING = "ping"
