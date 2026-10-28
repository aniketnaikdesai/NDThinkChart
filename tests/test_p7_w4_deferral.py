"""P7-T08 (P7-W4): watchlist reqMktData deferral under throttle + Q-41 gate.

T11 (integration): add a watchlist symbol while the mkt-data throttle is
exhausted; the row must persist through the deferral and exactly one deferred
subscription must issue for the reported wait — never a GUI-thread sleep.

T12 (unit): cross-path Q-41 assertion over the wave-continuation, prime-retry
and watchlist-deferral call sites — every PacingExceeded handler defers
(singleShot or the wave-continuation timer re-armed for the reported wait) and
no pacing path blocks — plus one live throttled drive per path.

T13 (manual, not in this file): full offscreen suite green, order-absence /
bars-schema / LWC-seam invariants, read-only live provenance on record.

Offscreen only. No live TWS connection. No order code touched.
"""

import ast
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QSettings, QTimer
from PyQt6.QtWidgets import QApplication

from ibkr.pacing import PacingExceeded
from ui.watchlist_panel import WatchlistPanel

REPO_ROOT = Path(__file__).resolve().parents[1]

APP = QApplication.instance() or QApplication([])


# ── fakes ────────────────────────────────────────────────────────────────────

class FakeMarketDataManager:
    """req_mkt_data raises PacingExceeded ``fail_times`` times, then issues."""

    def __init__(self, fail_times: int = 1, wait_seconds: float = 2.5):
        self.fail_times = fail_times
        self.wait_seconds = wait_seconds
        self.calls = 0
        self.issued: list[int] = []
        self.cancelled: list[int] = []
        self._next_req_id = 1000

    def req_mkt_data(self, contract, generic_ticks: str = "") -> int:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise PacingExceeded(self.wait_seconds)
        self._next_req_id += 1
        self.issued.append(self._next_req_id)
        return self._next_req_id

    def cancel_mkt_data(self, req_id) -> None:
        self.cancelled.append(req_id)


class SingleShotTrap:
    """Capture QTimer.singleShot schedules; fire them on demand (no waiting)."""

    def __init__(self, monkeypatch):
        self.scheduled: list[tuple[int, object]] = []
        monkeypatch.setattr(QTimer, "singleShot", self._capture)

    def _capture(self, ms: int, func) -> None:
        self.scheduled.append((int(ms), func))

    def fire_all(self) -> None:
        while self.scheduled:
            self.fire_one()

    def fire_one(self) -> None:
        _, func = self.scheduled.pop(0)
        func()


def _panel(tmp_path, md_manager) -> WatchlistPanel:
    ini = str(tmp_path / "watchlist.ini")
    panel = WatchlistPanel(
        settings=QSettings(ini, QSettings.Format.IniFormat)
    )
    panel.set_market_data_manager(md_manager)
    return panel


# ── T11: watchlist add defers under throttle ─────────────────────────────────

def test_t11_watchlist_add_defers_under_throttle(tmp_path, monkeypatch):
    """Throttled add: row persists, one deferred sub issues for the wait."""
    trap = SingleShotTrap(monkeypatch)
    md = FakeMarketDataManager(fail_times=1, wait_seconds=2.5)
    panel = _panel(tmp_path, md)
    contract = object()

    panel.add_symbol("AAPL", contract)

    # Row present immediately, nothing issued, nothing slept.
    assert panel._row_index_for_symbol("AAPL") == 0
    assert panel.table.rowCount() == 1
    assert md.calls == 1
    assert md.issued == []
    assert len(trap.scheduled) == 1
    ms, _callback = trap.scheduled[0]
    assert ms == int(2.5 * 1000)

    # Fire the deferred retry: the subscription follows, the row survives.
    trap.fire_all()
    assert md.calls == 2
    assert md.issued == [1001]
    assert panel._row_index_for_symbol("AAPL") == 0
    assert panel.table.rowCount() == 1
    assert panel._req_to_row == {1001: 0}
    assert trap.scheduled == []  # no further deferral once issued


