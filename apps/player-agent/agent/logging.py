"""Agent logging (structlog, console). Never logs the device token."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

_SECRET_KEYS = {"token", "device_token", "agent_device_token", "authorization", "secret"}


def _redact(_logger: Any, _method: str, event: dict[str, Any]) -> dict[str, Any]:
    for key in list(event.keys()):
        if key.lower() in _SECRET_KEYS and event[key]:
            event[key] = "«redacted»"
    return event


def configure_logging(level: str = "INFO") -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=lvl)
    processors: list[Any] = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact,
        structlog.dev.ConsoleRenderer(colors=False),
    ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(lvl),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[return-value]
