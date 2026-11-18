# Plan Review — Phase P24 (Option Spreads panel: owner-restated display contract, PCS ordering delta, D66)

**Status: APPROVED**

**Pass type:** `retry_2_of_3` — targeted re-validation of `RC-P24-1/-2/-3` plus the consistency ripple they
touch. This file supersedes the prior `CHANGES_REQUIRED` review; the three items it carried are recorded
below with their resolutions, and the full evidence for the unchanged material is the prior cycle's (the
delta was validated in full then and only these three items moved).

**Phase gate:** **open** — `docs/code_review/review_log_P23.md` ends `Status: REVIEW_COMPLETE`, newer than
`docs/build/build_log.md`'s last status (`NEEDS_CODE_REVIEW`, wave 380). P24 is therefore finalised here,
not kept provisional.

**Lint:** `plan_lint.py --phase P24` re-run this pass → `LINT PASS: P24 (canonical sections); 0 failure(s),
0 warning(s)`.

**Stamps (unavailable — tooling, not Plan):** `pipeline_state.py hash-section --file docs/plan.md --phase P24`
and its `architecture.md` twin both return `ERROR: no '## Phase P24' section` (same known `PHASE_HDR_RE`
mismatch recorded in the P23 review; an Orchestrator-script observation, not routed). Freshness falls back to
mtime and points the right way: `requirements.md` **15:25:50** → `plan.md` **15:44:59** /
`architecture.md` **15:47:30**.

**Escalations:** `escalations.json` holds **no open entry** — `ESC-125` (PLAN) is now `addressed`, as are
`ESC-123`/`ESC-124` (BUILD). Nothing to process.

---

## Required-change verification (this pass, verified on the tree — not on Plan's word)

### RC-P24-1 — `tests/test_d65_residue.py` inside the delta — **RESOLVED**

- **Fifth suite present.** `plan.md` § P24 header now reads "**five re-baselined suites**, one new fence
  suite"; `P24-03` lists `tests/test_d65_residue.py` in **Files**, and its deliverable 2 changes
  `CANONICAL_FIXTURES` (`tests/test_d65_residue.py:273`, confirmed on disk as `("7425/7445", "7340/7320")`)
  to `("7425/7445", "7325/7305")`, comment only, **gate body `:2536-2573`, holder list,
  `BANNED_EXAMPLES` (`:274`) and `LEGAL_NON_BANNED_PAIR` (`:275`) untouched** — all three verified verbatim
  in the file.
- **The canonical pair is named, not left to the worker.** `7325/7305` is `ladder_pairs(7325, SIDE_PCS)[1]`
  under S-P24-1's table — the anchor pair, row 2 — and the plan states the P23 precedent (`7340/7320` was
  P23's own anchor pair) as the reason. `AP-P24-3` and `S-P24-4` say the same.
- **Ordering pinned (`AP-P24-9`).** Panel fixture (P24-03 deliverable 1) **first**, residue constant
  (deliverable 2) in the same wave, never between waves; P24-01/P24-02 leave the ladder suite's
  `7340/7320` legality sites alone. Verified those sites exist and are exactly the five the plan lists:
  `tests/test_d65_option_ladder.py:158, :171, :188, :230, :246` (230 is the `_fixture_guard("PCS", 7340,
  7320)` call — separate args, so no slashed literal there), plus `:241`'s `("PCS", 7340.0)` loop, which stays
  green under the new table because every `ladder_pairs(7340, "PCS")` pair remains 20-wide and
  PCS-directional. So the old gate is satisfiable at P24-01 and P24-02, and the new one only after the panel
  fixture lands — the sequence AP-P24-9 describes is real.
- **Counts consistent everywhere.** Five suites in: the plan header, `P24-03`'s diff-scope allowlist,
  `AP-P24-1`, `S-P24-4`, `System Components` (seven suites = five re-baselined + two untouched), the
  `Codebase Summary` residue row (`[new/changed]`), the NOT-frozen block, `Non-Functional Approach`, and
  `docs/codebase-map.md` (P24 note "**five suites** `[changed in P24]`" at `:512-518`, test-impact row `:493`
  already carrying `test_d66_delta_fence`). No stale "four suites" survives in the P24 sections
  (`architecture.md:10019`'s "the four suites that hard-coded the shared table, **and** the residue suite" is
  correct English, not a stale count).
