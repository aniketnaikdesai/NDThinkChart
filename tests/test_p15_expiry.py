"""P15-T1 (D54.1) — T0-anchored single-shot expiry verdict at T0+10 s (S-P15-1).

Offscreen MainWindow tests (``IBApiClient.connect`` monkeypatched, historical
feed stubbed, clock-controlled T0) proving the per-wave expiry armed at wave
raise from the stamped-once ``_backfill_wave_start`` baseline (T0 = Load
Chart invocation; a coalesced same-triple reload never re-stamps it):

- T11 / AC1: an incomplete wave at T0+10 s renders arrived bars plus the
  verbatim AC-D16.4 shortfall for the missing remainder.
- T12 / AC1: zero arrived bars at T0+10 s — the shortfall lists every missing
  trading day and no bar is fabricated.
- T13 / AC2: completion at T0+9.9 s, and separately exactly at T0+10.0 s,
  takes the normal completion path; the expiry render path never runs.
- T14 / AC3: after a terminal path (normal completion, stranded
  finalization) the expiry is disarmed and never fires on the dead wave.

The T0+10 s firing itself is simulated by driving ``_on_backfill_expiry``
directly: the single-shot Qt timer is armed for a real 10 s at raise (so the
disarm assertions below read the real timer state), which cannot elapse
inside an offscreen test. Nothing here weakens, skips or rewrites an
existing test.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timezone

import pytest
from PyQt6.QtWidgets import QDockWidget

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from services.market_calendar import is_trading_day, trading_days

EASTERN = ZoneInfo("America/New_York")

SYMBOL = "SPY"
SYMBOL2 = "QQQ"
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


def _live_wave(monkeypatch, qapp, symbol: str = SYMBOL):
    """Seed + load a genuine multi-chunk in-flight wave; return (win, stub)."""
    _clear(symbol, TF)
    seed_count = _seed_day(symbol, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, TF, stub, NOW_TS)
    except Exception:
        win.close()
        raise
    return win, stub, seed_count


def _live_wave_empty(monkeypatch, qapp, symbol: str = SYMBOL):
    """Load with an empty cache: the planner emits one floor span.

    The filled wave (31 days x 192 bars) fits the retention budget, so a
    fully-fed wave finalizes through the clean completion line with no
    shortfall — unlike the seeded multi-chunk wave, whose refill exceeds
    the budget and is pruned back to a shortfall by pre-existing retention.
    """
    _clear(symbol, TF)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, TF, stub, NOW_TS)
    except Exception:
        win.close()
        raise
    return win, stub


def _span_days(session) -> list:
    """Every trading day the planner flagged missing for this wave's load."""
    return sorted(
        {
            day
            for span in session._backfill_missing_spans
            for day in trading_days(span.start_ts, span.end_ts)
        }
    )


def _feed_full_day(win, req_id: int, symbol: str, day: date) -> set[int]:
    """Feed one complete session of bars on one wave member; return fed ts."""
    fed: set[int] = set()
    for b in _session_bars(symbol, day):
        win._on_historical_bar(req_id, _FakeIbBar(b.ts, b.close, b.volume))
        fed.add(b.ts)
    return fed


# ---------------------------------------------------------------------------
# T11 / AC1 — incomplete wave at T0+10 s: arrived bars + shortfall verdict
# ---------------------------------------------------------------------------
def test_t11_expiry_renders_partial_bars_plus_shortfall(monkeypatch, qapp):
    win, stub, _seed_count = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2  # a genuine multi-chunk wave is in flight
        session = win.get_or_create_session(SYMBOL)
        assert win._backfill_wave_start is not None  # T0 stamped at raise
        assert win._backfill_expiry_timer.isActive()  # armed once at raise

        missing = _span_days(session)
        assert len(missing) >= 2
        fed_day = min(missing)
        fed_ts = _feed_full_day(win, wave[0]["reqId"], SYMBOL, fed_day)
        # No end marker anywhere: the wave is still incomplete at T0+10 s.
        assert session._history_req_ids  # still in flight

        win._on_backfill_expiry()  # simulate the T0+10 s firing
        qapp.processEvents()

        # Arrived bars render on the chart…
        shown = {b.ts for b in session.get_bars(TF)}
        assert fed_ts <= shown
        # …plus the verbatim AC-D16.4 shortfall for the missing remainder.
        remainder = [d for d in missing if d != fed_day]
        msg = win.status_bar.currentMessage()
        assert "backfill incomplete" in msg
        assert f"{len(remainder)} trading day(s) still missing" in msg
        assert remainder[0].isoformat() in msg
        # The wave itself continues: indicator live, members still tracked.
        assert win._backfill_state is not None
        assert win._backfill_indicator.text() != "Backfill: idle"
        assert session._history_req_ids
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T12 / AC1 — zero arrived bars at T0+10 s: every missing day listed
# ---------------------------------------------------------------------------
def test_t12_expiry_with_zero_bars_lists_all_missing_days(monkeypatch, qapp):
    win, stub, seed_count = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(SYMBOL)
        shown_before = [b.ts for b in session.get_bars(TF)]
        assert len(shown_before) == seed_count
        missing = _span_days(session)
        assert missing  # there is a genuine remainder to list

        win._on_backfill_expiry()  # T0+10 s with nothing arrived
        qapp.processEvents()

        # The shortfall lists every missing trading day…
        assert win._missing_backfill_trading_days(session, session.get_bars(TF)) == missing
        msg = win.status_bar.currentMessage()
        assert "backfill incomplete" in msg
        assert f"{len(missing)} trading day(s) still missing" in msg
        for day in missing[:5]:  # the message preview names the first five
            assert day.isoformat() in msg
        # …and no bar is fabricated: the chart still holds exactly the seed.
        shown_after = [b.ts for b in session.get_bars(TF)]
        assert shown_after == shown_before
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T13 / AC2 — completion at T0+9.9 s and exactly at T0+10.0 s: normal path
# ---------------------------------------------------------------------------
def _complete_wave_fully(win, stub) -> None:
    """Feed every missing day in full, then end every issued member."""
    session = win.get_or_create_session(SYMBOL)
    req_ids = [c["reqId"] for c in _wave_calls(stub)]
    assert req_ids
    # Round-robin full sessions across members so each chunk persists ≥1 bar.
    for i, day in enumerate(_span_days(session)):
        _feed_full_day(win, req_ids[i % len(req_ids)], SYMBOL, day)
    for req_id in req_ids:
        win._on_historical_data_end(req_id)