def test_t11_watchlist_add_redefers_while_still_throttled(tmp_path, monkeypatch):
    """Still throttled at retry time: re-defers for the new reported wait."""
    trap = SingleShotTrap(monkeypatch)
    md = FakeMarketDataManager(fail_times=2, wait_seconds=1.0)
    panel = _panel(tmp_path, md)
    contract = object()

    panel.add_symbol("aapl", contract)  # lower-case: normalises to the row
    assert panel._row_index_for_symbol("AAPL") == 0
    assert [ms for ms, _ in trap.scheduled] == [1000]

    trap.fire_one()  # first retry still throttled -> re-defer, row kept
    assert md.calls == 2
    assert md.issued == []
    assert panel._row_index_for_symbol("AAPL") == 0
    assert [ms for ms, _ in trap.scheduled] == [1000]

    trap.fire_one()  # second retry issues
    assert md.issued == [1001]
    assert panel._req_to_row == {1001: 0}


def test_t11_deferred_retry_dropped_after_remove(tmp_path, monkeypatch):
    """Row removed while deferred: the pending retry is a no-op, never lost."""
    trap = SingleShotTrap(monkeypatch)
    md = FakeMarketDataManager(fail_times=5, wait_seconds=2.5)
    panel = _panel(tmp_path, md)
    contract = object()

    panel.add_symbol("MSFT", contract)
    assert panel._row_index_for_symbol("MSFT") == 0
    assert panel.remove_symbol("MSFT") is True
    assert panel._row_index_for_symbol("MSFT") is None

    trap.fire_all()  # stale retry must not subscribe (nor resurrect the row)
    assert md.issued == []
    assert panel._row_index_for_symbol("MSFT") is None
    assert panel.table.rowCount() == 0


# ── T12: Q-41 cross-path contract ────────────────────────────────────────────

_PACING_PATH_FILES = [
    "ui/watchlist_panel.py",
    "ui/ticker_session.py",
    "ui/main_window.py",
    "ibkr/market_data.py",
]

_BLOCKING_TOKENS = ("time.sleep", "msleep", "QThread.sleep", "QEventLoop")


def _pacing_functions(path: Path):
    """Yield (node, source) for functions that touch the pacing contract."""
    src = path.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            seg = ast.get_source_segment(src, node) or ""
            if "PacingExceeded" in seg or "pacing" in node.name.lower():
                yield node, seg


def _except_pacing_handlers(seg_src: str, path: Path, func_name: str):
    tree = ast.parse(seg_src)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            text = ast.get_source_segment(seg_src, node) or ""
            if "PacingExceeded" in text:
                found.append(text)
    return found


def test_t12_q41_source_scan_defers_never_sleeps():
    """Every PacingExceeded handler defers; no pacing path blocks."""
    handler_sites: list[str] = []
    for rel in _PACING_PATH_FILES:
        path = REPO_ROOT / rel
        assert path.exists(), f"scan target missing: {rel}"
        for node, seg in _pacing_functions(path):
            for token in _BLOCKING_TOKENS:
                assert token not in seg, (
                    f"{rel}:{node.name} uses blocking primitive {token!r}"
                )
            for handler in _except_pacing_handlers(seg, path, node.name):
                assert ("singleShot" in handler
                        or "_schedule_wave_continuation" in handler), (
                    f"{rel}:{node.name} handles PacingExceeded without "
                    f"deferring"
                )
                assert "wait_seconds" in handler or "wait" in handler, (
                    f"{rel}:{node.name} defers without the reported wait"
                )
                handler_sites.append(f"{rel}:{node.name}")
    # All three pacing paths (wave, prime, watchlist/live-feed) represented.
    assert any(s.startswith("ui/watchlist_panel.py") for s in handler_sites)
    assert any(s.startswith("ui/ticker_session.py") for s in handler_sites)
    assert any(s.startswith("ui/main_window.py") for s in handler_sites)
    assert len(handler_sites) >= 6, handler_sites


def test_t12_drive_watchlist_throttled_add(tmp_path, monkeypatch):
    """Live drive 1/3 — watchlist path (real panel, throttled transport)."""
    trap = SingleShotTrap(monkeypatch)
    md = FakeMarketDataManager(fail_times=1, wait_seconds=2.0)
    panel = _panel(tmp_path, md)
    panel.add_symbol("NVDA", object())
    assert panel._row_index_for_symbol("NVDA") == 0
    assert [ms for ms, _ in trap.scheduled] == [2000]
    trap.fire_all()
    assert md.issued == [1001]
    assert panel._req_to_row == {1001: 0}


