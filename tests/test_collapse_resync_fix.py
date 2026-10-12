"""Fix-A (review): overlays must track the rebuilt collapse map on live bars.

When ``update_last_bar`` appends a new bar it rebuilds the collapse map.
Every overlay that renders at display-x (drawings, alarms, RTH-gap / VIX /
ICT studies) must then hold the NEW map object — otherwise ``to_display``
extrapolates unknown timestamps and elements render far off-screen across
collapsed gaps until the next full refresh.
"""

from __future__ import annotations

from data.models import Bar


def _bar(ts: int, value: float) -> Bar:
    return Bar(
        symbol="TEST",
        timeframe="5 mins",
        ts=ts,
        open=value,
        high=value + 0.5,
        low=value - 0.5,
        close=value,
        volume=1000.0,
    )


def test_update_last_bar_resyncs_overlay_collapse_map(chart_panel, sample_bars, qapp):
    chart_panel.set_timeframe("5 mins")
    chart_panel.update_chart(sample_bars)
    qapp.processEvents()
    old_map = chart_panel._collapse_map
    assert old_map is not None

    last = sample_bars[-1]
    chart_panel.update_last_bar(_bar(last.ts + 300, last.close + 1.0), is_new_candle=True)
    qapp.processEvents()

    new_map = chart_panel._collapse_map
    assert new_map is not old_map, "expected the collapse map to be rebuilt on a new bar"

    # Every display-x consumer must hold the NEW map, not the stale one.
    assert chart_panel.drawing_overlay._collapse_map is new_map
    assert chart_panel.alarm_overlay._collapse_map is new_map
    for overlay in (
        chart_panel._gap_overlay,
        chart_panel._vix_overlay,
        chart_panel._ict_overlay,
    ):
        assert overlay._collapse_map is new_map

    # Functional check: the overlay's map resolves the new bar's timestamp to
    # the same on-screen x as the panel's own map (no extrapolation drift).
    ts = last.ts + 300
    assert (
        chart_panel.drawing_overlay._collapse_map.to_display(ts)
        == new_map.to_display(ts)
    )
