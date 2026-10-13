"""D28.4 fix pass — panel series cap + study-cache invalidation on wholesale replace.

Fix 2: ``update_chart`` never invalidated the study cache — a
value-correcting backfill matching the incremental fingerprint
(n_bars, last_ts) took the incremental path on stale values.
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


def test_update_chart_invalidates_study_cache(qapp):
    """A value-correcting backfill with a matching (n_bars, last_ts)
    fingerprint must recompute studies from the corrected bars."""
    panel = _panel(qapp)
    try:
        original = [_bar(i, 100.0 + i * 0.1) for i in range(49)]
        panel.update_chart(original)
        qapp.processEvents()
        cached = panel._study_cache.get("TST", "5 mins", STUDIES_SMA)
        assert cached is not None and cached["n_bars"] == 49
        # Backfill: same 49 timestamps with corrected (+1.0) values, plus one
        # genuinely new bar. This matches the incremental fingerprint
        # (n == cached_n + 1, last_ts == bars[-2].ts).
        corrected = ([_bar(i, 101.0 + i * 0.1) for i in range(49)]
                     + [_bar(49, 200.0)])
        panel.update_chart(corrected)
        qapp.processEvents()
        cached = panel._study_cache.get("TST", "5 mins", STUDIES_SMA)
        assert cached is not None and cached["n_bars"] == 50
        expected = ind.calculate_sma([b.close for b in corrected], 20)
        got = cached["values"]["sma:0"]
        assert len(got) == len(expected)
        for g, e in zip(got, expected):
            _assert_close(g, e)
        # The stale result (incremental over the old closes) differs by 1.0
        # on the corrected region — guard against a vacuous pass.
        stale = ind.calculate_sma([b.close for b in original], 20)
        assert got[30] != pytest.approx(stale[30], rel=1e-9, abs=1e-9)
    finally:
        panel.close()
