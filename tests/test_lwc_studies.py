"""tests/test_lwc_studies.py — P6-T06 Phase 4 study overlays (M).

The study-parity cases: every study overlay the LWC engine receives carries
exactly the shared model's array for the same bars and settings (one
``StudyCache``-backed source, so parity is by construction), the JS membrane
returns those same numbers, and a second render of an identical state neither
recomputes nor sends anything while a new candle is served from the cache.
The residue scan closes the renderer-only boundary (no engine-side trading or
persistence surface, no study op on the bar transport).

QApplication usage: the driver is a ``QWidget``, so the render cases take the
repo's session-scoped ``qapp`` fixture (a locally created application gets
collected and aborts the process at the next widget construction).
"""

import ast
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from data.bar_aggregator import TIMEFRAME_SECONDS
from data.models import Bar
from services import chart_model
from ui import lwc_view as LV

REPO = Path(__file__).resolve().parent.parent
STUDIES_JS = REPO / "chart_assets" / "lwc" / "studies.js"
MATRIX = REPO / "docs" / "lwc_parity_matrix.md"

SYMBOL = "LWC-STUDY"
TF = "5 mins"
PERIOD = TIMEFRAME_SECONDS[TF]
EDT = 14400

#: Every numeric study kind the shared model computes, enabled together so
#: one render proves the whole family and the per-instance keys at once.
STUDIES = [
    {"type": "sma", "enabled": True,
     "params": {"period": 3, "color": "#ffcc00"}},
    {"type": "ema", "enabled": True, "params": {"period": 4}},
    {"type": "ema2", "enabled": True, "params": {"period": 2}},
    {"type": "vwap", "enabled": True, "params": {}},
    {"type": "bollinger", "enabled": True,
     "params": {"period": 5, "std_dev": 2.0, "color": "#22d3ee"}},
    {"type": "rsi", "enabled": True,
     "params": {"period": 4, "overbought": 70, "oversold": 30}},
    {"type": "macd", "enabled": True,
     "params": {"fast": 3, "slow": 6, "signal": 3}},
]


def _utc(y, mo, d, hh, mm):
    return int(datetime(y, mo, d, hh, mm, tzinfo=timezone.utc).timestamp())


def _bar(ts, i):
    base = 100.0 + (i % 7) * 0.5 + i * 0.1
    return Bar(
        symbol=SYMBOL, timeframe=TF, ts=ts,
        open=base, high=base + 1.2, low=base - 0.8,
        close=base + (0.3 if i % 2 else -0.2),
        volume=1000.0 + 10.0 * i,
    )


def _bars():
    """Two RTH sessions (Fri + Mon, EDT) with a 3-bar midday hole.

    Four pre-market bars lead the series: with extended hours off they are
    filtered out of the plotted set, so the fixture exercises both the
    plotted-row filter and the collapse step — exactly the cases where a
    second value source would drift.
    """
    premarket = [_utc(2026, 9, 25, 12, 45) + i * PERIOD for i in range(4)]
    fri = [_utc(2026, 9, 25, 13, 30) + i * PERIOD for i in range(20)]
    mon_have = [0, 1, 2, 6, 7, 8, 9, 10]
    mon = [_utc(2026, 9, 28, 13, 30) + i * PERIOD for i in mon_have]
    return [_bar(ts, i) for i, ts in enumerate(premarket + fri + mon)]


def _view(bars=None, studies=None, ext_hours=False):
    view = LV.LwcChartView(tz_offset=EDT)
    view.set_symbol(SYMBOL)
    view.set_timeframe(TF)
    view.set_extended_hours(ext_hours)
    view.set_studies(studies if studies is not None else STUDIES)
    view.set_series("candles", bars if bars is not None else _bars())
    return view


def _expected_ids(studies):
    """Overlay ids the renderer must publish, in render order."""
    ids = []
    for idx, study in enumerate(studies):
        if not study.get("enabled"):
            continue
        if study["type"] not in LV.STUDY_LINES:
            continue
        for suffix in LV.STUDY_LINES[study["type"]]:
            ids.append(f"{chart_model.study_key(study['type'], idx)}{suffix}")
    return ids


def _model_arrays(view):
    """A cold shared-model computation — the reference every engine renders."""
    cache = chart_model.StudyCache()
    all_vals, _states = chart_model.compute_study_values(
        view.plotted_bars, view.studies, cache, SYMBOL, TF)
    return all_vals


def _expected_series(model, overlay_id):
    if overlay_id.endswith("_hist"):
        key = overlay_id[: -len("_hist")]
        return [None if (m is None or s is None) else m - s
                for m, s in zip(model[key], model[f"{key}_signal"])]
    return model[overlay_id]


# ── T11 · study parity + cache reuse (AC1) ─────────────────────────────


