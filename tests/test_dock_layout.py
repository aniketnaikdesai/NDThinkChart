"""Offscreen unit tests for the pure dock-width model (D17/D18 Phase 1).

These tests must not require a QApplication and must not import any Qt module;
``ui/dock_layout`` is pure Python by design. ``tests/conftest.py`` may import Qt
for the rest of the suite, but the module under test and the T45-T01 import
isolation check do not depend on it.
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import ui.dock_layout as dock_layout
from ui.dock_layout import (
    CHART_MIN_WIDTH,
    WATCHLIST_MIN_WIDTH,
    DEFAULT_WATCHLIST_WIDTH,
    RIGHT_DOCK_MIN_WIDTH,
    WATCHLIST_CAP_FRACTION,
    RIGHT_DOCK_CAP_FRACTION,
    watchlist_max_width,
    right_dock_max_width,
    plan_dock_widths,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── T45-T01: import is Qt-free and needs no QApplication ─────────────────────

def test_T45_T01_module_imports_without_qt_or_qapplication():
    """Import the module in an isolated interpreter and assert no Qt module is
    loaded."""
    script = textwrap.dedent(
        """
        import sys
        import ui.dock_layout  # noqa: F401

        qt_modules = sorted(
            name for name in sys.modules
            if name == "PyQt6" or name.startswith("PyQt6.")
            or name == "pyqtgraph" or name.startswith("pyqtgraph.")
            or name == "PySide6" or name.startswith("PySide6.")
        )
        assert not qt_modules, "Qt modules were imported: %r" % (qt_modules,)
        assert "PyQt6.QtWidgets" not in sys.modules
        print("OK")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"isolated import failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "OK" in result.stdout


def test_T45_T01_source_imports_no_qt():
    """A static guard: the source imports no PyQt6/pyqtgraph/Qt symbol."""
    source = (Path("ui/dock_layout.py")).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert "PyQt6" not in stripped
            assert "pyqtgraph" not in stripped
            assert "Qt" not in stripped


# ── T45-T02: constants ───────────────────────────────────────────────────────

def test_T45_T02_constants():
    assert CHART_MIN_WIDTH == 400
    assert WATCHLIST_MIN_WIDTH == 150
    assert DEFAULT_WATCHLIST_WIDTH == 220
    assert RIGHT_DOCK_MIN_WIDTH == 200
    assert WATCHLIST_CAP_FRACTION == 0.50
    assert RIGHT_DOCK_CAP_FRACTION == 0.40


def test_T45_T02_chart_min_width_agrees_with_watchlist_panel():
    from ui.watchlist_panel import CHART_MIN_WIDTH as panel_chart_min
    from ui.watchlist_panel import WATCHLIST_MIN_WIDTH as panel_watchlist_min
    assert dock_layout.CHART_MIN_WIDTH == panel_chart_min
    assert dock_layout.WATCHLIST_MIN_WIDTH == panel_watchlist_min


# ── T45-T03: watchlist_max_width ─────────────────────────────────────────────

@pytest.mark.parametrize("chart_area_w", [1400, 900, 800, 600, 100, 400, 8000])
def test_T45_T03_watchlist_max_width_formula(chart_area_w):
    expected = max(WATCHLIST_MIN_WIDTH, min(int(chart_area_w * 0.50),
                                            chart_area_w - CHART_MIN_WIDTH))
    got = watchlist_max_width(chart_area_w)
    assert got == expected
    assert got >= WATCHLIST_MIN_WIDTH
    assert isinstance(got, int)


def test_T45_T03_narrow_case_chart_minimum_binds():
    # 600 - 400 = 200 < 0.50*600 = 300 -> chart-minimum term binds.
    assert watchlist_max_width(600) == 200
    # Tiny window -> flat cap below the dock minimum -> minimum wins.
    assert watchlist_max_width(100) == WATCHLIST_MIN_WIDTH


# ── T45-T04: right_dock_max_width ────────────────────────────────────────────

