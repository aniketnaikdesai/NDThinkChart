"""Schema regression tests for data/db.py (ESC-001 / DOC-3).

Guards that a fresh DB() creates the full table set and that ``_init_schema``
is defined exactly once in data/db.py.
"""

import ast
from pathlib import Path

import config.paths as paths

# ESC-001: the complete set of tables a fresh database must contain.
EXPECTED_TABLES = {
    "bars",
    "watchlist",
    "alarms",
    "zones",
    "drawing_groups",
    "drawings",
    "studies",
    "positions",
    "trade_groups",
    "position_group_map",
}

# data/db.py lives one directory above this test file.
_DB_SOURCE = Path(__file__).resolve().parent.parent / "data" / "db.py"


def test_fresh_db_creates_full_table_set(tmp_path, monkeypatch):
    """T26-T01: a fresh DB() against a temp path creates all ten tables."""
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
