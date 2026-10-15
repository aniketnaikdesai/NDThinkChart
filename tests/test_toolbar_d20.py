"""T62 / D20 Phase 2 — the derived ToolbarScroll height, the reserved
horizontal-scrollbar lane, and label legibility (AC-D20.1 .. AC-D20.5).

D19 wrapped the toolbar in a frameless horizontal ``QScrollArea``
(``ToolbarScroll``) to stop its ~1716px ``minimumSizeHint`` from pinning the
central widget. D20 then changed the wrapper's *fixed* height from a literal
36px to a **derived** value: the 36px content row PLUS the horizontal
scrollbar's own ``sizeHint().height()`` (offscreen 54px, macOS ~52px). That
reserves a lane entirely below the content so the scrollbar never overlaps the
label/button descenders.

This suite boots the **real** ``ui.main_window.MainWindow`` on the offscreen Qt
platform (``IBApiClient.connect`` monkeypatched to a no-op, matching the
D17/D18/D19 harnesses) and checks both the overflow (narrow, scrollbar shown)
and non-overflow (wide, scrollbar hidden) states.

Lane/overlap checks deliberately use the **mapped** form
``horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y()`` and
``viewport().height()`` — never ``geometry()``, which reports ``top == 0`` for
the offscreen scrollbar and would make the check vacuous.
"""

import pytest
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolBar,
    QWidget,
)

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
    "dom_btn",
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


def _parts(win):
    """Return the (wrapper, toolbar, viewport, hbar) quartet for a window."""
    wrapper = win.findChild(QScrollArea, "ToolbarScroll")
    toolbar = win.findChild(QWidget, "MainToolbar")
    assert wrapper is not None, "ToolbarScroll wrapper missing"
    assert toolbar is not None, "MainToolbar missing"
    return wrapper, toolbar, wrapper.viewport(), wrapper.horizontalScrollBar()


def _rect_in_wrapper(widget, wrapper, local_rect):
    """Map a widget-local ``QRect`` into ``wrapper`` coordinates."""
    top_left = widget.mapTo(wrapper, local_rect.topLeft())
    return QRect(top_left, local_rect.size())


def _lane_rect(wrapper, hbar):
    """The horizontal scrollbar's own rect, mapped into wrapper coordinates.

    Uses the mapped form (never ``geometry()``) so it is correct offscreen.
    """
    return _rect_in_wrapper(hbar, wrapper, hbar.rect())


def _viewport_rect(wrapper, viewport):
    return _rect_in_wrapper(viewport, wrapper, viewport.rect())


def _text_rects_in_wrapper(toolbar, wrapper):
    """Yield ``(name, text, rect)`` for every text-bearing toolbar control.

    Covers the toolbar's ``QLabel``/``QPushButton`` text (the AC-D20.1 wording)
    plus ``QComboBox`` current text, so a scrollbar overlapping *any* visible
    glyph is caught. The text's bounding rect is computed with
    ``QFontMetrics.boundingRect`` using the widget's real alignment, so the
    vertical extent reflects where the glyphs actually render.
    """
    widgets: list[QWidget] = []
    widgets += toolbar.findChildren(QLabel)
    widgets += toolbar.findChildren(QPushButton)
    widgets += toolbar.findChildren(QComboBox)

    rects = []
    for widget in widgets:
        if isinstance(widget, QComboBox):
            text = widget.currentText()
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        elif isinstance(widget, QPushButton):
            text = widget.text()
            align = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        else:  # QLabel
            text = widget.text()
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        if not text:
            continue

        local = widget.fontMetrics().boundingRect(widget.rect(), int(align), text)
        name = widget.objectName() or type(widget).__name__
        rects.append((name, text, _rect_in_wrapper(widget, wrapper, local)))
    return rects


