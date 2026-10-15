"""D41 Phase-3 guard: the right dock is Portfolio-only (AC-D41.7 / S6).

Pins the three things D41 changed about the right region:
1. it is ONE ``QDockWidget`` titled/objectNamed ``"Portfolio"``, whose widget is
   the retained Portfolio panel and whose title bar IS that panel's
   ``summary_label`` — and no "Active Trader" dock or widget exists anywhere;
2. the dock is visible and usable at full-screen size, with a non-zero width;
3. clicking the summary label collapses it to the single-button strip and lets
   the chart reclaim the width, and clicking again restores it — with no new
   QSettings key written.

The removed title may appear in this file only inside a NEGATIVE assertion
(pinned by ``test_stale_title_is_negative_only``), which is what lets the
removal guard in ``tests/test_d41_removal.py`` allow-list this suite.
"""

import ast
import time
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient

#: The removed dock title, built at runtime so this checker's own comparison
#: cannot be mistaken for a live use of the stale literal.
_STALE_TITLE = "Active" + " Trader"


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod
    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(1920, 1080)  # full-screen-sized (the original D17/D18 symptom)
    win.show()
    qapp.processEvents()
    return win


def _settle(qapp, *, turns: int = 80, deadline_s: float = 5.0) -> None:
    """Drain pending singleShot(0) callbacks — the dock clamp is deferred.

    Bounded by a fixed turn count AND a monotonic deadline, never unbounded
    (same discipline as the D10/D13 harness).
    """
    deadline = time.monotonic() + deadline_s
    for _ in range(turns):
        qapp.processEvents()
        if time.monotonic() >= deadline:
            break


def _right_area_docks(win):
    return [d for d in win.findChildren(QDockWidget)
            if win.dockWidgetArea(d) == Qt.DockWidgetArea.RightDockWidgetArea]


def test_portfolio_only_dock_shape_and_visibility(monkeypatch, qapp):
    """P1-T61-T11 / AC-D41.7: one Portfolio dock, visible, non-zero width."""
    win = _make_window(monkeypatch, qapp)
    try:
        dock = win.right_dock
        assert dock.windowTitle() == "Portfolio"
        assert dock.objectName() == "Portfolio"
        assert dock.widget() is win.portfolio_panel, (
            "the dock must host the Portfolio panel directly")
        assert dock.titleBarWidget() is win.portfolio_panel.summary_label, (
            "the panel's summary_label must be the dock's title bar")

        # No stale dock or widget survives anywhere in the tree.
        assert win.findChild(QDockWidget, "Active Trader") is None
        assert not [d for d in _right_area_docks(win)
                    if d.windowTitle() == "Active Trader"]

        # Visible and usable at full-screen size, with a non-zero width.
        assert dock.isVisible(), "the right dock must be visible in full screen"
        assert dock.width() > 0
        assert win.portfolio_panel.width() > 0

        # The region's width stays inside the configured bounds.
        from ui.dock_layout import RIGHT_DOCK_MIN_WIDTH
        assert dock.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
    finally:
        win.close()


def test_summary_label_collapses_and_restores(monkeypatch, qapp):
    """P1-T61-T21 / AC-D41.7: the retained header button collapses the dock and
    the chart reclaims the width; clicking again restores. No new QSettings key."""
    win = _make_window(monkeypatch, qapp)
    try:
        label = win.portfolio_panel.summary_label
        assert label.isCheckable(), "the header must be the collapse control"

        keys_before = set(win._settings.allKeys())
        chart_before = win._chart_area_width()

        # Collapse via the retained header button.
        label.setChecked(False)
        _settle(qapp)
        assert win._right_region_collapsed is True, "the dock did not collapse"
        collapsed_w = win._right_dock_collapsed_min_width
        assert win.right_dock.minimumWidth() == collapsed_w, (
            "the collapsed dock must be pinned to the button strip width")
        chart_collapsed = win._chart_area_width()
        assert chart_collapsed >= chart_before, (
            "the chart must reclaim the width the dock gave up")

        # Restore.
        label.setChecked(True)
        _settle(qapp)
        assert win._right_region_collapsed is False, "the dock did not restore"
        from ui.dock_layout import RIGHT_DOCK_MIN_WIDTH
        assert win.right_dock.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
        assert win._chart_area_width() <= chart_collapsed

        # No new right-dock persistence key appeared.
        new_keys = set(win._settings.allKeys()) - keys_before
        assert not [k for k in new_keys if "dock" in k.lower()
                    or "right" in k.lower()], (
            f"collapse must not write a new QSettings key: {sorted(new_keys)}")
    finally:
        win.close()


def test_stale_title_is_negative_only():
    """P1-T61-T31 / AC-D41.1: this suite may name the removed title only inside
    a negative assertion. Comments and docstrings are documentation and are
    allowed; any occurrence in *code* must sit inside an ``assert`` whose test is
    a negative check (checked per statement, so continuation lines count)."""
    src = Path(__file__).read_text()
    tree = ast.parse(src)

    # Line ranges that are documentation (module/class/function docstrings).
    doc_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                doc_lines.update(
                    range(first.lineno, (first.end_lineno or first.lineno) + 1))

    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    def enclosing_assert(node):
        cur = node
        while cur is not None:
            if isinstance(cur, ast.Assert):
                return cur
            cur = parents.get(id(cur))
        return None

    code_hits = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)
                 and _STALE_TITLE in n.value
                 and n.lineno not in doc_lines]
    assert code_hits, "this suite should still pin the removed title's absence"
    for node in code_hits:
        stmt = enclosing_assert(node)
        assert stmt is not None, (
            f"the removed title is not inside an assert (line {node.lineno})")
        text = ast.get_source_segment(src, stmt) or ""
        assert "not " in text or "is None" in text, (
            f"the removed title is used outside a negative assertion: {text!r}")
