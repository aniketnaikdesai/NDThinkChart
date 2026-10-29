"""P13-T2 — transactional attach with explicit acquisition-state tracking (D49.2).

T21: per-injection-point cases (sync raise, registration raise, save raise):
a failed offscreen attach leaves no stale session view, the realtime hold
count unchanged, the pop-out unregistered, and the signals disconnected.
T22: a failed second attach on a shared live session leaves the surviving
view's membership, hold, and updates undisturbed.
"""

from __future__ import annotations

import itertools

import pytest

SYMBOL = "P13A"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300

_SIGNALS = (
    "bar_updated",
    "bars_refreshed",
    "alarms_changed",
    "drawings_changed",
)

_SLOTS = (
    "_on_bar_updated",
    "_on_bars_refreshed",
    "_on_alarms_changed",
    "_on_drawings_changed",
)


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter(range(9001, 9200))
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    # D42's depth floor (S17) can issue many chunks from one load, so hand out
    # historical reqIds unbounded rather than exhausting a fixed list.
    hids = itertools.count(9301)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def _make_popout(win, symbol=SYMBOL, timeframe=TF):
    from ui.popout_window import PopoutChartWindow

    return PopoutChartWindow(symbol, timeframe, "Candles", False, win)


def _boom_factory(message):
    def _boom(*args, **kwargs):
        raise RuntimeError(message)

    return _boom


@pytest.mark.parametrize("point", ["sync", "registration", "save"])
def test_attach_failure_unwinds_acquired_steps(monkeypatch, qapp, point):
    """T21: each failure-injection point unwinds exactly what attach acquired."""
    from data.popout_store import PopoutStore

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        session = win._sessions[SYMBOL]
        holders_before = session._rt_holders
        views_before = list(session.views)
        assert holders_before >= 1  # the main chart holds one RT hold

        popout = _make_popout(win)
        if point == "sync":
            monkeypatch.setattr(
                session, "attach_view", _boom_factory("boom-sync")
            )
        elif point == "registration":
            monkeypatch.setattr(
                win, "_register_popout", _boom_factory("boom-registration")
            )
        else:
            monkeypatch.setattr(
                PopoutStore, "save", _boom_factory("boom-save")
            )

        with pytest.raises(RuntimeError, match=f"boom-{point}"):
            popout.attach()
        qapp.processEvents()

        # No stale session view (and the pre-existing views are untouched).
        assert popout.chart not in session.views
        assert list(session.views) == views_before
        # The realtime hold count is unchanged by the failed attach — the
        # save/registration failures acquired a hold and released exactly it;
        # the sync failure never acquired one.
        assert session._rt_holders == holders_before
        # The pop-out is unregistered.
        assert popout not in win._popouts
        # Every connected signal is disconnected: disconnecting again raises,
        # which is the Qt proof the slot is no longer connected (the same
        # signal detach() itself relies on for never-connected slots).
        for signal_name, slot_name in zip(_SIGNALS, _SLOTS):
            signal = getattr(session, signal_name)
            slot = getattr(popout, slot_name)
            with pytest.raises((RuntimeError, TypeError)):
                signal.disconnect(slot)
        # The failed attach drops its session reference so a later detach()
        # skips the RT/view block instead of releasing a hold it never kept.
        assert popout._session is None
        # NOTE: the failed popout is intentionally not closed here — its
        # cleanup already ran in the unwind above, and closing would route
        # through detach() paths owned outside this task. It is GC'd with
        # the test function (parentless offscreen widget, no session state).
    finally:
        win.close()


def test_failed_second_attach_leaves_survivor_undisturbed(monkeypatch, qapp):
    """T22: a failed attach on a shared live session never disturbs survivors."""
    from data.popout_store import PopoutStore

    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        session = win._sessions[SYMBOL]
        req_id = session.rt_req_id

        # First pop-out attaches cleanly (main chart + survivor = 2 holds).
        survivor = _make_popout(win)
        survivor.attach()
        qapp.processEvents()
        assert survivor in win._popouts
        assert session._rt_holders == 2

        # Seed one bar: a tick on an empty chart only appends on a new
        # candle, so without this the survivor update would not be observable.
        win._on_realtime_bar(
            req_id, NOW_TS + 1, 100.0, 100.1, 99.9, 100.0, 100.0, 100.0, 5
        )
        qapp.processEvents()
        assert survivor.chart._bars
        seed_close = survivor.chart._bars[-1].close

        # The second attach fails (at the last step, after acquiring view +
        # signals + hold + registration, so the unwind is maximal).
        monkeypatch.setattr(
            PopoutStore, "save", _boom_factory("boom-save-second")
        )
        failed = _make_popout(win)
        with pytest.raises(RuntimeError, match="boom-save-second"):
            failed.attach()
        qapp.processEvents()

        # The failed attach left nothing behind...
        assert failed.chart not in session.views
        assert failed not in win._popouts
        # ...and the survivor keeps its membership, hold, and updates.
        assert survivor.chart in session.views
        assert survivor in win._popouts
        assert session._rt_holders == 2
        win._on_realtime_bar(
            req_id, NOW_TS + 6, 101.0, 101.5, 100.5, 101.0, 101.0, 101.0, 7
        )
        qapp.processEvents()
        assert survivor.chart._bars[-1].close != seed_close

        survivor.close()
        qapp.processEvents()
        # RT refcount back to 1 (main chart only).
        assert session._rt_holders == 1
    finally:
        win.close()
