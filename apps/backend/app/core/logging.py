"""Structured logging with secret redaction.

Secrets (bot token, device tokens, signatures) must never reach the logs. A
processor redacts any value that looks like one of the known secret keys.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from .config import settings

_SECRET_KEYS = {
    "token",
    "bot_token",
    "telegram_bot_token",
    "device_token",
    "agent_device_token",
    "password",
    "secret",
    "secret_key",
    "authorization",
    "hash",
    "signature",
    "access_token",
    "webhook_secret",
}
_REDACTED = "«redacted»"


def _redact(_logger: Any, _method: str, event: dict[str, Any]) -> dict[str, Any]:
    for key in list(event.keys()):
        if key.lower() in _SECRET_KEYS and event[key]:
            event[key] = _REDACTED
    return event


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact,
    ]
    renderer: Any = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    structlog.configure(
        processors=[*shared, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[return-value]
