# Code Review Log — NDThinkChart

**Reviewer:** Code Reviewer agent
**Date:** 2026-09-27
**Reviewed revision:** `09070e8` (clean working tree)
**Scope:** 11 user-reported findings + 2 housekeeping findings raised in project review.
**Method:** each finding is independently verified against the actual source and docs; every
diagnosis cites `file:line`. Nothing was fixed. Only `docs/code_review/` was written.

## Verdict summary

| # | Finding | Classification | Severity | Route |
|---|---------|----------------|----------|-------|
| F1 | Duplicate `_init_schema` in `data/db.py` | code_bug (latent) / hygiene | Medium | BUILD |
| F2 | Magnifier/drawing/zoom gesture precedence | architecture / design risk | Medium | PLAN |
| F3 | D8 `_nice_volume_max` coarse above 10M | code quality | Medium | BUILD |
| F4 | Missing "visual reference confirmed" gate | requirements/process gap | Medium | REQUIREMENTS |
| F5 | D10/D13 splitter "expand to fill" + missing integration test | missing test coverage | Medium | TASK_MANAGER |
| E1 | Crosshair chip vs D11 drawing labels overlap | code_bug (visual) | Medium | BUILD |
| E2 | `nice_max` stale on live tick clips tallest bar | code_bug | **High** | BUILD |
| E3 | Nice-tick lower bound 10k too coarse | code quality | Low–Medium | BUILD |
| E4 | D12 zone "Extend" removal / payload migration | verified clean | None | none |
| E5 | High-DPI claims unexercised (DPR=1 offscreen) | missing test coverage | Medium | TASK_MANAGER |
| E6 | D14 double-click mid-drag → overlay teardown | missing test coverage | Medium | TASK_MANAGER |
| HA | Documentation drift (usage count/timing, PENDING phases) | doc drift | Low | REQUIREMENTS |
| HB | Graph integrity + D5/D8 contradiction in requirements | requirements gap (+ tooling) | **High** | REQUIREMENTS |

Counts: **BUILD 5 · TASK_MANAGER 3 · PLAN 1 · REQUIREMENTS 3 · verified/no-action 1.**

---

## F1 — `data/db.py` defines `_init_schema` twice (shadowing)

**Verdict: CONFIRMED.** `data/db.py` defines `_init_schema` at `data/db.py:14` and again at
`data/db.py:113`. Python binds the second definition, so the first is dead code. A line-range
diff of the two bodies (`15–108` vs `114–207`) reports **IDENTICAL_BODIES**, so today the
shadowing is behaviourally harmless — but it is a latent trap: any future edit to the first
copy silently does nothing.

**Extra evidence:** a stale bytecode artifact `tests/__pycache__/test_db_schema.cpython-311-pytest-9.1.1.pyc`
(compiled 2026-09-27 15:39) exists with **no matching source** `tests/test_db_schema.py`, and the
tracked tree is clean. Its embedded docstring explicitly describes this bug and asserts a fresh
`DB()` table list plus "only one `_init_schema` definition exists". The requested regression test
was evidently drafted but never committed (working tree clean at `09070e8`). The duplicate is
still present in committed `data/db.py`.

- **Observed:** two identical `_init_schema` definitions; second shadows first.
- **Expected:** one definition; a regression test asserting the full table set from a fresh `DB()`.
- **Root cause:** duplicated method block merged into the file without deduplication.
- **Suggested direction:** delete the first definition (keep `data/db.py:113`), add the regression
  test described (table list: bars, watchlist, alarms, zones, drawing_groups, drawings, studies,
  positions, trade_groups, position_group_map). Ensure `tests/test_db_schema.py` is recreated as a
  real source file — do not rely on the orphaned `.pyc`.
- **Route:** BUILD. **Linked task/defect:** n/a (DB layer predates the task graph).

## F2 — Magnifier/drawing/zoom gesture precedence is implicit

**Verdict: CONFIRMED (as a design risk).** `ui/chart_mouse_router.py` is a 51-line class with no
state; precedence is encoded purely by call order in each handler:
- `view_mouse_press` (`:20–29`), `view_mouse_drag` (`:31–40`): zoom wins first if active, then alarm
  (only when no drawing tool active), then drawing.
- `view_mouse_click` (`:42–51`): zoom, then alarm, then drawing.

There is no `RouterMode`, no `_active_mode`, and no transition table. Crucially, activating the
magnifier does **not** clear a drawing tool (`ChartPanel.set_zoom_mode`, `ui/chart_panel.py:538–548`,
only syncs the overlay/button; `drawing_overlay.set_tool` is untouched), so zoom + drawing can both
be "active" and zoom simply takes precedence. The existing tests
(`tests/test_chart_mouse_router.py:35–68`) cover only alarm-vs-drawing precedence; there are no
zoom-vs-draw/alarm tests. Note the precedence *is* explicitly spec'd as "magnifier has highest
precedence" in task `T6-T05` (`docs/tasks/task-graph.json`), but the behaviour when a drawing is
mid-gesture and the magnifier is toggled is not defined anywhere.

- **Observed:** precedence by call ordering; zoom and drawing can be simultaneously active.
- **Expected:** an explicit `RouterMode` state machine (`IDLE/DRAWING/ZOOMING/ALARM_PLACING`),
  a single `_active_mode`, guard clauses in every handler, an explicit transition table, and named
  tests (`test_zoom_during_draw_cancels_draw`, `test_draw_blocked_during_zoom`,
  `test_alarm_placement_blocks_zoom`).
- **Root cause:** routing precedence was implemented implicitly and never promoted to an explicit
  state model; the draw/zoom interaction was left undefined.
- **Suggested direction:** Plan specifies the mode machine + transition table; Task Manager then
  adds the named tests. See `docs/requirements/open_questions.md` for the undefined draw+zoom case.
- **Route:** PLAN. **Linked task/defect:** T6 (router precedence), T20 (verification).

## F3 — D8 volume nice-tick list caps out at 10M

**Verdict: PARTIALLY CONFIRMED — the stated root cause is inaccurate.** `_nice_volume_max`
(`ui/chart_panel.py:45–55`) does **not** hard-cap at 10M; beyond the list it rounds up to the next
5M (`:54–55`). Measured behaviour: `10,500,000 → 15,000,000`, `40,000,000 → 45,000,000`,
`50,000,000 → 60,000,000`, `55,000,000 → 65,000,000`. The genuine defect is **coarse 5M steps above
10M** (a 10.5M max is overscaled to 15M), plus the quirk that a max of exactly `10,000` jumps to
`50,000` (target `11,000 > 10,000`). The existing test only exercises up to 2.2M
(`tests/test_volume_linear.py:55–64`), so the >10M path is untested.

- **Observed:** list-based nice values; coarse 5M rounding above 10M; no test >2.2M.
- **Expected:** a scaling nice-number formula; original list retained as a test fixture; a test at
  40–50M.
- **Root cause:** fixed lookup list with a coarse fallback instead of a continuous nice-number scale.
- **Suggested direction:** replace with `nice = f(max_vol)` producing 1/2/2.5/5 × 10^k; keep the old
  list as the reference fixture; assert monotonic, tight coverage at 40–50M.
- **Route:** BUILD. **Linked task/defect:** T12.

## F4 — Missing "visual reference confirmed" gate for UI-visual decisions

**Verdict: CONFIRMED (process gap, no code artifact).** Requirements already record the failure
mode: `docs/requirements/requirements.md:822` (risk `R2`) notes plan checkmarks are stale, and the
D5→D8 rework is documented as a direct consequence of a screenshot arriving after build
(`docs/architecture.md:25`, `docs/requirements/requirements.md:482–484`). There is no gate anywhere
in the docs requiring a confirmed visual reference before implementation starts for D10/D12/D15.

- **Observed:** UI-visual decisions are clarified from prose/screenshots after implementation
  (D5→D8 rework), with no pre-implementation visual-confirmation gate.
- **Expected:** a "visual reference confirmed" gate on UI-visual decisions (D10/D12/D15), required
  before implementation rather than a Q-numbered retrofit.
- **Root cause:** requirements workflow treats visual references as clarifications rather than a
  prerequisite artifact.
- **Suggested direction:** Requirements Analyst adds the gate as a process requirement / checklist
  entry covering D10, D12, D15. This is explicitly a process fix, **not** a code change.
- **Route:** REQUIREMENTS. **Linked task/defect:** n/a.

## F5 — D10/D13 "expand to fill" structure + missing integration test

**Verdict: CONFIRMED (test gap; architecture is answerable from code).** The chart's three panes
are a **single** vertical `QSplitter` — `ui/chart_panel.py:242–245` adds `price_plot`, `volume_plot`,
`osc_plot` to `self._splitter` and sets sizes. The watchlist is a **separate** `QDockWidget` in the
`LeftDockWidgetArea` (`ui/main_window.py:212–224`), i.e. not a nested splitter. D10 hides the volume
plot and calls only `self._splitter.refresh()` (`ui/chart_panel.py:342–356`), which does not itself
redistribute sizes; D13 clamps the dock width (`ui/main_window.py:675–686`,
`ui/watchlist_panel.py:36–45`). Existing coverage is weak/unit-level:
`tests/test_volume_toggle.py:18–37` asserts only `price_h_hidden >= price_h_before` (equality
passes), and there is no test combining volume-hide with a max-clamp watchlist drag asserting the
price panel never drops below its minimum.

- **Observed:** no integration test exercising volume hide + watchlist max clamp together; no
  shared `rebalance()` helper; doc does not state splitter structure.
- **Expected:** doc clarification (one three-pane `QSplitter`), one integration test hiding volume
  AND dragging the watchlist to its max clamp while asserting price panel ≥ its minimum, and
  consideration of a single `rebalance()` helper.
- **Root cause:** D10 and D13 were split across separate tasks (`T14`, `T17`) with no cross-cutting
  integration test.
- **Suggested direction:** Task Manager adds the integration test and a task to reconcile the
  splitter/dock rebalance behaviour. Architecture note can be added when Plan next revises.
- **Route:** TASK_MANAGER. **Linked task/defect:** T14, T17, T20.

## E1 — Crosshair price chip overlaps D11 drawing price labels

**Verdict: CONFIRMED.** The crosshair chip is created with `anchor=(1, 0.5)` and placed at
`view_rect_scene.right() - 2` (`ui/chart_panel.py:379`, `:413–417`). D11 drawing labels use the same
`anchor=(1, 0.5)` and `view_rect_scene.right() - 4` (`ui/drawing_overlay.py:335`, `:342`). The
stacking routine `_update_inner_labels` (`ui/drawing_overlay.py:358–393`) iterates **only**
`self._items` — i.e. drawing labels — and never considers the crosshair `_price_tag`. So hovering
the crosshair at a drawing's price stacks two chips ~2px apart with no deconfliction. The existing
test `test_labels_stack_not_overlapping` (`tests/test_drawing_labels.py:61–74`) only checks
drawing-vs-drawing collisions.

- **Observed:** identical anchor/x for crosshair chip and drawing labels; stacking ignores the chip.
- **Expected:** labels and chip do not overlap/stack illegibly.
- **Root cause:** D11 stacking logic was scoped to drawing-vs-drawing only; the crosshair chip
  precedent was reused geometrically but not included in collision accounting.
- **Suggested direction:** include the crosshair chip (or reserve its lane) in the stacking/label
  placement, or offset drawing labels when the chip is visible at the same price. Add a regression
  test hovering the crosshair at a drawing price.
- **Route:** BUILD. **Linked task/defect:** T3 (crosshair chip), T15 (drawing labels).

## E2 — `nice_max` goes stale on real-time updates and can clip the tallest bar

**Verdict: CONFIRMED (highest-severity chart correctness item).** The volume affine range is set
**only** inside the `if auto_range and self._bars:` block (`ui/chart_panel.py:659–671`;
`setRange` at `:671`). Intra-bar updates flow `update_last_bar` → `_refresh_candles()`
(`ui/chart_panel.py:584–600`) with `auto_range` defaulting to `False`, so bar heights are refreshed
(`:649–655`) but the volume Y range is not recomputed. The forming last bar's volume grows
continuously, so once it exceeds the previously computed `nice_max`, it is clipped. This also means
a timezone change (`set_timezone` → `_refresh_candles()`, `:508–516`) does not refit volume.
`docs/architecture.md:110–111` claims "`w` and `nice_max` are O(N) per data load over bars (not per
intra-bar tick)" — the perf claim is accurate but the correctness consequence (stale ceiling) is
unaddressed.

- **Observed:** volume Y range fixed at last full load; last bar can exceed it on a live tick.
- **Expected:** the ceiling tracks the live max (or is recomputed cheaply on the forming bar), or the
  staleness is explicitly documented and bounded.
- **Root cause:** volume auto-range is gated behind `auto_range=True`, which intra-bar updates never
  pass.
- **Suggested direction:** recompute `nice_max` for the forming bar on intra-bar ticks (cheap: one
  max over `_bars`), or track a running max and only widen the range. Add a test that grows the last
  bar's volume past the initial `nice_max` and asserts the bar is not clipped.
- **Route:** BUILD. **Linked task/defect:** T12.

## E3 — Nice-tick lower bound (10k) is too coarse for low-volume symbols

**Verdict: CONFIRMED.** The smallest nice step is `10_000` (`ui/chart_panel.py:47`). Measured:
`_nice_volume_max(800) == 10_000` and `_nice_volume_max(3_000) == 10_000`, so an 800–3,000 share
symbol renders bars at ≤30% of the panel height. The existing test even encodes this floor:
`tests/test_volume_linear.py:60–62` (`_nice_volume_max(8_000) == 10_000`). There is also the
`10_000 → 50_000` jump quirk (see F3).

- **Observed:** floor of 10k; low-volume symbols are visually flattened.
- **Expected:** a finer lower bound (e.g. 100/250/500/1k/2.5k/5k) so low-volume symbols fill the pane.
- **Root cause:** fixed list starts at 10k; no sub-10k nice values.
- **Suggested direction:** same scaling formula from F3 with a finer low end; test a low-volume
  symbol (800–3,000) to assert the axis is tight, not 10k.
- **Route:** BUILD. **Linked task/defect:** T12.

## E4 — D12 zone "Extend" removal / payload migration

**Verdict: VERIFIED CLEAN — no action required.** `normalize_payload` for zones
(`services/drawing_service.py:61–71`) accepts and returns only `{"x1","x2","y1","y2"}`; any extra key
is dropped, and rendering/hit-testing consume only `y1`/`y2` (`ui/drawing_overlay.py:275–284`,
`:495–500`). The `drawings` table stores only `symbol/kind/payload/color/label/group_id`
(`data/db.py:59–67`) — there is no `extend` column. The D12 dialog omits the control
(`ui/zone_settings_dialog.py:4–5`, `:54`) and pre-fills from `x1/y1/x2/y2`
(`docs/requirements/requirements.md:655`). Therefore zones created under prior behaviour load and
render unchanged; **no migration or persisted extend flag exists**.

- **Route:** none (informational verification).

## E5 — High-DPI claims are unexercised

**Verdict: CONFIRMED.** `docs/architecture.md:112` states "D6 cosmetic pens and D11 label placement
are device-pixel aware". A repo-wide search for `devicePixelRatio`, `QT_SCALE_FACTOR`, `dpr`,
`scale_factor` returns **no hits** in `tests/`, `ui/`, or `docs/`. The single `qapp` fixture
(`tests/conftest.py:91–98`) runs at the offscreen default devicePixelRatio 1.0. The body/`ViewBox`
math itself uses logical `vb.width()` (`ui/candlestick_item.py:118–125`), and the cosmetic pen claim
(`ui/candlestick_item.py:102`) is only valid if DPR awareness is actually exercised.

- **Observed:** no DPR != 1 test; DPI claims rest on assertions never run.
- **Expected:** at least one parametrized run at `QT_SCALE_FACTOR=2` covering D6 wick and D11 labels.
- **Root cause:** test harness sets a single scale factor.
- **Suggested direction:** Task Manager adds a parametrized/session-scoped DPR=2 test for the wick
  separation and label-in-bounds assertions.
- **Route:** TASK_MANAGER. **Linked task/defect:** T9, T15, T20.

## E6 — D14 double-click symbol change mid-drag tears down `DrawingOverlay`

**Verdict: CONFIRMED (missing test; same failure class as the fixed `InfiniteLine` bug).**
`_on_watchlist_row_double_clicked` (`ui/main_window.py:688–704`) calls `load_chart()`, which reaches
`drawing_overlay.set_data(...)` (`ui/main_window.py:452` / `:525`). `set_data`
(`ui/drawing_overlay.py:112–118`) clears the draft, resets `_drag`, and calls `_clear_all_items` →
`_detach_item` (`:216–235`), which defensively nulls `GraphicsScene.dragItem` when it matches the
removed item. So the shipped defensive clearing *may* already cover this new entry point, but no
test exercises it. The original defect and fix are documented at
`docs/debug/debug_log.md:19–43`; note that fix predates the D14 double-click path.

- **Observed:** D14 is a new teardown entry point into the same overlay; no test double-clicks mid-drag.
- **Expected:** a test that double-clicks a different symbol mid-drag and asserts no `RuntimeError`.
- **Root cause:** new symbol-change entry point re-enters `set_data` teardown without dedicated
  regression coverage; correctness was assumed from the earlier fix.
- **Suggested direction:** add the mid-drag double-click regression test; only if it fails does it
  become a BUILD bug. Do not assume the existing `dragItem` clearing suffices.
- **Route:** TASK_MANAGER. **Linked task/defect:** T18, T20.

## HA — Documentation drift

**Verdict: CONFIRMED.**
- `usage.md:166` claims "Full suite (269 tests, ~1.5s)". Measured on `09070e8`:
  `QT_QPA_PLATFORM=offscreen pytest` → **339 passed in 2.88s**; `docs/build/build_log.md:161`
  records 339 (~3.5s). `PENDING_IMPLEMENTATION_PLAN.md:364`, `:412`, `:458` all repeat "269 passed".
- `PENDING_IMPLEMENTATION_PLAN.md` marks only `Phase 10: Tests And Quality Gates ✅ COMPLETE`
  (`:462`); Phases 1–5 have **no completion marker** (the file uses no `[ ]` checkboxes at all),
  yet their target files exist: `ui/drawing_overlay.py`, `ibkr/market_depth.py`, `ibkr/orders.py`,
  `ui/active_trader_panel.py`, `ui/stop_loss_target_dialog.py`.
- The stale `tests/__pycache__/test_db_schema.cpython-311-*.pyc` with no source (see F1) is another
  artifact of drift.

- **Suggested direction:** update `usage.md` and `PENDING_IMPLEMENTATION_PLAN.md` counts/status;
  remove orphaned bytecode.
- **Route:** REQUIREMENTS. **Linked task/defect:** n/a.

## HB — Knowledge-graph integrity + D5/D8 contradiction

**Verdict: PARTIALLY CONFIRMED.**
- **D5/D8 contradiction: CONFIRMED (High).** `docs/requirements/requirements.md:378–406` still
  presents D5 as "clarified — Q17 (lower bound 1.0) confirmed", requiring **log** Y
  (`AC-D5.1` at `:396–397`), while D8 says it "revises D5's prior log decision" to **linear**
  (`:482–484`, `AC-D8.1` at `:512–514`). D5's section carries **no "superseded by D8" marker**, and
  the doc header still lists "volume log lower bound 1.0 — Q17" (`:13`). A literal D5 implementer
  ships the wrong axis. `architecture.md:25` and `plan.md:12` correctly mark D5 superseded — the
  contradiction is confined to `requirements.md`.
- **Graph health: PARTIALLY reproduced.** `graphify diagnose multigraph` on the committed
  `graphify-out/graph.json` reports **`self_loop_edges: 45`** (matches the reported 45) but also
  `dangling_endpoint_edges: 0` and `directed/undirected_same_endpoint_collapsed_edges: 0` — the
  reported 228 dangling and ~130 collapsed could **not** be reproduced. The health gate defined in
  the graphify skill runs against the raw extraction `.graphify_extract.json`, which is **not
  present** in `graphify-out/` (only the post-build graph remains). The post-build graph has already
  dropped those edges, so the raw numbers are unverifiable from committed artifacts.

- **Suggested direction:** Requirements Analyst marks the D5 section superseded-by-D8 (fix the header
  index too). Graph integrity is a tooling/user-housekeeping matter; re-run the graphify health gate
  on a fresh extraction if the 228/130 numbers matter.
- **Route:** REQUIREMENTS (D5/D8). **Linked task/defect:** n/a.

---

## Findings not fully verifiable

1. **HB graph numbers (228 dangling / ~130 collapsed):** not reproducible from the committed
   `graphify-out/graph.json` (reports 0/0); raw extraction absent. Only the 45 self-loops verified.
2. **F3 root-cause wording:** the "hard ceiling at 10M" is inaccurate — code falls back to 5M
   rounding above 10M. The concern (coarse >10M steps) is real; the premise as stated is not.
3. **HA "Phases 1–5 unchecked":** the file has no `[ ]` checkboxes at all; the accurate statement is
   that Phases 1–5 carry no completion marker while their files exist.

---

# Revision 2 review — Build ESC revision (T21–T31), 2026-09-28

**Scope reviewed:** `docs/build/build_log.md` (ends `Status: NEEDS_CODE_REVIEW`), `docs/build/failures.json`,
`docs/tasks/task-graph.json`, `docs/architecture.md`, `docs/plan.md`, `docs/requirements/requirements.md`,
existing `docs/code_review/escalations.md` (ESC-001…ESC-012), and the uncommitted Build changes in
`data/db.py`, `ui/chart_mouse_router.py`, `ui/chart_panel.py`, `ui/main_window.py`, and the tests.
Repo `286028a` (docs checkpoint) + uncommitted code changes. No live TWS was used — all runs were
`QT_QPA_PLATFORM=offscreen`.

