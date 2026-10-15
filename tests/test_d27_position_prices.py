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

from ibkr.client import IBApiClient
from ui.watchlist_panel import TICK_LAST


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
    return SimpleNamespace(
        symbol="HELD",
        localSymbol="HELD",
        conId=12345,
        multiplier="1",
        lastDateOrMonth="",
        strike=0.0,
        putCall="",
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
