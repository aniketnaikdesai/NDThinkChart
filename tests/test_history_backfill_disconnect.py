"""T43 / D16 / ESC-024 — cancel + finalise a stranded backfill wave.

These are offscreen integration tests for ``ui.main_window.MainWindow``. They
stub the IBKR connection and the ``MarketDataManager`` exactly like
``tests/test_history_backfill_loadpath.py`` so the load path never touches TWS,
start a real multi-request backfill wave, then strand it via
``_on_disconnected`` or the bounded wave watchdog.

The behaviour under test (ESC-024):

    a dropped connection / stalled request mid-wave
      -> every tracked reqId cancelled, _history_req_ids emptied
      -> _history_generation advanced so late responses are rejected
      -> _finalize_history_wave runs exactly once and surfaces AC-D16.4's
         shortfall (status bar + WARNING log), with NO bar fabricated

Nothing here weakens, skips or rewrites an existing test.
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

EASTERN = ZoneInfo("America/New_York")

# Present sessions: 2026-10-12..10-16 and 2026-11-02..11-06.
# Missing sessions: 2026-10-19..10-30 (two full trading weeks) -> closure exceeds
# the "5 mins" configured 5 D fetch window, so the planner issues 3 requests.
PRESENT_DAYS = [
    (2026, 10, 12), (2026, 10, 13), (2026, 10, 14), (2026, 10, 15), (2026, 10, 16),
    (2026, 11, 2), (2026, 11, 3), (2026, 11, 4), (2026, 11, 5), (2026, 11, 6),
]
MISSING_DAYS = [
    (2026, 10, 19), (2026, 10, 20), (2026, 10, 21), (2026, 10, 22), (2026, 10, 23),
    (2026, 10, 26), (2026, 10, 27), (2026, 10, 28), (2026, 10, 29), (2026, 10, 30),
]
NOW = int(datetime(2026, 11, 6, 20, 0, tzinfo=EASTERN).timestamp())


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
    bars = [
        Bar(symbol, timeframe, _et_ts(y, m, d), 100.0 + i, 100.5 + i,
            99.5 + i, 100.0 + i, 1000.0)
        for i, (y, m, d) in enumerate(days)
    ]
    BarCache.save_bars(bars)


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0):
        self.date = str(int(ts))
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = 1000


class _ReqStub:
    """Captures ``req_historical_data`` calls and ``cancel_historical_data`` ids."""

    def __init__(self, first_id: int = 7000):
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


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    # closeEvent drives the real unsubscribe/cancel_all paths; stub them so a
    # test that exercises closeEvent never reaches an unconfigured ibapi client.
    win.rt_manager.unsubscribe = lambda *a, **k: None
    win.rt_manager.cancel_all = lambda *a, **k: None
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


def _seed_and_load(monkeypatch, qapp, symbol: str, tf: str = "5 mins"):
    """Seed PRESENT_DAYS, load, and return (win, stub, req_ids) for a live wave."""
    _clear(symbol, tf)
    _seed(symbol, tf, PRESENT_DAYS)
    win = _make_window(monkeypatch, qapp)
    stub = _ReqStub()
    _load(win, symbol, tf, stub, NOW)
    req_ids = [c["reqId"] for c in stub.calls]
    return win, stub, req_ids


# ---------------------------------------------------------------------------
# T43-T01 — disconnect mid-wave cancels every tracked reqId and empties the set
# ---------------------------------------------------------------------------
def test_t43_t01_disconnect_cancels_every_inflight_reqid(monkeypatch, qapp):
    symbol = "T43A"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        # A genuine multi-request wave is in flight.
        assert len(req_ids) >= 2
        assert win._history_req_ids == set(req_ids)

        win._on_disconnected()

        assert set(stub.cancelled) == set(req_ids)
        assert len(stub.cancelled) == len(set(req_ids))
        assert win._history_req_ids == set()
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T43-T02 — disconnect advances the generation; late events are rejected
# ---------------------------------------------------------------------------
def test_t43_t02_disconnect_advances_generation_rejects_late_events(
    monkeypatch, qapp
):
    symbol = "T43B"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        assert len(req_ids) >= 2
        gen_before = win._history_generation

        # Spy so we can prove finalisation happened exactly once, on the drop.
        finalise_calls: list[int] = []
        real_finalize = win._finalize_history_wave

        def spy_finalize():
            finalise_calls.append(1)
            return real_finalize()

        win._finalize_history_wave = spy_finalize

        win._on_disconnected()

        assert win._history_generation > gen_before
        assert finalise_calls == [1]

        # A pre-drop reqId is no longer accepted; its late events land nowhere.
        stale = req_ids[0]
        assert win._history_event_accepted(stale) is False
        win._on_historical_bar(stale, _FakeIbBar(_et_ts(2026, 10, 19)))
        win._on_historical_data_end(stale)

        assert win._pending_bars == []
        assert win._history_req_ids == set()
        # No second finalise from the late end marker.
        assert finalise_calls == [1]
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T43-T03 — the stranded wave surfaces the AC-D16.4 shortfall (bar + log)
# ---------------------------------------------------------------------------
def test_t43_t03_disconnect_surfaces_shortfall_once(monkeypatch, qapp, caplog):
    symbol = "T43C"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        assert len(req_ids) >= 2

        finalise_calls: list[int] = []
        real_finalize = win._finalize_history_wave

        def spy_finalize():
            finalise_calls.append(1)
            return real_finalize()

        win._finalize_history_wave = spy_finalize

        with caplog.at_level(logging.WARNING, logger="ui.main_window"):
            win._on_disconnected()

        assert finalise_calls == [1]

        msg = win.status_bar.currentMessage()
        assert "incomplete" in msg
        # At least one still-missing trading day is named in the message.
        assert any(date(y, m, d).isoformat() in msg for y, m, d in MISSING_DAYS)

        assert any(
            "historical backfill shortfall" in rec.getMessage().lower()
            for rec in caplog.records
        )
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T43-T04 — no bar fabricated: only the seeded bars survive a stranded wave
# ---------------------------------------------------------------------------
def test_t43_t04_no_bar_fabricated_on_stranded_wave(monkeypatch, qapp):
    symbol = "T43D"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        assert len(req_ids) >= 2
        before_bars = BarCache.get_bars(symbol, "5 mins")
        before_ts = {b.ts for b in before_bars}
        before_days = {_et_date(b.ts) for b in before_bars}

        # Disconnect without delivering any historical bar.
        win._on_disconnected()

        after_bars = BarCache.get_bars(symbol, "5 mins")
        after_ts = {b.ts for b in after_bars}
        assert after_ts == before_ts

        # No missing-span trading day leaks in.
        for y, m, d in MISSING_DAYS:
            assert date(y, m, d) not in {_et_date(b.ts) for b in after_bars}
            assert date(y, m, d) not in before_days

        # ChartPanel holds exactly the seeded timestamps.
        chart = win.chart_panel._bars
        assert {b.ts for b in chart} == before_ts

        # Volume series carries no injected value for a missing date.
        vol_x = [int(v) for v in win.chart_panel.volume_bars.opts["x"]]
        assert set(vol_x) == before_ts
        missing_ts = {
            _et_ts(y, m, d) for y, m, d in MISSING_DAYS
        }
        assert missing_ts.isdisjoint(set(vol_x))

        assert win._pending_bars == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T43-T05 — the bounded watchdog finalises a stalled wave through the same path
# ---------------------------------------------------------------------------
def test_t43_t05_watchdog_finalises_stalled_wave(monkeypatch, qapp, caplog):
    symbol = "T43E"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        assert len(req_ids) >= 2
        gen_before = win._history_generation

        finalise_calls: list[int] = []
        real_finalize = win._finalize_history_wave

        def spy_finalize():
            finalise_calls.append(1)
            return real_finalize()

        win._finalize_history_wave = spy_finalize

        # No connection drop: the watchdog itself strands the wave.
        with caplog.at_level(logging.WARNING, logger="ui.main_window"):
            win._on_history_wave_timeout()

        assert set(stub.cancelled) == set(req_ids)
        assert win._history_req_ids == set()
        assert win._history_generation > gen_before
        assert finalise_calls == [1]

        msg = win.status_bar.currentMessage()
        assert "incomplete" in msg
        assert any(
            "historical backfill shortfall" in rec.getMessage().lower()
            for rec in caplog.records
        )

        # Once stranded, a late pre-drop end marker must not finalise again.
        win._on_historical_data_end(req_ids[0])
        assert finalise_calls == [1]
        assert win._pending_bars == []
        assert BarCache.get_bars(symbol, "5 mins")
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T43-T06 — disconnect with no live wave is a no-op finalise-wise and safe
# ---------------------------------------------------------------------------
def test_t43_t06_disconnect_after_wave_finalised_no_double_finalise(
    monkeypatch, qapp
):
    symbol = "T43F"
    tf = "5 mins"
    _clear(symbol, tf)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        # Empty cache -> a single-request wave (set of one).
        _load(win, symbol, tf, stub, NOW)
        assert len(stub.calls) == 1
        rid = stub.calls[0]["reqId"]
        assert win._history_req_ids == {rid}

        # Drive the normal wave to completion: set empties, already finalised.
        win._on_historical_bar(rid, _FakeIbBar(_et_ts(2026, 11, 5)))
        win._on_historical_data_end(rid)
        assert win._history_req_ids == set()

        finalise_calls: list[int] = []
        real_finalize = win._finalize_history_wave

        def spy_finalize():
            finalise_calls.append(1)
            return real_finalize()

        win._finalize_history_wave = spy_finalize

        win._on_disconnected()  # must not raise

        assert finalise_calls == []
        assert win._history_req_ids == set()
        assert win.conn_badge.text() == "● Disconnected"
        assert win.status_bar.currentMessage() == "Disconnected from IBKR"
    finally:
        win.close()


# ===========================================================================
# T44 / ESC-025 — closeEvent disarms the wave watchdog, and the stranded-wave
# reason is live (behaviour-neutral; AC-D16.4 shortfall wording preserved).
# ===========================================================================

# ---------------------------------------------------------------------------
# T44-T01 — closeEvent disarms an armed backfill watchdog
# ---------------------------------------------------------------------------
def test_t44_t01_close_event_disarms_watchdog(monkeypatch, qapp):
    symbol = "T44A"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    armed = True
    try:
        assert len(req_ids) >= 2
        # load_chart armed the bounded 30 s watchdog for this multi-request wave.
        assert win._history_wave_timer.isActive() is True

        win.close()

        assert win._history_wave_timer.isActive() is False
    finally:
        if armed:
            win.close()


# ---------------------------------------------------------------------------
# T44-T02 — closeEvent terminates the wave via the same disarm helper the
# other wave-terminating paths use (symmetry)
# ---------------------------------------------------------------------------
def test_t44_t02_close_event_disarms_via_shared_helper(monkeypatch, qapp):
    symbol = "T44B"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        assert len(req_ids) >= 2
        gen_before = win._history_generation

        # Spy on the shared helper closeEvent must call.
        disarm_calls: list[int] = []
        real_disarm = win._disarm_history_wave_watchdog

        def spy_disarm():
            disarm_calls.append(1)
            return real_disarm()

        win._disarm_history_wave_watchdog = spy_disarm

        win.close()

        assert disarm_calls == [1]
        assert set(stub.cancelled) == set(req_ids)
        assert len(stub.cancelled) == len(set(req_ids))
        assert win._history_req_ids == set()
        assert win._history_generation > gen_before
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T44-T03 — the stranded-wave reason distinguishes timeout from disconnect,
# while preserving the AC-D16.4 shortfall wording
# ---------------------------------------------------------------------------
def test_t44_t03_reason_distinguishes_timeout_and_disconnect(
    monkeypatch, qapp, caplog
):
    def _strand(via: str, symbol: str):
        win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
        try:
            assert len(req_ids) >= 2
            with caplog.at_level(logging.WARNING, logger="ui.main_window"):
                if via == "timeout":
                    win._on_history_wave_timeout()
                else:
                    win._on_disconnected()
            msg = win.status_bar.currentMessage()
            warns = [
                rec.getMessage()
                for rec in caplog.records
                if "historical backfill shortfall" in rec.getMessage().lower()
            ]
            return msg, warns
        finally:
            win.close()

    caplog.clear()
    timeout_msg, timeout_warns = _strand("timeout", "T44C1")
    caplog.clear()
    disconnect_msg, disconnect_warns = _strand("disconnect", "T44C2")

    # AC-D16.4 wording preserved in both.
    for msg in (timeout_msg, disconnect_msg):
        assert "incomplete" in msg
        assert any(date(y, m, d).isoformat() in msg for y, m, d in MISSING_DAYS)
    assert timeout_warns and disconnect_warns
    for warn in (*timeout_warns, *disconnect_warns):
        assert "historical backfill shortfall" in warn.lower()

    # The two diagnostics differ in the cause they name -> reason is live.
    assert timeout_msg != disconnect_msg
    assert "timed out" in timeout_msg.lower()
    assert "disconnect" in disconnect_msg.lower()
    assert any("timed out" in w.lower() for w in timeout_warns)
    assert any("disconnect" in w.lower() for w in disconnect_warns)


# ---------------------------------------------------------------------------
# T44-T04 — using reason is behaviour-neutral: no fabrication, exactly one
# finalise, exactly the in-flight reqIds cancelled
# ---------------------------------------------------------------------------
def test_t44_t04_reason_is_behaviour_neutral(monkeypatch, qapp):
    symbol = "T44D"
    win, stub, req_ids = _seed_and_load(monkeypatch, qapp, symbol)
    try:
        assert len(req_ids) >= 2
        before_bars = BarCache.get_bars(symbol, "5 mins")
        before_ts = {b.ts for b in before_bars}

        finalise_calls: list[int] = []
        real_finalize = win._finalize_history_wave

        def spy_finalize():
            finalise_calls.append(1)
            return real_finalize()

        win._finalize_history_wave = spy_finalize

        win._on_disconnected()

        assert set(stub.cancelled) == set(req_ids)
        assert len(stub.cancelled) == len(set(req_ids))
        assert win._history_req_ids == set()
        assert finalise_calls == [1]

        after_bars = BarCache.get_bars(symbol, "5 mins")
        assert {b.ts for b in after_bars} == before_ts
        for y, m, d in MISSING_DAYS:
            assert date(y, m, d) not in {_et_date(b.ts) for b in after_bars}
        assert {b.ts for b in win.chart_panel._bars} == before_ts
        assert win._pending_bars == []
    finally:
        win.close()
