"""ESC-043 / AC-D27.6 — scope the portfolio render to the LIVE account and
converge the ``positions`` table on the live session.

Pre-fix, ``MainWindow._on_position_end`` loaded and rendered the WHOLE
``positions`` table with no account filter, so junk rows persisted by
non-hermetic probes (``HELD``/``DU123``, ``H``/``DU1``) appeared in the
portfolio panel. ``_on_position_update`` likewise persisted/rendered any
account. The fix scopes both paths to the accounts the account-summary
subscription has reported.

These tests drive the REAL chain offscreen and assert observable state (never
that an exception propagates out of ``emit`` — pyqtgraph's non-abort
excepthook swallows slot exceptions).

ESC-052: the destructive foreign-row prune is gated on the account-summary
stream COMPLETING (``_on_account_summary_end``), so a ``position_end`` that
fires while ``_live_accounts`` holds only SOME of the user's accounts cannot
delete the remaining real accounts' persisted rows.
"""

from __future__ import annotations

from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient

LIVE_ACCOUNT = "U13148604"
FOREIGN_ACCOUNT = "DU123"
SECOND_ACCOUNT = "U99999999"


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


def _seed_position(symbol: str, con_id: int, account: str,
                   qty: float = 10.0, avg_cost: float = 40.0) -> int:
    from data.db import db

    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO positions "
        "(symbol, account, con_id, contract_type, qty, avg_cost, local_symbol, "
        " multiplier, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (symbol, account, con_id, "stock", qty, avg_cost, symbol, 1.0, 0),
    )
    db.conn.commit()
    return int(cur.lastrowid)


def _count_account(account: str) -> int:
    from data.db import db

    cur = db.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM positions WHERE account=?", (account,))
    return int(cur.fetchone()[0])


def _stock_contract(symbol: str, con_id: int):
    from ibapi.contract import Contract

    contract = Contract()
    contract.symbol = symbol
    contract.localSymbol = symbol
    contract.conId = con_id
    contract.secType = "STK"
    contract.multiplier = "1"
    return contract


# ── AC1: the panel renders only the live account's holdings ─────────────────

def test_p2_t31_t11_render_scoped_to_live_account(monkeypatch, qapp):
    """AC1 — only live-account rows render after ``position_end``."""
    _seed_position("HELD", 999, FOREIGN_ACCOUNT)
    _seed_position("AAPL", 1, LIVE_ACCOUNT)

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, LIVE_ACCOUNT, "NetLiquidation", "100000")
    bridge.position_end.emit()
    qapp.processEvents()

    table = win.portfolio_panel.positions_table
    assert table.rowCount() == 1, (
        f"expected only the live-account row, got {table.rowCount()}")
    assert table.item(0, 0).text() == "AAPL", table.item(0, 0).text()
    rendered = [table.item(r, 0).text() for r in range(table.rowCount())]
    assert "HELD" not in rendered, rendered


# ── AC2: the table is converged on the live session ─────────────────────────

def test_p2_t31_t21_foreign_rows_pruned_live_rows_kept(monkeypatch, qapp):
    """AC2 — foreign rows are deleted when the live set is known; the prune is
    a no-op when the live set is not yet known."""
    _seed_position("HELD", 999, FOREIGN_ACCOUNT)
    _seed_position("AAPL", 1, LIVE_ACCOUNT)

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, LIVE_ACCOUNT, "NetLiquidation", "100000")
    # ESC-052: the destructive prune is gated on the account-summary stream
    # COMPLETING, so drive the end marker to establish the full live set.
    bridge.account_summary_end.emit(win._account_summary_req_id)
    bridge.position_end.emit()
    qapp.processEvents()

    assert _count_account(FOREIGN_ACCOUNT) == 0, "foreign row was not pruned"
    assert _count_account(LIVE_ACCOUNT) == 1, "live row was wrongly removed"

    # Live set unknown: a fresh window has received NO account summary, so the
    # prune must be a no-op — both rows survive.
    _seed_position("HELD", 999, FOREIGN_ACCOUNT)
    win2 = _make_window(monkeypatch, qapp)
    win2._on_position_end()
    qapp.processEvents()

    assert _count_account(FOREIGN_ACCOUNT) == 1, "prune ran with unknown live set"
    assert _count_account(LIVE_ACCOUNT) == 1, "live row was wrongly removed"


