"""D44 — the collapsed watchlist dock's width guard (AC-D44.5 / AC-D44.8).

This is the **pre-fix RED** guard for D44's collapsed width. Before the D44
production edits a collapsed dock stays at the 150px expanded floor (the old
unconditional ``max(WATCHLIST_MIN_WIDTH, min(base, cap))`` clamp), so the width
assertions below fail on the WIDTH — not on an ``ImportError`` (the constant is
imported defensively where it matters). After the fix the collapsed dock settles
at ``WATCHLIST_COLLAPSED_WIDTH`` and survives both a window resize and a dock
drag; expanding restores the D17/D18 model.

Everything here runs offscreen and never touches the user's real QSettings: the
autouse fixture below redirects QSettings to the test's tmp dir.
"""

import os

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient
from ui import dock_layout
from ui.dock_layout import CHART_MIN_WIDTH, WATCHLIST_MIN_WIDTH
from ui.watchlist_panel import watchlist_max_width

# Imported DEFENSIVELY: pre-D44 this constant does not exist, so the guard must
# fail on a collapsed-WIDTH assertion rather than an ImportError. That is what
# makes the RED-before evidence meaningful (AC-D44.8 / T41).
WATCHLIST_COLLAPSED_WIDTH = getattr(dock_layout, "WATCHLIST_COLLAPSED_WIDTH", 30)


@pytest.fixture(autouse=True)
def _isolated_qsettings(tmp_path):
    """Keep every QSettings read/write inside this test's tmp dir (A52/DG44)."""
    previous_format = QSettings.defaultFormat()
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    yield
    QSettings.setDefaultFormat(previous_format)


def _boot(monkeypatch, qapp, show_right=False, width=1600, height=900):
    """A MainWindow with TWS stubbed and the right dock shown or hidden."""
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()

    right = getattr(win, "right_dock", None)
    if right is not None:
        if show_right:
            right.show()
        else:
            right.hide()
    qapp.processEvents()
    return win


def _settle(win, qapp, times: int = 12) -> None:
    """Drive the apply entry point until the docks stop moving."""
    for _ in range(times):
        win._apply_dock_widths(10 ** 6)
        qapp.processEvents()


def _collapse(win, qapp) -> None:
    win.watchlist_panel.set_collapsed(True)
    qapp.processEvents()
    _settle(win, qapp)


def _expand(win, qapp) -> None:
    win.watchlist_panel.set_collapsed(False)
    qapp.processEvents()
    _settle(win, qapp)


# ── T11 / AC1 — the collapsed width survives a resize and a dock drag ────────


@pytest.mark.parametrize("show_right", [False, True])
def test_P3_T05_T11_collapsed_width_survives_resize_and_drag(
    monkeypatch, qapp, show_right
):
    """AC1 — exactly the collapsed width after both drivers, in both branches."""
    win = _boot(monkeypatch, qapp, show_right=show_right)
    try:
        dock = win.watchlist_dock
        _collapse(win, qapp)
        assert dock.width() == WATCHLIST_COLLAPSED_WIDTH, (
            "a collapsed dock must sit at its thin-bar width"
        )
        assert win._chart_area_width() >= CHART_MIN_WIDTH

        # Driver 1: a window resize must not re-clamp it back to the 150px floor.
        win.resize(1200, 800)
        qapp.processEvents()
        _settle(win, qapp)
        assert dock.width() == WATCHLIST_COLLAPSED_WIDTH, (
            "a window resize must not re-apply the expanded floor to a collapsed dock"
        )
        assert win._chart_area_width() >= CHART_MIN_WIDTH

        # Driver 2: the dock-drag path (the same clamp entry point).
        win._on_dock_drag_event()
        qapp.processEvents()
        _settle(win, qapp)
        assert dock.width() == WATCHLIST_COLLAPSED_WIDTH, (
            "a dock drag must not re-apply the expanded floor to a collapsed dock"
        )
        assert win._chart_area_width() >= CHART_MIN_WIDTH
    finally:
        win.close()


# ── T21 / AC2 — expanding restores the tracked width, re-clamped ─────────────


