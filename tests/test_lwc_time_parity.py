"""tests/test_lwc_time_parity.py — P6-T05 Phase 3 core chart (L*).

Time-parity cases on the Q60 record (DST fold + session-boundary fixtures
render identical logical-index series on both engines, whitespace runs
match ``gap_is_non_trading``, tz labels equal ``t - offset`` per mode,
live ``series.update`` advances the forming bar); the rendered-geometry
guard (gap >= 0; positive whenever ``barSpacing`` allows) plus the Q60
record assertion (retirement note present in matrix + result); and the
residue scan over the renderer-only boundary.

QApplication usage: only the live-driver cases instantiate the view (a
QWidget); they take the repo's session-scoped ``qapp`` fixture so the
application cannot be garbage-collected mid-suite (the bare-``QApplication``
helper that was collected immediately aborted the process at the next
``QWidget`` construction). Everything else is pure Qt-free mapping covered
offscreen.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from services import chart_model
from services.time_collapse_service import gap_is_non_trading
from ui import lwc_view as LV
from ui import lwc_bridge as LB

REPO = Path(__file__).resolve().parent.parent
LWC_DIR = REPO / "chart_assets" / "lwc"
MATRIX = REPO / "docs" / "lwc_parity_matrix.md"

EST = 18000
EDT = 14400

SYMBOL = "LWC-PARITY"
TF = "5 mins"
PERIOD = TIMEFRAME_SECONDS[TF]


def _bar(ts, o=100.0, h=101.0, low=99.0, c=100.5, v=1000.0):
    return Bar(symbol=SYMBOL, timeframe=TF, ts=ts, open=o, high=h,
              low=low, close=c, volume=v)


def _utc(y, mo, d, hh, mm):
    return int(datetime(y, mo, d, hh, mm, tzinfo=timezone.utc).timestamp())


def _friday_monday_rth():
    """Friday 2026-09-25 RTH tail + Monday 2026-09-28 RTH open (EDT).

    RTH 09:30-16:00 ET == 13:30-20:00 UTC in September (EDT, offset 14400).
    """
    fri = [_utc(2026, 9, 25, 19, 30) + i * 300 for i in range(6)]
    mon = [_utc(2026, 9, 28, 13, 30) + i * 300 for i in range(6)]
    return [_bar(ts) for ts in fri + mon]


def _monday_with_hole():
    """Monday RTH with a 3-bar midday hole (13:45-13:55 UTC missing)."""
    have = [0, 1, 2, 6, 7, 8]  # 5-min slots from the 13:30 UTC open
    base = _utc(2026, 9, 28, 13, 30)
    return [_bar(base + i * 300) for i in have]


def _dst_fold_sunday():
    """5-min bars across the 2026-11-01 ET fall-back (06:00 UTC).

    Sunday — no session either side — so the fold collapses exactly
    like the weekend around it; the assertion is continuity, not loss.
    """
    base = _utc(2026, 11, 1, 5, 30)
    return [_bar(base + i * 300) for i in range(9)]  # 05:30-07:30 UTC


def _default_engine_steps(bars, timeframe, ext_hours):
    """Reference steps from the default engine's shared value source."""
    plotted = [bars[i] for i in chart_model.plotted_index_rows(
        bars, timeframe, ext_hours)]
    cmap = chart_model.collapse_for_bars(plotted, timeframe, ext_hours)
    period = TIMEFRAME_SECONDS[timeframe]
    dx = [cmap.to_display(b.ts) for b in plotted]
    return plotted, [int(round((b - a) / period)) for a, b in
                     zip(dx, dx[1:])]


# ── T11 · time parity (AC1) ────────────────────────────────────────────


