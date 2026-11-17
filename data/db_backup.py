"""Pre-drop backup for the one-time D65 schema drop (AC-D65.18).

``DB._migrate_schema`` drops ``position_group_map``, ``positions`` and
``trade_groups`` once. That drop is irreversible, so it must never run without
a verified copy of the database beside it: this module copies the SQLite file,
opens the **copy** read-only and proves it holds the three tables (with their
row counts) before the caller executes a single ``DROP``. Any failure raises
``BackupVerificationError``; the caller must then skip the drop.

The application database is never opened here — not even read-only through
``data.db`` — so the ESC-043 production-DB opt-in gate is untouched. The copy
is opened through a ``mode=ro`` URI, which cannot write to the backup.
"""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from config import paths

#: Filename stem of the pre-D65 copy, completed with ``<YYYYMMDD-HHMMSS>``.
BACKUP_STEM = "charting_app_pre-D65"

#: The tables whose survival the copy must prove before the drop may run.
REQUIRED_TABLES = ("positions", "trade_groups", "position_group_map")


class BackupVerificationError(RuntimeError):
    """The pre-drop copy could not be created or verified; do not drop."""


class VerifiedBackupPath(type(Path())):
    """The verified copy's path, carrying the row counts read from the copy.

    Subclasses the platform's concrete ``Path`` class (``type(Path())``, the
    pathlib idiom) so ``backup_before_drop``'s declared ``-> Path`` contract
    holds, while the verified row counts are still returned to the caller
    (AC-D65.18) instead of being logged and lost.
    """

    __slots__ = ("row_counts",)

    def __new__(cls, *args, row_counts: dict[str, int] | None = None, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        self.row_counts = dict(row_counts or {})
        return self


def backup_before_drop(
    db_path: Path,
    now: datetime | None = None,
    backup_dir: Path | None = None,
) -> Path:
    """Copy ``db_path`` into the backups directory and verify the copy.

    Args:
        db_path: The application database about to be migrated.
        now: Timestamp for the filename (tests inject this); local time.
        backup_dir: Destination directory; defaults to
            ``config.paths.get_user_data_path("backups")``.

    Returns:
        A ``VerifiedBackupPath`` (a ``Path``) for
        ``charting_app_pre-D65_<YYYYMMDD-HHMMSS>.sqlite3`` whose
        ``row_counts`` maps each required table to its row count in the copy.

    Raises:
        BackupVerificationError: The copy could not be made, is not a readable
            SQLite database, fails ``PRAGMA integrity_check``, or lacks any of
            ``positions``/``trade_groups``/``position_group_map``.
    """
    source = Path(db_path)
    target_dir = (
        Path(backup_dir)
        if backup_dir is not None
        else paths.get_user_data_path("backups")
    )
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    backup_path = target_dir / f"{BACKUP_STEM}_{timestamp}.sqlite3"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup_path)
    except OSError as exc:
        raise BackupVerificationError(
            f"could not copy {source} to {backup_path}: {exc}"
        ) from exc

    row_counts = verify_backup_copy(backup_path)
    return VerifiedBackupPath(backup_path, row_counts=row_counts)


def verify_backup_copy(backup_path: Path) -> dict[str, int]:
    """Verify ``backup_path`` read-only and return the three row counts.

    Opens the copy through ``file:...?mode=ro`` — never the application DB —
    and requires ``PRAGMA integrity_check == "ok"`` plus every name in
    ``REQUIRED_TABLES``. Raises ``BackupVerificationError`` on any failure.
    """
    path = Path(backup_path)
    try:
        # mode=ro makes the read-only intent enforced, not merely intended.
        conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    except sqlite3.Error as exc:
        raise BackupVerificationError(
            f"could not open the backup copy {path}: {exc}"
        ) from exc

    try:
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.Error as exc:
            raise BackupVerificationError(
                f"the backup copy {path} is not a readable SQLite database: {exc}"
            ) from exc
        if not integrity or integrity[0] != "ok":
            raise BackupVerificationError(
                f"the backup copy {path} failed integrity_check: {integrity!r}"
            )

        row_counts: dict[str, int] = {}
        missing: list[str] = []
        for table in REQUIRED_TABLES:
            try:
                row_counts[table] = conn.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
            except sqlite3.Error:
                missing.append(table)
        if missing:
            raise BackupVerificationError(
                f"the backup copy {path} is missing required table(s): "
                + ", ".join(missing)
            )
    finally:
        conn.close()

    return row_counts
