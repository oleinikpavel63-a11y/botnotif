"""Bot handlers: commands, inline callbacks, free-text intents, track upload.

Every action re-validates on the backend via the services layer — buttons are
only a convenience, never the security boundary.
"""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import DomainError, HighVolumeConfirmationRequired
from ..core.logging import get_logger
from ..core.rbac import Permission, has_permission
from ..models import Device, User
from ..services.devices import DeviceService
from ..services.playback import CommandResult, PlaybackService
from ..services.scenarios import ScenarioService
from ..services.status import StatusService
from ..services.tracks import TrackService
from ..services.volume import step_volume
from . import keyboards as kb
from . import texts
from .confirmations import confirmations
from .parser import Intent, IntentType, parse

log = get_logger("bot")
router = Router(name="main")

_NO_DEVICE = "⚠️ Устройство (рупор) не настроено. Обратитесь к владельцу системы."


async def _default_device(session: AsyncSession) -> Device | None:
    return await DeviceService(session).get_default_device()


async def _panel_payload(session: AsyncSession):
    device = await _default_device(session)
    if device is None:
        return _NO_DEVICE, None
    now = await StatusService(session).now_playing(device)
    return texts.panel_text(now), kb.main_panel()


# ── Commands ─────────────────────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, user: User) -> None:
    text, markup = await _panel_payload(session)
    await message.answer(text, reply_markup=markup)


@router.message(Command("panel"))
async def cmd_panel(message: Message, session: AsyncSession, user: User) -> None:
    text, markup = await _panel_payload(session)
    await message.answer(text, reply_markup=markup)


@router.message(Command("help"))
async def cmd_help(message: Message, **_: object) -> None:
    await message.answer(texts.HELP)


@router.message(Command("now"))
async def cmd_now(message: Message, session: AsyncSession, **_: object) -> None:
    device = await _default_device(session)
    if device is None:
        await message.answer(_NO_DEVICE)
        return
    now = await StatusService(session).now_playing(device)
    await message.answer(texts.now_playing_text(now), reply_markup=kb.back_to_panel())


@router.message(Command("devices"))
async def cmd_devices(message: Message, session: AsyncSession, **_: object) -> None:
    svc = DeviceService(session)
    devices = await svc.list()
    if not devices:
        await message.answer(_NO_DEVICE)
        return
    lines = ["📟 <b>Устройства (рупоры)</b>\n"]
    for d in devices:
        badge = "🟢 онлайн" if svc.is_online(d) else "🔴 офлайн"
        last = d.last_seen_at.strftime("%d.%m %H:%M") if d.last_seen_at else "—"
        lines.append(f"{badge} — <b>{d.name}</b> ({d.zone})\n    Последняя связь: {last}")
    await message.answer("\n".join(lines))


@router.message(Command("scenarios"))
async def cmd_scenarios(message: Message, session: AsyncSession, **_: object) -> None:
    scenarios = await ScenarioService(session).list_active()
    await message.answer("🎬 Быстрые сценарии:", reply_markup=kb.scenarios_list(scenarios))


@router.message(Command("play"))
async def cmd_play(message: Message, session: AsyncSession, **_: object) -> None:
    tracks = await TrackService(session).list_all()
    if not tracks:
        await message.answer(
            "🎵 Пока нет треков. Отправьте боту аудиофайл или выполните scan-music."
        )
        return
    await message.answer("🎵 Выберите трек:", reply_markup=kb.tracks_list(tracks))


@router.message(Command("pause"))
async def cmd_pause(message: Message, session: AsyncSession, user: User) -> None:
    await _do_simple(message, session, user, "pause")


@router.message(Command("resume"))
async def cmd_resume(message: Message, session: AsyncSession, user: User) -> None:
    await _do_simple(message, session, user, "resume")


@router.message(Command("stop"))
async def cmd_stop(message: Message, session: AsyncSession, user: User) -> None:
    await _do_simple(message, session, user, "stop")


