"""D21-09 / D21.5 — configurable watchlist columns (add/remove/rearrange).

Covers AC-D21.5.1..4:
  * a right-click header popup offers add/remove/rearrange
  * the addable set is exactly the existing 7 fields
  * Symbol can never be removed
  * reorder/remove updates immediately with field-identity binding (DG32),
    D14 double-click still resolves the Symbol row, and the layout is
    persisted to QSettings ``watchlist/columns`` with a sanitised restore.
"""

import os

import pytest
from PyQt6.QtCore import QEvent, QPoint, QPointF, QSettings, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractButton,
    QDockWidget,
    QLabel,
    QMenu,
    QWidget,
)

from ui.dock_layout import WATCHLIST_COLLAPSED_WIDTH
from ui.visual_conventions import DiagonalStrikeButton
from ui.watchlist_panel import (
    ALL_FIELDS,
    CHART_MIN_WIDTH,
    COLUMN_DEFS,
    DEFAULT_FIELDS,
    HEADERS,
    SYMBOL_FIELD,
    TICK_ASK,
    TICK_BID,
    TICK_CLOSE,
    TICK_LAST,
    WATCHLIST_COLUMNS_KEY,
    WATCHLIST_MIN_WIDTH,
    WatchlistPanel,
    load_watchlist_columns,
    sanitise_watchlist_columns,
    save_watchlist_columns,
    watchlist_max_width,
)


class FakeMdManager:
    """Minimal MarketDataManager double: hands out unique reqIds."""

    def __init__(self):
        self._next = 1
        self.cancelled = []

    def req_mkt_data(self, contract):
        req_id = self._next
        self._next += 1
        return req_id

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


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
    settings = _isolated_settings(tmp_path / "watchlist_d21.ini")
    p = WatchlistPanel(settings=settings)
    p.set_market_data_manager(FakeMdManager())
    yield p
    p.close()


def _cell_text(panel, row, key):
    col = panel._active_fields.index(key)
    return panel.table.item(row, col).text()


# ── D21-09-T01 / AC-D21.5.1 — header popup offers add/remove/rearrange ────────

def test_D21_09_T01_header_menu_offers_add_remove_rearrange(panel):
    # The header is wired for a custom context menu (right-click).
    assert panel.table.horizontalHeader().contextMenuPolicy() == \
        Qt.ContextMenuPolicy.CustomContextMenu

    # Invoke the context-menu handler (show=False: build the popup, no exec).
    menu = panel._on_header_context_menu(QPoint(5, 5), show=False)
    assert isinstance(menu, QMenu)

    # Add/remove affordances: one checkable action per existing field.
    checkable = [a for a in menu.actions() if a.isCheckable()]
    assert [a.text() for a in checkable] == HEADERS
    assert len(checkable) == 7

    # Symbol is offered but cannot be removed.
    symbol_action = next(a for a in checkable if a.text() == "Symbol")
    assert symbol_action.isChecked()
    assert not symbol_action.isEnabled()

    # Rearrange affordances: a "Move" submenu with left/right entries.
    move_menus = [a.menu() for a in menu.actions() if a.menu() is not None]
    assert move_menus, "no rearrange affordance in the header popup"
    move_texts = [a.text() for a in move_menus[0].actions()]
    assert any(t.startswith("Move ") and t.endswith(" Left") for t in move_texts)
    assert any(t.startswith("Move ") and t.endswith(" Right") for t in move_texts)


# ── D21-09-T02 / AC-D21.5.2 — addable set == existing 7; add re-shows ─────────

