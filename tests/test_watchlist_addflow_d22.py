"""D22-07 — MainWindow connection state, add-enable gating, restore/seed guard
and lookup-service lifecycle (Phase 4).

Integration tests driving a real offscreen ``MainWindow`` (the D21 ``_boot``
pattern: TWS ``connect`` monkeypatched to a no-op). They cover:

  * AC-D22.7.1 (AC-D22.5) — ``_ibkr_connected`` tracks ``_on_connected`` /
    ``_on_disconnected`` and drives ``watchlist_panel.set_add_enabled``;
  * AC-D22.7.2 (S13) — ``_restore_watchlist`` is idempotent: it clears then
    reproduces exactly the persisted set on a reconnect;
  * AC-D22.7.3 (A52/DG44) — the ``watchlist/configured`` sentinel gates
    ``DEFAULT_WATCHLIST`` seeding, so an explicitly emptied list stays empty;
  * AC-D22.7.4 — a ``ContractLookupService`` is built from md_manager + bridge,
    its ``lookup_finished`` is connected, and ``cancel_all`` runs on disconnect.

The ``watchlist/configured`` sentinel is a real (non-injectable) QSettings
value, so every test swaps the window's ``_settings`` for a per-test ini file
(AR-D22-9) and patches ``ui.main_window.db`` with a throwaway SQLite DB — the
real user settings / DB are never touched.

All tests run offscreen (tests/conftest.py sets QT_QPA_PLATFORM=offscreen).
"""

import os

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtTest import QTest

import config.paths as paths
import ui.main_window as main_window
from ibkr.contracts import get_contract_for_symbol
from ibkr.pacing import PacingExceeded
from ui.watchlist_panel import SYMBOL_FIELD, WatchlistPanel


def _isolated_settings(path) -> QSettings:
    try:
        os.remove(path)
    except OSError:
        pass
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    settings.clear()
    settings.sync()
    return settings


def _panel_symbols(panel) -> list[str]:
    """The visible Symbols currently shown by the watchlist table (row order)."""
    col = panel._active_fields.index(SYMBOL_FIELD)
    return [
        panel.table.item(row, col).text()
        for row in range(panel.table.rowCount())
    ]


@pytest.fixture
def window(monkeypatch, qapp, tmp_path):
    """A shown MainWindow with an isolated DB + QSettings; never touches TWS."""
    from ibkr.client import ConnectionState, IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)

    # Throwaway DB: an absolute filename makes get_db_path() return it verbatim.
    db_file = tmp_path / "watchlist_addflow_d22.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))
    from data.db import DB

    fresh = DB()
    # Patch only the name _restore_watchlist reads; the global DB singleton used
    # elsewhere is untouched.
    monkeypatch.setattr(main_window, "db", fresh)

    win = None
    try:
        win = main_window.MainWindow()
        # Q-37: the real IBApiClient is handshake-gated (Q-34/Q-35) while
        # connect is a no-op here, so mark the handshake done at the client
        # level (flags only, mirroring _go_live — no CONNECTED emission, so
        # no connect handling runs during setup). The panel's real
        # market-data path can then subscribe; win._ibkr_connected still
        # starts False and each test drives _on_connected itself.
        win.ib_client._connected = True
        win.ib_client._connection_state = ConnectionState.CONNECTED
        # Swap in per-test settings BEFORE anything can write the real sentinel.
        settings = _isolated_settings(tmp_path / "watchlist_addflow_d22.ini")
        win._settings = settings
        win.resize(1600, 900)
        win.show()
        qapp.processEvents()
        yield win, fresh, settings
    finally:
        if win is not None:
            win.close()
        fresh.conn.close()


# ── D22-07-T01 / AC-D22.7.1 — connection flag gates the add affordance ───────

