"""D65 / P23-05 — the Option Spreads live stream wiring.

A real ``MainWindow`` against a fake TWS: the panel's ON/OFF lifecycle, the
chain request, per-leg subscribe/cancel application, the registry registration
under ``OPTION_LEGS`` (value ``"option_legs"``) with its ``reissue``/``rebind``
hooks, the one SPX spot line and its three tiers, the 16 + 1 line ceiling, the
1 s cadence evaluation, the coalesced refresh, the 16:15 ET cutoff and every
per-line fault routed end-to-end through ``_on_error``.

No test connects to TWS and no test can record an order call: the fake client's
order surface is a recorder that every case asserts empty.

Synthetic quotes: a 20-wide pair's credit mid is ``1.00 - 0.02 * (short - 7350)``
for CCS and ``1.00 + 0.02 * (short - 7350)`` for PCS, so one 5-point rung moves
the mid by 0.10 -- above ``h = 0.05`` at T < 3.00 -- and the Target's minimiser is
a known strike with the displayed (negative) pair exactly assertable.
Bid = price, ask = price + 0.10, so a pair's three credit bases are
``mid - 0.10``, ``mid`` and ``mid + 0.10``.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QDockWidget

from ibkr.client import IBApiClient
from ibkr.contracts import today_expiry_yyyymmdd
from ibkr.pacing import PacingExceeded
from ibkr.subscription_manager import MARKET_DATA, OPTION_LEGS, RT_BARS, S0_TICKS
from services.option_ladder import LegKey, match_band

TODAY = today_expiry_yyyymmdd()
SPOT = 7350.0
STRIKES = [7000.0 + 5.0 * i for i in range(121)]  # 7000 … 7600
#: The committed window at either anchor (rungs 1..4, top row first). Each side
#: reads its own per-row offsets: CCS keeps P23's +10/+5/0/-5, so its anchor is
#: row 3; PCS is +5/0/-5/-10, so its anchor is row 2 and the row-4 short is new.
EXPECTED_SHORTS_CCS = [7360.0, 7355.0, 7350.0, 7345.0]
EXPECTED_SHORTS_PCS = [7355.0, 7350.0, 7345.0, 7340.0]
#: The one window leg AC1 leaves unquoted (the partial-leg case).
UNFED = {7380.0}


# ---------------------------------------------------------------------------
# Synthetic quote model
# ---------------------------------------------------------------------------


def _price(strike: float, right: str) -> float:
    x = float(strike) - SPOT
    if right == "C":
        # f(x) - f(x+20) = 1.00 - 0.02x — the CCS credit mid falls 0.02/point,
        # so one 5-point rung changes d by 0.10 (above h = 0.05).
        return 100.0 - 0.06 * x + 0.0005 * x * x
    # g(x) - g(x-20) = 1.00 + 0.02x — the PCS credit mid rises 0.02/point.
    return 100.0 + 0.06 * x + 0.0005 * x * x


def _credit(short: float, side: str) -> float:
    """The pair's credit mid on ``side``: CCS falls 0.02/point, PCS rises."""
    points = float(short) - SPOT
    if side == "CCS":
        return 1.00 - 0.02 * points
    return 1.00 + 0.02 * points


def _delta(strike: float) -> float:
    return 0.5 - 0.001 * (float(strike) - SPOT)


def _gamma(strike: float) -> float:
    return 0.01 + 0.00002 * (float(strike) - SPOT)


def _expected_display(short: float, side: str) -> tuple[str, str]:
    mid = _credit(short, side)
    return f"{-mid + 0.10:.2f}", f"{-mid - 0.10:.2f}"


# ---------------------------------------------------------------------------
# The fake TWS client
# ---------------------------------------------------------------------------


class _FakeOptionTws:
    """Records every subscription; never reaches TWS, never places an order."""

    def __init__(self) -> None:
        self.mkt_data: list[int] = []
        self.option_lines: list[tuple[int, object]] = []
        self.cancels: list[int] = []
        self.sec_def: list[tuple] = []
        self.contract_details: list[int] = []
        self.historical: list[tuple] = []
        self.orders: list[tuple] = []
        self.live: dict[int, object] = {}
        self.events: list[tuple[str, int, object]] = []
        self.steps: list[tuple[int, int]] = []

    # -- market data -------------------------------------------------------
    def reqMktData(self, reqId, contract, generic_ticks="", *args, **kwargs):
        self.mkt_data.append(reqId)
        self.live[reqId] = contract
        if getattr(contract, "secType", "") == "OPT":
            self.option_lines.append((reqId, contract))
        self.events.append(("subscribe", reqId, contract))
        self._snapshot()

    def cancelMktData(self, reqId):
        self.cancels.append(reqId)
        self.live.pop(reqId, None)
        self.events.append(("cancel", reqId, None))
        self._snapshot()

    def drop_all(self) -> None:
        """A transport drop: TWS kills every line; no ``cancelMktData`` happens."""
        self.live.clear()

    # -- discovery ---------------------------------------------------------
    def reqContractDetails(self, reqId, contract):
        self.contract_details.append(reqId)

    def reqSecDefOptParams(self, reqId, symbol, exchange, sec_type, con_id):
        self.sec_def.append((reqId, symbol, exchange, sec_type, con_id))

    def reqHistoricalData(self, *args, **kwargs):
        self.historical.append(args)

    # -- the order surface: a recorder that must stay empty ----------------
    def placeOrder(self, *args, **kwargs):
        self.orders.append(("place", args))

    def cancelOrder(self, *args, **kwargs):
        self.orders.append(("cancel", args))

    def reqGlobalCancel(self, *args, **kwargs):
        self.orders.append(("global", args))

    # -- accounting --------------------------------------------------------
    def _snapshot(self) -> None:
        self.steps.append(self.counts())

    def counts(self) -> tuple[int, int]:
        option = sum(
            1 for c in self.live.values() if getattr(c, "secType", "") == "OPT"
        )
        spot = sum(
            1 for c in self.live.values() if getattr(c, "secType", "") == "IND"
        )
        return option, spot

    def live_of(self, sec_type: str) -> list[tuple[int, object]]:
        return [
            (req_id, contract)
            for req_id, contract in self.live.items()
            if getattr(contract, "secType", "") == sec_type
        ]

    def leg_req(self, strike: float, right: str) -> int | None:
        for req_id, contract in self.live.items():
            if getattr(contract, "secType", "") != "OPT":
                continue
            if (str(getattr(contract, "right", "")) == right
                    and abs(float(contract.strike) - float(strike)) < 1e-9):
                return req_id
        return None

    def leg_reqs(self) -> dict[tuple[str, float], int]:
        out: dict[tuple[str, float], int] = {}
        for req_id, contract in self.live.items():
            if getattr(contract, "secType", "") != "OPT":
                continue
            out[(str(contract.right), float(contract.strike))] = req_id
        return out


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


