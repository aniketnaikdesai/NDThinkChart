"""T30 / ESC-010 — D14 mid-drag symbol change (TR-17 / AC-D14.4).

A symbol change that lands while a drawing gesture is in flight (the D14
watchlist double-click path -> ``MainWindow.load_chart`` -> ``ChartPanel``)
must not leave the overlay or the mouse router holding on to torn-down
items. The historical failure mode (``docs/debug/debug_log.md``) is a
pyqtgraph ``GraphicsScene.dragItem`` reference to a drawing item that was
removed mid-gesture: the next drag event then dispatches to
``InfiniteLine.mouseDragEvent`` on a deleted C++ object and raises

    RuntimeError: wrapped C/C++ object of type InfiniteLine has been deleted

These tests drive the real double-click entry point while a drawing drag is
in flight and assert (a) zero unhandled ``RuntimeError``/``RuntimeWarning``,
(b) the new symbol's chart is displayed, and (c) the TR-17 router reset:
the draft/drag is cleared and ``_active_mode == RouterMode.IDLE``.
"""

import time
import warnings

import pyqtgraph as pg
import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDockWidget

from data.bar_cache import BarCache
from data.models import Bar, Drawing
from ui.chart_mouse_router import RouterMode

# The single right region (Active Trader ladder + Portfolio, D18 Phase 3) is
# unrelated to the D14 gesture/mode reset under test.
_RIGHT_DOCKS = ("Active Trader",)

# pyqtgraph's GraphicsScene only converts a press into a drag after this long
# (see GraphicsScene.minDragTime = 0.5s) or a movement beyond 5px.
_DRAG_SETTLE_S = 0.6


class FakeEvent:
    """Minimal pyqtgraph mouse-event double (button / scenePos / isFinish)."""

    def __init__(self, button, scene_pos, is_finish=False):
        self._button = button
        self._scene_pos = scene_pos
        self._is_finish = is_finish

    def button(self):
        return self._button

    def scenePos(self):
        return self._scene_pos

    def isFinish(self):
        return self._is_finish

    def accept(self):
        pass

    def ignore(self):
        pass


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    monkeypatch.setattr(IBApiClient, "connected", property(lambda self: True))

    from ui.main_window import MainWindow

    win = MainWindow()
    # The D14 path must only reach the (stubbed) managers, never a socket.
    win.md_manager.req_historical_data = lambda **k: 1
    win.rt_manager.subscribe = lambda *a, **k: 2
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in _RIGHT_DOCKS:
            dock.hide()
    qapp.processEvents()
    return win


