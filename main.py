import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from config import paths

# ESC-043 limb 2: this is the real application entry point, so opt in to the
# user-space production DB BEFORE anything imports data.db -- data/db.py builds
# its module-level `db = DB()` singleton at import time, and ui.main_window
# imports it. Without this, a normal run from source would trip the guard.
paths.opt_in_production_db()

from config import settings
from ui.main_window import MainWindow


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
    # connection is attempted. A paper-port typo must never silently trade
    # paper while the UI claims to be live.
    try:
        settings.check_live_port()
    except SystemExit as exc:
        QMessageBox.critical(None, "NDThinkChart — cannot start", str(exc))
        return 1

    theme_path = os.path.join(os.path.dirname(__file__), "config", "theme.qss")
    if os.path.exists(theme_path):
        with open(theme_path, "r") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
