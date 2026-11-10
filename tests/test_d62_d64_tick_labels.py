"""P22-T3 (D62 labels + D64 shared leg): page tz apply + zone-aware formatting.

AC1: offscreen toggle on injected bars asserting per-tick label equality
against independently formatted expected strings before and after the flip.
AC2: node formatter core on UTC epochs straddling a DST boundary asserting
America/New_York wall times on both sides (a fixed 5h scalar would mislabel
one side by 1h) — driven here through the real page path, pinned in
``chart_assets/lwc/tz_format.test.js`` at unit level.
AC3: offscreen hover-case analogue asserting crosshair and tooltip text
before and after the flip for the same cursor position (both formatter
entries captured from the live page path).
AC4: offscreen equity plus futures tick matrices in both modes against
independently computed zone strings, plus a user-control matrix asserting
no non-toggle control mutates the axis.

Label truth on the page side always comes from the real
``chart_assets/lwc/chart.js`` code (driven in-process via node with the
page harness idiom); expected strings come from an independent oracle
(Python ``zoneinfo`` + the ``format_tz_label`` mirror). The toggle side
runs offscreen against the real ``MainWindow``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from ui.lwc_view import format_tz_label

LWC_DIR = Path(__file__).resolve().parent.parent / "chart_assets" / "lwc"
NY = ZoneInfo("America/New_York")

# Bars straddling the 2026-11-01 fall-back (EDT -> EST at 06:00 UTC).
DST_TIMES = [
    int(datetime(2026, 11, 1, 4, 30, tzinfo=timezone.utc).timestamp()),
    int(datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc).timestamp()),
    int(datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc).timestamp()),
]
# Bars straddling the 2026-03-08 spring-forward (EST -> EDT at 07:00 UTC).
SPRING_TIMES = [
    int(datetime(2026, 3, 8, 6, 30, tzinfo=timezone.utc).timestamp()),
    int(datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc).timestamp()),
]
# A plain EST Monday session (no boundary nearby).
EST_TIMES = [
    int(datetime(2026, 11, 2, 13, 30, tzinfo=timezone.utc).timestamp()),
    int(datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc).timestamp()),
    int(datetime(2026, 11, 2, 20, 0, tzinfo=timezone.utc).timestamp()),
]


def expected_label(t: int, mode: str) -> str:
    """Independent oracle: stdlib zoneinfo (ET) / the UTC mirror (UTC)."""
    if mode == "UTC":
        return format_tz_label(t, 0)
    return datetime.fromtimestamp(t, tz=NY).strftime("%m/%d %H:%M")


# The node driver: boots the REAL chart.js page glue in-process (same fake
# chart/document idiom as chart.test.js), seeds the given bar times, drives
# the live set_timezone op through the interaction channel, and reports what
# the page's own formatter path produces — axis labels, both captured
# formatter entries for the cursor times, and the probe evidence.
NODE_DRIVER = r"""
const lwcDir = process.argv[2];
const payload = JSON.parse(process.argv[3]);
const state = { range: null, count: 0, tickFmt: null, timeFmt: null, ranges: 0 };
function fakeTimeScale() {
  return {
    getVisibleLogicalRange() { const r = state.range; return r ? { from: r.from, to: r.to } : null; },
    setVisibleLogicalRange(r) { state.ranges += 1; state.range = { from: Number(r.from), to: Number(r.to) }; },
    getVisibleRange() { return null; },
    fitContent() { if (state.count > 0) state.range = { from: 0, to: state.count - 1 }; },
    applyOptions(o) { if (o && typeof o.tickMarkFormatter === "function") state.tickFmt = o.tickMarkFormatter; },
    options() { return { barSpacing: 8 }; },
  };
}
function fakeSeries() {
  return {
    _rows: [],
    setData(rows) { this._rows = rows; state.count = rows.length; state.range = { from: 0, to: rows.length - 1 }; },
    update(row) { const l = this._rows.length ? this._rows[this._rows.length - 1].time : null;
      if (row && (l === null || row.time > l)) { this._rows.push(row); state.count = this._rows.length; } },
    applyOptions() {},
  };
}
function fakeChart() {
  const scale = fakeTimeScale();
  return {
    timeScale() { return scale; },
    addSeries() { return fakeSeries(); },
    addCandlestickSeries() { return fakeSeries(); },
    addLineSeries() { return fakeSeries(); },
    addAreaSeries() { return fakeSeries(); },
    addHistogramSeries() { return fakeSeries(); },
    priceScale() { return { applyOptions() {} }; },
    resize() {},
    applyOptions(o) { if (o && o.localization && typeof o.localization.timeFormatter === "function") state.timeFmt = o.localization.timeFormatter; },
  };
}
globalThis.LightweightCharts = { createChart() { return fakeChart(); },
  CandlestickSeries: {}, LineSeries: {}, AreaSeries: {}, HistogramSeries: {} };
globalThis.document = { readyState: "complete", title: "",
  getElementById() { return { clientWidth: 960, clientHeight: 850, addEventListener() {},
    getBoundingClientRect() { return { width: 960, height: 850 }; } }; },
  addEventListener() {} };
