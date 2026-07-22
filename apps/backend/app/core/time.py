"""Time helpers. Everything internal is timezone-aware UTC; display uses the
configured camp timezone (Europe/Chisinau)."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from .config import settings


def utcnow() -> datetime:
    """Current time as an aware UTC datetime."""
    return datetime.now(UTC)


def camp_tz() -> ZoneInfo:
    return ZoneInfo(settings.app_timezone)


def to_camp(dt: datetime) -> datetime:
    """Convert an aware datetime to the camp timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(camp_tz())


def fmt_time(dt: datetime) -> str:
    """HH:MM in camp timezone (for status messages)."""
    return to_camp(dt).strftime("%H:%M")


def fmt_datetime(dt: datetime) -> str:
    return to_camp(dt).strftime("%d.%m %H:%M")


def ensure_aware(dt: datetime) -> datetime:
    """Guarantee an aware datetime (assume UTC if naive — SQLite loses tzinfo)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
