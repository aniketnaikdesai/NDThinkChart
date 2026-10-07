# Plan Review — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

## Review Status
Status: APPROVED

## Validation Summary
Validation **pass 2 (retry 1 of 3)** for the **D23 increment**. It validates
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`) and `docs/architecture_proposal.md` against
`docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-07 with D23 /
Journey 28 / `AC-D23.1.1`–`AC-D23.2.4` / A53–A55 / R49–R50 / `DG45`). Existing-repo mode (marker
sentence + Current Tech Stack present; **PyQt6 + pyqtgraph + official `ibapi` + SQLite** is a hard
constraint). D1–D22 are not re-planned.

**Escalation routing note.** `docs/code_review/escalations.json` holds **ESC-030** and **ESC-031**
with `"routed_to": "BUILD"` (not `PLAN`), both `status: open`; there is **no** `PLAN`-routed entry, so
this is a normal forward validation cycle (I did not edit the escalations file). The Requirements
Analyst captured both as **D23**, and the proposal addresses them.

**RC-1 (blocking, previous pass) — resolved.** Plan adopted option (a): the pre-fix-red evidence for
D23.1 is now a **code-shape/source assertion**. The Validator independently re-ran the check on the
current tree: `inspect.getsource(MarketDataManager.cancel_contract_details)` yields an `ast.Attribute`
node with `attr == 'cancelContractDetails'`, the substring `self.client.cancelContractDetails(` is
present, and `getattr(self.client, …)` is **absent** → the assertion is genuinely **red pre-fix** and
green after the guard. The behavioural no-exception case is honestly reclassified as a **post-fix
guard** (independently confirmed: `MarketDataManager(SimpleNamespace(reqContractDetails=…))
.cancel_contract_details(7)` returns normally on the current pre-fix tree, because the retained
`try/except Exception: pass` swallows the bare `AttributeError`). Phase 1's exit condition, PA-D23-3,
S16, the Non-Functional Q8 bullet, AR-D23-2 and the Coverage Map are all updated; the "D23.1
verification note (RC-1 closure — not a gap)" is recorded in Flagged Issues. Q8 is now honestly met
for D23.1.

**RC-2 (minor, previous pass) — resolved.** The stale Codebase-Summary line references are refreshed
and were re-verified against source: `WatchlistPanel` **816 lines**, `add_symbol :664`, header strip
`:282–289`, D21.5 column menu `:605` (the D23 targets `remove_symbol :682–728`,
`cancel_contract_details :78–84`, `clear() :730` remain correct).

**Verdict.** All three phases are fully specified and implementable without any new architectural
decision; both fixes are correct, additive and behaviour-preserving; D23.2's fix and pre-fix-red
evidence are sound; no D1–D22 re-plan; no new dependency/schema/live-order-path change. **Approved.**

## Requirements Coverage (one line per step)
- **Coverage:** every `AC-D23.1.1`–`AC-D23.1.4`, `AC-D23.2.1`–`AC-D23.2.4`, Journey 28, A53–A55,
  R49–R50 and `DG45` is mapped to a phase with a verdict — **PASS**.
- **Completeness:** Tech Stack (existing S1/S2/S14 first, then `[new/changed]` S3/S15/S16), Codebase
  Summary, Summary, System Components, Data Model, Integration Points, Non-Functional Approach and
  Architecture Risks are all present, each decision carrying rationale + alternatives — **PASS**.
- **Consistency:** no contradiction — the guard satisfies the requirement's "no raised/swallowed
  `AttributeError`"; the retained containment keeps `AC-D23.1.3`; the narrow `_row_data.pop` yields
  `set(_row_data.keys()) == set(range(rowCount()))` for first/middle/last/only (traced n=1…3) and
  keeps `_prev_close`/`_last_price` reqId-keyed; phases depend only on defined work — **PASS**.
- **Plan quality:** three ordered milestone phases (guarded cancel + test; `remove_symbol` key fix +
  test; reconciliation + non-regression), each with goal / covered ACs / dependencies / deliverables /
  exit condition; no per-task or per-criterion test spec; no task-level dependency graph — **PASS**.
