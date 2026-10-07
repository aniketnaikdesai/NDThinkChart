"""D22-04 — watchlist add affordances, enable state, signals and pure helpers.

Pre-fix these tests are red (the '+' button, the strip "Add symbol…" menu, the
enable toggle, the two intent signals and the pure helpers do not exist);
post-fix they are green.

Covers the add side of D22 (add/remove):
  * AC-D22.4.1 — '+' on the header strip adjacent to the D21.11 toggle, a strip
    "Add symbol…" context menu, while the D21.5 column popup stays on the table's
    horizontal header;
  * AC-D22.4.2 — default-disabled '+' / action toggled by set_add_enabled;
  * AC-D22.4.3 — normalise_symbol / symbol_in_list (pure);
  * AC-D22.4.4 — the modal AddSymbolDialog is shown; accepted emits, rejected not;
  * AC-D22.4.5 — the panel declares both add and remove intent signals.

All tests run offscreen (tests/conftest.py sets QT_QPA_PLATFORM=offscreen).
"""

import os

import pytest
from PyQt6.QtCore import QPoint, QSettings, Qt, QTimer
from PyQt6.QtWidgets import QDialog, QPushButton

import ui.watchlist_panel as watchlist_panel
from ui.watchlist_panel import (
    SYMBOL_FIELD,
    TICK_LAST,
    WatchlistPanel,
    normalise_symbol,
    symbol_in_list,
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
    p = WatchlistPanel(settings=_isolated_settings(tmp_path / "watchlist_d22.ini"))
    yield p
    p.close()


# ── D22-04-T01 / AC-D22.4.1 — affordance + placement ─────────────────────────

def test_D22_04_T01_add_affordance_and_placement(panel, qapp):
    panel.show()
    qapp.processEvents()

    hb = panel.header_bar
    add_btn = panel.add_button

    # The '+' is a real button, a descendant of the header strip, and shares the
    # strip's layout with the D21.11 toggle.
    assert isinstance(add_btn, QPushButton)
    assert add_btn.text() == "+"
    assert add_btn.parent() is hb
    lay = hb.layout()
    assert lay is not None
    assert lay.indexOf(add_btn) != -1
    assert lay.indexOf(panel.header_button) != -1

    # The D21.11 toggle still collapses/restores the body while the strip stays.
    assert panel.body.isVisible()
    panel.header_button.click()
    qapp.processEvents()
    assert panel.is_collapsed()
    assert not panel.body.isVisible()
    assert hb.isVisible()
    panel.header_button.click()
    qapp.processEvents()
    assert not panel.is_collapsed()
    assert panel.body.isVisible()

    # The header strip has its own custom context menu offering "Add symbol…".
    assert hb.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
    strip_menu = panel._on_strip_context_menu(QPoint(4, 4), show=False)
    assert "Add symbol…" in [a.text() for a in strip_menu.actions()]

    # The D21.5 column popup remains bound to the table's horizontal header — a
    # distinct menu — and Symbol stays non-removable there.
    header = panel.table.horizontalHeader()
    assert header.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
    col_menu = panel._on_header_context_menu(QPoint(0, 0), show=False)
    assert col_menu is not strip_menu
    symbol_action = next(
        a for a in col_menu.actions()
        if a.isCheckable() and a.text() == "Symbol"
    )
    assert symbol_action.isChecked()
    assert not symbol_action.isEnabled()


# ── D22-04-T02 / AC-D22.4.2 — enable state ───────────────────────────────────

def test_D22_04_T02_set_add_enabled_toggles_both(panel):
    # Freshly constructed: both affordances are disabled by default.
    assert not panel.add_button.isEnabled()
    assert not panel.add_action.isEnabled()

    panel.set_add_enabled(True)
    assert panel.add_button.isEnabled()
    assert panel.add_action.isEnabled()

    panel.set_add_enabled(False)
    assert not panel.add_button.isEnabled()
    assert not panel.add_action.isEnabled()


# ── D22-04-T03 / AC-D22.4.3 — pure helpers ───────────────────────────────────

def test_D22_04_T03_pure_helpers():
    assert normalise_symbol(" msft ") == "MSFT"
    assert normalise_symbol("") == ""
    assert normalise_symbol("   ") == ""
    assert normalise_symbol(None) == ""

    assert symbol_in_list("msft", ["MSFT"]) is True
    assert symbol_in_list("MSFT", ["AAPL"]) is False
    # Case-insensitive within a larger list, and blanks are never "present".
    assert symbol_in_list("tsla", ["AAPL", "TSLA", "SPY"]) is True
    assert symbol_in_list("", ["MSFT"]) is False
    assert symbol_in_list("  ", ["MSFT"]) is False


# ── D22-04-T04 / AC-D22.4.4 — invocation + modal emission ────────────────────

class _FakeAddSymbolDialog:
    """Records exec() and reports a canned result / raw text."""

    instances: list = []
    result = QDialog.DialogCode.Accepted
    text_value = "msft"

    def __init__(self, parent=None):
        self.parent = parent
        self.exec_calls = 0
        _FakeAddSymbolDialog.instances.append(self)

    def exec(self):
        self.exec_calls += 1
        return _FakeAddSymbolDialog.result

    def text(self):
        return _FakeAddSymbolDialog.text_value


def test_D22_04_T04_invocation_emits_only_on_accept(panel, monkeypatch):
    monkeypatch.setattr(
        watchlist_panel, "AddSymbolDialog", _FakeAddSymbolDialog)
    _FakeAddSymbolDialog.instances = []
    _FakeAddSymbolDialog.result = QDialog.DialogCode.Accepted
    _FakeAddSymbolDialog.text_value = "msft"

    fired = []
    panel.symbol_add_requested.connect(lambda s: fired.append(s))

    panel.set_add_enabled(True)
    panel.add_button.click()

    # The '+' opened exactly one modal dialog, parented to the panel.
    assert len(_FakeAddSymbolDialog.instances) == 1
    dlg = _FakeAddSymbolDialog.instances[0]
    assert dlg.exec_calls == 1
    assert dlg.parent is panel
    # Accepted with non-empty text -> emitted with that (raw) symbol.
    assert fired == ["msft"]

    # Rejected (Cancel/Esc) opens a dialog but emits nothing.
    _FakeAddSymbolDialog.result = QDialog.DialogCode.Rejected
    _FakeAddSymbolDialog.text_value = "tsla"
    panel.add_button.click()
    assert len(_FakeAddSymbolDialog.instances) == 2
    assert _FakeAddSymbolDialog.instances[1].exec_calls == 1
    assert fired == ["msft"]

    # Accepted but blank text also emits nothing (non-empty is required).
    _FakeAddSymbolDialog.result = QDialog.DialogCode.Accepted
    _FakeAddSymbolDialog.text_value = "   "
    panel.add_button.click()
    assert fired == ["msft"]


# ── D22-04-T05 / AC-D22.4.5 — add + remove signals declared ──────────────────

def test_D22_04_T05_declares_add_and_remove_signals(panel):
    # Declared on the class...
    assert hasattr(WatchlistPanel, "symbol_add_requested")
    assert hasattr(WatchlistPanel, "symbol_remove_requested")

    # ...and live on the instance. A round-trip proves the remove signal exists
    # and carries a str (D22-05 consumes it).
    got = []
    panel.symbol_remove_requested.connect(lambda s: got.append(s))
    panel.symbol_remove_requested.emit("AAPL")
    assert got == ["AAPL"]


# ═════════════════════════════════════════════════════════════════════════════
# D22-05 — remove-side: body context menu + remove_symbol re-indexing
# ═════════════════════════════════════════════════════════════════════════════


class FakeMdManager:
    """Minimal MarketDataManager double: unique reqIds, records cancellations."""

    def __init__(self):
        self._next = 1
        self.cancelled = []

    def req_mkt_data(self, contract):
        req_id = self._next
        self._next += 1
        return req_id

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


@pytest.fixture
def remove_panel(qapp, tmp_path):
    """A 3-row panel (AAPL/MSFT/TSLA) backed by a recording FakeMdManager."""
    p = WatchlistPanel(
        settings=_isolated_settings(tmp_path / "watchlist_d22_remove.ini"))
    md = FakeMdManager()
    p.set_market_data_manager(md)
    for symbol in ("AAPL", "MSFT", "TSLA"):
        p.add_symbol(symbol, object())
    yield p, md
    p.close()


# ── D22-05-T01 / AC-D22.5.1 — body menu offers exactly "Remove symbol" ────────

def test_D22_05_T01_body_menu_offers_remove_for_real_row(remove_panel, qapp):
    panel, _md = remove_panel
    panel.resize(420, 300)
    panel.show()
    qapp.processEvents()

    fired = []
    panel.symbol_remove_requested.connect(lambda s: fired.append(s))

    # Reorder the Symbol column to the end: the menu must still resolve the
    # row's Symbol by field key, not by a fixed column index.
    panel._active_fields.remove(SYMBOL_FIELD)
    panel._active_fields.append(SYMBOL_FIELD)
    panel._apply_columns()
    qapp.processEvents()

    sym_col = panel._column_index(SYMBOL_FIELD)
    row = 1  # MSFT
    pos = panel.table.visualItemRect(panel.table.item(row, sym_col)).center()

    menu = panel._on_body_context_menu(pos, show=False)
    assert menu is not None
    assert [a.text() for a in menu.actions()] == ["Remove symbol"]

    menu.actions()[0].trigger()
    assert fired == ["MSFT"]

    # Empty area below the rows: no menu, no emission.
    assert panel._on_body_context_menu(QPoint(4, 10000), show=False) is None
    # Header area (above the viewport): likewise nothing.
    assert panel._on_body_context_menu(QPoint(4, -5), show=False) is None
    assert fired == ["MSFT"]


# ── D22-05-T02 / AC-D22.5.2 — cancel exactly one reqId + re-index ─────────────

def test_D22_05_T02_remove_cancels_and_reindexes(remove_panel):
    panel, md = remove_panel

    # Rows 0,1,2 ↔ reqIds 1,2,3.
    assert panel._req_to_row == {1: 0, 2: 1, 3: 2}
    panel._prev_close = {1: 100.0, 2: 200.0, 3: 300.0}
    panel._last_price = {1: 101.0, 2: 201.0, 3: 301.0}

    # Flash timers: row 0 stays, row 1 (removed) must be stopped, row 2 shifts up.
    t0, t1, t2 = QTimer(panel), QTimer(panel), QTimer(panel)
    panel._flash_timers = {(0, "last"): t0, (1, "last"): t1, (2, "last"): t2}

    assert panel.remove_symbol("msft") is True  # case-insensitive

    # Exactly the middle row's reqId was cancelled, exactly once.
    assert md.cancelled == [2]

    assert panel.table.rowCount() == 2
    assert panel._req_to_row == {1: 0, 3: 1}
    assert panel._row_data.keys() == {0, 1}
    # Removed reqId's per-reqId state is dropped; the others are untouched.
    assert panel._prev_close == {1: 100.0, 3: 300.0}
    assert panel._last_price == {1: 101.0, 3: 301.0}

    # Flash timers re-indexed: the removed row's timer (t1) is dropped, the row
    # above (t0) is untouched, and the row below (t2) shifts up into the vacated
    # row-1 slot.
    assert t1 not in panel._flash_timers.values()
    assert panel._flash_timers[(0, "last")] is t0
    assert panel._flash_timers[(1, "last")] is t2
    assert (2, "last") not in panel._flash_timers
    assert len(panel._flash_timers) == 2

    # A later tick for the moved-up row's reqId (3 = TSLA) lands on the right row.
    panel.on_tick_price(3, TICK_LAST, 305.0)
    sym_col = panel._column_index(SYMBOL_FIELD)
    last_col = panel._column_index("last")
    assert panel.table.item(1, sym_col).text() == "TSLA"
    assert panel.table.item(1, last_col).text() == "305.00"


# ── D22-05-T03 / AC-D22.5.3 — absent symbol is a no-op ────────────────────────

def test_D22_05_T03_absent_symbol_is_noop(remove_panel):
    panel, md = remove_panel
    before_req = dict(panel._req_to_row)
    before_rows = panel.table.rowCount()

    assert panel.remove_symbol("NOPE") is False
    assert md.cancelled == []
    assert panel.table.rowCount() == before_rows
    assert panel._req_to_row == before_req

    # A blank symbol is likewise a no-op (never matches / never cancels).
    assert panel.remove_symbol("") is False
    assert panel.remove_symbol("   ") is False
    assert md.cancelled == []
    assert panel.table.rowCount() == before_rows
    assert panel._req_to_row == before_req


# ═════════════════════════════════════════════════════════════════════════════
# D23-02 — remove_symbol drops the removed row's own _row_data key (D23.2 / ESC-031)
# ═════════════════════════════════════════════════════════════════════════════


def _three_row_panel(tmp_path, name):
    """A 3-row panel (AAPL/MSFT/TSLA ↔ reqIds 1/2/3) with a recording md double."""
    p = WatchlistPanel(settings=_isolated_settings(tmp_path / name))
    md = FakeMdManager()
    p.set_market_data_manager(md)
    for symbol in ("AAPL", "MSFT", "TSLA"):
        p.add_symbol(symbol, object())
    return p, md


def _one_row_panel(tmp_path, name):
    """A single-row panel (AAPL ↔ reqId 1) with a recording md double."""
    p = WatchlistPanel(settings=_isolated_settings(tmp_path / name))
    md = FakeMdManager()
    p.set_market_data_manager(md)
    p.add_symbol("AAPL", object())
    return p, md


# ── D23-02-T01 / AC-D23.2.1 — last-row removal drops the stale key ───────────

def test_D23_02_T01_last_row_removal_drops_stale_row_key(tmp_path, qapp):
    panel, md = _three_row_panel(tmp_path, "d23_02_t01.ini")
    try:
        # Rows 0,1,2 ↔ reqIds 1,2,3.
        assert panel._req_to_row == {1: 0, 2: 1, 3: 2}
        assert panel.table.rowCount() == 3

        assert panel.remove_symbol("TSLA") is True  # the last row

        assert md.cancelled == [3]
        assert panel.table.rowCount() == 2
        # The removed row's own key (2) must be dropped, not merely overwritten
        # by a later key: the old re-map alone leaves a stale key 2 behind.
        assert sorted(panel._row_data.keys()) == [0, 1]
        assert set(panel._row_data.keys()) == set(range(panel.table.rowCount()))
        assert panel._req_to_row == {1: 0, 2: 1}
        assert set(panel._req_to_row.values()) == set(range(panel.table.rowCount()))
    finally:
        panel.close()


# ── D23-02-T02 / AC-D23.2.2 — first / middle / only-row invariant ────────────

def test_D23_02_T02_first_middle_only_row_invariant(tmp_path, qapp):
    # ── First row removed ────────────────────────────────────────────────────
    panel, _md = _three_row_panel(tmp_path, "d23_02_t02_first.ini")
    try:
        t0, t1, t2 = QTimer(panel), QTimer(panel), QTimer(panel)
        panel._flash_timers = {(0, "last"): t0, (1, "last"): t1, (2, "last"): t2}

        assert panel.remove_symbol("AAPL") is True  # the first row

        rows = panel.table.rowCount()
        assert rows == 2
        assert set(panel._row_data.keys()) == set(range(rows))
        assert set(panel._req_to_row.values()) == set(range(rows))
        assert set(k[0] for k in panel._flash_timers) == set(range(rows))
        # The removed row's timer is gone; survivors shifted up correctly.
        assert t0 not in panel._flash_timers.values()
        assert panel._flash_timers[(0, "last")] is t1
        assert panel._flash_timers[(1, "last")] is t2
    finally:
        panel.close()

    # ── Middle row removed ───────────────────────────────────────────────────
    panel, _md = _three_row_panel(tmp_path, "d23_02_t02_middle.ini")
    try:
        t0, t1, t2 = QTimer(panel), QTimer(panel), QTimer(panel)
        panel._flash_timers = {(0, "last"): t0, (1, "last"): t1, (2, "last"): t2}

        assert panel.remove_symbol("MSFT") is True  # the middle row

        rows = panel.table.rowCount()
        assert rows == 2
        assert set(panel._row_data.keys()) == set(range(rows))
        assert set(panel._req_to_row.values()) == set(range(rows))
        assert set(k[0] for k in panel._flash_timers) == set(range(rows))
        assert t1 not in panel._flash_timers.values()
        assert panel._flash_timers[(0, "last")] is t0
        assert panel._flash_timers[(1, "last")] is t2
    finally:
        panel.close()

    # ── Only row removed ─────────────────────────────────────────────────────
    panel, _md = _one_row_panel(tmp_path, "d23_02_t02_only.ini")
    try:
        t_only = QTimer(panel)
        panel._flash_timers = {(0, "last"): t_only}

        assert panel.remove_symbol("AAPL") is True

        assert panel.table.rowCount() == 0
        assert panel._row_data == {}
        assert panel._req_to_row == {}
        assert panel._flash_timers == {}
    finally:
        panel.close()


# ── D23-02-T05 / AC-D23.2.4 — _row_data stays FieldKey-bound after removal ───

def test_D23_02_T05_row_data_stays_fieldkey_bound_after_removal(tmp_path, qapp):
    panel, _md = _three_row_panel(tmp_path, "d23_02_t05.ini")
    try:
        sym_col = panel._column_index(SYMBOL_FIELD)
        last_col = panel._column_index("last")

        # Cache a "last" value per row (FieldKey-bound).
        panel._set_cell(0, "last", 100.0)
        panel._set_cell(1, "last", 200.0)
        panel._set_cell(2, "last", 300.0)
        assert panel._row_data[1]["last"] == 200.0

        # Remove the first row (AAPL); MSFT's cached value must not shift onto
        # AAPL's vacated slot.
        assert panel.remove_symbol("AAPL") is True
        assert isinstance(panel._row_data, dict)
        assert panel._row_data[0]["last"] == 200.0  # MSFT, not AAPL's 100.0
        assert panel._row_data[1]["last"] == 300.0  # TSLA

        panel._rebuild_table()
        assert panel.table.item(0, sym_col).text() == "MSFT"
        assert panel.table.item(0, last_col).text() == "200.00"
        assert panel.table.item(1, sym_col).text() == "TSLA"
        assert panel.table.item(1, last_col).text() == "300.00"

        # A subsequent _set_cell keeps binding to the right symbol row.
        panel._set_cell(1, "last", 305.0)
        assert panel.table.item(1, last_col).text() == "305.00"

        # Remove the last row (TSLA) too; the remaining MSFT value stays put.
        assert panel.remove_symbol("TSLA") is True
        assert panel.table.rowCount() == 1
        assert set(panel._row_data.keys()) == {0}
        assert panel._row_data[0]["last"] == 200.0
        panel._rebuild_table()
        assert panel.table.item(0, sym_col).text() == "MSFT"
        assert panel.table.item(0, last_col).text() == "200.00"
    finally:
        panel.close()
