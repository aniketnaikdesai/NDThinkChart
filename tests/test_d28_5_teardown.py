"""D28.5 — explicit teardown on close (AC-D28.5).

closeEvent must: set a _closing flag (slots early-return), cancel
lookups, disarm timers, cancel subscriptions, disconnect, clear the UI,
and join the ibkr-reader thread with a timeout. Closing mid-backfill
must not touch cleared widgets or strand the reader thread.
"""
import threading

import pytest


def _make_window(monkeypatch, qapp, client_patches=()):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    for name, fn in client_patches:
        monkeypatch.setattr(IBApiClient, name, fn)
    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def test_close_mid_backfill_joins_reader_thread(monkeypatch, qapp):
    """Close with an in-flight wave: clean teardown, thread joined."""
    run_started = threading.Event()
    stop_reader = threading.Event()

    def fake_run(self):
        run_started.set()
        stop_reader.wait(timeout=30)

    def fake_disconnect(self):
        stop_reader.set()

    win = _make_window(
        monkeypatch, qapp,
        client_patches=[("run", fake_run), ("disconnect", fake_disconnect)],
    )
    try:
        assert run_started.wait(timeout=5), "reader thread never started"

        # Start a backfill wave that never completes (stubbed historical).
        hids = iter(range(7001, 7100))
        win.md_manager.req_historical_data = lambda *a, **k: next(hids)
        win.rt_manager.subscribe = lambda *a, **k: 4242
        win._now_ts = lambda: 1_760_000_000
        win.symbol_input.setText("TEAR")
        win.tf_combo.setCurrentText("5 mins")
        win.load_chart()
        qapp.processEvents()
        session = win.get_or_create_session("TEAR")
        assert session._history_req_ids, "expected an in-flight wave"

        win.close()
        qapp.processEvents()

        assert win._closing, "_closing flag must be set"
        assert not win._reader_thread.is_alive(), \
            "ibkr-reader thread must join within the timeout"
        assert session._history_req_ids == set(), \
            "in-flight wave must be cancelled"
        assert not session._history_wave_timer.isActive()
        assert not session._wave_continue_timer.isActive()
        assert not session._prime_timer.isActive()
    finally:
        stop_reader.set()


def test_slots_early_return_when_closing(monkeypatch, qapp):
    """With _closing set, data slots are no-ops (no cleared-widget touch)."""
    win = _make_window(monkeypatch, qapp)
    try:
        hids = iter(range(7101, 7200))
        win.md_manager.req_historical_data = lambda *a, **k: next(hids)
        win.rt_manager.subscribe = lambda *a, **k: 4242
        win._now_ts = lambda: 1_760_000_000
        win.symbol_input.setText("TEAR2")
        win.tf_combo.setCurrentText("5 mins")
        win.load_chart()
        qapp.processEvents()
        session = win.get_or_create_session("TEAR2")
        req_id = next(iter(session._history_req_ids))
        n_bars_before = len(session._pending_bars)

        win._closing = True
        from data.models import Bar

        bar = Bar("TEAR2", "5 mins", 1_760_000_000, 1.0, 1.0, 1.0, 1.0, 1.0)
        # None of these may mutate session state once closing.
        win._on_historical_bar(req_id, bar)
        win._on_historical_data_end(req_id)
        win._on_realtime_bar(req_id, 1_760_000_000, 1.0, 1.0, 1.0, 1.0,
                             1.0, 1.0, 1)
        win._on_error(req_id, 162, "pacing violation")
        qapp.processEvents()
        assert len(session._pending_bars) == n_bars_before
        assert session._history_req_ids, \
            "closing slots must not drop in-flight requests"
    finally:
        win.close()


def test_close_event_is_idempotent(monkeypatch, qapp):
    """A second closeEvent after teardown must not raise."""
    from PyQt6.QtGui import QCloseEvent

    win = _make_window(monkeypatch, qapp)
    try:
        win.close()
        qapp.processEvents()
        assert win._closing
        win.closeEvent(QCloseEvent())  # must not raise
        qapp.processEvents()
    finally:
        pass
