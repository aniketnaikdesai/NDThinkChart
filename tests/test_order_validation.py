"""D26.7: validate_order() gate — table-driven pure tests.

D41: the ticket-only ``_place_order`` wiring tests are dropped along with the
ticket. The gate's wiring on the RETAINED path (validate -> pacing -> transmit)
is covered by ``tests/test_d28_pacing.py`` and
``tests/test_d28_6_close_contracts.py``.

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


def test_max_order_notional_is_owner_approved_25000():
    """Pin the money number: the notional cap must be exactly the owner-approved
    USD 25,000 (plan §7.2). Changing it requires an explicit owner decision."""
    from config import settings
    assert settings.MAX_ORDER_NOTIONAL == 25000
