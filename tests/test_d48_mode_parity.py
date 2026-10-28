"""P8-T03 / D48.4 — canonical daily+ full-session mode parity.

Drives the **real** ``MainWindow`` load path offscreen for ``1 week`` and
``1 month`` under RTH (Ext-Hours OFF) and under ETH (ON) and asserts:

* both loads return identical bars from one shared cache treatment
  (the canonical full-session mode), with a single shared cache key —
  no rows are ever written under the RTH key;
* every historical request issued under either toggle position carries
  ``extended_hours=True`` (the canonical mode is on the wire, not just
  in the planner);
* toggling the mode with the span cached issues no extra **backfill**
  requests (the toggle reload is a pure cache hit for the wave);
* the chart-model plotted/collapse membership output is identical under
  both modes.

Seed convention: the planner measures day presence by bars inside the
mode's session window (noon ET is inside both), so the seeded span uses
one noon-ET bar per trading day; the hole day left out of the seed forces
exactly one wave chunk on the first load, proving the write path also
uses the canonical key. Bar timestamps are presence seeds, not calendar
bucket anchors — mode treatment, not aggregation anchoring, is under test.

Prime carve-out: a mid-session load still issues the existing forming-bar
priming request (unchanged S-P8-5 behaviour); it is a live-feed prime,
not a backfill request, so the "no extra requests" assertion counts
**wave** calls (``bar_size`` == the timeframe) and separately asserts
every prime call is canonical too.
"""

from __future__ import annotations

import itertools
from datetime import datetime, timedelta

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_cache import BarCache
from data.models import Bar
from services.chart_model import (
    collapse_for_bars,
    display_xs,
    is_bar_plotted,
    plotted_index_rows,
)
from services.market_calendar import is_trading_day

EASTERN = ZoneInfo("America/New_York")

#: Monday 2026-11-02 12:00 ET (mid-session: the seeded current-day bar is
#: "present", so a fully seeded span is cache-current with no wave).
NOW = int(datetime(2026, 11, 2, 12, 0, tzinfo=EASTERN).timestamp())

TIMEFRAMES = ["1 week", "1 month"]


# ---------------------------------------------------------------------------
# Harness (modelled on tests/test_d42_depth_floor.py + test_d27_aggregator_priming.py)
# ---------------------------------------------------------------------------
class _FakeIbBar:
    """Minimal ibapi ``BarData`` double consumed by ``_on_historical_bar``."""

    def __init__(self, ts: int, price: float = 100.0):
        self.date = str(int(ts))  # parse_ibkr_date accepts an epoch string
        self.open = price
        self.high = price + 0.5
        self.low = price - 0.5
        self.close = price
        self.volume = 1000


