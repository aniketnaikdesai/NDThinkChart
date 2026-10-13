"""Persistent footprint cache (D36, plan item 36.4).

One compressed JSON blob per (resolved contract, date, timeframe):
``{bar_ts: {level: [bidVol, askVol, tradeVol, tradeCount]}}``.

Cache-key rule (C36.3, binding everywhere): keys use the RESOLVED contract
(e.g. ``ESZ6``), never the continuous symbol — after a quarterly roll the
old entries remain valid history but are never read for the new front month.

Owner decision 2026-10-13: only SPX, SPY, QQQ, ES-front-month and NQ-front-
month are cached across restarts. Every other symbol re-fetches per session
(in-memory only — the service keeps those buckets in RAM, never here).

The cache is read before any paginated backfill and written on backfill
completion. A cache hit means zero IBKR requests for that symbol+date.
"""

from __future__ import annotations

import json
import sqlite3
import zlib

# Owner decision 2026-10-13: the only symbols whose footprint data persists
# across restarts. ES/NQ mean the front-month contract (resolved dynamically).
CACHEABLE_SYMBOLS = frozenset({"SPX", "SPY", "QQQ", "ES", "NQ"})


def is_cacheable(symbol: str) -> bool:
    """True only for the five owner-approved symbols (case-insensitive)."""
    return symbol.split()[0].upper() in CACHEABLE_SYMBOLS


class FootprintCache:
    """Thin wrapper over the ``footprint_cache`` SQLite table.

    ``conn`` is a sqlite3 connection (the app passes ``db.conn``; tests pass
    an in-memory connection). All values are JSON-serialisable; floats stay
    floats, ints stay ints.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    @staticmethod
    def _encode(data: dict) -> bytes:
        payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
        return zlib.compress(payload, 9)

    @staticmethod
    def _decode(blob: bytes) -> dict:
        raw = json.loads(zlib.decompress(blob).decode("utf-8"))
        # JSON object keys are strings; restore numeric bar/level keys.
        out: dict[int, dict[float, list]] = {}
        for bar_ts, levels in raw.items():
            out[int(bar_ts)] = {
                float(level): list(vals) for level, vals in levels.items()
            }
        return out

    def get(self, resolved_contract: str, date: str, timeframe: str) -> dict | None:
        """Return the cached footprint blob, or None on a miss."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT blob FROM footprint_cache "
            "WHERE resolved_contract = ? AND date = ? AND timeframe = ?",
            (resolved_contract, date, timeframe),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._decode(row[0])

    def put(
        self,
        resolved_contract: str,
        date: str,
        timeframe: str,
        data: dict,
    ) -> None:
        """Write (or replace) one blob. Commits immediately."""
        self._conn.execute(
            "INSERT OR REPLACE INTO footprint_cache "
            "(resolved_contract, date, timeframe, blob) VALUES (?, ?, ?, ?)",
            (resolved_contract, date, timeframe, self._encode(data)),
        )
        self._conn.commit()

    def has(self, resolved_contract: str, date: str, timeframe: str) -> bool:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT 1 FROM footprint_cache "
            "WHERE resolved_contract = ? AND date = ? AND timeframe = ?",
            (resolved_contract, date, timeframe),
        )
        return cur.fetchone() is not None
