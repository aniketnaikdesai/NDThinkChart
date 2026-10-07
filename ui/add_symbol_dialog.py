"""
add_symbol_dialog.py
Small modal dialog for entering a symbol to add to the watchlist.

Self-contained by design: it does not import from ui.watchlist_panel, so it can
be reused without pulling the panel (and its services) into scope.

The dialog exposes the text exactly as the user typed it. It never normalises
(case-folding, trimming, validation against a symbol universe, etc.) — the
caller owns that policy and applies it to ``text()`` / ``symbol()``.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class AddSymbolDialog(QDialog):
    """Prompt for a single symbol to add to the watchlist.

    Contract:
        * exactly one text field plus OK / Cancel buttons;
        * OK with non-empty (after strip) text accepts and exposes the raw,
          un-normalised text;
        * OK with empty/whitespace-only text is refused in place — the dialog
          stays open and shows an inline message;
        * Cancel or Esc rejects, and no accepted symbol is reported.
    """

    def __init__(self, parent=None, initial_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Add Symbol")
        self.setModal(True)

        self._accepted_symbol = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Symbol:"))

        self.symbol_input = QLineEdit(self)
        self.symbol_input.setPlaceholderText("e.g. AAPL")
        self.symbol_input.setText(initial_text)
        # Enter in the field behaves like clicking OK.
        self.symbol_input.returnPressed.connect(self._on_ok)
        layout.addWidget(self.symbol_input)

        self.message_label = QLabel(self)
        self.message_label.setObjectName("AddSymbolMessage")
        self.message_label.setStyleSheet("color: #f87171;")
        self.message_label.setVisible(False)
        layout.addWidget(self.message_label)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("OK", self)
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)
        button_row.addWidget(self.ok_btn)

        layout.addLayout(button_row)

    # ── Accessors ─────────────────────────────────────────────────────────────

    def text(self) -> str:
        """The raw, un-normalised text currently in the field."""
        return self.symbol_input.text()

    def symbol(self):
        """The accepted raw symbol, or ``None`` when nothing was accepted.

        Returned verbatim (not normalised) — the caller applies its own
        normalisation.
        """
        return self._accepted_symbol

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_ok(self):
        raw = self.symbol_input.text()
        if not raw.strip():
            self._accepted_symbol = None
            self.message_label.setText("Enter a symbol.")
            self.message_label.setVisible(True)
            return
        self._accepted_symbol = raw
        self.accept()