class TestStudyParity:
    def test_P6_T06_T11_every_overlay_equals_the_shared_model(self, qapp):
        view = _view()
        model = _model_arrays(view)
        overlays = view.study_overlays

        assert set(overlays) == set(_expected_ids(STUDIES))
        assert len(view.plotted_bars) < len(_bars()), (
            "fixture must exercise plotted-row filtering")
        for overlay_id, values in overlays.items():
            assert len(values) == len(view.plotted_bars), overlay_id
            assert values == _expected_series(model, overlay_id), overlay_id
            assert any(v is not None for v in values), (
                f"{overlay_id} rendered no value at all")
        # Overlay ids line up with the model's own keys, one for one.
        assert {k for k in overlays if not k.endswith("_hist")} <= set(model)
        assert len(view.study_ops) == len(overlays)

    def test_P6_T06_T11_ops_carry_logical_time_and_nullable_values(self, qapp):
        view = _view()
        envelopes = view.study_envelopes
        assert envelopes and envelopes[0]["v"] == 1
        for op in view.study_ops:
            assert set(op) == {
                "op", "series", "kind", "pane", "style", "cols"}
            assert op["op"] == "set_study"
            assert op["series"] == "studies"
            assert op["cols"]["ts"] == view.logical_index
            assert len(op["cols"]["value"]) == len(view.logical_index)
            base = LV.study_base_kind(op["kind"])
            expect_pane = ("oscillator" if base in LV.OSCILLATOR_STUDIES
                           else "price")
            assert op["pane"] == expect_pane, op["kind"]
            assert all(v is None or isinstance(v, (int, float))
                       for v in op["cols"]["value"])
            # The not-yet-valid prefix is a real null, never a fake 0
            # (VWAP is valid from the first bar — it has no prefix).
            if base != "vwap":
                assert op["cols"]["value"][0] is None, op["kind"]

    def test_P6_T06_T11_js_membrane_returns_the_model_values(self, qapp):
        view = _view()
        env = {"v": 1, "ops": view.study_ops}
        script = (
            "const s = require('./chart_assets/lwc/studies.js');"
            "const env = JSON.parse(process.env.STUDY_ENVELOPE);"
            "const check = s.validateEnvelope(env);"
            "const out = {check: check, ops: env.ops.map(function (op) {"
            "  return {kind: op.kind, pane: s.paneFor(op.kind),"
            "          rows: s.lineRows(op)};"
            "})};"
            "console.log(JSON.stringify(out));"
        )
        proc = subprocess.run(
            ["node", "-e", script], capture_output=True, text=True,
            cwd=str(REPO), timeout=120,
            env=dict(os.environ, STUDY_ENVELOPE=json.dumps(env)),
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        decoded = json.loads(proc.stdout)
        assert decoded["check"]["ok"] is True, decoded["check"]

        for got, op in zip(decoded["ops"], view.study_ops):
            assert got["kind"] == op["kind"]
            assert got["pane"] == op["pane"]
            assert [row["time"] for row in got["rows"]] == op["cols"]["ts"]
            values = [None if set(row) == {"time"} else row["value"]
                      for row in got["rows"]]
            assert values == op["cols"]["value"], op["kind"]

    def test_P6_T06_T11_second_render_serves_from_cache(self, qapp,
                                                       monkeypatch):
        calls = {"full": 0, "incremental": 0}
        real_full = chart_model.study_values_full
        real_incremental = chart_model.study_values_incremental

        def counting_full(bars, studies):
            calls["full"] += 1
            return real_full(bars, studies)

        def counting_incremental(cached, studies, new_bar):
            calls["incremental"] += 1
            return real_incremental(cached, studies, new_bar)

        monkeypatch.setattr(chart_model, "study_values_full", counting_full)
        monkeypatch.setattr(
            chart_model, "study_values_incremental", counting_incremental)

        view = _view()
        assert calls == {"full": 1, "incremental": 0}
        ops_before = view.study_ops
        envelopes_before = len(view.study_envelopes)

        # Second render, identical state: no recompute, no traffic.
        view.set_studies(STUDIES)
        assert calls == {"full": 1, "incremental": 0}
        assert len(view.study_envelopes) == envelopes_before
        assert view.study_ops == ops_before

        # One new candle: the cache's incremental path serves the render.
        last = view.plotted_bars[-1]
        nxt = _bar(last.ts + PERIOD, len(_bars()))
        view.update_live_bar(nxt)
        assert calls == {"full": 1, "incremental": 1}, (
            "a new candle must be served by the cache, not recomputed")
        assert len(view.study_envelopes) == envelopes_before + 1
        assert len(view.plotted_bars) == len(ops_before[0]["cols"]["ts"]) + 1
        cached = view.study_cache.get(SYMBOL, TF, view.studies)
        assert cached is not None
        assert cached["n_bars"] == len(view.plotted_bars)

        fresh, _states = chart_model.study_values_full(
            view.plotted_bars, view.studies)
        for overlay_id, values in view.study_overlays.items():
            assert len(values) == len(view.plotted_bars), overlay_id
            assert values[-1] == _expected_series(fresh, overlay_id)[-1], (
                f"{overlay_id} tail differs after the cached render")

    def test_P6_T06_T11_set_study_overlay_publishes_one_series(self, qapp):
        view = _view()
        values = [None] * 4 + [101.25] * (len(view.plotted_bars) - 4)
        seen = []
        view.studyOpsEmitted.connect(seen.append)

        view.set_study_overlay("sma:9", values)

        assert len(seen) == 1
        assert seen[0]["v"] == 1
        op = seen[0]["ops"][0]
        assert op["kind"] == "sma:9"
        assert op["pane"] == "price"
        assert op["cols"]["ts"] == view.logical_index
        assert op["cols"]["value"] == values
        assert view.study_overlays["sma:9"] == values

        with pytest.raises(ValueError):
            view.set_study_overlay("not_a_study:0", values)
        with pytest.raises(ValueError):
            view.set_study_overlay("sma:9", [1.0])

    def test_P6_T06_T11_overlay_studies_and_disabled_emit_no_series(self, qapp):
        view = _view()
        assert view.study_overlays
        before = len(view.study_envelopes)

        view.set_studies([
            {"type": "rth_gaps", "enabled": True, "params": {}},
            {"type": "sma", "enabled": False, "params": {}},
        ])

        assert view.study_overlays == {}
        assert len(view.study_envelopes) == before + 1
        assert view.study_envelopes[-1]["ops"] == [
            {"op": "clear_study", "series": "studies"}]
        assert view.study_ops[-1]["op"] == "clear_study"

    def test_P6_T06_T11_parity_row_8_moves_to_done(self):
        text = MATRIX.read_text(encoding="utf-8")
        rows = [line for line in text.splitlines() if line.startswith("| 8 |")]
        assert len(rows) == 1, rows
        assert "P6-06" in rows[0]
        assert rows[0].rstrip().endswith("Done / accepted |"), rows[0]
        assert "studies.js" in text, "the wave note names the JS module"


# ── T12 · residue scan (AC2, renderer-only boundary) ───────────────────


def _uses_pyqtgraph(src: str) -> bool:
    """True when source imports or instantiates pyqtgraph (ESC-072).

    The boundary is a property — the LWC engine must not import or use the
    default engine — not the literal word. A docstring that merely names the
    default engine passes; a real import/usage still fails.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:  # a JS asset: text is all there is
        return "pyqtgraph" in src
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] == "pyqtgraph"
                   for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "pyqtgraph":
                return True
        elif isinstance(node, ast.Name) and node.id == "pyqtgraph":
            return True
    return False


class TestRendererBoundary:
    SOURCES = ["ui/lwc_view.py", "chart_assets/lwc/studies.js"]

    FORBIDDEN = [
        "from ibkr", "import ibkr", "ibkr.",
        "sqlite", "QSettings", "StudyStore", "study_store",
        "placeOrder", "cancelOrder", "UserOrder", "OrderRateLimiter",
        "watchlist", "dock", "pyqtgraph",
        "stop_loss", "take_profit",
        "unpkg", "jsdelivr", "cdn.", "http://", "https://",
        "orders", "BarCache", "get_bars", "save_bars",
    ]

    def test_P6_T06_T12_no_out_of_scope_surface(self):
        hits = []
        for rel in self.SOURCES:
            src = (REPO / rel).read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                if token == "pyqtgraph":
                    # ESC-072: assert the property, not the word.
                    if _uses_pyqtgraph(src):
                        hits.append(f"{rel}: 'pyqtgraph' imported/used")
                elif token in src:
                    hits.append(f"{rel}: {token!r}")
        assert hits == [], f"out-of-scope residue: {hits}"

    def test_P6_T06_T12_study_ops_carry_timestamps_and_prices_only(self, qapp):
        view = _view()
        assert view.study_ops
        for op in view.study_ops:
            assert set(op["cols"]) == {"ts", "value"}
            assert all(isinstance(t, int) for t in op["cols"]["ts"])
            assert all(v is None or isinstance(v, (int, float))
                       for v in op["cols"]["value"])
            assert json.dumps(op)  # primitives only — no objects, no strings in

    def test_P6_T06_T12_studies_never_ride_the_bar_transport(self, qapp):
        view = _view()
        log = view.bridge.replay_log()
        assert log, "the bar transport must carry the candles/volume ops"
        assert all(op["series"] in {"candles", "volume"} for op in log)
        assert [op for op in log if op["series"] == "studies"] == []
