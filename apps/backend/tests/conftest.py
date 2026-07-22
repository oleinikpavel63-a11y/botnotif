"""Shared test fixtures. Uses a throwaway file-backed SQLite DB (so multiple
connections see the same data) and resets schema + hub state per test."""

from __future__ import annotations

import os
import tempfile

# Configure the app BEFORE importing any app module (settings read env at import).
_TMP_DB = os.path.join(tempfile.mkdtemp(prefix="lw-test-"), "test.db")
os.environ.update(
    APP_MODE="LOCAL_MVP",
    DATABASE_URL=f"sqlite+aiosqlite:///{_TMP_DB}",
    TELEGRAM_BOT_TOKEN="123456:TEST-TOKEN",
    SECRET_KEY="test-secret-key-that-is-long-enough-000",
    INITIAL_OWNER_TELEGRAM_ID="100",
    AGENT_DEVICE_TOKEN="device-secret-token",
    MUSIC_CACHE_PATH=tempfile.mkdtemp(prefix="lw-music-"),
    APP_TIMEZONE="Europe/Chisinau",
    MAX_SAFE_VOLUME="80",
    COMMAND_TTL_SECONDS="20",
)

import app.models  # noqa: E402,F401  (register tables)
import pytest_asyncio  # noqa: E402
from app.core.rbac import Role  # noqa: E402
from app.core.security import hash_token  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.models import Device, Track, User  # noqa: E402
from app.services.tracks import sha256_bytes  # noqa: E402
from app.websocket.hub import hub  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # Reset in-memory hub state between tests.
    hub._conns.clear()
    hub._states.clear()
    hub._last_hb.clear()
    hub._pending.clear()
    hub._admin_subs.clear()
    yield


@pytest_asyncio.fixture
async def session():
    async with SessionLocal() as s:
        yield s


async def _make_user(session, tg_id: int, role: Role, name: str) -> User:
    user = User(telegram_user_id=tg_id, role=role.value, first_name=name, is_active=True)
    session.add(user)
    await session.flush()
    return user


@pytest_asyncio.fixture
async def owner(session) -> User:
    u = await _make_user(session, 100, Role.OWNER, "Владелец")
    await session.commit()
    return u


@pytest_asyncio.fixture
async def operator(session) -> User:
    u = await _make_user(session, 200, Role.OPERATOR, "Павел")
    await session.commit()
    return u


@pytest_asyncio.fixture
async def viewer(session) -> User:
    u = await _make_user(session, 300, Role.VIEWER, "Гость")
    await session.commit()
    return u


@pytest_asyncio.fixture
async def device(session) -> Device:
    d = Device(
        code="main-camp-speakers",
        name="Главный ноутбук",
        zone="Весь лагерь",
        token_hash=hash_token("device-secret-token"),
        default_volume=60,
        max_volume=100,
    )
    session.add(d)
    await session.commit()
    return d


@pytest_asyncio.fixture
async def track(session) -> Track:
    """A ready-to-play track backed by a real file with a correct sha256."""
    from app.core.config import settings

    data = b"ID3 fake mp3 payload for tests" * 100
    settings.music_dir.mkdir(parents=True, exist_ok=True)
    sha = sha256_bytes(data)
    path = settings.music_dir / f"{sha[:8]}_test.mp3"
    path.write_bytes(data)
    t = Track(
        title="Сбор лагеря",
        category="scenario",
        original_filename="test.mp3",
        mime_type="audio/mpeg",
        sha256=sha,
        size=len(data),
        storage_path=str(path),
        recommended_volume=65,
        fade_in_seconds=2.0,
        fade_out_seconds=2.0,
    )
    session.add(t)
    await session.commit()
    return t
