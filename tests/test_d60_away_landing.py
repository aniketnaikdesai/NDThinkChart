"""P21-T2 — away-landing neutrality gate + session-open gap reset (D60.7/D60.4/D60.3).

Repro-first record (S-P21-5): the ES 5-min away repro — scrolled into the
past with a wave in flight, one chunk per leg (backfill continuation,
realtime update, prefetch arrival) — was driven against the pre-gate tree
(``git show HEAD:chart_assets/lwc/chart.js`` + working-tree P21-T1 shift)
through the real page glue (``lwApplyOps``). Legs A/B/C (same-symbol
preserve + upsert-only) already held bit-identical; the repro FAILED on two
of the candidate movers, and the trace named them:

* mover 1 — ``landFreshFrame`` via a ``set_visible_range`` op riding a
  same-symbol chunk while away (leg D): range yanked to the frame and
  follow re-engaged;
* mover 2 — ``fitToWidth()`` on a chunk replace without same-symbol
  continuity while away (leg E): range fit to ``{0, newest}`` and follow
  re-engaged;
* mover 3 (same family) — the ``fitToWidth()`` fallback on a failed
  range re-apply, which fires even while away.

The S-P21-5 gate (``chart.js::applyOps``) routes every away landing through
the preserve path: same-symbol data re-applies the pre-replace range (no
fresh-frame re-land, no fit, hold on failure); a chunk without continuity
and without its own frame holds the pre-envelope range instead of fitting;
a new-symbol/timeframe load carrying its own explicit frame still frames
(S-P18-4 precedence stands); first loads still fit; the follow shift
(S-P21-1) is untouched.

No Python production edit: ``set_series`` continuity (same-symbol chunks
always carry ``same_symbol=True`` while a report exists) and the
``update_live_bar`` emit shape (ticks/upserts only, hole republish with
``same_symbol=True``) plus the no-range-op landing shape already route
through the preserve path — pinned here by bridge-spy assertions. The
session-open reset (S-P21-3) likewise verifies as already structural:
``fresh_frame_ops`` consults only the ``following`` leg and
``FRESH_FRAME_RIGHT_PADDING``, never a carried range — pinned here as
tests-only.

AC-D51.2 guard note: ``test_p11_no_yank::T21`` (stay-put, no yank while
away) stays green on this tree; ``T22`` asserts the pre-P21 resume went
through ``scrollToRealTime`` (call-counted), which P21-T1 deliberately
removed in favour of the slot-delta shift — T22 is red for that P21-T1
reason, outside this task's footprint (reported, not touched).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.bar_cache import BarCache
from data.models import Bar
from services.market_calendar import is_trading_day
from ui.lwc_view import FRESH_FRAME_RIGHT_PADDING, series_times

REPO = Path(__file__).resolve().parent.parent

EASTERN = ZoneInfo("America/New_York")

TF = "5 mins"

# ---------------------------------------------------------------------------
# Page-level harness (no renderer): the real page glue (chart.js +
# envelope.js) against the same stubbed document / fake LightweightCharts
# 5.x tree test_p11_no_yank uses — seeded series driven through the real
# lwApplyOps and queried through the real lwVisibleRange / lwIsFollowing
# surface, including the real bindKeyboard pan path (AR-P11-1). The fake
# models setData framing the fresh series (AR-P11-3) and update leaving the
# visible range untouched.
# ---------------------------------------------------------------------------

_PRELUDE = r"""
const { readFileSync } = require("node:fs");
const assert = require("node:assert/strict");
const DIR = %DIR%;
const _fakeScaleState = { range: null };
const _fakeChartState = { count: 0 };
function _fakeTimeScale() {
  return {
    getVisibleLogicalRange() {
      const r = _fakeScaleState.range;
      return r ? { from: r.from, to: r.to } : null;
    },
    setVisibleLogicalRange(r) {
      _fakeScaleState.range = { from: Number(r.from), to: Number(r.to) };
    },
    getVisibleRange() { return null; },
    fitContent() {
      if (_fakeChartState.count > 0) {
        _fakeScaleState.range = { from: 0, to: _fakeChartState.count - 1 };
      }
    },
    scrollToRealTime() {
      const r = _fakeScaleState.range;
      const span = r ? (r.to - r.from) : 10;
      _fakeScaleState.range = {
        from: _fakeChartState.count - 1 - span,
        to: _fakeChartState.count - 1,
      };
    },
    applyOptions() {},
    options() { return {}; },
  };
}
function _fakeSeries(trackCount) {
  return {
    _rows: [],
    setData(rows) {
      this._rows = rows;
      if (trackCount) {
        _fakeChartState.count = rows.length;
        _fakeScaleState.range = { from: 0, to: rows.length - 1 };
      }
    },
    update(row) {
      const last = this._rows.length ? this._rows[this._rows.length - 1].time : null;
      if (row && (last === null || row.time > last)) {
        this._rows.push(row);
        if (trackCount) _fakeChartState.count = this._rows.length;
      } else if (row && last !== null && row.time === last) {
        this._rows[this._rows.length - 1] = row;
      }
    },
    applyOptions() {},
  };
}
function _fakeChart() {
  const scale = _fakeTimeScale();
  return {
    timeScale() { return scale; },
    addSeries(ctor) {
      return _fakeSeries(ctor !== globalThis.LightweightCharts.HistogramSeries);
    },
    addCandlestickSeries() { return _fakeSeries(true); },
    addLineSeries() { return _fakeSeries(true); },
    addAreaSeries() { return _fakeSeries(true); },
    addHistogramSeries() { return _fakeSeries(false); },
    priceScale() { return { applyOptions() {} }; },
    resize() {},
    applyOptions() {},
  };
}
const _fakeEl = {
  clientWidth: 960,
  clientHeight: 850,
  _listeners: {},
  addEventListener(type, fn) { this._listeners[type] = fn; },
  getBoundingClientRect() {
    return { width: 960, height: 850, top: 0, left: 0 };
  },
};
globalThis.LightweightCharts = {
  createChart() { return _fakeChart(); },
  CandlestickSeries: {},
  LineSeries: {},
  AreaSeries: {},
  HistogramSeries: {},
};
globalThis.document = {
  readyState: "complete",
  title: "",
  getElementById() { return _fakeEl; },
  addEventListener() {},
};
globalThis.window = {};
globalThis.window.setTimeout = (...a) => setTimeout(...a);
globalThis.window.clearTimeout = (...a) => clearTimeout(...a);
for (const name of ["LwInteraction", "LwAlarms", "LwPrimitives",
  "LwOverlays", "LwStudies", "LwGestures"]) {
  globalThis.window[name] = { bind() {} };
}
globalThis.window.LwEnvelope = require(DIR + "/envelope.js");
require(DIR + "/chart.js");
const page = globalThis.window;
const BASE = 1700000000;
function cols(n, start) {
  const ts = [], open = [], high = [], low = [], close = [];
  for (let i = 0; i < n; i++) {
    ts.push(BASE + (start + i) * 300);
    open.push(100 + (start + i) * 0.1);
    high.push(100 + (start + i) * 0.1 + 0.25);
    low.push(100 + (start + i) * 0.1 - 0.25);
    close.push(100 + (start + i) * 0.05);
  }
  return { ts, open, high, low, close };
}
function vols(n, start) {
  const ts = [], value = [];
  for (let i = 0; i < n; i++) {
    ts.push(BASE + (start + i) * 300);
    value.push(1000 + ((start + i) % 500));
  }
  return { ts, value };
}
function seedCandles(n) {
  const c = cols(n, 0);
  const v = vols(n, 0);
  const res = page.lwApplyOps({
    v: 1,
    ops: [
      { op: "set_bars", series: "candles",
        cols: { ts: c.ts, open: c.open, high: c.high, low: c.low, close: c.close } },
      { op: "set_volume", series: "volume",
        cols: { ts: v.ts, value: v.value } },
      { op: "set_visible_range", range: { from: 0, to: n - 1 + 2 },
        following: true },
    ],
  });
  assert.equal(res.error, null, "seed envelope applies");
}
function upsertTick(t, same) {
  const res = page.lwApplyOps({
    v: 1,
    ops: [
      { op: "update_bar", series: "candles",
        cols: { ts: [t], open: [106.0], high: [106.25], low: [105.75],
                close: [same ? 106.05 : 106.10] } },
      { op: "update_bar", series: "volume",
        cols: { ts: [t], value: [1200] } },
    ],
  });
  assert.equal(res.error, null, "tick envelope applies");
}
function replaceCandles(n, sameSymbol, extraOps) {
  const c = cols(n, 0);
  const v = vols(n, 0);
  const bars = { op: "set_bars", series: "candles",
    cols: { ts: c.ts, open: c.open, high: c.high, low: c.low, close: c.close } };
  if (sameSymbol) bars.same_symbol = true;
  const vol = { op: "set_volume", series: "volume",
    cols: { ts: v.ts, value: v.value } };
  if (sameSymbol) vol.same_symbol = true;
  const res = page.lwApplyOps({ v: 1, ops: [bars, vol, ...(extraOps || [])] });
  assert.equal(res.error, null, "replace envelope applies");
}
function pressKey(k) {
  _fakeEl._listeners["keydown"]({ key: k, preventDefault() {} });
}
function parkAway() {
  seedCandles(60);
  assert.equal(page.lwIsFollowing(), true, "seeded edge follows");
  for (let i = 0; i < 6; i++) pressKey("ArrowLeft"); // real pan path
  assert.equal(page.lwIsFollowing(), false, "panned away");
  const probe = page.lwVisibleRange();
  return { from: probe.range.from, to: probe.range.to };
}
"""


def _run_node(flow: str) -> dict:
    """Run the harness prelude + one test flow; return the JSON it prints."""
    program = _PRELUDE.replace("%DIR%", json.dumps(
        str(REPO / "chart_assets" / "lwc"))) + flow
    node = shutil.which("node") or "node"
    proc = subprocess.run(
        [node, "-e", program],
        capture_output=True, text=True, timeout=120,
        cwd=str(REPO),
    )
    assert proc.returncode == 0, (
        "node harness failed (exit %d):\nSTDOUT:\n%s\nSTDERR:\n%s"
        % (proc.returncode, proc.stdout, proc.stderr)
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, "node harness printed nothing"
    return json.loads(lines[-1])


# -- P21-T2-AC1: the away repro, one chunk per leg (page level) -------------


def test_p21_t2_ac1_legA_backfill_continuation():
    """Leg A (backfill continuation): same-symbol full replace while away."""
    payload = _run_node(r"""
