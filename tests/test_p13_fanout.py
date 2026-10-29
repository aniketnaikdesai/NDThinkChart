"""P13-T4 — single drawing fan-out (D49.4; S-P13-4).

T41 pins the current behavior FIRST (green-first by design): N pop-outs on
one symbol, one drawing change through the production commit sequence
(``reload_drawings`` + one ``sync_drawings_to_views``, mirroring
``MainWindow._on_drawing_added/_updated/_deleted/_groups_changed``),
record the per-change ``sync_drawings_to_views`` fan-out count and the
per-view end state. T42 asserts the dedupe: exactly one all-view sync per
change with end-state equality to the T41 baseline, while the
``drawings_changed`` signal and the per-pop-out wiring stay connected
(handler reduced to a single-view refresh of its receiving view, A125).

Both cases drive a real ``TickerSession`` through the stub host (no TWS,
no Chromium) with real pop-out windows, mirroring ``test_lwc_popouts.py``.
"""

from __future__ import annotations

from types import SimpleNamespace

SYMBOL = "P13F"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300
N_POPOUTS = 3

# Pinned by T41 on the current tree: per-change sync count + per-view end
# state. T42 asserts against it (falls back to the seeded expectation when
# T42 is run in isolation).
BASELINE: dict = {}


# ── Stubs (adapted from tests/test_lwc_popouts.py) ─────────────────────


class _StubStatusBar:
    def showMessage(self, msg, ms=0):
        pass


class _StubRtManager:
    def __init__(self):
        self._next = 5001

    def subscribe(self, symbol, contract):
        self._next += 1
        return self._next

    def unsubscribe(self, req_id):
        pass


class _StubSubManager:
    def subscribe(self, symbol, req_id, kind, reissue=None, rebind=None):
        pass

    def unsubscribe(self, req_id):
        pass


class _StubMdManager:
    def __init__(self):
        self._next = 7001

    def req_mkt_data(self, contract, generic_ticks=""):
        self._next += 1
        return self._next

    def cancel_mkt_data(self, req_id):
        pass


