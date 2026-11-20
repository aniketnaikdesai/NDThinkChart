"""P29-T5 — the phase fence for D96–D100 (``AC-D100.3``, ``AC-P29-05-PINS``,
``AC-P29-05-MAP``).

One assertion per named artefact the phase relies on. Every value is read off
the live modules or the live requirements record — nothing is copied from
prose, and no literal file/line count or phase commit hash is pinned, so a
later phase can extend the record without reddening this fence.

The fence pins:

* the requirements record's own markers: the existing-repository sentence, the
  ``D41``–``D95`` record (presence per id in *a* heading — the record is mixed,
  as the P26/P27/P28 fences note), P29's own ``#### D96``–``#### D100``
  entries, ``Journey 78``–``Journey 81``, the ``AC-D1.1``–``AC-D95.3`` range
  plus ``AC-D96.1``–``AC-D100.3``, ``A1``–``A240`` plus ``A241``–``A245``,
  ``R1``–``R180`` plus ``R181``–``R185``, and the Current Tech Stack section;
* the values P29 must not move, read off source: ``ENVELOPE_VERSION``,
  ``COALESCE_MS``, the ``CHANNELS`` tuple and the three op-kind frozensets
  (``update_bar``; ``set_bars``/``set_volume``/``clear``;
  ``set_visible_range``/``set_partial``), the ``studies`` and
  ``drawing_groups`` column sets through ``PRAGMA table_info`` (no migration
  landed), ``format_gap_report``'s signature and its ``unmonitored`` shape for
  a fixed epoch pair, ``Alarm``'s field set with **no** touch/armed field (a
  touch is derived — DG133 — and ``triggered`` stays the only latch),
  ``evaluate_alarms``'s signature, and ``DrawingStore.update_group``'s accepted
  set: exactly the four mutable names apply and a fifth raises ``ValueError``
  with the row untouched.

The delta-scope record (``git diff --name-only 3b92ce6`` against the phase
allowlist) is a **build artefact**, not a test: a git diff pinned inside pytest
would redden every later phase (S-P24-5 / the P24 fence precedent). It is
recorded in ``docs/build/results/P29-T5.json``. The phase allowlist is the
seven production files (``data/study_store.py``, ``data/drawing_store.py``,
``services/alarm_service.py``, ``services/alarm_monitor.py``,
``ui/main_window.py``, ``ui/lwc_bridge.py``, ``ui/lwc_host.py``), the three
re-baselined suites (``tests/test_alarm_service.py``,
``tests/test_d40_tws_lifecycle.py``, ``tests/test_lwc_bridge.py``), the four
new suites (this file, ``tests/test_d96_d100_store_atomicity.py``,
``tests/test_d98_outage_baseline.py``, ``tests/test_d99_page_ready_delivery.py``)
and ``docs/``. Anything outside that is a scope breach to escalate, never to
justify.

G6 is **owner-run and never claimed here**: no case in this suite (or any P29
unit suite) asserts a live TWS socket drop, a live alarm fire or a
post-reconnect price read from TWS. P29-T3's exit condition names G6 as the
owner's to observe.
"""

from __future__ import annotations

import inspect
import re
import time
import uuid
from dataclasses import fields
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
CODEBASE_MAP = REPO_ROOT / "docs" / "codebase-map.md"

#: The Existing Repository marker sentence (R25's standing rule).
MARKER_SENTENCE = "This is an existing repository."

#: ``D41``–``D95`` are the standing ledger the P29 phase must not drop.
PRE_P29_DEFECTS = range(41, 96)
#: P29's own defect entries, as ``#### D96``–``#### D100`` sub-headings.
P29_DEFECTS = range(96, 101)
#: Journeys 78–81 are P29's four journeys (D98's fixture is its ACs).
P29_JOURNEYS = (78, 79, 80, 81)

#: Defects that carry no numbered acceptance criteria. ``D29``–``D35`` are
#: *intentionally unassigned* (the record says so: the batch numbering jumps
#: ``D28`` → ``D36``); ``D42``/``D43`` are requirement-resolution defects whose
#: record is the resolution text plus A/R rows, with no ``AC-D<n>.<m>`` ledger.
DEFECTS_WITHOUT_CRITERIA = frozenset(range(29, 36)) | {42, 43}

