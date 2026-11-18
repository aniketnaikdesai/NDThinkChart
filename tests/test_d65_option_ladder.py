"""Offscreen unit tests for the pure option-ladder math (D65 / P23-T1).

``services/option_ladder`` is pure Python by design: these tests must not
require a QApplication and the module under test imports no Qt.

Coverage: the 20-wide ladder from one per-side, row-ordered offset table (AC1),
the short-leg-first row name and its fixture-convention guard (AC2), the
displayed/credit sign pair and its single sign source (AC3), the tick-derived
band (AC4), the quote validity screen (AC5), the three-basis distance and net
greeks (AC6), and snapping, the four-rung window legs, the row/leg fields and
the cell formatters (AC7).  P24 (D66) re-baselines the AC1 geometry onto the
per-side table and adds the display-row/label prose checks.
"""

import ast
import inspect
import math
import re
import subprocess
import sys
import textwrap
from dataclasses import fields
from datetime import date, datetime
from pathlib import Path

import pytest

import services.option_ladder as ladder
from services.option_ladder import (
    LegKey,
    RUNG_OFFSETS,
    SPREAD_WIDTH,
    STRIKE_STEP,
    SpreadRow,
    credit_bases,
    display_bases,
    distance,
    format_ask,
    format_bid,
    format_delta,
    format_gamma,
    format_instrument,
    ladder_pairs,
    match_band,
    net_greeks,
    option_tick,
    snap_rung,
    usable_quote,
    window_legs,
)


# ── AC1: geometry from one per-side, row-ordered offset table ────────────────


def test_P23_T1_AC1_constants():
    assert SPREAD_WIDTH == 20
    assert STRIKE_STEP == 5
    assert RUNG_OFFSETS == {
        "CCS": ((1, 10), (2, 5), (3, 0), (4, -5)),
        "PCS": ((4, 5), (3, 0), (2, -5), (1, -10)),
    }
    # A spread spans exactly four strike steps, and every offset on either side
    # is a whole number of steps.
    assert SPREAD_WIDTH == 4 * STRIKE_STEP
    for side in ("CCS", "PCS"):
        rows = RUNG_OFFSETS[side]
        assert isinstance(rows, tuple) and len(rows) == 4
        assert all(
            isinstance(label, int) and isinstance(offset, int)
            for label, offset in rows
        )
        assert all(offset % STRIKE_STEP == 0 for _, offset in rows)
        # The offset-0 row -- the anchor -- is label 3 on each side.
        assert [label for label, offset in rows if offset == 0] == [3]


@pytest.mark.parametrize("side", ["CCS", "PCS"])
@pytest.mark.parametrize("anchor", [7425.0, 7325.0, 7330.0])
def test_P23_T1_AC1_four_pairs_per_side(side, anchor):
    pairs = ladder_pairs(anchor, side)
    assert len(pairs) == 4
    direction = 1 if side == "CCS" else -1

    # The side's offsets are read in tuple order, top row first.
    shorts = [short for short, _ in pairs]
    assert [short - anchor for short in shorts] == (
        [10, 5, 0, -5] if side == "CCS" else [5, 0, -5, -10]
    )

    for index, (short, long) in enumerate(pairs):
        _label, offset = RUNG_OFFSETS[side][index]
        assert short == pytest.approx(anchor + offset)
        assert long == pytest.approx(short + direction * SPREAD_WIDTH)
        assert abs(long - short) == pytest.approx(SPREAD_WIDTH)


def test_P24_T1_AC1_per_side_table_and_no_second_copy():
    """One table, one entry per side: row order and anchor row are both literal."""
    # CCS keeps P23's offsets; PCS reads its own row-ordered tuple.
    assert [offset for _, offset in RUNG_OFFSETS["CCS"]] == [10, 5, 0, -5]
    assert [offset for _, offset in RUNG_OFFSETS["PCS"]] == [5, 0, -5, -10]
    assert [short - 7425.0 for short, _ in ladder_pairs(7425.0, "CCS")] == [
        10,
        5,
        0,
        -5,
    ]
    assert [short - 7325.0 for short, _ in ladder_pairs(7325.0, "PCS")] == [
        5,
        0,
        -5,
        -10,
    ]

    # The anchor (offset 0, label 3) is row 3 on CCS and row 2 on PCS.
    assert RUNG_OFFSETS["CCS"][2] == (3, 0)
    assert RUNG_OFFSETS["PCS"][1] == (3, 0)
    assert ladder_pairs(7425.0, "CCS")[2] == (7425.0, 7445.0)
    assert ladder_pairs(7325.0, "PCS")[1] == (7325.0, 7305.0)

    # No second offset table exists under either forbidden name.
    source = Path(ladder.__file__).read_text()
    assert "RUNG_OFFSETS_PCS" not in source
    assert "PCS_RUNG_OFFSETS" not in source


