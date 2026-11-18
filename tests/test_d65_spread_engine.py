"""P23-T7: pure tests for the option-spread seeding engine (D65, part 1).

These tests are Qt-free and ibapi-free by construction: the module under test
imports neither, and the isolation check below proves it in a fresh
interpreter. Every clock is injected -- the suite never relies on real elapsed
time and never uses a real wait.

Fixtures are hand-computed on purpose. ``credit_mid = short_mid - long_mid``
and ``credit_bid = short.bid - long.ask`` / ``credit_ask = short.ask -
long.bid``, so a 20-wide CCS pair's three bases are chosen here by picking the
two legs' quotes.
"""

import ast
import inspect
import math
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

import services.option_spread_engine as engine_module
from services.option_ladder import LegKey, match_band
from services.option_spread_engine import (
    MAX_OPTION_LINES,
    PENDING_SECONDS,
    PROBE_SPACING,
    PROBES_PER_SIDE,
    SCORED_PAIR_LIMIT,
    SpreadEngine,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "services" / "option_spread_engine.py"
TEST_PATH = Path(__file__).resolve()

# 7300..7360 in 5-point steps: the narrow chain whose probe window is three
# pairs wide (7310, 7330, 7350) and whose refine ring is 7325/7335.
CHAIN = [7300 + 5 * index for index in range(13)]


def make_series(c_strikes=None, p_strikes=None, expiry="20261117"):
    calls = list(CHAIN if c_strikes is None else c_strikes)
    puts = list(CHAIN if p_strikes is None else p_strikes)
    return SimpleNamespace(
        trading_class="SPXW",
        exchange="SMART",
        expiry=expiry,
        con_id=1,
        strikes_by_right={"C": calls, "P": puts},
    )


class Clock:
    """The injected clock: the engine reads it, the test advances it."""

    def __init__(self, value=1000.0):
        self.value = float(value)

    def __call__(self):
        return self.value

    def advance(self, delta):
        self.value += float(delta)


def leg(right, strike):
    return LegKey(right=right, strike=float(strike))


def side_right(side):
    return "C" if side == "CCS" else "P"


def quotes_for(side, table):
    right = side_right(side)
    return {leg(right, strike): value for strike, value in table.items()}


# A put credit spread is the call spread mirrored around the anchor strike: the
# put's long leg sits 20 *below* its short, so the same credit needs the price
# profile mirrored. 14660 = 2 * 7330 keeps every mirrored strike on the chain.
MIRROR = 2 * 7330


def mirror_table(table):
    return {MIRROR - strike: value for strike, value in table.items()}


def both_sides(table):
    plan = {}
    plan.update(quotes_for("CCS", table))
    plan.update(quotes_for("PCS", mirror_table(table)))
    return plan


def pending_from_state(engine):
    """The pending-leg fact, read through the live pool it was derived from."""
    return {item for item in engine._subscribed if engine.leg_state(item) == "pending"}


def feed(engine, plan):
    for key, value in plan.items():
        if len(value) == 4:
            engine.on_quote(key, *value)
        else:
            engine.on_quote(key, value[0], value[1], True, True)


def drive(engine, plan, clock, dt=0.1, max_steps=800):
    """Run the seed to completion, feeding quotes for newly subscribed legs."""
    batches = []
    for _ in range(max_steps):
        acts = engine.seed_actions()
        batches.append(acts)
        feed(engine, {item: plan[item] for item in acts.subscribes if item in plan})
        clock.advance(dt)
        if not engine.seed_state().active:
            break
    return batches


def actions(batches):
    return [action for batch in batches for action in batch.actions]


def messages(batches):
    return [message for batch in batches for message in batch.messages]


def seed_engine(table, clock, target=1.00, spot=7330.0):
    engine = SpreadEngine(clock=clock, target=target)
    engine.toggle_on()
    engine.on_chain(make_series())
    if spot is not None:
        engine.on_spot(spot)
    engine.begin_seed(clock())
    batches = drive(engine, both_sides(table), clock)
    return engine, batches


# The AC1 fixture: probe 7310 is far, 7330 is the strict best (d = 0), 7350 is
# far, and the 7325/7335 refine ring is worse than 7330.
AC1_TABLE = {
    7310: (6.65, 6.70),
    7330: (5.00, 5.05),
    7350: (3.95, 4.00),
    7370: (0.00, 0.00),
    7325: (2.95, 3.05),
    7345: (2.45, 2.55),
    7335: (3.95, 4.05),
    7355: (2.45, 2.55),
}


# ── P23-T7-AC1: the seed ladder ──────────────────────────────────────────────


def test_P23_T7_AC1_seed_ladder_tiers_and_one_final_rung():
    clock = Clock()
    engine, batches = seed_engine(AC1_TABLE, clock)
    state = engine.seed_state()
    assert state.active is False
    assert engine.anchor("CCS") == 7330
    assert engine.anchor("PCS") == 7330
    assert state.probes["CCS"] <= PROBES_PER_SIDE
    assert state.probes["PCS"] <= PROBES_PER_SIDE

    # ≤6 coarse probe pairs per side, 20 points apart, each leased and released.
    cold = actions(batches)
    probe_leases = [
        action for action in cold if action.kind == "lease" and action.reason == "probe"
    ]
    probe_shorts = {}
    for action in probe_leases:
        probe_shorts.setdefault(action.side, set()).add(action.pair[0])
    for side, shorts in probe_shorts.items():
        assert len(shorts) <= PROBES_PER_SIDE
        ordered = sorted(shorts)
        assert all(
            math.isclose(right - left, PROBE_SPACING)
            for left, right in zip(ordered, ordered[1:])
        )
    probe_releases = {
        (action.side, action.pair)
        for action in cold
        if action.kind == "release" and action.reason in ("probe", "refine")
    }
    for action in probe_leases:
        assert (action.side, action.pair) in probe_releases

    # Tier 1: the session anchor is reused with no probe lease at all.
    engine.begin_seed(clock())
    warm = []
    for _ in range(10):
        warm.append(engine.seed_actions())
        if not engine.seed_state().active:
            break
    warm_actions = actions(warm)
    assert [action for action in warm_actions if action.kind == "lease"] == []
    assert engine.anchor("CCS") == 7330
    assert engine.anchor("PCS") == 7330

    # Spot absent and spot refused reach the same final rung as the spot path.
    for spot in (None, float("nan"), -1.0):
        other_clock = Clock()
        other, _ = seed_engine(AC1_TABLE, other_clock, spot=spot)
        assert other.anchor("CCS") == 7330
        assert other.anchor("PCS") == 7330

    # A probe refused for capacity still finishes through the refine tier.
    refused_clock = Clock()
    refused, refused_batches = seed_engine(AC1_TABLE, refused_clock)
    refused.set_target(1.60)
    # The first probe pair's own quote is gone, so the probe needs a new lease --
    # and the live window holds all 16 lines.
    for right in ("C", "P"):
        refused.on_quote(leg(right, 7310), -1.0, 6.70, True, True)
    refused.begin_seed(refused_clock())
    refused_batches = drive(refused, both_sides(AC1_TABLE), refused_clock)
    assert refused.seed_state().active is False
    assert refused.anchor("CCS") == 7335
    assert any("Probe refused for capacity" in message for message in messages(refused_batches))


# ── P23-T7-AC2: the sweep bound ──────────────────────────────────────────────

WIDE_CHAIN = [7200 + 5 * index for index in range(61)]  # 7200..7500

# Every leg at 0.00: every pair scores (credit 0, mid 0) and none matches T=1.00.
# Dense on purpose, so the mirrored put legs quote too and no step waits.
WIDE_TABLE = {strike: (0.0, 0.0) for strike in range(7240, 7470, 5)}


def test_P23_T7_AC2_sweep_bound_is_one_message_and_rearms_at_cadence():
    clock = Clock()
    engine = SpreadEngine(clock=clock, target=1.00)
    engine.toggle_on()
    engine.on_chain(make_series(WIDE_CHAIN, WIDE_CHAIN))
    engine.on_spot(7350.0)
    engine.begin_seed(clock())
    batches = drive(engine, both_sides(WIDE_TABLE), clock)
    state = engine.seed_state()
    assert state.active is False
    assert state.bounded == "pairs"
    assert state.scored == SCORED_PAIR_LIMIT
    bound_messages = [message for message in messages(batches) if "Seed bound" in message]
    assert len(bound_messages) == 1
    assert "12" in bound_messages[0]
    kept = dict(state.anchors)
    assert kept  # the ladder stays on the best-known pair

    # No work between the bound and the next cadence evaluation.
    idle = engine.seed_actions()
    assert idle.actions == []
    assert idle.subscribes == []
    assert engine.seed_state().bounded == "pairs"

    # The next cadence evaluation re-arms the seed (and clears the bound latch).
    engine.evaluate(clock())
    assert engine.seed_state().bounded is None

    # The wall-clock bound: the injected clock crosses 10 s, never a real wait.
    slow_clock = Clock()
    slow = SpreadEngine(clock=slow_clock, target=1.00)
    slow.toggle_on()
    slow.on_chain(make_series(WIDE_CHAIN, WIDE_CHAIN))
    slow.on_spot(7350.0)
    slow.begin_seed(slow_clock())
    slow_batches = []
    for _ in range(400):
        batch = slow.seed_actions()
        slow_batches.append(batch)
        feed(slow, {item: WIDE_TABLE[item] for item in batch.subscribes if item in WIDE_TABLE})
        slow_clock.advance(1.0)
        if not slow.seed_state().active:
            break
    slow_state = slow.seed_state()
    assert slow_state.bounded == "seconds"
    assert slow_state.scored < SCORED_PAIR_LIMIT
    slow_bound = [message for message in messages(slow_batches) if "Seed bound" in message]
    assert len(slow_bound) == 1
    assert "10" in slow_bound[0]

    # The module never waits: the bound is measured on the injected clock only.
    source = inspect.getsource(engine_module)
    assert "time.sleep" not in source
    assert ".sleep(" not in source
    assert "sleep(" not in source.replace("time.sleep", "")


# ── P23-T7-AC3: pending legs and one-sided pairs ─────────────────────────────


def test_P23_T7_AC3_pending_leg_three_seconds_and_both_legs_required():
    clock = Clock()
    engine = SpreadEngine(clock=clock, target=1.00)
    engine.toggle_on()
    engine.on_chain(make_series())
    engine.on_spot(7330.0)
    engine.begin_seed(clock())
    first = engine.seed_actions()
    assert first.subscribes, "the first probe must lease and subscribe its pair"
    short_leg, long_leg = first.subscribes
    # Only the short leg ticks.
    engine.on_quote(short_leg, 6.65, 6.70, True, True)

    clock.advance(PENDING_SECONDS - 0.1)
    assert engine.leg_state(long_leg) == "awaiting"
    assert engine._score_pair_complete("CCS", 7310, 7330) is None
    assert pending_from_state(engine) == set()

    clock.advance(0.1)  # exactly 3.0 s since the subscription
    assert engine.leg_state(long_leg) == "pending"
    assert pending_from_state(engine) == {long_leg}
    assert engine._score_pair_complete("CCS", 7310, 7330) is None
    assert engine.seed_state().scored == 0

    # Both legs quoting makes the pair scoreable (and only then).
    engine.on_quote(long_leg, 5.00, 5.05, True, True)
    assert engine.leg_state(long_leg) == "quoted"
    assert engine._score_pair_complete("CCS", 7310, 7330) is not None

    # A received zero bid is a live price that still scores.
    zero_clock = Clock()
    zero = SpreadEngine(clock=zero_clock, target=1.00)
    zero.toggle_on()
    zero.on_chain(make_series())
    zero.on_spot(7330.0)
    zero.on_quote(leg("C", 7330), 0.0, 0.60, True, True)
    zero.on_quote(leg("C", 7350), 0.0, 0.00, True, True)
    score = zero._score_pair_complete("CCS", 7330, 7350)
    assert score is not None
    assert score.credit_bid == 0.0
    assert zero.leg_state(leg("C", 7330)) == "quoted"

    # One side absent: the pair never scores, even with a live other side.
    zero.on_quote(leg("C", 7350), 0.0, 0.00, True, False)
    assert zero._score_pair_complete("CCS", 7330, 7350) is None


# ── P23-T7-AC4: sentinels never reach the metric ─────────────────────────────


def test_P23_T7_AC4_sentinels_absent_and_good_to_sentinel_transition(monkeypatch):
    sentinels = [
        -1.0,
        1.7976931348623157e308,
        float("nan"),
        float("inf"),
        float("-inf"),
    ]
    recorded = []
    real_distance = engine_module.distance

    def spy(target, credit_bid, credit_ask, credit_mid):
        recorded.append((target, credit_bid, credit_ask, credit_mid))
        return real_distance(target, credit_bid, credit_ask, credit_mid)

    monkeypatch.setattr(engine_module, "distance", spy)

    engine = SpreadEngine(clock=Clock(), target=1.00)
    engine.toggle_on()
    engine.on_chain(make_series())
    for sentinel in sentinels:
        engine.on_quote(leg("C", 7330), sentinel, 5.05, True, True)
        engine.on_quote(leg("C", 7350), 3.95, 4.00, True, True)
        # Both wrapper facts -- eligibility and score -- are one internal read
        # now, so the pair is asserted unscoreable twice on purpose.
        assert engine._score_pair_complete("CCS", 7330, 7350) is None
        assert engine._score_pair_complete("CCS", 7330, 7350) is None
        assert engine.leg_state(leg("C", 7330)) == "idle"
    # A no-tick zero (received flags false) is absent too.
    engine.on_quote(leg("C", 7330), 0.0, 0.0, False, False)
    assert engine._score_pair_complete("CCS", 7330, 7350) is None

    # No sentinel reached the distance helper.
    for call in recorded:
        for value in call:
            assert math.isfinite(value)
            assert value != -1.0
            assert value < 1.7976931348623157e308

    # Good quotes seed, then one leg turns sentinel: the cell empties and the
    # pair is ineligible on the next evaluation.
    clock = Clock()
    live, _ = seed_engine(AC1_TABLE, clock)
    assert live.anchor("CCS") == 7330
    before = live.rows()["CCS"][2]
    assert before.short == 7330
    assert before.display_ask is not None and before.display_bid is not None
    assert before.matched is True
    assert live._score_pair_complete("CCS", 7330, 7350) is not None

    live.on_quote(leg("C", 7330), -1.0, 5.05, True, True)
    acts = live.evaluate(clock())
    after_rows = live.rows()["CCS"]
    stale = [row for row in after_rows if row.short == 7330][0]
    assert stale.display_ask is None
    assert stale.display_bid is None
    assert stale.matched is False
    assert live._score_pair_complete("CCS", 7330, 7350) is None
    assert acts.status in ("live", "seeding", "bounded")


# ── P23-T7-AC5: the credit metric, tie-breaks, and the seed ladder ───────────


def _tie_refine_filler(variant):
    # Refine legs quoted far from every Target used here, so the tie stands.
    if variant == "7305":
        return {7305: (0.10, 0.15), 7325: (0.00, 0.00),
                7315: (0.20, 0.25), 7335: (0.00, 0.00)}
    return {7325: (0.10, 0.15), 7345: (0.00, 0.00),
            7335: (0.20, 0.25), 7355: (0.00, 0.00)}


def test_P23_T7_AC5_metric_on_credit_bases_all_three_tie_breaks(monkeypatch):
    recorded = []
    real_distance = engine_module.distance

    def spy(target, credit_bid, credit_ask, credit_mid):
        recorded.append((target, credit_bid, credit_ask, credit_mid))
        return real_distance(target, credit_bid, credit_ask, credit_mid)

    monkeypatch.setattr(engine_module, "distance", spy)

    # Each of the three credit bases can be the one touching the Target.
    base_cases = {
        "mid": (0.90, 1.10),
        "ask": (0.80, 1.00),
        "bid": (1.00, 1.20),
    }
    for name, headline in base_cases.items():
        table = {
            7310: (0.00, 0.00),
            7330: headline,
            7350: (0.00, 0.00),
            7370: (0.00, 0.00),
            7325: (0.10, 0.15),
            7345: (0.00, 0.00),
            7335: (0.20, 0.25),
            7355: (0.00, 0.00),
        }
        clock = Clock()
        engine, _ = seed_engine(table, clock)
        assert engine.anchor("CCS") == 7330, name
        score = engine._score_pair_complete("CCS", 7330, 7350)
        assert score is not None and score.distance == 0.0
        if name == "mid":
            assert score.credit_mid == pytest.approx(1.00)
            assert score.credit_bid == pytest.approx(0.90)
            assert score.credit_ask == pytest.approx(1.10)
        elif name == "ask":
            assert score.credit_ask == pytest.approx(1.00)
            assert abs(score.credit_bid - 1.00) > 0
            assert abs(score.credit_mid - 1.00) > 0
        else:
            assert score.credit_bid == pytest.approx(1.00)
            assert abs(score.credit_ask - 1.00) > 0
            assert abs(score.credit_mid - 1.00) > 0

    # Tie 1: equal d, smaller |credit_mid - T| wins.
    tie1 = {
        7310: (6.05, 6.40),
        7330: (5.00, 5.05),
        7350: (3.95, 4.00),
        7370: (0.00, 0.00),
        **_tie_refine_filler(None),
    }
    clock = Clock()
    engine1, batches1 = seed_engine(tie1, clock)
    low = engine1._score_pair_complete("CCS", 7310, 7330)
    better = engine1._score_pair_complete("CCS", 7330, 7350)
    assert low is not None and better is not None
    assert low.distance == 0.0 and better.distance == 0.0
    assert abs(better.credit_mid - 1.00) < abs(low.credit_mid - 1.00)
    assert engine1.anchor("CCS") == 7330
    probed = {
        action.pair[0]
        for action in actions(batches1)
        if action.side == "CCS" and action.kind == "lease" and action.reason == "probe"
    }
    assert {7310, 7330} <= probed  # the tie was reached through the seed ladder

    # Tie 2: equal d and equal |credit_mid - T| -> credit_mid >= T wins.
    tie2 = {
        7310: (6.15, 6.30),
        7330: (5.00, 5.05),
        7350: (4.15, 4.30),
        7370: (0.00, 0.00),
        **_tie_refine_filler("7305"),
    }
    clock = Clock()
    engine2, batches2 = seed_engine(tie2, clock)
    high = engine2._score_pair_complete("CCS", 7310, 7330)
    below = engine2._score_pair_complete("CCS", 7330, 7350)
    assert high is not None and below is not None
    assert high.distance == pytest.approx(0.10)
    assert below.distance == pytest.approx(0.10)
    assert abs(high.credit_mid - 1.00) == pytest.approx(abs(below.credit_mid - 1.00))
    assert high.credit_mid >= 1.00 > below.credit_mid
    assert engine2.anchor("CCS") == 7310
    probed2 = {
        action.pair[0]
        for action in actions(batches2)
        if action.side == "CCS" and action.kind == "lease" and action.reason == "probe"
    }
    assert {7310, 7330} <= probed2

    # Tie 3a: equal on every metric -> the short strike nearer spot wins.
    tie3 = {
        7310: (6.15, 6.30),
        7330: (5.00, 5.05),
        7350: (3.75, 3.90),
        7370: (0.00, 0.00),
        **_tie_refine_filler(None),
    }
    clock = Clock()
    near, near_batches = seed_engine(tie3, clock, spot=7328.0)
    left = near._score_pair_complete("CCS", 7310, 7330)
    right = near._score_pair_complete("CCS", 7330, 7350)
    assert left is not None and right is not None
    assert left.distance == pytest.approx(0.10) == pytest.approx(right.distance)
    assert left.credit_mid == pytest.approx(right.credit_mid)
    assert near._spot == 7328.0
    assert near.anchor("CCS") == 7330
    near_probes = {
        action.pair[0]
        for action in actions(near_batches)
        if action.side == "CCS" and action.kind == "lease" and action.reason == "probe"
    }
    assert {7310, 7330} <= near_probes

    # Tie 3b: no price exists -> the lower short strike wins.
    clock = Clock()
    no_spot, _ = seed_engine(tie3, clock, spot=None)
    assert no_spot._spot is None
    assert no_spot.anchor("CCS") == 7310

    # The displayed negative values never enter the metric: the recorded
    # distance arguments for the anchor pair are its credit bases, all positive.
    assert any(
        math.isclose(target, 1.00)
        and math.isclose(credit_bid, 1.00, abs_tol=1e-9)
        and math.isclose(credit_ask, 1.10, abs_tol=1e-9)
        and math.isclose(credit_mid, 1.05, abs_tol=1e-9)
        for target, credit_bid, credit_ask, credit_mid in recorded
    )
    rows = engine1.rows()["CCS"]
    anchor_row = [row for row in rows if row.short == 7330][0]
    assert anchor_row.display_ask is not None and anchor_row.display_ask < 0
    assert anchor_row.display_bid is not None and anchor_row.display_bid < 0


# ── P23-T7-AC6: the band from match_band, never from a quote ─────────────────


def _headline_table(credit_bid, credit_ask):
    return {
        7310: (0.00, 0.00),
        7330: (credit_bid, credit_ask),
        7350: (0.00, 0.00),
        7370: (0.00, 0.00),
        7325: (0.10, 0.15),
        7345: (0.00, 0.00),
        7335: (0.20, 0.25),
        7355: (0.00, 0.00),
    }


def test_P23_T7_AC6_band_arithmetic_gates_match_and_never_follows_a_quote(monkeypatch):
    cases = [
        # target, credits, expected band, expected matched
        (1.00, (0.96, 1.04), 0.05, True),   # d = 0.04 (mid/ask touch)
        (1.00, (0.80, 0.90), 0.05, False),  # d = 0.10
        (2.95, (2.80, 2.90), 0.05, True),   # d = 0.05, on the band edge
        (2.95, (2.60, 2.80), 0.05, False),  # d = 0.15
        (3.00, (3.08, 3.18), 0.10, True),   # d = 0.08
        (3.00, (3.12, 3.22), 0.10, False),  # d = 0.12
    ]
    band_calls = []
    real_band = engine_module.match_band

    def spy(target):
        band_calls.append(target)
        return real_band(target)

    monkeypatch.setattr(engine_module, "match_band", spy)

    for target, credits, expected_band, expected_matched in cases:
        clock = Clock()
        engine, _ = seed_engine(_headline_table(*credits), clock, target=target)
        assert engine.band == pytest.approx(expected_band), (target, credits)
        assert engine.band == pytest.approx(real_band(target))
        row = engine.rows()["CCS"][2]
        assert row.short == 7330
        assert row.matched is expected_matched, (target, credits)

        # A quote change can neither widen nor narrow h.
        engine.on_quote(leg("C", 7330), 0.00, 0.50, True, True)
        engine.on_quote(leg("C", 7350), 0.00, 0.00, True, True)
        assert engine.band == pytest.approx(expected_band)

    assert band_calls
    assert all(call in (1.00, 2.95, 3.00) for call in band_calls)
    assert set(band_calls) >= {1.00, 2.95, 3.00}


# ── P23-T7-AC7: action vocabulary, 16-line budget, one message per cause ─────


def test_P23_T7_AC7_action_vocabulary_line_budget_and_per_cause_messages():
    clock = Clock()
    engine, batches = seed_engine(AC1_TABLE, clock)
    assert engine.anchor("CCS") == 7330

    # Re-anchor through the live step decision: the walk table's credit bases sit
    # below the Target, so CCS steps down and PCS up, one rung each.
    feed(engine, both_sides(WALK_TABLE))
    acts = engine.evaluate(clock())
    batches.append(acts)
    assert engine.anchor("CCS") == 7325
    # The put ladder mirrors the call ladder around the anchor strike.
    assert engine.anchor("PCS") == 7335

    leased = set()
    subscribed = set()
    peak = 0
    dip = None
    for action in actions(batches):
        assert action.kind in ("lease", "subscribe", "cancel", "release")
        for item in action.legs:
            if action.kind == "lease":
                assert item not in leased, "a leg was leased twice"
                assert item not in subscribed, "a live leg was leased again"
                leased.add(item)
            elif action.kind == "subscribe":
                assert item not in subscribed, "a leg was subscribed twice"
                assert item in leased, "a leg was subscribed without a lease"
                subscribed.add(item)
            elif action.kind == "cancel":
                assert item in subscribed
                subscribed.discard(item)
            else:
                assert item in leased
                leased.discard(item)
            peak = max(peak, len(subscribed))
            if len(subscribed) == MAX_OPTION_LINES - 2:
                dip = len(subscribed)
    assert peak <= MAX_OPTION_LINES
    assert peak == MAX_OPTION_LINES
    assert dip == MAX_OPTION_LINES - 2

    # One message per selection cause, each latched exactly once.
    no_dte = SpreadEngine(clock=Clock(), target=1.00)
    no_dte.toggle_on()
    no_dte.on_no_expiry()
    first = no_dte.evaluate(1000.0)
    second = no_dte.evaluate(1001.0)
    assert len([message for message in first.messages if "0DTE" in message]) == 1
    assert [message for message in second.messages if "0DTE" in message] == []

    # chain edge: the AC1 narrow chain's probe window runs off both ends.
    edge_messages = [message for message in messages(batches) if "Chain edge" in message]
    assert len(edge_messages) == 1

    # rung shortfall: a chain with no listed 20-wide pair at all.
    shortfall_clock = Clock()
    shortfall = SpreadEngine(clock=shortfall_clock, target=1.00)
    shortfall.toggle_on()
    shortfall.on_chain(make_series([7300, 7310, 7325, 7335], [7300, 7310, 7325, 7335]))
    shortfall.on_spot(7315.0)
    shortfall.begin_seed(shortfall_clock())
    shortfall_batches = drive(shortfall, {}, shortfall_clock)
    rung_messages = [
        message for message in messages(shortfall_batches) if "Rung shortfall" in message
    ]
    assert len(rung_messages) == 1
    assert shortfall.anchor("CCS") is None

    # budget refusal: the live window holds all 16 lines, so no probe fits.
    refused_clock = Clock()
    refused, _ = seed_engine(AC1_TABLE, refused_clock)
    refused.set_target(1.60)
    refused.begin_seed(refused_clock())
    refused_batches = drive(refused, both_sides(AC1_TABLE), refused_clock)
    refusal_messages = [
        message
        for message in messages(refused_batches)
        if "Probe refused for capacity" in message
    ]
    assert len(refusal_messages) == 1

    # seed bound: the 12-pair fixture stops once, with one message.
    bound_clock = Clock()
    bound = SpreadEngine(clock=bound_clock, target=1.00)
    bound.toggle_on()
    bound.on_chain(make_series(WIDE_CHAIN, WIDE_CHAIN))
    bound.on_spot(7350.0)
    bound.begin_seed(bound_clock())
    bound_batches = drive(bound, both_sides(WIDE_TABLE), bound_clock)
    bound_messages = [message for message in messages(bound_batches) if "Seed bound" in message]
    assert len(bound_messages) == 1


# ── P23-T8 fixtures: a walk ladder whose credit profile is hand-computed ───
#
# Each strike carries a single premium (bid = ask), so a CCS pair's three credit
# bases collapse to one number: credit(s) = premium(s) - premium(s + 20). The
# table is laid out so the pair at 7330 is 0.70 from a 1.00 Target (not matched),
# its 7335 neighbour is worse (0.75), its 7325 neighbour is better (0.55, an
# improvement of 0.15 > h = 0.05), and the *next* rung down (7320, 0.50) improves
# by exactly h -- which is not "more than h", so the walk stops there.

WALK_PREMIUMS = {
    7300: 2.00,
    7305: 3.45,
    7310: 3.30,
    7315: 3.25,
    7320: 1.50,
    7325: 1.45,
    7330: 1.30,
    7335: 1.25,
    7340: 1.00,
    7345: 1.00,
    7350: 1.00,
    7355: 1.00,
    7360: 0.50,
}

# All three of the anchor pair's credit bases sit below the 1.00 Target and the
# up-neighbour carries *less* credit: the AC-D65.4 direction veto holds.
WALK_TABLE = {strike: (value, value) for strike, value in WALK_PREMIUMS.items()}
WALK_TABLE[7370] = (0.00, 0.00)

# The up-walk profile: the anchor pair is 2.00 above the Target (so the step has
# to move away from the money, mid 2.00 -> 0.20), then 7335 is 0.20 below it (so
# the next step moves toward the money, 0.20 -> 0.60), then 7345 has no listed
# partner and the chain-edge stop takes over.
UP_PREMIUMS = {
    7300: 2.00,
    7305: 3.00,
    7310: 3.00,
    7315: 3.00,
    7320: 1.50,
    7325: 1.00,
    7330: 3.00,
    7335: 1.20,
    7340: 1.10,
    7345: 1.00,
    7350: 1.00,
    7355: 1.00,
    7360: 0.50,
}
UP_TABLE = {strike: (value, value) for strike, value in UP_PREMIUMS.items()}


def walk_engine(table=None, target=1.00, spot=7330.0):
    """Seed on the AC1 fixture (anchor 7330, matched), then re-quote the ladder."""
    clock = Clock()
    engine, _ = seed_engine(AC1_TABLE, clock, target=target, spot=spot)
    assert engine.anchor("CCS") == 7330
    assert engine.anchor("PCS") == 7330
    if table is not None:
        feed(engine, both_sides(table))
    return engine, clock


def peak_lines(live, acts):
    """Replay a plan's option actions over a live-leg set: (peak, low) line count."""
    subscribed = set(live)
    peak = low = len(subscribed)
    for action in acts.actions:
        for item in action.legs:
            if action.kind == "cancel":
                subscribed.discard(item)
            elif action.kind == "subscribe":
                subscribed.add(item)
            peak = max(peak, len(subscribed))
            low = min(low, len(subscribed))
    return peak, low


def greeks_row(engine, side, short):
    rows = engine.rows()[side]
    return [row for row in rows if row.short == short][0]


# ── P23-T8-AC1: one 5-point step, the decided direction, the stop rules ──────


def test_P23_T8_AC1_one_step_per_side_in_the_decided_direction_with_stops():
    engine, clock = walk_engine(WALK_TABLE)
    current = engine._score_pair_complete("CCS", 7330, 7350)
    assert current is not None and current.distance == pytest.approx(0.70)
    assert engine._score_pair_complete("CCS", 7335, 7355).distance == pytest.approx(0.75)
    assert engine._score_pair_complete("CCS", 7325, 7345).distance == pytest.approx(0.55)

    # Direction is decided by the anchor pair's own bases, not a requested
    # anchor: all three (0.30) sit below the Target, so the decided rung is the
    # toward-the-money one (CCS strikes down), never the worse up-neighbour.
    assert engine._step_candidate("CCS", 7330) == 7325
    assert engine._step_candidate("PCS", 7330) == 7335

    # The step, through evaluate(): both sides move exactly one 5-point rung in
    # their own decided direction.
    acts = engine.evaluate(clock())
    assert engine.anchor("CCS") == 7325
    assert engine.anchor("PCS") == 7335
    assert len(acts.cancels) == 2 and len(acts.subscribes) == 2
    # A CCS step down leaves 7360 and arrives at 7320; the mirrored put step up
    # leaves 7305 and arrives at 7345.
    assert set(acts.cancels) == {leg("C", 7360), leg("P", 7305)}
    assert set(acts.subscribes) == {leg("C", 7320), leg("P", 7345)}

    # Leaving pair cancelled before the arriving pair subscribes.
    kinds = [action.kind for action in acts.actions]
    last_cancel = max(index for index, kind in enumerate(kinds) if kind == "cancel")
    first_subscribe = min(index for index, kind in enumerate(kinds) if kind == "subscribe")
    assert last_cancel < first_subscribe

    # One step per evaluation, never a jump: 7320's 0.50 improves 7325's 0.55 by
    # exactly h, so the next evaluation installs nothing.
    stay = engine.evaluate(clock())
    assert stay.actions == [] and stay.cancels == [] and stay.subscribes == []
    assert engine.anchor("CCS") == 7325 and engine.anchor("PCS") == 7335

    # The up-walk: an all-above-target anchor steps away from the money (CCS up,
    # from a 2.00 credit to 0.20) and then stops, because the toward-the-money
    # rung its new bases decide is worse.
    up, up_clock = walk_engine(UP_TABLE)
    up.evaluate(up_clock())
    assert up.anchor("CCS") == 7335
    assert up._score_pair_complete("CCS", 7335, 7355).credit_mid == pytest.approx(0.20)
    up_again = up.evaluate(up_clock())
    assert up_again.actions == [] and up.anchor("CCS") == 7335

    # A stationary feed moves nothing and repeats nothing.
    frozen_feed = up.evaluate(up_clock())
    assert frozen_feed.actions == [] and frozen_feed.messages == []
    assert up.evaluate(up_clock()).actions == []

    # A pair matched on the ask only (credit_ask = 1.00) is matched: no move.
    ask_only, ask_clock = walk_engine(WALK_TABLE)
    ask_only.on_quote(leg("C", 7330), 4.95, 5.00, True, True)
    ask_only.on_quote(leg("C", 7350), 4.00, 4.05, True, True)
    scored = ask_only._score_pair_complete("CCS", 7330, 7350)
    assert scored is not None
    assert scored.credit_ask == pytest.approx(1.00)
    assert scored.distance == pytest.approx(0.0)
    matched = ask_only.evaluate(ask_clock())
    assert not any(item.right == "C" for item in matched.cancels + matched.subscribes)
    assert ask_only.anchor("CCS") == 7330

    # Equal-d neighbours (all three rungs 0.55): the decided rung improves
    # nothing, so repeated evaluations can never oscillate.
    tie_table = dict(WALK_TABLE)
    tie_table[7325] = (1.45, 1.45)
    tie_table[7330] = (1.45, 1.45)
    tie_table[7335] = (1.45, 1.45)
    tie, tie_clock = walk_engine(tie_table)
    for side_anchor in (7330, 7335, 7325):
        assert tie._score_pair_complete(
            "CCS", side_anchor, side_anchor + 20
        ).distance == pytest.approx(0.55)
    moves = 0
    for _ in range(6):
        moves += len(tie.evaluate(tie_clock()).actions)
    assert moves == 0
    assert tie.anchor("CCS") == 7330


# ── P23-T8-AC2: a shared leg keeps its line and its reqId ────────────────────


def test_P23_T8_AC2_shared_leg_untouched_and_the_line_budget_holds():
    engine, clock = walk_engine(WALK_TABLE)
    bound: dict = {}
    next_id = 500
    for live in sorted(engine.live_legs(), key=lambda item: (item.right, item.strike)):
        engine.rebind_leg(live, next_id)
        bound[live] = next_id
        next_id += 1
    assert len(bound) == MAX_OPTION_LINES

    acts = engine.evaluate(clock())
    leaving = {leg("C", 7360), leg("P", 7305)}
    arriving = {leg("C", 7320), leg("P", 7345)}
    assert set(acts.cancels) == leaving
    assert set(acts.subscribes) == arriving

    shared = set(bound) - leaving - arriving
    assert len(shared) == MAX_OPTION_LINES - 2
    for live in shared:
        # A leg in both the old and the new window: no cancel, no subscribe,
        # and the reqId it already held is the same one.
        assert live not in acts.cancels
        assert live not in acts.subscribes
        assert engine._req_ids.get(live) == bound[live]
    for gone in leaving:
        assert engine._req_ids.get(gone) is None
    for fresh in arriving:
        assert engine._req_ids.get(fresh) is None

    peak, low = peak_lines(bound, acts)
    assert peak <= MAX_OPTION_LINES
    assert low == MAX_OPTION_LINES - 2  # the leaving lines go before the arriving
    assert len(engine.live_legs()) == MAX_OPTION_LINES


# ── P23-T8-AC3: greek source precedence, never mixed across the legs ────────


def test_P23_T8_AC3_greek_sources_model_then_last_then_bidask_mean():
    # model (13) wins for both legs even when a last (12) tick is also present.
    model_engine, _ = walk_engine()
    model_engine.on_greek(leg("C", 7330), 13, 0.50, 0.02)
    model_engine.on_greek(leg("C", 7330), 12, 0.90, 0.90)
    model_engine.on_greek(leg("C", 7350), 13, 0.30, 0.01)
    model = model_engine.row_greeks("CCS", 7330, 7350)
    assert model is not None
    assert model.source == "model"
    assert model.delta == pytest.approx(-0.20)
    assert model.gamma == pytest.approx(-0.01)
    row = greeks_row(model_engine, "CCS", 7330)
    assert row.delta == pytest.approx(-0.20)
    assert row.gamma == pytest.approx(-0.01)
    assert model_engine.take_messages() == []

    # last (12) for both legs when neither carries a model greek.
    last_engine, _ = walk_engine()
    last_engine.on_greek(leg("C", 7330), 12, 0.50, 0.02)
    last_engine.on_greek(leg("C", 7350), 12, 0.30, 0.01)
    last = last_engine.row_greeks("CCS", 7330, 7350)
    assert last is not None and last.source == "last"
    assert last.delta == pytest.approx(-0.20)

    # The mean of bid (10) and ask (11) for both legs when neither of the above.
    mean_engine, _ = walk_engine()
    for tick_type, delta, gamma in ((10, 0.40, 0.02), (11, 0.60, 0.04)):
        mean_engine.on_greek(leg("C", 7330), tick_type, delta, gamma)
        mean_engine.on_greek(leg("C", 7350), tick_type, delta / 2, gamma / 2)
    mean = mean_engine.row_greeks("CCS", 7330, 7350)
    assert mean is not None and mean.source == "bidask_mean"
    assert mean.delta == pytest.approx(-0.25)
    assert mean.gamma == pytest.approx(-0.015)

    # Mixed sources (short model, long last): no value and exactly one message.
    mixed_engine, _ = walk_engine()
    mixed_engine.on_greek(leg("C", 7330), 13, 0.50, 0.02)
    mixed_engine.on_greek(leg("C", 7350), 12, 0.30, 0.01)
    assert mixed_engine.row_greeks("CCS", 7330, 7350) is None
    mixed_row = greeks_row(mixed_engine, "CCS", 7330)
    assert mixed_row.delta is None and mixed_row.gamma is None
    mixed_messages = mixed_engine.take_messages()
    assert len(mixed_messages) == 1
    assert "different greek sources" in mixed_messages[0]
    assert mixed_engine.take_messages() == []  # latched once, never repeated


# ── P23-T8-AC4: disconnect freezes, reconnect resumes, one re-seed at most ──


def test_P23_T8_AC4_disconnect_stale_freeze_and_reconnect_resume():
    engine, clock = walk_engine()
    before = {
        (side, row.short): (row.display_ask, row.display_bid)
        for side, rows in engine.rows().items()
        for row in rows
    }
    live = set(engine.live_legs())
    assert len(live) == MAX_OPTION_LINES

    engine.on_disconnected()
    assert engine.walk_frozen is True
    for leg_key in live:
        assert engine.leg_stale(leg_key), leg_key
    lost = engine.evaluate(clock())
    assert lost.status == "stale"
    assert lost.actions == [] and lost.subscribes == [] and lost.cancels == []
    assert lost.spot_subscribe is False and lost.spot_cancel is False
    assert len([message for message in lost.messages if "STALE" in message]) == 1
    frozen_again = engine.evaluate(clock())
    assert frozen_again.actions == [] and frozen_again.cancels == []
    assert engine.anchor("CCS") == 7330 and engine.anchor("PCS") == 7330
    after = {
        (side, row.short): (row.display_ask, row.display_bid)
        for side, rows in engine.rows().items()
        for row in rows
    }
    assert after == before  # every cell kept its last value

    # Reconnect: the same anchor, no re-seed, no re-quote, nothing cancelled.
    clock.advance(1.0)
    engine.on_reconnected()
    reseeds = []
    real_begin_seed = engine.begin_seed
    engine.begin_seed = lambda now: (reseeds.append(now), real_begin_seed(now))[1]
    resume = engine.evaluate(clock())
    assert engine.walk_frozen is False
    assert engine.anchor("CCS") == 7330 and engine.anchor("PCS") == 7330
    assert resume.actions == [] and resume.cancels == []
    assert engine.seed_state().active is False
    assert reseeds == []
    # The cells recover on their own ticks, not on a re-subscribe.
    assert engine.leg_stale(leg("C", 7360)) is True
    engine.on_quote(leg("C", 7360), 0.40, 0.45, True, True)
    assert engine.leg_stale(leg("C", 7360)) is False

    # One leg stays silent past the 3 s timeout after the reconnect: exactly one
    # re-seed, and a second cadence after it does not re-seed again.
    engine.on_quote(leg("C", 7335), -1.0, -1.0, True, True)
    clock.advance(PENDING_SECONDS)
    assert engine.leg_state(leg("C", 7335)) == "pending"
    engine.evaluate(clock())
    assert len(reseeds) == 1
    clock.advance(PENDING_SECONDS)
    engine.evaluate(clock())
    assert len(reseeds) == 1


# ── P23-T8-AC5: one state and one message per line-error class ──────────────


def test_P23_T8_AC5_line_error_classes_each_own_state_one_message():
    # 200 on a non-anchor pair: that pair is dropped for the session (row n/a).
    dropped, clock = walk_engine()
    dropped.on_leg_error(leg("C", 7335), 200)
    first = dropped.evaluate(clock())
    row = greeks_row(dropped, "CCS", 7335)
    assert row.display_ask is None and row.display_bid is None
    assert LegKey(right="C", strike=7335.0) in dropped._dropped
    assert dropped._reseat_counts.get("CCS", 0) == 0
    assert len([message for message in first.messages if "200" in message]) == 1
    # The dead line is gone from the pool and is never re-subscribed.
    assert leg("C", 7335) not in dropped.live_legs()
    dropped.evaluate(clock())
    assert leg("C", 7335) not in dropped.live_legs()

    # 10197, 354 and an unclassified code: no value, no re-seat, one message each.
    for code in (10197, 354, 10167):
        blank, blank_clock = walk_engine()
        blank.on_leg_error(leg("C", 7335), code)
        acts = blank.evaluate(blank_clock())
        healthy = set(blank.live_legs())
        row = greeks_row(blank, "CCS", 7335)
        assert row.display_ask is None and row.display_bid is None, code
        assert LegKey(right="C", strike=7335.0) not in blank._dropped, code
        assert blank._reseat_counts.get("CCS", 0) == 0, code
        assert leg("C", 7335) in healthy, code  # no cancel
        said = [message for message in acts.messages if str(code) in message]
        assert len(said) == 1, code
        assert blank.anchor("CCS") == 7330, code

    # 200 on the anchor pair: exactly one toward-the-money re-seat, then a stop.
    reseated, reseat_clock = walk_engine()
    reseated.on_leg_error(leg("C", 7330), 200)
    move = reseated.evaluate(reseat_clock())
    assert reseated.anchor("CCS") == 7335  # one step, toward the larger credit mid
    assert reseated._reseat_counts.get("CCS", 0) == 1
    assert len([message for message in move.messages if "re-seating" in message]) == 1
    # The same error again: the single re-seat is spent, nothing moves again.
    reseated.on_leg_error(leg("C", 7335), 200)
    stopped = reseated.evaluate(reseat_clock())
    assert reseated._reseat_counts.get("CCS", 0) == 1
    assert len([message for message in stopped.messages if "spent" in message]) == 1

    # 162 is transient: the line is kept, values go STALE after the timeout.
    transient, transient_clock = walk_engine()
    transient.on_leg_error(leg("C", 7335), 162)
    assert transient.leg_stale(leg("C", 7335)) is False
    said = transient.take_messages()
    assert len([message for message in said if "162" in message]) == 1
    row = greeks_row(transient, "CCS", 7335)
    assert row.display_ask is not None and row.display_bid is not None
    assert leg("C", 7335) in transient.live_legs()
    transient_clock.advance(PENDING_SECONDS)
    assert transient.leg_stale(leg("C", 7335)) is True
    assert transient.leg_stale(leg("C", 7355)) is True
    assert leg("C", 7335) in transient.live_legs()  # no cancel
    assert transient._reseat_counts.get("CCS", 0) == 0
    # A fresh tick is the recovery.
    transient.on_quote(leg("C", 7335), 3.95, 4.05, True, True)
    assert transient.leg_stale(leg("C", 7335)) is False


# ── P23-T23: the AC-D65.4 step lives in evaluate() ──────────────────────────


def _step_fixture(target, delta):
    """An anchor pair 0.50 below ``target`` and a decided rung ``delta`` nearer.

    Bid equals ask on every leg, so each pair's three credit bases collapse to
    one number: the anchor pair's is ``target - 0.50`` and the decided rung's is
    ``delta`` closer to the Target.
    """
    anchor_credit = target - 0.50
    rung_credit = anchor_credit + delta
    return {
        7350: (1.00, 1.00),
        7330: (1.00 + anchor_credit, 1.00 + anchor_credit),
        7345: (1.00, 1.00),
        7325: (1.00 + rung_credit, 1.00 + rung_credit),
    }


def test_P23_T23_AC1_evaluate_steps_one_rung_per_side_in_the_decided_direction():
    clock = Clock()
    engine, _ = seed_engine(AC1_TABLE, clock)
    feed(engine, both_sides(WALK_TABLE))

    anchor = engine._score_pair_complete("CCS", 7330, 7350)
    toward = engine._score_pair_complete("CCS", 7325, 7345)
    away = engine._score_pair_complete("CCS", 7335, 7355)
    assert anchor.credit_mid == pytest.approx(0.30)
    assert anchor.distance == pytest.approx(0.70)
    assert toward.distance == pytest.approx(0.55)
    assert away.distance == pytest.approx(0.75)

    acts = engine.evaluate(clock())
    assert engine.anchor("CCS") == 7325
    assert engine.anchor("PCS") == 7335
    assert len(acts.cancels) == 2 and len(acts.subscribes) == 2
    assert set(acts.cancels) == {leg("C", 7360), leg("P", 7305)}
    assert set(acts.subscribes) == {leg("C", 7320), leg("P", 7345)}
    kinds = [action.kind for action in acts.actions]
    assert max(index for index, kind in enumerate(kinds) if kind == "cancel") < min(
        index for index, kind in enumerate(kinds) if kind == "subscribe"
    )

    # The next rung improves d by exactly h (0.55 -> 0.50 at T = 1.00), so the
    # second evaluation on unchanged quotes installs nothing.
    next_rung = engine._score_pair_complete("CCS", 7320, 7340)
    assert engine.band == pytest.approx(0.05)
    assert toward.distance - next_rung.distance == pytest.approx(engine.band)
    second = engine.evaluate(clock())
    assert second.actions == [] and second.subscribes == [] and second.cancels == []
    assert engine.anchor("CCS") == 7325 and engine.anchor("PCS") == 7335

    # An all-above-target anchor steps CCS one rung up (away from the money) and
    # stops: its new bases decide the down rung, whose d is worse.
    up_clock = Clock()
    up, _ = seed_engine(AC1_TABLE, up_clock)
    feed(up, both_sides(UP_TABLE))
    up_anchor = up._score_pair_complete("CCS", 7330, 7350)
    assert up_anchor.credit_mid == pytest.approx(2.00)
    up.evaluate(up_clock())
    assert up.anchor("CCS") == 7335
    assert up._score_pair_complete("CCS", 7335, 7355).credit_mid == pytest.approx(0.20)
    stopped = up.evaluate(up_clock())
    assert stopped.actions == [] and up.anchor("CCS") == 7335


def test_P23_T23_AC2_every_refusal_leaves_the_anchor_and_emits_nothing():
    # (a) matched on the ask basis only: credit_ask == T, so d = 0.
    ask_only, ask_clock = walk_engine()
    ask_only.on_quote(leg("C", 7330), 4.95, 5.00, True, True)
    ask_only.on_quote(leg("C", 7350), 4.00, 4.05, True, True)
    score = ask_only._score_pair_complete("CCS", 7330, 7350)
    assert score is not None and score.credit_ask == pytest.approx(1.00)
    assert score.distance == pytest.approx(0.0)
    matched = ask_only.evaluate(ask_clock())
    assert not any(item.right == "C" for item in matched.cancels + matched.subscribes)
    assert ask_only.anchor("CCS") == 7330

    # (b) the decided rung is not a listed pair: no option action, one chain-edge
    # message naming the current anchor, and no repeat on the next evaluation.
    edge, edge_clock = walk_engine(WALK_TABLE)
    edge.on_chain(make_series([7350, 7355, 7360], [7350, 7355, 7360]))
    first = edge.evaluate(edge_clock())
    assert first.actions == [] and first.subscribes == [] and first.cancels == []
    chain_edge = [message for message in first.messages if "Chain edge" in message]
    assert len(chain_edge) == 1
    assert "7330" in chain_edge[0]
    assert edge.anchor("CCS") == 7330 and edge.anchor("PCS") == 7330
    second = edge.evaluate(edge_clock())
    assert [message for message in second.messages if "Chain edge" in message] == []

    # (c) the decided rung quoted as a sentinel leaves the anchor unchanged.
    unquoted, unquoted_clock = walk_engine(WALK_TABLE)
    for right, strike in (("C", 7325), ("C", 7345), ("P", 7335), ("P", 7315)):
        unquoted.on_quote(leg(right, strike), -1.0, -1.0, True, True)
    sentinel = unquoted.evaluate(unquoted_clock())
    assert sentinel.actions == []
    assert unquoted.anchor("CCS") == 7330 and unquoted.anchor("PCS") == 7330

    # (d) a stationary feed produces zero option actions after the first step.
    steady, steady_clock = walk_engine(WALK_TABLE)
    steady.evaluate(steady_clock())
    assert steady.anchor("CCS") == 7325
    for _ in range(5):
        still = steady.evaluate(steady_clock())
        assert still.actions == [] and still.subscribes == [] and still.cancels == []


@pytest.mark.parametrize(
    "target, delta, moves",
    [
        (1.00, 0.05, False),
        (1.00, 0.10, True),
        (3.00, 0.10, False),
        (3.00, 0.15, True),
    ],
)
def test_P23_T23_AC3_the_step_gate_is_the_band_at_both_tick_tiers(target, delta, moves):
    engine, clock = walk_engine()
    engine.set_target(target)
    feed(engine, both_sides(_step_fixture(target, delta)))
    anchor = engine._score_pair_complete("CCS", 7330, 7350)
    rung = engine._score_pair_complete("CCS", 7325, 7345)
    assert anchor is not None and rung is not None
    assert anchor.credit_mid == pytest.approx(target - 0.50)
    assert rung.credit_mid == pytest.approx(target - 0.50 + delta)
    assert anchor.distance - rung.distance == pytest.approx(delta)
    assert engine.band == pytest.approx(match_band(target))
    engine.evaluate(clock())
    assert engine.anchor("CCS") == (7325 if moves else 7330)


def test_P23_T23_AC4_disagreeing_bases_decide_no_direction():
    clock = Clock()
    engine, _ = seed_engine(AC1_TABLE, clock, target=0.90)
    assert engine.anchor("CCS") == 7330

    # credit_bid 0.60, credit_ask 1.40, mid 1.00 at T = 0.90: two bases above
    # the Target and one below, so no direction is decided.
    fixture = {
        7330: (1.40, 2.20),
        7350: (0.80, 0.80),
        7325: (0.95, 1.15),
        7345: (0.20, 0.20),
    }
    feed(engine, both_sides(fixture))
    anchor = engine._score_pair_complete("CCS", 7330, 7350)
    neighbour = engine._score_pair_complete("CCS", 7325, 7345)
    assert anchor is not None and neighbour is not None
    assert anchor.credit_bid == pytest.approx(0.60)
    assert anchor.credit_ask == pytest.approx(1.40)
    assert anchor.credit_mid == pytest.approx(1.00)
    assert anchor.distance == pytest.approx(0.10)
    assert neighbour.distance == pytest.approx(0.05)
    assert neighbour.distance < anchor.distance

    acts = engine.evaluate(clock())
    assert acts.actions == []
    assert engine.anchor("CCS") == 7330 and engine.anchor("PCS") == 7330


def test_P23_T23_AC5_improvement_below_the_band_never_moves_the_ladder():
    # Red before this change: the pre-change evaluation stepped to any rung with
    # a strictly smaller d. This rung's 0.03 improvement is below h, so it must
    # not move anything.
    clock = Clock()
    engine, _ = seed_engine(AC1_TABLE, clock)
    fixture = {
        7350: (1.00, 1.00),
        7330: (1.30, 1.30),
        7345: (1.00, 1.00),
        7325: (1.33, 1.33),
    }
    feed(engine, both_sides(fixture))
    anchor = engine._score_pair_complete("CCS", 7330, 7350)
    rung = engine._score_pair_complete("CCS", 7325, 7345)
    assert anchor.credit_mid == pytest.approx(0.30)
    assert anchor.distance == pytest.approx(0.70)
    assert rung.credit_mid == pytest.approx(0.33)
    assert rung.distance == pytest.approx(0.67)
    assert anchor.distance - rung.distance == pytest.approx(0.03)
    assert engine.band == pytest.approx(0.05)

    acts = engine.evaluate(clock())
    assert acts.actions == []
    assert engine.anchor("CCS") == 7330 and engine.anchor("PCS") == 7330


def test_P23_T23_ESC124_a_refused_install_leaves_the_session_anchor_with_the_live_one():
    # The walk table warrants both steps, so evaluate() will try to install
    # them. Two option lines are parked on a lease the step cannot reclaim
    # first: after the leaving legs are released the pool still holds all 16
    # lines, so _install_windows reports its capacity refusal (it cancels the
    # leaving legs and stops before it updates the committed window).
    engine, clock = walk_engine(WALK_TABLE)
    assert engine.anchor("CCS") == 7330 and engine.anchor("PCS") == 7330
    assert engine._session_anchor == {"CCS": 7330.0, "PCS": 7330.0}
    assert engine._step_candidate("CCS", 7330) == 7325
    assert engine._step_candidate("PCS", 7330) == 7335

    parked = [leg("C", 7000), leg("P", 6950)]
    engine._leased.update(parked)
    refused = engine.evaluate(clock())

    # The refusal really happened: nothing was subscribed and the leaving legs
    # went before the refusal, so the live window is two lines short.
    assert refused.subscribes == []
    assert len(engine.live_legs()) == MAX_OPTION_LINES - 2
    assert engine.anchor("CCS") == 7330 and engine.anchor("PCS") == 7330

    # The session anchor follows the install, not the request: a refused
    # install leaves it at the pair the live window still holds.
    assert engine._session_anchor == {"CCS": 7330.0, "PCS": 7330.0}

    # Free the parked lines: the same step now installs and both anchors move.
    engine._leased.difference_update(parked)
    installed = engine.evaluate(clock())
    assert set(installed.subscribes) == {leg("C", 7320), leg("P", 7345)}
    assert engine.anchor("CCS") == 7325 and engine.anchor("PCS") == 7335
    assert engine._session_anchor == {"CCS": 7325.0, "PCS": 7335.0}

    # The 200 re-seat path installs a one-rung window too, under the same guard.
    reseat, reseat_clock = walk_engine()
    reseat.on_leg_error(leg("C", 7330), 200)
    reseat._leased.update(parked)
    refused_reseat = reseat.evaluate(reseat_clock())
    assert refused_reseat.subscribes == []
    assert reseat.anchor("CCS") == 7330 and reseat.anchor("PCS") == 7330
    assert reseat._session_anchor == {"CCS": 7330.0, "PCS": 7330.0}
    reseat._leased.difference_update(parked)


def test_P23_T23_AC6_parallel_walk_api_is_gone_and_the_live_helpers_survive():
    removed = [
        "window" + "_step",
        "_requested" + "_targets",
        "_walk" + "_candidate",
        "_best" + "_neighbour",
    ]
    for name in removed:
        assert not hasattr(SpreadEngine, name), name

    engine_source = MODULE_PATH.read_text(encoding="utf-8")
    for name in removed:
        assert name not in engine_source, name

    # No module under ui/, services/, data/, ibkr/ or config/ -- and not main.py
    # or tests/ -- references any of the deleted names.
    roots = [
        REPO_ROOT / "ui",
        REPO_ROOT / "services",
        REPO_ROOT / "data",
        REPO_ROOT / "ibkr",
        REPO_ROOT / "config",
        REPO_ROOT / "tests",
    ]
    paths = [path for root in roots for path in root.rglob("*.py")]
    main_path = REPO_ROOT / "main.py"
    if main_path.exists():
        paths.append(main_path)
    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in removed:
            assert name not in text, (str(path), name)

    tree = ast.parse(engine_source)
    engine_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SpreadEngine"
    )
    class_doc = ast.get_docstring(engine_class) or ""
    assert "evaluate" in class_doc
    assert "step" in class_doc
    for name in removed:
        assert name not in class_doc, name
    module_doc = ast.get_docstring(tree) or ""
    assert "evaluate" in module_doc
    assert "step decision" in module_doc

    for name in (
        "_score_at",
        "_score_pair_complete",
        "_pair_listed",
        "_anchor_matched",
        "_install_windows",
        "_latch",
        "_rank",
        "_best_of",
        "evaluate",
        "band",
    ):
        assert hasattr(SpreadEngine, name), name
    assert isinstance(SpreadEngine.band, property)


