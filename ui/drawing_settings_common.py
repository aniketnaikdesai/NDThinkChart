"""Shared widgets for drawing settings dialogs (D12 / D15).

Provides the common Text and Visibility tabs plus a color-swatch button so the
zone and horizontal-line dialogs stay consistent with the reference app.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider, QSpinBox,
    QVBoxLayout, QWidget,
)

DEFAULT_TEXT_COLOR = "#ffffff"
FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24]
ALIGN_V = ["Top", "Middle", "Bottom"]
ALIGN_H = ["Left", "Center", "Right"]

# Visibility rows from the reference: (label, min, max) or None for plain checkbox
VISIBILITY_ROWS = [
    ("Seconds", 1, 59),
    ("Minutes", 1, 59),
    ("Hours", 1, 24),
    ("Days", 1, 366),
    ("Weeks", 1, 52),
    ("Months", 1, 12),
]


class ColorSwatchButton(QPushButton):
    """Small button showing a solid line in the current color; opens QColorDialog."""

    def __init__(self, color: str = DEFAULT_TEXT_COLOR, dashed: bool = False, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._dashed = dashed
        self.setFixedWidth(56)
        self.setFixedHeight(22)
        self.clicked.connect(self._pick)
        self._refresh()

    def color(self) -> str:
        return self._color.name()

    def setColor(self, color: str):
        self._color = QColor(color)
        self._refresh()

    def _pick(self):
        chosen = QColorDialog.getColor(self._color, self, "Choose color")
        if chosen.isValid():
            self._color = chosen
            self._refresh()

    def _refresh(self):
        style = (
            f"QPushButton {{ background-color: {self._color.name()}; border: 1px solid #4b5563;"
            f" border-radius: 3px; }}"
        )
        self.setStyleSheet(style)


class TextTab(QWidget):
    """Text tab: color, size, bold/italic, text, alignment (per reference)."""

    def __init__(self, parent=None, default_size: int = 14):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.color_swatch = ColorSwatchButton(DEFAULT_TEXT_COLOR)
        self.size_combo = QComboBox()
        self.size_combo.addItems([str(s) for s in FONT_SIZES])
        self.size_combo.setCurrentText(str(default_size))
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedWidth(28)
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedWidth(28)
        row.addWidget(self.color_swatch)
        row.addWidget(self.size_combo)
        row.addWidget(self.bold_btn)
        row.addWidget(self.italic_btn)
        row.addStretch()
        layout.addLayout(row)

        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Add text")
        self.text_edit.setMinimumHeight(60)
        layout.addWidget(self.text_edit)

        align_row = QHBoxLayout()
        align_row.addWidget(QLabel("Text alignment"))
        self.align_v = QComboBox()
        self.align_v.addItems(ALIGN_V)
        self.align_v.setCurrentText("Top")
        self.align_h = QComboBox()
        self.align_h.addItems(ALIGN_H)
        self.align_h.setCurrentText("Right")
        align_row.addWidget(self.align_v)
        align_row.addWidget(self.align_h)
        align_row.addStretch()
        layout.addLayout(align_row)

    def get_text_state(self) -> dict:
        return {
            "color": self.color_swatch.color(),
            "size": int(self.size_combo.currentText()),
            "bold": self.bold_btn.isChecked(),
            "italic": self.italic_btn.isChecked(),
            "text": self.text_edit.text(),
            "align_v": self.align_v.currentText(),
            "align_h": self.align_h.currentText(),
        }

    def set_text_state(self, state: dict):
        if not state:
            return
        self.color_swatch.setColor(state.get("color", DEFAULT_TEXT_COLOR))
        size = str(state.get("size", 14))
        idx = self.size_combo.findText(size)
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)
        self.bold_btn.setChecked(bool(state.get("bold", False)))
        self.italic_btn.setChecked(bool(state.get("italic", False)))
        self.text_edit.setText(state.get("text", ""))
        for combo, key, default in ((self.align_v, "align_v", "Top"), (self.align_h, "align_h", "Right")):
            idx = combo.findText(state.get(key, default))
            if idx >= 0:
                combo.setCurrentIndex(idx)


class VisibilityTab(QWidget):
    """Visibility tab: Ticks + time-frame rows with min/max sliders + Ranges."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.checks = {}

        self.checks["Ticks"] = QCheckBox("Ticks")
        self.checks["Ticks"].setChecked(True)
        layout.addWidget(self.checks["Ticks"])

        self.sliders = {}
        self.value_edits = {}
        for label, lo, hi in VISIBILITY_ROWS:
            row = QHBoxLayout()
            cb = QCheckBox(label)
            cb.setChecked(True)
            self.checks[label] = cb
            spin_lo = QSpinBox()
            spin_lo.setRange(lo, hi)
            spin_lo.setValue(lo)
            spin_lo.setFixedWidth(60)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(lo, hi)
            slider.setValue(lo)
            spin_hi = QSpinBox()
            spin_hi.setRange(lo, hi)
            spin_hi.setValue(hi)
            spin_hi.setFixedWidth(60)
            row.addWidget(cb, 1)
            row.addWidget(spin_lo)
            row.addWidget(slider, 1)
            row.addWidget(spin_hi)
            layout.addLayout(row)
            self.sliders[label] = (slider, spin_lo, spin_hi)

        self.checks["Ranges"] = QCheckBox("Ranges")
        self.checks["Ranges"].setChecked(True)
        layout.addWidget(self.checks["Ranges"])
        layout.addStretch()

    def get_visibility(self) -> dict:
        state = {name: cb.isChecked() for name, cb in self.checks.items()}
        for name, (slider, lo, hi) in self.sliders.items():
            state[f"{name}_lo"] = lo.value()
            state[f"{name}_hi"] = hi.value()
        return state

    def set_visibility(self, state: dict):
        if not state:
            return
        for name, cb in self.checks.items():
            if name in state:
                cb.setChecked(bool(state[name]))
        for name, (slider, lo, hi) in self.sliders.items():
            if f"{name}_lo" in state:
                lo.setValue(int(state[f"{name}_lo"]))
                slider.setMinimum(int(state[f"{name}_lo"]))
            if f"{name}_hi" in state:
                hi.setValue(int(state[f"{name}_hi"]))
                slider.setMaximum(int(state[f"{name}_hi"]))
