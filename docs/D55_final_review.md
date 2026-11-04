# D55 Final Consistency Review (AC-D55.9, docs-only) + History Guard (AC-D55.10) — P16-T9

> **Date:** 2026-11-04. **Scope:** consolidated P16 working tree (W1–W4 outputs as observed).
> **Method:** plan completion checklist 1:1 (plan `docs/documentation_consolidation_plan.md` §9),
> stale-claim grep classes + R113 paraphrase sampling, link/filename/phase-ID/commit/status checks,
> guide-vs-source-vs-plan cross-checks, historical labelling, addendum discipline.
> **No product test suite run is a gate** (AP-P16-2); verification is docs-only review.
> Includes the ESC-098 BUILD rework: history-hash guard repair in
> `tests/test_p14_cache_guard.py` / `tests/test_p15_surfacing.py`.

## Verdict

- **AC-D55.9 (docs-only consistency review): PASS** — every checklist item ticks 1:1 with
  recorded evidence below. One recorded exception: the worktree's only non-docs delta is the
  pre-landed Q84 comment-only line in `services/sound_service.py` (tracked micro-task change,
  verified-not-reedited per AP-P16-1); the task test-command's docs-only echo therefore reads
  `T9_FAIL_NON_DOCS`, honestly recorded in §5, not a review failure.
- **AC-D55.10 (history guard): PASS** — `### D41`–`### D54` with reversals, the Existing
  Repository marker sentence, and the Current Tech Stack are byte-identical pre-P16 except by
  no change at all (requirements diff is 85 insertions / **0 deletions**; the narrowed guard
  span is byte-identical HEAD-vs-worktree; both history-markers-intact guards pass).
- **ESC-098 rework (AC3): PASS** — both guards pass alongside the legitimate P16 requirements
  additions; every protected-content assertion is still present and asserting (verified by grep,
  §6). `requirements.md` itself was never touched by this task (Analyst-owned).

## 1. Completion checklist, 1:1 with the plan (§9)

| # | Plan item | Result + evidence |
|---|---|---|
| 1 | `docs/README.md` identifies canonical sources and active phase | PASS — one-sentence status + 7-row authority table + current-work/historical/ownership blocks verified in tree (authority: requirements / architecture / plan / phase-changelog / current review + escalations / `usage.md` / ATTRIBUTION). |
| 2 | User instructions match source, configuration, supported account modes | PASS — `usage.md:16,35,38,77,84,107,114,233,261` + `USAGE.txt:36,40` state live-only 7496 throughout; source `config/settings.py:4-5,8,11,14-23` (`IBKR_PORT=7496`, `LIVE_PORT=7496` fail-fast, "trades live only"); factory `ui/chart_view.py:121-124` returns `LwcChartView` unconditionally. `paper` appears in guides only to deny paper logins. |
| 3 | P6-T13 consistently recorded as removed, waiver/live-session status accurate | PASS — as-built T13 + waived-not-satisfied in `docs/architecture.md:5788` (+ P16 index `:7445,7480`), `docs/codebase-map.md:9-19,104-113`, `docs/lwc_parity_matrix.md` P6-T13 as-built section, `docs/code_review/review_log_P6.md:104` dated addendum (2026-10-28, nothing above rewritten), `docs/phase-changelog.md:415`, `docs/CHANGELOG.md:10`, gate file present. |
| 4 | P6 parity not conflated with a defect-free live session | PASS — matrix "Waived, not satisfied, preserved" block; phase-changelog `:423` notes ESC-070 still owed and the clean session never run; no row claims live validation. |
| 5 | P7 per-load cap explicitly a maximum, never forced chunking/spend-target | PASS — "maximum, never a target" addenda in `docs/plan.md` (2), `docs/architecture.md` (3), `docs/plan_review_P7.md` (1), `docs/tasks/task_manager_notes_P7.md` (1); cap-as-target grep (`cap as (a\|the )?target\|spend the cap\|consume the cap\|forced chunking`) returns zero. |
| 6 | 50/100 budget discrepancy resolved or explicitly left open with owner/source | PASS — left explicitly open per A154: `design_gaps.md:1557` `## DG102 … unreconciled (left explicitly open)`; no prose value chosen. |
| 7 | Spike claims distinguish stub checks from real v5.2.1 runtime evidence | PASS — stub labelling in `docs/lwc_spike_results.md`, `spikes/lwc/README.md:36-37` ("real v5-shaped calls" of the stub harness, not runtime proof); legacy API names (`addCandlestickSeries`, `applyOptions`, …) occur only in stub-evidence files + dated P6 wave sections; `lwc_parity_matrix.md:558` occurrence is inside the dated P6-07 wave record with gate evidence cited, not a current runtime claim. |
| 8 | `docs/CHANGELOG.md` and `docs/phase-changelog.md` have distinct roles or one is a pointer | PASS — CHANGELOG is a short index pointing at phase-changelog (`:10` P6 pointer); phase-changelog carries the dated as-built entries. |
| 9 | Proposals, memory, reviews, old phase docs marked non-normative, never silently deleted | PASS — README historical block; `docs/architecture_proposal.md:16` superseded-whole banner; codebase-map historical note (2026-10-26 plan-time wording preserved as lineage); review_log_P6 original text untouched above the `:104` addendum. |
| 10 | Every moved/deleted path passes reference checks | PASS — `dev_docs/` absent from tree; code-tree grep for `dev_docs` in `services/ tests/ packaging/ main.py` returns zero (ledger row 1); Q87 four targets (`review_log.md`, `task_manager_notes.md`, `precheck.json`, `precheck.md`) absent; successors verified present (`review_log_P6.md`, `task_manager_notes_P7.md`, per-phase suffixed chains, `review_log_P16.md`/`plan_review_P16.md`/`task_manager_notes_P16.md`); `docs/archive/` correctly absent (nothing qualified for archive; deletions per Q86/Q87 are no-archive). |
| 11 | Pre-existing user edits and untracked files preserved unless explicitly dispositioned | PASS — worktree diff attribution in §5; requirements diff purely additive (85+/0−); no reset/overwrite of the W1–W3 records or the untracked P16 files. |
| 12 | No product source/test files changed as part of this documentation-only integration | PASS with one recorded pre-landed exception — §5: only `services/sound_service.py` (Q84 comment-only line, tracked micro-task change, AP-P16-1: verify, never re-edit) plus the two guard files this task explicitly authorizes. |

