"""D95 / P28-06 — one process owns the user-space database.

The guard is keyed on the RESOLVED database path, so a ``DB_PATH`` override is
an independent instance by construction; its staleness is PID-based, so a crash
does not block a restart; and it is taken in ``main()`` after the port guard and
*before* the window import that constructs the DB.

Case (a) is a genuine two-process case: a holder child acquires the lock, a
second child runs the real ``main()`` against the same absolute temp DB path,
and an in-process probe re-checks that the holder kept it. No database file is
created because the refusal happens before ``data.db`` is imported.
"""

from __future__ import annotations

import inspect
import json
import os
import select
import subprocess
import sys
import time
import types
from pathlib import Path

from config import instance_lock, paths

REPO_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# Child-process helpers (two-process harness)
# --------------------------------------------------------------------------

_HOLDER_SOURCE = """\
import sys

sys.path.insert(0, sys.argv[1])

from pathlib import Path

from config import instance_lock

lock, message = instance_lock.acquire(Path(sys.argv[2]))
if lock is None:
    print("REFUSED " + message, flush=True)
    sys.exit(2)
print("HELD", flush=True)
sys.stdin.readline()
lock.unlock()
print("RELEASED", flush=True)
"""

_SECOND_SOURCE = """\
import json
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

from config import paths
import main as entry


class _Dialogs:
    calls = []

    @classmethod
    def critical(cls, parent, title, text):
        cls.calls.append([title, text])
        return 0

    @classmethod
    def warning(cls, parent, title, text):
        cls.calls.append([title, text])
        return 0


entry.QMessageBox = _Dialogs
code = entry.main()
db_path = paths.get_db_path()
print(json.dumps({
    "rc": code,
    "dialogs": _Dialogs.calls,
    "db_path": str(db_path),
    "db_exists": Path(db_path).exists(),
    "db_imported": "data.db" in sys.modules,
    "window_imported": "ui.main_window" in sys.modules,
}))
"""


def _child_env(db_path: Path) -> dict[str, str]:
    """A hermetic child environment: its own DB, offscreen Qt, live port."""
    env = dict(os.environ)
    env["DB_PATH"] = str(db_path)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["IBKR_PORT"] = "7496"
    env["IBKR_CLIENT_ID"] = "1"
    env.pop("PYTEST_CURRENT_TEST", None)
    return env


def _write_child_script(tmp_path: Path, name: str, source: str) -> Path:
    script = tmp_path / name
    script.write_text(source)
    return script


def _spawn_lock_holder(tmp_path: Path, db_path: Path, env: dict[str, str]):
    script = _write_child_script(tmp_path, "d95_holder.py", _HOLDER_SOURCE)
    proc = subprocess.Popen(
        [sys.executable, str(script), str(REPO_ROOT), str(db_path)],
        cwd=str(REPO_ROOT),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    ready, _, _ = select.select([proc.stdout], [], [], 30)
    if not ready:
        proc.kill()
        proc.wait(timeout=30)
        raise AssertionError("lock holder did not report readiness")
    line = proc.stdout.readline().strip()
    if line != "HELD":
        proc.kill()
        proc.wait(timeout=30)
        raise AssertionError(
            f"lock holder did not acquire the lock: {line!r} "
            f"{proc.stderr.read()}"
        )
    return proc


def _stop_lock_holder(proc) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.stdin.write("\n")
        proc.stdin.flush()
    except (BrokenPipeError, ValueError):
        pass
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=30)


# --------------------------------------------------------------------------
# (a) AC-D95.1 — the second instance refuses and opens no database
# --------------------------------------------------------------------------


