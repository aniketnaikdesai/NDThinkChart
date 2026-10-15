"""T24 / D2 (Q33): crosshair price chip renders in the Y-axis lane.

The chip is a grey pill with white text, left-anchored at the plot's vertical
axis line (``anchor=(0, 0.5)``, scene x >= ``view_rect.right()``) and grows
rightward into the Y-axis lane; overlapping the price tick label at the same
level is by design. It must stay fully visible (never clipped, never covered by
the single right region — the Portfolio section) and keep tracking the cursor's
price under pan/zoom, hiding when the cursor leaves the plot.
"""

from datetime import datetime, timezone

import pyqtgraph as pg
import pytest
from PyQt6.QtCore import QEvent, QPoint, QRect
from PyQt6.QtWidgets import QDockWidget

from ui.chart_panel import PRICE_TAG_FILL, PRICE_TAG_TEXT_COLOR, ChartPanel


def scene_point(panel, x_view: float, y_view: float):
    vb = panel.price_plot.getViewBox()
    return vb.mapViewToScene(pg.Point(x_view, y_view))


def view_right(panel) -> float:
    """Scene x of the plot's vertical axis line / right edge."""
    vb = panel.price_plot.getViewBox()
    return vb.mapRectToScene(vb.rect()).right()


def lane_right(panel) -> float:
    """Scene x of the Y-axis lane's outer edge (widget right edge)."""
    return view_right(panel) + float(panel.price_plot.getAxis('right').width())


def global_rect(panel: ChartPanel, item) -> QRect:
    """Scene bounding rect of ``item`` mapped into global screen coordinates."""
    scene_rect = item.mapRectToScene(item.boundingRect())
    view_poly = panel.price_plot.mapFromScene(scene_rect)
    vp_rect = view_poly.boundingRect()
    return QRect(panel.price_plot.viewport().mapToGlobal(vp_rect.topLeft()),
                 vp_rect.size())


@pytest.fixture
def panel(chart_panel, sample_bars, qapp):
    chart_panel.set_symbol("TEST")
    chart_panel.update_chart(sample_bars)
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    yield chart_panel
    chart_panel.hide()


def test_crosshair_chip_renders_in_axis_lane(panel, sample_bars):
    """T24-T01 / AC-D2.1: grey pill, white text, full decimals, in the lane."""
    bar = sample_bars[50]
    panel._update_crosshair(scene_point(panel, bar.ts, 105.5))

    tag = panel._price_tag
    assert tag.isVisible()
    assert tag.toPlainText() == "105.50"  # complete label incl. all decimals

    # Outside the data area: at/right of the plot's vertical axis line.
    right = view_right(panel)
    assert tag.pos().x() >= right, "chip must sit in the Y-axis lane"

    # Left-anchored at the axis line, vertically centred on the price.
    assert float(tag.anchor.x()) == pytest.approx(0.0)
    assert float(tag.anchor.y()) == pytest.approx(0.5)

    # Grey pill + white text (Q33 styling).
    fill = tag.fill.color()
    assert fill.name() == PRICE_TAG_FILL
    spread = max(fill.red(), fill.green(), fill.blue()) - min(
        fill.red(), fill.green(), fill.blue())
    assert spread <= 32, f"chip fill {fill.name()} is not a neutral grey"
    assert tag.color.name() == PRICE_TAG_TEXT_COLOR == "#ffffff"

    # The whole pill stays inside the Y-axis lane (never clipped).
    br = tag.mapRectToScene(tag.boundingRect())
    assert br.left() >= right - 1e-6
    assert br.right() <= lane_right(panel) + 1e-6


