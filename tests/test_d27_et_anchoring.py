"""D27.8 — ET anchoring for daily/4h aggregation and session VWAP.

``BarAggregator._period_start`` floored to UTC-epoch boundaries, so a live
"1 day" bar spanned 00:00-24:00 UTC (19:00-19:00 ET) — splitting the ET
trading session across two "daily" bars and never ts-matching IBKR's
historical daily series. VWAP's session reset used ``ts // 86400`` (UTC
day), drifting the reset 4-5h away from the ET session boundary.

AC-D27.8: the live forming daily bar ts-matches the historical daily series
(ET session days); VWAP resets at the ET session boundary with ext-hours on.
"""

from __future__ import annotations

from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import BarAggregator
from services.indicator_service import calculate_vwap

EASTERN = ZoneInfo("America/New_York")


def _et_ts(y: int, m: int, d: int, h: int, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _push_5sec(agg: BarAggregator, ts: int) -> None:
    # One 5-second bar is enough to open the period candle.
    agg.push(ts, 100.0, 100.5, 99.5, 100.0, 1000.0)


def test_d27_8_daily_bar_anchors_to_et_midnight():
    """Live daily bar ts == ET midnight, matching the historical daily series."""
    agg = BarAggregator("SPY", "1 day", on_bar_update=None)
    _push_5sec(agg, _et_ts(2026, 10, 12, 10, 0))  # Monday 10:00 ET

    bar = agg.current_bar()
    assert bar is not None
    assert bar.ts == _et_ts(2026, 10, 12, 0, 0), (
        f"daily bar anchored to {bar.ts} "
        f"({datetime.fromtimestamp(bar.ts, tz=EASTERN)}), not ET midnight"
    )


def test_d27_8_four_hour_bar_anchors_to_et_grid():
    """4h grid is 00/04/08/12/16/20 ET (EST date: UTC grid would differ)."""
    agg = BarAggregator("SPY", "4 hours", on_bar_update=None)
    # 2026-01-12 is a winter Monday (EST, UTC-5): 10:00 ET == 15:00 UTC.
    # UTC-anchored flooring gives 12:00 UTC == 07:00 ET; ET gives 08:00 ET.
    _push_5sec(agg, _et_ts(2026, 1, 12, 10, 0))

    bar = agg.current_bar()
    assert bar is not None
    assert bar.ts == _et_ts(2026, 1, 12, 8, 0), (
        f"4h bar anchored to {datetime.fromtimestamp(bar.ts, tz=EASTERN)}, "
        "not the 08:00 ET grid slot"
    )


def test_d27_8_intraday_timeframes_keep_utc_epoch_grid():
    """5-min bars are unaffected (UTC-epoch grid == ET wall grid for 5m)."""
    agg = BarAggregator("SPY", "5 mins", on_bar_update=None)
    _push_5sec(agg, _et_ts(2026, 10, 12, 10, 7))

    bar = agg.current_bar()
    assert bar is not None
    assert bar.ts == _et_ts(2026, 10, 12, 10, 5)


def test_d27_8_vwap_resets_on_et_date_change():
    """VWAP resets when the ET date rolls, even inside one UTC day.

    20:00 ET Oct 12 == 00:00 UTC Oct 13; 01:00 ET Oct 13 == 05:00 UTC Oct 13.
    UTC-day bucketing sees one day (no reset); ET sees Oct 12 -> Oct 13.
    """
    ts = [_et_ts(2026, 10, 12, 20, 0), _et_ts(2026, 10, 13, 1, 0)]
    hs, ls, cs, vs = [100.0, 200.0], [90.0, 190.0], [95.0, 195.0], [10.0, 10.0]

    r = calculate_vwap(hs, ls, cs, vs, timestamps=ts)

    tp2 = (200.0 + 190.0 + 195.0) / 3
    assert abs(r[1] - tp2) < 1e-9, (
        f"VWAP did not reset at the ET session boundary: {r}"
    )


def test_d27_8_vwap_does_not_reset_mid_et_session():
    """No spurious reset for two bars in the same ET session."""
    ts = [_et_ts(2026, 10, 12, 10, 0), _et_ts(2026, 10, 12, 15, 0)]
    hs, ls, cs, vs = [100.0, 100.0], [90.0, 90.0], [95.0, 95.0], [10.0, 10.0]

    r = calculate_vwap(hs, ls, cs, vs, timestamps=ts)

    assert abs(r[1] - 95.0) < 1e-9, f"spurious mid-session reset: {r}"
