"""P18-T2: fresh per-timeframe framing with follow-state memory (D57.2).

Offscreen pytest half (no renderer): seeded-series cases drive the real
``LwcChartView`` and assert the frame op appended post-``set_series``
through the existing range-op wire shape (``set_visible_range`` riding the
bar envelope after the rows). The page-side application (explicit frame
over the preserved-range path, deferred landing via the ``needsFit``
retry) lives in ``chart_assets/lwc/chart.js`` (``landFreshFrame`` /
``landDeferred``) and is pinned here through a small ``node`` harness
booting the real page glue, mirroring ``tests/test_p11_no_yank.py``.
"""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from data.models import Bar
from services.market_calendar import session_windows
from ui import lwc_view as LV

REPO = Path(__file__).resolve().parent.parent

# Thursday 2026-10-29 14:00 UTC (10:00 ET) — a regular-session weekday, so
# RTH filtering keeps seeded bars regardless of ``ext_hours``.
BASE_TS = int(datetime.datetime(2026, 10, 29, 14, 0,
                                tzinfo=datetime.timezone.utc).timestamp())

# (timeframe, bar step seconds, seeded count) — each seed covers more than
# its AC-D57.4 span so the frame is span-narrower-than-loaded (T21 proves
# the span, T22 the clamp).
TIMEFRAME_SEEDS = [
    ("1 min", 60, 5000),
    ("5 mins", 300, 3000),
    ("15 mins", 900, 2500),
    ("30 mins", 1800, 2500),
    ("1 hour", 3600, 2500),
    ("4 hours", 14400, 1500),
    ("1 day", 86400, 500),
    ("1 week", 7 * 86400, 100),
    ("1 month", 30 * 86400, 90),
]


def _bars(symbol, timeframe, newest_ts, count, step):
    rows = []
    start = newest_ts - (count - 1) * step
    for i in range(count):
        price = 100.0 + i * 0.1
        rows.append(Bar(symbol=symbol, timeframe=timeframe,
                        ts=start + i * step,
                        open=price, high=price + 0.5,
                        low=price - 0.5, close=price + 0.1,
                        volume=1000.0))
    return rows


@pytest.fixture
def view(qapp):
    """An offscreen view with the bar transport captured (no page)."""
    chart = LV.LwcChartView()
    sent = []
    chart._bridge.send_ops = lambda ops: sent.append(list(ops))
    chart._bridge.send_channel = lambda channel, ops: None
    chart._captured_bar_ops = sent
    return chart


def _last_envelope(view):
    assert view._captured_bar_ops, "no bar envelope emitted"
    return view._captured_bar_ops[-1]


def _frame_op(envelope):
    frames = [op for op in envelope
              if op.get("op") == "set_visible_range"]
    assert len(frames) <= 1, f"expected at most one frame op, got {frames}"
    return frames[0] if frames else None


def _set_bars(envelope):
    return next(op for op in envelope if op["op"] == "set_bars")


def _fresh_load(view, symbol, timeframe, rows):
    """A different-symbol load / timeframe change per the S-P18-4 lifecycle."""
    view.set_symbol(symbol)
    view.set_timeframe(timeframe)
    view._captured_bar_ops.clear()
    view.update_bars(rows)
    return _last_envelope(view)


def _expected_range(view, rows):
    """The span-derived logical range for ``rows`` on the loaded view."""
    plotted = list(view._plotted)
    logical = list(view._logical)
    assert len(plotted) == len(rows)
    newest = max(int(b.ts) for b in plotted)
    oldest = min(int(b.ts) for b in plotted)
    cutoff = LV.fresh_frame_cutoff(view._timeframe, newest, oldest,
                                   view._ext_hours)
    assert cutoff is not None
    first = next(i for i, b in enumerate(plotted) if int(b.ts) >= cutoff)
    return cutoff, first, int(logical[first]), int(logical[-1])


@pytest.mark.parametrize("timeframe,step,count", TIMEFRAME_SEEDS,
                         ids=[t for t, _, _ in TIMEFRAME_SEEDS])
