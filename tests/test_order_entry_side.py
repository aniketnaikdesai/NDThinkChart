"""D26.6: order entry must offer an explicit Buy/Sell side.

Pre-fix behaviour: _on_place hardcoded action="BUY"; the ladder recorded
_pending_ladder=("SELL", price) on ask-clicks but nothing ever read it, so
an ask-click intending to sell still bought.
"""

import pytest

from ui.active_trader_panel import OrderEntryWidget, ActiveTraderPanel


@pytest.fixture
def entry(qapp):
    w = OrderEntryWidget()
    w.enable_live_check.setChecked(True)
    return w


def _place(entry, side=None):
    """Optionally select a side, then Place -> Confirm; return payloads."""
    emitted = []
    entry.order_place_requested.connect(lambda *a: emitted.append(a))
    if side is not None:
        entry.side_combo.setCurrentText(side)
    entry._on_place()
    entry._on_confirm()
    return emitted


def test_place_defaults_to_buy(entry):
    emitted = _place(entry)
    assert emitted[0][0] == "BUY"


def test_place_with_sell_selected_transmits_sell(entry):
    # AC-D26.6: the selected side drives the transmitted action.
    emitted = _place(entry, side="SELL")
    assert len(emitted) == 1
    assert emitted[0][0] == "SELL"


def test_ladder_ask_click_selects_sell(qapp):
    # AC-D26.6: ask-click pre-selects SELL so a subsequent Place sells.
    panel = ActiveTraderPanel()
    panel._on_ladder_price_click(row=0, col=0, price=150.0)
    assert panel.order_entry.side_combo.currentText() == "SELL"


def test_ladder_bid_click_selects_buy(qapp):
    panel = ActiveTraderPanel()
    panel._on_ladder_price_click(row=0, col=2, price=149.5)
    assert panel.order_entry.side_combo.currentText() == "BUY"


def test_pending_ladder_dead_path_removed():
    # The write-only _pending_ladder must not exist anymore.
    assert not hasattr(ActiveTraderPanel(), "_pending_ladder")
