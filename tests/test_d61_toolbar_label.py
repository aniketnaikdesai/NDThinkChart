"""P22-T1 / D61 — the toolbar ``Symbol:`` label renders in full at every
window width (AC-D61.1) while the D19/D20 strip geometry holds (AC-D61.2).

Boots a **real** ``ui.main_window.MainWindow`` on the offscreen Qt platform
(``IBApiClient.connect`` monkeypatched to a no-op, matching the D17/D18/D19
harnesses) at a wide width and at a narrowed scrolling width. The top-left
label must read ``Symbol:`` in full — never truncated to ``SY`` — and no
other toolbar label may be clipped by its container. The D19/D20 suites run
unchanged alongside as the geometry guard; this module additionally pins the
content-row (~36px) and strip (~50-52px) heights plus scroll reachability.
"""

import pytest
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QLabel, QScrollArea, QWidget

from ui.main_window import TOOLBAR_CONTENT_HEIGHT

_WIDE_SIZE = (2600, 900)
_NARROW_SIZE = (1200, 700)

#: Every toolbar control that must stay reachable through the scroll region
#: (same inventory as the D19/D20 suites).
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


def _symbol_label(toolbar):
    """The top-left ``Symbol:`` static label."""
    for label in toolbar.findChildren(QLabel):
        if label.text() == "Symbol:":
            return label
    raise AssertionError("Symbol: label missing from the toolbar")


def _assert_label_in_full(label):
    """A label renders its text in full — never squeezed below text width."""
    text = label.text()
    assert text, "unexpected empty toolbar label"
    need = label.fontMetrics().horizontalAdvance(text)
    assert label.width() >= need, (
        "toolbar label clipped by its container",
        text,
        label.width(),
        need,
    )


# ── P22-T1-AC1 — Symbol: in full at wide width ───────────────────────────────

def test_P22_T1_AC1_symbol_label_full_at_wide_width(monkeypatch, qapp):
    """AC-D61.1 (wide): the top-left label reads ``Symbol:`` in full."""
    win = _make_window(monkeypatch, qapp, *_WIDE_SIZE)
    try:
        wrapper, toolbar, viewport, _hbar = _parts(win)
        label = _symbol_label(toolbar)
        assert label.text() == "Symbol:"
        _assert_label_in_full(label)
        # Fully inside the viewport (directly visible, not scrolled away).
        top_left = label.mapTo(viewport, QPoint(0, 0))
        assert top_left.x() >= 0, ("Symbol: label left of viewport", top_left.x())
        assert top_left.x() + label.width() <= viewport.width(), (
            "Symbol: label extends past the viewport",
            top_left.x() + label.width(),
            viewport.width(),
        )
    finally:
        win.close()


# ── P22-T1-AC1 — Symbol: in full at narrowed (scrolling) width ───────────────

def test_P22_T1_AC1_symbol_label_full_at_scrolling_width(monkeypatch, qapp):
    """AC-D61.1 (narrow): scrolling — the label keeps full ``Symbol:`` width.

    The label may be scrolled out of view, but its field keeps room for the
    full text (width never squeezed below the text advance), so scrolling
    back reveals ``Symbol:`` in full instead of a clipped ``SY``.
    """
    win = _make_window(monkeypatch, qapp, *_NARROW_SIZE)
    try:
        wrapper, toolbar, _viewport, hbar = _parts(win)
        # Narrow enough to scroll: the D19 wrapper stays the overflow path.
        assert hbar.maximum() > 0, (
            "expected horizontal overflow at the narrowed width",
            hbar.maximum(),
        )
        label = _symbol_label(toolbar)
        assert label.text() == "Symbol:"
        _assert_label_in_full(label)
    finally:
        win.close()


# ── P22-T1-AC1 — sweep: no other toolbar label clipped ───────────────────────

@pytest.mark.parametrize("size", [_WIDE_SIZE, _NARROW_SIZE], ids=["wide", "narrow"])
def test_P22_T1_AC1_no_toolbar_label_clipped(monkeypatch, qapp, size):
    """AC-D61.1 (sweep): no toolbar label is clipped by its container."""
    win = _make_window(monkeypatch, qapp, *size)
    try:
        _wrapper, toolbar, _viewport, _hbar = _parts(win)
        labels = [
            label
            for label in toolbar.findChildren(QLabel)
            if label.text()
        ]
        assert labels, "no text-bearing labels found in the toolbar"
        for label in labels:
            _assert_label_in_full(label)
    finally:
        win.close()


# ── P22-T1-AC2 — strip geometry + reachability in this module ───────────────

@pytest.mark.parametrize("size", [_WIDE_SIZE, _NARROW_SIZE], ids=["wide", "narrow"])
def test_P22_T1_AC2_strip_geometry_and_reachability(monkeypatch, qapp, size):
    """AC-D61.2: single ~36px row, ~50-52px strip, controls reachable."""
    win = _make_window(monkeypatch, qapp, *size)
    try:
        wrapper, toolbar, _viewport, _hbar = _parts(win)
        # Single ~36px content row (not wrapped, not stretched).
        assert toolbar.height() == TOOLBAR_CONTENT_HEIGHT, (
            toolbar.height(),
            TOOLBAR_CONTENT_HEIGHT,
        )
        # Total strip = content row + the scrollbar's own reserved lane.
        expected_strip = (
            TOOLBAR_CONTENT_HEIGHT
            + wrapper.horizontalScrollBar().sizeHint().height()
        )
        assert wrapper.height() == expected_strip, (
            wrapper.height(),
            expected_strip,
        )
        # Every control stays reachable inside the scroll region.
        for name in _CONTROL_NAMES:
            control = getattr(win, name, None)
            assert control is not None, name
            assert toolbar.isAncestorOf(control), f"{name} left the scroll region"
    finally:
        win.close()
