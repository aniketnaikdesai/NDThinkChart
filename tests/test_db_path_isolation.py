"""ESC-043 limb 2 (P2-T32): a non-app process must not open the owner's
user-space production DB when ``DB_PATH`` is unset.

Architecture S12: any non-pytest probe that can reach a DB-writing path must
export ``DB_PATH`` to a temp file. This suite pins the code guard that enforces
that rule at the escalation's prescribed shape:

* ``DB_PATH`` unset + no app opt-in -> ``data.db.DB()`` fails loudly, no
  connection is opened, the user-space DB is never created (AC1 / T11).
* the real app opts in from ``main.py`` -> the user-space DB still opens (AC2 /
  T21).
* ``DB_PATH`` set (the ``tests/conftest.py`` pattern) -> the guard is inert and
  that file opens (AC3 / T31).
"""

import os
import subprocess
import sys
from pathlib import Path

import config.paths as paths

REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_NAME = "charting_app.sqlite3"


def _clean_env(home: Path) -> dict:
    """Env for a subprocess that must NOT reach the owner's real DB.

    ``DB_PATH`` is unset (the bug ESC-043 describes) and ``HOME`` is redirected
    to a temp dir, so any user-space path resolution lands under ``home`` and
    can be asserted against rather than touching the owner's real directory.
    """
    env = os.environ.copy()
    env.pop("DB_PATH", None)
    env["HOME"] = str(home)
    env["QT_QPA_PLATFORM"] = "offscreen"
    return env


def _user_space_db(home: Path) -> Path:
    """The user-space production DB path under a redirected ``HOME``."""
    return (
        home
        / "Library"
        / "Application Support"
        / "NDThinkChart"
        / _DEFAULT_DB_NAME
    )


def _run(script: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_guard_blocks_production_db_without_optin(tmp_path):
    """P2-T32-T11 (AC1): DB_PATH unset + no opt-in -> loud error, no DB.

    A subprocess with ``DB_PATH`` unset and no app opt-in constructs
    ``data.db.DB()``; it must raise the guard's clear error (non-zero exit) and
    the user-space production DB file must NOT be created. Pre-fix, ``DB()``
    opens/creates the production path -> RED.
    """
    home = tmp_path / "home"
    home.mkdir()

    proc = _run("from data.db import DB\nDB()\n", _clean_env(home))

    assert proc.returncode != 0, (
        "constructing DB() with DB_PATH unset must fail loudly\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    err = proc.stderr
    assert "DB_PATH" in err, f"error must name DB_PATH: {err}"
    assert "opt" in err.lower(), f"error must name the app opt-in: {err}"
    assert not _user_space_db(home).exists(), (
        "the user-space production DB must never be created"
    )


def test_guard_fires_before_sqlite_connect(tmp_path):
    """P2-T32-T11 (AC1): the guard fires before ``sqlite3.connect``.

    With ``config.paths.get_db_path`` monkeypatched to a sentinel path, the
    guard must still raise (it keys on DB_PATH being unset, not on the resolved
    path) and ``sqlite3.connect`` must never be reached -- no connection
    attempt, no sentinel file.
    """
    home = tmp_path / "home"
    home.mkdir()
    sentinel = tmp_path / "sentinel.sqlite3"

    script = (
        "import pathlib, sqlite3\n"
        "import config.paths as paths\n"
        f"sentinel = pathlib.Path({str(sentinel)!r})\n"
        "paths.get_db_path = lambda: sentinel\n"
        "def _boom(*a, **k):\n"
        "    raise AssertionError('sqlite3.connect was reached')\n"
        "sqlite3.connect = _boom\n"
        "from data.db import DB\n"
        "DB()\n"
    )
    proc = _run(script, _clean_env(home))

    assert proc.returncode != 0, (
        f"the guard must fire with a sentinel get_db_path\nstderr: {proc.stderr}"
    )
    assert "DB_PATH" in proc.stderr
    assert "sqlite3.connect was reached" not in proc.stderr, (
        "the guard must fire before sqlite3.connect"
    )
    assert not sentinel.exists(), "no connection may be opened"


def test_optin_opens_user_space_db(tmp_path):
    """P2-T32-T21 (AC2): the app opt-in still opens the user-space DB.

    Applying the opt-in exactly as ``main.py`` does, under a redirected HOME,
    must resolve and open the user-space production path -- the real app's DB
    resolution is unchanged end to end.
    """
    home = tmp_path / "home"
    home.mkdir()

    script = (
        "import config.paths as paths\n"
        "paths.opt_in_production_db()\n"
        "from data.db import DB\n"
        "d = DB()\n"
        "print(d.db_path)\n"
        "d.conn.close()\n"
    )
    proc = _run(script, _clean_env(home))

    assert proc.returncode == 0, (
        f"the opted-in app path must still work\nstderr: {proc.stderr}"
    )
    expected = _user_space_db(home)
    assert expected.exists(), "the opted-in user-space DB must be opened/created"
    assert str(expected) in proc.stdout, (
        f"DB() must resolve the user-space path {expected}; got {proc.stdout!r}"
    )


def test_db_path_set_guard_inert(tmp_path, monkeypatch):
    """P2-T32-T31 (AC3): with DB_PATH set, the guard is inert.

    The ``tests/conftest.py`` pattern routes the DB at a temp file; ``DB()``
    must open exactly that file with the guard not firing (opt-in still off).
    """
    db_file = tmp_path / "isolated.sqlite3"
    monkeypatch.setattr(paths, "_DB_FILENAME", str(db_file))
    monkeypatch.setattr(paths, "_app_db_opt_in", False)

    from data.db import DB

    fresh = DB()
    try:
        assert fresh.db_path == db_file, (
            f"DB_PATH set -> open that file; got {fresh.db_path}"
        )
        assert db_file.exists()
    finally:
        fresh.conn.close()
