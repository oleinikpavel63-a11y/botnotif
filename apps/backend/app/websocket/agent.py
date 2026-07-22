"""WebSocket endpoint for Player Agents (`/ws/agent`).

The agent dials out and authenticates with its device token. The server never
initiates the connection, so the camp device needs no inbound ports.
"""

from __future__ import annotations

from fastapi import WebSocket, WebSocketDisconnect
from lw_contracts import (
    RESOLVING_STATUSES,
    AgentAuth,
    AgentCommandUpdate,
    AgentHeartbeat,
    AgentStatus,
    AgentSyncStatus,
    CommandStatus,
    ServerAuthError,
    ServerAuthOk,
    parse_agent_message,
)
from pydantic import ValidationError as PydanticValidationError

from ..core.config import settings
from ..core.logging import get_logger
from ..core.security import verify_token
from ..core.time import utcnow
from ..db.session import SessionLocal
from ..services.devices import DeviceService
from .hub import hub

log = get_logger("ws.agent")


async def _authenticate(device_id: str, token: str):
    """Return the Device row if the token matches, else None."""
    async with SessionLocal() as session:
        svc = DeviceService(session)
        device = await svc.get_by_code(device_id)
        if device is None or not device.is_active:
            return None
        if not verify_token(token, device.token_hash):
            return None
        return device.code


async def agent_ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    code: str | None = None
    try:
        # ── Handshake ────────────────────────────────────────────────────────
        first = await websocket.receive_json()
        msg = parse_agent_message(first)
        if not isinstance(msg, AgentAuth):
            await websocket.send_json(
                ServerAuthError(reason="expected auth").model_dump(mode="json")
            )
            await websocket.close()
            return

        verified = await _authenticate(msg.device_id, msg.token)
        if verified is None:
            log.warning("agent_auth_failed", device=msg.device_id)
            await websocket.send_json(
                ServerAuthError(reason="invalid device token").model_dump(mode="json")
            )
            await websocket.close()
            return

        code = verified
        hub.register(code, websocket)
        async with SessionLocal() as session:
            svc = DeviceService(session)
            device = await svc.get_by_code(code)
            if device is not None:
                await svc.mark_online(
                    device, app_version=msg.app_version, audio_device=msg.audio_device
                )
            await session.commit()

        await websocket.send_json(
            ServerAuthOk(
                device_id=code,
                server_time=utcnow(),
                heartbeat_interval_seconds=settings.heartbeat_interval_seconds,
            ).model_dump(mode="json")
        )
        log.info("agent_ready", device=code)

        # ── Message loop ─────────────────────────────────────────────────────
        while True:
            raw = await websocket.receive_json()
            try:
                message = parse_agent_message(raw)
            except PydanticValidationError as exc:
                log.warning("agent_bad_message", device=code, error=str(exc))
                continue
            await _handle_message(code, message)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.warning("agent_ws_error", device=code, error=str(exc))
    finally:
        if code is not None:
            hub.unregister(code, websocket)
            async with SessionLocal() as session:
                await DeviceService(session).mark_offline(code)
                await session.commit()


async def _handle_message(code: str, message) -> None:
    if isinstance(message, (AgentHeartbeat, AgentStatus)):
        hub.update_state(code, message.state)
        async with SessionLocal() as session:
            svc = DeviceService(session)
            device = await svc.get_by_code(code)
            if device is not None:
                await svc.heartbeat(device, message.state)
            await session.commit()
        hub.publish_admin(
            {"type": "device_state", "device": code, "state": message.state.model_dump(mode="json")}
        )

    elif isinstance(message, AgentCommandUpdate):
        await _handle_command_update(code, message)

    elif isinstance(message, AgentSyncStatus):
        hub.publish_admin(
            {
                "type": "sync_status",
                "device": code,
                "track_id": message.track_id,
                "state": message.state.value,
            }
        )


async def _handle_command_update(code: str, update: AgentCommandUpdate) -> None:
    # Persist the command lifecycle (best-effort — the row may not be committed
    # yet if the agent is extremely fast; the in-memory future still resolves).
    async with SessionLocal() as session:
        from ..repositories import CommandRepository

        repo = CommandRepository(session)
        cmd = await repo.get_by_command_id(update.command_id)
        if cmd is not None:
            cmd.status = update.status.value
            if update.error:
                cmd.error_message = update.error
            if update.status in (
                CommandStatus.COMPLETED,
                CommandStatus.FAILED,
                CommandStatus.REJECTED,
                CommandStatus.EXPIRED,
            ):
                cmd.completed_at = utcnow()
        await session.commit()

    if update.state is not None:
        hub.update_state(code, update.state)

    # Resolve the waiting caller (bot/API) as soon as the outcome is known.
    if update.status in RESOLVING_STATUSES:
        hub.resolve_pending(update.command_id, update)

    hub.publish_admin(
        {
            "type": "command_update",
            "device": code,
            "command_id": update.command_id,
            "status": update.status.value,
        }
    )
    log.info(
        "command_update", device=code, command_id=update.command_id, status=update.status.value
    )
