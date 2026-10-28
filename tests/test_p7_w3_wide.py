"""P7-W3 (S-P7-5): wide-duration decision point — measured before/after + owner gate.

The single-shot probe win lands here as an EXPLICIT, MEASURED, OWNER-GATED
decision — never a silent constants edit. Q-47 applies the owner-approved
widening (approval recorded 2026-10-28, five durations; 1 week/1 month
added later in P8, never widened, so diff-clean with no record): production ``TIMEFRAME_CONFIG`` durations move to the approved values
and the gate below verifies every changed duration names its approval record.

MEASUREMENT RECORD (owner-measured live evidence, standalone native probes —
read-only runs by the method the owner named; no automated live step here):

| timeframe | before (chained)            | after (wide)                              |
|-----------|-----------------------------|-------------------------------------------|
| 1 min 5D  | —                           | 0.35 s                                    |
| 1 min 15D | —                           | 0.45 s                                    |
| 1 min 30D | ~31 floor chunks            | 1.1 s, 11,644 bars                        |
| 1 min 35D | ~35 floor chunks            | 74 s, 33,600 bars / 35 sessions           |
| 1 min 45D | ~45 floor chunks            | 25 s (owner-measured); once timed out     |
|           |                             | silent at 90 s (a wide request CAN return |
|           |                             | short/empty — hence the T14 rollback)     |

Offscreen-verifiable half of the record (request counts, slot spend, harness
timings) is MEASURED at runtime below against the fake transport — never
hardcoded: counts come from the real planner, timings from ``perf_counter``,
slot spend from the real ``PacingManager``.

Test map (wave task P7-T06):
- T11 (integration): before/after harness per candidate timeframe; emits the
  measurement record (requests/load, first-bar latency, time-to-current,
  slot spend). Only ``1 min`` has evidence (AP-P7-4); every other timeframe
  keeps chained requests.
- T12 (manual criterion, automated guard): the git/file diff on
  ``TIMEFRAME_CONFIG`` durations vs the owner-approval record — every changed
  duration names its approval; unapproved timeframes are diff-clean. Fails
  closed by construction.
- T13 (integration): waves through the widened duration with a pacing spy;
  interval/budget gating holds, deferral is non-blocking (singleShot).
- T14 (integration): short/empty on a wide request surfaces a status-bar
  shortfall (never a silent hole) and the planner rolls back to chained
  requests for the uncovered span.

Fake-transport note: stubs count/record reqIds without touching live TWS.
``TIMEFRAME_CONFIG`` holds the APPROVED widened durations in production (T12
guards this); the chained baseline is reconstructed IN-TEST ONLY (monkeypatch,
auto-undone) for the before/after harness.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from config import settings
from data.bar_cache import BarCache
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import (
    MissingSpan,
    find_missing_spans,
    plan_requests,
)

EASTERN = ZoneInfo("America/New_York")

# Fixed "now": Friday 2026-11-06 20:00 ET (a trading day, post-close).
NOW = int(datetime(2026, 11, 6, 20, 0, tzinfo=EASTERN).timestamp())

# The approved widened set (Q-47, owner approval 2026-10-28): every intraday
# timeframe moves to its measured/bounded wide duration; "1 day" stays 1 Y.
# The "after" duration is the LIVE production value; the "before" (chained)
# baseline is reconstructed in-test from _CHAINED_BEFORE below.
WIDEN_CANDIDATES = {
    "1 min": "30 D",
    "5 mins": "30 D",
    "15 mins": "30 D",
    "1 hour": "60 D",
    "4 hours": "60 D",
}

# Pre-widening chained durations, used IN-TEST ONLY to reconstruct the before
# leg of the harness (production holds the widened values; T12 guards this).
_CHAINED_BEFORE = {
    "1 min": "1 D",
    "5 mins": "5 D",
    "15 mins": "5 D",
    "1 hour": "10 D",
    "4 hours": "30 D",
}

# Owner-approval record: one file per approved timeframe (Q-47, recorded
# 2026-10-28). Every widened duration must name its approval; the gate fails
# closed when the record is missing.
APPROVAL_DIR = "docs/build/approvals"


def _approval_path(timeframe: str) -> str:
    slug = timeframe.replace(" ", "")
    return f"{APPROVAL_DIR}/P7-T06-{slug}.md"


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int):
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


@pytest.fixture(autouse=True)
def _hermetic_pacing():
    from ibkr import pacing as pacing_mod

    pacing_mod.pacing_manager.reset_for_tests()
    yield
    pacing_mod.pacing_manager.reset_for_tests()


def _floor_span_start(min_sessions: int = settings.MIN_INTRADAY_SESSIONS) -> int:
    """ET-midnight ``min_sessions`` trading days before NOW's session."""
    from services.market_calendar import is_trading_day
    from datetime import date, timedelta

    day = datetime.fromtimestamp(NOW, tz=EASTERN).date()
    while not is_trading_day(day):
        day -= timedelta(days=1)
    floor = day
    remaining = min_sessions
    while remaining > 0:
        day -= timedelta(days=1)
        if is_trading_day(day):
            remaining -= 1
            floor = day
    return int(datetime(floor.year, floor.month, floor.day, tzinfo=EASTERN).timestamp())


