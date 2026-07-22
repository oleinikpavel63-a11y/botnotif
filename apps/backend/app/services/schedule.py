"""Scheduling: recurrence maths (timezone-aware), conflict detection and the
tick that fires due events. Missed events are NOT run long after the fact —
only within a configurable grace period."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.errors import Conflict, NotFound, ValidationError
from ..core.logging import get_logger
from ..core.rbac import Permission, require
from ..core.time import ensure_aware, utcnow
from ..models import Schedule, User
from ..repositories import (
    DeviceRepository,
    ScenarioRepository,
    ScheduleRepository,
    TrackRepository,
)
from .audit import AuditService

log = get_logger("schedule")

WEEKDAYS = [0, 1, 2, 3, 4, 5, 6]  # Mon..Sun


def _parse_hhmm(value: str) -> time:
    try:
        hh, mm = value.split(":")
        return time(int(hh), int(mm))
    except (ValueError, AttributeError) as exc:
        raise ValidationError(f"Некорректное время: {value!r}. Ожидается HH:MM.") from exc


def next_run_after(
    recurrence_type: str,
    config: dict,
    tz_name: str,
    after: datetime,
) -> datetime | None:
    """Compute the next fire time strictly after ``after`` (aware UTC), or None.

    ``config`` = {"time": "HH:MM", "days": [0..6], "date": "YYYY-MM-DD"} depending
    on ``recurrence_type`` (once | daily | weekly).
    """
    tz = ZoneInfo(tz_name)
    after = ensure_aware(after).astimezone(tz)

    if recurrence_type == "once":
        date_str = config.get("date")
        time_str = config.get("time", "00:00")
        if not date_str:
            return None
        y, m, d = (int(x) for x in date_str.split("-"))
        t = _parse_hhmm(time_str)
        candidate = datetime(y, m, d, t.hour, t.minute, tzinfo=tz)
        return candidate.astimezone(ZoneInfo("UTC")) if candidate > after else None

    t = _parse_hhmm(config.get("time", "00:00"))
    if recurrence_type == "daily":
        days = WEEKDAYS
    elif recurrence_type == "weekly":
        days = config.get("days") or []
        if not days:
            return None
    else:
        return None

    for offset in range(0, 8):
        day = (after + timedelta(days=offset)).date()
        if day.weekday() not in days:
            continue
        candidate = datetime(day.year, day.month, day.day, t.hour, t.minute, tzinfo=tz)
        if candidate > after:
            return candidate.astimezone(ZoneInfo("UTC"))
    return None


@dataclass
class ConflictInfo:
    schedule_id: str
    name: str
    time: str


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ScheduleRepository(session)
        self.devices = DeviceRepository(session)
        self.scenarios = ScenarioRepository(session)
        self.tracks = TrackRepository(session)
        self.audit = AuditService(session)

    async def list_all(self) -> list[Schedule]:
        return await self.repo.list_all()

    async def check_conflicts(
        self, device_id, recurrence_type: str, config: dict, *, exclude_id=None
    ) -> list[ConflictInfo]:
        """Warn about another schedule on the same device at (nearly) the same
        time on an overlapping day. Does not block — the admin decides priority."""
        new_time = _parse_hhmm(config.get("time", "00:00"))
        new_days = set(WEEKDAYS if recurrence_type != "weekly" else (config.get("days") or []))
        conflicts: list[ConflictInfo] = []
        for sched in await self.repo.list_enabled():
            if sched.device_id != device_id or sched.id == exclude_id:
                continue
            cfg = json.loads(sched.recurrence_config or "{}")
            other_time = _parse_hhmm(cfg.get("time", "00:00"))
            other_days = set(
                WEEKDAYS if sched.recurrence_type != "weekly" else (cfg.get("days") or [])
            )
            if not (new_days & other_days):
                continue
            delta = abs(
                (new_time.hour * 60 + new_time.minute) - (other_time.hour * 60 + other_time.minute)
            )
            if delta <= 5:
                conflicts.append(ConflictInfo(str(sched.id), sched.name, f"{other_time:%H:%M}"))
        return conflicts

    async def create(
        self,
        actor: User,
        *,
        name: str,
        scenario_id,
        device_id,
        recurrence_type: str,
        config: dict,
        priority=None,
        grace_period_seconds: int | None = None,
        allow_conflict: bool = False,
        interface: str = "api",
    ) -> Schedule:
        require(actor.role_enum, Permission.SCHEDULE_MANAGE)

        device = await self.devices.get(device_id)
        if device is None:
            raise NotFound("Устройство для расписания не найдено.")
        scenario = await self.scenarios.get(scenario_id)
        if scenario is None or not scenario.is_active:
            raise ValidationError("Сценарий не найден или отключён.")
        if scenario.track_id is None:
            raise ValidationError("К сценарию не привязан трек — расписание невозможно.")
        track = await self.tracks.get(scenario.track_id)
        if track is None or not track.sha256:
            raise ValidationError("Файл сценария не синхронизирован. Синхронизируйте музыку.")

        # Validate time & compute first run.
        _parse_hhmm(config.get("time", "00:00"))
        next_run = next_run_after(recurrence_type, config, settings.app_timezone, utcnow())
        if recurrence_type == "once" and next_run is None:
            raise ValidationError("Время одноразового события уже прошло.")

        if not allow_conflict:
            conflicts = await self.check_conflicts(device_id, recurrence_type, config)
            if conflicts:
                names = ", ".join(f"«{c.name}» ({c.time})" for c in conflicts)
                raise Conflict(
                    f"⚠️ Конфликт расписания на этом устройстве: {names}. "
                    "Подтвердите приоритет или измените время."
                )

        sched = Schedule(
            name=name,
            scenario_id=scenario_id,
            device_id=device_id,
            recurrence_type=recurrence_type,
            recurrence_config=json.dumps(config),
            timezone=settings.app_timezone,
            next_run_at=next_run,
            grace_period_seconds=grace_period_seconds or settings.schedule_grace_period_seconds,
            priority=(priority.value if priority else scenario.priority),
        )
        self.repo.add(sched)
        await self.repo.flush()
        await self.audit.log(
            action="schedule.create",
            user=actor,
            entity_type="schedule",
            entity_id=str(sched.id),
            interface=interface,
            meta={"name": name},
        )
        return sched

    async def set_enabled(
        self, actor: User, schedule_id, enabled: bool, *, interface="api"
    ) -> Schedule:
        require(actor.role_enum, Permission.SCHEDULE_MANAGE)
        sched = await self.repo.get_or_404(schedule_id)
        sched.is_enabled = enabled
        if enabled and sched.next_run_at is None:
            sched.next_run_at = next_run_after(
                sched.recurrence_type,
                json.loads(sched.recurrence_config or "{}"),
                sched.timezone,
                utcnow(),
            )
        await self.audit.log(
            action="schedule.toggle",
            user=actor,
            entity_type="schedule",
            entity_id=str(sched.id),
            interface=interface,
            meta={"enabled": enabled},
        )
        return sched

    async def delete(self, actor: User, schedule_id, *, interface="api") -> None:
        require(actor.role_enum, Permission.SCHEDULE_MANAGE)
        sched = await self.repo.get_or_404(schedule_id)
        await self.repo.delete(sched)
        await self.audit.log(
            action="schedule.delete",
            user=actor,
            entity_type="schedule",
            entity_id=str(schedule_id),
            interface=interface,
            meta={"name": sched.name},
        )

    async def due_schedules(self, now: datetime | None = None) -> list[Schedule]:
        """Enabled schedules whose next_run is within [now - grace, now]."""
        now = now or utcnow()
        due: list[Schedule] = []
        for sched in await self.repo.list_enabled():
            if sched.next_run_at is None:
                continue
            run_at = ensure_aware(sched.next_run_at)
            if run_at > now:
                continue
            # Too late? Skip (do not fire stale events after downtime).
            if (now - run_at).total_seconds() > sched.grace_period_seconds:
                sched.next_run_at = next_run_after(
                    sched.recurrence_type,
                    json.loads(sched.recurrence_config or "{}"),
                    sched.timezone,
                    now,
                )
                log.warning("schedule_missed", schedule=sched.name, was_due=run_at.isoformat())
                continue
            due.append(sched)
        return due

    def advance(self, sched: Schedule, now: datetime | None = None) -> None:
        now = now or utcnow()
        sched.last_run_at = now
        if sched.recurrence_type == "once":
            sched.is_enabled = False
            sched.next_run_at = None
        else:
            sched.next_run_at = next_run_after(
                sched.recurrence_type,
                json.loads(sched.recurrence_config or "{}"),
                sched.timezone,
                now,
            )
