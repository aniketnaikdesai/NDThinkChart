"""D21.3 / D21-05 — toolbar extended-hours button relabelling.

Boots a **real** ``ui.main_window.MainWindow`` on the offscreen Qt platform
(``IBApiClient.connect`` monkeypatched so the TWS-seeking managers never open a
socket, mirroring the D17/D18/D19 offscreen harnesses) and verifies the
extended-hours toolbar button's label tracks its checked state:

* AC-D21.3.1 — ON (checked) -> "Ext Hours"; OFF (unchecked) -> "RTH", updated
  immediately on toggle and preserved across a chart reload, with the fixed
  80px width fitting both labels.

D21-06 adds the persistent active-highlight coverage (``VIS-D21.2``):

* AC-D21.7.1 — a checkable toggle that is ON shows a persistent, clearly
  visible highlight and reverts when OFF; and the Studies/Alarms popup buttons
  are highlighted while their modal dialog is open and cleared on close, with
  the highlight independent of the D19 ``ToolbarScroll`` scroll position.

D21-07 adds the Alarm-Mode coverage (``D21.8``):

* AC-D21.8.1 — ``alarm_mode_btn`` shows the persistent ``VIS-D21.2`` highlight
  while Alarm Mode is armed and reverts when it is switched off.
* AC-D21.8.2 — the status-bar hint ("Alarm mode: click the chart to place a
  price alarm.") is shown with no timeout while armed and is cleared/replaced on
  every exit path (button off, alarm placed, drawing tool selected), so it never
  permanently masks a later status message.
"""

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QScrollArea, QWidget

from ui.visual_conventions import (
    ACTIVE_PROPERTY,
    VIS_D21_2_STYLESHEET,
    DiagonalStrikeButton,
    set_button_active,
)

_EXT_ON = "Ext Hours"
_EXT_OFF = "RTH"
_BTN_WIDTH = 80


class _ReqStub:
    """Counts ``req_historical_data`` calls so a reload is provably driven."""

    def __init__(self):
        self.calls: list[dict] = []

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, bar_size=None, duration=None):
        self.calls.append({
            "timeframe": timeframe,
            "extended_hours": extended_hours,
        })
        return len(self.calls)

    def cancel(self, req_id):
        pass


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    # The load path must reach only the (stubbed) managers, never a socket.
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    return win


def _stub_feed(win, stub: _ReqStub) -> None:
    """Route the chart-reload historical feed to the counting stub."""
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel


def test_D21_05_T01_label_tracks_checked_state(monkeypatch, qapp):
    """D21-05-T01: label switches immediately with the checked state."""
    win = _make_window(monkeypatch, qapp)
    try:
        btn = win.ext_hours_btn
        assert btn.isChecked() is True
        assert btn.text() == _EXT_ON

        btn.setChecked(False)
        assert btn.isChecked() is False
        assert btn.text() == _EXT_OFF

        btn.setChecked(True)
        assert btn.isChecked() is True
        assert btn.text() == _EXT_ON
    finally:
        win.close()


def test_D21_05_T02_label_reflects_state_after_reload(monkeypatch, qapp):
    """D21-05-T02: label survives a reload and the 80px width fits both labels."""
    win = _make_window(monkeypatch, qapp)
    try:
        btn = win.ext_hours_btn
        stub = _ReqStub()
        _stub_feed(win, stub)

        win.symbol_input.setText("SPY")
        win.load_chart()
        assert win._current_symbol == "SPY"

        # Toggle OFF -> relabel to RTH and drive a reload through the slot.
        before = len(stub.calls)
        btn.setChecked(False)
        assert btn.text() == _EXT_OFF
        assert len(stub.calls) > before

        # An explicit reload must not disturb the label.
        win.load_chart()
        assert btn.isChecked() is False
        assert btn.text() == _EXT_OFF

        # Toggle ON -> relabel to Ext Hours and reload.
        before = len(stub.calls)
        btn.setChecked(True)
        assert btn.text() == _EXT_ON
        assert len(stub.calls) > before

        win.load_chart()
        assert btn.text() == _EXT_ON

        # The fixed 80px width fits both labels.
        btn.setText(_EXT_ON)
        assert btn.sizeHint().width() <= _BTN_WIDTH
        btn.setText(_EXT_OFF)
        assert btn.sizeHint().width() <= _BTN_WIDTH
    finally:
        win.close()


# ── D21-06 / VIS-D21.2 — persistent active highlight ─────────────────────────

#: The VIS-D21.2 accent fill the stylesheet applies to an active button.  Its
#: presence/absence in the rendered pixels is what "clearly visible highlight"
#: means (asserting the resolved style, not just the dynamic property).
_ACTIVE_FILL = QColor("#1f6feb")

