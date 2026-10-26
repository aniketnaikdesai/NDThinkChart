"""P6-11 (Phase 9) — LWC views in pop-outs, cap 10, per-pop-out memory (DG90).

D24's contract is engine-independent: a pop-out attaches to the symbol's
``TickerSession`` and the session fans bars / studies / drawings / alarms out
to every attached view while the **main chart is the sole writer**. These
cases drive a real ``TickerSession`` through a stub host (no TWS, no
Chromium), so a pop-out exercises exactly the production attach / sync /
close path on the LWC engine — 1, 3 and 6 pop-outs — and accounts each
window's memory (DG90). The cap stays ``MAX_POPOUTS = 10`` (Q62/A107) with
the check ahead of engine selection, so neither engine can bypass it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from config import settings
from data.models import Bar

SYMBOL = "POPA"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300
ENGINE_ENV = "NDT_CHART_ENGINE"


# ── Fixtures / stubs ─────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_popout_ledger():
    """DG90's ledger is process-wide: never leak an entry between cases."""
    from ui.popout_window import POPOUT_MEMORY_LEDGER

    POPOUT_MEMORY_LEDGER.clear()
    yield
    POPOUT_MEMORY_LEDGER.clear()


class _StubStatusBar:
    def __init__(self):
        self.messages: list[str] = []

    def showMessage(self, msg, ms=0):
        self.messages.append(msg)


class _StubRtManager:
    """One reqId per subscribe; records subscribe/unsubscribe calls."""

    def __init__(self):
        self._next = 5001
        self.subscribes: list[tuple] = []
        self.unsubscribed: list[int] = []

    def subscribe(self, symbol, contract):
        self._next += 1
        self.subscribes.append((symbol, self._next))
        return self._next

    def unsubscribe(self, req_id):
        self.unsubscribed.append(req_id)


class _StubSubManager:
    def __init__(self):
        self.registered: dict[int, str] = {}

    def subscribe(self, symbol, req_id, kind, reissue=None, rebind=None):
        self.registered[req_id] = str(kind)

    def unsubscribe(self, req_id):
        self.registered.pop(req_id, None)


class _StubMdManager:
    def __init__(self):
        self._next = 7001
        self.cancelled: list[int] = []

    def req_mkt_data(self, contract, generic_ticks=""):
        self._next += 1
        return self._next

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


