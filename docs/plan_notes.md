# Plan Notes

> Owned by the Plan Artifact Editor & Validator. The Requirements Analyst reads this
> file. Entries record requirements or planning gaps found during validation.

## RG-001 — D13/D14 Defect Register entries are missing from `requirements.md`

**Requirement/Journey:** D13 (watchlist resizable to 50% with persistence) and D14
(watchlist double-click loads chart); Journeys 14 and 15; `AC-D13.1`–`AC-D13.3` and
`AC-D14.1`–`AC-D14.3`.

**Problem:** `docs/requirements/requirements.md` contains the D13/D14 user journeys
(Journey 14 and Journey 15), but the **Defect Register has no `### D13` or `### D14`
block**. As a result the authoritative acceptance criteria (`AC-D13.1`–`AC-D13.3`,
`AC-D14.1`–`AC-D14.3`), the Q25–Q29 decisions, and the watchlist assumptions and
risks are absent. The Assumptions Log now reuses `A17` for D15 and the Risks table
reuses `R15` for D15, so the numbering also collides. The D13/D14 content was
present earlier (referenced by the canonical plan and architecture) and was lost in
a subsequent requirements rewrite.

**Why it cannot be satisfied as currently written:** `docs/plan.md` (Phase 4) and
`docs/architecture.md` cite `AC-D13.1`–`AC-D14.3` and the watchlist assumptions as
authoritative. Task Manager is required to link every task to a real acceptance
criterion; those criteria do not currently exist in the requirements document, so
Task Manager could not build valid D13/D14 tasks without inventing them — which
would violate the "no invented requirements" rule.

**Suggested Direction:** restore the D13 and D14 Defect Register blocks (Reported,
Observed, Decisions from Q25–Q29, `AC-D13.1`–`AC-D13.3` / `AC-D14.1`–`AC-D14.3`,
Edge Cases) into `docs/requirements/requirements.md` after D12 and before D15.
Restore the watchlist assumptions as `A17` (D13 width, Q25/Q26), `A18` (D14
double-click, Q27/Q28), `A19` (D14 no-op, Q29), and move the D15 assumption to
`A20`. Restore risks `R15`–`R17` (D13 crowding, D14 accidental reload, D13
floating-vs-docked) and renumber the D15 risk to `R18`. The substance is recoverable
from `docs/plan.md` Phase 4 and from this conversation's requirements history.

**Status:** addressed — resolved 2026-09-20. The Requirements Analyst restored the
D13 and D14 Defect Register blocks (`### D13`, `### D14`) with `AC-D13.1`–`AC-D13.3`
and `AC-D14.1`–`AC-D14.3`, restored the watchlist assumptions as `A17`–`A19`, moved
the D15 assumption to `A20`, and restored risks `R15`–`R17` (D15 risk now `R18`).
Validation re-run passes; the block is cleared.

**Escalation:** ESCALATED_TO_REQUIREMENTS — resolved 2026-09-20.

---

## RG-002 — D8 nice-number family contradicts its own examples and fixtures

**Requirement/Journey:** D8 (`AC-D8.1`, `AC-D8.4`, `AC-D8.5`, D8 edge cases),
Journey 9; A24; ESC-003/ESC-008. Also blocks the Plan revision's Phase-1 Amendment A.

**Problem:** `AC-D8.1` defines the volume ceiling as "a 1/2/2.5/5×10^k value that is
`>= max_vol*1.1`". But the requirement's own examples and the retained regression
fixture assert values that are **not** in that family:
- `AC-D8.4` low-volume edge case: `nice_max(3_000) = 5000` (fine), but the D8 edge
  cases state "a max just below a boundary (e.g., 1.05M) rounds up to the next
  1/2/2.5/5×10^k value (`1.5M`)". `1.5M` is `1.5×10^6`, i.e. a `1.5` mantissa — it is
  **not** a 1/2/2.5/5×10^k value.
- `AC-D8.5` high-end example: "`10.5M → 15M`". `15M` is a `1.5` mantissa — likewise
  **not** a 1/2/2.5/5×10^k value.
- The remaining fixture `tests/test_volume_linear.py:61`
  (`_nice_volume_max(1_050_000) == 1_500_000`) encodes the same `1.5M` value.

**Why it cannot be satisfied as currently written:** Under the stated formula
(smallest `1/2/2.5/5×10^k` candidate `>= max_vol*1.1`), the answers are
`1.05M → 2.0M` and `10.5M → 20.0M`. No generator can return `1.5M`/`15M` for these
inputs while also being the smallest `{1,2,2.5,5}` candidate. The Plan revision
(`architecture_proposal.md` §3.2) repeats the contradictory set — its candidate list
omits the `2` mantissa (`…, 100, 250, 500, 1000, 2500, …`) while both proposals retain
the `1_050_000 → 1_500_000` fixture. Task Manager cannot write a D8 test that satisfies
`AC-D8.1` and `AC-D8.4`/`AC-D8.5` simultaneously without inventing the family.

**Suggested Direction:** Decide the canonical nice family explicitly:
- **Option A — strictly `{1, 2, 2.5, 5} × 10^k`:** correct `AC-D8.4`/`AC-D8.5` and the
  D8 edge cases (`1.05M → 2M`, `10.5M → 20M`), and the retained
  `1_050_000 → 1_500_000` fixture is updated (Build-owned). Re-check the `50M` case
  (`50M → 100M` under this family).