class _StubHost:
    """Minimal TickerSession host + pop-out registry surface."""

    def __init__(self):
        self._popouts: list = []
        self._sessions: dict = {}
        self._req_ids: dict[int, object] = {}
        self.status_bar = _StubStatusBar()
        self.rt_manager = _StubRtManager()
        self.sub_manager = _StubSubManager()
        self.md_manager = _StubMdManager()
        self.alarm_monitor = None
        self.volume_baseline = None

    def get_or_create_session(self, symbol):
        from ui.ticker_session import TickerSession

        key = symbol.upper()
        if key not in self._sessions:
            self._sessions[key] = TickerSession(key, self)
        return self._sessions[key]

    def _teardown_session(self, symbol):
        self._sessions.pop(symbol, None)

    def _register_req_id(self, req_id, session):
        self._req_ids[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_ids.pop(req_id, None)

    def _record_symbol_price(self, symbol, price):
        pass

    def _guard_md_lines(self, symbol, purpose):
        return True

    def _on_session_wave_complete(self, session):
        pass

    def _on_session_prime_complete(self, session):
        pass

    def _register_popout(self, popout):
        if popout not in self._popouts:
            self._popouts.append(popout)

    def _unregister_popout(self, popout):
        if popout in self._popouts:
            self._popouts.remove(popout)


def _bars(count: int = 8, start: int = NOW_TS):
    from data.models import Bar

    rows = []
    for i in range(count):
        ts = start - (count - 1 - i) * 300
        price = 100.0 + i
        rows.append(Bar(symbol=SYMBOL, timeframe=TF, ts=ts, open=price - 0.4,
                        high=price + 0.4, low=price - 0.6, close=price,
                        volume=1_000.0 + i))
    return rows


def _drawing(drawing_id: int = 1):
    return SimpleNamespace(id=drawing_id, symbol=SYMBOL, kind="horizontal",
                           payload={"y": 101.0}, color=None, group_id=None)


def _seed_store(monkeypatch, drawings):
    """Point the drawing store at canned records (hermetic, no DB rows)."""
    import data.drawing_store as store_mod

    monkeypatch.setattr(store_mod.DrawingStore, "drawings_for_symbol",
                        staticmethod(lambda symbol: list(drawings)))
    monkeypatch.setattr(store_mod.DrawingStore, "groups_for_symbol",
                        staticmethod(lambda symbol: []))


def _open_popouts(host, count=N_POPOUTS):
    from ui.popout_window import PopoutChartWindow

    popouts = []
    for _ in range(count):
        popout = PopoutChartWindow(symbol=SYMBOL, timeframe=TF,
                                   mode="Candles", extended_hours=False,
                                   host=host)
        popout.attach()
        popout.show()
        popouts.append(popout)
    return popouts


def _close_popouts(popouts, qapp):
    for popout in popouts:
        popout.close()
    qapp.processEvents()


def _run_scenario(monkeypatch, qapp):
    """N pop-outs, one drawing change, measure the fan-out.

    The change goes through the production commit sequence (reload + one
    direct all-view sync, as in ``MainWindow._on_drawing_updated``); a
    second probe uses a bare ``drawings_changed`` emission to show whether
    the handlers themselves still fan out and that the wiring is live.

    Returns ``(commit_calls, emit_calls, end_state, refreshed_state)``:
    sync counts for the commit and the bare emission, per-view drawing
    counts after the commit, and per-view counts after the wiring probe.
    """
    host = _StubHost()
    session = host.get_or_create_session(SYMBOL)
    session.set_bars(TF, _bars())
    _seed_store(monkeypatch, [_drawing(1)])
    popouts = _open_popouts(host)
    assert len(host._popouts) == N_POPOUTS
    assert session.view_count == N_POPOUTS
    qapp.processEvents()

    calls: list[str] = []
    orig_sync = session.sync_drawings_to_views

    def _spy():
        calls.append("sync")
        return orig_sync()

    session.sync_drawings_to_views = _spy
    try:
        # One drawing change through the production commit sequence.
        session.reload_drawings()
        session.sync_drawings_to_views()
        qapp.processEvents()
        commit_calls = len(calls)

        end_state = tuple(len(p.chart.drawings) for p in popouts)

        # Bare-emission probe: do the handlers themselves fan out, and is
        # the signal/slot wiring still live?
        calls.clear()
        _seed_store(monkeypatch, [_drawing(1), _drawing(2)])
        session.reload_drawings()
        session.drawings_changed.emit()
        qapp.processEvents()
        emit_calls = len(calls)

        refreshed_state = tuple(len(p.chart.drawings) for p in popouts)
    finally:
        _close_popouts(popouts, qapp)
    return commit_calls, emit_calls, end_state, refreshed_state


def test_p13_t41_pin_fanout_baseline(monkeypatch, qapp):
    """T41 (AC-D49.4 pin): record per-change fan-out count + end state.

    Green-first: passes on the current tree (count N+1 through the
    commit sequence) and after the dedupe (count 1) — it pins the end
    state T42 asserts against.
    """
    commit_calls, emit_calls, end_state, refreshed_state = _run_scenario(
        monkeypatch, qapp)
    BASELINE.update(commit_calls=commit_calls, emit_calls=emit_calls,
                    end_state=end_state)

    # At least one all-view sync per change on every tree.
    assert commit_calls >= 1
    # Every receiving view converged on the changed records.
    assert end_state == (1,) * N_POPOUTS
    # The signal/slot wiring delivers a later change to every view
    # (notification role intact, whatever the fan-out).
    assert refreshed_state == (2,) * N_POPOUTS


def test_p13_t42_single_sync_per_change(monkeypatch, qapp):
    """T42 (AC-D49.4 dedupe): exactly one all-view sync per change.

    Red without the dedupe (N handler fan-outs + the direct sync per
    change); green post-fix with end state identical to the T41 baseline.
    Signal + per-pop-out wiring stay connected (the bare-emit probe
    refreshes every view with zero all-view syncs).
    """
    commit_calls, emit_calls, end_state, refreshed_state = _run_scenario(
        monkeypatch, qapp)
    expected_end_state = BASELINE.get("end_state", (1,) * N_POPOUTS)

    # Exactly one all-view sync per change at the change point.
    assert commit_calls == 1
    # Handlers no longer fan out: a bare emission costs zero all-view
    # syncs (single-view refreshes only).
    assert emit_calls == 0
    # End state identical to the pinned baseline.
    assert end_state == expected_end_state == (1,) * N_POPOUTS
    # Wiring kept: the later change still reaches every receiving view.
    assert refreshed_state == (2,) * N_POPOUTS
