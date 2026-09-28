# Plan Proposal — NDThinkChart Stabilization (revision 2: RC-1…RC-4 fixes, D2/Q33, AC-D3.9)

> This proposal is the **revision delta** to the approved canonical `docs/plan.md`
> (Batches 3–9: D7–D15, `Status: READY_FOR_TASK_MANAGER`). It was produced because
> the Orchestrator re-invoked Plan for the escalation routed to Plan (`ESC-002`),
> together with the companion wording escalations (`ESC-003`, `ESC-006`, `ESC-007`),
> the newly decided **D2/Q33 chip relocation**, the newly decided **`AC-D3.9`**, and
> the parallel-build contract (`touches_files` / `build_config.json`).
>
> **Revision 2** applies the Validator's `CHANGES_REQUIRED` items RC-1…RC-4
> (`docs/plan_review.md`) to revision 1. The two requirements escalations (RG-002,
> RG-003) are now **resolved in `requirements.md`** (2026-09-27), so this revision
> consumes settled requirements rather than flagged assumptions.
>
> The full architecture and transition-table detail lives in
> `docs/architecture_proposal.md`; this file is the phased plan and its coverage /
> sequencing consequences. The canonical `docs/plan.md` Phases 1–5 remain valid and
> are **kept**, with the amendments below applied by the Validator.

## Scope statement

This is **not** a re-plan of Batches 1–9. It is a targeted architectural completion:

1. **ESC-002 (High) + `AC-D3.9`** — replace implicit tri-boolean gesture precedence
   in `ui/chart_mouse_router.py` with an explicit `RouterMode` state machine and a
   **total** transition table, encoding the newly-decided interactions from
   `AC-D3.7` (both directions), `AC-D3.8`, and `AC-D3.9` (magnifier refused during
   alarm placement).
2. **RC-2 / Q33** — carry the **re-opened D2** redesign: the crosshair price chip
   renders in the **Y-axis lane outside the plot** (grey pill, white text,
   axis-tick-label overlap permitted); dock-open visibility is a **separately
   verified acceptance criterion** requiring independent Code Reviewer verification
   after Build. Re-scope `AC-D11.4` to **label-vs-label stacking only**.
3. **RC-1 / ESC-003 companion** — state the **one** continuous scaling nice-number
   formula (pinned family `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`, no fixed ceiling, no
   `10K` floor, smallest value `100`) and make every retained fixture agree with it.
4. **RC-3** — specify how `_active_mode` is derived/synchronised when overlays are
   wired directly, so the five preserved router tests pass verbatim.
5. **RC-4a** — correct the canonical D10 affordance wording to the checkable **text
   label `Volume`** (not an eye icon).
6. **RC-4b** — document the `view_mouse_click` behaviour change in `DRAWING` mode.
7. **ESC-007 companion** — correct the architecture's volume-ceiling claim: the
   ceiling must track the forming bar's live volume in **O(1) against a cached
   running max**.
8. **Parallel-build contract** — record the sequencing consequence of Task Manager's
   per-task `touches_files` field and `docs/build/build_config.json`
   (`max_parallel_tasks`, default 4).

No requirement is restated as new. All behaviours trace to `AC-D3.7`–`AC-D3.9`,
`AC-D2.1`–`AC-D2.3`, `AC-D8.1`–`AC-D8.7`, `AC-D10.1`, `AC-D11.4`, `AC-D14.4`, and
the Q31/Q33/Q35/Q36/A22/A25/A26 confirmations in `docs/requirements/requirements.md`.

## Completed (unchanged)

- Batch 1 (D1–D3) and Batch 2 (D4–D6) built and verified; the 2026-09-19
  `DrawingOverlay` drag-lifecycle runtime fix is in place. D8 supersedes D5 (linear).
- Canonical Phases 1–5 of `docs/plan.md` were approved (`plan_review.md`:
  `APPROVED`). They are the backbone; the amendments below are additive.

## Phases

### Phase R1 (NEW) — Router state machine (ESC-002, AC-D3.9, RC-3, RC-4b)

