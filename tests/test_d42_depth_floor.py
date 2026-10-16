"""P2-T22 / D42 — the per-timeframe, per-mode intraday depth floor (AC-D16.8).

Drives the **real** ``MainWindow`` load path with a stubbed historical feed and
asserts the resulting series spans >= ``MIN_INTRADAY_SESSIONS`` (30) distinct
**mode-valid** sessions *before the current one*, for each of the five intraday
timeframes in **both** modes — and that the derived :func:`floor_bar_budget`
(not the flat ``RETENTION_BARS``/``SESSION_BAR_CAP``) actually retains it through
the wave's prune and the in-memory cap.

Measurables (task P2-T22):

    P2-T22-T11 (AC1) — the depth floor for each intraday timeframe x mode.
    P2-T22-T21 (AC2) — the floor survives retention (cached + in-memory).
    P2-T22-T31 (AC3) — both modes exercised; mode-validity respected (AC-D16.9).

RED pre-fix: ``1 min`` RTH yielded a single session — the ESC-038 repro.

The harness (``_seed``/``_FakeIbBar``/``_ReqStub``/``_make_window``/``_load``)
is modelled on ``tests/test_history_backfill_loadpath.py``. A session counts as
present only when it holds a bar inside the current mode's session window, so
presence is measured with :func:`services.backfill_service.present_days`, never
by calendar day.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from PyQt6.QtWidgets import QDockWidget

from config import settings
from data.bar_cache import RETENTION_BARS, BarCache
from data.models import Bar
from services.backfill_service import floor_bar_budget, present_days
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")

#: The five intraday timeframes the AC-D16.8 floor covers ("1 day" is excluded).
INTRADAY_TIMEFRAMES = ["1 min", "5 mins", "15 mins", "1 hour", "4 hours"]

#: A fixed "now": Friday 2026-11-06 20:00 ET (a trading day, after the close).
NOW = int(datetime(2026, 11, 6, 20, 0, tzinfo=EASTERN).timestamp())


# ---------------------------------------------------------------------------
# Deterministic calendar / timestamp helpers
# ---------------------------------------------------------------------------
def _et_ts(y: int, m: int, d: int, h: int = 12, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _trading_days_back(now_day: date, count: int) -> list[date]:
    """The ``count`` trading days ending at ``now_day`` (inclusive), ascending.

    ``now_day`` is a trading day here, so ``days[-1] == now_day`` and
    ``days[0]`` is ``count - 1`` trading days earlier.
    """
    days: list[date] = []
    day = now_day
    while len(days) < count:
        if is_trading_day(day):
            days.append(day)
        day -= timedelta(days=1)
    return list(reversed(days))


def _noon_ts(day: date) -> int:
    """A timestamp inside *both* mode windows (09:30-16:00 and 04:00-20:00 ET)."""
    return _et_ts(day.year, day.month, day.day, 12, 0)


def _rth_day_ts(day: date) -> list[int]:
    """One complete RTH day of 1-min bars: 09:30-15:59 ET (390 bars)."""
    stamps: list[int] = []
    for hour in range(9, 16):
        start_minute = 30 if hour == 9 else 0
        for minute in range(start_minute, 60):
            stamps.append(_et_ts(day.year, day.month, day.day, hour, minute))
    return stamps


def _before_current(present: set[date], current: date) -> set[date]:
    """The present sessions strictly before the current one."""
    return {day for day in present if day < current}


def _symbol_for(tf: str, mode: bool) -> str:
    # Uppercased: ``load_chart`` upper-cases the symbol, so the cache key the
    # test reads must match the one the load path wrote.
    tag = "".join(ch for ch in tf if ch.isalnum())
    return f"P22{tag}{'E' if mode else 'R'}".upper()


# ---------------------------------------------------------------------------
# Load-path harness (modelled on tests/test_history_backfill_loadpath.py)
# ---------------------------------------------------------------------------
def _clear(symbol: str, timeframe: str) -> None:
    from data.db import db

    db.conn.execute(
        "DELETE FROM bars WHERE symbol=? AND timeframe=?", (symbol, timeframe)
    )
    db.conn.commit()


class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0):
        self.date = str(int(ts))  # parse_ibkr_date accepts a 10-digit epoch string
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = 1000


class _ReqStub:
    """Unbounded ``req_historical_data`` double (the floor span issues MANY).

    Ids are drawn from an unbounded counter — never a fixed-list ``iter([...])``,
    which the multi-request floor span would exhaust (``StopIteration``).
    """

    def __init__(self, first_id: int = 1000):
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
    """Build a shown MainWindow that never touches TWS."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    right_docks = [
        dock for dock in win.findChildren(QDockWidget)
        if dock.windowTitle() in ("Portfolio",)
    ]
    assert right_docks, "expected the 'Portfolio' right dock to exist"
    for dock in right_docks:
        dock.hide()
    qapp.processEvents()
    return win


