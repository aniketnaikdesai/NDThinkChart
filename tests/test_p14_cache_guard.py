"""P14-T3 (D53.3/D53.4) — cache-current claim guard + batch history gate.

Offscreen MainWindow tests (``IBApiClient.connect`` monkeypatched, historical
feed stubbed) proving:

* T31/AC1 — the no-plans branch and the finalize path consult the single
  ``_is_cache_current`` predicate: while a wave is in flight or the planner
  reports missing spans for the current triple, neither "Cache current" nor
  any equivalent freshness claim is visible.
* T32/AC2 — a watchdog-stranded wave with missing days ends on the verbatim
  AC-D16.4 shortfall (wording byte-identical to the pre-change line).
* T33/AC3 — a zero-missing, no-wave load still reports currency exactly as
  today ("{symbol} - {n} cached bars. Cache current.").
* T34/AC4 — docs/requirements/requirements.md keeps the ### D41..### D52
  history, the Existing Repository marker sentence and the Current Tech
  Stack, with no pre-D53 wording touched (pinned against the recorded
  pre-batch snapshot hash; the batch diff itself was verified purely
  additive — zero deletions — so the snapshot equals the pre-batch text
  plus the batch's own D53 additions).

Helpers mirror ``tests/test_p14_lifecycle.py`` (seeded ``BarCache`` +
stubbed ``req_historical_data``); nothing here weakens, skips or rewrites
an existing test.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone

import pytest
from PyQt6.QtWidgets import QDockWidget

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from services.backfill_service import MissingSpan
from services.market_calendar import is_trading_day, trading_days

EASTERN = ZoneInfo("America/New_York")

TF5 = "5 mins"
TF_DAY = "1 day"
SEED_DAY = date(2026, 8, 3)  # one complete old 5-min session; everything since is missing
NOW_TS = int(datetime(2026, 10, 2, 20, 0, tzinfo=EASTERN).timestamp())
N_DAILY = 15  # seeded complete daily sessions for the zero-missing triple

# Claim family (A144): the literal plus equivalent freshness phrasings.
# Never the bare word "complete" — the honest shortfall contains
# "incomplete" and must not trip the absence check.
CLAIM_PHRASES = (
    "cache current",
    "up to date",
    "up-to-date",
    "fully cached",
    "all caught up",
)

# Recorded pre-batch snapshot: sha256 of requirements.md text before the
# "\n### D53 " heading, taken when the batch diff was verified purely
# additive (zero removed lines), so the pinned segment is the pre-batch
# text plus only the batch's own D53 additions.
PRE_D53_SHA256 = (
    "c51a84fd55e080bd564db0c8a9028584fc77c1a2b912a77f451a55457a774b88"
)


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _session_bars(symbol: str, day: date, base: float = 100.0) -> list[Bar]:
    """One deterministic complete 5-min session (04:00-20:00 ET)."""
    assert is_trading_day(day)
    period = TIMEFRAME_SECONDS[TF5]
    start = _et_ts(day.year, day.month, day.day, 4, 0)
    close = _et_ts(day.year, day.month, day.day, 20, 0)
    bars: list[Bar] = []
    ts, i = start, 0
    while ts < close:
        price = base + (i % 5) * 0.25
        bars.append(
            Bar(symbol, TF5, ts, price, price + 0.5, price - 0.5, price,
                1000.0 + (ts % 500))
        )
        ts += period
        i += 1
    return bars


def _seed_daily(symbol: str, n: int,
                end: date = date(2026, 10, 2)) -> int:
    """Seed ``n`` complete daily sessions ending on ``end`` (a trading day)."""
    assert is_trading_day(end)
    bars: list[Bar] = []
    day = end
    while len(bars) < n:
        if is_trading_day(day):
            ts = _et_ts(day.year, day.month, day.day, 12, 0)
            bars.append(
                Bar(symbol, TF_DAY, ts, 100.0, 101.0, 99.0, 100.5, 1000000.0)
            )
        day -= timedelta(days=1)
    BarCache.save_bars(bars)
    return len(bars)


def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


def _seed_day(symbol: str, day: date, base: float = 100.0) -> int:
    bars = _session_bars(symbol, day, base)
    BarCache.save_bars(bars)
    return len(bars)


class _ReqStub:
    """Captures ``req_historical_data`` calls; records cancels."""

    def __init__(self, first_id: int = 5000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, bar_size=None, duration=None):
        req_id = self._next
        self._next += 1
        self.calls.append({
            "reqId": req_id,
            "contract": contract,
            "timeframe": timeframe,
            "endDateTime": endDateTime,
            "whatToShow": whatToShow,
            "useRTH": useRTH,
            "extended_hours": extended_hours,
            "bar_size": bar_size,
            "duration": duration,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


def _wave_calls(stub: _ReqStub) -> list[dict]:
    """Issued backfill-wave calls (D27.9 priming is never a wave member)."""
    return [c for c in stub.calls if c.get("bar_size") != "5 secs"]


def _make_window(monkeypatch, qapp):
    """Build a shown ``MainWindow`` that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.rt_manager.unsubscribe = lambda *a, **k: None
    win.rt_manager.cancel_all = lambda *a, **k: None
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _stub_feed(win, stub: _ReqStub, now_ts: int = NOW_TS) -> None:
    win._now_ts = lambda: now_ts
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel


