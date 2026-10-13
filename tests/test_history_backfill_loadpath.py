"""T39 / D16 — MainWindow load-path correlated multi-request backfill.

These are offscreen integration tests for ``ui.main_window.MainWindow``. They
stub the IBKR connection and the ``MarketDataManager`` so the load path never
touches TWS, then drive the historical-data slots directly to model the bridge
signals.

The path under test:

    load_chart()
      -> services.backfill_service.find_missing_spans/plan_requests
      -> one md_manager.req_historical_data(endDateTime=plan.endDateTime) per chunk
      -> _register_history_request(reqId) into _history_req_ids
      -> _on_historical_bar / _on_historical_data_end accumulate the wave
      -> _finalize_history_wave once, only after the last member ends

Nothing here weakens or replaces the pure planner's own tests
(``tests/test_backfill_service.py``); it only asserts the window orchestration.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

import pytest
from PyQt6.QtWidgets import QDockWidget

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.models import Bar
from services.backfill_service import find_missing_spans, plan_requests

EASTERN = ZoneInfo("America/New_York")

# ---------------------------------------------------------------------------
# Deterministic calendar scenario
# ---------------------------------------------------------------------------
# Present sessions: 2026-10-12..10-16 and 2026-11-02..11-06.
# Missing sessions: 2026-10-19..10-30 (two full trading weeks -> one span whose
# closure (12 calendar days) exceeds the "5 mins" configured 5 D fetch window,
# so the planner chunks it into 3 requests). None of these days is a US-equity
# holiday in the market_calendar rule set.
PRESENT_DAYS = [
    (2026, 10, 12), (2026, 10, 13), (2026, 10, 14), (2026, 10, 15), (2026, 10, 16),
    (2026, 11, 2), (2026, 11, 3), (2026, 11, 4), (2026, 11, 5), (2026, 11, 6),
]
MISSING_DAYS = [
    (2026, 10, 19), (2026, 10, 20), (2026, 10, 21), (2026, 10, 22), (2026, 10, 23),
    (2026, 10, 26), (2026, 10, 27), (2026, 10, 28), (2026, 10, 29), (2026, 10, 30),
]
NOW = int(datetime(2026, 11, 6, 20, 0, tzinfo=EASTERN).timestamp())

# D27.7: _seed writes complete 1-min extended-hours days (04:00-20:00 ET).
_BARS_PER_DAY = 16 * 60


def _et_ts(y: int, m: int, d: int, h: int = 12, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


def _seed(symbol: str, timeframe: str, days) -> None:
    """Seed one *complete* extended-hours day of 1-min bars per ``(y, m, d)``.

    D27.7: ``find_missing_spans`` runs bar-period-granularity gap detection
    on trailing trading days using the load's ext-hours toggle (default ON:
    04:00-20:00 ET), so a "present"/"current" day must be a genuinely complete
    intraday series for that session — a single noon bar is (correctly)
    reported as a day with intraday holes. A full 1-min series is gap-free
    for every timeframe, so the day-presence assertions keep working.
    """
    bars = []
    for i, (y, m, d) in enumerate(days):
        h, minute = 4, 0
        while (h, minute) <= (19, 59):
            ts = _et_ts(y, m, d, h, minute)
            bars.append(Bar(symbol, timeframe, ts, 100.0 + i, 100.5 + i,
                            99.5 + i, 100.0 + i, 1000.0))
            minute += 1
            if minute >= 60:
                h += 1
                minute = 0
    BarCache.save_bars(bars)


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0):
        self.date = str(int(ts))  # parse_ibkr_date accepts a 10-digit epoch string
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = 1000


class _ReqStub:
    """Captures ``req_historical_data`` calls and ``cancel_historical_data`` ids."""

    def __init__(self, first_id: int = 1000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False):
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
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


class _FakeCloseEvent:
    def accept(self):  # pragma: no cover - trivial
        pass

    def ignore(self):  # pragma: no cover - trivial
        pass


def _make_window(monkeypatch, qapp):
    """Build a shown MainWindow that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    # The load path must reach only the (stubbed) managers, never a socket.
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Active Trader",):
            dock.hide()
    qapp.processEvents()
    return win


def _load(win, symbol: str, timeframe: str, stub: _ReqStub, now_ts: int) -> None:
    """Drive the real ``load_chart`` against the stubbed manager at a fixed now."""
    win._now_ts = lambda: now_ts
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(timeframe)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()


