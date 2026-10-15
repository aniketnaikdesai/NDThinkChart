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
    """AC-D24.6: pop-out panel is not editable (no drawing/alarm modes)."""
    from ui.chart_mouse_router import RouterMode

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        win._open_popout()
        qapp.processEvents()

        popout = win._popouts[0]
        assert popout.chart._editable is False
        assert popout.chart.mouse_router.active_mode == RouterMode.IDLE

        # Both adapters early-return on the _editable guard, so the router
        # never leaves IDLE and no tool/alarm mode is entered.
        popout.chart.set_drawing_tool("trendline")
        assert popout.chart.drawing_overlay.tool_active() is False
        assert popout.chart.mouse_router.active_mode == RouterMode.IDLE

        popout.chart.set_alarm_mode(True)
        assert popout.chart.alarm_overlay.is_alarm_mode() is False
        assert popout.chart.mouse_router.active_mode == RouterMode.IDLE

        popout.close()
        qapp.processEvents()
    finally:
        win.close()


def test_popout_drawing_sync(monkeypatch, qapp):
    """AC-D24.2: drawings created/deleted on the main chart sync to pop-outs."""
    from data.models import Drawing

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        win._open_popout()
        qapp.processEvents()

        popout = win._popouts[0]
        assert popout.chart.drawing_overlay._drawings == []

        # The main chart is the sole writer: its overlay emits `created`,
        # MainWindow persists it and the session fans the state out to views.
        drawing = Drawing(symbol=SYMBOL, kind="horizontal", payload={"y": 101.0})
        win.chart_panel.drawing_overlay.created.emit(drawing)
        qapp.processEvents()

        synced = popout.chart.drawing_overlay._drawings
        assert len(synced) == 1
        assert synced[0].payload == {"y": 101.0}

        win._on_drawing_deleted(drawing.id)
        qapp.processEvents()
        assert popout.chart.drawing_overlay._drawings == []
    finally:
        win.close()


def test_popout_study_sync(monkeypatch, qapp):
    """AC-D24.4: the study config syncs to an open pop-out.

    The pop-out does NOT connect ``studies_changed``; the session pushes the
    new config through its ``_views`` loop, so that loop is the path under test.
    """
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        win._open_popout()
        qapp.processEvents()

        popout = win._popouts[0]
        # The pop-out is seeded from the session on attach (the app's default
        # study set). Push a DIFFERENT config and require the pop-out to adopt it.
        studies = [{"type": "sma", "enabled": True, "params": {"period": 14}}]
        assert popout.chart._studies != studies

        win._on_studies_changed(studies)
        qapp.processEvents()

        assert popout.chart._studies == studies
    finally:
        win.close()


def test_popout_always_on_top_default_off(monkeypatch, qapp):
    """AC-D24.10: pop-outs are not always-on-top by default; the toggle flips it."""
    from PyQt6.QtCore import Qt

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        win._open_popout()
        qapp.processEvents()

        popout = win._popouts[0]
        assert popout._always_on_top is False
        assert not (popout.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)

        popout._toggle_always_on_top(True)
        qapp.processEvents()
        assert popout._always_on_top is True
        assert popout.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    finally:
        win.close()


def test_popout_reconnect_replays_and_resumes(monkeypatch, qapp):
    """AC-D24.7: the post-reconnect replay rebinds the RT reqId; the open
    pop-out keeps receiving live bars and the stale reqId is ignored."""
    win = _make_window(monkeypatch, qapp)
    # A persistent id source wide enough for the initial subscribe + the replay.
    ids = iter(range(7101, 7200))
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        win._open_popout()
        qapp.processEvents()

        session = win._sessions[SYMBOL]
        popout = win._popouts[0]
        old_req = session.rt_req_id
        assert old_req == 7101

        # Seed one bar: a tick on an empty chart only appends on a new candle,
        # so without this the later update would not be observable.
        win._on_realtime_bar(
            old_req, NOW_TS + 1, 100.0, 100.1, 99.9, 100.0, 100.0, 100.0, 5
        )
        qapp.processEvents()
        assert popout.chart._bars
        seed_close = popout.chart._bars[-1].close

        # The reconnect replay re-issues the registered RT_BARS subscription.
        win._replay_subscriptions()
        qapp.processEvents()

        new_req = session.rt_req_id
        assert new_req is not None and new_req != old_req, (
            "the replay must issue a fresh reqId"
        )

        # A live bar on the NEW reqId reaches the pop-out...
        win._on_realtime_bar(
            new_req, NOW_TS + 6, 101.0, 101.5, 100.5, 101.0, 101.0, 101.0, 7
        )
        qapp.processEvents()
        assert popout.chart._bars[-1].close != seed_close

        # ...and the stale reqId is ignored.
        after = popout.chart._bars[-1].close
        win._on_realtime_bar(
            old_req, NOW_TS + 11, 999.0, 999.0, 999.0, 999.0, 999.0, 999.0, 1
        )
        qapp.processEvents()
        assert popout.chart._bars[-1].close == after
    finally:
        win.close()