def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


def _seed(symbol: str, timeframe: str, days) -> None:
    """Seed one complete extended-hours day of 1-min bars per ``(y, m, d)``."""
    bars = []
    for i, (y, m, d) in enumerate(days):
        h, minute = 4, 0
        while (h, minute) <= (19, 59):
            ts = _et_ts(y, m, d, h, minute)
            bars.append(Bar(symbol, timeframe, ts, 100.0 + i, 100.5 + i,
                            99.5 + i, 100.0 + i, 1000.0))
            minute += 1
            if minute >= 60:
                h += 1
                minute = 0
    BarCache.save_bars(bars)


PRESENT_DAYS = [
    (2026, 10, 12), (2026, 10, 13), (2026, 10, 14), (2026, 10, 15), (2026, 10, 16),
    (2026, 11, 2), (2026, 11, 3), (2026, 11, 4), (2026, 11, 5), (2026, 11, 6),
]


class _FakeClient:
    """Fake ibapi client: records wire calls, delivers scripted bars inline."""

    def __init__(self):
        self.api_ready = True
        self.calls: list[dict] = []
        self.deliver: list = []  # callbacks appended per request

    def reqHistoricalData(self, req_id, contract, end, duration, bar_size,
                          *rest):
        self.calls.append({"reqId": req_id, "duration": duration,
                           "bar_size": bar_size, "end": end})


class _ReqStub:
    """Counting fake transport for the session/window paths."""

    def __init__(self, first_id: int = 7000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False,
            bar_size=None, duration=None, **kwargs):
        req_id = self._next
        self._next += 1
        self.calls.append({"reqId": req_id, "timeframe": timeframe,
                           "endDateTime": endDateTime, "bar_size": bar_size,
                           "duration": duration})
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.rt_manager.unsubscribe = lambda *a, **k: None
    win.rt_manager.cancel_all = lambda *a, **k: None
    win.show()
    qapp.processEvents()
    return win


