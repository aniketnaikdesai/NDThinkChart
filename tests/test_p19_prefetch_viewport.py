"""P19-T4 — prefetch viewport stability in both follow states.

Verifies the joint P19-T2/P19-T3 behaviour with no production edits:

* T02 — prefetch landings never move the viewport: the settled range report
  is identical before and after every landing in both away and following
  states (following extends only via the existing D51 live-update path,
  which is not driven here), no fresh-frame request is raised by any
  arrival, and no ``set_visible_range`` range op crosses the bridge on any
  arrival; every landed ``set_bars`` op carries the S-P11-3 preserve
  directive (``same_symbol=True``).
"""

from __future__ import annotations

from datetime import datetime

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.models import Bar
from ibkr.market_data import TIMEFRAME_CONFIG
from services.market_calendar import is_trading_day
from ui.lwc_view import series_times

EASTERN = ZoneInfo("America/New_York")

TF = "5 mins"


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _et_date(ts):
    from datetime import date  # noqa: F401  (kept local: helpers stay flat)
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _prev_trading_day(d):
    from datetime import timedelta

    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _trading_days_back(end, n: int) -> list:
    assert is_trading_day(end)
    days = [end]
    while len(days) < n:
        days.append(_prev_trading_day(days[-1]))
    return sorted(days)