@router.message(Command("volume"))
async def cmd_volume(message: Message, session: AsyncSession, user: User) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Укажите громкость: <code>/volume 60</code>")
        return
    await _set_volume(message, session, user, int(parts[1]))


# ── Free-text intents (incl. cyrillic /сбор and plain phrases) ───────────────


@router.message(F.text)
async def on_text(message: Message, session: AsyncSession, user: User) -> None:
    intent: Intent = parse(message.text or "")
    if intent.type == IntentType.PANEL:
        text, markup = await _panel_payload(session)
        await message.answer(text, reply_markup=markup)
    elif intent.type == IntentType.HELP:
        await message.answer(texts.HELP)
    elif intent.type == IntentType.NOW:
        await cmd_now(message, session=session)
    elif intent.type == IntentType.PAUSE:
        await _do_simple(message, session, user, "pause")
    elif intent.type == IntentType.RESUME:
        await _do_simple(message, session, user, "resume")
    elif intent.type == IntentType.STOP:
        await _do_simple(message, session, user, "stop")
    elif intent.type == IntentType.VOLUME and intent.volume is not None:
        await _set_volume(message, session, user, intent.volume)
    elif intent.type == IntentType.SCENARIO and intent.scenario_code:
        await _start_scenario(message, session, user, intent.scenario_code)
    else:
        await message.answer(
            "🤔 Не понял команду. Нажмите /panel или /help.",
        )


# ── Audio upload (add track) ─────────────────────────────────────────────────


@router.message(F.audio | F.voice | F.document)
async def on_audio(message: Message, session: AsyncSession, user: User, bot: Bot) -> None:
    if not has_permission(user.role_enum, Permission.TRACK_MANAGE):
        await message.answer("⛔️ Добавлять треки может только администратор.")
        return
    media = message.audio or message.document or message.voice
    if media is None:
        return
    filename = getattr(media, "file_name", None) or f"{media.file_unique_id}.mp3"
    try:
        buffer = await bot.download(media.file_id)
        data = buffer.read() if buffer else b""
        track = await TrackService(session).create_from_bytes(
            data,
            filename=filename,
            title=(message.caption or filename).strip(),
            creator=user,
            telegram_file_id=media.file_id,
            telegram_file_unique_id=media.file_unique_id,
            interface="bot",
        )
        await message.answer(
            f"✅ Трек добавлен: <b>{track.title}</b>\n"
            "Он будет синхронизирован на устройство при первом запуске."
        )
    except DomainError as exc:
        await message.answer(exc.message)


# ── Callbacks ────────────────────────────────────────────────────────────────


@router.callback_query(F.data == "nav:panel")
async def cb_panel(cb: CallbackQuery, session: AsyncSession, **_: object) -> None:
    text, markup = await _panel_payload(session)
    await _edit(cb, text, markup)
    await cb.answer()


@router.callback_query(F.data == "nav:scenarios")
async def cb_scenarios(cb: CallbackQuery, session: AsyncSession, **_: object) -> None:
    scenarios = await ScenarioService(session).list_active()
    await _edit(cb, "🎬 Быстрые сценарии:", kb.scenarios_list(scenarios))
    await cb.answer()


@router.callback_query(F.data == "nav:music")
async def cb_music(cb: CallbackQuery, session: AsyncSession, **_: object) -> None:
    tracks = await TrackService(session).list_all()
    if not tracks:
        await cb.answer("Пока нет треков.", show_alert=True)
        return
    await _edit(cb, "🎵 Выберите трек:", kb.tracks_list(tracks))
    await cb.answer()


@router.callback_query(F.data == "nav:announce")
async def cb_announce(cb: CallbackQuery, session: AsyncSession, **_: object) -> None:
    tracks = await TrackService(session).list_all()
    await _edit(cb, "📣 Объявления:", kb.tracks_list(tracks, announcements=True))
    await cb.answer()