def _set_mode(win, mode: bool) -> None:
    """Set the load's ext-hours toggle without firing its change slot."""
    win.ext_hours_btn.blockSignals(True)
    win.ext_hours_btn.setChecked(mode)
    win.ext_hours_btn.blockSignals(False)


def _drive_floor_wave(win, symbol: str, tf: str, mode: bool,
                      timestamps: list[int]) -> list[int]:
    """Load with an empty cache, feed the floor's bars, finalize the wave.

    The empty cache makes the planner emit exactly one **backwards floor span**
    (S17), which the window chunks into requests. Each ``timestamps`` entry is
    fed as one stubbed historical bar on the first member, then every member is
    ended so the wave finalizes (persist + prune + re-read + render).
    """
    _set_mode(win, mode)
    _clear(symbol, tf)
    stub = _ReqStub()
    win._now_ts = lambda: NOW
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(tf)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()

    req_ids = [c["reqId"] for c in stub.calls]
    assert req_ids, "the empty-cache depth floor must issue at least one request"
    anchor = req_ids[0]
    for ts in timestamps:
        win._on_historical_bar(anchor, _FakeIbBar(ts))
    for rid in req_ids:
        win._on_historical_data_end(rid)
    assert win._history_req_ids == set(), "the wave must finalize"
    return req_ids


# ---------------------------------------------------------------------------
# P2-T22-T11 (AC1) — the depth floor for each intraday timeframe x mode
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", [False, True], ids=["rth", "eth"])
@pytest.mark.parametrize("tf", INTRADAY_TIMEFRAMES)
def test_p2_t22_t11_depth_floor_all_intraday_timeframes_both_modes(
    monkeypatch, qapp, tf, mode
):
    """P2-T22-T11 (AC1): >= 30 mode-valid sessions before the current one.

    Drives the load path with the stub for each intraday timeframe x mode. RED
    pre-fix for ``1 min`` RTH (one session — the ESC-038 repro).
    """
    win = _make_window(monkeypatch, qapp)
    symbol = _symbol_for(tf, mode)
    current = _et_date(NOW)
    # 40 trading days ending at the current session: 39 sessions *before* it,
    # comfortably above the 30 floor.
    timestamps = [_noon_ts(day) for day in _trading_days_back(current, 40)]
    try:
        _drive_floor_wave(win, symbol, tf, mode, timestamps)

        cached = BarCache.get_bars(symbol, tf, ext_hours=mode)
        cached_before = _before_current(
            present_days([b.ts for b in cached], ext_hours=mode), current
        )
        assert len(cached_before) >= settings.MIN_INTRADAY_SESSIONS, (
            f"{tf} mode={'ETH' if mode else 'RTH'}: cached series spans only "
            f"{len(cached_before)} mode-valid sessions before the current one"
        )

        session = win.get_or_create_session(symbol)
        mem_before = _before_current(
            present_days([b.ts for b in session.get_bars(tf)], ext_hours=mode),
            current,
        )
        assert len(mem_before) >= settings.MIN_INTRADAY_SESSIONS, (
            f"{tf} mode={'ETH' if mode else 'RTH'}: in-memory series spans only "
            f"{len(mem_before)} mode-valid sessions before the current one"
        )
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P2-T22-T21 (AC2) — the floor survives retention (the derived budget)
# ---------------------------------------------------------------------------
def test_p2_t22_t21_floor_survives_retention(monkeypatch, qapp):
    """P2-T22-T21 (AC2): after the wave, cached + in-memory still hold >= 30.

    ``1 min`` RTH is the decisive case: the flat ``RETENTION_BARS`` (5000) is
    ~12 sessions, so a flat ``keep`` would trim the floor away. Feeding complete
    RTH days whose total exceeds 5000 but stays under the derived
    ``floor_bar_budget`` proves the derived budget — not the flat 5000 — is the
    retention the load path applies.
    """
    win = _make_window(monkeypatch, qapp)
    tf, mode, symbol = "1 min", False, "P22RET"
    current = _et_date(NOW)
    days = _trading_days_back(current, 34)  # 33 sessions before the current one
    timestamps: list[int] = []
    for day in days:
        timestamps.extend(_rth_day_ts(day))
    try:
        # Render seam: the retention invariant is on the series, not the pixels.
        win.chart_panel.update_chart = lambda bars: None
        _drive_floor_wave(win, symbol, tf, mode, timestamps)

        budget = floor_bar_budget(tf, mode)
        assert budget > RETENTION_BARS, (
            "the derived budget must exceed the flat retention for the floor to "
            "be meaningful"
        )
        assert len(timestamps) > RETENTION_BARS  # a flat keep would have pruned

        cached = BarCache.get_bars(symbol, tf, ext_hours=mode)
        # The derived keep retains every fed bar; a flat keep=5000 would leave 5000.
        assert len(cached) == len(timestamps)
        cached_before = _before_current(
            present_days([b.ts for b in cached], ext_hours=mode), current
        )
        assert len(cached_before) >= settings.MIN_INTRADAY_SESSIONS

        session = win.get_or_create_session(symbol)
        mem = session.get_bars(tf)
        assert len(mem) == len(timestamps)
        mem_before = _before_current(
            present_days([b.ts for b in mem], ext_hours=mode), current
        )
        assert len(mem_before) >= settings.MIN_INTRADAY_SESSIONS
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P2-T22-T31 (AC3) — both modes exercised; mode-validity respected
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("mode", [False, True], ids=["rth", "eth"])
def test_p2_t22_t31_both_modes_covered_and_mode_valid(monkeypatch, qapp, mode):
    """P2-T22-T31 (AC3): the floor assertion holds in RTH and in ETH.

    Both modes are exercised, and mode isolation holds: the wave's rows are
    scoped to the load's mode (the other mode's cache key stays empty,
    AC-D16.9), and a pre-market-only day (05:00 ET) counts as present under ETH
    but never under RTH.
    """
    win = _make_window(monkeypatch, qapp)
    tf = "5 mins"
    symbol = "P22BOTH" + ("E" if mode else "R")
    current = _et_date(NOW)
    days = _trading_days_back(current, 40)
    timestamps = [_noon_ts(day) for day in days]
    try:
        _drive_floor_wave(win, symbol, tf, mode, timestamps)

        cached = BarCache.get_bars(symbol, tf, ext_hours=mode)
        before = _before_current(
            present_days([b.ts for b in cached], ext_hours=mode), current
        )
        assert len(before) >= settings.MIN_INTRADAY_SESSIONS

        # AC-D16.9 mode isolation: the other mode's cache key is untouched.
        assert BarCache.get_bars(symbol, tf, ext_hours=not mode) == []

        # Mode-validity: a pre-market-only day is present under ETH, not RTH.
        premarket_day = days[0]
        premarket_ts = _et_ts(
            premarket_day.year, premarket_day.month, premarket_day.day, 5, 0
        )
        assert premarket_day in present_days([premarket_ts], ext_hours=True)
        assert premarket_day not in present_days([premarket_ts], ext_hours=False)
    finally:
        win.close()


