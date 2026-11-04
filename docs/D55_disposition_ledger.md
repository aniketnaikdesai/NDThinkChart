# D55 Disposition Ledger (P16-T8 — AC-D55.8, plan Phase 7)

**Task:** P16-T8 · **Date:** 2026-11-04 · **Status:** applied
**Authority:** `docs/plan.md` § Phase P16 (P16-W4), `docs/architecture.md` § Phase P16 (S-P16-4),
`docs/requirements/requirements.md` AC-D55.8, owner answers **Q84–Q87** (all answered 2026-11-04),
`docs/documentation_consolidation_plan.md` Phases 7–8 + disposition matrix, analyst defaults
**A149–A155** (esp. A150 history-addenda-only, A153 investigations-indexed-never-destroyed),
**R110–R113** (esp. R111 deletion-safety, R113 paraphrase sampling).

**Bucket vocabulary (exactly one bucket per in-scope file):**
- **keep-current** — live record; stays where it is, no banner needed.
- **keep-historical-bannered** — historical record; preserved as-is (addenda/banners only, A150).
- **pointer-or-merge-after-audit** — superseded/duplicative surface; becomes a pointer or merges only after the link audit passes.
- **conditional-deletion-candidate** — deleted only after its stated condition (successor-verified + reference-checked) is met; otherwise held.

**History guard (AC-D55.10):** no pre-P16 wording was touched by this task. Only the ledger (new file)
was added and the four Q87 targets (named below) were deleted. `docs/archive/` was **not** created —
zero archive moves executed (proposals stay historical until a link audit explicitly moves them).

## Disposition table

