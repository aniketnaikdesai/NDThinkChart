"""D26.9: TWS order errors route to the registry + ticket; codes promoted;
order entry blocked while disconnected.

Pre-fix behaviour: _on_error only special-cased backfill reqIds; order
errors (orderId in the reqId field) got an 8-second status message while the
ticket permanently read "Submitted".
"""

import pytest

from ibkr.error_codes import classify_error
from ibkr.orders import Orders, UserOrder


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def _fresh_registry(monkeypatch):
    fresh = Orders()
    monkeypatch.setattr("ui.main_window.order_registry", fresh)
    return fresh


def _register(reg, order_id=42):
    reg.register(UserOrder(order_id=order_id, symbol="AAPL", action="BUY",
                           total_qty=10, order_type="LMT", lmt_price=150.0))
    return order_id


def test_rejected_order_updates_registry_and_ticket(monkeypatch, qapp):
    # AC-D26.9: TWS 201 for a tracked orderId -> ticket shows Rejected.
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        oid = _register(reg)
        win._on_error(reqId=oid, errorCode=201,
                      errorString="Order rejected - reason: price violates tick")
        assert reg.get(oid).status == "Rejected"
        label = win.active_trader.order_entry.status_label.text()
        assert "Rejected" in label, f"ticket not updated: {label!r}"
        assert "tick" in label, f"TWS message missing from ticket: {label!r}"
    finally:
        win.close()


def test_cancelled_order_updates_registry(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        oid = _register(reg, order_id=43)
        win._on_error(reqId=oid, errorCode=202,
                      errorString="Order Canceled - reason:")
        assert reg.get(oid).status == "Cancelled"
    finally:
        win.close()


def test_non_order_error_untouched(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        oid = _register(reg)
        win._on_error(reqId=9999, errorCode=2105,
                      errorString="Data farm connection is broken")
        assert reg.get(oid).status == "", "unrelated error must not touch orders"
    finally:
        win.close()


def test_order_entry_blocked_while_disconnected(monkeypatch, qapp):
    # AC-D26.9: no placement while disconnected.
    win = _make_window(monkeypatch, qapp)
    try:
        assert win._ibkr_connected is False  # harness never connects
        calls = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda *a, **k: calls.append(a))
        win._place_order(contract=object(), symbol="AAPL", action="BUY",
                         qty=10, order_type="MKT", lmt_price=0.0,
                         stop_price=0.0, target_price=0.0)
        assert calls == [], "must not transmit while disconnected"
        assert "not connected" in win.status_bar.currentMessage().lower()
    finally:
        win.close()


@pytest.mark.parametrize("code", [201, 103, 1100, 502, 503, 509])
def test_order_and_connection_codes_promoted(code):
    assert classify_error(code) == "fatal", f"{code} must be fatal"


def test_info_codes_still_info():
    assert classify_error(2104) == "info"
    assert classify_error(2106) == "info"
