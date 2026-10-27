"""ui/popout_window.py — per-ticker pop-out chart windows (D24, P6-11).

A PopoutChartWindow is a slim, chrome-free window parented to the main window:
a ~28px header (``SYMBOL · timeframe · mode`` + close button) above a
read-only chart view. The panel renders bars, studies, drawings and alarms
live, but drawing / alarm-placement / studies / timeframe / mode interaction
is disabled — the main chart is the sole writer.

The view is created through ``ui.chart_view.create_chart_view``, so a pop-out
re-hosts on whichever engine the seam resolves: pyqtgraph stays present and
default (``NDT_CHART_ENGINE`` unset), and the ``"lwc"`` value gives the LWC
driver. Both views satisfy the same session surface the fan-out needs
(``update_chart`` / ``set_studies`` / ``drawing_overlay.set_data`` /
``set_alarms``), so D24's single-writer invariant and the pop-out cap
(``MAX_POPOUTS = 10``, Q62/A107) are engine-independent.

Each pop-out accounts its own memory in ``POPOUT_MEMORY_LEDGER`` (DG90) and
releases it on close, so 1/3/6 pop-outs are auditable per window rather than
as one opaque total.

The window attaches to the symbol's TickerSession (creating it if needed):
bars, studies, drawings and alarms sync in real time via the session's view
fan-out. The RT subscription is refcounted — one IBKR subscription per symbol
no matter how many pop-outs are open.

Always-on-top defaults to OFF with a per-window toggle in the header
context menu (owner decision 2026-10-12).
"""

from __future__ import annotations

import itertools

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
from ui.chart_view import create_chart_view

#: Mode label (the header/host text) → the LWC driver's mode name.
MODE_NAMES = {
    "Candles": "candles",
    "Hollow": "hollow",
    "Heikin-Ashi": "heikin",
    "Line": "line",
    "Area": "area",
}

#: DG90: one ledger entry per open pop-out, keyed by its pop-out serial.
POPOUT_MEMORY_LEDGER: dict[int, dict] = {}

#: DG90: bytes budgeted per stored bar when a view reports no account itself
#: (the pyqtgraph panel keeps a plain list of bars, nothing else per view).
BAR_BYTES = 128

_popout_serials = itertools.count(1)


def popout_view(tz_offset: float = 0.0):
    """The read-only chart view for one pop-out, on the resolved engine.

    ``ui.chart_view.create_chart_view`` is the single engine-selection
    authority (``NDT_CHART_ENGINE``, then the persisted override; anything
    other than ``"lwc"`` → pyqtgraph, which stays present and default). Its
    LWC branch is still the Phase-1a seam stub — the render driver's factory
    wiring is cutover work — so when the factory resolves ``"lwc"`` a pop-out
    re-hosts the real driver, composed directly exactly as the phase suites
    compose it. No engine name is resolved here: the factory decides.
    """
    view = create_chart_view(tz_offset=tz_offset, editable=False)
    if getattr(view, "ENGINE_NAME", None) != "lwc":
        return view
    from ui.lwc_view import LwcChartView as LwcDriverView

    if isinstance(view, LwcDriverView):
        return view
    view.deleteLater()
    return LwcDriverView(tz_offset=tz_offset, editable=False)


def view_memory_estimate(view) -> dict:
    """DG90 memory account for one pop-out's view.

    Engine views that can account themselves (the LWC driver's
    ``memory_bytes``) are asked; the pyqtgraph panel has no per-view transport
    or overlay arrays of its own — its bars list is the pop-out's private copy
    — so it is accounted from that list.
    """
    reporter = getattr(view, "memory_bytes", None)
    if callable(reporter):
        try:
            return dict(reporter())
        except Exception:
            pass
    bars = len(list(getattr(view, "_bars", None) or []))
    return {
        "engine": getattr(view, "ENGINE_NAME", type(view).__name__),
        "popout": True,
        "bars": bars,
        "buckets": {"bars": bars * BAR_BYTES},
        "total_bytes": bars * BAR_BYTES,
        "bridge": {},
    }


def popout_memory_ledger() -> dict[int, dict]:
    """Snapshot of the DG90 ledger — one entry per open pop-out window."""
    return {key: dict(value) for key, value in POPOUT_MEMORY_LEDGER.items()}


