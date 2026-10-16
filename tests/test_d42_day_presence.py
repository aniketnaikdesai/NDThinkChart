"""AC-D16.9 (D42) — mode-aware day presence: pre/post-only vs RTH-only days.

The exported presence predicate (``services.backfill_service.present_days``) and
its integration into :func:`find_missing_spans` decide a trading day *present*
against the **current mode's** session window — RTH ``09:30-16:00 ET``
(``ext_hours=False``) or ETH ``04:00-20:00 ET`` (``ext_hours=True``) — never the
bare calendar day's presence in the cache. This suite asserts the three
AC-D16.9 measurables:

* **(a)** a day whose cached bars are all *outside* RTH (only pre/post bars)
  yields a **non-empty RTH span** covering that day's RTH window;
* **(b)** that same seed's ``ext_hours=True`` call reports the day **present**
  (no missing span for it — its bars lie inside the ETH window);
* **(c)** a day with **only RTH bars** is reported present by **both** the RTH
  and the ETH call (RTH ``09:30-16:00`` lies inside ``04:00-20:00``), i.e. the
  two modes do not cross-contaminate.

Bar timestamps are period **starts** (``data/bar_aggregator.py``), so the window
membership test applies to a bar's start timestamp.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from services.backfill_service import find_missing_spans, present_days
from services.market_calendar import is_trading_day

_ET = ZoneInfo("America/New_York")

_TIMEFRAME = "5 mins"

# A trading day far enough behind *now* that D27.7's trailing bar-granularity
# pass (which only inspects the trailing 5 trading days) never touches it — so
# these assertions isolate the day-presence pass this criterion is about. The
# gap also gives ``find_missing_spans`` genuinely-uncached later days, proving
# the calls actually ran over the cache rather than bailing out early.
_SEED_DAY = date(2024, 5, 6)  # Monday, a trading day
_NOW_DAY = date(2024, 6, 3)  # Monday, ~19 trading days later


def _ts(day: date, hour: int, minute: int = 0) -> int:
    """Unix seconds for ``hour:minute`` ET on ``day``."""
    return int(
        datetime(day.year, day.month, day.day, hour, minute, tzinfo=_ET).timestamp()
    )


def _day_bounds(day: date) -> tuple[int, int]:
    """ET-midnight bounds ``[start, next_midnight)`` for ``day``."""
    nxt = day + timedelta(days=1)
    return _ts(day, 0, 0), _ts(nxt, 0, 0)


def _covers(span, day: date) -> bool:
    """True when ``span`` overlaps ``day``'s ET calendar day."""
    start, end = _day_bounds(day)
    return span.start_ts < end and span.end_ts > start


def _rth_window(day: date) -> tuple[int, int]:
    return _ts(day, 9, 30), _ts(day, 16, 0)


_NOW_TS = _ts(_NOW_DAY, 12, 0)
# Only pre/post (extended-hours) bars: outside RTH (09:30-16:00) but inside the
# ETH window (04:00-20:00).
_PREPOST_BARS = [_ts(_SEED_DAY, 8, 0), _ts(_SEED_DAY, 17, 0)]
# Only RTH bars: inside RTH, and therefore inside the ETH window too.
_RTH_BARS = [_ts(_SEED_DAY, 9, 45), _ts(_SEED_DAY, 15, 45)]


# ---------------------------------------------------------------------------
# (a)/(b) — a pre/post-only day is RTH-missing but ETH-present
# ---------------------------------------------------------------------------
def test_t11_prepost_only_day_rth_missing_eth_present():
    """P2-T20-T11 / AC-D16.9 (a)+(b): pre/post-only day → RTH span, no ETH span."""
    assert is_trading_day(_SEED_DAY), "seed day must be a trading day"

    rth = find_missing_spans(_PREPOST_BARS, _NOW_TS, _TIMEFRAME, ext_hours=False)
    assert rth, "pre/post-only day must yield a non-empty RTH span (RED pre-fix)"
    rth_cover = [s for s in rth if _covers(s, _SEED_DAY)]
    assert rth_cover, "the RTH span must cover the pre/post-only day"
    rth_start, rth_end = _rth_window(_SEED_DAY)
    assert any(
        s.start_ts <= rth_start and s.end_ts >= rth_end for s in rth_cover
    ), "the RTH span must cover the day's RTH window"

    eth = find_missing_spans(_PREPOST_BARS, _NOW_TS, _TIMEFRAME, ext_hours=True)
    # The ETH call still runs over the cache (the later uncached days are
    # genuinely missing), so it is non-empty — but none of its spans is *for*
    # the seed day: its pre/post bars lie inside the ETH window.
    assert not any(
        _covers(s, _SEED_DAY) for s in eth
    ), "the same seed's ETH call must report the day present (no span for it)"

    assert _SEED_DAY in present_days(_PREPOST_BARS, ext_hours=True)
    assert _SEED_DAY not in present_days(_PREPOST_BARS, ext_hours=False)


# ---------------------------------------------------------------------------
# (c) — an RTH-only day is present in both modes
# ---------------------------------------------------------------------------
def test_t21_rth_only_day_present_in_both_modes():
    """P2-T20-T21 / AC-D16.9 (c): RTH-only day → present under RTH *and* ETH."""
    assert is_trading_day(_SEED_DAY), "seed day must be a trading day"

    rth = find_missing_spans(_RTH_BARS, _NOW_TS, _TIMEFRAME, ext_hours=False)
    eth = find_missing_spans(_RTH_BARS, _NOW_TS, _TIMEFRAME, ext_hours=True)

    assert not any(_covers(s, _SEED_DAY) for s in rth), "RTH call: day is present"
    assert not any(_covers(s, _SEED_DAY) for s in eth), "ETH call: day is present"

    assert _SEED_DAY in present_days(_RTH_BARS, ext_hours=False)
    assert _SEED_DAY in present_days(_RTH_BARS, ext_hours=True)


# ---------------------------------------------------------------------------
# AC2 — the two directions of the window-membership predicate
# ---------------------------------------------------------------------------
def test_t31_presence_is_window_based_no_cross_contamination():
    """P2-T20-T31 / AC2: pre/post bars are not RTH coverage; RTH bars are ETH."""
    # Direction 1: pre/post-only bars are ETH coverage but *not* RTH coverage.
    assert _SEED_DAY not in present_days(_PREPOST_BARS, ext_hours=False)
    assert _SEED_DAY in present_days(_PREPOST_BARS, ext_hours=True)

    # Direction 2: RTH-only bars are RTH coverage *and* ETH coverage.
    assert _SEED_DAY in present_days(_RTH_BARS, ext_hours=False)
    assert _SEED_DAY in present_days(_RTH_BARS, ext_hours=True)

    # The predicate, not the cache key: the same cached day is judged present or
    # missing purely by which session window the mode selects.
    assert present_days(_PREPOST_BARS, ext_hours=False) != present_days(
        _PREPOST_BARS, ext_hours=True
    )
    assert present_days(_RTH_BARS, ext_hours=False) == present_days(
        _RTH_BARS, ext_hours=True
    )
