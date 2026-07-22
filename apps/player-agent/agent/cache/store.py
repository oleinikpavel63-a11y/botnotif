"""Local file cache + agent state (JSON).

Holds each track's local copy with its SHA-256, size and sync state, plus the set
of already-processed command ids (idempotency, survives restart/reconnect).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from lw_contracts import SyncState, TrackRef

from ..logging import get_logger

log = get_logger("cache")

_MAX_PROCESSED = 1000


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class CacheStore:
    def __init__(self, cache_dir: Path, state_path: Path) -> None:
        self.cache_dir = cache_dir
        self.state_path = state_path
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, Any] = {"tracks": {}, "processed": []}
        self._processed: set[str] = set()
        self._load()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self.state_path.exists():
            try:
                self._state = json.loads(self.state_path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                self._state = {"tracks": {}, "processed": []}
        self._state.setdefault("tracks", {})
        self._state.setdefault("processed", [])
        self._processed = set(self._state["processed"])

    def _save(self) -> None:
        self._state["processed"] = list(self._processed)[-_MAX_PROCESSED:]
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self.state_path)

    # ── Idempotency ──────────────────────────────────────────────────────────

    def is_processed(self, command_id: str) -> bool:
        return command_id in self._processed

    def mark_processed(self, command_id: str) -> None:
        self._processed.add(command_id)
        self._save()

    # ── Track cache ──────────────────────────────────────────────────────────

    def _path_for(self, ref: TrackRef) -> Path:
        safe = ref.filename.replace("\\", "/").split("/")[-1]
        return self.cache_dir / f"{ref.sha256[:8]}_{safe}"

    def sync_state(self, track_id: str) -> SyncState:
        info = self._state["tracks"].get(track_id)
        if not info:
            return SyncState.NOT_SYNCED
        return SyncState(info.get("state", SyncState.NOT_SYNCED.value))

    def local_path(self, track_id: str) -> Path | None:
        info = self._state["tracks"].get(track_id)
        if info and Path(info["path"]).exists():
            return Path(info["path"])
        return None

    def _record(
        self, ref: TrackRef, path: Path, state: SyncState, error: str | None = None
    ) -> None:
        self._state["tracks"][ref.track_id] = {
            "path": str(path),
            "sha256": ref.sha256,
            "size": ref.size,
            "state": state.value,
            "error": error,
        }
        self._save()

    async def ensure(self, ref: TrackRef, downloader) -> Path:
        """Return a verified local path for ``ref``, downloading if needed.

        Raises on download failure or SHA-256 mismatch — the caller must NOT play
        an unverified file.
        """
        path = self._path_for(ref)
        # Already present and verified?
        if path.exists() and sha256_of(path) == ref.sha256:
            self._record(ref, path, SyncState.READY)
            return path

        self._record(ref, path, SyncState.DOWNLOADING)
        try:
            await downloader.fetch(ref.download_url, path)
        except Exception as exc:
            self._record(ref, path, SyncState.ERROR, error=str(exc))
            raise RuntimeError(f"Не удалось загрузить трек: {exc}") from exc

        actual = sha256_of(path)
        if actual != ref.sha256:
            self._record(ref, path, SyncState.ERROR, error="sha256 mismatch")
            path.unlink(missing_ok=True)
            raise RuntimeError("Контрольная сумма трека не совпала (файл повреждён).")

        self._record(ref, path, SyncState.READY)
        return path
