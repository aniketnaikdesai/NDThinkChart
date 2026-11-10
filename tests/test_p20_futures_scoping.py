"""Offscreen futures session-scoping tests (P20-T2 / AC-D59.4 + AC-D59.3).

Covers the task's three automatable tests against a seeded overnight
futures feed, in both toggle modes:

* P20-T2-AC1 — canonical full-session mode: one shared cache, identical
  as-is-ET bar positions in either requested mode, and a cached toggle
  issues zero new historical requests (the planner returns no spans on a
  warm cache, so the wave has nothing to issue).
* P20-T2-AC2 — planner ``is_futures`` flag: equity defaults byte-identical
  (``False``), futures calendar-day presence, Saturday-only closure,
  equity holidays fetched-not-assumed, empty-fetch honest shortfall.
* P20-T2-AC3 — visual scoping: no overnight bar deleted (mode-empty
  vacuous), folded (collapse identity), or shaded (no session bands) for
  futures roots in either mode; equity folding/shading unchanged.

P20-T2-PROBE (owner-waived standalone live probe, D48/D52 precedent,
owner decision 2026-11-09 verbatim "Waive it", P6 live-session-waiver
precedent) is not a suite gate: it is recorded as a passing waiver
assertion below (see ``test_p20_t2_probe_waiver_recorded``) — the probe
is never claimed as run and IND venue risk stays open. The owner runs it
live only if ever needed; no suite depends on it.

No live TWS, no QApplication widget needed — only pure services plus the
LWC view's pure op builders. The shared pytest ``conftest`` isolates a
temp DB for the BarCache legs.
"""

from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta
from types import SimpleNamespace

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.models import Bar
from ibkr.contracts import is_futures_root
from services import chart_model
from services.backfill_service import (
    MissingSpan,
    find_missing_spans,
    futures_trading_days,
    plan_requests,
    present_days,
)
from services.market_calendar import is_trading_day
from services.time_collapse_service import build_collapse_map
from ui.lwc_view import (
    _collapse_for_view,
    _is_futures_symbol,
    drawing_axis,
    logical_indices,
    series_ops,
    session_regions,
)

EASTERN = ZoneInfo("America/New_York")
TIMEFRAME = "5 mins"
PERIOD = 300


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _et_ts(year: int, month: int, day: int,
           hour: int = 0, minute: int = 0) -> int:
    return int(datetime(year, month, day, hour, minute,
                        tzinfo=EASTERN).timestamp())


def _mkbar(symbol: str, ts: int, seq: int) -> Bar:
    base = 5000.0 + seq * 0.25
    return Bar(symbol, TIMEFRAME, ts, base, base + 1.0, base - 1.0,
               base + 0.5, 100.0 + seq)


def _feed(symbol: str, start_ts: int, end_ts: int,
          step: int = PERIOD) -> list:
    """Contiguous step-second bars on ``symbol`` in [start_ts, end_ts]."""
    bars, ts, seq = [], start_ts, 0
    while ts <= end_ts:
        bars.append(_mkbar(symbol, ts, seq))
        ts += step
        seq += 1
    return bars


def _feed_ts(symbol: str, start_ts: int, end_ts: int) -> list:
    return [b.ts for b in _feed(symbol, start_ts, end_ts)]


def _candles_ts(ops: list) -> list:
    for op in ops:
        if op.get("op") == "set_bars" and op.get("series") == "candles":
            return list(op["cols"]["ts"])
    raise AssertionError(f"no candles set_bars op in {ops!r}")


def _canonical(symbol: str, requested_ext_hours: bool) -> bool:
    """The load path's canonical-mode rule (S-P20-4): futures roots always
    run the full-session mode; every other symbol keeps the toggle."""
    return True if is_futures_root(symbol) else requested_ext_hours


# A near-24 h futures session: Tue 2026-10-13 18:00 ET -> Wed 12:00 ET.
# (2026-10-01 is a Thursday, so 10-13 Tue / 10-14 Wed / 10-16 Fri / 10-17
# Sat / 10-18 Sun / 10-19 Mon.)
OVERNIGHT_START = _et_ts(2026, 10, 13, 18, 0)
OVERNIGHT_END = _et_ts(2026, 10, 14, 12, 0)
FULL_DAY_START = _et_ts(2026, 10, 13, 0, 0)  # Tue midnight: no leading edge
NOW_WED = _et_ts(2026, 10, 14, 12, 5)


