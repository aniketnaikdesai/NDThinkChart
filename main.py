import sys
import os
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    # Configure pyqtgraph before any widgets are created
    pg.setConfigOption('background', '#0d0f14')
    pg.setConfigOption('foreground', '#a3a3a3')
    pg.setConfigOptions(antialias=True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    theme_path = os.path.join(os.path.dirname(__file__), "config", "theme.qss")
    if os.path.exists(theme_path):
        with open(theme_path, "r") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