- **Goal:** Replace the implicit precedence in `ui/chart_mouse_router.py` (three
  independent flags over `ZoomOverlay.is_active()`, `DrawingOverlay.tool_active()`,
  `AlarmOverlay.is_alarm_mode()`, resolved only by call order) with:
  - a `RouterMode` enum — `IDLE`, `DRAWING`, `ZOOMING`, `ALARM_PLACING` — and a single
    `ChartMouseRouter._active_mode` (mutually exclusive by construction);
  - a **guard clause at the top of every handler** (`view_mouse_press`,
    `view_mouse_drag`, `view_mouse_click`) that dispatches on `_active_mode`;
  - the **explicit, total transition table** in `docs/architecture_proposal.md` §2.4,
    including **TR-4** (`AC-D3.7` forward — magnifier during `DRAWING` cancels the
    in-progress drawing, discards the draft, enters `ZOOMING`), **TR-5**
    (`AC-D3.7` reverse / A26 — drawing tool during `ZOOMING` exits `ZOOMING` and
    activates the tool), **TR-6** (`AC-D3.8` — alarm placement during `ZOOMING` exits
    `ZOOMING` and enters `ALARM_PLACING`), and **TR-9** (`AC-D3.9` — magnifier during
    `ALARM_PLACING` is **REFUSED**: mode stays `ALARM_PLACING`, the pending placement
    is **not cancelled**, a status-bar hint is shown);
  - **RC-3 derivation:** `drawing`/`alarm`/`zoom` become properties whose setters call
    `_reconcile_mode_from_overlays()` (precedence `DRAWING > ZOOMING > ALARM_PLACING >
    IDLE`, defensive `getattr` probes), so direct attribute wiring — exactly what the
    five preserved tests do — derives the mode. Handlers never re-derive the mode.
  - **RC-4b:** `view_mouse_click` in `DRAWING` dispatches to the drawing overlay only
    (documented; alarm mode is force-cleared whenever a drawing tool is armed).
  - the router as the **single writer of `_active_mode`**; `ChartPanel.set_zoom_mode`
    / `set_drawing_tool` / `set_alarm_mode` become thin adapters that call router
    intent helpers and keep the widget state in sync (signatures unchanged).
  - **`AC-D3.9` surfacing:** `enter_zoom()` returns `False` (no mode change) in
    `ALARM_PLACING`; `ChartPanel.set_zoom_mode(True)` re-unchecks the magnifier button
    and emits a `zoom_refused` signal; `MainWindow` connects it to
    `status_bar.showMessage(...)`.
- **Named tests to implement (verbatim — not a generic "router precedence" mention):**
  - **New:** `test_zoom_during_draw_cancels_draw`,
    `test_draw_blocked_during_zoom` (asserts the **confirmed reverse** rule: draw
    exits zoom), `test_alarm_placement_blocks_zoom`,
    **`test_magnifier_refused_during_alarm_placement`** (`AC-D3.9`),
    **`test_click_in_drawing_reaches_only_drawing`** (RC-4b).
  - **Mode-model:** `test_router_mode_is_mutually_exclusive`,
    `test_zoom_stays_active_after_completed_zoom`,
    `test_esc_cancels_selection_not_mode`,
    `test_reconcile_mode_from_wired_overlays` (the RC-3 mechanism).
  - **Preserved (must keep passing verbatim):**
    `test_alarm_press_wins_in_cursor_mode`, `test_drawing_tool_blocks_alarm_press`,
    `test_alarm_miss_falls_through_to_drawing`,
    `test_click_prefers_alarm_then_drawing`, `test_missing_overlays_are_safe`.
- **Requirements / journeys covered:** `AC-D3.7` (both directions), `AC-D3.8`,
  `AC-D3.9`, `AC-D3.3`, `AC-D3.4`; Journey 4 edge cases; ESC-002.
- **Dependencies on earlier phases:** None.
- **Files:** `ui/chart_mouse_router.py` `[new/changed]`;
  `ui/chart_panel.py` (three adapters + `zoom_refused`) `[new/changed]`;
  `ui/main_window.py` (one status-bar connection) `[new/changed]`;
  `tests/test_chart_mouse_router.py` `[new/changed]`.
- **Sequencing:** **must be its own wave** — it modifies `ui/chart_panel.py` (also
  touched by R2/Phase 1/Phase 3) and `ui/main_window.py` (also touched by Phase 4).

