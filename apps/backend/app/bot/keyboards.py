"""Inline keyboards. Callback data is compact: ``prefix:arg``."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models import CampScenario, Track


def main_panel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏕 Сбор", callback_data="scn:general_gathering")
    kb.button(text="🎵 Музыка", callback_data="nav:music")
    kb.button(text="⏸ Пауза", callback_data="act:pause")
    kb.button(text="⏹ Стоп", callback_data="act:stop")
    kb.button(text="🔉 Тише", callback_data="act:vol_down")
    kb.button(text="🔊 Громче", callback_data="act:vol_up")
    kb.button(text="🎬 Сценарии", callback_data="nav:scenarios")
    kb.button(text="🗓 Расписание", callback_data="nav:schedule")
    kb.button(text="📣 Объявления", callback_data="nav:announce")
    kb.button(text="⚙️ Управление", callback_data="nav:manage")
    kb.adjust(2, 2, 2, 2, 2)
    return kb.as_markup()


def playback_controls() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⏸ Пауза", callback_data="act:pause")
    kb.button(text="⏹ Остановить", callback_data="act:stop")
    kb.button(text="🔉 −5%", callback_data="act:vol_down")
    kb.button(text="🔊 +5%", callback_data="act:vol_up")
    kb.button(text="⬅️ Панель", callback_data="nav:panel")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def confirm(token: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ Да, включить", callback_data=f"cf:{token}")
    kb.button(text="✖️ Отмена", callback_data="cancel")
    kb.adjust(1, 1)
    return kb.as_markup()


def scenarios_list(scenarios: list[CampScenario]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in scenarios:
        kb.button(text=f"{s.icon} {s.name}", callback_data=f"scn:{s.code}")
    kb.button(text="⬅️ Панель", callback_data="nav:panel")
    kb.adjust(1)
    return kb.as_markup()


def tracks_list(tracks: list[Track], *, announcements: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    shown = [t for t in tracks if t.is_announcement == announcements][:20]
    for t in shown:
        kb.button(text=f"🎵 {t.title}", callback_data=f"trk:{t.id}")
    kb.button(text="⬅️ Панель", callback_data="nav:panel")
    kb.adjust(1)
    return kb.as_markup()


def back_to_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Панель", callback_data="nav:panel")]]
    )
