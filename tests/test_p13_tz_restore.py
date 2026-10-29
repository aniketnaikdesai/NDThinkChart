"""P13-T8 (D49.6 persist/restore half): offset persisted with the set, restored with fallback.

T81 (integration): a pop-out set saved with a non-zero offset restores
offscreen carrying the stored offset, rendering identical time labels for
the seeded bars as the main chart. Red pre-fix (no persisted field).
T82 (integration): a pre-change saved set without the offset field
(migration read-back) restores carrying the main chart's current offset,
never a silent UTC default.
"""

from __future__ import annotations

import itertools
import json
from datetime import datetime, timezone

import pytest

from data.bar_cache import BarCache
from data.models import Bar
from data.popout_store import PopoutStore
from ui.lwc_view import format_tz_label

TF = "5 mins"
# Friday 2026-10-09 15:00 ET == 19:00 UTC (a trading day; ET is UTC-4).
NOW_TS = int(datetime(2026, 10, 9, 19, 0, tzinfo=timezone.utc).timestamp())
DAY_START_UTC = int(datetime(2026, 10, 9, 17, 0, tzinfo=timezone.utc).timestamp())

GEO = {"x": 10, "y": 20, "w": 640, "h": 420}


def _seed(symbol: str, start_ts: int, count: int, step: int = 300) -> list[Bar]:
    """Seed contiguous 5-min bars."""
    bars = [
        Bar(symbol, TF, start_ts + i * step, 100.0 + i, 100.5 + i,
            99.5 + i, 100.0 + i, 1000.0)
        for i in range(count)
    ]
    BarCache.save_bars(bars, ext_hours=True)
    return bars


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    rt_ids = itertools.count(7001)
    hist_calls: list = []

    def fake_subscribe(symbol, contract):
        return next(rt_ids)

    def fake_hist(**kwargs):
        hist_calls.append(kwargs)
        return next(itertools.count(7101 + len(hist_calls)))

    win.rt_manager.subscribe = fake_subscribe
    win.md_manager.req_historical_data = fake_hist
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


def test_p13_t81_saved_offset_restored_with_matching_labels(
    monkeypatch, qapp
):
    """Saved offset restores onto the view; labels match the main chart."""
    PopoutStore.clear()
    win = _make_window(monkeypatch, qapp)
    try:
        win._tz_offset = 14400.0
        seeded = _seed("TZR1", DAY_START_UTC, 20)
        PopoutStore.save("TZR1", TF, "Candles", True, dict(GEO),
                         tz_offset=14400.0)

        # Round-trip: the offset survives save/load.
        recs = PopoutStore.load_all()
        assert len(recs) == 1
        assert recs[0]["tz_offset"] == pytest.approx(14400.0)

        # Geometry re-saves without an offset must not clobber the stamp.
        PopoutStore.save("TZR1", TF, "Candles", True, dict(GEO))
        assert PopoutStore.load_all()[0]["tz_offset"] == pytest.approx(
            14400.0
        )

        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        popout = win._popouts[0]
        assert popout.chart.tz_offset == pytest.approx(14400.0)
        main_labels = [format_tz_label(b.ts, win._tz_offset) for b in seeded]
        restored_labels = [
            format_tz_label(b.ts, popout.chart.tz_offset) for b in seeded
        ]
        assert restored_labels == main_labels

        # The restored view carries the STORED value, not the fallback:
        # close out, move the main chart elsewhere, save under the old
        # offset, and restore — the view must still read the stored one.
        for p in list(win._popouts):
            p.close()
        qapp.processEvents()
        assert PopoutStore.load_all() == []
        win._tz_offset = 18000.0
        PopoutStore.save("TZR2", TF, "Candles", True, dict(GEO),
                         tz_offset=14400.0)
        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        assert win._popouts[0].chart.tz_offset == pytest.approx(14400.0)
    finally:
        _teardown(win)


def test_p13_t82_legacy_record_falls_back_to_main_offset(
    monkeypatch, qapp
):
    """A pre-change save without the field restores the main offset."""
    PopoutStore.clear()
    win = _make_window(monkeypatch, qapp)
    try:
        _seed("TZL1", DAY_START_UTC, 10)
        # Legacy pre-change row: written without the offset field, so the
        # additive migration leaves it NULL — the migration read-back case.
        from data.db import db

        db.conn.execute(
            """INSERT INTO popouts
               (symbol, timeframe, mode, ext_hours, geometry, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("TZL1", TF, "Candles", 1, json.dumps(dict(GEO)), 12345),
        )
        db.conn.commit()

        recs = PopoutStore.load_all()
        assert len(recs) == 1
        assert recs[0].get("tz_offset") is None

        # Non-zero main-chart offset: a silent-UTC fallback would read 0.0.
        win._tz_offset = 18000.0
        win._restore_popouts()
        qapp.processEvents()

        assert len(win._popouts) == 1
        popout = win._popouts[0]
        assert popout.chart.tz_offset == pytest.approx(win._tz_offset)
        assert popout.chart.tz_offset == pytest.approx(18000.0)
        assert popout.chart.tz_offset != pytest.approx(0.0)
    finally:
        _teardown(win)
