# Plan Review — NDThinkChart Batch 15 (D21: 13 UI defects/issues)

## Review Status
Status: APPROVED

## Validation Summary
This is validation **pass 2 (retry 1 of 3)** for the **D21 increment**. It re-validates
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`) and `docs/architecture_proposal.md`
against `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-06 with D21 /
`VIS-D21` / Journeys 22–26 / `AC-D21.*` / A41–A47 / R37–R44 / DG31–DG38, B9–B13 answered). No
`Status: ESCALATED_TO_PLAN` entry exists in `docs/code_review/escalations.md` (the only occurrence of
that string is the routing legend), so this is a normal forward validation cycle, not an escalation
round.

**Scope.** Batch 15 (**D21**, sub-defects D21.1–D21.13) plus the shared visual convention
`VIS-D21` (`VIS-D21.1` diagonal strike-through, `VIS-D21.2` active-button highlight), planned as an
*incremental* change-set on top of the **built, green D1–D20** baseline (commit `04397d9`, 585
tests). D1–D20 are frozen and are **not** re-planned. Existing-repo mode (the marker sentence
`This is an existing repository.` and the Current Tech Stack are present in `requirements.md`;
PyQt6 + pyqtgraph is a hard constraint).

**Prior cycle.** Validation pass 1 returned `CHANGES_REQUIRED` with three items: **RC-D21-1**
(blocking — the D21.4 collapse predicate was wrong for the ordinary overnight/weekend/holiday gap),
**RC-D21-2** (the D21.13 horizontal-collapse mechanism was under-specified), and **RC-D21-3** (the
D21.10 preview line was not scoped to the chart-click path). The Plan agent revised the proposal;
this pass validates the revision against the repository (the repository is authoritative).

**Verdict — all three prior items are genuinely resolved; the proposal now passes.** The
revised proposal is **complete, internally consistent, and implementable on the existing components**.
Requirements coverage is complete, every architectural decision is labelled and justified, the
`VIS-D21` primitives are defined once and referenced, the volume-axis supersessions are recorded, and
Task Manager can decompose all six phases without making a new architectural decision. The canonical
D21 artifacts are written this cycle and `docs/plan.md` is marked `READY_FOR_TASK_MANAGER`.