### Phase R2 (NEW) — D2/Q33 crosshair chip relocation (RC-2)

- **Goal:** Move the crosshair `_price_tag` from the Batch-1 **inside-plot**
  right-aligned position (`view_rect.right() - 2`) to the **Y-axis lane outside the
  plot**, right of the plot's vertical axis line; render it as a **grey pill with
  white text** (`anchor=(0,0.5)` left-anchored at the axis line); **permit**
  axis-tick-label overlap (no deconfliction offset). Keep the existing
  show-only-inside-plot / hide-on-leave behaviour (`AC-D2.3`) and pan/zoom tracking
  (`AC-D2.2`).
- **Dock-open visibility (`AC-D2.1` + edge case):** with the Active Trader and/or
  Portfolio dock open, the chip's full label (all decimals) must be visible and not
  covered by the dock. Because this **re-opens the original D2 defect surface**, it
  requires **independent Code Reviewer verification after Build** (A25) — the Batch-1
  fix must not be assumed to still hold.
- **D11 re-scope:** `AC-D11.4` applies to **label-vs-label stacking inside the plot
  only**; the chip is lane-separated and out of scope for that criterion (ESC-006
  re-scoped).
- **Named test:** `test_crosshair_chip_renders_in_axis_lane` (chip scene `x >=
  view_rect.right()`, left anchor, grey fill, white text). The dock-open check is the
  Code Reviewer's independent verification.
- **Requirements covered:** D2 (`AC-D2.1`–`AC-D2.3`), Q33/A25; `AC-D11.4`.
- **Dependencies on earlier phases:** None, but shares `ui/chart_panel.py` with
  R1/Phase 1/Phase 3 (serial chain).
- **Files:** `ui/chart_panel.py` `[new/changed]`; new/updated crosshair test `[new]`.

### Phase 1 (AMENDED) — Chart geometry: gap, volume width, volume axis (D7, D9, D8)

Canonical Phase 1 stands. Two amendments:

