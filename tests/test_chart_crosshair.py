"""Tests for the price-plot crosshair: cursor shape, axis price/time chips,
and show/hide behavior on enter, leave and empty data."""

from datetime import datetime, timezone

import pyqtgraph as pg
import pytest
from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ui.chart_panel import ChartPanel


def scene_point(panel, x_view: float, y_view: float):
    vb = panel.price_plot.getViewBox()
    return vb.mapViewToScene(pg.Point(x_view, y_view))


@pytest.fixture
def panel(chart_panel, sample_bars, qapp):
    chart_panel.set_symbol("TEST")
    chart_panel.update_chart(sample_bars)
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    yield chart_panel
    chart_panel.hide()


def test_viewport_shows_cross_cursor(panel):
    assert panel.price_plot.viewport().cursor().shape() == Qt.CursorShape.CrossCursor


def test_hover_inside_shows_lines_and_axis_chips(panel, sample_bars):
    bar = sample_bars[100]
    pos = scene_point(panel, bar.ts, 110.5)
    panel._update_crosshair(pos)

    assert panel.crosshair_v.isVisible()
    assert panel.crosshair_h.isVisible()
    # Horizontal line must be truly horizontal (inherited bug was angle=90 -> vertical)
    assert panel.crosshair_h.angle == 0
    assert panel.crosshair_v.angle == 90
    assert panel._price_tag.toPlainText() == "110.50"
    assert panel._price_tag.isVisible()
    # D2/Q33: the price chip lives in the Y-axis lane, left-anchored at the
    # plot's vertical axis line (scene x >= view_rect.right()) so it grows
    # rightward into the lane instead of being right-aligned inside the plot.
    vb = panel.price_plot.getViewBox()
    view_rect = vb.mapRectToScene(vb.rect())
    view_right = view_rect.right()
    lane_right = view_right + float(panel.price_plot.getAxis('right').width())
    assert panel._price_tag.pos().x() >= view_right
    # anchor (0,0.5) — left-anchored, vertically centred; stored as Point
    anchor = panel._price_tag.anchor
    assert float(anchor.x()) == pytest.approx(0.0)
    assert float(anchor.y()) == pytest.approx(0.5)
    # bounding rect fully inside the Y-axis lane (never clipped)
    br = panel._price_tag.mapRectToScene(panel._price_tag.boundingRect())
    assert br.left() >= view_right - 1e-6
    assert br.right() <= lane_right + 1e-6
    expected = datetime.fromtimestamp(bar.ts, tz=timezone.utc).strftime("%m/%d %H:%M")
    assert panel._time_tag.toPlainText() == expected
    assert panel._time_tag.isVisible()


def test_price_axis_on_right(panel):
    assert panel.price_plot.getAxis('right').isVisible()
    assert not panel.price_plot.getAxis('left').isVisible()
    assert panel.volume_plot.getAxis('right').isVisible()
    assert panel.osc_plot.getAxis('right').isVisible()


def test_time_chip_snaps_to_nearest_bar(panel, sample_bars):
    bar = sample_bars[100]
    # Offset the cursor 20s from the bar (within the half-bar tolerance)
    pos = scene_point(panel, bar.ts + 20, 110.5)
    panel._update_crosshair(pos)
    expected = datetime.fromtimestamp(bar.ts, tz=timezone.utc).strftime("%m/%d %H:%M")
    assert panel._time_tag.toPlainText() == expected


def test_hover_over_axis_area_hides_everything(panel):
    vb = panel.price_plot.getViewBox()
    rect = vb.mapRectToScene(vb.rect())
    below_axis = rect.center()
    below_axis.setY(rect.bottom() + 10)
    panel._update_crosshair(scene_point(panel, vb.viewRect().center().x(), 110.0))
    assert panel._time_tag.isVisible()

    panel._update_crosshair(below_axis)
    assert not panel.crosshair_v.isVisible()
    assert not panel.crosshair_h.isVisible()
    assert not panel._price_tag.isVisible()
    assert not panel._time_tag.isVisible()


def test_leave_event_hides_crosshair(panel, sample_bars):
    bar = sample_bars[50]
    panel._update_crosshair(scene_point(panel, bar.ts, 105.0))
    assert panel.crosshair_v.isVisible()

    leave = QEvent(QEvent.Type.Leave)
    panel.eventFilter(panel.price_plot.viewport(), leave)

    assert not panel.crosshair_v.isVisible()
    assert not panel.crosshair_h.isVisible()
    assert not panel._price_tag.isVisible()
    assert not panel._time_tag.isVisible()


