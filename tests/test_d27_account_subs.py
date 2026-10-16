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

    positions = win.portfolio_panel._positions
    assert any(p.symbol == "HELD" for p in positions)

    # ESC-032 / P2-T27: membership alone is INSUFFICIENT — the render throws on
    # an id-less Position (the append happens before _group_and_render) while
    # pyqtgraph's non-abort excepthook swallows the error. Assert the row was
    # actually rendered AND the position carries its real `positions.id` key.
    assert win.portfolio_panel.positions_table.rowCount() == 1
    assert win.portfolio_panel.positions_table.item(0, 0).text() == "HELD"
    held = next(p for p in positions if p.symbol == "HELD")
    assert held.id is not None


def test_d27_6_disconnect_shows_unavailable(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()
    assert win._account_subscribed is True

    win._on_disconnected()

    assert win._account_subscribed is False
    text = win.portfolio_panel.account_detail.text()
    assert "unavailable" in text.lower(), f"no unavailable state: {text!r}"


def test_p2_t34_t11_account_field_shows_subscribed_id(monkeypatch, qapp):
    """ESC-045 / AC1: the Account field shows the subscribed account id.

    IBKR never sends an 'Account' tag, so the id must come from the callback
    argument — the same id the connection badge is derived from.
    """
    from ui.main_window import conn_badge_text

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, "U13148604", "NetLiquidation", "100000")
    bridge.account_summary.emit(4242, "U13148604", "TotalCashValue", "25000")
    qapp.processEvents()

    text = win.portfolio_panel.account_detail.text()
    assert "Account: U13148604" in text, f"Account field not populated: {text!r}"
    assert "100000" in text and "25000" in text, f"values missing: {text!r}"

    # The same id drives the connection badge (no second source of truth).
    assert win._account_id == "U13148604"
    expected_badge, _ = conn_badge_text(
        win._account_id, win._account_summary.get("AccountType"))
    assert win.conn_badge.text() == expected_badge


def test_p2_t34_t21_no_fabrication_and_states(monkeypatch, qapp):
    """ESC-045 / AC2: untouched paths — disconnected, unavailable, no fabrication."""
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    # (a) Before any summary the disconnected text is unchanged.
    assert win.portfolio_panel.account_detail.text() == (
        "Account summary — disconnected")

    # (b) A summary with values but a genuinely unknown account id still shows
    # the '—' fallback — never a fabricated id.
    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, "", "NetLiquidation", "100000")
    bridge.account_summary.emit(4242, "", "TotalCashValue", "25000")
    qapp.processEvents()
    text = win.portfolio_panel.account_detail.text()
    assert "Account: —" in text, f"fabricated account id: {text!r}"
    assert "100000" in text, f"values missing: {text!r}"

    # (c) D27.6 unavailable state is unchanged and shows no Account field.
    win._on_disconnected()
    text = win.portfolio_panel.account_detail.text()
    assert "unavailable" in text.lower(), f"no unavailable state: {text!r}"
    assert "Account:" not in text, f"unavailable state shows an Account field: {text!r}"
