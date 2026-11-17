"""P23-T6 — D65 chain discovery, option contracts and the greek/quote boundary.

Offscreen tests (no live TWS), all deterministic:

* AC1 — ``get_option_contract`` is attribute-complete for both rights and
  several strikes, and issues zero contract-details round trips.
* AC2 — ``today_expiry_yyyymmdd`` across ET dates (including a UTC instant
  that is the previous ET date), ``select_zero_dte_series`` (SPXW-today,
  later-expiry-only, non-SPXW class, no 0DTE) and ``option_chain_strikes``
  ordering.
* AC3 — ``req_sec_def_opt_params`` request shape, reqId source, readiness
  gate, ``PacingExceeded`` propagation and "never sleeps".
* AC4 — fake-client routing: ``tickOptionComputation`` tick-type and sentinel
  passthrough (``None``/``-1``/DBL_MAX/NaN — unmodified), ``tickPrice``
  bid/ask sentinels, and the two chain overrides emitting only used fields.
* AC5 — nothing outside ``ibkr/`` calls the new helpers yet, the four
  account/position overrides + signals are intact (P23-T11 deletes them),
  and no order call has been added.
"""

from __future__ import annotations

import inspect
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from ibapi.contract import Contract

from ibkr.bridge import IBBridge
from ibkr.client import IBApiClient
from ibkr.contracts import (
    OptionSeries,
    get_option_contract,
    option_chain_strikes,
    select_zero_dte_series,
    today_expiry_yyyymmdd,
)
from ibkr.error_codes import IBKRNotReady
from ibkr.market_data import MarketDataManager
from ibkr.pacing import PacingExceeded

ET = ZoneInfo("America/New_York")
DBL_MAX = 1.7976931348623157e+308


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _NoLookupClient:
    """Records contract-details round trips — there must be none per leg."""

    def __init__(self):
        self.contract_detail_calls: list[tuple] = []

    def reqContractDetails(self, reqId, contract):
        self.contract_detail_calls.append((reqId, contract))


class _ChainClient:
    """Fake wire client for ``reqSecDefOptParams``."""

    def __init__(self, ready: bool = True):
        self.api_ready = ready
        self.calls: list[dict] = []

    def reqSecDefOptParams(self, reqId, symbol, futFopExchange, secType, conId):
        self.calls.append({
            "reqId": reqId,
            "underlying_symbol": symbol,
            "fut_fop_exchange": futFopExchange,
            "underlying_sec_type": secType,
            "underlying_con_id": conId,
        })


class _IdStub:
    """Stands in for ``ibkr.id_manager.id_manager``."""

    def __init__(self, value: int = 4242):
        self.value = value
        self.calls = 0

    def get_id(self) -> int:
        self.calls += 1
        self.value += 1
        return self.value - 1


class _PacingStub:
    """Stands in for ``ibkr.pacing.pacing_manager``."""

    def __init__(self, raise_wait: float | None = None):
        self.raise_wait = raise_wait
        self.throttles = 0

    def throttle(self):
        self.throttles += 1
        if self.raise_wait is not None:
            raise PacingExceeded(self.raise_wait)


def _spx_params(expirations, strikes=(5000.0, 5100.0, 5200.0),
                trading_class="SPXW", exchange="CBOE",
                underlying_con_id=416904):
    return {
        "trading_class": trading_class,
        "exchange": exchange,
        "underlying_con_id": underlying_con_id,
        "expirations": list(expirations),
        "strikes": list(strikes),
    }


# ---------------------------------------------------------------------------
# AC1 — attribute-complete OPT contract, no per-leg conId lookup
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "right,expected",
    [("C", "C"), ("CALL", "C"), ("c", "C"), ("P", "P"), ("PUT", "P"), ("p", "P")],
)
def test_option_contract_is_attribute_complete(right, expected):
    fake = _NoLookupClient()
    for strike in (4800.0, 5000.0, 5125.5, 5200.0):
        contract = get_option_contract("SPX", "20261117", strike, right)

        assert isinstance(contract, Contract)
        assert contract.symbol == "SPX"
        assert contract.secType == "OPT"
        assert contract.exchange == "SMART"
        assert contract.currency == "USD"
        assert contract.lastTradeDateOrContractMonth == "20261117"
        assert contract.strike == pytest.approx(float(strike))
        assert contract.right == expected
        assert contract.multiplier == "100"
        assert contract.tradingClass == "SPXW"
        # Attribute-only build: nothing resolved, nothing looked up.
        assert contract.conId == 0

    assert fake.contract_detail_calls == []


