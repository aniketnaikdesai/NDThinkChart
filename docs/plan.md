# Implementation Plan — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

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
| `AC-D44.2` (click the bar → expand to the previous width, re-clamped) | Phase 1 — `expand_requested` + `collapsed_changed` → `_on_watchlist_collapsed_changed`; `_watchlist_width` never overwritten while collapsed; guard asserts `dock.width() == clamp(W)` incl. the min-150 and at-cap edge cases | Covered |
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
| `ui/main_window.py` **(file-group C — the transition wiring)** | connect `panel.collapsed_changed` → `_on_watchlist_collapsed_changed`: swap the dock's title-bar widget (`collapsed_handle` while collapsed, `header_bar` on expand — un-hiding `header_bar` as it is restored, so the title bar is never a hidden widget), relax/restore the minimum widths (`panel` + `dock` → 30 / 150), then `_resize_docks_guarded` + `QTimer.singleShot(0, self._apply_dock_widths)` — the `_sync_right_dock_collapse` sequence (`S24`, `S25`) | **`tests/test_dock_widths_collapsed_d44.py` is owned here** (it asserts the end-to-end transition: collapse → 30px, survive a resize/drag, expand → `clamp(W)`, the min-width flip, no key) — a **different wave** from file-group A (the same production file) |
| `tests/test_dock_widths_collapsed_d44.py` **(new — file-group C)** | `AC-D44.5`/`AC-D44.2`/`AC-D44.7` + `AC-D44.1`'s width measurable: collapse at a known `W` → `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`; still the collapsed width after a window `resizeEvent` **and** after the drag-event path (`_on_dock_drag_event`); expand → `dock.width() == clamp(W)` (incl. the collapse-from-150 and collapse-from-cap edge cases); the dock's min width is 30 while collapsed and 150 after; **no** collapse key in `QSettings`; the `CHART_MIN_WIDTH` invariant in both states. **Must be RED at `0c4d478` for the right reason** | — |
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
  `dock.width() == clamp(W)`; collapse-from-150 → expand restores 150; collapse-from-cap → expand
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

Status: READY_FOR_TASK_MANAGER
