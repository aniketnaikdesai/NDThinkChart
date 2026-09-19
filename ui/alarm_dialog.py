from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from data.alarm_store import AlarmStore
from data.models import Alarm


CONDITIONS = {
    "Cross Above": "cross_above",
    "Cross Below": "cross_below",
    "Cross Either": "cross_either",
}


class AlarmDialog(QDialog):
    alarms_changed = pyqtSignal()

    def __init__(self, symbol: str, last_price: float | None = None, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.last_price = last_price
        self.setWindowTitle(f"{symbol} Alarms")
        self.setMinimumWidth(680)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Price", "Condition", "Active", "Triggered", "Sound", "Note"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        entry = QWidget()
        entry_layout = QHBoxLayout(entry)
        entry_layout.setContentsMargins(0, 0, 0, 0)

        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(4)
        self.price_input.setRange(0.0001, 1_000_000)
        self.price_input.setValue(last_price or 100.0)
        self.price_input.setFixedWidth(110)

        self.condition_input = QComboBox()
        self.condition_input.addItems(CONDITIONS.keys())

        self.sound_input = QCheckBox("Sound")
        self.sound_input.setChecked(True)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Note")

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_alarm)
        rearm_btn = QPushButton("Rearm")
        rearm_btn.clicked.connect(self._rearm_selected)
        mute_btn = QPushButton("Mute/Unmute")
        mute_btn.clicked.connect(self._toggle_mute_selected)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_selected)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        entry_layout.addWidget(QLabel("Price:"))
        entry_layout.addWidget(self.price_input)
        entry_layout.addWidget(self.condition_input)
        entry_layout.addWidget(self.sound_input)
        entry_layout.addWidget(self.note_input, 1)
        entry_layout.addWidget(add_btn)
        entry_layout.addWidget(rearm_btn)
        entry_layout.addWidget(mute_btn)
        entry_layout.addWidget(delete_btn)
        entry_layout.addWidget(close_btn)
        layout.addWidget(entry)

        self._alarms: list[Alarm] = []
        self._reload()

    def _reload(self):
        self._alarms = AlarmStore.load(self.symbol)
        self.table.setRowCount(0)
        for alarm in self._alarms:
            self._append_row(alarm)

    def _append_row(self, alarm: Alarm):
        row = self.table.rowCount()
        self.table.insertRow(row)
        label_by_condition = {value: label for label, value in CONDITIONS.items()}
        values = [
            f"{alarm.price:.4f}",
            label_by_condition.get(alarm.direction, alarm.direction),
            "Yes" if alarm.active else "No",
            "Yes" if alarm.triggered else "No",
            "Yes" if alarm.sound else "No",
            alarm.note,
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                if col == 0 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, col, item)

    def _selected_alarm(self) -> Alarm | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        index = rows[0].row()
        if index < 0 or index >= len(self._alarms):
            return None
        return self._alarms[index]

    def _add_alarm(self):
        AlarmStore.add(
            Alarm(
                id=None,
                symbol=self.symbol,
                price=self.price_input.value(),
                direction=CONDITIONS[self.condition_input.currentText()],
                sound=self.sound_input.isChecked(),
                note=self.note_input.text().strip(),
            )
        )
        self.note_input.clear()
        self._reload()
        self.alarms_changed.emit()

    def _rearm_selected(self):
        alarm = self._selected_alarm()
        if alarm and alarm.id is not None:
            AlarmStore.rearm(alarm.id)
            self._reload()
            self.alarms_changed.emit()

    def _toggle_mute_selected(self):
        alarm = self._selected_alarm()
        if alarm and alarm.id is not None:
            AlarmStore.set_sound(alarm.id, not alarm.sound)
            self._reload()
            self.alarms_changed.emit()

    def _delete_selected(self):
        alarm = self._selected_alarm()
        if alarm and alarm.id is not None:
            AlarmStore.delete(alarm.id)
            self._reload()
            self.alarms_changed.emit()