def _assert_texts_legible(wrapper, toolbar, viewport, hbar, *, expect_shown):
    """Every toolbar text is inside the content area and clear of the lane."""
    # The scrollbar is in the state the caller expects.
    assert hbar.isVisible() is expect_shown, (
        "horizontal scrollbar visibility",
        hbar.isVisible(),
        expect_shown,
    )

    # Reserved lane (when shown) sits entirely below the 36px content row.
    assert viewport.height() >= toolbar.height(), (
        viewport.height(),
        toolbar.height(),
    )
    if expect_shown:
        lane_y = hbar.mapTo(wrapper, QPoint(0, 0)).y()
        assert lane_y >= toolbar.height(), (
            "scrollbar lane overlaps the content row",
            lane_y,
            toolbar.height(),
        )

    # The toolbar's own (content) rect, mapped into the wrapper.
    toolbar_rect = _rect_in_wrapper(toolbar, wrapper, toolbar.rect())
    lane = _lane_rect(wrapper, hbar)

    rects = _text_rects_in_wrapper(toolbar, wrapper)
    assert rects, "no text-bearing controls found in the toolbar"

    for name, text, rect in rects:
        # Non-vacuous: the text is inside the toolbar content area...
        assert toolbar_rect.contains(rect), (
            "text escaped the toolbar content area",
            name,
            text,
            rect,
            toolbar_rect,
        )
        # ...and does not overlap the horizontal scrollbar's reserved lane.
        assert not rect.intersects(lane), (
            "text intersects the horizontal scrollbar lane",
            name,
            text,
            rect,
            lane,
        )


# ── T62-T01 / AC-D20.1 — legible while the scrollbar is shown (overflow) ─────

def test_T62_T01_labels_legible_scrollbar_shown(monkeypatch, qapp):
    """T62-T01 / AC-D20.1: narrow window — no glyph under the shown scrollbar."""
    win = _make_window(monkeypatch, qapp, *_NARROW_SIZE)
    try:
        wrapper, toolbar, viewport, hbar = _parts(win)
        _assert_texts_legible(
            wrapper, toolbar, viewport, hbar, expect_shown=True
        )
        # Content stays a single row.
        assert toolbar.height() <= 40, toolbar.height()
    finally:
        win.close()


# ── T62-T02 / AC-D20.1 — legible while the scrollbar is hidden (no overflow) ─

def test_T62_T02_labels_legible_scrollbar_hidden(monkeypatch, qapp):
    """T62-T02 / AC-D20.1: wide window — labels unclipped with no scrollbar."""
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper, toolbar, viewport, hbar = _parts(win)
        _assert_texts_legible(
            wrapper, toolbar, viewport, hbar, expect_shown=False
        )
        # Content stays a single row.
        assert toolbar.height() <= 40, toolbar.height()
    finally:
        win.close()


# ── T62-T03 / AC-D20.2 — derived container height; 36px content row ──────────

def test_T62_T03_derived_height_and_reserved_lane(monkeypatch, qapp):
    """T62-T03 / AC-D20.2: container = content row + scrollbar extent (< 60)."""
    from ui.main_window import TOOLBAR_CONTENT_HEIGHT

    win = _make_window(monkeypatch, qapp, *_NARROW_SIZE)
    try:
        wrapper, toolbar, viewport, hbar = _parts(win)

        # Content row is exactly the 36px single source of truth.
        assert TOOLBAR_CONTENT_HEIGHT == 36
        assert toolbar.height() == TOOLBAR_CONTENT_HEIGHT, toolbar.height()

        # Container is the DERIVED height — never a literal 36px (R36).
        assert wrapper.height() == (
            toolbar.height() + hbar.sizeHint().height()
        ), (wrapper.height(), toolbar.height(), hbar.sizeHint().height())
        assert wrapper.height() < 60, wrapper.height()

        # The reserved lane equals the scrollbar's own extent...
        assert wrapper.height() - toolbar.height() == hbar.sizeHint().height(), (
            wrapper.height(),
            toolbar.height(),
            hbar.sizeHint().height(),
        )
        # ...and sits entirely below the content.
        assert hbar.isVisible() is True
        assert hbar.mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height(), (
            hbar.mapTo(wrapper, QPoint(0, 0)).y(),
            toolbar.height(),
        )
        assert viewport.height() >= toolbar.height(), (
            viewport.height(),
            toolbar.height(),
        )

        # Explicitly NOT asserting a literal [50, 52] bound: that is the macOS
        # figure, while the offscreen derived value is 54px (plan RC-D20-1).
    finally:
        win.close()


# ── T62-T04 / AC-D20.3 — scrollbar as-needed in its reserved lane (B8) ───────