def test_P24_T1_AC1_no_second_table_in_production():
    """The forbidden names occur nowhere in the production tree either."""
    offenders = [
        str(path.relative_to(Path(__file__).resolve().parent.parent))
        for path in _production_sources()
        if "RUNG_OFFSETS_PCS" in path.read_text(encoding="utf-8")
        or "PCS_RUNG_OFFSETS" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_P23_T1_AC1_canonical_fixtures():
    ccs = ladder_pairs(7425.0, "CCS")
    assert ccs[2] == (7425.0, 7445.0)
    # CCS: short below long.
    assert ccs[2][0] < ccs[2][1]

    pcs = ladder_pairs(7325.0, "PCS")
    assert pcs == [
        (7330.0, 7310.0),
        (7325.0, 7305.0),
        (7320.0, 7300.0),
        (7315.0, 7295.0),
    ]
    # PCS: short above long, and the anchor pair is display row 2.
    assert pcs[1] == (7325.0, 7305.0)
    assert pcs[1][0] > pcs[1][1]

    # The same holds for every row of either side.
    assert all(short < long for short, long in ccs)
    assert all(short > long for short, long in pcs)


def test_P24_T1_AC3_row_order_and_label_order_are_read_independently():
    """Tuple order is the row order; label order is separate specification data."""
    ccs = RUNG_OFFSETS["CCS"]
    pcs = RUNG_OFFSETS["PCS"]

    assert [label for label, _ in ccs] == [1, 2, 3, 4]
    assert [offset for _, offset in ccs] == [10, 5, 0, -5]

    assert [label for label, _ in pcs] == [4, 3, 2, 1]
    assert [offset for _, offset in pcs] == [5, 0, -5, -10]

    pcs_shorts = [short for short, _ in ladder_pairs(7325.0, "PCS")]
    assert pcs_shorts == [7330.0, 7325.0, 7320.0, 7315.0]
    assert pcs_shorts == sorted(pcs_shorts, reverse=True)

    # A label-sorted iteration would reverse the PCS rows -- observably wrong.
    label_sorted_offsets = [offset for _, offset in sorted(pcs, key=lambda row: row[0])]
    assert label_sorted_offsets == [-10, -5, 0, 5]
    assert [7325.0 + offset for offset in label_sorted_offsets] != pcs_shorts


def test_P23_T1_AC1_unknown_side_rejected():
    with pytest.raises(ValueError):
        ladder_pairs(7425.0, "IC")
    # The side is case-insensitive and defaults to CCS.
    assert ladder_pairs(7425.0) == ladder_pairs(7425.0, "ccs")


@pytest.mark.parametrize("side", ["CCS", "PCS"])
@pytest.mark.parametrize("anchor", [7425.0, 7325.0, 7330.0])
def test_P24_T1_AC2_tuple_order_per_side(side, anchor):
    pairs = ladder_pairs(anchor, side)
    direction = 1 if side == "CCS" else -1
    expected_offsets = [10, 5, 0, -5] if side == "CCS" else [5, 0, -5, -10]

    assert [short - anchor for short, _ in pairs] == expected_offsets
    assert all(long == short + direction * SPREAD_WIDTH for short, long in pairs)

    if side == "CCS":
        # CCS geometry is byte-identical to P23's shared-table output.
        assert pairs == [
            (anchor + 10.0, anchor + 30.0),
            (anchor + 5.0, anchor + 25.0),
            (anchor, anchor + 20.0),
            (anchor - 5.0, anchor + 15.0),
        ]


def test_P24_T1_AC2_canonical_pairs_signature_and_errors():
    assert ladder_pairs(7325.0, "PCS") == [
        (7330.0, 7310.0),
        (7325.0, 7305.0),
        (7320.0, 7300.0),
        (7315.0, 7295.0),
    ]
    assert ladder_pairs(7325.0, "PCS")[1] == (7325.0, 7305.0)
    assert ladder_pairs(7425.0)[2] == (7425.0, 7445.0)

    # The default side is CCS, the signature is unchanged and an unknown side
    # still raises ValueError.
    signature = inspect.signature(ladder_pairs)
    assert list(signature.parameters) == ["anchor_short", "side"]
    assert signature.parameters["side"].default == "CCS"
    assert signature.return_annotation == "List[Tuple[float, float]]"
    assert ladder_pairs(7425.0) == ladder_pairs(7425.0, "ccs")
    with pytest.raises(ValueError):
        ladder_pairs(7425.0, "IC")


# ── P23-T20 AC1: the unused production fixture guard is deleted ─────────────

_PRODUCTION_DIRS = ("ui", "services", "data", "ibkr", "config")


def _production_sources():
    """Every production ``.py`` source under the repository root."""
    root = Path(__file__).resolve().parent.parent
    paths = []
    for name in _PRODUCTION_DIRS:
        paths.extend(sorted((root / name).rglob("*.py")))
    main_module = root / "main.py"
    if main_module.exists():
        paths.append(main_module)
    return paths


def test_P23_T20_AC1_validate_spread_is_gone():
    # The helper is gone from the module surface, including its docstring API list.
    assert not hasattr(ladder, "validate_spread")
    assert "validate_spread" not in (ladder.__doc__ or "")

    # No production module imports or references it, and no replacement helper
    # was added under the same name.
    root = Path(__file__).resolve().parent.parent
    offenders = [
        str(path.relative_to(root))
        for path in _production_sources()
        if "validate_spread" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


# ── AC2: short-leg-first naming and the fixture-convention guard ─────────────


def test_P23_T1_AC2_format_instrument_short_first():
    assert format_instrument("SPX", date(2026, 11, 17), 7425, 7445) == "SPX Nov17 7425/7445"
    assert format_instrument("SPX", date(2026, 11, 17), 7340, 7320) == "SPX Nov17 7340/7320"
    # The expiry may also arrive as a datetime or as an already-formatted string.
    assert (
        format_instrument("SPX", datetime(2026, 11, 17, 15, 30), 7425.0, 7445.0)
        == "SPX Nov17 7425/7445"
    )
    assert format_instrument("SPX", "Nov17", 7425, 7445) == "SPX Nov17 7425/7445"


@pytest.mark.parametrize(
    "side,short,long,expected",
    [
        ("CCS", 7425.0, 7445.0, "SPX Nov17 7425/7445"),
        ("PCS", 7340.0, 7320.0, "SPX Nov17 7340/7320"),
    ],
)
def test_P23_T1_AC2_name_carries_exactly_twenty_points(side, short, long, expected):
    assert format_instrument("SPX", date(2026, 11, 17), short, long) == expected
    # The name is short-leg-first, and the two legs printed in it are 20 apart.
    name_short, name_long = expected.rsplit(" ", 1)[1].split("/")
    assert float(name_short) == pytest.approx(short)
    assert float(name_long) == pytest.approx(long)
    assert abs(float(name_long) - float(name_short)) == pytest.approx(SPREAD_WIDTH)


def _fixture_guard(side, short, long):
    """The AC-D65.2 fixture convention, held here in the test file itself.

    A legal pair is exactly :data:`SPREAD_WIDTH` wide and points the way its
    side does: a CCS has its long strike *above* its short (7425/7445), a PCS
    has its long strike *below* its short (7340/7320).  So a 10-wide 7425/7435
    is rejected, and so is an inverted PCS such as 7315/7435; the legal 20-wide
    7435/7455 is accepted.
    """
    key = str(side).strip().upper()
    if key not in ("CCS", "PCS"):
        raise ValueError(f"unknown option side {side!r}: expected CCS or PCS")
    short_value = float(short)
    long_value = float(long)
    width = long_value - short_value
    if not math.isclose(abs(width), SPREAD_WIDTH, abs_tol=1e-9):
        raise ValueError(
            f"{key} pair {short_value:g}/{long_value:g} is {abs(width):g} wide, "
            f"not {SPREAD_WIDTH}"
        )
    if key == "CCS" and width <= 0:
        raise ValueError(
            f"CCS pair {short_value:g}/{long_value:g} has its long strike "
            "below its short strike"
        )
    if key == "PCS" and width >= 0:
        raise ValueError(
            f"PCS pair {short_value:g}/{long_value:g} has its long strike "
            "above its short strike"
        )


def test_P23_T20_AC2_fixture_guard_rejects_and_accepts():
    # A 10-wide pair is not a ladder spread.
    with pytest.raises(ValueError):
        _fixture_guard("CCS", 7425, 7435)

    # An inverted PCS (long strike above the short) is not a PCS -- both the
    # canonical 120-wide example and a 20-wide inversion are rejected.
    with pytest.raises(ValueError):
        _fixture_guard("PCS", 7315, 7435)
    with pytest.raises(ValueError):
        _fixture_guard("PCS", 7435, 7455)

    # The legal 20-wide pairs are accepted, canonical fixtures included.
    _fixture_guard("CCS", 7435, 7455)
    _fixture_guard("CCS", 7425, 7445)
    _fixture_guard("PCS", 7340, 7320)

    # Every canonical ladder pair passes the guard.
    for side, anchor in (("CCS", 7425.0), ("PCS", 7340.0)):
        for short, long in ladder_pairs(anchor, side):
            _fixture_guard(side, short, long)


# ── AC3: the displayed / credit sign pair ────────────────────────────────────


@pytest.mark.parametrize(
    "bid_s,ask_s,bid_l,ask_l",
    [
        # A real CCS 7425/7445 quote: the long (cheaper) call against the short.
        (60.00, 60.50, 50.00, 50.50),
        # A real PCS 7340/7320 quote: the long (cheaper) put against the short.
        (60.00, 60.50, 50.00, 50.50),
        # A flatter pair.
        (10.00, 10.20, 9.00, 9.30),
    ],
)
def test_P23_T1_AC3_display_and_credit_are_exact_negatives(bid_s, ask_s, bid_l, ask_l):
    display_ask, display_bid = display_bases(bid_s, ask_s, bid_l, ask_l)
    assert display_ask == pytest.approx(ask_l - bid_s)
    assert display_bid == pytest.approx(bid_l - ask_s)

    credit_bid, credit_ask, credit_mid = credit_bases(bid_s, ask_s, bid_l, ask_l)
    # The ASK cell pairs with credit_bid; the BID cell with credit_ask.
    assert credit_bid == pytest.approx(-display_ask)
    assert credit_ask == pytest.approx(-display_bid)
    assert credit_mid == pytest.approx((credit_bid + credit_ask) / 2.0)


def test_P23_T1_AC3_credit_pair_renders_negative_by_design():
    # The long leg of a credit spread is the cheaper one, so the displayed pair
    # is negative and the credit bases are its positive mirror.
    bid_s, ask_s, bid_l, ask_l = 60.00, 60.50, 50.00, 50.50
    display_ask, display_bid = display_bases(bid_s, ask_s, bid_l, ask_l)
    credit_bid, credit_ask, credit_mid = credit_bases(bid_s, ask_s, bid_l, ask_l)

    assert display_ask < 0.0
    assert display_bid < 0.0
    assert credit_bid > 0.0
    assert credit_ask > 0.0
    assert credit_mid > 0.0
    assert credit_bid + display_ask == pytest.approx(0.0)
    assert credit_ask + display_bid == pytest.approx(0.0)


def test_P23_T1_AC3_one_sign_source():
    """No third expression in the module negates a price."""
    tree = ast.parse(Path(ladder.__file__).read_text())
    priceish = re.compile(r"(bid|ask|credit|display|price|premium)")

    negating_functions = set()
    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        for node in ast.walk(function):
            if not isinstance(node, ast.UnaryOp) or not isinstance(node.op, ast.USub):
                continue
            if any(
                isinstance(child, ast.Name) and priceish.search(child.id.lower())
                for child in ast.walk(node.operand)
            ):
                negating_functions.add(function.name)

    assert negating_functions == {"credit_bases"}


# ── AC4: the tick-derived match band ────────────────────────────────────────


@pytest.mark.parametrize(
    "target,tick",
    [
        (1.00, 0.05),
        (2.95, 0.05),
        (3.00, 0.10),
        (5.00, 0.10),
    ],
)
def test_P23_T1_AC4_band_table(target, tick):
    assert option_tick(target) == pytest.approx(tick)
    assert match_band(target) == pytest.approx(max(0.05, tick))


def test_P23_T1_AC4_band_is_max_of_floor_and_tick_everywhere():
    levels = [0.05 + 0.05 * step for step in range(0, 399)]  # 0.05 .. 19.95
    for target in levels:
        tick = option_tick(target)
        assert tick in (0.05, 0.10)
        assert match_band(target) == pytest.approx(max(0.05, tick))

    # The tier boundary is exactly 3.00.
    assert option_tick(2.99) == pytest.approx(0.05)
    assert option_tick(3.00) == pytest.approx(0.10)
    assert match_band(2.99) == pytest.approx(0.05)
    assert match_band(3.00) == pytest.approx(0.10)


# ── AC5: quote validity ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "bid,ask,received_bid,received_ask,expected",
    [
        # A received 0 bid is a real price.
        (0.0, 1.0, True, True, (0.0, 1.0)),
        # Both sides valid.
        (1.0, 2.0, True, True, (1.0, 2.0)),
        # IBKR / junk sentinels on the bid.
        (-1, 1.0, True, True, (None, None)),
        (1.7976931348623157e308, 1.0, True, True, (None, None)),
        (float("nan"), 1.0, True, True, (None, None)),
        (float("inf"), 1.0, True, True, (None, None)),
        (-float("inf"), 1.0, True, True, (None, None)),
        # Sentinels on the ask.
        (1.0, -1, True, True, (None, None)),
        (1.0, 1.7976931348623157e308, True, True, (None, None)),
        (1.0, float("nan"), True, True, (None, None)),
        (1.0, float("inf"), True, True, (None, None)),
        # An unreceived side is absent even when the number looks valid.
        (1.0, 2.0, False, True, (None, None)),
        (1.0, 2.0, True, False, (None, None)),
        (0.0, 1.0, False, True, (None, None)),
        # A crossed quote invalidates the leg.
        (2.0, 1.0, True, True, (None, None)),
        # An absent numeric side.
        (None, 2.0, True, True, (None, None)),
    ],
)
def test_P23_T1_AC5_validity_table(bid, ask, received_bid, received_ask, expected):
    assert usable_quote(bid, ask, received_bid, received_ask) == expected


def test_P23_T1_AC5_one_sided_leg_is_absent_both_ways():
    bid, ask = usable_quote(1.0, 2.0, True, False)
    assert bid is None and ask is None
    bid, ask = usable_quote(1.0, 2.0, False, True)
    assert bid is None and ask is None


# ── AC6: distance and net greeks ────────────────────────────────────────────


@pytest.mark.parametrize(
    "target,credit_bid,credit_ask,credit_mid,expected",
    [
        # Mid-only distance.
        (10.00, 9.50, 10.50, 10.00, 0.00),
        (10.40, 9.50, 10.50, 10.00, 0.10),
        # The ask basis is the nearest.
        (10.90, 9.50, 10.50, 10.00, 0.40),
        # The bid basis is the nearest.
        (9.20, 9.50, 10.50, 10.00, 0.30),
        # Ask-only touch.
        (10.50, 9.50, 10.50, 10.00, 0.00),
        # Bid-only touch.
        (9.50, 9.50, 10.50, 10.00, 0.00),
    ],
)
def test_P23_T1_AC6_distance_over_credit_bases(
    target, credit_bid, credit_ask, credit_mid, expected
):
    computed = distance(target, credit_bid, credit_ask, credit_mid)
    assert computed == pytest.approx(expected)
    assert computed == pytest.approx(
        min(
            abs(credit_mid - target),
            abs(credit_ask - target),
            abs(credit_bid - target),
        )
    )


def test_P23_T1_AC6_distance_must_be_given_credits_not_display():
    bid_s, ask_s, bid_l, ask_l = 60.00, 60.50, 50.00, 50.50
    display_ask, display_bid = display_bases(bid_s, ask_s, bid_l, ask_l)
    credit_bid, credit_ask, credit_mid = credit_bases(bid_s, ask_s, bid_l, ask_l)
    target = 10.00

    on_credits = distance(target, credit_bid, credit_ask, credit_mid)
    on_display = distance(target, display_bid, display_ask, (display_ask + display_bid) / 2.0)

    assert on_credits == pytest.approx(0.00)
    assert on_display == pytest.approx(19.50)
    assert on_display != pytest.approx(on_credits)


def test_P23_T1_AC6_net_greeks_subtract_short_from_long():
    assert net_greeks(-0.30, 0.25, 0.010, 0.004) == (
        pytest.approx(0.55),
        pytest.approx(-0.006),
    )


@pytest.mark.parametrize(
    "delta_s,delta_l,expected_delta",
    [
        (None, 0.25, None),
        (-0.30, None, None),
        (None, None, None),
        (-0.30, 0.25, 0.55),
    ],
)
@pytest.mark.parametrize(
    "gamma_s,gamma_l,expected_gamma",
    [
        (None, 0.004, None),
        (0.010, None, None),
        (None, None, None),
        (0.010, 0.004, -0.006),
    ],
)
def test_P23_T1_AC6_net_greeks_propagate_none(
    delta_s, delta_l, expected_delta, gamma_s, gamma_l, expected_gamma
):
    delta, gamma = net_greeks(delta_s, delta_l, gamma_s, gamma_l)
    if expected_delta is None:
        assert delta is None
    else:
        assert delta == pytest.approx(expected_delta)
    if expected_gamma is None:
        assert gamma is None
    else:
        assert gamma == pytest.approx(expected_gamma)


def test_P23_T1_AC6_net_greeks_none_propagates_per_metric():
    delta, gamma = net_greeks(-0.30, 0.25, None, 0.004)
    assert delta == pytest.approx(0.55)
    assert gamma is None


# ── AC7: snapping, window legs, row fields, cell formatters ─────────────────


FULL_GRID = [float(7400 + 5 * step) for step in range(0, 13)]  # 7400 .. 7460


def test_P23_T1_AC7_snap_rung_exact_and_between():
    assert snap_rung(7425.0, FULL_GRID, 7425.0) == 7425.0
    # Between two listed strikes, the nearer one wins.
    assert snap_rung(7427.0, FULL_GRID, 7425.0) == 7425.0
    assert snap_rung(7428.0, FULL_GRID, 7425.0) == 7430.0


def test_P23_T1_AC7_snap_rung_tie_resolves_to_strike_nearer_anchor():
    # 7427.5 is equidistant from 7425 and 7430; the anchor decides.
    assert snap_rung(7427.5, FULL_GRID, 7425.0) == 7425.0
    assert snap_rung(7427.5, FULL_GRID, 7440.0) == 7430.0


def test_P23_T1_AC7_snap_rung_none_without_a_listed_twenty_wide_pair():
    # Three consecutive 5-point strikes, none of which has a partner 20 away.
    sparse = [7400.0, 7405.0, 7410.0]
    for strike in (7395.0, 7400.0, 7405.0, 7410.0, 7420.0):
        assert snap_rung(strike, sparse, 7405.0) is None
    assert snap_rung(7405.0, [], 7405.0) is None


def test_P23_T1_AC7_window_legs_eight_per_anchor():
    legs = window_legs(7425.0)
    assert len(legs) == 8
    assert legs == [
        LegKey("C", 7435.0), LegKey("C", 7455.0),
        LegKey("C", 7430.0), LegKey("C", 7450.0),
        LegKey("C", 7425.0), LegKey("C", 7445.0),
        LegKey("C", 7420.0), LegKey("C", 7440.0),
    ]

    pcs_legs = window_legs(7325.0, "PCS")
    assert len(pcs_legs) == 8
    assert pcs_legs == [
        LegKey("P", 7330.0), LegKey("P", 7310.0),
        LegKey("P", 7325.0), LegKey("P", 7305.0),
        LegKey("P", 7320.0), LegKey("P", 7300.0),
        LegKey("P", 7315.0), LegKey("P", 7295.0),
    ]

    # Every anchor yields its own pair-per-rung window: short then long.
    for anchor in (7425.0, 5000.0):
        legs = window_legs(anchor)
        assert len(legs) == 8
        pairs = ladder_pairs(anchor)
        for index, (short, long) in enumerate(pairs):
            assert legs[2 * index] == LegKey("C", short)
            assert legs[2 * index + 1] == LegKey("C", long)


def test_P23_T1_AC7_leg_key_and_spread_row_carry_exactly_their_fields():
    assert [field.name for field in fields(LegKey)] == ["right", "strike"]
    assert [field.name for field in fields(SpreadRow)] == [
        "rung",
        "short",
        "long",
        "display_name",
        "display_ask",
        "display_bid",
        "delta",
        "gamma",
        "matched",
    ]

    short, long = ladder_pairs(7425.0)[2]
    row = SpreadRow(
        rung=3,
        short=short,
        long=long,
        display_name=format_instrument("SPX", date(2026, 11, 17), short, long),
        display_ask=-10.5,
        display_bid=-10.0,
        delta=0.25,
        gamma=0.0043,
        matched=True,
    )
    assert row.rung == 3
    assert (row.short, row.long) == (7425.0, 7445.0)
    assert row.display_name == "SPX Nov17 7425/7445"
    assert row.matched is True


def test_P23_T1_AC7_cell_formatters():
    assert format_ask(4.2) == "4.20"
    assert format_bid(-3.8) == "-3.80"
    assert format_ask(0.0) == "0.00"
    assert format_delta(-0.1234) == "-0.123"
    assert format_delta(0.5) == "0.500"
    # Gamma is 4 significant digits, not 4 decimals.
    assert format_gamma(0.0123456) == "0.01235"
    assert format_gamma(4.52345) == "4.523"
    assert format_gamma(1.0) == "1"
    # An absent side formats as an empty cell.
    assert format_ask(None) == ""
    assert format_bid(None) == ""
    assert format_delta(None) == ""
    assert format_gamma(None) == ""


def test_P23_T1_AC7_module_is_qt_free():
    """The module imports in an isolated interpreter and loads no Qt module."""
    script = textwrap.dedent(
        """
        import sys
        import services.option_ladder  # noqa: F401

        loaded = sorted(
            name for name in sys.modules
            if name == "PyQt6" or name.startswith("PyQt6.")
            or name == "pyqtgraph" or name.startswith("pyqtgraph.")
        )
        assert not loaded, loaded
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(Path(__file__).resolve().parent.parent),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


# ── P24 AC4/AC5: the prose that states the per-side rule ────────────────────


def _rung_offsets_comment() -> str:
    """The comment block immediately above ``RUNG_OFFSETS``."""
    lines = Path(ladder.__file__).read_text(encoding="utf-8").splitlines()
    start = next(
        index for index, line in enumerate(lines) if line.startswith("RUNG_OFFSETS =")
    )
    block = []
    index = start - 1
    while index >= 0 and lines[index].lstrip().startswith("#"):
        block.append(lines[index])
        index -= 1
    return "\n".join(reversed(block))


def test_P24_T1_AC4_retired_invariant_is_gone():
    source = Path(ladder.__file__).read_text(encoding="utf-8")
    assert "both sides" not in source
    assert "identically on both sides" not in source
    assert "same offset table on both sides" not in source


@pytest.mark.parametrize(
    "block_name",
    ["module docstring", "offset table comment", "ladder_pairs docstring"],
)
def test_P24_T1_AC4_per_side_rule_stated(block_name):
    blocks = {
        "module docstring": inspect.getdoc(ladder) or "",
        "offset table comment": _rung_offsets_comment(),
        "ladder_pairs docstring": inspect.getdoc(ladder_pairs) or "",
    }
    text = blocks[block_name]

    # The per-side rule, the PCS offsets and the anchor row per side.
    assert "CCS" in text and "PCS" in text
    assert "per-side" in text or "that side's offset" in text
    assert "+5" in text and "-10" in text
    assert "row 3" in text
    assert "row 2" in text


def test_P24_T1_AC4_ladder_pairs_docstring_names_canonical_rows():
    doc = inspect.getdoc(ladder_pairs) or ""
    assert "7425/7445" in doc
    assert "ladder_pairs(7425)[2]" in doc
    assert "7325/7305" in doc
    assert "ladder_pairs(7325, SIDE_PCS)[1]" in doc
    # The PCS anchor sits on row 2, the CCS anchor on row 3.
    assert "row 2" in doc and "row 3" in doc


def test_P24_T1_AC5_spread_row_docstring_names_display_row_and_label():
    doc = inspect.getdoc(SpreadRow) or ""
    assert "display row" in doc
    assert "1-based" in doc
    assert "label" in doc
    assert "4, 3, 2, 1" in doc
    assert "1, 2, 3, 4" in doc
    assert "row-number" in doc
    assert "Nothing renders" in doc

    # The frozen field list, in order, with rung still first.
    assert [field.name for field in fields(SpreadRow)] == [
        "rung",
        "short",
        "long",
        "display_name",
        "display_ask",
        "display_bid",
        "delta",
        "gamma",
        "matched",
    ]
