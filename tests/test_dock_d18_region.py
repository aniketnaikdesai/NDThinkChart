"""T48 / D18 Phase 3 (D65 re-point) — the single right dock region.

Focused offscreen integration tests for the ``ui/main_window.py`` reshape: the
right ``RightDockWidgetArea`` region is ONE ``QDockWidget`` titled **and**
``objectName``ed ``"Option Spreads"`` (D65 / S-P23-1) whose widget is the
``OptionSpreadsPanel`` directly — the D18 two-section stacked region is gone.

Acceptance criteria exercised here
---------------------------------
* AC-D18.3 (T48-T01): the single remaining section renders at the region's
  content width (within 1px) and never exceeds the docked region.
* T48-T02: ``findChild(QDockWidget, "Option Spreads")`` resolves the single
  region; the objectName-keyed lookup the dock-hiding helper suites use still
  resolves it; the region's retained header toggle collapses/restores it;
  exactly one right-side region dock.
* T48-T03: the Option Spreads panel is the region's widget (the order signals
  are gone, D45).

Geometry note
-------------
D19 Phase 2: the offscreen toolbar's ``minimumSizeHint`` (~1716px) no longer
pins the layout — it is wrapped in a horizontal ``QScrollArea``
(``ToolbarScroll``) — so the harness runs with the toolbar **visible** and no
masking, and the dock geometry settles to the window size.
"""

from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QWidget

from ui.option_spreads_panel import OptionSpreadsPanel


def _make_window(monkeypatch, qapp, width=1600, height=900):
    """Build a shown ``MainWindow`` that never touches TWS.

    D19 Phase 2: the toolbar is wrapped in a horizontal ``QScrollArea``
    (``ToolbarScroll``) so its ~1716px natural width no longer pins the central
    widget. The harness therefore exercises a **toolbar-visible** window with no
    masking, and the dock geometry settles to the requested window size.
    """
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()
    qapp.processEvents()
    return win


# ── T57-T01 / AC-D19.6 — toolbar visible, no masking ─────────────────────────

def test_T57_T01_toolbar_visible_and_no_masking(monkeypatch, qapp):
    """T57-T01 / AC-D19.6: harness shows the toolbar; no hide() masking remains."""
    win = _make_window(monkeypatch, qapp)
    try:
        toolbar = win.findChild(QWidget, "MainToolbar")
        assert toolbar is not None, "MainToolbar widget not found"
        assert toolbar.isVisible(), "toolbar is not visible in the harness window"
    finally:
        win.close()

    # The module source must contain no toolbar-hiding masking and no stale
    # central-layout itemAt(0) toolbar lookup (which now resolves to the scroll
    # wrapper). Needles are built at runtime so this assertion cannot match itself.
    source = Path(__file__).read_text(encoding="utf-8")
    assert ("toolbar" + ".hide()") not in source
    assert ("itemAt(0).widget" + "()") not in source


# ── T48-T01 / AC-D18.3 — the single section fills the region ─────────────────

def test_T48_T01_spread_section_fills_region(monkeypatch, qapp):
    """T48-T01 / AC-D18.3: the single section spans the region's content width."""
    win = _make_window(monkeypatch, qapp)
    try:
        win.right_dock.show()
        qapp.processEvents()

        spread_w = win.option_spreads_panel.width()
        content_w = win.right_dock.widget().width()
        region_w = win.right_dock.width()

        # S-P23-1: the Option Spreads panel IS the region's widget — no wrapper
        # container and no second stacked section remain, so the equal-width
        # guarantee now reads "the one section spans the region".
        assert win.right_dock.widget() is win.option_spreads_panel
        # Real, non-zero docked geometry (a masked/hidden region reports 0).
        assert region_w > 0, region_w
        assert content_w > 0, content_w
        # The section occupies the region's content width (equal within the
        # mandated 1px tolerance) and never exceeds the region hosting it.
        assert abs(spread_w - content_w) <= 1, (spread_w, content_w)
        assert abs(spread_w - region_w) <= 1, (spread_w, region_w)
        assert spread_w <= region_w + 1, (spread_w, region_w)
    finally:
        win.close()


# ── T48-T02 — lookup, toggle, exactly one right dock ─────────────────────────

def test_T48_T02_findchild_resolves_and_toggles(monkeypatch, qapp):
    """T48-T02: ``findChild`` resolves the single region and its toggle works."""
    win = _make_window(monkeypatch, qapp)
    try:
        region = win.findChild(QDockWidget, "Option Spreads")
        assert region is not None
        assert region is win.right_dock
        assert region.objectName() == "Option Spreads"

        # AR-D41-3 / AC2: the objectName-keyed lookup the dock-hiding helper
        # suites use (``{d.objectName(): d ...}``) resolves the real region — a
        # stale key would leave those helpers silently hiding nothing.
        name_keyed = {
            d.objectName(): d for d in win.findChildren(QDockWidget)
        }
        assert name_keyed.get("Option Spreads") is region

        # The region's one surviving toggle is the retained Option Spreads
        # header button: it collapses the region to its button strip (D21.13)
        # and restores it. The region itself stays visible throughout.
        header = win.option_spreads_panel.header_button
        assert region.titleBarWidget() is header
        assert region.isVisible()
        header.click()
        qapp.processEvents()
        assert win.option_spreads_panel.is_collapsed()
        assert not win.option_spreads_panel.body.isVisible()
        assert region.width() <= win._right_dock_collapsed_min_width + 2
        header.click()
        qapp.processEvents()
        assert not win.option_spreads_panel.is_collapsed()
        assert win.option_spreads_panel.body.isVisible()
        assert region.isVisible()

        # Exactly one *region* dock lives in the right dock area.
        right_area = win.dockWidgetArea(region)
        assert right_area == Qt.DockWidgetArea.RightDockWidgetArea
        right_docks = [
            d for d in win.findChildren(QDockWidget)
            if win.dockWidgetArea(d) == Qt.DockWidgetArea.RightDockWidgetArea
        ]
        assert len(right_docks) == 1, right_docks
    finally:
        win.close()


# ── T48-T03 — panel present, collapse round trip, one right dock ─────────────

def test_T48_T03_panel_present_and_collapse_round_trip(monkeypatch, qapp):
    """T48-T03: the Option Spreads panel is the region's widget."""
    win = _make_window(monkeypatch, qapp)
    try:
        assert isinstance(win.option_spreads_panel, OptionSpreadsPanel)
        # S-P23-1: the region hosts the panel directly — the panel IS the
        # dock's widget (no intermediate container remains).
        container = win.right_dock.widget()
        assert isinstance(container, QWidget)
        assert container is win.option_spreads_panel

        # A collapse/expand round trip through the panel's own header leaves
        # exactly one right-area dock (nothing is spawned or orphaned by the
        # title-bar swap).
        win.option_spreads_panel.header_button.click()
        qapp.processEvents()
        win.option_spreads_panel.header_button.click()
        qapp.processEvents()
        assert not win.option_spreads_panel.is_collapsed()
        right_docks = [
            d for d in win.findChildren(QDockWidget)
            if win.dockWidgetArea(d) == Qt.DockWidgetArea.RightDockWidgetArea
        ]
        assert len(right_docks) == 1, right_docks
        assert right_docks[0] is win.right_dock
    finally:
        win.close()
