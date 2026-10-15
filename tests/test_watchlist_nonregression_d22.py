"""D22-09 — cross-cutting non-regression tests (AC-D22.9.1 / AC-D22.8).

Phase 5 of the Batch-16 (D22) add/remove-symbol work. These tests boot a real
offscreen ``MainWindow`` that carries the new D22 affordances and prove the
prior D1-D21 watchlist / dock behaviours are unchanged alongside them:

  * D21.5  — the right-click column-header popup still opens with the 7
             checkable fields and a non-removable Symbol;
  * D21.11 — the in-panel "Watchlist" toggle still hides/shows the body and the
             collapsed button stays visible + struck (VIS-D21.1);
  * D14    — a double-click still emits the row's symbol, resolved by field key;
  * D21.13 — the retained Portfolio header (the single right dock's title-bar
             toggle) still collapses + restores its panel and stays struck iff
             the panel is hidden.

Harness note: mirrors the D21 / D22-07 offscreen harness — ``IBApiClient.connect``
is monkeypatched to a no-op, the DB is a throwaway SQLite file, and the
non-injectable ``watchlist/configured`` QSettings sentinel is swapped for a
per-test ini file. No test connects to live TWS or transmits an order (Q9).

All tests run offscreen (tests/conftest.py sets QT_QPA_PLATFORM=offscreen).
"""

import os

import pytest
from PyQt6.QtCore import QPoint, QSettings
from PyQt6.QtWidgets import QDockWidget

import config.paths as paths
import ui.main_window as main_window
from ui.visual_conventions import DiagonalStrikeButton
from ui.watchlist_panel import HEADERS, SYMBOL_FIELD


def _isolated_settings(path) -> QSettings:
    try:
        os.remove(path)
    except OSError:
        pass
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    settings.clear()
    settings.sync()
    return settings


@pytest.fixture
def window(monkeypatch, qapp, tmp_path):
    """A shown MainWindow with an isolated DB + QSettings; never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    # Throwaway DB: an absolute filename makes get_db_path() return it verbatim.
    db_file = tmp_path / "watchlist_nonregression_d22.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))
    from data.db import DB

    fresh = DB()
    monkeypatch.setattr(main_window, "db", fresh)

    win = None
    try:
        win = main_window.MainWindow()
        # Swap in per-test settings BEFORE anything can write the real sentinel.
        win._settings = _isolated_settings(tmp_path / "watchlist_nonregression_d22.ini")
        win.resize(1600, 900)
        win.show()
        qapp.processEvents()
        yield win
    finally:
        if win is not None:
            win.close()
        fresh.conn.close()


# ── D22-09-T01 / AC-D22.9.1 — watchlist non-regression + D22 affordances ─────

def test_D22_09_T01_watchlist_nonregression(window, qapp):
    panel = window.watchlist_panel

    # ── The new D22 affordances are present alongside the D21 ones. ──────────
    assert panel.add_button is not None
    assert panel.add_button.text() == "+"
    assert hasattr(panel, "add_action")
    assert hasattr(panel, "symbol_add_requested")
    assert hasattr(panel, "symbol_remove_requested")

    # The strip's own "Add symbol…" menu is a distinct popup from the D21.5
    # column popup; the D21.5 column popup stays on the table's header.
    strip_menu = panel._on_strip_context_menu(QPoint(4, 4), show=False)
    assert "Add symbol…" in [a.text() for a in strip_menu.actions()]

    # ── D21.5 — column-header popup: 7 checkable fields, Symbol unremovable. ─
    col_menu = panel._on_header_context_menu(QPoint(5, 5), show=False)
    assert col_menu is not strip_menu
    checkable = [a for a in col_menu.actions() if a.isCheckable()]
    assert [a.text() for a in checkable] == HEADERS
    assert len(checkable) == 7
    symbol_action = next(a for a in checkable if a.text() == "Symbol")
    assert symbol_action.isChecked()
    assert not symbol_action.isEnabled()

    # ── D21.11 — the "Watchlist" toggle still hides/shows the body. ──────────
    button = panel.header_button
    assert isinstance(button, DiagonalStrikeButton)
    assert button.isChecked()
    assert not button.is_struck()

    button.click()
    qapp.processEvents()
    assert panel.is_collapsed()
    assert not panel.body.isVisible()
    assert panel.header_bar.isVisible()
    assert button.isVisible()
    assert button.is_struck()
    assert not button.isChecked()

    button.click()
    qapp.processEvents()
    assert not panel.is_collapsed()
    assert panel.body.isVisible()
    assert not button.is_struck()
    assert button.isChecked()

    # ── D14 — double-click still emits the row symbol. ──────────────────────
    panel.add_symbol("AAPL", object())
    qapp.processEvents()
    fired: list[str] = []
    panel.row_double_clicked.connect(lambda s: fired.append(s))
    # Pass a non-Symbol column index: the handler must resolve by field key.
    panel._on_cell_double_clicked(0, 0)
    assert fired == ["AAPL"]


# ── D22-09-T01 / AC-D22.9.1 — D21.13 right-dock toggles still work ───────────

def test_D22_09_T01_right_dock_toggles_nonregression(window, qapp):
    # D41 / S6: the right region is ONE Portfolio-only dock. The title-keyed
    # lookup follows the rename — a stale "Active Trader" handle would silently
    # stop addressing the dock (AR-D41-3), so the new title is asserted and the
    # old one proven absent.
    dock = window.findChild(QDockWidget, "Portfolio")
    assert dock is not None
    assert dock is window.right_dock
    assert dock.windowTitle() == "Portfolio"
    assert window.findChild(QDockWidget, "Active Trader") is None

    # The retained Portfolio header IS the dock's title-bar toggle button.
    btn = window.portfolio_panel.summary_label
    assert dock.titleBarWidget() is btn
    assert isinstance(btn, DiagonalStrikeButton)
    assert btn.text() == "Account Summary"
    assert btn.isCheckable()
    assert btn.isChecked() and not btn.is_struck()

    # The geometry measured below is a real docked window, not a detached widget.
    assert window.portfolio_panel.isVisible()
    assert btn.isVisible()
    assert dock.width() > 0

    # Collapse + restore the retained Portfolio panel; strike tracks hidden state.
    btn.click()
    qapp.processEvents()
    assert window.portfolio_panel.is_collapsed()
    assert not window.portfolio_panel.body.isVisible()
    assert btn.is_struck() and not btn.isChecked()

    btn.click()
    qapp.processEvents()
    assert not window.portfolio_panel.is_collapsed()
    assert window.portfolio_panel.body.isVisible()
    assert not btn.is_struck()
    assert btn.isChecked()
