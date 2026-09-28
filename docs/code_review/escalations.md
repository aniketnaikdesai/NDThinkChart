# Code Review Escalations — NDThinkChart

**Source review:** `docs/code_review/review_log.md` (revision `09070e8`, 2026-09-27; second pass
`286028a` + uncommitted Build changes, 2026-09-28).
**Note:** original pass (ESC-001…ESC-012). Second pass closed out every entry whose fix the Code
Reviewer independently verified; ESC-011 stays `open` (residual drift — see `review_log.md`).
New findings from the second pass are appended as ESC-013 … ESC-019.

Routing legend: `ESCALATED_TO_BUILD`, `ESCALATED_TO_TASK_MANAGER`, `ESCALATED_TO_PLAN`,
`ESCALATED_TO_REQUIREMENTS`.

---

## ESC-001 — Duplicate `_init_schema` shadows the first definition

- **Linked task/defect:** n/a (DB layer, predates task graph)
- **Observed:** `data/db.py` defines `_init_schema` at `:14` and again at `:113`; the second binds.
  Diff of the two bodies (`15–108` vs `114–207`) is IDENTICAL. A stale, source-less
  `tests/__pycache__/test_db_schema.cpython-311-pytest-9.1.1.pyc` shows the regression test was
  drafted but never committed.
- **Expected:** a single definition and a committed regression test asserting a fresh `DB()` creates
  the full table set (bars, watchlist, alarms, zones, drawing_groups, drawings, studies, positions,
  trade_groups, position_group_map) and that only one `_init_schema` exists.
- **Root cause:** duplicated method block merged without deduplication; fix+test attempted but not
  committed.
- **Suggested direction:** delete the first definition (keep `:113`), recreate
  `tests/test_db_schema.py` as a real source file (not the orphaned `.pyc`).
- **Status: addressed**
  - Verified: `grep -n "def _init_schema" data/db.py` → exactly one hit (`:14`); `tests/test_db_schema.py`
    now exists as real source and was run green (`T26-T01`/`T26-T02`, 2 passed) asserting the ten-table
    set and a single definition. The `tests/__pycache__/test_db_schema*.pyc` present is a normal pytest
    cache regenerated from that source, no longer orphaned.

## ESC-002 — Implicit gesture precedence; magnifier vs active drawing undefined

- **Linked task/defect:** T6 (magnifier router precedence), T20
- **Observed:** `ui/chart_mouse_router.py:20–51` encodes precedence by call order only; no
  `RouterMode`/`_active_mode`/transition table. Activating the magnifier does not clear a drawing
  tool (`ui/chart_panel.py:538–548`), so zoom and drawing can both be active. Tests
  (`tests/test_chart_mouse_router.py:35–68`) cover only alarm-vs-drawing; the draw+zoom interaction
  is undefined.
- **Expected:** explicit `RouterMode` state machine (`IDLE/DRAWING/ZOOMING/ALARM_PLACING`), single
  `_active_mode`, guard clauses in every handler, a transition table, and named tests
  (`test_zoom_during_draw_cancels_draw`, `test_draw_blocked_during_zoom`,
  `test_alarm_placement_blocks_zoom`).
- **Root cause:** precedence was implemented implicitly and never promoted to an explicit state
  model; the draw/zoom interaction was left unspecified.
- **Suggested direction:** Plan defines the state machine + transition table (and resolves the
  draw+zoom case); Task Manager adds the named tests afterward.
- **Status: addressed**
  - Verified: `docs/architecture.md` §"Router state machine (ESC-002)" now carries the `RouterMode`
    enum + normative TR-1…TR-17 table; `ui/chart_mouse_router.py` implements `_active_mode` as the sole
    source of truth with guard-clause dispatch and reconciliation. T21's named tests (T21-T01…T21-T11)
    were re-run green (15 passed in `tests/test_chart_mouse_router.py`).

## ESC-003 — Volume nice-tick list is coarse above 10M

- **Linked task/defect:** T12 (D8)
- **Observed:** `_nice_volume_max` (`ui/chart_panel.py:45–55`) rounds above the 10M list entry to
  coarse 5M steps (`10.5M→15M`, `45M→50M`, `50M→60M`), and `10,000→50,000`. Existing test only
  reaches 2.2M (`tests/test_volume_linear.py:55–64`).