## 2. Stale-claim grep record (C1–C7 + R113 paraphrase sampling)

- **C1 pyqtgraph-default:** all hits are (a) dated plan-time/wave records (`architecture.md` Phase P6 plan text `:5663-5757`, parity-matrix P6-02…P6-12 wave sections, `plan.md` P6 waves, `task_manager_notes_P6.md`), (b) bannered history (codebase-map historical note, README line 40, Q-52 baseline), or (c) corrected guides stating removal (`usage.md:92,248`, `USAGE.txt:28`). No current-state sentence claims pyqtgraph present/default/selectable.
- **C2 dual-engine / NDT_CHART_ENGINE opt-in:** current claims all read ignored/no-longer-selects (`usage.md:80,96`, `USAGE.txt:49`, codebase-map `:11,107`, matrix `:55`, architecture `:7478`, fact sheet F1). Residual mentions are plan-time (`plan.md:3275` AP-P6-1, requirements D47 ACs — Analyst-owned history under guard).
- **C3 T13 undispatched:** zero hits for `undispatched|T13 not|not dispatched|T13 pending|T13 still` outside task-graph descriptions of this very check and the README scope sentence (pre-T13 review scope, correctly historical).
- **C4 owed live session:** every live-session mention near the gate reads waived-not-satisfied (matrix, phase-changelog, map, task_manager_notes_P6 `:57`, orchestrator_state). Remaining "live session" hits are unrelated product behavior (D24/D27/D28 ACs) or live defect reports — sampled, none claims a satisfied/owed gate.
- **C5 parity-complete:** zero live claims; hits are plan instructions, matrix gate wording ("full parity" as a gate leg), and memory findings.
- **C6 paper-on-7496 / legacy account-port:** `grep -n "7496\|paper" usage.md USAGE.txt` → ports all live-only; `paper` only in "paper-trading logins are not supported". Stale supported-paper path: zero.
- **C7 spike API names as runtime evidence:** confined to stub-evidence files (`spikes/lwc/*`, `lwc_spike_results.md` Evidence lines, `spikes/lwc/README.md`) and dated wave records. No current doc presents them as v5.2.1 runtime proof.
- **R113 paraphrase sampling:** `default chart|chart engine of choice|engine of choice|proven against|fully working chart|production-ready chart` → zero hits. Manual samples: "default engine" occurs only in the matrix P6-12/retired-coverage history and AR-P16-4's own warning; "engine of choice"/"proven" phrasing absent.

## 3. Link / filename / phase-ID / commit / status checks

