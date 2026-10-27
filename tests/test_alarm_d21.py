"""D21.9 — per-row alarm Edit button + AlarmEditDialog with immediate persistence.

Task D21-12. Offscreen harness mirroring tests/test_alarm_store.py and
tests/test_alarm_interaction.py (QApplication via the shared ``qapp`` fixture;
no live TWS).
"""

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QPushButton

from data.alarm_store import AlarmStore
from data.db import db
from data.models import Alarm
from ui.alarm_dialog import AlarmDialog
from ui.alarm_edit_dialog import AlarmEditDialog


@pytest.fixture(autouse=True)
def clean_alarms():
    db.conn.execute("DELETE FROM alarms WHERE symbol='TEST'")
    db.conn.commit()
    yield
    db.conn.execute("DELETE FROM alarms WHERE symbol='TEST'")
    db.conn.commit()


def add_alarm(price=100.0, direction="cross_either", sound=True, note="",
              triggered=False):
    alarm = Alarm(id=None, symbol="TEST", price=price, direction=direction,
                  sound=sound, note=note)
    alarm.id = AlarmStore.add(alarm)
    if triggered:
        AlarmStore.mark_triggered(alarm.id)
    return alarm


@pytest.fixture
def dialog(qapp):
    dlg = AlarmDialog("TEST", last_price=100.0)
    yield dlg
    dlg.close()


def _row_edit_button(dialog, row):
    return dialog.table.cellWidget(row, dialog.EDIT_COLUMN)


def _open_edit_and(dialog, row, fill):
    """Click a row's Edit button and run ``fill`` against the modal dialog.

    ``fill`` receives the AlarmEditDialog and is invoked from a zero-delay
    timer once the modal exec loop is running.
    """
    button = _row_edit_button(dialog, row)
    assert isinstance(button, QPushButton)

    def _run():
        target = None
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, AlarmEditDialog) and widget.isVisible():
                target = widget
                break
        assert target is not None, "AlarmEditDialog did not open"
        fill(target)

    QTimer.singleShot(0, _run)
    button.click()


def test_d21_12_t01_each_row_has_right_end_edit_button(dialog, qapp):
    add_alarm(price=101.0)
    add_alarm(price=102.0)
    dialog._reload()

    assert dialog.table.rowCount() == 2
    for row in range(dialog.table.rowCount()):
        button = _row_edit_button(dialog, row)
        assert isinstance(button, QPushButton)
        assert button.text().strip().lower() == "edit"
    # The Edit column is the last column, i.e. the right-hand end of the row.
    assert dialog.EDIT_COLUMN == dialog.table.columnCount() - 1


def test_d21_12_t02_note_column_stretched_up_to_edit_button(dialog, qapp):
    add_alarm(price=101.0, note="a fairly long note for the row")
    dialog._reload()
    dialog.resize(680, 400)
    dialog.show()
    qapp.processEvents()

    header = dialog.table.horizontalHeader()
    note_left = header.sectionViewportPosition(dialog.NOTE_COLUMN)
    note_width = header.sectionSize(dialog.NOTE_COLUMN)
    edit_left = header.sectionViewportPosition(dialog.EDIT_COLUMN)
    edit_width = header.sectionSize(dialog.EDIT_COLUMN)

    # Note ends where the Edit column begins — no empty gap before the button.
    assert note_left + note_width >= edit_left - 1
    # The Edit button reaches the right-hand edge of the popup.
    assert edit_left + edit_width >= header.length() - 2
    # The Note column actually absorbed the slack.
    assert note_width > dialog.table.columnWidth(0)


