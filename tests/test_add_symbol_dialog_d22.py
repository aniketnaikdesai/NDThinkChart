"""D22-06 — AddSymbolDialog (small modal input).

Offscreen tests for ui/add_symbol_dialog.py. The dialog must provide exactly one
text field plus OK/Cancel, accept non-empty text verbatim (un-normalised),
refuse empty/whitespace input in place with an inline message, and reject on
Cancel/Esc without reporting an accepted symbol.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton

from ui.add_symbol_dialog import AddSymbolDialog


def _button_with_text(dialog, text: str):
    for btn in dialog.findChildren(QPushButton):
        if btn.text() == text:
            return btn
    return None


def test_D22_06_T01_accepts_nonempty_rejects_on_cancel(qapp):
    """AC-D22.6.1: one text field + OK/Cancel; accepts 'msft' verbatim; Cancel rejects."""
    dlg = AddSymbolDialog()

    # Exactly one text field, and both OK and Cancel buttons.
    assert len(dlg.findChildren(QLineEdit)) == 1
    ok_btn = _button_with_text(dlg, "OK")
    cancel_btn = _button_with_text(dlg, "Cancel")
    assert ok_btn is not None
    assert cancel_btn is not None

    # OK with non-empty text accepts, and the accessor returns it un-normalised.
    dlg.symbol_input.setText("msft")
    ok_btn.click()
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.symbol() == "msft"
    assert dlg.text() == "msft"
    dlg.deleteLater()

    # A fresh dialog: Cancel rejects and reports no accepted symbol.
    cancel_dlg = AddSymbolDialog()
    cancel_dlg.symbol_input.setText("msft")
    _button_with_text(cancel_dlg, "Cancel").click()
    assert cancel_dlg.result() == QDialog.DialogCode.Rejected
    assert cancel_dlg.symbol() is None
    cancel_dlg.deleteLater()

    # Esc must likewise reject.
    esc_dlg = AddSymbolDialog()
    esc_dlg.show()
    qapp.processEvents()
    esc_dlg.keyPressEvent(
        QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
    )
    assert esc_dlg.result() == QDialog.DialogCode.Rejected
    assert esc_dlg.symbol() is None
    esc_dlg.deleteLater()


def test_D22_06_T02_empty_or_whitespace_is_refused_in_place(qapp):
    """AC-D22.6.2: whitespace-only OK keeps the dialog open, shows a message, accepts nothing."""
    dlg = AddSymbolDialog()
    dlg.show()
    qapp.processEvents()

    dlg.symbol_input.setText("   ")
    _button_with_text(dlg, "OK").click()

    assert dlg.result() != QDialog.DialogCode.Accepted
    assert dlg.symbol() is None
    assert dlg.message_label.isVisible()
    assert dlg.message_label.text().strip() != ""
    # The dialog must remain open (not hide itself) on a refused OK.
    assert dlg.isVisible()

    dlg.deleteLater()
