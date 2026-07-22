"""Short-lived confirmation tokens for dangerous bot actions.

Each pending action is stored with an expiry. A stale inline button can no longer
be used — pressing it yields «команда устарела». This backs the callback-TTL
requirement without stuffing state into ``callback_data``.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from ..core.config import settings
from ..core.time import utcnow


@dataclass
class PendingAction:
    action: str  # e.g. "scenario" | "volume"
    user_id: int
    params: dict
    expires_at: float


class ConfirmationStore:
    def __init__(self) -> None:
        self._items: dict[str, PendingAction] = {}

    def create(self, action: str, user_id: int, params: dict) -> str:
        self._gc()
        token = secrets.token_urlsafe(8)
        self._items[token] = PendingAction(
            action=action,
            user_id=user_id,
            params=params,
            expires_at=utcnow().timestamp() + settings.callback_ttl_seconds,
        )
        return token

    def take(self, token: str, user_id: int) -> PendingAction | None:
        """Consume a token. Returns None if missing, expired or wrong user."""
        self._gc()
        item = self._items.pop(token, None)
        if item is None:
            return None
        if item.user_id != user_id:
            return None
        if item.expires_at < utcnow().timestamp():
            return None
        return item

    def _gc(self) -> None:
        now = utcnow().timestamp()
        expired = [t for t, i in self._items.items() if i.expires_at < now]
        for t in expired:
            self._items.pop(t, None)


confirmations = ConfirmationStore()
