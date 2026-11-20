"""P26-T1 / D71 — the reconnect replay is one transaction over a union budget
and retires every line it supersedes.

Fake-only fixtures: no TWS, no real market-data request, no GUI event loop.
"""

from __future__ import annotations

import contextlib
import time

import pytest
from PyQt6.QtCore import QTimer

import ibkr.subscription_manager as sub_mod
from ibkr.error_codes import IBKRNotReady
from ibkr.pacing import PacingExceeded, PacingManager
from ibkr.subscription_manager import (
    OPTION_LEGS,
    RT_BARS,
    S0_TICKS,
    SubscriptionManager,
)

INCLUDE = {RT_BARS, S0_TICKS, OPTION_LEGS}


# ---------------------------------------------------------------------------
# Fakes: one counter per real manager method the replay drives
# ---------------------------------------------------------------------------


class FakeMdManager:
    """Counts reqMktData / cancelMktData per reqId; can fail one contract."""

    def __init__(self):
        self._next = 1000
        self.issued: list[int] = []
        self.cancelled: list[int] = []
        self.fail_on: set[str] = set()

    def req_mkt_data(self, contract=None) -> int:
        if contract in self.fail_on:
            raise IBKRNotReady("market data farm is not ready")
        req_id = self._next
        self._next += 1
        self.issued.append(req_id)
        return req_id

    def cancel_mkt_data(self, req_id) -> None:
        self.cancelled.append(int(req_id))


class FakeRtManager:
    """Counts realtime subscribe / unsubscribe per reqId."""

    def __init__(self):
        self._next = 5000
        self.issued: list[int] = []
        self.unsubscribed: list[int] = []

    def subscribe(self, symbol, contract=None) -> int:
        req_id = self._next
        self._next += 1
        self.issued.append(req_id)
        return req_id

    def unsubscribe(self, req_id) -> None:
        self.unsubscribed.append(int(req_id))


class FakePacing:
    """The union gate, controllable: a batch of >1 is refused until admitted.

    Mirrors PacingManager's contract for the one property the replay needs:
    an empty reservation (``count <= 0``) never waits, and a batch of exactly
    one admits its single send by design (an open batch of ``n`` admits ``n``
    calls, AC-D71.5). A batch is either admissible (0.0) or refused for a
    reported wait.
    """

    def __init__(self, *, admit: bool, generic_wait: float = 0.0,
                 rt_wait: float = 0.0):
        self.admit = admit
        self.generic_wait = generic_wait
        self.rt_wait = rt_wait
        self.batch_counts: list[int] = []
        self.rt_counts: list[int] = []

    def realtime_wait_for_slots(self, n: int) -> float:
        self.rt_counts.append(int(n))
        return self.rt_wait if n > 0 else 0.0

    def generic_wait_for_batch(self, n: int) -> float:
        if n <= 1:
            return 0.0
        return 0.0 if self.admit else self.generic_wait

    @contextlib.contextmanager
    def generic_batch(self, count: int):
        wait = self.generic_wait_for_batch(count)
        if wait > 0:
            raise PacingExceeded(wait)
        self.batch_counts.append(int(count))
        yield


class _StatusBar:
    def __init__(self):
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int = 0) -> None:
        self.messages.append((message, timeout))


class _ReplayWindowStub:
    """Just enough of MainWindow to drive ``_replay_subscriptions``."""

    def __init__(self, sub_manager):
        self.sub_manager = sub_manager
        self.status_bar = _StatusBar()
        self._replay_serial = 0

    def _replay_subscriptions(self):
        from ui.main_window import MainWindow

        MainWindow._replay_subscriptions(self)


class _FlakySubManager:
    """A replay pass that refuses the first ``fail_times`` calls."""

    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.attempts = 0
        self.passes = 0
        self.include_sets: list[set] = []

    def replay_all(self, include_types=None):
        self.attempts += 1
        self.include_sets.append(set(include_types or ()))
        if self.attempts <= self.fail_times:
            raise PacingExceeded(1.0)
        self.passes += 1
        return []


# ---------------------------------------------------------------------------
# Registry fixtures: one RT_BARS entry + two OPTION_LEGS entries
# ---------------------------------------------------------------------------


