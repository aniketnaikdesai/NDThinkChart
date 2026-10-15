"""D21-11 / D21.13 — right dock hide/show toggles + horizontal collapse.

Focused offscreen integration tests for the single right dock region (D18),
re-pointed to the **Portfolio-only** dock (D41 / S6):

* the dock's **title bar** is the Portfolio panel's header strip, whose label is
  the retained ``summary_label`` — a ``DiagonalStrikeButton("Account Summary")``.
  With the two-section container gone there is exactly one visible label and it
  is the hide/show toggle; and
* the dock's ``windowTitle()`` **and** ``objectName()`` are ``"Portfolio"``, the
  region's stable title-keyed handle (the rename contract, S6).

Clicking the button hides/shows the panel body while the button itself stays
visible and struck (VIS-D21.1). Hiding the section collapses the whole region
horizontally to a single-button strip — the dock's minimum is relaxed below
``RIGHT_DOCK_MIN_WIDTH`` and the width is pinned explicitly — so the chart
reclaims the space (AC-D21.13.3). Hiding the region via the dock's own
visibility toggle never resets the panel's collapsed state, and a fully
collapsed region is treated as hidden by the cross-clamp so the watchlist
regains its own cap (T05).

Harness note: the D19 ``ToolbarScroll`` wrapper keeps the toolbar from pinning
the chart area, so the harness runs with the toolbar visible and no masking.
"""

from PyQt6.QtWidgets import QDockWidget

from ui.active_portfolio_panel import ActivePortfolioPanel
from ui.dock_layout import (
    CHART_MIN_WIDTH,
    RIGHT_DOCK_MIN_WIDTH,
    WATCHLIST_MIN_WIDTH,
    watchlist_max_width,
)
from ui.main_window import RIGHT_DOCK_COLLAPSED_MIN_WIDTH
from ui.visual_conventions import DiagonalStrikeButton


def _boot(monkeypatch, qapp, width=1600, height=900):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()
    return win


# ── D21-11-T01 / AC-D21.13.1 — title bar button + summary are one toggle ─────

def test_D21_11_T01_title_and_summary_are_toggle_buttons(monkeypatch, qapp):
    """D21-11-T01: dock title/objectName "Portfolio"; title bar = summary button."""
    win = _boot(monkeypatch, qapp)
    try:
        dock = win.right_dock

        # The single right dock is the renamed Portfolio region (S6): its title
        # and objectName are "Portfolio" and its widget IS the Portfolio panel
        # directly (no two-section container).
        assert isinstance(dock, QDockWidget)
        assert dock.windowTitle() == "Portfolio"
        assert dock.objectName() == "Portfolio"
        assert isinstance(dock.widget(), ActivePortfolioPanel)
        assert dock.widget() is win.portfolio_panel

        # The dock's title-bar widget is the Portfolio panel's header strip, and
        # its label is a checkable DiagonalStrikeButton.
        pf_btn = win.portfolio_panel.summary_label
        assert dock.titleBarWidget() is win.portfolio_panel.summary_label
        assert isinstance(pf_btn, DiagonalStrikeButton)
        assert pf_btn.text() == "Account Summary"
        assert pf_btn.isCheckable()
        assert pf_btn.isVisible()
        assert pf_btn.isChecked() and not pf_btn.is_struck()

        # Clicking the button toggles the panel body.
        pf_btn.click()
        qapp.processEvents()
        assert win.portfolio_panel.is_collapsed()
        assert not win.portfolio_panel.body.isVisible()
        pf_btn.click()
        qapp.processEvents()
        assert not win.portfolio_panel.is_collapsed()
        assert win.portfolio_panel.body.isVisible()
    finally:
        win.close()


# ── D21-11-T02 / AC-D21.13.2 — collapsing removes the body, dock stays real ──

def test_D21_11_T02_collapsed_section_keeps_real_window(monkeypatch, qapp):
    """D21-11-T02: collapse removes the body; the dock stays a visible window."""
    win = _boot(monkeypatch, qapp)
    try:
        pf = win.portfolio_panel
        # Expanded, the body contributes height: the panel needs more room than
        # its header button alone.
        hint_h0 = pf.sizeHint().height()
        assert pf.body.isVisible()
        assert hint_h0 > pf.summary_label.sizeHint().height()

        # Collapse: the body goes and the panel shrinks to just its header
        # button (AC-D21.13.2's surviving collapse outcome), while the dock
        # remains visible and non-zero width — still a real docked window, so
        # the geometry assertions below measure something (not a hidden dock).
        pf.summary_label.click()
        qapp.processEvents()
        assert pf.is_collapsed()
        assert not pf.body.isVisible()
        assert pf.sizeHint().height() <= pf.summary_label.sizeHint().height() + 2, (
            pf.sizeHint().height(), pf.summary_label.sizeHint().height()
        )
        assert win.right_dock.isVisible()
        assert win.right_dock.width() > 0

        # Re-show: the body is back and the panel needs its full height again.
        pf.summary_label.click()
        qapp.processEvents()
        assert not pf.is_collapsed()
        assert pf.body.isVisible()
        assert abs(pf.sizeHint().height() - hint_h0) <= 2
    finally:
        win.close()


