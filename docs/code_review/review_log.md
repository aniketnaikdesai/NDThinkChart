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

Status: REVIEW_COMPLETE