def test_D22_07_T01_connection_gates_add_enable(window, qapp):
    win, _fresh, _settings = window
    panel = win.watchlist_panel

    # Fresh window: disconnected, add affordances disabled.
    assert win._ibkr_connected is False
    assert not panel.add_button.isEnabled()
    assert not panel.add_action.isEnabled()

    win._on_connected()
    qapp.processEvents()
    assert win._ibkr_connected is True
    assert panel.add_button.isEnabled()
    assert panel.add_action.isEnabled()

    win._on_disconnected()
    qapp.processEvents()
    assert win._ibkr_connected is False
    assert not panel.add_button.isEnabled()
    assert not panel.add_action.isEnabled()


# ── D22-07-T02 / AC-D22.7.2 — restore clears then reproduces exactly ─────────

def test_D22_07_T02_restore_is_idempotent(window, qapp, monkeypatch):
    win, fresh, _settings = window
    fresh.set_watchlist(["AAPL", "TSLA"])

    events: list = []
    orig_clear = win.watchlist_panel.clear
    orig_add = win.watchlist_panel.add_symbol

    def spy_clear():
        events.append("clear")
        orig_clear()

    def spy_add(symbol, contract):
        events.append(("add", symbol))
        orig_add(symbol, contract)

    monkeypatch.setattr(win.watchlist_panel, "clear", spy_clear)
    monkeypatch.setattr(win.watchlist_panel, "add_symbol", spy_add)

    # First restore: clear ran first, then exactly the persisted set.
    win._restore_watchlist()
    assert _panel_symbols(win.watchlist_panel) == ["AAPL", "TSLA"]
    assert win.watchlist_panel.table.rowCount() == 2
    assert events[0] == "clear"
    assert [e for e in events if isinstance(e, tuple)] == [
        ("add", "AAPL"), ("add", "TSLA")
    ]

    # Second restore (a reconnect): cleared again, no duplicate rows.
    events.clear()
    win._restore_watchlist()
    assert _panel_symbols(win.watchlist_panel) == ["AAPL", "TSLA"]
    assert win.watchlist_panel.table.rowCount() == 2
    assert events[0] == "clear"
    assert [e for e in events if isinstance(e, tuple)] == [
        ("add", "AAPL"), ("add", "TSLA")
    ]


# ── D22-07-T03 / AC-D22.7.3 — seed-if-empty only when sentinel unset ─────────

def test_D22_07_T03_seed_guard(window, qapp):
    win, fresh, settings = window

    # Genuine first run: empty DB, sentinel unset.
    assert fresh.get_watchlist() == []
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is False

    win._restore_watchlist()
    qapp.processEvents()

    assert [sym for sym, _cat in fresh.get_watchlist()] == main_window.DEFAULT_WATCHLIST
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is True
    assert _panel_symbols(win.watchlist_panel) == main_window.DEFAULT_WATCHLIST

    # User explicitly emptied the list; sentinel stays set -> stay empty.
    fresh.set_watchlist([])
    win._restore_watchlist()
    qapp.processEvents()

    assert fresh.get_watchlist() == []
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is True
    assert win.watchlist_panel.table.rowCount() == 0


# ── D22-07-T04 / AC-D22.7.4 — lookup service wired + cancelled on disconnect ─

def test_D22_07_T04_lookup_service_lifecycle(window, qapp, monkeypatch):
    win, _fresh, _settings = window
    from services.contract_lookup_service import ContractLookupService

    service = win._contract_lookup
    assert isinstance(service, ContractLookupService)
    # Built from the window's market-data manager + the client bridge.
    assert service._md_manager is win.md_manager
    assert service._bridge is win.ib_client.bridge
    # Its lookup_finished signal is connected to the window's result slot.
    assert hasattr(win, "_on_contract_lookup_finished")
    assert service.receivers(service.lookup_finished) >= 1

    calls: list = []
    monkeypatch.setattr(service, "cancel_all", lambda: calls.append(True))
    win._on_disconnected()
    qapp.processEvents()
    assert calls == [True]


# ═════════════════════════════════════════════════════════════════════════════
# D22-08 — add/remove flow: gate, duplicate guard, live validation,
#          subscribe + persist (Phase 4)
# ═════════════════════════════════════════════════════════════════════════════