class TestTimeParity:
    def test_P6_T05_T11_session_boundary_collapses_both_modes(self):
        for ext_hours in (True, False):
            bars = _friday_monday_rth()
            plotted, ref_steps = _default_engine_steps(bars, TF, ext_hours)
            got = LV.logical_indices(plotted, TF, ext_hours)
            assert got[0] == 0
            steps = [b - a for a, b in zip(got, got[1:])]
            assert steps == ref_steps, f"ext_hours={ext_hours}"
            # The weekend span: with RTH only, Friday close -> Monday open
            # is one adjacent step on both engines. With ETH on, Monday's
            # 04:00-09:30 ET premarket lies inside the gap and is trading
            # time, so the authority keeps the whole span.
            if ext_hours:
                assert steps[5] > 1, f"premarket keeps the gap: {steps}"
                assert not gap_is_non_trading(
                    plotted[5].ts, plotted[6].ts, ext_hours, PERIOD)
            else:
                assert steps[5] == 1, f"weekend must collapse: {steps}"
                assert gap_is_non_trading(
                    plotted[5].ts, plotted[6].ts, ext_hours, PERIOD)
            # Authority agreement across every consecutive pair.
            for a, b, step in zip(plotted, plotted[1:], steps):
                authority = gap_is_non_trading(
                    a.ts, b.ts, ext_hours, PERIOD)
                if step > 1:
                    assert not authority, (a.ts, b.ts)
                if (b.ts - a.ts) > PERIOD and step == 1:
                    assert authority, (a.ts, b.ts)

    def test_P6_T05_T11_within_session_hole_is_whitespace(self):
        for ext_hours in (True, False):
            bars = _monday_with_hole()
            plotted, ref_steps = _default_engine_steps(bars, TF, ext_hours)
            got = LV.logical_indices(plotted, TF, ext_hours)
            steps = [b - a for a, b in zip(got, got[1:])]
            assert steps == ref_steps == [1, 1, 4, 1, 1]
            spans = LV.hole_spans(got)
            assert spans == [(2, 3)], f"one 3-slot hole: {spans}"
            hole_a, hole_b = plotted[2], plotted[3]
            assert not gap_is_non_trading(
                hole_a.ts, hole_b.ts, ext_hours, PERIOD), (
                "the midday hole is trading time — the authority keeps it")

    def test_P6_T05_T11_dst_fold_stays_continuous(self):
        bars = _dst_fold_sunday()
        for ext_hours in (True, False):
            plotted, ref_steps = _default_engine_steps(bars, TF, ext_hours)
            got = LV.logical_indices(plotted, TF, ext_hours)
            assert got == list(range(len(plotted))), got
            for a, b in zip(plotted, plotted[1:]):
                assert gap_is_non_trading(a.ts, b.ts, ext_hours, PERIOD)

    def test_P6_T05_T11_duplicate_display_x_never_loses_a_bar(self):
        bars = [_bar(1_700_000_000), _bar(1_700_000_000)]
        got = LV.logical_indices(bars, TF, True)
        assert got == [0, 1], "a same-time collision still advances"

    def test_P6_T05_T11_tz_labels_equal_t_minus_offset_per_mode(self):
        summer = _utc(2026, 7, 1, 16, 0)   # 12:00 EDT
        winter = _utc(2026, 1, 15, 14, 30)  # 09:30 EST
        for mode in LV.MODES:
            assert LV.format_tz_label(summer, EDT) == "07/01 12:00", mode
            assert LV.format_tz_label(winter, EST) == "01/15 09:30", mode
            assert LV.format_tz_label(summer, 0) == "07/01 16:00", mode

    def test_P6_T05_T11_live_update_advances_the_forming_bar(self, qapp):
        view = LV.LwcChartView(tz_offset=EDT)
        view.set_timeframe(TF)
        view.bridge.set_ready(True)
        seen = []
        view.bridge.opsEmitted.connect(seen.append)
        bars = _monday_with_hole()
        view.set_series("candles", bars)
        env = view.bridge.flush()
        assert env is not None and len(env["ops"]) == 2
        base = LB.apply_ops_to_bars(env["ops"])
        assert len(base) == len(bars)
        assert [r[0] for r in base] == view.logical_index

        # Same-ts tick: the forming bar advances, the count is unchanged.
        tick = _bar(bars[-1].ts, c=999.25, v=4242.0)
        view.update_live_bar(tick)
        env = view.bridge.flush()
        assert env is not None
        assert all(op["op"] == "update_bar" for op in env["ops"])
        assert {op["series"] for op in env["ops"]} == {"candles", "volume"}
        rows = LB.apply_ops_to_bars(
            view.bridge.replay_log()[-2:])
        assert rows[-1][4] == pytest.approx(999.25)
        assert len(LB.apply_ops_to_bars(view.bridge.replay_log())) == len(bars)

        # New-ts bar: the series grows by exactly one logical step.
        nxt = _bar(bars[-1].ts + PERIOD, c=101.5, v=10.0)
        view.update_live_bar(nxt)
        view.bridge.flush()
        grown = LB.apply_ops_to_bars(view.bridge.replay_log())
        assert len(grown) == len(bars) + 1
        assert grown[-1][4] == pytest.approx(101.5)

    def test_P6_T05_T11_all_modes_emit_valid_column_ops(self, qapp):
        view = LV.LwcChartView()
        view.set_timeframe(TF)
        view.bridge.set_ready(True)
        bars = _monday_with_hole()
        for mode in LV.MODES:
            view.set_series(mode, bars)
            env = view.bridge.flush()
            assert env is not None and env["v"] == 1
            candles, volume = env["ops"]
            assert candles["mode"] == mode
            assert set(candles["cols"]) == {
                "ts", "open", "high", "low", "close"}
            assert set(volume["cols"]) == {"ts", "value"}
            for col in candles["cols"].values():
                assert isinstance(col, list)
                assert all(isinstance(v, (int, float)) for v in col)


