"""ESC-007 / AC-D8.6, AC-D8.7 — live volume ceiling tests.

The forming (last) bar's volume grows live, so the volume Y ceiling must track
it without clipping. The ceiling is updated O(1) against a cached running max
on intra-bar ticks and only widened when the live max crosses the current
nice_max; a non-crossing tick performs no range write. On a load / new bar the
cached running max is rebuilt O(N), and ``auto_range=False`` refresh paths such
as ``set_timezone()`` re-apply the cached ceiling.
"""

import pytest

from ui.chart_panel import ChartPanel, _nice_volume_max
from data.models import Bar


def _bar(ts, vol, o=100, c=100, high=101, low=99):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=high,
               low=low, close=c, volume=vol)


def _make_panel(qapp):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    return panel


# ── T23-T01 / AC-D8.6 ─────────────────────────────────────────────────────────
def test_volume_ceiling_tracks_live_bar(qapp):
    """A live intra-bar tick past the initial nice_max widens the ceiling."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        bars = [_bar(ts0 + i * 60, 100 + i * 50) for i in range(5)]
        bars[-1] = _bar(ts0 + 4 * 60, 800)          # load-time max volume = 800
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()

        vb = panel.volume_plot.getViewBox()
        load_nice = _nice_volume_max(800)           # 1000
        assert panel._vol_max == pytest.approx(800)
        assert panel._volume_nice_max == pytest.approx(load_nice)
        assert vb.viewRange()[1][1] == pytest.approx(load_nice, rel=0.02)

        # Intra-bar tick on the same (last) bar — no full reload.
        live_vol = 5_000
        live_nice = _nice_volume_max(live_vol)      # 7500
        assert live_nice > load_nice
        panel.update_last_bar(_bar(bars[-1].ts, live_vol), is_new_candle=False)
        qapp.processEvents()

        assert panel._vol_max == pytest.approx(max(800, live_vol))
        assert panel._volume_nice_max == pytest.approx(live_nice)
        upper = vb.viewRange()[1][1]
        assert upper == pytest.approx(live_nice, rel=0.02)
        # Forming bar is not clipped: its volume sits under the pane top (> 0).
        assert 0 < live_vol <= upper
    finally:
        panel.hide()
        panel.close()


# ── T23-T02 / AC-D8.7 ─────────────────────────────────────────────────────────
def test_volume_ceiling_refit_on_timezone_refresh(qapp):
    """set_timezone() re-applies the cached ceiling rather than going stale."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        bars = [_bar(ts0 + i * 60, 100 + i * 50) for i in range(5)]
        bars[-1] = _bar(ts0 + 4 * 60, 800)
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()

        panel.update_last_bar(_bar(bars[-1].ts, 5_000), is_new_candle=False)
        qapp.processEvents()
        widened = _nice_volume_max(5_000)           # 7500
        assert panel._volume_nice_max == pytest.approx(widened)

        panel.set_timezone(18_000)
        qapp.processEvents()

        vb = panel.volume_plot.getViewBox()
        assert panel._volume_nice_max == pytest.approx(widened)
        assert vb.viewRange()[1][1] == pytest.approx(widened, rel=0.02)
        assert vb.viewRange()[1][0] == pytest.approx(0, abs=1)
    finally:
        panel.hide()
        panel.close()


# ── T23-T03 / O(1) only-widen ─────────────────────────────────────────────────
def test_non_crossing_tick_performs_no_range_write(qapp):
    """A tick below the ceiling leaves it untouched and writes no range."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        bars = [_bar(ts0 + i * 60, 1_000 + i * 1_000) for i in range(5)]  # max 5000
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()

        ceiling_before = panel._volume_nice_max
        assert ceiling_before == pytest.approx(_nice_volume_max(5_000))   # 7500

        vb = panel.volume_plot.getViewBox()
        writes = []
        orig_set_range = vb.setRange

        def _spy(*args, **kwargs):
            writes.append((args, kwargs))
            return orig_set_range(*args, **kwargs)

        vb.setRange = _spy
        try:
            # Tick below the ceiling and below the cached running max.
            panel.update_last_bar(_bar(bars[-1].ts, 1_000), is_new_candle=False)
            qapp.processEvents()
        finally:
            vb.setRange = orig_set_range

        assert panel._volume_nice_max == pytest.approx(ceiling_before)
        assert writes == []
    finally:
        panel.hide()
        panel.close()


# ── T23-T04 / Load refresh ────────────────────────────────────────────────────
def test_cached_running_max_refreshed_on_load_and_new_bar(qapp):
    """update_chart and a new bar rebuild _vol_max to the O(N) max bar volume."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        vols = [1_000, 2_000, 3_000, 2_200_000]
        bars = [_bar(ts0 + i * 60, v) for i, v in enumerate(vols)]
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()
        assert panel._vol_max == pytest.approx(max(vols))

        new_vol = 4_500_000
        new_bar = _bar(bars[-1].ts + 60, new_vol)
        panel.update_last_bar(new_bar, is_new_candle=True)
        qapp.processEvents()

        assert panel._vol_max == pytest.approx(max(vols + [new_vol]))
        assert panel._vol_max == pytest.approx(max(b.volume for b in panel._bars))
    finally:
        panel.hide()
        panel.close()