# ---------------------------------------------------------------------------
# P2-T25-T11 (AC1) — the session mode is set before the initial set_bars
# P2-T25-T21 (AC2) — the no-wave ETH path retains the ETH budget
# ---------------------------------------------------------------------------
#: Dense intraday timeframes whose RTH and ETH budgets differ (bar period <
#: ~397s), so a stale/default RTH mode is observable as a shorter series.
DENSE_TIMEFRAMES = ["1 min", "5 mins"]

#: Enough trading days that a dense series both satisfies the 30-session floor
#: (so NO wave is issued) and exceeds the ETH budget (so the cap is the limit).
_DENSE_DAYS = 36


def _dense_day_ts(day: date, mode: bool, period_min: int) -> list[int]:
    """One dense session day of ``period_min``-minute bars, mode-scoped.

    ETH: 04:00-20:00 ET; RTH: 09:30-16:00 ET. Bars are period **starts**, so the
    last bar of a dense day sits one period before the session end.
    """
    start_hour, end_hour = (4, 20) if mode else (9, 16)
    stamps: list[int] = []
    for hour in range(start_hour, end_hour):
        first_minute = 30 if (not mode and hour == start_hour) else 0
        for minute in range(first_minute, 60, period_min):
            stamps.append(_et_ts(day.year, day.month, day.day, hour, minute))
    return stamps


def _seed_dense_cache(symbol: str, tf: str, mode: bool, period_min: int,
                      days: int = _DENSE_DAYS) -> list[int]:
    """Seed a dense, floor-satisfying cache for ``symbol``/``tf`` in one mode.

    Dense over every trading day ending at the current session, so day-presence
    is complete and the trailing bar-level pass finds no hole — i.e. a load in
    this mode issues NO backfill wave. Returns the seeded timestamps.
    """
    _clear(symbol, tf)
    current = _et_date(NOW)
    bars: list[Bar] = []
    for day in _trading_days_back(current, days):
        for ts in _dense_day_ts(day, mode, period_min):
            bars.append(Bar(symbol, tf, ts, 100.0, 100.5, 99.5, 100.0, 1000))
    BarCache.save_bars(bars, ext_hours=mode)
    return [b.ts for b in bars]


