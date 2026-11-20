# Implementation Plan — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

> **Current baseline (P16-T7 navigation block, 2026-11-04 — navigation only, no phase re-planned).** Current architecture: PyQt6 + Lightweight-Charts-only terminal (live TWS 7496, SQLite, PyInstaller .app), as-built through P8 (D48); see `docs/architecture.md` § *Phase P16*. Active phase: **Phase P16 — Documentation consolidation (D55, docs-only)**, waves P16-W1…P16-W4 (`Status: READY_FOR_TASK_MANAGER`; this task P16-T7 = D55.7 navigation, P16-W3). Unresolved requirements: ESC-079 only (`AC-D16.8` restatement, Analyst debt RG-P7-1); Q84–Q87 answered; 50-vs-100 settled per the P16-D55.6 addendum below. As-built changelog: `docs/phase-changelog.md` (indexed by `docs/CHANGELOG.md`).
>
> **Link/reference audit (P16-T7, 2026-11-04): pass.** Filename/heading/phase-ID/commit/status checks across the canonical files; the only non-resolving hits are recorded history/absence, not dangling links (`dev_docs/delta.md` §3 = removed-per-Q86 true history; `docs/pending_doc_sync.md` = recorded absent). Repeated summaries are cross-references (R112), never duplicated prose. Archive candidates (pre-move check done, **zero moves executed here** — moves run under P16-T8): `docs/architecture_proposal.md`, `docs/plan_proposal.md` (superseded D45 pair; only historical/do-not-read pointers reference them — pre-move check passes).

> **Current baseline (appended 2026-10-28, Q-53 - navigation only, no phase re-planned).** As-built through **P8 (D48)** (P7 feature commit `7cba534`, P8 feature commit `09761fb`, both landed 2026-10-28; LWC-only tree; live-session sign-off waived-not-satisfied per `docs/build/gate_P6_T13.md`). **Phase P7: BUILT. Phase P8: BUILT** (per-section status lines below are the authority). Open debt: ESC-079 only (`AC-D16.8` restatement, Analyst debt RG-P7-1); ESC-070 and ESC-075-078 are addressed - see `docs/phase-changelog.md` Phase P6/P7 entries. Authority: `docs/README.md`. As-built history: `docs/phase-changelog.md` (indexed by `docs/CHANGELOG.md`).

> **Document state (2026-10-15).** This file is the canonical plan. Its **first section** is the
> approved **D23** plan (Phases 1–3, `Status: READY_FOR_TASK_MANAGER`); below it, the
> **as-built** records for **D24–D28** (as-built / **OWNER-APPROVED 2026-10-14**, Q41) and
> **D36–D40** (as-built 2026-10-13, Code Reviewer APPROVED, acceptance criteria **authored**
> 2026-10-14 per Q45/DG46) are carried, followed by a **plan-vs-code verification** section
> (Q41/DG53) and, appended 2026-10-15, the **D41 (Batch 18) removal plan** — validated
> `Status: APPROVED` and **approved for build, not yet built** — followed by the **D42 (Batch 18b)
> plan** (density-aware candle/volume body width + mode-aware intraday depth/day-presence, validated
> `Status: APPROVED` 2026-10-15, cycle 2 of 3, **approved for build, not yet built**) and, appended
> 2026-10-16, the **D44 (Batch 19) plan** — the collapsed Watchlist becomes a thin vertical bar that
> expands to the full panel (owner-requested; validated `Status: APPROVED` 2026-10-16, legacy
> single-scope cycle, **approved for build, not yet built**) (the live handoff status line is the one
> at the end of this file). **All of D1–D40 are built and merged to
> `main`** (the D40 merge is
> `b366b19`; `origin/main` is now `262ec81`, after `7566860` → `99fb8fa` → `262ec81`). The
> per-run "gated in TWS" planning constraint is **retired** (Q42/DEC-4);
> pop-out always-on-top defaults **OFF** (`AC-D24.10`, Q43); the D37 depth heatmap defaults
> **ON** (A67, Q44) — D37 itself is **superseded by D41**. No "DRAFT" / "unmerged" / "pending owner
> review" wording remains for D24–D28.

> **Citation convention (mirrors `docs/architecture.md`, adopted 2026-10-14 per `DG56`).**
> Cite a location as **`path::symbol`** — `ui/main_window.py::MainWindow._open_popout`,
> `config/settings.py::MAX_POPOUTS` — because a symbol survives any edit above it. A bare
> `file:line` is **indicative only** and drifts whenever lines are inserted above it
> (`99fb8fa` inserted 5 lines into `ui/main_window.py` and invalidated ~10 references at once).
> Where a line is kept it follows the symbol, in parentheses. The historical D16–D23 record
> (architecture increment sections, and the D23 phases below) keeps its at-that-commit line
> numbers deliberately — bounded, not renumbered; every symbol in it was re-verified against
> the tree. See `docs/architecture.md` § *Citation convention*.

Scope: **D23 only** — the two *nice-to-have* Code Reviewer findings on the just-built **D22** work,
both approved by the user for a full-pipeline fix:

- **D23.1 = ESC-030** — `MarketDataManager.cancel_contract_details` must be a **capability-guarded,
  documented** best-effort cancel (the pinned `ibapi` has **no**
  `EClient.cancelContractDetails` — `9.81.1.post1` at D23 time, and **still absent on the current
  `ibapi-latest==10.51.1` pin**, re-verified 2026-10-14). This **supersedes the task-level
  `AC-D22.2.3`** wire-cancel
  mandate and **reconciles architecture row `S3`**.
- **D23.2 = ESC-031** — `WatchlistPanel.remove_symbol` must leave **no stale `_row_data` key**
  (`set(_row_data.keys()) == set(range(rowCount()))`) for first/middle/last/only-row removals, with
  the missing coverage added.

It is planned on top of the **as-built, frozen D1–D22 baseline** (D1–D21 at commit `286341e`, 673
tests; D22 built and green at **712 tests**, uncommitted). This is an existing-repo run: items are
labelled `[existing]`, `[new]`, `[new/changed]`; the existing stack (**PyQt6 + pyqtgraph + official
`ibapi` + SQLite**) is a **hard constraint**. **No new product feature, no stack change, no schema
change, no new dependency, no new external integration, and no live-order-path change.**
**D23 does not reopen D22** — `AC-D22.1`–`AC-D22.9` stand.

> Companion architecture: `docs/architecture.md` (`## D23 increment` — D23 Codebase Summary,
> tech-stack rows S1/S2/**S3 (reconciled)**/S15/S16/S14, components, data model, integrations,
> non-functional, risks).
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-07
> with Batch 17 / **D23** / Journey 28 / `AC-D23.1.*`–`AC-D23.2.*` / A53–A55 / R49–R50 / **DG45**;
> `open_questions.md` Batch 17 — no blocking question). As-built baseline:
> `docs/architecture.md` (`## D22 increment`, validated 2026-10-07).

## Completed baseline — D1–D22 (as-built, frozen)

D1–D21 are built and verified at commit `286341e` (673 tests). **D22** — the in-app watchlist
**"Add symbol" / "Remove symbol"** affordance (live `reqContractDetails` validation, the
`ContractLookupService`, persistence, the seed sentinel) — is **built and green at 712 tests**
(uncommitted). D1–D22 are **frozen** and are **not** re-planned. D23 corrects only the two
task/implementation-level defects below and changes no D22 feature criterion.

## Coverage Map

| Requirement / journey / AC | What it demands | Phase | Verdict |
|---|---|---|---|
| **D23** — two D22 post-build quality corrections | Guarded cancel + no stale `_row_data` key | 1–3 | Covered |
| `AC-D23.1.1` (capability-guarded cancel — no raised/swallowed `AttributeError`) | Missing method (pinned `ibapi`) → returns without raising (no `AttributeError` occurs at all); present method → invoked once with `req_id` | 1 | Covered (S3, guarded `getattr` + call-if-present); pre-fix-red evidence = **code-shape/source assertion** (the requirement's two behavioural measurables are kept as post-fix guards) |
| `AC-D23.1.2` (documented absence + safety net) | `cancel_contract_details` documents the pinned-`ibapi` absence, TWS `contractDetailsEnd`/error termination, and `ContractLookupService` local invalidation as the safety net | 1 | Covered (S3 docstring/comment) |
| `AC-D23.1.3` (None-safe + containment preserved) | `req_id is None` → no-op; a rising capability-guarded cancel → no exception escapes | 1 | Covered (S3 keeps `None` guard + containment) |
| `AC-D23.1.4` (supersession + reconciliation recorded) | Correct task-level `AC-D22.2.3` and reconcile architecture `S3`; no D22 reopening | 1 + 3 | Covered (Task Manager rewrites `AC-D22.2.3`; Validator records `S3`; Build implements guard + test) |
| `AC-D23.2.1` (no stale row key — last-row removal) | 3-row panel, remove last → `rowCount() == 2` **and** `sorted(_row_data.keys()) == [0, 1]` | 2 | Covered (S15 + S16) |
| `AC-D23.2.2` (first / middle / only-row removal) | `set(_row_data.keys()) == set(range(rowCount()))` for first/middle/only (only → `rowCount()==0`, `_row_data=={}`); same for `_req_to_row` values and `_flash_timers` keys | 2 | Covered (S15 + S16) |
| `AC-D23.2.3` (coverage added) | A last-row (and/or first/only-row) assertion that **fails pre-fix**, not only the middle-row check | 2 | Covered (S16) |
| `AC-D23.2.4` (regression) | `test_D22_05_T02` (middle-row re-index, reqId cancellation, flash-timer re-index, later-tick routing) and `test_D22_05_T03` (absent/blank no-op) stay green; `_row_data` stays valid for `_rebuild_table`/`_set_cell` | 2 + 3 | Covered (S15 narrow fix + Phase 3 full suite) |
| Journey 28 — post-build quality corrections | Last-row removal leaves no stale key; the cancel is guarded/documented with no swallowed `AttributeError`; local invalidation is the safety net | 1–3 | Covered |
| A53 / A54 (D23.1 guard; wire cancel is dead code today) | Guarded + documented cancel; forward-correctness only, no D22 observable change | 1 + 3 | Covered (S3; S16 test) |
| A55 (D23.2 — only `_row_data` carries a stale key) | Fix applies to `_row_data`; `_req_to_row`/`_prev_close`/`_last_price`/flash timers already explicit | 2 | Covered (S15) |
| R49 (correcting `AC-D22.2.3` conflicts with built D22 tests) | Update the criterion and its `_FakeClient`-based test **in lockstep**; keep the suite green | 1 + 3 | Covered (S16 + Phase 3 lockstep note) |
| R50 (re-index could shift cached values onto the wrong row) | Narrow pop fix + set-equality assertions for first/middle/last/only | 2 | Covered (S15 + S16) |
| `DG45` (contract-details cancel conflicts with the pinned ibapi) | Capability-guarded, documented cancel; correct `AC-D22.2.3`, reconcile `S3` | 1 + 3 | Covered (S3 + reconciliation) |
| Q8/Q9 (regression + live-TWS safety) | Pre-fix-red/post-fix-green checks, offscreen, no live TWS | All phases | Covered — D23.2 pre-fix-red = last-row assertion; D23.1 pre-fix-red = code-shape/source assertion (its behavioural tests are post-fix guards, the fix being externally invisible) |
| D1–D22 | Frozen, re-affirmed; not re-planned | — | Covered |

No requirement is narrowed, reinterpreted, or left unsatisfied. **D23 supersedes only the task-level
`AC-D22.2.3`** (a task/implementation mandate, corrected) and **reconciles D22 architecture `S3`**;
no D22 **feature** criterion (`AC-D22.1`–`AC-D22.9`) changes.

## Phases

Each phase is a milestone, coarser than a task; the Task Manager decomposes each into tasks with
acceptance criteria and tests. Phases are ordered; a later phase depends on all earlier ones unless
stated. `touches_files` notes list the files a phase touches and flag the serialisation points.

### Phase 1 — [new/changed] Capability-guarded, documented contract-details cancel (D23.1)

- **Goal:** `MarketDataManager.cancel_contract_details` becomes a capability-guarded, documented
  best-effort cancel that neither raises nor silently swallows an `AttributeError` on the pinned
  `ibapi`; the D22 test covers the missing-capability surface.
- **Covers:** D23.1; `AC-D23.1.1`–`AC-D23.1.4`; Journey 28 (D23.1 steps); A53/A54; R49; `DG45`.
- **Deliverables:**
  - `[new/changed] ibkr/market_data.py` — rewrite `MarketDataManager.cancel_contract_details`
    (`:78–84`): keep `if req_id is None: return`; resolve
    `cancel = getattr(self.client, 'cancelContractDetails', None)`; call it only if present, inside
    the existing containment (`try/except Exception: pass`); add the docstring/comment documenting
    (a) the pinned `ibapi 9.81.1.post1` has no `EClient.cancelContractDetails`, (b) TWS's own
    `contractDetailsEnd`/error ends the wire request, (c) `ContractLookupService`'s local
    invalidation (bounded `QTimer` + `cancel_all` on disconnect) is the real safety net.
    `req_contract_details` is unchanged.
  - `[new/changed] tests/test_ibkr_contract_details_d22.py` — add **three** things:
    - **(pre-fix-red — the Q8 evidence for D23.1) a code-shape/source assertion** on
      `MarketDataManager.cancel_contract_details`'s **own source** (e.g.
      `ast.parse(textwrap.dedent(inspect.getsource(MarketDataManager.cancel_contract_details)))` —
      `textwrap.dedent` is required because `inspect.getsource` returns the method indented):
      assert (a) the bare, unguarded attribute access `self.client.cancelContractDetails(...)` is
      **gone** (no `ast.Attribute` node with `attr == 'cancelContractDetails'`; the substring
      equivalent `self.client.cancelContractDetails(` absent is acceptable), **and** (b) the
      capability guard `getattr(self.client, "cancelContractDetails", None)` is **present**. Red on
      the current file (bare access at `:82`, no `getattr`), green after the guard. (Empirically
      confirmed on the current tree by the Validator: AST attrs include `cancelContractDetails`, the
      guard is absent, and the behavioural call below returns with no exception — i.e. the
      source-shape assertion is the *only* pre-fix-red check.)
    - **(post-fix guard — explicitly NOT pre-fix-red) a missing-capability behavioural test**: a fake
      that does **not** define `cancelContractDetails` (e.g.
      `types.SimpleNamespace(reqContractDetails=lambda *a: None)`); assert
      `cancel_contract_details(7)` completes with no exception. This passes on **both** the pre- and
      post-fix trees (the retained `try/except Exception: pass` already swallows the pre-fix
      `AttributeError`), so it documents the intended no-op and guards a future regression that
      removes the guard *and* the containment — it is **not** the pre-fix-red evidence.
    - **(post-fix guard) a present-method behavioural test**: keep the method-defining `_FakeClient`
      and assert the method is invoked once with `req_id` (`cancel_calls == [7]`); keep the existing
      None-safe and raising-client cases.
- **Dependencies:** none (independent of Phase 2).
- **`touches_files`:** `ibkr/market_data.py`, `tests/test_ibkr_contract_details_d22.py`. No overlap
  with any other phase.
- **Exit condition:** the **code-shape/source assertion** is **red against the current code** (the
  bare `self.client.cancelContractDetails(...)` access is present and no `getattr(..., None)` guard
  exists) and **green after** the guard; the behavioural cases (missing-capability → no exception;
  present → invoked once with `req_id`; None-safe; raising-client) are **post-fix guards** expected
  to pass on **both** the pre- and post-fix trees and are explicitly **not** the pre-fix-red
  evidence. No `AttributeError` escapes the guarded method, and none is silently swallowed on the
  guarded path.

### Phase 2 — [new/changed] `remove_symbol` drops the removed row's `_row_data` key (D23.2)

- **Goal:** after any removal, `remove_symbol` leaves `_row_data` keyed exactly over the surviving
  rows, with the missing last/first/only-row coverage added.
- **Covers:** D23.2; `AC-D23.2.1`–`AC-D23.2.4`; Journey 28 (D23.2 steps); A55; R50.
- **Deliverables:**
  - `[new/changed] ui/watchlist_panel.py` — in `WatchlistPanel.remove_symbol` (`:682–728`), drop the
    removed row's own `_row_data` entry while re-indexing (e.g. `self._row_data.pop(row, None)`
    before the existing `{(r-1 if r > row else r): values …}` re-map), and update the
    `remove_symbol` docstring to state the invariant
    `set(_row_data.keys()) == set(range(table.rowCount()))` alongside the existing
    `_req_to_row`/flash-timer handling. `_prev_close`/`_last_price` (reqId-keyed) and
    `_req_to_row`/`_flash_timers` handling are unchanged.
  - `[new/changed] tests/test_watchlist_add_remove_d22.py` — add a **last-row** removal assertion
    (3-row panel, remove the last → `sorted(_row_data.keys()) == [0, 1]`, `rowCount() == 2`), and/or
    a **first-row** / **only-row** assertion (`rowCount() == 0` → `_row_data == {}`); keep the
    existing `test_D22_05_T02` (middle-row) and `test_D22_05_T03` (absent/blank no-op) green.
- **Dependencies:** none (independent of Phase 1).
- **`touches_files`:** `ui/watchlist_panel.py`, `tests/test_watchlist_add_remove_d22.py`. No overlap
  with any other phase (`ui/watchlist_panel.py` is not touched by Phase 1 or 3's code work; D22's
  `ui/main_window.py` is untouched).
- **Exit condition:** the new last-row assertion is **red against the current `remove_symbol`**
  (stale key survives) and **green after** the fix; `test_D22_05_T02`/`test_D22_05_T03` stay green;
  `_row_data` remains valid for `_rebuild_table`/`_set_cell`.

### Phase 3 — Reconciliation + non-regression verification

- **Goal:** the correction record is consistent across artifacts and the full pre-existing suite
  stays green; the ESC-030/ESC-031 fixes are independently re-verifiable.
- **Covers:** `AC-D23.1.4` (reconciliation record), `AC-D23.2.4`; R49/R50 closure; the global
  "pre-existing suite stays green" criterion.
- **Deliverables:**
  - **Validator** reconciles architecture `S3` in `docs/architecture.md` (the cancel is
    best-effort/unavailable on the pinned `ibapi`; `ContractLookupService` local invalidation is the
    safety net) and records the note in `docs/plan_notes.md`. *(Done in this validation cycle — see
    `docs/architecture.md` `## D23 increment` S3 + the D22 `S3` reconciliation note, and
    `docs/plan_notes.md` RG-D23-1.)*
  - **Task Manager** rewrites task-level `AC-D22.2.3` (and its test description) in
    `docs/tasks/task-graph.json` (task `D22-02`) to the capability-guarded, documented cancel — in
    lockstep with the Phase-1 test change.
  - **Build/verification** runs the full offscreen suite
    (`.venv/bin/python -m pytest`, `QT_QPA_PLATFORM=offscreen`) → **712 baseline tests plus the new
    cases all green**; a clean full-suite run (not an incremental one) is required per the recorded
    shared-test-DB / stale-`pytest`-shebang gotchas.
  - **Code Reviewer** re-verifies ESC-030 and ESC-031 after Build (flips them `addressed`).
- **Dependencies:** Phase 1 **and** Phase 2 complete.
- **`touches_files`:** no application code; artifact owners are the Validator
  (`docs/architecture.md`, `docs/plan_notes.md`) and Task Manager (`docs/tasks/task-graph.json`).
  Build/verification touches only test execution, not source.
- **Exit condition:** architecture `S3` and `AC-D22.2.3` read consistently with the pinned `ibapi`
  surface; every `AC-D23.*` criterion is observably satisfied; the full offscreen suite is green;
  no D1–D22 criterion regresses.

**Wave note.** Phase 1 and Phase 2 touch **fully disjoint** file sets and can run in a **single
wave**; Phase 3 runs after both. There is no file that two phases write.

## Assumptions

| # | Assumption | Rationale |
|---|---|---|
| PA-D23-1 | The guard uses `getattr(self.client, 'cancelContractDetails', None)` and calls the method only when it is not `None`; the `None`-`req_id` early return and the containment (`try/except Exception: pass`) are both retained | The requirement states the exact guard and requires no raised and no silently-swallowed `AttributeError` (`AC-D23.1.1`/`AC-D23.1.3`); retaining containment preserves the method's established contract |
| PA-D23-2 | The documentation lives in the method's docstring (with a short inline comment), naming the pinned version, TWS's `contractDetailsEnd`/error termination, and the `ContractLookupService` safety net | `AC-D23.1.2`'s measurable is "the named facts appear in the method's comment/docstring"; checkable by review |
| PA-D23-3 | For D23.1 the genuine **pre-fix-red** evidence is a **code-shape/source assertion** on `cancel_contract_details` (no bare `self.client.cancelContractDetails(...)` attribute access; the `getattr(self.client, "cancelContractDetails", None)` guard present) — red on the current file, green after. The **behavioural** cases are **post-fix guards**: the missing-capability fake (`types.SimpleNamespace(reqContractDetails=lambda *a: None)`) asserts no exception, and the "present" case keeps the method-defining `_FakeClient` (a spy) asserting a single call with `req_id`. The behavioural cases cannot be pre-fix-red | Because the fix retains `try/except Exception: pass`, pre- and post-fix behaviour is externally identical for a client lacking the method (the current code raises `AttributeError` inside the `try`, swallows it and returns normally), and a `getattr(..., None)` guard still performs the attribute lookup — verified on the current tree and confirmed by the Validator — so **no behavioural or attribute-access-spy assertion can distinguish pre- from post-fix**. The code-shape/source assertion is therefore the only honest pre-fix-red check and is what satisfies Q8 for D23.1; `AC-D23.1.1`'s two behavioural measurables are kept as post-fix guards |
| PA-D23-4 | The `_row_data` fix is the narrow `pop(row, None)` around the existing shift (not a table rebuild), keeping field-key binding unchanged | R50 mitigation and DG32: a rebuild would discard cached FieldKey-bound values and risk `_rebuild_table`/`_set_cell` regressions (`AC-D23.2.4`) |
| PA-D23-5 | The new coverage adds a **last-row** assertion and (optionally) a first/only-row assertion in `tests/test_watchlist_add_remove_d22.py`; the existing middle-row test is kept unchanged | `AC-D23.2.3` requires a case that fails pre-fix; the middle-row case provably passes pre-fix; `AC-D23.2.4` requires the existing cases to stay green |
| PA-D23-6 | Phase 3's reconciliation splits by artifact owner: **Validator** edits `docs/architecture.md` `S3` / `plan_notes.md`; **Task Manager** edits `AC-D22.2.3` in `docs/tasks/task-graph.json`; **Build** only implements + tests | `AC-D23.1.4`'s correction record assigns exactly these owners; Plan does not write those canonical files |
| PA-D23-7 | The baseline for the non-regression run is the **712** D22 tests (plus the new D23 cases); D1–D22 criteria are re-affirmed, not re-planned | `requirements.md` records the D22 build green at 712 tests; D23 changes no D22 feature criterion |
| PA-D23-8 | No `ibapi` version bump — D23 makes the code honest about the pinned surface rather than changing the dependency | Existing-repo hard constraint; no stack change; ESC-030's suggested direction is the guard, not an upgrade |
| PA-D23-9 | The wire cancel stays uncalled by production after the fix | A54/source-validated: no production caller exists; the method is corrected for forward-correctness "if/when a caller is added" |
| PA-D23-10 | AC-G.1 (visual reference gate) does not apply — D23 has no UI-visual decision (no icon/placement/colour/label/size choice) | Both findings are implementation/state correctness with documented, non-visual outcomes |

## Flagged Issues

**None.** Both D23 findings are satisfiable exactly as written on the existing stack, with no
requirements gap:

- D23.1's required behaviour is fully determined by the source evidence (the pinned `ibapi` surface)
  and is implementable as a capability-guarded, documented cancel with no dependency change
  (`DG45` records this and is `addressed`).
- D23.2's required behaviour is a mechanical state-bookkeeping fix with a measurable invariant and a
  pre-fix-failing test.

Two items are **cross-owner handoffs recorded in Phase 3, not requirements gaps** and must not be
mistaken for escalations: (i) the **Validator** records the `S3` reconciliation in
`docs/architecture.md`; (ii) the **Task Manager** corrects task-level `AC-D22.2.3` in
`docs/tasks/task-graph.json`. Both are directed by the binding correction record in `AC-D23.1.4`
and neither requires a requirements decision.

**D23.1 verification note (RC-1 closure — not a gap).** Validation pass 1 offered two paths:
(a) specify a genuine pre-fix-red check, or (b) declare none achievable and record a
Q8-applicability / accepted-gap note. Plan takes **(a)**: a code-shape/source assertion on
`cancel_contract_details` is genuinely red on the current file and green after the guard (see
Phase 1, S16, PA-D23-3) — the Validator independently re-ran the AST/source check and confirmed the
bare `self.client.cancelContractDetails(...)` access is present pre-fix and the `getattr(..., None)`
guard is absent. No Q8 gap remains, so **no accepted-gap or Q8-applicability note is recorded** —
D23.1 satisfies Q8 through that assertion, and its behavioural tests are honestly labelled post-fix
guards. This is a plan-level verification correction, **not** a requirements defect:
`AC-D23.1.1`'s stated behaviour is implementable and is implemented by S3.

---

Validation: the D1–D22 baseline above is **built and green** at **712 tests** (D1–D21 at commit
`286341e`, 673 tests; D22 uncommitted), independently re-run by the Validator. The **D23 increment**
(Batch 17) is **approved**: validation of `docs/plan_proposal.md` / `docs/architecture_proposal.md`
returned `Status: APPROVED` (see `docs/plan_review.md`), and the three phases above (Phases 1–3) are
the canonical plan for Task Manager. This artifact replaces the previous D22 canonical plan; the D22
phases remain recorded in `docs/architecture.md` (`## D22 increment`) and the task graph.

Handoff: canonical set complete — `docs/architecture.md` (`## D23 increment`, S3 reconciled),
`docs/plan.md` (this file), `docs/plan_review.md` (`Status: APPROVED`), and `docs/plan_notes.md`
(RG-D23-1, no escalation).

Status: READY_FOR_TASK_MANAGER

---

## D24 / D25 / D26 / D27 / D28 — as-built / OWNER-APPROVED 2026-10-14, merged to `main`

**Status: as-built / APPROVED (owner decision 2026-10-14, Q41).** The former "DRAFT, owner review
required" markers are **cleared**; `requirements.md` carries D24–D28 as `as-built / APPROVED
2026-10-14`, and this plan describes what actually shipped. D1–D23 are not reopened.

Phases 1–4 of the session/pacing/correctness program are **as-built and merged to `main`**
(all ancestors of `b366b19`): Phase 1 = **D26** order-path safety (779 passed, `5d4daf4`);
Phase 2 = **D27** correctness sweep (819 passed, `69a2313`); Phase 3 = **3a** pacing off the
GUI thread + **3b** `TickerSession` keystone (D28.2) + **3c** pop-outs/`AC-D24.9` + **3d** headless
alarm monitor (D25) (855 passed, `ba28c08`); Phase 4 = **4a** rolling-600 s historical pacing
(D28.3) + **4b** D28.4 render split/study cache/bisection/retention + **4c** explicit teardown
(D28.5) + **4d** test hardening (D28.6) (898 passed, `3d12821`).

**Owner resolutions carried here (2026-10-14 — no architectural decision changed):**

- **DEC-1 / Q41** — per-session alarm evaluation is the intended behaviour: a symbol's alarms are
  evaluated by its own `TickerSession` on every aggregated bar, so they fire while the main chart
  shows another ticker and with zero views open (headless, D25). The D25 conflict is resolved.
- **DEC-2** — D25 evaluation is **event-driven** (A58): 1-minute tracking granularity via
  `BarAggregator("1m")`, evaluation on every 5-sec push (second-level firing latency); the literal
  once-per-minute poll is rejected.
- **DEC-3** — `AC-D24.9` persists the pop-out set across restarts (symbol / timeframe / mode /
  ext-hours / geometry in SQLite; re-created on launch). Alarms/drawings/studies already persist via
  the existing stores. Pop-out timeframe/mode frozen at creation is accepted long-term (A56).
- **DEC-4 → RESOLVED (Q42)** — the per-run **"gated in TWS" planning constraint is retired**, so
  **D26 is planned/decomposed against the live-order path**. The retained safety behaviour is
  unchanged and still binding: `config/settings.py::check_live_port` fails fast unless
  `IBKR_PORT == 7496`; every order requires explicit user action; confirm dialogs remain; and no
  automated test transmits an order or connects to live TWS (Q9). The former "G5" reference in
  DEC-4 is dangling (no such item exists) and is recorded as resolved.
- **Q43** — pop-out **always-on-top defaults OFF** (standard windows; per-window toggle via the
  header context menu) — `AC-D24.10` / A66, matching
  `ui/popout_window.py::PopoutChartWindow._always_on_top` / `::PopoutChartWindow._toggle_always_on_top`.

**As-built feature detail (verified against the merged code 2026-10-14 — see the plan-vs-code
verification section at the end of this file):**

| Feature | As-built | ACs |
|---|---|---|
| **D24** pop-out chart windows | `ui/popout_window.py::PopoutChartWindow` — chrome-free (28px header `SYMBOL · timeframe · mode` + close; no toolbar/docks/status bar), `ChartPanel(editable=False)` (drawing / alarm-placement / study / timeframe / mode controls disabled — interaction only; overlays still render, crosshair/zoom/pan work); timeframe/mode/ext-hours frozen at creation (A56); `MAX_POPOUTS` (`config/settings.py::MAX_POPOUTS` = 10) — the 11th is **refused with a status-bar message** (`ui/main_window.py::MainWindow._open_popout`), the affordance is *not* `setEnabled(False)`-ed; opened while disconnected → cached bars render and the subscription starts on connect, with **no per-pop-out "connecting" indicator** (main window `conn_badge` only); always-on-top default OFF with per-window toggle; `AC-D24.9` restore via the additive `popouts` table + `data/popout_store.py`; one refcounted `reqRealTimeBars` per symbol; per-symbol sync of bars/studies/zones/lines/alarms with the main chart the sole writer (A64); `load_chart(symbol, timeframe, extended_hours)` parameterised | `AC-D24.1`–`AC-D24.10` |
| **D25** headless alarm monitor | `services/alarm_monitor.py::AlarmMonitor` + `AlarmStore.symbols_with_active_alarms()`; every alarmed symbol with no open view gets an ordinary headless `TickerSession` (`views == 0`, `monitored == True`) — one 5-sec RT sub, `BarAggregator("1m")`, per-push `evaluate_alarms`; `prev_price` seeded from the 1m cache else first-tick-no-eval (A59); **zero historical requests** (A60); reconcile on connect / alarm add-update-delete-rearm-trigger / view attach-detach; teardown only when `views == 0 AND NOT monitored` (A61); pacing guardrail with a warning naming unmonitored symbols (A63) | `AC-D25.1`–`AC-D25.5` |
| **D26** P0 real-money safety | bracket children on the **opposite** side; `id_manager.reserve(3)` before transmit; SL/TP dialog honestly labelled (no silent order transmission); MKT buttons fixed (qty from input, qty>0 guard); `IBKR_PORT == 7496` fail-fast + badge derived from the verified port and `AccountType`; explicit Buy/Sell side; single `validate_order()` gate; `reqGlobalCancel()` kill switch + per-ID cancels; reject/connection codes promoted to first-class alerts; order entry blocked while disconnected; orders removed from the realtime throttle onto their own `OrderRateLimiter` | `AC-D26.1`–`AC-D26.10` |
| **D27** P1 correctness | `_last_chart_price` never moves backward; MACD/ICT/gaps/VIX overlays plot in display-x; reconnect works (`connect()` not `eConnect`; subs type-tagged and replayed with rebound reqIds); per-session stream-health state + backoff retry; positions priced from a `symbol → last_price` map; `reqPositions`/`reqAccountSummary` on connect; bar-period backfill-gap detection; ET-anchored daily/4h aggregation; aggregator primed from trailing 5-sec history; drawing style edits persist | `AC-D27.1`–`AC-D27.11` |
| **D28** P2 robustness & scale | pacing never sleeps on the GUI thread (`PacingExceeded` + `singleShot` deferral; orders get their own limiter); the single-symbol data plane extracted into `TickerSession` (D28.2 — the keystone for D24/D25); rolling-600 s historical pacing (~60 chunks/wave, retry-once on error 162); bounded `_bars` (`SESSION_BAR_CAP = 5000`) + static-history/live-bar render split + study cache actually read + bisection + incremental collapse tails; explicit `closeEvent` teardown (`_closing` flag, reader thread joined with a timeout); test hardening | `AC-D28.1`–`AC-D28.7` |

Their full as-built record — components, data model, integration points, non-functional approach
and the per-subsystem **as-built → target delta table** — lives in `docs/architecture.md`
(§ *D24 / D25 / D28 increment*, § *Pop-out window architecture (D24)*,
§ *Headless alarm monitor (D25)*, § *As-built → target delta table*). No separate plan-level phase
breakdown was recorded for these increments on the docs branch; the architecture delta table plus
the table above are the as-built record.

## D36 — Footprint charts (as-built 2026-10-13)

Scope: D36 only — footprint charts (bid×ask volume-at-price), the P0 item of the D36–D40 program.
Planned in `~/workspace/ndthinkchart-doc-drafts/plan-d36-d40-draft.md` (36.1–36.5), validated
(APPROVE WITH CHANGES + delta re-validation), owner-approved, built on `feat/d36-footprint` @
`89fe152`, Code Reviewer **APPROVED** after rework. D1–D35 not reopened.

### Work items (as-built)

| # | Item | As-built |
|---|---|---|
| 36.1 | Tick-history client | `ibkr/tick_history.py::TickHistoryManager` — backward paging in 1000-tick windows (`BID_ASK` + `TRADES`), sequential, pacing-counted via `pacing_manager` (never sleeps); zero `reqTickByTickData` (registry + source-scan asserted). Bridge: 2 signals (`historical_ticks_bid_ask` / `historical_ticks_last`); `ibkr/client.py`: 2 overrides (`historicalTicksBidAsk` / `historicalTicksLast` — the planned histogram override was dropped with the histogram path, deviation 1) |
| 36.2 | Footprint aggregation | `services/footprint_service.py` — per-level `{bidVol, askVol, delta=askVol−bidVol}` from BID_ASK ticks; per-level trade volume + trade count from TRADES ticks. Bounded waves (≤60 requests/wave) under the binding priority order (D27 reconnect replay > D28 backfill > D36 completed-bar backfill > D36 forming-bar refresh > D39 baseline prime); viewport-newest-first; lazy-fill on scroll/timeframe change; structural per-bar loading/unavailable states; forming-bar incremental refresh follows the selected metric |
| 36.3 | Index proxy | `ibkr/contracts.py`: `INDEX_PROXY` (SPX→ES, NDX→NQ, DJI→YM, RUT→RTY), `resolve_footprint_contract()` via the existing `_front_month()` schedule, `footprint_cache_key()` — all keys use the RESOLVED contract (e.g. `ESZ6`), never the continuous symbol; re-resolved on session start and daily |
| 36.4 | Footprint cache | `data/footprint_cache.py` + additive `footprint_cache` table — one compressed JSON blob per (resolved contract, date, timeframe); read before backfill, write on completion; **only** SPX/SPY/QQQ/ES-front/NQ-front (owner decision); all other symbols re-fetch per session |
| 36.5 | Rendering | `ui/footprint_item.py` + session/chart wiring — **display-style toggle** (classic bid×ask bars vs heatmap-shaded candles) **× metric selector in heatmap mode** (per-level volume vs per-level trade count); classic is volume-only; intraday + daily; completed bars static (0 static regens on 100-tick burst); default OFF (owner, 2026-10-13) |
| 38a.0 | ibapi 10.51.01 alignment (gate precondition) | `requirements.txt`: `ibapi>=9.81` → `ibapi-latest==10.51.1` (plain `ibapi==10.51.01` not on PyPI — verified). Full suite green on the aligned version before any D36 code. Fixed real 10.51.1 breakage: `EWrapper.error` 5-arg; (reviewer-found) `orderStatus` 11th param `mktCapPrice`; `updateMktDepthL2` 8th param `isSmartDepth` |

### As-built deviations from plan

1. **`reqHistogramData` path removed (material).** The method signature is
   `reqHistogramData(tickerId, contract, useRTH, timePeriod)` — **no date parameter**, so
   per-bar histograms are impossible. The planned histogram path (36.1/36.2/§7) was deleted
   from code and docs. Tick-count metric now comes from the same TRADES tick pages as volume:
   **one dataset, two metrics, zero new requests** — strictly better than plan, and the
   owner's "same per-level data" decision is now literally true. *(Recorded in
   `docs/phase-changelog.md`, Phase D36 — Decisions and review finding A1; it is also why
   D36's real bridge/client surface is 2 signals + 2 overrides rather than the pre-removal
   "3 + 3".)*
2. **Footprint default OFF** (owner did not specify; reviewer agreed — pacing-expensive opt-in).
3. **10.51.1 lesson:** the 38a.0 "re-verify signatures" gate caught `error()` but missed
   `orderStatus`/`updateMktDepthL2` (reviewer B1/B2 — both would have raised TypeError in
   production). On future API upgrades, re-verify **ALL** `EWrapper` overrides against the
   wheel, not just the plan-named ones.

### Pacing (binding, as-built)

Footprint requests share the D28 4a rolling 600s historical budget (≤60/10min) via
`pacing_manager` — the single owner. No histogram budget (deleted). Priority order:
D27 reconnect replay > D28 backfill waves > D36 completed-bar backfill > D36 forming-bar
refresh > D39 baseline prime. `PacingExceeded` + `QTimer.singleShot` deferral everywhere;
nothing sleeps on the GUI thread.

Status: BUILT — Code Reviewer APPROVED 2026-10-13; 927 tests green; built on
`feat/d36-footprint` @ `89fe152`, merged to `main` at `efffc51` (an ancestor of `b366b19`).
**Acceptance criteria `AC-D36.1`–`AC-D36.5` are now authored** in `requirements.md` (`### D36`,
Q45/DG46 — previously cited while undefined); the work items above are consistent with them
(`AC-D36.3`: `reqHistoricalTicks` only, zero `reqTickByTickData`, no mock/stub endpoint in the
production tree).

---

## D37 — Microstructure (as-built 2026-10-13)

Scope: D37 only — depth heatmap + auction imbalance. Planned in
`~/workspace/ndthinkchart-doc-drafts/plan-d36-d40-draft.md` (§3, items 37.0–37.5), validated
(APPROVE WITH CHANGES + delta re-validation), owner-approved, built on `feat/d37-microstructure`
@ `69c2d66`, merged to `main` @ `9958891` (now on `origin/main`), Code Reviewer **APPROVED** (no blocking
findings). D1–D36 not reopened.

### Work items (as-built)

| # | Item | As-built |
|---|---|---|
| 37.0 | Substrate S0 — generic-tick plumbing | `ibkr/client.py`: `tickGeneric`/`tickString`/`tickNews` overrides (10.51.1-verified — `tickNews` is 6-arg incl. `extraData`); `ibkr/bridge.py`: 3 new signals; `ibkr/market_data.py`: `req_mkt_data(contract, generic_ticks="")`; per-symbol generic-tick union (`"225"` auction, `"292"` news push, `"456"` IB Dividends — D38 use) merged into the single per-symbol subscription; register/deregister re-subscribes only when the union changes |
| 37.1 | Depth heatmap data | `services/depth_heatmap.py` — price-keyed live book from the depth op stream; 60×30s price×time matrix; imbalance `(bidVol−askVol)/(bidVol+askVol)` over top-5 AND top-10 recomputed per op; refcounted per symbol (feed lives only while `views > 0`); depth replays on reconnect via the D27 path; `isSmartDepth` carried as row provenance for SMART-row disambiguation |
| 37.2 | Heatmap overlay | `ui/depth_heatmap_item.py` — price-aligned overlay strip at the chart's right edge (live layer); 100-op burst → 0 static regens (D28 discipline holds) |
| 37.3 | Auction chip | Header chip: imbalance side + paired shares + indicative price from ticks **34**/**35**/**36** (tick **61** regulatory imbalance when present); highlights during 9:25–9:35 / 15:55–16:05 ET; click expands a popover; absent ticks → explicit "no auction data" state |
| 37.4 | Degradation | IBKR error **354** → explicit `no_entitlement` state, feed cancelled, panel shows "Depth subscription required" + status bar `Depth [354]: <server message>` — never silently empty. Depth feeds refcounted 3–60 with separate sub-manager tags `DEPTH_HEATMAP`/`S0_TICKS` (the DOM's `unsubscribe_all_of_type(DEPTH)` would otherwise wipe session feeds) |
| 37.5 | MD line-budget guard | `services/md_line_guard.py` — owns the §7 market-data-line accounting: `ok` <90, `approaching` 90–99 (warns naming the symbol), `exceeded` ≥100 (refuses naming the symbol); S0's per-symbol reqMktData lines counted explicitly |

### As-built deviations from plan

1. **Depth heatmap default ON — owner-confirmed 2026-10-14 (Q44, assumption A67).** The plan did not
   specify a default; the code defaults ON (`ui/chart_panel.py::ChartPanel.depth_heatmap_item` adds
   `DepthHeatmapItem` unconditionally, `ui/chart_panel.py::ChartPanel._depth_enabled_ui` is `True`).
   The reviewer recommended **OFF** for
   consistency with D36's OFF default and to avoid burning depth budget by default; the **owner
   confirmed ON** on 2026-10-14, so the shipped default stands and the reviewer's OFF suggestion is
   an accepted-and-overridden trade-off (recorded as an architecture risk, not an open question).
   D36 footprint stays **OFF** (owner decision 2026-10-13).
2. **Drive-by fix (latent main-branch bug):** `primary_session` was referenced 26× but never defined — any footprint/depth toggle would have raised `AttributeError`. Fixed with a properly backed property (`ui/main_window.py`).
3. **Known limitation (recorded in code):** if TWS delivers delayed depth *instead of* the 354 error, it would render unlabeled — the 354 path is handled; delayed-depth labeling is a follow-up if the behavior is ever observed.

### Pacing (binding, as-built)

Depth feeds count against the 3–60 simultaneous budget (refcounted per symbol, sub-manager tags); S0 generic ticks ride the single per-symbol subscription (no new MD lines per feature). Market-data lines guarded at 100 by `md_line_guard` (warn at 90, refuse at 100, always naming the symbol). `pacing_manager` remains the single owner for historical requests; nothing sleeps on the GUI thread.

Status: BUILT — Code Reviewer APPROVED 2026-10-13; 947 tests green; merged to `main` @ `9958891` (an ancestor of `b366b19`).
**Acceptance criteria `AC-D37.1`–`AC-D37.5` are now authored** (Q45/DG46); **depth heatmap default ON is
owner-confirmed 2026-10-14 (Q44/A67)** — see deviation 1 above.

## D38 — Events & news (as-built 2026-10-13)

Scope: D38 only — event markers (IBKR tick-59 dividends + yfinance earnings/splits/dividends) and the
news-for-holdings digest. Planned in
`~/workspace/ndthinkchart-doc-drafts/plan-d36-d40-draft.md` (§4, items 38a.1–38b.2), validated
(APPROVE WITH CHANGES + delta re-validation), owner-approved, built on `feat/d38-events-news`
@ `b893911`, merged to `main` @ `8599ce4` (now on `origin/main`), Code Reviewer **APPROVED** (no blocking
findings). D1–D37 not reopened. **WSH is removed from D38 entirely** (owner decision 2026-10-13);
yfinance is the sole secondary source.

### Work items (as-built)

| # | Item | As-built |
|---|---|---|
| 38a.1 | News client | `ibkr/news.py::NewsManager` — `reqNewsProviders()` → the user's actual entitlement list; per-holding `reqHistoricalNews(...)` issued **sequentially via a FIFO queue** (no headline-fetch storm on digest open), pacing-aware; `reqNewsArticle(providerCode, articleId)` on headline click. Bridge: `historical_news` / `news_article` signals; `ibkr/client.py`: 4 new overrides (10.51.1 arg-for-arg verified) |
| 38a.2 | Digest dock | `ui/news_digest_dock.py` — **repositionable, closable dock**, reopenable from a minimal View-only menubar (`View → News Digest`, `Ctrl+Shift+N`; the app had no menubar — added, drive-by). Refresh = **backfill on open** + **live push primary** (generic tick `"292"` → `tickNews` → headline prepended) + **15-min periodic re-query backstop** (QTimer, only while the digest is open). Non-charted holdings get lightweight headless `TickerSession`s while the digest is open (D24 headless semantics), torn down on close; their S0 lines are counted in the MD-line budget. Honest states: "No API news subscription" (entitlement honesty — API news requires API-specific subscriptions), "No holdings", "Headlines unavailable" — never silently empty |
| 38b.1 | Event-provider layer | New `data/events/` package: `provider.py` (`Event` dataclass, corporate-events-only guard **rejecting non-corporate types at the provider boundary** — AC-D38.4, `EventProvider` ABC, defensive tick-59 dividend parser that **never raises**), `ibkr_source.py` (dividends from session tick-59 state, **skips futures contracts** — no dividend stream there), `yfinance_source.py` (SQLite per-symbol cache: 24h TTL, **6h revalidation for events within 7 days** so corrections propagate; single `QThread` worker, **≥1s between calls**, own connections — never on the IBKR pacing budget; lazy import; `failed_at` distinguishes outage from loading). `requirements.txt`: **`yfinance==1.7.0`** with a re-pin policy comment (re-pin quarterly or whenever Yahoo breaks the library; every re-pin re-runs the full offscreen suite). **yfinance is the sole secondary source — no other external API** (owner-mandated) |
| 38b.2 | Event markers | `ui/event_marker_overlay.py` — time-axis markers with **distinct icon/color per type**: earnings gold ◆E, dividend green ●D, split blue ▲S; countdown label ("Earnings in 3d") for the next upcoming event. Source priority **IBKR tick-59 dividends first → yfinance** (earnings/splits + dividend fallback); IBKR-first merge **drops same-date yfinance dividends**. **No-data rule (owner):** both sources empty → explicit "no event data" state, logged for the owner (owner decides on feature removal). Markers are **id-keyed, not date-keyed** — date corrections move the marker |
| S0 | Generic-tick union | Extended to `"225,292,456"` (auction, news push, IB Dividends); new `s0_register_many`/`s0_deregister_many` batch helpers (single resync — fixes double re-subscribe churn); one-subscription-per-symbol preserved |

### As-built deviations from plan

1. **Drive-by fix (self-fixed by the Coder):** duplicated `_on_auction_tick` body tail — dead code removed.
2. **Digest dock init-order fix:** signal wiring deferred to first dock open (the digest's sessions don't exist at construction).
3. **Minimal View-only menubar added** (the app had none) — just `View → News Digest` (`Ctrl+Shift+N`), no other menu surface.
4. **Reviewer advisory A1 applied post-review:** two merge tests re-pointed at the real `TickerSession._merge_events` (they had been asserting on a helper). A2 (harmless double `events_updated` emit) and A3 (`get_earnings_dates(limit=12)` usage validated) required no code change.

### Pacing (binding, as-built)

`reqHistoricalNews` fetches are sequential per holding via the FIFO queue (pacing-aware, counted by `pacing_manager`); no historical-request storm on digest open. yfinance HTTP traffic is **not on the IBKR pacing budget** — it has its own polite self-throttle (sequential, ≥1s between calls, single-digit concurrency) plus the per-symbol 24h cache (HTTP only on cache miss). S0 generic ticks (`"292"`, `"456"`) ride the single per-symbol subscription (no new MD lines per feature); headless digest sessions' S0 lines are counted in the MD-line budget. `pacing_manager` remains the single owner for IBKR pacing; nothing sleeps on the GUI thread.

Status: BUILT — Code Reviewer APPROVED 2026-10-13; 970 tests green; merged to `main` @ `8599ce4` (an ancestor of `b366b19`).
**Acceptance criteria `AC-D38.1`–`AC-D38.6` are now authored** (Q45/DG46); the plan's D38 items are
consistent with them (`AC-D38.4`: corporate-events-only guard rejecting non-corporate types at the
provider boundary, yfinance the sole secondary source).

## D39 — Volume-burst alerts + symbol search (as-built 2026-10-13)

Scope: D39 only — symbol search (39.1), volume baseline service (39.2), `volume_burst`
alarm kind (39.3), index proxy for burst (39.4). Planned in
`~/workspace/ndthinkchart-doc-drafts/plan-d36-d40-draft.md` (§5, items 39.1–39.4), validated
(APPROVE WITH CHANGES + delta re-validation), owner-approved, built on
`feat/d39-burst-search` @ `90b01e7` (+ post-review advisories `0b50fb7`), merged to `main`
@ `83f792a` (now on `origin/main`), Code Reviewer **APPROVED** (no blocking findings). D1–D38 not reopened.

### Work items (as-built)

| # | Item | As-built |
|---|---|---|
| 39.1 | Symbol search | New `services/symbol_search.py`: debounced `reqMatchingSymbols(pattern)` (**≤1 per 300ms** of typing), `symbolSamples` override verified **arg-for-arg against the 10.51.1 wheel** (`reqId, contractDescriptions`); ≤16 samples, 5s timeout, exactly-once correlation, disconnected/empty guards. Search box in the **watchlist header** — expanding, capped 180px, **zero minimum width** (a 110px minimum broke D17 dock tests). Results popup: symbol·secType·exchange; select → bounded contract resolution → `load_chart` |
| 39.2 | Volume baseline service | New `services/volume_baseline.py`: **robust median/MAD** (never mean/stddev) per (resolved-contract, time-of-day bucket), **N=30**, ET minute-of-day buckets, per-minute normalization. Three-tier chain: (1) persisted `volume_baseline` table (**`samples` JSON column** for exact recomputation) — the steady state after days of use; (2) one-time `BarCache` prime, **local only, zero IBKR requests**; (3) rolling-30 fallback. Guards (binding): **1.0/min volume floor** (no evaluation on dust), **5-bar warm-up** with explicit "warming up (n/5)" status (the early-session gap is documented, not silent), **5%-of-median MAD floor** (flat data scores z=0; real bursts on flat baselines fire finite). **Roll invalidation:** baseline keyed on D36's `footprint_cache_key` (front month embedded); key change tombstones in-session — DB rows for the old contract cannot resurrect; `record()` consults the tombstone set (post-review A2) |
| 39.3 | `volume_burst` alarm kind | `data/models.py::Alarm`: `kind: str = "price"` + `params: dict` (JSON; burst params: z-threshold, window N) — additive DB migration, price rows untouched. New `evaluate_volume_burst()` in `services/alarm_service.py`: robust z of the bar's volume vs the baseline service; fires when z ≥ **user-tunable threshold** (`params["z_threshold"]`, default 4.0) — z-score semantics throughout, no K-multiple language (C39.1). Wired into `TickerSession._on_aggregated_bar`'s per-push evaluation alongside `evaluate_alarms` (per-aggregator-push — coincides with 5s only on short timeframes, C39.3): forming bars evaluated (**conservative — partial volume ÷ full minutes can only understate**), completed bars recorded; **identical** persist/trigger/rearm semantics (`AlarmStore.mark_triggered`, `alarm_triggered` toast+sound exactly once, grouped emission, `AlarmMonitor` reconcile, headless included). Chart overlay skips non-price alarms; `evaluate_alarms` is kind-filtered — a price=0.0 burst alarm can never fire as a price alarm (genuine pre-fix bug, fixed as part of 39.3). **No generic rate ticks needed** — evaluation uses session bar volumes (the specified N=30-bars design) |
| 39.4 | Index proxy for burst | SPX/NDX/etc. burst alarms carry `params.proxy`/`proxy_label` from D36's `INDEX_PROXY` (**reused, not duplicated**). `AlarmMonitor.reconcile` routes to the **proxy tape's session** (ensured headless); **no session is created for the index itself**. Baseline keys on the resolved proxy contract and invalidates on roll (mirror of 36.3's never-compare-across-contracts rule). Alarm labelled proxy-derived — e.g. "Volume burst on ES tape (z=9.4)" |

### As-built deviations from plan

1. **No company name in search results (material).** The plan said results show "symbol + company name + exchange"; 10.51.1's `ContractDescription` carries only `contract` + `derivativeSecTypes` — no company-name field exists. The requirement's "company name" was an API-docs oversell (reviewer-verified). Results show symbol·secType·exchange; full details resolve on selection — the right call.
2. **Search-box sizing:** expanding with 180px cap and zero minimum width (a 110px minimum broke D17 dock tests).
3. **Reviewer advisory A1 applied post-review:** z-threshold spinbox floor raised **0.5→1.0** in both alarm dialogs + tooltip caution (below 1.0 fires on normal variance).
4. **Reviewer advisory A2 applied post-review:** `record()` consults the in-session tombstone set (tombstone symmetry — old-contract DB rows cannot resurrect on roll).
5. **Pre-fix bug fixed in 39.3:** kind-unfiltered `evaluate_alarms` would have let a `volume_burst` alarm with `price=0.0` fire as a price alarm; `evaluate_alarms` is now kind-filtered.

### Pacing (binding, as-built)

D39 adds **no new IBKR budget load**: search requests are debounced user-initiated traffic
(`reqMatchingSymbols` — not on the historical rolling-600s budget; ≤1 per 300ms of typing);
the baseline prime is local-only (`BarCache` read — zero IBKR requests); burst evaluation rides
the per-aggregator-push path on session bar volumes (no rate ticks 54/55/56/63/64/65 needed).
`pacing_manager` remains the single owner for IBKR pacing; nothing sleeps on the GUI thread.

Status: BUILT — Code Reviewer APPROVED 2026-10-13; 1009 tests green; merged to `main` @ `83f792a` (an ancestor of `b366b19`).
**Acceptance criteria `AC-D39.1`–`AC-D39.5` are now authored** (Q45/DG46), with `AC-D39.5` carrying an
explicit AMBIGUITY note (the shipped tests label only `AC-D39.1`–`AC-D39.4`, so `.5` is the batch
regression criterion authored from the baseline behaviour plus the `AC-D37.5`/`AC-D38.6` convention).

## D40 — TWS daily-lifecycle pause/resume (as-built 2026-10-13)

Scope: D40 only — disconnect classification (40.1), pause (40.2), resume (40.3), transient
path (40.4). Planned in `~/workspace/ndthinkchart-doc-drafts/plan-d36-d40-draft.md` (§6,
items 40.1–40.4), validated, owner-approved (TWS only, never Gateway; Aniket closes TWS
nightly and logs in manually each morning), built on `feat/d40-tws-lifecycle` @ `4ac2453`
(+ review fixes `d6f38e8`), merged to `main` @ `b366b19` (now on `origin/main`), Code Reviewer
**CHANGES REQUIRED → rework → APPROVED**. D1–D39 not reopened.

### Work items (as-built)

| # | Work item | Files | Tests → AC |
|---|---|---|---|
| 40.1 | **Disconnect classification.** New `ibkr/client.py::DisconnectClass` (`TRANSIENT` / `TWS_GONE`). `connectionClosed()` classifies TWS-gone per ibapi's own docstring ("fires when TWS closes the sockets connection … or when TWS is shut down"), records the classification before emitting `disconnected`, and **restarts the backoff reconnect loop** — drive-by fix of a real bug: the old code stopped polling after `connectionClosed` and scheduled nothing, so the app could never notice a morning TWS login without a restart. Backoff base 2s capped 16s (~1 gentle attempt/16s overnight). Error 502 during paused backoff → debug log (no all-night status-bar spam); a 502 at startup with no prior connection still surfaces. `_last_disconnect_class` reset on connect | `ibkr/client.py` | Simulated close → TWS-gone; simulated blip → transient → AC-D40.1, AC-D40.4 |
| 40.2 | **Pause.** `AlarmMonitor.pause_all()` records per-symbol pause-start, sets `monitoring_paused` on every alarmed session; both evaluation entry points (price-alarm and burst-alarm in `_on_aggregated_bar`) gate on the flag — headless included via the same path; proxy burst alarms pause with their tape. `conn_badge_text(..., monitoring_paused=...)` shows **"Monitoring paused — TWS disconnected"** in amber `#fbbf24`, never green | `services/alarm_monitor.py`; `ui/main_window.py` (badge) | TWS-gone → badge shows paused state, all symbols marked paused (assert, mocked) → AC-D40.1 |
| 40.3 | **Resume.** On `connected`: the as-built D27 replay re-issues subscriptions, then `reconcile()` FIRST, then `resume_all()`: every session's `prev_price` re-seeded to None (**AC-D25.3 first-tick-no-eval guard** — no phantom triggers), staged subscribes finished, gap intervals returned. Gap report surfaced in the status bar ("ES, NQ unmonitored 22:14–09:40"). Alarms created while TWS is down are staged (`_monitor_subscribe_pending`) and covered on resume. Backfill waves in flight → generation fencing applies (existing) | `services/alarm_monitor.py`; `ui/ticker_session.py`; `ibkr/client.py` | Reconnect after pause → subs resume, price through an alarm level fires once, resume alone fires nothing; gap report names symbols + duration → AC-D40.2, AC-D40.3 |
| 40.4 | **Transient path unchanged.** Poll-driven drops and 1100/1101/1102 stay transient: fast D27 reconnect, no pause UI, no gap accounting, `prev_price` untouched | `ibkr/client.py` | Transient drop → fast reconnect, no pause state → AC-D40.4 |

### As-built deviations from plan

1. **B1 (blocking, found in review, fixed before merge).** The Coder built resume as `resume_all`-then-`reconcile`; the reviewer showed reconcile-created sessions then took the normal path with a stale cache seed — a phantom-trigger hole. Fixed by swapping the call order to reconcile-then-resume plus a staged path for reconcile-created sessions (`monitoring_paused=True`, `last_chart_price=None`, subscribe deferred). Regression test `test_d40_2_resume_session_recreated_mid_pause_no_phantom` verified to **fail on the old order** (stale 99.0 seed) and **pass on the fix**.
2. **Reviewer advisory A1 applied:** `_last_disconnect_class` reset on connect (a stale TWS_GONE would otherwise downgrade a later transient drop to the paused path).
3. **Reviewer advisory A2 applied:** cancel-then-arm reconnect timer (no double-arm).
4. **Drive-by fix (40.1):** reconnect loop never restarted on `connectionClosed` — the app could never detect a morning TWS login without a restart (reviewer-verified real).

### Pacing (binding, as-built)

D40 adds **no IBKR budget load**: pause emits no requests; resume re-issues the as-built D27 replay (existing pacing-aware paths); the overnight backoff is ~1 reconnect attempt per 16s (connect handshake only, no data requests).

Status: BUILT — Code Reviewer CHANGES REQUIRED → rework → APPROVED 2026-10-13; merged to `main` @ `b366b19` (now on `origin/main`).
**Acceptance criteria `AC-D40.1`–`AC-D40.5` are now authored** (Q45/DG46), with `AC-D40.5` carrying an
explicit AMBIGUITY note (the shipped tests label only `AC-D40.1`–`AC-D40.4`). The test figure quoted
per landing commit (`1020 tests green`) is the **last recorded green** run; it is also the
**re-verified current** figure on this checkout (2026-10-14): **1,020 passed / 0 failed out of 1,020
collected** (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q`). The four
previously-open offscreen D19/D20 toolbar-geometry assertions
(`tests/test_toolbar_d20.py::test_T62_T02/T04/T05`, `tests/test_toolbar_scroll_d19.py::test_T53_T02`)
were fixed by `99fb8fa` and are **no longer open**. This agrees with
`docs/phase-changelog.md` (Phase D40 — "Tests: 1020 passing, 0 failing (offscreen)").

---

## Plan-vs-code verification — D24–D40 (owner-directed 2026-10-14, Q41/DG53)

Every D24–D28 and D36–D40 feature in this plan was cross-checked against the merged code at
`b366b19` (the D40 merge; `origin/main` is now `262ec81`). **Result: the plan describes what shipped.** Drift found and corrected:

| Item | Drift | Correction |
|---|---|---|
| D24 pop-out cap (`AC-D24.5`) | `architecture.md` and this plan said the pop-out action is **"disabled at the cap"** | Rewritten: the 11th pop-out is **refused with a status-bar message** (`ui/main_window.py::MainWindow._open_popout`); the affordance is **not** `setEnabled(False)`-ed |
| D24 session signals | `architecture.md` named a single **`bars_updated`** signal | Rewritten to the shipped pair: **`bar_updated`** (incremental) **and `bars_refreshed`** (full replace) — `ui/ticker_session.py::TickerSession.bar_updated` / `::TickerSession.bars_refreshed` |
| D24 disconnected pop-out | Requirement asserted a **per-pop-out "connecting" indicator** | Removed/corrected: cached bars render and the subscription starts on connect; there is **no per-pop-out indicator** — only the main window's `conn_badge` (`ui/main_window.py::MainWindow.conn_badge`) |
| D37 depth heatmap default | This plan said **"owner decision pending … awaiting owner confirmation 2026-10-13"** | Rewritten as **owner-confirmed ON 2026-10-14** (Q44/A67); matches `ui/chart_panel.py::ChartPanel.depth_heatmap_item` / `::ChartPanel._depth_enabled_ui`; D36 footprint stays OFF |
| D24–D28 status | Plan/architecture described the increments as as-built but the requirements still carried "DRAFT" | Plan now states **as-built / OWNER-APPROVED 2026-10-14 (Q41)**; no DRAFT / unmerged / pending-owner-review wording remains |
| "gated in TWS" (DEC-4) | Plan/architecture still carried the retired gate | Removed/rewritten per Q42 — D26 is planned against the live-order path; the safety behaviour (`IBKR_PORT == 7496` fail-fast, explicit user action per order, confirm dialogs) is retained |
| `AC-D36.*`–`AC-D40.*` citations | Cited while undefined (DG46) | Re-checked against the now-authored text: `AC-D36.3` (ticks-only + no mock endpoint), `AC-D38.4` (corporate-events-only guard), `AC-D40.1`–`AC-D40.4` (classification/pause, resume-without-phantoms, gap report + staging, transient path) — **all consistent**; no citation needed changing |
| D36–D40 work items (36.1–36.5, 37.0–37.5, 38a.1–38b.2, 39.1–39.4, 40.1–40.4) | — | **No behavioural drift found in the first pass.** Verified against the merged code: tick-paging/`reqHistoricalTicks`-only, `INDEX_PROXY` + resolved-contract cache keys, `CACHEABLE_SYMBOLS` scope, `≤60 requests/wave` + the binding priority order, S0 union `"225,292,456"`, md-line guard 90/100, robust median/MAD with N=30 / 1.0-min floor / 5-bar warm-up / 5 % MAD floor, z-threshold default 4.0 (floor 1.0), and the D40 classification/reconcile-then-resume behaviour. **(A few counting/shape corrections were made in the follow-up pass — see below.)** |

**Dependency pins re-checked** (2026-10-14): `requirements.txt` reads `ibapi-latest==10.51.1` and
`yfinance==1.7.0` as recorded. **D23 capability guard re-checked:** the rebuilt `.venv` is on
`ibapi 10.51.01`, where `hasattr(EClient, 'cancelContractDetails')` is **still `False`** — the guard
remains required and is kept version-neutral in both artifacts.

**Verification anchors** (spot-checked in source at `b366b19`): `MAX_POPOUTS = 10`
(`config/settings.py:42`), `SESSION_BAR_CAP = 5000` (`:45`), `LIVE_PORT = 7496` /
`check_live_port` (`:11`/`:20`), `MAX_ORDER_NOTIONAL = 25000` (`:39`), `_always_on_top = False`
(`ui/popout_window.py:56`) + toggle (`:289`), `DepthHeatmapItem` added unconditionally
(`ui/chart_panel.py:368`) with `_depth_enabled_ui = True` (`:370`), `TickerSession` signal pair
(`ui/ticker_session.py:65–73`), pop-out cap refusal (`ui/main_window.py::MainWindow._open_popout`),
`CACHEABLE_SYMBOLS = {"SPX","SPY","QQQ","ES","NQ"}` (`data/footprint_cache.py:26`),
`MD_LINE_CAP = 100` / `MD_LINE_WARN_AT = 90` (`services/md_line_guard.py:16–17`),
`DEFAULT_Z_THRESHOLD = 4.0` / `MIN_WARMUP_BARS = 5` / `N_BASELINE_BARS = 30` /
`MAD_FLOOR_RATIO = 0.05` (`services/volume_baseline.py:58–66`), and the merge ancestry of
`89fe152`/`efffc51`/`9958891`/`8599ce4`/`83f792a` under `b366b19`.

### Follow-up verification — second pass (2026-10-14, after `99fb8fa` / `262ec81`)

A second, adversarial pass re-checked every D24–D40 work item, constant and citation against the
source at `262ec81` (the graph at `graphify-out/graph.json` was built at `b366b19` and is behind
those two commits, so nothing was taken from it unverified). Result: **no behavioural drift** —
every described behaviour is what the shipped code does. Six **record/claim** corrections were
applied (none architectural; all in `architecture.md` and/or this file):

| # | Correction | Where |
|---|---|---|
| 1 | The suite is now **1,020 passed / 0 failed**, not "1,016 passed / 4 failed … open": `99fb8fa` fixed the four offscreen D19/D20 toolbar-geometry assertions (fixture `_WIDE_SIZE` 2400 → 2600 + theme font inside `#MainToolbar`) | `architecture.md` header + Suite-figure provenance; this file's D40 status |
| 2 | D36's bridge/client count was **2 signals + 2 overrides**, not "3 + 3" — the third pair was the histogram path deleted under deviation 1 (`ibkr/bridge.py:15–17`, `ibkr/client.py:314–318`); and D38's bridge surface is **4 signals** (`news_providers` / `historical_news` / `historical_news_end` / `news_article`, `ibkr/bridge.py:41–45`), not the two named | `architecture.md` D36 Codebase Summary + Integration Points, D38 Codebase Summary; this file's 36.1 row. **Both counts were inherited from the changelog** (`docs/phase-changelog.md:371` and `:282`) — see the changelog cross-check below |
| 3 | The `footprint_cache` blob is `{bar_ts: {level: [bidVol, askVol, tradeVol, tradeCount]}}` (4 values — the trade-count metric depends on the last two), not `[bid, ask]` (`data/footprint_cache.py:3–4`, `services/footprint_service.py:177`) | `architecture.md` D36 Data Model |
| 4 | The additive `popouts` table's `geometry` column is **TEXT** (JSON), not BLOB (`data/db.py:76–84`), and the `data/db.py` as-built note's line numbers/file length were stale (`_init_schema :14–157`, `_migrate_schema :159–179`, `_table_columns :181`, file 258 lines) | `architecture.md` D24.9 + Data Model |
| 5 | Line-number citations shifted by `99fb8fa` (+5 after `ui/main_window.py:~190`): the pop-out cap refusal is `:845–851` (was `:840–846`) and `conn_badge` is `:295` (was `:290`); `origin/main` is `262ec81` (the D40 merge `b366b19` is an ancestor) | both artifacts |
| 6 | `data/db.py`'s **single `_init_schema`** now carries four additive tables (`popouts`, `footprint_cache`, `yfinance_events_cache`, `volume_baseline`) plus the D27/D39 column additions — the pre-D24 "no schema change" framing needed the pointer added | `architecture.md` Data Model |

**Still-true and verified in this pass:** `MAX_POPOUTS = 10` (`config/settings.py:42`),
`SESSION_BAR_CAP = 5000` (`:45`), `LIVE_PORT = 7496` / `check_live_port` (`:11`/`:20`),
`MAX_ORDER_NOTIONAL = 25000` (`:39`), `MAX_REALTIME_BARS_PER_10_MIN = 60` (`:30`),
`MAX_HISTORICAL_PER_600S = 60` (`:35`); `_always_on_top = False` (`ui/popout_window.py:56`) +
toggle (`:289`); `DepthHeatmapItem` added unconditionally with `_depth_enabled_ui = True`
(`ui/chart_panel.py:368`/`:370`); the `TickerSession` signal pair (`ui/ticker_session.py:65–73`);
the pop-out refusal message text (`ui/main_window.py::MainWindow._open_popout`); `CACHEABLE_SYMBOLS` +
`is_cacheable` (`data/footprint_cache.py:26`/`:29`); `MD_LINE_CAP = 100` / `MD_LINE_WARN_AT = 90`
(`services/md_line_guard.py:16–17`); `DEFAULT_Z_THRESHOLD = 4.0` / `MIN_WARMUP_BARS = 5` /
`N_BASELINE_BARS = 30` / `MAD_FLOOR_RATIO = 0.05` / `VOLUME_FLOOR_PER_MIN = 1.0`
(`services/volume_baseline.py:58–66`); the z-threshold spinbox floor 1.0
(`ui/alarm_dialog.py:106`, `ui/alarm_edit_dialog.py:48`); `DisconnectClass` +
`_last_disconnect_class` reset on connect + 2s/16s backoff (`ibkr/client.py:20–59`, `:47–48`,
`:192`); reconcile-then-`resume_all` ordering (`ui/main_window.py:1189–1196`); the auction
highlight window 9:25–9:35 / 15:55–16:05 ET (`ui/chart_panel.py:917–924`); the D2 chip lane
(`anchor=(0,0.5)`, `x = view_rect.right() + PRICE_TAG_PAD`, lane reserved by
`PRICE_TAG_LANE_SAMPLE` and folded into the zoom offset at `ui/chart_panel.py:620`); the
ESC-013/ESC-020 ordering contract (`vb.setRange` before the candle picture, `w_vol` derived after
— `ui/chart_panel.py:1676`/`:1688`); the D11 measured-bbox stacking
(`ui/drawing_overlay.py:476`/`:481`); the `RouterMode` state machine incl. TR-9's refusal
(`ui/chart_mouse_router.py:271` lines, `:168`) and TR-17's `exit_to_idle` on symbol change
(`ui/chart_panel.py:1355–1362`); `requirements.txt` = `ibapi-latest==10.51.1` + `yfinance==1.7.0`.

**Not behaviour, but recorded:** the historical D16–D23 increment sections of `architecture.md`
(and the D23 phases here) cite `ui/main_window.py`, `ui/watchlist_panel.py` and
`ibkr/market_data.py` at pre-D24 line numbers; all three files have grown; the same applies to the
"Moved from (as-built)" column of the D24/D25/D28 session-extraction table (pre-extraction
`MainWindow`). The **§ *Citation convention*** block in `architecture.md` bounds both regions
explicitly — `path::symbol` is the durable form, a bare `file:line` is indicative only, and those
two regions keep their at-that-commit numbers deliberately (the *symbols* in them are verified
present; the line numbers are not renumbered).

**Changelog cross-check (`docs/phase-changelog.md`, read in full per the owner's standing
instruction, 2026-10-14).** Four of the corrections above are ones the changelog **records or
corroborates**, and those citations were added: the **D40 test figure** (Phase D40 — "1020 passing,
0 failing"), the **footprint blob's two-metric shape** (Phase D36 item 36.2 — per-level bid/ask
volume *plus* trade volume and trade count), the **histogram-path removal** that makes D36's real
API surface 2 + 2 (Phase D36 — Decisions + review finding A1), and the **four additive tables**
(Phase 3 D24.9, Phase D36 36.4, Phase D38 38b.1, Phase D39 39.2). Two of the corrections were
**inherited from the changelog** — the D36 "3 signals / 3 overrides" count (`:371`) and the D38
two-signal bridge list (`:282`) — so the changelog carries the same two errors; those were
reported, not edited here (it is not this agent's file). The remaining corrections (suite-figure
wording, `origin/main`, the `+5` line shifts, `popouts.geometry` as `TEXT`, `data/db.py`'s line
numbers) are **changelog-silent**: the changelog predates `99fb8fa` and never cites those lines.
The changelog's own status/SHA drift — phase statuses, the D40 `d6f38e8` fix SHA, and the D37
"depth default ON pending owner confirmation" — is already tracked as **DG62** in
`docs/requirements/design_gaps.md` and is not duplicated here.

---

## D41 — Batch 18 removal (D36 footprint + D37 depth/imbalance/auction + the **entire** Active Trader panel; right dock Portfolio-only) — validated 2026-10-15, **approved for build**

> **Document state.** This is the canonical D41 plan: `docs/plan_proposal.md` /
> `docs/architecture_proposal.md` were validated `Status: APPROVED` (D41 cycle 2) and are carried
> here. **D41 is approved and not yet built** — D1–D40 above are as-built and unchanged. Owner
> decision 2026-10-15: **Q48** = also remove the Active Trader DOM ladder; **Q49** = delete the
> persisted `footprint_cache` table **and rows**; **Q50** = remove the **entire** Active Trader panel
> (in-app order-entry UI included) and make the right dock **Portfolio-only**.
> Companion architecture: `docs/architecture.md` § *D41 increment* (Codebase Summary, decisions
> `S1`–`S12`, components, data model, integrations, non-functional, risks `AR-D41-1`–`AR-D41-12`).
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`), `### D41`
> (`:3263`–`:3426`, `AC-D41.1`–`AC-D41.7`), Journey 36 (`:855`–`:882`), `A68`–`A71`, `DG66`–`DG71`.
> Review: `docs/plan_review.md` (D41 cycle 2, `APPROVED`).

**Scope.** D41 is a **removal**, not a feature: (1) delete the D36 footprint tree and the D37
depth/heatmap/imbalance/auction tree; (2) delete the **entire** Active Trader panel (DOM ladder **and**
the in-app order-entry ticket) plus `ibkr/market_depth.py`, `ibkr/order_book.py`, the `DOM` toolbar
button, the watchlist depth wiring and the depth terms of the MD-line accounting, and re-shape the
single right dock into a **Portfolio-only** section; (3) delete the persisted `footprint_cache` table
(+ rows); and (4) **re-home** the D26 safety gates (disconnected guard + `validate_order()` gate, fed
by a retained `ref_price` source) onto Portfolio's close/flatten path, the app's only surviving order
emitter.

**Must not break:** the retained order machinery (`ibkr/orders.py` incl. `bracket_order`,
`ibkr/validation.py` + `validate_order()`, order-ID reservation, the kill switch, order registry /
error handling, the fail-fast port check) for Portfolio's Close / Close Group / Flatten All and the
SL/TP dialogs; D38 (news/dividends: `footprint_cache_key`, `INDEX_PROXY`, `md_line_guard.assess`,
`_guard_md_lines`, S0 `"292"`/`"456"`, the S0 substrate); D39 (`volume_baseline` + burst/search);
D27/D28 correctness/pacing/perf and the chart. **11 escalations stay open and untouched**
(ESC-032/033/034/036/037/**038**/041/042/043/044/045 — `escalations.json` holds **14** `open` entries
today, of which ESC-038 is `open`/routed REQUIREMENTS and D41-neutral); ESC-035/039/040 go **moot** by
removal only (DG66) and are flipped to `addressed` by the **Code Reviewer** after re-verification,
not by Build.

### Coverage / traceability (D41)

| Requirement / journey | Architecture (D41 increment) | Phase |
|---|---|---|
| `AC-D41.1` — no D36/D37/DOM-ladder/Active-Trader/order-entry control renders | `S3`, `S6`, `S9`, `S11`; Components *Removed*; AR-D41-8 | 1 (footprint/depth controls) + 2 (DOM / Active Trader / Portfolio-only) |
| `AC-D41.2` — no D36/D37/DOM-ladder request is ever issued (`reqHistoricalTicks`, `reqTickByTickData`, `reqMktDepth`/`cancelMktDepth`, generic `"225"`) | `S8`, `S9`; Integration Points | 1 (ticks/heatmap/`"225"`) + 2 (depth/ladder) |
| `AC-D41.3` — the 9 modules + 5 suites are gone, no dangling import/reference | `S3`, `S10`, `S11`; AR-D41-2, AR-D41-8, AR-D41-12 | 1 (D36/D37 modules) + 2 (Active Trader/depth modules) + 3 (scan guard) |
| `AC-D41.4` — D38/D39/D27–D28 substrate intact **and** the retained order machinery + resolving `ref_price` | `S4`, `S5`, `S8`, `S10`; Components *Retained unchanged*; AR-D41-6, AR-D41-7 | 1 (substrate + **the two KEEP-coverage re-homes**: `footprint_cache_key` → `tests/test_d39_burst_search.py`, `md_line_guard.assess` → `tests/test_d38_events_news.py`) + 2 (re-homed gates; `bracket_order` all-three-legs kept via `tests/test_kill_switch.py`; the retained close-path deferral kept via `tests/test_d28_pacing.py`) + 3 (evidence) |
| `AC-D41.5` — app starts and charts; full offscreen suite green | `S12`; AR-D41-10..12 | 3 (with 1–2 as prerequisites) |
| `AC-D41.6` — `### D36`/`### D37` + `AC-D36.*`/`AC-D37.*` carry `SUPERSEDED BY D41`, D18/D21.13 notes, tech-stack sentence intact | Requirements-owned (present at `requirements.md:69`, `:83`, `:2074`, `:2088`, `:3075`, `:3116`) — **no code work** (AP-5 / FI-3) | — (Requirements) |
| `AC-D41.7` — right dock is Portfolio-only, visible in full screen, non-zero width, clamped; re-derived cap/header | `S6`; AR-D41-3 | 2 (implementation + **all 17 title/title-bar consumers**) + 3 (evidence) |
| Journey 36 (all 6 steps + edge cases) | Summary; Components; Non-Functional Approach | 1, 2, 3 |
| **D1–D35 and D38–D40 are not reopened** — every criterion is unchanged-by-construction and re-verified as the non-regression contract | Components *Retained unchanged*; Non-Functional; AR-D41-1/2/9 | 1, 2 (preservation) + 3 (full-suite evidence) |
| Q49 / A69 / DG70 — persisted footprint data deleted | `S7`; Data Model row 1 | 1 |
| Q48 / DG69 / DG66 — ladder + whole panel removed; ESC-035/039/040 moot | `S3`, `S9`; Components *Removed* | 2 |
| DG71(1) — retained `ref_price` source | `S4` | 2 |
| DG71(2) — Portfolio-only dock cap/header re-derived | `S6` | 2 |
| DG67 — surgical removal (KEEP list) | `S8`, `S10`; Components *Retained unchanged* | 1, 2 |
| D26 safety standing; D18 / `AC-D18.3` / D21.13 superseded-but-surviving outcomes | `S5`, `S6` | 2 |

### Phases (D41)

Three phases, **strictly ordered**. Each phase's wave must be fully consolidated before the next
phase opens, because `ui/chart_panel.py`, `ui/ticker_session.py`, `ui/main_window.py`,
`ibkr/bridge.py`, `ibkr/client.py` and `ibkr/subscription_manager.py` each receive edits in more than
one phase. `tests/test_d27_reconnect.py` is edited in both Phase 1 and Phase 2 — this is deliberate
(disjoint lines: the depth-assertion drops must land with the code they assert; the dock-title split
cannot precede the rename).

#### Phase 1 — Remove the D36 footprint *and* the D37 depth / imbalance / auction feature trees

- **Goal:** after this phase the app has no footprint render layer, no footprint service/cache/tick
  history, no depth heatmap, no IMB/AUC controls, no session depth refcount, no `"225"` auction need,
  and no `footprint_cache` table — while the chart, the watchlist, D38's S0 lines, D39's burst/search
  substrate and the retained order machinery are unchanged.
- **Covers:** `AC-D41.1` (the footprint/depth/IMB/AUC half), `AC-D41.2` (the
  `reqHistoricalTicks`/`reqTickByTickData`/`reqMktDepth`-heatmap/`"225"` half), `AC-D41.3` (the
  D36/D37 modules + the two suites), `AC-D41.4` (the D38/D39 half + the two KEEP-coverage re-homes),
  and the Q49/A69/DG70 persisted-data drop.
- **Requirement/journey coverage:** Journey 36 steps 1–5 (postconditions 1 and 2, and the
  `footprint_cache` edge case); `### D41` "Scope — REMOVE" bullets 1–2 and "Persisted footprint data".
- **Depends on:** nothing (first phase of the batch).
- **Why these two features are one phase:** their chart-side removal is **one contiguous edit** in
  `ui/chart_panel.py` (a single floating cluster whose D37 row sits below the footprint row, plus one
  adjacent handler block) and one contiguous session edit in `ui/ticker_session.py`; splitting them
  would edit the same files twice for no verification gain, and D41's own scope presents them as one
  removal item. It also keeps `ui/main_window.py` to **one** edit in this phase (the docs cite its
  line numbers — churn is a real cost, AR-D41-10).

**`touches_files` map — Phase 1** *(20 file entries; one task per file; within a wave these sets are
disjoint)*

| File | Action | Content |
|---|---|---|
| `ui/footprint_item.py` | **delete** | `FootprintItem` |
| `services/footprint_service.py` | **delete** | `FootprintService`, `mark_no_tick_data` (dead), page/wave bookkeeping |
| `data/footprint_cache.py` | **delete** | `FootprintCache`, `is_cacheable` |
| `ibkr/tick_history.py` | **delete** | `TickHistoryManager.req_historical_ticks` |
| `ui/depth_heatmap_item.py` | **delete** | `DepthHeatmapItem` |
| `services/depth_heatmap.py` | **delete** | `DepthHeatmapService`, `BUCKET_SECONDS` |
| `tests/test_d36_footprint.py` | **delete** | D36 suite (551 lines) |
| `tests/test_d37_microstructure.py` | **delete** | D37 suite (421 lines) |
| `ui/chart_panel.py` | edit (delete-only) | imports `:15`–`:16`; signals `:249`–`:254` (`footprint_toggled`/`footprint_viewport_changed`/`depth_toggled`); render layers `:351`–`:376` (`footprint_static`/`footprint_live`/`depth_heatmap_item`/`_depth_enabled_ui`); the whole floating cluster (footprint row + D37 row) `:500`–`:565`; `_position_fp_controls`/`_on_fp_*`/`refresh_footprint`/`_fp_status_text`/`_fp_queue_viewport_sync`/`_fp_emit_viewport` `:651`–`:750`; D37 `:757`–`:971` (`depth_enabled`, `_position_d37_controls`, `_on_depth_toggled`, `_on_imb_clicked`, `_on_auction_clicked`, `_on_depth_refresh`, `bind_d37_session`/`unbind_d37_session`, `_on_auction_tick`, `update_auction_chip`, `_in_auction_window`, `set_depth_state`, `_depth_refresh_timer`); the `resizeEvent`/scroll back-references `:988`–`:992`, `:1790`–`:1797`. **Keep** the zoom cluster, the `Volume` toggle, D38 `bind_d38_session`/`_on_events_updated`, and the D6/D9 width math (`ui/chart_panel.py::ChartPanel._clamp_half_width`, `:1688`–`:1690` — ESC-041's subject, AR-D41-9) |
| `ui/ticker_session.py` | edit (delete-only) | imports `:41`, `:46`; signals `:76`–`:80`; `_footprint`/`_fp_*` state `:163`–`:179`; auction state + depth state/timer `:203`–`:217`; `attach_view`'s `{"auction": {"225"}}` registration `:260`–`:269`; `detach_view`'s auction dereg `:281`; `teardown` `:332`–`:345`; `_append_bar`'s footprint resync `:829`–`:838`; the whole `_fp_host_managers`/`footprint_enable`/`footprint_resync`/`footprint_disable`/wave/forming/`_fp_*` block `:958`–`:1420`; the depth block `:708`–`:830` (`ensure_depth_subscribed`, `release_depth`, `_cancel_depth`, `_reissue_depth`, `_rebind_depth_req_id`, `on_depth_update`, `on_depth_error`, `_set_depth_state`, `depth_imbalance`, `depth_req_id`, `_on_depth_roll_timeout`); auction ingress in `on_tick_price`/`on_tick_size` `:539`–`:556`. **Keep** `footprint_cache_key`'s D39 use (`:922`, inside `_evaluate_burst_alarms`), the S0 substrate + `on_s0_tick_generic`/`on_s0_tick_string`/`on_s0_tick_news`, the RT path |
| `ui/main_window.py` | edit (delete-only) | imports `:32`–`:33`, `:41`; `self.tick_history_manager`/`self.footprint_cache` `:556`–`:558`; `b.historical_ticks_*` connects `:654`–`:655`; `chart_panel.footprint_toggled`/`footprint_viewport_changed`/`depth_toggled` connects `:350`–`:355`; `footprint_updated` connect/disconnect `:935`–`:954`; `_on_depth_toggled`/`_on_fp_toggled`/`_on_fp_viewport`/`_on_primary_footprint_updated` `:965`–`:1015`; the footprint restart on reconnect `:1178`; the D36/D37 error branches `:1664`–`:1671`; `_on_fp_ticks_*` slots; the `depth` term of `_md_line_count` `:800`–`:801` and `_guard_depth_budget`/`DEPTH_FEED_CAP` `:99`, `:817`–`:824` (its only caller is `ui/ticker_session.py::TickerSession.ensure_depth_subscribed` `:720`, removed here). **Keep** `self.depth_manager` creation `:560` (its last consumers are Phase 2's DOM path) and `_guard_md_lines` `:805` |
| `ibkr/bridge.py` | edit (delete-only) | `historical_ticks_bid_ask` `:15`, `historical_ticks_last` `:17` |
| `ibkr/client.py` | edit (delete-only) | `historicalTicksBidAsk` `:314`–`:316`, `historicalTicksLast` `:318`–`:320` |
| `ibkr/subscription_manager.py` | edit (delete-only) | `DEPTH_HEATMAP` `:38` (**keep** `S0_TICKS`, and the retained `SubscriptionManager.has_subscription` `:81`) |
| `ibkr/contracts.py` | edit (delete-only) | `resolve_footprint_contract` `:160`+ (**keep** `footprint_cache_key` `:144` verbatim, `INDEX_PROXY` `:133`) |
| `data/db.py` | edit | remove the `footprint_cache` DDL `:118`–`:127`; add `DROP TABLE IF EXISTS footprint_cache` to `_migrate_schema` (S7). **Keep** `yfinance_events_cache` + `volume_baseline` |
| `services/md_line_guard.py` | edit (comment only) | module docstring de-references "depth feeds" (only the S0 lines gate on the verdict after D41); thresholds + `assess()` body unchanged (S8) |
| `tests/test_d27_reconnect.py` | edit | drop **the D37 session-depth assertions** (`:204`–`:208`, `:230`–`:232`) and the replayed-`mkt_data` count `:221`–`:223`, re-derived from the surviving watchlist row + S0 line (the `"225"` auction need is gone above); **keep** `:200`–`:203`/`:228`–`:229` (the DOM-depth assertions) **until Phase 2**, and **keep** the RT/S0/watchlist replay + rebinding assertions verbatim (`:220`, `:224`–`:227`, `:233`–`:236`). The `"Active Trader"` dock-title tuple `:163` is **left untouched here** — the rename lands in Phase 2, and the file is re-pointed again there for that one line |
| `tests/test_d39_burst_search.py` | edit (**KEEP-coverage re-home**) | gains `test_footprint_cache_key_rollover_isolates_tape` — the assertions moved **verbatim** from `tests/test_d36_footprint.py::test_rollover_key_change_isolates_tape` (`:389`–`:398`): `footprint_cache_key("SPX", now=…)` startswith `"ES"` for two dates on either side of the front-month roll, and `key1 != key2`. D39 is the surviving consumer of the key (`ui/ticker_session.py::TickerSession._evaluate_burst_alarms`, `:922`), so this is its natural home; without it the deleted D36 suite takes the symbol's **only** test |
| `tests/test_d38_events_news.py` | edit (**KEEP-coverage re-home**; previously "no change") | gains `test_md_line_guard_thresholds` — the assertions moved from `tests/test_d37_microstructure.py::test_md_line_guard_thresholds` (`:336`–`:344`), re-purposed to the **surviving** purpose: `assess(50, "SPX", "S0 ticks") == ("ok", "")`, `assess(90, …)` → `"approaching"` with `"SPX"` and `"90/100"` in the message, `assess(100, …)` → `"exceeded"` naming the symbol and refusing (`"not subscribing"`). The D38 S0 lines are what `_guard_md_lines` still gates, so the thresholds get their retained suite; without it the deleted D37 suite takes `assess`'s **only** test. Its existing `queue_depth` assertions (`:158`, `:165`) and its comment-only D36 references are untouched |

#### Phase 2 — Remove the Active Trader panel (DOM ladder + order-entry ticket) and the market-depth machinery; make the right dock Portfolio-only; re-home the retained order gates

- **Goal:** `ui/active_trader_panel.py`, `ibkr/market_depth.py` and `ibkr/order_book.py` are gone;
  the `DOM` button and every DOM/depth signal path is gone; the right dock hosts the Portfolio
  section only and still satisfies the surviving D18 visibility/clamp outcomes in full screen; and
  the app's only surviving order emitter (Portfolio Close / Close Group / Flatten All) is gated by
  the retained D26 machinery with a resolving `ref_price`.
- **Covers:** `AC-D41.1` (no DOM button, no Active Trader panel/ladder/ticket/title-bar button, no
  `active_trader` attribute), `AC-D41.2` (the `reqMktDepth`/`cancelMktDepth` and `updateMktDepth*`
  half), `AC-D41.3` (the three modules + `tests/test_market_depth.py`), the order-path half of
  `AC-D41.4`, and `AC-D41.7`.
- **Requirement/journey coverage:** Journey 36 steps 3 and 6 (postconditions 3 and 5); `### D41`
  DOM-ladder bullet, "Active Trader panel — whole" bullet, and the `ref_price` / D18 / D21.13 KEEP
  bullets (closing **DG71(1)**, **DG71(2)** and **DG69**).
- **Depends on:** Phase 1 (it edits `ui/main_window.py`, `ibkr/bridge.py`, `ibkr/client.py` and
  `ibkr/subscription_manager.py`, all already touched there; phases are strictly ordered).
- **Decisions consumed:** `S5` (`ref_price` source + re-homed gates), `S6` (Portfolio-only dock
  model), `S9` (remaining bridge/client deletions), `S11` (test re-pointing).

**`touches_files` map — Phase 2** *(37 rows / 39 file entries; one task per file; within a wave these
sets are disjoint)*

| File | Action | Content |
|---|---|---|
| `ui/active_trader_panel.py` | **delete** | whole file (ladder, book, `OrderEntryWidget`, panel shell/header) |
| `ibkr/market_depth.py` | **delete** | whole file (DOM + D37 shared halves) |
| `ibkr/order_book.py` | **delete** | whole file (`OrderBook`, `Level`, `apply_operation`, `SIDE_*`) |
| `tests/test_market_depth.py` | **delete** | 182 lines, depth-only |
| `tests/test_order_entry_mkt.py`, `tests/test_order_entry_side.py` | **delete** | widget-scoped only (verified: they import only `ui.active_trader_panel` and guard no retained order path — FI-6) |
| `ui/main_window.py` | edit | `ActiveTraderPanel`/`on_depth_callback` import `:76`, **and the now-dead `MarketDepthManager` import `:35` + the `self.depth_manager` construction `:560`** (their last consumers are the DOM/depth paths removed in this phase — AR-D41-2; *Validator completion, no new decision*); `dom_btn` (`:249`–`:254`, `:321`, `:1883`–`:1884`); `self.active_trader` construction + container `:471`–`:483`; dock creation/title-bar/minimum/objectName `:485`–`:502` (**rename to `"Portfolio"`**); collapse wiring `:524`–`:533`; `watchlist_panel.set_depth_manager` `:610`; `b.update_mkt_depth` connect `:668`; `order_place_requested` connect `:693`; `_depth_req_id` + `_rebind_depth_req_id` `:714`, `:1437`–`:1439`; `_on_mkt_depth` + `_on_dom_toggled` + `_subscribe_dom` `:2984`–`:3040`; the DOM depth error branch `:1677`–`:1683`; `closeEvent`'s depth cancels `:3550`–`:3555`; `_on_order_place_requested`/`_place_order` `:3092`–`:3246` and every `active_trader.*` call (`:1705`, `:3033`, `:3108`, `:3121`, `:3132`, `:3152`, `:3164`, `:3176`, `:3207`, `:3243`, `:3388`); **every** remaining `"Active Trader"` literal/comment in the file (`:249`, `:253`, `:464`–`:468`, `:2459`, `:2982`, `:2985`–`:2986`); **new** `_ref_price_for`; **new** gates in `_close_position_by_id` `:3446`–`:3508`; dock re-shape per `S6` (`_compute_right_dock_collapsed_min_width` `:2455`, `_right_region_is_collapsed` `:2477`, `_sync_right_dock_collapse` `:2494`, `_on_right_panel_toggled` `:2487`, `right_dock_container`/`_right_dock_layout` `:473`–`:487`, `:2510`). **`_update_order_status` `:3384`/`_on_order_error` `:1692` keep the registry update and drop only their ticket line** (their status-bar message stays — AR-D41-1) |
| `ibkr/bridge.py` | edit (delete-only) | `update_mkt_depth` `:52` |
| `ibkr/client.py` | edit (delete-only) | `updateMktDepth` `:391`–`:394`, `updateMktDepthL2` `:397`–`:406` |
| `ibkr/subscription_manager.py` | edit (delete-only) | `DEPTH` `:37` (**keep** `SubscriptionManager.has_subscription` `:81` — untagged, retained, and *not* D41's) |
| `ibkr/validation.py` | edit (**additive**) | one keyword `risk_reducing: bool = False`; skip the notional check when `True`; every structural check unchanged; the **module docstring `:5` is re-pointed** from "Wired at the top of `MainWindow._place_order`" to the retained emitter `MainWindow._close_position_by_id` |
| `ui/watchlist_panel.py` | edit (delete-only) | `_depth_manager` `:273`, `set_depth_manager` `:767`–`:769`, `on_depth_update` `:789`–`:793` |
| `data/models.py` | edit (delete-only) | `OrderBookLevel` `:105`–`:110` (zero references — inert; **FI-2**, accepted as an explicit scope close-out) |
| `ui/dock_layout.py` | edit (comments only) | module docstring + the constant comment "right (Active Trader) dock" → Portfolio-only; constants + `plan_dock_widths` **unchanged** (S6). *(Placed in Phase 2, not Phase 1: its only Active-Trader references belong to this phase's rename.)* |
| `tests/test_dock_d18_region.py` | edit (re-point) | `findChild(QDockWidget, "Active Trader")` `:107` + `objectName() == "Active Trader"` `:110` → `"Portfolio"`; `win.active_trader.width()` `:86`/`:140`/`:145`/`:163` → the Portfolio panel / the dock's widget; `win.right_dock_container` `:88`/`:173` → `win.right_dock.widget()`; docstring `:1`–`:13`; **keep** every surviving D18 visibility/clamp/equal-width assertion |
| `tests/test_right_dock_d21.py` | edit (re-point) | `from ui.active_trader_panel import ActiveTraderPanel` `:29` and every `win.active_trader.*` (`:64`, `:65`, `:69`, `:82`, `:83`, `:86`, `:87`, `:107`, `:159`, `:170`, `:189`, `:203`, `:234`, `:237`, `:249`, `:279`) → the single Portfolio section; the title-bar-text assertions `:57`/`:62`/`:67` (`at_btn.text() == "Active Trader"`) → the retained `summary_label` ("Account Summary") + the D21.13 strike-through on it; docstrings `:6`–`:7` |
| `tests/test_watchlist_nonregression_d22.py` | edit (re-point) | `window.active_trader.header_button` `:137` → the Portfolio `summary_label`; title-bar-text assertion `:142` (`== "Active Trader"`) → `"Account Summary"`; collapse/restore assertions `:148`–`:159` → the retained Portfolio header |
| `tests/test_dock_widths_d18.py` | edit (re-point) | `objectName() == "Active Trader"` `:177` → `"Portfolio"`; `win.active_trader.width()` `:277` and `win.active_trader.ladder.*` `:362`–`:363` → a wide widget inside the Portfolio section (AC-D18.6's "wide content cannot push the dock off-screen" probe survives); `win.right_dock_container.width()` `:279` → the dock's widget; `_RIGHT_PERSISTENCE_HINTS` `:72` drops the now-stale `"active_trader"` entry; docstring `:13`/`:17`; comment `:111`; **keep** every cap/min/chart-minimum assertion |
| `tests/test_dock_widths_d18_impl.py` | edit (re-point) | `win.active_trader.ladder.*` `:267`–`:268` → a wide widget inside the Portfolio section; `_RIGHT_PERSISTENCE_HINTS` `:48` drops `"active_trader"`; docstring `:9`; **keep** every `plan_dock_widths` invariant + the geometry assertions |
| `tests/test_dock_widths_d17.py` | edit (re-point) | `_RIGHT_DOCKS = ("Active Trader", "Portfolio")` `:37` (used `:73`) → `("Portfolio",)`; **keep** every ADR-17 clamp assertion |
| `tests/test_d10_d13_integration.py` | edit (1-line) | `_RIGHT_DOCKS` `:33`–`:35` (used `:53`) → `("Portfolio",)`; docstring `:17` (AR-D41-3) |
| `tests/test_watchlist_columns_d21.py` | edit (1-line) | `_RIGHT_DOCK_TITLES = ("Active Trader",)` `:308` (used `:322`) → `("Portfolio",)` |
| `tests/test_history_backfill_loadpath.py` | edit (1-line) | title-keyed hide `:165` → `("Portfolio",)` |
| `tests/test_d27_account_subs.py` | edit (1-line) | title-keyed hide `:27` → `("Portfolio",)` |
| `tests/test_d27_phantom_alarms.py` | edit (1-line) | title-keyed hide `:56` → `("Portfolio",)` |
| `tests/test_d27_stream_health.py` | edit (1-line) | title-keyed hide `:67` → `("Portfolio",)` |
| `tests/test_watchlist_d14_midrag.py` | edit | `_RIGHT_DOCKS = ("Active Trader",)` `:35` (used `:82`) + the comment `:33`–`:34` → `("Portfolio",)`. Without this the D14 gesture harness silently stops hiding the dock and runs against a different chart width |
| `tests/test_d27_position_prices.py` | edit | the title-keyed hide in `_make_window` `:29`–`:31` → `("Portfolio",)` |
| `tests/test_history_backfill.py` | edit | the title-keyed hide in the window factory `:198`–`:200` → `("Portfolio",)` |
| `tests/test_history_backfill_disconnect.py` | edit | the title-keyed hide in the window factory `:135`–`:137` → `("Portfolio",)` |
| `tests/test_crosshair_axis_lane.py` | edit | `region = docks["Active Trader"]` `:105` → `region = docks["Portfolio"]`; the now-**inverted** `assert "Portfolio" not in docks` `:106` → a positive assertion (`"Portfolio" in docks` **and** `"Active Trader" not in docks`), which is what D18 Phase 3's comment `:102`–`:104` was asserting in the old two-section world; docstring `:7` and the f-string at `:123` follow the rename. Without this the module fails with a deterministically red `KeyError` |
| `tests/test_d28_pacing.py` | edit | `test_place_order_defers_when_limiter_empty` `:117`–`:140` calls the **deleted** `win._place_order(...)` `:130` → re-point at the retained emitter: seed one `positions` row, keep `win._ibkr_connected = True` and the stubbed `placeOrder`, drive `win._close_position_by_id(<seeded id>)`, and keep the four D28.1 order-path guarantees (no immediate transmit, no GUI-thread sleep, a `pacing-limited` status message, exactly one deferred transmit after the bucket refills at `:137`). This is also the live proof of `S5`'s step-3 ordering (pacing after the gate, before `placeOrder`) |
| `tests/test_kill_switch.py` | edit | `test_bracket_place_registers_all_three_legs` `:77`–`:100` calls the **deleted** `win._place_order(order_type="BRACKET", …)` `:90` → re-point at the retained builders (`ibkr/orders.py::bracket_order` + `order_registry.register`), keeping the `IdManager` patch `:87`–`:89` so the legs are the reserved `1/2/3`, and keeping every assertion: all three legs registered at transmit time, ids `[1, 2, 3]`, parent `BUY`, both children `SELL` (`:93`–`:98`), and `_kill_switch` seeing the counts (the neighbouring `:63`–`:74`). This is **D26.8's only all-three-legs-at-transmit test** — it must not be deleted (`AC-D41.4`'s "retained machinery … exercised") |
| `tests/test_order_validation.py` | edit (re-point) | drop the two `_place_order` wiring tests (`:91`–`:107` refuses-invalid, `:109`–`:121` transmits-valid); **keep** every pure-gate test incl. the notional-cap pair (`:124`–`:128`); module docstring de-references `_place_order` |
| `tests/test_order_rejections.py` | edit (re-point) | keep the registry assertions; re-point the surfaced message from the removed ticket (`win.active_trader.order_entry.status_label.text()` `:46`) to `status_bar` (the message is already written at `ui/main_window.py::MainWindow._on_order_error` `:1706`); re-point `win._place_order(...)` `:85` (AC-D26.9's disconnected refusal) at the retained close path |
| `tests/test_toolbar_scroll_d19.py`, `tests/test_toolbar_d20.py` | edit | drop `dom_btn` from `_CONTROL_NAMES` (`:42` / `:44`); re-check the geometry fixtures (AR-D41-4) |
| `tests/test_toolbar_d21.py` | edit | drop `dom_btn` from `_CHECKABLE_TOGGLES` `:152` |
| `tests/test_d27_reconnect.py` | edit (1 line) | the dock-title tuple `:163` → `("Portfolio",)`. **Only this line changes in this phase** — the depth-assertion drops are Phase 1's; the split is forced by the rename landing here |

**Phase-2 files explicitly checked and *not* changed** (listed so no worker "fixes" them):
`tests/test_order_builders.py` (`bracket_order` side-correctness — `AC-D41.4`'s retained-builder
evidence, untouched), `tests/test_sltp_honesty.py` (the SL/TP dialog discloses non-transmission; the
dialog itself is untouched — `ui/stop_loss_target_dialog.py` contains no `placeOrder`),
`tests/test_port_guard.py`, `tests/test_id_manager.py`, `tests/test_dock_layout.py` (it reads
`win.right_dock`, which survives the rename, and asserts only pure `plan_dock_widths` geometry),
`tests/test_d38_events_news.py` and `tests/test_d39_burst_search.py` (Phase 1's only change is the
KEEP-coverage re-home), `tests/test_db_schema.py` (Phase 3's).

#### Phase 3 — Non-regression verification and the D41 guards

- **Goal:** the removals are **evidenced**, not asserted: automated guards prove the modules,
  identifiers, controls and requests are gone, the retained substrate/order machinery still works,
  and the whole offscreen suite is green.
- **Covers:** `AC-D41.3` (the scan half), `AC-D41.4` (substrate + retained machinery + resolving
  `ref_price`), `AC-D41.5`, `AC-D41.7` (measurable half), plus the Q49 drop verification.
- **Requirement/journey coverage:** Journey 36 steps 2, 4, 5.
- **Depends on:** Phases 1–2 (the guards cannot be green before both are complete).

**`touches_files` map — Phase 3** *(4 file entries)*

| File | Action | Content |
|---|---|---|
| `tests/test_d41_removal.py` | **new** | `AC-D41.1`/`AC-D41.3`/`AC-D41.5`: module-absence (`importlib.util.find_spec` `None` + source-path existence) for all 9 deleted modules and the 5 deleted suites; a **token scan** over `ui/`, `ibkr/`, `services/`, `data/`, `config/`, `tests/`, `main.py` (excluding `docs/`, `graphify-out/`, `__pycache__`) for the **complete** token set below; a **render probe** on a real offscreen `MainWindow` (no `Footprint`/`Classic`/`Tick count`/`Depth`/`IMB —`/`AUC —` button anywhere, no `DOM` button in the toolbar, `hasattr(win, "active_trader") is False`, no `footprint_*`/`depth_*`/`auction_*` attribute or signal on `ChartPanel`/`MainWindow`, while the zoom cluster, the `Volume` toggle and the Portfolio controls still render); a **request probe** (fake client records every call; drive `load_chart` + every remaining control + `_on_connected()` + a symbol switch ⇒ zero `reqMktDepth`/`cancelMktDepth`/`reqHistoricalTicks`/`reqTickByTickData` and no `reqMktData` generic-ticks string containing `"225"`, while the D38 S0 line and the watchlist market-data/RT lines still issue); and an app-start/chart smoke (`MainWindow()` → `load_chart` → bars render candles + volume) |
| `tests/test_d41_portfolio_dock.py` | **new** | `AC-D41.7`: exactly one right dock; `windowTitle()`/`objectName()` == `"Portfolio"`; its widget **is** `win.portfolio_panel`; no dock/widget titled `"Active Trader"` exists; **full-screen** visibility (non-zero width, on screen, not pushed past the window edge — the original D17/D18 symptom); `width <= right_dock_max_width(chart_area_after) + 1` and `>= RIGHT_DOCK_MIN_WIDTH`; the watchlist/chart minimums still hold (pure `plan_dock_widths` invariants re-asserted); clicking `portfolio_panel.summary_label` collapses to the single-button strip (`_right_dock_collapsed_min_width`) and the chart reclaims the width, clicking again restores; no **new** `QSettings` key is written for the right dock. Its `"Active Trader"` occurrences are **negative assertions only** (allow-listed in the token scan) |
| `tests/test_d41_retained_order_path.py` | **new** | `AC-D41.4`: `_ref_price_for` resolves from `_symbol_last_prices` (fed by the watchlist sink **and** by a session's aggregated bar) and returns `None` for an unknown symbol; a **disconnected** close refuses and never calls `placeOrder`; an **invalid** close (empty symbol / zero qty) refuses; a **valid** close with a >USD 25,000 notional transmits **exactly once** (the risk-reducing carve-out) while `validate_order` on the equivalent risk-increasing call is still rejected; the kill-switch/order-ID/port-check modules import and their existing suites stay untouched |
| `tests/test_db_schema.py` | edit (**add**) | a fresh `DB()` has **no** `footprint_cache` table, and a legacy DB pre-seeded with the old DDL + a row has it **dropped** after `DB()` init, while `volume_baseline` + `yfinance_events_cache` survive (Q49/A69/DG70); the existing `EXPECTED_TABLES`/`_init_schema`-once assertions stay |

**The removal guard's token set.** `tests/test_d41_removal.py` scans for **all** of:

- *Deleted modules/classes:* `FootprintItem`, `FootprintService`, `FootprintCache`,
  `TickHistoryManager`, `DepthHeatmapItem`, `DepthHeatmapService`, `MarketDepthManager`, `OrderBook`,
  `OrderBookLevel`, `LadderTable`, `BookTable`, `ActiveTraderPanel`, `OrderEntryWidget`,
  `RightDockContainer`.
- *Deleted members:* `is_cacheable`, `apply_operation`, `active_feed_count`,
  `resolve_footprint_contract`, `refresh_footprint`, `_fp_`, `_fp_host_managers`, `_on_fp_`,
  `bind_d37_session`, `unbind_d37_session`, `set_depth_state`, `update_auction_chip`, `depth_enabled`,
  `depth_state_changed`, `ensure_depth_subscribed`, `release_depth`, `cancel_depth`, `reissue_depth`,
  `rebind_depth_req_id`, `on_depth_update`, `on_depth_error`, `depth_imbalance`, `_depth_state`,
  `_depth_refresh_timer`, `depth_req_id`, `_depth_req_id`, `_depth_manager`, `set_depth_manager`,
  `footprint_enable`, `footprint_resync`, `footprint_disable`, `auction_state`, `_auction`,
  `_guard_depth_budget`, `DEPTH_FEED_CAP`, `active_trader`, `dom_btn`, `_subscribe_dom`,
  `_on_dom_toggled`, `_on_mkt_depth`, `_place_order`, `_on_order_place_requested`,
  `right_dock_container`, `_right_dock_layout`.
- *Deleted integration surface:* `historical_ticks_`, `historicalTicks`, `update_mkt_depth`,
  `updateMktDepth`, `reqMktDepth`, `cancelMktDepth`, `reqHistoricalTicks`, `reqTickByTickData`,
  `DEPTH_HEATMAP`, `DEPTH`, and the generic-tick literal `"225"`.
- *The removed dock identifier:* the **quoted literal** `"Active Trader"`.

**Documented allow-list** (each with the reason recorded in the guard's docstring, so a reader can
tell an intentional survivor from a miss):

1. `footprint_cache_key` — **kept verbatim** by `AC-D41.4`/DG67 (D39's burst-baseline key; S10, FI-5).
2. `queue_depth` — `NewsManager`'s retained queue depth (`tests/test_d38_events_news.py:158`).
3. `has_subscription` — **scoped, not bare**: `MarketDepthManager.has_subscription`
   (`ibkr/market_depth.py:45`, deleted) is covered by the `MarketDepthManager` module-absence check,
   while `SubscriptionManager.has_subscription` (`ibkr/subscription_manager.py:81`) is **retained**
   and is not D41's to remove. The guard therefore scans the **qualified** forms
   (`depth_manager.has_subscription`, `active_trader…`) rather than the bare token, and the bare
   token is allowed **only** in `ibkr/subscription_manager.py`.
4. `"Active Trader"` — allowed **only** in the guard files themselves
   (`tests/test_d41_removal.py`, `tests/test_d41_portfolio_dock.py`) where it appears in negative
   assertions; the guard excludes itself from the scan and allow-lists the dock suite's literal.
   Every other token above **is** scanned in both files.
5. `DEPTH`/`depth` as **substrings of retained names** are matched by whole-token boundaries only
   (`depth_state_changed`, `DEPTH_FEED_CAP`, …), so `NewsManager.queue_depth` and
   `md_line_guard`'s own `depth`-free code are not false positives.

**The guard must be red before the change.** The Phase-3 task's own acceptance includes running it
against the pre-removal tree (or against a stash of the removals) to prove every token it claims
actually fires; a token that never matches pre-D41 is struck rather than left as decoration.

### Sequencing and wave shape (D41)

- **Within a phase:** one task per file. Two tasks with overlapping `touches_files` must never be
  `in_progress` in the same wave — so the partition above *is* the parallelism plan. With
  `max_parallel_tasks` default **6**, Phase 1 (**20** file entries) and Phase 2 (**39** file entries)
  each run in a few rolling waves; the long pole is `ui/main_window.py`, which is therefore **one
  task per phase** (never split across workers in the same wave). The two-phase entries for
  `tests/test_d27_reconnect.py` are in **different** phases and therefore never share a wave.
- **Across phases:** strictly sequential — Phase 2 opens only after Phase 1's wave is consolidated,
  Phase 3 only after Phase 2's. The shared files are `ui/chart_panel.py`, `ui/ticker_session.py`,
  `ui/main_window.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/subscription_manager.py`
  (Phases 1 and 2) and `tests/test_d27_reconnect.py` (Phases 1 and 2, disjoint lines).
- **Deletions are safe to pair** with any edit task: deleting a module whose last importer is removed
  in the same wave is fine because the *edit* task owns the importer's file, and no other task
  imports the deleted module. Where a deletion and the edit that removes its last reference land in
  the same wave, the edit must land (`build_wave.py` re-runs the wave until the frontier drains; a
  `ModuleNotFoundError` from a partially-applied wave is expected and resolves on the next pass — run
  the phase's own test selection once the wave is consolidated, not per task).
- **Per-task verification:** each task carries its own focused check (the Task Manager's call). The
  **phase-level** acceptance evidence is: **Phase 1** — `test_d27_reconnect` + the D38/D39 suites
  **including the two KEEP-coverage re-homes** green; **Phase 2** — the re-pointed dock/toolbar/order
  suites **plus `test_d28_pacing`, `test_kill_switch`, `test_crosshair_axis_lane` and the four
  dock-hide-helper suites** green; **Phase 3** — the three new suites + the extended `test_db_schema`
  + the full offscreen run.

### Assumptions (D41)

Plan-level assumptions **not** already in `requirements.md`'s Assumptions Log (`A1`–`A71`).

- **AP-1 (phase ordering).** Phases 1–3 are strictly sequential: Phase 2 opens only after Phase 1's
  wave is consolidated and Phase 3 only after Phase 2's. Reason: six shared files receive edits in
  more than one phase, and `build_wave.py`'s non-overlap rule is per *wave*, not per batch.
- **AP-2 (wave shape).** Build runs `build_wave.py` with `max_parallel_tasks` default 6; the
  per-phase file partition above is the `touches_files` map, one task per file, and the long-pole
  `ui/main_window.py` stays a single task per phase.
- **AP-3 (test invocation).** The suite is run as `QT_QPA_PLATFORM=offscreen .venv/bin/python -m
  pytest` (the `pytest` entry point has a stale shebang); any non-pytest probe that can reach a
  DB-writing path exports `DB_PATH` to a temp file first (ESC-043; `tests/conftest.py` already does
  this for pytest).
- **AP-4 (no persisted-state migration beyond the table drop).** The right dock's width and collapse
  state are in-memory only (A36 — no `QSettings` key), and the DOM/depth/footprint toggles were never
  persisted. The **only** persisted artefact that changes is the `footprint_cache` table (S7).
  Consequently no settings-key cleanup task exists, and the new dock suite asserts no new key is
  written (the existing `_RIGHT_PERSISTENCE_HINTS` scan stays, minus its stale `"active_trader"`
  hint).
- **AP-5 (documentation ownership).** `AC-D41.6`'s markdown-history markers are **Requirements-owned**
  and already applied; Build must not edit `requirements.md`, `docs/architecture.md`, `docs/plan.md`
  or `docs/plan_notes.md`. `usage.md`'s test-count sentence (DOC-1) will need a docs-only refresh
  after the suite size drops — owner/Analyst follow-up, not a Build task.
- **AP-6 (test count moves down).** Five suites are deleted and two more shrink, so the suite total
  **falls**; `AC-D41.5` requires green, not parity of counts. Any docs figure quoting a total must be
  re-measured rather than assumed (DOC-1).
- **AP-7 (escalations are not D41's work).** **14** entries are `open` today; ESC-035/039/040 (all
  `should-fix`, verified in `escalations.json`) go moot by removal (DG66), leaving **11** open and
  untouched — ESC-032/033/034/036/037/038/041/042/043/044/045, all BUILD/REQUIREMENTS-owned (ESC-038
  is REQUIREMENTS-routed and D41-neutral). Flipping the three moot ones to `addressed` is the **Code
  Reviewer's** action after re-verification (DG66) — not Build's, and not a task in these phases.
- **AP-8 (clean tree for verification).** Phase 3 runs from a clean tree so orphaned `__pycache__`
  for deleted modules cannot confuse the module-absence guards (AR-D41-12; DOC-3/ESC-001 precedent).
- **AP-9 (`OrderBookLevel` removal is inert).** `data/models.py::OrderBookLevel` has **zero**
  references in the tree today, so removing it cannot change behaviour; it is included because it is
  the depth feature's model (see FI-2).
- **AP-10 (KEEP coverage is re-homed, not dropped).** `footprint_cache_key` and
  `md_line_guard.assess` each have exactly **one** test today and both live in suites D41 deletes, so
  their assertions are **moved** in the same phase as the deletion: the key rule into
  `tests/test_d39_burst_search.py` (D39 is the surviving consumer), the guard thresholds into
  `tests/test_d38_events_news.py` (the D38 S0 lines are the surviving caller). `AC-D41.4`'s "remain
  and remain exercised by their tests" is then literally true.
- **AP-11 (per-phase green).** Each phase's consolidated state is green on its own suite selection,
  not merely at the end of Phase 3. This is why the depth assertions leave `tests/test_d27_reconnect.py`
  in Phase 1 (their subjects go there) while its one dock-title line leaves in Phase 2 (the rename
  lands there), and why the three deterministically-red suites (`test_d28_pacing.py`,
  `test_kill_switch.py`, `test_crosshair_axis_lane.py`) are re-pointed inside Phases 1–2 rather than
  left to fail in Phase 3.

### Flagged issues and dispositions (D41)

The full dispositions are in `docs/architecture.md` § *D41 increment*, § *Flagged issues and
Validator dispositions*; the requirements-side record is `docs/plan_notes.md` **RG-D41-1**.

- **FI-1** — `AC-D41.4`'s "validate orders with a resolving `ref_price`" is not what the code does;
  satisfying it verbatim needs a decision inside a removal. **Ratified (reading (a)), non-blocking** —
  the re-homing (`S4`+`S5`) is what the AC and the KEEP list demand. Recorded as RG-D41-1; **no
  Requirements escalation**.
- **FI-2** — `OrderBookLevel` is not in D41's named tokens but is the removed feature's model.
  **Accepted** — within "all associated code", inert; recorded as an explicit scope close-out and
  machine-checked by the guard's token set.
- **FI-3** — D41 must not be credited with the wide-candle / volume-overlap defect (DG68 open; the
  concluded investigation rules the footprint overlay **out**). **Accepted with the severity
  correction** — ESC-041 stays **blocking** and BUILD-owned; D41 touches neither
  `ui/candlestick_item.py` nor the volume-width math.
- **FI-4** — the requirements do not say whether the right dock's stable title/`objectName` may
  change. **Ratified** (`S6` renames to `"Portfolio"` and updates **all 17** consumers in the same
  phase, with a new guard).
- **FI-5** — `footprint_cache_key`'s name survives D41 and will read as a leftover. **Accepted** —
  kept verbatim; the rename stays **FS17**, out of D41; its only test is re-homed.
- **FI-6** — removing `test_order_entry_mkt.py` / `test_order_entry_side.py` deletes D26.4/D26.6
  coverage. **Accepted** — both import only `ui.active_trader_panel`; their intent is carried to the
  retained path by `tests/test_d41_retained_order_path.py`.

Handoff: canonical set complete — `docs/architecture.md` (§ *D41 increment*), `docs/plan.md` (this
section), `docs/plan_review.md` (`Status: APPROVED`, D41 cycle 2), and `docs/plan_notes.md`
(`RG-D41-1`, no escalation). Phase order: **Phase 1 → Phase 2 → Phase 3**, strictly sequential, then
Code Reviewer verification (which also re-verifies and closes ESC-035/039/040 as moot per DG66).

Status: superseded by the D42 section below (D41's `READY_FOR_TASK_MANAGER` was consumed by the D41
build/review; the D41 handoff record above is kept as history).

---

## D42 — Batch 18b: density-aware candle/volume body width (WS1) + mode-aware intraday depth and day presence (WS2) — validated 2026-10-15, **approved for build**

> **Status of this section.** Validated by Plan Artifact Editor & Validator (`Status: APPROVED`,
> 2026-10-15, **cycle 2 of 3**) and **approved for build** — it is **not** as-built. **D42 is a
> requirements-decision batch with no new feature**: it resolves the two **REQUIREMENTS-routed** Code
> Reviewer escalations and supplies the normative target that unblocks the two corresponding
> **BUILD** escalations (**ESC-041**, **ESC-037** — which stay BUILD-owned and are **not** absorbed
> here). **D41 is built/reviewed/committed (`b48133d`) and is NOT reopened.** Requirements of record:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-15 19:06) —
> `### D42` (`:3529`–`:3617`), `AC-D6.4` (revised), `AC-D7.1` (revised), the `AC-D9.2` note,
> `AC-D16.8` (extended), **`AC-D16.9`** (new), `A72`–`A73`, `R63`–`R64`, `DG68` (resolved) + `DG72`,
> `open_questions.md` **Q51/Q52** (answered 2026-10-15). Companion architecture:
> `docs/architecture.md` § *D42 increment* (Codebase Summary, `S1`–`S3`/`S13`–`S21`, components, data
> model, integrations, non-functional, risks `AR-D42-1`–`AR-D42-11`, supersessions). Review:
> `docs/plan_review.md` (D42 cycle 3, `APPROVED`).
>
> **Round-2 note.** This section is the **revision-2** plan: the round-1 required changes are folded
> in — **`RC-D42-1`** (`ChartPanel.update_last_bar`'s `_bars` trim is now owned by **Phase 2**; the
> false "file-disjoint / shared files: none" claim is replaced by the corrected partition, with
> `ui/chart_panel.py` as the one shared file and its two tasks sequenced into **different waves**;
> `AP-D42-1` rewritten), **`RC-D42-2`** (the D16 **load-path** assertions that `S17`/`S18`
> legitimately change are enumerated **with their cause** as **intent-preserving corrections**; Phase
> 3's goal is re-stated), and **`RC-D42-3`** (the WS1 evidence **states** the pixel unit, applies `F`
> in it, **measures** the repro pitch and asserts only unit-free relations). `S13`/`S14`,
> `S15`–`S19`, `S18` and `FI-D42-1`/`FI-D42-3`/`FI-D42-4` are unchanged in substance — they were
> ratified in round 1 and are not re-litigated.
>
> **Round-3 note (2026-10-16, `ESC-050`).** An **enumeration/accuracy amendment only** — no
> architectural decision, no `AC`, no phase boundary and no task changes; the D42 design is unchanged
> (built, 26/26 tasks, full offscreen suite green). The D42 impact analysis **under-enumerated** the
> suites changed by design in two independent places, and the amendment closes both: **(1)** the
> **six suites that merely *drive* the load path** with a fixed-size `req_historical_data` reqId stub
> — `tests/test_d24_popouts.py` (7), `tests/test_phase3_fixpass.py` (7),
> `tests/test_d24_alarm_full_chain.py` (2), `tests/test_d24_smoke_gate.py` (1),
> `tests/test_d24_9_popout_persistence.py` (1), `tests/test_d28_tick_burst_baseline.py` (1) — **19**
> in total, now enumerated **with their cause**; **(2)** the further sites **inside** the three D16
> files, so that **all 14** changed test functions in those files are named. It also states the
> **invariant** and the generalisable **impact-analysis enumeration rule** (both below), and adds a
> **Frozen Interfaces** checklist to the architecture document.

### The two workstreams

- **WS1 — the candle/volume overlap (ESC-042 → unblocks ESC-041).** Rendered body width becomes
  `body = min( max(0.65 × pitch, F), pitch )` (one shared pure helper; `pitch` = inter-bar
  centre-to-centre distance, `F` = the existing 4-px legibility floor, all in the **same** unit);
  **`gap = pitch − body ≥ 0` always**; **`gap > 0` whenever `pitch > F`**; at `pitch ≤ F` bodies may
  **abut** (gap `0`, owner-confirmed Q51); the **wick stays a cosmetic 1-device-px line**; **volume
  inherits the same capped `w`** (`AC-D9.1`/`AC-D9.2` intent unchanged). Sites:
  `ui/candlestick_item.py::CandlestickItem._draw_candles` (the clamp, `:136`–`:138`) and the volume
  width math in `ui/chart_panel.py` (`::ChartPanel._clamp_half_width` `:1229`,
  `::ChartPanel._refresh_candles` `:1303`, `::ChartPanel._refresh_live_bar` `:1352`).
- **WS2 — the RTH/ETH intraday depth + present-but-empty day (ESC-038/ESC-037).** A **≥ 30 trading
  session** floor before the current session for each intraday timeframe in **both**
  `ext_hours=False` (RTH 09:30–16:00 ET) and `ext_hours=True` (ETH 04:00–20:00 ET), delivered as
  **backwards-extending chained fetches** through the existing wave pump; a **session counts only
  with a bar inside the current mode's window**; a **present-but-empty** trading day is a **missing
  span**; the bar cache/key is **mode-aware** in both directions. Sites:
  `services/backfill_service.py`, `data/bar_cache.py`, `data/db.py`, `config/settings.py`,
  `ui/ticker_session.py`, `ui/main_window.py`, and `ui/chart_panel.py` (the floor-aware `_bars` trim
  **only** — the third `SESSION_BAR_CAP` site, `RC-D42-1`).

**Out of scope — do NOT plan these.** The other open BUILD escalations: **ESC-032** (Position `id`),
**ESC-033** (Load Chart button), **ESC-034** (watchlist flash timer), **ESC-036** (priming `5 secs`),
**ESC-043** (`HELD`/`H` rows), **ESC-044** (option contract fields), **ESC-045** (Account Summary).
They are separate work with no task yet. **ESC-041** and **ESC-037** stay BUILD-owned — D42 supplies
the normative target they are re-checked against; D42 does not absorb them (the Code Reviewer flips
them after re-verification, and flips **ESC-038/ESC-042** from `open` on the same pass). No D42 path
reaches the order machinery, the D38/D39 substrate, or the D41 removals.

### Coverage / traceability (D42)

| Requirement / journey | Plan treatment | Phase | Supersession recorded? |
|---|---|---|---|
| `AC-D6.4` (revised: `body = min(max(0.65×pitch, F), pitch)`, `body <= pitch`, floor yields at `pitch < F`, wick stays 1 device px; `F` is 4 **ViewBox logical px** = 8 device px at DPR 2) | `S13`+`S14`; `ui/candlestick_item.py::CandlestickItem._draw_candles` (`:136`–`:138`), `ui/chart_panel.py::ChartPanel._clamp_half_width` (`:1229`/`:1242`–`:1244`) | 1 | **Yes** — the former *unconditional* "body remains `>= 4` device pixels wide" |
| `AC-D7.1` (revised: `gap >= 0` hard; `> 0` whenever `pitch > F`; `0` acceptable at `pitch <= F`; 35 % intent unchanged) | `S13`; Journey 8 edge case | 1 | **Yes** — the former "the gap remains positive" + the D7 dense-view edge case (Q51) |
| `AC-D9.1`/`AC-D9.2` + the `:1476` note (volume width == price body width, same capped `w`) | `S13` (one shared helper; volume consumes the same capped `w`) | 1 | n/a (intent unchanged) |
| `AC-D16.8` (extended: ≥ 30 trading sessions, **RTH and ETH**; a session counts only with a bar inside the current mode's window; all five intraday windows fall short; mode isolation) | `S15`, `S17`, `S18`, `S19`, `S20` — incl. **all three** `SESSION_BAR_CAP` sites + `prune`'s `keep` | 2 | **Yes** — the RTH-only default (Q52) |
| `AC-D16.9` (new: mode-aware day presence + mode-aware cache; present-but-empty = missing span, both directions; measurables (a)/(b)/(c)) | `S15`, `S16`, `S19`; Data Model `bars` | 2 | n/a (new criterion) |
| `AC-D16.1`/`AC-D16.3`/`AC-D16.4` (unchanged) | Phase 2 non-regression + Phase 3 | 2, 3 | n/a — preserved |
| `AC-D16.7` (ESC-023 New-Year exception) | Phase 3 non-regression | 3 | n/a — untouched |
| Journey 7 / Journey 8 edge cases (dense view, high-DPI, doji, single-bar fallback) | `S13`, `S14` | 1 | n/a |
| Journey 17 edge cases (internal hole, no-fill, genuine closures, Ext Hours mode switch, empty cache, all timeframes/any symbol) | `S15`–`S19` | 2 | n/a |
| `A72`, `R63`, `R64`, `DG72` | `S13`, `S17`, `S18`, `S21`; risks `AR-D42-1`–`AR-D42-6` | 1, 2 | n/a |
| Out-of-scope escalations (ESC-032/033/034/036/043/044/045; ESC-041/ESC-037 BUILD-owned) | Explicitly excluded | — | n/a — correct |

Both workstreams' `ext_hours=True` limbs are covered (WS1 via the ESC-041 Ext-Hours-ON repro; WS2 via
`S15`–`S19` for both modes), and each workstream states its own RED→GREEN evidence (below).

### Phases (D42)

Three phases. **Phase 1 and Phase 2 share exactly one file** — `ui/chart_panel.py` — so they are
**not** file-disjoint: Phase 1 edits its **width** path, Phase 2 edits
`ChartPanel.update_last_bar`'s **`_bars` trim** (`:1150`–`:1157`, the **third** `SESSION_BAR_CAP`
site, `RC-D42-1`). The two `ui/chart_panel.py` tasks are therefore **sequenced into different
waves** — Phase 2's trim runs **after** Phase 1's width edit (`build_wave.py` forbids two
`in_progress` tasks with overlapping `touches_files`). Phase 2's **other** files are disjoint from
Phase 1, so those tasks may still co-schedule with Phase 1. **Phase 3 depends on both.**

#### Phase 1 — Density-aware candle/volume body width (WS1)

- **Goal:** at any bar density the rendered candle body never exceeds the inter-bar pitch, the
  inter-bar gap is never negative, the 4-px legibility floor still binds whenever the pitch allows
  it, and the volume bar width is the **same** capped width as the price body — while the wick stays
  a cosmetic 1-px line and the D28.4 render split / ESC-013 / ESC-020 ordering is preserved.
- **Covers:** `AC-D6.4` (revised), `AC-D7.1` (revised), the `AC-D9.2` note, Journey 7 and Journey 8
  edge cases; `A72`, `R63`.
- **Requirements/journeys:** Journey 7 (steps 1–2, edge cases "dense 1-min", "doji", "high-DPI"),
  Journey 8 (steps 1, edge case "dense intraday view keeps a **non-negative** gap"), `AC-D6.4`
  (i)/(ii)/(iii) + its measurable paragraph (the repro at ≈ 3.83 **ViewBox logical px** —
  **measured**, not hard-coded — and the ≈ 8.86 logical-px non-dense case; `F = 4.0` in that same
  unit), `AC-D7.1`'s three regimes, `AC-D9.1`/`AC-D9.2`.
- **Dependencies:** none on Phase 2 — but Phase 1's `ui/chart_panel.py` **width** task must complete
  before Phase 2's `ui/chart_panel.py` **trim** task (the one shared file; different waves).
- **Deliverable:** one pure helper + its three call sites (**the `ui/chart_panel.py` width path
  only** — the floor-aware `_bars` trim belongs to Phase 2) + the corrected/added suites (below).

#### Phase 2 — Mode-aware intraday depth floor and day presence (WS2)

- **Goal:** each intraday timeframe in each mode loads **≥ 30 trading sessions before the current
  session**; a session counts only when it holds a bar inside the current mode's session window; a
  present-but-empty trading day is reported as a **missing span** (not filled); RTH and ETH never
  cross-contaminate, in the presence pass or in the cache; the floor is actually **retained and
  displayed** (all **three** `SESSION_BAR_CAP` sites become floor-aware — `TickerSession.set_bars`
  `:300`, `TickerSession._append_bar` `:313`, and **`ChartPanel.update_last_bar`'s `_bars` trim
  `:1150`–`:1157`** — plus `BarCache.prune`'s `keep`); and the D16 no-fill / genuine-closure /
  shortfall-report rules are unchanged.
- **Covers:** `AC-D16.8` (extended, both modes), `AC-D16.9` (new, both modes), Journey 17 edge cases
  (internal hole, no-fill, genuine closures, Ext Hours mode switch, empty cache, all timeframes/any
  symbol), `A73`, `R64`, `DG72`; `AC-D16.1`/`AC-D16.3`/`AC-D16.4` as the **non-regression contract**.
- **Dependencies:** **one ordering dependency on Phase 1** — the `ui/chart_panel.py` floor-aware
  `_bars` trim must land **after** Phase 1's `ui/chart_panel.py` width edit (the single shared file,
  so the two tasks sit in different waves). Phase 2's **other** files are disjoint from Phase 1.
  Internally ordered: `floor_bar_budget` must land **before** its consumers (the two session cap
  sites, the panel trim, and `prune`'s `keep`); the presence predicate and the cache key must land
  **before** the floor span is wired (the floor is measured against mode-aware presence).
- **Deliverable:** the mode-aware presence predicate + mode-aware `bars` key/migration + the
  `min_sessions` floor span + the floor-aware caps (**three cap sites + `prune`'s `keep`**) + the
  mode threading + the corrected/added suites.

#### Phase 3 — Reconciliation, non-regression and the correction record

- **Goal:** the whole offscreen suite is green, with **every** existing D16/D27/D28/D41 assertion
  either keeping its **exact** expectation or **corrected intent-preserving** to the new normative
  target — **none weakened, none deleted** — and every such correction recorded **with its cause**
  (the floor span, the removed empty-cache branch, the floor-aware prune/budget), the enumeration being
  **complete by rule** rather than by the suites the design happened to name (the `ESC-050` invariant:
  every suite that merely **drives** the changed load path is in scope); the two superseded
  criteria and the three additional artifacts are recorded for Task Manager / Build / Code Reviewer;
  the D42 increment is ready to merge into the canonical docs.
- **Covers:** the D42 correction record; `AC-D16.7` (ESC-023) and `AC-D16.1`/`AC-D16.3`/`AC-D16.4`
  as regression guards; the four escalations' disposition (ESC-041/ESC-037 stay BUILD-owned and are
  re-checked against the revised criteria; ESC-038/ESC-042 are resolved on the requirements side).
- **Dependencies:** **both** Phase 1 and Phase 2 consolidated.
- **Deliverable:** the full-suite green run + the correction-record entries, including the enumerated
  D16 **load-path** corrections and the `ESC-050` load-path-**driving** suite corrections
  (intent-preserving; no new behaviour).

### Per-file `touches_files` map and sequencing constraint (D42)

**Sequencing constraint (binding).** Build runs a wave frontier: two tasks with overlapping
`touches_files` must never be `in_progress` in the same wave. The partition below **is** the
parallelism plan (one task per file). **The two workstreams share exactly one file —
`ui/chart_panel.py`** (Phase 1: the **width** path; Phase 2: `ChartPanel.update_last_bar`'s `_bars`
trim `:1150`–`:1157`, the third `SESSION_BAR_CAP` site). The two `ui/chart_panel.py` tasks therefore
**must sit in different waves**: Phase 2's trim is **sequenced after** Phase 1's width edit. Every
**other** Phase 2 file (`services/backfill_service.py`, `data/bar_cache.py`, `data/db.py`,
`config/settings.py`, `ui/ticker_session.py`, `ui/main_window.py`) is disjoint from Phase 1, so those
tasks may be co-scheduled with Phase 1's. `ui/main_window.py` stays a **single** Phase-2 task (hot
file); Phase 3 adds no production edit.

**Phase 1 — WS1 file map**

| File | Change | Existing tests touching it |
|---|---|---|
| `ui/candlestick_item.py` | New pure `capped_body_half_width(...)`; `_draw_candles` calls it (replacing the unconditional `min_w` clamp, `:136`–`:138`); `set_data(..., pitch=…)` | `tests/test_candlestick_wick.py` (stays green — wick/cosmetic assertions only), `tests/test_candle_spacing.py` (**correct**), `tests/test_chart_dpi.py` (**correct**) |
| `ui/chart_panel.py` | **Width path only** (`RC-D42-1`; the `_bars` trim is Phase 2): `_compute_candle_half_width` also returns/stores the display-x pitch; `_clamp_half_width` delegates to the shared helper; `_refresh_candles`/`_refresh_live_bar` pass the pitch | `tests/test_volume_width.py` (**correct**), `tests/test_chart_dpi.py` (**correct**), `tests/test_d28_4a_render_layers.py`, `tests/test_volume_ceiling.py`, `tests/test_volume_d21.py` (stay green — no width-formula assertions) |
| `tests/test_candle_spacing.py` | **Correct**: string-presence → regime/geometry assertions on the shared helper (`pitch > F`, `pitch == F`, `pitch < F`) while preserving the 0.325 / 35 % intent | — |
| `tests/test_volume_width.py` | **Correct**: the dense `≈ 4.0 px` legs → `body == pitch`, `gap >= 0`, `volume_width == body_width`; the non-dense equality test unchanged | — |
| `tests/test_chart_dpi.py` | **Correct**: the dense `body_device_px >= 4.0` leg moves to the **non-dense** dataset; the dense dataset asserts `body_device_px <= pitch_device_px` (and `== pitch` at the repro) | — |
| `tests/test_d42_candle_width.py` **(new)** | **Add**: the ESC-041 repro geometry guard (192-bar SPY 5-min Ext-Hours, 900 px pane, DPR 2; the pitch is **measured** from the rendered series — ≈ 3.83 **ViewBox logical px**, `F = 4.0` in the **same** unit, i.e. 8 device px at DPR 2) asserting `body <= pitch` and `body == pitch`; and the non-dense case (78 bars, measured pitch ≈ 8.86 logical px → `body == max(0.65×pitch, F) > F`), measuring the body from the `QPicture` bbox. No assertion on `F` in device px (`RC-D42-3`) | — |

**Phase 2 — WS2 file map**

| File | Change | Existing tests touching it |
|---|---|---|
| `services/backfill_service.py` | Mode-aware presence predicate (window membership) used by `find_missing_spans` **and** exported for `MainWindow`; `min_sessions` floor span (backwards, collapses when filled); `floor_bar_budget(timeframe, ext_hours)`; empty-cache case returns the floor span when `min_sessions > 0` | `tests/test_backfill_service.py` (**extend** — existing cases keep exact semantics, `min_sessions=0`), `tests/test_d27_backfill_granularity.py` (**extend**), `tests/test_history_backfill*.py` (**correct** — load path) |
| `data/bar_cache.py` | `save_bars`/`get_bars`/`prune` take `ext_hours` (keyword, default `True`); the flat `RETENTION_BARS` stays the default | `tests/test_d28_4e_bar_cache_retention.py` (stays green — flat default preserved), `tests/test_d25_alarm_monitor.py`, `tests/test_d27_phantom_alarms.py`, `tests/test_watchlist_d14_midrag.py` (stays green — default mode) |
| `data/db.py` | `bars` DDL gains `ext_hours`; `_migrate_schema` gains the guarded, idempotent table rebuild (legacy rows → `ext_hours = 1`) | `tests/test_db_schema.py` (**extend**), `tests/test_d42_mode_cache.py` (**new**) |
| `config/settings.py` | `MIN_INTRADAY_SESSIONS = 30` (the floor's single tunable) | — |
| `ui/ticker_session.py` | Session mode for its own cache reads/writes (`get_bars` `:295`, D39 preload `:684`); the two cap sites use `floor_bar_budget(...)` (`:300`, `:313`) | `tests/test_d28_2_sessions.py::test_session_bar_cap` (**correct**), `tests/test_d28_2_sessions.py` (rest green), `tests/test_d39_burst_search.py` (re-verify — the baseline preload path) |
| `ui/chart_panel.py` | **The third `SESSION_BAR_CAP` site (`RC-D42-1`):** `ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`) uses `floor_bar_budget(timeframe, ext_hours)` instead of the flat `settings.SESSION_BAR_CAP`; the head-prune still rebuilds the collapse map + invalidates the study cache. **This task must sit in a different wave from Phase 1's `ui/chart_panel.py` task** (one shared file) and lands **after** `floor_bar_budget` exists | `tests/test_d28_4f_panel_bar_cap.py` (**correct**), `tests/test_d28_4a_render_layers.py` / `tests/test_volume_ceiling.py` (stay green) |
| `ui/main_window.py` | `load_chart`: pass the mode + `min_sessions` at `:1630`/`:1648`/`:1662`; **remove** the empty-cache single-window branch (`:1668`–`:1684`) — which requires bypassing the `find_missing_spans(...) if cached else []` guard at `:1647`–`:1652` and the empty-cache early return at `services/backfill_service.py:205`–`:206` when `min_sessions > 0`; `_finalize_history_wave`: mode at `:1970`/`:1973`/`:1974` + `keep=floor_bar_budget(...)`; `_missing_backfill_trading_days` uses the shared presence predicate (`:2052`–`:2054`) | `tests/test_history_backfill_loadpath.py` (**correct** — the floor span, the removed branch, the floor-aware `keep`), `tests/test_history_backfill.py` (**correct**), `tests/test_history_backfill_disconnect.py` (**correct**), **and — `ESC-050` — the six suites that merely *drive* this load path with a stubbed feed:** `tests/test_d24_popouts.py`, `tests/test_phase3_fixpass.py`, `tests/test_d24_alarm_full_chain.py`, `tests/test_d24_smoke_gate.py`, `tests/test_d24_9_popout_persistence.py`, `tests/test_d28_tick_burst_baseline.py` (**correct** — test-only: widen each fixed-size reqId stub to an unbounded `itertools.count` source; the invariant below), `tests/test_dock_widths_d17.py` etc. (unaffected — no dock/geometry change) |
| `tests/test_d28_4f_panel_bar_cap.py` | **Correct**: assert the derived budget (monkeypatch/assert against the helper) while keeping the "cap is enforced / oldest dropped" invariant | — |
| `tests/test_d42_day_presence.py` **(new)** | **Add**: `AC-D16.9` measurables (a)/(b)/(c) — pre/post-only day → non-empty **RTH** span and **no** ETH span; RTH-only day → present in **both** modes | — |
| `tests/test_d42_mode_cache.py` **(new)** | **Add**: the migration (rows preserved, tagged, per-mode reads) and no-cross-contamination (write ETH, read RTH → empty, and the reverse) | — |
| `tests/test_d42_depth_floor.py` **(new)** | **Add**: the per-timeframe, per-mode session-count guard — drive the real load path with a stubbed historical feed and assert `≥ 30` distinct mode-valid sessions **before** the current one, for each intraday timeframe in **both** modes; plus the budget guard (the floor survives `prune`/the in-memory trim) | — |

**Shared files across phases: exactly one — `ui/chart_panel.py`.** Phase 1 owns its **width** path;
Phase 2 owns `ChartPanel.update_last_bar`'s floor-aware `_bars` trim (`:1150`–`:1157`, the third
`SESSION_BAR_CAP` site). Those two tasks must be in **different waves** — Phase 2's trim is
**sequenced after** Phase 1's width edit (`RC-D42-1`). Every other file is single-phase:
`ui/candlestick_item.py` is Phase 1 only; `services/backfill_service.py`, `data/bar_cache.py`,
`data/db.py`, `config/settings.py`, `ui/ticker_session.py` and `ui/main_window.py` are Phase 2 only.
Phase 3 adds no production edit (reconciliation + docs only).

### Tests: corrected vs added, and the RED→GREEN evidence (D42)

**Corrected (never weakened, never deleted — the D42 correction record's mandate).**

| Suite | What is corrected | Why it must change |
|---|---|---|
| `tests/test_candle_spacing.py` (`:4`–`:10`) | The string-presence check (`"median_diff * 0.325"` / `"gap 35%"` in the source) → **regime/geometry assertions** on the shared helper | It "never renders" (the correction record's words) and cannot distinguish the old unconditional floor from the capped rule |
| `tests/test_volume_width.py` (`:103`–`:104`) | The dense legs `measured_body * px_per_sec ≈ 4.0` and `vol_width * px_per_sec ≈ 4.0` → `body == pitch`, `gap >= 0`, `vol_width == body_width` | It "asserts body == volume and ~4 px but never relates width to pitch" (the correction record's words); at the revised criterion the dense body is the pitch, not 4 px |
| `tests/test_chart_dpi.py` (`:245`–`:250`) | The dense `body_device_px >= 4.0` leg → the **non-dense** dataset carries the `>= F` and `> wick` claims; the dense dataset asserts `body_device_px <= pitch_device_px` | **Added by Plan** — the D42 correction record names only the two width suites, but this DPR-2 probe asserts the same **unconditional** floor in device pixels and would fail against the revised criterion |
| `tests/test_d28_2_sessions.py::test_session_bar_cap` (`:166`) | `len(kept) == SESSION_BAR_CAP` → the derived budget for `(timeframe, ext_hours)`, invariant "oldest dropped / newest kept" preserved | **Added by Plan** — `AC-D16.8`'s floor exceeds the flat 5000 for `1 min` (both modes) and `5 mins` (ETH), so the session cap must be floor-aware |
| `tests/test_d28_4f_panel_bar_cap.py` (`:53`) | `len(panel._bars) == settings.SESSION_BAR_CAP` → the derived budget for `(timeframe, ext_hours)`, invariant "oldest dropped / newest kept" preserved | **Added by Plan** — same reason as the session cap, for the **third** `SESSION_BAR_CAP` site (`ChartPanel.update_last_bar`'s `_bars` trim, `:1150`–`:1157`). Its **production subject is Phase 2**, so this correction sits in **Phase 2** too (`RC-D42-1`) |

**Corrected — D16 load-path (`RC-D42-2`; completed by `ESC-050`).** These change **by design**, because
the default load mode is **ETH** (`MainWindow.ext_hours_btn` checked at `:244`; the `:1570` fallback)
and because `S17` removes the empty-cache single-window branch while `S18` changes `prune`'s `keep`.
Every one is **intent-preserving**: the assertion's guarantee survives, only its expected
value/branch changes — **none weakened, none deleted**. The table names **all 14 changed test
functions** in the three D16 files: the **9** named in round 2, the **3** further sites `ESC-050`
records (`t40_t03`, `t43_t03`, `t44_t03`), and the **2** found by Plan re-verification (`t39_t04`,
`t39_t05`). `ESC-050` also names `t40_t05`, which is **unchanged** — its correction in fact lands in
`t40_t04`'s tail assertion (see the verification note below). Line citations are at the D42 baseline
`b48133d`.

| Suite / case | Assertion today | Cause of the correction | Intent preserved |
|---|---|---|---|
| `tests/test_history_backfill_loadpath.py::test_t39_t02` (`:238`) | `assert stub.calls == []` | **The floor span** — 5 seeded ETH sessions < 30, so the floor issues requests | "A cache that **satisfies the floor** and reaches *now* issues no **redundant** request" |
| `::test_t39_t03` (`:255`–`:257`) | `len(stub.calls) == 1`, `endDateTime == ""` | **The empty-cache branch `S17` removes** (`ui/main_window.py:1668`–`:1684`) | "An empty cache is covered by the **planner**" — now one floor span from the floor day to *now*, not a special branch |
| `::test_t39_t01` (`:202`/`:206`) | `len(stub.calls) == len(plans)` where `plans` come from the test's own `find_missing_spans(cached_ts, NOW, tf)` (no `min_sessions`) | The load path now passes the floor; the test's own planner call must pass it too | "One request per planned chunk, `endDateTime` non-empty, reqIds tracked" |
| `::test_t39_t06` (`:431`) / `::test_t39_t07` (`:477`) | `assert len(bars) == RETENTION_BARS` | **The floor-aware `keep`** — `5 mins`/ETH derives 6,624 (> 5,000) | The retention invariant at the **derived** budget: oldest dropped, newest kept, no fabricated bar |
| **`ESC-050`** — `::test_t39_t04` (`:286`–`:293`) | the `save_bars`/`get_bars` spies are `def spy_save(bars)` / `def spy_get(s, t)` | **`S19` mode threading** — the load path now passes `ext_hours` to `BarCache.save_bars`/`get_bars`, so the spies must forward it (`**kwargs`) or the forwarded call raises | The spies still count the save/get calls and the bar counts they carry |
| **`ESC-050`** — `::test_t39_t05` (`:363`) | `assert win._history_req_ids == set()` | **The floor span** — the new session starts its **own** wave (its floor span), so its in-flight id set is not empty | "The cancelled session's ids never leak into the new wave" — asserted as `isdisjoint(old_ids)` / `stale not in …` |
| `tests/test_history_backfill.py::test_t40_t01` (`:285`) | `assert len(stub.calls) == 1` | **The floor span** (the seed covers one internal hole only) | The AC-D16.5 hole is filled by its own chunk; the floor is separate work |
| **`ESC-050`** — `tests/test_history_backfill.py::test_t40_t03` (`:388`–`:390`) | `assert "incomplete" not in msg and "missing" not in msg and "failed" not in msg` | **The floor span** — a floor shortfall **is** now legitimately reported, so "no shortfall message" is wrong | "A genuine closure is never a shortfall" — asserted precisely: the closure days (**2026-09-05/06/07**) are never **named** missing |
| `tests/test_history_backfill.py::test_t40_t04` (`:451`–`:457` **and** `:480`–`:485`) | `len(wave_calls) == len(plans)` **and** the same "no shortfall message" form | Same as `t39_t01` — **plus** the floor shortfall (`t40_t04` carries **two** corrected assertions) | Multiple requests, continuous result, no silent hole; and "no **answered** day is reported as missing" (the floor's own further-back days may be) |
| **`ESC-050`** — `tests/test_history_backfill.py::test_t40_t05` | **no shortfall-message assertion in either revision** (see the verification note below) | — (kept in the list because `ESC-050` names it and it is the same defect class; the correction landed in **`t40_t04`'s tail assertion**) | "No **answered** day is reported as missing" |
| `tests/test_history_backfill.py::test_t40_t06` (`:590`) | `len(stub.calls) == 1`, `endDateTime == ""` | **The removed empty-cache branch** | An empty cache renders cleanly from the planner's floor span |
| **`ESC-050`** — `tests/test_history_backfill_disconnect.py::test_t43_t03` (`:249`–`:255`) | `assert any(date(y, m, d).isoformat() in msg for y, m, d in MISSING_DAYS)` | **The floor span** — the status bar previews only the **first five** missing days (now the floor days), while `_LOG.warning` carries the full list | "Every seeded missing day is surfaced" — asserted against the **log**, and `"incomplete"` is still required |
| **`ESC-050`** — `tests/test_history_backfill_disconnect.py::test_t44_t03` (`:481`–`:485`) | the same status-message form | Same as `t43_t03` | Same — asserted against the **log**; the timeout/disconnect distinction is kept |
| `tests/test_history_backfill_disconnect.py::test_t43_t06` (`:362`) | `len(stub.calls) == 1` | **The removed empty-cache branch** | The wave finalises once and a later disconnect is a no-op |
| `tests/test_d28_4f_panel_bar_cap.py` (`:53`) | `len(panel._bars) == settings.SESSION_BAR_CAP` | **`S18`**, not the presence predicate — the panel trim is floor-aware | "The cap is enforced / the oldest bars are pruned", asserted against the **derived** budget |

**Verification note on `t40_t05` (`ESC-050`).** `ESC-050` names `t40_t05` among the extra sites.
Re-verified against `git diff b48133d` on the live tree (Validator, cycle 3): the "no shortfall
message" → "no **answered** day reported as missing" correction lands in **`test_t40_t04`'s tail
assertion** (`b48133d:484`–`:485`, inside `test_t40_t04`, which spans `:446`–`:490`) —
`msg = win.status_bar.currentMessage().lower()` then `assert "incomplete" not in msg and "missing"
not in msg and "failed" not in msg`. `test_t40_t05_switch_mid_flight_isolated` (b48133d
`:495`–`:585`) carries **no** shortfall-message assertion in either revision and is green unchanged
(the diff shows no hunk for it). The site is kept in the list (same defect class, and `ESC-050` names
it) with the correction located precisely; `test_t40_t04` therefore carries **two** corrected
assertions, and the three D16 files carry **14** changed test functions in total (verified by the
`git diff -U0 b48133d` hunk headers: `test_history_backfill_loadpath.py` 7 — `t39_t01`…`t39_t07`;
`test_history_backfill.py` 4 — `t40_t01`, `t40_t03`, `t40_t04`, `t40_t06`;
`test_history_backfill_disconnect.py` 3 — `t43_t03`, `t43_t06`, `t44_t03`).

**Corrected — load-path-*driving* suites (`ESC-050`).** These suites are **not** D16 suites and were
enumerated nowhere. They change **by design** for one reason only: each **drives
`MainWindow.load_chart`** (directly or through a pop-out / reconnect / smoke-gate path) while stubbing
`md_manager.req_historical_data` with a **fixed-size** reqId iterator. `S17`'s floor span makes one
intraday load issue **many** chunks (an empty-cache `5 mins` load plans **9**), so the **second**
`next(hids)` raises `StopIteration` — a **fixture-exhaustion** failure, **not** a product defect. The
correction is **test-only** and mechanical: widen each stub to an **unbounded** id source
(`itertools.count(<first>)`, the `P2-T19` precedent at `tests/test_d28_2_sessions.py:41`), leaving
`lambda *a, **k: next(hids)` unchanged so the ids stay deterministic and distinct. **No assertion is
weakened, skipped or xfailed.** (Build-side fix: **`ESC-048`**, BUILD, blocking.)

| Suite | Failing cases | Cause of the correction | Intent preserved |
|---|---|---|---|
| `tests/test_d24_popouts.py` | **7** (every test in the file) | the floor span — the stub was `hids = iter([6101, 6102, 6103])` | Every pop-out/reconnect assertion is untouched; the stub only has to cover **every** request the load path makes |
| `tests/test_phase3_fixpass.py` | **7** (of the 9 tests; `fix2a`–`fix2e` never load a chart) | the floor span — `hids = iter([7101, 7102, 7103])` | Same — the `_restore_popouts` no-duplicate behaviour is asserted unchanged |
| `tests/test_d24_alarm_full_chain.py` | **2** (every test in the file) | the floor span — `hids = iter([8101, 8102])` | Same — the alarm full chain is asserted unchanged |
| `tests/test_d24_smoke_gate.py` | **1** (every test in the file) | the floor span — `hids = iter([9601, 9602])` | Same — the smoke gate is asserted unchanged |
| `tests/test_d24_9_popout_persistence.py` | **1** (of the 2 tests; `test_popout_save_load_delete` never boots a `MainWindow`) | the floor span — `hids = iter([7101])` (a **single** id: the first `next` already exhausts it) | Same — the pop-out persistence assertions are unchanged |
| `tests/test_d28_tick_burst_baseline.py` | **1** (every test in the file) | the floor span — `hids = iter([9101, 9102])` | Same — the ≤2×/≤5× tick-burst baseline ratio is asserted unchanged |

**Total changed by design: 19 load-path-driving cases in these six suites + 14 changed test functions
in the three D16 files.** All six suites pass at `b48133d` (pre-D42) and are red post-D42 **only** on
the stub exhaustion — the same mechanism `ESC-048` reports.

**The invariant (`ESC-050`).** Stated so it can be checked **before** dispatch, not discovered by a
reconciliation task:

> **Any test that drives `MainWindow.load_chart` with a stubbed `req_historical_data` must use an
> unbounded reqId source** — `itertools.count(...)`, never a fixed-size `iter([...])` — **because the
> floor span makes a load issue many requests.** Any test asserting the **exact number** of historical
> requests, **one** request/chunk per load, or the **empty-cache single-window branch** changes **by
> design** and belongs in this correction record **with its cause**.

**Impact-analysis enumeration rule (generalisable — `ESC-050`, applies to every future increment).**
This is the **second** under-count in this batch (the first was round 1's `FI-D42-2`: the D42
correction record named two enshrining suites where **five** exist). Both had the same cause, so the
rule is recorded rather than the incident:

1. **Enumerate by call site of the changed entry point — not by the suites the design names.** For each
   production symbol the increment changes (here: `MainWindow.load_chart`, `TickerSession.set_bars` /
   `_append_bar`, `BarCache.save_bars` / `get_bars` / `prune`, `ChartPanel.update_last_bar`,
   `find_missing_spans`), find **every** test that reaches it — **including tests that only *drive* it**
   (stub the feed, boot a `MainWindow`, click a toolbar button, restore a pop-out, run a smoke gate)
   and assert something downstream.
2. **The suites the design names are a *seed*, never the answer.** In D42 the seed was the three D16
   suites; the real set was **14 changed test functions in those three files** *plus* **19
   load-path-driving cases in six further suites** that merely drive the load path.
3. **A fixed-size stub of a changed feed is a defect *class*, not a one-off.** Grep the whole suite for
   fixed-size stubs of the changed call (`iter([...])` feeding `next(hids)` / `lambda *a, **k: next(...)`)
   and correct **all** of them in one scoped task, before dispatch — the `ESC-048`/`ESC-050` pair.
4. **State the invariant in the correction record** so the enumeration is verifiable by a rule, not by
   re-reading the diff: an enumeration that is asserted to be complete must either **be** complete or be
   replaced by the rule that generates it.

**Re-verified — exact semantics kept:** `tests/test_d39_burst_search.py` (the D39 baseline preload now
passes the mode), `tests/test_backfill_service.py` + `tests/test_d27_backfill_granularity.py` (their
seeds are complete days and `min_sessions` defaults to `0`, so their exact expectations hold; the new
mode-aware cases are additions), `tests/test_d28_4e_bar_cache_retention.py` (flat default preserved).

**Added (new suites).** `tests/test_d42_candle_width.py` (WS1 geometry guard),
`tests/test_d42_day_presence.py` (`AC-D16.9` (a)/(b)/(c)), `tests/test_d42_mode_cache.py`
(migration + no cross-contamination), `tests/test_d42_depth_floor.py` (the per-timeframe, per-mode
session-count guard + the budget guard).

**RED→GREEN evidence each workstream must produce (both runnable offscreen, no live TWS).**

- **WS1 (Phase 1).** **Unit, stated explicitly (`RC-D42-3`):** every width below is in the **ViewBox
  logical-pixel unit that `px_per_sec` yields** (`vb.width() / x_span` — the unit
  `ui/candlestick_item.py:136`'s `min_w = 2.0 / px_per_sec` already uses). `F = 4.0` in that unit is
  **8 device px at DPR 2**; the requirement's literal "4 device pixels at DPR 2" is the same
  legibility intent and `AC-D6.4`'s operative clause is "measured in the **same** pixel unit"
  (`FI-D42-4`/`AP-D42-5`). The requirement's `3.83` / `8.86` figures are **indicative only** (they
  depend on the ViewBox width the probe actually gets), so the test **measures** the repro pitch from
  the rendered series instead of hard-coding it, and the load-bearing assertions are the unit-free
  relations `body <= pitch` and `body == pitch` — **not** `F == 4.0` device px.
  Render the **real** `CandlestickItem` at **DPR 2** for the ESC-041 repro (192 bars, 5-min, Ext
  Hours ON, 900 px pane; pitch ≈ 3.83 logical px, **measured**) and measure the **rendered** body
  from the `QPicture` bounding box (never re-derive the formula): **RED pre-fix** — the body is the
  flat 4.0-logical-px floor, which **exceeds the measured pitch**, i.e. a contiguous zero-gap pixel
  run between adjacent body centres; **GREEN post-fix** — `body <= pitch` (and `body == pitch` at
  this density). Non-dense case (78 bars; pitch **measured**, ≈ 8.86 logical px):
  `body == max(0.65 × pitch, F) > F`, wick still 1 device px. Volume: the rendered candle body and
  `volume_bars.opts['width']` are equal within `rel=0.02` at **both** densities.
- **WS2 (Phase 2).** (a) Seed a trading day with only pre/post bars → `find_missing_spans(cached,
  now, tf, ext_hours=False)` returns a **non-empty** span covering that day's RTH window (**RED
  pre-fix**: returns `[]`), and `ext_hours=True` returns **no** span for that day. (b) Seed a day with
  only RTH bars → **both** the `ext_hours=False` and the `ext_hours=True` calls report it present.
  (c) Drive the real load path with a **stubbed** historical feed and assert the resulting series
  spans **≥ 30** distinct sessions before the current one for each of the five intraday timeframes in
  **both** modes (**RED pre-fix**: `1 min` RTH yields one session — the ESC-038 repro). (d) The floor
  survives retention: after the wave, the cached and in-memory series still hold ≥ 30 mode-valid
  sessions. (e) Mode isolation: a bar set written under `ext_hours=True` is not read as
  `ext_hours=False` coverage and vice versa.

### Assumptions (D42)

Plan-level assumptions **not** already in `requirements.md`'s Assumptions Log (`A1`–`A73`).

- **AP-D42-1 (Phase 1 and Phase 2 overlap in exactly one file, so they are sequenced there).** The two
  workstreams share **one** file — `ui/chart_panel.py` (Phase 1: the width path; Phase 2:
  `ChartPanel.update_last_bar`'s `_bars` trim, `:1150`–`:1157`). Their two `ui/chart_panel.py` tasks
  therefore sit in **different waves** — Phase 2's trim runs **after** Phase 1's width edit — because
  `build_wave.py` forbids two `in_progress` tasks with overlapping `touches_files`. Every **other**
  file is single-phase, so the remaining Phase 1 / Phase 2 tasks **may** be co-scheduled. The phase
  split is kept because each phase's wave must be individually green. Phase 3 waits for both.
- **AP-D42-2 (`min_sessions` defaults to 0).** The floor is **opt-in per call**, so every existing
  planner suite keeps its exact semantics and the D16 no-fill/no-silent-hole behaviour is unchanged
  when the floor is not requested. `R64`'s "the D16 suite stays green" is met by **exact** semantics in
  the pure-planner suites plus **intent-preserving** corrections in the D16 **load-path** suites
  (enumerated with their cause above) — never by weakening an assertion.
- **AP-D42-3 (the floor is scoped to chart loads).** `AC-D16.8` speaks of the **displayed** series of
  a loaded chart, so the floor is requested by `MainWindow.load_chart` — the primary chart's load
  path (pop-outs **attach a view** to the shared session and issue **no history** of their own,
  `ui/popout_window.py:131`; the pop-out's persisted `ext_hours` reaches the cache only through the
  session it attaches to) — and **not** by the D25 headless alarm-monitor sessions
  (`services/alarm_monitor.py:287`), which never request history. This is a faithful reading, not a
  narrowing — but it is a decision, recorded for the Validator.
- **AP-D42-4 (legacy cache rows are tagged ETH).** Justified by the app's default
  (`ext_hours_btn.setChecked(True)`); no row is deleted; presence stays window-based, so a tag can
  never manufacture coverage; an RTH load after the migration simply performs the floor fetch
  `AC-D16.8` requires anyway.
- **AP-D42-5 (the unit of `F`/`pitch`/`body`).** The requirement says "all in the same pixel unit";
  the shipped clamp's unit is the ViewBox logical-pixel unit that `px_per_sec` yields (which scales
  with DPR at render). The cap keeps **that** unit and the existing `F` constant, so the requirement's
  outcomes hold (`body ≤ pitch` at the repro; `body ≥ F` in the non-dense regime). No requirements
  change is implied. Per `RC-D42-3` the WS1 evidence **states** this unit, applies `F` in it, and
  asserts no `F == 4.0` device-px equality at DPR 2.
- **AP-D42-6 (`TIMEFRAME_CONFIG` is not changed).** Its durations are the **per-request** IBKR caps;
  the depth comes from chaining (`AC-D16.8` itself calls the window strategy a Plan/Build matter).
  `MIN_INTRADAY_SESSIONS = 30` is the one new constant.
- **AP-D42-7 (test invocation + probe isolation).** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m
  pytest` (the `pytest` entry point has a stale shebang); the DPR-2 probe stays in its isolated
  `QT_SCALE_FACTOR=2` subprocess; every non-pytest probe exports `DB_PATH` to a temp file (ESC-043).
- **AP-D42-8 (D41 is not reopened).** No Phase-1/2 file is a D41-removed file, and no D42 path
  touches the retained order machinery or the D38/D39 substrate.
- **AP-D42-9 (the suite total moves).** The **five** enshrining suites, the D16 **load-path** suites
  and — `ESC-050` — the **six load-path-*driving* suites** (19 cases) are corrected, the planner
  suites (`tests/test_backfill_service.py`, `tests/test_d27_backfill_granularity.py`) and
  `tests/test_db_schema.py` are extended, and **four** suites are added, so the count changes; the
  requirement is **green** with every assertion either **exact** or corrected **intent-preserving** —
  not count parity (any docs figure quoting a total must be re-measured). The corrected set is
  **complete by rule** (the `ESC-050` invariant), not by the suites the design named.

### Flagged issues and Validator dispositions (D42)

Requirements Plan could not satisfy with the architecture **as written**, or decisions a Task Manager
could not have made without inventing architecture.

- **FI-D42-1 — `AC-D16.8`'s floor is unsatisfiable while the D28.4 caps stay at 5000 (decided, needs
  ratification; no Requirements escalation).** A `1 min` RTH session is 390 bars, so 30 sessions =
  **11,700 bars**; `1 min` ETH = **28,800**; `5 mins` ETH = **5,760** — all above
  `config/settings.py::SESSION_BAR_CAP = 5000` and `data/bar_cache.py::RETENTION_BARS = 5000`, which
  would **delete the floor after fetching it**. The requirement is satisfiable, but only by revising
  a D28.4-blessed bound: `S18` makes the caps **floor-aware** (the flat values stay the
  default/minimum) at a memory cost of **~8–16 MB** per loaded `1 min` ETH chart (33,120 `Bar`
  dataclasses without `__slots__`, plus the two plot arrays). This is an architecture decision the
  requirements do not make, so it is recorded rather than assumed. **Disposition: RATIFIED as `S18`**
  — the Validator independently re-derived the arithmetic and the prune/trim behaviour in round 1
  and re-confirmed them in cycle 2; **no Requirements escalation** (the requirement's *outcome* is
  achievable and unchanged).
- **FI-D42-2 — the D42 correction record's artifact list is incomplete (Plan addition; no
  escalation). CONFIRMED and EXTENDED by the Validator: five suites enshrine the old behaviour, not
  two.** The record names `tests/test_candle_spacing.py` (`:4`–`:10`, a source-string check that never
  renders) and `tests/test_volume_width.py` (`:103`–`:104`). **`tests/test_chart_dpi.py:245`–`:250`**
  (`assert body_dev >= 4.0` on the dense 960-bar DPR-2 dataset — **this one will FAIL post-fix**, since
  the capped body ≈ the pitch), **`tests/test_d28_2_sessions.py:166`** and
  **`tests/test_d28_4f_panel_bar_cap.py:53`** enshrine the same old rule. All five are **corrections**
  (the intent preserved), not weakenings; the D16 **load-path** suites (see the *Corrected — D16
  load-path* table) are the same kind of intent-preserving correction. **Disposition: ACCEPTED** — the
  correction record now names **all five** suites plus the load-path set.
- **FI-D42-3 — `AC-D16.9`'s "RTH bars are ETH coverage" vs the mode-aware cache key (reading
  recorded).** With a strictly mode-keyed cache, an ETH load cannot **see** bars stored under the RTH
  key, so a day covered only by an RTH-mode fetch is **re-fetched** under ETH rather than read as
  present. The reading: `AC-D16.9`'s measurable (c) is a statement about the **presence predicate** on
  a given bar set (satisfied: RTH bars lie inside the ETH window, so the ETH call reports the day
  present) and **not** a requirement that an RTH-keyed row satisfy an ETH load. The cost is one extra
  fetch per mode switch; there is **no** hole and **no** cross-contamination. **Disposition:
  RATIFIED as read** (round 1, re-confirmed cycle 2); if a later reader takes it otherwise, the
  alternative (a `'LEGACY'` mode visible to both) is the recorded fallback. **Citations:**
  `AC-D16.9`'s measurable (c) is phrased as a **presence predicate** on a given bar set
  (`requirements.md:1967`–`:1969`: "seed a trading day with **only RTH bars** and assert **both** the
  RTH call and the ETH call report it present (RTH bars lie inside `04:00–20:00 ET`)"), while
  `requirements.md:1957`–`:1958` separately requires the mode-aware key ("The bar cache/key is
  **mode-aware** (RTH vs ETH) … This applies **in both directions**") — the two are satisfied together
  by this reading, which is exactly why the strict mode-keyed cache (`S16`) is consistent with the
  measurable.
- **FI-D42-4 — the `F` unit wording (observation; no escalation).** `AC-D6.4` says "`4` device pixels
  at DPR `2`" while the shipped clamp's constant is 4 px in the ViewBox unit (8 device px at DPR 2).
  The requirement's operative clause is "measured in the **same** pixel unit", so keeping the shipped
  constant and capping in that same unit satisfies the criterion's outcomes. Recorded as `AP-D42-5`
  so the discrepancy is not read as a silent reinterpretation. **Disposition: RATIFIED** with
  `AP-D42-5` (round 1) — and, per **`RC-D42-3`**, the WS1 evidence now **states** the unit (ViewBox
  logical px = `px_per_sec`'s unit; 4 logical px = 8 device px at DPR 2), applies `F` in it, and
  asserts no `F == 4.0` device-px equality.

### Correction record — for Task Manager / Build / Code Reviewer (D42)

The two **superseded** criteria and the artifacts that must change (mirrors `### D42`'s correction
record, plus Plan's three additions):

1. **`AC-D6.4`'s *unconditional* "the body remains `>= 4` device pixels wide"** is **superseded** by
   the density-aware rule `body = min( max(0.65 × pitch, F), pitch )`; the wick clause (cosmetic
   1 device px) is **unchanged**. (`F = 4.0` is in the **ViewBox logical-px** unit `px_per_sec`
   yields — 8 device px at DPR 2 — and `AC-D6.4`'s operative clause is "measured in the **same** pixel
   unit"; the shipped constant and unit are kept, `FI-D42-4`/`AP-D42-5`.)
2. **`AC-D7.1`'s "the gap remains positive"** (and the D7 dense-view edge case) is **relaxed to
   `gap >= 0`** — `> 0` whenever `pitch > F`, `0` acceptable at `pitch <= F` (owner-confirmed
   **Q51**); the 35 %-gap intent in the non-dense regime is **unchanged**.
3. **The RTH-only default of the depth floor** is **superseded** — `AC-D16.8`/`AC-D16.9` cover both
   `ext_hours=False` and `ext_hours=True` (owner-confirmed **Q52**), one floor, two modes.
4. **Task Manager:** write the two work items against `AC-D6.4`/`AC-D7.1`/`AC-D9.2` (revised) and
   `AC-D16.8`/`AC-D16.9` (both modes); the phase/file map above is the `touches_files` partition —
   **note the one shared file, `ui/chart_panel.py`**: Phase 1 owns its width path, Phase 2 owns
   `ChartPanel.update_last_bar`'s floor-aware `_bars` trim (`:1150`–`:1157`), and those two tasks must
   sit in **different waves** (Phase 2's trim sequenced after Phase 1's width edit).
5. **Build:** apply the cap in `ui/candlestick_item.py::CandlestickItem._draw_candles` **and** the
   volume width path (`::ChartPanel._clamp_half_width` / `::ChartPanel._refresh_candles` /
   `::ChartPanel._refresh_live_bar`); make `find_missing_spans` (and the exported presence predicate)
   **mode-aware**; make the bar cache/key **mode-aware** (`data/bar_cache.py` / `data/db.py`, keyed
   `symbol+timeframe+ext_hours`); deliver the floor as chained backwards requests and make the
   floor-aware budget apply at **all three** `SESSION_BAR_CAP` sites —
   `ui/ticker_session.py::TickerSession.set_bars` (`:300`), `::TickerSession._append_bar` (`:313`)
   **and** `ui/chart_panel.py::ChartPanel.update_last_bar` (`:1150`–`:1157`, the third site,
   `RC-D42-1`) — plus `BarCache.prune`'s `keep`; **correct (do not merely weaken)** the five
   enshrining suites named in `S21`/`FI-D42-2`, **and** the D16 **load-path** suites enumerated in the
   *Corrected — D16 load-path* table (each intent-preserving, its cause named), **and — `ESC-050` —
   the six load-path-*driving* suites** enumerated in the *Corrected — load-path-*driving* suites*
   table (test-only: widen each fixed-size `req_historical_data` reqId stub to an unbounded
   `itertools.count` source; **no assertion weakened, skipped or xfailed** — the production
   multi-request behaviour is requirements-mandated, so do **not** reduce the request count), and add
   the four new ones.
6. **Code Reviewer:** on the **ESC-041** re-check, verify against the **revised** `AC-D6.4`/`AC-D7.1`
   (a contiguous zero-gap pixel run at pitch ≈ 3.83 px is the failure); on **ESC-037**, verify
   `AC-D16.9` **in both modes** (the RTH-missing / ETH-present split **and** the reverse); **ESC-038**
   and **ESC-042** are resolved on the requirements side by `AC-D16.8`/`AC-D16.9` and
   `AC-D6.4`/`AC-D7.1` and may be flipped from `open` after re-verification. **ESC-041/ESC-037 stay
   BUILD-owned** — D42 does not close them. **`ESC-050`** is the enumeration fix recorded here (no
   code); the code/test fix it points at is **`ESC-048`** (BUILD, blocking) — the six stub widenings.
7. **Every future increment (`ESC-050` — the enumeration rule, generalisable).** The impact analysis
   must enumerate the assertions an increment changes **by call site of the changed entry point, not by
   the suites the design names** — including the suites that merely **drive** the changed path — and must
   state the **invariant** that generates the enumeration, so the set is checkable by a rule before
   dispatch instead of discovered by a reconciliation task afterwards. D42's two under-counts (round 1's
   `FI-D42-2`: two suites named where five exist; `ESC-050`: the D16 suites named where 14 changed test
   functions **plus 19 load-path-driving cases in six suites** exist) are the recorded precedents.

### Incidentally affected (noted, not absorbed) (D42)

- **ESC-041** (candle **and** volume overlap on a 5-min Ext-Hours chart) and **ESC-037** (the
  mode-blind day-presence pass) are the BUILD escalations D42 unblocks; their fixes are Phase 1 and
  Phase 2 respectively, but closing the escalations is the Code Reviewer's action after
  re-verification.
- **ESC-043** (offscreen probes must set `DB_PATH`) is a *test-harness* rule D42's new suites must
  honour, not a D42 work item.
- **DOC-1** (any doc figure quoting a suite total) goes stale again because four suites are added;
  the owner/Analyst follow-up, not a Build task.
- Nothing in D42 touches ESC-032/033/034/036/044/045 or the D41 removals.

Handoff: canonical set complete — `docs/architecture.md` (§ *D42 increment*, incl. the `ESC-050`
amendment and the `Frozen Interfaces` checklist), `docs/plan.md` (this section), `docs/plan_review.md`
(`Status: APPROVED`, D42 cycle 3 of 3), and `docs/plan_notes.md` (not modified this cycle — no
requirements or planning gap). Phase order: **Phase 1 → Phase 2 →
Phase 3**, with the **one shared file** `ui/chart_panel.py` sequenced across Phase 1/Phase 2 (its two
tasks in different waves), then Code Reviewer verification (which also re-verifies and flips
ESC-041/ESC-037 and ESC-038/ESC-042 as their owners require, and flips `ESC-050` after re-verifying
the enumeration above).

Status: superseded by the D44 section below (D42's `READY_FOR_TASK_MANAGER` was consumed by the D42
build — 26/26 tasks, full offscreen suite green, review `REVIEW_COMPLETE`, committed; the live handoff
status line is the one at the end of this file).

---

## D44 — Batch 19: the collapsed Watchlist becomes a thin vertical bar that expands to the full panel — validated 2026-10-16, **approved for build**

> **Status of this section.** The canonical D44 plan. Validated by Plan Artifact Editor & Validator
> (`Status: APPROVED`, 2026-10-16) on a **legacy single-scope run** (no `Phase: P<n>`; the unsuffixed
> proposal pair; no phase gate), so the D44 increment merged into the cumulative canonical artifacts as
> § *D44 increment* in `docs/architecture.md` and this section here. **Approved for build, not yet
> as-built.** **D1–D43 are not reopened.**
>
> **Requirements of record:** `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised
> 2026-10-16 17:28) — the D44 status/audit block (`:118`–`:136`), the revised `## Non-Goals`
> (`:258`–`:267`), the D44 work item (`:353`–`:365`), **Journey 37** (`:976`–`:989`), **`### D44`**
> (`:3782`–`:3925`), **`AC-D44.1`–`AC-D44.8`** (`:3854`–`:3891`), the supersession/revision record
> (`:3892`–`:3905`), the edge cases (`:3906`–`:3913`), the correction record (`:3914`–`:3925`),
> **A75–A78** (`:4005`–`:4008`), **R66–R67** (`:4129`–`:4130`) and the Batch-19 summary
> (`:4239`–`:4246`); `design_gaps.md` **DG74**; `open_questions.md` **Q54** (answered 2026-10-16,
> owner confirmation requested, non-blocking). Companion architecture: `docs/architecture.md`
> § *D44 increment*. Module index: `docs/codebase-map.md`.
>
> **Baseline:** `main` @ **`0c4d478`**, full offscreen suite green. Suite invocation
> `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale shebang).
>
> **Supersessions this plan keeps consistent (already recorded by the Requirements Analyst — never
> silent):** `AC-D21.11.2`/`AC-D21.11.3` (the collapsed **appearance**) are **revised**; the
> **150px-minimum clause** of `AC-D13.1`/`AC-D17.2` becomes **expanded-state only**; `AC-D21.11.1`,
> `AC-D22.1` (**expanded**) and the D13/D17 **cap / persistence / drag / re-clamp** clauses are
> **unchanged**; the `## Non-Goals` restyling bullet is revised **only** for the D44 bar, in the app
> palette.
>
> **Escalation state at validation time.** No escalation is open against this increment's decisions
> (`ESC-050` is `addressed`). The only open entry in `docs/code_review/escalations.json` is
> **ESC-055** (`routed_to: TASK_MANAGER`, `severity: nice-to-have`) — the D42/`ESC-050` enumeration
> rule's *ownership remedy*. D44 **applies** the rule (`AP-D44-8`) but does **not** absorb the
> escalation, which is Task Manager's.

**The one workstream.** The collapse mechanism already exists (D21.11); D44 changes the collapsed
**appearance** and adds the missing **collapsed width**. Two halves that must land together for the
feature to be true:

1. **The width (the core fix — `AC-D44.5`, R66/DG74).** A **pure** collapsed-width rule in
   `ui/dock_layout.py` (`WATCHLIST_COLLAPSED_WIDTH = 30`; the 150px minimum becomes **expanded-state
   only**), consumed by **both** clamp branches of the single apply entry point
   `MainWindow._apply_dock_widths` (`ui/main_window.py:2459` — the right-dock-visible branch via
   `plan_dock_widths`, and the right-dock-hidden branch's direct clamp at `:2527`), plus the
   **D21.13-style minimum-width relaxation** (`panel` + `dock` → 30 while collapsed, back to 150 on
   expand) and the deferred re-apply, so a `resizeEvent` **or** a dock drag cannot snap the bar back to
   150px. `MainWindow._watchlist_width` is **never overwritten while collapsed** — it *is* the
   "previous width" `AC-D44.2` restores.
2. **The visual + the expand affordance (`AC-D44.1`/`.2`/`.3`/`.4`/`.6`, A77).** A small custom widget
   with a `paintEvent` drawing the rotated `WATCHLIST` label (Qt cannot rotate a `QPushButton`'s text)
   as the panel's **full-height** collapsed body, in the app palette (`#141822` / `#232938` /
   `#cbd5e1`), with hover/pressed feedback through `ui/visual_conventions.py::set_button_active`; a
   30×28 handle in the dock's **title-bar slot** while collapsed (so the dock stays movable — DG37);
   the header strip, the D22.1 `+` and the column-header row hidden while collapsed and restored on
   expand; clicking the bar expands to the tracked previous width, re-clamped. **No persistence**
   (A76) — no new `QSettings` key; the app starts expanded.

**Out of scope — do NOT plan these.** Every earlier defect/feature (D1–D43) and their delivered
artifacts. No D44 path reaches the chart renderer (**pyqtgraph is a locked decision** — `docs/memory.md`,
2026-10-16), the load path, the planner, the bar cache, the alarms, the drawings/studies, the orders
machinery, the right dock, or the D42/D43 data paths. **No new dependency and no stack change.**
**ESC-055** stays TASK_MANAGER-owned.

### Coverage (D44)

| Criterion / journey | Plan treatment | Verdict |
|---|---|---|
| `AC-D44.1` (thin vertical bar of `WATCHLIST_COLLAPSED_WIDTH` in `LeftDockWidgetArea`, rotated label, app palette, not white) | Phase 1 — the pure width rule (`ui/dock_layout.py`) + `CollapsedWatchlistBar` + the collapsed panel styling; the width measurable in `tests/test_dock_widths_collapsed_d44.py`, the widget/palette in `tests/test_watchlist_collapsed_bar_d44.py` | Covered |
| `AC-D44.2` (click the bar → expand to the previous width, re-clamped) | Phase 1 — `expand_requested` + `collapsed_changed` → `_on_watchlist_collapsed_changed`; `_watchlist_width` never overwritten while collapsed; the guard asserts the **tracked** width exactly (`win._watchlist_width == clamp(W)`, by construction) incl. the min-150 and at-cap edge cases, **plus** a **tolerant** rendered-width check (`>= WATCHLIST_MIN_WIDTH`, `<= watchlist_max_width(...)`, `> WATCHLIST_COLLAPSED_WIDTH`) — restated 2026-10-16 per ESC-057 | Covered |
| `AC-D44.3` (collapse from the retained header button — the existing D21.11 path) | Phase 1 — `_on_header_toggled` preserved and extended with `_apply_collapsed_visual()` + the signal; API frozen | Covered |
| `AC-D44.4` (header strip / `+` (D22.1) / column-header row hidden while collapsed, visible on expand) | Phase 1 — explicit `hide()`/`show()` of `header_bar` + `table`; the three corrected sites assert the collapsed/expanded states | Covered |
| `AC-D44.5` (**the core fix** — the collapsed width survives a `resizeEvent` **or** a dock drag) | Phase 1 — the collapsed-aware apply path in **both** branches + the min-width pin + the deferred re-apply; the guard drives `win.resize(...)` **and** `_on_dock_drag_event()` | Covered |
| `AC-D44.6` (palette + hover/pressed via `set_button_active`) | Phase 1 — `S25`/`S26`; the bar suite asserts the palette from the stylesheet + the `active` property and that the `[active="true"]` style differs; the rendered palette check is the Code Reviewer's | Covered |
| `AC-D44.7` (collapse state not persisted; no `QSettings` key) | Phase 1 — `S27`; the guard asserts the app starts expanded and no collapse key exists | Covered |
| `AC-D44.8` (regression guard RED pre-fix; the expanded suites green or corrected in lockstep) | Phase 1 (the guard + the corrections) + Phase 2 (the RED→GREEN evidence + the reconciliation) | Covered |
| **Journey 37** (steps 1–5 + the edge cases) | Phase 1 (steps 1–4, all edge cases exercised by the two new suites) + Phase 2 (the restart leg + the re-check) | Covered |
| `AC-D21.11.2`/`.3` (REVISED), the 150px-minimum clause of `AC-D13.1`/`AC-D17.2` (REVISED to expanded-only), the `## Non-Goals` revision | Phase 1 — the corrections ride with the production change that invalidates them | Covered |
| `AC-D21.11.1`, `AC-D22.1` (expanded), `AC-D13.2`/`.3`, `AC-D17.1`/`.3`–`.6`, `AC-D18.*`, D21.13, D14, D21.5, D39 (non-regression contract) | Phase 1 (the expanded-path suites verified unchanged) + Phase 2 (the full-suite re-check) | Covered |
| `A75`–`A78`, `R66`, `R67`, `DG74` | The three flagged-issue rulings (below), `AP-D44-1`–`AP-D44-9`, the risk table `AR-D44-1`–`AR-D44-10` | Covered |

### Phases (D44)

Two phases. Phase 1 is the whole feature (production change + the suites it invalidates + the new
guards) — a single milestone, because the width rule and the bar are two halves of one user-visible
behaviour and because each corrected suite must ride **with** the production change that invalidates it
(the `ESC-055` lesson). Phase 2 is the batch-level reconciliation the repo always runs (the
D19/D20/D42 precedent) and adds **no production edit**.

#### Phase 1 — The collapsed watchlist thin bar: the width model, the apply path, the bar, the expand path, and the corrected + added suites

- **Goal:** collapsing the watchlist renders a **30px vertical bar** with the rotated `WATCHLIST` label
  in the app palette, the header strip / `+` (D22.1) / column-header row hidden; the collapsed width is
  **honoured by the layout** — a window `resizeEvent` or a dock drag does **not** snap it back to the
  150px minimum; clicking the bar **expands** the panel to the width it held immediately before
  collapsing (re-clamped to the current expanded cap/min); the dock stays **movable/floatable** while
  collapsed; the collapse state is **not** persisted; and the **expanded** D13/D17/D18/D21.13 criteria
  and their suites are unaffected.
- **Covers:** `AC-D44.1`–`AC-D44.8` (incl. **`AC-D44.5`**, the core fix); Journey 37 steps 1–5 + the
  edge cases; the revised `AC-D21.11.2`/`.3` and the revised 150px-minimum clause of
  `AC-D13.1`/`AC-D17.2`; `A75`–`A78`; `R66`, `R67`; `DG74`. Non-regression contract: `AC-D21.11.1`,
  `AC-D22.1` (expanded), `AC-D13.2`/`.3`, `AC-D17.1`/`.3`–`.6`, `AC-D18.*`, D21.13, D14, D21.5, D39.
- **Requirements/journeys:** Journey 37 steps 1–5 and its edge cases (collapse from the 150px minimum →
  expand restores 150; collapse from the cap → expand restores the cap; resize/drag while collapsed
  does not expand it; a floating watchlist is still clickable to expand; disconnected/empty watchlist
  still collapses/expands; first launch starts expanded; the `CHART_MIN_WIDTH` invariant holds in both
  states; a very narrow window where 30px still fits).
- **Dependencies:** none on any other phase. **Internally ordered** (see the per-file map): the pure
  rule (`ui/dock_layout.py`) **before** its consumers; the bar widget **before** the `MainWindow`
  wiring that swaps the title bar; each corrected suite in the **same phase** as the production change
  that invalidates it. The two file-groups that touch `ui/main_window.py`, and the two that touch
  `tests/test_watchlist_columns_d21.py`, must sit in **different waves** (`build_wave.py` forbids two
  `in_progress` tasks with overlapping `touches_files`).
- **Deliverable:** `ui/dock_layout.py` (the collapsed constant + the pure rule + the `left_collapsed`
  mode), `ui/watchlist_panel.py` (the bar widget + the handle + the visual sync + the transition
  signal), `ui/main_window.py` (the collapsed-aware apply path + the minimum-width pin + the wiring),
  the **two new suites**, the **two extended** suites, and the **corrected** sites — full offscreen
  suite green, with the new width guard **RED at `0c4d478`** for the right reason.

#### Phase 2 — Reconciliation, non-regression and the correction record

- **Goal:** the whole offscreen suite is green with **every** existing assertion either keeping its
  **exact** expectation or **corrected intent-preserving** to the revised criteria — **none weakened,
  none deleted** — and every such correction recorded **with its cause**; the enumeration of the
  affected suites is **complete by rule** (by call site of the changed entry points, not by the suites
  the design names — the `ESC-050` rule and `ESC-055`'s ownership remedy), so the *Verified unchanged*
  set is evidence rather than assumption; the RED-at-`0c4d478` → GREEN evidence is recorded for the
  guard; and the D44 increment is ready to merge into the canonical docs.
- **Covers:** `AC-D44.8` (the guard's RED→GREEN evidence and the expanded-state suites); `R67`; the D44
  correction record; the non-regression re-check of `AC-D13.2`/`.3`, `AC-D17.1`/`.3`–`.6`, `AC-D18.*`,
  `AC-D21.11.1`, `AC-D22.1` (expanded), D14/D21.5/D39.
- **Dependencies:** Phase 1 complete.
- **Deliverable:** the full-suite green run + the corrected/added/verified-unchanged enumeration with
  causes + the guard's RED→GREEN evidence + the correction-record entries for Task Manager / Build /
  Code Reviewer. **No production edit.**

### Per-file `touches_files` map and sequencing constraints (D44 Phase 1)

**Sequencing constraint (binding).** Build runs a wave frontier: two tasks with overlapping
`touches_files` must never be `in_progress` in the same wave. Two files are shared by more than one
file-group: **`ui/main_window.py`** (the apply path **and** the transition wiring) and
**`tests/test_watchlist_columns_d21.py`** (the collapsed-width leg **and** the collapsed-appearance
legs). Those pairs **must sit in different waves**, and the wiring must follow the apply path (it calls
it). `ui/watchlist_panel.py` is a **single** file-group (the widget and the visual sync belong to one
worker: the widget's geometry and the panel's layout are the same change).

| File | Change | Tests in the same task / touched by the change |
|---|---|---|
| `ui/dock_layout.py` | `+ WATCHLIST_COLLAPSED_WIDTH = 30`; `+ plan_watchlist_width(chart_area_w, requested_left, collapsed=False)` (the **single** collapsed/expanded width rule); `plan_dock_widths(..., left_collapsed=False)` — a collapsed left is **fixed** at the collapsed width, its own floor becomes 30, the cross-clamp loop may shrink **only** the right, the `chart_area_w - left - right >= CHART_MIN_WIDTH` budget is unchanged, and the infeasible branch returns `(left_min, RIGHT_DOCK_MIN_WIDTH)` so today's expanded `(150, 200)` is preserved exactly; `clamp_watchlist_width(width, chart_area_w)` delegates to the new helper with `collapsed=False` (`S23`) | `tests/test_dock_layout.py` (**extend** — the collapsed pure cases + the constants/agreement test, incl. the new constant's cross-module agreement), `tests/test_watchlist.py` (**extend** — the collapsed delegate case); `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_right_dock_d21.py`, `tests/test_d10_d13_integration.py`, `tests/test_dock_layout.py::test_T52_T04`, `tests/test_toolbar_scroll_d19.py` (**verified unchanged** — 3-argument/expanded call sites) |
| `ui/main_window.py` **(file-group A — the collapsed-aware apply path)** | `_apply_dock_widths`: read the watchlist collapse state into a **new local (`watchlist_collapsed`)** — do **not** reuse the name `collapsed`, which at `:2490` already means the *right region* is collapsed; the right-dock-visible branch forwards `left_collapsed=watchlist_collapsed` to `_plan_dock_widths`; the right-dock-hidden branch computes `desired = plan_watchlist_width(chart_area, base_left, collapsed=watchlist_collapsed)`; **`self._watchlist_width` is not assigned while collapsed**; `_plan_dock_widths` forwards the flag; `_dock_widths_consistent` becomes collapsed-aware (`S24`) | `tests/test_watchlist_columns_d21.py::test_D21_10_T03` (**correct** — the **collapsed-width** leg only: the `>= WATCHLIST_MIN_WIDTH` assertion after `_apply_dock_widths(10**6)` becomes the collapsed-width assertion, and the `>= WATCHLIST_MIN_WIDTH` leg moves to the **expanded** state); `tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_right_dock_d21.py`, `tests/test_d10_d13_integration.py`, `tests/test_dock_d18_region.py` (**verified unchanged** — all drive it with the watchlist expanded) |
| `ui/watchlist_panel.py` **(file-group B)** | `CollapsedWatchlistBar(QWidget)` (fixed width, `WA_StyledBackground`, the object-name stylesheet in the app palette, a `paintEvent` drawing `WATCHLIST` rotated 90° counter-clockwise and centred, `expand_requested`, `set_button_active` hover/pressed); `WatchlistPanel.collapsed_bar` (the **full-height** collapsed body) + `::collapsed_handle` (the 30×28 collapsed title-bar handle); `::_apply_collapsed_visual()` (explicit `hide()`/`show()` of `header_bar` — which carries the `+` and the search box — and `table`, plus the bar and the collapsed panel styling); `collapsed_changed = pyqtSignal(bool)`; `WATCHLIST_COLLAPSED_WIDTH` **aliased** from `dock_layout`; the collapse API preserved (`S25`, `S26`) | `tests/test_watchlist_columns_d21.py::test_D21_10_T02` (**correct** — the collapsed **appearance**) and `::test_D21_10_T03` (**correct** — the appearance + the title-bar/drag legs; a **different wave** from file-group A's edit of the same file), `tests/test_watchlist_nonregression_d22.py` (**correct** — the D21.11 block + the module docstring), `tests/test_watchlist_add_remove_d22.py::test_D22_04_T01` (**correct** — `hb.isVisible()` while collapsed); `tests/test_watchlist_columns_d21.py::test_D21_10_T01` (**verified unchanged** — expanded only); **`tests/test_watchlist_collapsed_bar_d44.py` is owned here** |
| `ui/main_window.py` **(file-group C — the transition wiring)** | connect `panel.collapsed_changed` → `_on_watchlist_collapsed_changed`: swap the dock's title-bar widget (`collapsed_handle` while collapsed, `header_bar` on expand — un-hiding `header_bar` as it is restored, so the title bar is never a hidden widget), relax/restore the minimum widths (`panel` + `dock` → 30 / 150), then `_resize_docks_guarded` + `QTimer.singleShot(0, self._apply_dock_widths)` — the `_sync_right_dock_collapse` sequence (`S24`, `S25`) | **`tests/test_dock_widths_collapsed_d44.py` is owned here** (it asserts the end-to-end transition: collapse → 30px, survive a resize/drag, expand → the tracked `_watchlist_width == clamp(W)` with the rendered width checked tolerantly, the min-width flip, no key) — a **different wave** from file-group A (the same production file) |
| `tests/test_dock_widths_collapsed_d44.py` **(new — file-group C)** | `AC-D44.5`/`AC-D44.2`/`AC-D44.7` + `AC-D44.1`'s width measurable: collapse at a known `W` → `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`; still the collapsed width after a window `resizeEvent` **and** after the drag-event path (`_on_dock_drag_event`); expand → the **tracked** `win._watchlist_width == clamp(W)` exactly (incl. the collapse-from-150 and collapse-from-cap edge cases) with a **tolerant** rendered-width check (`>= WATCHLIST_MIN_WIDTH`, `<= watchlist_max_width(...)`, `> WATCHLIST_COLLAPSED_WIDTH`); the dock's min width is 30 while collapsed and 150 after; **no** collapse key in `QSettings`; the `CHART_MIN_WIDTH` invariant in both states. **Must be RED at `0c4d478` for the right reason** | — |
| `tests/test_watchlist_collapsed_bar_d44.py` **(new — file-group B)** | `AC-D44.1`/`.3`/`.4`/`.6`: the collapsed bar exists with the rotated-label widget and the app palette; the header strip / `+` / column-header row are **not** visible while collapsed and are visible on expand; `set_button_active` drives the hover/pressed feedback (the `active` property + a differing stylesheet); `is_collapsed()`/`set_collapsed()`/`toggle_collapsed()` semantics; clicking the bar expands | — |

**Shared-file waves (Phase 1).** The file partition has four single-file groups — **A** the
collapsed-aware apply path (`ui/main_window.py` + `tests/test_watchlist_columns_d21.py`'s **width leg**);
**B** the bar widget + the collapsed visual (`ui/watchlist_panel.py` + `tests/test_watchlist_columns_d21.py`'s
**appearance legs** + the two D22 suites + `tests/test_watchlist_collapsed_bar_d44.py`); **C** the
transition wiring (`ui/main_window.py` + `tests/test_dock_widths_collapsed_d44.py`); **D** the pure
width model (`ui/dock_layout.py` + `tests/test_dock_layout.py` + `tests/test_watchlist.py`). (These
groups are the `touches_files` partition Task Manager decomposes into tasks — not tasks themselves.)
**Ordering:** **D before A and C** (the pure rule precedes its consumers); **A and B in different
waves** (both edit `tests/test_watchlist_columns_d21.py`); **A and C in different waves** (both edit
`ui/main_window.py`); **C after A and B** (it wires the transition and its guard asserts the
end-to-end outcome). B may co-schedule with A and D (disjoint files). Every other file is
single-group.

**Phase 2 adds no production edit** — reconciliation + docs only.

### Tests: corrected vs added, verified unchanged, and the RED→GREEN evidence (D44)

**Corrected (never weakened, never deleted — R67 and the D44 correction record).** Every correction
below moves an assertion to the **state in which it is still true**; none is deleted, skipped or
relaxed to "no exception raised".

| Suite / case | Assertion today | Cause of the correction | Intent preserved |
|---|---|---|---|
| `tests/test_watchlist_columns_d21.py::test_D21_10_T02` (`:386`–`:412`) | while collapsed: `panel.header_bar.isVisible()` (`:398`), `button.isVisible()` (`:399`), `button.is_struck()` (`:400`), `not button.isChecked()` (`:401`) | **The revised collapsed appearance** — `AC-D21.11.2`/`.3` are superseded for the collapsed state by D44 (`S26`): the strip is hidden while collapsed and the thin bar is shown | "Collapsing is reversible and the retained affordance is visible in the state where it is shown; the toggle's checked/struck state tracks the body": while collapsed assert the **bar** is visible + the strip/`+`/column-header row are **not**; on expand assert the strip + button return **checked and unstruck** |
| `::test_D21_10_T03` (`:417`–`:471`) — **the width leg** (Phase-1 file-group A) | `assert win.watchlist_dock.width() >= WATCHLIST_MIN_WIDTH` (`:465`) after `win._apply_dock_widths(10 ** 6)` (`:458`) **while collapsed** | **The collapsed width** (`S23`/`S24`): while collapsed the width is 30, not ≥150 — the 150px minimum is expanded-state only | "The width model holds in the state under test": while collapsed assert the **collapsed** width; the `>= WATCHLIST_MIN_WIDTH` leg **moves to the expanded state** (expand, then clamp, then assert) |
| `::test_D21_10_T03` — **the appearance + drag legs** (Phase-1 file-group B) | `button.isVisible()` (`:431`), `panel.header_bar.isVisible()` (`:433`), `dock.titleBarWidget() is panel.header_bar` (`:440`), the double-click-floats-the-dock on `panel.header_bar` (`:444`–`:452`) | **The revised collapsed appearance** + **the title-bar swap** (`S25`): while collapsed the title-bar widget is `collapsed_handle` | "The dock stays movable/floatable while collapsed (DG37) and the header strip is its title bar **when shown**": re-point the drag/float assertion at `collapsed_handle` and assert `dock.titleBarWidget() is panel.header_bar` **on expand** |
| `tests/test_watchlist_nonregression_d22.py` (`:104`–`:124` + the module docstring `:10`) | `panel.header_bar.isVisible()` (`:114`), `button.isVisible()` (`:115`), `button.is_struck()` (`:116`), `not button.isChecked()` (`:117`) while collapsed | **The revised collapsed appearance** (`S26`) — the same cause as `test_D21_10_T02` | "The D21.11 toggle still collapses/restores and the checked state tracks the body": the visibility assertions move to the **bar**; the expand-side assertions (`:121`–`:124`) are unchanged. The docstring's "the collapsed button stays visible + struck (VIS-D21.1)" is re-worded to the D44 collapsed form |
| `tests/test_watchlist_add_remove_d22.py::test_D22_04_T01` (`:79`) | `assert hb.isVisible()` while collapsed | **A77** (`S26`): the header strip is hidden while collapsed and returns on expand | "The `+` and the toggle remain in the strip's layout and are reachable": `:63`–`:71` (parent/layout/placement) and the post-expand legs (`:80`–`:83`) are unchanged; the collapsed leg asserts the strip (and therefore the `+`) is hidden |

**Extended (additions to existing suites).**

| Suite | What is added |
|---|---|
| `tests/test_dock_layout.py` | The collapsed pure cases (`plan_watchlist_width(..., collapsed=True) == 30`; `plan_dock_widths(..., left_collapsed=True)` fixes the left at 30, keeps `chart_area_w - left - right >= CHART_MIN_WIDTH` where feasible, keeps the right within its own cap/min, returns `(30, RIGHT_DOCK_MIN_WIDTH)` on an infeasible window, and never raises / stays int-stable over the T52 grid with `left_collapsed=True`); the constants test gains `WATCHLIST_COLLAPSED_WIDTH == 30`; the cross-module agreement test gains the new constant (the `CHART_MIN_WIDTH` invariant's sibling). The **expanded** cases stay **exactly** as they are |
| `tests/test_watchlist.py` | The collapsed delegate case (`clamp_watchlist_width` remains the **expanded** rule; the panel aliases `WATCHLIST_COLLAPSED_WIDTH` from `dock_layout`) |

**Added (new suites).** `tests/test_dock_widths_collapsed_d44.py` (`AC-D44.5`'s pinning guard,
`AC-D44.2`'s previous-width restore, `AC-D44.7`'s no-key assertion, `AC-D44.1`'s width measurable) and
`tests/test_watchlist_collapsed_bar_d44.py` (`AC-D44.1`/`.3`/`.4`/`.6`). Both use the repo's offscreen
harness conventions: `IBApiClient.connect` monkeypatched to a no-op, a throwaway SQLite DB (with
`DB_PATH` exported for any non-pytest probe — ESC-043), and a **per-test `QSettings` ini** (the D22
harness pattern) so no width/collapse state leaks between tests.

**Verified unchanged — enumerated by call site of the changed entry points (the `ESC-050` rule;
`ESC-055`'s ownership remedy).** The changed production entry points are
`ui/dock_layout.py::plan_dock_widths` / `::clamp_watchlist_width`,
`ui/main_window.py::MainWindow._apply_dock_widths` / `::_plan_dock_widths` / `::_dock_widths_consistent`,
and `ui/watchlist_panel.py::WatchlistPanel._on_header_toggled` / `::set_collapsed` / `::is_collapsed`.
Every test file that reaches any of them was found by grep and classified:

| Suite | How it reaches the change | Why it is unchanged |
|---|---|---|
| `tests/test_dock_layout.py` (21 tests) | `plan_dock_widths` (3 positional args), the constants | The new parameter defaults to the expanded rule; the expanded branch (incl. the infeasible `(150, 200)` result) is preserved bit-for-bit; the constants' **values** are unchanged (`WATCHLIST_COLLAPSED_WIDTH` is purely additive) |
| `tests/test_watchlist.py` | `watchlist_max_width`, `clamp_watchlist_width` | The delegation preserves the expanded formula exactly |
| `tests/test_dock_widths_d17.py` | `_apply_dock_widths`, the drag hook, `resizeEvent`, the persistence re-clamp | Drives it with the watchlist **expanded**; the 150px minimum, the drag enforcement and the persistence legs are the **expanded** state |
| `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py` | `_plan_dock_widths` / `plan_dock_widths`, `_apply_dock_widths` | Expanded; the B3 cross-clamp arithmetic is unchanged for a non-collapsed left |
| `tests/test_right_dock_d21.py` | `plan_dock_widths`, `_apply_dock_widths`, `watchlist_dock.width() >= WATCHLIST_MIN_WIDTH` (`:247`) | Expanded; the right dock's own model is untouched |
| `tests/test_dock_d18_region.py` | the **right** region's collapse (`portfolio_panel.is_collapsed`) | The right dock, not the watchlist |
| `tests/test_d10_d13_integration.py` | `_apply_dock_widths`, `clamp_watchlist_width`, `watchlist_max_width`, `WATCHLIST_MIN_WIDTH` | Expanded; the persistence clamp is expanded-only by definition |
| `tests/test_toolbar_scroll_d19.py` | the `CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH` sum | A constants sum used for D19 harness sizing; **no constant's value changes** |
| `tests/test_watchlist_columns_d21.py::test_D21_10_T01` | the panel's title-bar/label assertions | Boots **expanded** — exactly the state those assertions describe |
| `tests/test_d41_portfolio_dock.py`, `tests/test_d41_removal.py` | `dock_layout` constants, the right dock (`titleBarWidget` is the Portfolio `summary_label`) | Untouched surfaces |
| `tests/test_d24_popouts.py`, `tests/test_phase3_fixpass.py`, `tests/test_d24_alarm_full_chain.py`, `tests/test_d24_smoke_gate.py`, `tests/test_d24_9_popout_persistence.py`, `tests/test_d28_tick_burst_baseline.py` | boot a `MainWindow` (so `resizeEvent` → `_apply_dock_widths`, expanded) and drive the **load path** | D44 does not touch the load path, so the `ESC-050` fixed-size-stub defect class is **not** re-triggered |
| `tests/test_watchlist_d14_midrag.py`, `tests/test_d39_*`, `tests/test_d22*` (other cases) | the panel's data/search APIs | No D44 path changes them |

**The completeness of the set rests on a rule, not on inspection (normalized this cycle).** The
changed behaviour is **collapsed-gated**: the collapsed rule is applied only when
`watchlist_panel.is_collapsed()` is true, and the new parameters default to today's expanded
behaviour. Every other suite in the tree — including the ~45 further modules that boot a `MainWindow`
and therefore *drive* `_apply_dock_widths` through `resizeEvent` (`tests/test_d27_*`, `test_d28_*`,
`test_d41_*`, `test_d42_*`, `test_history_backfill*`, `test_kill_switch.py`, `test_toolbar_d20`/`d21`,
`test_alarm_d21.py`, `test_crosshair_axis_lane.py`, …) — runs with the watchlist **expanded**, so no
assertion in it can be invalidated by D44. The table above enumerates the direct call sites; the gate
plus the full-suite run in Phase 1/Phase 2 is the backstop, so the claim does not rest on an
enumeration being exhaustive by inspection (the D42/`ESC-050` lesson).

**RED→GREEN evidence Phase 1 must produce (runnable offscreen, no live TWS).**

- **The guard (`tests/test_dock_widths_collapsed_d44.py`) is RED at `0c4d478` for the right reason.**
  The guard drives the **existing** `set_collapsed(True)` API and asserts the **observable outcome**,
  referencing the new constant defensively (so an `ImportError` can never be mistaken for a behavioural
  RED). Pre-fix the collapsed dock stays at its expanded width and is ≥150 after the clamp (the
  Validator measured 256px collapsed with a 1138px chart area, and `resizeDocks([dock], [30])` → 150),
  so the assertions fail on the **width** — the repo's own credibility rule (`docs/memory.md`
  2026-10-05: "a regression guard is only credible if it fails on the pre-fix tree and passes
  post-fix").
- **GREEN after Phase 1:** collapse at a known `W` → `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`;
  after `win.resize(...)` + `qapp.processEvents()` → still the collapsed width; after
  `win._on_dock_drag_event()` + `qapp.processEvents()` → still the collapsed width; expand →
  the **tracked** `win._watchlist_width == clamp(W)` exactly (the rendered width asserted
  **tolerantly**: `> WATCHLIST_COLLAPSED_WIDTH`, `>= WATCHLIST_MIN_WIDTH`, `<= watchlist_max_width(...)`);
  collapse-from-150 → expand restores 150; collapse-from-cap → expand
  restores the cap; `QSettings` holds **no** collapse key; `chart_area_w >= CHART_MIN_WIDTH` in both
  states; the dock is still `DockWidgetMovable | DockWidgetFloatable` while collapsed.
- **The bar suite:** the bar and its rotated-label widget exist and are visible while collapsed; the
  strip, the `+` and the column-header row are not; the bar's stylesheet carries the app palette;
  hovering/pressing flips the `active` property (via `set_button_active`) and the `[active="true"]`
  style differs from the idle style; clicking the bar expands.
- **Commands:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_dock_widths_collapsed_d44.py
  tests/test_watchlist_collapsed_bar_d44.py -v` for the focused run, then the **full** offscreen suite
  (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`) — the whole-suite gate is what catches an
  assertion invalidated in a file outside a task's `touches_files` (`ESC-055`'s own lesson).

**The invariant (restated so the enumeration is checkable by rule, not by inspection).**

> **Enumerate by call site of the changed entry point — not by the suites the design names.** For every
> production symbol this increment changes (`plan_dock_widths`, `plan_watchlist_width`,
> `clamp_watchlist_width`, `MainWindow._apply_dock_widths` / `::_plan_dock_widths` /
> `::_dock_widths_consistent`, `WatchlistPanel._on_header_toggled` / `::set_collapsed` /
> `::is_collapsed`), find **every** test that reaches it — **including tests that only *drive* it**
> (boot a `MainWindow`, trigger a `resizeEvent`, drag a dock, click the header button) — and classify
> each as **corrected with its cause** or **verified unchanged**. Every corrected suite rides in the
> **same phase** as the production change that invalidates it, and any test file whose assertions a
> change can invalidate belongs to that change's `touches_files` (or to a sibling task's) — the
> `ESC-055` ownership remedy.

### Assumptions (D44)

Plan-level assumptions **not** already in `requirements.md`'s Assumptions Log (`A1`–`A78`).

- **AP-D44-1 (the collapsed width is enforced by relaxing the minimum + a collapsed-aware clamp — not by
  `setMaximumWidth`/`setFixedWidth`).** A left dock's reachable width is decided by its **widget
  minimums**, not by `resizeDocks` alone: an offscreen probe (2026-10-16, re-run independently by the
  Validator) held the dock at 128px when asked for 30 with the header strip in the title-bar slot, and
  yielded **exactly 30** once every visible widget's minimum was 30. The collapsed state therefore
  relaxes the panel's **and** the dock's minimum to `WATCHLIST_COLLAPSED_WIDTH` and restores
  `WATCHLIST_MIN_WIDTH` on expand — the D21.13 pattern.
- **AP-D44-2 (`_watchlist_width` keeps meaning "the expanded/requested width").** It is never assigned
  while collapsed, so it *is* the "width held immediately before collapsing" that `AC-D44.2` restores,
  and `closeEvent`'s `save_watchlist_width(self._settings, self._watchlist_width, …)` is unchanged.
  **Consequence (recorded, since A76 is silent on it — `FI-D44-3`, ratified):** a session that ends
  **collapsed** still persists the user's **expanded** width, so the next launch starts expanded at
  that width — the only choice consistent with "the app starts expanded".
- **AP-D44-3 (`AC-D44.5`'s measurable is scoped to the docked watchlist).** Journey 37's own
  precondition is "the Watchlist dock is visible and expanded on the left", and Qt does not lay a
  **floating** dock out in the dock area, so `resizeDocks`/the clamp govern the docked state. While
  floating, the collapse still swaps the visual and the bar remains clickable to expand (D44's
  edge-case wording: "the bar must still be clickable to expand"); the 30px pin is best-effort there.
  This is a faithful reading of the criterion's scope, recorded rather than assumed silently.
- **AP-D44-4 (the ±1px tolerance convention applies to inner measurements; the dock equality is
  asserted exactly — `FI-D44-1`, ratified).** `_apply_dock_widths` re-issues `resizeDocks` only when
  the delta exceeds 1px, and the D17 suite records that "a residual of at most 1px is expected and
  asserted with `+1`" (`tests/test_dock_widths_d17.py:17`–`:21`). The probe shows
  `resizeDocks([dock], [30])` yields exactly 30 offscreen, so the guard asserts the **dock** equality
  directly and keeps `+1` for derived/inner values.
- **AP-D44-5 (`WATCHLIST_COLLAPSED_WIDTH` lives in `ui/dock_layout.py` and is aliased in
  `ui/watchlist_panel.py`).** The D44 correction record names `ui/dock_layout.py`; the alias follows the
  existing pattern for `WATCHLIST_MIN_WIDTH`/`CHART_MIN_WIDTH`/`DEFAULT_WATCHLIST_WIDTH` (`:93`–`:95`),
  and the cross-module agreement test is extended to cover it — so the duplicated-constant invariant
  stays honest.
- **AP-D44-6 (no new dependency, no new Qt module, no rendering-stack change).** The only new Qt touch
  is a `QWidget.paintEvent` + `QPainter.rotate`; `QPainter` and a custom `paintEvent` are already in
  the repo (`ui/visual_conventions.py:190`, `ui/candlestick_item.py:135`) and `rotate` is a standard
  painter transform on the already-imported `QtGui` module. The pyqtgraph chart stack is a **locked**
  decision (`docs/memory.md`, 2026-10-16) and D44 does not touch it.
- **AP-D44-7 (test invocation and isolation).** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`
  (the `pytest` entry point has a stale shebang); any **non-pytest** probe that can reach a DB-writing
  path exports `DB_PATH` to a temp file (ESC-043); the new suites use a **per-test `QSettings` ini**
  (the D22 harness pattern) so the persisted width and the collapse state cannot leak between tests.
- **AP-D44-8 (the enumeration rule is applied, and each corrected suite rides with its cause).** The
  changed entry points are enumerated by call site (the *Verified unchanged* table), every correction
  names its cause, and no correction is left to the reconciliation phase alone — this is the `ESC-050`
  rule plus `ESC-055`'s ownership remedy, which stays TASK_MANAGER-owned and is **not** absorbed here.
- **AP-D44-9 (the suite total moves).** Two suites are added, two extended and three corrected (four
  sites + one docstring), so any doc figure quoting a suite total must be **re-measured** (the `DOC-1`
  follow-up) — the requirement is *green with every assertion exact or corrected intent-preserving*,
  not count parity.

### Flagged issues and Validator rulings (D44)

The plan surfaced three issues; the Validator **ruled on each** this cycle. All three are recorded in
`docs/plan_notes.md` as `FI-D44-1`–`FI-D44-3` with `Status: addressed` and `Escalation: none` — **no
`ESCALATED_TO_REQUIREMENTS`**, because no requirement is redefined, reinterpreted or left unsatisfied.

- **`FI-D44-1` — the exact-equality measurables vs the repo's ±1px tolerance convention → RATIFIED as a
  measurement convention (no Requirements change).** `AC-D44.1` and `AC-D44.5` both phrase the outcome
  as exact equality (`watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`), while the repo's
  established convention tolerates a 1px residual because `_apply_dock_widths` only re-issues a resize
  when the delta exceeds 1px. **Ruling:** assert the **dock** width exactly (probe-verified: 30, once
  the widget minimums allow it) and keep the `+1` tolerance only for inner/derived measurements the
  criteria do not name (`AP-D44-4`). The requirement's *outcome* — "the bar is 30px and stays 30px" —
  is unchanged, so the ACs need **no** requirement-side clarification. Two precisions recorded for
  Build: the guard asserts after the apply path has run (`processEvents`), and the 1px dead-band is
  itself unchanged behaviour, so the guard must not manufacture a 1px residual by its own driving
  sequence.
- **`FI-D44-2` — `A78`'s "the dock's title-bar widget presents the bar" cannot be literal for a
  *full-height* bar → CONFIRMED SATISFIED (intent met; no wording escalation).** Qt lays a left dock's
  title-bar widget out at the **top** of the dock, at the dock's full width and the widget's own
  `sizeHint` height — probe-verified by Plan and re-verified independently by the Validator — so a
  full-height vertical bar is impossible **in the title-bar slot**. D44 splits the affordance (`S25`):
  the full-height bar is the dock's **content** (`panel.collapsed_bar`) and the title-bar slot carries
  a 30×28 handle (`panel.collapsed_handle`) that keeps the dock movable (DG37) and clickable to expand.
  The **outcome** fixed by `AC-D44.1`/`AC-D44.6` (a thin, clickable, app-palette bar that reads as a
  panel) is unchanged, `A78` itself delegates the mechanism ("the widget/title-bar mechanism is an
  implementation choice"), and the requirement's own correction record sanctions the swap
  (`setTitleBarWidget` swaps to the bar, **or** the header widget reorients). The recorded **fallback**
  is the bar-as-title-bar variant if the handle proves problematic in build.
- **`FI-D44-3` — A76 does not say what width is persisted when the app is closed *while collapsed* →
  CONFIRMED (persist the tracked expanded width).** A76 fixes "not persisted; the app starts expanded"
  but is silent on the persisted **width** in that case. **Ruling:** the tracked **expanded** width is
  persisted (the `watchlist/width` key is unchanged and `_watchlist_width` is never overwritten while
  collapsed), so a restart starts expanded at the user's last expanded width. Persisting the applied
  30px would be re-clamped to the 150px minimum by `clamp_watchlist_width` on the way out — a silent
  loss of the user's width. An owner override would revise A76 and `S27`; the requirement's own outcome
  ("no collapse key exists; the app starts expanded") is satisfied either way.

### Correction record — for Task Manager / Build / Code Reviewer (D44)

The supersessions and the artifacts that must change (mirrors `### D44`'s correction record,
`:3914`–`:3925`):

1. **`AC-D21.11.2` / `AC-D21.11.3`** — their collapsed-appearance clause ("the collapsed state still
   shows the button", struck per `VIS-D21.1`) is **superseded for the collapsed watchlist state**: the
   collapsed form is the **thin bar with rotated text**. `VIS-D21.1` still applies to genuinely
   hidden/off **buttons** elsewhere (D21.12 volume, D21.13 portfolio) and to the header button whenever
   it is shown. **`AC-D21.11.1`** is unchanged (one "Watchlist" label; duplicate dock title deleted);
   the **title-bar widget identity** is `header_bar` while **expanded** and `collapsed_handle` while
   **collapsed** — the swap A78 authorises.
2. **`AC-D13.1` / `AC-D17.2`'s 150px minimum** — now applies to the **expanded** watchlist only; while
   collapsed the width is `WATCHLIST_COLLAPSED_WIDTH` (~30px). `AC-D13.2`/`.3` and `AC-D17.1`/`.3`–`.6`
   (cap, persistence, drag enforcement, re-clamp) are **unchanged for the expanded state**.
   `AC-D21.11`'s "collapsed-width geometry" edge case is **now specified** by `AC-D44.1`/`AC-D44.5`.
3. **The `## Non-Goals` restyling bullet** — revised by the owner (2026-10-16) to permit **only** the
   D44 collapsed-bar styling, in the **app palette** (`#141822` / `#232938` / `#cbd5e1`). The mockup's
   white rounded pill is explicitly **not** the target.
4. **Task Manager:** write the Phase-1 work items against `AC-D44.1`–`AC-D44.8` and the revised
   `AC-D21.11.2`/`.3` + the revised 150px-minimum scope; the per-file map above **is** the
   `touches_files` partition, and the two shared files (`ui/main_window.py`,
   `tests/test_watchlist_columns_d21.py`) force the two file-group pairs into **different waves** (the
   apply path before the wiring; the width-leg correction before the appearance-leg correction). The
   pure rule (`ui/dock_layout.py`) must land **before** its consumers, and the bar widget **before**
   the `MainWindow` wiring. Each corrected suite must be owned by the file-group that changes the
   behaviour it asserts (the `ESC-055` remedy) — do **not** defer the corrections to the reconciliation
   phase. Phase 2 adds no production edit. **`ESC-055` remains Task Manager's own open item** — D44
   applies its rule and does not absorb it.
5. **Build:** add `WATCHLIST_COLLAPSED_WIDTH` to `ui/dock_layout.py` and keep `CHART_MIN_WIDTH` in
   lockstep with `ui/watchlist_panel.py` (the documented invariant); make the collapsed width honoured
   by the **single** apply entry point in **both** branches, with the minimum-width relaxation +
   deferred re-apply; add the rotated-text bar widget in the app palette (with the title-bar handle)
   and wire click-to-expand to restore the tracked previous width; hide the header strip / `+` /
   column-header row while collapsed (un-hiding `header_bar` as it is restored to the title-bar slot).
   **Correct (do not merely weaken)** the four named sites + the docstring, and add the two new suites.
   **Demonstrate the guard is RED at `0c4d478`** — the collapsed dock staying at its expanded width /
   the 150px minimum, **not** an `ImportError` — and GREEN after, with the **full** offscreen suite
   green.
6. **Code Reviewer:** independently verify (a) the collapsed width **survives** a real `resizeEvent`
   **and** a drag-event path (the R66 defect class, the batch's core claim); (b) the palette matches the
   app and is **not** a white pill (the **rendered** check — the requirement assigns this to the
   reviewer, while the suites assert the stylesheet and the `active` property); (c) the **expanded**
   D13/D17/D18/D21.13 criteria and their suites are unaffected (run them, don't read them); (d) the dock
   is still **movable/floatable** while collapsed (DG37) and click-to-expand restores the **previous**
   width, re-clamped; (e) **no** collapse-state key is written (A76); (f) no corrected assertion was
   weakened, skipped or xfailed. Re-check `R66`/`R67`.
7. **Every future increment:** the **enumeration rule** — enumerate the assertions a change invalidates
   **by call site of the changed entry point, not by the suites the design names**, including suites
   that merely *drive* the changed path, and give the invalidated test files a home in `touches_files`
   (the `ESC-050` rule + `ESC-055`'s ownership remedy; D42's two under-counts and `ESC-055`'s
   recurrence are the recorded precedents).

### Incidentally affected (noted, not absorbed) (D44)

- **`ESC-055`** (`routed_to: TASK_MANAGER`, open, `nice-to-have`) — the D42/`ESC-050` enumeration rule's
  ownership remedy. D44 **applies** the rule (`AP-D44-8`) but does not absorb or close the escalation;
  it belongs to Task Manager.
- **`Q54`** (D44's owner-confirmation item) — **answered 2026-10-16** with recorded defaults A75–A77
  and surfaced to the owner as a non-blocking confirmation; no blocking question exists, so this run
  proceeds. An owner override would revise `AC-D44.1`/`.4`/`.7` + `A75`–`A77` + `S23`/`S26`/`S27`.
- **`DOC-1`** (any doc figure quoting a suite total) goes stale again because two suites are added and
  two extended; the owner/Analyst follow-up, not a Build task (`AP-D44-9`).
- **Line-number drift:** `docs/requirements/requirements.md` and the proposals cite line numbers that a
  `ui/main_window.py` edit invalidates (the file is edited often — `docs/memory.md`). Symbols are the
  primary pointer (`DG56`); every line reference in this section is **indicative only**.
- Nothing in D44 touches the chart renderer, the load path, the planner, the bar cache, the alarms, the
  drawings/studies, the orders machinery, the D41 removals, or the D42/D43 data paths.

Handoff: canonical set complete — `docs/architecture.md` (§ *D44 increment*, incl. the Codebase
Summary, `S22`–`S28`, the frozen-interface checklist, `AR-D44-1`–`AR-D44-10`, the traceability table
and the three ruled flagged issues), `docs/plan.md` (this section), `docs/plan_review.md`
(`Status: APPROVED`, D44 cycle), and `docs/plan_notes.md` (`FI-D44-1`–`FI-D44-3`, all `addressed`, no
escalation). Phase order: **Phase 1 → Phase 2**, with the pure rule before its consumers, the bar
widget before the wiring, and the two shared files (`ui/main_window.py`,
`tests/test_watchlist_columns_d21.py`) split across waves; then Code Reviewer verification
(a–f above), which also re-verifies `R66`/`R67`. **`ESC-055` stays TASK_MANAGER-owned.**

Status: superseded by the D45 section below (D44's `READY_FOR_TASK_MANAGER` was consumed by the D44
build — committed at `c702be9`, full offscreen suite green, review `REVIEW_COMPLETE`; the D44 handoff
record above is kept as history. The live handoff status line is the one at the end of this file).

---

## D45 — Batch 20: remove the News Digest dock (+ the `View` menubar), the Trade Context Menu, the **Kill switch** and the **SL/TP dialog** — the app ends with **zero order interaction** — validated 2026-10-25, **approved for build**

> **SUPERSEDED BY D46 / A99 (2026-10-25) — the stop/target *storage* half of this section.** D45 kept the columns and
> the fields ("no migration"); P5 **drops** them with a guarded migration (§ *Phase P5* `S47`). Every sentence below that
> says the storage is kept / unchanged / retained / migration-free is the **D45 record**, not the current end state.
>
> **Status of this section.** The canonical D45 plan. Validated by Plan Artifact Editor & Validator
> (`Status: APPROVED`, 2026-10-25) on a **legacy single-scope run** (no `Phase: P<n>`; the unsuffixed
> proposal pair; no phase gate), so the D45 increment merged into the cumulative canonical artifacts as
> § *D45 increment* in `docs/architecture.md` and this section here. **Approved for build, not yet
> as-built.** **D1–D44 are not reopened** beyond the supersessions D45 records.
>
> **Validation history (round 2 of 3).** Round 1 returned `CHANGES_REQUIRED` on four findings; all four
> were fixed by Plan in round 2 and **re-verified against the tree** at `c702be9`:
> **R1** — `tests/test_d27_flat_rows.py:110`–`:111` asserts `panel._selected_position`, which the panel
> edit deletes. Resolved by **deleting the selection tracker** (not by keeping it alive for one test) and
> adding that file to **wave 3** with an exact AC-3 adjustment; the test book is therefore
> **5 deleted / 7 adjusted / 1 added**.
> **R2** — the D27.1 AC-3 case (`tests/test_d27_position_id.py:170`–`:201`) passes only through the
> window's `position_sltp_changed` connection, so its **removal moved into wave 2** (the same wave as
> the connection it depends on); the `8`/`9` → `6`/`7` index edit stays in wave 3. Recorded as
> **sequencing rule 4**: no wave may leave an assertion referencing something a *previous* wave deleted.
> **R3** — the residue list gained the **nine** panel members wave 3 deletes, the scan scope is now
> stated in three parts (AST over `ui/ services/ data/ ibkr/ config/`; grep `ui/`-only; `tests/` in
> neither), and `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in the wave-6
> module.
> **R4** — the architecture's `tests/test_dock_d18_region.py` row now says the five-signal receiver loop
> is **deleted outright** (no signal survives), with the deviation from the D45 register's / DG77's
> suggested "three-signal loop" recorded here, in the architecture's supersession item **10** and in
> `docs/plan_notes.md` `RG-D45-1`.
> **No architectural decision changed** — the decisions `S29`–`S38` stand as validated in round 1.
>
> **Requirements of record:** `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, **0 open
> questions**) — **`### D45`** `:4100`–`:4481` (three removal groups, "Scope — KEEP", six owner-accepted
> consequences, `D45.1`–`D45.6`), **`AC-D45.1`–`AC-D45.10`** `:4282`–`:4370`, the supersession/revision
> record `:4371`–`:4416`, **A79–A90** `:4417`–`:4560`, correction record `:4461`–`:4481`; **Journey 38**
> `:1086`–`:1119`; **R68–R75** `:4699`–`:4706`; `design_gaps.md` **DG75** `:1189`–`:1212`, **DG76**
> `:1214`–`:1229`, **DG77** `:1231`–`:1260`. Companion architecture: `docs/architecture.md`
> § *D45 increment*. Module index: `docs/codebase-map.md` (refreshed for this batch).
>
> **Baseline:** `main` @ **`c702be9`** (2026-10-23); the working tree carried only this batch's
> requirements / design-gaps / map edits. Suite invocation
> `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale shebang).
>
> **Escalation state at validation time.** **No `PLAN`-routed escalation is open** —
> `docs/code_review/escalations.json` holds **no `status: "open"` entry at all**; the only
> `routed_to: PLAN` entry ever recorded (`ESC-050`) is `addressed`. `docs/tasks/task_manager_notes.md`
> carries no `ESCALATED_TO_PLAN`. **DG76** was the one open Plan-level question and it is **decided**
> here (`AP-D45-1` / architecture `S29`); DG75 is resolved by the requirements' own supersession (five
> named whole-file deletions); DG77 by the test book below. `docs/pending_doc_sync.md` is absent.
>
> **Owner decisions this plan does not re-litigate:** `A87` (Stop/Target **columns removed**, storage
> **kept**, no migration — **SUPERSEDED BY D46 / A99: the storage is DROPPED (§ *Phase P5* `S47`)**), `A89` (SL/TP dialog removed **completely**, including both `MainWindow`
> persistence slots and their row-`UPDATE`s), `A90` (the inbound order observers and the
> `order_registry` import are **intentionally inert**, not leftovers), `A79` (`"456"` dividends / tick
> 59 / `_dividend_info` / `dividend_updated` **stay**), `A86` (no menubar replaces the `View` menu),
> `A88` (no cancel capability survives or is re-pointed). **D41's "retained order machinery" is
> reversed** — **no** order path survives. **No new dependency**; PyQt6 / pyqtgraph / `ibapi` only, and
> **pyqtgraph is a locked decision** (`docs/memory.md`, 2026-10-16).

**The one workstream — subtractive, four removal groups, one invariant.** After D45 the app **places,
cancels and closes nothing**; trades and their protection live in **TWS**, and the app observes and
renders. The work splits by **member group** (never by file — the D41 lesson, memory 2026-10-15 / R69):

1. **Group A — the digest half of D38** (`AC-D45.1`, `.2`, `A79`, `A86`, R68): delete
   `ui/news_digest_dock.py` and `ibkr/news.py`; drop the dock + the **whole `View` menubar** + the news
   `"292"` S0 line and its digest-only plumbing. **Dividend substrate untouched.**
2. **Group B-main — the order path in the window** (`AC-D45.3`, `.4`, `A80`, A90): delete
   `_close_position_by_id` (the **only** `placeOrder` call site in the tree), the three close handlers,
   the two SL/TP persistence handlers, `_ref_price_for`, the `validate_order` import, and
   `ibkr/validation.py`.
3. **Group B-panel — the menu, the setter chain and the two columns** (`AC-D45.3`, `.5`, `.10`, `A87`,
   `A89`): delete `ui/trade_context_menu.py` and `ui/stop_loss_target_dialog.py`; strip the panel's menu
   policy/member/handlers, the five signals, the SL/TP chain, the menu-only selection tracker and the
   `Stop`/`Target` columns (**10 → 8**).
4. **Group C — the cancel path** (`AC-D45.6`, `A88`, `R73`, `R74`): delete `kill_btn` (+ its
   separator), `_on_kill_switch_clicked`, `_kill_switch`, and with them the app's **entire**
   `reqGlobalCancel` / `cancelOrder` capability. **Nothing is re-pointed; no replacement UI.**

The invariant that binds them is **reachability, not deletion count** (`D45.2`, `AC-D45.4`, `.6`): no
`ui/` module may call `placeOrder`, `cancelOrder` or `reqGlobalCancel`, import the deleted
feature/validation modules, or expose a removed member — verified by a **static source scan** plus a
**mocked-client zero-transmit walkthrough** (`S36`).

**Out of scope — do NOT plan these.** Every earlier defect/feature (D1–D44) and its delivered artifacts;
the chart/render stack (**pyqtgraph locked**), the load/backfill path, alarms, drawings, studies,
pop-outs, D39, D40, D42, D43, D44; `data/db.py`'s schema and migrations; `data/models.py`'s fields;
`ibkr/orders.py`'s **API** (retained — `S29`); `config/settings.py`; `ibkr/pacing.py`. **No new
dependency, no stack change, no replacement close/cancel/protection UI.**

---

### D45 phases — two phases, six waves (D45)

Phase 1 is the removal itself, split into **four waves forced by three shared files** (§ Sequencing):
one task per wave touches `ui/main_window.py`; `tests/test_dock_d18_region.py` and
`tests/test_d27_position_id.py` are each split across two waves by line range; and Group B's window half
lands **before** its panel half so every wave leaves the app importable and its own tests green. Phase 2
adds **no production edit**: it cleans the two owner-facing docs in one task and then builds the batch's
**acceptance instrument** and runs the batch gate.

#### Phase 1 — the removal (waves 1–4) (D45)

**Goal:** after wave 4 the app has **no order interaction** — no close/flatten, no cancel, no SL/TP
setter, no digest — while the dividend markers, the Portfolio render, D39, D40, D44 and the rest of the
app behave exactly as today.

**Covers:** `AC-D45.1`, `.2`, `.3`, `.4`, `.5`, `.6`, `.10`; requirements `D45.1`–`D45.4`, `D45.6`;
**Journey 38** steps 1–8; A79, A80, A86–A90; R68, R69, R72, R74, R75.

**Dependencies:** none on earlier batches (D1–D44 delivered). Internal order is **strictly sequential**.

| Wave | Task (proposed id) | Group | Goal | Files |
|---|---|---|---|---|
| **1** | `D45-01` | **A** — digest + `View` menubar + `"292"` | No digest dock, no menubar, no `Ctrl+Shift+N`, no `"292"` request; `"456"`/tick 59/markers intact | **edit** `ui/main_window.py`, `ui/ticker_session.py`, `tests/test_d38_events_news.py`, `tests/test_dock_d18_region.py`; **delete** `ui/news_digest_dock.py`, `ibkr/news.py` |
| **2** | `D45-02` | **B-main** — the order path in the window | `placeOrder` becomes **uncalled tree-wide**; no close/close-group/flatten; `validate_order` gone; the D27.1 AC-3 case leaves **with** the connection it depends on | **edit** `ui/main_window.py`, `tests/test_order_rejections.py`, `tests/test_d28_pacing.py`, `tests/test_dock_d18_region.py`, `tests/test_d27_position_id.py` (the AC-3 case only); **delete** `ibkr/validation.py`, `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`, `tests/test_order_validation.py` |
| **3** | `D45-03` | **B-panel** — menu + SL/TP chain + columns | No context menu, no close/SL-TP signals or setters, no dialog, no selection tracker; the table renders **8 columns** | **edit** `ui/active_portfolio_panel.py`, `tests/test_d27_position_id.py` (index edit), `tests/test_d27_position_prices.py`, `tests/test_d27_flat_rows.py`; **delete** `ui/trade_context_menu.py`, `ui/stop_loss_target_dialog.py`, `tests/test_sltp_honesty.py` |
| **4** | `D45-04` | **C** — the cancel path | No kill switch, no `reqGlobalCancel`/`cancelOrder` call anywhere; the toolbar keeps its remaining widgets + trailing stretch | **edit** `ui/main_window.py`; **delete** `tests/test_kill_switch.py` |

#### Phase 2 — docs, the acceptance instrument, and the batch gate (waves 5–6) (D45)

**Goal:** the docs advertise nothing that was removed, and the batch ships a **discriminating** guard for
"zero order interaction" plus the full-suite gate.

**Covers:** `AC-D45.7`, `AC-D45.8`, `AC-D45.9` (verification half); `D45.5`; **Journey 38** steps 8–9 and
its edge cases; R70, R71; `S36`, `S38`.

**Dependencies:** waves 1–4 complete (the guard asserts their end state; the docs must not describe a
live surface).

| Wave | Task (proposed id) | Goal | Files |
|---|---|---|---|
| **5** | `D45-05` | Docs cleaned in one task: no digest/`View`, no close/close-group/close-all, no kill switch, no SL/TP setter, no app-placed-order or "orders while disconnected" claim; instead: **closes and cancels happen in TWS**; SL/TP **columns** stay (no migration) — **SUPERSEDED BY D46 / A99: dropped; `D46.13`'s trail reads kept → cleared → dropped** | **edit** `USAGE.txt`, `usage.md` |
| **6** | `D45-06` | The acceptance instrument + batch gate: the new static/behavioural guard (**proven RED on the pre-D45 tree**), the full residue grep, the full offscreen suite, an import/launch check | **create** `tests/test_d45_removal.py`; **verify** everything else |

---

### D45 sequencing constraints — waves, shared files, and why the order is forced (D45)

Three facts fix the order. They are properties of the tree, not preferences:

1. **`ui/main_window.py` is touched by three groups** (A, B-main, C). The build scheduler must never
   place two tasks with overlapping `touches_files` in one wave, so the window is edited in **waves 1, 2
   and 4** — three separate tasks, strictly sequential.
2. **Group B splits along the panel's signal boundary, and the window must go first.**
   `MainWindow.__init__` connects `position_close_requested`, `group_close_requested`,
   `flatten_all_requested`, `position_sltp_changed` and `group_sltp_changed`
   (`ui/main_window.py:647`–`:651`). If the **panel** removed those signals first, `__init__` would raise
   `AttributeError` and **every** window-building test in the suite would fail for a reason unrelated to
   the work in flight — a wave that cannot pass its own tests. Removing the connections **first**
   (wave 2) leaves five signals with zero receivers: harmless, still constructible, still green once
   `tests/test_dock_d18_region.py`'s five-signal receiver loop is removed in the same wave. Wave 3 then
   removes the panel side. **This ordering is mandatory, not stylistic.**
3. **Two test files are shared across waves; the two docs are shared across *groups* and are therefore
   collapsed into one task.** `tests/test_dock_d18_region.py` and `tests/test_d27_position_id.py` are
   each touched in **more than one wave**: the two line ranges of `test_dock_d18_region.py` are split
   (**`:147` filter → wave 1; `:174`–`:179` receiver loop → wave 2**), and those of
   `test_d27_position_id.py` are split (**`:170`–`:201` AC-3 case → wave 2; `:164`–`:165` `8`/`9` →
   `6`/`7` → wave 3**) — different waves, so never concurrent. `USAGE.txt` / `usage.md` would otherwise
   be edited by three groups; they are **all deferred into one task (wave 5)** instead, because three
   groups editing the same prose in three waves would conflict for no benefit.
4. **No wave may leave an assertion that references something a *previous* wave deleted.** An assertion
   whose subject dies in wave *N* is removed or adjusted **in wave *N***, even when a later wave also
   edits that file. This is what fixes R2: the D27.1 AC-3 case's subject is the **window** connection
   (wave 2), not the panel setter (wave 3), so the case leaves in wave 2 while the same file's
   column-index edit stays in wave 3. The batch-end test book is unchanged in substance — only *which*
   wave carries the removal.

| Wave | Shared file | Other witnesses in the same wave? | Constraint |
|---|---|---|---|
| 1 | `ui/main_window.py`, `tests/test_dock_d18_region.py` | no | — |
| 2 | `ui/main_window.py`, `tests/test_dock_d18_region.py`, `tests/test_d27_position_id.py` (AC-3 case) | no (wave 1 finished) | **must follow wave 1** (same file); the AC-3 case goes **here**, in the wave that deletes the connection it passes through |
| 3 | `ui/active_portfolio_panel.py`, `tests/test_d27_position_id.py` (`8`/`9` → `6`/`7`) | `ui/main_window.py` **not** touched | **must follow wave 2** (panel signals may only go once the window stops connecting them); second touch of `test_d27_position_id.py` — different line range, never concurrent with wave 2 |
| 4 | `ui/main_window.py` | no | **must follow waves 1–2** (same file) |
| 5 | `USAGE.txt`, `usage.md` | no | must follow 1–4 (must not describe a live surface) |
| 6 | — (creates one new test module) | no | must follow 1–5 (asserts the end state) |

**Why not fewer waves?** Merging waves 2→3 (or 1→2) puts 300–500 deleted lines across 15+ files into one
task — exactly the size that killed three D41 workers (memory 2026-10-15; R69). Four waves of ~4–8 files
each is the mitigation the correction record asks for ("split the deletions by member group"). **Why not
more?** No task below the wave level: per-file/per-member decomposition is Task Manager's, and the six
waves are the milestone-level sequencing this plan owns.

---

### D45 per-file `touches_files` map (D45)

#### Wave 1 — `D45-01` (Group A) (D45)

| File | Action | Precise change (resolve by symbol, not by line) |
|---|---|---|
| `ui/main_window.py` | edit | Drop the `NewsDigestDock` import + `self.news_digest_dock` creation/addition + `menuBar()`/`view_menu`/`_news_digest_action`/`visibilityChanged` block; `_on_news_digest_visibility`; the `NewsManager` construction (`self.news_manager`); `b.tick_news.connect(self._on_s0_tick_news)`; `_on_s0_tick_news`. The window must then create **no `QMenuBar` at all**. |
| `ui/ticker_session.py` | edit | The news `"292"` need registration and its comments; `on_s0_tick_news`; `add_news_push_listener` / `remove_news_push_listener`; `set_s0_headless`; the `_s0_headless` attribute **and the two `or self._s0_headless` clauses** in `_s0_resync` / `_s0_reissue`. **Do not touch:** `_needs["dividends"] = {"456"}`, `on_s0_tick_string` (tick 59), `_dividend_info`, `dividend_info`, `dividend_updated`, `_merge_ibkr_dividend_event`, `_merge_events`, `events`. |
| `ui/news_digest_dock.py` | **delete** | whole file |
| `ibkr/news.py` | **delete** | whole file (its only consumer was the dock + its tests) |
| `tests/test_d38_events_news.py` | edit | Remove the `NewsManager` section (3 cases) and the **whole** `AC-D38.2`/`AC-D38.3` digest section (`_StubNewsManager`, `_StubHost`, `_make_dock`, 3 cases). Trim the module docstring of `AC-D38.2`/`AC-D38.3`/`NewsManager`; correct the md-line-guard docstring's `"292"` reference. **Keep** the tick-59, yfinance-cache, `AC-D38.1`/`.4`/`.5`, no-mock-endpoint and md-line-guard cases verbatim. |
| `tests/test_dock_d18_region.py` | edit | `:147` only — drop `and d.objectName() != "NewsDigest"` from the right-dock filter (**not** the receiver loop; that is wave 2). |

#### Wave 2 — `D45-02` (Group B-main) (D45)

| File | Action | Precise change |
|---|---|---|
| `ui/main_window.py` | edit | Remove the 5 `.connect` lines (3 close + 2 SL/TP); `_on_portfolio_close_position`; `_on_portfolio_close_group`; `_on_portfolio_flatten_all`; `_on_portfolio_sltp_changed`; `_on_portfolio_group_sltp_changed` (with the two `UPDATE … SET stop_loss=…` statements); `_close_position_by_id`; `_ref_price_for`; the `from ibkr.validation import validate_order` import; and the now-unused names in the `ibkr.pacing` import (`order_limiter`; `pacing_manager` is already unused at module level) **and** the unused `UserOrder` in the `ibkr.orders` import — keeping `orders as order_registry` and `PacingExceeded`. **Do not touch** `_on_open_order`/`_on_order_status`/`_on_exec_details`/`_on_order_error`/`_update_order_status` (A90). |
| `ibkr/validation.py` | **delete** | whole file |
| `tests/test_d28_6_close_contracts.py` | **delete** | whole file |
| `tests/test_d41_retained_order_path.py` | **delete** | whole file |
| `tests/test_order_validation.py` | **delete** | whole file |
| `tests/test_order_rejections.py` | edit | Delete `test_close_blocked_while_disconnected` (its subject is gone) and any helper only that case used; **keep** `pytest` (a surviving `@pytest.mark.parametrize` case uses it), the `_fresh_registry`/`_register` helpers, and the `_on_order_error` / `classify_error` cases (they cover the **retained** observer path). Update the module docstring's "the disconnected refusal is asserted on the retained close path" sentence. |
| `tests/test_d28_pacing.py` | edit | Delete `test_close_position_defers_when_limiter_empty` whole. Keep every historical-pacing case (D28.3, unrelated to the order bucket). |
| `tests/test_d27_position_id.py` | edit | Remove `test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row` (`:170`–`:201`) **whole** — its only passing path is `update_position_sltp` → `position_sltp_changed` → `MainWindow._on_portfolio_sltp_changed` (`:650`, `:3342`), and **this task deletes the window half** (R2). **Do not** touch `:164`–`:165` here — the table still has 10 columns until wave 3. **Keep** the AC1 live-update case and the AC2 bulk-`id` case verbatim, and leave the module docstring's pre-fix narrative alone (it records ESC-032 history, not live wiring). |
| `tests/test_dock_d18_region.py` | edit | `:174`–`:179` — **delete the five-signal receiver loop** (the wiring it asserts no longer exists in this wave: the window has stopped connecting all five, and the panel's own definitions follow in wave 3). Keep the surrounding assertions: the panel stays the dock's widget, `account_summary_changed` / `positions_changed` are still present, and the zero-receiver sanity probe on `positions_changed` still proves the probe is not vacuous. Replace the "exactly the five Portfolio connections wired by MainWindow" comment with the post-D45 statement (**no close/SL-TP signal is wired; the panel is view-only**). **No further edit to this file is needed in wave 3.** |

#### Wave 3 — `D45-03` (Group B-panel) (D45)

| File | Action | Precise change |
|---|---|---|
| `ui/active_portfolio_panel.py` | edit | Remove the `TradeContextMenu` / `StopLossTargetDialog` imports and `QMenu` if unused; the `position_sltp_changed` / `group_sltp_changed` / `position_close_requested` / `group_close_requested` / `flatten_all_requested` signals; `self._context_menu` and its five `.triggered.connect` lines; `setContextMenuPolicy(CustomContextMenu)` + its `customContextMenuRequested` connection (**back to the default policy**); `_show_context_menu`; `_on_set_sltp`; `_on_sltp_confirmed`; `update_position_sltp`; `update_group_sltp`; `_sltp_dialog`; `_on_close_position`; `_on_close_group`; `_on_ungroup`; `_on_flatten_all`; and the menu-only selection tracking (`_selected_row`, `_selected_position`, `_on_selection_changed`, its `itemSelectionChanged` connection, and the two comments that name it). **Columns:** `QTableWidget(0, 8)`, headers `Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`; drop the two `stop_loss`/`take_profit` values from `_render_table`'s list; right-aligned set `(1, 2, 4, 5)`; correct the `RIGHT_DOCK_MIN_WIDTH` docstring's "10-column" wording. **Do not touch:** `summary_label`/`_on_header_toggled`/`is_collapsed`/`set_collapsed`/`toggle_collapsed`, `set_account_summary`/`set_account_id`/`set_account_unavailable`, `set_positions`/`add_position`, `refresh`/`_render_summary`/`_group_and_render`, `account_summary_changed`, `positions_changed`, `_unrealized_pnl`, `RIGHT_DOCK_MIN_WIDTH`'s value. |
| `ui/trade_context_menu.py` | **delete** | whole file |
| `ui/stop_loss_target_dialog.py` | **delete** | whole file |
| `tests/test_sltp_honesty.py` | **delete** | whole file (both cases assert the deleted dialog's labels) |
| `tests/test_d27_position_id.py` | edit | `:164`–`:165` `8`/`9` → `6`/`7`. **Nothing else** — the AC-3 case was already removed in **wave 2** with the window half of its subject (R2). **Keep** the AC1 live-update case and the AC2 bulk-`id` case (the D27.1 id-correctness property stays covered there). |
| `tests/test_d27_flat_rows.py` | edit | **AC-3 only.** Delete `table.selectRow(0)` + `qapp.processEvents()` (`:108`–`:109`) and the two `panel._selected_position` assertions (`:110`–`:111`) — the tracker they read is deleted by this task (`AP-D45-4`, R1). **Keep `:104`–`:106` verbatim** (`rowCount() == len(panel._positions)`, plus the per-row `symbol`/column-0 alignment) — that is the property AC3 exists for. Rewrite the docstring's AC3 sentence (`:11`–`:13`), which names `_on_selection_changed`/`_selected_position`, to: *"AC3: the panel's position list and its rendered rows stay index-aligned, so a row index resolves to the row the user sees."* AC1/AC2 cases untouched. |
| `tests/test_d27_position_prices.py` | edit | `:290`–`:291` `8`/`9` → `6`/`7`. Nothing else. |

#### Wave 4 — `D45-04` (Group C) (D45)

| File | Action | Precise change |
|---|---|---|
| `ui/main_window.py` | edit | Remove `self.kill_btn` (text `"Kill Switch"`, `setObjectName("KillSwitchButton")`, tooltip, `#b91c1c` style, `clicked.connect`), **the `QLabel("|")` separator immediately before it**, `_on_kill_switch_clicked`, and `_kill_switch` (incl. `self.ib_client.reqGlobalCancel()`, the per-ID `self.ib_client.cancelOrder(oid)` loop, the terminal-status pre-count, the `order_registry.update_status(oid, "Cancelled")` marking and the pre/post status-bar message). The toolbar keeps its remaining widgets and its trailing `addStretch()`. **No replacement control; no teardown/disconnect cancel.** |
| `tests/test_kill_switch.py` | **delete** | whole file (4 cases; its `test_bracket_builder_registers_all_three_legs` also drives `_kill_switch`) |

#### Wave 5 — `D45-05` (docs) (D45)

| File | Action | Precise change |
|---|---|---|
| `USAGE.txt` | edit | Remove the Close/Close Group/Close All Positions section, the **Kill switch** bullet, the **Set Stop-Loss / Take-Profit** bullet, the "orders cannot be placed while disconnected" claim, and the **`View → News Digest (Ctrl+Shift+N)`** section. Add/keep one plain statement: **the app places, cancels and closes nothing — closes and cancels happen in TWS**, and the Portfolio panel is view-only; the stop/target **columns** are kept (no migration) but the values are no longer settable or shown, and are **cleared when the position next updates** (ESC-060). **SUPERSEDED BY D46 / A99: the columns are DROPPED at first open; a pre-P5 DB keeps every row and loses only those two values.** |
| `usage.md` | edit | Rework `### Portfolio & SL/TP` (heading + steps 2–3: no right-click close/flatten, no SL/TP dialog) into a view-only description; correct the Portfolio table row (line ~102: no "SL/TP, close/flatten actions"); in the Database section keep `positions` / `trade_groups` listed **with a note** that the SL/TP **columns** stay (no migration) but are no longer settable in-app and are cleared by the next position update (ESC-060) — **SUPERSEDED BY D46 / A99: the note must read DROPPED (one-time migration, every row kept)**; remove any news-digest mention. |

*(`docs/codebase-map.md` is **Plan-owned** and already refreshed in this batch — it is **not** a Build task.)*

#### Wave 6 — `D45-06` (instrument + gate) (D45)

| File | Action | Precise change |
|---|---|---|
| `tests/test_d45_removal.py` | **create** | The `S36` instrument: (a) `importlib.util.find_spec` returns `None` for the five deleted modules and the five deleted suites are absent; (b) an AST token scan over `ui/`, `services/`, `data/`, `ibkr/`, `config/` (identifiers **and** string constants, D41 precedent) finds none of the tokens in § *The residue verification step* outside the explicit survivor allow-list; (c) `ui/` contains no `placeOrder`/`cancelOrder`/`reqGlobalCancel` call site; (d) a real offscreen `MainWindow` with a mocked `IBApiClient.connect` and mocked `placeOrder`/`cancelOrder`/`reqGlobalCancel` driven through **every remaining affordance** (chart load, timeframe/mode/ext-hours switches, watchlist add/remove + column popup, alarms, studies, drawings, pop-outs, Portfolio selection + refresh, an external position update/close, a `_on_order_error` emission, `closeEvent`) asserts all three call counts are **0**; (e) the position table has `columnCount() == 8` with no `Stop`/`Target` header and Strategy/Group at `6`/`7`; (f) the dividend path is still alive (`"456"` registered, tick 59 → `dividend_updated`, `event_count() > 0`); (g) the `AC-D45.3` measurables asserted **directly** (the token list is a net, not a substitute): `hasattr(panel, name) is False` for the nine removed panel members (`_show_context_menu`, `_on_close_position`, `_on_close_group`, `_on_ungroup`, `_on_flatten_all`, `_selected_row`, `_selected_position`, `_on_selection_changed`, `set_sltp_action`) and for the five removed signals, plus `panel.positions_table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu`. |
| everything | **verify** | Full residue grep, full offscreen suite, import/launch check, and the **RED-on-`c702be9`** evidence (§ Tests). |

---

### D45 tests — deleted, adjusted, kept, and why each still means something (D45)

#### Deleted — five whole files (A81, `AC-D45.8`), all named; nothing rests on a count (D45)

| File | Subject that no longer exists | Coverage consequence (stated, not hidden) |
|---|---|---|
| `tests/test_d28_6_close_contracts.py` | `_close_position_by_id`'s contract rebuild + the disconnected gate | the only close-order contract/flatten coverage is gone |
| `tests/test_d41_retained_order_path.py` | `validate_order` + `_ref_price_for` + the retained order path | the retained-order-path assertions (D41-S4/S5) are gone with the path |
| `tests/test_order_validation.py` | `validate_order` (table-driven) | the notional/STP/BRACKET gate has no subject any more |
| `tests/test_kill_switch.py` | `_kill_switch` (4 cases) | the only **cancel-path** coverage, and the only *integration* driver of `Orders`/`bracket_order` registration, is gone |
| `tests/test_sltp_honesty.py` | `StopLossTargetDialog`'s disclosure labels | the only assertion that the SL/TP dialog transmitted nothing |

#### Adjusted — seven files, each with the exact invalidated assertion (D45)

| File | Invalidated assertion | Adjustment | Why it is invalidated |
|---|---|---|---|
| `tests/test_d38_events_news.py` | the 3 `NewsManager` cases + the 3 digest cases (`AC-D38.2`/`.3`) | remove both sections; keep everything else | `ibkr/news.py` and the dock are deleted (`AC-D38.2`/`.3` **superseded**) |
| `tests/test_dock_d18_region.py` | `:147` `objectName() != "NewsDigest"` filter; `:174`–`:179` five-signal receiver loop | drop the filter (wave 1); **delete the loop** and restate the wiring comment (wave 2) | the dock no longer exists; and after wave 2 the window connects none of the five removed signals, while the panel still defines them — a loop asserting "≥1 receiver" would be red for a reason already decided, and a loop asserting `hasattr` could not go green until wave 3 |
| `tests/test_order_rejections.py` | `test_close_blocked_while_disconnected` drives `_close_position_by_id` | delete that case (wave 2); keep helpers + `_on_order_error`/`classify_error` cases | the disconnected-order gate has no order path to guard (`AC-D26.9` moot); the **observer** path it also covers is retained (A90) |
| `tests/test_d28_pacing.py` | `test_close_position_defers_when_limiter_empty` | delete the case only (wave 2) | it drives `_close_position_by_id` and pins the (deleted) gate-before-pacing order |
| `tests/test_d27_position_id.py` | `test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row` (`:170`–`:201`); `:164`–`:165` `item(0, 8)`/`(0, 9)` | remove that case **in wave 2**; `8`/`9` → `6`/`7` **in wave 3** | its subject is deleted in **two halves** — the window connection/handler in wave 2, the panel setter in wave 3 — so the case cannot outlive either (R2); the columns shift in wave 3 |
| `tests/test_d27_flat_rows.py` | `:108`–`:111` — `table.selectRow(0)` then `assert panel._selected_position is not None` / `.symbol == table.item(0, 0).text()` | drop `:108`–`:111`; keep `:104`–`:106`; restate the AC3 docstring sentence (wave 3) | `AP-D45-4` deletes the selection tracker in wave 3 and every reader of it is deleted in the same batch, so the assertion's subject no longer exists (R1). The index-alignment property it guards stays asserted |
| `tests/test_d27_position_prices.py` | `:290`–`:291` Strategy/Group at `8`/`9` | `8`/`9` → `6`/`7` (wave 3) | the columns shifted (R75) |

> **Exactness note for Task Manager.** The Group B split makes the `test_dock_d18_region.py` receiver
> loop unassertable in the middle of the batch — after wave 2 the **window** connects none of the five
> signals, while the **panel** still defines them (they are deleted only in wave 3). Asserting "≥1
> receiver" would be red for an already-decided reason; asserting `hasattr(...) is False` could not go
> green until wave 3. So the loop is **deleted in wave 2** and the file carries no reference to the
> removed signals afterwards, which is the correct end state for both waves. The one remaining
> D45-related adjustment to that file is the `:147` dock filter in wave 1. Recorded so the second half is
> not "discovered" as a regression.
>
> **Deviation from the D45 register's suggested form (R4 / `RG-D45-1`) — do not "restore" it.** The
> register's own correction record (`requirements.md:4178`–`:4179`) and `design_gaps.md` DG77 item 4 both
> describe this same edit as "the five-signal receiver loop **shrinks to three**". That form is
> **unachievable**: D45 deletes **all five** signals (the three close signals in Group B-main and the two
> SL/TP signals in the extension), so after the batch **no signal survives** — a three-signal loop would
> reference three deleted attributes and be red in wave 3, while in wave 2 it would be red for the
> already-decided reason that the window connects none of them. The loop is therefore **deleted whole**
> in wave 2, which is exactly what `AC-D45.8` asks (the file is *adjusted*; no clause names a surviving
> signal). Recorded here, in `docs/plan_notes.md` `RG-D45-1`, in the architecture's System-Components row
> and in its supersession list (item 10), so Task Manager / Code Reviewer do not read the register's
> suggestion as pending work.

#### Kept by decision — verified individually, not assumed (D45)

| File | Decision | Verification performed | Why it still means something |
|---|---|---|---|
| `tests/test_stop_loss_target.py` | **keep unchanged** | reads only `data.models.Position`/`TradeGroup`; no UI import, no dialog reference | A87 keeps the model fields, so "the fields exist, default `None`, accept explicit values" is still true and still worth asserting — **SUPERSEDED BY D46 / A99: the fields are DELETED and this suite with them (§ *Phase P5* wave 7)** |
| `tests/test_d41_removal.py` | **keep unchanged** | its only news reference is the `queue_depth` **string** in `_ALLOWED_ANYWHERE`; its scan reads `ui/ services/ data/ ibkr/ config/` only and `queue_depth` never needs to resolve; its request-absence case still issues its S0/RT lines because `"456"` survives | it still guards D41's removals (footprint/depth/auction/order-entry UI), which D45 does not restore |
| `tests/test_order_builders.py` | **keep unchanged** | covers builders (`market_order`/`limit_order`/`stop_order`/`bracket_order` incl. OCA groups + `transmit` flags) **and** the registry (`register`/`get`/`update_status`/`clear_filled`/`all`) | **this is the residual unit coverage of the retained `ibkr/orders.py`** — DG77's "no tests at all" is corrected here: what the deletions took was the *integration* driver, not the module's own coverage |
| `tests/test_d27_position_id.py`'s **AC2** case | **keep** | asserts `_on_position_end` stamps each row's real `positions.id` | the D27.1 id-correctness property (ESC-032) survives even though the AC3 SL/TP row-addressing case cannot |
| every other suite | **untouched** | a `tests/`-wide scan found **no** other reference to the removed tokens (the nine panel members, the five signals, the deleted modules/methods, `_kill_switch`): the Portfolio context menu appears only in watchlist tests (a different, retained popup); no `positions_table.columnCount()` equality assertion other than the two named index files. The **one** file the book carries beyond the obvious set is `tests/test_d27_flat_rows.py` — its AC-3 tail reads `_selected_position`; adjusted in wave 3 (R1) | the suite's remaining 125+ modules build windows, charts, docks and pop-outs — the batch gate runs them all |

#### Added — one module (D45)

`tests/test_d45_removal.py` (wave 6). It must be **discriminating**: run it against a pristine `c702be9`
copy (`git worktree add`, or a copy of the tree) and record the **exact** failures it produces there
(e.g. the token scan reporting `kill_btn`, `_kill_switch`, `reqGlobalCancel`, `cancelOrder`,
`placeOrder`, `StopLossTargetDialog`, `position_sltp_changed`, `NewsManager`, `TradeContextMenu`,
`validate_order`, …; the walkthrough reporting non-zero cancel calls). A guard that passes on both trees
is not a guard — that evidence is part of the task's acceptance, not a nicety.

---

### D45 residue verification step (task-level, not a hope) (D45)

D45's correction record asks Build to grep **after each file**, per group. This plan makes that a
**named, checkable step in every wave** and a **full pass in wave 6**, with the **survivor allow-list**
beside it — so "fix the residue" cannot be satisfied by deleting things the requirement keeps.

**The two instruments, and their exact scope (R3).** They are **not** the same net, and the difference is
load-bearing:

1. **AST scan** — identifiers **and** string constants (the `tests/test_d41_removal.py` precedent) over
   **`ui/ services/ data/ ibkr/ config/`**. It reads *code*, so **comments are invisible to it**: the
   D26.7 comment in `config/settings.py` that names `validate_order()` is **not** an offence, and
   `config/settings.py` is a file **no D45 task may edit** (`AP-D45-11`).
2. **Grep step** — **`ui/` only** (the prose net for human workers), after each edited file and once per
   wave.
3. **`tests/` is covered by neither instrument.** The residue list is therefore a net, not a substitute
   for the test book: `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in
   `tests/test_d45_removal.py` (wave 6, item **(g)**).

**Forbidden after D45 — grep over `ui/`, AST over the five source dirs:**

`292` · `NewsManager` · `news_manager` · `news_digest` · `NewsDigest` · `news_digest_dock` ·
`_on_news_digest_visibility` · `menuBar` · `view_menu` · `Ctrl+Shift+N` · `_on_s0_tick_news` ·
`on_s0_tick_news` · `news_push_listener` · `set_s0_headless` · `_s0_headless` · `TradeContextMenu` ·
`trade_context_menu` · `position_close_requested` · `group_close_requested` · `flatten_all_requested` ·
`_on_portfolio_close_position` · `_on_portfolio_close_group` · `_on_portfolio_flatten_all` ·
`_close_position_by_id` · `validate_order` · `placeOrder` · `_ref_price_for` · `kill_btn` ·
`KillSwitchButton` · `_kill_switch` · `_on_kill_switch_clicked` · `reqGlobalCancel` · `cancelOrder` ·
`StopLossTargetDialog` · `stop_loss_target_dialog` · `position_sltp_changed` · `group_sltp_changed` ·
`_on_portfolio_sltp_changed` · `_on_portfolio_group_sltp_changed` · `_on_set_sltp` · `_on_sltp_confirmed` ·
`_sltp_dialog` · `update_position_sltp` · `update_group_sltp` · `_show_context_menu` · `_on_close_position` ·
`_on_close_group` · `_on_ungroup` · `_on_flatten_all` · `_selected_row` · `_selected_position` ·
`_on_selection_changed` · `set_sltp_action`

*The nine added tokens are the panel members wave 3 deletes. Each was re-counted on 2026-10-25 and lives
**only** in `ui/active_portfolio_panel.py` (plus `ui/trade_context_menu.py` for `set_sltp_action`), both
of which this batch edits/deletes ⇒ **zero** post-D45 hits: `_show_context_menu` 2 · `_on_close_position`
2 · `_on_close_group` 2 · `_on_ungroup` 2 · `_on_flatten_all` 2 · `_selected_row` 4 · `_selected_position`
15 occurrences on 13 lines · `_on_selection_changed` 4 · `set_sltp_action` 4.*

**Survivors — MUST NOT be reported as residue (they are `AC-D45.2`/A90's deliberate end state):**

| Survivor | Where | Why it stays |
|---|---|---|
| `"456"`, tick `59`, `_dividend_info`, `dividend_updated`, `dividend_info`, `_merge_ibkr_dividend_event`, `_merge_events`, `parse_ib_dividend_string` | `ui/ticker_session.py`, `data/events/` | the chart's dividend markers (`AC-D45.2`, R68) |
| `tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article` (bridge signals + client overrides) | `ibkr/bridge.py`, `ibkr/client.py` | the ibapi boundary mirrors; now unconnected, never requested (`S35`) |
| `order_registry`, `orders`, `UserOrder` (in `ibkr/orders.py`), `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`, `classify_error` | `ui/main_window.py`, `ibkr/orders.py`, `ibkr/error_codes.py` | A90's inert **observers** + `S29`'s retained module; they place/cancel nothing |
| `order_limiter` (definition), `pacing_manager`, `PacingExceeded`, `MAX_ORDER_NOTIONAL` (definition) — **and the D26.7 comment in `config/settings.py` that names `validate_order()`** | `ibkr/pacing.py`, `config/settings.py` | shared modules/config, **outside** the owner's inventory; left untouched (see *Incidentally affected*). The comment is a **comment**: the AST scan cannot see it and the grep does not read `config/`, so it is in scope for **no** instrument — and no task may "fix" it (`AP-D45-11`) |
| `queue_depth` (allow-list string) | `tests/test_d41_removal.py` | D41's documented allow-list entry; the file stays unchanged |

**Per-wave command shape** (Build runs it after each edited file, and once per wave):
`grep -rn --include="*.py" -e '<token>' … ui/` for each forbidden token — **zero hits**, plus a bespoke
`"292"`/`"456"` check in `ui/ticker_session.py` (`"292"` absent, `"456"` present) and an
`ls`/`find_spec` check that the five deleted modules are gone. **Wave 6** runs the same list as the static
half of `tests/test_d45_removal.py`, so the grep and the test cannot drift apart.

---

### D45 assumptions (D45)

| # | Assumption | Rationale |
|---|---|---|
| **AP-D45-1** | **`ibkr/orders.py` is retained, not deleted** (architecture `S29`). No task touches its API; the only permitted edit is a module-docstring note stating it is unreachable after D45. | DG76 is Plan-level and A80 defaults to "leave it". The module is **not** orphaned — `ui/main_window.py:36` imports the `orders` singleton for the retained observers (A90) — and deleting it would force registry-safe rewrites of the error path for zero reachability gain while discarding `tests/test_order_builders.py`'s real coverage. The requirement measures **unreachability**, not file existence. |
| **AP-D45-2** | **`MainWindow._ref_price_for` is deleted**; `_symbol_last_prices` stays. | Verified: one production caller (inside `_close_position_by_id`), zero after wave 2. R74 names a leftover `_ref_price_for` as a half-removed-path residue; keeping it would leave an order accessor with no consumer. The price map itself is read by the Portfolio P/L path (`:3207`) and **must not** be touched. |
| **AP-D45-3** | **`_s0_headless` removal is a three-site edit** (the attribute + the two `or self._s0_headless` clauses). A worker that removes only the attribute leaves a live `AttributeError`, and one that removes only the flag leaves a dead always-`False` condition. | Set only by the deleted digest; read in two S0 line-build paths. Recorded because it is the least discoverable part of Group A. |
| **AP-D45-4** | **The panel's selection tracking goes with the menu** (`_selected_row`, `_selected_position`, `_on_selection_changed`, its `itemSelectionChanged` connection, and the two comments naming it). | Every **production** reader is a handler this batch deletes (`_show_context_menu` :372, `_on_set_sltp` :377–379, `_on_close_position` :400–401, `_on_close_group` :405–406, `_on_ungroup` :410–411), and `_on_selection_changed`'s only other effect is `self._context_menu.set_actions_enabled(...)` (:358/:364/:368) — also deleted (re-verified `ui/`-wide 2026-10-25). The **one** reader outside the panel is `tests/test_d27_flat_rows.py:110`–`:111`; that file is adjusted in the **same wave** (R1), so the tracker does not outlive its last reader. If a worker finds any other consumer it must **stop and report**, not silently keep a half-wired tracker. |
| **AP-D45-5** | **Group B is window-first** (waves 2 → 3), never panel-first. | Panel-first makes `MainWindow.__init__` connect deleted signals → `AttributeError` in every window test (architecture `S37`). |
| **AP-D45-6** | **One task per wave on `ui/main_window.py`** (waves 1, 2, 4), strictly sequential; no two tasks in one wave may share a file. | The scheduler forbids overlapping `touches_files` within a wave; explicit dependency edges make the order deterministic. |
| **AP-D45-7** | **All doc edits are one task** (wave 5); `docs/codebase-map.md` is **Plan-owned** and already refreshed, so it is not a Build task. | Three groups would otherwise edit the same prose in three waves; the map is a per-batch Plan artifact (memory 2026-10-23). |
| **AP-D45-8** | **`tests/test_d41_removal.py` and `tests/test_stop_loss_target.py` are kept unchanged**, verified rather than assumed. | `AC-D45.8` names the first explicitly; A87 implies the second (model fields stay). **SUPERSEDED BY D46 / A99:** `tests/test_stop_loss_target.py` is **deleted** in P5 wave 7 because its subject (the four fields) is dropped. |
| **AP-D45-9** | **`tests/test_order_builders.py` stays** and is the residual unit coverage of the retained `ibkr/orders.py`. **SUPERSEDED BY D46 / A99 (`S39`): the module and this suite are both DELETED.** | Corrects DG77's premise; recorded so the module is not "found" untested later — and so no task deletes that file while tidying. |
| **AP-D45-10** | **The new guard scans identifiers AND string constants** (the `tests/test_d41_removal.py` precedent), with the explicit survivor allow-list above; therefore **docstrings naming a removed member must be rewritten in the same wave** (a comment is invisible to AST, a docstring/string constant is not). | Prevents a wave from being "green by grep, red by AST"; and prevents a false residue report from a survivor. |
| **AP-D45-11** | **`config/settings.MAX_ORDER_NOTIONAL` and `ibkr/pacing.order_limiter` are left in place** (no edit, no deletion). | Outside the owner's named inventory (`A85` scopes docs; the requirement names no config module). They are dead config/helper, recorded in *Incidentally affected* rather than silently cleaned. |
| **AP-D45-12** | The requirements' `_persist_position` is the tree's **`_upsert_position`**; no rename. | Naming drift in the requirements text; the symbol is unambiguous and the method is untouched by D45. |
| **AP-D45-13** | The test book is **5 deleted / 7 adjusted / 1 added** whole files, with case-level trims in six of the adjusted files (all but `tests/test_d27_position_prices.py`, which is a two-line index change). No other file changes. | Matches `A81`/`AC-D45.8` — five **named** whole-file deletions, and every invalidated assertion outside them enumerated; a `tests/`-wide scan found no eighth affected file. The seventh is `tests/test_d27_flat_rows.py` (the AC-3 `_selected_position` tail — R1). |

---

### D45 flagged issues and Validator rulings (D45)

**None blocking.** Every requirement in D45 (`D45.1`–`D45.6`, `AC-D45.1`–`AC-D45.10`, Journey 38) is
satisfiable as written by the decisions above — the removals are self-contained, the only shared
mechanism (the S0 register) is preserved by construction, and the storage requirement (A87) — **SUPERSEDED BY D46 / A99: the storage is DROPPED (§ *Phase P5* `S47`)** — needs **no**
migration. No requirement was narrowed or reinterpreted to fit a convenient architecture.

**Recorded for the Validator's awareness — deliberately *not* escalated (each is a note, not a
requirement defect):**

1. **Naming drift:** the requirements say the SL/TP persistence slots' "position upsert in
   `_persist_position`" stays unchanged; the tree's method is **`_upsert_position`**
   (`ui/main_window.py:3283`). Same method, same behaviour; `AP-D45-12`. No doc change is asked of
   Requirements because the intent is unambiguous.
2. **Two dead remnants are intentionally left standing:** `config/settings.MAX_ORDER_NOTIONAL` (only
   consumer was the deleted `ibkr/validation.py`) and `ibkr/pacing.order_limiter` (order-path bucket, now
   unread). Deleting them would exceed the owner's named inventory and touch shared modules
   (`AP-D45-11`); D45's consequence 3 ("the notional cap … no longer gate anything") already records the
   *mootness*.
3. **`docs/codebase-map.md`'s generated skeleton** is rebuilt from the tree by `update_codebase_map.py`,
   so it keeps listing the deleted files **until the next batch's refresh**; `AC-D45.7`'s "the map no
   longer lists …" is satisfied by the Plan-owned **annotation tables**, which are rewritten to the
   post-D45 target state and say so in the map's header (`S38`). This is a property of the tooling, not an
   unmet criterion.
4. **Validator rulings (2026-10-25).** `FI-D45-1` (the register's suggested "three-signal loop") is
   **ruled satisfied by the loop deletion** and recorded as `RG-D45-1` in `docs/plan_notes.md`
   (`Status: addressed`, no escalation); the test-book sequencing defects that round 1 found (R1/R2) are
   **closed in round 2** and re-verified against the tree; R3/R4 are closed by the instrument and the
   architecture correction. **No `ESCALATED_TO_REQUIREMENTS`.**

---

### D45 correction record — for Task Manager / Build / Code Reviewer (D45)

**Plan:** refreshed `docs/codebase-map.md` (re-ran `update_codebase_map.py`; rewrote the annotation
layer: the three removed modules and `ibkr/validation` no longer live; `_kill_switch` /
`StopLossTargetDialog` no longer named as retained; the **`placeOrder` ownership error corrected** — it
is ibapi's inherited `EClient.placeOrder`, not an `IBApiClient` method; `ibkr/orders.py` recorded as
**retained with no transmit caller**; the D45 test book and the wave order added). **Round 2:** R1–R4
applied — the selection tracker deleted with an added wave-3 file; the D27.1 AC-3 removal moved to
wave 2; the residue instrument's list and scope made true; the D18 receiver-loop row reconciled (the
map's book updated to 7 adjusted).

**Task Manager:**
- Build the six waves with **explicit dependency edges** `D45-01 → D45-02 → D45-03 → D45-04 → D45-05 →
  D45-06` (`ui/main_window.py` in 1/2/4, `tests/test_dock_d18_region.py` in 1/2,
  `tests/test_d27_position_id.py` in 2/3). Do **not** let two tasks share a file in a wave.
- **Enumerate invalidated assertions outside the edited files** (memory 2026-10-23 item 4; `ESC-055`
  rule): `tests/test_d41_removal.py` (verified green), `tests/test_dock_d18_region.py` (`:147` wave 1;
  `:174`–`:179` wave 2), `tests/test_d38_events_news.py` (two sections), `tests/test_d27_position_id.py`
  (**the SL/TP case in wave 2**; `8`/`9` in **wave 3**), `tests/test_d27_flat_rows.py` (`:108`–`:111`,
  wave 3), `tests/test_d27_position_prices.py` (`8`/`9`), `tests/test_stop_loss_target.py` (verified
  green — **SUPERSEDED BY D46 / A99: deleted in P5 wave 7**), `tests/test_order_builders.py` (verified green —
  **SUPERSEDED BY D46 / A99 (`S39`): deleted in P5 wave 3**).
- **Honour the wave-membership rule (sequencing rule 4)**: an assertion whose subject dies in wave *N* is
  removed or adjusted in wave *N*. Do **not** merge the two `tests/test_d27_position_id.py` edits into one
  task, and do not schedule either in a wave that does not also carry the change that invalidates it.
- **Do NOT task any change to `ibkr/orders.py`** beyond the permitted docstring note (`AP-D45-1`), and do
  not task any config/pacing cleanup (`AP-D45-11`).
- Wave 6's acceptance includes the **RED-on-`c702be9`** evidence for the new guard.

**Build:**
- Split by **member group**, and **run a syntax/import check plus the group's residue grep after each
  file** (the D41 worker-death mitigation, memory 2026-10-15).
- Every delete-only task: **`git status` the file list before finishing** — a "done" task that left a
  file half edited is the failure mode that killed three D41 workers.
- Deletions are **whole-file only** where the table says "delete"; any partial trim is enumerated in the
  per-file map above and nowhere else.
- Comments referencing a deleted member are prose; **docstrings or string constants naming one must be
  rewritten in the same wave** (`AP-D45-10`) or the wave-6 scan fails.

**Code Reviewer (independent, do not trust the task book):**
- Confirm **zero** `placeOrder`, **zero** `cancelOrder`, **zero** `reqGlobalCancel` call sites in `ui/`.
- Confirm **the dividend markers still render** (`"456"` registered; tick 59 → `dividend_updated`;
  `event_count() > 0`) — the single highest-risk deletion (R68).
- Confirm the positions table has **8 columns** with no `Stop`/`Target` header and that Strategy/Group
  sit at `6`/`7`.
- Confirm a **pre-D45 database** opens with its stored `stop_loss`/`take_profit` values intact and that
  `_upsert_position` still writes them (no migration, no data loss). **SUPERSEDED BY D46 / A99:** the columns are
  DROPPED at first open — every row survives, only those two values are lost (legacy-fixture test).
- Confirm the three docs advertise nothing removed, and that `docs/codebase-map.md` no longer names
  `_kill_switch`, `StopLossTargetDialog`, `ui/news_digest_dock`, `ui/trade_context_menu` or
  `ui/stop_loss_target_dialog` as live/retained.
- Confirm the **new guard is discriminating** (its pre-`c702be9` failures are recorded) and that the
  intentional survivors (A90's observers, the ibapi news signals, the dividend path) were **not**
  deleted.

---

### Incidentally affected (noted, not absorbed) (D45)

- **`config/settings.py::MAX_ORDER_NOTIONAL`** (and its D26.7 comment) — its only consumer was the
  deleted `ibkr/validation.py`; now dead config. **Deliberately not cleaned** (`AP-D45-11`): it is
  outside the owner's inventory and a config edit is not required for any D45 criterion.
- **`ibkr/pacing.py::order_limiter`** — the order-path bucket; no reader after D45. **Deliberately
  untouched** (shared, tested module; `pacing_manager` and the historical-pacing guarantees stay live).
- **`ibkr/bridge.py` news signals + `ibkr/client.py` news overrides** — become unconnected rather than
  removed (`S35`). A future reader may mistake them for leftovers; the map and A90 record them as the
  ibapi boundary.
- **`tests/test_d38_events_news.py`'s module docstring** lists `AC-D38.2`/`AC-D38.3` and "NewsManager
  sequential issuance" — trimmed by wave 1; its `test_md_line_guard_thresholds` docstring names
  `"292"`/`"456"` and is corrected to the surviving `"456"` line.
- **`tests/test_d41_removal.py`'s `queue_depth` allow-list entry** — survives the `ibkr/news.py`
  deletion as a string; the file is **not** edited (`AC-D45.8` names it as kept).
- **`ui/main_window.py`'s `ibkr.pacing` / `ibkr.orders` import lines** carry names that become unused
  (`order_limiter`, `UserOrder`, and the already-unused `pacing_manager`) — trimmed in wave 2 so the file
  has no dead import; `PacingExceeded` and `orders as order_registry` **must stay**.
- **macOS application menu** — with `menuBar()` gone the app contributes no app-menu items (A86). No
  replacement menubar, no orphan `QAction`.
- **Line-number drift:** every line reference in this section is **indicative only** (symbols are the
  primary pointer — `DG56`); `ui/main_window.py` is edited by three waves in this batch.

Handoff: canonical set complete — `docs/architecture.md` (§ *D45 increment*: Codebase Summary, `S29`–`S38`,
the frozen-interface table, `AR-D45-1`–`AR-D45-10`, the traceability table and the ten supersessions /
non-changes), `docs/plan.md` (this section), `docs/plan_review.md` (`Status: APPROVED`, D45 cycle 2 of 3),
and `docs/plan_notes.md` (`RG-D45-1`, `addressed`, no escalation). Phase order: **Phase 1 → Phase 2**,
with the window before the panel, the docs collapsed into one task, and the guard last. The Code Reviewer
re-verifies the batch's four claims (zero transmit / zero cancel / dividend markers alive / no Stop-Target
columns) independently of the task book.

Status: READY_FOR_TASK_MANAGER

---

## Phase P5 — D46 (Batch 21): **every** order-related coding path is deleted — the module, the observation chain, the zero-consumer order utilities, `IdManager.reserve`, and the stop/target storage (a real, guarded migration) — **drafted rev 1 2026-10-25, activated, DEMOTED by the scope-expansion run, re-drafted as revision 2, and validated + re-activated (validation 2, 2026-10-25)**

> **Revision notes — revision 2, 2026-10-25.** This is **not** a revision against a `CHANGES_REQUIRED` list: revision 1
> was **APPROVED** and activated, and then the **requirements were re-registered wider** (Q56–Q59; `D46` is now
> `D46.1`–`D46.13` / `AC-D46.1`–`AC-D46.13` / A91–A104 / R76–R85 / DG78–DG87). The section was **demoted from
> `READY_FOR_TASK_MANAGER` to a draft** by this run and re-drafted against the wider register. What changed, and
> nothing else:
>
> - **Waves 5 → 10**, because four new member groups joined (pacing + notional cap, the order-fill sound,
>   `IdManager.reserve`, and the stop/target storage) and the guard's token set had to move to a point where every
>   token names code that is already gone (**invariant I-1**). The forced order (consumer → boundary → module),
>   the group split and the per-name ownership discipline are **extended, not restarted**.
> - **The migration** (`S47`): four guarded in-place `ALTER TABLE … DROP COLUMN` statements — **executed and
>   measured** in `.venv` (rows, `sqlite_sequence`, the unique index, the FK, `foreign_key_check`,
>   `integrity_check`, the 13-column upsert + `RETURNING id`, a second open). Not the `bars` rebuild.
> - **The index shift** (`S48`, DG85): name-keyed read at the one reshaped SELECT **plus** a new assertion with a
>   non-null `trade_group_id` — measured: **no test seeds one today**, so the trap was uncovered.
> - **The instrument** (`S44`): the exact-match set for `orders`/`Orders` is **kept**, but revision 1's *reason* for it
>   ("a file no task may edit") is **void** — `pacing.py` and `id_manager.py` are now edited. `reserve` is **not** a
>   token (measured: 13 units / 11 files, all "preserve(s/d)"). `stop_loss`/`take_profit` are substring tokens
>   because a SQL column list is one string constant.
> - **The book**: `1 deleted / 3 adjusted / 0 added` → **`2 deleted / 13 adjusted / 0 added`**.
> - **`ESC-062` folded in** (`S49`): three comments in the wave that already edits their files, one deleted
>   incidentally, one test rename in the prose wave. No new task.
>
> **Status of this section — ACTIVE (Validated 2026-10-25, validation 2).** The canonical **P5** plan, drafted **in place**
> (Stage 3.4 — no separate proposal file), **demoted by the scope-expansion run** and re-drafted as revision 2. It was
> validated in full against the expanded register and **activated** by Plan Artifact Editor & Validator
> (`docs/plan_review_P5.md`); it ends `Status: READY_FOR_TASK_MANAGER`. Companion:
> `docs/architecture.md` § *Phase P5 — D46 increment* (decisions `S39`–`S50`, risks `AR-D46-1`–`AR-D46-12`, the frozen
> interfaces, the traceability table, the nineteen supersessions/revision records). Module index:
> `docs/codebase-map.md` — **refreshed by Plan in this phase** (`AC-D46.6`/DG81, `ESC-063`).
>
> **Requirements of record:** `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, **no blocking
> question**) — **`### D46`** (`D46.1`–`D46.13`, `AC-D46.1`–`AC-D46.13`, the DELETE/RETAIN inventory, the
> supersession record, A91–A104, the correction record), **Journey 39** (steps 1–10), **R76–R85**,
> `design_gaps.md` **DG78–DG87**, `open_questions.md` **Q56–Q59**.
>
> **Baseline:** `main` @ **`c702be9`** **plus the delivered D45 working tree** (D45 built, suite green, five
> modules and five suites already deleted). Suite: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`.
> **No new dependency; PyQt6 / pyqtgraph / `ibapi` only (pyqtgraph is locked — `docs/memory.md` 2026-10-16).**
>
> **Escalation state.** **`ESC-063`** (open, routed **PLAN**) is **already resolved in `docs/codebase-map.md:25`–`:29`**
> — the D45 book reads **5 deleted / 7 adjusted / 1 added** with the `ESC-063` note; this run keeps the map current
> for the wider scope and does not re-open the arithmetic. **`ESC-061`** (open, BUILD) is **MOOT** — it asked for a
> module-docstring note on `ibkr/orders`, which this phase deletes; **no task implements it** and the Code Reviewer
> closes it as moot. **`ESC-062`** (open, BUILD) is **folded into this phase** (`S49`, waves 1, 7 and 9) — its four
> comment sites sit in files this phase already edits, so **no separate wave** is created. **`ESC-059`/`ESC-060`**
> stay BUILD-owned and are **not** absorbed: ESC-060's behavioural half becomes **moot** when the columns go and its
> documentation half is **superseded** by this phase's trail (§ *Document trail*). `docs/pending_doc_sync.md` is
> absent.
>
> **Owner decisions this plan does not re-litigate:** A91 (module deleted **in full**, reversing A80), A92 (chain
> **removed**, not kept inert, reversing A90 — owner-confirmed), A93 (the generic line is the end state — no verdict,
> no order id, no 12 s — owner-confirmed), A94 (routing **not** reordered), A96 (`data.models.UserOrder` goes —
> owner-confirmed), **A99 (the four columns and every model field are DROPPED by migration, reversing A87 —
> owner-confirmed by Q59)**, A100 (`classify_error` + the generic error surface stay), A101 (module stays, only
> `reserve` goes — reversing A97's first half), A102 (`nextValidId` retained), A103 (the inventory is the acceptance
> instrument), A104 (the two suites are deleted whole). **No replacement order, cancel or protection UI** — not
> re-proposed anywhere.

**The one workstream — subtractive, ten member groups, one invariant, one migration.** After D45 the app has zero
order interaction; D46 removes the **fossil that still looks live** and the storage that outlived its only setter.
Every code member it deletes is already inert: `Orders.register()` is never called in production, so the registry is
permanently empty, every `get()` returns `None`, `_update_order_status` is a no-op and `_on_order_error` is
unreachable; `OrderRateLimiter`/`order_limiter`, `MAX_ORDER_NOTIONAL` and `SoundService.play_fill` have **zero**
production readers; `IdManager.reserve` has **tests only**; and the four stop/target columns are unreachable, unsettable
and undisplayed — a row that never receives another live update keeps its legacy bytes, which is why the drop is
stated as **the batch's only byte-destroying step** (A99/D46.12), not as a cost-free delete. The
work splits by **member group** (never by "all the order stuff" — the D41 lesson, memory 2026-10-15 / R76):
<span id="p5-groups"></span>

1. **Group 1 — the window consumers** (`AC-D46.1`, `.2`, `S40`/`S41`): the three `.connect` lines, the three slots,
   `_update_order_status`, `_on_order_error`, the `_on_error` registry branch (+ its D26.9 comment) and the
   `order_registry` import.
2. **Group 2 — the broker boundary** (`AC-D46.2`, `S40`): the three `EWrapper` overrides **and** the three `Bridge`
   signals, in **one** task.
3. **Group 3 — the module and its data-model twin** (`AC-D46.1`, `.4`, `.8`, `S39`/`S42`): `ibkr/orders`, the
   builders suite, `data.models.UserOrder`, the smoke assertion.
4. **Group 4 — the order-plumbing utilities** (`D46.11`): `OrderRateLimiter`/`order_limiter` and their two test
   sites, `MAX_ORDER_NOTIONAL`.
5. **Group 5 — the order-fill sound** (`D46.11`): `render_fill_blip`, `BLIP_DURATION`, `_fill_effect`, `play_fill`,
   the `"fill"` key, `order_fill.wav`, the docstring bullet, **and the `_effect` collapse**.
6. **Group 6 — `IdManager.reserve`** (`D46.10`, A101): the method, its D26.2 docstring, and its six test cases.
7. **Group 7 — the stop/target storage** (`D46.12`, A99, `S47`/`S48`): the DDL, the migration, the three model
   copies, the two factory parameters, all six persistence sites, and the whole stop/target test book — **one task**.
8. **Group 8 — the instrument** (`S44`): the guard's token set, absence pools, end-state test and prose.
9. **Group 9 — the surviving prose** (`D46.6`, `S50`): `classify_error`'s comment, `USAGE.txt`, `usage.md`, the
   `ESC-062` rename.
10. **Group 10 — the batch gate**: verification only.

The invariant that binds them is **proven inertness, preserved visibility, preserved rows**: no order module,
callback, signal, registry, dataclass, builder, limiter or `reserve()` in the tree (`D46.1`–`D46.11`); **201 / 103 /
202 still reach the status bar** as `Error [<code>]: <TWS's own message>` for **8000 ms** (`D46.3`, the owner's
constraint); and **every `positions`/`trade_groups` row survives** the migration with its unique index and FK
(`D46.12`). The **kept** surface is frozen with its consumer named (architecture `S46`): `classify_error`,
`IBApiClient.error`'s `severity != 'info'` gate, the D40.1 `502` suppression, `error_msg`, `_on_error`'s
session-first routing and its 8000 ms line, the fail-fast port check, the badge, **`IdManager` + `get_id` (six
callers)**, `nextValidId`, `PacingManager`/`PacingExceeded`/`pacing_manager`, the ICT order blocks, `sort_order`,
`TradeGroup`/strategy grouping, `Position`/the Portfolio view, `play_alarm`/`render_alarm_chime`,
`advancedOrderRejectJson`.

**Out of scope — do NOT plan these.** D1–D45 and their delivered artifacts; the chart/render stack (pyqtgraph
locked); the load/backfill path; alarms, drawings, studies, pop-outs, D39, D40, D42, D43, D44; `data/db.py`'s
**other** tables, indexes and migrations; `data/models.py`'s other entities; `ibkr/pacing.py`'s `PacingManager`;
`ibkr/id_manager.py`'s `get_id`/`set_next_valid_id`; `config/settings.py`'s other constants;
`services/sound_service.py`'s **alarm** path; `ibkr/error_codes.py`'s **code**; `ui/ticker_session.py`;
`ui/active_portfolio_panel.py`; the ICT order blocks; `sort_order`; `tests/test_d41_removal.py`;
`tests/test_db_schema.py`. **No new dependency, no stack change, no order/cancel/protection UI, no restoration of
the registry under another name, no DB file copy, and no fix to the pre-existing orderId↔session-reqId collision**
(A94/DG78).

---

### Phases (P5) — three phases, ten waves

Phase 1 is the removal itself, in **seven waves forced by the callback graph and by the schema** (§ *Sequencing*).
Phase 2 is **the instrument and the surviving prose** — no production removal. Phase 3 is the batch gate. Total:
**10 tasks**, one per wave, strictly sequential, never two tasks sharing a file in a wave.

#### Phase 1 — the removal (waves 1–7) (P5)

**Goal:** after wave 7 the app has **no order code at all** — no module, registry, override, signal, slot, builder,
limiter, notional cap, order tone or `reserve()` — **and no stop/target column or field**, while a TWS error carrying
201/103/202 still shows its code and TWS's message on the status bar, every `positions`/`trade_groups` row survives,
and every other feature behaves exactly as today.

**Covers:** `AC-D46.1`–`.4`, `.8`, `.10`, `.11`, `.12`; requirements `D46.1`–`D46.4`, `D46.8`, `D46.10`–`D46.12`;
**Journey 39** steps 1–2 and 7–8 with their edge cases; A91–A94, A96, A99–A102, A104; R76, R78, R81, R82, R84;
DG78, DG79, DG82, DG83, DG85, DG86, DG87.

**Dependencies:** none on earlier batches (D1–D45 delivered). Internal order is **strictly sequential**
(`P5-T01 → … → P5-T07`).

| Wave | Task | Group | Goal | Files |
|---|---|---|---|---|
| **1** | `P5-T01` | **1** — window consumers | No window-side order member, no order connect, no registry lookup in `_on_error`; the three signals still exist with **zero receivers** (harmless); the generic line untouched | **edit** `ui/main_window.py` (1st), `tests/test_order_rejections.py`, `tests/test_d45_removal.py` (1st) |
| **2** | `P5-T02` | **2** — broker boundary | No order `EWrapper` override, no order bridge signal — deleted **together**, so no emitter can outlive its signal | **edit** `ibkr/client.py`, `ibkr/bridge.py` |
| **3** | `P5-T03` | **3** — module + data-model twin | `import ibkr.orders` fails; no `UserOrder` anywhere; the builders suite gone; the smoke assertion gone | **delete** `ibkr/orders.py`, `tests/test_order_builders.py`; **edit** `data/models.py` (1st), `tests/test_ui_smoke.py` |
| **4** | `P5-T04` | **4** — pacing + notional cap | No `OrderRateLimiter`, no `order_limiter`, no `MAX_ORDER_NOTIONAL`; `pacing_manager` intact | **edit** `ibkr/pacing.py`, `config/settings.py`, `tests/conftest.py`, `tests/test_d28_pacing.py` |
| **5** | `P5-T05` | **5** — order-fill sound | No fill tone, no `"fill"` key, no `_fill_effect`; **the alarm chime still plays** | **edit** `services/sound_service.py`, `tests/test_sound_service.py` |
| **6** | `P5-T06` | **6** — `IdManager.reserve` | `reserve` gone; `get_id`/`set_next_valid_id`/the module intact and still called six ways | **edit** `ibkr/id_manager.py`, `tests/test_id_manager.py` |
| **7** | `P5-T07` | **7** — stop/target storage (schema + every reader) | No `stop_loss`/`take_profit` column, field or parameter; every row, the unique index and the FK preserved; the bulk load reads `trade_group_id` **by name**; the Portfolio stays 8 columns | **edit** `data/db.py`, `data/models.py` (2nd), `ibkr/account.py`, `ui/main_window.py` (2nd), `tests/test_account.py`, `tests/test_strategy_detection.py`, `tests/test_d27_position_id.py`, `tests/test_d27_account_partial_window.py`, `tests/test_d27_account_scoping.py`; **delete** `tests/test_stop_loss_target.py` |

#### Phase 2 — the instrument and the surviving prose (waves 8–9) (P5)

**Goal:** the guard names exactly the code that is gone (and nothing that survives), the end state is **asserted**
rather than inferred from a green suite, and no surviving prose tells a reader that the order surface or the
stop/target columns still exist.

**Covers:** `AC-D46.5`, `.6`, `.7`, `.9`, `.11`, `.12`, `.13` (verification halves); requirement `D46.5`, `D46.6`,
`D46.9`, `D46.13`; Journey 39 steps 9–10; R79, R80, R83, R85; DG80, DG81, DG84; `ESC-062`.

**Dependencies:** waves 1–7 complete (the instrument asserts their end state, and **invariant I-1** requires every
token to name code that is already gone).

| Wave | Task | Goal | Files |
|---|---|---|---|
| **8** | `P5-T08` | The instrument: `_SURVIVORS` 26 → 16, `_FORBIDDEN` 53 → 80, two absence pools, the end-state test (chain, module, `UserOrder`, `reserve`, the utilities, the four fields, the schema + idempotence), and the guard's own retention-era prose | **edit** `tests/test_d45_removal.py` (2nd, one coherent edit) |
| **9** | `P5-T09` | Prose matches the tree: `classify_error`'s comment, the two user docs (**kept → cleared → dropped**), the `ESC-062` test rename | **edit** `ibkr/error_codes.py` (comment only), `usage.md`, `USAGE.txt`, `tests/test_dock_d18_region.py` |

#### Phase 3 — the batch gate (wave 10) (P5)

**Goal:** the batch ships with the end state **proven**, not inferred.

**Covers:** `AC-D46.3`, `.5`, `.9`, `.12`, `.13`; Journey 39 steps 3–6; R77, R80, R82, R85.

| Wave | Task | Goal | Files |
|---|---|---|---|
| **10** | `P5-T10` | Full offscreen suite; the residue sweep with the survivor list beside it; `AC-D46.3` reproduced **for 201, 103 and 202**; an import/launch probe; the migration reproduced on a legacy fixture; the doc-trail grep; the recorded pre-P5 guard failure set | **verify** everything; **no production edit** |

---

### Sequencing constraints — waves, the callback graph, and why the order is forced (P5)

Five facts fix the order. They are properties of the tree, not preferences:

1. **Consumer before subject.** No wave may leave a reference to a name an earlier wave deleted (D45's rule 4,
   applied here). The `_on_error` registry branch, `_on_order_error` and `_update_order_status` are reachable
   **only** from a live TWS callback or a non-session error, so a stale reference to them is **invisible to the
   suite**. They go first, with the import, in wave 1.
2. **An emitter never outlives its signal.** `IBApiClient.orderStatus` / `openOrder` / `execDetails` emit
   `bridge.order_status` / `open_order` / `exec_details`. If the signal is deleted one wave before its emitter,
   `self.bridge.order_status.emit(...)` raises `AttributeError` **only when TWS sends an order callback** — which
   no test ever does — so the suite stays green while the app breaks on the owner's first order event. The
   overrides and the signals are therefore deleted in **one task** (wave 2).
3. **The window's connect/slot half goes before the bridge half.** `MainWindow.__init__` connects all three
   (`:595`–`:597`). Deleting the signals first would raise `AttributeError` at construction (loud, and every
   window test fails); deleting the slots while the connects remain would do the same. Wave 1 removes connects +
   slots + `_update_order_status` + `_on_order_error` + the branch + the import in one pass, leaving three live
   signals with **zero receivers** — constructible, harmless, green.
4. **The module goes last.** `ibkr/orders.py` has one importer (wave 1) and its registry is read only by
   `_update_order_status` (wave 1) and `_on_error` (wave 1). By wave 3 nothing names it, so its deletion cannot
   create an intermediate break; `data/models.UserOrder` and the builders suite have no relationship to the
   bridge and go in the same wave as their own subjects.
5. **The guard's token list may only name what is already gone (invariant I-1, new in revision 2).** At every wave
   boundary, every token in `_FORBIDDEN` names code that no longer exists and every name in `_SURVIVORS` still
   exists. With the wider scope the ten names die across **waves 1–6** and the storage dies in **wave 7**, so a
   staged token migration would have to be re-edited four times — in the one file where a mechanism error already
   cost a revision round. It therefore lands **once**, in wave 8, when all of them are gone; the interim net is the
   **mandatory per-wave residue grep**, which uses the final token list from wave 1 onward (§ *Residue*).
6. **The schema and its readers land in one task (R84/DG85).** A half-landed column drop does not fail loudly — it
   fails as `row[12]` holding a stop value in the **Group** column. Wave 7 therefore owns the DDL, the migration, the
   three model copies, the factory parameters, all six persistence sites **and** the whole stop/target test book. It
   is the only wave that would leave the suite red until its own test edits land, and nothing outside it depends on
   the columns.

| Wave | Shared file(s) | Constraint |
|---|---|---|
| 1 | `ui/main_window.py`, `tests/test_order_rejections.py`, `tests/test_d45_removal.py` | first — the consumer half of every pair it touches |
| 2 | `ibkr/client.py`, `ibkr/bridge.py` | **must follow 1** (its only receivers are gone); emitter + signal in one task |
| 3 | `ibkr/orders.py` (delete), `tests/test_order_builders.py` (delete), `data/models.py` (1st), `tests/test_ui_smoke.py` | **must follow 1–2**; the module dies after its only importer and readers |
| 4 | `ibkr/pacing.py`, `config/settings.py`, `tests/conftest.py`, `tests/test_d28_pacing.py` | independent of 1–3; `conftest`'s two resets die with `order_limiter` |
| 5 | `services/sound_service.py`, `tests/test_sound_service.py` | independent; `_effect` collapses in the same wave |
| 6 | `ibkr/id_manager.py`, `tests/test_id_manager.py` | independent; the module survives, only `reserve` goes |
| 7 | `data/db.py`, `data/models.py` (2nd), `ibkr/account.py`, `ui/main_window.py` (2nd), 3 seeders, `test_account`, `test_strategy_detection`, `test_stop_loss_target` (delete) | **must follow 3** (its `data/models.py` touch); schema + every reader + the whole test book in **one** task |
| 8 | `tests/test_d45_removal.py` (2nd) | **must follow 1–7**; second touch of the guard — different lines, never concurrent with wave 1 |
| 9 | `ibkr/error_codes.py`, `usage.md`, `USAGE.txt`, `tests/test_dock_d18_region.py` | must follow 1–8 (prose describes the end state) |
| 10 | — (verification only) | must follow 1–9 |

**Which wave owns each name** (so no wave has to guess, and no name is left ownerless):

| Name | Owned (deleted) by | Note |
|---|---|---|
| `order_registry` (the import and every read) | **wave 1** | guard token added in **wave 8** |
| `_on_open_order`, `_on_order_status`, `_on_exec_details` | **wave 1** | their last inbound path (the three `.connect` lines) dies in the same task |
| `_update_order_status` | **wave 1** | its three callers are the three slots — same task |
| `_on_order_error` (+ its only caller, the `_on_error` branch) | **wave 1** | and the walkthrough call in `tests/test_d45_removal.py` in the same task |
| `order_status`, `open_order`, `exec_details` (bridge signals) | **wave 2** | deleted **with** their emitters, after their receivers are gone |
| `orderStatus`, `openOrder`, `execDetails` (`EWrapper` overrides) | **wave 2** | same task as the signals — never split |
| `ibkr.orders`, `Orders`, `UserOrder` (module), the four builder names, the `orders` singleton | **wave 3** | module + builders suite in one task |
| `data.models.UserOrder` + its smoke assertion | **wave 3** | class and assertion together (R81) |
| `tests/test_order_builders` | **wave 3** | its whole subject is `ibkr.orders` |
| `OrderRateLimiter`, `order_limiter` (+ `conftest`'s two resets, the `test_d28_pacing` case) | **wave 4** | one task: the class, the singleton and their only readers |
| `MAX_ORDER_NOTIONAL` | **wave 4** | same wave as the pacing bucket (both are D46.11 utilities) |
| `render_fill_blip`, `BLIP_DURATION`, `_fill_effect`, `play_fill`, the `"fill"` key, `order_fill.wav`, the docstring bullet, **`_effect`'s collapse** | **wave 5** | `_effect` must collapse to alarm-only or the ternary's `"_fill_effect"` string keeps the scan red |
| `IdManager.reserve` (+ its docstring, its four pure cases, two rewritten cases) | **wave 6** | **the module stays** — six `get_id()` callers |
| `positions.stop_loss/take_profit`, `trade_groups.stop_loss/take_profit` (DDL + migration), `Position`/`TradeGroup` fields, `ibkr.account.Position` + the two factory parameters, all six persistence sites, `tests/test_stop_loss_target` | **wave 7** | one task (R84/DG85); `trade_group_id` 14 → 12, read **by name** |
| the guard's token set, absence pools, end-state test, its own prose | **wave 8** | one coherent edit (I-1) |
| `classify_error`'s comment, `USAGE.txt`, `usage.md`, the `ESC-062` rename | **wave 9** | prose only |
| `classify_error`, `_on_error`, `error_msg`, `IBApiClient.error`, `nextValidId`, `set_next_valid_id`, `get_id`, `id_manager`, `PacingManager`, `PacingExceeded`, `pacing_manager`, `order_blocks`, `sort_order`, `TradeGroup`, `Position`, `play_alarm`, `render_alarm_chime`, `advancedOrderRejectJson` | **no wave — survivors** | frozen (`S46`); deleting any of them is an offence, not a tidy-up. The `ibkr/error_codes.py` **comment** is reworded in wave 9, the code is not |

**Why not fewer waves?** Merging 1→3 puts the whole chain and the module in one delete-only task — the shape that
killed three D41 workers (memory 2026-10-15; R76) and the exact shape that makes the silent failure possible,
because nothing intermediate is checkable. **Why not more?** Three removal waves are the smallest split that keeps every
emitter/signal/receiver triple inside one wave and every subject with its own assertions; per-file/per-member
decomposition is Task Manager's, not this plan's.

**Why not the register's order?** Its correction record suggests "(1) `ibkr/orders.py` deletion + importer
cleanup" first. That is **not executable as a standalone wave**: removing the import while `_on_error` still
reads `order_registry` turns every non-session TWS error into a `NameError` — the very silent-path defect above —
and deleting the file while `ui/main_window.py` still imports it breaks every test at collection. The register's
**member groups** are kept; only their **order** is forced (architecture supersession item 9, `AP-D46-1`).

---

### Per-file `touches_files` map (P5)

#### Wave 1 — `P5-T01` (Group 1: window consumers) (P5)

| File | Action | Precise change (resolve by symbol, never by line) |
|---|---|---|
| `ui/main_window.py` | edit | Delete the import `from ibkr.orders import orders as order_registry`; the three `.connect` lines in `__init__` (`b.open_order` / `b.exec_details` / `b.order_status`); `_on_open_order`, `_on_exec_details`, `_on_order_status` (**whole methods, incl. `_on_order_status`'s `mktCapPrice` comment**); `_update_order_status` (whole); `_on_order_error` (whole); and in `_on_error` the D26.9 comment block **and** `if order_registry.get(reqId) is not None: self._on_order_error(...); return`. **Do NOT touch:** `_on_error`'s `_closing` guard, its `session = self._session_for_req_id(reqId)` branch (RT via `_on_rt_stream_error`, historical via `session.on_historical_error` + the same 8000 ms line), or the final `self.status_bar.showMessage(f"Error [{errorCode}]: {errorString}", 8000)` — these are the owner's error visibility (`AC-D46.3`) and are frozen. Also untouched: `b.error_msg.connect(self._on_error)`, `_symbol_last_prices`, `_upsert_position`, `_on_position_end`, `closeEvent`. |
| `tests/test_order_rejections.py` | edit | Delete the two registry cases (`test_rejected_order_updates_registry_and_status`, `test_cancelled_order_updates_registry`) and the helpers only they used (`_fresh_registry`, `_register`) and the `from ibkr.orders import Orders, UserOrder` import. **Repoint and rename** `test_non_order_error_untouched` → `test_non_order_error_shows_generic_line`: call `win._on_error(reqId=9999, errorCode=2105, errorString="Data farm connection is broken")` and assert `win.status_bar.currentMessage()` contains `"[2105]"` **and** the TWS string, and that nothing raises. **Add one parametrised case** `test_order_error_codes_surface_on_status_bar` over `201` / `103` / `202` (`ids=["201","103","202"]`), each calling `win._on_error(reqId=987654, errorCode=code, errorString=<TWS text>)` (an id matching **no** live session reqId) and asserting the message contains `f"[{code}]"` **and** TWS's own text. **Keep verbatim:** both `classify_error` cases and `_make_window`. Rewrite the module docstring — it names `MainWindow._on_order_error`; state that the status bar's generic line is the surface and that the order registry no longer exists. |
| `tests/test_d45_removal.py` | edit | **Two edits only in this wave** (the allow-list is wave 3): (a) in the behavioural walkthrough, replace `win._on_order_error(1, 201, "Order rejected (walkthrough)")` with `win._on_error(reqId=1, errorCode=201, errorString="Order rejected (walkthrough)")` — the survivor-path drive, not the removed handler; (b) update the module docstring's bullet 3, which lists "an `_on_order_error` emission", to name the **`_on_error` generic-line** drive instead. **Do not** touch `_SURVIVORS`/`_FORBIDDEN` here. |

#### Wave 2 — `P5-T02` (Group 2: broker boundary) (P5)

| File | Action | Precise change |
|---|---|---|
| `ibkr/client.py` | edit | Delete the `orderStatus` override (incl. the B1/`mktCapPrice` comment and the `super().orderStatus(...)` call and the `self.bridge.order_status.emit(...)`), the `openOrder` override, and the `execDetails` override — **whole methods, no `pass` stubs**. **Do NOT touch:** `error` (the D40.1 `502` suppression and `severity != 'info'` gate), `connected`, `_do_reconnect`, the lifecycle callbacks, or any other override. The class must define **no** `placeOrder`/`cancelOrder`/`reqGlobalCancel` before or after. |
| `ibkr/bridge.py` | edit | Delete `order_status`, `open_order`, `exec_details` and their two comment blocks. **Do NOT touch** `error_msg`, the news-boundary signals (`tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article` — D45 `S35`), or any other signal. |

#### Wave 3 — `P5-T03` (Group 3: module + data-model twin) (P5)

| File | Action | Precise change (resolve by symbol, never by line) |
|---|---|---|
| `ibkr/orders.py` | **delete** | whole file (140 L: `UserOrder`, `Orders` + four builders + five registry methods, the `orders` singleton). Nothing replaces it. |
| `data/models.py` | edit | Delete the `UserOrder` dataclass (`:104`–`:116`) **only**. **Do NOT touch** `Bar`/`Alarm`/`Study`/`Drawing`/`DrawingGroup`/`Position`/`TradeGroup`, the `dataclass`/`field` imports, or `stop_loss`/`take_profit` (they are wave 7's). |
| `tests/test_order_builders.py` | **delete** | whole file (17 cases — all for zero-caller builders and a never-populated registry). |
| `tests/test_ui_smoke.py` | edit | Drop `assert hasattr(data.models, "UserOrder")` (`:48`). **Keep** the `Position`/`Drawing` assertions and every import. |

*The guard is **not** touched in this wave — its token migration is wave 8 (invariant I-1).*

#### Wave 4 — `P5-T04` (Group 4: pacing + notional cap) (P5)

| File | Action | Precise change |
|---|---|---|
| `ibkr/pacing.py` | edit | Delete `class OrderRateLimiter` (`:128`–`:170`) and `order_limiter = OrderRateLimiter()` (`:172`); the `# Global singletons` comment becomes `# Global singleton`. **Do NOT touch** `PacingExceeded`, `PacingManager` (incl. `throttle`/`reset_for_tests`), `pacing_manager`, or any budget constant. |
| `config/settings.py` | edit | Delete `MAX_ORDER_NOTIONAL` and its two-line `validate_order()` comment (`:37`–`:39`). **Do NOT touch** any other constant. |
| `tests/conftest.py` | edit | Delete the two `pacing_mod.order_limiter.reset_for_tests()` lines (`:143`, `:146`) and the fixture docstring's "and a full order-token bucket (D28.1)" clause. **Keep** both `pacing_manager` resets. |
| `tests/test_d28_pacing.py` | edit | Drop `OrderRateLimiter` from the import (`:14`) and delete `test_order_limiter_allows_burst_then_denies` (`:97`–`:101`); rewrite the module docstring's "Orders use their own token-bucket limiter, never the realtime throttle." sentence. **Keep** every pacing case. |

#### Wave 5 — `P5-T05` (Group 5: order-fill sound) (P5)

| File | Action | Precise change |
|---|---|---|
| `services/sound_service.py` | edit | Delete the module-docstring bullet (`:9`), `BLIP_DURATION` (`:22`), `render_fill_blip` (`:75`–`:83`), `blip_path`/`order_fill.wav` and the `"fill"` entry (`:118`, `:121`–`:123`), `_fill_effect` (`:135`) and `play_fill` (`:170`–`:175`). **Collapse `_effect` to alarm-only** (`:148`–`:158`): `def _effect(self):` → returns/creates `self._alarm_effect` from `self._paths_or_create()["alarm"]`; `play_alarm` calls `self._effect()`. **This is not cosmetic** — the current ternary contains the **string constant** `"_fill_effect"`, which the AST scan sees, so leaving it keeps the guard red on a member this wave deletes. **Do NOT touch** `render_alarm_chime`, `ALARM_DURATION`, `_time_axis`/`_sine`/`_triangle`/`_decay_envelope`/`_normalize`/`to_pcm16`/`write_wav`/`default_sound_dir`, `warm`, or `set_enabled`. |
| `tests/test_sound_service.py` | edit | Drop `BLIP_DURATION`/`render_fill_blip` from the import (`:9`, `:15`); delete `class TestFillBlip` (2 cases, `:43`–`:51`); switch `test_write_wav_is_valid_pcm16` (`:57`) to `render_alarm_chime()`; delete the `paths["fill"]` assertion (`:76`) and rename `test_creates_both_files_once` for what it asserts. **9 cases → 7** (executed: `pytest --collect-only` reports 9 today; only `TestFillBlip`'s 2 cases go). |

#### Wave 6 — `P5-T06` (Group 6: `IdManager.reserve`) (P5)

| File | Action | Precise change |
|---|---|---|
| `ibkr/id_manager.py` | edit | Delete `IdManager.reserve` (`:19`–`:30`) **and its D26.2 docstring**. **Do NOT touch** `__init__`, `set_next_valid_id`, `get_id`, or the `id_manager` singleton — six `get_id()` callers depend on the module. |
| `tests/test_id_manager.py` | edit | Delete the four pure `reserve` cases (`:10`, `:18`, `:32`, `:56`); **rewrite** `test_set_next_valid_id_still_monotonic_with_reserve` without `reserve`, renamed `test_set_next_valid_id_still_monotonic` (`:39`–`:46`); **rewrite** `test_concurrent_allocations_never_duplicate` — drop the `reserve(3)` block (`:85`–`:86`) and change `8 * 203` to `8 * 200` (`:97`); rewrite the module docstring's bracket-order sentence (`:3`–`:4`). **8 cases → 4.** |

#### Wave 7 — `P5-T07` (Group 7: stop/target storage — schema **and** every reader) (P5)

| File | Action | Precise change |
|---|---|---|
| `data/db.py` | edit | (a) Remove `stop_loss REAL,` / `take_profit REAL,` from **both** `CREATE TABLE IF NOT EXISTS` blocks (`positions` `:120`–`:121`, `trade_groups` `:130`–`:131`). (b) In `_migrate_schema()`, **immediately after** the `CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_symbol_con_id` statement, add the guarded drop (`S47`): for each table in `("positions", "trade_groups")`, read `_table_columns(table)` **once** and `ALTER TABLE <t> DROP COLUMN <col>` for `stop_loss`/`take_profit` when present, with a comment naming D46/A99 and the four preserved things (rows, the unique index, the FK, `sqlite_sequence`). **Do NOT touch** any other table, index, migration or `_table_columns` itself. |
| `data/models.py` | edit | Delete `Position.stop_loss`/`take_profit` (`:86`–`:87`) and `TradeGroup.stop_loss`/`take_profit` (`:98`–`:99`). Nothing else. |
| `ibkr/account.py` | edit | Delete `Position.stop_loss`/`take_profit` (`:32`–`:33`), `build_position_from_ib`'s two parameters (`:64`–`:65`) and its two kwargs (`:79`–`:80`); reword the `Position.id` comment (`:40`–`:43`) to justify `id` by strategy grouping only. **`ESC-062`.** |
| `ui/main_window.py` | edit | (a) Delete `stop_loss=None, take_profit=None` and the D27.5 comment above them (`:3090`–`:3094`). (b) The `columns` tuple (`:3131`–`:3135`) loses the two names. (c) Read the bulk-load rows **by name**: use a dedicated cursor with `row_factory = sqlite3.Row` for both branches and build `Position(id=row["id"], … trade_group_id=row["trade_group_id"])` — **`trade_group_id` moves from `row[14]` to `row[12]`** and positional reading must not be kept (`S48`, DG85). (d) `_upsert_position` (`:3183`–`:3220`): drop the two column names, the two placeholders (15 → 13), the two `DO UPDATE SET` lines and the two values. (e) Reword the two `ESC-062` comments (`:3101`–`:3104`, `:3128`–`:3130`) so they justify `id` by strategy grouping and name the `—` render as the consequence of a missing id; and rewrite the `:3065` comment ("…the exact mirror of the D28.6 inverse on the **close-order path** (see below)") so it no longer cites a path D45 deleted — requirements DELETE row 22's third site, which no other wave owns. |
| `tests/test_d27_position_id.py`, `tests/test_d27_account_partial_window.py`, `tests/test_d27_account_scoping.py` | edit | The three raw `INSERT INTO positions` seeders lose the two column names, **two** placeholders and the two `None` values each (11 names / 11 `?` / 11 values → 9 / 9 / 9) (`test_d27_position_id` `:97`–`:103`; the other two `:66`–`:72`). **`test_d27_position_id` gains one case**: seed a row with a **non-null `trade_group_id`** (insert a `trade_groups` row first), drive `_on_position_end`, and assert the loaded `Position.trade_group_id` equals the seeded value — **the only guard against the silent index shift** (`S48`). |
| `tests/test_account.py`, `tests/test_strategy_detection.py` | edit | Four `build_position_from_ib` calls lose the two kwargs (`:36`–`:37`, `:62`–`:63`, `:85`–`:86`, `:103`–`:104`) and the two asserts go (`:108`–`:109`); `_pos()` loses its two `Position(...)` kwargs (`:30`–`:31`). |
| `tests/test_stop_loss_target.py` | **delete** | whole file (3 cases; its subject is the four model fields). |

#### Wave 8 — `P5-T08` (Group 8: the instrument — one coherent edit) (P5)

| File | Action | Precise change |
|---|---|---|
| `tests/test_d45_removal.py` | edit | (a) Remove the **ten** names from `_SURVIVORS` (`order_registry`, `orders`, `UserOrder`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`, `order_limiter`, `MAX_ORDER_NOTIONAL`) — **exactly ten; `classify_error`, `pacing_manager`, `PacingExceeded` and the dividend/news names stay** → **26 → 16**. (b) Add the **27** new tokens to `_FORBIDDEN` (**53 → 80**): `ibkr.orders`, `order_registry`, `orders`, `Orders`, `UserOrder`, the four builder names, the five window members, `order_status`, `open_order`, `exec_details`, `OrderRateLimiter`, `order_limiter`, `MAX_ORDER_NOTIONAL`, `render_fill_blip`, `BLIP_DURATION`, `play_fill`, `_fill_effect`, `order_fill`, `stop_loss`, `take_profit`. **`orders` and `Orders` are exact-matched** (whole identifier / whole string constant in the AST half, delimited word in the twin) — **never** `token in parts` in the AST half; the other **78** are substring. **`reserve` is NOT added** (measured 13 units / 11 files, all "preserve(s/d)") — it is asserted by `hasattr` in (d). (c) `_DELETED_MODULES` += `ibkr.orders`; `_DELETED_SUITES` += `tests/test_order_builders.py` and `tests/test_stop_loss_target.py`. (d) **One new end-state test** asserting: `hasattr(MainWindow, m) is False` for the five members; `hasattr(IBBridge, s) is False` for the three signals; **`name not in IBApiClient.__dict__`** for `orderStatus`/`openOrder`/`execDetails` (**never** `hasattr`); `find_spec("ibkr.orders") is None`; `ibkr/orders.py`, `tests/test_order_builders.py`, `tests/test_stop_loss_target.py` absent; `hasattr(data.models, "UserOrder") is False`; `"stop_loss" not in Position.__dataclass_fields__` for `data.models.Position`, `TradeGroup` **and** `ibkr.account.Position`, and neither name in `inspect.signature(build_position_from_ib).parameters`; `hasattr(IdManager, "reserve") is False` **and** `get_id`/`set_next_valid_id` present; `OrderRateLimiter`/`order_limiter` absent from `ibkr.pacing` while `pacing_manager` present; `MAX_ORDER_NOTIONAL` absent from `config.settings`; the fill names absent from `services.sound_service` while `play_alarm`/`render_alarm_chime` present and `ensure_sound_files()` returns exactly `{"alarm": …}`; **and the schema end state** on a fresh DB *and* a pre-seeded legacy fixture (drop applied, row counts equal, `sqlite_master` still lists `idx_positions_symbol_con_id`, `PRAGMA foreign_key_list(positions)` still reports the FK, a second `DB()` is a no-op). (e) **Correct the guard's own book** — the module docstring's "**five** deleted modules and **five** deleted suites", the `_DELETED_MODULES`/`_DELETED_SUITES` comments, the `_FORBIDDEN` header, the `_SURVIVORS` footnote and its `# A90's inert observers + S29's retained module` comment, and `_MIN_SUBSTRING`'s rationale. **Prose only** in (e). |

#### Wave 9 — `P5-T09` (Group 9: the surviving prose) (P5)

| File | Action | Precise change |
|---|---|---|
| `ibkr/error_codes.py` | edit | **Comment text only**, inside `classify_error`'s 202 clause: replace "…`_on_error` still routes it to the registry as Cancelled." with the post-P5 truth — a cancellation is a normal lifecycle event, `warning` (not `info`) so `IBApiClient.error` still emits it, and `_on_error` shows the generic status-bar line. **No code, no threshold, no return value changes** (`S46`). |
| `usage.md` | edit | (a) Drop `tests/test_order_builders.py` from the "Phase 10 core logic tests" pytest command (`:167`). (b) Rewrite the Database bullet (`:154`): the SL/TP columns are **dropped by a one-time migration on first open**; nothing is settable, displayed or retained; a pre-D46 database keeps every row and loses only those two values. |
| `USAGE.txt` | edit | Rewrite the stop/target bullet (`:88`–`:90`): the columns are **dropped** the first time this version opens the database; the app no longer stores a stop or a target at all. Keep the surrounding sentences (the app places/cancels/closes nothing; IBKR rejections appear in the status bar with TWS's message) **verbatim** — they already state the post-P5 end state. |
| `tests/test_dock_d18_region.py` | edit | Rename `test_T48_T03_panel_present_and_signals_wired` for what it now asserts; correct its "even though MainWindow consumes their effect via other slots" comment (`positions_changed`/`account_summary_changed` have **zero** receivers) and `_receiver_count`'s docstring's `>= 1` caller sentence. **`ESC-062` item 5.** No assertion changes. |

#### Wave 10 — `P5-T10` (Group 10: the batch gate) (P5)

| Target | Action | Precise change |
|---|---|---|
| everything | **verify** | (a) Full offscreen suite green. (b) The residue sweep over the full forbidden list (D45's + P5's 27), with the survivor allow-list beside it. (c) `AC-D46.3` reproduced **per code** (201, 103, 202) with `classify_error` and the 8000 ms line unchanged. (d) Import/launch probe: `python -c "import ui.main_window, data.models"`, an app start under `QT_QPA_PLATFORM=offscreen`, and `python -c "import ibkr.orders"` raising `ModuleNotFoundError`. (e) **The migration reproduced on a pre-P5 fixture** with `DB_PATH` exported to a temp file (memory 2026-10-15, ESC-043): row counts before/after, `sqlite_master`, `foreign_key_list`, a second open. (f) Confirm **no** `placeOrder`/`cancelOrder`/`reqGlobalCancel` call site and no new order/cancel/protection UI. (g) The **doc-trail grep** (`kept` / `no migration` / `retained` near the stop/target tokens over the six files). (h) Record the migrated guard's **pre-P5** failure set (§ *Tests* — evidence of discrimination). |

*`docs/codebase-map.md` is **Plan-owned**, refreshed in this phase — it is **not** a Build task.*

---

### Tests — deleted, adjusted, kept, and why each still means something (P5)

**The book: 2 deleted / 13 adjusted / 0 added.** No new test module and no new dependency (A95/A104/`S44`).

#### Deleted — two whole files (P5)

| File | Subject that no longer exists | Coverage consequence (stated, not hidden) |
|---|---|---|
| `tests/test_order_builders.py` (200 L, **17 cases**, `grep -c "^def test_"`) | the four zero-caller builders and the never-populated registry | order construction has **no** subject left, so there is nothing untested — that is the point (R80), not a gap |
| `tests/test_stop_loss_target.py` (**3 cases**) | the four model fields (`Position`/`TradeGroup` `stop_loss`/`take_profit`) | storage has **no** subject left; the *replacement* meaning is the guard's schema end-state assertions (wave 8) |

#### Adjusted — thirteen files, each with the exact invalidated assertion (P5)

| File | Invalidated assertion | Adjustment | Why it is invalidated |
|---|---|---|---|
| `tests/test_order_rejections.py` | the two registry cases (`_register` + `reg.get(oid).status`), `test_non_order_error_untouched` (asserts "the registry is untouched"), the `ibkr.orders` import, `_fresh_registry` (monkeypatches `ui.main_window.order_registry`), the docstring naming `_on_order_error` | delete both registry cases + both helpers + the import; repoint **and rename** the third at the generic line; **add** the parametrised 201/103/202 case; keep both `classify_error` cases → **3 of the original 5 survive** | the registry dies in **wave 1** (same wave); `classify_error` is **not** order-specific, and `AC-D46.3` needs a **positive per-code** proof |
| `tests/test_d45_removal.py` | the walkthrough's `win._on_order_error(1, 201, …)` (`:523`) and docstring bullet (`:22`); the ten names in `_SURVIVORS`; the absence of any end-state assertion; the guard's own retention-era prose | wave 1: repoint call + bullet. wave 8: `_SURVIVORS` −10, `_FORBIDDEN` +27, two `_DELETED_*` entries, the end-state test, the prose | the handler it calls dies in wave 1; the names die in waves 1–6; an instrument that keeps allow-listing what the batch deleted lets a resurrection pass |
| `tests/test_ui_smoke.py` | `assert hasattr(data.models, "UserOrder")` (`:48`) | drop that line | class deleted in the **same** wave (R81/A96) |
| `tests/test_account.py` | four `build_position_from_ib(..., stop_loss=None, take_profit=None)` calls + `assert pos.stop_loss is None` / `assert pos.take_profit is None` (`:36`–`:37`, `:62`–`:63`, `:85`–`:86`, `:103`–`:104`, `:108`–`:109`) | drop the eight kwargs and the two asserts | the factory parameters are gone (wave 7) |
| `tests/test_strategy_detection.py` | `_pos()`'s `stop_loss=`/`take_profit=` kwargs (`:30`–`:31`) | drop the two | the `Position` fields are gone (wave 7) |
| `tests/test_d27_position_id.py` | the seeder's `INSERT` names both columns (`:97`–`:103`) | drop the two names, **two** placeholders and the two `None` values (11 → 9 of each); **add** the non-null-`trade_group_id` case | `no such column` (loud) — and the added case covers the **silent** index shift |
| `tests/test_d27_account_partial_window.py` | the same seeder (`:66`–`:72`) | drop the two names, **two** placeholders and the two `None` values | `no such column` |
| `tests/test_d27_account_scoping.py` | the same seeder (`:66`–`:72`) | drop the two names, **two** placeholders and the two `None` values | `no such column` |
| `tests/conftest.py` | `pacing_mod.order_limiter.reset_for_tests()` (`:143`, `:146`) + the fixture docstring's order-bucket clause | drop both lines and the clause | `order_limiter` dies in the same wave |
| `tests/test_d28_pacing.py` | the `OrderRateLimiter` import (`:14`), `test_order_limiter_allows_burst_then_denies` (`:97`–`:101`), the docstring sentence | drop all three | the class is gone |
| `tests/test_sound_service.py` | `BLIP_DURATION`/`render_fill_blip` imports (`:9`, `:15`), `TestFillBlip` (`:43`–`:51`), the `render_fill_blip()` use (`:57`), **`paths["fill"]` (`:76`)** | drop the imports, the class and the assertion; repoint `:57` at `render_alarm_chime()`; rename the "both files" case → **9 cases → 7** | `ImportError`, then a **`KeyError`** once the `"fill"` key goes (`:76` is **not** in the register's book — Flagged Issue 2) |
| `tests/test_id_manager.py` | four pure `reserve` cases (`:10`, `:18`, `:32`, `:56`); `test_set_next_valid_id_still_monotonic_with_reserve` (`:39`); **`test_concurrent_allocations_never_duplicate` (`:74`, calls `reserve(3)` at `:85`)** | delete four; **rewrite two**; fix the module docstring → **8 cases → 4** | `AttributeError: 'IdManager' object has no attribute 'reserve'` — the concurrent case is **not** "kept" (Flagged Issue 1) |
| `tests/test_dock_d18_region.py` | none — the **name** and two comments are stale (`ESC-062` item 5) | rename the test, correct the two docstrings | prose drift, not a behaviour change |

#### Kept by decision — verified individually, not assumed (P5)

| File | Decision | Verification performed | Why it still means something |
|---|---|---|---|
| `tests/test_d40_tws_lifecycle.py` | keep unchanged | drives the badge/pause/resume and the D40.1 `502` suppression through `IBApiClient.error`, and `nextValidId` as the CONNECT event | P5 freezes that path (`S46`); it is the guard for the owner's error visibility **and** for `nextValidId` surviving |
| `tests/test_port_guard.py` | keep unchanged | asserts the fail-fast live-port check | untouched by P5 |
| `tests/test_d41_removal.py` | keep unchanged | its allow-list (`queue_depth`, `footprint_cache_key`) contains no order token | it still guards D41's removals, which P5 does not restore |
| `tests/test_db_schema.py` | keep unchanged | fresh-DB table set + `_init_schema` defined once | still true after the DDL edit; the **migration** assertions live in the guard (wave 8), because `AC-D46.5`'s file list has no room for a new file here |
| every other suite | **untouched** | a `tests/`-wide grep found no other reference to any removed name, and the five new ones (`OrderRateLimiter`, `MAX_ORDER_NOTIONAL`, `play_fill`, `render_fill_blip`, `reserve`) appear only in the files listed above | the remaining ~125 suites build windows, charts, docks and pop-outs; the gate runs them all |

#### Added — nothing, and why (P5)

No new test module. The acceptance instrument is the **existing** `tests/test_d45_removal.py` (architecture
`S44`): one AST scan over `ui/ services/ data/ ibkr/ config/` (identifiers **and** string constants), one
`ui/`-only raw-text twin, `find_spec`/`hasattr`/`__dict__`/`Path.exists()`/`_table_columns` checks, and the real
offscreen `MainWindow` walkthrough. A second module would duplicate those scans and create a second token list to
keep in sync — the same reasoning that keeps `tests/test_order_rejections.py` rather than renaming it.

**Evidence of discrimination (wave 8, recorded not assumed).** The ten names are *allow-listed* and every subject
still exists pre-P5, so migrating them is the discriminating change. **Counted on 2026-10-25 by running the migrated
`_scan_file`/`_matches` pair — with `_EXACT_ONLY = frozenset({"orders", "Orders"})` and the 27 new tokens — over the
working tree as it stands before wave 1:**

- **AST half:** **41** offences across **10** files — `ui/main_window.py` 14, `ibkr/orders.py` 7,
  `services/sound_service.py` 5, `data/models.py` 3, `ibkr/bridge.py` 3, `ibkr/client.py` 3, `ibkr/account.py` 2,
  `ibkr/pacing.py` 2, `data/db.py` 1, `config/settings.py` 1. **`ibkr/id_manager.py`: zero** (`orders` is
  exact-matched and its docstring is a whole string ≠ `orders`).
- **`ui`-only raw-text twin:** **40** hits, **all** in `ui/main_window.py` (`:36`, `:595`–`:597`, `:1546`–`:1551`,
  `:1559`, `:2951`–`:2965`, `:3093`–`:3094`, `:3133`–`:3134`, `:3164`–`:3165`, `:3186`, `:3198`–`:3199`,
  `:3216`–`:3217`, `:3226`–`:3227`) — every one on a line waves 1 or 7 deletes or edits.
- **Post-P5: both must be 0.** Verified by **executing the whole plan on a copy of the five source trees** (all ten
  groups' edits applied, including the `_effect` collapse): **0 AST offences, 0 twin hits.** Wave 10 re-runs both and
  records the numbers. Never claim a run that did not happen.

---

### Residue verification step (task-level, not a hope) (P5)

D46's correction record asks Build to grep after each file. This plan makes it a **named step in every wave** and
a **full pass in wave 10**, with the survivor allow-list beside it so "fix the residue" cannot be satisfied by
deleting something the requirement keeps.

**The instruments and their scope are unchanged from D45** (architecture `S44`): (1) **AST scan** — identifiers
**and** string constants over `ui/ services/ data/ ibkr/ config/`; comments are invisible to it; (2) **grep twin** —
`ui/` only, raw text (the prose net); (3) **`tests/` is covered by neither**, which is why the end state is
asserted **directly** in `tests/test_d45_removal.py` (wave 8).

**Forbidden after P5 — added to D45's list** (grep over `ui/`, AST over the five source dirs):

`ibkr.orders` · `order_registry` · `orders` *(exact-matched)* · `UserOrder` · `Orders` *(exact-matched)* ·
`market_order` · `limit_order` · `stop_order` · `bracket_order` · `_on_open_order` · `_on_order_status` ·
`_on_exec_details` · `_update_order_status` · `_on_order_error` · `order_status` · `open_order` · `exec_details` ·
`OrderRateLimiter` · `order_limiter` · `MAX_ORDER_NOTIONAL` · `render_fill_blip` · `BLIP_DURATION` · `play_fill` ·
`_fill_effect` · `order_fill` · `stop_loss` · `take_profit` — **27 new tokens**, `_FORBIDDEN` **53 → 80**.

*Counted 2026-10-25 by **executing** the migrated instrument (unit-level: identifiers ∪ string constants, per file):
**41 AST offences across 10 files** — `ui/main_window.py` 14, `ibkr/orders.py` 7, `services/sound_service.py` 5,
`data/models.py` 3, `ibkr/bridge.py` 3, `ibkr/client.py` 3, `ibkr/account.py` 2, `ibkr/pacing.py` 2,
`data/db.py` 1, `config/settings.py` 1 — and **40 twin hits, all `ui/main_window.py`**. **Every** offending unit
sits inside a region waves 1–7 delete or edit ⇒ **zero** post-P5 hits, confirmed by applying the plan to a copy of
the five source trees and re-running both nets (**0 / 0**). Three consequences worth stating rather than
discovering: `orders` is exact-matched, so `ibkr/id_manager.py` scores **0** even before `reserve` goes; the two
`stop_loss`/`take_profit` hits in `data/db.py` are inside the **`schema` string constant**, which is why they must
be substring tokens (whole-unit matching cannot see a column inside a SQL list); and `orders`' 5 **substring** units include
`_orders`, which only substring matching would catch — it is deleted with the module, so exact matching loses
nothing real.*

**The two exact-matched tokens (recorded, not a loophole — and the reason is now different).** `orders` and
`Orders` are exact-matched. **Revision 1's justification is void:** it existed because `ibkr/pacing.py:131`'s
`OrderRateLimiter` docstring and `ibkr/id_manager.py:22`'s `reserve` docstring sat in "files no task may edit", and
**this phase deletes both docstrings** (waves 4 and 6). The set survives on a *different*, stated ground:

- **Measured today:** `orders` appears on **5 scanned units**, `Orders` on **2**, and **every one** is inside a file
  this phase deletes (`ibkr/orders`' class, singleton, `_orders` and docstring; `pacing.py`'s class docstring;
  `id_manager.py`'s `reserve` docstring; `ui/main_window.py:36`'s alias). So a substring rule would also be **green**
  post-P5 — exact matching is therefore **not** required for greenness.
- **What it buys:** `orders`/`Orders` are ordinary English words that legitimate explanatory prose can contain
  (a future comment reading "the app places no orders" is not residue). Exact matching keeps the instrument's signal
  about **identifiers** — a `class Orders:` definition, an `Orders()` call, `import … as orders`, an `orders.`
  attribute — and all four are recorded by the AST, so nothing real is lost. **`AC-D46.1`'s `Orders(` spelling is
  covered by that identifier match.**
- **`token in parts` remains the wrong AST implementation** (`_SPLIT.split("Orders were throttled…")` yields
  `"Orders"` as a part) — but the branch must compare the **whole unit** (`name == token`), and only the raw-text
  `ui` twin uses a delimited word.

**Mechanism (exact, because the obvious shortcut is wrong).** One dedicated `_EXACT_ONLY = frozenset({"orders",
"Orders"})`, tested **before** the substring branch. **`reserve` is NOT a token**: measured at **13 units across 11
files** — `ibkr/id_manager.py`'s own two, **ten** docstring occurrences of the English word "preserve(s/d)", and
`ui/chart_panel.py`'s `_reserve_price_tag_lane` — a substring
rule would put the instrument red on `ui/chart_mouse_router.py`, `ui/dock_layout.py`, `services/time_collapse_service.py`
and seven more files the phase keeps. It is covered by **`hasattr(IdManager, "reserve") is False`** (`AC-D46.10`'s own
measurable), and the per-wave **grep** may use `reserve(` (with the paren), which is measured clean (2 lines, both in
`id_manager.py`, both deleted).

**The three override names are not tokens at all.** `orderStatus` / `openOrder` / `execDetails` are `ibapi`'s own
API names; a list over *this repo's* symbols cannot forbid them without also forbidding the inherited base. They are
covered by **`"orderStatus" not in IBApiClient.__dict__`** (and the other two) — **not** `hasattr`, which the
inherited `EWrapper` no-ops keep `True` before *and* after the deletion (`AP-D46-14`).

**Survivors — MUST NOT be reported as residue (they are the requirement's deliberate end state):**

| Survivor | Where | Why it stays |
|---|---|---|
| `classify_error`, `_on_error`, `error_msg`, `severity`, `IBApiClient.error` | `ibkr/error_codes.py`, `ibkr/client.py`, `ibkr/bridge.py`, `ui/main_window.py` | the owner's **error visibility** (`AC-D46.3`, `S46`) — 201/103/202 reach the status bar through exactly these |
| `order_limiter`, `pacing_manager`, `PacingExceeded`, `MAX_ORDER_NOTIONAL`, `reserve` (+ the "multi-leg orders" docstring) | `ibkr/pacing.py`, `config/settings.py`, `ibkr/id_manager.py` | **NO LONGER SURVIVORS — all four are tasks** (`D46.10`/`D46.11`, waves 4 and 6). This row is kept only so a reader of revision 1 sees the reversal: `order_limiter` and `MAX_ORDER_NOTIONAL` are **forbidden** tokens, and `reserve` is asserted by `hasattr` |
| `pacing_manager`, `PacingExceeded`, `PacingManager`, `IdManager`, `get_id`, `set_next_valid_id`, `id_manager` | `ibkr/pacing.py`, `ibkr/id_manager.py` | shared substrate with named consumers: realtime/historical pacing and **six** `get_id()` call sites (`ui/main_window.py:1095`, `ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`) — frozen (`S46`) |
| `nextValidId`, `set_next_valid_id` | `ibkr/client.py`, `ibkr/id_manager.py` | the **CONNECTED** transition and the reconnect reset — driven by `tests/test_d40_tws_lifecycle.py` and `tests/test_d25_alarm_monitor.py` (A102/DG82) |
| `order_blocks`, `_render_order_blocks`, `orderBlocks` | `services/ict_service.py`, `ui/overlays/ict_overlay.py` | ICT price structure, not trading orders (R83) |
| `sort_order` | `data/db.py`, `ui/watchlist_panel.py` | watchlist sequencing (R83) |
| `advancedOrderRejectJson` | `ibkr/client.py` | the IB 5-arg `error` signature, not app code (DG83) |
| `play_alarm`, `render_alarm_chime`, `"alarm"` | `services/sound_service.py` | the D21 alarm chime — the half of the file this phase **keeps** (`AC-D46.11`) |
| `Position`, `TradeGroup`, `trade_group_id`, `positions` | `data/models.py`, `data/db.py`, `ui/active_portfolio_panel.py` | the view-only Portfolio and the strategy grouping — which is `services.strategy_detection` over `Position.id`, **not** `trade_groups`; **`TradeGroup`/`trade_groups`/`position_group_map` are dead storage (zero readers, zero writers) retained only to avoid widening the batch** (audit R10 correction — they are *not* a display consumer); only the four stop/target fields go (`A99`) |
| `"456"`, tick `59`, `_dividend_info`, `dividend_updated`, `dividend_info`, `_merge_*`, `parse_ib_dividend_string` | `ui/ticker_session.py`, `data/events/` | the chart's dividend markers (`AC-D45.2`, R68) — untouched by P5 |
| `tick_news`, `news_providers`, `historical_news`, `historical_news_end`, `news_article` | `ibkr/bridge.py`, `ibkr/client.py` | the ibapi boundary mirrors D45 kept unconnected (`S35`) |
| `queue_depth`, `footprint_cache_key` | `tests/test_d41_removal.py` | D41's documented allow-list strings; the file is not edited |
| `_symbol_last_prices` | `ui/main_window.py` | feeds the Portfolio P/L path — **not** order state |

**Per-wave command shape** (Build runs it after each edited file and once per wave): the forbidden-token grep
over `ui/` + the AST scan via the guard module (**final** token list, from wave 1 onward — I-1); a file-existence
check (`ibkr/orders.py` present until wave 3, absent after; `tests/test_stop_loss_target.py` present until wave 7);
`python -c "import ui.main_window"`; for wave 2 a `grep -n "order_status\|open_order\|exec_details" ibkr/bridge.py ibkr/client.py` that must be empty; for waves 4–6 a `grep -n "OrderRateLimiter\|order_limiter\|MAX_ORDER_NOTIONAL\|play_fill\|render_fill_blip\|reserve(" ` over the touched files that must be empty; and for wave 7 `grep -n "stop_loss\|take_profit"` over the touched files plus a `PRAGMA table_info` check on a scratch DB.

---

### Assumptions (P5)

| # | Assumption | Rationale |
|---|---|---|
| **AP-D46-1** | **The wave order is consumer → boundary → module (waves 1–3)**, not the register's group order. | Group (1) "module deletion + importer cleanup" cannot be a standalone wave: removing the import while `_on_error` still reads `order_registry` turns every non-session TWS error into a `NameError`, and deleting the file with the import present breaks collection. The register's **member groups** are preserved; only their order is forced (`S43`, architecture supersession item 9). |
| **AP-D46-2** | Wave 1 deletes **all** window-side order members at once (3 connects, 3 slots, `_update_order_status`, `_on_order_error`, the `_on_error` branch + comment, the import) — even though only the connects/slots are "Group 1" in the register's naming. | They form one reference cluster: each is reachable only from another member of the cluster or from a live TWS callback, so splitting them across waves is exactly the silent-path risk. The import must fall with its last reader, not later. |
| **AP-D46-3** | `_on_order_error`'s three mappings go with it and **nothing** replaces them (A93). No order id, no verdict, no 12 s duration. | They never executed (the registry was empty), so the owner already sees the generic line; re-implementing them would invent order identity the app does not have (`S41`). |
| **AP-D46-4** | `tests/test_order_rejections.py` ends with **3 surviving originals + 1 new parametrised case (3 params)**; the "3 of 5" in `AC-D46.5`/A95 counts **surviving originals** and does not forbid `AC-D46.3`'s proof. | `AC-D46.3` requires a **positive per-code** assertion for 201, 103 and 202 ("not an absence test"); one unparametrised 2105 case cannot satisfy it, and the book forbids a new file, so the proof belongs in this file. |
| **AP-D46-5** | `test_non_order_error_untouched` is **renamed** to `test_non_order_error_shows_generic_line`. | Its old name means "the registry was not touched"; there is no registry. Keeping the name would be the prose-drift class `ESC-062` already records. The ACs name files and survivor counts, not case names. |
| **AP-D46-6** *(revised in revision 2)* | `tests/test_d45_removal.py` receives **two** edits across **two** waves — wave 1 (the walkthrough call + the docstring bullet) and wave **8** (the token migration, the absence pools, the end-state test and the guard's own book). | The walkthrough calls `_on_order_error` (`:523`) and the docstring lists it (`:22`); both reference a name wave 1 deletes, so they must move with it. Everything else moves to wave 8 under **I-1**, because the ten names die across waves 1–6 and the storage in wave 7 — staging the token list would re-edit the instrument four times. || **AP-D46-7** *(revised twice — `RC-1`, then revision 2)* | In the guard, every P5 token is a **substring** token **except** the bare singleton `orders` **and** `Orders`, which are **exact-matched**: in the AST half `name == token` (one identifier, or one whole string constant), in the raw-text `ui` twin a delimited word. One dedicated branch, checked **before** the substring loop. **`stop_loss`/`take_profit` are substring tokens** — the SQL column list that reintroduces them is one whole string constant, which whole-unit matching cannot see. | **Revision 1's reason is void:** it protected two docstrings in "files no task may edit" (`id_manager.py::reserve`, `pacing.py:131`) — **both deleted this phase** (waves 6 and 4). Measured today (executed): `orders` = **5 substring units / 2 exact units**, `Orders` = **2 substring units / 1 exact unit**, every one inside a file this phase deletes, so a substring rule would also be green post-P5. The set is kept because these are ordinary English words that legitimate prose can contain, while exact matching still catches every real re-introduction (class name, call site, alias, attribute — the AST records all four). `token in parts` is **not** an acceptable AST implementation (it splits a docstring into words). |
| **AP-D46-8** | `ibkr/error_codes.py` gets a **comment-only** edit; `classify_error`'s code is frozen. | `AC-D46.6` asks the comment to stop claiming a registry route; the function gates **every** TWS error and must not be "tidied" (A97, `S46`). |
| **AP-D46-9** *(corrected in revision 2)* | `usage.md` loses the deleted test file from its pytest example **and** its Database bullet is rewritten; `USAGE.txt`'s **stop/target bullet is rewritten too** (kept → **dropped**), while its status-bar sentence stays verbatim. | A98's "no user-facing doc change expected" was **incomplete**: the grep finds `usage.md:167` naming a deleted suite, and both files still say the columns are *kept* — which `D46.13` forbids. Wave 9 corrects all three sites; the parts that already state the end state (places/cancels/closes nothing; TWS message on the status bar) are left untouched. |
| **AP-D46-10** | `data/models.py` loses only the `UserOrder` class; `dataclass`/`field` stay. | `Study` uses `field(default_factory=dict)` (`:37`), so the imports are live after the deletion. |
| **AP-D46-11** | `docs/codebase-map.md` is refreshed **by Plan in this phase**, not by Build; the generated skeleton stays script-owned and keeps listing `ibkr/orders.py` until the next refresh. | A98's Plan/Build split, and the same tooling property D45 recorded: the annotations describe the post-P5 target state and say so; the skeleton is rebuilt from the tree by `update_codebase_map.py`. |
| **AP-D46-12** *(corrected in revision 2)* | **No new test module, no new dependency** — but **one schema change and one migration** (`S47`). | A95 keeps the rejection file (renaming is churn). The "no schema change" half was revision 1's, written under A87; **A99 reverses A87** and the register now fixes the dropped end state, so the plan owes a mechanism. The migration lives in the guard (wave 8) rather than a new suite, because `AC-D46.5`'s file list has no room for one. |
| **AP-D46-16** *(added 2026-10-25 — revision 2)* | The guard's token migration lands **once**, in wave 8 — not staged per deleting wave (invariant **I-1**). | The ten names die across waves 1–6 and the storage in wave 7; staging would re-edit `_matches`/`_FORBIDDEN`/`_SURVIVORS` four times in the file where a mechanism error already cost a revision round. The allow-list cannot *hide* a resurrection in between, because the token is not in `_FORBIDDEN` yet either — the state is coherent at every boundary, not merely permitted. The interim net is the mandatory per-wave residue grep with the **final** token list. |
| **AP-D46-17** *(added 2026-10-25 — revision 2)* | `reserve` is **not** a guard token; `AC-D46.10`'s `hasattr(IdManager, "reserve") is False` is its instrument. | Measured: **13 units / 11 files** — `id_manager.py`'s own two, ten "preserve(s/d)" docstrings in files this phase keeps, and `ui/chart_panel.py`'s `_reserve_price_tag_lane`. A substring token would put the instrument red on `ui/chart_mouse_router.py`, `ui/dock_layout.py`, `services/time_collapse_service.py` and seven more. The per-wave grep may still use `reserve(` (measured clean: 2 lines, both in `ibkr/id_manager.py`, both deleted). |
| **AP-D46-18** *(added 2026-10-25 — revision 2)* | The migration's row-preservation and idempotence assertions live in `tests/test_d45_removal.py` (wave 8), **not** in a new file and **not** in `tests/test_db_schema.py`. | `AC-D46.5` says "no other test file changes"; `AC-D46.12`'s measurables must exist somewhere. The guard is the batch's instrument (`S44`) and already asserts end states; `test_db_schema.py` stays untouched. The legacy fixture uses `monkeypatch.setattr(paths, "_DB_FILENAME", …)` + `DB()`, the pattern `test_db_schema.py:65` already proves. |
| **AP-D46-19** *(added 2026-10-25 — revision 2)* | Wave 7 is **one task with eleven files**, not three tasks. | R84/DG85 require the schema and its readers to land together. Splitting production from its test book leaves the suite red between waves **and** separates the schema from its readers — the exact trap. Measured size: ~40 edited lines, four of the eleven files mechanical; well under the L-size deletion profile of R84. |
| **AP-D46-20** *(added 2026-10-25 — revision 2)* | `ESC-062` is folded into waves 1, 7 and 9; **no wave is created for it**. | Its four comment sites are in files this phase already edits (three in wave 7's `main_window`/`account`, one deleted with wave 1's branch), and its test rename is in a file no earlier wave touches (wave 9). Zero new tasks, zero new files. |
| **AP-D46-13** | The line numbers quoted in this section are **indicative**; symbols are the primary pointer (`DG56`, and `ui/main_window.py` drifts on every edit). | Verified against the working tree on 2026-10-25; each symbol was resolved by name. |
| **AP-D46-14** *(added 2026-10-25 — `RC-2`)* | `AC-D46.2`'s **client** half is measured as `"orderStatus" not in IBApiClient.__dict__` (and `openOrder`, `execDetails`), **not** `hasattr(IBApiClient, …) is False`. The window (`hasattr` on five members) and bridge (`hasattr(IBBridge, …)`) halves stand as written. | `IBApiClient.__mro__` is `(IBApiClient, EWrapper, EClient)` and `EWrapper.__dict__` defines all three as no-op stubs, so `hasattr` is `True` **before and after** the override is deleted — re-verified in `.venv` on 2026-10-25 (`in EWrapper.__dict__` True; `hasattr` True). The AC's literal measurable cannot pass on any correct build, so a Build worker would have to weaken it silently. `__dict__` membership is the pattern the guard already uses for the transmit names and measures the AC's actual property ("this repo defines no `EWrapper` **override**") **more** strongly; the criterion's substance is met, not weakened. Recorded as `RG-D46-2`; the AC wording is a requirements-side fix for the next revision, not an edit this phase may make. |
| **AP-D46-15** *(added 2026-10-25 — `RC-1.4`; wave renumbered in revision 2)* | Wave **8** also corrects the guard's **own book**, which today documents the D45 retention this phase forbids: module docstring `:5`, the `_DELETED_MODULES`/`_DELETED_SUITES` comments and the absence-test docstring (`:52`, `:61`, `:231`), the `_FORBIDDEN` header (`:70`), the `_SURVIVORS` footnote (`:132`) and comment (`:144`), and `_MIN_SUBSTRING`'s rationale (`:152`–`:156`). Prose only — no token, no assertion, no branch changes in that sub-step. | A guard whose footnotes say "the retained `ibkr/orders.py`" and "every other token is a distinctive identifier" while its forbidden set deletes both is the DG81 class of defect **inside the instrument**: the next reader trusts the comment over the code. It is one file already tasked in that wave, so no scope is added and no criterion changes. |

---

### Flagged Issues (P5)

**Six items are returned to the Validator rather than fixed here — each is a defect in the *requirements text*, and
none is blocking.** The plan satisfies every criterion as written **via the stated interpretation**, and the
requirements side should record the correction. **No requirement was narrowed or reinterpreted to fit a convenient
architecture.**

| # | Requirement affected | Why it cannot be satisfied as written | Plan's interpretation (recorded, not silent) | Suggested direction |
|---|---|---|---|---|
| **1** | **`AC-D46.10`** | It says the suite "keeps `test_get_id_allocates_sequentially`, `test_set_next_valid_id_equal_is_noop` **and `test_concurrent_allocations_never_duplicate`**". That last case **calls `mgr.reserve(3)`** (`tests/test_id_manager.py:85`) and asserts `len(seen) == 8 * 203` (`:97`) — deleting `reserve` makes it raise `AttributeError`. **Six** of the eight cases touch `reserve`, not five. | The count **8 → 4** still holds, but **two** cases are rewritten (the monotonic one *and* the concurrent one), not one. Wave 6 does that. | Amend `AC-D46.10`/`D46.10` to say "**keeps three, rewrites two**". |
| **2** | **`D46.5` / `A104`** (the test book) | It lists `tests/test_sound_service.py` as "`TestFillBlip` (2), the `render_fill_blip` use" — but **`TestEnsureSoundFiles::test_creates_both_files_once` asserts `paths["fill"]` (`:76`)** and dies with `KeyError` once the `"fill"` key goes. Three sites, not two. | Wave 5 fixes `:76` and renames the case; the file's outcome is **9 cases → 7** (the register's "8" was unexecuted; `--collect-only` says 9). | Add the `:76` site to the book. |
| **3** | **`D46.12`** (a factual citation) | It says "this env is SQLite **3.54.0**, so both are available". The app's interpreter is **`.venv/bin/python`**, which links **3.53.1**; 3.54.0 is the system `python3`. | Both support `DROP COLUMN` (≥ 3.35), so **no criterion fails**; `S47` cites the measured version. | Correct the version, or say "≥ 3.35". |
| **4** | **`D46.13` / `AC-D46.13`** (one-directional trail) | The criterion is a grep over six files, two of which contain the superseded sentences in **already-activated sections** — `docs/architecture.md` § D45 (`:4647`, `:4662`, `:4690`, `:4701`–`:4704`, `:4824`–`:4833`, `:4850`, `:4872`–`:4874`, `:4903`, `:5024`) and `docs/plan.md` § D45 (`:2004`–`:2005`, `:2085`, `:2188`–`:2189`, `:2251`, `:2337`, `:2350`, `:2397`, `:2422`–`:2423`). **Plan may not edit an activated section.** | This section states the dropped end state and enumerates those sites by line (§ *Document trail*); the Validator attaches the `SUPERSEDED BY D46 / A99` markers at activation — the mechanism it used for revision 1 (*Activation note 2*). | Validator: add the markers at activation. |
| **5** | **`AC-D46.2`** (`RG-D46-2`, already open in `docs/plan_notes.md`) | Its measurable `hasattr(IBApiClient, "orderStatus") is False` **cannot pass on any correct build**: `EWrapper` defines all three as no-op stubs, so `hasattr` is `True` before *and* after (re-verified in `.venv`). | The client half is measured by **`name not in IBApiClient.__dict__`** (`AP-D46-14`) — the AC's substance ("this repo defines no override") is met more strongly. | Amend the AC's measurable. |
| **6** | **`D46.9`'s "no order-named symbol outside the two sets"** vs the Build residue list | The residue list ends with **`reserve(`**, but `reserve` cannot be a guard token: measured **13 units across 11 files**, all but two being the English word "preserve(s/d)" in docstrings of files the phase keeps. | `reserve` is asserted by `hasattr(IdManager, "reserve") is False`; the per-wave **grep** keeps `reserve(` (with the paren), which is measured clean. | Note that `reserve(` is a grep-only pattern, not a token. |

**Recorded for the Validator's awareness — deliberately *not* escalated (each is a note, not a requirement
defect):**

1. **The register's Build split order is not executable as written** (its group (1) puts `ibkr/orders.py` first).
   Resolved by reordering, `AP-D46-1` + architecture supersession item 9. A Build *suggestion*, not a criterion.
2. **`AC-D46.5`/A95 under-describe `tests/test_d45_removal.py`'s adjustment** ("allow-list shrink" only; the
   truth is four sub-edits across two waves, two of them in wave 1 and the instrument's own prose + token migration in wave 8). The file
   is named and *adjusted*, so no clause fails — `AP-D46-6`/`AP-D46-15`. This is the same class as `RG-D45-2` (an
   AC's enumeration slightly narrower than the delivered book); a future requirements revision may append the
   detail.
3. **A95's claim that the repointed case "is exactly `AC-D46.3`'s positive proof" is imprecise** — a single
   unrelated-code case cannot prove 201/103/202. The criterion is satisfiable and is met by the added
   parametrised case (`AP-D46-4`); the assumption's parenthetical is what is under-specified.
4. **A98's "no user-facing doc change expected" was checked and found incomplete** — `usage.md`'s pytest example
   names `tests/test_order_builders.py`, which this phase deletes (`AP-D46-9`). One line is corrected; no
   requirement changes.
5. **`ESC-063` (open, routed PLAN) is resolved by this draft's map refresh** — "adjusts six" → **seven**, plus
   the missing "+1 added". **`ESC-061` is MOOT** (the module it asked to annotate is deleted); no task
   implements it and the Code Reviewer should close it as moot, not re-dispatch it.
6. **DG78 item (2) stays open by decision** — an orderId colliding with a live session reqId keeps taking the
   session path (pre-existing; A94). **No task may "fix" this**, and no test may pin the collision as desired
   behaviour. DG80 (`IdManager.reserve`) stays out of scope (A97).
7. **`ESC-060`'s behavioural half is MOOT and its documentation half is SUPERSEDED.** There is no column for a live
   update to clear — the columns are dropped (`A99`, wave 7) — and `USAGE.txt`/`usage.md` are corrected in wave 9 so
   the trail reads **kept → cleared → dropped**. No P5 document, comment or test may claim the columns or their
   values survive, and none may claim they are "kept".
8. **`ESC-062` item 4 is incidentally satisfied** — the `_on_error` comment naming "the ticket" is deleted with
   wave 1's branch. That is a side effect, **not** a claim to have resolved the escalation (items 1–3 and 5 are
   BUILD's).
9. **`docs/plan_notes.md`'s `RG-D46-1` and `RG-D46-2` are addressed here and neither is escalated.** `RG-D46-1`
   (the rejection file's final shape: 3 surviving originals **+** the added parametrised case) by
   `AP-D46-4`/`AP-D46-5`, unchanged; `RG-D46-2` (the unsatisfiable `hasattr` measurable) by `AP-D46-14`. No analyst
   decision is needed before build, and this phase does not edit `requirements.md`.
10. **The `Orders` false positive is resolved by design, not waived.** `AP-D46-7` (revised) records all **four**
   occurrences and the exact-match mechanism; `ibkr/pacing.py:131`'s docstring is **not** an offence and no task
   may edit that file. Recorded so a future reader does not re-raise it, and so nobody "fixes" it by editing
   `pacing.py` (out of scope, DG80).

---

### Document trail — kept → cleared → dropped (P5)

`D46.13`/`AC-D46.13` is a **grep** criterion, and its failure mode is two live claims side by side. The table below
is the full site list, with the owner of each edit.

**This plan's own half (written in this draft):** `docs/architecture.md` § P5 (the whole section states the dropped
end state, with `S47`'s mechanism and the three-age DB table) and this section; `docs/codebase-map.md` refreshed in
this draft (module rows, P5 book, survivor list).

**Build's half (wave 9):**

| File | Site | Currently says | Must read |
|---|---|---|---|
| `USAGE.txt` | `:88`–`:90` | "The database columns are kept, but an update from TWS writes them empty, so do not rely on the saved values surviving." | the columns are **dropped** the first time this version opens the database; the app stores no stop or target at all |
| `usage.md` | `:154` | "The stop-loss / take-profit (SL/TP) columns are kept (no migration), but they are no longer settable or shown in-app…" | the columns are **dropped by a one-time migration** on first open; every row is kept; only those two values are lost |
| `usage.md` | `:167` | the pytest example names `tests/test_order_builders.py` | that file is deleted in wave 3 |

**The Validator's half — already-activated sections this run may not edit.** Each carries a `kept`/`no migration`/
`retained` claim within three lines of a stop/target token, so `AC-D46.13`'s grep will hit it until the marker is
attached. Quoted by line so the Validator can act without re-deriving:

| File | Lines | The claim |
|---|---|---|
| `docs/architecture.md` § D45 | `:4647`, `:4662` (`S33`), `:4690`, `:4701`–`:4704`, `:4824`–`:4833`, `:4850`, `:4872`–`:4874`, `:4903`, `:5024` | "storage is **untouched** … no migration, no destructive schema change"; "a pre-D45 database opens unchanged with its legacy stop/target values" |
| `docs/plan.md` § D45 | `:2004`–`:2005`, `:2085`, `:2188`–`:2189`, `:2251`, `:2337`, `:2350`, `:2397`, `:2422`–`:2423` | "storage **kept**, no migration"; "kept unchanged"; "opens with its stored `stop_loss`/`take_profit` values intact … (no migration, no data loss)" |

**Not a site, and not an edit:** the historical D45 register rows keep their wording — `A87`, `A80`, `A90` and `A97`
each already carry an explicit `REVERSED`/`SUPERSEDED` note in `requirements.md` (the analyst's half, done), and the
readable sequence is exactly **kept (A87) → cleared (ESC-060) → dropped (A99/D46.12)**.

---

### Correction record — for Task Manager / Build / Code Reviewer (P5)

**Plan (this draft):** refreshed `docs/codebase-map.md` — the `ibkr/orders.py` "**NOT orphaned and must NOT be
deleted**" claim replaced by the post-P5 target; the "retained observers … do not clean up" block replaced by a
"removed by P5" block; the `ibkr/orders.py (docstring note only)` test-impact row replaced by P5 rows; the
pointer sentences moved off the superseded D45 proposal drafts onto the canonical `docs/plan.md` /
`docs/architecture.md`; the D45 book arithmetic corrected to **5 deleted / 7 adjusted / 1 added** (`ESC-063`);
the P5 touch summary and test-impact rows added. Superseded `S29`/`AR-D45-10`/`S35`'s order half in
`docs/architecture.md` § *Phase P5*, voided D45's frozen rows for the module and the observers, and recorded
`ESC-061` as moot.

**Task Manager:**
- Build **ten** tasks in the chain `P5-T01 → … → P5-T10`, with `touches_files` exactly as
  the per-file map says (`tests/test_d45_removal.py` in **1 and 8** — different line ranges, never concurrent;
  `ui/main_window.py` in **1 and 7**; `data/models.py` in **3 and 7**). No two tasks in one wave may share a file.
- **Enumerate the assertions invalidated outside the edited files** (memory 2026-10-23 item 4 / `ESC-055`) — this is
  the **thirteen-file** book in § *Tests*: `tests/test_d45_removal.py`, `test_ui_smoke.py`, `test_order_rejections.py`,
  `test_account.py`, `test_strategy_detection.py`, `test_d27_position_id.py`, `test_d27_account_partial_window.py`,
  `test_d27_account_scoping.py`, `conftest.py`, `test_d28_pacing.py`, `test_sound_service.py`, `test_id_manager.py`,
  `test_dock_d18_region.py`. **Two of them are not in the register's book** (Flagged Issues 1 and 2) — verify against
  the files, do not trust the register.
- **Do NOT task** `ibkr/id_manager.py`'s `get_id`/`set_next_valid_id`, `ibkr/pacing.py`'s `PacingManager`,
  `config/settings.py`'s other constants, `services/sound_service.py`'s **alarm** half, `USAGE.txt`'s status-bar
  sentence, `tests/test_d41_removal.py`, `tests/test_db_schema.py`, the ICT order blocks, `sort_order`, or the
  `nextValidId` transition. Do **not** task any error-path reordering (A94).
- Wave 7's acceptance includes **the index shift proven** (the seeded `trade_group_id` case) and the migration's
  **row/index/FK preservation + a no-op second open**.
- Wave 10's acceptance includes the **per-code** 201/103/202 reproduction and the recorded pre-P5 guard failure set.
- **Do not split an emitter from its signal.** Wave 2 is one task by construction; if the graph must be split for
  any reason, the split is forbidden — report it instead.

**Build:**
- Work **group by group**, and after each file run a syntax/import check **and** the group's residue grep (the
  D41 worker-death mitigation, memory 2026-10-15).
- **Never leave a wave with a name that is reachable but broken.** The dangerous direction is *deleting a
  consumer's target while the consumer survives* (`_update_order_status` → registry, `client` → signal,
  `_on_error` → `_on_order_error`): those raise only on a live TWS callback, so the suite cannot catch them.
  Delete the **consumer** first, in the same task, and re-run `python -c "import ui.main_window"`.
- **Do not add `pass` stubs, compat shims or renamed aliases** for any removed member. If a worker believes one is
  needed, it must stop and report — the requirement is absence, not inertness.
- Comments naming a removed member are prose; **docstrings or string constants naming one must be rewritten in the
  same wave** (`S44`) or the wave-5 scan fails. The raw-text `ui/` twin reads comments too, so a `ui/` comment
  spelling `order_registry`/`_on_order_error` is an offence.
- `git status` the file list before finishing a delete-only task: a "done" task that left a file half edited is
  the failure mode that killed three D41 workers.

**Code Reviewer (independent — do not trust the task book):**
- Confirm `ibkr/orders.py` is **absent**, `import ibkr.orders` raises `ModuleNotFoundError`, and **no** module
  under `ui/ services/ data/ ibkr/ config/ main.py` names it (R78).
- Confirm the chain is absent **by symbol and by the right check for each half**: five `MainWindow` members by
  `hasattr`, three `Bridge` signals by `hasattr(IBBridge, …)`, the three `IBApiClient` overrides by
  **`name not in IBApiClient.__dict__`** (`hasattr` is `True` through inheritance and proves nothing, `AP-D46-14`),
  and no `order_registry`/`_on_order_error` in `_on_error`'s source.
- Confirm `Orders` and `orders` are **exact-matched — not substring-matched** — in the guard, and that
  `ibkr/pacing.py:131` and `ibkr/id_manager.py:22` stay **green** while `ibkr/pacing.py` is otherwise untouched
  (`AP-D46-7`). A substring `Orders` token means the instrument is red on a file no task may edit.
- **Independently reproduce `AC-D46.3` for 201, 103 and 202** — call a real offscreen `MainWindow._on_error`
  per code with no matching session reqId and assert the status bar carries `[code]` **and** TWS's text; then
  assert `classify_error`'s table and the 8000 ms duration are unchanged. "The suite is green" is not evidence
  (R77).
- Confirm `data.models` has **no** `UserOrder` and the smoke module is green (R81).
- Confirm `docs/codebase-map.md` no longer claims the module is retained / "NOT … deleted" / "do not clean up",
  and that its D45 book reads **5 / 7 / 1** (`ESC-063`).
- Confirm the guard's **ten** names really moved from allow-list to **forbidden**, that `classify_error`, `pacing_manager` and `PacingExceeded` are still survivors, that the two exact-matched tokens are exact-matched, and that the new end-state test is not vacuous (it must fail on the pre-P5 tree — the recorded pre-P5 run is **41** AST offences over 10 files and **40** twin hits).
- Confirm **no** replacement order/cancel/protection surface exists, and that `USAGE.txt`/`usage.md` advertise
  nothing removed (the status-bar sentence must still be true).

---

### Incidentally affected (noted, not absorbed) (P5)

- **`ibkr/id_manager.py::reserve`** — order-motivated (D26.2) with tests only; **now a task** (wave 6, `D46.10`/A101).
  Its docstring's phrase "multi-leg orders" is *deleted with it*, which is why revision 1's exact-match justification
  for `orders` is void (`AP-D46-7`).
- **`ibkr/pacing.py::order_limiter`** and **`config/settings.py::MAX_ORDER_NOTIONAL`** — dead after D45; **now tasks**
  (wave 4, `D46.11`) and **forbidden** tokens.
- **`ibkr/pacing.py:131`'s docstring** ("Orders were throttled by the realtime-bar budget…") — a **string constant**
  the AST scan can see; it **dies with `OrderRateLimiter` in wave 4**. Under revision 1 it was the reason `Orders` was
  exact-matched; that reason is gone, and exact matching is kept on the prose-safety ground instead (`AP-D46-7`).
- **`ibkr/bridge.py:42`'s `# Account & Orders` comment** — a **comment** (invisible to the AST scan, and the
  raw-text twin is `ui/`-only) and the section header for the **retained** `account_summary` / `position_update`
  signals, so wave 2 deletes only the three order signals beneath it and leaves this line alone. **Not an offence,
  and not a task** — recorded so nobody "fixes" it into a dead-test investigation.
- **`services/sound_service.py`'s `_effect`** — not an order member by name, but its ternary carries the **string
  constant** `"_fill_effect"`. The collapse to alarm-only is therefore part of **wave 5**, not a later tidy-up.
- **`tests/test_order_rejections.py`'s module docstring** — its pre-fix narrative names `_on_order_error`; wave 1
  rewrites it to name the status bar (a docstring is a string constant, so it is also what a future scan reads).
- **`ui/main_window.py`'s "ticket reflects reality" comment** — removed with the branch it justified in wave 1
  (`ESC-062` item 4, incidentally).
- **`ibkr/error_codes.py`'s 202 rationale** — kept as a rationale (cancellation is a normal lifecycle event;
  `warning`, not `info`, so it is not suppressed), with only the dead registry clause reworded (wave 9).
- **`docs/codebase-map.md`'s generated skeleton** — rebuilt from the tree by `update_codebase_map.py`, so it keeps
  listing `ibkr/orders.py` **until the next refresh**; the Plan-owned annotations describe the post-P5 target
  state and say so in the map header (`AP-D46-11`).
- **`graphify-out/graph.json`** — still describes the pre-D45 tree; discovery only, never truth (the source wins).
- **Line-number drift** — every line reference in this section is indicative; symbols are the primary pointer
  (`DG56`), and `ui/main_window.py` is edited twice in this batch (waves 1 and 7).

Handoff: canonical set for **P5**, **revision 2** — `docs/architecture.md` § *Phase P5 — D46 increment* (decisions
`S39`–`S50`, risks `AR-D46-1`–`AR-D46-12`, the frozen interfaces with their consumers, the traceability table and the
nineteen supersessions/non-changes) and `docs/plan.md` (this section: **three phases, ten waves**, the forced order
and the per-name ownership table, the per-file map, the **2/13/0** test book, the residue step, the document trail,
assumptions `AP-D46-1`–`AP-D46-20`, the six Flagged Issues and the correction record). `docs/codebase-map.md` is
refreshed in this draft (wider scope, the migration, the corrected survivors, the P5 book; `ESC-063` already fixed).
**This section is ACTIVE** — Plan Artifact Editor & Validator re-activated it after the scope change (validation 2,
`docs/plan_review_P5.md`, `Status: APPROVED`), and its activation corrections are recorded there. The phase order is **Phase 1 (waves 1–7) → Phase 2 (waves 8–9) →
Phase 3 (wave 10)**: consumer first, each emitter inside its signal's wave, the module before its utilities, the
schema **with** its readers, the instrument last among the removals, and the gate closing the batch.

Status: READY_FOR_TASK_MANAGER

---

## Phase P6 — D47 (Batch 22): the chart stack migrates to Lightweight Charts behind a `ChartView` seam — drafted 2026-10-26

> Companion: `docs/architecture.md` § *Phase P6 — D47 increment* (Codebase Summary, S51–S60, frozen interfaces,
> non-functional approach, R86–R92). Requirements: `docs/requirements/requirements.md` (D47, Journey 40,
> `AC-D47.1`–`AC-D47.9`, A105–A112, R86–R92, `design_gaps.md` DG88–DG96, `open_questions.md` Q60–Q63 —
> Q60 answered-by-default YES; Q61–Q63 ANSWERED 2026-10-26, owner-confirmed). The attached migration plan (updated,
> no soak) is the execution design — adopted whole (T1–T14, Phases 0–11, 19-row parity matrix, pyramid strategy,
> 66-file classification); the material adjustments vs its first version are all owner-decided: **no soak** (triple
> gate instead), **Phase 0 spike as the single no-prototype exception**, **owner-approval-only deletion**.
> Existing-repo run: Current Tech Stack is a hard constraint (extended by the D47 row, never replaced); every
> component/entity/integration below carries `[existing]` / `[new]` / `[new/changed]`; pyqtgraph stays **default
> through Phase 10** and **no pyqtgraph code is deleted before Phase 11**. D1–D46 are NOT reopened beyond the
> recorded Q60 density-cap supersession.

### Phases (milestones — Task Manager decomposes each wave into tasks)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. The pyramid test strategy rides
every wave (pure-Python suites + `node --test` JS suites + `@pytest.mark.webengine` skip-never-red cases + the manual
checklist); each wave exit updates `docs/lwc_parity_matrix.md`.

| Wave | D47 phase (effort) | Goal (which D47 items it delivers) | Gate |
|---|---|---|---|
| P6-01 | **Phase 0** spike (S) | Throwaway `spikes/lwc/` proves the 9 API behaviours; `docs/lwc_spike_results.md` lands with a **go/no-go record**; the measured `.app` size delta + signing-flow finding reported (A109/DG89); Phase-0 perf baseline captured for the cutover gate | Go/no-go recorded; spike unimported by production/tests (Build-enforced); no-go stops Phase 1 |
| P6-02 | **Phase 1a** seam (M) | `ChartView` protocol + `DrawingController`/`AlarmController` (exact signal signatures) + `create_chart_view(tz_offset, editable)` on `NDT_CHART_ENGINE`/QSettings (pyqtgraph default; unknown → pyqtgraph) | Factory unit cases (unset/unknown/pyqtgraph/lwc) + per-controller signal-signature assertions (`AC-D47.1`) |
| P6-03 | **Phase 1b** shared model (M) | Shared Qt-free chart model (plotted-index filtering, `floor_bar_budget`, whitespace, studies + cache, Heikin-Ashi, volume); `ChartPanel` delegates with **no behaviour change** — pre-D47 chart suites stay green unmodified | Delegation probe + named suites green (`AC-D47.2`) |
| P6-04 | **Phase 2** runtime + bridge (L) | `QWebEngineView` host + vendored v5.2.x via `ndt://` (registered before `QApplication`) + deny-default interceptor; `QWebChannel` `LwBridge` batched `{v:1,ops:[]}`, queue-until-ready, ~33ms coalesce, replay after `renderProcessTerminated`; backpressure counters instrumented (DG91); focus/keyboard model named (DG92); webengine viability probe (DG88) | Offline/airplane case + interceptor case + replay identity case (`AC-D47.3`/`AC-D47.4`) |
| P6-05 | **Phase 3** core chart (XL) | Panes (v5), logical-index time axis + whitespace, `gap_is_non_trading` authority, custom tz formatters, per-mode series, `series.update` live bar; **T10**: density-cap AC retirement for `barSpacing` (Q60 answered-by-default YES) + restated no-overlap guarantee (DG94) | Time parity cases (DST/session-boundary) + rendered-geometry guard (`AC-D47.5`/`AC-D47.6`) |
| P6-06 | **Phase 4** studies (M) | Study overlays through the shared model + cache on the LWC engine | Study parity rows |
| P6-07 | **Phase 5** interaction (XL) | In-HTML controls with Python shims; Python `RouterMode` + JS mirror (mirror never reinterprets TR-1…TR-17); crosshair drift to library-native (Q63/A108); focus round-trip | Router-mirror suites + dialog suites green (`AC-D47.7`) |
| P6-08 | **Phase 6** alarms (M) | Alarm lines/overlays on LWC; Qt alarm dialogs stay | Alarm parity rows |
| P6-09 | **Phase 7** drawings (XL, largest) | Primitives library (ts-to-fractional-index); zone/horizontal-line settings stay Qt | Drawing parity rows incl. timestamp edge fixtures (DG93) |
| P6-10 | **Phase 8** overlays/markers (M) | Session/gap/ICT/VIX overlays + event markers on LWC | Overlay parity rows |
| P6-11 | **Phase 9** pop-outs (L) | LWC views in pop-outs; cap stays 10 (Q62/A107); per-pop-out memory accounted (DG90) | 1/3/6 pop-out verification + memory accounting |
| P6-12 | **Phase 10** packaging/CI/cutover candidate (M) | Bundle + signing disposition from the measured delta (Q61/A109); CI wiring; parity matrix all Done/accepted (or rule-10 entries); owner acceptance; Phase-0 perf holds — the triple gate, no soak | Cutover candidate declared (`AC-D47.6`/`AC-D47.8`); pyqtgraph **still present and default** |
| P6-13 | **Phase 11** removal (S, separately gated) | pyqtgraph deletion **only on explicit owner approval after one live trading session with no engine defect**; never rides along with cutover | Approval + session sign-off on record (`AC-D47.8`); refused otherwise |

The T1–T14 work items from the attached plan sequence into these waves in D47-phase order (T10 density-cap
retirement lands in P6-05 with the Q60 record; deletion work is P6-13 only). Task Manager owns the final
T→task mapping and the 66-file keep/retarget/engine-specific classification; no task deletes pyqtgraph code before
P6-13.

### Traceability (requirement → architecture → wave)

| Requirement | Architecture section | Wave |
|---|---|---|
| D47.1 / `AC-D47.1` (seam selects; signatures unchanged) | S51; Frozen (RouterMode, stores) | P6-02 |
| D47.2 / `AC-D47.2` (model delegates; no behaviour change) | S52 | P6-03 |
| D47.3 / `AC-D47.3` (vendored and offline) | S53 | P6-04 |
| D47.4 / `AC-D47.4` (batched bridge; replay after crash) | S54 | P6-04 |
| D47.5 / `AC-D47.5` (time/panes/series parity) | S55; Frozen (`gap_is_non_trading`) | P6-05 |
| D47.6 / `AC-D47.6` (cutover gate; density-cap retirement via Q60) | S56 `[revises D42: S13]`; Frozen (backfill, cache, tunables) | P6-05 (T10) + P6-12 (gate) |
| D47.7 / `AC-D47.7` (contracts kept; out-of-scope untouched) | S57; all Frozen rows | P6-07 + every wave (residue scan) |
| D47.8 / `AC-D47.8` (phased delivery; removal gated) | S58, S59 | P6-01 → P6-13 in order |
| D47.9 / `AC-D47.9` (matrix current; history intact) | S58, S59; rule 10 | Every wave exit + P6-12 |
| D47.10 / `AC-D47.10` (pyramid tests; 66 files) | S60 | Every wave |
| D47.11 (cutover/removal gates) | S59 | P6-12, P6-13 |
| D47.12 (out of scope stays out) | S59; Frozen rows | Every wave |
| D47.13 (history preserved) | S59 | P6-12 |
| Journey 40 (end-to-end migration journey) | S51–S60 | P6-02 → P6-12 |
| A105–A112 | S51–S60 (A106→S56, A107→S59/wave P6-11, A108→S57, A109→S60/P6-01+P6-12, A110–A112→S60/S54/S55) | As noted |
| R86–R92 | Architecture Risks table → S51–S60 mitigations | As noted |
| DG88–DG96 | S60 (DG88), S59/S60 (DG89), S59 (DG90), S54 (DG91), S57 (DG92), S55 (DG93), S56 (DG94), S58 (DG95), S58 (DG96) | As noted |
| Q60 (answered-by-default YES) / Q61–Q63 (owner-confirmed) | S56 (Q60), S60/S59 (Q61), S59 (Q62), S57 (Q63) | P6-05, P6-01/P6-12, P6-11, P6-07 |

D1–D46 (all journeys/ACs) are frozen and re-affirmed, not re-planned — covered by the no-behaviour-change delegation
(P6-03), the frozen interfaces, and the full-suite-green exit of every wave.

### Assumptions (plan-level only — none restates `requirements.md` A105–A112)

| # | Assumption | Rationale |
|---|---|---|
| AP-P6-1 | The engine selector reads `NDT_CHART_ENGINE` first (`lwc` selects LWC; unset/unknown → pyqtgraph) with the `QSettings` equivalent as the persisted override; pyqtgraph remains the default through P6-12 | Cutover flips the default only when the triple gate holds; an unknown value must never blank the chart (Journey 40 edge case) |
| AP-P6-2 | `spikes/lwc/` stays throwaway: nothing there is imported by production or tests, it ships no test of its own into the suite book, and it is excluded from packaging; a production import of the spike fails the build | The single no-prototype exception (owner approval 3) stays an exception (DG96) |
| AP-P6-3 | T1–T14 map into waves P6-01→P6-13 in D47-phase order as tabulated; Task Manager owns the final assignment and the 66-file keep/retarget/engine-specific classification | The attached plan numbers the work; this plan sequences the waves — the file-by-file tasking is Task Manager's job |
| AP-P6-4 | Webengine cases are marked `@pytest.mark.webengine` and skip (never red) where no engine exists from P6-04 on; each names its manual-checklist counterpart | Offscreen viability is unproven (DG88/A110) — a red case must mean a regression |
| AP-P6-5 | Every wave exit re-reads `docs/lwc_parity_matrix.md` (19 rows); a row regressing without an escalation fails the wave (rule 10) | The matrix is the gate, not the suite alone (DG95/R92) |
| AP-P6-6 | AC-G.1 (visual reference gate) does not apply beyond Q63: the only UI-visual decision (crosshair drift) is owner-decided verbatim ("Accept drift"), so no reference artifact is required | Q63 settled appearance-vs-drift explicitly; nothing else in P6 is a UI-visual choice |

### Flagged Issues

**None.** Every D47 requirement is satisfiable as written on the existing stack plus the explicitly authorized
additions (vendored v5.2.x tree, `QWebChannel`, Qt-free model — all additive, none replacing a constrained choice):

- D47.6's density-cap retirement is **decided, not silent**: Q60 is answered-by-default YES (the attached plan states
  the replacement as an owner-visible AC change), the supersession of `AC-D6.4`/`AC-D7.1`/`AC-D9.1` density language is
  recorded in `requirements.md` and restated as S56 `[revises D42: S13]`, and T10 lands only with that record (DG94/R89).
- Q61–Q63 are owner-confirmed verbatim and change no scope (measure-first, keep 10, accept drift).
- DG88–DG96 are recorded Plan/Build details with owners and waves assigned above — none blocks planning.

Status: READY_FOR_TASK_MANAGER

---

## Phase P7 — data-path batch: historical backfill correct + fast, streaming correct (no holes, no duplicates, no dropped/late bars) — drafted 2026-10-28

> Companion: `docs/architecture.md` § *Phase P7 — data-path batch* (Codebase Summary, S-P7-1…S-P7-7, frozen
> interfaces, non-functional, AR-P7-1…AR-P7-6). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`); the P7 state brief (native-ibapi probe: SPY 1-min 30 D in ~1.1 s, AAPL 1-min
> complete — the 90 s zero-bar timeouts were our own reader-thread/handshake bugs, both understood);
> open escalations ESC-075/076/077/078 (`routed_to: BUILD`) and ESC-079 (`routed_to: PLAN`).
> Already landed — re-affirmed, never re-planned: handshake-gated readiness (`IBKRNotReady`, Q-35), 0.5 s
> interval + rolling budget (Q-30), error-162 retry, S0/D38 removal end state, Qt-free import boundary
> (`test_t38_t08`), per-view WebEngine profile (Q-40). Hard constraints: **no order-related code anywhere**
> (D45/D46); live validation is **read-only**; the **owner names the validation method**; the **full offscreen
> suite green is the gate**. Existing-repo run: every wave below modifies existing modules in place; **no new
> module, no new dependency, no schema migration**. One phase only — nothing past the P7 build wave is planned.

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P7-W1 | M | **Budget invariant + persist-and-resume backfill core** (S-P7-1, S-P7-2; architectural answer to ESC-079, code side of ESC-075/076). Per-load cap (≤ ¼ rolling budget), oldest-first monotonic floor fill across loads, per-chunk persist+render, same-chart reload coalescing, cancel-slot refund rule. | (1) A 1-min load issues at most ⌊budget/4⌋ historical requests before yielding; (2) killing/reloading mid-wave loses zero fetched bars (cache + chart advance monotonically); (3) a same symbol/timeframe/mode reload does not cancel an in-flight wave; (4) full offscreen suite green. | Offscreen: new wave-lifecycle suites with a fake transport (request counting, mid-wave reload, chunk-visibility assertions) + full suite. No live TWS needed. |
| P7-W2 | S | **Watchdog/prime/pacing coherence** (S-P7-3, S-P7-4; code side of ESC-077/078 + the 076 debug-classification). Window-relative watchdog bound, strand clears timer + queue, one-interval prime precedence (or explicit reservation), skipped-prime warning, superseded-reqId 162-ack at debug. | (1) A wave deferred on pacing for the full continuation delay is never flagged stranded; (2) a finalised wave cannot resume after a strand-clear; (3) the prime issues even when a full wave starts alongside it (or a counted warning names it); (4) full offscreen suite green. | Offscreen: watchdog/prime timing suites (fake clock/timers) + 162-classification assertions + full suite. No live TWS needed. |
| P7-W3 | S | **Wide-duration decision point** (S-P7-5): `"1 min"` (and only the timeframes the evidence supports) widened — e.g. `"1 D"` → `"30 D"` — **only with measured before/after and explicit owner approval**. Pacing re-verified with the wide request (0.5 s interval, rolling budget, no GUI-thread sleep). | (1) Before/after numbers on record (requests/load, time-to-first-bar, time-to-current, slot spend) for each widened timeframe; (2) owner approval on record before the constants change; (3) shortfall/empty on a wide request surfaces (never a silent hole) with rollback to chained requests; (4) full offscreen suite green. | Offscreen suites + a **read-only** live measurement run **only by the method the owner names** (owner-gated; no automated live step). Suite green is the merge gate either way. |
| P7-W4 | M | **Streaming correctness close-out + batch gate** (S-P7-6/S-P7-7): reconnect replay, stream-health/backoff, realtime-bars priming, watchlist `reqMktData` deferral, and the Q-41 deferral contract covered end-to-end; batch-wide non-regression. | (1) Reconnect replays subscriptions with rebound reqIds and no duplicate bars; (2) no dropped/late aggregated bars under a tick burst with priming intact; (3) watchlist adds while throttled defer without losing the row; (4) nothing sleeps on the GUI thread on any pacing path; (5) **full offscreen suite green**; (6) read-only live validation performed by the owner-named method. | Offscreen burst/reconnect/deferral suites + full suite, then the owner-named read-only live check. A red suite or an unapproved live step fails the wave. |

**What stays untouched by every P7 wave:** the `req_historical_data` / `req_mkt_data` signatures and pacing
contract; the pure planner function contracts (`find_missing_spans`, `plan_requests`, `floor_bar_budget`);
the pacing tunables' existence and the port guard; error ingress/classification; `RealtimeBarsManager` /
`StreamHealth` APIs; `BarCache` APIs; the Qt-free import boundary; the order-code absence; the entire LWC
renderer seam (`ui/chart_view.py`, `services/chart_model.py`, `ui/lwc_*`); the `bars` schema (no migration).

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| ESC-079 (PLAN: budget invariant, per-load cap, floor across loads, window-relative bounds) | S-P7-1; Frozen (tunables, planner contracts) | P7-W1 |
| ESC-075 (BUILD: persist-as-arrived, no resume-loss, floor must not cost one wave) | S-P7-1, S-P7-2; Frozen (`BarCache`, planner) | P7-W1 |
| ESC-076 (BUILD: coalesce same-chart reload; cancel accounting; 162-ack as debug) | S-P7-2; Frozen (error ingress) | P7-W1 (coalesce/refund) + P7-W2 (162 classification) |
| ESC-077 (BUILD: watchdog vs pacing-deferral coherence) | S-P7-3; Frozen (pacing contract) | P7-W2 |
| ESC-078 (BUILD: prime precedence vs wave starvation) | S-P7-4; Frozen (planner, RT bars) | P7-W2 |
| Probe: single-shot wide requests (30 D ≈ 1.1 s) → duration widening as gated decision | S-P7-5; Tech Stack table | P7-W3 |
| Streaming: watchlist `reqMktData` defer (Q-45), aggregator priming, stream health, reconnect replay (D27), Q-41 deferral contract | S-P7-6; Frozen (RT bars, StreamHealth, `req_mkt_data`) | P7-W4 (W1–W3 must not regress it) |
| Hard constraints: no order code (D45/D46); read-only live; owner names method; suite green gate | S-P7-7; Frozen (order absence, Qt-free boundary, renderer seam) | Every wave |
| Landed substrate (Q-30/Q-35/Q-38/Q-40, 162 retry, S0/D38 removal) | S-P7-7; Frozen | Re-affirmed, no wave |

### Per-load cap semantics (clarification 2026-10-28, Q-51 — no decision changed)

The per-load cap (S-P7-1, P7-W1) is a **maximum, never a target**:

- A single chart load issues **at most** `min(requests needed, floor(B/4))` historical requests, where `B` is the current `MAX_HISTORICAL_PER_600S` rolling budget — the cap never creates work to fill itself.
- Examples (with `floor(B/4) = 25`): a load needing **1** request issues **1** and stops; a load needing **10** issues at most **10**; a load needing **40** issues at most **25** in this load, persists the completed chunks, and resumes the remainder on later loads under the persist-and-resume / oldest-first floor contract (S-P7-2) — never forced chunking, never an automatic spend of reserved slots, never a promise of immediate full history.
- **Per-load** means one chart-load wave for one symbol + timeframe + ext-hours mode. A reload for the same chart **coalesces into** the running wave (AP-P7-2) and shares its allocation — it does not open a second allocation. A cancelled slot is refunded **only** when its request never reached TWS (pre-issue cancel, AP-P7-3); post-issue cancels keep their slot (AR-P7-4).
- **Budget-number reconciliation (Flagged Issue 3, settled as a reading, not a silent choice):** the tree carries `MAX_HISTORICAL_PER_600S = 100` (`config/settings.py`, whose comment marks it owner-set), while ESC-075's text cites a 50-slot budget. The 50 is **stale prose**; the operative value is **100 per the source**, and S-P7-1 states the invariant as a **fraction of the tunable** so it holds under either value and survives future retunes. `AC-D16.8` itself is untouched by this clarification — its restatement stays open Requirements Analyst debt (Flagged Issue 1 / RG-P7-1).

Every ESC-075…079 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P7-1 | The ¼-budget per-load cap is a starting bound, not a tuned optimum; waves measure actual slot spend and the Validator may tighten/loosen the fraction on evidence | A fixed count would rot on the next tunable retune (the 50-vs-100 drift in ESC-075's text is the proof) |
| AP-P7-2 | "Same chart" for reload coalescing means identical symbol + timeframe + ext-hours mode; any change of the three is a genuine new wave that cancels the old one | Coalescing across different charts would paint the wrong bars; generation fencing stays the guard |
| AP-P7-3 | Cancel-slot refund applies only to reqIds whose request never reached TWS (pre-issue cancel); post-issue cancels keep their slot | Refunding issued slots would over-count the budget and risk a real 162 storm (AR-P7-4) |
| AP-P7-4 | P7-W3 widens only the timeframes with measured evidence; timeframes without a before/after record keep chained requests | The brief gates each duration change on measurement, not on the wave as a whole |
| AP-P7-5 | Read-only live validation never places, cancels, or closes anything and never writes production state; the owner names the exact method (symbol set, session, read-only checks) before P7-W3/W4 run it | Zero order interaction (D45/D46) plus the live gate from the brief |
| AP-P7-6 | AC-G.1 (visual reference gate) does not apply: P7 makes no UI-visual decision (no icon/placement/colour/label/size choice) | All P7 outcomes are data-path behaviour with log/cache/render-state measurables |

### Flagged Issues

1. **`AC-D16.8` as literally written is unsatisfiable for `"1 min"` in one load** (ESC-079's measured proof:
   ~31 floor requests + hole repair against a 50–100-slot rolling budget shared by every session). P7 plans the
   satisfiable reading — the floor as an invariant over **successive loads** (S-P7-1) — but Plan does not rewrite
   requirements: the **Requirements Analyst must restate `AC-D16.8`** (floor met monotonically across loads,
   oldest-first, no single-load deadline) or explicitly confirm the restatement. Suggested direction: adopt the
   S-P7-1 wording verbatim. (The Validator carries this as the official escalation; it is surfaced here, not
   filed here.)
2. **Duration widening (S-P7-5/P7-W3) needs explicit owner approval per timeframe** with the measured
   before/after on record. If the owner declines, P7-W3 records the decline and the chained-request path
   (with W1/W2 fixes) stands as the shipped behaviour — the wave is still complete, just narrower.
3. **Budget-number drift:** ESC-075's text cites a 50-slot budget while the tree carries
   `MAX_HISTORICAL_PER_600S = 100`. S-P7-1 is deliberately fraction-based so the invariant holds under either
   value; no requirement change is needed, but the Validator should confirm which value the suite asserts.

Status: BUILT - waves P7-T01 through P7-T08 + Q-46/Q-47 landed 2026-10-28 (feature commit `7cba534`, tracking `c4f2be2`); as-built record in `docs/phase-changelog.md` Phase P7. ESC-075/076/077/078 addressed code-side (focused close-out 2026-10-28, `docs/code_review/review_log_P8.md`, commit `4610c35`); ESC-079 open as Requirements Analyst debt (RG-P7-1).

### P16-D55.6 coordinated addendum (2026-11-04 — appended delta, approval preserved, no P7 decision changed)

This subsection is appended; every line above stays byte-identical and the `Status: BUILT` record stands.

- **Per-load cap = maximum, never a target (S-P7-1 / P7-W1 reading):** a single chart load issues at most `min(requests needed, floor(B/4))` historical requests (`B` = current `MAX_HISTORICAL_PER_600S`); the cap never creates work to fill itself. Worked examples at `floor(B/4) = 25`: need **1** -> issue **1** and stop; need **10** -> issue at most **10**; need **40** -> issue at most **25** this load, persist completed chunks, resume the rest on later loads (persist-and-resume / oldest-first, S-P7-2). No forced chunking, no automatic spend of reserved slots, no promise of immediate full history.
- **Per-load defined:** one chart-load wave for one symbol + timeframe + ext-hours mode. A same-chart reload coalesces into the running wave and shares its allocation (AP-P7-2); a cancelled slot is refunded only when its request never reached TWS (AP-P7-3 / AR-P7-4).
- **50-vs-100 reconciled with cited evidence (DG102 / A154):** the tree carries `MAX_HISTORICAL_PER_600S = 100` (`config/settings.py`, owner-set per the source comment); ESC-075's "50-slot" text is stale prose. The operative value is **100 per the source**, and the invariant is fraction-based so it holds under either value — both figures are named here, none silently chosen. Decided from `config/settings.py` plus the P7 wave assertions (P7-W1 request-count caps); no open item remains on this point.
- **Requirement reference only:** `AC-D16.8` is cited by reference (`docs/requirements/requirements.md`, via RG-P7-1, still Analyst debt) and its text is restated nowhere in this addendum.

## Phase P8 — D48 (Batch 23): add `1 week` (2Y) and `1 month` (10Y) timeframes — drafted 2026-10-28

> Companion: `docs/architecture.md` § *Phase P8 — D48 increment* (Codebase Summary, S-P8-1…S-P8-7, frozen
> interfaces, non-functional, AR-P8-1…AR-P8-5). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — Batch 23 (D48), Journey 41, `AC-D48.1`–`AC-D48.7`, lite defaults A113–A120,
> R93–R95, `design_gaps.md` DG97–DG98. Hard constraints: **no order code anywhere** (D45/D46); live
> validation is **read-only** (the standalone probe issues historical requests only); the **full offscreen
> suite green is the gate**. Existing-repo run: every wave below modifies existing modules in place; **no
> new module, no new dependency, no schema migration**. One phase only — nothing past the P8 build wave
> is planned. If this decomposed L-sized, the lane is wrong: report back instead of building.

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P8-W1 | M | **Data plane: config + calendar bucketing + probe** (S-P8-1, S-P8-2, S-P8-3, S-P8-5; answers DG98 and the R93/R94 risks). Two `TIMEFRAME_CONFIG` rows; Monday-ET weekly + calendar-month bucketing with nominal-seconds keys; planner no-change verification; priming docstring rows; standalone probe of both new combos. | (1) Config holds the two exact rows and no other row changes; (2) weekly buckets open Monday ET and monthly on month boundary across DST-fold, February, and Dec/Jan unit cases; (3) a weekly/monthly load plans the configured duration (chunked as needed), never applies the `AC-D16.8` floor, and detects holes at bar granularity; (4) both probe requests complete with no 321-class rejection (a rejection fails the wave and escalates — never a silent shrink); (5) full offscreen suite green. | Offscreen unit/planner/aggregator suites with the new keys + the standalone probe record + full suite. |
| P8-W2 | S | **Presentation plane: picker + daily+ no-ops + visibility** (S-P8-4, S-P8-6, S-P8-7; answers DG97 and the R95 inventory). Picker order after `1 day` with select/load/persist parity; canonical full-session mode for daily+ (request, cache, planner, prime) with toggle-convergence; the shared daily-or-coarser predicate across bands/collapse/plotted/session-regions; visibility dialog guard; burst minutes mapping. | (1) Picker lists `1 week`/`1 month` immediately after `1 day` and each selects/loads/persists like every other timeframe; (2) RTH and ETH loads of each new timeframe return identical bars with one shared cache, no band and no collapse (toggle converges with no extra requests when cached); (3) visibility dialog opens with every box checked and the payload round-trips; (4) `minutes_for_timeframe` returns 1950.0/8190.0; (5) full offscreen suite green. | Offscreen picker/mode-parity/dialog/minutes suites + full suite. No live TWS needed. |
| P8-W3 | S | **Batch gate: probe record + non-regression close-out**. Both probe outcomes on record, every `AC-D48.*` observably satisfied, pre-D48 criteria untouched except the recorded enumeration extension, full suite green. | (1) Probe record present for both combos; (2) `AC-D16.1` "eight timeframes" wording and the `AC-D27.9` two added table rows verified, `### D41`–`### D47` + marker + Current Tech Stack intact; (3) **full offscreen suite green**. | Full suite + the AC checklist. A red suite or a missing probe record fails the wave. |

**What stays untouched by every P8 wave:** the `req_historical_data` / `req_mkt_data` signatures and
pacing contract; the planner function contracts; the pacing tunables and the port guard; error
ingress/classification; `RealtimeBarsManager` / `StreamHealth` APIs; `BarCache` APIs; the Qt-free
import boundary; the order-code absence; the entire LWC renderer seam; the `bars` schema (no
migration); the six existing `TIMEFRAME_CONFIG` rows' values; the visibility payload shape.

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| D48.1 / `AC-D48.1` (mapping: `1 week`→`1 week`/`2 Y`, `1 month`→`1 month`/`10 Y`) | S-P8-1; Frozen (six existing rows) | P8-W1 |
| D48.2 / `AC-D48.2` (Monday-ET weekly, calendar-month buckets, live forming-bar parity) | S-P8-2; Frozen (existing periods + `_period_start` grid) | P8-W1 |
| D48.3 / `AC-D48.3` (planner/backfill: configured duration, no `AC-D16.8` floor, bar-granular holes) | S-P8-3; Frozen (planner contracts) | P8-W1 |
| D48.4 / `AC-D48.4` (RTH/ETH no-op, shared cache, bands/collapse absent) | S-P8-4; Frozen (`req_historical_data`, `BarCache`) | P8-W2 |
| D48.5 / `AC-D48.5` (picker entries after `1 day`; select/load/persist parity; visibility default-on) | S-P8-1, S-P8-6; Frozen (visibility payload shape) | P8-W2 |
| D48.6 / `AC-D48.6` (standalone probe + suite green) | S-P8-5; Non-Functional stability gate | P8-W1 (probe) + P8-W3 (record) |
| D48.7 / `AC-D48.7` (history intact; only the recorded enumeration extension) | Frozen (all `[existing]` rows) | P8-W3 |
| Journey 41 (load weekly/monthly, toggle Ext Hours, switch symbols, suite green) | S-P8-1…S-P8-7 | P8-W1…P8-W3 |
| A113–A120 (lite defaults) | S-P8-1…S-P8-7 (each default cited at its decision) | P8-W1/P8-W2 |
| R93 (321 rejection → escalate) | AR-P8-1; S-P8-5 | P8-W1 (probe is the gate) |
| R94 (month-boundary drift) | AR-P8-2; S-P8-2 | P8-W1 (`AC-D48.2` Feb case) |
| R95 (hardcoded six-timeframe enumerations) | AR-P8-3; S-P8-4/S-P8-6 | P8-W2 (inventory checklist) |
| DG97 (visibility-grid rows) | S-P8-6 | P8-W2 (guard test) |
| DG98 (priming table for weekly/monthly spans) | S-P8-5 | P8-W1 (docstring rows + probe) |
| Hard constraints: no order code (D45/D46); read-only live; suite-green gate | S-P8-1…S-P8-7; Frozen (order absence, seam) | Every wave |

Every D48 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.
ESC-079 (open, PLAN-routed) is P7 scope, already answered by S-P7-1 — it is not re-planned here.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P8-1 | IBKR's native weekly/monthly bars anchor compatibly with Monday-00:00-ET weeks and calendar months; a systematic phase mismatch, if the first-load comparison shows one, becomes a follow-up rather than a silent re-anchor | Mirrors the recorded D27.8 4h-anchor caveat precedent; the assumption is checkable, not load-bearing for the batch gate |
| AP-P8-2 | An Ext-Hours toggle on a daily+ timeframe converges with no extra requests when the span is cached (canonical mode makes the reload a cache hit); the toggle control itself is left in place and keeps working for intraday | A118 requires identical bars, not a disabled control; convergence is the observable |
| AP-P8-3 | AC-G.1 (visual reference gate) does not apply: P8 makes no UI-visual decision — picker entries are text labels in the existing combo in A119 order, and the visibility grid is unchanged | All P8 outcomes are config/aggregation/planner behaviour with config-assertion and bar-equality measurables |

### Flagged Issues

**None.** Every D48 item is satisfiable as written on the existing stack:

- The two new combos ride the existing request shape; IBKR acceptance is probe-verified (`AC-D48.6`),
  and a rejection has a specified escalation (R93) rather than a gap.
- Calendar bucketing, the predicate sweep, the minutes mapping, and the visibility guard are all
  mechanical changes with stated measurables (DG97/DG98 both resolve inside the waves above).
- The `AC-D16.1` enumeration extension and the `AC-D27.9` table rows are recorded analyst-side
  wording, not Plan reinterpretation.

Status: BUILT - waves P8-T01 through P8-T04 + Q-48 landed 2026-10-28 (feature commit `09761fb`, tracking `b7978c2`); phase-final verdict REVIEW_COMPLETE (`docs/code_review/review_log_P8.md`, commit `f7d4e3c`); as-built record in `docs/phase-changelog.md` Phase P8.

---

## Phase P9 — alarm/drawing fix batch (Batch 25): five owner-ordered findings — drafted 2026-10-28

> Companion: `docs/architecture.md` § *Phase P9* (Codebase Summary, S-P9-1…S-P9-4, frozen
> interfaces, non-functional, AR-P9-1…AR-P9-4). Requirements basis (approved scope, not
> re-derived): `ALARM_AND_DRAWING_CODE_REVIEW.txt` §§ 1.4, 3.1–3.4 plus the five owner decisions
> relayed by the Orchestrator (3.1 carry group+color with symbol validation, repro-first; 3.2
> read-only name cell, unit test; 3.4 re-validate on every group reload; 1.4 isolate persistence
> failures, fault-injection test first; 3.3 recolor semantics **(c) Both** + leave-group rule,
> compose with the in-flight D50 drag-editing batch). `requirements.md` carries
> `Status: READY_FOR_PLAN`. Existing-repo run: `[existing]` / `[new]` / `[new/changed]` labels
> relative to the codebase; **no new module, no new dependency, no schema migration**. One phase
> only — nothing past the P9 build wave is planned. Out of scope: operation-level lock
> enforcement beyond hidden handles (no drag path enforces it today; rides with drag-editing,
> not this batch) and the D50 batch itself.

### Traceability (finding → architecture → wave)

| Finding / owner decision | Architecture section | Wave |
|---|---|---|
| 3.1 P1 — selected set not assigned to new LWC drawings (group + color into payload; symbol validation; repro-first) | S-P9-1; Frozen (persist rule, sole-writer) | P9-W3 |
| 3.2 P2 — inline group-name edit `TypeError` (read-only cell, `Rename` stays the path; unit test) | S-P9-2 | P9-W2 |
| 3.4 P2 — deleted group leaves stale `_active_draw_group_id` (re-validate on every reload; clear + combo + tool sync) | S-P9-2 | P9-W2 |
| 1.4 P2 — DB error in `mark_triggered` aborts the bar path (isolate: log, in-memory update, retry/reconcile; fault-injection test first) | S-P9-3; Frozen (`mark_triggered` signature) | P9-W1 |
| 3.3 P2 — recolor semantics, owner decision (c) Both (creation stamps group color, stored; recolor repaints members; leave-group rule; D50 keeps stored colors) | S-P9-4; Frozen (`drawing_op` visibility) | P9-W3 |
| No production behaviour change beyond the five items; no skips/xfails; suite green | Non-Functional gate | P9-W4 |
| D50 drag-editing (in flight) — composition only | S-P9-4 constraint | P9-W3 exit check, P9-W4 |

Every item above is addressed somewhere in the architecture AND the waves below; nothing is
narrowed or reinterpreted (the leave-group rule and the D50 constraint are the owner decisions
as relayed, recorded verbatim in S-P9-4).

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Every wave
lands its repro test **red-first** (failing on the current tree) before the fix.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P9-W1 | S | **Alarm persistence isolation (1.4; S-P9-3).** Fault-injection repro first (no fault was injected in the report — reproduce before fixing), then isolate both `mark_triggered` call sites: log with symbol/alarm context, update in-memory state, emit, queue retry. | (1) Injected `mark_triggered` failure → notification still emitted, `alarm.triggered` still set, `_last_chart_price` still advanced; (2) error logged with symbol + alarm context; (3) retry queue flushed on a later bar / `reload_alarms` with no duplicate emits; (4) full offscreen suite green. | Offscreen fault-injection + retry suites + full suite. |
| P9-W2 | S | **Dialog state fixes (3.2 + 3.4; S-P9-2).** Name cell read-only (Rename path unchanged); active-ID re-validation on every group reload (delete-group path included). | (1) Name-cell edit attempt is impossible (no `ItemIsEditable`); Rename button renames as today; (2) deleting the selected group clears `_active_draw_group_id` to `None`, combo shows Ungrouped, tool re-pushed; (3) ticker-change clear still works; (4) full offscreen suite green. | Offscreen dialog/panel suites (name-edit probe, delete-selected-group probe) + full suite. |
| P9-W3 | M | **Group-color pipeline (3.1 + 3.3; S-P9-1, S-P9-4).** Active group + color into the LWC commit payload with symbol validation; stored-color recolor semantics + leave-group rule; D50 composition check. | (1) New drawing under a selected set persists the set's ID **and** its color; ungrouped creation keeps the default; (2) foreign-group IDs coerce to `None` (no cross-symbol write); (3) recolor repaints all current members' stored colors; ungroup/reassign preserves stored color; (4) drag-edited drawings keep stored colors (D50 composition — verified, not re-implemented); (5) full offscreen + `node --test` suites green. | Offscreen payload/validation/recolor suites + gestures JS tests + full suite. |
| P9-W4 | S | **Batch gate: close-out.** Every item observably satisfied, nothing else changed, suite green. | (1) All five findings' acceptance checks green; (2) no production behaviour change beyond the five items (diff review); (3) no skipped/xfailed tests added; (4) **full offscreen suite green**. | Full suite + the five-item checklist. A red suite fails the wave. |

**What stays untouched by every P9 wave:** the `mark_triggered` signature; `assign_groups` /
`delete_group` contracts; `drawing_op` visibility; `drag_drawing_item` geometry; the D28.2
sole-writer rule; the `bars`/`alarms`/`drawings` schemas (no migration); the order-code absence
(D45/D46); the LWC renderer seam; error ingress/classification; pacing tunables and the port guard.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P9-1 | The JS active-group setter is the single writer of the tool state's group fields, re-pushed by `_apply_active_draw_group` on every group reload and symbol change (AR-P9-4) | One writer keeps page state from desyncing; the Python-side validation is the backstop regardless |
| AP-P9-2 | The retry queue is in-memory only (alarm IDs, flushed on subsequent bars / `reload_alarms`); a restart with an unflushed queue loses nothing observable because `reload_alarms` re-reads `triggered` state from the store | Persisting the queue would be a schema change for a transient condition; the store remains the durable truth |
| AP-P9-3 | Recolor repaints *current* members only — drawings that left the group earlier keep the color they had (the leave-group rule, S-P9-4) | Owner decision (c) as relayed: stored colors survive leave-group in both directions |
| AP-P9-4 | AC-G.1 (visual reference gate) does not apply: P9 makes no UI-visual decision (group colors are user data, the read-only cell removes an affordance rather than adding one) | All P9 outcomes are state/persistence behaviour with probe measurables |

### Flagged Issues

**None.** Every finding is satisfiable as written on the existing stack:

- 3.1/3.3 ride fields and renderer paths that already exist (`PageDrawing`, `Drawing.color`,
  `drawing_item`); only values and one validation are added.
- 3.2/3.4 are state-bookkeeping fixes with probe measurables.
- 1.4 is call-site isolation with a frozen store contract; the fault-injection repro is the
  wave's first deliverable because the report performed no injection.
- Operation-level lock enforcement (report §2.2) is **out of scope by owner order**, recorded
  here — not an open gap: hidden handles stay the enforcement signal until drag-editing lands.

Status: READY_FOR_TASK_MANAGER

---

## Phase P10 — D50 drag-editing for LWC drawings (whole-move + anchor drags, handle UI, lock, recolor interplay, persistence/fan-out) — drafted 2026-10-28

> Companion: `docs/architecture.md` § *Phase P10* (Codebase Summary, S-P10-1…S-P10-5,
> frozen interfaces, non-functional, AR-P10-1…AR-P10-4). Requirements basis (approved
> scope, not re-derived): D50, Journey 43, `AC-D50.1`–`AC-D50.5`, A127–A132, R99–R101,
> Q67–Q71 (answered owner-confirmed 2026-10-28). `requirements.md` carries
> `Status: READY_FOR_PLAN`. Existing-repo run: `[existing]` / `[new]` / `[new/changed]`
> labels relative to the codebase; **no new module, no new dependency, no schema
> migration, no order code**. One phase only — nothing past the P10 build wave is planned.
> Out of scope: creation behaviour (settled inputs A127/A128 — creation is not
> re-specified); render-path changes (primitives path proven, A127); any visual language
> beyond handle presence-gating.

### Traceability (requirement → architecture → wave)

| Requirement / journey / AC | Architecture section | Wave |
|---|---|---|
| D50.1 whole-move + per-kind anchor drags (Q67 both) | S-P10-2 (restated ESC-086: page `dragItem` mirror computes preview/commit geometry; `page_geometry_payload` commit-time check; `drag_drawing` lock/validation surface bound in tests/direct calls); Frozen (`drag_drawing_item`, `drawing_handle_points`) | P10-W2 |
| D50.2 handles only while selected; locked none (Q68) | S-P10-1 | P10-W1 |
| D50.3 operation-level lock: drag initiation/move/commit + delete refused, color allowed (Q69) | S-P10-4 | P10-W2 (drag refusal) + P10-W3 (delete refusal, color-allowed) |
| D50.4 recolor interplay, (c) Both + A132 mid-drag rule (Q70) | S-P10-5; Frozen (`update_drawing` None-contract) | P10-W3 |
| D50.5 store update + reload restore + exactly-once fan-out (Q71) | S-P10-3; Frozen (sole-writer rule) | P10-W2 (close-out) + P10-W4 (gate) |
| Journey 43 (select/drag/locked-attempt/reload) + edge cases | S-P10-1…S-P10-5 | P10-W1…W4 |
| A127–A129 settled inputs/facts; A130–A132 recolor + offscreen + mid-drag | Summary; S-P10-5; Non-Functional | All waves (constraints, not work) |
| R99 (matrix undecided) / R100 (visibility-only lock) / R101 (3.3 landing) | Settled pre-clarification risks — closed by Q67/Q69/Q70; S-P10-2/S-P10-4/S-P10-5 | — (no wave; recorded as closed) |
| No production behaviour change beyond D50; no skips/xfails; suite green | Non-Functional gate | P10-W4 |

Every item above is addressed somewhere in the architecture AND the waves below; nothing
is narrowed or reinterpreted (the per-kind matrix, the lock triple-forbid + color-allowed,
and the (c) Both + A132 rules are the owner decisions as recorded).

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Every
wave lands its repro test **red-first** (failing on the current tree) before the fix.
Waves are S/M only.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P10-W1 | S | **Handle UI (D50.2; S-P10-1).** Selection-gated handles; locked offers none (highlight only); deselect clears. | (1) Selecting a drawing attaches its per-kind handles; deselecting clears them; (2) a locked drawing carries `selected` highlight with empty handles; (3) visibility/visible-group rules unchanged; (4) full offscreen + `node --test` suites green. | Offscreen wire-item/selection probes + JS tests + full suite. |
| P10-W2 | M | **Drag initiation + commit close-out (D50.1/D50.5; S-P10-2 restated ESC-086, S-P10-3 + drag half of S-P10-4).** Page initiation (body whole-move all five kinds + per-kind anchors), page-mirror commit (`dragItem` recompute → `updated` → persist → reload → exactly-once fan-out, `page_geometry_payload` commit-time check); `drag_drawing` lock refusal at initiation; cancel writes nothing. | (1) Whole-move + anchor drags commit the dragged geometry per kind (endpoints, edges/corners, price level; fib levels / measure delta recomputed by the page mirror); (2) locked initiation refused: geometry unchanged, no store write; (3) mid-drag cancel leaves store + geometry identical; (4) committed edit survives session reload on every view with one fan-out; zero-view edit persists; (5) full suites green. | Per-kind geometry suites + lock-refusal/cancel probes + seeded-store reload/fan-out-count suites + full suite. |
| P10-W3 | S | **Lock completion + recolor interplay (D50.3/D50.4; S-P10-4, S-P10-5).** Delete refusal on locked drawings; color/style allowed incl. group recolour of locked members; geometry-only commits; mid-drag recolour case. | (1) Delete on a locked drawing refused (row + geometry intact); (2) color/style change on a locked drawing applies, incl. group recolour repainting a locked member's stored color; (3) drag-edit commit leaves stored color untouched; mid-drag recolour: ghost keeps start color, stored (recoloured) wins at commit; former members keep leave-group color; (4) full suites green. | Offscreen lock/delete/color probes + stored-color round-trips + mid-drag recolour suite + full suite. |
| P10-W4 | S | **Batch gate: close-out.** Every D50 criterion observably satisfied, nothing else changed, suite green. | (1) All five ACs' checks green; (2) no production behaviour change beyond D50 (diff review); creation path, render path, schemas, order-code absence untouched; (3) no skipped/xfailed tests added; (4) **full offscreen suite green**. | Full suite + the five-AC checklist. A red suite fails the wave. |

**What stays untouched by every P10 wave:** the `DrawingController` signal signatures;
`DrawingStore.update_drawing` / `delete_drawing` signatures and the `None`-means-unchanged
contract; `drag_drawing_item` / `drawing_handle_points` geometry; `drawing_op`
visibility; the creation path (`drawingItem`, `PageDrawing`, `_on_drawing_created`,
group validation); the primitives render path; the `bars`/`alarms`/`drawings` schemas (no
migration); the order-code absence (D45/D46); pacing tunables and the port guard.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P10-1 | Drag previews publish `drag_drawing` ops without touching the store; only pointer-up commits, and cancel restores via `_render_drawings` from store-fresh state | The engine already separates validated-geometry ops from persistence (`drag_drawing` never persists); previews must not create store-write pressure per drag tick |
| AP-P10-2 | The page echoes no color on drag commits (empty → normalised to unchanged); explicit colors travel only on color/style edits | Geometry and color are independent channels (A132); the `None`-means-unchanged contract already exists, so no new flag is needed — Task Manager verifies no existing caller depends on `""` overwriting |
| AP-P10-3 | Lock state is read from `DrawingGroup.locked` at the operation surface on every drag/delete attempt, never cached in the drawing row | Group lock is the settled source of truth; caching it in the row would desync on group edits |
| AP-P10-4 | AC-G.1 (visual reference gate) is satisfied by provisional assumption: handles reuse the proven primitives handle glyphs — D50 gates their presence only, introducing no new visual language | A127 settles the render path as proven; presence-gating has probe measurables and needs no confirmed reference |
| AP-P10-5 | R99–R101 are closed pre-clarification risks, not work: Q67 settled the matrix, Q69/S-P10-4 answers the visibility-only-lock concern structurally, Q70 settled (c) Both before P9 built on it | Recording closure so no wave re-litigates them; a future recolor change would arrive as a new requirement |

### Flagged Issues

**None.** Every D50 criterion is satisfiable as written on the existing stack:

- The per-kind matrix rides anchors and geometry functions that already exist
  (`drawing_handle_points`, `drag_drawing_item`); only initiation + gating are added.
- Operation-level lock is enforceable exactly where the owner pinned it (the
  `drag_drawing` initiation/move surface plus the delete path) with probe measurables.
- Stored-color semantics (P9 S-P9-4) plus the `None`-means-unchanged contract already
  implement (c) Both + A132; D50 only constrains commits to geometry-only.
- Persistence + fan-out reuse the settled `_on_drawing_updated` close-out and the D49.4
  pattern with offscreen measurables (A131/Q71).

Status: READY_FOR_TASK_MANAGER

---

## Phase P11 — D51 follow-live viewport for the LWC main chart (no yank while scrolled back) — drafted 2026-10-29

> Companion: `docs/architecture.md` § *Phase P11* (Codebase Summary, S-P11-1…S-P11-5,
> frozen interfaces, non-functional, AR-P11-1…AR-P11-4). Requirements basis (approved
> scope, not re-derived): D51, Journey 44, `AC-D51.1`–`AC-D51.5`, A135, R103,
> Q72–Q76 (answered-owner-confirmed 2026-10-29). `requirements.md` carries
> `Status: READY_FOR_PLAN`. Existing-repo run: `[existing]` / `[new]` / `[new/changed]`
> labels relative to the codebase; **no new module, no new dependency, no schema
> migration, no order code, no data-path change**. One phase only — nothing past the
> P11 build wave is planned. Out of scope: pop-out viewports (main chart only, D51
> register); creation/render/data paths beyond the viewport gating; any visual language
> beyond the go-to-realtime affordance's presence-gating.

### Traceability (requirement → architecture → wave)

| Requirement / journey / AC | Architecture section | Wave |
|---|---|---|
| D51.1 follow-vs-away definition (Q72 TradingView-copy) | S-P11-1 (derived `isFollowing()`; newest-slot-visible) | P11-W1 |
| D51.2 no yank while away; resume only on pan-back/Fit (Q73(a) stay-put) | S-P11-2 (live-update viewport gating) | P11-W2 |
| D51.3 Fit/reset frames all + re-engages + affordance (Q74(a) Fit+re-engage) | S-P11-4; Frozen (Reset affordance D3) | P11-W2 |
| D51.4 per-symbol viewport + follow memory (Q75(a)) | S-P11-5 (Python-side store + range reports) | P11-W3 |
| D51.5 same-symbol preserve / new-symbol follow (Q76(a)) | S-P11-3 (series-replace directive) | P11-W3 |
| Journey 44 (pan away → live bars → Fit → switch → replace) + edge cases | S-P11-1…S-P11-5 | P11-W1…W4 |
| A135 settled owner answers; R103 closed pre-clarification risk | Summary; Non-Functional | — (no wave; recorded as closed) |
| No production behaviour change beyond D51; no skips/xfails; suite green | Non-Functional gate | P11-W4 |

Every item above is addressed somewhere in the architecture AND the waves below; nothing
is narrowed or reinterpreted (the Q72–Q76 option-(a) answers are the owner decisions as
recorded verbatim in `open_questions.md`).

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Every
wave lands its repro test **red-first** (failing on the current tree) before the fix.
Waves are S/M only.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P11-W1 | S | **Follow-state definition + repro probes (D51.1; S-P11-1).** Page-side derived `isFollowing()` (newest bar's logical slot inside the visible logical range); offscreen-queryable follow state; repro-first probes proving the current tree has no follow state and yanks (unconditional `fitToWidth`). | (1) Loaded-at-edge chart reports following; pan/zoom-away chart reports scrolled back (AC-D51.1); (2) probes are red on the current tree (no `isFollowing` surface; `applyOps` refits unconditionally); (3) full offscreen + `node --test` suites green. | Offscreen follow-state probes + JS tests + full suite. |
| P11-W2 | M | **No-yank live path + Fit/reset + go-to-realtime affordance (D51.2/D51.3; S-P11-2, S-P11-4).** Live `update_bar` upserts leave the visible range untouched while away and follow only when following; unconditional refit removed; Fit/reset frames all loaded bars + re-engages follow; affordance appears on new-bars-while-away and invokes `scrollToRealTime`. | (1) Scrolled-back viewport bit-identical across injected live bars; follow stays disengaged (AC-D51.2); (2) pan-back-to-edge or Fit resumes follow; (3) Fit frames all loaded bars, re-engages follow, affordance available (AC-D51.3); (4) affordance invokes the realtime scroll; (5) full suites green. | Viewport-slot assertions before/after injected bars + Fit/affordance suites + full suite. |
| P11-W3 | S | **Per-symbol memory + same/new replacement (D51.4/D51.5; S-P11-5, S-P11-3).** Python-side per-symbol `{range, following}` store fed by throttled page range reports; save on switch-away, restore on switch-back; same-symbol full replace preserves, new-symbol load follows. | (1) Switch away and back restores remembered viewport + follow state (AC-D51.4); (2) same-symbol replace keeps viewport + follow state; new-symbol load starts following (AC-D51.5); (3) zero-bar Fit is a no-op with no error (Journey 44 edge); (4) full suites green. | Per-symbol state + same/new-replacement suites + full suite. |
| P11-W4 | S | **Batch gate: close-out.** Every D51 criterion observably satisfied, nothing else changed, suite green. | (1) All five ACs' checks green; (2) no production behaviour change beyond D51 (diff review — `chart.js` viewport path + view update path only); pop-out/data/order paths untouched; (3) no skipped/xfailed tests added; (4) **full offscreen suite green**. | Full suite + the five-AC checklist. A red suite fails the wave. |

**What stays untouched by every P11 wave:** the bar data path (history/backfill/pacing/aggregation); the Python `update_live_bar` bar-domain contract (still emits `update_bar` ops; only the page's viewport reaction changes); pop-out viewports; the `DrawingController`/`drawing_op`/drag geometry; the `bars`/`alarms`/`drawings` schemas (no migration — the per-symbol store is in-memory session state); the order-code absence (D45/D46); pacing tunables and the port guard.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P11-1 | Follow state is derived on query (newest-slot-visible), never stored as a page flag | A stored flag desyncs on every unobserved gesture (keyboard pan, wheel zoom); derivation from `getVisibleLogicalRange()` + snapshot length is O(1) and cannot drift |
| AP-P11-2 | The per-symbol viewport store is in-memory session state, keyed by upper-cased symbol; nothing persists it across restarts and no migration is added | D51 requires switch-back restore within the session (Journey 44); persistence was never asked for and every comparable UI show/hide toggle in this repo is unpersisted (D10/A36, D44/A76 precedent) |
| AP-P11-3 | Page→Python visible-range reports are throttled (gesture-end + post-update, not per-frame) and are the only new page→Python traffic | Per-move reporting has no latency budget (P10 S-P10-2 precedent); the store only needs switch-away freshness, which gesture-end/post-update reports guarantee |
| AP-P11-4 | AC-G.1 (visual reference gate) is satisfied by provisional assumption: the go-to-realtime affordance reuses the proven in-chart control idiom (existing Reset/zoom controls, D3) — P11 gates its presence and behaviour, introducing no new visual language | Same precedent as AP-P10-4 (handle presence-gating); show/hide + invoke behaviour has probe measurables and needs no confirmed reference |
| AP-P11-5 | R103 is a closed pre-clarification risk, not work: Q72–Q76 settled the threshold and resume rule before any build | Recording closure so no wave re-litigates the definition; a different threshold would arrive as a new requirement |

### Flagged Issues

**None.** Every D51 criterion is satisfiable as written on the existing stack:

- The yank is one unconditional call (`applyOps` → `fitToWidth()`); gating it on a
  derived follow check is additive page logic with probe measurables.
- `scrollToRealTime` / `setVisibleLogicalRange` / `fitContent` all exist in the vendored
  5.2.1 library; no library change is needed.
- Per-symbol memory rides the existing `set_symbol` lifecycle with an in-memory dict —
  no schema, no new module, no new integration.
- Same-vs-new replacement reuses the existing full-replace path with a continuity
  directive; the library preserves the logical range across `setData` unless fitted.

Status: READY_FOR_TASK_MANAGER

---

## Phase P12 — D52 (Batch 27): add `30 mins` (30 D) as a valid chart interval — drafted 2026-10-29

> Companion: `docs/architecture.md` § *Phase P12 — D52 increment* (Codebase Summary, S-P12-1…S-P12-6, frozen
> interfaces, non-functional, AR-P12-1…AR-P12-3). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — Batch 27 (D52), Journey 45, `AC-D52.1`–`AC-D52.8`, lite defaults A136–A141
> (A136 owner-decided per Q77 answered-owner-confirmed), R104–R105, `design_gaps.md` DG99. Hard constraints: **no order code anywhere**
> (D45/D46); live validation is **read-only** (the standalone probe issues historical requests only); the **full offscreen
> suite green is the gate**. Existing-repo run: every wave below modifies existing modules in place; **no
> new module, no new dependency, no schema migration**. One phase only — nothing past the P12 build wave
> is planned. D1–D51 are NOT reopened beyond the recorded timeframe-enumeration extension (`AC-D16.1` now
> reads nine; `AC-D16.8` Given now reads six intraday timeframes; the D43/`AC-D27.9` per-span table gains
> the `30 mins` row). If this decomposed larger than S, the lane is wrong: report back instead of building.

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Every wave is S.
Repro-first where behavior is new: the W1 bucketing tests land **red on the current tree** (unknown
`30 mins` falls back to the 300 s grid) before the fix; the priming-shape case is red-first at the
per-span table assertion (the table has no `30 mins` row) with the branch behavior pinned alongside.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P12-W1 | S | **Data plane: config + bucketing + probe** (S-P12-1, S-P12-2, S-P12-3, S-P12-5; answers DG99's priming half and the R104 risk). One `TIMEFRAME_CONFIG` row inserted between `15 mins` and `1 hour`; `TIMEFRAME_SECONDS` gains the 1800 key with the existing UTC-epoch grid (no anchor change); planner no-logic-change verification; priming docstring row; standalone probe of the new combo. | (1) Config holds the exact new row and no other row changes; (2) 30-minute buckets open on ET clock half-hours (`HH:00`/`HH:30`, `09:30` RTH open on a boundary) across a DST fold, and the forming bar aggregates into the current half-hour bucket; (3) a `30 mins` load plans the configured duration (chunked as needed), applies the `AC-D16.8` floor mode-aware, and detects holes at bar granularity; (4) the probe request completes with no 321-class rejection (a rejection fails the wave and escalates — never a silent shrink); (5) full offscreen suite green. | Offscreen unit/planner/aggregator suites with the new key (red-first bucketing cases) + the standalone probe record + full suite. |
| P12-W2 | S | **Presentation plane: picker + enumeration inventory** (S-P12-1 picker slot, S-P12-4, S-P12-6; answers DG99 and the R105 risk). Picker order with select/load/persist parity; RTH/ETH distinct bar sets with bands + collapse; visibility-m grid verification; burst-minutes pin. | (1) Picker lists `30 mins` between `15 mins` and `1 hour` and it selects/loads/persists like every other intraday timeframe; (2) RTH and ETH loads of `30 mins` return their mode's bars (not identical sets), and session bands + collapse apply as for the other intraday timeframes; (3) visibility dialog opens with every box default-checked and the payload round-trips (the `Minutes` unit row covers `30 mins` — verified, no new row); (4) `minutes_for_timeframe("30 mins")` returns 30.0; (5) full offscreen suite green. | Offscreen picker/mode-parity/dialog/minutes suites + full suite. No live TWS needed. |
| P12-W3 | S | **Batch gate: probe record + non-regression close-out**. The probe outcome on record, every `AC-D52.*` observably satisfied, pre-D52 criteria untouched except the recorded enumeration extension, full suite green. | (1) Probe record present for the `30 mins` / `30 D` combo; (2) `AC-D16.1` "nine timeframes" wording, the `AC-D16.8` six-intraday list, and the `AC-D27.9` added table row verified, `### D41`–`### D51` + marker + Current Tech Stack intact; (3) **full offscreen suite green**. | Full suite + the AC checklist. A red suite or a missing probe record fails the wave. |

**What stays untouched by every P12 wave:** the `req_historical_data` / `req_mkt_data` signatures and
pacing contract; the planner function contracts; the pacing tunables and the port guard; error
ingress/classification; `RealtimeBarsManager` / `StreamHealth` APIs; `BarCache` APIs; the Qt-free
import boundary; the order-code absence; the entire LWC renderer seam; the `bars` schema (no
migration); the eight existing `TIMEFRAME_CONFIG` rows' values and order; the visibility payload shape;
the daily-or-coarser canonical-mode rule (P8 — intraday keeps mode-aware keys).

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| D52.1 / `AC-D52.1` (mapping: `30 mins`→`30 mins`/`30 D`) | S-P12-1; Frozen (eight existing rows) | P12-W1 |
| D52.2 / `AC-D52.2` (ET half-hour buckets, live forming-bar parity) | S-P12-2; Frozen (existing periods + `_period_start`/`_bucket_start` grid) | P12-W1 |
| D52.3 / `AC-D52.3` (planner/backfill: configured duration, `AC-D16.8` floor applies mode-aware, bar-granular holes) | S-P12-3; Frozen (planner contracts) | P12-W1 |
| D52.4 / `AC-D52.4` (RTH/ETH distinct sets, bands + collapse as intraday) | S-P12-4; Frozen (`req_historical_data`, `BarCache`) | P12-W2 |
| D52.5 / `AC-D52.5` (picker entry between `15 mins` and `1 hour`; select/load/persist parity; visibility default-on) | S-P12-1, S-P12-6; Frozen (visibility payload shape) | P12-W2 |
| D52.6 / `AC-D52.6` (priming: `5 secs` branch, span 1800 s inside `[60 S, 3600 S]`) | S-P12-5; Frozen (prime span branches) | P12-W1 |
| D52.7 / `AC-D52.7` (standalone probe + suite green) | S-P12-5; Non-Functional stability gate | P12-W1 (probe) + P12-W3 (record) |
| D52.8 / `AC-D52.8` (history intact; only the recorded enumeration extension) | Frozen (all `[existing]` rows) | P12-W3 |
| Journey 45 (load 30-min chart, toggle modes, successive loads, switch symbols, suite green) | S-P12-1…S-P12-6 | P12-W1…P12-W3 |
| A136–A141 (lite defaults; A136 owner-confirmed) | S-P12-1…S-P12-6 (each default cited at its decision) | P12-W1/P12-W2 |
| R104 (321 rejection → escalate) | AR-P12-1; S-P12-1/S-P12-5 | P12-W1 (probe is the gate) |
| R105 (hardcoded intraday enumerations) | AR-P12-2; S-P12-6 | P12-W2 (inventory checklist) |
| DG99 (enumeration entries for the new timeframe) | S-P12-1/S-P12-5/S-P12-6 | P12-W1 (priming row) + P12-W2 (picker + inventory) |
| Hard constraints: no order code (D45/D46); read-only live; suite-green gate | S-P12-1…S-P12-6; Frozen (order absence, seam) | Every wave |

Every D52 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.
ESC-079 (open, PLAN-routed) is P7 scope, already answered by S-P7-1 — it is not re-planned here.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P12-1 | IBKR's native 30-minute bars anchor compatibly with ET clock half-hours; a systematic phase mismatch, if the first-load comparison shows one, becomes a follow-up rather than a silent re-anchor | Mirrors the recorded D27.8 4h-caveat and AP-P8-1 precedent; the assumption is checkable, not load-bearing for the batch gate |
| AP-P12-2 | The successive-loads reading of the `AC-D16.8` floor (P7 S-P7-1/S-P7-2: per-load cap, oldest-first, persist-and-resume) applies unchanged to `30 mins`; no new floor mechanics are introduced | The floor machinery is timeframe-generic; `30 D` yields ~21 RTH sessions per load, so the floor is met across loads exactly as for the other intraday timeframes |
| AP-P12-3 | AC-G.1 (visual reference gate) does not apply: P12 makes no UI-visual decision — the picker entry is a text label in the existing combo in A140 order, and the visibility grid is unchanged | All P12 outcomes are config/aggregation/planner behaviour with config-assertion and bar-equality measurables |

### Flagged Issues

**None.** Every D52 item is satisfiable as written on the existing stack:

- The new combo rides the existing request shape; IBKR acceptance is probe-verified (`AC-D52.7`),
  and a rejection has a specified escalation (R104) rather than a gap.
- Half-hour bucketing, the predicate membership, the minutes value, and the visibility coverage are all
  mechanical with stated measurables (DG99 resolves inside the waves above).
- The `AC-D16.1` / `AC-D16.8` enumeration extension and the `AC-D27.9` table row are recorded analyst-side
  wording, not Plan reinterpretation.

Status: READY_FOR_TASK_MANAGER

---

## Phase P13 — D49 pop-out robustness (Batch 24 + D49.6 timezone handoff) — drafted 2026-10-29

> Companion: `docs/architecture.md` § *Phase P13* (Codebase Summary, S-P13-1…S-P13-6, frozen
> interfaces, non-functional, AR-P13-1…AR-P13-4). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — Batch 24 (D49), Journey 42, `AC-D49.1`–`AC-D49.7`, A121–A126/A133–A134
> (Q64–Q66 answered 2026-10-28), R96–R98/R102. Hard constraints: **no order code anywhere**
> (D45/D46); offscreen-first acceptance (Q65: no live step named); **full offscreen suite green
> is the gate**; waves S/M only; no skips/xfails; no fine-grained task breakdown (Task Manager's
> job); no per-task tests prescribed. Existing-repo run: every wave modifies existing modules in
> place; **no new module, no new dependency**. One phase only — nothing past the P13 build waves
> is planned. D1–D48 are NOT reopened; D24's criteria stand and are not re-planned.

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Every
wave lands its repro/pinning test **red-first** (failing on the current tree) before the fix,
except where noted (W4 pins green-first by design; W6 is conditional). Waves are S/M only.

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P13-W1 | M | **Cold restore through the data path (D49.1; S-P13-1).** Session-less restore ensures cached bars + timeframe aggregator + realtime subscribe, with the existing history/backfill/pacing path where cache is incomplete. | (1) Repro-first failing test (empty session + saved pop-out → bars present + aggregator exists + subscribed; gapped-cache case issues the backfill request) red on the current tree, green after; (2) already-loaded main-chart symbol adds no second aggregator/subscription; (3) disconnected restore stays a D14-style no-op; (4) full offscreen suite green. | Offscreen restore suites with seeded `BarCache` + failure-injection + full suite. |
| P13-W2 | M | **Transactional attach (D49.2; S-P13-2).** `attach()` unwound exactly on any failure with explicit acquisition-state tracking. | (1) Per-injection-point cases (sync raise, registration raise, save raise) red-first, green after: no stale session view, hold count unchanged by the failed attach, pop-out unregistered, signals disconnected; (2) a failed attach on a shared live session never disturbs other views; (3) full offscreen suite green. | Offscreen injection suites asserting session-view membership + hold count + registry + full suite. |
| P13-W3 | S | **Host-failure error state (D49.3; S-P13-3).** A chart-host that raises on startup shows an in-pop-out error state on the ESC-070 model with the diagnostic log retained. | (1) Broken-host case red-first (blank chart today), green after: error state visible and unambiguous vs no-data, log capture retains the diagnostic entry; (2) copy/layout follows the Q64 owner-confirmed default (no new visual decision); (3) full offscreen suite green. | Offscreen broken-host suites + log-capture assertions + full suite. |
| P13-W4 | S | **Single drawing fan-out (D49.4; S-P13-4).** Pin current behavior first, then de-duplicate at the change point without changing update semantics. | (1) Pinning tests land FIRST on the current tree (fan-out count + end state recorded); (2) post-fix: all-view sync executes exactly once per change with end-state equality to the pinned baseline; (3) signal + per-pop-out wiring kept; (4) full offscreen suite green. | Fan-out-count spies + end-state-equality suites + full suite. |
| P13-W5 | S | **Hold-count verification probe (D49.5 probe half; S-P13-5).** The shared-hold lifecycle probe runs offscreen and its record is committed. | (1) Probe covers main-chart same-symbol reload + pop-out attach/close (+ zero-owner case asserting zero) and records whether the hold count exceeds active owners with a lasting effect; (2) the verification record exists in-repo either way; (3) **no production-code change in this wave**; (4) full offscreen suite green. | Offscreen lifecycle probe + committed record + full suite. |
| P13-W6 | S | **Conditional per-owner fix (D49.5 fix half; S-P13-5).** Lands ONLY if W5 confirms a lasting effect; otherwise no code change. | (1) If confirmed: idempotent per-owner acquire/release (owners: main chart, each pop-out, alarm monitor) with hold count equal to active owners across the W5 lifecycle, green suite; (2) if not confirmed: wave closes with NO code change and the W5 record closes D49.5 as verified (A126/Q66 — verified-close counts as delivered, not dropped); (3) a W6 diff with no W5 probe record fails review (R98). | The W5 lifecycle suites re-run against the fix (or the untouched tree) + full suite. |
| P13-W7 | S | **Timezone handoff create + persist + restore (D49.6; S-P13-6).** Main-chart offset threaded at creation, persisted with the set, applied at restore with the pre-change fallback. | (1) Creation case red-first (hardcoded `0.0` today): new view carries the main chart's non-zero offset; (2) persisted set round-trips the offset; restored view carries it and renders identical time labels for the same seeded bars; (3) pre-change save without the field falls back to the main chart's current offset (never silent UTC); (4) full offscreen suite green. | Offscreen create/restore/label-equality suites + migration read-back cases + full suite. |
| P13-W8 | S | **Batch gate: close-out.** Every D49 criterion observably satisfied, history intact, nothing else changed, suite green. | (1) `AC-D49.1`–`AC-D49.6` checks green (or verified-close with record for D49.5); (2) `AC-D49.7`: `### D41`–`### D48` with reversals, the Existing Repository marker + Current Tech Stack intact, no pre-D49 wording touched; (3) no order code, no new dependency, no skipped/xfailed tests; (4) **full offscreen suite green**. | Full suite + the AC checklist. A red suite fails the wave. |

**What stays untouched by every P13 wave:** D24's pop-out criteria (behavior corrected, criteria
not re-planned); the `bars`/`alarms`/`drawings` schemas (except the one additive
`popouts.tz_offset` column in W7); the `ChartView` seam and LWC renderer; pacing tunables and
the port guard; error ingress/classification; the order-code absence (D45/D46); the Qt-free
`data/` + `services/` import boundary.

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| D49.1 / `AC-D49.1` (restore through data path; repro-first) | S-P13-1; Frozen (`BarCache`, planner) | P13-W1 |
| D49.2 / `AC-D49.2` (transactional attach; per-injection cases) | S-P13-2; Frozen (`detach_view`) | P13-W2 |
| D49.3 / `AC-D49.3` (error state; log retained; Q64 copy) | S-P13-3; Frozen (`chart_engine_failure_message`) | P13-W3 |
| D49.4 / `AC-D49.4` (single fan-out; pin-first; semantics unchanged) | S-P13-4; Frozen (signal contracts) | P13-W4 |
| D49.5 / `AC-D49.5` (verify-first; conditional fix; verified-close) | S-P13-5 | P13-W5 (probe) + P13-W6 (gated fix) |
| D49.6 / `AC-D49.6` (tz handoff create + persist/restore + fallback) | S-P13-6; Frozen (`create_chart_view` seam) | P13-W7 |
| D49.7 / `AC-D49.7` (history intact) | Frozen (all `[existing]` rows) | P13-W8 |
| Journey 42 (cold restore, attach/host survival, drawing/hold exactness, tz) | S-P13-1…S-P13-6 | P13-W1…P13-W8 |
| A121–A126/A133–A134 (analyst defaults; A124/A126 owner-confirmed) | S-P13-1…S-P13-6 (each default cited at its decision) | P13-W1…P13-W7 |
| R96 (cold-start pacing pressure) | AR-P13-1; S-P13-1 | P13-W1 (cache-first + stagger note) |
| R97 (cleanup vs concurrent update) | AR-P13-2; S-P13-2 | P13-W2 (disconnect-first + under-update case) |
| R98 (verify read as build license) | AR-P13-3; S-P13-5 | P13-W5/W6 (probe-record gate) |
| R102 (pre-change saves lack the offset field) | AR-P13-4; S-P13-6 | P13-W7 (fallback cases) |
| Hard constraints: no order code (D45/D46); offscreen-only (Q65); suite-green gate | S-P13-1…S-P13-6; Frozen (order absence, seam) | Every wave |

Every D49 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.
D49.5's conditional wave is a gated decision the requirements specify (A126/Q66), not a gap.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P13-1 | AC-G.1 (visual reference gate) is satisfied by owner confirmation: D49.3's copy/layout is the Q64-accepted ESC-070-model default, and D49 has no other UI-visual decision | Q64 accepted the standing default verbatim; all D49.3 outcomes (visible, unambiguous, log retained) are probe-measurable without pixel details |
| AP-P13-2 | "Hold actually acquired" (A122) means `ensure_rt_subscribed` returned without raising — whether it created the subscription or bumped the refcount — and a raise means no hold was acquired | Matches the refcount contract in source (`_rt_holders += 1` vs subscribe-and-set-1); the flag is set at the single call site, so cleanup can never misattribute another view's hold |
| AP-P13-3 | The conditional per-owner fix (if W5 confirms) keys acquire/release by owner identity (main chart, each pop-out, alarm monitor) with idempotent release; the exact key type is a Task Manager/Build detail | `AC-D49.5` fixes the owner set and the idempotence property; the mechanism is standard refcount-by-owner and needs no architectural invention |
| AP-P13-4 | The `popouts.tz_offset` column follows the existing additive-migration precedent (nullable/additive, old rows readable, A134 fallback in code — never silent UTC) | Same pattern as the D24.9 additive `popouts` table and the D39 `Alarm.params` additive migration; no destructive schema step |
| AP-P13-5 | Disconnected restore stays a D14-style no-op (status message, no request) and a mid-session host crash stays outside D49.3 (existing crash handling owns it) | Both are Journey 42 edge cases carried verbatim; neither wave re-litigates them |

### Flagged Issues

**None.** Every D49 item is satisfiable as written on the existing stack:

- Cold restore reuses the standing cache/aggregator/RT/backfill machinery (A121) with
  repro-first measurables (`AC-D49.1`); pacing pressure has a specified handling (R96),
  not a gap.
- Transactional attach is mechanical step-flagging with per-injection-point measurables
  (`AC-D49.2`); the race has a specified ordering (R97).
- The error state reuses the owner-confirmed ESC-070 model at a new site (A123/A124, Q64).
- Single fan-out is call-site dedupe with pin-first semantics preservation (A125).
- The hold-count item is explicitly verify-first with verified-close as a legitimate
  delivered outcome (A126, Q66) — the gate is specified (R98), not missing.
- The timezone handoff threads an existing value through creation/persistence/restore
  with a stated fallback (A133/A134); the pre-change-save case has a specified handling
  (R102).

Status: READY_FOR_TASK_MANAGER

---

## Phase P14 — D53 persistent backfill-state indicator + cache-current guard (Finding 2, TWS probe 20261103) — drafted 2026-11-03

> Companion: `docs/architecture.md` § *Phase P14* (Codebase Summary, S-P14-1…S-P14-4, frozen
> interfaces, non-functional, AR-P14-1…AR-P14-4). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — Batch 28 (D53), Journey 46, `AC-D53.1`–`AC-D53.4`, analyst defaults A142–A144
> (Q78–Q80 non-blocking confirmations with logged defaults — build proceeds on them; no blocking item),
> R106–R107, `design_gaps.md` DG100. Hard constraints: **no order code anywhere** (D45/D46);
> offscreen-first acceptance (the probe file is evidence, never a gate); **full offscreen suite green
> is the gate**; waves S/M only; no skips/xfails; no fine-grained task breakdown (Task Manager's
> job); no per-task tests prescribed. Finding 1 needs NO code change — watchdog tuning and TWS-side
> causes are out of scope and no wave touches them. Existing-repo run: every wave modifies existing
> modules in place; **no new module, no new dependency, no schema migration**. One phase only — nothing
> past the P14 build waves is planned. D1–D52 are NOT reopened.

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Repro-first where
behavior is new: the W1 separation case and the W2 per-path cases land **red on the current tree**
(no indicator identity survives `showMessage` churn today; no per-path clearing exists) before the fix;
the W3 guard case is red-first (the current no-plans branch claims without consulting the planner).

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P14-W1 | M | **Persistent indicator, separate surface (D53.1; S-P14-1).** Permanent status-bar widget reporting at minimum in-flight count, queue count, elapsed time, current reqIds; raised on wave issue (queue-only waves included), refreshed on wave events, immune to transient `showMessage` traffic. | (1) Repro-first: offscreen wave + injected unrelated `showMessage` (account-summary receipt shape) — indicator identity/state unchanged across the churn, red today (no such widget), green after; (2) content asserts the at-least set (counts + elapsed + reqIds) at multiple wave instants incl. the queue-only instant; (3) all existing `showMessage` texts/timings unchanged; (4) full offscreen suite green. | Offscreen indicator suites with seeded `BarCache` + message injection + full suite. |
| P14-W2 | M | **Terminal-path lifecycle with coalesced-keep (D53.2; S-P14-2).** Indicator clears only on the four existing terminal paths; a coalesced same-triple reload keeps it with the elapsed baseline unreset. | (1) Per-path cases red-first, green after: normal completion / stranded (watchdog) finalization / cancellation (symbol switch + new-triple load) / disconnect each clear the indicator exactly once; (2) Branch-A same-triple reload mid-wave: no new reqIds, generation unchanged, indicator keeps running with elapsed unreset; (3) mode-switch mid-wave clears-and-reraises as a new wave (not a keep); (4) full offscreen suite green. | Offscreen lifecycle suites driving the real session callbacks + failure injection + full suite. |
| P14-W3 | S | **Cache-current guard + batch gate (D53.3/D53.4; S-P14-3/S-P14-4).** No freshness claim while a wave is in flight or the planner reports missing spans; stranded end keeps the `AC-D16.4` shortfall; history intact; suite green. | (1) In-flight and planner-missing cases assert absence of the claim family (literal + equivalents); (2) stranded-with-missing-days ends on the verbatim shortfall (wording unchanged); (3) zero-missing + no-wave loads still report currency exactly as today; (4) `AC-D53.4`: `### D41`–`### D52` with reversals, the marker sentence + Current Tech Stack intact, no pre-D53 wording touched; (5) **full offscreen suite green**. | Offscreen guard suites + the AC checklist. A red suite fails the wave. |

**What stays untouched by every P14 wave:** the watchdog bounds and strand timing; the pacing
budgets and continuation/prime precedence; the `req_historical_data` / `req_mkt_data` signatures;
the planner function contracts; `BarCache` APIs; error ingress/classification; the realtime/stream
APIs; the port guard; the LWC renderer seam; the `bars` schema (no migration); the order-code
absence; every existing `showMessage` text and the shortfall wording.

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| D53.1 / `AC-D53.1` (persistent indicator; at-least content; survives transient traffic) | S-P14-1; Frozen (`showMessage` sites read, not reworded) | P14-W1 |
| D53.2 / `AC-D53.2` (clears only on four terminal paths; coalesced reload keeps with baseline) | S-P14-2; Frozen (wave lifecycle hooked, not reshaped) | P14-W2 |
| D53.3 / `AC-D53.3` (no current-claim while in flight or spans missing; stranded keeps shortfall) | S-P14-3; Frozen (planner contracts, shortfall wording) | P14-W3 |
| D53.4 / `AC-D53.4` (history intact) | Frozen (all `[existing]` rows) | P14-W3 |
| Journey 46 (watch a wave start-to-finish; per-path + coalesced + freshness steps; queue-only/disconnect/mode-switch/zero-bar/account-burst edges) | S-P14-1…S-P14-4 | P14-W1…P14-W3 |
| A142 (permanent status-bar widget default; at-least content set) / Q78/Q79 | S-P14-1 | P14-W1 |
| A143 (four clearing paths; coalesced keep with baseline) | S-P14-2 | P14-W2 |
| A144 (claim-class guard; existing phrasing for copy) / Q80 | S-P14-3 | P14-W3 |
| R106 (content set may refine) | AR-P14-1; S-P14-1 | P14-W1 (at-least assertions) |
| R107 (transient-caller regression) | AR-P14-2; S-P14-1 | P14-W1 (injected-traffic case) + review check |
| DG100 (widget + copy are Plan details) | S-P14-1/S-P14-3 | P14-W1 (widget) + P14-W3 (copy) |
| Finding-1 boundary (no watchdog/TWS change) | S-P14-4 | Every wave (read-only relationship) |
| Hard constraints: no order code (D45/D46); offscreen-only; suite-green gate | S-P14-1…S-P14-4; Frozen (order absence, seam) | Every wave |

Every D53 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P14-1 | Q78–Q80 proceed on their logged defaults without waiting for answers: (a) permanent status-bar widget, (b) the probe-named set as the at-least set, (c) claim-class gating with existing status-bar phrasing for copy | The orchestration preamble and the requirements header both direct proceeding on defaults; every default is evidence-backed and `AC-D53.1`/`AC-D53.3` are written so a refinement cannot invalidate the build (R106) |
| AP-P14-2 | AC-G.1 (visual reference gate) does not apply: the indicator widget and any copy follow standing defaults (A142/A144, DG100) with measurable persistence/content/lifecycle/guard assertions, never pixel or exact-string assertions | DG100 records the exact-widget-and-copy choice as a Plan detail on the D49.3/Q64 precedent; all D53 outcomes are probe-measurable without a confirmed reference |
| AP-P14-3 | The wave-start timestamp lives on the session (in-memory, set on first plan issue, cleared on termination); the indicator's elapsed is a pure read of it | Matches the session-owned wave-state pattern (P7); persisting it would add a store for a display-only value |
| AP-P14-4 | Existing transient `showMessage` texts and timings are kept verbatim (including the mid-wave "backfilling N chunk(s)…" and the coalesced-reload notice) — the indicator is additive, not a message replacement | `AC-D53.1` requires the indicator to survive that traffic, not to silence it; rewording live user-facing copy is unasked scope |
| AP-P14-5 | The "Cache current" gate covers the no-plans branch and the finalize path through one predicate; a wave in flight alone (even with zero currently-known missing spans) suppresses the claim | Finding 2's +60 s instant (reqIds in flight, 0 cached bars) is precisely an in-flight claim risk, independent of what the planner last reported |

### Flagged Issues

**None.** Every D53 item is satisfiable as written on the existing stack:

- The persistent surface is a Qt-construction property (permanent widget outside the
  transient slot) with an injected-traffic measurable (`AC-D53.1`); the over-reading
  risk has a specified handling (R106 at-least set; Q78/Q79 non-blocking), not a gap.
- The four clearing paths plus the coalesced-keep case all exist as specified behaviour
  with per-path measurables (`AC-D53.2`); the mechanism risk is specified (R107), not
  missing.
- The guard is a planner read plus a two-site predicate with claim-class absence
  measurables (`AC-D53.3`); copy without a confirmed reference is a recorded default
  (A144/Q80/DG100), not a gap.
- Finding 1 is explicitly out of scope per the owner directive — recorded as the S-P14-4
  scope guard, not as an escalation.

Status: READY_FOR_TASK_MANAGER

## Phase P15 — 10-second target on load chart (D54) — drafted 2026-11-04

> Companion: `docs/architecture.md` § *Phase P15* (Codebase Summary, S-P15-1…S-P15-4, frozen
> interfaces, non-functional, AR-P15-1…AR-P15-4). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — Phase P15 (D54), Journey 47, `AC-D54.1`–`AC-D54.4` FINAL
> (A148 target reading; Q81–Q83 non-blocking confirmations with logged defaults — build proceeds
> on them; no blocking item), A145–A148, R108–R109, `design_gaps.md` DG101. Hard constraints:
> **no order code anywhere** (D45/D46); offscreen-first acceptance with clock control (no
> live-TWS step named); **full offscreen suite green is the gate**; waves S/M only; no
> skips/xfails; no fine-grained task breakdown (Task Manager's job); no per-task tests
> prescribed. Finding 1 / TWS-side silence causes and watchdog retuning are out of scope and
> no wave touches them; D53 is referenced, not reopened (no D53 criterion changes, no new
> surface, no copy rewrite). Existing-repo run: every wave modifies existing modules in
> place; **no new module, no new dependency, no schema migration**. One phase only — nothing
> past the P15 build waves is planned. D1–P14 are NOT reopened.

### Phases (milestones — Task Manager decomposes each wave into tasks with tests)

One commit per wave. Waves run in order; a later wave depends on all earlier ones. Repro-first where
behavior is new: the W1 expiry-render case lands **red on the current tree** (no T0+10 s verdict
exists today — an incomplete wave at T0+10 s renders nothing new and asserts no partial/shortfall
verdict) before the fix; the W2 continuation case is red-first (today nothing distinguishes
post-expiry background fill from the pre-expiry wave, and no seam pins disconnect-wins or
coalesced-T0); the W3 surfacing case is red-first (today no partial-vs-complete distinction exists
on the indicator and the expiry instant consults no freshness gate).

| Wave | Size | Goal (which inputs it delivers) | Acceptance criteria | Validation method |
|---|---|---|---|---|
| P15-W1 | M | **Expiry verdict at T0+10 s (D54.1; S-P15-1).** T0 anchored at Load Chart invocation (the stamped-once wave-start baseline); a single-shot expiry fires once per wave and, only when the wave is still incomplete, renders arrived bars plus the verbatim `AC-D16.4` shortfall for the missing remainder. | (1) Repro-first: offscreen clock-controlled wave forced incomplete at T0+10 s — partial bars present + shortfall marker within the bound, red today, green after; (2) a 9.9 s completion never takes the expiry path; completion exactly at T0+10.0 s counts as complete (single-sided bound); (3) zero-bar expiry lists all missing days as shortfall; (4) full offscreen suite green. | Offscreen expiry suites with clock control + seeded `BarCache` + full suite. |
| P15-W2 | M | **Background-continue with lifecycle seams (D54.2; S-P15-2).** No 10 s cancel path: the wave continues past expiry with the D53 indicator still running and the chart updating as bars land; normal completion / stranded finalization ends the wave as today; disconnect wins over a pending expiry; mode-switch / new-triple re-anchors T0; coalesced keep holds the original T0. | (1) Wave-state + indicator-state assertions past T0+10 s (in-flight continues, indicator running, late bars render), red-first, green after; (2) disconnect at T0+9.9 s finalizes via the disconnect path (expiry never fires on the dead wave); (3) mode-switch / new-triple mid-wave cancels the old wave (old expiry disarmed) and re-anchors T0; coalesced same-triple reload keeps the original T0 without extension; (4) full offscreen suite green. | Offscreen lifecycle suites driving the real session callbacks + failure/disconnect injection + clock control + full suite. |
| P15-W3 | S | **Expiry surfacing + batch gate (D54.3/D54.4; S-P15-3/S-P15-4).** Partial-vs-complete distinction on the existing D53 indicator at/after a miss; `AC-D16.4` shortfall visible with no current-cache claim while spans are missing; history intact; suite green. | (1) In-flight/stranded/complete expiry cases assert indicator state + shortfall presence + freshness-claim absence (claim family, never one literal), red-first, green after; (2) a wave complete by T0+10 s surfaces as complete through the unchanged path; (3) `AC-D54.4`: `### D41`–`### D53` with reversals, the marker sentence + Current Tech Stack intact, no pre-P15 wording touched; (4) **full offscreen suite green**. | Offscreen surfacing suites + the AC checklist. A red suite fails the wave. |

**What stays untouched by every P15 wave:** the watchdog bounds and strand timing; the pacing
budgets and continuation/prime precedence; the `req_historical_data` / `req_mkt_data` signatures;
the planner function contracts; `BarCache` APIs; error ingress/classification; the realtime/stream
APIs; the port guard; the LWC renderer seam; the `bars` schema (no migration); the order-code
absence; every existing `showMessage` text, the D53 indicator texts, and the shortfall wording.

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| D54.1 / `AC-D54.1` (10 s target verdict: partial bars + shortfall at miss; 9.9 s / exact-boundary / zero-bar edges) | S-P15-1; Frozen (`load_chart` T0/coalesced contract, shortfall wording) | P15-W1 |
| D54.2 / `AC-D54.2` (background-continue; D53 lifecycle unchanged; no 10 s cancel) | S-P15-2; Frozen (wave lifecycle hooked, not reshaped) | P15-W2 |
| D54.3 / `AC-D54.3` (D53 surface partial-vs-complete + `AC-D16.4` shortfall + no current-claim; completed-by-bound reads complete) | S-P15-3; Frozen (`set_backfill_state` / `clear_backfill_indicator` / `_is_cache_current`) | P15-W3 |
| D54.4 / `AC-D54.4` (history intact) | Frozen (all `[existing]` rows + P14 carry-forward) | P15-W3 |
| Journey 47 (load against the bound; render / background / surfacing steps; 9.9 s / zero-bar / disconnect-wins / coalesced-T0 / mode-switch-re-T0 / exact-boundary edges) | S-P15-1…S-P15-4 | P15-W1…P15-W3 |
| A145 (T0 = click/invocation; single-sided exact-boundary bound) | S-P15-1 | P15-W1 |
| A146 (main-chart loads; pop-out restore inherits, no separate criterion) | S-P15-4 | Every wave (same history/backfill path) |
| A147 (mechanism is Plan-level) | S-P15-1…S-P15-4 | Every wave |
| A148 ("ideally ≤10 s" is a target; Q81–Q83 miss semantics only on miss) / Q81/Q82/Q83 | S-P15-1 / S-P15-2 / S-P15-3 | P15-W1 / P15-W2 / P15-W3 |
| R108 (25–76 s legitimate latencies exceed the target) | AR-P15-1; S-P15-1/S-P15-3 | P15-W1 (graceful path) + P15-W3 (honest surfacing) |
| R109 (background-continue surprise vs cancel-strand) | AR-P15-2; S-P15-2 | P15-W2 (continue + seam cases) |
| DG101 (cap-vs-latency tension; mechanism is Plan's job) | S-P15-1…S-P15-4 | P15-W1…P15-W3 |
| Finding-1 / TWS-side boundary (no watchdog/TWS change) | S-P15-4 | Every wave (read-only relationship) |
| Hard constraints: no order code (D45/D46); offscreen-only; suite-green gate | S-P15-1…S-P15-4; Frozen (order absence, seam) | Every wave |

Every D54 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Assumptions (plan-level only)

| # | Assumption | Rationale |
|---|---|---|
| AP-P15-1 | Q81–Q83 proceed on their logged defaults without waiting for answers: (a) partial bars + shortfall, (b) background-continue, (c) D53 indicator + `AC-D16.4` shortfall with claim-class gating | The orchestration preamble and the requirements header both direct proceeding on defaults; every default is evidence-backed and `AC-D54.1`–`AC-D54.3` are written so a refinement changes only the named assertion, never the target, lifecycle, or guard |
| AP-P15-2 | AC-G.1 (visual reference gate) does not apply: the expiry verdict and any partial/complete distinction follow standing D53 defaults (A142/A144, DG100 carried forward) with measurable render/lifecycle/guard assertions, never pixel or exact-string assertions | DG100 records the widget-and-copy choice as a Plan detail; all D54 outcomes are clock-controlled offscreen-measurable without a confirmed reference |
| AP-P15-3 | T0 is the stamped-once `_backfill_wave_start` baseline (set at wave raise, never reset by refresh or coalesced keep, cleared only with the indicator); the expiry is a single-shot timer armed per wave and disarmed on every terminal path | Reuses the P14 baseline semantics so the Journey 47 coalesced no-extension edge holds by construction; a per-wave single firing needs no second lifecycle that could drift from the wave |
| AP-P15-4 | A pop-out restore riding the history/backfill path inherits the same verdict semantics with no separate criterion; no pop-out-specific wave is planned | A146 records the scope; the restore path is the same machinery, so a second cap would fork the requirement for no behavioural difference |
| AP-P15-5 | The "10 seconds or less" owner wording is a performance target for the common path (A148), not a fetch-acceleration mandate: waves optimize the verdict path and degrade gracefully, and no wave re-pages, re-primes, retunes, or re-times fetching to chase the bound as an end in itself | A147/A148 plus the R108 latency evidence: deep loads legitimately exceed the bound, so the satisfiable reading is verdict-by-bound plus honest miss semantics |

### Flagged Issues

**None.** Every D54 item is satisfiable as written on the existing stack:

- The expiry verdict is a T0-anchored hook plus the existing render/shortfall path
  with clock-controlled measurables (`AC-D54.1`); the cap-vs-latency tension has a
  specified handling (A148 target reading; Q81 non-blocking), not a gap.
- Background-continue reuses the existing terminal paths with per-seam measurables
  (`AC-D54.2`); the continue-vs-cancel fork is decided by default (Q82a), not
  missing.
- Surfacing reuses the D53 indicator and the standing shortfall/gate with
  claim-class absence measurables (`AC-D54.3`); copy without a confirmed reference
  is a recorded default (A144/Q83/DG100 carried forward), not a gap.
- Finding 1 / TWS-side causes and watchdog retuning are explicitly out of scope
  per the owner directive — recorded as the S-P15-4 scope guard, not as an
  escalation.

Status: READY_FOR_TASK_MANAGER

---

## Phase P16 — Documentation consolidation (D55, docs-only) — drafted 2026-11-04

> Companion: `docs/architecture.md` § *Phase P16* (Codebase Summary, S-P16-1…S-P16-4,
> frozen interfaces, non-functional, AR-P16-1…AR-P16-4). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P16 (D55),
> Journeys 48–50, `AC-D55.1`–`AC-D55.10` FINAL (Q84–Q87 all answered 2026-11-04; no
> blocking item), A149–A155, R110–R113, `design_gaps.md` DG102–DG105. Full authority:
> `docs/documentation_consolidation_plan.md` Phases 0–8 + disposition matrix + conditional
> deletion candidates. Hard constraints: **docs-only batch** (A149) — no wave edits `ui/`,
> `ibkr/`, `services/`, `data/`, `tests/`, packaging, or schemas; the final diff is
> docs-only and generated/cache/vendored outputs follow the build/ignore policy; **no
> product test run** — verification is the `AC-D55.9` docs-only review (stale-claim grep,
> link/reference/commit/status checks), never the offscreen suite; waves S/M only; no
> fine-grained task breakdown (Task Manager's job); no per-task tests prescribed.
> **D1–P15 are NOT reopened** — every edit lands as an appended addendum, banner, pointer,
> or annotation; history is never rewritten (A150, DOC-4 pattern). One phase only — nothing
> past the D55 consolidation is planned.

> **Pre-landed work (recorded, NOT re-planned).** Two owner-answered items already sit in
> the working tree and no wave redoes them: **Q84** — `services/sound_service.py:3` is
> already reworded to the self-contained comment-only line (numpy synthesis of the Web
> Audio alarm chime; the `dev_docs/delta.md` §3 citation is gone); **Q86** — `dev_docs/`
> (5 files) is already deleted. Waves below **verify** these states (reference check,
> dangling-citation grep) but never re-edit or revert them. The Q84 edit itself travels as
> a tracked micro-task pipeline change per the Q84 answer, never a hand-edit — and P16
> prescribes no further source edit of any kind.

### Traceability (requirement → architecture → wave)

| Requirement / input | Architecture section | Wave |
|---|---|---|
| D55.1 / `AC-D55.1` (inventory + cross-reference map, no deletions) + Journey 48 | S-P16-1; Frozen (code contracts read, never edited) | P16-W1 |
| D55.2 / `AC-D55.2` (fact sheet, per-fact citations; Q85-dependent facts marked open) + DG103 | S-P16-1 | P16-W1 |
| D55.3 / `AC-D55.3` (README authority blocks, per-doc metadata, map as index) + Journey 48 | S-P16-1 | P16-W1 |
| D55.4 / `AC-D55.4` (usage.md canonical live-only; USAGE.txt pointer; parity claim qualified) + Journey 50 + Q85 + R110 | S-P16-2; Frozen (port guard, engine factory) | P16-W2 |
| D55.5 / `AC-D55.5` (six-file P6 reconciliation) + Journey 49 + DG104 + R110 | S-P16-3; Frozen (gate disposition, parity matrix) | P16-W3 |
| D55.6 / `AC-D55.6` (P7 cap-as-maximum addendum; 50-vs-100 reconcile-or-open) + DG102 + A154 | S-P16-3 | P16-W3 |
| D55.7 / `AC-D55.7` (cumulative-spec navigation; archive moves with link checks) + DG105 | S-P16-3 | P16-W3 |
| D55.8 / `AC-D55.8` (disposition ledger; Q86/Q87 end states; investigations indexed) + Journey 48 + R111 + A153 | S-P16-4 | P16-W4 |
| D55.9 / `AC-D55.9` (final consistency review, docs-only) + R113 | S-P16-4 | P16-W4 |
| D55.10 / `AC-D55.10` (history intact) | Frozen (all pre-P16 criteria byte-identical) | Every wave (guard) |
| A149–A155, R110–R113, DG102–DG105, Q84–Q87 | S-P16-1…S-P16-4 | Every wave |
| Hard constraints: no order-code/product-code touch; no suite-meaning change | S-P16-4; Frozen (order absence) | Every wave |

Every D55 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Waves

Each wave is a milestone-sized docs changeset, coarser than tasks; Task Manager decomposes
each into file-level tasks with grep/measurable checks. Waves are ordered; a later wave
depends on all earlier ones unless stated. `touches_files` notes list the doc files a wave
touches. **No wave touches a source, test, packaging, or schema file.**

### P16-W1 — Inventory + fact reconciliation + navigation/labels (D55.1–D55.3; plan Phases 0–2) — size S

- **Goal:** the corpus is inventoried without deleting anything, the disputed facts are
  pinned to source with citations, and every current doc carries short role/status metadata
  so a new contributor lands on the canonical answer per Journey 48.
- **Covers:** D55.1–D55.3; `AC-D55.1`–`AC-D55.3`; Journey 48; A149/A150/A151/A152/A155;
  DG102 (opened), DG103, DG105 (opened); R112.
- **Deliverables:**
  - Preserved-working-state note + tracked/untracked inventory classified per the plan
    (normative / user-guidance / navigation / historical-evidence / one-off diagnostic /
    generated-vendored) + filename/heading cross-reference map (scripts, packaging, tests,
    tooling readers of affected docs). **No file deleted in this wave** (`AC-D55.1`).
  - Fact sheet with one source citation per fact: (a) LWC-only status
    (`ui/chart_view.py::create_chart_view` + P6-T13 commit/gate, waived-not-satisfied
    preserved per A152); (b) connection truth — host/port/client-ID per
    `config/settings.py`, account-mode per answered Q85 (live-only); (c) P7 cap as a
    per-load **maximum** with the three plan examples, per-load (coalesced/cancel-refund)
    definition, and the `AC-D16.8` requirement-vs-plan-interpretation separation;
    (d) spike labelled stub/call-shape with real-runtime evidence kept separate
    (vendored v5.2.1, API calls, host, pixel/interaction per A155); (e) P7/P8
    approval-vs-built dating with review/task-graph/as-built links. Unresolved facts
    (notably 50-vs-100 per A154/DG102) stay explicitly open, never guessed.
  - `docs/README.md` one-sentence status + authority table + current-work + historical +
    ownership blocks; short role/status/as-of/canonical/supersedes metadata on every
    current normative doc; `docs/codebase-map.md` reads as a module index (contradictory
    status prose removed by append-only correction, never silent rewrite).
- **Dependencies:** none (first wave; builds on changesets 1–2 as the executed prefix
  per A151 — continued, never redone or reverted).
- **`touches_files`:** `docs/README.md`, `docs/codebase-map.md` (index pass only),
  the new inventory/fact-sheet records (location per Task Manager), per-doc metadata
  headers. No overlap with any other wave's files except the W3/W4 addenda targets,
  which W1 does not edit.
- **Exit condition:** inventory + map present with zero deletions attributed to this wave;
  every fact-sheet row carries its citation; the Journey 48 walk lands on the canonical
  doc per question class.

### P16-W2 — User-guide live-only correction (D55.4; plan Phase 3) — size S

- **Goal:** `usage.md` becomes the single canonical full guide stating the Q85 live-only
  truth, and `USAGE.txt` becomes its short pointer — never two divergent full guides.
- **Covers:** D55.4; `AC-D55.4`; Journey 50; Q85 (answered: live-only); R110 (resolved by
  the Q85 answer); DG103 (engine-key wording follows source).
- **Deliverables:**
  - `usage.md` (canonical): one engine iff source confirms P6-T13 (no false opt-in or
    default; `NDT_CHART_ENGINE`/QSettings behaviour per source verification, never memory
    — DG103); port/account per answered Q85 (**live-only** — the paper-on-7496 sentences
    at `usage.md:106–107` and the port-guard bullet are corrected away); prerequisites,
    commands, packaging, DB path (incl. `DB_PATH` override), features, limitations
    refreshed; as-of date + troubleshooting/current-status link; any "parity complete"
    claim removed or qualified against parity records and known rendering defects.
  - `USAGE.txt`: short pointer/quick-start (or generated equivalent) — its paper-on-7496
    sentences corrected identically; the two files agree by construction.
- **Dependencies:** P16-W1 (fact sheet fixes the connection truth first; guides are never
  corrected on a guess).
- **`touches_files`:** `usage.md`, `USAGE.txt`. No overlap with any other wave.
- **Exit condition:** guide claims grep-clean against source/config on engine, port,
  account-mode, and DB path; `usage.md`/`USAGE.txt` agree (one full guide + one pointer);
  the paper-on-7496 grep returns zero.

### P16-W3 — Migration + backfill + navigation records (D55.5–D55.7; plan Phases 4–6) — size M

- **Goal:** the P6 chart-engine end state, the P7 cap reading, and the cumulative-spec
  navigation all agree in one coordinated pass — addenda only, approvals byte-identical.
- **Covers:** D55.5–D55.7; `AC-D55.5`–`AC-D55.7`; Journey 49; DG102/DG104/DG105; A152/A154.
- **Deliverables:**
  - Six-file P6 reconciliation in one changeset (`AC-D55.5`): `docs/architecture.md`
    (as-built T13 + gate disposition, plan-vs-delivered separated),
    `docs/codebase-map.md` (LWC-only engine/paths/counts, no retained-pyqtgraph claims),
    `docs/lwc_parity_matrix.md` (parity-vs-cutover structurally separated — distinct
    columns/sections, never a one-time relabel per DG104; no accepted row claiming a
    removed engine present/default; waived/retired/linked), `docs/code_review/review_log_P6.md`
    (**dated addendum only**, original review text untouched),
    `docs/phase-changelog.md` (P6/T13 outcome + commit + gate), `docs/CHANGELOG.md`
    (concise P6/P7/P8 index or pointer to phase-changelog per DG105). Every T13 reference
    preserves waived-not-satisfied (A152); Journey 49 contradiction grep returns zero.
  - P7 backfill wording as a coordinated addendum (plan + architecture + P7 review + P7
    task-manager notes, `AC-D55.6`): cap-as-**maximum** with the three plan examples, the
    per-load (coalesced/cancel-refund) definition, the 50-vs-100
    reconciliation-or-explicit-open (source `config/settings.py` + P7 assertions decide;
    otherwise recorded open per A154/DG102 — never silently chosen), and the
    approval-preserving delta note; `AC-D16.8` requirement text referenced, never restated
    (RG-P7-1 stays Analyst debt).
  - Cumulative-spec navigation (`AC-D55.7`): short current-baseline block atop each
    canonical file (current architecture, active phase, unresolved requirements, as-built
    changelog link); uniform status/commit/evidence/supersession metadata on increments;
    only self-contained completed history moves to `docs/archive/` after link/tooling
    checks; repeated full summaries become cross-references.
- **Dependencies:** P16-W1 (fact sheet + inventory precede all reconciliation).
- **`touches_files`:** `docs/architecture.md` (P6 addendum), `docs/codebase-map.md`,
  `docs/lwc_parity_matrix.md`, `docs/code_review/review_log_P6.md` (addendum),
  `docs/phase-changelog.md`, `docs/CHANGELOG.md`, `docs/plan.md` (P7 addendum),
  `docs/plan_review_P7.md` + `docs/tasks/task_manager_notes_P7.md` (deltas),
  canonical-file baseline blocks. No overlap with W2's files; W4 deletes nothing W3 moves.
- **Exit condition:** the six P6 files agree per Journey 49; cap-as-target grep returns
  zero; the approval records are byte-identical apart from appended deltas; link/reference
  checks pass before and after any archive move.

### P16-W4 — Disposition + final consistency review (D55.8–D55.9 + D55.10 guard; plan Phases 7–8) — size M

- **Goal:** every in-scope file lands in exactly one disposition bucket with evidence, the
  approved deletions execute, and the final docs-only review certifies the corpus clean —
  with pre-P16 history byte-identical.
- **Covers:** D55.8–D55.9; `AC-D55.8`–`AC-D55.10`; Journey 48; Q86/Q87 (answered); R111/R113;
  A153.
- **Deliverables:**
  - Disposition ledger (`AC-D55.8`): every file in exactly one bucket (keep-current /
    keep-historical-bannered / pointer-or-merge-after-audit /
    conditional-deletion-candidate) with condition evidence; audit records preserved by
    default; deletion only after unique content is migrated/retired AND references checked.
  - Deletions per answered Q86/Q87: `dev_docs/` already deleted pre-landing — W4 runs the
    reference check (cross-reference map + dangling-citation grep for the old code comment)
    rather than re-deleting; legacy unsuffixed logs (`docs/code_review/review_log.md`,
    `docs/tasks/task_manager_notes.md`) + generated precheck output
    (`docs/code_review/precheck.json`, `docs/code_review/precheck.md`) deleted **without
    archive** per Q87 (verify each has a suffixed successor carrying the live record
    before deleting). Proposals stay historical (archive optional after link audit); the 16
    investigation files are indexed, never destroyed (A153).
  - Final consistency review (`AC-D55.9`, docs-only, no product test run): stale-claim grep
    (pyqtgraph default, dual-engine, T13 undispatched, owed live session, parity-complete,
    legacy account/port instructions incl. paper-on-7496, spike API names as runtime
    evidence — plus paraphrase sampling per R113), link/filename/phase-ID/commit/status
    checks, guide-vs-source-vs-plan cross-checks, historical labelling, addendum
    discipline; the diff preserves pre-existing user edits and touches no source/test file.
  - History guard (`AC-D55.10`): `### D41`–`### D54` with reversals, the Existing Repository
    marker sentence, and the Current Tech Stack unchanged; no pre-P16 wording touched except
    by explicitly recorded supersession notes.
- **Dependencies:** P16-W1 (map precedes any deletion), P16-W2, P16-W3 (review runs last).
- **`touches_files`:** the disposition ledger, the four Q87 deletion targets, archive moves
  (if any), review checklists. No overlap with W2/W3 content files.
- **Exit condition:** ledger covers every in-scope file; deletion targets gone with successor
  records verified; the plan completion checklist ticks 1:1; the diff shows docs-only paths;
  `AC-D55.10` marker grep passes.

**Wave note.** P16-W1 runs first and alone (its map gates W4's deletions). P16-W2 and P16-W3
touch disjoint file sets and may run in one wave; P16-W4 runs after all three.
> **Increment metadata — uniform fields per wave (P16-T7, `AC-D55.7`):** Status / Commit / Evidence / Supersession. Active decisions stay with their requirements (traceability table above); summaries are cross-references (R112), never duplicated prose.
>
> - P16-W1 — Status: in progress (inventory + fact-sheet records landed); Commit: n/a, docs-only; Evidence: `docs/D55_inventory.md`, `docs/D55_fact_sheet.md`, `docs/README.md` authority blocks; Supersession: none (new records, zero deletions).
> - P16-W2 — Status: in progress; Commit: n/a, docs-only; Evidence: `usage.md` (canonical) + `USAGE.txt` (pointer), Q85 live-only; Supersession: correction only, no approval rewritten.
> - P16-W3 — Status: in progress (P16-T7 executing D55.7); Commit: n/a, docs-only; Evidence: six-file P6 addenda + P16-D55.6 cap addendum + baseline blocks atop both canonical files; Supersession: append-only, approvals byte-identical.
> - P16-W4 — Status: planned (runs after W1–W3); Commit: n/a, docs-only; Evidence: disposition ledger + docs-only review checklist (P16-T8); Supersession: none (deletions only per answered Q86/Q87).


### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P16-1 | The Q84 comment reword and Q86 `dev_docs/` deletion in the working tree are taken as landed; W4 verifies rather than redoes them | Orchestrator pre-landing record; re-editing risks clobbering the tracked micro-task change |
| AP-P16-2 | `AC-D55.9` verification is grep/link/checklist review only — the offscreen suite is not run as a P16 gate | Owner-ordered docs-only batch; no source/test file can change, so the suite cannot discriminate |
| AP-P16-3 | AC-G.1 (visual reference gate) does not apply — no wave makes a UI-visual decision (widget/copy choices follow standing D49.3/Q64 precedent: measurable outcome, no visual reference) | No pixel, placement, colour, or label choice is specified anywhere in D55 |
| AP-P16-4 | Archive moves use `docs/archive/` (created if needed); proposals move only after the link audit, and the 16 investigation files never move | Plan §§6–7 boundaries; A153 |
| AP-P16-5 | Sizes S/M only: W1/W2 are S (inventory + two-file guide fix); W3/W4 are M (six-file reconciliation + ledger + full-corpus review) | Owner scope sizes in the preamble; no wave exceeds M |

### Flagged Issues

**None.** Every D55 item is satisfiable as written on the existing stack:

- Q84–Q87 are all answered, so no wave waits on an owner decision; the only
  explicitly-open item (50-vs-100) has a specified handling (reconcile against
  `config/settings.py` + P7 assertions, else record open per A154/DG102) — recorded
  openness, not a gap.
- No consolidation step implies product behaviour: the one live/paper contradiction is
  settled by the Q85 answer before any guide is corrected (`AC-D55.4` gated on W1's fact
  sheet), and anything else that would imply behaviour is escalated, never decided
  (A149).
- No `PLAN`-routed escalation is open (all `addressed`); no `pending_doc_sync.md` entries
  remain unapplied (file absent); D1–P15 stay closed by the addenda-only rule.

Status: READY_FOR_TASK_MANAGER

---

## Phase P17 — Silence retry for historical chunks (D56) — drafted 2026-11-05

> Companion: `docs/architecture.md` § *Phase P17* (Codebase Summary, S-P17-1…S-P17-6,
> frozen interfaces, non-functional, AR-P17-1…AR-P17-6). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P17 (D56),
> Journey 51, `AC-D56.1`–`AC-D56.7` FINAL (Q88–Q91 all answered-owner-confirmed
> 2026-11-05; no blocking item), A156–A160, R114–R118, `design_gaps.md` DG106–DG108.
> Hard constraints: **D1–P16 are NOT reopened** (P17 touches P7/P14/P15-owned structures
> only additively; the watchdog, pacing budget, terminal finalization paths and
> `AC-D16.4`/`AC-D53.2` wording are read-only); sizes S/M only; no watchdog retuning, no
> chunk resizing, no TWS-side diagnosis, no new indicator surface, no D53 criterion
> change. One phase only — nothing past the D56 silence retry is planned.

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| D56.1 / `AC-D56.1` (single retry on silence — N = 30 s, per-chunk, zero-bar + trailing-silence triggers) + Journey 51 + Q88/Q89/Q91 + DG106 | S-P17-1 (fit-inside), S-P17-2 (sweeper + stamps); Frozen (cancel path, watchdog bound, generation fence) | P17-1 |
| D56.2 / `AC-D56.2` (re-issue silence falls through — no second retry, no watchdog change) | S-P17-4 (shared allowance: re-issue silence never re-issues); Frozen (strand finalization) | P17-1 (guard mechanism) + P17-3 (fall-through verification) |
| D56.3 / `AC-D56.3` (162 classification survives the retry) + DG108 | S-P17-3 (taxonomy); Frozen (error ingress, `classify_error`) | P17-2 |
| D56.4 / `AC-D56.4` (generation fencing of the superseded issue) | S-P17-2 (tag + drop + re-issue under current generation); Frozen (`_history_event_accepted`, cache PK) | P17-1 |
| D56.5 / `AC-D56.5` (pacing-slot accounting) + A160 + DG107 + Q89 | S-P17-5 (queue-with-deadline); Frozen (pacing constants, post-issue slot rule) | P17-2 |
| D56.6 / `AC-D56.6` (D53 indicator shows the retry — Q90 outcome) + A159 + DG100 | S-P17-6 (retry marker + latch label, elapsed continuing) | P17-3 |
| D56.7 / `AC-D56.7` (history intact + exactly-once counting) | S-P17-2 (identity-removal) + Frozen (PK idempotency, history-intact guard) | P17-1 (mechanism) + P17-3 (batch gate) |
| A156–A160, R114–R118, DG106–DG108, Q88–Q91 | S-P17-1…S-P17-6 | Every phase (guards) |

Every D56 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Phases

Each phase is a milestone, coarser than tasks; the Task Manager decomposes each into tasks
with acceptance criteria and tests. Phases are ordered; a later phase depends on earlier
ones unless stated. `touches_files` notes list the files a phase touches and flag the
serialisation points.

### P17-1 — Silence detection + cancel/re-issue core with fencing and exactly-once (D56.1, D56.2-guard, D56.4, D56.7-mechanism) — size M

- **Goal:** a chunk silent past 30 s (zero-bar primary rule or trailing-silence rule for
  partials) is cancelled and re-issued exactly once inside the watchdog horizon; late
  arrivals on the superseded reqId change nothing and no bar is counted twice.
- **Covers:** D56.1; `AC-D56.1`; D56.2-guard (no-second-retry enforcement lives here);
  `AC-D56.4`; D56.7-mechanism (identity-removal + PK idempotency); Journey 51 steps 1–3;
  A156/A157; R114/R116 (mechanism half); DG106.
- **Deliverables:**
  - `[new] ui/ticker_session.py` — `_history_req_last_activity: dict[int, float]`
    (stamped at registration/issue, re-stamped on each accepted `on_historical_bar`,
    removed with the reqId) + one session silence sweeper (`QTimer`, 1 s tick, armed only
    while history reqIds are in flight) + `_retry_silent_chunk(req_id)` (plan lookup,
    `cancel_historical_data`, superseded tag with slot kept, drop old reqId, pop
    `_req_bars[old]` with identity-removal from `_pending_bars`, paced re-issue of the
    identical plan under the current generation with a new reqId, `_retried_plans.add`).
    Guard: plans already in `_retried_plans` are never silence-retried; a re-issue's own
    silence never re-issues.
  - `[new/changed] tests` — offscreen clock-controlled cases: zero-bar-silent chunk
    (cancel + one identical re-issue), partial-then-stalled chunk (trailing rule fires),
    silent-at-30 s-minus-epsilon-then-delivering (no retry), late bars/END on the
    superseded reqId (fenced: counts, cache and wave state unchanged), double-delivery
    (count identity).
- **Dependencies:** none (first phase; reads P7/P14/P15 contracts, changes none).
- **`touches_files`:** `ui/ticker_session.py` + new/existing offscreen suites. No overlap
  with any other phase's production files (`ui/main_window.py` indicator/error work is
  P17-2/P17-3).
- **Exit condition:** per silent chunk exactly one cancel + one identical re-issue (same
  plan position, new reqId) concluding inside the watchdog horizon; no third issue for
  any chunk; minus-epsilon cases fire no retry; fenced late arrivals change nothing.

### P17-2 — Error taxonomy + pacing gate (D56.3, D56.5) — size S

- **Goal:** errors landing during a retry classify honestly and the re-issue never
  violates the rolling budget — exhaustion falls through to the unchanged watchdog path.
- **Covers:** D56.3; `AC-D56.3`; D56.5; `AC-D56.5`; A158/A160; R115/R117; DG107/DG108.
- **Deliverables:**
  - `[new/changed] ui/ticker_session.py` (same file as P17-1, later in order) +
    `[new/changed] ui/main_window.py::_on_error` (cancel-ack branch only) — generalise the
    cancel-ack rule: any error code on a cancel-tagged superseded reqId is debug-only
    (no status-bar, no shortfall, no pacing event); fresh-reqId errors keep existing
    semantics with the shared `_retried_plans` allowance checked first (a 162 on a
    silence-retried chunk finalizes short). Re-issue attempted immediately through
    `req_historical_data`; on `PacingExceeded` waits via the existing continuation path
    bounded by the unchanged watchdog (watchdog-first → stranded fall-through, fail-open
    and counted). Both reqIds consume pacing slots (post-issue rule, no refund).
  - `[new/changed] tests` — offscreen error-injection cases per reqId (cancel-ack 162 on
    superseded vs fresh 162 on re-issue, plus one non-162 cancel-ack generalization case)
    asserting classification + downstream shortfall/pacing; pacing-spy cases (slot
    consumption on both issues; exhaustion → watchdog fall-through, never a violation).
- **Dependencies:** P17-1 (re-uses the retry path, cancel tags, and `_retried_plans`
  writes; serialised on `ui/ticker_session.py` — not parallel with P17-1).
- **`touches_files`:** `ui/ticker_session.py` (retry-adjacent branches only; the P17-1
  structures are consumers, not rewrites) + `ui/main_window.py` (the `_on_error`
  162-superseded branch generalisation only — the `if errorCode == 162 and
  self._is_superseded_history_req(reqId)` condition) + offscreen suites.
- **Exit condition:** superseded-reqId errors of any inventoried code are cancel-acks
  with no user-facing or budget effect; fresh-reqId errors follow existing semantics
  with no third issue; pacing exhaustion yields counted fall-through, never a violation.

### P17-3 — D53 retry state + fall-through verification + batch gate (D56.6, D56.2-verify, D56.7-gate) — size S

- **Goal:** the retry is explicitly visible on the existing indicator with elapsed
  continuing, the double-silent fall-through is verified end to end, and the full suite
  stays green with history intact.
- **Covers:** D56.6; `AC-D56.6`; D56.2-verify (double-silent cases + watchdog
  finalization state); D56.7-gate (marker grep + full-suite green); A159; R118; DG100.
- **Deliverables:**
  - `[new/changed] ui/main_window.py` — retry marker in `_backfill_state`, `(retry …)`
    label set only while a retry is in flight and cleared only by the terminal clear
    (P15 latch pattern), elapsed a pure read of `_backfill_wave_start` (never reset by a
    retry), `AC-D53.3` no-current-claim re-asserted. Exact widget/copy/layout are Build
    details per DG100.
  - `[new/changed] tests` — wave-state + indicator-state assertions across first-issue /
    retry / completion (distinguishability, elapsed-continuity, no premature
    current-claim); double-silent cases (zero-bar and partial variants: exactly two
    issues per chunk + watchdog finalization state).
  - **Batch gate** — full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`, clean run per the recorded
    shared-test-DB / stale-`pytest`-shebang gotchas); `AC-D56.7` history-intact check
    (marker grep + `### D4[1-9]` / `### D5[0-5]` sections present, no pre-P17 wording
    touched).
- **Dependencies:** P17-1 (the retry-in-flight signal the indicator reads); independent
  of P17-2's files (may share a wave with P17-2).
- **`touches_files`:** `ui/main_window.py` (indicator only) + offscreen suites. No overlap
  with P17-2's production edits.
- **Exit condition:** retry state distinguishable from first-issue flight and completion
  with continuing elapsed and no current-cache claim; double-silent waves finalize via
  the unchanged watchdog path; suite green; history intact.

**Wave note.** P17-1 runs first (it owns `ui/ticker_session.py`'s retry structures).
P17-2 follows (same file, later branches, plus the `ui/main_window.py::_on_error`
branch). P17-3 depends on P17-1 and P17-2 and runs after P17-2: both P17-2 and P17-3
edit `ui/main_window.py` in disjoint regions (the `_on_error` cancel-ack branch vs
the indicator state), so Task Manager serialises on the shared file.

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P17-1 | The silence sweeper ticks at 1 s and is armed only while history reqIds are in flight; detection latency is therefore 30 s + ≤ 1 s tick, inside the S-P17-1 arithmetic | Keeps one timer flat across multi-chunk waves and clock-controllable; the ≤ 1 s is absorbed by the ≈ 55 s headroom |
| AP-P17-2 | Monotonic clock for the last-activity stamps (the session/window pattern), not wall-clock `time.time` deltas | Tests need clock control; wall-clock jumps would false-fire or mask silence |
| AP-P17-3 | The re-issue reuses the plan object at the same plan position (not queue re-insertion) with a new reqId under the current generation — no generation advance, no wave restart | A generation advance would fence the re-issue itself; queue re-insertion would reorder behind pacing-deferred chunks |
| AP-P17-4 | Identity-removal from `_pending_bars` drops exactly the old reqId's Bar objects (the same objects appended under `_req_bars[old]`); bars already persisted per-chunk stay in the cache (PK-idempotent) and are re-read, never duplicated in memory | `AC-D56.7` exactly-once counts the in-memory wave totals; the cache was already safe by PK |
| AP-P17-5 | The `(retry …)` label copy and any widget choice are Build details following standing D53 phrasing; only distinguishability + elapsed-continuity + no-current-claim are asserted | DG100 pattern (Q90 outcome fixed the state, not the pixels); AC-G.1 does not apply — no plan-level visual decision |
| AP-P17-6 | Disconnect mid-retry follows `AC-D53.2` (disconnect finalization wins, retry abandoned); coalesced same-triple reload mid-retry creates no new retry and advances no generation; mode switch / new-triple load starts a new wave and abandons the old retry with its wave | Journey 51 edge cases; each follows the existing terminal/coalescing/new-wave path with no new rule |
| AP-P17-7 | Sizes: P17-1 is M (new sweeper + retry path + fencing + identity cases); P17-2/P17-3 are S (branch generalizations + scoped cases + indicator) | Owner scope sizes; no phase exceeds M |

### Flagged Issues

**None.** Every D56 item is satisfiable as written on the existing stack:

- Q88–Q91 are all answered, so no phase waits on an owner decision; the aggressive-30 s
  tradeoff (R114), the per-chunk budget (Q89), the explicit retry state (Q90) and the
  expanded partial-stall scope (Q91/A156) are all pinned in ACs and mechanisms above.
- DG106–DG108 are answered by decisions, not open questions: the fit-inside arithmetic
  (S-P17-1), the queue-with-deadline seam (S-P17-5/DG107) and the generalized taxonomy
  with its code inventory (S-P17-3/DG108).
- The shared retry allowance (S-P17-4) unifies the silence axis with the pre-existing
  error-162 retry without revising the error path's semantics — no D1–P16 criterion is
  reinterpreted.
- No `PLAN`-routed escalation is open (all `addressed`); no `pending_doc_sync.md`
  entries remain unapplied (file absent); D1–P16 stay closed by the additive-only rule.

Status: READY_FOR_TASK_MANAGER

## Phase P18 — Viewport UX: visible go-to-latest chevron + fresh per-timeframe framing (D57) — drafted 2026-11-05

> Companion: `docs/architecture.md` § *Phase P18* (Codebase Summary, S-P18-1…S-P18-6,
> frozen interfaces, non-functional, AR-P18-1…AR-P18-6). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P18 (D57),
> Journeys 52–53, `AC-D57.1`–`AC-D57.7` FINAL (Q92–Q95 answered-owner-confirmed
> 2026-11-05; no blocking item), A161–A165 (A165 overridden with lineage), R119–R121
> (resolved), `design_gaps.md` DG109–DG110 (resolved; DG111 is P19-owned).
> Hard constraints: **D1–P17 are NOT reopened** (the two P11 revisions — visibility
> rule S-P11-4 → S-P18-1, range-restore S-P11-5 → S-P18-4 — are recorded revisions with
> lineage, not silent reopens); sizes S/M only; no watchdog retuning, no chunk
> resizing, no TWS-side diagnosis, no new indicator surface, no fetch-window change, no
> D51 criterion change beyond the two recorded supersessions. One phase only — nothing
> past the D57 viewport UX is planned (P19 prefetch is separate).

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| D57.1 / `AC-D57.1` (chevron visible whenever away — Q92 (a)) + Journey 52 + DG109 + R119 | S-P18-1 (away-only rule, supersedes badge rule); Frozen (`isFollowingSlot`, everything else untouched) | P18-1 |
| D57.1 / `AC-D57.2` (click = scroll-to-edge preserving span — Q93 (a)) + Journey 52 | S-P18-2 (existing `goToRealtime` caller); Frozen (`goToRealtime`/`followLive`) | P18-1 |
| D57.1 / `AC-D57.3` (glyph-only, bottom-right of price axis, visibility-coupled) | S-P18-1 (DOM shape + placement region + toggle path); Non-Functional (visual gate) | P18-1 |
| D57.2 / `AC-D57.4` (per-timeframe x-spans — 1 min/5 min decided + Q94 (a) table) + Journey 53 + DG110 + R120 | S-P18-3 (cutoff rule + clamp + zero-bar no-op); Frozen (`TIMEFRAME_CONFIG`, `session_windows`) | P18-2 |
| D57.2 / `AC-D57.5` (framing always fresh; follow-state memory stands — Q95 (b)) + Journey 53 + A165 + R121 | S-P18-4 (precedence + minimal back-shift); Data Model (range no longer read) | P18-2 |
| D57.2 / `AC-D57.6` (autoscale y over the framed window — A163) | S-P18-5 (library default, assertion-only) | P18-2 |
| D57.7 (history intact) | Frozen Interfaces + S-P18-6 (gate) | P18-3 |
| A161–A165, R119–R121, DG109–DG110, Q92–Q95 | S-P18-1…S-P18-6 | Every phase (guards) |

Every D57 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Phases

Each phase is a milestone, coarser than tasks; the Task Manager decomposes each into
tasks with acceptance criteria and tests. Phases are ordered; a later phase depends on
earlier ones unless stated. `touches_files` notes list the files a phase touches and
flag the serialisation points.

### P18-1 — Visible chevron: away-only visibility + go-to-realtime click (D57.1) — size S

- **Goal:** the main chart shows a glyph-only chevron at the bottom-right of the price
  axis whenever the viewport is away and hides it while following; one click scrolls
  to the live edge preserving span and re-engages follow.
- **Covers:** D57.1; `AC-D57.1` (away-alone-visible matrix incl. the supersession
  proof); `AC-D57.2` (post-click range + follow + chevron-hidden); `AC-D57.3`
  (placement + glyph-only + visibility coupling); Journey 52 incl. the deferred-fit,
  pan-back-to-edge and Fit/reset edges; A161/A162; R119; DG109.
- **Deliverables:**
  - `[new/changed] chart_assets/lwc/chart.html` — the chevron `<button>` DOM
    (glyph-only, keyboard-focusable with aria-label, hidden by default; no asset,
    module-order or offline-policy change).
  - `[new/changed] chart_assets/lwc/chart.js` — the away-only visibility control
    (`!isFollowing()`, superseding the badge rule per S-P18-1; badge bookkeeping
    stays internal), click wiring to the unchanged `goToRealtime`, and toggle on the
    existing viewport-change notification path (no polling). `followLive`,
    `fitAndFollow`, `fitToWidth` and the derivation itself are untouched.
  - `[new/changed] tests` — offscreen viewport-state × new-bars matrix (away-alone
    cells visible is the red-first proof against the old rule), click cases, and
    page-DOM placement/glyph/visibility-coupling cases; `node --test` core cases for
    the visibility predicate.
- **Dependencies:** none (first phase; reads P11 contracts, changes only the two
  recorded revisions).
- **`touches_files`:** `chart_assets/lwc/chart.html` + `chart_assets/lwc/chart.js` +
  new/existing offscreen + `node --test` suites. No overlap with any other phase's
  production files (`ui/lwc_view.py` framing work is P18-2).
- **Exit condition:** chevron visible in every away cell (with and without new bars),
  hidden in every following cell; click lands the span-preserved live edge with follow
  re-engaged and the chevron hidden; placement/glyph assertions hold.

### P18-2 — Fresh per-timeframe framing with follow-state memory (D57.2) — size M

- **Goal:** every different-symbol load and every timeframe change opens on the
  `AC-D57.4` frame with autoscaled y; remembered follow-state still decides whether
  the fresh frame tracks the edge; same-symbol data replaces keep preserving.
- **Covers:** D57.2; `AC-D57.4` (nine per-timeframe seeded-series frames incl. clamp
  and zero-bar); `AC-D57.5` (switch-back + timeframe-change freshness with follow-state
  encoding); `AC-D57.6` (visible price range covers the framed bars); Journey 53
  incl. rapid-switch, narrower-than-span and mode-switch edges; A163/A164/A165; R120/R121; DG110.
- **Deliverables:**
  - `[new/changed] ui/lwc_view.py` — the session-anchored frame computation (cutoff →
    logical `{from, to}` + `following`, clamped to loaded bars, zero-bar no-op),
    emission post-`set_series` through the existing range-op wire shape, and the
    precedence change (`set_symbol` to a different symbol and any `set_timeframe`
    change request a fresh frame; remembered `following` applied per S-P18-4 with the
    minimal back-shift for remembered-away; same-symbol replaces preserve per S-P11-3).
    Bar-domain emit behaviour and the report sink are unchanged.
  - `[new/changed] chart_assets/lwc/chart.js` (frame-application branch only) —
    apply an explicit fresh frame over the preserved-range path when the replace
    carries the fresh-frame directive (ordering after the rows; deferred-landing via
    the existing `needsFit` retry when unlaid-out). No derivation, live-path or
    chevron-logic change.
  - `[new/changed] tests` — per-timeframe seeded-series frame cases (session- and
    calendar-anchored cutoffs, clamping, zero-bar), switch-back freshness +
    follow-state cases (following → edge frame + tracking; remembered-away → fresh
    recent frame deriving away), timeframe-change freshness cases, and y-coverage
    cases.
- **Dependencies:** none on P18-1's production files (disjoint: page visibility logic
  vs Python framing + frame-application branch); shares the P18-3 gate. May share a
  wave with P18-1; Task Manager serialises only on `chart.js` if both waves touch it.
- **`touches_files`:** `ui/lwc_view.py` + `chart_assets/lwc/chart.js` (frame branch
  only — disjoint from P18-1's visibility/click hunks) + offscreen suites.
- **Exit condition:** all nine timeframes frame to their spans (or to loaded bars when
  narrower); switch-back and timeframe-change cases show fresh frames with the
  remembered follow-state honoured; same-symbol replaces still preserve; y covers the
  framed bars whenever bars exist.

### P18-3 — Cross-state verification + batch gate — size S

- **Goal:** chevron × framing interactions hold jointly and the full suite stays green
  with history intact.
- **Covers:** D57.7; cross-AC interactions (fresh frame while following hides the
  chevron; fresh frame while remembered-away shows it; chevron click after a fresh
  frame; Fit/reset consistency after framing); the declared P11 churn (away-alone
  assertions updated to away-only per S-P18-1/AR-P18-4); A161–A165 guards; R119–R121.
- **Deliverables:**
  - `[new/changed] tests` — joint chevron/frame state cases across both follow states
    plus the updated P11 away-alone assertions (rewritten to the superseded rule,
    recorded as churn, never silently weakened).
  - **Batch gate** — full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`, clean run per the recorded
    shared-test-DB / stale-`pytest`-shebang gotchas) + `node --test` for the page
    core; `AC-D57.7` history-intact check (marker grep + the `### D4[1-9]` /
    `### D5[0-6]` sections present, no pre-P18 wording touched).
- **Dependencies:** P18-1 and P18-2 (verifies their joint behaviour; runs after both).
- **`touches_files`:** offscreen + `node --test` suites only (no production edits).
- **Exit condition:** joint-state cases green; full suite green; history intact.

**Wave note.** P18-1 and P18-2 touch disjoint production surfaces except for two
hunks in `chart_assets/lwc/chart.js` (visibility/click vs frame-application branch)
that neither reads from the other — Task Manager may run them in one wave with the
file serialised, or in two waves. P18-3 depends on both and runs last; it edits no
production files.

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P18-1 | The chevron is a native page `<button>` (focusable, aria-labelled); exact pixels, offsets and dark-theme values are Build details asserted tolerantly as placement-region + glyph-only + visibility-coupling | `AC-D57.3` names placement and glyph, not pixels; the D3/P11 visual-gate precedent (behaviour gating, tolerant geometry) already covers this idiom |
| AP-P18-2 | Intraday session counts derive from the span names (1 wk → 5 sessions, 2 wks → 10, 1 M → ~22, 2 M → ~44, 6 M → ~126) resolved through `market_calendar` mode-aware windows, so holidays and RTH/ETH switches need no special case | The spans are session-anchored by owner acceptance (A164); the calendar already encodes genuine closures (ESC-023) and mode windows (`AC-D16.9`) |
| AP-P18-3 | A remembered-away fresh frame back-shifts minimally — the newest slot falls just outside the framed range — so `following == false` derives honestly while recency is maximal; the exact back-shift is asserted only as `following == false` + newest-window recency | The Q72 derivation model (P11 S-P11-1) leaves no other honest encoding: an explicit away flag would bifurcate the follow model, and a full-span retreat would bury the recent action the owner asked to see |
| AP-P18-4 | Same-symbol data replaces (backfill continuations, mode switches) and pop-out views keep existing behaviour — Q95 covers different-symbol loads and timeframe changes only | `AC-D57.5` scopes the supersession explicitly; widening it to every replace would re-open D51.2/D51.5, which are FINAL and untouched |
| AP-P18-5 | Sizes: P18-1 is S (one DOM element + visibility predicate + click wiring + matrix cases); P18-2 is M (cutoff computation across nine timeframes + precedence + frame-application branch + seeded matrices); P18-3 is S (joint cases + gate) | Owner scope sizes; no phase exceeds M |

### Flagged Issues

**None.** Every D57 item is satisfiable as written on the existing stack:

- Q92–Q95 are all answered, so no phase waits on an owner decision; the three
  recorded supersessions (badge rule → away-only per Q92; span table per Q94;
  range-restore → fresh framing per Q95 with follow-state memory standing) are all
  owner-decided with lineage on `AC-D57.1`/`AC-D57.4`/`AC-D57.5` and A165.
- DG109–DG110 are resolved by those answers (DG111 is P19-owned and untouched).
- The one genuine interaction the requirements leave to Plan — how remembered-away
  composes with a fresh frame under a pure-derivation follow model — is decided by
  S-P18-4/AP-P18-3 (minimal back-shift), not left for Task Manager to invent.
- No `PLAN`-routed escalation is open (all `addressed`); no `pending_doc_sync.md`
  entries remain unapplied (file absent); D1–P17 stay closed by the additive-only rule
  plus the two recorded P11 revisions.

Status: READY_FOR_TASK_MANAGER

## Phase P19 — Scroll-triggered backfill prefetch (D58) — drafted 2026-11-09

> Companion: `docs/architecture.md` § *Phase P19* (Codebase Summary, S-P19-1…S-P19-7,
> frozen interfaces, non-functional, AR-P19-1…AR-P19-6). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P19 (D58),
> Journey 54, `AC-D58.1`–`AC-D58.6` FINAL (analyst-decided per owner delegation
> 2026-11-05; owner corrections land as refinements), A166–A170 (A167's seam left to
> Plan — decided as S-P19-4/DG111), R122–R124 (mitigated),
> `design_gaps.md` DG111 (resolved by S-P19-4; Task Manager covers it under
> `AC-D58.2`).
> Hard constraints: **D1–P18 are NOT reopened** (P18 has no Plan yet — additive-only,
> no P11/P18 revision beyond the recorded S-P18-1/S-P18-4 lineage which P19 only
> reads); sizes S/M only; no watchdog retuning, no chunk resizing, no TWS-side
> diagnosis, no new indicator surface, no fetch-window or load-path change, no D51
> criterion change. One phase only — nothing past the D58 prefetch is planned (P20
> index/futures is separate).

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| D58.1 / `AC-D58.1` (trigger rule + per-timeframe table, settled viewports, mode-aware) + Journey 54 + A166 | S-P19-1 (Python settled-report host, never per tick); S-P19-2 (slot→ts distance, T = one `AC-D57.4` span); Frozen (`report_viewport`, `session_windows`, `TIMEFRAME_CONFIG`) | P19-1 |
| D58.2 / `AC-D58.2` (ordinary wave: one step, pacing, 120 s watchdog, D53, D56 retry, fencing, one in flight) + A167 + DG111 + Journey 54 | S-P19-3 (ordinary wave, one step/one in flight); S-P19-4 (DG111 coalesce seam); Frozen (`find_missing_spans`, `plan_requests`, `queue_wave_plans`, wave lifecycle) | P19-2 |
| D58.3 (incremental render, in-flight honesty, `AC-D16.4` shortfall, closures empty) + R123 + Journey 54 | S-P19-3 (ordinary-wave honesty inheritance); Non-Functional (honesty) | P19-3 |
| D58.4 (viewport untouched in both follow states; Q95 loads-only) + Journey 54 | S-P19-5 (preserve-path arrivals, no frame, no range op); Frozen (S-P11-3 preserve path) | P19-3 |
| D58.5 (chain while fetchable; closure stop; single shortfall; pacing fall-through) + A169 + R122 + Journey 54 | S-P19-3 (chaining) + S-P19-4 (pending-marker re-evaluation); S-P19-6 (per-view); Non-Functional (performance) | P19-2 |
| D58.6 (history intact) | Frozen Interfaces + S-P19-7 (gate) | P19-3 |
| A166–A170, R122–R124, DG111, Q75/Q95/D51/D53/D56 precedents | S-P19-1…S-P19-7 | Every phase (guards) |

Every D58 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Phases

Each phase is a milestone, coarser than tasks; the Task Manager decomposes each into
tasks with acceptance criteria and tests. Phases are ordered; a later phase depends on
earlier ones unless stated. `touches_files` notes list the files a phase touches and
flag the serialisation points.

### P19-1 — Settled-viewport trigger evaluation with per-timeframe thresholds (D58.1) — size S

- **Goal:** every settled viewport change (gesture-end / programmatic frame, including
  the initial frame) is evaluated against the trigger table and fires exactly when the
  oldest visible bar is within T(timeframe) of the oldest cached bar — mode-aware —
  staying silent otherwise.
- **Covers:** D58.1; `AC-D58.1` (per-timeframe fire/silent matrix incl. the
  single-sided boundary cell); Journey 54 trigger steps; A166 (settled-only) + A170
  (per-view evaluation); R122 rate bound (one-frame threshold).
- **Deliverables:**
  - `[new/changed] ui/lwc_view.py` — the trigger evaluation entry on the settled-report
    path: oldest-visible logical slot → real bar ts through the existing
    `_logical`/`_plotted` mapping, exposing the (oldest-visible-ts, following) reading.
    `report_viewport`'s store contract, `set_series` continuity and S-P18-4 precedence
    are untouched.
  - `[new/changed] ui/main_window.py` — the prefetch evaluator: gap (oldest-visible-ts
    vs oldest-cached-ts for the current triple) against T(timeframe) from the S-P19-2
    table (intraday session counts via `session_windows`, daily+ calendar spans),
    consulting `find_missing_spans` for the next older step. No wave issuance here —
    issuance is P19-2; this phase proves the fire/silent decision.
  - `[new/changed] tests` — offscreen per-timeframe viewport-matrix cases
    (within-T fires / beyond-T silent incl. the boundary, all nine timeframes,
    RTH + ETH mode-awareness, weekend-closure silence, pop-out per-view evaluation,
    following-at-edge no-op).
- **Dependencies:** none (first phase; reads P11/P18 contracts, changes only the two
  recorded NOT-frozen seams).
- **`touches_files`:** `ui/lwc_view.py` + `ui/main_window.py` (evaluation hunks only —
    disjoint from P19-2's issuance/state hunks by function, serialised if Task Manager
    shares a wave) + offscreen suites.
- **Exit condition:** the matrix is red-first against the no-trigger baseline and green
  after; boundary cell asserts single-sidedness (within fires, beyond silent); no wave
  is issued by this phase's code paths.

### P19-2 — Ordinary-wave prefetch with coalesce seam + fetch-while-fetchable (D58.2/D58.5) — size M

- **Goal:** a fired trigger moves exactly one older planner step through the existing
  wave lifecycle (pacing, watchdog, indicator, retry, fencing, one in flight), newer
  triggers coalesce instead of cancelling, and deep scrolls chain while the planner
  reports missing sessions — stopping honestly at closures, retention end, or pacing
  fall-through.
- **Covers:** D58.2 (`AC-D58.2`: one step, pacing gate, 120 s watchdog, D53 state, D56
  retry, fencing, one in flight, re-evaluation on completion + viewport change);
  D58.5 (`AC-D58.5`: chaining, closure stop, single shortfall, pacing fall-through);
  Journey 54 chaining/retention/pacing steps; A167 (one-step/one-in-flight) + A169
  (fetch while fetchable) + A170 (per-view); DG111 (S-P19-4 seam); R122/R124.
- **Deliverables:**
  - `[new/changed] ui/main_window.py` — single-step issuance: the fired trigger takes
    the next older step from `find_missing_spans`/`plan_requests` and issues it via
    the existing `queue_wave_plans` path when no wave is in flight for the triple;
    mode-switch/disconnect abandonment reuses the existing generation-bump + cancel
    paths (Branch-A coalesced reload keeps the running wave).
  - `[new/changed] ui/ticker_session.py` — the pending-prefetch marker (set on a newer
    trigger arriving mid-wave; consumed on completion with a fresh-viewport
    re-evaluation; cleared on every terminal path). All existing wave fields are read,
    not reshaped.
  - `[new/changed] tests` — offscreen wave-lifecycle cases (step size = one planner
    window, in-flight cap, pacing deferral, watchdog strand, D53 indicator state, D56
    exactly-once retry, generation fencing, coalesce-no-cancel + completion
    re-evaluation, mode-switch/disconnect abandonment with no cross-contamination),
    deep-scroll chaining cases (multi-step chain, weekend-closure stop with emptiness,
    beyond-retention single shortfall with no retry loop, pacing-exhaustion
    fail-open fall-through).
- **Dependencies:** P19-1 (consumes the fire decision; proves issuance against the
  matrix the trigger phase pinned).
- **`touches_files`:** `ui/main_window.py` (issuance hunks) + `ui/ticker_session.py`
  (marker + lifecycle reads) + offscreen suites. Serialised against P19-1 only on
  `ui/main_window.py` if waved together.
- **Exit condition:** one-step/one-in-flight lifecycle green; a mid-wave second trigger
  never cancels the running wave and re-evaluates on completion; chains extend while
  fetchable and stop honestly; full P7/P14/P15/P17 wave suites stay green.

### P19-3 — Honesty + viewport stability + batch gate — size S

- **Goal:** prefetch arrivals render incrementally without ever presenting in-flight
  regions as complete, the viewport never moves on arrival in either follow state, and
  the full suite stays green with history intact.
- **Covers:** D58.3 (`AC-D58.3`: incremental render, D53 in-flight state, `AC-D16.4`
  shortfall, closures empty); D58.4 (`AC-D58.4`: slot-stability in both follow states,
  Q95 loads-only); D58.6 (history intact); Journey 54 honesty/viewport steps; A168
  (load-neutrality incl. the daily+ background wave); R123.
- **Deliverables:**
  - `[new/changed] tests` — offscreen in-flight/stranded/closure cases (incremental
    per-chunk render assertions, D53-running-never-complete assertions, verbatim
    `AC-D16.4` shortfall at strand finalization, genuine-closure emptiness) and
    viewport-slot cases (identical range across landings while away; live-edge
    extension only via the D51 path while following; no fresh frame and no range op
    on any prefetch arrival).
  - **Batch gate** — full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`, clean run per the recorded
    shared-test-DB / stale-`pytest`-shebang gotchas); `AC-D58.6` history-intact check
    (marker grep + the `### D4[1-9]` / `### D5[0-8]` sections present, no pre-P19 wording
    touched).
- **Dependencies:** P19-1 and P19-2 (verifies their joint behaviour; runs after both).
- **`touches_files`:** offscreen suites only (no production edits).
- **Exit condition:** honesty + viewport-stability cases green; full suite green; history
  intact; no D51/P15/D53/D56 wording or behaviour regressed.

**Wave note.** P19-1 and P19-2 touch overlapping production surfaces only in
`ui/main_window.py` (evaluation vs issuance hunks, disjoint by function) — Task Manager
may run them in one wave with the file serialised, or in two waves. P19-3 depends on
both and runs last; it edits no production files.

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P19-1 | The evaluator lives host-side in `ui/main_window.py` next to the load/backfill orchestration, reading the stored settled report; `report_viewport` itself keeps its store-only contract | The host already owns the planner consult + `queue_wave_plans` call sites + generation proxy; splitting the evaluator into a new module would fork the P7 wave semantics |
| AP-P19-2 | Oldest-visible resolves through the same `_logical`/`_plotted`/`_cmap` mapping the S-P18-3 frame computation uses; collapsed (weekend-folded) windows are covered by seeded-series slot→ts cases, not by new mapping code | Reusing the proven mapping bounds AR-P19-3; a second mapping would drift from what the page actually shows |
| AP-P19-3 | One planner step = one `TIMEFRAME_CONFIG` duration window older under the existing stepping rule (e.g. `1 min`→`1 D` steps, `30 mins`→`30 D`, weekly→`2 Y`); per-wave chunk sizes are unchanged from load-time waves | `AC-D58.2` names one planner step; the stepping rule is the existing chunking the pacing/watchdog budgets were tuned against |
| AP-P19-4 | Load-time behaviour is byte-identical except that a daily+ initial frame within T fires one ordinary background wave; P15 T0 semantics are asserted unchanged around it (A168) | The load path is untouched — only the settled-report evaluation (which the initial frame also emits) can fire, and it runs as a background wave |
| AP-P19-5 | Sizes: P19-1 is S (evaluation entry + gap-vs-table decision + viewport matrix); P19-2 is M (single-step issuance + marker lifecycle + chaining/stop/fall-through matrices); P19-3 is S (honesty + slot-stability cases + gate) | Owner scope sizes; no phase exceeds M |

### Flagged Issues

**None.** Every D58 item is satisfiable as written on the existing stack:

- The trigger table is analyst-decidable from the settled `AC-D57.4` spans (owner
  delegation "decide and update to me") — S-P19-2 reuses the anchored P18 tables, so
  no new measurement or owner round is needed; owner corrections to any cell land as
  refinements without reopening the phase.
- DG111 (the one genuine Plan seam — cancel-replace vs queue-with-deadline) is decided
  by S-P19-4 (coalesce, never cancel) with rationale recorded, not left for Task
  Manager to invent; Task Manager covers the marker lifecycle under `AC-D58.2`.
- R122–R124 are mitigated by construction (one-step/one-in-flight + pacing gate,
  in-flight honesty + incremental render, ordinary background waves).
- No `PLAN`-routed escalation is open (all `addressed`); no `pending_doc_sync.md`
  entries remain unapplied (file absent); D1–P18 stay closed by the additive-only rule
  plus the recorded P11/P18 revisions, which P19 only reads.

Status: READY_FOR_TASK_MANAGER

## Phase P20 — Index + futures contract support (D59) — drafted 2026-11-09

> Companion: `docs/architecture.md` § *Phase P20* (Codebase Summary, S-P20-1…S-P20-7,
> frozen interfaces, non-functional, AR-P20-1…AR-P20-6). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P20 (D59),
> Journeys 55–56, `AC-D59.1`–`AC-D59.6` FINAL (Q96–Q99 answered-owner-confirmed
> 2026-11-09; Q99 is an owner override of the analyst default — one extra TWS
> round-trip on unknown symbols only, cost recorded in R128), A171–A174
> (CONFIRMED), R125–R129 (R128 RESOLVED), `design_gaps.md` DG112 (Plan-scoped as
> suppress in S-P20-5) + DG113 (resolved by the S-P20-3 probe seam).
> Hard constraints: **D1–P19 are NOT reopened** (P19 prefetch is in flight —
> read-only; the planner/wave/machinery P20 touches is only extended with
> default-preserving flags, never reshaped); sizes S/M only; no TWS-side-silence
> diagnosis, no prefetch change, no pacing/watchdog/D53/D56 retuning, no new tape
> feature, no continuous/back-adjusted series, no options support. One phase only —
> nothing past the D59 build waves is planned (P21 follow-offset is separate).

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| D59.1 / `AC-D59.1` (IND resolution: SPX+NDX+DJI+RUT, never STK/SMART) + Journey 55 + A171 + Q96 | S-P20-1 (IND table + rule order); Frozen (`get_stock_contract`, proxy path) | P20-1 |
| D59.4-unknown / `AC-D59.2` (probe-first: exactly one probe, then refuse-or-adopt) + Journeys 55–56 edge cases + A174 + Q99 + DG113 | S-P20-2 (STK pattern) + S-P20-3/S-P20-3a (probe seam + adopt); Frozen (`req_contract_details`, lookup lifecycle) | P20-1 |
| D59.2 / `AC-D59.3` (futures: ES+NQ+YM+RTY, CME/USD, `_front_month` auto-roll) + Journey 56 + A172 + Q97 | S-P20-1 (rule order; FUT leg unchanged); Frozen (`get_futures_contract`) | P20-1 |
| D59.3 / `AC-D59.4` (futures timestamps as-is ET; mode-empty never deletes) + Journey 56 + A173 + Q98 + R127 | S-P20-4 (canonical full-session mode) + S-P20-5 (presence bypass, collapse/band scoping); Frozen (`session_windows`, `plan_requests`) | P20-2 |
| D59.5 / `AC-D59.5` (proxy never for price) + Journey 55 edge cases + R129 | S-P20-6 (structural guard); Frozen (tape-only proxy path) | P20-3 |
| D59.6 / `AC-D59.6` (history intact) | Frozen Interfaces + S-P20-7 (gate) | P20-3 |
| A171–A174, R125–R129, DG112, Q96–Q99 precedents | S-P20-1…S-P20-7 | Every phase (guards) |

Every D59 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Phases

Each phase is a milestone, coarser than tasks; the Task Manager decomposes each into
tasks with acceptance criteria and tests. Phases are ordered; a later phase depends on
earlier ones unless stated. `touches_files` notes list the files a phase touches and
flag the serialisation points.

### P20-1 — Contract resolution + probe-first seam + error-200 honesty — size M

- **Goal:** every load resolves through the IND → FUT → STK-pattern → unknown
  order; unknowns probe exactly once before refuse-or-adopt; any error-200 leg
  ends honestly with no dead realtime attach.
- **Covers:** D59.1 (`AC-D59.1`: per-symbol IND capture matrix, never STK/SMART);
  D59.4-unknown (`AC-D59.2`: one probe reqId + refuse honesty / adopt-on-success);
  D59.2 (`AC-D59.3`: CME/USD/front-month capture); Journey 55 steps + Journey 56
  resolution step; A171/A172/A174; Q96/Q97/Q99; R125/R126/R128; DG113.
- **Deliverables:**
  - `[new/changed] ibkr/contracts.py` — the `IND_CONTRACTS` table (S-P20-1),
    `is_index_symbol` / `is_futures_root` predicates, rule-ordered
    `get_contract_for_symbol` (IND → FUTURES_SCHEDULE → STK pattern → unknown/None).
    `get_stock_contract` / `get_futures_contract` / `_front_month` bodies unchanged.
  - `[new/changed] ui/main_window.py` + `[new/changed] ui/ticker_session.py` —
    the probe-first seam (unknown → one `ContractLookupService.request` →
    adopt-first-details on ok / Q99 refuse on not-ok, all before prime/wave/realtime)
    and the error-200 leg gate (prime/wave 200 → verbatim `AC-D16.4` shortfall,
    realtime never attached on rejected contracts). Branch-A coalescing and the
    wave machinery otherwise unchanged.
  - `[new/changed] services/contract_lookup_service.py` — pending entries retain
    the first `contract_details` payload (adopt source); timeout/exactly-once/cancel
    semantics unchanged.
  - `[new/changed] tests` — offscreen per-symbol contract-capture matrices (IND ×
    4 + FUT × 4 asserting secType/exchange/currency/expiry; STK controls
    SPY/QQQ/DIA/IWM + AAPL untouched), unknown-symbol probe-once cases (exactly one
    probe reqId + refuse message + nothing persisted + zero prime/wave/realtime
    reqIds; adopt-on-success case), error-200 honesty cases (full-span shortfall,
    no realtime attach, no 300 s hang).
- **Dependencies:** none (first phase; reads P7/P14/P17 wave contracts, changes
  only the recorded NOT-frozen seams).
- **`touches_files`:** `ibkr/contracts.py` + `ui/main_window.py` +
  `ui/ticker_session.py` + `services/contract_lookup_service.py` + offscreen suites.
- **Exit condition:** the IND capture matrix is red-first against the current
  STK/SMART fallthrough and green after; unknown-symbol cases assert exactly one
  probe reqId; error-200 legs never attach realtime; per-symbol capture precedes
  any wave test (R125).

### P20-2 — Futures session scoping: canonical mode + presence bypass + visual scoping — size M

- **Goal:** futures charts run the full near-24 h session with TWS timestamps
  as-is in ET in both modes; no equity rule deletes, folds, or mis-shades
  overnight bars.
- **Covers:** D59.3 (`AC-D59.4`: as-is-ET positions both modes, mode-empty
  vacuous); Journey 56 overnight/mode-switch/rollover/weekend/pop-out steps;
  A173; Q98; R127; DG112 (bands suppressed).
- **Deliverables:**
  - `[new/changed] ui/main_window.py` + `[new/changed] ui/ticker_session.py` —
    futures roots forced onto the canonical full-session mode (S-P20-4, S-P8-4
    pattern): one shared cache, toggle as pure cache hit.
  - `[new/changed] services/backfill_service.py` — `present_days` /
    `find_missing_spans` gain defaulted `is_futures` (existing callers
    byte-identical); futures presence = calendar-day presence, Saturday-only
    closure (S-P20-5).
  - `[new/changed] services/time_collapse_service.py` + LWC session-band path
    (`ui/lwc_view.py`, `chart_assets/lwc/`) — collapse folding skipped and D1
    bands suppressed for futures roots (DG112).
  - `[new/changed] tests` — offscreen overnight-span matrix (seeded futures bars
    across the overnight session × RTH/ETH asserting as-is-ET slot equality +
    non-deletion), collapse/band scoping cases, canonical-mode toggle cases
    (identical bars, pure cache hit), rollover/weekend/pop-out edge cases.
  - **Standalone live probe (owner-run, D48/D52 precedent)** — IND table rows
    accepted by TWS (no error 200), ES price + as-is-ET time correct; recorded,
    not a suite gate.
- **Dependencies:** P20-1 (consumes the resolved FUT contract; proves scoping
  against the resolution the contract phase pinned).
- **`touches_files`:** `services/backfill_service.py` +
  `services/time_collapse_service.py` + `ui/main_window.py` +
  `ui/ticker_session.py` + `ui/lwc_view.py` + `chart_assets/lwc/` + offscreen
  suites. Serialised against P20-1 only on `ui/main_window.py` /
  `ui/ticker_session.py` if waved together.
- **Exit condition:** the overnight matrix is red-first against the current
  equity-mapped path and green after the bypasses; RTH/ETH render identical
  positions; no overnight bar is deleted, folded, or band-shaded; Q98 needs no
  new session model.

### P20-3 — Proxy guard + batch gate — size S

- **Goal:** INDEX_PROXY is structurally tape-only, and the full suite stays green
  with history intact.
- **Covers:** D59.5 (`AC-D59.5`: chart-series provenance, tape-only proxy);
  D59.6 (`AC-D59.6`: history intact); Journey 55 proxy edge cases; R129.
- **Deliverables:**
  - `[new/changed] tests` — offscreen provenance cases (index chart-series source
    ≠ futures across the IND family), a source-shape assertion (chart
    load/history path `INDEX_PROXY`-free), and the existing burst-proxy tests
    re-green (tape-only use preserved).
  - **Batch gate** — full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`, clean run per the
    recorded shared-test-DB / stale-`pytest`-shebang gotchas); `AC-D59.6`
    history-intact check (marker grep + the `### D4[1-9]` / `### D5[0-9]` sections
    present, no pre-P20 wording touched); standalone probe results recorded.
- **Dependencies:** P20-1 and P20-2 (verifies their joint behaviour; runs after both).
- **`touches_files`:** offscreen suites only (no production edits).
- **Exit condition:** provenance + shape cases green; burst-proxy tests green;
  full suite green; history intact; no D51/P15/D53/D56 wording or behaviour
  regressed.

**Wave note.** P20-1 and P20-2 touch overlapping production surfaces only in
`ui/main_window.py` / `ui/ticker_session.py` (resolution/leg-gating hunks vs
canonical-mode hunks, disjoint by function) — Task Manager may run them in one
wave with those files serialised, or in two waves. P20-3 depends on both and runs
last; it edits no production files.

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P20-1 | The IND table rows are Plan-stated per the TWS IND spec: SPX→(IND,CBOE,USD) highest confidence; NDX→(IND,NASDAQ,USD), DJI→(IND,CME,USD), RUT→(IND,CME,USD) medium; all rows confirmed by the owner-run standalone probe (D48/D52 precedent) | Q96 named symbols, not venues; TWS accepts/rejects per (exchange, currency), so values must be stated with rationale — Plan states them and the probe verifies; a rejected row keeps honest shortfall (Journey 55 step 3) and the correction lands as a table refinement without reopening |
| AP-P20-2 | STK = ticker-charset match (uppercase letters/digits/dot/dash, ≤8 chars — covers `BRK.B`/`BF-B`) AND not an IND/FUT root; SPY/QQQ/DIA/IWM stay STK regardless | Gives `AC-D59.2`'s "no STK rule" cell a real trigger while keeping every stock load probe-free (DG113 cost); errs toward STK so live stocks never pay the probe |
| AP-P20-3 | Probe-adopt uses the first returned `ContractDetails` payload's contract for that load only; nothing is persisted | TWS is session truth for unknowns; persisting risks stale contracts at listing changes, and the probe's point is discovery (S-P20-3a) |
| AP-P20-4 | Futures week = Sun–Fri for presence (Saturday the only futures closure); equity holidays are fetched, not assumed — an empty fetch ends in honest `AC-D16.4` shortfall | Futures trade through most equity holidays, so the equity calendar would wrongly close real sessions; the zero-bar-except-Saturday rule is self-correcting via fetch |
| AP-P20-5 | Sizes: P20-1 is M (IND table + rule order + probe seam + adopt + error-200 gating + matrices); P20-2 is M (canonical mode + planner flag + collapse/band scoping + overnight matrix + probe record); P20-3 is S (provenance + shape + gate) | Owner scope sizes; no phase exceeds M |
| AP-P20-6 | Q98 interaction note only: collapse/band scoping touches session-boundary geometry but Q98's as-is-ET rule is untouched — the math is slot-based and session-agnostic | P21's recorded reading; P20 changes which bars exist, never how a timestamp maps to ET |
| AP-P20-7 | The error-200 refuse path reuses the existing stranded/shortfall finalization wording (`AC-D16.4`) rather than a new status vocabulary | D53's indicator + shortfall language already covers failed waves; a second vocabulary would fork the honesty contract |

### Flagged Issues

**None.** Every D59 item is satisfiable as written on the existing stack:

- IND/FUT resolution is a table + rule order on the existing one-function seam
  (`get_contract_for_symbol`); the per-symbol venue uncertainty (R125) is a
  Plan-stated detail verified by the D48/D52-precedent standalone probe, not a
  requirements gap — the capture-case mitigation + honest-shortfall backstop hold
  for any row.
- The Q99 probe seam reuses the proven D22 lookup service (paced, 5 s bound,
  exactly-once); DG113 is decided by S-P20-3 (probe-before-legs, never parallel)
  with rationale recorded, not left for Task Manager to invent.
- The futures timestamp fix bypasses equity rules (canonical mode, presence flag,
  collapse/band scoping) without inventing the session model Q98 forbids; R127's
  cause-uncertainty is handled by repro-first ordering (S-P20-7), not guessing.
- DG112 is scoped (suppress) with rationale + rejected alternative; R126/R129 are
  mitigated by construction (existing roll behaviour; provenance + shape pins).
- No `PLAN`-routed escalation is open (all `addressed`); no `pending_doc_sync.md`
  entries remain unapplied (file absent); D1–P19 stay closed by the additive-only
  rule plus the recorded P8/P11/P18 revisions, which P20 only reads.

Status: READY_FOR_TASK_MANAGER

---

## Phase P21 — Follow-offset preservation on new-bar arrival (D60) — drafted 2026-11-09

> Companion: `docs/architecture.md` § *Phase P21* (Codebase Summary, S-P21-1…S-P21-6,
> frozen interfaces, non-functional, AR-P21-1…AR-P21-5). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P21 (D60),
> Journey 57, `AC-D60.1`–`AC-D60.7` FINAL (Q100–Q102 answered-owner-confirmed
> 2026-11-09; Q100 is an owner override of the analyst default — explicit actions
> preserve, recorded with lineage in A178), A175–A180 (A177/Q102 and A179/Q101
> CONFIRMED), R130–R133 (R130/R131 RESOLVED by the answers; R132/R133 Plan-scoped
> below), `open_questions.md` Q100–Q102. Hard constraints: **D1–P20 are NOT
> reopened** (P20 index/futures is in flight — read-only; the contract/planner/wave
> machinery P21 reads is never reshaped); the Q72–Q76 follow/away derivation, the
> S-P11-1 slot rule, the P19 prefetch trigger/thresholds, D53/D56, and the Q98
> as-is-ET rendering are all read-only; sizes S/M only; no new module, no new
> dependency, no schema migration, no live-TWS dependency, no order code. One phase
> only — nothing past the D60 build waves is planned.

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| D60.1 / `AC-D60.1` (preserve offset on new-bar arrival, G×N matrix, per-view evaluation) + Journey 57 steps 1–2 + A175/A176 + Q102 | S-P21-1 (envelope slot-delta shift); Frozen (`update_live_bar` emit, `isFollowingSlot`) | P21-1 |
| D60.2 / `AC-D60.2` (explicit return-to-edge preserves gap; ONLY manual scroll/pinch zeroes) + Journey 57 step 4 + Q100 + A178-override | S-P21-2 (remembered gap + preserve actions) | P21-1 |
| D60.5 / `AC-D60.5` (every view, per-view gap, never shared) + Journey 57 pop-out step + Q102 + A177 | S-P21-4 (per chart-page instance state) | P21-1 |
| D60.7 / `AC-D60.7` (wave landing while away bit-identical: backfill / realtime / prefetch legs) + Journey 57 away edge + A180 | S-P21-5 (landing neutrality, repro-first diagnosis) | P21-2 |
| D60.4 / `AC-D60.4` (away path untouched — `AC-D51.2` regression guard) + Journey 57 step 3 | S-P11-2 (read-only) + S-P21-5 | P21-2 |
| D60.3 / `AC-D60.3` (session open resets gap to fresh-frame default) + Journey 57 edge + Q101 + A179 | S-P21-3 (fresh-frame default wins; `fresh_frame_ops` frozen) | P21-2 |
| D60.6 / `AC-D60.6` (history intact) | Frozen Interfaces + S-P21-6 (gate) | P21-3 |
| A175/A176 (slot-based, forming-bar no-shift), R132 (library-seam cause), R133 (prefetch interplay) | S-P21-1/S-P21-6 | P21-1 (R132/R133 closed there) |
| A178 (overridden default, lineage), A179/A177 (confirmed), R130/R131 (resolved by answers) | Recorded in S-P21-2/S-P21-3/S-P21-4 | No phase (no work; resolution recorded) |

Every D60 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Phases

Each phase is a milestone, coarser than tasks; the Task Manager decomposes each into
tasks with acceptance criteria and tests. Phases are ordered; a later phase depends
on all earlier ones unless stated. `touches_files` notes list the files a phase
touches and flag the serialisation points.

### P21-1 — Follow-offset live path + explicit-action preserve + per-view — size M

- **Goal:** while following, every new-slot arrival shifts the visible range right
  by exactly the arrival width (gap preserved, never snapped); every explicit
  return-to-edge action resumes follow in place with the remembered gap; each view
  holds its own gap.
- **Covers:** D60.1 (`AC-D60.1`: G ∈ {0,1,3} × N ∈ {1,3} matrices, main + pop-out
  with different gaps); D60.2 (`AC-D60.2`: per-action preserve cases for
  Fit/reset, chevron/`goToRealtime`, right-edge double-click/Fit + the ONLY-zero
  path pinned on manual scroll/pinch); D60.5 (`AC-D60.5`: two-view independence);
  Journey 57 steps 1–2 + 4; A175/A176/A178; Q100/Q102; R130/R132/R133.
- **Deliverables:**
  - `[new/changed] chart_assets/lwc/chart.js` — the envelope slot-delta shift
    (S-P21-1): newest-slot delta across the envelope → one right-shift by the
    delta while following; forming-bar-only envelopes shift nothing; G = 0
    degenerates to the current edge outcome. Explicit actions (S-P21-2):
    `goToRealtime`/chevron keeps span and lands newest at remembered-gap offset;
    `fitAndFollow` frames all then extends `to` by the remembered gap; manual
    scroll/pinch stays the only zero path. Per-instance remembered gap (S-P21-4).
  - `[new/changed] tests` — offscreen viewport-slot matrices (pre/post ranges +
    gap equality), per-action preserve cases, two-view independence cases, and
    the G = 0 degeneracy — all red-first against the current snap-to-edge path.
  - `node --test` for the page pure core alongside the offscreen suites.
- **Dependencies:** none (first phase; reads the P11/P18 viewport contracts
  frozen below, changes only the recorded NOT-frozen page paths).
- **`touches_files`:** `chart_assets/lwc/chart.js` + offscreen/`node --test`
  suites. No Python production file is touched in this phase.
- **Exit condition:** the G×N matrices are red-first on the current
  `scrollToRealTime` path and green after the shift; per-action cases assert
  post-action gap == remembered gap + follow re-engaged; two-view cases assert
  independent preservation; manual scroll/pinch is the only asserted zero path.

### P21-2 — Away-landing neutrality + session-open reset — size M

- **Goal:** no landing (wave chunk, realtime update, prefetch arrival) ever moves
  an away viewport, and no stale gap survives a session open.
- **Covers:** D60.7 (`AC-D60.7`: ES 5-min away repro — scroll into the past with
  a wave in flight, land chunks per leg, assert bit-identical range + follow
  disengaged); D60.4 (`AC-D60.4`: away-arrival identity + disengaged follow as
  the `AC-D51.2` regression guard); D60.3 (`AC-D60.3`: carried-gap session-open
  cases asserting the post-open gap equals the fresh-frame default); Journey 57
  step 3 + away edge; A179/A180.
- **Deliverables:**
  - `[new/changed] chart_assets/lwc/chart.js` + `[new/changed] ui/lwc_view.py`
    (S-P21-5) — repro-first diagnosis of the away mover among the enumerated
    candidate sites (chunk render without same-symbol continuity, fresh-frame
    re-land on chunk, `fitToWidth` fallback on a failed range re-apply), then
    the gate: landings deliver bars only, never navigation. Session-open reset
    (S-P21-3): no Python gap is carried — the fresh frame lands on its default;
    pinned by carried-gap open cases (may land as tests-only if the reset is
    already structural).
  - `[new/changed] tests` — the ES away-repro per leg (backfill / realtime /
    prefetch), away-arrival identity suites, and session-open reset suites —
    the repro failing on the current tree before the fix.
- **Dependencies:** P21-1 (consumes the shift helper + remembered-gap state it
  pins; serialized on `chart.js` if waved together).
- **`touches_files`:** `chart_assets/lwc/chart.js` + `ui/lwc_view.py` + offscreen
  suites. Serialised against P21-1 on `chart.js`.
- **Exit condition:** the away repro is red-first and green after the gate (range
  bit-identical across every landing leg, follow stays disengaged);
  session-open cases assert default gap with a non-zero carried gap; `AC-D51.2`
  suites stay green.

### P21-3 — Batch gate — size S

- **Goal:** every `AC-D60.*` criterion observably satisfied, nothing else changed,
  suite green.
- **Covers:** D60.6 (`AC-D60.6`: history intact); the full-suite green gate; the
  R132/R133 closure record.
- **Deliverables:**
  - **Batch gate** — full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`, clean run per the
    recorded shared-test-DB / stale-`pytest`-shebang gotchas) + `node --test`
    for the page core green; `AC-D60.6` history-intact check (marker grep + the
    `### D4[1-9]` / `### D5[0-9]` sections present, no pre-P21 wording touched).
- **Dependencies:** P21-1 and P21-2 (verifies their joint behaviour; runs after both).
- **`touches_files`:** offscreen suites only (no production edits).
- **Exit condition:** full suites green; every `AC-D60.*` observably satisfied;
  no D51/P15/P18/P19 behaviour or wording regressed.

**Wave note.** P21-1 touches only the page + suites; P21-2 touches the page +
`ui/lwc_view.py` + suites — Task Manager runs P21-2 after P21-1 (it consumes the
shift helper), or serializes the two on `chart_assets/lwc/chart.js` if waved
together. P21-3 depends on both and edits no production files.

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P21-1 | The shift unit is the page logical slot (the library's logical-index range), never pixels; the window span is preserved (shift, not rescale) | The constraints fix slot-based measurement; a shift preserves span by construction, so density/width never enter the math (A176) |
| AP-P21-2 | Each view remembers its last following gap page-side (default = `FRESH_FRAME_RIGHT_PADDING` for views that never followed); explicit actions restore follow with that gap | `AC-D60.2` promises "current gap unchanged" from any viewport state — an away view holds no live gap, so the last following gap is the only honest reading; the default matches the fresh frame a never-followed view opens on |
| AP-P21-3 | Forming-bar growth is a no-shift structural consequence (same slot → zero envelope delta), not a separate branch | A175 + the envelope-delta design: no new slot means no new width to compensate, so tick-time jitter is impossible by construction |
| AP-P21-4 | The within-session hole-open live republish (`update_live_bar` opened-hole branch) travels the same envelope-delta shift, applied exactly once per envelope | The republish appends a new slot like any arrival; envelope-level delta accounting (not per-op shifting) makes double-shift structurally impossible |
| AP-P21-5 | Sizes: P21-1 is M (envelope shift + three explicit actions + per-view matrices + node core), P21-2 is M (away-mover diagnosis + landing gate + session-open pins), P21-3 is S (gate only) | Owner scope sizes; no phase exceeds M |
| AP-P21-6 | AC-G.1 (visual reference gate) is satisfied by reuse: no new control, glyph, colour, or placement — the chevron, Fit/reset, and double-click/Fit gestures keep their P18/D3 visuals; only post-action viewports change | Same precedent as AP-P11-4/AP-P18 assumptions: presence-gating, not visual language, so no confirmed reference is needed |

### Flagged Issues

**None.** Every D60 item is satisfiable as written on the existing stack:

- The defect is our own page call (`followLive` → `scrollToRealTime` snaps newest
  to edge; the fallback pins `{from: slot − span, to: slot}`) — replacing the
  edge-pin with an envelope slot-delta shift is additive page logic with
  probe measurables (R132 resolved as a scoped fix, not a gap).
- Q100/Q101/Q102 are all owner-answered FINAL; the override (Q100) is recorded
  with lineage in A178 and changes only assertions, not satisfiability.
- The away-landing yank (D60.7) is an owner-observed repro with enumerated
  candidate sites and a repro-first gate — diagnosis inside the phase, not a
  requirements gap (A180).
- R133 is closed by construction: D60 shifts evaluate as settled viewport
  changes like any pan (P19 evaluates settled reports only), and `AC-D58.4`
  already pins prefetch arrivals as viewport-neutral.
- No `PLAN`-routed escalation is open (all `addressed`); no `pending_doc_sync.md`
  entries remain unapplied (file absent); the P19/P20 wave machinery is only read.

Status: READY_FOR_TASK_MANAGER

---

## Phase P22 — Toolbar / timezone-toggle / crosshair / time-axis fixes (D61–D64) — drafted 2026-11-10

> Companion: `docs/architecture.md` § *Phase P22* (Codebase Summary, S-P22-1…S-P22-6,
> frozen interfaces, non-functional, AR-P22-1…AR-P22-5). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — Phase P22 (D61–D64),
> Journeys 58–61, `AC-D61.1`–`AC-D64.3` FINAL (Q103–Q105 answered-owner-confirmed
> 2026-11-10, all (a) recommended defaults), A181–A185, R134–R137, `open_questions.md`
> Q103–Q105. Hard constraints: **D1–P21 are NOT reopened** (P21 follow-offset in flight
> is read-only — P22's toggle re-render must preserve the P11/P18/P21 viewport contracts;
> the P19 prefetch and P20 contract machinery are only read); LWC-only tree (no
> pyqtgraph surface exists to update); display-only time math (A185 — cached timestamps
> never rewritten); no new module, no new dependency, no schema migration, no live-TWS
> dependency, no order code, no third timezone, no magnet control; sizes S/M only. One
> phase only — nothing past the D64 batch gate is planned.

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| D61 / `AC-D61.1` (full `Symbol:` label at any width) + Journey 58 + A181 | S-P22-1 (label-field room); Frozen (D19/D20 geometry) | P22-1 |
| D61 / `AC-D61.2` (D19/D20 geometry intact, suites green unmodified) + DG116 | S-P22-1 + AP-P22-4 tripwire; Frozen (toolbar geometry) | P22-1 (P22-4 gate) |
| D62 / `AC-D62.1` (axis re-labels, DST-correct) + Journey 59 axis steps + R134 + DG114 | S-P22-2 (apply path) + S-P22-3 (zone-aware formatting); Frozen (`_chart_call`, `axisProbe`) | P22-2 |
| D62 / `AC-D62.2` (crosshair/tooltip re-label) + Journey 59 hover steps | S-P22-2 + S-P22-3 (shared formatter path) | P22-2 |
| D62 / `AC-D62.3` (every view + persisted — Q103(a) FINAL) + A182 + Journey 59 pop-out/restart edges | S-P22-2 (fan-out + QSettings); Frozen (`_popouts`, D49.6 threading) | P22-2 |
| D63 / `AC-D63.1` (free-only, no snap — Q104(a) FINAL) + Journey 60 + A183 + R136 + FS20 | S-P22-4 (Normal pin, repro-first); Frozen (FS20 stays suggestion) | P22-3 |
| D63 vertical line (DG115, unspecified) + Journey 60 | S-P22-4 (library Normal line; escalate-not-assume tripwire) | P22-3 |
| D64 / `AC-D64.1` (correct labels, toggle-only control — Q105(a) FINAL) + Journey 61 + A184 | S-P22-2 + S-P22-3 + S-P22-5 (basis check) | P22-2 |
| D64 / `AC-D64.2` (shared-cause diagnosis is Plan's) + DG114 | S-P22-2 + S-P22-5; R135 via AR-P22-2 | P22-2 |
| D64 / `AC-D64.3` (history intact) | Frozen Interfaces + S-P22-6 (gate) | P22-4 |
| A185 (display never rewrites stored bars) + R134/R135/R136/R137 | S-P22-3/S-P22-6; Frozen (UTC basis); AR-P22-1…AR-P22-4 | P22-2/P22-3 (R137 via P22-1) |
| A181 (layout fix), A182/A183/A184 (confirmed), Q103/Q104/Q105 answers | Recorded in S-P22-1…S-P22-4 | No phase (no work; resolutions recorded) |

Every D61–D64 expectation is addressed somewhere above; no expectation is narrowed or reinterpreted.

### Phases

Each phase is a milestone, coarser than tasks; the Task Manager decomposes each into
tasks with acceptance criteria and tests. Phases are ordered; a later phase depends
on all earlier ones unless stated. `touches_files` notes list the files a phase
touches and flag the serialisation points.

### P22-1 — Toolbar label-field room — size S

- **Goal:** the `Symbol:` label (and every other toolbar label) renders in full at
  wide and scrolling widths while the D19/D20 strip rules hold exactly.
- **Covers:** D61 (`AC-D61.1`: full-label cases at wide + scrolling widths; `AC-D61.2`:
  content row ~36px, strip ~50–52px, scroll/elide reachability, existing D19/D20
  suites green unmodified); Journey 58 (incl. narrow + HiDPI edges); A181; R137;
  DG116 via the AP-P22-4 tripwire.
- **Deliverables:**
  - `[new/changed] ui/main_window.py` — the S-P22-1 label-field fix (sizing/minimum/
    overflow behaviour around the `Symbol:` field; text/font/style unchanged).
  - `[new/changed] tests` — offscreen wide + scrolling-width label cases (red-first
    on the current `SY` clip) plus the untouched D19/D20 suites as the guard.
- **Dependencies:** none (first phase; reads the frozen D19/D20 geometry, changes
  only the label field).
- **`touches_files`:** `ui/main_window.py` (toolbar block only) + offscreen suites.
  No overlap with any other phase's production edits.
- **Exit condition:** the narrow-width case is red-first on the current tree and
  green after the fix; D19/D20 suites green unmodified; scroll/elide reachability
  holds at every width.

### P22-2 — Timezone apply path + zone-aware formatting (D62 + D64 shared leg) — size M

- **Goal:** flipping UTC↔ET visibly re-labels the axis and cursor times on every open
  view with DST-date-correct labels, persists across restarts, and settles the D64
  axis (one fix or two, per `AC-D64.2`).
- **Covers:** D62 (`AC-D62.1`: per-tick equality vs independently formatted strings
  incl. DST-boundary bars; `AC-D62.2`: crosshair/tooltip text before/after;
  `AC-D62.3`: per-view matrices over main + pop-outs + restart-restore cases);
  D64 (`AC-D64.1`: equity + futures tick matrices in both modes + toggle-only control
  matrix; `AC-D64.2`: the confirmed-or-refuted shared-cause record); Journey 59
  (incl. mid-backfill-flip settling) + Journey 61; A182/A184/A185; R134/R135; DG114
  via S-P22-5.
- **Deliverables:**
  - `[new/changed] ui/lwc_view.py` — `LwcChartView.set_timezone` publishing the tz
    op (S-P22-2); nothing else on the view changes.
  - `[new/changed] ui/lwc_bridge.py` — the tz op channel/envelope shape.
  - `[new/changed] chart_assets/lwc/chart.js` — the tz apply (set var, re-apply both
    formatters, force re-render) + the zone-aware ET formatter (S-P22-3) + the
    S-P22-5 basis confirmation (probe evidence; second display-layer fix only if the
    basis itself is off).
  - `[new/changed] ui/main_window.py` — `_on_tz_changed` fan-out (main + every
    `self._popouts` entry) + QSettings persist/restore (S-P22-2).
  - `[new/changed] tests` — the toggle matrix suites (all red-first on the current
    silent-no-op path) + offscreen + `node --test` formatter cases.
- **Dependencies:** none on P22-1 (disjoint files except `ui/main_window.py`'s
  separate blocks — serialized on that file if waved together); P22-3 consumes its
  formatter path for cursor-time labels.
- **`touches_files`:** `ui/lwc_view.py` + `ui/lwc_bridge.py` +
  `chart_assets/lwc/chart.js` + `ui/main_window.py` (tz block only) + suites.
  Serialised against P22-1 on `ui/main_window.py` and against P22-3 on `chart.js`.
- **Exit condition:** every toggle-matrix case is red-first today (labels don't move)
  and green after (axis × crosshair × tooltip shift by the date-correct delta on all
  views; restart restores); the DG114 record names one seam or two; no stored
  timestamp changes; P21 viewport suites stay green.

### P22-3 — Crosshair free-tracking pin — size S

- **Goal:** the horizontal crosshair line tracks the cursor price continuously with
  no snap anywhere; the vertical line's behaviour is stated, not assumed.
- **Covers:** D63 (`AC-D63.1`: between-close hover cases at rest + during live ticks
  asserting line == cursor; absence cases asserting no Magnet mode id and no snap
  subscriber); Journey 60 (incl. out-of-range clamp edge); A183; R136; FS20 (stays
  a suggestion — nothing built); DG115 via the escalate-not-assume tripwire.
- **Deliverables:**
  - `[new/changed] chart_assets/lwc/chart.js` and/or `[new/changed]
    chart_assets/lwc/interaction.js` — the S-P22-4 pin (Normal-mode application at
    creation + on every crosshair-touching `applyOptions`; snap-source removal after
    the repro names it). Whichever file the diagnosis clears stays `[existing]`.
  - `[new/changed] tests` — the free-tracking suites, red-first on the current
    snap-to-close tree.
- **Dependencies:** P22-2 (consumes the S-P22-2/S-P22-3 formatter path for the time
  label leg; serialized on `chart.js` if waved together).
- **`touches_files`:** `chart_assets/lwc/chart.js` and/or `interaction.js` + suites.
- **Exit condition:** the between-close repro is red-first and green after (line ==
  cursor at every position, never a bar close); absence cases hold; if the vertical
  line needs an owner decision, the phase escalates instead of assuming
  (no silent Q104/Q105 follow-up scope).

### P22-4 — Batch gate — size S

- **Goal:** every `AC-D61.*`–`AC-D64.*` criterion observably satisfied, nothing else
  changed, suite green.
- **Covers:** D64 (`AC-D64.3`: history intact); the full-suite green gate; the
  DG114/DG115/DG116 closure record.
- **Deliverables:**
  - **Batch gate** — full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`, clean run per the
    recorded shared-test-DB / stale-`pytest`-shebang gotchas) + `node --test`
    for the page formatter core green; `AC-D64.3` history-intact check (marker grep +
    the `### D4[1-9]` / `### D5[0-9]` / `### D60` sections present, no pre-P22
    wording touched).
- **Dependencies:** P22-1, P22-2, and P22-3 (verifies their joint behaviour; runs
  after all three).
- **`touches_files`:** offscreen + `node --test` suites only (no production edits).
- **Exit condition:** full suites green; every `AC-D61.*`–`AC-D64.*` observably
  satisfied; no D1–P21 behaviour or wording regressed.

**Wave note.** P22-1 touches only the toolbar block + suites; P22-2 touches the tz
path + suites; P22-3 touches the crosshair path + suites — Task Manager runs P22-2
after P22-1 only as far as the shared `ui/main_window.py` file requires (separate
blocks), and serializes P22-2/P22-3 on `chart_assets/lwc/chart.js`. P22-4 depends on
all three and edits no production files.

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P22-1 | The new `set_timezone` view method publishes a tz op over the existing `LwBridge` envelopes (same batching/replay semantics as `set_series`); no `runJavaScript` eval path is added | The bridge is the established page transport with probe surfaces; an ad-hoc eval would bypass batching and replay (`handle_page_ready`) |
| AP-P22-2 | The persisted choice holds the mode (`UTC` / `Eastern Time`), and `_eastern_offset()` remains the construction-time scalar seed (D49.6 creation threading unchanged); per-tick date-correctness lives page-side, not in the persisted value | Q103(a) persists the choice, not per-bar offsets; the DST edge forces date-aware formatting at render time, which a scalar seed cannot carry — the seed stays for compat, the formatter owns correctness |
| AP-P22-3 | The toggle never refetches: re-label is a format + re-render pass over already-landed bars; a mid-backfill flip settles when the in-flight wave lands on the new offset (never a label mix) | AC-D62.3 promises re-render, not reload; refetching on a label change would waste pacing budget and risk P21 viewport churn |
| AP-P22-4 | The D61 fix stays label-field-local: no D19/D20-fixture-asserted width moves. If diagnosis proves otherwise, the fixtures are re-baselined (values only, assertions never weakened) solely on Analyst sign-off — Build never assumes it | DG116 and `AC-D61.2` ("suites green unmodified") collide exactly when an asserted width must move; the tripwire keeps the collision an Analyst decision, not a silent Build reinterpretation |
| AP-P22-5 | AC-G.1 (visual reference gate) is satisfied by reuse: no new control, glyph, colour, or placement — `Symbol:` keeps text/font/style, the toggle/crosshair/axis keep their visuals; only label correctness and viewport-neutral re-renders change | Same precedent as AP-P21-6/AP-P18 assumptions: presence-gating, not visual language, so no confirmed reference is needed |
| AP-P22-6 | Sizes: P22-2 is M (apply path + fan-out + persistence + zone-aware formatter + basis check + matrices); P22-1/P22-3/P22-4 are S (single-surface fix + suites; snap pin + suites; gate only) | Owner scope sizes; no phase exceeds M |

### Flagged Issues

**None.** Every D61–D64 item is satisfiable as written on the existing stack:

- D61 is a layout fix inside the existing scroll wrapper with a red-first width case
  and an unmodified-suite guard (A181; DG116 handled by the AP-P22-4 tripwire, which
  is a decision rule, not a gap).
- D62's break is diagnosed from source (the `_chart_call("set_timezone")` site names
  a method that exists nowhere in `ui/`; construction-only `_tz_offset`; boot-only
  `lwConfigure`) — the fix is additive plumbing with probe measurables (R134 closed
  by asserting rendered text, not state).
- D63's mechanism is repro-first inside the phase (the AC pins the outcome; the
  snap source is named by the failing repro, with the Magnet-default hypothesis
  recorded but not assumed); DG115's vertical line is stated-then-escalated, never
  assumed.
- D64's "shared cause" is explicitly budgeted by `AC-D64.2` (one fix or two), so
  cause-counting cannot stall the phase; the basis check is display-layer either way
  (A185 holds — no stored timestamp is ever rewritten).
- No `PLAN`-routed escalation is open (all `addressed` — verified 2026-11-10, 104
  entries, zero open/PLAN); no `pending_doc_sync.md` entries remain unapplied (file
  absent); the P21 wave machinery is only read.

Status: READY_FOR_TASK_MANAGER

## Phase P23 — Option Spreads panel in the right dock (D65) — drafted 2026-11-17

> Companion: `docs/architecture.md` § *Phase P23* (Codebase Summary, tech-stack decisions,
> S-P23-1…S-P23-24, frozen interfaces, non-functional approach, AR-P23-1…AR-P23-23).
> Requirements input: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) —
> Phase P23 (D65), Journeys 62–63, **`AC-D65.1`–`AC-D65.19` FINAL** (Q106–Q112 answered
> 2026-11-17; `AC-D65.9` amended by A201 with `AC-D65.11`; **`AC-D65.14`–`AC-D65.19` added
> 2026-11-17 by the owner's plan review**), `### Direction Rule (Q108(b))`, `### Unused-Code
> Rule`, **A186–A212**, **R138–R153**, `design_gaps.md` DG117–DG123,
> `open_questions.md` Q106–Q112. Hard constraints: **D1–P22 are NOT reopened** (the
> D18/D21.13/D44 dock model — **with the single recorded exception of D18's *launch* width,
> A201** — the P6 LWC chart, the P19/P20/P21 viewport and contract machinery, the D27.3
> replay division of labour, and the D45/D46 order-code absence are read-only inputs);
> **no order code of any kind**; display-only option data; no second network client;
> **≤16 option lines + at most one SPX spot line (17 total)**; **sizes S/M only**; one phase
> only — nothing past the P23 batch gate is planned. **DG122 (the P22 orphan sweep) is out of
> scope**: it is a standalone follow-up, scheduled by the analyst, not part of P23's build.
>
> **Implementation-plan handoff.** After the Validator approves this section, the
> Orchestrator produces a human-reviewable implementation plan for the owner instead of
> invoking Task Manager (owner process change, `docs/memory.md` 2026-11-17). The waves below
> are ordered, sized, file-scoped and each carries its tests, deletion inventory and exit
> condition so the document restates without re-planning.
>
> **Revision notes (pass 2, 2026-11-17 — against `docs/plan_review_P23.md`).**
> *(Wave numbers in every revision note up to and including pass 4 are the eight-wave numbering.
> Pass 5 re-cuts the phase into ten waves: read `P23-04` as P23-05, `P23-05` as P23-06, `P23-06`
> as P23-07, `P23-07` as P23-08 and `P23-08` as P23-09. The substance of RC-1…RC-13 is
> unchanged; only the labels moved.)*
> `RG-P23-1` answered by the owner (`A201`; `AC-D65.9` amended: 360 px preferred launch
> width, clamped) — **`FI-P23-1` is resolved**, so the dock-width work is executable and
> the "held assertion" wording is gone (*Flagged Issues* records the resolution, nothing is
> open). Per Required Change: **RC-1** — `tests/conftest.py` joins **P23-07** (its autouse
> teardown wipes the three dropped tables after every test) with an exit-condition line;
> **RC-2** — `tests/test_d45_removal.py` is now split per wave **by test function**
> (`test_removed_panel_members_absent` → P23-01; the `ibkr.account` half of
> `test_p5_end_state_all_removed_members_absent` → P23-06; its schema half → P23-07) and
> is no longer described as a title re-point — **superseded in part by pass 3's RC-7/RC-8
> assignment below, which is the operative one**; **RC-3** — `tests/test_p13_gate.py`'s
> `ui/*.py` allowlist edit is its own deliverable (add `option_spreads_panel.py`, drop
> `active_portfolio_panel.py`), and every other file in P23-01's test book now carries its
> real edit instead of "title/`objectName` only"; **RC-4** — five Frozen Interfaces entries
> in `docs/architecture.md` now carry literal signatures and two consumed ones are frozen
> (`PacingManager.throttle`/`PacingExceeded`, `market_calendar.is_trading_day`);
> **RC-5** — the scan is designed to carry overlap: **one movement primitive** (a
> `reqId`-preserving window step) and a **monotone sweep** for the chain scan, with the
> 16-line accounting in `docs/architecture.md` § *Non-Functional* and **S-P23-5**;
> **AP-P23-6** is rewritten (the pass-1 step-path narrowing is retired); **RC-6** —
> `S-P23-12` group (c) drops `ui/active_portfolio_panel.py` (that is P23-01's). The
> `AC-D65.9` re-derivation is in **P23-01**: preferred width, the launch clamp through the
> existing plan, the two owner-authorised re-baselines, and the wide/narrow fixture
> assertions.
>
> **Revision notes (pass 3, 2026-11-17 — against `docs/plan_review_P23.md`, retry 1).**
> **RC-7** — `tests/test_d45_removal.py`'s third affected group (the `walkthrough` fixture,
> `test_zero_transmit_walkthrough`, `test_positions_table_is_eight_columns`) is now assigned
> per wave: **P23-01** reworks the walkthrough onto the new panel (probe repointed, Portfolio
> half dropped, the one surviving collapse affordance retained) and deletes the eight-column
> test; **P23-05** removes `_stub_account_calls` and its call site in the same wave that
> deletes the account subscription that justified them. The same defect class surfaces one
> file group further and is fixed here as well: **the six D27 account/position suites are
> deleted in P23-01, not P23-05**, because every one of them reads `win.portfolio_panel` (or
> imports `ActivePortfolioPanel`) and therefore dies with the panel, not with the window path
> — with them still present, P23-01's "no `portfolio_panel` reference in `tests/`" could not
> hold for four waves. P23-01's exit condition now names the reworked walkthrough and that
> token-free state. **RC-8** — block (d) of `test_p5_end_state_all_removed_members_absent` is
> **rewritten in P23-06**, the wave that deletes its three subject classes: the existence loop
> (`:914-919`) and the `build_position_from_ib` paragraph become
> `data.models.Position`/`TradeGroup` **absence** assertions, and the then-unused
> `import inspect` goes with them; P23-06's exit condition names it, and P23-07 keeps only
> block (g), its fixtures and the carve-out. **RC-9** — the last artefacts of the withdrawn
> probe design are gone: `scan_anchor(...)`/`next_step(...)` leave the ladder's surface in
> `docs/architecture.md` (replaced by `window_legs(anchor_short)`), "Per scan: O(log n)" is
> restated as `O(k)` window steps, and `ui/ticker_session.py`'s
> `get_bars(self, timeframe: str) -> list[Bar]` joins Frozen Interfaces (tie-break 3's only
> price source). **RC-10** — the `AC-D65.9` narrow fixture moves from 1100×700 (352 px cap,
> 8 px under the preferred width) to **900×700** (272 px cap, ≈84 px name column), so the
> elide + tooltip path is asserted with real margin.
>
> **Revision notes (pass 4, 2026-11-17 — against `docs/plan_review_P23.md` retry 2,
> `RC-11`–`RC-13`).** *(Eight-wave numbering — see the pass-2 note's conversion table.)**
> **RC-11** — the rename's whole lookup surface is scheduled, not just the two files that
> assert: **twenty** surviving modules key a right-dock lookup on the retired identity and
> **all twenty are edited in P23-01**, the rename's own wave, by file and line in
> P23-01's test book. The predicate becomes `dock.objectName() in ("Option Spreads",)` —
> `objectName`, not the new title string — and the three sentinel assertions keep their
> `assert` on the new key. P23-01's exit condition and P23-08's batch gate now state the
> absence as exact greps over `tests/` (with one documented carve-out) instead of a prose
> claim. *(The review's list of nineteen missed
> the third hard-fail site: `test_dock_widths_d17.py` asserts `hidden == 1` and is a hard
> failure at P23-01 on its module constant, not a silent no-op.)*
> **RC-12** — `tests/test_dock_d18_region.py`'s entry is re-anchored: the `:32` module
> import, four groups, `T48-T03` (`:154-181`) named explicitly, the `:133` collapsed-floor
> assertion corrected (it is inside `T48-T02`, not `:150-172`), and `_receiver_count`'s
> removal scheduled with its only call site.
> **RC-13** — P23-05 now **deletes** the five inert `_record_symbol_price` fake-host stubs, so
> its tree-wide exit claim is literally true rather than narrowed.
> **Root-cause sweep (same defect class, two more sites found and fixed here):**
> P23-06's `tests/test_ui_smoke.py:48` edit is made mandatory (the `hasattr(data.models,
> "Position")` assertion hard-fails the moment P23-06 lands, and the previous "re-pointed if
> it guards the smoke surface" was not decidable), and P23-04's stream suite now schedules
> the fake client's two account-call recorders for deletion in P23-05 with the calls they
> absorb. The audit these fixes rest on is the **exit-condition audit** table below the
> eight waves. It also caught a conflict the three required changes did not name: P23-07 and
> P23-08 **spell** the retired tokens inside `tests/` (the forbidden-token tables), so a
> "grep `tests/` returns nothing" exit would redden on the gate itself two waves later.
> P23-01's exit and P23-08's re-run therefore carry an explicit, documented carve-out for
> those literal-string tables — and for nothing else.
>
> **Revision notes (pass 5, 2026-11-17 — owner-driven, against the amended `AC-D65.14`–`AC-D65.19`;
> this section is now `READY_FOR_VALIDATION` again).** The owner reviewed the derived
> implementation plan and returned ten findings; the requirements were amended to answer them
> and the waves below are re-cut from ten of them, one home each, with tests:
> **(1) connection lifecycle** → new **P23-04** (engine states + per-line error classes) and
> **P23-05** (registry registration with `reissue`, `_replay_subscriptions`'s one added tag,
> disconnect → `STALE` + frozen walk, reconnect → replay, `AC-D65.14`).
> **(2) seed + spot** → **P23-03** (three-tier seed, ≤6 probes/side, leases, 3 s pending,
> 10 s / 12-pair bound, `AC-D65.15`) and **P23-05** (the one spot line and its routing, the
> **16 + 1 = 17** ceiling).
> **(3) signs** → **P23-01** (the `display_bases`/`credit_bases` pair and the ASK↔credit_bid
> label swap) and **P23-03/04** (every `d`, message and step on credit only).
> **(4) quote validity** → **P23-01** (`usable_quote`) + **P23-03** (a pair is never scored or
> matched on one side).
> **(5) band** → **P23-01** (`option_tick`/`match_band`) + **P23-03** (match and move both on
> `h`), pinned at `T = 1.00`, `2.95`, `3.00`.
> **(6) Target validation** → **P23-01** (range, message, revert, no emit) + **P23-05** (no
> ladder state change in a live window).
> **(7) backup before the drop** → **P23-08** (`data/db_backup.py`, verified copy, row counts,
> abort-on-failure, `AC-D65.18`).
> **(8) full file set** → **P23-06** (the price sink in `ui/watchlist_panel.py` and
> `ui/ticker_session.py:562`, already scheduled) + **P23-08**'s file-set-wide residue grep.
> **(9) live-TWS, read-only acceptance** → new **P23-10**, an explicit owner-run gate against
> `127.0.0.1:7496` with a recorded checklist (`AC-D65.19`; observation-only, no order-shaped
> call exists or is possible), which the residue gate in **P23-09** explicitly does *not* claim.
> **(10) fixture convention** → **P23-01** (canonical `7425/7445` and `7340/7320` plus the
> guard that rejects any 10-wide pair or inverted PCS row, `AC-D65.2`/A212) and the fence on
> every fixture in **P23-03/05**.
> **Wave count 8 → 10** (the engine splits into measurement and maintenance/lifecycle; the
> acceptance run gets its own wave). Every renumbering is applied through the exit-condition
> audit, the deletion inventory and the serialisation note — no wave's exit now reads a
> subject another wave owns. **The two literal-vs-tree conflicts this pass surfaced were
> resolved in the requirement text on 2026-11-17**: **FI-P23-2** (`AC-D65.15`'s spot source is
> now the phase-stable chain 3a/3b/3c — `_symbol_last_prices` is explicitly *not* a source and
> `AC-D65.13`/`AC-D65.18` still delete it) and **FI-P23-3** (`AC-D65.14`(ii) now names the
> **`OPTION_LEGS`** tag verbatim, with `AC-D22.7.2`'s `MARKET_DATA` replay exclusion unchanged).
> The waves are written against the amended text, not against a recommendation.
>
> **Revision notes (pass 6, 2026-11-17 — against `docs/plan_review_P23.md` `RC-1`–`RC-7`).**
> **RC-1** — the spot chain is now exactly `AC-D65.15`'s three tiers, tier for tier:
> **3a** the chart's `_last_chart_price` **only when the charted symbol is SPX**; **3b**
> otherwise **exactly one** dedicated SPX spot line (counted, cancelled when the seed
> completes); **3c** refused/unavailable ⇒ **no** spot, the coarse probe runs region-less and
> the seed still completes. The two invented tiers (an existing SPX `TickerSession`'s last
> close, then an engine-level memory tier ahead of the line) are **deleted**, and the stream
> suite's expectation is inverted to the AC's: chart on SPX ⇒ **zero** spot lines; chart on
> any other symbol ⇒ **exactly one**. Rewritten: **AP-P23-15**, **AP-P23-2**, **AP-P23-16**,
> P23-05's spot deliverable, its stream-suite spot group and its exit, the `AC-D65.15`
> traceability row, *Flagged Issues*; in `docs/architecture.md` the Summary, the Tech Stack
> *Spot source* row, Integration Points, the *seeding* paragraph, and **S-P23-13**,
> **S-P23-18**, **AR-P23-12**.
> **RC-2** — the leg tag is **`OPTION_LEGS`** (`AC-D65.14`(ii); value `"option_legs"`, matching
> the module's lowercase tag strings) and the conflict framing is gone: AP-P23-14, P23-05's
> registry deliverable, *Flagged Issues* (FI-P23-1/-2/-3 all recorded **resolved 2026-11-17**),
> and the architecture's component list, S-P23-17, AR-P23-16 and the `[revises D27.3 …]`
> bullet name the constant and the replay include set as the AC states them.
> **RC-3** — P23-06's exit now names only tokens that are gone when it fires: the
> `ui/`-scoped handler/state tokens, `reqPositions`/`reqAccountSummary` and the price-sink
> chain. The bridge's `account_summary`/`position_update` (which survive in
> `ibkr/bridge.py:43-46` until P23-07) and `data/db.py:189`'s `_upsert_position` comment (which
> dies with the unique index in P23-08) are no longer claimed by P23-06; **P23-07's exit gains
> the explicit four-token grep**, and the audit table's P23-06 row is corrected.
> **RC-4** — the traceability table's *Phase* column is re-derived against the ten waves
> (nine rows corrected, two omissions filled).
> **RC-5** — P23-09's ban list is A212's actual typos, `7425/7435` (10-wide) and `7315/7435`
> (inverted PCS). `7435/7455` is a legal 20-wide pair and `AC-D65.9`(i)'s own width example, so
> it is no longer banned.
> **RC-6** — the `docs/architecture.md` header restates the ten-wave reality
> (`AC-D65.1`–`AC-D65.19`, A186–A212, R138–R153, Q106–Q112, three resolved flagged issues) and
> the registry tag anchor reads `:35-37`.
> **RC-7** — `docs/codebase-map.md` gives `ui/active_portfolio_panel.py` a
> **`[deleted in P23]`** status, names the tag **`OPTION_LEGS`**, and re-cuts the two stale
> wave numbers in its P23 test-impact note.
>
> **Same-defect-class sweep (RC-3 / RC-5's rule: an exit must not redden on text it requires).**
> P23-08's instrument re-baseline no longer tokenises the **three dropped table names**: the
> one-time `DROP TABLE IF EXISTS …` in `data/db.py` and the absence assertions in
> `test_db_schema.py`/block (g) must spell the names they drop and prove gone, so adding them to
> `_FORBIDDEN` would make the re-baselined instrument red on the migration it describes. Their
> absence is measured by the **schema case** (`sqlite_master`), and `data/db.py:189`'s
> `_upsert_position` comment (the one surviving spelling of a token that *is* forbidden, which
> would otherwise redden `data/db.py`) is deleted with the unique index in P23-08. The
> `_ALLOWED_IN_FILE` stop/target carve-out still goes: the columns it existed to exempt are
> dropped, so it has no subject left.
>
> **Revision notes (pass 7, 2026-11-17 — retry 3, against `docs/plan_review_P23.md` `RC-14`–`RC-15`).**
> Both are the same defect class the phase has been fighting — a claim (or an exit) outliving the
> subject it reads — now at the one place outside the deletion inventory: the connection badge.
> **RC-14 — the badge is the account path's last surviving reader, and it is now scheduled.**
> Decided in `docs/architecture.md` **S-P23-24** (`[revises D26]`): the badge states the
> **connection**, not the account. (i) `_update_conn_badge` (`:1645-1659`) is rewritten in
> **P23-06** to `conn_badge_text(monitoring_paused=self._tws_paused)`; `conn_badge_text`
> (`:201-223`) loses its `account_id`/`account_type` parameters and the `DU`/`DEMO`/`PAPER`
> branch, returning `"● Connected"`/`#34d399` when connected and D40's paused wording amber while
> `_tws_paused`; `"● Connecting"` (construction) and `"● Disconnected"` (`:2087`) are untouched.
> **Why no surviving source:** both account-typed inputs arrive on the account-summary stream this
> phase deletes, and the fail-fast port guard proves the *port* only — D26.5's own note allows a
> paper account on it — so a port-derived "Live" would be the hardcoded claim `AC-D26.5` forbade;
> per the review, no source is invented. The retirement is a **recorded consequence** of
> `AC-D65.13`/A194 (P23-06's deliverable, P23-09's gate record, `_account_id` in P23-08's token
> list, the *Flagged Issues* note), **not** a fourth `AC-D65.11` edit. *(ii)* `_account_id` — which
> has no declaration, only the write at `:4336` and the read at `:1653` — is deleted with its
> writer in P23-06 and joins the residue tokens; `_account_summary` goes with `_on_account_summary`.
> No write-less attribute survives. *(iii)* The `account_summary` call site at `:1651` is **changed
> in P23-06** (the preferred route — it is that wave's subject), so P23-07's four-token grep over
> `ui/` is true when it fires; P23-06's exit gains `_account_id`/`_account_summary` so the edit is
> asserted, not implied. The two architecture claims that called the badge "reused unchanged"
> (`Integration Points`, **S-P23-10**) now say re-pointed; **S-P23-24** and **AR-P23-23** record
> the decision and its failure mode.
> **RC-15 — the last `Account Summary` in `ui/` is scheduled with the wave that edits its function.**
> **P23-01** rewrites `_compute_right_dock_collapsed_min_width`'s docstring (`:3585-3587`,
> *"the Portfolio (Account Summary) header button"* → the `Option Spreads` header button) beside
> the code re-point it already owned, re-points `tests/test_right_dock_d21.py`'s module docstring
> (`:7`) with `:75`'s text assertion, and `tests/test_watchlist_nonregression_d22.py:161`'s text
> assertion; P23-01's exit now greps `ui/` for `Account Summary`, so the token is genuinely absent
> before P23-08 adds it to `_FORBIDDEN`.
> **Same-class sweep — every forbidden token → its last carrier → the wave that removes it** (scope:
> the instrument reads `ui/ services/ data/ ibkr/ config/` as AST identifiers + string constants and
> `ui/` again as raw text; `tests/` is covered by the waves' own greps). Verified in the tree today:
>
> | Token | Last carrier after that wave's edit | Wave |
> |---|---|---|
> | `ActivePortfolioPanel` | `ui/active_portfolio_panel.py:34`, `ui/main_window.py:76,638`, `ibkr/account.py:39` (comment) | P23-01 (panel + import + attr); P23-07 (`ibkr/account.py` whole file) |
> | `portfolio_panel` | **every** site dies here (RC-16): the dock block `:638,641,642,662`, the three probes `:3591,3606,3638`, and the ten `ActivePortfolioPanel` API calls `:849,850,852,1731,2072,4349,4350,4357,4468,4538` | **P23-01 only** — the rename, the probes and all ten call sites, so the token is absent from `ui/` when the wave ends |
> | `positions_table` | `ui/active_portfolio_panel.py` only | P23-01 |
> | `Account Summary` | `ui/main_window.py:3586` (docstring), the panel's header string | P23-01 (RC-15) |
> | `account_summary` | `ui/main_window.py:1651` (badge) + handlers/init; `ibkr/bridge.py:43`, `ibkr/client.py:455` | P23-06 (`ui/`); P23-07 (`ibkr/`) |
> | `account_summary_end` | `ui/main_window.py:844,4353`; `ibkr/bridge.py:44`, `ibkr/client.py:459` | P23-06; P23-07 |
> | `position_update` | `ui/main_window.py:845,4399`; `ibkr/bridge.py:45`, `ibkr/client.py:463` | P23-06; P23-07 |
> | `position_end` | `ui/main_window.py:846,4371,4470,4482`; `ibkr/bridge.py:46`, `ibkr/client.py:467` | P23-06; P23-07 |
> | `build_position_from_ib` | `ui/main_window.py:4403`; `ibkr/account.py:51` | P23-06; P23-07 |
> | `_parse_contract_type` | `ibkr/account.py:46,70` | P23-07 |
> | `detect_and_group` | `ui/active_portfolio_panel.py:23,252`; `services/strategy_detection.py:166` | P23-01; P23-07 |
> | `OptionLeg` | `services/strategy_detection.py` | P23-07 |
> | `strategy_detection` | `ui/active_portfolio_panel.py:23`; `services/strategy_detection.py` | P23-01; P23-07 |
> | `Position` | `ui/main_window.py:80,904,4493,4530,4541` **and the comment at `:891`**; `data/models.py:74`, `ibkr/account.py`, `services/strategy_detection.py` | P23-06 (the `:891` comment is now named with `_symbol_last_prices`); P23-07 |
> | `TradeGroup` | `data/models.py:91` | P23-07 |
> | `_upsert_position` | `ui/main_window.py:4467,4541`; `data/db.py:189` (comment) | P23-06; P23-08 |
> | `_symbol_last_prices` | `ui/main_window.py:893,3385,4460` (+ its `:890-892` D27.5 comment) | P23-06 |
> | `_record_symbol_price` | `ui/main_window.py:767,3382`, `ui/ticker_session.py:562`, five test stubs | P23-06 |
> | `set_price_sink` | `ui/main_window.py:767`, `ui/watchlist_panel.py:954` | P23-06 |
> | `_price_sink` | `ui/watchlist_panel.py:391,956,1149,1152` | P23-06 |
> | `reqAccountSummary` | `ui/main_window.py:1721,1729`; `ui/active_portfolio_panel.py:43,173` | P23-06; P23-01 |
> | `reqPositions` | `ui/main_window.py:1716,1718` | P23-06 |
> | `_account_id` | `ui/main_window.py:1653` (badge read), `:4336` (write); panel `:46,170,179,233` | P23-06; P23-01 |
>
> Three carriers the sweep added to the schedule, all in waves that already edit the file:
> `ui/main_window.py:891`'s comment (spells `Position`, and points at `_last_chart_price` as
> "never" the source — stale twice over) now leaves **with `_symbol_last_prices` in P23-06**;
> `tests/test_port_guard.py`'s four badge cases (`:25-51`) are replaced in **P23-06** with the new
> connected/paused contract (its two port-guard cases at `:13-21` are untouched — that rule is
> exactly what survives); and the dock block's own `Portfolio`-naming comments
> (`ui/main_window.py:630-634`, and `:854-855` — *(RC-16: corrected — these describe the replaced
> panel and leave with it in P23-01, not with P23-06's block)*) go with the code they describe.
> `Portfolio` on its own is **not** a forbidden token, so `ui/dock_layout.py`'s
> two "(Portfolio) dock" comments are deliberately left: that module is frozen and unchanged this
> phase, and neither comment is a title, an `objectName` or a lookup key (`AC-D65.1`'s measurable is
> `tests/`-wide).
>
> **Revision notes (pass 8, 2026-11-17 — retry 4, against `docs/plan_review_P23.md` `RC-16`,
> owner-decided: MERGE).** The panel-swap wave (**P23-01**) performs the rename **and** resolves
> every dereference of the renamed attribute, so no code path can reach the old name. The owner's
> decision is applied as the review's first option, and it is also the only mechanically sound
> one: after the rename the attribute **does not exist**, and the ten calls address
> `ActivePortfolioPanel`'s own API (`set_account_summary`, `set_account_id`,
> `set_account_unavailable`, `set_positions`, `add_position`) — the new panel has **none** of those
> methods — so "renaming" those lines would raise `AttributeError` on the *new* panel instead of
> the old attribute. They are **deletions**, not re-points, and they belong to the wave that
> retires their receiver.
>
> **Per-site disposition — ten call statements at the eight locations RC-16 names, all in
> `ui/main_window.py`:**
>
> | Site | Today | Here (P23-01) | Stays, and whose |
> |---|---|---|---|
> | `:849`, `:850`, `:852` in `__init__` (block `:848-855`, with the `D27.6`/`D45` comments) | `set_account_summary({})`, `set_positions([])`, `set_account_unavailable(True)` | **deleted with the block** — no panel state to initialise, no availability flag to set | nothing: the block's whole subject is the deleted panel. The four `b.*` connects above it (`:842-846`) are **P23-06's** |
> | `:1731`, last statement of `_subscribe_account_data` | `set_account_unavailable(False)` | **deleted** (one line) | the method's own body — `reqPositions()`/`reqAccountSummary(...)`, `_account_subscribed = True` — unchanged, **P23-06's** deletion |
> | `:2072`, `_on_disconnected` | `set_account_unavailable(True)` | **deleted** (one line) | the account state clears above it (`:2066-2071`) are **P23-06's** |
> | `:4349`, `:4350`, `_on_account_summary` | `set_account_id(account or None)`, `set_account_summary(summary)` | **deleted** (two lines) | the handler keeps its behaviour — the `_account_summary`/`_live_accounts`/`_account_id` collection and the `_update_conn_badge()` call — and dies whole in **P23-06** |
> | `:4357`, `_on_account_summary_end` | `set_account_summary(dict(summary))` | **deleted** (one line) | the status line and the ESC-052 prune guard stay with the handler, which dies in **P23-06** |
> | `:4468`, `_on_position_update` | `add_position(position)` | **deleted** (one line) | the position build and `_upsert_position` stay with the handler, which dies in **P23-06** |
> | `:4538`, `_on_position_end` | `set_positions(positions)` | **deleted** (one line) | the bulk read and `_positions_rendered = True` stay; **P23-06** deletes the read whole, including the `positions` local this deletion strands |
>
> **No handler is deleted in P23-01.** None of the four is panel-only: each is account-path work
> whose subject (the account-summary stream, the position stream, the prune, the bulk read) is
> P23-06's, so the merge removes their **panel calls** and leaves each handler's real subject with
> the wave that deletes it. That is the merge's whole shape — **P23-01 owns the receiver** (the
> rename and every line that addresses the old attribute), **P23-06 owns the account path** those
> handlers exist for.
>
> **One recorded intermediate, not a leak:** after P23-01, `_on_position_end`'s
> `positions = [Position(...) for row in rows]` (`:4530-4537`) has no reader until P23-06 deletes
> the bulk read whole. It is deliberately left — deleting it here would strand `rows` one level up
> and would take that wave's subject — it is a **local name**, not one of P23-08's forbidden
> tokens, and no exit in this phase reads it (every exit is a token grep or a suite, and the
> render assertion that would have read it is P23-06's subject there).
>
> **P23-06 shrinks to the residue it still owns:** the four `b.*` connects (`:842-846`),
> `_subscribe_account_data` and its connect-time call (`:1676`), the handlers' bodies and their
> mutual helpers (`_on_account_summary`, `_on_account_summary_end`, `_on_position_update`,
> `_on_position_end`, `_prune_foreign_positions`, `_upsert_position`, the bulk DB read), the six
> state fields and their comment block (`:890-913`), the account state clears (`:2066-2071`), the
> status line, the two dead imports, and the price-sink chain — plus S-P23-24's badge block. Its
> deliverable no longer claims the panel initialisers, its deletion-inventory row no longer lists
> them, and its exit reads none of them.
>
> **The plan's own "survives until P23-06" claim was false and is corrected** (P23-01's six-D27-suites
> bullet, and P23-06's deliverable): the account-path *behaviour* survives only in its
> subscription/state/bookkeeping half; its panel half cannot survive the rename and does not.
>
> **What proves a window still works between the two waves** (named in P23-01's exit):
> `tests/test_d65_option_panel.py` (constructs, and rebuilds, a real window and asserts the launch
> width); `tests/test_d45_removal.py`'s reworked `walkthrough` and
> `test_zero_transmit_walkthrough` (a real window driven through the surviving affordances);
> **`tests/test_d27_reconnect.py:183-215`** — the one surviving suite that walks
> `_on_connected()` → `_subscribe_account_data` → `_on_disconnected()` → `_on_connected()` on a
> real window, so `:1731` **and** `:2072` are both executed; `tests/test_d41_removal.py:355` and
> `tests/test_d40_tws_lifecycle.py:437` (two more `_on_connected`/`_on_disconnected` walks); plus
> the eight book suites and the twenty lookup modules, every one of which builds a window. The four
> handlers' deleted call sites are reached by **no** surviving test after this wave — the four
> suites that drove them (`test_d27_account_subs`, `test_d27_account_scoping`,
> `test_d27_account_partial_window`, `test_d27_position_id`) are deleted in this same wave — so
> they are dead-but-importable until P23-06, never a red suite.
>
> **Also updated for the merge:** the forbidden-token sweep's `portfolio_panel` row (now
> P23-01-only, every carrier line named), P23-01's `ui/main_window.py` deliverable / `Touches` /
> exit, P23-06's goal / deliverable / `Touches` / exit, both exit-audit rows, the serialisation
> note, two deletion-inventory rows, **AP-P23-8**'s sizing line, the `AC-D65.13` traceability row,
> and in `docs/architecture.md` the `[revises D41]` bullet, the `ui/main_window.py` component
> entry, the Codebase Summary's account-path inventory, **S-P23-12**'s wave list, and a new
> **AR-P23-24**.

### Traceability (requirement → architecture → phase)

| Requirement / input | Architecture section | Phase |
|---|---|---|
| `AC-D65.1` (panel shell, sub-headers, columns, Target, red/green toggle, **and the title/`objectName` search asserting no `Portfolio` dock remains**) + Journey 62 steps 1–3 + A194 | S-P23-1, S-P23-11; Tech stack (toggle colour); Frozen (VIS-D21, `dock_layout`) | P23-01 (shell + the 20 dock lookups), P23-09 (the re-run on the finished tree) |
| `AC-D65.2` (20-wide ladder, one offset formula, short-leg-first naming, listed strikes, SPX not the charted symbol, today's expiry) + Journey 62 steps 5,7 + A186/A187 + DG120 | S-P23-2, S-P23-6, S-P23-14; Data Model (`OptionSeries`) | P23-01 (geometry/naming), P23-02 (chain/expiry) |
| `AC-D65.3` (anchor minimises three-basis `d` **on credit bases**, three tie-breaks, selected through the seed ladder) + Journey 62 step 5 + A188 + A207 | S-P23-3 (credit vs displayed), S-P23-5 (window step + leases), S-P23-13, S-P23-18 (seed) | P23-03 |
| `AC-D65.4` (one 5-point step both legs, decided direction, stop rules, no oscillation, chain-edge message, **`h = max(0.05, one_tick)` pinned at both levels**) + Journey 62 step 6 + A189/A191/A204 + R139/R153 + DG117 | S-P23-4, S-P23-20 (band); Non-functional (cadence) | P23-01 (band function), P23-03 (the rule), P23-04 (ordered steps, stop rules, stationary feed, no oscillation) |
| `AC-D65.5` (**owner's displayed formulas** `ASK = long.ask − short.bid`, `BID = long.bid − short.ask`, `Δ/Γ = long − short`; greek precedence model → last → bid/ask mean; **never mixed across legs**; `—` on partial legs; no polling) + A190/A202/A203 + DG118 | S-P23-8, S-P23-3 (sign pair), S-P23-19 (validity); Non-functional (streaming fidelity) | P23-01 (basis/formatter pair), P23-02 (intake), P23-04 (greek source precedence + never-mixed), P23-05 (render) |
| `AC-D65.6` (**≤16 option lines**, drop/cancel timing, shared legs, guard, **probe leases are capacity-neutral**) + Journey 62 postconditions + A196/A206 + R138/R150 + DG123 | S-P23-5 (window step + leases), S-P23-9 (16 + 1); Non-functional (line accounting); Frozen (`assess`, `req_mkt_data`) | P23-03 (leases + sweep), P23-04 (the shared-leg rule on a re-anchor), P23-05 (issuance + spot line) |
| `AC-D65.7` (maintenance semantics; zero orders in any state) + D45/D46 | S-P23-9, S-P23-15; Frozen (order absence) | P23-05 (ON→move→OFF→ON, zero orders), P23-09 (the order-absence sweep) |
| `AC-D65.8` (degraded states, one message per cause, `No 0DTE expiry today`, **post-16:15 cutoff state**, recovery) + Journey 63 + Q107(b) + A193/A205 + R140/R144 | S-P23-10, S-P23-6, S-P23-9; AR-P23-6/AR-P23-11 | P23-02 (chain-level), P23-03 (latches), P23-04 (lifecycle causes), P23-05 (surfacing + cutoff) |
| `AC-D65.9` (360 px preferred launch width = `clamp(360, 200, right_dock_max_width(chart_area))`, names legible at launch, elide + tooltip below it, every dock rule intact, the two owner-authorised D18 re-baselines) + A201 + DG119 + A194 | S-P23-16, S-P23-1; Frozen (`dock_layout`, `right_dock_max_width`) | P23-01 (launch width, shell, elide), P23-09 (the gate) |
| `AC-D65.10` (coalesced repaint, no GUI-thread stalls) | S-P23-11; Non-functional (threading) | P23-05 |
| `AC-D65.11` (history intact; only the three recorded pre-P23 edits — the D41 title re-points, A194's supersession, and A201's D18 launch-width amendment with its two re-baselines — **plus one recorded phase-internal consequence: S-P23-24, the D26.5 badge derivation retiring with the account path, which changes no `requirements.md` text and is therefore not a fourth edit**) | Frozen Interfaces; S-P23-24 | P23-09 (the gate record, including the S-P23-24 consequence) |
| `AC-D65.12` (no unused residue — standing gate, seeded-fixture-proven) + A197 | S-P23-15; AR-P23-10 | P23-08 (the displaced-token half), P23-09 (the gate + its seeded-red fixture) |
| `AC-D65.13` (displaced stack absent **across the full file set AC-D65.18 names**; KEEP reasons present; three tables dropped) + A198/A200/A210 + DG121 + R146 | S-P23-12, S-P23-13, S-P23-15, **S-P23-24** (the badge, the account plane's last reader) | P23-01 (panel, **its ten call sites**, the six D27 suites + the title-keyed lookup surface), P23-06 (the account-path residue **and the badge's account read**), P23-07, P23-08, P23-09 |
| `AC-D65.14` (connection lifecycle: `STALE` + frozen walk on disconnect; registry replay on reconnect; per-line errors **200 / 10197 / 354 / 162 / other** with the defined re-seat rules; ON/OFF never survives a restart) + Journey 63 steps 4–5 + A193/A209/Q111 + R150 | S-P23-17 (registry tag + replay), S-P23-10 (error classes), S-P23-9; Non-functional (lifecycle); Frozen (`SubscriptionManager.subscribe`/`replay_all`) | P23-04 (engine states + classes), P23-05 (registry, replay, wiring) |
| `AC-D65.15` (seed ladder: session anchor → ≤6 coarse probes/side at 20-pt spacing → 5-pt refine; spot is an accelerator on the **3a/3b/3c** chain — chart price **only when the chart is on SPX**, otherwise **exactly one** dedicated spot line, otherwise none ⇒ **16 + 1 = 17**; 3 s leg timeout ⇒ pending and ineligible; sweep **10 s or 12 scored pairs**) + A206/A207/A208 + Q112 + R150/R151 | S-P23-18, S-P23-5 (leases), S-P23-13 (spot chain); Non-functional (seeding, line accounting) | P23-03 (seed tiers + bounds + leases), P23-05 (spot tiers 3a/3b/3c + routing + guard) |
| `AC-D65.16` (zero bid is live; `-1`/`1.7976931348623157e+308`/no-tick zero absent; one-sided pairs never match; sentinel transition) + A202/A208 | S-P23-19; Non-functional (streaming fidelity) | P23-01 (`usable_quote`), P23-03 (scoring gate) |
| `AC-D65.17` (Target `0.05 ≤ T ≤ 19.95`; blank/0/negative/NaN/Inf/≥20 rejected with one message and **no state change**) + Journey 63 step 6 | S-P23-23 (panel gate), S-P23-20 (band, for the accepted range's own behaviour) | P23-01 (range + message + revert + no emit), P23-05 (no ladder change in-window) |
| `AC-D65.18` (verified pre-drop backup, abort on failure; **full deletion file set** incl. `ui/watchlist_panel.py` and `ui/ticker_session.py`) + A210 + R152 | S-P23-21 (backup), S-P23-12 (file set); Codebase Summary (paths/migration seam) | P23-06 (the two modules beyond `main_window`), P23-08 (backup + drop + file-set grep) |
| `AC-D65.19` (owner-run live-TWS, **read-only** acceptance on `127.0.0.1:7496` — observation-only, no order-shaped call exists or is possible; six checklist items; recorded like D48/D52; a phase gate, waivable only by record) + A211 + R144 | S-P23-22 | P23-10 (built as P23-T26) |
| DG117 (chain edge) / DG118 (price-only ladder) / DG119 (D41 supersession) / DG120 (strike grid) / DG121 (data drop + `_symbol_last_prices`) | S-P23-4 / S-P23-3+8 / S-P23-1 / S-P23-14 / S-P23-12+13 | P23-03 / P23-03–04 / P23-01 / P23-01–02 / P23-06–08 |
| DG123 (single-consumer code must not be born dead) | S-P23-7, S-P23-15; Tech stack (payload minimalism) | P23-01…P23-04 |
| DG122 (P22 orphan sweep) | **not planned** — standalone follow-up (out of P23 scope) | — |
| R147 (naive scan vs name-invoked callbacks) / R149 (empty on weekends) | S-P23-15 / S-P23-6 | P23-09 / P23-02+04 |

Every `AC-D65.*` expectation — `AC-D65.1` through `AC-D65.19` — is addressed somewhere above;
nothing is narrowed or reinterpreted. All three conflicts this phase raised are **resolved in
the requirement text on 2026-11-17** and the waves implement the amended text verbatim: the
one that contradicted a shipped D18 default (`AC-D65.9`) by the owner (`A201`/`RG-P23-1`), the
spot chain (`FI-P23-2` → `AC-D65.15`'s phase-stable 3a/3b/3c tiers, A206), and the leg tag
(`FI-P23-3` → `AC-D65.14`(ii)'s `OPTION_LEGS`, with `AC-D22.7.2`'s `MARKET_DATA` replay
exclusion untouched). No Plan assumption replaces a requirement's *outcome* any more; the
remaining interpretive readings are stated as assumptions (AP-P23-11, -18, -21) and none
changes a criterion's measure.

### Phases

Ten waves, milestone-level; Task Manager decomposes each into tasks with acceptance
criteria and tests. Waves are ordered and each depends on its predecessors unless stated.
Sizes S/M only — no wave is L. `Touches` lists production files and flags serialisation
points.

### P23-01 — Panel shell + ladder math + dock swap + launch width — size M

- **Goal:** the right dock hosts an `Option Spreads` panel with the specified shell, ladder
  geometry and naming, **opening at the panel's preferred width clamped inside the existing
  cap**, **validating its Target at the panel** and **rendering the owner's displayed signs from
  the same helper pair the credit bases come from**, and the Portfolio panel and its module are
  gone.
- **Covers:** `AC-D65.1` (shell, column tuple, row counts, Target default, toggle placement
  and colour states); `AC-D65.2`'s geometry/naming half **and its fixture-convention guard**
  (A212: canonical `SPX Nov17 7425/7445` CCS and `SPX Nov17 7340/7320` PCS, 10-wide and
  inverted-PCS rows rejected); **`AC-D65.9` in full** — the 360 px preferred width, the
  `clamp(360, 200, cap)` launch, elide + tooltip below it, every D18 / D21.13 / D44 rule
  untouched, and the **two** owner-authorised D18 re-baselines (A201); **`AC-D65.17`**'s panel
  half (`0.05 ≤ T ≤ 19.95`, one message, revert, no emit — the in-window "no ladder change"
  half is P23-05's); **`AC-D65.16`**'s `usable_quote` screen; **`AC-D65.4`**'s band function
  (`option_tick`/`match_band`); **`AC-D65.5`**'s basis/formatter pair (the displayed values and
  their credit counterparts); Journey 62 steps 1–2, 5 (structure only); A187/A202/A204/A212;
  DG120's snap helper; DG123.
- **Deliverables:**
  - `[new] ui/option_spreads_panel.py` — `OptionSpreadsPanel` per S-P23-1: header
    `DiagonalStrikeButton("Option Spreads")` (exposed as `header_button`), controls row
    (`Target` field defaulting to `1.00` **with S-P23-23's validation gate: `0.05 ≤ T ≤ 19.95`,
    one message naming the range, the field restored to the last valid value, and no
    `target_committed` emitted on a rejection**, ON/OFF toggle right-aligned with the
    `spread_state` property and the two colour constants), status label, `CCS`/`PCS`
    sub-headers, two 4×5 tables with the exact header tuple (held as `ccs_table`/`pcs_table`
    — the members `apply_snapshot` writes and the shell/walkthrough tests read), empty-state
    label,
    tooltip-carrying name cells eliding with an ellipsis under a narrowed column,
    `PREFERRED_WIDTH = 360` + `preferred_width() -> int` + a `sizeHint()` whose width is the
    preferred width, `apply_snapshot`, `set_status`, `set_empty_state`,
    `target_value`/`set_target_value`, `toggle_state`/`set_toggle_state`,
    `toggle_clicked`/`target_committed` signals,
    `is_collapsed`/`set_collapsed`/`toggle_collapsed`.
    *(Note: the panel's `toggle_clicked`/`target_committed` signals are declared here and
    receive their engine receivers in P23-05; the residue gate that asserts
    emitted-and-connected runs in P23-09, at batch end, so no mid-batch state is left
    dormant.)*
  - `[new] services/option_ladder.py` — geometry (`SPREAD_WIDTH`, `STRIKE_STEP`, rung
    offsets, `ladder_pairs`), naming (`format_instrument`), **the sign pair** —
    `display_bases(bid_s, ask_s, bid_l, ask_l) -> (display_ask, display_bid)` (A202:
    `long.ask − short.bid`, `long.bid − short.ask`) and `credit_bases(...) ->
    (credit_bid, credit_ask, credit_mid)` (`−display_ask`, `−display_bid`, their mean) — the
    three-basis metric (`distance`), **`option_tick(target)` + `match_band(target)`** (A204),
    **`usable_quote(bid, ask, received_bid, received_ask)`** (AC-D65.16), `net_greeks`,
    `snap_rung`, `window_legs(anchor)`, and the cell formatters (ASK/BID 2 dp, Delta 3 dp,
    Gamma 4 significant digits). **No polarity is computed at a call site** — the two helpers
    are the only place a sign is decided, which is what makes the ASK↔`credit_bid` label swap
    testable.
  - `[new/changed] ui/main_window.py` — **the dock block, the rename, and every dereference of the
    renamed attribute (RC-16's merge — this wave owns both halves)**: `OptionSpreadsPanel`; dock
    title **and** `objectName` `Option Spreads`; title-bar widget = the panel's `header_button`;
    `setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)` unchanged; the window attribute renamed
    `portfolio_panel` → `option_spreads_panel` (the old name is a displaced token — S-P23-15);
    **the three collapse-probe re-points, docstrings included** — `_compute_right_dock_collapsed_min_width`
    (`:3583-3597`) re-points its code to `option_spreads_panel.header_button` **and its docstring**
    (`:3585-3587`, today *"The collapsed region is a vertical strip holding the Portfolio
    (Account Summary) header button"*) to the `Option Spreads` header button: it is the **last
    full-word `Account Summary` spelling in `ui/`**, and P23-08's token list reads docstrings, so
    leaving it would redden that wave on text it does not own (RC-15); the same treatment applies
    to the block's own `Portfolio`/`Portfolio panel` comments at `:630-634`, re-pointed with the
    code they describe; the `toggled` connection;
    **and the ten `ActivePortfolioPanel` API calls are deleted in this same wave** — not renamed,
    because the new panel has **none** of those methods (`set_account_summary`, `set_account_id`,
    `set_account_unavailable`, `set_positions`, `add_position`) and the old attribute no longer
    exists, so a dereference left behind is an `AttributeError` on the first window that reaches
    it. Exactly the eight locations RC-16 names, and what stays with which wave:

    | Site | Today | Here | Stays (owner) |
    |---|---|---|---|
    | `:849`,`:850`,`:852` in `__init__` (the `:848-855` block) | `set_account_summary({})`, `set_positions([])`, `set_account_unavailable(True)` | deleted with the block and its `D27.6`/`D45` comments | — the block's only subject is the deleted panel; the four `b.*` connects (`:842-846`) are **P23-06**'s |
    | `:1731` (`_subscribe_account_data`'s tail) | `set_account_unavailable(False)` | deleted | the subscription body (`reqPositions`/`reqAccountSummary`, `_account_subscribed = True`) — **P23-06** |
    | `:2072` (`_on_disconnected`) | `set_account_unavailable(True)` | deleted | the account state clears (`:2066-2071`) — **P23-06** |
    | `:4349`,`:4350` (`_on_account_summary`) | `set_account_id(account or None)`, `set_account_summary(summary)` | deleted | the handler's collection and its `_update_conn_badge()` call — **P23-06** |
    | `:4357` (`_on_account_summary_end`) | `set_account_summary(dict(summary))` | deleted | the status line and the ESC-052 prune guard — **P23-06** |
    | `:4468` (`_on_position_update`) | `add_position(position)` | deleted | the position build and `_upsert_position` — **P23-06** |
    | `:4538` (`_on_position_end`) | `set_positions(positions)` | deleted | the bulk read, and the `positions` local it strands — **P23-06** |

    **No handler is deleted here** — none of the four is panel-only, so each keeps its
    account-path body for P23-06 and loses only its panel call. **`_on_position_end`'s
    `positions = [...]` (`:4530-4537`) is deliberately left unread** until P23-06 deletes the bulk
    read whole: removing it here would strand `rows` one level up and would take that wave's
    subject; it is a local name, not a forbidden token, and no exit reads it.
    **The launch width per S-P23-16**: `self._right_launch_width = OptionSpreadsPanel.PREFERRED_WIDTH` at
    construction (a *remembered launch request*, in-memory only, no new key — the
    `_persisted_watchlist_width` analogue, D17.4) and `_deferred_dock_setup` passing
    `requested_right=self._right_launch_width` alongside the persisted watchlist request, so
    the first real-chart-area apply clamps 360 through `plan_dock_widths` to
    `clamp(360, 200, right_dock_max_width(ca))` and leaves `_right_dock_width` holding the
    clamped plan value (every later apply keeps tracking the live dock width);
    the panel's two signals are connected in P23-05, so this wave wires only the header
    collapse state.
  - **Unchanged:** `ui/dock_layout.py` (its minimum, cap, cross-clamp and
    `plan_dock_widths` are the frozen contract; **no new constant is added there** — the
    preferred width belongs to the panel, per `AC-D65.9`(i)).
  - **Deleted:** `ui/active_portfolio_panel.py` (whole file) and
    `tests/test_d41_portfolio_dock.py` (its subject).
  - **Test book — every file's real edit, nothing is "title only":**
    - `tests/test_right_dock_d21.py` — imports/references `OptionSpreadsPanel`; dock
      title/`objectName` `Option Spreads`; `win.portfolio_panel` →
      `win.option_spreads_panel`; `summary_label` → `header_button` with the text
      `Option Spreads`; the collapse/expand, `body.isVisible()` and
      `minimumWidth() == RIGHT_DOCK_MIN_WIDTH` assertions follow the renamed members
      (behaviour unchanged). **Its module docstring is part of the edit** — `:7`'s
      *"the retained ``summary_label`` — a ``DiagonalStrikeButton("Account Summary")``"* names
      the retired spelling, so it is re-worded with the code (RC-15), the in-body comments at
      `:60-66` follow, and `:75`'s `pf_btn.text() == "Account Summary"` becomes
      `header_button.text() == "Option Spreads"`. The file is the RENAME's own doc, so leaving a
      stale sentence there would contradict both its subject and P23-08's token list.
    - `tests/test_dock_d18_region.py` — re-pointed in all four of its groups, its module
      import removed, and its docstring (`:1-16`) rewritten; this is the rename's most
      load-bearing single file:
      1. **`:32` `from ui.active_portfolio_panel import ActivePortfolioPanel` is deleted** —
         left in place it is a **collection error** for the whole file once the module goes,
         so "no `ActivePortfolioPanel` in `tests/`" cannot hold without it.
      2. **`test_T48_T01` (`:77-101`, "the panel fills the region")** — `win.portfolio_panel`
         → `win.option_spreads_panel` at `:84` and `:91`; the three width relations
         (`:97-99`) are unchanged assertions on renamed members.
      3. **`test_T48_T02` (`:106-149`)** — `findChild(QDockWidget, "Portfolio")` →
         `"Option Spreads"` (`:110`), `objectName() == "Portfolio"` → `"Option Spreads"`
         (`:113`); the title-keyed probe at `:118-121` (AR-D41-3's "the lookup the
         dock-hiding helpers use still resolves the real region — a stale key would leave
         them hiding nothing") becomes **`objectName()`-keyed** and **keeps that job**: it is
         the sentinel for the twenty lookups edited in this wave; `header =
         win.portfolio_panel.summary_label` → `header_button` (`:126`), and the collapse
         assertions at `:129-138` follow `is_collapsed`/`body` (behaviour unchanged).
         **The collapsed-width floor is `:133`** —
         `assert region.width() <= win._right_dock_collapsed_min_width + 2` — inside this
         test; it is **not** `:150-172` (the previous entry's anchor was wrong), it reads no
         launch width, and its value is unchanged.
      4. **`test_T48_T03` (`:154-181`) — the group the previous entry omitted.** `:158`
         `isinstance(win.portfolio_panel, ActivePortfolioPanel)` →
         `isinstance(win.option_spreads_panel, OptionSpreadsPanel)`; `:161-163` (the panel
         **is** the dock's widget) is the group's real surviving assertion and is kept
         as written; `:165-179` — the `hasattr(..., "account_summary_changed")` and
         `hasattr(..., "positions_changed")` probes and the zero-receiver sanity check —
         **are deleted with the signals they name** (neither exists on the new panel), and
         **`_receiver_count` (`:184-194`) goes with them**: `:177` is its only call site, so
         leaving it would be an unused helper that P23-09's gate clause (ii) reddens.
      What the file asserts after this wave: the dock resolves by its new `objectName` and
      that lookup is the one the helper suites use; the panel fills the region within 1 px;
      the header toggle collapses to the strip and restores; exactly one right-area dock; the
      dock's widget *is* the panel. Nothing in the module then names `Portfolio`,
      `ActivePortfolioPanel`, `portfolio_panel` or `positions_table`.
    - `tests/test_dock_widths_d18.py` — dock title/`objectName` (:180-182), the
      panel-fills case (:291-296), **the "wide content" AC-D18.6 case (:370-380) rebuilt on
      the new panel's tables** (`positions_table` no longer exists), the docstring prose,
      and **the re-baselines at :437-438** (see *D18 re-baseline* below).
    - `tests/test_dock_widths_d18_impl.py` — the wide-content case (:265-270) rebuilt on the
      new panel's table and **the re-baselines at :328-329** (see below).
    - `tests/test_watchlist_nonregression_d22.py` — the D21.13 header/collapse probe
      (:147-180) renamed to the new panel (`header_button`, `is_collapsed`, `body`), **and its
      text assertion `:161` (`btn.text() == "Account Summary"`) re-pointed to
      `"Option Spreads"`** — the panel's header string is the token's last `tests/` carrier
      outside the instrument's own token tables.
      *(Not touched: `tests/test_dock_widths_collapsed_d44.py` — it exercises the **left**
      watchlist dock only, and its strip/restore assertions are unaffected by the right
      dock's launch width.)*
    - `tests/test_d41_removal.py` — `win.portfolio_panel` → `win.option_spreads_panel` and
      the dock title (:315-316).
    - `tests/test_p13_gate.py::test_no_new_dependency` (:199-217) — **the `ui/*.py`
      allowlist gains `option_spreads_panel.py` and loses `active_portfolio_panel.py`**;
      that is the file's whole change (no behavioural assertion moves).
    - `tests/test_d45_removal.py` — **three changes in this wave, all in the walkthrough's
      group** (the file's prose is re-pointed with the code, since `tests/` is covered by
      neither static instrument):
      1. **Delete `test_removed_panel_members_absent` (:710) and the
         `_REMOVED_PANEL_MEMBERS` tuple with its only subject** — it imports the module this
         wave deletes.
      2. **Rework the `walkthrough` fixture (:522) onto the new panel** instead of leaving a
         dead Portfolio probe: `_snapshot` (:501) reads `win.option_spreads_panel`'s
         `ccs_table`/`pcs_table` (row counts, the five-column header tuple, `is_collapsed`)
         for its per-step record instead of `positions_table`; the three `positions_table`
         lines (:610-613) become `win.option_spreads_panel.toggle_collapsed()` twice (the
         collapse handle is the one affordance this file drove that survives — the new
         panel's `refresh()`/`selectRow()` do not exist, `apply_snapshot` is the replacement);
         **both `bridge.position_update` emits (:605-608, :617-620), the `record["positions"]`
         dict (:607, :619) and the `:650-664` Portfolio-render assertions are removed** — the
         renderer they asserted dies in this wave, and its replacement is asserted in
         `tests/test_d65_option_panel.py` (same wave) and, once live, in P23-05's stream
         suite. `test_zero_transmit_walkthrough` keeps its zero-transmit/cancel assertion,
         its per-step constructibility assertion (re-pointed to the new panel's four-row,
         five-column shape) and its unhandled-`AttributeError`/`TypeError` assertion, and
         loses only the Portfolio half.
      3. **Delete `test_positions_table_is_eight_columns` (:669)** — its subject (the
         eight-column `positions_table`, its `Strategy`/`Group` headers included) dies here;
         the shell's own header tuple and row counts are asserted in
         `tests/test_d65_option_panel.py` in this same wave, so no criterion loses its
         measure.
      `_stub_account_calls` (:492) **stays** in this wave — its subject
      (`_subscribe_account_data`'s `reqPositions`/`reqAccountSummary` calls) is P23-06's, and
      it is removed there with its call site. *(Wave 1 of four: `_stub_account_calls` →
      P23-06, block (d) → P23-07, block (g) → P23-08.)* The P5 precedent (`AP-D46-6`, §
      *Phase P5*) split this same file across waves for exactly this reason: a test that
      references a name a wave deletes must move with it.
    - **The six D27 account/position suites are deleted in this wave, not in P23-06** —
      `tests/test_d27_account_subs.py`, `tests/test_d27_account_scoping.py`,
      `tests/test_d27_account_partial_window.py`, `tests/test_d27_flat_rows.py`,
      `tests/test_d27_position_id.py`, `tests/test_d27_position_prices.py`. Each one reads
      `win.portfolio_panel` (its `positions_table`, `account_detail` or `_positions`) or
      imports `ActivePortfolioPanel`, so **their subject is the panel this wave deletes**, not
      the window path P23-06 removes: `test_d27_flat_rows.py:17` imports the module directly
      and the rest assert rendered rows (e.g. `test_d27_account_subs.py:101-102`,
      `test_d27_position_id.py:129-134`). Leaving them for P23-06 would leave this wave's
      exit condition ("no `portfolio_panel` reference left in `tests/`") false for four waves
      by construction. The account-path *behaviour* they also touched survives in its
      **subscription/state/bookkeeping half only** — `_account_subscribed`, the reqId
      bookkeeping, the four connects, the bulk read — which nothing in P23-02…P23-05 changes and
      whose removal gate is P23-06's residue grep, so no live behaviour goes unguarded in
      between. Its **panel half does not survive**: those calls address `ActivePortfolioPanel`'s
      API, which the new panel does not have, and the panel they render into is gone in this
      wave, so the ten call sites are deleted here (RC-16). Recorded as
      subject-follows-test on the P5 precedent (`AP-D46-6`).
    - **The dock-lookup surface — twenty surviving modules, all edited in this wave (RC-11).**
      `S-P23-1` renames the dock's title **and** `objectName`; `A198`'s DELETE list already
      covers "the dock title `Portfolio` **plus every title-keyed lookup resolving it**", so
      this surface is part of the panel member group, not a follow-up. Every module below
      locates the right dock by the retired identity today and is re-pointed here, by line,
      to **`dock.objectName() in ("Option Spreads",)`**:

      | # | File | Site | Today | Bites at P23-01 as |
      |---|---|---|---|---|
      | 1 | `tests/test_history_backfill.py` | `:223-225` | `windowTitle() in ("Portfolio",)` hide loop | silent no-op |
      | 2 | `tests/test_history_backfill_disconnect.py` | `:136-138` | same | silent no-op |
      | 3 | `tests/test_d27_phantom_alarms.py` | `:55-57` | same | silent no-op |
      | 4 | `tests/test_d27_reconnect.py` | `:170-172` | same | silent no-op |
      | 5 | `tests/test_d27_stream_health.py` | `:66-68` | same | silent no-op |
      | 6 | `tests/test_p7_w1_persist.py` | `:197-199` | same | silent no-op |
      | 7 | `tests/test_p7_w2_prime.py` | `:44-46` | same | silent no-op |
      | 8 | `tests/test_p7_w2_watchdog.py` | `:42-44` | same | silent no-op |
      | 9 | `tests/test_p14_indicator.py` | `:139-141` | same | silent no-op |
      | 10 | `tests/test_p14_cache_guard.py` | `:182-184` | same | silent no-op |
      | 11 | `tests/test_p14_lifecycle.py` | `:140-142` | same | silent no-op |
      | 12 | `tests/test_p15_surfacing.py` | `:166-168` | same | silent no-op |
      | 13 | `tests/test_p15_expiry.py` | `:149-151` | same | silent no-op |
      | 14 | `tests/test_p15_continue.py` | `:150-152` | same | silent no-op |
      | 15 | `tests/test_p20_resolution_probe.py` | `:90-92` | same | silent no-op |
      | 16 | `tests/test_history_backfill_loadpath.py` | `:174-177` | list + `assert right_docks` | **hard fail** |
      | 17 | `tests/test_d42_depth_floor.py` | `:186-189` | list + `assert right_docks` | **hard fail** |
      | 18 | `tests/test_d10_d13_integration.py` | `:42` const, `:60` predicate | `_RIGHT_DOCKS = ("Portfolio",)` | silent no-op |
      | 19 | `tests/test_watchlist_columns_d21.py` | `:309` const, `:323` predicate | `_RIGHT_DOCK_TITLES = ("Portfolio",)` → `_RIGHT_DOCK_NAMES` | silent no-op |
      | 20 | `tests/test_dock_widths_d17.py` | `:40` const, `:77` predicate, `:83` assert | `_RIGHT_DOCKS = ("Portfolio",)` + `assert hidden == 1` | **hard fail** |

      Rows 1–15 are one identical three-line loop each, so the edit is the **predicate
      only** (`dock.objectName() in ("Option Spreads",)`); every one of those fifteen files
      imports `QDockWidget` for that loop alone, so rewriting the loop instead of the
      predicate would leave an unused import each. Rows 16–17 keep their `assert` (reworded
      to name `Option Spreads`) — they are the D19-trap sentinels
      (`tests/test_dock_d18_region.py:115-121`), and row 20 is a third one by accident: it
      counts what it hid and fails if the count is not 1. Rows 18–20 also re-point the
      predicate that consumes the constant and the comment above it; row 19 renames the
      constant because "titles" would then be false. **Three of the twenty hard-fail, not
      two** — `test_history_backfill_loadpath.py:177`, `test_d42_depth_floor.py:189` and
      `test_dock_widths_d17.py:83` — and the other seventeen are silent: the dock they no
      longer hide now launches at 360 px, so a width-sensitive suite measures a wider window
      than it intends rather than erroring. That is exactly the failure the three sentinel
      assertions exist to convert into a loud one, which is why every one of the twenty is
      scheduled here and none is left "for the suite to notice".
      **Why `objectName` and not the new title:** once `setTitleBarWidget(header_button)`
      replaces the dock's title bar the title string is not rendered at all — it is chrome —
      while `objectName` is the identity `findChild(QDockWidget, …)` already resolves the
      dock by in `test_dock_d18_region.py:110` and
      `test_watchlist_nonregression_d22.py:151`. Re-keying to the new title string would
      re-create the coupling that made this rename break twenty files, and the next header
      rewording would desync them a third time. **Why one wave and not its own wave:** the
      rename and the lookups cannot be separated — a wave *after* the rename leaves the
      rename's own wave red, and a wave *before* it would have to key on an identity that
      does not exist yet (a two-title tuple, which leaves `Portfolio` in the tree and
      contradicts this wave's exit). **Sizing:** still M (`AP-P23-8`) — twenty one-line
      predicate edits plus three constant-and-comment edits in the **same member group** the
      dock swap already owns; no new assertion is introduced and no numeric expectation
      moves.
  - **D18 re-baseline (A201, owner-authorised — not drift).** Exactly two sites, each
    changing **only its expected constant**: `tests/test_dock_widths_d18.py:437-438`
    (`test_T50_T06_restart_returns_default_not_persisted`) and
    `tests/test_dock_widths_d18_impl.py:328-329` (`test_T49_T06_right_region_not_persisted`).
    Both compare the tracked value and the rendered width against a module constant; both
    take `expected = max(RIGHT_DOCK_MIN_WIDTH, min(OptionSpreadsPanel.PREFERRED_WIDTH,
    right_dock_max_width(win2._chart_area_width())))`. Their "default restored, not
    persisted" semantics are unchanged, the "no right-region QSettings key" loop above them
    is untouched, and **no third assertion in either file changes**. Every other
    `RIGHT_DOCK_MIN_WIDTH` assertion in the D18/D21/D44 suites is a *below-minimum drag*
    case (`_apply_dock_widths(None, 0)`) or a collapsed-strip case, so it still holds at the
    new launch width and is not touched.
  - **New tests:** `tests/test_d65_option_panel.py` — shell assertions (title, sub-headers,
    header tuple, row counts, Target default; **the S-P23-23 gate: accepted edges `0.05` and
    `19.95`, and one case each for blank / `0` / negative / non-numeric / `NaN` / `Inf` /
    `20.00` asserting the message, the restored field value and that `target_committed` was
    **not** emitted**; toggle x-position > Target's right edge, colour property + stylesheet
    per state, empty state, elide + tooltip at narrow widths) **plus the `AC-D65.9` group**:
    the exact tracked assertion
    (`win._right_dock_width == max(200, min(360, right_dock_max_width(ca)))`) at launch
    **and** in a freshly rebuilt window (the "restart returns the launch width, never the
    last dragged width" case), a tolerant rendered assertion at the
    1600×900 fixture (dock width ≥ 340 px and no name's text width exceeds its column
    width), a **900×700** narrow case where the cap wins outright — chart area ≈680 px, so
    `right_dock_max_width` = `min(int(0.40 × 680), 680 − 400)` = **272 px**, 88 px below the
    360 px preferred width, leaving the elastic name column ≈84 px against the ≈140 px
    longest instrument name — so the elide + tooltip path is taken on real margin rather than
    by 8 px, and `preferred_width() == 360`; plus
    `tests/test_d65_option_ladder.py` (all eight strike pairs per side, width exactly 20, the
    offset table, name strings **and short/long ordering per side**, the **fixture-convention
    guard** — canonical `7425/7445` CCS and `7340/7320` PCS, and a rejection case for any
    10-wide pair and any PCS pair whose long strike is above its short — **the sign table**
    (a credit pair renders negative; `display_bases` and `credit_bases` are exact negatives of
    each other and the ASK cell reads `long.ask − short.bid`), **the band table**
    (`option_tick(1.00) = 0.05`, `option_tick(2.95) = 0.05`, `option_tick(3.00) = 0.10`,
    `match_band` = `max(0.05, …)` at each), **the validity table** (`0` bid live; `-1`,
    `1.7976931348623157e+308`, `NaN`, unreceived side, `bid > ask` each ⇒ absent),
    three-basis arithmetic, snapping, `window_legs(anchor_short)` per anchor).
  - **Window-constructibility between this wave and P23-06 (RC-16's second half).** Because the
    rename and all ten of its dereferences land here, the suites that build and drive a real
    `MainWindow` must still pass in this wave, and they are the proof that no dereference
    survived: `tests/test_d65_option_panel.py` (construct + rebuild — the first test to build a
    window after the swap), `tests/test_d45_removal.py`'s `walkthrough` and
    `test_zero_transmit_walkthrough` (connect path → `_subscribe_account_data`),
    **`tests/test_d27_reconnect.py:183-215`** (`_on_connected` → `_on_disconnected` →
    `_on_connected`, the only surviving suite that executes both `:1731` and `:2072`),
    `tests/test_d41_removal.py:355` and `tests/test_d40_tws_lifecycle.py:437`, and the sixty-odd
    other surviving modules whose fixtures construct a window. The four handlers' deleted calls
    are driven by no surviving test in this wave (the four suites that did are deleted here), so
    they are unreachable until P23-06 — no suite is left to discover them.
- **Dependencies:** none (first wave).
- **Touches:** `ui/option_spreads_panel.py` (new), `services/option_ladder.py` (new),
  `ui/main_window.py` (the dock block, the rename, **the ten `ActivePortfolioPanel` call-site
  deletions**, the launch-width line and `_deferred_dock_setup`'s one added argument),
  `ui/active_portfolio_panel.py` (delete) + the eight book test files, the **twenty lookup
  modules** in the table above, and the six D27 suites (delete).
  Serialisation: `ui/main_window.py` against P23-05/P23-06 (distinct blocks — this wave's are the
  dock block, the three probes and the ten call sites; P23-06 never names `option_spreads_panel`).
- **Exit condition:** the shell, ladder-math and `AC-D65.9` groups are green; the two D18
  re-baselines pass and a diff of the two suites shows **only** the four lines of those two
  assertions; **the retired dock identity is gone from `tests/` as code** — all of these
  return nothing over `tests/ --include='*.py'`: the keyed-lookup forms
  `windowTitle() in ("Portfolio"`, `windowTitle() == "Portfolio"`,
  `findChild(QDockWidget, "Portfolio")`, `objectName() == "Portfolio"` and `("Portfolio",)`;
  and the symbols `portfolio_panel`, `positions_table`, `ActivePortfolioPanel`; **and
  `portfolio_panel` is gone from `ui/` as well** — all **eighteen** spellings are this wave's (the
  module import at `:76`, the dock block `:638,641,642,662`, the three probes `:3591,3606,3638`,
  and the ten deleted calls at `:849,850,852,1731,2072,4349,4350,4357,4468,4538`), so the grep is
  true when the wave ends rather than five waves later, and the five `ActivePortfolioPanel` methods
  (`set_account_summary`, `set_account_id`, `set_account_unavailable`, `set_positions`,
  `add_position`) are spelled by no line of `ui/main_window.py`; **and `Account
  Summary` is gone from `ui/`** (the panel's header string and `:3586`'s docstring — the token
  P23-08 will add), so the later wave inherits a clean tree instead of an exception — with **one
  documented carve-out**: the **forbidden-token tables** (`tests/test_d45_removal.py`'s
  `_FORBIDDEN`/`_SURVIVORS`, and from P23-09 `tests/test_d65_residue.py`'s displaced-token
  list) are the only place those spellings may survive, because a token that is forbidden has
  to be spelled to be forbidden. They are literal-string tables — never an import, an
  attribute access or an assertion subject — so the carve-out cannot hide a live use; without
  it, P23-08's own token additions would make P23-09's re-run of this exit false. The twenty
  lookups, the eight book files and the seven deletions **together cover every file that holds
  the old identity today** (verified by grep; `test_dock_d18_region.py` and the two D18 suites
  are in both the book and the coverage set); the twenty lookups
  carry `objectName() in ("Option Spreads",)` (rows 18–20 carry the constant and its
  consumer) and the three sentinels still assert their lookup resolved;
  `tests/test_dock_d18_region.py` is green with `T48-T03` re-pointed, its `:32` import gone
  and `_receiver_count` gone with it; the reworked walkthrough is green — a real window driven
  through every surviving affordance, recording every step with zero transmit/cancel and no
  unhandled slot exception; `tests/test_p13_gate.py` is green with the repaired allowlist;
  `import ui.main_window` is clean. **The window still works after the rename — asserted, not
  assumed:** the connection half is proved by the suites that build a real `MainWindow` and walk
  it, `tests/test_d65_option_panel.py` (construct + rebuild, the launch-width group),
  `tests/test_d41_removal.py:355` and `tests/test_d40_tws_lifecycle.py:437` (`_on_connected` /
  `_on_disconnected`), and — the only one that walks both — `tests/test_d27_reconnect.py:183-215`
  (`_on_connected` → `_on_disconnected` → `_on_connected`, i.e. `_subscribe_account_data`'s tail
  and `_on_disconnected`'s clear both executed), plus the sixty-odd surviving modules that
  construct a window in their fixtures; the four handlers' deleted calls are reached by no
  surviving test (the four suites that drove them are deleted here), so nothing can trip them
  between this wave and P23-06. **No expectation outside the two A201 re-baseline sites
  moves** — if any of the twenty suites needs a numeric change to go green, that is a
  stop-and-escalate, not an in-wave re-baseline (owner authorisation covers exactly those two
  sites).

### P23-02 — Chain discovery, option contracts and the greek/quote boundary — size M

- **Goal:** the app can resolve SPX's 0DTE SPXW series, build per-leg contracts, and receive
  streamed quotes and greeks for a leg, with none of it reachable from the panel yet.
- **Covers:** `AC-D65.2`'s expiry/strike half (`SPX` regardless of the charted symbol;
  today's expiry only; listed strikes) + Q106(a)/Q107(b)/A186; `AC-D65.5`'s intake half
  (quotes + greeks per leg, no polling); `AC-D65.8`'s chain-level empty state and the
  sentinel/rejection inputs; R141/R149; DG123.
- **Deliverables:**
  - `[new/changed] ibkr/contracts.py` — `get_option_contract`, `today_expiry_yyyymmdd`,
    `select_zero_dte_series`, `option_chain_strikes`, `OptionSeries`. The S-P20-1 rule
    order and every existing function untouched.
  - `[new/changed] ibkr/market_data.py` — `req_sec_def_opt_params` (readiness check,
    `id_manager.get_id`, `pacing_manager.throttle`, never sleeps).
  - `[new/changed] ibkr/client.py` — `tickOptionComputation`,
    `securityDefinitionOptionParameter`, `securityDefinitionOptionParameterEnd` overrides
    emitting the three new bridge signals with only the fields used. **No deletion in this
    wave** (the account overrides die in P23-07).
  - `[new/changed] ibkr/bridge.py` — `option_params`, `option_params_end`,
    `option_computation`.
  - **New tests:** `tests/test_d65_option_chain.py` — option-contract attribute shape per
    right/multiplier/tradingClass; `today_expiry_yyyymmdd` across ET dates;
    `select_zero_dte_series` (SPXW with today; a later expiry present but ignored; no 0DTE →
    empty-state signal); strike-list extraction; `req_sec_def_opt_params` request shape +
    `PacingExceeded`/`IBKRNotReady` behaviour; and override→bridge routing with a fake client —
    `tickOptionComputation` **tick type passthrough** (`13` model, `12` last, `10`/`11`
    bid/ask — the values S-P23-8 resolves on) plus `None`/`-1`/`1.7976931348623157e+308`/NaN
    delta/gamma passthrough **unmodified** (screening is the engine's, never the bridge's), and
    `tickPrice` bid/ask sentinels reaching the engine untouched.
- **Dependencies:** P23-01 (the ladder module's `LegKey`/`SpreadRow` shapes are its
  consumer).
- **Touches:** `ibkr/contracts.py`, `ibkr/market_data.py`, `ibkr/client.py`,
  `ibkr/bridge.py` + the new suite. Serialisation: `ibkr/client.py`/`ibkr/bridge.py` (P23-07
  edits the same files for deletions).
- **Exit condition:** the chain suite is green and no production code outside `ibkr/` calls
  the new helpers yet (they are called by P23-03/04/05 and by tests — the residue gate's
  caller census for this wave names those); the four account overrides are still present
  (they are P23-07's).

### P23-03 — Spread engine A: seeding by measurement, quote validity, band and anchor selection — size M

- **Goal:** a pure engine that, fed a chain and leg data, **finds** the anchor by measurement —
  session anchor, else a bounded coarse probe, then a 5-point refine — scoring only pairs whose
  legs actually quote, and emitting lease/subscribe/cancel/row/message actions. Testable with no
  Qt, no window and no network.
- **Covers:** `AC-D65.3` (the credit-basis metric and all three tie-breaks, **selected through
  the seed ladder**), **`AC-D65.15` in full** except the spot *line* (tier order, ≤6 probes per
  side at 20-point spacing, lease-then-release, 3 s pending ⇒ match-ineligible, **10 s / 12
  scored pairs** bound with one message and retry-at-next-cadence), `AC-D65.16` (a pair is never
  scored or matched on one side; zero bid live; sentinels absent), `AC-D65.4`'s band arithmetic
  (`h` gates both match and move), `AC-D65.6`'s planning half (**lease accounting against the 16
  option slots**), A206/A207/A208, R150/R151; DG117/DG123.
- **Deliverables:**
  - `[new] services/option_spread_engine.py` (first half) — the state machine per S-P23-3,
    S-P23-5, S-P23-18, S-P23-19: `toggle_on`/`toggle_off`, `set_target`, `on_chain`,
    `on_no_expiry`, `on_quote(leg, bid, ask, received_bid, received_ask)`, `on_spot(price)`,
    `begin_seed(now)`, `seed_actions()`, `seed_state()`, `evaluate(now)`, `live_legs()`, plus
    the internal lease pool (`lease(pair)` refuses when the live window occupies the capacity,
    `release(pair)` on score) and the pending-leg timestamps. **Every action is one of
    `lease`/`subscribe`/`cancel`/`release`** so the line accounting is assertable on the emitted
    order; the deterministic issue order (CCS 3, 2, 4, 1 then PCS 3, 2, 4, 1) lives here.
- **New tests:** `tests/test_d65_spread_engine.py` (part 1) — pure pytest: **the seed ladder**
  (warm session anchor ⇒ no probe lease at all; cold ⇒ ≤6 probes per side at 20-point spacing,
  each leased and released, and the **same final rung** as the warm path against the fixture
  chain; a probe refused for capacity ⇒ the refine tier still finishes; the spot-absent and
  spot-refused branches), **the bounds** (a 12-pair fixture stops at pair 12 with one message
  and a stable rung; a wall-clock fixture asserting the 10 s deadline stops the sweep — asserted
  against an injected clock, never `sleep`), **the 3 s pending rule** (a leg with no tick is
  pending, its pair is not scored, and it becomes eligible only when both legs quote),
  **validity** (zero-bid pair scores; one-sided pair never scores; a sentinel cannot enter `d`;
  **a good value turning sentinel flips the cell to `—` and the pair stops being eligible on the
  next evaluation**),
  **the metric** (only mid / only credit_ask / only credit_bid touching `T`; one case per
  tie-break; a `T = 3.00` case asserting `h = 0.10` and a `T = 1.00`/`2.95` case asserting
  `h = 0.05`), **lease accounting** (the live option count never exceeds 16 at any emitted
  step and dips to 14 mid-step; no action ever leases a leg the live window holds), and the
  per-cause latch counts that belong to selection (no-0DTE, chain edge, rung shortfall, budget
  refusal, seed bound).
- **Dependencies:** P23-02 (`OptionSeries`, `LegKey`) and P23-01 (`option_ladder`:
  `credit_bases`, `distance`, `option_tick`, `match_band`, `usable_quote`, `snap_rung`,
  `window_legs`).
- **Touches:** `services/option_spread_engine.py` (new) + its suite. No production file outside
  `services/`.
- **Exit condition:** this suite is green; the seed/lease cases are red-first against the
  pre-P23 tree (the module does not exist) and green after; no module in the suite imports
  PyQt6 or `ibapi` (asserted); the wall-clock bound is asserted without a real sleep.

### P23-04 — Spread engine B: window-step maintenance, connection lifecycle and per-line error classes — size S

- **Goal:** the same pure engine maintains both ladders by `reqId`-preserving window steps,
  survives a disconnect/reconnect without inventing values, and gives each TWS line-error class
  its own state — all still with no Qt, no window and no network.
- **Covers:** `AC-D65.4`'s step rules (one 5-point step on both legs, decided direction, stop
  rules, stationary feed, the two-rung oscillation case), `AC-D65.6`'s shared-leg rule on a
  re-anchor, **`AC-D65.14`**'s engine half (`STALE` on disconnect with `walk_frozen`, resume from
  the same anchor on reconnect, re-seat one step only for a 200 on the anchor pair, no re-seat
  for 10197/354/other, 162 transient ⇒ `STALE` after the timeout), `AC-D65.5`'s greek
  **source precedence and the never-mixed rule**, `AC-D65.8`'s latches for the lifecycle causes,
  Journey 62 step 6 edges and Journey 63 steps 1–5; A193/A203; R139/R148.
- **Deliverables:**
  - `[new/changed] services/option_spread_engine.py` (second half) — `evaluate()` decides and
    installs the step itself: `_step_candidate(side, live)` returns the one 5-point rung
    `AC-D65.4` allows (direction from the anchor pair's three credit bases, the rung's `d` must
    beat the anchor's by more than `h`, otherwise no move; an unlisted rung latches the
    chain-edge message), and `_install_windows(acts, targets)` emits the `Actions` diff
    (`cancels` before `subscribes`, never both halves of a shared leg),
    `on_greek(leg, tick_type, delta, gamma)` with the per-row source agreement check,
    `on_leg_error(leg, code)` with the four-class table, `on_disconnected()`,
    `on_reconnected()`, `rebind_leg(leg, new_req_id)`, and the `walk_frozen` gate inside
    `evaluate()`.
- **New tests:** `tests/test_d65_spread_engine.py` (part 2) — the ordered step sequences per
  side with the decided strike direction; the matched-on-the-ask-only case that must not move;
  equal-`d` tie-break then stay; the chain-edge message; zero moves on a stationary feed; the
  two-rung oscillation case that must not occur; **the shared-leg case** (a leg in both the
  pre-change and the final window produces **no** cancel and **no** subscribe); **the lifecycle
  group** (disconnect ⇒ every cell `STALE`, `evaluate()` emits nothing while frozen, nothing is
  cancelled; reconnect ⇒ resume from the same anchor and no re-seed while the legs recover;
  a leg still silent past 3 s after reconnect ⇒ one re-seed); **the error-class group** (200 on
  a non-anchor pair ⇒ that pair dropped and `n/a`, **no** re-seat; 200 on the anchor ⇒ exactly
  one toward-the-money re-seat then a stop message; 10197 and 354 ⇒ `—`, no re-seat; 162 ⇒ line
  kept and values `STALE`, no cancel; an unclassified code ⇒ `—` and no re-seat; one message per
  class); **the greek group** (model-only, last-only, bid/ask-mean, and a mixed-source pair ⇒
  `—` + one message).
- **Dependencies:** P23-03 (same module; this is the second half of its surface).
- **Touches:** `services/option_spread_engine.py`, `tests/test_d65_spread_engine.py`. No
  production file outside `services/`.
- **Exit condition:** the engine suite is wholly green; the shared-leg, freeze and error-class
  cases are red-first and green after; no PyQt6/`ibapi` import in the suite; the re-seat case
  proves 10197/354/other **never** re-seat.

### P23-05 — Live wiring: ON/OFF lifecycle, registry replay, the spot line, line budget, coalescing, fault surfacing — size M

- **Goal:** with a fake client on the real `MainWindow`, switching the panel ON populates both
  ladders from streamed values inside the **16 + 1** line budget, moves the ladder when the
  Target drifts, **freezes and marks `STALE` on a disconnect and resumes by replay**, and every
  fault produces exactly one message — and OFF releases every line.
- **Covers:** `AC-D65.1`'s toggle behaviour in a live window; `AC-D65.5` render half (displayed
  values, never mixed greeks); `AC-D65.6` issuance/cancel/guard-refusal **and the shared-leg
  rule asserted on real reqIds**; `AC-D65.7` (ON→move→OFF→ON, zero orders); **`AC-D65.14`**'s
  wiring half (registry registration with `reissue`/`rebind`, the one tag in
  `_replay_subscriptions`, disconnect ⇒ `STALE` + frozen walk, reconnect ⇒ replay, per-line
  error routing); **`AC-D65.15`**'s spot half — tier **3a** (the chart's own price when the
  charted symbol is SPX, so **no** line), tier **3b** (otherwise the **single** SPX line, its
  routing, its cancel when the seed completes), tier **3c** (the refused/never-quoting branch),
  **17 = 16 + 1**; `AC-D65.8` in-window (injected faults, reconnect while
  ON, empty state, **post-16:15 cutoff**); **`AC-D65.17`**'s in-window half (a rejected Target
  changes no anchor and no line); `AC-D65.10`; `AC-D65.9`'s collapse-while-ON edge; Journey 62
  steps 3–7, Journey 63 steps 4–7; R138/R139/R140/R144/R150/R151.
- **Deliverables:**
  - `[new/changed] ui/main_window.py` — the option wiring per S-P23-9…S-P23-11 and S-P23-17/-18:
    engine construction, `OptionSpreadsPanel.toggle_clicked`/`target_committed` →
    `engine.toggle_on`/`toggle_off`/`set_target`; chain request issuance via
    `ContractLookupService` + `req_sec_def_opt_params`; leg subscribe/cancel application of
    the engine's `Actions`; **every leg registered in `self.sub_manager` under the panel's tag
    with `reissue=lambda: market_data.req_mkt_data(contract)` and
    `rebind=lambda new_id: engine.rebind_leg(leg, new_id)`**, and the matching
    `unsubscribe` on cancel; **`_replay_subscriptions`'s `include_types` gains that one tag**
    (`AC-D65.14`(ii): `replay_all(include_types={RT_BARS, S0_TICKS, OPTION_LEGS})`);
    the **one** dedicated SPX spot line, opened **only when tier 3a yields no price** — the
    charted symbol is not SPX, or it is SPX with no chart price yet — and therefore never
    alongside a usable chart price (`get_index_contract("SPX")` → `req_mkt_data` →
    `engine.on_spot`, registered the same way, counted, cancelled when the seed completes, a
    refusal tolerated); `self._option_req_ids` routing for `tick_price`, `option_computation`
    **and the spot line's last price**; the 1 s evaluation `QTimer`; the coalesced
    `_refresh_option_panel`; `_md_line_count` += live option lines **and the spot line**; the
    `_on_error` option-owned-reqId branch forwarding `(reqId, code, text)` to
    `engine.on_leg_error`; `connected`/`disconnected` hooks →
    `engine.on_reconnected()`/`on_disconnected()`; **the spot tiers exactly as `AC-D65.15`
    states them** — tier **3a** reads the chart's `_last_chart_price` **only when
    `self._current_symbol` is `SPX`** (on any other symbol that value is another instrument's
    price and is *not* a spot source), tier **3b** is the one dedicated line above, tier **3c**
    runs the seed with **no** spot at all when that line is refused or never quotes.
  - `[new/changed] ibkr/subscription_manager.py` — **one added module-level type tag,
    `OPTION_LEGS`** (`AC-D65.14`(ii); value `"option_legs"`, matching the module's
    `rt_bars`/`market_data`/`s0_ticks` tag strings); no method changes.
  - **New tests:** `tests/test_d65_option_stream.py` — offscreen with a fake client:
    ON → 8 rows with exact **displayed (negative)** values; partial-leg `—`; **a Target change
    from a settled ladder lands on the new minimiser with every leg present in both ladders
    keeping its original `reqId`** (asserted on the fake client's `(reqId, action, leg)`
    recorder — never cancelled-and-re-requested), the leaving legs cancelled before the arriving
    ones are subscribed and **the live option count never above 16 at any recorded step**; the
    **shared-leg case** asserted on real reqIds; OFF → zero option reqIds, zero spot reqIds and
    all `—`; guard refusal at the cap (one message, tail rows `—`); burst-coalescing refresh
    count; **the lifecycle group** — a simulated drop marks every cell `STALE`, no evaluation
    moves the ladder, nothing is cancelled, and reconnect re-issues **exactly one**
    `reqMktData` per leg (no duplicate subscription) with the ladder resuming from the same
    anchor; **the error-code group** — one case per class (200 non-anchor / 200 anchor /
    10197 / 354 / 162 / other) asserting the row, the single message and the re-seat behaviour
    end-to-end through `_on_error`; **the spot group — `AC-D65.15`'s three tiers, asserted one
    for one**: a chart on **SPX** **with a last price** opens **zero** spot lines (tier 3a —
    the chart's own last price *is* the spot); a chart on **any other symbol** — **including** a
    window holding a
    live SPX `TickerSession`, which is *not* a spot source — opens **exactly one** dedicated
    SPX line (tier 3b: one, never two and never zero), which is counted, whose last price is
    routed to `engine.on_spot`, and which is cancelled after the seed; a refused or never-
    quoting line leaves **no** spot and the seed still completes (tier 3c);
    **total-lines assertion** (`option ≤ 16`, `total ≤ 17`) at every recorded step; the cutoff
    state; a rejected Target changing no anchor and no line, **and an accepted Target edit
    emitting once and starting an immediate re-seed**; **a restart case asserting launch is OFF
    at `1.00` with zero option/spot lines**; injected faults (greeks
    absent/sentineled/mixed-source, rejected leg, invalid Target, no-0DTE day) each counted
    once; a fake-client recording assertion that no order call is made; collapse-while-ON keeps
    streaming.
    **One cross-wave obligation, stated so it is not discovered at build:** the fake client
    also carries `reqPositions()` and `reqAccountSummary(...)` as no-op recorders, because
    `_subscribe_account_data` still runs on connect until P23-06 deletes it; **P23-06 deletes
    those two recorders with `_stub_account_calls`** (same subject-follows-test rule), so
    P23-09's gate finds no dead fake method and no later wave inherits a live-looking stub.
- **Dependencies:** P23-01, P23-02, P23-03, P23-04 (all of them — the engine's full surface is
  what this wave drives).
- **Touches:** `ui/main_window.py` (option blocks + `_replay_subscriptions`),
  `ibkr/subscription_manager.py` (one constant) + the new suite. Serialisation:
  `ui/main_window.py` against P23-06; `ibkr/subscription_manager.py` is edited by no other wave.
- **Exit condition:** the stream suite is green; `AC-D65.6`'s reqId-set assertions hold exactly
  (≤16 option lines at every recorded step, the same `reqId` for every shared leg across a
  re-anchor, the expected diff on the leaving legs, 0 after OFF); `AC-D65.14`'s replay case
  proves **one** replay per leg and **no** duplicate subscription; `AC-D65.15`'s spot cases
  prove the 16 + 1 ceiling tier by tier — **zero** spot lines when the chart shows SPX **and
  has a price**, **exactly one** otherwise (any other symbol, or SPX with no chart price yet),
  **none** when the line is refused — plus no more than
  16 option lines at any recorded step; the burst case shows one refresh per
  event-loop turn; the **watchlist suite is green unchanged** (the registry change is one tag);
  a fresh `import main` is clean.

### P23-06 — Account/position window path removal — size S

- **Goal:** the window no longer subscribes to, receives, persists or renders account or
  position data — the panel that consumed it is already gone (P23-01, which also removed every
  panel call the window made) and the new panel is live (P23-05), so the dock is never empty
  mid-batch. This wave removes the **residue** the panel swap left: the subscription, the four
  connects, the state, the handlers' bodies and the price-sink chain.
- **Covers:** `AC-D65.13`'s window-consumer group; **`AC-D65.18`'s file set** for the two
  modules beyond `main_window`; `AC-D65.11`'s "no behavioural assertion weakened" bookkeeping;
  **S-P23-24** (the badge re-point that closes the account plane's last reader); DG121.
- **Deliverables (deletions, plus the badge re-point named below):** `ui/main_window.py` — the four `b.*` connects (`:842-846`)
  *(the panel initialisers and every other dereference of the renamed attribute are **not** here:
  P23-01 deleted them with the panel — RC-16)*; `_subscribe_account_data` and its connect-time call
  (`:1676`); `_on_account_summary` / `_on_account_summary_end` / `_on_position_update` /
  `_on_position_end` / `_prune_foreign_positions` / `_upsert_position` and the bulk DB read
  (**including the `positions` local the panel-call deletion stranded in P23-01**);
  the state (`_account_subscribed`, `_account_summary_req_id`, `_account_summary`,
  `_live_accounts`, `_account_summary_complete`, `_positions_rendered`, `_positions_*`) **and
  the ESC-043/ESC-052 comment blocks that document them (`:890-913`)**; the disconnect-time
  account state clears (`:2066-2071` — the panel availability call at `:2072` left in P23-01);
  the "Account summary received for …" status line; the dead
  imports at `:80` (`Position`) and `:4403`; `_symbol_last_prices` **and its D27.5 comment at
  `:890-892`** (it spells `Position` and names `_last_chart_price` as a source the panel is
  "never" to use — stale twice over, and `Position` joins P23-08's token list; it goes with the
  attribute it describes), `_record_symbol_price`
  and its `set_price_sink` registration (`:767`); **`ui/watchlist_panel.py`'s `set_price_sink`
  (`:954`), `_price_sink` (`:391`, `:1149-1152`) and its call site**; **`ui/ticker_session.py:562`**'s
  host call. **All three files are `AC-D65.18`'s named file set, not just `main_window`** —
  the price-sink plumbing the Portfolio P/L consumed dies with its only reader.
  **Suites:** the six D27 account/position suites (`test_d27_account_subs`,
  `test_d27_account_scoping`, `test_d27_account_partial_window`, `test_d27_flat_rows`,
  `test_d27_position_id`, `test_d27_position_prices`) are **already gone — P23-01 deleted
  them with the panel they render into**, so this wave deletes behaviour with no test file
  left to edit *for those suites*. The test-side edits this wave does own are the
  `_stub_account_calls` removal, the five `_record_symbol_price` stubs and the stream
  suite's two account recorders — all below.
  - `[new/changed] tests/test_d45_removal.py` — **`_stub_account_calls` (:492-498) and its
    call site (:555) leave in this wave**: their only purpose was to keep `_on_connected`'s
    `reqPositions`/`reqAccountSummary` calls off the mocked socket, and this wave deletes the
    `_subscribe_account_data` call that made them. Left in place they are a test helper with
    no consumer — exactly what P23-09's residue gate clause (ii) reddens.
  - **Five inert `_record_symbol_price` fake-host stubs leave in this wave (RC-13).**
    `ui/ticker_session.py:562` is the only caller of `_host._record_symbol_price` in the
    tree, and five surviving suites keep a stub for it. None asserts on the recorded value,
    so they are inert rather than red today — but each names a token this wave deletes, and
    the exit below is a tree-wide claim, so they go with the call:
    `tests/test_p7_w4_streaming.py:140-141` (`host.prices = {}` + the recording lambda —
    `host.prices` has no other reader in the file), `tests/test_d39_burst_search.py:332-335`
    (`_StubHost.recorded` + the method — `recorded` has no other reader),
    `tests/test_lwc_popouts.py:129-130`, `tests/test_p13_fanout.py:104-105` (method-only in
    both), and `tests/test_p9_alarm_persistence.py:39` (`_stub_host()`'s only argument, so
    its namespace becomes empty). One line each; nothing is re-pointed.
  - **The stream suite's two account recorders** (`tests/test_d65_option_stream.py`, added in
    P23-05 because the window still subscribed on connect) leave here with the calls they
    absorb.
  - **`[new/changed] ui/main_window.py` — the connection badge's account read is re-pointed in
    this wave (S-P23-24, RC-14(i)/(ii)).** `_update_conn_badge` (`:1645-1659`) is the account
    plane's last surviving reader; it loses `getattr(self, "_account_summary", {})` (`:1651`)
    and `getattr(self, "_account_id", None)` (`:1653`) and calls
    `conn_badge_text(monitoring_paused=self._tws_paused)`; `conn_badge_text` (`:201-223`) loses
    its `account_id`/`account_type` parameters and the `DU`/`DEMO`/`PAPER` branch, returning
    `"● Connected"`/`#34d399` while connected and the **unchanged** D40 paused wording (amber)
    while `_tws_paused`; the `"● Connecting"` construction default (`:418`),
    `_on_disconnected`'s `"● Disconnected"` (`:2087`) and the fail-fast port guard are
    untouched. **`_account_id` is deleted with its only writer (`:4336`)** and `_account_summary`
    with `_on_account_summary` — neither is left write-less, and the badge's docstring says what
    it now claims. Doing it here rather than later is what makes P23-07's `account_summary`
    grep true when it fires (RC-14(iii)); a worker may **not** invent a replacement source
    (S-P23-24's rejected alternatives) or keep the two fields alive.
  - **`[new/changed] tests/test_port_guard.py`** — the four badge cases (`:25-51`) test the
    account-typed contract that retires, so they are replaced: connected ⇒ `"● Connected"` with
    the green colour, and a paused window ⇒ the D40 paused wording with amber. The module
    docstring is re-worded to name S-P23-24. **The two port-guard cases (`:13-21`) are
    untouched** — the fail-fast live-port rule is exactly the half of `AC-D26.5` that survives.
- **Dependencies:** P23-05 (the panel must be live first).
- **Touches:** `ui/main_window.py`, `ui/watchlist_panel.py`, `ui/ticker_session.py`,
  `tests/test_d45_removal.py`, `tests/test_d65_option_stream.py`,
  `tests/test_p7_w4_streaming.py`, `tests/test_d39_burst_search.py`,
  `tests/test_lwc_popouts.py`, `tests/test_p13_fanout.py`,
  `tests/test_p9_alarm_persistence.py`, `tests/test_port_guard.py`. Serialisation:
  `ui/main_window.py` against P23-01/05 (separate blocks; **P23-01 has already removed the panel
  calls this wave's blocks sit beside, so no line of this wave names `option_spreads_panel`**),
  `tests/test_port_guard.py` by this wave only.
- **Exit condition:** the wave's **window-side** tokens are gone: a grep for `reqPositions`,
  `reqAccountSummary`, `_account_id`, `_account_summary`, `_live_accounts`,
  `_positions_rendered`, `_symbol_last_prices`,
  `_record_symbol_price`, `set_price_sink` and `_price_sink` over `ui/`, `ibkr/`, `services/`,
  `data/` **and `tests/`** is empty — `_account_summary` covers
  `_account_summary_req_id`/`_account_summary_complete` as substrings and does not touch the
  bridge's un-prefixed `account_summary`, which is P23-07's; **and the badge asserts its new
  contract**: `conn_badge_text` takes no account parameter, `_update_conn_badge` reads no
  account state, and `tests/test_port_guard.py` passes on the connected/paused pair. The five
  stub deletions and the two stream-suite
  recorders above are why that is literally true rather than true of production only, and
  `_price_sink`/`set_price_sink` appear in no test file at all (verified, which is why no
  watchlist test needs editing); the **handler/state** tokens are gone from `ui/`, their only
  home (`_on_account_summary`, `_on_account_summary_end`, `_on_position_update`,
  `_on_position_end`, `_prune_foreign_positions`, `_upsert_position`); **the same greps over
  the `AC-D65.18` file list** (`ui/main_window.py`, `ui/watchlist_panel.py`,
  `ui/ticker_session.py`, `ui/active_portfolio_panel.py`, `ibkr/account.py`, `ibkr/bridge.py`,
  `ibkr/client.py`, `data/db.py`, `data/models.py`, `services/strategy_detection.py`) are empty
  for **this wave's** tokens. **Two token families are deliberately not this wave's, so the
  exit is true when it fires:** `account_summary`/`account_summary_end` and `position_update`
  survive in `ibkr/bridge.py:43-46` and `ibkr/client.py:455-463` — the signals and the
  overrides are **P23-07's**, and P23-07's exit asserts those four absent; and
  `data/db.py:189`'s D27.5 comment still names `_upsert_position` because it documents the
  unique index **P23-08** deletes — the comment goes with the index in P23-08. No wave claims
  a token before its last occurrence dies. **The panel API the account path once called is
  likewise not this wave's:** `set_account_summary`, `set_account_id`, `set_account_unavailable`,
  `set_positions`, `add_position` and the attribute `portfolio_panel` are already absent from
  `ui/` — P23-01 deleted the ten call sites with the panel (RC-16) — so this wave neither claims
  them nor leaves a dereference of `option_spreads_panel` behind; the `positions` local it
  inherits from that deletion dies with the bulk read above. `_md_line_count` still returns RT + watchlist; the
  watchlist suite is green unchanged; `import main` is clean.

### P23-07 — Broker boundary, modules and models removal — size S

- **Goal:** the transport and data-model half of the displaced stack is gone, with each
  signal dying in the same wave as its only emitter.
- **Covers:** `AC-D65.13`'s broker-boundary and module groups.
- **Deliverables (delete only):** `ibkr/client.py` — `accountSummary`, `accountSummaryEnd`,
  `position`, `positionEnd`; `ibkr/bridge.py` — `account_summary`, `account_summary_end`,
  `position_update`, `position_end`; `ibkr/account.py` (whole file);
  `services/strategy_detection.py` (whole file); `data/models.py` — `Position`, `TradeGroup`;
  **deleted suites:** `tests/test_account.py`, `tests/test_strategy_detection.py`; and
  **`tests/test_ui_smoke.py:48` is a mandatory edit in this wave, not a conditional one** —
  `assert hasattr(data.models, "Position")` hard-fails the moment the dataclass goes, so it
  becomes `assert not hasattr(data.models, "Position")` and
  `assert not hasattr(data.models, "TradeGroup")` (the file is the import-surface smoke, and
  the absence assertion is the measure the retired symbol needs), with
  `assert hasattr(data.models, "Drawing")` at `:49` untouched.
  - `[new/changed] tests/test_d45_removal.py` — **block (d) is rewritten in this wave, not
    deferred**: all three of its subject classes (`data.models.Position`,
    `data.models.TradeGroup`, `ibkr.account.Position`) die here, so the existence-and-field
    loop (`:914-919`, which asserts `cls.__dataclass_fields__` is non-empty and that
    `stop_loss`/`take_profit` are absent from it) and the `build_position_from_ib` signature
    paragraph (`:920-923`) are **replaced by absence assertions** —
    `assert not hasattr(models, "Position")` and `assert not hasattr(models, "TradeGroup")`,
    the measure the deleted half needed all along — with `data.models.UserOrder`'s existing
    absence assertion (`:913`) untouched, and `data/models.py`'s stop/target field removal
    covered by them rather than by a field loop over classes that no longer exist. The
    `ibkr.account` imports (`:880-881`) go with the same wave, and the now-unused
    `import inspect` (`:48`) plus the docstring's `__dataclass_fields__`/`inspect.signature`
    sentence are removed with their only user. The schema block (g) and its
    `_PRE_P5_DDL`/`_write_pre_p5_db` fixtures stay for P23-08, which is where the
    column-absence half of the D46 retirement lands.
- **Dependencies:** P23-06 (consumers first — the four signals must have no receiver left).
- **Touches:** `ibkr/client.py`, `ibkr/bridge.py`, `ibkr/account.py` (delete),
  `services/strategy_detection.py` (delete), `data/models.py`, `tests/test_ui_smoke.py`,
  `tests/test_d45_removal.py`, the two deleted suites. Serialisation:
  `ibkr/client.py`/`ibkr/bridge.py` against P23-02 (different members).
- **Exit condition:** `import ibkr.account` raises `ModuleNotFoundError`;
  `import services.strategy_detection` raises `ModuleNotFoundError`; no module imports either;
  `data.models` exports no `Position`/`TradeGroup`; **`tests/test_ui_smoke.py:48-49` asserts
  those two absences and still asserts `Drawing`'s presence**; no `tests/` module contains
  `ibkr.account`, `build_position_from_ib`, `strategy_detection`, `detect_and_group` or
  `OptionLeg` (today's carriers are `tests/test_account.py` and
  `tests/test_strategy_detection.py` — the two suites this wave deletes — plus
  `tests/test_d27_position_id.py`, deleted in P23-01 with the panel, and
  `tests/test_d45_removal.py`, whose `ibkr.account` imports and block (d) go in this wave;
  the forbidden-token
  tables are excluded, per the convention in the exit-condition audit); **the four bridge
  signals and four overrides are absent — asserted, not inferred**: a wave-local grep for
  `account_summary`, `account_summary_end`, `position_update` and `position_end` (plus
  `accountSummary`, `accountSummaryEnd`, `positionEnd`) over `ui/`, `ibkr/`, `services/`,
  `data/` and `tests/` is empty, which is the claim P23-06 could not make and did not; **the one
  `ui/` carrier it could not see — the badge's `_account_summary`/`_account_id` read — was
  removed by P23-06's re-point (S-P23-24), so this grep now has no exception and no narrowed
  scope**; block
  (d) of
  `test_p5_end_state_all_removed_members_absent` is green with its
  `models.Position`/`models.TradeGroup` absence assertions and no existence loop left; the
  suite is green.

### P23-08 — Pre-drop backup, schema drop and residue-instrument re-baseline — size S

- **Goal:** **a verified copy exists before anything is dropped**, `positions`, `trade_groups`
  and `position_group_map` no longer exist in a fresh DB or an existing one, and the residue
  instrument describes the new tree.
- **Covers:** **`AC-D65.18` in full** (backup path/naming, read-only verification,
  `integrity_check`, row counts, abort-on-failure, the **full deletion file set** and its
  residue grep); `AC-D65.13`'s data group (A200); `AC-D65.12`'s displaced-token half;
  A210/R152.
- **Deliverables:**
  - `[new] data/db_backup.py` — `backup_before_drop(db_path: Path, now: datetime | None = None,
    backup_dir: Path | None = None) -> Path` per S-P23-21: `shutil.copy2` into
    `config.get_user_data_path("backups")` as
    `charting_app_pre-D65_<YYYYMMDD-HHMMSS>.sqlite3`, then a **read-only** open of the copy
    (`sqlite3.connect("file:…?mode=ro", uri=True)`, never the app's `DB`) requiring
    `PRAGMA integrity_check == "ok"` and `positions`/`trade_groups`/`position_group_map` present
    with their row counts (returned to the caller for the build result); raises on any failure.
  - `[new/changed] data/db.py` — the three `CREATE TABLE`s and the `idx_positions_symbol_con_id`
    creation removed; one guarded block in `_migrate_schema()` that **calls
    `backup_before_drop` first, only when at least one of the three tables still exists**, and
    **aborts the whole drop if it raises**; then `DROP TABLE IF EXISTS position_group_map` →
    `positions` → `trade_groups` (child first), idempotent on a fresh DB and on every later
    open; the D46 stop/target `ALTER TABLE … DROP COLUMN` loop deleted with its only subject;
    **the D27.5 comment at `:189` that names `_upsert_position` goes with the unique index it
    documents** — it is the index's own justification, and leaving it would redden the
    re-baselined instrument on `data/db.py` the moment `_upsert_position` joins `_FORBIDDEN`
    (below).
  - **New tests:** `tests/test_db_backup.py` — the backup exists at the expected name, opens
    read-only, passes `integrity_check` and reports the three row counts for a DB with rows; a
    **failure-injection** case (unreadable/corrupt copy source and a missing-table source) in
    which `backup_before_drop` raises **and** `_migrate_schema` leaves all three tables and their
    rows present; a fresh DB (no tables yet) skips the backup and still opens clean.
  - `[new/changed] tests/test_db_schema.py` — `EXPECTED_TABLES` (`:15-26`) loses **all
    three** names (`positions`, `trade_groups`, `position_group_map`) and gains an absence
    assertion for each plus a second-open no-op case (rows dropped once); the
    "ten tables" wording becomes the seven that remain.
  - `[new/changed] tests/conftest.py` — **the autouse `_isolate_test_db` teardown
    (`:105-124`) loses `position_group_map`, `positions` and `trade_groups` from its wipe
    list**, keeping the FK-child-first comment coherent for the tables that remain. Without
    this the whole suite raises `sqlite3.OperationalError: no such table: positions` at
    teardown of **every** test once the DROP lands.
  - `[new/changed] tests/test_d45_removal.py` — the schema half of
    `test_p5_end_state_all_removed_members_absent` (block (g), `:939-1001`, plus its
    `_PRE_P5_DDL` / `_write_pre_p5_db` fixtures at `:803`/`:837`) is **replaced by the
    table-absence case**: `sqlite_master` holds none of the three tables; a legacy DB built
    with the pre-P23 `_PRE_P5_DDL` loses them all on first open; a second open is a no-op.
    (Block (d)'s models half is already P23-07's — nothing of it is deferred to this wave.)
    `_FORBIDDEN` gains this phase's **symbol and module** tokens (`ActivePortfolioPanel`,
    `portfolio_panel`, `Account Summary`, `account_summary`, `account_summary_end`,
    `position_update`, `position_end`, `build_position_from_ib`, `_parse_contract_type`,
    `detect_and_group`, `OptionLeg`, `strategy_detection`, `Position`, `TradeGroup`,
    `_upsert_position`, `_symbol_last_prices`, `_record_symbol_price`, `set_price_sink`,
    `_price_sink`, `reqAccountSummary`, `reqPositions`, `_account_id`) — every one is dead by the
    end of this wave. **`_account_id` is the badge's token** (S-P23-24): it had no declaration,
    only the write in `_on_account_summary` and the read in `_update_conn_badge`, both removed in
    P23-06, so forbidding it here is what stops a future wave from resurrecting an account-typed
    badge source. **The three table names are deliberately *not* tokens** (`positions`, `trade_groups`,
    `position_group_map` are absent from `_FORBIDDEN` today and stay that way — they are not in
    `_SURVIVORS` today either): the one-time `DROP TABLE IF EXISTS …` in `data/db.py` and the
    absence assertions in `test_db_schema.py` and block (g) **must spell** the names they drop
    and prove gone, so tokenising them would redden the instrument on the very migration it
    describes — the same principle the token-table convention states below. Their absence is
    measured by the schema case, never by a token grep. The `_ALLOWED_IN_FILE` stop/target
    carve-out (`:220`), its `_allowed_in` helper (`:271`), the `_drop_column_subject_nodes` AST
    helper (`:1013-1046`), `_EXEMPT_TOKENS` (`:1010`) and
    `test_allowed_in_file_is_narrow_and_named_not_used` (`:1047+`) are **deleted with the
    columns they existed to migrate** — with the columns gone the exemption has no subject.
- **Dependencies:** P23-07 (nothing may read the tables when they drop).
- **Touches:** `data/db_backup.py` (new), `data/db.py`, `tests/test_db_backup.py` (new),
  `tests/test_db_schema.py`, `tests/conftest.py`, `tests/test_d45_removal.py`.
- **Exit condition:** **the backup exists, opens, passes `integrity_check` and holds the three
  tables with recorded row counts before the drop runs, and the injected-failure case proves the
  drop aborts with the tables intact**; a fresh DB has none of the three tables (nor the unique
  index) and took no backup; a legacy DB with rows loses all three tables on first open and a
  second open is a no-op; `tests/conftest.py` names no dropped table; `test_db_schema` and the
  re-baselined instrument are green; **the full suite runs clean at teardown** (no
  `no such table` error from any test); no `stop_loss`/`take_profit` carve-out remains; **the
  `AC-D65.18` file-set residue grep** — over `ui/main_window.py`, `ui/watchlist_panel.py`,
  `ui/ticker_session.py`, `ui/active_portfolio_panel.py` (gone), `ibkr/account.py` (gone),
  `ibkr/bridge.py`, `ibkr/client.py`, `data/db.py`, `data/models.py`,
  `services/strategy_detection.py` (gone) — finds no live occurrence of any displaced token
  (forbidden-token tables excepted, per the audit's convention).

### P23-09 — Standing residue gate + batch gate — size S

- **Goal:** the standing Unused-Code Rule is machine-checked from now on, and every
  `AC-D65.*` criterion **the build can observe** is satisfied with nothing else changed —
  `AC-D65.19` excluded, because it is the owner's recorded live-TWS, **read-only** run and
  P23-10 (built as P23-T26) owns it.
- **Covers:** `AC-D65.12` (the gate, proven red on a seeded dead-symbol fixture);
  `AC-D65.11` (history intact); **the 16 + 1 / sign / band consistency re-check** across every
  place those numbers are stated; the full-suite gate; `AC-D65.7`'s order-absence sweep;
  A197's inheritance.
- **Deliverables:**
  - `[new] tests/test_d65_residue.py` — S-P23-15's five clauses plus the seeded dead-symbol
    fixture (a temp module with an uncalled function must make the gate red), the new-symbol
    caller census with its allowlist carrying each registration site, the emitted-and-connected
    signal check, and the displaced-token absence sweep (P23-08's tokens).
  - **Batch gate:** full offscreen suite green
    (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`); `AC-D65.11` marker grep +
    `### D41`–`### D64` section presence; the record of **all three** owner-authorised
    pre-P23 edits (the D41 title re-points, A194's supersession, **A201's D18 launch-width
    amendment with its two re-baselines** — asserted by a `git log`/diff note in the gate
    record, not by a test), **plus the recorded phase-internal consequence of S-P23-24** —
    D26.5's paper/live badge derivation retired with the account path, its reason stated: the
    badge's only account-typed inputs died in P23-06, the port guard proves the port alone, and
    `"● Connected"` is the honest claim (it edits no `requirements.md` text, so `AC-D65.11`'s
    three records stand as three); **`AC-D65.9` observably closed** (the P23-01 group green: exact
    tracked launch width, the two re-baselines, the wide-fixture legibility and the narrow
    elide case); the bookkeeping checks — `tests/conftest.py` names no dropped table,
    `tests/test_p13_gate.py`'s allowlist holds `option_spreads_panel.py` and not
    `active_portfolio_panel.py`, and `tests/test_d45_removal.py` holds no test whose subject
    is deleted; **the line-accounting and sign consistency re-check** — one grep-driven pass
    asserting that `16` (option), `17` (with spot), `h = max(0.05, one_tick)`, the credit-vs-
    displayed pair and the canonical fixtures `7425/7445` / `7340/7320` are stated **identically
    in `docs/plan.md`, `docs/architecture.md`, the five new suites and the P23-10 record
    template**, with no surviving `7425/7435` or `7315/7435` example (A212's two typos — the
    10-wide pair and the inverted PCS; `7435/7455` is a **legal** 20-wide pair and
    `AC-D65.9`(i)'s own width example, so it is *not* banned) and no surviving flat-`0.05`-band
    phrasing; **`AC-D65.1`'s own measurable re-run against the finished tree** — a
    `tests/`-wide search finds no `Portfolio` dock title/`objectName` and no title-keyed
    right-dock lookup, using **P23-01's greps and its documented carve-out** (the
    forbidden-token tables of `test_d45_removal.py` and this wave's `test_d65_residue.py`);
    `USAGE.txt`/`docs/README` check that no text still advertises a
    Portfolio/Account Summary panel (the file names the right dock only as chrome today —
    verify, and correct only if it claims a Portfolio view); **and the explicit statement in
    the gate record that `AC-D65.19` is open and owned by P23-10**.
- **Dependencies:** P23-01…P23-08 (verifies their joint end state).
- **Touches:** `tests/test_d65_residue.py` (new) + docs prose only if the checks above find a
  stale claim. No production edits.
- **Exit condition:** the gate is green on the tree and red on the seeded fixture; the full
  suite is green at teardown (conftest clean); every `AC-D65.*` the build can observe is
  satisfied, including `AC-D65.9`, and `AC-D65.19` is **recorded as still open** rather than
  claimed; no D1–P22 behaviour or wording regressed beyond the three recorded edits **and
  S-P23-24's recorded badge consequence**; no `PLAN`-routed escalation open.

### P23-10 — Owner-run live-TWS, read-only acceptance (built as P23-T26) — size S (owner-run gate, docs only)

- **Goal:** the only evidence against a real gateway is produced and recorded: an owner-run
  live-TWS, **read-only** acceptance on `127.0.0.1:7496` (there is no paper account — A211) whose
  checklist is mechanical, observation-only, and whose evidence is written down.
- **Covers:** **`AC-D65.19` in full** (A211): (1) eight rows populate for today's SPXW expiry;
  (2) Delta/Gamma arrive from model greeks; (3) a Target change steps the ladder and re-reads
  the Target; (4) **OFF cancels every option line**, verified against TWS's own line count;
  (5) a forced disconnect marks values `STALE` and freezes the walk, reconnect replays and
  recovers; (6) the display-only guarantee holds **observationally** — TWS's Orders pane stays
  empty for the whole session and the session log shows no order-shaped call, matching the static
  residue guard (zero order code: no order-shaped call exists or is possible). R144/R150.
- **Deliverables:**
  - `[new] docs/archive/probe_records/d65_paper_tws_acceptance.md` — the recorded-probe shape
    of the neighbouring `d48_probe_record.md`/`d52_probe_record.md`: a header naming the live
    host/port `127.0.0.1:7496` (read-only by construction — zero order code; only
    `reqSecDefOptParams`/`reqMktData`/`cancelMktData` are issued) and the build commit, the six
    items as checkboxes each with an **evidence field** (what was seen, where), a **TWS
    market-data line count before ON, while ON and after OFF** table (expecting ≤17 while ON and
    a return to the pre-ON baseline after OFF), a place for screenshots/notes, and a closing
    statement recording the run date or the owner's explicit waiver. The file name is retained so
    existing references resolve; the record's own head block states that the path predates the
    2026-11-18 amendment and that the run is live.
- **Dependencies:** P23-09 (the phase must otherwise be green).
- **Touches:** `docs/archive/probe_records/d65_paper_tws_acceptance.md` (new). **No production
  or test-code edits** — a code change discovered by the run is escalated as a build finding,
  not patched in this wave.
- **Exit condition:** the record exists with all six items checked and their evidence filled
  in, the line-count table shows the return to baseline after OFF, and the run is signed with a
  date — **or** an explicit recorded owner waiver of the whole gate. Nothing in the automated
  suite may satisfy this exit; the wave is the owner's, and P23-09 may not claim it.

**Wave note (serialisation).** `ui/main_window.py` is edited in **P23-01** (dock block + the
rename **and the ten `ActivePortfolioPanel` call-site deletions** + the launch-width seed and
`_deferred_dock_setup`'s one added argument), **P23-05** (option wiring + the one added tag in
`_replay_subscriptions`) and **P23-06** (the account-path residue **and the badge block,
`conn_badge_text` included**) — distinct blocks, serialised in that order. **P23-01 leaves no
dereference of the renamed attribute behind** (eighteen spellings, all its own: the module import,
the dock block, the three probes and the ten calls) and **P23-06 introduces none** (it names
`option_spreads_panel` nowhere and no longer owns the panel initialisers), which is what makes the
two consecutive rather than parallel.
`tests/test_port_guard.py` is edited **only in P23-06** (the badge contract); `ibkr/subscription_manager.py` is edited **only in P23-05**
(one constant); `ibkr/client.py` and `ibkr/bridge.py` in **P23-02** (additions) and **P23-07**
(deletions); `services/option_spread_engine.py` across **P23-03** then **P23-04** (same new
module, second half — one worker per wave, never parallel); `data/models.py` only in P23-07;
`data/db_backup.py` and `data/db.py` only in P23-08; `tests/conftest.py` only in P23-08;
`tests/test_d45_removal.py` in **P23-01** (the walkthrough group), **P23-06**
(`_stub_account_calls`), **P23-07** (block (d)) and **P23-08** (block (g) + the carve-out), each
wave touching only its own functions; the acceptance record only in P23-10. **Ordering is
forced, not stylistic:** the new panel must be live before the account path dies (else the dock
is empty mid-batch and a worker death leaves an unusable window); each signal dies in the same
wave as its only emitter; a test dies in the same wave as the subject it reads (the six D27
suites with the panel, `_stub_account_calls` with the subscription call, block (d) with the two
model classes, block (g) with the tables); the registry tag lands with the wiring that registers
legs (P23-05) and before any deletion, so replay is never briefly unowned; the backup lands in
the same wave as the drop and **before** it, because a later wave would be too late; and the
token set lands last because a token may only name code that is already gone (the P5 lesson).

### Exit-condition audit (wave → dependency → ownership → verdict)

Every wave's exit condition was re-read against the tree, listing each test module and
production symbol it depends on, and each was checked to be either **owned by that wave** or
**untouched until the wave that does own it**. This is the check the last three reviews had to
re-derive; it is recorded so it can be verified instead. **It was re-derived again for the
ten-wave cut of pass 5**, including the two new subjects (the registry/lifecycle wiring and the
owner-run acceptance record).

**The token-grep convention, stated once.** P23-06's and P23-07's token greps are *wave-local*
— they are run at the end of their wave and are not re-run afterwards. P23-01's dock-identity
greps are *re-run at P23-09* on the finished tree, and they therefore carry a documented
carve-out: the forbidden-token tables (`tests/test_d45_removal.py`'s `_FORBIDDEN`/`_SURVIVORS`,
which P23-08 extends, and `tests/test_d65_residue.py`'s displaced-token list, which P23-09
creates) are the only places a retired spelling may survive — a forbidden token has to be
spelled to be forbidden, and those tables are literal strings, never imports, attribute
accesses or assertion subjects. Without the carve-out the gate would redden on itself.

| Wave | What its exit condition reads | Owner of that subject | Verdict |
|---|---|---|---|
| **P23-01** | `test_d65_option_panel.py`, `test_d65_option_ladder.py` (new); the 8 edited book suites (incl. `test_dock_d18_region.py` and `T48-T03`); the **20** lookup modules; the 2 D18 re-baseline sites; `test_d41_portfolio_dock.py` + the 6 D27 suites (deleted); `test_d45_removal.py`'s walkthrough group; `OptionSpreadsPanel`, `option_ladder` (incl. `usable_quote`, `option_tick`, `match_band`, the sign pair), `main_window`'s dock block **and its ten `ActivePortfolioPanel` call sites (deleted here — RC-16)**, `active_portfolio_panel.py` (deleted) | **all of them, this wave** | **PASS** — the exit's greps are satisfiable exactly because the 20 lookups, the 8 book files, the 10 call sites and the 7 deletions are all here; the Target-validation and fixture-guard groups read only the panel and the ladder module this wave creates; **and the rename does not outrun its consumers**: the ten dereferences die in the wave that renames the attribute, so the first `MainWindow()` after it constructs, connects and disconnects clean (`test_d27_reconnect.py:183-215`, `test_d65_option_panel.py`, the reworked walkthrough) instead of raising at `:849` |
| **P23-02** | `test_d65_option_chain.py` (new); the **persistence** of the four account `EWrapper` overrides; the three new overrides/signals; "no production caller outside `ibkr/`" | new suite here; the account overrides are **P23-07**'s, untouched | **PASS** — the exit asserts they still exist, which is true until P23-07, and no test it reads dies later |
| **P23-03** | `test_d65_spread_engine.py` (new, part 1); `option_ladder` (P23-01), `OptionSeries`/`LegKey` (P23-02) | new here; earlier waves, unmodified | **PASS** — pure engine, reads no test that moves; the seed/lease cases read only this wave's module |
| **P23-04** | `test_d65_spread_engine.py` (new, part 2 — same file, second wave); the module P23-03 created | **this wave** for the half it adds; P23-03's half is already green | **PASS** — the file is *appended to* by this wave and the exit names only its own groups; the module was created one wave earlier and is not renamed |
| **P23-05** | `test_d65_option_stream.py` (new); `main_window`'s option blocks + `_replay_subscriptions`; `ibkr/subscription_manager.py`'s one tag; the **still-live account path** (`reqPositions`/`reqAccountSummary` on connect) | option blocks, the tag and the spot line here; the account calls and the fake client's two recorders **P23-06** | **PASS** — the one cross-wave test surface is retired in the wave that deletes its subject (named in P23-06); the watchlist suite is read as *unchanged*, which is exactly what the tag edit must not disturb |
| **P23-06** | the window-side tokens (`reqPositions`, `reqAccountSummary`, **`_account_id`**, **`_account_summary`**, `_live_accounts`, `_positions_rendered`, `_symbol_last_prices`, `_record_symbol_price`, `set_price_sink`, `_price_sink`) over `ui/`, `ibkr/`, `services/`, `data/` and `tests/`; the handler/state tokens over `ui/`; **the badge re-point and `tests/test_port_guard.py`'s new contract**; `_stub_account_calls`; the **5 inert `_record_symbol_price` stubs**; the 2 stream-suite account recorders; **the `AC-D65.18` file list** for this wave's tokens | **all here — and only the residue**: the panel calls these handlers made left in P23-01 | **PASS (corrected, RC-3; extended, RC-14; narrowed, RC-16)** — every token on the list is gone when the wave ends, verified in the tree: the bridge/client `account_summary`/`position_update` and `data/db.py`'s `_upsert_position` comment are **excluded by name** and asserted by P23-07/-08, the waves that delete them; the badge's `:1651`/`:1653` reads — the one carrier the previous cut left standing — are removed by this wave's own edit (S-P23-24); and **no row of this exit reads the panel**: `portfolio_panel` and the five panel methods are already gone from `ui/` (P23-01), so the row claims nothing a different wave owns |
| **P23-07** | block (d) + `import inspect`; **`test_ui_smoke.py:48`** (mandatory); `test_account.py`/`test_strategy_detection.py` (deleted); `Position`/`TradeGroup`; `ibkr/account.py`; `services/strategy_detection.py`; **the four bridge/client account tokens** (`account_summary`, `account_summary_end`, `position_update`, `position_end` + the three camel-case overrides), absent tree-wide; the instrument's token lists naming this wave's tokens | **all here** | **PASS** — the smoke edit is an edit, not a judgement call, and the four account tokens are gone exactly here: `ibkr/bridge.py:43-46` and `ibkr/client.py:455-463` are this wave's deletions, so its grep is true when it fires |
| **P23-08** | `data/db_backup.py` (new) + `tests/test_db_backup.py` (new); `tests/conftest.py`; `test_db_schema.py` `EXPECTED_TABLES`; block (g) + `_PRE_P5_DDL`/`_write_pre_p5_db`; `_ALLOWED_IN_FILE`, `_allowed_in`, `_drop_column_subject_nodes`, `_EXEMPT_TOKENS`, `test_allowed_in_file_is_narrow_and_named_not_used` | **all here** | **PASS** — the backup module is created and called in the same wave as the drop, so no wave reads a backup that does not exist yet; verified the three tables' only other readers were the 6 deleted D27 suites + `test_d45_removal.py`, so no surviving suite breaks at teardown |
| **P23-09** | the full suite; `test_d65_residue.py` (new); P23-01's `AC-D65.9` group and its dock-identity greps **plus their token-table carve-out**; the conftest/p13/d45 bookkeeping; **the S-P23-24 consequence record**; the 16+1 / sign / band consistency greps over the phase's own documents and suites | owned here / artifacts of earlier waves | **PASS** — a verification wave owns no subject it outlives; the one place it *writes* a retired token (its own forbidden list, and P23-08's additions to `test_d45_removal.py`'s) is excluded by the carve-out stated above; **and it explicitly records `AC-D65.19` as open** rather than claiming an owner-run criterion |
| **P23-10** | **`AC-D65.19` only** — the six checklist items, their evidence, the TWS line-count table, the dated run/waiver; the phase's green state is P23-09's verdict, read as an input | **this wave (the owner's run)** | **PASS** — the wave owns its one subject and edits nothing in the tree but its own record; a code defect found by the run is escalated as a build finding rather than patched here |

**The invariant this table checks.** A wave's exit may only assert on (i) files it edits or
deletes in that wave, (ii) symbols it introduces or removes in that wave, or (iii) state whose
*persistence* it is the point of the wave to confirm (P23-02's four overrides). Where a later
wave changes something an earlier wave's test touches — P23-06 deleting the account calls
under P23-05's fake client, P23-08 dropping tables under the shared `conftest.py` — the
dependent edit is scheduled in that later wave and named in its deliverables, never left for
the build to discover. **Owner-run criteria are outside this table by construction**: P23-10's
exit is a recorded human run, so no build wave may claim `AC-D65.19`, and P23-09's gate record
states it as open rather than satisfied.

### Deletion inventory (member groups → wave → end-state token)

| Member group | Members | Wave | Absence token(s) asserted |
|---|---|---|---|
| Panel module + dock wiring | `ui/active_portfolio_panel.py`; dock title/`objectName` `Portfolio`; title-bar widget; the three collapse probes' panel references; **the ten `ActivePortfolioPanel` API call sites in `ui/main_window.py`** (`:849,850,852,1731,2072,4349,4350,4357,4468,4538` — deleted, not re-pointed: the new panel has none of those methods, RC-16); **the 20 surviving title-keyed dock lookups (re-pointed to `objectName()`)**; `tests/test_d41_portfolio_dock.py`; the six D27 account/position suites (every one reads `win.portfolio_panel` or imports the module) | P23-01 | `ActivePortfolioPanel`, `portfolio_panel`, `Portfolio` (dock title and any lookup keyed on it), `Account Summary`, and the five panel method names (`set_account_summary`, `set_account_id`, `set_account_unavailable`, `set_positions`, `add_position`) absent from `ui/main_window.py` |
| Window consumers | 4 connects (`:842-846` — the panel initialisers and every other panel call are **P23-01's**, in the row above); `_subscribe_account_data`; `_on_account_summary`/`_on_account_summary_end`/`_on_position_update`/`_on_position_end`/`_prune_foreign_positions`/`_upsert_position`; bulk DB read (with the `positions` local P23-01's deletion stranded); 6 state fields; the account state clears (`:2066-2071`); the account status line; 2 dead imports; **the badge's account read** (`_update_conn_badge`'s `_account_summary`/`_account_id`; `conn_badge_text`'s two account parameters and the `DU`/`DEMO`/`PAPER` branch) | P23-06 | `reqPositions`, `reqAccountSummary`, `_account_id`, `_account_summary`, `_live_accounts`, `_positions_rendered`, `_upsert_position`, `_on_account_summary`, `_on_position_update` — all absent **tree-wide** by the end of the wave, with one documented exception: `data/db.py:189`'s D27.5 comment names `_upsert_position` and goes with the unique index in **P23-08**. The two broker-boundary spellings are **not** this row's: `account_summary`/`position_update` die in **P23-07** |
| Displacement chain | `_symbol_last_prices` **and the D27.5 comment at `:890-892` that documents it**; `_record_symbol_price`; `set_price_sink`/`_price_sink`; the `ticker_session` host call (**the `AC-D65.18` file set: `ui/watchlist_panel.py`, `ui/ticker_session.py`**) | P23-06 | `_symbol_last_prices`, `_record_symbol_price`, `set_price_sink`, `_price_sink` |
| Broker boundary | 4 `EWrapper` overrides; 4 bridge signals | P23-07 | `accountSummary`, `accountSummaryEnd`, `positionEnd`, `account_summary`, `account_summary_end`, `position_update`, `position_end` |
| Modules + models | `ibkr/account.py`; `services/strategy_detection.py`; `data.models.Position`/`TradeGroup`; `tests/test_account.py`; `tests/test_strategy_detection.py` | P23-07 | `build_position_from_ib`, `_parse_contract_type`, `detect_and_group`, `OptionLeg`, `TradeGroup`, `strategy_detection` |
| Data path | `positions`/`trade_groups`/`position_group_map` DDL + rows; the unique index; the D46 column-drop loop; `test_db_schema` expectations; the instrument carve-out; **preceded by the verified backup** | P23-08 | the **schema case** (`sqlite_master` holds none of the three; the table names are spelled by the migration and by the absence assertions, so they are **not** grep tokens), `idx_positions_symbol_con_id`, and the `stop_loss`/`take_profit` carve-out |
| Test bookkeeping (suite-wide) | `tests/conftest.py`'s autouse wipe list; `tests/test_p13_gate.py`'s `ui/*.py` allowlist entry; the per-wave splits of `tests/test_d45_removal.py` | P23-01 (the panel-member test + its tuple, the walkthrough rework, the eight-column test), P23-06 (`_stub_account_calls` + its call site), P23-07 (block (d) → the two model-absence assertions), P23-08 (the `conftest.py` wipe list, block (g) → the table-absence case, the carve-out) | `position_group_map` absent from `conftest.py`, `active_portfolio_panel.py` absent from the p13 allowlist, `_REMOVED_PANEL_MEMBERS`, `_ALLOWED_IN_FILE`, `_stub_account_calls`, `test_positions_table_is_eight_columns` and any `portfolio_panel`/`positions_table` reference in `tests/` all absent (forbidden-token tables excepted, as above) |

**Not a deletion, but part of the same dangerous step:** `data/db_backup.py` (P23-08) is
**created** in the wave that drops the tables and is called by `_migrate_schema` **before** the
drop, so the deletion inventory above is only executable once the verified copy exists — the
backup is the precondition, not a follow-up.

**KEEP (with the surviving consumer, and why):** `IdManager.get_id` (six market-data callers
plus P23's legs); the generic TWS-error status path and `classify_error` (the only error
surface, and P23's option branch reads it); **`SubscriptionManager`** (the D27.3 registry — the
chart's RT bars, the S0 ticks and, from P23-05, the panel's legs; P23 adds one tag and changes
no method); the right dock itself (it hosts `Option Spreads`); `ui/dock_layout.py` (the width
model); `ui/visual_conventions.py` (the collapse header and the toggle-state shape);
`services/md_line_guard.py` (the budget the panel is built on); `config/paths.py` (the backup
directory); the bar/session/chart stack (untouched). **Nothing is retained-and-inert.**

### Assumptions

| # | Assumption | Rationale |
|---|---|---|
| AP-P23-1 | Both sides use the **same** rung offsets (1 = +10, 2 = +5, 3 = anchor, 4 = −5) with the short leg written first, so PCS row 1 is `anchor+10` (`7350/7330` in the owner's example) | A187/Q109(a): only this reading makes all eight worked numbers the same four 20-wide spreads; the mirrored reading is the typo the owner's own example contradicts |
| AP-P23-2 | Tie-break 3 (short strike nearer the underlying's last price) reads the **same spot chain as the seed** (S-P23-13/AP-P23-15): the chart's `_last_chart_price` when the charted symbol is SPX, else the price the **one** dedicated SPX line has delivered (tier 3b), else no price — the tie-break is skipped and the lower short strike wins | `AC-D65.15`'s chain is the only phase-stable source set, and sharing it means one implementation and one set of cases; `_symbol_last_prices` is not revived (A198/`AC-D65.18`) and no `TickerSession` bar read is added, because neither is a source the AC has. It is the last of three tie-breaks and its AC cases feed the price, so measurability is unaffected. S-P23-13 / AR-P23-12 |
| AP-P23-3 | Quote and greek sentinels are screened as `None`, `-1`, `1.7976931348623157e+308`, `NaN`/`±inf` **and** an unreceived side before use | The pinned client and older `ibapi` shapes differ on the "no value" encoding, and `AC-D65.16` names three encodings explicitly; screening them at one helper (`usable_quote`/the greek screen) is the only version-proof reading. A received `0` bid is **not** a sentinel — it is a price |
| AP-P23-4 | Launch state is Target `1.00`, toggle OFF, no persisted value, no QSettings key, no chain cache across restarts | A192/A209/Q111; a persisted ON state would subscribe lines before the user looks (FS25 remains the persistence suggestion) |
| AP-P23-5 | Option-owned TWS errors are routed by `_on_error` into the engine's latch and surfaced on the **panel** status label, not the window status bar; every other reqId keeps the generic line. The four classes are the engine's table, not `_on_error`'s | AC-D65.8/AC-D65.14(iii) count one message per cause; two surfaces would read as two errors, and keeping the classification in the pure engine is what makes all four branches testable without a window. The generic path is otherwise untouched (A198 KEEP) |
| AP-P23-6 | Every anchor change — a maintenance step, a Target change's refine, the OFF→ON seed's refine, an unusable-anchor correction — is **one window step**: the leaving leg pair is cancelled *before* the arriving pair is subscribed (2 + 2 per side), so the live **option** count is 16 → 14 → 16 and a leg held by both windows is never cancelled. The seed's coarse tier is **leases only** (2 lines against free capacity, released on score) — never a second pool, never a leg the live window holds | The only shape that satisfies the shared-leg rule *and* the option-line cap while still measuring a cold start: a lease is capacity-neutral, so the cap holds by construction rather than by luck. `S-P23-5` states the contiguity argument (a leg belongs to a contiguous range of anchors) |
| AP-P23-7 | The visual gate (AC-G.1) needs no new reference: the only new visual is the red/green toggle the owner specified, and every other control reuses VIS-D21 | Same reuse precedent as AP-P22-5/AP-P21-6 |
| AP-P23-8 | Sizes: P23-01, P23-03 and P23-05 are M; P23-02, P23-04, P23-06…P23-10 are S. P23-01 also carries the dock identity's **twenty-lookup surface** (A198's "every title-keyed lookup" clause) and the **ten `ActivePortfolioPanel` call-site deletions** (RC-16); P23-03/P23-04 are the two halves of one new module (never parallel) | Each wave is bounded by one member group; no wave exceeds M, which is what keeps the delete-only waves inside a worker's step budget (R146). The engine split follows the pass-5 additions (seed/validity vs lifecycle/errors), so neither half is L. The twenty lookups are one predicate line each inside the panel-swap member group the wave already owns — splitting them into their own wave is impossible in either order (after the rename it leaves the rename's wave red; before it, the key does not exist yet). **The ten call-site deletions are the same argument one step further:** a dereference of the renamed attribute cannot wait for P23-06 (the first `MainWindow()` raises), and cannot be re-pointed instead (the new panel has none of the five methods), so they are one-line deletions inside the member group the wave already owns and the wave stays M |
| AP-P23-9 | `position_group_map` and the `_symbol_last_prices` price-sink chain are **inventory completions** under A198 clause 3 ("every helper only it called"), not scope expansion — and `AC-D65.18` names the same file set | Verified: `position_group_map` has zero readers/writers and is a FK child of a dropped table; the price sink's only reader is the deleted position render. Leaving either would violate the rule P23 is gated on |
| AP-P23-10 | The residue-instrument re-baseline touches only `tests/test_d45_removal.py`'s declared token lists, its per-wave test removals and the schema case; no behavioural assertion is weakened | AC-D65.11/AC-D65.13; the P5 precedent (re-baseline recorded, not softened) |
| AP-P23-11 | `AC-D65.3`'s scan is read as *(a)* the seed's bounded measurement, then *(b)* the ordered candidate list explored **by a monotone sweep** (the minimiser found by the neighbour rule), which is exact because a 20-wide credit vertical's net bid/ask are monotone in strike distance from the money (`d` quasi-convex); a chain observed to break that switches to the full ordered sweep, which visits every window in one direction | Reaching a better pair *past* a plateau would require re-requesting legs of the previous ladder, which `AC-D65.6` forbids — so the two criteria are jointly satisfiable only under quasi-convexity, which the plan states instead of hiding. The ordered sweep is the exact-coverage fallback and keeps the same accounting; the 10 s / 12-pair bound (S-P23-18) applies to both |
| AP-P23-12 | A seed is a bounded, explicitly triggered sequence, not a tick loop: one probe lease per event-loop turn, then one window step per turn, paced by `PacingManager.throttle()`; the 1 s cadence (A191) governs **maintenance** decisions and re-arms a bounded seed | A191's 1 s debounce exists to stop tick-driven thrash; a seed is triggered by ON / a Target change / an unusable anchor. The alternative — an atomic wholesale cancel+refill — is the `AC-D65.6` violation RC-5 removed. Blank rows are never shown: every intermediate window is a real, quoted ladder |
| AP-P23-13 | The `AC-D65.9` launch width is derived, never stored: `_right_launch_width` holds the panel's preferred width from construction and `_deferred_dock_setup` applies it once (the D17.4 pattern), clamped through `plan_dock_widths`; no QSettings key is added and `_right_dock_width` keeps tracking the live width | `A201`/`A192`; "nothing is persisted — a restart returns the launch width" is asserted on the tracked value at launch and after a rebuild. The two D18 re-baseline sites change only their expected constant (A201), and the rendered line keeps the file's existing `+1` slack-distribution convention |
| AP-P23-14 | The option legs register under a **new** type tag in `ibkr/subscription_manager.py` — **`OPTION_LEGS`** — and `_replay_subscriptions`'s `include_types` gains that tag: `replay_all(include_types={RT_BARS, S0_TICKS, OPTION_LEGS})` | `AC-D65.14`(ii) states exactly this (a new `OPTION_LEGS` tag beside `RT_BARS`/`MARKET_DATA`/`S0_TICKS`, added to the include set at the single call site, legs **never** registered as `MARKET_DATA`). Every watchlist row already carries `MARKET_DATA` **with** a `reissue` hook (`ui/watchlist_panel.py:1003-1015`), so widening that tag would re-issue every row on top of `_restore_watchlist`'s pinned clear+re-add (AC-D22.7.2, unchanged). One constant + one include-set entry is the whole change, and the watchlist suite is asserted green unchanged. FI-P23-3 raised this and was **fixed in the requirement text 2026-11-17** |
| AP-P23-15 | The spot source is `AC-D65.15`'s chain and nothing else: **3a** the chart's `_last_chart_price` **only when the charted symbol is SPX** (on any other symbol that value is another instrument's price); **3b** otherwise — tier 3a yields no price: not on SPX, or on SPX with no chart price yet — **exactly one** dedicated SPX spot line, counted and cancelled when the seed completes; **3c** refused/unavailable ⇒ **no** spot, the coarse probe runs region-less and the seed still completes. `MainWindow._symbol_last_prices`, an SPX `TickerSession`'s last close and any engine-level memory tier are **not** spot sources | `AC-D65.15`/A206 name a phase-stable chain: `_symbol_last_prices` and its only writer die in this phase (`AC-D65.13`/`AC-D65.18`/A198), and a session-bar read would be a source the AC does not have — so the plan implements the AC tier for tier rather than inventing intermediate tiers ahead of the line. Spot only picks the probe's starting region, never a quote or a scored value, so a stale chart price cannot corrupt a credit. FI-P23-2 was **fixed in the requirement text 2026-11-17** |
| AP-P23-16 | The one spot line is opened **whenever tier 3a yields no price** — the charted symbol is not SPX, or it is SPX with no chart price yet — regardless of any other price in memory; it is registered in the same registry, counted in `_md_line_count`, cancelled when the seed completes, and a refusal is tolerated (tier 3c). The price it delivers is kept by the engine as the line's own last value (`last_spot_price`), which is a cache of 3b, never a precedence step ahead of it | `AC-D65.15`(3)/A206/Q112: with 3a defined as the chart's own price, "nothing in memory" is exactly "no chart price is usable" — that is when 3b pays its one line, and the AC requires **one**, not zero. Keeping the line open would spend a line on every launch and make 17 the standing footprint rather than the ceiling |
| AP-P23-17 | A pair is scorable/matched only when **both** legs have usable quotes; a leg past the 3 s timeout stays `pending` (cells `—`) rather than being treated as rejected, and the sweep's pair budget counts **scored** pairs only | `AC-D65.15`(ii) excludes partial pairs from scoring; A208 sets 3 s. Counting scored (not attempted) pairs is what makes the 12-pair bound meaningful when a chain has unquoted strikes, and a pending leg is not an error, so it must not consume an error latch |
| AP-P23-18 | `one_tick` is derived from the **Target's level** (`option_tick(T)`), not from a wobbling quote, and the market-rule branch of `AC-D65.4`'s parenthetical is not taken | Attribute-built OPT contracts (`S-P23-7`) carry no `marketRuleIds`, and a per-leg `reqContractDetails` round-trip is the throttled cost R141 warns about; A204 records the 0.05/0.10 rule as owner knowledge, unverified. Deriving from `T` keeps the band stable (a quote-derived band would itself be a hysteresis source) and matches the AC's measurable, which pins `h` by `T`. Both levels are pinned in the suite; a live disagreement is one constant |
| AP-P23-19 | `snap_rung`'s tie (equidistant listed strikes) resolves to the strike **nearer the anchor**, and a rung that cannot form a listed 20-wide pair renders `—` with a once-only shortfall message — it never requests an unlisted strike | DG120/`AC-D65.2`; an unlisted strike is a guaranteed error 200, and dropping the row would break the panel's fixed four-row shape, so `—` is the honest absence |
| AP-P23-20 | The canvas of the acceptance record is `docs/archive/probe_records/d65_paper_tws_acceptance.md` (beside `d48`/`d52`), not the legacy `docs/d48_probe_record.md` path the AC cites | The three existing probe records live in `docs/archive/probe_records/`; pointing the new one at the cited path would put it somewhere no other record lives. The **shape** is what the AC asks for, and the shape is `archive/probe_records`' |
| AP-P23-21 | The post-cutoff state uses a panel-owned constant `16:15 ET` because `services/market_calendar.py` models no option session (RTH close `16:00`, ext `20:00`, verified) | A205 says the calendar wins **if** it models an SPX-option session; today it does not, so the panel carries the constant and the assumption is visible. Adding an option session to the calendar is a later phase's work, not a quiet P23 change |
| AP-P23-22 | The connection badge states the **connection**, not the account: after P23-06 it reads `"● Connected"` (green) while connected and keeps D40's paused wording and the `"● Disconnected"`/`"● Connecting"` texts, with **no** paper/live claim; `conn_badge_text` keeps no account parameter and `_account_id`/`_account_summary` are deleted with their writer | `AC-D65.13`/A194/R143 accept the deletion of the whole account plane, and the badge's two paper/live inputs (`_account_id`, `AccountType`) are exactly that plane; `settings.check_live_port` proves the *port* only — D26.5's own docstring allows a paper account on it — so a port-derived `"Live"` is the hardcoded claim `AC-D26.5` forbade, and no other source exists to name. S-P23-24 decides it, P23-06 executes it, P23-09 records it, so the retirement is a decision on the record rather than a silent regression; it edits no `requirements.md` text and is therefore not a fourth `AC-D65.11` edit |

### Flagged Issues

**None open.** All three conflicts this phase raised are **resolved in the requirement text on
2026-11-17**, and the waves implement the amended criteria verbatim — nothing is carried into
the build as a recommendation, and no Plan assumption replaces a requirement's wording.

**One recorded consequence, not an issue.** `Q110(a)`/A194 deletes the whole account plane, and
the connection badge was its last reader (`_update_conn_badge` reading `_account_summary` and
`_account_id`), so `AC-D26.5`'s paper/live derivation retires with it — decided in
**S-P23-24**, executed in **P23-06**, recorded in **P23-09**'s gate record and stated in
**AP-P23-22**. It is a direct consequence of the deletion the owner authorised (R143's accepted
loss of the account view), not a new requirement and not a silent regression; no source is
invented, and the fail-fast live-port guard — the half of `AC-D26.5` that protects the account —
is untouched.

- **FI-P23-1 — `AC-D65.9`'s default dock width contradicted the shipped D18 default. RESOLVED
  2026-11-17 by the owner** (`A201`, recorded in `docs/plan_notes.md` as `RG-P23-1`
  *addressed*): the right dock's **launch** width becomes the panel's preferred 360 px clamped
  to `[200, right_dock_max_width(chart_area)]`, with the minimum, the 40 % cap, the 400 px
  chart minimum, the D21.13 collapse and the D44 strip unchanged, and exactly two D18
  assertions re-baselined by owner authorisation (`tests/test_dock_widths_d18.py:437`,
  `tests/test_dock_widths_d18_impl.py:328`) — their not-persisted semantics untouched. The
  criterion's ellipsis + tooltip case now has a real meaning (any width below 360 px), and the
  plan's work for it is P23-01's `AC-D65.9` group (S-P23-16).
- **FI-P23-2 — the spot chain named a map this same phase deletes. RESOLVED 2026-11-17 in
  `AC-D65.15`/A206.** The spot source is now the phase-stable three-tier chain: **(3a)** the
  chart's own SPX last price, **only when the charted symbol is SPX** (on any other symbol that
  value is another instrument's price); **(3b)** when 3a is unavailable, **exactly one**
  dedicated SPX spot line, counted (ceiling `16 + 1 = 17`), cancelled when the seed completes;
  **(3c)** when that line is refused or never quotes, **no spot at all** — the coarse probe
  runs region-less and the seed still completes. `_symbol_last_prices` and its only writer
  (`ui/ticker_session.py:562`) are explicitly **not** a spot source and stay deleted
  (`AC-D65.13`/`AC-D65.18`, A198). **AP-P23-15, AP-P23-2 and AP-P23-16 plus P23-05's spot
  group are that text, tier for tier**: the stream suite asserts **zero** spot lines on a chart
  showing SPX and **exactly one** on any other symbol (including a window holding an SPX
  session), and none when the line is refused.
- **FI-P23-3 — the literal `MARKET_DATA` tag would double-subscribe the watchlist. RESOLVED
  2026-11-17 in `AC-D65.14`(ii).** The AC now names the **new `OPTION_LEGS` tag verbatim** —
  "beside `RT_BARS`/`MARKET_DATA`/`S0_TICKS`", added to the include set at the single call site
  (`replay_all(include_types={RT_BARS, S0_TICKS, OPTION_LEGS})`) — and states that option legs
  must **not** be registered as `MARKET_DATA`, whose exclusion under `AC-D22.7.2` "stays as
  written and no behavioural assertion moves". **AP-P23-14 and S-P23-17 are that text**: the
  constant is `OPTION_LEGS` (value `"option_legs"`, matching the module's lowercase tag
  strings), and replay, `rebind` and the watchlist's untouched clear+re-add are unchanged.

The interpretive readings the plan records rather than hides are **AP-P23-11** (the seed's
bounded measurement plus the quasi-convexity basis and its ordered-sweep fallback), **AP-P23-18**
(`one_tick` derived from `T`, because the AC's market-rule branch is not exposed on an
attribute-built contract) and **AP-P23-21** (the 16:15 ET constant, because the calendar models
no option session) — none changes a criterion's outcome and none is a re-scope.

Status: READY_FOR_TASK_MANAGER

## Phase P24 — Option Spreads panel: owner-restated display contract, PCS ordering delta (D66) — drafted 2026-11-18

> Companion: `docs/architecture.md` § *Phase P24* (Relationship to prior phases, Codebase Summary,
> tech-stack decisions, S-P24-1…S-P24-6, frozen interfaces, non-functional approach,
> AR-P24-1…AR-P24-8). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — **Phase P24 (D66), Journey 64, `AC-D66.1`–`AC-D66.8` FINAL**
> (Q114 = reading B, Q115 = `7315/7295`, Q116, Q117 answered 2026-11-18), A213–A219, R154–R159,
> `design_gaps.md` DG124–DG127, `open_questions.md` Q114–Q117.
>
> **Baseline: HEAD `db21672`.** P23/D65 is present, wired and green there (seven `tests/test_d65_*`
> suites, 246 tests) and this phase is a **delta, not a rebuild** — A216/R157 withdraw the
> deleted-implementation premise, and no work item below restores, re-plans or re-accepts any P23
> artefact. The whole diff is: **one production table** (`services/option_ladder.py`), **five
> re-baselined suites**, **one new fence suite**, and the records.
>
> Hard constraints: D1–P23 are read-only inputs; **no order code of any kind**; no change to CCS
> geometry, naming, width, streaming, error states, dock width or the toggle's placement/colour;
> **no row-number column or digit** (Q117); sizes S/M only.

### Revision notes (re-validation against `docs/plan_review_P24.md`, 2026-11-18)

- **RC-P24-1 — the residue suite is inside the delta.** `tests/test_d65_residue.py` is now the **fifth
  re-baselined suite**: P24-03 re-points its `CANONICAL_FIXTURES` PCS entry `7340/7320` → `7325/7305`
  (the corrected table's **anchor pair** — the same pair the ladder suite and the panel fixture carry),
  in the same wave as the panel fixture and after it, so the gate is never left unsatisfiable; the gate
  body, its holder list, `BANNED_EXAMPLES` and `LEGAL_NON_BANNED_PAIR` are untouched. Every "four
  suites" count, the P24-03 diff-scope allowlist, the architecture's Codebase Summary / System
  Components / S-P24-4 / NOT-frozen block, and the `docs/codebase-map.md` P24 note + test-impact row now
  say five.
- **RC-P24-2 — the forbidden-string condition now matches `AC-D66.2`, and the docs stop quoting the
  pairs.** (i) P24-03's exit condition and S-P24-4 are scoped to **positive** use: no committed quotable
  fixture, seed quote plan, probe record or canonical example may present the two **banned** typo pairs
  `AC-D66.2` names, while the shipped **negative guards** that assert them absent
  (`test_d65_residue.py`'s `BANNED_EXAMPLES` and its ban-list self-guard, the ladder suite's
  `_fixture_guard` docstring) are permitted mentions that keep asserting absence for real fixtures and
  must not be deleted. Every retired *expectation* is still named in the wave result. (ii) **The plan and
  architecture now describe those pairs instead of quoting them** — "the 120-wide and the 80-wide
  restatement at strike 7315, as `AC-D66.2` writes them". Reason: the residue gate scans its
  `CONSISTENCY_FILES` for a banned string presented *outside* a claim-marker window (measured: the line
  plus the three before it), so a canonical-doc quotation is only safe while a marker word sits in that
  window — a prose-level trap for every later edit. Describing the pairs removes the dependency on that
  heuristic; the literal strings stay where the gate does **not** scan (`requirements.md`) and in the
  guards themselves. The alternative — widening the gate's "named as forbidden" exemption — was passed
  over: it edits a guard `AC-D65.2`/`AC-D65.13` own, to serve a doc's convenience.
- **RC-P24-3 — `S-P24-3` now has an implementing deliverable.** P24-01's deliverable 3 edits the
  `SpreadRow` docstring (`services/option_ladder.py:84`) to state that `rung` is the 1-based **display
  row** (top→bottom, `1..4`), that the owner's **labels** are specification-only and run `4,3,2,1`
  against those positions on PCS (`1,2,3,4` on CCS), and that nothing renders a digit (Q117); P24-01's
  exit condition asserts the docstring names both terms.

**Unchanged by this revision:** the delta itself (PCS `S3+5, S3, S3−5, S3−10` on rows 1–4 with the Target
on row 2; CCS unchanged with the Target on row 3), `AC-D66.8`'s freeze fence and delta-scope record, the
zero-production-change panel rule, the Frozen Interfaces block, and the D1–P23 read-only premise.

### Traceability (requirement → architecture → wave)

| Requirement / journey | Architecture | Wave |
|---|---|---|
| **AC-D66.2** — THE DELTA: PCS rows `4,3,2,1` with `S3+5, S3, S3−5, S3−10` (Target row 2); CCS unchanged (Target row 3); offsets read from a **per-side** table; no rendered number column | *Relationship* `[revises P23: S-P23-2]`; **S-P24-1** (table), **S-P24-2** (issue order), **S-P24-3** (`rung` = display row), *Data Model* | **P24-01** (table + ladder suite), **P24-02** (engine/stream fixtures), **P24-03** (no-column fence; panel fixture; residue gate) |
| **AC-D66.1** — four rows per side, `SPX MmmDD short/long`, short leg first, CCS `long = short+20` / PCS `long = short−20`, width 20, listed strikes | *Frozen Interfaces* (`format_instrument`, `SPREAD_WIDTH`/`STRIKE_STEP`, `snap_rung`); **S-P24-5** | **P24-01** (canonical names/width), **P24-03** (regex + ISO-rejection fence) |
| **AC-D66.3** — toggle right-aligned in the Target row, red OFF / green ON, both directions, not moved to the title bar | *Frozen Interfaces* (`COLOUR_OFF`/`COLOUR_ON`, `set_toggle_state`); **S-P24-5** | **P24-03** |
| **AC-D66.4** — Target `1.00` default, `0.05 ≤ T ≤ 19.95`, one message + last valid value, never persisted | *Frozen Interfaces* (`DEFAULT_TARGET`, `TARGET_MIN/MAX`, `apply_snapshot`); **S-P24-5** | **P24-03** |
| **AC-D66.5** — updates until OFF, then `—` and every line released; zero orders | *Non-Functional* (line budget/cadence); *Relationship* (engine unchanged) | **P24-02** (stream suite re-baselined, same lifecycle assertions) |
| **AC-D66.6** — `—` exactly in the gap cells, `STALE` on disconnect, one message per cause, recovery | *Non-Functional*; **S-P24-5** | **P24-03** (constant/behaviour assertions; the engine's own cases already exist) |
| **AC-D66.7** — D41–D65 and A186–A212 intact except the five `[revises P23, 2026-11-18 …]` notes; tech-stack section untouched | *Relationship* `[new in P24]` markers; **S-P24-6** | **P24-01** (code comments), **P24-03** (marker grep) |
| **AC-D66.8** — everything else verified-not-changed, plus a diff-scope check | *Relationship*; **S-P24-5** (fence + build-record scope check); *System Components* (`[existing]` engine/panel/window) | **P24-03** |
| **Journey 64** — read the delta on the live panel (header → ON → eight rows → Target edit → step → OFF) | *Relationship*; *Non-Functional* | **P24-02** (row sets + step direction), **P24-03** (header/panel facts) |
| A213/A216/A218/A219, R154–R159, DG125/DG127 | *Relationship*; **S-P24-1**, **S-P24-4**, **S-P24-6** | all three waves |
| DG126 (anchor legibility, non-blocking) | *Flagged Issues* (FI-P24-1) | — (owner decision, out of scope) |

### Phases

Dependency shape: **P24-01 → P24-02**, **P24-01 → P24-03** (02 and 03 are independent of each other and
may run in either order once 01 has landed). 01 is the only wave that touches production code.

#### P24-01 — Per-side offset table + the retired invariant's words — size S

- **Covers:** AC-D66.2 (table half), AC-D66.1 (canonical names), AC-D66.7 (the code-comment half), DG127.
- **Depends on:** nothing (first wave).
- **Files:** `services/option_ladder.py`; `tests/test_d65_option_ladder.py`. Nothing else.
- **Deliverables:**
  1. **Replace the shared literal** (`RUNG_OFFSETS = {1: 10, 2: 5, 3: 0, 4: -5}`, `:60`) with the
     per-side, row-ordered table of S-P24-1 — `{SIDE_CCS: ((1, 10), (2, 5), (3, 0), (4, -5)),
     SIDE_PCS: ((4, 5), (3, 0), (2, -5), (1, -10))}` — and **delete** the old literal (no retained
     copy, no second table under any name; A197/A219).
  2. **`ladder_pairs` reads the side's tuple in tuple order** (never `sorted()`), keeping its signature,
     default side, `_side_key` normalisation, four-pair/row-order output and `long = short ±
     SPREAD_WIDTH` by side. Update its docstring: CCS canonical `ladder_pairs(7425)[2] == (7425, 7445)`;
     PCS canonical `ladder_pairs(7325, SIDE_PCS)[1] == (7325, 7305)` with the anchor on **row 2**.
  3. **Retire the invariant's words in the same edit** (DG127): the module docstring's bullet 1
     (`:6-8`), the `RUNG_OFFSETS` comment (`:58-59`, "Applied identically on both sides — there is no
     mirrored copy of this table") and the `ladder_pairs` docstring's "the same offset table on both
     sides, never a mirrored copy of it" (`:112-115`). Replace with the per-side rule stated once, the
     row order and the anchor row per side. **Also the `SpreadRow` docstring** (`:84`, today only "One
     displayed ladder row -- the engine's unit, the panel's row payload") — S-P24-3's implementing site.
     It must say, in the dataclass's own prose: `rung` is the **1-based display row** (the row's position
     top→bottom, `1..4`, on both sides); the owner's **logical labels** are specification data only and
     run `4,3,2,1` against those positions on PCS (`1,2,3,4` on CCS); and nothing renders a digit or a
     row-number column (Q117). Fields, field names, their order and their types are unchanged.
  4. **Re-baseline the ladder suite**, naming each retired expectation in the result:
     `test_P23_T1_AC1_constants` (new shape; keep `SPREAD_WIDTH == 4 * STRIKE_STEP` and the
     whole-step check per side), `test_P23_T1_AC1_four_pairs_per_side` (per-side offset lists —
     CCS `[10, 5, 0, -5]`, PCS `[5, 0, -5, -10]`), `test_P23_T1_AC1_one_offset_table_on_both_sides`
     **replaced** by a per-side test (CCS provably unchanged; PCS offsets and label order; the anchor
     row per side; **the two forbidden-name strings kept** as the "no second module-level table"
     guard), `test_P23_T1_AC1_canonical_fixtures` (CCS `7425/7445`; PCS `7330/7310, 7325/7305,
     7320/7300, 7315/7295`), `test_P23_T1_AC7_window_legs_eight_per_anchor`'s PCS half (anchor 7325).
     Add one assertion per side that the **row order** and the **label order** are read independently
     (the `sorted()` trap, AR-P24-2).
- **Exit condition:** `pytest tests/test_d65_option_ladder.py` green; the ladder module still imports
  with no Qt module loaded (its existing isolated-interpreter test); `grep -n "both sides"
  services/option_ladder.py` returns nothing; no second offset table exists in production code —
  `RUNG_OFFSETS_PCS` / `PCS_RUNG_OFFSETS` appear nowhere in `services/`, `ui/`, `ibkr/`, `data/`,
  `config/` (the ladder suite's own *negative* string guards necessarily spell them, as the P23 carve-out
  pattern allows) — and the `SpreadRow` docstring names both terms, **"display row"** and **"label"**, so
  S-P24-3 is a measurable rather than a prose intention.
- **Do not:** touch `services/option_spread_engine.py`, `ui/`, `ibkr/`, or any suite other than the two
  named above. In particular leave the ladder suite's formatter and `_fixture_guard` legality examples
  (`:158`, `:171`, `:188`, `:230`, `:246` — all `7340/7320`) alone: they assert the 20-wide /
  short-leg-first rules, not the rung table, and they keep the residue suite's canonical-fixture gate
  green (`CANONICAL_FIXTURES` still holds `7340/7320` until P24-03 re-points it, RC-P24-1), so no wave
  exits red on a suite it did not touch.

#### P24-02 — Engine + stream fixture re-derivation (no production change) — size M

- **Covers:** AC-D66.2 (fixture half), AC-D66.5, Journey 64's row sets and step direction.
- **Depends on:** P24-01.
- **Files:** `tests/test_d65_spread_engine.py`; `tests/test_d65_option_stream.py`. **No production
  file** — if a production edit looks necessary here, stop and escalate: that is the boundary
  AC-D66.8 draws.
- **Deliverables:**
  1. **`mirror_table`/`MIRROR`** (`test_d65_spread_engine.py:86-97`): re-centre the mirror on the
     anchor each fixture drives and extend its profile to **every strike the shifted PCS window
     touches** — the new row-4 short mirrors to the table key at `anchor + 10` and the new row-4 long
     to `anchor + 30`, neither of which P23's model needed (the old window stopped at `anchor + 25`).
     Choose the added values so each fixture's chosen anchor does **not** move, and prove it with the
     existing anchor assertions rather than assuming it. Add an explicit **coverage assertion** per
     fixture: every leg of both committed windows appears in the quote plan before the seed is driven
     (AR-P24-3), so a future table change cannot leave a silently unquoted row.
  2. **Re-derive the PCS expectations** the shared table encoded: the seed's anchor is a **strike** and
     the probe/refine search is strike-based, so the same anchors can still win — the wave **confirms**
     them through the existing anchor assertions rather than assuming they are unchanged, and a fixture
     whose PCS anchor legitimately moves is a recorded re-derivation, not a production defect. The same
     holds for `_step_candidate("PCS", 7330) == 7335` (PCS steps **up**): the mechanics are
     `live ± STRIKE_STEP`, so the direction is unchanged, while the *quotes* that decide it come from
     the re-derived fixture. Every case that reads a PCS **row set** must be re-checked against the new
     table (window legs, kept/cancelled legs on a re-seat, chain-edge cases).
  3. **`test_d65_option_stream.py`**: split `EXPECTED_SHORTS` (`:41`) into `EXPECTED_SHORTS_CCS`
     (unchanged `[7360, 7355, 7350, 7345]` at `SPOT 7350`) and `EXPECTED_SHORTS_PCS`
     (`[7355, 7350, 7345, 7340]`), and use the right list per side at `:338`; move the PCS row-index
     expectations up one (`("PCS", 1, 7350.0)` — the anchor is now row 2, `:1295-1309`); re-derive the
     kept/arriving/cancelled PCS leg sets at the re-anchor case (`:392-445`, anchor `7350 → 7355`);
     keep every lifecycle/budget/zero-order assertion untouched (AC-D66.5).
- **Exit condition:** `pytest tests/test_d65_spread_engine.py tests/test_d65_option_stream.py` green,
  then **all seven** `tests/test_d65_*` suites green in one run; `git diff --name-only` shows no
  production file from this wave; the result names every retired P23 PCS expectation (R156/A201). The
  residue suite is green here because P24-01 left the ladder suite's `7340/7320` legality examples in
  place and P24-03 has not yet moved the panel fixture — the gate flips in the same wave as that fixture
  (AP-P24-9), never between waves.
- **Do not:** weaken a case to make it pass (e.g. dropping the coverage assertion, or asserting `>= 4`
  rows where `== 4`/exact names were asserted); re-derive by deleting assertions.

#### P24-03 — Restated-contract fence, panel fixture, delta record — size S

- **Covers:** AC-D66.1, AC-D66.3–AC-D66.8, Journey 64's header/panel facts, DG125 (do-not-edit), Q116/Q117.
- **Depends on:** P24-01 (02 not required).
- **Files:** `tests/test_d65_option_panel.py`; `tests/test_d65_residue.py` (its canonical-fixture
  constant and comment only); a new fence suite in `tests/`; the wave's own result record. **No
  production file.**
- **Deliverables:**
  1. **Panel fixture re-baseline:** `pcs_name` / its row (`test_d65_option_panel.py:484-492`, `:522`)
     becomes the corrected PCS **anchor pair** `SPX Nov17 7325/7305` — pinned, not "`7330/7310` as the
     first row": the residue gate (deliverable 2) and the ladder suite's canonical test must name one and
     the same pair, and the anchor pair is the P23 precedent — so the suite stops re-encoding the retired
     model (AR-P24-5).
  2. **Residue gate re-point (RC-P24-1):** in `tests/test_d65_residue.py`, change `CANONICAL_FIXTURES`
     (`:273`) from `("7425/7445", "7340/7320")` to `("7425/7445", "7325/7305")` and update its comment
     (`:265-267`) to say the PCS canonical is `AC-D66.2`'s **anchor** pair at `S3 = 7325`. **Do not**
     change the gate body (`:2536-2573`): its holder list (`docs/plan.md`, `docs/architecture.md`, the
     ladder suite, the panel suite) and its intent — each canonical fixture must still exist in every
     named file — stay exactly as they are. `BANNED_EXAMPLES` (`:274`) and `LEGAL_NON_BANNED_PAIR`
     (`:275`) stay intact: they are the negative guards RC-P24-2 keeps. This step **must land in this
     wave, after deliverable 1** — the gate can only pass once the panel suite carries the new pair, and
     moving the constant before the fixture would redden all seven suites.
  3. **The fence suite** (S-P24-5), one assertion per named artefact: `DEFAULT_TARGET == 1.00`,
     `TARGET_MIN`/`TARGET_MAX`, `COLOUR_OFF`/`COLOUR_ON` and `SPREAD_WIDTH == 20`; the eight rendered
     names match `AC-D66.1`'s regex verbatim, `^SPX (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:[1-9]|[12]\d|3[01]) \d+(?:\.\d+)?/\d+(?:\.\d+)?$`,
     with an ISO-dated and a zero-padded-day name **rejected**; four rows per side with the PCS anchor
     on **row 2** and the CCS anchor on **row 3**; **no** row-number column and no digit in the
     instrument cell (Q117); the toggle's alignment relative to the Target field and the panel's content
     edge, its `spread_state` dynamic property reading `on`/`off`, and an ON→OFF→ON sequence
     (Q116/AC-D66.3); the Target's accepted/rejected cases (the never-persisted restart case stays in
     the existing panel suite, unchanged); the `[revises P23, 2026-11-18` notes present at their **five named sites**
     (AC-D65.2, A187, A212, the P23 glossary's anchor entry, R142) — asserted **by site**, not by raw
     occurrence count, because the P24 header sentence also names them — plus the retired phrases
     absent from the ladder module (AC-D66.7).
  4. **Delta-scope record** (AC-D66.8, S-P24-5): the wave records `git diff --name-only db21672` and
     requires it to be a subset of `services/option_ladder.py` + the **five** re-baselined suites
     (`test_d65_option_ladder`, `test_d65_spread_engine`, `test_d65_option_stream`, `test_d65_option_panel`,
     `test_d65_residue`) + the new fence suite + `docs/` (the phase's own records). Recorded as evidence
     in the result, **not** as a hash-pinned test.
- **Exit condition:** all seven `tests/test_d65_*` suites **plus** the fence suite green in one run; the
  recorded diff-scope listing matches the allowlist exactly; no production file changed outside
  `services/option_ladder.py`; the two **banned** typo pairs are absent from every **positive** fixture —
  no committed quotable fixture, seed quote plan, probe record or canonical example presents them, and
  no doc quotes them either (they are described, not spelled, in this phase's plan/architecture text,
  which the residue gate scans) — while the shipped **negative guards** that assert them absent
  (`tests/test_d65_residue.py`'s `BANNED_EXAMPLES` and its ban-list self-guard, the ladder suite's
  `_fixture_guard` docstring) are permitted mentions and must stay; every retired expectation is named
  in the wave result (A201/R156).
- **Do not:** edit `format_instrument`/`_format_expiry` (DG125), the panel, the engine, or
  `docs/requirements/*` (the analyst's notes are input, not build output); do not touch the residue
  gate's body, its holder list, `BANNED_EXAMPLES` or `LEGAL_NON_BANNED_PAIR` (only its PCS canonical
  entry and comment change), and do not delete any negative guard that names a banned typo pair.

### Assumptions

- **AP-P24-1 — baseline and diff.** The build starts from HEAD `db21672` (or a descendant that changes
  nothing this phase reads). The delta is `services/option_ladder.py` + **five** test suites
  (`test_d65_option_ladder`, `test_d65_spread_engine`, `test_d65_option_stream`, `test_d65_option_panel`,
  `test_d65_residue`) + one new suite; the phase's docs are excluded from AC-D66.8's "production file"
  wording and are listed in the record explicitly so the scope check cannot read as ambiguous.
- **AP-P24-2 — the constant keeps its name.** `RUNG_OFFSETS` stays the single module-level offset
  table and changes shape (per side, row-ordered). No second table, no per-call special case (A219).
- **AP-P24-3 — canonical fixtures.** PCS examples use the owner's corrected table at `S3 = 7325`;
  CCS uses `S3 = 7425`. The **canonical** PCS pair is that table's **anchor** pair `7325/7305` — the one
  pair the ladder suite's canonical test, the panel fixture and the residue gate all name (P23's
  precedent made `7340/7320`, its own anchor pair, canonical). The stream suite's own anchors (`SPOT
  7350`, re-anchor to `7355`) are its fixtures' business: the wave derives the per-side row lists from
  the engine and asserts the **anchor row** explicitly, and the lists written here are the expected
  starting point, not a substitute for running the suite.
- **AP-P24-4 — the window issue order does not change.** `_WINDOW_ISSUE_ORDER` stays a single fixed
  index order; on PCS the anchor pair is issued second rather than first (one pacing slot, no criterion
  observes it; S-P24-2).
- **AP-P24-5 — `SpreadRow.rung` keeps its name and gains a documented meaning** (1-based display row);
  the owner's logical labels live only in the table and in test names (Q117/S-P24-3).
- **AP-P24-6 — no live-TWS run this phase.** AC-D66.8 is a suite-level fence; AC-D65.19's acceptance
  record stands as delivered, and ESC-123's stale commit hash inside that record is BUILD-routed and
  out of P24's scope.
- **AP-P24-7 — the requirements record is input.** The five `[revises P23, 2026-11-18 …]` notes and
  A213–A219 already exist in `requirements.md`; the build greps them, never rewrites them (AC-D66.7).
- **AP-P24-8 — no user-doc change is due.** `USAGE.md`'s Option Spreads section (items 1–6) describes the
  panel's behaviour and never states a rung offset or a row ordering (verified), so the delta makes
  nothing there stale; `docs/pending_doc_sync.md` does not exist, so there is nothing to fold. If the
  owner later wants the ordering documented for users, that is a separate doc request, not a silent
  P24 edit — AC-D66.2's labels are deliberately unrendered.
- **AP-P24-9 — the residue gate moves in one step, not two.** `test_d65_residue.py`'s
  `CANONICAL_FIXTURES` and the panel suite's snapshot fixture are edited in the same wave (P24-03, panel
  fixture first), and P24-01/P24-02 leave the ladder suite's `7340/7320` legality examples in place, so
  the old gate holds until the new one takes over. No wave may exit with the residue suite red, and no
  wave before P24-03 edits the residue constant.

### Flagged Issues

- **FI-P24-1 — DG126: the two side-by-side tables anchor on different rows, with no numbers to say so
  (non-blocking, owner decision).** After this delta the PCS Target sits on row 2 and the CCS Target on
  row 3, while Q117 forbids any rendered digit — so the asymmetry is decided but not legible. No
  criterion requires a marker and P24's non-goals exclude UI changes, so nothing in this plan adds one.
  Suggested direction if the owner wants it: a non-numeric anchor marker (the D21 active-row tone, or a
  `◀ Target` suffix in the instrument cell) as a separate micro-request — **not** a numbering column.
- **FI-P24-2 — ESC-125 re-verified clean while drafting (PLAN-routed, should-fix, `open`).** The
  canonical docs no longer describe the superseded paper-TWS acceptance or the deleted window-walk API:
  the only surviving `scan_anchor`/`next_step` occurrences are **negative** statements in historical
  revision notes (`docs/plan.md` P23 pass-3, `docs/architecture.md`'s P23 as-built note: "there is
  **no** `scan_anchor`/`next_step` helper"), and no `paper-TWS`/`7497` text remains in
  `docs/plan.md` or `docs/architecture.md`. Nothing to re-plan; recorded so the Validator can close it
  rather than re-derive it. (This section was planned against what is there, not against an assumption
  that it was fixed.)
- **FI-P24-3 — the architecture-doc revision is Plan's judgement, not an AC (non-blocking).** AC-D66.7
  scopes the recorded revision to `requirements.md`; three normative sentences in `docs/architecture.md`
  (the P23 pass-5 summary's item J, the P23 System Components entry, S-P23-2's row) would otherwise
  contradict the shipped rule, which ESC-066/ESC-069 treated as a defect. S-P24-6 therefore appends
  one-line supersession markers there **without** rewriting a P23 sentence or touching P23's
  `READY_FOR_TASK_MANAGER` status. Flagged so the Validator can confirm the treatment rather than
  discover it.

Status: READY_FOR_TASK_MANAGER

## Phase P25 — Silent wrong data on the chart: forming week/month candle, stolen live feed, out-of-order flush, whitespace rows (D67–D70) — drafted 2026-11-19

> **Revision notes — 2026-11-19, against `docs/plan_review_P25.md` (CHANGES_REQUIRED, all six PLAN-owned).**
>
> - **RC-P25-1 (D70's page half).** The premise was false: `chart.js::upsertRow` routes a candle upsert
>   through `envelope.js::mergeRows`, which keeps a `None`-close row, so `lwSnapshot()` retained it. Fixed by
>   changing the page's fold, not the criterion: `mergeRows` now applies the whitespace rule in both branches
>   and `upsertRow` sends `{time}` only for a whitespace row; `envelope.js`, `chart.js`, `envelope.test.js`
>   are added to **P25-03**'s file set, and the parity case runs the real `lwApplyOps`/`lwSnapshot()` over both
>   the update fixture and the `set_bars` fixture. AC-D70.1 is satisfied as written ("no row for that
>   timestamp" **and** "equals the page's merge"); restating it was not Plan's to do. `S-P25-6`, the
>   Codebase Summary rows, the D70 tech-stack row and P25-03's do-not list are aligned (see
>   `docs/architecture.md` § *Phase P25* revision notes).
> - **RC-P25-2 (`_wall_now` position).** Named exactly: the one line lands at **session creation**
>   (`MainWindow.get_or_create_session`, `ui/main_window.py:1077`) as a late-bound
>   `lambda: self._now_ts()`, which precedes the cold-restore path's `set_bars` (`:1220`) and the primary
>   load's (`:3173`) — adoption therefore sees the same clock the cached `set_bars` and the prime see, and
>   `test_d48_mode_parity.py`'s patched `_now_ts` (`:171`) is honoured.
> - **RC-P25-3 (`push`).** Resolved as "observable contract unchanged, one state field newly written": `push`
>   is the only place an `_AggState` is created, so it records `first_ts = ts` there; P25-01 item 3, System
>   Components, the frozen bullet and the map note use `prime_aggregator`'s wording, and AC-D67.2's partial
>   fixture drives `on_historical_bar` → `push`.
> - **RC-P25-4 (replay guard).** Adoption **preserves** `_last_pushed_ts` (P25-01 item 3, `S-P25-1`, System
>   Components, AR-P25-1, Non-Functional) with the safety argument, and new suite case (h) asserts a
>   redelivered 5-second bar is not re-counted into a base-derived candle.
> - **RC-P25-5 (marker rollover).** One rule replaces the ambiguous sentence: the view drives the page's
>   marker toward `(forming ts, forming.partial)` on every emitting tick — including `update_live_bar`'s
>   `new_period` branch — and inside `set_series`; page semantics (`partial: true` moves the marker,
>   `false` clears only on a match, a time absent from the rows is not marked) are stated. New suite case
>   (g) covers the rollover in both directions; the node case covers the move.
> - **RC-P25-6 (fence literals).** `TIMEFRAME_SECONDS` → **ten** keys; the bridge constants are cited as
>   **module-level** (`ui.lwc_bridge.ENVELOPE_VERSION` / `.COALESCE_MS` / `.LIVE_OPS`); the defect headings
>   are `#### D67`–`#### D70`; the `set_bars` frozen bullet now mirrors `prime_aggregator`'s "signature and
>   emit contract frozen; behaviour changes". No other fence entry changed. One ripple found while fixing
>   this: `### D41`–`### D66` is AC-D70.3's shorthand, not the record's literal shape (`### D41`–`### D53`
>   are defect headings; `D54`–`D66` live in `## Phase P<n>` headers and `#### Journey` titles), so the
>   fence's assertion is presence per id in a heading — P25-04 item 1 says so.
>
> Companion: `docs/architecture.md` § *Phase P25* (Relationship to prior phases, Codebase Summary,
> tech-stack decisions, S-P25-1…S-P25-6, frozen interfaces, Non-Functional Approach, AR-P25-1…AR-P25-8,
> the quick-lane fold). Requirements input: `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`) — **Phase P25 (D67–D70), Journeys 65–67, `AC-D67.1`–`AC-D70.3` FINAL**,
> A220–A224, R160–R164, gates **G1**/**G2** (owner-run), `design_gaps.md` DG129, `open_questions.md` Q119
> (open, non-blocking; default adopted verbatim).
>
> **Baseline: HEAD `94d6119`**, tree clean, P24/D66 shipped. The work is four independent seams, not a
> rebuild: **one data-plane change** (the forming period candle), **one pop-out release decision**, **one
> emission-order change plus one whitespace rule applied on both sides**, and **the records**. Hard constraints: D1–P24
> read-only; **no production behaviour outside these four defects**; no new production module,
> dependency, wire version or migration; sizes S/M only; the two live checks are **named gates**, never
> suite gates.

### Traceability (requirement → architecture → wave)

| Requirement / journey | Architecture | Wave |
|---|---|---|
| **AC-D67.1** — the forming week/month candle is the period's real aggregation when the data exists (open = first in-period open, high/low = extremes, close = latest, volume = the sum), and a period that starts today is complete and unmarked | **S-P25-1** (period base), **S-P25-3** (coverage rule), *Data Model* (`_AggState.first_ts`, `Bar.partial`) | **P25-01** |
| **AC-D67.2** — a candle that cannot cover the period carries the partial marker **and** its values are exactly the aggregate of the bars actually used; no marker on a complete candle | **S-P25-2** (one series marker, one directive op), **S-P25-3** (the rule), *Non-Functional* (one cue, one surface), AR-P25-1/2 | **P25-01** |
| **AC-D67.3** — every priming request is a pair TWS accepts (the `1 min` arm never exceeds `1 D`) and a rejected pair is never retried as-is | **S-P25-1** (no request at all when a base exists; the existing clamp otherwise), *Integration Points*, *Frozen Interfaces* (`prime_aggregator`) | **P25-01** |
| **AC-D68.1 / AC-D68.2** — a deferred pop-out's close leaves the main feed live (holder count back to its pre-open value, no unsubscribe); an acquired hold is released exactly once; two pop-outs in either order | **S-P25-4** (pop-out-local latch; session API frozen by the P13 fence) | **P25-02** |
| **AC-D69.1 / AC-D69.2** — arrival order preserved (`update_bar`→`set_bars` leaves exactly the replace; `set_bars`→`update_bar` applies the update last); every surviving op emitted exactly once, one replace per series per envelope | **S-P25-5** (sequence-stamped staging, supersession, directives last) | **P25-03** |
| **AC-D70.1 / AC-D70.2** — a `None`-close row is never a bar in either branch **on either side**; the reconstruction equals the page's own bar series | **S-P25-6** (one rule in `apply_ops_to_bars` **and** in the page's `mergeRows`; node parity against the real `lwApplyOps` + `lwSnapshot()`) | **P25-03** |
| **AC-D70.3** — D41–D66, Journeys 1–64, `AC-D1.1`–`AC-D66.8`, A1–A219, R1–R159, the marker sentence and Current Tech Stack unchanged and present | *Relationship to prior phases* (`[existing]`, read-only inputs); **P25-04**'s fence | **P25-04** |
| **Journey 65** — read a weekly chart mid-week and trust the forming candle (cache-covers and cannot-cover legs) | S-P25-1, S-P25-2, S-P25-3 | **P25-01**; live arm **G1** (owner-run) |
| **Journey 66** — close a pacing-deferred pop-out and watch the main chart keep ticking | S-P25-4 | **P25-02**; live arm **G2** (owner-run) |
| **Journey 67** — one coalesce window, one stale update, one rebuild | S-P25-5, S-P25-6 | **P25-03** |
| A220/A221/A222/A223/A224, DG129, Q119 | S-P25-1…S-P25-6 (each names the assumption it implements) | 01/02/03 |
| R160–R164 | *Architecture Risks* AR-P25-1…AR-P25-8 | all waves |

### Phases

Dependency shape: **P25-01 → P25-03** (same file, sequential), **P25-01 → P25-04** and
**P25-03 → P25-04** (the record wave last). **P25-02 touches no file P25-01 or P25-03 touches** and may run
in parallel with either. Exactly one wave (P25-01) changes user-visible data behaviour.

#### P25-01 — D67: the forming `1 week` / `1 month` candle gets a real base and an honest marker — size M

- **Covers:** AC-D67.1, AC-D67.2, AC-D67.3, Journey 65 (offscreen legs), A220/A221/A222, DG129, Q119's default.
- **Depends on:** nothing.
- **Files:** `data/models.py`, `data/bar_aggregator.py`, `services/market_calendar.py`,
  `ui/ticker_session.py`, `ui/lwc_view.py`, `ui/lwc_bridge.py` (op acceptance + reconstruction only —
  **not** the emission order, which P25-03 owns), `chart_assets/lwc/envelope.js`, `chart_assets/lwc/chart.js`,
  `chart_assets/lwc/chart.test.js`, `chart_assets/lwc/envelope.test.js`, `ui/main_window.py` (**one line**
  only: the `_wall_now` wiring at session creation, `get_or_create_session`), `tests/test_d48_mode_parity.py`
  (**its docstring only**), a new `tests/test_d67_forming_candle.py`.
- **Deliverables, in this order** (the page must accept the op before anything emits it — an unknown op
  rejects the whole envelope, AR-P25-3):
  1. **Page acceptance + marker (S-P25-2).** `chart_assets/lwc/envelope.js::validateOp` accepts
     `{"op": "set_partial", "ts": <int>, "partial": <bool>}` as a directive (no `series`, no `cols`), and
     `envelope.test.js` asserts it validates and that a missing/non-int `ts` or non-bool `partial` is
     rejected. `chart_assets/lwc/chart.js` lifts the directive in `applyOps` **before** `describeOp`
     (mirroring the `set_visible_range` branch), keeps the marked time in closure state, and re-applies one
     `createSeriesMarkers(candleSeries, [...])` entry after every rows application (`applyRows`,
     `upsertRow`, and after a replay); `partial: false` clears it; one named colour constant distinct from
     the up/down candle colours; a guarded call (`typeof createSeriesMarkers === "function"`) so an older
     page cannot throw. `chart.test.js`: the fake LWC gains `createSeriesMarkers`/`setMarkers`; one case
     asserts the marker appears for the marked bar, survives a `set_bars`, is cleared by
     `partial: false`, **moves** when a `partial: true` arrives for a second `ts`, and is absent when no
     directive arrived.
  2. **Bridge acceptance (S-P25-2's transport half).** `ui/lwc_bridge.py::_check_op_shape` accepts the
     directive (int `ts`, bool `partial`, no `series`/`cols`); `apply_ops_to_bars` ignores it explicitly
     (it carries no `series`, so the reconstruction is unchanged — say so in the docstring). **Do not**
     restructure `_stage`/`flush` here.
  3. **Data plane (S-P25-1).** `data/models.py`: `Bar.partial: bool = field(default=False, compare=False,
     repr=False)` with a comment that it is transient, presentation-only and never persisted.
     `data/bar_aggregator.py`: `_AggState.first_ts` — written in `push` **at the one place a state is
     created** (`first_ts = ts`), because that is the only place a first bar's `ts` exists; `push`'s
     observable contract (the `ts <= _last_pushed_ts` skip, the bucket-change rollover with
     `is_new_candle=True`, the high/low/close/volume merge, the callback) is **unchanged** — the
     `prime_aggregator` form: contract frozen, one state field newly written;
     `adopt_period_base(bar)` (sets the open candle from one rendered period row, `first_ts =
     period_start`, records that the state is base-derived, and **leaves `_last_pushed_ts` untouched** —
     `S-P25-1` and AR-P25-1 carry the safety argument); `drop_period_base()` (clears a base-derived state
     only); `covering_since` property.
     `period_start`, `current_bar`, the bucket helpers and `TIMEFRAME_SECONDS` are byte-identical.
     `services/market_calendar.py`: `first_session_open(period_start, now_ts, ext_hours) -> int | None`
     (the first ET session open in `[period_start, now_ts]`, holiday-aware via `trading_days`, `None`
     before any session opens) — `session_windows` untouched.
  4. **Session wiring (S-P25-1 + S-P25-3).** `ui/ticker_session.py`: a `_wall_now` seam (callable, default
     `time.time`, documented as the test clock); `set_bars` adopts the last bar as the period base for
     `1 week` / `1 month` when its bucket equals the current period under `_wall_now()`, else calls
     `drop_period_base()`; `prime_aggregator` returns `False` without issuing a request when a current-period
     base exists (both the fresh and the `retrying=True` entry, so a retry can never resurrect the request),
     and keeps the existing `1 min` / `[60 S, 1 D]` clamp otherwise; the **Per-span priming table** gains
     the base row and keeps the `'1 week'` / `'1 month'` tokens (`tests/test_d48_gate.py` greps them within
     2,000 characters of the anchor); `_on_aggregated_bar` stamps `partial` on the forming bar it emits
     (`agg.covering_since > first_session_open(...)` for the two calendar timeframes, `False` everywhere
     else), using `_wave_extended_hours` for the mode. `ui/main_window.py`: **one line at session
     creation** — in `get_or_create_session` (`:1077`), immediately after `TickerSession(key, self)`:
     `session._wall_now = lambda: self._now_ts()` (late-bound, so a test that replaces
     `MainWindow._now_ts` is honoured). It must sit **before the first `set_bars`**, because adoption
     reads the clock *inside* `set_bars`: the cold-restore path (`prepare_load` `:1218` → `set_bars`
     `:1220`) and the primary load (`prepare_load` `:3162` → `set_bars` `:3173`) both run after session
     creation, so this one line covers every path and nothing else in the window changes.
     `tests/test_d48_mode_parity.py`: restate the "prime carve-out" docstring sentence (a week/month
     load with a seeded current-period bar now primes **nothing**); its assertions do not change.
  5. **View lemma — one marker rule (S-P25-2/S-P25-3).** `ui/lwc_view.py` keeps `_partial_ts: int | None`
     and always drives the page's single marker toward the forming bar's state: `target = bar.ts if
     bar.partial else None`; if `target != _partial_ts`, emit `set_partial {ts: target, partial: true}`
     when the target is a `ts`, else `set_partial {ts: _partial_ts, partial: false}` when a marker was
     set, then store `target`. The rule runs in `update_live_bar` on **every** emitting tick — including
     its `new_period` branch, which is the rollover edge: the just-completed week/month candle loses its
     marker and the new forming bar is marked only when it is itself partial — and in `set_series`,
     applied to the replacement's last row (`rows[-1]`), so a full replace re-states the marker in the
     same op batch instead of leaving it on a candle that is no longer the forming one. The page
     semantics the rule relies on are part of the deliverable: one marked time; `partial: true`
     **moves** it; `partial: false` clears it only when `ts` equals the marked time; a marked time that
     is not in the current rows is not applied. `set_series`/`update_bars`/`update_last_bar`/
     `update_live_bar` signatures unchanged.
  6. **The suite** `tests/test_d67_forming_candle.py`: per timeframe (`1 week`, `1 month`) — (a) a cached
     current-period row built as the aggregate of an explicit component list: the forming bar's
     open/high/low/close/volume equal that aggregate, and no marker op is emitted; (b) an empty/pruned cache
     with an injected prime (fed through `TickerSession.on_historical_bar` → `BarAggregator.push`, the real
     write path that records `first_ts`): the marker is emitted for the forming `ts` and the values equal
     the aggregate of exactly the injected bars; (c) "the period begins today": full values, no marker;
     (d) a live bar in the next bucket appends a new bar and never duplicates the completed one; (e)
     `AC-D67.3`: the `(bar_size, duration)` tuples the test observes are inside the accepted set,
     week/month with a base issue no prime, and a `321` on a prime is not re-issued with the same pair;
     (f) the view→bridge path carries exactly one `set_partial` after a full replace, for the replacement's
     last row; (g) **rollover**: with the forming candle marked, a live bar in the next bucket emits exactly
     one `set_partial` naming the new `ts` (the completed candle is not the marked time), and when the new
     bucket's forming bar is complete the envelope carries `set_partial {old_ts, partial: false}` and no
     mark remains; (h) **the replay guard survives adoption**: push a live 5-second bar, adopt a
     current-period base via `set_bars`, then re-push the same `ts` — the base-derived volume is unchanged
     (no re-count) while a genuinely newer `ts` still merges into it.
- **Exit condition:** the new suite green **and** `tests/test_d48_gate.py tests/test_d48_mode_parity.py
  tests/test_d48_data_plane.py tests/test_d27_aggregator_priming.py tests/test_bar_aggregator.py
  tests/test_p7_w4_streaming.py tests/test_lwc_bridge.py tests/test_lwc_time_parity.py
  tests/test_lwc_page_wiring.py` green; `node --test chart_assets/lwc/` green; `git diff --name-only` is a
  subset of the file list above (nothing else, and in particular no `services/backfill_service.py`, no
  `ibkr/**`, no `data/bar_cache.py`).
- **Do not:** touch `TickerSession.ensure_rt_subscribed` / `release_rt` / `_rt_holders` or
  `ui/popout_window.py` (P25-02 owns those); restructure `_stage`/`flush` (P25-03 owns it); change
  `ENVELOPE_VERSION`, `COALESCE_MS`, `LIVE_OPS`, `KNOWN_SERIES`, `CHANNELS`, `mergeRows` (P25-03 owns the
  fold's whitespace rule), the `set_visible_range` contract, `BarCache` (schema, columns, mode key), the
  pacing manager, the wave's request shapes, or any anchor/indicator surface; add a request for
  week/month (the phase removes one); weaken a D48 case (its assertions stay; only one docstring sentence
  is restated).

#### P25-02 — D68: a pop-out releases at most the hold it acquired — size S

- **Covers:** AC-D68.1, AC-D68.2, Journey 66 (offscreen legs), A223, R162.
- **Depends on:** nothing (no shared file with 01 or 03).
- **Files:** `ui/popout_window.py`, a new `tests/test_d68_hold_balance.py`.
- **Deliverables:**
  1. **The latch (S-P25-4).** `PopoutChartWindow.attach` stores `self._hold_acquired` (True only on the
     `else` branch where `ensure_rt_subscribed()` returned) and its unwind reads that attribute instead of
     the local; `_retry_rt_subscribe` sets it on success and keeps its existing "was it closed?" membership
     guard; `detach` sets `self._closed = True` **first**, then releases **only** when `_hold_acquired`,
     clearing it; `_retry_rt_subscribe` returns immediately when `_closed` (so a retry that fires after
     close acquires nothing) in addition to the membership guard. Comment each write site with `D68` and
     state the P13 fence reason (`release_rt` takes no owner) so the next reader cannot "improve" it into an
     owner-keyed API.
  2. **The suite** `tests/test_d68_hold_balance.py` — a fake realtime manager recording subscribes and
     unsubscribes per reqId, a real `TickerSession`, and a pacing-limited `ensure_rt_subscribed` that raises
     `PacingExceeded` on the pop-out's first call. Cases: (a) deferred pop-out closed before its retry — the
     session's holder count returns to its pre-open value and **no unsubscribe** is recorded for the main
     reqId; (b) acquired pop-out closed — exactly **one** release; (c) two pop-outs, one deferred, closed in
     both orders — the count returns to its pre-open value and one-open leaves one; (d) the main chart closed
     first — the pop-out's hold keeps the feed alive until it closes too; (e) a retry that fires after close
     acquires nothing (count and subscribe log asserted); (f) `detach` twice is a no-op release-wise.
- **Exit condition:** the new suite green **and** `tests/test_p13_hold_fix.py tests/test_p13_attach.py
  tests/test_p13_hold_probe.py tests/test_d24_popouts.py tests/test_d24_9_popout_persistence.py
  tests/test_lwc_popouts.py` green; `git diff --name-only` ⊆ {`ui/popout_window.py`, the new suite}.
- **Do not:** edit `ui/ticker_session.py` at all; add `acquire_rt` / `release_rt_for` / `_rt_owners` or any
  owner argument; change `attach`/`detach`/`closeEvent` signatures; touch the pop-out's persisted record,
  geometry, MAX_POPOUTS cap, memory accounting or signal wiring; re-open D49.5.

#### P25-03 — D69 + D70: arrival-ordered emission and one whitespace rule — size S

- **Covers:** AC-D69.1, AC-D69.2, AC-D70.1, AC-D70.2, Journey 67, A224, R163, R164.
- **Depends on:** P25-01 (same file; the directive acceptance and the marker op must already exist).
- **Files:** `ui/lwc_bridge.py`, `chart_assets/lwc/envelope.js` (the page's fold), `chart_assets/lwc/chart.js`
  (the upsert display branch), `chart_assets/lwc/envelope.test.js` (a unit case for the fold),
  `chart_assets/lwc/chart.test.js` (the parity case through the real `lwApplyOps`/`lwSnapshot()`), a new
  `tests/test_d69_d70_bridge_contract.py`.
- **Deliverables:**
  1. **Sequence-stamped staging (S-P25-5).** `_stage` assigns `seq` from a monotonic counter and stores
     `(seq, op)` in `_outbox` / `_live_buf` (the coalescing key and last-tick-wins behaviour are unchanged,
     and a coalesce keeps the newest `seq`). `flush` builds one list from both buffers, applies the
     supersession rule (**per series: keep only the last full replace — `set_bars` / `set_volume` / `clear` —
     and drop that series' ops with a smaller `seq`**), emits survivors in ascending `seq`, then appends the
     non-series directives (`set_visible_range`, `set_partial`) in arrival order. `_op_log`, `replay_log`,
     `handle_page_ready` and the counters are untouched (arrival order, full fidelity, no new key).
  2. **One whitespace rule, both sides (S-P25-6).** Python: `apply_ops_to_bars`'s `update_bar` branch, when
     the row's `close` is `None`, **removes** that `ts` if present and writes nothing; the `set_bars` branch
     keeps its `if c is not None` filter; the docstring states one rule for both branches and names the
     page's bar series as the reference. Page: `chart_assets/lwc/envelope.js::mergeRows` applies the same
     rule — the `set_bars`/`set_volume` branch **skips** a whitespace row and the `update_bar` branch
     **deletes** that time (the op's `series` picks the test: candles `open`/`close` null, volume `value`
     null) — and `chart_assets/lwc/chart.js::upsertRow` sends `{time}` only to the library for a whitespace
     row, never a null-valued point. `applyRows`, `seriesRows` and `barRows` are unchanged, so the gap-slot
     display contract (AC-D21.4.4) is untouched; `lwSnapshot()` is unchanged and now agrees with the Python
     reconstruction by construction.
  3. **The suite** `tests/test_d69_d70_bridge_contract.py`: AC-D69.1 in both orders (headless bridge, no
     event loop, explicit `flush`); AC-D69.2 (multiplicity per envelope, one replace per series, the older
     replace dropped); Journey 67's edges (several series in one window; `clear` then `update_bar`; an
     update whose `ts` is absent from the later `set_bars`; an empty flush returns `None`); AC-D70.2 (the
     same whitespace row through `set_bars` and through `update_bar` — both exclude it, one shared expected
     series) and AC-D70.1's parity half driven through `node --test` (`lwApplyOps` + `window.lwSnapshot()`
     over the same op list, asserted equal to `apply_ops_to_bars`) — run over **both** the whitespace
     `update_bar` fixture and the whitespace-row `set_bars` fixture, so the page's fold, not just the
     reconstructor, is what the parity proves. `envelope.test.js` adds the fold's own unit case (a
     whitespace row skipped on replace, deleted on upsert, replayed twice identically); the parity case in
     `chart.test.js` rides the harness P25-01 already extended.
- **Exit condition:** the new suite green, `node --test chart_assets/lwc/` green, **and** the
  envelope-content suites green: `tests/test_lwc_bridge.py tests/test_lwc_time_parity.py
  tests/test_lwc_page_wiring.py tests/test_lwc_drawings.py tests/test_lwc_alarms.py
  tests/test_p7_w1_coalesce.py tests/test_p7_w4_streaming.py tests/test_d57_joint.py tests/test_d57_framing.py
  tests/test_d57_chevron.py tests/test_d60_away_landing.py tests/test_d60_follow_offset.py
  tests/test_d63_crosshair_free.py tests/test_d21_flash_lifetime.py`; `git diff --name-only` ⊆ the named
  files; the result states explicitly that **no** pre-existing expectation was re-baselined (if one must be,
  the wave stops and escalates to Plan).
- **Do not:** change `ENVELOPE_VERSION`, `COALESCE_MS`, `LIVE_OPS`, the op shapes or the two-key envelope;
  reorder `_op_log` (replay keeps arrival order); add or rename a counter; touch `seriesRows`, `barRows`,
  `mergeRows`'s signature or its handling of real (non-whitespace) rows, the viewport/landing logic
  (`applyOps`' range block), the channels, or the pacing/replay paths.

#### P25-04 — records and the phase fence — size S

- **Covers:** AC-D70.3, the phase's own evidence record.
- **Depends on:** P25-01, P25-02, P25-03.
- **Files:** a new `tests/test_p25_fence.py`; `docs/` records. **No production file.**
- **Deliverables:**
  1. **The fence suite** `tests/test_p25_fence.py`, one assertion per named artefact: `requirements.md`
     still carries `This is an existing repository.`, the `D41`–`D66` record, P25's own `#### D67`–`#### D70`
     entries, `Journey 65`–`Journey 67`, `AC-D1.1`–`AC-D66.8` and `AC-D67.1`–`AC-D70.3`, `A1`–`A219` plus
     `A220`–`A224`, `R1`–`R159` plus `R160`–`R164`, and the `Current Tech Stack` section — i.e. the phase
     added nothing to and removed nothing from the requirements record (AC-D70.3). The `D41`–`D66`
     assertion is **presence per id in a heading**, not a literal `### D<n>` prefix for every id: the
     record is mixed (`### D41`–`### D53` are defect entries; `D54`–`D66` sit in their `## Phase P<n>`
     headers and `#### Journey` titles — verified 2026-11-19), while AC-D70.3's `### D41`–`### D66` is
     shorthand for that record. Plus the three
     **module-level** constants the phase relies on and must not drift, read off the module (the package's
     existing alias style is `LB.ENVELOPE_VERSION`, `ui/lwc_view.py:2807`):
     `ui.lwc_bridge.ENVELOPE_VERSION == 1`, `ui.lwc_bridge.COALESCE_MS == 33`,
     `ui.lwc_bridge.LIVE_OPS == frozenset({"update_bar"})` — they are **not** `LwBridge` class attributes,
     so a literal `LwBridge.ENVELOPE_VERSION` would raise `AttributeError` — and the marker colour
     constant exists in `chart.js` and differs from the up/down candle colours.
  2. **The delta-scope record** — a build-record artefact, **not** a hash-pinned test (P24's precedent): the
     wave records `git diff --name-only 94d6119` and requires it to be a subset of {`data/models.py`,
     `data/bar_aggregator.py`, `services/market_calendar.py`, `ui/ticker_session.py`, `ui/lwc_view.py`,
     `ui/lwc_bridge.py`, `ui/popout_window.py`, `ui/main_window.py` (the one-line clock wiring at session
     creation), `chart_assets/lwc/envelope.js`, `chart_assets/lwc/chart.js`, `chart_assets/lwc/chart.test.js`,
     `chart_assets/lwc/envelope.test.js`, the three new suites + `tests/test_p25_fence.py`,
     `tests/test_d48_mode_parity.py` (docstring), `docs/`}. Anything else is a scope breach to escalate, not
     to justify.
  3. **Full offscreen suite green** recorded in the wave result, plus the two owner gates **G1**/**G2**
     listed as *named, not run* (the build does not claim them).
- **Exit condition:** the fence suite green, the full offscreen suite green, the recorded diff listing
  matches the allowlist exactly, and the result names both gates as owner-run.
- **Do not:** edit `docs/requirements/**` (the analyst's record is input), re-pin the phase's commit in a
  test, or add an assertion that would redden a later phase (no literal counts of files, lines or ops).

### Assumptions

- **AP-P25-1 — baseline and delta.** The build starts from HEAD `94d6119` (or a descendant that changes
  nothing this phase reads). The production delta is seven Python modules plus the two page sources
  (`chart_assets/lwc/envelope.js`, `chart.js`) and one line in `ui/main_window.py` (the clock wiring at
  session creation); everything else is tests and records (AP-P25-8 lists the file sets per wave).
- **AP-P25-2 — no new module, dependency, migration or wire version.** `Bar.partial` is an additive,
  non-persisted field; `set_partial` is an additive directive op inside the existing `{v: 1, ops}` envelope;
  no column, table, setting or asset version changes.
- **AP-P25-3 — the base's *tail* is not proved, and that is deliberate.** A present current-period row is
  treated as covering the period (it is IBKR's own aggregation and the load's wave refreshes it); the
  marker answers "is the period's **head** in this candle?", which is the failure `AC-D67.2` enumerates
  (empty / pruned / head-missing). Proving the tail would need a persisted capture time — a migration this
  phase forbids — so the boundary is recorded here and in FI-P25-1 rather than discovered later.
- **AP-P25-4 — the accepted request set is the priming path's.** `AC-D67.3` governs the **priming**
  request: `5 secs` within `[60 S, 3600 S]`, `1 min` within `[60 S, 1 D]`. The wave's wider windows (e.g.
  `30 D` / `1 min`, which Q-77 measured as a *working* request) are unaffected, unopened, and owned by
  P26/P27 — the architecture's quick-lane fold records that measurement so the two facts cannot be confused.
- **AP-P25-5 — the page accepts the op before anything emits it.** `validateOp` rejects unknown kinds and
  `validateEnvelope` rejects the whole envelope, so P25-01 lands page acceptance and the first emitter in
  the same wave and runs `node --test` in its exit condition (AR-P25-3).
- **AP-P25-6 — the marker's exact appearance is not a criterion.** The phase picks one shape/position
  (`circle`, `aboveBar`) and one named colour distinct from the up/down colours; the fence asserts the
  constant exists and is distinct, never a literal hue, so a later owner preference is a one-line change.
- **AP-P25-7 — G1 and G2 stay owner-run.** `AC-D67.2`/`AC-D68.1` are offscreen-asserted; the rendered
  candle (**G1**) and the live pop-out close (**G2**) are named gates the build lists and does not claim.
- **AP-P25-8 — per-wave file sets are disjoint where it matters.** P25-01 and P25-03 both edit
  `ui/lwc_bridge.py` and the page assets (`chart_assets/lwc/envelope.js`, `chart.js`, `chart.test.js`) and
  are therefore sequential; P25-02 edits only `ui/popout_window.py` and its suite and
  may run in parallel with either; P25-04 edits only tests and docs.
- **AP-P25-9 — the D48 week/month suites keep their assertions.** `test_d48_gate.py` greps the priming
  table's tokens (kept), and `test_d48_mode_parity.py` counts **wave** calls and checks every issued call's
  mode (a skipped prime only removes calls). One docstring sentence in the latter is restated because the
  behaviour it describes changed; no assertion is weakened.
- **AP-P25-10 — the quick-lane fold is Plan's, and is done.** `docs/pending_doc_sync.md` carried two entries
  (Q-76 expiry rendering, Q-77 shape-aware silence bound); both are folded into `docs/architecture.md`
  § *Phase P25* → *Quick-lane folds*, and the file is deleted. Neither entry names a user-facing doc: the
  only expiry wording in `USAGE.md` is the panel's `No 0DTE expiry today` empty state (verified 2026-11-19),
  which is a different statement from the formatter's `MmmDD` rendering, and nothing there mentions a retry
  bound — so no `USAGE.md` / `USAGE.txt` / `README` change is due.
- **AP-P25-11 — D70's contract is symmetric by decision, not by convenience.** `AC-D70.1` requires both
  "no row for that timestamp" and "equals the page's merge", and the glossary defines a whitespace row as
  not a bar. The page's fold therefore has to apply the same rule (P25-03's `mergeRows`/`upsertRow` change);
  re-stating the criterion to match the page's current keep-the-row behaviour would have been a
  requirements change, which is not Plan's to make. `mergeRows` is **not** the display fold (`applyRows`
  uses `seriesRows`/`barRows`), so the gap-slot rendering contract is unaffected — verified 2026-11-19.

### Flagged Issues

- **FI-P25-1 — a base that is stale but present is not marked (non-blocking, boundary, owner may overrule).**
  A current-period row fetched at the *previous* session covers the period's head, so the candle is rendered
  unmarked while its tail (last fetch → now) is filled by live bars only. The wave re-fetches and re-adopts
  on every load, and a failed wave already surfaces `AC-D16.4`'s shortfall line, so the window is small —
  but it is not zero, and `AC-D67.2` does not enumerate it. Proving it would need a capture time persisted
  with the row (a migration), which this phase forbids. Suggested direction if the owner wants it closed:
  a separate requirement for a per-`(symbol, timeframe, mode)` "last full fetch" stamp, marked partial while
  stale. No criterion in P25 changes if the owner accepts the boundary as written.
- **FI-P25-2 — "a cache hole inside the period" is only observable at the head (non-blocking, wording).**
  Journey 65's edge case lists a hole inside the period as a partial case, but a single periodic base row
  has no interior to inspect, and a no-trade gap is not missing data. P25's reading — head coverage decides
  the marker, and the values are always exactly the aggregate of the bars used — is what `AC-D67.2`'s
  measurable can assert. Flagged so the analyst can confirm the reading when Q119 closes; the alternative
  (interior gap counting) would mark a halt as missing data, which is wrong.
- **FI-P25-3 — the marker's visual weight is a judgement, not a criterion (non-blocking).** A small marker
  above the forming candle is the smallest honest cue the existing chart can carry (DG129/A220) and is
  assertable in both directions, but "visible enough" is not measurable offscreen. If the owner wants a
  heavier cue, it is a constant in `chart.js` plus one fence assertion — no architecture change.

Status: READY_FOR_TASK_MANAGER

## Phase P26 — Reconnect replay and backfill-wave lifecycle: all-or-nothing replay, cap-yield parking, retry bookkeeping (D71–D76) — drafted 2026-11-19

> Companion: `docs/architecture.md` § *Phase P26* (Relationship to prior phases, Codebase Summary,
> tech-stack decisions, System Components, frozen interfaces, Non-Functional Approach,
> AR-P26-1…AR-P26-8, S-P26-1…S-P26-7). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — **Phase P26 (D71–D76), Journeys
> 68–70, `AC-D71.1`–`AC-D76.3`**, A225–A229, R165–R169, gates **G3**/**G4** (owner-run),
> `design_gaps.md` DG130/DG131.
>
> **Baseline: HEAD `629be4a`**, tree clean, P25/D67–D70 shipped. The work is three seams around two
> lifecycle contracts that are already written down (the replay's "all-or-nothing under pacing
> pressure", the wave's "park and resume") plus one bookkeeping rule: **one replay transaction**
> (D71), **one parked-wave state** (D72/D75/D76 together — two faces of "a cap-parked wave must stay
> healthy"), and **one retry/ledger rule** (D73/D74). Hard constraints: D1–P25 read-only; **no
> production behaviour outside these six defects**; no new module, dependency, migration or settings
> constant; sizes S/M only; the two live checks are **named gates**, never suite gates.

### Traceability (requirement → architecture → wave)

| Requirement / journey | Architecture | Wave |
|---|---|---|
| **AC-D71.1** — with entries of more than one type and a pacing manager that refuses after the first send, one pass attempts **zero** reissues, schedules exactly one retry for the reported wait, and after the wait one pass reissues every entry once | **S-P26-1** (union pre-check + one transaction), **S-P26-2** (batch reservation), *Data Model* (`generic_n`/`rt_n`), AR-P26-1 | **P26-01** |
| **AC-D71.2** — after a completed replay the live count equals the pre-replay count, each old reqId is retired exactly once, no new reqId is registered twice; a second replay from the settled state gives the same numbers | **S-P26-3** (per-type retire resolver), *Integration Points* (TWS line count), AR-P26-3 | **P26-01** |
| **AC-D71.3** — a pressure-free replay is byte-identical in outcome to the pre-change behaviour (same entries, same rebinds, one pass); the existing replay suites stay green | **S-P26-1**/*Frozen Interfaces* (`replay_all` signature + return shape), AP-P26-6 | **P26-01** |
| **AC-D72.1** — a cap-yielded wave is never strand-finalised, the queue is intact, the D53 indicator reports the parked/queued state, no timeout shortfall is recorded | **S-P26-4** (parked state + settle rule + derived marker), **S-P26-7** (resume) | **P26-02** |
| **AC-D72.2** — a genuinely stalled in-flight member is finalised **once** with the stranded reason and the `AC-D16.4` shortfall, queue dropped as today | **S-P26-4** (disarm requires `not _history_req_ids`), AR-P26-4 | **P26-02** |
| **AC-D72.3** — a parked wave's next load issues the oldest queued plan, the indicator leaves the parked state, and the total issued across both loads stays inside the pacing budget | **S-P26-7** (coalesce-resume), **S-P26-4** (parked flag cleared) | **P26-02**; live arm **G4** (owner-run) |
| **AC-D73.1 / AC-D73.2** — after a 162 retry each timestamp appears once in `_pending_bars` and the persisted count equals the distinct timestamps; the silence path gives the identical post-condition | **S-P26-5** (one surrender helper, both paths) | **P26-03** |
| **AC-D74.1** — the cancel-tag set is bounded (constant / live-wave window, not linear in wave count) **and** a current-wave late ack still classifies as superseded (debug, no status-bar error) | **S-P26-6** (generation-windowed tags; two-batch window), AR-P26-7 | **P26-03** |
| **AC-D74.2** — wave A's two failures do not leak into wave B's shortfall; the failure set is empty after B | **S-P26-6** (per-wave reset in `queue_wave_plans`) | **P26-03** |
| **AC-D75.1 / AC-D75.2** — a parked (queue-only) wave coalesces (no cancel, queue survives, `_pending_prefetch` survives, no duplicate request); a genuine triple change still cancels and re-plans | **S-P26-7** (gate widened; resume), AP-P26-5 | **P26-02** |
| **AC-D76.1 / AC-D76.2** — an indefinitely not-ready transport cannot loop past the bound: either one finalise with a surfaced reason or a bounded retry count, never indefinite rescheduling; a short not-ready period converges with one continuation and the bound armed for the deferral it covers | **S-P26-4** (readiness episode armed once, transport-named reason), AR-P26-6 | **P26-02** |
| **AC-D76.3** — `### D41`–`### D70`, `AC-D1.1`–`AC-D70.3`, A1–A224, R1–R164, the existing-repository sentence and the Current Tech Stack unchanged and present | *Relationship to prior phases* (`[existing]`, read-only inputs); **P26-04**'s fence | **P26-04** |
| **Journey 68** — reconnect with the option panel ON and two lines pacing-gated | S-P26-1, S-P26-2, S-P26-3 | **P26-01**; live arm **G3** (owner-run) |
| **Journey 69** — park a wave at the per-load cap and leave it alone; reload resumes | S-P26-4, S-P26-7 | **P26-02**; live arm **G4** (owner-run) |
| **Journey 70** — retries, tags and a parked reload | S-P26-5, S-P26-6, S-P26-7 | **P26-02/P26-03** |
| A225/A226/A227/A228/A229, DG130, DG131 | S-P26-1…S-P26-7 (each names the assumption it implements) | 01/02/03 |
| R165–R169 | *Architecture Risks* AR-P26-1…AR-P26-8 | all waves |

### Phases

Dependency shape: **P26-01 → P26-02 → P26-03 → P26-04**. All four are sequential because two files
(`ui/ticker_session.py`, `ui/main_window.py`) carry every wave's edits; there is no parallel branch.
Exactly two waves change user-visible behaviour (P26-01 the reconnect settle, P26-02 the parked state
and its indicator word); P26-03 is invisible bookkeeping and P26-04 is the record.

#### P26-01 — D71: the reconnect replay is one transaction over a union budget — size M

- **Covers:** AC-D71.1, AC-D71.2, AC-D71.3, Journey 68 (offscreen legs), A225/A226, DG131, R165.
- **Depends on:** nothing.
- **Files:** `ibkr/subscription_manager.py`, `ibkr/pacing.py`, `ui/main_window.py` (the replay body,
  the resolver registrations in `__init__`, and the option reissue/rebind map cleanup), a new
  `tests/test_d71_replay_transaction.py`.
- **Deliverables, in this order:**
  1. **The batch reservation (S-P26-2).** `ibkr/pacing.py`: `generic_wait_for_batch(count) -> float`
     (pure: `0.0` when `count <= 1`, else
     `max(0.0, (count - 1) * (1.0 / settings.MAX_REQ_PER_SEC) - (now - self._last_req_time))` under the
     lock) and `generic_batch(count)` — a `contextlib.contextmanager` that re-checks the wait (raising
     `PacingExceeded(wait)` from inside `__enter__`, so the body never runs), sets
     `self._batch_remaining = int(count)`, and in `finally` clears it and calls
     `self.record_request_slot()`. `throttle()` gains one branch **before** the clock read:
     `if self._batch_remaining > 0: self._batch_remaining -= 1; return`. `reset_for_tests` clears the
     counter. Every other member, constant and docstring claim is untouched; the docstring states that
     the batch is the pass's reservation and that an over-spend falls through to the unchanged gate.
  2. **The transactional pass (S-P26-1) and the retire resolvers (S-P26-3).**
     `ibkr/subscription_manager.py`: add `self._cancel_hooks: dict[str, Callable[[int], None]] = {}`
     and `set_cancel_hook(req_type, fn)`. Rewrite `replay_all`'s body into three phases — union
     pre-check (`rt_n`, `generic_n = len(pending) - rt_n`, one `PacingExceeded(max(rt_wait,
     generic_wait))` before any mutation) → reissue every pending entry in registry order inside
     `with pacing_manager.generic_batch(generic_n):` (on any raise: retire every new id via its
     resolver, `rebind(old_id)` for each successful entry, then re-raise) → rebind, retire the old id
     through `self._cancel_hooks.get(entry.req_type)` (best-effort, debug-logged), move the registry
     key. Keep the signature, the return shape and the `include_types` filter. Restate the class
     docstring: the contract, DG131's global coupling, and why a split pass is forbidden.
  3. **The window's wiring.** Install the two resolvers immediately after
     `self.sub_manager = SubscriptionManager()`: `RT_BARS` → `self._unregister_req_id(old)` +
     `self.rt_manager.unsubscribe(old)`; `OPTION_LEGS` → `self._option_req_ids.pop(old, None)` +
     `self.md_manager.cancel_mkt_data(old)`. `_option_reissue_leg` keeps repointing its maps but no
     longer needs to "silently drop" the old id — say so in its docstring. Make
     `_replay_subscriptions`'s deferral replaceable: keep the single
     `QTimer.singleShot(int(e.wait_seconds * 1000), …)` call (its shape is pinned by
     `test_p7_t07_t13_replay_all_defers_via_singleshot`), but schedule an epoch-guarded callback
     (`self._replay_serial`, read with `getattr` so a stub window works) that returns immediately when
     a newer call has superseded it, and restate the method's docstring (union budget, one deferral,
     no stacked retries).
  4. **The suite** `tests/test_d71_replay_transaction.py` — fake resolve/parse-free fixtures: a fake
     `md_manager` counting `req_mkt_data`/`cancel_mkt_data` per id, a fake `rt_manager` counting
     subscribe/unsubscribe, a fake pacing object exposing `realtime_wait_for_slots` +
     `generic_wait_for_batch`/`generic_batch`, and a registry with one RT entry plus two
     `OPTION_LEGS` entries carrying `reissue`/`rebind`. Cases: (a) AC-D71.1 — the fake refuses the
     generic batch ⇒ zero reissue calls, registry byte-identical, exactly one deferral for the reported
     wait; then admit ⇒ one pass reissues all three once, in registration order. (b) AC-D71.2 — the
     live set's size equals the pre-pass size, each old id retired exactly once, no new id registered
     twice, and a second pass from the settled state reproduces the numbers. (c) AC-D71.3 — with both
     budgets open the pass yields the same `[(old, new)]` pairs and one rebind per entry. (d) unwind —
     the second entry's `reissue` raises `IBKRNotReady`: every new id retired, routing rebound to the
     old ids, registry byte-identical, the exception propagates. (e) Journey 68's edges — a second
     disconnect during the deferral leaves one scheduled callback that actually runs (epoch), and an
     RT-only pass is unaffected by a throttled generic gate. (f) the gate's own contract —
     `throttle()` raises after a batch has closed, and an over-spend inside a batch raises.
- **Exit condition:** the new suite green **and** `tests/test_d28_pacing.py
  tests/test_p7_w4_streaming.py tests/test_p7_w4_deferral.py tests/test_d65_option_stream.py
  tests/test_d27_reconnect.py tests/test_d40_tws_lifecycle.py tests/test_d24_popouts.py` green,
  unchanged; `git diff --name-only` ⊆ the three production files + the new suite.
- **Do not:** change `SubscriptionManager.subscribe`'s signature or `_Entry`'s fields; change the
  `include_types` set the window passes; touch `ibkr/realtime_bars.py`, `ibkr/market_data.py`,
  `ui/ticker_session.py` or `ui/watchlist_panel.py`; add a `cancel` keyword to `subscribe`; raise
  `MAX_REQ_PER_SEC` or any pacing constant; split the pass by type; make the replay sleep or wait.

#### P26-02 — D72 + D75 + D76: a cap-parked wave is a healthy state, and it resumes — size M

- **Covers:** AC-D72.1, AC-D72.2, AC-D72.3, AC-D75.1, AC-D75.2, AC-D76.1, AC-D76.2, Journey 69,
  R166, R169, A227, DG130.
- **Depends on:** P26-01 (same two files; and the replay's deferral shape must already be settled).
- **Files:** `ui/ticker_session.py`, `ui/main_window.py`, a new
  `tests/test_d72_d75_d76_parked_wave.py`.
- **Deliverables, in this order:**
  1. **Parked state and the settle rule (S-P26-4).** `ui/ticker_session.py`: `_wave_parked` and
     `_settle_parked_wave()` (disarm the watchdog and stop `_wave_continue_timer` when
     `_wave_parked and not self._history_req_ids`; return whether it settled). The cap branch in
     `_issue_wave_chunks` sets `_wave_parked = True` after the unchanged status message and calls the
     settle step (it will normally not settle — members are in flight); `on_historical_data_end` and
     `on_historical_error` call it before their `_wave_may_complete()` checks; the D72 defect's second
     site (the end marker that "cannot complete the wave") is therefore where the bound is released.
     Clear `_wave_parked` in `queue_wave_plans`, `_cancel_history_requests` and
     `_finalize_history_wave`. Do **not** change `_wave_may_complete`'s definition.
  2. **The readiness episode (S-P26-4's second half).** Split `_issue_wave_chunks`'s single
     `except (PacingExceeded, IBKRNotReady)` into two: `PacingExceeded` → unchanged
     `_schedule_wave_continuation(wait)`; `IBKRNotReady` → set `_wave_deferral_reason = "IBKR not
     ready"`, arm the watchdog **only if `not self._history_wave_timer.isActive()`** (base bound, no
     wait), surface one status line per episode (`_wave_not_ready_announced`), and start the
     continuation timer at the unchanged 1 s fallback without re-arming. A successful issue clears the
     reason and the announced latch. Same split in `_retry_silent_chunk`. `_schedule_wave_continuation`
     gains one keyword-only `transport_not_ready: bool = False` (the default path is byte-identical,
     which is what `test_p7_w2_watchdog.py::test_t11_watchdog_covers_pacing_deferral` pins). The bound
     formula and both window fractions are untouched.
  3. **The window half (S-P26-4's timeout guard + S-P26-7).** `_on_session_history_wave_timeout`
     returns without stranding when `session._wave_parked and not session._history_req_ids` (and
     because the session already disarmed, it normally never fires); otherwise it finalises as today,
     passing `"IBKR not ready"` when the session's `_wave_deferral_reason` names the transport, else
     `"Historical backfill timed out"`. Widen `_load_chart_resolved`'s coalesce gate to
     `(bool(new_session._history_req_ids) or bool(new_session._wave_plan_queue))` and same triple; in
     the coalesce branch, when the session is parked, reset `_wave_issued_this_load = 0`, clear
     `_wave_parked`, re-arm the watchdog (`_arm_history_wave_watchdog()`), call
     `_issue_wave_chunks()`, then refresh the indicator — leave the queue's identity intact (no
     `list(...)` copy, no clear); an in-flight coalesce keeps today's no-op. Add one derived marker to
     `set_backfill_state` (`parked`, from a `_backfill_parked` latch set by
     `_refresh_backfill_indicator` as `session._wave_parked and not session._history_req_ids` and
     cleared in `clear_backfill_indicator`); signature, keys and idle line unchanged.
  4. **The suite** `tests/test_d72_d75_d76_parked_wave.py` — a clock-controlled host (`_now_ts`, the
     session's timers driven directly) and a stub `md_manager` recording issue order. Cases:
     (a) AC-D72.1 — a plan list longer than `per_load_historical_cap()`, end every issued chunk, then
     advance past twice the bound: the finalise spy is never called, `_wave_plan_queue`'s length is
     unchanged, `_history_wave_timer.isActive()` is False and the indicator text contains `parked`.
     (b) AC-D72.2 — a cap-yielded wave with one member that never answers: the bound elapses, exactly
     one stranded finalise with the reason and the `AC-D16.4` line, queue dropped.
     (c) AC-D72.3 + AC-D75.1 — park, then load the identical triple: the cancel spy is not called, the
     queue's head object is the plan issued first, `_pending_prefetch` survives, the indicator leaves
     `parked`, and the issued count across both loads stays inside the pacing budget.
     (d) AC-D75.2 — a different symbol/timeframe/mode while parked: the cancel path runs, the
     generation advances and the old queue is cleared. (e) AC-D76.1 — an indefinitely not-ready
     client: the bound is armed once (`_history_wave_bound_ms` equals the base) and time past it
     produces one finalise naming the transport, never a growing retry count.
     (f) AC-D76.2 — not-ready for two seconds then ready: one continuation at a time, the issue lands
     as readiness arrives, and the arm arguments are the base bound. (g) Journey 69's edges — cap
     reached on the first issue call; a disconnect while parked drops the queue (unchanged); a resumed
     wave that then stalls is still bounded.
- **Exit condition:** the new suite green **and** `tests/test_p7_w1_cap.py
  tests/test_p7_w1_coalesce.py tests/test_p7_w1_persist.py tests/test_p7_w2_watchdog.py
  tests/test_p7_w2_prime.py tests/test_p14_indicator.py tests/test_p14_lifecycle.py
  tests/test_p15_continue.py tests/test_p15_expiry.py tests/test_p15_surfacing.py
  tests/test_history_backfill.py tests/test_history_backfill_disconnect.py
  tests/test_history_backfill_loadpath.py tests/test_p19_prefetch_wave.py` green, unchanged;
  `git diff --name-only` ⊆ the two production files + the new suite.
- **Do not:** change the bound formula, `_WATCHDOG_BASE_WINDOW_FRACTION`,
  `_WATCHDOG_MARGIN_WINDOW_FRACTION`, `per_load_historical_cap()` or `MAX_HISTORICAL_PER_600S`; touch
  the D54 expiry block (`_on_backfill_expiry`, `_BACKFILL_EXPIRY_BOUND_MS`, `_backfill_expiry_missed`)
  or `set_backfill_state`'s signature; add a widget, a window or a second indicator; change
  `_wave_may_complete`; cancel on a coalesce (except a genuine triple change); re-plan on a resume;
  reset the D53 elapsed baseline on a resume.

#### P26-03 — D73 + D74: one surrender rule, one wave-scoped ledger — size S

- **Covers:** AC-D73.1, AC-D73.2, AC-D74.1, AC-D74.2, Journey 70, A228, A229, R168.
- **Depends on:** P26-02 (same two files; the park's resets and the resume must already exist).
- **Files:** `ui/ticker_session.py`, `ui/main_window.py`, a new
  `tests/test_d73_d74_retry_ledger.py`.
- **Deliverables, in this order:**
  1. **The surrender helper (S-P26-5).** Extract `_surrender_chunk_bars(req_id)` — pop
     `_req_bars[req_id]` and drop exactly those `Bar` objects from `_pending_bars` by `id()` — and call
     it from `_retry_silent_chunk` (replacing its inline block, behaviour identical) and from
     `on_historical_error`'s `code == 162` branch **before** the plan is re-queued. Nothing else in
     either path changes: the cancel, the tag, the post-issue slot, the `_retried_plans` allowance and
     the continuation/arm behaviour stay as they are.
  2. **The wave-scoped ledger (S-P26-6).** `queue_wave_plans` also resets
     `self._backfill_failed_req_ids = set()` (per wave, beside `_retried_plans`) and calls the new
     prune. Tag bookkeeping: `_cancelled_history_gen: dict[int, int]` records `_history_generation` at
     each `_cancelled_history_req_ids.add(...)` site (cancel path and silence retry);
     `_register_history_request`'s existing `discard` also pops the gen entry; a `_prune_cancel_tags()`
     keeps ids whose tagged generation is `>= _history_generation - 1` and runs at the start of
     `queue_wave_plans`. `is_superseded` stays a set-membership read. In `ui/main_window.py`,
     `_teardown_session` merges each batch into `_superseded_history_windows` (keep the last two) and
     rebuilds `_superseded_history_reqs` as their union, so the attribute's name and meaning survive.
  3. **The suite** `tests/test_d73_d74_retry_ledger.py` — a stub `md_manager` whose `req` can return a
     chosen set of bars per reqId, a controllable `_silence_now`. Cases: (a) AC-D73.1 — five bars then
     a 162, the retry delivering the same five plus five more: `_pending_bars`'s per-timestamp
     multiset is all ones, and the cache row count equals the distinct timestamps.
     (b) AC-D73.2 — the identical scenario driven through the silence path: the same invariant, asserted
     by the same helper in the test (not two different expectations). (c) edges — a retry refused
     twice finalises short with the partial bars surrendered; a 162 with zero partial bars is a no-op
     surrender. (d) AC-D74.1 — many waves in one session: the tag set's size is bounded by the ids
     cancelled in the last two generations and does not grow with the wave count, while an ack for a
     current-wave id still classifies debug-only through `win._on_error` (no status-bar error).
     (e) AC-D74.2 — wave A with two failures then wave B with none: B's shortfall reports zero and the
     set is empty. (f) edge — a prefetch wave immediately after a failed load reports only its own
     failures.
- **Exit condition:** the new suite green **and** `tests/test_d56_silence_retry.py
  tests/test_d56_fencing.py tests/test_d56_taxonomy_pacing.py tests/test_d56_retry_indicator.py
  tests/test_p19_prefetch_depth.py tests/test_p19_prefetch_honesty.py
  tests/test_history_backfill_loadpath.py tests/test_d28_3_historical_pacing.py` green, unchanged;
  `git diff --name-only` ⊆ the two production files + the new suite.
- **Do not:** dedupe `_pending_bars` by timestamp anywhere else; change `_persist_chunk_bars`,
  `flush_pending_bars` or the finalise accounting; change `_retried_plans`' once-only rule; clear
  cancel tags for the *current* generation; introduce a TTL, an LRU or a numeric cap for the tag set;
  touch `_SUPERSEDED_HISTORICAL_ACK_CODES` or `is_superseded`'s answer.

#### P26-04 — records and the phase fence — size S

- **Covers:** AC-D76.3, the phase's own evidence record.
- **Depends on:** P26-01, P26-02, P26-03.
- **Files:** a new `tests/test_p26_fence.py`; `docs/` records; `docs/codebase-map.md`'s P26 note.
  **No production file.**
- **Deliverables:**
  1. **The fence suite** `tests/test_p26_fence.py`, one assertion per named artefact:
     `requirements.md` still carries `This is an existing repository.`, the `D41`–`D70` record (presence
     per id in a heading — the record is mixed, exactly as P25-04 records), P26's own `#### D71`–`#### D76`
     entries, `Journey 68`–`Journey 70`, `AC-D1.1`–`AC-D70.3` **plus** `AC-D71.1`–`AC-D76.3`,
     `A1`–`A224` plus `A225`–`A229`, `R1`–`R164` plus `R165`–`R169`, and the `Current Tech Stack`
     section.
  2. **The pinning assertions** (read off the modules, not off prose): `per_load_historical_cap() ==
     max(1, settings.MAX_HISTORICAL_PER_600S // 4)`; `_WATCHDOG_BASE_WINDOW_FRACTION == 1 / 5` and
     `_WATCHDOG_MARGIN_WINDOW_FRACTION == 1 / 20`; `_history_wave_watchdog_bound_ms()` at a zero wait
     equals `int(pacing_manager._hist_window * 1000 / 5)`; the four tags' values; the
     `include_types` set `_replay_subscriptions` passes; and `TIMEFRAME_CONFIG`'s keys unchanged. No
     literal file/line counts, no phase-commit hash.
  3. **The delta-scope record** — a build-record artefact (P24/P25 precedent), not a hash-pinned test:
     the wave records `git diff --name-only 629be4a` and requires it to be a subset of
     {`ibkr/subscription_manager.py`, `ibkr/pacing.py`, `ui/ticker_session.py`, `ui/main_window.py`,
     the four new suites, `docs/`}. Anything else is a scope breach to escalate, not to justify.
  4. **Full offscreen suite green** recorded in the wave result, plus the two owner gates **G3**/**G4**
     listed as *named, not run*.
- **Exit condition:** the fence suite green, the full offscreen suite green, the recorded diff listing
  matches the allowlist exactly, and the result names both gates as owner-run.
- **Do not:** edit `docs/requirements/**`; assert a phase commit hash or a file/line count; add an
  assertion that a later phase (P27's planner work) would redden.

### Assumptions

- **AP-P26-1 — baseline and delta.** The build starts from HEAD `629be4a` (or a descendant that changes
  nothing this phase reads). The production delta is four modules (`ibkr/subscription_manager.py`,
  `ibkr/pacing.py`, `ui/ticker_session.py`, `ui/main_window.py`); everything else is tests and records.
  No new module, dependency, migration, wire change or settings constant.
- **AP-P26-2 — the union gate is global on purpose.** A throttled generic gate defers an RT-containing
  pass as a whole (DG131/R165). This is the documented contract, not an oversight: it is written into
  `replay_all`'s class docstring and S-P26-1, and it is exercised by a suite case. Per-type progress
  would need its own requirement, not a quiet split.
- **AP-P26-3 — "parked" means cap-yielded with nothing in flight.** The cap-yield marks the queue
  parked *immediately* (so the indicator can say so), but the watchdog is released only when the last
  member ends; while members are outstanding the bound still applies (R166). A resumed wave re-arms
  the bound in the same step that clears the flag.
- **AP-P26-4 — the D54 T0+10 s verdict is not suppressed.** `AC-D54.*` is explicitly out of scope
  (Non-Goals): a parked wave still receives the 10 s "partial" verdict and, when spans remain missing,
  the `AC-D16.4` missing-days line — which is a **different** statement from the watchdog's
  `"Historical backfill timed out"` reason that `AC-D72.1` measures (finalise spy + queue length).
  P26 adds the `parked` word beside `partial`; it does not silence the D54 line. Recorded as
  FI-P26-2 for the owner.
- **AP-P26-5 — AC-D75.1's "no new request is issued for the parked plans" is read as "no duplicate or
  extra request".** The resume issues exactly the queued plans, once, in order, and re-plans nothing —
  which is what `AC-D72.3`'s measurable ("the oldest queued plan is issued") requires. The alternative
  literal reading (issue nothing at all) makes the two criteria jointly unsatisfiable and would turn
  the park into a silent stop. Recorded as FI-P26-1 so the analyst can confirm the wording.
- **AP-P26-6 — the existing suites stay green as they are.** No assertion is re-baselined. In
  particular `test_d28_pacing.py`'s replay case (RT-only, so `generic_n = 0`) and
  `test_p7_w4_streaming.py::test_p7_t07_t13_replay_all_defers_via_singleshot` (which pins one
  `QTimer.singleShot` call at `2000` ms) stay unchanged — that is why the replay's deferral keeps its
  `singleShot` shape and the retirement is per-type rather than a `subscribe` keyword (four test
  doubles carry the five-argument `subscribe`). If a pre-existing expectation must be re-baselined,
  the wave stops and escalates to Plan.
- **AP-P26-7 — G3 and G4 stay owner-run.** Every AC is offscreen-assertable with fakes; the live
  reconnect settle (**G3**) and the four-minute idle parked wave plus its reload (**G4**) are named
  gates the build lists and does not claim.
- **AP-P26-8 — the four waves are strictly sequential.** `ui/ticker_session.py` and
  `ui/main_window.py` are edited by 01, 02 and 03; P26-04 edits only tests and docs. There is no
  disjoint parallel branch, and `touches_files` overlap must serialise them in that order.
- **AP-P26-9 — no new tunable.** The readiness episode is bounded by the existing watchdog bound; the
  park uses `per_load_historical_cap()`; the batch arithmetic is `(n − 1)` intervals of
  `1 / MAX_REQ_PER_SEC`. No constant is added to `config/settings.py`.
- **AP-P26-10 — one new user-visible word, no new surface.** `parked` on the existing D53 label is the
  only addition; the per-load-budget message, the "pacing-limited, continuing backfill…" line, the
  reconnect "retrying in Ns…" line and the `AC-D16.4` shortfall keep their wording, with the `[reason]`
  suffix naming the transport for a readiness episode.

### Flagged Issues

- **FI-P26-1 — AC-D75.1's last clause contradicts AC-D72.3 as literally written (non-blocking if the
  reading in AP-P26-5 is accepted).** `AC-D75.1` says an identical-triple reload issues "no new request
  … for the parked plans"; `AC-D72.3` says the same load "issues the oldest queued plan" and its
  measurable is "issued-plan order + pacing-manager call log". Both cannot hold literally. Plan adopts
  the reading under which the reload **resumes** the parked queue (no cancel, no re-plan, no duplicate,
  no extra request beyond the queued plans themselves), which satisfies both ACs' measurables
  (`AC-D75.1`'s measurable names only the cancel spy, the queue and `_pending_prefetch`). Suggested
  direction: the analyst confirms the wording ("no *duplicate* request") when the batch closes; a
  different reading would need `AC-D72.3` restated, which is not Plan's act.
- **FI-P26-2 — a parked wave still surfaces the D54 T0+10 s verdict and its missing-days line
  (non-blocking, boundary).** `AC-D54.*` is out of scope by this phase's Non-Goals, so P26 cannot
  suppress it; the line is a genuine incompleteness report about a chart whose remainder is queued, and
  it is **not** the watchdog's `"Historical backfill timed out"` reason `AC-D72.1` measures. If the
  owner reads D72's "never a shortfall" as covering the D54 line too, that is a new requirement
  (suppress/soften the 10 s verdict for a parked wave) and would reopen `AC-D54.*`.
- **FI-P26-3 — parked work survives a same-triple reload, not a session teardown (non-blocking,
  boundary).** A symbol switch away (or any path that tears the session down) drops the parked queue by
  design — Journey 69's disconnect edge says so, and the planner re-derives the remainder from the
  persisted cache on the next load, so no fetched data is lost and the per-load cap applies again.
  What is **not** preserved is the queue's identity and the `_pending_prefetch` marker across a
  teardown; P26 does not extend the park's lifetime beyond the session, because that would need
  persisted wave state (a migration this phase forbids).

Status: READY_FOR_TASK_MANAGER

## Phase P27 — Planner, pacing and backfill hygiene: duplicate chunks, the prime retry that cannot fire, window edges (D77–D83) — drafted 2026-11-19

> Companion: `docs/architecture.md` § *Phase P27* (Relationship to prior phases, Codebase Summary,
> tech-stack decisions, System Components, Data Model, frozen interfaces, Non-Functional Approach,
> AR-P27-1…AR-P27-9, S-P27-1…S-P27-7). Requirements input:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`) — **Phase P27 (D77–D83), Journeys
> 71–73, `AC-D77.1`–`AC-D83.2`**, A230–A234, R170–R174, `design_gaps.md` **DG135**; no live gate.
>
> **Baseline: HEAD `70b16f2`** (P26 build complete; tree clean at drafting time; P26's code review is
> still open, so AP-P27-1 fixes how the build treats a P26 review fix). The work is four rules behind
> seven defects: **one request per identity** (D77/D83 — the planner over-requests), **one window
> rule** (D82 — the same function's arithmetic), **one owner for the prime's completion** (D78), and
> **budget stamped only by a send that crossed the wire** (D81, which makes D80's refund vacuous and
> retires it, with D79's dead cache read). Hard constraints: D1–P26 read-only apart from the two
> labelled revisions; `plan_requests` stays pure; **no new module, dependency, migration or settings
> constant**; no pacing-constant retuning; sizes S/M only; every criterion offscreen.

### Traceability (requirement → architecture → wave)

| Requirement / journey | Architecture | Wave |
|---|---|---|
| **AC-D77.1** — no two plans share `(endDateTime, duration, bar_size)`, and the union of the plans' coverage is unchanged by the change while containing every input span (AP-P27-2) | **S-P27-1** (identity de-duplication in `plan_requests`), *Data Model*, AR-P27-1 | **P27-01** |
| **AC-D77.2** — every interval covered before the change is still covered; a floor span starting earlier than the presence span still fetches the earlier part | **S-P27-1** (detector untouched; first occurrence wins per identity), AP-P27-2 | **P27-01** |
| **AC-D77.3** — a coinciding-span scenario spends exactly one request where the pre-change planner spent two, and the per-load cap is charged once | **S-P27-1**, *Non-Functional* (spend proportionality) | **P27-01** |
| **AC-D82.1** — a bar timestamped exactly at a session's end belongs to exactly one window and adds no duplicate boundary coverage | **S-P27-2** (half-open `[start, end)`, `now` cap inclusive), AR-P27-2 | **P27-01** |
| **AC-D82.2** — a one-period trailing hole is not reported and a two-period hole is; the docstring and the code state the same number | **S-P27-2** (one `gap_threshold = 1.5 × period`), AR-P27-3 | **P27-01** |
| **AC-D83.1** — a span whose end equals its start emits no plan, and a list of only such spans yields an empty list | **S-P27-1** (`end_ts <= start_ts` guard; `max(1, …)` removed) | **P27-01** |
| **AC-D78.1** — with `wait > 15 s`, either the prime issues at the reported wait or the retry is gone and the phase records the single backstop path; a pending retry that cannot run fails | **S-P27-3** (`_prime_backstop_ms(retry_ms)`), DG135 | **P27-02** |
| **AC-D78.2** — an issued prime that never answers fails open exactly once, with no second attempt; `AC-D65.15`'s timeout cases stay green | **S-P27-3** (issued-prime branch keeps the flat 15 s; `_on_prime_timeout` frozen), AR-P27-4 | **P27-02** |
| **AC-D78.3** — refusal → (issued prime or fail-open attach) is bounded by the reported wait plus the backstop; no unbounded wait | **S-P27-3**, *Non-Functional* (bounded prime), R172 | **P27-02** |
| **AC-D79.1** — `get_last_timestamp` no longer exists (or is mode-aware with a caller); no production module queries `bars` by symbol+timeframe ignoring `ext_hours` | **S-P27-6** (deletion + a static scan that keeps the class out) | **P27-03** |
| **AC-D80.1** — a refund frees exactly one slot that is the refunding request's own, **or** the path is removed and its caller with it; the two-request fixture's other slot survives | **S-P27-5** (retired: `refund_historical_slot`, its caller branch and the ledger that gated it), AP-P27-5 | **P27-03** |
| **AC-D81.1** — a client whose request call raises leaves the interval clock and the budgets unchanged; the next successful request is spaced from the previous **successful** one | **S-P27-4** (`throttle(stamp=False)` + post-send `record_request_slot()`), AR-P27-5 | **P27-03** |
| **AC-D81.2** — the id sequence has no gap caused by a failed send (or the phase records why an allocated id is acceptable) | **S-P27-4** (`IdManager.release_id`, newest-allocation rollback only), AR-P27-7 | **P27-03** |
| **AC-D83.2** — `### D41`–`### D76`, `AC-D1.1`–`AC-D76.3`, A1–A229, R1–R169, the existing-repository sentence and the Current Tech Stack unchanged and present | *Relationship to prior phases* (`[existing]`, read-only inputs); **P27-04**'s fence | **P27-04** |
| **Journey 71** — plan a load from a cache that is entirely out-of-mode; a partial floor; an empty cache; a zero-length span | S-P27-1, S-P27-2, AR-P27-9 | **P27-01** |
| **Journey 72** — prime right after a backfill wave, when the wait exceeds the backstop; a wait below it; the 15 s boundary | S-P27-3 | **P27-02** |
| **Journey 73** — two requests, one refused send; the slot count and the id sequence; a cancel with no slot | S-P27-4, S-P27-5 | **P27-03** |
| A230/A231/A232/A233/A234, DG135 | S-P27-1…S-P27-6 (each names the assumption it implements) | 01/02/03 |
| R170–R174 | *Architecture Risks* AR-P27-1…AR-P27-9 | all waves |

### Phases

Dependency shape: **P27-01 ∥ P27-02 → P27-03 → P27-04.** `P27-01` edits only
`services/backfill_service.py` (plus its own suite) and shares no file with the other waves, so it may
run alongside them. `P27-02` and `P27-03` both edit `ui/ticker_session.py`, so they serialise in that
order (the prime first: it is the smaller edit to that file, and the ledger deletion is easier to
reason about once nothing else in the session is moving). `P27-04` records the phase and runs last.

Two waves change user-visible behaviour: `P27-01` (fewer/cleaner requests — the wave a load issues)
and `P27-02` (a prime that can actually retry after a backfill, so the forming bar appears without a
reload). `P27-03` is invisible budget hygiene; `P27-04` is the record.

#### P27-01 — D77 + D82 + D83: one request per identity, one window rule — size M

- **Covers:** AC-D77.1, AC-D77.2, AC-D77.3, AC-D82.1, AC-D82.2, AC-D83.1, Journey 71, A230, A232,
  R170, R171.
- **Depends on:** nothing.
- **Files:** `services/backfill_service.py` (three functions + the module docstring), a new
  `tests/test_d77_d82_d83_planner_identity.py`.
- **Deliverables, in this order:**
  1. **The empty-span guard and the identity set (S-P27-1).** In `plan_requests`: inside the
     per-span loop, `if span.end_ts <= span.start_ts: continue` (replacing the `span_seconds < 0`
     test, which the new guard subsumes); `chunk_count = -(-span_seconds // chunk_seconds)` — drop the
     `max(1, …)` clamp, which the guard makes unnecessary; before appending, compute
     `end_dt = _format_end_date(anchor)` and skip when `(end_dt, duration, bar_size)` is already in a
     local `seen` set, otherwise add it and append the `RequestPlan` with the **current** span's
     `span_start_ts`/`span_end_ts`. Ordering (spans by `end_ts` desc, anchors descending), the
     `TIMEFRAME_CONFIG` lookup and every field stay as they are.
  2. **The window arithmetic (S-P27-2).** In `_bar_level_missing_spans`: keep
     `bound = min(we, now_ts)`, then select `in_window` with `ws <= t <= bound` **only when**
     `now_ts < we` (the window is capped by *now* — A232's exception) and with `ws <= t < bound`
     otherwise; replace the trailing-edge test with `if bound - in_window[-1] > gap_threshold:` so the
     leading, internal and trailing edges share `gap_threshold = period * 1.5`. In `present_days`'
     equity branch: `if any(window_start <= ts < window_end for ts in day_ts): present.add(day)`.
     The futures branches of both functions are untouched.
  3. **The docstrings, stated once.** The module docstring and `_bar_level_missing_spans`' docstring
     say: windows are half-open `[start, end)` with the `now` cap inclusive; one gap threshold of
     **1.5 bar periods** governs leading, internal and trailing edges; a span with no positive length
     yields no plan; each distinct `(endDateTime, duration, bar_size)` appears once.
  4. **The suite** `tests/test_d77_d82_d83_planner_identity.py` — pure, no Qt, no DB, injected
     timestamps. Cases: (a) AC-D77.1/AC-D77.3 — Journey 71's out-of-mode cache (ETH bars cached, RTH
     load with `min_sessions=30`): the plan-identity multiset has no duplicate, and the coinciding
     newest chunk appears once; assert the plan count drops by exactly the number of coinciding
     identities and that a hand-built two-span list with the same `end_ts` yields one plan for the
     shared anchor. (b) AC-D77.2 — a partially overlapping pair where the floor span starts earlier:
     the test derives the expected anchor set from the input spans with its **own** chunk arithmetic
     (independent of the implementation, the pre-change rule), asserts every expected anchor is present
     and each exactly once, and asserts the earlier part of the floor span is still covered
     (AP-P27-2). (c) an identity-keyed difference: two coinciding anchors with
     **different durations** emit two plans (AR-P27-1). (d) AC-D83.1 — `MissingSpan(t, t)` emits none,
     and a list of only such spans yields `[]`. (e) AC-D82.1 — a bar timestamped exactly at a session's
     end belongs to no window of that day, and a fixture with a close-instant bar plus a next-window
     bar shows each instant in exactly one window's accounting and no duplicate span at the boundary;
     the same fixture through `find_missing_spans` (with the day-presence pass) still covers the day
     (AR-P27-2). (f) AC-D82.2 — trailing holes of 1.0, 1.7 and 2.0 periods: 1.0 not reported, 1.7 and
     2.0 reported (the 1.7 case is the one that distinguishes the unification from the old
     `>= period` rule); the module docstring's number equals the constant the code uses (read it, do
     not restate it). (g) Journey 71's edges — a partial floor, an empty cache with the floor enabled
     (one span, not two), and a cache with exactly one in-mode bar.
- **Exit condition:** the new suite green **and** `tests/test_backfill_service.py
  tests/test_d27_backfill_granularity.py tests/test_d42_day_presence.py tests/test_d42_depth_floor.py
  tests/test_d42_mode_cache.py tests/test_d42_nonregression.py tests/test_d48_planner_probe.py
  tests/test_p12_planner_probe.py tests/test_p19_prefetch_depth.py tests/test_p19_prefetch_honesty.py
  tests/test_history_backfill.py tests/test_history_backfill_loadpath.py` green, **unchanged**;
  `git diff --name-only` ⊆ `services/backfill_service.py` + the new suite.
- **Do not:** touch `find_missing_spans`, `_build_span`, `_floor_missing_span`, `present_days`'
  signature/futures branch, `bar_period_seconds`, `floor_bar_budget`, `TRAILING_BAR_GRANULARITY_DAYS`
  or `TIMEFRAME_CONFIG`; merge or sort spans into a union; change `MissingSpan`/`RequestPlan` fields;
  de-duplicate anywhere outside `plan_requests`; import anything new (no DB, clock or Qt); re-baseline a
  red existing assertion (stop and escalate instead — AP-P27-4).

#### P27-02 — D78: the prime's backstop is armed for the retry's own deadline — size S

- **Covers:** AC-D78.1, AC-D78.2, AC-D78.3, Journey 72, A231, DG135, R172.
- **Depends on:** nothing (file-disjoint from P27-01; must precede P27-03).
- **Files:** `ui/ticker_session.py` (two module constants, one helper, `prime_aggregator`'s deferral
  branch and its comments), a new `tests/test_d78_prime_retry_reachable.py`.
- **Deliverables, in this order:**
  1. **The derived deadline (S-P27-3).** Module constants beside the existing prime constants:
     `_PRIME_BACKSTOP_MS = 15_000`, `_PRIME_RETRY_GRACE_MS = 1_000`; helper
     `def _prime_backstop_ms(retry_ms: int) -> int: return max(_PRIME_BACKSTOP_MS, retry_ms +
     _PRIME_RETRY_GRACE_MS)` with a docstring stating that the backstop is armed for the retry's own
     deadline so it can never pre-empt it.
  2. **The one place the two timers are armed.** In `prime_aggregator`'s `PacingExceeded` branch:
     compute `retry_ms = max(1000, int(wait_s * 1000))` **once**, pass it to
     `QTimer.singleShot(retry_ms, self._on_prime_retry)` (same call shape — the P7 test double pins
     one `singleShot`) and start the backstop with `self._prime_timer.start(_prime_backstop_ms(
     retry_ms))`. The issued-prime branch keeps `self._prime_timer.start(_PRIME_BACKSTOP_MS)`.
     Rewrite the surrounding comment: the backstop covers the retry's deferral **and** the answer to an
     issued prime; the retry is the first path, never dead code.
  3. **The suite** `tests/test_d78_prime_retry_reachable.py` — a fake clock/host with a stub
     `md_manager` counting `req_historical_data` calls, and a `historical_wait_seconds` stub returning a
     chosen `PacingExceeded.wait_seconds`. Cases: (a) AC-D78.1 with `wait=40`: after the refusal
     `_prime_retry_pending` is `True` and `_prime_timer.interval() == 41_000`; at 15 s (the old
     backstop) the retry is still pending and nothing was attached; at `wait − ε` the same; at the wait
     the retry runs and a priming request is issued (`_prime_req_id` set). (b) the same with `wait=2`:
     the interval is exactly `15_000` (today's value preserved) and the retry fires at 2 s. (c) the
     boundary `wait=15`: interval `16_000`, retry fires first. (d) AC-D78.2 — an issued prime that
     never answers: the backstop attaches exactly once (`host` spy) and no second request follows.
     (e) AC-D78.3 — for several waits, the clock time from refusal to (issue or attach) never exceeds
     `wait + 1 s + 15 s`. (f) Journey 72's edges — the retry itself refused (fail open once, no third
     attempt), a new load during the deferral (the `singleShot` callback is a no-op and the new load's
     own prime governs), a disconnect during the deferral leaves the pending callback harmless.
- **Exit condition:** the new suite green **and** `tests/test_p7_w2_prime.py
  tests/test_d28_3_historical_pacing.py tests/test_p7_w4_deferral.py tests/test_d27_aggregator_priming.py
  tests/test_d67_forming_candle.py tests/test_prime_retry_pacing.py green, **unchanged**;
  `git diff --name-only` ⊆ `ui/ticker_session.py` + the new suite.
- **Do not:** change `_on_prime_timeout`, `_on_prime_retry`, `_fail_open_prime` or `prepare_load`;
  remove the retry; lengthen the *issued*-prime bound; add a settings key; touch the wave, the silence
  sweeper or any P26 state; add a timer.

#### P27-03 — D79 + D80 + D81: budget stamped only by a send that crossed the wire — size M

- **Covers:** AC-D79.1, AC-D80.1, AC-D81.1, AC-D81.2, Journey 73, A233, A234, R173, R174.
- **Depends on:** P27-02 (both edit `ui/ticker_session.py`).
- **Files:** `ibkr/pacing.py`, `ibkr/market_data.py`, `ibkr/id_manager.py`, `ui/ticker_session.py`
  (the `_cancel_history_requests` branch and the `_history_req_issued` ledger), `data/bar_cache.py`;
  re-baselined `tests/test_p7_w1_coalesce.py`, `tests/test_d56_taxonomy_pacing.py`; updated pacing
  doubles in `tests/test_d65_option_chain.py` and `tests/test_ibkr_contract_details_d22.py`; a new
  `tests/test_d79_d80_d81_budget_honesty.py`.
- **Deliverables, in this order:**
  1. **The gate/stamp split without a second gate (S-P27-4).** `ibkr/pacing.py`:
     `def throttle(self, *, stamp: bool = True) -> bool:` — the reservation branch is unchanged except
     that it `return True`; otherwise `request_wait_seconds()`, raise `PacingExceeded(wait)` when
     positive, `if stamp: self.record_request_slot()`, `return False`. The docstring states the two
     modes and that `stamp=False` is for callers that stamp after their own send.
  2. **The four generic request paths.** In `req_mkt_data`, `req_contract_details`,
     `req_sec_def_opt_params` and `req_matching_symbols`: `self._require_api_ready()` →
     `reserved = pacing_manager.throttle(stamp=False)` → `req_id = id_manager.get_id()` →
     `try: self.client.req…(…)` / `except Exception: id_manager.release_id(req_id); raise` →
     `if not reserved: pacing_manager.record_request_slot()` → `return req_id`. Docstrings state the
     order and cite the historical path's existing rule. In `req_historical_data`: move the existing
     `wait = pacing_manager.historical_wait_seconds(); if wait > 0: raise PacingExceeded(wait)` block
     **in front of** `id_manager.get_id()`; the send and `record_historical_slot()` stay where they are.
  3. **The id rollback.** `ibkr/id_manager.py`: `def release_id(self, req_id: int) -> bool:` — under the
     lock, `if self._next_id - 1 == req_id: self._next_id = req_id; return True` else `return False`,
     with a docstring stating that only the newest allocation can be rolled back and that a rolled-back
     id was never sent.
  4. **The retired refund (S-P27-5).** `ibkr/pacing.py`: delete `refund_historical_slot` (update any
     docstring that names it). `ui/ticker_session.py`: delete the
     `if req_id not in self._history_req_issued: pacing_manager.refund_historical_slot()` lines and
     restate that comment as the rule ("the slot was recorded after the send; a wave never refunds");
     delete `_history_req_issued` (declaration and the comment block that describes it, the clear in
     `_cancel_history_requests`, the in-place reset, the `discard` in `_register_history_request`) and
     `mark_history_request_issued` together with its two call sites (`_issue_wave_chunks`,
     `_reissue_historic`).
  5. **The dead cache read (S-P27-6).** `data/bar_cache.py`: delete `get_last_timestamp` and the
     `Optional` import that only it used (verified: no other reference in the file).
  6. **The re-baselined cases, minimal and named.** `tests/test_p7_w1_coalesce.py`'s pre/post-issue case
     keeps its cancel-tag half and asserts the retired rule instead: two slots recorded, one pre-issue
     and one post-issue id cancelled, the slot count is **unchanged (2)** and both ids are superseded;
     the refund-half and the `_history_req_issued` line go. `tests/test_d56_taxonomy_pacing.py`'s T33
     keeps "both legs consumed a slot" (`len(pacing_manager._hist_times) == 2`) and drops the refund
     counter and the issued-set assertion. The two pacing doubles gain the keyword-only parameter
     (`def throttle(self, *, stamp=True)`), counting calls as they do today.
  7. **The suite** `tests/test_d79_d80_d81_budget_honesty.py` — a fake client whose chosen call raises,
     a fake `id_manager` wrapper over the real `IdManager`, a monkeypatched clock. Cases: (a) AC-D81.1
     — a successful send, then a raising one, then a successful one: the interval between (1) and (3)
     is one minimum interval (the failed attempt consumed none) and the budgets are unchanged by it.
     (b) AC-D81.2 — the id sequence has no gap: after the failing send the next successful request
     receives the id the failed attempt took. (c) `release_id`'s guard — releasing a non-newest id
     returns `False` and changes nothing. (d) AC-D80.1 — the two-request fixture: both requests issued
     (two slots), both cancelled, the slot count is unchanged and no refund symbol exists on the
     manager. (e) AC-D79.1 — `not hasattr(BarCache, "get_last_timestamp")` **and** a static scan over
     `data/`, `services/`, `ui/` for `MAX(ts)` queries against `bars` that filter `symbol` and
     `timeframe` without `ext_hours` (R174: include `tests/` and repo-root probes in the scan).
     (f) the batch contract — inside `pacing_manager.generic_batch(3)`, three `req_mkt_data` sends
     consume three reservation units and leave `_last_req_time` untouched, and the batch's exit stamps
     once (AR-P27-5).
- **Exit condition:** the new suite green and the two re-baselined cases green **and**
  `tests/test_d28_pacing.py tests/test_d71_replay_transaction.py tests/test_d65_option_chain.py
  tests/test_ibkr_contract_details_d22.py tests/test_d28_3_historical_pacing.py
  tests/test_d56_taxonomy_pacing.py tests/test_d56_silence_retry.py tests/test_d56_fencing.py
  tests/test_p7_w1_cap.py tests/test_p7_w1_coalesce.py tests/test_p7_w3_wide.py
  tests/test_history_backfill_loadpath.py tests/test_id_manager.py` green;
  `git diff --name-only` ⊆ the five production files + the two re-baselined files + the two doubles +
  the new suite.
- **Do not:** change any pacing constant or the shape of `historical_wait_seconds`,
  `record_historical_slot`, `realtime_*`, `generic_wait_for_batch` or `generic_batch`; keep or replace
  the refund with an "exact" variant (the resolution is retirement); add a second gate method; change
  the cancel tags, the generation stamping, `_prune_cancel_tags`, the wave lifecycle or any P26 state;
  re-baseline any assertion other than the two named cases (stop and escalate — AP-P27-4); touch
  `config/settings.py`.

#### P27-04 — records and the phase fence — size S

- **Covers:** AC-D83.2, the phase's own evidence record.
- **Depends on:** P27-01, P27-02, P27-03.
- **Files:** a new `tests/test_p27_fence.py`; `docs/` records; `docs/codebase-map.md`'s P27 note.
  **No production file.**
- **Deliverables:**
  1. **The fence suite** `tests/test_p27_fence.py`, one assertion per named artefact:
     `requirements.md` still carries `This is an existing repository.`, the `D41`–`D76` record
     (presence per id in a heading — the record is mixed, exactly as P26-04 records), P27's own
     `#### D77`–`#### D83` entries, `Journey 71`–`Journey 73`, `AC-D1.1`–`AC-D76.3` **plus**
     `AC-D77.1`–`AC-D83.2`, `A1`–`A229` plus `A230`–`A234`, `R1`–`R169` plus `R170`–`R174`, and the
     `Current Tech Stack` section.
  2. **The pinning assertions** (read off the modules, not off prose): the five settings values
     (`MAX_REQ_PER_SEC`, `HISTORICAL_MIN_INTERVAL_S`, `MAX_HISTORICAL_PER_600S`,
     `MIN_INTRADAY_SESSIONS`, `SESSION_BAR_CAP`); `per_load_historical_cap() ==
     max(1, settings.MAX_HISTORICAL_PER_600S // 4)`; `_WATCHDOG_BASE_WINDOW_FRACTION == 1 / 5` and
     `_WATCHDOG_MARGIN_WINDOW_FRACTION == 1 / 20`; `_PRIME_BACKSTOP_MS == 15_000`;
     `_prime_backstop_ms(2_000) == 15_000`, `_prime_backstop_ms(40_000) == 41_000`;
     `TIMEFRAME_CONFIG`'s nine keys and durations unchanged; `plan_requests` still pure (the
     isolated-interpreter Qt-free case stays green). No literal file/line counts, no phase hash.
  3. **The delta-scope record** — a build-record artefact (P24/P25/P26 precedent), not a hash-pinned
     test: the wave records `git diff --name-only 70b16f2` and requires it to be a subset of
     {`services/backfill_service.py`, `ui/ticker_session.py`, `ibkr/pacing.py`,
     `ibkr/market_data.py`, `ibkr/id_manager.py`, `data/bar_cache.py`, the four new suites, the two
     re-baselined files, the two pacing doubles, `docs/`}. Anything else is a scope breach to escalate,
     not to justify.
  4. **Full offscreen suite green** recorded in the wave result; no live gate is claimed or listed
     (the requirements declare none).
- **Exit condition:** the fence suite green, the full offscreen suite green, and the recorded diff
  listing matches the allowlist exactly.
- **Do not:** edit `docs/requirements/**`; assert a phase commit hash or a file/line count; add an
  assertion that a later phase (P28's lifecycle work) would redden.

### Assumptions

- **AP-P27-1 — baseline, and what a P26 review fix may change.** The build starts from HEAD `70b16f2`
  or a descendant that carries only P26 review fixes. Because P26's review is open, the wave re-reads
  `ibkr/pacing.py` (`throttle`, `generic_batch`, `reset_for_tests`), `ibkr/market_data.py` and
  `ui/ticker_session.py` before editing: if a P26 fix has changed the batch's shape, the
  stamp-after-send split (S-P27-4) adapts to the **new** shape and the reservation contract is
  re-pinned in the new suite. P27 does not revert or re-decide anything P26 owns.
- **AP-P27-2 — `AC-D77.1`'s "the union equals the union of the input spans" is read as
  "unchanged by the change, and containing every input span".** Chunk-granularity means each plan
  covers a whole configured duration ending at its anchor, so the earliest chunk of a span starts
  *before* the span's `start_ts` — today and after P27. Literal equality between plan coverage and span
  coverage is therefore false before the change too; the constraint that matters ("the set of covered
  intervals is identical before and after; only the request count changes") is what the suite asserts.
  Recorded as FI-P27-1 for the analyst.
- **AP-P27-3 — the one threshold is 1.5 periods, and the `now` cap stays inclusive.** A232's exception
  is applied literally: a window capped by *now* keeps `t <= now_ts` (so today's open session is not
  over-fetched), while every other edge is half-open. The docstring states both halves.
- **AP-P27-4 — existing assertions are not re-baselined except the two named D80 cases.** Every other
  red is a stop-and-escalate. The two named cases *encode the defect* (one cannot tell whose slot the
  refund popped; the other counts a refund that no longer exists), so leaving them would keep asserting
  behaviour the phase removes.
- **AP-P27-5 — `AC-D80.1`'s parenthetical is the adopted branch.** "the path is removed and its caller
  with it" is what P27 does; the AC's measurable still holds in its two-request form — after cancelling
  a pre-issue and a post-issue id the slot count is unchanged, so the other request's slot survives.
  Recorded as FI-P27-2 so the analyst can confirm the branch.
- **AP-P27-6 — the retry's grace tick is a module constant, not a setting.** `_PRIME_RETRY_GRACE_MS =
  1_000` lives beside `_PRIME_BACKSTOP_MS` in `ui/ticker_session.py`; it exists so a wait of exactly
  15 s (and any wait whose retry lands on the backstop's instant) cannot be pre-empted by timer
  ordering. No `config/settings.py` key is added.
- **AP-P27-7 — `throttle`'s default path is a compatibility contract.** `stamp=True` must behave
  byte-identically (raise on a closed gate, stamp on success, consume a reservation unit inside a
  batch) because `test_d28_pacing.py` and P26's replay suite pin it; the new parameter and return are
  additions, and the return is ignored by every existing caller.
- **AP-P27-8 — the phase has no live gate.** The requirements declare none; every criterion is
  offscreen with injected timestamps and a monkeypatched clock. No owner observation is claimed.
- **AP-P27-9 — the four waves are ordered, not parallel-decomposed.** `P27-02` → `P27-03` because both
  edit `ui/ticker_session.py`; `P27-01` may run alongside both because it touches one other file; the
  Task Manager may serialise all four if it prefers one chain. `P27-04` runs last, always.
- **AP-P27-10 — no user-visible wording changes.** The per-load-budget message, the pacing-limited
  lines, the prime's warning and the `AC-D16.4` shortfall keep their wording; P27 changes how many
  requests are made and when budget is charged, never what the user reads.

### Flagged Issues

- **FI-P27-1 — `AC-D77.1`'s "the union of the plans' covered intervals equals the union of the input
  spans" cannot hold literally, before or after P27 (non-blocking under AP-P27-2).** A plan's anchor is
  the span end and its coverage is one configured duration backwards, so the oldest chunk of every span
  reaches before the span's start (that is the accepted chunk-granularity over-fetch the cache's PK
  makes harmless). Plan therefore asserts the constraint the requirements state in prose — the union is
  identical before and after, and no input interval is dropped — plus a containment check. Suggested
  direction: the analyst rewords `AC-D77.1`'s "equals" as "unchanged, and covering", or states the
  chunk-granularity exception; a literal reading would need a planner that truncates the oldest chunk,
  which `TIMEFRAME_CONFIG`'s fixed durations cannot express.
- **FI-P27-2 — three existing APIs are retired rather than repaired (non-blocking; A233's preferred
  branch and D79's own preference, recorded for confirmation).** `AC-D80.1` allows either "frees
  exactly its own slot" or "the path is removed and its caller with it", and D79 allows either deletion
  or a mode-aware read with a caller. P27 takes the removal branch for both: `refund_historical_slot`,
  its `_cancel_history_requests` branch and the `_history_req_issued` / `mark_history_request_issued`
  ledger that gated it are deleted (with the slot recorded after the send — D81 makes this uniform — a
  request that never crossed the wire holds no slot, so an exact refund returns `False` by
  construction and the API can only be dead code or a thief), and `BarCache.get_last_timestamp` is
  deleted (zero callers in production and in `tests/`). Consequences to be confirmed, not assumed:
  P26's frozen list still names `mark_history_request_issued`, so the deletion carries a
  `[revises P26]` label and that frozen-list entry becomes history — P26's own requirements, ACs and
  decisions are untouched, and its contract ("a post-issue cancel keeps its slot") is preserved by the
  stronger rule that nothing is ever refunded; and two existing test cases are re-baselined (AP-P27-4)
  because they encode the retired behaviour. If the owner prefers a live refund path or a live
  mode-aware read, each is a new requirement (a slot-owner ledger for a pre-issue window that does not
  exist today; a caller the application does not have), not a P27 edit.
- **FI-P27-3 — the unified trailing threshold requests a band the old rule skipped (non-blocking,
  deliberate).** A trailing hole between 1.5 and 2 periods is today *not* reported and after P27 *is*
  (`> 1.5 × period` instead of `>= 2 × period`). This is the direction `AC-D82.2` and the module
  docstring require (one number for one edge), and its cost is bounded by one chunk per affected
  day-load; R171's opposite worry (a real one-period hole stopped being repaired) does not arise —
  a hole of exactly one period is reported by neither rule. Recorded so the owner can see the budget
  effect is intentional.

Status: READY_FOR_VALIDATION
