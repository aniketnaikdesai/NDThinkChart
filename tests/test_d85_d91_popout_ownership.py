"""D85/D91 — the main window owns its pop-outs; a failed open leaves nothing.

Invariant under test:

* A window is closed by its owner: ``MainWindow.closeEvent`` closes every
  registered pop-out FIRST (iterating a copy, each close in its own guard),
  before session teardown — so each pop-out releases its RT hold and detaches
  its view while the session it references is still alive.
* An open is one transaction: a failure anywhere between construction and the
  last save (both open sites) closes the constructed window, unregisters
  nothing that was not registered, retains no hold, and reports exactly once —
  never an ``UnboundLocalError`` from inside the handler, and
  ``_discard_popout(popout, exc)`` tolerates a ``None`` window.

Offscreen harness follows ``tests/test_d24_popouts.py``: real ``MainWindow``,
monkeypatched ``connect``, unbounded fake req ids, temp DB from conftest.
"""

from __future__ import annotations

import itertools

from PyQt6.QtWidgets import QApplication

SYMBOL = "POPOWN"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300


def _visible_windows() -> set:
    """Currently visible top-level widgets (the "no window left behind" lens)."""
    return {w for w in QApplication.topLevelWidgets() if w.isVisible()}


def _make_window(monkeypatch, qapp):
    """The shipped offscreen harness (test_d24_popouts) plus one loaded chart."""
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    win._transport_ready = lambda: True
    ids = itertools.count(6001)
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    hids = itertools.count(6101)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    win._now_ts = lambda: NOW_TS
    win.load_chart(SYMBOL, TF)
    qapp.processEvents()
    return win


def _capture_messages(win) -> list[str]:
    """Record status-bar lines (the "reports exactly once" lens)."""
    messages: list[str] = []
    win.status_bar.showMessage = lambda msg, *a: messages.append(msg)
    return messages


# ── D91: a failed open leaves nothing ───────────────────────────────────────


def test_p28_t7_01_tail_save_failure_leaves_nothing(monkeypatch, qapp):
    """AC-D91.1, case (a): PopoutStore.save forced to raise during an open.

    The constructed window is closed and not visible, the registry is
    unchanged, the session's hold count is exactly what it was, and exactly
    one status line is shown (A238: the guard stays even if this settling
    experiment shows no leak in the pre-fix tree).
    """
    import ui.popout_window as popout_window
    from data.popout_store import PopoutStore

    win = _make_window(monkeypatch, qapp)
    created: list = []
    try:
        session = win._sessions[SYMBOL]
        before_holders = session._rt_holders
        before_windows = _visible_windows()

        real_cls = popout_window.PopoutChartWindow

        class SpyWindow(real_cls):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                created.append(self)

        monkeypatch.setattr(popout_window, "PopoutChartWindow", SpyWindow)

        def _boom(*a, **k):
            raise RuntimeError("save exploded")

        monkeypatch.setattr(PopoutStore, "save", staticmethod(_boom))
        messages = _capture_messages(win)

        win._open_popout()

        assert created, "the window must have been constructed before the save"
        assert created[0].isVisible() is False
        assert win._popouts == []
        assert session._rt_holders == before_holders
        assert len(messages) == 1
        assert "Pop-out failed to open" in messages[0]
        assert "save exploded" in messages[0]
        qapp.processEvents()
        assert _visible_windows() == before_windows
    finally:
        win.close()
        qapp.processEvents()