def test_P18_T2_T21_per_timeframe_fresh_frame_spans(view, timeframe,
                                                    step, count):
    """P18-T2-T21 (AC1): each timeframe opens on its AC-D57.4 span."""
    rows = _bars("AAA", timeframe, BASE_TS, count, step)
    envelope = _fresh_load(view, "AAA", timeframe, rows)
    frame = _frame_op(envelope)
    assert frame is not None, f"{timeframe}: fresh load must carry a frame"
    # New-symbol load: preserve path stays off, the page frames fresh.
    assert _set_bars(envelope)["same_symbol"] is False
    cutoff, first, from_slot, newest_slot = _expected_range(view, rows)
    assert frame["range"] == {"from": float(from_slot),
                              "to": float(newest_slot + 2)}
    assert frame["following"] is True
    # Span-narrower-than-loaded: the frame starts strictly inside the
    # loaded history (the span is shorter than what was loaded).
    assert first > 0, f"{timeframe}: seed must exceed the span"
    # Anchoring: intraday cutoffs are Nth-session starts through the
    # mode-aware calendar; daily+ cutoffs are calendar spans off newest.
    newest = max(int(b.ts) for b in rows)
    if timeframe in LV.FRESH_FRAME_INTRADAY_SESSIONS:
        sessions = LV.FRESH_FRAME_INTRADAY_SESSIONS[timeframe]
        lookback = (sessions + 40) * 86400
        starts = sorted(w["start_ts"] for w in session_windows(
            newest - lookback, newest, view._ext_hours))
        assert starts, f"{timeframe}: no session windows under the seed"
        expected = (starts[-sessions] if len(starts) >= sessions
                    else starts[0])
        assert cutoff == max(int(expected), min(int(b.ts) for b in rows))
    else:
        span_days = LV.FRESH_FRAME_DAILY_SPAN_DAYS[timeframe]
        assert cutoff == newest - span_days * 86400


def test_P18_T2_T22_clamped_frame_and_zero_bar_noop(view):
    """P18-T2-T22 (AC2): narrower-than-span clamps; zero bars is a no-op."""
    timeframe, step = "1 min", 60
    rows = _bars("AAA", timeframe, BASE_TS, 10, step)
    envelope = _fresh_load(view, "AAA", timeframe, rows)
    frame = _frame_op(envelope)
    assert frame is not None, "clamped load must still carry a frame"
    assert frame["range"] == {"from": 0.0,
                              "to": float(len(rows) - 1 + 2)}
    assert frame["following"] is True
    # The cutoff clamped to the oldest loaded bar: the frame covers all
    # loaded bars (no fetch change — framing reads loaded bars only).
    assert LV.fresh_frame_cutoff(timeframe, BASE_TS,
                                 BASE_TS - 9 * step,
                                 view._ext_hours) == BASE_TS - 9 * step
    # Zero-bar load: silent no-op through the existing empty-series path.
    view._captured_bar_ops.clear()
    view.update_bars([])
    envelope = _last_envelope(view)
    assert _frame_op(envelope) is None


def test_P18_T2_T23_switch_back_applies_fresh_frame_not_memory(view):
    """P18-T2-T23 (AC3): switch-back re-frames fresh (Q95 (b) over Q75)."""
    timeframe, step = "5 mins", 300
    rows_a = _bars("AAA", timeframe, BASE_TS, 3000, step)
    _fresh_load(view, "AAA", timeframe, rows_a)
    # Scroll back on A: the freshest throttled report wins (AR-P11-2).
    assert view.report_viewport({"from": 2.0, "to": 20.0},
                                following=False) is True
    rows_b = _bars("BBB", timeframe, BASE_TS, 3000, step)
    _fresh_load(view, "BBB", timeframe, rows_b)
    assert view.report_viewport({"from": 0.0, "to": 30.0},
                                following=True) is True
    # Switch back to A: the remembered *range* is never restored — the
    # load carries a fresh AC1 frame ending at the live edge...
    envelope = _fresh_load(view, "AAA", timeframe, rows_a)
    frame = _frame_op(envelope)
    assert frame is not None
    _, first, from_slot, newest_slot = _expected_range(view, rows_a)
    assert frame["range"] == {"from": float(from_slot),
                              "to": float(newest_slot + 2)}
    # ...with tracking (remembered-following honoured): the newest slot
    # sits inside the range and following derives honestly.
    assert frame["following"] is True
    assert frame["range"]["from"] <= newest_slot <= frame["range"]["to"]
    assert frame["range"] != {"from": 2.0, "to": 20.0}
    assert _set_bars(envelope)["same_symbol"] is False


