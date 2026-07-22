"""Player Agent CLI: ``python -m agent.cli <command>``.

stop                Emergency stop (writes the stop-file — works offline).
status              Print local player status.
list-audio-devices  List mpv audio output devices.
test-audio          Play a short test tone through the selected device.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .audio.devices import list_audio_devices
from .audio.mpv_player import MpvPlayer
from .config import get_config
from .logging import configure_logging


async def cmd_stop() -> None:
    config = get_config()
    config.stop_file.parent.mkdir(parents=True, exist_ok=True)
    config.stop_file.write_text("stop", "utf-8")
    print(f"🛑 Аварийный стоп-файл создан: {config.stop_file}")
    print("Агент остановит звук немедленно (даже без связи с backend).")


async def cmd_status() -> None:
    config = get_config()
    if not config.state_db.exists():
        print("Состояние агента не найдено (ещё не запускался).")
        return
    print(f"Устройство: {config.agent_device_id}")
    print(f"Сервер: {config.agent_server_url}")
    print(f"Аудиоустройство mpv: {config.mpv_audio_device or 'по умолчанию'}")
    print(f"Кэш: {config.cache_dir}")
    print(f"Файл состояния: {config.state_db}")


async def cmd_list_audio() -> None:
    config = get_config()
    try:
        devices = await list_audio_devices(config.mpv_binary)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        return
    if not devices:
        print("Устройства не найдены.")
        return
    print("Доступные аудиоустройства (значение для MPV_AUDIO_DEVICE):\n")
    for d in devices:
        print(f"  {d.name}")
        if d.description:
            print(f"      {d.description}")


async def cmd_test_audio() -> None:
    config = get_config()
    player = MpvPlayer(
        mpv_binary=config.mpv_binary,
        ipc_socket=config.default_ipc_socket,
        audio_device=config.mpv_audio_device,
        default_volume=min(config.default_volume, 50),
    )
    try:
        await player.start()
    except Exception as exc:
        print(f"❌ Не удалось запустить mpv: {exc}")
        return
    # mpv can synthesise a test tone via its AV filter graph.
    try:
        await player._command(["loadfile", "av://lavfi:sine=frequency=440:duration=2", "replace"])
        print("🔊 Воспроизводится тестовый тон (2 сек)...")
        await asyncio.sleep(2.5)
        print("✅ Готово. Если звука не было — проверьте MPV_AUDIO_DEVICE и провода.")
    finally:
        await player.close()


def main(argv: list[str] | None = None) -> int:
    configure_logging("WARNING")
    parser = argparse.ArgumentParser(prog="agent.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("stop")
    sub.add_parser("status")
    sub.add_parser("list-audio-devices")
    sub.add_parser("test-audio")
    args = parser.parse_args(argv)

    commands = {
        "stop": cmd_stop,
        "status": cmd_status,
        "list-audio-devices": cmd_list_audio,
        "test-audio": cmd_test_audio,
    }
    asyncio.run(commands[args.command]())
    return 0


if __name__ == "__main__":
    sys.exit(main())
