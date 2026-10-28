"""P7-W1: per-load historical budget cap with oldest-first floor fill.

T11 — a 1-min load on an empty cache issues at most floor(B/4) historical
       requests before yielding; the remainder stays queued (not dropped),
       and the bound scales with the tunable (never a hardcoded 25).
T12 — two successive capped loads against a session/cache double: the second
       load starts from the first load's persisted depth, opens older than
       the first load opened (next-oldest span first), never re-plans an
       already-persisted span, and cached depth strictly increases toward
       (and here reaches) the 30-session floor — without any single wave
       carrying it all.
T13 — the pure planner contracts are unchanged (signatures + Qt-free) and
       the scoped existing suites stay green unmodified.

Fake-transport note: the doubles below count ``req_historical_data`` issues
without touching ``pacing_manager``, so the suite is hermetic.
"""

from __future__ import annotations

import glob
import inspect
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

_ET = ZoneInfo("America/New_York")

# Fixed load instant: a Tuesday midday ET (a trading day; late October has no
# US-equity holiday nearby). Fixed so chunk counts are deterministic forever.
NOW_TS = int(datetime(2026, 10, 27, 12, 0, tzinfo=_ET).timestamp())


@pytest.fixture(scope="module")
def _qt():
    """A QApplication for TickerSession's QTimers (offscreen in CI)."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app


class _StubBar:
    def __init__(self):
        self.messages: list = []

    def showMessage(self, msg, ms=0):
        self.messages.append(msg)


class _FakeMD:
    """Counting fake transport: issues reqIds, never paces, never sleeps."""

    def __init__(self):
        self.issued: list = []
        self._next = 7000

    def req_historical_data(self, **kwargs):
        self._next += 1
        self.issued.append(dict(kwargs))
        return self._next

    def cancel_historical_data(self, req_id):
        pass


class _StubHost:
    def __init__(self):
        self.md_manager = _FakeMD()
        self.status_bar = _StubBar()
        self.reg: dict = {}
        self.wave_complete_calls: list = []

    def _register_req_id(self, req_id, session):
        self.reg[req_id] = session

    def _unregister_req_id(self, req_id):
        self.reg.pop(req_id, None)

    def _on_session_wave_complete(self, session):
        self.wave_complete_calls.append(session)

    def _on_session_prime_complete(self, session):
        pass


def _anchor_utc(end_datetime_str: str) -> datetime:
    """Parse a planner ``endDateTime`` (``yyyyMMdd-HH:mm:ss`` UTC)."""
    return datetime.strptime(end_datetime_str, "%Y%m%d-%H:%M:%S").replace(
        tzinfo=timezone.utc
    )


def _rth_ts(day) -> int:
    """A 14:00 ET timestamp on ``day`` — inside the RTH session window."""
    return int(
        datetime(day.year, day.month, day.day, 14, 0, tzinfo=_ET).timestamp()
    )


def _persist_answered_chunk(cache_ts: list, plan) -> None:
    """Append dense 1-min bars for the chunk's calendar date (capped at now).

    A single timestamp per day would trip the D27.7 bar-level hole-repair
    pass (leading/trailing-edge gaps); real fetched chunks are dense, so the
    double is dense too: every 1-min period start in the RTH window.
    """
    day = _anchor_utc(plan.endDateTime).astimezone(_ET).date()
    start = int(
        datetime(day.year, day.month, day.day, 9, 30, tzinfo=_ET).timestamp()
    )
    end = int(
        datetime(day.year, day.month, day.day, 16, 0, tzinfo=_ET).timestamp()
    )
    end = min(end, NOW_TS)
    ts = start
    while ts < end:
        cache_ts.append(ts)
        ts += 60


def _issue_and_answer(sess, host, plans):
    """Answer every currently-issued request with one bar + end marker.

    Returns the (req_id, plan) pairs in issue order (newest chunk first).
    """
    seen = set(sess._history_req_ids)
    pairs = []
    for req_id in list(host.reg.keys()):
        if req_id in seen and req_id in sess._history_req_ids:
            pairs.append(req_id)
    # Host reg is insertion-ordered; the session's in-flight set holds the
    # same ids. Pair positionally with the plans just issued.
    issued_plans = plans[: len(pairs)]
    for req_id, plan in zip(pairs, issued_plans):
        anchor = _anchor_utc(plan.endDateTime)
        sess.on_historical_bar(
            req_id,
            SimpleNamespace(
                date=anchor.strftime("%Y%m%d %H:%M:%S"),
                open=1.0,
                high=2.0,
                low=0.5,
                close=1.5,
                volume=100.0,
            ),
        )
        sess.on_historical_data_end(req_id)
    return list(zip(pairs, issued_plans))


def test_t11_per_load_cap(_qt, monkeypatch):
    from config import settings
    from services.backfill_service import find_missing_spans, plan_requests
    from ui.ticker_session import TickerSession, per_load_historical_cap

    cap = per_load_historical_cap()
    # Fraction of the tunable — never a hardcoded 25.
    assert cap == settings.MAX_HISTORICAL_PER_600S // 4
    assert cap >= 1

    missing = find_missing_spans(
        [], NOW_TS, "1 min", ext_hours=False,
        min_sessions=settings.MIN_INTRADAY_SESSIONS,
    )
    plans = plan_requests(missing, "1 min")
    assert len(plans) > cap, "floor must need more than one load"

    host = _StubHost()
    sess = TickerSession("SPY", host)
    sess.queue_wave_plans(plans, object(), "1 min", False)

    # Issued-before-yield is bounded by floor(B/4) ...
    assert len(host.md_manager.issued) == cap
    assert len(host.md_manager.issued) <= settings.MAX_HISTORICAL_PER_600S // 4
    # ... and the remainder stays queued, not dropped.
    assert len(sess._wave_plan_queue) == len(plans) - cap > 0

    # The bound scales with the tunable.
    monkeypatch.setattr(settings, "MAX_HISTORICAL_PER_600S", 50)
    assert per_load_historical_cap() == 12
    host2 = _StubHost()
    sess2 = TickerSession("SPY", host2)
    sess2.queue_wave_plans(plans, object(), "1 min", False)
    assert len(host2.md_manager.issued) == 12
    assert len(sess2._wave_plan_queue) == len(plans) - 12


def test_t12_monotonic_oldest_first_across_loads(_qt, monkeypatch):
    from config import settings
    from data.bar_cache import BarCache
    from services.backfill_service import (
        find_missing_spans,
        plan_requests,
        present_days,
    )
    from ui.ticker_session import TickerSession, per_load_historical_cap

    saved_batches: list = []
    monkeypatch.setattr(
        BarCache, "save_bars",
        lambda bars, ext_hours=True: saved_batches.append(list(bars)),
    )

    cap = per_load_historical_cap()
    min_sessions = settings.MIN_INTRADAY_SESSIONS

    def plan_for(cache_ts):
        spans = find_missing_spans(
            cache_ts, NOW_TS, "1 min", ext_hours=False,
            min_sessions=min_sessions,
        )
        return spans, plan_requests(spans, "1 min")

    # ---- load 1: empty cache -> floor span, capped issue ----
    cache_ts: list = []
    spans1, plans1 = plan_for(cache_ts)
    assert len(spans1) == 1, "empty cache plans one backwards floor span"
    assert len(plans1) > cap

    host = _StubHost()
    sess = TickerSession("SPY", host)
    sess.queue_wave_plans(plans1, object(), "1 min", False)
    assert len(host.md_manager.issued) == cap
    assert sess._wave_issued_this_load == cap
    assert len(sess._wave_plan_queue) == len(plans1) - cap

    answered1 = _issue_and_answer(sess, host, plans1)
    assert len(answered1) == cap
    assert len(sess._pending_bars) == cap
    # Queue non-empty: the capped wave does NOT finalise mid-floor.
    assert host.wave_complete_calls == []

    # Persist like a same-symbol reload would (load_chart flushes the
    # previous wave before cancelling it): dense bars per answered chunk
    # stand in for the fetched bars, plus the real pending flush.
    for _, plan in answered1:
        _persist_answered_chunk(cache_ts, plan)
    assert sess.flush_pending_bars() == cap
    # T02 landed per-chunk persist: every answered chunk was already saved
    # on arrival (one single-bar save per chunk-end), so the flush persists
    # the wave remainder as one closing batch — cap singles plus one batch
    # of cap. The cap/resume intent is unchanged: bounded issue, no
    # mid-floor finalise, remainder queued.
    assert len(saved_batches) == cap + 1
    assert [len(b) for b in saved_batches[:-1]] == [1] * cap
    assert len(saved_batches[-1]) == cap
    assert sess._pending_bars == []
    depth1_days = present_days(cache_ts, False)
    assert len(depth1_days) > 0

    # ---- load 2: resumes from the persisted depth ----
    spans2, plans2 = plan_for(cache_ts)
    assert len(spans2) == 1
    assert spans2[0].start_ts == spans1[0].start_ts, "same floor"
    assert spans2[0].end_ts < spans1[0].end_ts, "resumed past load 1"
    # No already-persisted span is re-planned: the new span starts at or
    # before the oldest *persisted trading day* (weekend cache entries are
    # invisible to the planner's trading-day presence, so the comparison is
    # day-granular, like the planner itself).
    end_day = datetime.fromtimestamp(spans2[0].end_ts, tz=_ET).date()
    assert all(d >= end_day for d in depth1_days), (
        sorted(depth1_days)[:3], end_day,
    )
    # Next-oldest span first: load 2 opens older than load 1 opened.
    assert plans2[0].span_end_ts < plans1[0].span_end_ts
    assert _anchor_utc(plans2[0].endDateTime) < _anchor_utc(
        plans1[0].endDateTime
    )

    before = set(host.reg.keys())
    n_before = len(host.md_manager.issued)
    sess.queue_wave_plans(plans2, object(), "1 min", False)
    issued2 = len(host.md_manager.issued) - n_before
    assert issued2 == min(cap, len(plans2)), "spend resets per load"
    assert sess._wave_issued_this_load == issued2
    assert len(sess._wave_plan_queue) == len(plans2) - issued2
    # Total spend across the two loads exceeds one cap: no single wave
    # carries the floor by itself.
    assert cap + issued2 > cap

    answered2 = _issue_and_answer(sess, host, plans2)
    assert len(answered2) == issued2
    for _, plan in answered2:
        _persist_answered_chunk(cache_ts, plan)
    depth2_days = present_days(cache_ts, False)

    # Monotonic oldest-first growth, converging to the floor.
    assert depth1_days < depth2_days, "cached depth strictly increases"
    assert len(depth2_days) >= min_sessions, "floor converged across loads"

    if not sess._wave_plan_queue:
        # Load 2 drained the floor: the wave completes exactly once.
        assert host.wave_complete_calls == [sess]


def test_t13_planner_contracts_and_scoped_suites():
    import pathlib
    import subprocess

    from services import backfill_service as bf

    # Planner contracts unchanged: same pure signatures ...
    assert list(inspect.signature(bf.find_missing_spans).parameters) == [
        "cached_ts", "now_ts", "timeframe", "trailing_days",
        "ext_hours", "min_sessions",
    ]
    assert list(inspect.signature(bf.plan_requests).parameters) == [
        "missing_spans", "timeframe",
    ]
    assert list(inspect.signature(bf.floor_bar_budget).parameters) == [
        "timeframe", "ext_hours",
    ]
    assert list(inspect.signature(bf.bar_period_seconds).parameters) == [
        "timeframe",
    ]
    # ... and still Qt-free (no Qt *import*; the docstring names the
    # boundary in prose, which is allowed).
    import re

    src = pathlib.Path("services/backfill_service.py").read_text()
    qt_imports = [
        ln for ln in src.splitlines()
        if re.match(r"\s*(import|from)\b", ln)
        and ("PyQt" in ln or "PySide" in ln)
    ]
    assert not qt_imports, f"Qt imports leaked into planner: {qt_imports}"

    # Scoped existing suites, unmodified, stay green.
    files = ["tests/test_backfill_service.py"]
    files += sorted(glob.glob("tests/test_history_backfill*.py"))
    files += ["tests/test_d42_depth_floor.py", "tests/test_d42_day_presence.py"]
    missing = [f for f in files if not pathlib.Path(f).exists()]
    assert not missing, f"scoped suite files missing: {missing}"
    assert len(files) >= 4, f"expected history_backfill suites, got: {files}"

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", *files],
        capture_output=True,
        text=True,
        timeout=600,
    )
    tail = (proc.stdout + proc.stderr)[-3000:]
    assert proc.returncode == 0, f"scoped suites red:\n{tail}"
