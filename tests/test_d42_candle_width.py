"""P2-T06 / ESC-041 / AC-D6.4 (revised 2026-10-15 by D42/ESC-042) — the rendered
candle-width geometry guard.

The D42 density cap renders the candle body as ``min(max(0.65 * pitch, F),
pitch)``, so at the ESC-041/ESC-042 repro (192-bar SPY 5-min, Ext Hours ON, 900 px
pane) the body yields to the inter-bar pitch and adjacent bodies never overlap.

This guard renders the **real** ``CandlestickItem`` at **DPR 2** and MEASURES the
pitch from the rendered series' display-x (``_raw_data``) and the body from the
recorded ``QPicture`` bounding rect.  It asserts only the unit-free relations
``body <= pitch`` and ``body == pitch`` — it does NOT hard-code the requirement's
indicative ``3.83`` (RC-D42-3), and it makes NO ``F == 4.0`` device-px equality
assertion: ``F`` is 4 ViewBox **logical** px (8 device px at DPR 2), the unit
``px_per_sec`` yields.

DPR 2 is exercised in an isolated ``QT_SCALE_FACTOR=2`` subprocess (the harness
convention from ``tests/test_chart_dpi.py``), never by mutating the session
``qapp``.  The probe sets its own ``DB_PATH`` (ESC-043) so a non-pytest offscreen
child never opens the user-space production DB.

Test map (wave manifest P2-T06):
  * P2-T06-T11 -> test_dense_repro_body_never_exceeds_measured_pitch  (AC1)
  * P2-T06-T21 -> test_non_dense_body_is_floor_or_65pct_of_pitch      (AC2)
  * P2-T06-T31 -> test_guard_discriminates_against_pre_fix_flat_floor (AC3)
  * P2-T06-T41 -> test_volume_width_matches_rendered_body_at_both_densities (AC4)
"""

import functools
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_SENTINEL = "D42_PROBE_JSON:"

# The D6 legibility floor, in ViewBox **logical** pixels — the unit ``px_per_sec``
# yields (``vb.width() / x_span``) and the unit ``capped_body_half_width``'s
# ``floor_px`` expects.  4 logical px == 8 device px at DPR 2.  Never asserted in
# device px (RC-D42-3).
FLOOR_PX = 4.0

