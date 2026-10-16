"""D27.5 — position market prices come from the position's own symbol.

Regression test: ``_on_position_update`` stamped every position with the
*chart's* ``_last_chart_price``, so any holding other than the charted symbol
showed the wrong market price and unrealized P&L.

AC-D27.5: positions in non-charted symbols show their own symbol's last
price and correct unrealized P&L.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QDockWidget

from ibapi.contract import Contract

from ibkr.client import IBApiClient
from ui.watchlist_panel import TICK_LAST


def _real_contract(**kwargs) -> Contract:
    """Build a REAL `ibapi.contract.Contract` (ESC-044 / P2-T33).

    A ``SimpleNamespace`` with invented attribute names (``class_`` /
    ``lastDateOrMonth`` / ``putCall``) could never fail on an attribute-name
    regression; the production reader must be exercised against the actual
    ibapi contract type.
    """
    contract = Contract()
    for key, value in kwargs.items():
        setattr(contract, key, value)
    return contract


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    # D41/S6: the right region is now ONE dock titled "Portfolio". Hiding it
    # keeps the window at the width this suite has always exercised. The
    # found-count guard makes a stale title a hard failure instead of a silent
    # no-op (AR-D41-3).
    hidden = 0
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
            hidden += 1
    assert hidden >= 1, "no dock titled 'Portfolio' found to hide"
    qapp.processEvents()
    return win


def _held_contract():
    # P2-T33 / ESC-044: a REAL Contract (secType 'STK'), not a fake
    # SimpleNamespace with the non-existent `lastDateOrMonth`/`putCall`.
    return _real_contract(
        symbol="HELD",
        localSymbol="HELD",
        conId=12345,
        secType="STK",
        multiplier="1",
        lastTradeDateOrContractMonth="",
        strike=0.0,
        right="",
    )


def test_d27_5_position_uses_own_symbol_price(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)

    # The chart shows CHART at 100; the position is in HELD.
    win._current_symbol = "CHART"
    win._last_chart_price = 100.0

    # HELD last trades at 50 via the watchlist feed.
    win.watchlist_panel._md_manager = SimpleNamespace(
        req_mkt_data=lambda contract: 777,
        cancel_mkt_data=lambda req_id: None,
    )
    win.watchlist_panel.add_symbol("HELD", SimpleNamespace(symbol="HELD"))
    win.watchlist_panel.on_tick_price(777, TICK_LAST, 50.0)

    captured: list = []
    monkeypatch.setattr(
        win.portfolio_panel, "add_position", lambda pos: captured.append(pos))

    win._on_position_update("DU123", _held_contract(), 10.0, 40.0)

    assert captured, "position never reached the portfolio panel"
    pos = captured[0]
    assert pos.market_price == 50.0, (
        f"position stamped with chart price: {pos.market_price}"
    )
    # Unrealized P&L = (50 - 40) * 10 * 1
    from ui.active_portfolio_panel import ActivePortfolioPanel
    assert ActivePortfolioPanel._unrealized_pnl(pos) == pytest.approx(100.0)


def test_d27_5_chart_symbol_position_uses_chart_price(monkeypatch, qapp):
    """The charted symbol's own position still prices off the chart feed."""
    win = _make_window(monkeypatch, qapp)
    win._current_symbol = "HELD"
    win._last_chart_price = 55.0
    # Simulate one aggregated bar so the central map learns HELD=55.
    from data.models import Bar
    bar = Bar("HELD", "5 mins", 1_760_000_000, 54, 56, 53, 55.0, 1000.0)
    win._on_aggregated_bar(bar, False)

    captured: list = []
    monkeypatch.setattr(
        win.portfolio_panel, "add_position", lambda pos: captured.append(pos))
    win._on_position_update("DU123", _held_contract(), 10.0, 40.0)

    assert captured[0].market_price == 55.0


def test_d27_5_unknown_symbol_falls_back_to_zero_not_chart_price(monkeypatch,
                                                                qapp):
    """No price feed for the symbol -> 0.0, never the chart's price."""
    win = _make_window(monkeypatch, qapp)
    win._current_symbol = "CHART"
    win._last_chart_price = 100.0

    captured: list = []
    monkeypatch.setattr(
        win.portfolio_panel, "add_position", lambda pos: captured.append(pos))
    win._on_position_update("DU123", _held_contract(), 10.0, 40.0)

    assert captured[0].market_price == 0.0


# ── P2-T33 / ESC-044 — real ibapi Contract attributes ────────────────────────


