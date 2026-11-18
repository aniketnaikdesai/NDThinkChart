"""Option Spreads panel shell (D65 / S-P23-1).

The right dock's panel: a collapsed-able shell holding two four-row option-spread
tables (``CCS`` and ``PCS``), a Target field with its own validation gate
(S-P23-23 / AC-D65.17), and the red/green ON/OFF spread toggle.

This module is deliberately self-contained: it declares the panel's
``toggle_clicked`` / ``target_committed`` signals and exposes the members the
dock drives (``header_button`` — the dock's title-bar widget and collapse
control — ``body`` and :meth:`OptionSpreadsPanel.is_collapsed`) without wiring
any engine or window.  The signals receive their engine receivers in P23-09.

Sizing follows ``AC-D65.9``: the panel advertises :data:`PREFERRED_WIDTH` (360 px)
through :meth:`OptionSpreadsPanel.sizeHint`, while its horizontal size policy is
``Ignored`` so the dock model (``ui/dock_layout``) keeps the width clamp.  The
instrument-name column elides right with a trailing ellipsis and carries the
full name as its tooltip, so a narrow dock never hard-truncates a name into an
unreadable cell.
"""

from __future__ import annotations

import math

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.visual_conventions import DiagonalStrikeButton

#: Exact column headers of both spread tables, in rendering order (S-P23-1).
HEADERS = ("Financial instrument", "ASK", "BID", "Delta", "Gamma")

#: Width the panel asks the dock model for at launch (AC-D65.9 (i)).
PREFERRED_WIDTH = 360

#: Minimum rows both tables always show (the shell's four-row shape).
MIN_ROWS = 4

#: S-P23-23's Target gate: 0.05 <= T <= 19.95.
TARGET_MIN = 0.05
TARGET_MAX = 19.95

#: The field's default (and its last valid value until a commit succeeds).
DEFAULT_TARGET = 1.00

#: The one message a rejected Target edit leaves in the status label.
TARGET_RANGE_MESSAGE = (
    f"Target must be between {TARGET_MIN:.2f} and {TARGET_MAX:.2f}"
)

#: The two named toggle colours: red while off, green while on.
COLOUR_OFF = "#ef4444"
COLOUR_ON = "#22c55e"

#: Default empty-state text (shown while no rows have been applied).
DEFAULT_EMPTY_STATE = "No option spreads"

#: State-keyed toggle stylesheet — the ``spread_state`` dynamic property
#: selects the rule, so the rendered colour follows the state.
TOGGLE_STATE_STYLESHEET = (
    "QPushButton#SpreadStateToggle {\n"
    "    font-weight: 700;\n"
    "    padding: 1px 10px;\n"
    "    border-radius: 3px;\n"
    "}\n"
    'QPushButton#SpreadStateToggle[spread_state="off"] {\n'
    f"    color: {COLOUR_OFF};\n"
    f"    border: 1px solid {COLOUR_OFF};\n"
    "}\n"
    'QPushButton#SpreadStateToggle[spread_state="on"] {\n'
    f"    color: {COLOUR_ON};\n"
    f"    border: 1px solid {COLOUR_ON};\n"
    "}\n"
)


