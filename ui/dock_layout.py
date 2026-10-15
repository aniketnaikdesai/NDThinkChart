"""Shared, Qt-free dock-width model (D17/D18 Phase 1).

Single source of truth for the widths of the left watchlist dock and the right
(Portfolio-only) dock, **measured against the chart area** — the width of
``MainWindow``'s central widget (B1), not the whole window.

This module is deliberately pure: it imports no PyQt6 / pyqtgraph / any Qt
symbol and needs no ``QApplication``. That makes the cross-clamp rule (B3)
exhaustively unit-testable in isolation, matching the repo's pure-service
pattern (``session_service``, ``backfill_service``).

Constants here are kept in agreement with the pre-existing D13 constants in
``ui/watchlist_panel`` — in particular :data:`CHART_MIN_WIDTH` must equal
``ui/watchlist_panel.CHART_MIN_WIDTH``.
"""

# ── Constants ────────────────────────────────────────────────────────────────

#: Minimum width the chart pane must keep, in px. Shared with
#: ``ui/watchlist_panel.CHART_MIN_WIDTH``.
CHART_MIN_WIDTH = 400

#: Minimum width of the left watchlist dock, in px.
WATCHLIST_MIN_WIDTH = 150

#: Default width restored for the left watchlist dock, in px.
DEFAULT_WATCHLIST_WIDTH = 220

#: Minimum width of the right (Portfolio) dock, in px.
RIGHT_DOCK_MIN_WIDTH = 200

#: Cap fraction the watchlist max width is derived from (50% of chart area).
WATCHLIST_CAP_FRACTION = 0.50

#: Cap fraction the right dock max width is derived from (40% of chart area).
RIGHT_DOCK_CAP_FRACTION = 0.40


# ── Per-dock caps ────────────────────────────────────────────────────────────

def watchlist_max_width(chart_area_w: int) -> int:
    """Maximum left-dock width for a chart area ``chart_area_w``.

    Equal to ``max(WATCHLIST_MIN_WIDTH, min(floor(0.50 * chart_area_w),
    chart_area_w - CHART_MIN_WIDTH))``. Never below :data:`WATCHLIST_MIN_WIDTH`,
    so an infeasible (tiny) chart area does not produce a sub-minimum width.
    """
    cap = int(chart_area_w * WATCHLIST_CAP_FRACTION)
    return max(WATCHLIST_MIN_WIDTH, min(cap, chart_area_w - CHART_MIN_WIDTH))


def right_dock_max_width(chart_area_w: int) -> int:
    """Maximum right-dock width for a chart area ``chart_area_w``.

    Equal to ``max(RIGHT_DOCK_MIN_WIDTH, min(floor(0.40 * chart_area_w),
    chart_area_w - CHART_MIN_WIDTH))``. Never below :data:`RIGHT_DOCK_MIN_WIDTH`.
    """
    cap = int(chart_area_w * RIGHT_DOCK_CAP_FRACTION)
    return max(RIGHT_DOCK_MIN_WIDTH, min(cap, chart_area_w - CHART_MIN_WIDTH))


# ── B3 combined cross-clamp ──────────────────────────────────────────────────

def plan_dock_widths(chart_area_w: int, requested_left: int,
                     requested_right: int) -> tuple:
    """Plan the left/right dock widths for a chart area (B3 cross-clamp).

    Applies each dock's independent cap first, then enforces the combined rule
    ``chart_area_w - left - right >= CHART_MIN_WIDTH`` by shrinking whichever
    dock is over budget — it shrinks the far-from-maximum dock first and falls
    back to the larger when both are at their caps. This makes
    "enlarging one forces the other to shrink" (AC-D18.5) a deterministic, pure
    rule rather than emergent Qt behaviour.

    Guarantees:

    * each returned width is within its own ``[min, max]`` cap;
    * the chart minimum is preserved **where feasible**;
    * neither width ever drops below its dock minimum — on an infeasible window
      (where ``2 * min`` alone exceeds ``chart_area_w - CHART_MIN_WIDTH``) the
      chart minimum yields and the dock minimums win;
    * returns stable ``int`` widths and never raises.

    Returns ``(left, right)``.
    """
    left_max = watchlist_max_width(chart_area_w)
    right_max = right_dock_max_width(chart_area_w)

    left = max(WATCHLIST_MIN_WIDTH, min(int(requested_left), left_max))
    right = max(RIGHT_DOCK_MIN_WIDTH, min(int(requested_right), right_max))

    # Combined budget: how much the two docks may consume while preserving the
    # chart minimum. If it is already below the sum of the dock minimums the
    # window is infeasible — dock minimums win and the chart minimum yields.
    budget = chart_area_w - CHART_MIN_WIDTH
    min_total = WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH
    if budget < min_total:
        return WATCHLIST_MIN_WIDTH, RIGHT_DOCK_MIN_WIDTH

    while left + right > budget:
        # Prefer shrinking whichever dock is below its cap (i.e. the one that was
        # not pushed to its maximum); if both are at their caps, shrink the
        # larger one. This is the "enlarging one forces the other to shrink"
        # behaviour when the flat caps alone would starve the chart.
        #
        # Crucially, the shrink step must never take a dock below its own
        # minimum: on a one-sided over-budget request the preferred dock may
        # already sit at its minimum, so fall through to the other dock. A
        # feasible window (``budget >= min_total``, checked above) always has
        # enough room to satisfy the chart minimum without crossing a dock
        # minimum, so at least one dock can absorb every decrement.
        left_can_shrink = left > WATCHLIST_MIN_WIDTH
        right_can_shrink = right > RIGHT_DOCK_MIN_WIDTH
        if not left_can_shrink and not right_can_shrink:
            break
        left_at_max = left >= left_max
        right_at_max = right >= right_max
        if right_at_max and not left_at_max:
            if left_can_shrink:
                left -= 1
            else:
                right -= 1
        elif left_at_max and not right_at_max:
            if right_can_shrink:
                right -= 1
            else:
                left -= 1
        elif left >= right:
            if left_can_shrink:
                left -= 1
            else:
                right -= 1
        else:
            if right_can_shrink:
                right -= 1
            else:
                left -= 1

    return int(left), int(right)