- **`docs/plan.md` / `docs/architecture.md` still hold both canonical pairs**, so the flipped gate
  (`7425/7445`, `7325/7305`) will be satisfiable in all four holders once the wave lands.

### RC-P24-2 — forbidden-string condition scoped to positive use — **RESOLVED**

- **Prohibition narrowed.** `P24-03`'s exit condition and `S-P24-4` now ban the pairs from every **positive**
  fixture / seed quote plan / probe record / canonical example, and explicitly protect the shipped negative
  guards (`test_d65_residue.py`'s `BANNED_EXAMPLES` + ban-list self-guard, the ladder suite's
  `_fixture_guard` docstring) as permitted mentions that "must stay". That matches `AC-D66.2`'s own wording
  ("no fixture may contain …") and no longer requires deleting `AC-D65.2`/`AC-D65.13`'s guard.
- **Docs describe, don't quote — independently confirmed.** `AC-D66.2`'s banned pairs are `7315/7435`
  (120-wide) and `7315/7395` (80-wide). Both P24 sections are at **zero literal occurrences**:
  `sed -n '6756,7032p' docs/plan.md | grep "7315/7435\|7315/7395\|7425/7435"` → no match; the same over
  `docs/architecture.md:9928-10210` → no match. Both now say "the 120-wide and the 80-wide restatement at
  strike 7315". The only `7340/7320` hits in the P24 ranges are the retired 20-wide canonical being moved —
  legal, and required by RC-1's argument.
- **`pytest tests/test_d65_residue.py` is green now:** 47 tests, exit 0, on a tree whose only modified files
  are docs (`git status` — no production file touched at HEAD `db21672`). `docs/plan_review_P24.md` quotes
  the literals but is outside `CONSISTENCY_FILES` (`docs/plan.md`, `docs/architecture.md` + `P23_SUITES[:-1]`),
  so the gate cannot trip on it.

### RC-P24-3 — `S-P24-3` gets an implementing deliverable — **RESOLVED**

- **Deliverable present.** `P24-01` deliverable 3 now edits the `SpreadRow` docstring in the same edit as the
  invariant's words, requiring: `rung` = 1-based **display row** (top→bottom, `1..4`, both sides); the
  owner's **logical labels** specification-only, `4,3,2,1` against those positions on PCS (`1,2,3,4` on
  CCS); nothing renders a digit or row-number column (Q117); fields, names, order and types unchanged.
- **Exit assertion present.** `P24-01`'s exit condition requires the docstring to name both terms,
  **"display row"** and **"label"** — a measurable, not a prose intention.
- **Site verified.** `services/option_ladder.py` — `@dataclass` at `:83`, `class SpreadRow:` at `:84`, its
  docstring at **`:85`** ("One displayed ladder row -- the engine's unit, the panel's row payload"), fields
  `:87-95`. The `:84` in the plan/architecture is the class line one above the docstring (see *Editorial
  observations*); the deliverable binds on the symbol, so this cannot misdirect.
- **Consistent downstream:** `S-P24-3` names the implementing site, the `Data Model` entry states the same
  meaning, the `Codebase Summary`'s `SpreadRow` row (`:83-95`) is correct, the `Frozen Interfaces` entry
  freezes the field list and explicitly unfreezes the docstring prose, and the `codebase-map` P24 note
  records the docstring change.

---

## Regression panel (nothing moved except the three fixes)