# ---------------------------------------------------------------------------
# T39-T01 — one request per planned chunk, endDateTime non-empty, ids tracked
# ---------------------------------------------------------------------------
def test_t39_t01_issues_one_request_per_planned_chunk(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "T39A", "5 mins"
    try:
        _clear(symbol, tf)
        _seed(symbol, tf, PRESENT_DAYS)
        stub = _ReqStub()
        _load(win, symbol, tf, stub, NOW)

        cached_ts = [b.ts for b in BarCache.get_bars(symbol, tf)]
        plans = plan_requests(find_missing_spans(cached_ts, NOW, tf), tf)

        # The seeded hole needs more than one configured (5 D) fetch window.
        assert len(plans) > 1
        assert len(stub.calls) == len(plans)

        # Every chunk rides the existing endDateTime parameter; signature intact.
        for call in stub.calls:
            assert call["endDateTime"]  # non-empty anchor
            assert call["timeframe"] == tf
            assert call["whatToShow"] == "TRADES"
            assert call["useRTH"] == 1
            assert "extended_hours" in call
        assert [c["endDateTime"] for c in stub.calls] == [p.endDateTime for p in plans]

        returned = {c["reqId"] for c in stub.calls}
        assert returned <= win._history_req_ids
        assert returned == win._history_req_ids
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T39-T02 — no redundant request when the cache reaches now
# ---------------------------------------------------------------------------
def test_t39_t02_cache_current_issues_no_request(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "T39B", "5 mins"
    try:
        _clear(symbol, tf)
        # A current cache: every trading day from its earliest to now is present.
        _seed(symbol, tf, [(2026, 11, 2), (2026, 11, 3), (2026, 11, 4),
                           (2026, 11, 5), (2026, 11, 6)])
        stub = _ReqStub()
        _load(win, symbol, tf, stub, NOW)

        assert stub.calls == []
        assert win._history_req_ids == set()
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T39-T03 — empty cache falls back to the configured window as a set of one
# ---------------------------------------------------------------------------
def test_t39_t03_empty_cache_fallback_single_request(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "T39C", "5 mins"
    try:
        _clear(symbol, tf)  # no cached bars at all
        stub = _ReqStub()
        _load(win, symbol, tf, stub, NOW)

        assert len(stub.calls) == 1
        assert stub.calls[0]["endDateTime"] == ""
        assert win._history_req_ids == {stub.calls[0]["reqId"]}

        # "Set of one": ending the single member finalises immediately.
        win._on_historical_data_end(stub.calls[0]["reqId"])
        assert win._history_req_ids == set()
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T39-T04 — bars accumulate across members; one finalise; stale/non-member ignored
# ---------------------------------------------------------------------------
def test_t39_t04_multi_request_wave_finalises_once(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "T39D", "5 mins"
    try:
        _clear(symbol, tf)
        _seed(symbol, tf, PRESENT_DAYS)
        stub = _ReqStub()
        _load(win, symbol, tf, stub, NOW)
        req_ids = [c["reqId"] for c in stub.calls]
        assert len(req_ids) >= 2

        # Spy after load so the immediate cached render isn't counted.
        real_save = BarCache.save_bars
        real_get = BarCache.get_bars
        save_calls: list[int] = []
        get_calls: list[tuple] = []

        def spy_save(bars):
            save_calls.append(len(bars))
            return real_save(bars)

        def spy_get(s, t):
            get_calls.append((s, t))
            return real_get(s, t)

        monkeypatch.setattr(BarCache, "save_bars", staticmethod(spy_save))
        monkeypatch.setattr(BarCache, "get_bars", staticmethod(spy_get))

        update_calls: list[int] = []
        win.chart_panel.update_chart = lambda bars: update_calls.append(len(bars))

        # A non-member event is ignored.
        win._on_historical_bar(999_999, _FakeIbBar(_et_ts(2026, 10, 19)))
        assert win._pending_bars == []

        # A stale-generation event (tracked id, but the token moved on) is ignored.
        gen = win._history_generation
        win._history_generation = gen + 1
        win._on_historical_bar(req_ids[0], _FakeIbBar(_et_ts(2026, 10, 19, 12, 30)))
        win._history_generation = gen
        assert win._pending_bars == []

        # Bars from every member accumulate; nothing is saved/rendered mid-wave.
        for i, rid in enumerate(req_ids):
            win._on_historical_bar(rid, _FakeIbBar(_et_ts(2026, 10, 19) + i * 300))
        assert win._pending_bars
        assert save_calls == [] and get_calls == [] and update_calls == []

        # End all but the last: the wave is still open, so still no finalise.
        for rid in req_ids[:-1]:
            win._on_historical_data_end(rid)
        assert win._history_req_ids == {req_ids[-1]}
        assert save_calls == [] and get_calls == [] and update_calls == []

        # The last end empties the set: exactly one save + re-read + render.
        win._on_historical_data_end(req_ids[-1])
        assert win._history_req_ids == set()
        assert len(save_calls) == 1
        assert len(get_calls) == 1
        assert len(update_calls) == 1
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T39-T05 — switch and close cancel every id and advance the generation
# ---------------------------------------------------------------------------
def test_t39_t05_switch_and_close_cancel_all(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    sym_hole, sym_current, tf = "T39E", "T39F", "5 mins"
    try:
        _clear(sym_hole, tf)
        _clear(sym_current, tf)
        _seed(sym_hole, tf, PRESENT_DAYS)              # has a hole -> a wave
        _seed(sym_current, tf, [(2026, 11, 2), (2026, 11, 3), (2026, 11, 4),
                                (2026, 11, 5), (2026, 11, 6)])  # current -> none

        stub = _ReqStub(first_id=2000)
        _load(win, sym_hole, tf, stub, NOW)
        old_ids = set(win._history_req_ids)
        gen_before = win._history_generation
        assert len(old_ids) >= 2

        # Symbol/timeframe switch: every tracked id is cancelled exactly once and
        # the generation token advances.
        win.symbol_input.setText(sym_current)
        win.tf_combo.setCurrentText(tf)
        win.load_chart()
        assert set(stub.cancelled) == old_ids
        assert len(stub.cancelled) == len(old_ids)
        # D28.2: generations are per-session now. The old session's wave was
        # invalidated (reqIds unregistered from the routing table); the new
        # session starts its own generation.
        assert win._history_generation == 1
        assert win._history_req_ids == set()

        # Late responses from the previous generation never reach the render path.
        stale = next(iter(old_ids))
        win._on_historical_bar(stale, _FakeIbBar(_et_ts(2026, 10, 19)))
        win._on_historical_data_end(stale)
        assert win._pending_bars == []
        assert win._history_req_ids == set()

        # Re-open a wave on the hole symbol, then close the window.
        win.symbol_input.setText(sym_hole)
        win.load_chart()
        wave_ids = set(win._history_req_ids)
        assert len(wave_ids) >= 2
        gen_before_close = win._history_generation

        stub.cancelled.clear()
        win.closeEvent(_FakeCloseEvent())

        assert set(stub.cancelled) == wave_ids
        assert len(stub.cancelled) == len(wave_ids)
        assert win._history_generation == gen_before_close + 1
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T39-T06 — a failed member is dropped so the wave can finalise; shortfall shown
# ---------------------------------------------------------------------------
def test_t39_t06_failed_member_finalises_with_shortfall(monkeypatch, qapp, caplog):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "T39G", "5 mins"
    try:
        _clear(symbol, tf)
        _seed(symbol, tf, PRESENT_DAYS)
        stub = _ReqStub()
        _load(win, symbol, tf, stub, NOW)
        req_ids = [c["reqId"] for c in stub.calls]
        assert len(req_ids) >= 2

        failed = req_ids[0]
        with caplog.at_level(logging.WARNING, logger="ui.main_window"):
            win._on_error(failed, 200, "No security definition has been found")

        # Dropped from the wave so the remaining members can still empty it.
        assert failed not in win._history_req_ids
        assert failed in win._backfill_failed_req_ids

        # One genuine bar, then end the rest: finalisation still happens.
        remaining = [r for r in req_ids if r != failed]
        win._on_historical_bar(remaining[0], _FakeIbBar(_et_ts(2026, 10, 19)))
        for rid in remaining:
            win._on_historical_data_end(rid)
        assert win._history_req_ids == set()

        # Shortfall surfaced (status bar + log); no bar fabricated for the gap.
        msg = win.status_bar.currentMessage()
        assert "incomplete" in msg or "missing" in msg or "failed" in msg
        assert any(
            "shortfall" in rec.getMessage().lower() or "failed" in rec.getMessage().lower()
            for rec in caplog.records
        )

        bars = BarCache.get_bars(symbol, tf)
        # D27.7: seeds are complete 1-min days now (see _seed).
        assert len(bars) == _BARS_PER_DAY * len(PRESENT_DAYS) + 1
        assert date(2026, 10, 28) not in {_et_date(b.ts) for b in bars}
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T39-T07 — a still-empty trading day after the wave is surfaced, never faked
# ---------------------------------------------------------------------------
def test_t39_t07_completed_wave_surfaces_missing_day_no_fabrication(
    monkeypatch, qapp, caplog
):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "T39H", "5 mins"
    try:
        _clear(symbol, tf)
        _seed(symbol, tf, PRESENT_DAYS)
        stub = _ReqStub()
        _load(win, symbol, tf, stub, NOW)
        req_ids = [c["reqId"] for c in stub.calls]
        assert len(req_ids) >= 1

        omitted = date(2026, 10, 28)
        with caplog.at_level(logging.WARNING, logger="ui.main_window"):
            for (y, m, d) in MISSING_DAYS:
                if date(y, m, d) == omitted:
                    continue
                win._on_historical_bar(req_ids[0], _FakeIbBar(_et_ts(y, m, d)))
            for rid in req_ids:
                win._on_historical_data_end(rid)

        msg = win.status_bar.currentMessage()
        assert "incomplete" in msg
        assert omitted.isoformat() in msg
        assert any("shortfall" in rec.getMessage().lower() for rec in caplog.records)

        bars = BarCache.get_bars(symbol, tf)
        present_days = {_et_date(b.ts) for b in bars}
        assert omitted not in present_days

        # No fabricated/interpolated bar: exactly the seeds plus genuine returns.
        expected_days = {date(*d) for d in PRESENT_DAYS}
        expected_days |= {date(*d) for d in MISSING_DAYS if date(*d) != omitted}
        assert present_days == expected_days
        # D27.7: seeds are complete 1-min days; each delivered missing day
        # contributed exactly one genuine bar.
        assert len(bars) == (
            _BARS_PER_DAY * len(PRESENT_DAYS) + len(MISSING_DAYS) - 1
        )
    finally:
        win.close()