@pytest.mark.parametrize("chart_area_w", [1400, 900, 800, 600, 100, 400, 8000])
def test_T45_T04_right_dock_max_width_formula(chart_area_w):
    expected = max(RIGHT_DOCK_MIN_WIDTH, min(int(chart_area_w * 0.40),
                                             chart_area_w - CHART_MIN_WIDTH))
    got = right_dock_max_width(chart_area_w)
    assert got == expected
    assert got >= RIGHT_DOCK_MIN_WIDTH
    assert isinstance(got, int)


def test_T45_T04_narrow_case_chart_minimum_binds():
    # 600 - 400 = 200 < 0.40*600 = 240 -> chart-minimum term binds.
    assert right_dock_max_width(600) == 200
    # Tiny window -> flat cap below the dock minimum -> minimum wins.
    assert right_dock_max_width(100) == RIGHT_DOCK_MIN_WIDTH


# ── T45-T05: normal cross-clamp ──────────────────────────────────────────────

def test_T45_T05_caps_hold_and_chart_remainder():
    chart_area_w = 1400
    left, right = plan_dock_widths(chart_area_w, 999999, 999999)
    assert left <= watchlist_max_width(chart_area_w)
    assert right <= right_dock_max_width(chart_area_w)
    assert chart_area_w - left - right >= CHART_MIN_WIDTH
    assert isinstance(left, int) and isinstance(right, int)


def test_T45_T05_enlarging_left_shrinks_right():
    chart_area_w = 1000
    # Both requested at their flat caps: 500 + 400 = 900 leaves only 100 for the
    # chart, so the cross-clamp must bite.
    left_a, right_a = plan_dock_widths(chart_area_w, 500, 400)
    left_b, right_b = plan_dock_widths(chart_area_w, 600, 400)
    assert left_b <= watchlist_max_width(chart_area_w)
    assert right_b <= right_dock_max_width(chart_area_w)
    assert chart_area_w - left_b - right_b >= CHART_MIN_WIDTH
    # Asking the left for more must not grow the total; the right shrinks.
    assert right_b <= right_a
    assert left_b >= left_a


def test_T45_T05_enlarging_right_shrinks_left():
    chart_area_w = 1000
    left_a, right_a = plan_dock_widths(chart_area_w, 500, 400)
    left_b, right_b = plan_dock_widths(chart_area_w, 500, 500)
    assert right_b <= right_dock_max_width(chart_area_w)
    assert chart_area_w - left_b - right_b >= CHART_MIN_WIDTH
    assert left_b <= left_a


def test_T45_T05_small_requests_pass_through():
    chart_area_w = 1400
    left, right = plan_dock_widths(chart_area_w, 220, 250)
    assert (left, right) == (220, 250)
    assert chart_area_w - left - right >= CHART_MIN_WIDTH


# ── T45-T06: edge cases ──────────────────────────────────────────────────────

def test_T45_T06_tiny_window_returns_dock_minimums_without_raising():
    # chart_area_w=100: flat caps (50/40) are below the dock minimums, and
    # 100 - 400 is infeasible. Dock minimums must win, no exception.
    left, right = plan_dock_widths(100, 999999, 999999)
    assert left == WATCHLIST_MIN_WIDTH
    assert right == RIGHT_DOCK_MIN_WIDTH
    assert isinstance(left, int) and isinstance(right, int)


def test_T45_T06_infeasible_window_returns_dock_minimums():
    # Even at chart_area_w = 400 the two dock minimums (350) exceed the budget
    # (0), so the chart minimum yields and the minimums are returned.
    left, right = plan_dock_widths(400, 500, 500)
    assert left == WATCHLIST_MIN_WIDTH
    assert right == RIGHT_DOCK_MIN_WIDTH


def test_T45_T06_both_at_max_never_below_min():
    chart_area_w = 1000
    left, right = plan_dock_widths(chart_area_w, 100000, 100000)
    assert left >= WATCHLIST_MIN_WIDTH
    assert right >= RIGHT_DOCK_MIN_WIDTH
    assert left <= watchlist_max_width(chart_area_w)
    assert right <= right_dock_max_width(chart_area_w)
    assert chart_area_w - left - right >= CHART_MIN_WIDTH


