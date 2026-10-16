"""D21.5 / ESC-034 — watchlist flash-timer lifetime across a column-layout rebuild.

Covers AC-D21.5.4.  ``_flash`` starts a 400 ms single-shot ``QTimer`` to fade a
cell back to the default background.  A column-layout rebuild
(``_rebuild_table`` via ``_apply_columns`` / ``_on_field_toggled`` /
``_move_field``) replaces *every* cell item without touching ``_flash_timers``,
so a timer that captured the old item fires against a freed C++ object:

    RuntimeError: wrapped C/C++ object of type QTableWidgetItem has been deleted

The fix resolves the cell lazily at fire time (``_unflash(row, key)`` looks up
the *current* item) rather than swallowing the error — see the ESC-034 note.

All tests run offscreen (``tests/conftest.py`` sets ``QT_QPA_PLATFORM=offscreen``).
"""

import inspect
import os
import sys

from PyQt6.QtCore import QEventLoop, QSettings, QTimer

import ui.watchlist_panel as watchlist_panel
from ui.watchlist_panel import GREEN, WatchlistPanel

DEFAULT_BG = "#101218"


class FakeMdManager:
    """Minimal MarketDataManager double: hands out unique reqIds."""

    def __init__(self):
        self._next = 1
        self.cancelled = []

    def req_mkt_data(self, contract):
        req_id = self._next
        self._next += 1
        return req_id

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


def _isolated_settings(path) -> QSettings:
    try:
        os.remove(path)
    except OSError:
        pass
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    settings.clear()
    settings.sync()
    return settings


def _panel(tmp_path, name) -> WatchlistPanel:
    p = WatchlistPanel(settings=_isolated_settings(tmp_path / name))
    p.set_market_data_manager(FakeMdManager())
    return p


def _spin(qapp, ms: int) -> None:
    """Process the event loop for ``ms`` real milliseconds."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def _bg(panel, row: int, key: str) -> str:
    item = panel._item(row, key)
    assert item is not None, f"no cell item at ({row}, {key!r})"
    return item.background().color().name()


def _flash_through(panel, qapp, trigger) -> None:
    """Flash row 0/'last', replace its item via ``trigger``, then let the
    pending reset fire; assert it neither raises nor touches a deleted item.
    """
    panel._flash(0, "last", GREEN)
    assert _bg(panel, 0, "last") == GREEN.name(), "flash did not highlight"

    trigger()
    # The rebuild does not touch _flash_timers: the timer is still pending.
    assert (0, "last") in panel._flash_timers

    # pyqtgraph's non-abort excepthook prints and SWALLOWS a slot exception, so
    # assert observable state via a temporary recording hook (ESC-034 note).
    recorded = []
    prev_hook = sys.excepthook

    def _record(exc_type, exc, tb):
        recorded.append((exc_type, exc))

    sys.excepthook = _record
    try:
        _spin(qapp, 600)  # past the 400 ms flash window
    finally:
        sys.excepthook = prev_hook

    assert recorded == [], recorded
    # The reset landed on the CURRENT (rebuilt) cell.
    assert _bg(panel, 0, "last") == DEFAULT_BG


# ── P2-T29-T11 / AC1 — the reset survives an item replacement ─────────────────

def test_p2_t29_t11_flash_reset_survives_item_replacement(tmp_path, qapp):
    panel = _panel(tmp_path, "d21_flash_t11.ini")
    try:
        panel.add_symbol("AAPL", object())
        assert panel._item(0, "last") is not None

        # A full column-layout rebuild replaces every cell item.
        _flash_through(panel, qapp, panel._apply_columns)
        # A reorder (also routed through _apply_columns -> _rebuild_table).
        _flash_through(panel, qapp, lambda: panel._move_field("last", -1))
    finally:
        panel.close()


# ── P2-T29-T21 / AC2 — lazy resolution, not a mask ───────────────────────────

def test_p2_t29_t21_flash_reset_is_lazy_and_unmasked():
    # The reset resolves the cell at fire time via _unflash, not by closing
    # over the item (which a rebuild may have deleted).
    assert hasattr(WatchlistPanel, "_unflash"), (
        "the flash reset must resolve the cell lazily at fire time (_unflash)"
    )
    flash_src = inspect.getsource(WatchlistPanel._flash)
    unflash_src = inspect.getsource(WatchlistPanel._unflash)

    # Lazy resolution: the reset looks up the CURRENT item by (row, key)...
    assert "self._item(row, key)" in unflash_src
    assert "setBackground" in unflash_src
    # ...and the timeout is wired to that lazy reset, not to a captured item.
    assert "_unflash" in flash_src
    assert "lambda: item.setBackground" not in flash_src

    # No exception-swallowing shim: no shiboken6.isValid, no try/except around
    # the flash callback — the reset must not depend on catching a deleted
    # object error.
    assert "shiboken6" not in inspect.getsource(watchlist_panel)
    combined = flash_src + "\n" + unflash_src
    assert "except RuntimeError" not in combined
    assert "except Exception" not in combined


# ── P2-T29-T31 / AC3 — the already-safe paths stay safe ──────────────────────

def test_p2_t29_t31_remove_clear_and_uninterrupted_flash(tmp_path, qapp):
    # ── remove_symbol (first / middle / last row): _flash_timers stays exact ──
    for name, idx in (("first", 0), ("middle", 1), ("last", 2)):
        symbols = ("AAPL", "MSFT", "TSLA")
        panel = _panel(tmp_path, f"d21_flash_t31_{name}.ini")
        try:
            for symbol in symbols:
                panel.add_symbol(symbol, object())

            timers = {}
            for row in range(len(symbols)):
                timer = QTimer(panel)
                timer.setSingleShot(True)
                timer.start(10_000)  # long-lived: must be stopped on removal
                timers[row] = timer
            panel._flash_timers = {(r, "last"): t for r, t in timers.items()}

            assert panel.remove_symbol(symbols[idx]) is True

            remaining = len(symbols) - 1
            # Keys are exactly the live (row, key) set — no stale key survives.
            assert set(panel._flash_timers.keys()) == \
                {(r, "last") for r in range(remaining)}
            assert timers[idx] not in panel._flash_timers.values()
            assert not timers[idx].isActive(), "removed row's timer not stopped"
        finally:
            panel.close()

    # ── clear(): stops every timer and empties the registry ──
    panel = _panel(tmp_path, "d21_flash_t31_clear.ini")
    try:
        panel.add_symbol("AAPL", object())
        panel.add_symbol("MSFT", object())
        timers = {}
        for row in range(2):
            timer = QTimer(panel)
            timer.start(10_000)
            timers[row] = timer
        panel._flash_timers = {(r, "last"): t for r, t in timers.items()}

        panel.clear()

        assert panel._flash_timers == {}
        assert all(not t.isActive() for t in timers.values())
        assert panel.table.rowCount() == 0
    finally:
        panel.close()

    # ── an uninterrupted flash still resets its cell after ~400 ms ──
    panel = _panel(tmp_path, "d21_flash_t31_uninterrupted.ini")
    try:
        panel.add_symbol("AAPL", object())
        panel._flash(0, "last", GREEN)
        assert _bg(panel, 0, "last") == GREEN.name()
        _spin(qapp, 600)
        assert _bg(panel, 0, "last") == DEFAULT_BG
    finally:
        panel.close()
