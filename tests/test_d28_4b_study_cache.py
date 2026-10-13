"""D28.4 (4b-2) — the study cache is actually read.

Incremental single-bar updates must exactly match the tail of the batch
``calculate_*`` functions; the panel must use the cache on new candles
instead of recomputing every study over all bars.
"""
import pytest

from services import indicator_service as ind

# Deterministic series: trend + oscillation so indicators actually move.
CLOSES = [100.0 + i * 0.3 + (i % 7) * 0.5 - (i % 3) * 0.4 for i in range(200)]
HIGHS = [c + 0.6 for c in CLOSES]
LOWS = [c - 0.6 for c in CLOSES]
VOLS = [1000.0 + (i % 11) * 100.0 for i in range(200)]
TSS = [1_700_000_000 + i * 300 for i in range(200)]


def _assert_close(a, b):
    if a is None or b is None:
        assert a is b, f"None mismatch: {a!r} vs {b!r}"
    else:
        assert a == pytest.approx(b, rel=1e-9, abs=1e-9), f"{a!r} vs {b!r}"


def test_sma_incremental_matches_batch():
    batch = ind.calculate_sma(CLOSES, 20)
    state: dict = {}
    for i, c in enumerate(CLOSES):
        _assert_close(ind.sma_update(state, c, 20), batch[i])


def test_ema_incremental_matches_batch():
    batch = ind.calculate_ema(CLOSES, 9)
    state: dict = {}
    for i, c in enumerate(CLOSES):
        _assert_close(ind.ema_update(state, c, 9), batch[i])


def test_vwap_incremental_matches_batch():
    batch = ind.calculate_vwap(HIGHS, LOWS, CLOSES, VOLS, timestamps=TSS)
    state: dict = {}
    for i in range(len(CLOSES)):
        _assert_close(
            ind.vwap_update(state, HIGHS[i], LOWS[i], CLOSES[i], VOLS[i], TSS[i]),
            batch[i],
        )


def test_vwap_incremental_resets_on_et_day_change():
    # Two bars on different ET dates: the second must reset the session.
    state: dict = {}
    ts_day1 = 1_700_000_000  # a fixed ts
    ts_day2 = ts_day1 + 86400
    v1 = ind.vwap_update(state, 101.0, 99.0, 100.0, 1000.0, ts_day1)
    v2 = ind.vwap_update(state, 111.0, 109.0, 110.0, 1000.0, ts_day2)
    assert v1 == pytest.approx(100.0)
    assert v2 == pytest.approx(110.0), "new ET day must reset VWAP"


def test_bollinger_incremental_matches_batch():
    upper, mid, lower = ind.calculate_bollinger_bands(CLOSES, 20, 2.0)
    state: dict = {}
    for i, c in enumerate(CLOSES):
        u, m, lo = ind.bollinger_update(state, c, 20, 2.0)
        _assert_close(u, upper[i])
        _assert_close(m, mid[i])
        _assert_close(lo, lower[i])


def test_rsi_incremental_matches_batch():
    batch = ind.calculate_rsi(CLOSES, 14)
    state: dict = {}
    for i, c in enumerate(CLOSES):
        _assert_close(ind.rsi_update(state, c, 14), batch[i])


def test_macd_incremental_matches_batch():
    macd_b, sig_b, _ = ind.calculate_macd(CLOSES, 12, 26, 9)
    state: dict = {}
    for i, c in enumerate(CLOSES):
        m, s = ind.macd_update(state, c, 12, 26, 9)
        _assert_close(m, macd_b[i])
        _assert_close(s, sig_b[i])


def test_incremental_short_series_matches_batch():
    """Series shorter than the warm-up: Nones line up exactly."""
    short = CLOSES[:10]
    batch = ind.calculate_sma(short, 20)
    assert all(v is None for v in batch)
    state: dict = {}
    for i, c in enumerate(short):
        assert ind.sma_update(state, c, 20) is None


# ── Panel wiring: the cache is actually read on new candles ─────────────

STUDIES = [
    {"type": "sma", "enabled": True, "params": {"period": 20}},
    {"type": "ema", "enabled": True, "params": {"period": 9}},
    {"type": "vwap", "enabled": True, "params": {}},
    {"type": "bollinger", "enabled": True,
     "params": {"period": 20, "std_dev": 2.0}},
    {"type": "rsi", "enabled": True, "params": {"period": 14}},
    {"type": "macd", "enabled": True,
     "params": {"fast": 12, "slow": 26, "signal": 9}},
]

BASE = 1_760_000_000


def _pbar(i, px=100.0):
    from data.models import Bar
    return Bar("TST", "5 mins", BASE + i * 300,
               px, px + 1.0, px - 1.0, px + 0.5, 1000.0 + i)


def _study_panel(qapp, n=200):
    from ui.chart_panel import ChartPanel
    panel = ChartPanel()
    panel.set_symbol("TST")
    panel.set_timeframe("5 mins")
    panel.set_studies(STUDIES)
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    panel.update_chart([_pbar(i, 100.0 + i * 0.1) for i in range(n)])
    qapp.processEvents()
    return panel


def test_new_candle_skips_batch_recompute(monkeypatch, qapp):
    """On a new candle the batch calculators must not run (cache is read)."""
    import ui.chart_panel as cp
    panel = _study_panel(qapp)
    try:
        calls: list[str] = []
        for name in ("calculate_sma", "calculate_ema", "calculate_vwap",
                     "calculate_bollinger_bands", "calculate_rsi",
                     "calculate_macd"):
            monkeypatch.setattr(
                cp, name,
                (lambda n: lambda *a, **k: (calls.append(n), None)[1])(name),
            )
        # Sanity: the full path populated the cache.
        cached = panel._study_cache.get("TST", "5 mins", STUDIES)
        assert cached is not None and cached["n_bars"] == 200
        # One new candle: incremental only.
        panel.update_last_bar(_pbar(200, 120.0), True)
        qapp.processEvents()
        assert calls == [], \
            f"batch calculators ran on new candle: {calls}"
        cached2 = panel._study_cache.get("TST", "5 mins", STUDIES)
        assert cached2["n_bars"] == 201, "cache must advance by one bar"
    finally:
        panel.close()


def test_incremental_values_match_fresh_full_compute(qapp):
    """Cached incremental values == a from-scratch full computation."""
    panel = _study_panel(qapp, n=200)
    try:
        panel.update_last_bar(_pbar(200, 120.0), True)
        qapp.processEvents()
        cached = panel._study_cache.get("TST", "5 mins", STUDIES)
        assert cached["n_bars"] == 201
        fresh_vals, _ = panel._study_values_full(panel._bars)
        for key, vals in fresh_vals.items():
            got = cached["values"][key]
            assert len(got) == len(vals) == 201
            for g, f in zip(got, vals):
                if g is None or f is None:
                    assert g is f
                else:
                    assert g == pytest.approx(f, rel=1e-9, abs=1e-9)
    finally:
        panel.close()


def test_study_change_invalidates_cache(qapp):
    """A study edit falls back to the full path (no stale incremental)."""
    panel = _study_panel(qapp, n=50)
    try:
        other = [dict(s, params=dict(s["params"], period=10))
                 if s["type"] == "sma" else s for s in STUDIES]
        panel.set_studies(other)
        qapp.processEvents()
        cached = panel._study_cache.get("TST", "5 mins", other)
        assert cached is not None and cached["n_bars"] == 50
        # The old study set no longer hits.
        assert panel._study_cache.get("TST", "5 mins", STUDIES) is None
    finally:
        panel.close()
