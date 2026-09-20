"""
studies_dialog.py
Modal dialog for toggling and configuring chart studies.
Emits studies_changed(list[dict]) when confirmed.
"""

from copy import deepcopy
from typing import List

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSpinBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QScrollArea, QWidget, QComboBox, QColorDialog
)


# Default study configuration
DEFAULT_STUDIES = [
    {"type": "sma",       "label": "SMA",           "enabled": False, "params": {"period": 20,  "source": "close", "color": "#f59e0b"}},
    {"type": "ema",       "label": "EMA",            "enabled": False, "params": {"period": 9,   "source": "close", "color": "#818cf8"}},
    {"type": "ema2",      "label": "EMA 2",          "enabled": False, "params": {"period": 21,  "source": "close", "color": "#c084fc"}},
    {"type": "vwap",      "label": "VWAP",           "enabled": False, "params": {"color": "#34d399"}},
    {"type": "bollinger", "label": "Bollinger Bands","enabled": False, "params": {"period": 20, "std_dev": 2.0, "color": "#60a5fa"}},
    {"type": "rsi",       "label": "RSI",            "enabled": False, "params": {"period": 14, "overbought": 70, "oversold": 30}},
    {"type": "macd",      "label": "MACD",           "enabled": False, "params": {"fast": 12, "slow": 26, "signal": 9}},
    {"type": "rth_gaps",  "label": "RTH Gaps",       "enabled": False, "params": {"extendBars": 20, "minTicks": 1, "maxGaps": 10}},
    {"type": "vix_sd",    "label": "VIX Expected Move","enabled": False,
     "params": {"sdDivisor": 15.87, "anchorSource": "prev_close", "showAnchor": True,
                "showSd05": True, "showSd1": True, "showSd2": True, "showSd3": False,
                "color05": "#94a3b8", "color1": "#38bdf8", "color2": "#f59e0b",
                "color3": "#c084fc"}},
    {"type": "ict",       "label": "ICT Concepts",   "enabled": False,
     "params": {"showMS": True, "msLength": 5, "showMSS": True, "showBOS": True,
                "showOB": True, "obLength": 10, "useBody": True,
                "showFVG": True, "showBPR": True, "showLiquidity": True,
                "showVI": True, "showNWOG": True, "showNDOG": True,
                "showDisplacement": False, "showKillzones": False,
                "cMSSBull": "#00e6a1", "cMSSBear": "#e60400",
                "cBullOB": "#3e89fa", "cBearOB": "#ff3131",
                "cFVGBull": "#00e676", "cFVGBear": "#ff5252",
                "cLiqBuy": "#fa451c", "cLiqSell": "#1ce4fa",
                "cNWOG": "#ff5252", "cNDOG": "#ff9800"}},
]


class StudyRow(QWidget):
    """One study as a checkable QGroupBox holding its param fields."""

    def __init__(self, study: dict, parent=None):
        super().__init__(parent)
        self._study = study

        group = QGroupBox(study["label"])
        group.setCheckable(True)
        group.setChecked(study["enabled"])
        self.group = group

        form = QFormLayout(group)
        form.setContentsMargins(8, 4, 8, 6)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._param_widgets: dict = {}
        self._color_widgets: dict = {}
        for key, val in study.get("params", {}).items():
            looks_like_color = (isinstance(val, str) and
                                (val.startswith("#") or val.startswith("rgba(")))
            if "color" in key or looks_like_color:
                swatch = QPushButton()
                swatch.setFixedSize(46, 22)
                swatch.setCursor(Qt.CursorShape.PointingHandCursor)
                self._set_swatch(swatch, val)
                swatch.clicked.connect(
                    lambda _checked=False, k=key: self._pick_color(k)
                )
                self._color_widgets[key] = swatch
                form.addRow(self._label_text(key), swatch)
                continue
            if isinstance(val, bool):
                widget = QCheckBox()
                widget.setChecked(val)
                self._param_widgets[key] = widget
            elif isinstance(val, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.01, 100.0)
                widget.setSingleStep(0.5)
                widget.setValue(val)
                self._param_widgets[key] = widget
            elif isinstance(val, int):
                widget = QSpinBox()
                widget.setRange(1, 500)
                widget.setValue(val)
                self._param_widgets[key] = widget
            elif isinstance(val, str):
                widget = QComboBox()
                if key == "anchorSource":
                    widget.addItems(["prev_close", "session_open"])
                else:
                    widget.addItem(val)
                widget.setCurrentText(val)
                self._param_widgets[key] = widget
            form.addRow(self._label_text(key), widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(group)

    @staticmethod
    def _label_text(key: str) -> str:
        return key.replace("_", " ").title() + ":"

    @staticmethod
    def _set_swatch(swatch: QPushButton, color: str) -> None:
        swatch.setToolTip(color)
        swatch.setStyleSheet(
            f"background: {color}; border: 1px solid #334155; border-radius: 3px;"
        )

    def _pick_color(self, key: str):
        swatch = self._color_widgets[key]
        current = swatch.toolTip()
        chosen = QColorDialog.getColor(
            QColor(current) if current else Qt.GlobalColor.white, self,
            f"Choose color: {key}",
        )
        if chosen.isValid():
            hex_color = chosen.name()
            self._set_swatch(swatch, hex_color)
            swatch.setToolTip(hex_color)

    def get_config(self) -> dict:
        cfg = deepcopy(self._study)
        cfg["enabled"] = self.group.isChecked()
        for key, widget in self._param_widgets.items():
            if isinstance(widget, QCheckBox):
                cfg["params"][key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                cfg["params"][key] = widget.currentText()
            else:
                cfg["params"][key] = widget.value()
        for key, swatch in self._color_widgets.items():
            cfg["params"][key] = swatch.toolTip()
        return cfg


class StudiesDialog(QDialog):
    studies_changed = pyqtSignal(list)  # emits list of study dicts

    def __init__(self, current_studies: List[dict] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Studies")
        self.setMinimumWidth(520)
        self.setStyleSheet("background: #101218;")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Toggle and configure studies:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)

        studies = deepcopy(current_studies or DEFAULT_STUDIES)
        self._rows: List[StudyRow] = []
        for study in studies:
            row = StudyRow(study)
            self._rows.append(row)
            container_layout.addWidget(row)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Apply")
        ok_btn.clicked.connect(self._apply)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _apply(self):
        configs = [row.get_config() for row in self._rows]
        self.studies_changed.emit(configs)
        self.accept()