- **Amendment A — nice-number formula (RC-1 / ESC-003 / RG-002 resolved;
  `AC-D8.4`/`AC-D8.5`).** The volume ceiling is generated by **one** continuous
  scaling "nice number" formula over **one** candidate family:
  **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (`10 × 10^k` is the next decade's `1`),
  with **no fixed ceiling and no `10K` floor**:
  `nice_max = the smallest family value >= max_vol * 1.1`; `max_vol == 0` → the
  smallest value **`100`**. The formula is a **pure importable function** (same shape
  as today's `_nice_volume_max`) and is unit-testable without a `qapp`. Testable
  properties: monotonic non-decreasing; tight coverage
  `nice_max / (max_vol * 1.1) <= 2` where the ceiling is above the required `100` floor
  (`max_vol >= 100 / 2.2 ≈ 45.5`; below that the ceiling is the floor `100`, per
  PA-R8); the 40–50M cases (`45M → 50M`, `50M → 75M`) come
  from the family (no coarse 5M fallback). **The original fixed list
  `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]` is retained
  only as a test fixture** — every entry is a member of the pinned family, so the
  fixture stays valid; it is never a live code path. **Values to preserve:** the
  validated axis set (`500.0K / 1.0M / 1.5M / 2.0M / 2.5M` ticks per Q20) and the
  canonical `0` lower bound with no negatives.
  - **Existing-test consequence (flagged, requirement-backed):** of the assertions in
    `tests/test_volume_linear.py:57–61`, **only** `_nice_volume_max(0) == 10_000` is
    stale and must become **`100`** (`AC-D8.4`). `_nice_volume_max(8_000) == 10_000`,
    `(80_000) == 100_000`, `(2_200_000) == 2_500_000` and
    `(1_050_000) == 1_500_000` are **retained as fixture cross-checks** (all correct
    under the pinned family). *(This corrects revision 1, which wrongly flagged
    `(8_000) == 10_000` for change.)*
- **Amendment B — live ceiling (ESC-007 companion; `AC-D8.6`/`AC-D8.7`).** Correct
  the canonical architecture claim that `nice_max` is "not per intra-bar tick". The
  ceiling currently updates only under `if auto_range:` in `_refresh_candles`, while
  `update_last_bar` calls `_refresh_candles(auto_range=False)` — so the forming bar
  is clipped once its live volume passes the initial ceiling. Decided behaviour: the
  ceiling **also updates on RT volume changes**, in **O(1) against a cached running
  max** — keep a cached `_vol_max` from the load, compute
  `live_max = max(cached_max, last_bar.volume)` per tick, and **only widen** when
  `live_max` crosses the current `nice_max` (a tick that does not cross a boundary
  performs no range write). The `auto_range=False` refresh paths (`set_timezone()`)
  re-apply the cached ceiling so the axis is not stale. This is an **explicit
  exception to the per-load rule**; the full O(N) recompute stays on `update_chart`
  only, and its `nice_max` comes from Amendment A.
  - **Named tests:** `test_volume_ceiling_tracks_live_bar` and
    `test_volume_ceiling_refit_on_timezone_refresh` (`AC-D8.7`).
- **Requirements / journeys covered:** D7 (AC-D7.1–7.2), D9 (AC-D9.1–9.2), D8
  (`AC-D8.1`–`AC-D8.7` incl. the ESC-003/007/008 criteria); A11, A24, R9, R10, R20;
  DG8, DG9.
- **Dependencies on earlier phases:** None technically.
- **Files:** `ui/candlestick_item.py`, `ui/chart_panel.py`,
  `tests/test_volume_linear.py` (+ new volume-ceiling tests).

### Phase 2 (UNCHANGED) — Drawing visuals: inner-right labels + double-click dialogs (D11, D12, D15)

Canonical Phase 2 stands with no amendment. `AC-D11.4` remains scoped to
**label-vs-label stacking** (Q33/ESC-006 re-scope — the crosshair chip now lives in
the Y-axis lane, §5.4 of the architecture). Files: `ui/drawing_overlay.py` and the
two dialogs.

### Phase 3 (UNCHANGED) — Volume panel visibility toggle (D10)

Canonical Phase 3 stands with **one documentation correction** (RC-4a): the D10
affordance is the checkable **text label `Volume`** (Q31/A22/`AC-D10.1`) at the top
left of the volume panel (bottom left of the price chart, A23), **not** an eye icon.
The canonical `docs/architecture.md:30` "(eye icon)" wording must be rewritten (§5.5
of the architecture). Files: `ui/chart_panel.py` (volume plot + splitter). **Note the
`chart_panel.py` overlap** with R1/R2/Phase 1 — see sequencing.

### Phase 4 (AMENDED) — Watchlist resize + double-click load (D13, D14)

Canonical Phase 4 stands, with one amendment:

- **Amendment — symbol change resets router mode.** A symbol change (including the D14
  mid-drag double-click path, `AC-D14.4`) while a drawing drag/draft is in progress
  must bring the router back to `IDLE` in addition to clearing the overlay's
  draft/drag state (`DrawingOverlay.set_data()` already clears it defensively at
  `:112–118`). Otherwise `_active_mode` can read `DRAWING` after the tool was
  implicitly cleared. Verified by the ESC-010 regression test (`AC-D14.4`) plus a
  mode assertion.
- **Soft dependency:** the mode-reset clause is only verifiable once Phase R1 lands,
  but the watchlist/QSettings work itself is independent.
- **Files:** `ui/watchlist_panel.py`, `ui/main_window.py`, `QSettings` read/write
  site, `tests/` (watchlist + `AC-D14.4` regression). **`ui/main_window.py` now also
  conflicts with Phase R1** (status-bar connection) — serialize.

### Phase 5 (AMENDED) — Verification and regression (all batches)

Canonical Phase 5 stands, with added coverage:

- Router mode transitions — the §2.6 named tests (new + `AC-D3.9` + preserved +
  mode-model + reconciliation).
- Nice-number generator — the §3.2 family/formula, monotonic, tight coverage
  (`<= 2`), floor `100`, the `40M–50M` cases, and the legacy-list fixture
  cross-checks.
- Live ceiling — `test_volume_ceiling_tracks_live_bar`,
  `test_volume_ceiling_refit_on_timezone_refresh`.
- D2 chip — `test_crosshair_chip_renders_in_axis_lane`, plus the **Code Reviewer's
  independent dock-open verification** for `AC-D2.1`.
- `touches_files`-aware sequencing honoured (no two built tasks in a wave share a
  file).
- Global criteria unchanged: the pre-existing suite stays green offscreen
  (`QT_QPA_PLATFORM=offscreen`), no live-TWS connection or order transmission (Q8/Q9).

## Parallel sequencing (Task Manager contract change)

The pipeline contract requires the Task Manager to add a **`touches_files`** field to
every task so Build's Lead (a Lead + Worker pair) can dispatch non-conflicting tasks
in parallel up to `max_parallel_tasks` (default 4; optional user-owned
`docs/build/build_config.json`). Sequencing consequence for this revision — the file
map is the input the Task Manager should use to populate `touches_files`:

| File | Phases that touch it | Consequence |
|---|---|---|
| `ui/chart_panel.py` | R1 (router adapters + `zoom_refused`), R2 (crosshair chip), 1 (volume axis/ceiling/width), 3 (volume toggle + splitter) | **Serial chain** — R1, R2, Phase 1, and Phase 3 must not share a wave |
| `ui/main_window.py` | R1 (status-bar connection), 4 (watchlist wiring) | **Serial** — R1 and Phase 4 must not share a wave |
| `ui/chart_mouse_router.py` | R1 only | R1's core file |
| `ui/drawing_overlay.py` | 2, plus the Phase-4 mode-reset amendment | Serial with itself |
| `ui/zoom_overlay.py` | R1 (read-mostly; any change must be flagged) | Serial with R1 |
| `ui/candlestick_item.py` | 1 (D7 gap) | May run parallel with `chart_panel`/`main_window` tasks |
| `ui/watchlist_panel.py`, `QSettings` site | 4 | May run concurrently with Phase 1/3/R2 (its `main_window.py` part serializes with R1) |
| New dialog files (`ui/zone_settings_dialog.py`, `ui/horizontal_line_settings_dialog.py`) | 2 | New files → may run concurrently with Phase 1/3/R1/R2 |
| `tests/test_chart_mouse_router.py` | R1 | Serial per file |
| `tests/test_volume_linear.py` + new volume tests | 1 | Serial per file |
| New crosshair test | R2 | Serial per file |
| `tests/` watchlist + D14 regression | 4 | Serial per file |

Practical rule: **Phase R1 must be scheduled alone or with tasks that touch neither
`ui/chart_panel.py` nor `ui/main_window.py`**, because it rewrites `chart_panel`'s
`set_zoom_mode`/`set_drawing_tool`/`set_alarm_mode` adapters and adds the
`zoom_refused` connection. **Phase R2** is serial with R1/Phase 1/Phase 3 on
`chart_panel.py`. Phase 2's new dialog files and Phase 1's `candlestick_item.py` work
are the natural parallel companions. Verification tasks that touch the same test file
must be serialized. This is an **architecture-level constraint on the task graph**,
not a task decomposition: the Task Manager populates `touches_files`; the Lead
enforces the wave rule.

## Assumptions

Inherited and confirmed from `docs/requirements/requirements.md`: A8, A10–A20,
A22–A26 (and the canonical `PA1-batch3`…`PA8-batch3`), all unchanged.

New plan-level assumptions for this revision (full detail in
`docs/architecture_proposal.md` §9):

- **PA-R2.** `RouterMode.DRAWING` is synonymous with `DrawingOverlay.tool_active()`;
  an unarmed drawing tool is `IDLE`. No requirements gap.
- **PA-R3.** `test_draw_blocked_during_zoom` keeps the escalation-assigned **name**
  while asserting the **confirmed reverse** rule (draw exits zoom). No requirements
  gap.
- **PA-R4.** "Only widen" on intra-bar ceiling updates satisfies `AC-D8.6`'s
  "recomputed/**widened** … or the bound is explicitly documented" clause. No
  requirements gap.
- **PA-R5.** The original fixed nice list is retained **as a test fixture only**; of
  the existing `tests/test_volume_linear.py` assertions, **only**
  `_nice_volume_max(0) == 10_000` changes (→ `100`). Requirement-backed test change
  (Journey 1 edge case), not a silent test edit. No requirements gap.
- **PA-R6.** D2 chip implementation geometry: left-anchored at the axis line
  (`anchor=(0,0.5)`, scene `x = view_rect_scene.right()` + small pad), extending
  right into the Y-axis lane, with the existing in-view clamp and a right-edge guard
  so a long price is not clipped. Implementation detail; the lane/style/overlap are
  requirements. No requirements gap.
- **PA-R7.** `AC-D3.9`'s status-bar hint is surfaced by a new
  `ChartPanel.zoom_refused` signal connected in `MainWindow`; the exact hint string
  is a plan-level choice. No requirements gap.
- **PA-R8.** The `<= 2` tightness bound in `AC-D8.4` is asserted only where the
  ceiling is above the required `100` floor (equivalently `max_vol >= 100 / 2.2 ≈
  45.5`); below that threshold `nice_max` is the floor `100` (per `AC-D8.4`/A24), so
  the ratio can exceed `2`. Build must not write a test that contradicts the required
  floor. Test-scoping detail; no requirements gap.
- ~~**PA-R1** (`ALARM_PLACING → ZOOMING`)~~ — **RETIRED:** superseded by `AC-D3.9`
  (Q36 option (b)); the router refuses and stays in `ALARM_PLACING`.

## Requirements gaps surfaced

**None.** RG-002 (nice-number family) and RG-003 (`ALARM_PLACING → ZOOMING`) are both
**resolved in `requirements.md` (2026-09-27)** — the family is pinned to
`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`, and the magnifier is **refused** during alarm
placement (`AC-D3.9`). The D2/Q33 chip relocation and D11 re-scope are specified in
D2/D11 (`AC-D2.1`–`AC-D2.3`, `AC-D11.4`). `AC-D3.7` (both directions), `AC-D3.8` and
`AC-D8.4`–`AC-D8.7` are sufficient to build Phases R1/R2 and the Phase-1 amendments
without inventing behaviour.

## Coverage matrix

| Requirement / AC | Phase | Architectural treatment |
|---|---|---|
| `AC-D3.7` forward (Q35 option (a)) | R1 | TR-4 — magnifier during `DRAWING` cancels the drawing + discards the draft, enters `ZOOMING` |
| `AC-D3.7` reverse (A26, confirmed) | R1 | TR-5 — drawing tool during `ZOOMING` exits zoom + activates tool |
| `AC-D3.8` | R1 | TR-6 — alarm placement during `ZOOMING` exits zoom + enters `ALARM_PLACING` |
| **`AC-D3.9` (Q36 option (b))** | **R1** | **TR-9 — magnifier during `ALARM_PLACING` REFUSED: mode unchanged, placement intact, status-bar hint; `test_magnifier_refused_during_alarm_placement`** |
| `AC-D3.3`, `AC-D3.4` | R1 | TR-14/TR-15 sub-state vs mode; `test_esc_cancels_selection_not_mode`, `test_zoom_stays_active_after_completed_zoom` |
| `AC-D8.1`–`AC-D8.5` (ESC-003/008, RG-002) | 1 (amend) | §3 one pinned family `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`, floor `100`, no ceiling; old list = fixture |
| `AC-D8.6`, `AC-D8.7` (ESC-007) | 1 (amend) | §4 live ceiling O(1) via cached running max, only-widen; `auto_range=False` paths re-apply the cached ceiling |
| **`AC-D2.1`–`AC-D2.3` (Q33/A25)** | **R2** | **chip in the Y-axis lane, grey pill + white text, overlap permitted; dock-open visibility + independent CR verification** |
| `AC-D11.4` (ESC-006 re-scope) | 2 | label-vs-label inside the plot only; chip lane-separated |
| `AC-D10.1` (Q31/A22) | 3 (doc) | canonical affordance = checkable text label `Volume` |
| D7, D9, `AC-D8.1`–`AC-D8.3` | 1 | Unchanged from canonical Architecture (re-affirmed) |
| D12, D15 | 2 | Unchanged from canonical (re-affirmed) |
| D13, D14 (+ `AC-D14.4` ESC-010) | 4 (amend) | Canonical + symbol change also resets router mode to `IDLE` |
| Global AC | 5 | Offscreen suite green; no live-TWS traffic |

---

Status: READY_FOR_VALIDATION