def test_P23_T23_AC7_spread_suite_passes_on_the_live_path_without_the_deleted_api():
    source = TEST_PATH.read_text(encoding="utf-8")
    assert "window" + "_step" not in source

    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    expected = {
        "test_P23_T8_AC1_one_step_per_side_in_the_decided_direction_with_stops": (
            'leg("C", 7360)',
            'leg("C", 7320)',
            "engine.evaluate(",
        ),
        "test_P23_T8_AC2_shared_leg_untouched_and_the_line_budget_holds": (
            "engine._req_ids.get(live) == bound[live]",
            "engine.evaluate(",
            "MAX_OPTION_LINES",
        ),
        "test_P23_T8_AC4_disconnect_stale_freeze_and_reconnect_resume": (
            'lost.status == "stale"',
            "engine.evaluate(",
        ),
        "test_P23_T8_AC5_line_error_classes_each_own_state_one_message": (
            "dropped.evaluate(",
            "blank.evaluate(",
            "reseated.evaluate(",
        ),
        "test_P23_T7_AC7_action_vocabulary_line_budget_and_per_cause_messages": (
            "peak == MAX_OPTION_LINES",
            "dip == MAX_OPTION_LINES - 2",
            "engine.evaluate(",
        ),
    }
    for name, fragments in expected.items():
        assert name in functions, name
        segment = ast.get_source_segment(source, functions[name]) or ""
        for fragment in fragments:
            assert fragment in segment, (name, fragment)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(TEST_PATH),
            "-q",
            "-p",
            "no:cacheprovider",
            "-k",
            "not P23_T23_AC7",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]