**Independent verification (2026-10-06; the Validator inspected the current source and re-measured
the collapse predicate with the real calendar helper rather than trusting the proposal's prose):**

- **RC-D21-1 — collapse predicate (VERIFIED RESOLVED).** The proposal now defines a gap between
  consecutive bars `a < b` as collapsed **iff**
  `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty, with
  `bar_period = TIMEFRAME_SECONDS[timeframe]` and a bar at `ts` covering `[ts, ts + bar_period)`.
  Source confirmed: `services/market_calendar.py::session_windows` (`:195–216`, one clipped window
  per trading day, `clipped_end > clipped_start`), `data/bar_aggregator.py::TIMEFRAME_SECONDS`
  (`:6–14`), `_period_start` (`:30–32`), and `Bar.ts = period_start` (`:93`) — so the last RTH bar is
  at 15:55 (ext 19:55), whose coverage ends exactly at the 16:00 (ext 20:00) close. The Validator
  **re-ran a read-only probe** with the real helper (`bar_period = 300`):

  | Boundary case | `session_windows(a+300, b, ext)` | Verdict | Raw `session_windows(a, b, ext)` |
  |---|---|---|---|
  | RTH overnight `Fri 15:55 → Mon 09:30` | empty | **collapse** | non-empty → old predicate wrongly kept |
  | Ext overnight `Fri 19:55 → Mon 04:00` | empty | **collapse** | non-empty → old predicate wrongly kept |
  | Weekend `Sat 16:00 → Mon 09:30` | empty | **collapse** | empty |
  | Holiday `Fri 15:55 → Tue 09:30` (Labor Day Mon) | empty | **collapse** | non-empty → old predicate wrongly kept |
  | Within-session hole `11:00 → 13:00` | non-empty | **keep** | non-empty |
  | Missing full session `Mon close → Wed open` (Tue absent) | non-empty | **keep** | non-empty |
  | Partial half-day afternoon hole `11:00 → 13:30` | non-empty | **keep** | non-empty |
  | Adjacent bars `11:00 → 11:05` | empty | collapse (no-op) | non-empty |

  The coverage-adjusted predicate collapses every ordinary between-session gap (the exact case the
  previous predicate failed) while keeping within-session holes and missing trading sessions visible
  (`AC-D21.4.4`). Phase 6's exit condition now names all five boundary cases, and PA-D21-9 records the
  rule. **Resolved.**
- **RC-D21-2 — D21.13 horizontal collapse (VERIFIED RESOLVED).** Source confirmed:
  `ui/main_window.py:323` pins `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH = 200)`, and the
  hidden branch of `_apply_dock_widths` (`:1189–1194`) resizes **only** the watchlist dock via
  `_resize_docks_guarded` (`:1201–1224`). The proposal now states the required mechanism explicitly
  (S12, PA-D21-5, Phase 4, Non-Functional): the collapsed state (a) **relaxes the dock's minimum
  width** to `RIGHT_DOCK_COLLAPSED_MIN_WIDTH` (the two buttons' `sizeHint()` + margins, replacing the
  pinned 200px) and (b) **explicitly resizes** the dock to that strip
  (`_resize_docks_guarded([right_dock], [collapsed_width])`), while **keeping** the "treat collapsed
  as hidden for the cross-clamp" rule so the chart minimum holds; showing a panel restores the 200px
  minimum and the normal B3 cross-clamp. `AC-D21.13.3` is now achievable. **Resolved.**
- **RC-D21-3 — D21.10 preview-line path scope (VERIFIED RESOLVED).** Source confirmed the two open
  paths: `_on_alarm_create_requested(price)` (`:1502–1509`, chart-click, price from the click) and
  `_open_alarm_dialog()` (`:980–987`, Alarms button, pre-fills `self._last_chart_price`). The
  proposal now states the preview line is created **only** on the chart-click path
  (`_on_alarm_create_requested`) with an add-on-open/remove-on-close lifecycle tied to that path, and
  that the Alarms-button path (`_open_alarm_dialog`) creates **no** preview line (S14, PA-D21-8,
  Phase 5, exit condition). **Resolved.**
- **Rest of the proposal unchanged and still sound.** The volume-axis supersession (D21.2 →
  `1.10 × max visible`, superseding D8's nice-max and ESC-007's only-widen), the `VIS-D21` primitives,
  the watchlist field-identity column model + `QSettings` persistence, the alarm-edit semantics
  (`AlarmStore.update` leaves `active/triggered/triggered_at` untouched), and the six-phase ordering
  are as reviewed in pass 1 and remain coherent. D1–D20 are frozen and unaffected.
- **Graphify.** `graphify-out/graph.json` exists (2416 nodes, refreshed 2026-10-06); the volume,
  watchlist, dock, toolbar, alarm and session symbols resolve (`graphify query` returned the
  `session_windows` / `session_bands` / `_period_start` / `market_calendar.py` / `chart_panel.py`
  nodes). Every Codebase-Summary claim the Validator sampled was confirmed against the current source.

## Requirements Coverage
| Requirement / journey / AC | Proposal treatment | Verdict |
|---|---|---|
| D21.1 / `AC-D21.1.1` — volume Y min never below 0 | Phase 1 (`setLimits(yMin=0)`) | Covered |
| D21.2 / `AC-D21.2.1` — `[0, 1.10 × max visible]` on any visible-x change; supersedes D8 nice-max + ESC-007 only-widen | Phase 1 (recompute on `sigXRangeChanged`; `_nice_volume_max` kept for the all-zero floor); supersession recorded on `AC-D21.2.1` | Covered (lockstep volume tests named) |
| D21.3 / `AC-D21.3.1` — `Ext Hours` ↔ `RTH` label | Phase 2 | Covered |
| D21.4 / `AC-D21.4.1`–`AC-D21.4.4` — collapse between-session non-trading time; `1 day` no-op; RTH; D16 unchanged | Phase 6 (`services/time_collapse_service.py`, coverage-adjusted predicate) | **Covered (RC-D21-1 resolved; Validator probe reproduced all boundary cases)** |
| D21.5 / `AC-D21.5.1`–`AC-D21.5.4` — column add/remove/rearrange, Symbol kept, persisted | Phase 3 (field-key model + `QSettings watchlist/columns`) | Covered |
| D21.6 / `AC-D21.6.1` — volume pane ≥ 360px, price pane ~200px min | Phase 1 (`VOLUME_PANE_MAX_HEIGHT = 480`, `PRICE_PANE_MIN_HEIGHT = 200`) | Covered |
| D21.7 / `AC-D21.7.1` — persistent active highlight | Phase 2 (`VIS-D21.2`) | Covered |
| D21.8 / `AC-D21.8.1`–`AC-D21.8.2` — Alarm-Mode highlight + persistent message | Phase 2 | Covered |
| D21.9 / `AC-D21.9.1`–`AC-D21.9.4` — row Edit, widened Note, edit dialog, triggered alarm keeps state | Phase 5 (`AlarmStore.update` as-is) | Covered |
| D21.10 / `AC-D21.10.1`–`AC-D21.10.5` — clicked price, preview line lifecycle, condition default | Phase 5 (preview line chart-click path only) | **Covered (RC-D21-3 resolved)** |
| D21.11 / `AC-D21.11.1`–`AC-D21.11.3` — single "Watchlist" label, toggle survives collapse, strike | Phase 3 (header strip as title-bar widget) | Covered |
| D21.12 / `AC-D21.12.1` — Volume button struck when hidden | Phase 2 | Covered |
| D21.13 / `AC-D21.13.1`–`AC-D21.13.4` — Active Trader / Account Summary toggles + collapse geometry | Phase 4 (minimum relaxed + explicit dock resize to the button strip) | **Covered (RC-D21-2 resolved)** |
| `VIS-D21.1` — diagonal strike-through | Phase 2 primitive (`DiagonalStrikeButton`), consumed by Phases 3/4 | Covered (defined once, referenced) |
| `VIS-D21.2` — active-button highlight | Phase 2 primitive (stylesheet + `set_button_active`) | Covered (defined once, referenced) |
| Journeys 22–26 | Phases 1–6 | Covered |
| A41–A47, R37–R44, DG31–DG38 | Phases 1–6 | Covered (DG37/DG38 mechanisms chosen) |
| D1–D20 | Frozen, re-affirmed; not re-planned | Covered |

The two recorded supersessions (D21.2 → D8's nice-max / ESC-007's only-widen; D21.4 → the display
part of `AC-D16.3`) are recorded on the requirements (`AC-D21.2.1`, `AC-D16.3`, D21.4) and are
**not** silent changes.

## Architecture Findings
- **Complete.** Tech stack (unchanged, with `[new]`/`[new/changed]` additions labelled and
  justified), components + responsibilities, relationships, data model, integrations, non-functional
  approach (performance/correctness/high-DPI/security), and risks are all present, each with rationale
  in the Tech Stack Decisions table (S1–S18).
- **Volume-axis supersession coherent.** D21.2's `[0, 1.10 × max visible]` on any visible-x-range
  change is stated consistently (S4/S5, Phase 1, PA-D21-2, Non-Functional) and supersedes D8's
  nice-max and ESC-007's only-widen while preserving ESC-007's core intent (recompute on bar updates)
  and D8's linear/no-negatives/min-0/price-colour behaviour. The lockstep test files are named and a
  new disjoint `tests/test_volume_d21.py` is proposed.
- **`VIS-D21` defined once and referenced.** `[new] ui/visual_conventions.py` owns
  `DiagonalStrikeButton` (`VIS-D21.1`) and the `VIS-D21.2` stylesheet + `set_button_active`;
  D21.7/D21.8/D21.11/D21.12/D21.13 consume it rather than re-implementing the conventions.
- **D21.13 geometry is implementable on the existing single right-dock region** — the horizontal
  collapse mechanism is now explicit (RC-D21-2 resolved).
- **D19/D20 toolbar constraints unaffected.** D21.3/D21.7/D21.8 change only the toolbar's text /
  styling / status message inside the existing scroll wrapper; the wrapper's derived height, the
  reserved scrollbar lane, `setWidgetResizable(False)`, and the central-widget minimum-width benefit
  are untouched.
- **Alarm semantics correct.** `AlarmStore.update` edits only the passed fields, so D21.9's
  "triggered alarm keeps its state" holds without a new store method.
- **D21.4 collapse consumers named.** `ChartPanel` stores the map; `DrawingOverlay._bar_ts`,
  `SessionOverlay` bands, the date axis/crosshair and the alarm label x are mapped/inverse-mapped
  through it; `Bar.ts` (the SQLite key) is never mutated. The D21.2 visible-max scan reconciliation
  with display-x is explicitly sequenced into Phase 6.

## Plan Findings
- **Phases are correctly structured.** Six ordered milestone phases (volume axis/pane; `VIS-D21`
  primitives + toolbar; watchlist; right dock; alarm; time collapse), each with a goal, covered
  requirements/journeys, explicit dependencies, and an exit condition. They are coarse enough for
  Task Manager to decompose and contain no task-level dependency graph or per-task test spec.
- **Ordering is logical.** Phase 6 (the x-model change) is sequenced last and explicitly reconciles
  the D21.2 scan with the collapse map; the shared-file serialisation points (`ui/chart_panel.py`,
  `ui/main_window.py`) are called out in the `touches_files` notes and the parallel-sequencing table.
- **Assumptions are plan-level.** PA-D21-1…PA-D21-13 are implementation details; PA-D21-9 now states
  the **correct** coverage-adjusted collapse rule (RC-D21-1 resolved) and PA-D21-5/PA-D21-8 state the
  resolved collapse mechanism and preview-line scope.
- **No scope drift.** D21 is the new clarified batch; D1–D20 are frozen. Nothing is added or removed,
  and no requirement is narrowed or reinterpreted.
- **No Task Manager-level task breakdown** is present.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + `ibapi` terminal; `requirements.md` contains the literal
marker sentence `This is an existing repository.` and a Current Tech Stack. Checks:

- **Codebase Summary present and substantive — PASS.** `architecture_proposal.md` carries a
  *Codebase Summary (existing repository — D21 surface)* that inventories the volume pane/axis
  (methods + line ranges), the toolbar/D19–D20 wrapper, the watchlist, the single right-dock region +
  `dock_layout`/`_apply_dock_widths`, the alarm dialog/overlay/store, the session/x-axis surfaces, the
  bar-timestamp period-start fact, the data models/tables, the integrations, and the relevant existing
  tests. Every claim the Validator sampled was confirmed against the current source.
- **Existing stack respected — PASS.** Tech Stack Decisions (S1/S2/S18) keep Python 3.11+ / PyQt6 /
  pyqtgraph / `ibapi` / numpy / SQLite / pytest-qt **unchanged** (`[existing]`), listed before the
  D21 `[new]`/`[new/changed]` rows; "no stack change, no new dependency" is stated. Nothing existing
  is replaced or deprecated.
- **Labels present — PASS.** System Components, Data Model, and Integration Points each mark every
  item `[existing]`, `[new]`, or `[new/changed]`.
- **Additive-only — PASS.** Existing components are extended, not redesigned beyond what a
  requirement calls for; new/changed work is separated from what already exists.
- **Codebase Summary consistent with the proposal — PASS.** Every component the proposal treats as
  `[existing]` (chart panel, toolbar/wrapper, watchlist, right dock, alarm dialog/overlay/store,
  session service/overlay, `dock_layout`, `market_calendar`, `drawing_overlay`, bar aggregator) appears
  in the Codebase Summary and was confirmed in source.
- **Graphify stated and validated — PASS.** The proposal states graphify was used for discovery and
  every claim validated against source; the graph exists and the claims check out.

## Required Changes
None. RC-D21-1, RC-D21-2 and RC-D21-3 are all resolved and independently verified. No new required
change is raised by this pass.

## Requirements Escalations
None. Every D21 sub-defect and `VIS-D21` is satisfiable as written; no issue is a requirement defect.
No `ESCALATED_TO_REQUIREMENTS` entry is added to `docs/plan_notes.md`. (The historical `plan_notes.md`
entries RG-001/RG-002/RG-003 and FI-D16-1/FI-D16-2 remain resolved/addressed and are not reopened.)

## Task Manager Readiness
**Yes.** Task Manager can create a valid task graph from `docs/architecture.md` (D21 increment) and
`docs/plan.md` (D21) without making a new architectural decision: every required technology is fixed,
component boundaries are explicit, the two `[new]` modules are named with defined contracts, the
collapse predicate is fully specified and empirically verified, the right-dock collapse mechanism is
explicit, the preview-line path scope is explicit, the data model and persistence stores are decided,
and each phase carries its covered requirements and dependencies.

## Final Decision
Status: APPROVED