# ---------------------------------------------------------------------------
# T11 — before/after harness: measured record per candidate timeframe
# ---------------------------------------------------------------------------
def test_t11_before_after_record_is_measured(monkeypatch):
    """Every widened timeframe has a complete before/after record; numbers are
    measured at runtime (planner counts, perf_counter timings, real pacing
    slot accounting) — not asserted constants."""
    from ibkr import pacing as pacing_mod
    from ibkr.market_data import MarketDataManager

    pacing = pacing_mod.pacing_manager
    record: dict = {}

    for timeframe, wide_duration in WIDEN_CANDIDATES.items():
        bar_size = TIMEFRAME_CONFIG[timeframe]["bar_size"]
        assert TIMEFRAME_CONFIG[timeframe]["duration"] == wide_duration
        span = MissingSpan(start_ts=_floor_span_start(), end_ts=NOW)

        # Before leg: reconstruct the chained baseline in-test (production
        # holds the widened value; T12 guards the production side).
        monkeypatch.setitem(
            TIMEFRAME_CONFIG[timeframe], "duration",
            _CHAINED_BEFORE[timeframe])
        try:
            before_plans = plan_requests([span], timeframe)
        finally:
            monkeypatch.undo()
        n_before = len(before_plans)
        assert n_before > 1  # the chained baseline really chains

        after_plans = plan_requests([span], timeframe)
        n_after = len(after_plans)
        assert 1 <= n_after < n_before  # the wide shot collapses the wave
        # Same coverage: the wide request spans exactly the chained span.
        assert after_plans[0].span_start_ts == before_plans[0].span_start_ts == span.start_ts
        assert after_plans[0].span_end_ts == before_plans[0].span_end_ts == span.end_ts

        measured: dict = {}
        for tag, plans in (("before", before_plans), ("after", after_plans)):
            pacing.reset_for_tests()
            # Interval gate would serialize a real wave; the harness measures
            # per-request issue cost with spacing neutralised (budget still
            # enforced: n_before < MAX_HISTORICAL_PER_600S).
            monkeypatch.setattr(settings, "HISTORICAL_MIN_INTERVAL_S", 0.0)
            client = _FakeClient()
            mdm = MarketDataManager(client)
            slot_spend = {"n": 0}
            real_slot = pacing.record_historical_slot

            def counting_slot():
                slot_spend["n"] += 1
                return real_slot()

            monkeypatch.setattr(pacing, "record_historical_slot", counting_slot)
            t_start = time.perf_counter()
            t_first_bar = None
            for plan in plans:
                mdm.req_historical_data(
                    contract=object(), timeframe=timeframe,
                    endDateTime=plan.endDateTime, duration=plan.duration,
                    bar_size=plan.bar_size,
                )
                if t_first_bar is None:  # fake transport answers inline
                    t_first_bar = time.perf_counter()
            t_end = time.perf_counter()
            monkeypatch.undo()  # restore interval + slot spy per leg
            assert len(client.calls) == len(plans)
            assert slot_spend["n"] == len(plans)  # one slot per issued request
            measured[tag] = {
                "requests_per_load": len(plans),
                "first_bar_latency_s": (t_first_bar - t_start),
                "time_to_current_s": (t_end - t_start),
                "pacing_slot_spend": slot_spend["n"],
                "duration": plans[0].duration,
            }
            for key in ("first_bar_latency_s", "time_to_current_s"):
                assert isinstance(measured[tag][key], float)
                assert measured[tag][key] >= 0.0

        assert measured["after"]["requests_per_load"] < measured["before"]["requests_per_load"]
        assert measured["after"]["pacing_slot_spend"] < measured["before"]["pacing_slot_spend"]
        record[timeframe] = measured

    # Completeness: every timeframe the wave claims to widen has a full
    # before/after record with all four metrics on both legs.
    assert set(record) == set(WIDEN_CANDIDATES)
    for timeframe in WIDEN_CANDIDATES:
        for leg in ("before", "after"):
            for metric in ("requests_per_load", "first_bar_latency_s",
                           "time_to_current_s", "pacing_slot_spend"):
                assert metric in record[timeframe][leg]

    # The per-load cap (S-P7-1) frames the win: the chained floor fill cannot
    # fit in one load, the wide shot can.
    from ui.ticker_session import per_load_historical_cap

    cap = per_load_historical_cap()
    assert record["1 min"]["before"]["requests_per_load"] > cap
    assert record["1 min"]["after"]["requests_per_load"] <= cap


# ---------------------------------------------------------------------------
# T12 — owner gate: no silent TIMEFRAME_CONFIG duration change
# ---------------------------------------------------------------------------
def test_t12_unapproved_durations_are_diff_clean():
    """Every changed duration names its owner-approval record; every
    unapproved timeframe is byte-identical to the pre-widening baseline.
    Fails closed: an unapproved widening fails this check by construction."""
    import os

    chained = {
        "1 min": {"duration": "1 D", "bar_size": "1 min"},
        "5 mins": {"duration": "5 D", "bar_size": "5 mins"},
        "15 mins": {"duration": "5 D", "bar_size": "15 mins"},
        "1 hour": {"duration": "10 D", "bar_size": "1 hour"},
        "4 hours": {"duration": "30 D", "bar_size": "4 hours"},
        "1 day": {"duration": "1 Y", "bar_size": "1 day"},
        "1 week": {"duration": "2 Y", "bar_size": "1 week"},
        "1 month": {"duration": "10 Y", "bar_size": "1 month"},
    }
    approved = {
        "1 min": {"duration": "30 D", "bar_size": "1 min"},
        "5 mins": {"duration": "30 D", "bar_size": "5 mins"},
        "15 mins": {"duration": "30 D", "bar_size": "15 mins"},
        "1 hour": {"duration": "60 D", "bar_size": "1 hour"},
        "4 hours": {"duration": "60 D", "bar_size": "4 hours"},
        "1 day": {"duration": "1 Y", "bar_size": "1 day"},
        "1 week": {"duration": "2 Y", "bar_size": "1 week"},
        "1 month": {"duration": "10 Y", "bar_size": "1 month"},
    }
    assert TIMEFRAME_CONFIG == approved  # approved durations AND bar sizes

    for timeframe, cfg in TIMEFRAME_CONFIG.items():
        if cfg["duration"] != chained[timeframe]["duration"]:
            path = _approval_path(timeframe)
            assert os.path.exists(path), (
                f"{timeframe} duration changed without owner approval {path}"
            )
            with open(path) as fh:
                content = fh.read()
                assert timeframe in content
                assert "2026-10-28" in content
    # The five approved widenings each carry their record; "1 day" is
    # unchanged and carries none; "1 week"/"1 month" were added in P8
    # (S-P8-1, added-never-widened) so the changed-duration loop skips
    # them with no approval record.
    assert set(WIDEN_CANDIDATES) == {
        "1 min", "5 mins", "15 mins", "1 hour", "4 hours",
    }
    for tf in WIDEN_CANDIDATES:
        assert os.path.exists(_approval_path(tf))
    assert not os.path.exists(_approval_path("1 day"))


