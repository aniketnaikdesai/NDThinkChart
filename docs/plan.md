# Implementation Plan — NDThinkChart Stabilization (Batch 3–9: D7–D15 + ESC-002/003/006/007 revision)

Scope: the Batch 3–9 refinements in `docs/requirements/requirements.md` (D7–D15)
**plus** the validated revision (2026-09-27) — the ESC-002 gesture state machine
(`AC-D3.7`–`AC-D3.9`), the ESC-003/ESC-007/ESC-008 volume nice-number formula and live
ceiling (`AC-D8.1`–`AC-D8.7`), the re-opened D2/Q33 crosshair-chip relocation
(`AC-D2.1`–`AC-D2.3`), and the ESC-006 `AC-D11.4` re-scope. This is a stabilization
run; no new features, no schema changes, no new integrations. Items are labelled
`[existing]`, `[new]`, or `[new/changed]`.

## Completed — Batch 1 and Batch 2
Batch 1 (D1–D3: session shading, crosshair chip, zoom controls/magnifier) and
Batch 2 (D4–D6: zoom label/position, volume log, pixel-stable wick) were approved,
built, and verified, plus the 2026-09-19 `DrawingOverlay` drag-lifecycle runtime
stability fix (see `docs/build/build_log.md` and `docs/debug/debug_log.md`). Note:
**D8 supersedes D5’s log decision** — the volume axis returns to linear. The
Batch-1 crosshair chip was an inside-plot right-align; **D2/Q33 now supersedes it**
(chip moves to the Y-axis lane).

## Phases

### Phase R1 (NEW) — Router state machine (ESC-002, `AC-D3.9`, RC-3, RC-4b)
- **Goal:** Replace the implicit tri-boolean precedence in
  `ui/chart_mouse_router.py` (`ZoomOverlay.is_active()` / `DrawingOverlay.tool_active()` /
  `AlarmOverlay.is_alarm_mode()`, resolved only by call order) with an explicit
  `RouterMode { IDLE, DRAWING, ZOOMING, ALARM_PLACING }`, a single `_active_mode`, a
  guard clause at the top of every handler, and the **total normative transition table**
  (`docs/architecture.md` → “Router state machine”), including TR-4 (`AC-D3.7`
  forward), TR-5 (`AC-D3.7` reverse), TR-6 (`AC-D3.8`), and **TR-9** (`AC-D3.9` —
  magnifier refused during alarm placement: mode unchanged, placement intact, status
  hint). Implement the **RC-3** reconciliation (properties whose setters call
  `_reconcile_mode_from_overlays()`, precedence `DRAWING > ZOOMING > ALARM_PLACING >
  IDLE`, defensive probes) so the five preserved router tests pass verbatim; document
  the **RC-4b** `view_mouse_click`-in-`DRAWING` behaviour. The router is the single
  writer of `_active_mode`; `ChartPanel.set_zoom_mode`/`set_drawing_tool`/`set_alarm_mode`
  become thin adapters (signatures unchanged), plus a `zoom_refused` signal connected in
  `MainWindow` to `status_bar.showMessage(...)` for `AC-D3.9`.
- **Named tests:** new `test_zoom_during_draw_cancels_draw`,
  `test_draw_blocked_during_zoom` (asserts the confirmed reverse rule),
  `test_alarm_placement_blocks_zoom`, `test_magnifier_refused_during_alarm_placement`,
  `test_click_in_drawing_reaches_only_drawing`; mode-model
  `test_router_mode_is_mutually_exclusive`, `test_zoom_stays_active_after_completed_zoom`,
  `test_esc_cancels_selection_not_mode`, `test_reconcile_mode_from_wired_overlays`;
  preserved verbatim `test_alarm_press_wins_in_cursor_mode`,
  `test_drawing_tool_blocks_alarm_press`, `test_alarm_miss_falls_through_to_drawing`,
  `test_click_prefers_alarm_then_drawing`, `test_missing_overlays_are_safe`.
- **Requirements / journeys covered:** `AC-D3.7` (both directions), `AC-D3.8`,
  `AC-D3.9`, `AC-D3.3`, `AC-D3.4`; Journey 4 edge cases; ESC-002.
- **Files `[new/changed]`:** `ui/chart_mouse_router.py`, `ui/chart_panel.py`
  (adapters + `zoom_refused`), `ui/main_window.py` (one status-bar connection),
  `tests/test_chart_mouse_router.py`.
