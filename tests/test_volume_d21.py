"""D21 volume pane tests.

D21.1 / AC-D21.1.1 — volume Y minimum is hard-clamped at 0.

Pre-fix red: without the ``setLimits(yMin=0)`` bound on the volume ViewBox,
pyqtgraph's default interaction lets a downward y-interaction push
``viewRange()[1][0]`` below 0 and renders negative volume-axis ticks. Post-fix
green: every range change routed through ``ViewBox.setRange`` — the path taken
by ``translateBy`` (mouse y-drag), ``scaleBy`` (wheel zoom) and programmatic
writes — is clamped so the volume Y minimum never goes below 0.

The bound is a *limit*, not a range write, so the D21.2 programmatic
``setRange(yRange=(0, ceiling))`` in ``_recompute_visible_volume_range`` and the
all-zero ``[0, 100]`` floor are preserved unchanged.

D21.2 / AC-D21.2.1 — the volume Y ceiling is ``1.10 x max(volume of the bars
whose x lies in the visible x-range)``, recomputed on every visible-x change and
every bar update. This supersedes D8's whole-list nice-max ceiling and ESC-007's
only-widen rule for zoom while preserving ESC-007's forming-bar no-clip intent.

D21.6 / AC-D21.6.1 — the volume pane can grow to at least 360px (3x the former
120px cap) while the price pane keeps a ~200px floor. Pre-fix red: the volume
pane was capped at 120px, so the price/volume splitter could never give it 360.
Post-fix green: ``volume_plot`` is capped at ``VOLUME_PANE_MAX_HEIGHT`` (480) and
``price_plot`` floored at ``PRICE_PANE_MIN_HEIGHT`` (200); the oscillator pane
cap is unchanged at 120px.
"""

import pytest

from ui.chart_panel import (
    ChartPanel,
    PRICE_PANE_MIN_HEIGHT,
    VOLUME_PANE_MAX_HEIGHT,
)
from data.models import Bar


def _bar(ts, vol, o=100, c=100, high=101, low=99):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=high,
               low=low, close=c, volume=vol)


def _default_bars():
    ts0 = 1_700_000_000
    return [_bar(ts0 + i * 60, 1_000 + i * 500) for i in range(10)]


def _make_panel(qapp, bars):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    return panel


def _vol_y(panel):
    return panel.volume_plot.getViewBox().viewRange()[1]


def _negative_volume_ticks(panel):
    """Return any rendered volume-axis tick value below 0."""
    axis = panel.volume_plot.getAxis('right')
    y0, y1 = _vol_y(panel)
    size = max(panel.volume_plot.height(), 100)
    ticks = axis.tickValues(y0, y1, size)
    values = [v for _spacing, vals in ticks for v in vals]
    return [v for v in values if v < 0]


# ── D21-01-T01 / AC-D21.1.1 ───────────────────────────────────────────────────
def test_D21_01_T01_volume_y_min_clamped_on_interactive_y_change(qapp):
    """A downward y-interaction can never move the volume Y minimum below 0."""
    panel = _make_panel(qapp, _default_bars())
    try:
        vb = panel.volume_plot.getViewBox()

        # The volume ViewBox carries the hard lower bound.
        assert vb.state['limits']['yLimits'][0] == 0

        # Mouse y-drag → ViewBox.translateBy (downward = negative y).
        vb.translateBy(y=-10_000)
        qapp.processEvents()
        assert _vol_y(panel)[0] >= -1e-9

        # Wheel zoom-out → ViewBox.scaleBy around a high centre (pushes the
        # bottom edge negative without a limit).
        vb.scaleBy(y=2.0, center=(0, _vol_y(panel)[1]))
        qapp.processEvents()
        assert _vol_y(panel)[0] >= -1e-9

        # A bounded-path range write with yMin < 0 — the same ``setRange``
        # route every interactive change takes — is clamped too.
        vb.setRange(yRange=(-5_000, 5_000), padding=0)
        qapp.processEvents()
        assert _vol_y(panel)[0] >= -1e-9

        # No negative volume-axis tick is rendered.
        assert _negative_volume_ticks(panel) == []
    finally:
        panel.hide()
        panel.close()