def test_D21_09_T02_addable_set_and_readd(panel):
    # Addable set is exactly the existing 7 fields; no new data field exists.
    assert len(COLUMN_DEFS) == 7
    assert set(COLUMN_DEFS.keys()) == {
        "symbol", "last", "bid", "ask", "chg", "chgpct", "vol",
    }
    assert [COLUMN_DEFS[k]["header"] for k in ALL_FIELDS] == HEADERS
    assert panel.table.columnCount() == 7

    # Remove a column...
    panel._on_field_toggled("vol", False)
    assert "vol" not in panel._active_fields
    assert panel.table.columnCount() == 6
    assert "Vol" not in [panel.table.horizontalHeaderItem(c).text()
                         for c in range(panel.table.columnCount())]

    # ...then re-add it: "add" == re-showing a previously removed column.
    panel._on_field_toggled("vol", True)
    assert "vol" in panel._active_fields
    assert panel.table.columnCount() == 7
    assert panel.table.horizontalHeaderItem(
        panel._active_fields.index("vol")).text() == "Vol"

    # Every active key is one of the known fields — nothing new introduced.
    assert set(panel._active_fields) <= set(COLUMN_DEFS.keys())


# ── D21-09-T03 / AC-D21.5.3 — Symbol removal blocked; Symbol always remains ───

def test_D21_09_T03_symbol_cannot_be_removed(panel):
    # Attempt to remove Symbol: blocked, still present.
    panel._on_field_toggled(SYMBOL_FIELD, False)
    assert SYMBOL_FIELD in panel._active_fields
    assert panel.table.columnCount() == 7

    # The menu's Symbol action is checkable but disabled (unremovable).
    menu = panel._on_header_context_menu(QPoint(0, 0), show=False)
    symbol_action = next(a for a in menu.actions()
                         if a.isCheckable() and a.text() == "Symbol")
    assert symbol_action.isChecked()
    assert not symbol_action.isEnabled()

    # All other columns can be removed, leaving only Symbol.
    for key in list(ALL_FIELDS):
        if key != SYMBOL_FIELD:
            panel._on_field_toggled(key, False)
    assert panel._active_fields == [SYMBOL_FIELD]
    assert panel.table.columnCount() == 1
    assert panel.table.horizontalHeaderItem(0).text() == "Symbol"


# ── D21-09-T04 / AC-D21.5.4 — field binding after reorder + D14 still works ───

def test_D21_09_T04_field_identity_binding_and_d14_after_reorder(panel):
    panel.add_symbol("AAPL", object())
    req_id = next(iter(panel._req_to_row))

    # Remove a column and reorder: [symbol,last,bid,...] -> [last,symbol,ask,...]
    panel._on_field_toggled("bid", False)
    panel._move_field("last", -1)
    assert panel._active_fields.index("last") == 0
    assert panel._active_fields.index("symbol") == 1
    assert "bid" not in panel._active_fields

    # Live ticks must land in the correct *field* cell, not a fixed index.
    panel.on_tick_price(req_id, TICK_CLOSE, 100.0)
    panel.on_tick_price(req_id, TICK_LAST, 105.0)   # +5.00 / +5.00%
    panel.on_tick_price(req_id, TICK_BID, 104.5)    # removed -> not shown
    panel.on_tick_price(req_id, TICK_ASK, 105.5)
    panel.on_tick_size(req_id, 8, 12345)

    assert _cell_text(panel, 0, "symbol") == "AAPL"
    assert _cell_text(panel, 0, "last") == "105.00"
    assert _cell_text(panel, 0, "ask") == "105.50"
    assert _cell_text(panel, 0, "chg") == "+5.00"
    assert _cell_text(panel, 0, "chgpct") == "+5.00%"
    assert _cell_text(panel, 0, "vol") == "12,345"

    # Field-identity proof: the reordered layout put Symbol in column 1, and
    # the Symbol cell there still holds the symbol (no index corruption).
    assert panel.table.item(0, 1).text() == "AAPL"
    assert panel.table.item(0, 0).text() == "105.00"

    # D14 still resolves the Symbol row after a reorder (double-click col 0,
    # which is now "Last", must still emit the row's symbol).
    fired = []
    panel.row_double_clicked.connect(lambda s: fired.append(s))
    panel._on_cell_double_clicked(0, 0)
    assert fired == ["AAPL"]


# ── D21-09-T05 / AC-D21.5.4 — persistence + sanitised restore ─────────────────