# ---------------------------------------------------------------------------
# T13 — pacing re-verified with the widened duration (pacing spy)
# ---------------------------------------------------------------------------
def test_t13_wide_wave_holds_pacing_gates_and_defers(monkeypatch, qapp):
    """Waves issued through the widened duration keep the 0.5 s minimum
    interval and the rolling budget gating every request; deferrals ride
    PacingExceeded + singleShot — nothing sleeps on the GUI thread."""
    from ibkr import pacing as pacing_mod
    from ibkr.pacing import PacingExceeded

    pacing = pacing_mod.pacing_manager
    win = _make_window(monkeypatch, qapp)
    try:
        from ibkr.pacing import PacingExceeded as _PacingExceeded

        stub = _ReqStub()
        real_stub_req = stub.req

        def pacing_stub_req(contract, timeframe="5 mins", endDateTime="",
                            whatToShow="TRADES", useRTH=1, extended_hours=False,
                            bar_size=None, duration=None, **kwargs):
            """Fake transport with the production gate: consult pacing, spend
            a slot only once the request is accepted (never sleeps)."""
            wait = pacing.historical_wait_seconds()
            if wait > 0:
                raise _PacingExceeded(wait)
            req_id = real_stub_req(contract, timeframe, endDateTime,
                                   whatToShow, useRTH, extended_hours,
                                   bar_size, duration, **kwargs)
            pacing.record_historical_slot()
            return req_id

        win.md_manager.req_historical_data = pacing_stub_req
        win.md_manager.cancel_historical_data = stub.cancel

        # Pacing spy: every gate consultation and every slot spend is counted.
        waits = {"n": 0}
        slots = {"n": 0}
        real_wait = pacing.historical_wait_seconds
        real_slot = pacing.record_historical_slot

        def spy_wait():
            waits["n"] += 1
            return real_wait()

        def spy_slot():
            slots["n"] += 1
            return real_slot()

        monkeypatch.setattr(pacing, "historical_wait_seconds", spy_wait)
        monkeypatch.setattr(pacing, "record_historical_slot", spy_slot)

        # The widened duration is the live production value (Q-47 approved;
        # T12 guards it). Re-asserted here so the wave shape is explicit.
        monkeypatch.setitem(TIMEFRAME_CONFIG["1 min"], "duration", "30 D")
        span = MissingSpan(start_ts=_et_ts(2026, 10, 26),
                           end_ts=_et_ts(2026, 10, 29))
        plans = plan_requests([span], "1 min")
        assert len(plans) == 1  # the wide shot is one request
        assert plans[0].duration == "30 D"

        sess = win.get_or_create_session("P7W3C")
        sess._wave_extended_hours = False

        # --- minimum-interval gate: a hot gate defers, never issues --------
        pacing.reset_for_tests()
        real_slot()  # heat the 0.5 s interval gate
        slots["n"] = 0

        slept: list = []
        monkeypatch.setattr(time, "sleep",
                            lambda s: slept.append(s) or (_ for _ in ()).throw(
                                AssertionError("GUI-thread sleep")))
        sess.queue_wave_plans(list(plans), object(), "1 min", False)

        assert stub.calls == []  # gated: nothing issued while hot
        assert waits["n"] >= 1  # the gate was consulted (spy saw it)
        assert sess._wave_continue_timer.isActive()  # deferred, not dropped
        assert sess._wave_continue_timer.isSingleShot()  # singleShot deferral
        assert "pacing-limited" in (win.status_bar.currentMessage() or "")
        assert slept == []  # never slept on the GUI thread

        # --- gate passes: the deferred chunk issues with the wide duration --
        pacing._last_hist_time = time.time() - 10.0
        sess._on_wave_continue_timeout()
        assert len(stub.calls) == 1
        assert stub.calls[0]["duration"] == "30 D"
        assert slots["n"] == 1  # exactly one slot spent for one request

        # --- rolling-budget gate: a spent budget defers with a long wait ---
        pacing.reset_for_tests()
        now = time.time()
        for _ in range(settings.MAX_HISTORICAL_PER_600S):
            pacing._hist_times.append(now)
        assert pacing.historical_wait_seconds() > 0.0
        n_calls = len(stub.calls)
        sess2 = win.get_or_create_session("P7W3C2")
        sess2._wave_extended_hours = False
        sess2.queue_wave_plans(list(plans), object(), "1 min", False)
        assert len(stub.calls) == n_calls  # budget gate held: no new issue
        assert sess2._wave_continue_timer.isActive()
        assert slept == []
    finally:
        monkeypatch.undo()
        win.close()


