"""P25-T4: D69 + D70 — the bridge contract after S-P25-5 / S-P25-6.

D69 (S-P25-5): every staged op carries a monotonic arrival sequence and
``flush`` emits one arrival-ordered stream: per series only the last full
replace (``set_bars`` / ``set_volume`` / ``clear``) survives and that
series' older ops are dropped; the non-series directives
(``set_visible_range``, ``set_partial``) still ride after the rows.
``_op_log`` / ``replay_log`` keep every accepted op in plain arrival order.

D70 (S-P25-6): a whitespace row (a placeholder whose value slots are
``None``) is not a bar in either branch on either side — Python's
``apply_ops_to_bars`` skips it on a replace and removes its time on an
upsert; the page's real ``mergeRows`` / ``lwSnapshot()`` agree, and the
library sees a ``{time}`` placeholder only.

The parity case shells out to ``node`` and drives the *real* page glue
(``chart_assets/lwc/chart.js`` + ``envelope.js``) through ``lwApplyOps`` and
``window.lwSnapshot()`` — never a hand-written JS mirror (AR-P25-7).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

from ui.lwc_bridge import (
    LwBridge,
    apply_ops_to_bars,
    candle_update_op,
    candles_set_op,
    volume_set_op,
)

REPO = Path(__file__).resolve().parent.parent
LWC_DIR = REPO / "chart_assets" / "lwc"

BASE = 1_700_000_000
STEP = 300
T0 = BASE
T1 = BASE + STEP
T2 = BASE + 2 * STEP


# ── fixtures ───────────────────────────────────────────────────────────────


def _bar(ts, o=100.0, h=101.0, lo=99.0, c=100.5, volume=10.0):
    return SimpleNamespace(ts=ts, open=o, high=h, low=lo, close=c,
                           volume=volume)


def _whitespace(ts):
    """The Q-20 placeholder row: value slots ``None``, the time real."""
    return SimpleNamespace(ts=ts, open=None, high=None, low=None,
                           close=None, volume=None)


def _candle_row(bar):
    return (bar.ts, bar.open, bar.high, bar.low, bar.close)


def _bridge():
    """A headless bridge: no Qt event loop, explicit ``flush`` only."""
    b = LwBridge()
    b.set_ready(True)
    return b


def _three_bars():
    return [_bar(T0, 100.0, 101.0, 99.0, 100.5),
            _bar(T1, 101.0, 102.0, 100.0, 101.5),
            _bar(T2, 102.0, 103.0, 101.0, 102.5)]


def _frame():
    return {"op": "set_visible_range", "range": {"from": 0, "to": 2}}


def _marker(ts, partial=True):
    return {"op": "set_partial", "ts": ts, "partial": partial}


# ── AC1: arrival order and the supersession rule, both orders ─────────────


def test_ac1_update_staged_before_replace_is_superseded():
    """update_bar(then) a set_bars replace: no stale op, only the rows."""
    b = _bridge()
    bars = _three_bars()
    stale = candle_update_op(_bar(BASE + 50, c=999.0))
    replace = candles_set_op(bars)
    b.send_ops([stale])
    b.send_ops([replace, _frame(), _marker(bars[-1].ts)])

    env = b.flush()
    assert env is not None
    assert [op["op"] for op in env["ops"]] == [
        "set_bars", "set_visible_range", "set_partial",
    ], "the rows first, the directives after"
    assert not any(op["op"] == "update_bar" for op in env["ops"]), (
        "no op for that series older than its full replace may cross")
    assert env["ops"][0] is replace
    assert apply_ops_to_bars(env["ops"]) == [_candle_row(x) for x in bars]


def test_ac1_replace_staged_before_update_applies_last():
    """set_bars then update_bar: the update is the last data op and wins."""
    b = _bridge()
    bars = _three_bars()
    b.send_ops([candles_set_op(bars)])
    tick = _bar(bars[-1].ts, 102.0, 104.0, 101.0, 103.5)
    b.send_ops([candle_update_op(tick), _frame()])

    env = b.flush()
    assert env is not None
    assert [op["op"] for op in env["ops"]] == [
        "set_bars", "update_bar", "set_visible_range",
    ]
    assert len(env["ops"]) == 3, "every surviving op crosses exactly once"
    expected = [_candle_row(x) for x in bars]
    expected[-1] = _candle_row(tick)
    assert apply_ops_to_bars(env["ops"]) == expected


# ── AC2: several series, one replace per series, full-fidelity log ────────


def test_ac2_one_replace_per_series_and_arrival_order_survive():
    b = _bridge()
    bars = _three_bars()

    u0 = candle_update_op(_bar(T0, c=11.0))
    u1 = candle_update_op(_bar(T1, c=12.0))
    u2 = candle_update_op(_bar(T2, c=13.0))
    first_replace = candles_set_op(bars)
    vol_replace = volume_set_op(bars)
    later_rows = [_bar(T0 + 10 * STEP, 200.0, 201.0, 199.0, 200.5),
                  _bar(T1 + 10 * STEP, 201.0, 202.0, 200.0, 201.5)]
    later_replace = candles_set_op(later_rows)
    after_replace_u2 = candle_update_op(
        _bar(T2 + 10 * STEP, 201.0, 203.0, 200.0, 202.5))
    frame = _frame()

    arrival = [u0, u1, u2, first_replace, vol_replace, later_replace,
               after_replace_u2, frame]
    b.send_ops(arrival)

    env = b.flush()
    assert env is not None
    # Data ops in ascending arrival order; directives appended after.
    assert env["ops"][0] is vol_replace
    assert env["ops"][1] is later_replace
    assert env["ops"][2] is after_replace_u2
    assert env["ops"][3] is frame
    assert len(env["ops"]) == 4, "survivors appear exactly once"
    assert all(op is not first_replace for op in env["ops"]), (
        "the older replace is dropped")
    for dropped in (u0, u1, u2):
        assert all(op is not dropped for op in env["ops"]), (
            "an update older than the series' last replace is dropped")
    # Per-series arrival order: the surviving candles ops are the replace
    # then the update that arrived after it.
    candle_ops = [op for op in env["ops"] if op.get("series") == "candles"]
    assert [op["op"] for op in candle_ops] == ["set_bars", "update_bar"]
    assert apply_ops_to_bars(env["ops"])[-1] == (
        T2 + 10 * STEP, 201.0, 203.0, 200.0, 202.5)

    # The log keeps every accepted op, in arrival order, with no new keys.
    log = b.replay_log()
    assert log == arrival, "replay keeps plain arrival order and full fidelity"
    assert [op["op"] for op in log] == [op["op"] for op in arrival]
    assert b.counters()["received"] == len(arrival)
    for original, logged in zip(arrival, log):
        assert set(logged) == set(original), "no key is added on the log"
    assert log[3]["op"] == "set_bars" and log[3]["cols"] == first_replace["cols"]


def test_ac2_two_replaces_of_one_series_keep_only_the_later():
    b = _bridge()
    old = _bar(T0, 1.0, 2.0, 0.5, 1.5)
    new = _bar(T1, 2.0, 3.0, 1.5, 2.5)
    first = candles_set_op([old])
    second = candles_set_op([new])
    b.send_ops([first, second])
    env = b.flush()
    assert env is not None
    assert len(env["ops"]) == 1
    assert env["ops"][0] is second, "the older replace is dropped, not both"
    assert apply_ops_to_bars(env["ops"]) == [_candle_row(new)]


# ── AC3: one whitespace rule, both reconstruction branches ────────────────


def test_ac3_whitespace_update_removes_and_set_bars_skips():
    bars = _three_bars()
    expected = [_candle_row(bars[0]), _candle_row(bars[2])]

    via_update = [
        candles_set_op(bars),
        candle_update_op(_whitespace(T1)),
    ]
    via_replace = [candles_set_op([bars[0], _whitespace(T1), bars[2]])]

    assert apply_ops_to_bars(via_update) == expected, (
        "an update naming a None-close row removes the existing bar")
    assert apply_ops_to_bars(via_replace) == expected, (
        "a None-close row inside set_bars is never written")
    assert apply_ops_to_bars(via_update) == apply_ops_to_bars(via_replace)


def test_ac3_whitespace_update_for_an_absent_time_writes_nothing():
    bars = _three_bars()
    ops = [candles_set_op(bars), candle_update_op(_whitespace(T2 + STEP))]
    assert apply_ops_to_bars(ops) == [_candle_row(x) for x in bars]


# ── AC5: edge legs ────────────────────────────────────────────────────────


def test_ac5_clear_then_update_yields_one_bar():
    b = _bridge()
    tick = _bar(T0, 50.0, 55.0, 49.0, 54.0)
    b.send_ops([{"op": "clear", "series": "candles"},
                candle_update_op(tick)])
    env = b.flush()
    assert env is not None
    assert [op["op"] for op in env["ops"]] == ["clear", "update_bar"]
    assert apply_ops_to_bars(env["ops"]) == [_candle_row(tick)]


def test_ac5_update_before_a_replace_that_removes_its_time_is_dropped():
    b = _bridge()
    removed = T1
    b.send_ops([candle_update_op(_bar(removed, 700.0, 701.0, 699.0, 700.5))])
    replacement = [_bar(T0, 100.0, 101.0, 99.0, 100.5),
                   _bar(T2, 102.0, 103.0, 101.0, 102.5)]
    replace = candles_set_op(replacement)
    b.send_ops([replace])

    env = b.flush()
    assert env is not None
    assert len(env["ops"]) == 1 and env["ops"][0] is replace
    rows = apply_ops_to_bars(env["ops"])
    assert [r[0] for r in rows] == [T0, T2], "the removed bar does not come back"


def test_ac5_update_after_the_replace_applies_as_the_last_data_op():
    b = _bridge()
    replacement = [_bar(T0, 100.0, 101.0, 99.0, 100.5),
                   _bar(T2, 102.0, 103.0, 101.0, 102.5)]
    b.send_ops([candles_set_op(replacement)])
    later = _bar(T2, 102.0, 104.0, 101.0, 103.5)
    b.send_ops([candle_update_op(later), _marker(T2)])

    env = b.flush()
    assert env is not None
    assert [op["op"] for op in env["ops"]] == [
        "set_bars", "update_bar", "set_partial",
    ]
    rows = apply_ops_to_bars(env["ops"])
    assert [r[0] for r in rows] == [T0, T2]
    assert rows[-1] == _candle_row(later)


def test_ac5_empty_flush_returns_none_and_emits_nothing():
    b = LwBridge()
    b.set_ready(True)
    seen = []
    b.opsEmitted.connect(seen.append)
    b.opsJson.connect(seen.append)
    assert b.flush() is None
    assert seen == []
    assert b.counters()["emissions"] == 0


# ── AC4: parity through the page's real lwApplyOps + lwSnapshot() ─────────

#: A self-contained node harness: the REAL page glue against a stubbed
#: document and the fake LightweightCharts 5.x tree (the same minimum the
#: repo's node suites use). It records every row the page hands the library
#: so the `{time}`-placeholder property is observable.
_NODE_HARNESS = r"""
const DIR = %DIR%;
const _fakeScaleState = { range: null };
const _fakeChartState = { count: 0 };
const _libRows = [];
function _record(series, row) {
  if (row && typeof row === "object") {
    _libRows.push({ series: series, row: JSON.parse(JSON.stringify(row)) });
  }
}
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
    applyOptions() {},
    options() { return {}; },
  };
}
function _fakeSeries(name) {
  return {
    _rows: [],
    setData(rows) {
      this._rows = rows;
      for (let i = 0; i < rows.length; i++) _record(name, rows[i]);
      if (name === "candles") {
        _fakeChartState.count = rows.length;
        _fakeScaleState.range = { from: 0, to: Math.max(rows.length - 1, 0) };
      }
    },
    update(row) {
      _record(name, row);
      const last = this._rows.length
        ? this._rows[this._rows.length - 1].time : null;
      if (row && (last === null || row.time > last)) {
        this._rows.push(row);
        if (name === "candles") _fakeChartState.count = this._rows.length;
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
      const lib = globalThis.LightweightCharts;
      if (ctor === lib.CandlestickSeries) return _fakeSeries("candles");
      if (ctor === lib.HistogramSeries) return _fakeSeries("volume");
      if (ctor === lib.LineSeries) return _fakeSeries("line");
      if (ctor === lib.AreaSeries) return _fakeSeries("area");
      return _fakeSeries("series");
    },
    addCandlestickSeries() { return _fakeSeries("candles"); },
    addLineSeries() { return _fakeSeries("line"); },
    addAreaSeries() { return _fakeSeries("area"); },
    addHistogramSeries() { return _fakeSeries("volume"); },
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
globalThis.window.setTimeout = function (fn, ms) { return setTimeout(fn, ms); };
globalThis.window.clearTimeout = function (h) { return clearTimeout(h); };
for (const name of ["LwInteraction", "LwAlarms", "LwPrimitives",
  "LwOverlays", "LwStudies", "LwGestures"]) {
  globalThis.window[name] = { bind() {} };
}
globalThis.window.LwEnvelope = require(DIR + "/envelope.js");
require(DIR + "/chart.js");
const page = globalThis.window;
const fixtures = JSON.parse(process.env.P25_FIXTURES);
const snapshots = {};
const libRows = {};
for (const name of Object.keys(fixtures)) {
  _libRows.length = 0;
  const res = page.lwApplyOps({ v: 1, ops: fixtures[name] });
  if (res.error) {
    process.stderr.write("lwApplyOps rejected " + name + ": " + res.error);
    process.exit(3);
  }
  snapshots[name] = page.lwSnapshot();
  libRows[name] = _libRows.slice();
}
process.stdout.write(JSON.stringify({ snapshots: snapshots, libRows: libRows }));
"""


def _run_node(fixtures: dict) -> dict:
    program = _NODE_HARNESS.replace("%DIR%", json.dumps(str(LWC_DIR)))
    node = shutil.which("node") or "node"
    proc = subprocess.run(
        [node, "-e", program],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(REPO),
        env={**os.environ, "P25_FIXTURES": json.dumps(fixtures)},
    )
    assert proc.returncode == 0, (
        "node harness failed (exit %d):\nSTDOUT:\n%s\nSTDERR:\n%s"
        % (proc.returncode, proc.stdout, proc.stderr))
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    assert lines, "node harness printed nothing"
    return json.loads(lines[-1])


def _rows_as_page_dicts(rows):
    return [
        {"time": ts, "open": o, "high": h, "low": lo, "close": c}
        for (ts, o, h, lo, c) in rows
    ]


def test_ac4_page_parity_for_whitespace_update_and_replace():
    bars = _three_bars()
    fixtures = {
        # The same whitespace ts delivered once through update_bar...
        "upsert": [
            candles_set_op(bars),
            candle_update_op(_whitespace(T1)),
        ],
        # ...and once as a row inside set_bars.
        "replace": [candles_set_op([bars[0], _whitespace(T1), bars[2]])],
    }
    payload = _run_node(fixtures)
    snapshots = payload["snapshots"]

    for name in ("upsert", "replace"):
        expected = _rows_as_page_dicts(apply_ops_to_bars(fixtures[name]))
        assert snapshots[name]["candles"] == expected, (
            "the page's bar series equals the Python reconstruction "
            "element-for-element for the %s fixture" % name)
        assert T1 not in [r["time"] for r in snapshots[name]["candles"]], (
            "the whitespace timestamp is absent from the page's candles")

    # A whitespace row reaches the library as `{time}` only — never a
    # null-valued point, and never painted as a candle.
    lib_rows = payload["libRows"]
    for name in ("upsert", "replace"):
        entries = lib_rows[name]
        for entry in entries:
            assert not any(v is None for v in entry["row"].values()), (
                "the library was handed a null-valued point: %r" % (entry,))
        t1_writes = [
            entry for entry in entries
            if entry["series"] == "candles" and entry["row"]["time"] == T1
        ]
        assert t1_writes, (
            "the whitespace time must be represented at the library (%s)" % name)
        assert set(t1_writes[-1]["row"].keys()) == {"time"}, (
            "the whitespace row is a {time} placeholder only (%s): %r"
            % (name, t1_writes[-1]["row"]))