# ── Module purity (the P23-03 exit condition) ────────────────────────────────


def test_module_is_qt_free_and_ibapi_free():
    script = textwrap.dedent(
        f"""
        import importlib
        import sys
        sys.path.insert(0, {str(REPO_ROOT)!r})
        importlib.import_module("services.option_spread_engine")
        loaded = sorted(
            name for name in sys.modules
            if name.split(".")[0] in ("PyQt6", "PyQt5", "pyqtgraph", "ibapi")
        )
        print(",".join(loaded))
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "", result.stdout
    source = MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("import PyQt6", "import PyQt5", "import pyqtgraph", "import ibapi", "from ibapi"):
        assert forbidden not in source


# ── P23-T16 (ESC-119): the engine owns the session reset ────────────────────


def drive_full_session(target=2.00):
    """Drive a fresh engine through every piece of session state AC1 names."""
    clock = Clock()
    engine, _batches = seed_engine(AC1_TABLE, clock, target=target)
    ccs_anchor = engine.anchor("CCS")
    assert ccs_anchor is not None and engine.anchor("PCS") is not None
    live = set(engine.live_legs())
    assert len(live) == MAX_OPTION_LINES
    assert engine._leased and engine._subscribed_at  # leased and subscribed legs
    assert engine._spot == 7330.0

    # The committed window's pairs, in issue order (each pair is short, long).
    legs = engine._window_legs["CCS"]
    pairs = [(legs[index], legs[index + 1]) for index in range(0, len(legs), 2)]
    anchor_pair = [pair for pair in pairs if pair[0].strike == ccs_anchor][0]
    others = [pair for pair in pairs if pair != anchor_pair]

    # Greeks and line identity (reqIds) on the committed window.
    for item in (anchor_pair[0], anchor_pair[1], others[0][0], others[0][1]):
        engine.on_greek(item, 13, 0.40, 0.02)
    assert engine.row_greeks(
        "CCS", anchor_pair[0].strike, anchor_pair[1].strike
    ) is not None
    for index, item in enumerate(sorted(live, key=lambda key: (key.right, key.strike))):
        engine.rebind_leg(item, 500 + index)
    assert all(engine._req_ids.get(item) is not None for item in live)

    # A seed in progress, a dropped pair, a transient stale leg, latched
    # messages and a pending re-seat left behind by a frozen walk.
    engine.begin_seed(clock())
    engine.on_leg_error(others[0][0], 200)      # non-anchor pair: dropped
    engine.on_leg_error(others[1][0], 162)      # transient: STALE after the timeout
    engine.on_leg_error(anchor_pair[0], 200)    # anchor pair: one pending re-seat
    engine.on_disconnected()                    # frozen walk, every cell STALE
    assert engine.seed_state().active is True
    assert (others[0][0] in engine._dropped) is True
    assert engine.walk_frozen is True
    assert engine.stale_legs() != set()
    assert sorted(engine._latched) != []
    assert engine._pending_reseat
    return engine, clock, live



def assert_session_reset(engine, clock, target, live):
    """AC1's state set: every __init__ field back, clock and Target untouched."""
    fresh = SpreadEngine(clock=clock, target=target)
    expected = {
        name: value
        for name, value in vars(fresh).items()
        if name not in ("_clock", "_target")
    }
    actual = {
        name: value
        for name, value in vars(engine).items()
        if name not in ("_clock", "_target")
    }
    assert actual == expected

    # The named AC1 reads, through the public surface.
    assert engine.live_legs() == set()
    assert engine.rows() == {}
    assert all(engine._req_ids.get(item) is None for item in live)
    assert engine.anchor("CCS") is None and engine.anchor("PCS") is None
    assert engine.seed_state().active is False
    assert engine.walk_frozen is False
    assert engine.stale_legs() == set()
    assert engine.take_messages() == []
    assert sorted(engine._latched) == []

    # The clock seam and the Target survive: set_target is the only writer.
    assert engine._clock is clock
    assert engine._now() == clock()
    clock.advance(11.0)
    assert engine._now() == clock()
    assert engine._target == target


def test_P23_T16_AC1_reset_session_restores_every_init_field_but_clock_and_target():
    engine, clock, live = drive_full_session(target=2.00)

    engine.reset_session()

    assert_session_reset(engine, clock, 2.00, live)
    assert engine._target == 2.00


def test_P23_T16_AC2_toggle_off_delegates_and_the_tree_has_no_constructor_reentry():
    engine, clock, live = drive_full_session(target=2.00)

    engine.toggle_off()

    assert_session_reset(engine, clock, 2.00, live)

    # The tree keeps the OFF entry point live and never re-runs the constructor.
    window_source = (REPO_ROOT / "ui" / "main_window.py").read_text(encoding="utf-8")
    engine_source = MODULE_PATH.read_text(encoding="utf-8")
    assert "_option_reset_engine" not in window_source
    assert re.search(r"_option_engine\.__init__\s*\(", window_source) is None
    assert ".__init__(" not in engine_source  # no call anywhere, only the def

    window_tree = ast.parse(window_source)
    main_class = next(
        node
        for node in window_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "MainWindow"
    )
    methods = {
        node.name: node
        for node in main_class.body
        if isinstance(node, ast.FunctionDef)
    }
    assert "_option_reset_engine" not in methods
    off_source = ast.get_source_segment(window_source, methods["_option_stop"])
    cutoff_source = ast.get_source_segment(
        window_source, methods["_option_enter_cutoff"]
    )
    assert "_option_engine.toggle_off()" in off_source
    assert "_option_engine.reset_session()" in cutoff_source

    # Both names are in the documented public API.
    module_doc = ast.get_docstring(ast.parse(engine_source)) or ""
    assert "toggle_off()" in module_doc
    assert "reset_session()" in module_doc
    class_doc = ast.get_docstring(
        next(
            node
            for node in ast.walk(ast.parse(engine_source))
            if isinstance(node, ast.ClassDef) and node.name == "SpreadEngine"
        )
    ) or ""
    assert "toggle_off" in class_doc
    assert "reset_session" in class_doc


# ── P23-T22 (ESC-121): the eleven test-only accessors are gone ──────────────
#
# The surface that only the tests ever read was deleted, not allowlisted
# (AC-D65.12(i)). The two tests below are the standing gate: the class no
# longer carries the accessors, its documented API block no longer lists them,
# and neither engine suite references one. Each name is assembled from
# fragments so this suite never spells a name it also forbids.


def _deleted_accessor_names():
    """The eleven deleted accessors, assembled so the suite never spells one."""
    return [
        "latched" + "_causes",
        "pair" + "_score",
        "pair" + "_eligible",
        "lease",
        "release",
        "pending" + "_legs",
        "pair" + "_dropped",
        "reseat" + "_count",
        "target",
        "spot",
        "req" + "_id",
    ]


def _accessor_call(block, name):
    """True when ``block`` documents or calls ``name`` as an entry of its own.

    A plain substring search is not the fact being asserted: the surviving
    surface legitimately contains these words as signature parameters
    (``set_target(target)``, ``on_spot(price)``) and as the tail of a longer
    name (``rebind_leg(..., new_req_id)``). The accessor shape is the name as a
    standalone call or property entry, so the two lookarounds and the ``(``/``->``
    that follow it are the whole test.
    """
    return re.search(rf"(?<![\w.]){name}\s*(?:\(|->)", block) is not None


def test_P23_T22_AC1_deleted_accessors_absent_from_the_class_and_its_api():
    names = _deleted_accessor_names()
    for name in names:
        assert name not in vars(SpreadEngine), name

    # The surviving production surface is intact.
    for name in (
        "toggle_on",
        "toggle_off",
        "reset_session",
        "set_target",
        "live_legs",
        "anchor",
        "rows",
        "evaluate",
        "seed_actions",
        "take_messages",
    ):
        assert callable(getattr(SpreadEngine, name)), name

    module_doc = inspect.getdoc(engine_module) or ""
    api_block = module_doc.split("Public API::", 1)[1].split("\n\nNo PyQt6", 1)[0]
    for block in (inspect.getdoc(SpreadEngine) or "", api_block):
        for name in names:
            assert not _accessor_call(block, name), name


def test_P23_T22_AC3_neither_engine_suite_references_a_deleted_accessor():
    names = _deleted_accessor_names()
    for path in (TEST_PATH, REPO_ROOT / "tests" / "test_d65_option_stream.py"):
        text = path.read_text(encoding="utf-8")
        for name in names:
            assert re.search(rf"\.{name}\b", text) is None, (path.name, name)