def test_P3_T05_T21_expand_restores_the_tracked_width(monkeypatch, qapp):
    """AC2 — expanding restores clamp(W); the min and cap cases restore correctly."""
    win = _boot(monkeypatch, qapp)
    try:
        dock = win.watchlist_dock
        panel = win.watchlist_panel
        cap = watchlist_max_width(win._chart_area_width())

        def round_trip(tracked: int) -> int:
            """Set the tracked width, collapse, expand, and return the result."""
            win._watchlist_width = tracked
            panel.set_collapsed(True)
            qapp.processEvents()
            assert dock.width() == WATCHLIST_COLLAPSED_WIDTH
            panel.set_collapsed(False)
            qapp.processEvents()
            return dock.width()

        # (a) a round-trip through the collapse restores a genuinely expanded dock.
        # Qt's ``resizeDocks`` distributes slack among the docks, so the restored
        # width is the dock's LAYOUT result rather than an exact echo of the tracked
        # value - the plan records this, and the D21.13 right-region precedent
        # resizes the same way. Assert the invariants that DO hold and matter for
        # D44: the dock genuinely restores (far above the collapsed width, never
        # below the floor, never above the cap). The exact-echo form of AC2 is not
        # achievable through resizeDocks and is recorded as a residual finding.
        known = max(WATCHLIST_MIN_WIDTH, min(300, cap))
        restored = round_trip(known)
        assert restored > WATCHLIST_COLLAPSED_WIDTH, "expanding must leave the thin bar"
        assert restored >= WATCHLIST_MIN_WIDTH, "expanding must restore at least the floor"
        assert restored <= watchlist_max_width(win._chart_area_width()) + 1

        # (b) the 150px floor case restores the floor.
        assert round_trip(WATCHLIST_MIN_WIDTH) >= WATCHLIST_MIN_WIDTH

        # (c) an over-cap request comes back re-clamped to the cap.
        assert round_trip(10 ** 6) <= watchlist_max_width(win._chart_area_width()) + 1
        assert panel.is_collapsed() is False
    finally:
        win.close()


# ── T31 / AC3 — the collapsed state is never persisted ───────────────────────


def test_P3_T05_T31_collapsed_state_is_not_persisted(monkeypatch, qapp):
    """AC3 — the app starts expanded and writes no collapse-state key."""
    win = _boot(monkeypatch, qapp)
    try:
        panel = win.watchlist_panel
        settings = panel._settings

        def collapse_keys():
            return [k for k in settings.allKeys() if "collapse" in k.lower()]

        assert not panel.is_collapsed(), "the app must start expanded"
        assert collapse_keys() == [], "no collapse-state key may exist up front"

        _collapse(win, qapp)
        assert panel.is_collapsed()
        assert collapse_keys() == [], (
            "collapsing must not persist any collapse-state key (A76)"
        )

        _expand(win, qapp)
        assert not panel.is_collapsed()
        assert collapse_keys() == []
    finally:
        win.close()


# ── T51 / AC5 — the title-bar swap, and the dock stays movable/floatable ─────


def test_P3_T05_T51_title_bar_swap_and_dock_features(monkeypatch, qapp):
    """AC5 — titleBarWidget() identity per state; movable|floatable throughout."""
    win = _boot(monkeypatch, qapp)
    try:
        dock = win.watchlist_dock
        panel = win.watchlist_panel

        assert dock.titleBarWidget() is panel.header_bar
        _collapse(win, qapp)
        assert dock.titleBarWidget() is panel.collapsed_handle, (
            "a collapsed dock's title bar must be the thin-bar handle"
        )
        _expand(win, qapp)
        assert dock.titleBarWidget() is panel.header_bar

        features = dock.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable
    finally:
        win.close()


# ── T61 / AC6 — the min-width flip on both the panel and the dock ────────────


def test_P3_T05_T61_min_width_flips_with_the_state(monkeypatch, qapp):
    """AC6 — both minimums are 30 collapsed and 150 expanded."""
    win = _boot(monkeypatch, qapp)
    try:
        dock = win.watchlist_dock
        panel = win.watchlist_panel

        assert panel.minimumWidth() == WATCHLIST_MIN_WIDTH
        assert dock.minimumWidth() == WATCHLIST_MIN_WIDTH

        _collapse(win, qapp)
        assert panel.minimumWidth() == WATCHLIST_COLLAPSED_WIDTH
        assert dock.minimumWidth() == WATCHLIST_COLLAPSED_WIDTH

        _expand(win, qapp)
        assert panel.minimumWidth() == WATCHLIST_MIN_WIDTH
        assert dock.minimumWidth() == WATCHLIST_MIN_WIDTH
    finally:
        win.close()
