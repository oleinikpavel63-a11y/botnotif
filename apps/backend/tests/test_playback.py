"""Integration tests for the playback flow with a fake agent over the hub."""

from __future__ import annotations

import json

import pytest
from app.core.errors import DeviceOffline, HighVolumeConfirmationRequired
from app.core.rbac import Role
from app.models import CampScenario, PlaybackCommand
from app.repositories import AuditRepository, SessionRepository
from app.services.playback import PlaybackService
from fake_agent import FakeAgent
from lw_contracts import CommandStatus
from sqlalchemy import select


async def _scenario(session, track, *, code="general_gathering", volume=65, confirm=True):
    sc = CampScenario(
        code=code,
        name="Общий сбор",
        icon="🏕",
        track_id=track.id,
        volume=volume,
        fade_in_seconds=2.0,
        confirmation_required=confirm,
        allowed_roles=json.dumps([Role.OWNER.value, Role.ADMIN.value, Role.OPERATOR.value]),
    )
    session.add(sc)
    await session.commit()
    return sc


async def test_play_scenario_online_returns_started(session, operator, device, track):
    scenario = await _scenario(session, track)
    agent = FakeAgent(device.code)
    agent.connect()

    playback = PlaybackService(session)
    result = await playback.play_scenario(operator, device, scenario, high_confirmed=True)
    await session.commit()

    assert result.status == CommandStatus.STARTED
    assert result.volume == 65
    assert result.track_title == "Сбор лагеря"

    # A command was recorded and a playback session opened.
    cmd = (await session.execute(select(PlaybackCommand))).scalars().first()
    assert cmd is not None
    assert cmd.type == "PLAY_TRACK"

    active = await SessionRepository(session).active_for_device(device.id)
    assert active is not None
    assert active.started_by_name == "Павел"

    # The action is audited.
    entries = await AuditRepository(session).recent()
    assert any(e.action == "playback.play" for e in entries)

    # The fake agent actually received a PLAY_TRACK frame.
    assert any(f["kind"] == "command" for f in agent.received)


async def test_play_offline_raises_device_offline(session, operator, device, track):
    scenario = await _scenario(session, track)
    # No agent connected -> device offline.
    playback = PlaybackService(session)
    with pytest.raises(DeviceOffline):
        await playback.play_scenario(operator, device, scenario, high_confirmed=True)


async def test_viewer_cannot_play(session, viewer, device, track):
    scenario = await _scenario(session, track)
    FakeAgent(device.code).connect()
    from app.core.errors import PermissionDenied

    playback = PlaybackService(session)
    with pytest.raises(PermissionDenied):
        await playback.play_scenario(viewer, device, scenario, high_confirmed=True)


async def test_stop_closes_session(session, operator, device, track):
    scenario = await _scenario(session, track)
    agent = FakeAgent(device.code)
    agent.connect()
    playback = PlaybackService(session)
    await playback.play_scenario(operator, device, scenario, high_confirmed=True)
    await session.commit()

    await playback.stop(operator, device)
    await session.commit()

    active = await SessionRepository(session).active_for_device(device.id)
    assert active is None  # session was closed


async def test_pause_resume_roundtrip(session, operator, device, track):
    FakeAgent(device.code, respond=CommandStatus.COMPLETED).connect()
    playback = PlaybackService(session)
    pr = await playback.pause(operator, device)
    rr = await playback.resume(operator, device)
    assert pr.status == CommandStatus.COMPLETED
    assert rr.status == CommandStatus.COMPLETED


async def test_admin_high_volume_needs_confirmation(session, owner, device):
    FakeAgent(device.code, respond=CommandStatus.COMPLETED).connect()
    playback = PlaybackService(session)
    with pytest.raises(HighVolumeConfirmationRequired):
        await playback.set_volume(owner, device, 95)
    # With confirmation it goes through.
    result = await playback.set_volume(owner, device, 95, high_confirmed=True)
    assert result.volume == 95


async def test_operator_volume_over_ceiling_rejected(session, operator, device):
    FakeAgent(device.code, respond=CommandStatus.COMPLETED).connect()
    from app.core.errors import VolumeNotAllowed

    playback = PlaybackService(session)
    with pytest.raises(VolumeNotAllowed):
        await playback.set_volume(operator, device, 95)
