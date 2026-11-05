"""P15-T3 (D54.3/D54.4) — expiry surfacing on the D53 indicator + batch gate.

Offscreen MainWindow tests (``IBApiClient.connect`` monkeypatched, historical
feed stubbed) proving:

* T31/AC1 — at/after a missed T0+10 s expiry with spans still missing, the
  D53 indicator carries the explicit ``(partial)`` marker, the verbatim
  AC-D16.4 shortfall (missing-days + reason) stays visible, and no
  current-cache claim from the claim family is shown — in the in-flight,
  stranded, and post-expiry-continuation cases.
* T32/AC2 — a wave complete by T0+10 s surfaces as complete through the
  unchanged completion path: no partial marker, no shortfall line.
* T33/AC3 — docs/requirements/requirements.md keeps the ### D41..### D53
  history (reversals intact), the Existing Repository marker sentence and
  the Current Tech Stack, with no pre-P15 wording touched (pinned against
  the P14-recorded pre-D53 snapshot for the D41–D52 region, plus the D53
  section's own rows and the D54 phase block); the offscreen suite gate is
  this file's own green run.

Helpers mirror ``tests/test_p14_cache_guard.py`` (seeded ``BarCache`` +
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

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.models import Bar
from services.market_calendar import is_trading_day, trading_days

EASTERN = ZoneInfo("America/New_York")

TF5 = "5 mins"
TF_DAY = "1 day"
SEED_DAY = date(2026, 8, 3)  # one complete old 5-min session; everything since is missing
NOW_TS = int(datetime(2026, 10, 2, 20, 0, tzinfo=EASTERN).timestamp())
N_DAILY = 15  # seeded complete daily sessions ending on 2026-10-02

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

# P16-narrowed snapshot (tests/test_p14_cache_guard.py::PROTECTED_SPAN_SHA256):
# sha256 of the protected span only — from the Existing Repository marker
# sentence through the end of the D52 section (up to "\n### D53 ").
# Top-of-file navigation/baseline blocks sit outside the pin by design.
# Reproving it here shows no protected wording moved under P15 either.
PROTECTED_SPAN_SHA256 = (
    "2fe7b1ec62fa0e60c7292731e22569f616fdac95becbff8e00d4ee38cee0c139"
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
# T31 / AC1 — missed expiry with spans missing: partial marker + shortfall,
# no current-cache claim (in-flight case)
# ---------------------------------------------------------------------------
def test_t31_expiry_in_flight_partial_marker_shortfall_no_claim(
    monkeypatch, qapp
):
    """Incomplete wave at T0+10 s: marker on the indicator, shortfall kept."""
    sym = "SPY"
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

        # Miss the bound: the single-shot expiry fires with spans missing.
        win._on_backfill_expiry()

        indicator = win._backfill_indicator.text()
        assert indicator.startswith("Backfill (partial):")
        assert "in flight" in indicator
        assert "reqIds=" in indicator
        current = win.status_bar.currentMessage()
        assert "backfill incomplete:" in current
        assert "trading day(s) still missing" in current
        _assert_no_claim(indicator)
        _assert_no_claim(current)
        # The unchanged gate is what suppresses the claim family.
        assert win._is_cache_current(sym, TF5, True) is False
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T31 / AC1 — stranded case: expiry first (marker shown), then the watchdog
# strand finalizes — shortfall with cause, no claim, terminal path unchanged
# ---------------------------------------------------------------------------
def test_t31_expiry_then_strand_shortfall_no_claim_terminal_idle(
    monkeypatch, qapp
):
    """Stranded-after-expiry: marker at the miss, shortfall + idle at rest."""
    sym = "QQQ"
    _seed_day(sym, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF5, True)
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(sym)
        assert session._history_req_ids

        # The miss surfaces on the live wave first.
        win._on_backfill_expiry()
        assert win._backfill_indicator.text().startswith(
            "Backfill (partial):"
        )
        assert "backfill incomplete:" in win.status_bar.currentMessage()

        # Then the watchdog strands the still-incomplete wave.
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
        # The terminal path is unchanged: indicator back to idle, latch
        # cleared with the wave — the marker was a live-wave state only.
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert win._backfill_expiry_missed is False
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T31 / AC1 — post-expiry continuation: per-chunk progress refreshes keep
# the partial marker until the wave terminates
# ---------------------------------------------------------------------------
def test_t31_post_expiry_progress_keeps_partial_marker(monkeypatch, qapp):
    """Background-continue past expiry: chunk ends keep the marker, no claim."""
    sym = "AAPL"
    _seed_day(sym, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF5, True)
        assert len(_wave_calls(stub)) >= 2
        session = win.get_or_create_session(sym)
        assert session._history_req_ids

        win._on_backfill_expiry()
        assert win._backfill_indicator.text().startswith(
            "Backfill (partial):"
        )

        # Pin one member so the wave cannot terminate mid-case; every real
        # end marker then travels the genuine per-chunk path while live.
        session._register_history_request(999001)
        try:
            live = sorted(
                rid for rid in session._history_req_ids if rid != 999001
            )
            assert live  # the wave really is still in flight
            for rid in live:
                win._on_historical_data_end(rid)
                assert win._backfill_indicator.text().startswith(
                    "Backfill (partial):"
                )
            # Still live (pinned member) with the baseline kept: the
            # background-continue wave, indicator still running.
            assert session._history_req_ids
            assert win._backfill_wave_start is not None
            indicator = win._backfill_indicator.text()
            assert indicator.startswith("Backfill (partial):")
            _assert_no_claim(indicator)
            _assert_no_claim(win.status_bar.currentMessage())
        finally:
            session._history_req_ids.discard(999001)
            session._history_req_generation.pop(999001, None)
            session._req_bars.pop(999001, None)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T32 / AC2 — complete cache (wave complete by the bound): currency line,
# idle indicator, stray expiry a silent no-op
# ---------------------------------------------------------------------------
def test_t32_complete_cache_currency_idle_no_marker(monkeypatch, qapp):
    """Complete triple: exact currency line, no marker, no shortfall."""
    sym = "NVDA"
    n = _seed_daily(sym, N_DAILY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF_DAY, True)
        assert win.status_bar.currentMessage() == (
            f"{sym} — {n} cached bars. Cache current."
        )
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "(partial)" not in win._backfill_indicator.text()
        assert "backfill incomplete" not in win.status_bar.currentMessage()
        assert win._backfill_wave_start is None
        assert win._backfill_expiry_missed is False

        # A stray/late expiry with no live wave is a silent no-op.
        win._on_backfill_expiry()
        assert win.status_bar.currentMessage() == (
            f"{sym} — {n} cached bars. Cache current."
        )
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "(partial)" not in win._backfill_indicator.text()
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T32 / AC2 — wave completing before the bound through the real end-marker
# funnel: unchanged completion line, no marker, no shortfall, expiry silent
# ---------------------------------------------------------------------------
def test_t32_wave_completed_before_bound_no_marker_no_shortfall(
    monkeypatch, qapp
):
    """Real completion funnel: completion line, idle, stray expiry silent."""
    sym = "TSLA"
    n = _seed_daily(sym, N_DAILY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _stub_feed(win, stub)
        win.load_chart(sym, TF_DAY, True)
        session = win.get_or_create_session(sym)
        # One wave member through the real registration seam, ended
        # through the real end-marker funnel → genuine completion path.
        session._register_history_request(995001)
        win._on_historical_data_end(995001)

        current = win.status_bar.currentMessage()
        assert current.startswith(f"{sym} — {n} bars (0 new). Stream ")
        assert "backfill incomplete" not in current
        assert "(partial)" not in win._backfill_indicator.text()
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert win._backfill_expiry_missed is False

        # The bound expiry on the completed wave never takes the miss path.
        win._on_backfill_expiry()
        assert win.status_bar.currentMessage() == current
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert "(partial)" not in win._backfill_indicator.text()
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T33 / AC3 — batch history gate over requirements.md
# ---------------------------------------------------------------------------
def test_t33_history_markers_intact():
    """D41–D53 headings, reversals, marker sentence, Tech Stack, D54 block."""
    import pathlib

    text = pathlib.Path("docs/requirements/requirements.md").read_text()
    for num in range(41, 54):
        assert f"\n### D{num} " in text, f"### D{num} heading missing"
    # Reversals stay recorded, never rewritten.
    assert "REVERSED BY D45" in text
    assert "A87 is REVERSED" in text
    assert "SUPERSEDED BY D47" in text
    # Existing Repository marker sentence + Current Tech Stack intact.
    assert "This is an existing repository." in text
    assert "Current Tech Stack:" in text
    # The D53 batch's own rows (now pre-P15 wording) are intact.
    assert "\n### D53 " in text
    assert "Journey 46" in text
    assert "AC-D53.3" in text
    assert "A144" in text
    assert "R107" in text
    # The phase's own additions landed.
    assert "## Phase P15" in text
    assert "Journey 47" in text
    assert "AC-D54.1" in text
    assert "AC-D54.3" in text
    assert "AC-D54.4" in text
    assert "A148" in text
    assert "R108" in text
    # No protected wording touched: the marker-through-D52 span still matches
    # the P16-narrowed snapshot.
    head, sep, _tail = text.partition("\n### D53 ")
    assert sep
    start = text.index("This is an existing repository.")
    span = text[start : text.index("\n### D53 ")]
    assert (
        hashlib.sha256(span.encode()).hexdigest() == PROTECTED_SPAN_SHA256
    ), "protected requirements history span changed"
