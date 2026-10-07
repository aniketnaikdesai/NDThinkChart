from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHeaderView, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QBrush, QPalette

import ui.dock_layout as dock_layout
from ui.visual_conventions import DiagonalStrikeButton

# ── D21.5: field-key column model ─────────────────────────────────────────────
# The table is no longer addressed by fixed column indices. ``COLUMN_DEFS`` maps
# a stable field *key* to its header label and an ``extractor`` that renders a
# raw value into display text. ``_active_fields`` (an ordered list of keys) is
# the live layout; every write resolves a key -> column index through it, so a
# reorder/remove can never land a value in the wrong column (DG32).


def _fmt_symbol(value) -> str:
    if value is None:
        return "—"
    text = str(value).strip()
    return text if text else "—"


def _fmt_price(value) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_signed(value) -> str:
    try:
        return f"{float(value):+.2f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_signed_pct(value) -> str:
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_volume(value) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


COLUMN_DEFS = {
    "symbol": {"header": "Symbol", "extractor": _fmt_symbol},
    "last":   {"header": "Last",   "extractor": _fmt_price},
    "bid":    {"header": "Bid",    "extractor": _fmt_price},
    "ask":    {"header": "Ask",    "extractor": _fmt_price},
    "chg":    {"header": "Chg",    "extractor": _fmt_signed},
    "chgpct": {"header": "Chg %",  "extractor": _fmt_signed_pct},
    "vol":    {"header": "Vol",    "extractor": _fmt_volume},
}

#: Canonical field order; the addable set is exactly these existing 7 fields.
ALL_FIELDS = list(COLUMN_DEFS.keys())
#: The Symbol column can never be removed (AC-D21.5.3).
SYMBOL_FIELD = "symbol"
#: Layout used when nothing valid is persisted.
DEFAULT_FIELDS = list(ALL_FIELDS)
#: Backward-compatible header labels in canonical order (default layout).
HEADERS = [COLUMN_DEFS[k]["header"] for k in ALL_FIELDS]

#: QSettings key holding the ordered, comma-joined active field keys (D21.5).
WATCHLIST_COLUMNS_KEY = "watchlist/columns"

# IBKR tick types
TICK_LAST  = 4
TICK_BID   = 1
TICK_ASK   = 2
TICK_CLOSE = 9   # Previous day's close

GREEN = QColor('#34d399')  # emerald-400
RED   = QColor('#f87171')  # red-400
DIM   = QColor('#a3a3a3')  # neutral-400

# ── Watchlist width limits (D13) ───────────────────────────────────────────────
# Constants are kept in agreement with the pure ``ui.dock_layout`` model, which
# is the single source of truth for the width caps (D17 Phase 1). The cap
# formula is NOT duplicated here any more — the helpers below delegate to it.
WATCHLIST_MIN_WIDTH = dock_layout.WATCHLIST_MIN_WIDTH
CHART_MIN_WIDTH = dock_layout.CHART_MIN_WIDTH
DEFAULT_WATCHLIST_WIDTH = dock_layout.DEFAULT_WATCHLIST_WIDTH
WATCHLIST_WIDTH_KEY = "watchlist/width"


def watchlist_max_width(chart_area_w: int) -> int:
    """Maximum docked watchlist width for a given **chart-area** width (D17/B1).

    Delegates the cap formula to :func:`ui.dock_layout.watchlist_max_width`, the
    single source of truth: ~50% of the chart area, but the chart keeps at least
    ``CHART_MIN_WIDTH`` px and the watchlist never drops below
    ``WATCHLIST_MIN_WIDTH``. The one-argument signature shape is preserved.
    """
    return dock_layout.watchlist_max_width(chart_area_w)


def clamp_watchlist_width(width: int, chart_area_w: int) -> int:
    """Clamp a requested watchlist width into [min, max] for the chart area."""
    return max(WATCHLIST_MIN_WIDTH,
               min(int(width), dock_layout.watchlist_max_width(chart_area_w)))


def load_watchlist_width(settings: QSettings, chart_area_w: int) -> int:
    """Return the persisted watchlist width, clamped for the chart area."""
    try:
        raw = settings.value(WATCHLIST_WIDTH_KEY)
        width = int(raw) if raw is not None else DEFAULT_WATCHLIST_WIDTH
    except (TypeError, ValueError):
        width = DEFAULT_WATCHLIST_WIDTH
    return clamp_watchlist_width(width, chart_area_w)


def save_watchlist_width(settings: QSettings, width: int, chart_area_w: int) -> int:
    """Persist the (clamped) watchlist width and return it."""
    clamped = clamp_watchlist_width(width, chart_area_w)
    settings.setValue(WATCHLIST_WIDTH_KEY, clamped)
    return clamped


