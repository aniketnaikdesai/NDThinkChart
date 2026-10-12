"""D27.1 — _last_chart_price must never move backward on backfill finalize.

Regression test for the phantom-alarm bug: ``_finalize_history_wave``
unconditionally rewound ``_last_chart_price`` to the older historical close
even after realtime ticks had advanced it, so the next tick evaluated a
discontinuous (prev, curr) pair and any alarm level between the stale close
and the live price reported a cross that never happened.

AC-D27.1: backfill finalize after live ticks -> no phantom trigger; the live
forming bar survives finalize (no live-candle wipe).
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QDockWidget

from data.bar_cache import BarCache
from data.models import Alarm, Bar

SYMBOL = "PHANTOM"
TIMEFRAME = "5 mins"
BASE_TS = 1_760_000_000  # fixed; 5-min period containing BASE_TS..BASE_TS+25


def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


def _seed_history() -> None:
    """Three historical 5-min bars, last close 100.0 (older than live)."""
    bars = [
        Bar(SYMBOL, TIMEFRAME, BASE_TS - 900, 98.0, 98.5, 97.5, 98.0, 1000.0),
        Bar(SYMBOL, TIMEFRAME, BASE_TS - 600, 99.0, 99.5, 98.5, 99.0, 1000.0),
        Bar(SYMBOL, TIMEFRAME, BASE_TS - 300, 100.0, 100.5, 99.5, 100.0, 1000.0),
    ]
    BarCache.save_bars(bars)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Active Trader",):
            dock.hide()
    qapp.processEvents()
    return win


def _load(win, now_ts: int) -> None:
    win._now_ts = lambda: now_ts
    win.symbol_input.setText(SYMBOL)
    win.tf_combo.setCurrentText(TIMEFRAME)
    win.load_chart()


def _live_tick(win, ts: int, price: float) -> None:
    """One 5-second realtime push straight into the window's slot."""
    win._on_realtime_bar(
        4242, ts, price - 0.2, price + 0.2, price - 0.3, price, 100.0, price, 5
    )


def test_d27_1_no_phantom_alarm_after_finalize(monkeypatch, qapp):
    """Live ticks advance the price; finalize must not rewind it.

    Alarm at 105 sits between the stale historical close (100) and the live
    price (110). After finalize + one more tick, the alarm must NOT fire:
    the (prev, curr) pair evaluated is the continuous live pair (110, 111),
    not the rewound (100, 111).
    """
    _clear(SYMBOL, TIMEFRAME)
    _seed_history()
    win = _make_window(monkeypatch, qapp)
    _load(win, BASE_TS + 10_000)
    assert win._last_chart_price == 100.0
    assert win._rt_req_id == 4242

    # No alarms while live ticks advance the price 102 -> 110.
    win._current_alarms = []
    for i, price in enumerate((102.0, 104.0, 106.0, 108.0, 110.0)):
        _live_tick(win, BASE_TS + 5 * (i + 1), price)
    assert win._last_chart_price == 110.0

    # The user now arms an alarm between the stale close and the live price.
    alarm = Alarm(
        id=None, symbol=SYMBOL, price=105.0, direction="cross_above",
        active=True,
    )
    win._current_alarms = [alarm]

    # The backfill wave finalises (empty wave: cache was already current).
    win._pending_bars = []
    win._finalize_history_wave()

    # The live forming bar must survive the finalize full-refresh.
    assert win.chart_panel._bars, "chart was wiped by finalize"
    assert win.chart_panel._bars[-1].close == 110.0

    # One more live tick: continuous pair (110, 111) -> no cross of 105.
    _live_tick(win, BASE_TS + 30, 111.0)
    assert alarm.triggered is False, (
        "PHANTOM TRIGGER: alarm fired on the rewound (100, 111) pair"
    )
    assert win._last_chart_price == 111.0


def test_d27_1_last_chart_price_never_moves_backward(monkeypatch, qapp):
    """Direct unit assertion of the never-move-backward rule."""
    _clear(SYMBOL, TIMEFRAME)
    _seed_history()
    win = _make_window(monkeypatch, qapp)
    _load(win, BASE_TS + 10_000)

    win._current_alarms = []
    _live_tick(win, BASE_TS + 5, 110.0)
    assert win._last_chart_price == 110.0

    win._pending_bars = []
    win._finalize_history_wave()
    assert win._last_chart_price == 110.0, (
        f"_last_chart_price rewound to {win._last_chart_price}"
    )