def _load_no_wave(win, symbol: str, tf: str, mode: bool) -> None:
    """Load ``symbol``/``tf`` in ``mode`` against a floor-satisfying cache.

    Asserts the load issues NO backfill wave. Only the 5-sec aggregator priming
    (if any) may hit ``req_historical_data``; a wave request carries the
    timeframe's own ``bar_size``.
    """
    _set_mode(win, mode)
    stub = _ReqStub()
    win._now_ts = lambda: NOW
    win.symbol_input.setText(symbol)
    win.tf_combo.setCurrentText(tf)
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win.load_chart()
    wave_calls = [c for c in stub.calls if c.get("bar_size") != "5 secs"]
    assert wave_calls == [], (
        f"the floor-satisfying cache must issue NO wave, got {len(wave_calls)}"
    )
    assert win._history_req_ids == set(), "no backfill wave may be in flight"


def test_p2_t25_t11_mode_set_before_initial_set_bars(monkeypatch, qapp):
    """P2-T25-T11 (AC1): the mode is the load's mode at the initial set_bars.

    RED pre-fix: ``queue_wave_plans`` was the only setter, so a no-wave load
    left ``_wave_extended_hours`` at its RTH default — the ETH load's initial
    ``set_bars`` saw RTH, and a stale mode survived into the next load.
    """
    from ui.ticker_session import TickerSession

    win = _make_window(monkeypatch, qapp)
    tf = "5 mins"
    symbol = "P25MODEE"

    seen: list[bool] = []
    orig_set_bars = TickerSession.set_bars

    def spy(self, timeframe, bars):
        seen.append(bool(self._wave_extended_hours))
        return orig_set_bars(self, timeframe, bars)

    monkeypatch.setattr(TickerSession, "set_bars", spy)
    try:
        # 1) A no-wave ETH load: the mode must already be ETH at set_bars.
        _seed_dense_cache(symbol, tf, True, 5)
        _load_no_wave(win, symbol, tf, True)
        session = win.get_or_create_session(symbol)
        assert seen and seen[0] is True, (
            "the session mode must be the load's extended_hours at the initial "
            "set_bars (a no-wave ETH load must not cap at the RTH budget)"
        )
        assert session._wave_extended_hours is True

        # 2) A subsequent no-wave RTH load must not carry the stale ETH mode.
        seen.clear()
        _seed_dense_cache(symbol, tf, False, 5)
        _load_no_wave(win, symbol, tf, False)
        assert seen and seen[0] is False, (
            "the RTH load must set RTH at the initial set_bars"
        )
        assert session._wave_extended_hours is False, (
            "a stale ETH mode must not survive into the RTH load"
        )
    finally:
        win.close()


@pytest.mark.parametrize("tf", DENSE_TIMEFRAMES)
def test_p2_t25_t21_no_wave_eth_path_retains_eth_budget(monkeypatch, qapp, tf):
    """P2-T25-T21 (AC2): the no-wave ETH path keeps the ETH budget (guard).

    A floor-satisfying ETH cache means NO wave is issued, so the in-memory cap
    is set by the load's mode alone. RED pre-fix: the default RTH mode capped
    the series at the RTH budget (e.g. 5,000 for ``5 mins``) instead of the ETH
    budget (6,624); the RTH/ETH budgets differ for every dense timeframe.
    """
    win = _make_window(monkeypatch, qapp)
    period_min = 1 if tf == "1 min" else 5
    symbol = _symbol_for(tf, True)
    budget = floor_bar_budget(tf, True)
    rth_budget = floor_bar_budget(tf, False)
    assert budget > rth_budget, (
        f"{tf}: the RTH/ETH budgets must differ for the guard to be decisive"
    )
    try:
        seeded = _seed_dense_cache(symbol, tf, True, period_min)
        assert len(seeded) > budget, (
            "the seeded cache must exceed the ETH budget so the cap is the limit"
        )
        _load_no_wave(win, symbol, tf, True)

        session = win.get_or_create_session(symbol)
        mem = session.get_bars(tf)
        assert len(mem) == budget, (
            f"{tf} ETH no-wave: in-memory series is {len(mem)}, expected the ETH "
            f"budget {budget} (the RTH budget {rth_budget} is the pre-fix value)"
        )
    finally:
        win.close()