def popout_memory_total() -> int:
    """Total bytes accounted across every open pop-out (DG90)."""
    return sum(int(entry.get("total_bytes", 0))
               for entry in POPOUT_MEMORY_LEDGER.values())


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

        # Read-only chart view, on whichever engine the seam resolves.
        self.chart = popout_view(tz_offset=0.0)
        self.chart.set_symbol(self.symbol)
        self.chart.set_timeframe(timeframe)
        self.chart.set_extended_hours(extended_hours)
        # Mode is frozen at creation (display-only for pop-outs).
        self._apply_mode(mode)
        layout.addWidget(self.chart, 1)

        self.resize(640, 420)

        # D24.9: persist geometry on move/resize end (not per-pixel).
        self._geo_timer = QTimer(self)
        self._geo_timer.setSingleShot(True)
        self._geo_timer.setInterval(500)
        self._geo_timer.timeout.connect(self._save_geometry)
        self._popout_id: int | None = None
        # P6-11/DG90: per-pop-out memory account (ledger key + last report).
        self.memory_id: int = next(_popout_serials)
        self.memory: dict = {}
        self._engine_host = None

    # ── Engine-neutral view helpers ───────────────────────────────────

    def _apply_mode(self, mode: str) -> None:
        """Apply the snapshot's mode on the LWC view (frozen for pop-outs)."""
        set_mode = getattr(self.chart, "set_mode", None)
        if set_mode is not None:
            set_mode(MODE_NAMES.get(mode, "candles"))

    def _push_bars(self, bars: list) -> None:
        """Full-series replace on either engine (``update_chart``/``update_bars``)."""
        update = getattr(self.chart, "update_chart", None)
        if update is None:
            update = getattr(self.chart, "update_bars", None)
        if update is not None:
            update(list(bars or []))

    def _ensure_engine_host(self) -> None:
        """Give this pop-out its own offline host, when the engine is present.

        The D47 host is per view (``ensure_host``); each pop-out therefore owns
        one rather than sharing the main chart's. Engine-less CI (DG88) has no
        Chromium: ``ensure_host`` raises, the view still syncs through its
        bridge, and the pop-out never depends on the host existing.
        """
        ensure = getattr(self.chart, "ensure_host", None)
        if not callable(ensure):
            return
        try:
            self._engine_host = ensure()
        except Exception:
            self._engine_host = None

    # ── DG90 memory accounting ────────────────────────────────────────

    @property
    def memory_bytes(self) -> int:
        """This pop-out's accounted bytes (0 once released)."""
        return int(self.memory.get("total_bytes", 0))

    def _account_memory(self) -> None:
        """Record (or refresh) this pop-out's DG90 ledger entry."""
        self.memory = view_memory_estimate(self.chart)
        self.memory.update({
            "id": self.memory_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "mode": self.mode,
            "host": self._engine_host is not None,
        })
        POPOUT_MEMORY_LEDGER[self.memory_id] = self.memory

    def _release_memory(self) -> None:
        """Release the ledger entry and the view's arrays on close (DG90)."""
        POPOUT_MEMORY_LEDGER.pop(self.memory_id, None)
        self.memory = {}
        release = getattr(self.chart, "release_resources", None)
        if callable(release):
            try:
                release()
            except Exception:
                pass

    # ── Session wiring ────────────────────────────────────────────────

    def attach(self) -> None:
        """Attach to the symbol's session (initial full sync + RT refcount)."""
        self._ensure_engine_host()
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
        # P6-11/DG90: account this pop-out's memory (per window).
        self._account_memory()
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
            # P6-11/DG90: release this pop-out's accounted memory (no leak).
            self._release_memory()

    # ── Session signal slots ──────────────────────────────────────────

    def _on_bar_updated(self, bar, is_new_candle: bool) -> None:
        if bar.timeframe != self.timeframe:
            return
        self.chart.update_last_bar(bar, is_new_candle)

    def _on_bars_refreshed(self, timeframe: str, bars: list) -> None:
        if timeframe != self.timeframe:
            return
        self._push_bars(bars)
        # DG90: a full replace is the one sync that changes the view's
        # accounted size materially (and the replay log always grows).
        self._account_memory()

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
