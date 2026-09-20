from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QBrush

# Column indices
COL_SYMBOL = 0
COL_LAST   = 1
COL_BID    = 2
COL_ASK    = 3
COL_CHG    = 4
COL_CHGPCT = 5
COL_VOL    = 6

HEADERS = ["Symbol", "Last", "Bid", "Ask", "Chg", "Chg %", "Vol"]

# IBKR tick types
TICK_LAST  = 4
TICK_BID   = 1
TICK_ASK   = 2
TICK_CLOSE = 9   # Previous day's close

GREEN = QColor('#34d399')  # emerald-400
RED   = QColor('#f87171')  # red-400
DIM   = QColor('#a3a3a3')  # neutral-400

# ── Watchlist width limits (D13) ───────────────────────────────────────────────
WATCHLIST_MIN_WIDTH = 150
CHART_MIN_WIDTH = 400
DEFAULT_WATCHLIST_WIDTH = 220
WATCHLIST_WIDTH_KEY = "watchlist/width"


def watchlist_max_width(window_width: int) -> int:
    """Maximum docked watchlist width: ~50% of the window, but the chart keeps
    at least CHART_MIN_WIDTH px, and the watchlist never exceeds the window."""
    half = int(window_width * 0.50)
    return max(WATCHLIST_MIN_WIDTH, min(half, window_width - CHART_MIN_WIDTH))


def clamp_watchlist_width(width: int, window_width: int) -> int:
    """Clamp a requested watchlist width into [min, max] for the window size."""
    return max(WATCHLIST_MIN_WIDTH, min(int(width), watchlist_max_width(window_width)))


def load_watchlist_width(settings: QSettings, window_width: int) -> int:
    """Return the persisted watchlist width, clamped for the current window."""
    try:
        raw = settings.value(WATCHLIST_WIDTH_KEY)
        width = int(raw) if raw is not None else DEFAULT_WATCHLIST_WIDTH
    except (TypeError, ValueError):
        width = DEFAULT_WATCHLIST_WIDTH
    return clamp_watchlist_width(width, window_width)


def save_watchlist_width(settings: QSettings, width: int, window_width: int) -> int:
    """Persist the (clamped) watchlist width and return it."""
    clamped = clamp_watchlist_width(width, window_width)
    settings.setValue(WATCHLIST_WIDTH_KEY, clamped)
    return clamped


def should_load_on_double_click(current_symbol: str, requested_symbol: str,
                                connected: bool) -> str:
    """D14 decision helper.

    Returns one of:
      "load"               — a different symbol while connected
      "noop_same"          — the requested symbol already matches the chart
      "noop_disconnected"  — IBKR is not connected
      "noop_empty"         — nothing meaningful was double-clicked
    """
    clean = (requested_symbol or "").strip().upper()
    if not clean:
        return "noop_empty"
    current = (current_symbol or "").strip().upper()
    if clean == current:
        return "noop_same"
    if not connected:
        return "noop_disconnected"
    return "load"


