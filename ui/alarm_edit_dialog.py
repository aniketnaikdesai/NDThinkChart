"""Small modal dialog for editing one existing price alarm.

Persists immediately on Save via :meth:`AlarmStore.update`, and deliberately
never touches ``active``/``triggered``/``triggered_at`` — so a triggered or set
alarm keeps its state across an edit.
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
)

from data.alarm_store import AlarmStore
from data.models import Alarm


CONDITIONS = {
    "Cross Above": "cross_above",
    "Cross Below": "cross_below",
    "Cross Either": "cross_either",
}


class AlarmEditDialog(QDialog):
    """Edit price/condition/sound/note for a single alarm."""

    def __init__(self, alarm: Alarm, parent=None):
        super().__init__(parent)
        self.alarm = alarm
        self.setWindowTitle("Edit Alarm")
        self.setModal(True)

        layout = QFormLayout(self)

        # D39: burst alarms tune the z-threshold, not a price level.
        self._is_burst = getattr(alarm, "kind", "price") == "volume_burst"
        if self._is_burst:
            from services.volume_baseline import DEFAULT_Z_THRESHOLD

            self.z_input = QDoubleSpinBox()
            self.z_input.setDecimals(1)
            self.z_input.setRange(0.5, 50.0)
            self.z_input.setSingleStep(0.5)
            try:
                z0 = float((alarm.params or {}).get(
                    "z_threshold", DEFAULT_Z_THRESHOLD))
            except (TypeError, ValueError):
                z0 = DEFAULT_Z_THRESHOLD
            self.z_input.setValue(z0)
            layout.addRow("Burst threshold (z ≥):", self.z_input)
            proxy_label = (alarm.params or {}).get("proxy_label")
            if proxy_label:
                layout.addRow("Tape:", QLabel(f"Volume burst on {proxy_label}"))
        else:
            self.price_input = QDoubleSpinBox()
            self.price_input.setDecimals(4)
            self.price_input.setRange(0.0001, 1_000_000)
            self.price_input.setValue(float(alarm.price))
            layout.addRow("Price:", self.price_input)

            self.condition_input = QComboBox()
            self.condition_input.addItems(CONDITIONS.keys())
            label_by_condition = {value: label for label, value in CONDITIONS.items()}
            self.condition_input.setCurrentText(
                label_by_condition.get(alarm.direction, alarm.direction)
            )
            layout.addRow("Condition:", self.condition_input)

        self.sound_input = QCheckBox("Play sound")
        self.sound_input.setChecked(bool(alarm.sound))
        layout.addRow("Sound:", self.sound_input)

        self.note_input = QLineEdit(alarm.note or "")
        self.note_input.setPlaceholderText("Note")
        layout.addRow("Note:", self.note_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        self.cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        if self.alarm is not None and self.alarm.id is not None:
            if self._is_burst:
                params = dict(self.alarm.params or {})
                params["z_threshold"] = round(float(self.z_input.value()), 1)
                AlarmStore.update(
                    self.alarm.id,
                    params=params,
                    sound=bool(self.sound_input.isChecked()),
                    note=self.note_input.text().strip(),
                )
            else:
                AlarmStore.update(
                    self.alarm.id,
                    price=float(self.price_input.value()),
                    direction=CONDITIONS[self.condition_input.currentText()],
                    sound=bool(self.sound_input.isChecked()),
                    note=self.note_input.text().strip(),
                )
        self.accept()