# A genuine non-trading gap: Fri 2026-10-16 18:00-20:00 ET then
# Mon 2026-10-19 04:00-06:00 ET (the weekend between has no session).
_WEEKEND_GAP_TS = (
    _feed_ts("ES", _et_ts(2026, 10, 16, 18, 0), _et_ts(2026, 10, 16, 20, 0))
    + _feed_ts("ES", _et_ts(2026, 10, 19, 4, 0), _et_ts(2026, 10, 19, 6, 0))
)


# ---------------------------------------------------------------------------
# P20-T2-AC1 — canonical full-session mode
# ---------------------------------------------------------------------------
def test_p20_t2_ac1_futures_roots_are_canonical() -> None:
    """ES/NQ/YM/RTY resolve as futures roots; stocks and indexes do not."""
    for root in ("ES", "NQ", "YM", "RTY"):
        assert is_futures_root(root) is True, root
        assert _canonical(root, False) is True, root
        assert _canonical(root, True) is True, root
    for sym in ("AAPL", "SPY", "SPX"):
        assert is_futures_root(sym) is False, sym
        assert _canonical(sym, False) is False, sym
        assert _canonical(sym, True) is True, sym
    assert _is_futures_symbol("ES") is True
    assert _is_futures_symbol("AAPL") is False


def test_p20_t2_ac1_shared_cache_and_identical_slots() -> None:
    """One shared cache + identical as-is-ET positions in either mode."""
    feed = _feed("ES", FULL_DAY_START, OVERNIGHT_END)
    feed_ts = [b.ts for b in feed]
    BarCache.save_bars(feed, ext_hours=True)  # canonical write, once

    renders = {}
    for requested in (False, True):
        canon = _canonical("ES", requested)
        assert canon is True  # the toggle converges on the full session
        cached = BarCache.get_bars("ES", TIMEFRAME, ext_hours=canon)
        assert [b.ts for b in cached] == feed_ts
        # The overnight bar survives the read in either requested mode.
        assert _et_ts(2026, 10, 14, 2, 0) in [b.ts for b in cached]
        ops = series_ops("candles", cached, TIMEFRAME, canon, symbol="ES")
        renders[requested] = _candles_ts(ops)

    assert renders[False] == renders[True] == feed_ts


def test_p20_t2_ac1_toggle_is_pure_cache_hit() -> None:
    """A warm-cache toggle plans nothing, so the wave issues nothing."""
    feed_ts = _feed_ts("ES", FULL_DAY_START, OVERNIGHT_END)
    BarCache.save_bars(_feed("ES", FULL_DAY_START, OVERNIGHT_END),
                       ext_hours=True)
    for requested in (False, True):
        canon = _canonical("ES", requested)
        spans = find_missing_spans(feed_ts, NOW_WED, TIMEFRAME,
                                   ext_hours=canon, is_futures=True)
        assert spans == [], f"warm futures cache plans {spans}"
        assert plan_requests(spans, TIMEFRAME) == []
    # No spans -> the wave has no plans -> zero new historical reqIds.


def test_p20_t2_ac1_equity_mapped_path_is_red() -> None:
    """Contrast: the old equity mapping drops/reports overnight bars."""
    feed = _feed("AAPL", OVERNIGHT_START, _et_ts(2026, 10, 14, 5, 0))
    feed_ts = [b.ts for b in feed]
    # RTH presence sees neither the Tue-evening nor the Wed-overnight bars.
    rth_spans = find_missing_spans(feed_ts, NOW_WED, TIMEFRAME,
                                   trailing_days=0, ext_hours=False)
    assert rth_spans != []
    # RTH rendering filters the overnight bars out of the plotted set.
    rth_ts = _candles_ts(series_ops("candles", feed, TIMEFRAME, False,
                                    symbol="AAPL"))
    assert len(rth_ts) < len(feed_ts)
    assert _et_ts(2026, 10, 14, 2, 0) not in rth_ts
    # Futures mapping keeps every bar in both requested modes.
    for requested in (False, True):
        fut_ts = _candles_ts(series_ops(
            "candles", feed, TIMEFRAME, _canonical("ES", requested),
            symbol="ES"))
        assert fut_ts == feed_ts


