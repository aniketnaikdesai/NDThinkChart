import os
import tempfile
import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from ui.watchlist_panel import (
    WatchlistPanel,
    CHART_MIN_WIDTH,
    WATCHLIST_MIN_WIDTH,
    DEFAULT_WATCHLIST_WIDTH,
    WATCHLIST_WIDTH_KEY,
    watchlist_max_width,
    clamp_watchlist_width,
    load_watchlist_width,
    save_watchlist_width,
    should_load_on_double_click,
)
import ui.dock_layout as dock_layout


# ── D13/D17: width limits & persistence, measured against the chart area ─────

def test_watchlist_max_width_delegates_to_chart_area_cap():
    # D17/B1: the cap is derived from the chart area, via the single source of
    # truth in ui.dock_layout (no duplicated formula here).
    for chart_area_w in (1400, 900, 800, 600, 100, 400, 8000):
        assert watchlist_max_width(chart_area_w) == \
            dock_layout.watchlist_max_width(chart_area_w)
    # 50% of the chart area keeps the chart's own minimum in view.
    assert watchlist_max_width(1400) == 700
    # Narrow chart area: the chart minimum (400) wins over 50%.
    assert watchlist_max_width(600) == max(WATCHLIST_MIN_WIDTH, 200)
    # Never below the watchlist minimum.
    assert watchlist_max_width(100) == WATCHLIST_MIN_WIDTH


def test_clamp_watchlist_width_chart_area():
    assert clamp_watchlist_width(5000, 1400) == dock_layout.watchlist_max_width(1400)
    assert clamp_watchlist_width(5000, 1400) == 700
    assert clamp_watchlist_width(10, 1400) == WATCHLIST_MIN_WIDTH
    assert clamp_watchlist_width(300, 1400) == 300


def test_watchlist_width_settings_roundtrip():
    path = os.path.join(tempfile.gettempdir(), "wl_width_test.ini")
    try:
        os.remove(path)
    except OSError:
        pass
    settings = QSettings(path, QSettings.Format.IniFormat)
    # No saved value → default clamped
    assert load_watchlist_width(settings, 1400) == DEFAULT_WATCHLIST_WIDTH
    # Save a value, reload it
    saved = save_watchlist_width(settings, 640, 1400)
    assert saved == 640
    settings.sync()
    settings2 = QSettings(path, QSettings.Format.IniFormat)
    assert load_watchlist_width(settings2, 1400) == 640
    # Restore under a narrower chart area clamps to the new 50% cap
    assert load_watchlist_width(settings2, 900) == 450
    # Corrupt value falls back to default
    settings2.setValue(WATCHLIST_WIDTH_KEY, "not-a-number")
    assert load_watchlist_width(settings2, 1400) == DEFAULT_WATCHLIST_WIDTH


# ── D14: double-click load semantics (decision helper) ───────────────────────

def test_should_load_on_double_click():
    assert should_load_on_double_click("SPY", "AAPL", True) == "load"
    assert should_load_on_double_click("aapl", "AAPL", True) == "noop_same"
    assert should_load_on_double_click("SPY", "aapl", False) == "noop_disconnected"
    assert should_load_on_double_click("SPY", "   ", True) == "noop_empty"
    assert should_load_on_double_click("", "AAPL", True) == "load"


# ── D14: the panel emits the row's symbol on double-click ────────────────────

def test_panel_double_click_emits_symbol(qapp):
    panel = WatchlistPanel()
    panel.table.insertRow(0)
    from PyQt6.QtWidgets import QTableWidgetItem
    for col in range(panel.table.columnCount()):
        panel.table.setItem(0, col, QTableWidgetItem("—"))
    panel.table.item(0, 0).setText("AAPL")

    fired = []
    panel.row_double_clicked.connect(lambda s: fired.append(s))
    # Directly invoke the handler (cellDoubleClicked is emitted by Qt on a real
    # double-click; calling the slot verifies the mapping logic).
    panel._on_cell_double_clicked(0, 0)
    assert fired == ["AAPL"]

    # Empty / placeholder rows do not emit
    panel.table.item(0, 0).setText("—")
    panel._on_cell_double_clicked(0, 0)
    assert fired == ["AAPL"]
    panel.close()