#: P29's own criteria: the ``AC-D96.1``–``AC-D100.3`` ledger, per defect.
P29_CRITERIA = {
    96: (1, 2, 3),
    97: (1, 2, 3),
    98: (1, 2),
    99: (1, 2),
    100: (1, 2, 3),
}

#: The standing A1–A240 / R1–R180 ranges plus P29's A241–A245 / R181–R185.
ASSUMPTIONS = range(1, 241)
P29_ASSUMPTIONS = range(241, 246)
RISKS = range(1, 181)
P29_RISKS = range(181, 186)

#: The four suites P29 adds (the plan's D97 cases live in the existing
#: ``tests/test_alarm_service.py`` beside its one named re-baseline).
NEW_SUITES = (
    "tests/test_d96_d100_store_atomicity.py",
    "tests/test_d98_outage_baseline.py",
    "tests/test_d99_page_ready_delivery.py",
    "tests/test_p29_fence.py",
)

#: The three named re-baselines, asserted where the map records them.
REBASELINED_CASES = (
    "test_exactly_on_alert_price_above_counts",
    "test_d40_4_transient_drop_no_pause_ui",
    "test_queue_until_ready_holds_pre_ready_ops",
)

#: The seven production files P29 changes in place (no new module).
CHANGED_PRODUCTION = (
    "data/study_store.py",
    "data/drawing_store.py",
    "services/alarm_service.py",
    "services/alarm_monitor.py",
    "ui/main_window.py",
    "ui/lwc_bridge.py",
    "ui/lwc_host.py",
)

#: A sample of the notes the map must carry forward (P28's note is named by
#: the AC; the older ones witness that a refresh appends rather than replaces).
PRIOR_NOTE_MARKERS = (
    "P6 note",
    "P9 note",
    "P25 note",
    "P28 note",
)

#: Today's column sets, read from the ``CREATE TABLE`` blocks in ``data/db.py``
#: (P29 adds no migration, so ``PRAGMA table_info`` must still agree).
STUDIES_COLUMNS = frozenset({"id", "symbol", "type", "enabled", "params"})
DRAWING_GROUPS_COLUMNS = frozenset(
    {
        "id",
        "symbol",
        "name",
        "seq_number",
        "color",
        "visible",
        "locked",
        "created_at",
    }
)

#: ``update_group``'s four mutable names — it may accept no fifth.
UPDATE_GROUP_FIELDS = ("name", "color", "visible", "locked")


def _text() -> str:
    return REQUIREMENTS.read_text(encoding="utf-8")


def _headings(text: str) -> list[str]:
    """Every markdown heading line, at any level (1–6 ``#``)."""
    return [line for line in text.splitlines() if re.match(r"^#{1,6} \S", line)]


# ── AC-D100.3 / P29-T5-01 — the requirements record's markers ───────────────

def test_existing_repository_marker_and_current_tech_stack_are_present():
    text = _text()
    assert MARKER_SENTENCE in text
    assert "Current Tech Stack" in text
    # The stack section itself, not merely a mention of its name.
    assert re.search(r"(?m)^\*\*Current Tech Stack:\*\*", text)


def test_d41_to_d95_are_present_per_id_in_a_heading():
    headings = _headings(_text())
    missing = [
        defect
        for defect in PRE_P29_DEFECTS
        if not any(re.search(rf"\bD{defect}\b", heading) for heading in headings)
    ]
    assert not missing, f"D41–D95 ids missing from every heading: {missing}"

    # P29's own entries are the ``#### D96``–``#### D100`` sub-headings.
    for defect in P29_DEFECTS:
        assert any(
            re.match(rf"^#### D{defect}\b", heading) for heading in headings
        ), f"#### D{defect} entry missing"


def test_p29_journeys_are_present():
    headings = _headings(_text())
    for journey in P29_JOURNEYS:
        assert any(
            re.match(rf"^#{{2,4}} Journey {journey}\b", heading)
            for heading in headings
        ), f"Journey {journey} heading missing"


