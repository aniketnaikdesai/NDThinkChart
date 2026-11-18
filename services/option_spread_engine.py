"""Pure, Qt-free and ibapi-free option-spread seeding engine (D65, part 1).

This module is the first half of the Option Spreads decision layer: the state
machine that *finds* the anchor by measurement and owns the lease accounting.
It is fed a chain and leg quotes and emits an :class:`Actions` plan -- it never
touches Qt, a window, IBKR or the network. The second half (the walk, the
lifecycle and the error classes) is P23-T8's and extends the same module.

What lives here
---------------
* **The seed ladder** (``AC-D65.15``) -- three tiers, in order:

  1. the **session anchor** for today's expiry, when this session already
     produced one for the current target (no probe lease at all);
  2. otherwise a **bounded coarse probe**: at most
     :data:`PROBES_PER_SIDE` pairs per side, spaced :data:`PROBE_SPACING`
     apart, each pair leased against free capacity, scored and *released
     immediately*;
  3. then a **5-point refine** by window steps around the best probe.

  Every branch of a seed runs through the same total ordering, so the same
  chain and the same quotes reach the same final rung whichever tier supplied
  the starting point.

* **The sweep bound** (``AC-D65.15``) -- a seed stops at
  :data:`SCORED_PAIR_LIMIT` scored pairs or :data:`WALL_CLOCK_LIMIT` seconds,
  whichever comes first, keeps the best-known pair, latches exactly one
  message naming the bound and the value, and re-arms only at the next cadence
  evaluation. The bound is checked against the injected clock; nothing in this
  module measures or advances real time itself.

* **Quote validity and pending legs** (``AC-D65.16``) -- a pair is scored and
  match-eligible only when *both* its legs quote; a leg without a tick becomes
  ``pending`` after :data:`PENDING_SECONDS`; a received zero bid is a live
  price; every sentinel (``-1``, ``sys.float_info.max``, a no-tick zero, NaN,
  ``+/-inf``) and every unreceived side is absent and never reaches the
  distance computation.

* **The metric and the anchor** (``AC-D65.3``) -- the anchor is the listed
  20-wide pair minimising
  ``d = min(|credit_mid - T|, |credit_ask - T|, |credit_bid - T|)`` on the
  **credit** bases only; ties break by smaller ``|credit_mid - T|``, then
  ``credit_mid >= T``, then the short strike nearer the underlying's last
  price (the lower short strike when no price exists).

* **The band** (``AC-D65.4``) -- the band gating match and movement is
  :func:`services.option_ladder.match_band` of the target, read from the tick
  tiers and never derived from a quote.

* **The lease pool** (``AC-D65.6`` planning half) -- every emitted action is
  one of ``lease`` / ``subscribe`` / ``cancel`` / ``release``, the live option
  line count never exceeds :data:`MAX_OPTION_LINES`, a lease is refused when
  the live window occupies the capacity, and no action ever leases or
  subscribes a leg the live window already holds. Window legs are issued in
  the deterministic order CCS 3, 2, 4, 1 then PCS 3, 2, 4, 1.

The second half (``P23-T8``) adds the maintenance surface on the same class:

* **The window walk** (``AC-D65.4``) -- :meth:`SpreadEngine.window_step` emits at
  most one 5-point step per side toward the requested anchor, in the
  toward-the-money / away-from-the-money direction the live pair's credit bases
  decide, only when that step improves ``d`` by more than ``h``; it stops on a
  matched pair, on a step that does not improve enough, and on a rung that is
  not a listed pair (one chain-edge message). Every step cancels before it
  subscribes, and a leg present in both windows keeps its line and its reqId.
* **The greek sources** (``AC-D65.5``) -- :meth:`SpreadEngine.row_greeks` reads a
  row from the model greek (13) when both legs carry one, else last (12) for
  both, else the mean of bid (10) and ask (11) for both; the legs are never
  mixed, and a mixed pair shows no value with exactly one message.
* **The connection lifecycle** (``AC-D65.14``) -- a disconnect freezes the walk
  and marks every cell STALE without cancelling anything; a reconnect resumes
  from the same anchor and re-seeds once only if a leg is still silent past the
  3 s timeout. The engine owns no reconnect mechanism of its own.
* **The per-line error classes** (``AC-D65.14``) -- ``200`` on a non-anchor pair
  drops that pair for the session, ``200`` on the anchor pair re-seats exactly
  one step toward the money and retries once, ``10197``/``354``/unclassified
  show no value with no re-seat, and ``162`` keeps the line with its values
  going STALE after the timeout.

Public API::

    SpreadEngine(clock=None, target=1.00)
    toggle_on() / toggle_off() / set_target(target)
    on_chain(series) / on_no_expiry() / on_quote(leg, bid, ask, rb, ra) /
    on_spot(price)
    begin_seed(now) / seed_actions() / seed_state() / evaluate(now)
    live_legs() -> set[LegKey]
    lease(side, short, long) -> bool / release(side, short, long)
    pair_score(side, short, long) / pair_eligible(side, short, long)
    leg_state(leg) / rows() / band
    window_step(target_anchor) -> Actions
    on_greek(leg, tick_type, delta, gamma) / row_greeks(side, short, long)
    on_leg_error(leg, code) / on_disconnected() / on_reconnected() /
    rebind_leg(leg, new_req_id)
    req_id(leg) / leg_stale(leg) / stale_legs() / walk_frozen /
    pair_dropped(side, short) / reseat_count(side) / take_messages()

No PyQt6/pyqtgraph/Qt import appears anywhere in this module, and no ``ibapi``
import either: the chain is consumed duck-typed (``expiry`` and
``strikes_by_right``), so importing this module needs no ``QApplication`` and
opens no IBKR connection.
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from services.option_ladder import (
    SIDES,
    SIDE_CCS,
    SIDE_PCS,
    SPREAD_WIDTH,
    STRIKE_STEP,
    LegKey,
    SpreadRow,
    credit_bases,
    display_bases,
    distance,
    format_instrument,
    ladder_pairs,
    match_band,
    net_greeks,
    snap_rung,
    usable_quote,
    window_legs,
)

#: The panel's option-slot budget (``AC-D65.6``): 16 live option lines.
MAX_OPTION_LINES = 16
#: At most this many coarse probe pairs per side.
PROBES_PER_SIDE = 6
#: Coarse probe spacing, in index points.
PROBE_SPACING = 20.0
#: The sweep bound: 12 scored pairs ...
SCORED_PAIR_LIMIT = 12
#: ... or 10 s wall clock, whichever comes first.
WALL_CLOCK_LIMIT = 10.0
#: A subscribed leg with no tick is ``pending`` after this long.
PENDING_SECONDS = 3.0

_SIDE_RIGHT = {SIDE_CCS: "C", "PCS": "P"}
# The deterministic window issue order: rungs 3, 2, 4, 1 (short then long).
# ``window_legs`` returns rungs 1..4, so these are its leg indices.
_WINDOW_ISSUE_ORDER = (4, 5, 2, 3, 6, 7, 0, 1)

CAUSE_NO_0DTE = "no-0DTE"
CAUSE_CHAIN_EDGE = "chain-edge"
CAUSE_RUNG_SHORTFALL = "rung-shortfall"
CAUSE_BUDGET_REFUSAL = "budget-refusal"
CAUSE_SEED_BOUND = "seed-bound"

#: Greek tick types, in the ``AC-D65.5`` precedence order.
GREEK_MODEL = 13
GREEK_LAST = 12
GREEK_BID = 10
GREEK_ASK = 11
#: The three greek sources, most authoritative first.
SOURCE_MODEL = "model"
SOURCE_LAST = "last"
SOURCE_BIDASK = "bidask_mean"

CAUSE_WALK_CHAIN_EDGE = "walk-chain-edge"
CAUSE_GREEK_MIXED = "greek-mixed"
CAUSE_LINE_200_PAIR = "line-200-pair"
CAUSE_LINE_200_ANCHOR = "line-200-anchor"
CAUSE_LINE_200_STOP = "line-200-stop"
CAUSE_LINE_10197 = "line-10197"
CAUSE_LINE_354 = "line-354"
CAUSE_LINE_162 = "line-162"
CAUSE_LINE_OTHER = "line-unclassified"


@dataclass(frozen=True)
class Quote:
    """One leg's last tick, exactly as received (sentinels are not screened here)."""

    bid: float
    ask: float
    received_bid: bool
    received_ask: bool
    at: float