- **Expected:** a scaling nice-number formula; original list kept as a test fixture; a test at 40–50M.
- **Root cause:** fixed lookup list with a coarse fallback rather than a continuous nice-number scale.
- **Suggested direction:** replace with a 1/2/2.5/5×10^k generator; keep the old list as the
  fixture; assert monotonic, tight coverage at 40–50M.
- **Status: addressed**
  - Verified: `_nice_volume_max` (`ui/chart_panel.py:68`) now derives the smallest member of the pinned
    `1/1.5/2/2.5/5/7.5×10^k` family `>= max_vol*1.1` (floor 100, no ceiling); the old list lives only
    as `LEGACY_NICE_LIST` in the test. Re-ran `tests/test_volume_linear.py` green, including the
    40–50M cases (`10.5M→15M`, `45M→50M`, `50M→75M`).

## ESC-004 — No "visual reference confirmed" gate for UI-visual decisions

- **Linked task/defect:** n/a (process)
- **Observed:** D5→D8 rework happened because the screenshot arrived after build
  (`docs/architecture.md:25`, `docs/requirements/requirements.md:482–484`); `requirements.md:822`
  (risk R2) already notes stale plan checkmarks. No pre-implementation visual gate exists for
  D10/D12/D15.
- **Expected:** a "visual reference confirmed" gate required before implementation starts, rather
  than a Q-numbered retrofit after the fact. This is a process fix, not code.
- **Root cause:** visual references are treated as post-hoc clarifications rather than prerequisite
  artifacts.
- **Suggested direction:** Requirements Analyst adds the gate as a process requirement/checklist
  entry covering D10, D12, D15.
- **Status: addressed**
  - Verified: `docs/requirements/requirements.md` now defines **AC-G.1 (Visual reference gate — ESC-004)**
    (`:242–265`) requiring a user-confirmed `Visual reference:` artifact before any UI-visual fix, with
    per-defect status D10/D12/D15/D2 all `CONFIRMED` and provisional-assumption fallback (A21–A26).

## ESC-005 — Missing cross-cutting integration test for D10/D13 "expand to fill"

- **Linked task/defect:** T14 (D10), T17 (D13), T20
- **Observed:** one vertical `QSplitter` holds price/volume/osc (`ui/chart_panel.py:242–245`); the
  watchlist is a separate `QDockWidget` (`ui/main_window.py:212–224`), not a nested splitter. D10
  only calls `_splitter.refresh()` (`ui/chart_panel.py:342–356`). Existing toggle test asserts only
  `price_h_hidden >= price_h_before` (`tests/test_volume_toggle.py:18–37`). No test combines volume
  hide with a max-clamp watchlist drag.
- **Expected:** doc clarification of the splitter structure; one integration test hiding the volume
  panel AND dragging the watchlist to its max clamp in the same test asserting the price panel never
  drops below its minimum; consider a single `rebalance()` helper.
- **Root cause:** D10 and D13 were split into separate tasks with no cross-cutting integration test.
- **Suggested direction:** Task Manager adds the integration test and a task to reconcile the
  splitter/dock rebalance behaviour.
- **Status: addressed**
  - Verified: `tests/test_d10_d13_integration.py` (T28) exists and was re-run green (T28-T01/T28-T02):
    it hides the volume panel and drags the watchlist to its D13 max clamp in one offscreen `MainWindow`
    and asserts `price_plot`/central stay `>= CHART_MIN_WIDTH` (400). No `ui/chart_panel.py` rebalance
    helper proved necessary (existing `_on_volume_toggled → QSplitter.refresh()` suffices).

## ESC-006 — Crosshair price chip can overlap/stack with D11 drawing labels

