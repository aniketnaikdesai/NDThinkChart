"""3b tick-burst baseline for the 3c pop-out smoke gate.

Measures the wall-clock cost of a burst of realtime ticks on a single chart.
3c asserts: with 3 concurrent pop-outs, the burst cost is <= 2x this baseline
and zero full QPicture regenerations happen per tick.

This is a measurement, not a gate — it records the number for the report.
"""

from __future__ import annotations

import time

from data.models import Bar

SYMBOL = "BURST"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([9001, 9002, 9003])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = iter([9101, 9102])
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def test_tick_burst_baseline(monkeypatch, qapp, capsys):
    """Measure 100 rapid 5-sec ticks; print the per-tick cost."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        req_id = win._rt_req_id
        assert req_id is not None

        # Warm up.
        for i in range(10):
            win._on_realtime_bar(
                req_id, NOW_TS + 1 + i, 100.0, 100.1, 99.9, 100.0,
                100.0, 100.0, 5,
            )
        qapp.processEvents()

        # Timed burst: 100 ticks, 5 seconds apart in the same 5-min period.
        start = time.perf_counter()
        for i in range(100):
            price = 100.0 + (i % 10) * 0.1
            win._on_realtime_bar(
                req_id, NOW_TS + 11 + i * 5, price - 0.1, price + 0.1,
                price - 0.2, price, 100.0, price, 5,
            )
        qapp.processEvents()
        elapsed = time.perf_counter() - start

        per_tick_ms = (elapsed / 100) * 1000
        # Record for the 3c smoke-gate report.
        with capsys.disabled():
            print(
                f"\n[TICK-BURST BASELINE] 100 ticks: {elapsed*1000:.1f}ms "
                f"total, {per_tick_ms:.2f}ms per tick"
            )
        # Sanity: a tick must not take longer than 50ms on average.
        assert per_tick_ms < 50.0
    finally:
        win.close()
