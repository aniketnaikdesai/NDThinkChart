"""Phase 3 fix-pass regression tests (reviewer REQUEST-CHANGES items).

Each test was written red-first against the pre-fix code.
"""

from __future__ import annotations

from data.alarm_store import AlarmStore
from data.models import Alarm

SYM = "FIXA"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


def _clear(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.commit()


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = iter([7101, 7102, 7103])
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def _add_alarm(symbol: str, price: float) -> int:
    a = Alarm(
        id=None, symbol=symbol, price=price, direction="cross_above",
        active=True, sound=False,
    )
    return AlarmStore.add(a)


class _View:
    """Minimal stand-in for a chart view registered on a session."""


# ── Fix 1: detach_view notifies the alarm monitor ──────────────────────────


def test_fix1_detach_view_promotes_to_headless_monitoring(monkeypatch, qapp):
    """Reviewer fix 1 [HIGH]: detaching the last view of a session with an
    active alarm must promote it to headless monitoring (monitored=True,
    views==0) via alarm_monitor.on_session_detached — NOT tear it down.

    Pre-fix: the shadowing second detach_view never notifies the monitor,
    so the session is torn down and the alarm goes unmonitored.
    """
    _clear(SYM)
    win = _make_window(monkeypatch, qapp)
    try:
        _add_alarm(SYM, 100.0)

        session = win.get_or_create_session(SYM)
        view = _View()
        session.attach_view(view, TF, sync=False)
        assert session.views, "view should be attached"

        notified = []
        orig = win.alarm_monitor.on_session_detached
        win.alarm_monitor.on_session_detached = (
            lambda s: (notified.append(s), orig(s))
        )

        session.detach_view(view)
        qapp.processEvents()

        assert notified, "on_session_detached was never invoked (dead code path)"
        assert SYM in win._sessions, "session was torn down instead of monitored"
        assert session.monitored is True, "session not promoted to headless monitoring"
        assert session.views == [], "views should be empty after detach"
    finally:
        _clear(SYM)
        win.close()
