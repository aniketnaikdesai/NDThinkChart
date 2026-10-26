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

Mirroring convention follows ``ibkr/bridge.py::IBBridge`` (Qt signals on a
``QObject``); the op-application math mirrors ``chart_assets/lwc/envelope.js``
(``apply_ops_to_bars`` here == ``mergeRows`` there).
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication

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
    (volume ops are ignored — this is the candle-series reconstruction). The
    result is ``[(ts, open, high, low, close)]`` sorted by ``ts`` with no
    duplicates. Mirrors ``mergeRows`` in ``chart_assets/lwc/envelope.js``.
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
    opsEmitted = pyqtSignal(dict)
    #: Emitted after a render-process recovery replay (count of ops replayed).
    replayFinished = pyqtSignal(int)

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
        self.opsEmitted.emit(env)
        self._counters["emitted"] += len(staged)
        self._counters["emissions"] += 1
        return env

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
            self.opsEmitted.emit(env)
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
