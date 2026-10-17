"""D44 — the collapsed watchlist bar, the collapsed title-bar handle, the
collapsed visual sync, the ``collapsed_changed`` signal and the constant alias.

Pre-fix these tests are red (``CollapsedWatchlistBar``, ``collapsed_bar``,
``collapsed_handle``, ``_apply_collapsed_visual`` and
``WATCHLIST_COLLAPSED_WIDTH`` do not exist); post-fix they are green.

Covers:
  * AC1 / AC-D44.1 / AC-D44.6 / A75 — the collapsed bar's form + app palette;
  * AC2 / AC-D44.1 — the rotated ``WATCHLIST`` label (a custom paintEvent);
  * AC3 / AC-D44.4 / A77 — ``header_bar`` and ``table`` hidden while collapsed;
  * AC4 / AC-D44.3 — the collapse API preserved + click-to-expand;
  * AC5 / AC-D44.6 — hover/pressed via the shared ``set_button_active``;
  * AC6 / AP-D44-5 — the constant-alias agreement with ``ui/dock_layout``;
  * AC7 / AC-D44.1 / A78 — the 30×28 collapsed title-bar handle.

All tests run offscreen (tests/conftest.py sets ``QT_QPA_PLATFORM=offscreen``
and ``DB_PATH`` before the app modules are imported — ESC-043).
"""

import os
import re

import pytest
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest

import ui.dock_layout as dock_layout
import ui.visual_conventions as visual_conventions
import ui.watchlist_panel as watchlist_panel
from ui.watchlist_panel import (
    COLLAPSED_BAR_TEXT,
    WATCHLIST_COLLAPSED_WIDTH,
    CollapsedWatchlistBar,
    WatchlistPanel,
)


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
def panel(qapp, tmp_path):
    """An offscreen panel backed by per-test settings (never the real user DB)."""
    p = WatchlistPanel(settings=_isolated_settings(tmp_path / "watchlist_d44.ini"))
    yield p
    p.close()


# ── T11 / AC1 — the collapsed bar's form + app palette ───────────────────────

def test_P3_T03_T11_collapsed_bar_form_and_palette(panel, qapp):
    panel.show()
    panel.set_collapsed(True)
    qapp.processEvents()

    bar = panel.collapsed_bar
    assert isinstance(bar, CollapsedWatchlistBar)
    assert bar.objectName() == "WatchlistCollapsedBar"
    # The panel's full-height collapsed body: visible while collapsed.
    assert bar.isVisible()
    # Fixed to the collapsed thin-bar width.
    assert bar.minimumWidth() == WATCHLIST_COLLAPSED_WIDTH
    assert bar.maximumWidth() == WATCHLIST_COLLAPSED_WIDTH

    ss = bar.styleSheet()
    assert "#141822" in ss  # background
    assert "#232938" in ss  # border
    assert "#cbd5e1" in ss  # text
    assert "white" not in ss.lower()
    assert "#ffffff" not in ss.lower()


# ── T21 / AC2 — the rotated WATCHLIST label ──────────────────────────────────

def test_P3_T03_T21_rotated_label_pixels(panel, qapp):
    panel.show()
    panel.set_collapsed(True)
    qapp.processEvents()

    bar = panel.collapsed_bar
    bar.resize(WATCHLIST_COLLAPSED_WIDTH, 320)

    img = QImage(bar.size(), QImage.Format.Format_ARGB32)
    img.fill(0)
    bar.render(img)

    target = (0xCB, 0xD5, 0xE1)  # COLLAPSED_BAR_TEXT #cbd5e1
    xs: list[int] = []
    ys: list[int] = []
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            if (abs(c.red() - target[0]) <= 60
                    and abs(c.green() - target[1]) <= 60
                    and abs(c.blue() - target[2]) <= 60):
                xs.append(x)
                ys.append(y)

    assert xs, "the paintEvent painted no text-coloured pixels"
    width = max(xs) - min(xs) + 1
    height = max(ys) - min(ys) + 1
    # Rotated 90°: the label's extent runs vertically, so height > width.
    assert height > width


# ── T31 / AC3 — header_bar + table hidden while collapsed ────────────────────