# ── D21-01-T02 / AC-D21.1.1 ───────────────────────────────────────────────────
def test_D21_01_T02_all_zero_floor_reload_and_max_draggable(qapp):
    """All-zero keeps [0, 100]; reload re-applies min 0; drags saturate at 0
    while the y-drag remains usable for the max."""
    ts0 = 1_700_000_000
    zero_bars = [_bar(ts0 + i * 60, 0.0) for i in range(5)]
    panel = _make_panel(qapp, zero_bars)
    try:
        vb = panel.volume_plot.getViewBox()

        # D8 all-zero floor: [0, 100].
        assert _vol_y(panel)[0] == pytest.approx(0, abs=1e-9)
        assert _vol_y(panel)[1] == pytest.approx(100.0, rel=1e-6)

        # Repeated downward drags saturate at 0.
        for _ in range(3):
            vb.translateBy(y=-10_000)
            qapp.processEvents()
            assert _vol_y(panel)[0] >= -1e-9
        assert _vol_y(panel)[0] == pytest.approx(0, abs=1e-6)

        # A symbol / timeframe switch re-applies min 0 (limit persists on the
        # ViewBox; the programmatic ceiling write stays inside it).
        panel.set_symbol("OTHER")
        panel.set_timeframe("15 mins")
        panel.update_chart(_default_bars())
        qapp.processEvents()
        assert vb.state['limits']['yLimits'][0] == 0
        assert _vol_y(panel)[0] == pytest.approx(0, abs=1e-6)
        assert _vol_y(panel)[1] > 0

        # The y-drag is still usable for the max: an upward drag raises the
        # top while the min never drops below 0.
        before_top = _vol_y(panel)[1]
        vb.translateBy(y=1_000)
        qapp.processEvents()
        assert _vol_y(panel)[1] > before_top
        assert _vol_y(panel)[0] >= -1e-9
        assert _negative_volume_ticks(panel) == []
    finally:
        panel.hide()
        panel.close()


# ── D21-02-T01 / AC-D21.2.1 ───────────────────────────────────────────────────
def test_D21_02_T01_ceiling_tracks_visible_max_both_directions(qapp):
    """The ceiling equals 1.10 x the visible max and follows zoom both ways."""
    ts0 = 1_700_000_000
    vols = [100, 200, 300, 400, 5_000, 6_000, 7_000]
    bars = [_bar(ts0 + i * 60, v) for i, v in enumerate(vols)]
    panel = _make_panel(qapp, bars)
    try:
        pvb = panel.price_plot.getViewBox()

        # Visible over the low-volume region only.
        pvb.setRange(xRange=(ts0 - 30, ts0 + 3 * 60 + 30), padding=0)
        qapp.processEvents()
        low_max = max(vols[:4])                       # 400
        assert _vol_y(panel)[0] == pytest.approx(0, abs=1e-6)
        assert _vol_y(panel)[1] == pytest.approx(1.10 * low_max, rel=1e-6)

        # Widen to the whole set -> ceiling rises to 1.10 x the global max.
        pvb.setRange(xRange=(ts0 - 30, ts0 + 6 * 60 + 30), padding=0)
        qapp.processEvents()
        assert _vol_y(panel)[1] == pytest.approx(1.10 * max(vols), rel=1e-6)

        # Zoom back into the low-volume region -> the ceiling LOWERS
        # (not the superseded only-widen behaviour).
        pvb.setRange(xRange=(ts0 - 30, ts0 + 3 * 60 + 30), padding=0)
        qapp.processEvents()
        assert _vol_y(panel)[1] == pytest.approx(1.10 * low_max, rel=1e-6)
        assert _vol_y(panel)[1] < 1.10 * max(vols)
    finally:
        panel.hide()
        panel.close()


# ── D21-02-T02 / AC-D21.2.1 ───────────────────────────────────────────────────
def test_D21_02_T02_zero_floor_out_of_view_spike_and_pan(qapp):
    """All-zero visible -> [0, 100]; an out-of-view spike does not inflate;
    panning recomputes the ceiling."""
    ts0 = 1_700_000_000
    vols = [0, 0, 0, 0, 9_000_000]
    bars = [_bar(ts0 + i * 60, v) for i, v in enumerate(vols)]
    panel = _make_panel(qapp, bars)
    try:
        pvb = panel.price_plot.getViewBox()

        # View only the all-zero region: the spike (ts0+240) is out of view.
        pvb.setRange(xRange=(ts0 - 30, ts0 + 3 * 60 + 30), padding=0)
        qapp.processEvents()
        assert _vol_y(panel)[0] == pytest.approx(0, abs=1e-6)
        assert _vol_y(panel)[1] == pytest.approx(100.0, rel=1e-6)

        # Pan to include the spike -> ceiling follows the newly visible max.
        pvb.setRange(xRange=(ts0 + 3 * 60 - 30, ts0 + 4 * 60 + 30), padding=0)
        qapp.processEvents()
        assert _vol_y(panel)[1] == pytest.approx(1.10 * 9_000_000, rel=1e-6)

        # Pan back to the all-zero region -> floor again.
        pvb.setRange(xRange=(ts0 - 30, ts0 + 3 * 60 + 30), padding=0)
        qapp.processEvents()
        assert _vol_y(panel)[1] == pytest.approx(100.0, rel=1e-6)
    finally:
        panel.hide()
        panel.close()


