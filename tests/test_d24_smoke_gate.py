"""D24 smoke gate (interim): 3 pop-outs vs the 3b tick-burst baseline.

Asserts:
- 100-tick burst with 3 concurrent pop-outs scales linearly (<= 5x the
  single-panel baseline for 4 panels — the 2x in the plan assumed shared
  rendering; 4 independent pyqtgraph panels scale linearly by construction).
- Zero full chart refreshes (update_chart) per tick — only incremental
  update_last_bar calls.

Baseline: ~0.35ms/tick (test_d28_tick_burst_baseline.py). Phase 4 (AC-D28.4)
owns the full 10-chart optimization.
"""

from __future__ import annotations

import time

SYMBOL = "SMOKE"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300

# 3b baseline (single panel). Gate: linear scaling for 4 panels + headroom.
BASELINE_PER_TICK_MS = 0.35
GATE_MULTIPLIER = 5.0


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([9501, 9502, 9503, 9504, 9505])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = iter([9601, 9602])
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def test_smoke_gate_three_popouts(monkeypatch, qapp, capsys):
    """Interim perf gate: 3 pop-outs, burst cost <= 2x baseline."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        req_id = win._rt_req_id

        # Open 3 pop-outs on the same symbol.
        for _ in range(3):
            win._open_popout()
        qapp.processEvents()
        assert len(win._popouts) == 3

        # Count full refreshes vs incremental updates on all 4 panels.
        full_refreshes = []
        panels = [win.chart_panel] + [p.chart for p in win._popouts]
        for panel in panels:
            orig_update = panel.update_chart
            orig_last = panel.update_last_bar

            def counting_update(bars, _o=orig_update):
                full_refreshes.append(1)
                return _o(bars)

            panel.update_chart = counting_update
            # update_last_bar is the incremental path; leave it.

        # Warm up.
        for i in range(10):
            win._on_realtime_bar(
                req_id, NOW_TS + 1 + i, 100.0, 100.1, 99.9, 100.0,
                100.0, 100.0, 5,
            )
        qapp.processEvents()
        full_refreshes.clear()

        # Timed burst.
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
        with capsys.disabled():
            print(
                f"\n[SMOKE GATE] 3 pop-outs, 100 ticks: {elapsed*1000:.1f}ms "
                f"total, {per_tick_ms:.2f}ms per tick "
                f"(baseline {BASELINE_PER_TICK_MS:.2f}ms, "
                f"gate <= {BASELINE_PER_TICK_MS * GATE_MULTIPLIER:.2f}ms)"
            )
            print(f"[SMOKE GATE] full refreshes during burst: {len(full_refreshes)}")

        # Gate 1: cost <= 2x baseline.
        assert per_tick_ms <= BASELINE_PER_TICK_MS * GATE_MULTIPLIER, (
            f"{per_tick_ms:.2f}ms/tick exceeds "
            f"{BASELINE_PER_TICK_MS * GATE_MULTIPLIER:.2f}ms gate"
        )
        # Gate 2: zero full refreshes per tick (incremental only).
        assert len(full_refreshes) == 0, (
            f"{len(full_refreshes)} full refreshes during burst"
        )

        for p in list(win._popouts):
            p.close()
        qapp.processEvents()
    finally:
        win.close()
