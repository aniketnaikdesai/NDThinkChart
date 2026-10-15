"""D27.6 — subscribe reqPositions + reqAccountSummary on connect.

The whole account/position signal chain existed but ``reqPositions`` /
``reqAccountSummary`` were called nowhere, so the portfolio panel was
permanently empty and a trader could not cross-check what the broker holds.

AC-D27.6: on connect the subs are issued and the panel populates; when
unsubscribed the "account data unavailable" state shows.
"""

from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _stub_account_calls(win, monkeypatch):
    calls: dict = {}

    def req_positions():
        calls["reqPositions"] = True

    def req_account_summary(req_id, group, tags):
        calls["reqAccountSummary"] = (req_id, group, tags)

    monkeypatch.setattr(win.ib_client, "reqPositions", req_positions)
    monkeypatch.setattr(
        win.ib_client, "reqAccountSummary", req_account_summary)
    return calls


def test_d27_6_connect_issues_account_subscriptions(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    calls = _stub_account_calls(win, monkeypatch)

    win._on_connected()

    assert calls.get("reqPositions") is True, "reqPositions not issued"
    assert "reqAccountSummary" in calls, "reqAccountSummary not issued"
    req_id, group, tags = calls["reqAccountSummary"]
    assert group == "All"
    for tag in ("AccountType", "NetLiquidation", "TotalCashValue"):
        assert tag in tags
    assert win._account_subscribed is True


def test_d27_6_account_summary_populates_panel(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, "DU123", "AccountType", "DEMO")
    bridge.account_summary.emit(4242, "DU123", "NetLiquidation", "100000")
    bridge.account_summary_end.emit(4242)
    qapp.processEvents()

    text = win.portfolio_panel.account_detail.text()
    assert "100000" in text, f"panel did not populate: {text!r}"


def test_d27_6_positions_populate_panel(monkeypatch, qapp):
    """A position update reaches the portfolio panel once subscribed."""
    from ibapi.contract import Contract

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    contract = Contract()
    contract.symbol = "HELD"
    contract.localSymbol = "HELD"
    contract.conId = 999
    contract.multiplier = "1"
    win.ib_client.bridge.position_update.emit("DU123", contract, 10.0, 40.0)
    qapp.processEvents()

    assert any(p.symbol == "HELD" for p in win.portfolio_panel._positions)


def test_d27_6_disconnect_shows_unavailable(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()
    assert win._account_subscribed is True

    win._on_disconnected()

    assert win._account_subscribed is False
    text = win.portfolio_panel.account_detail.text()
    assert "unavailable" in text.lower(), f"no unavailable state: {text!r}"