def test_d21_12_t03_save_persists_and_cancel_discards(dialog, qapp):
    add_alarm(price=100.0, direction="cross_above", sound=True, note="orig")
    dialog._reload()

    def save(dlg):
        dlg.price_input.setValue(123.4567)
        dlg.condition_input.setCurrentText("Cross Below")
        dlg.sound_input.setChecked(False)
        dlg.note_input.setText("edited")
        dlg.save_button.click()

    _open_edit_and(dialog, 0, save)

    loaded = AlarmStore.load("TEST")
    assert len(loaded) == 1
    assert loaded[0].price == pytest.approx(123.4567, abs=1e-4)
    assert loaded[0].direction == "cross_below"
    assert loaded[0].sound is False
    assert loaded[0].note == "edited"

    # Re-open and Cancel: nothing changes.
    dialog._reload()

    def cancel(dlg):
        dlg.price_input.setValue(999.0)
        dlg.condition_input.setCurrentText("Cross Either")
        dlg.sound_input.setChecked(True)
        dlg.note_input.setText("should not persist")
        dlg.cancel_button.click()

    _open_edit_and(dialog, 0, cancel)

    loaded = AlarmStore.load("TEST")
    assert loaded[0].price == pytest.approx(123.4567, abs=1e-4)
    assert loaded[0].direction == "cross_below"
    assert loaded[0].sound is False
    assert loaded[0].note == "edited"


def test_d21_12_t04_triggered_alarm_state_preserved_and_wire_op_updated(
    dialog, qapp
):
    add_alarm(price=100.0, note="orig", triggered=True)
    before = AlarmStore.load("TEST")[0]
    assert before.triggered is True
    assert before.triggered_at is not None
    triggered_at = before.triggered_at

    dialog._reload()

    def save(dlg):
        dlg.price_input.setValue(150.25)
        dlg.save_button.click()

    _open_edit_and(dialog, 0, save)

    after = AlarmStore.load("TEST")[0]
    assert after.price == pytest.approx(150.25, abs=1e-4)
    # Editing a triggered/set alarm must not re-arm, reset or disable it.
    assert after.triggered is True
    assert after.active is True
    assert after.triggered_at == triggered_at

    # The rendered alarm set reflects the edited price once reloaded from the
    # store, and crosses to the LWC engine as one replace-all ``set_alarms`` op.
    from ui.lwc_view import LwcChartView

    view = LwcChartView(tz_offset=14400, editable=True)
    view.set_alarms(AlarmStore.load("TEST"))
    op = view.alarm_ops[-1]
    assert op["op"] == "set_alarms"
    cols = op["cols"]
    assert cols["price"] == [pytest.approx(150.25, abs=1e-4)]
    # Editing a triggered alarm must not re-arm it on the wire either.
    assert cols["triggered"] == [True]
    assert cols["active"] == [True]


# ── D21.10 / D21-13 — smart alarm setup: clicked price, yellow dashed preview,
#    on-open condition default ────────────────────────────────────────────────

def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS (offscreen)."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    # The chart-click path must reach only the (stubbed) managers, never a socket.
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    return win


def test_d21_13_t01_click_price_prefills_popup(monkeypatch, qapp):
    """D21-13-T01 / AC-D21.10.1: the clicked price pre-fills the popup."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "TEST"
        win._last_chart_price = 100.0
        captured = {}

        def fake_exec(self):
            captured["price"] = self.price_input.value()
            return 0

        monkeypatch.setattr(AlarmDialog, "exec", fake_exec)
        win._on_alarm_create_requested(123.45)
        qapp.processEvents()

        assert captured["price"] == pytest.approx(123.45, abs=1e-4)
    finally:
        win.close()


def test_d21_13_t02_preview_line_visible_while_open(monkeypatch, qapp):
    """D21-13-T02 / AC-D21.10.2: the preview sits at the clicked level."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "TEST"
        win._last_chart_price = 100.0
        captured = {}

        def fake_exec(self):
            captured["price"] = win.chart_panel.alarm_preview_price
            captured["op"] = win.chart_panel.alarm_ops[-1]
            return 0

        monkeypatch.setattr(AlarmDialog, "exec", fake_exec)
        win._on_alarm_create_requested(118.25)
        qapp.processEvents()

        assert captured["price"] == pytest.approx(118.25, abs=1e-4)
        # ... and the level crossed to the engine while the popup was open.
        assert captured["op"] == {
            "op": "set_alarm_preview", "series": "alarms", "price": 118.25}
    finally:
        win.close()


