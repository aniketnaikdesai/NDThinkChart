"""P7-W1 (S-P7-2): per-chunk persist-and-render with resume-not-restart finalisation.

Replaces the all-or-nothing wave finalise: every completed chunk is
``BarCache.save_bars``-persisted and incrementally rendered on arrival, so
killing/reloading mid-wave loses zero fetched bars and overlapping resumes
never duplicate rows (``INSERT OR REPLACE`` idempotence).

T11 — a 2-chunk wave through the real MainWindow load path (fake transport):
    after each chunk-end the cache and the session/chart bars advance while
    the remaining chunk is still in flight; exactly one save plus one set
    per completed chunk.
T12 — interrupt the wave mid-flight (same-symbol reload), then resume:
    the completed chunk's bars survive in cache and on the chart, the cache
    is never smaller than before the wave, the completed span is not
    re-fetched, and the resume converges without re-delivering it.
T13 — unit: the same chunk fed twice yields no duplicate rows with exactly
    one save plus one set per completion; a superseded generation's bars
    and end marker are rejected (fence holds, wave cannot finalise stale).

Fake-transport note: the stub counts/issues reqIds without touching
``pacing_manager``, so the suites are hermetic. The calendar is fixed
(NOW = 2026-11-06 20:00 ET; the Sep28-Oct30 hole chunks into exactly 2
"5 mins" requests under the widened 30 D duration once the 30-session floor
is seeded), so chunk counts and anchors are deterministic forever.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QDockWidget

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from config import settings
from data.bar_cache import BarCache
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.backfill_service import (
    find_missing_spans,
    present_days,
)
from services.market_calendar import is_trading_day
from ui.ticker_session import TickerSession

EASTERN = ZoneInfo("America/New_York")

# Fixed load instant: Friday 2026-11-06 20:00 ET — exactly on a 5-min
# boundary, so there is no aggregator-priming span (prime_aggregator returns
# False) and the wave members are the only requests in flight.
NOW = int(datetime(2026, 11, 6, 20, 0, tzinfo=EASTERN).timestamp())
NOW_DAY = date(2026, 11, 6)
TF = "5 mins"

# The hole: five full trading weeks. Its closure exceeds the widened "5 mins"
# 30 D fetch window (33 calendar days), so the planner chunks it into 2
# requests.
MISSING_DAYS = [
    (2026, 9, 28), (2026, 9, 29), (2026, 9, 30),
    (2026, 10, 1), (2026, 10, 2),
    (2026, 10, 5), (2026, 10, 6), (2026, 10, 7), (2026, 10, 8),
    (2026, 10, 9), (2026, 10, 12), (2026, 10, 13), (2026, 10, 14),
    (2026, 10, 15), (2026, 10, 16), (2026, 10, 19), (2026, 10, 20),
    (2026, 10, 21), (2026, 10, 22), (2026, 10, 23), (2026, 10, 26),
    (2026, 10, 27), (2026, 10, 28), (2026, 10, 29), (2026, 10, 30),
]
_MISSING_SET = {date(*t) for t in MISSING_DAYS}


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _trading_days_back(now_day: date, count: int) -> list[date]:
    days: list[date] = []
    day = now_day
    while len(days) < count:
        if is_trading_day(day):
            days.append(day)
        day -= timedelta(days=1)
    return list(reversed(days))


# 60 trading sessions back from NOW, minus the hole: 35 present sessions, so
# the 30-session depth floor is satisfied and the wave is exactly the hole's
# 2 chunks (no floor span). Bars are native 5-min RTH density (78/day), so
# the whole scenario (60*78 = 4680 bars) fits under the 5000 RTH floor
# budget: nothing is trimmed from memory or retention mid-test, and every
# assertion reads exact sets. Deterministic forever (fixed calendar).
SEED_DAYS = [
    d for d in _trading_days_back(NOW_DAY, 60) if d not in _MISSING_SET
]
assert len(SEED_DAYS) == 35

MODE = False  # RTH: native-density days fit under the floor budget


def _day_bars(symbol: str, day: date) -> list[Bar]:
    """One complete RTH day of 5-min bars (09:30-16:00 ET, 78 bars).

    A "present" day must be genuinely gap-free for the planner's bar-level
    hole detection; the same generator feeds seeded and fetched bars.
    """
    bars: list[Bar] = []
    ts = _et_ts(day.year, day.month, day.day, 9, 30)
    end = _et_ts(day.year, day.month, day.day, 16, 0)
    i = 0
    while ts < end:
        price = 100.0 + (i % 7) * 0.25
        bars.append(Bar(symbol, TF, ts, price, price + 0.5, price - 0.5,
                        price, 1000.0))
        ts += 300
        i += 1
    assert len(bars) == 78
    return bars


def _clear(symbol: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, TF)
    )
    db.conn.commit()


def _seed(symbol: str) -> None:
    bars = [b for day in SEED_DAYS for b in _day_bars(symbol, day)]
    BarCache.save_bars(bars, ext_hours=MODE)


def _cached(symbol: str) -> list[Bar]:
    return BarCache.get_bars(symbol, TF, ext_hours=MODE)


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0):
        self.date = str(int(ts))  # parse_ibkr_date accepts epoch strings
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = 1000


class _ReqStub:
    """Captures ``req_historical_data`` calls and cancelled reqIds."""

    def __init__(self, first_id: int = 3000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, **kwargs):
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
            **kwargs,
        })
        return req_id

    def cancel(self, req_id):
        self.cancelled.append(req_id)


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


def _load(win, symbol: str, stub: _ReqStub) -> None:
    """Drive the real ``load_chart`` against the stubbed manager at fixed NOW."""
    win._now_ts = lambda: NOW
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(TF)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()


def _wave_req_ids(win, session, stub):
    """Issued wave-member reqIds in issue order (priming never issues here)."""
    return [c["reqId"] for c in stub.calls if c["reqId"] in session._history_req_ids]


def _duration_seconds(duration: str) -> int:
    units = {"S": 1, "D": 86400, "W": 604800, "M": 2592000, "Y": 31536000}
    token = (duration or "").strip().upper()
    if token and token[-1] in units and token[:-1].strip().isdigit():
        return int(token[:-1]) * units[token[-1]]
    return int(token)


def _parse_end(end: str) -> int:
    from datetime import timezone
    return int(datetime.strptime(end, "%Y%m%d-%H:%M:%S").replace(
        tzinfo=timezone.utc).timestamp())


def _chunk_ts(call: dict, expected_ts: set[int], delivered: set[int]) -> list[int]:
    """Expected timestamps this chunk's window owns that are not yet delivered."""
    duration = _duration_seconds(TIMEFRAME_CONFIG[TF]["duration"])
    anchor = _parse_end(call["endDateTime"])
    lo, hi = anchor - duration, anchor
    return sorted(
        ts for ts in expected_ts if ts not in delivered and lo < ts <= hi
    )


