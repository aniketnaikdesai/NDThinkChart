# P23 — Implementation Plan: Option Spreads panel

**Status:** ready for owner review · **Author:** Orchestrator (one-off, written by hand — not an agent output)
**Basis:** `docs/plan.md` § Phase P23 (validated, `READY_FOR_TASK_MANAGER`), `docs/architecture.md` § Phase P23, `docs/requirements/requirements.md` D65, `docs/plan_review_P23.md`
**Scope:** 8 waves · sizes S/M · no new dependency, no schema additions (one destructive drop), zero order code

---

## 1. What ships

A new **Option Spreads** panel replaces the Portfolio / Account Summary panel in the right dock. When switched on, it maintains four 20-wide SPX 0DTE credit spreads per side (four call credit spreads above spot, four put credit spreads below), keeps the "target" spread priced near your Target, streams live ASK/BID/Delta/Gamma per leg, and closes every quote line it stops using when you switch it off.

Everything that displayed positions or account summary is **deleted**, not hidden: the panel module, the position/account data path, the models, and the three database tables.

**What you gain:** the spread ladder you specified, live.
**What you lose:** any in-app view of positions or account summary. You accepted this when choosing "replace" (Q110a). If it ever bites, a positions view is a *new* feature (FS26), not resurrected code.

---

## 2. How it works (the parts worth reviewing)

**Chain discovery.** Ask TWS for SPX's option chain (`reqSecDefOptParams`) filtered to today's expiry. The 0DTE series is **SPXW**, not the monthly SPX — the plan uses the trading class the exchange returns rather than assuming a name. If there is no 0DTE expiry today (weekend, holiday, after the close), the panel shows an explicit empty state with zero option lines subscribed — no fallback to a later expiry, no silent blank.

**Finding the anchor (spread 3).** A pair is four numbers: short strike `s`, long strike `s+20`. Its credit can be read three ways — net mid, net ask, net bid. Your rule says a spread is "at target" if **any** of those is within 0.05 of the Target, so the match test is `d = min(|mid−T|, |ask−T|, |bid−T|) ≤ 0.05`, and a matched pair is **never moved** even if its mid drifts.

**Walking the ladder.** You delegated the direction, so the plan decides it: when no pair is matched, step one 5-point strike step toward the pair with the smaller `d` — and only if it improves `d` by more than 0.05. Ties break on the net mid closer to Target. At most one step per second, and one step immediately on Target change or on OFF→ON. Stops when matched, when no neighbour improves, or at the chain edge (one message naming the best reachable value).

Because a credit spread's value rises as strikes move toward the money, the direction is unambiguous per side: **CCS moves both strikes down to raise credit, PCS moves both strikes up.** Both legs always move together, so the width stays 20.

**Why moving is cheap.** The two neighbours of the anchor are already displayed as rungs 2 and 4, so a step decision needs **no extra subscriptions** — just two cancels and two subscribes per side. That is what keeps the design inside the 16-line budget.

**Line budget.** Steady state is **16 lines** (8 legs × 2 sides... precisely: 4 spreads × 2 legs × 2 sides). A window step is 16 → 14 → 16, and every leg that survives a step keeps its **same reqId** — that is the shared-leg rule made measurable. The chain scan is a monotone sweep of these window steps (`O(k)`), never a parallel probe pool.

**Switching off.** OFF cancels all option lines, clears the tables and stops the evaluator. Nothing stays subscribed "in case".

---

## 3. Build order

Each wave is independently reviewable and green on its own exits. Order is forced by three rules: the new panel must be live **before** the account path dies; each signal dies with the emitter that feeds it; the schema drop comes after its last reader.

### P23-01 — Panel shell, ladder math, dock swap, launch width (M)
Builds `ui/option_spreads_panel.py` (header, Target field defaulting to `1.00`, ON/OFF toggle, CCS/PCS tables, elide+tooltip name cells, `PREFERRED_WIDTH = 360`) and `services/option_ladder.py` (pure geometry/naming/metric/formatters). Swaps the dock to `Option Spreads` and deletes `ui/active_portfolio_panel.py`.

Carries the **broadest test surgery** in the phase: the right dock's identity changes from `"Portfolio"` to `"Option Spreads"` as both title and `objectName`, and **20 surviving test modules** look the dock up by the old title — 3 hard-fail immediately, 17 silently stop hiding the dock (which matters because the dock is now 360 px and would mask width-sensitive suites). All 20 are edited here, keyed on `objectName`.

Also: the launch width. The dock opens at `clamp(360, 200, 40% of chart area)` — achievable at a normal window (≳1480 px wide with the default watchlist), capped smaller on narrow screens, where names elide with a tooltip. Minimum width, cap, collapse behaviour and the "never persisted" rule are untouched; exactly **two** D18 assertions are re-baselined, by your decision (A201).

