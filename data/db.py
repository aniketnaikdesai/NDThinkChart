"""SQLite schema and the app's single connection.

``yfinance_events_cache`` is retained but **unused**: the D38 corporate-event
feature was its only reader and has been removed. The table is left in place
deliberately — a stale table is cheaper than a schema change — so nothing
reads or writes it any more.
"""

import sqlite3
from config import paths


class DB:
    def __init__(self):
        # ESC-043 limb 2: refuse to open the owner's user-space production DB
        # from a process that has not opted in as the real application. With
        # DB_PATH unset, paths.get_db_path() resolves to the user-space
        # production DB (~/Library/Application Support/NDThinkChart/...); only
        # main.py opts in. A forgotten DB_PATH in an offscreen/REPL probe fails
        # loudly here -- before sqlite3.connect -- instead of writing the
        # owner's real database (architecture S12).
        if paths.uses_production_db() and not paths.is_production_db_opted_in():
            raise RuntimeError(
                "Refusing to open the user-space production database "
                f"({paths.production_db_path()}) because DB_PATH is unset and "
                "this process has not opted in as the real application. "
                "Non-app processes (offscreen probes, REPL, scripts) must "
                "export DB_PATH to a temp file before importing the app; the "
                "real app opts in via config.paths.opt_in_production_db() "
                "(called from main.py)."
            )
        # Use paths.get_db_path() for production (user-space) and dev (local)
        self.db_path = paths.get_db_path()
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=True)
        self._init_schema()

    def _init_schema(self):
        schema = """
        -- D42 / S16: mode-aware bars key. ext_hours (0/1) is part of the
        -- primary key so an RTH load can never read ETH bars as coverage
        -- (AC-D16.9 / AC-D16.8's mode-isolation clause). Default 1 matches
        -- the app default (Ext Hours ON).
        CREATE TABLE IF NOT EXISTS bars (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ext_hours INTEGER NOT NULL DEFAULT 1,
            ts INTEGER NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume REAL,
            PRIMARY KEY (symbol, timeframe, ext_hours, ts)
        );
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            sort_order INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            direction TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            triggered INTEGER NOT NULL DEFAULT 0,
            triggered_at INTEGER,
            sound INTEGER NOT NULL DEFAULT 1,
            note TEXT
        );
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price_low REAL NOT NULL,
            price_high REAL NOT NULL,
            kind TEXT NOT NULL,
            label TEXT,
            color TEXT,
            visible INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS drawing_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            seq_number INTEGER NOT NULL,
            color TEXT,
            visible INTEGER NOT NULL DEFAULT 1,
            locked INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL,
            color TEXT,
            label TEXT,
            group_id INTEGER REFERENCES drawing_groups(id)
        );
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            type TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            params TEXT NOT NULL
        );
        -- D24.9: pop-out window persistence (additive; restored on launch).
        CREATE TABLE IF NOT EXISTS popouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            mode TEXT NOT NULL,
            ext_hours INTEGER NOT NULL DEFAULT 1,
            geometry TEXT NOT NULL DEFAULT '{}',
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            account TEXT NOT NULL,
            con_id INTEGER,
            contract_type TEXT NOT NULL,
            qty REAL NOT NULL,
            avg_cost REAL,
            local_symbol TEXT,
            multiplier REAL DEFAULT 1,
            expiry TEXT,
            strike REAL,
            right TEXT,
            trade_group_id INTEGER REFERENCES trade_groups(id),
            updated_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trade_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            strategy_type TEXT NOT NULL,
            underlying TEXT NOT NULL,
            collapsed INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS position_group_map (
            ibkr_position_id TEXT NOT NULL,
            trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
            PRIMARY KEY (ibkr_position_id, trade_group_id)
        );
        -- D38: yfinance event cache (38b.1). One row per symbol: JSON list of
        -- corporate events (earnings/dividends/splits), 24h TTL (6h for
        -- near-term events). failed_at marks the last failed fetch with no
        -- usable cache -> the explicit "event data unavailable" state.
        CREATE TABLE IF NOT EXISTS yfinance_events_cache (
            symbol TEXT NOT NULL PRIMARY KEY,
            fetched_at REAL NOT NULL DEFAULT 0,
            failed_at REAL NOT NULL DEFAULT 0,
            payload TEXT NOT NULL DEFAULT '[]'
        );
        -- D39: volume-burst baseline (39.2). One row per (resolved contract,
        -- time-of-day bucket): robust median/MAD over <=30 per-minute volume
        -- samples. The samples JSON is the exact sample set (median/MAD need
        -- the raw values); median/mad/n are the fast read path. Keyed on the
        -- resolved contract (e.g. ESZ6, never bare ES) so a roll can never
        -- compare one contract's volume against another's baseline (C39.2).
        CREATE TABLE IF NOT EXISTS volume_baseline (
            resolved_contract TEXT NOT NULL,
            bucket INTEGER NOT NULL,
            median REAL NOT NULL DEFAULT 0,
            mad REAL NOT NULL DEFAULT 0,
            n INTEGER NOT NULL DEFAULT 0,
            samples TEXT NOT NULL DEFAULT '[]',
            updated_at INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (resolved_contract, bucket)
        );
        """
        self.conn.executescript(schema)
        self._migrate_schema()
        self.conn.commit()

    def _migrate_schema(self):
        alarm_columns = self._table_columns("alarms")
        if "created_at" not in alarm_columns:
            self.conn.execute("ALTER TABLE alarms ADD COLUMN created_at INTEGER")
        # D39.3: volume_burst alarm kind — additive columns; price alarms
        # untouched. kind defaults to 'price', params to '{}' (JSON).
        if "kind" not in alarm_columns:
            self.conn.execute(
                "ALTER TABLE alarms ADD COLUMN kind TEXT NOT NULL DEFAULT 'price'"
            )
        if "params" not in alarm_columns:
            self.conn.execute(
                "ALTER TABLE alarms ADD COLUMN params TEXT NOT NULL DEFAULT '{}'"
            )
        # D27.5: _upsert_position's ON CONFLICT(symbol, con_id) requires a
        # matching unique constraint — without it every position persist
        # raised OperationalError.
        self.conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "idx_positions_symbol_con_id ON positions(symbol, con_id)"
        )
        # D46 / A99 (reversing A87): the stop/target storage is gone — the four
        # columns are dropped, not merely ignored. Guarded by PRAGMA table_info
        # like every migration above: a fresh DB (already created without them)
        # and every later open see no such column and skip all four statements,
        # so this is idempotent and never half-builds a table. Each `DROP
        # COLUMN` is one atomic autocommitted statement, so an open interrupted
        # between two of them is finished by the next one. Preserved: every row
        # (and its `trade_group_id`), `idx_positions_symbol_con_id`, the
        # `trade_group_id -> trade_groups.id` foreign key, and `sqlite_sequence`
        # (ids are never reissued). Only the two columns' values are lost.
        for _table in ("positions", "trade_groups"):
            _columns = self._table_columns(_table)
            for _column in ("stop_loss", "take_profit"):
                if _column in _columns:
                    self.conn.execute(
                        f"ALTER TABLE {_table} DROP COLUMN {_column}"
                    )
        # D42 / S16 (AR-D42-5): mode-aware bars key. SQLite cannot alter a
        # primary key, so a legacy `bars` table (symbol, timeframe, ts) is
        # rebuilt once with the new key (symbol, timeframe, ext_hours, ts).
        # Guarded by PRAGMA table_info(bars): a fresh DB — already created
        # with the new key above — and every subsequent open are no-ops
        # (idempotent). INSERT OR IGNORE copies every legacy row tagged
        # ext_hours = 1 (ETH, the app's default mode); no row is deleted.
        _tables = {
            row[0]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if "bars_new" in _tables:
            # A prior open was interrupted mid-rebuild: Python's sqlite3 runs
            # the CREATE outside the implicit DML transaction, so a leftover
            # `bars_new` can survive while the INSERT/DROP/RENAME roll back
            # together. Salvage any rows it holds, then drop it so the
            # rebuild below starts from a clean slate. When `bars` is still
            # legacy the leftover is necessarily empty, so nothing is lost.
            if "ext_hours" in self._table_columns("bars"):
                self.conn.execute(
                    "INSERT OR IGNORE INTO bars SELECT * FROM bars_new"
                )
            self.conn.execute("DROP TABLE bars_new")
        if "ext_hours" not in self._table_columns("bars"):
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS bars_new ("
                "symbol TEXT NOT NULL, "
                "timeframe TEXT NOT NULL, "
                "ext_hours INTEGER NOT NULL DEFAULT 1, "
                "ts INTEGER NOT NULL, "
                "open REAL, high REAL, low REAL, close REAL, volume REAL, "
                "PRIMARY KEY (symbol, timeframe, ext_hours, ts))"
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO bars_new "
                "(symbol, timeframe, ext_hours, ts, open, high, low, close, volume) "
                "SELECT symbol, timeframe, 1, ts, open, high, low, close, volume "
                "FROM bars"
            )
            self.conn.execute("DROP TABLE bars")
            self.conn.execute("ALTER TABLE bars_new RENAME TO bars")
        # D41 / S7 (Q49/A69/DG70): the D36 footprint cache feature is removed;
        # drop its table and rows on every open. _migrate_schema() already runs
        # unconditionally here, and IF EXISTS keeps this an idempotent,
        # crash-safe no-op on fresh DBs and after the first drop.
        self.conn.execute("DROP TABLE IF EXISTS footprint_cache")

    def _table_columns(self, table_name: str) -> set[str]:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}

    # ── Watchlist ──────────────────────────────────────────────────────────────

    def get_watchlist(self) -> list[tuple[str, str]]:
        """Return [(symbol, category)] ordered by sort_order."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT symbol, category FROM watchlist ORDER BY sort_order ASC")
        return [(row[0], row[1]) for row in cursor.fetchall()]

    def add_watchlist_symbol(self, symbol: str, category: str = "EQUITIES") -> None:
        """Append a symbol to the watchlist (case-insensitive, idempotent).

        If ``symbol`` is already present under any letter case the existing row
        is left untouched (its category and sort_order are preserved). Otherwise
        a new row is appended with ``sort_order = max(existing) + 1`` (0 when the
        table is empty).
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO watchlist (symbol, category, sort_order) "
            "SELECT ?, ?, (SELECT COALESCE(MAX(sort_order), -1) + 1 FROM watchlist) "
            "WHERE NOT EXISTS ("
            "SELECT 1 FROM watchlist WHERE symbol = ? COLLATE NOCASE"
            ")",
            (symbol, category, symbol),
        )
        self.conn.commit()

    def remove_watchlist_symbol(self, symbol: str) -> None:
        """Remove a symbol (case-insensitive) and renumber survivors 0..n-1.

        The remaining rows are renumbered contiguously preserving their relative
        order. Removing a symbol that is not present is a no-op.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM watchlist WHERE symbol = ? COLLATE NOCASE", (symbol,)
        )
        if cursor.rowcount == 0:
            self.conn.commit()
            return
        cursor.execute("SELECT rowid FROM watchlist ORDER BY sort_order ASC")
        rowids = [row[0] for row in cursor.fetchall()]
        for new_order, rowid in enumerate(rowids):
            cursor.execute(
                "UPDATE watchlist SET sort_order = ? WHERE rowid = ?",
                (new_order, rowid),
            )
        self.conn.commit()

    def set_watchlist(self, symbols: list[str], category: str = "EQUITIES", sort_order: list[str] | None = None) -> None:
        """Replace the whole watchlist.

        Args:
            symbols: list of symbol strings.
            category: category label for all symbols (default: 'EQUITIES').
            sort_order: optional list of sort-order strings (same length as symbols).
                If not provided, numeric indices are used.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM watchlist")
        if sort_order is None:
            sort_order = [str(i) for i in range(len(symbols))]
        elif len(sort_order) != len(symbols):
            raise ValueError("sort_order must have same length as symbols")
        cursor.executemany(
            "INSERT OR REPLACE INTO watchlist (symbol, category, sort_order) VALUES (?, ?, ?)",
            [(sym, category, sort_order[i]) for i, sym in enumerate(symbols)],
        )
        self.conn.commit()


# Main thread singleton
db = DB()
