"""Schema regression tests for data/db.py (ESC-001 / DOC-3).

Guards that a fresh DB() creates the full table set and that ``_init_schema``
is defined exactly once in data/db.py.
"""

import ast
from pathlib import Path

import config.paths as paths

# ESC-001: the complete set of tables a fresh database must contain. The D65
# position/trade-group tables were retired with their feature — their absence
# is asserted below, not their presence (AC-D65.18).
EXPECTED_TABLES = {
    "bars",
    "watchlist",
    "alarms",
    "zones",
    "drawing_groups",
    "drawings",
    "studies",
}

#: The three tables D65 dropped; a fresh DB must never create them again.
_RETIRED_TABLES = ("positions", "trade_groups", "position_group_map")

# data/db.py lives one directory above this test file.
_DB_SOURCE = Path(__file__).resolve().parent.parent / "data" / "db.py"


def test_fresh_db_creates_full_table_set(tmp_path, monkeypatch):
    """T26-T01 / P23-T12-AC5: a fresh DB() creates all seven expected tables."""
    db_file = tmp_path / "fresh_schema_test.sqlite3"
    # Route the DB at a throwaway path so nothing touches the shared test DB.
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))

    from data.db import DB

    fresh = DB()
    try:
        rows = fresh.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        tables = {row[0] for row in rows}
    finally:
        fresh.conn.close()

    missing = EXPECTED_TABLES - tables
    assert not missing, f"missing tables: {sorted(missing)}"
    assert EXPECTED_TABLES <= tables


def test_init_schema_defined_once():
    """T26-T02: data/db.py defines _init_schema exactly once."""
    source = _DB_SOURCE.read_text()
    tree = ast.parse(source)
    count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_init_schema"
    )
    assert count == 1, f"expected 1 _init_schema definition, found {count}"


