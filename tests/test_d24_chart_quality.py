"""Q-4 — the rendered candle body must follow the CURRENT view range.

This is the guard the earlier passes (D6, D28.4, D42, ESC-013/T32) never had.
Every one of them fixed *generation-time* ordering, so a fresh load always
looked right; none of them regenerated the picture on a **range change**, so a
chart loaded while the 4-px floor was binding kept a body width of one full
pitch in data units. Zooming in scaled that width with the geometry: the
candles touched at every zoom level until the next data refresh.

The tests below therefore measure the picture that is actually baked
(``CandlestickItem.last_body_half_width``) after a real ViewBox range change,
not just after ``update_chart``.
"""
import pytest
from PyQt6.QtTest import QTest

from data.models import Bar
from ui.chart_panel import CANDLE_WIDTH_RESYNC_MS, ChartPanel

BASE = 1_760_000_000
SPACING = 300


def _bar(i, px=None):
    p = (100.0 + (i % 10) * 0.1) if px is None else px
    return Bar("TEST", "5 mins", BASE + i * SPACING,
               p, p + 1.0, p - 1.0, p + 0.5, 1_000.0)


@pytest.fixture
def panel(qapp):
    p = ChartPanel()
    p.set_timeframe("5 mins")
    p.resize(900, 600)
    p.show()
    qapp.processEvents()
    yield p
    p.hide()
    p.close()


def _settle(qapp):
    """Wait past the debounce so the range-change re-apply has run."""
    QTest.qWait(CANDLE_WIDTH_RESYNC_MS + 80)
    qapp.processEvents()


def _measure(panel):
    """Return (body_px, pitch_px) for what is baked into the picture.

    ``last_body_half_width`` is the data-unit half-width the last generated
    QPicture actually drew with; ``_candle_median_diff`` is the data-unit bar
    spacing. Scaling both by the current view gives the logical-pixel geometry
    the user sees, which is what the invariant is stated in.
    """
    px_per_sec = panel._view_px_per_sec()
    assert px_per_sec, "the panel must be laid out for a measurable pitch"
    spacing = panel._candle_median_diff
    half = panel.candlestick.last_body_half_width
    return 2.0 * half * px_per_sec, spacing * px_per_sec


def test_zoom_in_after_dense_load_leaves_a_visible_gap(panel, qapp):
    """Load dense (floor binds) -> zoom to a wide pitch -> gap must reappear."""
    panel.update_chart([_bar(i) for i in range(3000)])
    qapp.processEvents()

    # Dense load: the 4-px floor cannot fit, so the body fills the sub-pixel
    # pitch. Touching here is the accepted high-density regime.
    body_dense, pitch_dense = _measure(panel)
    assert pitch_dense < 6.0, "fixture must force the dense clamp"
    assert body_dense <= pitch_dense * 1.001, \
        "body must never exceed the pitch, even at high density"

    # Zoom the ViewBox in to ~60 bars (pitch comfortably above the floor) and
    # let the debounced re-apply run. This is the step that was missing.
    bars = panel._plotted_bars
    x0 = panel._to_display(bars[-60].ts)
    x1 = panel._to_display(bars[-1].ts)
    panel.candlestick.regen_count = 0
    panel.price_plot.getViewBox().setRange(xRange=(x0, x1), padding=0)
    qapp.processEvents()
    _settle(qapp)

    body, pitch = _measure(panel)
    assert pitch >= 6.0, "zoomed-in pitch must clear the 4-px floor"
    assert panel.candlestick.regen_count == 1, (
        "the settled range change must regenerate the picture exactly once "
        "(not once per wheel step, not never)")
    assert body <= 0.7 * pitch, (
        f"body/pitch = {body / pitch:.3f} (body {body:.1f}px of {pitch:.1f}px) "
        "— a visible gap is required at any zoom")
    assert pitch - body >= 0.3 * pitch, (
        f"gap = {pitch - body:.1f}px of {pitch:.1f}px — required >= 30%")


def test_zoom_out_to_dense_keeps_the_legibility_floor(panel, qapp):
    """Zooming out must re-apply the 4-px floor instead of a hairline body."""
    panel.update_chart([_bar(i) for i in range(3000)])
    qapp.processEvents()

    bars = panel._plotted_bars
    x0 = panel._to_display(bars[-60].ts)
    x1 = panel._to_display(bars[-1].ts)
    panel.price_plot.getViewBox().setRange(xRange=(x0, x1), padding=0)
    _settle(qapp)
    body_wide, pitch_wide = _measure(panel)
    assert pitch_wide >= 6.0
    assert body_wide <= 0.7 * pitch_wide

    # Back out to the whole series: the pitch collapses, the body must follow
    # it down (never wider than the pitch) rather than staying at the wide
    # zoom's fraction-of-pitch pixel size.
    xw0 = panel._to_display(bars[0].ts)
    xw1 = panel._to_display(bars[-1].ts)
    panel.price_plot.getViewBox().setRange(xRange=(xw0, xw1), padding=0)
    _settle(qapp)
    body_dense, pitch_dense = _measure(panel)
    assert pitch_dense < 6.0
    assert body_dense <= pitch_dense * 1.001


def test_pan_does_not_regenerate_the_picture(panel, qapp):
    """A same-span pan changes no width, so it must not regenerate anything."""
    panel.update_chart([_bar(i) for i in range(3000)])
    qapp.processEvents()

    # Settle at a zoom where the cap is *not* saturated (pitch ~14 px, body
    # 65 % of pitch), so a stale pixel-based pitch would actually show up.
    bars = panel._plotted_bars
    x0 = panel._to_display(bars[-80].ts)
    x1 = panel._to_display(bars[-20].ts)
    panel.price_plot.getViewBox().setRange(xRange=(x0, x1), padding=0)
    _settle(qapp)
    body, pitch = _measure(panel)
    assert body == pytest.approx(0.65 * pitch, rel=0.03)

    # Pan by 20 bars, same span -> identical pitch, identical body width.
    panel.candlestick.regen_count = 0
    panel.live_candle.regen_count = 0
    shift = panel._to_display(bars[-20].ts) - panel._to_display(bars[-40].ts)
    panel.price_plot.getViewBox().setRange(xRange=(x0 - shift, x1 - shift), padding=0)
    qapp.processEvents()
    _settle(qapp)

    assert panel.candlestick.regen_count == 0, \
        "panning must not regenerate the static candle picture"
    assert panel.live_candle.regen_count == 0, \
        "panning must not regenerate the live candle picture"


def test_volume_width_matches_candle_body_after_zoom(panel, qapp):
    """Volume bars stay consistent with the candle bodies after a range change."""
    panel.update_chart([_bar(i) for i in range(3000)])
    qapp.processEvents()

    bars = panel._plotted_bars
    x0 = panel._to_display(bars[-60].ts)
    x1 = panel._to_display(bars[-1].ts)
    panel.price_plot.getViewBox().setRange(xRange=(x0, x1), padding=0)
    _settle(qapp)

    body, pitch = _measure(panel)
    vol_width = float(panel.volume_bars.opts['width'])
    assert vol_width == pytest.approx(2.0 * panel._rendered_candle_half_width)
    px_per_sec = panel._view_px_per_sec()
    assert vol_width * px_per_sec == pytest.approx(body, rel=1e-6)
    assert body <= 0.7 * pitch
