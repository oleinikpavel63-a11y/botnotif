from __future__ import annotations

import pytest
from agent.cache.store import CacheStore, sha256_of
from helpers import FakeDownloader, sha256_bytes
from lw_contracts import SyncState, TrackRef


def _ref(content: bytes) -> TrackRef:
    return TrackRef(
        track_id="t1",
        filename="song.mp3",
        sha256=sha256_bytes(content),
        size=len(content),
        download_url="/api/agent/download/t1",
    )


async def test_ensure_downloads_and_verifies(tmp_path):
    content = b"audio content here" * 20
    store = CacheStore(tmp_path / "c", tmp_path / "s.json")
    dl = FakeDownloader(content)
    path = await store.ensure(_ref(content), dl)

    assert path.exists()
    assert sha256_of(path) == sha256_bytes(content)
    assert store.sync_state("t1") == SyncState.READY
    assert dl.calls == 1


async def test_ensure_uses_cache_second_time(tmp_path):
    content = b"cached" * 100
    store = CacheStore(tmp_path / "c", tmp_path / "s.json")
    dl = FakeDownloader(content)
    await store.ensure(_ref(content), dl)
    await store.ensure(_ref(content), dl)
    assert dl.calls == 1  # not re-downloaded


async def test_ensure_rejects_corrupt_download(tmp_path):
    good = b"good" * 100
    store = CacheStore(tmp_path / "c", tmp_path / "s.json")
    dl = FakeDownloader(b"corrupt bytes")  # wrong content
    with pytest.raises(RuntimeError):
        await store.ensure(_ref(good), dl)
    assert store.sync_state("t1") == SyncState.ERROR


async def test_processed_persists_across_instances(tmp_path):
    state = tmp_path / "s.json"
    store = CacheStore(tmp_path / "c", state)
    store.mark_processed("cmd-42")
    assert store.is_processed("cmd-42")

    reopened = CacheStore(tmp_path / "c", state)
    assert reopened.is_processed("cmd-42")  # survived "restart"
