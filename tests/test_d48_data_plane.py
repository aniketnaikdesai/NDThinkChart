"""P8-T01 (D48 data plane): TIMEFRAME_CONFIG rows + calendar bucketing.

T11: the two exact TIMEFRAME_CONFIG rows, key order, byte-equality of the
six pre-existing rows, and TIMEFRAME_SECONDS nominal keys.
T21: Monday-00:00-ET weekly and calendar-month-boundary monthly bucketing
over a DST fold, February, and a Dec/Jan boundary (sessions-only, no
fabrication), with live forming-bar parity through BarAggregator.
"""
from datetime import datetime

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import (
    BarAggregator,
    TIMEFRAME_SECONDS,
    _period_start,
    month_bucket_start,
    week_bucket_start,
)
from ibkr.market_data import TIMEFRAME_CONFIG

_ET = ZoneInfo("America/New_York")


def _et(y, mo, d, h=12, mi=0):
    """Noon-ET session timestamp (safely inside the trading day)."""
    return int(datetime(y, mo, d, h, mi, tzinfo=_ET).timestamp())


def _midnight(y, mo, d):
    """ET-midnight bucket-open timestamp."""
    return int(datetime(y, mo, d, 0, 0, tzinfo=_ET).timestamp())


# ---------------------------------------------------------------------------
# P8-T01-T11: config rows, order, pre-existing byte-equality, nominal seconds
# ---------------------------------------------------------------------------

_EXPECTED_CONFIG = {
    "1 min": {"duration": "30 D", "bar_size": "1 min"},
    "5 mins": {"duration": "30 D", "bar_size": "5 mins"},
    "15 mins": {"duration": "30 D", "bar_size": "15 mins"},
    "30 mins": {"duration": "30 D", "bar_size": "30 mins"},
    "1 hour": {"duration": "60 D", "bar_size": "1 hour"},
    "4 hours": {"duration": "60 D", "bar_size": "4 hours"},
    "1 day": {"duration": "1 Y", "bar_size": "1 day"},
    "1 week": {"duration": "2 Y", "bar_size": "1 week"},
    "1 month": {"duration": "10 Y", "bar_size": "1 month"},
}

_EXPECTED_ORDER = [
    "1 min", "5 mins", "15 mins", "30 mins", "1 hour", "4 hours",
    "1 day", "1 week", "1 month",
]

_EXPECTED_SECONDS = {
    "5 secs": 5,
    "1 min": 60,
    "5 mins": 300,
    "15 mins": 900,
    "30 mins": 1800,
    "1 hour": 3600,
    "4 hours": 14400,
    "1 day": 86400,
    "1 week": 604800,
    "1 month": 2592000,
}


def test_p8_t01_t11_timeframe_config_rows_order_and_history():
    assert list(TIMEFRAME_CONFIG.keys()) == _EXPECTED_ORDER
    assert TIMEFRAME_CONFIG == _EXPECTED_CONFIG
    # Byte-equality of the six pre-existing rows: exact dicts, exact values.
    for tf in ("1 min", "5 mins", "15 mins", "1 hour", "4 hours", "1 day"):
        assert TIMEFRAME_CONFIG[tf] == _EXPECTED_CONFIG[tf]
        assert set(TIMEFRAME_CONFIG[tf].keys()) == {"duration", "bar_size"}
    # The P12 30-min row sits between "15 mins" and "1 hour".
    assert list(TIMEFRAME_CONFIG.keys()).index("30 mins") == 3
    assert TIMEFRAME_CONFIG["30 mins"] == {"duration": "30 D", "bar_size": "30 mins"}
    # The two P8 rows appended immediately after "1 day".
    assert list(TIMEFRAME_CONFIG.keys()).index("1 week") == 7
    assert list(TIMEFRAME_CONFIG.keys()).index("1 month") == 8
    assert TIMEFRAME_CONFIG["1 week"] == {"duration": "2 Y", "bar_size": "1 week"}
    assert TIMEFRAME_CONFIG["1 month"] == {"duration": "10 Y", "bar_size": "1 month"}


def test_p8_t01_t11_timeframe_seconds_nominal_keys():
    assert TIMEFRAME_SECONDS == _EXPECTED_SECONDS
    assert TIMEFRAME_SECONDS["1 week"] == 604800
    assert TIMEFRAME_SECONDS["1 month"] == 2592000
    # The seven pre-existing periods are unchanged.
    for tf, secs in (
        ("5 secs", 5), ("1 min", 60), ("5 mins", 300), ("15 mins", 900),
        ("1 hour", 3600), ("4 hours", 14400), ("1 day", 86400),
    ):
        assert TIMEFRAME_SECONDS[tf] == secs


