"""D26.9: TWS order errors route to the registry + the status bar; codes
promoted; placement blocked while disconnected.

Pre-fix behaviour: _on_error only special-cased backfill reqIds; order
errors (orderId in the reqId field) got an 8-second status message while the
ticket permanently read "Submitted".

D41: the order-entry ticket is gone, so the surfaced message is the status bar
(``MainWindow._on_order_error``) and the disconnected refusal is asserted on the
retained close path.
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


def test_rejected_order_updates_registry_and_status(monkeypatch, qapp):
    # AC-D26.9: TWS 201 for a tracked orderId -> registry Rejected, surfaced.
    # D41: the ticket is gone; the surfaced message is the status bar.
    win = _make_window(monkeypatch, qapp)
    try:
        reg = _fresh_registry(monkeypatch)
        oid = _register(reg)
        win._on_error(reqId=oid, errorCode=201,
                      errorString="Order rejected - reason: price violates tick")
        assert reg.get(oid).status == "Rejected"
        msg = win.status_bar.currentMessage()
        assert "Rejected" in msg, f"rejection not surfaced: {msg!r}"
        assert "tick" in msg, f"TWS message missing from status: {msg!r}"
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


def test_close_blocked_while_disconnected(monkeypatch, qapp):
    # AC-D26.9 / D41-S5: no placement while disconnected. The retained close
    # path carries the guard now that the order-entry ticket is gone.
    from data.db import db
    win = _make_window(monkeypatch, qapp)
    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO positions (symbol, account, con_id, contract_type, qty,"
        " avg_cost, local_symbol, multiplier, expiry, strike, right,"
        " updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("AAPL", "DU123", None, "stock", 10.0, 100.0, None, 1.0,
         None, None, None, 1_760_000_000),
    )
    db.conn.commit()
    pid = cur.lastrowid
    try:
        assert win._ibkr_connected is False  # harness never connects
        calls = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda *a, **k: calls.append(a))
        win._close_position_by_id(pid)
        assert calls == [], "must not transmit while disconnected"
        assert "not connected" in win.status_bar.currentMessage().lower()
    finally:
        cur.execute("DELETE FROM positions WHERE id=?", (pid,))
        db.conn.commit()
        win.close()


@pytest.mark.parametrize("code", [201, 103, 1100, 502, 503, 509])
def test_order_and_connection_codes_promoted(code):
    assert classify_error(code) == "fatal", f"{code} must be fatal"


def test_info_codes_still_info():
    assert classify_error(2104) == "info"
    assert classify_error(2106) == "info"
