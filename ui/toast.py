"""A lightweight transient notification overlaid on a parent widget."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel


class Toast(QLabel):
    def __init__(self, parent=None, duration_ms: int = 4500):
        super().__init__(parent)
        self._duration_ms = duration_ms
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setStyleSheet(
            "background: rgba(15, 23, 42, 235);"
            "color: #f8fafc;"
            "border: 1px solid #334155;"
            "border-radius: 6px;"
            "padding: 8px 14px;"
            "font-weight: 600;"
        )
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, duration_ms: int | None = None) -> None:
        self.setText(text)
        self.adjustSize()
        parent = self.parentWidget()
        if parent is not None:
            x = max((parent.width() - self.width()) // 2, 8)
            self.move(x, 12)
        self.raise_()
        self.show()
        self._timer.start(duration_ms or self._duration_ms)
