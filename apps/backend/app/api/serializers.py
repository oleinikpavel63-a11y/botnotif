"""Model -> schema converters (kept out of the ORM models)."""

from __future__ import annotations

from ..models import CampScenario, Device, Schedule, Track, User
from ..schemas import DeviceOut, ScenarioOut, ScheduleOut, TrackOut, UserOut
from ..schemas.auth import CurrentUserOut
from ..services.devices import DeviceService
from ..services.scenarios import parse_allowed_roles


def user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role_enum,
        is_active=user.is_active,
        last_seen_at=user.last_seen_at,
    )


def current_user_out(user: User) -> CurrentUserOut:
    return CurrentUserOut(
        id=str(user.id),
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        role=user.role_enum,
        is_active=user.is_active,
    )


def device_out(device: Device, svc: DeviceService) -> DeviceOut:
    return DeviceOut(
        id=str(device.id),
        code=device.code,
        name=device.name,
        zone=device.zone,
        status=svc.status_of(device),
        online=svc.is_online(device),
        last_seen_at=device.last_seen_at,
        audio_device_name=device.audio_device_name,
        default_volume=device.default_volume,
        max_volume=device.max_volume,
        app_version=device.app_version,
        is_active=device.is_active,
        live=svc.live_state(device),
    )


def track_out(track: Track) -> TrackOut:
    return TrackOut(
        id=str(track.id),
        title=track.title,
        category=track.category,
        duration=track.duration,
        size=track.size,
        sha256=track.sha256,
        recommended_volume=track.recommended_volume,
        fade_in_seconds=track.fade_in_seconds,
        fade_out_seconds=track.fade_out_seconds,
        is_announcement=track.is_announcement,
        is_active=track.is_active,
    )


def scenario_out(scenario: CampScenario) -> ScenarioOut:
    from lw_contracts import Priority

    return ScenarioOut(
        id=str(scenario.id),
        code=scenario.code,
        name=scenario.name,
        icon=scenario.icon,
        track_id=str(scenario.track_id) if scenario.track_id else None,
        playlist_id=str(scenario.playlist_id) if scenario.playlist_id else None,
        volume=scenario.volume,
        fade_in_seconds=scenario.fade_in_seconds,
        fade_out_seconds=scenario.fade_out_seconds,
        confirmation_required=scenario.confirmation_required,
        priority=Priority(scenario.priority),
        color=scenario.color,
        allowed_roles=parse_allowed_roles(scenario.allowed_roles),
        is_active=scenario.is_active,
    )


def schedule_out(sched: Schedule) -> ScheduleOut:
    return ScheduleOut(
        id=str(sched.id),
        name=sched.name,
        scenario_id=str(sched.scenario_id),
        device_id=str(sched.device_id),
        recurrence_type=sched.recurrence_type,
        recurrence_config=sched.recurrence_config,
        timezone=sched.timezone,
        next_run_at=sched.next_run_at,
        last_run_at=sched.last_run_at,
        grace_period_seconds=sched.grace_period_seconds,
        priority=sched.priority,
        is_enabled=sched.is_enabled,
    )