def test_D21_09_T05_layout_persists_and_restores(tmp_path, qapp):
    path = tmp_path / "watchlist_persist.ini"
    settings = _isolated_settings(path)
    panel = WatchlistPanel(settings=settings)
    try:
        # Change the layout: remove Bid, move Vol to the front.
        panel._on_field_toggled("bid", False)
        while panel._active_fields.index("vol") > 0:
            panel._move_field("vol", -1)
        expected = list(panel._active_fields)
        assert expected[0] == "vol"
        assert "bid" not in expected
        settings.sync()

        # Stored form is the ordered, comma-joined field keys.
        stored = QSettings(str(path), QSettings.Format.IniFormat)
        assert stored.value(WATCHLIST_COLUMNS_KEY) == ",".join(expected)

        # Simulated restart: a fresh panel restores the same ordered set.
        reloaded = QSettings(str(path), QSettings.Format.IniFormat)
        panel2 = WatchlistPanel(settings=reloaded)
        try:
            assert panel2._active_fields == expected
            assert panel2.table.columnCount() == len(expected)
            assert [panel2.table.horizontalHeaderItem(c).text()
                    for c in range(panel2.table.columnCount())] == \
                [COLUMN_DEFS[k]["header"] for k in expected]
        finally:
            panel2.close()
    finally:
        panel.close()


def test_D21_09_T05_sanitised_restore(tmp_path, qapp):
    path = tmp_path / "watchlist_sanitise.ini"

    # Unknown keys are dropped and duplicates collapsed.
    settings = _isolated_settings(path)
    settings.setValue(WATCHLIST_COLUMNS_KEY, "bogus,last,symbol,last,unknown")
    settings.sync()
    panel = WatchlistPanel(settings=QSettings(str(path), QSettings.Format.IniFormat))
    try:
        assert panel._active_fields == ["last", "symbol"]
    finally:
        panel.close()

    # Symbol is forced present when the persisted layout omits it.
    settings = _isolated_settings(path)
    settings.setValue(WATCHLIST_COLUMNS_KEY, "last,vol")
    settings.sync()
    panel = WatchlistPanel(settings=QSettings(str(path), QSettings.Format.IniFormat))
    try:
        assert panel._active_fields[0] == SYMBOL_FIELD
        assert set(panel._active_fields) == {"symbol", "last", "vol"}
    finally:
        panel.close()

    # A value with no known keys falls back to the full default layout.
    settings = _isolated_settings(path)
    settings.setValue(WATCHLIST_COLUMNS_KEY, "bogus,unknown")
    settings.sync()
    panel = WatchlistPanel(settings=QSettings(str(path), QSettings.Format.IniFormat))
    try:
        assert panel._active_fields == DEFAULT_FIELDS
    finally:
        panel.close()


def test_D21_09_sanitise_and_save_helpers(tmp_path):
    # Pure helpers: sanitise handles the stored string form and sequences.
    assert sanitise_watchlist_columns(None) == DEFAULT_FIELDS
    assert sanitise_watchlist_columns("") == DEFAULT_FIELDS
    assert sanitise_watchlist_columns("last,vol") == ["symbol", "last", "vol"]
    assert sanitise_watchlist_columns(["vol", "vol", "nope"]) == ["symbol", "vol"]

    settings = _isolated_settings(tmp_path / "watchlist_helpers.ini")
    saved = save_watchlist_columns(settings, ["vol", "last"])
    assert saved == ["symbol", "vol", "last"]
    settings.sync()
    assert load_watchlist_columns(settings) == ["symbol", "vol", "last"]


# ═════════════════════════════════════════════════════════════════════════════
# D21-10 / D21.11 — one "Watchlist" label; header becomes the hide/show toggle
# ═════════════════════════════════════════════════════════════════════════════
#
# The duplicate ``QDockWidget("Watchlist")`` title is deleted and the in-panel
# header strip (whose label is a ``DiagonalStrikeButton``) becomes the dock's
# title-bar widget via ``setTitleBarWidget``. Clicking the button collapses the
# body (the table) while the header/button — now the title bar — stays visible
# and struck (VIS-D21.1); clicking again restores it and removes the strike.
#
# ``_boot_main_window`` mirrors the D17/D18 offscreen harness: TWS connect is
# stubbed, the unrelated right region is hidden, and the toolbar stays visible
# (D19's scroll wrapper keeps it from pinning the chart area).