class FakeMdManager:
    """Deterministic contract-lookup + market-data double (no TWS, no reqIds)."""

    def __init__(self, first_id: int = 500):
        self._next = first_id
        self.contract_calls: list[tuple[int, object]] = []
        self.mkt_calls: list[tuple[int, object]] = []
        self.cancelled: list[int] = []

    def req_contract_details(self, contract):
        req_id = self._next
        self._next += 1
        self.contract_calls.append((req_id, contract))
        return req_id

    def req_mkt_data(self, contract):
        req_id = self._next
        self._next += 1
        self.mkt_calls.append((req_id, contract))
        return req_id

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


@pytest.fixture
def addflow(window):
    """A MainWindow wired to a FakeMdManager for the add/remove flow.

    Re-points the window, its watchlist panel and its ``ContractLookupService``
    at one fake so no real IBKR request is ever issued. The D22-07 ``window``
    fixture already isolates the DB and the non-injectable QSettings sentinel.
    """
    win, fresh, settings = window
    fake = FakeMdManager()
    win.md_manager = fake
    win.watchlist_panel.set_market_data_manager(fake)
    win._contract_lookup._md_manager = fake
    fresh.set_watchlist([])  # deterministic starting point (fixture never connects)
    yield win, fresh, settings, fake


# ── D22-08-T01 / AC-D22.8.1 — disconnected add is denied ─────────────────────

def test_D22_08_T01_disconnected_add_is_denied(addflow, qapp):
    win, fresh, _settings, fake = addflow

    assert win._ibkr_connected is False
    win._on_watchlist_symbol_add_requested("MSFT")
    qapp.processEvents()

    assert "not connected" in win.status_bar.currentMessage().lower()
    assert fake.contract_calls == []
    assert fake.mkt_calls == []
    assert win.watchlist_panel.table.rowCount() == 0
    assert fresh.get_watchlist() == []

    # Wiring: the panel's add intent is routed to the same handler.
    win.watchlist_panel.symbol_add_requested.emit("MSFT")
    qapp.processEvents()
    assert fake.contract_calls == []
    assert win.watchlist_panel.table.rowCount() == 0
    assert fresh.get_watchlist() == []


# ── D22-08-T02 / AC-D22.8.2 — case-insensitive duplicate is a no-op ──────────

def test_D22_08_T02_duplicate_add_is_noop(addflow, qapp):
    win, fresh, _settings, fake = addflow
    fresh.set_watchlist(["AAPL"])
    win._ibkr_connected = True
    win._restore_watchlist()
    qapp.processEvents()
    assert win.watchlist_panel.table.rowCount() == 1
    mkt_before = len(fake.mkt_calls)  # the restore's own AAPL subscription

    win._on_watchlist_symbol_add_requested("aapl")
    qapp.processEvents()

    assert "already" in win.status_bar.currentMessage().lower()
    assert fake.contract_calls == []
    # No duplicate row / subscription / DB change.
    assert win.watchlist_panel.table.rowCount() == 1
    assert len(fake.mkt_calls) == mkt_before
    assert fresh.get_watchlist() == [("AAPL", "EQUITIES")]


# ── D22-08-T03 / AC-D22.8.3 — resolved lookup adds + subscribes + persists ───

def test_D22_08_T03_successful_add_subscribes_and_persists(addflow, qapp):
    win, fresh, settings, fake = addflow
    win._ibkr_connected = True

    win._on_watchlist_symbol_add_requested("MSFT")
    assert len(fake.contract_calls) == 1
    req_id, contract = fake.contract_calls[0]
    assert contract.symbol == "MSFT"
    assert win._contract_lookup.is_pending(req_id)

    win._contract_lookup.lookup_finished.emit(req_id, "MSFT", True, "ok")
    qapp.processEvents()

    # Row added and subscribed through the panel (req_mkt_data issued).
    assert _panel_symbols(win.watchlist_panel) == ["MSFT"]
    assert win.watchlist_panel.table.rowCount() == 1
    assert len(fake.mkt_calls) == 1
    assert fake.mkt_calls[0][1].symbol == "MSFT"
    # Persisted + configured sentinel set + confirmation shown.
    assert fresh.get_watchlist() == [("MSFT", "EQUITIES")]
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is True
    assert "added" in win.status_bar.currentMessage().lower()
    # The window's own pending map is drained by the resolution.
    assert win._pending_watchlist_add == {}


