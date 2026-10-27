"""ui/lwc_bridge.py — batched self-healing QWebChannel bridge (P6-04, D47.4).

Transport for the offline LWC host (`ui/lwc_host.py`). Python emits one
versioned envelope per crossing — ``{"v": 1, "ops": [...]}`` — where every
data op carries column arrays (never scalars, never row objects)::

    {"op": "set_bars",   "series": "candles", "cols": {"ts": [...],
     "open": [...], "high": [...], "low": [...], "close": [...]}})
    {"op": "update_bar", "series": "candles", "cols": {"ts": [t],
     "open": [o], "high": [h], "low": [l], "close": [c]}}   (length-1 columns)
    {"op": "set_volume", "series": "volume",  "cols": {"ts": [...],
     "value": [...]}})
    {"op": "clear",      "series": "<name>"}                (no cols)

JS receives timestamps and prices only — no formatted strings, no trading
logic (renderer boundary: nothing under ``ibkr/``, no DB/store, no service
or order surface is touched from here).

Behaviour:

* **queue-until-ready** — ops accepted before the page signals ready are
  held in order and drained on ``set_ready(True)``; nothing is dropped.
  Readiness is the **page's** word (Q-19/S3d): ``chart.js`` calls the
  ``pageReady()`` slot after its QWebChannel subscription exists, because
  ``loadFinished`` fires before that subscription and a replay from there had
  no listener.
* **two payloads per crossing** — ``opsEmitted(dict)`` for Python consumers
  and ``opsJson(str)`` for the page (Q-19/S3c: a dict reaches a JS slot as a
  Python ``repr``, not JSON). The JSON is compact and ``allow_nan=False``.
* **~33 ms live coalesce** — consecutive ``update_bar`` ops for the same
  (series, ts) merge with last-tick-wins while the coalesce window is open,
  so a tick storm crosses at most once per window. ``flush()`` is explicit
  (tests drive it); a ``QTimer`` single-shot is armed as well whenever a Qt
  event loop exists, so production never waits on a manual flush.
* **replay after ``renderProcessTerminated``** — the full op log (every op
  ever accepted, in order) is re-emitted once the fresh page is ready; the
  JS side applies it idempotently, so the re-rendered series has no
  duplicated or lost bars.
* **backpressure counters from day one** — ``counters()`` reports received /
  queued / coalesced / emitted / emissions / replays / queue-depth-max.
* **whitespace placeholders** — a candle/volume column may hold ``None`` in a
  value slot (never in ``ts``). The row is a whitespace point: it occupies one
  index slot so a within-session hole renders as empty space
  (AC-D21.4.4), and it is not a bar (``apply_ops_to_bars`` skips it,
  ``chart_assets/lwc/chart.js`` sends ``{time}`` only to the series).

**Page → Python messages (Q-20).** Every call below is a ``pyqtSlot`` whose
single argument is a JSON string — the mirror of :attr:`opsJson`, so no
dict/``repr`` ambiguity exists in either direction. Each slot re-emits a
``page*`` signal; ``ui/lwc_view.py`` maps them onto the pre-D47
``DrawingController`` / ``AlarmController`` signals and its own
``zoom_refused`` / ``key_pressed``:

============================ ============================ =======================
page call                    payload keys                 bridge signal
============================ ============================ =======================
``pageReady()``              —                            (drain + replay)
``focusReleased()``          —                            ``pageFocusReleased``
``drawingCommitted()``       kind, points/price, color    ``pageDrawingCommitted``
``drawingUpdated()``         id, payload, color           ``pageDrawingUpdated``
``drawingDeleted()``         id                           ``pageDrawingDeleted``
``selectionChanged()``       id (``null``/``-1`` clears)  ``pageSelectionChanged``
``alarmCreated()``           price                        ``pageAlarmCreated``
``alarmMoved()``             id, price                    ``pageAlarmMoved``
``alarmDeleted()``           id                           ``pageAlarmDeleted``
``zoomRefused()``            trigger                      ``pageZoomRefused``
``keyPressed()``             key                          ``pageKeyPressed``
============================ ============================ =======================

Mirroring convention follows ``ibkr/bridge.py::IBBridge`` (Qt signals on a
``QObject``); the op-application math mirrors ``chart_assets/lwc/envelope.js``
(``apply_ops_to_bars`` here == ``mergeRows`` there).
"""

