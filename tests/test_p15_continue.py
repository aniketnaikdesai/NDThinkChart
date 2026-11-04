"""P15-T2 (D54.2) — background-continue past expiry with lifecycle seams.

Offscreen MainWindow tests (``IBApiClient.connect`` monkeypatched, historical
feed stubbed, clock controlled) proving the P15-T1 expiry verdict is pure:

- T21 / AC1: past T0+10 s the incomplete wave continues under the unchanged
  D53 lifecycle — wave state continued, indicator still running, late bars
  rendered — and ends through the normal path with no cancel-at-10 s.
- T22 / AC2: a disconnect at T0+9.9 s via the real ``_on_disconnected`` path
  wins over the pending expiry — the disconnect funnel runs exactly once and
  the expiry never fires on the dead wave.
- T23 / AC3: a mid-wave mode-switch and, separately, a new-triple symbol load
  cancel the old wave with its expiry and re-anchor T0 on the new wave (old
  reqIds fenced by generation).
- T24 / AC3: a mid-wave same-triple reload (Branch-A coalesced keep) keeps the
  original T0 with no extension and leaves the running wave untouched.

Helpers mirror ``tests/test_p14_lifecycle.py`` (seeded ``BarCache`` +
stubbed ``req_historical_data``); nothing here weakens, skips or rewrites an
existing test.
"""

from __future__ import annotations

import logging
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
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")

SYMBOL = "SPY"
SYMBOL2 = "QQQ"
TF = "5 mins"
SEED_DAY = date(2026, 8, 3)  # one complete old session; everything since is missing
NOW_TS = int(datetime(2026, 10, 2, 20, 0, tzinfo=EASTERN).timestamp())
T_START = 1_700_000_000.0


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


def _freeze_clock(monkeypatch):
    """Pin ``time.time`` to a controllable box (the T0 clock control)."""
    now = [T_START]
    monkeypatch.setattr(time, "time", lambda: now[0])
    return now


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
    _seed_day(symbol, SEED_DAY)
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        _load(win, symbol, TF, stub, NOW_TS)
    except Exception:
        win.close()
        raise
    return win, stub


def _land_chunk(win, call: dict, price: float = 101.0) -> None:
    """Land one full chunk (one bar + end marker) through the real slots."""
    anchor = _parse_end(call["endDateTime"])
    win._on_historical_bar(call["reqId"], _FakeIbBar(anchor - 60, price))
    win._on_historical_data_end(call["reqId"])


