from __future__ import annotations

import json
from datetime import timedelta

import pytest
from app.core.errors import Conflict
from app.core.rbac import Role
from app.core.time import utcnow
from app.models import CampScenario
from app.services.schedule import ScheduleService


async def _scenario(session, track):
    sc = CampScenario(
        code="wake_up",
        name="Подъём",
        icon="🌅",
        track_id=track.id,
        volume=60,
        allowed_roles=json.dumps([Role.OWNER.value]),
    )
    session.add(sc)
    await session.commit()
    return sc


async def test_create_schedule_and_conflict(session, owner, device, track):
    scenario = await _scenario(session, track)
    svc = ScheduleService(session)
    sched = await svc.create(
        owner,
        name="Подъём 07:30",
        scenario_id=scenario.id,
        device_id=device.id,
        recurrence_type="daily",
        config={"time": "07:30"},
    )
    await session.commit()
    assert sched.next_run_at is not None

    # A near-simultaneous schedule on the same device conflicts.
    with pytest.raises(Conflict):
        await svc.create(
            owner,
            name="Подъём 07:32",
            scenario_id=scenario.id,
            device_id=device.id,
            recurrence_type="daily",
            config={"time": "07:32"},
        )

    # ...unless the admin explicitly allows it.
    ok = await svc.create(
        owner,
        name="Подъём 07:32 (forced)",
        scenario_id=scenario.id,
        device_id=device.id,
        recurrence_type="daily",
        config={"time": "07:32"},
        allow_conflict=True,
    )
    assert ok is not None


async def test_due_schedules_skips_stale(session, owner, device, track):
    scenario = await _scenario(session, track)
    svc = ScheduleService(session)
    sched = await svc.create(
        owner,
        name="Подъём",
        scenario_id=scenario.id,
        device_id=device.id,
        recurrence_type="daily",
        config={"time": "07:30"},
        grace_period_seconds=60,
    )
    await session.commit()

    now = utcnow()
    # Within grace: due.
    sched.next_run_at = now - timedelta(seconds=30)
    await session.commit()
    assert sched in await svc.due_schedules(now)

    # Way past grace: NOT fired (advanced instead).
    sched.next_run_at = now - timedelta(seconds=600)
    await session.commit()
    assert sched not in await svc.due_schedules(now)


async def test_operator_cannot_create_schedule(session, operator, device, track):
    scenario = await _scenario(session, track)
    from app.core.errors import PermissionDenied

    svc = ScheduleService(session)
    with pytest.raises(PermissionDenied):
        await svc.create(
            operator,
            name="x",
            scenario_id=scenario.id,
            device_id=device.id,
            recurrence_type="daily",
            config={"time": "07:30"},
        )
