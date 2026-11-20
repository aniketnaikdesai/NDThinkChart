"""D86 + D94 (P28-05): startup reaches a dialog.

Two startup hazards used to kill the process before a dialog could exist:

* an **unverifiable pre-drop backup** — ``DB._migrate_schema`` called
  ``db_backup.backup_before_drop`` unguarded, and ``data/db.py`` builds its
  ``db = DB()`` singleton at import, so a read-only/full disk raised
  ``BackupVerificationError`` before ``main()``'s ``QMessageBox`` path existed
  (D86);
* a **malformed settings value** — ``int(os.getenv(...))`` raised a bare
  ``ValueError`` while ``main`` was being imported, i.e. before ``QApplication``
  and before ``check_live_port()`` could turn it into the fatal dialog (D94).

Both are now non-fatal at import: a skipped drop records exactly one notice in
``DB.startup_notices`` (shown once by ``main()`` after ``QApplication``) and the
app starts with the retired tables intact; a malformed port/client id is kept
as raw text and refused by ``check_live_port()`` inside ``main()``.

The verified-copy contract is **not** weakened: the drop still requires a
verified copy, and there is no force-drop path. ``tests/test_db_backup.py``
remains the contract suite for that (AC-D65.18).
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import data.db_backup as db_backup
from data.db_backup import BackupVerificationError

_REPO = Path(__file__).resolve().parent.parent

_RETIRED_TABLES = ("position_group_map", "positions", "trade_groups")

#: A pre-D65 database: the three retired tables and rows in each.
_LEGACY_DDL = """
CREATE TABLE trade_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    trade_group_id INTEGER REFERENCES trade_groups(id)
);
CREATE TABLE position_group_map (
    ibkr_position_id TEXT NOT NULL,
    trade_group_id INTEGER NOT NULL REFERENCES trade_groups(id),
    PRIMARY KEY (ibkr_position_id, trade_group_id)
);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_legacy_db(path: Path) -> Path:
    """Create a DB holding the three retired tables and one/two/four rows."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(_LEGACY_DDL)
        conn.execute("INSERT INTO trade_groups (id, name) VALUES (7, 'PCS')")
        conn.executemany(
            "INSERT INTO positions (id, symbol, trade_group_id) VALUES (?, ?, 7)",
            [(1, "AAPL"), (2, "MSFT")],
        )
        conn.execute(
            "INSERT INTO position_group_map (ibkr_position_id, trade_group_id)"
            " VALUES ('DU123:1', 7)"
        )
        conn.execute(
            "INSERT INTO position_group_map (ibkr_position_id, trade_group_id)"
            " VALUES ('DU123:2', 7)"
        )
        conn.commit()
    finally:
        conn.close()
    return path


def _route_db(monkeypatch, db_file: Path, user_dir: Path) -> None:
    """Point ``DB()`` at ``db_file`` and its backups at ``user_dir``."""
    from config import paths

    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))
    monkeypatch.setattr(paths, "_USER_APP_SUPPORT_DIR", user_dir)


def _trace_connects(monkeypatch, statements: list[str]) -> None:
    """Record every statement executed through ``sqlite3.connect``."""
    real_connect = sqlite3.connect

    def _connect(database, *args, **kwargs):
        conn = real_connect(database, *args, **kwargs)
        conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(sqlite3, "connect", _connect)


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


def _retired_drops(statements: list[str]) -> list[str]:
    return [
        sql.strip()
        for sql in statements
        if sql.strip().upper().startswith("DROP TABLE")
        and any(table in sql for table in _RETIRED_TABLES)
    ]


def _row_counts(path: Path) -> dict[str, int]:
    """Row count of every user table in ``path`` (``sqlite_*`` excluded)."""
    conn = sqlite3.connect(str(path))
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            if not row[0].startswith("sqlite_")
        ]
        return {
            table: conn.execute(
                f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in tables
        }
    finally:
        conn.close()


def _row_counts_on(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        for table in sorted(_table_names(conn))
        if not table.startswith("sqlite_")
    }


def _run_harness(script: str, tmp_path: Path, **env_overrides: str):
    """Run a ``-c`` script in this repo with offscreen Qt and a temp DB."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("IBKR_")}
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["DB_PATH"] = str(tmp_path / "harness.sqlite3")
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(_REPO),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _harness_payload(proc: subprocess.CompletedProcess) -> dict:
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("HARNESS "):
            return json.loads(line[len("HARNESS "):])
    raise AssertionError(
        "harness printed no result line\n"
        f"exit={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


# ---------------------------------------------------------------------------
# (a) AC-D86.1 — a failed backup skips the drop, keeps the tables, one notice
# ---------------------------------------------------------------------------

def test_failed_backup_skips_drop_and_records_one_notice(tmp_path, monkeypatch):
    legacy = _write_legacy_db(tmp_path / "legacy_skip.sqlite3")
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, legacy, user_dir)

    def _boom(*args, **kwargs):
        raise BackupVerificationError("injected: copy failed integrity_check")

    monkeypatch.setattr(db_backup, "backup_before_drop", _boom)
    statements: list[str] = []
    _trace_connects(monkeypatch, statements)

    from data.db import DB

    db = DB()  # must not raise — the app has to start
    try:
        assert set(_RETIRED_TABLES) <= _table_names(db.conn)
        assert db.conn.execute(
            "SELECT COUNT(*) FROM positions").fetchone() == (2,)
        assert db.conn.execute(
            "SELECT COUNT(*) FROM trade_groups").fetchone() == (1,)
        assert db.conn.execute(
            "SELECT COUNT(*) FROM position_group_map").fetchone() == (2,)

        # No drop ran, for any of the three names.
        assert _retired_drops(statements) == []

        # Exactly one notice, naming the backup location and the cause.
        assert len(db.startup_notices) == 1
        notice = db.startup_notices[0]
        assert str(legacy) in notice
        assert str(user_dir / "backups") in notice
        assert "injected: copy failed integrity_check" in notice
        assert "inert" in notice
        assert "next launch" in notice
    finally:
        db.conn.close()