import json

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QCoreApplication

#: Envelope version pinned for this wave. The JS side rejects anything else.
ENVELOPE_VERSION = 1

#: Live-tick coalesce window (ms). One crossing per window per forming bar.
COALESCE_MS = 33

#: Ops eligible for last-tick-wins merging inside the coalesce window.
LIVE_OPS = frozenset({"update_bar"})

#: Series the bridge knows. Anything else is rejected at the boundary.
KNOWN_SERIES = frozenset({"candles", "volume"})

_CANDLE_COLS = ("ts", "open", "high", "low", "close")
_VOLUME_COLS = ("ts", "value")


def _check_op_shape(op) -> None:
    """Raise ``ValueError`` when ``op`` is not a well-formed column-array op."""
    if not isinstance(op, dict):
        raise ValueError(f"op must be a dict, got {type(op).__name__}")
    kind = op.get("op")
    series = op.get("series")
    if not isinstance(kind, str) or not kind:
        raise ValueError("op['op'] must be a non-empty string")
    if not isinstance(series, str) or not series:
        raise ValueError("op['series'] must be a non-empty string")
    if kind == "clear":
        if "cols" in op:
            raise ValueError("clear must not carry cols")
        return
    if series not in KNOWN_SERIES:
        raise ValueError(f"unknown series: {series!r}")
    if kind not in ("set_bars", "set_volume", "update_bar"):
        raise ValueError(f"unknown op: {kind!r}")
    want = _CANDLE_COLS if series == "candles" else _VOLUME_COLS
    cols = op.get("cols")
    if not isinstance(cols, dict):
        raise ValueError("op['cols'] must be a dict of column arrays")
    if sorted(cols) != sorted(want):
        raise ValueError(f"cols must be exactly {list(want)}")
    n = None
    for name in want:
        col = cols[name]
        if not isinstance(col, list):
            raise ValueError(f"cols[{name!r}] must be a list (column array)")
        if n is None:
            n = len(col)
        elif len(col) != n:
            raise ValueError("column arrays must share one length")
    if kind == "update_bar" and n != 1:
        raise ValueError("update_bar must carry single-element columns")
    # Q-20 whitespace placeholders: a *value* slot may be ``None`` (that row
    # renders as ``{time}`` only — a hole, AC-D21.4.4); a ``ts`` slot never
    # may. The series times are real UTC epoch seconds, ascending and unique.
    if any(t is None for t in cols["ts"]):
        raise ValueError("ts columns must carry real times, never None")


def candles_set_op(bars) -> dict:
    """Build a ``set_bars`` op for the candle series from Bar-like objects.

    Each bar needs ``ts``/``open``/``high``/``low``/``close`` (the ``Bar``
    value shape from ``data/bar_cache.py``).
    """
    rows = list(bars)
    return {
        "op": "set_bars",
        "series": "candles",
        "cols": {
            "ts": [b.ts for b in rows],
            "open": [b.open for b in rows],
            "high": [b.high for b in rows],
            "low": [b.low for b in rows],
            "close": [b.close for b in rows],
        },
    }


def candle_update_op(bar) -> dict:
    """Build a single-tick ``update_bar`` op (length-1 column arrays)."""
    return {
        "op": "update_bar",
        "series": "candles",
        "cols": {
            "ts": [bar.ts],
            "open": [bar.open],
            "high": [bar.high],
            "low": [bar.low],
            "close": [bar.close],
        },
    }


def volume_set_op(bars) -> dict:
    """Build a ``set_volume`` op from Bar-like objects (``ts``/``volume``)."""
    rows = list(bars)
    return {
        "op": "set_volume",
        "series": "volume",
        "cols": {
            "ts": [b.ts for b in rows],
            "value": [b.volume for b in rows],
        },
    }


