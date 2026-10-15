# Implementation Plan — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

> **Document state (2026-10-14).** This file is the canonical plan. Its **first section** is the
> approved **D23** plan (Phases 1–3, `Status: READY_FOR_TASK_MANAGER`); below it, the
> **as-built** records for **D24–D28** (as-built / **OWNER-APPROVED 2026-10-14**, Q41) and
> **D36–D40** (as-built 2026-10-13, Code Reviewer APPROVED, acceptance criteria **authored**
> 2026-10-14 per Q45/DG46) are carried, followed by a **plan-vs-code verification** section
> (Q41/DG53). **All of D1–D40 are built and merged to `main`** (the D40 merge is
> `b366b19`; `origin/main` is now `262ec81`, after `7566860` → `99fb8fa` → `262ec81`). The
> per-run "gated in TWS" planning constraint is **retired** (Q42/DEC-4);
> pop-out always-on-top defaults **OFF** (`AC-D24.10`, Q43); the D37 depth heatmap defaults
> **ON** (A67, Q44). No "DRAFT" / "unmerged" / "pending owner review" wording remains for
> D24–D28.

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
  header context menu) — `AC-D24.10` / A66, matching `ui/popout_window.py:56`/`:289`.

**As-built feature detail (verified against the merged code 2026-10-14 — see the plan-vs-code
verification section at the end of this file):**

| Feature | As-built | ACs |
|---|---|---|
| **D24** pop-out chart windows | `ui/popout_window.py::PopoutChartWindow` — chrome-free (28px header `SYMBOL · timeframe · mode` + close; no toolbar/docks/status bar), `ChartPanel(editable=False)` (drawing / alarm-placement / study / timeframe / mode controls disabled — interaction only; overlays still render, crosshair/zoom/pan work); timeframe/mode/ext-hours frozen at creation (A56); `MAX_POPOUTS = 10` (`config/settings.py:42`) — the 11th is **refused with a status-bar message** (`ui/main_window.py:845–851`), the affordance is *not* `setEnabled(False)`-ed; opened while disconnected → cached bars render and the subscription starts on connect, with **no per-pop-out "connecting" indicator** (main window `conn_badge` only); always-on-top default OFF with per-window toggle; `AC-D24.9` restore via the additive `popouts` table + `data/popout_store.py`; one refcounted `reqRealTimeBars` per symbol; per-symbol sync of bars/studies/zones/lines/alarms with the main chart the sole writer (A64); `load_chart(symbol, timeframe, extended_hours)` parameterised | `AC-D24.1`–`AC-D24.10` |
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
   specify a default; the code defaults ON (`ui/chart_panel.py:368` adds `DepthHeatmapItem`
   unconditionally, `:370` `_depth_enabled_ui = True`). The reviewer recommended **OFF** for
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
| D24 pop-out cap (`AC-D24.5`) | `architecture.md` and this plan said the pop-out action is **"disabled at the cap"** | Rewritten: the 11th pop-out is **refused with a status-bar message** (`ui/main_window.py:845–851`); the affordance is **not** `setEnabled(False)`-ed |
| D24 session signals | `architecture.md` named a single **`bars_updated`** signal | Rewritten to the shipped pair: **`bar_updated`** (incremental) **and `bars_refreshed`** (full replace) — `ui/ticker_session.py:65–73` |
| D24 disconnected pop-out | Requirement asserted a **per-pop-out "connecting" indicator** | Removed/corrected: cached bars render and the subscription starts on connect; there is **no per-pop-out indicator** — only the main window's `conn_badge` (`ui/main_window.py:295`) |
| D37 depth heatmap default | This plan said **"owner decision pending … awaiting owner confirmation 2026-10-13"** | Rewritten as **owner-confirmed ON 2026-10-14** (Q44/A67); matches `ui/chart_panel.py:368`/`:370`; D36 footprint stays OFF |
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
(`ui/ticker_session.py:65–73`), pop-out cap refusal (`ui/main_window.py:845–851`),
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
the pop-out refusal message text (`ui/main_window.py:845–851`); `CACHEABLE_SYMBOLS` +
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
`ibkr/market_data.py` at pre-D24 line numbers; all three files have grown. A "Line-citation
currency" note in `architecture.md` bounds this — the *symbols* are verified present, the line
numbers are indicative.

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