def test_T45_T06_one_side_over_budget():
    chart_area_w = 1200
    left, right = plan_dock_widths(chart_area_w, 100000, 10)
    assert left <= watchlist_max_width(chart_area_w)
    assert right >= RIGHT_DOCK_MIN_WIDTH
    assert right <= right_dock_max_width(chart_area_w)
    assert chart_area_w - left - right >= CHART_MIN_WIDTH


@pytest.mark.parametrize("chart_area_w", [0, 1, 100, 400, 550, 700, 1000, 1400])
def test_T45_T06_never_raises_and_integer_stable(chart_area_w):
    for req_l, req_r in [(0, 0), (10, 10), (100000, 100000), (100000, 1), (1, 100000)]:
        left, right = plan_dock_widths(chart_area_w, req_l, req_r)
        assert isinstance(left, int) and isinstance(right, int)
        # Repeatable.
        assert plan_dock_widths(chart_area_w, req_l, req_r) == (left, right)


# ── T52 regression: never below a dock minimum (ESC-026) ─────────────────────

def test_T52_T01_grid_never_below_dock_minimum():
    """T52-T01: over a chart-area × request grid, every width is >= its minimum.

    This is the coarse grid the ESC-026 diagnosis used (chart_area 100..3000
    step 50 × requests {0, 200, 400, 700, 100000}²) — the pre-fix helper returned
    108/1475 below-minimum combinations; after the shrink-loop fix there must be
    zero.
    """
    chart_areas = list(range(100, 3001, 50))
    requests = (0, 200, 400, 700, 100000)
    for chart_area_w in chart_areas:
        for req_l in requests:
            for req_r in requests:
                left, right = plan_dock_widths(chart_area_w, req_l, req_r)
                assert left >= WATCHLIST_MIN_WIDTH, (
                    chart_area_w, req_l, req_r, left, right,
                )
                assert right >= RIGHT_DOCK_MIN_WIDTH, (
                    chart_area_w, req_l, req_r, left, right,
                )


def test_T52_T02_reproduced_one_sided_over_budget():
    """T52-T02: the exact one-sided cases that returned a sub-minimum width.

    Pre-fix: ``(750, 100000, 200) -> (350, 0)`` and
    ``(750, 200, 0) -> (175, 175)``. Both must now keep each dock at/above its
    own minimum (componentwise ``>= (150, 200)``), and the (350, 0) / (175, 175)
    results are explicitly failures.
    """
    left, right = plan_dock_widths(750, 100000, 200)
    assert (left, right) >= (WATCHLIST_MIN_WIDTH, RIGHT_DOCK_MIN_WIDTH), (left, right)
    assert left >= WATCHLIST_MIN_WIDTH, (left, right)
    assert right >= RIGHT_DOCK_MIN_WIDTH, (left, right)
    assert (left, right) != (350, 0), "regressed to the pre-fix (350, 0) result"

    left, right = plan_dock_widths(750, 200, 0)
    assert (left, right) >= (WATCHLIST_MIN_WIDTH, RIGHT_DOCK_MIN_WIDTH), (left, right)
    assert left >= WATCHLIST_MIN_WIDTH, (left, right)
    assert right >= RIGHT_DOCK_MIN_WIDTH, (left, right)
    assert (left, right) != (175, 175), "regressed to the pre-fix (175, 175) result"