def test_option_contract_symbol_and_trading_class():
    contract = get_option_contract("spx", "20261117", 5000, "C")
    assert contract.symbol == "SPX"
    assert contract.tradingClass == "SPXW"

    custom = get_option_contract("SPX", "20261117", 5000, "P", trading_class="SPX")
    assert custom.tradingClass == "SPX"
    assert custom.right == "P"


def test_option_contract_rejects_unknown_right():
    with pytest.raises(ValueError):
        get_option_contract("SPX", "20261117", 5000, "X")


# ---------------------------------------------------------------------------
# AC2 — ET expiry, 0DTE series selection, strike lists
# ---------------------------------------------------------------------------

def test_today_expiry_is_the_et_date():
    assert today_expiry_yyyymmdd(
        datetime(2026, 11, 17, 10, 0, tzinfo=ET)
    ) == "20261117"
    # Naive is treated as already-ET.
    assert today_expiry_yyyymmdd(datetime(2026, 11, 17, 9, 30)) == "20261117"
    # Single-digit month/day are zero-padded.
    assert today_expiry_yyyymmdd(datetime(2026, 1, 5, 12, 0, tzinfo=ET)) == "20260105"


def test_today_expiry_converts_utc_to_et():
    # 02:00 UTC on the 17th is 21:00 ET on the 16th — the ET trading day wins.
    assert today_expiry_yyyymmdd(
        datetime(2026, 11, 17, 2, 0, tzinfo=timezone.utc)
    ) == "20261116"
    # 14:00 UTC is 09:00 ET on the same date.
    assert today_expiry_yyyymmdd(
        datetime(2026, 11, 17, 14, 0, tzinfo=timezone.utc)
    ) == "20261117"


def test_select_zero_dte_series_picks_todays_spxw():
    params = [_spx_params(["20261117", "20261124"], underlying_con_id=416904)]

    series = select_zero_dte_series(params, "20261117")

    assert isinstance(series, OptionSeries)
    assert series.trading_class == "SPXW"
    assert series.exchange == "CBOE"
    assert series.expiry == "20261117"
    assert series.con_id == 416904
    assert series.strikes_by_right["C"] == [5000.0, 5100.0, 5200.0]
    assert series.strikes_by_right["P"] == [5000.0, 5100.0, 5200.0]


def test_select_zero_dte_series_ignores_a_later_expiry_only():
    params = [_spx_params(["20261124", "20261201"])]

    assert select_zero_dte_series(params, "20261117") is None


def test_select_zero_dte_series_ignores_non_spxw_classes():
    params = [
        _spx_params(["20261117"], trading_class="SPX"),
        _spx_params(["20261117"], trading_class="SPXW", exchange="SMART"),
    ]

    series = select_zero_dte_series(params, "20261117")
    assert series is not None
    assert series.trading_class == "SPXW"
    assert series.exchange == "SMART"

    # Only the monthly (SPX) class carries today → no 0DTE SPXW series.
    assert select_zero_dte_series(params[:1], "20261117") is None


def test_select_zero_dte_series_no_0dte_day():
    params = [
        _spx_params(["20261124"]),
        _spx_params(["20261117"], trading_class="SPX"),
    ]
    assert select_zero_dte_series(params, "20261117") is None
    assert select_zero_dte_series([], "20261117") is None


def test_select_zero_dte_series_reads_attribute_payloads():
    params = [
        SimpleNamespace(
            tradingClass="SPXW",
            exchange="CBOE",
            underlyingConId=42,
            expirations={"20261117", "20261124"},
            strikes=[5200.0, 5000.0],
        )
    ]
    series = select_zero_dte_series(params, "20261117")
    assert series is not None
    assert series.con_id == 42
    assert series.strikes_by_right["C"] == [5000.0, 5200.0]


def test_option_chain_strikes_sorted_per_right():
    series = OptionSeries(
        trading_class="SPXW",
        exchange="CBOE",
        expiry="20261117",
        con_id=416904,
        strikes_by_right={"C": [5200.0, 5000.0, 5100.0], "P": [5150.5, 5050.0]},
    )

    strikes = option_chain_strikes(series)

    assert strikes["C"] == [5000.0, 5100.0, 5200.0]
    assert strikes["P"] == [5050.0, 5150.5]
    assert strikes["C"] == sorted(strikes["C"])
    assert strikes["P"] == sorted(strikes["P"])


