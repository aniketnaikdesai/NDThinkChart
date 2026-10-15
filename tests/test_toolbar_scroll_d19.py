"""T53 / D19 Phase 1 — the central-widget toolbar wrapped in a horizontal
``QScrollArea`` (AC-D19.4 / AC-D19.5).

Boots a **real** ``ui.main_window.MainWindow`` on the offscreen Qt platform
(``IBApiClient.connect`` monkeypatched to a no-op so the TWS-seeking managers
never open a socket, matching the D17/D18 suites) and verifies that the toolbar
stays inside the central widget as a single ~36px row while its full natural
width lives inside a frameless horizontal ``QScrollArea``. That keeps the
toolbar's ~1716px ``minimumSizeHint`` from pinning the central widget, so the
central widget can shrink toward the dock-minima + chart-minimum budget
(``CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH`` = 750px).
"""

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QScrollArea,
    QToolBar,
    QWidget,
)

from ui.dock_layout import CHART_MIN_WIDTH, RIGHT_DOCK_MIN_WIDTH
from ui.watchlist_panel import WATCHLIST_MIN_WIDTH

#: Feasible minimum for the central widget once the toolbar no longer dominates:
#: chart minimum + both dock minima.
_CENTRAL_MIN_BUDGET = (
    CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH
)  # 750px

#: Every toolbar control that must stay reachable through the scroll region.
_CONTROL_NAMES = (
    "symbol_input",
    "tf_combo",
    "load_btn",
    "mode_combo",
    "studies_btn",
    "alarms_btn",
    "alarm_mode_btn",
    "sound_btn",
    "ext_hours_btn",
    "tz_combo",
    "draw_combo",
    "draw_set_combo",
    "draw_sets_btn",
    "draw_delete_btn",
    "conn_badge",
)

_WIDE_SIZE = (2600, 900)
_NARROW_SIZE = (1200, 700)


def _make_window(monkeypatch, qapp, width: int, height: int = 900):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()
    return win


# ── T53-T01 / AC-D19.4(i) — toolbar stays in central, no longer pins min ─────

def test_T53_T01_toolbar_stays_in_central_and_min_drops(monkeypatch, qapp):
    """T53-T01 / AC-D19.4(i): central min-hint <= 750; toolbar stays in central."""
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        central = win.centralWidget()
        assert central is not None

        # The toolbar no longer dominates the central widget's minimum.
        assert central.minimumSizeHint().width() <= _CENTRAL_MIN_BUDGET, (
            central.minimumSizeHint().width(),
            _CENTRAL_MIN_BUDGET,
        )

        # The toolbar is still a descendant of the central widget (not moved to a
        # QMainWindow toolbar area).
        toolbar = win.findChild(QWidget, "MainToolbar")
        assert toolbar is not None
        assert central.isAncestorOf(toolbar), "toolbar left the central widget"

        # Item 0 of the central layout is the scroll wrapper, not the toolbar.
        layout = central.layout()
        assert layout is not None and layout.count() >= 1
        item0 = layout.itemAt(0).widget()
        assert isinstance(item0, QScrollArea), type(item0)
        assert item0.objectName() == "ToolbarScroll"

        # No QMainWindow toolbar area was used.
        assert win.findChildren(QToolBar) == [], "addToolBar was used"
    finally:
        win.close()


# ── T53-T02 / AC-D19.4(ii) — controls reachable via scroll; one row ──────────