# ── D21.5: column layout persistence + sanitised restore ──────────────────────

def ensure_symbol_present(fields) -> list[str]:
    """Return a de-duplicated, known-only field list with Symbol guaranteed.

    Unknown keys are dropped. Symbol is inserted at the front when missing so
    it always remains in the layout (AC-D21.5.3).
    """
    ordered: list[str] = []
    for key in fields or []:
        if key in COLUMN_DEFS and key not in ordered:
            ordered.append(key)
    if SYMBOL_FIELD not in ordered:
        ordered.insert(0, SYMBOL_FIELD)
    return ordered


def sanitise_watchlist_columns(raw) -> list[str]:
    """Normalise a persisted value into an ordered, valid field list.

    Accepts a comma-joined string (the stored form) or a sequence. Unknown
    keys are dropped, duplicates removed, Symbol forced present. A missing /
    empty / unusable value falls back to the full default layout.
    """
    if raw is None:
        return list(DEFAULT_FIELDS)
    if isinstance(raw, str):
        if not raw.strip():
            return list(DEFAULT_FIELDS)
        parts = [p.strip() for p in raw.split(",")]
    elif isinstance(raw, (list, tuple)):
        parts = [str(p).strip() for p in raw]
    else:
        return list(DEFAULT_FIELDS)

    ordered: list[str] = []
    for key in parts:
        if key in COLUMN_DEFS and key not in ordered:
            ordered.append(key)
    if not ordered:
        return list(DEFAULT_FIELDS)
    if SYMBOL_FIELD not in ordered:
        ordered.insert(0, SYMBOL_FIELD)
    return ordered


def load_watchlist_columns(settings: QSettings) -> list[str]:
    """Return the persisted active-field layout, sanitised for this build."""
    try:
        raw = settings.value(WATCHLIST_COLUMNS_KEY)
    except Exception:  # noqa: BLE001 — corrupt settings must never crash launch
        return list(DEFAULT_FIELDS)
    return sanitise_watchlist_columns(raw)