- **Option B — a family that includes `1.5`/`7.5`** (as the old fixed list did): state
  it explicitly in `AC-D8.1` (e.g. `1/1.5/2/2.5/5/7.5 × 10^k`) so `1.05M → 1.5M` and
  `10.5M → 15M` are valid, and reconcile the `50M` case (next `7.5`-family value is
  `75M`, which is *coarser* than the `60M` the requirement rejects — decide the rule).

Once Requirements fixes the family, Plan re-validates Phase-1 Amendment A against it.

**Status:** RESOLVED — 2026-09-27. The Requirements Analyst pinned the family to
**`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (`AC-D8.1`, A24), reproducing every confirmed
value (`750K`, `1.5M`); the `10K` floor is removed (smallest generated value **`100`**)
and the old list is retained only as a test fixture. Revision 2 of the Plan proposal
(`docs/architecture_proposal.md` §3.2/§3.4) now uses the one formula and agrees on every
example and fixture — including `1_050_000 → 1_500_000` and `50M → 75M`. Validation
pass 2 confirms **RC-1** is closed. Block cleared.

**Escalation:** ESCALATED_TO_REQUIREMENTS — resolved 2026-09-27 (folded into
`AC-D8.1`/`A24`).

---

## RG-003 — `ALARM_PLACING → ZOOMING` transition is unspecified (PA-R1)

**Requirement/Journey:** D3 (`AC-D3.7`, `AC-D3.8`), Journey 4; Plan assumption PA-R1.

**Problem:** The Plan revision makes `ChartMouseRouter` a single-valued `RouterMode`
state machine whose transition table must be total. The requirements decide
`DRAWING↔ZOOMING` (`AC-D3.7`, both directions) and `ZOOMING → ALARM_PLACING`
(`AC-D3.8`), but are silent on the corner **invoking the magnifier while alarm
placement mode is active** (`ALARM_PLACING → ZOOMING`). Plan derived TR-9 (exit alarm
mode and enter `ZOOMING`) and flagged it as PA-R1 because the table must be total to be
testable.

**Why it matters:** TR-9 encodes required runtime behaviour that will be tested; it
should be a confirmed requirement rather than a plan-level assumption, so no reader
mistakes an invented transition for settled intent.

**Suggested Direction:** Requirements Analyst confirms (or corrects) PA-R1: activating
the magnifier while `ALARM_PLACING` exits alarm mode and enters `ZOOMING`, consistent
with the "one mode at a time" precedent (`main_window._on_draw_tool_changed` unchecks
alarm). If confirmed, fold it into D3's transition semantics alongside `AC-D3.7`/
`AC-D3.8`.

**Status:** RESOLVED — 2026-09-27. The Requirements Analyst answered Q36 with **option
(b)** and recorded it as **`AC-D3.9`**: invoking the magnifier while `ALARM_PLACING` is
active is **REFUSED** — the router stays in `ALARM_PLACING`, the pending placement is
**not** cancelled, and a status-bar hint is shown (the `ALARM_PLACING + magnifier →
ALARM_PLACING` cell that makes the transition table total). This supersedes Plan's
derived TR-9 and **retires PA-R1**; revision 2 rewrites TR-9 accordingly. Validation
pass 2 confirms the cell is total and refuses zoom. Block cleared.

**Escalation:** ESCALATED_TO_REQUIREMENTS — resolved 2026-09-27 (folded into `AC-D3.9`).

---

## FI-D16-1 — AC-D16.1's per-bar cadence measurable cannot hold for illiquid symbols

**Requirement/Journey:** `AC-D16.1` (measurable clause), against Q39 / A30 ("any symbol");
D16, Journey 17; raised by Plan as Flagged Issue FI-D16-1.

**Problem:** `AC-D16.1`'s measurable clause requires that "the maximum inter-bar gap
**within** a trading session does not exceed one bar period", asserted parameterized over
all six timeframes and at least two symbols. IBKR omits bars for periods with no trades, so
a thinly traded symbol (or an empty pre-market period) legitimately has inter-bar gaps
larger than one bar period even with a complete, correct bar list. Asserting cadence for
"any symbol" against real illiquid data would fail on correct data and would push the fix
toward fabricating/interpolating bars — which `AC-D16.3` and `AC-D16.4` explicitly forbid.

**Why it cannot be satisfied as currently written:** taken literally over live illiquid
symbols, the cadence clause contradicts the requirement's own no-fabrication clauses
(`AC-D16.3`/`AC-D16.4`). However, the measurable procedure in `AC-D16.1` is explicitly an
**offscreen test with a seeded cache and a stubbed historical feed**, so the test controls
the bar series and cadence is assertable there.

**Resolution (accepted by Validator, 2026-10-02 — no Requirements escalation):** the
cadence assertion is applied to the **stubbed/liquid test scenarios** (the `SPY 5 mins`
repro and a liquid second symbol per timeframe), and for illiquid symbols the requirement is
satisfied by **session-presence** continuity (every trading session has ≥1 bar). The
mechanism stays symbol-generic (Q39). This keeps the fix honest and matches the defect
class. Carried into `docs/plan.md` as `PA-D16-7` and into `docs/architecture.md`
(detection granularity + risks).

**Status:** addressed — accepted interpretation; no escalation.

**Escalation:** none (satisfiable under `AC-D16.1`'s offscreen stubbed-feed measurable
clause).

---

## FI-D16-2 — "any symbol" vs an equity holiday calendar for instruments that trade US equity holidays

**Requirement/Journey:** Q39 / A30 ("any symbol"), `AC-D16.3` (holidays are closures);
D16, Journey 17; also `design_gaps.md` DG1 (open); raised by Plan as Flagged Issue FI-D16-2.

**Problem:** a calendar that treats a US equity holiday as non-trading is wrong for futures
(which trade some of those days), while a per-instrument calendar is not feasible from the
current contract model. One calendar cannot be simultaneously correct for equities and for
all futures. So the literal "any symbol" continuity guarantee cannot hold for every
instrument under a single equity calendar.

**Why it cannot be satisfied as currently written:** a single equity holiday calendar is
not simultaneously correct for equities and futures. But the requirement does not ask for
per-instrument session modelling; Q39/A30 asks that the **fix and its verification be
symbol-generic**, and D1 already accepted the equity-session model as the default for every
symbol (A7 / DG1 / `services/session_service.py`).

**Resolution (accepted by Validator, 2026-10-02 — no Requirements escalation):** D16's
continuity guarantee is scoped to the **accepted equity-session model** (the existing
DG1/A7/D1 default), which is a standing accepted decision, not a new one. The futures
caveat is recorded (PA-D16-3, architecture risk row, DG1 remains the tracked open design
gap). If truly symbol-generic per-instrument session handling is ever required, that is a
separate requirements change for the Requirements Analyst — it is not needed to satisfy
`AC-D16.1`–`AC-D16.6` for the reported defect and the accepted model.

**Status:** addressed — accepted interpretation; no escalation.

**Escalation:** none (satisfiable under the accepted equity-session default; futures caveat
recorded, DG1 retained).

---

## FI-D22-1 — D22: requirements prose says `watchlist_panel.clear()` runs "on disconnect"; the repo runs it on close

**Requirement/Journey:** D22 / Journey 27; `AC-D22.4`–`AC-D22.7`, `DG40`; the descriptive prose at
`docs/requirements/requirements.md:2121` ("`clear()` … called on disconnect,
`ui/main_window.py:2107`") and `design_gaps.md` DG40 ("`_on_disconnected` → `watchlist_panel.clear()`
`:2107`").

**Problem:** The repository (authoritative) shows `watchlist_panel.clear()` is called from
**`closeEvent`** (`ui/main_window.py:2107`), while `_on_disconnected` (`:550–562`) does **not** clear
the panel. The requirements prose's "on disconnect" is an imprecise restatement of the *call site's
line number*, which is in fact the close path. This is a wording imprecision in a **descriptive**
paragraph, not in any `AC-D22.*` acceptance criterion.

**Why it cannot be satisfied as written:** It can — the imprecision does not make any criterion
unsatisfiable. No `AC-D22.*` outcome depends on whether the panel is cleared on disconnect or on
close: B16b **denies adding while disconnected**, the SQLite `watchlist` table is the single source
of truth, and the canonical plan makes `_restore_watchlist` **clear-then-repopulate** (S13 /
PA-D22-6) so a reconnect faithfully reproduces the persisted set (`AC-D22.7`). The stale wording is
recorded here and in `docs/architecture.md` (D22 increment, Codebase Summary fact #3 / Non-Functional)
so it is not mistaken for a discrepancy by Build or Code Reviewer.

**Suggested Direction:** (optional, non-blocking) The Requirements Analyst may correct the
parenthetical in `requirements.md:2121` / `DG40` to "called on app close (and cleared before
repopulating on connect)". No Requirements Analyst action is required for Task Manager to proceed.

**Status:** addressed — documented as an implementation note in `docs/architecture.md`; no
acceptance criterion is affected, so no requirements change is required.

**Escalation:** none.

---

## RG-D23-1 — D23.1: architecture `S3` / task-level `AC-D22.2.3` reconciliation record (AC-D23.1.4)

**Requirement/Journey:** D23.1 / `AC-D23.1.4` (supersession + reconciliation recorded); Journey 28;
`DG45`; A53/A54; R49. This is the binding correction record, **not** a requirements gap.

**Record.** `requirements.md` D23.1 supersedes the **task-level** `AC-D22.2.3` wire-cancel mandate
and reconciles architecture row `S3` (the D23.1 correction record names the owners: Task Manager →
`docs/tasks/task-graph.json` task `D22-02`; Build → the guard + test; Plan/Validator →
`docs/architecture.md`).

- **Validator (this cycle).** Architecture `S3` is reconciled: `docs/architecture.md`
  `## D23 increment` → Tech Stack Decisions **S3 (reconciled)** rewrites
  `MarketDataManager.cancel_contract_details` to the capability-guarded, documented best-effort
  cancel (the pinned `ibapi 9.81.1.post1` exposes no `EClient.cancelContractDetails`; the
  `reqContractDetails` request path is unchanged; `ContractLookupService`'s bounded-QTimer +
  `cancel_all` local invalidation is the safety net). The D22 `S3` row carries a cross-reference note
  pointing to this reconciliation so a reader does not take the D22 wording as the current mandate.
