"""P7-W1 (S-P7-2): same-chart reload coalescing, cancel-slot refund,
superseded-162 at debug.

Covers P7-T03 T11..T14 against the task's acceptance criteria. The
transport is a recording fake (no TWS), the bar cache is an in-memory
fake in both namespaces that use it (no DB writes); everything else is
the real window/session/pacing code.
"""

import logging

import pytest

from ibkr.pacing import pacing_manager
from ui.ticker_session import TickerSession


# ── Fakes ────────────────────────────────────────────────────────────────────

class RecordingTransport:
    """Stand-in for MarketDataManager: hands out reqIds, records everything."""

    def __init__(self):
        self.requests: list = []  # (req_id, kwargs)
        self.cancels: list = []  # req_id
        self._next = 1000

    def req_historical_data(self, contract, **kwargs):
        self._next += 1
        self.requests.append((self._next, dict(kwargs)))
        return self._next

    def cancel_historical_data(self, req_id: int) -> None:
        self.cancels.append(req_id)


class FakeBarCache:
    """In-memory mode-aware bar store (mirrors the BarCache call shape)."""

    store: dict = {}

    @classmethod
    def _key(cls, symbol, timeframe, ext_hours):
        return (symbol, timeframe, bool(ext_hours))

    @classmethod
    def save_bars(cls, bars, ext_hours=True):
        if not bars:
            return
        key = cls._key(bars[0].symbol, bars[0].timeframe, ext_hours)
        bucket = cls.store.setdefault(key, {})
        for bar in bars:
            bucket[bar.ts] = bar

    @classmethod
    def get_bars(cls, symbol, timeframe, ext_hours=True):
        bucket = cls.store.get(cls._key(symbol, timeframe, ext_hours), {})
        return [bucket[ts] for ts in sorted(bucket)]

    @classmethod
    def prune(cls, symbol, timeframe, ext_hours=True, keep=5000):
        bucket = cls.store.get(cls._key(symbol, timeframe, ext_hours), {})
        for ts in sorted(bucket)[:-keep]:
            del bucket[ts]

    @classmethod
    def reset(cls):
        cls.store = {}


class StubStatusBar:
    def __init__(self):
        self.messages: list = []

    def showMessage(self, text, timeout=0):
        self.messages.append(str(text))

    def currentMessage(self):
        return self.messages[-1] if self.messages else ""


class StubHost:
    """Minimal TickerSession host (routing table + transport + status)."""

    def __init__(self):
        self.md_manager = RecordingTransport()
        self.status_bar = StubStatusBar()
        self.routes: dict = {}

    def _register_req_id(self, req_id, session):
        self.routes[req_id] = session

    def _unregister_req_id(self, req_id):
        self.routes.pop(req_id, None)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def window(qapp, monkeypatch):
    """A real MainWindow with the socket reader stubbed and a fake transport."""
    from ibkr.client import IBApiClient
    from ui import main_window as mw_mod
    from ui import ticker_session as ts_mod

    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    # RT attach is orthogonal to the wave assertions; keep it deterministic
    # (a load landing exactly on a period boundary would otherwise attach).
    monkeypatch.setattr(
        TickerSession, "ensure_rt_subscribed", lambda self: 9999
    )
    monkeypatch.setattr(ts_mod, "BarCache", FakeBarCache)
    monkeypatch.setattr(mw_mod, "BarCache", FakeBarCache)
    FakeBarCache.reset()

    win = mw_mod.MainWindow()
    fake = RecordingTransport()
    win.md_manager = fake
    return win


@pytest.fixture
def session_host():
    pacing_manager.reset_for_tests()
    yield StubHost()
    pacing_manager.reset_for_tests()


# ── T11: identical reload coalesces ──────────────────────────────────────────

