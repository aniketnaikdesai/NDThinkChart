"""P13-T1 — cold restore routes through cached bars + aggregator + realtime subscribe (D49.1)."""

from __future__ import annotations

import itertools
from datetime import datetime, timezone

from data.bar_cache import BarCache
from data.models import Bar
from data.popout_store import PopoutStore

TF = "5 mins"
# Friday 2026-10-09 15:00 ET == 19:00 UTC (a trading day; ET is UTC-4).
NOW_TS = int(datetime(2026, 10, 9, 19, 0, tzinfo=timezone.utc).timestamp())
DAY_START_UTC = int(datetime(2026, 10, 9, 17, 0, tzinfo=timezone.utc).timestamp())


def _seed(symbol: str, start_ts: int, count: int, skip: set[int] | None = None,
          step: int = 300) -> list[Bar]:
    """Seed contiguous 5-min bars (1-based index set skips a gap)."""
    skip = skip or set()
    bars = [
        Bar(symbol, TF, start_ts + i * step, 100.0 + i, 100.5 + i,
            99.5 + i, 100.0 + i, 1000.0)
        for i in range(count) if i not in skip
    ]
    BarCache.save_bars(bars, ext_hours=True)
    return bars


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    rt_ids = itertools.count(7001)
    rt_calls: list = []
    hist_calls: list = []

    def fake_subscribe(symbol, contract):
        rt_calls.append(symbol)
        return next(rt_ids)

    def fake_hist(**kwargs):
        hist_calls.append(kwargs)
        return next(itertools.count(7101 + len(hist_calls)))

    win.rt_manager.subscribe = fake_subscribe
    win.md_manager.req_historical_data = fake_hist
    win._hist_calls = hist_calls
    win._rt_calls = rt_calls
    win._ibkr_connected = True
    win._now_ts = lambda: NOW_TS
    win.show()
    qapp.processEvents()
    return win


def _teardown(win) -> None:
    try:
        for p in list(win._popouts):
            p.close()
        PopoutStore.clear()
    finally:
        win.close()


def test_p13_t1_cold_restore_bars_aggregator_subscription(monkeypatch, qapp):
    """P13-T1-T11: session-less restore shows cached bars, owns the timeframe
    aggregator, and holds a realtime subscription."""
    PopoutStore.clear()
    win = _make_window(monkeypatch, qapp)
    try:
        seeded = _seed("COLD1", DAY_START_UTC, 20)
        PopoutStore.save("COLD1", TF, "Candles", True,
                         {"x": 10, "y": 20, "w": 640, "h": 420})
        assert "COLD1" not in win._sessions

        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        popout = win._popouts[0]
        assert popout.symbol == "COLD1"
        session = win._sessions["COLD1"]
        # The window shows the cached bars (session series + synced view).
        assert [b.ts for b in session.get_bars(TF)] == [b.ts for b in seeded]
        assert [b.ts for b in popout.chart._bars] == [b.ts for b in seeded]
        # The timeframe aggregator exists on the session …
        assert session._aggregators.get(TF) is not None
        # … and a realtime hold is held (one IBKR subscription).
        assert session._rt_req_id is not None
        assert session._rt_holders >= 1
    finally:
        _teardown(win)


def test_p13_t1_gapped_cache_issues_backfill(monkeypatch, qapp):
    """P13-T1-T12: a gapped seeded cache issues a backfill request through the
    existing history path instead of leaving the window stale."""
    PopoutStore.clear()
    win = _make_window(monkeypatch, qapp)
    try:
        # 30-min hole (indices 6..11) inside the trailing session.
        seeded = _seed("GAP1", DAY_START_UTC, 20, skip=set(range(6, 12)))
        PopoutStore.save("GAP1", TF, "Candles", True,
                         {"x": 10, "y": 20, "w": 640, "h": 420})

        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        # The cached bars still reach the window …
        session = win._sessions["GAP1"]
        assert [b.ts for b in session.get_bars(TF)] == [b.ts for b in seeded]
        # … and the gap is covered by a request on the existing path.
        assert len(win._hist_calls) >= 1
        assert all("endDateTime" in call for call in win._hist_calls)
    finally:
        _teardown(win)


def test_p13_t1_loaded_symbol_and_disconnected_noop(monkeypatch, qapp):
    """P13-T1-T13: the already-loaded main-chart symbol gains no second
    aggregator/subscription; disconnected restore is a status-message no-op
    issuing no request."""
    PopoutStore.clear()
    win = _make_window(monkeypatch, qapp)
    try:
        win.load_chart("POPY", TF)
        qapp.processEvents()
        session = win._sessions["POPY"]
        agg_before = session._aggregators.get(TF)
        assert agg_before is not None
        rt_before = session._rt_req_id
        assert rt_before is not None
        n_hist_before = len(win._hist_calls)
        n_rt_before = len(win._rt_calls)

        PopoutStore.save("POPY", TF, "Candles", True,
                         {"x": 10, "y": 20, "w": 640, "h": 420})
        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        assert session._aggregators.get(TF) is agg_before
        assert session._rt_req_id == rt_before
        # No second subscription (refcount bump only — no new IBKR
        # subscribe) and no backfill wave for the loaded symbol.
        assert len(win._rt_calls) == n_rt_before
        assert len(win._hist_calls) == n_hist_before

        # Disconnected restore: status message, zero new requests.
        messages: list = []
        win.status_bar.showMessage = lambda msg, *a: messages.append(msg)
        win._ibkr_connected = False
        PopoutStore.save("AWAY1", TF, "Candles", True,
                         {"x": 10, "y": 20, "w": 640, "h": 420})
        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        assert "AWAY1" not in win._sessions
        assert len(win._hist_calls) == n_hist_before
        assert len(win._rt_calls) == n_rt_before
        assert any("disconnect" in m.lower() for m in messages)
    finally:
        _teardown(win)
