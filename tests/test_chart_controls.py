import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from data.models import Bar
from ui.chart_panel import ChartPanel


def _bar(ts, close, volume=1_000.0):
    return Bar("TEST", "5 mins", ts, close, close + 0.5, close - 0.5,
               close, volume)

@pytest.fixture
def panel(qapp):
    p = ChartPanel()
    p.resize(900, 600)
    p.show()
    qapp.processEvents()
    yield p
    p.hide()
    p.close()

def test_controls_rendered_top_right_outlined(panel, qapp):
    # Controls should exist and be visible
    assert hasattr(panel, "_chart_controls")
    ctrl = panel._chart_controls
    assert ctrl.isVisible()
    # 4 buttons
    buttons = [ctrl.btn_minus, ctrl.btn_plus, ctrl.btn_magnify, ctrl.btn_reset]
    assert len(buttons) == 4
    for b in buttons:
        assert b.isVisible()
    # outlined border and larger label font (magnifier 21px)
    assert "border" in ctrl.styleSheet().lower()
    assert "14px" in ctrl.styleSheet()
    assert "21px" in ctrl.styleSheet()
    assert ctrl.btn_magnify.objectName() == "Magnifier"
    # geometry near top-right, fully inside chart area left of the price axis
    qapp.processEvents()
    # Ensure resizeEvent positioned it
    ctrl_x = ctrl.x()
    ctrl_right = ctrl_x + ctrl.width()
    panel_w = panel.width()
    try:
        axis_w = panel.price_plot.getAxis('right').width()
    except Exception:
        axis_w = 50
    if axis_w < 20:
        axis_w = 50
    # controls right edge should be left of the axis
    assert ctrl_right <= panel_w - axis_w + 5
    assert ctrl_right <= panel_w
    assert ctrl_x >= panel_w - ctrl.width() - axis_w - 35
    assert ctrl.y() <= 15
    # magnifier checkable
    assert ctrl.btn_magnify.isCheckable()

def test_controls_emit_signals(panel, qapp):
    ctrl = panel._chart_controls
    # Use flags to track signals
    flags = {"in":0, "out":0, "mag":None, "reset":0}
    ctrl.zoom_in.connect(lambda: flags.__setitem__("in", flags["in"]+1))
    ctrl.zoom_out.connect(lambda: flags.__setitem__("out", flags["out"]+1))
    ctrl.magnify_toggled.connect(lambda v: flags.__setitem__("mag", v))
    ctrl.reset.connect(lambda: flags.__setitem__("reset", flags["reset"]+1))

    QTest.mouseClick(ctrl.btn_plus, Qt.MouseButton.LeftButton)
    assert flags["in"] == 1
    QTest.mouseClick(ctrl.btn_minus, Qt.MouseButton.LeftButton)
    assert flags["out"] == 1
    # magnifier toggle
    QTest.mouseClick(ctrl.btn_magnify, Qt.MouseButton.LeftButton)
    assert flags["mag"] is True
    assert ctrl.btn_magnify.isChecked() is True
    QTest.mouseClick(ctrl.btn_magnify, Qt.MouseButton.LeftButton)
    assert flags["mag"] is False
    QTest.mouseClick(ctrl.btn_reset, Qt.MouseButton.LeftButton)
    assert flags["reset"] == 1


def test_update_last_bar_same_ts_replaces_not_appends(panel, qapp):
    """Q-3 (defect A): a same-timestamp live bar must replace, not append.

    The first live push after prepare_load() is flagged is_new_candle=True
    (the aggregator starts with no state), but the historical load already
    delivered the forming period — IBKR returns the partial current bar. The
    timestamp is authoritative: appending would draw the live candle on top of
    the last history candle at the same display-x and duplicate the ts.
    """
    panel.set_symbol("TEST")
    panel.set_timeframe("5 mins")
    bars = [_bar(1_700_000_000 + i * 300, 100.0 + i) for i in range(120)]
    panel.update_chart(bars)
    qapp.processEvents()
    assert len(panel._bars) == 120
    last = panel._bars[-1]
    live = _bar(last.ts, last.close + 7.5, volume=9_999.0)
    panel.update_last_bar(live, is_new_candle=True)
    qapp.processEvents()
    assert len(panel._bars) == 120, "same-ts live bar must not append"
    assert len({b.ts for b in panel._bars}) == 120, "duplicate timestamp"
    assert panel._bars[-1].ts == last.ts
    assert panel._bars[-1].close == live.close, "live values must replace"
    assert len(panel._plot_xs) == 120, "one display-x per bar"