def test_p2_t33_option_contract_fields_persisted_and_handed(monkeypatch, qapp):
    """AC1 — an OPT Contract yields contract_type/expiry/right/strike.

    Emits through the connected window's bridge (the production signal path),
    then checks BOTH the persisted `positions` row and the Position handed to
    the panel. Pre-fix: 'stock'/None/None/sentinel -> RED.
    """
    win = _make_window(monkeypatch, qapp)
    win._current_symbol = "SPXW"

    contract = _real_contract(
        secType="OPT",
        symbol="SPX",
        localSymbol="SPXW  261016P05900000",
        conId=987654,
        multiplier="100",
        lastTradeDateOrContractMonth="261016",
        right="P",
        strike=5900.0,
    )

    captured: list = []
    monkeypatch.setattr(
        win.portfolio_panel, "add_position", lambda pos: captured.append(pos))

    win.ib_client.bridge.position_update.emit("DU123", contract, 10.0, 40.0)

    assert captured, "position never reached the portfolio panel"
    pos = captured[0]
    assert pos.contract_type == "option", pos.contract_type
    assert pos.expiry == "261016", pos.expiry
    assert pos.right == "P", pos.right
    assert pos.strike == pytest.approx(5900.0), pos.strike

    from data.db import db

    cur = db.conn.cursor()
    cur.execute(
        "SELECT contract_type, expiry, right, strike FROM positions "
        "WHERE con_id=?",
        (987654,),
    )
    row = cur.fetchone()
    assert row is not None, "position was not persisted"
    assert row[0] == "option", row
    assert row[1] == "261016", row
    assert row[2] == "P", row
    assert row[3] == pytest.approx(5900.0), row


def test_p2_t33_no_sentinel_and_panel_vocabulary(monkeypatch, qapp):
    """AC2 — UNSET_DOUBLE strike -> None; STK/FUT -> 'stock'/'future'."""
    import sys

    win = _make_window(monkeypatch, qapp)

    captured: list = []
    monkeypatch.setattr(
        win.portfolio_panel, "add_position", lambda pos: captured.append(pos))

    # (a) option whose strike is ibapi's UNSET_DOUBLE sentinel.
    sentinel_contract = _real_contract(
        secType="OPT",
        symbol="SPX",
        localSymbol="SPXW  UNSET",
        conId=1,
        multiplier="100",
        lastTradeDateOrContractMonth="261016",
        right="C",
        strike=sys.float_info.max,
    )
    win.ib_client.bridge.position_update.emit(
        "DU123", sentinel_contract, 1.0, 1.0)
    assert captured[-1].strike is None, captured[-1].strike

    from data.db import db

    cur = db.conn.cursor()
    cur.execute("SELECT strike FROM positions WHERE con_id=?", (1,))
    stored = cur.fetchone()
    assert stored is not None and stored[0] is None, stored

    # (b) stock.
    stock = _real_contract(
        secType="STK",
        symbol="AAPL",
        localSymbol="AAPL",
        conId=2,
        multiplier="",
        lastTradeDateOrContractMonth="",
        strike=0.0,
        right="",
    )
    win.ib_client.bridge.position_update.emit("DU123", stock, 1.0, 1.0)
    assert captured[-1].contract_type == "stock", captured[-1].contract_type

    # (c) future.
    future = _real_contract(
        secType="FUT",
        symbol="ES",
        localSymbol="ESZ6",
        conId=3,
        multiplier="50",
        lastTradeDateOrContractMonth="20261218",
        strike=0.0,
        right="",
    )
    win.ib_client.bridge.position_update.emit("DU123", future, 1.0, 1.0)
    assert captured[-1].contract_type == "future", captured[-1].contract_type


def test_p2_t33_options_render_option_and_group(monkeypatch, qapp):
    """AC3 — two option legs render Type=OPTION and populate Strategy/Group.

    Pre-fix: every leg was persisted 'stock', so `_group_and_render` never saw
    `contract_type == 'option'`, Type read STOCK and Strategy/Group stayed '—'.
    """
    win = _make_window(monkeypatch, qapp)
    win._current_symbol = "SPXW"

    # Short higher put + long lower put = PCS credit spread, same expiry.
    short_put = _real_contract(
        secType="OPT",
        symbol="SPX",
        localSymbol="SPXW  261016P05900000",
        conId=1001,
        multiplier="100",
        lastTradeDateOrContractMonth="261016",
        right="P",
        strike=5900.0,
    )
    long_put = _real_contract(
        secType="OPT",
        symbol="SPX",
        localSymbol="SPXW  261016P05850000",
        conId=1002,
        multiplier="100",
        lastTradeDateOrContractMonth="261016",
        right="P",
        strike=5850.0,
    )

    win.ib_client.bridge.position_update.emit("DU123", short_put, -1.0, 5.0)
    win.ib_client.bridge.position_update.emit("DU123", long_put, 1.0, 3.0)

    table = win.portfolio_panel.positions_table
    assert table.rowCount() == 2, table.rowCount()
    types = [table.item(row, 3).text() for row in range(table.rowCount())]
    assert types == ["OPTION", "OPTION"], types
    strategies = [table.item(row, 8).text() for row in range(table.rowCount())]
    groups = [table.item(row, 9).text() for row in range(table.rowCount())]
    assert all(s != "—" for s in strategies), strategies
    assert all(g != "—" for g in groups), groups
    assert set(strategies) == {"PCS"}, strategies
    assert set(groups) == {"PCS 261016"}, groups