def _move(panel, pos: QPoint, buttons: bool = False):
    """Send a mouse-move; with ``buttons`` held it becomes a drag."""
    held = Qt.MouseButton.LeftButton if buttons else Qt.MouseButton.NoButton
    event = QMouseEvent(
        QEvent.Type.MouseMove, QPointF(pos),
        Qt.MouseButton.NoButton, held,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(panel.price_plot.viewport(), event)
    QApplication.processEvents()
    time.sleep(0.03)  # respect pyqtgraph's mouseRateLimit (100/s)


def _start_item_drag(panel, scene_pos):
    """Hover then press+drag so pyqtgraph assigns ``scene.dragItem``.

    Only an item that accepts the hover becomes the scene's drag item; the
    drawing overlay's own ``InfiniteLine``s are created non-movable, so the
    test marks the target line movable first — which is exactly the state
    the historical InfiniteLine use-after-free was reported in.
    """
    ov = panel.drawing_overlay
    lines = [it for it in ov._items.get(1, []) if isinstance(it, pg.InfiniteLine)]
    assert lines, "expected a horizontal InfiniteLine drawing"
    for line in lines:
        line.setMovable(True)

    vp = panel.price_plot.viewport()
    pt = QPoint(int(scene_pos.x()), int(scene_pos.y()))
    _move(panel, pt)          # hover registers the line as a drag candidate
    _move(panel, pt)
    QTest.mousePress(vp, Qt.MouseButton.LeftButton, pos=pt)
    QApplication.processEvents()
    time.sleep(_DRAG_SETTLE_S)
    _move(panel, QPoint(pt.x() + 30, pt.y() + 30), buttons=True)
    return pt


# ── T30-T01 / AC-D14.4 — mid-drag watchlist double-click ─────────────────────

def test_T30_T01_mid_drag_symbol_change_no_exception_and_renders(
    monkeypatch, qapp, sample_bars
):
    """T30-T01 / AC-D14.4: D14 double-click while a drag is in flight."""
    aapl_bars = [
        Bar("AAPL", "5 mins", 1_700_000_000 + i * 60, 200 + i * 0.1,
            200.5 + i * 0.1, 199.5 + i * 0.1, 200 + i * 0.1, 500.0)
        for i in range(40)
    ]
    BarCache.save_bars(aapl_bars)

    win = _make_window(monkeypatch, qapp)
    try:
        cp = win.chart_panel
        cp.resize(900, 600)
        win._current_symbol = "TEST"
        cp.set_symbol("TEST")
        cp.update_chart(sample_bars)
        qapp.processEvents()

        ov = cp.drawing_overlay
        ov.set_data("TEST", [Drawing(
            symbol="TEST", kind="horizontal", payload={"y": 112.0}, id=1)], [])
        ov.set_tool("cursor")
        qapp.processEvents()

        vb = cp.price_plot.getViewBox()
        scene_pos = vb.mapViewToScene(pg.Point(sample_bars[10].ts, 112.0))
        pt = _start_item_drag(cp, scene_pos)

        # A real drag is in flight: the scene is tracking the drawing item.
        scene = cp.price_plot.scene()
        assert scene.dragItem is not None
        dragged_item = scene.dragItem
        assert ov._drag is not None

        errors = []
        warnings_seen = []
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            # D14 path: double-click a different watchlist row mid-drag.
            try:
                win._on_watchlist_row_double_clicked("AAPL")
                qapp.processEvents()
                # The in-flight gesture keeps emitting while the button is held;
                # these must not dispatch to the removed item.
                _move(cp, QPoint(pt.x() + 40, pt.y() + 40), buttons=True)
                _move(cp, QPoint(pt.x() + 60, pt.y() + 50), buttons=True)
            except Exception as exc:  # noqa: BLE001 — the failure under test
                errors.append(exc)
            finally:
                QTest.mouseRelease(
                    cp.price_plot.viewport(), Qt.MouseButton.LeftButton,
                    pos=QPoint(pt.x() + 60, pt.y() + 50))
                qapp.processEvents()
            warnings_seen = [w for w in caught]

        assert errors == [], f"unhandled exception during mid-drag symbol change: {errors!r}"
        runtime_warnings = [w for w in warnings_seen
                            if issubclass(w.category, RuntimeWarning)]
        assert runtime_warnings == [], runtime_warnings

        # The defensive dragItem clearing (drawing_overlay._detach_item) ran:
        # the scene no longer references the removed drawing item.
        assert scene.dragItem is not dragged_item

        # AC-D14.4: the new symbol's chart is displayed (renders normally).
        assert cp._symbol == "AAPL"
        assert win._current_symbol == "AAPL"
        assert len(cp._bars) == len(aapl_bars)
        assert [b.symbol for b in cp._bars] == ["AAPL"] * len(aapl_bars)
    finally:
        win.close()


# ── T30-T02 / TR-17 — router mode reset + draft/drag clearing ────────────────

def test_T30_T02_symbol_change_clears_draft_and_resets_router_mode(
    chart_panel, sample_bars, qapp
):
    """T30-T02 / TR-17: DRAWING (mid-draft) -> symbol change -> IDLE."""
    panel = chart_panel
    panel.resize(900, 600)
    panel.show()
    panel.set_symbol("TEST")
    panel.update_chart(sample_bars)
    qapp.processEvents()

    # Start a draft gesture: tool armed, first press begins the draft.
    panel.set_drawing_tool("zone")
    assert panel.mouse_router.active_mode == RouterMode.DRAWING

    vb = panel.price_plot.getViewBox()
    mid_ts = panel._bars[len(panel._bars) // 2].ts
    press = FakeEvent(Qt.MouseButton.LeftButton,
                      vb.mapViewToScene(pg.Point(mid_ts, 110.0)))
    assert panel.mouse_router.view_mouse_press(press) is True
    assert panel.drawing_overlay._draft is not None
    preview = list(panel.drawing_overlay._draft["preview"])
    assert preview

    # Symbol change (the overlay reset half of the D14 path, unit-level).
    panel.set_symbol("AAPL")
    qapp.processEvents()

    assert panel.drawing_overlay._draft is None
    assert panel.drawing_overlay._drag is None
    assert panel.drawing_overlay.tool_active() is False
    assert panel.mouse_router.active_mode == RouterMode.IDLE
    assert all(item.scene() is None for item in preview)

    # The cursor-mode body-drag sub-state is cleared by the same path.
    panel.set_symbol("TEST")
    panel.update_chart(sample_bars)
    qapp.processEvents()
    ov = panel.drawing_overlay
    ov.set_data("TEST", [Drawing(
        symbol="TEST", kind="horizontal", payload={"y": 110.0}, id=7)], [])
    ov.set_tool("cursor")
    hit = FakeEvent(Qt.MouseButton.LeftButton,
                    vb.mapViewToScene(pg.Point(mid_ts, 110.0)))
    assert panel.mouse_router.view_mouse_press(hit) is True
    assert ov._drag is not None

    panel.set_symbol("AAPL")
    qapp.processEvents()
    assert ov._drag is None
    assert panel.mouse_router.active_mode == RouterMode.IDLE


# ── T30-T03 / AC-D14.1-3 preserved — existing D14 no-op paths unchanged ──────

def test_T30_T03_existing_d14_noop_paths_unchanged(qapp):
    """T30-T03 / AC-D14.1-3: re-run the existing D14 decision + emit tests."""
    # Imported lazily so the manifest's new file does not alter the originals.
    from tests.test_watchlist import (
        test_should_load_on_double_click,
        test_panel_double_click_emits_symbol,
    )

    test_should_load_on_double_click()
    test_panel_double_click_emits_symbol(qapp)
