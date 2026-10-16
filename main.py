import sys
import os
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMessageBox
from config import paths

# ESC-043 limb 2: this is the real application entry point, so opt in to the
# user-space production DB BEFORE anything imports data.db -- data/db.py builds
# its module-level `db = DB()` singleton at import time, and ui.main_window
# imports it. Without this, a normal run from source would trip the guard.
paths.opt_in_production_db()

from config import settings
from ui.main_window import MainWindow


def main() -> int:
    # Configure pyqtgraph before any widgets are created
    pg.setConfigOption('background', '#0d0f14')
    pg.setConfigOption('foreground', '#a3a3a3')
    pg.setConfigOptions(antialias=True)

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
