"""Emergency stop-file watcher.

If the configured stop-file appears, the agent stops audio immediately — even
with no connection to the backend. The file is then removed so playback can
resume later on an explicit command.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from ..logging import get_logger

log = get_logger("stopfile")


async def watch_stop_file(
    path: Path, on_stop: Callable[[], Awaitable[None]], *, interval: float = 0.5
) -> None:
    # Ignore a stale flag left over from a previous run.
    if path.exists():
        path.unlink(missing_ok=True)
    while True:
        try:
            if path.exists():
                log.warning("stop_file_detected", path=str(path))
                path.unlink(missing_ok=True)
                await on_stop()
            await asyncio.sleep(interval)
        except asyncio.CancelledError:  # pragma: no cover
            raise
        except Exception as exc:
            log.warning("stop_file_watch_error", error=str(exc))
            await asyncio.sleep(interval)