class _LogCapture(logging.Handler):
    """Collect rendered log records off the ``ui.main_window`` logger."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _shortfalls(cap: _LogCapture) -> list[logging.LogRecord]:
    # NOTE: the WARNING log wording ("Historical backfill shortfall …")
    # differs from the status-bar wording ("… backfill incomplete: …");
    # both carry the verbatim AC-D16.4 shortfall for the same event.
    return [r for r in cap.records if "Historical backfill shortfall" in r.getMessage()]


# ---------------------------------------------------------------------------
# T21 / AC1 — the wave continues past expiry and finalizes through the
# unchanged normal path (no cancel-at-10 s)
# ---------------------------------------------------------------------------
def test_t21_wave_continues_past_expiry_and_finalizes_normally(
    monkeypatch, qapp
):
    now = _freeze_clock(monkeypatch)
    win, stub = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2  # a genuine multi-chunk wave is in flight
        session = win.get_or_create_session(SYMBOL)
        t0 = win._backfill_wave_start
        assert t0 == T_START  # T0 anchored at the Load Chart invocation
        old_ids = [c["reqId"] for c in wave]
        gen_before = session._history_generation
        queue_before = list(session._wave_plan_queue)
        assert win._backfill_expiry_timer.isActive()  # expiry armed
        assert win._backfill_state is not None  # indicator running

        # T0+10 s with the wave still incomplete: the P15-T1 verdict fires.
        # (The single-shot spends itself at the firing instant; invoking the
        # handler is the deterministic form of that instant.)
        now[0] = t0 + 10.0
        win._backfill_expiry_timer.stop()
        win._on_backfill_expiry()

        # AC1: the wave is untouched — still in flight, same generation,
        # no cancel invented, indicator still running on the original T0.
        assert set(session._history_req_ids) == set(old_ids)
        assert session._history_generation == gen_before
        assert list(session._wave_plan_queue) == queue_before
        assert not any(i in stub.cancelled for i in old_ids)
        assert win._backfill_wave_start == t0
        assert win._backfill_state is not None
        assert win._backfill_indicator.text() != "Backfill: idle"

        # A further chunk lands past expiry: late bars render, wave still live.
        mode = session._wave_extended_hours
        n_before = len(BarCache.get_bars(SYMBOL, TF, ext_hours=mode))
        _land_chunk(win, wave[0])
        n_after = len(BarCache.get_bars(SYMBOL, TF, ext_hours=mode))
        assert n_after == n_before + 1  # the late bar landed and persisted
        assert win._backfill_state is not None  # not finalized mid-wave
        assert win._backfill_state["in_flight"] == len(old_ids) - 1
        assert win._backfill_wave_start == t0  # T0 never extended

        # The rest of the wave completes normally through the unchanged path.
        for c in wave[1:]:
            _land_chunk(win, c)
        assert not session._history_req_ids
        assert win._backfill_state is None
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert session._wave_start_ts is None  # session baseline cleared
        # Still no cancel of the continued wave, no generation fence tripped.
        assert not any(i in stub.cancelled for i in old_ids)
        assert session._history_generation == gen_before
        # The unchanged finalize surfaces the shortfall, never a fresh claim.
        msg = win.status_bar.currentMessage()
        assert "backfill incomplete" in msg
        assert "Cache current" not in msg
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T22 / AC2 — a disconnect at T0+9.9 s wins over the pending expiry
# ---------------------------------------------------------------------------
def test_t22_disconnect_before_expiry_wins_and_expiry_never_fires(
    monkeypatch, qapp
):
    now = _freeze_clock(monkeypatch)
    win, stub = _live_wave(monkeypatch, qapp)
    cap = _LogCapture()
    logger = logging.getLogger("ui.main_window")
    logger.addHandler(cap)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(SYMBOL)
        t0 = win._backfill_wave_start
        assert t0 == T_START
        old_ids = [c["reqId"] for c in wave]
        gen_before = session._history_generation
        assert win._backfill_expiry_timer.isActive()  # expiry pending

        # T0+9.9 s: the transport drops via the real disconnect path.
        now[0] = t0 + 9.9
        win._on_disconnected()

        # The existing disconnect finalization won: one stranded shortfall
        # with the disconnect cause, indicator idle, expiry disarmed, the
        # old reqIds cancelled and fenced by a generation advance.
        assert len(_shortfalls(cap)) == 1
        assert "[Disconnected from IBKR]" in _shortfalls(cap)[0].getMessage()
        assert win._backfill_state is None
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert win._backfill_wave_start is None
        assert not win._backfill_expiry_timer.isActive()
        assert set(old_ids) <= set(stub.cancelled)
        assert session._history_generation == gen_before + 1
        assert not session._history_req_ids
        before = win.status_bar.currentMessage()

        # Past T0+10 s: the expiry instant arrives on the dead wave and is a
        # no-op — no second funnel, no new shortfall, indicator stays idle.
        now[0] = t0 + 11.0
        win._on_backfill_expiry()
        assert len(_shortfalls(cap)) == 1
        assert win._backfill_state is None
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert win._backfill_wave_start is None
        assert win.status_bar.currentMessage() == before

        # A late end marker for a pre-drop reqId is rejected, not finalized.
        win._on_historical_data_end(old_ids[0])
        assert len(_shortfalls(cap)) == 1
        assert win._backfill_state is None
        assert win.status_bar.currentMessage() == before
    finally:
        logger.removeHandler(cap)
        win.close()


# ---------------------------------------------------------------------------
# T23 / AC3 — mid-wave mode-switch / new-triple load cancels the old wave
# with its expiry and re-anchors T0 on the new wave
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["mode-switch", "new-triple"])
def test_t23_seam_load_cancels_old_wave_and_reanchors_t0(
    monkeypatch, qapp, kind: str
):
    now = _freeze_clock(monkeypatch)
    win, stub = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        old_session = win.get_or_create_session(SYMBOL)
        session_mode = old_session._wave_extended_hours
        t0_old = win._backfill_wave_start
        assert t0_old == T_START
        old_ids = [c["reqId"] for c in wave]
        gen_before = old_session._history_generation

        events: list[str] = []
        real_clear = win.clear_backfill_indicator
        real_raise = win._raise_backfill_indicator

        def _spy_clear():
            events.append("clear")
            return real_clear()

        def _spy_raise(session_arg):
            events.append("raise")
            return real_raise(session_arg)

        monkeypatch.setattr(win, "clear_backfill_indicator", _spy_clear)
        monkeypatch.setattr(win, "_raise_backfill_indicator", _spy_raise)

        if kind == "new-triple":
            _clear(SYMBOL2, TF)
            _seed_day(SYMBOL2, SEED_DAY, base=200.0)

        # Mid-wave seam load, 3 s after the old wave raised.
        now[0] = t0_old + 3.0
        n_calls_before = len(stub.calls)
        if kind == "mode-switch":
            win.load_chart(SYMBOL, TF, not session_mode)
        else:
            win.load_chart(SYMBOL2, TF, session_mode)

        # The old wave died with exactly one clear, then the new wave raised
        # exactly once (clear-before-raise: the old expiry was disarmed before
        # the new one armed, so the old expiry can never fire).
        assert events == ["clear", "raise"], f"events={events}"
        # Every old reqId was cancelled…
        assert set(old_ids) <= set(stub.cancelled)
        # …and fenced: same-session switch advanced the generation; the
        # new-triple switch tore the old session down and unrouted its reqIds.
        if kind == "mode-switch":
            assert old_session._history_generation == gen_before + 1
        else:
            assert SYMBOL not in win._sessions
            assert win._session_for_req_id(old_ids[0]) is None
        # T0 re-anchored on the new wave: a fresh stamp at the switch instant.
        assert win._backfill_wave_start == t0_old + 3.0
        assert win._backfill_state is not None
        assert win._backfill_indicator.text() != "Backfill: idle"
        assert win._backfill_expiry_timer.isActive()  # new expiry armed
        # The running wave is genuinely new: fresh reqIds on the live widget.
        new_wave = [c for c in stub.calls[n_calls_before:]
                    if c.get("bar_size") != "5 secs"]
        assert len(new_wave) >= 1
        assert sorted(win._backfill_state["req_ids"]) == sorted(
            c["reqId"] for c in new_wave
        )
        # A late end marker for an old reqId finalizes nothing.
        win._on_historical_data_end(old_ids[0])
        assert win._backfill_state is not None
        assert sorted(win._backfill_state["req_ids"]) == sorted(
            c["reqId"] for c in new_wave
        )
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T24 / AC3 — mid-wave same-triple reload keeps the original T0, untouched
# ---------------------------------------------------------------------------
def test_t24_same_triple_reload_keeps_original_t0(monkeypatch, qapp):
    _freeze_clock(monkeypatch)  # frozen: any re-stamp would still be provable
    win, stub = _live_wave(monkeypatch, qapp)
    try:
        wave = _wave_calls(stub)
        assert len(wave) >= 2
        session = win.get_or_create_session(SYMBOL)
        gen_before = session._history_generation
        t0_before = win._backfill_wave_start
        assert t0_before == T_START
        ts_before = session._wave_start_ts
        assert ts_before is not None
        reqs_before = set(session._history_req_ids)
        queue_before = list(session._wave_plan_queue)
        state_before = dict(win._backfill_state)
        n_calls_before = len(stub.calls)
        assert win._backfill_expiry_timer.isActive()

        cleared: list = []
        raised: list = []
        real_clear = win.clear_backfill_indicator
        real_raise = win._raise_backfill_indicator

        def _spy_clear():
            cleared.append(None)
            return real_clear()

        def _spy_raise(session_arg):
            raised.append(None)
            return real_raise(session_arg)

        monkeypatch.setattr(win, "clear_backfill_indicator", _spy_clear)
        monkeypatch.setattr(win, "_raise_backfill_indicator", _spy_raise)

        win.load_chart()  # same (symbol, timeframe, ext-hours): Branch A

        # No new historical reqId, generation untouched…
        assert len(stub.calls) == n_calls_before
        assert session._history_generation == gen_before
        # …neither terminal seam ran (no clear, no re-raise)…
        assert cleared == []
        assert raised == []
        # …the expiry still belongs to the original wave…
        assert win._backfill_expiry_timer.isActive()
        # …and the original T0 baseline is unreset with the wave untouched.
        assert win._backfill_wave_start == t0_before
        assert session._wave_start_ts == ts_before
        assert set(session._history_req_ids) == reqs_before
        assert list(session._wave_plan_queue) == queue_before
        assert win._backfill_state is not None
        assert win._backfill_state["in_flight"] == state_before["in_flight"]
        assert sorted(win._backfill_state["req_ids"]) == sorted(
            state_before["req_ids"]
        )
        assert win._backfill_indicator.text() != "Backfill: idle"
    finally:
        win.close()
