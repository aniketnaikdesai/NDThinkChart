# Implementation Plan Proposal — NDThinkChart Batch 20 (**D45**): remove the News Digest dock (+ the `View` menubar), the Trade Context Menu, the **Kill switch** and the **SL/TP dialog** — the app ends with **zero order interaction**

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical plan —
> `docs/plan.md` is written by Plan Artifact Editor & Validator after validation. Companion:
> `docs/architecture_proposal.md` (relationship table `S29`–`S38`, Codebase Summary, components, data model,
> integrations, frozen interfaces, non-functional approach, risks `AR-D45-1`–`AR-D45-10`, traceability).
> Module index: `docs/codebase-map.md` (refreshed for this batch; `update_codebase_map.py` re-run 2026-10-25).
>
> **Run shape:** **legacy single-scope** — the invocation preamble carries **no `phase: P<n>`**, so these are
> the unsuffixed proposal files and the D45 increment merges into the cumulative canonical
> `docs/plan.md` / `docs/architecture.md` as a `## D45 increment` section (the D16–D44 precedent).
>
> **This file replaces the stale D44 draft WHOLESALE** (the previous contents were the D44 plan). **D44 is
> delivered** — committed at `c702be9`, full offscreen suite green, review complete. A previous **D45** Plan
> run was **cancelled after refreshing `docs/codebase-map.md`**; its never-activated draft is superseded whole
> by this pair, and **no identifier it minted carries authority** (its `FI-D45-1`, "SL/TP dialog retained with
> no entry point", is now **moot** — the dialog is deleted). This is **Revision 2** (round 2 of 3), revised
> against the Validator's `CHANGES_REQUIRED` on R1–R4 — see the revision notes immediately below.
>
> **Revision notes — round 2 (R1–R4).** One line per Validator Required Change.
> **R1 (blocking, untracked assertion)** — `tests/test_d27_flat_rows.py:110`–`:111` asserts
> `panel._selected_position`, which wave 3 deletes. Resolved by **deletion of the tracker**, not by keeping it
> (`AP-D45-4` corrected, new wave-3 per-file row): after D45 the tracker has **no** production reader, so
> keeping it alive for one test is the "green while proving less" shape `AR-D45-3` names. The file joins
> **wave 3** with an exact AC-3 adjustment; the test book is now **7 adjusted**, `AP-D45-13` recounts, and the
> map's book is updated.
> **R2 (blocking, assertion outliving its subject)** — the D27.1 AC3 case passes only through the wave-2 window
> SL/TP connection removal, so its **removal moves into wave 2**; the `8`/`9` → `6`/`7` index edit stays in
> wave 3. Recorded in the wave table, both per-file maps, the shared-file table, the test book and a new
> sequencing rule ("no wave leaves an assertion referencing something a *previous* wave deleted").
> **R3 (residue instrument)** — the forbidden list gains the **nine** panel members wave 3 deletes; the scan
> scope is stated precisely (**AST over `ui/ services/ data/ ibkr/ config/`; grep `ui/`-only**; `tests/`
> excluded), so `config/settings.py`'s `validate_order()` *comment* is out of scope in a file no task may edit;
> and `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in the wave-6 module.
> `AR-D45-5` is rewritten to be true.
> **R4 (documentation contradiction)** — the architecture's `tests/test_dock_d18_region.py` row is corrected to
> "the loop is **deleted**" (all five signals go, so no signal survives); the deviation from the D45 register's
> / `DG77`'s suggested "three-signal loop" is recorded in the § Exactness note, in the architecture's
> supersession list (item 10), and in `docs/plan_notes.md` `RG-D45-1`.
>
> **Scope: D45 only** — an **owner-requested removal batch** (Batch 20, 2026-10-25) **including its later
> extension the same day**, which moved the **Kill switch** and the **SL/TP dialog** from *retained* to
> *removed*, **inverted `AC-D45.6`**, added `AC-D45.10`, and **reversed A82/A83**. The app ends with **zero
> order interaction**. Requirements of record (`docs/requirements/requirements.md`,
> `Status: READY_FOR_PLAN`, **0 open questions**): **`### D45`** `:4100`–`:4481`, **`AC-D45.1`–`AC-D45.10`**
> `:4282`–`:4370`, the supersession/revision record `:4371`–`:4416`, **A79–A90** `:4417`–`:4560`, correction
> record `:4461`–`:4481`; **Journey 38** `:1086`–`:1119`; **R68–R75** `:4699`–`:4706`; `design_gaps.md`
> **DG75** `:1189`–`:1212`, **DG76** `:1214`–`:1229`, **DG77** `:1231`–`:1260`.
> **Baseline:** `main` @ **`c702be9`**; the working tree carries only this batch's requirements/design-gaps/map
> edits.
>
> **Escalation state at planning time.** **No `PLAN`-routed escalation is open** —
> `docs/code_review/escalations.json` holds **no `status: "open"` entry at all** (re-checked 2026-10-25).
> `docs/plan_review.md` is the **APPROVED** D44 cycle (its freshness note is about the D42 fold-in, not a
> `CHANGES_REQUIRED`). `docs/tasks/task_manager_notes.md` carries no `ESCALATED_TO_PLAN`. **DG76 is the only
> open Plan-level question and it is decided here** (§ Assumptions `AP-D45-1`, architecture `S29`); DG75 is
> resolved by the requirements' own supersession (five named whole-file deletions), DG77 by the test book
> below.
>
> **Owner decisions this plan does not re-litigate:** `A87` (Stop/Target **columns removed**, storage **kept**,
> no migration), `A89` (SL/TP dialog removed **completely**, including both `MainWindow` persistence slots and
> their row-`UPDATE`s), `A90` (the inbound order observers and the `order_registry` import are **intentionally
> inert**, not leftovers), `A79` (`"456"` dividends / tick 59 / `_dividend_info` / `dividend_updated` **stay**),
> `A86` (no menubar replaces the `View` menu), `A88` (no cancel capability survives or is re-pointed).
> **D41's "retained order machinery" is reversed** — **no** order path survives. **D1–D44 are not reopened**
> beyond the supersessions D45 already records. **No new dependency**; PyQt6 / pyqtgraph / `ibapi` only, and
> **pyqtgraph is a locked decision** (`docs/memory.md`, 2026-10-16).

**The one workstream — subtractive, four removal groups, one invariant.** After D45 the app **places, cancels
and closes nothing**; trades and their protection live in **TWS**, and the app observes and renders. The work
splits by **member group** (never by file — the D41 lesson, memory 2026-10-15 / R69):

1. **Group A — the digest half of D38** (`AC-D45.1`, `.2`, `A79`, `A86`, R68): delete `ui/news_digest_dock.py`
   and `ibkr/news.py`; drop the dock + the **whole `View` menubar** + the news `"292"` S0 line and its
   digest-only plumbing. **Dividend substrate untouched.**
2. **Group B-main — the order path in the window** (`AC-D45.3`, `.4`, `A80`, A90): delete
   `_close_position_by_id` (the **only** `placeOrder` call site in the tree), the three close handlers, the two
   SL/TP persistence handlers, `_ref_price_for`, the `validate_order` import, and `ibkr/validation.py`.
3. **Group B-panel — the menu, the setter chain and the two columns** (`AC-D45.3`, `.5`, `.10`, `A87`,
   `A89`): delete `ui/trade_context_menu.py` and `ui/stop_loss_target_dialog.py`; strip the panel's menu
   policy/member/handlers, the five signals, the SL/TP chain and the `Stop`/`Target` columns (**10 → 8**).
4. **Group C — the cancel path** (`AC-D45.6`, `A88`, `R73`, `R74`): delete `kill_btn` (+ its separator),
   `_on_kill_switch_clicked`, `_kill_switch`, and with them the app's **entire** `reqGlobalCancel` /
   `cancelOrder` capability. **Nothing is re-pointed; no replacement UI.**

The invariant that binds them is **reachability, not deletion count** (`D45.2`, `AC-D45.4`, `.6`): no `ui/`
module may call `placeOrder`, `cancelOrder` or `reqGlobalCancel`, import the deleted feature/validation
modules, or expose a removed member — verified by a **static source scan** plus a **mocked-client zero-transmit
walkthrough** (`S36`).

**Out of scope — do NOT plan these.** Every earlier defect/feature (D1–D44) and its delivered artifacts; the
chart/render stack (**pyqtgraph locked**), the load/backfill path, alarms, drawings, studies, pop-outs, D39,
D40, D42, D43, D44; `data/db.py`'s schema and migrations; `data/models.py`'s fields; `ibkr/orders.py`'s **API**
(retained — `S29`); `config/settings.py`; `ibkr/pacing.py`. **No new dependency, no stack change, no
replacement close/cancel/protection UI.**

---

## Phases

**Two phases, six waves.** Phase 1 is the removal itself, split into **four waves forced by three shared
files** (§ Sequencing): one task per wave touches `ui/main_window.py`; `tests/test_dock_d18_region.py` and
`tests/test_d27_position_id.py` are each split across two waves by line range; and Group B's window half lands
**before** its panel half so every wave leaves the app importable and its own tests green. Phase 2 adds **no production edit**:
it cleans the two owner-facing docs in one task and then builds the batch's **acceptance instrument** and runs
the batch gate.

### Phase 1 — The removal (waves 1–4)

**Goal:** after wave 4 the app has **no order interaction** — no close/flatten, no cancel, no SL/TP setter, no
digest — while the dividend markers, the Portfolio render, D39, D40, D44 and the rest of the app behave
exactly as today.

**Covers:** `AC-D45.1`, `.2`, `.3`, `.4`, `.5`, `.6`, `.10`; requirements `D45.1`–`D45.4`, `D45.6`;
**Journey 38** steps 1–8; A79, A80, A86–A90; R68, R69, R72, R74, R75.

**Dependencies:** none on earlier batches (D1–D44 delivered). Internal order is **strictly sequential** (see
below).

| Wave | Task (proposed id) | Group | Goal | Files |
|---|---|---|---|---|
| **1** | `D45-01` | **A** — digest + `View` menubar + `"292"` | No digest dock, no menubar, no `Ctrl+Shift+N`, no `"292"` request; `"456"`/tick 59/markers intact | **edit** `ui/main_window.py`, `ui/ticker_session.py`, `tests/test_d38_events_news.py`, `tests/test_dock_d18_region.py`; **delete** `ui/news_digest_dock.py`, `ibkr/news.py` |
| **2** | `D45-02` | **B-main** — the order path in the window | `placeOrder` becomes **uncalled tree-wide**; no close/close-group/flatten; `validate_order` gone; the D27.1 AC3 case leaves **with** the connection it depends on | **edit** `ui/main_window.py`, `tests/test_order_rejections.py`, `tests/test_d28_pacing.py`, `tests/test_dock_d18_region.py`, `tests/test_d27_position_id.py` (the AC3 case only); **delete** `ibkr/validation.py`, `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`, `tests/test_order_validation.py` |
| **3** | `D45-03` | **B-panel** — menu + SL/TP chain + columns | No context menu, no close/SL-TP signals or setters, no dialog, no selection tracker; the table renders **8 columns** | **edit** `ui/active_portfolio_panel.py`, `tests/test_d27_position_id.py` (index edit), `tests/test_d27_position_prices.py`, `tests/test_d27_flat_rows.py`; **delete** `ui/trade_context_menu.py`, `ui/stop_loss_target_dialog.py`, `tests/test_sltp_honesty.py` |
| **4** | `D45-04` | **C** — the cancel path | No kill switch, no `reqGlobalCancel`/`cancelOrder` call anywhere; the toolbar keeps its remaining widgets + trailing stretch | **edit** `ui/main_window.py`; **delete** `tests/test_kill_switch.py` |

### Phase 2 — Docs, the acceptance instrument, and the batch gate (waves 5–6)

**Goal:** the three docs advertise nothing that was removed, and the batch ships a **discriminating** guard for
"zero order interaction" plus the full-suite gate.

**Covers:** `AC-D45.7`, `AC-D45.8`, `AC-D45.9` (verification half); `D45.5`; **Journey 38** steps 8–9 and its
edge cases; R70, R71; `S36`, `S38`.

**Dependencies:** waves 1–4 complete (the guard asserts their end state; the docs must not describe a live
surface).

| Wave | Task (proposed id) | Goal | Files |
|---|---|---|---|
| **5** | `D45-05` | Docs cleaned in one task: no digest/`View`, no close/close-group/close-all, no kill switch, no SL/TP setter, no app-placed-order or "orders while disconnected" claim; instead: **closes and cancels happen in TWS**; SL/TP are **stored** but not settable in-app | **edit** `USAGE.txt`, `usage.md` |
| **6** | `D45-06` | The acceptance instrument + batch gate: the new static/behavioural guard (**proven RED on the pre-D45 tree**), the full residue grep, the full offscreen suite, an import/launch check | **create** `tests/test_d45_removal.py`; **verify** everything else |

---

## Sequencing constraints — waves, shared files, and why the order is forced

Three facts fix the order. They are properties of the tree, not preferences:

1. **`ui/main_window.py` is touched by three groups** (A, B-main, C). The build scheduler must never place two
   tasks with overlapping `touches_files` in one wave, so the window is edited in **waves 1, 2 and 4** — three
   separate tasks, strictly sequential.
2. **Group B splits along the panel's signal boundary, and the window must go first.** `MainWindow.__init__`
   connects `position_close_requested`, `group_close_requested`, `flatten_all_requested`,
   `position_sltp_changed` and `group_sltp_changed` (`ui/main_window.py:647`–`:651`). If the **panel** removed
   those signals first, `__init__` would raise `AttributeError` and **every** window-building test in the
   suite would fail for a reason unrelated to the work in flight — a wave that cannot pass its own tests.
   Removing the connections **first** (wave 2) leaves five signals with zero receivers: harmless, still
   constructible, still green once `tests/test_dock_d18_region.py`'s five-signal receiver loop is removed in
   the same wave.
   Wave 3 then removes the panel side. **This ordering is mandatory, not stylistic.**
3. **`tests/test_dock_d18_region.py`, `tests/test_d27_position_id.py`, `USAGE.txt` and `usage.md` are each
   touched in more than one wave.** The two line ranges of `test_dock_d18_region.py` are split (**`:147` filter
   → wave 1; `:174`–`:179` receiver loop → wave 2**) and those of `test_d27_position_id.py` are split
   (**`:170`–`:201` AC3 case → wave 2; `:164`–`:165` `8`/`9` → `6`/`7` → wave 3**) — different waves, so never
   concurrent. The two docs are **all** deferred into **one** task (wave 5), because three groups editing the
   same prose in three waves would conflict for no benefit.
4. **No wave may leave an assertion that references something a *previous* wave deleted.** An assertion whose
   subject dies in wave *N* is removed or adjusted **in wave *N***, even when a later wave also edits that
   file. This is what fixes R2: the D27.1 AC3 case's subject is the **window** connection (wave 2), not the
   panel setter (wave 3), so the case leaves in wave 2 while the same file's column-index edit stays in
   wave 3. The batch-end test book is unchanged in substance — only *which* wave carries the removal.

| Wave | Shared file | Other witnesses in the same wave? | Constraint |
|---|---|---|---|
| 1 | `ui/main_window.py`, `tests/test_dock_d18_region.py` | no | — |
| 2 | `ui/main_window.py`, `tests/test_dock_d18_region.py`, `tests/test_d27_position_id.py` (AC3 case) | no (wave 1 finished) | **must follow wave 1** (same file); the AC3 case goes **here**, in the wave that deletes the connection it passes through |
| 3 | `ui/active_portfolio_panel.py`, `tests/test_d27_position_id.py` (`8`/`9` → `6`/`7`) | `ui/main_window.py` **not** touched | **must follow wave 2** (panel signals may only go once the window stops connecting them); second touch of `test_d27_position_id.py` — different line range, never concurrent with wave 2 |
| 4 | `ui/main_window.py` | no | **must follow waves 1–2** (same file) |
| 5 | `USAGE.txt`, `usage.md` | no | must follow 1–4 (must not describe a live surface) |
| 6 | — (creates one new test module) | no | must follow 1–5 (asserts the end state) |

**Why not fewer waves?** Merging waves 2→3 (or 1→2) puts 300–500 deleted lines across 15+ files into one task —
exactly the size that killed three D41 workers (memory 2026-10-15; R69). Four waves of ~4–8 files each is the
mitigation the correction record asks for ("split the deletions by member group"). **Why not more?** No task
below the wave level: per-file/per-member decomposition is Task Manager's, and the six waves are the
milestone-level sequencing this plan owns.

---

## Per-file `touches_files` map

### Wave 1 — `D45-01` (Group A)

| File | Action | Precise change (resolve by symbol, not by line) |
|---|---|---|
| `ui/main_window.py` | edit | Drop the `NewsDigestDock` import + `self.news_digest_dock` creation/addition + `menuBar()`/`view_menu`/`_news_digest_action`/`visibilityChanged` block; `_on_news_digest_visibility`; the `NewsManager` construction (`self.news_manager`); `b.tick_news.connect(self._on_s0_tick_news)`; `_on_s0_tick_news`. The window must then create **no `QMenuBar` at all**. |
| `ui/ticker_session.py` | edit | The news `"292"` need registration and its comments; `on_s0_tick_news`; `add_news_push_listener` / `remove_news_push_listener`; `set_s0_headless`; the `_s0_headless` attribute **and the two `or self._s0_headless` clauses** in `_s0_resync` / `_s0_reissue`. **Do not touch:** `_needs["dividends"] = {"456"}`, `on_s0_tick_string` (tick 59), `_dividend_info`, `dividend_info`, `dividend_updated`, `_merge_ibkr_dividend_event`, `_merge_events`, `events`. |
| `ui/news_digest_dock.py` | **delete** | whole file |
| `ibkr/news.py` | **delete** | whole file (its only consumer was the dock + its tests) |
| `tests/test_d38_events_news.py` | edit | Remove the `NewsManager` section (3 cases) and the **whole** `AC-D38.2/AC-D38.3` digest section (`_StubNewsManager`, `_StubHost`, `_make_dock`, 3 cases). Trim the module docstring of `AC-D38.2`/`AC-D38.3`/`NewsManager`; correct the md-line-guard docstring's `"292"` reference. **Keep** the tick-59, yfinance-cache, AC-D38.1/`.4`/`.5`, no-mock-endpoint and md-line-guard cases verbatim. |
| `tests/test_dock_d18_region.py` | edit | `:147` only — drop `and d.objectName() != "NewsDigest"` from the right-dock filter (**not** the receiver loop; that is wave 2). |

### Wave 2 — `D45-02` (Group B-main)

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

### Wave 3 — `D45-03` (Group B-panel)

| File | Action | Precise change |
|---|---|---|
| `ui/active_portfolio_panel.py` | edit | Remove the `TradeContextMenu` / `StopLossTargetDialog` imports and `QMenu` if unused; the `position_sltp_changed` / `group_sltp_changed` / `position_close_requested` / `group_close_requested` / `flatten_all_requested` signals; `self._context_menu` and its five `.triggered.connect` lines; `setContextMenuPolicy(CustomContextMenu)` + its `customContextMenuRequested` connection (**back to the default policy**); `_show_context_menu`; `_on_set_sltp`; `_on_sltp_confirmed`; `update_position_sltp`; `update_group_sltp`; `_sltp_dialog`; `_on_close_position`; `_on_close_group`; `_on_ungroup`; `_on_flatten_all`; and the menu-only selection tracking (`_selected_row`, `_selected_position`, `_on_selection_changed`, its `itemSelectionChanged` connection, and the two comments that name it). **Columns:** `QTableWidget(0, 8)`, headers `Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`; drop the two `stop_loss`/`take_profit` values from `_render_table`'s list; right-aligned set `(1, 2, 4, 5)`; correct the `RIGHT_DOCK_MIN_WIDTH` docstring's "10-column" wording. **Do not touch:** `summary_label`/`_on_header_toggled`/`is_collapsed`/`set_collapsed`/`toggle_collapsed`, `set_account_summary`/`set_account_id`/`set_account_unavailable`, `set_positions`/`add_position`, `refresh`/`_render_summary`/`_group_and_render`, `account_summary_changed`, `positions_changed`, `_unrealized_pnl`, `RIGHT_DOCK_MIN_WIDTH`'s value. |
| `ui/trade_context_menu.py` | **delete** | whole file |
| `ui/stop_loss_target_dialog.py` | **delete** | whole file |
| `tests/test_sltp_honesty.py` | **delete** | whole file (both cases assert the deleted dialog's labels) |
| `tests/test_d27_position_id.py` | edit | `:164`–`:165` `8`/`9` → `6`/`7`. **Nothing else** — the AC3 case was already removed in **wave 2** with the window half of its subject (R2). **Keep** the AC1 live-update case and the AC2 bulk-`id` case (the D27.1 id-correctness property stays covered there). |
| `tests/test_d27_flat_rows.py` | edit | **AC-3 only.** Delete `table.selectRow(0)` + `qapp.processEvents()` (`:108`–`:109`) and the two `panel._selected_position` assertions (`:110`–`:111`) — the tracker they read is deleted by this task (`AP-D45-4`, R1). **Keep `:104`–`:106` verbatim** (`rowCount() == len(panel._positions)`, plus the per-row `symbol`/column-0 alignment) — that is the property AC3 exists for. Rewrite the docstring's AC3 sentence (`:11`–`:13`), which names `_on_selection_changed`/`_selected_position`, to: *"AC3: the panel's position list and its rendered rows stay index-aligned, so a row index resolves to the row the user sees."* AC1/AC2 cases untouched. |
| `tests/test_d27_position_prices.py` | edit | `:290`–`:291` `8`/`9` → `6`/`7`. Nothing else. |

### Wave 4 — `D45-04` (Group C)

| File | Action | Precise change |
|---|---|---|
| `ui/main_window.py` | edit | Remove `self.kill_btn` (text `"Kill Switch"`, `setObjectName("KillSwitchButton")`, tooltip, `#b91c1c` style, `clicked.connect`), **the `QLabel("|")` separator immediately before it**, `_on_kill_switch_clicked`, and `_kill_switch` (incl. `self.ib_client.reqGlobalCancel()`, the per-ID `self.ib_client.cancelOrder(oid)` loop, the terminal-status pre-count, the `order_registry.update_status(oid, "Cancelled")` marking and the pre/post status-bar message). The toolbar keeps its remaining widgets and its trailing `addStretch()`. **No replacement control; no teardown/disconnect cancel.** |
| `tests/test_kill_switch.py` | **delete** | whole file (4 cases; its `test_bracket_builder_registers_all_three_legs` also drives `_kill_switch`) |

### Wave 5 — `D45-05` (docs)

| File | Action | Precise change |
|---|---|---|
| `USAGE.txt` | edit | Remove the Close/Close Group/Close All Positions section, the **Kill switch** bullet, the **Set Stop-Loss / Take-Profit** bullet, the "orders cannot be placed while disconnected" claim, and the **`View → News Digest (Ctrl+Shift+N)`** section. Add/keep one plain statement: **the app places, cancels and closes nothing — closes and cancels happen in TWS**, and the Portfolio panel is view-only; stop/target values saved before this version stay in the database but are no longer settable or shown. |
| `usage.md` | edit | Rework `### Portfolio & SL/TP` (heading + steps 2–3: no right-click close/flatten, no SL/TP dialog) into a view-only description; correct the Portfolio table row (line ~102: no "SL/TP, close/flatten actions"); in the Database section keep `positions` / `trade_groups` listed **with a note** that SL/TP stay **stored** but are no longer settable in-app; remove any news-digest mention. |

*(`docs/codebase-map.md` is **Plan-owned** and already refreshed in this batch — it is **not** a Build task.)*

### Wave 6 — `D45-06` (instrument + gate)

| File | Action | Precise change |
|---|---|---|
| `tests/test_d45_removal.py` | **create** | The `S36` instrument: (a) `importlib.util.find_spec` returns `None` for the five deleted modules and the five deleted suites are absent; (b) an AST token scan over `ui/`, `services/`, `data/`, `ibkr/`, `config/` (identifiers **and** string constants, D41 precedent) finds none of the tokens in § *The residue verification step* outside the explicit survivor allow-list; (c) `ui/` contains no `placeOrder`/`cancelOrder`/`reqGlobalCancel` call site; (d) a real offscreen `MainWindow` with a mocked `IBApiClient.connect` and mocked `placeOrder`/`cancelOrder`/`reqGlobalCancel` driven through **every remaining affordance** (chart load, timeframe/mode/ext-hours switches, watchlist add/remove + column popup, alarms, studies, drawings, pop-outs, Portfolio selection + refresh, an external position update/close, a `_on_order_error` emission, `closeEvent`) asserts all three call counts are **0**; (e) the position table has `columnCount() == 8` with no `Stop`/`Target` header and Strategy/Group at `6`/`7`; (f) the dividend path is still alive (`"456"` registered, tick 59 → `dividend_updated`, `event_count() > 0`); (g) the `AC-D45.3` measurables asserted **directly** (the token list is a net, not a
substitute): `hasattr(panel, name) is False` for the nine removed panel members (`_show_context_menu`,
`_on_close_position`, `_on_close_group`, `_on_ungroup`, `_on_flatten_all`, `_selected_row`,
`_selected_position`, `_on_selection_changed`, `set_sltp_action`) and for the five removed signals, plus
`panel.positions_table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu`. |
| everything | **verify** | Full residue grep, full offscreen suite, import/launch check, and the **RED-on-`c702be9`** evidence (§ Tests). |

---

## Tests: deleted, adjusted, kept, and why each still means something

### Deleted — five whole files (A81, `AC-D45.8`), all named; nothing rests on a count

| File | Subject that no longer exists | Coverage consequence (stated, not hidden) |
|---|---|---|
| `tests/test_d28_6_close_contracts.py` | `_close_position_by_id`'s contract rebuild + the disconnected gate | the only close-order contract/flatten coverage is gone |
| `tests/test_d41_retained_order_path.py` | `validate_order` + `_ref_price_for` + the retained order path | the retained-order-path assertions (D41-S4/S5) are gone with the path |
| `tests/test_order_validation.py` | `validate_order` (table-driven) | the notional/STP/BRACKET gate has no subject any more |
| `tests/test_kill_switch.py` | `_kill_switch` (4 cases) | the only **cancel-path** coverage, and the only *integration* driver of `Orders`/`bracket_order` registration, is gone |
| `tests/test_sltp_honesty.py` | `StopLossTargetDialog`'s disclosure labels | the only assertion that the SL/TP dialog transmitted nothing |

### Adjusted — seven files, each with the exact invalidated assertion

| File | Invalidated assertion | Adjustment | Why it is invalidated |
|---|---|---|---|
| `tests/test_d38_events_news.py` | the 3 `NewsManager` cases + the 3 digest cases (`AC-D38.2`/`.3`) | remove both sections; keep everything else | `ibkr/news.py` and the dock are deleted (`AC-D38.2`/`.3` **superseded**) |
| `tests/test_dock_d18_region.py` | `:147` `objectName() != "NewsDigest"` filter; `:174`–`:179` five-signal receiver loop | drop the filter (wave 1); **delete the loop** and restate the wiring comment (wave 2) | the dock no longer exists; and after wave 2 the window connects none of the five removed signals, while the panel still defines them — a loop asserting "≥1 receiver" would be red for a reason already decided, and a loop asserting `hasattr` could not go green until wave 3 |
| `tests/test_order_rejections.py` | `test_close_blocked_while_disconnected` drives `_close_position_by_id` | delete that case; keep helpers + `_on_order_error`/`classify_error` cases | the disconnected-order gate has no order path to guard (`AC-D26.9` moot); the **observer** path it also covers is retained (A90) |
| `tests/test_d28_pacing.py` | `test_close_position_defers_when_limiter_empty` | delete the case only | it drives `_close_position_by_id` and pins the (deleted) gate-before-pacing order |
| `tests/test_d27_position_id.py` | `test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row` (`:170`–`:201`); `:164`–`:165` `item(0, 8)`/`(0, 9)` | remove that case **in wave 2**; `8`/`9` → `6`/`7` **in wave 3** | its subject is deleted in **two halves** — the window connection/handler in wave 2, the panel setter in wave 3 — so the case cannot outlive either (R2); the columns shift in wave 3 |
| `tests/test_d27_flat_rows.py` | `:108`–`:111` — `table.selectRow(0)` then `assert panel._selected_position is not None` / `.symbol == table.item(0, 0).text()` | drop `:108`–`:111`; keep `:104`–`:106`; restate the AC3 docstring sentence | `AP-D45-4` deletes the selection tracker in wave 3 and every reader of it is deleted in the same batch, so the assertion's subject no longer exists (R1). The index-alignment property it guards stays asserted |
| `tests/test_d27_position_prices.py` | `:290`–`:291` Strategy/Group at `8`/`9` | `8`/`9` → `6`/`7` | the columns shifted (R75) |

> **Exactness note for Task Manager:** the Group B split makes the `test_dock_d18_region.py` receiver loop
> unassertable in the middle of the batch — after wave 2 the **window** connects none of the five signals,
> while the **panel** still defines them (they are deleted only in wave 3). Asserting "≥1 receiver" would be
> red for an already-decided reason; asserting `hasattr(...) is False` could not go green until wave 3. So the
> loop is **deleted in wave 2** and the file carries no reference to the removed signals afterwards, which is
> the correct end state for both waves. The one remaining D45-related adjustment to that file is the `:147`
> dock filter in wave 1. Recorded so the second half is not "discovered" as a regression.
>
> **Deviation from the D45 register's suggested form (R4 / `RG-D45-1`) — do not "restore" it.** The register's
> own correction record (`requirements.md:4178`–`:4179`) and `design_gaps.md` DG77 item 4 both describe this
> same edit as "the five-signal receiver loop **shrinks to three**". That form is **unachievable**: D45 deletes
> **all five** signals (the three close signals in Group B-main and the two SL/TP signals in the extension), so
> after the batch **no signal survives** — a three-signal loop would reference three deleted attributes and be
> red in wave 3, while in wave 2 it would be red for the already-decided reason that the window connects none
> of them. The loop is therefore **deleted whole** in wave 2, which is exactly what `AC-D45.8` asks (the file
> is *adjusted*; no clause names a surviving signal). Recorded here, in `docs/plan_notes.md` `RG-D45-1`, in the
> architecture's System-Components row and in its supersession list (item 10), so Task Manager / Code Reviewer
> do not read the register's suggestion as pending work.

### Kept by decision — verified individually, not assumed

| File | Decision | Verification performed in this run | Why it still means something |
|---|---|---|---|
| `tests/test_stop_loss_target.py` | **keep unchanged** | reads only `data.models.Position`/`TradeGroup`; 3 cases, no UI import, no dialog reference | A87 keeps the model fields, so "the fields exist, default `None`, accept explicit values" is still true and still worth asserting |
| `tests/test_d41_removal.py` | **keep unchanged** | its only news reference is the `queue_depth` **string** in `_ALLOWED_ANYWHERE`; its scan reads `ui/ services/ data/ ibkr/ config/` only and `queue_depth` never needs to resolve | it still guards D41's removals (footprint/depth/auction/order-entry UI), which D45 does not restore |
| `tests/test_order_builders.py` | **keep unchanged** | covers builders (`market_order`/`limit_order`/`stop_order`/`bracket_order` incl. OCA groups + `transmit` flags) **and** the registry (`register`/`get`/`update_status`/`clear_filled`/`all`) | **this is the residual unit coverage of the retained `ibkr/orders.py`** — DG77's "no tests at all" is corrected here: what the deletions took was the *integration* driver, not the module's own coverage |
| `tests/test_d27_position_id.py`'s **AC2** case | **keep** | asserts `_on_position_end` stamps each row's real `positions.id` | the D27.1 id-correctness property (ESC-032) survives even though the AC3 SL/TP row-addressing case cannot |
| every other suite | **untouched** | a `tests/`-wide scan found **no** other reference to the removed tokens (the nine panel members, the five signals, the deleted modules/methods, `_kill_switch`): the Portfolio context menu appears only in watchlist tests (a different, retained popup); no `positions_table.columnCount()` equality assertion other than the two named index files. The **one** file the book carries beyond the obvious set is `tests/test_d27_flat_rows.py` — its AC3 tail reads `_selected_position`; adjusted in wave 3 (R1) | the suite's remaining 125+ modules build windows, charts, docks and pop-outs — the batch gate runs them all |

### Added — one module

`tests/test_d45_removal.py` (wave 6). It must be **discriminating**: run it against a pristine `c702be9` copy
(`git worktree add`, or a copy of the tree) and record the **exact** failures it produces there (e.g. the token
scan reporting `kill_btn`, `_kill_switch`, `reqGlobalCancel`, `cancelOrder`, `placeOrder`,
`StopLossTargetDialog`, `position_sltp_changed`, `NewsManager`, `TradeContextMenu`, `validate_order`, …; the
walkthrough reporting non-zero cancel calls). A guard that passes on both trees is not a guard — that evidence
is part of the task's acceptance, not a nicety.

---

## The residue verification step (task-level, not a hope)

D45's correction record asks Build to grep **after each file**, per group. This plan makes that a **named,
checkable step in every wave** and a **full pass in wave 6**, with the **survivor allow-list** beside it — so
"fix the residue" cannot be satisfied by deleting things the requirement keeps.

**The two instruments, and their exact scope (R3).** They are **not** the same net, and the difference is
load-bearing:

1. **AST scan** — identifiers **and** string constants (the `tests/test_d41_removal.py` precedent) over
   **`ui/ services/ data/ ibkr/ config/`**. It reads *code*, so **comments are invisible to it**: the D26.7
   comment in `config/settings.py` that names `validate_order()` is **not** an offence, and
   `config/settings.py` is a file **no D45 task may edit** (`AP-D45-11`).
2. **Grep step** — **`ui/` only** (the prose net for human workers), after each edited file and once per wave.
3. **`tests/` is covered by neither instrument.** The residue list is therefore a net, not a substitute for
   the test book: `AC-D45.3`'s `hasattr(...) is False` measurables are asserted **directly** in
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
**only** in `ui/active_portfolio_panel.py` (plus `ui/trade_context_menu.py` for `set_sltp_action`), both of
which this batch edits/deletes ⇒ **zero** post-D45 hits: `_show_context_menu` 2 · `_on_close_position` 2 ·
`_on_close_group` 2 · `_on_ungroup` 2 · `_on_flatten_all` 2 · `_selected_row` 4 · `_selected_position` 13 ·
`_on_selection_changed` 4 · `set_sltp_action` 4.*

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

## Assumptions

| # | Assumption | Rationale |
|---|---|---|
| **AP-D45-1** | **`ibkr/orders.py` is retained, not deleted** (architecture `S29`). No task touches its API; the only permitted edit is a module-docstring note stating it is unreachable after D45. | DG76 is Plan-level and A80 defaults to "leave it". The module is **not** orphaned — `ui/main_window.py:36` imports the `orders` singleton for the retained observers (A90) — and deleting it would force registry-safe rewrites of the error path for zero reachability gain while discarding `tests/test_order_builders.py`'s real coverage. The requirement measures **unreachability**, not file existence. |
| **AP-D45-2** | **`MainWindow._ref_price_for` is deleted**; `_symbol_last_prices` stays. | Verified: one production caller (inside `_close_position_by_id`), zero after wave 2. R74 names a leftover `_ref_price_for` as a half-removed-path residue; keeping it would leave an order accessor with no consumer. The price map itself is read by the Portfolio P/L path (`:3207`) and **must not** be touched. |
| **AP-D45-3** | **`_s0_headless` removal is a three-site edit** (the attribute + the two `or self._s0_headless` clauses). A worker that removes only the attribute leaves a live `AttributeError`, and one that removes only the flag leaves a dead always-`False` condition. | Set only by the deleted digest; read in two S0 line-build paths. Recorded because it is the least discoverable part of Group A. |
| **AP-D45-4** | **The panel's selection tracking goes with the menu** (`_selected_row`, `_selected_position`, `_on_selection_changed`, its `itemSelectionChanged` connection, and the two comments naming it). | Every **production** reader is a handler this batch deletes (`_show_context_menu` :372, `_on_set_sltp` :377–379, `_on_close_position` :400–401, `_on_close_group` :405–406, `_on_ungroup` :410–411), and `_on_selection_changed`'s only other effect is `self._context_menu.set_actions_enabled(...)` (:358/:364/:368) — also deleted (re-verified `ui/`-wide 2026-10-25). The **one** reader outside the panel is `tests/test_d27_flat_rows.py:110`–`:111`; that file is adjusted in the **same wave** (R1), so the tracker does not outlive its last reader. If a worker finds any other consumer it must **stop and report**, not silently keep a half-wired tracker. |
| **AP-D45-5** | **Group B is window-first** (waves 2 → 3), never panel-first. | Panel-first makes `MainWindow.__init__` connect deleted signals → `AttributeError` in every window test (architecture `S37`). |
| **AP-D45-6** | **One task per wave on `ui/main_window.py`** (waves 1, 2, 4), strictly sequential; no two tasks in one wave may share a file. | The scheduler forbids overlapping `touches_files` within a wave; explicit dependency edges make the order deterministic. |
| **AP-D45-7** | **All doc edits are one task** (wave 5); `docs/codebase-map.md` is **Plan-owned** and already refreshed, so it is not a Build task. | Three groups would otherwise edit the same prose in three waves; the map is a per-batch Plan artifact (memory 2026-10-23). |
| **AP-D45-8** | **`tests/test_d41_removal.py` and `tests/test_stop_loss_target.py` are kept unchanged**, verified above rather than assumed. | `AC-D45.8` names the first explicitly; A87 implies the second (model fields stay). |
| **AP-D45-9** | **`tests/test_order_builders.py` stays** and is the residual unit coverage of the retained `ibkr/orders.py`. | Corrects DG77's premise; recorded so the module is not "found" untested later — and so no task deletes that file while tidying. |
| **AP-D45-10** | **The new guard scans identifiers AND string constants** (the `tests/test_d41_removal.py` precedent), with the explicit survivor allow-list above; therefore **docstrings naming a removed member must be rewritten in the same wave** (a comment is invisible to AST, a docstring/string constant is not). | Prevents a wave from being "green by grep, red by AST"; and prevents a false residue report from a survivor. |
| **AP-D45-11** | **`config/settings.MAX_ORDER_NOTIONAL` and `ibkr/pacing.order_limiter` are left in place** (no edit, no deletion). | Outside the owner's named inventory (`A85` scopes docs; the requirement names no config module). They are dead config/helper, recorded in *Incidentally affected* rather than silently cleaned. |
| **AP-D45-12** | The requirements' `_persist_position` is the tree's **`_upsert_position`**; no rename. | Naming drift in the requirements text; the symbol is unambiguous and the method is untouched by D45. |
| **AP-D45-13** | The test book is **5 deleted / 7 adjusted / 1 added** whole files, with case-level trims in six of the adjusted files (all but `tests/test_d27_position_prices.py`, which is a two-line index change). No other file changes. | Matches `A81`/`AC-D45.8` exactly — five **named** whole-file deletions, and every invalidated assertion outside them enumerated; a `tests/`-wide scan found no eighth affected file. The seventh is `tests/test_d27_flat_rows.py` (the AC3 `_selected_position` tail — R1). |

---

## Flagged Issues

**None blocking.** Every requirement in D45 (`D45.1`–`D45.6`, `AC-D45.1`–`AC-D45.10`, Journey 38) is
satisfiable as written by the decisions above — the removals are self-contained, the only shared mechanism
(the S0 register) is preserved by construction, and the storage requirement (A87) needs **no** migration. No
requirement was narrowed or reinterpreted to fit a convenient architecture.

**Recorded for the Validator's awareness — deliberately *not* escalated (each is a note, not a requirement
defect):**

1. **Naming drift:** the requirements say the SL/TP persistence slots' "position upsert in `_persist_position`"
   stays unchanged; the tree's method is **`_upsert_position`** (`ui/main_window.py:3283`). Same method, same
   behaviour; `AP-D45-12`. No doc change is asked of Requirements because the intent is unambiguous.
2. **Two dead remnants are intentionally left standing:** `config/settings.MAX_ORDER_NOTIONAL` (only consumer
   was the deleted `ibkr/validation.py`) and `ibkr/pacing.order_limiter` (order-path bucket, now unread).
   Deleting them would exceed the owner's named inventory and touch shared modules (`AP-D45-11`); D45's
   consequence 3 ("the notional cap … no longer gate anything") already records the *mootness*.
3. **`docs/codebase-map.md`'s generated skeleton** is rebuilt from the tree by `update_codebase_map.py`, so it
   will keep listing the deleted files **until the next batch's refresh**; `AC-D45.7`'s "the map no longer
   lists …" is satisfied by the Plan-owned **annotation tables**, which are rewritten to the post-D45 target
   state and say so in the map's header (`S38`). This is a property of the tooling, not an unmet criterion.

---

## Correction record — for Task Manager / Build / Code Reviewer

**Plan (this run):** refreshed `docs/codebase-map.md` (re-ran `update_codebase_map.py`; rewrote the annotation
layer: the three removed modules and `ibkr/validation` no longer live; `_kill_switch` / `StopLossTargetDialog`
no longer named as retained; the **`placeOrder` ownership error corrected** — it is ibapi's inherited
`EClient.placeOrder`, not an `IBApiClient` method; `ibkr/orders.py` recorded as **retained with no transmit
caller**; the D45 test book and the wave order added). Replaced both proposal files wholesale (the D44 pair).
**Round 2:** R1–R4 applied — the selection tracker deleted with an added wave-3 file, the D27.1 AC3 removal
moved to wave 2, the residue instrument's list and scope made true, the D18 receiver-loop row reconciled
(`docs/codebase-map.md`'s book updated to 7 adjusted).

**Task Manager:**
- Build the six waves with **explicit dependency edges** `D45-01 → D45-02 → D45-03 → D45-04 → D45-05 → D45-06`
  (`ui/main_window.py` in 1/2/4, `tests/test_dock_d18_region.py` in 1/2). Do **not** let two tasks share a file
  in a wave.
- **Enumerate invalidated assertions outside the edited files** (memory 2026-10-23 item 4; `ESC-055` rule):
  `tests/test_d41_removal.py` (verified green), `tests/test_dock_d18_region.py` (`:147` wave 1;
  `:174`–`:179` wave 2), `tests/test_d38_events_news.py` (two sections), `tests/test_d27_position_id.py`
  (**the SL/TP case in wave 2**; `8`/`9` in **wave 3**), `tests/test_d27_flat_rows.py` (`:108`–`:111`,
  wave 3), `tests/test_d27_position_prices.py` (`8`/`9`), `tests/test_stop_loss_target.py` (verified green),
  `tests/test_order_builders.py` (verified green).
- **Honour the wave-membership rule**: an assertion whose subject dies in wave *N* is removed or adjusted in
  wave *N*. Do **not** merge the two `tests/test_d27_position_id.py` edits into one task, and do not schedule
  either in a wave that does not also carry the change that invalidates it.
- **Do NOT task any change to `ibkr/orders.py`** beyond the permitted docstring note (`AP-D45-1`), and do not
  task any config/pacing cleanup (`AP-D45-11`).
- Wave 6's acceptance includes the **RED-on-`c702be9`** evidence for the new guard.

**Build:**
- Split by **member group**, and **run a syntax/import check plus the group's residue grep after each file**
  (the D41 worker-death mitigation, memory 2026-10-15).
- Every delete-only task: **`git status` the file list before finishing** — a "done" task that left a file half
  edited is the failure mode that killed three D41 workers.
- Deletions are **whole-file only** where the table says "delete"; any partial trim is enumerated in the
  per-file map above and nowhere else.
- Comments referencing a deleted member are prose; **docstrings or string constants naming one must be
  rewritten in the same wave** (`AP-D45-10`) or the wave-6 scan fails.

**Code Reviewer (independent, do not trust the task book):**
- Confirm **zero** `placeOrder`, **zero** `cancelOrder`, **zero** `reqGlobalCancel` call sites in `ui/`.
- Confirm **the dividend markers still render** (`"456"` registered; tick 59 → `dividend_updated`;
  `event_count() > 0`) — the single highest-risk deletion (R68).
- Confirm the positions table has **8 columns** with no `Stop`/`Target` header and that Strategy/Group sit at
  `6`/`7`.
- Confirm a **pre-D45 database** opens with its stored `stop_loss`/`take_profit` values intact and that
  `_upsert_position` still writes them (no migration, no data loss).
- Confirm the three docs advertise nothing removed, and that `docs/codebase-map.md` no longer names
  `_kill_switch`, `StopLossTargetDialog`, `ui/news_digest_dock`, `ui/trade_context_menu` or
  `ui/stop_loss_target_dialog` as live/retained.
- Confirm the **new guard is discriminating** (its pre-`c702be9` failures are recorded) and that the
  intentional survivors (A90's observers, the ibapi news signals, the dividend path) were **not** deleted.

---

## Incidentally affected (noted, not absorbed)

- **`config/settings.py::MAX_ORDER_NOTIONAL`** (and its D26.7 comment) — its only consumer was the deleted
  `ibkr/validation.py`; now dead config. **Deliberately not cleaned** (`AP-D45-11`): it is outside the owner's
  inventory and a config edit is not required for any D45 criterion.
- **`ibkr/pacing.py::order_limiter`** — the order-path bucket; no reader after D45. **Deliberately untouched**
  (shared, tested module; `pacing_manager` and the historical-pacing guarantees stay live).
- **`ibkr/bridge.py` news signals + `ibkr/client.py` news overrides** — become unconnected rather than
  removed (`S35`). A future reader may mistake them for leftovers; the map and A90 record them as the ibapi
  boundary.
- **`tests/test_d38_events_news.py`'s module docstring** lists `AC-D38.2`/`AC-D38.3` and "NewsManager sequential
  issuance" — trimmed by wave 1; its `test_md_line_guard_thresholds` docstring names `"292"`/`"456"` and is
  corrected to the surviving `"456"` line.
- **`tests/test_d41_removal.py`'s `queue_depth` allow-list entry** — survives the `ibkr/news.py` deletion as a
  string; the file is **not** edited (`AC-D45.8` names it as kept).
- **`ui/main_window.py`'s `ibkr.pacing` / `ibkr.orders` import lines** carry names that become unused
  (`order_limiter`, `UserOrder`, and the already-unused `pacing_manager`) — trimmed in wave 2 so the file has no
  dead import; `PacingExceeded` and `orders as order_registry` **must stay**.
- **macOS application menu** — with `menuBar()` gone the app contributes no app-menu items (A86). No
  replacement menubar, no orphan `QAction`.

---

## Handoff

Nothing in this pair is active until Plan Artifact Editor & Validator reviews it. The architecture decisions
live in `docs/architecture_proposal.md` (`S29`–`S38`, frozen interfaces, risks `AR-D45-1`–`AR-D45-10`); this
file owns the phase/wave sequencing, the per-file map, the test book, the residue verification and the
correction record.

Status: READY_FOR_VALIDATION