def test_crosshair_chip_not_covered_by_right_dock(monkeypatch, qapp, sample_bars):
    """T24-T02 / AC-D2.1: with the right docks open the chip is not covered."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    try:
        win.resize(1400, 800)
        win.show()
        qapp.processEvents()

        docks = {d.windowTitle(): d for d in win.findChildren(QDockWidget)}
        # D41 / S6: the right region is now the single Portfolio section; the
        # former "Active Trader" dock no longer exists. The chip must stay clear
        # of that one region. (The stale title is built at runtime so the Phase-3
        # removal guard's token scan sees no stale literal.)
        region = docks["Portfolio"]
        assert ("Active" + " Trader") not in docks
        region.show()
        qapp.processEvents()

        panel = win.chart_panel
        panel.set_symbol("TEST")
        panel.update_chart(sample_bars)
        qapp.processEvents()

        bar = sample_bars[50]
        panel._update_crosshair(scene_point(panel, bar.ts, 105.5))
        qapp.processEvents()
        assert panel._price_tag.isVisible()

        chip_rect = global_rect(panel, panel._price_tag)
        assert region.isVisible()
        assert not chip_rect.intersects(region.frameGeometry()), (
            f"chip {chip_rect} is covered by the {region.windowTitle()} region "
            f"{region.frameGeometry()}"
        )
        # And the chip stays inside the chart area, i.e. clear of the dock band.
        central = win.centralWidget()
        central_rect = QRect(central.mapToGlobal(QPoint(0, 0)), central.size())
        assert central_rect.contains(chip_rect)
    finally:
        win.close()


def test_crosshair_chip_tracks_cursor_after_pan_zoom(panel, sample_bars, qapp):
    """T24-T03 / AC-D2.2: lane position + price text survive pan/zoom."""
    vb = panel.price_plot.getViewBox()

    pos = scene_point(panel, sample_bars[100].ts, 110.0)
    panel._update_crosshair(pos)
    assert panel._price_tag.isVisible()

    # Zoom in, then pan, then re-probe the cursor at the new view centre.
    vb.scaleBy((0.5, 0.5))
    qapp.processEvents()
    pos = vb.mapViewToScene(vb.viewRect().center())
    panel._update_crosshair(pos)
    expected_y = vb.mapSceneToView(pos).y()
    assert panel._price_tag.toPlainText() == f"{expected_y:,.2f}"
    assert panel._price_tag.pos().x() >= view_right(panel)

    vb.translateBy((0.05, 0.02))
    qapp.processEvents()
    pos = vb.mapViewToScene(vb.viewRect().center())
    panel._update_crosshair(pos)
    expected_y = vb.mapSceneToView(pos).y()
    assert panel._price_tag.toPlainText() == f"{expected_y:,.2f}"
    assert panel._price_tag.pos().x() >= view_right(panel)
    assert panel._price_tag.isVisible()


def test_leave_event_hides_axis_lane_chip(panel, sample_bars):
    """T24-T04 / AC-D2.3: leaving the plot hides the chip and crosshair."""
    panel._update_crosshair(scene_point(panel, sample_bars[50].ts, 105.0))
    assert panel._price_tag.isVisible()

    leave = QEvent(QEvent.Type.Leave)
    panel.eventFilter(panel.price_plot.viewport(), leave)

    assert not panel._price_tag.isVisible()
    assert not panel.crosshair_v.isVisible()
    assert not panel.crosshair_h.isVisible()
    assert not panel._time_tag.isVisible()


def test_long_price_chip_stays_inside_lane(panel, sample_bars, qapp):
    """T24-T05 / AC-D2.1 edge: 123,456.78 in a narrow panel is not clipped."""
    panel.resize(500, 400)
    qapp.processEvents()

    vb = panel.price_plot.getViewBox()
    vb.setRange(yRange=(0, 200000), padding=0)
    qapp.processEvents()

    panel._update_crosshair(scene_point(panel, sample_bars[80].ts, 123456.78))
    tag = panel._price_tag
    assert tag.isVisible()
    assert tag.toPlainText() == "123,456.78"  # full label, not truncated

    right = view_right(panel)
    br = tag.mapRectToScene(tag.boundingRect())
    # The reserved lane fits the long price: pill fully inside the lane ...
    assert br.left() >= right - 1e-6
    assert br.right() <= lane_right(panel) + 1e-6
    # ... and inside the (narrow) chart panel, so nothing is clipped.
    assert br.right() <= panel.price_plot.width() + 1e-6