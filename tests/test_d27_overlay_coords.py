"""D27.2 — overlay x-coordinates must lie inside the panel's view x-range.

Regression tests for the invisible-overlay bug: the MACD histogram plotted
bar *indices* while the MACD/signal lines plot at display-x, and the ICT /
RTH-gap / VIX overlays plotted raw bar indices on the (display-x) price plot,
rendering every element off-screen.

AC-D27.2 / R56: every rendered element's x-coordinate lies inside the panel's
view x-range. This assertion pattern is the standard for overlay tests going
forward.
"""

from __future__ import annotations

import pyqtgraph as pg
import pytest

from services.gap_vix_service import (
    calculate_rth_gaps,
    calculate_vix_standard_deviation,
    infer_ticker_context,
)
from services.ict_service import calculate_ict_concepts
from ui.overlays.gap_overlay import RthGapOverlay
from ui.overlays.ict_overlay import ICTStudyOverlay
from ui.overlays.vix_overlay import VixOverlay

ICT_PARAMS = {
    "showMS": True, "showMSS": True, "showBOS": True,
    "showOB": True, "showFVG": True, "showBPR": True,
    "showLiquidity": True, "showVI": True,
    "showNWOG": True, "showNDOG": True,
    "showDisplacement": True, "showKillzones": True,
}


def _view_x_range(plot):
    vx0, vx1 = plot.getViewBox().viewRange()[0]
    return float(vx0), float(vx1)


def _rendered_xs(overlay) -> list[float]:
    """Collect representative x-coordinates from every rendered item."""
    xs: list[float] = []
    for item in overlay._items:
        if isinstance(item, pg.PlotDataItem):
            xs.extend(float(v) for v in item.xData)
        elif isinstance(item, pg.TextItem):
            xs.append(float(item.pos().x()))
        elif isinstance(item, pg.ScatterPlotItem):
            xs.extend(float(p.pos().x()) for p in item.points())
        elif isinstance(item, pg.LinearRegionItem):
            xs.extend(float(v) for v in item.getRegion())
        # pg.InfiniteLine (VIX sigma hlines) spans all x: nothing to assert.
    return xs


def _assert_in_view(xs: list[float], vx0: float, vx1: float, what: str) -> None:
    assert xs, f"{what}: no x-coords rendered at all"
    assert vx0 <= min(xs), (
        f"{what}: min rendered x {min(xs):.1f} left of view [{vx0:.1f}, {vx1:.1f}]"
    )
    assert max(xs) <= vx1, (
        f"{what}: max rendered x {max(xs):.1f} right of view [{vx0:.1f}, {vx1:.1f}]"
    )


def test_d27_2_macd_histogram_x_in_view_range(chart_panel, sample_bars, qapp):
    chart_panel.set_timeframe("5 mins")
    chart_panel.update_chart(sample_bars)
    chart_panel.set_studies([{"type": "macd", "enabled": True, "params": {}}])
    qapp.processEvents()
    hists = [
        it for it in chart_panel._osc_items if isinstance(it, pg.BarGraphItem)
    ]
    assert hists, "no MACD histogram rendered"
    xs = [float(v) for h in hists for v in h.opts["x"]]
    vx0, vx1 = _view_x_range(chart_panel.osc_plot)
    _assert_in_view(xs, vx0, vx1, "MACD histogram")


def test_d27_2_rth_gap_overlay_x_in_view_range(chart_panel, gap_bars, qapp):
    chart_panel.set_timeframe("5 mins")
    chart_panel.update_chart(gap_bars)
    qapp.processEvents()
    overlay = RthGapOverlay(chart_panel.price_plot)
    overlay.set_collapse_map(chart_panel._collapse_map)
    ticker = infer_ticker_context("TEST", gap_bars)
    gaps = calculate_rth_gaps(gap_bars, ticker)
    assert gaps, "fixture produced no gaps"
    overlay.render(gaps, gap_bars)
    vx0, vx1 = _view_x_range(chart_panel.price_plot)
    _assert_in_view(_rendered_xs(overlay), vx0, vx1, "RTH gap overlay")


def test_d27_2_vix_overlay_x_in_view_range(chart_panel, sample_bars, qapp):
    chart_panel.set_timeframe("5 mins")
    chart_panel.update_chart(sample_bars)
    qapp.processEvents()
    overlay = VixOverlay(chart_panel.price_plot)
    overlay.set_collapse_map(chart_panel._collapse_map)
    ticker = infer_ticker_context("TEST", sample_bars)
    result = calculate_vix_standard_deviation(ticker, sample_bars)
    assert result.get("levels"), "fixture produced no VIX levels"
    overlay.render(result, sample_bars)
    vx0, vx1 = _view_x_range(chart_panel.price_plot)
    _assert_in_view(_rendered_xs(overlay), vx0, vx1, "VIX overlay labels")


def test_d27_2_ict_overlay_x_in_view_range(chart_panel, impulse_bars, qapp):
    chart_panel.set_timeframe("5 mins")
    chart_panel.update_chart(impulse_bars)
    qapp.processEvents()
    overlay = ICTStudyOverlay(chart_panel.price_plot)
    overlay.set_collapse_map(chart_panel._collapse_map)
    ticker = infer_ticker_context("TEST", impulse_bars)
    result = calculate_ict_concepts(impulse_bars, ticker, dict(ICT_PARAMS))
    assert overlay_item_count(result) > 0, "fixture produced no ICT concepts"
    overlay.render(result, impulse_bars)
    vx0, vx1 = _view_x_range(chart_panel.price_plot)
    _assert_in_view(_rendered_xs(overlay), vx0, vx1, "ICT overlay")


def overlay_item_count(result: dict) -> int:
    return (
        len(result.get("marketStructures", []))
        + len(result.get("orderBlocks", []))
        + len(result.get("fairValueGaps", []))
        + len(result.get("liquidityPools", []))
        + len(result.get("volumeImbalances", []))
        + len(result.get("openingGaps", []))
        + len(result.get("killzones", []))
        + len(result.get("displacements", []))
    )
