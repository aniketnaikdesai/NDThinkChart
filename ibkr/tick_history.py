"""Historical-tick request manager (D36 footprint).

Owns every historical-tick call the app makes: ``reqHistoricalTicks``
(BID_ASK and TRADES pages for per-level footprint bucketing). This is the
first new ``req*`` family since D27.

Pacing: tick-history requests count against the rolling 600s historical
budget owned by ``pacing_manager`` (conservative per plan §10.2 — if build
observes they are budgeted separately the constraint relaxes; the code path
is the same either way). The manager never sleeps: when the budget is
exhausted it raises ``PacingExceeded`` and the caller defers via
``QTimer.singleShot`` (D28.3 pattern).

AC-D36.3: footprint data comes from historical ticks ONLY. This module has
no ``reqTickByTickData`` call and never will — live tick-by-tick spam
(≤1 request per instrument per 15s) is a pacing violation.

Note on ``reqHistogramData`` (A1, honest limitation): the API takes no
date parameter — ``(tickerId, contract, useRTH, timePeriod)`` — so a
histogram always covers the trailing period ending *now* and cannot be
attributed to an individual historical bar. The footprint service therefore
derives the heatmap's tick-count metric from the same TRADES tick pages as
the volume metric (one dataset, two metrics — the owner's "same per-level
data" decision, literally). The histogram plumbing was removed entirely:
no request method, no bridge signal, no override.
"""

from ibapi.contract import Contract

from ibkr.pacing import PacingExceeded, pacing_manager
from ibkr.id_manager import id_manager

# IBKR caps historical-tick responses at 1000 ticks per request; the
# footprint paginator pages backward in windows of this size.
TICKS_PER_REQUEST = 1000


class TickHistoryManager:
    """Issues historical-tick and histogram requests against the real client.

    ``client`` is the production ``IBApiClient``; tests inject a fake with
    the same method names (fakes live in ``tests/`` only — never here).
    """

    def __init__(self, client):
        self.client = client

    # ── Historical ticks ─────────────────────────────────────────────

    def req_historical_ticks(
        self,
        contract: Contract,
        startDateTime: str = "",
        endDateTime: str = "",
        numberOfTicks: int = TICKS_PER_REQUEST,
        whatToShow: str = "BID_ASK",
        useRTH: int = 1,
    ) -> int:
        """Request one page of historical ticks.

        Pagination convention (plan 36.1): page *backward* — set
        ``endDateTime`` to the window end and leave ``startDateTime`` empty;
        TWS returns up to ``numberOfTicks`` ticks at or before ``endDateTime``.
        The caller pages with ``endDateTime`` = (earliest tick seen − 1s)
        until the window start is covered or a page arrives with ``done``.
        ``endDateTime`` uses the ``yyyyMMdd-HH:mm:ss`` UTC form.

        Raises ``PacingExceeded`` (never sleeps) when the 600s historical
        budget is exhausted; the slot is recorded only after the request is
        actually issued (D28.3).
        """
        req_id = id_manager.get_id()
        wait = pacing_manager.historical_wait_seconds()
        if wait > 0:
            raise PacingExceeded(wait)
        self.client.reqHistoricalTicks(
            req_id,
            contract,
            startDateTime,
            endDateTime,
            numberOfTicks,
            whatToShow,
            useRTH,
            False,  # ignoreSize
            [],
        )
        pacing_manager.record_historical_slot()
        return req_id

    def cancel_historical_ticks(self, req_id: int | None) -> None:
        """Best-effort cancel, capability-guarded like the other cancels."""
        if req_id is None:
            return
        cancel = getattr(self.client, "cancelHistoricalTicks", None)
        if cancel is None:
            return
        try:
            cancel(req_id)
        except Exception:
            pass
