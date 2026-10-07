"""D21.2 / AC-D21.2.1 — live volume ceiling tests.

Supersedes ESC-007 / AC-D8.6, AC-D8.7 for the live panel ceiling.

The forming (last) bar's volume grows live, so the volume Y ceiling must track
it without clipping. Under D21.2 the ceiling is ``1.10 x max(volume of the bars
in the visible x-range)``, recomputed on every visible-x change and on every bar
update. The D8 whole-list nice-max ceiling and ESC-007's only-widen rule for
zoom are superseded; a bar update that does not change the visible max still
performs no range write (the range is written only when the ceiling changes).
"""

import pytest

from ui.chart_panel import ChartPanel
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


# ── T23-T01 / AC-D21.2.1 ──────────────────────────────────────────────────────
def test_volume_ceiling_tracks_live_bar(qapp):
    """A live intra-bar tick past the current visible ceiling widens it."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        bars = [_bar(ts0 + i * 60, 100 + i * 50) for i in range(5)]
        bars[-1] = _bar(ts0 + 4 * 60, 800)          # load-time max volume = 800
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()

        vb = panel.volume_plot.getViewBox()
        load_ceiling = 800 * 1.1                     # 880
        assert panel._volume_nice_max == pytest.approx(load_ceiling, rel=1e-6)
        assert vb.viewRange()[1][1] == pytest.approx(load_ceiling, rel=0.02)

        # Intra-bar tick on the same (last) bar — no full reload.
        live_vol = 5_000
        live_ceiling = live_vol * 1.1                # 5500
        assert live_ceiling > load_ceiling
        panel.update_last_bar(_bar(bars[-1].ts, live_vol), is_new_candle=False)
        qapp.processEvents()

        assert panel._volume_nice_max == pytest.approx(live_ceiling, rel=1e-6)
        upper = vb.viewRange()[1][1]
        assert upper == pytest.approx(live_ceiling, rel=0.02)
        # Forming bar is not clipped: its volume sits under the pane top (> 0).
        assert 0 < live_vol <= upper
    finally:
        panel.hide()
        panel.close()


# ── T23-T02 / AC-D21.2.1 (was AC-D8.7) ────────────────────────────────────────
def test_volume_ceiling_refit_on_timezone_refresh(qapp):
    """set_timezone() re-applies the visible ceiling rather than going stale."""
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
        widened = 5_000 * 1.1                        # 5500
        assert panel._volume_nice_max == pytest.approx(widened, rel=1e-6)

        panel.set_timezone(18_000)
        qapp.processEvents()

        vb = panel.volume_plot.getViewBox()
        assert panel._volume_nice_max == pytest.approx(widened, rel=1e-6)
        assert vb.viewRange()[1][1] == pytest.approx(widened, rel=0.02)
        assert vb.viewRange()[1][0] == pytest.approx(0, abs=1)
    finally:
        panel.hide()
        panel.close()


# ── T23-T03 / no-op bar update (not only-widen) ───────────────────────────────
def test_non_crossing_tick_performs_no_range_write(qapp):
    """A tick that leaves the visible max unchanged writes no range."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        # The last bar is NOT the visible max, so a tick on it stays below it.
        bars = [_bar(ts0 + i * 60, 5_000 - i * 1_000) for i in range(5)]
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()

        ceiling_before = panel._volume_nice_max
        assert ceiling_before == pytest.approx(5_000 * 1.1, rel=1e-6)   # 5500

        vb = panel.volume_plot.getViewBox()
        writes = []
        orig_set_range = vb.setRange

        def _spy(*args, **kwargs):
            writes.append((args, kwargs))
            return orig_set_range(*args, **kwargs)

        vb.setRange = _spy
        try:
            # Tick below the visible max (5_000) and the ceiling.
            panel.update_last_bar(_bar(bars[-1].ts, 1_500), is_new_candle=False)
            qapp.processEvents()
        finally:
            vb.setRange = orig_set_range

        assert panel._volume_nice_max == pytest.approx(ceiling_before, rel=1e-6)
        assert writes == []
    finally:
        panel.hide()
        panel.close()


# ── T23-T04 / Load refresh ────────────────────────────────────────────────────
def test_visible_ceiling_refreshed_on_load_and_new_bar(qapp):
    """update_chart and a new bar recompute the visible ceiling (D21.2)."""
    panel = _make_panel(qapp)
    try:
        ts0 = 1_700_000_000
        vols = [1_000, 2_000, 3_000, 2_200_000]
        bars = [_bar(ts0 + i * 60, v) for i, v in enumerate(vols)]
        panel.set_symbol("TEST")
        panel.update_chart(bars)
        qapp.processEvents()
        assert panel._volume_nice_max == pytest.approx(2_200_000 * 1.1, rel=1e-6)

        new_vol = 4_500_000
        new_bar = _bar(bars[-1].ts + 60, new_vol)
        panel.update_last_bar(new_bar, is_new_candle=True)
        qapp.processEvents()
        assert panel._volume_nice_max == pytest.approx(new_vol * 1.1, rel=1e-6)
        assert panel._volume_nice_max == pytest.approx(
            1.1 * max(b.volume for b in panel._bars), rel=1e-6
        )
    finally:
        panel.hide()
        panel.close()
