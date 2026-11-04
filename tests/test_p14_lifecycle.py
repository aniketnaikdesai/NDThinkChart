"""P14-T2 (D53.2) — indicator lifecycle on the four terminal paths (S-P14-2).

Offscreen MainWindow tests (``IBApiClient.connect`` monkeypatched, historical
feed stubbed) proving the P14-T1 indicator clears exactly once on each of the
four existing terminal paths (normal completion, stranded watchdog
finalisation, cancellation via symbol-switch load, disconnect), that a
mid-wave same-triple reload keeps the running indicator with its elapsed
baseline unreset (Branch-A coalesced keep), and that a mid-wave mode-switch
(ext-hours toggle) clears-and-reraises as a new wave.

Helpers mirror ``tests/test_p14_indicator.py`` (seeded ``BarCache`` +
stubbed ``req_historical_data``); nothing here weakens, skips or rewrites an
existing test.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from PyQt6.QtWidgets import QDockWidget

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")

SYMBOL = "SPY"
SYMBOL2 = "QQQ"
TF = "5 mins"
SEED_DAY = date(2026, 8, 3)  # one complete old session; everything since is missing
NOW_TS = int(datetime(2026, 10, 2, 20, 0, tzinfo=EASTERN).timestamp())


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _session_bars(symbol: str, day: date, base: float = 100.0) -> list[Bar]:
    """One deterministic complete 5-min session (04:00-20:00 ET)."""
    assert is_trading_day(day)
    period = TIMEFRAME_SECONDS[TF]
    start = _et_ts(day.year, day.month, day.day, 4, 0)
    close = _et_ts(day.year, day.month, day.day, 20, 0)
    bars: list[Bar] = []
    ts, i = start, 0
    while ts < close:
        price = base + (i % 5) * 0.25
        bars.append(
            Bar(symbol, TF, ts, price, price + 0.5, price - 0.5, price,
                1000.0 + (ts % 500))
        )
        ts += period
        i += 1
    return bars


def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


def _seed_day(symbol: str, day: date, base: float = 100.0) -> int:
    bars = _session_bars(symbol, day, base)
    BarCache.save_bars(bars)
    return len(bars)


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


class _ReqStub:
    """Captures ``req_historical_data`` calls; records cancels."""

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


def _wave_calls(stub: _ReqStub) -> list[dict]:
    """Issued backfill-wave calls (D27.9 priming is never a wave member)."""
    return [c for c in stub.calls if c.get("bar_size") != "5 secs"]


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.rt_manager.unsubscribe = lambda *a, **k: None
    win.rt_manager.cancel_all = lambda *a, **k: None
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _load(win, symbol: str, tf: str, stub: _ReqStub, now_ts: int) -> None:
    """Drive the real ``load_chart`` against the stubbed manager at fixed now."""
    win._now_ts = lambda: now_ts
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(tf)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()


def _parse_end(end: str) -> int:
    return int(
        datetime.strptime(end, "%Y%m%d-%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    )


def _live_wave(monkeypatch, qapp, symbol: str = SYMBOL):
    """Seed + load a genuine multi-chunk in-flight wave; return (win, stub)."""
    _clear(symbol, TF)
    _seed_day(symbol, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, TF, stub, NOW_TS)
    except Exception:
        win.close()
        raise
    return win, stub


# ---------------------------------------------------------------------------
# T21 / AC1 — each terminal path clears the live indicator exactly once
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["normal", "watchdog", "cancel", "disconnect"])
def test_t21_terminal_path_clears_indicator_exactly_once(
    monkeypatch, qapp, path: str
):
    win, stub = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2  # a genuine multi-chunk wave is in flight
        session = win.get_or_create_session(SYMBOL)
        assert session._wave_start_ts is not None  # baseline stamped at issue
        assert win._backfill_state is not None  # indicator is live

        # Spy AFTER the load: the load-path cancel itself clears once, and
        # only terminations after this point may clear again.
        clears: list = []
        real_clear = win.clear_backfill_indicator

        def _spy():
            clears.append(None)
            return real_clear()

        monkeypatch.setattr(win, "clear_backfill_indicator", _spy)

        if path == "normal":
            # Per-chunk completion to empty: the last end marker finalises.
            for c in wave:
                anchor = _parse_end(c["endDateTime"])
                win._on_historical_bar(
                    c["reqId"], _FakeIbBar(anchor - 60, 101.0)
                )
                win._on_historical_data_end(c["reqId"])
        elif path == "watchdog":
            # Watchdog timeout injection on the live wave.
            win._on_session_history_wave_timeout(session)
        elif path == "cancel":
            # Symbol-switch load cancels the old wave…
            _clear(SYMBOL2, TF)
            _seed_day(SYMBOL2, SEED_DAY, base=200.0)
            win.symbol_input.setText(SYMBOL2)
            win.tf_combo.setCurrentText(TF)
            win.load_chart()
            # …and immediately raises a fresh wave for the new symbol.
            assert win._backfill_state is not None
        elif path == "disconnect":
            # Transport-drop injection with the wave in flight.
            win._on_disconnected()

        assert len(clears) == 1, f"{path}: cleared {len(clears)}x, want exactly 1"

        if path == "cancel":
            # The new symbol's wave re-raised afresh on the same widget.
            session2 = win.get_or_create_session(SYMBOL2)
            assert session2._wave_start_ts is not None
            assert session._wave_start_ts is None  # old baseline died
        else:
            assert win._backfill_state is None
            assert win._backfill_indicator.text() == "Backfill: idle"
            assert session._wave_start_ts is None  # baseline cleared
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T22 / AC2 — same-triple reload keeps the indicator with baseline unreset
# ---------------------------------------------------------------------------
def test_t22_same_triple_reload_keeps_indicator_and_baseline(
    monkeypatch, qapp
):
    win, stub = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(SYMBOL)
        gen_before = session._history_generation
        ts_before = session._wave_start_ts
        assert ts_before is not None
        indicator_before = win._backfill_indicator
        state_before = dict(win._backfill_state)
        n_calls_before = len(stub.calls)

        win.load_chart()  # same (symbol, timeframe, ext-hours): Branch A

        # No new historical reqId, generation untouched…
        assert len(stub.calls) == n_calls_before
        assert session._history_generation == gen_before
        # …same indicator object, still running…
        assert win._backfill_indicator is indicator_before
        assert win._backfill_state is not None
        assert win._backfill_state["in_flight"] == state_before["in_flight"]
        assert sorted(win._backfill_state["req_ids"]) == sorted(
            state_before["req_ids"]
        )
        # …elapsed baseline unreset: the stamp is identical and elapsed is
        # continuous (never rewound by the coalesced reload).
        assert session._wave_start_ts == ts_before
        assert win._backfill_state["elapsed_s"] >= state_before["elapsed_s"]
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T23 / AC3 — mode-switch load clears-and-reraises as a new wave
# ---------------------------------------------------------------------------
def test_t23_mode_switch_clears_and_reraises_new_wave(monkeypatch, qapp):
    win, stub = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(SYMBOL)
        old_req_ids = [c["reqId"] for c in wave]
        gen_before = session._history_generation
        ts_before = session._wave_start_ts
        assert ts_before is not None

        events: list[str] = []
        real_clear = win.clear_backfill_indicator
        real_raise = win._raise_backfill_indicator

        def _spy_clear():
            events.append("clear")
            return real_clear()

        def _spy_raise(session_arg):
            events.append("raise")
            return real_raise(session_arg)

        monkeypatch.setattr(win, "clear_backfill_indicator", _spy_clear)
        monkeypatch.setattr(win, "_raise_backfill_indicator", _spy_raise)
        n_calls_before = len(stub.calls)

        # Ext-hours toggle mid-wave: a new triple, not a coalesced keep.
        # (The suite never assumes the toolbar toggle default — it flips
        # whatever mode the live wave is running in.)
        win.load_chart(SYMBOL, TF, not session._wave_extended_hours)

        # The old wave cancelled…
        assert set(old_req_ids) <= set(stub.cancelled)
        assert session._history_generation == gen_before + 1
        # …the indicator cleared exactly once, then re-raised for the new
        # wave (a clear-and-reraise, never a keep of the old state).
        assert events.count("clear") == 1, f"events={events}"
        assert events.count("raise") == 1, f"events={events}"
        assert events.index("clear") < events.index("raise")
        # The new wave is genuinely new: fresh reqIds on the same widget with
        # a freshly stamped baseline.
        new_wave = [c for c in stub.calls[n_calls_before:]
                    if c.get("bar_size") != "5 secs"]
        assert len(new_wave) >= 1
        assert win._backfill_state is not None
        assert sorted(win._backfill_state["req_ids"]) == sorted(
            c["reqId"] for c in new_wave
        )
        assert session._wave_start_ts is not None
    finally:
        win.close()