# ── T12 · geometry guard + Q60 record (AC2) ────────────────────────────


class TestGeometryGuard:
    SPACINGS = [0.5, 1.0, 2.0, 4.0, 5.0, 8.0, 20.0, 100.0]

    def test_P6_T05_T12_no_overlap_in_any_regime(self):
        for s in self.SPACINGS:
            body, gap = LV.bar_spacing_geometry(s)
            assert body <= s, f"body never exceeds the pitch at S={s}"
            assert gap >= 0, f"gap >= 0 always at S={s}"

    def test_P6_T05_T12_gap_positive_whenever_spacing_allows(self):
        for s in self.SPACINGS:
            _body, gap = LV.bar_spacing_geometry(s)
            assert (gap > 0) == (s > LV.FLOOR_PX), f"S={s}"

    def test_P6_T05_T12_non_dense_split_is_65_35(self):
        body, gap = LV.bar_spacing_geometry(100.0)
        assert body == pytest.approx(65.0)
        assert gap == pytest.approx(35.0)

    def test_P6_T05_T12_volume_shares_the_price_rule(self):
        # One helper governs both panes — the volume payload aligns 1:1
        # with the candle payload it shares the pitch with.
        ops = LV.series_ops("candles", _monday_with_hole(), TF, True)
        assert ops[0]["cols"]["ts"] == ops[1]["cols"]["ts"]

    def test_P6_T05_T12_q60_retirement_recorded_in_matrix(self):
        text = MATRIX.read_text(encoding="utf-8")
        assert "P6-05" in text
        for token in ("Q60", "A106", "barSpacing", "DG94",
                      "AC-D6.4", "AC-D7.1", "AC-D9.1"):
            assert token in text, f"matrix must record {token}"

    def test_P6_T05_T12_node_chart_suite_is_green(self):
        proc = subprocess.run(
            ["node", "--test", str(LWC_DIR / "chart.test.js")],
            capture_output=True, text=True, cwd=str(REPO), timeout=120)
        assert proc.returncode == 0, proc.stderr[-2000:]


# ── T13 · residue scan (AC3, renderer-only boundary) ──────────────────


class TestRendererBoundary:
    SOURCES = ["ui/lwc_view.py", "chart_assets/lwc/chart.js"]

    # P6-05's list predates P6-10 (Phase 8), which renders the session bands
    # from the unchanged, pure ``services.session_service.session_bands`` — a
    # renderer input the default engine uses too, not an out-of-scope surface.
    # That one module is therefore off this list; ibkr, the stores, any
    # persistence, any order surface, any network access and pyqtgraph itself
    # still must never appear here.
    FORBIDDEN = [
        "from ibkr", "import ibkr", "ibkr.",
        "sqlite", "QSettings",
        "placeOrder", "cancelOrder", "UserOrder", "OrderRate",
        "watchlist", "dock", "pyqtgraph",
        "stop_loss", "take_profit",
        "unpkg", "jsdelivr", "cdnjs", "cdn.",
        "http://", "https://",
        "orders", "BarCache", "get_bars", "save_bars",
    ]

    def test_P6_T05_T13_no_out_of_scope_surface(self):
        hits = []
        for rel in self.SOURCES:
            src = (REPO / rel).read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                if token in src:
                    hits.append(f"{rel}: {token!r}")
        assert hits == [], f"out-of-scope residue: {hits}"

    def test_P6_T05_T13_envelope_carries_timestamps_and_prices_only(self):
        ns = SimpleNamespace(ts=1_700_000_000, open=1.0, high=2.0,
                             low=0.5, close=1.5, volume=7.0)
        for mode in LV.MODES:
            ops = LV.series_ops(mode, [ns], TF, True)
            for op in ops:
                assert set(op) <= {"op", "series", "cols", "mode"}, op
            candles, volume = ops
            assert set(candles["cols"]) == {
                "ts", "open", "high", "low", "close"}
            assert set(volume["cols"]) == {"ts", "value"}
