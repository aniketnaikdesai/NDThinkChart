"""config/instance_lock.py — one process owns the user-space database (D95).

The guard is about **database ownership** (A240), not window management: the
lock file is derived from the resolved database path, so it sits beside the
database it protects and is named after it. ``config.paths.get_db_path()``
honours ``DB_PATH``, so an override resolves to a different file -- and
therefore to a different lock -- by construction; two differently configured
instances never contend.

``QLockFile`` records the holder's pid and hostname. ``setStaleLockTime(0)``
makes staleness a matter of process liveness (POSIX ``kill(pid, 0)``) rather
than a 30-second timer, so a crashed instance cannot block a restart: the
next start breaks its lock immediately.

The lock is taken by the entry point (``main.main``) before anything imports
the database. It must never be acquired in ``MainWindow.__init__`` or
``data/db.py`` -- hundreds of tests construct one of those and none of them is
a second database owner.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QLockFile, QSysInfo

LOCK_SUFFIX = ".lock"
_APP_NAME = "NDThinkChart"


def lock_path_for(db_path: Path) -> Path:
    """Return the lock file that guards ``db_path``: ``<parent>/<name>.lock``."""
    db_path = Path(db_path)
    return db_path.parent / (db_path.name + LOCK_SUFFIX)


def acquire(db_path: Path) -> tuple[object | None, str]:
    """Take the database-ownership lock for the resolved ``db_path``.

    Returns ``(lock, "")`` when this process now owns the database, or
    ``(None, message)`` when another live process holds it. The message names
    the running instance (pid and host) when ``QLockFile`` can report it; the
    returned lock must be ``unlock()``ed by the caller when it is finished.
    """
    lock = QLockFile(str(lock_path_for(db_path)))
    # PID liveness, not a 30 s timer: a crash must not block a restart.
    lock.setStaleLockTime(0)
    if lock.tryLock(0):
        return lock, ""
    return None, _refusal_message(lock)


def _refusal_message(lock: QLockFile) -> str:
    """The refusal text: who is running, and how to run side by side."""
    ok, pid, hostname, _appname = lock.getLockInfo()
    if ok and pid > 0:
        where = (
            "on this machine"
            if not hostname or hostname == QSysInfo.machineHostName()
            else f"on {hostname}"
        )
        return (
            f"{_APP_NAME} is already running (process {pid} {where}). "
            "Close it to continue, or set DB_PATH to run against a different "
            "database."
        )
    return (
        f"{_APP_NAME} is already running. Close the other instance to "
        "continue, or set DB_PATH to run against a different database."
    )