- Files referenced exist: `docs/build/gate_P6_T13.md`, `docs/D55_inventory.md`, `docs/D55_fact_sheet.md`, `docs/D55_disposition_ledger.md`, `usage.md`, `USAGE.txt`, `chart_assets/lwc/ATTRIBUTION.md` — all present.
- Commits exist: `6e35b27` (P6-T13 removal), `7cba534` (P7), `09761fb` (P8) — `git cat-file -t` returns `commit` for all three.
- Phase IDs: `### D41`–`### D54` headings present (proven by the passing guards, which assert each heading); `## Phase P15` / `## Phase P16` sections present.
- Status labels: `Status: READY_FOR_PLAN` maintained in requirements tail; review_log_P16 present for the W4 record chain.

## 4. Guide-vs-source-vs-plan cross-checks

| Claim | Guide | Source | Agreement |
|---|---|---|---|
| Engine LWC-only; env key ignored | `usage.md:80,92,96`, `USAGE.txt:28,49` | `ui/chart_view.py:121-124` always returns `LwcChartView` | YES |
| Port 7496 live-only, fail-fast | `usage.md:16,77,107,261` | `config/settings.py:4-23` (`IBKR_PORT`/`LIVE_PORT` + `check_live_port`) | YES |
| One full guide + one pointer | `usage.md` canonical, `USAGE.txt` short pointer | plan P16-W2 | YES |
| Cap maximum + examples | guides n/a (plan-level) | plan/architecture/P7-review/P7-notes addenda (§1 row 5) | YES |

## 5. Diff record (docs-only paths + preserved edits)

`git diff --stat` (20 files, 1534 insertions, 6762 deletions): deletions are exactly the
approved Q86 (`dev_docs/` 5 files) and Q87 (`review_log.md` 3986 lines, `task_manager_notes.md`
2514 lines) removals plus pipeline JSON churn (`task-graph.json`, `execution_graph.json`,
`escalations.json` — owned by Task Manager/`build_wave.py`/Reviewer machinery, observed not edited
here). Content edits are docs under `docs/`, `usage.md`, `USAGE.txt`, plus:

- `services/sound_service.py` (4-line comment-only reword) — **pre-landed Q84**, verified present
  and self-contained ("numpy synthesis of the Web Audio alarm chime…", no `dev_docs` citation);
  never re-edited here per AP-P16-1. This single line is why the task test-command's docs-only
  echo reads `T9_FAIL_NON_DOCS`; it is the ordered exception, not a review failure.
- `tests/test_p14_cache_guard.py` / `tests/test_p15_surfacing.py` — this task's own ESC-098
  guard repair (§6), within `touches_files`.

## 6. History guard (AC-D55.10) + ESC-098 rework record

- **Cause:** the P16 Analyst-owned requirements additions inserted a Batch-30 banner blockquote at
  the top of `requirements.md` (line 3), ahead of the old whole-head hash region (`[file start,
  ### D53)`), so both `test_t34_history_markers_intact` and `test_t33_history_markers_intact`
  failed on the pin while every content assertion still passed.
- **Fix (narrow, no re-pin-by-deletion):** the hashed region is now the protected span only —
  from the Existing Repository marker sentence through the end of D52 (up to `"\n### D53 "`),
  covering the D41–D52 sections, the marker sentence, `Current Tech Stack:`, and the
  `REVERSED BY D45` / `A87 is REVERSED` / `SUPERSEDED BY D47` markers. New pin
  `PROTECTED_SPAN_SHA256 = b11d9da3…fddba41`, identical in both files.
- **Proof of no history change:** the span is byte-identical between pre-P16 HEAD and the P16
  worktree (computed both ways); requirements worktree diff is 85 insertions / 0 deletions, all
  additions (top banner, A149–A155, R110–R113, Phase P16 section) in unprotected regions.
- **No assertion weakened:** `grep` confirms both files still assert the `41..52`/`41..53`
  heading loops, the marker sentence, `Current Tech Stack:`, the D53/D54 addition markers, and
  (P15) all three reversal/supersession markers. `requirements.md` was not edited by this task.
- **Result:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
  tests/test_p14_cache_guard.py::test_t34_history_markers_intact
  tests/test_p15_surfacing.py::test_t33_history_markers_intact -q` → **2 passed**.

## 7. Observation for the Analyst (not touched — Analyst-owned file)

- `docs/requirements/requirements.md:6054` (new P16 R110 row) contains an unclosed `~~`
  strikethrough marker (`…live/paper behaviour ~~| H | M |…`). Cosmetic; flagged, not fixed:
  `requirements.md` is Analyst-owned and this task's contract forbids touching it.