# ---------------------------------------------------------------------------
# P8-T01-T21: calendar bucketing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "session_ts,expected_monday",
    [
        # DST-fold week (fall-back Sun 2025-11-02): Tue/Wed sessions bucket
        # to Monday 2025-11-03 00:00 ET; the fold Sunday itself belongs to
        # the prior week starting Monday 2025-10-27.
        (_et(2025, 11, 4), _midnight(2025, 11, 3)),
        (_et(2025, 11, 5), _midnight(2025, 11, 3)),
        (_et(2025, 11, 2, h=12), _midnight(2025, 10, 27)),
        (_et(2025, 11, 3, h=9, mi=30), _midnight(2025, 11, 3)),
        # Cross-year Dec/Jan week: Tue 2025-12-30 and Fri 2026-01-02 both
        # bucket to Monday 2025-12-29 00:00 ET.
        (_et(2025, 12, 30), _midnight(2025, 12, 29)),
        (_et(2025, 12, 31), _midnight(2025, 12, 29)),
        (_et(2026, 1, 2), _midnight(2025, 12, 29)),
        (_et(2026, 1, 5), _midnight(2026, 1, 5)),
        # Holiday week (Thanksgiving Thu 2025-11-27, market closed):
        # Mon/Wed/Fri sessions share the Monday 2025-11-24 bucket.
        (_et(2025, 11, 24), _midnight(2025, 11, 24)),
        (_et(2025, 11, 26), _midnight(2025, 11, 24)),
        (_et(2025, 11, 28), _midnight(2025, 11, 24)),
    ],
)
def test_p8_t01_t21_weekly_buckets_open_monday_midnight_et(
    session_ts, expected_monday
):
    assert week_bucket_start(session_ts) == expected_monday
    # The live forming-bar path agrees with the bucket helper.
    assert BarAggregator("SYM", "1 week").period_start(session_ts) == expected_monday


@pytest.mark.parametrize(
    "session_ts,expected_first",
    [
        # February 2025 (28-day month): sessions bucket to 2025-02-01 ET.
        (_et(2025, 2, 3), _midnight(2025, 2, 1)),
        (_et(2025, 2, 28), _midnight(2025, 2, 1)),
        (_et(2025, 3, 3), _midnight(2025, 3, 1)),
        # 30-day month (April 2025) and 31-day month (July 2025).
        (_et(2025, 4, 1), _midnight(2025, 4, 1)),
        (_et(2025, 4, 15), _midnight(2025, 4, 1)),
        (_et(2025, 4, 30), _midnight(2025, 4, 1)),
        (_et(2025, 5, 1), _midnight(2025, 5, 1)),
        (_et(2025, 7, 3), _midnight(2025, 7, 1)),
        (_et(2025, 7, 31), _midnight(2025, 7, 1)),
        (_et(2025, 8, 1), _midnight(2025, 8, 1)),
        # Dec/Jan boundary: months never straddle the year end.
        (_et(2025, 12, 15), _midnight(2025, 12, 1)),
        (_et(2025, 12, 31), _midnight(2025, 12, 1)),
        (_et(2026, 1, 5), _midnight(2026, 1, 1)),
    ],
)
def test_p8_t01_t21_monthly_buckets_open_on_month_boundary_et(
    session_ts, expected_first
):
    assert month_bucket_start(session_ts) == expected_first
    assert BarAggregator("SYM", "1 month").period_start(session_ts) == expected_first


