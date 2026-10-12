"""D26.3 (labelling branch): the Set Stop-Loss/Take-Profit dialog must state
plainly that it places no orders — it only records target prices locally.

AC-D26.3 (labelling branch): dialog text asserts non-transmission.
"""

from PyQt6.QtWidgets import QLabel

from ui.stop_loss_target_dialog import StopLossTargetDialog


def _label_texts(dlg):
    return " ".join(w.text() for w in dlg.findChildren(QLabel)).lower()


def test_sltp_dialog_discloses_no_order_transmission(qapp):
    dlg = StopLossTargetDialog(symbol="AAPL", market_price=150.0)
    texts = _label_texts(dlg)
    assert "does not place" in texts or "no orders" in texts, (
        f"dialog must disclose non-transmission; labels were: {texts!r}"
    )


def test_sltp_dialog_warns_no_protective_orders(qapp):
    dlg = StopLossTargetDialog(symbol="AAPL", market_price=150.0)
    texts = _label_texts(dlg)
    assert "no protective" in texts or "not protected" in texts, (
        f"dialog must warn the position is unprotected; labels were: {texts!r}"
    )