def apply_ops_to_bars(ops) -> list:
    """Reconstruct the candle series from an op list (replay-identity check).

    ``set_bars`` replaces, ``update_bar`` upserts by ``ts``, ``clear`` empties
    (volume ops are ignored — this is the candle-series reconstruction). A
    whitespace placeholder (a row whose ``close`` is ``None``, Q-20) is not a
    bar and is skipped. The result is ``[(ts, open, high, low, close)]``
    sorted by ``ts`` with no duplicates. Mirrors ``mergeRows`` in
    ``chart_assets/lwc/envelope.js``.
    """
    by_ts: dict = {}
    for op in ops or []:
        if not isinstance(op, dict) or op.get("series") != "candles":
            continue
        kind = op.get("op")
        if kind == "clear":
            by_ts = {}
        elif kind == "set_bars":
            cols = op["cols"]
            by_ts = {
                ts: (ts, o, h, lo, c)
                for ts, o, h, lo, c in zip(
                    cols["ts"], cols["open"], cols["high"],
                    cols["low"], cols["close"],
                )
                if c is not None
            }
        elif kind == "update_bar":
            cols = op["cols"]
            ts = cols["ts"][0]
            by_ts[ts] = (ts, cols["open"][0], cols["high"][0],
                         cols["low"][0], cols["close"][0])
    return [by_ts[ts] for ts in sorted(by_ts)]


