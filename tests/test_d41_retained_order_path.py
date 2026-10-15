"""D41 Phase-3 guard: the retained order machinery + the resolving ``ref_price``.

D41 deleted the order-entry UI but **kept** the order path that Portfolio's
Close / Close Group / Flatten All still use. Three things must stay true:

1. ``MainWindow._ref_price_for`` (decision S4) resolves from both feeds that
   populate the D27.5 ``symbol -> last_price`` map — the watchlist price sink
   and a session's aggregated bar — and returns ``None`` for an unknown symbol
   (``validate_order`` then simply skips the notional check);
2. the retained close emitter's gates (S5 / AR-D41-6): a **disconnected** close
   and an **invalid** close refuse without transmitting, while a valid close
   **above** the USD 25,000 cap still transmits exactly once because it is
   risk-reducing — and a risk-*increasing* call above the cap is still rejected;
3. the retained modules import cleanly and their own suites still pass.
"""

import os
import subprocess
import sys
from pathlib import Path

from ibkr.client import IBApiClient
from ibkr.validation import validate_order


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win, None


def _seed_position(symbol="AAPL", qty=10.0, avg_cost=100.0):
    from data.db import db
    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO positions (symbol, account, con_id, contract_type, qty,"
        " avg_cost, local_symbol, multiplier, expiry, strike, right,"
        " updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (symbol, "DU123", None, "stock", qty, avg_cost, None, 1.0,
         None, None, None, 1_760_000_000),
    )
    db.conn.commit()
    return cur.lastrowid


def _clear_position(pid):
    from data.db import db
    cur = db.conn.cursor()
    cur.execute("DELETE FROM positions WHERE id=?", (pid,))
    db.conn.commit()


def test_ref_price_resolves_from_both_feeds(monkeypatch, qapp):
    """P1-T62-T11 / AC-D41.4 (S4): the retained ``ref_price`` source resolves
    from both feeds, upper-case normalised, and is ``None`` when unknown."""
    from data.models import Bar
    from ui.ticker_session import TickerSession

    win, _ = _make_window(monkeypatch, qapp)
    try:
        assert win._ref_price_for("AAPL") is None, "nothing recorded yet"
        assert win._ref_price_for("") is None

        # (a) the watchlist price sink, wired at MainWindow:560
        assert win.watchlist_panel._price_sink == win._record_symbol_price, (
            "the watchlist sink must be the D27.5 recorder")
        win.watchlist_panel._price_sink("aapl", 150.25)
        assert win._ref_price_for("AAPL") == 150.25
        assert win._ref_price_for("aapl") == 150.25, "reads must upper-case"

        # (b) a session aggregated bar (TickerSession:647)
        session = TickerSession("MSFT", win)
        session._on_aggregated_bar(
            Bar(symbol="MSFT", timeframe="5 mins", ts=1_760_000_000,
                open=300.0, high=301.0, low=299.0, close=300.5,
                volume=1000.0),
            True,
        )
        assert win._ref_price_for("MSFT") == 300.5
        assert win._ref_price_for("msft") == 300.5

        # An unknown symbol yields None, so the notional check is skipped
        # rather than guessing a price.
        assert win._ref_price_for("NOPE") is None
    finally:
        win.close()


def test_retained_close_gates(monkeypatch, qapp):
    """P1-T62-T21 / AC-D41.4 (S5/AR-D41-6): the four gate cases."""
    win, _ = _make_window(monkeypatch, qapp)
    placed: list = []
    monkeypatch.setattr(win.ib_client, "placeOrder",
                        lambda *a, **k: placed.append(a))
    import ui.main_window as mw
    monkeypatch.setattr(mw.order_limiter, "try_acquire", lambda: True)

    # 1000 @ 100 = $100,000, comfortably above the $25,000 cap.
    big = _seed_position(symbol="AAPL", qty=1000.0)
    bad_symbol = _seed_position(symbol="", qty=10.0)
    zero_qty = _seed_position(symbol="AAPL", qty=0.0)
    try:
        # (1) disconnected -> refuse before the row read or any token
        win._ibkr_connected = False
        win._close_position_by_id(big)
        assert placed == [], "a disconnected close must not transmit"
        assert "not connected" in win.status_bar.currentMessage().lower()

        # (2) invalid (empty symbol / zero qty) -> refuse, no transmit
        win._ibkr_connected = True
        win._close_position_by_id(bad_symbol)
        assert placed == [], "an invalid close must not transmit"
        assert "reject" in win.status_bar.currentMessage().lower()
        win._close_position_by_id(zero_qty)
        assert placed == [], "a zero-qty close must not transmit"

        # (3) valid close ABOVE the cap -> risk-reducing, transmits exactly once
        win._record_symbol_price("AAPL", 100.0)
        win._close_position_by_id(big)
        assert len(placed) == 1, (
            "a >$25,000 risk-reducing close must still be transmittable")

        # (4) ...while a risk-INCREASING call above the cap is still rejected,
        # and the same call with risk_reducing=True is not.
        hot = validate_order(action="BUY", order_type="MKT", qty=1000.0,
                             symbol="AAPL", ref_price=100.0)
        assert any("exceeds" in p for p in hot), (
            "the notional cap must still reject risk-increasing orders")
        assert validate_order(action="BUY", order_type="MKT", qty=1000.0,
                              symbol="AAPL", ref_price=100.0,
                              risk_reducing=True) == [], (
            "risk_reducing must skip ONLY the notional cap")
    finally:
        for pid in (big, bad_symbol, zero_qty):
            _clear_position(pid)
        win.close()


def test_retained_modules_import_and_their_suites_pass():
    """P1-T62-T31 / AC-D41.4: the retained order machinery imports cleanly and
    its own suites still pass."""
    import importlib

    for mod in ("ibkr.orders", "ibkr.validation", "ibkr.id_manager"):
        importlib.import_module(mod)
    from config.settings import check_live_port
    assert callable(check_live_port)

    repo = Path(__file__).resolve().parent.parent
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_order_builders.py", "tests/test_kill_switch.py", "-q"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        "the retained order suites must still pass:\n"
        + (proc.stdout or "")[-2000:] + (proc.stderr or "")[-2000:])
