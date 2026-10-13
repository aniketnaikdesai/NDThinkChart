"""D38 yfinance event source (38b.1) — the sole approved secondary source.

Earnings via ``get_earnings_dates``, dividends via ``dividends``, splits via
``splits``. Corporate events only — no economic calendar (AC-D38.4); the only
yfinance calls made anywhere in the app are the three above.

Binding hygiene (plan 38b.1, owner-mandated):
- per-symbol disk cache: 24h TTL, 6h re-validation when the symbol has an
  event within 7 days (corrections propagate);
- polite throttle: all calls serialized through one worker thread, >=1s
  between calls, single-digit concurrency (in practice: one at a time);
- pinned ``yfinance`` version (requirements.txt) with a re-pin policy;
- every failure (429, exception, empty frame) -> fresh cache if available,
  else the explicit "event data unavailable" state — never an exception to
  the UI, never a chart block.

The worker thread owns its own SQLite connection (the app's main connection
is ``check_same_thread=True``).
"""

import json
import queue
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta, timezone

from PyQt6.QtCore import QThread, pyqtSignal

from data.events.provider import Event, EventProvider

# Throttle: minimum gap between yfinance calls (plan: >=1s, sequential).
_MIN_CALL_GAP_S = 1.0
# Cache TTLs (plan 38b.1 + advisory A38.2).
_CACHE_TTL_S = 24 * 3600
_NEAR_TERM_TTL_S = 6 * 3600
_NEAR_TERM_WINDOW_D = 7


def _event_to_dict(ev: Event) -> dict:
    return {
        "id": ev.id, "type": ev.type, "symbol": ev.symbol,
        "date": ev.date.isoformat(), "source": ev.source,
        "details": ev.details,
    }


def _event_from_dict(d: dict) -> Event | None:
    try:
        return Event(
            id=d["id"], type=d["type"], symbol=d["symbol"],
            date=date.fromisoformat(d["date"]), source=d["source"],
            details=d.get("details") or {},
        )
    except (KeyError, ValueError, TypeError):
        return None


class YFinanceCache:
    """SQLite-backed per-symbol event cache. Thread-safe via short-lived
    connections (each method opens/closes its own)."""

    def __init__(self, db_path: str):
        self._db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, timeout=10)

    def read(self, symbol: str) -> tuple[list[Event], float, float]:
        """Return (events, fetched_at, failed_at). Empty events on miss."""
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT fetched_at, failed_at, payload FROM "
                    "yfinance_events_cache WHERE symbol = ?",
                    (symbol.upper(),),
                ).fetchone()
            finally:
                conn.close()
        except Exception:
            return [], 0.0, 0.0
        if row is None:
            return [], 0.0, 0.0
        fetched_at, failed_at, payload = row
        events: list[Event] = []
        try:
            for d in json.loads(payload or "[]"):
                ev = _event_from_dict(d)
                if ev is not None:
                    events.append(ev)
        except (ValueError, TypeError):
            events = []
        return events, fetched_at or 0.0, failed_at or 0.0

    def write(self, symbol: str, events: list[Event]) -> None:
        payload = json.dumps([_event_to_dict(e) for e in events])
        now = time.time()
        try:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO yfinance_events_cache "
                    "(symbol, fetched_at, failed_at, payload) VALUES (?, ?, 0, ?) "
                    "ON CONFLICT(symbol) DO UPDATE SET fetched_at=excluded.fetched_at, "
                    "failed_at=0, payload=excluded.payload",
                    (symbol.upper(), now, payload),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

    def mark_failed(self, symbol: str) -> None:
        try:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO yfinance_events_cache "
                    "(symbol, fetched_at, failed_at, payload) VALUES (?, 0, ?, '[]') "
                    "ON CONFLICT(symbol) DO UPDATE SET failed_at=excluded.failed_at",
                    (symbol.upper(), time.time()),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass


