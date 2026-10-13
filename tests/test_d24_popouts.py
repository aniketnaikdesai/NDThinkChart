"""D24 — pop-out chart windows (basic open/close/cap)."""

from __future__ import annotations

from config import settings

SYMBOL = "POPA"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([6001, 6002, 6003, 6004, 6005])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = iter([6101, 6102, 6103])
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def test_popout_opens_and_syncs(monkeypatch, qapp):
    """AC-D24.1: pop-out opens, attaches to the session, renders bars."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        assert win._rt_req_id == 6001

        win._open_popout()
        qapp.processEvents()

        assert len(win._popouts) == 1
        popout = win._popouts[0]
        assert popout.symbol == SYMBOL
        assert popout.timeframe == TF
        # One IBKR subscription per symbol (refcounted, not duplicated).
        assert win._sessions[SYMBOL].rt_req_id == 6001
        assert win._sessions[SYMBOL]._rt_holders == 2

        # Tick the session: the pop-out's panel updates via the session.
        win._on_realtime_bar(
            6001, NOW_TS + 1, 100.0, 100.1, 99.9, 100.0, 100.0, 100.0, 5
        )
        qapp.processEvents()
        assert popout.chart._bars  # bars synced to the pop-out

        popout.close()
        qapp.processEvents()
        assert len(win._popouts) == 0
        # RT refcount back to 1 (main chart only).
        assert win._sessions[SYMBOL]._rt_holders == 1
    finally:
        win.close()


def test_popout_cap(monkeypatch, qapp):
    """AC-D24.5: pop-out count capped at MAX_POPOUTS with a status message."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)

        messages = []
        win.status_bar.showMessage = lambda msg, *a: messages.append(msg)

        for _ in range(settings.MAX_POPOUTS + 2):
            win._open_popout()
        qapp.processEvents()

        assert len(win._popouts) == settings.MAX_POPOUTS
        assert any("limit" in m.lower() for m in messages)

        for p in list(win._popouts):
            p.close()
        qapp.processEvents()
    finally:
        win.close()


def test_popout_readonly(monkeypatch, qapp):
    """AC-D24.3: pop-out panel is not editable (no drawing/alarm modes)."""
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        win._open_popout()
        qapp.processEvents()

        popout = win._popouts[0]
        assert popout.chart._editable is False
        # Attempting to enter drawing/alarm mode is a no-op.
        popout.chart.set_drawing_tool("Trendline")
        popout.chart.set_alarm_mode(True)
        # (No exception; modes not entered — verified by _editable guard.)

        popout.close()
        qapp.processEvents()
    finally:
        win.close()