def _assert_no_claim(text: str) -> None:
    lowered = text.lower()
    assert "Cache current" not in text
    for phrase in CLAIM_PHRASES:
        assert phrase not in lowered, f"freshness claim {phrase!r} in {text!r}"


# ---------------------------------------------------------------------------
# T31 / AC1 — in-flight wave suppresses the no-plans claim
# ---------------------------------------------------------------------------
def test_t31_no_plans_in_flight_suppresses_claim(monkeypatch, qapp):
    """Same-session stuck in-flight reqIds + genuinely empty plans: no claim."""
    sym = "SPY"
    _clear(sym, TF_DAY)
    n = _seed_daily(sym, N_DAILY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        session = win.get_or_create_session(sym)
        # Stuck in-flight bookkeeping the load does not clear (the cancel
        # seam is defeated to simulate a wave the load cannot see end).
        session._history_req_ids.add(96001)
        monkeypatch.setattr(
            session, "_cancel_history_requests", lambda: None
        )
        win.load_chart(sym, TF_DAY, True)
        current = win.status_bar.currentMessage()
        _assert_no_claim(current)
        # Honest bare count, no freshness wording.
        assert current == f"{sym} — {n} cached bars."
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T31 / AC1 — planner-missing spans suppress the no-plans claim
# ---------------------------------------------------------------------------
def test_t31_no_plans_planner_missing_suppresses_claim(monkeypatch, qapp):
    """Plans empty (chunker yields nothing) but the planner reports spans."""
    import ui.main_window as mw

    sym = "QQQ"
    _clear(sym, TF5)
    n = _seed_day(sym, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        # The chunker disagrees with the planner: no plans issued even
        # though missing spans exist. The no-plans branch must consult the
        # planner (via the predicate), not the empty plan list.
        monkeypatch.setattr(mw, "plan_requests", lambda spans, tf: [])
        win.load_chart(sym, TF5, True)
        current = win.status_bar.currentMessage()
        _assert_no_claim(current)
        assert current == f"{sym} — {n} cached bars."
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T31 / AC1 — finalize path with a wave in flight: no claim
# ---------------------------------------------------------------------------
def test_t31_finalize_in_flight_suppresses_claim(monkeypatch, qapp):
    """Finalize racing a wave (planner clean): counts, never currency."""
    sym = "AAPL"
    _clear(sym, TF_DAY)
    n = _seed_daily(sym, N_DAILY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF_DAY, True)
        # Sanity: the covered path still claims exactly as today.
        assert win.status_bar.currentMessage() == (
            f"{sym} — {n} cached bars. Cache current."
        )
        session = win.get_or_create_session(sym)
        # A wave racing finalization (planner-clean cache, reqIds live).
        session._history_req_ids.add(97001)
        win._finalize_history_wave(session)
        current = win.status_bar.currentMessage()
        _assert_no_claim(current)
        assert "Finalized while a wave is in flight" in current
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T31 / AC1 — finalize path with a planner hole: shortfall shape, no claim
# ---------------------------------------------------------------------------
def test_t31_finalize_planner_hole_keeps_shortfall_shape(
    monkeypatch, qapp
):
    """Planner hole below day presence: same shortfall shape, no claim."""
    import ui.main_window as mw

    sym = "MSFT"
    _clear(sym, TF_DAY)
    _seed_daily(sym, N_DAILY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF_DAY, True)
        session = win.get_or_create_session(sym)
        hole_day = date(2026, 9, 30)
        assert is_trading_day(hole_day)
        span = MissingSpan(
            start_ts=_et_ts(2026, 9, 30), end_ts=_et_ts(2026, 10, 1)
        )
        monkeypatch.setattr(mw, "find_missing_spans", lambda *a, **k: [span])
        # Predicate and shortfall recompute consult the same planner.
        assert win._is_cache_current(sym, TF_DAY, True) is False
        win._finalize_history_wave(session)
        current = win.status_bar.currentMessage()
        _assert_no_claim(current)
        days = trading_days(span.start_ts, span.end_ts)
        assert len(days) >= 1
        preview = ", ".join(d.isoformat() for d in days[:5])
        assert current == (
            f"{sym} — backfill incomplete: {len(days)} trading day(s) "
            f"still missing ({preview})."
        )
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T32 / AC2 — stranded-with-missing-days: verbatim AC-D16.4 shortfall
# ---------------------------------------------------------------------------
def test_t32_stranded_watchdog_verbatim_shortfall(monkeypatch, qapp):
    """Watchdog-stranded wave: exact shortfall, unchanged wording, no claim."""
    sym = "SPY"
    _clear(sym, TF5)
    _seed_day(sym, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF5, True)
        wave = _wave_calls(stub)
        assert len(wave) >= 2  # a genuine multi-chunk wave is in flight
        session = win.get_or_create_session(sym)
        assert session._history_req_ids  # stranded while reqIds live

        win._on_session_history_wave_timeout(session)

        # Expected shortfall recomputed from the wave's own spans (no bar
        # was ever fetched, so every spanned trading day is missing).
        expected_days: list = []
        for span in session._backfill_missing_spans:
            expected_days.extend(trading_days(span.start_ts, span.end_ts))
        assert expected_days
        preview = ", ".join(d.isoformat() for d in expected_days[:5])
        expected = (
            f"{sym} — backfill incomplete: "
            f"{len(expected_days)} trading day(s) "
            f"still missing ({preview}). [Historical backfill timed out]"
        )
        current = win.status_bar.currentMessage()
        assert current == expected
        _assert_no_claim(current)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T33 / AC3 — zero-missing, no-wave load: currency exactly as today
# ---------------------------------------------------------------------------
def test_t33_zero_missing_reports_currency_exact(monkeypatch, qapp):
    """Complete daily cache, no wave: the exact currency line, gated True."""
    sym = "NVDA"
    _clear(sym, TF_DAY)
    n = _seed_daily(sym, N_DAILY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF_DAY, True)
        assert win.status_bar.currentMessage() == (
            f"{sym} — {n} cached bars. Cache current."
        )
        # The predicate itself: clean triple with no wave is current…
        assert win._is_cache_current(sym, TF_DAY, True) is True
        # …an in-flight wave alone suppresses it…
        session = win.get_or_create_session(sym)
        session._history_req_ids.add(98001)
        try:
            assert win._is_cache_current(sym, TF_DAY, True) is False
        finally:
            session._history_req_ids.discard(98001)
        assert win._is_cache_current(sym, TF_DAY, True) is True
    finally:
        win.close()


def test_t33_predicate_false_on_planner_missing(monkeypatch, qapp):
    """Incomplete 5-min cache (floor unfilled): predicate False, no wave."""
    sym = "AMD"
    _clear(sym, TF5)
    _seed_day(sym, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        _stub_feed(win, _ReqStub())
        assert win._is_cache_current(sym, TF5, True) is False
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T34 / AC4 — batch history gate over requirements.md
# ---------------------------------------------------------------------------
def test_t34_history_markers_intact():
    """D41–D52 headings, marker sentence, Current Tech Stack, snapshot pin."""
    import pathlib

    text = pathlib.Path("docs/requirements/requirements.md").read_text()
    for num in range(41, 53):
        assert f"\n### D{num} " in text, f"### D{num} heading missing"
    assert "This is an existing repository." in text  # marker sentence
    assert "Current Tech Stack:" in text
    # The batch's own additions landed.
    assert "\n### D53 " in text
    assert "Journey 46" in text
    assert "AC-D53.3" in text
    assert "A144" in text
    assert "R107" in text
    # No pre-D53 wording touched since the recorded snapshot.
    head, sep, _tail = text.partition("\n### D53 ")
    assert sep
    assert (
        hashlib.sha256(head.encode()).hexdigest() == PRE_D53_SHA256
    ), "pre-D53 requirements text changed"
