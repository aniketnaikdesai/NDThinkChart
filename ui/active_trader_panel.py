"""Active trader panel with Level I/II price ladder and aggregated book views.

Renders the near-touch market-depth snapshot the same way the reference app
does: best bid at the center-right, best ask center-left, size, price, with an
optional cumulative toggle and per-cell flash on size changes.

Phase 5 additions:
- Order Entry tab with Buy/Sell MKT buttons, order-type selector,
  safety gate ("Enable live orders" switch, default OFF),
  confirmation label before send, and status row.
- Ladder click-to-trade: clicking bid column builds a BUY LMT at that price;
  clicking ask builds a SELL LMT.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPalette
from PyQt6.QtWidgets import (
    QCheckBox, QLabel, QPushButton, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QVBoxLayout, QHBoxLayout,
    QWidget, QHeaderView, QComboBox, QLineEdit, QSizePolicy,
)

import ui.dock_layout as dock_layout
from ui.visual_conventions import DiagonalStrikeButton

#: Bounded minimum width of this panel (D18 Phase 4). Shared with the right
#: region's own minimum so the ladder/book tables can never demand more width
#: than the region is allowed to have and push it off-screen (AC-D18.6).
RIGHT_DOCK_MIN_WIDTH = dock_layout.RIGHT_DOCK_MIN_WIDTH

GREEN = QColor('#34d399')
RED = QColor('#f87171')
BG = QColor('#101218')
MID = QColor('#fbbf24')

SIDE_ASK = 0
SIDE_BID = 1


class LadderTable(QTableWidget):
    # row, col, price -> clicked price level
    price_clicked = pyqtSignal(int, int, float)

    def __init__(self, num_levels: int = 10):
        self._num_levels = num_levels
        rows = 2 * num_levels + 1
        super().__init__(rows, 4)
        self.setHorizontalHeaderLabels(["Ask Size", "Ask", "Bid", "Bid Size"])
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # D18 Phase 4: bound the table's width demand. ``Ignored`` horizontal
        # policy + a zero minimum means the Stretch columns are laid out to the
        # available width instead of forcing a content-driven minimum that would
        # push the whole right region off-screen (AC-D18.6).
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored, self.sizePolicy().verticalPolicy()
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._flash_timers: dict[int, QTimer] = {}
        self._prev_sizes: dict[tuple, int] = {}
        self._last_price: float | None = None
        self._style_columns()

    def _style_columns(self):
        self.setStyleSheet("""
            QTableWidget { background: #101218; border: none; font-size: 12px; }
            QTableWidget::item { padding: 2px 6px; }
            QHeaderView::section { background: #1a1f2e; color: #cbd5e1;
                                   border: none; padding: 3px; }
        """)

    def _set(self, row: int, col: int, text: str, color: str | None = None):
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.setItem(row, col, item)
        item.setText(text)
        if color:
            item.setForeground(QBrush(QColor(color)))
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if col not in (2,) else Qt.AlignmentFlag.AlignCenter
        )

    def clear_all(self):
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                self._set(row, col, "")
        self._prev_sizes.clear()

    def set_last_price(self, price: float | None):
        self._last_price = price
        if price is not None:
            mid_row = self._num_levels
            self._set(mid_row, 0, "", "#475569")
            self._set(mid_row, 2, f"{price:.2f}", "#fbbf24")
            self._set(mid_row, 3, "", "#475569")
            self._set(mid_row, 1, "", "#475569")

    def render(self, asks: list, bids: list, cumulative: bool):
        """asks/bids ordered inside -> outside (position 0 = best)."""
        n = self._num_levels
        mid_row = n

        ask_rows = asks[:n]
        bid_rows = bids[:n]

        for j in range(n):
            src_row = n - 1 - j
            if src_row < len(ask_rows):
                level = ask_rows[src_row]
                self._set(j, 0, f"{level['size']:,}", "#f87171")
                self._set(j, 1, f"{level['price']:.2f}", "#f87171")
                self._maybe_flash_size(j, 0, level['size'], RED)
            else:
                self._set(j, 0, "")
                self._set(j, 1, "")

        for j in range(n):
            row = mid_row + 1 + j
            if j < len(bid_rows):
                level = bid_rows[j]
                self._set(row, 2, f"{level['price']:.2f}", "#34d399")
                self._set(row, 3, f"{level['size']:,}", "#34d399")
                self._maybe_flash_size(row, 3, level['size'], GREEN)
            else:
                self._set(row, 2, "")
                self._set(row, 3, "")

        if cumulative:
            self._apply_cumulative(ask_rows, bid_rows)

    def _apply_cumulative(self, ask_rows, bid_rows):
        running = 0
        for j in range(self._num_levels):
            src_row = self._num_levels - 1 - j
            if src_row < len(ask_rows):
                running += ask_rows[src_row]['size']
                self._set(j, 0, f"{running:,}", "#f87171")
        running = 0
        for j in range(self._num_levels):
            if j < len(bid_rows):
                running += bid_rows[j]['size']
                self._set(self._num_levels + 1 + j, 3, f"{running:,}", "#34d399")

    def _maybe_flash_size(self, row: int, col: int, size: int, color: QColor):
        key = (row, col)
        prev = self._prev_sizes.get(key)
        self._prev_sizes[key] = size
        if prev is not None and prev != size:
            self._flash(row, col, color)

    def _flash(self, row: int, col: int, color: QColor):
        item = self.item(row, col)
        if not item:
            return
        item.setBackground(QBrush(color))
        key = row * 20 + col
        if key in self._flash_timers:
            self._flash_timers[key].stop()
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: item.setBackground(QBrush(BG)))
        timer.start(400)
        self._flash_timers[key] = timer

    def clear_flash_timers(self):
        for timer in self._flash_timers.values():
            timer.stop()
        self._flash_timers.clear()

    def cellClicked(self, row: int, col: int):
        price_str = self.item(row, col)
        if price_str is None or not price_str.text():
            return
        try:
            price = float(price_str.text())
        except ValueError:
            return
        self.price_clicked.emit(row, col, price)


class BookTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 3)
        self.setHorizontalHeaderLabels(["Side", "Price", "Size"])
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # D18 Phase 4: same width bound as LadderTable — content must not force
        # the right region past its cap (AC-D18.6).
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored, self.sizePolicy().verticalPolicy()
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def render(self, asks: list, bids: list, cumulative: bool):
        self.setRowCount(0)
        rows = []
        for level in asks:
            rows.append(("Ask", level["price"], level["size"], "#f87171"))
        for level in bids:
            rows.append(("Bid", level["price"], level["size"], "#34d399"))
        for side, price, size, color in rows:
            row = self.rowCount()
            self.insertRow(row)
            self._cell(row, 0, side, color)
            self._cell(row, 1, f"{price:.2f}", color)
            self._cell(row, 2, f"{size:,}", color)

    def _cell(self, row: int, col: int, text: str, color: str):
        item = QTableWidgetItem(text)
        item.setForeground(QBrush(QColor(color)))
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.setItem(row, col, item)


class OrderEntryWidget(QWidget):
    """Order entry form with safety gate and confirmation step."""

    # Emitted when user requests an order to be placed:
    # (action, qty, order_type, limit_price, stop_price, target_price)
    # limit_price, stop_price, target_price are 0.0 when not applicable
    order_place_requested = pyqtSignal(str, int, str, float, float, float)

    def __init__(self):
        super().__init__()
        self._symbol: str = ""
        self._last_price: float | None = None
        self._pending: dict | None = None

        # D18 Phase 4: bound the order-entry form width so its price fields cannot
        # force the right region past the 40% cap (AC-D18.6).
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored, self.sizePolicy().verticalPolicy()
        )

        layout = QVBoxLayout(self)

        # ── Safety gate ──
        self.enable_live_check = QCheckBox("Enable live orders (default OFF)")
        self.enable_live_check.setChecked(False)
        layout.addWidget(self.enable_live_check)

        # ── Symbol display ──
        sym_row = QHBoxLayout()
        sym_row.addWidget(QLabel("Symbol:"))
        self.symbol_label = QLabel("—")
        self.symbol_label.setStyleSheet("font-weight: 700; font-size: 13px;")
        sym_row.addWidget(self.symbol_label)
        sym_row.addStretch()
        layout.addLayout(sym_row)

        # ── Quantity ──
        qty_row = QHBoxLayout()
        qty_row.addWidget(QLabel("Qty:"))
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 100_000)
        self.qty_input.setValue(100)
        self.qty_input.setPrefix("Qty ")
        qty_row.addWidget(self.qty_input)
        qty_row.addStretch()
        layout.addLayout(qty_row)

        # ── Quick Buy/Sell MKT ──
        mkt_row = QHBoxLayout()
        self.buy_mkt_btn = QPushButton("Buy MKT")
        self.buy_mkt_btn.setStyleSheet("background: #34d399; color: #0d0f14;")
        self.sell_mkt_btn = QPushButton("Sell MKT")
        self.sell_mkt_btn.setStyleSheet("background: #f87171; color: #0d0f14;")
        self.buy_mkt_btn.clicked.connect(self._on_buy_mkt)
        self.sell_mkt_btn.clicked.connect(self._on_sell_mkt)
        mkt_row.addWidget(self.buy_mkt_btn)
        mkt_row.addWidget(self.sell_mkt_btn)
        mkt_row.addStretch()
        layout.addLayout(mkt_row)

        # ── Order type ──
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Order Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["MKT", "LMT", "STP", "BRACKET"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo)
        type_row.addStretch()
        layout.addLayout(type_row)

        # ── Price fields ──
        price_row = QHBoxLayout()
        price_row.addWidget(QLabel("Limit:"))
        self.lmt_price_input = QLineEdit()
        self.lmt_price_input.setPlaceholderText("—")
        price_row.addWidget(self.lmt_price_input)
        price_row.addWidget(QLabel("Stop:"))
        self.stop_price_input = QLineEdit()
        self.stop_price_input.setPlaceholderText("—")
        price_row.addWidget(self.stop_price_input)
        price_row.addWidget(QLabel("Target:"))
        self.target_price_input = QLineEdit()
        self.target_price_input.setPlaceholderText("—")
        price_row.addWidget(self.target_price_input)
        layout.addLayout(price_row)

        # ── Place order button ──
        self.place_btn = QPushButton("Place Order")
        self.place_btn.clicked.connect(self._on_place)
        layout.addWidget(self.place_btn)

        # ── Confirmation step ──
        confirm_box = QHBoxLayout()
        self.confirm_label = QLabel("")
        self.confirm_label.setStyleSheet("color: #fbbf24; font-weight: 700;")
        self.confirm_label.setVisible(False)
        confirm_box.addWidget(self.confirm_label)

        self.confirm_btn = QPushButton("Confirm Send")
        self.confirm_btn.setVisible(False)
        self.confirm_btn.clicked.connect(self._on_confirm)
        confirm_box.addWidget(self.confirm_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        confirm_box.addWidget(self.cancel_btn)
        confirm_box.addStretch()
        layout.addLayout(confirm_box)

        # ── Status row ──
        self.status_label = QLabel("No active orders")
        self.status_label.setStyleSheet("color: #a3a3a3; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.enable_live_check.toggled.connect(self._on_enable_toggled)
        self._on_enable_toggled(False)
        self._on_type_changed(0)

    def set_symbol(self, symbol: str, last_price: float | None = None):
        self._symbol = symbol
        self.symbol_label.setText(symbol or "—")
        self._last_price = last_price
        if last_price:
            self.lmt_price_input.setText(f"{last_price:.2f}")

    def set_order_status(self, order_id: int, action: str, qty: float,
                         status: str):
        self.status_label.setText(
            f"#{order_id} {self._symbol or '?'} {action} {qty:g} {status}"
        )

    def _on_enable_toggled(self, enabled: bool):
        self.place_btn.setEnabled(enabled)
        self.buy_mkt_btn.setEnabled(enabled)
        self.sell_mkt_btn.setEnabled(enabled)

    def _on_type_changed(self, _index: int):
        order_type = self.type_combo.currentText()
        is_bracket = order_type == "BRACKET"
        self.target_price_input.setEnabled(is_bracket)
        self.stop_price_input.setPlaceholderText(
            "Stop price" if order_type in ("STP", "BRACKET") else "—"
        )
        self.lmt_price_input.setPlaceholderText(
            "Limit price" if order_type in ("LMT", "BRACKET") else "—"
        )

    def _on_buy_mkt(self):
        self._request_send("BUY", "MKT", 0.0, 0.0, 0.0)

    def _on_sell_mkt(self):
        self._request_send("SELL", "MKT", 0.0, 0.0, 0.0)

    def _on_place(self):
        order_type = self.type_combo.currentText()
        qty = self.qty_input.value()
        action = "BUY"

        lmt_price = 0.0
        stop_price = 0.0
        target_price = 0.0

        if order_type in ("LMT", "BRACKET"):
            lmt_price = float(self.lmt_price_input.text() or 0)
        if order_type in ("STP", "BRACKET"):
            stop_price = float(self.stop_price_input.text() or 0)
        if order_type == "BRACKET":
            target_price = float(self.target_price_input.text() or 0)

        self._request_send(action, order_type, qty, lmt_price, stop_price, target_price)

    def _request_send(self, action: str, order_type: str, qty: float,
                      lmt_price: float, stop_price: float, target_price: float):
        """Show confirmation label instead of sending immediately."""
        price_display = f"@ {lmt_price:.2f}" if lmt_price else "@ market"
        self.confirm_label.setText(f"{qty:g} x {order_type} {price_display}")
        self.confirm_label.setVisible(True)
        self.confirm_btn.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.place_btn.setEnabled(False)

        self._pending = {
            "action": action,
            "order_type": order_type,
            "qty": qty,
            "lmt_price": lmt_price,
            "stop_price": stop_price,
            "target_price": target_price,
        }

    def _on_confirm(self):
        if not self._pending:
            return
        if not self.enable_live_check.isChecked():
            self.status_label.setText("Enable live orders first.")
            return
        p = self._pending
        self.order_place_requested.emit(
            p["action"], p["qty"], p["order_type"],
            p["lmt_price"], p["stop_price"], p["target_price"],
        )

    def _on_cancel(self):
        self._reset_confirmation()
        self.place_btn.setEnabled(self.enable_live_check.isChecked())

    def _reset_confirmation(self):
        self.confirm_label.setVisible(False)
        self.confirm_btn.setVisible(False)
        self.cancel_btn.setVisible(False)
        self._pending = None


class ActiveTraderPanel(QWidget):
    """Dockable panel: Ladder + Book + Order Entry."""

    # symbol, action, qty, order_type, limit_price, stop_price, target_price
    order_place_requested = pyqtSignal(str, str, int, str, float, float, float)

    def __init__(self, num_levels: int = 10):
        super().__init__()
        self._num_levels = num_levels
        self._symbol: str = ""
        self._last_price: float | None = None
        self._collapsed = False

        # D18 Phase 4: the panel's own width is bounded to the shared right-region
        # minimum and its horizontal size policy ignores the content size hint, so
        # the ladder/book tabs scroll or clip internally rather than forcing the
        # region wider than the 40% cap (AC-D18.6).
        self.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored, self.sizePolicy().verticalPolicy()
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header strip (D21.13) ─────────────────────────────────────────────
        # ``MainWindow`` promotes this strip to the right dock's title-bar widget
        # via ``setTitleBarWidget``; its label is a ``DiagonalStrikeButton`` that
        # hides/shows the body below while the button itself stays visible
        # (AC-D21.13.1/AC-D21.13.4). It is exposed as ``header_bar`` /
        # ``header_button`` so the dock and tests can address it.
        self.header_bar = QWidget()
        self.header_bar.setObjectName("ActiveTraderHeader")
        self.header_bar.setFixedHeight(28)
        self.header_bar.setStyleSheet(
            "background: #141822; border-bottom: 1px solid #232938;"
        )
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(8, 0, 8, 0)

        self.header_button = DiagonalStrikeButton("Active Trader", self.header_bar)
        self.header_button.setObjectName("ActiveTraderHeaderButton")
        # Checked == shown/unstruck; unchecked == hidden/struck.
        self.header_button.setCheckable(True)
        self.header_button.setChecked(True)
        self.header_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_button.setStyleSheet(
            "QPushButton#ActiveTraderHeaderButton {"
            " background: transparent; border: none;"
            " color: #e5e7eb; font-weight: 600; text-align: left; padding: 0; }"
        )
        # Keep the palette in sync so the VIS-D21.1 strike uses the label colour.
        _pal = self.header_button.palette()
        _pal.setColor(QPalette.ColorRole.ButtonText, QColor("#e5e7eb"))
        self.header_button.setPalette(_pal)
        self.header_button.toggled.connect(self._on_header_toggled)
        header_layout.addWidget(self.header_button)
        header_layout.addStretch()
        outer.addWidget(self.header_bar)

        # ── Body — the collapsible content (D21.13) ───────────────────────────
        self.body = QWidget()
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(6, 6, 6, 6)

        # ── Header row ──
        header_row = QHBoxLayout()
        self.symbol_label = QLabel("—")
        self.symbol_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        self.cumulative_check = QCheckBox("Cumulative")
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 100_000)
        self.qty_input.setValue(100)
        self.qty_input.setPrefix("Qty ")
        header_row.addWidget(self.symbol_label)
        header_row.addStretch()
        header_row.addWidget(self.cumulative_check)
        header_row.addWidget(self.qty_input)
        layout.addLayout(header_row)

        # ── Tabs ──
        self.tabs = QTabWidget()
        self.ladder = LadderTable(num_levels)
        self.book = BookTable()
        self.tabs.addTab(self.ladder, "Ladder")
        self.tabs.addTab(self.book, "Book")

        # ── Order Entry tab ──
        self.order_entry = OrderEntryWidget()
        self.order_entry.order_place_requested.connect(self._on_order_place_requested)
        self.tabs.addTab(self.order_entry, "Order Entry")
        layout.addWidget(self.tabs, 1)

        outer.addWidget(self.body, 1)

        # Wire ladder click
        self.ladder.price_clicked.connect(self._on_ladder_price_click)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    # ── Header collapse toggle (D21.13) ──────────────────────────────────────

    def _on_header_toggled(self, checked: bool) -> None:
        """Hide/show the panel body from the header button (D21.13).

        ``checked`` is the visible state: unchecked -> body hidden + VIS-D21.1
        strike (auto-applied by :class:`DiagonalStrikeButton`); checked -> body
        shown + no strike.
        """
        visible = bool(checked)
        self._collapsed = not visible
        self.body.setVisible(visible)

    def is_collapsed(self) -> bool:
        """True while the panel body is hidden behind its header button."""
        return self._collapsed

    def set_collapsed(self, collapsed: bool) -> None:
        """Programmatically collapse/restore the body, syncing the button."""
        collapsed = bool(collapsed)
        self.header_button.setChecked(not collapsed)
        self._on_header_toggled(not collapsed)

    def toggle_collapsed(self) -> None:
        """Flip the collapsed state (convenience for callers/tests)."""
        self.set_collapsed(not self._collapsed)

    def _on_tab_changed(self, index: int):
        """Sync qty between header spinbox and order entry."""
        if self.tabs.widget(index) is self.order_entry:
            self.order_entry.setEnabled(True)

    @property
    def quantity(self) -> int:
        return self.qty_input.value()

    def set_symbol(self, symbol: str):
        self._symbol = symbol
        self.symbol_label.setText(symbol or "—")
        self.order_entry.set_symbol(symbol, self._last_price)
        self.order_entry.status_label.setText("Ready")

    def set_last_price(self, price: float | None):
        self._last_price = price
        self.ladder.set_last_price(price)
        if self._symbol:
            self.order_entry.set_symbol(self._symbol, price)

    def update_from_snapshot(self, snapshot: dict):
        self._snapshot = snapshot
        self._render()

    def set_order_status(self, order_id: int, action: str, qty: float, status: str):
        """Forward order status to the order-entry sub-widget."""
        self.order_entry.set_order_status(order_id, action, qty, status)

    def _render(self, *_args):
        snapshot = getattr(self, "_snapshot", None)
        if not snapshot:
            return
        cumulative = self.cumulative_check.isChecked()
        self.ladder.render(snapshot["asks"], snapshot["bids"], cumulative)
        self.book.render(snapshot["asks"], snapshot["bids"], cumulative)

    def clear(self):
        self.ladder.clear_all()
        self.book.setRowCount(0)
        self._snapshot = {}

    def _on_ladder_price_click(self, row: int, col: int, price: float):
        """Click-to-trade from the ladder: bid -> BUY LMT, ask -> SELL LMT."""
        self.tabs.setCurrentWidget(self.order_entry)
        self.order_entry.lmt_price_input.setText(f"{price:.2f}")
        self.order_entry.type_combo.setCurrentText("LMT")
        if col in (2, 3):
            self.order_entry.qty_input.setValue(self.qty_input.value())
            self._pending_ladder = ("BUY", price)
        elif col in (0, 1):
            self._pending_ladder = ("SELL", price)

    def _on_order_place_requested(self, action: str, qty: float, order_type: str,
                                   lmt_price: float, stop_price: float, target_price: float):
        """Forward the order request to the MainWindow."""
        self.order_place_requested.emit(
            self._symbol, action, qty, order_type, lmt_price, stop_price, target_price
        )


def on_depth_callback(panel, snapshot: dict):
    panel.update_from_snapshot(snapshot)