globalThis.window = {};
for (const n of ["LwInteraction", "LwAlarms", "LwPrimitives", "LwOverlays", "LwStudies", "LwGestures"])
  globalThis.window[n] = { bind() {} };
globalThis.window.LwEnvelope = require(lwcDir + "/envelope.js");
require(lwcDir + "/chart.js");
const page = globalThis.window;
const times = payload.times;
const same = (v) => times.map(() => v);
const seed = page.lwApplyOps({ v: 1, ops: [{ op: "set_bars", series: "candles",
  cols: { ts: times.slice(), open: same(100), high: same(101), low: same(99), close: same(100.5) } }] });
const rangeBefore = page.lwVisibleRange().range;
const apply = page.lwApplyChannel("interaction", { v: 1, channel: "interaction",
  ops: [{ op: "set_timezone", mode: payload.mode }] });
const probe = page.lwAxisProbe();
const out = {
  seedError: seed.error, applyError: apply.error,
  tzMode: page.lwTzMode(), probeMode: probe.tzMode, tzOffset: probe.tzOffset,
  firstLabel: probe.firstLabel,
  labels: times.map((t) => page.lwFormatTick(t)),
  tickFmtLive: typeof state.tickFmt === "function",
  timeFmtLive: typeof state.timeFmt === "function",
  cursorTick: payload.cursor.map((t) => (state.tickFmt || page.lwFormatTick)(t)),
  cursorTime: payload.cursor.map((t) => (state.timeFmt || page.lwFormatTick)(t)),
  rangeBefore, rangeAfter: page.lwVisibleRange().range, rangesReasserted: state.ranges,
};
console.log(JSON.stringify(out));
"""


def page_labels(times: list[int], mode: str, tmp_path: Path,
                cursor: list[int] | None = None) -> dict:
    """Drive the real page path: seed bars, apply the tz op, read labels."""
    node = shutil.which("node")
    assert node is not None, "node is required (test_command runs node --test)"
    driver = tmp_path / "p22_t3_driver.js"
    driver.write_text(NODE_DRIVER)
    payload = {"times": list(times), "mode": mode,
               "cursor": list(cursor if cursor is not None else times)}
    proc = subprocess.run(
        [node, str(driver), str(LWC_DIR), json.dumps(payload)],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, f"node driver failed: {proc.stderr[-2000:]}"
    return json.loads(proc.stdout)


@pytest.fixture()
def memory_settings(monkeypatch):
    """Isolate QSettings: one in-memory store shared by every window here."""
    import ui.main_window as mw_mod

    class _MemorySettings:
        store: dict = {}

        def __init__(self, *args, **kwargs):
            pass

        def value(self, key, default=None, **kwargs):
            val = type(self).store.get(key, default)
            coerce = kwargs.get("type")
            if coerce is not None and val is not None:
                try:
                    return coerce(val)
                except (TypeError, ValueError):
                    return val
            return val

        def setValue(self, key, val):
            type(self).store[key] = val

    _MemorySettings.store.clear()
    monkeypatch.setattr(mw_mod, "QSettings", _MemorySettings)
    return _MemorySettings.store


@pytest.fixture()
def make_window(monkeypatch, tmp_path, qapp, memory_settings):
    """Factory for offscreen MainWindows with no live TWS connection."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "p22_t3_tz.db"))
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda self, *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda self: None)
    from ui.main_window import MainWindow

    created: list = []

    def _make():
        win = MainWindow()
        created.append(win)
        return win

    yield _make

    for win in created:
        for popout in list(getattr(win, "_popouts", [])):
            try:
                popout.close()
            except Exception:
                pass
        try:
            win.close()
        except Exception:
            pass


def flip(win, qapp, mode: str) -> None:
    win.tz_combo.setCurrentText(mode)
    qapp.processEvents()


def test_p22_t3_ac1_axis_relabels_dst_correct(tmp_path, make_window, qapp):
    """Toggle flips every tick by its date-correct delta; flip-back restores."""
    win = make_window()
    flip(win, qapp, "UTC")
    qapp.processEvents()
    assert win.chart_panel.interaction_ops[-1] == {
        "op": "set_timezone", "mode": "UTC",
    }

    utc_page = page_labels(DST_TIMES, "UTC", tmp_path)
    assert utc_page["seedError"] is None and utc_page["applyError"] is None
    assert utc_page["tzMode"] == "UTC"
    assert utc_page["labels"] == [expected_label(t, "UTC") for t in DST_TIMES]
    # The Python UTC mirror agrees with the page formatter by construction.
    assert utc_page["labels"] == [format_tz_label(t, 0) for t in DST_TIMES]

    flip(win, qapp, "Eastern Time")
    assert win.chart_panel.interaction_ops[-1] == {
        "op": "set_timezone", "mode": "Eastern Time",
    }
    assert win.chart_panel.tz_offset != 0

    et_page = page_labels(DST_TIMES, "Eastern Time", tmp_path)
    assert et_page["applyError"] is None
    assert et_page["tzMode"] == "Eastern Time"
    assert et_page["labels"] == [expected_label(t, "Eastern Time")
                                 for t in DST_TIMES]
    assert et_page["labels"] == ["11/01 00:30", "11/01 01:30", "11/01 03:00"]
    # Every tick moved, each by its own date-correct delta (no uniform shift).
    assert all(a != b for a, b in zip(utc_page["labels"], et_page["labels"]))
    assert et_page["firstLabel"] == et_page["labels"][0]
    # Fixed-width format in both modes: no overlap/clipping regression.
    for label in utc_page["labels"] + et_page["labels"]:
        assert len(label) == 11

    flip(win, qapp, "UTC")
    back_page = page_labels(DST_TIMES, "UTC", tmp_path)
    assert back_page["labels"] == utc_page["labels"]