# ---------------------------------------------------------------------------
# P20-T2-AC2 — planner is_futures flag
# ---------------------------------------------------------------------------
def test_p20_t2_ac2_flag_defaults_preserve_equity() -> None:
    """The new flag defaults to False on every extended signature."""
    assert inspect.signature(present_days).parameters["is_futures"].default \
        is False
    assert inspect.signature(
        find_missing_spans).parameters["is_futures"].default is False
    assert inspect.signature(
        build_collapse_map).parameters["is_futures"].default is False
    # Equity mode-aware presence is unchanged (AC-D16.9 / D42).
    pre_post = [_et_ts(2026, 10, 15, 5, 0), _et_ts(2026, 10, 15, 19, 0)]
    assert present_days(pre_post, ext_hours=False) == set()
    assert present_days(pre_post, ext_hours=True) == {date(2026, 10, 15)}
    # Empty cache without a floor still returns [] (T38-T05).
    assert find_missing_spans([], NOW_WED, TIMEFRAME) == []


def test_p20_t2_ac2_calendar_day_presence_saturday_closure() -> None:
    """Any bar on the ET date counts; only Saturday is closed."""
    overnight = _et_ts(2026, 10, 14, 2, 0)  # Wed, deep overnight
    assert present_days([overnight], ext_hours=False,
                        is_futures=True) == {date(2026, 10, 14)}
    assert present_days([overnight], ext_hours=True,
                        is_futures=True) == {date(2026, 10, 14)}
    saturday = _et_ts(2026, 10, 17, 12, 0)
    assert present_days([saturday], is_futures=True) == set()
    sunday = _et_ts(2026, 10, 18, 12, 0)
    assert present_days([sunday], is_futures=True) == {date(2026, 10, 18)}
    # The futures week skips Saturday and nothing else.
    week = futures_trading_days(_et_ts(2026, 10, 12),
                                _et_ts(2026, 10, 19, 12, 0))
    assert date(2026, 10, 17) not in week
    assert date(2026, 10, 18) in week
    assert date(2026, 10, 16) in week  # Friday trades


def test_p20_t2_ac2_saturday_never_reported_missing() -> None:
    """A Fri->Mon gap reports Sunday, never Saturday."""
    fri_ts = _feed_ts("ES", _et_ts(2026, 10, 16, 0, 0),
                      _et_ts(2026, 10, 16, 23, 55))
    now_mon = _et_ts(2026, 10, 19, 12, 0)
    spans = find_missing_spans(fri_ts, now_mon, TIMEFRAME, trailing_days=0,
                               ext_hours=True, is_futures=True)
    assert spans != []
    covered = set()
    for span in spans:
        day = datetime.fromtimestamp(span.start_ts,
                                     tz=EASTERN).date()
        while _et_ts(day.year, day.month, day.day) < span.end_ts:
            covered.add(day)
            day += timedelta(days=1)
    assert date(2026, 10, 18) in covered  # Sunday is fetched
    assert date(2026, 10, 17) not in covered  # Saturday is the closure


def test_p20_t2_ac2_equity_holiday_fetched_not_assumed() -> None:
    """Futures fetch through equity holidays; equities stay closed."""
    holiday = next(
        date(2026, 11, d) for d in range(20, 31)
        if date(2026, 11, d).weekday() < 5
        and not is_trading_day(date(2026, 11, d))
    )
    prev_day = holiday - timedelta(days=1)
    next_day = holiday + timedelta(days=1)
    cached = (
        _feed_ts("ES", _et_ts(prev_day.year, prev_day.month, prev_day.day),
                 _et_ts(prev_day.year, prev_day.month, prev_day.day, 23, 55))
        + _feed_ts("ES", _et_ts(next_day.year, next_day.month, next_day.day),
                   _et_ts(next_day.year, next_day.month, next_day.day, 12, 0))
    )
    now = _et_ts(next_day.year, next_day.month, next_day.day, 12, 5)
    fut_spans = find_missing_spans(cached, now, TIMEFRAME, trailing_days=0,
                                   ext_hours=True, is_futures=True)
    assert any(s.start_ts <= _et_ts(holiday.year, holiday.month, holiday.day)
               and s.end_ts >= _et_ts(holiday.year, holiday.month,
                                      holiday.day) + 86400
               for s in fut_spans), f"holiday not fetched: {fut_spans}"
    eq_spans = find_missing_spans(cached, now, TIMEFRAME, trailing_days=0,
                                  ext_hours=True)
    assert eq_spans == []  # genuine equity closure, correctly silent
    # ... while a bar on the holiday counts as futures presence.
    assert present_days([_et_ts(holiday.year, holiday.month, holiday.day,
                                12, 0)],
                        is_futures=True) == {holiday}


