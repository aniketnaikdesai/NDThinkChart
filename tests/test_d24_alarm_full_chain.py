"""D24 — alarm full chain via pop-out sessions.

Asserts the FULL trigger chain from a background (pop-out) session:
persisted mark_triggered + toast + sound exactly once from MainWindow,
no badge change for the non-firing symbol. Plus a same-symbol variant
asserting the badge updates.
"""

from __future__ import annotations

import itertools

import pytest

from data.alarm_store import AlarmStore
from data.models import Alarm

SYM_MAIN = "ALMMAIN"
SYM_BG = "ALMBG"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


def _clear_alarms(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([8001, 8002, 8003, 8004])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    # D42's depth floor (S17) can issue many chunks from one load, so hand out
    # historical reqIds unbounded rather than exhausting a fixed list.
    hids = itertools.count(8101)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def _rt_bar(win, req_id: int, ts: int, price: float) -> None:
    win._on_realtime_bar(
        req_id, ts, price - 0.2, price + 0.2, price - 0.3, price, 100.0,
        price, 5,
    )


def test_alarm_full_chain_background_symbol(monkeypatch, qapp):
    """Full chain: bg symbol alarm fires → persisted + toast + sound once,
    badge unchanged (main chart shows another symbol)."""
    win = _make_window(monkeypatch, qapp)
    try:
        for s in (SYM_MAIN, SYM_BG):
            _clear_alarms(s)
        # Alarm on the background symbol.
        bg_alarm = Alarm(
            id=None, symbol=SYM_BG, price=50.5, direction="cross_above",
            active=True, sound=True,
        )
        bg_alarm.id = AlarmStore.add(bg_alarm)

        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM_BG, TF)   # rt 8001
        sess_bg = win._sessions[SYM_BG]
        # Keep BG alive with a pop-out-style second view.
        from unittest.mock import MagicMock

        sess_bg.attach_view(MagicMock(), TF)
        sess_bg.ensure_rt_subscribed()

        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM_MAIN, TF)  # rt 8002; main chart on SYM_MAIN
        badge_before = win.alarms_btn.text()

        # Spy on the full chain.
        toasts = []
        sounds = []
        win.toast.show_message = lambda msg: toasts.append(msg)
        win.sound_service.play_alarm = lambda: sounds.append(1)
        marked = []
        orig_mark = AlarmStore.mark_triggered
        AlarmStore.mark_triggered = staticmethod(
            lambda aid, ts=None: (marked.append(aid), orig_mark(aid, ts))[0]
        )

        # Tick BG across its level.
        _rt_bar(win, 8001, NOW_TS + 1, 50.0)
        _rt_bar(win, 8001, NOW_TS + 6, 51.0)

        # FULL CHAIN assertions.
        assert marked == [bg_alarm.id]  # persisted exactly once
        assert len(toasts) == 1 and SYM_BG in toasts[0]  # toast exactly once
        assert len(sounds) == 1  # sound exactly once
        # Badge reflects the main-chart symbol only (SYM_MAIN, no alarms).
        assert win.alarms_btn.text() == badge_before
        # The alarm is marked triggered in the store.
        reloaded = AlarmStore.load(SYM_BG)
        assert reloaded[0].triggered is True
    finally:
        AlarmStore.mark_triggered = orig_mark
        for s in (SYM_MAIN, SYM_BG):
            _clear_alarms(s)
        win.close()


def test_alarm_full_chain_same_symbol_updates_badge(monkeypatch, qapp):
    """Same-symbol variant: badge updates when the main chart's alarm fires."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear_alarms(SYM_MAIN)
        alarm = Alarm(
            id=None, symbol=SYM_MAIN, price=50.5, direction="cross_above",
            active=True, sound=False,
        )
        alarm.id = AlarmStore.add(alarm)

        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM_MAIN, TF)
        badge_before = win.alarms_btn.text()
        assert "Alarms (1)" in badge_before

        _rt_bar(win, win._rt_req_id, NOW_TS + 1, 50.0)
        _rt_bar(win, win._rt_req_id, NOW_TS + 6, 51.0)

        # Badge shows the trigger.
        assert "/ 1" in win.alarms_btn.text()
    finally:
        _clear_alarms(SYM_MAIN)
        win.close()
