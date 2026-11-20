"""P30-T4 — the phase fence for D101–D104 (``AC-D104.3``,
``AC-P30-04-PINS``, ``AC-P30-04-MAP``).

One assertion per named artefact a later phase could quietly move. Every
value is read off the live modules or the live requirements record — nothing
is copied from prose, and no literal file/line count or phase commit hash is
pinned, so a later phase can legitimately extend the record without reddening
this fence.

The fence pins:

* the requirements record's own markers: the existing-repository sentence,
  the ``D41``–``D100`` record (presence per id in *a* heading — the record is
  mixed, as the P26–P29 fences note), P30's own ``#### D101``–``#### D104``
  entries, ``Journey 82``–``Journey 85``, the ``AC-D1.1``–``AC-D100.3`` range
  plus ``AC-D101.1``–``AC-D104.3``, ``A1``–``A245`` plus ``A246``–``A250``,
  ``R1``–``R185`` plus ``R186``–``R191``, and the Current Tech Stack section;
* Q118's answer sentence, in ``docs/requirements/open_questions.md`` and in
  the P30 requirements header;
* the phase's decisions, read off the live tree rather than prose:
  the **four-way declaration join** (the page's ``CONTROL_BUTTONS``, the ids
  the page mounts, ``LV.CONTROL_IDS`` and ``CONTROL_SPECS``, and
  ``ChartControls``' four signal names), the **latch rule** (no optimistic
  write: refusal → pre-click value, synchronous mode → pressed iff
  ``ZOOMING``, no answer → leave it; one refusal report), the
  **local-viewport / durable-state seam** (the click applies the page's own
  ``zoom`` / ``fitAndFollow`` and no consumer is added for the published
  ``zoom`` / ``reset_view`` step; only a state op drives the latch), the
  **popup dismissal** and **selection-restore-by-identity** rules, and D104's
  end state (``release_resources`` clears both channel structures;
  ``memory_bytes`` keeps its bar-log-only bucket set as the named residual,
  AR-P30-6);
* the bridge envelope contract that must not move (``ENVELOPE_VERSION``,
  ``CHANNELS``) and the one slot the restore adds;
* ``docs/codebase-map.md``'s P30 note, read-only (the map is Plan-owned — this
  suite never writes a map line).

The phase delta listing (``git diff --name-only 956f9f8`` against the phase
allowlist) is a **build artefact, not a test**: a git diff pinned inside
pytest would redden every later phase (S-P24-5 / the P24 fence precedent). It
is recorded in ``docs/build/results/P30-T4.json``, together with the phase
allowlist and any scope breach.

G7 is **owner-run and never claimed here**: no case in this suite (or in any
P30 suite) asserts a painted page, a real ``QWebEngineView`` render, a click
inside Chromium or a live-window screenshot — offscreen Chromium cannot
rasterise on this box (``tests/test_lwc_render_smoke.py``'s measured note).
"""

from __future__ import annotations

import inspect
import json
import re
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
OPEN_QUESTIONS = REPO_ROOT / "docs" / "requirements" / "open_questions.md"
CODEBASE_MAP = REPO_ROOT / "docs" / "codebase-map.md"
LWC_VIEW_SOURCE = REPO_ROOT / "ui" / "lwc_view.py"
CHART_HTML = REPO_ROOT / "chart_assets" / "lwc" / "chart.html"
INTERACTION_JS = REPO_ROOT / "chart_assets" / "lwc" / "interaction.js"
CHART_JS = REPO_ROOT / "chart_assets" / "lwc" / "chart.js"

#: The Existing Repository marker sentence (R25's standing rule).
MARKER_SENTENCE = "This is an existing repository."

#: Q118's answer, verbatim in both the question record and the P30 header.
Q118_ANSWER = "Restore them (Recommended)"

#: ``D41``–``D100`` are the standing ledger the P30 phase must not drop.
PRE_P30_DEFECTS = range(41, 101)
#: P30's own defect entries, as ``#### D101``–``#### D104`` sub-headings.
P30_DEFECTS = range(101, 105)
#: Journeys 82–85 are P30's four journeys.
P30_JOURNEYS = (82, 83, 84, 85)