def test_footprint_cache_absent_and_dropped(tmp_path, monkeypatch):
    """P1-T63-T11 / AC-D41.3 (Q49/A69/DG70): the removed D36 footprint cache
    table is absent from a fresh DB and is DROPPED from a legacy DB on open.

    A pre-D41 install carries ``footprint_cache`` with rows; the S7 migration
    must remove both the table and its data on the next open.
    """
    import sqlite3

    # (a) legacy DB: pre-seed the OLD DDL + a row, as a pre-D41 install has it.
    legacy_file = tmp_path / "legacy_footprint.sqlite3"
    legacy = sqlite3.connect(str(legacy_file))
    legacy.execute(
        "CREATE TABLE footprint_cache (key TEXT PRIMARY KEY, payload TEXT,"
        " updated_at INTEGER)"
    )
    legacy.execute(
        "INSERT INTO footprint_cache (key, payload, updated_at) VALUES (?,?,?)",
        ("AAPL|5 mins|stock", "{}", 1_760_000_000),
    )
    legacy.commit()
    legacy.close()

    monkeypatch.setattr(paths, "_DB_FILENAME", str(legacy_file))
    from data.db import DB

    upgraded = DB()
    try:
        tables = {r[0] for r in upgraded.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
        assert "footprint_cache" not in tables, (
            "the removed D36 table must be dropped on open")
    finally:
        upgraded.conn.close()

    # (b) fresh DB: the DDL is gone from _init_schema too, so it never appears.
    fresh_file = tmp_path / "fresh_no_footprint.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(fresh_file))
    fresh = DB()
    try:
        tables = {r[0] for r in fresh.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
        assert "footprint_cache" not in tables
    finally:
        fresh.conn.close()


def test_retained_d41_tables_survive(tmp_path, monkeypatch):
    """P1-T63-T21 / AC-D41.4: the D38/D39 tables survive the footprint removal.

    ``yfinance_events_cache`` (D38) and ``volume_baseline`` (D39) are KEEP-list
    substrate; the D41 drop must not take them with it.
    """
    db_file = tmp_path / "retained_tables.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))

    from data.db import DB

    fresh = DB()
    try:
        tables = {r[0] for r in fresh.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
    finally:
        fresh.conn.close()

    assert {"volume_baseline", "yfinance_events_cache"} <= tables
    # The pre-existing subset assertion still holds.
    assert EXPECTED_TABLES <= tables


def _bars_primary_key(conn):
    """Return ``bars``' primary-key columns in key order (via PRAGMA)."""
    info = conn.execute("PRAGMA table_info(bars)").fetchall()
    # PRAGMA row shape: (cid, name, type, notnull, dflt_value, pk). pk is a
    # 1-based position within the key, 0 for non-key columns.
    return [row[1] for row in sorted((r for r in info if r[5]), key=lambda r: r[5])]


def _bars_column(conn, name):
    """Return the PRAGMA table_info row for ``name``, or None when absent."""
    for row in conn.execute("PRAGMA table_info(bars)").fetchall():
        if row[1] == name:
            return row
    return None


def test_bars_ext_hours_column_and_key(tmp_path, monkeypatch):
    """P2-T17-T11 / AC1 (D42 / S16): a fresh DB's ``bars`` carries the
    ``ext_hours INTEGER NOT NULL DEFAULT 1`` column and the mode-aware key
    ``(symbol, timeframe, ext_hours, ts)``.
    """
    db_file = tmp_path / "fresh_bars_key.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))

    from data.db import DB

    fresh = DB()
    try:
        col = _bars_column(fresh.conn, "ext_hours")
        assert col is not None, "bars must gain the ext_hours column"
        # (cid, name, type, notnull, dflt_value, pk)
        assert col[2].upper() == "INTEGER", col
        assert col[3] == 1, "ext_hours must be NOT NULL"
        assert str(col[4]) == "1", "ext_hours must default to 1 (ETH)"

        assert _bars_primary_key(fresh.conn) == [
            "symbol",
            "timeframe",
            "ext_hours",
            "ts",
        ], "the bars key must be (symbol, timeframe, ext_hours, ts)"
    finally:
        fresh.conn.close()


def test_legacy_bars_migration_preserves_rows(tmp_path, monkeypatch):
    """P2-T17-T11 / AC1 (D42 / S16): a legacy ``bars`` table (old key
    ``(symbol, timeframe, ts)``) is rebuilt once with the new key, every row
    preserved and tagged ``ext_hours = 1``.
    """
    import sqlite3

    # (a) legacy DB: pre-seed the OLD DDL + rows, as a pre-D42 install has it.
    legacy_file = tmp_path / "legacy_bars.sqlite3"
    legacy = sqlite3.connect(str(legacy_file))
    legacy.execute(
        "CREATE TABLE bars ("
        "symbol TEXT NOT NULL, timeframe TEXT NOT NULL, ts INTEGER NOT NULL, "
        "open REAL, high REAL, low REAL, close REAL, volume REAL, "
        "PRIMARY KEY (symbol, timeframe, ts))"
    )
    seeded = [
        ("AAPL", "5 mins", 1_760_000_000, 1.0, 2.0, 0.5, 1.5, 100.0),
        ("AAPL", "5 mins", 1_760_000_300, 1.5, 2.5, 1.0, 2.0, 110.0),
        ("SPY", "1 day", 1_760_000_000, 10.0, 11.0, 9.5, 10.5, 200.0),
    ]
    legacy.executemany(
        "INSERT INTO bars (symbol, timeframe, ts, open, high, low, close, volume) "
        "VALUES (?,?,?,?,?,?,?,?)",
        seeded,
    )
    legacy.commit()
    legacy.close()

    monkeypatch.setattr(paths, "_DB_FILENAME", str(legacy_file))
    from data.db import DB

    upgraded = DB()
    try:
        # The rebuilt key is the mode-aware one.
        assert _bars_primary_key(upgraded.conn) == [
            "symbol",
            "timeframe",
            "ext_hours",
            "ts",
        ]
        assert _bars_column(upgraded.conn, "ext_hours") is not None

        # Every legacy row survived, tagged ext_hours = 1 (ETH default), with
        # its price/volume payload intact.
        rows = upgraded.conn.execute(
            "SELECT symbol, timeframe, ext_hours, ts, open, high, low, close,"
            " volume FROM bars ORDER BY symbol, ts"
        ).fetchall()
        assert len(rows) == len(seeded), "no legacy bar row may be dropped"
        assert all(row[2] == 1 for row in rows), "legacy rows must be ETH (1)"
        assert {row[:4] for row in rows} == {
            (s, tf, 1, ts) for (s, tf, ts, *_rest) in seeded
        }
        # Payload columns round-trip unchanged.
        assert {
            (row[0], row[1], row[3], row[4], row[5], row[6], row[7], row[8])
            for row in rows
        } == set(seeded)
    finally:
        upgraded.conn.close()


def test_legacy_bars_migration_is_idempotent(tmp_path, monkeypatch):
    """P2-T17-T11 / AC1 (D42 / S16): reopening an already-migrated DB is a
    no-op — no rows dropped, no duplicate rows.
    """
    import sqlite3

    legacy_file = tmp_path / "legacy_bars_reopen.sqlite3"
    legacy = sqlite3.connect(str(legacy_file))
    legacy.execute(
        "CREATE TABLE bars ("
        "symbol TEXT NOT NULL, timeframe TEXT NOT NULL, ts INTEGER NOT NULL, "
        "open REAL, high REAL, low REAL, close REAL, volume REAL, "
        "PRIMARY KEY (symbol, timeframe, ts))"
    )
    legacy.execute(
        "INSERT INTO bars (symbol, timeframe, ts, open, high, low, close, volume)"
        " VALUES (?,?,?,?,?,?,?,?)",
        ("AAPL", "5 mins", 1_760_000_000, 1.0, 2.0, 0.5, 1.5, 100.0),
    )
    legacy.commit()
    legacy.close()

    monkeypatch.setattr(paths, "_DB_FILENAME", str(legacy_file))
    from data.db import DB

    first = DB()
    first.conn.close()
    second = DB()
    try:
        rows = second.conn.execute(
            "SELECT symbol, timeframe, ext_hours, ts FROM bars"
        ).fetchall()
        assert rows == [("AAPL", "5 mins", 1, 1_760_000_000)]
    finally:
        second.conn.close()


# The pre-D65 DDL: the three retired tables plus the unique index none of them
# carries any more. Kept minimal — the migration only has to remove them.
_LEGACY_RETIRED_DDL = """
CREATE TABLE trade_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    underlying TEXT NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    collapsed INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE positions (
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
    stop_loss REAL,
    take_profit REAL,
    trade_group_id INTEGER REFERENCES trade_groups(id),
    updated_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX idx_positions_symbol_con_id
    ON positions(symbol, con_id);
CREATE TABLE position_group_map (
    ibkr_position_id TEXT NOT NULL,
    trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
    PRIMARY KEY (ibkr_position_id, trade_group_id)
);
"""


def _legacy_retired_db(path):
    """Write a legacy DB holding one row in each retired table."""
    import sqlite3

    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_LEGACY_RETIRED_DDL)
        conn.execute(
            "INSERT INTO trade_groups (id, name, strategy_type, underlying,"
            " stop_loss, take_profit, collapsed, created_at)"
            " VALUES (7, 'PCS', 'PCS', 'AAPL', 1.5, 2.5, 0, 1760000000)"
        )
        conn.execute(
            "INSERT INTO positions (id, symbol, account, con_id,"
            " contract_type, qty, avg_cost, local_symbol, multiplier, expiry,"
            " strike, right, stop_loss, take_profit, trade_group_id,"
            " updated_at)"
            " VALUES (1, 'AAPL', 'DU123', 1, 'stock', 10.0, 40.0, 'AAPL',"
            " 1.0, NULL, NULL, NULL, 1.5, 2.5, 7, 1760000000)"
        )
        conn.execute(
            "INSERT INTO position_group_map (ibkr_position_id, trade_group_id)"
            " VALUES ('DU123:1', 7)"
        )
        conn.commit()
    finally:
        conn.close()


def _schema_names(conn):
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')"
        ).fetchall()
    }