- **Linked task/defect:** T3 (crosshair chip), T15 (D11 labels)
- **Observed:** chip uses `anchor=(1,0.5)` at `right()-2` (`ui/chart_panel.py:379`, `:413–417`);
  drawing labels use `anchor=(1,0.5)` at `right()-4` (`ui/drawing_overlay.py:335`, `:342`).
  `_update_inner_labels` (`ui/drawing_overlay.py:358–393`) iterates only `self._items`, so the chip is
  never deconflicted. `tests/test_drawing_labels.py:61–74` covers drawing-vs-drawing only.
- **Expected:** price labels and the crosshair chip do not overlap or stack illegibly at the same price.
- **Root cause:** D11 stacking was scoped to drawing-vs-drawing; the chip lane was reused
  geometrically but not included in collision accounting.
- **Suggested direction:** include the crosshair chip (or reserve its lane) in label placement, or
  offset labels when the chip is visible at the same price; add a crosshair-at-drawing-price test.
- **Status: addressed**
  - Verified: the chip moved out of the plot into the Y-axis lane (`ui/chart_panel.py:_create_crosshair`
    `anchor=(0,0.5)`; `_position_price_tag`) per Q33, so chip-vs-label collision no longer exists;
    `tests/test_crosshair_axis_lane.py` (T24) passes and the Code Reviewer's independent dock-open
    verification confirms the pill renders in the lane and is not covered by the open docks. The
    **label-vs-label** overlap that remains is a distinct new finding (ESC-014).

## ESC-007 — `nice_max` is stale on intra-bar updates and clips the tallest bar

- **Linked task/defect:** T12 (D8)
- **Observed:** volume Y range is set only under `if auto_range` (`ui/chart_panel.py:659–671`);
  `update_last_bar` calls `_refresh_candles()` with `auto_range=False` (`:584–600`), so bar heights
  update but the ceiling does not. As the forming bar's volume grows past `nice_max` it is clipped.
  `docs/architecture.md:110–111` claims per-data-load computation, which is true but leaves the
  staleness unaddressed.
- **Expected:** the ceiling tracks the live max (or is recomputed for the forming bar), or the
  staleness is explicitly documented and bounded.
- **Root cause:** volume auto-range is gated behind `auto_range=True`, which intra-bar updates never pass.
- **Suggested direction:** recompute `nice_max` on intra-bar ticks (one max over `_bars`) or track a
  running max and only widen; add a test growing the last bar past the initial ceiling and asserting
  no clipping.
- **Status: addressed**
  - Verified: `ui/chart_panel.py` now caches `_vol_max` and implements `_recompute_vol_max()` (O(N) on
    load/new bar), `_widen_volume_for()` / `_ensure_volume_range()` (O(1) only-widen intra-bar; no
    range write on a non-crossing tick), and re-applies the ceiling on `set_timezone()`. Re-ran
    `tests/test_volume_ceiling.py` green (T23-T01…T23-T04, incl. the no-range-write spy).

## ESC-008 — Nice-tick lower bound 10k flattens low-volume symbols

- **Linked task/defect:** T12 (D8)
- **Observed:** smallest nice step is `10_000` (`ui/chart_panel.py:47`); measured
  `_nice_volume_max(800)==10_000`, `_nice_volume_max(3_000)==10_000`
  (`tests/test_volume_linear.py:60–62` encodes the 8k floor). An 800–3,000 share symbol uses <30% of
  the pane.
- **Expected:** a finer low end (e.g. 100/250/500/1k/2.5k/5k) so low-volume symbols fill the pane.
- **Root cause:** fixed list starts at 10k; no sub-10k nice values.
- **Suggested direction:** use the scaling formula from ESC-003 with a finer low end; add a
  low-volume-symbol test asserting a tight axis.
- **Status: addressed**
  - Verified: the pinned family floors at `100` with no `10k` floor; re-ran `tests/test_volume_linear.py`
    green — `_nice_volume_max(0) == 100`, `(800) == 1_000`, `(3_000) == 5_000`, monotonic/tight sweep
    (T22-T04/T22-T05).

## ESC-009 — High-DPI claims are not exercised

- **Linked task/defect:** T9 (D6 wick), T15 (D11 labels), T20
- **Observed:** `docs/architecture.md:112` claims D6/D11 are "device-pixel aware", but a repo search
  finds no `devicePixelRatio` / `QT_SCALE_FACTOR` / `dpr` anywhere in `tests/`, `ui/`, or `docs/`.
  The `qapp` fixture (`tests/conftest.py:91–98`) runs at DPR 1.0.
