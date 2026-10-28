"""P7-T07 (P7-W4): streaming correctness close-out — regression net.

Proves the W1-W3 waves changed none of the streaming behaviour:

- T11: reconnect replays subscriptions with rebound reqIds; stream health
  returns through its documented transitions; no bar is duplicated or lost.
- T12: primed aggregators survive a tight tick burst — every tick accounted
  exactly once in order, forming candle reflects primed history (D27.9).
- T13: every pacing path in this task's footprint defers via PacingExceeded
  plus QTimer.singleShot (or an equivalent armed QTimer) and none blocks.

Scope note: the row-subscription deferral *inside* ``ui/watchlist_panel.py``
(Q-45, landed) is outside this task's read footprint, so it is not
re-asserted here — only the window/panel seam files in this task's footprint
are scanned. All behaviour below is driven through the real production code
(``TickerSession``, ``RealtimeBarsManager``, ``StreamHealth``, and the
``MainWindow`` pacing handlers invoked unbound on stubs) with fake transports.
"""

import ast
import os
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from data.bar_aggregator import TIMEFRAME_SECONDS
from ibkr.pacing import PacingExceeded
from ibkr.realtime_bars import RealtimeBarsManager
from ibkr.stream_health import StreamHealth, StreamState
from ibkr.subscription_manager import RT_BARS, S0_TICKS
from ui import ticker_session as ticker_session_mod
from ui.ticker_session import TickerSession


_APP = QApplication.instance() or QApplication([])


# ── Fakes ────────────────────────────────────────────────────────────────────

class FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, msg, ms=0):
        self.messages.append((msg, ms))


class FakeRTManager:
    """Fake 5-sec realtime transport that records every subscription reqId."""

    def __init__(self, first_id=1000):
        self._next = first_id
        self.subs = {}          # reqId -> (symbol, contract)
        self.unsubscribed = []

    def subscribe(self, symbol, contract):
        self._next += 1
        self.subs[self._next] = (symbol, contract)
        return self._next

    def unsubscribe(self, req_id):
        self.unsubscribed.append(req_id)
        self.subs.pop(req_id, None)


class FakeSubManager:
    def __init__(self):
        self.entries = {}
        self.replay_calls = []

    def subscribe(self, symbol, req_id, kind, reissue=None, rebind=None):
        self.entries[req_id] = (symbol, kind, reissue, rebind)

    def unsubscribe(self, req_id):
        self.entries.pop(req_id, None)

    def replay_all(self, include_types=None):
        self.replay_calls.append(include_types)
        rebound = {}
        for req_id, (symbol, kind, reissue, rebind) in list(self.entries.items()):
            if include_types is not None and kind not in include_types:
                continue
            new_id = reissue()
            rebound[req_id] = new_id
            if rebind is not None:
                rebind(new_id)
        return rebound


class FakeMDManager:
    """Fake historical transport: raising or issuing on demand."""

    def __init__(self):
        self.mode = "raise"     # "raise" | "issue"
        self.wait = 1.5
        self._next = 5000
        self.requests = []
        self.cancelled = []

    def req_historical_data(self, **kwargs):
        self.requests.append(kwargs)
        if self.mode == "raise":
            raise PacingExceeded(self.wait)
        self._next += 1
        return self._next

    def cancel_historical_data(self, req_id):
        self.cancelled.append(req_id)


class FakeIbapiClient:
    """Fake ibapi client recording reqRealTimeBars traffic."""

    def __init__(self):
        self.rt_requests = []   # (reqId, symbol)
        self.rt_cancels = []

    def reqRealTimeBars(self, req_id, contract, barSize, whatToShow,
                        useRTH, opts):
        self.rt_requests.append((req_id, getattr(contract, "symbol", "?")))

    def cancelRealTimeBars(self, req_id):
        self.rt_cancels.append(req_id)


