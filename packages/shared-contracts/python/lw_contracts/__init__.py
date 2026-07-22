"""Shared protocol contracts for Living Water Audio Control.

This package is the *single source of truth* for the WebSocket protocol spoken
between the backend and the Player Agent. Both the backend (``apps/backend``) and
the agent (``apps/player-agent``) import from here so message shapes never drift.

A mirror for the Mini App lives in ``../typescript/contracts.ts`` and a
language-neutral description in ``../protocol.json``.
"""

from __future__ import annotations

from .enums import (
    AGENT_MSG,
    FAILURE_STATUSES,
    IMMEDIATE_COMMANDS,
    PRIORITY_ORDER,
    RESOLVING_STATUSES,
    SERVER_MSG,
    CommandStatus,
    CommandType,
    DeviceStatus,
    PlayerState,
    Priority,
    SyncState,
)
from .messages import (
    AgentAuth,
    AgentCommandUpdate,
    AgentHeartbeat,
    AgentPong,
    AgentStatus,
    AgentSyncStatus,
    CommandEnvelope,
    DeviceState,
    IssuedBy,
    ServerAuthError,
    ServerAuthOk,
    ServerCommand,
    ServerPing,
    ServerSync,
    TrackRef,
    parse_agent_message,
    parse_server_message,
)

PROTOCOL_VERSION = "1.0.0"

__all__ = [
    "AGENT_MSG",
    "FAILURE_STATUSES",
    "IMMEDIATE_COMMANDS",
    "PRIORITY_ORDER",
    "PROTOCOL_VERSION",
    "RESOLVING_STATUSES",
    "SERVER_MSG",
    "AgentAuth",
    "AgentCommandUpdate",
    "AgentHeartbeat",
    "AgentPong",
    "AgentStatus",
    "AgentSyncStatus",
    "CommandEnvelope",
    "CommandStatus",
    "CommandType",
    "DeviceState",
    "DeviceStatus",
    "IssuedBy",
    "PlayerState",
    "Priority",
    "ServerAuthError",
    "ServerAuthOk",
    "ServerCommand",
    "ServerPing",
    "ServerSync",
    "SyncState",
    "TrackRef",
    "parse_agent_message",
    "parse_server_message",
]
