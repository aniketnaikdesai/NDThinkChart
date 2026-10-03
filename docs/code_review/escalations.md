# Code Review Escalations — NDThinkChart

**Source review:** `docs/code_review/review_log.md` (revision `09070e8`, 2026-09-27; second pass
`286028a` + uncommitted Build changes, 2026-09-28).
**Note:** original pass (ESC-001…ESC-012). Second pass closed out every entry whose fix the Code
Reviewer independently verified; ESC-011 stays `open` (residual drift — see `review_log.md`).
New findings from the second pass are appended as ESC-013 … ESC-019.
Third pass (2026-09-28, rework round; `952a083` + uncommitted Build changes) independently re-verified
and closed **ESC-013, ESC-014, ESC-015, ESC-016, ESC-017, ESC-018, ESC-019**; ESC-011 remains open
(owner dependency). One new finding appended: **ESC-020** (D9 volume-width ordering).
Fourth pass (2026-09-28, focused ESC-021 rework; `952a083` + uncommitted Build changes) independently
re-verified and closed **ESC-020** (product ordering) and then **ESC-021** (test robustness) on the
wave-13 rework. ESC-011 remains open (owner dependency). No new finding this pass.
Sixth pass (2026-09-28, root-doc verification, no Build output change) independently re-verified and
closed **ESC-011** — the owner's residual fixes to `usage.md` / `PENDING_IMPLEMENTATION_PLAN.md` check out
(no `269` left, suite re-measured at 383, all ten phases `✅ COMPLETE`). One same-class finding was surfaced
outside ESC-011's enumerated scope and appended as **ESC-022** (`test_plan.md:76`).
Seventh pass (2026-09-28, ESC-022 verification, no Build output change) independently re-verified and closed
**ESC-022** — `test_plan.md:76` now reads the current full-suite figure (`383 passed in ~6.5s`; independently
re-measured at **383 passed in 6.13s**, exit 0), and no `269` remains in any root doc.
Eighth pass (2026-10-02, D16 batch) opened **ESC-023** (calendar year-end, REQUIREMENTS) and **ESC-024**
(dropped-connection mid-wave, BUILD).
Ninth pass (2026-10-02, ESC-023 correction round; `9c2fafa` + uncommitted D16 changes) independently
re-verified and closed **ESC-023** (T37 rework + T42 gate); **ESC-024** was re-routed from BUILD to
**TASK_MANAGER** (no task carries it and it is incompatible with the T42 unchanged-consumer constraint).
Tenth pass (2026-10-02, ESC-024 rework round; T43 done) independently re-verified and closed **ESC-024**
(reproduced the disconnect drain and the watchdog path, confirmed the shortfall is surfaced, no bar is
fabricated, the generation advance rejects late events, and a no-op disconnect does not double-finalise
or raise; full suite re-run **489 passed**). One new non-blocking quality finding appended: **ESC-025**
(`closeEvent` leaves the watchdog armed; the stranded-wave `reason` parameter is unused).
**ESC-024 is `addressed`; the only open entry is ESC-025 (`ESCALATED_TO_BUILD`, nice-to-have).**
Eleventh pass (2026-10-02, ESC-025 rework round; T44 done) independently re-verified and closed **ESC-025**
on the live tree (offscreen probes, not Build's report): `closeEvent` now disarms the watchdog via the
shared `_disarm_history_wave_watchdog()` helper (armed → `isActive()` False after close), close cancels
exactly the in-flight reqIds / empties the set / advances the generation, and the stranded-wave `reason`
is diagnostic-live so a timeout and a disconnect are distinguishable — while the AC-D16.4 shortfall wording
(`"incomplete"` + a named missing day + `"Historical backfill shortfall"`) and the no-fabrication guarantee
are preserved. Full offscreen suite re-run **493 passed, 0 failed, exit 0**. **No open escalations remain**
(ESC-001…ESC-025 all `addressed`).

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
- **Status: addressed**
  - Verified (2026-09-28, sixth pass): the repository owner applied the residual fixes to both root docs
    and I re-checked the live tree myself (not from the owner's word). `grep -n "269" usage.md
    PENDING_IMPLEMENTATION_PLAN.md` → **0 hits** (previously 1 in `usage.md`, 3 in the plan). `usage.md:166`
    now reads `# Full suite (383 tests, ~6s)`, and the current suite was independently re-measured this
    pass at **383 passed in 6.49s** (`QT_QPA_PLATFORM=offscreen`, exit 0) — the stated size is accurate.
    `PENDING_IMPLEMENTATION_PLAN.md:364`/`:412`/`:458` now read **383 passed**; all ten phase headers
    (`:69`, `:129`, `:172`, `:213`, `:243`, `:282`, `:326`, `:368`, `:416`, `:462`) now carry
    `✅ COMPLETE` (previously only Phases 6–10). The orphaned-`.pyc` part stays resolved via ESC-001 and
    the D5-index part via ESC-012. **ESC-011's enumerated residual is fully closed** — the three listed
    locations above are the entire scope this entry named. (A newly-noted, same-class instance in a
    *different* root doc — `test_plan.md:76` — was surfaced this pass and is tracked separately as
    **ESC-022**; it was never part of ESC-011's enumerated scope.)
- **Residual (re-checks 2026-09-28 second pass and 2026-09-28 third pass):** the orphaned-bytecode and
  D5-index parts are resolved (ESC-001 / ESC-012). What **remains**, unchanged, is root-doc drift that no
  pipeline agent owns:
  - `usage.md:166` still reads "Full suite (269 tests, ~1.5s)"; the current suite is **383 passed**.
  - `PENDING_IMPLEMENTATION_PLAN.md:364`, `:412`, `:458` still read "269 passed".
  - `PENDING_IMPLEMENTATION_PLAN.md` Phases 1–5 still carry no `✅ COMPLETE` marker (only Phases 6–10 do).
  Owner: **Requirements Analyst / repository owner (user)** — this is a recorded root-doc owner
  dependency (`requirements.md` DOC-1/DOC-2), not a Build task and not dispatchable by Build. Left open;
  no re-diagnosis beyond this.

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
- **Status: addressed**
  - Verified: `ui/chart_panel.py::_refresh_candles()` now applies `vb.setRange(...)` **before**
    `self.candlestick.set_data(...)` on the `auto_range` path, and the non-auto path regenerates the
    picture against the already-real range. Independently re-ran `tests/test_chart_dpi.py` → **5 passed**
    (dense body 4.004 device px @DPR1 / 8.007 @DPR2, wick 1). Reviewer probe (offscreen, 900×600,
    960×60s bars) confirmed the clamp binds on every path: first load 4.004 px, `set_timezone(-5h)`
    4.004 px, non-auto `_refresh_candles()` 4.004 px, empty load no error, symbol change returns the
    router to `IDLE`. T29 re-run green. (The sibling volume-width ordering defect this left in place is
    a distinct new finding — ESC-020.)

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
- **Status: addressed**
  - Verified: `ui/drawing_overlay.py::_update_inner_labels()` now stacks by
    `offset = max(15.0, height, last_height)` using `_label_scene_height()` (measured
    `mapRectToScene(boundingRect()).height()`) and clamps the whole label box inside `view_rect`.
    Reviewer probe measured the two near-price labels at **separation 23.00 px == measured bbox height**
    (was 15 px), no intersection; a degenerate collapsed y-range raised no exception. `T25-T01` genuinely
    discriminates — it asserts `centerΔ >= max(bbox height)` and `not intersects()`, both false under the
    old 15 px offset (fails at 15 < 23; non-tautological, and the pre-fix failure was reproduced). The
    vacuous `assert label.isVisible() or True` was replaced with real visibility + right-edge containment
    assertions (`tests/test_drawing_labels.py:69–73`). Re-ran the file → **5 passed** (×3, no flakiness).

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
- **Status: addressed**
  - Verified: `tests/test_volume_log.py::test_volume_zero_mapped_to_one` now asserts
    `y_range[1] == approx(_nice_volume_max(max_vol), rel=0.02)` **and** pins
    `_nice_volume_max(max_vol) == approx(1_500, rel=0.02)`; the stale `max 1000 -> 10k` comment is
    corrected. Real, not looser: the previous `approx(10_000, rel=0.1)` fails against the measured
    `1500.0`, and the pinned `== 1_500` fails if the family regresses to the removed 10k floor.
    Independently re-ran `tests/test_volume_log.py` → **3 passed**.

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
- **Status: addressed**
  - Verified: the four assertions in `tests/test_chart_crosshair.py::test_hover_inside_shows_lines_and_axis_chips`
    and `tests/test_crosshair_chip_bounds.py` (`::test_chip_visible_inside_right_edge`,
    `::test_chip_stays_inside_after_zoom`, `::test_long_price_and_edge_positions`) now assert the
    D2/Q33 lane contract — `anchor=(0,0.5)`, scene `pos().x() >= view_rect.right()`, and the bbox inside
    `[view_rect.right(), view_rect.right()+axis('right').width()]`. Non-tautological: the old inside-plot
    behaviour (`anchor=(1,0.5)`, `pos().x() <= view_right-1`) fails both `>= view_right` and
    `anchor.x()==0`. Independently re-ran both files → **16 passed** (12 + 4); the pre-change baseline
    reproduced ESC-016's exact 4 failures.

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
- **Status: addressed**
  - Verified: `ui/main_window.py` connects `drawing_overlay.mode_changed` →
    `_on_drawing_tool_mode_changed`, which calls a `blockSignals`-guarded
    `_reset_draw_combo_to_cursor()` when the tool falls back to `"cursor"`; the alarm-mode reset routes
    through the same helper. Re-running `tests/test_draw_combo_sync.py` → **3 passed** (`T36-T01`
    zoom-cancels-draw, `T36-T02` TR-17 symbol change, `T36-T03` no spurious signal + alarm path intact).
    Re-entrancy is genuinely prevented: `_on_draw_tool_changed` is only reachable via
    `currentTextChanged`, which `blockSignals(True)` suppresses (asserted `seen == []`), and the helper
    early-returns when the combo already reads `"Cursor"`. The legitimate user re-arm path
    (`_arm` → `DRAWING`) and the alarm-mode reset both still work.

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
- **Status: addressed**
  - Verified: `docs/tasks/task-graph.json:1256` now reads `"Fixture mappings (ESC-018)"` and the T22-T02
    (`:1270`) / T22-T06 (`:1298`) descriptions assert the confirmed `input -> output` mappings plus family
    membership; the term "fixed point" no longer appears in any task graph acceptance criterion or test
    description (remaining hits are only in build/review history). `tests/test_volume_linear.py` T22-T02/
    T22-T06 implement exactly that wording. Re-ran `tests/test_volume_linear.py` → **11 passed**.

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
- **Status: addressed**
  - Verified: no eye glyph remains in any Plan-owned artifact — `grep -rn "👁" docs/` returns hits only in
    `docs/build/**` and this review's own historical entries. `docs/plan.md:111,113` now read "not an eye
    icon" and `QPushButton("Volume")`; `docs/plan_proposal.md:16,46,208,341` and
    `docs/architecture_proposal.md:26,52,56,609,614,678,827` all describe the checkable text label
    `Volume`; `docs/plan_review.md` records the correction.

## ESC-020 — D9 volume bar width does not follow the clamped price body width on the first (auto-range) load

- **Linked task/defect:** T13 (D9) — sibling ordering defect exposed while verifying ESC-013/T32
- **Observed:** In `ui/chart_panel.py::_refresh_candles()` the volume half-width `w_vol` is computed by
  reading the price `ViewBox.viewRange()` (`:805–823`) **before** the auto-range branch applies
  `vb.setRange(...)` (`:849`); `volume_bars.setOpts(width=w_vol*2)` is likewise called at `:831`, before
  the range is set. On a first load the range is still the untouched default, so the volume
  `min_w_vol` clamp never binds and the unclamped width is used. Reviewer probe (offscreen, 900×600,
  960×60 s bars): first load candle body = **4.004 device px** but volume bar = **0.517 device px**
  (39 data units vs the price body's 302); after one non-auto `_refresh_candles()` the volume width jumps
  to **4.000 device px** and matches. T32 fixed this ordering for the candle picture; the identical
  ordering defect remains for `w_vol`.
- **Expected:** `AC-D9.1` / `AC-D9.2` (`docs/requirements/requirements.md:765–770`) — "the volume bar
  width equals the price body width (`w*2`)"; "Given a dense 1-min view where the 4px body minimum
  applies … Then volume bars follow the same clamped `w`". Architecture D9 row (`docs/architecture.md:40`)
  states the shared `w` "guarantees vertical alignment including the dense 4px minimum".
- **Root cause:** `w_vol` and its `setOpts` are evaluated before the target x-range is applied — the same
  generate-before-`setRange` ordering T32 fixed for the candle picture, left in place for the volume
  width. Not a regression introduced by T32; a sibling instance of the same defect.
- **Witness the current test misses it:** `tests/test_volume_width.py::test_volume_width_dense_clamped`
  only asserts `vol_width > 10` (39 passes) and `!= 0.6`; it never compares the volume width to the
  clamped candle body width, so it passes with the unclamped value.
- **Suggested direction:** compute `w_vol` / call `volume_bars.setOpts` **after** the real x-range is
  applied on the auto-range path (or derive the clamp from the target span), mirroring T32's reorder; and
  strengthen `test_volume_width_dense_clamped` to assert the dense-view volume width equals the clamped
  price body width (`w*2`), not merely `> 10`.
- **Status: addressed**
  - Verified: `ui/chart_panel.py::_refresh_candles()` now applies `vb.setRange(...)` (`:827–828`) **before**
    the `w_vol` / `min_w_vol` block (`:838–854`) and `volume_bars.setOpts(width=w_vol*2)` (`:858`), so
    `w_vol` is derived from the **final** range on every path — first/auto-range load, non-auto/intra-bar
    refresh, `set_timezone`, empty load (`w_vol=0.25`) and symbol change. Reviewer offscreen probe
    (900×600, 960×60 s bars): first load candle body **4.0036 device px** vs volume bar **4.0000 device px**
    (pre-fix sibling value was 0.517); dense 301.730 vs 301.730 data units at the final range, non-dense
    195 vs 195 (17.28 device px both). The strengthened
    `tests/test_volume_width.py::test_volume_width_dense_clamped` is **real, not tautological**: run against
    the pre-fix ordering (HEAD `952a083`, `setOpts` at `:832` before `setRange` at `:844`) it fails
    `assert 39.0 == 301.73023255860653 ± 3.0173`, and passes on the fixed tree (`2 passed`). No
    candle-fix regression: `tests/test_chart_dpi.py` 5 passed, `tests/test_volume_linear.py` +
    `test_volume_log.py` + `test_volume_ceiling.py` + `test_volume_toggle.py` 26 passed; full suite
    **383 passed, 0 failed**. Residual (non-blocking) test-robustness gap recorded as the new ESC-021.

## ESC-021 — D9 width test binds the volume width to a re-derived formula, not to the rendered candle body

- **Linked task/defect:** T13 (D9) — strengthened `tests/test_volume_width.py`
- **Observed:** the strengthened D9 tests compute the "expected price body width" analytically in the test
  helper `_clamped_price_body_width()` (`tests/test_volume_width.py:9–23`), duplicating the production
  candle formula (`median_diff * 0.325`, `min_w = 2.0 / px_per_sec`), and assert `vol_width` against that
  re-derivation. They never read the **actual** `CandlestickItem` body geometry. Concrete demonstration:
  taking the fixed working tree and changing only the candle half-width in
  `ui/candlestick_item.py:98` from `median_diff * 0.325` to `median_diff * 0.30` (a genuine D9
  misalignment — real candle bodies now narrower than the volume bars) still yields
  `tests/test_volume_width.py` → **2 passed**. So a future D7-style gap change applied to only one of the
  two duplicated constants would silently break the D9 "volume width equals price body width" contract
  without failing this test.
- **Expected:** the D9 test should bind the volume bar width to the **rendered candle body** width (as
  `tests/test_chart_dpi.py::body_geometry` already does by measuring the item's `QPicture`), not to a
  second copy of the formula. Today's alignment does hold (probe: dense 301.730 == 301.730 data units,
  non-dense 195 == 195), so this is a robustness gap, not a present defect.
- **Root cause:** the `w` computation is duplicated across `ui/candlestick_item.py::_draw_candles`
  (generation) and `ui/chart_panel.py::_refresh_candles` (volume width); the test mirrors the second copy,
  so it can only detect volume-side regressions (which is how ESC-020 was caught), not candle-side drift.
- **Suggested direction:** in `test_volume_width_*`, derive the expected body width from the rendered
  `panel.candlestick` picture (bbox width − timestamp span, accounting for cosmetic-pen inflation) and
  compare the volume width to that, or factor the shared `w` computation into one helper both production
  sites call. Test-only or small-refactor change; not blocking any acceptance criterion.
- **Status: addressed**
  - Verified: `tests/test_volume_width.py` no longer re-derives the production formula. The duplicated
    helper `_clamped_price_body_width()` is gone (grep shows no references; no live `0.325`/`median_diff`
    formula in the file — only the two docstring/comments that explain its removal). Both tests now obtain
    the expected width by **measuring the rendered item**: `_measured_body_width()` reads
    `panel.candlestick.boundingRect()` (the recorded `QPicture` bbox) and subtracts the timestamp span,
    exactly `tests/test_chart_dpi.py::body_geometry`; `_px_per_sec()` derives the scale from the final
    `ViewBox.viewRange()`. Neither `candlestick` nor `volume_bars` appears in any expected-value
    derivation, so the two sides are genuinely independent.
  - **Drift experiment re-run by the reviewer** (not taken from Build's report): backed up
    `ui/candlestick_item.py` (sha256 `6eb4dc49…58ffb`), applied only `median_diff * 0.325 → 0.30` at
    `:98`, cleared `__pycache__`, ran `tests/test_volume_width.py` → **1 failed, 1 passed**, non-dense
    `T13-T01` `assert 195.0 == 180.0 ± 3.6` (exactly Build's reported figure); restored from backup and
    re-verified the same sha256 `6eb4dc49…58ffb` with `git status --short ui/candlestick_item.py` empty
    (clean vs HEAD), then re-ran the file → **2 passed**. The candle-side drift the old formula-mirror
    missed is now caught.
  - **No assertion weakened or made tautological:** the expected value is a *different* quantity from the
    asserted one (measured candle render vs volume `opts['width']`), so the equality is non-tautological
    (the drift run proves it fails). The dense 4-device-px checks survive
    (`measured_body * px_per_sec ≈ 4.0` and `vol_width * px_per_sec ≈ 4.0`), as do both real regressions
    (`!= 0.6`, `!= 39.0`). The dense tolerance stays **2%** (`rel=0.02`) and is meaningful: it absorbs
    only the integer `QPicture` bbox quantisation (~1.0 data unit on the non-dense 195 / ~0.27 on the
    dense 301.7), while the `39.0` regression sits ~9.8% away — far outside it. Counter-check: Build's own
    pre-fix ordering experiment (`ESC-020` re-simulated) makes dense `T13-T02` fail `assert 39.0 == 302.0
    ± 6.04`, which I re-confirmed independently on the wave-11 tree in the previous pass; the ESC-020
    witness is therefore retained.
  - Suite re-verified: full offscreen run **383 passed, 0 failed, exit 0**; `test_volume_width` +
    `test_chart_dpi` + `test_chart_mouse_router` spot-check **22 passed**. `ui/candlestick_item.py` and
    `ui/chart_panel.py` sha256s match the pre-rework values (no product change, no diagnostic residue).

---

## Sixth-pass finding (2026-09-28) — root-doc drift outside ESC-011's enumerated scope

Surfaced while verifying ESC-011: the owner's fix correctly closed every location ESC-011 named, but the
same documentation-drift class still persists in a *third* root doc that ESC-011 never listed.

## ESC-022 — `test_plan.md` still advertises the stale full-suite figure "269 passed in ~1.5s"

- **Linked task/defect:** n/a (root-level doc, no pipeline agent owns it)
- **Observed:** `test_plan.md:76`, in section `### 4.3 Run Full Test Suite (all tests)`, shows
  `python -m pytest tests/ -v` with the comment `# → 269 passed in ~1.5s (all phases)`. The current suite
  is **383 passed in ~6.5s** (independently re-measured this pass: `383 passed in 6.49s`, exit 0,
  `QT_QPA_PLATFORM=offscreen`). This is the identical drift class ESC-011 tracked, but in `test_plan.md`,
  which ESC-011's observed/residual scope (`usage.md`, `PENDING_IMPLEMENTATION_PLAN.md`) never named, so it
  survived the owner's fix. `test_plan.md` presents itself as a current living doc (Purpose: "defines the
  scope, organization, and execution strategy for the automated GUI test suite"), so the figure reads as
  the present full-suite output, not a historical snapshot.
- **Expected:** an accurate current full-suite figure/timing, consistent with `usage.md:166`
  (`# Full suite (383 tests, ~6s)`) and `PENDING_IMPLEMENTATION_PLAN.md:364`/`:412`/`:458` (383).
- **Root cause:** the doc was not updated after later batches landed — same cause as ESC-011.
- **Suggested direction:** the repository owner updates `test_plan.md:76` to the current figure
  (e.g. `# → 383 passed in ~6s (all phases)`). Wording-only; not a Build task and not dispatchable by
  Build. (Line `:149` "All 98 GUI tests pass" refers to the GUI subset, not the full suite, and is not
  asserted to be stale.)
- **Status: addressed**
  - Verified (2026-09-28, seventh pass): the repository owner updated `test_plan.md:76` and I re-checked the
    live tree myself (not from the owner's word). `test_plan.md:76` (section
    `### 4.3 Run Full Test Suite (all tests)`) now reads `# → 383 passed in ~6.5s (all phases)` (was
    `269 passed in ~1.5s`). I independently re-measured the current suite this pass:
    `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`383 passed in 6.13s`**,
    exit 0 — the count is exact and the timing is the same order. A repo-root `*.md` sweep confirms **no
    `269` remains in any root doc** (`grep -rn "269"` now hits only pipeline history: `docs/code_review/**`
    and `docs/requirements/**`). No other full-suite count in `test_plan.md` is stale: `:149`/`:159`/`:175`
    ("98 GUI tests") are the legitimate GUI subset, and `:151`'s `< 5s full suite runtime` is a stated CI
    target/acceptance criterion, not a present-tense measured output — not a count claim, so not treated as
    drift. `usage.md:166` (383) and `PENDING_IMPLEMENTATION_PLAN.md:364`/`:412`/`:458` (383) remain
    consistent; `:322`'s "254 passed" is inside Phase 6's historical completion record, not a living figure.

---

## Verified with no escalation

- **E4 — D12 zone "Extend" removal / payload migration:** verified clean. No persisted extend flag
  (`data/db.py:59–67`), zone payload is `{"x1","x2","y1","y2"}` only
  (`services/drawing_service.py:61–71`), rendering consumes `y1/y2` (`ui/drawing_overlay.py:275–284`),
  dialog omits the control (`ui/zone_settings_dialog.py:4–5`, `:54`). Prior zones render unchanged;
  no migration required.

---

## D16 batch (Batch 10, T37–T41) — new findings, 2026-10-02

Source: `docs/code_review/review_log.md` §"Revision 8 review — D16". Reviewed against the live tree
(every base-file read from disk, suite re-run by the reviewer), not Build's report. No live TWS was
used — all runs were `QT_QPA_PLATFORM=offscreen`.

## ESC-023 — Calendar marks the year-end Friday (Dec 31) closed when New Year's Day falls on Saturday

- **Linked task/defect:** T37 (D16) — the ET trading-day/holiday calendar
- **Observed:** `services/market_calendar.py::_observed()` (`:82–92`) shifts **any** Saturday
  fixed-date holiday to the preceding Friday, and is applied to New Year's Day at `:112`. In every
  year whose Jan 1 is a Saturday it therefore flags **Dec 31 of the prior year** as a market closure.
  Reviewer probe: `is_trading_day(date(2021,12,31)) is False`, and likewise for `2027-12-31`,
  `2032-12-31`, `2038-12-31`. This behaviour is asserted deliberately by the acceptance criterion
  `docs/tasks/task-graph.json` T37-T03 ("New Year's 2022-01-01 Saturday gives 2021-12-31 Friday
  closed") and by `tests/test_market_calendar.py:112–114` (`assert is_trading_day(date(2021, 12, 31))
  is False`).
- **Expected:** US equity markets do **not** close on the preceding Friday when that Friday is the
  **year-end accounting date**. NYSE Rule 7.2's Saturday→preceding-Friday rule carries an explicit
  exception for "unusual business conditions … such as the ending of a … yearly accounting period",
  and the market was in fact **open on Friday 2021-12-31** (independent sources: Bloomberg, "Why
  Stock Market Will Be Open on New Year's Eve 2021"; Benzinga quoting NYSE on the calendar/fourth-
  quarter accounting-period end; USA Today). So Dec 31 of a Jan-1-Saturday year is a **trading day**
  and must be treated as one; the other observed-shift cases (Independence Day Sat→Fri, Christmas
  Sat→Fri/Sun→Mon, Juneteenth) are correct and unchanged.
- **Consequence for D16 (`AC-D16.1` / `AC-D16.4`):** `find_missing_spans` classifies days via
  `is_trading_day`, so a genuine missing-bar hole on such a Dec 31 is treated as a "genuine closure":
  it is never requested and never surfaced by `_finalize_history_wave`. That is exactly the **silent
  hole** `AC-D16.1` ("no artificial hole") and `AC-D16.4` ("never a silent hole") forbid. It is
  latent (next occurrence 2027-12-31) and does not affect the reported Sept-2026 repro, so it is not
  blocking — but it is a real calendar-correctness defect.
- **Root cause:** the **acceptance criterion itself** encodes an inaccurate US-equity convention
  (a naive Saturday→preceding-Friday shift with no year-end exception); the code faithfully
  implements that AC, so this is a requirements/domain gap, not an implementation deviation.
- **Suggested direction:** the Requirements Analyst corrects the D16 holiday convention to include
  the NYSE year-end (monthly/yearly accounting-period) exception. Then Task Manager updates the
  T37-T03 AC, and Build adjusts `services/market_calendar.py::_observed` (and
  `tests/test_market_calendar.py:112–114`) so Dec 31 stays open when it is the preceding Friday of a
  Saturday New Year's Day. No other observed-shift case changes; no bars are fabricated.
- **Status: addressed**
  - Verified (2026-10-02, ESC-023 correction round; HEAD `9c2fafa` + uncommitted D16 changes):
    independently re-checked on the live tree, not from Build's report.
    - **Requirements corrected:** `docs/requirements/requirements.md` now carries **`AC-D16.7`**
      (`:1233–1251`) — Dec 31 of a Jan-1-Saturday year returns **True** (NYSE Rule 7.2 year-end
      accounting-period exception), with the four dates and the unchanged-shift regression guards;
      A33 (`:1322`) and R27 (`:1395`) record it; the Status header (`:3`) and Journey 17 (`:298`)
      both state Dec 31 is a trading session. The old naive Saturday-to-preceding-Friday rule is gone.
    - **Task graph corrected:** `docs/tasks/task-graph.json` T37 acceptance criterion 3 + T37-T03
      now require `is_trading_day(2021-12-31/2027-12-31/2032-12-31/2038-12-31) is True`, keep the
      unchanged shifts (2026-07-03/2022-12-26/2027-06-18/2023-01-02 closed), and assert the
      Saturday legal date 2022-01-01 non-trading with 2022-01-03 trading; **no** assertion expects a
      Dec 31 closure any more.
    - **Code corrected:** `services/market_calendar.py::_holidays_for_year()` (`:116–121`) now adds a
      New Year's closure only when Jan 1 is **not** Saturday; `_observed()` itself is unchanged.
    - **Behaviour re-verified by the reviewer** (offscreen, no live TWS), against the live module:
      `is_trading_day` is **True** for 2021-12-31, 2027-12-31, 2032-12-31, 2038-12-31 (all Fridays;
      each Jan 1 is a Saturday); `2022-01-01` (Sat) is False, `2022-01-03` (Mon) is True; the Sunday
      Jan 1 2023 case is still observed `2023-01-02 is False`; and every other observed shift is
      unchanged (`2026-07-03` False, `2022-12-26` False, `2027-06-18` False; legal weekend dates
      2026-07-04 / 2022-12-25 / 2027-06-19 all False). No substitute closure is created.
    - **Tests corrected and green:** `tests/test_market_calendar.py::test_t37_t03_new_years_year_end_exception_keeps_dec31_open`
      (`:128–145`) asserts exactly the corrected contract; the wrong `date(2021,12,31)` entry was
      removed from the weekend-legal-dates loop. Independently re-ran
      `tests/test_market_calendar.py` -> **35 passed** (T37-T01…T37-T06).
    - **No weakening:** the corrected assertions are discriminating (they would fail under the old
      unconditional Saturday-to-Friday shift), and no other observed-shift guard was removed.

## ESC-024 — A dropped connection (or a stalled request) mid-wave never finalises and never surfaces the shortfall

- **Linked task/defect:** T39 (D16) — `ui/main_window.py` backfill orchestration
- **Observed:** `_on_disconnected` (`ui/main_window.py:392–396`) only updates the badge/status and
  disables the load button. It does **not** cancel or invalidate an in-flight backfill wave. If the
  connection drops mid-wave — or a request never yields `historical_data_end` (and no `error_msg`) —
  `_history_req_ids` never empties, `_finalize_history_wave` never runs, and the chart keeps the
  un-backfilled cached bars (including the internal hole). The only feedback is the generic
  "Disconnected" status; no shortfall is surfaced by the D16 mechanism. There is also no timeout /
  watchdog around a wave.
- **Expected:** `AC-D16.4` requires that where data genuinely cannot be obtained, the chart shows
  only available bars and the shortfall is **surfaced explicitly — never a silent hole**. A
  dropped/stalled wave is exactly that case.
- **Root cause:** the wave lifecycle handles switch/close (cancel + generation advance) and per-chunk
  errors, but not a transport drop or a request that never completes.
- **Suggested direction:** on `_on_disconnected`, cancel/drain the tracked wave, advance
  `_history_generation` so late responses are ignored, and surface the outstanding shortfall; and/or
  add a bounded timeout for a wave with no progress. **Do not fabricate any bar.** (Nice-to-have: the
  current reported repro and the suite pass without this; it is a robustness edge, not a live defect.)
- **History — re-routed by Code Reviewer on the ESC-023 correction pass (2026-10-02):** the finding itself was
  unchanged and still reproduced by code reading against the live tree: `_on_disconnected`
  (`ui/main_window.py:392–396`) did not touch `_history_req_ids`/`_history_generation`, and there was no
  wave timeout. It was a genuine, unmitigated robustness edge under `AC-D16.4` ("surfaced explicitly —
  never a silent hole"), not accepted scope: no requirement, assumption, risk row, AC, or task covered a
  transport drop or a stalled request (R22 covers pacing/shortfall from a *responding* peer only; the
  switch/close cancel path and `_on_error` do not cover a peer that goes silent). The owner moved from
  BUILD to TASK_MANAGER because there was no task carrying ESC-024 and the then-current graph's
  **T42-T02** required `ui/main_window.py` to be unchanged, so an ESC-024 fix would have failed T42's own
  gate by construction; the missing piece was a Task-Manager-owned task/AC. Task Manager added **T43**
  (with T43 AC1–AC6 and T43-T01…T43-T06) and, since T42 is now `done`, actioned it this round.
- **Status: addressed**
  - Verified (2026-10-02, ESC-024 rework round; T43 `done`, HEAD + uncommitted D16 changes). Independently
    re-verified on the live tree by re-running the T43 module and by reviewer probes (offscreen, no live
    TWS), not from Build's report:
    - **Disconnect drain (AC1):** a real 3-request wave (`load_chart`, seeded internal hole covering two
      full trading weeks) then `_on_disconnected()` with no responses delivered → `cancel_historical_data`
      called for exactly `{8000,8001,8002}`, `_history_req_ids == set()`. `tests/test_history_backfill_disconnect.py`
      → **6 passed** in isolation; reviewer probe reproduced the same set equality.
    - **Generation advance / late-event rejection (AC2):** `_history_generation` strictly increased;
      `_history_event_accepted(pre_drop_rid) is False`; a late `_on_historical_bar` + `_on_historical_data_end`
      for a pre-drop reqId appended nothing to `_pending_bars` and did **not** run `_finalize_history_wave`
      a second time (finalise spy recorded exactly one call).
    - **Shortfall surfaced exactly once (AC3):** status bar now reads
      `"<SYM> — backfill incomplete: 10 trading day(s) still missing (2026-10-19, …)"` and a
      `"Historical backfill shortfall …"` WARNING is emitted; finalise ran exactly once.
    - **No fabricated bar (AC4):** post-drop `BarCache.get_bars` timestamps equal the seeded set exactly;
      no missing-span day leaks into `_bars` or the volume `x` series; `_pending_bars == []`.
    - **Watchdog (AC5):** with no connection drop, `_on_history_wave_timeout()` cancels every tracked reqId,
      empties the set, advances the generation, disarms the timer, surfaces the same shortfall once, and
      fabricates no bar (probe: timer `remainingTime ~29868 ms` while armed; disarmed after).
    - **No-op disconnect (AC6):** with a completed single-request wave (`_history_req_ids == set()`),
      `_on_disconnected()` ran `_finalize_history_wave` **zero** times, did not raise, and set the badge
      `"● Disconnected"` / status `"Disconnected from IBKR"`. Double-disconnect is idempotent (one finalise).
    - **No regression:** full offscreen suite re-run by the reviewer → **489 passed, 0 failed, exit 0**
      (9.22s), confirming the D16 batch (T37–T42, incl. the ESC-023 year-end correction: `is_trading_day`
      True for 2021-12-31/2027-12-31, False for 2022-01-01) and the ESC-023 correction still hold. The
      worker's three flagged flaky tests pass in isolation (`5 passed`). All D16 modules
      (`market_calendar`, `backfill_service`, `history_backfill_loadpath`, `history_backfill`,
      `history_backfill_disconnect`) → **106 passed**; no live-TWS references in the new test.
    - ESC-024's originally observed gap (no `_history_req_ids`/`_history_generation` handling on
      `_on_disconnected`, no wave timeout) is closed: `_finalize_stranded_history_wave` (shared by
      `_on_disconnected` and the 30 s `QTimer` watchdog) cancels the wave, advances the generation, and
      finalises once. Two non-blocking residual quality items surfaced by this pass are tracked separately
      as **ESC-025**.

## ESC-023 correction pass — no new findings (2026-10-02)

The ESC-023 correction round (T37 rework + T42 regression gate) introduced no new finding. Review
verified the full D16 batch still holds — see `review_log.md` §"Revision 9 review".

## ESC-024 rework round — new findings, 2026-10-02

Source: `docs/code_review/review_log.md` §"Revision 10 review — ESC-024 rework". Reviewed against the
live tree (T43's `ui/main_window.py` + `tests/test_history_backfill_disconnect.py` read from disk, the
T43 module and the full suite re-run by the reviewer); no live TWS was used (all runs
`QT_QPA_PLATFORM=offscreen`). ESC-024 itself is verified and closed; the two residual items below are
non-blocking quality notes on the new code.

## ESC-025 — New watchdog QTimer outlives `closeEvent`, and the stranded-wave `reason` is discarded

- **Linked task/defect:** T43 (D16 / ESC-024) — `ui/main_window.py` wave lifecycle
- **Category / severity:** `quality` / **nice-to-have** (no functional or AC impact; latent tidiness)
- **Observed (two small items, one entry):**
  1. **Watchdog not disarmed on close.** `closeEvent` (`ui/main_window.py:1357–1390`) calls
     `_cancel_history_requests()` + `_history_generation += 1` (lines 1370–1373) but never calls
     `_disarm_history_wave_watchdog()`. Reviewer probe (offscreen, seeded 3-request wave):
     `win._history_wave_timer.isActive()` was `True` **before** `win.close()` and still `True`
     **after** it, with `_history_req_ids == set()` and the ids cancelled. The single-shot timer is
     parented to the window (`timer.parent() is win`) and `close()` does not destroy the object, so if
     the event loop keeps running after the window closes, the timer fires `_on_history_wave_timeout`
     ~30 s later. That path is currently *benign* — `_finalize_stranded_history_wave` returns `False`
     immediately because `_history_req_ids` is empty, so there is no double-finalise and no exception
     (verified: firing it manually post-close is a no-op) — but the armed timer outliving the window is
     untidy and relies on the empty-set guard rather than symmetry.
  2. **`reason` is a dead parameter.** `_finalize_stranded_history_wave(reason=...)`
     (`ui/main_window.py:412`) accepts `reason` and both call sites pass a meaningful string —
     `"Disconnected from IBKR"` (`:409`) and `"Historical backfill timed out"` (`:443`) — but the
     parameter is never read or logged anywhere (grep for `reason` in `ui/main_window.py` → only the
     3 definition/call-site lines). Consequently a **watchdog timeout** and a **transport disconnect**
     produce the identical surfaced message (`"<SYM> — backfill incomplete: N trading day(s) still
     missing (…)"`) with no indication of which cause stranded the wave — the diagnostic distinction
     the call sites clearly intended is silently lost.
- **Expected / direction (for Build, wording-only / small code change, no AC change):**
  1. Add `self._disarm_history_wave_watchdog()` to `closeEvent` (next to the existing
     `_cancel_history_requests()` call) so arm/disarm is symmetric across all wave-terminating paths
     (finalise, disconnect, watchdog, switch/`load_chart`, close).
  2. Either use `reason` (e.g. append it to the status-bar/log shortfall line, or `_LOG.warning` it) so
     a timeout and a disconnect are distinguishable in diagnostics — as the two call sites already
     imply — or drop the parameter entirely if it is not wanted. This is a **behaviour-neutral**
     diagnostics improvement; it does **not** require an acceptance-criterion or test change and must
     **not** alter the shortfall wording that T43-T03/T43-T05 assert on (`"incomplete"` + a named
     missing day + the `"Historical backfill shortfall"` log record must still hold).
- **Not blocking:** full offscreen suite **489 passed / 0 failed**; T43's own 6 tests all pass. Neither
  item affects any T43 acceptance criterion or fabricates a bar. No test should be weakened to fit it.
- **Status: addressed**
  - Verified (2026-10-02, ESC-025 rework round; T44 `done`). Independently re-verified on the live tree
    by reading `ui/main_window.py` and by reviewer probes (offscreen, no live TWS), not from Build's report:
    - **Item 1 — arm/disarm symmetry on close:** `closeEvent` (`ui/main_window.py:1397`) now calls
      `self._disarm_history_wave_watchdog()` before `_cancel_history_requests()` + the
      `_history_generation += 1` bump. Reviewer probe (seeded 3-request wave): `_history_wave_timer.isActive()`
      was **True** before `win.close()` and **False** afterwards; the cancelled set equalled the in-flight
      reqId set exactly, `_history_req_ids == set()`, and the generation advanced. Firing
      `_on_history_wave_timeout()` post-close ran `_finalize_history_wave` **zero** times (benign no-op
      preserved; the empty-set guard remains). Disarm now routes through the same shared
      `_disarm_history_wave_watchdog()` helper used by finalise/disconnect/timeout/load_chart, satisfying
      T44-AC2's symmetry requirement.
    - **Item 2 — `reason` is diagnostic-live and distinguishes the two causes:** my probe stranded the same
      3-request wave two ways. Timeout (`_on_history_wave_timeout`, reason `"Historical backfill timed out"`)
      produced status `"… backfill incomplete: 10 trading day(s) still missing (2026-10-19, …). [Historical
      backfill timed out]"` + WARNING `"Historical backfill shortfall … [Historical backfill timed out]"`;
      disconnect (`_on_disconnected`, reason `"Disconnected from IBKR"`) produced the same shortfall with
      `[Disconnected from IBKR]`. The two diagnostics genuinely differ by the named cause — `reason` is
      read (stashed at `:434`, consumed at `:787`, cleared at `:788`), no longer dead.
    - **AC-D16.4 / D16 wording preserved:** both shortfall lines still contain `"incomplete"` and name a
      still-missing trading day; both WARNINGs still read `"Historical backfill shortfall"`. T43-T03/T43-T05
      remain green (retained verbatim), so the wording contract is unbroken.
    - **Behaviour-neutral (no stale suffix leak):** `_history_stranded_reason` is cleared to `""` by the
      finaliser on **every** path; a subsequent normal finalise produced `"… backfill incomplete: …"`
      with **no** bracket suffix (probe: `" [" not in msg`), and the stash read back `''` after both a
      stranded finalise and a normal one. No bar fabricated: post-drop cache timestamps and
      `chart_panel._bars` equalled the seeded set, `_pending_bars == []` (T44-T04 + reviewer probe).
    - **Tests:** `tests/test_history_backfill_disconnect.py` → **10 passed** (T44-T01…T44-T04 + retained
      T43-T01…T43-T06). Full offscreen suite re-run by the reviewer → **493 passed, 0 failed, exit 0**;
      D16 modules in isolation → **110 passed**; ESC-023 year-end exception intact
      (`is_trading_day` True for 2021-12-31/2027-12-31, False for 2022-01-01); no live-TWS references in
      the new tests. All four T44 acceptance criteria independently verified.

---

## Batch 11 (D17 + D18, T45–T51) — new finding, 2026-10-03

Reviewed against the live tree (full offscreen suite re-run by the reviewer → **562 passed / exit 0**, two
runs, no segfault; the pure helper and the T49 `MainWindow` workaround probed directly; the D2/D17/D18 test
suites re-run). `failures.json.blocked` is empty; T45–T51 are all `done`. ESC-001…ESC-025 remain `addressed`
(verified — nothing relevant changed for them). One new escalation below.

## ESC-026 — `ui/dock_layout.py::plan_dock_widths` can return a width below a dock minimum

- **Linked task/defect:** T45 (D17/D18 Phase 1, `ui/dock_layout.py`) — reported in
  `docs/build/failures.json.pending_routing` `kind: dock_layout_plan_below_minimum`.
- **Routed to:** BUILD.
- **Category / severity:** `bug` / **should-fix** (not blocking — no task is held by it; the only production
  consumer, `MainWindow._plan_dock_widths`, carries a verified workaround, so AC-D18.4/AC-D18.5 hold at the
  MainWindow layer today. Fix it properly so the pure helper is not a latent trap.)
- **Root-cause classification:** `code_bug`. AC-D18.4 (`docs/requirements/requirements.md`, "never below the
  minimum") and the architecture row (`docs/architecture.md:663`) both specify the correct behaviour, and the
  function's own docstring (`ui/dock_layout.py:79–81`) promises it — the implementation simply violates them.
  This is not an AC or task-breakdown gap.
- **Observed vs. expected:**
  - **Observed** (`ui/dock_layout.py:100–114`, reproduced by the reviewer):
    `plan_dock_widths(750, 100000, 200) -> (350, 0)` (right `0 < RIGHT_DOCK_MIN_WIDTH = 200`);
    `plan_dock_widths(750, 200, 0) -> (175, 175)` (both below their minimums).
    A coarse reviewer grid (chart_area 100..3000 step 50 × requests {0,200,400,700,100000}²) found
    **108/1475** below-minimum combinations (Build's finer enumeration: 2158).
  - **Expected** (docstring lines 79–81; AC-D18.4): "neither width ever drops below its dock minimum … on an
    infeasible window … the dock minimums win." Each returned width must be `>= WATCHLIST_MIN_WIDTH`
    (`150`) / `RIGHT_DOCK_MIN_WIDTH` (`200`).
  - **Root cause:** the `while left + right > budget:` shrink loop decrements `left`/`right` (lines 107–114)
    **without re-flooring** at the dock minimums, so a dock that was already capped-floored at lines 89–90
    can be decremented below its own minimum.
- **Test gap (same route, worth fixing together):** T45's own tests never exercised the one-sided
  over-budget combination that starves the other dock — `test_T45_T06_one_side_over_budget` uses
  `(1200, 100000, 10)` (feasible at chart_area 1200), and `test_T45_T06_never_raises_and_integer_stable`
  asserts only `int`/stability. So T45 legitimately reported `done` with green tests. This is a coverage gap,
  **not** an incorrect AC, so it belongs with the code fix rather than a task-manager re-scope.
- **T49 workaround (context, verified sound — not the fix):** `MainWindow._plan_dock_widths`
  (`ui/main_window.py:1055–1118`) floors each width and re-shrinks the over-budget dock. The reviewer
  brute-forced it over **4,340** chart_area/request combos → **0 below-minimum, 0 raises**, including the
  exact repro inputs. So D18's ACs hold *today*, but the repo now has two divergent cross-clamp
  implementations and a future direct call of `plan_dock_widths` (or removal of the repair) reintroduces the
  defect.
- **Suggested direction (optional, for Build):** re-floor `left`/`right` at their minimums inside the shrink
  loop (or restructure so the chart minimum yields before a dock minimum is crossed); add a regression test
  for `plan_dock_widths(750, 100000, 200)` / `(750, 200, 0)`; once the helper is correct, remove the T49
  `_plan_dock_widths` repair to restore the single source of truth. No AC, architecture, or task-breakdown
  change is required or proposed.
- **Evidence retained:** reviewer reproduction commands and the 108/1475 grid result; Build's independent
  reproduction in `docs/build/failures.json.pending_routing` (wave-6 consolidation); T45's worker log
  (`docs/build/logs/T45.md`) and the untested combination in `tests/test_dock_layout.py`.
- **Status: addressed**
  - Verified (2026-10-03, ESC-026 rework round; T52 `done`). Independently re-verified on the live tree by the
    reviewer — my own probes and runs, not Build's report:
    - **Witnesses fixed:** `plan_dock_widths(750, 100000, 200) -> (150, 200)` and
      `plan_dock_widths(750, 200, 0) -> (150, 200)` — each component `>=` its dock minimum; the pre-fix
      `(350, 0)` / `(175, 175)` are gone.
    - **Grid clean:** my own coarse grid (chart_area 100..3000 step 50 × requests {0,200,400,700,100000}²) →
      **1475 total, 0 below-minimum, 0 raises** (was 108 below-minimum). I re-derived the pre-fix loop
      in-memory (no repo edit) and reproduced exactly 108/1475 + `(350,0)` + `(175,175)`, confirming the
      T52-T01/T52-T02 witnesses genuinely discriminate the bug (non-tautological).
    - **Precedence preserved:** infeasible `plan_dock_widths(400, 500, 500) == (150, 200)` (dock minimums win,
      chart minimum yields); feasible over-budget `plan_dock_widths(1000, 500, 400) == (200, 400)` and
      `(1000, 100000, 100000) == (200, 400)` keep `chart_area - left - right >= 400`.
    - **T49 workaround genuinely removed:** `MainWindow._plan_dock_widths` (`ui/main_window.py:1055–1099`) now
      contains no re-floor / combined-shrink repair — it only iterates the pure
      `ui.dock_layout.plan_dock_widths` to its post-resize fixed point (invariant `S = chart_area + cur_left +
      cur_right`, ≤24 passes). `git diff` shows the repair block added by T49 is gone.
    - **MainWindow path still enforces D18 cap + cross-clamp (reviewer probe, offscreen, no TWS, 1600×900):**
      over-cap drag → `right == 200 <= floor(0.40·chart_area)+1`; under-min drag →
      `right == RIGHT_DOCK_MIN_WIDTH (200)`, `watchlist == 150`; cross-clamp → `chart_area == 1716 >= 400`
      with `left=150 right=200`. So the D18 guarantees now rest solely on the corrected helper.
    - **Tests:** `tests/test_dock_layout.py` → **40 passed** (T45-T01…T06 + T52-T01…T04); retained
      Batch-11 D17/D18 set (`test_dock_widths_d18_impl`, `test_dock_widths_d18`, `test_dock_widths_d17`,
      `test_dock_d18_region`, `test_d10_d13_integration`, `test_watchlist`) → **40 passed**; full offscreen
      suite re-run **twice** → **566 passed, 0 failed, exit 0** each time.
    - **T45-T01 Qt-free guard still holds:** `test_dock_layout.py` has no module-scope Qt import; the only
      `PyQt6` reference outside the guard's string assertions is the function-local `from PyQt6.QtCore import
      Qt` inside T52-T04. Isolated `import ui.dock_layout` loads no PyQt6/pyqtgraph/PySide6, and the two
      T45-T01 tests pass in isolation. No test was weakened, skipped, or rewritten.
