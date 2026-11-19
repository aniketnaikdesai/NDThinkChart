"""P25-T2 / D67 — the forming ``1 week`` / ``1 month`` candle.

The two calendar-bucketed timeframes get a real source for their open
period: the **current-period row the chart already renders** (S-P25-1) is
adopted as the aggregator's base, live/primed bars extend it, and the
period's head coverage decides one transient ``Bar.partial`` flag
(S-P25-3) which the view forwards as one ``set_partial`` directive
(S-P25-2).

AC map (the wave file's ``tests`` array):

* ``P25-T2-AC1`` — a cached current-period row built as the aggregate of an
  explicit component list *is* the forming candle: its OHLCV equal that
  aggregate, ``partial`` is False and no ``set_partial`` is emitted.
* ``P25-T2-AC2`` — an empty/pruned cache with a prime injected through
  ``TickerSession.on_historical_bar`` → ``BarAggregator.push``: the values
  are exactly the injected bars' aggregate, ``partial`` is True and exactly
  one ``set_partial`` names the forming ``ts``.
* ``P25-T2-AC3`` — every bar at or after the period's first session open
  (the period begins today): full values, ``partial`` False, no marker.
* ``P25-T2-AC4`` — a current-period base skips the prime (fresh **and**
  ``retrying=True``, no request, caller may attach the live feed); without
  a base the issued pair is inside the accepted set and no outside pair is
  ever issued.
* ``P25-T2-AC5`` / ``-REPLAY`` — a live bar in the next bucket appends
  exactly one candle and drives the envelope's one marker; adoption keeps
  the replay guard (a redelivered 5-second bar is not re-counted while a
  newer tick merges).
* ``P25-T2-AC6`` / ``-SEAM`` — a full replace whose last row is partial
  emits exactly one ``set_partial`` naming that row, after the rows; the
  window's ``_wall_now`` wiring is late-bound and the session default is
  ``time.time``.

Deterministic clock: 2026-06-01 is a Monday **and** the first of the month,
so both calendar buckets begin "today" — which is what AC3's
"period begins today" leg needs. ``session._wall_now`` is set explicitly
per case.

``parse_ibkr_date`` reads a 10-digit epoch string, which is what ``_hist``
hands it (the same shape ``test_d27_aggregator_priming`` uses).
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication

from data.models import Bar
from ibkr.pacing import PacingExceeded
from services.market_calendar import first_session_open
from ui.lwc_view import LwcChartView
from ui.ticker_session import TickerSession

_APP = QApplication.instance() or QApplication([])

# 2026-06-01 00:00 ET — Monday and month start (week + month bucket).
P = 1_780_286_400
RTH_OPEN = 1_780_320_600        # 2026-06-01 09:30 ET
ETH_OPEN = 1_780_300_800        # 2026-06-01 04:00 ET
MON_1200 = 1_780_329_600        # 2026-06-01 12:00 ET
TUE_1000 = 1_780_408_800        # 2026-06-02 10:00 ET
TUE_1001 = 1_780_408_860
TUE_1002 = 1_780_408_920
WED_1200 = 1_780_502_400        # 2026-06-03 12:00 ET
NEXT_MON = 1_780_891_200        # 2026-06-08 00:00 ET (next week bucket)
NEXT_MON_RTH = 1_780_925_400    # 2026-06-08 09:30 ET
NEXT_MON_0935 = 1_780_925_700   # 2026-06-08 09:35 ET
NEXT_MONTH = 1_782_878_400      # 2026-07-01 00:00 ET (next month bucket)
NEXT_MONTH_RTH = 1_782_912_600  # 2026-07-01 09:30 ET
NEXT_MONTH_0935 = 1_782_912_900  # 2026-07-01 09:35 ET
LATE_JUNE = 1_782_403_200       # 2026-06-25 12:00 ET (span > 1 D)
LATE_WEEK = 1_782_316_800       # 2026-06-24 12:00 ET (span > 1 D)

CALENDAR_TFS = ("1 week", "1 month")

# (period_start, first session open, 5 min after that open) for the *next*
# bucket of each timeframe — the rollover fixtures.
NEXT_PERIOD = {
    "1 week": (NEXT_MON, NEXT_MON_RTH, NEXT_MON_0935),
    "1 month": (NEXT_MONTH, NEXT_MONTH_RTH, NEXT_MONTH_0935),
}

# Explicit component lists. Their aggregate is computed by ``_aggregate`` —
# never by the production aggregator — so AC1/AC2 compare two independent
# computations.
COMPONENT_BARS = [
    (RTH_OPEN, 100.0, 101.0, 99.5, 100.5, 1000.0),
    (RTH_OPEN + 300, 100.5, 102.0, 100.0, 101.0, 2000.0),
    (WED_1200 - 60, 101.0, 101.5, 98.0, 99.0, 500.0),
]
PRIME_BARS = [
    (TUE_1000, 100.0, 101.0, 99.0, 100.5, 1000.0),
    (TUE_1001, 100.5, 102.0, 100.0, 101.0, 2000.0),
    (TUE_1002, 101.0, 101.5, 98.0, 99.0, 500.0),
]


# ── harness (same pattern as tests/test_p7_w4_streaming.py) ────────────────


class _FakeRTManager:
    def __init__(self):
        self.subs = {}
        self.unsubscribed = []

    def subscribe(self, symbol, contract):
        req_id = 9000 + len(self.subs)
        self.subs[req_id] = symbol
        return req_id

    def unsubscribe(self, req_id):
        self.unsubscribed.append(req_id)
        self.subs.pop(req_id, None)


class _FakeSubManager:
    def subscribe(self, symbol, req_id, kind, reissue=None, rebind=None):
        return None

    def unsubscribe(self, req_id):
        return None


class _FakeMDManager:
    """Records ``req_historical_data`` calls; can reject the next one."""

    def __init__(self):
        self.requests: list[dict] = []
        self.reject_next = None
        self._next = 7000

    def req_historical_data(self, **kwargs):
        self.requests.append(kwargs)
        if self.reject_next is not None:
            exc, self.reject_next = self.reject_next, None
            raise exc
        self._next += 1
        return self._next


def make_host():
    """Minimal duck-typed host for ``TickerSession`` (no MainWindow)."""
    host = SimpleNamespace()
    host.rt_manager = _FakeRTManager()
    host.sub_manager = _FakeSubManager()
    host.md_manager = _FakeMDManager()
    host._req_to_session = {}
    host._register_req_id = lambda req_id, sess: host._req_to_session.__setitem__(req_id, sess)
    host._unregister_req_id = lambda req_id: host._req_to_session.pop(req_id, None)
    host._on_session_prime_complete = lambda sess: None
    host._on_session_wave_complete = lambda sess: None
    host._on_session_prime_timeout = lambda sess: None
    host._on_session_wave_timeout = lambda sess: None
    return host


def _new_session(symbol="SPY"):
    host = make_host()
    session = TickerSession(symbol, host)
    # No live contract resolution in tests.
    session._wave_contract = object()
    return session, host


def _hist(ts, o, h, l, c, v):
    """IBKR historical bar stand-in (``parse_ibkr_date``: 10-digit epoch)."""
    return SimpleNamespace(date=str(ts), open=o, high=h, low=l, close=c,
                           volume=v)


def _aggregate(components):
    """Independent aggregate of an explicit ``(ts, o, h, l, c, v)`` list."""
    return {
        "open": components[0][1],
        "high": max(row[2] for row in components),
        "low": min(row[3] for row in components),
        "close": components[-1][4],
        "volume": sum(row[5] for row in components),
    }


def _make_view(timeframe):
    view = LwcChartView()
    view.bridge.set_ready(True)
    view.set_timeframe(timeframe)
    return view


def _attach(session, view, timeframe):
    """Wire the two production fan-out signals the window wires."""
    session.bar_updated.connect(view.update_last_bar)
    session.bars_refreshed.connect(
        lambda tf, bars: view.update_bars(bars) if tf == timeframe else None)


def _partial_ops(env):
    if not env:
        return []
    return [op for op in env["ops"] if op.get("op") == "set_partial"]


def _candles_set_op(env):
    assert env is not None, "no envelope was emitted"
    for op in env["ops"]:
        if op.get("op") == "set_bars" and op.get("series") == "candles":
            return op
    raise AssertionError("no candle set_bars op in the envelope")


def _assert_pair_inside_accepted_set(request):
    """AC-D67.3: '5 secs' in [60 S, 3600 S]; '1 min' in [60 S, 1 D]."""
    bar_size = request["bar_size"]
    duration = request["duration"]
    assert isinstance(duration, str) and duration.endswith(" S")
    seconds = int(duration.split()[0])
    if bar_size == "5 secs":
        assert 60 <= seconds <= 3_600
    elif bar_size == "1 min":
        assert 60 <= seconds <= 86_400
    else:  # pragma: no cover - a pair outside the accepted set is a defect
        pytest.fail(f"bar_size outside the accepted set: {bar_size!r}")


def _assert_values(bar, expected):
    assert bar.open == expected["open"]
    assert bar.high == expected["high"]
    assert bar.low == expected["low"]
    assert bar.close == expected["close"]
    assert bar.volume == expected["volume"]


# ── AC1: the cached current-period row is the forming candle ───────────────


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac1_cached_current_period_row_is_the_forming_candle(timeframe):
    session, host = _new_session()
    session._wall_now = lambda: MON_1200
    agg = session.aggregator_for(timeframe)
    view = _make_view(timeframe)
    _attach(session, view, timeframe)

    expected = _aggregate(COMPONENT_BARS)
    row = Bar("SPY", timeframe, P, **expected)
    session.set_bars(timeframe, [row])

    # The rendered row *is* the aggregator's base ...
    assert agg.has_period_base is True
    assert agg.covering_since == P
    assert agg.current_bar().ts == P
    _assert_values(agg.current_bar(), expected)

    # ... the series' forming bar carries it unmarked ...
    forming = session.get_bars(timeframe)[-1]
    _assert_values(forming, expected)
    assert forming.partial is False

    # ... and rendering it emits no marker, with the same values on the wire.
    env = view.bridge.flush()
    assert _partial_ops(env) == []
    candles = _candles_set_op(env)
    assert candles["cols"]["ts"][-1] == P
    for key in ("open", "high", "low", "close"):
        assert candles["cols"][key][-1] == expected[key]
    assert host.md_manager.requests == []  # no prime needed for a base


# ── AC2: a prime-only candle is the aggregate of exactly what was injected ─


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac2_pruned_cache_prime_marks_the_forming_candle(timeframe):
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    session._wave_extended_hours = False
    session.aggregator_for(timeframe)
    view = _make_view(timeframe)
    _attach(session, view, timeframe)

    # Empty/pruned cache: the aggregator has no base, so the prime issues.
    assert session.prime_aggregator(
        object(), timeframe, WED_1200, False) is True
    assert len(host.md_manager.requests) == 1
    _assert_pair_inside_accepted_set(host.md_manager.requests[0])
    req_id = session._prime_req_id
    assert req_id is not None

    # The real write path: TickerSession.on_historical_bar -> push.
    for component in PRIME_BARS:
        session.on_historical_bar(req_id, _hist(*component))

    expected = _aggregate(PRIME_BARS)
    forming = session.get_bars(timeframe)[-1]
    assert forming.ts == P
    assert forming.partial is True
    # Exactly the injected set — never a value from an unmarked window.
    _assert_values(forming, expected)

    assert _partial_ops(view.bridge.flush()) == [
        {"op": "set_partial", "ts": P, "partial": True}]


# ── AC3: "the period begins today" is complete ─────────────────────────────


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac3_period_begins_today_is_complete(timeframe):
    session, host = _new_session()
    session._wall_now = lambda: MON_1200
    session._wave_extended_hours = False
    agg = session.aggregator_for(timeframe)
    view = _make_view(timeframe)
    _attach(session, view, timeframe)

    assert first_session_open(P, MON_1200, False) == RTH_OPEN
    assert session.prime_aggregator(object(), timeframe, MON_1200, False) is True
    req_id = session._prime_req_id

    components = [
        (RTH_OPEN, 100.0, 101.0, 99.0, 100.5, 10.0),
        (RTH_OPEN + 60, 100.5, 101.5, 100.0, 101.0, 20.0),
    ]
    for component in components:
        session.on_historical_bar(req_id, _hist(*component))

    forming = session.get_bars(timeframe)[-1]
    expected = _aggregate(components)
    assert agg.covering_since == RTH_OPEN  # the period's head is covered
    assert forming.partial is False
    _assert_values(forming, expected)
    assert _partial_ops(view.bridge.flush()) == []


def test_ac3_non_calendar_timeframes_are_never_marked():
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    session.aggregator_for("5 mins")
    req_id = session.ensure_rt_subscribed()

    session.on_realtime_bar(req_id, WED_1200, 100.0, 101.0, 99.0, 100.5, 10.0)

    forming = session.get_bars("5 mins")[-1]
    assert forming.timeframe == "5 mins"
    assert forming.partial is False


# ── AC4: the prime is skipped with a base, and only accepted pairs issue ────


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac4_current_period_base_skips_the_prime(timeframe):
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    session.aggregator_for(timeframe)
    expected = _aggregate(PRIME_BARS)
    session.set_bars(
        timeframe, [Bar("SPY", timeframe, P, **expected)])

    assert host.md_manager.requests == []
    # Fresh entry: nothing to fetch, the caller may attach the live feed.
    assert session.prime_aggregator(
        object(), timeframe, WED_1200, False) is False
    assert host.md_manager.requests == []
    # The deferred-retry entry can never resurrect the request either.
    assert session.prime_aggregator(
        object(), timeframe, WED_1200, False, retrying=True) is False
    assert host.md_manager.requests == []


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac4_no_base_issues_only_a_pair_inside_the_accepted_set(timeframe):
    session, host = _new_session()
    now = LATE_JUNE if timeframe == "1 month" else LATE_WEEK
    session._wall_now = lambda: now
    session.aggregator_for(timeframe)

    assert session.prime_aggregator(object(), timeframe, now, False) is True
    assert len(host.md_manager.requests) == 1
    request = host.md_manager.requests[0]
    _assert_pair_inside_accepted_set(request)
    # A week/month span is clamped to 1 D, never the 1-min/7-D pair TWS
    # rejects (error 321) — so no rejected literal is ever issued.
    assert request["bar_size"] == "1 min"
    assert request["duration"] == "86400 S"


def test_ac4_pacing_rejection_defers_then_issues_an_accepted_pair():
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    session.aggregator_for("1 week")

    host.md_manager.reject_next = PacingExceeded(1.0)
    # Pacing-limited: deferred with one retry, nothing issued yet.
    assert session.prime_aggregator(
        object(), "1 week", WED_1200, False) is True
    assert len(host.md_manager.requests) == 1
    _assert_pair_inside_accepted_set(host.md_manager.requests[0])

    # The explicit retry issues a pair still inside the accepted set.
    assert session.prime_aggregator(
        object(), "1 week", WED_1200, False, retrying=True) is True
    assert len(host.md_manager.requests) == 2
    for request in host.md_manager.requests:
        _assert_pair_inside_accepted_set(request)


# ── AC5: rollover appends one candle and drives the one marker ─────────────


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac5_rollover_moves_the_marker_to_the_new_forming_bar(timeframe):
    next_start, _next_open, next_after = NEXT_PERIOD[timeframe]
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    session.aggregator_for(timeframe)
    view = _make_view(timeframe)
    _attach(session, view, timeframe)

    # Mark the old forming candle through the prime path (head uncovered).
    assert session.prime_aggregator(
        object(), timeframe, WED_1200, False) is True
    session.on_historical_bar(
        session._prime_req_id, _hist(TUE_1000, 100.0, 101.0, 99.0, 100.5, 1000.0))
    assert session.get_bars(timeframe)[-1].partial is True
    assert _partial_ops(view.bridge.flush()) == [
        {"op": "set_partial", "ts": P, "partial": True}]

    req_id = session.ensure_rt_subscribed()
    session._wall_now = lambda: next_after
    session.on_realtime_bar(
        req_id, next_after, 105.0, 106.0, 104.0, 105.5, 50.0)

    series = session.get_bars(timeframe)
    assert [bar.ts for bar in series] == [P, next_start]
    assert sum(1 for bar in series if bar.ts == P) == 1  # never duplicated
    assert series[0].volume == 1000.0
    assert series[-1].partial is True

    assert _partial_ops(view.bridge.flush()) == [
        {"op": "set_partial", "ts": next_start, "partial": True}]


@pytest.mark.parametrize("timeframe", CALENDAR_TFS)
def test_ac5_rollover_clears_the_marker_when_the_new_bar_is_complete(timeframe):
    next_start, next_open, _next_after = NEXT_PERIOD[timeframe]
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    session.aggregator_for(timeframe)
    view = _make_view(timeframe)
    _attach(session, view, timeframe)

    assert session.prime_aggregator(
        object(), timeframe, WED_1200, False) is True
    session.on_historical_bar(
        session._prime_req_id, _hist(TUE_1000, 100.0, 101.0, 99.0, 100.5, 1000.0))
    assert _partial_ops(view.bridge.flush()) == [
        {"op": "set_partial", "ts": P, "partial": True}]

    req_id = session.ensure_rt_subscribed()
    # A live bar exactly at the new period's first session open covers the
    # head -> the new forming bar is complete and the old mark is cleared.
    session._wall_now = lambda: next_open
    session.on_realtime_bar(
        req_id, next_open, 105.0, 106.0, 104.0, 105.5, 50.0)

    series = session.get_bars(timeframe)
    assert [bar.ts for bar in series] == [P, next_start]
    assert series[-1].partial is False
    assert _partial_ops(view.bridge.flush()) == [
        {"op": "set_partial", "ts": P, "partial": False}]


def test_ac5_replay_guard_survives_adoption():
    session, host = _new_session()
    session._wall_now = lambda: WED_1200
    agg = session.aggregator_for("1 week")
    req_id = session.ensure_rt_subscribed()

    first_ts = TUE_1000
    session.on_realtime_bar(
        req_id, first_ts, 100.0, 101.0, 99.0, 100.0, 77.0)
    assert agg.current_bar().volume == 77.0
    assert agg._last_pushed_ts == first_ts

    # Adopt a rendered current-period row *after* live bars were pushed.
    session.set_bars("1 week", [Bar("SPY", "1 week", P, 200.0, 210.0, 190.0, 205.0, 5000.0)])
    assert agg.has_period_base is True
    assert agg._last_pushed_ts == first_ts  # guard outlives adoption
    assert agg.covering_since == P
    assert agg.current_bar().volume == 5000.0

    # The redelivered 5-second ts is not re-counted (no double-count).
    session.on_realtime_bar(
        req_id, first_ts, 300.0, 400.0, 50.0, 350.0, 999.0)
    assert agg.current_bar().volume == 5000.0
    assert agg.current_bar().high == 210.0
    assert agg.current_bar().close == 205.0

    # A genuinely newer ts still merges into the same candle.
    session.on_realtime_bar(
        req_id, first_ts + 5, 205.0, 206.0, 204.0, 205.5, 100.0)
    assert agg.current_bar().ts == P
    assert agg.current_bar().volume == 5100.0
    assert agg.current_bar().close == 205.5
    assert agg.current_bar().high == 210.0
    assert agg.covering_since == P


# ── AC6: the marker follows a full replace's rows ─────────────────────────


def test_ac6_set_series_emits_one_marker_after_the_rows():
    view = _make_view("1 week")
    rows = [
        Bar("SPY", "1 week", 1_779_076_800, 90.0, 95.0, 88.0, 94.0, 1000.0),
        Bar("SPY", "1 week", 1_779_681_600, 94.0, 99.0, 92.0, 98.0, 2000.0),
        Bar("SPY", "1 week", P, 100.0, 102.0, 98.0, 99.0, 3500.0,
            partial=True),
    ]

    view.update_bars(rows)
    env = view.bridge.flush()
    partials = _partial_ops(env)
    assert partials == [{"op": "set_partial", "ts": P, "partial": True}]

    ops = env["ops"]
    marker_index = ops.index(partials[0])
    candles_index = next(
        i for i, op in enumerate(ops)
        if op.get("op") == "set_bars" and op.get("series") == "candles")
    volume_index = next(
        i for i, op in enumerate(ops) if op.get("op") == "set_volume")
    assert marker_index > candles_index
    assert marker_index > volume_index
    assert marker_index == len(ops) - 1  # the directive rides last
    assert view._partial_ts == P


# ── AC6: the window clock seam is late-bound; the default is time.time ─────


def test_ac6_seam_main_window_wall_now_is_late_bound(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ibkr import pacing as pacing_mod

    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    try:
        session = win.get_or_create_session("P25SEAM")
        assert session._wall_now() == win._now_ts()

        fixed = 1_900_000_123
        win._now_ts = lambda: fixed  # replacement made after creation
        assert session._wall_now() == fixed
    finally:
        win.close()
        win.deleteLater()
        qapp.processEvents()


def test_ac6_seam_default_session_clock_is_time_time():
    session, host = _new_session()
    assert session._wall_now is time.time
    assert abs(session._wall_now() - time.time()) < 1.0