# ---------------------------------------------------------------------------
# (b) AC-D86.3 — the skip path modifies/removes no row anywhere
# ---------------------------------------------------------------------------

def test_skip_path_preserves_every_surviving_table(tmp_path, monkeypatch):
    legacy = _write_legacy_db(tmp_path / "legacy_rows.sqlite3")
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, legacy, user_dir)
    before = _row_counts(legacy)

    def _boom(*args, **kwargs):
        raise BackupVerificationError("injected: backup volume read-only")

    monkeypatch.setattr(db_backup, "backup_before_drop", _boom)

    from data.db import DB

    db = DB()
    try:
        after = _row_counts_on(db.conn)
        for table, count in before.items():
            assert table in after, f"{table!r} disappeared on the skip path"
            assert after[table] == count, (
                f"{table!r} changed on the skip path: {count} -> {after[table]}")
        assert db.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        db.conn.close()


# ---------------------------------------------------------------------------
# (c) AC-D86.2 — a verified copy still drops exactly once, no notice
# ---------------------------------------------------------------------------

def test_successful_backup_drops_once_and_records_no_notice(
        tmp_path, monkeypatch):
    legacy = _write_legacy_db(tmp_path / "legacy_drop.sqlite3")
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, legacy, user_dir)

    calls: list[Path] = []

    def _verified(db_path, *args, **kwargs):
        calls.append(Path(db_path))
        return tmp_path / "charting_app_pre-D65_verified.sqlite3"

    monkeypatch.setattr(db_backup, "backup_before_drop", _verified)
    statements: list[str] = []
    _trace_connects(monkeypatch, statements)

    from data.db import DB

    db = DB()
    try:
        assert calls == [legacy]
        assert _retired_drops(statements) == [
            "DROP TABLE IF EXISTS position_group_map",
            "DROP TABLE IF EXISTS positions",
            "DROP TABLE IF EXISTS trade_groups",
        ]
        assert not set(_RETIRED_TABLES) & _table_names(db.conn)
        assert db.startup_notices == []
    finally:
        db.conn.close()


