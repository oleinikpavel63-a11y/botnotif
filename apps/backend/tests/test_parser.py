from __future__ import annotations

import pytest
from app.bot.parser import IntentType, parse


@pytest.mark.parametrize(
    "text,code",
    [
        ("включить сбор", "general_gathering"),
        ("музыка на сбор", "general_gathering"),
        ("общий сбор", "general_gathering"),
        ("/сбор", "general_gathering"),
        ("подъем", "wake_up"),
        ("завтрак", "breakfast"),
        ("отбой", "lights_out"),
    ],
)
def test_scenario_phrases(text, code):
    intent = parse(text)
    assert intent.type == IntentType.SCENARIO
    assert intent.scenario_code == code


def test_stop_phrases():
    assert parse("остановить музыку").type == IntentType.STOP
    assert parse("стоп").type == IntentType.STOP


def test_volume_phrases():
    assert parse("громкость 60").type == IntentType.VOLUME
    assert parse("громкость 60").volume == 60
    assert parse("60%").volume == 60


def test_volume_clamped():
    assert parse("громкость 150").volume == 100


def test_now_and_panel():
    assert parse("что сейчас играет").type == IntentType.NOW
    assert parse("меню").type == IntentType.PANEL


def test_unknown():
    assert parse("привет как дела").type == IntentType.UNKNOWN


def test_longest_scenario_keyword_wins():
    # "общий сбор" should still resolve to gathering (not a partial mismatch).
    assert parse("объявляется общий сбор отрядов").scenario_code == "general_gathering"