# ── D21-11-T03 / AC-D21.13.3 — collapsed region collapses horizontally ──────

def test_D21_11_T03_collapsed_region_collapses_horizontally(monkeypatch, qapp):
    """D21-11-T03: collapsed -> button strip width; showing restores 200px."""
    win = _boot(monkeypatch, qapp)
    try:
        calls = []
        original = win._resize_docks_guarded

        def spy(docks, sizes):
            calls.append((list(docks), [int(s) for s in sizes]))
            return original(docks, sizes)

        monkeypatch.setattr(win, "_resize_docks_guarded", spy)

        win.portfolio_panel.summary_label.click()
        qapp.processEvents()

        collapsed_w = win._right_dock_collapsed_min_width
        assert win._right_region_collapsed
        # Relaxed minimum: below RIGHT_DOCK_MIN_WIDTH, at/above the baseline, and
        # wide enough for the retained toggle button.
        assert win.right_dock.minimumWidth() == collapsed_w
        assert collapsed_w < RIGHT_DOCK_MIN_WIDTH
        assert collapsed_w >= RIGHT_DOCK_COLLAPSED_MIN_WIDTH
        assert collapsed_w >= win.portfolio_panel.summary_label.sizeHint().width()

        # The dock was explicitly reduced to the button strip via
        # _resize_docks_guarded([right_dock], [collapsed_width]).
        assert any(
            docks == [win.right_dock] and sizes == [collapsed_w]
            for docks, sizes in calls
        ), calls
        assert win.right_dock.width() <= collapsed_w + 2, win.right_dock.width()
        assert win.right_dock.width() < RIGHT_DOCK_MIN_WIDTH
        # The chart keeps at least its minimum width.
        assert win._chart_area_width() >= CHART_MIN_WIDTH - 1

        # Show the panel again: the 200px minimum and the cross-clamp are back.
        win.portfolio_panel.summary_label.click()
        qapp.processEvents()
        assert not win._right_region_collapsed
        assert win.right_dock.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
        assert win.portfolio_panel.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
        assert win.right_dock.isVisible()
        assert win._right_dock_available()
    finally:
        win.close()


# ── D21-11-T04 / AC-D21.13.4 — strike reflects the panel's hidden state ─────

def test_D21_11_T04_strike_reflects_hidden_state(monkeypatch, qapp):
    """D21-11-T04: the button is struck iff the panel is hidden."""
    win = _boot(monkeypatch, qapp)
    try:
        pf_btn = win.portfolio_panel.summary_label
        # The struck button is the dock's title-bar control (the retained one).
        assert win.right_dock.titleBarWidget() is pf_btn
        assert not pf_btn.is_struck()

        pf_btn.click()
        qapp.processEvents()
        assert pf_btn.is_struck() and not pf_btn.isChecked()

        pf_btn.click()
        qapp.processEvents()
        assert not pf_btn.is_struck()
        assert pf_btn.isChecked()
    finally:
        win.close()


# ── D21-11-T05 / AC-D21.13.1 — region toggle; collapsed = hidden ─────────────

def test_D21_11_T05_region_toggle_and_collapsed_crossclamp(monkeypatch, qapp):
    """D21-11-T05: hiding the region keeps panel state; collapsed region is hidden."""
    win = _boot(monkeypatch, qapp)
    try:
        win.portfolio_panel.summary_label.click()
        qapp.processEvents()
        assert win.portfolio_panel.is_collapsed()
        assert win._right_region_collapsed

        # The whole-region toggle is now the dock's own visibility (the DOM
        # toolbar button is gone, D41). It must not reset the panel's hidden
        # state.
        win.right_dock.setVisible(False)
        qapp.processEvents()
        assert not win.right_dock.isVisible()
        win.right_dock.setVisible(True)
        qapp.processEvents()
        assert win.right_dock.isVisible()
        assert win.portfolio_panel.is_collapsed()
        assert win._right_region_collapsed

        # A collapsed region is treated as hidden by _apply_dock_widths: the B3
        # cross-clamp is never consulted, so the watchlist regains its own cap.
        plan_calls = []
        original_plan = win._plan_dock_widths

        def spy_plan(*args, **kwargs):
            plan_calls.append(args)
            return original_plan(*args, **kwargs)

        monkeypatch.setattr(win, "_plan_dock_widths", spy_plan)

        for _ in range(8):
            win._apply_dock_widths(10 ** 6)
            qapp.processEvents()

        assert not plan_calls, "cross-clamp must not run for a collapsed region"
        ca = win._chart_area_width()
        cap = watchlist_max_width(ca)
        assert win.watchlist_dock.width() <= cap + 1, (
            win.watchlist_dock.width(), cap
        )
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH
        assert ca >= CHART_MIN_WIDTH - 1
        collapsed_w = win._right_dock_collapsed_min_width
        assert win.right_dock.width() <= collapsed_w + 2
        # The panel's hidden state still persists after the clamp cycle.
        assert win.portfolio_panel.is_collapsed()
    finally:
        win.close()
