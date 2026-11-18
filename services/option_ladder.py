"""Pure, Qt-free option-ladder geometry, naming and arithmetic (D65).

This module is the decision layer behind the Option Spreads dock. It owns every
option-geometry and arithmetic rule the panel and its engine share:

* the 20-wide ladder, built from **one per-side, row-ordered** offset table:
  rows read top to bottom as ``+10, +5, 0, -5`` on a CCS (anchor on row 3) and
  ``+5, 0, -5, -10`` on a PCS (anchor on row 2), each offset measured from the
  anchor short strike (:data:`SPREAD_WIDTH`, :data:`STRIKE_STEP`,
  :data:`RUNG_OFFSETS`, :func:`ladder_pairs`);
* the short-leg-first row name (:func:`format_instrument`);
* the displayed/credit sign pair -- the module's only sign decision
  (:func:`display_bases`, :func:`credit_bases`);
* the tick-derived match band (:func:`option_tick`, :func:`match_band`);
* the quote-validity screen (:func:`usable_quote`);
* the three-basis metric and the net greeks (:func:`distance`,
  :func:`net_greeks`);
* rung snapping, the four-rung window legs and the cell formatters
  (:func:`snap_rung`, :func:`window_legs`, :func:`format_ask`,
  :func:`format_bid`, :func:`format_delta`, :func:`format_gamma`).

No search and no stepping live here: the seed strike is the engine's (P23-T7)
and the walk is the engine's window step (P23-T8).

Public API::

    SPREAD_WIDTH, STRIKE_STEP, RUNG_OFFSETS, SIDES
    LegKey(right, strike)
    SpreadRow(rung, short, long, display_name, display_ask, display_bid,
              delta, gamma, matched)
    ladder_pairs(anchor_short, side="CCS")             -> list[tuple[float, float]]
    window_legs(anchor_short, side="CCS")              -> list[LegKey]
    format_instrument(symbol, expiry, short, long)     -> str
    display_bases(bid_s, ask_s, bid_l, ask_l)          -> (display_ask, display_bid)
    credit_bases(bid_s, ask_s, bid_l, ask_l)           -> (credit_bid, credit_ask, credit_mid)
    option_tick(target) / match_band(target)           -> float
    usable_quote(bid, ask, received_bid, received_ask) -> (bid | None, ask | None)
    distance(target, credit_bid, credit_ask, credit_mid) -> float
    net_greeks(delta_s, delta_l, gamma_s, gamma_l)     -> (delta | None, gamma | None)
    snap_rung(strike, listed, anchor)                  -> float | None
    format_ask / format_bid / format_delta / format_gamma

No PyQt6/pyqtgraph/Qt import appears anywhere in this module; importing it needs
no ``QApplication`` and opens no IBKR connection.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

# ── Geometry ─────────────────────────────────────────────────────────────────

#: Width of one spread in index points (4 rungs of the 5-point strike grid).
SPREAD_WIDTH = 20
#: Distance between adjacent listed strikes, in index points.
STRIKE_STEP = 5

#: The two sides, exactly as the panel labels them.
SIDE_CCS = "CCS"
SIDE_PCS = "PCS"
SIDES = (SIDE_CCS, SIDE_PCS)

#: The single per-side offset table, in display-row order (top row first): each
#: side maps to a 4-tuple of (logical label, short-strike offset from the anchor
#: short strike).  CCS rows read +10, +5, 0, -5 with the anchor on row 3; PCS
#: rows read +5, 0, -5, -10 with the anchor on row 2.  There is no second
#: offset table under any other name.
RUNG_OFFSETS = {
    SIDE_CCS: ((1, 10), (2, 5), (3, 0), (4, -5)),
    SIDE_PCS: ((4, 5), (3, 0), (2, -5), (1, -10)),
}

#: Option tick tiers: below 3.00 the tick is 0.05, at and above it 0.10.
TICK_BREAK = 3.00
SMALL_TICK = 0.05
LARGE_TICK = 0.10
#: The match band never narrows below this.
MIN_BAND = 0.05


@dataclass(frozen=True)
class LegKey:
    """One option leg: its right (``"C"`` / ``"P"``) and its strike."""

    right: str
    strike: float


@dataclass
class SpreadRow:
    """One displayed ladder row -- the engine's unit, the panel's row payload.

    ``rung`` is the 1-based **display row**: the row's position top to bottom
    (``1..4``) on either side.  The owner's logical labels are specification
    data only and run ``4, 3, 2, 1`` against those positions on a PCS
    (``1, 2, 3, 4`` on a CCS).  Nothing renders a label digit or a row-number
    column.
    """

    rung: int
    short: float
    long: float
    display_name: str
    display_ask: Optional[float]
    display_bid: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    matched: bool


_RIGHT_BY_SIDE = {SIDE_CCS: "C", SIDE_PCS: "P"}


def _side_key(side: str) -> str:
    """Normalise ``side`` to ``"CCS"`` / ``"PCS"`` or raise ``ValueError``."""
    key = str(side).strip().upper()
    if key not in SIDES:
        raise ValueError(f"unknown option side {side!r}: expected one of {SIDES}")
    return key


def ladder_pairs(anchor_short: float, side: str = SIDE_CCS) -> List[Tuple[float, float]]:
    """The four 20-wide spreads of one side, in display-row order, top row first.

    Row ``n``'s short strike is ``anchor_short`` plus that side's offset from
    :data:`RUNG_OFFSETS`, read in tuple order and never sorted by label: a CCS
    reads ``+10, +5, 0, -5`` (anchor on row 3), a PCS ``+5, 0, -5, -10``
    (anchor on row 2).  The long leg sits exactly :data:`SPREAD_WIDTH` away in
    the side's direction: above the short for a CCS (short below long), below
    it for a PCS (short above long).

    The anchor short strike is the offset-0 row, so the canonical CCS
    ``7425/7445`` is ``ladder_pairs(7425)[2]`` (anchor on row 3) and the
    canonical PCS ``7325/7305`` is ``ladder_pairs(7325, SIDE_PCS)[1]`` (anchor
    on row 2).
    """
    anchor = float(anchor_short)
    key = _side_key(side)
    pairs: List[Tuple[float, float]] = []
    for _label, offset in RUNG_OFFSETS[key]:
        short = anchor + offset
        if key == SIDE_CCS:
            long = short + SPREAD_WIDTH
        else:
            long = short - SPREAD_WIDTH
        pairs.append((short, long))
    return pairs


# ── Naming ───────────────────────────────────────────────────────────────────

_MONTH_ABBREVIATIONS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _format_expiry(expiry) -> str:
    """``Nov17`` from a date/datetime (or pass an already-formatted string)."""
    if isinstance(expiry, str):
        return expiry.strip()
    month = getattr(expiry, "month", None)
    day = getattr(expiry, "day", None)
    if month is not None and day is not None:
        return f"{_MONTH_ABBREVIATIONS[int(month) - 1]}{int(day)}"
    raise TypeError(f"unsupported expiry {expiry!r}: expected a date/datetime or a string")


def _format_strike(strike: float) -> str:
    """``7425`` for whole strikes, ``7425.5`` otherwise."""
    value = float(strike)
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def format_instrument(symbol: str, expiry, short: float, long: float) -> str:
    """Render a row name short-leg-first: ``SPX Nov17 7425/7445``.

    The short strike always comes first, so a CCS reads short/long (7425/7445)
    and a PCS reads its higher short strike first (7340/7320).
    """
    return (
        f"{str(symbol).strip()} {_format_expiry(expiry)} "
        f"{_format_strike(short)}/{_format_strike(long)}"
    )


# ── The sign pair (the module's only sign decision) ──────────────────────────


def display_bases(
    bid_s: float, ask_s: float, bid_l: float, ask_l: float
) -> Tuple[float, float]:
    """The displayed ladder values, as ``(display_ask, display_bid)``.

    ``display_ask = long.ask - short.bid`` and ``display_bid = long.bid -
    short.ask``.  A credit spread's long leg is the cheaper one, so a credit
    pair renders negative in the panel by design.
    """
    display_ask = float(ask_l) - float(bid_s)
    display_bid = float(bid_l) - float(ask_s)
    return display_ask, display_bid


def credit_bases(
    bid_s: float, ask_s: float, bid_l: float, ask_l: float
) -> Tuple[float, float, float]:
    """The credit bases: ``(credit_bid, credit_ask, credit_mid)``.

    Exactly the negatives of :func:`display_bases` -- ``credit_bid =
    -display_ask`` (the ASK cell's counterpart) and ``credit_ask =
    -display_bid`` (the BID cell's counterpart) -- with ``credit_mid`` their
    mean.  Every match and score runs on these credit bases; the panel renders
    the negative display pair.

    Together with :func:`display_bases` this is the module's only sign
    decision -- no caller negates a price.
    """
    display_ask, display_bid = display_bases(bid_s, ask_s, bid_l, ask_l)
    credit_bid = -display_ask
    credit_ask = -display_bid
    credit_mid = (credit_bid + credit_ask) / 2.0
    return credit_bid, credit_ask, credit_mid


# ── The tick-derived match band ──────────────────────────────────────────────


def option_tick(target: float) -> float:
    """The option's price tick at ``target``: 0.05 below 3.00, 0.10 from 3.00."""
    return SMALL_TICK if float(target) < TICK_BREAK else LARGE_TICK


def match_band(target: float) -> float:
    """The match band around ``target``: its tier tick, never below 0.05."""
    return max(MIN_BAND, option_tick(target))


# ── Quote validity ───────────────────────────────────────────────────────────


def _usable_price(value, received) -> Optional[float]:
    """One side of a leg's quote, or ``None`` when it is absent."""
    if not received or value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(price):
        return None
    if price == -1:
        return None
    if price >= sys.float_info.max:
        return None
    if price < 0:
        return None
    return price


def usable_quote(
    bid, ask, received_bid, received_ask
) -> Tuple[Optional[float], Optional[float]]:
    """Screen one leg's quote as ``(bid | None, ask | None)``.

    A **received 0 bid is a real price and stays usable**.  Each sentinel --
    ``-1``, ``1.7976931348623157e+308`` (``sys.float_info.max``), NaN,
    ``+/-inf`` -- and each unreceived side reports that side absent, as does a
    crossed quote (``bid > ask``).  A leg with either side absent returns
    ``(None, None)``, so no pair can be scored or matched on one side alone.
    """
    usable_bid = _usable_price(bid, received_bid)
    usable_ask = _usable_price(ask, received_ask)
    if usable_bid is None or usable_ask is None:
        return (None, None)
    if usable_bid > usable_ask:
        return (None, None)
    return (usable_bid, usable_ask)


# ── Metrics ──────────────────────────────────────────────────────────────────


def distance(
    target: float, credit_bid: float, credit_ask: float, credit_mid: float
) -> float:
    """Distance from ``target`` to the nearest of the three credit bases.

    ``min(|credit_mid - T|, |credit_ask - T|, |credit_bid - T|)``, computed on
    the credits only -- never on the displayed negative values.
    """
    level = float(target)
    return min(
        abs(float(credit_mid) - level),
        abs(float(credit_ask) - level),
        abs(float(credit_bid) - level),
    )


def _net(short_value, long_value) -> Optional[float]:
    if short_value is None or long_value is None:
        return None
    return float(long_value) - float(short_value)


def net_greeks(
    delta_s, delta_l, gamma_s, gamma_l
) -> Tuple[Optional[float], Optional[float]]:
    """``(long - short)`` for delta and for gamma, independently.

    A ``None`` side propagates as ``None`` rather than as a number, so a
    half-quoted spread never invents a greek.
    """
    return _net(delta_s, delta_l), _net(gamma_s, gamma_l)


# ── Snapping and the four-rung window ────────────────────────────────────────


def _has_partner(strike: float, listed: Iterable[float]) -> bool:
    """True when a strike exactly ``SPREAD_WIDTH`` away is also listed."""
    return any(
        math.isclose(abs(float(other) - strike), SPREAD_WIDTH, abs_tol=1e-9)
        for other in listed
    )


def snap_rung(strike: float, listed: Sequence[float], anchor: float) -> Optional[float]:
    """The listed rung ``strike`` snaps to, or ``None``.

    A listed strike is a usable rung only when a strike exactly
    :data:`SPREAD_WIDTH` away is listed too, so ``None`` means no listed
    20-wide pair exists.  Among the usable rungs the nearest to ``strike``
    wins; an equidistant tie resolves to the strike nearer ``anchor`` (and then
    to the lower strike).
    """
    level = float(strike)
    anchor_value = float(anchor)
    candidates = sorted(
        {float(value) for value in listed},
        key=lambda value: (abs(value - level), abs(value - anchor_value), value),
    )
    for candidate in candidates:
        if _has_partner(candidate, candidates):
            return candidate
    return None


def window_legs(anchor_short: float, side: str = SIDE_CCS) -> List[LegKey]:
    """The eight legs of the four-rung window, per rung short then long.

    Four rungs x two legs.  Every leg carries the side's right -- ``"C"`` for a
    CCS window, ``"P"`` for a PCS window -- so the caller can subscribe to
    exactly the eight contracts the window needs.
    """
    key = _side_key(side)
    right = _RIGHT_BY_SIDE[key]
    legs: List[LegKey] = []
    for short, long in ladder_pairs(anchor_short, key):
        legs.append(LegKey(right=right, strike=short))
        legs.append(LegKey(right=right, strike=long))
    return legs


# ── Cell formatters ──────────────────────────────────────────────────────────


def _format_value(value, spec: str) -> str:
    if value is None:
        return ""
    return format(float(value), spec)


def format_ask(value) -> str:
    """An ASK cell: 2 decimal places (``""`` for an absent side)."""
    return _format_value(value, ".2f")


def format_bid(value) -> str:
    """A BID cell: 2 decimal places (``""`` for an absent side)."""
    return _format_value(value, ".2f")


def format_delta(value) -> str:
    """A Delta cell: 3 decimal places (``""`` for an absent side)."""
    return _format_value(value, ".3f")


def format_gamma(value) -> str:
    """A Gamma cell: 4 significant digits (``""`` for an absent side)."""
    return _format_value(value, ".4g")