- **Task Manager (Phase 3).** Rewrites task-level `AC-D22.2.3` (and its test description) in
  `docs/tasks/task-graph.json` (task `D22-02`) to the capability-guarded, documented cancel — in
  lockstep with the Phase-1 test change (R49).
- **Code Reviewer (after Build).** Re-verifies ESC-030 and ESC-031, flipping them `addressed`.

**Why it is not a gap:** the requirement's required behaviour is unambiguous from the source
evidence and fully implementable on the existing stack; no product/scope decision is needed.

**Status:** addressed — architecture `S3` reconciled in `docs/architecture.md` this cycle; the
Task-Manager-owned `AC-D22.2.3` rewrite is a Phase-3 task-graph edit by its owner.

**Escalation:** none.

---

- Issue: **RG-D41-1**

**Requirement/Journey:** `AC-D41.4` (Batch 18 / D41) — "…the retained order paths (**Close / Close
Group / Flatten All**, SL/TP dialogs) still build and **validate** orders with a **resolving
`ref_price`**"; together with `### D41` "Scope — KEEP" → "Retained order-path `ref_price` — KEEP
with a NEW source (Plan-level detail)" and Journey 36's postcondition ("the retained order **machinery**
still builds/validates orders for the Portfolio / SL-TP paths").

**Problem:** as written, the clause does not describe the code and has two readings (surfaced by the
Plan proposal as **FI-1**):
(1) *ratify the plan's re-homing* — the retained close/flatten path becomes gated (D26.9 disconnected
guard + `validate_order()` with `risk_reducing=True` and a `ref_price` from `_ref_price_for`), so the
retained path genuinely "builds and validates"; or
(2) *pure removal* — no behaviour change on the close path, `validate_order`/`ref_price` exercised
only by their own unit tests, and `MAX_ORDER_NOTIONAL` becomes an unused cap.
Secondarily, the clause's "SL/TP dialogs" limb is **vacuous**: `ui/stop_loss_target_dialog.py`
places **no** orders at all (verified repo-wide — no `placeOrder`/`order_registry` call in that
module; `ui/main_window.py:3446`–`:3508` `_close_position_by_id` is the app's only surviving
emitter). `tests/test_sltp_honesty.py:16`/`:24` asserts the dialog's **disclosure label**, not
non-transmission, so it does not evidence the AC's clause either way.

