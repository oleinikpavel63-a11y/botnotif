"""Line-delimited JSON-IPC transport for mpv.

Two transports: a Unix-domain-socket one (Linux / macOS / Raspberry Pi) built on
asyncio streams, and a Windows named-pipe one built on a blocking file handle in
a reader thread. Both expose the same tiny async interface.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, Protocol


class IpcTransport(Protocol):
    async def connect(self) -> None: ...
    async def send_line(self, data: bytes) -> None: ...
    async def read_line(self) -> bytes | None: ...
    async def close(self) -> None: ...


class UnixSocketTransport:
    def __init__(self, path: str) -> None:
        self._path = path
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_unix_connection(self._path)

    async def send_line(self, data: bytes) -> None:
        assert self._writer is not None
        self._writer.write(data)
        await self._writer.drain()

    async def read_line(self) -> bytes | None:
        assert self._reader is not None
        line = await self._reader.readline()
        return line or None

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:  # pragma: no cover - best-effort
                pass


class WindowsPipeTransport:
    """Named-pipe client using a blocking handle + a reader thread."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._fh: Any = None
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._reader_thread: Any = None
        self._closed = False

    async def connect(self) -> None:
        import threading

        # Long-lived named-pipe handle owned by the transport (closed in close()).
        self._fh = await asyncio.to_thread(lambda: open(self._path, "r+b", buffering=0))  # noqa: SIM115

        def _reader() -> None:
            try:
                while not self._closed:
                    line = self._fh.readline()
                    if not line:
                        break
                    asyncio.run_coroutine_threadsafe(self._queue.put(line), loop)
            finally:
                asyncio.run_coroutine_threadsafe(self._queue.put(None), loop)

        loop = asyncio.get_event_loop()
        self._reader_thread = threading.Thread(target=_reader, daemon=True)
        self._reader_thread.start()

    async def send_line(self, data: bytes) -> None:
        await asyncio.to_thread(self._fh.write, data)

    async def read_line(self) -> bytes | None:
        return await self._queue.get()

    async def close(self) -> None:
        self._closed = True
        if self._fh is not None:
            try:
                await asyncio.to_thread(self._fh.close)
            except Exception:  # pragma: no cover
                pass


def make_transport(path: str) -> IpcTransport:
    if sys.platform == "win32":
        return WindowsPipeTransport(path)
    return UnixSocketTransport(path)