def test_P3_T03_T31_hidden_affordances(panel, qapp):
    panel.show()
    qapp.processEvents()
    assert panel.header_bar.isVisible()
    assert panel.table.isVisible()

    panel.set_collapsed(True)
    qapp.processEvents()
    assert not panel.header_bar.isVisible()
    assert not panel.table.isVisible()
    assert panel.collapsed_bar.isVisible()

    panel.set_collapsed(False)
    qapp.processEvents()
    assert panel.header_bar.isVisible()
    assert panel.table.isVisible()
    assert not panel.collapsed_bar.isVisible()


# ── T41 / AC4 — the collapse API preserved + click-to-expand ─────────────────

def test_P3_T03_T41_collapse_api_and_click_expand(panel, qapp):
    panel.show()
    qapp.processEvents()

    # Signatures/semantics unchanged.
    assert panel.is_collapsed() is False
    panel.set_collapsed(True)
    assert panel.is_collapsed() is True
    panel.set_collapsed(False)
    assert panel.is_collapsed() is False
    panel.toggle_collapsed()
    assert panel.is_collapsed() is True
    panel.toggle_collapsed()
    assert panel.is_collapsed() is False

    # Collapsing from the retained header button still works.
    panel.header_button.click()
    qapp.processEvents()
    assert panel.is_collapsed() is True
    panel.header_button.click()
    qapp.processEvents()
    assert panel.is_collapsed() is False

    # ``collapsed_changed`` fires on a real state flip (and only then).
    seen: list[bool] = []
    panel.collapsed_changed.connect(seen.append)
    panel.set_collapsed(True)
    panel.set_collapsed(False)
    assert seen == [True, False]

    # The bar's expand intent restores the panel.
    panel.set_collapsed(True)
    panel.collapsed_bar.expand_requested.emit()
    qapp.processEvents()
    assert panel.is_collapsed() is False

    # A real mouse click on the bar expands it too.
    panel.set_collapsed(True)
    qapp.processEvents()
    QTest.mouseClick(panel.collapsed_bar, Qt.MouseButton.LeftButton)
    qapp.processEvents()
    assert panel.is_collapsed() is False


# ── T51 / AC5 — hover/pressed via the shared convention ──────────────────────

def _background(css_block: str):
    match = re.search(r"background:\s*([^;]+);", css_block)
    return match.group(1).strip() if match else None


def test_P3_T03_T51_hover_pressed_via_shared_helper(panel, qapp):
    # The helper is the shared one from ui/visual_conventions (not hand-rolled).
    assert watchlist_panel.set_button_active is visual_conventions.set_button_active

    panel.show()
    panel.set_collapsed(True)
    qapp.processEvents()
    bar = panel.collapsed_bar

    assert bar.property(visual_conventions.ACTIVE_PROPERTY) in (None, False)
    visual_conventions.set_button_active(bar, True)
    assert bar.property(visual_conventions.ACTIVE_PROPERTY) is True

    ss = bar.styleSheet()
    assert '[active="true"]' in ss
    active_index = ss.index('[active="true"]')
    idle_block = ss[:active_index]
    active_block = ss[active_index:]
    # The active style differs from the idle style.
    assert _background(idle_block) != _background(active_block)

    visual_conventions.set_button_active(bar, False)
    assert bar.property(visual_conventions.ACTIVE_PROPERTY) is False

    # Press/hover drive the shared helper.
    QTest.mousePress(bar, Qt.MouseButton.LeftButton)
    assert bar.property(visual_conventions.ACTIVE_PROPERTY) is True
    QTest.mouseRelease(bar, Qt.MouseButton.LeftButton)
    assert bar.property(visual_conventions.ACTIVE_PROPERTY) is False


# ── T61 / AC6 — the constant-alias agreement ─────────────────────────────────

def test_P3_T03_T61_constant_alias_agreement():
    assert (watchlist_panel.WATCHLIST_COLLAPSED_WIDTH
            == dock_layout.WATCHLIST_COLLAPSED_WIDTH)
    assert watchlist_panel.CHART_MIN_WIDTH == dock_layout.CHART_MIN_WIDTH


# ── T71 / AC7 — the collapsed title-bar handle ───────────────────────────────

def test_P3_T03_T71_collapsed_handle_size(panel, qapp):
    handle = panel.collapsed_handle
    assert handle is not None
    assert handle.minimumWidth() == 30
    assert handle.maximumWidth() == 30
    assert handle.minimumHeight() == 28
    assert handle.maximumHeight() == 28
