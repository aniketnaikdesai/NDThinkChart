# Plan Review — NDThinkChart Stabilization Batches 3–9 (D7–D15)

## Review Status
Status: APPROVED

## Validation Summary
The Plan proposal for Batches 3–9 (D7–D15) was validated against
`docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; Batch 1 built,
Batches 2–9 D4–D15 clarified per Q15–Q30). Every clarified defect is covered by the
architecture and the phased plan; the architecture is internally consistent; each
meaningful decision carries a rationale and considered alternatives.

A previous review of this same proposal returned `BLOCKED` for requirements gap
`RG-001` (the D13/D14 Defect Register blocks and their `AC-D13.1`–`AC-D14.3`
criteria were missing from `requirements.md`). The Requirements Analyst has since
restored D13 and D14 (with decisions Q25–Q29, acceptance criteria, and edge cases)
and restored the watchlist assumptions `A17`–`A19` and risks `R15`–`R17` (D15 moved
to `A20`/`R18`). `RG-001` is now `addressed` in `docs/plan_notes.md`. The canonical
`docs/architecture.md` and `docs/plan.md` were updated from the proposal, and
`docs/plan.md` now carries `Status: READY_FOR_TASK_MANAGER`. No unresolved
architectural decision remains. Task Manager may proceed.

## Requirements Coverage
| Requirement / Journey | Architectural treatment | Phase |
|---|---|---|
| D7 / AC-D7.1–7.2 / Journey 8 | Body half-width `median_diff*0.325` (35% gap); single-bar `0.25`; D6 4px minimum kept; `xRange` unchanged | Phase 1 |
| D8 / AC-D8.1–8.3 / Journey 9 | Volume `ViewBox` linear Y, `yRange=(0, nice_max)` (`max_vol*1.1` rounded via the nice set), `0` lower bound, no negatives, price-coloured bars, `500.0K / 1.0M` ticks — **supersedes D5** | Phase 1 |
| D9 / AC-D9.1–9.2 / Journey 10 | `volume_bars.width = w*2` (same `w` as price), `y0=0`, X linked | Phase 1 |
| D10 / AC-D10.1–10.2 / Journey 11 | Checkable control at the top left of the volume panel, default visible, `setVisible()` + splitter rebalance, not persisted | Phase 3 |
| D11 / AC-D11.1–11.3 / Journey 12 | Inner-right `TextItem` labels `view_rect.right()-4`, `anchor=(1,0.5)`, colour-matched, stacking | Phase 2 |
| D12 / AC-D12.1–12.3 / Journey 13 | `Rectangle` dialog, 4 tabs, `Extend` omitted, `#1/#2 (price, bar)`, 8-row Visibility | Phase 2 |
| D13 / AC-D13.1–13.3 / Journey 14 | Watchlist draggable to `min(floor(0.50×W), W−400)`, min 150px, chart min 400px, `QSettings` persistence, clamped on restore/resize | Phase 4 |
| D14 / AC-D14.1–14.3 / Journey 15 | `cellDoubleClicked` → `symbol_input` + existing `load_chart()`; no-op on same symbol/disconnected/header | Phase 4 |
| D15 / AC-D15.1–15.3 / Journey 16 | `Horizontal line` dialog, 4 tabs, `Line` style, Text `12`, single `#1 (price)` | Phase 2 |
| Global AC (all batches) | Offscreen suite green; no live-TWS traffic | Phase 5 |
| D1–D6 (Batch 1–2, built) | Unchanged — preserved in the canonical artifacts as built | Completed — not replanned |

No in-scope requirement is weakened, reinterpreted, or removed. Out-of-scope items
(FS1–FS5, Phase 12 combo orders, paper mode) remain excluded.

## Architecture Findings
- **Completeness:** Tech stack, components, responsibilities, relationships, data
  model, integration points, non-functional approach, and risks are all present;
  each D7–D15 decision carries a rationale and considered alternatives.
- **Consistency:** D8 is explicitly recorded as superseding D5’s log decision in
  both requirements and architecture; D9 uses the post-D7 `w`; D13/D14 reuse the
  existing `load_chart()` path. No contradictions found.
- **Data model:** explicitly unchanged for D7–D11. D12/D15 read/write the existing
  `drawings` via `DrawingStore`; D13 persists an `int` width via `QSettings` (no
  `watchlist` migration) — documented with the SQLite alternative.
- **Integration:** no new IBKR calls; no new SQLite schema; only `QSettings` and the
  existing Qt signal bus are added.
- **Flagged, out of scope:** `data/db.py` defines `_init_schema` twice (second
  shadows the first) — low-severity, unchanged.

## Plan Findings
- Phases are ordered logically, state a goal, name the requirements/journeys they
  cover, and declare dependencies. Phases 1–2 share `chart_panel.py`/
  `drawing_overlay.py` and Phase 3 shares the volume plot, so the plan states they
  build serially; Phase 4 is isolated to the watchlist; Phase 5 verifies.
- Phases are at the correct abstraction — no task-level breakdown, no dependency
  graph, no per-task test specifications.
- Assumptions PA1–PA8 are plan-level, map to answered Q19–Q30, and do not redefine
  requirements.

## Required Changes
None. `RG-001` (the sole blocking item in the prior review) is resolved by the
Requirements Analyst, and no new issues were found on re-validation.

## Requirements Escalations
None outstanding. `RG-001` was raised under `ESCALATED_TO_REQUIREMENTS` in
`docs/plan_notes.md` and is now marked **addressed** (D13/D14 restored;
`A17`–`A19` and `R15`–`R17` restored; D15 moved to `A20`/`R18`). No
`ESCALATED_TO_PLAN` entry exists (`docs/debug/escalations.md` absent). No new
requirements gap requires `plan_notes.md`.

Non-blocking requirements-document notes (no action needed to proceed): the
`Per-defect criteria` intro still phrases D15 as `proposed` in one place while the
authoritative Defect Register marks D15 `clarified 2026-09-20 — Q30 correct` (AC
governs); `A9` (volume log) remains marked unconfirmed in source although Q17/D5
record it confirmed; and D5’s log decision is superseded by D8 in the same document.

## Task Manager Readiness
Yes — `READY_FOR_TASK_MANAGER`. Every technology, component boundary, interface, and
behaviour needed to build a task graph is specified: the `0.325` body factor and
4px minimum; the volume linear `0`–nice-max with price colours and tick format; the
shared `w` volume width; the top-left volume toggle and splitter handling; the
inner-right label geometry and stacking; the two 4-tab dialogs (`Extend` omitted;
single `#1 (price)` for horizontal); the watchlist 50% clamp/persistence; and the
double-click load semantics with no-ops. Task Manager can decompose all four phases
without making a new architectural decision.

## Final Decision
Status: APPROVED