def _make_window(monkeypatch, qapp):
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod

    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    fake = _FakeOptionTws()
    win.rt_manager.client = fake
    win.md_manager.client = fake
    win._restore_popouts = lambda: None
    # Pin the ET clock BEFORE the 16:15 cutoff so the suite is independent of
    # when it runs; only the cutoff case overrides this.
    win._option_et_now = lambda: datetime(2026, 11, 17, 10, 0)
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.objectName() == "Option Spreads":
            dock.hide()
    qapp.processEvents()
    return win, fake


class _StatusLog:
    """Records every non-empty panel status message (one per fault cause)."""

    def __init__(self, win) -> None:
        self.messages: list[str] = []
        win.option_spreads_panel.set_status = self._record

    def _record(self, text) -> None:
        if text:
            self.messages.append(str(text))

    def matching(self, needle: str) -> list[str]:
        return [m for m in self.messages if needle in m]


def _cells(win, side: str, row: int) -> list[str]:
    panel = win.option_spreads_panel
    table = panel.ccs_table if side == "CCS" else panel.pcs_table
    out: list[str] = []
    for column in range(5):
        item = table.item(row, column)
        out.append(item.text() if item is not None else "")
    return out


def _feed_spot(win, fake, price: float = SPOT) -> int | None:
    spots = fake.live_of("IND")
    if not spots:
        return None
    req_id = spots[-1][0]
    win.ib_client.bridge.tick_price.emit(req_id, 4, price)
    return req_id


def _feed_leg(win, fake, strike: float, right: str, *, greeks: bool = True,
              bid: float | None = None, ask: float | None = None) -> None:
    req_id = fake.leg_req(strike, right)
    if req_id is None:
        return
    price = _price(strike, right)
    bridge = win.ib_client.bridge
    bridge.tick_price.emit(req_id, 1, price if bid is None else bid)
    bridge.tick_price.emit(req_id, 2, price + 0.10 if ask is None else ask)
    if greeks:
        bridge.option_computation.emit(
            req_id, 13, _delta(strike), _gamma(strike))


def _feed_all(win, fake, *, greeks: bool = True, skip=()) -> None:
    for _req_id, contract in list(fake.live.items()):
        if getattr(contract, "secType", "") != "OPT":
            continue
        strike = float(contract.strike)
        if strike in skip:
            continue
        _feed_leg(win, fake, strike, str(contract.right), greeks=greeks)


def _toggle_on(win, fake, *, spot: float | None = SPOT) -> None:
    """Click the panel's toggle ON and feed the spot (tier 3b by default)."""
    panel = win.option_spreads_panel
    panel.toggle_button.click()
    assert panel.toggle_button.isChecked() is True
    if spot is not None:
        _feed_spot(win, fake, spot)


def _deliver_chain(win, fake, *, strikes=None, expirations=None,
                   trading_class: str = "SPXW") -> None:
    """Answer the contract lookup and the chain request (the real signal path)."""
    assert fake.contract_details, "the SPX index lookup was never issued"
    lookup_id = fake.contract_details[-1]
    bridge = win.ib_client.bridge
    bridge.contract_details.emit(
        lookup_id, SimpleNamespace(contract=SimpleNamespace(conId=12345)))
    bridge.contract_details_end.emit(lookup_id)
    assert fake.sec_def, "reqSecDefOptParams was never issued"
    chain_id = fake.sec_def[-1][0]
    bridge.option_params.emit(
        chain_id,
        {
            "tradingClass": trading_class,
            "exchange": "SMART",
            "expirations": list(expirations or [TODAY]),
            "strikes": list(STRIKES if strikes is None else strikes),
            "underlyingConId": 12345,
        },
    )
    bridge.option_params_end.emit(chain_id)


def _settle(win, fake, *, ticks: int = 60, greeks: bool = True,
            skip=()) -> float:
    """Drive the 1 s cadence until the seed commits; return the last clock read."""
    base = time.monotonic() + 1.0
    now = base
    for index in range(ticks):
        _feed_all(win, fake, greeks=greeks, skip=skip)
        now = base + index * 0.2
        win._option_eval_step(now)
        if (not win._option_engine.seed_state().active
                and win._option_engine.anchor("CCS") is not None):
            _feed_all(win, fake, greeks=greeks, skip=skip)
            win._option_eval_step(now + 0.2)
            return now + 0.2
    raise AssertionError("the seed never committed")


# ---------------------------------------------------------------------------
# AC1 — ON populates both ladders with the owner's displayed values
# ---------------------------------------------------------------------------


