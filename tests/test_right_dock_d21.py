"""D21-11 / D21.13 — right dock hide/show toggles + horizontal collapse.

Focused offscreen integration tests for the single right dock region (D18)
gaining the two D21.13 toggles:

* the dock's **title bar** is the Active Trader panel's header strip, whose
  label is a ``DiagonalStrikeButton("Active Trader")``; and
* the portfolio's ``summary_label`` is a ``DiagonalStrikeButton("Account
  Summary")``.

Clicking either button hides/shows the matching panel body while the button
itself stays visible and struck (VIS-D21.1). Hiding one panel collapses it in
height and the other expands into the vacated space (AC-D21.13.2). Hiding both
collapses the whole region horizontally to a two-button strip — the dock's
minimum is relaxed below ``RIGHT_DOCK_MIN_WIDTH`` and the width is pinned
explicitly — so the chart reclaims the space (AC-D21.13.3). ``_on_dom_toggled``
stays the whole-region toggle and never resets per-panel state; a fully
collapsed region is treated as hidden by the cross-clamp so the watchlist
regains its own cap (T05).

Harness note: the D19 ``ToolbarScroll`` wrapper keeps the toolbar from pinning
the chart area, so the harness runs with the toolbar visible and no masking.
"""

import pytest
from PyQt6.QtWidgets import QDockWidget

from ui.active_portfolio_panel import ActivePortfolioPanel
from ui.active_trader_panel import ActiveTraderPanel
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


# ── D21-11-T01 / AC-D21.13.1 — title + summary are mapped toggle buttons ─────

def test_D21_11_T01_title_and_summary_are_toggle_buttons(monkeypatch, qapp):
    """D21-11-T01: title bar = 'Active Trader' button; summary = 'Account Summary'."""
    win = _boot(monkeypatch, qapp)
    try:
        dock = win.right_dock

        # The dock's title-bar widget is the Active Trader panel's header strip,
        # and its label is a checkable DiagonalStrikeButton.
        assert dock.titleBarWidget() is win.active_trader.header_bar
        at_btn = win.active_trader.header_button
        assert isinstance(at_btn, DiagonalStrikeButton)
        assert at_btn.text() == "Active Trader"
        assert at_btn.isCheckable()
        assert win.active_trader.header_bar.isAncestorOf(at_btn)
        assert at_btn.isChecked() and not at_btn.is_struck()

        # The portfolio summary label is the Account Summary toggle button.
        pf_btn = win.portfolio_panel.summary_label
        assert isinstance(pf_btn, DiagonalStrikeButton)
        assert pf_btn.text() == "Account Summary"
        assert pf_btn.isCheckable()
        assert pf_btn.isChecked() and not pf_btn.is_struck()

        # Clicking each button toggles the matching panel body.
        at_btn.click()
        qapp.processEvents()
        assert win.active_trader.is_collapsed()
        assert not win.active_trader.body.isVisible()
        at_btn.click()
        qapp.processEvents()
        assert not win.active_trader.is_collapsed()
        assert win.active_trader.body.isVisible()

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


# ── D21-11-T02 / AC-D21.13.2 — one hidden collapses, the other expands ───────

def test_D21_11_T02_one_hidden_collapses_other_expands(monkeypatch, qapp):
    """D21-11-T02: hiding one panel collapses it; the other fills the space."""
    win = _boot(monkeypatch, qapp)
    try:
        at, pf = win.active_trader, win.portfolio_panel
        at_h0, pf_h0 = at.height(), pf.height()
        assert at_h0 > 0 and pf_h0 > 0

        # Hide the portfolio: it collapses to just its button, Active Trader grows.
        pf.summary_label.click()
        qapp.processEvents()
        assert pf.is_collapsed()
        assert pf.height() <= pf.summary_label.height() + 2, (
            pf.height(), pf.summary_label.height()
        )
        assert at.height() > at_h0, (at.height(), at_h0)

        # Re-show: the original split is restored.
        pf.summary_label.click()
        qapp.processEvents()
        assert not pf.is_collapsed()
        assert abs(pf.height() - pf_h0) <= 2
        assert abs(at.height() - at_h0) <= 2

        # Hide the Active Trader body: it collapses; the portfolio fills.
        at.header_button.click()
        qapp.processEvents()
        assert at.is_collapsed()
        assert not at.body.isVisible()
        assert pf.height() > pf_h0, (pf.height(), pf_h0)

        # Re-show restores.
        at.header_button.click()
        qapp.processEvents()
        assert not at.is_collapsed()
        assert abs(at.height() - at_h0) <= 2
        assert abs(pf.height() - pf_h0) <= 2
    finally:
        win.close()