| # | File / set | Bucket | Condition evidence (verifier-reproducible) |
|---|---|---|---|
| 1 | `dev_docs/` (5-file initial design set: `trading_app_architecture.txt`, `detailed_technical_spec.md`, `development_phases_tasks.md`, `ibkr_TOS_trading_terminal_implementation_plan.md`, `delta.md`) | conditional-deletion-candidate → **EXECUTED (Q86: delete outright, pre-landed; verified-then-held)** | (a) Only live code reference was `services/sound_service.py:3` → `dev_docs/delta.md` §3 — resolved by **Q84**: module docstring is now self-contained ("numpy synthesis of the Web Audio alarm chime…", recipe inlined, no `dev_docs` citation; verified in tree). (b) Code-tree grep `grep -rn 'dev_docs' services/ tests/ packaging/ main.py` returns **zero hits**. (c) `dev_docs/` directory is **absent** from the tree. (d) Remaining `dev_docs` mentions under `docs/` are true history (Q86/Q84 records, plan/requirements/audit prose), not live dependencies — they stay. No archive copy (Q86: outright, not archived). |
| 2 | `docs/code_review/review_log.md` (legacy unsuffixed log) | conditional-deletion-candidate → **EXECUTED (Q87: delete, no archive)** | Successor verified live: `docs/code_review/review_log_P15.md` read in full — full-pass P15 review ending `Status: REVIEW_COMPLETE`, plus the per-phase suffixed chain (`review_log_P4`…`review_log_P16`) present in `docs/code_review/`. Legacy content superseded by the suffixed live record. Deleted without archive per Q87; no archive copy created (`docs/archive/` absent). |
| 3 | `docs/tasks/task_manager_notes.md` (legacy unsuffixed notes) | conditional-deletion-candidate → **EXECUTED (Q87: delete, no archive)** | Successor verified live: `docs/tasks/task_manager_notes_P15.md` read in full — P15 decomposition/size record — plus the per-phase suffixed chain (`task_manager_notes_P5`…`task_manager_notes_P16`) present in `docs/tasks/`. Legacy content superseded by the per-phase live records. Deleted without archive per Q87; no archive copy created. |
| 4 | `docs/code_review/precheck.json` (generated precheck output) | conditional-deletion-candidate → **EXECUTED (Q87: delete, no archive)** | Generated, reproducible artifact (produced by `review_precheck.py` per run; scope P16-T1…T7 recorded inside). Live record family verified present: `docs/code_review/test_verification.json` + `test_verification.log` in `docs/code_review/`, and `review_log_P15.md` pass header cites the `test_verification.json` verdict (pass, exit 0). Nothing unique to preserve — regenerable on the next precheck run. Deleted without archive per Q87. |
| 5 | `docs/code_review/precheck.md` (generated precheck output) | conditional-deletion-candidate → **EXECUTED (Q87: delete, no archive)** | Same evidence as #4 (human-readable rendering of the same generated run; regenerable). Deleted without archive per Q87. |
| 6 | The 16 investigation files (knowledge base, A153) | **keep-current (indexed, never destroyed, never merged)** | Owner order + A153: consolidate-by-index, do not destroy. Verified: all investigation files present in the tree, none deleted, none merged, none moved by this task (this task's diff touches only the ledger + the four Q87 targets). |
| 7 | Proposal pair `docs/architecture_proposal.md`, `docs/plan_proposal.md` (superseded D45 drafts) + any other superseded proposals | **keep-historical-bannered (archive optional ONLY after the link audit)** | Link-audit pre-move check (P16-T7, recorded in `docs/architecture.md`): only historical/do-not-read pointers reference them — but the audit moves themselves run under a later disposition, not here. **Zero moves executed by this task** (`docs/archive/` does not exist). Proposals stay historical. |
| 8 | Six P6 reconciliation files (`docs/architecture.md` § Phase P6, `docs/codebase-map.md`, `docs/lwc_parity_matrix.md`, `docs/code_review/review_log_P6.md`, `docs/phase-changelog.md`, `docs/CHANGELOG.md`) | **keep-current** (reconciled in P16-W3 with addenda; approvals byte-identical) | Out of this task's deletion scope by plan (P16-W3 deliverables). Untouched by this task. |
| 9 | User guides `usage.md` (canonical full guide, live-only per Q85) + `USAGE.txt` (short pointer) | **keep-current** | Out of this task's deletion scope by plan (P16-W2 deliverables). Untouched by this task. |
| 10 | `docs/README.md` authority blocks, per-doc metadata, cross-reference map; `docs/D55_inventory.md`, `docs/D55_fact_sheet.md` (P16-W1 records) | **keep-current** | Navigation + evidence records this ledger builds on. Untouched by this task (map precedes deletions per R111; ledger follows it). |
| 11 | `docs/D55_disposition_ledger.md` (this file) | **keep-current** (new record) | Created by this task as the AC-D55.8 evidence artifact. |
| 12 | Per-phase suffixed logs/notes (`review_log_P4`…`review_log_P16`, `task_manager_notes_P5`…`task_manager_notes_P16`), `test_verification.json`/`test_verification.log`, per-task result JSONs | **keep-current** (audit records preserved by default) | The live-record family the Q87 deletions were gated on. Untouched by this task. |

## Deletion execution record (AC2)

1. **Q86 `dev_docs/`** — already deleted pre-landing; this task re-ran the reference check
   (sound-service docstring self-contained; code-tree `dev_docs` grep zero hits in
   `services/ tests/ packaging/ main.py`; historical `docs/` mentions confirmed as true history)
   and held the deleted state (no re-delete, no restore, no archive).
2. **Q87 four targets** — each suffixed successor / live-record replacement verified live
   (rows #2–#5 above), then deleted without archive:
   `docs/code_review/review_log.md`, `docs/tasks/task_manager_notes.md`,
   `docs/code_review/precheck.json`, `docs/code_review/precheck.md` — all four absent post-task,
   and `docs/archive/` remains absent (no archive copy created).
3. **Proposals** — untouched (historical; archive only after the link audit, which is not this task).
4. **16 investigation files** — untouched (indexed, never destroyed, A153).

## Verification (reproducer)

```sh
test -f docs/D55_disposition_ledger.md \
  && test ! -e docs/code_review/review_log.md \
  && test ! -e docs/tasks/task_manager_notes.md \
  && test ! -e docs/code_review/precheck.json \
  && test ! -e docs/code_review/precheck.md \
  && ! grep -rn 'dev_docs' services/ tests/ packaging/ main.py 2>/dev/null \
  && echo T8_OK
```

Result: `T8_OK` (see task result JSON for the transcribed run).