# The probe runs via ``python -c`` in a child process so its QApplication is
# created with the child's own ``QT_SCALE_FACTOR`` and is fully isolated from the
# session ``qapp`` fixture.  It prints one JSON line prefixed with _SENTINEL.
_PROBE_SRC = textwrap.dedent(
    '''
    import json, os, sys, tempfile
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["DB_PATH"] = os.path.join(
        tempfile.gettempdir(), "ndthinkchart_d42_probe.sqlite3")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QImage, QPainter
    from PyQt6.QtCore import Qt, QPointF
    from data.models import Bar
    from ui.chart_panel import ChartPanel

    SENTINEL = "D42_PROBE_JSON:"
    BASE = 1_700_000_000
    GREEN = (0x34, 0xd3, 0x99)


    def bar(i, spacing, o, h, l, c):
        return Bar("TEST", "5 mins", BASE + i * spacing,
                   float(o), float(h), float(l), float(c), 1000.0)


    def make_panel(app, bars, size=(900, 600)):
        # Ext Hours ON is ChartPanel's default (ui/chart_panel.py:380), so the
        # ESC-041 repro needs no set_extended_hours call.
        p = ChartPanel()
        p.resize(*size)
        p.show()
        app.processEvents()
        p.set_symbol("TEST")
        p.update_chart(bars)
        app.processEvents()
        app.processEvents()
        return p


    def geometry(panel):
        """Measure body + pitch from the rendered series (never re-derive)."""
        vb = panel.price_plot.getViewBox()
        xr = vb.viewRange()[0]
        x_span = xr[1] - xr[0]
        px_per_sec = vb.width() / x_span if x_span else 0.0
        dpr = panel.devicePixelRatioF()
        pic = panel.candlestick.boundingRect()
        # D28.4: the static layer holds the closed bars (bars[:-1]); the forming
        # bar lives in live_candle, so measure the span from the static layer's
        # own display-x data, never from the full input list.
        static_ts = [c[0] for c in panel.candlestick._raw_data]
        data_span = (max(static_ts) - min(static_ts)) if static_ts else 0
        # Bodies span [t - w, t + w] and wicks sit at x == t, so the picture
        # width is (t_last - t0) + 2w (+ a small cosmetic-pen inflation).
        body_data_w = pic.width() - data_span
        diffs = sorted(static_ts[i + 1] - static_ts[i]
                       for i in range(len(static_ts) - 1))
        median_diff = diffs[len(diffs) // 2] if diffs else 0.0
        return {
            "vb_width": vb.width(),
            "dpr": dpr,
            "data_span": data_span,
            "body_data_width": body_data_w,
            "median_diff": median_diff,
            "px_per_sec": px_per_sec,
            # The unit-free relations are asserted in ViewBox logical px.
            "body_logical": body_data_w * px_per_sec,
            "pitch_logical": median_diff * px_per_sec,
            "vol_width": panel.volume_bars.opts["width"],
        }


    def render_viewport(panel):
        pp = panel.price_plot
        vp = pp.viewport()
        dpr = pp.devicePixelRatioF()
        img = QImage(int(vp.width() * dpr), int(vp.height() * dpr),
                     QImage.Format.Format_ARGB32_Premultiplied)
        img.setDevicePixelRatio(dpr)
        img.fill(Qt.GlobalColor.black)
        painter = QPainter(img)
        vp.render(painter)
        painter.end()
        return img


    def scan_row(img, panel, vb, price, t):
        """Contiguous runs of candle-colour pixels on the scanline through price."""
        sp = vb.mapViewToScene(QPointF(t, price))
        qp = panel.price_plot.mapFromScene(sp)
        dpr = panel.devicePixelRatioF()
        y = int(round(qp.y() * dpr))
        runs, cur = [], 0
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            is_green = (abs(c.green() - GREEN[1]) <= 40
                        and abs(c.red() - GREEN[0]) <= 40
                        and abs(c.blue() - GREEN[2]) <= 40
                        and c.alpha() > 128)
            if is_green:
                cur += 1
            else:
                if cur:
                    runs.append(cur)
                cur = 0
        if cur:
            runs.append(cur)
        return runs


    def main():
        result = {}
        app = QApplication.instance() or QApplication([])
        result["platformName"] = app.platformName()
        result["scale_factor"] = float(os.environ.get("QT_SCALE_FACTOR", "1"))
        result["dpr"] = app.primaryScreen().devicePixelRatio()

        # (A) ESC-041 repro: 192-bar 5-min series, Ext Hours ON, 900 px pane.
        dense = [bar(i, 300, 100, 110, 90, 101) for i in range(192)]
        result["dense"] = geometry(make_panel(app, dense))

        # (B) Non-dense: 78 bars — the pitch is wide enough for the floor to bind.
        non_dense = [bar(i, 300, 100, 110, 90, 101) for i in range(78)]
        panel_nd = make_panel(app, non_dense)
        result["non_dense"] = geometry(panel_nd)
        # The wick is a cosmetic 1-px pen: scan a row between the body top (101)
        # and the high (110) where wicks are separable.
        vb_nd = panel_nd.price_plot.getViewBox()
        img_nd = render_viewport(panel_nd)
        wick_runs = scan_row(img_nd, panel_nd, vb_nd, 105.0, non_dense[0].ts)
        result["non_dense"]["wick_runs"] = wick_runs
        result["non_dense"]["wick_max_run"] = max(wick_runs) if wick_runs else None

        result["live_connection"] = False
        print(SENTINEL + json.dumps(result))
        return 0


    if __name__ == "__main__":
        sys.exit(main())
    '''
)


@functools.lru_cache(maxsize=None)
def _probe():
    """Run the isolated DPR-2 offscreen probe once; return its JSON result/io."""
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_SCALE_FACTOR"] = "2"
    env["DB_PATH"] = os.path.join(
        tempfile.gettempdir(), "ndthinkchart_d42_probe_parent.sqlite3")
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SRC],
        capture_output=True, text=True, env=env, cwd=str(REPO_ROOT), timeout=180,
    )
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith(_SENTINEL):
            payload = json.loads(line[len(_SENTINEL):])
    assert payload is not None, (
        "D42 DPR-2 probe produced no JSON.\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    return {"result": payload, "stdout": proc.stdout, "stderr": proc.stderr,
            "returncode": proc.returncode}