def test_P23_T9_AC1_on_populates_both_ladders_negative_and_partial_legs(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake, skip=UNFED)

        # Eight rows: four per side. CCS reads 7360/7355/7350/7345; PCS reads
        # 7355/7350/7345/7340 (the per-side table's anchor is row 2 on PCS).
        assert win.option_spreads_panel.ccs_table.rowCount() == 4
        assert win.option_spreads_panel.pcs_table.rowCount() == 4

        for side, shorts, delta_text, gamma_text in (
            ("CCS", EXPECTED_SHORTS_CCS, "-0.020", "0.0004"),
            ("PCS", EXPECTED_SHORTS_PCS, "0.020", "-0.0004"),
        ):
            for index, short in enumerate(shorts):
                cells = _cells(win, side, index)
                assert cells[0].startswith("SPX "), cells
                if side == "CCS" and index == 0:
                    # 7380 never ticked: a partial leg shows no value.
                    assert cells[1:] == ["", "", "", ""], cells
                    continue
                ask, bid = _expected_display(short, side)
                assert cells[1] == ask, (side, index, cells)
                assert cells[2] == bid, (side, index, cells)
                assert cells[3] == delta_text, (side, index, cells)
                assert cells[4] == gamma_text, (side, index, cells)
                # A credit spread renders negative by design.
                assert float(cells[1]) < 0 and float(cells[2]) < 0

        # One chain lookup + one sec-def request, no polling/history while ON.
        assert len(fake.contract_details) == 1
        assert len(fake.sec_def) == 1
        assert fake.historical == []
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC1_launch_is_off_at_default_target(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        panel = win.option_spreads_panel
        assert panel.toggle_button.isChecked() is False
        assert panel._last_valid_target == pytest.approx(1.00)
        assert panel.target_edit.text() == "1.00"
        assert win._option_engine._target == pytest.approx(1.00)
        assert win._option_leg_req == {}
        assert win._option_spot_req_id is None
        assert fake.mkt_data == []
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC2 — registry, reqId stability, the 16-line budget, OFF, guard refusal
# ---------------------------------------------------------------------------


def test_P23_T9_AC2_registry_shared_legs_ordering_budget_and_off(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        assert OPTION_LEGS == "option_legs"
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        now = _settle(win, fake)

        assert win._option_engine.anchor("CCS") == 7350.0
        assert win._option_engine.anchor("PCS") == 7350.0
        # Every live option line is registered with the panel's tag, and each
        # carries both replay hooks.
        entries = win.sub_manager.entries_of_type(OPTION_LEGS)
        assert len(entries) == 16
        for req_id, _symbol in entries:
            entry = win.sub_manager._entries[req_id]
            assert entry.req_type == OPTION_LEGS
            assert entry.reissue is not None
            assert entry.rebind is not None
        # The ceiling, recorded at every subscribe/cancel step.
        assert max(option for option, _spot in fake.steps) <= 16
        assert max(option + spot for option, spot in fake.steps) <= 17

        before = fake.leg_reqs()
        cancel_floor = len(fake.cancels)
        event_floor = len(fake.events)

        # A Target change moves each anchor exactly one AC-D65.4 rung in its
        # decided direction: the 0.02/point curve puts T=1.20 on the *lower*
        # CCS strike (7345: bases 1.00/1.10/1.20) and the *higher* PCS strike
        # (7355: bases 1.00/1.10/1.20); 7350's bases are 0.90/1.00/1.10.
        edits: list[float] = []
        win.option_spreads_panel.target_committed.connect(edits.append)
        win.option_spreads_panel.target_edit.setText("1.20")
        win.option_spreads_panel.target_edit.editingFinished.emit()

        assert edits == [pytest.approx(1.20)]
        assert win._option_engine._target == pytest.approx(1.20)
        assert win._option_engine.anchor("CCS") == 7345.0
        assert win._option_engine.anchor("PCS") == 7355.0

        after = fake.leg_reqs()
        # Shared legs keep their original reqId (never cancelled + re-requested).
        # CCS 7350 -> 7345 keeps 7360 as a long and leaves 7380 for 7340. PCS
        # 7350 -> 7355 keeps seven legs -- including 7340, which moves from the
        # row-4 short to the row-1 long -- and swaps only its row-4 long 7320
        # for the new row-1 short 7360.
        for key in (("C", 7360.0), ("C", 7355.0), ("C", 7350.0), ("C", 7345.0),
                    ("C", 7375.0), ("C", 7370.0), ("C", 7365.0),
                    ("P", 7355.0), ("P", 7350.0), ("P", 7345.0), ("P", 7340.0),
                    ("P", 7335.0), ("P", 7330.0), ("P", 7325.0)):
            assert after[key] == before[key], key
        # Exactly one leg leaves and one arrives per side.
        assert ("C", 7380.0) not in after
        assert ("P", 7320.0) not in after
        assert before[("C", 7380.0)] in fake.cancels
        assert before[("P", 7320.0)] in fake.cancels
        assert after[("C", 7340.0)] not in before.values()
        assert after[("P", 7360.0)] not in before.values()
        # ... and each leaving leg was cancelled BEFORE its side's arrival.
        new_events = fake.events[event_floor:]
        leaving_index = next(
            i for i, (kind, _rid, _c) in enumerate(new_events)
            if kind == "cancel"
        )
        arriving_index = next(
            i for i, (kind, _rid, contract) in enumerate(new_events)
            if kind == "subscribe" and getattr(contract, "secType", "") == "OPT"
        )
        assert leaving_index < arriving_index
        assert max(option for option, _spot in fake.steps) <= 16
        assert len(fake.cancels) - cancel_floor == 2  # C7380 + P7320 only

        # A second evaluation moves nothing: both new anchors are matched (d=0).
        cancels_after_step = len(fake.cancels)
        win._option_eval_step(now + 1.0)
        assert win._option_engine.anchor("CCS") == 7345.0
        assert win._option_engine.anchor("PCS") == 7355.0
        assert fake.leg_reqs() == after
        assert len(fake.cancels) == cancels_after_step

        # OFF releases every option line and the spot line.
        win.option_spreads_panel.toggle_button.click()
        assert win.option_spreads_panel.toggle_button.isChecked() is False
        assert win._option_req_ids == {}
        assert win._option_leg_req == {}
        assert win._option_spot_req_id is None
        assert win.sub_manager.entries_of_type(OPTION_LEGS) == []
        assert fake.counts() == (0, 0)
        assert win._md_line_count() == 0
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[1:] == ["", "", "", ""]
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC2_budget_refusal_is_one_message_and_no_over_cap_subscribe(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        # Fill the engine's pool: 8 non-overlapping pairs = 16 distinct legs,
        # holding no live line at all.
        for index in range(8):
            short = 7000.0 + 40.0 * index
            assert win._option_engine._lease_pair(
                None, "CCS", short, short + 20.0, reason="manual")

        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        for index in range(40):
            win._option_eval_step(time.monotonic() + 1.0 + index * 0.5)

        refusals = log.matching("16 option lines")
        assert len(refusals) == 1, log.messages
        assert "capacity" in refusals[0]
        # No over-cap subscribe: the fake holds no option line at all.
        assert fake.live_of("OPT") == []
        assert win._option_req_ids == {}
        # The tail rows are empty rather than over-budget.
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[1:] == ["", "", "", ""]
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# ESC-117 — OFF is a clean pre-ON session; a same-session ON re-subscribes
# ---------------------------------------------------------------------------


def test_P23_T9_AC2_second_on_rebuilds_the_session_and_streams_fresh_values(
        monkeypatch, qapp):
    """ESC-117: OFF discards the engine's session, so ON re-subscribes afresh."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        assert len(win._option_engine.live_legs()) == 16
        before = _cells(win, "CCS", 2)
        assert before[1] != "" and before[2] != ""
        engine = win._option_engine

        # OFF returns the engine to a clean pre-ON session: no live legs, no
        # rows, no reqIds and no lines on the wire.
        win.option_spreads_panel.toggle_button.click()
        assert win.option_spreads_panel.toggle_button.isChecked() is False
        assert win._option_engine is engine  # the same engine, reset
        assert engine.live_legs() == set()
        assert engine.rows() == {}
        assert win._option_engine.live_legs() == set()
        assert win._option_leg_req == {}
        assert win._option_req_ids == {}
        assert win._option_spot_req_id is None
        assert win.sub_manager.entries_of_type(OPTION_LEGS) == []
        assert fake.counts() == (0, 0)
        assert win._md_line_count() == 0
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[1:] == ["", "", "", ""]

        # A same-session ON re-seeds and re-subscribes from scratch.
        event_floor = len(fake.events)
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        subscribes = {
            req_id
            for kind, req_id, contract in fake.events[event_floor:]
            if kind == "subscribe" and getattr(contract, "secType", "") == "OPT"
        }
        assert len(subscribes) >= 16, "the second ON issued no fresh leg lines"
        assert len(win._option_engine.live_legs()) == 16
        live = fake.live_of("OPT")
        assert len(live) == 16
        assert {req_id for req_id, _contract in live} <= subscribes, (
            "a live row is backed by a pre-OFF line")
        assert max(option for option, _spot in fake.steps) <= 16
        assert max(option + spot for option, spot in fake.steps) <= 17
        assert win._md_line_count() <= 17

        # Every row is backed by a live line: a changed bid reaches the cell
        # (a stale pre-OFF row would silently keep its old value).
        _feed_leg(win, fake, 7350.0, "C", bid=_price(7350.0, "C") + 0.05)
        qapp.processEvents()
        assert _cells(win, "CCS", 2)[1] == f"{-_credit(7350.0, 'CCS') + 0.05:.2f}"
        assert set(win._option_engine.stale_legs()) == set()
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC2_deferred_leg_retry_after_off_opens_no_line(
        monkeypatch, qapp):
    """A PacingExceeded retry queued before OFF opens nothing once OFF."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        real_req = win.md_manager.req_mkt_data
        attempted: list[tuple[str, float]] = []

        def _refuse(contract):
            if getattr(contract, "secType", "") == "OPT":
                attempted.append((str(contract.right), float(contract.strike)))
                raise PacingExceeded(0.3)
            return real_req(contract)

        win.md_manager.req_mkt_data = _refuse
        _toggle_on(win, fake)
        _deliver_chain(win, fake)  # the chain reply drives the first eval step

        assert attempted, "no leg subscribe reached the client"
        leg = LegKey(right=attempted[0][0], strike=attempted[0][1])
        # The pacing refusal deferred the line: the leg is still unbound, and
        # the engine still believes it holds a live line (the retry's premise).
        assert leg not in win._option_leg_req
        assert fake.live_of("OPT") == []
        assert leg in win._option_engine.live_legs()
        win.md_manager.req_mkt_data = real_req

        # OFF, then the queued QTimer.singleShot retry lands.
        win.option_spreads_panel.toggle_button.click()
        assert win.option_spreads_panel.toggle_button.isChecked() is False
        assert fake.live_of("OPT") == []
        win._option_subscribe_leg(leg)

        assert win._option_leg_req == {}
        assert fake.live_of("OPT") == []
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC3 — the replay include set, STALE freeze, one replay per leg
# ---------------------------------------------------------------------------


def test_P23_T9_AC3_replay_include_set_is_exactly_the_three_tags(monkeypatch, qapp):
    win, _fake = _make_window(monkeypatch, qapp)
    try:
        seen: dict[str, set] = {}

        def _record(include_types=None):
            seen["types"] = set(include_types or ())
            return []

        win.sub_manager.replay_all = _record
        win._replay_subscriptions()
        assert seen["types"] == {RT_BARS, S0_TICKS, OPTION_LEGS}
        # AC-D22.7.2's exclusion is untouched: option legs are never MARKET_DATA.
        assert MARKET_DATA not in seen["types"]
    finally:
        win.close()


def test_P23_T9_AC3_disconnect_marks_stale_freezes_and_replays_once(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        legs = set(win._option_engine.live_legs())
        assert len(legs) == 16
        anchors_before = {
            side: win._option_engine.anchor(side) for side in ("CCS", "PCS")
        }
        reqs_before = dict(fake.leg_reqs())
        cancels_before = len(fake.cancels)
        subscribe_before = len(fake.mkt_data)

        # ---- simulated drop ----
        win._on_disconnected()
        fake.drop_all()  # TWS killed the server-side lines; no local cancel
        assert win._option_engine.walk_frozen is True
        # Every live window leg is STALE (the engine also holds STALE quotes for
        # probe legs whose cells are no longer displayed).
        assert legs <= win._option_engine.stale_legs()
        assert len(log.matching("STALE")) == 1
        # Every cell of every populated row is marked STALE.
        for side in ("CCS", "PCS"):
            table = (win.option_spreads_panel.ccs_table if side == "CCS"
                     else win.option_spreads_panel.pcs_table)
            for index in range(4):
                for column in range(5):
                    assert table.item(index, column).toolTip() == "STALE"

        # No evaluation moves the ladder and nothing is cancelled.
        for index in range(5):
            win._option_eval_step(time.monotonic() + 100.0 + index)
        for side, anchor in anchors_before.items():
            assert win._option_engine.anchor(side) == anchor
        assert len(fake.cancels) == cancels_before

        # ---- reconnect: exactly one reqMktData per leg, no duplicate ----
        win._on_connected()
        assert win._option_engine.walk_frozen is False
        assert len(fake.mkt_data) - subscribe_before == 16
        assert len(fake.live_of("OPT")) == 16
        assert len(win.sub_manager.entries_of_type(OPTION_LEGS)) == 16
        assert len(set(fake.mkt_data[subscribe_before:])) == 16
        for side, anchor in anchors_before.items():
            assert win._option_engine.anchor(side) == anchor
        # Same anchor: the rebound line feeds the same leg's cell.
        rebound = fake.leg_reqs()
        assert rebound[("C", 7350.0)] != reqs_before[("C", 7350.0)]
        _feed_leg(win, fake, 7350.0, "C")
        qapp.processEvents()
        ask, bid = _expected_display(7350.0, "CCS")
        assert _cells(win, "CCS", 2)[1] == ask
        assert _cells(win, "CCS", 2)[2] == bid
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC4 — the spot chain's three tiers and the 16 + 1 ceiling
# ---------------------------------------------------------------------------


def test_P23_T9_AC4_tier_3a_chart_on_spx_with_price_opens_zero_spot_lines(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        win._current_symbol = "SPX"
        win._last_chart_price = SPOT
        _toggle_on(win, fake, spot=None)  # tier 3a: the chart's own price
        assert fake.live_of("IND") == []
        assert win._md_line_count() == 0
        assert win._option_engine._spot == pytest.approx(SPOT)

        _deliver_chain(win, fake)
        _settle(win, fake)
        assert fake.live_of("IND") == []
        assert max(option for option, _spot in fake.steps) <= 16
        assert max(option + spot for option, spot in fake.steps) <= 17
        ask, bid = _expected_display(7350.0, "CCS")
        assert _cells(win, "CCS", 2)[1] == ask
        assert _cells(win, "CCS", 2)[2] == bid
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC4_tier_3b_other_symbol_opens_exactly_one_counted_spot(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        # A live SPX TickerSession in the background is NOT a spot source.
        win._current_symbol = "AAPL"
        win.get_or_create_session("SPX").last_chart_price = SPOT
        _toggle_on(win, fake, spot=None)

        spots = fake.live_of("IND")
        assert len(spots) == 1
        spot_req = spots[0][0]
        assert win._md_line_count() == 1  # the one spot line is counted
        win.ib_client.bridge.tick_price.emit(spot_req, 4, 7351.0)
        assert win._option_engine._spot == pytest.approx(7351.0)

        _deliver_chain(win, fake)
        _settle(win, fake)
        # One line, never two; cancelled when the seed completes.
        assert win._option_spot_req_id is None
        assert spot_req in fake.cancels
        assert len(fake.live_of("OPT")) == 16  # 16 live legs, one spot ever
        assert win._md_line_count() == 16
        ask, bid = _expected_display(7350.0, "CCS")
        assert _cells(win, "CCS", 2)[1] == ask
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC4_tier_3c_refused_or_silent_spot_still_completes_seed(
        monkeypatch, qapp):
    for refused in (True, False):
        win, fake = _make_window(monkeypatch, qapp)
        try:
            log = _StatusLog(win)
            _toggle_on(win, fake, spot=None)
            spots = fake.live_of("IND")
            assert len(spots) == 1
            if refused:
                win._on_error(spots[0][0], 354, "not subscribed")
                assert win._option_spot_req_id is None
                assert not log.matching("Error [354]")

            _deliver_chain(win, fake)
            _settle(win, fake)
            assert win._option_spot_req_id is None
            # No spot, but the seed still completed with eight rows.
            assert win._option_engine.anchor("CCS") is not None
            assert _cells(win, "CCS", 2)[0].startswith("SPX ")
            assert max(option for option, _spot in fake.steps) <= 16
            assert max(option + spot for option, spot in fake.steps) <= 17
            assert fake.orders == []
        finally:
            win.close()


# ---------------------------------------------------------------------------
# AC5 — injected faults: one message each, the defined cell state
# ---------------------------------------------------------------------------


def test_P23_T9_AC5_greeks_absent_and_sentineled_leave_no_value(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake, greeks=False)
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[3] == ""
                assert _cells(win, side, index)[4] == ""

        # Sentineled greeks are screened exactly like absent ones.
        bridge = win.ib_client.bridge
        for _req_id, contract in fake.live_of("OPT"):
            bridge.option_computation.emit(
                _req_id, 13, float("nan"), float("nan"))
        qapp.processEvents()
        for side in ("CCS", "PCS"):
            assert _cells(win, side, 1)[3] == ""
            assert _cells(win, side, 1)[4] == ""
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC5_mixed_greek_sources_one_message_and_no_value(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake, greeks=False)

        bridge = win.ib_client.bridge
        short_req = fake.leg_req(7345.0, "C")
        long_req = fake.leg_req(7365.0, "C")
        bridge.option_computation.emit(short_req, 13, 0.30, 0.012)
        bridge.option_computation.emit(long_req, 12, 0.20, 0.008)
        qapp.processEvents()

        mixed = log.matching("different greek sources")
        assert len(mixed) == 1, log.messages
        assert _cells(win, "CCS", 3)[3] == ""
        assert _cells(win, "CCS", 3)[4] == ""
        # The other rows are untouched (no source covers them either).
        assert _cells(win, "CCS", 1)[1] != ""
    finally:
        win.close()


def test_P23_T9_AC5_rejected_leg_drops_the_pair_with_one_message(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        req_id = fake.leg_req(7360.0, "C")
        pair_long = fake.leg_req(7380.0, "C")
        win._on_error(req_id, 200, "No security definition")
        qapp.processEvents()

        dropped = log.matching("dropped for this session")
        assert len(dropped) == 1, log.messages
        assert _cells(win, "CCS", 0)[1:] == ["", "", "", ""]
        # Both lines of the dropped pair are released; no other line is.
        assert req_id in fake.cancels and pair_long in fake.cancels
        assert len(fake.live_of("OPT")) == 14
        # The generic status line is NOT used for an option-owned reqId.
        assert win.status_bar.currentMessage() != "Error [200]: No security definition"
        assert fake.orders == []
    finally:
        win.close()


@pytest.mark.parametrize("code", [10197, 354, 7777])
def test_P23_T9_AC5_blanking_codes_show_no_value_one_message(
        monkeypatch, qapp, code):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        req_id = fake.leg_req(7355.0, "C")
        win._on_error(req_id, code, "refused")
        qapp.processEvents()

        assert len(log.matching(f"TWS error {code}")) == 1, log.messages
        assert _cells(win, "CCS", 1)[1:] == ["", "", "", ""]
        # The line is kept (nothing re-seats, nothing is cancelled).
        assert req_id in fake.live
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC5_162_keeps_the_line_then_goes_stale(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        now = _settle(win, fake)

        req_id = fake.leg_req(7355.0, "C")
        win._on_error(req_id, 162, "Historical market data timeout")
        qapp.processEvents()
        leg = LegKey(right="C", strike=7355.0)
        assert win._option_engine.leg_stale(leg) is False
        assert len(log.matching("kept")) == 1
        # The row keeps its last value until the timeout elapses.
        ask, _bid = _expected_display(7355.0, "CCS")
        assert _cells(win, "CCS", 1)[1] == ask
        assert req_id in fake.live

        win._option_eval_step(now + 30.0)
        table = win.option_spreads_panel.ccs_table
        assert table.item(1, 1).toolTip() == "STALE"
        assert win._option_engine.leg_stale(leg) is True
        assert req_id in fake.live  # 162 never cancels
    finally:
        win.close()


def test_P23_T9_AC5_no_0dte_is_empty_with_zero_option_req_ids(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        _deliver_chain(win, fake, expirations=["20991231"])

        assert win._option_leg_req == {}
        assert fake.live_of("OPT") == []
        assert win._option_engine.rows() == {}
        assert not win.option_spreads_panel.empty_label.isHidden()
        assert win.option_spreads_panel.empty_label.text() == "No 0DTE expiry today"
        assert len(log.matching("No 0DTE SPXW expiry is listed today")) == 1
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[1:] == ["", "", "", ""]
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC5_post_1615_cutoff_state(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        win._option_et_now = lambda: datetime(2026, 11, 17, 16, 20)
        win.option_spreads_panel.toggle_button.click()

        assert win._option_active is True
        assert fake.mkt_data == []  # no chain, no legs, no spot
        assert fake.sec_def == []
        assert win._md_line_count() == 0
        status = win.option_spreads_panel.status_label.text()
        assert "16:15 ET" in status
        assert win.option_spreads_panel.empty_label.text() == (
            "0DTE chain closed (after 16:15 ET)")
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[1:] == ["", "", "", ""]
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC5_cutoff_discards_the_session_and_blocks_deferred_lines(
        monkeypatch, qapp):
    """Crossing 16:15 ET clears the session exactly like OFF (ESC-117)."""
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)
        assert len(win._option_engine.live_legs()) == 16
        engine = win._option_engine

        # The live session crosses the cutoff while the panel stays ON.
        win._option_et_now = lambda: datetime(2026, 11, 17, 16, 20)
        win._option_eval_step(time.monotonic() + 1.0)

        assert win._option_cutoff is True
        assert win._option_engine is engine
        assert engine.live_legs() == set()
        assert win._option_engine.live_legs() == set()
        assert win._option_engine.rows() == {}
        assert win._option_leg_req == {}
        assert win._option_req_ids == {}
        assert win._option_spot_req_id is None
        assert fake.counts() == (0, 0)
        assert win._md_line_count() == 0
        for side in ("CCS", "PCS"):
            for index in range(4):
                assert _cells(win, side, index)[1:] == ["", "", "", ""]

        # Neither a deferred leg retry nor the spot tier may open a line.
        win._option_subscribe_leg(LegKey(right="C", strike=7360.0))
        win._option_ensure_spot()
        assert win._option_leg_req == {}
        assert fake.counts() == (0, 0)
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC5_non_option_reqid_keeps_the_generic_line(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        shown: list[str] = []
        win.status_bar.showMessage = lambda text, *a, **k: shown.append(str(text))
        win._on_error(424242, 200, "No security definition")

        assert any("Error [200]: No security definition" in line
                   for line in shown), shown
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# AC6 — the Target field, collapse, restart, coalescing, zero orders
# ---------------------------------------------------------------------------


def test_P23_T9_AC6_rejected_target_changes_nothing_accepted_edit_moves_once(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        panel = win.option_spreads_panel
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        edits: list[float] = []
        panel.target_committed.connect(edits.append)
        anchors = {side: win._option_engine.anchor(side) for side in ("CCS", "PCS")}
        reqs = dict(fake.leg_reqs())
        cancels = len(fake.cancels)

        # A rejected Target changes no anchor and no line.
        panel.target_edit.setText("99.00")
        panel.target_edit.editingFinished.emit()
        assert edits == []
        assert win._option_engine._target == pytest.approx(1.00)
        assert {side: win._option_engine.anchor(side)
                for side in ("CCS", "PCS")} == anchors
        assert fake.leg_reqs() == reqs
        assert len(fake.cancels) == cancels
        assert panel.target_edit.text() == "1.00"
        assert "Target must be between" in panel.status_label.text()

        # An accepted edit emits once and re-evaluates immediately. T=1.20 is
        # outside 7350's three credit bases [0.90, 1.00, 1.10] but on the lower
        # CCS strike's ask basis (7345: 1.00/1.10/1.20) and the higher PCS
        # strike's ask basis (7355: 1.00/1.10/1.20) -> one rung each, opposite
        # strike directions.
        panel.target_edit.setText("1.20")
        panel.target_edit.editingFinished.emit()
        assert edits == [pytest.approx(1.20)]
        assert win._option_engine._target == pytest.approx(1.20)
        assert win._option_engine.anchor("CCS") == 7345.0
        assert win._option_engine.anchor("PCS") == 7355.0
        assert fake.leg_reqs()[("C", 7345.0)] == reqs[("C", 7345.0)]
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC6_collapse_while_on_keeps_streaming(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        panel = win.option_spreads_panel
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        panel.header_button.setChecked(False)
        assert panel.is_collapsed() is True
        before = win._option_refresh_count
        win._option_eval_timer.stop()  # isolate the coalesced tick refresh
        # A changed bid on one leg still flows to the hidden tables.
        _feed_leg(win, fake, 7345.0, "C", bid=_price(7345.0, "C") + 0.05)
        qapp.processEvents()

        assert win._option_refresh_count > before
        assert _cells(win, "CCS", 3)[1] == f"{-_credit(7345.0, 'CCS') + 0.05:.2f}"
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC6_burst_coalesces_to_one_refresh_per_turn(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)
        win._option_eval_timer.stop()
        qapp.processEvents()

        before = win._option_refresh_count
        bridge = win.ib_client.bridge
        for strike in (7360.0, 7355.0, 7350.0, 7345.0):
            req_id = fake.leg_req(strike, "C")
            for _ in range(5):
                bridge.tick_price.emit(req_id, 1, _price(strike, "C"))
                bridge.tick_price.emit(req_id, 2, _price(strike, "C") + 0.10)
        qapp.processEvents()

        assert win._option_refresh_count == before + 1
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC6_restart_launches_off_at_target_1_with_zero_lines(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        assert win.option_spreads_panel.toggle_button.isChecked() is False
        assert win.option_spreads_panel._last_valid_target == pytest.approx(1.00)
        assert win.option_spreads_panel.target_edit.text() == "1.00"
        assert win._option_req_ids == {}
        assert win._option_spot_req_id is None
        assert fake.mkt_data == []
        assert fake.sec_def == []
        assert fake.orders == []
    finally:
        win.close()


def test_P23_T9_AC6_no_order_call_in_any_state(monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)
        req_id = fake.leg_req(7360.0, "C")
        win._on_error(req_id, 200, "rejected")
        win.option_spreads_panel.toggle_button.click()  # OFF
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# ESC-119 — the engine owns the reset: OFF and the 16:15 cutoff never re-init
# ---------------------------------------------------------------------------


def _counting_init(monkeypatch):
    """Count every SpreadEngine construction from here on (must stay 0)."""
    from services.option_spread_engine import SpreadEngine

    calls: list[object] = []
    real_init = SpreadEngine.__init__

    def counting_init(self, *args, **kwargs):
        calls.append(self)
        return real_init(self, *args, **kwargs)

    monkeypatch.setattr(SpreadEngine, "__init__", counting_init)
    return calls


def _assert_empty_engine(engine, *, clock, target, live):
    """AC1's empty-session state on the live engine, clock and Target intact."""
    assert engine.live_legs() == set()
    assert engine.rows() == {}
    assert all(engine._req_ids.get(item) is None for item in live)
    assert engine.anchor("CCS") is None and engine.anchor("PCS") is None
    assert engine.seed_state().active is False
    assert engine.walk_frozen is False
    assert engine.stale_legs() == set()
    assert engine.take_messages() == []
    assert sorted(engine._latched) == []
    assert engine._target == target
    assert engine._clock is clock


def test_P23_T16_AC3_off_and_cutoff_empty_the_live_engine_without_reinit(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        engine = win._option_engine
        live = set(engine.live_legs())
        assert len(live) == 16
        bound = sorted(live, key=lambda key: (key.right, key.strike))[0]
        engine.rebind_leg(bound, 7777)
        assert engine._req_ids.get(bound) == 7777
        win._option_engine.set_target(2.00)
        clock = lambda: 424242.0
        engine._clock = clock

        calls = _counting_init(monkeypatch)
        win.option_spreads_panel.toggle_button.click()  # OFF

        assert win.option_spreads_panel.toggle_button.isChecked() is False
        assert calls == []
        assert win._option_engine is engine
        _assert_empty_engine(engine, clock=clock, target=2.00, live=live)
        assert win._option_leg_req == {}
        assert win._option_req_ids == {}
        assert win._option_spot_req_id is None
        assert fake.counts() == (0, 0)
        assert win._md_line_count() == 0
        assert fake.orders == []
    finally:
        win.close()

    # The cutoff path on a freshly opened live window: the same empty session
    # through reset_session(), the same instance, no further __init__.
    win2, fake2 = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win2, fake2)
        _deliver_chain(win2, fake2)
        _settle(win2, fake2)

        engine2 = win2._option_engine
        live2 = set(engine2.live_legs())
        assert len(live2) == 16
        bound2 = sorted(live2, key=lambda key: (key.right, key.strike))[0]
        engine2.rebind_leg(bound2, 7778)
        assert engine2._req_ids.get(bound2) == 7778
        win2._option_engine.set_target(2.00)
        clock2 = lambda: 515151.0
        engine2._clock = clock2

        calls.clear()
        win2._option_enter_cutoff()

        assert win2._option_cutoff is True
        assert calls == []
        assert win2._option_engine is engine2
        _assert_empty_engine(engine2, clock=clock2, target=2.00, live=live2)
        assert win2._option_leg_req == {}
        assert win2._option_req_ids == {}
        assert win2._option_spot_req_id is None
        assert fake2.counts() == (0, 0)
        assert win2._md_line_count() == 0
        assert fake2.orders == []
    finally:
        win2.close()


# ---------------------------------------------------------------------------
# P23-T25 — the fixture's credit curves are faithful to the approved rule
# ---------------------------------------------------------------------------


def test_P23_T25_AC1_pair_mids_fall_rise_and_seed_at_7350(monkeypatch, qapp):
    """CCS mid falls / PCS mid rises 0.02 per point; one rung moves d by 0.10.

    At T = 1.00 the seeded anchor is 7350 on both sides. A single 5-point rung
    moves the pair's credit mid by 0.10 — twice h = 0.05 — so AC-D65.4's strict
    "more than h" rule can actually step on this feed.
    """
    win, fake = _make_window(monkeypatch, qapp)
    try:
        _toggle_on(win, fake)
        _deliver_chain(win, fake)
        _settle(win, fake)

        engine = win._option_engine
        assert engine.anchor("CCS") == 7350.0
        assert engine.anchor("PCS") == 7350.0
        assert match_band(1.00) == pytest.approx(0.05)

        ccs_7350 = engine._score_pair_complete("CCS", 7350.0, 7370.0)
        ccs_7345 = engine._score_pair_complete("CCS", 7345.0, 7365.0)
        pcs_7350 = engine._score_pair_complete("PCS", 7350.0, 7330.0)
        pcs_7355 = engine._score_pair_complete("PCS", 7355.0, 7335.0)
        for score in (ccs_7350, ccs_7345, pcs_7350, pcs_7355):
            assert score is not None

        assert ccs_7350.credit_mid == pytest.approx(1.00)
        assert ccs_7345.credit_mid == pytest.approx(1.10)
        assert pcs_7350.credit_mid == pytest.approx(1.00)
        assert pcs_7355.credit_mid == pytest.approx(1.10)

        # One rung moves the mid by 0.10, which is strictly more than the band,
        # in the decided direction on each side (CCS down, PCS up).
        assert ccs_7345.credit_mid - ccs_7350.credit_mid == pytest.approx(0.10)
        assert pcs_7355.credit_mid - pcs_7350.credit_mid == pytest.approx(0.10)
        assert abs(ccs_7345.credit_mid - ccs_7350.credit_mid) > match_band(1.00)
        assert abs(pcs_7355.credit_mid - pcs_7350.credit_mid) > match_band(1.00)

        # The three credit bases bracket the mid by one tick each way.
        for score in (ccs_7350, ccs_7345, pcs_7350, pcs_7355):
            assert score.credit_bid == pytest.approx(score.credit_mid - 0.10)
            assert score.credit_ask == pytest.approx(score.credit_mid + 0.10)

        # Every displayed cell is computed from those mids. The anchor row on
        # each side: PCS 7350 is row index 1 (display row 2, the anchor of the
        # per-side table's +5/0/-5/-10), CCS 7350 is row index 2 (row 3 of
        # +10/+5/0/-5); the rung above each anchor carries the same values.
        for side, index, short in (
            ("CCS", 2, 7350.0), ("CCS", 3, 7345.0),
            ("PCS", 1, 7350.0), ("PCS", 0, 7355.0),
        ):
            ask, bid = _expected_display(short, side)
            cells = _cells(win, side, index)
            assert cells[1] == ask, (side, index, cells)
            assert cells[2] == bid, (side, index, cells)
            assert float(cells[1]) < 0 and float(cells[2]) < 0
        assert _cells(win, "PCS", 1)[0].endswith("7350/7330")
        assert _cells(win, "CCS", 2)[0].endswith("7350/7370")
        assert fake.orders == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# Q-74 — a refused chain request is not an empty expiry, and it leaves evidence
# ---------------------------------------------------------------------------


def _resolve_lookup_and_issue_chain(win, fake) -> int:
    """Answer only the SPX contract lookup; return the chain request's reqId."""
    assert fake.contract_details, "the SPX index lookup was never issued"
    lookup_id = fake.contract_details[-1]
    bridge = win.ib_client.bridge
    bridge.contract_details.emit(
        lookup_id, SimpleNamespace(contract=SimpleNamespace(conId=12345)))
    bridge.contract_details_end.emit(lookup_id)
    assert fake.sec_def, "reqSecDefOptParams was never issued"
    return fake.sec_def[-1][0]


def test_Q74_chain_error_surfaces_code_and_never_claims_no_0dte(
        monkeypatch, qapp, caplog):
    from ui.main_window import (
        OPTION_CHAIN_FAILED_EMPTY_STATE,
        OPTION_CHAIN_FAILED_MESSAGE,
        OPTION_NO_0DTE_TEXT,
    )

    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)
        _toggle_on(win, fake)
        chain_id = _resolve_lookup_and_issue_chain(win, fake)

        with caplog.at_level(logging.WARNING, logger="ui.main_window"):
            win._on_error(chain_id, 354, "not subscribed")
            qapp.processEvents()
            # The cadence keeps turning; its "no series yet" read must not
            # relabel the failure as the factual no-0DTE claim.
            win._option_eval_step(time.monotonic() + 1.0)
            qapp.processEvents()

        # The status line names the IB error code — the only evidence a
        # terminal run leaves behind.
        assert log.matching(OPTION_CHAIN_FAILED_MESSAGE.format(code=354)), (
            log.messages)
        assert len(log.matching("failed (code 354)")) == 1, log.messages
        # Never the empty-expiry claim, in either the status or the label.
        assert not log.matching("No 0DTE SPXW expiry is listed today"), (
            log.messages)
        assert win.option_spreads_panel.empty_label.text() == (
            OPTION_CHAIN_FAILED_EMPTY_STATE)
        assert win.option_spreads_panel.empty_label.text() != OPTION_NO_0DTE_TEXT

        # Exactly one warning, carrying reqId, code and error string.
        warnings = [
            record.getMessage() for record in caplog.records
            if "0DTE SPXW chain request" in record.getMessage()
        ]
        assert len(warnings) == 1, warnings
        assert str(chain_id) in warnings[0]
        assert "354" in warnings[0]
        assert "not subscribed" in warnings[0]
        assert fake.orders == []
    finally:
        win.close()


def test_Q74_chain_failed_names_each_cause_and_never_says_refused(
        monkeypatch, qapp):
    from ui.main_window import (
        OPTION_CHAIN_NOT_CONNECTED_EMPTY_STATE,
        OPTION_CHAIN_UNKNOWN_INDEX_EMPTY_STATE,
        OPTION_NO_0DTE_TEXT,
    )

    win, fake = _make_window(monkeypatch, qapp)
    try:
        log = _StatusLog(win)

        win._option_chain_failed("not connected")
        assert log.messages[-1] == (
            "Not connected to TWS, so the 0DTE SPXW chain was not requested; "
            "the ladders are empty."
        )
        assert "refused" not in log.messages[-1].lower()
        assert win.option_spreads_panel.empty_label.text() == (
            OPTION_CHAIN_NOT_CONNECTED_EMPTY_STATE)
        assert win.option_spreads_panel.empty_label.text() != OPTION_NO_0DTE_TEXT

        win._option_chain_failed("unknown index")
        assert log.messages[-1] == (
            "The SPX index contract is unknown, so the 0DTE SPXW chain was "
            "not requested; the ladders are empty."
        )
        assert win.option_spreads_panel.empty_label.text() == (
            OPTION_CHAIN_UNKNOWN_INDEX_EMPTY_STATE)
        assert (win.option_spreads_panel.empty_label.text()
                != OPTION_CHAIN_NOT_CONNECTED_EMPTY_STATE)
        assert fake.orders == []
    finally:
        win.close()


def test_Q74_chain_error_never_overwrites_the_post_1615_cutoff(
        monkeypatch, qapp):
    win, fake = _make_window(monkeypatch, qapp)
    try:
        win._option_et_now = lambda: datetime(2026, 11, 17, 16, 20)
        win.option_spreads_panel.toggle_button.click()

        cutoff = win.option_spreads_panel.status_label.text()
        assert "16:15 ET" in cutoff
        assert win.option_spreads_panel.empty_label.text() == (
            "0DTE chain closed (after 16:15 ET)")

        # A late discovery failure must leave the cutoff state alone.
        win._option_chain_failed("not connected")
        assert win.option_spreads_panel.status_label.text() == cutoff
        assert win.option_spreads_panel.empty_label.text() == (
            "0DTE chain closed (after 16:15 ET)")
        assert fake.orders == []
    finally:
        win.close()