class _StubHost:
    """Minimal TickerSession host + the MainWindow pop-out registry surface.

    No DB, no IBKR client, no Qt main window: exactly the host members the
    session and ``PopoutChartWindow`` touch.
    """

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

    # session registry
    def get_or_create_session(self, symbol):
        from ui.ticker_session import TickerSession

        key = symbol.upper()
        if key not in self._sessions:
            self._sessions[key] = TickerSession(key, self)
        return self._sessions[key]

    def _teardown_session(self, symbol):
        self._sessions.pop(symbol, None)

    # reqId routing
    def _register_req_id(self, req_id, session):
        self._req_ids[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_ids.pop(req_id, None)

    # misc session hooks
    def _record_symbol_price(self, symbol, price):
        pass

    def _guard_md_lines(self, symbol, purpose):
        return True

    def _on_session_wave_complete(self, session):
        pass

    def _on_session_prime_complete(self, session):
        pass

    # D24 pop-out registry + cap boundary (MainWindow's members)
    def _register_popout(self, popout):
        if popout not in self._popouts:
            self._popouts.append(popout)

    def _unregister_popout(self, popout):
        if popout in self._popouts:
            self._popouts.remove(popout)


def _bars(count: int = 8, start: int = NOW_TS) -> list[Bar]:
    rows = []
    for i in range(count):
        ts = start - (count - 1 - i) * 300
        price = 100.0 + i
        rows.append(Bar(symbol=SYMBOL, timeframe=TF, ts=ts, open=price - 0.4,
                        high=price + 0.4, low=price - 0.6, close=price,
                        volume=1_000.0 + i))
    return rows


def _alarm(price: float = 101.25):
    return SimpleNamespace(id=1, symbol=SYMBOL, kind="price", price=price,
                           direction="cross_above", active=True,
                           triggered=False, sound=True, note="test")


def _drawing():
    return SimpleNamespace(id=1, symbol=SYMBOL, kind="horizontal",
                           payload={"y": 101.0}, color=None, group_id=None)


def _open_popout(host):
    """One attached + shown pop-out on the engine the env var selects."""
    from ui.popout_window import PopoutChartWindow

    popout = PopoutChartWindow(
        symbol=SYMBOL, timeframe=TF, mode="Candles",
        extended_hours=False, host=host,
    )
    popout.attach()
    popout.show()
    return popout


# ── P6-T11-T11: 1/3/6 LWC pop-outs sync and release ───────────────────


@pytest.mark.parametrize("count", [1, 3, 6])
def test_lwc_popouts_sync_and_account_memory(count, monkeypatch, qapp):
    """AC1: 1/3/6 LWC pop-outs open, sync and close; memory accounted/released."""
    from ui.lwc_view import LwcChartView
    from ui.popout_window import (
        popout_memory_ledger,
        popout_memory_total,
    )

    monkeypatch.setenv(ENGINE_ENV, "lwc")
    host = _StubHost()
    session = host.get_or_create_session(SYMBOL)
    session.set_bars(TF, _bars())

    popouts = [_open_popout(host) for _ in range(count)]
    views = [popout.chart for popout in popouts]

    # ── open: one LWC view per pop-out, read-only, synced from the session ──
    assert len(host._popouts) == count
    assert session.view_count == count
    # One IBKR realtime subscription per symbol, however many pop-outs: the
    # refcount is the number of holding views, the reqId is issued once.
    assert session._rt_holders == count
    assert len(host.rt_manager.subscribes) == 1
    assert session.rt_req_id is not None
    for view in views:
        assert isinstance(view, LwcChartView)
        assert view.editable is False
        assert len(view._bars) == len(_bars())      # initial full sync
        assert view.bridge.counters()["received"] > 0
        # D24: the pop-out is never a writer — no tool, no alarm placement.
        assert view.drawing_overlay.tool_active() is False
        assert view.set_alarm_mode(True) == "IDLE"
        assert view.router.active_mode.name == "IDLE"

    # ── DG90: every pop-out accounted individually, no double counting ──
    ledger = popout_memory_ledger()
    assert len(ledger) == count
    assert set(ledger) == {popout.memory_id for popout in popouts}
    for popout in popouts:
        entry = ledger[popout.memory_id]
        assert entry["engine"] == "lwc"
        assert entry["symbol"] == SYMBOL
        assert entry["bars"] == len(_bars())
        assert entry["buckets"]["op_log"] > 0
        assert entry["total_bytes"] == popout.memory_bytes > 0
    assert popout_memory_total() == sum(
        entry["total_bytes"] for entry in ledger.values())

    # ── sync: one full replace fans out to every pop-out ────────────────
    grown = _bars() + [_bars(1, start=NOW_TS + 300)[0]]
    session.set_bars(TF, grown)
    qapp.processEvents()
    for view in views:
        assert len(view._bars) == len(grown)
    assert all(popout_memory_ledger()[p.memory_id]["bars"] == len(grown)
               for p in popouts)

    # ── sync: a live tick advances the forming bar on every pop-out ─────
    session.prepare_load(TF)
    req_id = session.rt_req_id
    assert req_id is not None
    session.on_realtime_bar(req_id, NOW_TS + 301, 100.0, 100.5, 99.5,
                            100.0, 10.0)
    session.on_realtime_bar(req_id, NOW_TS + 306, 100.0, 100.5, 99.5,
                            102.0, 12.0)
    qapp.processEvents()
    for view in views:
        assert view._bars[-1].close == 102.0

    # ── sync: studies, drawings and alarms via the session fan-out ──────
    studies = [{"type": "sma", "enabled": True, "params": {"period": 3}}]
    session.set_studies(studies)
    session._drawings = [_drawing()]
    session._drawing_groups = []
    session.sync_drawings_to_views()
    session.set_alarms([_alarm()])
    qapp.processEvents()
    for view in views:
        assert view.studies == studies
        assert len(view.drawings) == 1
        assert len(view.alarms) == 1
        assert view.alarm_envelopes                     # line published
        assert view.alarm_envelopes[-1]["ops"][0]["cols"]["price"] == [101.25]

    # ── close: the session and the DG90 ledger both release ─────────────
    for popout in popouts:
        popout.close()
    qapp.processEvents()

    assert session.view_count == 0
    assert host._popouts == []
    assert popout_memory_ledger() == {}
    assert popout_memory_total() == 0
    assert session._rt_holders == 0
    for view in views:
        # The view's private arrays and replay log are gone (no leak)...
        assert view._bars == []
        assert view.memory_bytes()["total_bytes"] == 0
    for popout in popouts:
        assert popout.memory_bytes == 0


# ── P6-T11-T12: the cap stays 10 on both engines ─────────────────────


def test_max_popouts_is_ten():
    """AC2/Q62/A107: the owner-confirmed cap is unchanged."""
    assert settings.MAX_POPOUTS == 10


@pytest.mark.parametrize("engine", ["pyqtgraph", "lwc"])
def test_eleventh_popout_refused_on_either_engine(engine, monkeypatch, qapp):
    """AC2: the 11th open is refused with the D24 message on both engines.

    The cap check runs in ``MainWindow._open_popout`` *before* the window (and
    therefore the engine view) is constructed, so no engine can bypass it —
    asserted by the factory not being called for the refused request.
    """
    from ibkr.client import IBApiClient
    from ui import popout_window
    from ui.chart_view import PyqtgraphChartView
    from ui.lwc_view import LwcChartView
    from ui.main_window import MainWindow

    if engine == "lwc":
        monkeypatch.setenv(ENGINE_ENV, "lwc")
    else:
        monkeypatch.delenv(ENGINE_ENV, raising=False)

    real_factory = popout_window.create_chart_view
    created: list = []

    def _spy(*args, **kwargs):
        view = real_factory(*args, **kwargs)
        created.append(view)
        return view

    monkeypatch.setattr(popout_window, "create_chart_view", _spy)

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    win = MainWindow()
    # Nothing to talk to: the session subscribe path is all the pop-out needs.
    win.rt_manager.subscribe = lambda *a, **k: 6001
    win.md_manager.req_mkt_data = lambda *a, **k: 6002
    win.md_manager.cancel_mkt_data = lambda *a, **k: None
    win._current_symbol = SYMBOL
    win._current_tf = TF
    try:
        messages: list[str] = []
        win.status_bar.showMessage = lambda msg, *a, **k: messages.append(msg)

        for _ in range(settings.MAX_POPOUTS + 2):
            win._open_popout()
        qapp.processEvents()

        assert len(win._popouts) == settings.MAX_POPOUTS
        assert len(created) == settings.MAX_POPOUTS
        assert any(
            "pop-out limit reached" in message.lower()
            and str(settings.MAX_POPOUTS) in message
            for message in messages
        ), messages

        # Every accepted pop-out landed on the engine under test.
        expected = LwcChartView if engine == "lwc" else PyqtgraphChartView
        assert all(isinstance(popout.chart, expected) for popout in win._popouts)

        for popout in list(win._popouts):
            popout.close()
        qapp.processEvents()
        assert win._popouts == []
    finally:
        win.close()


# ── P6-T11-T13: residue scan (no out-of-scope surface) ───────────────


def test_residue_scan_no_out_of_scope_surface(monkeypatch, qapp):
    """AC3: sessions, persistence, dock and engine-default surfaces untouched."""
    import inspect

    from data import popout_store
    from data.popout_store import PopoutStore
    from ui import chart_view, lwc_view, popout_window, ticker_session

    # 1. Pop-out persistence API unchanged: same four entries, same signature.
    public = sorted(name for name in vars(PopoutStore)
                    if not name.startswith("_"))
    assert public == ["clear", "delete", "load_all", "save"]
    assert list(inspect.signature(PopoutStore.save).parameters) == [
        "symbol", "timeframe", "mode", "ext_hours", "geometry",
    ]
    store_src = inspect.getsource(popout_store)
    for token in ("lwc", "Lwc", "popout_memory", "engine"):
        assert token not in store_src

    # 2. The session fan-out (D24 single writer) carries no engine vocabulary:
    #    no new store/DB/service/order surface entered it.
    session_src = inspect.getsource(ticker_session)
    for token in ("LwcChartView", "lwc_view", "popout_memory",
                  "create_chart_view", "PopoutStore"):
        assert token not in session_src

    # 3. The cap is unchanged (Q62/A107) and reads from settings, not a copy.
    assert settings.MAX_POPOUTS == 10
    assert "MAX_POPOUTS = 10" in inspect.getsource(settings)

    # 4. pyqtgraph stays present and default: the factory resolves the default
    #    engine (no env override, no persisted override) to the pyqtgraph view.
    monkeypatch.delenv("NDT_CHART_ENGINE", raising=False)
    monkeypatch.setattr(chart_view, "_read_persisted_engine", lambda: "")
    assert isinstance(chart_view.create_chart_view(editable=False),
                      chart_view.PyqtgraphChartView)

    # 5. The pop-out module added no order / DB / network path, and no dock or
    #    watchlist surface; persistence semantics stay PopoutStore's.
    popout_src = inspect.getsource(popout_window)
    for token in ("reqHistoricalData", "reqMktData", "placeOrder",
                  "import sqlite3", "sqlite3.", "requests", "urllib",
                  "QDockWidget", "watchlist", "orders"):
        assert token not in popout_src, token
    # The only ibkr import is the unchanged pacing deferral hook.
    assert "from ibkr.pacing import PacingExceeded" in popout_src

    # 6. The LWC driver stays renderer-only: no broker, DB, network or main
    #    window import (the pre-existing `data` imports are the one shared
    #    chart model / aggregator contract, not a store).
    lwc_src = inspect.getsource(lwc_view)
    for token in ("placeOrder", "reqHistoricalData", "reqMktData",
                  "ibkr.", "sqlite3", "ui.main_window"):
        assert token not in lwc_src, token

    # 7. Pop-outs on the default engine still get the pyqtgraph panel — the
    #    new seam did not make LWC the default.
    host = _StubHost()
    host.get_or_create_session(SYMBOL).set_bars(TF, _bars())
    popout = _open_popout(host)
    try:
        assert isinstance(popout.chart, chart_view.PyqtgraphChartView)
        assert popout.memory_bytes > 0
    finally:
        popout.close()
        qapp.processEvents()