#: Defects that carry no numbered acceptance criteria. ``D29``–``D35`` are
#: *intentionally unassigned* (the batch numbering jumps ``D28`` → ``D36``);
#: ``D42``/``D43`` are requirement-resolution defects whose record is the
#: resolution text plus A/R rows, with no ``AC-D<n>.<m>`` ledger.
DEFECTS_WITHOUT_CRITERIA = frozenset(range(29, 36)) | {42, 43}

#: P30's own criteria: the ``AC-D101.1``–``AC-D104.3`` ledger, per defect.
P30_CRITERIA = {
    101: (1, 2, 3, 4, 5),
    102: (1, 2),
    103: (1, 2),
    104: (1, 2, 3),
}

#: The standing A1–A245 / R1–R185 ranges plus P30's A246–A250 / R186–R191.
ASSUMPTIONS = range(1, 246)
P30_ASSUMPTIONS = range(246, 251)
RISKS = range(1, 186)
P30_RISKS = range(186, 192)

#: The six suites P30 adds (four pytest files, two node files).
NEW_SUITES = (
    "tests/test_d101_control_cluster.py",
    "tests/test_d102_d103_surface_state.py",
    "tests/test_d104_stale_claims.py",
    "tests/test_p30_fence.py",
    "chart_assets/lwc/interaction.controls.test.js",
    "chart_assets/lwc/controls.test.js",
)

#: The four control ids, in the order the page mounts and the shim accepts.
CONTROL_IDS = ("zoom-out", "zoom-in", "magnifier", "reset")

#: ``ChartControls``' four signal names, in ``CONTROL_SPECS`` order.
CONTROL_SIGNALS = ("zoom_out", "zoom_in", "magnify_toggled", "reset")

#: The page's own control declaration intents, same order.
CONTROL_INTENTS = ("zoom_out", "zoom_in", "magnify_toggle", "reset")

#: The five non-bar channels (P29/DG134's replay logs).
CHANNELS = ("studies", "interaction", "alarms", "drawings", "overlays")

#: The offline page's complete script list, in load order — no new asset, no
#: remote host, and the qrc webchannel shim in its shipped position.
PAGE_SCRIPTS = (
    "./lightweight-charts.standalone.production.js",
    "./envelope.js",
    "./interaction.js",
    "./alarms.js",
    "./primitives.js",
    "./overlays.js",
    "./studies.js",
    "./gestures.js",
    "qrc:///qtwebchannel/qwebchannel.js",
    "./chart.js",
)

#: ``memory_bytes``' bucket set — AR-P30-6's named residual is that the
#: channel logs are *not* a bucket; the release empties them instead.
MEMORY_BUCKETS = frozenset(
    {"bars", "plotted", "logical", "study_values", "drawing_items", "op_log"}
)

#: ``update_group``'s four mutable names — it may accept no fifth.
UPDATE_GROUP_FIELDS = ("name", "color", "visible", "locked")

#: A sample of the notes the map must carry forward (P30 appends, never
#: replaces) plus the P29 note the phase builds on.
PRIOR_NOTE_MARKERS = ("P6 note", "P9 note", "P25 note", "P28 note", "P29 note")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _headings(text: str) -> list[str]:
    """Every markdown heading line, at any level (1–6 ``#``)."""
    return [line for line in text.splitlines() if re.match(r"^#{1,6} \S", line)]


def _section(text: str, start_marker: str) -> str:
    """The slice from ``start_marker`` to the next same-or-higher heading."""
    start = text.index(start_marker)
    rest = text[start + len(start_marker):]
    match = re.search(r"(?m)^## ", rest)
    return rest[: match.start()] if match else rest


# ── AC-D104.3 / P30-T4-01 — the requirements record's markers ───────────────

def test_existing_repository_marker_and_current_tech_stack_are_present():
    text = _text(REQUIREMENTS)
    assert MARKER_SENTENCE in text
    assert "Current Tech Stack" in text
    # The stack section itself, not merely a mention of its name.
    assert re.search(r"(?m)^\*\*Current Tech Stack:\*\*", text)