- **Expected:** at least one parametrized run at `QT_SCALE_FACTOR=2`.
- **Root cause:** test harness uses a single scale factor; DPI claims rest on unrun assertions.
- **Suggested direction:** Task Manager adds a DPR=2 parametrized/session run asserting wick/body
  separation and label-in-bounds for D6 and D11.
- **Status: addressed**
  - Verified: `tests/test_chart_dpi.py` (T29) runs the real `ChartPanel` in an isolated subprocess at
    `QT_SCALE_FACTOR=1` and `=2` and asserts `dpr`, wick 1-device-px, and label-in-bounds; T29-T02
    (labels) and T29-T03 (isolation) pass. The coverage is real and **exposed a genuine pre-existing
    bug** in D6 (picture-generation ordering) — tracked as the new ESC-015, not a defect in the
    coverage itself.

## ESC-010 — D14 double-click symbol change mid-drag is untested

- **Linked task/defect:** T18 (D14), T20
- **Observed:** `_on_watchlist_row_double_clicked` → `load_chart()` → `set_data`
  (`ui/main_window.py:688–704`, `:452`/`:525`); `set_data` clears drag/draft and detaches items
  (`ui/drawing_overlay.py:112–118`, `:216–235`). The defensive `dragItem` clearing may cover it, but
  no test exercises the mid-drag path; the earlier `InfiniteLine` use-after-free is documented at
  `docs/debug/debug_log.md:19–43`.
- **Expected:** a test that double-clicks a different symbol mid-drag and asserts no `RuntimeError`.
- **Root cause:** a new symbol-change entry point re-enters overlay teardown without dedicated
  regression coverage.
- **Suggested direction:** add the mid-drag double-click regression test rather than assuming the
  existing defensive clearing covers it; only convert to a BUILD bug if it actually fails.
- **Status: addressed**
  - Verified: `tests/test_watchlist_d14_midrag.py` (T30) drives the real D14 double-click entry point
    mid-drag (no TWS) and asserts no `RuntimeError`/`RuntimeWarning`, the new chart renders, and the
    router returns to `IDLE`; re-run green (T30-T01…T30-T03). `ChartPanel.set_symbol()` now clears the
    drawing tool and calls `router.exit_to_idle()` (TR-17).

## ESC-011 — Documentation drift (test count/timing, PENDING phases, orphaned bytecode)

- **Linked task/defect:** n/a
- **Observed:** `usage.md:166` says "269 tests, ~1.5s"; measured `09070e8` gives **339 passed in
  2.88s** and `docs/build/build_log.md:161` already records 339. `PENDING_IMPLEMENTATION_PLAN.md:364`,
  `:412`, `:458` repeat "269 passed". Only Phase 10 is marked COMPLETE (`:462`); Phases 1–5 carry no
  completion marker though `ui/drawing_overlay.py`, `ibkr/market_depth.py`, `ibkr/orders.py`,
  `ui/active_trader_panel.py`, `ui/stop_loss_target_dialog.py` exist. A source-less
  `tests/__pycache__/test_db_schema.cpython-311-*.pyc` remains.
- **Expected:** accurate counts/timing and phase status; no orphaned build artifacts.
- **Root cause:** docs were not updated after later batches landed.
- **Suggested direction:** Requirements Analyst updates `usage.md` / `PENDING_IMPLEMENTATION_PLAN.md`;
  the orphaned `.pyc` should be removed (covered by ESC-001).
- **Status: ESCALATED_TO_REQUIREMENTS**

## ESC-012 — `requirements.md` still presents D5 (log) although D8 (linear) supersedes it

