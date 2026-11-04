# D55 Inventory — preserved state + classified file list + cross-reference map (D55.1)

> **Role:** W1 record for `AC-D55.1`. **Status:** current as of 2026-11-04. **Canonical:** yes
> (inventory only — it confers no product facts; source code wins on implementation facts).
> **Zero deletions:** this task deletes no file.

## 1. Preserved-working-state note (checkout at task start)

- HEAD: `945a2b2` — "Scratch + evidence: D53 4-phase live probe harness (v3 logging) and TWS probe findings/reports".
- **Staged deletions (pre-landed Q86, verified — never re-done here):** `dev_docs/delta.md`,
  `dev_docs/detailed_technical_spec.md`, `dev_docs/development_phases_tasks.md`,
  `dev_docs/ibkr_TOS_trading_terminal_implementation_plan.md`,
  `dev_docs/trading_app_architecture.txt` (5 files, 1566 deletions). Working tree has no `dev_docs/`.
- **Staged modifications (preserved, not overwritten):** `docs/architecture.md`, `docs/codebase-map.md`,
  `docs/plan.md`, `docs/requirements/design_gaps.md`, `docs/requirements/feature_suggestions.md`,
  `docs/requirements/open_questions.md`, `docs/requirements/requirements.md`,
  `docs/tasks/execution_graph.json`, `docs/tasks/task-graph.json`,
  `services/sound_service.py` (Q84: docstring is self-contained — "numpy synthesis of the Web Audio
  alarm chime"; the `dev_docs/delta.md` §3 citation is gone).
- **Untracked files (preserved):** `docs/plan_review_P16.md`, `docs/tasks/task_manager_notes_P16.md`.
- **Git-ignored generated files present on disk (not inventory buckets — listed §4):**
  `docs/code_review/precheck.json`, `docs/code_review/precheck.md` (`.gitignore:53-54`),
  `docs/code_review/test_verification.json`, `docs/code_review/test_verification.log`,
  `docs/build/*` (`.gitignore:7`), `graphify-out/` (`.gitignore:50`).

## 2. Classified inventory (tracked Markdown/text, one bucket per file)

Scope: every tracked `*.md` / `*.txt` file (`git ls-files | grep -E '\.(md|txt)$'` — 79 files at
task start; staged-deleted `dev_docs/` files are out of the index and recorded in §1/§3 instead).
Buckets per `docs/documentation_consolidation_plan.md` Phase 0.

### normative (14) — current authority / decision / configuration records

- `docs/requirements/requirements.md`
- `docs/requirements/design_gaps.md`
- `docs/requirements/open_questions.md`
- `docs/requirements/feature_suggestions.md`
- `docs/architecture.md`
- `docs/plan.md`
- `docs/plan_notes.md`
- `docs/documentation_consolidation_plan.md`
- `docs/phase-changelog.md`
- `docs/plan_review_P7.md` (approval evidence, active phase)
- `docs/plan_review_P8.md` (approval evidence, active phase)
- `docs/code_review/escalations.md` (open escalation ledger companion)
- `requirements.txt` (dependency pins — configuration, not prose)
- `requirements-dev.txt` (dependency pins — configuration, not prose)

### user-guidance (2) — install/use instructions

- `usage.md` (canonical full guide)
- `USAGE.txt` (short pointer + quick start)

### navigation (3) — index / map / pointer docs

- `docs/README.md`
- `docs/codebase-map.md`
- `docs/CHANGELOG.md` (short index pointing at `docs/phase-changelog.md`)

### historical-evidence (52) — audit trail, superseded proposals, past-phase records

- `docs/architecture_proposal.md`
- `docs/plan_proposal.md`
- `docs/plan_review.md`, `docs/plan_review_P5.md`, `docs/plan_review_P6.md`
- `docs/plan_review_P9.md`, `docs/plan_review_P10.md`, `docs/plan_review_P11.md`
- `docs/plan_review_P12.md`, `docs/plan_review_P13.md`, `docs/plan_review_P14.md`
- `docs/plan_review_P15.md`
- `docs/code_review/review_log.md`
- `docs/code_review/review_log_P4.md`, `docs/code_review/review_log_P5.md`
- `docs/code_review/review_log_P6.md`, `docs/code_review/review_log_P8.md`
- `docs/code_review/review_log_P9.md`, `docs/code_review/review_log_P10.md`
- `docs/code_review/review_log_P11.md`, `docs/code_review/review_log_P12.md`
- `docs/code_review/review_log_P13.md`, `docs/code_review/review_log_P14.md`
- `docs/code_review/review_log_P15.md`
- `docs/code_review/architecture_vs_code_audit.md`
- `docs/code_review/candle_overlap_investigation.md`
- `docs/code_review/footprint_permissions.md`
- `docs/code_review/market_depth_permissions.md`
- `docs/code_review/one_min_backfill_starvation.md`
- `docs/code_review/order_code_audit.md`
- `docs/code_review/portfolio_held_rows.md`
- `docs/code_review/priming_321_investigation.md`
- `docs/code_review/rth_single_day_investigation.md`
- `docs/tasks/task_manager_notes.md`
- `docs/tasks/task_manager_notes_P5.md`, `docs/tasks/task_manager_notes_P6.md`
- `docs/tasks/task_manager_notes_P7.md`, `docs/tasks/task_manager_notes_P8.md`
- `docs/tasks/task_manager_notes_P9.md`, `docs/tasks/task_manager_notes_P10.md`
- `docs/tasks/task_manager_notes_P11.md`, `docs/tasks/task_manager_notes_P12.md`
- `docs/tasks/task_manager_notes_P13.md`, `docs/tasks/task_manager_notes_P14.md`
- `docs/tasks/task_manager_notes_P15.md`
- `docs/lwc_parity_matrix.md` (P6 acceptance evidence; live test readers in §3)
- `docs/lwc_spike_results.md`
- `spikes/lwc/README.md`
- `docs/memory.md` (non-normative context per plan matrix)
- `docs/debug/debug_log.md`
- `docs/thinkorswim-feature-gap-analysis.md` (dated research)
- `docs/ibkr-api-data-inventory.md` (dated research)

### one-off diagnostic (7) — untracked-style snapshots and probe records

- `ALARM_AND_DRAWING_CODE_REVIEW.txt`
- `NDThinkChart_TWS_probe_findings_20261103.txt`
- `POPOUT_AND_MAIN_CHART_REVIEW.txt`
- `POPOUT_CHART_CODE_TRACE_REPORT.txt`
- `docs/d48_probe_record.md`
- `docs/d52_probe_record.md`
- `docs/p13_hold_probe_record.md`

### generated-vendored (1) — vendored third-party attribution

- `chart_assets/lwc/ATTRIBUTION.md`

Bucket count check: 14 + 2 + 3 + 52 + 7 + 1 = 79 = every tracked `*.md` / `*.txt` file, each exactly once.

## 3. Cross-reference map (filename/heading → live readers with source locations)

Conventions: "code reader" = `*.py` / `*.spec` / `*.ini` / packaging under
`services/ tests/ packaging/ main.py config/ data/ ibkr/ ui/`. Prose mentions of
disposition-target docs are true history and stay untouched.

| Affected doc | Live reader (source location) | Kind |
|---|---|---|
| `dev_docs/` (all 5 files, deleted per Q86) | **No code reader.** `grep -rn dev_docs services/ tests/ packaging/ main.py config/ data/ ibkr/ ui/` returns zero hits (verified 2026-11-04). Former `services/sound_service.py:3` citation resolved by Q84 — docstring now self-contained | verified absent |
| `dev_docs/` historical mentions | `docs/README.md:37`, `docs/requirements/requirements.md` (A1 row, § Phase P16), `docs/documentation_consolidation_plan.md:203,228`, `docs/architecture.md:7372-7386`, `docs/plan.md:4032,4173`, `docs/codebase-map.md:99`, `docs/requirements/open_questions.md` (Q84–Q86), `docs/build/quick/Q-63.md`, `docs/tasks/task-graph.json`, `docs/plan_review_P16.md`, `docs/tasks/task_manager_notes_P16.md` | prose history (kept) |
| `docs/lwc_parity_matrix.md` | `tests/test_lwc_cutover_gate.py:54,180,187,249,253,301`; `tests/test_chart_view_seam.py:221`; `tests/test_lwc_removal_gate.py:9` (docstring); `tests/test_lwc_drawings.py:50`; `tests/test_lwc_alarms.py:36`; `tests/test_lwc_time_parity.py:37`; `tests/test_lwc_studies.py:32`; `tests/test_lwc_overlays.py:50` | test gate readers |
| `docs/lwc_spike_results.md` | `tests/test_lwc_cutover_gate.py:55,80,249,253`; `packaging/build.spec:126` (comment only, not a load) | test + comment |
| `docs/build/gate_P6_T13.md` | `tests/test_chart_view_seam.py:4` (docstring); `ui/chart_view.py:9` (comment citing waived-not-satisfied) | test + code comment |
| `docs/requirements/requirements.md` | `tests/test_p15_surfacing.py:404` (reads `### D41`–`### D53` block) | test reader |
| `docs/p13_hold_probe_record.md` | `tests/test_p13_hold_probe.py:8` (docstring) | test docstring |
| `docs/build/approvals/P7-T06-*.md` | `tests/test_ibkr_handshake_gate.py:170` | test reader |
| `chart_assets/lwc/ATTRIBUTION.md` (+ `VERSION`) | `NDThinkChart.spec:13` (comment); `packaging/build.spec:41` (comment); whole `chart_assets/lwc/` shipped as bundle data | packaging bundle |
| `usage.md` / `USAGE.txt` | No code/packaging/test reader found (neither `.spec` references them); pointer relationship only | no live reader |
| `docs/code_review/review_log.md`, `docs/tasks/task_manager_notes.md` (Q87 targets) | No code reader (code-only grep for `review_log|task_manager_notes|precheck` over py/spec/ini returns only the doc-gate tests above). Prose references only (plan matrix, task-graph, build wave files) | prose only |
| `docs/code_review/precheck.json` / `precheck.md`, `test_verification.json` / `.log` (Q87 / generated targets) | Git-ignored generated output; no code reader; referenced by prose/build tooling only | generated, no live reader |

Dangling-reference assertion (T12): zero `dev_docs` hits across `services/ tests/ packaging/
main.py` (plus `config/ data/ ibkr/ ui/`); the Q84 `sound_service` docstring is self-contained.
No code-tree reference into a deleted or candidate-deleted doc remains dangling.

## 4. Untracked / ignored doc files (listed separately, not bucketed)

- Untracked working-tree docs: `docs/plan_review_P16.md`, `docs/tasks/task_manager_notes_P16.md`,
  `docs/D55_fact_sheet.md` (sibling W1 record, landed after this inventory), and this file itself.
- Git-ignored generated docs (outside the canonical set per the consolidation plan):
  `docs/code_review/precheck.json`, `docs/code_review/precheck.md`,
  `docs/code_review/test_verification.json`, `docs/code_review/test_verification.log`,
  `docs/build/*`, `graphify-out/*`.
