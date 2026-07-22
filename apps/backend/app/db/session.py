"""Async engine + session factory. SQLite (LOCAL_MVP) or PostgreSQL (FULL)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..core.config import REPO_ROOT, settings


def _normalise_sqlite_url(url: str) -> str:
    """Make the SQLite path absolute and ensure the parent dir exists."""
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        return url
    raw = url[len(prefix) :]
    if raw.startswith(":memory:") or raw == "":
        return url
    path = Path(raw)
    if not path.is_absolute():
        path = REPO_ROOT / raw
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"{prefix}{path}"


def create_engine() -> AsyncEngine:
    url = _normalise_sqlite_url(settings.database_url)
    connect_args: dict = {}
    if settings.is_sqlite:
        connect_args["timeout"] = 30
    return create_async_engine(
        url,
        echo=False,
        pool_pre_ping=not settings.is_sqlite,
        connect_args=connect_args,
    )


engine: AsyncEngine = create_engine()
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session and commits/rolls back."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
