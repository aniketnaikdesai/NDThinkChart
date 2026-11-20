"""P28-02 (D84/D88) — one readiness seam, one replay, the drop owes the attach.

Cases (P28-T2-01..08):

(a) AC-D84.3 — ``RealtimeBarsManager.subscribe`` refuses through the same
    ``api_ready`` seam the market-data manager uses, before pacing, before
    the id, before the send; a ready client behaves as today.
(b) AC-D84.1 — none of the three arrivals (prime completes, prime times out,
    fail-open) attaches on a not-ready transport, and the refusal is
    remembered on the session. LOAD-BEARING: this uses a real ``MainWindow``
    and its REAL ``_transport_ready`` (both ``_ibkr_connected`` and the
    client's ``_connected`` are set; nothing is overridden), which is what
    keeps the audited suites' ``win._transport_ready = lambda: True`` a
    harness stub rather than a hole.
(c) AC-D84.2 — a drop clears every session's prime block through the one
    helper, stops the RT retry timer, and issues no subscribe; the three
    in-file call sites call ``_clear_prime_state()`` instead of re-stating
    the six statements.
(d) AC-P28-02-1 / Journey 74 / R175 — the drop owes the attach, the
    reconnect pays it exactly once, plus the two negatives (a background
    session; a session whose line was already live).
(e) AC-D88.1 — the realtime manager's dead replay is gone, with no code
    use of the symbol anywhere in ``ui/``, ``ibkr/`` or ``tests/``. Prose
    mentions and ``not hasattr`` strings are not uses, and neither is the
    legitimate ``SubscriptionManager.replay_all`` (the one replay P28 keeps).
(f) AC-D84.3 — one function serves both managers; ``_require_api_ready``'s
    signature and exception identity are unchanged.
(g) AC-P28-02-3 — the new flag defaults to False and dies with the session.
(h) The two named re-baselines (test-hygiene only, supporting AC-D88.1).
"""

from __future__ import annotations

import ast
import inspect
import itertools
from pathlib import Path

import pytest
from ibapi.contract import Contract

import ibkr.error_codes as error_codes
import ibkr.market_data as market_data
import ibkr.realtime_bars as realtime_bars
from ibkr.error_codes import IBKRNotReady
from ibkr.market_data import MarketDataManager
from ibkr.realtime_bars import RealtimeBarsManager
from ui.ticker_session import TickerSession

ROOT = Path(__file__).resolve().parents[1]
RETIRED_STREAMING_ID = "test_p7_t07_t11_manager_replay_rebounds_every_subscription"


# ── Doubles ─────────────────────────────────────────────────────────────────


class _ReadinessClient:
    """Client double with settable readiness and a recording send."""

    def __init__(self, api_ready: bool = False):
        self.api_ready = api_ready
        self.rt_requests: list[tuple] = []

    def reqRealTimeBars(self, *args):
        self.rt_requests.append(args)

    def cancelRealTimeBars(self, req_id):  # pragma: no cover - not exercised
        pass


class _PacingRecorder:
    def __init__(self):
        self.realtime_slots = 0

    def realtime_wait_seconds(self) -> float:
        return 0.0

    def record_realtime_slot(self) -> None:
        self.realtime_slots += 1


class _IdRecorder:
    def __init__(self):
        self.calls = 0
        self._next = 7000

    def get_id(self) -> int:
        self.calls += 1
        self._next += 1
        return self._next


# ── Window harness ──────────────────────────────────────────────────────────


@pytest.fixture
def win_factory(monkeypatch, qapp):
    """Real ``MainWindow``, real predicate, fake realtime manager.

    The shipped window-factory convention (monkeypatched ``connect``,
    unbounded id source, ``qapp.processEvents``) with one addition: the
    connection flags are set so the REAL ``_transport_ready`` answers, never
    by overriding the predicate.
    """
    from ibkr.client import IBApiClient
    from ui.main_window import MainWindow

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    windows = []

    def make(*, connected: bool = False, api_ready: bool = False):
        win = MainWindow()
        ids = itertools.count(9001)
        subs: list[tuple] = []

        def fake_subscribe(symbol, contract):
            subs.append((symbol, contract))
            return next(ids)

        win.rt_manager.subscribe = fake_subscribe
        win._ibkr_connected = connected
        win.ib_client._connected = api_ready
        win.show()
        qapp.processEvents()
        win._p28_subs = subs
        windows.append(win)
        return win

    yield make
    for win in windows:
        win.close()


# ── (a) AC-D84.3 — the realtime gate ────────────────────────────────────────