def _mixed_registry(reg: SubscriptionManager, rt: FakeRtManager,
                    md: FakeMdManager):
    """Register (in order) rt, opt1, opt2; return observable state."""
    order: list[str] = []
    routes: dict[str, int] = {}
    rebinds: list[tuple[str, int]] = []

    def rt_reissue() -> int:
        order.append("rt")
        new_id = rt.subscribe("AAA")
        routes["rt"] = new_id
        return new_id

    def rt_rebind(new_id: int) -> None:
        rebinds.append(("rt", int(new_id)))
        routes["rt"] = int(new_id)

    reg.subscribe("AAA", 101, RT_BARS, reissue=rt_reissue, rebind=rt_rebind)
    routes["rt"] = 101

    def add_leg(name: str, old_id: int) -> None:
        def reissue() -> int:
            order.append(name)
            new_id = md.req_mkt_data(name)
            routes[name] = new_id
            return new_id

        def rebind(new_id: int) -> None:
            rebinds.append((name, int(new_id)))
            routes[name] = int(new_id)

        reg.subscribe(name, old_id, OPTION_LEGS, reissue=reissue,
                      rebind=rebind)
        routes[name] = old_id

    add_leg("opt1", 201)
    add_leg("opt2", 301)
    return order, routes, rebinds


def _install_resolvers(reg: SubscriptionManager, rt: FakeRtManager,
                       md: FakeMdManager) -> None:
    reg.set_cancel_hook(RT_BARS, rt.unsubscribe)
    reg.set_cancel_hook(OPTION_LEGS, md.cancel_mkt_data)


# ---------------------------------------------------------------------------
# AC-D71.1 — the union gate defers the entire pass; one deferral; one replay
# ---------------------------------------------------------------------------


def test_P26_T1_AC1_union_gate_defers_then_replays_every_entry_once(
        monkeypatch):
    reg = SubscriptionManager()
    rt = FakeRtManager()
    md = FakeMdManager()
    order, _routes, _rebinds = _mixed_registry(reg, rt, md)
    _install_resolvers(reg, rt, md)

    # The generic gate refuses a batch of 2 (it would admit only the first
    # send); the realtime budget is open, so the union is what defers.
    pacing = FakePacing(admit=False, generic_wait=2.0)
    monkeypatch.setattr(sub_mod, "pacing_manager", pacing)

    scheduled: list[tuple[int, object]] = []
    monkeypatch.setattr(
        QTimer, "singleShot", lambda ms, fn: scheduled.append((ms, fn))
    )

    stub = _ReplayWindowStub(reg)
    before = dict(reg._entries)

    stub._replay_subscriptions()  # must not raise: one deferral instead

    assert order == []
    assert md.issued == [] and rt.issued == []
    assert list(reg._entries) == list(before)
    assert all(reg._entries[k] is before[k] for k in before)
    assert len(scheduled) == 1
    assert scheduled[0][0] == 2000
    assert "pacing-limited" in stub.status_bar.messages[-1][0].lower()

    # Admit the generic batch and run the one scheduled callback.
    pacing.admit = True
    scheduled[0][1]()

    assert order == ["rt", "opt1", "opt2"]     # registry order, once each
    assert len(md.issued) == 2
    assert len(rt.issued) == 1
    assert len(scheduled) == 1                 # the admitted pass defers not


# ---------------------------------------------------------------------------
# AC-D71.2 — every superseded line retired exactly once; repeat passes settle
# ---------------------------------------------------------------------------


def test_P26_T1_AC2_retires_every_superseded_line_and_repeats_cleanly(
        monkeypatch):
    reg = SubscriptionManager()
    rt = FakeRtManager()
    md = FakeMdManager()
    _mixed_registry(reg, rt, md)
    _install_resolvers(reg, rt, md)
    monkeypatch.setattr(sub_mod, "pacing_manager", FakePacing(admit=True))

    before_ids = list(reg._entries)
    assert len(before_ids) == 3

    pairs1 = reg.replay_all(INCLUDE)
    live1 = list(reg._entries)
    assert pairs1 == [(101, 5000), (201, 1000), (301, 1001)]
    assert len(live1) == len(before_ids) == 3
    assert len(set(live1)) == 3                # no new id registered twice
    assert rt.unsubscribed == [101]            # old RT retired exactly once
    assert md.cancelled == [201, 301]          # old legs, each exactly once

    pairs2 = reg.replay_all(INCLUDE)
    live2 = list(reg._entries)
    assert len(live2) == len(before_ids) == 3
    assert len(set(live2)) == 3
    # The second pass retires exactly the ids the first pass introduced,
    # once each, and leaves the same live-count / fresh-id shape.
    assert rt.unsubscribed == [101, 5000]
    assert md.cancelled == [201, 301, 1000, 1001]
    assert [old for old, _new in pairs2] == live1
    assert len({new for _old, new in pairs1}) == 3
    assert len({new for _old, new in pairs2}) == 3
    assert set(live2).isdisjoint(before_ids)