- **Dependencies on earlier phases:** None. **Must be its own wave** — it modifies
  `ui/chart_panel.py` (also touched by R2/Phase 1/Phase 3) and `ui/main_window.py`
  (also touched by Phase 4).

### Phase R2 (NEW) — D2/Q33 crosshair chip relocation (RC-2)
- **Goal:** Move `_price_tag` from the Batch-1 **inside-plot** right-aligned position
  (`view_rect.right() - 2`) to the **Y-axis lane outside the plot**, right of the
  plot’s vertical axis line; render it as a **grey pill with white text**
  (`anchor=(0,0.5)`), and **permit** axis-tick-label overlap (no deconfliction offset).
  Retain the show-only-inside-plot / hide-on-leave behaviour (`AC-D2.3`) and pan/zoom
  tracking (`AC-D2.2`). Because this **re-opens the original D2 defect surface**,
  dock-open visibility (`AC-D2.1` + edge case) must be **independently verified by the
  Code Reviewer after Build** (A25) — the Batch-1 fix must not be assumed to still hold.
- **D11 re-scope:** `AC-D11.4` applies to **label-vs-label stacking inside the plot
  only**; the chip is lane-separated and out of scope for that criterion (ESC-006).
- **Named test:** `test_crosshair_chip_renders_in_axis_lane` (chip scene
  `x >= view_rect.right()`, left anchor, grey fill, white text). The dock-open check is
  the Code Reviewer’s independent verification.
- **Requirements covered:** D2 (`AC-D2.1`–`AC-D2.3`), Q33/A25; `AC-D11.4`.
- **Files `[new/changed]`:** `ui/chart_panel.py`; new/updated crosshair test `[new]`.
- **Dependencies on earlier phases:** None, but shares `ui/chart_panel.py` with
  R1/Phase 1/Phase 3 (serial chain).

