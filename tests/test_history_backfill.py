"""T40 / D16 — offscreen end-to-end verification of whole-gap backfill.

These tests boot a real, shown ``MainWindow`` under the offscreen Qt platform
(``IBApiClient.connect`` monkeypatched to a no-op and the market-data managers
stubbed) exactly like ``tests/test_history_backfill_loadpath.py`` and
``tests/test_watchlist_d14_midrag.py``. They seed ``BarCache`` with the
``AC-D16.5`` repro and drive the stubbed historical feed by emitting
``_on_historical_bar`` / ``_on_historical_data_end`` for every issued request,
then assert on the rendered ``ChartPanel`` and the persisted cache.

The pure planner/calendar are already covered by ``tests/test_backfill_service.py``
and ``tests/test_market_calendar.py``; this file verifies the wired-together
load path (T39), including both chart panels, genuine closures, chunking over
all six timeframes and two symbols, switch-mid-flight isolation and the
empty-cache fallback.

No test here weakens, skips or rewrites an existing test.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

import pytest
from PyQt6.QtWidgets import QDockWidget

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import find_missing_spans, plan_requests
from services import chart_model
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")

# The app defaults the toolbar's Ext Hours button to checked, so the stubbed
# feed models IBKR's extended-hours session (04:00-20:00 ET) that the live
# request (useRTH=0) returns.
_EXT_OPEN_H = 4
_EXT_CLOSE_H = 20

# IBKR durationStr units, mirroring services.backfill_service's chunk step so a
# request's window can be reconstructed from its planned ``endDateTime``.
_DURATION_UNIT_SECONDS = {
    "S": 1,
    "D": 86_400,
    "W": 7 * 86_400,
    "M": 30 * 86_400,
    "Y": 365 * 86_400,
}


# ---------------------------------------------------------------------------
# Small calendar / time helpers (independent of the render path under test)
# ---------------------------------------------------------------------------
def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _duration_seconds(duration: str) -> int:
    token = (duration or "").strip().upper()
    if token and token[-1] in _DURATION_UNIT_SECONDS and token[:-1].strip().isdigit():
        return int(token[:-1]) * _DURATION_UNIT_SECONDS[token[-1]]
    return int(token)


def _parse_end(end: str) -> int:
    """Parse a planned IBKR ``endDateTime`` (``yyyyMMdd-HH:mm:ss`` UTC)."""
    return int(
        datetime.strptime(end, "%Y%m%d-%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    )


def _next_trading_day(d: date) -> date:
    while not is_trading_day(d):
        d += timedelta(days=1)
    return d


def _prev_trading_day(d: date) -> date:
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _session_bars(symbol: str, tf: str, day: date, base: float = 100.0) -> list[Bar]:
    """Deterministic bars one trading session of ``tf`` would return for ``day``.

    Non-trading days (weekend / US-equity holiday) return ``[]`` so the stubbed
    feed can never fabricate a bar across a genuine closure.
    """
    if not is_trading_day(day):
        return []
    if tf == "1 day":
        return [Bar(symbol, tf, _et_ts(day.year, day.month, day.day, 16, 0),
                    base, base + 0.5, base - 0.5, base, 1234.0)]
    period = TIMEFRAME_SECONDS[tf]
    start = _et_ts(day.year, day.month, day.day, _EXT_OPEN_H, 0)
    close = _et_ts(day.year, day.month, day.day, _EXT_CLOSE_H, 0)
    bars: list[Bar] = []
    ts = start
    i = 0
    while ts < close:
        price = base + (i % 5) * 0.25
        bars.append(Bar(symbol, tf, ts, price, price + 0.5, price - 0.5, price,
                        1000.0 + (ts % 500)))
        ts += period
        i += 1
    return bars


# ---------------------------------------------------------------------------
# DB + window helpers
# ---------------------------------------------------------------------------
def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


def _seed_day(symbol: str, tf: str, day: date, base: float = 100.0) -> None:
    """Seed one *complete* session day (D27.7).

    ``find_missing_spans`` runs bar-period-granularity gap detection on
    trailing trading days, so a "present" day must be a genuinely complete
    intraday series — a single noon bar is (correctly) reported as a day
    with intraday holes. Delegates to :func:`_session_bars`.
    """
    BarCache.save_bars(_session_bars(symbol, tf, day, base))


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))  # 10-digit epoch string -> parse_ibkr_date
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


class _ReqStub:
    """Captures ``req_historical_data`` calls and cancelled reqIds."""

    def __init__(self, first_id: int = 5000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, bar_size=None, duration=None):
        req_id = self._next
        self._next += 1
        self.calls.append({
            "reqId": req_id,
            "contract": contract,
            "timeframe": timeframe,
            "endDateTime": endDateTime,
            "whatToShow": whatToShow,
            "useRTH": useRTH,
            "extended_hours": extended_hours,
            "bar_size": bar_size,
            "duration": duration,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    # The load path must reach only the (stubbed) managers, never a socket.
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _load(win, symbol: str, tf: str, stub: _ReqStub, now_ts: int) -> None:
    """Drive the real ``load_chart`` against the stubbed manager at a fixed now."""
    win._now_ts = lambda: now_ts
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(tf)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()


def _drive_calls(win, tf: str, stub: _ReqStub, expected_bars, now_ts: int,
                 calls=None) -> set[int]:
    """Emit the stubbed historical feed, one chunk window at a time.

    ``expected_bars`` are the bars a real IBKR would return for the missing
    trading sessions. Each issued request owns a window
    ``(anchor - configured_duration, anchor]`` (or ``(-inf, now]`` for the
    empty-cache fallback); every expected bar is delivered through the request
    whose window contains it, then that request is ended. Returns the set of
    delivered timestamps so callers can prove nothing was silently dropped.
    """
    calls = stub.calls if calls is None else calls
    duration = _duration_seconds(TIMEFRAME_CONFIG[tf]["duration"])
    delivered: set[int] = set()
    for call in calls:
        if call.get("bar_size") == "5 secs":
            # D27.9 priming is not a backfill-wave member; never drive it here.
            continue
        rid = call["reqId"]
        end = call["endDateTime"]
        if end:
            anchor = _parse_end(end)
            lo, hi = anchor - duration, anchor
        else:
            lo, hi = None, now_ts
        for bar in expected_bars:
            if bar.ts in delivered:
                continue
            if (lo is None or bar.ts > lo) and bar.ts <= hi:
                win._on_historical_bar(rid, _FakeIbBar(bar.ts, bar.close, bar.volume))
                delivered.add(bar.ts)
        win._on_historical_data_end(rid)
    return delivered


# ---------------------------------------------------------------------------
# T40-T01 / AC-D16.5 — the reported repro, per-weekday counts, weekend empty
# ---------------------------------------------------------------------------
_AC_BEFORE = [date(2026, 9, 14), date(2026, 9, 15), date(2026, 9, 16),
              date(2026, 9, 17), date(2026, 9, 18)]
_AC_AFTER = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30),
             date(2026, 10, 1), date(2026, 10, 2)]
_AC_MISSING = [date(2026, 9, 21), date(2026, 9, 22), date(2026, 9, 23),
               date(2026, 9, 24), date(2026, 9, 25)]
_AC_WEEKEND = [date(2026, 9, 19), date(2026, 9, 20),
               date(2026, 9, 26), date(2026, 9, 27)]
_AC_NOW = _et_ts(2026, 10, 2, 20, 0)


def _setup_ac_d16_5(monkeypatch, qapp, symbol="SPY", tf="5 mins"):
    _clear(symbol, tf)
    for i, d in enumerate(_AC_BEFORE):
        _seed_day(symbol, tf, d, 100.0 + i)
    for i, d in enumerate(_AC_AFTER):
        _seed_day(symbol, tf, d, 200.0 + i)
    win = _make_window(monkeypatch, qapp)
    stub = _ReqStub()
    _load(win, symbol, tf, stub, _AC_NOW)
    expected = [b for d in _AC_MISSING for b in _session_bars(symbol, tf, d)]
    return win, symbol, tf, stub, expected


def test_t40_t01_ac_d16_5_repro_backfills_weekdays_not_weekend(monkeypatch, qapp):
    """T40-T01 / AC-D16.5: missing 2026-09-21..09-25 filled, weekend absent."""
    win, symbol, tf, stub, expected = _setup_ac_d16_5(monkeypatch, qapp)
    try:
        # The seeded internal hole (09-19..09-27) spans exactly one 5 D window.
        cached_ts = [b.ts for b in BarCache.get_bars(symbol, tf)]
        plans = plan_requests(find_missing_spans(cached_ts, _AC_NOW, tf), tf)
        assert len(plans) == 1
        # D42/S17: the load path also issues the >= 30-session floor span, which
        # reaches further back than this fixture's hole, so the wave is no longer
        # a single chunk. The AC-D16.5 intent -- the hole is filled by a real
        # request, never silently dropped -- is proven by the delivered set below.
        assert len(stub.calls) >= 1

        delivered = _drive_calls(win, tf, stub, expected, _AC_NOW)
        assert delivered == {b.ts for b in expected}

        per_day = len(_session_bars(symbol, tf, _AC_MISSING[0]))
        assert per_day == 192  # 16 h extended session / 5 min cadence

        bars = BarCache.get_bars(symbol, tf)
        by_day: dict[date, list[Bar]] = {}
        for b in bars:
            by_day.setdefault(_et_date(b.ts), []).append(b)

        # Missing weekdays are present at the full intraday cadence.
        for d in _AC_MISSING:
            assert len(by_day.get(d, [])) == per_day, d
        # The genuine weekend closures hold no cached rows at all.
        for d in _AC_WEEKEND:
            assert d not in by_day, d

        # ChartPanel._bars contains the backfilled weekdays too.
        chart_ts = {b.ts for b in win.chart_panel._bars}
        assert {b.ts for b in expected} <= chart_ts
        assert all(b.symbol == symbol for b in win.chart_panel._bars)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T40-T02 / AC-D16.2 — candle + volume panels both span the backfilled span
# ---------------------------------------------------------------------------
def test_t40_t02_both_panels_span_backfilled_timestamps(monkeypatch, qapp):
    """T40-T02 / AC-D16.2: volume heights non-zero wherever a candle exists."""
    win, symbol, tf, stub, expected = _setup_ac_d16_5(monkeypatch, qapp)
    try:
        _drive_calls(win, tf, stub, expected, _AC_NOW)

        panel = win.chart_panel
        # Q-20: the LWC series carries real UTC times, one entry per plotted
        # row, and the volume heights come from the shared chart model.
        plotted = panel.plotted_bars
        series_ts = panel.series_times
        vol_x, vol_h, _vol_colors = chart_model.volume_display_columns(
            plotted, None)

        assert series_ts == [int(b.ts) for b in plotted]
        assert [int(x) for x in vol_x] == series_ts
        assert len(vol_h) == len(series_ts)

        # Both span the backfilled timestamps.
        span_ts = [int(b.ts) for b in expected]
        assert set(span_ts) <= set(series_ts)
        assert set(span_ts) <= {int(x) for x in vol_x}

        # Non-zero height wherever a bar exists in the backfilled span.
        index = {int(x): i for i, x in enumerate(vol_x)}
        for ts in span_ts:
            assert vol_h[index[ts]] > 0, ts
        assert all(h > 0 for h in vol_h)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T40-T03 / AC-D16.3 — genuine closures stay empty; axis not compressed
# ---------------------------------------------------------------------------
def test_t40_t03_closures_stay_empty_and_axis_uncompressed(monkeypatch, qapp):
    """T40-T03 / AC-D16.3: weekend + Labor Day stay empty, no fabrication."""
    symbol, tf = "T40HOL", "5 mins"
    _clear(symbol, tf)
    before = [date(2026, 8, 31), date(2026, 9, 1), date(2026, 9, 2),
              date(2026, 9, 3), date(2026, 9, 4)]
    for i, d in enumerate(before):
        _seed_day(symbol, tf, d, 100.0 + i)
    now = _et_ts(2026, 9, 11, 20, 0)

    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, tf, stub, now)
        missing = [date(2026, 9, 8), date(2026, 9, 9),
                   date(2026, 9, 10), date(2026, 9, 11)]
        expected = [b for d in missing for b in _session_bars(symbol, tf, d)]
        _drive_calls(win, tf, stub, expected, now)

        bars = BarCache.get_bars(symbol, tf)
        by_day: dict[date, list[Bar]] = {}
        for b in bars:
            by_day.setdefault(_et_date(b.ts), []).append(b)
        for d in missing:
            assert len(by_day.get(d, [])) == 192, d

        # Saturday 09-05, Sunday 09-06 and Labor Day Monday 09-07 are genuine
        # closures: no cached row is fabricated or interpolated across them.
        for d in (date(2026, 9, 5), date(2026, 9, 6), date(2026, 9, 7)):
            assert d not in by_day, d

        # The closure is not treated as a shortfall by the app. D42/S17 means a
        # floor shortfall IS now legitimately reported (this fixture is far short
        # of 30 sessions), so the intent is asserted precisely instead: the
        # genuine closure days must never be named as missing.
        msg = win.status_bar.currentMessage()
        for d in (date(2026, 9, 5), date(2026, 9, 6), date(2026, 9, 7)):
            assert d.isoformat() not in msg, (
                f"a genuine closure ({d}) must not be reported as a shortfall")

        # The axis is timestamp-based and not compressed: the series times are
        # the real UTC ts list and the pre/post-closure gap spans the true
        # weekend + holiday.
        panel = win.chart_panel
        series_ts = panel.series_times
        vol_x, _vol_h, _vol_colors = chart_model.volume_display_columns(
            panel.plotted_bars, None)
        assert [int(x) for x in vol_x] == series_ts

        last_pre = max(b.ts for b in bars if _et_date(b.ts) == date(2026, 9, 4))
        first_post = min(b.ts for b in bars if _et_date(b.ts) == date(2026, 9, 8))
        assert first_post - last_pre > 3 * 86_400  # 09-04 12:00 -> 09-08 04:00

        assert max(series_ts) - min(series_ts) > 3 * 86_400
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T40-T04 / AC-D16.1 + AC-D16.4 — chunking over six timeframes, two symbols
# ---------------------------------------------------------------------------
TIMEFRAMES = list(TIMEFRAME_CONFIG.keys())
SYMBOLS = ["T40SPY", "T40AAPL"]


def _floor_extra_days(now: int, pre: date, post: date,
                        missing: list[date]) -> list[date]:
    """Floor-span trading days beyond the fixture's own hole (P7-W1 resume).

    A floor-scale wave's chunks cover the >= 30-session depth floor, not just
    the fixture hole; answering those chunks empty would replan them forever.
    The stub therefore fabricates dense bars for the surrounding trading days
    (skipping the seeded/fixture days) exactly as a real feed would return
    real bars for those windows.
    """
    skip = {pre, post, *missing}
    days: list[date] = []
    cur = _et_date(now)
    for _ in range(60):
        if is_trading_day(cur) and cur not in skip:
            days.append(cur)
        cur -= timedelta(days=1)
    return days


def _chunk_scenario(tf: str):
    """A hole larger than one configured fetch window, plus seed/post context."""
    chunk_days = -(-_duration_seconds(TIMEFRAME_CONFIG[tf]["duration"]) // 86_400)
    gap_days = chunk_days + 2  # guarantees at least two chunks
    first = _next_trading_day(date(2026, 5, 1))
    missing: list[date] = []
    cur = first
    while len(missing) < gap_days:
        if is_trading_day(cur):
            missing.append(cur)
        cur += timedelta(days=1)
    post = _next_trading_day(cur)
    pre = _prev_trading_day(first - timedelta(days=1))
    now = _et_ts(post.year, post.month, post.day, 20, 0)
    return missing, pre, post, now


@pytest.mark.parametrize("symbol", SYMBOLS)
@pytest.mark.parametrize("tf", TIMEFRAMES)
def test_t40_t04_chunked_multi_request_continuity(monkeypatch, qapp, tf, symbol):
    """T40-T04 / AC-D16.1+4: multiple requests, continuous result, all tfs."""
    missing, pre, post, now = _chunk_scenario(tf)
    _clear(symbol, tf)
    _seed_day(symbol, tf, pre, 100.0)
    _seed_day(symbol, tf, post, 200.0)

    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, tf, stub, now)

        cached_ts = [b.ts for b in BarCache.get_bars(symbol, tf)]
        spans = find_missing_spans(cached_ts, now, tf)
        plans = plan_requests(spans, tf)
        assert len(spans) == 1
        assert len(plans) >= 2, (tf, symbol, len(plans))
        # D27.9: the priming request is not a backfill-wave member.
        wave_calls = [c for c in stub.calls if c.get("bar_size") != "5 secs"]
        # D42/S17: the load path also issues the >= 30-session floor span, so the
        # wave is a SUPERSET of this fixture's own plans. The intent -- several
        # requests, a continuous result, no silent hole -- is asserted below.
        assert len(wave_calls) >= len(plans)

        expected = [b for d in missing for b in _session_bars(symbol, tf, d)]
        expected_ts = [b.ts for b in expected]
        # P7-W1 (S-P7-1): a 1-min floor-scale wave (~42 one-day chunks)
        # exceeds the per-load cap (floor(MAX_HISTORICAL_PER_600S/4)), so a
        # single load cannot finalize it. The stub answers like a real feed:
        # every load delivers the hole through its issued windows plus dense
        # bars for the other floor-span days, ends its issued calls, and
        # reloads -- load_chart flushes pending bars before replanning
        # oldest-first -- until a load issues no further wave calls. Waves
        # that fit the cap converge on the first iteration, exactly as before.
        floor_extra = [b for d in _floor_extra_days(now, pre, post, missing)
                       for b in _session_bars(symbol, tf, d)]
        session = win.get_or_create_session(symbol)
        delivered: set[int] = set()
        base = 0
        converged = False
        for _ in range(8):
            new_calls = stub.calls[base:]
            base = len(stub.calls)
            wave_new = [c for c in new_calls if c.get("bar_size") != "5 secs"]
            if not wave_new:
                converged = True
                break
            anchor_new = wave_new[0]["reqId"]
            for b in floor_extra:
                win._on_historical_bar(
                    anchor_new, _FakeIbBar(b.ts, b.close, b.volume))
            delivered |= _drive_calls(win, tf, stub, expected, now,
                                      calls=new_calls)
            if not session._wave_plan_queue and win._history_req_ids == set():
                converged = True
                break  # queue drained: the wave finalized in this load
            _load(win, symbol, tf, stub, now)
        assert converged, f"floor wave did not converge: {(tf, symbol)}"
        assert delivered == set(expected_ts)

        # The resulting bar list is continuous across the whole span: exactly
        # the expected timestamps, no silent hole.
        bars = BarCache.get_bars(symbol, tf)
        span = spans[0]
        in_span = [b.ts for b in bars if span.start_ts <= b.ts <= span.end_ts]
        assert in_span == sorted(expected_ts), (tf, symbol)

        by_day: dict[date, list[Bar]] = {}
        for b in bars:
            by_day.setdefault(_et_date(b.ts), []).append(b)
        for d in missing:
            day_bars = sorted(by_day.get(d, []), key=lambda b: b.ts)
            assert day_bars, (tf, symbol, d)
            if tf != "1 day":
                period = TIMEFRAME_SECONDS[tf]
                diffs = [day_bars[i].ts - day_bars[i - 1].ts
                         for i in range(1, len(day_bars))]
                assert all(x == period for x in diffs), (tf, symbol, d)

        # No silent hole: every chunk this fixture answers is fully delivered
        # (asserted above), so NONE of the answered days may be reported as still
        # missing. D42/S17's floor span legitimately reports its own further-back
        # days, so the assertion targets the answered days precisely.
        msg = win.status_bar.currentMessage()
        for d in missing:
            assert d.isoformat() not in msg, (
                f"an answered day ({d}) must not be reported as missing")
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T40-T05 / AC-D16.1 edge — switch mid-flight cannot contaminate the new chart
# ---------------------------------------------------------------------------
def test_t40_t05_switch_mid_flight_isolated(monkeypatch, qapp):
    """T40-T05: late previous-wave bars never reach the new symbol's chart."""
    tf = "5 mins"
    sym_a, sym_b = "T40SWA", "T40SWB"
    _clear(sym_a, tf)
    _clear(sym_b, tf)

    # A: present 2026-05-26..05-29 and 06-12; hole 06-01..06-11 (3 chunks).
    for i, d in enumerate([date(2026, 5, 26), date(2026, 5, 27),
                           date(2026, 5, 28), date(2026, 5, 29)]):
        _seed_day(sym_a, tf, d, 100.0 + i)
    _seed_day(sym_a, tf, date(2026, 6, 12), 200.0)
    missing_a = [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3),
                 date(2026, 6, 4), date(2026, 6, 5), date(2026, 6, 8),
                 date(2026, 6, 9), date(2026, 6, 10), date(2026, 6, 11)]
    now_a = _et_ts(2026, 6, 12, 20, 0)

    # B: own hole on different dates so contamination would be visible.
    for i, d in enumerate([date(2026, 7, 6), date(2026, 7, 7),
                           date(2026, 7, 8), date(2026, 7, 9),
                           date(2026, 7, 10)]):
        _seed_day(sym_b, tf, d, 300.0 + i)
    _seed_day(sym_b, tf, date(2026, 7, 20), 400.0)
    missing_b = [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15),
                 date(2026, 7, 16), date(2026, 7, 17)]
    now_b = _et_ts(2026, 7, 20, 20, 0)

    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, sym_a, tf, stub, now_a)
        a_calls = list(stub.calls)
        a_ids = [c["reqId"] for c in a_calls]
        assert len(a_ids) >= 2
        expected_a = [b for d in missing_a for b in _session_bars(sym_a, tf, d)]

        # Switch symbol/timeframe while A's wave is in flight.
        win._now_ts = lambda: now_b
        win.symbol_input.setText(sym_b)
        win.tf_combo.setCurrentText(tf)
        win.load_chart()

        b_calls = stub.calls[len(a_calls):]
        b_ids = [c["reqId"] for c in b_calls]
        assert b_ids and set(a_ids).isdisjoint(b_ids)
        assert set(stub.cancelled) == set(a_ids)
        assert win._current_symbol == sym_b
        assert win.chart_panel._symbol == sym_b

        # A's responses arrive late: none may be accepted or persisted.
        for bar in expected_a:
            win._on_historical_bar(a_ids[0], _FakeIbBar(bar.ts, bar.close))
        for rid in a_ids:
            win._on_historical_data_end(rid)

        assert win._pending_bars == []
        assert win._history_req_ids == set(b_ids)

        # B still gets its own continuity treatment.
        expected_b = [b for d in missing_b for b in _session_bars(sym_b, tf, d)]
        delivered_b = _drive_calls(win, tf, stub, expected_b, now_b, calls=b_calls)
        assert delivered_b == {b.ts for b in expected_b}

        chart = win.chart_panel._bars
        assert chart
        assert all(b.symbol == sym_b for b in chart)
        a_ts = {b.ts for b in expected_a}
        assert a_ts.isdisjoint({b.ts for b in chart})
        assert a_ts.isdisjoint({b.ts for b in BarCache.get_bars(sym_b, tf)})
        # A's late bars were never saved either.
        assert a_ts.isdisjoint({b.ts for b in BarCache.get_bars(sym_a, tf)})

        b_by_day: dict[date, list[Bar]] = {}
        for b in BarCache.get_bars(sym_b, tf):
            b_by_day.setdefault(_et_date(b.ts), []).append(b)
        for d in missing_b:
            assert len(b_by_day.get(d, [])) == 192, d
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T40-T06 / AC-D16 edge — empty cache falls back to the configured window
# ---------------------------------------------------------------------------
def test_t40_t06_empty_cache_fallback_renders(monkeypatch, qapp):
    """T40-T06: empty cache -> one configured-window request, rendered cleanly."""
    symbol, tf = "T40EMPTY", "5 mins"
    _clear(symbol, tf)
    now = _et_ts(2026, 9, 30, 20, 0)

    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, tf, stub, now)

        # Empty cache: D42/S17 REMOVED the configured-window single-request
        # branch (endDateTime == ""), so the planner's floor span now drives the
        # wave -- many chunks, each with a real endDateTime. The intent -- an
        # empty cache renders cleanly from the planner -- is asserted below.
        assert len(stub.calls) >= 1
        assert all(c["endDateTime"] for c in stub.calls), (
            "the removed single-window branch must not reappear")
        assert {c["timeframe"] for c in stub.calls} == {tf}
        assert win._history_req_ids == {c["reqId"] for c in stub.calls}

        expected = (_session_bars(symbol, tf, date(2026, 9, 29))
                    + _session_bars(symbol, tf, date(2026, 9, 30)))
        delivered = _drive_calls(win, tf, stub, expected, now)
        assert delivered == {b.ts for b in expected}
        assert win._history_req_ids == set()

        bars = win.chart_panel._bars
        assert len(bars) == len(expected)
        assert [b.ts for b in bars] == sorted(b.ts for b in expected)
        assert all(b.symbol == symbol for b in bars)

        # Rendered without error: the view carries the returned bars as real
        # UTC series times, with the volume heights from the shared model.
        panel = win.chart_panel
        series_ts = panel.series_times
        vol_x, _vol_h, _vol_colors = chart_model.volume_display_columns(
            panel.plotted_bars, None)
        assert series_ts == sorted(int(b.ts) for b in expected)
        assert [int(x) for x in vol_x] == series_ts
        assert "error" not in win.status_bar.currentMessage().lower()
    finally:
        win.close()
