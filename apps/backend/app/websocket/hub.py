"""In-memory runtime hub: agent connections, command futures, live device state.

A single process-wide :class:`AgentHub` (``hub``) is shared by the WebSocket
endpoint, the REST API, and the bot. It is intentionally ephemeral — everything
here is rebuilt from agent heartbeats after a restart. Durable facts live in the
database.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from lw_contracts import AgentCommandUpdate, DeviceState
from pydantic import BaseModel

from ..core.config import settings
from ..core.logging import get_logger
from ..core.time import ensure_aware, utcnow

log = get_logger("hub")


class _Connection:
    """Wraps one agent WebSocket with a send-lock (frames must not interleave)."""

    def __init__(self, ws: object) -> None:
        self.ws = ws
        self.lock = asyncio.Lock()


class AgentHub:
    def __init__(self) -> None:
        self._conns: dict[str, _Connection] = {}
        self._states: dict[str, DeviceState] = {}
        self._last_hb: dict[str, datetime] = {}
        self._pending: dict[str, asyncio.Future[AgentCommandUpdate]] = {}
        self._admin_subs: set[asyncio.Queue[dict]] = set()

    # ── Connections ──────────────────────────────────────────────────────────

    def register(self, code: str, ws: object) -> _Connection:
        conn = _Connection(ws)
        self._conns[code] = conn
        self._last_hb[code] = utcnow()
        log.info("agent_connected", device=code)
        return conn

    def unregister(self, code: str, ws: object) -> None:
        conn = self._conns.get(code)
        if conn is not None and conn.ws is ws:
            del self._conns[code]
            self._states.pop(code, None)
            log.info("agent_disconnected", device=code)

    def is_connected(self, code: str) -> bool:
        return code in self._conns

    def is_online(self, code: str) -> bool:
        """Connected *and* heartbeat is fresh."""
        if code not in self._conns:
            return False
        last = self._last_hb.get(code)
        if last is None:
            return True
        age = (utcnow() - ensure_aware(last)).total_seconds()
        return age < settings.device_offline_after_seconds * 2

    def online_codes(self) -> set[str]:
        return {c for c in self._conns if self.is_online(c)}

    async def send(self, code: str, message: BaseModel) -> bool:
        """Send a message to a connected agent. Returns False if not connected."""
        conn = self._conns.get(code)
        if conn is None:
            return False
        payload = message.model_dump(mode="json")
        try:
            async with conn.lock:
                await conn.ws.send_json(payload)  # type: ignore[attr-defined]
            return True
        except Exception as exc:  # pragma: no cover - network edge
            log.warning("agent_send_failed", device=code, error=str(exc))
            self.unregister(code, conn.ws)
            return False

    # ── Live state ───────────────────────────────────────────────────────────

    def touch(self, code: str) -> None:
        self._last_hb[code] = utcnow()

    def update_state(self, code: str, state: DeviceState) -> None:
        self._states[code] = state
        self._last_hb[code] = utcnow()

    def get_state(self, code: str) -> DeviceState | None:
        return self._states.get(code)

    def last_heartbeat(self, code: str) -> datetime | None:
        return self._last_hb.get(code)

    def stale_codes(self) -> list[str]:
        """Connected devices whose heartbeat has gone stale."""
        cutoff = utcnow() - timedelta(seconds=settings.device_offline_after_seconds)
        return [
            code
            for code, last in self._last_hb.items()
            if code in self._conns and ensure_aware(last) < cutoff
        ]

    # ── Pending command futures ──────────────────────────────────────────────

    def create_pending(self, command_id: str) -> asyncio.Future[AgentCommandUpdate]:
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[AgentCommandUpdate] = loop.create_future()
        self._pending[command_id] = fut
        return fut

    def resolve_pending(self, command_id: str, update: AgentCommandUpdate) -> None:
        fut = self._pending.pop(command_id, None)
        if fut is not None and not fut.done():
            fut.set_result(update)

    def cancel_pending(self, command_id: str) -> None:
        self._pending.pop(command_id, None)

    # ── Admin live-update pub/sub (SSE / /ws/admin) ───────────────────────────

    def subscribe_admin(self) -> asyncio.Queue[dict]:
        q: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self._admin_subs.add(q)
        return q

    def unsubscribe_admin(self, q: asyncio.Queue[dict]) -> None:
        self._admin_subs.discard(q)

    def publish_admin(self, event: dict) -> None:
        for q in list(self._admin_subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:  # pragma: no cover - slow consumer
                pass


#: Process-wide singleton.
hub = AgentHub()