def test_T53_T02_controls_reachable_via_scroll(monkeypatch, qapp):
    """T53-T02 / AC-D19.4(ii): h-scroll range > 0 narrow; controls visible wide."""
    # ── Narrow: content is wider than the viewport, so the scroll range is > 0 ─
    win = _make_window(monkeypatch, qapp, *_NARROW_SIZE)
    try:
        wrapper = win.findChild(QScrollArea, "ToolbarScroll")
        assert wrapper is not None
        toolbar = win.findChild(QWidget, "MainToolbar")
        assert toolbar is not None

        assert wrapper.horizontalScrollBar().maximum() > 0, (
            wrapper.horizontalScrollBar().maximum(),
            wrapper.viewport().width(),
            toolbar.width(),
        )

        # Every control remains a descendant of the scroll content (the toolbar),
        # i.e. reachable by scrolling.
        for name in _CONTROL_NAMES:
            control = getattr(win, name, None)
            assert control is not None, name
            assert toolbar.isAncestorOf(control), f"{name} left the scroll region"

        # One row, ~36px tall (not wrapped onto multiple rows).
        assert toolbar.height() <= 40, toolbar.height()
    finally:
        win.close()

    # ── Wide: every control lies within the viewport, directly visible ────────
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper = win.findChild(QScrollArea, "ToolbarScroll")
        toolbar = win.findChild(QWidget, "MainToolbar")
        assert wrapper is not None and toolbar is not None
        viewport = wrapper.viewport()
        assert viewport.width() >= toolbar.width(), (
            viewport.width(),
            toolbar.width(),
        )

        for name in _CONTROL_NAMES:
            control = getattr(win, name)
            top_left = control.mapTo(viewport, QPoint(0, 0))
            assert top_left.x() >= 0, (name, top_left.x())
            assert top_left.x() + control.width() <= viewport.width(), (
                name,
                top_left.x() + control.width(),
                viewport.width(),
            )

        assert toolbar.height() <= 40, toolbar.height()
    finally:
        win.close()


# ── T53-T03 / AC-D19.5 — central width tracks the window, not the toolbar ────

def test_T53_T03_central_width_tracks_window(monkeypatch, qapp):
    """T53-T03 / AC-D19.5: central width shrinks with the window, not pinned."""
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wide_central = win.centralWidget().width()
        assert wide_central > 0

        win.resize(*_NARROW_SIZE)
        qapp.processEvents()
        narrow_central = win.centralWidget().width()

        assert narrow_central < wide_central, (narrow_central, wide_central)
        # Not pinned at the toolbar's ~1716px minimum.
        assert narrow_central < 1700, narrow_central
    finally:
        win.close()


# ── T53-T04 / structural mechanism — wrapper properties + scroll region ──────

def test_T53_T04_wrapper_mechanism(monkeypatch, qapp):
    """T53-T04: wrapper properties, objectNames, conn_badge inside scroll region."""
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper = win.findChild(QScrollArea, "ToolbarScroll")
        assert wrapper is not None

        assert wrapper.frameShape() == QFrame.Shape.NoFrame
        assert wrapper.widgetResizable() is False
        assert wrapper.horizontalScrollBarPolicy() == (
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        assert wrapper.verticalScrollBarPolicy() == (
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        toolbar = win.findChild(QWidget, "MainToolbar")
        assert toolbar is not None

        # D20: the content row stays 36px, but the wrapper's fixed height is
        # DERIVED — the content row PLUS the horizontal scrollbar's reserved
        # lane below it (offscreen 54px, macOS ~52px). Never a literal 36px
        # container (R36).
        from ui.main_window import TOOLBAR_CONTENT_HEIGHT

        assert TOOLBAR_CONTENT_HEIGHT == 36
        assert toolbar.height() == TOOLBAR_CONTENT_HEIGHT, toolbar.height()
        assert wrapper.height() == (
            toolbar.height() + wrapper.horizontalScrollBar().sizeHint().height()
        ), (wrapper.height(), toolbar.height())
        assert wrapper.minimumHeight() == wrapper.height()
        assert wrapper.maximumHeight() == wrapper.height()

        # Stable objectNames.
        assert wrapper.objectName() == "ToolbarScroll"

        # conn_badge and the toolbar's controls live inside the scroll content.
        assert toolbar.isAncestorOf(win.conn_badge), "conn_badge left the toolbar"
        assert wrapper.widget() is toolbar, "scroll content is not the toolbar"
    finally:
        win.close()