@dataclass(frozen=True)
class Action:
    """One emitted plan action: ``lease`` / ``subscribe`` / ``cancel`` / ``release``."""

    kind: str
    legs: Tuple[LegKey, ...] = ()
    side: Optional[str] = None
    pair: Optional[Tuple[float, float]] = None
    reason: str = ""


@dataclass
class Actions:
    """The engine's emitted plan for one step (the panel's unit of work)."""

    subscribes: List[LegKey] = field(default_factory=list)
    cancels: List[LegKey] = field(default_factory=list)
    spot_subscribe: bool = False
    spot_cancel: bool = False
    rows: Dict[str, List[SpreadRow]] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    empty_state: Optional[str] = None
    status: str = "idle"
    #: The same plan as an ordered action list, so lease accounting is assertable.
    actions: List[Action] = field(default_factory=list)
    #: Cells whose last value is held but marked STALE (disconnect / 162 timeout).
    stale_legs: Set[LegKey] = field(default_factory=set)


@dataclass(frozen=True)
class PairScore:
    """One scoreable 20-wide pair: its credit bases and its distance to the target."""

    side: str
    short: float
    long: float
    credit_bid: float
    credit_ask: float
    credit_mid: float
    distance: float


@dataclass(frozen=True)
class Greeks:
    """One row's net greeks and the source they were read from.

    ``source`` is one of ``"model"`` (tick type 13), ``"last"`` (12) or
    ``"bidask_mean"`` (the mean of 10 and 11) -- the two legs of a row always
    share one source, never a mixture.
    """

    delta: Optional[float]
    gamma: Optional[float]
    source: str


@dataclass(frozen=True)
class SeedState:
    """A read-only snapshot of the seed ladder."""

    active: bool
    phase: str
    scored: int
    probes: Dict[str, int]
    bounded: Optional[str]
    anchors: Dict[str, float]
    warm: Dict[str, bool]


@dataclass
class _SideSeed:
    phase: str = "probe"          # probe | refine | commit | done
    queue: List[float] = field(default_factory=list)
    index: int = 0
    best: Optional[PairScore] = None
    outstanding: Optional[Tuple[float, float]] = None
    leased_at: float = 0.0
    scores: List[PairScore] = field(default_factory=list)
    probe_pairs: int = 0


def _right(side: str) -> str:
    return _SIDE_RIGHT[side]


def _q(value: float) -> float:
    """Quantise a rank key so exact metric ties are not broken by float noise."""
    return round(float(value), 9)