### Phase 1 (AMENDED) — Chart geometry: gap, volume width, volume axis (D7, D9, D8)
Canonical Phase 1 stands, with two amendments:
- **Amendment A — nice-number formula (`AC-D8.1`–`AC-D8.5`; RC-1 / ESC-003/ESC-008,
  RG-002 resolved).** Replace the fixed list with **one** pure, importable generator
  over **one** candidate family **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`**, floor `100`,
  no fixed ceiling: `nice_max = smallest family value >= max_vol * 1.1`;
  `max_vol == 0 → 100`. The original list becomes a **test fixture only**. Of
  `tests/test_volume_linear.py:57–61`, **only** `_nice_volume_max(0) == 10_000` changes
  (→ `100`); the `8_000`, `80_000`, `2_200_000`, `1_050_000` assertions stay valid.
- **Amendment B — live ceiling (`AC-D8.6`/`AC-D8.7`; ESC-007).** The volume ceiling also
  updates on RT volume changes in **O(1) against a cached running max** (only-widen),
  and `auto_range=False` refresh paths (`set_timezone()`) re-apply the cached ceiling.
  Named tests: `test_volume_ceiling_tracks_live_bar`,
  `test_volume_ceiling_refit_on_timezone_refresh`.
- **Requirements / journeys covered:** D7 (`AC-D7.1`–`7.2`), D9 (`AC-D9.1`–`9.2`),
  D8 (`AC-D8.1`–`AC-D8.7`); A11, A24, R9, R10, R20; DG8, DG9; Journey 8/9/10.
- **Files:** `ui/candlestick_item.py` `[new/changed]`, `ui/chart_panel.py`
  `[new/changed]`, `tests/test_volume_linear.py` + new volume-ceiling tests
  `[new/changed]`.
- **Dependencies on earlier phases:** None technically; shares `ui/chart_panel.py`
  with R1/R2/Phase 3 (serial chain).

### Phase 2 (AMENDED) — Drawing visuals: inner-right labels + double-click dialogs (D11, D12, D15)
Canonical Phase 2 stands. `AC-D11.4` is scoped to **label-vs-label stacking** only —
the crosshair chip now lives in the Y-axis lane (D2/Q33), so chip-vs-label
deconfliction is retired (ESC-006). Files: `ui/drawing_overlay.py` `[new/changed]` and
the two dialogs `[new]`.
- **Requirements / journeys covered:** D11 (`AC-D11.1`–`AC-D11.5`), D12
  (`AC-D12.1`–`AC-D12.3`), D15 (`AC-D15.1`–`AC-D15.3`); A15, A16, A20; R13, R14, R18,
  R21; Journeys 12/13/16.
- **Dependencies on earlier phases:** None technically; shares `ui/drawing_overlay.py`
  with the Phase-4 mode-reset amendment (serial).

### Phase 3 (AMENDED) — Volume panel visibility toggle (D10)
Canonical Phase 3 stands with **one documentation correction** (RC-4a): the D10
affordance is the checkable **text label `Volume`** (Q31/A22/`AC-D10.1`) at the top
left of the volume panel (bottom left of the price chart, A23), **not** an eye icon.
This corrects the canonical architecture row only; the built control remains
`QPushButton("👁 Volume")` (`ui/chart_panel.py:250`) and its user-facing affordance is
the `Volume` text label.
- **Requirements / journeys covered:** D10 (`AC-D10.1`–`AC-D10.2`); A14, A22, A23; R12;
  Journey 11.
- **Files:** `ui/chart_panel.py` `[new/changed]` (volume plot + splitter).
- **Dependencies on earlier phases:** Phase 1 (shares `ui/chart_panel.py`), so build
  serially after it.

### Phase 4 (AMENDED) — Watchlist resize + double-click load (D13, D14)
Canonical Phase 4 stands, with one amendment:
- **Amendment — symbol change resets router mode.** A symbol change (including the D14
  mid-drag double-click path, `AC-D14.4`) while a drawing drag/draft is in progress must
  return the router to `IDLE` (TR-17) in addition to clearing the overlay’s draft/drag
  state (`DrawingOverlay.set_data()` already clears it defensively at `:112–118`).
  Verified by the ESC-010 regression test (`AC-D14.4`) plus a mode assertion.
- **Soft dependency:** the mode-reset clause is only verifiable once Phase R1 lands;
  the watchlist/QSettings work itself is independent.
- **Requirements / journeys covered:** D13 (`AC-D13.1`–`AC-D13.3`), D14
  (`AC-D14.1`–`AC-D14.4`); A17–A19; R15–R17; Journeys 14/15.
- **Files:** `ui/watchlist_panel.py` `[new/changed]`, `ui/main_window.py`
  `[new/changed]`, the `QSettings` read/write site, `tests/` (watchlist + `AC-D14.4`
  regression) `[new/changed]`.
- **Dependencies on earlier phases:** None, but its `ui/main_window.py` change
  serializes with Phase R1.

### Phase 5 (AMENDED) — Verification and regression (all batches)
Canonical Phase 5 stands, with added coverage:
- Router mode transitions — the Phase R1 named tests (new + `AC-D3.9` + preserved +
  mode-model + reconciliation).
- Nice-number generator — family/formula, monotonic, tight coverage (`<= 2`), floor
  `100`, the `40M–50M` cases, and the legacy-list fixture cross-checks.
- Live ceiling — `test_volume_ceiling_tracks_live_bar`,
  `test_volume_ceiling_refit_on_timezone_refresh`.
- D2 chip — `test_crosshair_chip_renders_in_axis_lane`, plus the **Code Reviewer’s
  independent dock-open verification** for `AC-D2.1`.
- `touches_files`-aware sequencing honoured (no two built tasks in a wave share a file).
- Global criteria unchanged: the pre-existing suite stays green offscreen
  (`QT_QPA_PLATFORM=offscreen`, measured 339 passed at `09070e8`), no live-TWS connection
  or order transmission (Q8/Q9).
- **Dependencies on earlier phases:** Phases R1, R2, 1, 2, 3, and 4.

## Parallel sequencing (`touches_files` contract)
The Task Manager must add a **`touches_files`** field to every task so Build’s Lead (a
Lead + Worker pair) can dispatch non-conflicting tasks in parallel up to
`max_parallel_tasks` (default 4; optional user-owned `docs/build/build_config.json`).
The Lead is the sole writer of task status, so concurrent workers never race on the
graph. Sequencing consequence for this revision:

| File | Phases that touch it | Consequence |
|---|---|---|
| `ui/chart_panel.py` | R1 (router adapters + `zoom_refused`), R2 (crosshair chip), 1 (volume axis/ceiling/width), 3 (volume toggle + splitter) | **Serial chain** — must not share a wave |
| `ui/main_window.py` | R1 (status-bar connection), 4 (watchlist wiring) | **Serial** — R1 and Phase 4 must not share a wave |
| `ui/chart_mouse_router.py` | R1 only | R1’s core file |
| `ui/drawing_overlay.py` | 2, plus the Phase-4 mode-reset amendment | Serial |
| `ui/zoom_overlay.py` | R1 (read-mostly; any change must be flagged) | Serial with R1 |
| `ui/candlestick_item.py` | 1 (D7 gap) | May run parallel with `chart_panel`/`main_window` tasks |
| `ui/watchlist_panel.py`, `QSettings` site | 4 | May run concurrently with R2/Phase 1/3 (its `main_window.py` part serializes with R1) |
| New dialog files (`ui/zone_settings_dialog.py`, `ui/horizontal_line_settings_dialog.py`) | 2 | New files → may run concurrently with R1/R2/Phase 1/3 |
| `tests/test_chart_mouse_router.py` | R1 | Serial per file |
| `tests/test_volume_linear.py` + new volume tests | 1 | Serial per file |
| New crosshair test | R2 | Serial per file |
| `tests/` watchlist + D14 regression | 4 | Serial per file |

Practical rule: **Phase R1 must be scheduled alone or only with tasks that touch
neither `ui/chart_panel.py` nor `ui/main_window.py`**; **Phase R2** is serial with
R1/Phase 1/Phase 3 on `ui/chart_panel.py`. This is an architecture-level constraint on
the task graph, not a task decomposition: the Task Manager populates `touches_files`
accurately and the Lead enforces the wave rule.

## Assumptions
Inherited and confirmed from `docs/requirements/requirements.md`: A8, A10–A26 (including
the canonical `PA1-batch3`…`PA8-batch3`), all unchanged.

Plan-level assumptions for this revision (implementation details only; **no requirements
gap**):
- **PA-R2** — `RouterMode.DRAWING` is synonymous with `DrawingOverlay.tool_active()`;
  an unarmed drawing tool is `IDLE`.
- **PA-R3** — `test_draw_blocked_during_zoom` keeps its escalation-assigned **name**
  while asserting the **confirmed reverse** rule (draw exits zoom).
- **PA-R4** — only-widen on intra-bar ceiling updates satisfies `AC-D8.6`’s
  “recomputed/**widened** … or the bound is explicitly documented” clause.
- **PA-R5** — the original fixed nice list is retained **as a test fixture only**; of
  the existing `tests/test_volume_linear.py` assertions, **only**
  `_nice_volume_max(0) == 10_000` changes (→ `100`) — requirement-backed (Journey 1
  edge case), not a silent test edit.
- **PA-R6** — D2 chip implementation geometry: left-anchored at the axis line
  (`anchor=(0,0.5)`, scene `x = view_rect_scene.right()` + small pad), extending right
  into the Y-axis lane, with the existing in-view clamp and a right-edge guard so a long
  price is not clipped. The lane/style/overlap are requirements; the pad is detail.
- **PA-R7** — `AC-D3.9`’s status-bar hint is surfaced by a new
  `ChartPanel.zoom_refused` signal connected in `MainWindow`; the exact hint string is a
  plan-level choice (“Finish or cancel alarm placement before zooming”).
- **PA-R8** — the `<= 2` tightness bound in `AC-D8.4` is asserted only where the ceiling
  is above the required `100` floor (`max_vol >= 100/2.2 ≈ 45.5`); below that the ceiling
  is the floor and the ratio may exceed `2`. Build must not write a test that contradicts
  the required floor.
- ~~**PA-R1** (`ALARM_PLACING → ZOOMING`)~~ — **RETIRED:** superseded by `AC-D3.9`
  (Q36 option (b)); the router refuses and stays in `ALARM_PLACING`.

The two requirements escalations raised during validation pass 1 are **resolved in
`requirements.md` (2026-09-27)**: **RG-002** (nice-number family pinned to
`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`, no `10K` floor, value `100`) and **RG-003**
(Q36 option (b) → `AC-D3.9`). No requirements gaps remain.

---

Status: READY_FOR_TASK_MANAGER
