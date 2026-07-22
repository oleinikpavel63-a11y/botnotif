"""HTTP downloader for track files (authenticated with the device token)."""

from __future__ import annotations

from pathlib import Path

import httpx

from ..logging import get_logger

log = get_logger("downloader")


class Downloader:
    def __init__(self, api_base_url: str, device_token: str) -> None:
        self._base = api_base_url.rstrip("/")
        self._token = device_token

    async def fetch(self, download_url: str, dest: Path) -> None:
        """Stream ``download_url`` (relative or absolute) into ``dest``."""
        url = download_url if download_url.startswith("http") else f"{self._base}{download_url}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        headers = {"X-Device-Token": self._token}
        async with (
            httpx.AsyncClient(timeout=60) as client,
            client.stream("GET", url, headers=headers) as resp,
        ):
            resp.raise_for_status()
            with tmp.open("wb") as fh:
                async for chunk in resp.aiter_bytes(1 << 16):
                    fh.write(chunk)
        tmp.replace(dest)
        log.info("downloaded", url=url, dest=str(dest))