# ── D22-08-T04 / AC-D22.8.4 — failure / disconnect adds nothing ──────────────

def test_D22_08_T04_failed_lookup_and_disconnect_add_nothing(addflow, qapp):
    win, fresh, settings, fake = addflow
    win._ibkr_connected = True

    # (a) lookup resolves ok=False (no contract / IBKR error / timeout).
    win._on_watchlist_symbol_add_requested("MSFT")
    req_id = fake.contract_calls[-1][0]
    win._contract_lookup.lookup_finished.emit(req_id, "MSFT", False, "no contract")
    qapp.processEvents()

    assert "could not add" in win.status_bar.currentMessage().lower()
    assert win.watchlist_panel.table.rowCount() == 0
    assert fake.mkt_calls == []
    assert fresh.get_watchlist() == []
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is False

    # (b) connection drops mid-flight before resolution.
    win._on_watchlist_symbol_add_requested("TSLA")
    pending_id = fake.contract_calls[-1][0]
    assert win._contract_lookup.is_pending(pending_id)
    win._on_disconnected()
    qapp.processEvents()

    assert "cancel" in win.status_bar.currentMessage().lower()
    assert win.watchlist_panel.table.rowCount() == 0
    assert fake.mkt_calls == []
    assert fresh.get_watchlist() == []

    # A late resolution for the dropped reqId must not add anything either.
    win._contract_lookup.lookup_finished.emit(pending_id, "TSLA", True, "ok")
    qapp.processEvents()
    assert win.watchlist_panel.table.rowCount() == 0
    assert fake.mkt_calls == []
    assert fresh.get_watchlist() == []


# ── D22-08-T05 / AC-D22.8.5 — remove cancels + drops + persists ──────────────

def test_D22_08_T05_remove_cancels_drops_persists(addflow, qapp):
    win, fresh, settings, fake = addflow
    fresh.set_watchlist(["AAPL"])
    win._ibkr_connected = True
    win._restore_watchlist()
    qapp.processEvents()
    aapl_req = fake.mkt_calls[-1][0]
    assert win.watchlist_panel.table.rowCount() == 1

    win._on_watchlist_symbol_remove_requested("AAPL")
    qapp.processEvents()

    assert fake.cancelled == [aapl_req]
    assert win.watchlist_panel.table.rowCount() == 0
    assert fresh.get_watchlist() == []
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is True
    assert "removed" in win.status_bar.currentMessage().lower()

    # Removal still succeeds while disconnected.
    win.watchlist_panel.add_symbol("TSLA", get_contract_for_symbol("TSLA"))
    fresh.add_watchlist_symbol("TSLA")
    win._on_disconnected()
    qapp.processEvents()
    tsla_req = fake.mkt_calls[-1][0]

    win._on_watchlist_symbol_remove_requested("TSLA")
    qapp.processEvents()

    assert win.watchlist_panel.table.rowCount() == 0
    assert tsla_req in fake.cancelled
    assert fresh.get_watchlist() == []
    assert "removed" in win.status_bar.currentMessage().lower()
    assert win._ibkr_connected is False


# ── D22-08-T06 / AC-D22.8.6 — restart round-trip + no re-seed ────────────────