def test_d21_13_t03_preview_follows_price_live(monkeypatch, qapp):
    """D21-13-T03 / AC-D21.10.3: the preview line tracks the spinbox live."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "TEST"
        win._last_chart_price = 100.0
        seen = []

        def fake_exec(self):
            self.price_input.setValue(130.75)
            qapp.processEvents()
            seen.append(win.chart_panel.alarm_preview_price)
            return 0

        monkeypatch.setattr(AlarmDialog, "exec", fake_exec)
        win._on_alarm_create_requested(118.0)
        qapp.processEvents()

        assert len(seen) == 1
        assert seen[0] == pytest.approx(130.75, abs=1e-4)
    finally:
        win.close()


def test_d21_13_t04_preview_removed_close_and_replaced_on_add(
    monkeypatch, qapp
):
    """D21-13-T04 / AC-D21.10.4: removed on close; real line replaces it on Add."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "TEST"
        win._last_chart_price = 100.0

        # Close without Add -> preview removed, no real alarm line.
        monkeypatch.setattr(AlarmDialog, "exec", lambda self: 0)
        win._on_alarm_create_requested(120.0)
        qapp.processEvents()
        assert win.chart_panel.alarm_preview_price is None
        assert win.chart_panel.alarms == []

        # Add -> preview removed and the real alarm line replaces it.
        def fake_exec(self):
            self.price_input.setValue(120.0)
            self._add_alarm()
            return 1

        monkeypatch.setattr(AlarmDialog, "exec", fake_exec)
        win._on_alarm_create_requested(120.0)
        qapp.processEvents()

        assert win.chart_panel.alarm_preview_price is None
        alarms = AlarmStore.load("TEST")
        assert len(alarms) == 1
        op = win.chart_panel.alarm_ops[-1]
        assert op["op"] == "set_alarms"
        assert op["cols"]["price"] == [pytest.approx(120.0, abs=1e-4)]
    finally:
        win.close()


def test_d21_13_t05_condition_default_on_open(qapp):
    """D21-13-T05 / AC-D21.10.5: on-open condition default, override sticks."""
    # current (100) below the alarm (110) -> price must rise -> Cross Above.
    dlg = AlarmDialog("TEST", last_price=100.0, initial_price=110.0)
    assert dlg.condition_input.currentText() == "Cross Above"
    dlg.close()

    # current (100) above the alarm (90) -> price must fall -> Cross Below.
    dlg = AlarmDialog("TEST", last_price=100.0, initial_price=90.0)
    assert dlg.condition_input.currentText() == "Cross Below"
    dlg.close()

    # current price unknown -> Cross Above.
    dlg = AlarmDialog("TEST", last_price=None, initial_price=110.0)
    assert dlg.condition_input.currentText() == "Cross Above"
    dlg.close()

    # User override is allowed and the default is not recomputed on a price
    # change (50 would be Cross Below if it were recomputed).
    dlg = AlarmDialog("TEST", last_price=100.0, initial_price=110.0)
    assert dlg.condition_input.currentText() == "Cross Above"
    dlg.condition_input.setCurrentText("Cross Either")
    dlg.price_input.setValue(50.0)
    assert dlg.condition_input.currentText() == "Cross Either"
    dlg.close()


def test_d21_13_t06_alarms_button_path_has_no_preview(monkeypatch, qapp):
    """D21-13-T06 / AC-D21.10.2: the Alarms-button path creates no preview line."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "TEST"
        win._last_chart_price = 100.0
        captured = {}

        def fake_exec(self):
            captured["preview"] = win.chart_panel.alarm_preview_price
            return 0

        monkeypatch.setattr(AlarmDialog, "exec", fake_exec)
        win._open_alarm_dialog()
        qapp.processEvents()

        assert captured["preview"] is None
        assert win.chart_panel.alarm_preview_price is None
    finally:
        win.close()