def test_T62_T04_scrollbar_as_needed_in_lane(monkeypatch, qapp):
    """T62-T04 / AC-D20.3: hidden when it fits, shown below content when not."""
    from ui.main_window import TOOLBAR_CONTENT_HEIGHT

    # ── Wide: content fits, scrollbar hidden, strip height unchanged ─────────
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper, toolbar, _viewport, hbar = _parts(win)
        assert hbar.isVisible() is False, "scrollbar shown when content fits"
        assert wrapper.height() == (
            TOOLBAR_CONTENT_HEIGHT + hbar.sizeHint().height()
        ), (wrapper.height(), TOOLBAR_CONTENT_HEIGHT, hbar.sizeHint().height())
    finally:
        win.close()

    # ── Narrow: content overflows, scrollbar shown in its lane below content ─
    win = _make_window(monkeypatch, qapp, *_NARROW_SIZE)
    try:
        wrapper, toolbar, _viewport, hbar = _parts(win)
        assert hbar.isVisible() is True, "scrollbar hidden when content overflows"
        assert hbar.mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height(), (
            hbar.mapTo(wrapper, QPoint(0, 0)).y(),
            toolbar.height(),
        )
        # Strip height is stable across both states — the lane is reserved even
        # when the scrollbar is hidden.
        assert wrapper.height() == (
            TOOLBAR_CONTENT_HEIGHT + hbar.sizeHint().height()
        ), (wrapper.height(), TOOLBAR_CONTENT_HEIGHT, hbar.sizeHint().height())
    finally:
        win.close()


# ── T62-T05 / AC-D20.4 — D19 scroll/elide reachability preserved ─────────────

def test_T62_T05_d19_reachability_preserved(monkeypatch, qapp):
    """T62-T05 / AC-D20.4: scroll range > 0 narrow; all controls visible wide."""
    # ── Narrow: scrollable, every control inside the scroll content ──────────
    win = _make_window(monkeypatch, qapp, *_NARROW_SIZE)
    try:
        wrapper, toolbar, _viewport, hbar = _parts(win)
        assert hbar.maximum() > 0, (
            hbar.maximum(),
            wrapper.viewport().width(),
            toolbar.width(),
        )
        for name in _CONTROL_NAMES:
            control = getattr(win, name, None)
            assert control is not None, name
            assert toolbar.isAncestorOf(control), f"{name} left the scroll content"
    finally:
        win.close()

    # ── Wide: every control lies within the viewport ─────────────────────────
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper, toolbar, viewport, _hbar = _parts(win)
        assert viewport.width() >= toolbar.width(), (
            viewport.width(),
            toolbar.width(),
        )
        for name in _CONTROL_NAMES:
            control = getattr(win, name, None)
            assert control is not None, name
            top_left = control.mapTo(viewport, QPoint(0, 0))
            assert top_left.x() >= 0, (name, top_left.x())
            assert top_left.x() + control.width() <= viewport.width(), (
                name,
                top_left.x() + control.width(),
                viewport.width(),
            )
    finally:
        win.close()


# ── T62-T06 / AC-D20.5 — single row, inside central, no QMainWindow toolbar ──

def test_T62_T06_single_row_inside_central(monkeypatch, qapp):
    """T62-T06 / AC-D20.5: one row, central-widget QScrollArea, no addToolBar."""
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper, toolbar, _viewport, _hbar = _parts(win)
        central = win.centralWidget()
        assert central is not None

        # Single row (not wrapped onto multiple rows).
        assert toolbar.height() <= 40, toolbar.height()

        # The toolbar stays a descendant of the central widget.
        assert central.isAncestorOf(toolbar), "toolbar left the central widget"

        # Item 0 of the central layout is the ToolbarScroll QScrollArea.
        layout = central.layout()
        assert layout is not None and layout.count() >= 1
        item0 = layout.itemAt(0).widget()
        assert isinstance(item0, QScrollArea), type(item0)
        assert item0.objectName() == "ToolbarScroll"

        # No QMainWindow toolbar area was used (rejected in D19/B5).
        assert win.findChildren(QToolBar) == [], "addToolBar was used"
    finally:
        win.close()