def test_d41_to_d100_are_present_per_id_in_a_heading():
    headings = _headings(_text(REQUIREMENTS))
    missing = [
        defect
        for defect in PRE_P30_DEFECTS
        if not any(re.search(rf"\bD{defect}\b", heading) for heading in headings)
    ]
    assert not missing, f"D41–D100 ids missing from every heading: {missing}"

    # P30's own entries are the ``#### D101``–``#### D104`` sub-headings.
    for defect in P30_DEFECTS:
        assert any(
            re.match(rf"^#### D{defect}\b", heading) for heading in headings
        ), f"#### D{defect} entry missing"


def test_p30_journeys_are_present():
    headings = _headings(_text(REQUIREMENTS))
    for journey in P30_JOURNEYS:
        assert any(
            re.match(rf"^#{{2,4}} Journey {journey}\b", heading)
            for heading in headings
        ), f"Journey {journey} heading missing"


def test_acceptance_criteria_ranges_are_present():
    text = _text(REQUIREMENTS)
    # The standing range's endpoint definitions are what
    # "AC-D1.1–AC-D100.3" names.
    assert re.search(r"\*\*AC-D1\.1\b", text)
    assert re.search(r"\*\*AC-D100\.3\b", text)

    # Presence per defect id across the whole ledger, minus the defects the
    # record itself states carry no numbered criteria.
    missing = [
        defect
        for defect in range(1, 101)
        if defect not in DEFECTS_WITHOUT_CRITERIA
        and not re.search(rf"\*\*AC-D{defect}\.\d", text)
    ]
    assert not missing, f"AC-D<defect>.<n> families missing: {missing}"

    # P30's own AC-D101.1–AC-D104.3, criterion by criterion. The range's
    # endpoint is asserted explicitly so a truncated ledger cannot pass.
    assert re.search(r"\*\*AC-D104\.3\b", text)
    for defect, suffixes in P30_CRITERIA.items():
        for suffix in suffixes:
            assert re.search(rf"\*\*AC-D{defect}\.{suffix}\b", text), (
                f"AC-D{defect}.{suffix} missing"
            )


def test_assumption_and_risk_ranges_are_present():
    text = _text(REQUIREMENTS)

    # Assumptions appear in two shapes: the early table (``| A<n> |``) and
    # the later bold bullets (``- **A<n> —``); both are recorded entries.
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
        f"A1–A245 ids missing: {missing_assumptions(ASSUMPTIONS)}"
    )
    assert not missing_assumptions(P30_ASSUMPTIONS), (
        f"A246–A250 ids missing: {missing_assumptions(P30_ASSUMPTIONS)}"
    )
    assert not missing_risks(RISKS), (
        f"R1–R185 ids missing: {missing_risks(RISKS)}"
    )
    assert not missing_risks(P30_RISKS), (
        f"R186–R191 ids missing: {missing_risks(P30_RISKS)}"
    )


def test_q118_answer_is_recorded_in_the_question_and_the_phase_header():
    questions = _section(_text(OPEN_QUESTIONS), "## Q118 —")
    assert "ANSWERED 2026-11-19" in questions
    assert Q118_ANSWER in questions

    # The P30 requirements header carries the answer verbatim (the phase is
    # FINAL because of it); the delete arm is recorded as declined, not lost.
    header = _section(_text(REQUIREMENTS), "## Phase P30 —")
    assert "Q118" in header
    assert Q118_ANSWER in header
    assert "declined" in header


# ── AC-P30-04-PINS / P30-T4-02 — the values, read off the modules ───────────

