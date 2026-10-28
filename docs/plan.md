# Implementation Plan — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

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