def _session_bars(symbol: str, day, base: float = 100.0) -> list[Bar]:
    """One complete ETH session (04:00-20:00) of 5-min bars, like the feed."""
    if not is_trading_day(day):
        return []
    period = TIMEFRAME_SECONDS[TF]
    start = _et_ts(day.year, day.month, day.day, 4, 0)
    close = _et_ts(day.year, day.month, day.day, 20, 0)
    bars: list[Bar] = []
    ts, i = start, 0
    while ts < close:
        price = base + (i % 5) * 0.25
        bars.append(Bar(symbol, TF, ts, price, price + 0.5, price - 0.5,
                        price, 1000.0 + (ts % 500)))
        ts += period
        i += 1
    assert bars, f"no {TF} bars for {day}"
    return bars


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
    """Captures ``req_historical_data`` calls and cancelled reqIds."""

    def __init__(self, first_id: int = 5000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._next = first_id

    def req(self, contract, timeframe="5 mins", endDateTime="",
            whatToShow="TRADES", useRTH=1, extended_hours=False,
            bar_size=None, duration=None):
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


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    return win


def _setup(monkeypatch, qapp, symbol: str, now_ts: int):
    """Window with stubbed transport, current triple fixed, no load issued."""
    win = _make_window(monkeypatch, qapp)
    stub = _ReqStub()
    win.md_manager.req_historical_data = stub.req
    win.md_manager.cancel_historical_data = stub.cancel
    win._current_symbol = symbol
    win._current_tf = TF
    win.symbol_input.setText(symbol)
    idx = win.tf_combo.findText(TF)
    if idx >= 0:
        win.tf_combo.setCurrentIndex(idx)
    win.ext_hours_btn.setChecked(True)
    win._now_ts = lambda: now_ts
    session = win.get_or_create_session(symbol)
    return win, stub, session


def _ordinal_for_ts(view, target_ts: int) -> float:
    """Page ordinal of a plotted bar (first non-whitespace entry at ts)."""
    period = TIMEFRAME_SECONDS[TF]
    times, whitespace = series_times(view.plotted_bars, view.logical_index,
                                     period, True)
    for i, (t, ws) in enumerate(zip(times, whitespace)):
        if int(t) == int(target_ts) and not ws:
            return float(i)
    raise AssertionError(f"ts {target_ts} not plotted")


def _run_landing_case(monkeypatch, qapp, symbol: str, following: bool) -> None:
    """One follow-state leg: a prefetch wave lands; the viewport is pinned.

    Seeds recent + older blocks with a one-day interior hole, reports a
    settled viewport on the main chart, issues the prefetch wave, then
    asserts slot equality, no fresh-frame request and no range op across
    every arrival (per-bar landings plus the chunk end).
    """
    from datetime import timedelta  # noqa: F401 (kept: helper shape)

    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    try:
        now_day = _et_date(now_ts)
        recent = _trading_days_back(now_day, 5)
        hole = [_prev_trading_day(recent[0])]
        older: list = []
        cur = _prev_trading_day(hole[0])
        while len(older) < 3:
            older.append(cur)
            cur = _prev_trading_day(cur)
        older = sorted(older)
        assert len(older) == 3 and len(hole) == 1
        seed: list[Bar] = []
        for i, d in enumerate(recent):
            seed.extend(_session_bars(symbol, d, base=200.0 + i))
        for i, d in enumerate(older):
            seed.extend(_session_bars(symbol, d, base=100.0 + i))
        BarCache.save_bars(seed)
        cached = BarCache.get_bars(symbol, TF)
        visible = min(b.ts for b in cached
                      if _et_date(b.ts) == recent[0])

        # Production wiring: the main chart renders this session's wave.
        win._set_primary_session(session)
        panel = win.chart_panel
        panel.set_timeframe(TF)
        panel.set_extended_hours(True)
        panel.update_bars(list(cached))

        slot = _ordinal_for_ts(panel, visible)
        view_range = {"from": float(slot), "to": float(slot) + 10.0}
        assert panel.report_viewport(dict(view_range), following) is True
        before = dict(panel._pending_viewport["range"])
        assert panel._pending_viewport["following"] is following
        assert panel._pending_fresh_frame is False

        # Bridge spy: every op crossing on any prefetch arrival is captured.
        sent: list[list] = []
        bridge = panel._bridge
        orig_send = bridge.send_ops

        def _recording_send(ops):
            sent.append(list(ops))
            return orig_send(ops)

        monkeypatch.setattr(bridge, "send_ops", _recording_send)

        # Issue the prefetch wave for the settled report (decision + issue).
        win._on_viewport_settled(visible, following)
        assert len(stub.calls) == 1
        (rid,) = tuple(session._history_req_ids)
        issued_ops = len(sent)

        # Drive every bar of the hole through this chunk's window, landing by
        # landing, then the chunk end — the full arrival sequence.
        from services.backfill_service import find_missing_spans, plan_requests

        cached_ts = [b.ts for b in cached]
        plans = plan_requests(
            find_missing_spans(cached_ts, now_ts, TF, trailing_days=60,
                               ext_hours=True), TF)
        assert len(plans) == 1
        hole_bars: list[Bar] = []
        for d in hole:
            hole_bars.extend(_session_bars(symbol, d))
        for bar in hole_bars:
            win._on_historical_bar(
                rid, _FakeIbBar(bar.ts, bar.close, bar.volume))
            # Per-bar arrivals never touch the viewport or the bridge.
            assert panel._pending_viewport["range"] == before
            assert panel._pending_viewport["following"] is following
            assert panel._pending_fresh_frame is False
            assert len(sent) == issued_ops
        (rid2,) = tuple(session._history_req_ids)
        assert rid2 == rid  # the wave is still the single issued chunk
        win._on_historical_data_end(rid)
        qapp.processEvents()

        # The landed chunk rendered (the chart advanced) without moving.
        assert len(panel._bars) > len(cached)
        assert panel._pending_viewport["range"] == before
        assert panel._pending_viewport["following"] is following
        assert panel._pending_fresh_frame is False
        # No fresh frame was requested and no range op crossed on any
        # arrival: only data-replace ops (S-P11-3 preserve path).
        landing_ops = [op for batch in sent[issued_ops:] for op in batch]
        assert landing_ops, "expected the landed chunk to render"
        assert not [op for op in landing_ops
                    if op.get("op") == "set_visible_range"]
        set_bars_ops = [op for op in landing_ops
                        if op.get("op") == "set_bars"]
        assert set_bars_ops
        assert all(op.get("same_symbol") is True for op in set_bars_ops)
        # Terminal state: the wave idled with no viewport side effect.
        assert session._history_req_ids == set()
        assert win._backfill_indicator.text() == "Backfill: idle"
        assert panel._pending_viewport["range"] == before
    finally:
        win.close()


def test_t02_away_range_identical_across_landings(monkeypatch, qapp):
    """T02 (away): every prefetch arrival leaves the settled range alone."""
    _run_landing_case(monkeypatch, qapp, "P19V_A", following=False)


def test_t02_following_range_identical_across_landings(monkeypatch, qapp):
    """T02 (following): arrivals never extend the range — only the D51 live
    path (not driven here) may move the live edge."""
    _run_landing_case(monkeypatch, qapp, "P19V_B", following=True)
