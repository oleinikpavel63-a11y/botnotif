from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

from lw_contracts import AgentCommandUpdate, CommandEnvelope, CommandType, IssuedBy


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeDownloader:
    """Writes ``content`` to the destination (or fails), simulating a backend fetch."""

    def __init__(self, content: bytes | None = None, *, fail: bool = False) -> None:
        self.content = content
        self.fail = fail
        self.calls = 0

    async def fetch(self, download_url: str, dest: Path) -> None:
        self.calls += 1
        if self.fail:
            raise RuntimeError("network down")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.content or b"")


class UpdateSink:
    def __init__(self) -> None:
        self.updates: list[AgentCommandUpdate] = []

    async def __call__(self, update: AgentCommandUpdate) -> None:
        self.updates.append(update)

    @property
    def statuses(self) -> list[str]:
        return [u.status.value for u in self.updates]


def make_command(
    ctype: CommandType,
    *,
    command_id: str = "cmd-1",
    payload: dict | None = None,
    ttl_seconds: int = 20,
) -> CommandEnvelope:
    now = datetime.now(UTC)
    return CommandEnvelope(
        command_id=command_id,
        type=ctype,
        device_id="main-camp-speakers",
        payload=payload or {},
        issued_by=IssuedBy(telegram_user_id=1, display_name="Павел"),
        created_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
    )


def play_payload(content: bytes, *, volume: int = 65) -> dict:
    return {
        "track": {
            "track_id": "track-1",
            "filename": "sbor.mp3",
            "sha256": sha256_bytes(content),
            "size": len(content),
            "download_url": "/api/agent/download/track-1",
        },
        "volume": volume,
        "fade_in_seconds": 0,
    }