def test_acceptance_criteria_ranges_are_present():
    text = _text()
    # The standing range's endpoint definitions are what
    # "AC-D1.1–AC-D95.3" names.
    assert re.search(r"\*\*AC-D1\.1\b", text)
    assert re.search(r"\*\*AC-D95\.3\b", text)

    # Presence per defect id across the whole ledger, minus the defects the
    # record itself states carry no numbered criteria.
    missing = [
        defect
        for defect in range(1, 96)
        if defect not in DEFECTS_WITHOUT_CRITERIA
        and not re.search(rf"\*\*AC-D{defect}\.\d", text)
    ]
    assert not missing, f"AC-D<defect>.<n> families missing: {missing}"

    # P29's own AC-D96.1–AC-D100.3, criterion by criterion. The range's
    # endpoint is asserted explicitly so a truncated ledger cannot pass.
    assert re.search(r"\*\*AC-D100\.3\b", text)
    for defect, suffixes in P29_CRITERIA.items():
        for suffix in suffixes:
            assert re.search(rf"\*\*AC-D{defect}\.{suffix}\b", text), (
                f"AC-D{defect}.{suffix} missing"
            )


def test_assumption_and_risk_ranges_are_present():
    text = _text()
    # Assumptions appear in two shapes: the early table (``| A<n> |``) and the
    # later bold bullets (``- **A<n> —``); both are recorded entries.
    def missing_assumptions(numbers) -> list[int]:
        return [
            n
            for n in numbers
            if not re.search(
                rf"(?m)^(?:\| A{n}(?=[ |—])|- \*\*A{n} —)", text
            )
        ]

    # Risks are recorded the same way (the standing table, plus the bold
    # bullets a phase may add); presence per id is the claim.
    def missing_risks(numbers) -> list[int]:
        return [
            n
            for n in numbers
            if not re.search(
                rf"(?m)^(?:\| R{n}(?=[ |—])|- \*\*R{n} —)", text
            )
        ]

    assert not missing_assumptions(ASSUMPTIONS), (
        f"A1–A240 ids missing: {missing_assumptions(ASSUMPTIONS)}"
    )
    assert not missing_assumptions(P29_ASSUMPTIONS), (
        f"A241–A245 ids missing: {missing_assumptions(P29_ASSUMPTIONS)}"
    )
    assert not missing_risks(RISKS), (
        f"R1–R180 ids missing: {missing_risks(RISKS)}"
    )
    assert not missing_risks(P29_RISKS), (
        f"R181–R185 ids missing: {missing_risks(P29_RISKS)}"
    )


# ── AC-P29-05-PINS / P29-T5-02 — the values, read off the modules ───────────

def test_the_bridge_envelope_and_op_sets_are_pinned():
    from ui import lwc_bridge

    assert lwc_bridge.ENVELOPE_VERSION == 1
    assert lwc_bridge.COALESCE_MS == 33
    assert lwc_bridge.CHANNELS == (
        "studies",
        "interaction",
        "alarms",
        "drawings",
        "overlays",
    )
    # The three op-kind families D99 kept untouched: the coalesced live op,
    # the whole-series replacements, and the non-series directives.
    assert lwc_bridge.LIVE_OPS == frozenset({"update_bar"})
    assert lwc_bridge._REPLACE_OPS == frozenset(
        {"set_bars", "set_volume", "clear"}
    )
    assert lwc_bridge._DIRECTIVE_OPS == frozenset(
        {"set_visible_range", "set_partial"}
    )


def test_the_store_column_sets_are_unchanged_no_migration_landed():
    from data.db import db

    studies = {
        row[1] for row in db.conn.execute("PRAGMA table_info(studies)").fetchall()
    }
    groups = {
        row[1]
        for row in db.conn.execute("PRAGMA table_info(drawing_groups)").fetchall()
    }

    assert studies == set(STUDIES_COLUMNS), (
        f"studies columns moved: {sorted(studies ^ STUDIES_COLUMNS)}"
    )
    assert groups == set(DRAWING_GROUPS_COLUMNS), (
        f"drawing_groups columns moved: {sorted(groups ^ DRAWING_GROUPS_COLUMNS)}"
    )


def test_gap_report_signature_and_unmonitored_shape_are_pinned():
    from services.alarm_monitor import AlarmMonitor

    sig = inspect.signature(AlarmMonitor.format_gap_report)
    assert list(sig.parameters) == ["gaps"]
    assert sig.parameters["gaps"].default is inspect.Parameter.empty
    assert sig.return_annotation is not inspect.Signature.empty

    # A fixed epoch pair, formatted by the one owner-approved formatter. The
    # wording and the two local clock readings are the pinned shape (the dash
    # is either the en dash the record shows or an ASCII hyphen).
    start, end = 1_700_000_000.0, 1_700_036_000.0
    report = AlarmMonitor.format_gap_report([("SYM", start, end)])
    assert re.fullmatch(
        r"SYM unmonitored \d{2}:\d{2}[–-]\d{2}:\d{2}", report
    ), f"unexpected gap report shape: {report!r}"
    for epoch in (start, end):
        assert time.strftime("%H:%M", time.localtime(epoch)) in report