def test_retired_position_tables_are_absent_and_dropped_once(tmp_path, monkeypatch):
    """P23-T12-AC3/AC5: none of the three retired tables (nor their unique
    index) exists in a fresh DB; a legacy DB holding rows loses all three on
    the first open, and a second open is a no-op.
    """
    # Keep the pre-drop backup out of the owner's application-support dir.
    monkeypatch.setattr(paths, "_USER_APP_SUPPORT_DIR", tmp_path / "userdata")

    # (a) a fresh DB never creates them, and never creates the index.
    fresh_file = tmp_path / "fresh_no_retired.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(fresh_file))
    from data.db import DB

    fresh = DB()
    try:
        names = _schema_names(fresh.conn)
        for table in _RETIRED_TABLES:
            assert table not in names, (
                f"a fresh DB still creates the retired table {table!r}")
        assert "idx_positions_symbol_con_id" not in names
    finally:
        fresh.conn.close()

    # (b) a legacy DB holding rows loses all three on the first open.
    legacy_file = tmp_path / "legacy_retired.sqlite3"
    _legacy_retired_db(legacy_file)
    monkeypatch.setattr(paths, "_DB_FILENAME", str(legacy_file))

    first = DB()
    try:
        names = _schema_names(first.conn)
        for table in _RETIRED_TABLES:
            assert table not in names, (
                f"the migration left the retired table {table!r} behind")
        assert "idx_positions_symbol_con_id" not in names, (
            "idx_positions_symbol_con_id outlived its positions table")
    finally:
        first.conn.close()

    # (c) a second open is a no-op — no error, still absent, no backup retaken.
    backups_dir = tmp_path / "userdata" / "backups"
    backup_count = len(list(backups_dir.glob("charting_app_pre-D65_*.sqlite3")))
    second = DB()
    try:
        names = _schema_names(second.conn)
        for table in _RETIRED_TABLES:
            assert table not in names, (
                f"a second open resurrected the retired table {table!r}")
        assert "idx_positions_symbol_con_id" not in names
    finally:
        second.conn.close()
    assert backup_count == 1, "the first open must take exactly one backup"
    assert len(list(backups_dir.glob("charting_app_pre-D65_*.sqlite3"))) == 1, (
        "a second open must not take another pre-drop backup")


def test_d46_stop_target_migration_and_carveout_are_gone():
    """P23-T12-AC3: the stop/target column loop and its exemption lost their
    only subject, so both are deleted with the tables that carried them.
    """
    source = _DB_SOURCE.read_text()
    assert "DROP COLUMN" not in source, (
        "data/db.py still drops a column; the D46 loop lost its subject")
    for token in ("stop_loss", "take_profit"):
        assert token not in source, (
            f"data/db.py still names the retired column {token!r}")

    instrument = (
        Path(__file__).resolve().parent / "test_d45_removal.py"
    ).read_text()
    for name in (
        "_ALLOWED_IN_FILE",
        "_allowed_in",
        "_drop_column_subject_nodes",
        "_EXEMPT_TOKENS",
        "test_allowed_in_file_is_narrow_and_named_not_used",
    ):
        assert name not in instrument, (
            f"tests/test_d45_removal.py still carries the subject-less "
            f"stop/target carve-out member {name!r}")

