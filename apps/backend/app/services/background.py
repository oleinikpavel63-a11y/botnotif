"""Periodic backend jobs: fire due schedules and mark stale devices offline."""

from __future__ import annotations

from lw_contracts import DeviceStatus, Priority
from sqlalchemy import select

from ..core.logging import get_logger
from ..core.rbac import Role
from ..db.session import SessionLocal
from ..models import Device, User
from ..repositories import DeviceRepository, ScenarioRepository
from ..websocket.hub import hub
from .playback import PlaybackService
from .schedule import ScheduleService

log = get_logger("background")


async def _system_actor(session) -> User | None:
    """An OWNER acts as initiator for scheduled events (full permissions)."""
    result = await session.execute(
        select(User).where(User.role == Role.OWNER.value, User.is_active).limit(1)
    )
    return result.scalar_one_or_none()


async def schedule_tick() -> None:
    """Fire any schedules due within their grace period."""
    async with SessionLocal() as session:
        svc = ScheduleService(session)
        due = await svc.due_schedules()
        if not due:
            await session.commit()
            return
        actor = await _system_actor(session)
        devices = DeviceRepository(session)
        scenarios = ScenarioRepository(session)
        playback = PlaybackService(session)
        for sched in due:
            svc.advance(sched)
            if actor is None:
                log.warning("schedule_no_owner", schedule=sched.name)
                continue
            device = await devices.get(sched.device_id)
            scenario = await scenarios.get(sched.scenario_id)
            if device is None or scenario is None:
                continue
            try:
                await playback.play_scenario(
                    actor, device, scenario, interface="schedule", high_confirmed=True
                )
                log.info("schedule_fired", schedule=sched.name, scenario=scenario.code)
            except Exception as exc:
                log.warning("schedule_fire_failed", schedule=sched.name, error=str(exc))
        await session.commit()


async def device_watchdog() -> None:
    """Mark devices OFFLINE when their connection dropped or heartbeat went stale."""
    async with SessionLocal() as session:
        repo = DeviceRepository(session)
        devices = await repo.list_all()
        for device in devices:
            if device.status == DeviceStatus.MAINTENANCE.value:
                continue
            online = hub.is_online(device.code)
            if not online and device.status != DeviceStatus.OFFLINE.value:
                device.status = DeviceStatus.OFFLINE.value
                log.info("device_offline", device=device.code)
        await session.commit()


# Re-exported for clarity in scheduler wiring.
__all__ = ["Device", "Priority", "device_watchdog", "schedule_tick"]
