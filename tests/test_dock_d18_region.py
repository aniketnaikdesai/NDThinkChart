"""T48 / D18 Phase 3 (D41 re-point) — the single right dock region.

Focused offscreen integration tests for the ``ui/main_window.py`` reshape: the
right ``RightDockWidgetArea`` region is ONE ``QDockWidget`` titled **and**
``objectName``ed ``"Portfolio"`` (D41 / S6) whose widget is the retained
``ActivePortfolioPanel`` directly — the D18 two-section stacked region is gone.

Acceptance criteria exercised here
----------------------------------
* AC-D18.3 (T48-T01): the single remaining section renders at the region's
  content width (within 1px) and never exceeds the docked region.
* T48-T02: ``findChild(QDockWidget, "Portfolio")`` resolves the single region;
  the region's retained header toggle collapses/restores it; exactly one
  right-side region dock.
* T48-T03: the retained Portfolio panel is the region's widget and its existing
  signal connections are intact.

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

from ui.active_portfolio_panel import ActivePortfolioPanel


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

def test_T48_T01_portfolio_section_fills_region(monkeypatch, qapp):
    """T48-T01 / AC-D18.3: the single section spans the region's content width."""
    win = _make_window(monkeypatch, qapp)
    try:
        win.right_dock.show()
        qapp.processEvents()

        portfolio_w = win.portfolio_panel.width()
        content_w = win.right_dock.widget().width()
        region_w = win.right_dock.width()

        # S6: the retained Portfolio panel IS the region's widget — no wrapper
        # container and no second stacked section remain, so the equal-width
        # guarantee now reads "the one section spans the region".
        assert win.right_dock.widget() is win.portfolio_panel
        # Real, non-zero docked geometry (a masked/hidden region reports 0).
        assert region_w > 0, region_w
        assert content_w > 0, content_w
        # The section occupies the region's content width (equal within the
        # mandated 1px tolerance) and never exceeds the region hosting it.
        assert abs(portfolio_w - content_w) <= 1, (portfolio_w, content_w)
        assert abs(portfolio_w - region_w) <= 1, (portfolio_w, region_w)
        assert portfolio_w <= region_w + 1, (portfolio_w, region_w)
    finally:
        win.close()


# ── T48-T02 — title lookup, toggle, exactly one right dock ───────────────────

def test_T48_T02_findchild_resolves_and_toggles(monkeypatch, qapp):
    """T48-T02: ``findChild`` resolves the single region and its toggle works."""
    win = _make_window(monkeypatch, qapp)
    try:
        region = win.findChild(QDockWidget, "Portfolio")
        assert region is not None
        assert region is win.right_dock
        assert region.objectName() == "Portfolio"

        # AR-D41-3 / AC2: the title-keyed lookup the dock-hiding helper suites
        # use (``{d.windowTitle(): d ...}``) still resolves the real region — a
        # stale key would leave those helpers silently hiding nothing.
        title_keyed = {
            d.windowTitle(): d for d in win.findChildren(QDockWidget)
        }
        assert title_keyed.get("Portfolio") is region

        # The region's one surviving toggle is the retained Portfolio header
        # button: it collapses the region to its button strip (D21.13) and
        # restores it. The region itself stays visible throughout.
        header = win.portfolio_panel.summary_label
        assert region.titleBarWidget() is header
        assert region.isVisible()
        header.click()
        qapp.processEvents()
        assert win.portfolio_panel.is_collapsed()
        assert not win.portfolio_panel.body.isVisible()
        assert region.width() <= win._right_dock_collapsed_min_width + 2
        header.click()
        qapp.processEvents()
        assert not win.portfolio_panel.is_collapsed()
        assert win.portfolio_panel.body.isVisible()
        assert region.isVisible()

        # Exactly one *region* dock lives in the right dock area (the D38
        # news digest dock also lives there but is not part of the region).
        right_area = win.dockWidgetArea(region)
        assert right_area == Qt.DockWidgetArea.RightDockWidgetArea
        right_docks = [
            d for d in win.findChildren(QDockWidget)
            if win.dockWidgetArea(d) == Qt.DockWidgetArea.RightDockWidgetArea
            and d.objectName() != "NewsDigest"
        ]
        assert len(right_docks) == 1, right_docks
    finally:
        win.close()


# ── T48-T03 — panel present, signal wiring intact ────────────────────────────

def test_T48_T03_panel_present_and_signals_wired(monkeypatch, qapp):
    """T48-T03: the retained panel is the region's widget; key signals stay wired."""
    win = _make_window(monkeypatch, qapp)
    try:
        assert isinstance(win.portfolio_panel, ActivePortfolioPanel)
        # S6: the region hosts the retained panel directly — the panel IS the
        # dock's widget (no intermediate container remains).
        container = win.right_dock.widget()
        assert isinstance(container, QWidget)
        assert container is win.portfolio_panel

        # Existing signal connections are intact (connected to MainWindow slots).
        # ``QObject.receivers(signal)`` reports the number of live receivers of a
        # signal *emitted by* that object; the sender is the panel, so measure on
        # the panel and require at least one MainWindow-slot receiver. These are
        # exactly the five Portfolio connections wired by MainWindow before the
        # reshape (no wiring changed by T48).
        for signal in (
            win.portfolio_panel.position_close_requested,
            win.portfolio_panel.group_close_requested,
            win.portfolio_panel.flatten_all_requested,
            win.portfolio_panel.position_sltp_changed,
            win.portfolio_panel.group_sltp_changed,
        ):
            assert _receiver_count(win.portfolio_panel, signal) >= 1, signal
        # The panel still exposes its summary/positions signals (present and
        # unchanged even though MainWindow consumes their effect via other slots).
        assert hasattr(win.portfolio_panel, "account_summary_changed")
        assert hasattr(win.portfolio_panel, "positions_changed")

        # Sanity: an unconnected signal on the very panel probed above reports
        # zero, proving that probe is not a vacuous pass.
        assert _receiver_count(
            win.portfolio_panel, win.portfolio_panel.positions_changed
        ) == 0
    finally:
        win.close()


def _receiver_count(obj, signal) -> int:
    """Number of live receivers of ``signal`` emitted by ``obj`` (0 if unknown).

    ``QObject.receivers`` is the only reliable public measurement in PyQt6.
    Returns -1 when the API is unavailable, so the caller's ``>= 1`` assertion
    fails loudly rather than passing vacuously.
    """
    try:
        return int(obj.receivers(signal))
    except Exception:
        return -1