def test_P18_T2_T24_timeframe_change_fresh_and_remembered_away(view):
    """P18-T2-T24 (AC3): timeframe change re-frames; away stays away."""
    step = 300
    rows = _bars("AAA", "5 mins", BASE_TS, 3000, step)
    _fresh_load(view, "AAA", "5 mins", rows)
    # Timeframe change on the same symbol: a fresh frame, never a
    # viewport preserve.
    view.set_timeframe("15 mins")
    view._captured_bar_ops.clear()
    view.update_bars(_bars("AAA", "15 mins", BASE_TS, 2500, 900))
    envelope = _last_envelope(view)
    frame = _frame_op(envelope)
    assert frame is not None, "timeframe change must re-frame fresh"
    assert _set_bars(envelope)["same_symbol"] is False
    # Remembered-away encodes honestly: the fresh frame back-shifts
    # minimally so the newest slot falls outside the range (AP-P18-3).
    assert view.report_viewport({"from": 5.0, "to": 50.0},
                                following=False) is True
    view.set_timeframe("5 mins")
    view._captured_bar_ops.clear()
    view.update_bars(rows)
    envelope = _last_envelope(view)
    frame = _frame_op(envelope)
    assert frame is not None
    assert frame["following"] is False
    newest_slot = int(view._logical[-1])
    assert frame["range"]["to"] == float(newest_slot - 1)
    assert not (frame["range"]["from"] <= newest_slot
                <= frame["range"]["to"])
    # Maximal recency: the frame still starts at the span cutoff (shifted
    # by exactly the one-slot minimal back-shift).
    _, first, from_slot, _ = _expected_range(view, rows)
    assert frame["range"]["from"] == float(max(0, from_slot - 1))


def test_P18_T2_T25_same_symbol_replace_preserves(view):
    """P18-T2-T25 (AC3): backfill waves + mode switches preserve (S-P11-3)."""
    timeframe, step = "1 day", 86400
    rows = _bars("AAA", timeframe, BASE_TS, 500, step)
    _fresh_load(view, "AAA", timeframe, rows)
    assert view.report_viewport({"from": 100.0, "to": 200.0},
                                following=False) is True
    # Backfill continuation wave: older bars prepended, same symbol.
    view._captured_bar_ops.clear()
    backfilled = (_bars("AAA", timeframe, BASE_TS - 20 * step, 20, step)
                  + rows)
    view.update_bars(backfilled)
    envelope = _last_envelope(view)
    assert _set_bars(envelope)["same_symbol"] is True
    assert _frame_op(envelope) is None
    assert view._pending_viewport == {
        "range": {"from": 100.0, "to": 200.0}, "following": False}
    # RTH/ETH mode switch: same bars, display mode only — still preserves.
    view._captured_bar_ops.clear()
    view.set_extended_hours(False)
    envelope = _last_envelope(view)
    assert _set_bars(envelope)["same_symbol"] is True
    assert _frame_op(envelope) is None


