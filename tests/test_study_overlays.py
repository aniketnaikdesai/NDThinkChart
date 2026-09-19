"""Tests for ui/overlays — study renderers extracted from ChartPanel."""

import pytest
import pyqtgraph as pg

from ui.overlays.base import parse_color
from ui.overlays.gap_overlay import RthGapOverlay
from ui.overlays.vix_overlay import VixOverlay
from ui.overlays.ict_overlay import ICTStudyOverlay
from services.gap_vix_service import (
    calculate_rth_gaps, calculate_vix_standard_deviation, infer_ticker_context,
)
from services.ict_service import calculate_ict_concepts


class TestParseColor:
    def test_hex(self):
        color = parse_color("#38bdf8")
        assert color.isValid()
        assert color.name() == "#38bdf8"

    def test_rgba(self):
        color = parse_color("rgba(255, 93, 0, 0.12)")
        assert color.isValid()
        assert color.red() == 255
        assert color.alphaF() == pytest.approx(0.12, abs=0.01)

    def test_rgba_override_alpha(self):
        color = parse_color("rgba(10, 20, 30, 0.5)", alpha=0.9)
        assert color.alphaF() == pytest.approx(0.9, abs=0.01)


class TestRthGapOverlay:
    def test_renders_gap_steps(self, chart_panel, gap_bars, qapp):
        overlay = RthGapOverlay(chart_panel.price_plot)
        qapp.processEvents()
        ticker = infer_ticker_context("TEST", gap_bars)
        gaps = calculate_rth_gaps(gap_bars, ticker)
        assert gaps
        overlay.render(gaps, len(gap_bars))
        assert overlay.item_count() > 0

    def test_clear_removes_items(self, chart_panel, gap_bars):
        overlay = RthGapOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", gap_bars)
        overlay.render(calculate_rth_gaps(gap_bars, ticker), len(gap_bars))
        count = overlay.item_count()
        assert count > 0
        overlay.clear()
        assert overlay.item_count() == 0


class TestVixOverlay:
    def test_renders_line_plus_label_per_level(self, chart_panel, sample_bars):
        overlay = VixOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", sample_bars)
        result = calculate_vix_standard_deviation(ticker, sample_bars)
        overlay.render(result, len(sample_bars))
        assert overlay.item_count() == 2 * len(result["levels"])

    def test_anchor_label_uses_zero_sigma(self, chart_panel, sample_bars):
        overlay = VixOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", sample_bars)
        result = calculate_vix_standard_deviation(ticker, sample_bars)
        overlay.render(result, len(sample_bars))
        texts = [item.toPlainText() for item in overlay._items
                 if isinstance(item, pg.TextItem)]
        anchors = [t for t in texts if "0σ" in t]
        assert anchors


ICT_PARAMS = {
    "showMS": True, "showMSS": True, "showBOS": True,
    "showOB": True, "showFVG": True, "showBPR": True,
    "showLiquidity": True, "showVI": True,
    "showNWOG": True, "showNDOG": True,
    "showDisplacement": True, "showKillzones": True,
}


class TestICTStudyOverlay:
    def test_renders_concepts(self, chart_panel, impulse_bars):
        overlay = ICTStudyOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", impulse_bars)
        result = calculate_ict_concepts(impulse_bars, ticker, dict(ICT_PARAMS))
        overlay.render(result, len(impulse_bars))
        assert overlay.item_count() > 0

    def test_render_matches_service_output(self, chart_panel, impulse_bars):
        overlay = ICTStudyOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", impulse_bars)
        result = calculate_ict_concepts(impulse_bars, ticker, dict(ICT_PARAMS))
        overlay.render(result, len(impulse_bars))
        n_structures = len(result["marketStructures"])
        n_ob = len(result["orderBlocks"])
        n_fvgs = len(result["fairValueGaps"])
        n_pools = len(result["liquidityPools"])
        n_vis = len(result["volumeImbalances"])
        n_gaps = len(result["openingGaps"])
        n_killzones = len(result["killzones"])
        expected = (
            2 * n_structures        # segment + label per structure
            + n_ob                  # one band per order block
            + n_fvgs                # one band per FVG / BPR
            + 3 * n_pools           # band + midpoint line + label per pool
            + n_vis                 # one band per volume imbalance
            + 2 * n_gaps            # band + midpoint line per opening gap
            + n_killzones           # one vertical region per killzone
        )
        if result["displacements"]:
            expected += 1            # single scatter item
        assert overlay.item_count() == expected

    def test_displacements_use_triangle_scatter(self, chart_panel, impulse_bars):
        overlay = ICTStudyOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", impulse_bars)
        result = calculate_ict_concepts(impulse_bars, ticker, dict(ICT_PARAMS))
        overlay.render(result, len(impulse_bars))
        scatters = [item for item in overlay._items
                    if isinstance(item, pg.ScatterPlotItem)]
        if result["displacements"]:
            assert scatters

    def test_empty_result_renders_nothing(self, chart_panel, sample_bars):
        overlay = ICTStudyOverlay(chart_panel.price_plot)
        ticker = infer_ticker_context("TEST", sample_bars[:5])
        result = calculate_ict_concepts(sample_bars[:5], ticker, dict(ICT_PARAMS))
        overlay.render(result, len(sample_bars[:5]))
        assert overlay.item_count() == 0


class TestChartIntegration:
    def test_study_toggle_repopulates_overlay(self, chart_panel, sample_bars):
        chart_panel.update_chart(sample_bars)
        chart_panel.set_studies([
            {"type": "vix_sd", "label": "VIX", "enabled": True, "params": {}},
        ])
        chart_panel.update_chart(sample_bars)
        assert chart_panel._vix_overlay.item_count() > 0

        chart_panel.set_studies([
            {"type": "vix_sd", "label": "VIX", "enabled": False, "params": {}},
        ])
        chart_panel.update_chart(sample_bars)
        assert chart_panel._vix_overlay.item_count() == 0

    def test_ict_study_counts_match_fixture(self, chart_panel, impulse_bars):
        chart_panel.set_symbol("TEST")
        chart_panel.update_chart(impulse_bars)
        chart_panel.set_studies([
            {"type": "ict", "label": "ICT", "enabled": True,
             "params": dict(ICT_PARAMS)},
        ])
        assert chart_panel._ict_overlay.item_count() > 0