class WatchlistPanel(QWidget):
    """
    Dense watchlist table. Each row subscribes to IBKR reqMktData.
    Cells flash green/red on tick updates using a QTimer fade.
    """

    row_double_clicked = pyqtSignal(str)  # symbol (D14)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._req_to_row: dict[int, int] = {}   # reqId → row index
        self._prev_close: dict[int, float] = {}  # reqId → prev close
        self._last_price: dict[int, float] = {}  # reqId → last price
        self._flash_timers: dict[int, QTimer] = {}
        self._md_manager = None  # injected after connection

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header strip
        header_bar = QWidget()
        header_bar.setFixedHeight(28)
        header_bar.setStyleSheet("background: #141822; border-bottom: 1px solid #232938;")
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(8, 0, 8, 0)
        h_layout.addWidget(QLabel("Watchlist"))
        h_layout.addStretch()
        layout.addWidget(header_bar)

        # Table
        self.table = QTableWidget(0, len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(COL_SYMBOL, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(COL_SYMBOL, 70)
        for col in range(1, len(HEADERS)):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { font-size: 11px; }
            QTableWidget::item { padding: 2px 4px; }
        """)
        layout.addWidget(self.table)

        # D14: double-click anywhere on a row requests the chart load
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    # ── Public API ─────────────────────────────────────────────────────────────

    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        item = self.table.item(row, COL_SYMBOL)
        if item is None:
            return
        symbol = (item.text() or "").strip()
        if symbol and symbol != "—":
            self.row_double_clicked.emit(symbol)

    def set_depth_manager(self, depth_manager):
        """Inject MarketDepthManager for position mapping."""
        self._depth_manager = depth_manager

    def set_market_data_manager(self, md_manager):
        """Inject MarketDataManager for live tick subscriptions."""
        self._md_manager = md_manager

    # ── MarketDepth management ───────────────────────────────────────────────────

    def on_depth_update(self, req_id: int, position: int, operation: int,
                        side: int, price: float, size: int) -> None:
        """Handle incoming depth updates from the bridge."""
        if self._depth_manager:
            self._depth_manager.on_update(req_id, position, operation, side, price, size)

    def add_symbol(self, symbol: str, contract):
        """Add a new row and subscribe to live ticks."""
        if not self._md_manager:
            return
        row = self.table.rowCount()
        self.table.insertRow(row)

        for col in range(len(HEADERS)):
            item = QTableWidgetItem("—")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)
        self.table.item(row, COL_SYMBOL).setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.item(row, COL_SYMBOL).setText(symbol)

        req_id = self._md_manager.req_mkt_data(contract)
        self._req_to_row[req_id] = row

    def clear(self):
        """Cancel all active market-data subscriptions and empty the table."""
        if self._md_manager:
            for req_id in list(self._req_to_row.keys()):
                self._md_manager.cancel_mkt_data(req_id)
        self._req_to_row.clear()
        self._prev_close.clear()
        self._last_price.clear()
        for timer in self._flash_timers.values():
            timer.stop()
        self._flash_timers.clear()
        self.table.setRowCount(0)

    # ── Tick handler — called from bridge signal (main thread) ─────────────────

    def on_tick_price(self, req_id: int, tick_type: int, price: float):
        row = self._req_to_row.get(req_id)
        if row is None or price <= 0:
            return

        if tick_type == TICK_CLOSE:
            self._prev_close[req_id] = price
            return

        col = None
        if tick_type == TICK_LAST:
            col = COL_LAST
            old = self._last_price.get(req_id)
            self._last_price[req_id] = price
            # Compute change
            prev = self._prev_close.get(req_id)
            if prev and prev > 0:
                chg = price - prev
                chg_pct = (chg / prev) * 100
                self._set_cell(row, COL_CHG, f"{chg:+.2f}")
                self._set_cell(row, COL_CHGPCT, f"{chg_pct:+.2f}%")
                color = GREEN if chg >= 0 else RED
                self.table.item(row, COL_CHG).setForeground(QBrush(color))
                self.table.item(row, COL_CHGPCT).setForeground(QBrush(color))
            # Flash the last column
            if old is not None:
                self._flash(row, col, GREEN if price >= old else RED)
        elif tick_type == TICK_BID:
            col = COL_BID
        elif tick_type == TICK_ASK:
            col = COL_ASK

        if col is not None:
            self._set_cell(row, col, f"{price:.2f}")

    def on_tick_size(self, req_id: int, tick_type: int, size: int):
        row = self._req_to_row.get(req_id)
        if row is None:
            return
        # tick_type 8 = volume
        if tick_type == 8:
            self._set_cell(row, COL_VOL, f"{size:,}")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _set_cell(self, row: int, col: int, text: str):
        item = self.table.item(row, col)
        if item:
            item.setText(text)

    def _flash(self, row: int, col: int, color: QColor):
        """Briefly highlight a cell then fade back to default."""
        item = self.table.item(row, col)
        if not item:
            return
        item.setBackground(QBrush(color))
        key = row * 10 + col
        if key in self._flash_timers:
            self._flash_timers[key].stop()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: item.setBackground(QBrush(QColor('#101218'))))
        timer.start(400)  # flash for 400 ms
        self._flash_timers[key] = timer