def test_the_control_cluster_is_one_four_way_declaration():
    from PyQt6.QtCore import pyqtSignal

    from ui import chart_controls as CC
    from ui import lwc_view as LV

    # The page's declaration (ids, intents and the single toggle flag).
    page_source = _text(INTERACTION_JS)
    block = re.search(
        r"var CONTROL_BUTTONS = \[(.*?)\n  \];", page_source, re.S
    )
    assert block is not None, "CONTROL_BUTTONS declaration not found"
    page_ids = tuple(re.findall(r'id: "([^"]+)"', block.group(1)))
    page_intents = tuple(re.findall(r'intent: "([^"]+)"', block.group(1)))
    assert page_ids == CONTROL_IDS
    assert page_intents == CONTROL_INTENTS
    assert re.findall(r"toggle: true", block.group(1)) == ["toggle: true"], (
        "exactly the magnifier is a toggle"
    )

    # Python's one declaration and the ids the shim accepts derive from it.
    assert LV.CONTROL_IDS == CONTROL_IDS
    assert tuple(spec.id for spec in CC.CONTROL_SPECS) == LV.CONTROL_IDS
    assert tuple(spec.signal for spec in CC.CONTROL_SPECS) == CONTROL_SIGNALS
    assert tuple(spec.intent for spec in CC.CONTROL_SPECS) == CONTROL_INTENTS

    # ``ChartControls``' four signals are still carried by the declaration —
    # the module production imports, so the surface is not test-only.
    for name in CONTROL_SIGNALS:
        assert isinstance(CC.ChartControls.__dict__.get(name), pyqtSignal), (
            f"ChartControls signal {name} missing"
        )
    assert "from ui.chart_controls import" in _text(LWC_VIEW_SOURCE)


def test_the_bridge_envelope_and_control_slot_are_pinned():
    from PyQt6.QtCore import pyqtSignal

    from ui import lwc_bridge

    assert lwc_bridge.ENVELOPE_VERSION == 1
    assert lwc_bridge.CHANNELS == CHANNELS

    # ``controlPressed`` is a real Qt slot (registered on the metaobject), and
    # the view-facing signal exists; nothing is returned to the page.
    assert lwc_bridge.LwBridge.staticMetaObject.indexOfSlot(
        b"controlPressed(QString)"
    ) >= 0, "controlPressed is not a pyqtSlot"
    assert isinstance(
        lwc_bridge.LwBridge.__dict__.get("pageControlPressed"), pyqtSignal
    )
    assert list(inspect.signature(lwc_bridge.LwBridge.controlPressed).parameters) == [
        "self",
        "payload",
    ]


def test_handle_control_signature_and_three_return_shapes(qapp):
    from ui.lwc_view import LwcChartView

    sig = inspect.signature(LwcChartView.handle_control)
    assert list(sig.parameters) == ["self", "control_id", "value"]
    assert sig.parameters["value"].default is None

    view = LwcChartView(tz_offset=0.0)

    zoom = view.handle_control("zoom-in")
    assert zoom["op"] == {"op": "zoom", "step": 1}
    assert set(zoom) == {"control", "op", "mode", "refused"}

    toggle = view.handle_control("magnifier", True)
    assert toggle["op"]["op"] == "router_mode"
    assert set(toggle["op"]) == {"op", "mode", "intent", "refused"}
    assert toggle["op"]["intent"] == "enter_zoom"

    reset = view.handle_control("reset")
    assert reset["op"] == {"op": "reset_view", "mode": "IDLE"}

    # Every press is still one interaction op on the log the page replays.
    log = view._bridge._channel_logs["interaction"]
    assert [op["op"] for op in log] == ["zoom", "router_mode", "reset_view"]

    assert view.handle_control("zoom-out")["op"] == {"op": "zoom", "step": -1}


def test_a_refusal_is_reported_once_and_an_unknown_id_is_ignored(qapp):
    from ui.lwc_view import LwcChartView

    view = LwcChartView(tz_offset=0.0)
    reports: list[int] = []
    view.zoom_refused.connect(lambda: reports.append(1))

    # TR-9: the magnifier is refused while alarm placing is armed.
    view._router.enter_alarm_placing()
    before = len(view._bridge._channel_logs["interaction"])
    view._bridge.controlPressed(json.dumps({"control": "magnifier", "value": True}))

    assert len(reports) == 1, "the refusal must be reported exactly once"
    assert len(view._bridge._channel_logs["interaction"]) == before + 1
    refused_op = view._bridge._channel_logs["interaction"][-1]
    assert refused_op["op"] == "router_mode" and refused_op["refused"] is True

    # A stale id from the page is ignored — never raised across the bridge.
    after = len(view._bridge._channel_logs["interaction"])
    view._bridge.controlPressed(json.dumps({"control": "no-such-control"}))
    assert len(view._bridge._channel_logs["interaction"]) == after
    assert len(reports) == 1


