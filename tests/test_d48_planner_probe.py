"""P8-T02 (S-P8-3/S-P8-5, DG98): planner verification for the D48 timeframes.

Verification, not code: asserts that the existing planner contracts in
:mod:`services.backfill_service` already satisfy AC-D48.3 for ``1 week``
(``2 Y`` / ``1 week``) and ``1 month`` (``10 Y`` / ``1 month``) — the
P8-T01 config rows — with zero planner source changes:

- a full-span load plans the configured duration in one chunk;
- a span wider than one window chunks by that duration, newest first;
- the AC-D16.8 30-session floor never fires (``period >= 86400``);
- a hole in the middle of cached coverage is detected at bar granularity
  (for daily-or-larger timeframes, day presence *is* bar granularity —
  the bar-level pass is skipped and day presence owns detection).

Qt-free: no QApplication, no TWS connection.
"""

from datetime import datetime, timedelta

import pytest

from config.settings import SESSION_BAR_CAP
from data.bar_aggregator import TIMEFRAME_SECONDS
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import (
    MissingSpan,
    bar_period_seconds,
    find_missing_spans,
    floor_bar_budget,
    plan_requests,
)
from services.market_calendar import is_trading_day

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")

# (timeframe, configured duration, configured bar size) — the P8-T01 rows.
COMBOS = [
    ("1 week", "2 Y", "1 week"),
    ("1 month", "10 Y", "1 month"),
]

Y_SECONDS = 365 * 86_400


def _et_midnight(day):
    return int(datetime(day.year, day.month, day.day, tzinfo=_EASTERN).timestamp())


def _recent_trading_days(count, end=None):
    """Return ``count`` trading days ending at ``end`` (default today), ascending."""
    day = (datetime.now(_EASTERN).date() if end is None else end)
    days = []
    while len(days) < count:
        if is_trading_day(day):
            days.append(day)
        day -= timedelta(days=1)
    return sorted(days)


def _in_session_ts(day, hour=14):
    """A timestamp inside both the RTH and ETH session windows of ``day``."""
    return _et_midnight(day) + hour * 3600


# ---------------------------------------------------------------------------
# Configured duration is planned in one chunk for a full-span load
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe,duration,bar_size", COMBOS)
def test_full_span_plans_configured_duration_in_one_chunk(
    timeframe, duration, bar_size
):
    """A span within one window yields one plan carrying the configured pair."""
    assert TIMEFRAME_CONFIG[timeframe]["duration"] == duration
    assert TIMEFRAME_CONFIG[timeframe]["bar_size"] == bar_size
    now_ts = _et_midnight(datetime.now(_EASTERN).date()) + 14 * 3600
    span_seconds = TIMEFRAME_CONFIG[timeframe]["duration"] and (
        2 * Y_SECONDS if timeframe == "1 week" else 10 * Y_SECONDS
    )
    span = MissingSpan(
        start_ts=now_ts - span_seconds + 86_400, end_ts=now_ts
    )
    plans = plan_requests([span], timeframe)
    assert len(plans) == 1
    assert plans[0].duration == duration
    assert plans[0].bar_size == bar_size
    assert plans[0].span_start_ts == span.start_ts
    assert plans[0].span_end_ts == span.end_ts


# ---------------------------------------------------------------------------
# Wider spans chunk by the configured duration, newest first
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe,duration,bar_size", COMBOS)
def test_wider_span_chunks_by_configured_duration_newest_first(
    timeframe, duration, bar_size
):
    """A span wider than one window splits into ceil(span/duration) chunks."""
    years = 2 if timeframe == "1 week" else 10
    now_ts = _et_midnight(datetime.now(_EASTERN).date()) + 14 * 3600
    extra = 45 * 86_400  # push just past one full window
    span = MissingSpan(
        start_ts=now_ts - (years * Y_SECONDS + extra), end_ts=now_ts
    )
    plans = plan_requests([span], timeframe)
    assert len(plans) == 2
    assert all(p.duration == duration for p in plans)
    assert all(p.bar_size == bar_size for p in plans)
    # Newest chunk first: endDateTime anchors descend.
    assert plans[0].endDateTime >= plans[1].endDateTime


# ---------------------------------------------------------------------------
# The AC-D16.8 30-session floor never fires for weekly/monthly
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe,duration,bar_size", COMBOS)
def test_depth_floor_never_fires_for_weekly_monthly(timeframe, duration, bar_size):
    """Empty cache + min_sessions=30 yields no floor span; flat cap holds."""
    assert bar_period_seconds(timeframe) >= 86_400
    assert TIMEFRAME_SECONDS[timeframe] >= 86_400
    now_ts = _et_midnight(datetime.now(_EASTERN).date()) + 14 * 3600
    assert find_missing_spans([], now_ts, timeframe, min_sessions=30) == []
    for ext_hours in (False, True):
        assert floor_bar_budget(timeframe, ext_hours) == SESSION_BAR_CAP


# ---------------------------------------------------------------------------
# A hole in the middle is detected at bar granularity
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe", ["1 week", "1 month"])
def test_hole_in_middle_detected_at_bar_granularity(timeframe):
    """A missing run of trading days inside cached coverage yields one span."""
    days = _recent_trading_days(15)
    gap = days[5:10]  # five consecutive trading days with no cached bars
    cached_days = days[:5] + days[10:]
    cached_ts = [_in_session_ts(d) for d in cached_days]
    now_ts = _in_session_ts(days[-1])
    spans = find_missing_spans(cached_ts, now_ts, timeframe, min_sessions=30)
    assert len(spans) == 1
    assert spans[0].start_ts == _et_midnight(gap[0])
    assert spans[0].end_ts == _et_midnight(gap[-1] + timedelta(days=1))