def test_dense_repro_body_never_exceeds_measured_pitch():
    """P2-T06-T11 / AC-D6.4 (revised) — at the ESC-041 repro the rendered body
    never exceeds the inter-bar pitch, and equals it (the floor yields).

    The pitch is MEASURED from the rendered series at the final view range — not
    hard-coded from the requirement's indicative 3.83 (RC-D42-3) — and the body
    is measured from the ``QPicture`` bounding box, never re-derived.
    """
    run = _probe()
    result = run["result"]
    assert result["platformName"] == "offscreen", run["stderr"]
    assert result["dpr"] == pytest.approx(2.0), run["stderr"]

    dense = result["dense"]
    pitch = dense["pitch_logical"]
    body = dense["body_logical"]

    # Measured, not hard-coded: the pitch comes from the rendered series.
    assert dense["median_diff"] > 0
    assert pitch > 0

    # AC-D6.4 (i): body <= pitch at any density — adjacent bodies never overlap.
    assert body <= pitch + 1e-6, (
        f"AC-D6.4: dense repro body {body:.3f} logical px exceeds the measured "
        f"inter-bar pitch {pitch:.3f} logical px; dense={dense}"
    )
    # AC-D6.4 (iii) at the repro: the floor yields, so body == pitch.
    assert body == pytest.approx(pitch, rel=0.05), (
        f"AC-D6.4: at the dense repro the body ({body:.3f} logical px) should "
        f"equal the measured pitch ({pitch:.3f} logical px); dense={dense}"
    )


def test_non_dense_body_is_floor_or_65pct_of_pitch():
    """P2-T06-T21 / AC-D6.4 (revised) — at 78 bars the body is
    ``max(0.65 * pitch, F) > F`` and the wick is still 1 device px.

    No ``F == 4.0`` device-px equality is asserted: ``F`` is 4 ViewBox logical px
    (8 device px at DPR 2), and only the relation ``body > F`` is load-bearing.
    """
    run = _probe()
    result = run["result"]
    assert result["dpr"] == pytest.approx(2.0), run["stderr"]

    nd = result["non_dense"]
    pitch = nd["pitch_logical"]
    body = nd["body_logical"]

    # The dataset must actually be in the non-dense regime for this leg to bind.
    assert pitch > FLOOR_PX, (
        f"non-dense pitch {pitch:.3f} logical px is not above the floor "
        f"{FLOOR_PX} — the dataset is not in the non-dense regime; nd={nd}"
    )
    assert body == pytest.approx(max(0.65 * pitch, FLOOR_PX), rel=0.05), (
        f"AC-D6.4: non-dense body {body:.3f} logical px != "
        f"max(0.65 * pitch, F) = {max(0.65 * pitch, FLOOR_PX):.3f}; nd={nd}"
    )
    assert body > FLOOR_PX
    assert body <= pitch + 1e-6

    # The wick stays a cosmetic 1 device px (the unchanged AC-D6.4 clause).
    assert nd["wick_max_run"] == 1, (
        f"AC-D6.4: non-dense wick is {nd['wick_max_run']} device px "
        f"(expected 1); runs={nd['wick_runs']}"
    )


def test_guard_discriminates_against_pre_fix_flat_floor():
    """P2-T06-T31 / AC3 — the guard is discriminating: the repro pitch sits below
    the pre-fix flat floor, so the pre-fix tree (body == F) rendered body > pitch
    (RED — a contiguous zero-gap run between adjacent body centres), while the
    post-fix tree renders body <= pitch (GREEN).
    """
    run = _probe()
    result = run["result"]
    dense = result["dense"]
    pitch = dense["pitch_logical"]
    body = dense["body_logical"]

    # RED pre-fix: the flat F floor exceeds the measured pitch -> overlapping
    # bodies.  This is the regression ESC-041 reports and the guard catches.
    assert FLOOR_PX > pitch, (
        f"the ESC-041 repro pitch ({pitch:.3f} logical px) is not below the "
        f"pre-fix flat floor ({FLOOR_PX} logical px) — the repro is not dense "
        f"enough to discriminate; dense={dense}"
    )
    # GREEN post-fix: the density cap yields the body to the pitch.
    assert body <= pitch + 1e-6, (
        f"post-fix dense body {body:.3f} logical px still exceeds the measured "
        f"pitch {pitch:.3f} logical px; dense={dense}"
    )


def test_volume_width_matches_rendered_body_at_both_densities():
    """P2-T06-T41 / AC-D9.1 + AC-D9.2 — the volume bar width equals the rendered
    price body width (measured from the candle ``QPicture``) at both densities.
    """
    run = _probe()
    result = run["result"]
    for name in ("dense", "non_dense"):
        geom = result[name]
        vol_width = geom["vol_width"]
        measured_body = geom["body_data_width"]
        assert vol_width == pytest.approx(measured_body, rel=0.02), (
            f"AC-D9.1: {name} volume width {vol_width} != rendered body "
            f"{measured_body}; geom={geom}"
        )