class SpreadEngine:
    """The pure option-spread seeding state machine (D65, part 1)."""

    def __init__(self, clock: Optional[Callable[[], float]] = None, target: float = 1.00):
        self._clock = clock
        self._now_value: Optional[float] = None
        self._target = float(target)
        self._on = False
        self._series = None
        self._expiry = ""
        self._symbol = "SPX"
        self._quotes: Dict[LegKey, Quote] = {}
        self._spot: Optional[float] = None
        self._spot_subscribed = False

        # Lease pool: ``_leased`` reserves a slot, ``_subscribed`` is a live line.
        self._leased: Set[LegKey] = set()
        self._subscribed: Set[LegKey] = set()
        self._subscribed_at: Dict[LegKey, float] = {}

        # The committed window, per side.
        self._window_legs: Dict[str, List[LegKey]] = {}
        self._anchors: Dict[str, float] = {}
        # The session's measured anchor, per side (today's expiry only).
        self._session_anchor: Dict[str, float] = {}
        self._session_anchor_expiry = ""

        # Seed ladder.
        self._seed_active = False
        self._seed_started = 0.0
        self._seed_scored = 0
        self._seed_bounded: Optional[str] = None
        self._seed_sides: Dict[str, _SideSeed] = {}

        # Once-only messages.
        self._latched: Set[str] = set()
        self._pending_messages: List[str] = []

        # Part 2: line identity (reqId), per-cell state, the connection lifecycle
        # and the per-line error classes.
        self._req_ids: Dict[LegKey, int] = {}
        self._greeks: Dict[LegKey, Dict[int, Tuple[float, float]]] = {}
        self._dropped: Set[LegKey] = set()
        self._no_value: Set[LegKey] = set()
        self._stale: Set[LegKey] = set()
        self._stale_after: Dict[LegKey, float] = {}
        self._walk_frozen = False
        self._disconnected_at: Optional[float] = None
        self._reconnect_at: Optional[float] = None
        self._reseed_done = False
        self._pending_reseat: Dict[str, float] = {}
        self._reseat_counts: Dict[str, int] = {}

    # ── Clock ────────────────────────────────────────────────────────────────

    def _now(self) -> float:
        """The injected clock's reading (the engine never reads wall time itself)."""
        if self._clock is not None:
            return float(self._clock())
        if self._now_value is not None:
            return float(self._now_value)
        return time.monotonic()

    # ── Messages ─────────────────────────────────────────────────────────────

    def _latch(self, cause: str, message: str) -> None:
        """Latch ``cause``'s message exactly once (``AC-D65.15`` per-cause messages)."""
        if cause in self._latched:
            return
        self._latched.add(cause)
        self._pending_messages.append(message)

    def _drain(self) -> List[str]:
        messages = list(self._pending_messages)
        self._pending_messages.clear()
        return messages

    def latched_causes(self) -> List[str]:
        """The causes whose one message has been latched, in no particular order."""
        return sorted(self._latched)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def toggle_on(self) -> None:
        self._on = True

    def toggle_off(self) -> None:
        self._on = False
        self._seed_active = False

    @property
    def target(self) -> float:
        return self._target

    def set_target(self, target: float) -> None:
        """Set the Target; a new Target invalidates the session's measurement."""
        value = float(target)
        if not math.isfinite(value):
            raise ValueError(f"target must be finite, got {target!r}")
        self._target = value
        # The session anchor was measured for the old Target -- re-measure.
        self._session_anchor.clear()
        self._seed_bounded = None

    @property
    def band(self) -> float:
        """``h``, read from the Target's tick tier and never from a quote."""
        return match_band(self._target)

    # ── Chain ────────────────────────────────────────────────────────────────

    def on_chain(self, series) -> None:
        """Accept today's 0DTE series (duck-typed: ``expiry``/``strikes_by_right``)."""
        if series is None:
            self.on_no_expiry()
            return
        expiry = str(getattr(series, "expiry", "") or "")
        if self._session_anchor_expiry and expiry and expiry != self._session_anchor_expiry:
            # A different expiry is a different session measurement and window.
            self._session_anchor.clear()
            self._anchors.clear()
            self._window_legs.clear()
            self._leased.clear()
            self._subscribed.clear()
            self._subscribed_at.clear()
        self._series = series
        self._expiry = expiry
        self._symbol = str(getattr(series, "symbol", "SPX") or "SPX")
        self._session_anchor_expiry = expiry

    def on_no_expiry(self) -> None:
        """Today's chain has no 0DTE SPXW expiry: the chain-level empty state."""
        self._series = None
        self._expiry = ""
        self._anchors.clear()
        self._window_legs.clear()
        self._seed_active = False
        self._latch(
            CAUSE_NO_0DTE,
            "No 0DTE SPXW expiry is listed today; the spread ladders are empty.",
        )

    # ── Inputs ───────────────────────────────────────────────────────────────

    def on_quote(self, leg: LegKey, bid, ask, received_bid, received_ask) -> None:
        """Store one leg's last tick, exactly as received (screening is at use).

        A fresh tick is the cell's own recovery: it clears the leg's STALE flag,
        its ``162`` timeout and any "no value" state it was showing.
        """
        self._stale.discard(leg)
        self._stale_after.pop(leg, None)
        self._no_value.discard(leg)
        self._quotes[leg] = Quote(
            bid=bid,
            ask=ask,
            received_bid=bool(received_bid),
            received_ask=bool(received_ask),
            at=self._now(),
        )

    def on_spot(self, price: float) -> None:
        """The underlying's last price; a sentinel or a non-positive value is refused."""
        try:
            value = float(price)
        except (TypeError, ValueError):
            self._spot = None
            return
        if not math.isfinite(value) or value <= 0.0 or value >= 1.7976931348623157e308:
            self._spot = None
            return
        self._spot = value

    @property
    def spot(self) -> Optional[float]:
        return self._spot

    # ── Geometry helpers ─────────────────────────────────────────────────────

    def _listed(self, side: str) -> List[float]:
        series = self._series
        if series is None:
            return []
        by_right = getattr(series, "strikes_by_right", None) or {}
        try:
            values = by_right.get(_right(side), [])
        except AttributeError:  # pragma: no cover - defensive
            return []
        return sorted(float(value) for value in values)

    def _long_for(self, side: str, short: float) -> float:
        return float(short) + SPREAD_WIDTH if side == SIDE_CCS else float(short) - SPREAD_WIDTH

    def _pair_listed(self, side: str, short: float) -> bool:
        long = self._long_for(side, short)
        return any(math.isclose(other, long, abs_tol=1e-9) for other in self._listed(side))

    def _pair_quote(
        self, side: str, short: float, long: float
    ) -> Optional[Tuple[float, float, float, float]]:
        """Both legs' usable ``(bid, ask)`` pairs, or ``None`` when the pair cannot score."""
        right = _right(side)
        short_quote = self._quotes.get(LegKey(right=right, strike=float(short)))
        long_quote = self._quotes.get(LegKey(right=right, strike=float(long)))
        if short_quote is None or long_quote is None:
            return None
        bid_s, ask_s = usable_quote(
            short_quote.bid,
            short_quote.ask,
            short_quote.received_bid,
            short_quote.received_ask,
        )
        bid_l, ask_l = usable_quote(
            long_quote.bid,
            long_quote.ask,
            long_quote.received_bid,
            long_quote.received_ask,
        )
        if bid_s is None or bid_l is None:
            return None
        return bid_s, ask_s, bid_l, ask_l

    def _score_pair_complete(
        self, side: str, short: float, long: float
    ) -> Optional[PairScore]:
        """The pair's score, or ``None`` when either leg is absent (``AC-D65.16``)."""
        quote = self._pair_quote(side, short, long)
        if quote is None:
            return None
        bid_s, ask_s, bid_l, ask_l = quote
        credit_bid, credit_ask, credit_mid = credit_bases(bid_s, ask_s, bid_l, ask_l)
        return PairScore(
            side=side,
            short=float(short),
            long=float(long),
            credit_bid=credit_bid,
            credit_ask=credit_ask,
            credit_mid=credit_mid,
            distance=distance(self._target, credit_bid, credit_ask, credit_mid),
        )

    def pair_score(self, side: str, short: float, long: float) -> Optional[PairScore]:
        """Public probe: the pair's score, or ``None`` when it is not scoreable."""
        return self._score_pair_complete(side, short, long)

    def pair_eligible(self, side: str, short: float, long: float) -> bool:
        """True only when both legs quote and the pair can be scored and matched."""
        return self._score_pair_complete(side, short, long) is not None

    def _score_at(self, side: str, short: float) -> Optional[PairScore]:
        return self._score_pair_complete(side, float(short), self._long_for(side, float(short)))

    def _rank(self, score: PairScore) -> Tuple[float, float, int, float, float]:
        """The ``AC-D65.3`` total order: d, |mid-T|, mid>=T, spot distance, short."""
        if self._spot is None:
            spot_key = 0.0
        else:
            spot_key = abs(score.short - self._spot)
        return (
            _q(score.distance),
            _q(abs(score.credit_mid - self._target)),
            0 if score.credit_mid >= self._target else 1,
            _q(spot_key),
            score.short,
        )

    def _best_of(self, scores: Sequence[PairScore]) -> Optional[PairScore]:
        usable = [score for score in scores if score is not None]
        if not usable:
            return None
        return min(usable, key=self._rank)

    def _best_neighbour(self, side: str, anchor: float) -> Optional[PairScore]:
        candidates = []
        for short in (anchor - STRIKE_STEP, anchor, anchor + STRIKE_STEP):
            if not self._pair_listed(side, short):
                continue
            candidates.append(self._score_at(side, short))
        return self._best_of([score for score in candidates if score is not None])

    # ── Lease pool ───────────────────────────────────────────────────────────

    def live_legs(self) -> Set[LegKey]:
        """The legs currently holding a live option line."""
        return set(self._subscribed)

    def _emit(self, acts: Optional[Actions], action: Action) -> None:
        if acts is not None:
            acts.actions.append(action)

    def _lease_pair(
        self,
        acts: Optional[Actions],
        side: str,
        short: float,
        long: float,
        reason: str = "probe",
    ) -> bool:
        """Lease + subscribe a pair's two legs, refusing when the capacity is full.

        Refusal latches the ``budget-refusal`` cause exactly once and leaves the
        pool untouched, so the live line count can never exceed the budget.
        """
        right = _right(side)
        legs = (LegKey(right=right, strike=float(short)), LegKey(right=right, strike=float(long)))
        new_leases = [leg for leg in legs if leg not in self._leased]
        if len(self._leased) + len(new_leases) > MAX_OPTION_LINES:
            self._latch(
                CAUSE_BUDGET_REFUSAL,
                "Probe refused for capacity: the live window holds all "
                f"{MAX_OPTION_LINES} option lines; seeding from its quotes.",
            )
            return False
        for leg in new_leases:
            self._leased.add(leg)
            self._emit(acts, Action("lease", (leg,), side, (float(short), float(long)), reason))
        for leg in legs:
            if leg in self._subscribed:
                continue
            self._subscribed.add(leg)
            self._subscribed_at[leg] = self._now()
            self._emit(acts, Action("subscribe", (leg,), side, (float(short), float(long)), reason))
            if acts is not None:
                acts.subscribes.append(leg)
        return True

    def _release_pair(
        self, acts: Optional[Actions], side: str, short: float, long: float, reason: str = "probe"
    ) -> None:
        """Cancel then release a pair's two legs (the probe is always released)."""
        right = _right(side)
        legs = (LegKey(right=right, strike=float(short)), LegKey(right=right, strike=float(long)))
        for leg in legs:
            if leg in self._subscribed:
                self._subscribed.discard(leg)
                self._subscribed_at.pop(leg, None)
                self._emit(
                    acts, Action("cancel", (leg,), side, (float(short), float(long)), reason)
                )
                if acts is not None:
                    acts.cancels.append(leg)
        for leg in legs:
            if leg in self._leased:
                self._leased.discard(leg)
                self._emit(
                    acts, Action("release", (leg,), side, (float(short), float(long)), reason)
                )

    def lease(self, side: str, short: float, long: float) -> bool:
        """Public lease: ``False`` when the live window occupies the capacity."""
        return self._lease_pair(None, side, short, long, reason="manual")

    def release(self, side: str, short: float, long: float) -> None:
        """Public release of a leased pair."""
        self._release_pair(None, side, short, long, reason="manual")

    def _window_legs_for(self, side: str, anchor: float) -> List[LegKey]:
        """The side's eight window legs in the deterministic issue order (3,2,4,1)."""
        legs = window_legs(anchor, side)
        return [legs[index] for index in _WINDOW_ISSUE_ORDER]

    def _install_windows(self, acts: Actions, targets: Dict[str, float]) -> bool:
        """Install the requested windows, batching every side's stale legs first.

        Cancels and releases precede the new leases and subscriptions, so the
        live line count dips mid-step (16 -> 14 -> 16) instead of peaking above
        the budget, and a leg already held is never leased or subscribed again.
        """
        if not targets:
            return True
        new_legs: Dict[str, List[LegKey]] = {
            side: self._window_legs_for(side, anchor) for side, anchor in targets.items()
        }
        stale: List[LegKey] = []
        for side, legs in new_legs.items():
            for leg in self._window_legs.get(side, []):
                if leg not in legs and leg not in stale:
                    stale.append(leg)
        added: List[LegKey] = []
        for side, legs in new_legs.items():
            previous = self._window_legs.get(side, [])
            for leg in legs:
                if leg not in previous and leg not in added:
                    added.append(leg)
        for leg in stale:
            if leg in self._subscribed:
                self._subscribed.discard(leg)
                self._subscribed_at.pop(leg, None)
                self._req_ids.pop(leg, None)
                self._stale.discard(leg)
                self._stale_after.pop(leg, None)
                acts.cancels.append(leg)
                self._emit(acts, Action("cancel", (leg,), None, None, "window"))
        for leg in stale:
            if leg in self._leased:
                self._leased.discard(leg)
                self._emit(acts, Action("release", (leg,), None, None, "window"))
        free = MAX_OPTION_LINES - len(self._leased)
        # A leg whose line was dropped for the session is never leased again.
        new_leases = [leg for leg in added if leg not in self._leased and leg not in self._dropped]
        added = [leg for leg in added if leg not in self._dropped]
        if len(new_leases) > free:
            self._latch(
                CAUSE_BUDGET_REFUSAL,
                "Window refused for capacity: the live window holds all "
                f"{MAX_OPTION_LINES} option lines.",
            )
            return False
        for leg in new_leases:
            self._leased.add(leg)
            self._emit(acts, Action("lease", (leg,), None, None, "window"))
        for leg in added:
            if leg in self._subscribed:
                continue
            self._subscribed.add(leg)
            self._subscribed_at[leg] = self._now()
            acts.subscribes.append(leg)
            self._emit(acts, Action("subscribe", (leg,), None, None, "window"))
        for side, legs in new_legs.items():
            self._window_legs[side] = list(legs)
            self._anchors[side] = float(targets[side])
        return True

    def _install_window(self, acts: Actions, side: str, anchor: float) -> bool:
        return self._install_windows(acts, {side: anchor})

    # ── Rows ─────────────────────────────────────────────────────────────────

    def rows(self) -> Dict[str, List[SpreadRow]]:
        """The committed ladder rows per side, with absent cells left empty."""
        out: Dict[str, List[SpreadRow]] = {}
        for side in SIDES:
            anchor = self._anchors.get(side)
            if anchor is None:
                continue
            rows: List[SpreadRow] = []
            right = _right(side)
            for rung, (short, long) in enumerate(ladder_pairs(anchor, side), start=1):
                name = format_instrument(self._symbol, self._expiry, short, long)
                short_leg = LegKey(right=right, strike=float(short))
                long_leg = LegKey(right=right, strike=float(long))
                blocked = (
                    short_leg in self._dropped
                    or long_leg in self._dropped
                    or short_leg in self._no_value
                    or long_leg in self._no_value
                )
                greeks = None if blocked else self.row_greeks(side, short, long)
                delta = greeks.delta if greeks is not None else None
                gamma = greeks.gamma if greeks is not None else None
                quote = None if blocked else self._pair_quote(side, short, long)
                if quote is None:
                    rows.append(
                        SpreadRow(rung, short, long, name, None, None, delta, gamma, False)
                    )
                    continue
                bid_s, ask_s, bid_l, ask_l = quote
                display_ask, display_bid = display_bases(bid_s, ask_s, bid_l, ask_l)
                credit_bid, credit_ask, credit_mid = credit_bases(
                    bid_s, ask_s, bid_l, ask_l
                )
                d = distance(self._target, credit_bid, credit_ask, credit_mid)
                matched = d <= self.band + 1e-9
                rows.append(
                    SpreadRow(
                        rung,
                        short,
                        long,
                        name,
                        display_ask,
                        display_bid,
                        delta,
                        gamma,
                        matched,
                    )
                )
            out[side] = rows
        return out

    def anchor(self, side: str) -> Optional[float]:
        """The committed anchor short strike for ``side``, if any."""
        return self._anchors.get(side)

    def _anchor_matched(self, side: str) -> bool:
        anchor = self._anchors.get(side)
        if anchor is None:
            return False
        score = self._score_at(side, anchor)
        return score is not None and score.distance <= self.band + 1e-9

    # ── Leg state ────────────────────────────────────────────────────────────

    def leg_state(self, leg: LegKey) -> str:
        """``quoted`` / ``pending`` / ``awaiting`` / ``idle`` for one leg."""
        quote = self._quotes.get(leg)
        if quote is not None:
            bid, ask = usable_quote(
                quote.bid, quote.ask, quote.received_bid, quote.received_ask
            )
            if bid is not None:
                return "quoted"
        if leg not in self._subscribed:
            return "idle"
        subscribed_at = self._subscribed_at.get(leg)
        if subscribed_at is not None and self._now() - subscribed_at >= PENDING_SECONDS:
            return "pending"
        return "awaiting"

    def pending_legs(self) -> Set[LegKey]:
        """Every subscribed leg that has been silent for at least 3 s."""
        return {leg for leg in self._subscribed if self.leg_state(leg) == "pending"}

    # ── Seed ladder ──────────────────────────────────────────────────────────

    def begin_seed(self, now: float) -> None:
        """Start (or restart) a seed; the sweep runs from ``now``."""
        self._now_value = float(now)
        if not self._on or self._series is None:
            self._seed_active = False
            return
        self._seed_active = True
        self._seed_started = float(now)
        self._seed_scored = 0
        self._seed_bounded = None
        self._seed_sides = {}
        for side in SIDES:
            session_anchor = self._session_anchor.get(side)
            if session_anchor is not None:
                state = _SideSeed(phase="probe")
                state.queue = []
                state.index = 0
                state.best = self._score_at(side, session_anchor)
                state.phase = "warm"
                self._seed_sides[side] = state
                continue
            state = _SideSeed(phase="probe")
            state.queue = self._probe_queue(side)
            self._seed_sides[side] = state

    def _probe_center(self, side: str) -> float:
        listed = self._listed(side)
        low, high = listed[0], listed[-1]
        if self._spot is None:
            return statistics.median(listed)
        if self._spot < low or self._spot > high:
            self._latch(
                CAUSE_CHAIN_EDGE,
                f"Chain edge: the underlying at {self._spot:g} is outside the listed "
                f"strikes {low:g}-{high:g}; probing from the edge.",
            )
            return min(max(self._spot, low), high)
        return self._spot

    def _probe_queue(self, side: str) -> List[float]:
        """At most six coarse probe shorts, exactly 20 points apart (``AC-D65.15``)."""
        listed = self._listed(side)
        if not listed:
            self._latch(
                CAUSE_RUNG_SHORTFALL,
                "Rung shortfall: the chain lists no strikes for the "
                f"{side} ladder.",
            )
            return []
        center = self._probe_center(side)
        base = snap_rung(center, listed, center)
        if base is None:
            self._latch(
                CAUSE_RUNG_SHORTFALL,
                f"Rung shortfall: no listed 20-wide rung near {center:g}; "
                "the seed keeps the current ladder.",
            )
            return []
        queue: List[float] = []
        for step in (-2, -1, 0, 1, 2, 3):
            short = base + step * PROBE_SPACING
            if not (listed[0] <= short <= listed[-1] and self._pair_listed(side, short)):
                self._latch(
                    CAUSE_CHAIN_EDGE,
                    f"Chain edge reached at {short:g}; probing stops at the last "
                    "listed rung.",
                )
                continue
            if short not in queue:
                queue.append(short)
        if not queue:
            self._latch(
                CAUSE_RUNG_SHORTFALL,
                "Rung shortfall: no listed 20-wide probe pair near the underlying; "
                "the seed keeps the current ladder.",
            )
        return queue[:PROBES_PER_SIDE]

    def _refine_queue(self, side: str, best_short: float) -> List[float]:
        """The 5-point refine: one window step each way around the best probe."""
        queue: List[float] = []
        for delta in (-STRIKE_STEP, STRIKE_STEP):
            short = float(best_short) + delta
            if self._pair_listed(side, short):
                queue.append(short)
            else:
                self._latch(
                    CAUSE_RUNG_SHORTFALL,
                    f"Rung shortfall at {short:g}; the refine skips that window step.",
                )
        return queue

    def _record(self, state: _SideSeed, score: PairScore, counted: bool) -> None:
        if counted:
            self._seed_scored += 1
        state.scores.append(score)
        if state.best is None or self._rank(score) < self._rank(state.best):
            state.best = score

    def _advance_side(self, side: str, state: _SideSeed, acts: Actions) -> str:
        """One unit of work for one side: ``awaiting`` / ``progressed`` / ``finished``."""
        now = self._now()

        if state.phase == "warm":
            state.phase = "commit"
            return "progressed"

        if state.outstanding is not None:
            short, long = state.outstanding
            score = self._score_pair_complete(side, short, long)
            if score is not None:
                self._release_pair(acts, side, short, long, reason=state.phase)
                state.outstanding = None
                self._record(state, score, counted=True)
                state.index += 1
                return "progressed"
            if now - state.leased_at < PENDING_SECONDS:
                return "awaiting"
            # Silent for 3 s: the pair never scores; release and step on.
            self._release_pair(acts, side, short, long, reason=state.phase)
            state.outstanding = None
            state.index += 1
            return "progressed"

        if state.phase in ("probe", "refine"):
            while state.index < len(state.queue):
                short = state.queue[state.index]
                long = self._long_for(side, short)
                score = self._score_pair_complete(side, short, long)
                if score is not None:
                    self._record(state, score, counted=True)
                    state.index += 1
                    return "progressed"
                if self._lease_pair(acts, side, short, long, reason=state.phase):
                    state.outstanding = (short, long)
                    state.leased_at = now
                    if state.phase == "probe":
                        state.probe_pairs += 1
                    return "progressed"
                # Capacity refusal: no probe can score, so the refine tier
                # finishes the seed from the live window's own quotes.
                if state.phase == "probe":
                    anchor = state.best.short if state.best is not None else self._anchors.get(side)
                    if anchor is not None:
                        anchor_score = self._score_at(side, anchor)
                        state.best = self._best_of(
                            [score for score in (state.best, anchor_score) if score is not None]
                        )
                        state.phase = "refine"
                        state.queue = self._refine_queue(side, anchor)
                        state.index = 0
                    else:
                        state.phase = "commit"
                    return "progressed"
                state.index += 1

            if state.phase == "probe":
                if state.best is None:
                    anchor = self._anchors.get(side)
                    self._latch(
                        CAUSE_RUNG_SHORTFALL,
                        "Rung shortfall: no probe pair in the chain quoted; "
                        "the seed keeps the current ladder.",
                    )
                    if anchor is not None:
                        state.best = self._score_at(side, anchor)
                    state.phase = "commit"
                else:
                    state.phase = "refine"
                    state.queue = self._refine_queue(side, state.best.short)
                    state.index = 0
                return "progressed"
            state.phase = "commit"
            return "progressed"

        if state.phase == "commit":
            anchor = None
            if state.best is not None:
                anchor = state.best.short
            if anchor is None:
                anchor = self._anchors.get(side)
            if anchor is None:
                anchor = self._session_anchor.get(side)
            if anchor is None:
                state.phase = "done"
                return "finished"
            self._install_window(acts, side, anchor)
            self._session_anchor[side] = float(anchor)
            self._session_anchor_expiry = self._expiry
            state.phase = "done"
            return "finished"

        state.phase = "done"
        return "finished"

    def _finish_bound(self, acts: Actions, kind: str, value: float) -> None:
        """Stop the sweep at the best-known pair and latch the one bound message."""
        for side, state in self._seed_sides.items():
            if state.outstanding is not None:
                short, long = state.outstanding
                self._release_pair(acts, side, short, long, reason=state.phase)
                state.outstanding = None
        targets: Dict[str, float] = {}
        for side, state in self._seed_sides.items():
            if state.phase == "done":
                continue
            anchor = None
            if state.best is not None:
                anchor = state.best.short
            if anchor is None:
                anchor = self._anchors.get(side)
            if anchor is None:
                anchor = self._session_anchor.get(side)
            if anchor is None:
                continue
            targets[side] = float(anchor)
        self._install_windows(acts, targets)
        self._seed_active = False
        self._seed_bounded = kind
        kept = ", ".join(f"{side} {anchor:g}" for side, anchor in sorted(targets.items()))
        label = f"{value:g} scored pairs" if kind == "pairs" else f"{value:g} s"
        self._latch(
            CAUSE_SEED_BOUND,
            f"Seed bound reached at {label}: keeping {kept or 'no rung'}.",
        )

    def seed_actions(self) -> Actions:
        """Advance the seed by one bounded unit and return the emitted plan."""
        acts = Actions()
        if not self._on:
            return self._out(acts, "off")
        if self._series is None:
            return self._out(acts, "no-0DTE")
        if not self._seed_active:
            return self._out(acts)

        for _ in range(64):
            if not self._seed_active:
                break
            if self._seed_scored >= SCORED_PAIR_LIMIT:
                self._finish_bound(acts, "pairs", float(SCORED_PAIR_LIMIT))
                break
            if self._now() - self._seed_started >= WALL_CLOCK_LIMIT:
                self._finish_bound(acts, "seconds", WALL_CLOCK_LIMIT)
                break
            progressed = False
            for side in SIDES:
                state = self._seed_sides.get(side)
                if state is None or state.phase == "done":
                    continue
                result = self._advance_side(side, state, acts)
                if result == "awaiting":
                    return self._out(acts, "seeding")
                if acts.actions or acts.subscribes or acts.cancels:
                    return self._out(acts, "seeding")
                progressed = result in ("progressed", "finished")
            if all(
                state.phase == "done" for state in self._seed_sides.values()
            ):
                self._seed_active = False
                break
            if not progressed:
                break
        return self._out(acts)

    def seed_state(self) -> SeedState:
        """A snapshot of the ladder: phase, scored count, probes, bound, anchors."""
        if self._seed_active:
            phase = "probing"
            for side in SIDES:
                state = self._seed_sides.get(side)
                if state is not None and state.phase in ("refine", "commit"):
                    phase = "refining"
                    break
            if self._seed_sides and all(
                state.phase == "done" for state in self._seed_sides.values()
            ):
                phase = "done"
        elif self._seed_bounded is not None:
            phase = "bounded"
        elif self._anchors:
            phase = "done"
        else:
            phase = "idle"
        return SeedState(
            active=self._seed_active,
            phase=phase,
            scored=self._seed_scored,
            probes={
                side: state.probe_pairs for side, state in self._seed_sides.items()
            },
            bounded=self._seed_bounded,
            anchors=dict(self._anchors),
            warm={
                side: side in self._session_anchor
                and self._session_anchor.get(side) == self._anchors.get(side)
                for side in SIDES
            },
        )

    # ── Cadence evaluation ───────────────────────────────────────────────────

    def _out(self, acts: Actions, status: Optional[str] = None) -> Actions:
        if status is None:
            if not self._on:
                status = "off"
            elif self._series is None:
                status = "no-0DTE"
            elif self._seed_active:
                status = "seeding"
            elif self._seed_bounded is not None:
                status = "bounded"
            else:
                status = "live"
        acts.status = status
        if self._series is not None:
            acts.rows = self.rows()
        else:
            acts.empty_state = "no-0DTE"
        acts.stale_legs = self.stale_legs()
        acts.messages = self._drain()
        return acts

    def evaluate(self, now: float) -> Actions:
        """One cadence evaluation: seed if needed, match, move, subscribe the spot."""
        self._now_value = float(now)
        acts = Actions()
        if self._walk_frozen:
            # Disconnected: the walk is frozen. Nothing is moved, subscribed or
            # cancelled -- the cells keep their last value, marked STALE.
            return self._out(acts, "stale")
        if not self._on:
            if self._spot_subscribed:
                self._spot_subscribed = False
                acts.spot_cancel = True
            return self._out(acts, "off")
        if self._series is None:
            return self._out(acts, "no-0DTE")
        if self._reconnect_at is not None and not self._reseed_done:
            if any(self.leg_state(leg) == "pending" for leg in self._subscribed):
                # A leg is still silent past the 3 s timeout after the reconnect:
                # re-seed exactly once (the engine's only recovery step).
                self._reseed_done = True
                self.begin_seed(now)
                return self.seed_actions()
        if self._seed_active:
            return self._out(acts, "seeding")
        if self._pending_reseat:
            # A 200 on the anchor pair: one re-seat step, then stop.
            targets = {side: self._pending_reseat.pop(side) for side in list(self._pending_reseat)}
            for side, target in targets.items():
                self._reseat_counts[side] = self._reseat_counts.get(side, 0) + 1
                self._session_anchor[side] = float(target)
                self._session_anchor_expiry = self._expiry
            self._install_windows(acts, targets)
            if not self._spot_subscribed:
                self._spot_subscribed = True
                acts.spot_subscribe = True
            return self._out(acts)
        if not self._anchors:
            self.begin_seed(now)
            return self.seed_actions()
        if self._seed_bounded is not None:
            matched = [self._anchor_matched(side) for side in self._anchors]
            if not all(matched):
                # Re-arm only here, at the next cadence evaluation.
                self.begin_seed(now)
                return self.seed_actions()
        else:
            targets: Dict[str, float] = {}
            for side, anchor in list(self._anchors.items()):
                if self._anchor_matched(side):
                    continue
                best = self._best_neighbour(side, anchor)
                if best is not None and best.short != anchor:
                    targets[side] = best.short
            if targets:
                self._install_windows(acts, targets)
                for side, anchor in targets.items():
                    self._session_anchor[side] = float(anchor)
                    self._session_anchor_expiry = self._expiry
        if not self._spot_subscribed:
            self._spot_subscribed = True
            acts.spot_subscribe = True
        return self._out(acts)

    # ── Part 2: the window walk (AC-D65.4) ───────────────────────────────────

    def window_step(self, target_anchor) -> Actions:
        """Emit at most one 5-point window step per side toward ``target_anchor``.

        ``target_anchor`` is the anchor the caller wants: a single strike applied
        to both sides, or a ``{"CCS": strike, "PCS": strike}`` mapping when the
        two ladders are headed in different strike directions (which the two
        sides' quote profiles usually are).

        The step is *one rung*, never a jump, and it is emitted only when
        ``AC-D65.4`` warrants it:

        * the live anchor pair is not matched (a matched pair never moves);
        * the rung one step toward the requested anchor carries a credit mid in
          the AC-D65.4 direction -- **toward the money** (a higher credit mid)
          when all three of the live pair's credit bases sit below the Target,
          **away from the money** (a lower credit mid) when all three sit above;
        * that rung improves ``d`` by **more than** ``h``. Equal-``d`` neighbours
          therefore resolve to staying -- the total order's credit-mid tie-break
          decides which pair is better, and the strict ``> h`` rule is what makes
          a two-rung oscillation impossible;
        * the rung is a listed 20-wide pair. A step whose required rung is not
          listed latches exactly one chain-edge message naming the best reachable
          value and moves nothing.

        Every emitted step cancels the legs leaving the window before it
        subscribes the legs arriving, and a leg present in both the old and the
        new window is neither cancelled nor subscribed -- it keeps its reqId.
        """
        acts = Actions()
        if self._walk_frozen:
            return self._out(acts, "stale")
        if not self._on:
            return self._out(acts, "off")
        if self._series is None:
            return self._out(acts, "no-0DTE")
        if self._seed_active:
            return self._out(acts, "seeding")
        targets = self._requested_targets(target_anchor)
        steps: Dict[str, float] = {}
        for side in SIDES:
            live = self._anchors.get(side)
            wanted = targets.get(side)
            if live is None or wanted is None:
                continue
            candidate = self._walk_candidate(side, live, wanted)
            if candidate is not None:
                steps[side] = float(candidate)
        if steps and self._install_windows(acts, steps):
            for side, anchor in steps.items():
                self._session_anchor[side] = float(anchor)
                self._session_anchor_expiry = self._expiry
        return self._out(acts)

    @staticmethod
    def _requested_targets(target_anchor) -> Dict[str, float]:
        """Normalise ``window_step``'s argument to one anchor per side."""
        if isinstance(target_anchor, dict):
            out: Dict[str, float] = {}
            for key, value in target_anchor.items():
                name = str(key).strip().upper()
                if name in SIDES:
                    out[name] = float(value)
            return out
        return {side: float(target_anchor) for side in SIDES}

    def _walk_candidate(
        self, side: str, live: float, wanted: float
    ) -> Optional[float]:
        """The one-rung anchor a step may move to, or ``None`` when a stop holds."""
        if math.isclose(float(wanted), float(live), abs_tol=1e-9):
            return None
        if self._anchor_matched(side):
            return None  # stop: the pair is matched, a matched pair never moves
        current = self._score_at(side, live)
        if current is None:
            return None  # the live anchor pair is not quoting
        step = STRIKE_STEP if float(wanted) > float(live) else -STRIKE_STEP
        candidate = float(live) + step
        if not self._pair_listed(side, candidate):
            self._latch(
                CAUSE_WALK_CHAIN_EDGE,
                f"Chain edge: the window step from {float(live):g} needs the rung "
                f"{candidate:g}, which is not a listed 20-wide pair; the best "
                f"reachable value is {float(live):g}.",
            )
            return None  # stop: the improving neighbour is not a listed pair
        nxt = self._score_at(side, candidate)
        if nxt is None:
            return None  # the arriving pair has not quoted yet
        bases = (current.credit_bid, current.credit_ask, current.credit_mid)
        below = all(value < self._target for value in bases)
        above = all(value > self._target for value in bases)
        if below and nxt.credit_mid <= current.credit_mid:
            return None  # AC-D65.4: toward the money (a higher credit mid)
        if above and nxt.credit_mid >= current.credit_mid:
            return None  # AC-D65.4: away from the money (a lower credit mid)
        if nxt.distance >= current.distance - self.band:
            return None  # stop: no neighbour improves d by more than h
        return candidate

    # ── Part 2: greek sources (AC-D65.5) ─────────────────────────────────────

    def on_greek(self, leg: LegKey, tick_type: int, delta, gamma) -> None:
        """Store one leg's greek for one tick type (13 model, 12 last, 10/11 bid/ask).

        A tick with an absent or non-finite side is not recorded, so a half
        greek never reaches a row.
        """
        try:
            key = int(tick_type)
        except (TypeError, ValueError):
            return
        values = self._greeks.setdefault(leg, {})
        screened = self._screened_greek(delta, gamma)
        if screened is None:
            values.pop(key, None)
            return
        values[key] = screened

    @staticmethod
    def _screened_greek(delta, gamma) -> Optional[Tuple[float, float]]:
        out: List[float] = []
        for value in (delta, gamma):
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
            if not math.isfinite(number):
                return None
            out.append(number)
        return out[0], out[1]

    @staticmethod
    def _tier_value(
        values: Dict[int, Tuple[float, float]], source: str
    ) -> Optional[Tuple[float, float]]:
        if source == SOURCE_MODEL:
            return values.get(GREEK_MODEL)
        if source == SOURCE_LAST:
            return values.get(GREEK_LAST)
        bid = values.get(GREEK_BID)
        ask = values.get(GREEK_ASK)
        if bid is None or ask is None:
            return None
        return (bid[0] + ask[0]) / 2.0, (bid[1] + ask[1]) / 2.0

    def _leg_source(self, values: Dict[int, Tuple[float, float]]) -> Optional[str]:
        for source in (SOURCE_MODEL, SOURCE_LAST, SOURCE_BIDASK):
            if self._tier_value(values, source) is not None:
                return source
        return None

    def row_greeks(self, side: str, short: float, long: float) -> Optional[Greeks]:
        """One row's net greeks and source, or ``None`` when no source covers both legs.

        The three sources are tried in order -- model (13), last (12), then the
        mean of bid (10) and ask (11) -- and the first one *both* legs carry wins,
        so the two legs are never mixed. A pair whose legs each resolve to a
        different source shows no value and latches exactly one message.
        """
        right = _right(side)
        short_values = self._greeks.get(LegKey(right=right, strike=float(short)), {})
        long_values = self._greeks.get(LegKey(right=right, strike=float(long)), {})
        for source in (SOURCE_MODEL, SOURCE_LAST, SOURCE_BIDASK):
            short_tick = self._tier_value(short_values, source)
            long_tick = self._tier_value(long_values, source)
            if short_tick is None or long_tick is None:
                continue
            delta, gamma = net_greeks(
                short_tick[0], long_tick[0], short_tick[1], long_tick[1]
            )
            return Greeks(delta=delta, gamma=gamma, source=source)
        short_source = self._leg_source(short_values)
        long_source = self._leg_source(long_values)
        if (
            short_source is not None
            and long_source is not None
            and short_source != long_source
        ):
            self._latch(
                f"{CAUSE_GREEK_MIXED}:{side}:{float(short):g}",
                f"{side} {float(short):g}/{float(long):g}: the legs carry different "
                f"greek sources ({short_source} and {long_source}); no Delta/Gamma "
                "value is shown.",
            )
        return None

    # ── Part 2: the connection lifecycle (AC-D65.14) ─────────────────────────

    def on_disconnected(self) -> None:
        """Freeze the walk and mark every cell STALE; nothing is cancelled.

        The engine holds no values of its own making -- each cell keeps its last
        received value and is flagged STALE. It also adds no reconnect mechanism:
        it waits for :meth:`on_reconnected` from the connection owner.
        """
        self._walk_frozen = True
        self._disconnected_at = self._now()
        self._stale.update(self._subscribed)
        self._stale.update(self._quotes)
        self._pending_messages.append(
            "Connection lost: every cell keeps its last value marked STALE; the "
            "window walk is frozen and nothing is cancelled."
        )

    def on_reconnected(self) -> None:
        """Resume from the SAME anchor with no re-seed while the legs recover."""
        self._walk_frozen = False
        self._reconnect_at = self._now()
        self._reseed_done = False
        for leg in self._subscribed:
            self._subscribed_at[leg] = self._reconnect_at
        self._pending_messages.append(
            "Connection restored: the ladder resumes from the same anchor; no "
            "re-seed while the legs recover."
        )

    def rebind_leg(self, leg: LegKey, new_req_id: int) -> None:
        """Record the reqId a re-subscribed leg now holds; its cell is live again."""
        self._req_ids[leg] = int(new_req_id)
        self._stale.discard(leg)
        self._stale_after.pop(leg, None)
        self._no_value.discard(leg)

    def req_id(self, leg: LegKey) -> Optional[int]:
        """The reqId bound to ``leg``'s live line, or ``None``."""
        return self._req_ids.get(leg)

    @property
    def walk_frozen(self) -> bool:
        """True while a disconnect holds the walk frozen."""
        return self._walk_frozen

    def leg_stale(self, leg: LegKey) -> bool:
        """True when ``leg``'s cell holds its last value marked STALE."""
        if leg in self._stale:
            return True
        deadline = self._stale_after.get(leg)
        return deadline is not None and self._now() >= deadline

    def stale_legs(self) -> Set[LegKey]:
        """Every leg whose cell is currently STALE."""
        return {
            leg
            for leg in set(self._stale) | set(self._stale_after)
            if self.leg_stale(leg)
        }

    # ── Part 2: the per-line error classes (AC-D65.14) ───────────────────────

    def on_leg_error(self, leg: LegKey, code: int) -> None:
        """Apply one TWS per-line error class to the pair that holds ``leg``.

        Each class keeps its own state and latches exactly one message:

        * ``200`` on a non-anchor pair -- the pair is dropped for the session
          (its row shows ``n/a``) and the window is **not** re-seated;
        * ``200`` on the anchor pair -- exactly one toward-the-money re-seat,
          applied by the next :meth:`evaluate`; a second one stops with a message;
        * ``10197`` and ``354`` -- the pair shows no value and nothing re-seats;
        * ``162`` -- the line is kept, its values go STALE after
          :data:`PENDING_SECONDS`, nothing is cancelled;
        * any other code -- the pair shows no value and nothing re-seats.
        """
        side = self._side_for_leg(leg)
        pair = self._pair_for_leg(side, leg) if side is not None else None
        if pair is None:
            self._pending_messages.append(
                f"TWS line error {code} for {leg.right} {float(leg.strike):g}: no "
                "live pair holds that leg; no value is shown."
            )
            return
        try:
            value = int(code)
        except (TypeError, ValueError):
            value = -1
        short, long = pair
        if value == 200:
            anchor = self._anchors.get(side)
            if anchor is not None and math.isclose(
                float(short), float(anchor), abs_tol=1e-9
            ):
                self._queue_reseat(side, pair)
            else:
                self._drop_pair(side, pair)
            return
        if value == 162:
            self._hold_pair(side, pair)
            return
        if value == 10197:
            self._blank_pair(
                side,
                pair,
                f"{CAUSE_LINE_10197}:{side}:{short:g}",
                f"TWS error 10197 on {side} {short:g}/{long:g}: the pair shows no "
                "value; the window is not re-seated.",
            )
            return
        if value == 354:
            self._blank_pair(
                side,
                pair,
                f"{CAUSE_LINE_354}:{side}:{short:g}",
                f"TWS error 354 on {side} {short:g}/{long:g}: the pair shows no "
                "value; the window is not re-seated.",
            )
            return
        self._blank_pair(
            side,
            pair,
            f"{CAUSE_LINE_OTHER}:{side}:{short:g}:{value}",
            f"TWS error {value} on {side} {short:g}/{long:g}: unclassified; the "
            "pair shows no value and the window is not re-seated.",
        )

    @staticmethod
    def _side_for_leg(leg: LegKey) -> Optional[str]:
        if leg.right == "C":
            return SIDE_CCS
        if leg.right == "P":
            return SIDE_PCS
        return None

    def _pair_for_leg(
        self, side: Optional[str], leg: LegKey
    ) -> Optional[Tuple[float, float]]:
        """The live ladder pair that holds ``leg``, or ``None``."""
        if side is None:
            return None
        anchor = self._anchors.get(side)
        if anchor is None:
            return None
        strike = float(leg.strike)
        for short, long in ladder_pairs(anchor, side):
            if math.isclose(strike, float(short), abs_tol=1e-9) or math.isclose(
                strike, float(long), abs_tol=1e-9
            ):
                return float(short), float(long)
        return None

    def _drop_pair(self, side: str, pair: Tuple[float, float]) -> None:
        """Drop a pair for the session: the line is gone at TWS, so nothing is sent."""
        short, long = pair
        right = _right(side)
        for strike in (short, long):
            dead = LegKey(right=right, strike=float(strike))
            self._dropped.add(dead)
            self._subscribed.discard(dead)
            self._subscribed_at.pop(dead, None)
            self._leased.discard(dead)
            self._req_ids.pop(dead, None)
            self._stale.discard(dead)
            self._stale_after.pop(dead, None)
        self._latch(
            f"{CAUSE_LINE_200_PAIR}:{side}:{float(short):g}",
            f"TWS error 200 on {side} {float(short):g}/{float(long):g}: the pair is "
            "dropped for this session and its row shows n/a; the window is not "
            "re-seated.",
        )

    def _blank_pair(
        self, side: str, pair: Tuple[float, float], cause: str, message: str
    ) -> None:
        """Show no value for a pair, leaving its window seat alone."""
        short, long = pair
        right = _right(side)
        for strike in (short, long):
            self._no_value.add(LegKey(right=right, strike=float(strike)))
        self._latch(cause, message)

    def _hold_pair(self, side: str, pair: Tuple[float, float]) -> None:
        """A ``162`` is transient: keep the line, go STALE after the timeout."""
        short, long = pair
        right = _right(side)
        deadline = self._now() + PENDING_SECONDS
        for strike in (short, long):
            self._stale_after[LegKey(right=right, strike=float(strike))] = deadline
        self._latch(
            f"{CAUSE_LINE_162}:{side}:{float(short):g}",
            f"TWS error 162 on {side} {float(short):g}/{float(long):g}: the line is "
            f"kept and its values go STALE after {PENDING_SECONDS:g} s; nothing is "
            "cancelled.",
        )

    def _queue_reseat(self, side: str, pair: Tuple[float, float]) -> None:
        """Queue the single toward-the-money re-seat a ``200`` on the anchor earns."""
        short, long = pair
        if self._reseat_counts.get(side, 0) >= 1:
            self._latch(
                f"{CAUSE_LINE_200_STOP}:{side}",
                f"TWS error 200 on the {side} anchor pair {float(short):g}/"
                f"{float(long):g} again: the single re-seat is spent; the ladder "
                "stops here.",
            )
            return
        target = self._toward_money(side)
        if target is None:
            self._latch(
                f"{CAUSE_LINE_200_ANCHOR}:{side}",
                f"TWS error 200 on the {side} anchor pair {float(short):g}/"
                f"{float(long):g}: no neighbouring 20-wide rung can carry the "
                "re-seat; the ladder stops here.",
            )
            return
        self._pending_reseat[side] = float(target)
        self._latch(
            f"{CAUSE_LINE_200_ANCHOR}:{side}",
            f"TWS error 200 on the {side} anchor pair {float(short):g}/"
            f"{float(long):g}: re-seating one step toward the money at {target:g}.",
        )

    def _toward_money(self, side: str) -> Optional[float]:
        """The neighbouring rung with the larger credit mid (the money direction)."""
        live = self._anchors.get(side)
        if live is None:
            return None
        scored: List[PairScore] = []
        for delta in (-STRIKE_STEP, STRIKE_STEP):
            short = float(live) + delta
            if not self._pair_listed(side, short):
                continue
            score = self._score_at(side, short)
            if score is not None:
                scored.append(score)
        if scored:
            spot = self._spot

            def key(score: PairScore):
                spot_key = 0.0 if spot is None else _q(abs(score.short - spot))
                return (-_q(score.credit_mid), spot_key, -score.short)

            return min(scored, key=key).short
        if self._spot is not None and not math.isclose(
            self._spot, float(live), abs_tol=1e-9
        ):
            step = STRIKE_STEP if self._spot > float(live) else -STRIKE_STEP
            candidate = float(live) + step
            return candidate if self._pair_listed(side, candidate) else None
        return None

    # ── Part 2: read-only state ──────────────────────────────────────────────

    def pair_dropped(self, side: str, short: float) -> bool:
        """True when the pair at ``short`` was dropped for the session by a ``200``."""
        right = _right(side)
        return LegKey(right=right, strike=float(short)) in self._dropped

    def reseat_count(self, side: str) -> int:
        """How many anchor re-seats a ``200`` on this side's anchor has caused."""
        return self._reseat_counts.get(side, 0)

    def take_messages(self) -> List[str]:
        """Drain the latched messages without emitting an action plan."""
        return self._drain()
