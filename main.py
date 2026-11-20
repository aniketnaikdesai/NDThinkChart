import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from config import instance_lock, paths

# ESC-043 limb 2: this is the real application entry point, so opt in to the
# user-space production DB BEFORE anything imports data.db -- data/db.py builds
# its module-level `db = DB()` singleton at import time, and ui.main_window
# imports it. Without this, a normal run from source would trip the guard.
paths.opt_in_production_db()

from config import settings


def _register_lwc_scheme_before_qapp() -> None:
    """Register the ``ndt://`` scheme at import time — the ORDER is required.

    ``QWebEngineUrlScheme.registerScheme()`` is only honoured before a
    ``QApplication`` exists, and QtWebEngine itself must be imported before
    one too. ``ui/lwc_host`` is otherwise imported lazily by the engine
    factory, *after* ``QApplication`` — where the QtWebEngine import fails,
    ``HAS_WEBENGINE`` is False, ``LwcChartView.ensure_host()`` raises and the
    chart area stays blank while bars still load. This call therefore lives
    at module level (above ``main()``) and must never move below the
    ``QApplication(sys.argv)`` line.

    Silent no-op when the LWC engine (PyQt6-WebEngine) is not installed:
    startup must never fail over the scheme.
    """
    try:
        from ui.lwc_host import register_ndt_scheme
    except Exception:  # pragma: no cover — engine-less box
        return
    try:
        register_ndt_scheme()
    except Exception:  # pragma: no cover — never break startup
        pass


_register_lwc_scheme_before_qapp()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # D26.5: fail fast unless configured for the live TWS port — before any
    # connection is attempted. This is a configuration check: it verifies the
    # configured port only, not the TWS account behind it, and the app places
    # no orders.
    # D94: this is also where a malformed IBKR_PORT/IBKR_CLIENT_ID is refused —
    # settings' import keeps the raw value so the message can name it, and this
    # guard runs after QApplication, so the refusal is a dialog rather than a
    # bare ValueError raised while main was being imported.
    try:
        settings.check_live_port()
    except SystemExit as exc:
        QMessageBox.critical(None, "NDThinkChart — cannot start", str(exc))
        return 1

    # D95 / S-P28-7: one process owns the user-space database. The lock is
    # keyed on the RESOLVED DB path (so a DB_PATH override is an independent
    # instance by construction) and is taken here -- after the port guard and
    # BEFORE the window/DB import below -- so a second instance refuses without
    # ever opening a second SQLite writer.
    lock, refusal = instance_lock.acquire(paths.get_db_path())
    if lock is None:
        QMessageBox.critical(None, "NDThinkChart — already running", refusal)
        return 1

    try:
        # D86 / S-P28-5: the window import constructs the DB singleton, and that
        # singleton's open can skip a migration for a machine reason (an
        # unverifiable pre-drop backup). Importing it HERE — after QApplication,
        # the port guard and the instance lock — means such a condition can be
        # reported through a dialog instead of killing the process before any UI
        # exists. It also means the DB is constructed while the lock is held.
        from data import db as db_module
        from ui.main_window import MainWindow

        for notice in db_module.startup_notices():
            QMessageBox.warning(
                None, "NDThinkChart — database migration skipped", notice)

        theme_path = os.path.join(os.path.dirname(__file__), "config", "theme.qss")
        if os.path.exists(theme_path):
            with open(theme_path, "r") as f:
                app.setStyleSheet(f.read())

        window = MainWindow()
        window.show()

        return app.exec()
    finally:
        lock.unlock()


if __name__ == "__main__":
    sys.exit(main())