# ── AC2 (ESC-052): a PARTIAL live set must not prune ────────────────────────

def test_p2_t31_t41_partial_live_set_does_not_prune(monkeypatch, qapp):
    """ESC-052 — `position_end` firing while only SOME of the user's accounts
    have streamed their summary must NOT delete the remaining real accounts'
    persisted rows. `position_end` (reqPositions) and `accountSummaryEnd`
    (reqAccountSummary) are independent streams with no ordering guarantee."""
    _seed_position("AAPL", 1, LIVE_ACCOUNT)
    _seed_position("MSFT", 2, SECOND_ACCOUNT)

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    # Only ONE of the two real accounts has streamed its summary so far.
    bridge.account_summary.emit(4242, LIVE_ACCOUNT, "NetLiquidation", "100000")
    # `position_end` fires BEFORE the summary stream completes.
    bridge.position_end.emit()
    qapp.processEvents()

    # The un-summarised real account's rows MUST survive — no destructive prune
    # on a partial live set.
    assert _count_account(SECOND_ACCOUNT) == 1, (
        "a real account's rows were pruned on a partial live set")
    assert _count_account(LIVE_ACCOUNT) == 1, "live row was wrongly removed"

    # The render is still scoped to the accounts known so far (no foreign leak).
    table = win.portfolio_panel.positions_table
    rendered = [table.item(r, 0).text() for r in range(table.rowCount())]
    assert rendered == ["AAPL"], rendered

    # Once the summary stream completes with BOTH accounts, the prune runs and
    # the panel converges on the now-complete live set.
    req_id = win._account_summary_req_id
    bridge.account_summary.emit(req_id, SECOND_ACCOUNT, "NetLiquidation", "50000")
    bridge.account_summary_end.emit(req_id)
    qapp.processEvents()

    assert _count_account(SECOND_ACCOUNT) == 1, "live row was wrongly removed"
    assert _count_account(LIVE_ACCOUNT) == 1, "live row was wrongly removed"
    rendered = sorted(
        table.item(r, 0).text() for r in range(table.rowCount()))
    assert rendered == ["AAPL", "MSFT"], rendered


# ── AC3: the live path cannot re-leak a foreign account ─────────────────────

def test_p2_t31_t31_foreign_position_update_not_persisted_or_rendered(
        monkeypatch, qapp):
    """AC3 — with the live account known, a foreign update is dropped."""
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, LIVE_ACCOUNT, "NetLiquidation", "100000")
    # ESC-054 / P2-T38: the live-account set is only AUTHORITATIVE once the
    # account-summary stream COMPLETES. A foreign update arriving BEFORE that
    # is now (correctly) persisted — ESC-054 fixed that silent drop — so this
    # test asserts the "a foreign update is dropped" guarantee after the
    # stream has completed, which is when the guarantee holds.
    bridge.account_summary_end.emit(win._account_summary_req_id)
    qapp.processEvents()

    before = win.portfolio_panel.positions_table.rowCount()
    bridge.position_update.emit(
        FOREIGN_ACCOUNT, _stock_contract("FOREIGN", 999), 5.0, 3.0)
    qapp.processEvents()

    assert _count_account(FOREIGN_ACCOUNT) == 0, (
        "foreign-account update was persisted")
    table = win.portfolio_panel.positions_table
    assert table.rowCount() == before, "foreign-account row was rendered"
    rendered = [table.item(r, 0).text() for r in range(table.rowCount())]
    assert "FOREIGN" not in rendered, rendered