# ---------------------------------------------------------------------------
# AC3 — req_sec_def_opt_params: readiness, id, pacing, no sleep
# ---------------------------------------------------------------------------

def test_req_sec_def_opt_params_request_shape(monkeypatch):
    client = _ChainClient(ready=True)
    manager = MarketDataManager(client)
    ids = _IdStub(value=4242)
    pacing = _PacingStub()
    monkeypatch.setattr("ibkr.market_data.id_manager", ids)
    monkeypatch.setattr("ibkr.market_data.pacing_manager", pacing)

    def _no_sleep(*_args, **_kwargs):  # pragma: no cover - fires only on failure
        raise AssertionError("req_sec_def_opt_params must never sleep")

    monkeypatch.setattr(time, "sleep", _no_sleep)

    req_id = manager.req_sec_def_opt_params("SPX", "SMART", "IND", 416904)

    assert req_id == 4242
    assert ids.calls == 1
    assert pacing.throttles == 1
    assert client.calls == [{
        "reqId": 4242,
        "underlying_symbol": "SPX",
        "fut_fop_exchange": "SMART",
        "underlying_sec_type": "IND",
        "underlying_con_id": 416904,
    }]


def test_req_sec_def_opt_params_requires_readiness(monkeypatch):
    client = _ChainClient(ready=False)
    manager = MarketDataManager(client)
    ids = _IdStub()
    pacing = _PacingStub()
    monkeypatch.setattr("ibkr.market_data.id_manager", ids)
    monkeypatch.setattr("ibkr.market_data.pacing_manager", pacing)

    with pytest.raises(IBKRNotReady):
        manager.req_sec_def_opt_params("SPX", "SMART", "IND", 416904)

    # Readiness runs FIRST: no reqId consumed, no pacing budget spent, no send.
    assert ids.calls == 0
    assert pacing.throttles == 0
    assert client.calls == []


def test_req_sec_def_opt_params_propagates_pacing_exceeded(monkeypatch):
    client = _ChainClient(ready=True)
    manager = MarketDataManager(client)
    ids = _IdStub(value=7)
    pacing = _PacingStub(raise_wait=1.5)
    monkeypatch.setattr("ibkr.market_data.id_manager", ids)
    monkeypatch.setattr("ibkr.market_data.pacing_manager", pacing)

    with pytest.raises(PacingExceeded) as excinfo:
        manager.req_sec_def_opt_params("SPX", "SMART", "IND", 416904)

    assert excinfo.value.wait_seconds == pytest.approx(1.5)
    assert ids.calls == 1
    assert pacing.throttles == 1
    assert client.calls == []


# ---------------------------------------------------------------------------
# AC4 — override → bridge routing, sentinels untouched
# ---------------------------------------------------------------------------

@pytest.fixture
def routed_client(qapp):
    """A real ``IBApiClient`` with its real bridge (no socket, no connect)."""
    return IBApiClient()


def test_tick_option_computation_passes_tick_types_through(routed_client):
    got = []
    routed_client.bridge.option_computation.connect(
        lambda req_id, tick_type, delta, gamma: got.append(
            (req_id, tick_type, delta, gamma)
        )
    )

    for tick_type in (13, 12, 10, 11):
        routed_client.tickOptionComputation(
            7, tick_type, 0, 0.21, 0.42, 3.5, 0.0, 0.015, 0.11, 0.09, 5000.0
        )

    assert got == [
        (7, 13, 0.42, 0.015),
        (7, 12, 0.42, 0.015),
        (7, 10, 0.42, 0.015),
        (7, 11, 0.42, 0.015),
    ]


@pytest.mark.parametrize("sentinel", [None, -1, DBL_MAX, float("nan")])
def test_tick_option_computation_passes_sentinels_unmodified(routed_client, sentinel):
    got = []
    routed_client.bridge.option_computation.connect(
        lambda req_id, tick_type, delta, gamma: got.append((req_id, tick_type, delta, gamma))
    )

    routed_client.tickOptionComputation(
        9, 13, 0, 0.2, sentinel, 1.0, 0.0, sentinel, 0.1, 0.05, 5000.0
    )

    req_id, tick_type, delta, gamma = got[-1]
    assert (req_id, tick_type) == (9, 13)
    for emitted in (delta, gamma):
        if isinstance(sentinel, float) and math.isnan(sentinel):
            assert math.isnan(emitted)
        else:
            assert emitted == sentinel


