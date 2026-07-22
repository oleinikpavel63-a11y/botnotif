from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.rbac import Permission
from ...models import User
from ...schemas import ScenarioOut, ScenarioUpsert
from ...services.scenarios import ScenarioService
from ..deps import CurrentUser, SessionDep, require_permission
from ..serializers import scenario_out

router = APIRouter(tags=["scenarios"])


@router.get("/scenarios", response_model=list[ScenarioOut])
async def list_scenarios(session: SessionDep, _: CurrentUser) -> list[ScenarioOut]:
    return [scenario_out(s) for s in await ScenarioService(session).list_all()]


@router.post("/scenarios", response_model=ScenarioOut)
async def upsert_scenario(
    payload: ScenarioUpsert,
    session: SessionDep,
    user: User = Depends(require_permission(Permission.SCENARIO_MANAGE)),
) -> ScenarioOut:
    scenario = await ScenarioService(session).upsert(
        user,
        code=payload.code,
        name=payload.name,
        icon=payload.icon,
        volume=payload.volume,
        fade_in_seconds=payload.fade_in_seconds,
        fade_out_seconds=payload.fade_out_seconds,
        confirmation_required=payload.confirmation_required,
        track_id=payload.track_id,
        allowed_roles=payload.allowed_roles,
        color=payload.color,
        interface="api",
    )
    return scenario_out(scenario)


@router.patch("/scenarios/{scenario_id}", response_model=ScenarioOut)
async def patch_scenario(
    scenario_id: str,
    payload: ScenarioUpsert,
    session: SessionDep,
    user: User = Depends(require_permission(Permission.SCENARIO_MANAGE)),
) -> ScenarioOut:
    scenario = await ScenarioService(session).upsert(
        user,
        code=payload.code,
        name=payload.name,
        icon=payload.icon,
        volume=payload.volume,
        fade_in_seconds=payload.fade_in_seconds,
        fade_out_seconds=payload.fade_out_seconds,
        confirmation_required=payload.confirmation_required,
        track_id=payload.track_id,
        allowed_roles=payload.allowed_roles,
        color=payload.color,
        interface="api",
    )
    return scenario_out(scenario)
