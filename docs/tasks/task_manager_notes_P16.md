# Task Manager notes — P16 (D55 docs-only consolidation)

## Decomposition record

- 9 doc tasks across the plan's 4 waves: P16-T1 (inventory + cross-reference map) and
  P16-T2 (fact sheet) parallel with no dependencies; P16-T3 (navigation/labels) deps
  T1+T2; P16-T4 (guide correction) dep T2 only, per the plan's explicit gating
  ("fact sheet fixes the connection truth first"); P16-T5 (P6 six-file reconciliation),
  P16-T6 (P7 cap addendum), P16-T7 (navigation blocks) deps T1+T2; P16-T8
  (ledger + deletions) deps T1..T7; P16-T9 (final review + history guard) dep T8.
- Sizes S/M only per the phase scope. No step-fit exception: the broadest task (T5,
  six files) is a coordinated prose pass with one grep suite, well under ~20 steps.
- No GRAPHIFY tracing: the surface is named doc files, not code relationships
  (`needs_graphify: false` everywhere).

## Deliberate deviations from the wave text (recorded, not silent)

1. **Archive moves execute in P16-T8, not P16-T7.** The plan lists archive moves under
   W3 deliverables but gates every move on the link audit and every deletion on the
   ledger; T7 therefore records the pre-move audit and the candidate list with zero
   moves, and T8 (which owns the ledger) executes any move. The plan's own W4
   deliverables list "archive moves (if any)", so this stays inside the plan.
2. **New-record locations chosen by Task Manager** (the plan left them open):
   `docs/D55_inventory.md` (T1), `docs/D55_fact_sheet.md` (T2),
   `docs/D55_disposition_ledger.md` (T8), `docs/D55_final_review.md` (T9). These do
   not exist at graph time, so they appear in `touches_files` but not in `read_files`
   (pure-output files; the expected `check_tasks.py` warnings apply).
3. **Q84 comment + Q86 dev_docs/ deletion are verified, never redone** (AP-P16-1):
   T8 re-runs the reference check instead of re-editing or re-deleting.

## Flag for Requirements Analyst (no escalation status; user relays)

- **P16-T7 excludes the requirements.md baseline block.** AC-D55.7 asks for a short
  current-baseline block "atop each canonical file", which includes
  `docs/requirements/requirements.md` — but that tree is Analyst-owned and Task
  Manager assigns no edits there. T7 covers `docs/architecture.md` + `docs/plan.md`
  only and asserts `docs/requirements/` untouched. If the requirements.md block is
  wanted in-batch, the Analyst adds it; otherwise the AC's "each canonical file"
  reads as each file this batch may edit.

## No open items

- ESC-097 + ESC-098 were `TASK_MANAGER`-routed and open as of 2026-11-04; both are
  translated into this graph below (rework record section).
- No approved `feature_suggestions.md` item falls in D55 scope (no approved entry
  found; FS17/FS18 are proposals, not approved scope).
- Q84–Q87 are all answered; the only explicitly-open item (50-vs-100, A154/DG102)
  has its specified handling inside P16-T6 (reconcile with evidence, else record
  open — never silently choose).
- D1–P15 are not reopened: every task carries the addenda-only rule via its
  byte-identical approval-record tests, and no task touches source, tests,
  packaging, or schemas.

## Build scheduling note

- T1 and T2 are wave-1 parallel. T5/T6/T7 share `docs/architecture.md`
  (`touches_files` overlap) so Build must serialize them despite no DEPENDS_ON edge
  between them — the overlap is intentional (distinct addendum sections, one file).
  Same for T3/T5 on `docs/codebase-map.md` (index pass vs LWC-only correction).

## Rework record — ESC-097 + ESC-098 (2026-11-04, owner-approved Code Reviewer rework)

- **ESC-097 (P16-T4 test_command).** One-word fix in place: dropped the leading
  `test ` so the command is runnable shell (`! grep -q 'paper (DU)' … && echo
  T4_OK`, verified by the Reviewer to print T4_OK on the live tree). T4 substance,
  scope, and deps (`P16-T2`; still gates T8→T9) are untouched. T4 status reset
  `blocked` → `not_started` for the re-run; its fresh result cures PRE-015
  (malformed result `task_id`) downstream — PRE-015 itself is BUILD-routed and is
  not touched here.
- **ESC-098 (history-hash guards).** Root cause is Analyst-owned P16 requirements
  additions (Batch 30 D55 banner + A/R rows) reddening the over-broad whole-head
  `PRE_D53_SHA256` hash shared by `test_t34_history_markers_intact`
  (tests/test_p14_cache_guard.py) and `test_t33_history_markers_intact`
  (tests/test_p15_surfacing.py) — not any P16 build task. Fix is kept inside task
  definitions Task Manager owns: explicit BUILD rework scope added to P16-T9 (the
  history-guard owner — AC2/T92 already certifies D41–D54/marker/stack), never a
  silent footprint expansion. New AC3 is invariant-shaped (both guards pass with
  every protected-content assertion intact — D41–D52 headings, marker sentence,
  Tech Stack, reversal/supersession markers; no assertion removed or weakened)
  with matching T93; `touches_files`/`read_files` explicitly name both guard
  files with edit-site pinning; the T9 `test_command` docs-only gate now exempts
  exactly those two test paths and additionally runs both guards. Reviewer
  preference (narrow the hashed region; re-pin only as fallback) is stated in the
  task description. No P16 task claims `docs/requirements/*` (Analyst-owned); the
  9-task structure, all other tasks, and all deps are unchanged.
- **Size reason (step-fit rule):** P16-T9 S → M. The ESC-098 scope adds two edited
  test files plus the narrow-vs-repin judgment to the final-review doc, making it
  multi-file with design judgment — M, no exception needed (well under ~32).
