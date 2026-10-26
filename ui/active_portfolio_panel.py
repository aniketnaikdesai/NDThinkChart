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
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from data.models import Position
from services.strategy_detection import detect_and_group
from ui.visual_conventions import DiagonalStrikeButton

import ui.dock_layout as dock_layout

#: Bounded minimum width of this panel (D18 Phase 4). Shared with the right
#: region so the positions table can never demand more width than the region is
#: allowed and push it off-screen (AC-D18.6).
RIGHT_DOCK_MIN_WIDTH = dock_layout.RIGHT_DOCK_MIN_WIDTH


class ActivePortfolioPanel(QWidget):
    """Renders account summary and positions; auto-groups option legs."""

    account_summary_changed = pyqtSignal(dict)
    positions_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._summary: dict[str, str] = {}
        # ESC-045: the account id IBKR delivers as the reqAccountSummary
        # CALLBACK argument (never a summary tag), kept so the Account field
        # can show it even when no 'Account' key is present in the summary.
        self._account_id: str | None = None
        # D27.6: True when no account subscription is live — the panel then
        # shows the "unavailable" state instead of stale/empty values.
        self._account_unavailable: bool = False
        self._positions: list[Position] = []
        self._groups: dict[int, str] = {}
        self._collapsed = False

        # D18 Phase 4: bound the panel so its positions table scrolls or clips
        # internally rather than forcing the right region past the 40% cap
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

        # 8 columns: Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group
        self.positions_table = QTableWidget(0, 8)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol",
            "Qty",
            "Avg Price",
            "Type",
            "Multiplier",
            "P/L",
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
        layout.addWidget(self.positions_table)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)

        outer.addWidget(self.body, 1)

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

    def set_account_id(self, account_id: str | None) -> None:
        """ESC-045: record the subscribed account id for the Account field.

        IBKR delivers the account id as the ``reqAccountSummary`` callback
        argument, not as a summary tag, so ``_summary`` never carries an
        ``'Account'`` key. Storing it here lets ``_render_summary`` show the
        same id the connection badge uses; ``None``/empty means genuinely
        unknown and keeps the ``—`` fallback (no fabrication).
        """
        self._account_id = account_id or None
        self._render_summary()

    def set_account_unavailable(self, unavailable: bool) -> None:
        """D27.6: show/hide the 'account data unavailable' state."""
        self._account_unavailable = bool(unavailable)
        self._render_summary()

    def set_positions(self, positions: list[Position]) -> None:
        """Replace positions and re-render.

        ESC-053 (owner decision: "Hide qty==0 positions"): a flat position
        (``qty == 0``) is a real broker holding at flat size, but it must not be
        rendered. It is dropped from the panel's held list here — rather than
        filtered only at paint time — so the rendered rows stay index-aligned
        with ``self._positions``.
        """
        self._positions = [p for p in positions if p.qty != 0]
        self._group_and_render()
        self.positions_changed.emit(self._positions)

    def add_position(self, position: Position) -> None:
        """Upsert a single position.

        ESC-053: a flat (``qty == 0``) add is not rendered, and an update that
        flattens an existing holding removes it from the panel's list, keeping
        the same row/list alignment ``set_positions`` maintains.
        """
        existing = next((p for p in self._positions if p.con_id == position.con_id), None)
        if existing is not None:
            self._positions.remove(existing)
        if position.qty != 0:
            self._positions.append(position)
        self._group_and_render()
        self.positions_changed.emit(self._positions)

    def refresh(self) -> None:
        """Re-render current state (called after external changes)."""
        self._render_summary()
        self._group_and_render()

    def _render_summary(self) -> None:
        # D27.6: unsubscribed beats everything — never show stale values
        # as if they were live.
        if self._account_unavailable:
            self.account_detail.setText(
                "Account data unavailable — not subscribed")
            return
        if not self._summary:
            self.account_detail.setText("Account summary — disconnected")
            return
        # ESC-045: prefer an explicit 'Account' summary key when one is ever
        # present, then the subscribed id from the callback argument, and only
        # fall back to '—' when the account is genuinely unknown.
        account = self._summary.get("Account") or self._account_id or "—"
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
        # ESC-053: ``self._positions`` already excludes flat (qty == 0) rows
        # (see ``set_positions``/``add_position``), so the rendered rows remain
        # one-to-one with the panel's position list.
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
                strategy_by_id.get(pos.id, "—"),
                self._groups.get(pos.id, "—"),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight if col in (1, 2, 4, 5) else Qt.AlignmentFlag.AlignLeft)
                self.positions_table.setItem(row, col, item)

    @staticmethod
    def _unrealized_pnl(position: Position) -> float:
        """Compute P/L when market price is available."""
        if not hasattr(position, "market_price") or position.market_price in (None, 0):
            return 0.0
        return (position.market_price - position.avg_cost) * position.qty * position.multiplier