"""ESC-032 / P2-T27 — the live position path must hand the panel a Position
that carries the REAL ``positions.id`` DB row key.

Pre-fix, ``MainWindow._on_position_update`` built an ``ibkr.account.Position``
(which had no ``id`` field) while ``ActivePortfolioPanel._render_table``
dereferences ``pos.id`` for strategy grouping and the SL/TP dialog. Every TWS
position update therefore raised ``AttributeError: 'Position' object has no
attribute 'id'`` inside the render; pyqtgraph's non-abort ``sys.excepthook``
swallowed it, so the panel silently showed nothing while the object was still
appended to ``_positions`` (membership-only assertions passed).

These tests drive the REAL chain offscreen and assert observable state (never
that an exception propagates out of ``emit``).
"""

from __future__ import annotations

import sys

import pytest
from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _stub_account_calls(win, monkeypatch):
    calls: dict = {}

    def req_positions():
        calls["reqPositions"] = True

    def req_account_summary(req_id, group, tags):
        calls["reqAccountSummary"] = (req_id, group, tags)

    monkeypatch.setattr(win.ib_client, "reqPositions", req_positions)
    monkeypatch.setattr(win.ib_client, "reqAccountSummary", req_account_summary)
    return calls


def _stock_contract(symbol: str = "AAPL", con_id: int = 265598):
    from ibapi.contract import Contract

    contract = Contract()
    contract.symbol = symbol
    contract.localSymbol = symbol
    contract.conId = con_id
    contract.secType = "STK"
    contract.multiplier = "1"
    return contract


class _RecordingExcepthook:
    """Temporary ``sys.excepthook`` that records unhandled exceptions.

    pyqtgraph installs a non-abort excepthook, so a slot exception is printed
    and swallowed — observable state is the only reliable guard. This records
    anything that reaches the hook so a defect cannot hide.
    """

    def __init__(self):
        self.records: list = []
        self._prev = None

    def __call__(self, exc_type, exc_value, tb):
        self.records.append((exc_type, exc_value, tb))

    def __enter__(self):
        self._prev = sys.excepthook
        sys.excepthook = self
        return self

    def __exit__(self, *exc):
        sys.excepthook = self._prev
        return False


def _seed_position(symbol: str, con_id: int, account: str = "DU123",
                   qty: float = 10.0, avg_cost: float = 40.0) -> int:
    from data.db import db

    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO positions "
        "(symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, "
        " multiplier, stop_loss, take_profit, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (symbol, account, con_id, "stock", qty, avg_cost, symbol, 1.0,
         None, None, 0),
    )
    db.conn.commit()
    return int(cur.lastrowid)


# ── AC1: live path ──────────────────────────────────────────────────────────

def test_p2_t27_t11_live_position_update_renders_with_real_id(monkeypatch, qapp):
    """AC1 — every live update renders and carries a populated `id`."""
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    recorder = _RecordingExcepthook()
    with recorder:
        win.ib_client.bridge.position_update.emit(
            "DU123", _stock_contract(), 10.0, 40.0)
        qapp.processEvents()
        # AC1 says EVERY update, not just the first: a repeat update for the
        # same contract must upsert (still one row) and stay renderable.
        win.ib_client.bridge.position_update.emit(
            "DU123", _stock_contract(), 12.0, 41.0)
        qapp.processEvents()

    assert recorder.records == [], (
        f"unhandled exception on the live position path: {recorder.records!r}")

    table = win.portfolio_panel.positions_table
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "AAPL"      # Symbol populated
    assert table.item(0, 3).text() == "STOCK"     # Type populated

    positions = win.portfolio_panel._positions
    assert len(positions) == 1
    assert positions[0].id is not None


# ── AC2: bulk path ──────────────────────────────────────────────────────────

def test_p2_t27_t21_position_end_loads_every_row_with_its_own_id(monkeypatch, qapp):
    """AC2 — `_on_position_end` must load each row's `positions.id`."""
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    first_id = _seed_position("AAPL", 265598)
    second_id = _seed_position("MSFT", 111)

    win._on_position_end()
    qapp.processEvents()

    positions = win.portfolio_panel._positions
    assert len(positions) == 2
    ids = {p.symbol: p.id for p in positions}
    assert ids == {"AAPL": first_id, "MSFT": second_id}
    assert all(p.id is not None for p in positions)

    # The table must be built from id-carrying objects — Strategy/Group cells
    # exist (they render '—' for stock, but the render must not be skipped).
    table = win.portfolio_panel.positions_table
    assert table.rowCount() == 2
    assert table.item(0, 8) is not None
    assert table.item(0, 9) is not None


# ── AC3: the id is the real DB row key (SL/TP persistence) ──────────────────

def test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row(monkeypatch, qapp):
    """AC3 — the populated id is the row key `UPDATE ... WHERE id=?` targets."""
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    # Live path populates a real id.
    win.ib_client.bridge.position_update.emit(
        "DU123", _stock_contract(), 10.0, 40.0)
    qapp.processEvents()

    pos = win.portfolio_panel._positions[0]
    assert pos.id is not None
    pos_id = pos.id

    # A decoy row that must NOT change.
    decoy_id = _seed_position("MSFT", 111)
    assert decoy_id != pos_id

    # `position_sltp_changed -> MainWindow._on_portfolio_sltp_changed` is wired
    # in MainWindow.__init__, so this drives the real persistence path.
    win.portfolio_panel.update_position_sltp(pos_id, 1.5, 3.5)
    qapp.processEvents()

    from data.db import db

    cur = db.conn.cursor()
    cur.execute("SELECT stop_loss, take_profit FROM positions WHERE id=?", (pos_id,))
    assert cur.fetchone() == (1.5, 3.5)

    cur.execute("SELECT stop_loss, take_profit FROM positions WHERE id=?", (decoy_id,))
    assert cur.fetchone() == (None, None)