# ---------------------------------------------------------------------------
# (d) a database with no retired tables: nothing happens, no notice
# ---------------------------------------------------------------------------

def test_no_retired_tables_means_no_backup_and_no_notice(tmp_path, monkeypatch):
    fresh = tmp_path / "fresh.sqlite3"
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, fresh, user_dir)

    def _unexpected(*args, **kwargs):
        raise AssertionError("a fresh database must not trigger a backup")

    monkeypatch.setattr(db_backup, "backup_before_drop", _unexpected)
    statements: list[str] = []
    _trace_connects(monkeypatch, statements)

    from data.db import DB

    db = DB()
    try:
        assert db.startup_notices == []
        assert _retired_drops(statements) == []
        assert not set(_RETIRED_TABLES) & _table_names(db.conn)
    finally:
        db.conn.close()


# ---------------------------------------------------------------------------
# (e) two consecutive failing launches: one notice each, neither drops
# ---------------------------------------------------------------------------

def test_two_failing_launches_each_record_one_notice_and_never_drop(
        tmp_path, monkeypatch):
    legacy = _write_legacy_db(tmp_path / "legacy_twice.sqlite3")
    user_dir = tmp_path / "userdata"
    _route_db(monkeypatch, legacy, user_dir)

    def _boom(*args, **kwargs):
        raise BackupVerificationError("injected: verification still failing")

    monkeypatch.setattr(db_backup, "backup_before_drop", _boom)
    statements: list[str] = []
    _trace_connects(monkeypatch, statements)

    from data.db import DB

    for launch in range(2):
        statements.clear()
        db = DB()
        try:
            assert len(db.startup_notices) == 1, (
                f"launch {launch}: expected one notice, "
                f"got {db.startup_notices!r}")
            assert _retired_drops(statements) == []
            assert set(_RETIRED_TABLES) <= _table_names(db.conn)
        finally:
            db.conn.close()


# ---------------------------------------------------------------------------
# (f)/(g) AC-D94.1 / AC-P28-05-2 / AC-P28-05-3 — the fatal dialog path
# ---------------------------------------------------------------------------

_FATAL_HARNESS = """
import json
import sys

import main

recorded = []


class _FakeBox:
    @staticmethod
    def critical(parent, title, text):
        recorded.append({"title": title, "text": text})

    @staticmethod
    def warning(parent, title, text):
        recorded.append({"title": title, "text": text})


main.QMessageBox = _FakeBox

rc = main.main()

print("HARNESS " + json.dumps({
    "rc": rc,
    "recorded": recorded,
    "ui_main_window_imported": "ui.main_window" in sys.modules,
    "module_has_mainwindow": hasattr(main, "MainWindow"),
}), flush=True)
sys.exit(rc)
"""


def test_malformed_port_reaches_fatal_dialog(tmp_path):
    proc = _run_harness(_FATAL_HARNESS, tmp_path, IBKR_PORT="abc")

    assert proc.returncode == 1, proc.stderr
    payload = _harness_payload(proc)
    assert payload["rc"] == 1
    assert len(payload["recorded"]) == 1
    assert payload["recorded"][0]["title"] == "NDThinkChart — cannot start"
    message = payload["recorded"][0]["text"]
    assert "abc" in message, message
    assert "IBKR_PORT" in message
    assert "read-only market-data client" in message
    # MainWindow — and so the DB singleton import — never happened.
    assert payload["ui_main_window_imported"] is False
    assert payload["module_has_mainwindow"] is False
    # No bare ValueError escaped the import.
    assert "ValueError" not in proc.stdout
    assert "ValueError" not in proc.stderr


def test_malformed_client_id_reaches_fatal_dialog(tmp_path):
    proc = _run_harness(
        _FATAL_HARNESS, tmp_path, IBKR_PORT="7496", IBKR_CLIENT_ID="abc")

    assert proc.returncode == 1, proc.stderr
    payload = _harness_payload(proc)
    assert payload["rc"] == 1
    assert len(payload["recorded"]) == 1
    message = payload["recorded"][0]["text"]
    assert "abc" in message, message
    assert "IBKR_CLIENT_ID" in message
    assert "read-only market-data client" in message
    assert payload["ui_main_window_imported"] is False
    assert "ValueError" not in proc.stdout
    assert "ValueError" not in proc.stderr


