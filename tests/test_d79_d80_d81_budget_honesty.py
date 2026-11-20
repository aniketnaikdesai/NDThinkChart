"""P27-T3 / D81 — the pacing budget is stamped only by a send that crossed
the wire, and a failed send neither charges the clock nor burns a reqId.

Fake-only fixtures: no TWS, no real request. Cases (a)–(c) and (f) are
P27-T3's (D81); cases (d) and (e) are P27-T4's (D80/D79).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ibkr.market_data as md
import ibkr.pacing as pacing_mod
from data.bar_cache import BarCache
from ibkr.id_manager import IdManager
from ibkr.pacing import PacingExceeded, PacingManager
from ui.ticker_session import TickerSession

# The four generic request paths share one ordering contract (D81).
PATHS = (
    "req_mkt_data",
    "req_contract_details",
    "req_sec_def_opt_params",
    "req_matching_symbols",
)


class _Clock:
    """A hand-driven clock; the pacing manager reads only ``time()``."""

    def __init__(self, now: float = 1000.0):
        self.now = now

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _FakeClient:
    """A wire client whose next chosen request call raises on demand."""

    def __init__(self):
        self.attempted: list[int] = []
        self.issued: list[int] = []
        self.fail_next = False

    def _send(self, req_id: int) -> None:
        self.attempted.append(req_id)
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("wire failure")
        self.issued.append(req_id)

    def reqMktData(self, reqId, contract, generic_ticks="", *args):
        self._send(reqId)

    def reqContractDetails(self, reqId, contract):
        self._send(reqId)

    def reqSecDefOptParams(self, reqId, *args):
        self._send(reqId)

    def reqMatchingSymbols(self, reqId, pattern):
        self._send(reqId)


def _send(manager, which: str) -> int:
    if which == "req_mkt_data":
        return manager.req_mkt_data(object())
    if which == "req_contract_details":
        return manager.req_contract_details(object())
    if which == "req_sec_def_opt_params":
        return manager.req_sec_def_opt_params("SPX", "SMART", "IND", 416904)
    assert which == "req_matching_symbols"
    return manager.req_matching_symbols("AAPL")


@pytest.fixture
def wired(monkeypatch):
    """A fake clock, a fresh pacing manager, and a real IdManager.

    ``MAX_REQ_PER_SEC = 1`` keeps the interval exactly one second so the
    interval assertions are exact rather than float-boundary-sensitive; the
    production constant is monkeypatched, never edited.
    """
    clock = _Clock()
    monkeypatch.setattr(pacing_mod, "time", clock)
    monkeypatch.setattr(pacing_mod.settings, "MAX_REQ_PER_SEC", 1)
    pm = PacingManager()
    pm._last_req_time = clock.now - 1.0  # a full interval has elapsed
    ids = IdManager()
    monkeypatch.setattr(md, "pacing_manager", pm)
    monkeypatch.setattr(md, "id_manager", ids)
    client = _FakeClient()
    return clock, pm, ids, client


# ---------------------------------------------------------------------------
# (a) / P27-T3-01 — AC-D81.1: a failed send charges no interval and no budget
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("which", PATHS)
def test_t01_failed_send_charges_no_interval_and_no_budget(wired, which):
    clock, pm, ids, client = wired
    manager = md.MarketDataManager(client)

    first = _send(manager, which)
    assert client.issued == [first]
    first_stamp = pm._last_req_time
    assert first_stamp == clock.now

    # Exactly one minimum interval later the failed attempt is admissible.
    clock.advance(pm._min_interval)
    hist_before = (list(pm._hist_times), pm._last_hist_time)
    rt_before = list(pm._rt_times)

    client.fail_next = True
    with pytest.raises(RuntimeError):
        _send(manager, which)

    # The failed attempt stamped nothing and consumed no budget of either kind.
    assert pm._last_req_time == first_stamp
    assert (list(pm._hist_times), pm._last_hist_time) == hist_before
    assert list(pm._rt_times) == rt_before
    assert client.issued == [first]

    # At the same instant the gate is still measured from the last SUCCESS, so
    # the third send is admitted and the successful spacing is one interval.
    third = _send(manager, which)
    assert client.issued == [first, third]
    assert pm._last_req_time == clock.now
    assert pm._last_req_time - first_stamp == pm._min_interval


# ---------------------------------------------------------------------------
# (b) / P27-T3-02 — AC-D81.2: no failure-shaped gap in the id sequence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("which", PATHS)
def test_t02_failed_send_leaves_no_gap_in_the_id_sequence(wired, which):
    clock, pm, ids, client = wired
    manager = md.MarketDataManager(client)

    first = _send(manager, which)
    clock.advance(pm._min_interval)

    client.fail_next = True
    with pytest.raises(RuntimeError):
        _send(manager, which)

    failed_id = client.attempted[-1]
    assert failed_id == first + 1, "the failed attempt did take a reqId"

    third = _send(manager, which)
    assert third == failed_id, "the next success must reuse the released id"
    assert [first, third] == [first, first + 1]
    assert ids._next_id == third + 1


# ---------------------------------------------------------------------------
# (c) / P27-T3-03 — release_id rolls back only the newest allocation
# ---------------------------------------------------------------------------

def test_t03_release_id_rolls_back_only_the_newest_allocation():
    ids = IdManager()

    first = ids.get_id()
    assert ids.release_id(first) is True
    assert ids.get_id() == first, "a released id is handed out again"

    # Grow the pool, then try to release a non-newest allocation.
    a = ids.get_id()
    b = ids.get_id()
    assert (a, b) == (first + 1, first + 2)
    assert ids.release_id(a) is False, "an older id may still be live"
    assert ids.get_id() == b + 1, "a refused release changes nothing"

    # After another get_id the previous newest is no longer the newest.
    newest = b + 1
    assert ids.release_id(newest) is True
    assert ids.get_id() == newest
    assert ids.release_id(a) is False


# ---------------------------------------------------------------------------
# (f) / P27-T3-04 — AC-P27-03-3: the batch reservation contract
# ---------------------------------------------------------------------------

def test_t04_batch_consumes_one_unit_per_send_and_stamps_once(wired, monkeypatch):
    clock, pm, ids, client = wired
    manager = md.MarketDataManager(client)
    stamps: list[float] = []
    original = pm.record_request_slot

    def _counting_stamp() -> None:
        stamps.append(clock.now)
        original()

    monkeypatch.setattr(pm, "record_request_slot", _counting_stamp)

    pm._last_req_time = clock.now - 2 * pm._min_interval
    with pm.generic_batch(3):
        for _ in range(3):
            _send(manager, "req_mkt_data")
        assert pm._batch_remaining == 0, "three sends consumed three units"
        assert pm._last_req_time == clock.now - 2 * pm._min_interval, \
            "a send inside a reservation must not stamp"
        assert stamps == [], "no stamp inside the batch"
    assert stamps == [clock.now], "the batch's exit stamps exactly once"
    assert len(client.issued) == 3


def test_t04_empty_batch_reserves_nothing_and_stamps_nothing(wired, monkeypatch):
    clock, pm, ids, client = wired
    manager = md.MarketDataManager(client)
    stamps: list[float] = []
    original = pm.record_request_slot

    def _counting_stamp() -> None:
        stamps.append(clock.now)
        original()

    monkeypatch.setattr(pm, "record_request_slot", _counting_stamp)

    with pm.generic_batch(0):
        assert pm._batch_remaining == 0, "an empty reservation reserves nothing"
        # The gate is open: the send is admitted and stamps once (caller path).
        _send(manager, "req_mkt_data")
        assert stamps == [clock.now]
        # The gate is closed: the send is refused, spending no id and no stamp.
        pm._last_req_time = clock.now
        next_id = ids._next_id
        with pytest.raises(PacingExceeded):
            _send(manager, "req_mkt_data")
        assert stamps == [clock.now]
        assert ids._next_id == next_id, "a refused send consumes no reqId"
    assert stamps == [clock.now], "an empty batch stamps nothing on exit"


# ---------------------------------------------------------------------------
# P27-T3-05 — AC-P27-03-4: the default throttle() path is unchanged
# ---------------------------------------------------------------------------

def test_t05_default_throttle_keeps_its_contract(wired):
    clock, pm, ids, client = wired

    # Closed gate: raises carrying the reported wait and stamps nothing.
    pm._last_req_time = clock.now
    reported = pm.request_wait_seconds()
    assert reported > 0
    with pytest.raises(PacingExceeded) as excinfo:
        pm.throttle()
    assert excinfo.value.wait_seconds == pytest.approx(reported)
    assert pm._last_req_time == clock.now, "a refusal stamps nothing"

    # Open gate: stamps once and reports that no reservation unit was spent.
    clock.advance(pm._min_interval)
    assert pm.throttle() is False
    assert pm._last_req_time == clock.now
    with pytest.raises(PacingExceeded):
        pm.throttle()

    # Inside an open reservation: one unit spent, clock untouched, True.
    clock.advance(5.0)
    before = pm._last_req_time
    with pm.generic_batch(1):
        assert pm.throttle() is True
        assert pm._batch_remaining == 0
        assert pm._last_req_time == before, "the reservation touches no clock"
    assert pm._last_req_time == clock.now, "the batch's exit stamps once"


# ---------------------------------------------------------------------------
# (d) / P27-T4-01 — AC-D80.1: a wave never refunds a cancelled slot
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class _CancelTransport:
    """Records cancellations; hands out no request (the wave is registered
    directly, so no send is needed to reach the cancel path)."""

    def __init__(self):
        self.cancels: list[int] = []

    def cancel_historical_data(self, req_id: int) -> None:
        self.cancels.append(req_id)


class _HostStub:
    def __init__(self):
        self.md_manager = _CancelTransport()
        self.routes: dict = {}

    def _register_req_id(self, req_id, session):
        self.routes[req_id] = session

    def _unregister_req_id(self, req_id):
        self.routes.pop(req_id, None)


def test_t06_cancel_of_either_kind_refunds_no_slot(qapp, monkeypatch):
    """Two slots recorded, two tracked ids cancelled: the slot deque is
    byte-identical afterwards and the refund API does not exist.

    The retired pre/post-issue distinction is expressed by the ids' history:
    41's request never reached the wire, 42's did (both hold a slot because
    only a send records one). Either way a cancel refunds nothing.
    """
    clock = _Clock()
    monkeypatch.setattr(pacing_mod, "time", clock)
    pm = pacing_mod.pacing_manager
    pm.reset_for_tests()
    try:
        pm.record_historical_slot()           # 41: sent, recorded after it
        clock.advance(1.0)
        pm.record_historical_slot()           # 42: sent, recorded after it
        slots_before = list(pm._hist_times)
        assert len(slots_before) == 2

        host = _HostStub()
        session = TickerSession("TST", host)
        session._register_history_request(41)
        session._register_history_request(42)

        session._cancel_history_requests()

        assert set(host.md_manager.cancels) == {41, 42}
        assert len(pm._hist_times) == 2, "a cancel never refunds a slot"
        assert list(pm._hist_times) == slots_before, \
            "the other request's slot survives untouched"
        assert session.is_superseded(41)
        assert session.is_superseded(42)
        assert not hasattr(pm, "refund_historical_slot"), \
            "the retired refund API must not exist"
        assert not hasattr(session, "_history_req_issued")
        assert not hasattr(session, "mark_history_request_issued")
    finally:
        pm.reset_for_tests()


# ---------------------------------------------------------------------------
# (e) / P27-T4-03 — AC-D79.1: no mode-blind MAX(ts) read survives
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCAN_DIRS = ("data", "services", "ui", "tests")


def _mode_blind_max_ts_hits() -> list[str]:
    """Files whose source holds a MAX(ts) read against ``bars`` filtered by
    symbol + timeframe without ``ext_hours`` (the D79 rule).

    Scanned: every ``.py`` under ``data/``, ``services/``, ``ui/``, ``tests/``
    and the repo root (R174). This file is skipped: it carries the pattern
    as text, not as a query.
    """
    paths = [p for d in _SCAN_DIRS for p in (_REPO_ROOT / d).rglob("*.py")]
    paths += list(_REPO_ROOT.glob("*.py"))
    hits: list[str] = []
    for path in paths:
        if path.resolve() == Path(__file__).resolve():
            continue
        flat = " ".join(path.read_text(encoding="utf-8", errors="ignore").split())
        start = flat.lower().find("max(ts)")
        while start != -1:
            window = flat[max(0, start - 400):start + 400].lower()
            if (
                "from bars" in window
                and "symbol" in window
                and "timeframe" in window
                and "ext_hours" not in window
            ):
                hits.append(f"{path.relative_to(_REPO_ROOT)}: {window[:160]}")
            start = flat.lower().find("max(ts)", start + 1)
    return hits


def test_t07_no_mode_blind_cache_read_survives():
    assert not hasattr(BarCache, "get_last_timestamp"), \
        "the mode-blind cache read is retired, not deprecated"
    assert _mode_blind_max_ts_hits() == []
