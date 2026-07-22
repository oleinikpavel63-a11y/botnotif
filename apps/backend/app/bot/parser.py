"""Safe, dictionary-based parser for free-text Russian commands.

Deliberately *not* an AI model — a small, auditable keyword matcher. It never
executes anything itself; it only maps text to a typed :class:`Intent` that the
handler layer validates and (where needed) confirms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class IntentType(str, Enum):
    PANEL = "panel"
    SCENARIO = "scenario"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    VOLUME = "volume"
    NOW = "now"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    type: IntentType
    scenario_code: str | None = None
    volume: int | None = None
    raw: str = ""
    extra: dict = field(default_factory=dict)


#: keyword (normalised) -> scenario code. Matched by whole-word containment.
SCENARIO_KEYWORDS: dict[str, str] = {
    "сбор": "general_gathering",
    "общий сбор": "general_gathering",
    "подъем": "wake_up",
    "подъём": "wake_up",
    "завтрак": "breakfast",
    "обед": "lunch",
    "ужин": "dinner",
    "игры": "games",
    "спорт": "games",
    "служение": "evening_service",
    "творчество": "creative",
    "творческий": "creative",
    "фон": "background",
    "фоновая": "background",
    "отбой": "lights_out",
    "объявление": "urgent_announcement",
    "срочное": "urgent_announcement",
}

_STOP_WORDS = {"стоп", "останови", "остановить", "выключи", "выключить", "тихо"}
_PAUSE_WORDS = {"пауза", "поставь на паузу", "приостанови"}
_RESUME_WORDS = {"продолжи", "продолжить", "возобнови", "resume"}
_NOW_WORDS = {"что играет", "что сейчас играет", "сейчас", "статус"}
_PANEL_WORDS = {"панель", "меню", "старт"}
_HELP_WORDS = {"помощь", "справка"}

_VOLUME_RE = re.compile(r"громкост\w*\s*(\d{1,3})")
_VOLUME_ALT_RE = re.compile(r"\b(\d{1,3})\s*%")


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).lstrip("/")


def parse(text: str) -> Intent:
    raw = text or ""
    norm = normalise(raw)
    if not norm:
        return Intent(IntentType.UNKNOWN, raw=raw)

    # Volume: "громкость 60" / "60%"
    m = _VOLUME_RE.search(norm) or _VOLUME_ALT_RE.search(norm)
    if m and ("громк" in norm or "%" in norm):
        vol = max(0, min(100, int(m.group(1))))
        return Intent(IntentType.VOLUME, volume=vol, raw=raw)

    if any(w in norm for w in _PANEL_WORDS):
        return Intent(IntentType.PANEL, raw=raw)
    if any(w in norm for w in _HELP_WORDS):
        return Intent(IntentType.HELP, raw=raw)
    if any(w in norm for w in _NOW_WORDS):
        return Intent(IntentType.NOW, raw=raw)
    if any(w in norm for w in _PAUSE_WORDS):
        return Intent(IntentType.PAUSE, raw=raw)
    if any(w in norm for w in _RESUME_WORDS):
        return Intent(IntentType.RESUME, raw=raw)
    if any(w in norm for w in _STOP_WORDS):
        return Intent(IntentType.STOP, raw=raw)

    # Scenarios (longest keyword first so "общий сбор" wins over "сбор").
    for keyword in sorted(SCENARIO_KEYWORDS, key=len, reverse=True):
        if re.search(rf"(^|\W){re.escape(keyword)}(\W|$)", norm):
            return Intent(IntentType.SCENARIO, scenario_code=SCENARIO_KEYWORDS[keyword], raw=raw)

    return Intent(IntentType.UNKNOWN, raw=raw)