_RIGHT_DOCK_TITLES = ("Portfolio",)


def _boot_main_window(monkeypatch, qapp, width=1600, height=900):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.resize(width, height)
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in _RIGHT_DOCK_TITLES:
            dock.hide()
    qapp.processEvents()
    return win


def _visible_watchlist_texts(root: QWidget):
    """Visible label/button widgets whose text is exactly 'Watchlist'."""
    found = []
    for widget in root.findChildren(QWidget):
        if isinstance(widget, (QLabel, QAbstractButton)):
            text = getattr(widget, "text", lambda: "")()
            if text == "Watchlist" and widget.isVisible():
                found.append(widget)
    return found


def _send_mouse(widget, event_type, pos: QPointF, button, buttons):
    global_pos = QPointF(widget.mapToGlobal(pos.toPoint()))
    event = QMouseEvent(
        event_type, pos, global_pos, button, buttons,
        Qt.KeyboardModifier.NoModifier,
    )
    from PyQt6.QtWidgets import QApplication

    QApplication.sendEvent(widget, event)


# ── D21-10-T01 / AC-D21.11.1 — exactly one label; header is the title bar ────

def test_D21_10_T01_single_watchlist_label_and_header_is_titlebar(monkeypatch, qapp):
    """D21-10-T01: one visible 'Watchlist' label; header strip is the title bar."""
    win = _boot_main_window(monkeypatch, qapp)
    try:
        dock = win.watchlist_dock
        panel = win.watchlist_panel

        # The duplicate dock title text is gone: exactly one visible
        # "Watchlist" label remains across the dock title and the panel.
        assert "Watchlist" not in dock.windowTitle(), (
            "the duplicate QDockWidget title was not deleted"
        )
        visible = _visible_watchlist_texts(win)
        assert len(visible) == 1, (
            f"expected exactly one visible 'Watchlist' label, got {len(visible)}"
        )
        assert visible[0] is panel.header_button

        # The in-panel header strip is the dock's title-bar widget.
        assert dock.titleBarWidget() is panel.header_bar

        # The header control is a clickable toggle button (VIS-D21.1 button).
        assert isinstance(panel.header_button, DiagonalStrikeButton)
        assert panel.header_button.isCheckable()
        assert panel.header_button.isEnabled()
        # Starts visible/unstruck (checked == shown).
        assert panel.header_button.isChecked()
        assert not panel.header_button.is_struck()
    finally:
        win.close()


# ── D21-10-T02 / AC-D21.11.2 — toggle hides body, struck button stays ────────

def test_D21_10_T02_toggle_hides_body_and_keeps_struck_button(monkeypatch, qapp):
    """D21-10-T02: clicking hides the body; D44 shows the thin bar in its place."""
    win = _boot_main_window(monkeypatch, qapp)
    try:
        panel = win.watchlist_panel
        button = panel.header_button

        # Click -> collapse: body hidden and the D44 thin bar shown as the body;
        # the expanded strip (its D22.1 '+' and the D39.1 search box) and the
        # table (whose horizontalHeader() is the column-header row) are hidden.
        button.click()
        qapp.processEvents()
        assert panel.is_collapsed()
        assert not panel.body.isVisible(), "the panel body should be hidden"
        assert panel.collapsed_bar.isVisible(), "the D44 thin bar must be shown"
        assert not panel.header_bar.isVisible(), "the expanded strip must be hidden"
        assert not panel.add_button.isVisible(), "the '+' hides with the strip"
        assert not panel.table.isVisible(), "the column-header row must be hidden"
        assert button.is_struck(), "the collapsed button must be struck (VIS-D21.1)"
        assert not button.isChecked()

        # Click again -> restore: body + strip shown; the retained button returns
        # checked and unstruck (its checked/struck state tracks the body).
        button.click()
        qapp.processEvents()
        assert not panel.is_collapsed()
        assert panel.body.isVisible(), "the body should be shown again"
        assert panel.header_bar.isVisible(), "the strip returns on expand"
        assert button.isChecked(), "the retained header button returns checked"
        assert not button.is_struck(), "the strike must be removed when shown"
    finally:
        win.close()