### P23-02 — Chain, contracts, greeks (M)
`ibkr/contracts.py` gains index-option contract building; `ibkr/market_data.py` gains the option-quote subscription (greeks arrive via `tickOptionComputation` on each leg's own line); `ibkr/client.py` gains the wrapper callback. No production code outside `ibkr/` calls the new surface yet — every symbol here is exercised by the new chain suite, so nothing is dormant.

### P23-03 — Spread engine (M)
`services/option_spread_engine.py`: pure, no Qt, no sockets. Selects the anchor from a chain snapshot, maintains both ladders, emits step decisions, and surfaces once-only faults (target unreachable, chain edge, greeks missing). Fed by fixtures; this is where the direction rule and the 0.05 band are proved.

### P23-04 — Live wiring (M)
`ui/main_window.py`: ON/OFF lifecycle, the 16-line accounting through the existing `md_line_guard`, coalescing (one evaluation in flight, latest viewport wins), fault surfacing to the panel status line. Runs the real window against a fake client — this is the first wave where the panel is live end to end.

### P23-05 — Account/position window path removal (S)
Removes the window's account subscription, its three handlers, `_upsert_position`, the price sink, and the five inert `_record_symbol_price` test stubs. Exit is a tree-wide grep for its own tokens returning empty.

### P23-06 — Broker boundary, modules, models (S)
Deletes the account/position signals and their `EClient`/`EWrapper` overrides, `ibkr/account.py` entirely, and `data.models.Position` / `TradeGroup`. The D45 residue instrument's model assertions move here (they currently assert those classes *exist*).

### P23-07 — Schema drop (S)
`DROP TABLE IF EXISTS` for `positions`, `trade_groups`, `position_group_map` in `_migrate_schema`, plus the `conftest.py` teardown that still wipes them after every test. Destructive and owner-confirmed; the rows were a broker mirror re-received on connect, with their stop/target columns already gone since D46.

### P23-08 — Standing residue gate (S)
`tests/test_d65_residue.py`: the machine check for your no-unused-code rule — new-symbol reachability, displaced-token absence, unused imports/branches, test-helper-used, and the signal three-way check (declared / emitted / connected). Proven **red on a seeded dead symbol** before it is trusted. From here the rule is enforced by the suite rather than by review.

---

## 4. What gets deleted

| Group | Wave | Gone from the tree |
|---|---|---|
| Panel | 01 | `ui/active_portfolio_panel.py`; `portfolio_panel` attribute; its tests |
| Dock identity | 01 | `Portfolio` title/`objectName`; 20 test lookups re-keyed to `objectName` |
| Window path | 05 | account subscription, `_on_account_summary`, `_on_position_update`, `_on_position_end`, `_upsert_position`, `_symbol_last_prices` chain |
| Signals + transport | 06 | `account_summary`/`position_update` bridge signals and client overrides |
| Modules + models | 06 | `ibkr/account.py`, `services/strategy_detection.py`, `data.models.Position`/`TradeGroup` |
| Schema | 07 | `positions`, `trade_groups`, `position_group_map` + their rows and index |

**Kept, with the consumer named:** `IdManager.get_id` (six reqId callers), the generic TWS-error status path, `error_codes.classify_error`, the bar/session/chart stack, the right dock itself.

---

## 5. Test plan

* **New suites per wave:** panel shell (`test_d65_option_panel`), chain/contracts (`test_d65_option_chain`), engine (`test_d65_spread_engine`), live stream (`test_d65_option_stream`), residue gate (`test_d65_residue`).
* **Re-baselined:** exactly two D18 assertions (owner-authorised), plus D41/D45 title-keyed assertions re-pointed — no behavioural assertion weakened.
* **Deleted with their subject:** 6 D27 account/position suites, `test_d41_portfolio_dock.py`, and three groups inside `test_d45_removal.py` split across waves by subject.
* **Exit-condition audit** (§ *Phase P23*): every wave's exit reads only files/symbols that wave owns. This was the recurring review failure in three revisions — a wave claiming green while its subject died two waves later.
* **Gate:** full offscreen suite green, node suite green, residue gate green, and the gate proved red on a seeded fixture.

---

## 6. Risks worth your attention

1. **The three-basis match can look "at target" on the ask alone** while mid sits well below Target. That is the literal reading of your rule; the ASK/BID columns show both sides. If you'd rather it be mid-only, that's a one-line rule change — say so and I'll amend before build.
2. **0DTE only** means the panel is empty outside today's session and on non-trading days. Deliberate (Q107b), with an explicit empty state.
3. **The chain scan assumes the `d` surface is quasi-convex** along strikes. If a real chain breaks that, the engine falls back to a full ordered sweep — same line accounting, more steps. If a live chain ever shows a non-converging walk, that is a defect to report, not to tune around.
4. **Deletion is irreversible for the cached snapshot** of positions/account rows (owner-confirmed).
5. **Greeks depend on your OPRA/option entitlement.** Missing greeks → the panel shows price-only with a status message; it never fabricates deltas.

---

## 7. Outside this phase (flagged, not fixed here)

* **P22 orphan sweep (D66):** P22's timezone/crosshair work may have displaced code that P23's gate cannot see (different seam). A small follow-up batch runs the same residue checks over the P22 seams and records the result either way.
* **Two tooling defects, mine to fix, neither gating:**
  * `update_codebase_map.py` emits `(root)/` backticked, which `plan_lint.py` then treats as a path and fails — the next map regeneration will break lint until fixed.
  * `pipeline_state.py`'s `PHASE_HDR_RE` expects a bare `## Phase P<n>`; this repo's headers carry trailing text, so section hashes never stamp and freshness falls back to mtime.

---

## 8. What approval means

Approving this plan starts the normal pipeline: Task Manager decomposes the eight waves into tasks, the build loop runs them in order, and Code Review verifies each. Estimated shape: two M waves with heavy test surgery (01, 02/04), one pure-logic M (03), four S waves.

If you want anything changed — the mid-only match, a different walk direction, keeping one of the deleted artifacts — say which and I'll amend the requirements/plan before any code is written.
