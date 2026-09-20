"""Horizontal line settings dialog — D15.

Double-click on a horizontal line opens this modal with four tabs:
Style / Text / Coordinates / Visibility. Style shows only a "Line" swatch;
Coordinates has a single "#1 (price)" field (no bar), per the reference.
"""

from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QDoubleSpinBox, QSpinBox, QPushButton,
    QTabWidget, QVBoxLayout, QWidget,
)

from ui.drawing_settings_common import ColorSwatchButton, TextTab, VisibilityTab


class HorizontalLineSettingsDialog(QDialog):
    def __init__(self, drawing, parent=None):
        super().__init__(parent)
        self._drawing = drawing
        self.setWindowTitle("Horizontal line")
        self.setModal(True)
        self.resize(360, 280)

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.tabs.addTab(self._build_style_tab(), "Style")
        self.tabs.addTab(TextTab(default_size=12), "Text")
        self.tabs.addTab(self._build_coords_tab(), "Coordinates")
        self.tabs.addTab(VisibilityTab(), "Visibility")

        btns = QHBoxLayout()
        btns.addStretch()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        root.addLayout(btns)

        self._load_from_drawing()

    def _build_style_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        row.addWidget(QLabel("Line"))
        self.line_swatch = ColorSwatchButton()
        row.addWidget(self.line_swatch)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()
        return page

    def _build_coords_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        row.addWidget(QLabel("#1 (price)"))
        self.price = QDoubleSpinBox()
        self.price.setRange(-1e9, 1e9)
        self.price.setDecimals(2)
        self.price.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        row.addWidget(self.price)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()
        return page

    def _load_from_drawing(self):
        payload = getattr(self._drawing, "payload", {}) or {}
        color = getattr(self._drawing, "color", None) or "#38bdf8"
        self.line_swatch.setColor(color)
        self.tabs.widget(1).set_text_state(payload.get("text", {}) or {})
        self.tabs.widget(3).set_visibility(payload.get("visibility", {}) or {})
        self.price.setValue(float(payload.get("y", 0.0)))

    def get_updated_drawing(self):
        payload = dict(getattr(self._drawing, "payload", {}) or {})
        payload["y"] = self.price.value()
        payload["text"] = self.tabs.widget(1).get_text_state()
        payload["visibility"] = self.tabs.widget(3).get_visibility()
        return payload, self.line_swatch.color()
