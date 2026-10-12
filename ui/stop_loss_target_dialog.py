"""
stop_loss_target_dialog.py
Dialog for setting stop-loss and take-profit prices for positions or groups.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class StopLossTargetDialog(QDialog):
    """Dialog to set stop-loss and take-profit for a position or trade group."""

    # Signal emitted when user confirms: (apply_type, target_id, stop_price, target_price)
    # apply_type: 'position' or 'group'
    # target_id: position ID or group ID
    # stop_price, target_price: floats (or None if not set)
    confirmed = pyqtSignal(str, int, float, float)

    def __init__(self, symbol: str, market_price: float, parent=None):
        """
        Args:
            symbol: The symbol (for display)
            market_price: Current market price (for validation)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(f"Set Stop-Loss / Take-Profit — {symbol}")
        self.setModal(True)
        self._symbol = symbol
        self._market_price = market_price

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel(
            f"Set stop-loss and take-profit levels for {symbol}\n"
            f"Current market price: {market_price:.2f}"
        )
        header.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        layout.addWidget(header)

        # D26.3 (labelling branch): this dialog records target prices locally
        # only — it does NOT transmit orders. Say so plainly; a user who sets
        # levels here and walks away must know the position is not protected.
        notice = QLabel(
            "Note: this saves target prices locally only — it does NOT place "
            "stop-loss or take-profit orders with your broker. The position "
            "has no protective orders until real legs are transmitted."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet("color: #fbbf24; font-weight: 600;")
        notice.setObjectName("NoOrdersNotice")
        layout.addWidget(notice)

        # Form layout
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        # Apply to selector
        self.apply_to_combo = QComboBox()
        self.apply_to_combo.addItems(["Position", "Trade Group"])
        form.addRow("Apply to:", self.apply_to_combo)

        # Target ID (will be set by caller)
        self.target_id_label = QLabel("—")
        self.target_id_label.setStyleSheet("font-family: monospace;")
        form.addRow("Target ID:", self.target_id_label)

        # Stop price
        self.stop_input = QLineEdit()
        self.stop_input.setPlaceholderText("e.g. 145.00")
        self.stop_input.setToolTip("Stop-loss price")
        form.addRow("Stop Price:", self.stop_input)

        # Target price
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g. 160.00")
        self.target_input.setToolTip("Take-profit price")
        form.addRow("Target Price:", self.target_input)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("Set Levels")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)

        # Initially disable OK until target_id is set
        self.ok_btn.setEnabled(False)

    def set_target_info(self, apply_type: str, target_id: int, target_label: str = ""):
        """
        Set the target position/group for which we're setting SL/TP.

        Args:
            apply_type: 'position' or 'group'
            target_id: The ID of the position or group
            target_label: Optional descriptive label (e.g., symbol or group name)
        """
        self._apply_type = apply_type  # 'position' or 'group'
        self._target_id = target_id
        self.target_id_label.setText(f"{target_id} ({target_label})")
        self.ok_btn.setEnabled(True)

    def _validate_and_accept(self):
        """Validate inputs and emit confirmed signal if valid."""
        try:
            stop_text = self.stop_input.text().strip()
            target_text = self.target_input.text().strip()

            stop_price = float(stop_text) if stop_text else None
            target_price = float(target_text) if target_text else None

            # Validate that at least one is set
            if stop_price is None and target_price is None:
                QMessageBox.warning(
                    self,
                    "Input Required",
                    "Please set at least one of Stop Price or Target Price.",
                )
                return

            # Validate stop < market < target for longs (reverse for shorts)
            # Since we don't know position direction here, we'll do basic validation
            # The actual position direction validation will happen in the caller
            # based on position.qty sign

            # Basic sanity checks
            if stop_price is not None and stop_price <= 0:
                QMessageBox.warning(
                    self,
                    "Invalid Stop Price",
                    "Stop price must be positive.",
                )
                return

            if target_price is not None and target_price <= 0:
                QMessageBox.warning(
                    self,
                    "Invalid Target Price",
                    "Target price must be positive.",
                )
                return

            # Emit confirmed signal
            self.confirmed.emit(
                self._apply_type, self._target_id, stop_price or 0.0, target_price or 0.0
            )
            self.accept()

        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter valid numeric values for prices.",
            )