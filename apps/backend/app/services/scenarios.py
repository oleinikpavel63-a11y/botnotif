from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import ValidationError
from ..core.rbac import Permission, Role, require
from ..models import CampScenario, User
from ..repositories import ScenarioRepository
from .audit import AuditService


def parse_allowed_roles(raw: str) -> list[Role]:
    try:
        return [Role(r) for r in json.loads(raw)]
    except (json.JSONDecodeError, ValueError):
        return [Role.OWNER, Role.ADMIN, Role.OPERATOR]


class ScenarioService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ScenarioRepository(session)
        self.audit = AuditService(session)

    async def list_active(self) -> list[CampScenario]:
        return await self.repo.list_active()

    async def list_all(self) -> list[CampScenario]:
        return await self.repo.list_all()

    async def get_by_code(self, code: str) -> CampScenario | None:
        return await self.repo.get_by_code(code)

    def can_run(self, scenario: CampScenario, role: Role) -> bool:
        return role in parse_allowed_roles(scenario.allowed_roles)

    async def upsert(
        self,
        actor: User,
        *,
        code: str,
        name: str,
        icon: str = "🎵",
        volume: int = 60,
        fade_in_seconds: float = 0.0,
        fade_out_seconds: float = 0.0,
        confirmation_required: bool = True,
        track_id=None,
        playlist_id=None,
        allowed_roles: list[Role] | None = None,
        color: str | None = None,
        interface: str = "api",
    ) -> CampScenario:
        require(actor.role_enum, Permission.SCENARIO_MANAGE)
        if not code:
            raise ValidationError("Код сценария обязателен.")
        scenario = await self.repo.get_by_code(code)
        roles_json = json.dumps(
            [r.value for r in (allowed_roles or [Role.OWNER, Role.ADMIN, Role.OPERATOR])]
        )
        if scenario is None:
            scenario = CampScenario(code=code)
            self.repo.add(scenario)
        scenario.name = name
        scenario.icon = icon
        scenario.volume = volume
        scenario.fade_in_seconds = fade_in_seconds
        scenario.fade_out_seconds = fade_out_seconds
        scenario.confirmation_required = confirmation_required
        scenario.track_id = track_id
        scenario.playlist_id = playlist_id
        scenario.allowed_roles = roles_json
        scenario.color = color
        await self.repo.flush()
        await self.audit.log(
            action="scenario.upsert",
            user=actor,
            entity_type="scenario",
            entity_id=str(scenario.id),
            interface=interface,
            meta={"code": code},
        )
        return scenario

    async def set_track(
        self, actor: User, scenario_id, track_id, *, interface: str = "api"
    ) -> CampScenario:
        require(actor.role_enum, Permission.SCENARIO_MANAGE)
        scenario = await self.repo.get_or_404(scenario_id)
        scenario.track_id = track_id
        scenario.playlist_id = None
        await self.audit.log(
            action="scenario.set_track",
            user=actor,
            entity_type="scenario",
            entity_id=str(scenario.id),
            interface=interface,
            meta={"track_id": str(track_id)},
        )
        return scenario
