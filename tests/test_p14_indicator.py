"""P14-T1 (D53.1) — persistent backfill-state indicator (S-P14-1).

Offscreen MainWindow tests (``IBApiClient.connect`` monkeypatched, historical
feed stubbed) proving the indicator is a permanent status-bar widget that is
raised on wave issue (queue-only waves included), refreshed on wave events, and
immune to transient ``showMessage`` traffic — while every pre-existing
transient text/timing stays byte-identical.

Helpers mirror ``tests/test_history_backfill.py`` (seeded ``BarCache`` +
stubbed ``req_historical_data``); nothing here weakens, skips or rewrites an
existing test.
"""

from __future__ import annotations

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
from ibkr.pacing import PacingExceeded
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")

SYMBOL = "SPY"
TF = "5 mins"
SEED_DAY = date(2026, 8, 3)  # one complete old session; everything since is missing
NOW_TS = int(datetime(2026, 10, 2, 20, 0, tzinfo=EASTERN).timestamp())


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _session_bars(symbol: str, day: date, base: float = 100.0) -> list[Bar]:
    """One deterministic complete 5-min session (04:00-20:00 ET)."""
    assert is_trading_day(day)
    period = TIMEFRAME_SECONDS[TF]
    start = _et_ts(day.year, day.month, day.day, 4, 0)
    close = _et_ts(day.year, day.month, day.day, 20, 0)
    bars: list[Bar] = []
    ts, i = start, 0
    while ts < close:
        price = base + (i % 5) * 0.25
        bars.append(
            Bar(symbol, TF, ts, price, price + 0.5, price - 0.5, price,
                1000.0 + (ts % 500))
        )
        ts += period
        i += 1
    return bars


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


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0, volume: float = 1000.0):
        self.date = str(int(ts))
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = volume


class _ReqStub:
    """Captures ``req_historical_data`` calls; optionally pacing-fails."""

    def __init__(self, first_id: int = 5000, fail_with_pacing: bool = False):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self.fail_with_pacing = fail_with_pacing
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, bar_size=None, duration=None):
        if self.fail_with_pacing:
            raise PacingExceeded(5.0)
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
    win.show()
    qapp.processEvents()
    for dock in win.findChildren(QDockWidget):
        if dock.windowTitle() in ("Portfolio",):
            dock.hide()
    qapp.processEvents()
    return win


def _load(win, symbol: str, tf: str, stub: _ReqStub, now_ts: int) -> None:
    """Drive the real ``load_chart`` against the stubbed manager at fixed now."""
    win._now_ts = lambda: now_ts
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(tf)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()


def _parse_end(end: str) -> int:
    return int(
        datetime.strptime(end, "%Y%m%d-%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    )


def _required_keys(state: dict) -> None:
    """AC2 at-least content set: in-flight, queue, elapsed, reqIds."""
    assert set(("in_flight", "queued", "elapsed_s", "req_ids")) <= set(state.keys())
    assert isinstance(state["in_flight"], int)
    assert isinstance(state["queued"], int)
    assert isinstance(state["elapsed_s"], float)
    assert isinstance(state["req_ids"], list)
    assert state["elapsed_s"] >= 0.0


# ---------------------------------------------------------------------------
# T11 / AC1 — indicator survives unrelated transient showMessage traffic
# ---------------------------------------------------------------------------
def test_t11_indicator_identity_and_state_survive_transient_traffic(
    monkeypatch, qapp
):
    _clear(SYMBOL, TF)
    _seed_day(SYMBOL, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, SYMBOL, TF, stub, NOW_TS)
        wave = _wave_calls(stub)
        assert len(wave) >= 2  # multi-chunk in-flight wave

        indicator = win._backfill_indicator
        assert indicator is not None
        before = dict(win._backfill_state)
        _required_keys(before)
        assert before["in_flight"] == len(wave)
        assert before["queued"] == 0
        assert sorted(before["req_ids"]) == sorted(c["reqId"] for c in wave)

        # Unrelated transient traffic: the account-summary receipt shape.
        win.status_bar.showMessage(
            f"Account summary received for {SYMBOL}", 4000
        )

        assert win._backfill_indicator is indicator
        assert win._backfill_state == before
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T12 / AC2 — at-least content at every instant, incl. the queue-only instant
# ---------------------------------------------------------------------------
def test_t12_indicator_reports_at_least_set_at_each_wave_instant(
    monkeypatch, qapp
):
    _clear(SYMBOL, TF)
    _seed_day(SYMBOL, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub(fail_with_pacing=True)
        _load(win, SYMBOL, TF, stub, NOW_TS)

        # Instant 0 — queue-only: everything queued, zero in flight.
        queued_0 = dict(win._backfill_state)
        _required_keys(queued_0)
        assert queued_0["in_flight"] == 0
        assert queued_0["queued"] >= 2
        assert queued_0["req_ids"] == []
        n_plans = queued_0["queued"]

        # Continuation tick: pacing clears, the queued wave issues.
        stub.fail_with_pacing = False
        session = win.get_or_create_session(SYMBOL)
        session._on_wave_continue_timeout()
        win._refresh_backfill_indicator(session)
        issued = dict(win._backfill_state)
        _required_keys(issued)
        assert issued["in_flight"] == n_plans
        assert issued["queued"] == 0
        assert sorted(issued["req_ids"]) == sorted(
            c["reqId"] for c in _wave_calls(stub)
        )
        assert issued["elapsed_s"] >= queued_0["elapsed_s"]

        # First-chunk progress: one end marker drains one in-flight reqId.
        first = _wave_calls(stub)[0]
        anchor = _parse_end(first["endDateTime"])
        win._on_historical_bar(
            first["reqId"], _FakeIbBar(anchor - 60, 101.0)
        )
        win._on_historical_data_end(first["reqId"])
        progress = dict(win._backfill_state)
        _required_keys(progress)
        assert progress["in_flight"] == n_plans - 1
        assert progress["queued"] == 0
        assert first["reqId"] not in progress["req_ids"]
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T13 / AC3 — pre-existing transient texts and timings are byte-identical
# ---------------------------------------------------------------------------
def test_t13_transient_showmessage_sequence_unchanged(monkeypatch, qapp):
    _clear(SYMBOL, TF)
    seeded_count = _seed_day(SYMBOL, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        calls: list[tuple] = []
        orig = win.status_bar.showMessage

        def _rec(msg, timeout=0):
            calls.append((msg, timeout))
            return orig(msg, timeout)

        monkeypatch.setattr(win.status_bar, "showMessage", _rec)

        stub = _ReqStub()
        _load(win, SYMBOL, TF, stub, NOW_TS)
        n_plans = len(_wave_calls(stub))
        assert n_plans >= 2

        # Coalesced same-triple reload mid-wave (Branch-A early return).
        win.load_chart()

        assert calls == [
            (f"{SYMBOL} — {seeded_count} cached bars. Fetching delta…", 0),
            (f"{SYMBOL} — backfilling {n_plans} historical chunk(s)…", 0),
            (
                f"{SYMBOL} — already backfilling; reload coalesced into "
                "the running wave…",
                4000,
            ),
        ]
    finally:
        win.close()
