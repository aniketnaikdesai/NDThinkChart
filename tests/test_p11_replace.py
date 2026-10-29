"""P11-T5 (D51.5 / S-P11-3): same/new full-series replacement continuity.

Offscreen integration coverage for the continuity directive ``set_series``
stamps on every full replace (``same_symbol`` on both the ``set_bars`` and
``set_volume`` ops):

* T51 (AC1): a scrolled-back chart's same-symbol full replace (backfill
  shape) preserves viewport + follow state — the wire carries
  ``same_symbol=True`` (the page re-applies its own pre-replace range, so
  no fit jumps it), no stale ``set_visible_range`` restore crosses
  (AR-P11-2), and the pending viewport stays slot-identical.
* T52 (AC2): a new symbol's full replace carries ``same_symbol=False``
  with no restore op (the page fits to the live edge); a zero-bar series
  replaces and Fits (reset) with no error (Journey 44 edge).

The page-side application (re-apply vs fit, zero-bar no-op fit) lives in
``chart_assets/lwc/chart.js`` (``replacePreservesViewport`` + ``applyOps`` +
``fitToWidth``) and rides the ``node --test`` suite; these tests pin the
Python half of the contract.
"""

import datetime

import pytest

from data.models import Bar
from ui.lwc_view import LwcChartView

# Thursday 2026-10-29 14:00 UTC (10:00 ET) — a regular-session weekday, so
# RTH filtering keeps every seeded bar regardless of ``ext_hours``.
BASE_TS = int(datetime.datetime(2026, 10, 29, 14, 0,
                                tzinfo=datetime.timezone.utc).timestamp())


def _bars(symbol, start_ts, count, step=60):
    """``count`` 1-minute bars from ``start_ts`` (ascending ``ts``)."""
    rows = []
    for i in range(count):
        price = 100.0 + i
        rows.append(Bar(symbol=symbol, timeframe="1 min", ts=start_ts + i * step,
                        open=price, high=price + 1.0, low=price - 1.0,
                        close=price + 0.5, volume=1000.0))
    return rows


def _set_bars(ops):
    return next(op for op in ops if op["op"] == "set_bars")


def _set_volume(ops):
    return next(op for op in ops if op["op"] == "set_volume")


@pytest.fixture
def view(qapp):
    """An offscreen view with the bar transport captured (no page)."""
    chart = LwcChartView()
    sent = []
    chart._bridge.send_ops = lambda ops: sent.append(list(ops))
    chart._bridge.send_channel = lambda channel, ops: None
    chart._captured_bar_ops = sent
    return chart


def test_P11_T5_T51_same_symbol_replace_preserves_viewport_follow(view):
    """P11-T5-T51: same-symbol full replace preserves viewport + follow."""
    view.set_symbol("AAA")
    view.set_timeframe("1 min")
    view.update_bars(_bars("AAA", BASE_TS, 20))

    # First load of a symbol has no prior replace and no report: it is a
    # new-symbol load and follows (fits) the live edge.
    first = view._captured_bar_ops[-1]
    assert _set_bars(first)["same_symbol"] is False
    assert _set_volume(first)["same_symbol"] is False

    # Scroll back: the newest slot (19) sits outside [2, 10]; not following.
    assert view.report_viewport({"from": 2, "to": 10}, following=False) is True

    view._captured_bar_ops.clear()
    n_interaction = len(view.interaction_ops)

    # Backfill-shaped same-symbol replace: five older bars prepended.
    view.update_bars(_bars("AAA", BASE_TS - 5 * 60, 25))

    ops = view._captured_bar_ops[-1]
    candles = _set_bars(ops)
    volume = _set_volume(ops)
    # Continuity: the page re-applies its own pre-replace range — no fit,
    # no jump — so both ops are stamped for preservation.
    assert candles["same_symbol"] is True
    assert volume["same_symbol"] is True
    # The whole backfilled series crossed (no truncation to the old window).
    assert len(candles["cols"]["ts"]) == 25
    # No stale restore op crosses: the page already holds the freshest
    # range, and a throttled Python report must never yank it (AR-P11-2).
    assert len(view.interaction_ops) == n_interaction
    # Follow state preserved: the pending viewport is untouched and still
    # scrolled back (slot-identical, not following).
    assert view._pending_viewport == {
        "range": {"from": 2.0, "to": 10.0}, "following": False}


def test_P11_T5_T52_new_symbol_follows_and_zero_bar_fit_is_noop(view):
    """P11-T5-T52: new symbol follows; zero-bar Fit is a no-op, no error."""
    view.set_symbol("AAA")
    view.set_timeframe("1 min")
    view.update_bars(_bars("AAA", BASE_TS, 20))

    # A new symbol with no remembered viewport: the replace carries no
    # continuity and no restore op, so the page fits to the live edge.
    view.set_symbol("BBB")
    view._captured_bar_ops.clear()
    n_interaction = len(view.interaction_ops)
    view.update_bars(_bars("BBB", BASE_TS, 10))

    ops = view._captured_bar_ops[-1]
    assert _set_bars(ops)["same_symbol"] is False
    assert _set_volume(ops)["same_symbol"] is False
    assert len(_set_bars(ops)["cols"]["ts"]) == 10
    assert len(view.interaction_ops) == n_interaction

    # Zero-bar series (Journey 44 edge): the replace crosses empty columns
    # with no error, and Fit (reset) on the empty series is accepted —
    # the page-side fit is defined as a no-op there, never an error.
    view.set_series("candles", [])
    empty = view._captured_bar_ops[-1]
    assert _set_bars(empty)["cols"]["ts"] == []
    assert _set_volume(empty)["cols"]["value"] == []
    result = view.handle_control("reset")
    assert result["op"]["op"] == "reset_view"
    assert result["refused"] is False