def make_host(symbol="AAPL"):
    """Minimal duck-typed host for TickerSession (no MainWindow)."""
    host = SimpleNamespace()
    host.rt_manager = FakeRTManager()
    host.sub_manager = FakeSubManager()
    host.md_manager = FakeMDManager()
    host.status_bar = FakeStatusBar()
    host._req_to_session = {}
    host._register_req_id = lambda req_id, sess: host._req_to_session.__setitem__(req_id, sess)
    host._unregister_req_id = lambda req_id: host._req_to_session.pop(req_id, None)
    host.prices = {}
    host._record_symbol_price = lambda sym, px: host.prices.__setitem__(sym, px)
    host.prime_completions = []
    host._on_session_prime_complete = lambda sess: host.prime_completions.append(sess.symbol)
    host.wave_completions = []
    host._on_session_wave_complete = lambda sess: host.wave_completions.append(sess.symbol)
    host._on_session_prime_timeout = lambda sess: None
    host._on_session_wave_timeout = lambda sess: None
    return host


def ibkr_day_ts(date_str, hhmmss):
    """Epoch seconds for a UTC date+time (deterministic test clock)."""
    dt = datetime.strptime(f"{date_str} {hhmmss}", "%Y%m%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    return int(dt.timestamp())


def ibkr_date(ts):
    """IBKR historical-bar date string for an epoch (what parse_ibkr_date reads)."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y%m%d %H:%M:%S")


def hist_bar(ts, o, h, l, c, v):
    return SimpleNamespace(date=ibkr_date(ts), open=o, high=h, low=l,
                           close=c, volume=v)


def mid_period_ts(timeframe="5 mins"):
    """A fixed timestamp 90 s into a 300 s-aligned period (span >= 5 s)."""
    base = 1_700_000_000
    step = TIMEFRAME_SECONDS[timeframe]
    start = base - (base % step)
    return start + 90


# ── T11: reconnect replay ────────────────────────────────────────────────────

def test_p7_t07_t11_replay_rebinds_reqids_without_bar_loss_or_dupes():
    """Subscribe, drop mid-stream, replay: rebound ids, bar-set preserved."""
    host = make_host()
    sess = TickerSession("AAPL", host)
    agg = sess.aggregator_for("5 mins")
    period = TIMEFRAME_SECONDS["5 mins"]
    now = mid_period_ts()
    ps = agg.period_start(now)

    rid1 = sess.ensure_rt_subscribed()
    assert sess._rt_req_id == rid1
    assert sess.stream_health.state == StreamState.AWAITING_FIRST_BAR

    # Pre-drop stream: three in-period 5-sec bars -> one forming candle.
    pre = [
        (ps + 10, 100.0, 100.5, 99.5, 100.25, 100.0),
        (ps + 20, 100.25, 100.75, 100.0, 100.5, 200.0),
        (ps + 30, 100.5, 101.0, 100.25, 100.0, 300.0),
    ]
    for ts, o, h, l, c, v in pre:
        sess.on_realtime_bar(rid1, ts, o, h, l, c, v)
    assert sess.stream_health.is_live
    assert len(sess.get_bars("5 mins")) == 1
    snapshot = [(b.ts, b.open, b.high, b.low, b.close, b.volume)
                for b in sess.get_bars("5 mins")]

    # Transport drop + reconnect replay through the session's replay hook.
    rid2 = sess._reissue_rt()
    assert rid2 != rid1
    assert host._req_to_session.get(rid2) is sess
    assert rid1 not in host._req_to_session

    # A stale bar on the pre-drop reqId must be ignored (no dupe, no loss).
    sess.on_realtime_bar(rid1, ps + 40, 100.0, 100.0, 100.0, 100.0, 999.0)
    assert [(b.ts, b.open, b.high, b.low, b.close, b.volume)
            for b in sess.get_bars("5 mins")] == snapshot

    # Post-reconnect bars on the rebound reqId extend the series exactly once.
    sess.on_realtime_bar(rid2, ps + 40, 100.0, 100.5, 99.75, 100.5, 400.0)
    sess.on_realtime_bar(rid2, ps + 50, 100.5, 101.5, 100.5, 101.0, 500.0)
    bars = sess.get_bars("5 mins")
    assert len(bars) == 1  # same forming candle, extended — never duplicated
    forming = bars[0]
    assert forming.open == 100.0            # primed by the pre-drop stream
    assert forming.high == 101.5
    assert forming.low == 99.5
    assert forming.close == 101.0
    assert forming.volume == 100.0 + 200.0 + 300.0 + 400.0 + 500.0
    assert forming.volume < 100.0 + 200.0 + 300.0 + 400.0 + 500.0 + 999.0


def test_p7_t07_t11_manager_replay_rebounds_every_subscription():
    """RealtimeBarsManager.replay_all resubscribes every stream with fresh ids."""
    client = FakeIbapiClient()
    mgr = RealtimeBarsManager(client)
    from ibapi.contract import Contract
    c1, c2 = Contract(), Contract()
    c1.symbol, c2.symbol = "AAPL", "ES"
    id1 = mgr.subscribe("AAPL", c1)
    id2 = mgr.subscribe("ES", c2)
    assert id1 != id2
    assert len(client.rt_requests) == 2

    mgr.replay_all()

    assert len(client.rt_requests) == 4
    rebound = [r for r in client.rt_requests[2:]]
    assert {r[1] for r in rebound} == {"AAPL", "ES"}
    assert {r[0] for r in rebound}.isdisjoint({id1, id2})


def test_p7_t07_t11_health_reaches_live_only_on_first_post_reconnect_bar():
    """FAILED -> resubscribe -> awaiting; live only on the first live bar."""
    host = make_host()
    sess = TickerSession("AAPL", host)
    sess.aggregator_for("5 mins")

    rid1 = sess.ensure_rt_subscribed()
    assert sess.stream_health.state == StreamState.AWAITING_FIRST_BAR

    # A bar on an unknown (stale/foreign) reqId must not flip health to live.
    sess.on_realtime_bar(rid1 + 999, 1_700_000_000, 1.0, 1.0, 1.0, 1.0, 10.0)
    assert not sess.stream_health.is_live

    sess.on_realtime_bar(rid1, 1_700_000_000, 1.0, 1.0, 1.0, 1.0, 10.0)
    assert sess.stream_health.is_live

    # Failure -> backoff-preserving resubscribe -> awaiting again.
    sess.stream_health.mark_failed(2105, "HMDS query returned no data")
    assert sess.stream_health.state == StreamState.FAILED
    rid2 = sess.resubscribe_rt()
    assert rid2 != rid1
    assert sess.stream_health.state == StreamState.AWAITING_FIRST_BAR
    assert not sess.stream_health.is_live

    sess.on_realtime_bar(rid1, 1_700_000_005, 1.0, 1.0, 1.0, 1.0, 10.0)
    assert not sess.stream_health.is_live  # stale id cannot revive the stream
    sess.on_realtime_bar(rid2, 1_700_000_005, 1.0, 1.0, 1.0, 1.5, 10.0)
    assert sess.stream_health.is_live


# ── T12: burst integrity over primed aggregators ──────────────────────────────

def test_p7_t07_t12_burst_keeps_priming_with_exact_once_ordering():
    """Prime, then a tight cross-boundary burst: no drops, no lates."""
    host = make_host()
    sess = TickerSession("AAPL", host)
    agg = sess.aggregator_for("5 mins")
    period = TIMEFRAME_SECONDS["5 mins"]
    now = mid_period_ts()
    ps = agg.period_start(now)
    span = now - ps
    assert span >= 5

    host.md_manager.mode = "issue"
    assert sess.prime_aggregator(object(), "5 mins", now, False) is True
    prime_req = sess._prime_req_id
    assert prime_req is not None
    last_call = host.md_manager.requests[-1]
    assert last_call["bar_size"] in ("5 secs", "1 min")
    assert last_call["duration"].endswith(" S")

    # Priming history inside the current period (ascending, D27.9 replay).
    prime = [
        (ps + 10, 100.0, 100.5, 99.5, 100.25, 100.0),
        (ps + 30, 100.25, 100.5, 100.0, 100.5, 200.0),
        (ps + 50, 100.5, 101.0, 100.25, 100.75, 300.0),
        (ps + 70, 100.75, 101.25, 100.5, 101.0, 400.0),
    ]
    for ts, o, h, l, c, v in prime:
        sess.on_historical_bar(prime_req, hist_bar(ts, o, h, l, c, v))
    sess.on_historical_data_end(prime_req)
    assert host.prime_completions == ["AAPL"]

    formed = sess.get_bars("5 mins")
    assert len(formed) == 1
    assert (formed[0].open, formed[0].high, formed[0].low,
            formed[0].close, formed[0].volume) == (100.0, 101.25, 99.5,
                                                  101.0, 1000.0)

    # Tight ascending burst crossing the period boundary (no gaps, no lates).
    rid = sess.ensure_rt_subscribed()
    burst = []
    ts = now + 5
    px = 101.0
    step = 0
    while ts <= ps + period + 60:
        px += 0.25
        burst.append((ts, px, px + 0.5, px - 0.25, px + 0.25, 50.0))
        ts += 5
        step += 1
    for ts, o, h, l, c, v in burst:
        sess.on_realtime_bar(rid, ts, o, h, l, c, v)

    pushed_ts = [t for t, *_ in prime] + [t for t, *_ in burst]
    pushed_vol = sum(v for *_, v in prime) + sum(v for *_, v in burst)
    expected_periods = {agg.period_start(t) for t in pushed_ts}

    series = sess.get_bars("5 mins")
    assert [b.ts for b in series] == sorted(b.ts for b in series)
    assert len(series) == len(expected_periods)
    assert sum(b.volume for b in series) == pytest.approx(pushed_vol)

    # Priming survival: the first candle still opens on primed history and
    # carries every primed tick plus the in-period burst ticks in order.
    first = series[0]
    assert first.open == 100.0
    in_first = [(t, o, h, l, c, v) for (t, o, h, l, c, v) in prime + burst
                if agg.period_start(t) == agg.period_start(ps + 10)]
    assert first.close == in_first[-1][4]
    assert first.high == max(r[2] for r in in_first)
    assert first.low == min(r[3] for r in in_first)
    assert first.volume == pytest.approx(sum(r[5] for r in in_first))

    # Forming candle reflects the burst tail in order.
    assert series[-1].close == burst[-1][4]
    assert sess._last_chart_price == burst[-1][4]


# ── T13: pacing paths defer, never block ──────────────────────────────────────

PACING_PATH_FILES = ("ui/ticker_session.py", "ui/main_window.py")
_DEFERRAL_MARKERS = ("singleShot", ".start(", "_schedule_wave_continuation")


def _repo_path(rel):
    root = os.path.dirname(os.path.dirname(
        os.path.abspath(ticker_session_mod.__file__)))
    return os.path.join(root, *rel.split("/"))


def _function_sources(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    return {n.name: ast.get_source_segment(src, n)
            for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def test_p7_t07_t13_no_blocking_sleep_on_any_pacing_path():
    """Zero blocking-sleep primitives anywhere in the footprint files."""
    offenders = []
    for rel in PACING_PATH_FILES:
        path = _repo_path(rel)
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("sleep", "msleep", "usleep")):
                offenders.append(f"{rel}:{node.lineno}")
    assert offenders == []


def test_p7_t07_t13_every_pacing_handler_defers_without_blocking():
    """Each PacingExceeded handler defers (singleShot/timer/continuation)."""
    unpaced = []
    for rel in PACING_PATH_FILES:
        for name, src in _function_sources(_repo_path(rel)).items():
            if ("PacingExceeded" in src and "except" in src
                    and "import" not in src.splitlines()[0]):
                if not any(m in src for m in _DEFERRAL_MARKERS):
                    unpaced.append(f"{rel}::{name}")
    assert unpaced == []


def test_p7_t07_t13_wave_continuation_defers_and_resumes():
    """Wave issue pacing-limited -> continuation timer + watchdog; then resumes."""
    from ibkr.pacing import pacing_manager
    host = make_host()
    sess = TickerSession("AAPL", host)
    plan = SimpleNamespace(endDateTime="", bar_size="5 mins", duration="1 D")

    sess.queue_wave_plans([plan], object(), "5 mins", False)

    assert sess._wave_continue_timer.isActive()
    assert sess._wave_plan_queue == [plan]  # nothing issued, nothing lost
    window = float(getattr(pacing_manager, "_hist_window", 600.0))
    assert sess._history_wave_bound_ms >= int(1.5 * 1000 + window * 1000 / 20)
    assert any("pacing-limited" in m for m, _ in host.status_bar.messages)

    host.md_manager.mode = "issue"
    sess._on_wave_continue_timeout()
    assert sess._wave_plan_queue == []
    assert len(sess._history_req_ids) == 1


def test_p7_t07_t13_prime_retry_defers_then_issues():
    """Pacing-limited prime -> one singleShot retry -> issues on retry."""
    fired = []
    orig = QTimer.singleShot
    QTimer.singleShot = lambda ms, fn: fired.append((ms, fn))
    try:
        host = make_host()
        sess = TickerSession("AAPL", host)
        sess.aggregator_for("5 mins")
        now = mid_period_ts()

        assert sess.prime_aggregator(object(), "5 mins", now, False) is True
        assert sess._prime_retry_pending is True
        assert sess._prime_reserved is True
        assert len(fired) == 1
        ms, fn = fired[0]
        assert ms >= 1000
        assert getattr(fn, "__self__", None) is sess
        assert getattr(fn, "__func__", None) is TickerSession._on_prime_retry

        host.md_manager.mode = "issue"
        sess._on_prime_retry()
        assert sess._prime_req_id is not None
        assert sess._prime_reserved is False
        assert sess._prime_retry_pending is False
    finally:
        QTimer.singleShot = orig


def test_p7_t07_t13_prime_retry_fail_open_counts_skip():
    """Retry still pacing-limited -> fail open, counted skip, live feed call."""
    host = make_host()
    sess = TickerSession("AAPL", host)
    sess.aggregator_for("5 mins")
    now = mid_period_ts()

    assert sess.prime_aggregator(object(), "5 mins", now, False) is True
    sess._on_prime_retry()  # transport still throttled

    assert sess._prime_skipped_count == 1
    assert sess._prime_reserved is False
    assert sess._prime_retry_pending is False
    assert host.prime_completions == ["AAPL"]


def test_p7_t07_t13_live_feed_attach_defers_via_singleshot():
    """Pacing-limited RT subscribe in the attach path defers, never blocks."""
    from ui.main_window import MainWindow

    fired = []
    orig = QTimer.singleShot
    QTimer.singleShot = lambda ms, fn: fired.append((ms, fn))
    try:
        session = SimpleNamespace()
        session.ensure_rt_subscribed_calls = 0

        def _raise():
            session.ensure_rt_subscribed_calls += 1
            raise PacingExceeded(3.0)

        session.ensure_rt_subscribed = _raise
        stub = SimpleNamespace(
            status_bar=FakeStatusBar(),
            get_or_create_session=lambda symbol: session,
            _retry_attach_live_feed=lambda symbol, contract: None,
        )
        MainWindow._attach_live_feed(stub, "AAPL", object())

        assert session.ensure_rt_subscribed_calls == 1
        assert len(fired) == 1
        assert fired[0][0] == 3000
    finally:
        QTimer.singleShot = orig


def test_p7_t07_t13_replay_all_defers_via_singleshot():
    """Pacing-limited reconnect replay defers the whole replay, never blocks."""
    from ui.main_window import MainWindow

    fired = []
    orig = QTimer.singleShot
    QTimer.singleShot = lambda ms, fn: fired.append((ms, fn))
    try:
        sub = FakeSubManager()
        calls = {"n": 0}
        real_replay = sub.replay_all

        def _flaky(include_types=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise PacingExceeded(2.0)
            return real_replay(include_types)

        sub.replay_all = _flaky
        stub = SimpleNamespace(
            status_bar=FakeStatusBar(),
            sub_manager=sub,
            _replay_subscriptions=lambda: None,
        )
        MainWindow._replay_subscriptions(stub)
        assert len(fired) == 1
        assert fired[0][0] == 2000

        MainWindow._replay_subscriptions(stub)
        assert sub.replay_calls == [{RT_BARS, S0_TICKS}]
    finally:
        QTimer.singleShot = orig


def test_p7_t07_t13_backoff_progresses_and_retry_preserves_it():
    """Stream-health backoff 5->10->20->40->60(cap); retry never resets it."""
    h = StreamHealth()
    assert [h.next_retry_delay_s() for _ in range(6)] == [5.0, 10.0, 20.0,
                                                          40.0, 60.0, 60.0]

    host = make_host()
    sess = TickerSession("AAPL", host)
    sess.aggregator_for("5 mins")
    sess.ensure_rt_subscribed()
    sess.stream_health.mark_failed(2105, "no data")
    before = sess.stream_health.retry_attempt
    sess.stream_health.next_retry_delay_s()
    sess.resubscribe_rt()  # Fix-B: retry path never resets the counter
    assert sess.stream_health.retry_attempt == before + 1
    assert sess.stream_health.state == StreamState.AWAITING_FIRST_BAR
