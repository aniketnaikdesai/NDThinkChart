from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHeaderView, QMenu, QDialog, QLineEdit, QListWidget,
    QListWidgetItem, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QBrush, QPalette

import ui.dock_layout as dock_layout
from ui.visual_conventions import DiagonalStrikeButton
from ui.add_symbol_dialog import AddSymbolDialog
from ibkr.subscription_manager import MARKET_DATA

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


# ── D22.3: symbol normalisation helpers (pure) ────────────────────────────────

def normalise_symbol(text) -> str:
    """Return the canonical (trimmed, upper-cased) form of a symbol string.

    Empty / whitespace-only / ``None`` input normalises to ``""`` so callers can
    treat that as "no symbol" without a separate emptiness check.
    """
    return str(text if text is not None else "").strip().upper()


def symbol_in_list(symbol, symbols) -> bool:
    """Case-insensitively test whether ``symbol`` already appears in ``symbols``.

    A blank ``symbol`` is never considered present — a missing entry must not be
    reported as a duplicate of another blank entry.
    """
    target = normalise_symbol(symbol)
    if not target:
        return False
    return any(normalise_symbol(s) == target for s in (symbols or []))


class WatchlistPanel(QWidget):
    """
    Dense watchlist table. Each row subscribes to IBKR reqMktData.
    Cells flash green/red on tick updates using a QTimer fade.

    Columns are configurable (D21.5): a right-click on the header offers
    add/remove/rearrange, and the layout is persisted to QSettings.
    """

    row_double_clicked = pyqtSignal(str)  # symbol (D14)
    # D22: add/remove intent signals. ``symbol_remove_requested`` is consumed by
    # the remove affordance (D22-05); both carry the raw symbol string.
    symbol_add_requested = pyqtSignal(str)
    symbol_remove_requested = pyqtSignal(str)
    # D39.1: symbol search intents. ``search_text_changed`` fires on every
    # keystroke (the service debounces); ``search_sample_selected`` carries
    # the chosen ContractDescription.
    search_text_changed = pyqtSignal(str)
    search_sample_selected = pyqtSignal(object)

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
        # D27.3: subscription registry (injected by MainWindow) so live
        # market-data subs are type-tagged for the reconnect replay.
        self._sub_manager = None
        # D27.5: sink for (symbol, last_price) fed to MainWindow's central
        # symbol -> last_price map.
        self._price_sink = None
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

        # D22.1: a small '+' affordance adjacent to the title toggle. It shares
        # the header strip's layout and is enabled/disabled together with the
        # "Add symbol…" menu action by ``set_add_enabled``.
        self.add_button = QPushButton("+", self.header_bar)
        self.add_button.setObjectName("WatchlistAddButton")
        self.add_button.setFixedSize(18, 18)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setToolTip("Add symbol")
        self.add_button.setStyleSheet(
            "QPushButton#WatchlistAddButton {"
            " background: transparent; border: none;"
            " color: #e5e7eb; font-weight: 700; font-size: 14px;"
            " padding: 0; }"
            "QPushButton#WatchlistAddButton:disabled { color: #4b5563; }"
        )
        self.add_button.clicked.connect(self._on_add_clicked)
        h_layout.addWidget(self.add_button)

        # D39.1: symbol search box in the watchlist header. Every keystroke
        # is forwarded (debounced downstream); results appear in a popup.
        self.search_box = QLineEdit(self.header_bar)
        self.search_box.setObjectName("WatchlistSearchBox")
        self.search_box.setPlaceholderText("Search symbols…")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setFixedHeight(20)
        # D39.1: no minimum width — the box yields so the dock can still
        # shrink to WATCHLIST_MIN_WIDTH (150, D17-tested); it expands to
        # fill available header space otherwise (capped at 180).
        self.search_box.setMinimumWidth(0)
        self.search_box.setMaximumWidth(180)
        self.search_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_box.setStyleSheet(
            "QLineEdit#WatchlistSearchBox {"
            " background: #0f1420; border: 1px solid #232938;"
            " border-radius: 3px; color: #e5e7eb; font-size: 11px;"
            " padding: 1px 4px; }"
            "QLineEdit#WatchlistSearchBox:disabled { color: #4b5563; }"
        )
        self.search_box.textChanged.connect(self._on_search_text_changed)
        self.search_box.setEnabled(False)  # enabled on connect (39.1)
        h_layout.addWidget(self.search_box)

        # Results popup (dismissed on outside click by the Popup flag;
        # parented to the panel so it dies with it).
        self._search_popup = QFrame(self, Qt.WindowType.Popup)
        self._search_popup.setObjectName("WatchlistSearchPopup")
        self._search_popup.setStyleSheet(
            "QFrame#WatchlistSearchPopup {"
            " background: #141822; border: 1px solid #2b3348; }"
        )
        popup_layout = QVBoxLayout(self._search_popup)
        popup_layout.setContentsMargins(2, 2, 2, 2)
        self._search_list = QListWidget(self._search_popup)
        self._search_list.setStyleSheet(
            "QListWidget { background: #141822; color: #e5e7eb;"
            " font-size: 11px; border: none; }"
            "QListWidget::item { padding: 3px 6px; }"
            "QListWidget::item:selected { background: #1f3a5f; }"
        )
        self._search_list.itemClicked.connect(self._on_search_item_clicked)
        popup_layout.addWidget(self._search_list)
        self._search_popup.hide()

        h_layout.addStretch()

        # D22.2/D22.5: the header strip offers "Add symbol…" via its own custom
        # context menu. The D21.5 column popup stays on the table's horizontal
        # header — this strip menu is a separate affordance and must not shadow
        # it. Starts disabled (``set_add_enabled(False)`` below).
        self.header_bar.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.header_bar.customContextMenuRequested.connect(
            self._on_strip_context_menu)
        self._add_enabled = False
        self._strip_menu = None
        self._build_strip_menu()
        self.set_add_enabled(False)

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

        # D22.5: right-clicking the table *body* (the viewport) offers
        # "Remove symbol" for the row under the cursor. This is a separate
        # affordance from the D21.5 header popup, which stays on the header.
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_body_context_menu)

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

    # ── Add affordance (D22) ────────────────────────────────────────────────────

    def _build_strip_menu(self) -> QMenu:
        """Build (but do not show) the header-strip "Add symbol…" popup.

        The menu/action are kept on the panel so :meth:`set_add_enabled` can
        toggle the action without rebuilding it.
        """
        menu = QMenu(self.header_bar)
        self.add_action = menu.addAction("Add symbol…")
        self.add_action.setEnabled(self._add_enabled)
        self.add_action.triggered.connect(self._on_add_requested)
        self._strip_menu = menu
        return menu

    def _ensure_strip_menu(self) -> QMenu:
        if self._strip_menu is None:
            self._build_strip_menu()
        return self._strip_menu

    def _on_strip_context_menu(self, pos, show: bool = True):
        """Header-strip context-menu handler; returns the popup (exec unless show)."""
        menu = self._ensure_strip_menu()
        if show:
            menu.exec(self.header_bar.mapToGlobal(pos))
        return menu

    def set_add_enabled(self, enabled: bool) -> None:
        """Enable/disable the '+' button and the "Add symbol…" menu action.

        Defaults to disabled; ``MainWindow`` (D22-07/08) enables it once the
        symbol source is available. The D21.11 collapse toggle is untouched.
        """
        enabled = bool(enabled)
        self._add_enabled = enabled
        self.add_button.setEnabled(enabled)
        action = getattr(self, "add_action", None)
        if action is not None:
            action.setEnabled(enabled)

    # ── D39.1 symbol search ──────────────────────────────────────────────

    def set_search_enabled(self, enabled: bool) -> None:
        """Enable/disable the header search box (transport state).

        Disabled while disconnected — typing then is refused with the box
        greyed out (AC: "disconnected → disabled + message"; the message is
        the tooltip/status text, owned by MainWindow).
        """
        self.search_box.setEnabled(bool(enabled))
        if not enabled:
            self.clear_search_results()

    def _on_search_text_changed(self, text: str) -> None:
        if not text.strip():
            self.clear_search_results()
        self.search_text_changed.emit(text)

    def show_search_results(self, samples: list) -> None:
        """Populate the results popup (≤16 ContractDescriptions)."""
        self._search_list.clear()
        for desc in samples or []:
            contract = getattr(desc, "contract", None)
            symbol = getattr(contract, "symbol", "?") or "?"
            sec_type = getattr(contract, "secType", "") or ""
            exchange = getattr(contract, "exchange", "") or ""
            label = symbol
            detail = " · ".join(p for p in (sec_type, exchange) if p)
            if detail:
                label += f"  ({detail})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, desc)
            self._search_list.addItem(item)
        if not samples:
            item = QListWidgetItem("No matches")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setData(Qt.ItemDataRole.UserRole, None)
            self._search_list.addItem(item)
        self._search_list.setCurrentRow(-1)
        self._search_list.setFixedHeight(
            min(220, max(30, self._search_list.count() * 24 + 8)))
        self._search_list.setFixedWidth(
            max(200, self.search_box.width() + 60))
        pos = self.search_box.mapToGlobal(
            self.search_box.rect().bottomLeft())
        self._search_popup.move(pos)
        self._search_popup.show()

    def clear_search_results(self) -> None:
        self._search_popup.hide()
        self._search_list.clear()

    def _on_search_item_clicked(self, item: QListWidgetItem) -> None:
        desc = item.data(Qt.ItemDataRole.UserRole)
        if desc is None:
            return
        self.clear_search_results()
        self.search_box.clear()
        self.search_sample_selected.emit(desc)

    def _on_add_clicked(self, *_args) -> None:
        self._invoke_add_symbol()

    def _on_add_requested(self, *_args) -> None:
        self._invoke_add_symbol()

    def _invoke_add_symbol(self) -> None:
        """Show the modal AddSymbolDialog and emit on an accepted symbol.

        Cancel/Esc (rejected) emits nothing; an accepted but blank text emits
        nothing. The accepted text is reported verbatim (raw) — the window owns
        any normalisation policy.
        """
        if not self._add_enabled:
            return
        dialog = AddSymbolDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            raw = dialog.text()
            if raw is not None and raw.strip():
                self.symbol_add_requested.emit(raw)

    # ── Remove affordance (D22.5) ───────────────────────────────────────────────

    def _row_symbol(self, row: int) -> str:
        """Return the row's Symbol text, resolved **by field key** (reorder-safe).

        The Symbol column is looked up through the live ``_active_fields`` layout
        (``_item`` -> ``_column_index``), so a column reorder can never make this
        read a different field's cell. Returns ``""`` for a missing / placeholder
        cell (an "empty" row).
        """
        item = self._item(row, SYMBOL_FIELD)
        if item is None:
            return ""
        text = (item.text() or "").strip()
        return "" if text in ("", "—") else text

    def _row_index_for_symbol(self, symbol) -> int | None:
        """Return the first row whose Symbol matches ``symbol`` (case-insensitive).

        ``None`` when the table has no such row.
        """
        target = normalise_symbol(symbol)
        if not target:
            return None
        for row in range(self.table.rowCount()):
            if normalise_symbol(self._row_symbol(row)) == target:
                return row
        return None

    def _on_body_context_menu(self, pos, show: bool = True):
        """Build the table-body "Remove symbol" popup for the row under ``pos``.

        Returns the popup (or ``None`` when there is no real row there). Header
        and empty areas resolve to no row, so nothing is offered and nothing can
        be emitted. The row's Symbol is read by field key (reorder-safe) and
        carried verbatim into ``symbol_remove_requested`` when the action fires.
        """
        index = self.table.indexAt(pos)
        if not index.isValid():
            return None
        row = index.row()
        symbol = self._row_symbol(row)
        if not symbol:
            return None
        menu = QMenu(self.table)
        action = menu.addAction("Remove symbol")
        action.triggered.connect(lambda _=False, s=symbol: self._on_remove_requested(s))
        if show:
            menu.exec(self.table.viewport().mapToGlobal(pos))
        return menu

    def _on_remove_requested(self, symbol: str) -> None:
        """Emit the remove intent for a symbol resolved from the body menu."""
        self.symbol_remove_requested.emit(symbol)

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

    def set_market_data_manager(self, md_manager):
        """Inject MarketDataManager for live tick subscriptions."""
        self._md_manager = md_manager

    def set_subscription_manager(self, sub_manager):
        """Inject the SubscriptionManager for reconnect replay (D27.3)."""
        self._sub_manager = sub_manager

    def set_price_sink(self, sink):
        """Inject the (symbol, price) sink for the central price map (D27.5)."""
        self._price_sink = sink

    # ── MarketDepth management ───────────────────────────────────────────────────

    def active_row_count(self) -> int:
        """Live market-data rows (each holds one reqMktData line)."""
        return len(self._req_to_row)

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
        # D27.3: type-tag the live subscription for the reconnect replay.
        # (Re-issued by _restore_watchlist's clear+re-add on reconnect, so
        # replay_all skips MARKET_DATA — see MainWindow._replay_subscriptions.)
        if self._sub_manager is not None:
            self._sub_manager.subscribe(
                symbol,
                req_id,
                MARKET_DATA,
                reissue=lambda c=contract: self._md_manager.req_mkt_data(c),
                rebind=lambda new_id, _old=req_id, _sym=symbol: (
                    self._rebind_mkt_data_req_id(_sym, _old, new_id)
                ),
            )

    def _rebind_mkt_data_req_id(self, symbol: str, old_id: int,
                                new_id: int) -> None:
        """D27.3: point a watchlist row at a replayed subscription's reqId.

        Row lookup is by symbol (not the captured row) because removes
        re-index the row-keyed state.
        """
        self._req_to_row.pop(old_id, None)
        for cache in (self._prev_close, self._last_price):
            if old_id in cache:
                cache[new_id] = cache.pop(old_id)
        row = self._row_index_for_symbol(symbol)
        if row is not None:
            self._req_to_row[new_id] = row

    def remove_symbol(self, symbol: str) -> bool:
        """Remove the row for ``symbol`` and stop its live subscription.

        Finds the row by Symbol (case-insensitive), cancels that row's
        ``req_mkt_data`` subscription, stops the removed row's flash timers,
        deletes the row and re-indexes the row-keyed state — ``_req_to_row``
        values, ``_row_data`` keys and flash-timer keys — so a later tick for a
        remaining reqId still lands on the correct Symbol row. After a
        successful removal the row-keyed state is exactly over the surviving
        rows: ``set(self._row_data.keys()) == set(range(self.table.rowCount()))``
        (and likewise the ``_req_to_row`` values and flash-timer keys cover
        exactly those rows). ``_prev_close`` / ``_last_price`` are keyed by
        reqId, so the removed reqId's entries are dropped and the remaining
        ones are left untouched.

        Returns ``True`` when a row was removed, ``False`` (a no-op that cancels
        and changes nothing) when the symbol is absent or blank.
        """
        row = self._row_index_for_symbol(symbol)
        if row is None:
            return False

        # Cancel this row's subscription(s) and drop their per-reqId state.
        req_ids = [rid for rid, r in self._req_to_row.items() if r == row]
        for req_id in req_ids:
            if self._md_manager:
                self._md_manager.cancel_mkt_data(req_id)
            if self._sub_manager is not None:
                self._sub_manager.unsubscribe(req_id)
            self._req_to_row.pop(req_id, None)
            self._prev_close.pop(req_id, None)
            self._last_price.pop(req_id, None)

        # Stop the removed row's flash timers (they must not fire post-removal).
        for timer_key in [k for k in self._flash_timers if k[0] == row]:
            self._flash_timers.pop(timer_key).stop()

        self.table.removeRow(row)

        # Drop the removed row's own cached entry, then re-index the row-keyed
        # state for every row above the removed one. Popping first is what keeps
        # the invariant exact: without it the re-map would leave the removed
        # row's key behind as a stale entry.
        self._row_data.pop(row, None)
        self._row_data = {
            (r - 1 if r > row else r): values
            for r, values in self._row_data.items()
        }
        self._req_to_row = {
            req_id: (r - 1 if r > row else r)
            for req_id, r in self._req_to_row.items()
        }
        self._flash_timers = {
            ((k[0] - 1 if k[0] > row else k[0]), k[1]): timer
            for k, timer in self._flash_timers.items()
        }
        return True

    def clear(self):
        """Cancel all active market-data subscriptions and empty the table."""
        if self._md_manager:
            for req_id in list(self._req_to_row.keys()):
                self._md_manager.cancel_mkt_data(req_id)
        # D27.3: drop the registry entries too, so a later reconnect replay
        # never re-issues these dead subscriptions.
        if self._sub_manager is not None:
            self._sub_manager.unsubscribe_all_of_type(MARKET_DATA)
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
            # D27.5: feed the central symbol -> last_price map.
            if self._price_sink is not None:
                symbol = self._row_data.get(row, {}).get(SYMBOL_FIELD)
                if symbol:
                    self._price_sink(symbol, price)
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

    def _unflash(self, row: int, key: str):
        """Reset a flashed cell to the default background.

        The cell item is resolved lazily by ``(row, key)`` at fire time rather
        than captured by the timer closure. A column-layout rebuild
        (``_rebuild_table`` via ``_apply_columns`` / ``_on_field_toggled`` /
        ``_move_field``) replaces every cell item without touching
        ``_flash_timers``, so a captured item could already be a freed C++
        object when the pending timer fires
        (``RuntimeError: wrapped C/C++ object of type QTableWidgetItem has been
        deleted``, ESC-034). Resolving the *current* item is what makes the
        reset robust to any item replacement; it is deliberately not an
        exception-swallowing shim.
        """
        item = self._item(row, key)
        if item:
            item.setBackground(QBrush(QColor('#101218')))

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
        # ESC-034: resolve the cell at fire time (``_unflash``) instead of
        # closing over the item, which a rebuild may have deleted by then.
        timer.timeout.connect(lambda: self._unflash(row, key))
        timer.start(400)  # flash for 400 ms
        self._flash_timers[timer_key] = timer
