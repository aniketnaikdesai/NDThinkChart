"""services/alarm_monitor.py — headless alarm monitor (D25).

The AlarmMonitor owns headless TickerSessions for symbols that have active
alarms but no open view. A headless session is an ordinary TickerSession with
``views == 0`` and ``monitored == True``:

- one ``reqRealTimeBars`` (5-sec) subscription, refcounted like any session,
- a ``BarAggregator("1m")`` fed by the 5-sec pushes,
- alarm evaluation on every aggregated 1-min bar (DEC-2: event-driven, not
  polled),
- ``prev_price`` seeded from ``BarCache.get_bars(symbol, "1m")`` last close;
  if no cache, the first tick seeds with NO evaluation (no phantom trigger
  when starting beyond the level — depends on D27.1),
- ZERO historical requests.

Reconciliation triggers: (re)connect, alarm CRUD, alarm rearm, alarm trigger,
session attach (a view opens → the session is no longer headless), session
detach (last view closes → may become headless).

Pacing guardrail: symbols are subscribed most-recently-active first; if the
pacing budget is exhausted, a warning names the symbols left unmonitored.
"""

from __future__ import annotations

import logging
import time

from data.alarm_store import AlarmStore
from data.bar_cache import BarCache
from ibkr.pacing import PacingExceeded

_LOG = logging.getLogger(__name__)


class AlarmMonitor:
    """Owns headless alarm-monitoring sessions. Wired to the MainWindow
    session registry; the window calls :meth:`reconcile` on the triggers
    listed above."""

    def __init__(self, host):
        # host: MainWindow (duck-typed) — get_or_create_session(),
        # _sessions, _teardown_session(), status_bar.
        self._host = host

    # ── Reconciliation ──────────────────────────────────────────────

    def reconcile(self) -> None:
        """Ensure exactly the symbols with active alarms are monitored.

        - Symbols with active alarms and no session → create a monitored
          headless session (1m aggregator, RT subscribe, no history).
        - Symbols with no active alarms whose session is headless+monitored
          → release the monitor (teardown if orphaned).
        - Sessions with views are never touched (their views drive them).
        """
        wanted = set(AlarmStore.symbols_with_active_alarms())
        # Most-recently-active first: order by latest alarm created_at.
        wanted = self._order_by_recency(wanted)

        for symbol in wanted:
            session = self._host.get_or_create_session(symbol)
            if session.views:
                # Has views: not headless; ensure it's not marked monitored
                # (a view opening on a monitored session promotes it).
                session.monitored = False
                continue
            if not session.monitored:
                self._start_monitoring(session)

        # Release monitors for symbols that no longer want them.
        for symbol, session in list(self._host._sessions.items()):
            if (
                session.monitored
                and not session.views
                and symbol not in wanted
            ):
                self._stop_monitoring(session)

    def _order_by_recency(self, symbols: set[str]) -> list[str]:
        """Most-recently-active first (pacing guardrail)."""
        from data.db import db

        recency: dict[str, int] = {}
        for symbol in symbols:
            cur = db.conn.execute(
                "SELECT MAX(created_at) FROM alarms "
                "WHERE symbol=? AND active=1 AND triggered=0",
                (symbol,),
            )
            row = cur.fetchone()
            recency[symbol] = row[0] or 0
        return sorted(symbols, key=lambda s: recency[s], reverse=True)

    # ── Headless session lifecycle ──────────────────────────────────

    def _start_monitoring(self, session) -> None:
        """Begin headless monitoring: 1m aggregator, seeded price, RT sub."""
        session.monitored = True
        # Seed prev_price from the 1m cache; else first-tick seed (no eval).
        cached = BarCache.get_bars(session.symbol, "1m")
        if cached:
            session.last_chart_price = cached[-1].close
            _LOG.info(
                "AlarmMonitor: %s seeded at %.4f from 1m cache",
                session.symbol,
                cached[-1].close,
            )
        else:
            session.last_chart_price = None
            _LOG.info(
                "AlarmMonitor: %s no 1m cache; first tick seeds (no eval)",
                session.symbol,
            )
        # The 1m aggregator is created on demand by the RT path.
        session.aggregator_for("1m")
        # Alarms are already on the session (prepare_load/reload_alarms);
        # ensure they're fresh.
        session.reload_alarms()
        try:
            session.ensure_rt_subscribed()
        except PacingExceeded as e:
            # Pacing guardrail: warn naming the unmonitored symbol; the next
            # reconcile (or the session's own retry) picks it up.
            _LOG.warning(
                "AlarmMonitor: pacing-limited, %s left unmonitored "
                "(retry in %.0fs)",
                session.symbol,
                e.wait_seconds,
            )
            try:
                self._host.status_bar.showMessage(
                    f"Alarm monitor pacing-limited: {session.symbol} "
                    f"unmonitored, retrying…",
                    15000,
                )
            except Exception:
                pass
            # Stay marked monitored so a later reconcile retries the subscribe.
            return
        _LOG.info("AlarmMonitor: monitoring %s (headless 1m)", session.symbol)

    def _stop_monitoring(self, session) -> None:
        """Release a headless monitor; teardown if fully orphaned."""
        session.monitored = False
        session.release_rt()
        if not session.views:
            self._host._teardown_session(session.symbol)
        _LOG.info("AlarmMonitor: stopped monitoring %s", session.symbol)

    # ── Event hooks (called by the host) ────────────────────────────

    def on_alarm_changed(self) -> None:
        """Alarm CRUD / rearm / trigger → reconcile."""
        self.reconcile()

    def on_session_attached(self, session) -> None:
        """A view opened on the session → it's no longer headless."""
        if session.monitored and session.views:
            # Promote: the view now drives the session; keep the RT sub
            # (refcounted) but clear the monitored flag so reconcile won't
            # tear it down when alarms go quiet.
            session.monitored = False
            self.reconcile()

    def on_session_detached(self, session) -> None:
        """Last view closed → may become a headless monitor."""
        self.reconcile()