def test_paper_port_still_refused_through_the_same_dialog(tmp_path):
    from config import settings

    assert settings.LIVE_PORT == 7496

    proc = _run_harness(_FATAL_HARNESS, tmp_path, IBKR_PORT="7497")

    assert proc.returncode == 1, proc.stderr
    payload = _harness_payload(proc)
    assert len(payload["recorded"]) == 1
    message = payload["recorded"][0]["text"]
    assert "7497" in message
    assert "7496" in message
    assert all(p in message for p in ("read-only market-data client", "places no orders", "configured port")), message
    assert payload["ui_main_window_imported"] is False


# ---------------------------------------------------------------------------
# AC-P28-05-1 — main() shows each recorded notice exactly once, after QApplication
# ---------------------------------------------------------------------------

_NOTICE_HARNESS = """
import json
import sys
import types

import main
from data import db as db_module

shown = []


class _FakeBox:
    @staticmethod
    def critical(parent, title, text):
        shown.append(["critical", title, text])

    @staticmethod
    def warning(parent, title, text):
        shown.append(["warning", title, text])


main.QMessageBox = _FakeBox


class _FakeApp:
    def __init__(self, argv):
        shown.append(["qapplication"])

    def setStyle(self, _style):
        pass

    def setStyleSheet(self, _qss):
        pass

    def exec(self):
        return 0


class _FakeWindow:
    def __init__(self):
        shown.append(["window-constructed"])

    def show(self):
        pass


fake_ui = types.ModuleType("ui.main_window")
fake_ui.MainWindow = _FakeWindow
sys.modules["ui.main_window"] = fake_ui

db_module.startup_notices = lambda: ["first notice", "second notice"]
main.QApplication = _FakeApp

rc = main.main()

print("HARNESS " + json.dumps({"rc": rc, "shown": shown}), flush=True)
sys.exit(rc)
"""


def test_main_shows_each_notice_once_after_qapplication(tmp_path):
    proc = _run_harness(_NOTICE_HARNESS, tmp_path, IBKR_PORT="7496")

    assert proc.returncode == 0, proc.stderr
    payload = _harness_payload(proc)
    assert payload["rc"] == 0
    shown = payload["shown"]

    warnings = [entry for entry in shown if entry[0] == "warning"]
    assert warnings == [
        ["warning", "NDThinkChart — database migration skipped", "first notice"],
        ["warning", "NDThinkChart — database migration skipped", "second notice"],
    ]
    qapp_at = shown.index(["qapplication"])
    window_at = shown.index(["window-constructed"])
    assert qapp_at < shown.index(warnings[0]) < window_at
    assert shown.index(warnings[1]) < window_at


def test_main_keeps_the_module_level_startup_ordering():
    import inspect

    import main

    module_src = inspect.getsource(main)
    main_src = inspect.getsource(main.main)

    # The window import (and so the DB singleton) lives inside main(), after
    # both QApplication and the port guard.
    assert "from ui.main_window import MainWindow" in main_src
    assert "from ui.main_window import" not in module_src.replace(main_src, "")
    assert not hasattr(main, "MainWindow")

    qapp_at = main_src.index("QApplication(sys.argv)")
    guard_at = main_src.index("settings.check_live_port()")
    import_at = main_src.index("from ui.main_window import MainWindow")
    notices_at = main_src.index("db_module.startup_notices()")
    window_at = main_src.index("window = MainWindow()")
    assert qapp_at < guard_at < import_at < notices_at < window_at

    # The two required module-level calls keep their place, the scheme
    # registration above the QApplication line.
    assert module_src.index("paths.opt_in_production_db()") < module_src.index(
        "def main()")
    assert module_src.index("\n_register_lwc_scheme_before_qapp()\n") < (
        module_src.index("app = QApplication(sys.argv)"))
