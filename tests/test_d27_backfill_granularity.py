"""D27.7 — backfill gap detection at bar-period granularity.

``find_missing_spans`` treated a day with *any* cached bar as present, so a
stranded wave's partial day was marked present forever — a silent, permanent
intraday hole no later load repaired.

AC-D27.7: a stranded partial-day backfill is detected at bar level by a
later load and completed.
"""

from __future__ import annotations

from datetime import datetime

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from services.backfill_service import find_missing_spans

EASTERN = ZoneInfo("America/New_York")

# 2026-10-12 is a Monday; 10-12..10-16 are all trading days.
NOW_TS = int(datetime(2026, 10, 16, 20, 0, tzinfo=EASTERN).timestamp())


def _et_ts(y: int, m: int, d: int, h: int, minute: int) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _morning_bars_5min(y: int, m: int, d: int, last_h: int = 11,
                       last_min: int = 0) -> list[int]:
    """5-min RTH bar timestamps from 9:30 through (last_h:last_min)."""
    out = []
    h, minute = 9, 30
    while (h, minute) <= (last_h, last_min):
        out.append(_et_ts(y, m, d, h, minute))
        minute += 5
        if minute >= 60:
            h += 1
            minute = 0
    return out


def _full_day_bars_5min(y: int, m: int, d: int) -> list[int]:
    return _morning_bars_5min(y, m, d, 15, 55)


def test_d27_7_stranded_partial_day_detected():
    """Oct 15 stranded at 11:00 -> span covers the 11:00-16:00 gap."""
    cached = []
    for day in (12, 13, 14):
        cached += _full_day_bars_5min(2026, 10, day)
    cached += _morning_bars_5min(2026, 10, 15)  # stranded at 11:00
    cached += _full_day_bars_5min(2026, 10, 16)

    spans = find_missing_spans(cached, NOW_TS, "5 mins")

    gap_start = _et_ts(2026, 10, 15, 11, 0)
    gap_end = _et_ts(2026, 10, 15, 16, 0)
    assert any(
        s.start_ts <= gap_start and s.end_ts >= gap_end for s in spans
    ), f"stranded afternoon not covered: {spans}"


def test_d27_7_midday_gap_detected():
    """Bars 9:30-10:00 and 14:00-16:00 -> span covers the 10:00-14:00 hole."""
    cached = _morning_bars_5min(2026, 10, 15, 10, 0)
    # afternoon block 14:00-15:55
    h, minute = 14, 0
    while (h, minute) <= (15, 55):
        cached.append(_et_ts(2026, 10, 15, h, minute))
        minute += 5
        if minute >= 60:
            h += 1
            minute = 0

    spans = find_missing_spans(cached, NOW_TS, "5 mins")

    assert any(
        s.start_ts <= _et_ts(2026, 10, 15, 10, 0)
        and s.end_ts >= _et_ts(2026, 10, 15, 14, 0)
        for s in spans
    ), f"midday hole not covered: {spans}"


def test_d27_7_full_days_produce_no_spans():
    """Complete trailing days -> nothing to repair (no spurious spans)."""
    cached = []
    for day in (12, 13, 14, 15, 16):
        cached += _full_day_bars_5min(2026, 10, day)

    spans = find_missing_spans(cached, NOW_TS, "5 mins")
    assert spans == [], f"spurious spans for complete days: {spans}"


def test_d27_7_empty_day_still_detected_by_day_presence():
    """A day with zero bars is still caught (day-presence path intact)."""
    cached = []
    for day in (12, 13, 14, 16):  # Oct 15 entirely missing
        cached += _full_day_bars_5min(2026, 10, day)

    spans = find_missing_spans(cached, NOW_TS, "5 mins")

    assert any(
        s.start_ts <= _et_ts(2026, 10, 15, 9, 30)
        and s.end_ts >= _et_ts(2026, 10, 15, 16, 0)
        for s in spans
    ), f"empty day not covered: {spans}"


# ---------------------------------------------------------------------------
# D42 / S15 (AC-D16.9) — mode-aware day presence: RTH vs ETH
# ---------------------------------------------------------------------------
def _pre_post_bars_5min(y: int, m: int, d: int) -> list[int]:
    """Bars outside the RTH window but inside the ETH window (pre 05:00, post 19:00)."""
    return [_et_ts(y, m, d, 5, 0), _et_ts(y, m, d, 19, 0)]


def test_d27_7_pre_post_only_day_rth_missing_eth_present():
    """AC-D16.9: a pre/post-only day -> RTH span non-empty, ETH no span.

    ``trailing_days=0`` isolates the mode-aware presence pass from the D27.7
    bar-period pass, so the assertions speak only to presence.
    """
    cached = []
    for day in (12, 13, 14, 16):
        cached += _full_day_bars_5min(2026, 10, day)
    cached += _pre_post_bars_5min(2026, 10, 15)

    rth = find_missing_spans(
        cached, NOW_TS, "5 mins", trailing_days=0, ext_hours=False
    )
    assert any(
        s.start_ts <= _et_ts(2026, 10, 15, 0, 0)
        and s.end_ts >= _et_ts(2026, 10, 16, 0, 0)
        for s in rth
    ), f"pre/post-only day not reported missing under RTH: {rth}"

    eth = find_missing_spans(
        cached, NOW_TS, "5 mins", trailing_days=0, ext_hours=True
    )
    assert eth == [], f"pre/post-only day wrongly missing under ETH: {eth}"


def test_d27_7_rth_only_day_present_in_both_modes():
    """AC-D16.9: an RTH-only day -> present in both modes (no span either way)."""
    cached = []
    for day in (12, 13, 14, 15, 16):
        cached += _full_day_bars_5min(2026, 10, day)

    for ext_hours in (False, True):
        spans = find_missing_spans(
            cached, NOW_TS, "5 mins", trailing_days=0, ext_hours=ext_hours
        )
        assert spans == [], (
            f"RTH-only day wrongly missing (ext_hours={ext_hours}): {spans}"
        )