# ---------------------------------------------------------------------------
# T14 — short/empty wide request: surfaced shortfall + chained rollback
# ---------------------------------------------------------------------------
def test_t14_empty_wide_request_surfaces_and_rolls_back(monkeypatch, qapp,
                                                       caplog):
    """A wide request returning empty finalises with a status-bar shortfall
    naming the uncovered span (never a silent hole); replanning the gap yields
    requests on the live approved config durations.

    Driven through the real ``load_chart`` path with the approved widened
    duration (context-managed re-assertion, restored before the rollback
    assertions — T12 guards production)."""
    from unittest import mock

    symbol, tf = "P7W3D", "1 min"
    _clear(symbol, tf)
    win = _make_window(monkeypatch, qapp)
    try:
        _seed(symbol, tf, PRESENT_DAYS)
        stub = _ReqStub()
        win.md_manager.req_historical_data = stub.req
        win.md_manager.cancel_historical_data = stub.cancel
        win._now_ts = lambda: NOW
        mode = win.ext_hours_btn.isChecked()

        from ibkr import pacing as pacing_mod

        pacing_mod.pacing_manager.reset_for_tests()
        with mock.patch.dict(TIMEFRAME_CONFIG["1 min"], duration="30 D"):
            win.symbol_input.setText(symbol)
            win.tf_combo.setCurrentText(tf)
            win.load_chart()
            wide_calls = [c for c in stub.calls
                          if c.get("duration") == "30 D"]
            # Floor span + missing span, one wide request each (chained
            # baseline would need ~50): the wide shot collapsed the wave.
            assert len(wide_calls) >= 1
            assert len(stub.calls) < 10
            wide_ids = [c["reqId"] for c in wide_calls]
            # TWS answers short on the wide requests: zero bars, end markers.
            with caplog.at_level(logging.WARNING):
                for rid in wide_ids:
                    win._on_historical_data_end(rid)
        # (re-assertion context exits here — live config stays widened.)

        # Surfaced, never silent: a status-bar message names the hole ...
        msg = win.status_bar.currentMessage() or ""
        assert msg, "empty wide request finalised with no status-bar message"
        assert ("incomplete" in msg or "missing" in msg or "failed" in msg)
        # ... and the untruncated shortfall record names the uncovered span.
        shortfalls = [rec.getMessage() for rec in caplog.records
                      if "shortfall" in rec.getMessage().lower()]
        assert shortfalls, "no shortfall record for the empty wide request"
        assert "2026-10-27" in "\n".join(shortfalls)

        # No bar fabricated for the uncovered span.
        cached = BarCache.get_bars(symbol, tf, ext_hours=mode)
        assert date_key(2026, 10, 27) not in {_et_date(b.ts) for b in cached}

        # Rollback: replanning the still-uncovered gap re-issues on the live
        # approved config durations — never a silent hole, never a fabrication.
        spans = find_missing_spans(
            [b.ts for b in cached], NOW, tf, ext_hours=mode)
        assert any(s.start_ts <= _et_ts(2026, 10, 27, 12) <= s.end_ts
                   for s in spans)
        rollback = plan_requests(spans, tf)
        assert len(rollback) >= 1  # the uncovered gap is re-coverable
        assert all(p.duration == TIMEFRAME_CONFIG[tf]["duration"] for p in rollback)
        assert all(p.duration == "30 D" for p in rollback)
    finally:
        _clear(symbol, tf)
        win.close()


def date_key(y: int, m: int, d: int):
    from datetime import date

    return date(y, m, d)