def test_p28_t2_01_realtime_gate_refuses_before_pacing_id_and_send(monkeypatch):
    pacing = _PacingRecorder()
    ids = _IdRecorder()
    monkeypatch.setattr(realtime_bars, "pacing_manager", pacing)
    monkeypatch.setattr(realtime_bars, "id_manager", ids)

    client = _ReadinessClient(api_ready=False)
    mgr = RealtimeBarsManager(client)
    contract = Contract()

    with pytest.raises(IBKRNotReady) as excinfo:
        mgr.subscribe("AAPL", contract)

    assert type(excinfo.value) is IBKRNotReady
    assert str(excinfo.value) == "IBKR API not ready (handshake pending)"
    assert ids.calls == 0, "a refused attach must allocate no reqId"
    assert pacing.realtime_slots == 0, "a refused attach must record no slot"
    assert client.rt_requests == []
    assert mgr._subscriptions == {}

    # A ready client behaves exactly as today: one id, one send, one slot.
    client.api_ready = True
    req_id = mgr.subscribe("AAPL", contract)
    assert ids.calls == 1
    assert pacing.realtime_slots == 1
    assert len(client.rt_requests) == 1
    assert client.rt_requests[0][0] == req_id
    assert mgr._subscriptions[req_id] == ("AAPL", contract)


# ── (b) AC-D84.1 — no arrival attaches on a not-ready transport ─────────────


@pytest.mark.parametrize("arrival", ["prime_complete", "prime_timeout", "fail_open"])
@pytest.mark.parametrize("connected,api_ready", [(False, False), (True, False)])
def test_p28_t2_02_arrivals_never_attach_on_a_not_ready_transport(
    win_factory, arrival, connected, api_ready
):
    win = win_factory(connected=connected, api_ready=api_ready)
    win._current_symbol = "AAPL"
    session = win.get_or_create_session("AAPL")
    session._wave_contract = Contract()

    if arrival == "prime_complete":
        win._on_session_prime_complete(session)
    elif arrival == "prime_timeout":
        win._on_session_prime_timeout(session)
    else:
        session._fail_open_prime("5 mins")

    assert win._p28_subs == [], "no realtime subscription may be created"
    assert session._rt_req_id is None
    assert session._rt_attach_pending is True


# ── (c) AC-D84.2 — one prime clear, four call sites ─────────────────────────


def test_p28_t2_03_disconnect_clears_every_prime_block(win_factory, qapp):
    win = win_factory(connected=True, api_ready=True)
    win._current_symbol = "AAPL"
    primary = win.get_or_create_session("AAPL")
    background = win.get_or_create_session("ES")

    for session in (primary, background):
        session._prime_timer.start(0)
        assert session._prime_timer.isActive()
        session._prime_req_id = 1234
        session._prime_retry_pending = True
        session._prime_retry_args = (Contract(), "5 mins", False)
        session._prime_reserved = True

    win._rt_retry_timer.start(0)
    assert win._rt_retry_timer.isActive()

    win._on_disconnected()
    # A 0 ms deadline fires on the next turn of the loop; a stopped timer
    # cannot, so this is the clock advance past the old deadline.
    qapp.processEvents()
    qapp.processEvents()

    for session in (primary, background):
        assert not session._prime_timer.isActive()
        assert session._prime_req_id is None
        assert session._prime_retry_pending is False
        assert session._prime_retry_args is None
        assert session._prime_reserved is False

    assert not win._rt_retry_timer.isActive()
    assert win._p28_subs == []


def test_p28_t2_03_prime_clear_is_one_helper_not_three_copies():
    for func in (
        TickerSession.teardown,
        TickerSession.prepare_load,
        TickerSession._fail_open_prime,
    ):
        src = inspect.getsource(func)
        assert "_clear_prime_state()" in src, func.__name__
        assert "_prime_timer.stop()" not in src, func.__name__
        assert "_prime_req_id = None" not in src, func.__name__
        assert "_prime_retry_args = None" not in src, func.__name__
        assert "_prime_reserved = False" not in src, func.__name__

    fail_open_src = inspect.getsource(TickerSession._fail_open_prime)
    assert "_prime_skipped_count += 1" in fail_open_src
    assert "_on_session_prime_complete(self)" in fail_open_src

    from ui.main_window import MainWindow

    assert "session._clear_prime_state()" in inspect.getsource(
        MainWindow._on_disconnected
    )


# ── (d) AC-P28-02-1 / Journey 74 / R175 — the drop owes the attach ──────────


def test_p28_t2_04_drop_owes_attach_and_reconnect_pays_it_once(win_factory):
    win = win_factory(connected=True, api_ready=True)
    win._current_symbol = "AAPL"
    session = win.get_or_create_session("AAPL")
    session._wave_contract = Contract()
    session._prime_timer.start(15000)
    assert session._prime_timer.isActive()

    win._on_disconnected()
    assert session._rt_attach_pending is True
    assert not session._prime_timer.isActive()
    assert win._p28_subs == []

    win._on_connected()
    assert len(win._p28_subs) == 1
    assert session._rt_attach_pending is False
    assert session._rt_holders == 1
    assert session._rt_req_id == 9001

    # The replay re-issues the now-registered line; the deferred pass adds
    # nothing (the flag is already paid).
    win._on_connected()
    assert len(win._p28_subs) == 2
    assert session._rt_holders == 1
    assert session._rt_attach_pending is False