# ── D21-11-T03 / AC-D21.13.3 — both hidden collapses horizontally ────────────

def test_D21_11_T03_both_hidden_collapses_horizontally(monkeypatch, qapp):
    """D21-11-T03: both hidden -> button strip width; showing restores 200px."""
    win = _boot(monkeypatch, qapp)
    try:
        calls = []
        original = win._resize_docks_guarded

        def spy(docks, sizes):
            calls.append((list(docks), [int(s) for s in sizes]))
            return original(docks, sizes)

        monkeypatch.setattr(win, "_resize_docks_guarded", spy)

        win.active_trader.header_button.click()
        win.portfolio_panel.summary_label.click()
        qapp.processEvents()

        collapsed_w = win._right_dock_collapsed_min_width
        assert win._right_region_collapsed
        # Relaxed minimum: below RIGHT_DOCK_MIN_WIDTH, at/above the baseline, and
        # wide enough for both toggle buttons.
        assert win.right_dock.minimumWidth() == collapsed_w
        assert collapsed_w < RIGHT_DOCK_MIN_WIDTH
        assert collapsed_w >= RIGHT_DOCK_COLLAPSED_MIN_WIDTH
        assert collapsed_w >= win.active_trader.header_button.sizeHint().width()
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

        # Show one panel again: the 200px minimum and the cross-clamp are back.
        win.portfolio_panel.summary_label.click()
        qapp.processEvents()
        assert not win._right_region_collapsed
        assert win.right_dock.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
        assert win.active_trader.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
        assert win.portfolio_panel.minimumWidth() == RIGHT_DOCK_MIN_WIDTH
        assert win.right_dock.isVisible()
        assert win._right_dock_available()
    finally:
        win.close()


# ── D21-11-T04 / AC-D21.13.4 — strike reflects each panel's hidden state ─────

def test_D21_11_T04_strike_reflects_hidden_state(monkeypatch, qapp):
    """D21-11-T04: each button is struck iff its panel is hidden."""
    win = _boot(monkeypatch, qapp)
    try:
        at_btn = win.active_trader.header_button
        pf_btn = win.portfolio_panel.summary_label
        assert not at_btn.is_struck() and not pf_btn.is_struck()

        at_btn.click()
        qapp.processEvents()
        assert at_btn.is_struck() and not at_btn.isChecked()
        assert not pf_btn.is_struck()

        at_btn.click()
        qapp.processEvents()
        assert not at_btn.is_struck()

        pf_btn.click()
        qapp.processEvents()
        assert pf_btn.is_struck() and not pf_btn.isChecked()
        assert not at_btn.is_struck()

        pf_btn.click()
        qapp.processEvents()
        assert not pf_btn.is_struck()
    finally:
        win.close()


# ── D21-11-T05 / AC-D21.13.1 — DOM toggle whole-region; collapsed = hidden ───

def test_D21_11_T05_dom_toggle_and_collapsed_crossclamp(monkeypatch, qapp):
    """D21-11-T05: DOM toggle keeps per-panel state; collapsed region is hidden."""
    win = _boot(monkeypatch, qapp)
    try:
        win.active_trader.header_button.click()
        win.portfolio_panel.summary_label.click()
        qapp.processEvents()
        assert win.active_trader.is_collapsed()
        assert win.portfolio_panel.is_collapsed()
        assert win._right_region_collapsed

        # _on_dom_toggled stays the whole-region toggle.
        win._on_dom_toggled(False)
        qapp.processEvents()
        assert not win.right_dock.isVisible()
        win._on_dom_toggled(True)
        qapp.processEvents()
        assert win.right_dock.isVisible()
        # It must not reset the per-panel hidden states.
        assert win.active_trader.is_collapsed()
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
        # Per-panel state still persists after the clamp cycle.
        assert win.active_trader.is_collapsed()
        assert win.portfolio_panel.is_collapsed()
    finally:
        win.close()
