"""
drawing_store.py
SQLite persistence for drawing_groups and drawings tables.
"""

import json
import time
from typing import Iterable, Optional

from data.db import db
from data.models import Drawing, DrawingGroup


class DrawingStore:

    # ── Groups ─────────────────────────────────────────────────────────────────

    @staticmethod
    def groups_for_symbol(symbol: str) -> list[DrawingGroup]:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            SELECT id, symbol, name, seq_number, color, visible, locked, created_at
            FROM drawing_groups WHERE symbol=? ORDER BY seq_number ASC
            """,
            (symbol,),
        )
        return [
            DrawingGroup(
                id=row[0],
                symbol=row[1],
                name=row[2],
                seq_number=row[3],
                color=row[4],
                visible=bool(row[5]),
                locked=bool(row[6]),
                created_at=row[7],
            )
            for row in cursor.fetchall()
        ]

    @staticmethod
    def next_group_seq(symbol: str) -> int:
        groups = DrawingStore.groups_for_symbol(symbol)
        return max((g.seq_number for g in groups), default=0) + 1

    @staticmethod
    def create_group(symbol: str, name: str, seq_number: int,
                     color: Optional[str] = None) -> int:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO drawing_groups (symbol, name, seq_number, color, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (symbol, name, seq_number, color, int(time.time())),
        )
        db.conn.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update_group(group_id: int, **fields) -> None:
        if not fields:
            return
        allowed = {"name", "color", "visible", "locked"}
        assigns = [f"{k}=?" for k in fields if k in allowed]
        if not assigns:
            return
        values = [int(v) if isinstance(v, bool) else v for v in fields.values()]
        cursor = db.conn.cursor()
        cursor.execute(
            f"UPDATE drawing_groups SET {', '.join(assigns)} WHERE id=?",
            [*values, group_id],
        )
        db.conn.commit()

    @staticmethod
    def delete_group(group_id: int) -> None:
        cursor = db.conn.cursor()
        cursor.execute("UPDATE drawings SET group_id=NULL WHERE group_id=?", (group_id,))
        cursor.execute("DELETE FROM drawing_groups WHERE id=?", (group_id,))
        db.conn.commit()

    # ── Drawings ───────────────────────────────────────────────────────────────

    @staticmethod
    def drawings_for_symbol(symbol: str) -> list[Drawing]:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            SELECT id, symbol, kind, payload, color, label, group_id
            FROM drawings WHERE symbol=? ORDER BY id ASC
            """,
            (symbol,),
        )
        drawings = []
        for row in cursor.fetchall():
            try:
                payload = json.loads(row[3])
            except (TypeError, json.JSONDecodeError):
                payload = {}
            drawings.append(Drawing(
                id=row[0],
                symbol=row[1],
                kind=row[2],
                payload=payload,
                color=row[4],
                label=row[5] or "",
                group_id=row[6],
            ))
        return drawings

    @staticmethod
    def create_drawing(drawing: Drawing) -> int:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO drawings (symbol, kind, payload, color, label, group_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                drawing.symbol,
                drawing.kind,
                json.dumps(drawing.payload),
                drawing.color,
                drawing.label,
                drawing.group_id,
            ),
        )
        db.conn.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update_drawing(drawing_id: int, payload: dict) -> None:
        cursor = db.conn.cursor()
        cursor.execute(
            "UPDATE drawings SET payload=? WHERE id=?",
            (json.dumps(payload), drawing_id),
        )
        db.conn.commit()

    @staticmethod
    def delete_drawing(drawing_id: int) -> None:
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM drawings WHERE id=?", (drawing_id,))
        db.conn.commit()

    @staticmethod
    def delete_drawings(drawing_ids: Iterable[int]) -> None:
        ids = list(drawing_ids)
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        cursor = db.conn.cursor()
        cursor.execute(f"DELETE FROM drawings WHERE id IN ({placeholders})", ids)
        db.conn.commit()

    @staticmethod
    def assign_groups(drawing_ids: Iterable[int], group_id: Optional[int]) -> None:
        ids = list(drawing_ids)
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        cursor = db.conn.cursor()
        cursor.execute(
            f"UPDATE drawings SET group_id=? WHERE id IN ({placeholders})",
            [group_id, *ids],
        )
        db.conn.commit()