"""Human-facing message text for the bot (Russian)."""

from __future__ import annotations

from ..core.time import fmt_time, utcnow
from ..services.status import NowPlaying

HELP = (
    "🏕 <b>Живая вода • Рупор</b> — помощь\n\n"
    "<b>Команды:</b>\n"
    "/start, /panel — панель управления\n"
    "/now — что сейчас играет\n"
    "/play — включить музыку\n"
    "/pause, /resume — пауза / продолжить\n"
    "/stop — остановить\n"
    "/volume 60 — громкость\n"
    "/devices — состояние рупоров\n"
    "/schedule — расписание\n"
    "/scenarios — быстрые сценарии\n"
    "/help — помощь\n\n"
    "<b>Быстрые сценарии:</b> /сбор, /подъем, /завтрак, /обед, /ужин, "
    "/служение, /спорт, /отбой\n\n"
    "Можно писать обычным текстом: «включить сбор», «остановить музыку», "
    "«громкость 60», «что сейчас играет»."
)


def _online_badge(now: NowPlaying) -> str:
    return "🟢 онлайн" if now.online else "🔴 офлайн"


def panel_text(now: NowPlaying) -> str:
    playing = now.track_title or "ничего не играет"
    return (
        "🏕 <b>ЖИВАЯ ВОДА • РУПОР</b>\n"
        f"{_online_badge(now)} • Рупор: {now.device_name}\n"
        f"🎵 Сейчас: {playing}\n"
        f"🔊 Громкость: {now.volume}%\n"
        f"📍 Зона: {now.zone}\n\n"
        "Выберите действие:"
    )


def now_playing_text(now: NowPlaying) -> str:
    if not now.online:
        return (
            f"🔴 <b>Рупор недоступен</b>\nУстройство: {now.device_name}\n"
            "Проверьте, включён ли ноутбук и запущен ли Player Agent."
        )
    if not now.track_title:
        return (
            f"🟢 <b>{now.device_name}</b> — онлайн\n"
            "🎵 Сейчас ничего не играет.\n"
            f"🔊 Громкость: {now.volume}%"
        )
    lines = [
        "🎵 <b>Сейчас играет</b>",
        f"📀 {now.track_title}",
    ]
    if now.scenario_name:
        lines.append(f"📂 Сценарий: {now.scenario_name}")
    if now.duration_seconds:
        pos = int(now.position_seconds or 0)
        dur = int(now.duration_seconds)
        lines.append(f"⏱ {pos // 60}:{pos % 60:02d} / {dur // 60}:{dur % 60:02d}")
    lines.append(f"🔊 Громкость: {now.volume}%")
    lines.append(f"📍 {now.zone}")
    if now.started_by:
        lines.append(f"👤 Запустил: {now.started_by}")
    return "\n".join(lines)


def playback_started_text(
    *, track_title: str, scenario_name: str | None, volume: int, zone: str, actor: str
) -> str:
    lines = [
        "✅ <b>ВОСПРОИЗВЕДЕНИЕ ЗАПУЩЕНО</b>",
        f"🎵 {track_title}",
    ]
    if scenario_name:
        lines.append(f"📂 Сценарий: {scenario_name}")
    lines += [
        f"🔊 Громкость: {volume}%",
        f"📍 {zone}",
        f"👤 Запустил: {actor}",
        f"🕒 {fmt_time(utcnow())}",
    ]
    return "\n".join(lines)


def confirm_scenario_text(*, icon: str, name: str, volume: int, zone: str) -> str:
    return (
        f"{icon} <b>Включить «{name}»?</b>\n"
        f"🔊 Громкость: {volume}%\n"
        f"📍 Зона: {zone}\n\n"
        "Подтвердите запуск:"
    )


def volume_changed_text(volume: int, actor: str) -> str:
    return f"🔊 Громкость: {volume}%\n👤 {actor} • 🕒 {fmt_time(utcnow())}"
