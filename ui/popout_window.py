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
import logging

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

_LOG = logging.getLogger(__name__)

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
        except Exception as exc:
            # Q-43: accounting probe failed — logged, falls back to bars.
            _LOG.debug("memory_bytes probe failed: %s: %s",
                       type(exc).__name__, exc)
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
        tz_offset: float = 0.0,
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
        # D49.6: threaded from the main chart's current offset via _open_popout
        # (never the hardcoded 0.0).
        self.chart = popout_view(tz_offset=tz_offset)
        self.chart.set_symbol(self.symbol)
        self.chart.set_timeframe(timeframe)
        self.chart.set_extended_hours(extended_hours)
        # Mode is frozen at creation (display-only for pop-outs).
        self._apply_mode(mode)
        layout.addWidget(self.chart, 1)

        # D49.3 (ESC-070 model): in-pop-out host-failure error state. A
        # dedicated message area plus a status strip, both hidden until a
        # chart host fails at startup. The text reuses
        # ``chart_engine_failure_message`` verbatim (never reworded) and the
        # widget is a distinct object from the chart itself, so the failure
        # state is unambiguous versus the no-data (blank-chart) state.
        self.chart_engine_failed = False
        self._engine_error_label = QLabel("", self)
        self._engine_error_label.setObjectName("PopoutEngineError")
        self._engine_error_label.setWordWrap(True)
        self._engine_error_label.setStyleSheet(
            "background: #2a1d1d; color: #f0a8a8; font-size: 12px; "
            "padding: 8px; border-top: 1px solid #5a2a2a;"
        )
        self._engine_error_label.hide()
        layout.addWidget(self._engine_error_label)
        self._status_label = QLabel("", self)
        self._status_label.setObjectName("PopoutStatus")
        self._status_label.setStyleSheet(
            "background: #1a1d24; color: #c8ccd4; font-size: 11px; "
            "padding: 2px 8px; border-top: 1px solid #2a2e38;"
        )
        self._status_label.hide()
        layout.addWidget(self._status_label)

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

    def _show_engine_failure_state(self, engine_name: str) -> None:
        """D49.3: surface a host-startup failure in the pop-out (ESC-070 model).

        Shows the dedicated message area plus the status strip, both carrying
        the ``chart_engine_failure_message`` wording verbatim, and records
        the ``chart_engine_failed`` flag mirroring the main window. The
        diagnostic log entry stays in ``_ensure_engine_host`` at its current
        level; this method only presents the state.
        """
        # Lazy import: ui.main_window reaches back into this module at call
        # sites, so a top-level import would risk a cycle.
        from ui.main_window import chart_engine_failure_message

        message = chart_engine_failure_message(engine_name)
        self.chart_engine_failed = True
        self._engine_error_label.setText(message)
        self._engine_error_label.show()
        self._status_label.setText(message)
        self._status_label.show()

    def _ensure_engine_host(self) -> None:
        """Give this pop-out its own offline host, when the engine is present.

        The D47 host is per view (``ensure_host``); each pop-out therefore owns
        one rather than sharing the main chart's. Engine-less CI (DG88) has no
        Chromium: ``ensure_host`` raises, the view still syncs through its
        bridge, and the pop-out never depends on the host existing.

        D49.3: a host that raises on startup additionally surfaces the ESC-070
        error state in the pop-out (message area + status text, verbatim
        wording). The diagnostic log below is retained at its current level.
        """
        ensure = getattr(self.chart, "ensure_host", None)
        if not callable(ensure):
            return
        try:
            self._engine_host = ensure()
        except Exception as exc:
            # Q-43: offline-host best-effort — logged, view still syncs.
            _LOG.debug("Pop-out %s engine host unavailable: %s: %s",
                       self.symbol, type(exc).__name__, exc)
            self._engine_host = None
            self._show_engine_failure_state(
                getattr(self.chart, "ENGINE_NAME", "unknown")
            )

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
            except Exception as exc:
                # Q-43: true teardown cleanup — stays best-effort, logged.
                _LOG.debug("Pop-out %s release_resources failed: %s: %s",
                           self.symbol, type(exc).__name__, exc)

    # ── Session wiring ────────────────────────────────────────────────

    def attach(self) -> None:
        """Attach to the symbol's session (initial full sync + RT refcount).

        Transactional (S-P13-2, D49.2): each step records what it acquired
        — connected signals, attached view, RT hold (set ONLY where
        ``ensure_rt_subscribed`` returned), registration, resources — and
        ANY failure unwinds exactly what this attach acquired: disconnect
        connected signals first (R97, so a concurrent session update never
        iterates a half-detached view), detach the view via the frozen
        ``TickerSession.detach_view``, release the RT hold only if this
        attach acquired one, unregister, release resources. A hold acquired
        means ``ensure_rt_subscribed`` returned without raising (whether it
        created the subscription or bumped the refcount); a raise (pacing
        or otherwise) means no hold was acquired and unwind releases none —
        never another view's hold. The session reference is dropped on
        failure so a later ``detach()`` is a safe no-op for the RT/view
        block (disconnects stay best-effort, unregister + memory release
        still run in its ``finally``).
        """
        self._ensure_engine_host()
        session = self._host.get_or_create_session(self.symbol)
        self._session = session
        connected: list = []
        view_attached = False
        hold_acquired = False
        registered = False
        resources_acquired = False
        try:
            session.attach_view(self.chart, self.timeframe, sync=True)
            view_attached = True
            # Live updates: bars, studies, drawings, alarms.
            for signal, slot in (
                (session.bar_updated, self._on_bar_updated),
                (session.bars_refreshed, self._on_bars_refreshed),
                (session.alarms_changed, self._on_alarms_changed),
                (session.drawings_changed, self._on_drawings_changed),
            ):
                signal.connect(slot)
                connected.append((signal, slot))
            try:
                session.ensure_rt_subscribed()
            except PacingExceeded as e:
                # D28.1: pacing-limited subscribes defer via singleShot — never
                # sleep, and never swallow silently. (The old comment claiming
                # "the host's retry path re-attaches" was wrong:
                # _retry_attach_live_feed is main-chart-only.) The view stays
                # registered; sync already happened from cache. No hold was
                # acquired (the call raised), so unwind releases none.
                self._host.status_bar.showMessage(
                    f"Pop-out {self.symbol} pacing-limited, "
                    f"retrying in {e.wait_seconds:.0f}s…",
                    15000,
                )
                QTimer.singleShot(
                    int(e.wait_seconds * 1000), self._retry_rt_subscribe
                )
            except Exception as exc:
                # Q-43: unexpected (non-pacing) subscribe failure — surfaced like
                # the pacing branch (status + stream health + the same singleShot
                # retry) instead of discarded. The view stays registered and
                # synced from cache so the session stays consistent. No hold
                # was acquired (the call raised), so unwind releases none.
                _LOG.warning(
                    "Pop-out %s RT subscribe failed (%s: %s); retrying…",
                    self.symbol, type(exc).__name__, exc,
                )
                try:
                    session.stream_health.mark_failed(
                        -1, f"pop-out subscribe failed: {exc}"
                    )
                except Exception as health_exc:
                    _LOG.debug(
                        "Pop-out %s stream-health mark failed: %s: %s",
                        self.symbol, type(health_exc).__name__, health_exc,
                    )
                self._host.status_bar.showMessage(
                    f"Pop-out {self.symbol} subscription failed, retrying in 5s…",
                    15000,
                )
                QTimer.singleShot(5000, self._retry_rt_subscribe)
            else:
                hold_acquired = True
            # Track for the MAX_POPOUTS cap and persistence.
            self._host._register_popout(self)
            registered = True
            # P6-11/DG90: account this pop-out's memory (per window).
            self._account_memory()
            resources_acquired = True
            # D24.9: persist on open.
            self._popout_id = PopoutStore.save(
                self.symbol,
                self.timeframe,
                self.mode,
                self.extended_hours,
                self._geometry_dict(),
            )
        except Exception as exc:
            _LOG.warning(
                "Pop-out %s attach failed (%s: %s); unwinding "
                "signals=%d view=%s hold=%s registered=%s resources=%s",
                self.symbol, type(exc).__name__, exc, len(connected),
                view_attached, hold_acquired, registered, resources_acquired,
            )
            # R97: disconnect-signals-first — a concurrent session update
            # must never iterate a half-detached view.
            for signal, slot in reversed(connected):
                try:
                    signal.disconnect(slot)
                except (RuntimeError, TypeError) as disconnect_exc:
                    _LOG.debug(
                        "Pop-out %s unwind disconnect: %s",
                        self.symbol, disconnect_exc,
                    )
            if view_attached:
                try:
                    session.detach_view(self.chart)
                except Exception as detach_exc:
                    _LOG.debug(
                        "Pop-out %s unwind detach_view failed: %s: %s",
                        self.symbol, type(detach_exc).__name__, detach_exc,
                    )
            if hold_acquired:
                try:
                    session.release_rt()
                except Exception as release_exc:
                    _LOG.debug(
                        "Pop-out %s unwind release_rt failed: %s: %s",
                        self.symbol, type(release_exc).__name__, release_exc,
                    )
            if registered:
                try:
                    self._host._unregister_popout(self)
                except Exception as unregister_exc:
                    _LOG.debug(
                        "Pop-out %s unwind unregister failed: %s: %s",
                        self.symbol, type(unregister_exc).__name__,
                        unregister_exc,
                    )
            if resources_acquired:
                try:
                    self._release_memory()
                except Exception as memory_exc:
                    _LOG.debug(
                        "Pop-out %s unwind release_memory failed: %s: %s",
                        self.symbol, type(memory_exc).__name__, memory_exc,
                    )
            if getattr(self, "_session", None) is session:
                self._session = None
            raise

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
        except Exception as exc:
            # Q-43: same treatment as the pacing branch — log, surface,
            # retry — so an unexpected failure can never strand the pop-out
            # silently. The open-popout guard above re-checks on fire.
            _LOG.warning(
                "Pop-out %s RT re-subscribe failed (%s: %s); retrying…",
                self.symbol, type(exc).__name__, exc,
            )
            self._host.status_bar.showMessage(
                f"Pop-out {self.symbol} subscription failed, retrying in 5s…",
                15000,
            )
            QTimer.singleShot(5000, self._retry_rt_subscribe)

    def detach(self) -> None:
        """Release the session (RT refcount + view)."""
        try:
            session = getattr(self, "_session", None)
            if session is not None:
                try:
                    session.bar_updated.disconnect(self._on_bar_updated)
                except (RuntimeError, TypeError) as exc:
                    # Q-43: teardown disconnect of a never-connected slot is
                    # expected — stays best-effort, logged at debug.
                    _LOG.debug("Pop-out %s bar_updated disconnect: %s",
                               self.symbol, exc)
                try:
                    session.bars_refreshed.disconnect(self._on_bars_refreshed)
                except (RuntimeError, TypeError) as exc:
                    _LOG.debug("Pop-out %s bars_refreshed disconnect: %s",
                               self.symbol, exc)
                try:
                    session.alarms_changed.disconnect(self._on_alarms_changed)
                except (RuntimeError, TypeError) as exc:
                    _LOG.debug("Pop-out %s alarms_changed disconnect: %s",
                               self.symbol, exc)
                try:
                    session.drawings_changed.disconnect(
                        self._on_drawings_changed
                    )
                except (RuntimeError, TypeError) as exc:
                    _LOG.debug("Pop-out %s drawings_changed disconnect: %s",
                               self.symbol, exc)
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
        # D49.4/S-P13-4: single-view refresh. The one all-view sync per
        # change is the commit path's direct sync_drawings_to_views();
        # this handler only re-applies the current records to its
        # receiving view. Signal and per-pop-out wiring unchanged (A125).
        try:
            self.chart.drawing_overlay.set_data(
                self._session.symbol,
                self._session.drawings,
                self._session.drawing_groups,
            )
        except Exception as exc:
            # Q-43: a broken receiving view must never take down the
            # signal emission for the remaining views — log and continue.
            _LOG.warning(
                "Pop-out %s drawings refresh failed (%s: %s); skipped",
                self.symbol, type(exc).__name__, exc,
            )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        # D24.9: delete the persisted record on close.
        if self._popout_id is not None:
            try:
                PopoutStore.delete(self._popout_id)
            except Exception as exc:
                # Q-43: teardown persistence cleanup — best-effort, logged.
                _LOG.debug("Pop-out %s persisted-record delete failed: %s: %s",
                           self.symbol, type(exc).__name__, exc)
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
        except Exception as exc:
            # Q-43: geometry-persist best-effort — logged, never breaks close.
            _LOG.debug("Pop-out %s geometry save failed: %s: %s",
                       self.symbol, type(exc).__name__, exc)

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
        except (TypeError, ValueError) as exc:
            # Q-43: corrupt-record best-effort — logged with the symbol.
            _LOG.debug("Pop-out %s geometry restore failed: %s",
                       self.symbol, exc)

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