def test_the_latch_follows_the_answer_never_the_click():
    source = _text(INTERACTION_JS)

    # The three-branch rule in the click handler: refusal restores the
    # pre-click value, a synchronous mode is the truth, no answer writes
    # nothing; the exported state op drives the attribute when it arrives.
    assert "function syncControlState(op)" in source
    assert "syncControlState: syncControlState" in source
    assert "no optimistic write" in source
    assert "if (result && result.refused)" in source
    assert 'btn.setAttribute("aria-pressed", value ? "false" : "true")' in source
    assert 'result.mode === "ZOOMING" ? "true" : "false"' in source
    assert "btn.setAttribute(\"aria-pressed\", op.mode === \"ZOOMING\" ? \"true\" : \"false\")" in source

    # One refusal report, by the side that knows the answer (Q-20/TR-9).
    assert source.count(
        "reportZoomRefused(spec.intent, bridge, result.mode)"
    ) == 1

    # Idempotent per container: a second mount appends nothing.
    assert "if (container.__lwControls) return container.__lwControls;" in source


def test_the_viewport_action_is_local_and_only_state_crosses_back():
    source = _text(CHART_JS)

    # The click applies this file's own viewport functions, once, and then
    # reports the press; the production shape returns nothing.
    start = source.index("function controlPressed(controlId, value)")
    end = source.index("function mountControlCluster()")
    body = source[start:end]
    assert "chart.timeScale().getVisibleLogicalRange()" in body
    assert "zoom(range" in body
    assert "fitAndFollow()" in body
    assert "target.controlPressed(JSON.stringify" in body
    assert "return undefined;" in body

    # No consumer is added for the published step ops: ``reset_view`` is
    # router state only, and a ``zoom`` op is not consumed at all (a replayed
    # log may replay state, never increments — P29/DG134, AR-P30-1).
    assert source.count('if (op.op === "reset_view")') == 1
    assert 'op.op === "zoom"' not in source
    branch_start = source.index('if (op.op === "reset_view")')
    branch_end = source.index("if (gestures", branch_start)
    branch = source[branch_start:branch_end]
    assert "zoom(" not in branch and "fitAndFollow(" not in branch

    # The durable state op is what drives the latch after a replay.
    assert source.count("li2.syncControlState(op)") == 1


def test_the_page_container_and_the_offline_script_list_are_pinned():
    html = _text(CHART_HTML)

    assert 'id="controls"' in html
    assert re.search(r'<div id="controls" role="toolbar"', html)
    assert tuple(re.findall(r'<script src="([^"]+)"', html)) == PAGE_SCRIPTS

    # R186: the chart keeps the whole viewport; the strip is an overlay.
    assert "#chart { width: 100%; height: 100%; }" in html

    # The airplane policy: vendored relative assets plus the qrc shim only.
    assert "http://" not in html and "https://" not in html


def test_create_chart_view_signature_is_unchanged():
    from ui.chart_view import create_chart_view

    sig = inspect.signature(create_chart_view)
    assert list(sig.parameters) == ["tz_offset", "editable"]
    assert sig.parameters["tz_offset"].default == 0.0
    assert sig.parameters["editable"].default is True
    assert sig.return_annotation is not inspect.Signature.empty


def test_the_watchlist_dismisses_its_popup_and_keeps_its_signatures():
    from ui.watchlist_panel import WatchlistPanel

    assert list(inspect.signature(WatchlistPanel.set_collapsed).parameters) == [
        "self",
        "collapsed",
    ]
    assert list(
        inspect.signature(WatchlistPanel.show_search_results).parameters
    ) == ["self", "samples"]
    assert list(
        inspect.signature(WatchlistPanel.clear_search_results).parameters
    ) == ["self"]

    # D102: the collapse path is the one visual owner and clears the popup.
    collapse = inspect.getsource(WatchlistPanel._apply_collapsed_visual)
    assert "if collapsed:" in collapse
    assert "self.clear_search_results()" in collapse

    # ... and a result delivered after the collapse cannot re-open it.
    show = inspect.getsource(WatchlistPanel.show_search_results)
    assert "if self._collapsed:" in show
    assert "self.clear_search_results()" in show
    assert show.index("if self._collapsed:") < show.index("self._search_popup.show()")


