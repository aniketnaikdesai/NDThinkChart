import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from ui.chart_panel import ChartPanel

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
