"""Command handler: TTL, idempotency, no-replay after reconnect, sync failures."""

from __future__ import annotations

from helpers import FakeDownloader, make_command, play_payload
from lw_contracts import CommandStatus, CommandType, PlayerState


async def test_play_downloads_verifies_and_plays(make_handler, player, sink):
    content = b"real audio bytes" * 100
    handler = make_handler(FakeDownloader(content))
    await handler.handle(make_command(CommandType.PLAY_TRACK, payload=play_payload(content)))

    assert "STARTED" in sink.statuses
    assert any(c[0] == "play" for c in player.calls)
    snap = await player.snapshot()
    assert snap.player_state == PlayerState.PLAYING
    assert snap.volume == 65


async def test_expired_command_not_executed(make_handler, player, sink):
    content = b"audio" * 100
    handler = make_handler(FakeDownloader(content))
    cmd = make_command(CommandType.PLAY_TRACK, payload=play_payload(content), ttl_seconds=-5)
    await handler.handle(cmd)

    assert sink.statuses[-1] == "EXPIRED"
    assert not any(c[0] == "play" for c in player.calls)


async def test_idempotent_same_command_runs_once(make_handler, player, sink):
    content = b"audio" * 100
    handler = make_handler(FakeDownloader(content))
    cmd = make_command(CommandType.PLAY_TRACK, payload=play_payload(content), command_id="dup-1")

    await handler.handle(cmd)
    plays_before = sum(1 for c in player.calls if c[0] == "play")
    # Deliver the exact same command again (e.g. duplicate delivery).
    await handler.handle(cmd)
    plays_after = sum(1 for c in player.calls if c[0] == "play")

    assert plays_before == 1
    assert plays_after == 1  # not replayed


async def test_no_replay_after_reconnect(make_handler, player, cache, sink):
    """A new handler (simulating reconnect) sharing the cache must not re-run."""
    content = b"audio" * 100
    cmd = make_command(CommandType.PLAY_TRACK, payload=play_payload(content), command_id="keep-1")
    handler1 = make_handler(FakeDownloader(content))
    await handler1.handle(cmd)
    assert sum(1 for c in player.calls if c[0] == "play") == 1

    # Reconnect: fresh handler, SAME persisted cache/state.
    from agent.commands.handler import CommandHandler

    handler2 = CommandHandler(
        device_id="main-camp-speakers",
        player=player,
        cache=cache,  # same state file -> command_id already processed
        downloader=FakeDownloader(content),
        send_update=sink,
    )
    await handler2.handle(cmd)
    assert sum(1 for c in player.calls if c[0] == "play") == 1  # still once


async def test_missing_file_fails_without_playing(make_handler, player, sink):
    content = b"audio" * 100
    handler = make_handler(FakeDownloader(fail=True))  # download fails
    await handler.handle(make_command(CommandType.PLAY_TRACK, payload=play_payload(content)))

    assert sink.statuses[-1] == "FAILED"
    assert any("sync" in (u.error or "") for u in sink.updates)
    assert not any(c[0] == "play" for c in player.calls)


async def test_sha256_mismatch_rejected(make_handler, player, sink):
    good = b"the correct file" * 100
    wrong = b"a different file" * 100
    # Payload declares the sha of `good`, but the downloader serves `wrong`.
    handler = make_handler(FakeDownloader(wrong))
    await handler.handle(make_command(CommandType.PLAY_TRACK, payload=play_payload(good)))

    assert sink.statuses[-1] == "FAILED"
    assert not any(c[0] == "play" for c in player.calls)


async def test_stop_and_volume(make_handler, player, sink):
    handler = make_handler(FakeDownloader(b"x"))
    await handler.handle(
        make_command(CommandType.SET_VOLUME, command_id="v1", payload={"volume": 40})
    )
    assert (await player.snapshot()).volume == 40

    await handler.handle(make_command(CommandType.STOP, command_id="s1"))
    assert (await player.snapshot()).player_state == PlayerState.STOPPED


async def test_maintenance_blocks_play(make_handler, player, sink):
    content = b"audio" * 100
    handler = make_handler(FakeDownloader(content))
    await handler.handle(
        make_command(CommandType.SET_MAINTENANCE, command_id="m1", payload={"enabled": True})
    )
    await handler.handle(
        make_command(CommandType.PLAY_TRACK, command_id="p1", payload=play_payload(content))
    )
    assert sink.updates[-1].status == CommandStatus.REJECTED
    assert not any(c[0] == "play" for c in player.calls)


async def test_emergency_stop_works_in_maintenance(make_handler, player, sink):
    handler = make_handler(FakeDownloader(b"x"))
    await handler.handle(
        make_command(CommandType.SET_MAINTENANCE, command_id="m2", payload={"enabled": True})
    )
    await handler.handle(make_command(CommandType.EMERGENCY_STOP, command_id="e1"))
    assert (await player.snapshot()).player_state == PlayerState.STOPPED
    assert handler.emergency_latched is True