def test_D22_08_T06_restart_round_trip(addflow, qapp):
    win, fresh, settings, fake = addflow
    fresh.set_watchlist(["AAPL"])
    settings.setValue(main_window.WATCHLIST_CONFIGURED_KEY, True)
    win._ibkr_connected = True
    win._restore_watchlist()
    qapp.processEvents()
    assert _panel_symbols(win.watchlist_panel) == ["AAPL"]

    # Add MSFT (resolved) then remove AAPL — all through the window.
    win._on_watchlist_symbol_add_requested("MSFT")
    req_id = fake.contract_calls[-1][0]
    win._contract_lookup.lookup_finished.emit(req_id, "MSFT", True, "ok")
    win._on_watchlist_symbol_remove_requested("AAPL")
    qapp.processEvents()

    # Read the persisted set back the way a restart does.
    win._restore_watchlist()
    qapp.processEvents()
    shown = _panel_symbols(win.watchlist_panel)
    assert "MSFT" in shown
    assert "AAPL" not in shown
    assert [s for s, _cat in fresh.get_watchlist()] == ["MSFT"]

    # Remove the last symbol, re-run the restore: stays empty (no re-seed).
    win._on_watchlist_symbol_remove_requested("MSFT")
    win._restore_watchlist()
    qapp.processEvents()
    assert win.watchlist_panel.table.rowCount() == 0
    assert fresh.get_watchlist() == []
    assert settings.value(
        main_window.WATCHLIST_CONFIGURED_KEY, False, type=bool
    ) is True


# ═════════════════════════════════════════════════════════════════════
# Q-45 — throttled add defers the subscription (no GUI-thread sleep),
#        with a removal guard on the deferred retry
# ═════════════════════════════════════════════════════════════════════


class _PacingFakeMdManager:
    """Market-data double raising PacingExceeded on demand (Q-41, no sleep)."""

    def __init__(self, throttle_first_n: int = 1, wait_s: float = 0.2):
        self._throttle_first_n = throttle_first_n
        self._wait_s = wait_s
        self._next = 900
        self.attempts = 0
        self.issued: list[int] = []
        self.cancelled: list[int] = []

    def req_mkt_data(self, contract):
        self.attempts += 1
        if self.attempts <= self._throttle_first_n:
            raise PacingExceeded(self._wait_s)
        req_id = self._next
        self._next += 1
        self.issued.append(req_id)
        return req_id

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


def _bare_panel(tmp_path, tag: str) -> WatchlistPanel:
    """A panel with isolated settings and no window (pacing-independent)."""
    settings = _isolated_settings(tmp_path / f"q45_{tag}.ini")
    return WatchlistPanel(settings=settings)


def test_Q45_throttled_add_row_present_then_subscribed(qapp, tmp_path):
    """Throttled add: row appears at once, subscription lands after the wait."""
    panel = _bare_panel(tmp_path, "defer")
    fake = _PacingFakeMdManager(throttle_first_n=1, wait_s=0.2)
    panel.set_market_data_manager(fake)
    try:
        panel.add_symbol("MSFT", object())
        # Row present immediately even though the subscribe was throttled.
        assert panel.table.rowCount() == 1
        assert _panel_symbols(panel) == ["MSFT"]
        assert fake.issued == []
        assert panel.active_row_count() == 0
        # The deferred singleShot retry (no sleep) subscribes once the wait
        # elapses.
        QTest.qWait(700)
        assert fake.attempts == 2
        assert fake.issued != []
        assert panel.active_row_count() == 1
    finally:
        panel.close()


def test_Q45_throttled_add_dropped_after_remove(qapp, tmp_path):
    """Throttled add + remove before the retry fires: no late subscription."""
    panel = _bare_panel(tmp_path, "drop")
    fake = _PacingFakeMdManager(throttle_first_n=1, wait_s=0.3)
    panel.set_market_data_manager(fake)
    try:
        panel.add_symbol("MSFT", object())
        assert panel.table.rowCount() == 1
        assert panel.remove_symbol("MSFT") is True
        assert panel.table.rowCount() == 0
        # The deferred retry fires while the row is gone: it must drop the
        # retry (no re-issue), so the chain ends with nothing subscribed.
        QTest.qWait(800)
        assert fake.attempts == 1
        assert fake.issued == []
        assert panel.active_row_count() == 0
        assert panel.table.rowCount() == 0
    finally:
        panel.close()