def test_T52_T03_precedence_infeasible_vs_feasible_over_budget():
    """T52-T03: infeasible window -> dock minimums win; feasible over-budget ->
    chart minimum preserved with both widths at/above their minimums.

    Uses the task's example inputs: ``plan_dock_widths(400, 500, 500)`` is
    infeasible (350 > 400-400=0) and must return exactly (150, 200); a feasible
    over-budget case (``plan_dock_widths(1000, 500, 400)``) must keep
    ``chart_area_w - left - right >= CHART_MIN_WIDTH`` while neither width drops
    below its minimum.
    """
    # Infeasible: the two dock minimums alone exceed chart_area_w - CHART_MIN_WIDTH.
    left, right = plan_dock_widths(400, 500, 500)
    assert (left, right) == (WATCHLIST_MIN_WIDTH, RIGHT_DOCK_MIN_WIDTH), (left, right)

    # Feasible but the combined request is over budget: the chart minimum holds
    # and no dock minimum is crossed.
    chart_area_w = 1000
    left, right = plan_dock_widths(chart_area_w, 500, 400)
    assert left >= WATCHLIST_MIN_WIDTH, (left, right)
    assert right >= RIGHT_DOCK_MIN_WIDTH, (left, right)
    assert chart_area_w - left - right >= CHART_MIN_WIDTH, (left, right)

    # Explicit high-request feasible case too (both request huge).
    left, right = plan_dock_widths(chart_area_w, 100000, 100000)
    assert left >= WATCHLIST_MIN_WIDTH, (left, right)
    assert right >= RIGHT_DOCK_MIN_WIDTH, (left, right)
    assert chart_area_w - left - right >= CHART_MIN_WIDTH, (left, right)


# ── T52-T04: MainWindow apply path after the T49 in-place repair is removed ──

def test_T52_T04_mainwindow_apply_path_without_t49_repair(monkeypatch, qapp):
    """T52-T04: the D18 guarantees rest solely on the pure helper.

    Offscreen ``MainWindow`` (no live TWS) driving the shared apply path with the
    T49 repair removed: grow the right dock to its cap, shrink it below its
    minimum, and cross-clamp both docks. Asserts the 40% cap, each dock minimum,
    and the chart-area minimum all still hold.
    """
    from PyQt6.QtCore import Qt
    from ui.dock_layout import watchlist_max_width, right_dock_max_width

    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(1600, 900)
    win.show()
    qapp.processEvents()
    central_layout = win.centralWidget().layout()
    if central_layout is not None and central_layout.count() > 0:
        toolbar = central_layout.itemAt(0).widget()
        if toolbar is not None:
            toolbar.hide()
    qapp.processEvents()
    win.resize(1600, 900)
    qapp.processEvents()

    try:
        assert win.right_dock.isVisible()

        # ── Over-cap drag: right stops at floor(0.40 × chart_area) ──────────
        for _ in range(14):
            win._apply_dock_widths(None, 10 ** 6)
            qapp.processEvents()
        ca = win._chart_area_width()
        cap = right_dock_max_width(ca)
        assert win.right_dock.width() <= cap + 1, (win.right_dock.width(), cap)
        assert win.right_dock.width() >= RIGHT_DOCK_MIN_WIDTH, win.right_dock.width()

        # ── Under-min drag: no width drops below its dock minimum ───────────
        for _ in range(6):
            win._apply_dock_widths(None, 0)
            qapp.processEvents()
        assert win.right_dock.width() == RIGHT_DOCK_MIN_WIDTH, win.right_dock.width()
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH

        # ── Cross-clamp: enlarging one dock keeps chart >= CHART_MIN_WIDTH ──
        ca = win._chart_area_width()
        win.resizeDocks(
            [win.watchlist_dock, win.right_dock],
            [watchlist_max_width(ca) - 10, right_dock_max_width(ca) - 10],
            Qt.Orientation.Horizontal,
        )
        qapp.processEvents()
        left_before = win.watchlist_dock.width()
        win._apply_dock_widths(None, 10 ** 6)
        qapp.processEvents()
        assert win._chart_area_width() >= CHART_MIN_WIDTH, win._chart_area_width()
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH
        assert win.right_dock.width() >= RIGHT_DOCK_MIN_WIDTH
        assert win.watchlist_dock.width() <= left_before

        ca = win._chart_area_width()
        win.resizeDocks(
            [win.watchlist_dock, win.right_dock],
            [watchlist_max_width(ca) - 10, right_dock_max_width(ca) - 10],
            Qt.Orientation.Horizontal,
        )
        qapp.processEvents()
        right_before = win.right_dock.width()
        win._apply_dock_widths(10 ** 6, None)
        qapp.processEvents()
        assert win._chart_area_width() >= CHART_MIN_WIDTH, win._chart_area_width()
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH
        assert win.right_dock.width() >= RIGHT_DOCK_MIN_WIDTH
        assert win.right_dock.width() <= right_before
    finally:
        win.close()
