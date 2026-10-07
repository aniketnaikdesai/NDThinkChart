"""Offscreen unit tests for ``ContractLookupService`` (D22-03 / AC-D22.3.1..6).

The service is exercised with a **fake bridge** (a plain ``QObject`` exposing the
same three signals the real ``IBBridge`` does) and a **fake market-data manager**
that hands out deterministic reqIds. No TWS connection, no live EClient and no
database are touched.

A single shared offscreen ``QApplication`` (the ``qapp`` fixture) is required
only to construct ``QObject``/``QTimer`` instances; every signal here is a
same-thread direct connection, so emissions resolve synchronously.
"""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QObject, pyqtSignal

from services.contract_lookup_service import (
    CONTRACT_LOOKUP_TIMEOUT_MS,
    ContractLookupService,
    PendingLookup,
)


class FakeBridge(QObject):
    """Minimal signal surface of ``IBBridge`` (D22-02) — no transport."""

    contract_details = pyqtSignal(int, object)   # reqId, ContractDetails
    contract_details_end = pyqtSignal(int)       # reqId
    error_msg = pyqtSignal(int, int, str)        # reqId, errorCode, errorString


class FakeMdManager:
    """Deterministic stand-in for ``MarketDataManager.req_contract_details``."""

    def __init__(self, first_id: int = 100):
        self._next_id = first_id
        self.calls: list[tuple[int, object]] = []

    def req_contract_details(self, contract) -> int:
        req_id = self._next_id
        self._next_id += 1
        self.calls.append((req_id, contract))
        return req_id


class _Contract:
    """Sentinel contract object — passed through unchanged."""


@pytest.fixture
def bridge() -> FakeBridge:
    return FakeBridge()


@pytest.fixture
def md() -> FakeMdManager:
    return FakeMdManager()


@pytest.fixture
def svc(qapp, md, bridge) -> ContractLookupService:
    return ContractLookupService(md_manager=md, bridge=bridge)


def _record(svc: ContractLookupService) -> list[tuple]:
    """Attach an event recorder to ``lookup_finished`` and return its list."""
    events: list[tuple] = []
    svc.lookup_finished.connect(lambda *args: events.append(args))
    return events


# --------------------------------------------------------------- D22-03-T01
def test_D22_03_T01_success_resolves_ok_exactly_once(svc, bridge, md):
    events = _record(svc)

    req_id = svc.request("AAPL", _Contract())
    assert req_id == md.calls[-1][0]
    assert svc.is_pending(req_id)

    bridge.contract_details.emit(req_id, object())
    bridge.contract_details_end.emit(req_id)

    assert len(events) == 1
    got_id, symbol, ok, reason = events[0]
    assert got_id == req_id
    assert symbol == "AAPL"
    assert ok is True
    assert isinstance(reason, str) and reason
    assert not svc.is_pending(req_id)

    # A second end for the same reqId must not fire again.
    bridge.contract_details_end.emit(req_id)
    assert len(events) == 1


# --------------------------------------------------------------- D22-03-T02
def test_D22_03_T02_end_with_zero_details_rejects(svc, bridge):
    events = _record(svc)

    req_id = svc.request("NOPE", _Contract())
    bridge.contract_details_end.emit(req_id)

    assert len(events) == 1
    got_id, symbol, ok, reason = events[0]
    assert got_id == req_id
    assert symbol == "NOPE"
    assert ok is False
    assert isinstance(reason, str) and reason
    assert not svc.is_pending(req_id)

    # Duplicate end still emits nothing further.
    bridge.contract_details_end.emit(req_id)
    assert len(events) == 1


# --------------------------------------------------------------- D22-03-T03
def test_D22_03_T03_error_correlation_ignores_unrelated_reqid(svc, bridge):
    events = _record(svc)

    first = svc.request("AAPL", _Contract())
    second = svc.request("MSFT", _Contract())

    bridge.error_msg.emit(first, 200, "No security definition")
    bridge.error_msg.emit(987654, 200, "unrelated market-data error")

    # Only the errored pending lookup resolved; the unknown reqId did nothing.
    assert len(events) == 1
    got_id, symbol, ok, reason = events[0]
    assert got_id == first
    assert symbol == "AAPL"
    assert ok is False
    assert isinstance(reason, str) and reason

    assert not svc.is_pending(first)
    assert svc.is_pending(second)
    assert len(events) == 1  # second lookup still silent

    # The second lookup resolves normally when it finally ends with details.
    bridge.contract_details.emit(second, object())
    bridge.contract_details_end.emit(second)
    assert len(events) == 2
    assert events[1][0] == second
    assert events[1][1] == "MSFT"
    assert events[1][2] is True


# --------------------------------------------------------------- D22-03-T04
def test_D22_03_T04_bounded_timeout_rejects_and_drops(svc):
    events = _record(svc)

    req_id = svc.request("AAPL", _Contract())
    pending = svc.pending_lookup(req_id)
    assert isinstance(pending, PendingLookup)
    assert pending.timer is not None
    assert pending.timer.isSingleShot()
    assert pending.timer.isActive()
    assert pending.timer.interval() == CONTRACT_LOOKUP_TIMEOUT_MS

    svc.on_timeout(req_id)

    assert len(events) == 1
    got_id, symbol, ok, reason = events[0]
    assert got_id == req_id
    assert symbol == "AAPL"
    assert ok is False
    assert isinstance(reason, str) and reason
    assert not svc.is_pending(req_id)
    assert svc.pending_count() == 0

    # A duplicate timeout is also a no-op.
    svc.on_timeout(req_id)
    assert len(events) == 1


# --------------------------------------------------------------- D22-03-T05
def test_D22_03_T05_late_events_after_timeout_are_ignored(svc, bridge):
    events = _record(svc)

    req_id = svc.request("AAPL", _Contract())
    svc.on_timeout(req_id)
    assert len(events) == 1

    # Late details + end for the already-resolved reqId.
    bridge.contract_details.emit(req_id, object())
    bridge.contract_details_end.emit(req_id)
    assert len(events) == 1


# --------------------------------------------------------------- D22-03-T06
def test_D22_03_T06_cancel_and_cancel_all_invalidate(svc, bridge, md):
    events = _record(svc)

    first = svc.request("AAPL", _Contract())
    second = svc.request("MSFT", _Contract())
    third = svc.request("GOOG", _Contract())
    assert len({first, second, third}) == 3

    svc.cancel(first)
    svc.cancel_all()

    assert not svc.is_pending(first)
    assert not svc.is_pending(second)
    assert not svc.is_pending(third)
    assert svc.pending_count() == 0

    # Late callbacks / error / timeout for cancelled reqIds emit nothing.
    bridge.contract_details.emit(first, object())
    bridge.contract_details_end.emit(first)
    bridge.contract_details.emit(second, object())
    bridge.contract_details_end.emit(second)
    bridge.error_msg.emit(third, 200, "late error")
    svc.on_timeout(third)
    assert events == []

    # Cancelling an unknown reqId is harmless.
    svc.cancel(424242)

    # A fresh request returns its registered reqId and is pending.
    fresh = svc.request("TSLA", _Contract())
    assert fresh == md.calls[-1][0]
    assert svc.is_pending(fresh)
    assert svc.pending_lookup(fresh).symbol == "TSLA"

    bridge.contract_details.emit(fresh, object())
    bridge.contract_details_end.emit(fresh)
    assert len(events) == 1
    assert events[0] == (fresh, "TSLA", True, events[0][3])