def test_p8_t01_t21_fixed_seconds_month_grid_fails_february():
    # Discrimination check: a nominal 30-day fixed-seconds grid cannot track
    # real month boundaries (February proves it).
    feb = _et(2025, 2, 28)
    fixed_grid = (feb // 2592000) * 2592000
    assert fixed_grid != month_bucket_start(feb)
    assert month_bucket_start(feb) == _midnight(2025, 2, 1)


def _daily_bar(ts, o, h, low, c, v):
    return (ts, o, h, low, c, v)


def test_p8_t01_t21_holiday_week_sessions_only_no_fabrication():
    # Thanksgiving week: only Mon/Wed/Fri sessions exist (Thu closed).
    # Aggregation yields exactly one bucket — no Thursday bar is fabricated.
    events = []
    agg = BarAggregator(
        "SYM", "1 week",
        on_bar_update=lambda bar, is_new: events.append((bar, is_new)),
    )
    sessions = [
        _daily_bar(_et(2025, 11, 24), 100.0, 102.0, 99.0, 101.0, 1000.0),
        _daily_bar(_et(2025, 11, 26), 101.0, 103.0, 100.0, 102.0, 1200.0),
        _daily_bar(_et(2025, 11, 28), 102.0, 104.0, 101.0, 103.0, 800.0),
    ]
    for ts, o, h, low, c, v in sessions:
        agg.push(ts, o, h, low, c, v)
    assert [is_new for _, is_new in events] == [True, False, False]
    bar = agg.current_bar()
    assert bar.ts == _midnight(2025, 11, 24)
    assert bar.open == 100.0
    assert bar.high == 104.0
    assert bar.low == 99.0
    assert bar.close == 103.0
    assert bar.volume == 3000.0


def test_p8_t01_t21_cross_year_week_splits_at_monday():
    events = []
    agg = BarAggregator(
        "SYM", "1 week",
        on_bar_update=lambda bar, is_new: events.append((bar, is_new)),
    )
    agg.push(_et(2025, 12, 30), 10.0, 11.0, 9.0, 10.5, 500.0)
    agg.push(_et(2026, 1, 2), 10.5, 12.0, 10.0, 11.5, 600.0)
    agg.push(_et(2026, 1, 5), 11.5, 13.0, 11.0, 12.5, 700.0)
    assert [is_new for _, is_new in events] == [True, False, True]
    assert events[0][0].ts == _midnight(2025, 12, 29)
    assert events[2][0].ts == _midnight(2026, 1, 5)


def test_p8_t01_t21_monthly_february_sessions_single_bucket():
    events = []
    agg = BarAggregator(
        "SYM", "1 month",
        on_bar_update=lambda bar, is_new: events.append((bar, is_new)),
    )
    sessions = [
        _daily_bar(_et(2025, 2, 3), 50.0, 51.0, 49.0, 50.5, 200.0),
        _daily_bar(_et(2025, 2, 14), 50.5, 52.0, 50.0, 51.5, 300.0),
        _daily_bar(_et(2025, 2, 28), 51.5, 53.0, 51.0, 52.5, 400.0),
    ]
    for ts, o, h, low, c, v in sessions:
        agg.push(ts, o, h, low, c, v)
    assert [is_new for _, is_new in events] == [True, False, False]
    bar = agg.current_bar()
    assert bar.ts == _midnight(2025, 2, 1)
    assert (bar.open, bar.high, bar.low, bar.close, bar.volume) == (
        50.0, 53.0, 49.0, 52.5, 900.0,
    )
    # March opens a new bucket.
    agg.push(_et(2025, 3, 3), 52.5, 54.0, 52.0, 53.5, 100.0)
    assert events[-1][1] is True
    assert events[-1][0].ts == _midnight(2025, 3, 1)


def test_p8_t01_t21_monthly_30_and_31_day_months():
    for sessions, boundary in (
        ([_et(2025, 4, 1), _et(2025, 4, 30)], _midnight(2025, 4, 1)),
        ([_et(2025, 7, 1), _et(2025, 7, 31)], _midnight(2025, 7, 1)),
    ):
        agg = BarAggregator("SYM", "1 month")
        for ts in sessions:
            agg.push(ts, 1.0, 2.0, 0.5, 1.5, 10.0)
        assert agg.current_bar().ts == boundary


def test_p8_t01_t21_existing_fixed_seconds_grid_untouched():
    # The pre-existing grid keeps its values: UTC-epoch for intraday,
    # ET-midnight for "1 day"/"4 hours" — including the new nominal keys,
    # which must never drive bucketing.
    ts = _et(2025, 2, 28)
    assert _period_start(ts, 300, "5 mins") == (ts // 300) * 300
    assert _period_start(ts, 86400, "1 day") == _midnight(2025, 2, 28)
    assert TIMEFRAME_SECONDS["1 week"] == 604800
    assert TIMEFRAME_SECONDS["1 month"] == 2592000
    assert BarAggregator("SYM", "5 mins").period_start(ts) == (ts // 300) * 300