const frozen = parkAway();
assert.equal(typeof page.lwRememberedGap, "function", "gap probe exists");
assert.equal(page.lwRememberedGap(), 2, "gap default mirrors FRESH_FRAME_RIGHT_PADDING");
replaceCandles(70, true);
const probe = page.lwVisibleRange();
assert.deepEqual(probe.range, frozen, "backfill chunk moved the away range");
assert.equal(page.lwIsFollowing(), false, "backfill chunk re-engaged follow");
assert.equal(probe.newestSlot, 69, "series grew under the frozen viewport");
console.log(JSON.stringify({ test: "legA", frozen, range: probe.range,
  newestSlot: probe.newestSlot, following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "legA"
    assert payload["range"] == payload["frozen"]
    assert payload["newestSlot"] == 69
    assert payload["following"] is False


def test_p21_t2_ac1_legB_realtime_update():
    """Leg B (realtime update): new-bar upserts + a forming tick while away."""
    payload = _run_node(r"""
const frozen = parkAway();
let lastT = BASE + 59 * 300;
for (let k = 0; k < 3; k++) {
  lastT += 300;
  upsertTick(lastT, false); // new period
}
upsertTick(lastT, true); // forming-bar tick on the newest period
const probe = page.lwVisibleRange();
assert.deepEqual(probe.range, frozen, "realtime update moved the away range");
assert.equal(page.lwIsFollowing(), false, "realtime update re-engaged follow");
assert.equal(probe.newestSlot, 62, "series grew under the frozen viewport");
console.log(JSON.stringify({ test: "legB", frozen, range: probe.range,
  newestSlot: probe.newestSlot, following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "legB"
    assert payload["range"] == payload["frozen"]
    assert payload["newestSlot"] == 62
    assert payload["following"] is False


def test_p21_t2_ac1_legC_prefetch_arrival():
    """Leg C (prefetch arrival): same-length same-symbol replace while away."""
    payload = _run_node(r"""
const frozen = parkAway();
replaceCandles(60, true); // hole-fill shape: same length, same symbol
const probe = page.lwVisibleRange();
assert.deepEqual(probe.range, frozen, "prefetch arrival moved the away range");
assert.equal(page.lwIsFollowing(), false, "prefetch arrival re-engaged follow");
assert.equal(probe.newestSlot, 59, "series length unchanged");
console.log(JSON.stringify({ test: "legC", frozen, range: probe.range,
  newestSlot: probe.newestSlot, following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "legC"
    assert payload["range"] == payload["frozen"]
    assert payload["newestSlot"] == 59
    assert payload["following"] is False


def test_p21_t2_ac1_legD_fresh_frame_on_chunk_held():
    """Leg D (mover 1): a fresh frame riding a same-symbol chunk while away.

    Pre-gate this failed — ``landFreshFrame`` yanked the range to the frame
    and re-engaged follow. Post-gate the chunk holds the away range.
    """
    payload = _run_node(r"""
const frozen = parkAway();
replaceCandles(70, true, [
  { op: "set_visible_range", range: { from: 20, to: 71 }, following: true },
]);
const probe = page.lwVisibleRange();
assert.deepEqual(probe.range, frozen, "fresh frame re-landed on the chunk");
assert.equal(page.lwIsFollowing(), false, "chunk frame re-engaged follow");
console.log(JSON.stringify({ test: "legD", frozen, range: probe.range,
  newestSlot: probe.newestSlot, following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "legD"
    assert payload["range"] == payload["frozen"]
    assert payload["following"] is False


def test_p21_t2_ac1_legE_no_continuity_chunk_held():
    """Leg E (mover 2): a chunk without continuity while away never fits.

    Pre-gate this failed — the replace fell into ``fitToWidth()`` and framed
    ``{0, newest}`` with follow re-engaged. Post-gate it holds the
    pre-envelope range.
    """
    payload = _run_node(r"""
const frozen = parkAway();
replaceCandles(70, false); // no same_symbol directive, no frame
const probe = page.lwVisibleRange();
assert.deepEqual(probe.range, frozen, "no-continuity chunk fit the viewport");
assert.equal(page.lwIsFollowing(), false, "no-continuity chunk re-engaged follow");
console.log(JSON.stringify({ test: "legE", frozen, range: probe.range,
  newestSlot: probe.newestSlot, following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "legE"
    assert payload["range"] == payload["frozen"]
    assert payload["following"] is False


def test_p21_t2_ac1_new_symbol_frame_still_wins():
    """S-P18-4 precedence stands: a new-symbol load's own frame still lands."""
    payload = _run_node(r"""
const frozen = parkAway();
const c = cols(60, 200);
const res = page.lwApplyOps({ v: 1, ops: [
  { op: "set_bars", series: "candles",
    cols: { ts: c.ts, open: c.open, high: c.high, low: c.low, close: c.close } },
  { op: "set_visible_range", range: { from: 20, to: 61 }, following: true },
]});
assert.equal(res.error, null, "new-symbol envelope applies");
const probe = page.lwVisibleRange();
assert.deepEqual(probe.range, { from: 20, to: 61 }, "new-symbol frame dropped");
assert.equal(page.lwIsFollowing(), true, "new-symbol frame must follow");
console.log(JSON.stringify({ test: "freshWins", frozen, range: probe.range,
  following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "freshWins"
    assert payload["range"] == {"from": 20, "to": 61}
    assert payload["following"] is True


# -- P21-T2-AC2: away-arrival identity + disengaged follow (page level) ------


def test_p21_t2_ac2_forming_ticks_hold_and_pan_resumes():
    """Away arrivals move nothing; only an explicit pan-back resumes follow.

    The green half of the AC-D51.2 guard (``T21``-equivalent) without the
    stale ``scrollToRealTime`` call-count assertion P21-T1 retired.
    """
    payload = _run_node(r"""
const frozen = parkAway();
const lastT = BASE + 59 * 300;
for (let k = 0; k < 5; k++) upsertTick(lastT, true); // forming ticks only
assert.deepEqual(page.lwVisibleRange().range, frozen, "ticks moved the view");
assert.equal(page.lwIsFollowing(), false, "ticks re-engaged follow");
let pans = 0;
while (!page.lwIsFollowing() && pans < 60) { pressKey("ArrowRight"); pans++; }
assert.equal(page.lwIsFollowing(), true, "pan-back-to-edge never resumes");
console.log(JSON.stringify({ test: "ac2", frozen,
  range: page.lwVisibleRange().range, pans,
  following: page.lwIsFollowing() }));
""")
    assert payload["test"] == "ac2"
    assert payload["following"] is True
    assert payload["pans"] > 0


# ---------------------------------------------------------------------------
# Python offscreen half: every landing leg through the real driver
# (LwcChartView via MainWindow) — viewport untouched, follow disengaged, no
# range op on the bridge, same-symbol continuity stamped.
# ---------------------------------------------------------------------------


def _et_ts(y: int, m: int, d: int, h: int = 0, minute: int = 0) -> int:
    return int(datetime(y, m, d, h, minute, tzinfo=EASTERN).timestamp())


def _prev_trading_day(d):
    d -= timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def _next_trading_day(d):
    d += timedelta(days=1)
    while not is_trading_day(d):
        d += timedelta(days=1)
    return d


def _et_date(ts):
    return datetime.fromtimestamp(ts, tz=EASTERN).date()


def _ordinal_for_ts(view, target_ts: int) -> float:
    """Page ordinal of a plotted bar (first non-whitespace entry at ts)."""
    period = TIMEFRAME_SECONDS[TF]
    times, whitespace = series_times(view.plotted_bars, view.logical_index,
                                     period, True)
    for i, (t, ws) in enumerate(zip(times, whitespace)):
        if int(t) == int(target_ts) and not ws:
            return float(i)
    raise AssertionError(f"ts {target_ts} not plotted")


def _trading_days_back(end, n: int) -> list:
    assert is_trading_day(end)
    days = [end]
    while len(days) < n:
        days.append(_prev_trading_day(days[-1]))
    return sorted(days)


def _session_bars(symbol: str, day, base: float = 100.0) -> list[Bar]:
    """One complete ETH (04:00-20:00) 5-min session, like the feed."""
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


def _seeded_away(monkeypatch, qapp, symbol: str, seed_days: int = 5,
                 hole: bool = False):
    """Seeded main chart with a settled AWAY report; returns harness dict.

    P19 shape (ESC-113): the full recent block is always seeded; when
    ``hole`` is true the day before ``recent[0]`` is left out as a genuine
    one-day *interior* hole (with a 3-day older block behind it, so the
    planner sees hole spans, not a leading-edge gap), and the settled
    report is slot-mapped off a real bar ts — the wave-in-flight setup
    ``_on_viewport_settled`` needs to issue exactly 1 request.
    """
    now_ts = _et_ts(2026, 10, 2, 20, 0)  # Friday
    win, stub, session = _setup(monkeypatch, qapp, symbol, now_ts)
    try:
        now_day = datetime.fromtimestamp(now_ts, tz=EASTERN).date()
        recent = _trading_days_back(now_day, seed_days)
        if hole:
            hole_day = _prev_trading_day(recent[0])
            older: list = []
            cur = _prev_trading_day(hole_day)
            while len(older) < 3:
                older.append(cur)
                cur = _prev_trading_day(cur)
            older = sorted(older)
            seed_days_list = list(recent)
            hole_days = [hole_day]
        else:
            seed_days_list = list(recent)
            older = []
            hole_days = []
        seed: list[Bar] = []
        for i, d in enumerate(seed_days_list):
            seed.extend(_session_bars(symbol, d, base=200.0 + i))
        for i, d in enumerate(older):
            seed.extend(_session_bars(symbol, d, base=100.0 + i))
        BarCache.save_bars(seed)
        cached = BarCache.get_bars(symbol, TF)
        win._set_primary_session(session)
        panel = win.chart_panel
        panel.set_timeframe(TF)
        panel.set_extended_hours(True)
        panel.update_bars(list(cached))
        newest_ts = max(b.ts for b in cached)
        period = TIMEFRAME_SECONDS[TF]
        times, whitespace = series_times(panel.plotted_bars,
                                         panel.logical_index, period, True)
        assert not any(whitespace)
        # Slot-mapped settled report off a real bar ts (P19 shape): the
        # oldest visible bar is the first bar of recent[0].
        visible_ts = min(b.ts for b in cached
                         if _et_date(b.ts) == recent[0])
        slot = _ordinal_for_ts(panel, visible_ts)
        view_range = {"from": float(slot), "to": float(slot) + 10.0}
        assert panel.report_viewport(dict(view_range), False) is True
        before = dict(panel._pending_viewport["range"])
        assert panel._pending_viewport["following"] is False
        sent: list[list] = []
        bridge = panel._bridge
        orig_send = bridge.send_ops

        def _recording_send(ops):
            sent.append(list(ops))
            return orig_send(ops)

        monkeypatch.setattr(bridge, "send_ops", _recording_send)
        return {
            "win": win, "stub": stub, "session": session, "panel": panel,
            "cached": cached, "seed_days": seed_days_list,
            "hole_days": hole_days, "older_days": list(older),
            "recent": recent, "now_ts": now_ts,
            "before": before, "sent": sent, "issued_ops": len(sent),
            "newest_ts": newest_ts, "visible_ts": visible_ts,
        }
    except Exception:
        win.close()
        raise


def _assert_away_pinned(ctx, issue_note: str = "") -> list:
    """The away viewport is bit-identical, follow disengaged, no range op."""
    panel = ctx["panel"]
    assert panel._pending_viewport["range"] == ctx["before"], issue_note
    assert panel._pending_viewport["following"] is False, issue_note
    assert panel._pending_fresh_frame is False, issue_note
    landing = [op for batch in ctx["sent"][ctx["issued_ops"]:]
               for op in batch]
    assert not [op for op in landing
                if op.get("op") == "set_visible_range"], issue_note
    return landing


def test_p21_t2_ac1_backfill_chunk_with_wave_in_flight(monkeypatch, qapp):
    """AC1 backfill leg: an interior-hole wave lands chunk-by-chunk, away."""
    ctx = _seeded_away(monkeypatch, qapp, "P21TA", hole=True)
    win = ctx["win"]
    panel = ctx["panel"]
    try:
        from services.backfill_service import find_missing_spans, plan_requests

        win._on_viewport_settled(ctx["visible_ts"], False)
        assert len(ctx["stub"].calls) == 1
        (rid,) = tuple(ctx["session"]._history_req_ids)
        cached_ts = [b.ts for b in ctx["cached"]]
        plans = plan_requests(
            find_missing_spans(cached_ts, ctx["now_ts"], TF,
                               trailing_days=60, ext_hours=True), TF)
        assert len(plans) == 1
        hole_bars: list[Bar] = []
        for d in ctx["hole_days"]:
            hole_bars.extend(_session_bars("P21TA", d))
        for bar in hole_bars:
            win._on_historical_bar(
                rid, _FakeIbBar(bar.ts, bar.close, bar.volume))
            assert panel._pending_viewport["range"] == ctx["before"]
            assert panel._pending_viewport["following"] is False
        win._on_historical_data_end(rid)
        qapp.processEvents()
        assert len(panel._bars) > len(ctx["cached"])
        landing = _assert_away_pinned(ctx, "backfill chunk moved the view")
        assert landing, "expected the landed chunk to render"
        set_bars = [op for op in landing if op.get("op") == "set_bars"]
        assert set_bars
        assert all(op.get("same_symbol") is True for op in set_bars)
    finally:
        win.close()


def test_p21_t2_ac1_realtime_and_forming_ticks(monkeypatch, qapp):
    """AC1 realtime leg + AC2 identity: live arrivals never move an away view.

    New periods (next trading session open) and same-timestamp forming
    ticks cross as tick upserts only — no range op, no fresh frame, no
    continuity stamp needed, viewport bit-identical, follow disengaged.
    """
    ctx = _seeded_away(monkeypatch, qapp, "P21TB")
    win = ctx["win"]
    panel = ctx["panel"]
    try:
        now_day = datetime.fromtimestamp(ctx["now_ts"], tz=EASTERN).date()
        monday = _next_trading_day(now_day)
        period = TIMEFRAME_SECONDS[TF]
        base_ts = _et_ts(monday.year, monday.month, monday.day, 4, 0)
        last_close = ctx["newest_ts"]
        assert base_ts > last_close
        for k in range(3):
            ts = base_ts + k * period
            price = 210.0 + k * 0.1
            panel.update_live_bar(
                Bar("P21TB", TF, ts, price, price + 0.5, price - 0.5,
                    price, 1500.0))
            assert panel._pending_viewport["range"] == ctx["before"]
            assert panel._pending_viewport["following"] is False
        panel.update_live_bar(
            Bar("P21TB", TF, base_ts + 2 * period, 211.0, 211.4, 210.6,
                210.9, 1600.0))
        landing = _assert_away_pinned(ctx, "live bars moved the away view")
        assert landing, "expected live-bar ops to cross"
        assert not [op for op in landing if op.get("op") in
                    ("set_bars", "set_volume")], (
            "steady live bars must not republish the series")
        assert [op for op in landing if op.get("op") == "update_bar"], (
            "live bars cross as tick upserts")
    finally:
        win.close()


def test_p21_t2_ac1_prefetch_hole_fill_replace(monkeypatch, qapp):
    """AC1 prefetch leg: the hole-fill full replace holds the away range."""
    ctx = _seeded_away(monkeypatch, qapp, "P21TC", hole=True)
    win = ctx["win"]
    panel = ctx["panel"]
    try:
        full: list[Bar] = list(ctx["cached"])
        for d in ctx["hole_days"]:
            full.extend(_session_bars("P21TC", d))
        full.sort(key=lambda b: b.ts)
        assert len(full) > len(ctx["cached"])
        panel.update_bars(full)
        qapp.processEvents()
        landing = _assert_away_pinned(ctx, "prefetch replace moved the view")
        set_bars = [op for op in landing if op.get("op") == "set_bars"]
        assert set_bars
        assert all(op.get("same_symbol") is True for op in set_bars)
    finally:
        win.close()


def test_p21_t2_ac3_session_open_resets_carried_gap(monkeypatch, qapp):
    """AC3: no stale gap survives a session open — the frame lands default.

    Tests-only (already structural): ``fresh_frame_ops`` consults only the
    ``following`` leg, never a carried range; ``set_symbol`` clears the
    pending report so no stale gap crosses the open.
    """
    assert FRESH_FRAME_RIGHT_PADDING == 2
    ctx = _seeded_away(monkeypatch, qapp, "P21TD")
    win = ctx["win"]
    panel = ctx["panel"]
    try:
        # Poison the memory + pending report with a carried non-zero gap.
        panel._viewport_memory["P21TD"] = {
            "range": {"from": 1000.0, "to": 2000.0}, "following": True}
        panel.report_viewport({"from": 5.0, "to": 15.0}, True)
        # Session open on a fresh symbol: pending cleared, frame armed.
        panel.set_symbol("P21TE")
        assert panel._pending_viewport is None
        assert panel._pending_fresh_frame is True
        seed: list[Bar] = []
        for i, d in enumerate(ctx["seed_days"]):
            seed.extend(_session_bars("P21TE", d, base=300.0 + i))
        BarCache.save_bars(seed)
        panel.update_bars(list(BarCache.get_bars("P21TE", TF)))
        qapp.processEvents()
        frame = panel.fresh_frame_ops()
        assert frame is not None
        period = TIMEFRAME_SECONDS[TF]
        times, _ws = series_times(panel.plotted_bars, panel.logical_index,
                                  period, True)
        newest_slot = len(times) - 1
        gap = float(frame["range"]["to"]) - newest_slot
        assert gap == FRESH_FRAME_RIGHT_PADDING == 2, (
            f"post-open gap {gap} != fresh-frame default 2")
        # The wire agrees: the landed frame carries the default gap and the
        # poisoned range never crossed.
        landing = [op for batch in ctx["sent"][ctx["issued_ops"]:]
                   for op in batch]
        frames = [op for op in landing
                  if op.get("op") == "set_visible_range"]
        assert len(frames) == 1
        assert frames[0]["range"] == frame["range"]
        assert frames[0]["range"] != {"from": 1000.0, "to": 2000.0}
    finally:
        win.close()