@pytest.mark.parametrize("offset_s", [9.9, 10.0])
def test_t13_completion_by_bound_never_takes_expiry_path(
    monkeypatch, qapp, offset_s: float
):
    # NOTE (P15-T1): the completable wave is the empty-cache wave. The
    # seeded multi-chunk wave's full refill (~8.4k bars) exceeds the
    # floor-aware retention keep (6624 bars @ 5-min ETH), so the unchanged
    # _finalize_history_wave prune re-opens the oldest spans as shortfall
    # by pre-existing D28.4 retention — a fully-fed seeded wave can never
    # take the clean completion line T13 asserts. The empty-cache wave's
    # floor-span refill fits the budget and finalizes clean (see
    # _live_wave_empty); every assertion below is unchanged.
    win, stub = _live_wave_empty(monkeypatch, qapp)
    try:
        session = win.get_or_create_session(SYMBOL)
        # Clock control: T0 is the stamped baseline; complete the wave at
        # T0+offset and let the bound pass afterwards.
        t0 = session._wave_start_ts
        assert t0 is not None
        clock = {"t": float(t0)}
        monkeypatch.setattr(time, "time", lambda: clock["t"])

        clock["t"] = float(t0) + offset_s
        _complete_wave_fully(win, stub)
        qapp.processEvents()

        # Normal completion path: no shortfall, indicator idle, disarmed.
        msg = win.status_bar.currentMessage()
        assert "backfill incomplete" not in msg
        assert "bars" in msg and "Stream" in msg
        assert win._backfill_state is None
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert session._wave_start_ts is None
        assert not win._backfill_expiry_timer.isActive()

        # The bound passes with the wave already complete: driving the
        # expiry changes nothing — the render path never runs.
        rendered: list = []
        real_set_bars = session.set_bars

        def _spy(tf, bars):
            rendered.append((tf, len(bars)))
            return real_set_bars(tf, bars)

        monkeypatch.setattr(session, "set_bars", _spy)
        clock["t"] = float(t0) + 30.0
        win._on_backfill_expiry()
        qapp.processEvents()
        assert rendered == []
        assert win.status_bar.currentMessage() == msg
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T14 / AC3 — terminal paths disarm the expiry; it never fires afterwards
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["normal", "stranded"])
def test_t14_terminal_path_disarms_expiry(monkeypatch, qapp, path: str):
    win, stub, _seed_count = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(SYMBOL)

        clears: list = []
        real_clear = win.clear_backfill_indicator

        def _spy_clear():
            clears.append(None)
            return real_clear()

        monkeypatch.setattr(win, "clear_backfill_indicator", _spy_clear)

        if path == "normal":
            # Per-chunk completion to empty: the last end marker finalises.
            for c in wave:
                anchor = _parse_end(c["endDateTime"])
                win._on_historical_bar(c["reqId"], _FakeIbBar(anchor - 60, 101.0))
                win._on_historical_data_end(c["reqId"])
        else:
            # Watchdog strand injection finalises through the stranded path.
            win._on_session_history_wave_timeout(session)

        assert len(clears) == 1
        assert win._backfill_state is None
        assert not win._backfill_expiry_timer.isActive()  # disarmed

        # Past the bound the dead wave stays finalized: driving the expiry
        # renders nothing, resurfaces nothing, clears nothing further.
        rendered: list = []
        real_set_bars = session.set_bars

        def _spy_set(tf, bars):
            rendered.append((tf, len(bars)))
            return real_set_bars(tf, bars)

        monkeypatch.setattr(session, "set_bars", _spy_set)
        msg = win.status_bar.currentMessage()
        bars_before = list(session.get_bars(TF))
        win._on_backfill_expiry()
        qapp.processEvents()
        assert rendered == []
        assert win.status_bar.currentMessage() == msg
        assert list(session.get_bars(TF)) == bars_before
        assert len(clears) == 1
        assert win._backfill_indicator.text() == "Backfill: idle"
    finally:
        win.close()
