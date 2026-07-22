"""Backend management CLI: ``python -m app.cli <command>``.

Commands:
  seed          Seed OWNER, default device, scenarios, settings (idempotent).
  scan-music    Import audio files from storage/music into the library.
  create-device Create a device and print its token (shown once).
  list-devices  List devices and their status.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .core.config import settings
from .core.logging import configure_logging
from .db.base import Base
from .db.seed import seed_all
from .db.session import SessionLocal, engine
from .services.devices import DeviceService
from .services.tracks import TrackService


async def _ensure_schema() -> None:
    if settings.is_sqlite:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def cmd_seed() -> None:
    await _ensure_schema()
    async with SessionLocal() as session:
        token = await seed_all(session)
        await session.commit()
    print("✅ Сидинг выполнен.")
    if token:
        print(f"🔑 Токен устройства (сохраните в AGENT_DEVICE_TOKEN): {token}")


async def cmd_scan_music() -> None:
    await _ensure_schema()
    async with SessionLocal() as session:
        tracks = await TrackService(session).scan_music_folder()
        await session.commit()
    print(f"✅ Импортировано треков: {len(tracks)}")
    for t in tracks:
        print(f"   • {t.title} ({t.sha256[:8] if t.sha256 else '?'})")


async def cmd_create_device(code: str, name: str) -> None:
    await _ensure_schema()
    async with SessionLocal() as session:
        device, token = await DeviceService(session).create(code=code, name=name)
        await session.commit()
    print(f"✅ Устройство создано: {device.code}")
    print(f"🔑 Токен (сохраните, показывается один раз): {token}")


async def cmd_list_devices() -> None:
    await _ensure_schema()
    async with SessionLocal() as session:
        svc = DeviceService(session)
        for d in await svc.list():
            state = "онлайн" if svc.is_online(d) else "офлайн"
            print(f"   • {d.code} — {d.name} [{state}] zone={d.zone}")


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed")
    sub.add_parser("scan-music")
    p_dev = sub.add_parser("create-device")
    p_dev.add_argument("code")
    p_dev.add_argument("name")
    sub.add_parser("list-devices")

    args = parser.parse_args(argv)
    if args.command == "seed":
        asyncio.run(cmd_seed())
    elif args.command == "scan-music":
        asyncio.run(cmd_scan_music())
    elif args.command == "create-device":
        asyncio.run(cmd_create_device(args.code, args.name))
    elif args.command == "list-devices":
        asyncio.run(cmd_list_devices())
    return 0


if __name__ == "__main__":
    sys.exit(main())