def _expected_hole_ts(symbol: str) -> set[int]:
    return {b.ts for t in MISSING_DAYS for b in _day_bars(symbol, date(*t))}


def _drive_chunk(win, rid: int, timestamps: list[int]) -> None:
    for ts in timestamps:
        win._on_historical_bar(rid, _FakeIbBar(ts))
    win._on_historical_data_end(rid)


# ---------------------------------------------------------------------------
# T11 — per-chunk persist-and-render while the rest of the wave is in flight
# ---------------------------------------------------------------------------
def test_t11_per_chunk_persist_and_render(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol = "P7W1A"
    try:
        _clear(symbol)
        _seed(symbol)
        stub = _ReqStub()
        win.ext_hours_btn.blockSignals(True)
        win.ext_hours_btn.setChecked(MODE)
        win.ext_hours_btn.blockSignals(False)
        _load(win, symbol, stub)
        assert win.ext_hours_btn.isChecked() == MODE
        session = win.get_or_create_session(symbol)
        req_ids = _wave_req_ids(win, session, stub)
        assert len(req_ids) == 2, f"hole must chunk into 2 requests: {stub.calls}"

        # Spy after load so the initial cached render is not counted.
        real_save = BarCache.save_bars
        save_lengths: list[int] = []
        real_set = TickerSession.set_bars
        set_lengths: list[int] = []

        def spy_save(bars, **kwargs):
            save_lengths.append(len(bars))
            return real_save(bars, **kwargs)

        def spy_set(self, timeframe, bars):
            set_lengths.append(len(bars))
            return real_set(self, timeframe, bars)

        monkeypatch.setattr(BarCache, "save_bars", staticmethod(spy_save))
        monkeypatch.setattr(TickerSession, "set_bars", spy_set)

        expected = _expected_hole_ts(symbol)
        delivered: set[int] = set()
        rows_before = len(_cached(symbol))

        for i, rid in enumerate(req_ids):
            new_ts = _chunk_ts(
                next(c for c in stub.calls if c["reqId"] == rid),
                expected, delivered,
            )
            assert new_ts, f"chunk {i} must own expected bars (setup)"
            _drive_chunk(win, rid, new_ts)
            delivered.update(new_ts)

            # Exactly one save plus one set per completed chunk. The final
            # chunk's end also completes the wave, so the finaliser adds its
            # single final render (no save: the remainder is empty).
            assert len(save_lengths) == i + 1, (
                f"one save per completed chunk, got {save_lengths}"
            )
            expected_sets = i + 1 + (1 if i == len(req_ids) - 1 else 0)
            assert len(set_lengths) == expected_sets, (
                f"one set per completed chunk plus the final render, "
                f"got {len(set_lengths)}"
            )

            # Cache and chart advanced monotonically — before the rest done.
            rows_after = len(_cached(symbol))
            assert rows_after - rows_before == len(new_ts), (
                "cache grows by exactly the new chunk (no duplicates)"
            )
            rows_before = rows_after
            assert delivered <= {b.ts for b in _cached(symbol)}
            assert delivered <= {b.ts for b in session.get_bars(TF)}, (
                "the completed chunk is rendered while others are in flight"
            )
            if i < len(req_ids) - 1:
                assert session._history_req_ids, (
                    "remaining chunks still in flight after a chunk-end"
                )

        # The last end completed the wave: ids empty, finalise ran once.
        assert session._history_req_ids == set()
        # Completed chunks were already persisted: the finaliser owes no
        # save (remainder empty) and adds only the final render.
        assert len(save_lengths) == 2, save_lengths
        assert len(set_lengths) == 3, len(set_lengths)
        assert expected <= {b.ts for b in _cached(symbol)}
        # The wave record is drained by the finalise (pinned finalize
        # contract: the fetched bars live in the cache and on the chart now,
        # so a later reload has nothing to re-flush and cannot re-save them).
        assert session._pending_bars == []
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T12 — interrupted wave resumes instead of restarting
# ---------------------------------------------------------------------------
def test_t12_interrupted_wave_resumes_not_restarts(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    symbol = "P7W1B"
    try:
        _clear(symbol)
        _seed(symbol)
        pre_count = len(_cached(symbol))
        stub = _ReqStub(first_id=4000)
        win.ext_hours_btn.blockSignals(True)
        win.ext_hours_btn.setChecked(MODE)
        win.ext_hours_btn.blockSignals(False)
        _load(win, symbol, stub)
        session = win.get_or_create_session(symbol)
        req_ids = _wave_req_ids(win, session, stub)
        assert len(req_ids) == 2

        expected = _expected_hole_ts(symbol)
        first_call = next(c for c in stub.calls if c["reqId"] == req_ids[0])
        chunk_ts = _chunk_ts(first_call, expected, set())
        assert chunk_ts, "first chunk must own expected bars (setup)"

        # Complete exactly one chunk, then interrupt with a same-target reload.
        _drive_chunk(win, req_ids[0], chunk_ts)
        assert set(chunk_ts) <= {b.ts for b in _cached(symbol)}
        assert session._history_req_ids, "one chunk still in flight"
        n_calls_load1 = len(stub.calls)
        gen_before = session._history_generation

        win.load_chart()  # same symbol/timeframe/mode: resume, not restart
        qapp.processEvents()

        # The completed chunk survives in cache and on the chart; the cache
        # after interruption is never smaller than before the wave started.
        after = _cached(symbol)
        assert len(after) == pre_count + len(chunk_ts)
        assert set(chunk_ts) <= {b.ts for b in after}
        assert set(chunk_ts) <= {b.ts for b in session.get_bars(TF)}, (
            "completed chunk still on the chart after the reload render"
        )

        # T03 landed same-chart coalescing: an identical reload mid-wave
        # cancels nothing, spends no new reqId, and bumps no generation —
        # the remainder continues on its original reqIds (not re-fetched).
        assert len(stub.calls) == n_calls_load1, (
            "coalesced reload issues no new requests"
        )
        assert stub.cancelled == []
        assert session._history_generation == gen_before
        assert set(session._history_req_ids) == set(req_ids[1:])

        # The completed span is not re-fetched: no replan ran at all, and
        # its days are present so no missing span covers them.
        mode = win.ext_hours_btn.isChecked()
        cached_ts = [b.ts for b in BarCache.get_bars(
            symbol, TF, ext_hours=mode)]
        assert {_et_date(ts) for ts in chunk_ts} <= present_days(cached_ts, mode)

        # Resume converges delivering only the remainder — never redelivering
        # the completed chunk — and the hole ends up continuous.
        delivered = set(chunk_ts)
        for _ in range(10):
            pending = [c["reqId"] for c in stub.calls
                       if c["reqId"] in session._history_req_ids]
            if not pending and not session._wave_plan_queue:
                break
            for c in [c for c in stub.calls if c["reqId"] in pending]:
                new_ts = _chunk_ts(c, expected, delivered)
                assert not (set(new_ts) & set(chunk_ts)), (
                    "resume must not re-deliver the completed chunk"
                )
                _drive_chunk(win, c["reqId"], new_ts)
                delivered.update(new_ts)
            if not session._history_req_ids and not session._wave_plan_queue:
                break
            win.load_chart()
        assert session._history_req_ids == set(), "the resumed wave converged"
        assert expected <= {b.ts for b in _cached(symbol)}
        assert delivered == expected
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T13 — overlap idempotence + generation fence (session-level unit)
# ---------------------------------------------------------------------------
class _StubBar:
    def __init__(self):
        self.messages: list = []

    def showMessage(self, msg, ms=0):
        self.messages.append(msg)


class _FakeMD:
    """Counting fake transport: issues reqIds, never paces, never sleeps."""

    def __init__(self):
        self.issued: list = []
        self._next = 8000

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


def test_t13_overlap_idempotent_and_generation_fence(monkeypatch, qapp):
    sym, tf = "P7W1C", "5 mins"
    _clear(sym)

    real_save = BarCache.save_bars
    save_lengths: list[int] = []

    def spy_save(bars, **kwargs):
        save_lengths.append(len(bars))
        return real_save(bars, **kwargs)

    monkeypatch.setattr(BarCache, "save_bars", staticmethod(spy_save))

    host = _StubHost()
    sess = TickerSession(sym, host)
    set_calls: list = []
    sess.bars_refreshed.connect(lambda _tf, bars: set_calls.append(len(bars)))

    plans = [
        SimpleNamespace(endDateTime=f"2026103{i}-04:00:00",
                        bar_size="5 mins", duration="5 D")
        for i in range(1, 4)
    ]
    sess.queue_wave_plans(plans, object(), tf, False)
    r1, r2, r3 = list(host.reg.keys())
    assert len(sess._history_req_ids) == 3

    base = 1_700_000_100
    chunk_ts = [base + k * 300 for k in range(5)]
    for ts in chunk_ts:
        sess.on_historical_bar(r1, _FakeIbBar(ts, price=101.0))
    sess.on_historical_data_end(r1)

    # One save plus one set for the first completion; rows persisted.
    assert save_lengths == [5]
    assert len(set_calls) == 1
    mode_rows = lambda: BarCache.get_bars(sym, tf, ext_hours=False)
    assert {b.ts for b in mode_rows()} == set(chunk_ts)

    # The same chunk re-fetched (overlap): no duplicate rows, still exactly
    # one save plus one set for the completion.
    for ts in chunk_ts:
        sess.on_historical_bar(r2, _FakeIbBar(ts, price=101.0))
    sess.on_historical_data_end(r2)
    assert save_lengths == [5, 5]
    assert len(set_calls) == 2
    assert {b.ts for b in mode_rows()} == set(chunk_ts)
    assert len(mode_rows()) == 5, "INSERT OR REPLACE idempotence: no dup rows"

    # Superseded generation: the stale member's bars and end marker are
    # rejected — no save, no set, no wave completion, ids untouched.
    sess._history_generation += 1
    n_pending = len(sess._pending_bars)
    sess.on_historical_bar(r3, _FakeIbBar(base + 9999, price=102.0))
    sess.on_historical_data_end(r3)
    sess.on_historical_bar(999_999, _FakeIbBar(base + 8888, price=103.0))
    assert save_lengths == [5, 5]
    assert len(set_calls) == 2
    assert len(sess._pending_bars) == n_pending
    assert r3 in sess._history_req_ids, "stale end cannot drain the wave"
    assert host.wave_complete_calls == [], "superseded wave cannot finalise"
    assert base + 9999 not in {b.ts for b in mode_rows()}

    # The wave record still holds every accepted fetched bar.
    assert len(sess._pending_bars) == 10