- **Task Manager readiness:** can Task Manager build a valid task graph without a new architectural
  decision? **Yes** — guard shape, docstring facts, fake shapes, narrow pop fix, test shapes, and the
  `S3`/`AC-D22.2.3` reconciliation owners are all fixed — **PASS**.
- **Scope integrity:** D23 supersedes only the task-level `AC-D22.2.3` and reconciles `S3`; adds/
  removes no product scope; `AC-D22.1`–`AC-D22.9` stand — **PASS**.
- **Existing-repo compliance (step 7):** all six checks **PASS** (see below).

## Architecture Findings
- The D23.1 fix is correct as a capability-guarded no-op (`getattr(self.client,
  'cancelContractDetails', None)` + call-if-present inside the retained containment): correct on the
  pinned dep today, forward-correct if a future `ibapi` exposes the method. `S3` is reconciled in
  `docs/architecture.md` (written this cycle in `## D23 increment` S3, with a cross-reference note on
  the D22 `S3` row).
- The D23.2 fix is correct (pop the removed key before the existing shift); FieldKey-bound values are
  untouched, so `_rebuild_table`/`_set_cell` do not regress.
- No new dependency, no schema change, no new integration, no live-order-path change; the pinned
  `ibapi` version is not changed.

## Plan Findings
- Phases are correctly structured and coarse enough for Task Manager; Phases 1 and 2 touch **fully
  disjoint** file sets (`ibkr/market_data.py` + its test vs `ui/watchlist_panel.py` + its test) and
  may share one wave; Phase 3 follows.
- D23.1's pre-fix-red evidence is now genuine (code-shape/source assertion) and its behavioural
  tests are honestly labelled post-fix guards. D23.2's last-row assertion is genuinely red pre-fix.
- Assumptions PA-D23-1…PA-D23-10 are plan-level and encode no requirements decision.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + official `ibapi` + SQLite terminal (`requirements.md`
contains the literal marker sentence and a Current Tech Stack). Checks:

- **Codebase Summary present and substantive — PASS.** Inventories the SQLite `watchlist` table and
  access helpers, the `WatchlistPanel` in-memory row-keyed state, `MarketDataManager`,
  `IBApiClient`/`IBBridge`, `ContractLookupService._pending`, `MainWindow`, `data/db.py`, the key
  entry points, the existing integrations, and five source-validated facts.
- **Existing stack respected — PASS.** S1/S2/S14 keep Python 3.11+ / PyQt6 / pyqtgraph / official
  `ibapi` (pinned `9.81.1.post1`, live 7496 only) / numpy / SQLite / PyInstaller / pytest-qt
  unchanged and **listed before** the D23 rows; nothing is replaced or deprecated; no version bump.
- **Labels present — PASS.** System Components, Data Model and Integration Points each mark every
  item `[existing]` / `[new]` / `[new/changed]`.
- **Additive-only — PASS.** Only two method bodies are corrected (`cancel_contract_details`,
  `remove_symbol`) plus their tests; the D22 change set is not reopened; the request/persistence
  paths are untouched.
- **Codebase Summary consistent with the proposal — PASS.** Every `[existing]` item named appears in
  the Codebase Summary and was confirmed in source; the `[new/changed]` items are exactly the two
  methods, their docstrings and the two test modules.

## Required Changes
**None.** RC-1 and RC-2 from pass 1 are resolved and independently re-verified.

## Requirements Escalations
**None.** The RC-1 closure is a plan-level verification correction, not a requirements defect;
`AC-D23.1.1`'s stated behaviour is implementable and is implemented by S3. No
`ESCALATED_TO_REQUIREMENTS` entry is added to `docs/plan_notes.md`.

## Task Manager Readiness
**Yes.** Task Manager can decompose the three phases into tasks with acceptance criteria and tests
without inventing any architecture. The canonical artifacts (`docs/architecture.md` `## D23
increment`, `docs/plan.md`, `docs/plan_notes.md` RG-D23-1) carry the reconciled `S3`, the phased D23
plan, and the reconciliation record. Phase 3's Task-Manager-owned `AC-D22.2.3` rewrite (task
`D22-02` in `docs/tasks/task-graph.json`) is directed by `AC-D23.1.4` and is the only task-graph
edit expected.

## Final Decision
Status: APPROVED