def test_the_group_dialog_restores_selection_by_identity():
    from ui.drawing_groups_dialog import DrawingGroupsDialog

    assert list(inspect.signature(DrawingGroupsDialog.reload).parameters) == [
        "self"
    ]
    assert list(
        inspect.signature(DrawingGroupsDialog._selected_drawing_ids).parameters
    ) == ["self"]

    # D103: ids are captured before the rebuild, and re-applied on the new
    # items by identity (never by row index).
    reload_source = inspect.getsource(DrawingGroupsDialog.reload)
    assert "selected = set(self._selected_drawing_ids())" in reload_source
    assert reload_source.index("selected = set(self._selected_drawing_ids())") < (
        reload_source.index("self.drawings_list.clear()")
    )
    assert "if drawing.id in selected:" in reload_source
    assert "item.setSelected(True)" in reload_source


def test_update_group_accepts_exactly_the_four_mutable_names():
    from data.db import db
    from data.drawing_store import DrawingStore

    symbol = f"P30FENCE{uuid.uuid4().hex[:8]}"
    group_id = DrawingStore.create_group(symbol, "fence-group", 1, "#112233")

    # Each of the four names applies (bool -> int for the two integer fields).
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
    assert set(UPDATE_GROUP_FIELDS) == {"name", "color", "visible", "locked"}


def test_release_clears_both_channel_structures_and_memory_keeps_its_residual(
    qapp,
):
    from ui.lwc_view import LwcChartView

    view = LwcChartView(tz_offset=0.0)
    bridge = view._bridge
    bridge.send_channel("studies", [{"op": "clear"}])
    bridge.send_channel("interaction", [{"op": "zoom", "step": 1}])
    bridge._channel_queue.append(("alarms", [{"op": "x"}]))

    assert any(bucket for bucket in bridge._channel_logs.values())
    assert bridge._channel_queue

    view.release_resources()

    # D104: the per-channel replay logs and their queue go; the structure
    # survives (one empty list per channel) because a later press logs again.
    assert tuple(bridge._channel_logs) == CHANNELS
    assert all(bucket == [] for bucket in bridge._channel_logs.values())
    assert bridge._channel_queue == []

    # Idempotent — a second release is a no-op.
    view.release_resources()
    assert all(bucket == [] for bucket in bridge._channel_logs.values())
    assert bridge._channel_queue == []

    # AR-P30-6, named residual: ``memory_bytes`` still accounts the bar log
    # only; the channel logs are reported empty after the release, not counted.
    buckets = view.memory_bytes()["buckets"]
    assert set(buckets) == MEMORY_BUCKETS
    assert not any("channel" in name for name in buckets)


# ── AC-P30-04-MAP / P30-T4-03 — the map and the six new suites ──────────────

def test_the_six_new_suites_exist_on_disk():
    missing = [rel for rel in NEW_SUITES if not (REPO_ROOT / rel).is_file()]
    assert not missing, f"P30 suites missing from the tree: {missing}"


def test_the_map_carries_the_p30_note_and_every_prior_annotation():
    text = _text(CODEBASE_MAP)

    # Read-only: this test locates the P30 note and never writes a map line.
    note_start = text.index("P30 note (2026-11-20)")
    note_end = text.index("<!-- MAP-SKELETON:BEGIN -->")
    note = text[note_start:note_end]

    for rel in NEW_SUITES:
        # The note names the four pytest suites by module stem and the two
        # node suites by filename; either spelling identifies the suite.
        name = rel.rsplit("/", 1)[-1]
        stem = name[:-3] if name.endswith(".py") else name
        assert name in note or stem in note, (
            f"P30 note does not name the new suite {rel}"
        )

    # Zero harness change, stated where the page suites are recorded.
    assert "no existing suite is edited" in note
    assert "chart.test.js" in note and "harness is untouched" in note

    # G7's boundary is part of the record, not an implied claim.
    assert "G7 is owner-run and not claimed" in note

    # Every prior annotation carries forward (a refresh appends, never
    # replaces), and the skeleton's root row stays in the slash-free form.
    for marker in PRIOR_NOTE_MARKERS:
        assert marker in text, f"prior annotation lost: {marker}"
    assert "(root)/" not in text
