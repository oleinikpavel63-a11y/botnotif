from __future__ import annotations

from sqlalchemy import select

from ..models import AuditLog
from .base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def recent(self, limit: int = 50) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
