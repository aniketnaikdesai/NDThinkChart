"""Zoom control cluster — outlined top-right widget."""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal


class ChartControls(QFrame):
    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()
    magnify_toggled = pyqtSignal(bool)
    reset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ChartControls")
        self.setStyleSheet(
            "QFrame#ChartControls { border: 1px solid #4b5563; border-radius: 6px; background-color: rgba(30,30,30,180); }"
            "QPushButton { min-width: 28px; min-height: 24px; padding: 2px 6px; border: none; background: transparent; color: #e5e7eb; font-size: 14px; font-weight: 700; }"
            "QPushButton#Magnifier { font-size: 21px; }"
            "QPushButton:hover { background: rgba(75,85,99,0.5); border-radius: 4px; }"
            "QPushButton:checked { background: rgba(59,130,246,0.5); border-radius: 4px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        self.btn_minus = QPushButton("−", self)
        self.btn_minus.setToolTip("Zoom out")
        self.btn_minus.clicked.connect(self.zoom_out.emit)

        self.btn_plus = QPushButton("+", self)
        self.btn_plus.setToolTip("Zoom in")
        self.btn_plus.clicked.connect(self.zoom_in.emit)

        self.btn_magnify = QPushButton("⌕", self)
        self.btn_magnify.setObjectName("Magnifier")
        self.btn_magnify.setCheckable(True)
        self.btn_magnify.setToolTip("Magnifier (drag to zoom)")
        self.btn_magnify.toggled.connect(self.magnify_toggled.emit)

        self.btn_reset = QPushButton("Reset", self)
        self.btn_reset.setToolTip("Reset view")
        self.btn_reset.clicked.connect(self.reset.emit)

        for btn in (self.btn_minus, self.btn_plus, self.btn_magnify, self.btn_reset):
            layout.addWidget(btn)

        self.adjustSize()
