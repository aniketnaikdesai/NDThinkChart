"""
config/paths.py

Runtime path helpers for bundled builds (PyInstaller / Py2EXE).

When running inside a PyInstaller bundle, files are extracted to a temporary
subdirectory exposed by `sys._MEIPASS`. This module provides utilities to
resolve paths relative to the bundled application folder rather than the
project root, which is essential for accessing bundled resources like
QSS themes and sound assets.

Also provides user-space path resolution for application data (DB, settings,
logs) using the platform-specific user application support directory.
"""

import os
import sys
from pathlib import Path
from config import settings

# Determine if we're running in a PyInstaller bundle
if getattr(sys, "frozen", False):
    # Running in a bundle
    _BASE_DIR = Path(sys._MEIPASS)
else:
    # Running from source
    _BASE_DIR = Path(__file__).parent.parent.resolve()

# User-space paths for application data (DB, settings, logs)
if sys.platform == "darwin":
    # macOS: ~/Library/Application Support/NDThinkChart/
    _USER_APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "NDThinkChart"
elif sys.platform == "win32":
    # Windows: %%LOCALAPPDATA%%\NDThinkChart\
    _USER_APP_SUPPORT_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NDThinkChart"
else:
    # Linux: ~/.local/share/NDThinkChart/
    _USER_APP_SUPPORT_DIR = Path.home() / ".local" / "share" / "NDThinkChart"

_USER_APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)

# Database filename: allow environment override, default to "charting_app.sqlite3"
_DEFAULT_DB_FILENAME = "charting_app.sqlite3"
_DB_FILENAME = os.getenv("DB_PATH", _DEFAULT_DB_FILENAME)

# ESC-043 limb 2: the real application opts in to opening the user-space
# production database. Any other process (offscreen probe, REPL, script) that
# leaves DB_PATH unset must NOT open it -- data.db.DB enforces this.
_app_db_opt_in = False


def opt_in_production_db() -> None:
    """Opt in to opening the user-space production database.

    The real application calls this from its entry point (``main.py``) before
    importing anything that constructs ``data.db.DB`` (whose module-level
    singleton opens the DB at import time). Non-app processes must instead
    export ``DB_PATH`` to a temp file (architecture S12).
    """
    global _app_db_opt_in
    _app_db_opt_in = True


def is_production_db_opted_in() -> bool:
    """True when the real application has opted in to the user-space DB."""
    return _app_db_opt_in


def uses_production_db() -> bool:
    """True when ``DB_PATH`` is unset, so ``get_db_path()`` resolves to the
    owner's user-space production database."""
    return _DB_FILENAME == _DEFAULT_DB_FILENAME


def production_db_path() -> Path:
    """Return the canonical user-space production database path."""
    return get_user_data_path(_DEFAULT_DB_FILENAME)


def get_resource_path(filename: str) -> Path:
    """
    Return absolute path to a resource file within the bundle.

    This is intended for accessing bundled assets (e.g., QSS theme files,
    pre-rendered sound files) that are packaged alongside the executable.
    """
    return _BASE_DIR / filename


def get_user_data_path(filename: str | None = None) -> Path:
    """
    Return absolute path to a user-space data file (DB, logs, etc.).

    Files created here persist across app launches and survive updates.
    If filename is None, returns the user data directory itself.
    """
    if filename is None:
        return _USER_APP_SUPPORT_DIR
    return _USER_APP_SUPPORT_DIR / filename


def get_db_path() -> Path:
    """
    Return the canonical path to the application database.

    Production: user-space directory (e.g., ~/Library/Application Support/NDThinkChart/)
    Development: project-relative path if not in user-space (for local testing)
    """
    # If DB_PATH is set and we're not running from the project source,
    # use it relative to user app support directory
    if _DB_FILENAME != "charting_app.sqlite3":
        return get_user_data_path(_DB_FILENAME)

    # Production path: user-space only
    return get_user_data_path(_DB_FILENAME)


def is_bundled() -> bool:
    """Return True if running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def print_paths() -> None:
    """Debug helper to print resolved paths."""
    print(f"Platform: {sys.platform}")
    print(f"Is bundled: {is_bundled()}")
    print(f"Base dir: {_BASE_DIR}")
    print(f"User app support dir: {_USER_APP_SUPPORT_DIR}")
    print(f"DB filename: {_DB_FILENAME}")
    print(f"DB path: {get_db_path()}")


if __name__ == "__main__":
    print_paths()