from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...core.rbac import Permission
from ...models import User
from ...repositories import AuditRepository
from ..deps import SessionDep, require_permission

router = APIRouter(tags=["audit"])


class AuditOut(BaseModel):
    id: str
    actor_name: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    interface: str | None
    meta: dict
    created_at: datetime


@router.get("/audit", response_model=list[AuditOut])
async def list_audit(
    session: SessionDep,
    _: User = Depends(require_permission(Permission.AUDIT_VIEW)),
    limit: int = 50,
) -> list[AuditOut]:
    entries = await AuditRepository(session).recent(limit=min(limit, 200))
    return [
        AuditOut(
            id=str(e.id),
            actor_name=e.actor_name,
            action=e.action,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            interface=e.interface,
            meta=e.meta,
            created_at=e.created_at,
        )
        for e in entries
    ]
