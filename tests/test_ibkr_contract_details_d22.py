"""D22 Phase 2 — IBKR contract-details request/callback plumbing.

New path added by this task, mirroring the historical-data plumbing:

    IBApiClient.contractDetails(reqId, contractDetails)
        -> super().contractDetails(...)
        -> bridge.contract_details.emit(reqId, contractDetails)
    IBApiClient.contractDetailsEnd(reqId)
        -> super().contractDetailsEnd(...)
        -> bridge.contract_details_end.emit(reqId)
    MarketDataManager.req_contract_details(contract) -> int
        -> id_manager.get_id() + pacing_manager.throttle()
        -> client.reqContractDetails(reqId, contract)
    MarketDataManager.cancel_contract_details(reqId)  # None-safe, swallows exceptions

These are offscreen unit tests with fakes/spies — no live TWS. Existing
historical/RT-tick callbacks are re-exercised to prove no regression.
"""

from unittest.mock import MagicMock

import pytest
from PyQt6.QtCore import pyqtBoundSignal

from ibkr.bridge import IBBridge
from ibkr.client import IBApiClient
from ibkr.market_data import MarketDataManager


# ── T01 — bridge signals ──────────────────────────────────────────

class TestD22_02_T01BridgeSignals:
    def test_contract_details_signals_exist_and_round_trip(self):
        bridge = IBBridge()

        assert isinstance(bridge.contract_details, pyqtBoundSignal)
        assert isinstance(bridge.contract_details_end, pyqtBoundSignal)

        got = []
        bridge.contract_details.connect(lambda rid, cd: got.append(("details", rid, cd)))
        bridge.contract_details_end.connect(lambda rid: got.append(("end", rid)))

        sentinel = object()
        bridge.contract_details.emit(42, sentinel)
        bridge.contract_details_end.emit(42)

        assert got == [("details", 42, sentinel), ("end", 42)]

    def test_contract_details_arity_is_int_object(self):
        bridge = IBBridge()
        bridge.contract_details.connect(lambda *a: None)
        bridge.contract_details_end.connect(lambda *a: None)

        # (int, object) — a single arg is rejected
        with pytest.raises(TypeError):
            bridge.contract_details.emit(42)
        # (int) — zero args is rejected
        with pytest.raises(TypeError):
            bridge.contract_details_end.emit()


# ── T02 — client overrides forward ────────────────────────────────

class TestD22_02_T02ClientOverrides:
    def test_contract_details_override_calls_super_and_forwards(self, monkeypatch):
        from ibapi.wrapper import EWrapper

        super_calls = []

        def spy_contract_details(self, reqId, contractDetails):
            super_calls.append(("contractDetails", reqId, contractDetails))

        def spy_contract_details_end(self, reqId):
            super_calls.append(("contractDetailsEnd", reqId))

        monkeypatch.setattr(EWrapper, "contractDetails", spy_contract_details)
        monkeypatch.setattr(EWrapper, "contractDetailsEnd", spy_contract_details_end)

        client = IBApiClient()

        received = []
        client.bridge.contract_details.connect(
            lambda rid, cd: received.append(("details", rid, cd))
        )
        client.bridge.contract_details_end.connect(
            lambda rid: received.append(("end", rid))
        )

        cd = object()
        client.contractDetails(11, cd)
        client.contractDetailsEnd(11)

        assert super_calls == [
            ("contractDetails", 11, cd),
            ("contractDetailsEnd", 11),
        ]
        assert received == [("details", 11, cd), ("end", 11)]


# ── T03 — manager request / cancel ────────────────────────────────

class _FakeIdManager:
    def __init__(self, value):
        self.value = value

    def get_id(self):
        return self.value


class _FakePacing:
    def __init__(self):
        self.calls = 0

    def throttle(self):
        self.calls += 1


class _FakeClient:
    def __init__(self, cancel_raises=False):
        self.req_calls = []
        self.cancel_calls = []
        self.cancel_raises = cancel_raises

    def reqContractDetails(self, reqId, contract):
        self.req_calls.append((reqId, contract))

    def cancelContractDetails(self, reqId):
        if self.cancel_raises:
            raise RuntimeError("cancel failed")
        self.cancel_calls.append(reqId)


class TestD22_02_T03ManagerRequestCancel:
    def test_req_contract_details_allocates_throttles_delegates(self, monkeypatch):
        import ibkr.market_data as md

        monkeypatch.setattr(md, "id_manager", _FakeIdManager(4242))
        pacing = _FakePacing()
        monkeypatch.setattr(md, "pacing_manager", pacing)

        client = _FakeClient()
        mgr = MarketDataManager(client)
        contract = MagicMock()

        req_id = mgr.req_contract_details(contract)

        assert req_id == 4242
        assert pacing.calls == 1
        assert client.req_calls == [(4242, contract)]

    def test_cancel_contract_details_delegates_and_is_none_safe(self, monkeypatch):
        import ibkr.market_data as md

        client = _FakeClient()
        mgr = MarketDataManager(client)

        mgr.cancel_contract_details(7)
        assert client.cancel_calls == [7]

        mgr.cancel_contract_details(None)
        assert client.cancel_calls == [7]  # still just the one call

    def test_cancel_contract_details_swallows_client_exception(self, monkeypatch):
        import ibkr.market_data as md

        client = _FakeClient(cancel_raises=True)
        mgr = MarketDataManager(client)

        # Must not propagate.
        mgr.cancel_contract_details(7)


