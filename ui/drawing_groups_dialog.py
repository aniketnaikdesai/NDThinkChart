"""
drawing_groups_dialog.py
Manages drawing groups for the current symbol: create, rename, recolor,
lock, show/hide, bulk assign/unassign/delete drawings. Mutations persist
immediately through DrawingStore and emit `changed` so the overlay reloads.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QInputDialog, QPushButton, QColorDialog,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QAbstractItemView,
    QListWidget, QListWidgetItem, QLabel, QMessageBox,
)
from PyQt6.QtGui import QColor

from data.drawing_store import DrawingStore
from services.drawing_service import auto_group_name, drawing_summary


class DrawingGroupsDialog(QDialog):
    changed = pyqtSignal()

    PRECOLORS = [
        "#38bdf8", "#f472b6", "#a78bfa", "#34d399",
        "#fbbf24", "#fb7185", "#60a5fa", "#c084fc",
    ]

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Drawing Sets — {symbol}")
        self.resize(580, 620)
        self._symbol = symbol

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Drawing groups"))
        self.groups_table = QTableWidget(0, 4)
        self.groups_table.setHorizontalHeaderLabels(["Name", "Color", "Visible", "Locked"])
        self.groups_table.horizontalHeader().setStretchLastSection(True)
        self.groups_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.groups_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.groups_table.itemChanged.connect(self._on_group_item_changed)
        layout.addWidget(self.groups_table)

        group_btns = QHBoxLayout()
        self.new_group_btn = QPushButton("New Group")
        self.rename_btn = QPushButton("Rename")
        self.recolor_btn = QPushButton("Recolor")
        self.delete_group_btn = QPushButton("Delete Group")
        for btn in (self.new_group_btn, self.rename_btn, self.recolor_btn, self.delete_group_btn):
            group_btns.addWidget(btn)
        self.new_group_btn.clicked.connect(self._new_group)
        self.rename_btn.clicked.connect(self._rename_group)
        self.recolor_btn.clicked.connect(self._recolor_group)
        self.delete_group_btn.clicked.connect(self._delete_group)
        layout.addLayout(group_btns)

        layout.addWidget(QLabel("Drawings"))
        self.drawings_list = QListWidget()
        self.drawings_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.drawings_list)

        assign_row = QHBoxLayout()
        self.group_combo = QComboBox()
        self.assign_btn = QPushButton("Assign")
        self.ungroup_btn = QPushButton("Ungroup")
        self.delete_drawings_btn = QPushButton("Delete Selected")
        assign_row.addWidget(QLabel("Assign to:"))
        assign_row.addWidget(self.group_combo, 1)
        assign_row.addWidget(self.assign_btn)
        assign_row.addWidget(self.ungroup_btn)
        assign_row.addWidget(self.delete_drawings_btn)
        self.assign_btn.clicked.connect(self._assign_selected)
        self.ungroup_btn.clicked.connect(self._ungroup_selected)
        self.delete_drawings_btn.clicked.connect(self._delete_selected_drawings)
        layout.addLayout(assign_row)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

        self.reload()

    # ── Data reload ───────────────────────────────────────────────────────────

    def _groups(self):
        return DrawingStore.groups_for_symbol(self._symbol)

    def _drawings(self):
        return DrawingStore.drawings_for_symbol(self._symbol)

    def reload(self):
        groups = self._groups()
        drawings = self._drawings()

        self.groups_table.blockSignals(True)
        self.groups_table.setRowCount(len(groups))
        for r, group in enumerate(groups):
            name_item = QTableWidgetItem(group.name)
            name_item.setData(Qt.ItemDataRole.UserRole, group.id)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            color_item = QTableWidgetItem()
            while len(self.PRECOLORS) < 8:
                self.PRECOLORS.append("#ffffff")
            color_item.setData(
                Qt.ItemDataRole.BackgroundRole,
                QColor(group.color or "#888888"),
            )
            color_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            visible_item = QTableWidgetItem()
            visible_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            visible_item.setCheckState(
                Qt.CheckState.Checked if group.visible else Qt.CheckState.Unchecked
            )
            visible_item.setData(Qt.ItemDataRole.UserRole, ("visible", group.id))
            locked_item = QTableWidgetItem()
            locked_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            locked_item.setCheckState(
                Qt.CheckState.Checked if group.locked else Qt.CheckState.Unchecked
            )
            locked_item.setData(Qt.ItemDataRole.UserRole, ("locked", group.id))
            self.groups_table.setItem(r, 0, name_item)
            self.groups_table.setItem(r, 1, color_item)
            self.groups_table.setItem(r, 2, visible_item)
            self.groups_table.setItem(r, 3, locked_item)
        self.groups_table.blockSignals(False)

        group_by_id = {g.id: g for g in groups}
        self.drawings_list.clear()
        for drawing in drawings:
            label = drawing_summary(drawing)
            group = group_by_id.get(drawing.group_id)
            prefix = f"[{group.name}] " if group else "(ungrouped) "
            item = QListWidgetItem(f"{prefix}{label}")
            item.setData(Qt.ItemDataRole.UserRole, drawing.id)
            self.drawings_list.addItem(item)

        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        self.group_combo.addItem("— Ungrouped —", None)
        for group in groups:
            self.group_combo.addItem(group.name, group.id)
        self.group_combo.blockSignals(False)

    def _selected_group_ids(self) -> list[int]:
        rows = self.groups_table.selectionModel().selectedRows()
        ids = []
        for index in rows:
            item = self.groups_table.item(index.row(), 0)
            gid = item.data(Qt.ItemDataRole.UserRole) if item else None
            if gid is not None:
                ids.append(gid)
        return ids

    def _selected_drawing_ids(self) -> list[int]:
        ids = []
        for item in self.drawings_list.selectedItems():
            gid = item.data(Qt.ItemDataRole.UserRole)
            if gid is not None:
                ids.append(gid)
        return ids

    # ── Group actions ─────────────────────────────────────────────────────────

    def _new_group(self):
        seq = DrawingStore.next_group_seq(self._symbol)
        color = self.PRECOLORS[(seq - 1) % len(self.PRECOLORS)]
        DrawingStore.create_group(self._symbol, auto_group_name(seq), seq, color)
        self._commit()

    def _rename_group(self):
        ids = self._selected_group_ids()
        if not ids:
            return
        name, ok = QInputDialog.getText(self, "Rename group", "Name:")
        if ok and name.strip():
            DrawingStore.update_group(ids[0], name=name.strip())
            self._commit()

    def _recolor_group(self):
        ids = self._selected_group_ids()
        if not ids:
            return
        group = next((g for g in self._groups() if g.id == ids[0]), None)
        if group is None:
            return
        color = QColorDialog.getColor(QColor(group.color or "#888888"), self, "Group color")
        if color.isValid():
            new_color = color.name()
            DrawingStore.update_group(ids[0], color=new_color)
            DrawingStore.repaint_group_members(ids[0], new_color)
            self._commit()

    def _delete_group(self):
        ids = self._selected_group_ids()
        if not ids:
            return
        ret = QMessageBox.question(
            self, "Delete group",
            "Drawings stay on the chart but become ungrouped. Continue?",
        )
        if ret == QMessageBox.StandardButton.Yes:
            DrawingStore.delete_group(ids[0])
            self._commit()

    # ── Drawing actions ───────────────────────────────────────────────────────

    def _assign_selected(self):
        ids = self._selected_drawing_ids()
        if not ids:
            return
        DrawingStore.assign_groups(ids, self.group_combo.currentData())
        self._commit()

    def _ungroup_selected(self):
        ids = self._selected_drawing_ids()
        if ids:
            DrawingStore.assign_groups(ids, None)
            self._commit()

    def _delete_selected_drawings(self):
        ids = self._selected_drawing_ids()
        if ids:
            DrawingStore.delete_drawings(ids)
            self._commit()

    # ── Table checkbox toggles ────────────────────────────────────────────────

    def _on_group_item_changed(self, item: QTableWidgetItem):
        if item.data(Qt.ItemDataRole.UserRole) is None:
            return
        field, group_id = item.data(Qt.ItemDataRole.UserRole)
        value = item.checkState() == Qt.CheckState.Checked
        DrawingStore.update_group(group_id, **{field: value})
        self.reload()
        self.changed.emit()

    def _commit(self):
        self.reload()
        self.changed.emit()