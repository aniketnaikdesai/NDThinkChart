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
    def save(
        symbol: str,
        timeframe: str,
        mode: str,
        ext_hours: bool,
        geometry: dict,
    ) -> int:
        """Upsert a pop-out record; returns the row id."""
        from data.db import db

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
            db.conn.execute(
                """UPDATE popouts SET ext_hours=?, geometry=?, updated_at=?
                   WHERE id=?""",
                (1 if ext_hours else 0, geo_json, now, row[0]),
            )
            db.conn.commit()
            return row[0]
        cur = db.conn.execute(
            """INSERT INTO popouts
               (symbol, timeframe, mode, ext_hours, geometry, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                symbol.upper(),
                timeframe,
                mode,
                1 if ext_hours else 0,
                geo_json,
                now,
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
        """All saved pop-outs, most-recently-updated first."""
        from data.db import db

        cur = db.conn.execute(
            """SELECT id, symbol, timeframe, mode, ext_hours, geometry,
                      updated_at
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
                }
            )
        return out

    @staticmethod
    def clear() -> None:
        from data.db import db

        db.conn.execute("DELETE FROM popouts")
        db.conn.commit()
