"""Phase 3 fix-pass regression tests (reviewer REQUEST-CHANGES items).

Each test was written red-first against the pre-fix code.
"""

from __future__ import annotations

import itertools

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
    # D42's depth floor (S17) can issue many chunks from one load, so hand out
    # historical reqIds unbounded rather than exhausting a fixed list.
    hids = itertools.count(7101)
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


def _clear_popouts(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM popouts WHERE symbol=?", (symbol.upper(),))
    db.conn.commit()


# ── Fix 3: _restore_popouts duplicates windows on reconnect ────────────────


def test_fix3_restore_popouts_no_duplicates_on_reconnect(monkeypatch, qapp):
    """Reviewer fix 3: firing _on_connected again (reconnect) must not
    re-open persisted pop-outs that are already open."""
    _clear(SYM)
    _clear_popouts(SYM)
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM, TF)
        win._open_popout()
        qapp.processEvents()
        assert len(win._popouts) == 1

        # Simulate a reconnect: _on_connected fires again.
        win._on_connected()
        qapp.processEvents()

        assert len(win._popouts) == 1, (
            f"reconnect duplicated pop-outs: {len(win._popouts)} open"
        )
        assert len(win._popouts) <= 10  # cap respected
    finally:
        for p in list(win._popouts):
            p.close()
        qapp.processEvents()
        _clear(SYM)
        _clear_popouts(SYM)
        win.close()


# ── Fix 4: pacing-limited pop-out attach never retries ─────────────────────


def test_fix4_popout_pacing_exceeded_schedules_retry(monkeypatch, qapp):
    """Reviewer fix 4: PacingExceeded on pop-out attach must schedule a
    retry with the exception's wait seconds (and show a status) — not
    swallow silently leaving the pop-out on stale cache."""
    from ibkr.pacing import PacingExceeded
    from ui.ticker_session import TickerSession
    import ui.popout_window as popmod

    _clear(SYM)
    _clear_popouts(SYM)
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYM, TF)  # 1st ensure_rt_subscribed: succeeds
        qapp.processEvents()

        real_ensure = TickerSession.ensure_rt_subscribed
        state = {"raise_once": False}

        def fake_ensure(self):
            if state["raise_once"]:
                # The pop-out's attach hits the pacing budget wall.
                state["raise_once"] = False
                raise PacingExceeded(7.0)
            return real_ensure(self)

        monkeypatch.setattr(
            TickerSession, "ensure_rt_subscribed", fake_ensure)

        scheduled = []
        monkeypatch.setattr(
            popmod.QTimer, "singleShot",
            lambda ms, fn: scheduled.append((ms, fn)))

        messages = []
        win.status_bar.showMessage = lambda msg, *a: messages.append(msg)

        state["raise_once"] = True
        win._open_popout()  # pop-out attach: PacingExceeded
        qapp.processEvents()

        assert scheduled, (
            "PacingExceeded on pop-out attach scheduled no retry "
            "(silently stale)"
        )
        ms, retry_fn = scheduled[0]
        assert ms == 7000, f"retry not scheduled with wait_seconds: {ms}ms"
        assert any("pacing" in m.lower() for m in messages), (
            "no pacing status shown for the pop-out"
        )

        # The scheduled retry actually subscribes once budget recovers.
        session = win._sessions[SYM]
        holders_before = session._rt_holders
        retry_fn()
        assert session._rt_holders == holders_before + 1, (
            "retry did not complete the pop-out's RT subscription"
        )
    finally:
        for p in list(win._popouts):
            p.close()
        qapp.processEvents()
        _clear(SYM)
        _clear_popouts(SYM)
        win.close()


SYM2 = "FIXB"


# ── Fix 5: pacing-exhausted headless start never retries ───────────────────


def test_fix5_headless_pacing_exhausted_schedules_retry(monkeypatch, qapp):
    """Reviewer fix 5: a headless monitor start that hits pacing exhaustion
    must schedule a retry with the exception's wait seconds — the session
    must not sit silently unmonitored with nothing scheduled."""
    from ibkr.pacing import PacingExceeded
    from ui.ticker_session import TickerSession
    import services.alarm_monitor as ammon

    _clear(SYM2)
    win = _make_window(monkeypatch, qapp)
    try:
        _add_alarm(SYM2, 100.0)

        real_ensure = TickerSession.ensure_rt_subscribed
        state = {"raise_once": False}

        def fake_ensure(self):
            if state["raise_once"]:
                state["raise_once"] = False
                raise PacingExceeded(6.0)
            return real_ensure(self)

        monkeypatch.setattr(
            TickerSession, "ensure_rt_subscribed", fake_ensure)

        scheduled = []
        monkeypatch.setattr(
            ammon.QTimer, "singleShot",
            lambda ms, fn: scheduled.append((ms, fn)))

        messages = []
        win.status_bar.showMessage = lambda msg, *a: messages.append(msg)

        state["raise_once"] = True
        win.alarm_monitor.reconcile()  # headless start hits the budget wall
        qapp.processEvents()

        session = win._sessions[SYM2]
        assert session.monitored is True
        assert scheduled, (
            "pacing-exhausted headless start scheduled no retry "
            "(silently unmonitored)"
        )
        assert scheduled[0][0] == 6000, (
            f"retry not scheduled with wait_seconds: {scheduled[0][0]}ms"
        )
        assert any(SYM2 in m for m in messages), (
            "unmonitored warning does not name the symbol"
        )

        # The scheduled retry subscribes once budget recovers.
        scheduled[0][1]()
        assert session._rt_req_id is not None, (
            "retry did not complete the headless RT subscription"
        )
    finally:
        _clear(SYM2)
        win.close()