class LwBridge(QObject):
    """Batched ``QWebChannel`` transport: ``send_ops`` + ``replay_log``.

    Signals mirror the ``IBBridge`` convention (``ibkr/bridge.py``): the Qt
    side subscribes, the transport decides *when* to cross.
    """

    #: Emitted once per crossing with the full ``{"v": 1, "ops": [...]}`` dict.
    #: Python consumers keep this shape. A JS slot connected to it receives a
    #: Python ``repr`` string (``"{'v': 1, ...}"``), which is **not** JSON —
    #: that is why the page subscribes to :attr:`opsJson` instead.
    opsEmitted = pyqtSignal(dict)
    #: The same envelope as compact JSON (Q-19/S3c). Emitted beside every
    #: ``opsEmitted`` crossing (flush + replay); ``allow_nan=False`` makes a
    #: non-finite price fail loudly here rather than silently in the page.
    #: Measured 33k-bar replay on this machine (2026-10-26): **1,411,535 bytes
    #: / 13.4 ms** in ``json.dumps`` (13.6 ms for the whole
    #: ``handle_page_ready`` replay) — no chunking or ``runJavaScript``
    #: fallback is needed at that size.
    opsJson = pyqtSignal(str)
    #: Emitted after a render-process recovery replay (count of ops replayed).
    replayFinished = pyqtSignal(int)
    #: Page → Python focus hand-back (Q-19/S3e): the page's ``focusReleased()``
    #: pyqtSlot below re-emits this so the view's ``handle_focus_released``
    #: (and its ``focusRoundTrip`` controller signal) runs. A signal cannot
    #: share the slot's name, hence the distinct spelling.
    pageFocusReleased = pyqtSignal()
    #: Page → Python message channels (Q-20): one signal per ``pyqtSlot``
    #: below. The payload is the parsed JSON object the page sent; the view
    #: maps it onto the pre-D47 controller signal (see the module table).
    pageDrawingCommitted = pyqtSignal(dict)
    pageDrawingUpdated = pyqtSignal(dict)
    pageDrawingDeleted = pyqtSignal(dict)
    pageSelectionChanged = pyqtSignal(dict)
    pageAlarmCreated = pyqtSignal(dict)
    pageAlarmMoved = pyqtSignal(dict)
    pageAlarmDeleted = pyqtSignal(dict)
    pageZoomRefused = pyqtSignal(dict)
    pageKeyPressed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ready = False
        self._op_log: list = []     # every op ever accepted, in order
        self._queued: list = []     # accepted while not ready (order kept)
        self._outbox: list = []     # staged non-live ops for the next flush
        self._live_buf: dict = {}   # (series, ts) -> update_bar op (coalesced)
        self._counters = {
            "received": 0,
            "queued": 0,
            "coalesced": 0,
            "emitted": 0,
            "emissions": 0,
            "replays": 0,
            "queue_depth_max": 0,
        }
        self._timer: QTimer | None = None

    # ── readiness / queue-until-ready ──────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._ready

    def set_ready(self, ready: bool) -> None:
        """Mark the page ready (or not). Draining the held queue on True."""
        self._ready = bool(ready)
        if self._ready and self._queued:
            held, self._queued = self._queued, []
            self._stage(held)

    # ── send path ──────────────────────────────────────────────────────

    def send_ops(self, ops: list) -> None:
        """Accept ``ops``: log always, queue while not ready, else stage."""
        ops = list(ops or [])
        for op in ops:
            _check_op_shape(op)
        self._op_log.extend(ops)
        self._counters["received"] += len(ops)
        if not self._ready:
            self._queued.extend(ops)
            self._counters["queued"] += len(ops)
            depth = len(self._queued)
            if depth > self._counters["queue_depth_max"]:
                self._counters["queue_depth_max"] = depth
            return
        self._stage(ops)

    def _stage(self, ops: list) -> None:
        for op in ops:
            if op["op"] in LIVE_OPS:
                key = (op["series"], op["cols"]["ts"][0])
                if key in self._live_buf:
                    self._counters["coalesced"] += 1
                self._live_buf[key] = op
            else:
                self._outbox.append(op)
        self._arm_timer()

    def _arm_timer(self) -> None:
        """Arm the ~33 ms coalesce flush when a Qt event loop exists.

        Headless/test contexts without an application simply accumulate until
        ``flush()`` is called explicitly — nothing is emitted from here.
        """
        if QCoreApplication.instance() is None:
            return
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.setInterval(COALESCE_MS)
            self._timer.timeout.connect(self.flush)
        if not self._timer.isActive():
            self._timer.start()

    def flush(self):
        """Cross one envelope now; returns it (``None`` when nothing staged)."""
        staged = list(self._outbox)
        staged.extend(self._live_buf.values())
        self._outbox.clear()
        self._live_buf.clear()
        if not staged:
            return None
        env = {"v": ENVELOPE_VERSION, "ops": staged}
        self._emit(env)
        self._counters["emitted"] += len(staged)
        self._counters["emissions"] += 1
        return env

    def _emit(self, env: dict) -> None:
        """Emit one envelope on both channels (dict + compact JSON string).

        Centralised so the flush crossing and the replay crossing can never
        diverge: ``opsJson`` is emitted beside every ``opsEmitted`` (Q-19/S3c).
        ``allow_nan=False`` turns a NaN/inf into a ``ValueError`` here — loud
        at the boundary — instead of producing text the page's envelope check
        silently rejects.
        """
        payload = json.dumps(env, separators=(",", ":"), allow_nan=False)
        self.opsEmitted.emit(env)
        self.opsJson.emit(payload)

    # ── page → Python slots (Q-19/S3d/S3e) ─────────────────────────────

    @pyqtSlot()
    def pageReady(self) -> None:
        """The page's QWebChannel half is subscribed; drain and replay now.

        ``QWebEngineView.loadFinished`` fires before ``QWebChannel``'s JS
        setup completes, so replaying from :meth:`_on_load_finished` raced an
        absent listener and the bars never reached the page (S3d). Readiness
        is the page's word: ``chart_assets/lwc/chart.js`` calls this slot
        *after* connecting :attr:`opsJson` and before anything else.

        Idempotent in the same way :meth:`handle_page_ready` is — a second
        call replays the same log again, which the page applies idempotently.
        """
        self.handle_page_ready()

    @pyqtSlot()
    def focusReleased(self) -> None:
        """JS slot: the page's Esc blur hands focus back to the Qt chain."""
        self.pageFocusReleased.emit()

    # ── page → Python message slots (Q-20) ────────────────────────────
    #
    # One slot per message name the page calls (``chart.js`` keyboard,
    # ``interaction.js`` controls/refusals, ``primitives.js`` drawing commits,
    # ``alarms.js`` alarm edits). Each payload is a JSON string — the mirror
    # of :attr:`opsJson` — parsed here so no ``QVariantMap``/``repr`` ambiguity
    # exists. The names are the JS call names; the signals carry a ``page``
    # prefix because a Qt signal and a slot cannot share one name.

    @staticmethod
    def _payload(raw) -> dict:
        """Decode one page message payload (``{}`` on anything unusable)."""
        text = raw if isinstance(raw, str) else ""
        if not text.strip():
            return {}
        try:
            value = json.loads(text)
        except (TypeError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    @pyqtSlot(str)
    def drawingCommitted(self, payload: str = "") -> None:
        """JS slot: a drawing gesture finished in the page."""
        self.pageDrawingCommitted.emit(self._payload(payload))

    @pyqtSlot(str)
    def drawingUpdated(self, payload: str = "") -> None:
        """JS slot: an existing drawing's geometry/colour was edited."""
        self.pageDrawingUpdated.emit(self._payload(payload))

    @pyqtSlot(str)
    def drawingDeleted(self, payload: str = "") -> None:
        """JS slot: a drawing was deleted in the page."""
        self.pageDrawingDeleted.emit(self._payload(payload))

    @pyqtSlot(str)
    def selectionChanged(self, payload: str = "") -> None:
        """JS slot: the page's selected drawing changed (``null`` clears)."""
        self.pageSelectionChanged.emit(self._payload(payload))

    @pyqtSlot(str)
    def alarmCreated(self, payload: str = "") -> None:
        """JS slot: an alarm was placed on the page's price axis."""
        self.pageAlarmCreated.emit(self._payload(payload))

    @pyqtSlot(str)
    def alarmMoved(self, payload: str = "") -> None:
        """JS slot: an alarm line was dragged to a new price."""
        self.pageAlarmMoved.emit(self._payload(payload))

    @pyqtSlot(str)
    def alarmDeleted(self, payload: str = "") -> None:
        """JS slot: an alarm line was deleted in the page."""
        self.pageAlarmDeleted.emit(self._payload(payload))

    @pyqtSlot(str)
    def zoomRefused(self, payload: str = "") -> None:
        """JS slot: the page's router refused a zoom (TR-9)."""
        self.pageZoomRefused.emit(self._payload(payload))

    @pyqtSlot(str)
    def keyPressed(self, payload: str = "") -> None:
        """JS slot: a chart keyboard gesture the page handled."""
        self.pageKeyPressed.emit(self._payload(payload))

    # ── recovery / replay ──────────────────────────────────────────────

    def replay_log(self) -> list:
        """Return the full op log (a copy) — the replay source of truth."""
        return [dict(op) for op in self._op_log]

    def handle_render_terminated(self) -> None:
        """``renderProcessTerminated`` hook: the renderer is gone, hold traffic.

        The page reloads, then ``handle_page_ready`` replays the full log.
        """
        self.set_ready(False)

    def handle_page_ready(self):
        """Fresh page signalled ready: drain, then replay the full op log.

        Returns the replay envelope (``None`` when the log is empty).
        """
        self.set_ready(True)
        pending = self.flush()  # drain anything staged before the crash first
        envelopes = [pending] if pending else []
        if self._op_log:
            env = {"v": ENVELOPE_VERSION, "ops": list(self._op_log)}
            self._emit(env)
            self._counters["emitted"] += len(self._op_log)
            self._counters["emissions"] += 1
            self._counters["replays"] += 1
            self.replayFinished.emit(len(self._op_log))
            envelopes.append(env)
            return env
        return envelopes[0] if envelopes else None

    # ── backpressure counters (instrumented from day one) ───────────────

    def counters(self) -> dict:
        """Snapshot of the backpressure counters."""
        return dict(self._counters)
