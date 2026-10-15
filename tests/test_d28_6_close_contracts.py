"""D28.6 T-2 — contract reconstruction for close paths.

``_close_position_by_id`` rebuilds the IBKR contract from the positions
row: stock (bare stock contract), option (secType OPT + conId /
localSymbol / expiry / strike / right), future (secType FUT + conId /
localSymbol / expiry / multiplier). No live transmission: ``placeOrder``
is captured and the order-path limiter is forced open.
"""
import pytest

from data.db import db


def _insert_position(**kw):
    defaults = dict(
        symbol="T2STK", account="DU123", con_id=None, contract_type="stock",
        qty=10.0, avg_cost=100.0, local_symbol=None, multiplier=1.0,
        expiry=None, strike=None, right=None,
    )
    defaults.update(kw)
    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO positions (symbol, account, con_id, contract_type, qty,"
        " avg_cost, local_symbol, multiplier, expiry, strike, right,"
        " updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (defaults["symbol"], defaults["account"], defaults["con_id"],
         defaults["contract_type"], defaults["qty"], defaults["avg_cost"],
         defaults["local_symbol"], defaults["multiplier"],
         defaults["expiry"], defaults["strike"], defaults["right"],
         1_760_000_000),
    )
    db.conn.commit()
    return cur.lastrowid


def _clear_position(pid):
    cur = db.conn.cursor()
    cur.execute("DELETE FROM positions WHERE id=?", (pid,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    # D41-S5: ``_close_position_by_id`` now carries the D26.9 disconnected
    # guard, so the fixture window (whose ``connect`` is stubbed) must be
    # marked connected for the close contracts below to transmit.
    win._ibkr_connected = True
    win.show()
    qapp.processEvents()
    return win


@pytest.fixture()
def closer(monkeypatch, qapp):
    """A window with placeOrder captured and the order limiter forced open."""
    win = _make_window(monkeypatch, qapp)
    placed = []
    monkeypatch.setattr(
        win.ib_client, "placeOrder",
        lambda order_id, contract, order: placed.append(
            (order_id, contract, order)),
    )
    import ui.main_window as mw

    monkeypatch.setattr(mw.order_limiter, "try_acquire", lambda: True)
    from ibkr import id_manager as idm

    monkeypatch.setattr(idm.id_manager, "get_id", lambda: 9001)
    yield win, placed
    win.close()


def test_close_stock_rebuilds_bare_stock_contract(closer):
    win, placed = closer
    pid = _insert_position(symbol="T2STK", contract_type="stock", qty=10.0)
    try:
        win._close_position_by_id(pid)
        assert len(placed) == 1
        order_id, contract, order = placed[0]
        assert order_id == 9001
        assert contract.secType == "STK"
        assert contract.symbol == "T2STK"
        assert order.action == "SELL" and order.totalQuantity == 10.0
    finally:
        _clear_position(pid)


def test_close_option_rebuilds_opt_contract(closer):
    win, placed = closer
    pid = _insert_position(
        symbol="T2OPT", contract_type="option", qty=-2.0,
        con_id=424242, local_symbol="T2OPT  241220C00150000",
        expiry="20241220", strike=150.0, right="C", multiplier=100.0,
    )
    try:
        win._close_position_by_id(pid)
        assert len(placed) == 1
        _, contract, order = placed[0]
        assert contract.secType == "OPT"
        assert contract.conId == 424242
        assert contract.localSymbol == "T2OPT  241220C00150000"
        assert contract.lastTradeDateOrContractMonth == "20241220"
        assert contract.strike == 150.0
        assert contract.right == "C"
        assert contract.multiplier == "100"
        # Short position -> offsetting BUY.
        assert order.action == "BUY" and order.totalQuantity == 2.0
    finally:
        _clear_position(pid)


def test_close_future_rebuilds_fut_contract(closer):
    win, placed = closer
    pid = _insert_position(
        symbol="T2FUT", contract_type="future", qty=3.0,
        con_id=987654, local_symbol="T2FUTH5",
        expiry="202503", multiplier=50.0,
    )
    try:
        win._close_position_by_id(pid)
        assert len(placed) == 1
        _, contract, order = placed[0]
        assert contract.secType == "FUT"
        assert contract.conId == 987654
        assert contract.localSymbol == "T2FUTH5"
        assert contract.lastTradeDateOrContractMonth == "202503"
        assert contract.multiplier == "50"
        assert order.action == "SELL" and order.totalQuantity == 3.0
    finally:
        _clear_position(pid)


def test_close_zero_qty_and_missing_row_are_noops(closer):
    win, placed = closer
    pid = _insert_position(symbol="T2ZERO", qty=0.0)
    try:
        win._close_position_by_id(pid)
        win._close_position_by_id(999_999_999)  # no such row
        assert placed == []
    finally:
        _clear_position(pid)


# ── P1-T65: `_ref_price_for` + the re-homed D41-S5 / D26 gates ───────────────


def test_p1_t65_t11_ref_price_for_normalises_case(closer):
    """T11 (AC1): upper-case-normalised read; None for an unknown symbol."""
    win, _ = closer
    win._symbol_last_prices["T65STK"] = 100.0
    assert win._ref_price_for("t65stk") == 100.0
    assert win._ref_price_for("T65STK") == 100.0
    assert win._ref_price_for("ZZZ") is None


def test_p1_t65_t21_disconnected_refuses_without_transmitting(closer):
    """T21 (AC2): D26.9 guard refuses while disconnected, never placing."""
    win, placed = closer
    win._ibkr_connected = False
    pid = _insert_position(symbol="T65DISC", qty=5.0)
    try:
        win._close_position_by_id(pid)
        assert placed == []
        assert "Not connected" in win.status_bar.currentMessage()
    finally:
        _clear_position(pid)


def test_p1_t65_t31_validation_rejection_precedes_pacing(closer, monkeypatch):
    """T31 (AC3): a failed validation refuses before the pacing token."""
    win, placed = closer
    import ui.main_window as mw

    calls = []
    monkeypatch.setattr(
        mw.order_limiter, "try_acquire",
        lambda: calls.append(1) or False,
    )
    pid = _insert_position(symbol="", qty=5.0)
    try:
        win._close_position_by_id(pid)
        assert placed == []
        assert win.status_bar.currentMessage().startswith("Order rejected:")
        assert calls == []  # gate ran before pacing — no token consumed
    finally:
        _clear_position(pid)


def test_p1_t65_t41_valid_close_transmits_once_with_ref_price(closer):
    """T41 (AC4): a valid close transmits exactly once with ref_price used."""
    win, placed = closer
    win._symbol_last_prices["T65OK"] = 42.5
    pid = _insert_position(symbol="T65OK", contract_type="stock", qty=10.0)
    try:
        win._close_position_by_id(pid)
        assert len(placed) == 1
        _, contract, order = placed[0]
        assert contract.secType == "STK"
        assert contract.symbol == "T65OK"
        assert order.action == "SELL" and order.totalQuantity == 10.0
    finally:
        _clear_position(pid)
