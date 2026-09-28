"""D8 volume axis tests.

The live volume nice-max comes from the single pinned family
``1 / 1.5 / 2 / 2.5 / 5 / 7.5 x 10^k`` (RG-002 / AC-D8.1), floored at ``100``
with no fixed ceiling. The old fixed ``[10k .. 10M]`` list is retained here
**only as a regression fixture** — it is never a live code path.
"""

import pytest

from ui.chart_panel import (
    ChartPanel,
    _format_volume_tick,
    _nice_volume_max,
    _volume_nice_family,
)
from data.models import Bar


# ── Legacy regression fixture (architecture §3.3) ─────────────────────────────
# The pre-RG-002 fixed list. Every entry is a member of the pinned family, so it
# stays valid as a fixture; it is never a live code path.
LEGACY_NICE_LIST = [
    10_000, 50_000, 100_000, 250_000, 500_000, 750_000,
    1_000_000, 1_500_000, 2_000_000, 2_500_000, 5_000_000, 10_000_000,
]

# Confirmed ``(max_vol -> nice_max)`` pairs the generator must reproduce.
CONFIRMED_MAPPINGS = [
    (8_000, 10_000),
    (80_000, 100_000),
    (2_200_000, 2_500_000),
    (1_050_000, 1_500_000),  # RG-002 contested case
]


def _bar(ts, vol, o=100, c=100):
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=o, high=101, low=99, close=c, volume=vol)


def _is_family_value(value: float) -> bool:
    return any(abs(value - member) <= 1e-6 * max(1.0, abs(value))
               for member in _volume_nice_family())


# ── T22-T01 — updated legacy expectations ─────────────────────────────────────
def test_T22_T01_updated_legacy_expectations():
    assert _nice_volume_max(0) == 100              # was 10_000; stale 10k floor removed
    assert _nice_volume_max(8_000) == 10_000
    assert _nice_volume_max(80_000) == 100_000
    assert _nice_volume_max(2_200_000) == 2_500_000
    assert _nice_volume_max(1_050_000) == 1_500_000


# ── T22-T02 — legacy fixture members + confirmed mappings ─────────────────────
def test_T22_T02_legacy_fixture_family_members_and_mappings():
    """Every legacy member/confirmed output is a family value; mappings hold.

    NOTE: ``_nice_volume_max(v) == v`` is impossible for every ``v > 0`` by
    design — the pinned margin (``>= v * 1.1``) always advances a positive
    family value to the next family value (architecture §3.2: ``10_000 ->
    15_000``). The fixture is therefore cross-checked as (a) family membership of
    every legacy member and confirmed output, and (b) reproduction of every
    confirmed legacy ``input -> output`` mapping.
    """
    for v in LEGACY_NICE_LIST:
        assert _is_family_value(v), f"{v} is not a member of the pinned family"
    for _src, expected in CONFIRMED_MAPPINGS:
        assert _is_family_value(expected)
    for src, expected in CONFIRMED_MAPPINGS:
        assert _nice_volume_max(src) == expected


# ── T22-T03 — large-volume family values, no coarse fallback/clamp ────────────
def test_T22_T03_large_volume_high_end():
    assert _nice_volume_max(10_500_000) == 15_000_000
    assert _nice_volume_max(45_000_000) == 50_000_000
    assert _nice_volume_max(50_000_000) == 75_000_000
    assert _nice_volume_max(50_000_000) != 100_000_000


# ── T22-T04 — fine low end, no 10k floor ──────────────────────────────────────
def test_T22_T04_fine_low_end_no_10k_floor():
    assert _nice_volume_max(0) == 100
    assert _nice_volume_max(800) == 1_000
    assert _nice_volume_max(3_000) == 5_000


# ── T22-T05 — monotonic sweep with tight coverage ─────────────────────────────
def test_T22_T05_sweep_monotonic_and_tight():
    sweep = []
    for decade in range(0, 9):          # 10^0 .. 10^8
        base = 10 ** decade
        sweep.extend(base * m for m in (1, 1.1, 1.5, 2, 2.2, 2.5, 3, 4, 5, 7.5, 9))
    sweep.extend([45.5, 45.6, 90, 90.9, 91, 1_050_000, 2_500_000, 54_999_999, 55_000_000])
    sweep = sorted(set(sweep))

    previous = 0.0
    for max_vol in sweep:
        nice = _nice_volume_max(max_vol)
        assert nice >= previous, f"not monotonic at {max_vol}"
        previous = nice
        if nice > 100.0:  # ceiling above the required 100 floor (PA-R8)
            assert nice / (max_vol * 1.1) <= 2.0 + 1e-9, f"ratio too loose at {max_vol}"