@router.callback_query(F.data == "nav:schedule")
async def cb_schedule(cb: CallbackQuery, session: AsyncSession, **_: object) -> None:
    from ..services.schedule import ScheduleService

    scheds = await ScheduleService(session).list_all()
    if not scheds:
        await _edit(cb, "🗓 Расписание пусто.", kb.back_to_panel())
    else:
        lines = ["🗓 <b>Расписание</b>\n"]
        for s in scheds:
            state = "✅" if s.is_enabled else "⏸"
            when = s.next_run_at.strftime("%d.%m %H:%M") if s.next_run_at else "—"
            lines.append(f"{state} {s.name} → {when}")
        await _edit(cb, "\n".join(lines), kb.back_to_panel())
    await cb.answer()


@router.callback_query(F.data == "nav:manage")
async def cb_manage(cb: CallbackQuery, user: User, **_: object) -> None:
    if not has_permission(user.role_enum, Permission.USER_VIEW):
        await cb.answer("⛔️ Недостаточно прав.", show_alert=True)
        return
    await _edit(
        cb,
        "⚙️ <b>Управление</b>\nОткройте Mini App для полного администрирования "
        "(пользователи, устройства, журнал).",
        kb.back_to_panel(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("scn:"))
async def cb_scenario(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    code = (cb.data or "").split(":", 1)[1]
    await _start_scenario(cb, session, user, code)


@router.callback_query(F.data.startswith("trk:"))
async def cb_track(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    track_id = (cb.data or "").split(":", 1)[1]
    device = await _default_device(session)
    if device is None:
        await cb.answer(_NO_DEVICE, show_alert=True)
        return
    playback = PlaybackService(session)
    track = await playback.tracks.get(track_id)
    if track is None:
        await cb.answer("Трек не найден.", show_alert=True)
        return
    await _execute(
        cb,
        session,
        user,
        lambda: playback.play_track(user, device, track, interface="bot"),
        success_render=lambda r: _render_started(user, device, r),
    )


@router.callback_query(F.data == "act:pause")
async def cb_pause(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _do_simple(cb, session, user, "pause")


@router.callback_query(F.data == "act:stop")
async def cb_stop(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _do_simple(cb, session, user, "stop")


@router.callback_query(F.data == "act:vol_up")
async def cb_vol_up(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _nudge_volume(cb, session, user, +1)


@router.callback_query(F.data == "act:vol_down")
async def cb_vol_down(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _nudge_volume(cb, session, user, -1)


@router.callback_query(F.data == "cancel")
async def cb_cancel(cb: CallbackQuery, **_: object) -> None:
    await _edit(cb, "✖️ Отменено.", kb.back_to_panel())
    await cb.answer()


@router.callback_query(F.data.startswith("cf:"))
async def cb_confirm(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    token = (cb.data or "").split(":", 1)[1]
    pending = confirmations.take(token, cb.from_user.id)
    if pending is None:
        await cb.answer("⏳ Команда устарела. Откройте панель и повторите.", show_alert=True)
        return
    device = await _default_device(session)
    if device is None:
        await cb.answer(_NO_DEVICE, show_alert=True)
        return
    playback = PlaybackService(session)
    if pending.action == "scenario":
        scenario = await ScenarioService(session).get_by_code(pending.params["code"])
        if scenario is None:
            await cb.answer("Сценарий не найден.", show_alert=True)
            return
        await _execute(
            cb,
            session,
            user,
            lambda: playback.play_scenario(
                user, device, scenario, interface="bot", high_confirmed=True
            ),
            success_render=lambda r: _render_started(user, device, r),
        )
    elif pending.action == "volume":
        vol = int(pending.params["volume"])
        await _execute(
            cb,
            session,
            user,
            lambda: playback.set_volume(user, device, vol, interface="bot", high_confirmed=True),
            success_render=lambda r: texts.volume_changed_text(r.volume or vol, user.display_name),
        )


# ── Shared execution helpers ─────────────────────────────────────────────────


async def _start_scenario(target, session: AsyncSession, user: User, code: str) -> None:
    device = await _default_device(session)
    if device is None:
        await _reply(target, _NO_DEVICE)
        return
    scenario = await ScenarioService(session).get_by_code(code)
    if scenario is None:
        await _reply(target, "Сценарий не найден.")
        return
    if scenario.confirmation_required:
        token = confirmations.create("scenario", _uid(target), {"code": code})
        await _reply(
            target,
            texts.confirm_scenario_text(
                icon=scenario.icon, name=scenario.name, volume=scenario.volume, zone=device.zone
            ),
            kb.confirm(token),
        )
        return
    playback = PlaybackService(session)
    await _execute(
        target,
        session,
        user,
        lambda: playback.play_scenario(
            user, device, scenario, interface="bot", high_confirmed=True
        ),
        success_render=lambda r: _render_started(user, device, r),
    )


async def _do_simple(target, session: AsyncSession, user: User, action: str) -> None:
    device = await _default_device(session)
    if device is None:
        await _reply(target, _NO_DEVICE)
        return
    playback = PlaybackService(session)
    verbs = {
        "pause": (playback.pause, "⏸ Пауза"),
        "resume": (playback.resume, "▶️ Продолжено"),
        "stop": (playback.stop, "⏹ Остановлено"),
    }
    fn, ok_text = verbs[action]
    await _execute(
        target,
        session,
        user,
        lambda: fn(user, device, interface="bot"),
        success_render=lambda r: f"{ok_text} • 👤 {user.display_name}",
    )


async def _set_volume(target, session: AsyncSession, user: User, volume: int) -> None:
    device = await _default_device(session)
    if device is None:
        await _reply(target, _NO_DEVICE)
        return
    playback = PlaybackService(session)
    try:
        result = await playback.set_volume(user, device, volume, interface="bot")
        await _reply(target, texts.volume_changed_text(result.volume or volume, user.display_name))
    except HighVolumeConfirmationRequired as exc:
        token = confirmations.create("volume", _uid(target), {"volume": volume})
        await _reply(target, exc.message, kb.confirm(token))
    except DomainError as exc:
        await _reply(target, exc.message)


async def _nudge_volume(
    cb: CallbackQuery, session: AsyncSession, user: User, direction: int
) -> None:
    from ..core.config import settings

    device = await _default_device(session)
    if device is None:
        await cb.answer(_NO_DEVICE, show_alert=True)
        return
    state = DeviceService(session).live_state(device)
    current = state.volume if state else device.default_volume
    target_vol = step_volume(
        current, direction * settings.volume_step, role=user.role_enum, device=device
    )
    await _set_volume(cb, session, user, target_vol)
    await cb.answer(f"🔊 {target_vol}%")


async def _execute(target, session, user, action, *, success_render) -> None:
    """Run a playback action, rendering success or a friendly error."""
    try:
        result: CommandResult = await action()
    except DomainError as exc:
        await _reply(target, exc.message, kb.back_to_panel())
        if isinstance(target, CallbackQuery):
            await target.answer()
        return
    except Exception as exc:
        log.warning("bot_action_error", error=str(exc))
        await _reply(target, "⚠️ Внутренняя ошибка. Попробуйте позже.", kb.back_to_panel())
        return
    await _reply(target, success_render(result), kb.playback_controls())
    if isinstance(target, CallbackQuery):
        await target.answer("Готово")


def _render_started(user: User, device: Device, result: CommandResult) -> str:
    return texts.playback_started_text(
        track_title=result.track_title or "—",
        scenario_name=None,
        volume=result.volume or device.default_volume,
        zone=device.zone,
        actor=user.display_name,
    )


# ── Message/callback IO abstraction ──────────────────────────────────────────


def _uid(target) -> int:
    return target.from_user.id


async def _reply(target, text: str, markup=None) -> None:
    if isinstance(target, CallbackQuery):
        await _edit(target, text, markup)
    else:
        await target.answer(text, reply_markup=markup)


async def _edit(cb: CallbackQuery, text: str, markup=None) -> None:
    from aiogram.types import Message

    if not isinstance(cb.message, Message):
        return
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except Exception:
        await cb.message.answer(text, reply_markup=markup)