# ---------------------------------------------------------------------------
# AC-D71.3 (unwind) — a mid-reissue raise retires only the new lines
# ---------------------------------------------------------------------------


def test_P26_T1_AC3_unwind_retires_new_ids_rebinds_old_and_propagates(
        monkeypatch):
    reg = SubscriptionManager()
    md = FakeMdManager()
    routes: dict[str, int] = {}
    rebinds: list[tuple[str, int]] = []

    def add_leg(name: str, old_id: int) -> None:
        def reissue() -> int:
            new_id = md.req_mkt_data(name)
            routes[name] = new_id
            return new_id

        def rebind(new_id: int) -> None:
            rebinds.append((name, int(new_id)))
            routes[name] = int(new_id)

        reg.subscribe(name, old_id, OPTION_LEGS, reissue=reissue,
                      rebind=rebind)
        routes[name] = old_id

    add_leg("opt1", 201)
    add_leg("opt2", 301)
    md.fail_on.add("opt2")          # second reissue raises after the first
    reg.set_cancel_hook(OPTION_LEGS, md.cancel_mkt_data)
    monkeypatch.setattr(sub_mod, "pacing_manager", FakePacing(admit=True))

    before = dict(reg._entries)

    with pytest.raises(IBKRNotReady):
        reg.replay_all(INCLUDE)

    assert md.issued == [1000]                # only the first entry issued
    assert md.cancelled == [1000]             # ... and its new id was retired
    assert 201 not in md.cancelled and 301 not in md.cancelled
    assert routes == {"opt1": 201, "opt2": 301}
    assert rebinds == [("opt1", 201), ("opt2", 301)]
    assert list(reg._entries) == list(before)
    assert all(reg._entries[k] is before[k] for k in before)


# ---------------------------------------------------------------------------
# AC-D71.4 — same pairs / one rebind per entry with both budgets open
# ---------------------------------------------------------------------------


def test_P26_T1_AC4_pairs_and_one_rebind_per_entry_with_budgets_open(
        monkeypatch):
    reg = SubscriptionManager()
    rt = FakeRtManager()
    md = FakeMdManager()
    _order, _routes, rebinds = _mixed_registry(reg, rt, md)
    _install_resolvers(reg, rt, md)
    pacing = FakePacing(admit=True)
    monkeypatch.setattr(sub_mod, "pacing_manager", pacing)

    pairs = reg.replay_all(INCLUDE)

    assert pairs == [(101, 5000), (201, 1000), (301, 1001)]
    assert [name for name, _new in rebinds] == ["rt", "opt1", "opt2"]
    assert len(rebinds) == 3                  # exactly one rebind per entry
    assert len({new for _old, new in pairs}) == 3
    assert pacing.batch_counts == [2]         # generic_n excludes the RT entry


# ---------------------------------------------------------------------------
# AC-D71.5 — the reservation is one-shot, fail-closed, and resettable
# ---------------------------------------------------------------------------


def test_P26_T1_AC5_generic_batch_reservation_is_fail_closed():
    pm = PacingManager()
    pm.reset_for_tests()
    pm._last_req_time = time.time() - 1.0

    assert pm.generic_wait_for_batch(0) == 0.0
    assert pm.generic_wait_for_batch(1) == 0.0
    assert pm.generic_wait_for_batch(3) == 0.0

    with pm.generic_batch(3):
        for _ in range(3):
            pm.throttle()                     # all reserved: no sleep, no gate
        assert pm._batch_remaining == 0
        # A send elsewhere stamped the interval: the (n+1)th call must fall
        # through to the unchanged minimum-interval gate (fail-closed), not
        # consume the reservation twice.
        pm.record_request_slot()
        with pytest.raises(PacingExceeded):
            pm.throttle()
    assert pm._batch_remaining == 0

    # After the batch has closed the gate behaves exactly as before: the
    # ``finally`` stamped the clock, so an immediate call is refused.
    with pytest.raises(PacingExceeded):
        pm.throttle()

    # reset_for_tests clears an open reservation, so it can never admit a
    # later send: inside a fresh batch the gate is authoritative again.
    pm.reset_for_tests()
    pm._last_req_time = time.time() - 1.0
    with pm.generic_batch(2):
        pm.reset_for_tests()
        assert pm._batch_remaining == 0
        pm.throttle()                         # admitted by the unchanged gate
        with pytest.raises(PacingExceeded):
            pm.throttle()                     # no reservation left to spend