# ── T22-T06 — legacy list cross-check ─────────────────────────────────────────
def test_T22_T06_legacy_list_family_crosscheck():
    family = set(_volume_nice_family())
    for v in LEGACY_NICE_LIST:
        assert v in family, f"legacy member {v} missing from the pinned family"
        assert _nice_volume_max(v) in family  # generator is closed over the family


# ── T22-T07 — offscreen panel: linear, 0-based, nice-max ceiling ──────────────
def test_T22_T07_panel_linear_viewbox_nice_max(qapp):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    assert tuple(bool(x) for x in vb.state["logMode"]) == (False, False)

    bars = [_bar(1_700_000_000 + i * 60, 500_000 + i * 10_000) for i in range(10)]
    bars[-1] = _bar(1_700_000_900, 2_200_000)
    max_vol = max(b.volume for b in bars)
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()

    y_range = vb.viewRange()[1]
    assert y_range[0] == pytest.approx(0, abs=1)
    assert y_range[0] >= 0                       # no negative tick
    assert y_range[1] == pytest.approx(_nice_volume_max(max_vol), rel=0.02)
    panel.hide()
    panel.close()


# ── T22-T08 — tick formatter + price-coloured bars ────────────────────────────
def test_T22_T08_tick_formatter_and_price_colours(qapp):
    assert _format_volume_tick(500_000) == "500.0K"
    assert _format_volume_tick(1_000_000) == "1.0M"

    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    bars = [
        _bar(1_700_000_000, 1_000, o=95, c=105),      # up   -> green
        _bar(1_700_000_060, 1_000, o=105, c=95),       # down -> red
    ]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    brushes = panel.volume_bars.opts.get("brushes")
    assert list(brushes) == ["#34d399", "#f87171"]
    panel.hide()
    panel.close()


# ── Retained original tests ───────────────────────────────────────────────────
def test_volume_y_linear_no_negatives_nice_max(qapp):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    # Should be linear
    assert vb.state["logMode"] == [False, False] or vb.state["logMode"][1] is False
    # Create bars with max 2.2M
    bars = [_bar(1_700_000_000 + i * 60, 500_000 + i * 10_000) for i in range(10)]
    # Set max to 2.2M
    bars[-1] = _bar(1_700_000_900, 2_200_000)
    max_vol = max(b.volume for b in bars)
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    y_range = vb.viewRange()[1]
    assert y_range[0] == pytest.approx(0, abs=1)
    # Upper should be nice_max
    expected_nice = _nice_volume_max(max_vol)
    assert y_range[1] == pytest.approx(expected_nice, rel=0.02)
    # No negative tick
    assert y_range[0] >= 0
    panel.hide()
    panel.close()


def test_volume_bars_coloured_by_price(qapp):
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    # Create up and down candles
    bars = [
        _bar(1_700_000_000, 1000, o=95, c=105),   # up -> green
        _bar(1_700_000_060, 1000, o=105, c=95),   # down -> red
    ]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    assert len(panel._bars) == 2
    assert list(panel.volume_bars.opts.get("brushes")) == ["#34d399", "#f87171"]
    panel.hide()
    panel.close()


def test_volume_ticks_formatting(qapp):
    # Test nice_max logic directly
    assert _nice_volume_max(0) == 100
    assert _nice_volume_max(8_000) == 10_000
    assert _nice_volume_max(80_000) == 100_000
    assert _nice_volume_max(2_200_000) == 2_500_000
    assert _nice_volume_max(1_050_000) == 1_500_000
    # Check that yRange lower is 0 for various max
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    bars = [_bar(1_700_000_000 + i * 60, 10_000) for i in range(5)]
    panel.set_symbol("TEST")
    panel.update_chart(bars)
    qapp.processEvents()
    vb = panel.volume_plot.getViewBox()
    y_range = vb.viewRange()[1]
    assert y_range[0] == pytest.approx(0, abs=1)
    panel.hide()
    panel.close()