def test_second_instance_refuses_before_opening_the_database(tmp_path):
    db_path = tmp_path / "p28_instance.sqlite3"
    env = _child_env(db_path)

    holder = _spawn_lock_holder(tmp_path, db_path, env)
    try:
        second_script = _write_child_script(
            tmp_path, "d95_second.py", _SECOND_SOURCE)
        second = subprocess.run(
            [sys.executable, str(second_script), str(REPO_ROOT), str(db_path)],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert second.returncode == 0, second.stderr
        payload = json.loads(second.stdout.strip().splitlines()[-1])

        # The second instance refused, with a dialog-named refusal.
        assert payload["rc"] == 1, payload
        assert payload["dialogs"], payload
        title, message = payload["dialogs"][-1]
        assert title == "NDThinkChart — already running"
        assert "already running" in message
        assert str(holder.pid) in message
        # ... and it never reached the DB/window import that would have made it
        # a second writer (the temp file would exist after sqlite3.connect).
        assert payload["db_imported"] is False, payload
        assert payload["window_imported"] is False, payload
        assert payload["db_exists"] is False, payload
        assert not db_path.exists()

        # A third probe still refuses: the first instance still owns the lock.
        probe, refusal = instance_lock.acquire(db_path)
        assert probe is None
        assert "already running" in refusal
        assert str(holder.pid) in refusal
        assert instance_lock.lock_path_for(db_path).exists()
        assert not db_path.exists()
    finally:
        _stop_lock_holder(holder)
    assert holder.returncode == 0


# --------------------------------------------------------------------------
# (b) AC-P28-06-1 — path derivation and no contention across DB_PATH values
# --------------------------------------------------------------------------


def test_lock_path_is_derived_from_the_db_path(tmp_path):
    one = tmp_path / "one.sqlite3"
    two = tmp_path / "elsewhere" / "two.sqlite3"
    two.parent.mkdir()

    assert instance_lock.LOCK_SUFFIX == ".lock"
    assert instance_lock.lock_path_for(one) == tmp_path / "one.sqlite3.lock"
    assert (
        instance_lock.lock_path_for(two)
        == two.parent / "two.sqlite3.lock"
    )

    # Two different DB_PATH values are two different instances: both acquire.
    first, first_message = instance_lock.acquire(one)
    second, second_message = instance_lock.acquire(two)
    try:
        assert first is not None, first_message
        assert first_message == ""
        assert second is not None, second_message
        assert second_message == ""
        assert instance_lock.lock_path_for(one).exists()
        assert instance_lock.lock_path_for(two).exists()

        # Same path, same process: the held lock still refuses.
        again, refusal = instance_lock.acquire(one)
        assert again is None
        assert "already running" in refusal
    finally:
        for lock in (first, second):
            if lock is not None:
                lock.unlock()


# --------------------------------------------------------------------------
# (c) AC-P28-06-1 — a crashed holder's lock is broken by PID liveness
# --------------------------------------------------------------------------


def test_dead_pid_lock_is_broken_without_the_30s_timer(tmp_path):
    db_path = tmp_path / "crashed.sqlite3"
    env = _child_env(db_path)

    # A real QLockFile held by a process that is then killed: the file stays.
    crashed = _spawn_lock_holder(tmp_path, db_path, env)
    crashed.kill()
    crashed.wait(timeout=30)
    assert instance_lock.lock_path_for(db_path).exists()

    started = time.monotonic()
    lock, message = instance_lock.acquire(db_path)
    elapsed = time.monotonic() - started
    try:
        assert lock is not None, message
        assert message == ""
        # PID liveness, not a 30 s timer.
        assert elapsed < 5.0, f"stale lock took {elapsed:.1f}s to break"
    finally:
        if lock is not None:
            lock.unlock()


# --------------------------------------------------------------------------
# (d) AC-D95.2 — no second writer, and the upsert stays idempotent
# --------------------------------------------------------------------------


def test_lock_precedes_the_window_import_and_popout_save_is_idempotent():
    import main as entry

    source = inspect.getsource(entry.main)
    lock_at = source.index("instance_lock.acquire")
    db_at = source.index("from data import db as db_module")
    window_at = source.index("from ui.main_window import MainWindow")
    assert lock_at < db_at, "the lock must be taken before data.db is imported"
    assert lock_at < window_at, "the lock must be taken before the window import"
    assert lock_at < source.index("app.exec()")
    assert source.index("finally:") < source.index("lock.unlock()")

    # Within one process the guard removes the cross-process duplicate; the
    # store's SELECT-then-write upsert is unchanged and still yields one row.
    from data import db as db_module
    from data.popout_store import PopoutStore

    first = PopoutStore.save(
        "AAPL", "5 mins", "candles", False, {"x": 1}, tz_offset=0.0)
    second = PopoutStore.save(
        "AAPL", "5 mins", "candles", False, {"x": 2}, tz_offset=0.0)
    assert first == second
    rows = db_module.db.conn.execute(
        "SELECT COUNT(*) FROM popouts "
        "WHERE symbol=? AND timeframe=? AND mode=?",
        ("AAPL", "5 mins", "candles"),
    ).fetchone()[0]
    assert rows == 1


# --------------------------------------------------------------------------
# (e) AC-P28-06-2 — a clean return releases the lock, and leaves no file
# --------------------------------------------------------------------------


def test_clean_exit_releases_the_lock(monkeypatch):
    import main as entry

    class _FakeApp:
        def setStyle(self, *args):
            return None

        def setStyleSheet(self, *args):
            return None

        def exec(self):
            return 0

    class _FakeWindow:
        def show(self):
            return None

    calls = []

    class _Dialogs:
        @staticmethod
        def critical(parent, title, text):
            calls.append((title, text))
            return 0

        @staticmethod
        def warning(parent, title, text):
            calls.append((title, text))
            return 0

    fake_window_module = types.ModuleType("ui.main_window")
    fake_window_module.MainWindow = _FakeWindow
    monkeypatch.setitem(sys.modules, "ui.main_window", fake_window_module)
    monkeypatch.setattr(entry, "QApplication", lambda *a, **k: _FakeApp())
    monkeypatch.setattr(entry, "QMessageBox", _Dialogs)
    # The port guard must pass for the lock branch to be the one exercised.
    monkeypatch.setattr(entry.settings, "IBKR_PORT", 7496, raising=False)
    monkeypatch.setattr(entry.settings, "_PORT_PARSE_ERROR", None, raising=False)

    db_path = paths.get_db_path()
    lock_path = instance_lock.lock_path_for(db_path)
    assert not lock_path.exists()

    assert entry.main() == 0
    assert not calls, calls
    assert not lock_path.exists(), "the lock file outlived main()"

    # ... and the next start can take it.
    following, message = instance_lock.acquire(db_path)
    try:
        assert following is not None, message
    finally:
        if following is not None:
            following.unlock()

    # No lock file is left in the repo or the project directory.
    assert not (REPO_ROOT / "charting_app.sqlite3.lock").exists()
    assert list(REPO_ROOT.glob("*.lock")) == []