def _repolish(widget: QWidget) -> None:
    """Re-run the style sheet for *widget* so a property change renders."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class _ElideNameDelegate(QStyledItemDelegate):
    """Right-elides the instrument-name column with a trailing ellipsis."""

    def initStyleOption(self, option, index) -> None:  # noqa: N802 (Qt name)
        super().initStyleOption(option, index)
        option.textElideMode = Qt.TextElideMode.ElideRight


class OptionSpreadsPanel(QWidget):
    """The right dock's Option Spreads shell.

    Emits :attr:`toggle_clicked` when the user flips the spread toggle and
    :attr:`target_committed` exactly once per accepted Target edit; a rejected
    edit restores the last valid value and emits nothing.
    """

    #: ``AC-D65.9``: the launch/preferred width, owned by the panel.
    PREFERRED_WIDTH = PREFERRED_WIDTH

    #: The new spread-toggle state after a user click.
    toggle_clicked = pyqtSignal(bool)
    #: The accepted Target value (only emitted for 0.05 <= T <= 19.95).
    target_committed = pyqtSignal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed = False
        self._last_valid_target = float(DEFAULT_TARGET)
        self._empty_state_text = DEFAULT_EMPTY_STATE

        # The dock model keeps the width clamp; the panel itself never demands
        # width (AC-D65.9 / AC-D18.6).
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored, self.sizePolicy().verticalPolicy()
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header (D21.13 / D44 collapse contract) ──────────────────────────
        # The header is the dock's title-bar widget: checkable so it doubles as
        # the hide/show toggle, struck while the body is hidden.
        self.header_button = DiagonalStrikeButton("Option Spreads")
        self.header_button.setObjectName("OptionSpreadsHeaderButton")
        self.header_button.setCheckable(True)
        self.header_button.setChecked(True)
        self.header_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_button.setStyleSheet(
            "QPushButton#OptionSpreadsHeaderButton {"
            " background: transparent; border: none;"
            " color: #cbd5e1; font-weight: 600; text-align: left;"
            " padding: 4px 8px; }"
        )
        # Keep the palette in sync so the VIS-D21.1 strike uses the label colour.
        _pal = self.header_button.palette()
        _pal.setColor(QPalette.ColorRole.ButtonText, QColor("#cbd5e1"))
        self.header_button.setPalette(_pal)
        self.header_button.toggled.connect(self._on_header_toggled)
        outer.addWidget(self.header_button)

        # ── Body — the collapsible content ───────────────────────────────────
        self.body = QWidget()
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Controls row: Target field on the left, spread toggle on the right.
        self.controls_row = QWidget()
        controls = QHBoxLayout(self.controls_row)
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)

        self.target_label = QLabel("Target")
        self.target_edit = QLineEdit(f"{DEFAULT_TARGET:.2f}")
        self.target_edit.setObjectName("SpreadTargetField")
        self.target_edit.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.target_edit.setFixedWidth(70)
        self.target_edit.editingFinished.connect(self._commit_target)

        self.toggle_button = QPushButton("ON")
        self.toggle_button.setObjectName("SpreadStateToggle")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setStyleSheet(TOGGLE_STATE_STYLESHEET)
        self.toggle_button.toggled.connect(self._on_toggle_toggled)

        controls.addWidget(self.target_label)
        controls.addWidget(self.target_edit)
        controls.addStretch(1)
        controls.addWidget(self.toggle_button)
        layout.addWidget(self.controls_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("OptionSpreadsStatus")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #cbd5e1; font-weight: 600;")
        layout.addWidget(self.status_label)

        # Empty state — visible until a snapshot supplies rows.
        self.empty_label = QLabel(self._empty_state_text)
        self.empty_label.setObjectName("OptionSpreadsEmptyState")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #94a3b8; padding: 6px;")
        layout.addWidget(self.empty_label)

        # ── CCS then PCS, each over its own four-row table ───────────────────
        self.ccs_header = QLabel("CCS")
        self.ccs_header.setStyleSheet("color: #cbd5e1; font-weight: 700;")
        layout.addWidget(self.ccs_header)

        self._name_delegate = _ElideNameDelegate(self)
        self.ccs_table = self._build_table()
        layout.addWidget(self.ccs_table)

        self.pcs_header = QLabel("PCS")
        self.pcs_header.setStyleSheet("color: #cbd5e1; font-weight: 700;")
        layout.addWidget(self.pcs_header)

        self.pcs_table = self._build_table()
        layout.addWidget(self.pcs_table)

        outer.addWidget(self.body, 1)

        # Establish the default toggle state (property, colour, palette, text).
        self._apply_toggle_state(True)

    # ── Table construction ───────────────────────────────────────────────────

    def _build_table(self) -> QTableWidget:
        """A five-column, four-row read-only spread table with elided names."""
        table = QTableWidget(MIN_ROWS, len(HEADERS))
        table.setHorizontalHeaderLabels(list(HEADERS))
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        table.setMinimumWidth(0)
        table.setSizePolicy(
            QSizePolicy.Policy.Ignored, table.sizePolicy().verticalPolicy()
        )
        table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        # Never hard-truncate: right-elide with a trailing ellipsis (AC-D65.9).
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.setItemDelegateForColumn(0, self._name_delegate)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, len(HEADERS)):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        # The shell always shows its four rows, empty until a snapshot lands.
        for row in range(MIN_ROWS):
            for column in range(len(HEADERS)):
                table.setItem(row, column, self._table_item("", column))
        return table

    @staticmethod
    def _table_item(text: str, column: int) -> QTableWidgetItem:
        """A read-only cell; the name column carries the full text as tooltip."""
        item = QTableWidgetItem(str(text))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if column == 0:
            item.setToolTip(str(text))
        else:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
        return item

    # ── Snapshot application ────────────────────────────────────────────────

    def apply_snapshot(self, ccs_rows, pcs_rows) -> None:
        """Fill the two tables and drop the empty state once rows arrive.

        Each row may be any sequence matching :data:`HEADERS`; a bare string is
        treated as a lone instrument name so the shell is easy to exercise.
        Both tables always keep at least :data:`MIN_ROWS` rows.
        """
        ccs_rows = list(ccs_rows or [])
        pcs_rows = list(pcs_rows or [])
        self._populate(self.ccs_table, ccs_rows)
        self._populate(self.pcs_table, pcs_rows)
        if ccs_rows or pcs_rows:
            self.set_empty_state(None)
        else:
            self.set_empty_state(self._empty_state_text)

    def _populate(self, table: QTableWidget, rows: list) -> None:
        row_count = max(MIN_ROWS, len(rows))
        table.setRowCount(row_count)
        for row in range(row_count):
            cells = self._cells_for(rows[row]) if row < len(rows) else []
            for column in range(len(HEADERS)):
                text = cells[column] if column < len(cells) else ""
                table.setItem(row, column, self._table_item(text, column))

    @staticmethod
    def _cells_for(row) -> list:
        """Normalise one snapshot row to a flat list of cell values."""
        if row is None:
            return []
        if isinstance(row, bytes):
            return [row.decode(errors="replace")]
        if isinstance(row, str):
            return [row]
        try:
            return list(row)
        except TypeError:
            return [str(row)]

    def set_status(self, text: str | None) -> None:
        """Replace the status label's one-line message."""
        self.status_label.setText("" if text is None else str(text))

    def set_empty_state(self, text: str | None) -> None:
        """Show the empty-state label with *text*, or hide it when ``None``."""
        if text is None:
            self.empty_label.setVisible(False)
            return
        self._empty_state_text = str(text)
        self.empty_label.setText(self._empty_state_text)
        self.empty_label.setVisible(True)

    # ── Target field (S-P23-23 validation gate) ─────────────────────────────

    def set_target_value(self, value: float) -> None:
        """Set the Target programmatically, keeping the same gate (no emit)."""
        parsed = self._parse_target(str(value))
        if parsed is None:
            self._reject_target()
            return
        self._last_valid_target = parsed
        self.target_edit.setText(f"{parsed:.2f}")

    def _commit_target(self) -> None:
        """Validate one user commit: accept, or revert with one message."""
        parsed = self._parse_target(self.target_edit.text().strip())
        if parsed is None:
            self._reject_target()
            return
        self._last_valid_target = parsed
        self.target_edit.setText(f"{parsed:.2f}")
        self.target_committed.emit(parsed)

    @staticmethod
    def _parse_target(raw: str) -> float | None:
        """Return *raw* as a float iff 0.05 <= T <= 19.95, else ``None``."""
        if not raw:
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        if value < TARGET_MIN or value > TARGET_MAX:
            return None
        return value

    def _reject_target(self) -> None:
        """Restore the last valid value and leave exactly one message."""
        self.target_edit.setText(f"{self._last_valid_target:.2f}")
        self.set_status(TARGET_RANGE_MESSAGE)

    # ── Spread toggle (red off / green on) ──────────────────────────────────

    def set_toggle_state(self, on: bool) -> None:
        """Programmatically flip the toggle (property, colour, palette, text)."""
        self._apply_toggle_state(bool(on))

    def _apply_toggle_state(self, on: bool) -> None:
        on = bool(on)
        # Keep the check state in sync without echoing a second toggle_clicked.
        blocked = self.toggle_button.blockSignals(True)
        try:
            self.toggle_button.setChecked(on)
        finally:
            self.toggle_button.blockSignals(blocked)
        self.toggle_button.setText("ON" if on else "OFF")
        self.toggle_button.setProperty("spread_state", "on" if on else "off")
        colour = QColor(COLOUR_ON if on else COLOUR_OFF)
        palette = self.toggle_button.palette()
        palette.setColor(QPalette.ColorRole.ButtonText, colour)
        self.toggle_button.setPalette(palette)
        _repolish(self.toggle_button)

    def _on_toggle_toggled(self, checked: bool) -> None:
        self._apply_toggle_state(bool(checked))
        self.toggle_clicked.emit(bool(checked))

    # ── Collapse contract (D21.13 / D44) ────────────────────────────────────

    def _on_header_toggled(self, checked: bool) -> None:
        """Hide/show the body from the header button (checked == visible)."""
        visible = bool(checked)
        self._collapsed = not visible
        self.body.setVisible(visible)

    def is_collapsed(self) -> bool:
        """True while the body is hidden behind the header button."""
        return self._collapsed

    # ── Sizing ──────────────────────────────────────────────────────────────

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt name)
        hint = super().sizeHint()
        return QSize(PREFERRED_WIDTH, hint.height())
