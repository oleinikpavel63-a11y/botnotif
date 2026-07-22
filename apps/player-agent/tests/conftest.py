from __future__ import annotations

import pytest
from agent.audio.mock_player import MockPlayer
from agent.cache.store import CacheStore
from agent.commands.handler import CommandHandler
from helpers import UpdateSink


@pytest.fixture
def player() -> MockPlayer:
    return MockPlayer()


@pytest.fixture
def cache(tmp_path) -> CacheStore:
    return CacheStore(tmp_path / "cache", tmp_path / "state.json")


@pytest.fixture
def sink() -> UpdateSink:
    return UpdateSink()


@pytest.fixture
def make_handler(player, cache, sink):
    def _make(downloader) -> CommandHandler:
        return CommandHandler(
            device_id="main-camp-speakers",
            player=player,
            cache=cache,
            downloader=downloader,
            send_update=sink,
        )

    return _make
