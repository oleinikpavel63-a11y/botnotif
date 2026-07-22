"""Player Agent entry point.

On start it checks mpv/audio, connects to the backend, syncs state and begins
heartbeating. It never auto-starts playback after a restart (RESUME_AFTER_RESTART
defaults to false).
"""

from __future__ import annotations

import asyncio
import contextlib
import signal

from .audio.mpv_player import MpvPlayer
from .cache.downloader import Downloader
from .cache.store import CacheStore
from .config import AgentConfig, get_config
from .connection.client import AgentClient
from .logging import configure_logging, get_logger
from .security.stopfile import watch_stop_file

log = get_logger("agent")


def _build_player(config: AgentConfig) -> MpvPlayer:
    return MpvPlayer(
        mpv_binary=config.mpv_binary,
        ipc_socket=config.default_ipc_socket,
        audio_device=config.mpv_audio_device,
        default_volume=config.default_volume,
    )


async def async_main(config: AgentConfig | None = None) -> None:
    config = config or get_config()
    configure_logging(config.log_level)
    log.info(
        "agent_starting",
        device=config.agent_device_id,
        server=config.agent_server_url,
        resume_after_restart=config.resume_after_restart,
    )
    if not config.agent_device_token:
        log.error("no_device_token", hint="set AGENT_DEVICE_TOKEN in .env")

    player = _build_player(config)
    try:
        await player.start()
        log.info("mpv_ready")
    except Exception as exc:
        log.error("mpv_unavailable", error=str(exc))

    cache = CacheStore(config.cache_dir, config.state_db)
    downloader = Downloader(config.agent_api_base_url, config.agent_device_token)
    client = AgentClient(config, player, cache, downloader)

    async def _on_stop() -> None:
        if client.handler is not None:
            await client.handler.local_emergency_stop()
        else:
            with contextlib.suppress(Exception):
                await player.stop(fade_out_seconds=0.0)

    stop_watch = asyncio.create_task(watch_stop_file(config.stop_file, _on_stop))
    stop_event = asyncio.Event()

    def _signal(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _signal)

    client_task = asyncio.create_task(client.run())
    log.info("READY")
    await stop_event.wait()
    log.info("shutting_down")
    await client.stop()
    stop_watch.cancel()
    client_task.cancel()
    for task in (stop_watch, client_task):
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await player.close()


def run() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:  # pragma: no cover
        pass


if __name__ == "__main__":
    run()
