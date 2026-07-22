"""Player Agent configuration (reads the shared ``.env``)."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AGENT_DIR.parent.parent


class AgentConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", AGENT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    agent_server_url: str = "ws://127.0.0.1:8000/ws/agent"
    agent_api_base_url: str = "http://127.0.0.1:8000"
    agent_device_id: str = "main-camp-speakers"
    agent_device_token: str = ""
    agent_app_version: str = "1.0.0"
    agent_stop_file: str = "./data/agent-stop.flag"
    agent_state_db: str = "./data/agent-state.json"
    agent_hotkey: str = ""

    mpv_executable_path: str = ""
    mpv_audio_device: str = ""
    mpv_ipc_socket: str = ""

    music_cache_path: str = "./storage/music"

    default_volume: int = 60
    max_safe_volume: int = 80
    absolute_max_volume: int = 100

    heartbeat_interval_seconds: int = 5
    resume_after_restart: bool = False

    log_level: str = "INFO"

    def _abs(self, raw: str) -> Path:
        p = Path(raw)
        return p if p.is_absolute() else (REPO_ROOT / raw)

    @property
    def stop_file(self) -> Path:
        return self._abs(self.agent_stop_file)

    @property
    def state_db(self) -> Path:
        return self._abs(self.agent_state_db)

    @property
    def cache_dir(self) -> Path:
        return self._abs(self.music_cache_path)

    @property
    def mpv_binary(self) -> str:
        if self.mpv_executable_path:
            return self.mpv_executable_path
        return "mpv.exe" if sys.platform == "win32" else "mpv"

    @property
    def default_ipc_socket(self) -> str:
        if self.mpv_ipc_socket:
            return self.mpv_ipc_socket
        if sys.platform == "win32":
            return r"\\.\pipe\lw-mpv"
        return str(self._abs("./data/lw-mpv.sock"))


@lru_cache
def get_config() -> AgentConfig:
    return AgentConfig()