# ── D21-10-T03 / AC-D21.11.3 — collapsed keeps button; dock drag; width model ─

def test_D21_10_T03_collapsed_button_reachable_drag_and_width_model(
    monkeypatch, qapp
):
    """D21-10-T03: collapsed shows the D44 collapsed form; dock drag; width model."""
    win = _boot_main_window(monkeypatch, qapp)
    try:
        dock = win.watchlist_dock
        panel = win.watchlist_panel
        button = panel.header_button

        # Collapse. D44 (AC-D44.4) hides the expanded affordances — the header
        # strip and the button inside it — and shows the thin collapsed bar.
        button.click()
        qapp.processEvents()
        assert panel.is_collapsed()
        assert not panel.header_bar.isVisible()
        assert panel.collapsed_bar.isVisible()

        # The dock stays movable/floatable and the collapsed thin handle is its
        # title bar, so a title-bar drag/float is still available (A78).
        features = dock.features()
        assert features & QDockWidget.DockWidgetFeature.DockWidgetMovable
        assert features & QDockWidget.DockWidgetFeature.DockWidgetFloatable
        assert dock.titleBarWidget() is panel.collapsed_handle

        # D44's collapsed bar is CLICK-TO-EXPAND, so a synthetic double-click on
        # the handle expands the panel (the expanding release fires before Qt's
        # title-bar double-click handling) rather than floating the dock. The
        # drag/float affordance is asserted structurally above — the handle IS the
        # title bar and the dock keeps both features — and the float path itself is
        # exercised for real on the EXPANDED header strip below (re-pointed, not
        # deleted).

        # The D17/D18 width model still holds while the body is hidden — but the
        # 150px EXPANDED floor is NOT applied to a collapsed dock (D44 revises
        # AC-D13.1/AC-D17.2): the collapsed dock settles at its exact thin-bar
        # width now that the collapsed handle is the title bar (P3-T05).
        for _ in range(12):
            win._apply_dock_widths(10 ** 6)
            qapp.processEvents()
        ca = win._chart_area_width()
        cap = watchlist_max_width(ca)
        assert isinstance(win._watchlist_width, int)
        assert win.watchlist_dock.width() <= cap + 1
        assert win.watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH, (
            "a collapsed dock settles at its exact thin-bar width (D44)"
        )
        assert ca >= CHART_MIN_WIDTH
        # Still collapsible/restorable after the clamp cycle.
        assert panel.is_collapsed()
        assert panel.collapsed_bar.isVisible()

        # The >= WATCHLIST_MIN_WIDTH leg belongs to the EXPANDED state (D44 moved
        # the 150px minimum there — revised, not deleted).
        panel.set_collapsed(False)
        qapp.processEvents()
        for _ in range(12):
            win._apply_dock_widths(10 ** 6)
            qapp.processEvents()
        assert not panel.is_collapsed()
        assert panel.header_bar.isVisible()
        assert button.isVisible()
        assert dock.titleBarWidget() is panel.header_bar

        # The float path itself still works: on the EXPANDED dock the header strip
        # is the title bar, and a double-click on it floats the dock (the same path
        # a title-bar drag uses). This is the drag/float leg D44 re-points rather
        # than deletes.
        before_float = dock.isFloating()
        _send_mouse(
            panel.header_bar, QEvent.Type.MouseButtonDblClick,
            QPointF(panel.header_bar.width() / 2, panel.header_bar.height() / 2),
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        )
        qapp.processEvents()
        assert dock.isFloating() != before_float, (
            "title-bar events must still reach the dock (drag/float preserved)"
        )
        dock.setFloating(False)
        qapp.processEvents()
        for _ in range(12):
            win._apply_dock_widths(10 ** 6)
            qapp.processEvents()

        cap = watchlist_max_width(win._chart_area_width())
        assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH, (
            "the EXPANDED watchlist dock must honour the 150px floor"
        )
        assert win.watchlist_dock.width() <= cap + 1
    finally:
        win.close()


