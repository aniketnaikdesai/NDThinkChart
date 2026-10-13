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


# ── Fix 2: pop-out read-only holes in IDLE interactions ────────────────────

from PyQt6.QtCore import QPointF, Qt, QEvent
from PyQt6.QtGui import QKeyEvent


class _MouseEv:
    def __init__(self, button, scene_pos=None, finish=False):
        self._button = button
        self._scene_pos = scene_pos or QPointF(0, 0)
        self._finish = finish

    def button(self):
        return self._button

    def scenePos(self):
        return self._scene_pos

    def isFinish(self):
        return self._finish


def _popout_with_alarm(monkeypatch, qapp):
    """Window + pop-out whose alarm overlay holds one alarm at 100.0."""
    _clear(SYM)
    win = _make_window(monkeypatch, qapp)
    win._now_ts = lambda: NOW_TS
    win.load_chart(SYM, TF)
    win._open_popout()
    qapp.processEvents()
    popout = win._popouts[0]
    overlay = popout.chart.alarm_overlay
    alarm = Alarm(id=901, symbol=SYM, price=100.0, direction="cross_above",
                  active=True, sound=False)
    overlay.set_data([alarm])
    return win, popout, overlay, alarm


def test_fix2a_popout_alarm_drag_does_not_mutate_price(monkeypatch, qapp):
    """Reviewer fix 2a: dragging an alarm line in a pop-out must not mutate
    the shared Alarm.price (session evaluation would use the wrong level)."""
    win, popout, overlay, alarm = _popout_with_alarm(monkeypatch, qapp)
    try:
        assert popout.chart._editable is False
        # Simulate a drag in flight ending at a different y.
        overlay._drag = {"id": alarm.id}
        overlay.view_mouse_drag(_MouseEv(Qt.MouseButton.LeftButton,
                                         QPointF(50, 50), finish=True))
        assert alarm.price == 100.0, (
            f"pop-out drag mutated shared Alarm.price to {alarm.price}"
        )
    finally:
        _clear(SYM)
        win.close()


def test_fix2b_popout_press_does_not_start_alarm_drag(monkeypatch, qapp):
    """Reviewer fix 2b: left-press on an alarm in a pop-out must not start
    a drag (drag-start gate)."""
    win, popout, overlay, alarm = _popout_with_alarm(monkeypatch, qapp)
    try:
        overlay._hit = lambda sp: alarm  # hit-test stub; gate is under test
        handled = overlay.view_mouse_press(
            _MouseEv(Qt.MouseButton.LeftButton, QPointF(10, 10)))
        assert overlay._drag is None, "pop-out press started an alarm drag"
        assert handled is False
    finally:
        _clear(SYM)
        win.close()


def test_fix2c_popout_rightclick_no_alarm_menu(monkeypatch, qapp):
    """Reviewer fix 2c: right-click on an alarm in a pop-out must not show
    the Rearm/Mute/Delete menu (signals connected nowhere)."""
    win, popout, overlay, alarm = _popout_with_alarm(monkeypatch, qapp)
    try:
        shown = []
        overlay._show_menu = lambda a: shown.append(a)
        overlay._hit = lambda sp: alarm
        overlay.view_mouse_click(
            _MouseEv(Qt.MouseButton.RightButton, QPointF(10, 10)))
        assert shown == [], "alarm context menu shown in read-only pop-out"
    finally:
        _clear(SYM)
        win.close()


def test_fix2d_popout_delete_does_not_remove_drawing(monkeypatch, qapp):
    """Reviewer fix 2d: Delete/Backspace in a pop-out must not remove a
    drawing from the overlay."""
    _clear(SYM)
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM, TF)
        win._open_popout()
        qapp.processEvents()
        popout = win._popouts[0]
        assert popout.chart._editable is False

        removed = []
        popout.chart.drawing_overlay.has_selection = lambda: True
        popout.chart.drawing_overlay.delete_selected = (
            lambda: removed.append(True))

        ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete,
                       Qt.KeyboardModifier.NoModifier)
        popout.chart.keyPressEvent(ev)
        assert removed == [], "Delete removed a drawing in read-only pop-out"
    finally:
        _clear(SYM)
        win.close()


def test_fix2e_popout_drawing_drag_does_not_mutate_payload(monkeypatch, qapp):
    """Fix 2 (extra hole found in fix pass): IDLE-mode drawing drag in a
    pop-out must not mutate the shared drawing payload."""
    _clear(SYM)
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM, TF)
        win._open_popout()
        qapp.processEvents()
        popout = win._popouts[0]
        dov = popout.chart.drawing_overlay
        assert popout.chart._editable is False
        assert dov._editable is False

        # A horizontal-line drawing whose payload the drag would rewrite.
        from data.models import Drawing
        d = Drawing(id=902, symbol=SYM, kind="horizontal",
                    payload={"y": 100.0})
        dov._drawings = [d]
        dov._drag = {"id": 902, "point_index": -1, "body": True,
                     "locked": False, "grab": (0.0, 0.0)}
        dov.view_mouse_drag(_MouseEv(Qt.MouseButton.LeftButton,
                                     QPointF(10, 10), finish=True))
        assert d.payload["y"] == 100.0, (
            f"pop-out drag mutated shared drawing payload: {d.payload}"
        )
    finally:
        _clear(SYM)
        win.close()