# ---------------------------------------------------------------------------
# Journey 68 edges: a newer generation supersedes a pending deferral, and an
# RT-only pass is untouched by a throttled generic gate.
# ---------------------------------------------------------------------------


def test_P26_T1_epoch_supersedes_a_stacked_deferral(monkeypatch):
    scheduled: list[tuple[int, object]] = []
    monkeypatch.setattr(
        QTimer, "singleShot", lambda ms, fn: scheduled.append((ms, fn))
    )
    sub = _FlakySubManager(fail_times=2)
    stub = _ReplayWindowStub(sub)

    stub._replay_subscriptions()      # generation 1: refused, schedules
    stub._replay_subscriptions()      # generation 2: refused, schedules
    assert sub.attempts == 2 and sub.passes == 0
    assert len(scheduled) == 2
    assert all(ms == 1000 for ms, _fn in scheduled)
    assert sub.include_sets[0] == INCLUDE

    scheduled[0][1]()                 # stale epoch: returns, no second pass
    assert sub.attempts == 2 and sub.passes == 0

    scheduled[1][1]()                 # current epoch: exactly one pass
    assert sub.attempts == 3 and sub.passes == 1


def test_P26_T1_rt_only_pass_ignores_a_throttled_generic_gate(monkeypatch):
    reg = SubscriptionManager()
    rt = FakeRtManager()
    reg.subscribe(
        "AAA", 101, RT_BARS,
        reissue=lambda: rt.subscribe("AAA"),
        rebind=lambda _new: None,
    )
    pacing = FakePacing(admit=False, generic_wait=5.0)
    monkeypatch.setattr(sub_mod, "pacing_manager", pacing)

    pairs = reg.replay_all(INCLUDE)

    assert pairs == [(101, 5000)]
    assert pacing.rt_counts == [1]
    assert pacing.batch_counts == [0]   # generic_n is exactly len(pending)-rt_n


# ---------------------------------------------------------------------------
# ESC-129 rework: an empty reservation is not spendable and does not touch
# the interval clock; a batch of one says plainly that it admits its send.
# ---------------------------------------------------------------------------


def test_P26_T1_empty_reservation_spends_nothing_and_stamps_nothing():
    pm = PacingManager()
    pm.reset_for_tests()
    pm._last_req_time = time.time() - 1.0   # the ordinary gate is open

    with pm.generic_batch(0):
        assert pm._batch_remaining == 0     # nothing was reserved
        pm.throttle()                       # the unchanged gate decides
        stamped = pm._last_req_time
    # The exit stamp is skipped for a zero-unit reservation: the clock is
    # exactly where the body's own admitted send left it.
    assert pm._last_req_time == stamped
    assert pm._batch_remaining == 0

    # On a throttled manager an empty reservation neither admits a send nor
    # resets the interval clock.
    pm._last_req_time = time.time()
    stamped = pm._last_req_time
    with pm.generic_batch(0):
        with pytest.raises(PacingExceeded):
            pm.throttle()
    assert pm._last_req_time == stamped

    # Negative counts are empty reservations too.
    with pm.generic_batch(-2):
        with pytest.raises(PacingExceeded):
            pm.throttle()
    assert pm._last_req_time == stamped


def test_P26_T1_batch_of_one_admits_its_single_send_by_design():
    pm = PacingManager()
    pm.reset_for_tests()
    pm._last_req_time = time.time()         # the ordinary gate would refuse

    with pm.generic_batch(1):
        pm.throttle()                       # reserved: no gate read
        assert pm._batch_remaining == 0
        pm.record_request_slot()
        with pytest.raises(PacingExceeded):
            pm.throttle()                   # over-spend falls through to gate
    # The finally stamp leaves the ordinary gate authoritative afterwards.
    with pytest.raises(PacingExceeded):
        pm.throttle()
    assert pm._batch_remaining == 0


def test_P26_T1_rt_only_pass_leaves_the_generic_clock_untouched(monkeypatch):
    """ESC-129 case (1): an RT-only pass must not defer the next send."""
    pm = PacingManager()
    pm.reset_for_tests()
    reg = SubscriptionManager()
    rt = FakeRtManager()
    reg.subscribe(
        "AAA", 101, RT_BARS,
        reissue=lambda: rt.subscribe("AAA"),
        rebind=lambda _new: None,
    )
    monkeypatch.setattr(sub_mod, "pacing_manager", pm)

    assert reg.replay_all(INCLUDE) == [(101, 5000)]
    # generic_n was 0, so no phantom 20 ms was spent: the very next send is
    # admitted by the unchanged gate instead of being refused.
    pm.throttle()
