"""D28.4 fix pass — panel series cap + study-cache invalidation on wholesale replace.

Fix 1: ``ChartPanel._bars`` was unbounded (session caps at 5000 but the
panel never pruned) — the new-candle path must mirror the session cap,
rebuild the collapse map on the prune path, and invalidate the study cache.
"""
import pytest

from config import settings
from data.models import Bar
from services import indicator_service as ind
from ui.chart_panel import ChartPanel

BASE = 1_760_000_000
STUDIES_SMA = [{"type": "sma", "enabled": True, "params": {"period": 20}}]


def _bar(i, px=100.0):
    return Bar("TST", "5 mins", BASE + i * 300,
               px, px + 1.0, px - 1.0, px + 0.5, 1000.0 + i)


def _assert_close(a, b):
    if a is None or b is None:
        assert a is b, f"None mismatch: {a!r} vs {b!r}"
    else:
        assert a == pytest.approx(b, rel=1e-9, abs=1e-9), f"{a!r} vs {b!r}"


def _panel(qapp):
    panel = ChartPanel()
    panel.set_symbol("TST")
    panel.set_timeframe("5 mins")
    panel.set_studies(STUDIES_SMA)
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    return panel


def test_panel_bars_pruned_at_session_cap(monkeypatch, qapp):
    """New candles past the cap prune the head (mirrors the session cap)."""
    monkeypatch.setattr(settings, "SESSION_BAR_CAP", 100)
    panel = _panel(qapp)
    try:
        panel.update_chart([_bar(i, 100.0 + i * 0.1) for i in range(100)])
        qapp.processEvents()
        assert len(panel._bars) == 100
        # 5 new candles: head must be pruned to stay at the cap.
        for i in range(100, 105):
            panel.update_last_bar(_bar(i, 100.0 + i * 0.1), True)
            qapp.processEvents()
        assert len(panel._bars) == settings.SESSION_BAR_CAP, (
            f"panel series unbounded: {len(panel._bars)}")
        assert panel._bars[0].ts == BASE + 5 * 300, "oldest bars must be pruned"
        assert panel._bars[-1].ts == BASE + 104 * 300
        # Plotted arrays consistent with the pruned series.
        assert panel._plot_xs == [
            panel._to_display(b.ts) for b in panel._plotted_bars]
        assert len(panel._plot_vols) == len(panel._plotted_bars)
        # Studies exact vs batch after the prune (full recompute, not stale
        # incremental state).
        cached = panel._study_cache.get("TST", "5 mins", STUDIES_SMA)
        assert cached is not None and cached["n_bars"] == 100
        expected = ind.calculate_sma([b.close for b in panel._bars], 20)
        got = cached["values"]["sma:0"]
        assert len(got) == len(expected)
        for g, e in zip(got, expected):
            _assert_close(g, e)
    finally:
        panel.close()


