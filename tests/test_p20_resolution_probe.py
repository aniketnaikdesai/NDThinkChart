"""P20-T1 — contract resolution + probe-first seam + error-200 honesty.

Offscreen tests (no live TWS):

* AC1 — 4 index symbols x 2 modes asserting IND + table exchange/currency
  via ``get_contract_for_symbol`` (red-first against STK/SMART fallthrough).
* AC2 — 4 futures roots asserting FUT/CME/USD + ``_front_month`` expiry;
  STK controls (SPY/QQQ/DIA/IWM/AAPL/BRK.B) asserting STK with no probe.
* AC3a — unknown-symbol load with a failing probe: exactly one probe reqId,
  zero prime/wave/realtime reqIds, refuse status, nothing persisted.
* AC3b — unknown-symbol load with a succeeding probe: the legs proceed on
  the first returned ``ContractDetails`` payload's contract for that load
  only, with no mapping persisted.
* AC4 — error 200 on a prime/wave leg: verbatim AC-D16.4 shortfall, no
  realtime attach, no lingering realtime reqIds.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QDockWidget

from ibapi.contract import Contract

from ibkr import contracts as contracts_mod
from ibkr.contracts import get_contract_for_symbol
from data.bar_cache import BarCache
from data.db import db


# ---------------------------------------------------------------------------
# Shared offscreen harness (load-path style: stubbed managers, never a socket)
# ---------------------------------------------------------------------------

class _ReqStub:
    """Captures historical + contract-details requests and RT subscribes."""

    def __init__(self, first_id: int = 1000):
        self.hist_calls: list[dict] = []
        self.probe_calls: list[dict] = []
        self.rt_calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False, **kwargs):
        req_id = self._next
        self._next += 1
        self.hist_calls.append({
            "reqId": req_id,
            "contract": contract,
            "timeframe": timeframe,
            "endDateTime": endDateTime,
            "extended_hours": extended_hours,
            **kwargs,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)

    def req_details(self, contract):
        req_id = self._next
        self._next += 1
        self.probe_calls.append({"reqId": req_id, "contract": contract})
        return req_id

    def subscribe(self, symbol, contract):
        req_id = self._next
        self._next += 1
        self.rt_calls.append(
            {"reqId": req_id, "symbol": symbol, "contract": contract}
        )
        return req_id


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

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


def _wire(win, stub: _ReqStub):
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.md_manager.req_contract_details = stub.req_details
    win.rt_manager.subscribe = stub.subscribe


def _clear(symbol: str, timeframe: str) -> None:
    for ext in (True, False):
        for tf in {timeframe, "5 mins"}:
            db.conn.execute(
                "DELETE FROM bars WHERE symbol=? AND timeframe=?",
                (symbol, tf),
            )
    db.conn.commit()


def _mid_period_now() -> int:
    """Wall-clock now guaranteed mid-period for '5 mins' (prime active)."""
    now = int(time.time())
    return (now // 300) * 300 + 120


# ---------------------------------------------------------------------------
# P20-T1-AC1 — index resolution matrix (IND table, never STK/SMART)
# ---------------------------------------------------------------------------

_EXPECTED_IND = {
    "SPX": ("IND", "CBOE", "USD"),
    "NDX": ("IND", "NASDAQ", "USD"),
    "DJI": ("IND", "CME", "USD"),
    "RUT": ("IND", "CME", "USD"),
}


@pytest.mark.parametrize("symbol", sorted(_EXPECTED_IND))
@pytest.mark.parametrize("extended_hours", [True, False])
def test_p20_t1_ac1_index_symbols_resolve_ind(symbol, extended_hours):
    sec_type, exchange, currency = _EXPECTED_IND[symbol]
    contract = get_contract_for_symbol(symbol)
    assert contract is not None, f"{symbol} must resolve (never unknown)"
    assert contract.symbol == symbol
    assert contract.secType == sec_type
    assert contract.secType == "IND"
    assert contract.secType != "STK"
    assert contract.exchange == exchange
    assert contract.exchange != "SMART"
    assert contract.currency == currency


# ---------------------------------------------------------------------------
# P20-T1-AC2 — futures roots + STK controls (no probe for either)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("root", ["ES", "NQ", "YM", "RTY"])
def test_p20_t1_ac2_futures_roots_resolve_fut_front_month(root):
    now = None  # production clock; expected computed from the same clock
    contract = get_contract_for_symbol(root)
    assert contract is not None
    assert contract.symbol == root
    assert contract.secType == "FUT"
    assert contract.exchange == "CME"
    assert contract.currency == "USD"
    year, month = contracts_mod._front_month(root, now)
    assert contract.lastTradeDateOrContractMonth == f"{year}{month:02d}"


@pytest.mark.parametrize("symbol", ["SPY", "QQQ", "DIA", "IWM", "AAPL", "BRK.B"])
def test_p20_t1_ac2_stk_controls_resolve_stk_without_probe(
    monkeypatch, qapp, symbol
):
    contract = get_contract_for_symbol(symbol)
    assert contract is not None, f"{symbol} must resolve STK (no probe)"
    assert contract.secType == "STK"

    # Load-level: an STK symbol never enters the probe path.
    win = _make_window(monkeypatch, qapp)
    try:
        _clear(symbol, "5 mins")
        stub = _ReqStub()
        _wire(win, stub)
        win._now_ts = _mid_period_now
        win.load_chart(symbol, "5 mins", True)
        assert stub.probe_calls == [], (
            f"{symbol} is STK — the probe path must never be entered"
        )
        assert win._pending_probes == {}
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P20-T1-AC3a — unknown symbol, failing probe: one probe, refuse, nothing else
# ---------------------------------------------------------------------------

def test_p20_t1_ac3a_unknown_symbol_failing_probe_refuses(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "VERYLONGSYMBOL", "5 mins"  # 13 chars: STK-charset miss
    assert get_contract_for_symbol(symbol) is None
    try:
        _clear(symbol, tf)
        stub = _ReqStub()
        _wire(win, stub)
        win._now_ts = _mid_period_now
        win.load_chart(symbol, tf, True)

        # Exactly one probe reqId, zero prime/wave/realtime reqIds.
        assert len(stub.probe_calls) == 1
        assert stub.hist_calls == []
        assert stub.rt_calls == []
        assert len(win._pending_probes) == 1
        probe_id = stub.probe_calls[0]["reqId"]
        # The probe rides the bare symbol-only contract (no STK/SMART guess).
        probe_contract = stub.probe_calls[0]["contract"]
        assert probe_contract.symbol == symbol
        assert getattr(probe_contract, "secType", "") != "STK"

        # The probe fails (TWS error) → honest refuse.
        win._contract_lookup.on_error(probe_id, 200, "No security definition")
        assert stub.hist_calls == []
        assert stub.rt_calls == []
        assert win._pending_probes == {}
        assert symbol not in win._sessions
        assert "load refused" in win.status_bar.currentMessage()
        assert BarCache.get_bars(symbol, tf, ext_hours=True) == []
        assert BarCache.get_bars(symbol, tf, ext_hours=False) == []
        assert symbol not in [s for s, _cat in db.get_watchlist()]
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P20-T1-AC3b — unknown symbol, succeeding probe: adopt first details, no map
# ---------------------------------------------------------------------------

def test_p20_t1_ac3b_unknown_symbol_probe_success_adopts(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "TOOLONGNAME!", "5 mins"  # charset miss ('!' + 12 chars)
    assert get_contract_for_symbol(symbol) is None
    try:
        _clear(symbol, tf)
        stub = _ReqStub()
        _wire(win, stub)
        win._now_ts = _mid_period_now
        win.load_chart(symbol, tf, True)

        assert len(stub.probe_calls) == 1
        probe_id = stub.probe_calls[0]["reqId"]

        # TWS resolves the symbol: first details payload wins for this load.
        adopted = Contract()
        adopted.symbol = symbol
        adopted.secType = "STK"
        adopted.exchange = "SMART"
        adopted.currency = "USD"
        win._contract_lookup.on_contract_details(
            probe_id, SimpleNamespace(contract=adopted)
        )
        win._contract_lookup.on_contract_details_end(probe_id)

        # Every leg (prime + wave, and any realtime attach) rides the adopted
        # contract — with exactly one probe reqId preceding them.
        assert stub.hist_calls, "adopted legs must issue historical requests"
        for call in stub.hist_calls:
            assert call["contract"] is adopted
        for call in stub.rt_calls:
            assert call["contract"] is adopted
        assert win._pending_probes == {}

        # No mapping is persisted: resolution still returns None afterwards,
        # and the symbol is in no watchlist row.
        assert get_contract_for_symbol(symbol) is None
        assert symbol not in [s for s, _cat in db.get_watchlist()]
    finally:
        win.close()


# ---------------------------------------------------------------------------
# ESC-108 — adopted probe contract survives restore and prefetch waves
# (no None contract queued)
# ---------------------------------------------------------------------------

def test_p20_t1_esc108_prefetch_keeps_adopted_contract(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "TOOLONGNAME!", "5 mins"  # charset miss ('!' + 12 chars)
    assert get_contract_for_symbol(symbol) is None
    try:
        _clear(symbol, tf)
        stub = _ReqStub()
        _wire(win, stub)
        win._now_ts = _mid_period_now
        win.load_chart(symbol, tf, True)

        assert len(stub.probe_calls) == 1
        probe_id = stub.probe_calls[0]["reqId"]
        adopted = Contract()
        adopted.symbol = symbol
        adopted.secType = "STK"
        adopted.exchange = "SMART"
        adopted.currency = "USD"
        win._contract_lookup.on_contract_details(
            probe_id, SimpleNamespace(contract=adopted)
        )
        win._contract_lookup.on_contract_details_end(probe_id)

        session = win._sessions[symbol]
        assert session._wave_contract is adopted

        # Simulate a completed wave with one old cached bar behind it, so
        # the prefetch seam has something fetchable to issue.
        session._history_req_ids = set()
        session._wave_plan_queue = []
        old_ts = _mid_period_now() - 30 * 86400
        monkeypatch.setattr(
            BarCache,
            "get_bars",
            staticmethod(lambda *a, **k: [SimpleNamespace(ts=old_ts)]),
        )
        try:
            win.ext_hours_btn.setChecked(True)
        except Exception:
            pass
        stub.hist_calls.clear()
        win._current_symbol = symbol
        win._current_tf = tf
        fired = win.maybe_issue_prefetch_wave(old_ts, False, fire=True)

        # The prefetch wave rides the adopted contract — never None.
        assert fired is True
        assert len(stub.hist_calls) == 1
        assert stub.hist_calls[0]["contract"] is adopted
    finally:
        win.close()


def test_p20_t1_esc108_restore_never_queues_none_contract(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "VERYLONGSYMBOL", "5 mins"  # 13 chars: STK-charset miss
    assert get_contract_for_symbol(symbol) is None
    try:
        _clear(symbol, tf)
        stub = _ReqStub()
        _wire(win, stub)
        win._now_ts = _mid_period_now
        old_ts = _mid_period_now() - 30 * 86400
        monkeypatch.setattr(
            BarCache,
            "get_bars",
            staticmethod(lambda *a, **k: [SimpleNamespace(ts=old_ts)]),
        )
        win._ensure_restore_data_path(
            {"symbol": symbol, "timeframe": tf, "ext_hours": True}
        )

        # Spans exist (non-vacuous) but no wave may carry a None contract.
        assert win._sessions[symbol]._backfill_missing_spans != []
        assert stub.hist_calls == []
        assert stub.probe_calls == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P20-T1-AC4 — error 200 on a leg: shortfall, no realtime, no dead reqIds
# ---------------------------------------------------------------------------

def test_p20_t1_ac4_error_200_rejects_contract_honestly(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol, tf = "ES", "5 mins"
    try:
        _clear(symbol, tf)
        stub = _ReqStub()
        _wire(win, stub)
        win._now_ts = _mid_period_now
        assert get_contract_for_symbol(symbol) is not None  # known: no probe
        win.load_chart(symbol, tf, True)
        assert stub.probe_calls == []

        session = win._sessions[symbol]
        leg_ids = set(session._history_req_ids)
        if session._prime_req_id is not None:
            leg_ids.add(session._prime_req_id)
        assert leg_ids, "expected prime and/or wave legs in flight"

        # TWS rejects the contract on every leg (error 200).
        for req_id in sorted(leg_ids):
            win._on_error(req_id, 200, "No security definition for contract")

        # The latch is set; realtime never attached (no dead reqIds); the
        # wave finalizes with the verbatim AC-D16.4 shortfall wording.
        assert session._contract_rejected_200 is True
        assert stub.rt_calls == []
        assert session.rt_req_id is None
        message = win.status_bar.currentMessage()
        assert (
            "backfill incomplete" in message
            or "chart may be incomplete" in message
        ), f"expected AC-D16.4 shortfall, got: {message!r}"
    finally:
        win.close()
