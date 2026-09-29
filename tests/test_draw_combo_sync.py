"""ESC-017 / TR-4 / TR-17 — the toolbar combo must follow the router's tool reset.

A drawing tool armed from the toolbar lives in two places: the
``ChartMouseRouter`` (which owns the gesture mode) and the drawing overlay
(which owns the active tool). When the router clears the drawing tool — the
magnifier invoked mid-draw (TR-4) or a symbol change (TR-17) — the combo must
fall back to ``"Cursor"`` too. Otherwise the stale label swallows the next
``currentTextChanged`` and the *same* tool can never be re-armed.

The reset is programmatic, so it must be signal-blocked (ESC-017 guard): a
naive ``setCurrentText("Cursor")`` would emit ``currentTextChanged`` and loop
back into ``_on_draw_tool_changed`` -> ``ChartPanel.set_drawing_tool`` ->
router while the router is mid-transition.
"""

import pytest

from ui.chart_mouse_router import RouterMode
from ui.drawing_overlay import TOOL_CURSOR


@pytest.fixture
def window(monkeypatch, qapp):
    """A shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    monkeypatch.setattr(IBApiClient, "connected", property(lambda self: True))

    from ui.main_window import MainWindow

    win = MainWindow()
    # The symbol-change path must reach only (stubbed) managers, never a socket.
    win.md_manager.req_historical_data = lambda **k: 1
    win.rt_manager.subscribe = lambda *a, **k: 2
    win.chart_panel.resize(900, 600)
    win.show()
    qapp.processEvents()
    yield win
    win.close()
    qapp.processEvents()


def _arm(win, qapp, label="Trendline"):
    """Arm a drawing tool the way a user does: through the toolbar combo."""
    win.draw_combo.setCurrentText(label)
    qapp.processEvents()
    assert win.chart_panel.mouse_router.active_mode == RouterMode.DRAWING
    assert win.chart_panel.drawing_overlay.tool_active() is True
    assert win.draw_combo.currentText() == label


def test_zoom_clears_draw_combo(window, qapp):
    """T36-T01 / AC-D3.7 side effect: TR-4 zoom-cancels-draw resets the combo."""
    win = window
    cp = win.chart_panel
    _arm(win, qapp, "Trendline")

    # Invoke the magnifier the way its toggle does (routes through enter_zoom).
    cp.set_zoom_mode(True)
    qapp.processEvents()

    assert cp.mouse_router.active_mode == RouterMode.ZOOMING
    assert cp.drawing_overlay._tool == TOOL_CURSOR
    assert win.draw_combo.currentText() == "Cursor"

    # With the combo no longer stale, re-selecting the same tool re-arms it.
    win.draw_combo.setCurrentText("Trendline")
    qapp.processEvents()
    assert cp.mouse_router.active_mode == RouterMode.DRAWING
    assert cp.drawing_overlay.tool_active() is True
    assert cp.drawing_overlay._tool == "trendline"


def test_symbol_change_clears_draw_combo(window, qapp):
    """T36-T02 / TR-17: a symbol change resets the combo and returns to IDLE."""
    win = window
    cp = win.chart_panel
    _arm(win, qapp, "Horizontal")

    win.symbol_input.setText("AAPL")
    win.load_chart()  # the real TR-17 symbol-change path
    qapp.processEvents()

    assert cp.mouse_router.active_mode == RouterMode.IDLE
    assert cp.drawing_overlay.tool_active() is False
    assert cp.drawing_overlay._tool == TOOL_CURSOR
    assert win.draw_combo.currentText() == "Cursor"


def test_reset_does_not_emit_spurious_signal(window, qapp):
    """T36-T03 / ESC-017 guard: the reset is signal-blocked; alarm path intact."""
    win = window
    cp = win.chart_panel
    _arm(win, qapp, "Zone")

    seen: list[str] = []
    win.draw_combo.currentTextChanged.connect(seen.append)

    cp.set_zoom_mode(True)  # reset path under test
    qapp.processEvents()
    assert win.draw_combo.currentText() == "Cursor"
    assert seen == []  # blockSignals: the reset emitted nothing

    # The alarm-mode reset path still works, and is equally quiet.
    win.draw_combo.setCurrentText("Measure")
    qapp.processEvents()
    assert cp.mouse_router.active_mode == RouterMode.DRAWING
    seen.clear()

    win.alarm_mode_btn.setChecked(True)
    qapp.processEvents()

    assert win.draw_combo.currentText() == "Cursor"
    assert cp.alarm_overlay.is_alarm_mode() is True
    assert seen == []
