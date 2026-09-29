"""T13 / D9 — the volume bar width must follow the *rendered* price body width.

``AC-D9.1`` / ``AC-D9.2`` require that the volume ``BarGraphItem`` width equals
the price candle body width (``w*2``, 35% gap) at every zoom, including the
dense-view 4 device-pixel body minimum.

ESC-021: an earlier version of this file re-derived the expected body width in a
test helper that duplicated the production candle formula
(``median_diff * 0.325``, ``min_w = 2.0 / px_per_sec``).  Such a test can only
detect a *volume-side* regression — a drift applied to the candle formula alone
still passed.  The expected value is now **measured from the rendered
``CandlestickItem``** (the recorded ``QPicture`` bounding rect), exactly as
``tests/test_chart_dpi.py::body_geometry`` does, so candle-side drift is caught
too.  No production formula is repeated in this file.
"""

import pytest
from ui.chart_panel import ChartPanel
from data.models import Bar


def _bar(ts, vol, o=100, c=100):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=101, low=99, close=c, volume=vol)


def _measured_body_width(panel, bars):
    """Full price-candle body width in data units, measured from the render.

    Reads the ``CandlestickItem``'s recorded ``QPicture`` bounding rect.
    Bodies span ``[t - w, t + w]`` for every bar and wicks sit at ``x == t``, so
    the picture width is ``(t_last - t0) + 2w + pen_inflation``.  Subtracting
    the timestamp span therefore recovers the full body width plus a small
    constant cosmetic-pen inflation (~1 data unit).  ``QPicture.boundingRect()``
    is integer-quantised, so the caller allows ``rel=0.02``.
    """
    pic = panel.candlestick.boundingRect()
    data_span = bars[-1].ts - bars[0].ts
    return pic.width() - data_span


def _px_per_sec(panel):
    """Horizontal data-units-per-second scale of the *final* applied view range."""
    vb = panel.price_plot.getViewBox()
    x0, x1 = vb.viewRange()[0]
    return vb.width() / (x1 - x0)


def test_volume_width_equals_price_width(qapp):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i * 300, 1000) for i in range(20)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()

    vol_width = panel.volume_bars.opts['width']

    # AC-D9.1 / ESC-021: expected width comes from the rendered candle body,
    # NOT from a re-derivation of median_diff*0.325.  In this non-dense view the
    # 4-px minimum does not bind, so this assertion also catches candle-side
    # drift (e.g. a narrowed candle body) that the old formula-mirror missed.
    measured_body = _measured_body_width(panel, bars)
    assert vol_width == pytest.approx(measured_body, rel=0.02)

    # Same gap as the price panel: identical data width => identical pixel width.
    px_per_sec = _px_per_sec(panel)
    assert vol_width * px_per_sec == pytest.approx(measured_body * px_per_sec, rel=0.02)

    # Not the old fixed 0.6 width.
    assert vol_width != pytest.approx(0.6, rel=0.01)

    panel.hide()
    panel.close()


def test_volume_width_dense_clamped(qapp):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i * 60, 1000) for i in range(960)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()

    vol_width = panel.volume_bars.opts['width']

    # AC-D9.2 / ESC-020 / ESC-021: in this dense 1-min view the 4px body minimum
    # fires, and the volume bar must follow the *same clamped* w as the rendered
    # price body.  The expected value is measured from the candle QPicture at the
    # FINAL view range — computing w_vol before `setRange` (the pre-fix ordering)
    # yields the unclamped 39 data units instead and fails the equality below.
    measured_body = _measured_body_width(panel, bars)
    px_per_sec = _px_per_sec(panel)
    assert vol_width == pytest.approx(measured_body, rel=0.02)

    # The dense-view minimum genuinely binds at ~4 device px for both body and bar.
    assert measured_body * px_per_sec == pytest.approx(4.0, rel=0.05)
    assert vol_width * px_per_sec == pytest.approx(4.0, rel=0.05)

    # Regress against the old fixed width and the unclamped (pre-fix) value 39.
    assert vol_width != pytest.approx(0.6, rel=0.01)
    assert vol_width != pytest.approx(39.0, rel=0.01)

    panel.hide()
    panel.close()