def test_p20_t2_ac2_empty_fetch_is_honest_shortfall() -> None:
    """Empty futures cache + floor -> a fetch span, never silence."""
    spans = find_missing_spans([], NOW_WED, TIMEFRAME, is_futures=True,
                               min_sessions=2)
    assert len(spans) == 1
    # Futures week: Wed session back 2 -> Monday 2026-10-12.
    assert spans[0].start_ts == _et_ts(2026, 10, 12)
    assert spans[0].end_ts == NOW_WED
    # The completed-wave shortfall names the unfetched day (AC-D16.4),
    # using the futures enumeration for futures roots.
    import ui.main_window as main_window_mod

    holiday = date(2026, 11, 26)
    assert not is_trading_day(holiday)
    span = MissingSpan(_et_ts(2026, 11, 25), _et_ts(2026, 11, 27, 12, 0))
    fut_session = SimpleNamespace(symbol="ES",
                                  _backfill_missing_spans=[span],
                                  _wave_extended_hours=True)
    fut_missing = main_window_mod.MainWindow._missing_backfill_trading_days(
        None, fut_session, [])
    assert holiday in fut_missing  # fetched-not-assumed: named, not silent
    eq_session = SimpleNamespace(symbol="AAPL",
                                 _backfill_missing_spans=[span],
                                 _wave_extended_hours=True)
    eq_missing = main_window_mod.MainWindow._missing_backfill_trading_days(
        None, eq_session, [])
    assert holiday not in eq_missing  # genuine equity closure stays silent


# ---------------------------------------------------------------------------
# P20-T2-AC3 — collapse / band scoping
# ---------------------------------------------------------------------------
def test_p20_t2_ac3_collapse_identity_for_futures() -> None:
    """Overnight futures bars are never folded; equities still fold."""
    feed_ts = _feed_ts("ES", OVERNIGHT_START, _et_ts(2026, 10, 14, 5, 0))
    for requested in (False, True):
        cmap = build_collapse_map(feed_ts, TIMEFRAME, requested,
                                  is_futures=True)
        assert cmap.is_identity is True
        assert cmap.x_values == feed_ts
    equity = build_collapse_map(_WEEKEND_GAP_TS, TIMEFRAME, True)
    assert equity.is_identity is False  # the weekend gap collapses
    assert max(equity.x_values) - min(equity.x_values) < max(
        _WEEKEND_GAP_TS) - min(_WEEKEND_GAP_TS)
    weekend_fut = build_collapse_map(_WEEKEND_GAP_TS, TIMEFRAME, True,
                                     is_futures=True)
    assert weekend_fut.is_identity is True  # futures never fold, even weekends
    assert weekend_fut.x_values == _WEEKEND_GAP_TS
    assert _collapse_for_view(feed_ts, TIMEFRAME, True,
                              "ES").is_identity is True
    # Control: the equity leg delegates byte-identically to the shared
    # chart-model authority (S-P20-5 "suppressed, never remodeled"). This
    # contiguous overnight feed has no foldable gap between consecutive
    # 5-min bars, so both the direct and the routed equity maps are
    # identity here; the genuine equity-folding control is the weekend
    # gap routed through the view (it folds, as direct did above).
    eq_direct = chart_model.collapse_for_bars(feed_ts, TIMEFRAME, True)
    eq_routed = _collapse_for_view(feed_ts, TIMEFRAME, True, "AAPL")
    assert eq_routed.is_identity is eq_direct.is_identity is True
    assert eq_routed.x_values == eq_direct.x_values
    assert _collapse_for_view(
        _WEEKEND_GAP_TS, TIMEFRAME, True, "AAPL").is_identity is False