# ── P3-T02 (D44) — the collapsed-aware dock-width apply path ─────────────────
#
# RESIDUE recorded for P3-T05: a collapsed dock cannot settle at its exact
# thin-bar width (WATCHLIST_COLLAPSED_WIDTH) until the header strip stops
# occupying the title-bar slot — i.e. until P3-T05 swaps in the 30x28 handle and
# the thin bar becomes the dock's content. Until then the dock is bounded by the
# strip (128px), so the tests below assert the D44 behaviour that IS observable
# at this stage: the collapsed width is PLANNED, and the 150px expanded floor is
# not applied. The exact-width assertion lands in P3-T05.


def _drive_apply(win, qapp, times: int = 12) -> None:
    """Drive the single dock-width apply entry point until it settles."""
    for _ in range(times):
        win._apply_dock_widths(10 ** 6)
        qapp.processEvents()


def test_P3_T02_T11_collapsed_width_planned_floor_not_applied(monkeypatch, qapp):
    """AC1 — the right-dock-VISIBLE branch plans the collapsed width (D44)."""
    win = _boot_main_window(monkeypatch, qapp)
    try:
        panel = win.watchlist_panel
        right = getattr(win, "right_dock", None)
        if right is not None:
            right.show()
        qapp.processEvents()
        assert win._right_dock_available()
        ca = win._chart_area_width()

        panel.set_collapsed(True)
        qapp.processEvents()
        _drive_apply(win, qapp)

        plan_left, _ = win._plan_dock_widths(ca, 10 ** 6, 10 ** 6, left_collapsed=True)
        assert plan_left == WATCHLIST_COLLAPSED_WIDTH
        assert win.watchlist_dock.width() < WATCHLIST_MIN_WIDTH, (
            "a collapsed dock must not be forced up to the 150px expanded floor"
        )
    finally:
        win.close()


def test_P3_T02_T21_collapsed_width_hidden_branch_floor_not_applied(monkeypatch, qapp):
    """AC2 — the right-dock-HIDDEN direct-clamp branch plans the collapsed width."""
    win = _boot_main_window(monkeypatch, qapp)  # this harness hides the right dock
    try:
        panel = win.watchlist_panel
        assert not win._right_dock_available()
        ca = win._chart_area_width()

        panel.set_collapsed(True)
        qapp.processEvents()
        _drive_apply(win, qapp)

        desired = win._plan_dock_widths(ca, 10 ** 6, 10 ** 6, left_collapsed=True)[0]
        assert desired == WATCHLIST_COLLAPSED_WIDTH
        assert win.watchlist_dock.width() < WATCHLIST_MIN_WIDTH
    finally:
        win.close()


def test_P3_T02_T31_tracked_width_survives_the_collapse(monkeypatch, qapp):
    """AC3 — `_watchlist_width` tracks the EXPANDED width and is never overwritten."""
    win = _boot_main_window(monkeypatch, qapp)
    try:
        panel = win.watchlist_panel
        _drive_apply(win, qapp)
        expanded = win._watchlist_width
        assert isinstance(expanded, int) and expanded >= WATCHLIST_MIN_WIDTH

        panel.set_collapsed(True)
        qapp.processEvents()
        _drive_apply(win, qapp)
        assert win._watchlist_width == expanded, (
            "_watchlist_width must not be overwritten with the collapsed width"
        )

        panel.set_collapsed(False)
        qapp.processEvents()
        _drive_apply(win, qapp)
        assert win._watchlist_width >= WATCHLIST_MIN_WIDTH
    finally:
        win.close()
