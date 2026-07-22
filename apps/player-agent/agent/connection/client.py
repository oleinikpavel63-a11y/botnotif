"""WebSocket client: outbound connection, auth, heartbeat, reconnect.

The agent always dials out (WSS in FULL) so the camp device needs no inbound
ports. On disconnect it reconnects with exponential backoff and re-authenticates;
old immediate commands are never replayed (idempotency + TTL enforced by the
command handler).
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC
from typing import Any

import websockets
from lw_contracts import (
    SERVER_MSG,
    AgentAuth,
    AgentHeartbeat,
    ServerCommand,
    ServerSync,
    parse_server_message,
)
from websockets.exceptions import ConnectionClosed

from ..commands.handler import CommandHandler
from ..config import AgentConfig
from ..logging import get_logger

log = get_logger("connection")

_MAX_BACKOFF = 30.0


class AgentClient:
    def __init__(self, config: AgentConfig, player, cache, downloader) -> None:
        self.config = config
        self.player = player
        self.cache = cache
        self.downloader = downloader
        self._ws: Any = None
        self._send_lock = asyncio.Lock()
        self._stopping = False
        self.handler: CommandHandler | None = None

    async def run(self) -> None:
        backoff = 1.0
        while not self._stopping:
            try:
                await self._session()
                backoff = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("connection_lost", error=str(exc), retry_in=round(backoff, 1))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)

    async def stop(self) -> None:
        self._stopping = True
        if self._ws is not None:
            await self._ws.close()

    # ── One connected session ────────────────────────────────────────────────

    async def _session(self) -> None:
        log.info("connecting", url=self.config.agent_server_url)
        async with websockets.connect(
            self.config.agent_server_url,
            ping_interval=20,
            ping_timeout=20,
            max_size=2**20,
        ) as ws:
            self._ws = ws
            await self._send(
                AgentAuth(
                    device_id=self.config.agent_device_id,
                    token=self.config.agent_device_token,
                    app_version=self.config.agent_app_version,
                    audio_device=self.config.mpv_audio_device or None,
                )
            )
            raw = await ws.recv()
            reply = parse_server_message(json.loads(raw))
            if reply.kind == SERVER_MSG.AUTH_ERROR:
                log.error("auth_rejected", reason=reply.reason)
                self._stopping = True  # bad token — do not spin forever
                raise RuntimeError(f"auth error: {reply.reason}")
            if reply.kind != SERVER_MSG.AUTH_OK:
                raise RuntimeError("unexpected handshake reply")

            log.info("authenticated", device=self.config.agent_device_id, ready=True)
            self.handler = CommandHandler(
                device_id=self.config.agent_device_id,
                player=self.player,
                cache=self.cache,
                downloader=self.downloader,
                send_update=self._send,
                absolute_max_volume=self.config.absolute_max_volume,
            )
            heartbeat = asyncio.create_task(self._heartbeat_loop())
            try:
                async for raw in ws:
                    await self._on_message(raw)
            finally:
                heartbeat.cancel()
                self._ws = None

    async def _on_message(self, raw: str | bytes) -> None:
        try:
            msg = parse_server_message(json.loads(raw))
        except Exception as exc:
            log.warning("bad_server_message", error=str(exc))
            return
        assert self.handler is not None
        if isinstance(msg, ServerCommand):
            await self.handler.handle(msg.command)
        elif isinstance(msg, ServerSync):
            from datetime import datetime, timedelta

            from lw_contracts import CommandEnvelope, IssuedBy

            # Wrap a sync request as an internal SYNC_TRACK command.
            now = datetime.now(UTC)
            env = CommandEnvelope(
                command_id=f"sync-{msg.track.track_id}",
                type="SYNC_TRACK",  # type: ignore[arg-type]
                device_id=self.config.agent_device_id,
                payload={"track": msg.track.model_dump(mode="json")},
                issued_by=IssuedBy(telegram_user_id=0, display_name="system"),
                created_at=now,
                expires_at=now + timedelta(hours=1),
            )
            await self.handler.handle(env)
        elif msg.kind == SERVER_MSG.PING:
            from lw_contracts import AgentPong

            await self._send(AgentPong())

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                state = await self.handler.build_state() if self.handler else None
                if state is not None:
                    await self._send(AgentHeartbeat(state=state))
            except ConnectionClosed:
                return
            except Exception as exc:
                log.warning("heartbeat_failed", error=str(exc))
                return
            await asyncio.sleep(self.config.heartbeat_interval_seconds)

    async def _send(self, message) -> None:
        if self._ws is None:
            return
        data = json.dumps(message.model_dump(mode="json"))
        async with self._send_lock:
            await self._ws.send(data)