**Why it cannot be satisfied as currently written:** the sentence admits reading (2), but reading (2)
requires an explicit requirements-level **supersession** of the clause (Plan cannot pick "do
nothing" from a text that says "validate"), while reading (1) adds behaviour to a surviving path
inside a removal batch. The requirements' own KEEP list resolves the tension in favour of (1)
("`ref_price` … **must keep resolving** for the retained order paths"), and `DG71`/`A71` record both
the source and the mechanism as Plan-level details.

**Suggested Direction:** **no change to `requirements.md` is required.** The Validator has ruled
this cycle on the basis of the KEEP list: reading (1) stands — the D26.9 guard and the
`validate_order()` gate are re-homed onto `_close_position_by_id`, fed by
`MainWindow._ref_price_for(symbol)` over the retained D27.5 `symbol → last_price` map
(`ui/main_window.py:727`, `:2263`–`:2266`, `:609`, `tests/…`-verified), with one additive
`risk_reducing: bool = False` keyword that skips only the notional cap so a position above
USD 25,000 can still be flattened. Recorded here so a later reader does not read the clause as
unmet and does not "fix" it by adding a gate to the SL/TP dialog (which transmits nothing).
If the owner ever prefers reading (2), the correct route is an explicit `AC-D41.4` supersession note
by the Requirements Analyst — not a plan-level assumption.

**Status:** addressed — the Validator ruled on this item and the ruling stands in the cycle-2
`APPROVED` review (`docs/plan_review.md`): reading (1) applies — the D26.9 guard and the
`validate_order()` gate are re-homed onto `_close_position_by_id`, fed by
`MainWindow._ref_price_for(symbol)`, with the additive `risk_reducing` keyword; no change to
`requirements.md` and no Requirements Analyst action is required. `AC-D41.4` is therefore satisfied
as written, and the plan is approved for Task Manager.

**Escalation:** none.

---

- Issue: **FI-D44-1**

**Requirement/Journey:** `AC-D44.1` and `AC-D44.5` (Batch 19 / D44) — both phrase their measurable as
**exact equality** (`watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`); together with the repo's
established ±1px convention (`tests/test_dock_widths_d17.py:17`–`:21`: "`_apply_dock_widths` only
re-issues `resizeDocks` when the computed width differs from the current width by **more than 1px** …
so a residual of at most 1px is expected and asserted with `+1`"). Raised by the Plan proposal as
`FI-D44-1`.

**Problem:** the criteria demand exact equality while the apply path has a deliberate 1px dead-band, so
a strict `==` on **every** measurement could produce a false RED (a platform's 1px dock separator) and
make the guard untrustworthy — and, conversely, a blanket `+1` tolerance everywhere would weaken the
criterion's stated outcome.

**Why it cannot be satisfied as currently written:** it can — the tension is a *measurement* question,
not an outcome question. The criteria fix the outcome ("the bar is 30px and stays 30px"); they say
nothing about which derived/inner values may carry a 1px residual.

**Suggested Direction / ruling:** **ratified as a measurement convention — no Requirements change.**
Assert the **dock** width exactly, as the criteria write it (Validator probe, offscreen, 2026-10-16:
`resizeDocks([dock], [30])` yields **exactly 30** once the widget minimums allow it), and keep the
`+1` convention only for inner/derived measurements the criteria do not name. Recorded as
`AP-D44-4`. Two precisions carried into the canonical plan for Build: the guard asserts **after** the
apply path has run (`processEvents`), and the 1px dead-band is itself unchanged behaviour, so the guard
must not manufacture a 1px residual by its own driving sequence.

**Status:** addressed — ratified this cycle; no `AC-D44.*` clause is weakened or reinterpreted.

**Escalation:** none.

---

- Issue: **FI-D44-2**

**Requirement/Journey:** `A78` (Batch 19 / D44) — "the dock's title-bar widget presents the bar while
collapsed while keeping the dock movable (DG37)"; with `AC-D44.1`/`AC-D44.6` (the outcome: a thin,
clickable, app-palette bar that reads as a panel). Raised by the Plan proposal as `FI-D44-2`.

**Problem:** the literal reading ("the dock's title-bar widget **is** the full-height bar") is
**impossible**: Qt lays a left dock's title-bar widget out at the **top** of the dock, at the dock's
full width and the widget's own `sizeHint` height — verified by an offscreen probe by Plan and
re-verified independently by the Validator (a 28px widget occupied `QRect(0, 0, 63, 28)`), so the
title-bar slot can never hold a full-height vertical bar.

**Why it cannot be satisfied as currently written:** the *mechanism* sentence cannot be literal; the
*outcome* sentences can. `A78` itself delegates the mechanism ("the widget/title-bar mechanism is an
implementation choice"), and the requirement's own correction record offers two mechanisms —
"`setTitleBarWidget` swaps to the bar, **or** the header widget reorients".

**Suggested Direction / ruling:** **confirmed satisfied as an intent — no wording escalation.** D44's
split affordance (`S25`) puts the **full-height bar** in the dock's **content** (`panel.collapsed_bar`)
and a 30×28 handle (`panel.collapsed_handle`) in the **title-bar slot**, which keeps the dock
movable/floatable (DG37) and clickable to expand. Everything `A78` fixes is preserved; the recorded
fallback (bar-as-title-bar) remains if the handle proves problematic in build.

**Status:** addressed — ruled satisfied this cycle; recorded in `docs/architecture.md`
§ *D44 increment* (`S25`, `FI-D44-2`).

**Escalation:** none.

---

- Issue: **FI-D44-3**

**Requirement/Journey:** `A76` (Batch 19 / D44) — "the collapsed/expanded state is **NOT** persisted;
the app starts expanded" — which is **silent** on what **width** is persisted when the app is closed
**while collapsed**. Raised by the Plan proposal as `FI-D44-3`.

**Problem:** `closeEvent`'s unchanged `save_watchlist_width(self._settings, self._watchlist_width,
self._chart_area_width())` writes whichever width `_watchlist_width` holds at close time. If the
applied 30px were persisted while collapsed, the next launch's **expanded** dock would be re-clamped by
`clamp_watchlist_width` to the 150px minimum — a silent loss of the user's width.

**Why it cannot be satisfied as currently written:** it can — A76's own outcome ("no collapse key
exists; the app starts expanded") is satisfied either way; only the persisted *width* needed a
decision, and it is a Plan-level detail.

**Suggested Direction / ruling:** **confirmed — persist the tracked *expanded* width.** Because
`_watchlist_width` is never assigned while collapsed (`S24`), a session that ends collapsed still
persists the user's expanded width, so the next launch starts expanded at that width — the only choice
consistent with "the app starts expanded". Recorded as `S27`/`AP-D44-2`. An owner override would revise
A76 and `S27`.

**Status:** addressed — decided and recorded this cycle; no Requirements Analyst action required.

**Escalation:** none.

---

- Issue: **RG-D45-1**

**Requirement/Journey:** Batch 20 / **D45** — `AC-D45.8` and its supporting text: the register's
correction record (`requirements.md:4178`–`:4179`, "… `:177-178` the two SL/TP signals in the
five-signal receiver loop → **a three-signal loop**") and `design_gaps.md` **DG77** item 4 ("the loop
must **shrink to three** or the suite fails on a `hasattr`/attribute error"). Raised by the Validator
during D45 initial validation.

**Problem:** the suggested intermediate form is **unachievable**. The loop in
`tests/test_dock_d18_region.py:173`–`:179` iterates **five** signals —
`position_close_requested`, `group_close_requested`, `flatten_all_requested`,
`position_sltp_changed`, `group_sltp_changed`. D45 removes **all five** (the three close signals in
Group B, the two SL/TP signals in the extension), so after D45 **no signal survives**; a "three-signal
loop" could not exist in either the wave-2 state (window connects none, panel still defines all five —
the loop's `>= 1 receiver` assertion would be red) or the wave-3 end state (the attributes are gone, so
the loop raises `AttributeError`). The Plan's resolution — **delete the five-signal receiver loop**
in wave 2, keep the surrounding assertions (`account_summary_changed`/`positions_changed` `hasattr`,
and the `positions_changed` zero-receiver sanity probe) and restate the wiring comment — is the only
coherent end state, and it satisfies `AC-D45.8` (which requires the file to be *adjusted*, not a
specific loop width).

**Why it cannot be satisfied as currently written:** a three-signal loop would have to reference
deleted attributes; no requirement clause names any of the five signals as surviving, and the D45
"Scope — KEEP" list names none of them.

**Suggested Direction:** **ratify the Plan's loop deletion; no `AC-D45.8` wording change is needed.**
Record the deviation from the register/DG77 *suggested* form in the plan's exactness note and in the
canonical `docs/plan.md` D45 section so Task Manager / Code Reviewer do not "restore" the three close
signals. The architecture proposal's System Components row ("shrinks … to the three surviving
signals") must be corrected to match (Validator R4 in `docs/plan_review.md`).

**Status:** addressed — ruled satisfied this cycle (no AC weakened; the loop deletion is the correct
end state). The corresponding test-book sequencing/late-removal defects (the Validator's R1/R2) were
**closed in round 2** and re-verified against the tree; R4's architecture correction is applied
(System Components row + supersession item 10).

**Escalation:** none.

---

- Issue: **RG-D45-2**

**Requirement/Journey:** Batch 20 / **D45** — `AC-D45.8` ("no dangling references; suite green; test
book as recorded"). Raised by the Validator during D45 round-2 validation, derived from round 1's R1.

**Problem:** `AC-D45.8`'s recorded test book enumerates **six** adjusted suites
(`test_order_rejections`, `test_d28_pacing`, `test_dock_d18_region`, `test_d27_position_id`,
`test_d27_position_prices`, `test_d38_events_news`) and says the suite must be green "with exactly the
recorded test-book change". The delivered book adjusts **seven**, adding
`tests/test_d27_flat_rows.py` (its AC-3 tail asserts `panel._selected_position`, which the panel edit
deletes). The seventh is unavoidable if the selection tracker goes — and the tracker has **no**
production reader after D45 (`_show_context_menu`, `_on_set_sltp`, `_on_close_position`,
`_on_close_group`, `_on_ungroup` all die; `_on_selection_changed` only assigns it and calls the deleted
menu's `set_actions_enabled`).

**Why it cannot be satisfied as currently written:** the enumeration is descriptive, not exhaustive —
keeping the tracker solely so the file stays byte-for-byte would leave dead state with no reader, the
"green while proving less" shape `AR-D45-3` names, and would itself contradict R74's half-removed-path
concern. The criterion's substantive clauses (no dangling imports, full suite green, no *unreported*
test change) are all met: every change is enumerated in `docs/plan.md` § *D45 tests*, with the file,
the exact lines (`:108`–`:111` dropped, `:104`–`:106` kept) and the wave.

**Suggested Direction:** **ratify, no `AC-D45.8` rewrite required in this batch.** `AC-D45.8`'s own
measurable ("import/compile check + full-suite run") is unaffected; the plan records the addition
explicitly (`AP-D45-13`: 5 deleted / 7 adjusted / 1 added), so nothing is hidden. If the Analyst wants
the record exact, append `tests/test_d27_flat_rows.py` (AC-3 selection-tail removed, index-alignment
assertions kept) to `AC-D45.8`'s adjusted list at the next requirements revision.

**Status:** addressed — ruled satisfied this cycle (one additional **reported** adjustment; no clause
weakened, no silent change).

**Escalation:** none.

---

# Batch 21 — D46 / Phase P5 (recorded by the Validator, 2026-10-25, `final_pass`)

- Issue: **RG-D46-1**

**Requirement/Journey:** Batch 21 / **D46** — `AC-D46.5` ("the suite is green with exactly the recorded test
book … **reduced** `tests/test_order_rejections.py` … **3 of 5**") and **`A95`**'s parenthetical ("the repointed case
is exactly `AC-D46.3`'s positive proof").

**Problem:** the two clauses describe the rejection file as *reduced only*, but the file the batch must deliver
keeps **3 surviving originals** *and* gains **one parametrised case over 201 / 103 / 202** — because
`AC-D46.3`'s own measurable demands "three parametrised offscreen cases asserting `status_bar.currentMessage()`
contains `[201]` / `[103]` / `[202]`". A single repointed case on an unrelated code (2105) cannot prove three
codes, so `A95`'s "exactly `AC-D46.3`'s positive proof" is imprecise as well as incomplete.

**Why it cannot be satisfied as currently written:** taken literally, "reduced … 3 of 5" reads as a *file shape*
that would leave `AC-D46.3` with no positive per-code proof — i.e. the two clauses of the same requirement cannot
both be satisfied by the file `A95` describes. It is a description defect, not a delivery defect: `AC-D46.5`'s
operative clause is "No other test **file** changes", which the added case does not breach (the file is already
named as adjusted), and the survivor count "3 of 5" remains exactly true.

**Suggested Direction:** **ratify, no rewrite required in this batch.** The delivered file ends at **4 test
functions**: `test_non_order_error_shows_generic_line` (repointed/renamed from `…_untouched`), the two
`classify_error` cases, and the new parametrised `test_order_error_codes_surface_on_status_bar` (3 params). At the
next requirements revision, append the added case to `AC-D46.5`'s "reduced" clause and replace `A95`'s parenthetical
with "the repointed case proves the generic line for an unrelated code; the per-code proof is the added
parametrised case". Plan records the reasoning as `AP-D46-4`/`AP-D46-5` and flags it (P5 flagged issues 2–3).

**Status:** addressed — ruled satisfied this cycle (a **reported** addition inside an already-adjusted file; no
clause weakened, no silent change).

**Escalation:** none.

---

- Issue: **RG-D46-2**

**Requirement/Journey:** Batch 21 / **D46** — `AC-D46.2` ("chain absent") and its parenthetical measurable
"`hasattr(IBApiClient, "orderStatus") is False` (and the other two); `hasattr(Bridge, "order_status") is False`".

**Problem:** the measurable is **unsatisfiable for the client half**. `IBApiClient` is declared
`class IBApiClient(EWrapper, EClient)`, and `ibapi.wrapper.EWrapper` itself defines `orderStatus`, `openOrder` and
`execDetails` as no-op stubs (verified in `.venv`: `EWrapper.__dict__` membership is `True` for all three, so
`hasattr(IBApiClient, "orderStatus") is True` both **before and after** the repo's override is deleted). Deleting
our override returns the class to the inherited no-op — which is the correct end state, and is exactly what
architecture `S40` / *Tech Stack Decisions* say — but it can never make `hasattr(...)` false. Separately, the AC
names the bridge class `Bridge`; the real class is `IBBridge` (`ibkr/bridge.py:4`).

**Why it cannot be satisfied as currently written:** no implementation of "delete our three overrides" can produce
`hasattr(IBApiClient, "orderStatus") is False`, because inheritance supplies the name. A Build worker following the
measurable literally hits a red assertion and may "resolve" it by weakening the assertion or by removing the
inheritance — the second would break the `ibapi` boundary, the first is a silent criterion erosion.

**Suggested Direction:** **ratify with the substituted measurable — the criterion's substance is unchanged and not
weakened.** The property the AC is after ("this repo defines no order-lifecycle override") is measured exactly, and
more strongly than `hasattr`, by `__dict__` membership — the pattern the guard already uses for transmit names:
`assert "orderStatus" not in IBApiClient.__dict__` (and `openOrder`, `execDetails`). The bridge half is fine as
written once the class name is corrected to `IBBridge`. At the next requirements revision, restate
`AC-D46.2`'s measurable accordingly, and note that D46.2's prose ("no `EWrapper` **override** for
`orderStatus` / `openOrder` / `execDetails`") is already correct.

**Status:** open — non-blocking (the batch is plannable and buildable with the `__dict__` measurable recorded in
the plan; no analyst decision is needed before build).

**Escalation:** none.

**Round 2 (2026-10-25):** the plan now records the substitution in `AP-D46-14` (architecture `S44`, `AR-D46-2`,
*Non-Functional*, System Components, traceability, reviewer step, handoff). This note stays **open** only for the
requirements-side restatement of `AC-D46.2`'s measurable (and the `Bridge` → `IBBridge` name) at the next revision;
nothing in P5 depends on it.

---

- Issue: **RG-D46-3**

**Requirement/Journey:** Batch 21 / **`D46.9`** ("**No order-named symbol exists outside those two sets**") and its
`AC-D46.9` measurable.

**Problem:** the sentence is **literally false in two harmless places** and the register's own `M-5`/`M-4` audit rows
say so. (1) `tests/test_d41_removal.py:97` keeps `_on_order_place_requested`, `_place_order` and `dom_btn` in its
historical **forbidden-token** list — a D41 guard, untouched by P5. (2) `ibkr/bridge.py:42` keeps the section comment
`# Account & Orders` above the **retained** account/position signals.

**Why it cannot be satisfied as currently written:** `AC-D46.9`'s measurable ("scan for every DELETE-set identifier,
assert `found ⊆ retained`") is sound and passes — but the prose claim that **no** order-named symbol exists outside the
two sets cannot, because a test guard and a comment are deliberately kept.

**Suggested Direction:** at the next requirements revision, scope the sentence to **live symbols/identifiers** (or add
the two sites to the RETAIN set with "historical guard list" / "section header for retained signals" as the reason).
No build change: neither site is order code, neither is in P5's file set, and `ibkr/bridge.py:42` is dispositioned as a
keep in the plan (§ *Incidentally affected*).

**Status:** open — non-blocking.

**Escalation:** none this cycle (no build impact; nothing P5 delivers depends on the wording).

---

- Issue: **RG-D46-4**

**Requirement/Journey:** Batch 21 / **`AC-D46.10`** — "keeps `test_get_id_allocates_sequentially`,
`test_set_next_valid_id_equal_is_noop` and `test_concurrent_allocations_never_duplicate`".

**Problem:** **six** of `tests/test_id_manager.py`'s eight cases touch `reserve`, not five. The third "kept" case,
`test_concurrent_allocations_never_duplicate`, calls `mgr.reserve(3)` (`:85`) and asserts `len(seen) == 8 * 203`
(`:97`), so deleting `reserve` makes it raise `AttributeError` — it cannot be kept **unchanged**.

**Why it cannot be satisfied as currently written:** the AC's count (8 → 4) and its "keeps" list are consistent only if
"keeps" means *the case survives*, not *the case is untouched*.

**Suggested Direction:** **ratify — the plan's reading is the only satisfiable one.** Wave 6 deletes the four pure
`reserve` cases and **rewrites two** (the monotonic case, and the concurrent case without its `reserve` block, `8 * 203`
→ `8 * 200`), landing **8 → 4** with the three named cases alive. At the next revision, say "**keeps three, rewrites
two**".

**Status:** open — non-blocking (interpretation recorded in plan Flagged Issue 1 and `AP-D46-…`; wave 6 is executable
as written).

**Escalation:** none this cycle.

---

- Issue: **RG-D46-5**

**Requirement/Journey:** Batch 21 / **`D46.5`** and **`A104`** (the test book), plus `AC-D46.5`'s "no other test file
changes".

**Problem:** the register's book under-lists four measured sites (only one of which it names as a Flagged Issue):
1. `tests/test_sound_service.py:76` asserts `paths["fill"]` → **`KeyError`** once the `"fill"` key goes (3 sites in
   that file, not 2);
2. `tests/test_id_manager.py`'s concurrent case calls `reserve` (see `RG-D46-4`);
3. the three raw-SQL seeders need **two** placeholders and **two** `None` values removed, not "one placeholder"
   (11 names / 11 `?` / 11 values → 9 / 9 / 9);
4. `tests/test_d45_removal.py` needs **four sub-edits across two waves** (the `:523` call + `:22` bullet in wave 1; the
   token migration, absence pools, end-state test and its own prose in wave 8), not "allow-list shrink" only.

**Why it cannot be satisfied as currently written:** a Build worker following the register's book literally leaves the
sound test red (`KeyError`), the id-manager case red (`AttributeError`), the seeders red (`ProgrammingError`), and the
guard's walkthrough red (`AttributeError` on `_on_order_error`).

**Suggested Direction:** **the plan's book is the operative one** (2 deleted / 13 adjusted / 0 added, sites enumerated
per assertion). At the next revision, fold the four sites into `D46.5`/`A104`.

**Status:** open — non-blocking (the plan's book is complete and executable; task graph does not exist yet).

**Escalation:** none this cycle.

---

- Issue: **RG-D46-6**

**Requirement/Journey:** Batch 21 / **`D46.12`** — "this env is SQLite **3.54.0**, so both are available".

**Problem:** the app's interpreter is **`.venv/bin/python` → SQLite 3.53.1** (measured). 3.54.0 is the *system*
`python3`. Both support `ALTER TABLE … DROP COLUMN` (≥ 3.35) and `RETURNING` (≥ 3.35), so **no criterion fails**.

**Why it cannot be satisfied as currently written:** it is a factual citation about the wrong interpreter, repeated to
justify a destructive step.

**Suggested Direction:** state "**≥ 3.35**" (or 3.53.1, the app's measured version). Recorded in the architecture's
Codebase Summary and `S47`; plan Flagged Issue 3.

**Status:** open — non-blocking.

**Escalation:** none this cycle.

---

- Issue: **RG-D46-7**

**Requirement/Journey:** Batch 21 / **`A99`** — "the drop therefore destroys nothing that survived … the columns could
only ever hold `NULL`".

**Problem:** **overstated for an inherited database.** A row from a pre-D45 file that **never receives another live
position update** (symbol no longer held/streamed, account not subscribed) keeps its old stop/target bytes. Those bytes
are invisible (8-column panel), unsettable (no dialog/menu since D45) and unsupported — so the drop is defensible — but
it is the batch's **only byte-destroying step**, and "could only ever hold `NULL`" is not true.

**Why it cannot be satisfied as currently written:** the justification is a false premise for a destructive step, which
is exactly the class of statement a future reader will trust.

**Suggested Direction:** say **"destroys nothing the app can reach"** and add the byte-level truth ("a row that never
updates again keeps its legacy bytes and loses them at the drop"). The plan and architecture now say this
(`S47`, *Data Model*, *Non-Functional*, plan § *Phase P5*); `D46.12`'s **row**-preservation requirement is unchanged
and is what keeps the step bounded.

**Status:** open — non-blocking (end state and mechanism unchanged; wording only).

**Escalation:** none this cycle.

---

- Issue: **RG-D46-8**

**Requirement/Journey:** Batch 21 / **`R10`** — "`TradeGroup`, `trade_group_id`, strategy grouping … display-only
strategy grouping; only its four stop/target fields go".

**Problem:** **the named consumers do not exist.** `TradeGroup` has **no** production consumer; `trade_groups` and
`position_group_map` have **no reader and no writer** anywhere; and the Strategy/Group columns come from
`services/strategy_detection.py` over `Position.id`/`qty`/`strike`/`right` — not from `trade_groups`.
`AC-D46.9`'s own test ("each RETAIN entry still has its named consumer") therefore **fails for this row**.

**Why it cannot be satisfied as currently written:** the retain decision is fine; the *evidence* is false, and a RETAIN
row justified by a consumer that does not exist is the exact "not audited" defect D46 exists to fix.

**Suggested Direction:** **retain, corrected rationale** — "dead storage (zero readers, zero writers), retained only to
avoid widening the batch (deleting it would touch `tests/test_db_schema.py`)". The plan's survivor table, the
architecture's `S46` and the codebase map now say that; nothing else changes.

**Status:** open — non-blocking (no build impact: the tables/fields are not touched by P5).

**Escalation:** none this cycle.

---

- Issue: **RG-D46-9**

**Requirement/Journey:** Batch 21 / **`D46.13`** / **`AC-D46.13`** ("no live statement … over the six files"), against
`requirements.md` itself.

**Problem:** the register's correction record says the stop/target statements were "amended or annotated in place in
this revision". **Seven requirements.md sites still carry the live pre-D46 claim** and are not inside any supersession
note: `:1183` ("DB schema is unchanged (no migration, no destructive schema change)"), `:4337` (KEEP list: "retained —
no schema change, no migration (A87)"), `:4399` (`D45.6`: "retained unchanged (no migration)"), `:4539` (edge case: "DB
schema is unchanged"), `:4565` (D45 `A87`: "stay, with no migration and no destructive schema change"), `:4584`
("model fields/DB columns stay (A87)"), `:5515` (D45 batch summary: "retained but unsettable/unrendered (A87, no
migration)"). The other five documents are clean as of this activation (the Validator attached the D46/A99 markers to
the activated D45 sections of `architecture.md`/`plan.md`; the map is refreshed; `USAGE.txt`/`usage.md` are wave-9
work).

**Why it cannot be satisfied as currently written:** the criteria contradict each other inside the requirements file —
`D46.7` keeps D45 history verbatim, `D46.13` forbids a live "kept" claim, and the annotations that resolve the tension
were only partly applied.

**Suggested Direction:** annotate those seven sites with `SUPERSEDED BY D46 / A99 — storage DROPPED` (the pattern used
at `:223`, `:483`, `:1171`, `:4345`, `:4508`). **No build change**: `requirements.md` is not a build input and the plan
already carries the end state.

**Status:** open — non-blocking for the build (recorded for the analyst; the Code Reviewer should treat this as an
analyst-owned documentation defect, not a Build or Plan failure).

**Escalation:** none this cycle — **the fix would not change what gets built** (owner policy on document rounds),
so it is recorded for the next requirements revision rather than pausing P5.