class _ReqStub:
    """Unbounded ``req_historical_data`` double (the D42 gotcha).

    Ids are drawn from an unbounded counter — never a fixed-list
    ``iter([...])``, which a multi-request span would exhaust
    (``StopIteration``).
    """

    def __init__(self, first_id: int = 1000):
        self.calls: list[dict] = []
        self.cancelled: list[int] = []
        self._ids = itertools.count(first_id)

    def req(self, contract, timeframe="5 mins", endDateTime="", whatToShow="TRADES",
            useRTH=1, extended_hours=False, **kwargs):
        req_id = next(self._ids)
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
    from ibkr import pacing as pacing_mod

    monkeypatch.setattr(pacing_mod.pacing_manager, "throttle", lambda: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.rt_manager.subscribe = lambda *a, **k: 4242
    win.show()
    qapp.processEvents()
    return win


def _set_mode(win, mode: bool) -> None:
    """Set the load's ext-hours toggle without firing its change slot."""
    win.ext_hours_btn.blockSignals(True)
    win.ext_hours_btn.setChecked(mode)
    win.ext_hours_btn.blockSignals(False)


def _trading_days_ending(now_day, count: int):
    """The ``count`` trading days ending at ``now_day`` (inclusive), ascending."""
    days = []
    day = now_day
    while len(days) < count:
        if is_trading_day(day):
            days.append(day)
        day -= timedelta(days=1)
    return list(reversed(days))


def _noon_ts(day) -> int:
    """A timestamp inside *both* mode windows (09:30-16:00 and 04:00-20:00 ET)."""
    return int(datetime(day.year, day.month, day.day, 12, 0,
                        tzinfo=EASTERN).timestamp())


def _wave_calls(stub: _ReqStub, timeframe: str) -> list[dict]:
    """Backfill-wave calls only (primes carry ``'5 secs'``/``'1 min'``)."""
    return [c for c in stub.calls if c.get("bar_size") == timeframe]


def _series_key(bars) -> list[tuple]:
    return [(b.ts, b.open, b.high, b.low, b.close, b.volume) for b in bars]


# ---------------------------------------------------------------------------
# P8-T03-T11 — mode parity for each new timeframe
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("timeframe", TIMEFRAMES)
def test_p8_t03_daily_plus_mode_parity(monkeypatch, qapp, timeframe):
    now_day = datetime.fromtimestamp(NOW, tz=EASTERN).date()
    seed_days = _trading_days_ending(now_day, 10)
    hole_day = seed_days[3]
    symbol = f"P8{'W' if timeframe == '1 week' else 'M'}1"
    win = _make_window(monkeypatch, qapp)
    try:
        stub = _ReqStub()
        win._now_ts = lambda: NOW

        # Seed all but the hole day at noon ET (in-window under both modes).
        for i, day in enumerate(seed_days):
            if day == hole_day:
                continue
            BarCache.save_bars(
                [Bar(
                    symbol=symbol, timeframe=timeframe, ts=_noon_ts(day),
                    open=100.0 + i, high=100.5 + i, low=99.5 + i,
                    close=100.0 + i, volume=1000,
                )],
                ext_hours=True,
            )

        # Load #1 under RTH (button OFF): the hole day forces one wave chunk.
        _set_mode(win, False)
        win.symbol_input.setText(symbol.lower())  # load_chart upper-cases
        win.tf_combo.setCurrentText(timeframe)
        win.md_manager.req_historical_data = stub.req
        win.md_manager.cancel_historical_data = stub.cancel
        win.load_chart()
        qapp.processEvents()

        session = win.get_or_create_session(symbol)
        wave_ids = [c["reqId"] for c in stub.calls
                    if c["reqId"] in session._history_req_ids]
        assert wave_ids, f"{timeframe}: expected one wave chunk for the hole day"
        # The wave is canonical: full-session mode on the wire despite RTH.
        for call in _wave_calls(stub, timeframe):
            assert call["extended_hours"] is True, (
                f"{timeframe}: wave call not canonical: {call}"
            )
        # Feed the hole day, then end every issued request (wave + prime).
        for ts_price in [(_noon_ts(hole_day), 142.0)]:
            win._on_historical_bar(
                wave_ids[0], _FakeIbBar(ts_price[0], ts_price[1])
            )
        issued = [c["reqId"] for c in stub.calls]
        prime_id = session._prime_req_id
        for req_id in issued:
            win._on_historical_data_end(req_id)
        qapp.processEvents()

        bars_rth = _series_key(session.get_bars(timeframe))
        assert len(bars_rth) == len(seed_days), (
            f"{timeframe}: expected the seeded span + hole day, got {len(bars_rth)}"
        )
        n_wave_after_first = len(_wave_calls(stub, timeframe))

        # Load #2 under ETH (button ON): identical bars, no new wave requests.
        _set_mode(win, True)
        win.load_chart()
        qapp.processEvents()
        bars_eth = _series_key(session.get_bars(timeframe))
        assert bars_eth == bars_rth, (
            f"{timeframe}: RTH and ETH loads diverged"
        )
        assert len(_wave_calls(stub, timeframe)) == n_wave_after_first, (
            f"{timeframe}: ETH load issued extra wave requests when cached"
        )

        # Single shared cache key: nothing under RTH, everything canonical.
        assert BarCache.get_bars(symbol, timeframe, ext_hours=False) == []
        cached_eth = _series_key(
            BarCache.get_bars(symbol, timeframe, ext_hours=True)
        )
        assert cached_eth == bars_rth

        # Toggle back to RTH through the real slot: cache hit, no new waves.
        n_calls_before_toggle = len(stub.calls)
        win.ext_hours_btn.setChecked(False)  # fires _on_ext_hours_toggled
        qapp.processEvents()
        bars_toggled = _series_key(session.get_bars(timeframe))
        assert bars_toggled == bars_rth, (
            f"{timeframe}: toggled reload diverged"
        )
        new_wave = [c for c in stub.calls[n_calls_before_toggle:]
                    if c.get("bar_size") == timeframe]
        assert new_wave == [], (
            f"{timeframe}: toggle issued extra wave requests: {new_wave}"
        )
        # Every request on the wire — wave and prime — used the canonical mode.
        for call in stub.calls:
            assert call["extended_hours"] is True, (
                f"{timeframe}: non-canonical request: {call}"
            )

        # Chart-model membership is mode-independent for daily-and-coarser.
        bars = BarCache.get_bars(symbol, timeframe, ext_hours=True)
        assert plotted_index_rows(bars, timeframe, False) == list(range(len(bars)))
        assert (plotted_index_rows(bars, timeframe, False)
                == plotted_index_rows(bars, timeframe, True))
        assert all(is_bar_plotted(b, timeframe, False) for b in bars)
        assert all(is_bar_plotted(b, timeframe, True) for b in bars)
        assert (display_xs(bars, collapse_for_bars(bars, timeframe, False))
                == display_xs(bars, collapse_for_bars(bars, timeframe, True)))
    finally:
        win.close()