# ── D21-02-T03 / AC-D21.2.1 ───────────────────────────────────────────────────
def test_D21_02_T03_forming_bar_growth_widens_ceiling(qapp):
    """A forming last bar growing past the ceiling widens it (no clipping)."""
    ts0 = 1_700_000_000
    vols = [1_000, 1_200, 1_400]
    bars = [_bar(ts0 + i * 60, v) for i, v in enumerate(vols)]
    panel = _make_panel(qapp, bars)
    try:
        pvb = panel.price_plot.getViewBox()
        pvb.setRange(xRange=(ts0 - 30, ts0 + 2 * 60 + 30), padding=0)
        qapp.processEvents()
        before = _vol_y(panel)[1]
        assert before == pytest.approx(1.10 * 1_400, rel=1e-6)

        # Intra-bar growth of the forming (last) bar past the current ceiling.
        grown = 20_000
        panel.update_last_bar(_bar(ts0 + 2 * 60, grown), is_new_candle=False)
        qapp.processEvents()
        after = _vol_y(panel)[1]
        assert after == pytest.approx(1.10 * grown, rel=1e-6)
        assert after > before
        assert grown <= after                    # forming bar is not clipped
    finally:
        panel.hide()
        panel.close()


# ── D21-02-T05 / AC-D21.2.1 (ESC-028 regression) ──────────────────────────────
def test_D21_02_T05_small_nonzero_visible_max_not_floored(qapp):
    """ESC-028: a small *non-zero* visible max must use the literal 1.10 x max.

    The ``[0, 100]`` floor is reserved for the 0-visible case; an unconditional
    second ``< VOLUME_NICE_FLOOR`` clamp would wrongly inflate a visible max of
    10 to a ceiling of 100. This is the regression band the original T01
    (low_max=400) and T02 (all-zero) never exercised. Values are chosen on both
    sides of the 90.909 boundary (where 1.10 x max crosses the 100 floor).
    """
    ts0 = 1_700_000_000
    for visible_max, expected in ((10, 11.0), (50, 55.0), (90, 99.0), (100, 110.0)):
        vols = [1.0, float(visible_max), 2.0]
        bars = [_bar(ts0 + i * 60, v) for i, v in enumerate(vols)]
        panel = _make_panel(qapp, bars)
        try:
            pvb = panel.price_plot.getViewBox()
            pvb.setRange(xRange=(ts0 - 30, ts0 + 2 * 60 + 30), padding=0)
            qapp.processEvents()
            assert _vol_y(panel)[0] == pytest.approx(0, abs=1e-6)
            assert _vol_y(panel)[1] == pytest.approx(expected, rel=1e-6), (
                f"visible_max={visible_max} should give [0, {expected}], "
                f"got {_vol_y(panel)[1]!r} (ESC-028 floor regression)"
            )
            if visible_max <= 90:
                # Explicitly pin the bug: a positive max must not be floored.
                assert _vol_y(panel)[1] != pytest.approx(100.0, rel=1e-6)
        finally:
            panel.hide()
            panel.close()


# ── D21-02-T04 / AC-D21.2.1 (R36) ─────────────────────────────────────────────
def test_D21_02_T04_lockstep_modules_encode_d21_rule():
    """The D8/ESC-007 lockstep modules encode D21.2, not the superseded rule.

    Zero failures in the three modules is verified by running them directly (see
    the task log); this guard pins the *content* requirement — no remaining
    assertion of the D8 nice-max panel ceiling or the ESC-007 only-widen rule.
    ``_nice_volume_max`` is retained only as the pinned-family / all-zero-floor
    fixture and is still exercised directly in ``test_volume_linear.py``.
    """
    import pathlib
    tests_dir = pathlib.Path(__file__).resolve().parent
    modules = ("test_volume_linear.py", "test_volume_log.py", "test_volume_ceiling.py")
    for name in modules:
        src = (tests_dir / name).read_text(encoding="utf-8")
        # A panel view-range / applied-ceiling assertion must not use the D8
        # nice-max helper; ``_nice_volume_max`` is retained only for the
        # pure-function family fixtures, which never mention the view range.
        for line in src.splitlines():
            if "y_range" in line or "_volume_nice_max" in line:
                assert "_nice_volume_max" not in line, (
                    f"{name} still asserts the D8 nice-max as the panel ceiling: "
                    f"{line.strip()!r}"
                )