_CHECKABLE_TOGGLES = ("sound_btn", "ext_hours_btn", "alarm_mode_btn")


def _render(widget: QWidget) -> QImage:
    """Render *widget* into an ARGB image (offscreen, no extra show() needed)."""
    widget.ensurePolished()
    if widget.width() <= 0 or widget.height() <= 0:
        size = widget.sizeHint()
        widget.resize(max(size.width(), 80), max(size.height(), 28))
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    widget.render(image)
    return image


def _pixels(image: QImage) -> bytes:
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    ptr = image.constBits()
    ptr.setsize(image.sizeInBytes())
    return bytes(ptr)


def _images_differ(a: QImage, b: QImage) -> bool:
    if a.size() != b.size():
        return True
    return _pixels(a) != _pixels(b)


def _active_fill_pixels(image: QImage) -> int:
    """Count pixels exactly matching the VIS-D21.2 active fill."""
    return sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y) == _ACTIVE_FILL
    )


def _toolbar(win):
    """The D19-wrapped ``#MainToolbar`` content widget."""
    toolbar = win.findChild(QWidget, "MainToolbar")
    assert toolbar is not None, "MainToolbar not found"
    return toolbar


def test_D21_06_T01_checkable_toggles_highlight(monkeypatch, qapp):
    """D21-06-T01: each checkable toggle highlights while ON, reverts when OFF."""
    win = _make_window(monkeypatch, qapp)
    try:
        toolbar = _toolbar(win)
        # The shared VIS-D21.2 sheet is applied to the toolbar and keys the
        # checkable toggles off the :checked pseudo-state.
        assert VIS_D21_2_STYLESHEET.strip() in toolbar.styleSheet()
        assert ":checked" in toolbar.styleSheet()

        for name in _CHECKABLE_TOGGLES:
            btn = getattr(win, name)
            assert btn.isCheckable(), f"{name} is not a checkable toggle"

            btn.setChecked(False)
            qapp.processEvents()
            off = _render(btn)
            assert _active_fill_pixels(off) == 0, f"{name} highlighted while OFF"

            btn.setChecked(True)
            qapp.processEvents()
            on = _render(btn)
            assert _images_differ(off, on), f"{name} shows no highlight when ON"
            assert _active_fill_pixels(on) > 0, (
                f"{name} ON render lacks the VIS-D21.2 highlight fill"
            )

            # Reverts to the inactive rendering when turned OFF again.
            btn.setChecked(False)
            qapp.processEvents()
            reverted = _render(btn)
            assert _active_fill_pixels(reverted) == 0, f"{name} did not clear when OFF"
            assert not _images_differ(off, reverted), (
                f"{name} did not revert to its inactive style"
            )
    finally:
        win.close()


def test_D21_06_T02_popup_buttons_highlight(monkeypatch, qapp):
    """D21-06-T02: Studies/Alarms buttons highlight while their dialog is open."""
    win = _make_window(monkeypatch, qapp)
    try:
        from ui.alarm_dialog import AlarmDialog
        from ui.studies_dialog import StudiesDialog

        captured: dict[str, bool] = {}

        def fake_studies_exec(self):
            # Sampled *inside* exec(): the button must be active while open.
            captured["studies"] = win.studies_btn.property(ACTIVE_PROPERTY)
            return 0

        monkeypatch.setattr(StudiesDialog, "exec", fake_studies_exec)

        win._open_studies_dialog()
        assert captured["studies"] is True, "studies_btn not active while dialog open"
        assert win.studies_btn.property(ACTIVE_PROPERTY) is False, (
            "studies_btn highlight not cleared on close"
        )

        # The alarms dialog bails out without a loaded symbol.
        win._current_symbol = "SPY"

        def fake_alarms_exec(self):
            captured["alarms"] = win.alarms_btn.property(ACTIVE_PROPERTY)
            return 0

        monkeypatch.setattr(AlarmDialog, "exec", fake_alarms_exec)

        win._open_alarm_dialog()
        assert captured["alarms"] is True, "alarms_btn not active while dialog open"
        assert win.alarms_btn.property(ACTIVE_PROPERTY) is False, (
            "alarms_btn highlight not cleared on close"
        )

        # The shared sheet targets the toolbar objectName / [active="true"] so
        # the highlight resolves regardless of the D19 scroll position.
        toolbar = _toolbar(win)
        assert VIS_D21_2_STYLESHEET.strip() in toolbar.styleSheet()
        assert '[active="true"]' in toolbar.styleSheet()

        btn = win.studies_btn
        inactive = _render(btn)
        set_button_active(btn, True)
        qapp.processEvents()
        active = _render(btn)
        assert _images_differ(inactive, active), "active popup button did not render"
        assert _active_fill_pixels(active) > 0, "active popup button lacks highlight fill"

        # Scroll the D19 wrapper to the far right: the objectName-keyed highlight
        # must still resolve (it is not a function of scroll position).
        wrapper = win.findChild(QScrollArea, "ToolbarScroll")
        assert wrapper is not None, "ToolbarScroll wrapper not found"
        assert wrapper.widget() is toolbar, "scroll content is not the toolbar"
        wrapper.horizontalScrollBar().setValue(
            wrapper.horizontalScrollBar().maximum()
        )
        qapp.processEvents()

        set_button_active(btn, False)
        qapp.processEvents()
        set_button_active(btn, True)
        qapp.processEvents()
        scrolled_active = _render(btn)
        assert _active_fill_pixels(scrolled_active) > 0, (
            "highlight lost after scrolling the D19 wrapper"
        )

        # Cleared -> back to the inactive rendering.
        set_button_active(btn, False)
        qapp.processEvents()
        assert _active_fill_pixels(_render(btn)) == 0
    finally:
        win.close()