# ── T04 — existing callbacks unchanged ────────────────────────────

class TestD22_02_T04ExistingCallbacksUnchanged:
    def test_historical_and_rt_tick_forwarding_still_works(self, monkeypatch):
        from ibapi.wrapper import EWrapper

        super_calls = []

        def make_spy(name):
            def spy(self, *args, **kwargs):
                super_calls.append((name, args))
            return spy

        for name in ("historicalData", "historicalDataEnd", "tickPrice",
                     "tickSize", "realtimeBar"):
            monkeypatch.setattr(EWrapper, name, make_spy(name))

        client = IBApiClient()

        got = {}
        client.bridge.historical_bar.connect(
            lambda rid, bar: got.__setitem__("hist", (rid, bar))
        )
        client.bridge.historical_data_end.connect(
            lambda rid: got.__setitem__("hist_end", rid)
        )
        client.bridge.tick_price.connect(
            lambda rid, tt, p: got.__setitem__("tick_price", (rid, tt, p))
        )
        client.bridge.tick_size.connect(
            lambda rid, tt, s: got.__setitem__("tick_size", (rid, tt, s))
        )
        client.bridge.realtime_bar.connect(
            lambda *a: got.__setitem__("rt", a)
        )

        bar = object()
        client.historicalData(1, bar)
        client.historicalDataEnd(1, "start", "end")
        client.tickPrice(1, 4, 10.5, None)
        client.tickSize(1, 4, 100)
        client.realtimeBar(1, 2, 3.0, 4.0, 2.0, 3.5, 100.0, 3.4, 5)

        assert ("historicalData", (1, bar)) in super_calls
        assert ("historicalDataEnd", (1, "start", "end")) in super_calls
        assert ("tickPrice", (1, 4, 10.5, None)) in super_calls
        assert ("tickSize", (1, 4, 100)) in super_calls
        assert ("realtimeBar", (1, 2, 3.0, 4.0, 2.0, 3.5, 100.0, 3.4, 5)) in super_calls

        assert got["hist"] == (1, bar)
        assert got["hist_end"] == 1
        assert got["tick_price"] == (1, 4, 10.5)
        assert got["tick_size"] == (1, 4, 100)
        assert got["rt"] == (1, 2, 3.0, 4.0, 2.0, 3.5, 100.0, 3.4, 5)


# ── D23-01 — capability-guarded, documented contract-details cancel ──

class TestD23_01_CapabilityGuardedCancel:
    """D23.1 / ESC-030: ``cancel_contract_details`` must be capability-guarded.

    The pinned ``ibapi 9.81.1.post1`` exposes no ``EClient.cancelContractDetails``;
    the bare ``self.client.cancelContractDetails(...)`` access is gone, the method
    is resolved via ``getattr(self.client, "cancelContractDetails", None)``, and
    the absence + real safety net are documented in the source.
    """

    def test_D23_01_T01_source_has_no_bare_cancel_attribute_and_uses_getattr_guard(
        self,
    ):
        """Pre-fix-red: the bare attribute access must be gone; the guard present."""
        import ast
        import inspect
        import textwrap

        src = textwrap.dedent(
            inspect.getsource(MarketDataManager.cancel_contract_details)
        )
        tree = ast.parse(src)

        bare_attr = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "cancelContractDetails"
        ]
        assert bare_attr == [], (
            "bare self.client.cancelContractDetails(...) attribute access must be gone"
        )
        assert "self.client.cancelContractDetails(" not in src
        assert (
            "getattr(self.client, 'cancelContractDetails', None)" in src
            or 'getattr(self.client, "cancelContractDetails", None)' in src
        ), "the capability guard getattr(self.client, 'cancelContractDetails', None) must be present"

    def test_D23_01_T02_missing_capability_is_a_silent_no_op(self):
        """Post-fix guard: the pinned-ibapi shape (no cancel method) must not raise."""
        import types

        client = types.SimpleNamespace(reqContractDetails=lambda *a: None)
        mgr = MarketDataManager(client)

        # Pinned-ibapi shape: no cancelContractDetails -> must complete, no exception.
        mgr.cancel_contract_details(7)

    def test_D23_01_T03_present_capability_called_once_with_req_id(self):
        """Post-fix guard: when present, the method is invoked exactly once with req_id."""
        client = _FakeClient()
        mgr = MarketDataManager(client)

        mgr.cancel_contract_details(7)

        assert client.cancel_calls == [7]

    def test_D23_01_T04_source_documents_absence_and_safety_net(self):
        """The method documents the pinned-version absence, TWS end, and safety net."""
        import inspect

        src = inspect.getsource(MarketDataManager.cancel_contract_details)

        assert "9.81.1.post1" in src
        assert "contractDetailsEnd" in src
        assert "ContractLookupService" in src
        assert "cancel_all" in src

    def test_D23_01_T06_none_req_id_is_a_no_op(self):
        """None-safe: req_id is None returns immediately without invoking the client."""
        client = _FakeClient()
        mgr = MarketDataManager(client)

        mgr.cancel_contract_details(None)

        assert client.cancel_calls == []

    def test_D23_01_T07_raising_present_capability_is_contained(self):
        """Containment preserved: a raising present-method cancel does not propagate."""
        client = _FakeClient(cancel_raises=True)
        mgr = MarketDataManager(client)

        # Must not propagate.
        mgr.cancel_contract_details(7)
