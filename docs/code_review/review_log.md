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

Status: REVIEW_COMPLETE