def save_watchlist_columns(settings: QSettings, fields) -> list[str]:
    """Persist the ordered active-field layout; return the sanitised list."""
    ordered = ensure_symbol_present(fields)
    settings.setValue(WATCHLIST_COLUMNS_KEY, ",".join(ordered))
    return ordered


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

    Columns are configurable (D21.5): a right-click on the header offers
    add/remove/rearrange, and the layout is persisted to QSettings.
    """

    row_double_clicked = pyqtSignal(str)  # symbol (D14)

    def __init__(self, parent=None, settings: QSettings | None = None):
        super().__init__(parent)
        self._settings = (settings if settings is not None
                          else QSettings("NDThinkChart", "NDThinkChart"))
        # Ordered active field keys — the live column layout (D21.5).
        self._active_fields = load_watchlist_columns(self._settings)
        self._req_to_row: dict[int, int] = {}   # reqId → row index
        self._prev_close: dict[int, float] = {}  # reqId → prev close
        self._last_price: dict[int, float] = {}  # reqId → last price
        self._flash_timers: dict[tuple, QTimer] = {}
        # row index → {field key: raw value} so a rebuild can re-render every
        # cell through the correct extractor (field-identity binding, DG32).
        self._row_data: dict[int, dict] = {}
        self._md_manager = None  # injected after connection
        self._depth_manager = None  # injected after connection
        # D21.11: body (table) collapse state driven by the header button.
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header strip — the single "Watchlist" label (D21.11) ──────────────
        # ``MainWindow`` promotes this strip to the dock's title-bar widget via
        # ``setTitleBarWidget`` and deletes the duplicate ``QDockWidget`` title.
        # The label is a ``DiagonalStrikeButton``: clicking it collapses the
        # watchlist body (the table) while this header/button stays visible and
        # is struck (VIS-D21.1); clicking again restores it and removes the
        # strike. The strip is exposed as ``header_bar`` / ``header_button`` so
        # the dock and tests can address it.
        self.header_bar = QWidget()
        self.header_bar.setObjectName("WatchlistHeader")
        self.header_bar.setFixedHeight(28)
        self.header_bar.setStyleSheet("background: #141822; border-bottom: 1px solid #232938;")
        h_layout = QHBoxLayout(self.header_bar)
        h_layout.setContentsMargins(8, 0, 8, 0)

        self.header_button = DiagonalStrikeButton("Watchlist", self.header_bar)
        self.header_button.setObjectName("WatchlistHeaderButton")
        # Checked == visible/unstruck; unchecked == collapsed/struck.
        self.header_button.setCheckable(True)
        self.header_button.setChecked(True)
        self.header_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_button.setStyleSheet(
            "QPushButton#WatchlistHeaderButton {"
            " background: transparent; border: none;"
            " color: #e5e7eb; font-weight: 600; text-align: left; padding: 0; }"
        )
        # Keep the palette in sync so the VIS-D21.1 strike uses the same
        # foreground colour as the label text (not the default dark ButtonText).
        _pal = self.header_button.palette()
        _pal.setColor(QPalette.ColorRole.ButtonText, QColor("#e5e7eb"))
        self.header_button.setPalette(_pal)
        self.header_button.toggled.connect(self._on_header_toggled)
        h_layout.addWidget(self.header_button)
        h_layout.addStretch()
        layout.addWidget(self.header_bar)

        # Table — built from the active-field layout, not a fixed index schema.
        self.table = QTableWidget(0, len(self._active_fields))
        self.table.setHorizontalHeaderLabels(self._headers())
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._apply_header_resize_modes()
        self.table.setStyleSheet("""
            QTableWidget { font-size: 11px; }
            QTableWidget::item { padding: 2px 4px; }
        """)
        layout.addWidget(self.table)
        #: The collapsible body — hidden by the header button (D21.11) while the
        #: header/title bar stays visible.
        self.body = self.table

        # D21.5: right-click a column header to add/remove/rearrange columns.
        header = self.table.horizontalHeader()
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_context_menu)

        # D14: double-click anywhere on a row requests the chart load
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    # ── Header collapse toggle (D21.11) ─────────────────────────────────────────

    def _on_header_toggled(self, checked: bool) -> None:
        """Collapse (hide) or restore the watchlist body from the header button.

        The button itself is the dock's title bar (set by ``MainWindow``), so it
        stays visible when the body is hidden. ``checked`` is the visible state:
        unchecked -> body hidden + VIS-D21.1 strike (auto-applied by
        :class:`DiagonalStrikeButton`); checked -> body shown + no strike.
        """
        visible = bool(checked)
        self._collapsed = not visible
        self.body.setVisible(visible)

    def is_collapsed(self) -> bool:
        """True while the watchlist body is hidden behind the header button."""
        return self._collapsed

    def set_collapsed(self, collapsed: bool) -> None:
        """Programmatically collapse/restore the body, syncing the header button."""
        collapsed = bool(collapsed)
        # ``setChecked`` emits ``toggled`` only when the state actually changes,
        # so apply the handler explicitly as well (idempotent).
        self.header_button.setChecked(not collapsed)
        self._on_header_toggled(not collapsed)

    def toggle_collapsed(self) -> None:
        """Flip the collapsed state (convenience for callers/tests)."""
        self.set_collapsed(not self._collapsed)

    # ── Column model (D21.5) ────────────────────────────────────────────────────

    def _headers(self) -> list[str]:
        return [COLUMN_DEFS[k]["header"] for k in self._active_fields]

    def _column_index(self, key: str) -> int:
        """Resolve a field key to its current column index, or -1 if hidden."""
        try:
            return self._active_fields.index(key)
        except ValueError:
            return -1

    def _format_field(self, key: str, value) -> str:
        definition = COLUMN_DEFS.get(key)
        if definition is None:
            return "—"
        return definition["extractor"](value)

    def _item(self, row: int, key: str):
        col = self._column_index(key)
        if col < 0:
            return None
        return self.table.item(row, col)

    def _apply_header_resize_modes(self) -> None:
        header = self.table.horizontalHeader()
        sym_col = self._column_index(SYMBOL_FIELD)
        for col in range(len(self._active_fields)):
            if col == sym_col:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(col, 70)
            else:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

    def _rebuild_table(self) -> None:
        """Rebuild columns/rows in the current order, re-rendering each cell.

        Values are held per row by field key, so a reorder/remove can never
        shift a value into the wrong field (DG32).
        """
        self.table.setColumnCount(len(self._active_fields))
        self.table.setHorizontalHeaderLabels(self._headers())
        self._apply_header_resize_modes()
        for row in range(self.table.rowCount()):
            values = self._row_data.get(row, {})
            for col, key in enumerate(self._active_fields):
                item = QTableWidgetItem(self._format_field(key, values.get(key)))
                align = (Qt.AlignmentFlag.AlignLeft if key == SYMBOL_FIELD
                         else Qt.AlignmentFlag.AlignRight)
                item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, col, item)

    def _apply_columns(self) -> None:
        """Apply the current layout to the table and persist it."""
        self._active_fields = ensure_symbol_present(self._active_fields)
        self._rebuild_table()
        save_watchlist_columns(self._settings, self._active_fields)

    def _build_header_menu(self) -> QMenu:
        """Build (but do not show) the header add/remove/rearrange popup."""
        menu = QMenu(self)
        for key in ALL_FIELDS:
            action = menu.addAction(COLUMN_DEFS[key]["header"])
            action.setCheckable(True)
            action.blockSignals(True)
            action.setChecked(key in self._active_fields)
            action.blockSignals(False)
            # Symbol can never be removed (AC-D21.5.3): shown checked+disabled.
            action.setEnabled(key != SYMBOL_FIELD)
            action.toggled.connect(
                lambda checked, k=key: self._on_field_toggled(k, checked))
        menu.addSeparator()
        move_menu = menu.addMenu("Move")
        for key in self._active_fields:
            idx = self._active_fields.index(key)
            header = COLUMN_DEFS[key]["header"]
            left = move_menu.addAction(f"Move {header} Left")
            left.setEnabled(idx > 0)
            left.triggered.connect(lambda _=False, k=key: self._move_field(k, -1))
            right = move_menu.addAction(f"Move {header} Right")
            right.setEnabled(idx < len(self._active_fields) - 1)
            right.triggered.connect(lambda _=False, k=key: self._move_field(k, +1))
        return menu

    def _on_header_context_menu(self, pos, show: bool = True):
        """Header context-menu handler; returns the popup (exec unless show)."""
        menu = self._build_header_menu()
        if show:
            menu.exec(self.table.horizontalHeader().mapToGlobal(pos))
        return menu

    def _on_field_toggled(self, key: str, checked: bool) -> None:
        """Add (re-show) or remove a field, then apply + persist."""
        if key == SYMBOL_FIELD:
            return  # Symbol always remains
        if checked:
            if key not in self._active_fields:
                self._active_fields.append(key)
                self._apply_columns()
        else:
            if key in self._active_fields:
                self._active_fields.remove(key)
                self._apply_columns()

    def _move_field(self, key: str, delta: int) -> None:
        """Move a field left/right in the layout, then apply + persist."""
        if key not in self._active_fields:
            return
        idx = self._active_fields.index(key)
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self._active_fields):
            return
        self._active_fields.pop(idx)
        self._active_fields.insert(new_idx, key)
        self._apply_columns()

    # ── Public API ─────────────────────────────────────────────────────────────

    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        # Resolve the Symbol cell by field key, so a reorder cannot break D14.
        item = self._item(row, SYMBOL_FIELD)
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
        self._row_data[row] = {SYMBOL_FIELD: symbol}

        for col, key in enumerate(self._active_fields):
            item = QTableWidgetItem(self._format_field(key, self._row_data[row].get(key)))
            align = (Qt.AlignmentFlag.AlignLeft if key == SYMBOL_FIELD
                     else Qt.AlignmentFlag.AlignRight)
            item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)

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
        self._row_data.clear()
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

        field = None
        if tick_type == TICK_LAST:
            field = "last"
            old = self._last_price.get(req_id)
            self._last_price[req_id] = price
            # Compute change
            prev = self._prev_close.get(req_id)
            if prev and prev > 0:
                chg = price - prev
                chg_pct = (chg / prev) * 100
                self._set_cell(row, "chg", chg)
                self._set_cell(row, "chgpct", chg_pct)
                color = GREEN if chg >= 0 else RED
                self._set_foreground(row, "chg", color)
                self._set_foreground(row, "chgpct", color)
            # Flash the last column
            if old is not None:
                self._flash(row, field, GREEN if price >= old else RED)
        elif tick_type == TICK_BID:
            field = "bid"
        elif tick_type == TICK_ASK:
            field = "ask"

        if field is not None:
            self._set_cell(row, field, price)

    def on_tick_size(self, req_id: int, tick_type: int, size: int):
        row = self._req_to_row.get(req_id)
        if row is None:
            return
        # tick_type 8 = volume
        if tick_type == 8:
            self._set_cell(row, "vol", size)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _set_cell(self, row: int, key: str, value):
        """Store the raw value against the field key and render the cell."""
        self._row_data.setdefault(row, {})[key] = value
        item = self._item(row, key)
        if item:
            item.setText(self._format_field(key, value))

    def _set_foreground(self, row: int, key: str, color: QColor):
        item = self._item(row, key)
        if item:
            item.setForeground(QBrush(color))

    def _flash(self, row: int, key: str, color: QColor):
        """Briefly highlight a cell then fade back to default."""
        item = self._item(row, key)
        if not item:
            return
        item.setBackground(QBrush(color))
        timer_key = (row, key)
        if timer_key in self._flash_timers:
            self._flash_timers[timer_key].stop()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: item.setBackground(QBrush(QColor('#101218'))))
        timer.start(400)  # flash for 400 ms
        self._flash_timers[timer_key] = timer