- **Linked task/defect:** n/a
- **Observed:** `docs/requirements/requirements.md:378–406` presents D5 as clarified and requires
  **log** Y (`AC-D5.1` at `:396–397`), with no superseded marker; D8 says it revises D5 to **linear**
  (`:482–484`, `AC-D8.1` at `:512–514`); the header at `:13` still lists "volume log lower bound 1.0
  — Q17". `architecture.md:25` and `plan.md:12` already mark D5 superseded. A literal D5 implementer
  would ship the wrong axis. (Graph-integrity numbers from the report — 228 dangling / ~130
  collapsed — were not reproducible from the committed `graphify-out/graph.json`; only 45 self-loops
  matched. Raw extraction `.graphify_extract.json` is absent.)
- **Expected:** D5 clearly marked superseded by D8 in `requirements.md`, including the header index.
- **Root cause:** D8 was appended as a revision without annotating the D5 section it overrode.
- **Suggested direction:** Requirements Analyst marks D5 "superseded by D8" and fixes the header
  index. Graph health is tooling/user housekeeping — re-run the graphify health gate on a fresh
  extraction if the dangling/collapsed counts matter.
- **Status: addressed**
  - Verified: `requirements.md` now marks D5 superseded (Journey 6 `:155`, `AC-D5.1 (superseded by
    AC-D8.1)` `:542`, superseded edge-cases `:549`, DOC-4 `:1136`) and the header index (`:13`) reads
    "volume log lower bound 1.0 — Q17 — SUPERSEDED by D8 (linear, Q20); see D5".

---

## Second-pass findings (2026-09-28) — ESC revision `286028a` + uncommitted Build changes

Source: `docs/code_review/review_log.md` §"Revision 2 review". Verified against the live tree, not
against Build's report: each of the two blocked tasks was reproduced by running its own failing test.

## ESC-013 — D6 body clamp never fires: the candle picture is generated before the view range is set

- **Linked task/defect:** T29 (AC-D6.4, ESC-009 follow-on) — **blocked**
- **Observed:** `T29-T01[dpr1]`/`[dpr2]` fail: `AC-D6.4: the dense-view candle body renders
  0.56 / 1.06 device px wide (expected >= 4)`. Reproduced here:
  `pytest tests/test_chart_dpi.py -q` → the two `[dpr1]`/`[dpr2]` cases fail with
  `body_device_px ≈ 0.53 (dpr1) / 1.06 (dpr2)`.
- **Expected:** at DPR 1 and 2 the dense-view body is `>= 4` device px and strictly wider than the
  1-device-px wick (AC-D6.4).
- **Root cause:** `ui/chart_panel.py::_refresh_candles()` calls `self.candlestick.set_data(...)`
  (`:831`), which runs `ui/candlestick_item.py::_draw_candles()`'s `>=4-device-px` clamp against the
  **current** `ViewBox.viewRange()` (`:118–125`), **before** `vb.setRange(...)` (`:844–845`) applies
  the real x-range. At generation time the range is the untouched default (`[[-0.5, 0.5]]`,
  `px_per_sec ≈ 863`) so `min_w` never binds and the stored `w = median_diff*0.325` (19.5) survives;
  the later real range (`x_span ≈ 61,628` for 960×60s bars) maps that to ~0.55 logical px.
  Regenerating the picture **after** `setRange` yields 4.00/8.01 device px — the clamp math is
  DPR-safe; only the generation ordering is broken. This is a pre-existing ordering bug the new
  DPR test exposed.
- **Suggested direction:** set the price `xRange` **before** `candlestick.set_data(...)` (or
  regenerate the picture after `setRange`, e.g. a second `set_data`/`update`), and/or compute the
  clamp from the target range. Fix sites are `ui/chart_panel.py` (ordering) and/or
  `ui/candlestick_item.py`; both are outside T29's `touches_files`.
- **Status: ESCALATED_TO_BUILD**

## ESC-014 — D11 label stacking only guarantees 15 px but real label bboxes are ~23 px tall

- **Linked task/defect:** T25 (AC-D11.4, ESC-006 re-scope) — **blocked**
- **Observed:** `T25-T01` (`tests/test_drawing_labels.py::test_label_vs_label_bbox_no_intersection`)
  fails: `D11 label bounding boxes overlap: centre separation 15.0px < label bbox height 23.0px`.
  Reproduced here (`1 failed, 4 passed`). Measured labels `102.05` bbox=(811.94, 257.38, 48.06, 23.00)
  and `102.00` bbox=(811.80, 272.38, 48.20, 23.00); `intersects() == True` (8 px overlap).
