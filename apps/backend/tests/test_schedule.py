from __future__ import annotations

from datetime import UTC, datetime

from app.services.schedule import next_run_after


def _utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=UTC)


def test_daily_next_run_same_day_chisinau():
    # Chisinau is UTC+3 in July (DST). 07:30 local = 04:30 UTC.
    after = _utc(2026, 7, 22, 3, 0)  # 06:00 local
    nxt = next_run_after("daily", {"time": "07:30"}, "Europe/Chisinau", after)
    assert nxt == _utc(2026, 7, 22, 4, 30)


def test_daily_rolls_to_tomorrow_when_past():
    after = _utc(2026, 7, 22, 5, 0)  # 08:00 local, past 07:30
    nxt = next_run_after("daily", {"time": "07:30"}, "Europe/Chisinau", after)
    assert nxt == _utc(2026, 7, 23, 4, 30)


def test_weekly_picks_correct_weekday():
    # 2026-07-22 is a Wednesday (weekday 2). Ask for Friday (4) at 20:00 local.
    after = _utc(2026, 7, 22, 12, 0)
    nxt = next_run_after("weekly", {"time": "20:00", "days": [4]}, "Europe/Chisinau", after)
    assert nxt is not None
    # 20:00 local = 17:00 UTC on Friday 2026-07-24.
    assert nxt == _utc(2026, 7, 24, 17, 0)


def test_once_in_past_returns_none():
    after = _utc(2026, 7, 22, 12, 0)
    nxt = next_run_after("once", {"date": "2026-07-01", "time": "10:00"}, "Europe/Chisinau", after)
    assert nxt is None


def test_once_in_future():
    after = _utc(2026, 7, 22, 12, 0)
    nxt = next_run_after("once", {"date": "2026-08-01", "time": "10:00"}, "Europe/Chisinau", after)
    assert nxt == _utc(2026, 8, 1, 7, 0)  # 10:00 +3 -> 07:00 UTC


def test_winter_dst_offset_is_plus_two():
    # January: Chisinau is UTC+2. 07:30 local = 05:30 UTC.
    after = _utc(2026, 1, 15, 3, 0)
    nxt = next_run_after("daily", {"time": "07:30"}, "Europe/Chisinau", after)
    assert nxt == _utc(2026, 1, 15, 5, 30)
