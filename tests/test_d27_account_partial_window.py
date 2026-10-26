"""ESC-054 — a real account's ``position_update`` arriving before its own
``account_summary`` callback must not be silently dropped.

``reqPositions`` (``position_update``/``position_end``) and
``reqAccountSummary`` (``account_summary``/``account_summary_end``) are
INDEPENDENT streams with no ordering guarantee. ``_live_accounts`` is
AUTHORITATIVE only once the summary stream has COMPLETED
(``_account_summary_complete``); before that the set may hold only SOME of the
user's accounts. Gating ``_on_position_update``'s foreign-account early-return
on a non-empty-but-partial set silently discarded a real second account's
update — neither persisted nor rendered, unrecoverable for the session.

These tests drive the REAL chain offscreen and assert observable state (never
that an exception propagates out of ``emit`` — pyqtgraph's non-abort excepthook
swallows slot exceptions).

ESC-043/ESC-052: the completed-set gate is NOT reverted — a foreign-account
update arriving AFTER the summary stream completes is still dropped (AC3).
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


def _rendered(win) -> list[str]:
    table = win.portfolio_panel.positions_table
    return [table.item(r, 0).text() for r in range(table.rowCount())]


# ── AC1: a pre-completion update for a real account is NOT discarded ────────

def test_p2_t38_t11_pre_completion_update_persisted_and_rendered(
        monkeypatch, qapp):
    """AC1 — with the summary stream IN PROGRESS (one callback for A, no end
    marker), an update for a real second account B is persisted AND rendered."""
    _seed_position("AAPL", 1, LIVE_ACCOUNT)

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    # ONLY account A has streamed its summary — NO account_summary_end yet, so
    # `_live_accounts == {A}` is non-empty but PARTIAL.
    bridge.account_summary.emit(4242, LIVE_ACCOUNT, "NetLiquidation", "100000")
    qapp.processEvents()

    # A real second account B's update arrives before its own summary callback.
    bridge.position_update.emit(
        SECOND_ACCOUNT, _stock_contract("MSFT", 2), 10.0, 5.0)
    qapp.processEvents()

    assert _count_account(SECOND_ACCOUNT) == 1, (
        "pre-completion update for a real account was discarded (not persisted)")
    rendered = _rendered(win)
    assert "MSFT" in rendered, (
        f"pre-completion update was not rendered: {rendered}")


# ── AC2: the outcome is recoverable once the summary completes ──────────────

def test_p2_t38_t21_pre_completion_update_survives_completion(
        monkeypatch, qapp):
    """AC2 — continue the T11 sequence: once the summary stream completes with
    the full set {A, B} and ``position_end`` runs, B's row still exists and is
    rendered — the panel converges on the complete live set."""
    _seed_position("AAPL", 1, LIVE_ACCOUNT)

    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    bridge.account_summary.emit(4242, LIVE_ACCOUNT, "NetLiquidation", "100000")
    qapp.processEvents()
    bridge.position_update.emit(
        SECOND_ACCOUNT, _stock_contract("MSFT", 2), 10.0, 5.0)
    qapp.processEvents()

    assert _count_account(SECOND_ACCOUNT) == 1, (
        "pre-completion update was discarded before the summary completed")

    # The summary stream now completes with the FULL set {A, B}, then the
    # position stream ends.
    req_id = win._account_summary_req_id
    bridge.account_summary.emit(req_id, SECOND_ACCOUNT, "NetLiquidation", "50000")
    bridge.account_summary_end.emit(req_id)
    bridge.position_end.emit()
    qapp.processEvents()

    assert _count_account(SECOND_ACCOUNT) == 1, (
        "a real account's row was missing after the summary completed")
    rendered = sorted(_rendered(win))
    assert rendered == ["AAPL", "MSFT"], (
        f"panel did not converge on the complete live set: {rendered}")


# ── AC3: ESC-043/ESC-052 completed-set gate is NOT reverted ─────────────────

def test_p2_t38_t31_foreign_update_after_completion_still_dropped(
        monkeypatch, qapp):
    """AC3 — once the summary stream has COMPLETED and the live set is {A}, a
    foreign-account update is still neither persisted nor rendered."""
    win = _make_window(monkeypatch, qapp)
    _stub_account_calls(win, monkeypatch)
    win._on_connected()

    bridge = win.ib_client.bridge
    req_id = win._account_summary_req_id
    bridge.account_summary.emit(req_id, LIVE_ACCOUNT, "NetLiquidation", "100000")
    bridge.account_summary_end.emit(req_id)
    qapp.processEvents()

    before = win.portfolio_panel.positions_table.rowCount()
    bridge.position_update.emit(
        FOREIGN_ACCOUNT, _stock_contract("FOREIGN", 999), 5.0, 3.0)
    qapp.processEvents()

    assert _count_account(FOREIGN_ACCOUNT) == 0, (
        "foreign-account update after completion was persisted")
    table = win.portfolio_panel.positions_table
    assert table.rowCount() == before, "foreign-account row was rendered"
    assert "FOREIGN" not in _rendered(win), _rendered(win)