def test_P18_T2_T26_y_covers_framed_bars_no_explicit_y_op(view):
    """P18-T2-T26 (AC4): autoscale covers the framed window; no y op."""
    timeframe, step = "1 hour", 3600
    rows = _bars("AAA", timeframe, BASE_TS, 2500, step)
    envelope = _fresh_load(view, "AAA", timeframe, rows)
    frame = _frame_op(envelope)
    assert frame is not None
    from_slot = int(frame["range"]["from"])
    framed = [b for b, slot in zip(view._plotted, view._logical)
              if int(slot) >= from_slot]
    assert framed, "framed window must be non-empty"
    lo = min(float(b.low) for b in framed)
    hi = max(float(b.high) for b in framed)
    assert hi > lo
    # The frame sets the time axis only (library autoscales y, A163):
    # no emitted op carries a price/y range.
    for op in envelope:
        payload = json.dumps(op).lower()
        assert "autosc" not in payload
        for key in ("low", "high", "price_range", "y_range", "yfrom",
                    "yto", "visible_price"):
            assert key not in op, f"unexpected y op key {key}: {op}"


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
    fitContent() {
      if (_fakeChartState.count > 0) {
        _fakeScaleState.range = { from: 0, to: _fakeChartState.count - 1 };
      }
    },
    applyOptions() {},
  };
}
function _fakeSize(w, h) {
  return {
    clientWidth: w, clientHeight: h, _listeners: {},
    addEventListener(type, fn) { this._listeners[type] = fn; },
    getBoundingClientRect() { return { width: w, height: h, top: 0, left: 0 }; },
  };
}
const _fakeEl = _fakeSize(960, 850);
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
"""


def _run_node(flow: str) -> dict:
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
        % (proc.returncode, proc.stdout, proc.stderr))
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_P18_T2_T24b_page_holds_same_symbol_frame_while_away():
    """P18-T2-T24 (page half, S-P21-5): same-symbol + frame holds; fresh wins.

    Landing neutrality: the driver never emits same_symbol + frame (continuity
    stamping), so a same-symbol replace carrying a frame while away holds the
    away range with follow disengaged (consistent with T2 legD) instead of
    re-framing. A fresh (new-symbol) load carrying an explicit frame still
    frames: the frame wins over the preserved-range path.
    """
    flow = r"""
const BASE = 1700000000;
function seed(n) {
  const ts = [], open = [], high = [], low = [], close = [];
  for (let i = 0; i < n; i++) {
    ts.push(BASE + i * 300);
    open.push(100 + i * 0.1);
    high.push(100 + i * 0.1 + 0.25);
    low.push(100 + i * 0.1 - 0.25);
    close.push(100 + i * 0.1 + 0.05);
  }
  const res = page.lwApplyOps({ v: 1, ops: [
    { op: "set_bars", series: "candles", cols: { ts, open, high, low, close } },
  ]});
  assert.equal(res.error, null);
}
// A scrolled-back viewport, then a same-symbol replace carrying an
// explicit fresh frame: S-P21-5 landing neutrality — the away range
// holds with follow disengaged instead of re-framing.
seed(40);
page.lwApplyOps({ v: 1, ops: [
  { op: "set_visible_range", range: { from: 2, to: 20 }, following: false },
]});
const before = page.lwVisibleRange();
assert.deepEqual([before.range.from, before.range.to], [2, 20]);
{
  const ts = [], open = [], high = [], low = [], close = [];
  for (let i = 0; i < 40; i++) {
    ts.push(BASE + i * 300);
    open.push(100 + i * 0.1);
    high.push(100 + i * 0.1 + 0.25);
    low.push(100 + i * 0.1 - 0.25);
    close.push(100 + i * 0.1 + 0.05);
  }
  const res = page.lwApplyOps({ v: 1, ops: [
    { op: "set_bars", series: "candles", same_symbol: true,
      cols: { ts, open, high, low, close } },
    { op: "set_visible_range", range: { from: 30, to: 41 }, following: true },
  ]});
  assert.equal(res.error, null);
}
const held = page.lwVisibleRange();
assert.deepEqual([held.range.from, held.range.to], [2, 20]);
assert.equal(page.lwIsFollowing(), false);
// A fresh (new-symbol) load carrying an explicit frame still frames:
// the frame wins over the preserved-range path.
{
  const ts = [], open = [], high = [], low = [], close = [];
  for (let i = 0; i < 40; i++) {
    ts.push(BASE + i * 300);
    open.push(100 + i * 0.1);
    high.push(100 + i * 0.1 + 0.25);
    low.push(100 + i * 0.1 - 0.25);
    close.push(100 + i * 0.1 + 0.05);
  }
  const res = page.lwApplyOps({ v: 1, ops: [
    { op: "set_bars", series: "candles",
      cols: { ts, open, high, low, close } },
    { op: "set_visible_range", range: { from: 30, to: 41 }, following: true },
  ]});
  assert.equal(res.error, null);
}
const framed = page.lwVisibleRange();
assert.deepEqual([framed.range.from, framed.range.to], [30, 41]);
console.log(JSON.stringify({ ok: true }));
"""
    assert _run_node(flow) == {"ok": True}
