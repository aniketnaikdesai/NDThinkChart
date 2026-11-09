"""P19-T1 — settled-viewport prefetch trigger evaluation (D58.1), offscreen.

Proves the fire/silent decision only (P19-2 owns issuance; no wave is issued
by any code path exercised here):

* T01 — per-timeframe viewport matrix (all nine timeframes, intraday in both
  RTH and ETH modes): within-T fires, beyond-T stays silent, with the
  single-sided boundary cell (within side fires, beyond side silent). Seeded
  series with clock control (``win._now_ts``) and stubbed cache reads
  (``BarCache.get_bars``). Every fire cell seeds the fetchable next-older
  step the trigger exists to fetch; the complete-cache leg pins the other
  half of the consult — within-T with nothing fetchable stays silent (no
  wave to nowhere), which also keeps a weekend-closure-only gap silent.
* T02 — live ticks never evaluate; a following-at-edge report over a full
  buffer is silent by distance; per-view reports (main vs pop-out) evaluate
  independently against the shared mode-aware cache; a weekend-only (or
  holiday-only) closure gap stays silent while a real missing session fires.

Design notes locked by these tests:

* The trigger table is the S-P18-3 span table reused as lookahead
  (``FRESH_FRAME_INTRADAY_SESSIONS`` / ``FRESH_FRAME_DAILY_SPAN_DAYS``);
  no timeframes, counts or spans are restated here.
* Intraday fire cells seed a planner-visible hole strictly inside the
  cached span (the planner only reports [first-cached, now]): ``1 min``
  (the only N=2 timeframe, whose oldest day sits inside the trailing
  bar-granularity window) omits the first two bars of the oldest day (a
  leading gap > 1.5 bar periods); every other intraday timeframe omits a
  whole middle day instead (``4 hours``/RTH has two bars per day, so no
  partial-day hole is planner-visible there).
* Weekly/monthly buckets (Monday-00:00 / month-boundary-00:00 ET) lie
  outside every session window, so the day-granular planner always reports
  spans there by construction. The matrix therefore proves fire-within /
  silence-beyond for those timeframes, while the complete-cache leg is
  intraday+daily only (stated, not silently skipped).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import (
    TIMEFRAME_SECONDS,
    month_bucket_start,
    week_bucket_start,
)
from data.bar_cache import BarCache
from data.models import Bar
from services.market_calendar import is_trading_day
from ui.lwc_view import (
    FRESH_FRAME_DAILY_SPAN_DAYS,
    FRESH_FRAME_INTRADAY_SESSIONS,
    LwcChartView,
    series_times,
)

EASTERN = ZoneInfo("America/New_York")
SYMBOL = "P19T"

INTRADAY_TFS = ["1 min", "5 mins", "15 mins", "30 mins", "1 hour", "4 hours"]

# Weekend-closure fixtures (all trading days verified in-test).
_FRIDAY = date(2026, 9, 25)   # Friday
_MONDAY = date(2026, 9, 28)   # Monday
_THURSDAY = date(2026, 9, 24)  # Thursday
# US-equity holiday closure: Fri 2026-07-03 is the observed Independence Day.
_HOL_THU = date(2026, 7, 2)   # Thursday (trading)
_HOL_MON = date(2026, 7, 6)   # Monday (trading)


# ---------------------------------------------------------------------------
# Small calendar / bar helpers (independent of the trigger under test)
# ---------------------------------------------------------------------------
def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts: int) -> date:
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _prev_trading_day(d: date) -> date:
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _trading_days_back(end: date, n: int) -> list[date]:
    """``n`` trading days ending on ``end`` (inclusive), ascending."""
    assert is_trading_day(end), f"anchor {end} is not a trading day"
    days = [end]
    while len(days) < n:
        days.append(_prev_trading_day(days[-1]))
    return sorted(days)


def _bar(symbol: str, tf: str, ts: int, base: float = 100.0) -> Bar:
    return Bar(symbol, tf, ts, base, base + 0.5, base - 0.5, base, 1000.0)


def _session_grid(tf: str, ext_hours: bool) -> tuple[tuple[int, int],
                                                     tuple[int, int], int]:
    period = TIMEFRAME_SECONDS[tf]
    if ext_hours:
        return (4, 0), (20, 0), period
    return (9, 30), (16, 0), period


def _intraday_bars(symbol: str, tf: str, day: date,
                   ext_hours: bool) -> list[Bar]:
    (oh, om), (ch, cm), period = _session_grid(tf, ext_hours)
    start = _et_ts(day.year, day.month, day.day, oh, om)
    close = _et_ts(day.year, day.month, day.day, ch, cm)
    bars: list[Bar] = []
    ts = start
    i = 0
    while ts < close:
        bars.append(_bar(symbol, tf, ts, 100.0 + (i % 5) * 0.25))
        ts += period
        i += 1
    assert bars, f"no bars for {tf} on {day} (ext={ext_hours})"
    return bars


def _daily_bars(symbol: str, days: list[date]) -> list[Bar]:
    return [_bar(symbol, "1 day",
                 _et_ts(d.year, d.month, d.day, 16, 0), 100.0)
            for d in days]


def _bucket_bars(symbol: str, tf: str, days: list[date],
                 count: int) -> list[Bar]:
    """Coarse bucket bars (weekly/monthly), newest-first capped at ``count``."""
    assert tf in ("1 week", "1 month")
    fn = week_bucket_start if tf == "1 week" else month_bucket_start
    seen: dict[int, Bar] = {}
    for d in days:
        probe = _et_ts(d.year, d.month, d.day, 12, 0)
        bucket = fn(probe)
        if bucket not in seen:
            step = (bucket // 604800) % 5
            price = 100.0 + step * 0.25
            seen[bucket] = Bar(symbol, tf, bucket, price, price + 0.5,
                               price - 0.5, price, 1000.0 + (bucket % 500))
    ordered = sorted(seen)
    assert len(ordered) >= count, f"only {len(ordered)} buckets for {tf}"
    return [seen[ts] for ts in ordered[-count:]]


# ---------------------------------------------------------------------------
# View / window / stub helpers
# ---------------------------------------------------------------------------
def _make_view(qapp, tf: str, ext_hours: bool, bars: list[Bar]) -> LwcChartView:
    view = LwcChartView(tz_offset=0.0)
    view.set_timeframe(tf)
    view.set_extended_hours(ext_hours)
    view.update_bars(list(bars))
    return view


def _ordinal_for_ts(view: LwcChartView, tf: str, ext_hours: bool,
                    target_ts: int) -> float:
    """Page ordinal of a plotted bar (first non-whitespace entry at its ts)."""
    period = TIMEFRAME_SECONDS[tf]
    times, whitespace = series_times(view.plotted_bars, view.logical_index,
                                     period, ext_hours)
    for i, (t, ws) in enumerate(zip(times, whitespace)):
        if int(t) == int(target_ts) and not ws:
            return float(i)
    raise AssertionError(f"ts {target_ts} not plotted for {tf}")


def _visible_ts(view: LwcChartView, slot: float) -> int:
    """Report a settled viewport at ``slot`` and read back the oldest ts."""
    assert view.report_viewport({"from": float(slot),
                                 "to": float(slot) + 10.0}, False) is True
    ts = view.oldest_visible_ts()
    assert ts is not None
    return int(ts)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def _triple(win, tf: str, ext_hours: bool, now_ts: int) -> None:
    win._current_symbol = SYMBOL
    win._current_tf = tf
    win.ext_hours_btn.setChecked(ext_hours)
    win._now_ts = lambda: now_ts


class _CacheStub:
    """Stubbed mode-aware cache read that records the requested mode."""

    def __init__(self, bars: list[Bar]):
        self.bars = list(bars)
        self.requested: list[bool] = []

    def __call__(self, symbol, timeframe, ext_hours=True):
        self.requested.append(bool(ext_hours))
        assert symbol == SYMBOL
        assert timeframe == self.timeframe
        return list(self.bars)


def _stub_cache(monkeypatch, tf: str, bars: list[Bar]) -> _CacheStub:
    stub = _CacheStub(bars)
    stub.timeframe = tf
    monkeypatch.setattr(BarCache, "get_bars",
                        staticmethod(stub.__call__))
    return stub


# ---------------------------------------------------------------------------
# T01 — intraday trigger matrix (six timeframes × RTH/ETH)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("tf", INTRADAY_TFS)
@pytest.mark.parametrize("ext_hours", [True, False], ids=["ETH", "RTH"])
def test_t01_trigger_matrix_intraday(monkeypatch, qapp, tf, ext_hours):
    """T01: within-T fires, beyond-T silent, boundary single-sided, all tfs."""
    sessions = FRESH_FRAME_INTRADAY_SESSIONS[tf]
    end = date(2026, 9, 30)
    days = _trading_days_back(end, sessions + 2)  # P+1 .. P+N+2

    def seed(hole: bool) -> tuple[list[Bar], list[date]]:
        bars: list[Bar] = []
        for i, d in enumerate(days):
            day_bars = _intraday_bars(SYMBOL, tf, d, ext_hours)
            if hole and sessions == 2 and i == 0:
                # N=2 only ("1 min"): the oldest day is inside the
                # trailing bar-granularity window, so a leading gap there
                # is planner-visible.
                day_bars = day_bars[2:]  # leading gap > 1.5 bar periods
                assert day_bars, f"{tf} oldest day too short"
            elif hole and sessions > 2 and i == 1:
                day_bars = []  # whole missing day, strictly inside
            bars.extend(day_bars)
        return bars, days

    fire_bars, _ = seed(hole=True)
    by_day: dict[date, list[Bar]] = {}
    for b in fire_bars:
        by_day.setdefault(_et_date(b.ts), []).append(b)
    oldest = days[0]
    (oh, om), _, period = _session_grid(tf, ext_hours)
    if sessions == 2:
        expect_c = _et_ts(oldest.year, oldest.month, oldest.day,
                           oh, om) + 2 * period
        assert by_day[oldest][0].ts == expect_c  # leading-gap shape pinned
        v_within = by_day[oldest][0].ts
    else:
        assert by_day[oldest][0].ts == _et_ts(
            oldest.year, oldest.month, oldest.day, oh, om)
        assert days[1] not in by_day  # the missing middle day
        v_within = by_day[days[2]][0].ts
    oldest_cached = by_day[oldest][0].ts
    v_boundary_fire = by_day[days[sessions - 1]][0].ts
    v_boundary_beyond = by_day[days[sessions]][0].ts
    v_beyond = by_day[days[sessions + 1]][0].ts
    now_ts = _et_ts(end.year, end.month, end.day, 20, 0)

    cache = _stub_cache(monkeypatch, tf, fire_bars)
    view = _make_view(qapp, tf, ext_hours, fire_bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, tf, ext_hours, now_ts)
        assert min(b.ts for b in fire_bars) == oldest_cached
        # Within-T fires (oldest edge, then the boundary within side).
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, ext_hours,
                                              v_within)), False) is True
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, ext_hours,
                                              v_boundary_fire)), False) is True
        # Boundary beyond side + deep beyond stay silent (single-sided).
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, ext_hours,
                                              v_boundary_beyond)),
            False) is False
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, ext_hours,
                                              v_beyond)), False) is False
        # The read is mode-aware: the requested mode matches the triple.
        assert cache.requested and all(r == ext_hours
                                       for r in cache.requested)

        # Complete cache, within-T: nothing fetchable → silence (no wave to
        # nowhere). The planner consult is load-bearing here.
        complete_bars, _ = seed(hole=False)
        cache.bars = complete_bars
        view2 = _make_view(qapp, tf, ext_hours, complete_bars)
        v_early = complete_bars[0].ts
        assert win.maybe_prefetch(
            _visible_ts(view2, _ordinal_for_ts(view2, tf, ext_hours,
                                               v_early)), False) is False
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T01 — daily / weekly / monthly matrix
# ---------------------------------------------------------------------------
def test_t01_trigger_matrix_daily(monkeypatch, qapp):
    """T01 (1 day): fire/silence/boundary incl. the exact single-sided cell."""
    end = date(2026, 9, 30)
    days = _trading_days_back(end, 380)
    hole = set(days[10:13])  # strictly inside: the planner sees [first, now]
    seeded = [d for d in days if d not in hole]
    fire_bars = _daily_bars(SYMBOL, seeded)
    by_ts = {b.ts: b for b in fire_bars}
    oldest_cached = min(by_ts)
    assert _et_date(oldest_cached) == days[0]
    now_ts = _et_ts(end.year, end.month, end.day, 20, 0)

    def bar_on_or_after(ts: int) -> int:
        return min(t for t in by_ts if t >= ts)

    v_within = bar_on_or_after(max(t for t in by_ts
                                   if _et_date(t) == days[13]))
    # Exact single-sided boundary: ±1 trading day around C + 365 days.
    exact = oldest_cached + 365 * 86400
    below = max(t for t in by_ts if t <= exact)
    above = min(t for t in by_ts if t > exact)
    assert above - below <= 4 * 86400  # adjacent cells across the threshold
    v_beyond = bar_on_or_after(oldest_cached + 370 * 86400)

    cache = _stub_cache(monkeypatch, "1 day", fire_bars)
    view = _make_view(qapp, "1 day", True, fire_bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, "1 day", True, now_ts)
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, "1 day", True,
                                              v_within)), False) is True
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, "1 day", True,
                                              below)), False) is True
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, "1 day", True,
                                              above)), False) is False
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, "1 day", True,
                                              v_beyond)), False) is False
        # Daily+ reads the canonical (ETH) cache even with RTH selected.
        win.ext_hours_btn.setChecked(False)
        assert win.maybe_prefetch(v_within, False) is True
        assert cache.requested and all(cache.requested)

        complete_bars = _daily_bars(SYMBOL, days)
        cache.bars = complete_bars
        win.ext_hours_btn.setChecked(True)
        view2 = _make_view(qapp, "1 day", True, complete_bars)
        assert win.maybe_prefetch(
            _visible_ts(view2, _ordinal_for_ts(view2, "1 day", True,
                                               complete_bars[0].ts)),
            False) is False
    finally:
        win.close()


@pytest.mark.parametrize("tf", ["1 week", "1 month"])
def test_t01_trigger_matrix_coarse(monkeypatch, qapp, tf):
    """T01 (weekly/monthly): fire within the calendar span, silent beyond."""
    span_days = FRESH_FRAME_DAILY_SPAN_DAYS[tf]
    end = date(2026, 9, 30)
    days = _trading_days_back(end, 2600 if tf == "1 month" else 560)
    count = 80
    bars = _bucket_bars(SYMBOL, tf, days, count)
    by_ts = sorted(b.ts for b in bars)
    oldest_cached = by_ts[0]
    now_ts = _et_ts(end.year, end.month, end.day, 20, 0)

    v_within = by_ts[2]
    margin = 7 * 86400 if tf == "1 week" else 31 * 86400
    below = max(t for t in by_ts if t <= oldest_cached + span_days * 86400)
    above = min(t for t in by_ts if t > oldest_cached + span_days * 86400)
    assert (oldest_cached + span_days * 86400) - below <= 2 * margin
    assert above - (oldest_cached + span_days * 86400) <= 2 * margin
    v_beyond = min(t for t in by_ts
                   if t >= oldest_cached + (span_days + 7) * 86400)

    _stub_cache(monkeypatch, tf, bars)
    view = _make_view(qapp, tf, True, bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, tf, True, now_ts)
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, True,
                                              v_within)), False) is True
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, True,
                                              below)), False) is True
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, True,
                                              above)), False) is False
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, True,
                                              v_beyond)), False) is False
    finally:
        win.close()


# ---------------------------------------------------------------------------
# T02 — gating, per-view independence, closures
# ---------------------------------------------------------------------------
def test_t02_no_evaluation_on_live_path(monkeypatch, qapp):
    """T02: live ticks and live-bar updates never run the trigger."""
    now_ts = _et_ts(2026, 9, 30, 20, 0)
    day = date(2026, 9, 30)
    bars = _intraday_bars(SYMBOL, "5 mins", day, True)
    view = _make_view(qapp, "5 mins", True, bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, "5 mins", True, now_ts)
        calls: list = []
        monkeypatch.setattr(
            win, "maybe_prefetch",
            lambda *a, **k: calls.append((a, k)) or False)
        emitted: list = []
        view.viewport_settled.connect(lambda ts, fol: emitted.append((ts, fol)))

        session = win.get_or_create_session(SYMBOL)
        monkeypatch.setattr(session, "on_realtime_bar",
                            lambda *a, **k: None)
        win._register_req_id(4242, session)
        win._on_realtime_bar(4242, now_ts, 100.0, 101.0, 99.0, 100.5,
                             1000.0, 100.2, 10)
        win._on_realtime_bar(999999, now_ts, 100.0, 101.0, 99.0, 100.5,
                             1000.0, 100.2, 10)  # unknown reqId: ignored
        live = _bar(SYMBOL, "5 mins", now_ts, 101.0)
        view.update_last_bar(live, True)
        view.update_last_bar(live, False)

        assert calls == []
        assert emitted == []
    finally:
        win.close()


def test_t02_following_at_edge_full_buffer_is_silent(monkeypatch, qapp):
    """T02: following-at-edge over a full buffer is beyond T → silence."""
    end = date(2026, 9, 30)
    days = _trading_days_back(end, 30)
    bars = [b for d in days for b in _intraday_bars(SYMBOL, "5 mins", d, True)]
    now_ts = _et_ts(end.year, end.month, end.day, 20, 0)
    _stub_cache(monkeypatch, "5 mins", bars)
    view = _make_view(qapp, "5 mins", True, bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, "5 mins", True, now_ts)
        newest = max(b.ts for b in bars)
        slot = _ordinal_for_ts(view, "5 mins", True, newest)
        assert view.report_viewport({"from": slot, "to": slot + 10.0},
                                    True) is True
        ts = view.oldest_visible_ts()
        assert ts == newest
        assert win.maybe_prefetch(ts, True) is False
    finally:
        win.close()


def test_t02_per_view_reports_evaluate_independently(monkeypatch, qapp):
    """T02: main vs pop-out viewports decide per view, one shared cache."""
    sessions = FRESH_FRAME_INTRADAY_SESSIONS["5 mins"]
    end = date(2026, 9, 30)
    days = _trading_days_back(end, sessions + 2)
    bars: list[Bar] = []
    for i, d in enumerate(days):
        day_bars = _intraday_bars(SYMBOL, "5 mins", d, True)
        if i == 0:
            day_bars = day_bars[2:]
        bars.extend(day_bars)
    by_day: dict[date, list[Bar]] = {}
    for b in bars:
        by_day.setdefault(_et_date(b.ts), []).append(b)
    now_ts = _et_ts(end.year, end.month, end.day, 20, 0)
    _stub_cache(monkeypatch, "5 mins", bars)
    main_view = _make_view(qapp, "5 mins", True, bars)
    popout_view = _make_view(qapp, "5 mins", True, bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, "5 mins", True, now_ts)
        near = _visible_ts(main_view,
                           _ordinal_for_ts(main_view, "5 mins", True,
                                           by_day[days[0]][0].ts))
        far_ts = by_day[days[-1]][0].ts
        far = _visible_ts(popout_view,
                          _ordinal_for_ts(popout_view, "5 mins", True, far_ts))
        assert near != far
        assert win.maybe_prefetch(near, False) is True
        assert win.maybe_prefetch(far, False) is False
    finally:
        win.close()


@pytest.mark.parametrize("ext_hours", [True, False], ids=["ETH", "RTH"])
@pytest.mark.parametrize("tf", ["5 mins", "1 day"])
def test_t02_weekend_closure_gap_is_silent(monkeypatch, qapp, tf, ext_hours):
    """T02: a gap spanning only a weekend closure produces silence."""
    for d in (_FRIDAY, _MONDAY, _THURSDAY):
        assert is_trading_day(d), d
    if tf == "1 day":
        cache_bars = _daily_bars(SYMBOL, [_FRIDAY, _MONDAY])
        v_ts = _et_ts(_MONDAY.year, _MONDAY.month, _MONDAY.day, 16, 0)
    else:
        cache_bars = (_intraday_bars(SYMBOL, tf, _FRIDAY, ext_hours)
                      + _intraday_bars(SYMBOL, tf, _MONDAY, ext_hours))
        v_ts = _intraday_bars(SYMBOL, tf, _MONDAY, ext_hours)[2].ts
    view_bars = list(cache_bars)
    now_ts = _et_ts(_MONDAY.year, _MONDAY.month, _MONDAY.day, 20, 0)
    _stub_cache(monkeypatch, tf, cache_bars)
    view = _make_view(qapp, tf, ext_hours, view_bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, tf, ext_hours, now_ts)
        assert _visible_ts(view, _ordinal_for_ts(view, tf, ext_hours,
                                                 v_ts)) == v_ts
        assert win.maybe_prefetch(v_ts, False) is False
    finally:
        win.close()


def test_t02_holiday_closure_gap_is_silent(monkeypatch, qapp):
    """T02: a gap spanning only the observed-Independence-Day closure is silent."""
    assert is_trading_day(_HOL_THU) and is_trading_day(_HOL_MON)
    assert not is_trading_day(date(2026, 7, 3))  # observed holiday Friday
    tf = "5 mins"
    cache_bars = (_intraday_bars(SYMBOL, tf, _HOL_THU, True)
                  + _intraday_bars(SYMBOL, tf, _HOL_MON, True))
    now_ts = _et_ts(_HOL_MON.year, _HOL_MON.month, _HOL_MON.day, 20, 0)
    _stub_cache(monkeypatch, tf, cache_bars)
    view = _make_view(qapp, tf, True, cache_bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, tf, True, now_ts)
        v_ts = _intraday_bars(SYMBOL, tf, _HOL_MON, True)[2].ts
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, True, v_ts)),
            False) is False
    finally:
        win.close()


def test_t02_real_missing_session_fires(monkeypatch, qapp):
    """T02 control: the same Monday edge fires when Friday is really missing."""
    tf = "5 mins"
    cache_bars = (_intraday_bars(SYMBOL, tf, _THURSDAY, True)
                  + _intraday_bars(SYMBOL, tf, _MONDAY, True))
    now_ts = _et_ts(_MONDAY.year, _MONDAY.month, _MONDAY.day, 20, 0)
    _stub_cache(monkeypatch, tf, cache_bars)
    view = _make_view(qapp, tf, True, cache_bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, tf, True, now_ts)
        v_ts = _intraday_bars(SYMBOL, tf, _MONDAY, True)[2].ts
        assert win.maybe_prefetch(
            _visible_ts(view, _ordinal_for_ts(view, tf, True, v_ts)),
            False) is True
    finally:
        win.close()


def test_t02_guardrails(monkeypatch, qapp):
    """T02: unusable readings, empty cache, unknown triple → silence."""
    now_ts = _et_ts(2026, 9, 30, 20, 0)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, "5 mins", True, now_ts)
        assert win.maybe_prefetch(None) is False
        assert win.maybe_prefetch("not-a-ts") is False
        _stub_cache(monkeypatch, "5 mins", [])
        assert win.maybe_prefetch(now_ts - 3600) is False
        win._current_tf = "9 parsecs"
        assert win.maybe_prefetch(now_ts - 3600) is False
        win._current_tf = "5 mins"
        win._current_symbol = ""
        assert win.maybe_prefetch(now_ts - 3600) is False
    finally:
        win.close()


def test_t02_oldest_visible_mapping_edges(qapp):
    """T02: slot→ts mapping — holes, clamps, and the no-report case."""
    tf = "5 mins"
    day_a = date(2026, 9, 29)
    day_b = date(2026, 9, 30)
    bars_a = _intraday_bars(SYMBOL, tf, day_a, True)
    # An internal hole: the mapping must skip whitespace placeholders.
    hole_ts = {b.ts for b in bars_a[10:14]}
    bars = [b for b in bars_a if b.ts not in hole_ts] + _intraday_bars(
        SYMBOL, tf, day_b, True)
    view = _make_view(qapp, tf, True, bars)
    period = TIMEFRAME_SECONDS[tf]
    times, whitespace = series_times(view.plotted_bars, view.logical_index,
                                     period, True)
    hole_idx = next(i for i, ws in enumerate(whitespace) if ws)
    first_real = next(i for i in range(hole_idx, len(times))
                      if not whitespace[i])
    assert view.report_viewport({"from": float(hole_idx),
                                 "to": float(hole_idx) + 5.0}, False) is True
    assert view.oldest_visible_ts() == int(times[first_real])
    # Over-scrolled past the last bar → the last real bar.
    last_real = max(i for i, ws in enumerate(whitespace) if not ws)
    assert view.report_viewport({"from": float(len(times) + 100),
                                 "to": float(len(times)) + 110.0},
                                False) is True
    assert view.oldest_visible_ts() == int(times[last_real])
    # Over-scrolled before the first bar → the first real bar.
    assert view.report_viewport({"from": -50.0, "to": 10.0}, False) is True
    assert view.oldest_visible_ts() == int(times[0])
    # No settled report stored → no reading.
    fresh = _make_view(qapp, tf, True, bars)
    assert fresh.oldest_visible_ts() is None
    # An unusable report never stores → still no reading.
    assert fresh.report_viewport({"from": "xx", "to": 10.0}, False) is False
    assert fresh.oldest_visible_ts() is None


def test_t02_settled_report_fanout_evaluates(monkeypatch, qapp):
    """T02: a settled main-chart report runs the evaluator (decision only)."""
    sessions = FRESH_FRAME_INTRADAY_SESSIONS["5 mins"]
    end = date(2026, 9, 30)
    days = _trading_days_back(end, sessions + 2)
    bars: list[Bar] = []
    for i, d in enumerate(days):
        day_bars = _intraday_bars(SYMBOL, "5 mins", d, True)
        if i == 0:
            day_bars = day_bars[2:]
        bars.extend(day_bars)
    now_ts = _et_ts(end.year, end.month, end.day, 20, 0)
    _stub_cache(monkeypatch, "5 mins", bars)
    win = _make_window(monkeypatch, qapp)
    try:
        _triple(win, "5 mins", True, now_ts)
        panel = win.chart_panel
        assert hasattr(panel, "viewport_settled")
        panel.set_timeframe("5 mins")
        panel.set_extended_hours(True)
        panel.update_bars(list(bars))
        calls: list = []
        orig = win.maybe_prefetch
        def counting(ts, following=False):
            calls.append((ts, following))
            return orig(ts, following)
        monkeypatch.setattr(win, "maybe_prefetch", counting)
        v_ts = bars[0].ts
        slot = _ordinal_for_ts(panel, "5 mins", True, v_ts)
        panel._on_page_viewport_report(
            {"range": {"from": slot, "to": slot + 5.0}, "following": False})
        assert calls == [(v_ts, False)]
        assert win._last_prefetch_decision == {
            "oldest_visible_ts": v_ts,
            "following": False,
            "fire": True,
        }
    finally:
        win.close()