def test_p28_t7_02_attach_save_failure_leaves_nothing(monkeypatch, qapp):
    """AC-P28-04-1, case (b): the same raise at attach()'s own save site."""
    import ui.popout_window as popout_window
    from data.popout_store import PopoutStore

    win = _make_window(monkeypatch, qapp)
    created: list = []
    try:
        session = win._sessions[SYMBOL]
        before_holders = session._rt_holders
        before_windows = _visible_windows()

        real_cls = popout_window.PopoutChartWindow

        class SpyWindow(real_cls):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                created.append(self)

        monkeypatch.setattr(popout_window, "PopoutChartWindow", SpyWindow)

        calls = {"n": 0}

        def _flaky(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                # attach()'s own save — succeeds, so the window registers and
                # acquires its hold before the tail save fails.
                return 4242
            raise RuntimeError("attach save exploded")

        monkeypatch.setattr(PopoutStore, "save", staticmethod(_flaky))
        messages = _capture_messages(win)

        win._open_popout()

        assert calls["n"] == 2, "attach's save then the D49.6 tail save"
        assert created and created[0].isVisible() is False
        assert win._popouts == []
        assert session._rt_holders == before_holders
        assert len(messages) == 1
        assert "Pop-out failed to open" in messages[0]
        qapp.processEvents()
        assert _visible_windows() == before_windows
    finally:
        win.close()
        qapp.processEvents()


def test_p28_t7_07_construction_and_restore_path_failures_report_once(
    monkeypatch, qapp
):
    """AC-P28-04-1, case (g): a pre-construction raise at both open sites.

    ``PopoutChartWindow`` raising before construction completes must report
    once (no ``UnboundLocalError`` masking it), and ``_ensure_restore_data_path``
    raising inside ``_restore_popouts`` must do the same while the restore loop
    survives. Neither leaves a registered pop-out or a new visible window.
    """
    import ui.popout_window as popout_window
    from data.popout_store import PopoutStore

    win = _make_window(monkeypatch, qapp)
    try:
        before_windows = _visible_windows()

        class BoomWindow(popout_window.PopoutChartWindow):
            def __init__(self, *a, **k):
                raise RuntimeError("construct exploded")

        monkeypatch.setattr(popout_window, "PopoutChartWindow", BoomWindow)
        messages = _capture_messages(win)

        # (1) the user's open: the constructor raises before the local binds.
        win._open_popout()  # must not raise (UnboundLocalError included)
        assert len(messages) == 1
        assert "Pop-out failed to open" in messages[0]
        assert "construct exploded" in messages[0]
        assert win._popouts == []
        assert _visible_windows() == before_windows

        # (2) the restore site: the data-path ensure raises before any window.
        record = {
            "symbol": SYMBOL,
            "timeframe": TF,
            "mode": "Candles",
            "ext_hours": True,
            "geometry": {"x": 0, "y": 0, "w": 640, "h": 420},
        }
        monkeypatch.setattr(
            PopoutStore, "load_all", staticmethod(lambda: [dict(record)])
        )

        def _boom_ensure(_record):
            raise RuntimeError("data path exploded")

        monkeypatch.setattr(win, "_ensure_restore_data_path", _boom_ensure)
        win._ibkr_connected = True
        messages.clear()

        win._restore_popouts()  # must not raise either

        assert len(messages) == 1
        assert "Pop-out failed to open" in messages[0]
        assert "data path exploded" in messages[0]
        assert win._popouts == []
        assert _visible_windows() == before_windows
    finally:
        win.close()
        qapp.processEvents()


# ── D85: a window is closed by its owner ────────────────────────────────────


def test_p28_t7_03_main_close_closes_registered_popouts(monkeypatch, qapp):
    """AC-D85.1, case (c): two registered pop-outs, then the main close."""
    import ui.popout_window as popout_window

    baseline = _visible_windows()
    win = _make_window(monkeypatch, qapp)
    detaches: list = []
    real_detach = popout_window.PopoutChartWindow.detach

    def _spy_detach(self):
        detaches.append(self)
        return real_detach(self)

    monkeypatch.setattr(popout_window.PopoutChartWindow, "detach", _spy_detach)
    try:
        win._open_popout()
        win._open_popout()
        qapp.processEvents()

        windows = list(win._popouts)
        assert len(windows) == 2

        win.close()
        qapp.processEvents()

        assert win._popouts == []
        for popout in windows:
            assert detaches.count(popout) == 1
            try:
                assert popout.isVisible() is False
            except RuntimeError:
                pass  # WA_DeleteOnClose already destroyed the C++ object
        # No other visible top-level widget remains beyond the pre-test set.
        assert _visible_windows() <= baseline
    finally:
        win.close()
        qapp.processEvents()


def test_p28_t7_04_already_closed_popout_is_not_touched(monkeypatch, qapp):
    """AC-D85.2, case (d): one pop-out closed first, then the main close."""
    import ui.popout_window as popout_window

    win = _make_window(monkeypatch, qapp)
    detaches: list = []
    real_detach = popout_window.PopoutChartWindow.detach

    def _spy_detach(self):
        detaches.append(self)
        return real_detach(self)

    monkeypatch.setattr(popout_window.PopoutChartWindow, "detach", _spy_detach)
    try:
        win._open_popout()
        win._open_popout()
        qapp.processEvents()

        first, second = list(win._popouts)
        first.close()
        qapp.processEvents()
        assert detaches.count(first) == 1

        win.close()  # must not raise, must not touch the closed window
        qapp.processEvents()

        assert detaches.count(first) == 1
        assert win._popouts == []
        assert detaches.count(second) == 1
    finally:
        win.close()
        qapp.processEvents()


def test_p28_t7_05_raising_close_does_not_stop_the_main_close(monkeypatch, qapp):
    """AC-P28-04-3, case (e): Journey 75's edge — one pop-out's close raises."""
    import ui.popout_window as popout_window

    baseline = _visible_windows()
    win = _make_window(monkeypatch, qapp)
    detaches: list = []
    real_detach = popout_window.PopoutChartWindow.detach

    def _spy_detach(self):
        detaches.append(self)
        return real_detach(self)

    monkeypatch.setattr(popout_window.PopoutChartWindow, "detach", _spy_detach)
    exploding = healthy = None
    try:
        win._open_popout()
        win._open_popout()
        qapp.processEvents()

        exploding, healthy = list(win._popouts)

        def _boom_close():
            raise RuntimeError("close exploded")

        exploding.close = _boom_close

        win.close()  # nothing propagates out of closeEvent
        qapp.processEvents()

        assert win._popouts == []
        assert detaches.count(healthy) == 1
        try:
            assert healthy.isVisible() is False
        except RuntimeError:
            pass  # WA_DeleteOnClose
        # The guard cannot close a window whose close() raises; every other
        # window is gone and only the exploding one may still be visible.
        assert _visible_windows() - baseline <= {exploding}
    finally:
        for popout in (local for local in (exploding, healthy) if local):
            try:
                popout.hide()
                popout_window.PopoutChartWindow.close(popout)
            except Exception:
                pass
        win.close()
        qapp.processEvents()


def test_p28_t7_06_main_hold_survives_popout_close(monkeypatch, qapp):
    """AC-P28-04-2, case (f): the D68 rule — the pop-out releases at most its own."""
    win = _make_window(monkeypatch, qapp)
    try:
        session = win._sessions[SYMBOL]
        before = session._rt_holders
        assert before == 1  # the main chart's own hold

        win._open_popout()
        qapp.processEvents()
        assert session._rt_holders == before + 1

        popout = win._popouts[0]
        popout.close()
        qapp.processEvents()

        assert session._rt_holders == before
        # The subscription stays live for the main chart.
        assert session.rt_req_id is not None
    finally:
        win.close()
        qapp.processEvents()
