"""D28.4 (4b-4) — incremental collapse-map tail updates.

Appending a new bar must extend the TimeCollapseMap at the tail instead
of rebuilding it: extend() must agree exactly with a fresh
build_collapse_map(), and the panel's new-candle path must not call the
full rebuild.
"""
from data.models import Bar
from services.time_collapse_service import build_collapse_map
from ui.chart_panel import ChartPanel

BASE = 1_760_000_000


def _bar(i, spacing=300):
    return Bar("TEST", "5 mins", BASE + i * spacing,
               100.0, 101.0, 99.0, 100.5, 1000.0)


def _check_equal(map_a, map_b, bars):
    assert map_a.x_values == map_b.x_values
    assert map_a.is_identity == map_b.is_identity
    for b in bars:
        assert map_a.to_display(b.ts) == map_b.to_display(b.ts)


def test_extend_matches_fresh_build_no_gap():
    bars = [_bar(i) for i in range(100)]
    m = build_collapse_map(bars, "5 mins", True)
    m.extend(_bar(100).ts)
    _check_equal(m, build_collapse_map(bars + [_bar(100)], "5 mins", True),
                 bars + [_bar(100)])


def test_extend_matches_fresh_build_weekend_gap():
    import datetime
    utc = datetime.timezone.utc
    # 100 five-min bars ending Friday 2025-10-10 15:55 ET (19:55 UTC).
    fri = int(datetime.datetime(2025, 10, 10, 19, 55, tzinfo=utc).timestamp())
    bars = [Bar("TEST", "5 mins", fri - (99 - i) * 300,
                100.0, 101.0, 99.0, 100.5, 1000.0) for i in range(100)]
    # Next bar Monday 2025-10-13 09:30 ET (13:30 UTC): the Fri-16:00 →
    # Mon-09:30 ET gap holds no RTH session, so the map flips from
    # identity to collapsed at the tail.
    mon = int(datetime.datetime(2025, 10, 13, 13, 30, tzinfo=utc).timestamp())
    gapped = Bar("TEST", "5 mins", mon, 100.0, 101.0, 99.0, 100.5, 1000.0)
    m = build_collapse_map(bars, "5 mins", False)
    assert m.is_identity
    assert m.extend(gapped.ts) is True
    fresh = build_collapse_map(bars + [gapped], "5 mins", False)
    assert not fresh.is_identity
    _check_equal(m, fresh, bars + [gapped])


def test_extend_multiple_sequential():
    bars = [_bar(i) for i in range(50)]
    m = build_collapse_map(bars, "5 mins", True)
    extra = [_bar(50 + i) for i in range(10)]
    for b in extra:
        m.extend(b.ts)
    _check_equal(m, build_collapse_map(bars + extra, "5 mins", True),
                 bars + extra)


def test_extend_non_forward_ts_is_noop():
    bars = [_bar(i) for i in range(50)]
    m = build_collapse_map(bars, "5 mins", True)
    before = list(m.x_values)
    assert m.extend(bars[-1].ts) is False  # duplicate ts: not extended
    assert m.extend(bars[0].ts) is False   # backward ts: not extended
    assert m.x_values == before


def test_panel_new_candle_does_not_full_rebuild(monkeypatch, qapp):
    panel = ChartPanel()
    panel.set_timeframe("5 mins")
    panel.resize(900, 600)
    panel.show()
    try:
        panel.update_chart([_bar(i) for i in range(50)])
        qapp.processEvents()
        rebuilds: list = []
        orig = ChartPanel._rebuild_collapse_map
        monkeypatch.setattr(
            ChartPanel, "_rebuild_collapse_map",
            lambda self: (rebuilds.append(1), orig(self)),
        )
        panel.update_last_bar(_bar(50), True)
        qapp.processEvents()
        assert rebuilds == [], \
            "new-candle path must tail-extend, not full-rebuild"
        # ...and the result must equal a fresh build.
        fresh = build_collapse_map(panel._plotted_bars, "5 mins", True)
        _check_equal(panel._collapse_map, fresh, panel._plotted_bars)
        assert panel._plot_xs == [
            panel._to_display(b.ts) for b in panel._plotted_bars]
    finally:
        panel.close()


def test_panel_new_candle_rth_filtered_tail(qapp):
    """With Ext Hours OFF, a non-RTH new bar leaves plotted state alone."""
    panel = ChartPanel()
    panel.set_timeframe("5 mins")
    panel.set_extended_hours(False)
    panel.resize(900, 600)
    panel.show()
    try:
        # Friday 15:55 ET bar then a Saturday bar (non-RTH).
        import datetime
        fri = int(datetime.datetime(2026, 10, 9, 15, 55,
                                    tzinfo=datetime.timezone.utc).timestamp())
        bars = [Bar("TEST", "5 mins", fri - (9 - i) * 300,
                    100.0, 101.0, 99.0, 100.5, 1000.0) for i in range(10)]
        panel.update_chart(bars)
        qapp.processEvents()
        n_plotted = len(panel._plotted_bars)
        sat = Bar("TEST", "5 mins", fri + 86400, 100.0, 101.0, 99.0, 100.5,
                  1000.0)
        panel.update_last_bar(sat, True)
        qapp.processEvents()
        # The Saturday bar is not plotted (RTH filter); plotted state is
        # rebuilt rather than tail-extended, and stays consistent.
        assert panel._plot_xs == [
            panel._to_display(b.ts) for b in panel._plotted_bars]
        fresh = build_collapse_map(panel._plotted_bars, "5 mins", False)
        _check_equal(panel._collapse_map, fresh, panel._plotted_bars)
    finally:
        panel.close()