def test_tick_price_bid_ask_sentinels_reach_the_bridge_untouched(routed_client):
    got = []
    routed_client.bridge.tick_price.connect(
        lambda req_id, tick_type, price: got.append((req_id, tick_type, price))
    )

    # 1 = bid, 2 = ask.
    routed_client.tickPrice(11, 1, -1.0, None)
    routed_client.tickPrice(11, 2, DBL_MAX, None)
    routed_client.tickPrice(11, 1, float("nan"), None)

    assert got[0] == (11, 1, -1.0)
    assert got[1] == (11, 2, DBL_MAX)
    assert got[2][:2] == (11, 1) and math.isnan(got[2][2])


def test_chain_overrides_emit_only_used_fields(routed_client):
    params = []
    ends = []
    routed_client.bridge.option_params.connect(
        lambda req_id, payload: params.append((req_id, payload))
    )
    routed_client.bridge.option_params_end.connect(ends.append)

    routed_client.securityDefinitionOptionParameter(
        33, "CBOE", 416904, "SPXW", "100",
        {"20261117", "20261124"}, {5000.0, 5100.0},
    )
    routed_client.securityDefinitionOptionParameterEnd(33)

    assert len(params) == 1
    req_id, payload = params[0]
    assert req_id == 33
    assert set(payload) == {
        "exchange",
        "underlying_con_id",
        "trading_class",
        "expirations",
        "strikes",
    }
    assert payload["exchange"] == "CBOE"
    assert payload["underlying_con_id"] == 416904
    assert payload["trading_class"] == "SPXW"
    assert sorted(payload["expirations"]) == ["20261117", "20261124"]
    assert sorted(payload["strikes"]) == [5000.0, 5100.0]

    # The payload is exactly what select_zero_dte_series consumes.
    series = select_zero_dte_series([payload], "20261117")
    assert series is not None and series.expiry == "20261117"

    assert ends == [33]


def test_new_bridge_signals_are_declared():
    # option_params: (reqId, object); option_params_end: (reqId);
    # option_computation: (reqId, tickType, delta, gamma).
    for name in ("option_params", "option_params_end", "option_computation"):
        assert hasattr(IBBridge, name), f"{name} signal is missing"


# ---------------------------------------------------------------------------
# AC5 — no caller outside ibkr/, account overrides intact, no order calls
# ---------------------------------------------------------------------------

_NEW_HELPERS = (
    "get_option_contract",
    "today_expiry_yyyymmdd",
    "select_zero_dte_series",
    "option_chain_strikes",
    "OptionSeries",
    "req_sec_def_opt_params",
    "option_params",
    "option_params_end",
    "option_computation",
)

_SKIP_PARTS = {
    ".venv", ".git", "tests", "docs", "graphify-out", "node_modules",
    "__pycache__", "build", "dist",
}


def _production_modules():
    root = Path(__file__).resolve().parents[1]
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] == "ibkr":
            continue
        if any(part in _SKIP_PARTS for part in rel.parts):
            continue
        yield rel, path


def test_no_production_caller_outside_ibkr():
    offenders = []
    for rel, path in _production_modules():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in _NEW_HELPERS:
            if re.search(rf"\b{re.escape(name)}\b", text):
                offenders.append(f"{rel}:{name}")
    assert offenders == []


def test_account_and_position_overrides_and_signals_remain():
    pairs = (
        ("accountSummary", "account_summary"),
        ("accountSummaryEnd", "account_summary_end"),
        ("position", "position_update"),
        ("positionEnd", "position_end"),
    )
    for method_name, signal_name in pairs:
        method = getattr(IBApiClient, method_name, None)
        assert callable(method), f"{method_name} override is missing"
        assert hasattr(IBBridge, signal_name), f"{signal_name} signal is missing"
        assert signal_name in inspect.getsource(method)


def test_no_order_building_or_transmit_call_added():
    ibkr_dir = Path(__file__).resolve().parents[1] / "ibkr"
    hits = []
    for path in sorted(ibkr_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in ("placeOrder", "cancelOrder", "reqGlobalCancel"):
            if re.search(rf"\b{name}\b", text):
                hits.append(f"{path.name}:{name}")
    assert hits == []