def test_p7_t11_identical_reload_coalesces(window):
    """An identical-triple reload mid-wave cancels nothing, bumps no
    generation, spends no new reqId, and the wave still completes."""
    window.load_chart("AAPL", "5 mins", True)
    session = window.get_or_create_session("AAPL")
    inflight = set(session._history_req_ids)
    assert inflight, "precondition: the first load must leave a wave in flight"
    generation = session._history_generation
    spent = len(window.md_manager.requests)

    window.load_chart("AAPL", "5 mins", True)

    assert window.md_manager.cancels == []
    assert session._history_generation == generation
    assert set(session._history_req_ids) == inflight
    assert len(window.md_manager.requests) == spent

    for req_id in sorted(inflight):
        window._on_historical_data_end(req_id)
    assert session._history_req_ids == set()
    assert window.md_manager.cancels == []


# ── T12: different symbol still fences ───────────────────────────────────────

def test_p7_t12_different_symbol_cancels_and_fences(window):
    """Loading a different symbol cancels the old wave, advances the new
    session's generation, and late events for old reqIds are ignored."""
    window.load_chart("AAPL", "5 mins", True)
    aapl = window.get_or_create_session("AAPL")
    old_reqs = set(aapl._history_req_ids)
    assert old_reqs, "precondition: AAPL wave must be in flight"
    old_req = next(iter(old_reqs))

    window.load_chart("MSFT", "5 mins", True)
    msft = window.get_or_create_session("MSFT")

    assert set(window.md_manager.cancels) >= old_reqs
    assert aapl._history_req_ids == set()
    assert msft._history_generation == 1  # 0 -> 1 on the genuine new wave
    assert msft._history_req_ids, "the MSFT wave must be in flight"

    tracked = set(msft._history_req_ids)
    window._on_historical_data_end(old_req)  # late end marker: ignored
    window._on_historical_bar(old_req, object())  # late bar: ignored
    assert set(msft._history_req_ids) == tracked


# ── T13: pre-issue refund vs post-issue keep ─────────────────────────────────

def test_p7_t13_pre_issue_refund_post_issue_keep(session_host):
    """Cancelling a pre-issue reqId frees exactly its pacing slot; a
    post-issue cancel frees nothing."""
    pacing_manager.record_historical_slot()
    pacing_manager.record_historical_slot()
    assert len(pacing_manager._hist_times) == 2

    session = TickerSession("TST", session_host)
    session._register_history_request(101)  # pre-issue: never reached TWS
    session._register_history_request(102)
    session.mark_history_request_issued(102)  # post-issue: reached TWS

    session._cancel_history_requests()

    assert set(session_host.md_manager.cancels) == {101, 102}
    assert len(pacing_manager._hist_times) == 1
    assert session.is_superseded(101)
    assert session.is_superseded(102)

    # A refund with an empty budget is a no-op — never inflates the bound.
    pacing_manager.reset_for_tests()
    assert pacing_manager.refund_historical_slot() is False
    assert len(pacing_manager._hist_times) == 0


# ── T14: superseded 162 at debug, genuine 162 unchanged ──────────────────────

def test_p7_t14_superseded_162_debug_genuine_162_surfaced(window, caplog):
    """A 162 for a superseded reqId is debug-only with no status-bar error;
    a 162 on a live wave reqId keeps warning + status-bar + retry."""
    window.load_chart("AAPL", "5 mins", True)
    aapl = window.get_or_create_session("AAPL")
    old_reqs = set(aapl._history_req_ids)
    assert old_reqs
    old_req = next(iter(old_reqs))

    window.load_chart("MSFT", "5 mins", True)  # supersedes the AAPL reqIds
    msft = window.get_or_create_session("MSFT")
    live_req = next(iter(msft._history_req_ids))
    window.status_bar.clearMessage() if hasattr(
        window.status_bar, "clearMessage"
    ) else None
    baseline = window.status_bar.currentMessage()

    caplog.set_level(logging.DEBUG, logger="ui.main_window")
    window._on_error(old_req, 162, "Historical data request pacing violation")

    assert window.status_bar.currentMessage() == baseline
    assert any(
        r.name == "ui.main_window"
        and r.levelno == logging.DEBUG
        and str(old_req) in r.getMessage()
        for r in caplog.records
    )

    window._on_error(live_req, 162, "Historical data request pacing violation")

    assert "162" in window.status_bar.currentMessage()
    assert live_req not in msft._history_req_ids
    assert len(msft._retried_plans) == 1  # retry-once path taken
