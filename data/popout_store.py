"""data/popout_store.py — persistence for D24.9 pop-out window restore.

Additive ``popouts`` table: symbol, timeframe, mode, ext_hours, geometry JSON,
updated_at. Saved on pop-out open/close and on move/resize end (not per-pixel);
restored on launch after connect (lazy attach, cache-first render).
"""

from __future__ import annotations

import json
import time


class PopoutStore:
    @staticmethod
    def _columns() -> set[str]:
        from data.db import db

        cur = db.conn.execute("PRAGMA table_info(popouts)")
        return {row[1] for row in cur.fetchall()}

    @staticmethod
    def _ensure_tz_column() -> None:
        """D49.6 additive migration: nullable ``tz_offset`` column.

        Lives here (not ``data/db.py``) so the whole persist/restore half
        stays in this task's footprint. Idempotent: fresh and pre-change
        tables gain the column once; pre-change rows read back NULL, which
        ``load_all`` surfaces as ``None`` so restore can apply the A134
        fallback (main chart's current offset, never silent UTC).
        """
        from data.db import db

        if "tz_offset" not in PopoutStore._columns():
            db.conn.execute("ALTER TABLE popouts ADD COLUMN tz_offset REAL")
            db.conn.commit()

    @staticmethod
    def save(
        symbol: str,
        timeframe: str,
        mode: str,
        ext_hours: bool,
        geometry: dict,
        tz_offset: float | None = None,
    ) -> int:
        """Upsert a pop-out record; returns the row id.

        ``tz_offset`` is the main chart's current offset at save time
        (D49.6). ``None`` means "no offset supplied" — on an UPDATE the
        stored offset is preserved (the pre-offset ``attach`` /
        ``_save_geometry`` call sites pass none and must not clobber a
        stamped value back to NULL); on an INSERT the row stores NULL
        (pre-change shape).
        """
        from data.db import db

        PopoutStore._ensure_tz_column()
        now = int(time.time())
        geo_json = json.dumps(geometry)
        # One row per (symbol, timeframe, mode): reopening the same snapshot
        # updates the geometry instead of duplicating.
        cur = db.conn.execute(
            "SELECT id FROM popouts WHERE symbol=? AND timeframe=? AND mode=?",
            (symbol.upper(), timeframe, mode),
        )
        row = cur.fetchone()
        if row:
            if tz_offset is not None:
                db.conn.execute(
                    """UPDATE popouts SET ext_hours=?, geometry=?, updated_at=?,
                       tz_offset=? WHERE id=?""",
                    (1 if ext_hours else 0, geo_json, now, float(tz_offset),
                     row[0]),
                )
            else:
                db.conn.execute(
                    """UPDATE popouts SET ext_hours=?, geometry=?, updated_at=?
                       WHERE id=?""",
                    (1 if ext_hours else 0, geo_json, now, row[0]),
                )
            db.conn.commit()
            return row[0]
        cur = db.conn.execute(
            """INSERT INTO popouts
               (symbol, timeframe, mode, ext_hours, geometry, updated_at,
                tz_offset)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                symbol.upper(),
                timeframe,
                mode,
                1 if ext_hours else 0,
                geo_json,
                now,
                float(tz_offset) if tz_offset is not None else None,
            ),
        )
        db.conn.commit()
        return cur.lastrowid

    @staticmethod
    def delete(popout_id: int) -> None:
        from data.db import db

        db.conn.execute("DELETE FROM popouts WHERE id=?", (popout_id,))
        db.conn.commit()

    @staticmethod
    def load_all() -> list[dict]:
        """All saved pop-outs, most-recently-updated first.

        Pre-change rows (NULL ``tz_offset``) read back with
        ``record["tz_offset"] is None`` — the key is always present so
        restore can distinguish "no stored offset" from "stored UTC".
        """
        from data.db import db

        PopoutStore._ensure_tz_column()
        cur = db.conn.execute(
            """SELECT id, symbol, timeframe, mode, ext_hours, geometry,
                      updated_at, tz_offset
               FROM popouts ORDER BY updated_at DESC"""
        )
        out = []
        for row in cur.fetchall():
            try:
                geometry = json.loads(row[5]) if row[5] else {}
            except (json.JSONDecodeError, TypeError):
                geometry = {}
            out.append(
                {
                    "id": row[0],
                    "symbol": row[1],
                    "timeframe": row[2],
                    "mode": row[3],
                    "ext_hours": bool(row[4]),
                    "geometry": geometry,
                    "updated_at": row[6],
                    "tz_offset": float(row[7]) if row[7] is not None else None,
                }
            )
        return out

    @staticmethod
    def clear() -> None:
        from data.db import db

        db.conn.execute("DELETE FROM popouts")
        db.conn.commit()
