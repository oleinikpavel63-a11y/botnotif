from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger
from ..models import AuditLog, User

log = get_logger("audit")


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        *,
        action: str,
        user: User | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        interface: str | None = None,
        meta: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user.id if user else None,
            actor_name=user.display_name if user else "system",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            interface=interface,
            meta=meta or {},
            ip_address=ip_address,
        )
        self.session.add(entry)
        log.info(
            "audit",
            action=action,
            actor=entry.actor_name,
            entity_type=entity_type,
            entity_id=entry.entity_id,
            interface=interface,
        )
        return entry