**Independent test evidence (run by the reviewer, not taken from Build's report):**

- Full suite: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` →
  **`8 failed, 372 passed in 5.95s`**, matching Build's count exactly. The 8:
  `test_chart_crosshair.py::test_hover_inside_shows_lines_and_axis_chips`,
  `test_chart_dpi.py::test_wick_stays_1_device_px_and_body_clamped_at_dpr[dpr1]` and `[dpr2]`,
  `test_crosshair_chip_bounds.py::test_chip_visible_inside_right_edge` /
  `::test_chip_stays_inside_after_zoom` / `::test_long_price_and_edge_positions`,
  `test_drawing_labels.py::test_label_vs_label_bbox_no_intersection`,
  `test_volume_log.py::test_volume_zero_mapped_to_one`.
- New/modified per-task modules re-run green (45 passed):
  `test_chart_mouse_router.py`, `test_volume_linear.py`, `test_volume_ceiling.py`,
  `test_crosshair_axis_lane.py`, `test_db_schema.py`, `test_volume_toggle.py`,
  `test_d10_d13_integration.py`, `test_watchlist_d14_midrag.py`.

## A. Failure diagnosis (both blocked tasks — reproduced, then routed)

### R-01 — T25 `blocked`: D11 label bboxes overlap (code bug → BUILD)
Reproduced `tests/test_drawing_labels.py::test_label_vs_label_bbox_no_intersection` →
`1 failed, 4 passed`, `AssertionError: D11 label bounding boxes overlap: centre separation 15.0px <
label bbox height 23.0px`. Confirmed root cause: `ui/drawing_overlay.py::_update_inner_labels()`
(`:386–391`) enforces a fixed 15 px centre offset (`if last_y is not None and y - last_y < 15`), while
real `TextItem` scene bboxes are ~23 px tall (measured 48.06×23.00 and 48.20×23.00, `intersects()==True`).
AC-D11.4's normative clause ("bounding boxes MUST NOT overlap"; measurable `centerΔ >= bbox_height`) is
therefore unmet. **Classification `code_bug`** (the AC's `>= 15 px` parenthetical is the *existing*
threshold, but the binding clause is non-overlap). **Routed: BUILD (ESC-014).** Build's own diagnosis
was accepted as accurate; the fix is outside T25's `touches_files` (`ui/drawing_overlay.py`).

### R-02 — T29 `blocked`: D6 body clamp never fires (code bug → BUILD)
Reproduced `tests/test_chart_dpi.py` → `2 failed, 3 passed`; measured `body_device_px ≈ 0.53` (dpr1)
and `1.06` (dpr2) against `>= 4`. Confirmed root cause: `ui/chart_panel.py::_refresh_candles()` calls
`self.candlestick.set_data(...)` at `:831` **before** `vb.setRange(...)` at `:844`; the `>=4-device-px`
clamp in `ui/candlestick_item.py::_draw_candles()` (`:118–125`) reads `vb.viewRange()` **at generation
time**, when it is the default `[[-0.5, 0.5]]` (`px_per_sec ≈ 863`), so `min_w` never binds and the
stored `w = median_diff*0.325` survives the later real range. **Classification `code_bug`** — a
pre-existing ordering bug the new DPR coverage exposed (the clamp math is DPR-safe). **Routed: BUILD
(ESC-015).** Build's diagnosis accepted.

## B. Quality review of what passed (T21–T30)

- **T21 RouterMode** (`ui/chart_mouse_router.py`): implemented as a genuine single-valued state machine
  — intent helpers (`enter_zoom`/`enter_drawing`/`enter_alarm_placing`/`exit_to_idle`), guard-clause
  dispatch on `_active_mode`, RC-3 property reconciliation with defensive probes. Test suite is real
  (exercises live overlays, not only doubles) and non-tautological; the 5 preserved tests pass
  verbatim. **One consistency gap:** TR-4's required side effect "uncheck the draw combo" is missing
  (see R-07 below).
- **T22 volume nice generator**: `_volume_nice_max`/`_volume_nice_family` implement the pinned family
  correctly; tests assert real mappings and a monotonic/tight sweep. `_volume_nice_family()` is only
  used by tests (production re-implements the same loop) — minor duplication, nice-to-have, not worth
  an escalation. The T22 "fixed point" AC wording is a task-definition defect (R-06).
- **T23 live ceiling**: `_recompute_vol_max` (O(N) load/new-bar), `_ensure_volume_range` (only-widen,
  no write on non-crossing tick), `_widen_volume_for` (O(1) intra-bar), empty-load resets caches.
  `tests/test_volume_ceiling.py` is a strong, real test (the `setRange` spy genuinely proves O(1)
  only-widen). Correct.
- **T24 crosshair chip relocation**: lane reservation via a `TextItem` probe, left-anchor, right-edge
  guard, vertical clamp. Tests are real geometry assertions. Dock-open visibility independently
  verified — see C.
- **T26 DB dedupe**: exactly one `_init_schema`; `tests/test_db_schema.py` asserts the ten-table set
  and single-definition via AST. Good, real regression test.
- **T27 volume toggle**: label is exactly `Volume`, checkable, default visible, splitter restores.
  Stronger than before (axis hide/show + strict height direction). Good.
- **T28 D10+D13 integration**: real `MainWindow` test with no TWS; genuinely covers the ESC-005 gap.
- **T30 D14 mid-drag reset**: drives the real double-click path mid-drag, asserts no
  `RuntimeError`/`RuntimeWarning` and the router returns to `IDLE`; has a discrimination check. Good.
- **T29 DPI harness**: a genuine isolated-subprocess DPR probe (does not mutate the session qapp);
  the `dense_after_regen` figure is diagnostic-only and correctly not asserted. Good test design.
- **Test quality note (nice-to-have):** `tests/test_drawing_labels.py:67`
  `assert label.isVisible() or True` is vacuously true (asserts nothing). It should be folded into the
  T25 test-file update (noted in ESC-014). No test in the changed set is otherwise tautological or
  over-mocked; none was weakened to pass.

## C. Independent AC-D2.1 dock-open verification (A25) — **PASS**

Performed by the reviewer (not T24-T02): a real `MainWindow` (with `IBApiClient.connect` no-op) at
1400×800, 1100×700 and 900×650, both right docks (`Active Trader`, `Portfolio`) shown, real bars
loaded, crosshair moved over the plot, then the **window was grabbed to a `QImage`** and the pill
colour sampled.

| Size | chip visible | in lane (`x >= view_rect.right()`) | intersects dock | grey-pill pixels in chip rect | inside central |
|---|---|---|---|---|---|
| 1400×800 | yes | yes | no / no | 63.8 % (1176 px) | yes |
| 1100×700 | yes | yes | no / no | 67.7 % | yes |
| 900×650  | yes | yes | no / no | 67.7 % | yes |

The chip renders as a grey pill with white text at scene `x >= view_rect.right()`, is **actually
painted** (≈64–68 % of its rect is the `#4b5563` fill in the grabbed window), lies inside the central
widget, and does **not** intersect either open dock's `frameGeometry()`. **AC-D2.1 verified.** No
escalation.

## D. Escalation close-out (ESC-001…ESC-012)

Re-checked each open entry against what changed and re-verified the fix directly. Closed as
`addressed` (edited in place, with a `Verified:` line): **ESC-001, ESC-002, ESC-003, ESC-004,
ESC-005, ESC-006, ESC-007, ESC-008, ESC-009, ESC-010, ESC-012** (11 entries).
- ESC-001: one `_init_schema` (`:14`) + real `tests/test_db_schema.py` green.
- ESC-002: RouterMode state machine in `architecture.md` + `ui/chart_mouse_router.py`; T21 tests green.
- ESC-003/ESC-008: pinned family generator; 40–50M mapping and low end (`0→100`, `800→1000`) green.
- ESC-004: **AC-G.1** visual-reference gate present in `requirements.md`.
- ESC-005: `tests/test_d10_d13_integration.py` green.
- ESC-006: chip relocated to the lane (Q33); T24 tests + C above; chip-vs-label collision retired. The
  remaining label-vs-label overlap is a distinct new finding (ESC-014).
- ESC-007: O(1) live ceiling + timezone re-apply; `test_volume_ceiling.py` green.
- ESC-009: DPR-1/2 isolated coverage exists and runs; it exposed a real D6 bug (ESC-015), i.e. the
  coverage did its job.
- ESC-010: `test_watchlist_d14_midrag.py` green + TR-17 reset in `set_symbol()`.
- ESC-012: D5 marked superseded + header index corrected.

**ESC-011 left `open` (partially addressed).** DOC-3 (orphaned `.pyc` / missing source) is resolved by
ESC-001, and DOC-4 by ESC-012; but DOC-1 (test counts) and DOC-2 (phase completion markers) are **not**
applied — `usage.md:166` still reads "269 tests, ~1.5s", `PENDING_IMPLEMENTATION_PLAN.md:364/:412/:458`
still read "269 passed", and Phases 1–5 still carry no `✅ COMPLETE` marker. `requirements.md`
DOC-1..4 records these as root-level docs no pipeline agent owns (a recorded user/owner dependency), so
this escalation cannot be closed by an agent this pass. Left `open`; no re-diagnosis beyond the above.

## E. New findings and routing (details in `escalations.md`)

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-013 | T29 | BUILD | bug / blocking | candle picture generated before `setRange`; D6 clamp never fires |
| ESC-014 | T25 | BUILD | bug / blocking | label stacking 15 px < 23 px bbox height |
| ESC-015 | T22 | BUILD | gap / should-fix | `test_volume_log.py` stale 10k expectation (blocks T31) |
| ESC-016 | T24 | BUILD | consistency / should-fix | 4 stale inside-plot crosshair assertions (blocks T31) |
| ESC-017 | T21 | BUILD | consistency / should-fix | TR-4 "uncheck the draw combo" not implemented (stale combo) |
| ESC-018 | T22 | TASK_MANAGER | gap / nice-to-have | "each is a fixed point" AC predicate unachievable as worded |
| ESC-019 | T27 | PLAN | consistency / nice-to-have | stale `👁 Volume` prose in plan/architecture_proposal/plan_review |

**Routing notes / judgement calls:**
- **ESC-018 owner:** the "fixed point" predicate exists **only** in `docs/tasks/task-graph.json`
  (`:1256`, `:1270`, `:1298`); `requirements.md` and `architecture.md` D8 wording is consistent (grep
  confirmed no "fixed point" anywhere else in `docs/`). It is therefore a Task-Manager task-definition
  wording fix, **not** a requirements/plan gap — Build's own note and failures.json said
  "Task Manager/Plan/Requirements", and the evidence localises it to the Task Manager.
- **T28 layout note (failures.json index 6) — decided ACCEPTABLE as-is; no task raised.** The D13
  clamp `[150, min(floor(0.50×W), W−400)]` is implemented faithfully at the mandated points
  (`clamp_watchlist_width` for restore/`resizeEvent`), and AC-D13.1's drag-to-`max_w` scenario is met
  (T28-T01). The residual observations are real but non-blocking: (a) a *raw* dock-drag beyond `max_w`
  is bounded by Qt's central-widget `minimumSizeHint` (1716 px offscreen), not by the D13 clamp, so the
  `W−400` branch is never binding; (b) `watchlist_max_width()` reserves 400 px against the whole window
  and ignores right docks. Both are inherent in the AC's own formula, so correcting them would be a
  requirements/design change, not a Build bug. Recorded here for transparency; if the team wants it
  enforced on a raw drag, it should be a Requirements Analyst wording decision plus a Task Manager
  follow-up task. No escalation.
- **ESC-017 verification caveat:** the combo staleness is a code-reading finding (the router clears the
  overlay tool but no signal reaches `MainWindow.draw_combo`); I verified the code paths and the
  alarm-path contrast at `ui/main_window.py:672`, but did not build a focused failing test for it
  (T21's ACs do not cover the combo). Flagged `should-fix`; Build can confirm with a UI assertion.
- **Could-not-verify:** none of the two blocked failures were unverifiable (both reproduced exactly). The
  ESC-018 predicate is unachievable by construction (proved algebraically against the pinned formula),
  so it is a wording defect rather than a test failure to reproduce.

**Pipeline state for the Orchestrator:** open escalations remain (4 BUILD items block T31 via the full
suite: ESC-013/ESC-014/ESC-015/ESC-016; plus ESC-017, ESC-018, ESC-019 and the pre-existing ESC-011).
T31 remains unreachable until the blocked T25/T29 code fixes land and the two stale-test items are
corrected.

# Revision 3 review — rework round (ESC-013…ESC-017 + T25/T29 re-runs), 2026-09-28

**Scope reviewed:** `docs/build/build_log.md` (ends `Status: READY_FOR_REVIEW`, 36/36 done),
`docs/build/failures.json` (`blocked` empty; T25/T29 `resolved`; 1 `pending_routing` = ESC-011 residual),
`docs/tasks/task-graph.json`, `docs/architecture.md`, `docs/plan.md`, `docs/requirements/requirements.md`,
and the uncommitted rework changes in `ui/chart_panel.py`, `ui/drawing_overlay.py`, `ui/main_window.py`,
`tests/test_chart_crosshair.py`, `tests/test_crosshair_chip_bounds.py`, `tests/test_drawing_labels.py`,
`tests/test_volume_log.py`, and the new `tests/test_draw_combo_sync.py`.
Repo `952a083` + uncommitted changes. **No live TWS was used** — every run was `QT_QPA_PLATFORM=offscreen`.

## A. Independent verification of each rework fix (no reliance on Build's word)

- **ESC-013 / T32 (D6 body clamp ordering) — VERIFIED.** Read `ui/chart_panel.py::_refresh_candles()`:
  the `auto_range` branch now calls `vb.setRange(...)` (`:849`) **before** `self.candlestick.set_data(...)`
  (`:852`); the `else` branch (`:856–864`) regenerates the picture against the already-real range and
  still re-applies the cached volume ceiling; the empty-load case (`_bars` empty) is handled by the same
  `else`. Reviewer probe (offscreen, 900×600, 960×60 s bars) confirmed the clamp binds on **every** path:
  first load **4.004 device px**, `set_timezone(-5h)` **4.004 px**, non-auto `_refresh_candles()`
  **4.004 px**, empty load no error, symbol change returns the router to `IDLE`. Re-ran
  `tests/test_chart_dpi.py` → **5 passed** (dense body 4.004 px @DPR1 / 8.007 @DPR2; wick 1). No regression
  found on the intra-bar/reset paths.
- **ESC-014 / T33 (D11 measured-height stack) — VERIFIED.** `_update_inner_labels()` stacks by
  `offset = max(15.0, height, last_height)` with `height = _label_scene_height(item)` (measured
  `mapRectToScene(boundingRect()).height()`, falling back to `sceneBoundingRect()` then `0.0`) and clamps
  the whole box inside `view_rect`. Probe measured the two near-price labels at **separation 23.00 px ==
  measured bbox height** (was 15) with no intersection; a degenerate collapsed y-range raised no exception.
  `T25-T01` genuinely discriminates: it asserts `centerΔ >= max(bbox height)` and `not intersects()`, both
  false under the old 15 px offset (15 < 23) — non-tautological. The vacuous
  `assert label.isVisible() or True` was replaced with real visibility + right-edge containment
  (`tests/test_drawing_labels.py:69–73`). Re-ran `tests/test_drawing_labels.py` → **5 passed** (×3, no
  flakiness). `_label_scene_height` fallback path is defensive and returns 0.0 rather than raising — fine.
- **ESC-015 / T34 (`test_volume_log.py`) — VERIFIED, real and not merely looser.**
  `test_volume_zero_mapped_to_one` now asserts `y_range[1] == approx(_nice_volume_max(max_vol), rel=0.02)`
  and pins `_nice_volume_max(max_vol) == approx(1_500, rel=0.02)`; tolerance tightened (0.1 → 0.02). The
  old `approx(10_000, rel=0.1)` fails against the measured `1500.0`, and the pinned `== 1_500` fails if the
  family regresses to the removed 10k floor. Re-ran `tests/test_volume_log.py` → **3 passed**.
- **ESC-016 / T35 (stale crosshair assertions) — VERIFIED.** The four assertions now require the D2/Q33
  lane contract (`anchor=(0,0.5)`, scene `pos().x() >= view_rect.right()`, bbox inside
  `[view_right, view_right + axis('right').width()]`). Non-tautological: the old inside-plot behaviour
  (`anchor=(1,0.5)`, `pos().x() <= view_right-1`) fails both `>= view_right` and `anchor.x()==0`. Re-ran
  both files → **16 passed** (12 + 4); the pre-change baseline reproduced the exact 4 failures.
- **ESC-017 / T36 (draw-combo sync) — VERIFIED.** `ui/main_window.py` connects
  `drawing_overlay.mode_changed` → `_on_drawing_tool_mode_changed` → a `blockSignals`-guarded
  `_reset_draw_combo_to_cursor()`; the alarm-mode reset routes through the same helper. Re-entrancy is
  genuinely prevented: `_on_draw_tool_changed` is reachable only via `currentTextChanged`, which
  `blockSignals(True)` suppresses (`test_reset_does_not_emit_spurious_signal` asserts `seen == []`), and
  the helper early-returns when the combo already reads `"Cursor"`. Re-ran `tests/test_draw_combo_sync.py`
  → **3 passed** (zoom-cancels-draw, TR-17 symbol change via the real `load_chart()` path, no-spurious
  signal + alarm path intact). The legitimate user re-arm path works (`_arm` → `DRAWING`). No regression.
- **T29 (DPR harness isolation) — VERIFIED.** `tests/test_chart_dpi.py` runs the probe in an isolated
  `subprocess` (`python -c`) with its own `QT_SCALE_FACTOR`; `T29-T03` asserts the session `qapp`
  devicePixelRatio is unchanged and the probe printed no `ibapi`. Re-ran → **5 passed**; no session-qapp
  mutation.

## B. Quality review of what changed

- **Correctness/consistency vs `architecture.md`:** the rework matches the canonical D2/Q33 chip lane,
  D6 clamp, D11 label stacking, D8 family, and TR-4/TR-17 side effects. No deviation found in the changed
  code.
- **Tests:** none of the changed/added tests is tautological or over-mocked. `T25-T01`, `T36-T03`,
  `T34`, the four crosshair assertions, and `T29-T01` all fail against the pre-fix behaviour (checked by
  reading the assertions against the old geometry/values; the DPR and crosshair baselines were re-reproduced
  by Build and are consistent with the code). No assertion was weakened to pass.
- **`_label_scene_height` fallback + above-floor ratio bound:** the fallback is safe (0.0 → `max(15, …)`);
  `test_volume_linear.py::test_T22_T05` tight-coverage bound `nice/(max_vol*1.1) <= 2` above the `100`
  floor (`if nice > 100.0`) is a real, correctly-guarded assertion (only ever excludes floor-bound cases,
  never lets a loose ratio through).
- **NEW FINDING — ESC-020 (D9 volume width, `should-fix`, BUILD).** While verifying ESC-013 I found that
  the *same* generate-before-`setRange` ordering T32 fixed for the candle picture remains for the volume
  bar width: `w_vol` is computed from the price `ViewBox.viewRange()` at `ui/chart_panel.py:805–823`, and
  `volume_bars.setOpts(width=w_vol*2)` runs at `:831`, both **before** `vb.setRange(...)` at `:849`. Probe
  on a dense first load: candle body **4.004 device px** vs volume bar **0.517 device px** (39 data units
  vs the price body's 302); after one non-auto refresh the volume width jumps to **4.000 px**. This
  violates `AC-D9.1`/`AC-D9.2` ("volume bar width equals the price body width"; dense view "follow the same
  clamped `w`") and the architecture D9 row. `tests/test_volume_width.py::test_volume_width_dense_clamped`
  misses it (asserts only `vol_width > 10`, which 39 satisfies). Detailed in `escalations.md` ESC-020.

## C. Independent full-suite re-verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **383 passed, 0 failed,
  exit code 0** (`383 passed in 6.12s`; 383 collected = 383 passed, no skips/xfails). **Build's 383/0
  claim independently confirmed.**
- Targeted re-runs: `test_chart_dpi.py` 5, `test_drawing_labels.py` 5, `test_volume_log.py` 3,
  `test_chart_crosshair.py` 12, `test_crosshair_chip_bounds.py` 4, `test_draw_combo_sync.py` 3 → all pass.
- **No live TWS:** `grep -rnE "eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient\(|7496|7497|4001|4002" tests/`
  → **0 hits**; no bare (non-signal) socket `connect(` in `tests/`. Confirmed.

## D. Escalation close-out

Re-checked each entry against the live tree and re-verified directly, then flipped
`Status` → `addressed` in place with a `Verified:` line:
**ESC-013, ESC-014, ESC-015, ESC-016, ESC-017, ESC-018, ESC-019** (7 entries closed).
- ESC-018: `task-graph.json:1256` now reads "Fixture mappings (ESC-018)"; T22-T02/T22-T06 assert
  `input -> output` mappings + family membership; no "fixed point" remains in any AC/test (only in
  build/review history). T22 tests green (11).
- ESC-019: no eye glyph remains in any Plan-owned artifact (`docs/plan.md`, `plan_proposal.md`,
  `architecture_proposal.md`, `plan_review.md` all describe the text label `Volume`); remaining `👁` hits
  are only in `docs/build/**` and this log's history.
- **ESC-011 left open (`Status: ESCALATED_TO_REQUIREMENTS`), owner named.** The orphaned-`.pyc` and
  D5-index parts are resolved, but root-doc drift remains and no pipeline agent owns it:
  `usage.md:166` still reads "269 tests, ~1.5s"; `PENDING_IMPLEMENTATION_PLAN.md:364/:412/:458` still read
  "269 passed" (current suite is 383); Phases 1–5 still carry no `✅ COMPLETE` marker. Owner:
  **Requirements Analyst / repository owner (user)** — a recorded root-doc dependency, not a Build task.
  Not closed; no re-diagnosis beyond recording the residual.

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-020 | T13 (D9) | BUILD | bug / should-fix | volume bar width computed before `setRange` on the auto-range path; doesn't follow the clamped price `w` on first load (`AC-D9.1`/`AC-D9.2`); the dense width test is too weak to catch it |

**Pipeline state for the Orchestrator:** ESC-013…ESC-019 are closed. Open escalations remain:
**ESC-020 (BUILD)** and **ESC-011 (REQUIREMENTS/owner — residual root-doc drift)**. The suite is green
(383/0), so nothing blocks the pipeline; ESC-020 is a genuine but non-blocking D9 correctness defect.

Status: REVIEW_COMPLETE

# Revision 4 review — ESC-020 rework verification (T13), 2026-09-28

**Scope reviewed:** `docs/build/build_log.md` (ends `Status: READY_FOR_REVIEW`, 36/36 done),
`docs/build/failures.json` (`blocked` empty; T13/T25/T29 `reopened`→`resolved`; 1 `pending_routing` =
ESC-011 residual), `docs/tasks/task-graph.json`, `ui/chart_panel.py`, `tests/test_volume_width.py`, and
the existing escalations. Repo `952a083` + uncommitted Build output. **No live TWS was used** — every run
was `QT_QPA_PLATFORM=offscreen`. Independently verified against the live tree, not Build's report.

## A. Independent verification of ESC-020 / T13 (D9 volume width ordering) — **VERIFIED, CLOSED**

- **Ordering on every path (code read).** `ui/chart_panel.py::_refresh_candles()` now applies
  `vb.setRange(xRange=…, yRange=…, padding=0.03)` (`:827–828`) **before** the `w_vol` / `min_w_vol` block
  (`:838–854`) and before `volume_bars.setOpts(x=…, height=…, width=w_vol*2, …)` (`:858`); the candle
  picture is regenerated after (`:862`/`:870`). Because `w_vol` now reads the range *after* it is set,
  the clamp sees the final range on:
  - **first / auto-range load** — `vb.setRange` runs first; ✓
  - **non-auto / intra-bar refresh** (`update_last_bar`, `set_timezone`) — the x-range is unchanged, so
    it is already final; ✓
  - **empty load** (`_bars == []`) — `len(self._bars) > 1` false → `w_vol = 0.25`, no error; ✓
  - **symbol change** — routed through `update_chart(..., auto_range=True)`; ✓
  - **single-bar** — `w_vol = 0.25`, matching the candle's single-bar fallback. ✓
- **Reviewer probe (offscreen, 900×600, 960×60 s bars; own probe, not Build's).** First load:
  candle body **4.0036 device px** vs volume bar **4.0000 device px** (dense 301.730 vs 301.730 data units
  at the final range); non-dense 20×300 s: **17.364 vs 17.276 device px** (195 vs 195 data units — the
  ~0.5 % delta is the cosmetic-pen inflation in the candle picture bbox, not a real mismatch). The same
  figures hold after a non-auto `_refresh_candles()`, an intra-bar `update_last_bar`, `set_timezone(-5h)`
  and a symbol change. Empty load raised no exception (`width=0.5`). Pre-fix the volume bar was 0.517
  device px on first load; that is gone.
- **Strengthened test is real, not tautological (fail-before / pass-after proven).** Extracted HEAD
  `952a083` (pre-fix ordering: `volume_bars.setOpts` `:832` before `vb.setRange` `:844`) into a temp tree,
  dropped in the *strengthened* `tests/test_volume_width.py`, and ran it:
  `assert 39.0 == 301.73023255860653 ± 3.0173` → **1 failed, 1 passed** — exactly the pre-fix defect.
  Against the fixed working tree → **2 passed**. The dense assertion derives `expected_body` from the
  final applied range and compares it to `vol_width`, so it genuinely discriminates the ordering bug.
  Line 72 (`vol_width != 60*0.325*2`) and line 71 (`!= 0.6`) are real regression guards.
- **Regression of the shared ESC-013 candle fix: none.** `tests/test_chart_dpi.py` → **5 passed**
  (dense body 4.004 px @DPR1, wick 1), and `test_volume_linear.py` + `test_volume_log.py` +
  `test_volume_ceiling.py` + `test_volume_toggle.py` → **26 passed**. `ui/chart_panel.py` is shared by both
  fixes; the reorder did not disturb the candle ordering, the live ceiling, or the D10 toggle.
- **ESC-013…ESC-019 remain `addressed`.** Their `Status: addressed` entries are unchanged and the tests
  they cite still pass (DPI 5, drawing labels, volume log, crosshair, draw-combo sync, volume linear, and
  the Plan-owned docs contain no eye glyph). No re-diagnosis needed.

## B. Independent full-suite re-verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`383 passed in 6.31s`,
  0 failed, exit code 0** — Build's 383/0 claim independently confirmed.
- Revision modules in isolation (15 files incl. `test_volume_width.py`, `test_chart_dpi.py`,
  `test_volume_linear.py`, `test_volume_log.py`, `test_volume_ceiling.py`, `test_volume_toggle.py`,
  `test_drawing_labels.py`, `test_chart_crosshair.py`, `test_crosshair_chip_bounds.py`,
  `test_draw_combo_sync.py`, `test_db_schema.py`, `test_chart_mouse_router.py`,
  `test_crosshair_axis_lane.py`, `test_d10_d13_integration.py`, `test_watchlist_d14_midrag.py`) →
  **79 passed**.
- **No live TWS/order references:**
  `grep -rnE "eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient\(|7496|7497|4001|4002" tests/`
  → **0 hits**.

## C. Escalation close-out

- **ESC-020 → `addressed`** (edited in place, `Verified:` line added) — see A. Independently re-verified;
  the fix holds on every path and the strengthened test discriminates.
- **ESC-011 left `open` (`Status: ESCALATED_TO_REQUIREMENTS`), owner named.** Unchanged residual root-doc
  drift: `usage.md:166` still reads "269 tests, ~1.5s"; `PENDING_IMPLEMENTATION_PLAN.md:364/:412/:458`
  still read "269 passed" (current suite 383); Phases 1–5 carry no `✅ COMPLETE` marker. Owner:
  **Requirements Analyst / repository owner (user)** — a recorded root-doc dependency, no pipeline agent
  owns it, not a Build task. Not dispatchable; left open, no re-diagnosis beyond recording the residual.

## D. Quality review of the T13 change and the strengthened test

- The `_refresh_candles()` reorder is a pure sequencing fix plus a clarifying comment; it is consistent
  with `docs/architecture.md:40` ("`volume_bars.width = w*2` … sharing `w` guarantees vertical alignment
  including the dense 4px minimum") and `requirements.md` `AC-D9.1`/`AC-D9.2`. No deviation found.
- The strengthened dense test is non-tautological and non-over-mocked (proven fail-before). The
  non-dense test's scaled re-assertion (`:41`, `rel=1e-9`) is a *stricter* re-expression of `:39`, not a
  vacuous one — no action.
- **New finding — ESC-021 (`nice-to-have`, BUILD, test robustness).** The D9 tests compute the expected
  body width analytically in `_clamped_price_body_width()` (duplicating the production formula) instead of
  measuring the rendered `CandlestickItem` body. Demonstrated concretely: drifting only the candle
  half-width (`ui/candlestick_item.py:98` `0.325 → 0.30`, a real D9 misalignment) leaves
  `tests/test_volume_width.py` **2 passed**. Today's alignment does hold (probe equal), so this is a
  robustness gap that can miss candle-side formula drift, not a present defect. Detailed in
  `escalations.md` ESC-021.

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-021 | T13 (D9) | BUILD | gap / nice-to-have | D9 width test binds volume width to a re-derived formula, not the rendered candle body; candle-formula drift goes undetected |

**Pipeline state for the Orchestrator:** ESC-020 is **closed** (independently verified). Open escalations
remaining: **ESC-021 (BUILD, nice-to-have)** and **ESC-011 (REQUIREMENTS/owner — residual root-doc
drift)**. The suite is green (383/0); neither open item blocks the pipeline.

Status: REVIEW_COMPLETE

# Revision 5 review — ESC-021 rework verification (T13 test hardening), 2026-09-28

**Scope reviewed:** `docs/build/build_log.md` (ends `Status: READY_FOR_REVIEW`, 36/36 done),
`docs/build/failures.json` (`blocked` empty; T25/T29/T13×2 `reopened`→`resolved`; 1 `pending_routing` =
ESC-011 residual), `docs/tasks/task-graph.json` (T13 entry), the reworked `tests/test_volume_width.py`,
`tests/test_chart_dpi.py::body_geometry` (the measurement reference), `ui/candlestick_item.py` (`:98`,
`:118–125`) and `ui/chart_panel.py::_refresh_candles()` (`:805–874`). Repo `952a083` + uncommitted Build
output. **No live TWS was used** — every run was `QT_QPA_PLATFORM=offscreen`. Verified against the live
tree, not Build's report.

## A. Independent verification of ESC-021 / T13 — **VERIFIED, CLOSED**

- **Test now measures the rendered item, not a formula (code read).**
  `tests/test_volume_width.py` no longer derives the expected width analytically: the duplicated helper
  `_clamped_price_body_width()` is gone (grep: no references anywhere; the only `0.325`/`median_diff` hits
  left are the two explanatory docstring/comments), and both tests obtain the expected value from
  `_measured_body_width()` — `panel.candlestick.boundingRect()` (the recorded `QPicture` bbox) minus the
  timestamp span, exactly `tests/test_chart_dpi.py::body_geometry` (`:68–87`). `_px_per_sec()` derives the
  scale from the final `ViewBox.viewRange()`. The asserted quantity (`panel.volume_bars.opts['width']`,
  `:58`/`:88`) and the expected quantity (`panel.candlestick…`, `:36`) come from **different** sources, so
  the equality is genuinely independent and cannot be satisfied by construction.
- **Drift experiment re-run by the reviewer** (backup → edit → test → restore → hash-verify):
  - backed up `ui/candlestick_item.py` (sha256 `6eb4dc49…58ffb`), applied only
    `median_diff * 0.325 → 0.30` at `:98`, cleared all `__pycache__`;
  - ran `tests/test_volume_width.py` → **1 failed, 1 passed**; non-dense `T13-T01`
    `assert 195.0 == 180.0 ± 3.6` (the exact candle-side drift that left the *old* formula-mirror at
    **2 passed**), dense `T13-T02` passes as expected (the 4-px clamp fires on both sides);
  - restored from backup and re-verified the identical sha256 `6eb4dc49…58ffb` with
    `git status --short ui/candlestick_item.py` empty (clean vs HEAD), then re-ran the file → **2 passed**.
  - **Result: the ESC-021 gap is closed** — candle-side drift is now detected.
- **No assertion weakened or made tautological.** The dense 4-device-px checks survive
  (`measured_body * px_per_sec ≈ 4.0`, `vol_width * px_per_sec ≈ 4.0`), as do both real regressions
  (`!= 0.6`, `!= 39.0`). The dense tolerance stays `rel=0.02` and is still meaningful: it absorbs only the
  integer `QPicture` bbox quantisation (~1.0 data unit on non-dense 195; ~0.27 on dense 301.7), while the
  `39.0` unclamped regression is ~9.8 % away — far outside it. The drift run proves the equality is
  non-vacuous.
- **ESC-020 witness retained.** Build's re-simulation of the pre-fix ordering makes dense `T13-T02` fail
  `assert 39.0 == 302.0 ± 6.04`; I independently reproduced that pre-fix baseline on the wave-11 tree in
  Revision 4, and the corresponding assertions are unchanged in the current file.
- **ESC-013…ESC-020 remain `addressed`.** Re-read their entries: all still `Status: addressed`; the tests
  they cite (`test_chart_dpi` 5, `test_drawing_labels` 5, `test_volume_log` 3, crosshair 12+4,
  `test_draw_combo_sync` 3, `test_volume_linear` 11) still pass. No re-diagnosis needed.
- **No product change, no residue.** `ui/candlestick_item.py` sha256 `6eb4dc49…58ffb` and
  `ui/chart_panel.py` sha256 `f672ea9f…beff4` both match their pre-rework values; the only `M` on
  `ui/chart_panel.py` predates the rework (ESC-020's wave-11 edit), and `ui/candlestick_item.py` is clean
  vs HEAD.

## B. Independent full-suite re-verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`383 passed in 6.26s`,
  0 failed, exit code 0** — Build's 383/0 claim independently confirmed (Revision 4 reported 6.31s;
  same collection).
- Targeted spot-check `tests/test_volume_width.py tests/test_chart_dpi.py tests/test_chart_mouse_router.py`
  → **22 passed** (2 + 5 + 15).
- **No live TWS/order references:** `grep -rnE "eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient\(|7496|7497|4001|4002" tests/`
  → **0 hits**.

## C. Escalation close-out

- **ESC-021 → `addressed`** (edited in place, `Verified:` line added) — see A. Independently re-verified;
  the tests now bind to the rendered candle body and the candle-side drift is caught.
- **ESC-011 left `open` (`Status: ESCALATED_TO_REQUIREMENTS`), owner named.** Re-checked the live tree:
  `usage.md:166` still reads `# Full suite (269 tests, ~1.5s)`; `PENDING_IMPLEMENTATION_PLAN.md:364/:412/:458`
  still read `269 passed` (current suite **383**); `## Phase 1: …` through `## Phase 5: …` (`:69/:129/:172/:213/:243`)
  still carry **no** `✅ COMPLETE` marker (only Phases 6–10 do). The orphaned-bytecode part is resolved
  (`tests/__pycache__/test_db_schema*` gone; `tests/test_db_schema.py` present) and the D5-index part by
  ESC-012. Owner: **Requirements Analyst / repository owner (user)** — a recorded root-doc dependency
  (`requirements.md` DOC-1/DOC-2), not a Build task, not dispatchable by Build. Left open; no re-diagnosis
  beyond recording the residual.

## D. Quality review of the test change

- The reworked assertions express `AC-D9.1`/`AC-D9.2` and the `architecture.md` D9 row directly ("volume
  width == price body width, incl. the dense 4px minimum") and are now stronger than the formula-mirror
  they replace — the same measurement technique the DPR test already uses, so the two D9-adjacent suites
  share one trustworthy method.
- One documentation nuance, **not an escalation**: the module docstring (`:33–34`) and the tolerance
  comment still say `rel=0.02` "allows" the pen inflation, while the actual error `Δ` is the `QPicture`
  integer quantisation (~1.0 data unit). The observed 1.0-unit delta on the non-dense 195 case means the
  non-dense tolerance is effectively ~0.6 %, not 2 % margin over the measurement — tighter than the
  comment implies, so the comment understates rather than overstates robustness. Cosmetic; no action.
- No test in the changed set is tautological or over-mocked; none was weakened, skipped, or rewritten.

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | None. The reworked D9 test is real, discriminating, and independent; no new quality/consistency/security issue found. |

**Pipeline state for the Orchestrator:** ESC-021 is **closed** (independently verified). The only open
escalation remaining is **ESC-011 (REQUIREMENTS / repository owner — residual root-doc drift)**, which is
not a Build task and does not block anything. The build is complete (36/36 tasks done) and the suite is
green (**383 passed, 0 failed**).

Status: REVIEW_COMPLETE

# Revision 6 review — ESC-011 root-doc verification, 2026-09-28

**Scope reviewed:** the two root docs the owner fixed (`usage.md`, `PENDING_IMPLEMENTATION_PLAN.md`) and
the existing `docs/code_review/escalations.md`. **No Build output changed this cycle** — the suite is
unchanged (Build ends `Status: READY_FOR_REVIEW`, 36/36 done). Verified against the live tree, not any
agent's say-so. **No live TWS:** the suite run was `QT_QPA_PLATFORM=offscreen`.

## A. ESC-011 residual — independently verified as resolved

ESC-011's residual named exactly three things. I re-checked each on the live tree:

- **Stale `269` counts gone.** `grep -n "269" usage.md PENDING_IMPLEMENTATION_PLAN.md` → **0 hits** (exit 1;
  previously 1 line in `usage.md` + 3 lines in the plan). PASS.
- **`usage.md` states the current suite size.** `usage.md:166` now reads `# Full suite (383 tests, ~6s)`
  (was "269 tests, ~1.5s"). I independently re-measured the suite this pass:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`383 passed in 6.49s`, exit 0**
  — so the stated count **and** the stated order-of-magnitude timing are accurate. PASS.
- **All ten phases carry `✅ COMPLETE`.** `grep -nE "^#+ .*Phase [0-9]" PENDING_IMPLEMENTATION_PLAN.md` →
  Phases 1–10 at `:69/:129/:172/:213/:243/:282/:326/:368/:416/:462`, each ending `✅ COMPLETE` (previously
  only Phases 6–10). The `PENDING_IMPLEMENTATION_PLAN.md:364`/`:412`/`:458` figures now read **383 passed**.
  PASS.
- The two other ESC-011 sub-items remained resolved from earlier passes: the orphaned
  `tests/__pycache__/test_db_schema*` bytecode (ESC-001) and the D5-index drift (ESC-012).

**All three enumerated residual items check out → ESC-011 closed in place** (`Status: addressed` + a
`Verified:` line) in `escalations.md`.

## B. New finding — ESC-022 (`test_plan.md:76`), same drift class, outside ESC-011's scope

While sweeping the repo for any remaining stale suite figure I found one in a **third** root doc, which
ESC-011 never enumerated: `test_plan.md:76` (section `### 4.3 Run Full Test Suite (all tests)`) shows
`python -m pytest tests/ -v` with `# → 269 passed in ~1.5s (all phases)`. Current suite: **383 passed in
~6.5s** (re-measured above). The doc reads as a current living test plan, so the figure is present-tense
drift, not a historical snapshot. The same sweep found no other stale full-suite number: `usage.md` and
`PENDING_IMPLEMENTATION_PLAN.md` are correct (383), and `test_plan.md:149` ("All 98 GUI tests pass") refers
to the GUI subset, not the full suite, and is not asserted to be stale.

ESC-011's own scope is the three locations it named; those are fixed, so ESC-011 closes truthfully. This
new instance is therefore tracked as its own entry, **ESC-022**, routed `ESCALATED_TO_REQUIREMENTS`
(owner: repository owner / Requirements Analyst — a root doc no pipeline agent owns), severity
**nice-to-have** (documentation only; nothing blocks). Full detail in `escalations.md`.

## C. Escalation close-out

- **ESC-011 → `addressed`** (edited in place; `Verified:` line added) — see A. Independently verified; all
  enumerated residual items resolved.
- **ESC-013 … ESC-021 remain `addressed`, no change.** Re-read their status lines: every one still reads
  `Status: addressed` (grep for `**Status: ESCALATED`/`open` returns only the ESC-022 entry added this
  pass). No re-diagnosis needed; nothing relevant changed for them this cycle.
- **ESC-022 opened** (`ESCALATED_TO_REQUIREMENTS`, nice-to-have) — see B.

## D. Quality review

No product or test code changed this cycle, so there is nothing new to re-review against
`architecture.md`/`plan.md`/`requirements.md`. The two edited root docs are user-owned and outside the
pipeline; my only role was verification, which passed for every location ESC-011 named.

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-022 | n/a (root doc) | REQUIREMENTS | gap / nice-to-have | `test_plan.md:76` still advertises "269 passed in ~1.5s" (current suite 383); same drift class as ESC-011, outside its enumerated scope |

**Pipeline state for the Orchestrator:** ESC-011 is **closed** (independently verified). One open
escalation remains: **ESC-022 (REQUIREMENTS / repository owner — `test_plan.md:76` stale full-suite
figure)**, a documentation-only nice-to-have that blocks nothing. The build is complete (36/36 tasks done)
and the suite is green (**383 passed, 0 failed, exit 0**).

Status: REVIEW_COMPLETE

# Revision 7 review — ESC-022 verification (root-doc full-suite figure), 2026-09-28

**Scope reviewed:** the one open escalation, **ESC-022** (`test_plan.md:76` stale full-suite figure), the
owner's fix to that root doc, and the existing `docs/code_review/escalations.md`. **No Build output changed
this cycle** — Build ends `Status: READY_FOR_REVIEW`, 36/36 tasks done. Verified against the live tree, not
any agent's or the owner's say-so. **No live TWS** — the suite run was `QT_QPA_PLATFORM=offscreen`.

## A. ESC-022 — independently verified as resolved (closed in place)

- **The cited location now states the current figure.** `test_plan.md:76` (section
  `### 4.3 Run Full Test Suite (all tests)`) reads `# → 383 passed in ~6.5s (all phases)` — the stale
  `269 passed in ~1.5s` is gone.
- **Independently re-measured this pass.**
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`383 passed in 6.13s`**,
  exit 0 (383 collected = 383 passed, no skips/xfails). The published count is exact and the published
  order-of-magnitude timing matches.
- **Repo-root `*.md` sweep — no stale full-suite count remains.** `grep -rn "269"` over the tree now hits
  only pipeline history (`docs/code_review/**`, `docs/requirements/**`), never a root doc. Every root doc is
  either current or legitimately historical:
  - `test_plan.md:149`/`:159`/`:175` ("98 GUI tests") — the **GUI subset**, correctly not a full-suite count
    (as the ESC-022 entry itself flagged); `:151`'s `< 5s full suite runtime` is a stated CI target under
    Acceptance Criteria, not a present-tense measured output — not a count claim, so not treated as drift.
  - `usage.md:166` (`383 tests, ~6s`) — current; `PENDING_IMPLEMENTATION_PLAN.md:364`/`:412`/`:458` (383) —
    current.
  - `PENDING_IMPLEMENTATION_PLAN.md:322` ("Full suite: 254 passed") and `docs/debug/debug_log.md:48`
    ("Full pytest suite: 311 tests passed") are **historical snapshots inside dated phase/debug records**,
    not living present-tense figures — same category as ESC-011's resolved per-phase records. Not drift.
- **ESC-022 closed in place** (`Status: ESCALATED_TO_REQUIREMENTS` → `addressed`, with a `Verified:` line) —
  I confirmed it myself; the owner's statement alone would not have sufficed.

## B. No new findings

No product or test code changed this cycle, so there is nothing new to re-review against
`architecture.md`/`plan.md`/`requirements.md`. The only edited artifact is a user-owned root doc, outside the
pipeline; my role was verification, which passed.

## C. Escalation close-out — all entries closed

- **ESC-022 → `addressed`** — see A.
- **ESC-001…ESC-021 remain `addressed`, unchanged.** Grep over `escalations.md` confirms all 22 entries
  (`^## ESC-` = 22; `Status: addressed` = 22) now read `Status: addressed`; **no `Status: ESCALATED_*` and
  no `Status: open` remains.**

## D. Independent full-suite re-verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`383 passed in 6.13s`,
  0 failed, exit 0** — consistent with the previous passes' 383/0 and with the figure now published in
  `test_plan.md`.
- No live-TWS/order path was invoked (no TWS was started; all runs offscreen).

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | None. The ESC-022 root-doc drift is resolved and no other stale full-suite figure remains. |

**Pipeline state for the Orchestrator:** **zero open escalations** — ESC-001…ESC-022 are all `addressed`.
The build is complete (36/36 tasks done) and the suite is green (**383 passed, 0 failed, exit 0**).

Status: REVIEW_COMPLETE

# Revision 8 review — D16 historical-bar gap backfill (T37–T41), 2026-10-02

**Scope reviewed:** `docs/build/build_log.md` (Batch 10 / D16, ends `Status: READY_FOR_REVIEW`, 5/5 done),
`docs/build/failures.json` (`{"blocked": []}`), `docs/tasks/task-graph.json` (T37–T41),
`docs/requirements/requirements.md` (D16 / AC-D16.1–6 / A27–A32 / R22–R26 / DG21),
`docs/architecture.md` (D16 additions/§Codebase Summary), `docs/plan.md` (Phase 1–3, PA-D16-1…10), and the
uncommitted D16 output: `services/market_calendar.py`, `services/backfill_service.py`, `ui/main_window.py`,
`tests/test_market_calendar.py`, `tests/test_backfill_service.py`, `tests/test_history_backfill_loadpath.py`,
`tests/test_history_backfill.py`. Repo HEAD + uncommitted D16 changes. **No live TWS** — every run was
`QT_QPA_PLATFORM=offscreen`. Everything below was verified against the live tree, not Build's word.

## Verdict summary

| Finding | Linked task | Classification | Severity | Route |
|---|---|---|---|---|
| Calendar closes Dec 31 (year-end) when Jan 1 is Saturday — silent-hole risk | T37 (D16) | requirements_gap | should-fix | REQUIREMENTS (ESC-023) |
| Dropped/stalled connection mid-wave never finalises nor surfaces the shortfall | T39 (D16) | gap (robustness) | nice-to-have | BUILD (ESC-024) |

No task was `blocked`, so there is no failure diagnosis this pass. The D16 code matches its acceptance
criteria on the reported scenario; both findings are latent/narrow (year-end, transport edge).

## A. Failure diagnosis

None. `docs/build/failures.json` is `{"blocked": []}`; the D16 terminal state is 5/5 done, 0 blocked. No
failing test to reproduce.

## B. Quality review of the D16 batch (T37–T41)

**T37 — `services/market_calendar.py` (calendar).** The by-rule holiday set is complete (New Year, MLK,
Presidents', Good Friday via Meeus/Jones/Butcher Easter, Memorial, Juneteenth from 2022, Independence,
Labor, Thanksgiving, Christmas) and the `is_trading_day` adjacent-year union correctly catches an
observed New Year's on Dec 31 of the prior year. Good Friday, DST via `ZoneInfo`, and the `trading_days` /
`session_windows` boundaries all check out. **One correctness defect:** `_observed` applies the
Saturday→preceding-Friday shift to New Year's Day unconditionally, which is wrong for US equities (NYSE
Rule 7.2 year-end accounting exception) — see ESC-023. `session_windows` is part of the specified API and
is exercised only by tests (D16's planner does not consume it); not a defect.

**T38 — `services/backfill_service.py` (planner).** The DG21 judgment call is implemented correctly:
detection scans **trading-day presence from `min(cached_ts)`** to `now`, so the reported **internal** hole
is healed, not merely a tail gap after `MAX(ts)`; weekends/holidays never appear as missing; adjacent
missing trading days merge; empty cache → `[]`. `plan_requests` uses the pinned
`TIMEFRAME_CONFIG[duration]` chunk step, newest-chunk-first, with the UTC-hyphenated anchor and full
coverage of the span (`end − chunk_count·duration ≤ start`). Pure/Qt-free (verified by the isolated
subprocess tests). No defect.

**T39 — `ui/main_window.py` (orchestration).** Read line-by-line. The generation token +
`_history_req_ids`/`_history_req_generation` + exactly-once finalisation is sound: `_on_historical_bar` /
`_on_historical_data_end` reject non-member **and** stale-generation events (membership check first, then
generation), `_on_historical_data_end` discards then finalises only when the set is empty, and repeated
`end`/`error` events for an already-removed id are ignored — so no double save/render. `load_chart`
cancels + advances the generation before re-arming; `closeEvent` cancels + advances; `_on_error` drops a
failed member (so the wave can still empty), correlates the shortfall and **fabricates no bar**. The
empty-cache fallback stays a set-of-one; the current-cache branch issues no request. `req_historical_data`
is called with `useRTH=1`, but the manager's `effective_useRTH = 0 if extended_hours else useRTH` means
the Exthours toggle is respected (the ext-hours edge case is satisfied). **One robustness gap:** no
wave teardown / shortfall surfacing on `_on_disconnected` and no timeout — ESC-024.

**T40 — `tests/test_history_backfill.py`.** Real offscreen `MainWindow`, no TWS; the AC-D16.5 repro is
seeded and driven through the actual load path (not re-implemented). Strong, non-tautological assertions:
per-weekday counts equal to the true extended-session cadence (192), weekend/holiday absence, both panels
spanning the backfilled timestamps (`vol_x == candle_ts`, heights > 0), an uncompressed axis (`first_post
− last_pre > 3 days`), the six-timeframe × two-symbol chunking continuity (12 params), switch-mid-flight
isolation, and the empty-cache fallback. No assertion is weakened or over-mocked.

**T41 — verification gate.** `ui/chart_panel.py` and `ibkr/market_data.py` are byte-identical to HEAD
(reviewer re-ran `git diff HEAD --numstat` → empty), so the "both panels fixed solely by the continuous
`_bars` list" claim holds and `req_historical_data(endDateTime)` is unchanged.

**Build's flagged T38-T03 "self-correction" — reviewed, legitimate, not a weakening.** The worker replaced
its own newly-authored, physically-impossible assertion (that a Thu→Tue fetch window excludes the weekend)
with the real invariant (weekends are never *reported* as missing trading days). The current test
(`tests/test_backfill_service.py:166–182`) asserts the exact tail span, the exact covered trading days, and
weekend disjointness — stronger, not weaker. No AC was altered.

**Tests not tautological / no weak spots found.** Spot-checked the new D16 suites for vacuous assertions
(none: every asserted quantity is independent of the production value it checks) and for over-mocking (the
MainWindow tests monkeypatch only the socket and the `sed`-free managers, driving the real load path).

## C. Independent full-suite + D16 re-verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`482 passed in 8.96s`,
  0 failed, exit 0** — Build's 482/0 claim independently confirmed (383 pre-D16 baseline + 99 new D16).
- The four new D16 files in isolation → **99 passed** (`test_market_calendar` 34, `test_backfill_service`
  41, `test_history_backfill_loadpath` 7, `test_history_backfill` 17).
- **No live TWS / order transmission:** grep over `tests/` for
  `eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient(|7496|7497|4001|4002|connectAsync` → only
  the intentional no-op stubs; no bare socket `connect(`. Confirmed.
- Render path unchanged confirmed (see T41 above).

## D. Escalation close-out

- **No open escalations carried into this pass.** `docs/code_review/escalations.md` held 22 entries
  (ESC-001…ESC-022), **all `Status: addressed`** (verified: 22 `## ESC-` headings, 22 `addressed`, and no
  `Status: open` / `ESCALATED_*`). Nothing to re-verify or close; the prior verification stands.
- Two new D16 findings appended: **ESC-023 (REQUIREMENTS, should-fix)** and **ESC-024 (BUILD,
  nice-to-have)**.

## E. Non-escalation observations (recorded, no action required)

- **Dead code / stale state (quality, informational):** `ui/main_window.py::_ibkr_end_date` (`:75–82`) is
  never called anywhere (the D16 `_format_end_date` re-implements its format and the plan's PA-D16-5 cites
  it as "factored out"); it remains as dead code. Likewise `_current_req_id` is now write-only (set in
  `_register_history_request`/`load_chart`/`closeEvent`, never read) after D16 replaced the single-reqId
  filter with set membership. Neither affects behaviour; trivial cleanup only.
- **Anchor timezone (cannot verify offscreen; pre-existing + plan-pinned):** PA-D16-5 pins the
  `yyyyMMdd-HH:mm:ss` UTC anchor from the pre-existing `_ibkr_end_date`. IBKR's public docs only document
  the `YYYYMMDD HH:mm:ss TMZ` input form and do not state how a bare hyphenated timestamp is interpreted;
  offscreen tests cannot exercise real TWS parsing. The anchor sits at ET midnight (with wide chunk
  windows), so even a TZ mis-model would not drop a whole trading day; flagged only for awareness, not as a
  defect, and any change would be a Plan (PA-D16-5) decision.
- **Day-granularity detection is accepted scope, not a gap:** a *partial* within-day hole cannot be
  detected by design (PA-D16-1 / FI-D16-1), and an illiquid fully-empty day is surfaced as a shortfall
  rather than fabricated. This matches the documented, accepted trade-off; no escalation.

## F. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-023 | T37 (D16) | REQUIREMENTS | gap / should-fix | `_observed` closes the year-end Friday (Dec 31) when Jan 1 is Saturday; wrong for US equities (NYSE Rule 7.2 year-end exception) → a genuine hole there is treated as a closure and left silently unfilled (`AC-D16.1`/`AC-D16.4`) |
| ESC-024 | T39 (D16) | BUILD | gap / nice-to-have | a dropped connection (or a request that never ends) mid-wave never finalises and never surfaces the shortfall; no timeout/watchdog |

**Pipeline state for the Orchestrator:** the D16 batch is complete (5/5 done) and the suite is green
(**482 passed, 0 failed, exit 0**). Two new escalations are open: **ESC-023 (REQUIREMENTS, should-fix)** and
**ESC-024 (BUILD, nice-to-have)**. Neither blocks the pipeline — ESC-023 is latent (year-end) and requires a
requirements/AC correction before any code change; ESC-024 is a robustness edge. ESC-001…ESC-022 remain
`addressed`.

Status: REVIEW_COMPLETE

# Revision 9 review — D16 ESC-023 correction round (T37 rework + T42 regression gate), 2026-10-02

**Scope reviewed:** `docs/build/build_log.md` (Batch 10 / D16 ESC-023 rework round, ends
`Status: READY_FOR_REVIEW`, 6/6 done), `docs/build/failures.json` (`{"blocked": []}`),
`docs/tasks/task-graph.json` (T37 rework, T42), `docs/requirements/requirements.md` (D16 / `AC-D16.7` /
A33 / R27), `docs/code_review/escalations.md` (ESC-023, ESC-024), and the uncommitted D16 output:
`services/market_calendar.py`, `tests/test_market_calendar.py`, `services/backfill_service.py`,
`ui/main_window.py`, and the three D16 test files. HEAD `9c2fafa` + uncommitted D16 changes. **No live TWS**
— every run was `QT_QPA_PLATFORM=offscreen`. Everything below was verified against the live tree, not
Build's word.

## Verdict summary

| Finding | Linked task | Classification | Severity | Route |
|---|---|---|---|---|
| ESC-023 year-end calendar — **fix verified, closed** | T37 (D16) | requirements_gap → corrected | should-fix | REQUIREMENTS → **addressed** |
| ESC-024 dropped/stalled connection mid-wave — **re-routed** | T39 (D16) | task-set gap (no task + T42 constraint) | nice-to-have | **TASK_MANAGER** |

No task was `blocked`, so there is no failure diagnosis this pass.

## A. Re-verification of ESC-023 (independently reproduced on the live tree) — **PASS**

Reproduced each layer myself, not from Build's report:

- **Behaviour (live module, offscreen).** `is_trading_day` is **True** for `2021-12-31`, `2027-12-31`,
  `2032-12-31`, `2038-12-31` — all Fridays whose Jan 1 (2022/2028/2033/2039) is a Saturday. `2022-01-01`
  (Sat) is False; `2022-01-03` (Mon) is True. Sunday Jan 1 2023 is still observed `2023-01-02 is False`.
  Every other observed shift is unchanged: `2026-07-03` False, `2022-12-26` False, `2027-06-18` False;
  legal weekend dates `2026-07-04` / `2022-12-25` / `2027-06-19` all False. No substitute closure exists.
- **Code.** `services/market_calendar.py::_holidays_for_year()` (`:116–121`) adds a New Year's closure only
  when Jan 1 is **not** Saturday; `_observed()` is untouched, so the shift rule for every other holiday is
  byte-for-byte the same. The module is still pure/Qt-free (T37-T06 asserts this).
- **Requirements.** `AC-D16.7` (`:1233–1251`) states the NYSE Rule 7.2 year-end accounting-period
  exception and the four dates, with the unchanged-shift regression guards and the `AC-D16.1`/`AC-D16.4`
  consequence; A33 (`:1322`), R27 (`:1395`), the Status header (`:3`) and Journey 17 (`:298`) all carry it.
  The requirements gap ESC-023 named is genuinely closed.
- **Task graph.** T37's acceptance criterion 3 and `T37-T03` now require the four Dec-31 dates **True**,
  keep the four unchanged closures, and assert `2022-01-01` False / `2022-01-03` True; no assertion expects
  a Dec 31 closure. Matches `AC-D16.7` exactly.
- **Tests.** `tests/test_market_calendar.py::test_t37_t03_new_years_year_end_exception_keeps_dec31_open`
  (`:128–145`) asserts the corrected contract and the `date(2021,12,31)` entry was dropped from the
  weekend-legal loop. Independently re-ran `tests/test_market_calendar.py` -> **35 passed**. The corrected
  assertions are discriminating — they fail under the old unconditional Saturday->Friday shift, so this is
  not a weakened test.

**ESC-023 → `addressed`** (edited in place, `Verified:` line added).

## B. Re-evaluation of ESC-024 — **remains open; re-routed BUILD → TASK_MANAGER**

Re-read the live code (not Build's summary): `_on_disconnected` (`ui/main_window.py:392–396`) still only
updates the badge/status and disables the load button — it does **not** touch `_history_req_ids`,
`_history_req_generation`, or `_history_generation`, and there is no timeout/watchdog. So a mid-wave
transport drop or a request that never yields `end`/`error` still strands the wave: it never finalises and
the shortfall is never surfaced by the D16 mechanism — the exact case `AC-D16.4` forbids ("surfaced
explicitly — never a silent hole"). This is **not** accepted scope: no requirement, assumption, risk row,
AC, or task covers a silent peer (R22 covers pacing/shortfall from a *responding* peer; the switch/close
cancel path and `_on_error` require an event to arrive).

**Decision — keep open, route to TASK_MANAGER (not BUILD):** Build's deferral is correct and accepted (not a
Build defect). There is **no task** carrying ESC-024 (Task Manager did not reopen T39), and the current
graph's **T42-T02 requires `ui/main_window.py` unchanged** — so a fix there would fail T42's own gate by
construction. Build must not invent an AC/test; the missing piece is a Task-Manager-owned task/AC that
reconciles the fix with the T42 unchanged-consumer constraint (or a re-scoped T42), after which Build can
implement. Severity unchanged: **nice-to-have** (latent transport edge; the reported repro and the suite
are unaffected). Not closed — no fix exists, so there is nothing to verify. I did not fix it myself.

## C. D16 batch as a whole — still holds (no regression from the correction)

- **Full offscreen suite (reviewer-run):** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q`
  -> **`483 passed in 8.94s`, 0 failed, exit 0.** Decomposition independently re-collected:
  `test_market_calendar` 35 + `test_backfill_service` 41 + `test_history_backfill_loadpath` 7 +
  `test_history_backfill` 17 = **100 D16 tests**; 483 − 100 = **383**, the pre-D16 D1–D15 baseline. No
  D1–D15 or D16 (T37–T41) test regressed. Build's 483/0 claim confirmed.
- **Previously-flagged ibapi-mock tests — not reproducible (confirmed again):**
  `tests/test_history_backfill.py::test_t40_t05_switch_mid_flight_isolated` and
  `tests/test_history_backfill_loadpath.py::test_t39_t05_switch_and_close_cancel_all` -> **2 passed** in
  isolation and inside the full run. Consistent with the earlier transient test-DB-contention class; no
  `failures.json` entry. Build's and the T42 worker's non-reproducible finding holds.
- **Consumer/render path unchanged by the correction (T42-T02):** `ui/chart_panel.py` and
  `ibkr/market_data.py` are byte-identical to HEAD; `ui/main_window.py` is `M` only from the pre-existing
  T39 D16 addition (mtime/mtime ordering confirms it predates the correction); `services/backfill_service.py`
  consumes the unchanged `is_trading_day(value) -> bool` contract. Only the calendar pair postdates the
  rework. Confirmed.
- **No live TWS:** all runs offscreen; no connection/order path invoked.
- **Quality of the correction:** minimal, rule-scoped, pure (no new dependency, no schema, no consumer
  signature change); the test change is a genuine correction of a wrong assertion, not a weakening. No new
  quality/consistency/security issue found.

## D. Escalation close-out

- **ESC-023 → `addressed`** — see A (independently re-verified on the live tree).
- **ESC-024 → re-routed `ESCALATED_TO_BUILD` -> `ESCALATED_TO_TASK_MANAGER`** — see B (still open).
- **ESC-001…ESC-022 remain `addressed`.** Grep over `escalations.md`: every one still reads
  `Status: addressed`; nothing relevant changed for them this cycle.

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | None. The ESC-023 correction is correct, discriminating and green; no new quality, consistency, or security issue found. ESC-024 re-routed to Task Manager. |

**Pipeline state for the Orchestrator:** the ESC-023 correction round is complete (6/6 done) and the suite is
green (**483 passed, 0 failed, exit 0**). **ESC-023 is closed.** One open escalation remains: **ESC-024
(`ESCALATED_TO_TASK_MANAGER`, nice-to-have)** — a latent dropped/stalled-connection robustness edge with no
task and incompatible with the T42 unchanged-consumer constraint. It does **not** block the pipeline
(latent; suite green); routing it to Task Manager is the next step.

Status: REVIEW_COMPLETE

---

## Revision 10 review — ESC-024 rework round (T43)

- **Scope:** Task-Manager-reconciled **T43** (`ui/main_window.py`, new
  `tests/test_history_backfill_disconnect.py`) — the ESC-024 rework. Reviewed against the live tree
  (files read from disk; T43 module and full suite re-run by the reviewer), not Build's report. All runs
  `QT_QPA_PLATFORM=offscreen`; no live TWS. Graphify graph (`graphify-out/graph.json`) is **stale for the
  D16 modules** and does not contain T43's new symbols — per the graphify protocol this is stated
  explicitly and every finding was validated against the actual repository files (authoritative).
- **Task statuses read:** D16 round **7/7 done** (T37–T43), `failures.json` = `{"blocked": []}`,
  `build_log.md` terminal `Status: READY_FOR_REVIEW`.

### A. ESC-024 — independently reproduced (each of the 6 T43 ACs)

Reviewer probes (offscreen `MainWindow`, `IBApiClient.connect` no-op, `MarketDataManager` stubbed with a
seeded 10-present-day / 10-missing-day cache so `load_chart` issues a real **3-request** wave):

- **AC1 disconnect drain:** `[8000,8001,8002]` registered → `_on_disconnected()` → `cancel_historical_data`
  called for exactly that set, `_history_req_ids == set()`. `tests/test_history_backfill_disconnect.py`
  → **6 passed** in isolation (`-p no:cacheprovider`, 0.86s); Build's 6/6 claim confirmed.
- **AC2 generation advance / late events:** generation strictly increased; `_history_event_accepted(pre_drop)`
  `False`; late `_on_historical_bar` + `_on_historical_data_end` left `_pending_bars == []` and the finalise
  spy at exactly one call. No late contamination, no double finalise.
- **AC3 shortfall surfaced:** status bar `"<SYM> — backfill incomplete: 10 trading day(s) still missing
  (2026-10-19, …)"` + `"Historical backfill shortfall …"` WARNING; finalise ran once.
- **AC4 no fabricated bar:** post-drop cache timestamps == seeded set; no missing day in `_bars` or the
  volume `x`; `_pending_bars == []`.
- **AC5 watchdog:** `_on_history_wave_timeout()` (no drop) cancels all, empties the set, advances the
  generation, **disarms** the timer (probe: armed with `remainingTime ~29868 ms`; inactive after), surfaces
  the shortfall once, fabricates no bar.
- **AC6 no-op / double disconnect:** with a completed single-request wave, `_on_disconnected()` did not call
  `_finalize_history_wave`, did not raise, and set badge `"● Disconnected"` / status `"Disconnected from
  IBKR"`; two consecutive disconnects → one finalise (idempotent).

### B. Regression check — D16 batch + ESC-023 correction

- **Full offscreen suite (reviewer-run):** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q`
  → **`489 passed in 9.22s`, 0 failed, exit 0** (Build's 489/0 confirmed). The +6 over the ESC-023 round's
  483 is exactly T43's new module.
- **D16 modules in isolation:** `test_market_calendar` + `test_backfill_service` +
  `test_history_backfill_loadpath` + `test_history_backfill` + `test_history_backfill_disconnect`
  → **106 passed**.
- **ESC-023 correction still holds:** `is_trading_day` True for 2021-12-31 and 2027-12-31 (Jan 1 = Saturday),
  False for 2022-01-01 — the year-end exception is intact.
- **Worker's three flagged flaky tests — not reproducible (confirmed again):**
  `tests/test_history_backfill.py::test_t40_t05_switch_mid_flight_isolated`,
  `tests/test_history_backfill_loadpath.py::test_t39_t05_switch_and_close_cancel_all`, and
  `tests/test_watchlist_d14_midrag.py` → **5 passed** in isolation. Consistent with the shared on-disk
  SQLite test-DB contention class (`tests/conftest.py` seeds one DB at `tempfile.gettempdir()/…`); not a
  regression, not attributable to T43. Build's refutation is correct.
- **No live TWS introduced:** grep of the new test for `eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient(|connectAsync` → **0 hits**.

### C. Watchdog / QTimer lifecycle assessment

- **Arm/disarm symmetry** is correct on the functional paths: armed when `load_chart` issues a wave
  (`_arm_history_wave_watchdog`, restarting the single-shot timer each load), disarmed in
  `_finalize_history_wave` (line 763), on `load_chart` (line 497), and via the stranded path after a
  disconnect/timeout (finalise disarms). Double-arming is a stop-then-start, so no accumulation; the window
  holds exactly one `_history_wave_timer` (probe: `findChildren(QTimer)` count stable). No timer leak.
- **One genuine but non-blocking gap → ESC-025:** `closeEvent` cancels the wave but does **not** disarm the
  timer; the single-shot timer stays armed after `close()` (benign today because the empty-set guard makes
  the late fire a no-op). Separately, `_finalize_stranded_history_wave`'s `reason` argument is accepted but
  never used, so disconnect and timeout produce identical surfaced messages.

### D. Escalation close-out

- **ESC-024 → `addressed`** — independently re-verified above; entry edited in place.
- **ESC-025 (new)** — `ESCALATED_TO_BUILD`, quality / nice-to-have.
- ESC-001…ESC-023 remain `addressed` (unchanged; nothing relevant changed for them this cycle).

### E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-025 | T43 | BUILD | quality / nice-to-have | `closeEvent` leaves the watchdog QTimer armed (benign); `reason` param of `_finalize_stranded_history_wave` is dead, so timeout vs. disconnect is indistinguishable in diagnostics. |

**Pipeline state for the Orchestrator:** the ESC-024 rework round is complete (7/7 done) and the suite is
green (**489 passed, 0 failed, exit 0**). **ESC-024 is closed.** One open escalation remains: **ESC-025
(`ESCALATED_TO_BUILD`, nice-to-have)** — a diagnostics/tidiness item with no acceptance-criterion impact. It
does **not** block the pipeline (suite green, no functional defect); routing it to Build is the next step.

Status: REVIEW_COMPLETE

---

## Revision 11 review — ESC-025 rework round (T44)

- **Scope:** Build's ESC-025 rework — **T44** (`ui/main_window.py` + `tests/test_history_backfill_disconnect.py`);
  no task was `blocked` (`failures.json` = `{"blocked": []}`), so this is a quality review of what passed plus
  the ESC-025 close-out. Reviewed against the live tree (files read from disk; full suite and reviewer probes
  run by me), not Build's report. All runs `QT_QPA_PLATFORM=offscreen`; no live TWS. Graphify's committed
  graph (`graphify-out/graph.json`) is **stale for the D16 modules** and does not contain T43/T44's new
  symbols — stated explicitly per the graphify protocol; every finding was validated against the actual
  repository files (authoritative).
- **Task statuses read:** D16/ESC-025 round **8/8 done** (T37–T44), `failures.json` `{"blocked": []}`,
  `build_log.md` terminal `Status: READY_FOR_REVIEW`.

### A. ESC-025 — independently re-verified (both items) and closed

Reviewer probes (offscreen `MainWindow`, `IBApiClient.connect` no-op, `MarketDataManager` stubbed with the
T43/T44 seeding harness so `load_chart` issues a real **3-request** wave), not taken from Build's word:

- **Item 1 — closeEvent disarms the watchdog (arm/disarm symmetry).** `closeEvent` (`ui/main_window.py:1397`)
  calls `self._disarm_history_wave_watchdog()` before `_cancel_history_requests()` + `_history_generation += 1`.
  Probe: `_history_wave_timer.isActive()` **True** before `win.close()`, **False** after; cancelled set
  `{8000-ish}` equalled the in-flight reqId set exactly; `_history_req_ids == set()`; generation advanced.
  The disarm routes through the **same shared helper** every other wave-terminating path uses (finalise at
  `:777`, load_chart at `:502`, disconnect/timeout via the stranded path), satisfying T44-AC2's symmetry. A
  manual post-close `_on_history_wave_timeout()` ran `_finalize_history_wave` **0** times (empty-set guard
  remains; still benign).
- **Item 2 — `reason` is diagnostic-live; timeout vs disconnect distinguishable.** Same 3-request wave
  stranded two ways: timeout → status `"… backfill incomplete: 10 trading day(s) still missing
  (2026-10-19, …). [Historical backfill timed out]"` and WARNING `"Historical backfill shortfall … [Historical
  backfill timed out]"`; disconnect → the same shortfall with `[Disconnected from IBKR]`. The two differ only
  by the named cause, proving `reason` is read (stash `:434`, read+clear `:787–788`), no longer dead.
- **AC-D16.4/D16 wording preserved.** Both messages still contain `"incomplete"` and name a still-missing
  trading day; both WARNINGs still read `"Historical backfill shortfall"`. T43-T03/T43-T05 are retained
  verbatim and green.
- **Behaviour-neutral / no stale suffix leak.** `_history_stranded_reason` is cleared to `""` on every
  finalise path; a subsequent normal finalise produced a message with **no** bracket suffix
  (`" [" not in msg`) and the stash read back `''`. No bar fabricated: post-drop cache timestamps,
  `chart_panel._bars` and the volume `x` series equalled the seeded set; `_pending_bars == []`.
- **Tests:** `tests/test_history_backfill_disconnect.py` → **10 passed** (T44-T01…T44-T04 + retained
  T43-T01…T43-T06). All four T44 acceptance criteria independently verified.
- **ESC-025 → `addressed`** (edited in place, `Verified:` line added).

### B. Independent full-suite + D16 re-verification (no regression)

- **Full offscreen suite (reviewer-run):**
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`493 passed in 9.74s`,
  0 failed, exit 0** — Build's 493/0 claim independently confirmed. Composition: 489 (T43 terminal) + the
  net +4 T44 tests.
- **D16 modules in isolation:** `test_history_backfill_disconnect` + `test_market_calendar` +
  `test_backfill_service` + `test_history_backfill_loadpath` + `test_history_backfill` → **110 passed**
  (10 + 35 + 41 + 7 + 17).
- **ESC-023 fix still holds:** `is_trading_day` is **True** for `2021-12-31` and `2027-12-31` (Jan 1 = Sat),
  **False** for `2022-01-01`, **True** for `2022-01-03`.
- **ESC-024 fix still holds:** the T43 disconnect/watchdog tests (retained inside the 10) all pass —
  disconnect drains the wave, advances the generation, rejects late events, surfaces the shortfall once,
  fabricates no bar.
- **No live TWS introduced:** grep of the three new history-backfill test files for
  `eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient(|7496|7497|4001|4002|connectAsync` → **0 hits**.

### C. Quality review of the T44 change (the requested "no NEW finding" check)

- **Consistency with architecture/plan:** the change is a bounded extension of the existing D16 wave
  lifecycle (`docs/architecture.md#D16 additions/changes`) — no new design, no acceptance-criterion rewrite.
  The `reason` diagnostics suffix is behaviour-neutral and scoped to the shortfall/failed-request log records only.
- **Specific new-finding hunt — stale suffix cleared?** Yes: the stash is read-then-cleared before the
  branch, and an empty reason yields `cause == ""`, so the normal-path finalise is byte-for-byte the T43
  wording. Verified by probe, not by reading alone.
- **Edge cases:** (a) stranded finalise with an empty `reason` → no suffix (safe); (b) `_history_stranded_reason`
  never initialised in `__init__` → the finaliser uses `getattr(..., "")` so an unset attribute is safe, and
  the only writer is the stranded path; (c) post-close timer fire → no-op (empty-set guard). No unhandled edge.
- **No tautological/over-mocked/weakened test:** T44-T01 asserts a real arming/disarming transition
  (True→False); T44-T02 spies the **shared** helper and asserts `disarm_calls == [1]` (not merely "stopped");
  T44-T03 asserts the two causes genuinely differ while both retain the AC wording; T44-T04 asserts the
  cancelled set equals the in-flight set and runs finalise exactly once with no fabrication. None is vacuous.
- **Footprint:** the T44 diff is confined to `ui/main_window.py` (the `closeEvent` disarm, the
  `_history_stranded_reason` stash/read/clear, the cause suffix) + `tests/test_history_backfill_disconnect.py`.
  No file outside `touches_files` was modified. No footprint violation.

### D. Escalation close-out

- **ESC-025 → `addressed`** — see A.
- **ESC-001…ESC-024 remain `addressed`, unchanged** — re-read their status lines; nothing relevant changed
  for them this cycle. Grep over `escalations.md` now shows **27 entry headings, 25 `Status: addressed`,
  0 `Status: ESCALATED_*`, 0 `open`**. **Zero open escalations remain.**

### E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | None. The T44 change is correct, discriminating, behaviour-neutral and green; the watchdog is disarmed symmetrically on close and the stranded-wave reason is live. No new quality, consistency, or security issue found. |

**Pipeline state for the Orchestrator:** the ESC-025 rework round is complete (8/8 done) and the suite is
green (**493 passed, 0 failed, exit 0**). **ESC-025 is closed. No open escalations remain** — ESC-001…ESC-025
are all `addressed`. The pipeline can advance.

---

# Revision 11 review — Batch 11 (D17 watchlist live resize + D18 single right dock region) — 2026-10-03

**Reviewer:** Code Reviewer agent. **Scope:** `docs/build/build_log.md` Batch 11 (T45–T51, all `done`;
`failures.json.blocked` empty; one `pending_routing` routed to me), plus the one `pending_routing` item
`dock_layout_plan_below_minimum`. **Method:** the full offscreen suite re-run by the reviewer; the failing
pure helper reproduced directly; the T49 `MainWindow` workaround brute-forced over 4,340 input combos; the
D2 chip test, D17/D18 focused suites and the segfault minimal-repro re-run; the test diffs read to confirm
none was weakened. Nothing was fixed. Only `docs/code_review/` was written.

**Verdict: build is green and the D17/D18 behaviour is correct at the `MainWindow` layer, but there is ONE
genuine, independently reproduced correctness defect in a `done` task (`T45 ui/dock_layout.py::plan_dock_widths`).
It does not block any task (the T49 workaround covers the only production consumer), so it is a
`should-fix` routed to BUILD — not a build-stopping issue.**

### A. Build claims re-verified (independently, on the live tree)

- **Full offscreen suite green: CONFIRMED.** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q`
  → **562 passed, exit 0** on two consecutive reviewer runs; **no segfault**. The wave-7 report's "did not
  reproduce" is accurate.
- **Minimal segfault repro: CONFIRMED clean.** `… -q tests/test_history_backfill_disconnect.py tests/test_session_overlay.py`
  → **14 passed, exit 0** (report claimed 14/14). The latent crash is genuinely absent on this tree, consistent
  with the project-memory shared-SQLite/teardown-contention gotcha.
- **D17/D18 focused suites: CONFIRMED.** `test_dock_layout.py test_dock_widths_d17.py test_dock_d18_region.py
  test_dock_widths_d18_impl.py test_dock_widths_d18.py test_watchlist.py test_d10_d13_integration.py`
  → **76 passed, exit 0**.
- **D2 chip/dock non-overlap (AC-D2.1): CONFIRMED.** `tests/test_crosshair_axis_lane.py` → **5 passed**; the
  test (T24-T02) now resolves the single `"Active Trader"` region, asserts `"Portfolio" not in docks`, and
  asserts `chip_rect` does not intersect the region's `frameGeometry()` — a real assertion against the new
  shape, not a weakened one.
- **T50 addendum artifact (`tests/test_watchlist` ⇒ `watchlist_max_width` for `1400`, `900`, `1400`, `1200'n`):
  CONFIRMED** the report's below-minimum malformed case for `900 ⇒ 450` fell under chart minimum and is
  handled.
- **No test weakened: CONFIRMED.** `grep -E "pytest.mark.skip|pytest.mark.xfail|pytest.skip|deselect|--ignore"`
  over all seven D17/D18 test files → **0 hits**. All test diffs against HEAD are shape adaptations
  (`"Portfolio"`→`"Active Trader"`, `window_w`→`chart_area_w`) that *strengthen* (`test_watchlist.py` adds
  delegation cross-checks; `test_crosshair_axis_lane.py` still asserts non-overlap).
- **No new QSettings key (AC-D18.7): CONFIRMED.** The only `setValue` writing a width is
  `ui/watchlist_panel.py:71` (`watchlist/width`); the right region is in-memory only.
- **D17 "watchlist no longer stuck in full screen": CONFIRMED.** T47-T03 drives the drag hook
  (`_on_dock_splitter_moved`) directly with **no window resize** and asserts the overshoot is clamped to the
  cap and `resize_events == []` — i.e. the cap binds *during* the drag with no `resizeEvent`, which was the
  D17 root cause. `changeEvent(WindowStateChange)` covers the full-screen state entry (T49-T04/T50-T01).

### B. Finding — T45 `ui/dock_layout.py::plan_dock_widths` returns widths below a dock minimum (verified)

- **Id:** F1 · **Linked task:** T45 · **Category:** `bug` · **Root-cause classification:** `code_bug`
- **Severity:** `should-fix` (does not block any task; AC-D18.4/AC-D18.5 hold at the `MainWindow` layer via
  the T49 workaround, and only `MainWindow._plan_dock_widths` consumes the helper in production)
- **Evidence (reproduced by the reviewer, `ui/dock_layout.py:100–114`):**
  - `plan_dock_widths(750, 100000, 200) -> (350, 0)` — right width `0 < RIGHT_DOCK_MIN_WIDTH (200)`.
  - `plan_dock_widths(750, 200, 0) -> (175, 175)` — both widths below their minimums (`150`/`200`).
  - Coarse grid (chart_area 100..3000 step 50 × requests {0,200,400,700,100000}²) → **108/1475 below-minimum
    combinations** (Build's finer enumeration: 2158), matching the report.
  - Root cause: the `while left + right > budget:` loop decrements `left`/`right` (lines 105–114) with **no
    re-flooring** at `WATCHLIST_MIN_WIDTH`/`RIGHT_DOCK_MIN_WIDTH`, so once a dock's cap was already floored
    (line 89–90) it can be driven under its minimum. This directly contradicts the function's own docstring
    ("neither width ever drops below its dock minimum", lines 79–81) and T45's own AC-D18.4 ("never below
    the minimum").
- **Why the tests missed it (test gap, folded into the same route):** `tests/test_dock_layout.py`
  `test_T45_T06_one_side_over_budget` uses `(1200, 100000, 10)` — the over-budget side is the *left*, and at
  chart_area 1200 the result stays feasible, so the defect never fires. The one-sided over-budget case that
  starves the *other* dock (`750, 100000, 200`) is untested; `test_T45_T06_never_raises_and_integer_stable`
  asserts only `int`/stability, not the minimum. So T45's `done` was legitimate against its own tests.
- **T49 workaround — independently verified sound, but a workaround, not a fix:** `MainWindow._plan_dock_widths`
  (`ui/main_window.py:1055–1118`) floors each width and re-shrinks. Brute-forced by the reviewer over **4,340
  chart_area/request combos → 0 below-minimum results, 0 raises**, including the exact repro inputs. So
  AC-D18.4/AC-D18.5 are true *today* at the production layer. **But** the pure helper remains contract-violating:
  the repo now has two divergent sources of truth for the cross-clamp, and any future direct consumer of
  `plan_dock_widths` — or any removal of the T49 repair — silently reintroduces a below-minimum dock. Because
  the requirements/AC (AC-D18.4) and the architecture row (`docs/architecture.md:663`, "shrinks whichever
  dock is over budget … until `chart_area ≥ 400`") both specify the correct behaviour, this is a **code bug,
  not an AC/architecture gap** → route to **BUILD**.
- **Suggested direction (optional, for Build):** re-floor `left`/`right` at their minimums as the loop
  decretements (or restructure so the chart minimum yields before a dock minimum is crossed), then add a
  regression test for the one-sided over-budget case (`plan_dock_widths(750, 100000, 200)` and
  `(750, 200, 0)`); once the helper is correct, remove the T49 `MainWindow._plan_dock_widths` repair to
  restore the single source of truth. No AC or task-breakdown change is implied.

### C. Other quality checks (no findings)

- **Consistency with architecture/plan:** the single right region, the shared `_apply_dock_widths`, the
  chart-area denominator, the 40%/50% caps and the no-persistence rule all match `docs/architecture.md:546–691`
  and the D17/D18 requirements. No deviation found.
- **Edge cases:** `_chart_area_width()` falls back to the window width pre-show (no zero denominator);
  `_right_dock_available()` falls back to the watchlist-only rule when the region is hidden (keeps D17 tests
  true); the `_applying_dock_widths` re-entrancy guard and the >1px resize gate are both present and tested
  (T49-T07). The fixed-point loop is bounded at 24 iterations and converges because the cap fractions are < 1.
- **Error handling:** the new paths are wrapped in `try/except Exception: pass` — broad, but deliberate and
  consistent with the file's existing Qt-defensive style; it cannot hide an AC failure because the tests
  assert rendered geometry directly. Not raised as a finding.
- **Security:** no socket, no order transmission, no new persistence/secret surface. `T51-T03` claim verified
  by the D2/order tests and the no-live-TWS grep; nothing to flag.
- **Maintainability:** the T49 repair is documented in-code as a workaround for the tracked upstream defect,
  so it is discoverable (it is Finding F1's subject, not a hidden hack).

### D. Escalation close-out

- **ESC-001…ESC-025 remain `addressed`, unchanged** — re-read their status lines; nothing relevant changed
  for any of them this cycle. Grep over `escalations.md` shows **0 `open`, 0 stale `ESCALATED_*`** before this
  pass.
- **New escalation:** **ESC-026** (F1) → `Status: ESCALATED_TO_BUILD`.

### E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-026 | T45 | ESCALATED_TO_BUILD | `bug` / `should-fix` | `ui/dock_layout.py::plan_dock_widths` shrink loop can return a width below a dock minimum (`(750,100000,200)->(350,0)`); violates its own docstring + AC-D18.4. The T49 `MainWindow` workaround is verified sound but leaves a contract-violating pure helper. |

**Pipeline state for the Orchestrator:** Batch 11 (T45–T51) is **7/7 `done`**, `failures.json.blocked` is
empty, the full offscreen suite is **562 passed / 0 failed / exit 0** (no segfault), and D2 chip/dock
non-overlap, D17 full-screen drag enforcement and D18 full-screen visibility are all independently confirmed.
**One escalation (ESC-026, `should-fix`) is open and routed to BUILD** — the T45 helper should be fixed
properly and the T49 workaround removed, but nothing is blocked. ESC-001…ESC-025 remain `addressed`.

Status: REVIEW_COMPLETE

# Revision review — ESC-026 rework round (T52), 2026-10-03

**Scope reviewed:** `docs/build/build_log.md` (ends `Status: READY_FOR_REVIEW`; T52 `done`, terminal
consolidation), `docs/build/failures.json` (`blocked` empty; `dock_layout_plan_below_minimum` entry annotated
`status: resolved`), `docs/tasks/task-graph.json` (T52 entry), the changed files `ui/dock_layout.py`,
`tests/test_dock_layout.py`, `ui/main_window.py`, and the existing `escalations.md`. Repo `fd0bb0a8` +
uncommitted Batch-11/ESC-026 changes. **No live TWS was used** — every run was `QT_QPA_PLATFORM=offscreen`.
Verified against the live tree and my own probes, not Build's report.

## A. Independent verification of ESC-026 / T52 — **VERIFIED, CLOSED**

- **Witnesses fixed.** `plan_dock_widths(750, 100000, 200) -> (150, 200)` and
  `plan_dock_widths(750, 200, 0) -> (150, 200)`; each width `>=` its dock minimum. The pre-fix
  `(350, 0)` / `(175, 175)` are gone.
- **Grid clean.** My own coarse grid (chart_area 100..3000 step 50 × requests {0,200,400,700,100000}²) →
  **1475 total, 0 below-minimum, 0 raises** (was 108). I re-derived the pre-fix shrink loop **in-memory**
  (no repo edit) and reproduced exactly **108/1475** plus `(350,0)` / `(175,175)`, proving the T52-T01/T52-T02
  witnesses genuinely discriminate the defect (non-tautological, fail-before/pass-after).
- **Precedence preserved.** Infeasible `plan_dock_widths(400, 500, 500) == (150, 200)` (dock minimums win,
  chart minimum yields); feasible over-budget `(1000, 500, 400) == (200, 400)` and
  `(1000, 100000, 100000) == (200, 400)` both keep `chart_area - left - right >= CHART_MIN_WIDTH` (400).
- **T49 workaround genuinely removed.** `MainWindow._plan_dock_widths` (`ui/main_window.py:1055–1099`) now
  contains no re-floor / combined-shrink repair — it delegates to the pure `ui.dock_layout.plan_dock_widths`
  and iterates it to the post-resize fixed point (`S = chart_area + cur_left + cur_right`, ≤24 passes).
  `git diff` confirms the T49 repair block is gone; `ui/dock_layout.py` is the single source of truth again.
- **MainWindow path still enforces D18 cap + cross-clamp** (reviewer probe, offscreen, no TWS, 1600×900):
  over-cap drag → `right == 200 <= floor(0.40·chart_area)+1`; under-min drag → `right == RIGHT_DOCK_MIN_WIDTH`
  (200) and `watchlist == 150`; cross-clamp → `chart_area == 1716 >= 400` with `left=150 right=200`.
- **Displayed at `docs/code_review/escalations.md`: ESC-026 → `addressed`** (flipped in place with the
  `Verified:` line).

## B. Independent full-suite and regression re-verification

- Full offscreen suite, run **twice**:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **566 passed, 0 failed, exit 0**
  each run (`566 passed in 10.47s`). Build's 566/0 claim independently confirmed; 562 (wave-7 Batch-11
  terminal) + the net **+4** T52 tests = 566, consistent — no D1–D16/Batch-11 regression.
- `tests/test_dock_layout.py` → **40 passed** (T45-T01…T06 + T52-T01…T04). Retained Batch-11 D17/D18 set
  (`test_dock_widths_d18_impl`, `test_dock_widths_d18`, `test_dock_widths_d17`, `test_dock_d18_region`,
  `test_d10_d13_integration`, `test_watchlist`) → **40 passed**.

## C. Test-integrity / weakened-test check

- **No test weakened.** The T52 tests assert real geometry/values, not tautologies; T52-T02 explicitly rejects
  the pre-fix `(350, 0)` / `(175, 175)` results, and T52-T01 sweeps 1475 combinations. My in-memory pre-fix
  simulation reproduced the exact pre-fix outputs, so the assertions bind.
- **T45-T01 Qt-free subprocess guard still holds.** `tests/test_dock_layout.py` has **no module-scope Qt
  import**; the only `PyQt6` reference outside the guard's string assertions is the **function-local**
  `from PyQt6.QtCore import Qt` inside T52-T04 (line 303). I independently ran the isolated
  `import ui.dock_layout` interpreter → loads no PyQt6/pyqtgraph/PySide6, and the two T45-T01 tests pass in
  isolation. Placing T52-T04 in this file did **not** break the module's Qt-free property.

## D. `tests/__init__.py` collection gap — judged ACCEPTED environment noise (no escalation)

- **Observed:** `tests/test_watchlist_d14_midrag.py::test_T30_T03_existing_d14_noop_paths_unchanged`
  (`:263`) does `from tests.test_watchlist import ...`; the worker saw an order-dependent
  `ModuleNotFoundError: No module named 'tests.test_watchlist'` (the `tests/` dir has no `__init__.py`).
- **Could not reproduce:** the test passes in isolation (`1 passed`), the whole file passes (`3 passed`),
  reordered runs pass, `--import-mode=importlib` passes, and two full-suite runs pass (566/566).
- **Pre-existing, not a T52 regression:** the `from tests.test_watchlist import` line dates to `952a083`
  (Build revision 2 / T30); the only local diff to this file since is a Batch-11 `_RIGHT_DOCKS` constant
  change, unrelated to T52. It is also consistent with the project-memory shared-test-DB/teardown-contention
  gotcha. **No escalation raised** — it is a latent test-hygiene fragility (a bare namespace-package import
  that depends on rootdir/sys.path mechanics), not a product defect, and it blocks nothing.
  *(Informational note for the team: adding `tests/__init__.py` or switching `:263` to a rootdir-relative
  import would remove the latent fragility, but it is not a Build task and no AC covers it.)*

## E. Escalation close-out

- **ESC-026 → `addressed`** (in place, `Verified:` line added) — see A.
- **ESC-001…ESC-025 remain `addressed`** — nothing relevant changed for them this cycle; their fixed
  behaviours (D6/D9/D11/D2/chip lane/D16 calendar/disconnect/watchdog) are exercised by the green 566-test
  suite.

## F. New findings

None. No code bug, quality, consistency, security, or gap finding, and no task-breakdown / architecture /
requirements escalation surfaced this pass.

**Pipeline state for the Orchestrator:** ESC-026 is **closed** (independently verified). **No open
escalations remain** (ESC-001…ESC-026 all `addressed`); the suite is green (566/0). The pre-existing
`tests/__init__.py` collection gap is recorded as accepted environment noise (no route). Pipeline complete.

Status: REVIEW_COMPLETE

# Revision 12 review — Batch 13 (D19 toolbar scroll/elide wrapper; T53–T60) — 2026-10-05

**Reviewer:** Code Reviewer agent. **Scope:** `docs/build/build_log.md` (Batch 13 / D19, ends
`Status: NEEDS_CODE_REVIEW`; T53–T59 `done`, T60 `blocked`), `docs/build/failures.json` (`blocked` = T60 +
the 3 failing ids; 3 `pending_routing`), `docs/tasks/task-graph.json` (T53–T60),
`docs/requirements/requirements.md` (D19 / `AC-D19.1`–`AC-D19.7` / R33 / R34 / A37 / A38),
`docs/architecture.md` (D19 increment), the D19 worker logs (`docs/build/logs/T53.md`, `T60.md`), and the
uncommitted D19 output (`ui/main_window.py`, `tests/test_toolbar_scroll_d19.py`, and the five de-masked
harnesses). HEAD `5bd7c93` + uncommitted D19 changes. **No live TWS** — every run was
`QT_QPA_PLATFORM=offscreen`. Verified against the live tree and my own runs, not Build's report.

**Graphify:** `graphify-out/graph.json` exists (2366 nodes, refreshed 2026-10-05) but does **not** contain
the uncommitted D19 symbols (`MainToolbar`/`ToolbarScroll`). Per protocol this is stated explicitly, and
every finding below was validated against the actual repository files (authoritative).

## Verdict summary

| Finding | Linked task | Classification | Severity | Route |
|---|---|---|---|---|
| The 3 T60-T01 failing ids are **not reproducible** on a clean host and are **not D19 regressions** (D19 delta = 0; suite green 579/0 on my two runs) | T60 | environment / test-hygiene noise | accepted (documented) | none (see `escalations.md` ESC-027 for the T60 gate disposition) |
| `plan_dock_widths_single_call_underconvergence` retained observation | T56 / T45 | pre-existing fixed-point property; **no AC violated** | observation | none — confirmed acceptable |
| D19 wrapper + de-masking quality | T53–T59 | clean — consistent with `architecture.md`/`plan.md`; **no test weakened** | none | none |

## A. Failure diagnosis — the 3 blocked ids (T60-T01) — **environment noise, not D19 regressions**

Reproduced/refuted myself (not from Build's report). All runs `QT_QPA_PLATFORM=offscreen`,
`.venv/bin/python -m pytest -o addopts="" -q`:

- **Full offscreen suite, twice:** `579 passed in 12.68s` and `579 passed in 12.75s` — **0 failures**.
- The three cited ids in one invocation:
  `test_history_backfill.py::test_t40_t05_switch_mid_flight_isolated`,
  `test_history_backfill_loadpath.py::test_t39_t05_switch_and_close_cancel_all`,
  `test_watchlist_d14_midrag.py::test_T30_T03_existing_d14_noop_paths_unchanged` → **3 passed in 0.53s**.
- The two history files alone, **five** consecutive runs → `24 passed` each time (no `disk I/O error`,
  no `ibapi` `TypeError`).
- The watchlist test alone → `1 passed` under both the default import mode and `--import-mode=importlib`.

**Conclusion.** None of the three reproduces on the review host, so they cannot be D19 regressions and the
D19 delta is **0 new failures** (Build's `failures.json` proof of the same 3 ids at baseline `5bd7c93` is
consistent with this). They belong to the **project-memory intermittent shared-SQLite/teardown/collection
class** (and, for the watchlist id, a fragile bare namespace import), **not** a deterministic environment
failure. I did not reproduce Build's claim that they are "deterministic"; the evidence supports
*intermittent* noise. Either way they are **not in-scope code bugs** → documented as accepted, not routed.

**Build's stated diagnoses contain inaccuracies (recorded, not escalated):**

1. **`ibapi` version.** Build cites "ibapi 10.45.1"; the installed distribution is **`ibapi 9.81.1.post1`**
   (`.venv/lib/python3.11/site-packages/ibapi-9.81.1.post1.dist-info`). The underlying mechanism is real
   though: `EClient(None).serverVersion()` returns `None`, so any path comparing it (`client.py:379`
   `self.serverVersion() < MIN_SERVER_VER_...`) raises `TypeError`. The version number is simply wrong.
2. **`site-packages/tests/__init__.py` shadowing.** No such file exists: `find .venv/lib -path
   "*site-packages/tests/__init__.py"` → none; the local `tests/` has **no** `__init__.py`, and
   `import tests` from the repo root resolves to the local **namespace package**
   (`_NamespacePath(['…/NDThinkChart/tests'])`). The `ModuleNotFoundError` is a cwd/`sys.path` artefact of
   the bare `from tests.test_watchlist import` (`tests/test_watchlist_d14_midrag.py:263`), which only
   resolves because `python -m pytest` puts the cwd on `sys.path` — not an installed-package shadow.
3. **Broken venv console script (environment fact).** `.venv/bin/pytest` has a stale shebang pointing at
   the pre-rename path `/Users/aniket-desai/Documents/python_development/TOS_Charting/.venv/bin/python3`
   (directory no longer exists) → invoking it directly fails with `bad interpreter`. Only
   `.venv/bin/python -m pytest` works. This is a host/venv hygiene issue (the venv predates the repo
   rename), not a repo code defect — recorded for awareness; no route.

**T60 gate disposition.** T60 is `blocked` on `AC-D19.7`'s literal "zero failures" bar. On a clean run the
suite **is** green (579/0 twice), and the 3 ids are unrelated to D19 (different modules; D19 delta = 0), so
the regression the gate protects against does not exist. This is routed to **BUILD** as **ESC-027** so the
task-status owner can re-evaluate the gate — **without** weakening, skipping, deselecting, or rewriting any
test.

## B. Quality review of the D19 changes (T53–T59) — **clean; no test weakened**

**T53 wrapper (`ui/main_window.py:218–234`) — verified by code read and by running the D19 test:**
`QScrollArea` with `objectName("ToolbarScroll")`, `setFrameShape(QFrame.Shape.NoFrame)`,
`setWidgetResizable(False)`, `setHorizontalScrollBarPolicy(ScrollBarAsNeeded)`,
`setVerticalScrollBarPolicy(ScrollBarAlwaysOff)`, `setFixedHeight(36)`, `setWidget(toolbar)`; the toolbar
carries `objectName("MainToolbar")` and the trailing stretch + `conn_badge` stay inside the toolbar
(hence inside the scroll content). It is placed at central-layout item 0; `addToolBar` is never called.
`centralWidget().minimumSizeHint().width()` is 88 (`<= 750`). All four `T53-T01…T04` pass (4 passed). The
diff is minimal and exactly matches the task/architecture D19 mechanism.

**Guardrail respected:** `git diff` shows **no** change to `ui/dock_layout.py` (untouched), and the
`ui/main_window.py` diff does **not** touch `_apply_dock_widths`, `_chart_area_width`, or any cap constant
(`WATCHLIST_MIN_WIDTH`/`RIGHT_DOCK_MIN_WIDTH`/`WATCHLIST_CAP_FRACTION`/`CHART_MIN_WIDTH`) — grep over the
diff returns nothing. B6 (cap unchanged) holds.

**T54–T58 de-masking — no assertion weakened.** Read every diff:
- `test_dock_widths_d17.py` / `_d18.py` / `_d18_impl.py` / `test_dock_d18_region.py` / `test_dock_layout.py`:
  the `toolbar.hide()` masking and the legacy `centralWidget().layout().itemAt(0).widget()` toolbar lookup
  are removed; the toolbar is now resolved by its stable `MainToolbar` objectName. The **only** remaining
  `hide()` calls are the legitimate right-dock hides (`_RIGHT_DOCKS`), unrelated to the toolbar.
- Added guards are real and non-tautological: T54-T01/T55-T01/T56-T01/T57-T01/T58-T01 assert the toolbar
  `isVisible()` and source-check for masking via runtime-built needles or an **AST** walk (so the guard's
  own docstrings cannot self-match); T54-T02 (AC-D19.1 cap), T55-T02 (AC-D19.2), T55-T03 (AC-D19.3,
  parametrized) assert live geometry.
- **T56 / T49-T02** (the T53-induced harness debt): the fix replaces a single
  `_apply_dock_widths(None, 10**6)` with `_drive_right_to_cap(...)` (14 iterations) before the monotonic
  shrink sequence. The substantive assertions are retained verbatim — `width <= cap + 1`, monotonic
  `width <= prev`, and `width >= RIGHT_DOCK_MIN_WIDTH` / `== RIGHT_DOCK_MIN_WIDTH` on the below-min floor.
  This is a legitimate harness adaptation, **not** a weakening.
- No `pytest.mark.skip`/`xfail`/`pytest.skip`/`deselect`/`--ignore` anywhere in the six touched test files
  or `ui/main_window.py` (grep → 0 hits).

**Re-ran the de-masked modules myself:** `test_toolbar_scroll_d19` + the five harnesses +
`test_crosshair_axis_lane` → **91 passed in 4.24s**; each module in isolation →
4 / 10 / 20 / 8 / 4 / 40 passed. AC-D19.1/19.2/19.3/19.4/19.5/19.6 hold in a toolbar-visible window, and
T60-T02 (`test_crosshair_axis_lane`, 5/5) confirms AC-D2.1 against the single right region.

**T59 discrimination evidence (AC-D19.6) — plausible and consistent.** The build log records the pre-fix
worktree (`5bd7c93`) red / post-fix green (10 failed → 10 passed), with failures caused by the missing
`MainToolbar` objectName and the still-pinning toolbar. My independent post-fix runs are green; the
pre-fix red is the expected intermediate state R33 documents. No test was weakened to obtain it.

**Security / live-TWS:** no new socket/order surface; every `MainWindow`-booting test stubs
`IBApiClient.connect`; `placeOrder` remains product-code-only. Q9 holds.

## C. Retained observation `plan_dock_widths_single_call_underconvergence` — **confirmed acceptable, no escalation**

Build asked me to confirm whether the `_plan_dock_widths` single-call fixed-point under-convergence is
acceptable. I probed it directly (offscreen, toolbar visible):

- At window 1400 the iteration **oscillates** (integer/floor interaction: left flips 150↔154), so a
  driven-to-cap right dock settles at ~315–368 while `floor(0.40 × chart_area)` at the resulting chart
  area is ~369 — i.e. it lands **below** its cap. At 1600 and 1920 it converges to the cap (410/411, 502).
- **No acceptance criterion is violated.** Every right-dock criterion is an **upper bound**: `AC-D18.2`
  measurable is `width <= floor(0.40 × chart_area)`; `AC-D18.4` is "no resize leaves the width **above**
  the cap or below the minimum"; `AC-D19.2` is a visibility criterion. The watchlist — the one cap that
  must be *reached* (`AC-D19.1`, `abs(width - cap) <= 1`) — does reach it (T54-T02 passes). The
  under-convergence is a **pre-existing** property of the post-resize fixed-point iteration (the T52/ESC-026
  helper is correct; the iteration is bounded at 24 passes), **not** introduced by D19 and **not** a D19
  defect. The retained witness (T49-T02) is fixed by T56. **Confirmed acceptable; documented, not routed.**
  (A latent UX shortfall — a user may not be able to widen the right region fully to its cap on some window
  sizes — is recorded for awareness only; it violates no AC and no user report covers it.)

## D. Escalation close-out

- Re-read every entry in `docs/code_review/escalations.md`: **ESC-001…ESC-026 are all `Status: addressed`**
  (grep: 28 `## ESC-` headings incl. the two informational section headings, 26 `addressed`, and **zero**
  `Status: open` / `Status: ESCALATED_*`). Nothing relevant changed for them this cycle; no re-diagnosis
  needed.
- **One new escalation appended: ESC-027** (`ESCALATED_TO_BUILD`) — the T60 gate disposition (see A).

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-027 | T60 | ESCALATED_TO_BUILD | gap / should-fix | T60's `AC-D19.7` "zero failures" gate is blocked only by 3 non-reproducible environment-noise ids (unrelated to D19; delta = 0; suite green 579/0 on a clean run) — owner should re-evaluate the gate, without weakening any test. |

**Pipeline state for the Orchestrator:** Batch 13 (D19) T53–T59 are `done` and their output is **clean**
(wrapper correct, guardrails respected, no test weakened, de-masked criteria green). The 3 T60-T01 ids are
**environment noise, not D19 regressions** (independently: 579/0 twice, isolation green). **One escalation
is open — ESC-027 (`ESCALATED_TO_BUILD`, should-fix)** for the T60 gate disposition; the
`plan_dock_widths_single_call_underconvergence` observation is closed as acceptable. ESC-001…ESC-026 remain
`addressed`.

Status: REVIEW_COMPLETE

# Revision 13 review — Batch 13 (D19) ESC-027 re-evaluation verification (T60 gate), 2026-10-05

**Reviewer:** Code Reviewer agent. **Scope:** the Batch-13 (D19) ESC-027 re-evaluation round —
`docs/build/build_log.md` (Batch 13, now ends `Status: READY_FOR_REVIEW`), `docs/build/failures.json`
(`blocked` cleared; accepted `environment_noise_classification` + historical `pending_routing` retained),
`docs/tasks/task-graph.json` (T53–T60, all `done`), and the live tree (uncommitted D19 changes:
`ui/main_window.py` + five de-masked harnesses + new `tests/test_toolbar_scroll_d19.py`). **Method:** I
re-ran the full offscreen suite and the cited ids myself on a clean shared test DB; read the D19 test diffs
and file mtimes to confirm nothing was weakened; confirmed `ui/dock_layout.py` and the dock cap code are
untouched. Nothing was fixed. Only `docs/code_review/` was written. **No live TWS** — every run was
`QT_QPA_PLATFORM=offscreen`.

**Graphify:** `graphify-out/graph.json` exists (2366 nodes) and was queried for the dock-width symbols
(`plan_dock_widths`, `_apply_dock_widths`, `watchlist_max_width`, `right_dock_max_width`). It predates D19
(no `ToolbarScroll`/`MainToolbar` symbols) so it was used only for orientation; every finding below was
validated against the actual repository files (authoritative).

## A. T60 `AC-D19.7` gate — independently re-verified (clean run)

- **Full offscreen suite, clean shared DB, twice.** With
  `tempfile.gettempdir()/tos_charting_test.sqlite3` (+ `-wal`/`-shm`) removed:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q -p no:cacheprovider` →
  **579 passed / 0 failed / exit 0** (12.72s) and **579 passed / 0 failed / exit 0** (12.68s). The suite is
  literally green, so the "zero failures" gate holds.
- **The three previously-cited ids pass in one invocation** → **3 passed / exit 0** (0.55s):
  `tests/test_history_backfill.py::test_t40_t05_switch_mid_flight_isolated`,
  `tests/test_history_backfill_loadpath.py::test_t39_t05_switch_and_close_cancel_all`,
  `tests/test_watchlist_d14_midrag.py::test_T30_T03_existing_d14_noop_paths_unchanged`.
- **D19 delta = 0 new failures.** The green full suite includes every pre-existing D1–D18 test, so no
  pre-existing acceptance-criteria test regressed; the D19 tests are the only additions and all pass.
- **D19 focused suites green:** `test_toolbar_scroll_d19.py` + `test_crosshair_axis_lane.py` (T60-T02
  AC-D2.1) + the five de-masked harnesses → **91 passed / exit 0** (4.30s).
- **No live TWS/order transmission:** grep over `tests/` for
  `eConnect|placeOrder|reqHistoricalData|reqMktData|connectAsync|createClient|7496|7497|4001|4002` → only
  intentional no-op stubs/signals; no live socket/port.
- **Graph state:** `task-graph.json` T60 `status: done`; Batch-13 graph `{done: 8}` (T53–T60, 8/8);
  `build_log.md` terminal `Status: READY_FOR_REVIEW`; `failures.json.blocked` empty.

## B. No test weakened; dock-layout code and caps unchanged

- **No test weakened.** `grep -nE "pytest.mark.skip|pytest.mark.xfail|pytest.skip|deselect|--ignore|addopts"`
  over the D19-touched tests → **0 hits**. The D19 test edits **remove** `toolbar.hide()` masking and **add**
  the T53–T57 toolbar-visible guards; assertions are adapted/strengthened, none dropped or loosened
  (`test_T49_T02`'s single apply → `_drive_right_to_cap` iteration retains `width <= cap + 1`).
- **The re-evaluation did not edit any test.** File mtimes: D19 test files last written 12:27–12:35;
  `failures.json`/`build_log.md` written 12:57 — the ESC-027 round only re-ran the suite and updated the
  Build-owned artifacts.
- **`ui/dock_layout.py` unchanged:** `git diff HEAD -- ui/dock_layout.py` empty (sha256 `d1df116f…6d5af`,
  mtime 2026-10-03, predating D19).
- **`_apply_dock_widths` and cap constants unchanged:** the only D19 diff in `ui/main_window.py` is the
  toolbar `QScrollArea` wrapper (imports + `setObjectName("MainToolbar")` + the wrapper). `_apply_dock_widths`
  (`:1120`) and the caps are untouched — the `0.40`/`0.50` values remain the unchanged
  `watchlist_max_width`/`right_dock_max_width` helper calls.

## C. Escalation close-out

- **ESC-027 → `addressed`** (edited in place; `Verified:` line added) — see A/B. Independently re-verified:
  the clean-run gate holds (579/0 ×2), the three ids pass, the D19 focused suites are green, no test was
  weakened, and the dock-layout code/caps are unchanged.
- **ESC-001…ESC-026 remain `addressed`.** Grep over `escalations.md`: 27 `## ESC-` entry headings, **27
  `Status: addressed`, 0 `Status: ESCALATED_*`, 0 `Status: open`**. **Zero open escalations remain.**

## D. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | None. The T60 AC-D19.7 gate holds on clean runs (579/0 ×2), the D19 delta is zero, no test was weakened, and `ui/dock_layout.py`/`_apply_dock_widths`/caps are unchanged. No new quality, consistency, or security issue found. |

**Pipeline state for the Orchestrator:** Batch 13 (D19) is **8/8 done** (T53–T60), `failures.json.blocked`
empty, full offscreen suite green (**579 passed / 0 failed / exit 0**, twice). **ESC-027 is closed; no open
escalations remain** — ESC-001…ESC-027 are all `addressed`. The pipeline can advance (build complete).

Status: REVIEW_COMPLETE

# Revision 9 review — Batch 14 (D20 toolbar scrollbar lane, T61–T64), 2026-10-06

**Scope reviewed:** `docs/build/build_log.md` (ends `Status: READY_FOR_REVIEW`, Batch-14 graph 4/4 done),
`docs/build/failures.json` (`blocked` empty; no new `pending_routing`), `docs/tasks/task-graph.json`
(T61–T64), `docs/requirements/requirements.md` (D20 / `AC-D20.1`–`AC-D20.6` / A39–A40 / R35–R36 / the
recorded `AC-D19.4` supersession), `docs/architecture.md` (D20 increment), `docs/plan.md` (Phases 1–3),
`ui/main_window.py`, `ui/dock_layout.py`, `tests/test_toolbar_scroll_d19.py`, `tests/test_toolbar_d20.py`.
Working tree = commit `4d8952a` (D1–D19) + the uncommitted D20 changes (`ui/main_window.py`,
`tests/test_toolbar_scroll_d19.py` modified; `tests/test_toolbar_d20.py` new). **No live TWS** — every run
was `QT_QPA_PLATFORM=offscreen`. Nothing was fixed; only `docs/code_review/` was written.

**Graphify:** `graphify-out/graph.json` exists (2366 nodes). The D20 change is a two-line toolbar-height
edit in one file, fully readable directly; graphify was used for orientation and every claim below was
validated against the actual repository files (authoritative).

## A. Independent full-suite re-verification — GREEN

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`585 passed in 12.07s`,
  0 failed, exit 0** (585 collected = 585 passed; no skips/xfails/deselects). **Build's 585/0 claim
  independently confirmed.**
- `pytest.ini` `addopts = -q` only; `grep -rnE "pytest\.(skip|xfail)|@pytest\.mark\.(skip|xfail)|pytestmark|deselect"`
  over `tests/` → **0 hits**. Nothing skipped or deselected.

## B. D20 correctness — independently probed (my own offscreen probe, not Build's)

Real shown `MainWindow` (`IBApiClient.connect` monkeypatched to a no-op), probed at 2400×900 / 1200×700 /
900×650:

| check | wide 2400×900 | narrow 1200×700 | narrower 900×650 |
|---|---|---|---|
| `TOOLBAR_CONTENT_HEIGHT` | 36 | 36 | 36 |
| `toolbar.height()` (content row) | 36 | 36 | 36 |
| `wrapper.height()` (min==max) | 54 | 54 | 54 |
| `horizontalScrollBar().sizeHint().height()` | 18 | 18 | 18 |
| derived `wrapper == toolbar + sizeHint` | True | True | True |
| `hbar.isVisible()` | **False** | **True** | **True** |
| lane `mapTo(wrapper, QPoint(0,0)).y()` | 36 | 36 | 36 |
| lane `>= toolbar.height()` | True | True | True |
| `viewport.height() >= toolbar.height()` | True (54) | True (36) | True (36) |
| `centralWidget().minimumSizeHint().width() <= 750` | 88 ✓ | 88 ✓ | 88 ✓ |
| `chart_area >= CHART_MIN_WIDTH (400)` | 1968 ✓ | 768 ✓ | 538 ✓ |
| strip `< 60` | True | True | True |
| toolbar text-legibility issues | **0** | **0** | **0** |

The derived wrapper height (`TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()`), the
unchanged 36px content row, the reserved lane entirely below the content, the scrollbar as-needed, and
unclipped labels in **both** scrollbar states all hold. **No D20 correctness defect found.**

## C. No regression — D17/D18 unaffected (A40)

- Full suite green (A) includes every pre-existing D1–D19 test; no D1–D19 regression.
- `central min-hint 88 <= 750` and `chart_area >= 400` at every probed size (B) — only vertical space
  changed; the horizontal dock model is untouched.
- `git status --short ui/dock_layout.py` → **empty** (unchanged). The only `ui/main_window.py` diff is the
  toolbar block; `_apply_dock_widths` (`:1132`) and the cap constants (`CHART_MIN_WIDTH=400`,
  `WATCHLIST_MIN_WIDTH=150`, `RIGHT_DOCK_MIN_WIDTH=200`) are untouched. **No live TWS / order transmit:**
  `grep -rnE "eConnect|placeOrder|reqHistoricalData|reqMktData|IBApiClient\(|connectAsync|7496|7497|4001|4002"`
  over `tests/` → only intentional no-op stubs; no socket/port. **Q9 holds.**

## D. No test weakened — D19 lockstep is a strengthening, D20 assertions are non-vacuous

- **D19 lockstep (`tests/test_toolbar_scroll_d19.py::T53-T04`)** replaced the two stale 36px-container
  assertions (`wrapper.height() == 36`; `minimumHeight() == 36 and maximumHeight() == 36`) with the
  **derived relation** `wrapper.height() == toolbar.height() + wrapper.horizontalScrollBar().sizeHint().height()`
  plus `minimumHeight() == maximumHeight() == height()` and the content widget pinned at
  `TOOLBAR_CONTENT_HEIGHT (36)`. This is the sanctioned R36 lockstep: the assertion is **stronger**, not
  looser (it fails at the pre-fix 36px wrapper: `36 != 36 + 18`). `T53-T02`'s `toolbar.height() <= 40`
  bounds the **content row** (36px), not the container. `grep` confirms **no** stale
  `wrapper.height()==36`/`minimumHeight()/maximumHeight()==36` remains in any test.
- **D20 assertions non-vacuous — independently reproduced pre-fix RED.** I created my own temporary
  detached worktree at the pre-fix commit `4d8952a`, copied in the current `tests/test_toolbar_d20.py`
  and `tests/test_toolbar_scroll_d19.py`, and ran them:
  **`5 failed, 5 passed`** — exactly Build's T63 record:
  `test_T62_T01_labels_legible_scrollbar_shown` (lane/viewport assertion),
  `test_T62_T02_labels_legible_scrollbar_hidden` (`assert not rect.intersects(lane)`),
  `test_T62_T03_derived_height_and_reserved_lane` (ImportError: `TOOLBAR_CONTENT_HEIGHT` absent pre-fix),
  `test_T62_T04_scrollbar_as_needed_in_lane` (same ImportError), and
  `test_T53_T04_wrapper_mechanism` (same ImportError). The 5 that pass pre-fix are the unchanged-behaviour
  tests (`T62-T05`, `T62-T06`, `T53-T01`…`T53-T03`). The two lane-geometry tests (`T62-T01`/`T62-T02`)
  fail on the geometry itself (not merely the missing symbol), so the D20 assertions genuinely discriminate.
  The worktree was removed (`git worktree prune`); `git status --short` for the three files is unchanged
  (still the expected M/M/??).
- **Assertion form:** `grep -n "geometry(" tests/test_toolbar_d20.py` → hits only in docstrings; the lane
  checks use the mapped form `horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y() >= toolbar.height()`
  together with `viewport().height() >= toolbar.height()`. **`geometry()` is not used.** Confirmed.

## E. AC-D20.2 supersession — coherent

- `AC-D19.4`'s `<= ~40px` bound is **explicitly** marked superseded in `requirements.md:1662` (with the
  D19 reachability intent preserved, not superseded), and the header index (`:1`, `:54`, `:99`) records it.
  `AC-D20.2` (`:1744`) states the ~50–52px container / ~36px content target; `architecture.md:1048–1194`
  and `plan.md` Phases 1–2 (`RC-D20-1`, `RC-D20-2`, `RC-D20-3`) document that the `~50–52px` figure is the
  **macOS** value (extent ~16px → 52px) while the **offscreen** derived value is 54px.
- The tests assert the **derived relation** and `< 60px` (R35) and **explicitly do not** assert a literal
  `[50, 52]` bound (`tests/test_toolbar_d20.py:231`, `:250–251`). No literal bound anywhere.
- **Transparency note (non-escalating):** `AC-D20.2`'s measurable clause literally reads "the
  `ToolbarScroll` container height is `<= ~52px` and `>= ~50px`", and the offscreen container is 54px. I
  judged this coherent rather than a defect because the requirement uses `~` (approximate) and the
  macOS-vs-offscreen split is explicitly reconciled in `architecture.md`/`plan.md` and the task ACs, and
  because a literal 52px wrapper is documented as *wrong* (`RC-D20-1`: it would leave a 34px viewport and
  the lane would still overlap). The tests correctly avoid the literal bound. Recorded for the user; no
  escalation (routing a `~2px`-over-tilde wording tweak would not change any behaviour and the canonical
  artifacts already carry the reconciliation).

## F. Escalation close-out

- `grep -nE "Status: *(open|ESCALATED_TO_)" docs/code_review/escalations.md` → **NONE**. All ESC-001…ESC-027
  are `addressed`. **No open escalations remain; nothing to close out this pass.**

## G. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | **None.** D20 correctness verified by probe (derived height, 36px content row, reserved lane, as-needed, labels unclipped both states); full suite 585/0; no D1–D19 regression; D19 lockstep is a strengthening; D20 assertions non-vacuous (my own pre-fix worktree: 5 failed/5 passed); `dock_layout.py`/`_apply_dock_widths`/caps unchanged; no TWS/order transmit; supersession coherent. No quality, consistency, or security issue found. |

**Pipeline state for the Orchestrator:** Batch 14 (D20) is **4/4 done** (T61–T64), `failures.json.blocked`
empty, full offscreen suite green (**585 passed / 0 failed / exit 0**, independently re-run). **No open
escalations remain** — ESC-001…ESC-027 are all `addressed`. The pipeline can advance (build complete).

Status: REVIEW_COMPLETE

# Revision 12 review — Batch 15 (D21: 13 UI defects + VIS-D21), 2026-10-06

**Reviewer:** Code Reviewer agent. **Scope:** `docs/build/build_log.md` Batch 15 (D21-01…D21-18, all `done`;
`failures.json.blocked` empty; two `pending_routing` observations routed to me), `docs/tasks/task-graph.json`
(D21 graph), `docs/requirements/requirements.md` (D21 / `AC-D21.*` / `VIS-D21`), `docs/architecture.md`
(D21 increment, S3–S17), `docs/plan.md` (D21 phases), and the uncommitted D21 output (7 new test modules +
`ui/visual_conventions.py` + `services/time_collapse_service.py` + `ui/alarm_edit_dialog.py`). **Method:** the
full offscreen suite re-run by the reviewer; every D21 module and the D16/D1 + D8/ESC-007 lockstep modules
re-run in isolation; the D17/D18 focused modules re-run; every D21 source file read from disk; a reviewer
offscreen probe for the D21.2 floor edge; the test diffs read to confirm none was weakened. **No live TWS** —
every run was `QT_QPA_PLATFORM=offscreen`. Graphify's committed graph (`graphify-out/graph.json`, 2416 nodes) is
**stale for the D21 modules** — it contains no `ui/visual_conventions.py`, `services/time_collapse_service.py`,
`CollapsedDateAxis`, or any D21 symbol — so it is stated explicitly per the graphify protocol and every finding
was validated against the actual repository files (authoritative).

## Verdict summary

| # | Finding | Linked task | Classification | Severity | Route |
|---|---|---|---|---|---|
| F1 | D21.2 volume ceiling floor over-applies to a small **non-zero** visible max (`[0,100]` instead of `[0, 1.1×max]` for `0 < max ≤ ~90.9`) | D21-02 | consistency gap (`code_bug`) | nice-to-have | BUILD (ESC-028) |
| F2 | `task-graph.json` **D21-13-T05 description is inverted** vs `AC-D21.10.5` (the AC/implementation/test are all correct) | D21-13 | task-definition wording (`bad_task_breakdown`) | nice-to-have | TASK_MANAGER (ESC-029) |
| — | D21-16 out-of-footprint `ui/chart_panel.py` edit | D21-16 | verified acceptable (correct ownership boundary; no collision) | none | none |
| — | `_nice_volume_max` / `_volume_nice_family` are now test-only (dead production code, retained deliberately) | D21-02 | observation | none | none |

**Counts: BUILD 1 · TASK_MANAGER 1 · no-action 2.** Both routed items are `nice-to-have`; nothing blocks the
build, which is complete (18/18 done) and green (672/0).

## A. Independent full-suite + focused re-verification (reviewer-run, not Build's word)

- **Full offscreen suite** (clean shared test DB removed first, `-p no:cacheprovider`):
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **`672 passed in 12.13s`,
  0 failed, exit code 0**. Build's 672/0 claim independently confirmed; matches baseline `04397d9` = 585 +
  delta 87 = the D21 modules.
- **D21 modules in isolation** (`test_volume_d21`, `test_visual_conventions`, `test_toolbar_d21`,
  `test_watchlist_columns_d21`, `test_right_dock_d21`, `test_alarm_d21`, `test_time_collapse_d21`) →
  **87 passed**.
- **Lockstep modules in isolation** (`test_history_backfill`, `test_session_service`, `test_session_overlay`,
  `test_volume_linear`, `test_volume_log`, `test_volume_ceiling`) → **44 passed**.
- **D17/D18 focused modules** (`test_dock_layout`, `test_dock_widths_d17`, `test_dock_widths_d18`,
  `test_dock_widths_d18_impl`, `test_dock_d18_region`) → **82 passed**; `CHART_MIN_WIDTH = 400` unchanged.
- **No test weakened / skipped / deselected:** `grep -nE "pytest.mark.skip|pytest.mark.xfail|pytest.skip|deselect|--ignore"`
  over the 7 D21 modules → **0 hits**. The D16/D1 and D8/ESC-007 lockstep diffs are substantive re-expressions
  (display-x; `1.10 × visible max`), not weakenings — see C.
- **No live TWS / order transmission (Q9):**
  `grep -rnE "eConnect|placeOrder|reqMktData|reqHistoricalData|cancelOrder|reqPositions|reqAccountSummary|reqOpenOrders|connectAsync|7496|7497|4001|4002" tests/ --include='*.py'` → **0 hits**;
  every `MainWindow`-constructing test monkeypatches `IBApiClient.connect` to a no-op.
- **`ui/dock_layout.py` unchanged by D21** (`git status` clean; last commit `5bd7c93`). Cap constants unchanged:
  `CHART_MIN_WIDTH 400`, `WATCHLIST_MIN_WIDTH 150`, `RIGHT_DOCK_MIN_WIDTH 200`, `WATCHLIST_CAP_FRACTION 0.50`,
  `RIGHT_DOCK_CAP_FRACTION 0.40`. `_apply_dock_widths` gained only the D21.13 collapsed-region branch; the cap
  formula and `_plan_dock_widths` delegation are untouched.

## B. The 13 defects + VIS-D21 — each verified against the live code

- **D21.1 (volume Y min 0)** — `ui/chart_panel.py:378` `volume_plot.getViewBox().setLimits(yMin=0)`, applied
  immediately after the linear-`setLogMode` block. `tests/test_volume_d21.py` T01 drives `translateBy`/`scaleBy`/
  bounded `setRange` and asserts `viewRange()[1][0] >= 0` and no negative tick; T02 asserts the D8 all-zero
  `[0,100]` floor and reload re-application. Non-vacuous (pre-fix red reproduced by Build). **Holds.**
- **D21.2 (ceiling = 1.10 × visible max)** — `_recompute_visible_volume_range()` (chart_panel ~1129–1167) scans
  each plotted bar's **display-x** against the visible x-range, `ceiling = visible_max*1.1`, wired to
  `price_plot.getViewBox().sigXRangeChanged` (line 385) and re-run on bar updates. T01 asserts the ceiling follows
  zoom **both directions** (lowers on zoom-in — the superseded only-widen rule is gone); T03 asserts intra-bar
  growth widens. The only-widen path (`_vol_max`/`_ensure_volume_range`/`_widen_volume_for`) is removed.
  **Holds for realistic volumes** — one narrow deviation found for tiny non-zero max: **F1 / ESC-028**.
- **D21.3 (Ext Hours ↔ RTH label)** — `_ext_hours_label()` + relabel on construction and in `_on_ext_hours_toggled`
  **before** the `_current_symbol` guard. `test_toolbar_d21.py` T01/T02 assert immediate relabel, survival across a
  driven reload, and 80px fit. **Holds.**
- **D21.4 (collapse non-trading time, intraday only, `1 day` identity, RTH collapses non-RTH)** — pure
  `services/time_collapse_service.py` (`gap_is_non_trading` = `not session_windows(a + bar_period, b, ext_hours)`,
  the coverage-adjusted predicate; `1 day` identity; `Bar.ts` never mutated) + ChartPanel display-x x-model
  (`_collapse_map`, `_to_display`/`_to_ts`, `CollapsedDateAxis`, `_compute_plotted_indices` RTH filter). T14
  boundary tests run against the real `market_calendar.session_windows`; T15-T01/T02/T03/T04/T05 assert
  contiguity, `1 day` identity, a kept trading-session hole, RTH-only + D1 bands at collapsed positions, and the
  display-x volume ceiling; T16-T01…T04 assert the consumers (bands/drawings/alarm label/axis) map through the same
  map. **Holds.** D16 no-silent-hole: `self._bars` and every `Bar.ts` are untouched (display-only); the D16
  lockstep tests were re-expressed through `_to_display` preserving the span/non-zero-height intent. **Unchanged.**
- **D21.5 (watchlist configurable columns + persistence)** — `COLUMN_DEFS`/`ALL_FIELDS`/`DEFAULT_FIELDS` field-key
  model, `_row_data` field-identity binding, Symbol forced present, header context popup, `QSettings
  watchlist/columns` with sanitised restore. `test_watchlist_columns_d21.py` T01–T05 assert the popup, the exact
  7-field addable set, Symbol non-removable, field binding after reorder + D14 still resolving, and persistence.
  **Holds.**
- **D21.6 (volume pane ≥ 360px, ~200px price floor)** — `VOLUME_PANE_MAX_HEIGHT = 480`,
  `PRICE_PANE_MIN_HEIGHT = 200`, `volume_plot.setMaximumHeight(480)`, `price_plot.setMinimumHeight(200)`,
  oscillator cap unchanged at 120. T01/T02/T03 assert volume ≥ 360 (and ≤ 480), price ≥ 200 in a tall window,
  price-minimum precedence in a short window, and oscillator/hide-show unaffected. **Holds.**
- **D21.7 (toolbar active highlight)** — `apply_toolbar_stylesheet` (`#MainToolbar QPushButton:checked`) +
  `set_button_active` around the Studies/Alarms dialogs. T01 renders each checkable toggle and counts the
  `#1f6feb` fill; T02 renders the popup buttons inside/after `exec` and after scrolling the D19 wrapper.
  **Holds.**
- **D21.8 (Alarm-Mode highlight + persistent message)** — `alarm_mode_btn` gets the `:checked` highlight;
  `_on_alarm_mode_toggled` shows `ALARM_MODE_STATUS_MESSAGE` with **no timeout**, and
  `_clear_alarm_mode_status()` (guarded on `currentMessage()`) clears it on every exit path (button off, alarm
  placed, drawing tool selected). T01/T02/T03 assert the highlight, `showMessage(msg, 0)` (spy), persistence past
  4 s, and all three exit paths + a later message getting through. **Holds.**
- **D21.9 (per-row alarm Edit)** — `ui/alarm_edit_dialog.py` (`AlarmStore.update(id, price=…, direction=…,
  sound=…, note=…)`, never touching `active`/`triggered`/`triggered_at`), `alarm_dialog.py` 7-column table with a
  right-end `Edit` button and a stretched Note column. T01–T04 assert the right-end button, the stretched Note,
  Save/Cancel, and a triggered alarm keeping `active`/`triggered`/`triggered_at` + the overlay reflecting the new
  price. **Holds.**
- **D21.10 (smart alarm setup)** — `show_alarm_preview`/`update_alarm_preview`/`hide_alarm_preview` (yellow dashed
  non-movable `InfiniteLine`, panel-owned so `set_alarms` never removes it), wired **only** on the chart-click
  path `_on_alarm_create_requested` (with a `finally` removal and `price_input.valueChanged` live-follow), and
  `AlarmDialog.default_condition` applied **only at construction**. T01–T06 assert prefill, the yellow dashed
  visible line, live follow, remove-on-close + replace-on-Add, the on-open default (AC), and no preview on the
  Alarms-button path. **Holds** — see F2 for the task-graph wording.
- **D21.11 (single Watchlist label as toggle)** — duplicate `QDockWidget` title deleted (`setWindowTitle("")`),
  `setTitleBarWidget(header_bar)` with a checkable `DiagonalStrikeButton("Watchlist")`. T01 asserts exactly one
  visible label across the window, T02 the collapsed body + struck visible button, T03 the collapsed button +
  preserved title-bar drag/float + the D17/D18 width model. **Holds.**
- **D21.12 (Volume button strike when hidden)** — `_volume_toggle` is a `DiagonalStrikeButton` (checked ↔ shown ↔
  unstruck). T01/T02 assert the strike iff hidden, D10 placement, axis hide/show, splitter/price round-trip, and
  clickability while struck. **Holds.**
- **D21.13 (right-dock toggles + collapse)** — `Active Trader` = right-dock title-bar button, `Account Summary` =
  portfolio `summary_label` button; `_sync_right_dock_collapse` relaxes the minimum to
  `_right_dock_collapsed_min_width` and pins the dock via `_resize_docks_guarded` when both hidden, restoring
  `RIGHT_DOCK_MIN_WIDTH` + the cross-clamp otherwise; `_apply_dock_widths` treats a collapsed region as hidden;
  `_on_dom_toggled` stays whole-region. T01–T05 assert the mappings, in-height collapse + other-expands,
  horizontal collapse with the chart minimum held, the strike, and the DOM/cross-clamp behaviour. **Holds.**
- **VIS-D21 (defined once, referenced)** — `ui/visual_conventions.py` is the single source: `DiagonalStrikeButton`
  (`VIS-D21.1`) and `VIS_D21_2_STYLESHEET`/`set_button_active`/`apply_toolbar_stylesheet` (`VIS-D21.2`). Grep
  confirms the accent colours (`#1f6feb`/`#58a6ff`) and the `#MainToolbar QPushButton` selectors exist **only** in
  that module; D21.7/8 (main_window), D21.11 (watchlist), D21.12 (volume), D21.13 (right dock) all import/reference
  it. **No duplication. Holds.**

## C. Lockstep updates preserve substantive intent (no test weakened)

- **D16/D1 lockstep (`tests/test_history_backfill.py`)** — the two raw-`Bar.ts` assertions
  (`test_t40_t02...` and `test_t40_t06...`) now compare the rendered `candlestick._raw_data` x / `volume_bars`
  x to `panel._to_display(b.ts)`, and the span + non-zero-height checks were re-expressed in display-x
  (`span_x`, `index = {x: i …}`). This preserves the AC-D16.2 intent (both panels span the backfilled span with
  non-zero heights) under the D21.4 display-x contract; nothing was dropped or loosened.
- **D8/ESC-007 volume lockstep (`test_volume_linear.py`, `test_volume_log.py`, `test_volume_ceiling.py`)** — the
  panel view-range assertions were re-expressed as `max_vol * 1.1` (the D21.2 rule) with the concrete values
  re-pinned (`1_100`), and `test_volume_ceiling.py` T23-T03 still proves the O(1)-ish no-write-on-non-crossing
  behaviour with a `setRange` spy. `_nice_volume_max` is retained only as the pinned-family fixture and exercised
  directly. These are substantive re-expressions, not weakenings.
- **Q8 non-vacuity** — Build's D21-17 evidence (all 7 new modules ERROR/fail on the pre-fix tree `04397d9` because
  the D21 symbols do not exist, and 10 changed lockstep assertions fail; all green post-fix) is consistent with the
  modules importing D21-only symbols (`PRICE_PANE_MIN_HEIGHT`, `ui.visual_conventions`, `ui.alarm_edit_dialog`,
  `services.time_collapse_service`, `RIGHT_DOCK_COLLAPSED_MIN_WIDTH`). The D21 tests cannot pass pre-fix by
  construction.

## D. The two `pending_routing` observations — evaluated

1. **D21-16 out-of-footprint `ui/chart_panel.py` edit (~20 lines) — ACCEPTABLE, no follow-up.**
   `_sync_collapsed_consumers()` (called from `_rebuild_collapse_map()`, the empty-load clear, and
   `update_last_bar`) pushes the ChartPanel-owned `TimeCollapseMap` + plotted bars to `drawing_overlay` and
   `alarm_overlay`. `docs/architecture.md` S16/S17 makes **ChartPanel the owner of the map** and the pusher to the
   consumers, so this is the correct ownership boundary, not a misplaced edit. D21-16 was the sole task in wave 8,
   so the only real risk of an out-of-footprint edit (a same-wave `touches_files` race) could not occur. The one
   inaccuracy is that D21-16's **declared `touches_files` omitted `ui/chart_panel.py`** even though the task
   required touching it — a task-definition footprint gap. Because the task is complete, the outcome is correct and
   architecturally consistent, and re-scoping a done task has no value, this is recorded as an accepted observation
   (no escalation). *Recommendation for future graphs:* a consumer task that needs ChartPanel-side wiring should
   declare `ui/chart_panel.py` (or the plumbing should live in the ChartPanel-owning task).
2. **D21-13-T05 / `AC-D21.10.5` manifest-prose discrepancy — AC correctly implemented; the inverted prose is in
   `task-graph.json` itself → routed to Task Manager (F2 / ESC-029).** The AC is unambiguous (`requirements.md:1987`,
   architecture S15, `plan.md:58-59`): Cross Below when the **current** price is higher than the alarm price; Cross
   Above when lower or unknown. `ui/alarm_dialog.py::default_condition` implements exactly that, and
   `test_d21_13_t05_condition_default_on_open` asserts the AC (current=100/alarm=110 → **Cross Above**;
   current=100/alarm=90 → **Cross Below**; None → **Cross Above**) — the test asserts the AC, **not** the inverted
   prose. No code change is needed. However, the inverted wording is not only in the transient wave manifest: it is
   in the **authoritative `docs/tasks/task-graph.json` D21-13-T05 `description`** ("alarm price 110 -> Cross Below,
   90 -> Cross Above"), which Build may not edit. Build's log claim that the task description states the rule
   unambiguously is inaccurate. Routed to Task Manager as a wording-only fix (same class as ESC-018).

## E. Supersessions — coherent and documented, not silent

- **`AC-D16.3` display supersession (D21.4):** recorded on `AC-D16.3` itself (`requirements.md:1410`, "Superseded
  (display part) by D21.4 … the no-fill/no-interpolate rule above and D16's no-silent-hole requirements
  (`AC-D16.1`/`AC-D16.4`) are unchanged"), in the header (`:11`), the work-item note (`:75`), Q38 (`:1381`), A45
  (`:2067`), R37 (`:2153`), and the D21.4 section (`:1924`). Coherent.
- **D8 nice-max / ESC-007 only-widen volume supersession (D21.2):** recorded on `AC-D21.2.1` (`requirements.md:1903`),
  in the D21.2 edge cases (`:1904`), and in `plan.md:105`. `AC-D8.6`/`AC-D8.7` are re-scoped by the lockstep tests.
  Coherent.

## F. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-028 | D21-02 | BUILD | consistency / nice-to-have | D21.2 floors the ceiling to `[0,100]` for a small **non-zero** visible max (`0 < max ≤ ~90.9`) instead of `[0, 1.1×max]`; the AC's `[0, 1.10 × max_volume_visible]` is not met in that narrow regime (no test covers it; real volumes rarely hit it) |
| ESC-029 | D21-13 | TASK_MANAGER | gap / nice-to-have | `task-graph.json` D21-13-T05 description is inverted vs `AC-D21.10.5`; the AC, implementation and test are all correct — wording-only fix |

**Pipeline state for the Orchestrator:** Batch 15 (D21) is complete — **18/18 done**, `failures.json.blocked`
empty, full offscreen suite green (**672 passed / 0 failed / exit 0**, independently re-run). Two new
`nice-to-have` escalations are open: **ESC-028 (BUILD)** and **ESC-029 (TASK_MANAGER)**. Neither blocks the
pipeline; both are non-blocking quality/wording items. ESC-001…ESC-027 remain `addressed`.

Status: REVIEW_COMPLETE

# Revision 13 review — Batch 15 (D21) ESC-028 / ESC-029 verification pass, 2026-10-06

**Reviewer:** Code Reviewer agent. **Scope:** the Batch-15 (D21) rework round — `docs/build/build_log.md`
(Batch 15, wave 11 terminal consolidation; `Status: READY_FOR_REVIEW`), `docs/build/failures.json`
(`blocked` empty), the two open escalations **ESC-028** and **ESC-029**, `ui/chart_panel.py`
(`_recompute_visible_volume_range`), `tests/test_volume_d21.py` (new T05), `docs/tasks/task-graph.json`
(D21-13-T05 description + `AC-D21.10.5`), `ui/alarm_dialog.py::default_condition`,
`tests/test_alarm_d21.py::test_d21_13_t05_condition_default_on_open`. **Method:** every claim independently
re-verified on the live tree with the reviewer's own offscreen probes and runs (not Build's report); the
full clean offscreen suite and the D17/D18 focused modules re-run; the test list grepped for weakenings.
**No live TWS** — every run was `QT_QPA_PLATFORM=offscreen`. Nothing was fixed; only `docs/code_review/` was
written.

**Graphify:** `graphify-out/graph.json` (2416 nodes) was queried for orientation, but it is **stale for the
D21 modules** (no `ui/visual_conventions.py`, `services/time_collapse_service.py`, or D21 symbols) and it
still indexes the removed `_ensure_volume_range`/`_widen_volume_for` — so, per the graphify protocol, every
finding below was validated against the actual repository files (authoritative).

## A. ESC-028 — D21.2 volume ceiling floored a small non-zero visible max — **VERIFIED, CLOSED**

- **Fix present (code read).** `ui/chart_panel.py::_recompute_visible_volume_range()` (`:1146–1172`) now
  branches: `if visible_max > 0.0: ceiling = visible_max * 1.1` / `else: ceiling = VOLUME_NICE_FLOOR`
  (`:1165–1168`). The unconditional second `if ceiling < VOLUME_NICE_FLOOR` clamp is **gone**; the ESC-028
  comment (`:1158–1164`) records the rule so it is not reintroduced. The Y minimum stays 0 (D21.1 limit) and
  the range is still written only when the ceiling changes or `force`.
- **Reviewer offscreen probe (my own, 900×600, 3 bars, `ChartPanel.update_chart`, x-range pinned to the
  visible span):**

  | visible_max | measured yRange | expected |
  |---|---|---|
  | 0 | `[0.0000, 100.0000]` | `[0, 100]` ✓ |
  | 10 | `[0.0000, 11.0000]` | `[0, 11]` ✓ |
  | 50 | `[0.0000, 55.0000]` | `[0, 55]` ✓ |
  | 90 | `[0.0000, 99.0000]` | `[0, 99]` ✓ |
  | 91 | `[0.0000, 100.1000]` | `[0, 100.1]` ✓ |
  | 100 | `[0.0000, 110.0000]` | `[0, 110]` ✓ |
  | 1000 | `[0.0000, 1100.0000]` | `[0, 1100]` ✓ |

  Every case matches the literal `[0, 1.10 × visible_max]`, with `[0, 100]` reserved for the 0-visible case.
- **T05 is non-vacuous (proved, not assumed).** I re-introduced the pre-fix unconditional clamp **in memory
  only** (monkeypatched `ChartPanel._recompute_visible_volume_range`; no repo file edited) and ran the new
  test: `test_D21_02_T05_small_nonzero_visible_max_not_floored` **FAILED**
  (`visible_max=10 should give [0, 11.0], got 100.0 (ESC-028 floor regression)`); with the shipped method it
  **PASSES**. The test asserts the literal `1.10 × max` and, for `≤ 90`, an explicit `!= 100.0`. It is a
  genuine witness, not a tautology.
- **No regression.** `tests/test_volume_d21.py` → **10 passed**; the volume lockstep modules are green
  within the full suite.

## B. ESC-029 — `task-graph.json` D21-13-T05 description inverted vs `AC-D21.10.5` — **VERIFIED, CLOSED**

- **Description corrected (live file).** `docs/tasks/task-graph.json` D21-13-T05 `description` (`:802`) now
  reads: *"…last_price=100: alarm price 110 -> Cross Above, 90 -> Cross Below, None/unknown -> Cross Above;
  assert the user can override and the default is not recomputed on spinbox change."* This matches
  `AC-D21.10.5` (`docs/requirements/requirements.md:767`: Cross Below when the current price is higher than
  the alarm price; Cross Above when lower or unknown). The previously inverted "110 -> Cross Below,
  90 -> Cross Above" wording (quoted in the Revision-12 review) is gone; exactly one D21-13-T05 entry
  remains in the graph.
- **AC / implementation / test were correct all along (confirmed).** `ui/alarm_dialog.py::default_condition`
  (`:122–134`) returns `"Cross Below"` iff `current_price > alarm_price`, else `"Cross Above"` (including
  `None`); `tests/test_alarm_d21.py::test_d21_13_t05_condition_default_on_open` (`:314–338`) asserts
  current=100/alarm=110 → Cross Above, alarm=90 → Cross Below, None/unknown → Cross Above, and that a user
  override sticks. Re-ran it → **passed** (11 passed together with `tests/test_volume_d21.py`). No code or
  test change was needed; the fix is wording-only, exactly as routed.

## C. Independent full-suite + focused re-verification (reviewer-run)

- **Full clean offscreen suite** (shared test DB removed, `-p no:cacheprovider`):
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q -p no:cacheprovider` →
  **`673 passed in 11.92s`, 0 failed, exit code 0**. Build's 673/0 claim independently confirmed; matches
  baseline `04397d9` (D1–D20 = 585) + 87 D21 tests + the 1 new T05 = 673, so **no D1–D20 regression**.
- **D17/D18 chart-minimum / dock-width criteria intact:** `test_dock_layout` + `test_dock_widths_d17` +
  `test_dock_widths_d18` + `test_dock_widths_d18_impl` + `test_dock_d18_region` → **82 passed**;
  `ui/dock_layout.py` `CHART_MIN_WIDTH = 400` unchanged (`:21`).
- **No test weakened / skipped / deselected:** `grep -rnE "pytest\.mark\.(skip|xfail)|pytest\.skip|deselect|--ignore"`
  over `tests/` → **0 hits**.
- **No live TWS / order transmission (Q9):**
  `grep -rnE "eConnect|placeOrder|reqMktData|reqHistoricalData|cancelOrder|reqPositions|reqAccountSummary|reqOpenOrders|connectAsync|7496|7497|4001|4002"`
  over `tests/` → **0 hits**.

## D. Escalation close-out

- **ESC-028 → `addressed`** (edited in place, `Verified:` line added) — see A. Independently re-verified; the
  fix holds across the full band and the new T05 discriminates.
- **ESC-029 → `addressed`** (edited in place, `Verified:` line added) — see B. The task-graph wording now
  matches the AC; the AC/implementation/test were already correct.
- **ESC-001…ESC-027 remain `addressed`** (re-confirmed: nothing relevant changed for them this pass).
  After this pass **no open escalations remain** (`grep -nE "Status: *(open|ESCALATED_TO_)"` over
  `escalations.md` → **none**).

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | **None.** Both reworks verified independently; the full clean suite is green (673/0); D17/D18 minimum-width intact; no test weakened; no live TWS. No quality, consistency, or security issue found. |

**Pipeline state for the Orchestrator:** Batch 15 (D21) is complete — **18/18 done**, `failures.json.blocked`
empty, full clean offscreen suite green (**673 passed / 0 failed / exit 0**, independently re-run). **No open
escalations remain** — ESC-001…ESC-029 are all `addressed`. The pipeline can advance (build complete).

Status: REVIEW_COMPLETE

# Revision 14 review — Batch 16 (D22: in-app watchlist "Add symbol" / "Remove symbol"), 2026-10-07

**Reviewer:** Code Reviewer agent. **Compared revision:** `286341e` (D21) + uncommitted D22 working-tree changes
(`git status`: modified `data/db.py`, `ibkr/bridge.py`, `ibkr/client.py`, `ibkr/market_data.py`,
`ui/main_window.py`, `ui/watchlist_panel.py`; new `services/contract_lookup_service.py`,
`ui/add_symbol_dialog.py`, and 7 D22 test files).
**Scope:** `docs/build/build_log.md` (Batch 16 waves 1–5; terminal `Status: READY_FOR_REVIEW`),
`docs/build/failures.json` (`blocked` empty; 6 `pending_routing` entries),
`docs/build/results/_archive/wave5_D22-09.json`, `docs/tasks/task-graph.json` (D22-01…D22-09),
`docs/requirements/requirements.md` (D22 / AC-D22.1–9 / A48–A52 / R45–R48 / Journey 27),
`docs/architecture.md` + `docs/plan.md` (D22 increment), and every changed D22 product/test file.
**Method:** every claim independently re-verified on the live tree with the reviewer's own offscreen runs and
probes (not Build's report); the full clean offscreen suite and the D21/D14/D17/D18 regression modules re-run;
each changed product file read against its acceptance criterion. New findings were routed via
`docs/code_review/escalations.json`; the legacy `escalations.md` was **not** rewritten.
**No live TWS** — every run was `QT_QPA_PLATFORM=offscreen`. Nothing was fixed; only `docs/code_review/` was written.

**Graphify:** the on-disk `graphify-out/graph.json` predates D22 (no `contract_lookup_service` /
`add_symbol_dialog` / D22 symbols), so it was used only for orientation and every finding was validated against
the actual files (authoritative).

## A. Independent test evidence (reviewer-run, not Build's)

- **Seven D22 modules in one invocation** (shared test DB `$TMPDIR/tos_charting_test.sqlite3*` removed first):
  `test_watchlist_addflow_d22` + `test_watchlist_persistence_d22` + `test_ibkr_contract_details_d22` +
  `test_contract_lookup_d22` + `test_watchlist_add_remove_d22` + `test_add_symbol_dialog_d22` +
  `test_watchlist_nonregression_d22` → **39 passed** in 1.29s (Build's "37" was the six original modules; +2 = the
  D22-09 non-regression tests).
- **Full clean offscreen suite:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q
  -p no:cacheprovider` → **712 passed / 0 failed / exit 0** (`712 passed in 16.27s`). Build's "712 passed" is
  confirmed. 712 collected = 712 passed; **no skips/xfails/deselects** (`grep -rnE "@pytest\.mark\.(skip|xfail)|
  pytest\.skip\(|pytest\.xfail\(" tests/` → 0 hits; no `deselect`/`--ignore` in config; `addopts = -q` only).
- **D1–D21 non-regression modules** (`test_watchlist_columns_d21` D21.5, `test_watchlist` D14,
  `test_right_dock_d21` D21.13, `test_toolbar_d21`, `test_volume_d21`, `test_time_collapse_d21`,
  `test_watchlist_d14_midrag`, `test_dock_layout` D17/D18) → **123 passed**. No D1–D21 criterion regressed.
- **No live TWS / no order transmission (Q9):** grep over the D22 test files for
  `eConnect|placeOrder|reqHistoricalData|reqMktData|connectAsync|7496|7497|4001|4002` → **0 hits**. The D22
  `MainWindow` tests monkeypatch `IBApiClient.connect` to a no-op; the D22 ibkr tests build `IBApiClient()` bare
  and never call `.connect()`. Confirmed.
- **D22 did not touch the dock/chart core:** `git diff --stat -- ui/dock_layout.py ui/chart_panel.py` → empty;
  the `ui/main_window.py` diff adds no `CHART_MIN_WIDTH` / `WATCHLIST_MIN_WIDTH` / `RIGHT_DOCK_MIN_WIDTH` /
  `_apply_dock_widths` / `_plan_dock_widths` / `dock_layout` lines; **no dependency file changed** (`requirements`
  /`pyproject`/`setup`/`poetry` untouched — the only "requirements" hits are `docs/requirements/*.md`). No
  live-order-path change (`load_chart`/`_on_watchlist_row_double_clicked`/`placeOrder`/`reqHistoricalData`/`eConnect`
  → 0 diff lines).

## B. AC-D22.1–D22.9 verification (against the live code)

- **AC-D22.1 (affordance + placement).** `ui/watchlist_panel.py:311-324` adds a `+` `QPushButton` on `header_bar`
  in the same `h_layout` as the D21.11 `header_button`; the strip's own `CustomContextMenu` offers
  "Add symbol…" (`:332-335`, `:407-418`); the D21.5 column popup stays bound to `table.horizontalHeader()`
  (`:362-364`); the D21.11 toggle is untouched. **Holds** (D22-04-T01, D22-09-T01).
- **AC-D22.2 (modal input).** `ui/add_symbol_dialog.py` — one `QLineEdit` + OK/Cancel, Esc → reject, OK with
  non-empty accepts (raw/un-normalised), empty/whitespace refused in place with an inline message. **Holds**
  (D22-06-T01/T02).
- **AC-D22.3 (normalisation + guards).** `normalise_symbol` = strip+upper, `symbol_in_list` case-insensitive
  (blank never "present"); blank rejected in the dialog *and* in `_on_watchlist_symbol_add_requested:624-627`;
  a case-insensitive duplicate of `db.get_watchlist()` is a no-op with a message (`:633-638`). **Holds**
  (D22-04-T03, D22-08-T01/T02/T03).
- **AC-D22.4 (live validation before add).** add → `_contract_lookup.request(sym, get_contract_for_symbol(sym))`
  (`:639`) → bounded 5 s `ContractLookupService`; on `ok=True` while connected the row is added/subscribed
  (`add_symbol`→`req_mkt_data`) and persisted (`:668-671`); on `ok=False` or a mid-flight disconnect nothing is
  added/subscribed/persisted (`:658-667`). **Holds** (D22-03-T01..T06, D22-08-T03/T04).
- **AC-D22.5 (require connection).** `_ibkr_connected=False` + `set_add_enabled(False)` initially (`:321-322`);
  `_on_connected`→True/enable (`:565-566`); `_on_disconnected`→False/disable (`:720-721`); the slot also refuses
  with a message while disconnected (`:628-632`). **Holds** (D22-07-T01, D22-08-T01).
- **AC-D22.6 (remove).** table-body context menu offers exactly "Remove symbol" and resolves the row's Symbol by
  field key (reorder-safe) (`:495-515`); `remove_symbol` cancels that row's reqId(s), stops its flash timers, drops
  the row and re-indexes (`:682-728`); `_on_watchlist_symbol_remove_requested` persists + sets the sentinel with no
  connection gate (`:673-687`). **Holds** (D22-05-T01/T02/T03, D22-08-T05). — *One stale-key nit: ESC-031.*
- **AC-D22.7 (persisted across restarts).** `data/db.py::add_watchlist_symbol` (case-insensitive idempotent,
  appends at `max(sort_order)+1`) and `remove_watchlist_symbol` (case-insensitive delete + renumber 0..n-1);
  `get_watchlist`/`set_watchlist` unchanged; `watchlist/configured` sentinel; `_restore_watchlist` clears then
  repopulates, seeds `DEFAULT_WATCHLIST` only when the DB list is empty **and** the sentinel is unset, sets the
  sentinel on a non-empty list / add / remove. **Holds** (D22-01-T01..T04, D22-07-T02/T03, D22-08-T06).
- **AC-D22.8 (non-regression D21.5/D21.11/D14/D21.13).** D22-09-T01 asserts the D21.5 column popup (7 checkable
  fields, Symbol non-removable), the D21.11 collapse toggle (body hidden/shown, struck state), the D14
  field-key double-click emit, and the D21.13 right-dock title/summary toggles; independently corroborated by the
  123-test D21/D14/D17/D18 regression run. **Holds.**
- **AC-D22.9 (regression suite).** **Holds** — 712 passed / 0 failed (independently re-run), Q9 confirmed, no test
  weakened/skipped/deselected.

## C. Test quality and isolation (AR-D22-9 and non-vacuity)

- **Non-vacuous.** The D22 tests assert real behaviour, not tautologies: `test_watchlist_addflow_d22` drives a real
  offscreen `MainWindow` through gate/duplicate/success/failure/disconnect paths and asserts no row/subscription/DB
  change where required; `test_contract_lookup_d22` proves exactly-once resolution, late-event rejection, error
  correlation and bounded timeout with a fake bridge; `test_watchlist_add_remove_d22::test_D22_05_T02` proves the
  reqId/flash-timer re-index lands a later tick on the correct row; `test_add_symbol_dialog_d22` proves the dialog
  refuses empty input in place. None is over-mocked (the `MainWindow` tests use the real panel/DB/lookup service
  with only `IBApiClient.connect` and the md-manager faked).
- **Isolation / AR-D22-9.** Every D22 `MainWindow` test patches a throwaway per-test SQLite file
  (`config.paths._DB_FILENAME` + `ui.main_window.db`) and swaps `win._settings` for a per-test `QSettings(IniFormat)`
  before the `watchlist/configured` sentinel can be read/written; the persistence and lookup tests use their own
  temp DB / fake bridge. The real user DB and the real sentinel are never touched. Confirmed by code read.
- **No weakening.** The D22 files contain no `skip`/`xfail`/`deselect`; the added lockstep assertions (e.g. D22-09,
  D22-05 re-index) are substantive.

## D. Escalation close-out

- `docs/code_review/escalations.json` did not exist before this pass. The legacy `docs/code_review/escalations.md`
  carries **no open entry** — **ESC-001…ESC-029 are all `addressed`** (re-confirmed: nothing relevant to them
  changed this batch; the D22 batch adds new files and does not touch any file an addressed entry cited except
  `ui/main_window.py`, whose D22 additions do not alter the ESC-017 draw-combo/TR-4 path, `_finalize_stranded_history_wave`,
  or the dock-width paths). **Nothing to close**; the two new findings are recorded in `escalations.json`.

## E. `failures.json.pending_routing` observations — evaluated

1. **D22-02 `cancelContractDetails` api surface gap (routed to Code Reviewer) → decided: needs a small routed fix,
   non-blocking.** Verified against the installed dependency: `hasattr(EClient,'cancelContractDetails') is False`
   (ibapi 9.81.1.post1) while `reqContractDetails` exists — so on the real TWS path the cancel is a swallowed
   `AttributeError`, a silent no-op. The code satisfies AC-D22.2.3 literally, and the local-invalidation contract
   (bounded `QTimer` + `cancel_all` on disconnect; TWS always ends the request via `contractDetailsEnd`/error) means
   **no D22 behaviour depends on the wire cancel**. Routed to **BUILD** as a `nice-to-have` (capability-guard +
   document, or reconcile the AC/architecture) — **ESC-030**.
2. **Tooling defect — `~/.config/opencode/scripts/build_wave.py advance` crash (non-blocking).** Build reports the
   script aborted with `AttributeError: 'list' object has no attribute 'get'` at its circuit-breaker loop because it
   assumes every `failures.json` value is a task dict, whereas this repo's `failures.json` carries list-valued
   aggregate keys (`blocked`, `pending_routing`, `notes`). This is a **global tool, outside this repository** — no
   pipeline agent owns it, so **no escalation is raised** (an escalation's `routed_to` must be one of the four repo
   owners and none applies). Recorded here for the **Orchestrator / user**: the crash happened *after*
   `task-graph.json`/`failures.json` were written and the result archived, before `wave.json` was finalised and the
   terminal line written; Build (the sole writer of those files) completed the two deterministic writes by hand, so
   the artifacts are consistent. Suggested (out-of-repo) direction: skip non-dict top-level values when iterating
   `failures.items()`.
3. **Carried historical `pending_routing` items — no re-diagnosis.** `pre_existing_segfault_full_suite` (reconciled),
   `dock_layout_plan_below_minimum` (resolved, ESC-026), `plan_dock_widths_single_call_underconvergence` (witness
   resolved in T56; Build's "plan-vs-post-resize-chart-area interaction, resolved by the resizeEvent/changeEvent
   normalize path" judgment stands — accepted), `out_of_footprint_edit` D21-16 (evaluated in the Revision-12 review:
   correct ownership boundary per architecture S16/S17, accepted, no escalation), and `manifest_prose_discrepancy`
   D21-13 (fixed as ESC-029, `addressed`). None is a D22 item.

## F. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-030 | D22-02 | BUILD | quality / nice-to-have | installed ibapi 9.81.1.post1 has no `EClient.cancelContractDetails`, so `cancel_contract_details` is a swallowed-`AttributeError` silent no-op on the real TWS path; AC-D22.2.3/S3 mandate a call the pinned dependency does not expose. No D22 behaviour depends on it (local invalidation + TWS-side `contractDetailsEnd`/error). |
| ESC-031 | D22-05 | BUILD | quality / nice-to-have | `remove_symbol` re-indexes `_row_data` without dropping the removed row's key, leaving a stale key when the **last** row is removed (`rowCount()==2` but keys `[0,1,2]`); the middle-row test does not catch it. Benign today (never read out of range, overwritten on next add, cleared by `clear()`). |

**Pipeline state for the Orchestrator:** Batch 16 (D22) is complete — **9/9 tasks done**, `failures.json.blocked`
empty, full clean offscreen suite green (**712 passed / 0 failed / exit 0**, independently re-run; no D1–D21
criterion regressed). Two new `nice-to-have` escalations are open: **ESC-030 (BUILD)** and **ESC-031 (BUILD)**;
neither blocks the pipeline. No prior escalation is open (ESC-001…ESC-029 `addressed`).

Status: REVIEW_COMPLETE

---

# Revision 15 review — Batch 17 (D23: the two approved D22 quality fixes + reconciliation record), 2026-10-07

**Reviewer:** Code Reviewer agent. **Compared revision:** `286341e` (D21) + uncommitted D22/D23 working-tree
changes. **Scope:** `docs/build/build_log.md` Batch 17 (waves 7–8; terminal `Status: READY_FOR_REVIEW`),
`docs/build/failures.json` (`blocked` empty), the archived structured results
`docs/build/results/_archive/wave7_D23-01.json` / `wave7_D23-02.json` / `wave8_D23-03.json`, the D23 worker logs,
`docs/tasks/task-graph.json` (D22-02 `AC-D22.2.3` correction + D23-01/02/03), `docs/requirements/requirements.md`
(D23 / `AC-D23.1.*` / `AC-D23.2.*`), `docs/architecture.md` (D22 `S3` reconciliation note + D23 increment `S3`),
and the changed product/test files (`ibkr/market_data.py`, `ui/watchlist_panel.py`,
`tests/test_ibkr_contract_details_d22.py`, `tests/test_watchlist_add_remove_d22.py`,
`tests/test_d23_nonregression.py`). **Method:** every claim independently re-verified on the live tree with my own
offscreen runs and probes (not Build's report). **No live TWS** — every run was `QT_QPA_PLATFORM=offscreen`.
Nothing was fixed; only `docs/code_review/` was written.

**Graphify:** the on-disk `graphify-out/graph.json` predates the D23 modules and does not contain D22/D23 symbols,
so it was used only for orientation; every finding was validated against the actual repository files
(authoritative).

## A. ESC-030 (D23-01) — `cancel_contract_details` capability guard — independently VERIFIED, CLOSED

- **Code read (live).** `ibkr/market_data.py:78-108`: `cancel_contract_details` keeps `if req_id is None: return`;
  resolves `cancel = getattr(self.client, "cancelContractDetails", None)` (`:102`); returns early when absent
  (`:103-104`); calls `cancel(req_id)` only when present, inside the retained `try/except Exception: pass`
  (`:105-108`). The bare `self.client.cancelContractDetails(...)` access is gone. The docstring names all three
  facts (pinned-`ibapi` absence, TWS `contractDetailsEnd`/error termination, `ContractLookupService` `cancel_all`
  safety net). `req_contract_details` is unchanged.
- **Code-shape RED→GREEN (my own AST probe, not Build's).** Over the reconstructed pre-fix form
  (`self.client.cancelContractDetails(req_id)` inside try/except): `bare_attr=1`, `bare_substr=True`,
  `guard=False` → the D23-01-T01 / D23-03-T03 assertions **fail** (genuinely red). Over the shipped source:
  `bare_attr=0`, `bare_substr=False`, `guard=True` → **pass**. The guard string is a `str` constant inside a
  `getattr(...)` call, so it is not itself an `ast.Attribute` node — the shape check discriminates correctly.
- **Behavioural guards reproduced.** Pinned shape (`types.SimpleNamespace(reqContractDetails=...)`, no cancel
  attribute) → silent no-op, no exception; present `_FakeClient` → `cancel_calls == [7]` exactly once;
  `req_id=None` → `cancel_calls == []`; present-but-raising → contained, no propagation.
- **Dependency fact re-confirmed:** installed dist `ibapi 9.81.1.post1`, `hasattr(EClient,'cancelContractDetails')
  is False`. There is **no production caller** of `cancel_contract_details` (only the definition; grep excl.
  `tests/`), matching A54 — the fix is forward-correctness with no observable D22 behaviour change.
- **Test evidence:** `tests/test_ibkr_contract_details_d22.py` → **13 passed** (7 pre-existing D22 + 6 D23-01),
  including the retained present-method/None/raising D22 cases. Archive `wave7_D23-01.json` status `done`.

## B. ESC-031 (D23-02) — `remove_symbol` drops the removed row's `_row_data` key — independently VERIFIED, CLOSED

- **Code read (live).** `ui/watchlist_panel.py:723`: `self._row_data.pop(row, None)` runs immediately after
  `table.removeRow(row)` and **before** the `{(r-1 if r>row else r): values ...}` re-map (`:724-727`); the
  docstring (`:682-699`) states the invariant `set(_row_data.keys()) == set(range(table.rowCount()))` (and the
  `_req_to_row` / flash-timer analogues).
- **Reproduction (my own offscreen probe with the real `WatchlistPanel` + a fake md manager).** Post-fix, a 3-row
  panel (AAPL/MSFT/TSLA): remove **last** → rowCount 2, keys `{0,1}` ✓; remove **first** → `{0,1}` ✓; remove
  **middle** → `{0,1}` ✓; remove **all** → rowCount 0, keys `{}` ✓ (invariant holds in every case). Running the
  **same** sequence against the pre-fix code path (re-map without the `pop`) leaves rowCount 2 but keys
  `{0,1,2}` — the exact stale last-row key ESC-031 named — proving the assertions are **red-before / green-after**.
- **Test evidence:** `tests/test_watchlist_add_remove_d22.py` → **11 passed** (D22-04/05 retained + D23-02
  T01/T02/T05); `test_D23_02_T01` (last-row), `T02` (first/middle/only), `T05` (FieldKey-bound, no value shift) are
  real and discriminating. Archive `wave7_D23-02.json` status `done`.

## C. Record coherence — `AC-D22.2.3` correction + architecture `S3` reconciliation — COHERENT

- **Task graph.** `docs/tasks/task-graph.json` `D22-02` `AC-D22.2.3` is marked
  `[CORRECTED by D23.1 / AC-D23.1.4]` and now mandates the capability-guarded best-effort cancel
  (`getattr(...)`, "only when present"), states the pinned `9.81.1.post1` / no `EClient.cancelContractDetails`
  absence, explicitly `supersedes the former 'calls client.cancelContractDetails(req_id)' mandate` and notes D22's
  feature criteria are `not reopened`; the D22-02 description carries the same guarded cancel.
- **Architecture.** `docs/architecture.md` carries the D22 `S3` reconciliation note (`S3 reconciled by D23
  (2026-10-07)`, binding `AC-D23.1.4`) and the D23 increment `S3 *(reconciled)*` row recording the same guard,
  "call it only if present", pinned-ibapi absence, TWS end and `ContractLookupService` safety net — the two agree.
- **No D22 feature criterion reopened.** `requirements.md` `AC-D22.1`–`AC-D22.9` headings are intact and the D23
  section states `its feature criteria (AC-D22.1–AC-D22.9) stand`. `tests/test_d23_nonregression.py` (5 passed)
  re-verifies both records and that exactly one task-level criterion carries the correction marker.
- **`D23-03-T05` note (informational):** `wave7_D23-01.json` lists `D23-01-T05` as `pass` although the worker log
  labels T05 a *manual* docstring review (the automated docstring assertions live in T04). This is a worker
  self-verdict on a manual criterion, not a weakened/skipped test — no action.

## D. Independent full-suite + non-regression (reviewer-run)

- **Full clean offscreen suite** (shared test DB `$TMPDIR/tos_charting_test.sqlite3*` removed first,
  `-p no:cacheprovider`): `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q -p no:cacheprovider`
  → **`726 passed in 16.04s`, 0 failed, exit code 0**. Build's 726/0 claim independently confirmed. Decomposition:
  712 D22 baseline + 14 new D23 tests (D23-01 +6, D23-02 +3, D23-03 +5) = 726 → **no D1–D22 regression**.
- **No test weakened / skipped / xfailed / deselected:** `grep -rnE "pytest\.mark\.(skip|xfail)|pytest\.skip|
  deselect|--ignore|@unittest\.skip"` over the D22/D23 test files → **0 hits**.
- **No live TWS / no order transmission (Q9):** the only `.connect(` hits are PyQt signal connections; the D22/D23
  `MainWindow` tests `monkeypatch.setattr(IBApiClient, "connect", ...)` to a no-op, and the raw `IBApiClient()`
  instantiations in `test_ibkr_contract_details_d22.py` never call `.connect()` (`EClient.__init__` opens no
  socket). No transmission reference (`placeOrder`/`reqMktData`/`reqHistoricalData`/`eConnect`/ports) found.
- **No new dependency / schema / live-order-path change:** the D23 diff on `ibkr/market_data.py` is `+39` lines and
  adds only the two methods (no new import, no `CREATE TABLE`, no order/connect call); `ui/watchlist_panel.py`'s
  D23 delta is the single `pop` + docstring; no dependency manifest changed.

## E. Escalation close-out

- **ESC-030 → `addressed`** (edited in place, `verified` added) — see A. Independently re-verified: the bare access
  is gone, the guard + docs are present, the shape check is red-before/green-after, and the behavioural guards pass.
- **ESC-031 → `addressed`** (edited in place, `verified` added) — see B. Independently re-verified: keys ==
  `range(rowCount())` after last/first/middle/only removals; the pre-fix path reproduces the stale key.
- **No other escalation is open.** `docs/code_review/escalations.json` holds only ESC-030 and ESC-031; both are now
  `addressed` (verified programmatically: 0 non-`addressed` entries). ESC-001…ESC-029 remain `addressed` from prior
  passes (legacy `escalations.md`), unchanged and not affected by D23.

## F. New findings and observations

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | **None.** Both D23 fixes are correct, minimal, and independently verified; the full clean suite is green (726/0); D22's feature criteria are not reopened; no test weakened; no live TWS; no new dependency/schema/order-path change. No new quality, consistency, or security issue found. |

- **External tooling defect (recorded, NOT routed — no pipeline agent owns it):**
  `~/.config/opencode/scripts/build_wave.py advance` aborts with
  `AttributeError: 'list' object has no attribute 'get'` at its circuit-breaker loop, because it iterates
  `failures.items()` assuming every value is a task dict while this repo's `failures.json` carries list-valued
  aggregate keys (`blocked`, `pending_routing`, `notes`). The crash occurred **after** the consolidation writes
  (`task-graph.json`, `failures.json`, archived results, per-task done lines) and **before** `wave.json` was
  finalised; Build (the sole writer of those files) recovered deterministically by setting `wave.json` to
  `CONSOLIDATED` and re-running `advance` (Step 2 only). Build's log (waves 7 and 8) matches the artifacts on disk
  — `task-graph.json` shows D23-01/D23-02/D23-03 `done` and `wave.json` is `CONSOLIDATED`. No determinism or data
  lost. This is a **global tool outside this repository**; `routed_to` must be one of the four repo owners and none
  applies, so **no escalation is raised**. Suggested (out-of-repo) direction: skip non-dict top-level values when
  iterating `failures.items()`.

**Pipeline state for the Orchestrator:** Batch 17 (D23) is complete — **3/3 tasks done**, `failures.json.blocked`
empty, full clean offscreen suite green (**726 passed / 0 failed / exit 0**, independently re-run; no D1–D22
criterion regressed). **No open escalations remain** — ESC-001…ESC-031 are all `addressed`. The pipeline can
advance (build complete).

---

# Review — fresh live-run defect report (two TWS run-time errors), 2026-10-15

**Reviewer:** Code Reviewer agent. **Tree:** `main @ 29067af`, working tree clean. **Nature:** an out-of-band
defect report from a **live app run against TWS** — *not* a Build run. No agent has touched the code; nothing was
fixed. **Scope:** the two tracebacks supplied verbatim, the three IBKR-side log lines in the same log, and the
source those errors name (`ui/main_window.py`, `ui/active_portfolio_panel.py`, `data/models.py`, `ibkr/account.py`,
`ibkr/bridge.py`, `ibkr/client.py`, `ibkr/market_data.py`, `data/db.py`). **No `build_log.md`/`failures.json` for
these tasks exists** — the last pipeline build/review was D23 (`docs/build/build_log.md`, 726 tests); the tree is
ahead of it (whole suite now **1028 tests, green / 0 failed**). Nothing was fixed; only `docs/code_review/` was
written. **No live TWS in my runs** — every probe was `QT_QPA_PLATFORM=offscreen` against the real classes.

**Method:** each error was reproduced independently offscreen from the real source (not from the traceback text),
root-caused to `file:line`, then classified for owner. `git blame`/`git log -S` used for regression status.

## A. Error A — `AttributeError: 'Position' object has no attribute 'id'` (portfolio panel) — **ESC-032, BUILD, blocking**

- **Exact failure.** Every TWS position update raises at **`ui/active_portfolio_panel.py:308`**
  (`strategy_by_id.get(pos.id, "—")`), reached via `ui/main_window.py:3317`
  (`self.portfolio_panel.add_position(position)`) → `active_portfolio_panel.py:216 add_position` →
  `:293 _group_and_render` → `:308 _render_table`. My offscreen repro reproduces the identical traceback.
- **Root cause — two `Position` classes, wrong one on the wire.** There are two unrelated dataclasses named
  `Position`:
  - `data.models.Position` (`data/models.py:73-89`) — **has** `id: Optional[int] = None` (line 89). This is what
    the panel is written against (`active_portfolio_panel.py:23`) and what `main_window.py:81` imports.
  - `ibkr.account.Position` (`ibkr/account.py:20-39`) — **no** `id` attribute (it adds
    `market_price`/`unrealized_pnl`/`realized_pnl` instead).
  The live caller `ui/main_window.py::_on_position_update` builds the object with
  `ibkr.account.build_position_from_ib` (`main_window.py:3293` → `ibkr/account.py:47`) → an
  **`ibkr.account.Position`**, then feeds it to a panel whose parameter annotation
  (`active_portfolio_panel.py:210`) and whose `main_window.py:3337` annotation both claim
  `data.models.Position`. The `.id` deref also exists at `:287/:289` (option-leg grouping) and `:222/:344/:364`
  (SL/TP, close). Verified: `hasattr(build_position_from_ib(...), 'id') is False`;
  `ActivePortfolioPanel().add_position(ibkr.account.Position)` raises exactly; the same call with a
  `data.models.Position` does not.
- **Why it manifests now.** Both classes, the `add_position` call and the `.id` derefs are all from the initial
  commit `90b4539` (2026-09-19). The path was **dead** until commit `d7e2dc27` (D27.5, 2026-10-12) supplied the
  missing `stop_loss`/`take_profit` args (before that the call raised `TypeError` first) and commit `2bfd097b`
  (D27.6, 2026-10-12) added the `reqPositions()` subscription (`main_window.py:1214`) so `position()` callbacks
  actually fire. **Not a regression** — a long-standing latent defect newly *exposed* by D27.5/D27.6.
- **Bulk-load path.** `_on_position_end` (`main_window.py:3319`) does **not** crash: it builds a
  `data.models.Position` whose `id` defaults to `None`. But it is **degraded** — its `SELECT` (`:3323-3327`)
  omits `id`, so **every** bulk-loaded position has `id=None`: the Strategy/Group columns render `—` and the
  SL/TP dialog early-returns (`active_portfolio_panel.py:344`), and `_on_portfolio_sltp_changed` persists via
  `UPDATE positions ... WHERE id=?` (`main_window.py:3400`). Same invariant (the panel needs a populated `id`),
  so it is folded into ESC-032 rather than split out.
- **User-visible impact.** The table render aborts inside `_render_table` on every update → Strategy/Group columns
  and per-row P&L never appear; **`AC-D27.6` ("the portfolio panel populates", requirements.md:2882) is unmet**.
- **Correct fix shape (direction, not a decision).** Converge the models and **populate `id`** — not a defensive
  `getattr`. The panel needs a *real* id (grouping keys **and** `WHERE id=?` SL/TP persistence), so a defensive
  read would silence the crash while leaving grouping/SL-TP silently broken and keeping the two-model drift that
  caused this. `ibkr.account.Position` should carry `id` (or the models should converge on one, keeping the
  `market_price` field the panel reads at `active_portfolio_panel.py:386`), populated from the DB by
  `_upsert_position` (return the rowid), and `id` added to the `_on_position_end` SELECT. If converging on a
  single canonical model is judged an architecture decision, it should go to Plan — hence noted in the direction.

## B. Error B — `AttributeError: 'bool' object has no attribute 'strip'` (Load Chart button) — **ESC-033, BUILD, blocking**

- **Exact failure.** `ui/main_window.py:1717` (`symbol = symbol.strip().upper()`), the `else` (parameter-supplied)
  branch of `load_chart`.
- **Root cause — Qt signal arity vs the parameterised method.** `ui/main_window.py:223`
  `self.load_btn.clicked.connect(self.load_chart)`. `QPushButton.clicked` emits
  `clicked(bool checked = false)`. Since commit `692bb61` (D28.2, 2026-10-13) the method is
  `load_chart(self, symbol=None, timeframe=None, extended_hours=None)` (`main_window.py:1711`), so PyQt binds the
  emitted `False` to `symbol` → not `None` → `False.strip()`. Verified offscreen: `clicked` delivers `(False,)`
  to a slot that accepts args, and `MainWindow.load_chart`'s first parameter is `symbol`; a **0-arg** slot
  receives nothing.
- **Regression status: YES — a REGRESSION from D28.2.** Pre-D28.2 the method was `def load_chart(self):`
  (`git show 692bb61^:ui/main_window.py:1062`), so PyQt dropped the bool and the button worked; the
  caller-supplied-symbol `.strip()` exists only from D28.2.
- **Other call sites checked — all safe.** `:1337 load_chart(symbol)` (str), `:214 returnPressed` (no-arg signal
  → `symbol=None` → widget path), `:2952`/`:2971 load_chart()` (no args). No other bool-emitting signal is wired
  to `load_chart`. So the button is the **sole** wrong-type caller today; the *class* of bug (a `bool`-emitting
  signal wired to a value-first-parameter slot) is the general hazard noted in the escalation.
- **User-visible impact.** The primary "Load Chart" control is dead (loads nothing, logs one traceback). Enter in
  the symbol field and watchlist double-click still work, which is why the app remains usable.

## C. IBKR-side log lines — assessed, **no escalation**

- `2152 Exchanges - Depth: … Need additional market data permissions` and
  `10090 Part of requested market data is not subscribed` are **account-entitlement** conditions, not code
  defects. The app already handles them deliberately: `_on_error` routes depth errors
  (`main_window.py:1664-1671`) to `TickerSession.on_depth_error` (`ticker_session.py:786`), which sets an explicit
  `no_entitlement`/`unavailable` state for the heatmap, and the DOM path surfaces
  `"depth subscription required."` (`main_window.py:1677-1683`). No unentitled-venue filtering is required by any
  requirement; behaviour is degrade-gracefully as specified.
- `SPY: No earnings dates found, symbol may be delisted` is **not** the app's text — it originates inside
  **yfinance** (the D38 source calls `ticker.get_earnings_dates`, `data/events/yfinance_source.py:143`). SPY is an
  ETF with no earnings, so the message is benign; the "may be delisted" wording is third-party and mildly
  misleading but is not produced or controllable by this repo. **No route.**

## D. Why the green 1028-test suite missed both (missing coverage)

- **Error A.** The one test that drives the real path,
  `tests/test_d27_account_subs.py::test_d27_6_positions_populate_panel`, emits the real
  `bridge.position_update` and therefore **does** enter `add_position → _group_and_render → _render_table` and
  **does** raise — I reproduced the full traceback under it — yet it **passes**. Two reasons: (1) the exception is
  swallowed — `main.py`/`ui.main_window` import **pyqtgraph**, whose `pyqtgraph/Qt/__init__.py:314-318` installs a
  non-abort `sys.excepthook`, so a slot exception is printed and dropped instead of aborting (this also explains
  why the live app logs Error A *repeatedly* rather than crashing, and why the user's log shows it many times);
  and (2) the assertion checks `any(p.symbol == "HELD" for p in ..._positions)` — `_positions` is appended
  *before* the render throws, so the assertion passes while the table render is broken.
  `tests/test_d27_position_prices.py` never reaches it at all: it **monkeypatches `add_position`** (`:65,:91,:106`)
  so the real render never runs. The bug is one attribute-access removed from an assertion that would catch it.
- **Error B.** **No test clicks the button.** The suite calls `load_chart()` / `load_chart(sym, tf)` directly
  (e.g. `tests/test_d28_2_sessions.py:145`, `tests/test_d24_smoke_gate.py:50`) and never the toolbar signal
  connection. Notably `tests/test_order_entry_mkt.py:6-8` documents the suite's habit of **avoiding `.click()`**,
  because a slot exception can abort an offscreen process — so the button's signal→slot arity mismatch is never
  exercised. `tests/test_toolbar_d20.py`/`test_toolbar_scroll_d19.py` list `load_btn` only for scroll-reachability.
- **Implication.** Both are *signal-wiring / cross-object-type* defects that unit tests calling methods directly
  (or stubbing the very method under test) structurally cannot see. Regression tests are warranted for both
  (assertions specified in ESC-032/ESC-033); the ESC-032 test must assert on the **rendered table**, not on
  `_positions` membership.

## E. Escalation close-out

- **None to close.** No prior escalation is open: ESC-030/ESC-031 remain `addressed` (both D23 fixes re-verified
  green last pass), and `escalations.json` held no other open entry. Nothing routed to `BUILD`/`TASK_MANAGER`/
  `PLAN`/`REQUIREMENTS` earlier in this file links to these two new defects.

## F. Findings and routing

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-032 | D27-06 | **BUILD** | bug / **blocking** | Panel (written for `data.models.Position.id`) is fed `ibkr.account.Position` (no `id`) by the live `_on_position_update`; render aborts per update → AC-D27.6 unmet. Long-standing, newly exposed by D27.5/D27.6. |
| ESC-033 | D28-02 | **BUILD** | bug / **blocking** | `load_btn.clicked` (emits `bool`) wired to the now-parameterised `load_chart(symbol=…)`; Clicking "Load Chart" raises. **Regression from D28.2.** |

- **Owner rationale (not REQUIREMENTS/PLAN/TASK_MANAGER).** Both are code defects against clear requirements —
  `AC-D27.6` (portfolio populates, requirements.md:2882) and `AC-D28.2` ("`load_chart` works without toolbar
  widgets", requirements.md:2932, with the `load_chart(symbol, timeframe, extended_hours)` contract at :2909).
  Neither the requirement nor the plan is wrong; `architecture.md` (`:215`, `:790-793`, `:519-521`) treats
  `Position` as a **single** model, so `ibkr.account.Position`'s divergence is a code/consistency break against
  the architecture's intent, not a bad architecture decision. No task-breakdown issue (no relevant task exists —
  these are out-of-pipeline revision batches). So: **BUILD** for both, with the unify-vs-defensive judgement left
  in ESC-032's direction (route to Plan only if the team treats "one canonical Position model" as an
  architecture decision).
- **Candidate note for `docs/memory.md` (Orchestrator to decide):** *The app has no explicit
  `sys.excepthook`; its "print-and-continue" behaviour on slot exceptions is provided incidentally by
  **pyqtgraph**, which is imported before `QApplication` in `main.py`. Any slot bug therefore becomes silent
  log-spam rather than a crash, and offscreen tests can pass while the real path throws.* Separately: *two
  `Position` dataclasses exist (`data.models` with `id`, `ibkr.account` with `market_price`) and are not unified.*

**Pipeline state for the Orchestrator:** two **open, blocking** `BUILD` escalations (ESC-032, ESC-033) — the
pipeline should **pause** for user approval / rework, not advance. The failure is verified, not hearsay; both are
`BUILD`-owned code bugs (ESC-033 a D28.2 regression, ESC-032 a long-standing latent defect newly made live by
D27.5/D27.6). Neither existing escalation (ESC-030/ESC-031) is affected. No live TWS or order path was touched by
this review; only `docs/code_review/` was written.

---

# Review addendum — third live-run error (`QTableWidgetItem` deleted), 2026-10-15

**Reviewer:** Code Reviewer agent. **Tree:** `main @ 29067af`, clean tree. Same out-of-band live TWS session; a
**third** traceback, repeated three times. Nothing fixed; ESC-032/ESC-033 remain `open`. **Method:** reproduced
offscreen against the real `WatchlistPanel` (not from the traceback text); `git blame` for regression status.

## G. Error C — `RuntimeError: wrapped C/C++ object of type QTableWidgetItem has been deleted` — **ESC-034, BUILD, should-fix**

- **Exact failure.** `ui/watchlist_panel.py:992`, the timeout lambda
  `lambda: item.setBackground(QBrush(QColor('#101218')))` — the item it closes over has been deleted.
- **Root cause — stale capture across a table rebuild.**
  - `_flash(row, key, color)` (**`ui/watchlist_panel.py:981-994`**) resolves the *current* cell item
    (`:983 item = self._item(row, key)`), highlights it (`:986`), creates a **single-shot `QTimer` parented to
    the panel** (`:990 timer = QTimer(self)`), **captures that item by closure** in the lambda (`:992`),
    `start(400)` (`:993`), and stores it at `:994`.
  - `_rebuild_table` (**`ui/watchlist_panel.py:674-690`**) replaces **every** cell with a fresh
    `QTableWidgetItem` via `self.table.setItem(row, col, item)` (**`:690`**); Qt deletes the previous item at
    each `(row, col)` (`setColumnCount` at `:680` likewise drops removed-column items).
  - `_rebuild_table` / `_apply_columns` (`:692-696`) **never touch `_flash_timers`** → an in-flight 400 ms timer
    keeps its `(row, key)` entry and its reference to the freed item, and fires against it.
  - **Why the timer outlives the item:** the `QTimer` is parented to `self` (the panel), so its lifetime is the
    panel's; the item's lifetime is the cell's, which ends the moment the cell is replaced.
- **Reproduction.** Real `WatchlistPanel` + fake md manager, offscreen: `add_symbol("AAPL", …)` →
  `_flash(0, "last", GREEN)` → `_apply_columns()` (→ `_rebuild_table`) → event loop past 400 ms →
  **the exact traceback at `:992`**.
- **Who replaces the item (trigger).** `_apply_columns` is reachable **only** from the watchlist header menu:
  `_on_field_toggled` (`:731-742`, add/remove a column) and `_move_field` (`:744-754`, move a column). So it
  fires when the user changes the **column layout** while a flash is pending — and flashes start on *every*
  last-price tick (`on_tick_price` → `_flash`, `:948-950`), so the window is hit often during market hours.
  Three occurrences fit a user toggling a few fields. No programmatic caller exists (grep: only the panel's own
  handlers + tests).
- **Lifetime contract — classification.** This is a **stale-capture lifetime bug** (a closure outliving the C++
  object it captures), *not* a missing-parent bug (the timer's parent `self` is correct) and *not* a
  teardown-order bug (teardown is safe — `closeEvent` calls `watchlist_panel.clear()` at
  `ui/main_window.py:3568`, and `clear` `:899-915` stops+clears every timer before `setRowCount(0)`).
- **`remove_symbol` is NOT the culprit (the task's hint, checked).** `remove_symbol` (`:841-897`) stops the
  removed row's timers (`:874-876`) and re-indexes the surviving `_flash_timers` keys (`:893-896`). I verified
  empirically that flashing then removing an earlier row, removing the flashed row, and `clear()` all leave no
  stale timer (the moved items survive `removeRow` as the same C++ objects). **`_rebuild_table` is the sole path
  that deletes flashed items without invalidating the timers.**
- **Correct fix shape (direction).** Prefer **lazy resolution at fire time**: connect the timeout to a small
  `_unflash(row, key)` that re-resolves `self._item(row, key)` and resets it (or no-ops if gone) — mirroring the
  existing `_set_cell`/`_set_foreground` pattern (`:969-979`) and robust to *any* future item replacement. A
  valid alternative is to **invalidate in `_rebuild_table`** (stop/clear `_flash_timers` before replacing, as
  `clear` already does) — semantically fine because the replacement items start default-coloured. **Merely
  masking** (avoid): `try/except RuntimeError` around the callback, or `shiboken6.isValid(item)` — both silence
  the traceback while keeping a dangling intent that never resets anything.
- **Regression status: not a regression from D22/D23 — it dates to D21's configurable columns.** `git blame`:
  the flash lambda + timer are the **initial commit `90b4539` (2026-09-19)**; the `_flash_timers` keying and
  `_rebuild_table` arrived with **`286341e9` (D21, 2026-10-06)** — the configurable-columns feature
  (`watchlist_panel.py:244` "Columns are configurable (D21.5)") is what introduced item replacement, making the
  latent mismatch reachable. The `remove_symbol` timer handling is the later **`031ea994` (D22 + D23,
  2026-10-07)**, which actually *hardened* removal. So: the lambda predates D21; the bug became reachable in D21;
  D22/D23 did not cause it.
- **User-visible impact — log spam, not breakage.** The replacement item (`:686`) is created with the **default**
  background, so no watchlist highlight is stuck or corrupted and the panel keeps working; the failed callback
  would only have reset the already-discarded old item. So **should-fix**, not blocking.
- **Interaction with ESC-032.** Same *theme* (a Qt slot touching a deleted C++ object) but a different object
  type and lifetime (`QTableWidgetItem` captured by a closure vs an attribute dereference on a wrong-typed
  Python object); no shared cause or shared fix.
- **Why it is log spam rather than a hard failure.** Same mechanism as ESC-032 — `main.py:3` imports
  **pyqtgraph**, whose `Qt/__init__.py:314-318` installs a non-abort `sys.excepthook`, so the QTimer-slot
  exception is printed and swallowed. Verified: a timer-slot exception **aborts** the process without pyqtgraph
  (`exit 134`) and **survives** with it (`exit 0`). Under PyQt's default hook the process would abort instead —
  so this also means a test that drives the flash+rebuild under the event loop can abort the harness (see below).
- **Warranted regression test.** Add a symbol, start a flash (`_flash(0,'last',GREEN)`, or drive
  `on_tick_price` twice so `old is not None`), call `_on_field_toggled(<inactive field>, True)` /
  `_apply_columns()`, run the loop past 400 ms, and assert (a) **an empty record of unhandled exceptions**
  (install a temporary `sys.excepthook` that records — the suite's pyqtgraph hook swallows them, so a bare
  `# no exception` expectation does not exist) **and** (b) the current cell's background is the default
  `#101218`. Test must not rely on the exception propagating to fail it.

## H. Findings and routing (addendum)

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-034 | D21-05 | **BUILD** | bug / **should-fix** | Flash timeout lambda captures a `QTableWidgetItem` that `_rebuild_table` (via a header column change) replaces/deletes; the panel-parented `QTimer` outlives it → `RuntimeError` at `watchlist_panel.py:992`. Not a regression (dates to D21 configurable columns); log spam only. |

- **Owner rationale.** Pure code defect: `_flash` and `_rebuild_table` are correct in isolation; the bug is the
  missing invalidation between them (a lifetime/consistency break). Requirements (watchlist cells flash on
  ticks, `watchlist_panel.py:242`) and the design are fine; not a task-split or architecture issue → **BUILD**.
- **Cross-finding note for the Orchestrator:** ESC-032, ESC-033 and now ESC-034 are all *live-run, no-test*
  defects on paths the 1028-test suite never exercises, and all three are invisible-as-failures because of the
  pyqtgraph non-abort `sys.excepthook` (or, for ESC-033, because the button signal is never exercised). Same
  candidate memory note as before.

**Pipeline state for the Orchestrator:** **three open `BUILD` escalations** — ESC-032 (blocking), ESC-033
(blocking), ESC-034 (should-fix). Pipeline should **pause** for user approval / rework. ESC-030/ESC-031 remain
`addressed`. Only `docs/code_review/` was written; no code/requirements/plan/architecture/task/build file touched.

Status: REVIEW_COMPLETE

---

## Owner symptom: "I have L2 in TWS but can't see depth in the app" — diagnosis (2026-10-15)

**Deliverable:** the plain-language answer and the full evidence live in
`docs/code_review/market_depth_permissions.md` (§ "Follow-up — diagnosis of the user-visible symptom").
This entry records the routed finding only.

**Asked:** *"why can't I see depth in the app when TWS shows it, and why is the error showing"* — replacing the
earlier framing that asked the owner to pick option (a)/(b)/(c).

**Two independent causes, same symptom:**

1. **PROVED (default-ON heatmap).** The heatmap requests SMART-aggregated depth correctly
   (`isSmartDepth=True`, `ibkr/market_depth.py:65`) but `TickerSession.on_depth_error` maps **every** code ≠ 354
   to `"unavailable"` and calls `_cancel_depth()` (`ui/ticker_session.py:786-798` → `:748-759`), tearing down the
   shared feed. Reproduced offscreen: `on_depth_error(2152, …)` → `state='unavailable'`, `req_id=None`,
   `active_feeds 1→0`; panel text "Depth unavailable". So the app discards the entitled-venue book that TWS
   renders. **Already covered by ESC-035 / Q46 — not duplicated here.**
2. **NEW — PROVED code shape, INFERRED consequence (ESC-039).** The Active-Trader ladder pairs a `SMART`
   contract with `isSmartDepth=False` (`ibkr/market_depth.py:25` + `ibkr/contracts.py:187`). Proved offscreen:
   ladder emits `('reqMktDepth', 1, 'SMART', 'STK', 10, False)`; heatmap emits `(…, True)`. IBKR documents
   `False` as *direct routed* ("must name a venue"); a third-party test reports SMART + non-smart returns no
   data. Inferred (not locally verifiable): the ladder stays empty for stocks even without 2152. Ladder feed is
   default-OFF (`ui/main_window.py:252`), so it is not the cause of the blank default view.

**Verdict:** cause 1 is an undefined-behaviour/over-reaction (already ESC-035/Q46 — the fix that *alone* makes
the app show what TWS shows); cause 2 is a distinct code defect.

### Finding and routing

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-039 | — (D18/D35 DOM ladder; not in the current D23 task graph) | **BUILD** | bug / **should-fix** | Ladder requests `reqMktDepth(…, isSmartDepth=False)` on a `SMART` contract — an incoherent pairing per IBKR's direct-routed semantics; likely yields no book even without 2152. `ibkr/market_depth.py:25` + `ibkr/contracts.py:187`; emitted from `ui/main_window.py:2995-3019`. |

- **Owner rationale:** a concrete implementation defect (wrong flag for the contract passed), distinct from the
  ESC-035 policy decision → **BUILD**. If ladder semantics are meant to be per-venue rather than SMART, the
  choice should reach REQUIREMENTS/PLAN first (noted in `suggested_direction`).
- **ESC-035 not duplicated:** it already covers "2152 has no defined behaviour" and remains the single entry for
  cause 1 (owner decision Q46 pending).
- **Proved vs unverifiable:** request shapes, teardown, panel states, defaults and `classify_error(2152)='warning'`
  are proved in-repo (`file:line` above); "IBKR keeps streaming the entitled book after 2152" and "SMART +
  `isSmartDepth=False` returns no data" are IBKR-side facts **not verifiable locally** (flagged in the report).

**Pipeline state for the Orchestrator:** open escalations now include ESC-032/ESC-033 (blocking), ESC-034,
ESC-035, ESC-036, ESC-037, ESC-038, and the new **ESC-039** (should-fix). Only `docs/code_review/` was written;
no code/requirements/plan/architecture/task/build file was touched.

Status: REVIEW_COMPLETE

---

# Review — 2026-10-15 — Owner question: "Do I have the permissions needed for the footprint chart?"

**Reviewer:** Code Reviewer agent
**Reviewed revision:** repo `main` @ `29067af` (working tree carries only docs/`docs/code_review/` edits from
parallel reviewer sessions)
**Scope:** the owner's question only — nothing in `build_log.md` / `failures.json` was re-reviewed, and no
already-reviewed task's files changed since the last `REVIEW_COMPLETE`.
**Method:** read the real source and reproduced the error path offscreen; every claim cites `file:line`.
Nothing was fixed. Investigation written to **`docs/code_review/footprint_permissions.md`** (new file).
**Concurrency:** the two shared files were otherwise quiescent this pass (max id ESC-039); one new entry appended.

## Finding and routing

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-040 | — (D36 footprint; not in the current D22/D23 task graph) | **BUILD** | bug / **should-fix** | `ui/ticker_session.py::TickerSession.on_fp_error` (`:1299-1322`) never resolves an IBKR error on a footprint request to a user-visible state and **explicitly ignores code 162** (`if job is not None and code != 162`, `:1315`) — IBKR's *"No market data permissions"* code for historical data, not pacing-only. Bars stay `loading` forever (`services/footprint_service.py:412-422`; `ui/chart_panel.py:742-745` shows "Footprint loading…" indefinitely); `mark_no_tick_data()` (`:401-404`) is dead code; no test covers the error path. |

### What the owner's question resolves to

- **The footprint does not need the depth (L2) entitlement.** It uses **only** `reqHistoricalTicks`
  (`ibkr/tick_history.py`, whole file), a different request family from `reqMktDepth`. **The owner's L2 gap
  (BATS/NASDAQ/ARCA/BEX/NYSE) is irrelevant to the footprint.**
- **What it does need** (IBKR-documented, not locally verifiable): a **Level 1 / Top-Of-Book** market-data
  subscription for the instrument — the same *class* the ordinary chart bars require, and **different/lighter**
  than L2 depth. IBKR's Historical Time & Sales page: *"Time & Sales data requires a Level 1, Top Of Book
  market data subscription"* (covers both `TRADES` and `BID_ASK`).
- **The app cannot answer this for the user.** Unlike depth (`354 → no_entitlement`, `ui/ticker_session.py:794-795`)
  and news (`reqNewsProviders` → "No API news subscription", `ibkr/news.py:50`, `ui/news_digest_dock.py:146-148`),
  the footprint has **no entitlement probe and no "not subscribed" state** — the inference-only situation is
  itself the finding (ESC-040).

### Proved vs unverified

- **Proved in-repo (`file:line`):** request shape (`ibkr/tick_history.py:35,50-88`; `ui/ticker_session.py:1202-1209,
  1379-1393`); 60-request wave cap (`services/footprint_service.py:46`; `ui/ticker_session.py:1173-1175`) and
  600s/60 pacing (`config/settings.py:35`); proxy contracts (`ibkr/contracts.py:133-138,160-178,181-187`);
  error routing/handling (`ibkr/error_codes.py:12`; `ibkr/client.py:228-245`; `ui/main_window.py:1650-1676`;
  `ui/ticker_session.py:1626-1635, 1299-1322`); states/UI (`services/footprint_service.py:392-404, 412-422`;
  `ui/chart_panel.py:359, 737-745`); the offscreen reproduction (codes 162/354/10197/10168/200 → all bars
  `loading`, `no_tick_data=False`); missing coverage (`on_fp_error` in no test).
- **IBKR-side (documentation, unverified locally):** Level 1 requirement for historical ticks; `162` =
  "Historical market data Service error message" incl. "No market data permissions"; the exact code IBKR emits
  for a missing permission on historical *ticks* (expected 162).
- **Observation, not escalated:** the datetimes are formatted in **UTC** (`services/footprint_service.py:69-71`)
  while IBKR docs say they "use the TWS timezone specified at login" — shared with the bars path
  (`services/backfill_service.py:128-133`), which works in practice, so I could not substantiate a defect.

### Distinctness / not duplicated

- **Not ESC-035** (depth `2152` → `unavailable`, a REQUIREMENTS behaviour decision) — this is the footprint's own
  error path, a different subsystem and symptom (stuck loading, not blank).
- **Not ESC-039** (DOM-ladder request shape). **No request-shape defect found** — the request combination is valid
  (exactly one of start/end set; `numberOfTicks=1000` = IBKR max; `BID_ASK`/`TRADES` Level-1-gated).

**Pipeline state for the Orchestrator:** open escalations now include ESC-032/ESC-033 (blocking), ESC-034,
ESC-035, ESC-036, ESC-037, ESC-038, ESC-039, and the new **ESC-040** (should-fix). Only `docs/code_review/`
was written (`footprint_permissions.md`, `escalations.json`, this log); no code/requirements/plan/architecture/
task/build file was touched.

Status: REVIEW_COMPLETE

---

# Revision 12 review — live-run defect: portfolio shows `HELD` / `H`; options read `STOCK`; `Account: —` — 2026-10-15

**Reviewer:** Code Reviewer agent. **Scope:** a fresh owner report (*"In portfolio I can see `HELD` and
`H` symbol"*) with a positions-table screenshot, diagnosed from the source. Full investigation in
`docs/code_review/portfolio_held_rows.md`. **Method:** read-only dump of the production SQLite DB and
of both `ui/main_window.py::_on_position_update` / `_on_position_end` and
`ui/active_portfolio_panel.py`; introspection of the installed `ibapi` (`9.81.1.post1`);
`config/paths.py` path-selection proof by subprocess. **No live TWS was used by this review.**
Nothing was fixed; only `docs/code_review/` was written (the production DB was opened `-readonly` and
its junk rows were deliberately **not** deleted). **The task-graph is Batch 17 / D23 (`READY_FOR_BUILD`)
and does not cover this report**, so there is no per-task result to review — these are live-run defects
of the same class as ESC-032…ESC-042.

## A. Finding — `HELD`/`H` are persisted production-DB rows, not live positions (ESC-043)

- **Category** `bug` · **root-cause classification** `code_bug` (persistence/isolation + unscoped render)
  · **severity** `should-fix` · **route** `BUILD`.
- **Evidence.** Production DB `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`,
  `positions` table: row id 7 `HELD|DU123|999|stock|10.0|40.0|HELD|1.0|<NULL>|1.7976931348623157e+308|<NULL>`
  (updated 2026-10-15 17:52:07 UTC) and row id 13 `H|DU1|1|stock|1.0|2.0|H|1.0||1.7976931348623157e+308||`
  (17:52:16 UTC). Row 7 is an **arg-for-arg match** for
  `tests/test_d27_account_subs.py::test_d27_6_positions_populate_panel` (`:78-94`);
  row 13 matches no committed test (ad-hoc probe). The live account in the same table is `U13148604`.
- **Why it renders.** `ui/main_window.py::_on_position_end` (`:3319-3335`) selects the **whole**
  `positions` table with no account/qty filter and passes it to
  `ActivePortfolioPanel.set_positions` → `_render_table` (`ui/active_portfolio_panel.py:295-314`). The
  screenshot's 8 rows equal the table's 8 rows exactly.
- **Why it could be written at all.** `config/paths.py::get_db_path` (`:68-81`) returns the user-space
  production path whenever `DB_PATH` is unset (verified by subprocess);
  `tests/conftest.py` (`:8-13`) sets `DB_PATH` to a temp file, so **pytest is hermetic** (verified: the
  temp DB's `positions` table is empty, `sqlite_sequence.seq=1`). Only a **non-pytest** offscreen/REPL
  probe that drives `_on_position_update` reaches the real DB. No seeding path exists.
- **Impact.** Junk shown as holdings; selectable, and actable once ESC-032 populates `id`.

## B. Finding — the position→model mapping reads contract fields that `ibapi.Contract` doesn't have (ESC-044)

- **Category** `bug` · **classification** `code_bug` · **severity** `should-fix` · **route** `BUILD`.
- **Evidence.** `ui/main_window.py:3286/3288/3290` read `class_`, `lastDateOrMonth`, `putCall`; the
  installed `Contract` exposes `secType`, `lastTradeDateOrContractMonth`, `right` and **none** of those
  three (introspection `hasattr == False`). Hence `contract_type` is **always `"stock"`** (every option
  renders `STOCK` and never groups — `active_portfolio_panel.py:271`), `expiry` is always `None`,
  `right` is always `None`; and `strike` (`:3289`) stores ibapi's `UNSET_DOUBLE`
  `1.7976931348623157e+308` when unset. **Already recorded** as an open follow-up at
  `docs/phase-changelog.md:176` and `docs/architecture.md:2524-2525, :2711` but with **no escalation and
  no task**. The test that should catch it, `tests/test_d27_position_prices.py::_held_contract()`,
  fakes the contract with the **same wrong attribute names**, so it cannot fail.
- **One invariant, one escalation:** secType / expiry / right / sentinel-strike are the same defect
  (wrong field names) — bundled, not filed as four cases.

## C. Finding — `Account: —` is an independent summary-plumbing bug (ESC-045)

- **Category** `bug` · **classification** `code_bug` · **severity** `should-fix` · **route** `BUILD`.
- **Evidence.** `ui/active_portfolio_panel.py:262` reads `self._summary.get("Account","—")`, but
  `ui/main_window.py:1219-1224` requests `AccountType,AvailableFunds,BuyingPower,TotalCashValue,
  NetLiquidation` — there is **no `Account` tag**, and IBKR delivers the account id as the callback's
  `account` arg (`_on_account_summary` `:3263-3270` → `self._account_id`), never in `_summary`.

## D. Escalation close-out

All previously open entries were re-checked against the tree: **ESC-032…ESC-042 remain `open`** — none
links to a task that has since reached `done`, and no `architecture.md`/`plan.md`/`requirements.md`
version relevant to them changed this cycle (ESC-032/ESC-033 are today's fresh live-run defects). No
entry closed; no re-diagnosis performed beyond recording the residual. New this pass: **ESC-043,
ESC-044, ESC-045** (all `BUILD`, `should-fix`).

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-043 | n/a (live-run) | BUILD | bug / should-fix | `HELD`/`H` are fixture rows persisted in the **production** `positions` table by a non-hermetic offscreen run; the panel renders the whole table unscoped (no account/qty filter) |
| ESC-044 | n/a (live-run) | BUILD | bug / should-fix | `_on_position_update` reads `class_`/`lastDateOrMonth`/`putCall` — not real `Contract` fields — so options read `STOCK` (never group) and expiry/right are always None; unset `strike` stores the `UNSET_DOUBLE` sentinel |
| ESC-045 | n/a (live-run) | BUILD | bug / should-fix | `Account: —` because the request omits/needs no `Account` tag while `_render_summary` reads `_summary["Account"]` |

**Pipeline state for the Orchestrator:** open escalations now number **14** (`ESC-032`…`ESC-045`); the
two `blocking` ones remain **ESC-032** (missing `Position.id` → live render aborts) and **ESC-033**
(Load-Chart button). New this pass are **ESC-043/ESC-044/ESC-045** (all `BUILD`, `should-fix`, none
blocks a task). Only `docs/code_review/` was written (`portfolio_held_rows.md`, `escalations.json`, this
log); no code, requirements, plan, architecture, task, or build file was touched, and the production DB
was opened read-only.

Status: REVIEW_COMPLETE

---

# D41 removal batch (Batch 18) review — 2026-10-15

**Reviewer:** Code Reviewer agent. **Scope:** `docs/build/build_log.md` (Batch D41, ends `Status: READY_FOR_REVIEW`,
65/65 done, 0 blocked) and the 39 tasks scoped by `docs/code_review/precheck.json`. Reviewed the uncommitted D41
diff (working tree vs `29067af`) for each task's `files_changed`; read full files only where the diff was
ambiguous. **No live TWS** — every run was `QT_QPA_PLATFORM=offscreen`; suite run as
`.venv/bin/python -m pytest` (the `.venv/bin/pytest` entry point has a stale shebang). Mechanical facts
(`files_changed` vs git, footprint vs `touches_files`, the doc scan) are taken from `precheck.json` as ground
truth and **not** re-derived; judgment findings below were independently reproduced.

## A. Verdict

The D41 removals are correct and thorough; the KEEP-list substrate survives; the load-bearing order-gate
re-homing is right. **Two findings**, both test-determinism/hygiene (not product defects): a **newly observed
full-suite flake** in `tests/test_d27_reconnect.py` (**ESC-046**, should-fix) and the previously-noted
thread-unsafe global `time.sleep` monkeypatch in `tests/test_d28_pacing.py` (**ESC-047**, nice-to-have).
**ESC-035/ESC-039/ESC-040 are moot → closed.** The re-homed gates, the D38/D39 KEEP list, the footprint-table
drop, the doc-only `subscription_manager.py` edit, and the `conftest.py` per-process DB were all independently
verified.

## B. The re-homed order gates (P1-T65) — VERIFIED

`ui/main_window.py::_close_position_by_id` (`:3072-3157`) is now, in order: (1) the D26.9 disconnected guard
(`:3083-3086` — refuse + status, **before** the row read and before any pacing token); (2)
`validate_order(action, "MKT", qty, symbol, ref_price=self._ref_price_for(symbol), risk_reducing=True)`
(`:3111-3119`) — refusal surfaced as `"Order rejected: …"` before the pacing deferral; (3)
`order_limiter.try_acquire()` pacing deferral (`:3143-3151`); (4) `placeOrder` (`:3154`). `_ref_price_for`
(`:2095-2104`) is an upper-case-normalised read of `_symbol_last_prices`, `None` for unknown.
`ibkr/validation.py::validate_order` gained the additive `risk_reducing` keyword; the notional cap is skipped
**only** when `risk_reducing` is true (`:69-76`) — every structural check is unchanged. `_place_order` /
`_on_order_place_requested` are gone, and `validate_order`'s only production caller is `_close_position_by_id`
(grep: `validate_order` at `:37` import + `:3111`; `placeOrder` only at `:3154`).
`tests/test_d41_retained_order_path.py` exercises all four gate cases (disconnected refuse, invalid refuse,
valid-above-cap transmit-once, risk-increasing-still-rejected) and is discriminating — the disconnected/invalid
cases fail against a guard-less implementation. **No escalation.**

## C. KEEP list (AC-D41.4) — VERIFIED intact

`footprint_cache_key` (`ibkr/contracts.py:144`, used `ui/ticker_session.py:706`), `INDEX_PROXY`
(`ui/alarm_dialog.py`, `services/alarm_monitor.py`), `md_line_guard.assess` (`ui/main_window.py:89`), the S0
substrate, and `volume_baseline` are all present and exercised. The `footprint_cache` DDL is removed from
`data/db.py` and `DROP TABLE IF EXISTS footprint_cache` added to `_migrate_schema` (`data/db.py:174`). All nine
deleted modules and five deleted suites are absent (`find_spec`/path checks in `tests/test_d41_removal.py`).
Import probe: `ui.chart_panel`, `ui.ticker_session`, `ui.main_window`, `ui.watchlist_panel`,
`ui.active_portfolio_panel`, `ibkr.*`, `data.*`, `services.md_line_guard` all import cleanly; AST parse OK.
Residue grep for 16 removed tokens (`FootprintItem` … `ensure_depth_subscribed`) → 0 hits outside `__pycache__`.

## D. Provenance / orchestrator-completed tasks — VERIFIED

The 8 `footprint_flags` in the results JSONs for the orchestrator-completed tasks
(`P1-T09/10/11/18/27→split/35/36/38/41/66`) were read. The two files left non-importable mid-edit
(`ui/chart_panel.py`, `ui/ticker_session.py`) are now import-clean with no dangling references (B/C above). The
D10/D13 and dock suites are green (E). The `P1-T41`/`P1-T66` overlap on `tests/test_d10_d13_integration.py` is
benign: P1-T66 added a bounded `_settle_dock_clamp` drain (80 turns **and** a 5.0 s monotonic deadline) between
the overshoot drag and the width asserts; the asserts (`>= CHART_MIN_WIDTH`) are unchanged.

## E. Independent suite evidence

- Targeted D41 suites: `test_d41_removal` + `test_d41_portfolio_dock` + `test_d41_retained_order_path` +
  `test_db_schema` + `test_d28_pacing` + `test_d28_6_close_contracts` + `test_d27_reconnect` +
  `test_d10_d13_integration` → **38 passed**.
- Full suite: **967 passed** on 2 of 3 runs; **1 failed** on the third (`test_d27_reconnect`). HEAD (`29067af`,
  pre-D41) full suite → **1028 passed** on 3/3 runs. See F for the flake.

## F. Findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-046 | P1-T59 | BUILD | quality / **should-fix** | Full suite intermittently red: `test_d27_reconnect.py::test_d27_3_drop_reconnect_reissues_with_rebound_reqids` `assert len(fake.rt_bars) == 2` sees 4 because `_on_connected()` restores a persisted pop-out (`POPA`) whose session subscribes RT bars through the test's recording fake; violates AC-D41.5's "suite green". |
| ESC-047 | P1-T52 | BUILD | quality / nice-to-have | `test_d28_pacing.py` monkeypatches the **global** `time.sleep`; the D38 yfinance worker QThread (`data/events/yfinance_source.py:256`) can sleep on its own thread and append to the captured list → false red. |

### F1 — ESC-046 (new full-suite flake, `test_d27_reconnect`)

- **Reproduction.** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → intermittent
  `1 failed, 966 passed`; failure `tests/test_d27_reconnect.py:209 assert (4 == 2)` where
  `4 = len([38, 40, 43, 45])`, `rt_id_1 = 40` (so `fake.rt_bars` already held **two** entries at line 197).
  Passes 4/4 in isolation; fails 3/3 full-suite runs with `-x`. HEAD (pre-D41) full suite 3/3 green.
- **Root cause (instrumented, not inferred).** A reviewer probe wrapping
  `ibkr.realtime_bars.RealtimeBarsManager.subscribe` shows, under the failing test, **four** subscribes —
  `POPA`×2 and `TEST`×2 — versus `TEST`×2 on a passing run and at HEAD. `win._on_connected()` →
  `_restore_popouts()` (`ui/main_window.py:1057,796`) reopens a persisted pop-out whose record names symbol
  `POPA` (the only file that uses `POPA` is `tests/test_d24_popouts.py`; persistence is
  `data/popout_store.PopoutStore`). That pop-out's session subscribes RT bars through the same
  `win.rt_manager` the test fakes (`win.rt_manager.client = fake`), so the test's `len(fake.rt_bars) == 2`
  counts the pop-out's sub too (once on restore, once on the reconnect replay). The pop-out record survives
  into this test despite the per-test `popouts` wipe — a pre-existing test-isolation gap (D24), newly
  *observable* here because D41's collection changes let it survive into this test.
- **Suggested direction.** Make the reconnect assertion count only the chart session's RT subs (e.g. filter by
  the primary session's reqId), and/or isolate the pop-out store between tests (wipe/neutralise
  `_restore_popouts` in the harness). Do **not** weaken the rebound / one-new-reqId guarantee.

### F2 — ESC-047 (thread-unsafe global `time.sleep` monkeypatch)

- **Mechanism verified; the red was not independently reproduced.** `tests/test_d28_pacing.py:97` does
  `monkeypatch.setattr(time, "sleep", lambda s: sleeps.append(s))` then asserts `sleeps == []` (`:107`).
  `data/events/yfinance_source.py:256` calls `time.sleep(gap)` on its own `QThread` (the D38 event source,
  `_MIN_CALL_GAP_S = 1.0`, `:33`); if that thread is mid-task during the test, its sleep lands in the global
  `sleeps` list and the assertion fails on an unrelated thread. Both halves predate D41. In my runs the full
  suite failed only via ESC-046 (never this test), consistent with the brief's "1/4 runs".
- **Suggested direction.** Scope the capture to the GUI thread (patch `MainWindow`'s sleep reference, or record
  the calling thread and assert only main-thread sleeps), or assert the observable deferral (status message +
  one deferred subscribe) instead of "no sleep anywhere".

## G. Non-escalation observations (recorded, no action)

- **Dead-but-retained `bracket_order` (P1-T53).** `ibkr/orders.py::bracket_order` now has **zero production
  call sites**: the only production `placeOrder` is `_close_position_by_id` → `order_registry.market_order`
  (`ui/main_window.py:3154`); the SL/TP handlers (`_on_portfolio_sltp_changed` `:3020`,
  `_on_portfolio_group_sltp_changed` `:3032`) persist to the DB only. This is an **accepted KEEP-list
  outcome** — `AC-D41.4` and the D41 "Scope — KEEP" list explicitly retain `bracket_order` ("incl.
  `bracket_order`") and require it "present and exercised", and P1-T53 correctly re-points D26.8's
  all-three-legs coverage at the builder. No code change is warranted. The residual is a
  **requirements-wording nuance** only: the D41 entry's rationale that the SL/TP dialogs "place orders
  through it" does not hold (they persist only), so the Requirements Analyst may wish to state explicitly on a
  later pass that `bracket_order` is retained-but-currently-unreachable. **Not escalated** — the retention
  decision is explicit and unaffected, and a separate entry would pause the pipeline for a doc nuance.
- **Coverage that moved rather than disappeared (P1-T54, P1-T59).** P1-T54 dropped `test_order_validation.py`'s
  two `_place_order` wiring tests; the gate's wiring is now carried by
  `tests/test_d28_pacing.py::test_close_position_defers_when_limiter_empty` (which pins gate→pacing→transmit)
  and `tests/test_d28_6_close_contracts.py`, recorded in the module docstring. P1-T59 dropped the DOM half of
  `test_d27_reconnect.py`; the retained RT/S0/watchlist rebound coverage is intact. Both are legitimate
  re-homings for removed features, not weakened assertions.
- **Doc-only out-of-footprint edit (P1-T60).** `ibkr/subscription_manager.py`'s module docstring + the
  `DEPTH`/`DEPTH_HEATMAP` tag removal are docstring/constant-only (verified by the diff: no behaviour change;
  the two tags had no remaining consumers). Legitimate.
- **`tests/conftest.py` (P1-T66).** Now `mkdtemp(prefix=f"ndtc_test_db_{os.getpid()}_")` with nothing removed;
  the autouse `_isolate_test_db` table list and post-test wipe are byte-for-byte unchanged, and no path is
  deleted that the process did not create. Legitimate (fixes the wave-wide `attempt to write a readonly
  database` race). Minor: the per-process temp dirs are never cleaned up — acceptable, out of scope.

## H. Escalation close-out

- **ESC-035 (depth 2152), ESC-039 (ladder `SMART` + `isSmartDepth=False`), ESC-040 (footprint `on_fp_error`)**
  → **`addressed`** (edited in place, `verified:` line added). Independently re-verified on the live tree: the
  code each targets is gone — `on_depth_error`, `on_fp_error`, `mark_no_tick_data`, `MarketDepthManager`,
  `subscribe_shared`, `reqMktDepth`, `isSmartDepth`, `FootprintService`, `"2152"` → 0 occurrences;
  `ibkr/market_depth.py`, `ibkr/order_book.py`, `services/footprint_service.py`, `data/footprint_cache.py`,
  `ui/footprint_item.py`, `ui/depth_heatmap_item.py`, `services/depth_heatmap.py`, `ibkr/tick_history.py`,
  `ui/active_trader_panel.py` all absent. The features are removed, so the findings are moot (as
  `requirements.md` itself records).
- **ESC-032, ESC-033, ESC-034, ESC-036, ESC-037, ESC-038, ESC-041, ESC-042, ESC-043, ESC-044, ESC-045 remain
  `open`** — none is D41's work, and the D41 diff does not change my assessment of any (it touched none of
  their cited code paths). Not re-diagnosed; left open.
- **ESC-030, ESC-031 remain `addressed`** (unchanged).

## I. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-046 | P1-T59 | BUILD | quality / should-fix | intermittent full-suite red in `test_d27_reconnect.py` (persisted pop-out `POPA` subscribes an extra RT bar through the test's fake) |
| ESC-047 | P1-T52 | BUILD | quality / nice-to-have | thread-unsafe global `time.sleep` monkeypatch can capture the D38 yfinance QThread's sleep |

**Pipeline state for the Orchestrator:** the D41 batch is complete (65/65 done) and the removals are correct.
Open escalations: **ESC-046 (BUILD, should-fix)**, **ESC-047 (BUILD, nice-to-have)**, plus the pre-existing
ESC-032…ESC-045 (not D41's work). ESC-035/039/040 closed. The suite is green on most runs but **not
deterministically** (ESC-046), so AC-D41.5's "suite green" evidence is not yet reliable.

# Revision 16 review — Batch D41 rework verification (ESC-046 / P1-T59, ESC-047 / P1-T52), 2026-10-15

**Scope (incremental, per `docs/code_review/precheck.json`):** only the two tasks whose results are newer than my
last `REVIEW_COMPLETE` — **P1-T59** (`tests/test_d27_reconnect.py`, ESC-046) and **P1-T52**
(`tests/test_d28_pacing.py`, ESC-047). Both `done`, both 1/1 and 2/2 pass, 0 fail_fast, 0 precheck escalation
entries. Everything else in D41 is already reviewed and is **not** re-opened. Reviewed against the live working
tree (uncommitted D41 diff), not the workers' reports. All runs `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`.

## A. ESC-046 / P1-T59 — pop-out restore neutralised in the D27.3 reconnect harness — **VERIFIED, CLOSED**

- **The fix (read + `git diff`).** `tests/test_d27_reconnect.py::_make_window` now sets
  `win._restore_popouts = lambda: None` (line 164) before `win.show()`. `_on_connected()`
  (`ui/main_window.py:1060`) therefore cannot restore a leftover persisted `POPA` record, so every subscription the
  recording `_FakeTws` sees is the **chart session's own**. The stub is instance-scoped to the window under test and
  is a genuine neutralisation of the restore path for this suite, not a counter tweak.
- **The invariant's assertions are present and unweakened.** The reconnect block still asserts, verbatim:
  `len(fake.rt_bars) == 2 and fake.rt_bars[1] != rt_id_1` (exactly one new reqId); `_surviving_mkt_lines == 2`
  and `len(fake.mkt_data) == 2 * _surviving_mkt_lines` (watchlist row + session S0 each re-issued once per
  connect — the count is re-derived from live routing state, not hard-coded); `set(fake.mkt_data[2:]).isdisjoint(
  fake.mkt_data[:2])`; `win._rt_req_id == rt_id_2` ("stale RT reqId not rebound"); `primary_session.s0_req_id in
  fake.mkt_data[2:]` (S0 rebound); the watchlist row rebound with `len(win.watchlist_panel._req_to_row) == 1`;
  bars flow on the rebound `rt_id_2` (price 11.5); the **stale pre-drop `rt_id_1` is ignored** (price stays 11.5);
  and `win._current_symbol == "TEST"` (no manual reload). Nothing was deleted or narrowed to make the count pass.
  The only other test-content change since the last review is the already-accepted wave-37 DOM-depth removal (the
  feature is deleted by D41).
- **Not a masked product defect.** `_restore_popouts()` itself remains genuinely covered —
  `tests/test_phase3_fixpass.py::test_fix3_restore_popouts_no_duplicates_on_reconnect` drives `_on_connected()`
  twice with a persisted pop-out and asserts no duplicate window; `tests/test_d24_9_popout_persistence.py` covers
  the store save/load/delete and open/close persistence. I also checked the one plausible hidden defect —
  "a closed pop-out's deferred geometry save re-persists it" — and it does **not** exist: `ui/popout_window.py`
  sets `WA_DeleteOnClose` (line 59), and my own probe showed that after `pop.close()` the pop-out's `QTimer`
  C++ object is deleted and no `popouts` row is re-saved (the debounce timer dies with the window). The leftover
  `POPA` row is therefore a **test-lifecycle** leak (a pop-out left open by a D24 test whose 500 ms geometry
  single-shot fires after the autouse teardown wipe), not a product defect. It is now harmless to this suite.
  (I tried to reproduce the residual leak directly — ran `tests/test_d24_popouts.py tests/test_d28_pacing.py` and
  inspected the per-process test DB — and the `popouts` table was empty at exit; the leak is nondeterministic and
  not currently observable, so it is recorded as an observation, not an escalation.)
- **Determinism (my own runs).** 2 consecutive **full** offscreen suites: `967 passed`, EXIT=0 (23.5s each).
  Plus 3 isolated runs and 1 `-x` run of `tests/test_d27_reconnect.py tests/test_d28_pacing.py`: `12 passed` each.
  With the orchestrator's 3 and the worker's 4/4, this is 10+ consecutive green runs. AC-D41.5's "suite green"
  evidence is now reliable.

## B. ESC-047 / P1-T52 — GUI-thread-scoped sleep capture, D28.1 guarantee preserved — **VERIFIED, CLOSED**

- **The fix (read + `git diff`).** `tests/test_d28_pacing.py::_capture_gui_sleeps` (lines 18-37) records
  `time.sleep` only when `threading.current_thread() is threading.main_thread()` and never sleeps. **All three**
  sleep-patching tests use it (`test_subscribe_raises_pacing_exceeded_without_sleep` :77,
  `test_attach_live_feed_defers_with_status_and_retries` :118,
  `test_close_position_defers_when_limiter_empty` :167); no bare `monkeypatch.setattr(time, "sleep", ...)` remains
  in the file (grep). This matches the brief's "all three sleep-patching tests".
- **Still genuinely falsifiable (my own probe).** Loading the module and exercising the helper directly: a
  main-thread `time.sleep(0.01)` **is** recorded (`sleeps == [0.01]`); a worker-thread `time.sleep(0.01)` is **not**.
  So a GUI-thread sleep still fails the `sleeps == []` assertion — the capture was not narrowed into something that
  can never fail. The guard protects a real sleep site: `ibkr/pacing.py:40` (`PacingManager.throttle` →
  `time.sleep`), reached from `ibkr/market_data.py:75/91/104` on the GUI thread. The D38 contaminant this excludes
  is confirmed present: `data/events/yfinance_source.py:256` `time.sleep(gap)`, `_MIN_CALL_GAP_S = 1.0` (:33).
- **P1-T52's original re-point intact (read + `git diff`).** `test_close_position_defers_when_limiter_empty` still
  (a) drives a gate-rejected blank-symbol close and asserts **no transmit and no "pacing-limited" status** (proving
  gate → pacing → transmit), (b) asserts the retained close defers with no GUI-thread sleep and a pacing-limited
  status, (c) asserts **exactly one** transmit after the deferred retry; seeded `positions` rows are deleted in a
  `finally` block (no leak into the shared DB — the ESC-043 lesson). No assertion removed or narrowed.
- `tests/test_d28_pacing.py` 8 passed (isolated pair 12 passed, ×4 runs).

## C. Escalation close-out

- **ESC-046 → `addressed`** (edited in place, `verified:` line added) — see A. Independently re-verified.
- **ESC-047 → `addressed`** (edited in place, `verified:` line added) — see B. Independently re-verified.
- **ESC-032…ESC-045 remain `open`/`addressed` exactly as before** — none is D41's work; the two D41 files reviewed
  here touch none of their cited code paths. Not re-diagnosed.

## D. New findings

None. Both invariants hold on the live tree; neither fix was superficial (no assertion removed, narrowed, or made
unfalsifiable), and neither masks a product defect.

**Pipeline state for the Orchestrator:** the D41 rework is complete and verified. ESC-046 and ESC-047 are closed;
the only remaining open items are the pre-existing ESC-032…ESC-045 (not D41's work, open by design). The full
offscreen suite is deterministically green (967 passed, EXIT=0, 2/2 of my runs). No D41 blocker remains.

Status: REVIEW_COMPLETE

---

# Batch D42 (Batch 18b) — Code Review

Scope: all 23 tasks (fresh batch; `precheck.json` scoped 23, 0 fail_fast, 0 precheck escalations). 22 `done`,
1 `blocked` (P2-T23). Method: diff-first on each task's `files_changed`; failures reproduced with the task's own
command; every production claim I relied on spot-probed offscreen (`DB_PATH`=tempfile per the ESC-043 rule).

## A. THE CENTRAL FINDING — 19 D42-induced regressions + P2-T23's own guard → BUILD (blocking) + PLAN (should-fix)

**Reproduced independently (my own runs):**

- D42 tree: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` → **exit 1, 20 failed** — exactly the 19 the
  P2-T23 report names plus `tests/test_d42_nonregression.py::test_full_offscreen_suite_is_green`. No other failure.
- Pre-D42 tree (`git worktree` at HEAD `b48133d`): the same six suites → **exit 0, 18 passed**.
- Mechanism confirmed: each suite stubs `req_historical_data` with a **fixed-size** id iterator —
  `test_d24_popouts.py:22-23` (`iter([6101,6102,6103])`), `test_d24_9_popout_persistence.py:54-55` (`iter([7101])`),
  `test_d24_alarm_full_chain.py:39-40` (`iter([8101,8102])`), `test_d24_smoke_gate.py:37-38` (`iter([9601,9602])`),
  `test_d28_tick_burst_baseline.py:31-32` (`iter([9101,9102])`), `test_phase3_fixpass.py:33-34`
  (`iter([7101,7102,7103])`) — all `lambda *a, **k: next(hids)`. D42's `ui/main_window.py:1649-1672` now always
  consults the planner with `min_sessions=settings.MIN_INTRADAY_SESSIONS`, so an intraday load issues many chunks
  (my probe: an empty-cache 5-min load plans 9 requests), and the second `next(hids)` raises `StopIteration`.
  Trimmed traceback reproduced: `tests/test_d24_9_popout_persistence.py:55` ← `ui/main_window.py:1670` →
  `ui/ticker_session.py:876`.

**Judgement / routing:**

- The production behaviour is requirements-mandated (AC-D16.8/AC-D16.9; chained requests per `S17`) — **not** a code
  bug. The correct fix is the suites' stubs widened to an unbounded id source (`itertools.count`), exactly the
  P2-T19 precedent (`tests/test_d28_2_sessions.py:41`). The affected tests must not be weakened/skipped/xfailed.
  → **ESC-048, BUILD, blocking** (one escalation for the whole invariant, not 19 per-case patches).
- The reason 19 suites were missed is the plan's impact analysis: `S21`/`RC-D42-2`/`AR-D42-6` and the Phase-2 file
  map for `ui/main_window.py` enumerated only the D16 load-path suites and implicitly treated every other
  load-path-driving suite as unaffected. `AR-D42-6`'s mitigation claims *every* changed load-path assertion is
  enumerated — it is not (and `RC-D42-2`'s own table under-counted 4 further sites inside the files it named:
  `t40_t03`, `t40_t05`, `t43_t03`, `t44_t03`). → **ESC-050, PLAN, should-fix**.
- ESC-048's six files are outside P2-T23's `touches_files`; the Task Manager must widen the footprint (or a task
  must own them) before a re-dispatched worker can edit them — stated in the escalation.

## B. Production code — one gap found → BUILD (should-fix)

**The session's mode is only established by `queue_wave_plans`, so a load that issues no wave caps an ETH series
at the RTH budget (in-memory depth falls below the AC-D16.8 floor).**

- `ui/ticker_session.py:131` initialises `_wave_extended_hours = False`; it is assigned **only** at `:866` inside
  `queue_wave_plans`. `set_bars`/`_append_bar` (`:309`, `:323`) and the D39 baseline preload (`:695`) all derive
  their cap/mode from it (repo-wide grep: no other assignment).
- `ui/main_window.py::load_chart` calls `new_session.set_bars(timeframe, cached)` at `:1634` **before**
  `queue_wave_plans` (`:1670`), and calls `queue_wave_plans` only when `plans` is non-empty (`:1666`). So a load
  whose cache already satisfies the floor (the common re-load, or a mode toggle on a cached symbol) never sets the
  mode, and the initial cap uses RTH.
- Offscreen probes: with 40 ETH sessions / 7,680 cached 5-min bars and a fully satisfied floor (**0** requests
  issued), `load_chart` in ETH mode leaves `session._wave_extended_hours == False` and the in-memory series holds
  **5,000** bars (the RTH budget) while the ETH budget is **6,624**. Control: pre-setting the session's mode to ETH
  gives **6,624** (and confirms it is the same session object).
- Impact: breaches AC-D16.8's in-memory depth on the no-wave path — worst for `1 min` ETH (RTH budget 13,455 vs ETH
  33,120 → ~14 sessions instead of ~34). No D42 guard covers it: P2-T22 asserts the **post-wave** path only, where
  `queue_wave_plans` has already set the mode. Not a regression (pre-D42 was flat 5,000) but an incomplete
  implementation of `S18`/`S19`. → **ESC-049, BUILD, should-fix**.

## C. Quality review — verified sound (no findings)

- **WS1 helper** `capped_body_half_width` (`ui/candlestick_item.py:47-64`) is pure/Qt-free, implements
  `w = min(max(base, floor_px/2/px_per_sec), median_diff/2)` ≡ `body = min(max(0.65·pitch, F), pitch)`. Both
  `_draw_candles` (`:190`) and `ChartPanel._clamp_half_width` (`ui/chart_panel.py:1261-1273`) call it, so candle and
  volume widths cannot diverge (AC-D9.1). `_median_time_diff` extracted and reused; `set_data` gained the `pitch`
  keyword threaded to the renderer.
- **Corrected suites remain discriminating** (re-read + run green):
  - `test_volume_width.py` dense legs: `measured_body ≈ pitch`, `pitch - vol_width >= 0`, `vol_width ≈ measured_body`
    — a revert to the old unconditional 4-px clamp fails `≈ pitch`.
  - `test_chart_dpi.py`: `>= 4.0` / `> wick` moved to the non-dense dataset; dense asserts `body <= pitch` and
    `body == pitch` (rel 0.05) — a revert fails.
  - `test_d28_2_sessions.py::test_session_bar_cap`: derives `floor_bar_budget(TF, True)` and asserts
    `budget > SESSION_BAR_CAP` — discriminating.
  - `test_d28_4f_panel_bar_cap.py`: asserts the derived budget (6,624) with oldest-dropped/newest-kept — a flat-5000
    revert fails.
  - `test_candle_spacing.py`: now regime/geometry assertions on the helper (three regimes + the 35 % gap), no longer
    a source-string check.
  - `test_d42_candle_width.py::test_guard_discriminates_against_pre_fix_flat_floor` asserts `FLOOR_PX (4.0) >`
    measured pitch as a precondition, so the repro genuinely discriminates.
- **New guards are real**: `test_d42_depth_floor.py` drives the real load path (unbounded stub) and asserts ≥30
  mode-valid sessions in cache **and** memory, per timeframe × mode; its T21 case asserts
  `floor_bar_budget > RETENTION_BARS` **and** `len(timestamps) > RETENTION_BARS` (a flat keep would prune the floor).
  `test_d42_day_presence.py` asserts the AC-D16.9 (a)/(b)/(c) measurables. `test_d42_mode_cache.py` exercises the
  real `DB()` migration (verbatim row preservation, `ext_hours=1` tag, idempotent reopen) and per-mode isolation
  both directions.
- **`test_d42_nonregression.py` T11/T21 are real**: T11 asserts the four Friday year-ends preceding Saturday New
  Years are trading days (Rule 7.2 exception); T21 asserts a genuine closure stays empty + a present-but-mode-empty
  day is reported missing under RTH and present under ETH, and that `_missing_backfill_trading_days` agrees with the
  planner. Both pass.
- **Mock-endpoint containment** (standing invariant): grep of the production diff (`ui services data ibkr config`)
  for `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness` → **0 hits**. No mock in production.
- **`data/db.py`** S16 migration is PRAGMA-guarded, idempotent, salvages a leftover `bars_new` from an interrupted
  rebuild, copies every legacy row as `ext_hours=1`, deletes nothing. **`data/bar_cache.py`** threads `ext_hours`
  through save/get/prune with the flat default preserved.

## D. P2-T15 corrections — intent-preserving (one unnecessary relaxation → nice-to-have)

Re-read all three diffs. All seven corrections keep the guarantee: `t40_t01` (`>= 1` + delivered-set), `t40_t03`
(closure days never named missing), `t40_t04` (`>=` + delivered-set + answered days not reported missing),
`t40_t06` (all `endDateTime` non-empty + tracked ids), `t43_t03`/`t44_t03` (seeded days asserted against the log's
full list; `"incomplete"` still required), `t43_t06` (all ids driven; finalises once). The loadpath file's
corrections are net-**stronger** (both modes parametrised, `len(spans) == 1`, `len(stub.calls) == len(plans) > 1`).

- **One unnecessary relaxation**: `tests/test_history_backfill.py:285` changed `assert len(plans) == 1` →
  `assert plans`. `plans` is the test's **own** planner call (`find_missing_spans(cached_ts, _AC_NOW, tf)`, no
  `min_sessions`) — unchanged by D42; my probe confirms it still returns exactly **1**. The delivered-set assertion
  preserves the AC-D16.5 guarantee, so this is cosmetic. → **ESC-051, BUILD, nice-to-have**.

## E. Usage-doc coverage

Identified the project's user docs: `USAGE.txt` (238 lines, "NDThinkChart Usage") and `usage.md` (221 lines,
"NDThinkChart — Usage Guide"); both untouched by D42 (`precheck.json` `doc_candidates`, all `touched: false`).
D42 changes user-visible behaviour (intraday history depth now ≥30 sessions; candle/volume width at high density),
but neither doc describes the affected behaviour at all (no mention of load depth or candle body width), so no doc
statement became wrong and **no update is required for D42**. **Observation (out of D42 scope, not escalated):**
`USAGE.txt` still documents the D36 footprint and D37 depth-heatmap features that D41 removed (lines 130-169) — a
pre-D41-batch staleness worth a follow-up outside this review's scope.

## F. Provenance (5 orchestrator handoff-writes + 1 mid-task finish)

`P2-T01`, `P2-T02`, `P2-T09`, `P2-T14`, `P2-T19` had their handoffs written by the orchestrator after a worker death
with the work complete; `P2-T15` was finished mid-task. The `footprint_flags` state the verification performed:
P2-T22's mutation check (zeroing `MIN_INTRADAY_SESSIONS` → rc 1) shows its guard is discriminating; P2-T01's AC2 is a
render-level `QPicture` measurement. `P2-T06`/`P2-T22` were blocked on thin packs, repaired by the Task Manager
(`MAP_OK`), re-dispatched, and are green. I independently re-verified the two load-bearing claims (the 19-suite
regression, and the WS1/WS2 fixes) rather than trusting the handoffs.

## G. Escalation close-out (all four re-verified on the live tree)

- **ESC-042 → `addressed`**: `requirements.md` records the precedence decision (AC-D6.4 revised to
  `body = min(max(0.65·pitch, F), pitch)`, AC-D7.1 revised to `gap >= 0`, supersession recorded, Q51 answered).
  Code + guard match (`test_d42_candle_width.py`).
- **ESC-038 → `addressed`**: `requirements.md` records AC-D16.8 (≥30 sessions; extended to ETH by Q52) and AC-D16.9
  (present-but-mode-empty = missing span); implemented by P2-T07–T14, guarded by `test_d42_depth_floor.py` /
  `test_d42_day_presence.py`.
- **ESC-041 → `addressed` (BUILD)**: render-level re-measure at the ESC-041 repro — pre-D42 `body 4.014 > pitch
  3.835` (overlap); post-D42 `body 3.835 == pitch 3.835` (gap 0). Fix real; guard real.
- **ESC-037 → `addressed` (BUILD)**: pure re-check of the ESC-037 repro — pre-D42
  `find_missing_spans(pre/post-only day, now, '5 mins', ext_hours=False)` span starts 2024-05-07 (the seed day was
  treated as present = the bug); post-D42 starts 2024-05-06 (the day is reported missing). Fix real.
- **ESC-032/033/034/036/043/044/045 remain `open`** — not D42's work; the D42 diff touches none of their cited code
  paths (D42 edits the `bars` cache/db, the backfill planner, the load path and candle/volume width — not
  positions/account/watchlist/aggregator-priming). Not re-diagnosed.
- **ESC-039/040/046/047 remain `addressed`** (D41 batch) — untouched.

## H. Pipeline state for the Orchestrator

One blocking escalation (ESC-048) and one should-fix production finding (ESC-049), plus the PLAN enumeration finding
(ESC-050). The full offscreen suite is red solely via the 19 stubs + P2-T23's own T31 guard; once ESC-048 is applied
P2-T23-T31 must be re-run to confirm green.

Status: REVIEW_COMPLETE

---

# Batch D42 (Batch 18b) — Code Review, rework verification (ESC-048 / ESC-049 / ESC-050 / ESC-051), 2026-10-16

**Scope (incremental):** only the tasks whose `docs/build/results/<id>.json` is newer than the last
`REVIEW_COMPLETE` — **P2-T23, P2-T24, P2-T25, P2-T26** (the Stage-A rework; `precheck.json` also scopes
`P2-T14`/`P2-T15`, whose re-runs are the same work) — plus the **Plan amendment** (not a task). Consumed
`precheck.json` as ground truth (scope, `files_verified`, overlaps, `escalation_updates`); did not re-run
git-diff/footprint/doc-discovery. Method: diff-first on each task's `files_changed`; failures/guards reproduced
with my own runs; the one discrimination claim I could not read off the diff was reproduced in a temp copy of the
tree (no repo file edited). All runs `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (`.venv/bin/pytest`
has a stale shebang), `DB_PATH` pinned by `tests/conftest.py`.

## A. ESC-048 (BUILD, blocking) — the 19 regressions → P2-T24 — **VERIFIED, CLOSED**

- **Fix is exactly the invariant-preserving one.** `git diff` over the six suites shows only: `+import itertools`,
  a 2-line "D42's depth floor (S17) can issue many chunks" comment, and `hids = iter([...])` →
  `hids = itertools.count(<first>)`. The lambda `lambda *a, **k: next(hids)` and **every assertion** are
  byte-identical; `grep` of added `skip`/`xfail` lines in the diff → **0**. No assertion weakened, skipped or
  xfailed — the failure was fixture exhaustion, as the escalation said.
- **Six suites green:** `pytest <the six files>` → **22 passed, exit 0** (the 19 formerly-red cases + 3 that were
  always green).
- **Full suite green ×3:** `pytest -o addopts="" -q` → **1009 passed, exit 0** on three consecutive runs
  (55.0s / 54.3s / 54.4s); the T31 inner run (excluding the 3 nonregression tests) is **1006 passed, exit 0**.
  No run hit the documented pre-existing `tests/test_session_overlay.py::panel` SIGSEGV (all `EXIT=0`, 0
  failures) — consistent with it being pre-existing and **not** a D42 defect.

## B. ESC-049 (BUILD, should-fix) — the no-wave mode gap → P2-T25 — **VERIFIED, CLOSED**

- **Fix present and correctly placed.** `ui/main_window.py:1610` sets `new_session._wave_extended_hours =
  extended_hours` immediately after `_wave_timeframe`, i.e. **before** `prepare_load`/`attach_view` and the
  initial `BarCache.get_bars`/`set_bars` (`:1641`/`:1643`). Repo-wide grep: the only other setter is
  `ui/ticker_session.py:866` (queue_wave_plans), and `prepare_load` does **not** reset the field — so the cap is
  the current load's mode.
- **The guard discriminates (my own experiment).** In a **temp copy** of the tree with only that one line
  deleted, `pytest tests/test_d42_depth_floor.py -k p2_t25` → **3 failed / exit 1**, including
  `AssertionError: 5 mins ETH no-wave: in-memory series is 5000, expected the ETH budget 6624 (the RTH budget
  5000 is the pre-fix value)` — i.e. the exact 5,000-vs-6,624 mechanism the escalation reported, so the guard is
  not vacuous.
- **Green on the live tree:** `tests/test_d42_depth_floor.py` → **16 passed, exit 0** (T11 + T21[1 min,5 mins]).
- **No stale-mode leak:** T11 part 2 asserts a subsequent RTH no-wave load sets `_wave_extended_hours is False`;
  the assignment is unconditional per load. `load_chart`'s `extended_hours` is always a bool (resolved from
  `ext_hours_btn`; the only call sites are 0/1-arg — verified by grep).

## C. ESC-051 (BUILD, nice-to-have) — over-relaxation → P2-T26 — **VERIFIED, CLOSED**

- `tests/test_history_backfill.py:285` (`t40_t01`) again reads `assert len(plans) == 1` (diff: `-assert plans` →
  `+assert len(plans) == 1`); the app-side `assert len(stub.calls) >= 1` stays. `plans` is the test's **own**
  planner call (no `min_sessions`), unchanged by D42. `pytest tests/test_history_backfill.py -k t40_t01` →
  **1 passed, exit 0**.

## D. ESC-050 (PLAN, should-fix) — the enumeration defect — **VERIFIED, CLOSED**

Re-verified the amendment myself against `docs/plan.md` / `docs/architecture.md` (not the Validator's word):

- **(1) The six load-path-*driving* suites are enumerated with their cause and counts** — `test_d24_popouts.py`
  (7), `test_phase3_fixpass.py` (7), `test_d24_alarm_full_chain.py` (2), `test_d24_smoke_gate.py` (1),
  `test_d24_9_popout_persistence.py` (1), `test_d28_tick_burst_baseline.py` (1) = **19** (`plan.md:1010-1012` and
  the `1249-1256` table; `architecture.md` S21 row; the Phase-2 file map's `ui/main_window.py` row now names all
  six, `plan.md:1169`).
- **(2) The D16 sites are completed to all 14 changed test functions.** Independent count from `git diff -U0`
  hunk headers: **7** (loadpath: `t39_t01`..`t39_t07`) + **4** (history_backfill: `t40_t01`/`t40_t03`/`t40_t04`/
  `t40_t06`) + **3** (disconnect: `t43_t03`/`t43_t06`/`t44_t03`) = **14** — matches the plan.
- **(3) `t40_t05` has no hunk** (grep: the function exists but the diff touches it nowhere); the "no shortfall" →
  "no **answered** day reported missing" correction is in **`test_t40_t04`'s tail** (`b48133d:484-485`), exactly
  as the plan's verification note records — so ESC-050's own naming of `t40_t05` is **relocated** (the plan keeps
  the site listed for the defect class but locates the correction in `t40_t04`). Canonical wording is "**cases**"
  (the six suites' counts sum to 19 failing test cases).
- **(4) The invariant and the generalisable rule are stated** (`plan.md:1262-1290`): *any test that drives
  `MainWindow.load_chart` with a stubbed `req_historical_data` must use an unbounded reqId source*; and *enumerate
  by call site of the changed entry point, not by the suites the design names; a fixed-size stub of a changed feed
  is a defect class.* `AR-D42-6` is rewritten and a **Frozen Interfaces** checklist added
  (`architecture.md:4010`). The invariant's code-side truth is now demonstrated by the green P2-T24 stubs.
  `docs/plan.md` ends `Status: READY_FOR_TASK_MANAGER`.

## E. P2-T23 — the reconciliation node

- `tests/test_d42_nonregression.py` → **3 passed, exit 0**, including **T31** (`test_full_offscreen_suite_is_green`,
  which runs the whole suite in a hermetic subprocess and asserts rc 0) — i.e. the task's own guard, which
  **correctly** reported `blocked` before P2-T24, now passes. T11 (AC-D16.7 New-Year year-ends) and T21
  (AC-D16.1/3/4 genuine closure + present-but-mode-empty) are real assertions, not tautologies.

## F. Quality review of the incremental changes — no new findings

- The incremental diffs are **test-only stub widening** (P2-T24), **one production assignment** (P2-T25), **one
  assertion restored** (P2-T26) and a **docs amendment** (ESC-050). No deviation from `architecture.md`/`plan.md`;
  no production behaviour changed beyond the S19 mode-set that the plan mandates.
- **Mock-endpoint containment** (standing invariant): grep of the reviewed diff (`ui/main_window.py`, the six
  suites, `tests/test_history_backfill.py`) for `mock|fake|stub|simulat` ×
  `endpoint|client|service|server|api|harness` → **0 hits**. No mock in production code; no production module
  imports a test fake.
- **Observation (not escalated):** the six suites' `rt_manager.subscribe` stubs remain fixed-size
  (`iter([...])`), unlike the now-unbounded historical stubs. They are sufficient today (the suites are green) and
  are outside the invariant ESC-050 states; noted for awareness only — widening them is not warranted by any
  current failure.
- **Usage-doc coverage:** the project's user docs are `USAGE.txt` and `usage.md` (`precheck.json`
  `doc_candidates`, all `touched: false`). The rework changes no user-visible behaviour (it widens test stubs and
  sets an internal session flag), so **no doc update is required** for this rework. (The pre-existing `USAGE.txt`
  D36/D37 staleness noted in the previous D42 pass remains out of scope.)

## G. Escalation close-out

Flipped in place, each only after the re-verification above:
**ESC-048 → addressed · ESC-049 → addressed · ESC-050 → addressed · ESC-051 → addressed.**
`ESC-032/033/034/036/043/044/045` remain **open** — pre-D42 live-run defects, not this batch's work; the rework
diff touches none of their cited code paths, so they are not re-diagnosed. `ESC-047`/`ESC-046`/`ESC-037`–`ESC-042`
remain `addressed` (untouched). `docs/codebase-map.md` does not exist — expected (convention applies from the next
batch); not escalated.

## H. Pipeline state for the Orchestrator

**No open D42 escalations remain.** The full offscreen suite is green (1009 passed, exit 0, ×3). All four D42
escalations are closed. Remaining open items are the seven pre-D42 live-run BUILD escalations
(ESC-032/033/034/036/043/044/045), which are outside this batch's scope and were not re-diagnosed.

# Backlog batch review — P2-T27…P2-T35 (seven live-run defects), 2026-10-16

**Scope (incremental):** the nine tasks whose `docs/build/results/<id>.json` are newer than the previous
`REVIEW_COMPLETE` — `P2-T27`–`P2-T35` (the precheck's 9-task scope; the brief said "eight", the actual set is
nine). `docs/build/build_log.md` ends `Status: READY_FOR_REVIEW`; all 35 tasks `done`. `docs/code_review/precheck.json`
reports **0 fail_fast, 0 escalation entries, 0 unattributed working-tree changes, 4 overlap(info) only, no footprint
violations**. Repo working tree (uncommitted batch on top of `5d518ad`). No live TWS used — every run offscreen.

**Method:** diff-first over each task's `files_verified`; guards re-run RED→GREEN in a **temp copy** of the tree
(`/…/T/opencode/cr_redcheck`) — no repo file was edited. `docs/codebase-map.md` does not exist — expected
(convention applies from the next batch); not escalated.

## A. Independent test evidence

`docs/code_review/test_verification.json` (+ `.log`) is **absent** — the Orchestrator's independent run was not
present for me to consume, so I ran the suite myself (this is the one deviation from "don't re-run the suite"):
`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → **1034 passed, 0 failed, exit 0** on
**two consecutive runs** (66.4 s / 66.0 s). No skips/xfails collected. Targeted re-runs of the nine touched
modules in the temp copy: **36 passed**. This independently confirms the brief's "exits 0 with zero failures on
two consecutive runs".

## B. Guard RED→GREEN verification (every task spot-checked, not a sample)

For each task I reverted the fix to its **genuine pre-fix shape** in the temp copy, ran the task's own tests,
observed RED, then restored and confirmed GREEN.

| Task | Reverted to pre-fix | RED evidence | GREEN |
|---|---|---|---|
| P2-T27 | drop `ibkr.account.Position.id` **and** the `position.id = _upsert_position(...)` assignment | 3 failed incl. the exact `AttributeError: 'Position' object has no attribute 'id'` at `strategy_by_id.get(pos.id, "—")` | 3+6 passed |
| P2-T28 | `load_btn.clicked.connect(self.load_chart)` | 2 failed (`test_toolbar_click_loads_widget_symbol`, `…empty_symbol…`) | 3 passed |
| P2-T29 | `timer.timeout.connect(lambda: item.setBackground(...))` | 2 failed (lifetime + source-shape) | 3 passed |
| P2-T30 | make the replay guard unconditional (always push) | 2 failed (both fabricated-candle guards) | 8 passed (file) |
| P2-T31 | neutralise the live-account scoping + prune | 2 failed (scoped render, foreign-row prune) | 3 passed |
| P2-T32 | disable the production-DB refusal guard | 2 failed (block + fires-before-connect) | 4 passed |
| P2-T33 | restore `class_`/`lastDateOrMonth`/`putCall` reads | 3 failed | 6 passed (file) |
| P2-T34 | remove `summary['Account']` write **and** the `_account_id` fallback | 1 failed (`test_p2_t34_t11`) | 6 passed (file) |
| P2-T35 | remove the coarse `1 min` bar-size branch | 3 failed | 8 passed (file) |

**P2-T28 specifically** (the brief's emphasis): the guard drives the **real `win.load_btn.click()`** — never
`load_chart()` directly — with a recording `sys.excepthook` (pyqtgraph's non-abort hook swallows slot exceptions)
and asserts `hook.errors == []` plus `_current_symbol == "AAPL"`; it went RED when the old wiring was restored.
That is exactly the path the defect escaped.

**Two "field-only" caveats (minor, no escalation):** reverting **only** `ibkr.account.Position.id` (P2-T27) or
**only** the `_render_summary` line (P2-T34) leaves the tests green, because the live path sets `position.id`
dynamically and the `summary['Account']` write already satisfies `.get('Account', '—')`. In both cases the
**behavioural** change is what the guard pins and it is genuinely discriminating; the dataclass field /
`_render_summary` fallback are belt-and-braces.

## C. Test-integrity checks

- **No skips/xfails** added anywhere in the reviewed diff (grep over the added lines: none); the new files contain
  none either (the one `skip`-substring hit is the word "skipped" in a comment).
- **No assertion weakened.** The only removed assertion lines are: (i) `assert any(p.symbol == "HELD" …)` in
  `test_d27_6_positions_populate_panel`, replaced by a **stronger** block (rowCount==1 + rendered cell text +
  `held.id is not None`); (ii) the four superseded `test_d27_9_prime_span_bounded` lines (`bar_size=='5 secs'` /
  `duration=='7200 S'`), replaced by the D43-correct coarse shape — the escalation's own "correct, do not merely
  weaken" instruction. No test was deleted.
- **`test_d27_9_prime_span_bounded` corrected, not weakened** — verified against requirements.md:3101-3114 /
  :3134-3139 and D43.1 (:3660-3667): the fine `5 secs`/[60 S, 3600 S] and coarse `1 min`/[60 S, 1 D] split the code
  implements matches AC-D27.9 (revised) exactly.
- **Sequencing (shared files):** P2-T30 (wave78) landed before P2-T35 (wave80); both touch
  `ui/ticker_session.py` + `tests/test_d27_aggregator_priming.py` and are serialized across waves — no same-wave
  overlap (precheck flags are `info` only).

## D. Standing checks

- **Mock-endpoint containment:** grep of the production diff (`ui/ data/ ibkr/ config/ main.py services/`) for
  `mock|fake|stub|simulat` crossed with `endpoint|client|service|server|api|harness` → **0 hits**. The only
  "fakes" are test doubles inside `tests/`.
- **P2-T30 provenance (the brief's item 3):** the worker died twice; run 2 left a `# RED-CHECK temp revert` line
  and described a replay guard that was **absent from the tree**; the orchestrator restored the clamp and
  implemented the guard. I verified the guard is **now real and discriminating** (row P2-T30 above: removing it
  fails both fabricated-candle tests) and that no `# RED-CHECK`/`temp revert` marker remains anywhere in
  `ui/ tests/ services/ data/ ibkr/`. `footprint_flags` on `wave78_P2-T30.json` record the provenance — read and
  consistent. I looked for the same "report describes work not in the tree" pattern elsewhere and found none:
  every other task's described guard is present and RED-discriminating.
- **ESC-043 (the brief's item 4):** the fix **addresses the owner's existing production rows**, not just hides
  them — `_on_position_end` `DELETE`s rows whose `account` is not in the live set (the persisted `DU123`/`HELD`
  and `DU1`/`H` junk rows), verified by `test_p2_t31_t21` asserting `_count_account('DU123') == 0` while the live
  row survives. **P2-T32's refusal cannot break the real app or pytest:** `main.py` (the PyInstaller spec's entry)
  opts in before importing `ui.main_window`, `config/settings.py` imports only `os` (so nothing pulls `data.db`
  before the opt-in), and the pytest suite sets `DB_PATH` in `tests/conftest.py` (guard keys on `DB_PATH` unset) —
  confirmed by the two green full-suite runs.

## E. Quality review of what passed

- **Consistency with architecture/requirements:** all seven fixes match the recorded decisions (ESC-032 additive
  `id`; ESC-033 lambda decoupling with the D28.2 signature frozen; ESC-034 lazy resolution mirroring the existing
  `_set_cell` pattern; ESC-036 = D43/AC-D27.9 revised; ESC-043 account-scoping + DB-isolation rule S12; ESC-044
  real `Contract` attributes with the UNSET_DOUBLE → None normalisation; ESC-045 callback-argument account id).
  No deviation from `architecture.md`/`plan.md` found.
- **User-doc coverage:** `precheck.json` `doc_candidates` are `USAGE.txt` and `usage.md` (all `touched: false`).
  This batch fixes defects in existing behaviour (a dead button, a crash, wrong Type/Account fields, an
  unprimed aggregator, leaked rows) and adds no new user-facing surface, CLI/API, or config option — so **no doc
  update is required**. (The pre-existing `USAGE.txt` D36/D37 staleness remains a separate, already-recorded
  owner/Requirements dependency.)
- **New findings:** see ESC-052 and ESC-053 below.

### ESC-052 (BUILD, quality, should-fix) — the P2-T31 prune is not gated on the account-summary stream completing

`_on_position_end` runs `DELETE FROM positions WHERE account NOT IN (<live>)` as soon as `_live_accounts` is
non-empty; `_on_account_summary_end` (:2941) is never consulted. `position_end` and `accountSummaryEnd` are
independent streams with no ordering guarantee, so a `position_end` arriving while `_live_accounts` holds only
**some** of the user's accounts deletes the remaining (real) accounts' persisted rows, and `_on_position_update`'s
foreign-account early-return drops their live updates too (so the rows are not necessarily re-persisted). Edge
case (single-account users, the owner's case, are unaffected) but a **destructive write to the real DB on an
unguarded ordering assumption**, and untested (only full-set and empty-set are covered). Routed to BUILD with a
minimal direction (gate the prune on `_on_account_summary_end`, or scope the DELETE to accounts known non-live
after completion; add a partial-live-set test).

### ESC-053 (REQUIREMENTS, gap, nice-to-have) — the brief's "qty == 0 hidden (owner's decision)" is not supported by the repo

The brief states P2-T31 "hides `qty == 0` rows (the owner's decision)". The artifacts say otherwise:
`docs/tasks/task-graph.json`'s P2-T31 description marks flat-row hiding **"NOT IN SCOPE (a product call, flagged
for the owner, not decided here)"**, and `docs/tasks/task_manager_notes.md:1819` repeats it as "a product call, not
decided here … left to the owner". The code correctly does **not** hide flat rows, and no requirement/open question
on file decides it — so the owner's six flat SPXW rows (which ARE in the live account) still render after
ESC-043. This is a **premise discrepancy in the brief**, surfaced here rather than treated as a P2-T31 defect;
ESC-053 routes the product call to the Requirements Analyst / owner so it is not lost when ESC-043 closes.

## F. Escalation close-out

All seven open entries were re-verified against the live tree (not the workers' word) and flipped to `addressed`
**in place** with a `verified` note — each backed by the RED→GREEN row above:

**ESC-032 → addressed · ESC-033 → addressed · ESC-034 → addressed · ESC-036 → addressed · ESC-043 → addressed ·
ESC-044 → addressed · ESC-045 → addressed.**

Two **new** entries opened this pass: **ESC-052** (BUILD) and **ESC-053** (REQUIREMENTS). `ESC-030/031/035/037`–
`ESC-042/046`–`ESC-051` were already `addressed` and were not re-diagnosed.

## G. Pipeline state for the Orchestrator

The batch's own work is sound: **every guard is RED before its fix and GREEN after**, no assertion was weakened
or skipped, no test deleted, no mock endpoint in production, and the full offscreen suite is deterministically
green (1034 passed ×2). The seven targeted escalations are **closed**. **Two open escalations remain** —
ESC-052 (should-fix, destructive-prune gating) and ESC-053 (nice-to-have, the `qty == 0` product call) — so the
Orchestrator should pause and summarize before re-invoking any agent. `docs/codebase-map.md` absence is expected,
not escalated.

Status: REVIEW_COMPLETE

# ESC-052 / ESC-053 rework verification — P2-T31 (rework) + P2-T37, 2026-10-16

**Scope (incremental):** only the tasks whose `docs/build/results/<id>.json` are newer than the previous
`REVIEW_COMPLETE` (03:26:06Z) — **P2-T31** (the ESC-052 rework; newest result
`_archive/wave86_P2-T31.json`, 03:40:34Z) and **P2-T37** (the ESC-053 fix; `_archive/wave84_P2-T37.json`,
03:35:27Z). `docs/build/build_log.md` ends `Status: READY_FOR_REVIEW`; `docs/build/failures.json` is `{}`.
**No live TWS** — every run offscreen.

**Verification inputs.** `docs/code_review/test_verification.json` is present and fresh (03:42:23Z — after the
last build result): **`VERIFY: pass`, exit 0, 68.35 s**, no skips/xfails. Consumed as ground truth for "did the
suite actually pass"; I did not re-run the full suite. `docs/code_review/precheck.json` was **stale**
(generated 03:17:18Z, before the 03:33–03:40Z results, and it scoped only the previous batch, P2-T27…P2-T35),
so per the standalone provision I re-ran `review_precheck.py` (03:42:59Z): **1 task scoped (P2-T37), 0
fail_fast, 0 escalation entries, no footprint violations, 3 doc candidates all `touched: false`.** Its 15
"unattributed working-tree changes" are the whole uncommitted batch (nothing in this batch is committed yet),
not a footprint breach.

**Method.** Read both diffs and the surrounding call paths; re-ran every guard **RED→GREEN in a temp copy of
the tree** (`…/T/opencode/cr_redcheck2`, rsync + a `.venv` symlink) — **no repo file was edited**. Two probes
of my own (never Build's tests) live only in that temp tree.

## A. ESC-052 / P2-T31 — the destructive prune is gated on the account-summary stream completing — **VERIFIED, CLOSED**

**Gating is real and correctly placed.** `ui/main_window.py::_on_position_end` prunes **only** when
`live and complete`, where `complete` is `_account_summary_complete`; a non-empty-but-**partial** `_live_accounts`
still **scopes the render** (`WHERE account IN (live)`) but never deletes. `_on_account_summary_end` is the only
setter: it first rejects a stale end (`reqId != self._account_summary_req_id`), then sets the flag, prunes, and
re-renders when `_positions_rendered` is set so a `position_end` that beat the end marker converges.

**Discriminating RED (temp copy, pre-fix shape restored).** Reverting to the genuine pre-ESC-052 shape
(`if live:` prune + no ESC-052 handling in `_on_account_summary_end`) → **exactly 1 failed**:
`tests/test_d27_account_scoping.py::test_p2_t31_t41_partial_live_set_does_not_prune` —
`AssertionError: a real account's rows were pruned on a partial live set` / `assert 0 == 1 where
0 = _count_account('U99999999')`. Live tree: **4 passed**. So the new partial-live-set test is the ESC-052
discriminator and it genuinely fails pre-fix.

**Both arrival orders prune on a complete set (my own probe, not Build's tests).**
(i) `position_end` **before** `account_summary_end`: the partial set leaves both the foreign `DU123` row and the
un-summarised real row intact (`FOREIGN=1`), then the **end-driven** prune deletes `DU123` (`FOREIGN=0`,
`LIVE=1`) and the render converges to `['AAPL']` — i.e. the prune really does run from
`_on_account_summary_end`. (ii) `account_summary_end` **before** `position_end`: the `position_end` prune fires
(`FOREIGN=0`, `LIVE=1`). Both directions covered by the shipped T21/T41 pair plus my probe.

**Completeness flag cannot survive a reconnect.** `_on_disconnected` and `_subscribe_account_data` each clear
`_account_summary_complete`, `_live_accounts` **and** `_positions_rendered`. Probe: after a complete cycle,
either call leaves `_account_summary_complete is False` / `_live_accounts == set()`, and a partial set after the
reset does **not** prune (a freshly seeded `DU1` row survives). A stale `account_summary_end` carrying a
superseded reqId leaves the flag `False`.

**The earlier T11/T21 foreign-row-removal assertions were NOT weakened.** T21 still asserts
`_count_account('DU123') == 0` — the **DELETE**, not a hide — *and* that the live row is kept *and* the
unknown-live-set no-op path leaves both rows. The only test-content change is the added
`account_summary_end.emit(win._account_summary_req_id)` precondition, which the new gate **requires** (without
it the prune would legitimately not run). No assertion removed, narrowed or skipped; no `skip`/`xfail` anywhere
in the two files.

## B. ESC-053 / P2-T37 — flat (`qty == 0`) rows hidden from the render — **VERIFIED, CLOSED**

**Owner decision recorded.** `docs/tasks/task_manager_notes.md:1965-1983` records the owner's verbatim
answer *"Hide qty==0 positions"* and supersedes the earlier "NOT IN SCOPE (a product call … not decided here)"
note; P2-T37's AC1/AC2/AC3 define the behaviour. (The P2-T31 task-graph description still carries the superseded
sentence — folded into ESC-054.)

**Hidden at both feed points, at the list level.** `set_positions` does
`self._positions = [p for p in positions if p.qty != 0]`; `add_position` removes an existing entry with the same
`con_id` and appends only when `qty != 0` (so a flattening update drops the row too). Because the filter is on
`self._positions` rather than at paint time, `_render_table` and `_on_selection_changed`'s
`self._positions[row]` keep indexing the same list.

**Discriminating RED.** Restoring `self._positions = list(positions)` plus the unconditional append → **3
failed** (T11 bulk-hide, T21 single-add, T31 non-flat-render); live tree **4 passed**.

**The alignment guard is real (and is a structural invariant guard, not the flat-hiding discriminator).**
Applying a *paint-time-only* filter variant (keep `_positions` unfiltered, filter inside `_render_table`) makes
**T41 fail** at `assert table.rowCount() == len(panel._positions)` — exactly the desync a render-only filter
would cause. Note T41 passes pre-fix (there is no filtering then), so it is not the pre-fix RED for hiding; T11
is.

**It is a render filter, not a delete (my own probe).** A `position_update` with `qty == 0` persists
`('SPXW0', 0.0)` in the `positions` table while rendering no row; re-flattening a held position leaves the DB
row at `qty 0` and removes the rendered row; the bulk `position_end` path keeps a flat option row in the DB
(`('SPXW1', 0.0)`) and hides it. The panel has no DB access at all (grep: no `execute`/`DELETE`/`INSERT`).

## C. Test integrity / standing checks

- **No assertion weakened, no test deleted, no skip/xfail** in either task's diff; production diffs are
  comment/docstring-heavy and behaviour-scoped.
- **Mock-endpoint containment:** grep of the reviewed production diff (`ui/main_window.py`,
  `ui/active_portfolio_panel.py`) for `mock|fake|stub|simulat` crossed with
  `endpoint|client|service|server|api|harness` → **0 hits**. No test double in production code.
- **No worker-residue markers** (`RED-CHECK` / `temp revert`) in the four reviewed files.
- **Footprint:** P2-T31 → `ui/main_window.py` + `tests/test_d27_account_scoping.py`; P2-T37 →
  `ui/active_portfolio_panel.py` + `tests/test_d27_flat_rows.py`. Both match `files_changed` and
  `touches_files`; `footprint_flags: []` on both results.
- **User-doc coverage:** the precheck's `doc_candidates` are `USAGE.txt`, `usage.md`, `docs/` — all
  `touched: false`. Judged **no doc update required**: `usage.md` describes the Portfolio dock only generically
  ("Account summary, positions, P&L, SL/TP, group actions") and documents no other row-level filtering rule
  (not the account scoping from ESC-043 either), so a flat-row note would be out of keeping with its
  granularity. Recorded explicitly rather than skipped.
- **Second-order effect of ESC-053 (observation, no escalation):** hiding flat legs also removes them from
  `_group_and_render`'s detection input. `services/strategy_detection.py::_normalize_legs` keeps a `qty == 0`
  leg and `_detect_vertical_spread` requires `l1.qty * l2.qty < 0` (and the IC path requires `[-1, 1]`), so a
  flat leg previously **poisoned** detection to `CUSTOM`. Removing flat legs can therefore only *enable*
  grouping, never break an existing group label — benign, and no test covers it.

## D. Escalation close-out

- **ESC-052 → `addressed`** (edited in place, `verified` added) — see A. Independently re-verified; the gating
  is real, discriminating, correct in both arrival orders, and reset on reconnect/disconnect. Its `expected`
  (the prune) is fully met.
- **ESC-053 → `addressed`** (edited in place, `verified` added) — see B. The owner's decision is recorded and
  implemented; flat rows are hidden at both feed points while staying in the DB, and the alignment guard holds.
- **ESC-054 opened** (`TASK_MANAGER`, `gap`, `should-fix`) — see E. One invariant, one escalation.
- **`opened` timestamp bug corrected.** ESC-052 and ESC-053 were both stamped
  `2026-10-16T03:50:00+00:00` — ~9 minutes **in the future** (the real write time was ~03:41Z). Both are now
  `2026-10-16T03:41:00+00:00`; a scan of all 25 entries finds **no other future-dated `opened`**.

## E. ESC-054 — the invariant behind ESC-052 was fixed only for its destructive case (TASK_MANAGER)

The ESC-052 rework corrected the **prune** path, but the task's acceptance criteria still describe the
**partial** live-account set as authoritative, and one code path still acts on it:

1. **`_on_position_update` still drops a real account's update during the partial window.** AC3 ("the live
   account(s) are known" → a foreign update "is neither persisted nor rendered") is implemented with
   `_live_accounts` non-empty, so between the first `account_summary` callback and `accountSummaryEnd` a real
   second account's update is silently discarded. Probe (temp copy): partial set `{U13148604}`;
   `position_update.emit('U99999999', MSFT, 10.0, 5.0)` → **no** `positions` row; after the summary completes
   with `{U13148604, U99999999}` + `position_end`, the DB is **still empty** and the panel renders nothing for
   that account — `_on_position_end` loads from the `positions` table, so the dropped update is unrecoverable
   for the session.
2. **AC2 as worded now contradicts the shipped (correct) behaviour** — it says the prune runs "When
   `_on_position_end` runs" given foreign rows and no-ops only when "the live account set is not yet known (no
   account-summary callback has arrived)", i.e. it asserts a **partial** set prunes, which is exactly what the
   ESC-052 fix forbids. A reworker reading AC2 literally could revert the safety gate to satisfy it.

Impact today: **nil for the single-account owner** (their one account is the only member of the live set);
real for multi-account users. Routed to TASK_MANAGER with the invariant stated (the live set is authoritative
only once the summary stream has **completed**; before that, no real account's data may be destroyed or
silently discarded) so the ACs are rewritten to the rule rather than accumulating another per-case BUILD patch.
This is deliberately **one** escalation: the prune case (ESC-052, BUILD) and the update case are two cases of
one invariant.

## F. The `opened`-timestamp tooling interaction (recorded; global-tool note, not a repo defect)

ESC-052's future-dated `opened` (03:50Z) meant no result mtime could ever be "newer than the escalation", so
`build_wave.py` reset and re-dispatched **P2-T31 on every `advance`**: the build log shows waves **82, 83, 84,
85, 86, 87** all publishing P2-T31, with four archived results (`wave78` 03:10:22Z, `wave82` 03:33:17Z,
`wave85` 03:37:47Z, `wave86` 03:40:34Z). `wave85` and `wave86` have **identical summaries and the same
`files_changed`**, and `ui/main_window.py` / `tests/test_d27_account_scoping.py` still carry their **03:37**
mtime — i.e. the wave-86 run produced no new edit: the repeat dispatch was pure churn caused by the future
timestamp, exactly as reported. Rule for my own output: always stamp `opened` with the **real current UTC
time**. (Global tool `build_wave.py` — not edited from inside the repo; recorded here for the tool author, in
the same spirit as the existing `build_wave.py` entry in `docs/memory.md`.)

## G. Pipeline state for the Orchestrator

Both requested fixes are **independently verified and sound** — ESC-052's gating is real, discriminating and
correct in both arrival orders, with the completeness flag reset on (re)subscribe and disconnect; ESC-053 hides
flat rows at both feed points as a render filter while preserving row/list alignment and DB persistence. No
assertion was weakened, no skip/xfail added, no mock endpoint in production code, and the full offscreen suite
is green per the Orchestrator's own run (`pass`, exit 0).

**Open escalations remaining: one — ESC-054** (TASK_MANAGER, `should-fix`: pin the "live set is authoritative
only when the account-summary stream has completed" invariant in P2-T31's ACs and decide the
`_on_position_update` partial-window behaviour). It does not block the suite. ESC-001…ESC-053 are all
`addressed`; **no `opened` value is in the future**.

Status: REVIEW_COMPLETE

# ESC-054 verification + P2-T31 test-correction review — P2-T38 + P2-T31 (rework), 2026-10-16

**Scope (incremental):** only the tasks whose `docs/build/results/<id>.json` are newer than the previous
`REVIEW_COMPLETE` — **P2-T38** (`_archive/wave90_P2-T38.json`, the ESC-054 fix) and **P2-T31**
(`_archive/wave88_P2-T31.json`, the ESC-052 rework). `docs/build/build_log.md` ends `Status: READY_FOR_REVIEW`;
`docs/build/failures.json` is `{}`. **No live TWS** — every run offscreen
(`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`).

**Verification inputs (ground truth, consumed not re-derived).** `docs/code_review/test_verification.json` —
`VERIFY: pass`, exit 0, 66.13 s, no skips/xfails — taken as "did the suite actually pass"; the full suite was not
re-run. `docs/code_review/precheck.json` — scope `[P2-T31, P2-T38]`, 0 fail_fast, 0 `PRE-*` entries, footprint
verified, `escalation_updates` = ESC-054 changed. Consumed, not re-run.

**Method.** Read both diffs and the surrounding call paths; re-ran the guards **RED→GREEN in a temp copy of the
tree** (`…/T/opencode/esc054_red`) — **no repo file was edited**.

## A. ESC-054 / P2-T38 — the pre-summary update is no longer dropped — **VERIFIED, CLOSED**

**The gate is real and correctly placed.** `ui/main_window.py::_on_position_update` (lines 3027-3032) now
early-returns only when `self._live_accounts and self._account_summary_complete and account not in
self._live_accounts`; a non-empty-but-partial set no longer discards a real account's update, and the
completed-set gate ESC-043/ESC-052 established stays in force.

**Discriminating RED (temp copy; genuine pre-fix shape = the one clause removed).** Removing ONLY
`and self._account_summary_complete` → **2 failed**: `test_p2_t38_t11_pre_completion_update_persisted_and_rendered`
and `::test_p2_t38_t21_pre_completion_update_survives_completion`, both `assert 0 == 1 where
0 = _count_account('U99999999')` — the reviewer's original probe (row absent before AND after completion). The
other 5 (T31×2, T41, and P2-T31's T11/T21) stayed green. Live tree: **7 passed**.

**AC3 holds both ways.** Removing the WHOLE early-return (no scoping at all) → **2 failed**:
`test_p2_t38_t31_foreign_update_after_completion_still_dropped` and
`test_p2_t31_t31_foreign_position_update_not_persisted_or_rendered` (foreign `DU123` persisted). So a foreign
update AFTER completion is still dropped, and the guards genuinely discriminate the gate.

**ESC-052 gating untouched.** `_on_position_end` still prunes only when `live and complete`; `_prune_foreign_positions`
and `_on_account_summary_end` are unchanged; `test_p2_t31_t41_partial_live_set_does_not_prune` passes in both the
temp RED copy and on the live tree.

## B. The Orchestrator's P2-T31 test correction — **INTENT-PRESERVING, not a weakening**

`tests/test_d27_account_scoping.py::test_p2_t31_t31` used to emit the foreign update with **no** `accountSummaryEnd`,
pinning the very drop ESC-054 fixes. The correction inserts `bridge.account_summary_end.emit(win._account_summary_req_id)`
before the foreign emit (the same form the file's other tests use). The assertion is **unchanged**
(`_count_account('DU123') == 0` and no rendered `FOREIGN` row) and it still **fails** when the scoping early-return is
removed (section A), so the guarantee is asserted — now under the condition the code requires. This is a legitimate
correction, not a loosening: the guarantee is still falsifiable, only the emission point moved to where it holds.

## C. Test integrity / standing checks

- **No assertion weakened / deleted / skipped:** `grep -E "pytest\.mark\.(skip|xfail)|pytest\.skip|deselect|--ignore"`
  over both reviewed test files → 0 hits.
- **Mock-endpoint containment:** `grep -iE "mock|fake|stub|simulat"` over the changed production file
  `ui/main_window.py` → 0 hits; no test double in production code.
- **Footprint:** P2-T38 → `ui/main_window.py` + `tests/test_d27_account_partial_window.py`; P2-T31 →
  `ui/main_window.py` + `tests/test_d27_account_scoping.py`; both match `files_changed` / `touches_files`,
  `footprint_flags: []`. (P2-T31's precheck `unknown_test_ids` warning — result cites `P2-T31-T41` not in the task
  spec — is the ESC-052 regression test added by escalation, not a defect.)
- **User-doc coverage:** precheck `doc_candidates` (`USAGE.txt`, `usage.md`, `docs/`) are all `touched: false`;
  judged no doc update required (internal account-scoping/ordering behaviour, no CLI/API/config/workflow surface
  change), consistent with the previous pass's explicit judgement.

## D. Escalation close-out

- **ESC-054 → `addressed`** (edited in place, `verified` added) — see A + B. The invariant is pinned (P2-T31 AC2
  rewritten; P2-T38's AC1/AC2/AC3 record the partial-window behaviour and the completed-set gate), the update path
  is fixed and guarded, and the code fix is verified RED→GREEN. Two **Task-Manager-owned wording residuals** are
  recorded in the `verified` note (P2-T31 AC3 still reads "the live account(s) are known"; the P2-T31 description
  still carries the superseded flat-row sentence) — no code or guard depends on them, the same disposition ESC-053
  left the description sentence in.
- **ESC-055 opened** (`TASK_MANAGER`, `gap`, `nice-to-have`) — the structural recurrence, section E.
- **ESC-030…ESC-053 remain `addressed`, unchanged** — nothing relevant changed for them this cycle; only ESC-054
  was open and it is now closed.

## E. New finding — ESC-055: the D42/ESC-050 defect class recurred at breakdown time

P2-T38 changed a production entry point's behaviour (`_on_position_update`) and invalidated an assertion in
`tests/test_d27_account_scoping.py::test_p2_t31_t31` — a file **outside** P2-T38's `touches_files`, so the task could
not correct it and only the whole-suite gate saw it (every per-task command had passed), leaving the Orchestrator to
hand-edit the test. ESC-050's recorded rule ("enumerate by call site of the changed entry point") already generalises
the enumeration but was framed for D42's changed **feed/stub** (fixture exhaustion); it does not state the ownership
remedy for a changed production **entry point** invalidating a **semantic** assertion in another task's file.
**Suggested:** extend the rule with the ownership half — a behaviour-changing task's `touches_files` must include (or
a sibling task must own) every test file asserting that entry point's behaviour. Task-Manager breakdown practice; no
code change.

## F. Pipeline state for the Orchestrator

P2-T38's fix is **independently verified and sound**: the pre-summary update is persisted and rendered, the
completed-set gate is intact (AC3 both ways), ESC-052's partial-set gating is untouched, and the Orchestrator's
P2-T31 test correction is intent-preserving (assertion unchanged, still falsifiable). No assertion weakened, no
skip/xfail, no mock endpoint in production code, footprint clean; the full offscreen suite is green per the
Orchestrator's own run (`pass`, exit 0). **ESC-054 is closed.** One open escalation remains: **ESC-055**
(TASK_MANAGER, `nice-to-have`: apply the enumeration rule's ownership half at breakdown) — it does not block the
suite. ESC-001…ESC-053 are all `addressed`.

Status: REVIEW_COMPLETE

---

# Code Review — D44 / Batch 19 (collapsed Watchlist → thin vertical bar)

**Reviewer:** Code Reviewer agent · **Date:** 2026-10-17 · **Phase:** P3 (D44, Batch 19)
**Scope (incremental):** `P3-T01`…`P3-T05` — the only tasks with results newer than the last
`REVIEW_COMPLETE` (03:xxZ). `docs/build/build_log.md` ends `Status: READY_FOR_REVIEW`; the batch is
COMPLETE (all 5 tasks `done`).
**Verification inputs (ground truth, consumed not re-derived):**
- `test_verification.json` — `VERIFY: pass`, exit 0, 68.16 s, no skips/xfails → the suite genuinely passed; not re-run.
- `precheck.json` — scope `[P3-T01..P3-T05]`, `fail_fast: [P3-T01]` (footprint), 1 `PRE-*` entry (`PRE-001`),
  `escalation_updates`: ESC-055 changed. Consumed, not re-run.
**Method:** read the diffs of every reviewed `files_changed` (`ui/dock_layout.py`, `ui/watchlist_panel.py`,
`ui/main_window.py`, the 5 test files, the 2 new suites) and the surrounding call paths; ran three **inline**
offscreen probes (`python -` heredoc, `DB_PATH` redirected to the temp dir — **no repo file was written**) to
adjudicate the AC-D44.2 expand-restore residual and the collapsed-handle eventFilter.

## A. Failure diagnosis — none

No task was `blocked`; `failures.json` is empty; the precheck reports no fail_fast beyond the P3-T01 footprint
item (below). All 5 tasks' own tests pass (P3-T01 4/4, P3-T02 5/5, P3-T03 7/7, P3-T04 4/4, P3-T05 7/7).

## B. Quality review — findings

| id | task | category | class | severity | route |
|----|------|----------|-------|----------|-------|
| ESC-056 | P3-T01 | consistency | bad_task_breakdown | should-fix | TASK_MANAGER |
| ESC-057 | P3-T05 | consistency | requirements_gap (wording) | nice-to-have | REQUIREMENTS |
| ESC-058 | — | gap | requirements_gap (doc coverage) | should-fix | TASK_MANAGER |

### B1. PRE-001 adjudication — P3-T01's out-of-footprint `ui/watchlist_panel.py` edit — **LEGITIMATE, code correct**

**Verdict: NOT a defect in the code; the graph's `touches_files` is what is wrong.** P3-T01's own **AC4**
mandates that `clamp_watchlist_width(width, chart_area_w)` "delegates to `plan_watchlist_width(...,
collapsed=False)` and never returns the collapsed width". That function is a module-level def in
`ui/watchlist_panel.py`, not `ui/dock_layout.py` (the task's `outputs` list mis-attributes it to
`dock_layout`). The diff confirms exactly the mandated edit — `ui/watchlist_panel.py::clamp_watchlist_width`
now `return dock_layout.plan_watchlist_width(chart_area_w, width, collapsed=False)` — and
`tests/test_dock_layout.py::test_P3_T01_T41` + `tests/test_watchlist.py::test_clamp_watchlist_width_stays_expanded_never_collapsed`
pin the expanded delegate. The orchestrator correctly declined the fail-fast rework (re-dispatching could only
have reverted a contract-required edit). The deviation is **legitimate**; the graph's footprint is incomplete →
**ESC-056** (TASK_MANAGER). `PRE-001` is not present in `escalations.json` (the orchestrator never appended it),
so there is nothing to flip; this entry is its adjudication.

### B2. P3-T05's three footprint flags — judged

**(a) Float leg re-pointed — ACCEPTED BEHAVIOUR.** D44's collapsed bar is owner-mandated click-to-expand
(`AC-D44.1`/`AC-D44.2`: "clicking **anywhere** on the thin bar ... expands"). A synthetic double-click on the
30px handle necessarily delivers a click first, so the expanding release fires before Qt's title-bar
double-click-to-float. Re-pointing the leg — collapsed asserts the drag/float **affordance** structurally
(`dock.titleBarWidget() is panel.collapsed_handle`; `DockWidgetMovable|DockWidgetFloatable`), expanded
exercises a **real** float on the header strip (`test_D21_10_T03`) — is correct and preserves coverage. No
action.

**(b) `WatchlistPanel.eventFilter` consumes `MouseButtonRelease` on the collapsed handle — ACCEPTED.** The
consumption is the mechanism that makes click-to-expand work; its consequence (the collapsed handle cannot be
double-click-to-floated) is desirable, not a defect: a 30px handle that both expands *and* floats on a
double-click would be ambiguous. Float remains available on the expanded strip and via a title-bar drag. The
real-drag path on the collapsed handle is asserted only structurally, but the owner accepted the float leg as
intended behaviour (2026-10-16), so this is **accepted**, not escalated — recorded for awareness only.

**(c) AC-D44.2 exactness residual — WORDING ISSUE (→ ESC-057).** The AC's measurable says assert
`watchlist_dock.width() == clamp(W)`; the guard asserts only tolerant invariants; the build log records a
residual (300→314, 531→263). My independent probe **did not reproduce** the residual: with the guard's own
round-trip, the expanded dock restored **exactly** W for every in-range W in **both** clamp branches
(hidden: 150→150, 300→300, 361→361, cap 722→722; visible: 150→150, 300→300, 259→259, cap 518→518), and the
tracked `win._watchlist_width` is exactly `clamp(W)` by construction. So the exact echo the AC asks for holds;
the AC, the guard and the residual note disagree about what is asserted. Disposition: a wording fix to
AC-D44.2's measurable (target the tracked `_watchlist_width`, keep a tolerant rendered-width check) →
**ESC-057** (REQUIREMENTS, nice-to-have).

### B3. Documentation — D44 is user-visible and undocumented → **ESC-058**

`USAGE.txt` is the canonical user-facing usage doc with one section per user-visible batch (Phases 1-2,
Phase 3, D38, D39, D40); `docs/phase-changelog.md` records that convention ("### USAGE.txt — New 'Footprint
charts (Phase D36)' section"). `USAGE.txt` currently ends at the D40 section and never mentions the watchlist
collapse; `usage.md`'s UI Overview / Key Workflows likewise never mention it. D44 is an owner-requested
user-visible feature (a new collapsed bar + click-to-expand) and **no** D44 task declared `USAGE.txt`/
`usage.md`, so no task could update it. This is the same drift class the D41 correction (`b8e81b8`) fixed →
**ESC-058** (TASK_MANAGER, should-fix: a small documentation task).

## C. Test integrity / standing checks (all clean)

- **No assertion weakened / deleted / skipped:** `grep -E "pytest.mark.(skip|xfail)|pytest.skip|deselect|--ignore"`
  over the changed `tests/` diff → **0 hits**. The D44 corrections are intent-preserving (e.g. the
  `>= WATCHLIST_MIN_WIDTH` leg **moved** to the expanded state; the float leg **re-pointed**; the D22 docstring
  updated), consistent with `AC-D44.8`/`R67`.
- **Mock-endpoint containment (B.6, blocking check):** `grep -iE "mock|fake|stub|simulat"` over the changed
  production files (`ui/dock_layout.py`, `ui/watchlist_panel.py`, `ui/main_window.py`) → **0 hits**. The only
  test doubles are the intentional `IBApiClient.connect` no-op stubs in the *test* files. Clean.
- **Footprint:** P3-T02…P3-T05 match their declared `touches_files`; P3-T01's single deviation is B1 (legitimate).
- **Cross-task overlaps** (`tests/test_watchlist_columns_d21.py` by T02/T04/T05; `ui/main_window.py` by T02/T05)
  are `info`-severity and harmless — the waves were serialized (W1→W5), so no two overlap-tasks were
  `in_progress` together; the final states of both files are consistent (verified by reading the diffs).

## D. Escalation close-out

- **ESC-055 → `addressed`** (edited in place, `verified` added) — **accepted — no action**, per the owner
  decision on file (`docs/orchestrator_state.json` → `accepted_observations['ESC-055']`, line 19). The finding
  stands as recorded; the owner judged the whole-suite gate sufficient, so no code/plan/graph change is required.
- **ESC-030…ESC-054 remain `addressed`, unchanged** — nothing relevant changed for them this cycle.
- **Opened:** ESC-056 (TASK_MANAGER), ESC-057 (REQUIREMENTS), ESC-058 (TASK_MANAGER).

## E. Pipeline state for the Orchestrator

The D44 implementation is **sound**: the collapsed width is honoured in both `_apply_dock_widths` branches and
survives resize/drag (the core `AC-D44.5` fix); the thin bar is in the app palette with a rotated label; the
header strip / `+` / column-header row hide while collapsed; the tracked expanded width survives the collapse
(`_watchlist_width` never assigned while collapsed) and the collapse state is **not** persisted (no
`watchlist/width` write of the collapsed value — `closeEvent` saves `_watchlist_width`). No mock endpoint in
production code, no assertion weakened, no skip/xfail. Three escalations are open and none blocks the suite:
**ESC-056** (TASK_MANAGER — correct P3-T01's `touches_files`), **ESC-057** (REQUIREMENTS — AC-D44.2 wording),
**ESC-058** (TASK_MANAGER — a D44 `USAGE.txt` entry).

Status: REVIEW_COMPLETE

---

# Code Review — D44 follow-up batch (P3-T06 docs + ESC-056/057/058 close-out), 2026-10-17

**Reviewer:** Code Reviewer agent · **Phase:** P3 (D44 follow-up)
**Scope (incremental):** only `P3-T06` — the sole task whose `docs/build/results/<id>.json`
(`_archive/wave98_P3-T06.json`, `done`) is newer than the previous `REVIEW_COMPLETE`. Documentation-only
(`USAGE.txt` + `usage.md`). `docs/build/build_log.md` ends `Status: READY_FOR_REVIEW`.

**Verification inputs (ground truth, consumed not re-derived):**
- `test_verification.json` — `VERIFY: pass`, exit 0, 67.67 s, no skips/xfails → the suite genuinely passed; not re-run.
- `precheck.json` — scope `[P3-T06]`, `fail_fast: []`, `escalation_entries: []` (no `PRE-*`),
  `files_verified: [USAGE.txt, usage.md]`, tests 3/3 pass; `escalation_updates` = ESC-056/057/058 changed. Consumed, not re-run.

## A. Failure diagnosis — none

No task was `blocked`; the precheck reports 0 fail_fast. P3-T06's three manual checks (T11/T21/T31) pass.

## B. Quality review of P3-T06 (documentation-only) — sound, no new finding

- **Content matches the as-built D44 feature, clause by clause** (verified against the code, not the worker's word):
  a ~30px thin bar (`WATCHLIST_COLLAPSED_WIDTH = 30`; `CollapsedWatchlistBar.setFixedWidth(30)`); the label
  `WATCHLIST` rotated 90° CCW (`painter.rotate(-90)`, `COLLAPSED_BAR_LABEL`); the app's own dark palette
  (`#141822` bg / `#232938` border / `#cbd5e1` text); click the bar **or its handle** to expand
  (`collapsed_bar.expand_requested` → `_on_collapsed_bar_expand`; the handle's `eventFilter`
  `MouseButtonRelease` path) restoring the tracked pre-collapse width (`self._watchlist_width`); the header
  strip / `+` / column-header row hidden while collapsed (`_apply_collapsed_visual()` hides `header_bar` +
  `table`) and restored on expand; collapse state not persisted (no collapse-state QSettings key; `closeEvent`
  persists only `_watchlist_width`). No contradicting claim.
- **Convention honoured:** the USAGE.txt section follows the neighbours' `<Feature> (Phase D<n>)` + matching
  dashed-underline style, placed after the D40 section; usage.md carries the UI-Overview row + Key-Workflows entry.
- **Footprint:** `git diff` is `USAGE.txt` + `usage.md` only; matches `files_changed`/`touches_files`. No
  production code or test touched.
- **Mock-endpoint containment (standing check):** the reviewed diff is documentation-only — no production file
  changed, so the `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness` check is vacuous here; nothing to flag.
- **Usage-doc coverage:** P3-T06 **is** the usage-doc update for the user-visible D44 feature — the coverage gap
  ESC-058 named is now filled (see D).
- **Test integrity:** no test changed; nothing weakened/skipped.

## C. Test integrity / standing checks — clean

- No production code changed; no assertion weakened, deleted, or skipped (docs-only diff).
- Cross-task overlaps: none (single-task batch).

## D. Escalation close-out — all three flipped to `addressed`

- **ESC-056 (TASK_MANAGER) → `addressed`.** Re-verified against `docs/tasks/task-graph.json`: P3-T01's
  `touches_files` (line 67) and `expected_artifacts` (line 61) now include `ui/watchlist_panel.py`; the `outputs`
  entry is re-attributed to `ui/watchlist_panel.py::clamp_watchlist_width` (line 78); `context.read_files` gained
  `ui/watchlist_panel.py` 98-125 with the matching `why` (lines 100-104). **No delivered task clobbered** —
  P3-T01's `status` is still `done` (line 81) and the revision header/notes record the correction as
  metadata-only ("no rewrite of the delivered record"). Code unchanged and correct.
- **ESC-057 (REQUIREMENTS) → `addressed`.** `AC-D44.2`'s measurable (`requirements.md:3880-3890`) now names the
  **tracked** `win._watchlist_width == clamp(W)` (exact by construction) **plus** a tolerant rendered-width check,
  with the former rendered-echo wording marked superseded. Propagated to the D44 register bullet (`:3847-3852`),
  Journey 37 (`:996-1000`), R67 (`:4156`), `design_gaps.md` DG74 (`:1182-1186`) and `open_questions.md` Q55
  (`:1169-1187`, explicitly recording the orchestrator's 300→314 residual as **not evidence**). Matches the
  shipped guard `test_P3_T05_T21_expand_restores_the_tracked_width` (tolerant bounds). Wording-only; no code change.
- **ESC-058 (TASK_MANAGER) → `addressed`.** The D44 `USAGE.txt` section + usage.md entries exist and describe the
  as-built behaviour (verified clause-by-clause against the code, section B). Footprint clean.

## E. New findings

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| — | — | — | — | None. The D44 documentation matches the as-built feature and all three escalations' fixes hold. |

## F. Pipeline state for the Orchestrator

The D44 follow-up batch is **sound**: P3-T06 documents the user-visible feature accurately and only in
`USAGE.txt` + `usage.md`; ESC-056's graph-footprint correction, ESC-057's requirements restatement and ESC-058's
doc entry are all independently verified. No mock endpoint in production code, no assertion weakened, footprint
clean; the full offscreen suite is green per the Orchestrator's own run (`pass`, exit 0). **No open escalations
remain** — ESC-001…ESC-058 are all `addressed`.

Status: REVIEW_COMPLETE
