"""T48 / D18 Phase 3 — single right dock region (Active Trader + Portfolio).

Focused offscreen integration tests for the ``ui/main_window.py`` reshape:
the two separate ``RightDockWidgetArea`` docks (Active Trader / Portfolio) are
replaced by one ``QDockWidget`` ('Active Trader', stable ``objectName``) whose
widget is a vertical container stacking ``ActiveTraderPanel`` over
``ActivePortfolioPanel``.

Acceptance criteria exercised here
----------------------------------
* AC-D18.3 (T48-T01): the two stacked sections render at equal width (within
  1px) and neither exceeds the region content width.
* T48-T02: ``findChild(QDockWidget, "Active Trader")`` resolves the single
  region; ``_on_dom_toggled`` flips its visibility; exactly one right-side dock.
* T48-T03: both panels are present inside the single region and their existing
  signal connections are intact.
* T48-T04: the updated right-dock lookup tests resolve the single region.

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
from ui.active_trader_panel import ActiveTraderPanel


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


# ── T48-T01 / AC-D18.3 — equal-width stacked sections ────────────────────────

def test_T48_T01_sections_equal_width_within_region(monkeypatch, qapp):
    """T48-T01 / AC-D18.3: ladder and portfolio share the region width."""
    win = _make_window(monkeypatch, qapp)
    try:
        win.right_dock.show()
        qapp.processEvents()

        trader_w = win.active_trader.width()
        portfolio_w = win.portfolio_panel.width()
        content_w = win.right_dock_container.width()

        # The two stacked sections are equal within the mandated 1px tolerance.
        assert abs(trader_w - portfolio_w) <= 1, (trader_w, portfolio_w)
        # Neither exceeds the region's content width.
        assert trader_w <= content_w + 1, (trader_w, content_w)
        assert portfolio_w <= content_w + 1, (portfolio_w, content_w)
        # The sections occupy the full content width (equal by construction).
        assert abs(trader_w - content_w) <= 1, (trader_w, content_w)
    finally:
        win.close()


# ── T48-T02 — title lookup, toggle, exactly one right dock ───────────────────

def test_T48_T02_findchild_resolves_and_toggles(monkeypatch, qapp):
    """T48-T02: ``findChild`` resolves the single region and toggling works."""
    win = _make_window(monkeypatch, qapp)
    try:
        region = win.findChild(QDockWidget, "Active Trader")
        assert region is not None
        assert region is win.right_dock
        assert region.objectName() == "Active Trader"

        # _on_dom_toggled still flips the single region's visibility.
        win._on_dom_toggled(False)
        qapp.processEvents()
        assert not region.isVisible()
        win._on_dom_toggled(True)
        qapp.processEvents()
        assert region.isVisible()

        # Exactly one dock lives in the right dock area.
        right_area = win.dockWidgetArea(region)
        assert right_area == Qt.DockWidgetArea.RightDockWidgetArea
        right_docks = [
            d for d in win.findChildren(QDockWidget)
            if win.dockWidgetArea(d) == Qt.DockWidgetArea.RightDockWidgetArea
        ]
        assert len(right_docks) == 1, right_docks
    finally:
        win.close()


# ── T48-T03 — panels present, signal wiring intact ───────────────────────────

def test_T48_T03_panels_present_and_signals_wired(monkeypatch, qapp):
    """T48-T03: both panels live inside the region; key signals stay connected."""
    win = _make_window(monkeypatch, qapp)
    try:
        assert isinstance(win.active_trader, ActiveTraderPanel)
        assert isinstance(win.portfolio_panel, ActivePortfolioPanel)
        # Both panels are descendants of the single region's container.
        container = win.right_dock.widget()
        assert isinstance(container, QWidget)
        assert container.isAncestorOf(win.active_trader)
        assert container.isAncestorOf(win.portfolio_panel)

        # Existing signal connections are intact (connected to MainWindow slots).
        # ``QObject.receivers(signal)`` reports the number of live receivers of a
        # signal *emitted by* that object; the sender is the panel, so measure on
        # the panel and require at least one MainWindow-slot receiver. These are
        # exactly the five portfolio + one active-trader connections wired by
        # MainWindow before the reshape (no wiring changed by T48).
        for signal in (
            win.portfolio_panel.position_close_requested,
            win.portfolio_panel.group_close_requested,
            win.portfolio_panel.flatten_all_requested,
            win.portfolio_panel.position_sltp_changed,
            win.portfolio_panel.group_sltp_changed,
        ):
            assert _receiver_count(win.portfolio_panel, signal) >= 1, signal
        assert _receiver_count(
            win.active_trader, win.active_trader.order_place_requested
        ) >= 1
        # The panels still expose their summary/positions signals (present and
        # unchanged even though MainWindow consumes their effect via other slots).
        assert hasattr(win.portfolio_panel, "account_summary_changed")
        assert hasattr(win.portfolio_panel, "positions_changed")

        # Sanity: an unconnected signal reports zero, proving the probe above is
        # not a vacuous pass.
        assert _receiver_count(
            win.right_dock_container, win.right_dock_container.destroyed
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
