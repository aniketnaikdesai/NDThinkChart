"""D28.4 binding gate — 10-chart 5-second tick burst (AC-D28.4).

R52 requires the full 10-chart bar before Phase 3 merges to main. The
Phase 3 interim smoke gate (<=5x baseline for 4 panels) does NOT satisfy
this. Configuration: the main chart + 9 pop-outs on one symbol (the
realistic max-load layout), each holding a 500-bar series.

  Gate 1: zero static-layer full QPicture regens per forming tick
          (render-call counters) — the B-2.4 pathology. One trailing
          new-candle tick is allowed exactly one static regen per panel.
  Gate 2: per-tick cost within a generous bound (counters first, timing
          second — no wall-clock flakes).
  Gate 3: memory bounded — every panel's series stays within the cap and
          the cached arrays stay consistent.
"""
from __future__ import annotations

import time

from data.models import Bar

SYMBOL = "GATE10"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300
N_BARS = 500
N_POPOUTS = 9  # + main chart = 10 charts

# Generous: measured ~4ms for 10 charts; this only catches pathological
# regressions (e.g. a reintroduced per-tick full regen is ~10x this).
GATE_PER_TICK_MS = 50.0


def _bar(i, px=100.0):
    return Bar(SYMBOL, TF, NOW_TS - (N_BARS - 1 - i) * 300,
               px, px + 1.0, px - 1.0, px + 0.5, 1000.0 + i)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter(range(9501, 9600))
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = iter(range(9601, 9700))
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def _all_panels(win):
    return [win.chart_panel] + [p.chart for p in win._popouts]


def test_ten_chart_tick_burst_gate(monkeypatch, qapp, capsys):
    """AC-D28.4: 10 charts, 100 forming ticks + 1 new candle."""
    from config import settings
    SESSION_BAR_CAP = settings.SESSION_BAR_CAP

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        req_id = win._rt_req_id
        assert req_id is not None

        for _ in range(N_POPOUTS):
            win._open_popout()
        qapp.processEvents()
        panels = _all_panels(win)
        assert len(panels) == 10, f"expected 10 charts, got {len(panels)}"

        # Seed every panel with a realistic series.
        bars = [_bar(i, 100.0 + (i % 50) * 0.2) for i in range(N_BARS)]
        for panel in panels:
            panel.update_chart(bars)
        qapp.processEvents()
        for panel in panels:
            panel.candlestick.regen_count = 0
            panel.live_candle.regen_count = 0

        # Warm up the aggregator's forming bar (not measured).
        for i in range(5):
            win._on_realtime_bar(
                req_id, NOW_TS + 1 + i, 100.0, 100.1, 99.9, 100.0,
                100.0, 100.0, 5,
            )
        qapp.processEvents()
        for panel in panels:
            panel.candlestick.regen_count = 0
            panel.live_candle.regen_count = 0

        # Gate 1+2: 99 forming ticks — no static regen anywhere.
        start = time.perf_counter()
        for i in range(99):
            price = 100.0 + (i % 10) * 0.1
            win._on_realtime_bar(
                req_id, NOW_TS + 6 + i, price - 0.1, price + 0.1,
                price - 0.2, price, 100.0, price, 5,
            )
        qapp.processEvents()
        forming_elapsed = time.perf_counter() - start

        static_regens = sum(p.candlestick.regen_count for p in panels)
        live_regens = sum(p.live_candle.regen_count for p in panels)
        assert static_regens == 0, (
            f"B-2.4 pathology: {static_regens} static full regens during "
            f"99 forming ticks across 10 charts"
        )
        assert live_regens == 99 * 10, (
            f"live layer must refresh once per tick per chart "
            f"(got {live_regens}, expected {99 * 10})"
        )

        per_tick_ms = (forming_elapsed / 99) * 1000
        with capsys.disabled():
            print(
                f"\n[10-CHART GATE] 99 forming ticks x 10 charts: "
                f"{forming_elapsed * 1000:.1f}ms total, "
                f"{per_tick_ms:.2f}ms per tick "
                f"(gate <= {GATE_PER_TICK_MS:.1f}ms)"
            )
            print(f"[10-CHART GATE] static regens: {static_regens}, "
                  f"live regens: {live_regens}")
        assert per_tick_ms <= GATE_PER_TICK_MS, (
            f"{per_tick_ms:.2f}ms/tick exceeds the {GATE_PER_TICK_MS:.1f}ms "
            f"gate for 10 charts"
        )

        # One new candle: exactly one static regen per panel (the commit).
        for panel in panels:
            panel.candlestick.regen_count = 0
        win._on_realtime_bar(
            req_id, NOW_TS + 301, 101.0, 101.1, 100.9, 101.0,
            101.0, 101.0, 5,
        )
        qapp.processEvents()
        assert sum(p.candlestick.regen_count for p in panels) == 10

        # Gate 3: memory bounded on every panel.
        for panel in panels:
            assert len(panel._bars) <= SESSION_BAR_CAP, (
                f"panel series unbounded: {len(panel._bars)}"
            )
            assert panel._plot_xs == [
                panel._to_display(b.ts) for b in panel._plotted_bars]
            assert len(panel._plot_vols) == len(panel._plotted_bars)
    finally:
        for p in list(win._popouts):
            p.close()
        qapp.processEvents()
        win.close()