- **Expected:** AC-D11.4 requires that consecutive label text bounding boxes **MUST NOT overlap**;
  its measurable clause is `abs(centerΔ) >= bbox_height` (bounding rects do not intersect).
- **Root cause:** `ui/drawing_overlay.py::_update_inner_labels()` (`:386–391`) pushes a label down
  only when `y - last_y < 15`, using a fixed 15 px centre offset. A real `TextItem` scene bbox is
  ~23 px tall (9 pt font + document margins), so the minimum-offset pair still overlaps by ~8 px.
  The AC's `>= 15 px` parenthetical is the *existing* threshold, but the AC's normative/measurable
  clause is non-overlap (`>= bbox_height`) — the code satisfies the weaker number and violates the
  stronger clause.
- **Suggested direction:** stack with `offset = max(15, measured_bbox_height)` (or use the emitted
  `TextItem.sceneBoundingRect().height()`) rather than a hard-coded 15 px; the clamp to
  `view_rect.bottom()` stays. Fix site `ui/drawing_overlay.py`, outside T25's `touches_files`.
  While in `tests/test_drawing_labels.py` (inside T25's footprint) also remove the vacuous
  assertion at `:67` `assert label.isVisible() or True` (always true — asserts nothing).
- **Status: ESCALATED_TO_BUILD**

## ESC-015 — `tests/test_volume_log.py` still expects the removed 10k floor

- **Linked task/defect:** T22 (D8) collateral — blocks T31
- **Observed:** `tests/test_volume_log.py::test_volume_zero_mapped_to_one:34` fails:
  `assert y_range[1] == pytest.approx(10_000, rel=0.1)` → `assert 1500.0 == 10000 ± 1.0e+03`.
  Reproduced here. Comment at `:33` still says "nice_max for max 1000 -> 10k".
- **Expected:** the pinned family gives `_nice_volume_max(1000) == 1500` under `>= 1000*1.1`.
- **Root cause:** a stale test expectation encoding the removed 10k floor; not a product regression
  (T22's mandated behaviour change). `tests/test_volume_log.py` is in no task's `touches_files`.
- **Suggested direction:** one-line update `10_000 → 1_500` (preferably assert against
  `_nice_volume_max(max_vol)` so it cannot drift). Test-only change; owner inherits T22.
- **Status: ESCALATED_TO_BUILD**

## ESC-016 — Four stale crosshair assertions still expect the superseded inside-plot chip

- **Linked task/defect:** T24 (D2/Q33) collateral — blocks T31
- **Observed:** reproduced `4 failed`:
  `tests/test_chart_crosshair.py::test_hover_inside_shows_lines_and_axis_chips`
  (`:50` `pos().x() <= view_right - 1`; `:53` anchor `(1,0.5)`),
  `tests/test_crosshair_chip_bounds.py::test_chip_visible_inside_right_edge` (`:31`, `:34`),
  `::test_chip_stays_inside_after_zoom` (`:47`, `:49`), `::test_long_price_and_edge_positions` (`:70`).
- **Expected:** the chip now lives in the Y-axis lane (`anchor=(0,0.5)`, scene `x >= view_rect.right()`),
  so the old inside-plot bounds are superseded by Q33.
- **Root cause:** Batch-1 tests assert the pre-Q33 inside-plot position; T24's mandated relocation
  changed the behaviour. Neither file is in T24's `touches_files`.
- **Suggested direction:** update both files to the axis-lane contract (scene `x >= view_rect.right()`,
  `anchor=(0,0.5)`, grey pill/white text, not clipped). Do not weaken to a tautology — assert the new
  geometry. Test-only change.
- **Status: ESCALATED_TO_BUILD**

## ESC-017 — TR-4 side effect "uncheck the draw combo" is not implemented (combo goes stale)

- **Linked task/defect:** T21 (TR-4 / AC-D3.7 forward; also TR-17)
- **Observed:** after a drawing tool is active and the magnifier is invoked, the router clears the
  drawing overlay tool (`ChartMouseRouter.enter_zoom()` → `_clear_drawing_tool()`), but
  `MainWindow.draw_combo` still displays the previously selected tool (`ui/main_window.py:155–158`).
  Likewise `ChartPanel.set_symbol()` clears the tool on TR-17 without resetting the combo.
  `MainWindow` only resets the combo for the *alarm* path (`:672`). Because the combo text is
  unchanged, re-selecting the same tool later emits no `currentTextChanged` and cannot re-arm it.
- **Expected:** `docs/architecture.md` TR-4 side effects list "clear the drawing tool; **uncheck the
  draw combo**"; T21 explicitly named `ui/main_window.py` in `touches_files`, so this was in scope.
- **Root cause:** TR-4 was implemented at the router/overlay level only; no signal flows back to the
  toolbar combo when the router clears the tool (zoom-during-draw or symbol change).
- **Suggested direction:** on `enter_zoom()` from `DRAWING` (and on the TR-17 symbol reset), reset
  `MainWindow.draw_combo` to `"Cursor"` (guard against recurrence with `blockSignals` if needed), or
  emit a router/adapter signal the window can observe. UI-consistency fix.
- **Status: ESCALATED_TO_BUILD**

## ESC-018 — T22 "each is a fixed point" acceptance/test predicate is unachievable as worded

- **Linked task/defect:** T22 (D8) — task definition, not code
- **Observed:** `docs/tasks/task-graph.json` AC `"Fixture fixed points"` (`:1256`) and test
  descriptions T22-T02 (`:1270`) / T22-T06 (`:1298`) require asserting `_nice_volume_max(v) == v`
  ("each is a fixed point"). Under the pinned `>= v*1.1` formula **no positive value is a fixed
  point** — every positive value advances to a strictly larger family member (`10_000 → 15_000`, as
  the AC's own examples show). The AC's parenthetical examples (`8_000 -> 10_000`, …) are
  input→output mappings, contradicting the "fixed point" phrasing.
- **Expected:** the predicate should assert the intended **input→output mapping / family
  membership**, which is what the worker encoded (tests pass).
- **Root cause:** wording defect confined to the Task-Manager-owned acceptance criterion and test
  descriptions. The phrase does **not** appear in `requirements.md` or `architecture.md` (checked by
  grep), whose D8/§3.3 wording is consistent, so this is not a requirements/architecture gap.
- **Suggested direction:** reword the `"Fixture fixed points"` AC and T22-T02/T22-T06 to the
  input→output mapping (or "every retained expectation is reproduced / a family member"), and drop
  the term "fixed point". Wording-only; no code change.
- **Status: ESCALATED_TO_TASK_MANAGER**

## ESC-019 — Stale `👁 Volume` prose in the Plan-owned artifacts

- **Linked task/defect:** T27 (RC-4a)
- **Observed:** RC-4a changed the D10 affordance to the checkable text label `Volume` in code, but
  `docs/plan.md` (`:113`, "the built control remains `QPushButton(\"👁 Volume\")`"),
  `docs/plan_review.md`, and `docs/architecture_proposal.md` still describe the eye-glyph label.
- **Expected:** prose matches the shipped `Volume` text label (`ui/chart_panel.py:327`).
- **Root cause:** documentation drift in Plan-owned files after the RC-4a correction; not a code
  defect (T27's own tests pass).
- **Suggested direction:** update the stale `👁 Volume` wording in `docs/plan.md`,
  `docs/plan_review.md`, and `docs/architecture_proposal.md` to the text label `Volume`.
  Wording-only; Build must not edit these files.
- **Status: ESCALATED_TO_PLAN**

---

## Verified with no escalation

- **E4 — D12 zone "Extend" removal / payload migration:** verified clean. No persisted extend flag
  (`data/db.py:59–67`), zone payload is `{"x1","x2","y1","y2"}` only
  (`services/drawing_service.py:61–71`), rendering consumes `y1/y2` (`ui/drawing_overlay.py:275–284`),
  dialog omits the control (`ui/zone_settings_dialog.py:4–5`, `:54`). Prior zones render unchanged;
  no migration required.