# ── D21-07 / D21.8 — Alarm Mode persistent highlight + status hint ───────────

def test_D21_07_T01_alarm_mode_button_highlight(monkeypatch, qapp):
    """D21-07-T01: alarm_mode_btn is highlighted while armed, reverted when off."""
    win = _make_window(monkeypatch, qapp)
    try:
        btn = win.alarm_mode_btn
        assert btn.isCheckable(), "alarm_mode_btn is not a checkable toggle"

        btn.setChecked(False)
        qapp.processEvents()
        off = _render(btn)
        assert _active_fill_pixels(off) == 0, "alarm_mode_btn highlighted while OFF"

        btn.setChecked(True)
        qapp.processEvents()
        on = _render(btn)
        assert _images_differ(off, on), "alarm_mode_btn shows no highlight while ON"
        assert _active_fill_pixels(on) > 0, (
            "alarm_mode_btn ON render lacks the VIS-D21.2 highlight fill"
        )

        btn.setChecked(False)
        qapp.processEvents()
        reverted = _render(btn)
        assert _active_fill_pixels(reverted) == 0, "alarm_mode_btn did not clear when OFF"
        assert not _images_differ(off, reverted), (
            "alarm_mode_btn did not revert to its inactive style"
        )
    finally:
        win.close()


def test_D21_07_T02_status_hint_persists_and_clears(monkeypatch, qapp):
    """D21-07-T02: the hint is shown with no timeout while armed, cleared when off.

    Persistence past the old 4000 ms timeout is asserted via a ``showMessage``
    spy (a timeout of 0 means "never auto-clear") instead of real sleeping, so
    the test stays fast and deterministic.
    """
    from ui.main_window import ALARM_MODE_STATUS_MESSAGE

    win = _make_window(monkeypatch, qapp)
    try:
        calls: list[tuple[str, int]] = []
        original = win.status_bar.showMessage

        def spy(message, timeout=0):
            calls.append((message, timeout))
            return original(message, timeout)

        monkeypatch.setattr(win.status_bar, "showMessage", spy)

        win.alarm_mode_btn.setChecked(True)
        qapp.processEvents()

        assert win.status_bar.currentMessage() == ALARM_MODE_STATUS_MESSAGE
        assert calls[-1] == (ALARM_MODE_STATUS_MESSAGE, 0), (
            "the Alarm-Mode hint must be shown with no timeout (0), not 4000 ms"
        )

        # A persistent (timeout 0) message is never auto-cleared, so it remains
        # on screen after the old 4000 ms window would have elapsed.
        assert win.status_bar.currentMessage() == ALARM_MODE_STATUS_MESSAGE

        win.alarm_mode_btn.setChecked(False)
        qapp.processEvents()
        assert win.status_bar.currentMessage() != ALARM_MODE_STATUS_MESSAGE
    finally:
        win.close()


