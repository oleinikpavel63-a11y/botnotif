"""Backend management CLI: ``python -m app.cli <command>``.

Commands:
  seed             Seed OWNER, default device, scenarios, settings (idempotent).
  scan-music       Import audio files from storage/music into the library.
  create-device    Create a device and print its token (shown once).
  list-devices     List devices and their status.
  list-scenarios   List scenarios and their bound track.
  bind-scenario    Bind a track (by title substring) to a scenario (by code).
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
from .repositories import ScenarioRepository, TrackRepository
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


async def cmd_list_scenarios() -> None:
    await _ensure_schema()
    async with SessionLocal() as session:
        scenarios = await ScenarioRepository(session).list_all()
        tracks = TrackRepository(session)
        for s in scenarios:
            track = await tracks.get(s.track_id) if s.track_id else None
            bound = track.title if track else "— (трек не привязан)"
            print(f"   {s.icon} {s.code:22} {s.name:20} → {bound}")


async def cmd_bind_scenario(code: str, title_query: str) -> None:
    await _ensure_schema()
    async with SessionLocal() as session:
        scenario = await ScenarioRepository(session).get_by_code(code)
        if scenario is None:
            print(f"❌ Сценарий с кодом «{code}» не найден. См. list-scenarios.")
            return
        all_tracks = await TrackRepository(session).list_all()
        matches = [t for t in all_tracks if title_query.lower() in t.title.lower()]
        if not matches:
            print(f"❌ Трек по запросу «{title_query}» не найден. Сначала scan-music.")
            return
        if len(matches) > 1:
            print("⚠️ Найдено несколько треков, уточните запрос:")
            for t in matches:
                print(f"   • {t.title}")
            return
        track = matches[0]
        scenario.track_id = track.id
        scenario.playlist_id = None
        await session.commit()
    print(f"✅ Сценарий «{scenario.name}» ({code}) → трек «{track.title}»")


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
    sub.add_parser("list-scenarios")
    p_bind = sub.add_parser("bind-scenario")
    p_bind.add_argument("code", help="scenario code, e.g. general_gathering")
    p_bind.add_argument("title", help="substring of the track title to bind")

    args = parser.parse_args(argv)
    if args.command == "seed":
        asyncio.run(cmd_seed())
    elif args.command == "scan-music":
        asyncio.run(cmd_scan_music())
    elif args.command == "create-device":
        asyncio.run(cmd_create_device(args.code, args.name))
    elif args.command == "list-devices":
        asyncio.run(cmd_list_devices())
    elif args.command == "list-scenarios":
        asyncio.run(cmd_list_scenarios())
    elif args.command == "bind-scenario":
        asyncio.run(cmd_bind_scenario(args.code, args.title))
    return 0


if __name__ == "__main__":
    sys.exit(main())