def test_p28_t2_04_background_armed_prime_is_not_owed(win_factory):
    win = win_factory(connected=True, api_ready=True)
    win._current_symbol = "AAPL"
    win.get_or_create_session("AAPL")
    background = win.get_or_create_session("ES")
    background._wave_contract = Contract()
    background._prime_timer.start(15000)
    assert background._prime_timer.isActive()

    win._on_disconnected()
    assert background._rt_attach_pending is False
    assert not background._prime_timer.isActive()

    win._on_connected()
    assert background._rt_req_id is None
    assert win._p28_subs == []


def test_p28_t2_04_live_line_is_not_flagged_and_replays_once(win_factory):
    win = win_factory(connected=True, api_ready=True)
    win._current_symbol = "AAPL"
    session = win.get_or_create_session("AAPL")
    session._wave_contract = Contract()
    session.ensure_rt_subscribed()
    assert session._rt_req_id is not None
    assert session._rt_holders == 1
    baseline = len(win._p28_subs)
    session._prime_timer.start(15000)

    win._on_disconnected()
    assert session._rt_attach_pending is False
    assert not session._prime_timer.isActive()

    win._on_connected()
    assert session._rt_attach_pending is False
    assert session._rt_holders == 1
    # Exactly one subscribe: the replay's re-issue. The deferred pass is a
    # no-op for a line that was never refused.
    assert len(win._p28_subs) == baseline + 1


# ── (e) AC-D88.1 — the dead replay is gone ──────────────────────────────────


def test_p28_t2_05_dead_replay_absent_everywhere():
    assert not hasattr(RealtimeBarsManager, "replay_all")

    needles = ("rt_manager." + "replay_all",
               "RealtimeBarsManager." + "replay_all")
    hits = []
    for subtree in ("ui", "ibkr", "tests"):
        for path in sorted((ROOT / subtree).rglob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for needle in needles:
                if needle in text:
                    hits.append(f"{path.relative_to(ROOT)}: {needle}")
    assert hits == []


# ── (f) AC-D84.3 — one function, two call sites ─────────────────────────────


def test_p28_t2_06_one_seam_serves_both_managers():
    assert market_data.require_api_ready is error_codes.require_api_ready
    assert realtime_bars.require_api_ready is error_codes.require_api_ready

    src = inspect.getsource(MarketDataManager._require_api_ready)
    assert "require_api_ready(self.client)" in src
    assert "hasattr" not in src, "the body moved; the manager only delegates"

    assert list(
        inspect.signature(MarketDataManager._require_api_ready).parameters
    ) == ["self"]

    client = _ReadinessClient(api_ready=False)
    md = MarketDataManager(client)
    with pytest.raises(IBKRNotReady) as md_exc:
        md.req_historical_data(contract=Contract())
    with pytest.raises(IBKRNotReady) as seam_exc:
        error_codes.require_api_ready(client)
    with pytest.raises(IBKRNotReady):
        RealtimeBarsManager(client).subscribe("AAPL", Contract())

    assert type(md_exc.value) is error_codes.IBKRNotReady
    assert str(md_exc.value) == str(seam_exc.value) == (
        "IBKR API not ready (handshake pending)"
    )


# ── (g) AC-P28-02-3 — the flag's lifetime ───────────────────────────────────


def test_p28_t2_07_attach_flag_defaults_false_and_dies_with_session(win_factory):
    win = win_factory()
    session = win.get_or_create_session("AAPL")
    assert session._rt_attach_pending is False

    session._rt_attach_pending = True
    session.teardown()
    assert session._rt_attach_pending is False


# ── (h) The two named re-baselines (supporting AC-D88.1) ────────────────────


def _module_functions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_p28_t2_08_named_rebaselines():
    streaming = ROOT / "tests" / "test_p7_w4_streaming.py"
    assert RETIRED_STREAMING_ID not in _module_functions(streaming)

    invariant = ROOT / "tests" / "test_qt_app_import_invariant.py"
    tree = ast.parse(invariant.read_text(encoding="utf-8"))
    streaming_ids = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "STREAMING_IDS"
            for t in node.targets
        ):
            streaming_ids = ast.literal_eval(node.value)
    assert streaming_ids is not None
    assert len(streaming_ids) == 12, "the id tuple has twelve entries"
    assert RETIRED_STREAMING_ID not in streaming_ids