def test_D21_07_T03_exit_paths_clear_status(monkeypatch, qapp):
    """D21-07-T03: every Alarm-Mode exit clears/replaces the persistent hint."""
    from ui.alarm_dialog import AlarmDialog
    from ui.main_window import ALARM_MODE_STATUS_MESSAGE

    win = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "SPY"
        monkeypatch.setattr(AlarmDialog, "exec", lambda self: 0)

        # Exit path 1: placing an alarm.
        win.alarm_mode_btn.setChecked(True)
        qapp.processEvents()
        assert win.status_bar.currentMessage() == ALARM_MODE_STATUS_MESSAGE

        win._on_alarm_create_requested(123.45)
        qapp.processEvents()
        assert win.alarm_mode_btn.isChecked() is False
        assert win.status_bar.currentMessage() != ALARM_MODE_STATUS_MESSAGE

        # The stale hint must not mask a later status message.
        win.status_bar.showMessage("Alarm created.", 2000)
        assert win.status_bar.currentMessage() == "Alarm created."

        # Exit path 2: selecting a drawing tool.
        win.status_bar.clearMessage()
        win.alarm_mode_btn.setChecked(True)
        qapp.processEvents()
        assert win.status_bar.currentMessage() == ALARM_MODE_STATUS_MESSAGE

        win.draw_combo.setCurrentText("Trendline")
        qapp.processEvents()
        assert win.alarm_mode_btn.isChecked() is False
        assert win.status_bar.currentMessage() != ALARM_MODE_STATUS_MESSAGE

        # Exit path 3: toggling the button off directly.
        win.alarm_mode_btn.setChecked(True)
        qapp.processEvents()
        assert win.status_bar.currentMessage() == ALARM_MODE_STATUS_MESSAGE

        win.alarm_mode_btn.setChecked(False)
        qapp.processEvents()
        assert win.status_bar.currentMessage() != ALARM_MODE_STATUS_MESSAGE

        # A later message still gets through afterwards.
        win.status_bar.showMessage("Done.", 2000)
        assert win.status_bar.currentMessage() == "Done."
    finally:
        win.close()


# ── D21-08 / D21.12 — Volume toggle struck while the pane is hidden ───────────

def test_D21_08_T01_volume_toggle_strikes_when_hidden(qapp):
    """D21-08-T01 / AC-D21.12.1: the Volume toggle strikes iff the pane is hidden."""
    from ui.chart_panel import ChartPanel

    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    try:
        toggle = panel._volume_toggle

        # The D10 affordance is now the VIS-D21.1 strike-capable button.
        assert isinstance(toggle, DiagonalStrikeButton)
        assert toggle.text() == "Volume"

        # Default: checked (pane shown) and therefore not struck.
        assert toggle.isChecked() is True
        assert toggle.struck is False
        assert panel.volume_plot.isVisible()

        # Unchecked (pane hidden) -> struck.
        toggle.setChecked(False)
        qapp.processEvents()
        assert toggle.struck is True
        assert not panel.volume_plot.isVisible()

        # Re-checked (pane shown) -> strike removed.
        toggle.setChecked(True)
        qapp.processEvents()
        assert toggle.struck is False
        assert panel.volume_plot.isVisible()
    finally:
        panel.hide()
        panel.close()


def test_D21_08_T02_d10_placement_and_toggle_preserved(qapp):
    """D21-08-T02 / AC-D21.12.1: D10 placement/toggle behaviour is unchanged.

    The strike is cosmetic: the button stays at the top-left of the volume pane
    while shown, and toggling still hides/shows ``volume_plot`` + its axis and
    refreshes the splitter exactly as D10 did.
    """
    from ui.chart_panel import ChartPanel

    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    try:
        toggle = panel._volume_toggle

        # Shown/checked: the toggle sits at the top-left of the volume pane (D10).
        panel._position_volume_toggle()
        qapp.processEvents()
        vol_tl = panel.volume_plot.mapTo(panel, QPoint(0, 0))
        assert abs(toggle.x() - (vol_tl.x() + 8)) <= 1, (toggle.pos(), vol_tl)
        assert abs(toggle.y() - (vol_tl.y() + 4)) <= 1, (toggle.pos(), vol_tl)

        sizes_visible = panel._splitter.sizes()
        price_h_visible = panel.price_plot.height()

        # Hide: struck, pane + axis hidden, price expands (D10 splitter refresh).
        toggle.setChecked(False)
        qapp.processEvents()
        assert toggle.struck is True
        assert not panel.volume_plot.isVisible()
        assert not panel.volume_plot.getAxis('right').isVisible()
        assert panel._splitter.sizes() != sizes_visible
        assert panel.price_plot.height() > price_h_visible

        # Show again: unstruck, pane + axis visible, splitter/price restored.
        toggle.setChecked(True)
        qapp.processEvents()
        assert toggle.struck is False
        assert panel.volume_plot.isVisible()
        assert panel.volume_plot.getAxis('right').isVisible()
        assert panel._splitter.sizes() == sizes_visible
        assert panel.price_plot.height() == price_h_visible

        # The strike is cosmetic only: the button remains clickable while struck.
        toggle.setChecked(False)
        qapp.processEvents()
        assert toggle.struck is True
        fired: list[bool] = []
        toggle.clicked.connect(lambda: fired.append(True))
        toggle.click()
        qapp.processEvents()
        assert fired == [True], "struck Volume toggle is no longer clickable"
        # The click toggled it back on (checked -> unstruck, pane visible).
        assert toggle.isChecked() is True
        assert toggle.struck is False
        assert panel.volume_plot.isVisible()
    finally:
        panel.hide()
        panel.close()
