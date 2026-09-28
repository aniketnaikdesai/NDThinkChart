# Code Review Escalations — NDThinkChart

**Source review:** `docs/code_review/review_log.md` (revision `09070e8`, 2026-09-27).
**Note:** none of these entries are marked `addressed` — this is the first pass.

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
- **Status: ESCALATED_TO_BUILD**

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
- **Status: ESCALATED_TO_PLAN**

## ESC-003 — Volume nice-tick list is coarse above 10M

- **Linked task/defect:** T12 (D8)
- **Observed:** `_nice_volume_max` (`ui/chart_panel.py:45–55`) rounds above the 10M list entry to
  coarse 5M steps (`10.5M→15M`, `45M→50M`, `50M→60M`), and `10,000→50,000`. Existing test only
  reaches 2.2M (`tests/test_volume_linear.py:55–64`).
- **Expected:** a scaling nice-number formula; original list kept as a test fixture; a test at 40–50M.
- **Root cause:** fixed lookup list with a coarse fallback rather than a continuous nice-number scale.
- **Suggested direction:** replace with a 1/2/2.5/5×10^k generator; keep the old list as the
  fixture; assert monotonic, tight coverage at 40–50M.
- **Status: ESCALATED_TO_BUILD**

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
- **Status: ESCALATED_TO_REQUIREMENTS**

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
- **Status: ESCALATED_TO_TASK_MANAGER**

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
- **Status: ESCALATED_TO_BUILD**

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
- **Status: ESCALATED_TO_BUILD**

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
- **Status: ESCALATED_TO_BUILD**

## ESC-009 — High-DPI claims are not exercised

- **Linked task/defect:** T9 (D6 wick), T15 (D11 labels), T20
- **Observed:** `docs/architecture.md:112` claims D6/D11 are "device-pixel aware", but a repo search
  finds no `devicePixelRatio` / `QT_SCALE_FACTOR` / `dpr` anywhere in `tests/`, `ui/`, or `docs/`.
  The `qapp` fixture (`tests/conftest.py:91–98`) runs at DPR 1.0.
- **Expected:** at least one parametrized run at `QT_SCALE_FACTOR=2`.
- **Root cause:** test harness uses a single scale factor; DPI claims rest on unrun assertions.
- **Suggested direction:** Task Manager adds a DPR=2 parametrized/session run asserting wick/body
  separation and label-in-bounds for D6 and D11.
- **Status: ESCALATED_TO_TASK_MANAGER**

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
- **Status: ESCALATED_TO_TASK_MANAGER**

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
- **Status: ESCALATED_TO_REQUIREMENTS**

---

## Verified with no escalation

- **E4 — D12 zone "Extend" removal / payload migration:** verified clean. No persisted extend flag
  (`data/db.py:59–67`), zone payload is `{"x1","x2","y1","y2"}` only
  (`services/drawing_service.py:61–71`), rendering consumes `y1/y2` (`ui/drawing_overlay.py:275–284`),
  dialog omits the control (`ui/zone_settings_dialog.py:4–5`, `:54`). Prior zones render unchanged;
  no migration required.