def test_on_mouse_moved_updates_crosshair(panel, sample_bars):
    # sigMouseMoved stops firing when the mouse exits the scene; the leave
    # filter is what clears the crosshair.
    bar = sample_bars[50]
    panel._on_mouse_moved(scene_point(panel, bar.ts, 105.0))
    assert panel.crosshair_h.isVisible()


def test_real_mouse_move_shows_crosshair(panel, sample_bars):
    # Regression: the crosshair was originally wired to sigMouseHover, which
    # emits hovered items (origin coords), not the cursor position. Drive the
    # real Qt event path to ensure the chips actually appear.
    bar = sample_bars[100]
    QTest.qWait(50)  # let pyqtgraph's move-event throttle expire
    scene = scene_point(panel, bar.ts, 110.5)
    QTest.mouseMove(
        panel.price_plot.viewport(),
        pos=QPoint(int(scene.x()), int(scene.y())),
    )
    QApplication.processEvents()

    assert panel.crosshair_v.isVisible()
    assert panel.crosshair_h.isVisible()
    assert float(panel._price_tag.toPlainText().replace(",", "")) == pytest.approx(
        110.5, abs=0.1
    )
    expected = datetime.fromtimestamp(bar.ts, tz=timezone.utc).strftime("%m/%d %H:%M")
    assert panel._time_tag.toPlainText() == expected
    assert panel._time_tag.isVisible()


def test_real_mouse_move_over_axis_hides_crosshair(panel, sample_bars):
    # Different coords than the previous test: Qt coalesces a move sent to
    # the exact position the global cursor already occupies.
    bar = sample_bars[60]
    QTest.qWait(50)
    inside = scene_point(panel, bar.ts, 108.0)
    QTest.mouseMove(
        panel.price_plot.viewport(), pos=QPoint(int(inside.x()), int(inside.y()))
    )
    QApplication.processEvents()
    assert panel._price_tag.isVisible()

    vb = panel.price_plot.getViewBox()
    rect = vb.mapRectToScene(vb.rect())
    # pyqtgraph throttles move events (mouseRateLimit=100/s); back off so the
    # second synthetic move is not swallowed. Probe the right axis strip.
    QTest.qWait(50)
    QTest.mouseMove(
        panel.price_plot.viewport(),
        pos=QPoint(int(rect.right() + 8), int(rect.center().y())),
    )
    QApplication.processEvents()
    assert not panel.crosshair_v.isVisible()
    assert not panel.crosshair_h.isVisible()
    assert not panel._price_tag.isVisible()
    assert not panel._time_tag.isVisible()


def test_empty_bars_hides_crosshair(chart_panel, qapp):
    chart_panel.resize(900, 600)
    chart_panel.show()
    qapp.processEvents()
    vb = chart_panel.price_plot.getViewBox()
    center = vb.mapToScene(vb.rect().center())
    chart_panel._update_crosshair(center)
    assert not chart_panel.crosshair_v.isVisible()
    chart_panel.hide()


def test_update_chart_with_empty_list_hides_stale_crosshair(panel, sample_bars):
    bar = sample_bars[50]
    panel._update_crosshair(scene_point(panel, bar.ts, 105.0))
    assert panel.crosshair_v.isVisible()
    panel.update_chart([])
    assert not panel.crosshair_v.isVisible()
    assert not panel._price_tag.isVisible()


def test_time_chip_respects_tz_offset(qapp, sample_bars):
    panel = ChartPanel(tz_offset=18000)  # EST: axis labels 5h behind UTC
    panel.update_chart(sample_bars)
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    bar = sample_bars[100]
    panel._update_crosshair(scene_point(panel, bar.ts, 110.5))
    expected = datetime.fromtimestamp(bar.ts - 18000, tz=timezone.utc).strftime("%m/%d %H:%M")
    assert panel._time_tag.toPlainText() == expected
    utc_text = datetime.fromtimestamp(bar.ts, tz=timezone.utc).strftime("%m/%d %H:%M")
    assert panel._time_tag.toPlainText() != utc_text
    panel.hide()
    panel.close()