def test_p20_t2_ac3_bands_suppressed_for_futures() -> None:
    """No D1 pre/post bands for futures roots; equities keep shading."""
    day_feed = _feed("AAPL", _et_ts(2026, 10, 13, 6, 0),
                     _et_ts(2026, 10, 13, 19, 0))
    plotted = list(day_feed)
    equity_regions = session_regions(day_feed, plotted, TIMEFRAME, True,
                                     symbol="AAPL")
    assert equity_regions != []  # control: equity shading unchanged
    assert session_regions(day_feed, plotted, TIMEFRAME, True) != []
    for requested in (False, True):
        assert session_regions(day_feed, plotted, TIMEFRAME, requested,
                               symbol="ES") == []
    # The overnight range itself is never shaded for futures roots.
    night_feed = _feed("ES", OVERNIGHT_START, _et_ts(2026, 10, 14, 5, 0))
    assert session_regions(night_feed, list(night_feed), TIMEFRAME, True,
                           symbol="ES") == []


def test_p20_t2_ac3_overnight_bars_survive_both_modes() -> None:
    """No deletion, no folding, no shading, no whitespace in either mode."""
    feed = _feed("ES", OVERNIGHT_START, _et_ts(2026, 10, 14, 5, 0))
    feed_ts = [b.ts for b in feed]
    for requested in (False, True):
        canon = _canonical("ES", requested)
        ops = series_ops("candles", feed, TIMEFRAME, canon, symbol="ES")
        assert _candles_ts(ops) == feed_ts  # every bar plotted, as-is in ET
        idx = logical_indices(feed, TIMEFRAME, canon, symbol="ES")
        assert idx == list(range(len(feed)))  # identity steps, no folding
        _xs, _inds, cmap = drawing_axis(feed, TIMEFRAME, canon,
                                        symbol="ES")
        assert cmap.is_identity is True
        assert session_regions(feed, list(feed), TIMEFRAME, canon,
                               symbol="ES") == []
    # Equity control on a genuine non-trading gap: the weekend folds.
    eq_cmap = build_collapse_map(_WEEKEND_GAP_TS, TIMEFRAME, True)
    assert eq_cmap.is_identity is False  # folded, shading path unchanged


def test_p20_t2_ac3_mode_empty_vacuous_for_futures() -> None:
    """The mode flag is ignored by futures presence (nothing to delete)."""
    feed_ts = _feed_ts("ES", OVERNIGHT_START, _et_ts(2026, 10, 14, 5, 0))
    assert present_days(feed_ts, ext_hours=False, is_futures=True) == \
        present_days(feed_ts, ext_hours=True, is_futures=True)
    assert find_missing_spans(feed_ts, NOW_WED, TIMEFRAME, trailing_days=0,
                              ext_hours=False, is_futures=True) == \
        find_missing_spans(feed_ts, NOW_WED, TIMEFRAME, trailing_days=0,
                           ext_hours=True, is_futures=True)


# ---------------------------------------------------------------------------
# P20-T2-PROBE — waived-documented step (owner decision 2026-11-09 verbatim
# "Waive it"; P6 live-session-waiver precedent). NOT run: the standalone
# live probe (SPX/NDX/DJI/RUT + ES on live TWS, D48/D52 precedent) was never
# executed and is never claimed as run — this test asserts the waiver
# record and the no-claim invariant on automated evidence only, with no
# live-TWS suite dependency. IND venue risk stays explicitly open.
# ---------------------------------------------------------------------------
P20_T2_PROBE_WAIVER = {
    "owner_decision": "Waive it",
    "owner_date": "2026-11-09",
    "precedent": "P6 live-session-waiver",
    "probe_claimed_run": False,
    "ind_venue_risk": "open",
}


def test_p20_t2_probe_waiver_recorded() -> None:
    """P20-T2-PROBE — owner-waived standalone live probe: assert the waiver.

    Passes on the waiver record alone: owner verbatim "Waive it" (2026-11-09,
    P6 live-session-waiver precedent cited); the standalone live probe
    (SPX/NDX/DJI/RUT IND rows accepted, ES price + as-is-ET time) is
    explicitly NOT claimed as run; IND venue risk stays open; no live TWS,
    no suite dependency — finalization rests on the automated P20-T2-AC1 /
    AC2 / AC3 set plus the honest-shortfall backstop.
    """
    assert P20_T2_PROBE_WAIVER["owner_decision"] == "Waive it"
    assert P20_T2_PROBE_WAIVER["owner_date"] == "2026-11-09"
    assert P20_T2_PROBE_WAIVER["precedent"] == "P6 live-session-waiver"
    assert P20_T2_PROBE_WAIVER["probe_claimed_run"] is False
    assert P20_T2_PROBE_WAIVER["ind_venue_risk"] == "open"
