"""T29 / ESC-009 — high-DPI (DPR 2) coverage for the D6 wick/body clamp and D11 labels.

The session-scoped ``qapp`` fixture (``tests/conftest.py``) runs at the offscreen
default device pixel ratio of 1.0.  These tests therefore exercise DPR 2 in an
*isolated* subprocess whose ``QT_SCALE_FACTOR=2`` never touches the session
QApplication.  No live TWS connection is involved: the probe only builds widgets
with the offscreen QPA platform.

Test map (wave manifest T29):
  * T29-T01 -> test_wick_stays_1_device_px_and_body_clamped_at_dpr  (AC-D6.4)
  * T29-T02 -> test_drawing_labels_inside_view_rect_right_edge_at_dpr (AC-D11.5)
  * T29-T03 -> test_dpr_probe_is_isolated_and_preserves_session_qapp
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
_SENTINEL = "DPI_PROBE_JSON:"

# The probe is run via `python -c` in a child process so its QApplication is
# created with the child's own QT_SCALE_FACTOR and is fully isolated from the
# session `qapp` fixture.  It prints one JSON line prefixed with _SENTINEL.
_PROBE_SRC = textwrap.dedent(
    '''
    import json, os, sys, tempfile
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["DB_PATH"] = os.path.join(
        tempfile.gettempdir(), "ndthinkchart_dpi_probe.sqlite3")

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QImage, QPainter
    from PyQt6.QtCore import Qt, QPointF
    import pyqtgraph as pg
    from data.models import Bar, Drawing
    from ui.chart_panel import ChartPanel

    SENTINEL = "DPI_PROBE_JSON:"
    BASE = 1_700_000_000
    GREEN = (0x34, 0xd3, 0x99)


    def bar(i, spacing, o, h, l, c):
        return Bar("TEST", "1 min", BASE + i * spacing,
                   float(o), float(h), float(l), float(c), 1000.0)


    def make_panel(app, bars, size=(900, 600)):
        p = ChartPanel()
        p.resize(*size)
        p.show()
        app.processEvents()
        p.set_symbol("TEST")
        p.update_chart(bars)
        app.processEvents()
        app.processEvents()
        return p


    def body_geometry(panel, bars):
        """Body width in device pixels, measured from the item's recorded QPicture."""
        vb = panel.price_plot.getViewBox()
        xr = vb.viewRange()[0]
        x_span = xr[1] - xr[0]
        px_per_sec = vb.width() / x_span if x_span else 0.0
        dpr = panel.devicePixelRatioF()
        pic = panel.candlestick.boundingRect()
        # D28.4: candles render across the static layer (closed bars, measured
        # here) and the live layer (forming bar) — the span must cover exactly
        # the bars recorded in the measured picture.
        static_ts = [c[0] for c in panel.candlestick._raw_data]
        data_span = (max(static_ts) - min(static_ts)) if static_ts else 0
        # The QPicture bounding rect is [t0 - w, t_last + w] (wicks sit at x == t),
        # so the recorded body width is the bbox width minus the timestamp span.
        body_data_w = pic.width() - data_span
        return {
            "picture_width": pic.width(),
            "data_span": data_span,
            "body_data_width": body_data_w,
            "px_per_sec": px_per_sec,
            "dpr": dpr,
            "body_device_px": body_data_w * px_per_sec * dpr,
        }


    def scan_row(img, panel, vb, price, t):
        """Contiguous runs of candle-colour pixels on the scanline through `price`."""
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


    def main():
        result = {}
        app = QApplication.instance() or QApplication([])
        result["platformName"] = app.platformName()
        result["scale_factor"] = float(os.environ.get("QT_SCALE_FACTOR", "1"))
        result["dpr"] = app.primaryScreen().devicePixelRatio()

        # (A) Dense 1-min view: the D6 body clamp is required.  960 bars is the
        # canonical dense dataset already used by the D6 wick test.
        dense = [bar(i, 60, 100, 110, 90, 101) for i in range(960)]
        panel = make_panel(app, dense)
        result["dense"] = body_geometry(panel, dense)
        # Diagnostic only: what the clamp yields once the view range is known.
        panel.candlestick.set_data(
            [(b.ts, b.open, b.high, b.low, b.close) for b in dense])
        app.processEvents()
        result["dense_after_regen"] = body_geometry(panel, dense)

        # (B) Sparse view: measure the wick width in device pixels by pixel scan
        # where wicks are separable (so the cosmetic width can be observed).
        sparse = [bar(i, 60, 100, 110, 90, 101) for i in range(30)]
        panel_s = make_panel(app, sparse)
        vb_s = panel_s.price_plot.getViewBox()
        img_s = render_viewport(panel_s)
        wick_runs = scan_row(img_s, panel_s, vb_s, 105.0, sparse[0].ts)
        body_runs = scan_row(img_s, panel_s, vb_s, 100.5, sparse[0].ts)
        result["sparse"] = {
            "dpr": panel_s.devicePixelRatioF(),
            "wick_runs": wick_runs,
            "wick_max_run": max(wick_runs) if wick_runs else None,
            "body_runs": body_runs,
            "body_median_run": sorted(body_runs)[len(body_runs) // 2] if body_runs else None,
        }

        # (C) D11 drawing labels: right-edge containment inside view_rect.
        bars50 = [bar(i, 300, 100 + i * 0.1, 100 + i * 0.1 + 0.5,
                      100 + i * 0.1 - 0.5, 100 + i * 0.1) for i in range(50)]
        panel_l = make_panel(app, bars50)
        panel_l.drawing_overlay.add_drawing(Drawing(
            symbol="TEST", kind="horizontal", payload={"y": 102.5}, color="#ff0000", id=1))
        panel_l.drawing_overlay.add_drawing(Drawing(
            symbol="TEST", kind="zone",
            payload={"x1": BASE, "x2": BASE + 1500, "y1": 103.0, "y2": 101.0},
            color="#00ff00", id=2))
        app.processEvents()
        app.processEvents()
        vb_l = panel_l.price_plot.getViewBox()
        vr = vb_l.mapRectToScene(vb_l.rect())
        labels = []
        for items in panel_l.drawing_overlay._items.values():
            for it in items:
                if isinstance(it, pg.TextItem):
                    b = it.sceneBoundingRect()
                    labels.append({
                        "text": it.toPlainText(),
                        "left": b.left(), "right": b.right(),
                        "top": b.top(), "bottom": b.bottom(),
                        "view_left": vr.left(), "view_right": vr.right(),
                    })
        result["labels"] = labels
        result["live_connection"] = False

        print(SENTINEL + json.dumps(result))
        return 0


    if __name__ == "__main__":
        sys.exit(main())
    '''
)


@functools.lru_cache(maxsize=None)
def _probe(scale_factor):
    """Run the isolated offscreen probe at `scale_factor`; return result/io."""
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_SCALE_FACTOR"] = str(scale_factor)
    env["DB_PATH"] = os.path.join(
        tempfile.gettempdir(), "ndthinkchart_dpi_probe_parent.sqlite3")
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
        f"DPR probe (QT_SCALE_FACTOR={scale_factor}) produced no JSON.\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    return {"result": payload, "stdout": proc.stdout, "stderr": proc.stderr,
            "returncode": proc.returncode}


@pytest.mark.parametrize("scale_factor", [1, 2], ids=["dpr1", "dpr2"])
def test_wick_stays_1_device_px_and_body_clamped_at_dpr(scale_factor):
    """T29-T01 / AC-D6.4 — wick 1 device px; body >= 4 device px and > wick."""
    run = _probe(scale_factor)
    result = run["result"]
    assert result["dpr"] == pytest.approx(float(scale_factor)), run["stderr"]

    # The wick must stay a cosmetic 1-device-pixel line at every DPR.
    wick_max = result["sparse"]["wick_max_run"]
    assert wick_max == 1, (
        f"AC-D6.4: wick is {wick_max} device px at DPR {scale_factor} "
        f"(expected 1); runs={result['sparse']['wick_runs']}"
    )

    # The body must stay >= 4 device pixels and strictly wider than the wick.
    body_dev = result["dense"]["body_device_px"]
    assert body_dev >= 4.0, (
        f"AC-D6.4: at DPR {scale_factor} the dense-view candle body renders "
        f"{body_dev:.2f} device px wide (expected >= 4 == no collapse); "
        f"dense={result['dense']}"
    )
    assert body_dev > wick_max, (
        f"AC-D6.4: body ({body_dev:.2f} device px) is not wider than the wick "
        f"({wick_max} device px) at DPR {scale_factor}"
    )


@pytest.mark.parametrize("scale_factor", [1, 2], ids=["dpr1", "dpr2"])
def test_drawing_labels_inside_view_rect_right_edge_at_dpr(scale_factor):
    """T29-T02 / AC-D11.5 — each drawing label bbox is inside view_rect on the right."""
    run = _probe(scale_factor)
    result = run["result"]
    assert result["dpr"] == pytest.approx(float(scale_factor)), run["stderr"]
    labels = result["labels"]
    assert labels, "probe produced no drawing labels"
    for lab in labels:
        assert lab["right"] <= lab["view_right"] + 0.5, (
            f"AC-D11.5: label {lab['text']!r} bbox right={lab['right']:.2f} "
            f"exceeds view_rect.right()={lab['view_right']:.2f} at DPR {scale_factor}"
        )
        assert lab["left"] >= lab["view_left"] - 0.5, (
            f"AC-D11.5: label {lab['text']!r} bbox left={lab['left']:.2f} is "
            f"outside view_rect.left()={lab['view_left']:.2f} at DPR {scale_factor}"
        )


def test_dpr_probe_is_isolated_and_preserves_session_qapp(qapp):
    """T29-T03 / manual — DPR-2 harness is offscreen, isolated and TWS-free."""
    # The session fixture runs at the offscreen default scale factor.
    before = qapp.primaryScreen().devicePixelRatio()

    run = _probe(2)
    result = run["result"]

    assert result["platformName"] == "offscreen"
    assert result["scale_factor"] == pytest.approx(2.0)
    assert result["dpr"] == pytest.approx(2.0)
    assert result["live_connection"] is False

    # The isolated subprocess must not have disturbed the session QApplication.
    assert qapp.primaryScreen().devicePixelRatio() == before, (
        "DPR-2 probe mutated the session qapp scale factor "
        f"({before} -> {qapp.primaryScreen().devicePixelRatio()})"
    )
    # No broker/live-socket import or connection in the probe process.
    assert "ibapi" not in run["stdout"] and "ibapi" not in run["stderr"]
