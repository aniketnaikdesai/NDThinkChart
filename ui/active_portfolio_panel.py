"""
active_portfolio_panel.py
Phase 6: Active Portfolio panel — account summary + positions table with
automatic option-strategy grouping.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from data.models import Position
from services.strategy_detection import detect_and_group
from ui.stop_loss_target_dialog import StopLossTargetDialog
from ui.trade_context_menu import TradeContextMenu
from ui.visual_conventions import DiagonalStrikeButton

import ui.dock_layout as dock_layout

#: Bounded minimum width of this panel (D18 Phase 4). Shared with the right
#: region so the 10-column positions table can never demand more width than the
#: region is allowed and push it off-screen (AC-D18.6).
RIGHT_DOCK_MIN_WIDTH = dock_layout.RIGHT_DOCK_MIN_WIDTH


class ActivePortfolioPanel(QWidget):
    """Renders account summary and positions; auto-groups option legs."""

    account_summary_changed = pyqtSignal(dict)
    positions_changed = pyqtSignal(list)
    # Emitted when SL/TP is set for a position: (position_id, stop_loss, take_profit)
    position_sltp_changed = pyqtSignal(int, float, float)
    # Emitted when SL/TP is set for a group: (group_id, stop_loss, take_profit)
    group_sltp_changed = pyqtSignal(int, float, float)
    # Emitted when position should be closed: (position_id,)
    position_close_requested = pyqtSignal(int)
    # Emitted when group should be closed: (group_id,)
    group_close_requested = pyqtSignal(int)
    # Emitted when all positions should be flattened
    flatten_all_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._summary: dict[str, str] = {}
        self._positions: list[Position] = []
        self._groups: dict[int, str] = {}
        self._collapsed = False

        # D18 Phase 4: bound the panel so its 10-column positions table scrolls or
        # clips internally rather than forcing the right region past the 40% cap
        # (AC-D18.6).
        self.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored, self.sizePolicy().verticalPolicy()
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header (D21.13) — the "Account Summary" toggle button ─────────────
        # ``summary_label`` is the panel's hide/show control: a
        # ``DiagonalStrikeButton`` that hides the body below (the account detail
        # + positions table) while the button itself stays visible, struck while
        # hidden (AC-D21.13.1/AC-D21.13.4).
        self.summary_label = DiagonalStrikeButton("Account Summary")
        self.summary_label.setObjectName("AccountSummaryHeaderButton")
        # Checked == shown/unstruck; unchecked == hidden/struck.
        self.summary_label.setCheckable(True)
        self.summary_label.setChecked(True)
        self.summary_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.summary_label.setStyleSheet(
            "QPushButton#AccountSummaryHeaderButton {"
            " background: transparent; border: none;"
            " color: #cbd5e1; font-weight: 600; text-align: left;"
            " padding: 4px 8px; }"
        )
        # Keep the palette in sync so the VIS-D21.1 strike uses the label colour.
        _pal = self.summary_label.palette()
        _pal.setColor(QPalette.ColorRole.ButtonText, QColor("#cbd5e1"))
        self.summary_label.setPalette(_pal)
        self.summary_label.toggled.connect(self._on_header_toggled)
        outer.addWidget(self.summary_label)

        # ── Body — the collapsible content (D21.13) ───────────────────────────
        self.body = QWidget()
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(6, 6, 6, 6)

        # The dynamic account values live in the body (the button keeps the
        # static "Account Summary" label).
        self.account_detail = QLabel("Account summary — disconnected")
        self.account_detail.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        layout.addWidget(self.account_detail)

        # 10 columns: Symbol, Qty, Avg Price, Type, Multiplier, P/L, SL, TP, Strategy, Group
        self.positions_table = QTableWidget(0, 10)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol",
            "Qty",
            "Avg Price",
            "Type",
            "Multiplier",
            "P/L",
            "Stop",
            "Target",
            "Strategy",
            "Group",
        ])
        self.positions_table.verticalHeader().setVisible(False)
        self.positions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.positions_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.positions_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # D18 Phase 4: the table itself must not demand the sum of its column
        # widths; Stretch columns fill the available region width and the table
        # scrolls horizontally if it ever needs to (AC-D18.6).
        self.positions_table.setMinimumWidth(0)
        self.positions_table.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            self.positions_table.sizePolicy().verticalPolicy(),
        )
        self.positions_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.positions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.positions_table.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.positions_table)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)

        outer.addWidget(self.body, 1)

        # Context menu
        self._context_menu = TradeContextMenu(self)
        self._context_menu.set_sltp_action.triggered.connect(self._on_set_sltp)
        self._context_menu.close_position_action.triggered.connect(self._on_close_position)
        self._context_menu.close_group_action.triggered.connect(self._on_close_group)
        self._context_menu.ungroup_action.triggered.connect(self._on_ungroup)
        self._context_menu.flatten_all_action.triggered.connect(self._on_flatten_all)

        # Selected row tracking
        self._selected_row = -1
        self._selected_position: Position | None = None
        self.positions_table.itemSelectionChanged.connect(self._on_selection_changed)

        # SL/TP dialog
        self._sltp_dialog = None

    # ── Header collapse toggle (D21.13) ──────────────────────────────────────

    def _on_header_toggled(self, checked: bool) -> None:
        """Hide/show the panel body from the "Account Summary" button (D21.13).

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
        self.summary_label.setChecked(not collapsed)
        self._on_header_toggled(not collapsed)

    def toggle_collapsed(self) -> None:
        """Flip the collapsed state (convenience for callers/tests)."""
        self.set_collapsed(not self._collapsed)

    def set_account_summary(self, summary: dict[str, str]) -> None:
        """Apply account summary key/value pairs."""
        self._summary = dict(summary)
        self._render_summary()
        self.account_summary_changed.emit(self._summary)

    def set_positions(self, positions: list[Position]) -> None:
        """Replace positions and re-render."""
        self._positions = list(positions)
        self._group_and_render()
        self.positions_changed.emit(self._positions)

    def add_position(self, position: Position) -> None:
        """Upsert a single position."""
        existing = next((p for p in self._positions if p.con_id == position.con_id), None)
        if existing is not None:
            self._positions.remove(existing)
        self._positions.append(position)
        self._group_and_render()
        self.positions_changed.emit(self._positions)

    def update_position_sltp(self, position_id: int, stop_loss: float, take_profit: float) -> None:
        """Update SL/TP for a position after dialog confirmation."""
        for pos in self._positions:
            if pos.id == position_id:
                if stop_loss > 0:
                    pos.stop_loss = stop_loss
                if take_profit > 0:
                    pos.take_profit = take_profit
                self._group_and_render()
                self.positions_changed.emit(self._positions)
                self.position_sltp_changed.emit(position_id, pos.stop_loss or 0.0, pos.take_profit or 0.0)
                break

    def update_group_sltp(self, group_id: int, stop_loss: float, take_profit: float) -> None:
        """Update SL/TP for all positions in a group."""
        updated = False
        for pos in self._positions:
            if pos.trade_group_id == group_id:
                if stop_loss > 0:
                    pos.stop_loss = stop_loss
                if take_profit > 0:
                    pos.take_profit = take_profit
                updated = True
        if updated:
            self._group_and_render()
            self.positions_changed.emit(self._positions)
            self.group_sltp_changed.emit(group_id, stop_loss, take_profit)

    def refresh(self) -> None:
        """Re-render current state (called after external changes)."""
        self._render_summary()
        self._group_and_render()

    def _render_summary(self) -> None:
        if not self._summary:
            self.account_detail.setText("Account summary — disconnected")
            return
        account = self._summary.get("Account", "—")
        net_liq = self._summary.get("NetLiquidation", "—")
        cash = self._summary.get("TotalCashValue", "—")
        self.account_detail.setText(
            f"Account: {account}  |  Net Liq: {net_liq}  |  Cash: {cash}"
        )

    def _group_and_render(self) -> None:
        """Detect strategy per option cluster and render the table."""
        option_positions = [p for p in self._positions if p.contract_type == "option"]
        strategy_by_id: dict[int, str] = {}
        group_by_id: dict[int, str] = {}

        # Group by expiry first so detection only sees same-expiry legs.
        by_expiry: dict[str, list[Position]] = {}
        for pos in option_positions:
            by_expiry.setdefault(pos.expiry or "", []).append(pos)

        for expiry, legs in by_expiry.items():
            strategy, indices = detect_and_group(legs)
            if strategy == "CUSTOM":
                continue
            group_name = f"{strategy} {expiry or ''}".strip()
            for idx in indices:
                leg = legs[idx]
                if leg.id is None:
                    continue
                strategy_by_id[leg.id] = strategy
                group_by_id[leg.id] = group_name

        self._groups = group_by_id
        self._render_table(strategy_by_id)

    def _render_table(self, strategy_by_id: dict[int, str]) -> None:
        self.positions_table.setRowCount(len(self._positions))
        for row, pos in enumerate(self._positions):
            pnl = self._unrealized_pnl(pos)
            values = [
                pos.symbol,
                f"{pos.qty:,.2f}",
                f"{pos.avg_cost:,.2f}",
                pos.contract_type.upper(),
                f"{pos.multiplier:g}",
                f"{pnl:,.2f}",
                f"{pos.stop_loss:,.2f}" if pos.stop_loss is not None else "—",
                f"{pos.take_profit:,.2f}" if pos.take_profit is not None else "—",
                strategy_by_id.get(pos.id, "—"),
                self._groups.get(pos.id, "—"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight if col in (1, 2, 4, 5, 6, 7) else Qt.AlignmentFlag.AlignLeft)
                self.positions_table.setItem(row, col, item)

    def _on_selection_changed(self) -> None:
        """Track selected row and update context menu availability."""
        selected = self.positions_table.selectedItems()
        if not selected:
            self._selected_row = -1
            self._selected_position = None
            self._context_menu.set_actions_enabled(False)
            return
        row = selected[0].row()
        if 0 <= row < len(self._positions):
            self._selected_row = row
            self._selected_position = self._positions[row]
            self._context_menu.set_actions_enabled(True)
        else:
            self._selected_row = -1
            self._selected_position = None
            self._context_menu.set_actions_enabled(False)

    def _show_context_menu(self, pos) -> None:
        """Show context menu at cursor position if a valid row is selected."""
        if self._selected_position is not None:
            self._context_menu.exec(self.positions_table.mapToGlobal(pos))

    def _on_set_sltp(self) -> None:
        """Open SL/TP dialog for selected position."""
        if self._selected_position is None:
            return
        pos = self._selected_position
        if pos.id is None:
            return
        self._sltp_dialog = StopLossTargetDialog(
            symbol=pos.symbol,
            market_price=getattr(pos, "market_price", 0.0) or pos.avg_cost,
            parent=self,
        )
        self._sltp_dialog.confirmed.connect(self._on_sltp_confirmed)
        self._sltp_dialog.set_target_info("position", pos.id, pos.symbol)
        self._sltp_dialog.exec()

    def _on_sltp_confirmed(self, apply_type: str, target_id: int, stop_price: float, target_price: float) -> None:
        """Handle SL/TP dialog confirmation."""
        if apply_type == "position":
            self.update_position_sltp(target_id, stop_price, target_price)
        elif apply_type == "group":
            self.update_group_sltp(target_id, stop_price, target_price)

    def _on_close_position(self) -> None:
        """Emit signal to close the selected position."""
        if self._selected_position is not None and self._selected_position.id is not None:
            self.position_close_requested.emit(self._selected_position.id)

    def _on_close_group(self) -> None:
        """Emit signal to close the selected position's group."""
        if self._selected_position is not None and self._selected_position.trade_group_id is not None:
            self.group_close_requested.emit(self._selected_position.trade_group_id)

    def _on_ungroup(self) -> None:
        """Remove the selected position from its trade group."""
        if self._selected_position is not None:
            self._selected_position.trade_group_id = None
            self._group_and_render()
            self.positions_changed.emit(self._positions)

    def _on_flatten_all(self) -> None:
        """Emit signal to close all positions."""
        self.flatten_all_requested.emit()

    @staticmethod
    def _unrealized_pnl(position: Position) -> float:
        """Compute P/L when market price is available."""
        if not hasattr(position, "market_price") or position.market_price in (None, 0):
            return 0.0
        return (position.market_price - position.avg_cost) * position.qty * position.multiplier