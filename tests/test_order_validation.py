"""D26.7: validate_order() gate — table-driven pure tests + _place_order wiring.

AC-D26.7: invalid input is rejected with a UI message; no placeOrder call,
no traceback.
"""

import pytest

from ibkr.validation import validate_order


def _valid(**over):
    base = dict(action="BUY", order_type="LMT", qty=100, lmt_price=150.0,
                symbol="AAPL")
    base.update(over)
    return base


@pytest.mark.parametrize("field,value", [
    ("qty", 0), ("qty", -5),
    ("lmt_price", 0.0), ("lmt_price", -1.0),
    ("symbol", ""), ("symbol", "   "),
    ("action", "HOLD"), ("order_type", "TRAIL"),
])
def test_invalid_inputs_rejected(field, value):
    problems = validate_order(**_valid(**{field: value}))
    assert problems, f"expected rejection for {field}={value!r}"


def test_stp_zero_stop_rejected():
    # The killer defect: auxPrice=0.0 triggers immediately as a market order.
    problems = validate_order(action="SELL", order_type="STP", qty=100,
                              stop_price=0.0, symbol="AAPL")
    assert problems


def test_bracket_geometry_buy():
    # BUY bracket needs stop < entry < target.
    assert validate_order(**_valid(order_type="BRACKET", stop_price=145.0,
                                   target_price=160.0)) == []
    bad = validate_order(**_valid(order_type="BRACKET", stop_price=155.0,
                                  target_price=160.0))
    assert bad, "stop above entry for a BUY bracket must be rejected"


def test_bracket_geometry_sell():
    assert validate_order(action="SELL", order_type="BRACKET", qty=100,
                          lmt_price=150.0, stop_price=155.0,
                          target_price=140.0, symbol="AAPL") == []
    bad = validate_order(action="SELL", order_type="BRACKET", qty=100,
                         lmt_price=150.0, stop_price=145.0,
                         target_price=140.0, symbol="AAPL")
    assert bad, "stop below entry for a SELL bracket must be rejected"


def test_notional_cap_enforced():
    # 1000 shares @ $150 = $150,000 > $25,000 cap.
    problems = validate_order(**_valid(qty=1000, lmt_price=150.0))
    assert any("exceeds" in p for p in problems)


def test_notional_cap_uses_ref_price_for_mkt():
    problems = validate_order(action="BUY", order_type="MKT", qty=1000,
                              symbol="AAPL", ref_price=150.0)
    assert any("exceeds" in p for p in problems)


def test_notional_cap_skipped_without_price_basis():
    # No lmt_price and no ref_price: notional cannot be computed; other
    # checks still apply, but no spurious notional rejection.
    problems = validate_order(action="BUY", order_type="MKT", qty=10,
                              symbol="AAPL")
    assert problems == []


def test_valid_mkt_order():
    assert validate_order(action="SELL", order_type="MKT", qty=10,
                          symbol="AAPL") == []


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def test_place_order_refuses_invalid_without_transmit(monkeypatch, qapp):
    # Wiring: _place_order validates FIRST — no placeOrder, message surfaced.
    win = _make_window(monkeypatch, qapp)
    try:
        win._ibkr_connected = True  # isolate the validation path
        calls = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda *a, **k: calls.append(a))
        win._place_order(contract=object(), symbol="", action="BUY", qty=0,
                         order_type="MKT", lmt_price=0.0, stop_price=0.0,
                         target_price=0.0)
        assert calls == [], "invalid order must never reach placeOrder"
        label = win.active_trader.order_entry.status_label.text()
        assert "reject" in label.lower(), f"rejection not surfaced: {label!r}"
    finally:
        win.close()


def test_place_order_transmits_valid(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        win._ibkr_connected = True  # harness never fires _on_connected
        calls = []
        monkeypatch.setattr(win.ib_client, "placeOrder",
                            lambda *a, **k: calls.append(a))
        win._place_order(contract=object(), symbol="AAPL", action="BUY",
                         qty=10, order_type="MKT", lmt_price=0.0,
                         stop_price=0.0, target_price=0.0)
        assert len(calls) == 1, "valid order must transmit exactly once"
    finally:
        win.close()