| Check | Verdict | Evidence |
|---|---|---|
| The delta itself | **PASS** | PCS rows `4,3,2,1` = `S3+5, S3, S3−5, S3−10`, Target row 2; CCS `1,2,3,4` = `S3+10, S3+5, S3, S3−5`, Target row 3 — identical in `AC-D66.2`, `S-P24-1`, the plan's `P24-01` table and the `Data Model`. |
| `AC-D66.8`'s fence | **PASS** | `P24-03` deliverable 3 (one assertion per named artefact) + deliverable 4 (build-record diff scope), mirroring `S-P24-5`; the diff-scope test stays a record, not a hash-pinned test. |
| Zero-production-change panel rule | **PASS** | `P24-01` is the only wave with a production file (`services/option_ladder.py`: table literal + three comment/docstring blocks + the `SpreadRow` docstring). `P24-02`/`P24-03` say "no production file" with an escalate-if-it-looks-necessary clause; the panel, engine, `ibkr/`, `ui/` are untouched. |
| Frozen interfaces | **PASS** | Every frozen entry is `[existing]`, verbatim and unmodified; the two changing things (offset table, `ladder_pairs` body/docstring) plus the `SpreadRow` prose sit in the NOT-frozen block. |
| D1–P23 read-only | **PASS** | Header, `A216`/`R157`, the non-goals and `AC-D66.8` all hold the delta premise; no wave restores or re-plans P23. |
| Lint | **PASS** | `LINT PASS: P24`, 0 failures, 0 warnings. |
| Residue suite today | **PASS** | `pytest tests/test_d65_residue.py` → 47 passed, exit 0. |

---

## Validation-step summary

- **1. Requirements coverage** — PASS: `AC-D66.1`–`AC-D66.8`, Journey 64, `A213`–`A219`, `R154`–`R159`,
  `DG124`–`DG127` all mapped in the traceability table (now including the residue suite in the AC-D66.2 and
  AC-D66.8 rows).
- **2. Architecture completeness** — PASS (unchanged from the prior cycle; the revision only re-worded the
  forbidden-string scope and added the residue suite to S-P24-4 / the Codebase Summary).
- **3. Consistency** — PASS on the touched areas: suite counts, allowlists, map labels, the Codebase Summary
  residue row and the NOT-frozen block now all agree with the tree.
- **4. Plan quality** — PASS: three waves (S/M/S), `P24-01 → P24-02`, `P24-01 → P24-03`; phase-level, no task
  graph, no per-task test lists beyond the `R156` re-baseline naming rule.
- **5. Task Manager readiness** — **YES**: the file set (five suites + one fence + one production file), the
  canonical pair, the gate-move ordering and the docstring deliverable are all decided here. Nothing left for
  Task Manager to invent.
- **6. Scope integrity** — PASS: no product scope added or removed; Q114–Q117 not re-opened.
- **7. Existing-repo compliance** — PASS (Codebase Summary residue row corrected to `[new/changed]`; stack
  unchanged; labels present; additive-only).
- **8. Frozen interfaces** — PASS (see panel).
- **9. Codebase map** — PASS: P24 note and test-impact row say five suites, name only existing modules plus
  the planned fence suite (marked "named without backticks until it lands").
- **10. Pending doc sync** — PASS: `docs/pending_doc_sync.md` does not exist.

## Editorial observations (non-blocking, no action required of any agent)

- `services/option_ladder.py:84` is the `class SpreadRow:` line; the docstring is `:85`. Both the plan and
  `S-P24-3` cite `:84` as the docstring's location. Symbol-bound deliverable, one-line hint drift.
- `P24-03` deliverable 2 cites the residue constant's comment as `:265-267`; the comment block is `:266-267`
  (`:265` is blank). Same class of hint drift.
- `Non-Functional Approach`'s "the five re-baselined suites keep their existing fake chain/quote doubles (the
  residue gate reads text files, not quotes)" — the parenthetical already corrects it; the residue suite has
  no quote doubles.

## Requirements Escalations

None. No P24 entry was added to `plan_notes.md`: the three RCs were Plan-owned and are now closed, and
`DG126`/`FI-P24-1` is a non-blocking owner decision already recorded in `design_gaps.md`.

## Final Decision

**`Status: APPROVED`** — `docs/plan.md` § P24 flipped to `Status: READY_FOR_TASK_MANAGER`. Task Manager may
proceed on the three-wave split (`P24-01` → `P24-02` / `P24-03`), with `tests/test_d65_residue.py` in the
change set as the fifth re-baselined suite.