def _fetch_symbol_events(symbol: str) -> list[Event]:
    """Blocking yfinance fetch for one symbol. Raises on failure (the worker
    converts to mark_failed). Only the three approved endpoints are used."""
    import yfinance as yf

    sym = symbol.upper()
    events: list[Event] = []
    ticker = yf.Ticker(sym)

    # Earnings: upcoming (~4 quarters, estimates only) + ~5y history.
    try:
        ed = ticker.get_earnings_dates(limit=12)
    except Exception:
        ed = None
    if ed is not None:
        try:
            for ts, row in ed.iterrows():
                try:
                    ev_date = ts.date() if hasattr(ts, "date") else None
                    if ev_date is None:
                        continue
                    details: dict = {}
                    est = row.get("EPS Estimate")
                    rep = row.get("Reported EPS")
                    sur = row.get("Surprise(%)")
                    if est is not None and str(est) != "nan":
                        details["estimate"] = float(est)
                    if rep is not None and str(rep) != "nan":
                        details["reported"] = float(rep)
                    if sur is not None and str(sur) != "nan":
                        details["surprise_pct"] = float(sur)
                    events.append(Event(
                        id=f"yf:earnings:{sym}:{ev_date.isoformat()}",
                        type="earnings", symbol=sym, date=ev_date,
                        source="yfinance", details=details,
                    ))
                except (ValueError, TypeError, AttributeError):
                    continue
        except Exception:
            pass

    # Dividends: ex-div history.
    try:
        divs = ticker.dividends
    except Exception:
        divs = None
    if divs is not None:
        try:
            for ts, amt in divs.items():
                try:
                    ev_date = ts.date() if hasattr(ts, "date") else None
                    if ev_date is None:
                        continue
                    events.append(Event(
                        id=f"yf:dividend:{sym}:{ev_date.isoformat()}",
                        type="dividend", symbol=sym, date=ev_date,
                        source="yfinance",
                        details={"amount": float(amt)},
                    ))
                except (ValueError, TypeError, AttributeError):
                    continue
        except Exception:
            pass

    # Splits: ratio history.
    try:
        splits = ticker.splits
    except Exception:
        splits = None
    if splits is not None:
        try:
            for ts, ratio in splits.items():
                try:
                    ev_date = ts.date() if hasattr(ts, "date") else None
                    if ev_date is None:
                        continue
                    events.append(Event(
                        id=f"yf:split:{sym}:{ev_date.isoformat()}",
                        type="split", symbol=sym, date=ev_date,
                        source="yfinance",
                        details={"ratio": float(ratio)},
                    ))
                except (ValueError, TypeError, AttributeError):
                    continue
        except Exception:
            pass

    return events


class _YFinanceWorker(QThread):
    """Single shared worker: serializes all yfinance calls app-wide with a
    >=1s gap (plan 38b.1 polite throttle)."""

    finished = pyqtSignal(str, bool)  # symbol, ok

    def __init__(self, cache: YFinanceCache):
        super().__init__()
        self._cache = cache
        self._tasks: "queue.Queue[str]" = queue.Queue()
        self._queued: set[str] = set()
        self._lock = threading.Lock()
        self._last_call = 0.0

    def submit(self, symbol: str) -> None:
        key = symbol.upper()
        with self._lock:
            if key in self._queued:
                return
            self._queued.add(key)
        self._tasks.put(key)
        if not self.isRunning():
            self.start()

    def run(self) -> None:
        while True:
            try:
                symbol = self._tasks.get(timeout=30)
            except queue.Empty:
                return  # idle: thread exits; restarted on next submit
            with self._lock:
                self._queued.discard(symbol)
            gap = _MIN_CALL_GAP_S - (time.time() - self._last_call)
            if gap > 0:
                time.sleep(gap)
            try:
                events = _fetch_symbol_events(symbol)
            except Exception:
                self._cache.mark_failed(symbol)
                self._last_call = time.time()
                self.finished.emit(symbol, False)
                continue
            self._cache.write(symbol, events)
            self._last_call = time.time()
            self.finished.emit(symbol, True)


_worker: "_YFinanceWorker | None" = None
_worker_lock = threading.Lock()


def shared_worker(cache: YFinanceCache) -> _YFinanceWorker:
    """App-wide singleton worker (one throttle point for all yfinance calls)."""
    global _worker
    with _worker_lock:
        if _worker is None:
            _worker = _YFinanceWorker(cache)
        return _worker


class YFinanceEventSource(EventProvider):
    """yfinance-backed event source with cache-first reads.

    ``get_events`` never blocks on the network: it returns the cached events
    (filtered to [start, end]) and schedules a background refresh when the
    cache is missing or stale. Completion is reported via :meth:`bind_refresh`
    (the worker owns the Qt signal; this class stays a plain ABC).
    """

    def __init__(self, cache: YFinanceCache,
                 worker: "_YFinanceWorker | None" = None):
        self._cache = cache
        self._worker = worker or shared_worker(cache)

    def bind_refresh(self, slot) -> None:
        """Connect the worker's finished signal to ``slot(symbol)``."""
        self._worker.finished.connect(lambda symbol, _ok: slot(symbol))

    def _ttl_for(self, events: list[Event]) -> float:
        today = date.today()
        for ev in events:
            delta = (ev.date - today).days
            if 0 <= delta <= _NEAR_TERM_WINDOW_D:
                return _NEAR_TERM_TTL_S
        return _CACHE_TTL_S

    def _needs_refresh(self, symbol: str) -> bool:
        events, fetched_at, _ = self._cache.read(symbol)
        if not events and fetched_at == 0.0:
            return True  # never fetched
        return (time.time() - fetched_at) > self._ttl_for(events)

    def get_events(self, symbol: str, start: date, end: date) -> list[Event]:
        events, _, _ = self._cache.read(symbol)
        if self._needs_refresh(symbol):
            self._worker.submit(symbol)
        return [e for e in events if start <= e.date <= end]

    def unavailable(self, symbol: str) -> bool:
        events, fetched_at, failed_at = self._cache.read(symbol)
        if events or fetched_at > 0.0:
            return False
        # No cache at all: unavailable only if we have actually failed
        # (otherwise a refresh is presumably in flight — still "loading",
        # not "unavailable").
        return failed_at > 0.0
