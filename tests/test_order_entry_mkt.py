"""D26.4: Buy/Sell MKT buttons must not crash and must use the quantity input.

Pre-fix behaviour: _on_buy_mkt/_on_sell_mkt called _request_send with 5 args
against a 6-parameter signature (TypeError on click) and hardcoded qty=0.0.

Note: slots are invoked directly (not via .click()) because an unhandled
TypeError inside a Qt slot aborts the offscreen test process instead of
failing cleanly.
"""

import pytest

from ui.active_trader_panel import OrderEntryWidget


@pytest.fixture
def entry(qapp):
    w = OrderEntryWidget()
    w.enable_live_check.setChecked(True)  # allow _on_confirm to emit
    return w


def _send_mkt(entry, side):
    """Invoke the MKT slot then Confirm; return the emitted payloads."""
    emitted = []
    entry.order_place_requested.connect(lambda *a: emitted.append(a))
    if side == "BUY":
        entry._on_buy_mkt()
    else:
        entry._on_sell_mkt()
    entry._on_confirm()
    return emitted


def test_buy_mkt_transmits_spinbox_qty(entry):
    # D26.4 / AC-D26.4: no TypeError; qty comes from the spinbox.
    entry.qty_input.setValue(50)
    emitted = _send_mkt(entry, "BUY")
    assert len(emitted) == 1
    action, qty, order_type, lmt, stop, target = emitted[0]
    assert action == "BUY"
    assert qty == 50
    assert order_type == "MKT"
    assert (lmt, stop, target) == (0.0, 0.0, 0.0)


def test_sell_mkt_transmits_spinbox_qty(entry):
    entry.qty_input.setValue(25)
    emitted = _send_mkt(entry, "SELL")
    assert len(emitted) == 1
    action, qty, order_type, *_ = emitted[0]
    assert action == "SELL"
    assert qty == 25
    assert order_type == "MKT"


def test_mkt_zero_qty_refused(entry):
    # D26.4: qty<=0 must be refused, never transmitted.
    entry.qty_input.setRange(0, 100_000)
    entry.qty_input.setValue(0)
    emitted = _send_mkt(entry, "BUY")
    assert emitted == []
    assert entry._pending is None