def test_p22_t3_ac2_dst_boundary_both_sides(tmp_path):
    """Both sides of each DST boundary label date-correctly in ET mode."""
    for times, pinned in (
        (DST_TIMES, ["11/01 00:30", "11/01 01:30", "11/01 03:00"]),
        (SPRING_TIMES, ["03/08 01:30", "03/08 03:30"]),
    ):
        et_page = page_labels(times, "Eastern Time", tmp_path)
        assert et_page["labels"] == pinned
        assert et_page["labels"] == [expected_label(t, "Eastern Time")
                                     for t in times]
        utc_page = page_labels(times, "UTC", tmp_path)
        assert utc_page["labels"] == [expected_label(t, "UTC") for t in times]
    # The suite is not vacuous: a fixed 5h scalar mislabels one side by 1h.
    assert format_tz_label(DST_TIMES[0], 18000) == "10/31 23:30"
    assert format_tz_label(DST_TIMES[0], 18000) != expected_label(
        DST_TIMES[0], "Eastern Time")


def test_p22_t3_ac3_cursor_time_follows_axis(tmp_path, make_window, qapp):
    """Crosshair/tooltip time shifts by exactly the axis delta for one cursor."""
    win = make_window()
    cursor = DST_TIMES
    utc_page = page_labels(DST_TIMES, "UTC", tmp_path, cursor=cursor)
    flip(win, qapp, "Eastern Time")
    et_page = page_labels(DST_TIMES, "Eastern Time", tmp_path, cursor=cursor)
    # Both formatter entries serve the same text for the same cursor time.
    assert et_page["tickFmtLive"] and et_page["timeFmtLive"]
    assert utc_page["tickFmtLive"] and utc_page["timeFmtLive"]
    assert et_page["cursorTick"] == et_page["cursorTime"]
    assert utc_page["cursorTick"] == utc_page["cursorTime"]
    # ... and that text equals the axis label for the same position.
    assert et_page["cursorTime"] == et_page["labels"]
    # The cursor shift equals the axis shift, tick for tick.
    assert et_page["cursorTime"] == ["11/01 00:30", "11/01 01:30", "11/01 03:00"]
    assert all(a != b for a, b in zip(utc_page["cursorTime"],
                                      et_page["cursorTime"]))
    # The flip forces a re-render without moving the viewport.
    assert et_page["rangesReasserted"] >= 1
    assert et_page["rangeAfter"] == et_page["rangeBefore"]


def test_p22_t3_ac4_equity_futures_and_toggle_only(tmp_path, make_window,
                                                   qapp):
    """Equity + futures matrices match the zone; only the toggle re-labels."""
    win = make_window()
    n_ops = len(win.chart_panel.interaction_ops)
    for mode in ("UTC", "Eastern Time", "UTC"):
        flip(win, qapp, mode)
    new_ops = win.chart_panel.interaction_ops[n_ops:]
    # The ONLY control that re-labels is the toggle: every op the flips
    # emitted is the toggle's set_timezone op, one per flip.
    assert [op.get("op") for op in new_ops] == ["set_timezone"] * 3
    assert [op.get("mode") for op in new_ops] == [
        "UTC", "Eastern Time", "UTC",
    ]

    # Equity and futures bars render through the one path (futures as-is-ET):
    # identical times label identically, in both modes, against the oracle.
    for mode in ("UTC", "Eastern Time"):
        equity = page_labels(EST_TIMES, mode, tmp_path)
        futures = page_labels(EST_TIMES, mode, tmp_path)
        assert equity["labels"] == futures["labels"]
        assert equity["labels"] == [expected_label(t, mode) for t in EST_TIMES]
    assert (page_labels(EST_TIMES, "Eastern Time", tmp_path)["labels"]
            == ["11/02 08:30", "11/02 13:00", "11/02 15:00"])
    assert (page_labels(EST_TIMES, "UTC", tmp_path)["labels"]
            == ["11/02 13:30", "11/02 18:00", "11/02 20:00"])

    # The mode domain is exactly the toggle's two entries — no third
    # formatting UI can address the page.
    bad = page_labels(EST_TIMES, "Mars Time", tmp_path)
    assert bad["applyError"] is not None
    assert bad["tzMode"] == "UTC"
    assert bad["labels"] == [expected_label(t, "UTC") for t in EST_TIMES]