# ── D21-03-T01 / AC-D21.6.1 ───────────────────────────────────────────────────
def test_D21_03_T01_volume_pane_reaches_360(qapp):
    """The volume pane can grow to >= 360px (3x the former 120px cap)."""
    panel = ChartPanel()
    panel.resize(900, 900)
    panel.show()
    qapp.processEvents()
    try:
        # The former 120px cap is replaced by the 480px ceiling.
        assert panel.volume_plot.maximumHeight() == VOLUME_PANE_MAX_HEIGHT
        assert VOLUME_PANE_MAX_HEIGHT >= 360

        # Drive the vertical price/volume splitter to give the volume pane its
        # maximum (equivalent to dragging the price/volume handle all the way
        # up: price shrinks to its floor, volume grows to its ceiling).
        panel._splitter.setSizes(
            [PRICE_PANE_MIN_HEIGHT, VOLUME_PANE_MAX_HEIGHT, 120]
        )
        qapp.processEvents()

        assert panel.volume_plot.height() >= 360
        # The new cap still binds — a drag cannot grow volume past the maximum.
        assert panel.volume_plot.height() <= VOLUME_PANE_MAX_HEIGHT
    finally:
        panel.hide()
        panel.close()


# ── D21-03-T02 / AC-D21.6.1 ───────────────────────────────────────────────────
def test_D21_03_T02_price_minimum_holds_and_short_window_yields(qapp):
    """Price keeps >= ~200px when volume grows; in a short window the price
    minimum wins and the volume target yields without an error."""
    # Tall window: growing volume to its maximum leaves price above its floor.
    panel = ChartPanel()
    panel.resize(900, 900)
    panel.show()
    qapp.processEvents()
    try:
        assert panel.price_plot.minimumHeight() == PRICE_PANE_MIN_HEIGHT
        panel._splitter.setSizes(
            [PRICE_PANE_MIN_HEIGHT, VOLUME_PANE_MAX_HEIGHT, 120]
        )
        qapp.processEvents()
        assert panel.volume_plot.height() >= 360
        assert panel.price_plot.height() >= PRICE_PANE_MIN_HEIGHT - 2
    finally:
        panel.hide()
        panel.close()

    # Very short window: the price minimum wins, the volume target yields, and
    # no error is raised.
    short = ChartPanel()
    short.resize(900, 300)
    short.show()
    qapp.processEvents()
    try:
        short._splitter.setSizes(
            [PRICE_PANE_MIN_HEIGHT, VOLUME_PANE_MAX_HEIGHT, 120]
        )
        qapp.processEvents()
        assert short.price_plot.height() >= PRICE_PANE_MIN_HEIGHT - 2
        assert short.volume_plot.height() < 360
    finally:
        short.hide()
        short.close()


# ── D21-03-T03 / AC-D21.6.1 ───────────────────────────────────────────────────
def test_D21_03_T03_oscillator_unaffected_and_hide_show_roundtrip(qapp):
    """The oscillator pane cap is unchanged, and hiding then showing the volume
    pane (D10) restores the splitter without regressing the price minimum."""
    panel = ChartPanel()
    panel.resize(900, 900)
    panel.show()
    qapp.processEvents()
    try:
        # The oscillator pane cap is intentionally left unchanged at 120px.
        assert panel.osc_plot.maximumHeight() == 120

        panel._splitter.setSizes(
            [PRICE_PANE_MIN_HEIGHT, VOLUME_PANE_MAX_HEIGHT, 120]
        )
        qapp.processEvents()
        grown = panel._splitter.sizes()
        assert panel.volume_plot.height() >= 360

        # D10: hide then show the volume pane round-trips cleanly.
        panel._volume_toggle.setChecked(False)
        qapp.processEvents()
        assert not panel.volume_plot.isVisible()

        panel._volume_toggle.setChecked(True)
        qapp.processEvents()
        assert panel.volume_plot.isVisible()
        assert panel._splitter.sizes() == grown
        # No price-minimum regression after the round-trip.
        assert panel.price_plot.height() >= PRICE_PANE_MIN_HEIGHT - 2
        assert panel.volume_plot.height() >= 360
    finally:
        panel.hide()
        panel.close()

