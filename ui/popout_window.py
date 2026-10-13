"""ui/popout_window.py — per-ticker pop-out chart windows (D24).

A PopoutChartWindow is a slim, chrome-free window parented to the main window:
a ~28px header (``SYMBOL · timeframe · mode`` + close button) above a
read-only ChartPanel. The panel renders bars, studies, drawings and alarms
live, but drawing / alarm-placement / studies / timeframe / mode interaction
is disabled — the main chart is the sole writer.

The window attaches to the symbol's TickerSession (creating it if needed):
bars, studies, drawings and alarms sync in real time via the session's view
fan-out. The RT subscription is refcounted — one IBKR subscription per symbol
no matter how many pop-outs are open.

Always-on-top defaults to OFF with a per-window toggle in the header
context menu (owner decision 2026-10-12).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from data.popout_store import PopoutStore
from ibkr.pacing import PacingExceeded
from ui.chart_panel import ChartPanel


class PopoutChartWindow(QWidget):
    """A single pop-out chart for one symbol/timeframe/mode snapshot."""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        mode: str,
        extended_hours: bool,
        host,  # MainWindow (duck-typed)
        parent=None,
    ):
        # Always construct as a plain Window; the always-on-top toggle flips
        # the hint at runtime (default OFF per owner decision 2026-10-12).
        super().__init__(parent, Qt.WindowType.Window)

        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.mode = mode
        self.extended_hours = extended_hours
        self._host = host
        self._always_on_top = False

        self.setWindowTitle(f"{self.symbol} · {timeframe} · {mode}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Slim header (~28px).
        header = QWidget(self)
        header.setFixedHeight(28)
        header.setStyleSheet(
            "background: #1a1d24; border-bottom: 1px solid #2a2e38;"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 4, 0)
        self._title_label = QLabel(
            f"{self.symbol} · {timeframe} · {mode}", header
        )
        self._title_label.setStyleSheet(
            "color: #c8ccd4; font-size: 11px; font-weight: 600; "
            "background: transparent; border: none;"
        )
        hl.addWidget(self._title_label, 1)
        # Header context menu (always-on-top toggle) on right-click.
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_header_menu)

        close_btn = QPushButton("✕", header)
        close_btn.setFixedSize(24, 22)
        close_btn.setStyleSheet(
            "QPushButton { color: #8a8f9c; background: transparent; "
            "border: none; font-size: 12px; }"
            "QPushButton:hover { color: #ffffff; background: #3a3f4c; "
            "border-radius: 3px; }"
        )
        close_btn.setToolTip("Close pop-out")
        close_btn.clicked.connect(self.close)
        hl.addWidget(close_btn)
        layout.addWidget(header)

        # Read-only chart panel.
        self.chart = ChartPanel(editable=False)
        self.chart.set_symbol(self.symbol)
        self.chart.set_timeframe(timeframe)
        self.chart.set_extended_hours(extended_hours)
        # Mode is frozen at creation (display-only for pop-outs).
        from ui.chart_panel import ChartMode

        mode_by_label = {
            "Candles": ChartMode.CANDLES,
            "Hollow": ChartMode.HOLLOW,
            "Heikin-Ashi": ChartMode.HEIKIN,
            "Line": ChartMode.LINE,
            "Area": ChartMode.AREA,
        }
        self.chart.set_chart_mode(mode_by_label.get(mode, ChartMode.CANDLES))
        layout.addWidget(self.chart, 1)

        self.resize(640, 420)

        # D24.9: persist geometry on move/resize end (not per-pixel).
        self._geo_timer = QTimer(self)
        self._geo_timer.setSingleShot(True)
        self._geo_timer.setInterval(500)
        self._geo_timer.timeout.connect(self._save_geometry)
        self._popout_id: int | None = None

    # ── Session wiring ────────────────────────────────────────────────

    def attach(self) -> None:
        """Attach to the symbol's session (initial full sync + RT refcount)."""
        session = self._host.get_or_create_session(self.symbol)
        self._session = session
        session.attach_view(self.chart, self.timeframe, sync=True)
        # Live updates: bars, studies, drawings, alarms.
        session.bar_updated.connect(self._on_bar_updated)
        session.bars_refreshed.connect(self._on_bars_refreshed)
        session.alarms_changed.connect(self._on_alarms_changed)
        session.drawings_changed.connect(self._on_drawings_changed)
        try:
            session.ensure_rt_subscribed()
        except PacingExceeded as e:
            # D28.1: pacing-limited subscribes defer via singleShot — never
            # sleep, and never swallow silently. (The old comment claiming
            # "the host's retry path re-attaches" was wrong:
            # _retry_attach_live_feed is main-chart-only.) The view stays
            # registered; sync already happened from cache.
            self._host.status_bar.showMessage(
                f"Pop-out {self.symbol} pacing-limited, "
                f"retrying in {e.wait_seconds:.0f}s…",
                15000,
            )
            QTimer.singleShot(
                int(e.wait_seconds * 1000), self._retry_rt_subscribe
            )
        except Exception:
            # Unexpected subscribe failure: the view stays registered and
            # synced from cache; a later reconnect replays subscriptions.
            pass
        # Track for the MAX_POPOUTS cap and persistence.
        self._host._register_popout(self)
        # D24.9: persist on open.
        self._popout_id = PopoutStore.save(
            self.symbol,
            self.timeframe,
            self.mode,
            self.extended_hours,
            self._geometry_dict(),
        )

    def _retry_rt_subscribe(self) -> None:
        """D28.1: pacing-deferred RT subscribe retry for this pop-out.

        Skips if the pop-out was closed while the retry was pending.
        """
        if self not in self._host._popouts:
            return
        try:
            self._session.ensure_rt_subscribed()
        except PacingExceeded as e:
            QTimer.singleShot(
                int(e.wait_seconds * 1000), self._retry_rt_subscribe
            )
        except Exception:
            pass

    def detach(self) -> None:
        """Release the session (RT refcount + view)."""
        try:
            session = getattr(self, "_session", None)
            if session is not None:
                try:
                    session.bar_updated.disconnect(self._on_bar_updated)
                except (RuntimeError, TypeError):
                    pass
                try:
                    session.bars_refreshed.disconnect(self._on_bars_refreshed)
                except (RuntimeError, TypeError):
                    pass
                try:
                    session.alarms_changed.disconnect(self._on_alarms_changed)
                except (RuntimeError, TypeError):
                    pass
                try:
                    session.drawings_changed.disconnect(
                        self._on_drawings_changed
                    )
                except (RuntimeError, TypeError):
                    pass
                session.release_rt()
                session.detach_view(self.chart)
        finally:
            self._host._unregister_popout(self)

    # ── Session signal slots ──────────────────────────────────────────

    def _on_bar_updated(self, bar, is_new_candle: bool) -> None:
        if bar.timeframe != self.timeframe:
            return
        self.chart.update_last_bar(bar, is_new_candle)

    def _on_bars_refreshed(self, timeframe: str, bars: list) -> None:
        if timeframe != self.timeframe:
            return
        self.chart.update_chart(bars)

    def _on_alarms_changed(self) -> None:
        self.chart.set_alarms(self._session.alarms)

    def _on_drawings_changed(self) -> None:
        self._session.sync_drawings_to_views()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        # D24.9: delete the persisted record on close.
        if self._popout_id is not None:
            try:
                PopoutStore.delete(self._popout_id)
            except Exception:
                pass
        self.detach()
        super().closeEvent(event)

    # ── D24.9 geometry persistence ────────────────────────────────────

    def _geometry_dict(self) -> dict:
        g = self.geometry()
        return {"x": g.x(), "y": g.y(), "w": g.width(), "h": g.height()}

    def _save_geometry(self) -> None:
        try:
            PopoutStore.save(
                self.symbol,
                self.timeframe,
                self.mode,
                self.extended_hours,
                self._geometry_dict(),
            )
        except Exception:
            pass

    def moveEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        super().moveEvent(event)
        self._geo_timer.start()

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        super().resizeEvent(event)
        self._geo_timer.start()

    def apply_geometry(self, geometry: dict) -> None:
        """Restore a saved geometry dict (D24.9)."""
        try:
            self.setGeometry(
                int(geometry.get("x", 100)),
                int(geometry.get("y", 100)),
                int(geometry.get("w", 640)),
                int(geometry.get("h", 420)),
            )
        except (TypeError, ValueError):
            pass

    # ── Header ────────────────────────────────────────────────────────

    def _show_header_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        toggle = menu.addAction("Always on top")
        toggle.setCheckable(True)
        toggle.setChecked(self._always_on_top)
        toggle.triggered.connect(self._toggle_always_on_top)
        header = self.findChild(QWidget)
        menu.exec(header.mapToGlobal(pos) if header else self.mapToGlobal(pos))

    def _toggle_always_on_top(self, checked: bool) -> None:
        self._always_on_top = bool(checked)
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self._always_on_top
        )
        # setWindowFlag hides the window; re-show to apply.
        self.show()