def test_t12_drive_live_feed_attach_throttled(monkeypatch, tmp_path):
    """Live drive 2/3 — MainWindow live-feed attach defers, retry re-drives."""
    os.environ.setdefault("DB_PATH", str(tmp_path / "t12_drive.sqlite"))
    from ui.main_window import MainWindow  # noqa: PLC0415 (needs DB_PATH)

    trap = SingleShotTrap(monkeypatch)
    shown: list[str] = []
    stopped: list[bool] = []
    badged: list[bool] = []

    class _Session:
        def ensure_rt_subscribed(self):
            raise PacingExceeded(3.0)

    stub = SimpleNamespace(
        _current_symbol="AAPL",
        get_or_create_session=lambda symbol: _Session(),
        status_bar=SimpleNamespace(
            showMessage=lambda msg, timeout=None: shown.append(msg)),
        _rt_retry_timer=SimpleNamespace(stop=lambda: stopped.append(True)),
        _update_stream_badge=lambda: badged.append(True),
    )
    contract = object()
    MainWindow._attach_live_feed(stub, "AAPL", contract)

    assert [ms for ms, _ in trap.scheduled] == [3000]
    assert any("etrying" in m for m in shown)
    assert badged == []  # no live badge while pacing-limited

    # The deferred retry re-enters the attach for the still-current symbol.
    reentered: list[tuple] = []
    retry_stub = SimpleNamespace(
        _current_symbol="AAPL",
        _attach_live_feed=lambda s, c: reentered.append((s, c)),
    )
    _, callback = trap.scheduled[0]
    # Fire through the real retry entry point (not the raw closure).
    MainWindow._retry_attach_live_feed(retry_stub, "AAPL", contract)
    assert reentered == [("AAPL", contract)]

    # User moved on meanwhile: the retry is a no-op.
    retry_stub._current_symbol = "MSFT"
    MainWindow._retry_attach_live_feed(retry_stub, "AAPL", contract)
    assert reentered == [("AAPL", contract)]


def test_t12_drive_wave_continuation_and_prime_retry(tmp_path):
    """Live drive 3/3 — session wave + prime deferred paths (real methods)."""
    os.environ.setdefault("DB_PATH", str(tmp_path / "t12_drive2.sqlite"))
    from ui.ticker_session import TickerSession  # noqa: PLC0415 (needs DB_PATH)

    # Wave continuation: the reported wait reaches the timer + watchdog.
    started: list[int] = []
    armed: list[float] = []
    status: list[str] = []
    wave_stub = SimpleNamespace(
        symbol="SPY",
        _wave_continue_wait_s=None,
        _continuation_delay_ms=lambda w: int(w * 1000) + 50,
        _format_wait=lambda w: f"{w:.0f}s",
        _status=lambda msg: status.append(msg),
        _arm_history_wave_watchdog=lambda w: armed.append(w),
        _wave_continue_timer=SimpleNamespace(
            start=lambda ms: started.append(ms)),
    )
    TickerSession._schedule_wave_continuation(wave_stub, 2.5)
    assert wave_stub._wave_continue_wait_s == 2.5
    assert started == [2550]
    assert armed == [2.5]
    assert any("pacing-limited" in m for m in status)

    # Prime retry: single deferred re-entry with retrying=True, then fail-open.
    contract = object()
    entered: list[tuple] = []
    failed_open: list[str] = []

    def _prime(c, timeframe, now_ts, ext, retrying=False):
        entered.append((timeframe, retrying))
        return False  # retry also pacing-limited -> fail open

    prime_stub = SimpleNamespace(
        _prime_retry_pending=True,
        _prime_retry_args=(contract, "5 mins", False),
        prime_aggregator=_prime,
        _fail_open_prime=lambda tf: failed_open.append(tf),
    )
    TickerSession._on_prime_retry(prime_stub)
    assert entered and entered[0][1] is True  # explicit retrying=True
    assert failed_open == ["5 mins"]  # fail-open when the retry can't issue
    assert prime_stub._prime_retry_pending is False

    # Stale retry (superseded/cleared): no-op, never reschedules.
    entered.clear()
    failed_open.clear()
    prime_stub._prime_retry_pending = False
    TickerSession._on_prime_retry(prime_stub)
    assert entered == [] and failed_open == []
