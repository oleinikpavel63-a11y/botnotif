"""Enumerate audio output devices via ``mpv --audio-device=help``."""

from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass


@dataclass
class AudioDevice:
    name: str
    description: str


async def list_audio_devices(mpv_binary: str) -> list[AudioDevice]:
    if shutil.which(mpv_binary) is None and not os.path.exists(mpv_binary):
        raise RuntimeError(f"mpv не найден: {mpv_binary}")
    proc = await asyncio.create_subprocess_exec(
        mpv_binary,
        "--audio-device=help",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    devices: list[AudioDevice] = []
    for line in out.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line.startswith("'"):
            continue
        # format: 'name' (Description)
        try:
            name = line.split("'", 2)[1]
            desc = line.split("(", 1)[1].rstrip(")") if "(" in line else ""
        except IndexError:
            continue
        devices.append(AudioDevice(name=name, description=desc))
    return devices