def test_alarm_has_no_touch_or_armed_field():
    from data.models import Alarm

    names = {field.name for field in fields(Alarm)}
    # ``triggered`` stays the only latch; a touch is derived from ``prev``.
    assert "triggered" in names
    offenders = sorted(name for name in names if re.search(r"touch|arm", name))
    assert not offenders, f"a stored touch/armed field landed: {offenders}"


def test_evaluate_alarms_signature_is_unchanged():
    from services.alarm_service import evaluate_alarms

    sig = inspect.signature(evaluate_alarms)
    assert list(sig.parameters) == ["prev_price", "curr_price", "alarms"]
    assert all(
        param.default is inspect.Parameter.empty
        for param in sig.parameters.values()
    )
    assert sig.return_annotation is not inspect.Signature.empty


def test_update_group_accepts_exactly_the_four_mutable_names():
    from data.db import db
    from data.drawing_store import DrawingStore

    symbol = f"P29FENCE{uuid.uuid4().hex[:8]}"
    group_id = DrawingStore.create_group(symbol, "fence-group", 1, "#112233")

    # Each of the four names applies, through one statement/parameter
    # derivation (bool -> int for the two integer fields).
    DrawingStore.update_group(group_id, name="fence-renamed")
    DrawingStore.update_group(group_id, color="#445566")
    DrawingStore.update_group(group_id, visible=False)
    DrawingStore.update_group(group_id, locked=True)

    row = db.conn.execute(
        "SELECT name, color, visible, locked, seq_number FROM drawing_groups "
        "WHERE id = ?",
        (group_id,),
    ).fetchone()
    assert row[0] == "fence-renamed"
    assert row[1] == "#445566"
    assert row[2] == 0
    assert row[3] == 1
    assert row[4] == 1

    # A fifth name is rejected before any statement runs, and nothing moves.
    try:
        DrawingStore.update_group(group_id, seq_number=99)
    except ValueError:
        pass
    else:  # pragma: no cover - the assertion below is the claim
        raise AssertionError("update_group accepted a fifth field name")

    after = db.conn.execute(
        "SELECT name, color, visible, locked, seq_number FROM drawing_groups "
        "WHERE id = ?",
        (group_id,),
    ).fetchone()
    assert after == row


# ── AC-P29-05-MAP / P29-T5-03 — the map and the four new suites ─────────────

def test_the_four_new_suites_exist_on_disk():
    missing = [
        rel for rel in NEW_SUITES if not (REPO_ROOT / rel).is_file()
    ]
    assert not missing, f"P29 suites missing from the tree: {missing}"


def test_the_map_carries_the_p29_note_and_every_prior_annotation():
    text = CODEBASE_MAP.read_text(encoding="utf-8")

    # The P29 note itself: what moved, and the phase's named artefacts.
    note_start = text.index("P29 note (2026-11-20)")
    note_end = text.index("<!-- MAP-SKELETON:BEGIN -->")
    note = text[note_start:note_end]

    # What moved: the seven production files, the four new suites, and the
    # three named re-baselines.
    for rel in CHANGED_PRODUCTION:
        assert rel in note, f"P29 note does not name the moved file {rel}"
    for rel in NEW_SUITES:
        assert rel in note, f"P29 note does not name the new suite {rel}"
    for case in REBASELINED_CASES:
        assert case in note, f"P29 note does not name the re-baseline {case}"

    # Every prior annotation carries forward (P28's note is the AC's own case).
    for marker in PRIOR_NOTE_MARKERS:
        assert marker in text, f"prior annotation lost: {marker}"

    # The generated skeleton's root row is the slash-free form the lint reads.
    assert "(root)/" not in text, "the generator's (root)/ row was not repaired"
    assert re.search(r"(?m)^- (?:`\(root\)`|\(root\)) — ", text), (
        "the (root) row is missing"
    )
