"""P12-T3 (S-P12-3/S-P12-5): planner verification for the 30 mins timeframe.

Verification, not code: asserts that the existing planner contracts in
:mod:`services.backfill_service` already satisfy AC-D52.3 for ``30 mins``
(``30 D`` / ``30 mins`` — the P12-T1 config row) with zero planner source
changes:

- a full-span load plans the configured duration in one chunk;
- a span wider than one window chunks by that duration, newest first;
- the AC-D16.8 30-session floor fires (``period < 86400``) and is mode-aware
  (RTH vs ETH presence), with the flat cap holding for both modes;
- a hole in the middle of cached coverage is detected at bar granularity.

Plus the S-P12-5 priming shape (a mid-period ``30 mins`` load primes with
``5 secs`` bars and a duration inside ``[60 S, 3600 S]``) and the docstring
per-span table row, and the standalone-probe record gate (AC-D52.7).

Qt-free except the priming-shape case, which drives ``prime_aggregator``
directly offscreen (no TWS connection). The probe-record case reads the
P12-T3 probe artifact; it never re-probes.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from config.settings import SESSION_BAR_CAP
from data.bar_aggregator import TIMEFRAME_SECONDS
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import (
    MissingSpan,
    bar_period_seconds,
    find_missing_spans,
    floor_bar_budget,
    plan_requests,
)
from services.market_calendar import is_trading_day

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")

# The P12-T1 row under verification.
TIMEFRAME, DURATION, BAR_SIZE = "30 mins", "30 D", "30 mins"

D_SECONDS = 86_400
WINDOW_SECONDS = 30 * D_SECONDS  # the configured 30 D chunk

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBE_RECORD = REPO_ROOT / "docs" / "d52_probe_record.md"
PRIME_TABLE_OWNER = REPO_ROOT / "ui" / "ticker_session.py"


def _et_midnight(day):
    return int(datetime(day.year, day.month, day.day, tzinfo=_EASTERN).timestamp())


def _recent_trading_days(count, end=None):
    """Return ``count`` trading days ending at ``end`` (default today), ascending."""
    day = (datetime.now(_EASTERN).date() if end is None else end)
    days = []
    while len(days) < count:
        if is_trading_day(day):
            days.append(day)
        day -= timedelta(days=1)
    return sorted(days)


def _rth_session_bars(day):
    """Full RTH-session 30-min bar starts for ``day`` (09:30–15:30 ET)."""
    base = _et_midnight(day) + (9 * 3600 + 30 * 60)
    return [base + k * 1800 for k in range(13)]


# ---------------------------------------------------------------------------
# Configured duration is planned in one chunk for a full-span load
# ---------------------------------------------------------------------------
def test_full_span_plans_configured_duration_in_one_chunk():
    """A span within one window yields one plan carrying the configured pair."""
    assert TIMEFRAME_CONFIG[TIMEFRAME]["duration"] == DURATION
    assert TIMEFRAME_CONFIG[TIMEFRAME]["bar_size"] == BAR_SIZE
    now_ts = _et_midnight(datetime.now(_EASTERN).date()) + 14 * 3600
    span = MissingSpan(
        start_ts=now_ts - WINDOW_SECONDS + D_SECONDS, end_ts=now_ts
    )
    plans = plan_requests([span], TIMEFRAME)
    assert len(plans) == 1
    assert plans[0].duration == DURATION
    assert plans[0].bar_size == BAR_SIZE
    assert plans[0].span_start_ts == span.start_ts
    assert plans[0].span_end_ts == span.end_ts


# ---------------------------------------------------------------------------
# Wider spans chunk by the configured duration, newest first
# ---------------------------------------------------------------------------
def test_wider_span_chunks_by_configured_duration_newest_first():
    """A span wider than one window splits into ceil(span/duration) chunks."""
    now_ts = _et_midnight(datetime.now(_EASTERN).date()) + 14 * 3600
    extra = 5 * D_SECONDS  # push just past one full window
    span = MissingSpan(
        start_ts=now_ts - (WINDOW_SECONDS + extra), end_ts=now_ts
    )
    plans = plan_requests([span], TIMEFRAME)
    assert len(plans) == 2
    assert all(p.duration == DURATION for p in plans)
    assert all(p.bar_size == BAR_SIZE for p in plans)
    # Newest chunk first: endDateTime anchors descend.
    assert plans[0].endDateTime >= plans[1].endDateTime


# ---------------------------------------------------------------------------
# The AC-D16.8 30-session floor fires, mode-aware (intraday polarity)
# ---------------------------------------------------------------------------
def test_depth_floor_fires_mode_aware_with_flat_cap():
    """Empty cache + min_sessions=30 yields one backwards floor span.

    The floor covers exactly 30 trading sessions back from the current
    session, under both modes; the flat cap holds for both modes (the
    derived intraday budget sits below it).
    """
    assert bar_period_seconds(TIMEFRAME) == 1800
    assert TIMEFRAME_SECONDS[TIMEFRAME] == 1800
    days = _recent_trading_days(40)
    now_ts = _et_midnight(days[-1]) + 14 * 3600  # mid-session, trading day
    for ext_hours in (False, True):
        spans = find_missing_spans([], now_ts, TIMEFRAME,
                                   min_sessions=30, ext_hours=ext_hours)
        assert len(spans) == 1, f"ext_hours={ext_hours}: {spans}"
        floor_day = datetime.fromtimestamp(
            spans[0].start_ts, tz=_EASTERN).date()
        assert is_trading_day(floor_day)
        assert spans[0].end_ts == now_ts
        # Session count: exactly 30 trading days strictly after the floor
        # day through the current session.
        count = 0
        day = floor_day + timedelta(days=1)
        while day <= datetime.fromtimestamp(now_ts, tz=_EASTERN).date():
            if is_trading_day(day):
                count += 1
            day += timedelta(days=1)
        assert count == 30, f"ext_hours={ext_hours}: floor covers {count}"
        assert floor_bar_budget(TIMEFRAME, ext_hours) == SESSION_BAR_CAP


def test_depth_floor_is_mode_aware():
    """Pre-market bars count as present under ETH but missing under RTH."""
    days = _recent_trading_days(10)
    # 08:00 ET: inside the ETH window (04:00-20:00), outside RTH (09:30-16:00).
    cached_ts = [_et_midnight(d) + 8 * 3600 for d in days]
    now_ts = _et_midnight(days[-1]) + 14 * 3600
    # trailing_days=0 isolates the mode-aware day-presence predicate (the
    # bar-level pass is covered by the hole test below; a lone 08:00 bar
    # would otherwise read as session edges with holes on both sides).
    rth_spans = find_missing_spans(cached_ts, now_ts, TIMEFRAME,
                                   min_sessions=30, ext_hours=False,
                                   trailing_days=0)
    eth_spans = find_missing_spans(cached_ts, now_ts, TIMEFRAME,
                                   min_sessions=30, ext_hours=True,
                                   trailing_days=0)
    # Under RTH nothing is present: the floor runs from the floor day to
    # now, alongside the day-presence span over the cached range.
    assert len(rth_spans) == 2
    assert any(s.end_ts == now_ts for s in rth_spans)
    assert any(s.start_ts == _et_midnight(days[0]) for s in rth_spans)
    # Under ETH every day is present: no day-presence span, and the floor
    # stops at the earliest present day, so the span ends before now.
    assert len(eth_spans) == 1
    assert eth_spans[0].end_ts == _et_midnight(days[0])
    assert eth_spans[0].end_ts < now_ts


# ---------------------------------------------------------------------------
# A hole in the middle is detected at bar granularity
# ---------------------------------------------------------------------------
def test_hole_in_middle_detected_at_bar_granularity():
    """A missing run of trading days inside cached coverage yields one span."""
    days = _recent_trading_days(12)
    gap = days[4:7]  # three consecutive trading days with no cached bars
    cached_days = days[:4] + days[7:]
    cached_ts = []
    now_ts = _et_midnight(days[-1]) + 14 * 3600
    for day in cached_days:
        if day == days[-1]:
            # Today is partial: bars only up to the current half-hour slot,
            # so the trailing-edge pass sees no over-fetchable tail.
            for ts in _rth_session_bars(day):
                if ts <= now_ts - 1800:
                    cached_ts.append(ts)
        else:
            cached_ts.extend(_rth_session_bars(day))
    spans = find_missing_spans(cached_ts, now_ts, TIMEFRAME, min_sessions=0)
    assert len(spans) == 1, f"expected exactly the gap span: {spans}"
    assert spans[0].start_ts == _et_midnight(gap[0])
    assert spans[0].end_ts == _et_midnight(gap[-1] + timedelta(days=1))


# ---------------------------------------------------------------------------
# Priming shape: a mid-period 30 mins load uses the 5 secs branch
# ---------------------------------------------------------------------------
class _StubHost:
    """Minimal prime_aggregator host (no MainWindow, no TWS)."""

    def __init__(self):
        self.calls = []
        self._next_req_id = 9100

    def req_historical(self, **kwargs):
        self.calls.append(kwargs)
        self._next_req_id += 1
        return self._next_req_id

    def _register_req_id(self, req_id, session):
        pass

    def _on_session_prime_complete(self, session):
        pass


def test_mid_period_prime_uses_five_secs_branch(qapp):
    """Late-period 30 mins load -> '5 secs' bars, duration in [60 S, 3600 S]."""
    from ui.ticker_session import TickerSession

    host = _StubHost()
    session = TickerSession("TEST", host)
    session._host.md_manager = host  # route req_historical_data at the stub
    host.req_historical_data = host.req_historical
    agg = session.aggregator_for(TIMEFRAME)
    period_start = agg.period_start(1_760_000_000)
    # Late in the forming half-hour (a boundary-exact ``now`` is a period
    # boundary with nothing to prime, so the latest primable instant is
    # one second shy of the full 1800 s elapsed span).
    now = period_start + 1799
    assert session.prime_aggregator(
        contract=object(), timeframe=TIMEFRAME, now_ts=now,
        extended_hours=False,
    ) is True
    prime_calls = [c for c in host.calls if c.get("timeframe") == TIMEFRAME]
    assert len(prime_calls) == 1, f"expected one priming request: {host.calls}"
    call = prime_calls[0]
    assert call["bar_size"] == "5 secs", (
        f"30 mins load took the coarse branch: {call}"
    )
    duration_s = int(call["duration"].split()[0])
    assert duration_s == 1799, f"duration not the clamped span: {call['duration']!r}"
    assert 60 <= duration_s <= 3600, (
        f"duration {call['duration']!r} outside [60 S, 3600 S]"
    )


def test_priming_docstring_names_thirty_min_row():
    """The per-span table names the 30 mins row in the 5 secs group."""
    text = PRIME_TABLE_OWNER.read_text(encoding="utf-8")
    anchor = text.index("Per-span priming table")
    window = text[anchor:anchor + 2000]
    assert "'30 mins'" in window, "30 mins priming-table row missing"
    row = next(
        line for line in window.splitlines() if "'30 mins'" in line
    )
    assert "'5 secs'" in row, f"30 mins row not in the 5 secs group: {row!r}"
    assert "1 min" not in row, f"30 mins row names the coarse branch: {row!r}"


# ---------------------------------------------------------------------------
# Standalone probe record gate (AC-D52.7) — reads the artifact, never re-probes
# ---------------------------------------------------------------------------
class TestProbeRecord:
    def test_probe_record_exists(self):
        assert PROBE_RECORD.is_file(), "docs/d52_probe_record.md missing"

    def test_probe_record_names_the_combo(self):
        text = PROBE_RECORD.read_text(encoding="utf-8")
        assert "(30 D, 30 mins)" in text, "30 mins combo not documented"

    def test_probe_record_clean_completion_no_321(self):
        text = PROBE_RECORD.read_text(encoding="utf-8")
        assert "`30 D` | `30 mins` | yes" in text, "combo row not completed"
        assert "no 321-class rejection" in text, "no-rejection statement missing"
        assert "probe gate **passes**" in text, "pass conclusion missing"
