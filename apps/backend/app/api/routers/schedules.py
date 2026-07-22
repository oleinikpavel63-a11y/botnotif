from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.rbac import Permission
from ...models import User
from ...schemas import OkResponse, ScheduleCreate, ScheduleOut
from ...services.schedule import ScheduleService
from ..deps import CurrentUser, SessionDep, require_permission
from ..serializers import schedule_out

router = APIRouter(tags=["schedules"])


@router.get("/schedules", response_model=list[ScheduleOut])
async def list_schedules(session: SessionDep, _: CurrentUser) -> list[ScheduleOut]:
    return [schedule_out(s) for s in await ScheduleService(session).list_all()]


@router.post("/schedules", response_model=ScheduleOut)
async def create_schedule(
    payload: ScheduleCreate,
    session: SessionDep,
    user: User = Depends(require_permission(Permission.SCHEDULE_MANAGE)),
) -> ScheduleOut:
    sched = await ScheduleService(session).create(
        user,
        name=payload.name,
        scenario_id=payload.scenario_id,
        device_id=payload.device_id,
        recurrence_type=payload.recurrence_type,
        config=payload.config.model_dump(exclude_none=True),
        grace_period_seconds=payload.grace_period_seconds,
        allow_conflict=payload.allow_conflict,
        interface="api",
    )
    return schedule_out(sched)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleOut)
async def toggle_schedule(
    schedule_id: str,
    enabled: bool,
    session: SessionDep,
    user: User = Depends(require_permission(Permission.SCHEDULE_MANAGE)),
) -> ScheduleOut:
    sched = await ScheduleService(session).set_enabled(user, schedule_id, enabled, interface="api")
    return schedule_out(sched)


@router.delete("/schedules/{schedule_id}", response_model=OkResponse)
async def delete_schedule(
    schedule_id: str,
    session: SessionDep,
    user: User = Depends(require_permission(Permission.SCHEDULE_MANAGE)),
) -> OkResponse:
    await ScheduleService(session).delete(user, schedule_id, interface="api")
    return OkResponse(message="Расписание удалено.")
