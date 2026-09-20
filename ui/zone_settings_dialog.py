"""Zone (Rectangle) settings dialog — D12.

Double-click on a zone opens this modal with four tabs: Style / Text /
Coordinates / Visibility. The reference app's "Extend" dropdown is omitted —
the zone always extends both sides (Q24).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QSpinBox,
    QTabWidget, QVBoxLayout, QWidget,
)

from ui.drawing_settings_common import (
    ColorSwatchButton, TextTab, VisibilityTab,
)


class ZoneSettingsDialog(QDialog):
    def __init__(self, drawing, parent=None):
        super().__init__(parent)
        self._drawing = drawing
        self.setWindowTitle("Rectangle")
        self.setModal(True)
        self.resize(360, 300)

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.tabs.addTab(self._build_style_tab(), "Style")
        self.tabs.addTab(TextTab(default_size=14), "Text")
        self.tabs.addTab(self._build_coords_tab(), "Coordinates")
        self.tabs.addTab(VisibilityTab(), "Visibility")

        btns = QHBoxLayout()
        btns.addStretch()
        from PyQt6.QtWidgets import QPushButton
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        root.addLayout(btns)

        self._load_from_drawing()

    # ── Tabs ────────────────────────────────────────────────────────────────

    def _build_style_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        # NOTE: no "Extend" control — zone always extends both sides (Q24)

        border_row = QHBoxLayout()
        border_row.addWidget(QLabel("Border"))
        self.border_swatch = ColorSwatchButton()
        border_row.addWidget(self.border_swatch)
        border_row.addStretch()
        layout.addLayout(border_row)

        mid_row = QHBoxLayout()
        self.middle_check = QCheckBox("Middle line")
        self.middle_swatch = ColorSwatchButton("#a855f7")
        mid_row.addWidget(self.middle_check)
        mid_row.addWidget(self.middle_swatch)
        mid_row.addStretch()
        layout.addLayout(mid_row)

        bg_row = QHBoxLayout()
        self.bg_check = QCheckBox("Background")
        self.bg_check.setChecked(True)
        self.bg_swatch = ColorSwatchButton()
        bg_row.addWidget(self.bg_check)
        bg_row.addWidget(self.bg_swatch)
        bg_row.addStretch()
        layout.addLayout(bg_row)
        layout.addStretch()
        return page

    def _build_coords_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.price1 = QDoubleSpinBox()
        self.price1.setRange(-1e9, 1e9)
        self.price1.setDecimals(2)
        self.price1.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.bar1 = QSpinBox()
        self.bar1.setRange(-10_000_000, 10_000_000)
        self.price2 = QDoubleSpinBox()
        self.price2.setRange(-1e9, 1e9)
        self.price2.setDecimals(2)
        self.price2.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.bar2 = QSpinBox()
        self.bar2.setRange(-10_000_000, 10_000_000)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("#1 (price, bar)"))
        r1.addWidget(self.price1)
        r1.addWidget(self.bar1)
        layout.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("#2 (price, bar)"))
        r2.addWidget(self.price2)
        r2.addWidget(self.bar2)
        layout.addLayout(r2)
        layout.addStretch()
        return page

    # ── State round-trip ────────────────────────────────────────────────────

    def _load_from_drawing(self):
        payload = getattr(self._drawing, "payload", {}) or {}
        color = getattr(self._drawing, "color", None) or "#38bdf8"
        self.border_swatch.setColor(color)
        self.bg_swatch.setColor(color)
        style = payload.get("style", {}) or {}
        self.middle_check.setChecked(bool(style.get("middle_line", False)))
        self.bg_check.setChecked(bool(style.get("background", True)))
        text_state = payload.get("text", {}) or {}
        self.tabs.widget(1).set_text_state(text_state)
        vis_state = payload.get("visibility", {}) or {}
        self.tabs.widget(3).set_visibility(vis_state)
        self.price1.setValue(float(payload.get("y1", 0.0)))
        self.price2.setValue(float(payload.get("y2", 0.0)))
        self.bar1.setValue(int(payload.get("x1", 0)))
        self.bar2.setValue(int(payload.get("x2", 0)))

    def get_updated_drawing(self):
        """Return (payload, color) reflecting the dialog state."""
        payload = dict(getattr(self._drawing, "payload", {}) or {})
        payload["y1"] = self.price1.value()
        payload["y2"] = self.price2.value()
        payload["x1"] = self.bar1.value()
        payload["x2"] = self.bar2.value()
        payload["style"] = {
            "middle_line": self.middle_check.isChecked(),
            "background": self.bg_check.isChecked(),
        }
        payload["text"] = self.tabs.widget(1).get_text_state()
        payload["visibility"] = self.tabs.widget(3).get_visibility()
        return payload, self.border_swatch.color()
