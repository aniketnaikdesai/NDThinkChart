# Architecture Proposal — NDThinkChart Batch 13 (D19: toolbar scroll/elide wrapper)

> **Scope.** An *incremental* change on top of the **already-built, green D1–D18** system
> (commit `5bd7c93`; full offscreen suite **566 passed**). D1–D18 are **frozen** and are
> **not** re-planned. This is an **existing-repo** run: `requirements.md` contains the marker
> sentence `This is an existing repository.` and a Current Tech Stack; **PyQt6 + pyqtgraph is
> a hard constraint**. No stack change, no schema change, no new dependency, no new external
> integration, and no live-order-path change. Items are labelled `[existing]`, `[new]`, or
> `[new/changed]`.
>
> **Defect.** D19 — the toolbar's ~1716px `minimumSizeHint` sits inside the central widget and
> pins it, so the D17/D18 dock-width behaviour is not effective in the real (toolbar-visible)
> app. The D17/D18 test harnesses hid the toolbar, masking it (`DG27`/`DG28`). **Decision
> (B5, 2026-10-05):** wrap the toolbar in a **horizontal scroll / elide** container **in
> place** — it stays inside the central widget as a single ~36px row. **B6:** the watchlist cap
> stays `floor(0.50 × chart_area)`.
>
> Companion proposal: `docs/plan_proposal.md`. As-built baseline: `docs/architecture.md`.
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D19 / Journey
> 20 / `AC-D19.1`–`AC-D19.7`; A37–A38; R32–R34; B5–B6 answered 2026-10-05; DG27–DG28).

---

## Codebase Summary (existing repository — D19 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2366 nodes,
> refreshed 2026-10-05) and then **validated against the current source files** (the repository
> is authoritative). The graph surfaced the relevant symbols (`MainWindow`,
> `_apply_dock_widths`, `_chart_area_width`, `WatchlistPanel`, `test_dock_widths_d18`,
> `test_dock_layout`); every claim below was confirmed by direct inspection of the current tree
> on 2026-10-05.

**Toolbar construction — `[existing] ui/main_window.py:100–211`**
- `toolbar = QWidget()`; `toolbar.setFixedHeight(36)`; inline stylesheet
  (`background: #101218; border-bottom: 1px solid #232938;`).
- `tb_layout = QHBoxLayout(toolbar)`, margins `(8, 0, 8, 0)`, spacing `6`.
- Fixed-width controls: `symbol_input` 120, `tf_combo` 90, `mode_combo` 110, `sound_btn` 56,
  `ext_hours_btn` 80, `tz_combo` 110, `draw_combo` 110, `draw_set_combo` 140,
  `draw_delete_btn` 38; plus variable-width buttons/labels (`Load Chart`, `Studies…`,
  `Alarms (0)`, `Alarm Mode`, `DOM`, `Sets…`, `Symbol:`, `TF:`, `Mode:`, `Draw:`, `|`).
- Layout order ends with `tb_layout.addStretch()` then `conn_badge` (`QLabel("● Connecting")`,
  `:186–187`, `:210–211`). The stretch means the badge is pushed to the right edge.
- **Consequence:** the toolbar's `minimumSizeHint().width()` is ≈ **1716px** (sum of the
  fixed widths + labels + spacings + button size hints).

**Central-widget composition — `[existing] ui/main_window.py:213–223`**
- `self.chart_panel = ChartPanel(tz_offset=…)`; `central = QWidget()`;
  `vbox = QVBoxLayout(central)` (margins `0`, spacing `0`); `vbox.addWidget(toolbar)`;
  `vbox.addWidget(self.chart_panel)`; `self.setCentralWidget(central)`.
- **Consequence:** `centralWidget().minimumSizeHint().width()` is therefore ≈ 1716px, so
  `QMainWindow` cannot shrink the central area below it and the dock splitter has no slack.

**Chart-area denominator + D17/D18 width model — `[existing]`**
- `MainWindow._chart_area_width()` (`:1027–1038`) returns `centralWidget().width()`, falling
  back to `self.width()` when the central widget is absent/not yet laid out.
- `MainWindow._apply_dock_widths()` (`:1101–1168`) is the **single apply entry point**; it
  reads `_chart_area_width()`, plans via `_plan_dock_widths()` (`:1055–1099`), and issues
  `resizeDocks`. It is driven by the dock event filter (`:1350–1363`), `resizeEvent`
  (`:1381–1390`), `changeEvent(WindowStateChange)` (`:1365–1379`), the deferred normalize
  (`_deferred_dock_setup`, `:1238–1257`) and `right_dock.visibilityChanged`
  (`_on_right_dock_visibility_changed`, `:1259–1271`).
- `ui/dock_layout.py` (`[existing]`, pure, Qt-free) is the single source of truth:
  `CHART_MIN_WIDTH = 400`, `WATCHLIST_MIN_WIDTH = 150`, `DEFAULT_WATCHLIST_WIDTH = 220`,
  `RIGHT_DOCK_MIN_WIDTH = 200`, `WATCHLIST_CAP_FRACTION = 0.50`,
  `RIGHT_DOCK_CAP_FRACTION = 0.40`; `watchlist_max_width`, `right_dock_max_width`,
  `plan_dock_widths` (B3 cross-clamp).
- Single right dock region — `[existing] ui/main_window.py:264–306`: one `QDockWidget("Active
  Trader")` (objectName `"Active Trader"`) whose container stacks `ActiveTraderPanel` over
  `ActivePortfolioPanel`; the region keeps the title/objectName so `_on_dom_toggled`'s
  `findChild(QDockWidget, "Active Trader")` resolves it.
- Watchlist dock — `[existing] ui/main_window.py:225–262`: `QDockWidget("Watchlist")` in
  `LeftDockWidgetArea`, `setMinimumWidth(WATCHLIST_MIN_WIDTH)`.

**Affected D17/D18 test harnesses (the masking) — `[existing] tests/`**
Five test modules locate the toolbar through the central layout and hide it, exactly as DG28
records. After the D19 fix, `centralWidget().layout().itemAt(0).widget()` returns the **scroll
wrapper**, not the toolbar:
- `tests/test_dock_widths_d17.py:67–72` — `_make_window` hides the toolbar (its docstring at
  `:10–12` admits it "pins the central widget … masking the very behaviour under test").
- `tests/test_dock_widths_d18.py:111–116` — same masking.
- `tests/test_dock_widths_d18_impl.py:67–72` — same masking.
- `tests/test_dock_d18_region.py:46–51` — same masking.
- `tests/test_dock_layout.py:315–319` — same masking.

**Existing data models / tables — unchanged by D19**
`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`, `OrderBookLevel`,
`UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`,
`studies`, `positions`, `trade_groups`, `position_group_map`. **No schema change.**

**Existing integrations in play — unchanged by D19**
IBKR historical/RT data, SQLite, the Qt signal bus, `QSettings("NDThinkChart","NDThinkChart")`
key `watchlist/width`, and `PyQt6.QtWidgets` dock/geometry APIs. **No new external
integration.**

**Key structural fact the D19 design must respect.**
The toolbar's width enters the central widget's `minimumSizeHint` purely because the toolbar is
a direct `QVBoxLayout` child with no horizontal-shrink affordance. Wrapping it in a horizontal
`QScrollArea` removes that width from the central minimum without moving the toolbar out of the
central widget and without touching any control's construction or signal wiring.

---

## Summary

D19 is a **minimal, in-place UI change**. The existing toolbar `QWidget` is wrapped in a
horizontal `QScrollArea` (no frame, `setWidgetResizable(False)`, horizontal
`ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`) whose height is fixed at **36px**, and the
wrapper is inserted into the central widget's `QVBoxLayout` **where the bare toolbar was**. The
toolbar therefore contributes only a small minimum width to the central widget, which can now
shrink; the **already-built** D17/D18 width model then becomes effective in a toolbar-visible
window. Nothing else changes: the watchlist cap (`floor(0.50 × chart_area)`, B6), the pure
`ui/dock_layout.py` model, `_apply_dock_widths`, the single right dock region, and all D1–D18
behaviour are untouched.

---

## Tech Stack Decisions

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | **Unchanged `[existing]`:** Python 3.11+, PyQt6 (`≥6.6`), pyqtgraph (`≥0.13`). "Changing the tech stack" is a stated Non-Goal | Existing-repo hard constraint; D19 is a layout fix only | A new toolbar framework / embedded web view (out of scope, no dependency allowed) |
| Dock width model | **Unchanged `[existing]`** `ui/dock_layout.py` — cap constants and `plan_dock_widths` are **not** touched | **B6** keeps the watchlist cap at `floor(0.50 × chart_area)`; D19 fixes only the toolbar pinning | Change the cap (explicitly **not** adopted, B6) |
| Test stack | **Unchanged `[existing]`** pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS | Repo standard (Q8/Q9); the regression guard is offscreen | Manual-only (rejected) |
| **Toolbar overflow mechanism** | **`[new/changed]`** wrap the existing toolbar `QWidget` in a **`QScrollArea`** (no frame, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`), inserted into the central `QVBoxLayout` **in place of the bare toolbar** | Standard Qt class, no new dependency; removes the toolbar's ~1716px width from the central widget's minimum while keeping it **inside the central widget** as one row (B5); the pure `QScrollArea` does the shrink/scroll with no per-control changes | (b) wrap to multiple rows, (c) compress/overflow `»` menu, (d) move to `QMainWindow.addToolBar` — **all explicitly not adopted (B5)**. Also: `QScrollArea` with `setWidgetResizable(True)` or a default always-on scrollbar — **passed over** (would let the toolbar reflow/grow or reserve a scrollbar lane and break the single-row height) |
| **Toolbar row height** | **`[new/changed]`** wrapper height fixed at **36px**; the horizontal scrollbar is **overlay/transient** (FI-D19-1) so it does not add height | `AC-D19.4` requires the laid-out toolbar height to stay `<= ~40px` (one row); a reserved scrollbar lane would add ~15px and break it | A normal (non-overlay) horizontal scrollbar lane (~51px total) — rejected |
| **`conn_badge` placement** | **`[existing]` behaviour retained:** `conn_badge` stays **inside the scroll region** and scrolls with the toolbar (FI-D19-2) | Keeps the toolbar a single uniform scrollable row; no split widget | Pin the badge outside the scroll region (splits the row / adds a second layout) — not adopted |
| **Toolbar identification for tests** | **`[new]`** give the toolbar and its scroll wrapper stable `objectName`s (e.g. `"MainToolbar"` / `"ToolbarScroll"`) | After wrapping, `centralWidget().layout().itemAt(0).widget()` is the **wrapper**, not the toolbar; the affected harnesses must locate by name (and stop hiding) | Continue keying on `itemAt(0)` — fragile and semantically wrong once wrapped |
| **Watchlist cap** | **Unchanged `[existing]`** `floor(0.50 × chart_area)` (B1/B6) | B6: the formula was never the problem; D19 fixes only the toolbar pinning | Raise the cap — **not adopted (B6)** |
| Persistence | **No change:** `[existing]` `QSettings watchlist/width` for the watchlist; no new key; right region still not persisted (A36) | D19 adds no user-visible state | Persist the toolbar scroll position — not requested |

---

## System Components

Each item is labelled `[existing]`, `[new]`, or `[new/changed]`.

- **`[existing]` central chart area** — `QWidget` + `QVBoxLayout` in `ui/main_window.py`
  (`:217–223`). Structurally unchanged; it now holds the scroll wrapper instead of the bare
  toolbar. Its `width()` remains `chart_area` for the D17/D18 maths.
- **`[new/changed]` toolbar scroll wrapper** — a `QScrollArea` created in
  `ui/main_window.py`, inserted into the central `QVBoxLayout` in the toolbar's slot. No frame,
  `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`,
  fixed height **36px**, stable `objectName` (`"ToolbarScroll"`). This is the whole D19
  mechanism.
- **`[existing]` toolbar `QWidget` and controls** (`ui/main_window.py:100–211`) — construction,
  fixed widths, signal wiring, and `conn_badge` are **unchanged**; the widget is reparented
  into the scroll wrapper (and gains `objectName` `"MainToolbar"`).
- **`[existing]` D17/D18 width model** — `ui/dock_layout.py`, `MainWindow._chart_area_width`,
  `MainWindow._apply_dock_widths`, the dock event filter, `resizeEvent`, and
  `changeEvent(WindowStateChange)`. **Unchanged.** D19 only lowers the central widget's
  minimum so this model can take effect in a toolbar-visible window.
- **`[existing]` watchlist dock** and **`[existing]` single right dock region** — unchanged.
- **`[new/changed]` affected D17/D18 test harnesses** — `tests/test_dock_widths_d17.py`,
  `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`,
  `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`: remove the `toolbar.hide()`
  masking and exercise a **toolbar-visible** window, plus at least one D17 and one D18
  toolbar-visible regression guard (`AC-D19.6`).

---

## Data Model

**No schema change. No new persisted state.**

- `[existing]` `QSettings("NDThinkChart", "NDThinkChart")` key `watchlist/width` (int, px) —
  retained unchanged (B6 keeps the cap; the restore clamp is unchanged).
- `[new]` none. D19 adds only two in-memory `objectName` strings (toolbar, scroll wrapper) —
  ephemeral widget state, not a model.
- `[existing]` Right-region width/visibility is still not persisted (A36); no new key.
- Existing models/tables (`Bar`, `Position`, …; `bars`, `positions`, …) are unchanged.

---

## Integration Points

- **`[new]` `MainWindow` ↔ `QScrollArea`** — the one new wiring point: the toolbar is set as
  the scroll area's widget and the scroll area is added to the central `QVBoxLayout` in the
  toolbar's place. Uses only existing PyQt6 widgets; **no new external service, dependency, or
  IBKR call shape**.
- **`[existing]` Qt layout / dock geometry APIs** — `QMainWindow.setCentralWidget`,
  `QVBoxLayout`, `QMainWindow.resizeDocks`, `resizeEvent`, `changeEvent(WindowStateChange)`,
  `QSplitter`/event-filter fallback — unchanged.
- **`[existing]` D17/D18 clamp path** — `_chart_area_width()` → `_apply_dock_widths()` now
  reads a smaller central minimum; the code itself is unchanged. The B3 cross-clamp
  (`plan_dock_widths`) is unaffected.
- **`[existing]` `QSettings`** — unchanged.
- **`[existing]` test dock/toolbar lookups** — the five affected harnesses must resolve the
  toolbar/wrapper by `objectName` (or simply stop hiding it) rather than by
  `itemAt(0).widget()`.
- **`[existing]` IBKR / SQLite / pyqtgraph** — unchanged; no new call type, no schema, no
  dependency.

---

## Non-Functional Approach

- **Correctness (central widget can shrink — `AC-D19.4`/`AC-D19.5`):** wrapping the toolbar in
  a horizontal `QScrollArea` removes its ~1716px width from
  `centralWidget().minimumSizeHint()`. Target: `centralWidget().minimumSizeHint().width() <=
  CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH + RIGHT_DOCK_MIN_WIDTH` (= **750px**); the adopted
  in-memory probe measured **1716 → 88**.
- **Correctness (single ~36px row — B5 / `AC-D19.4`):** the wrapper's height is fixed at 36px,
  the vertical scrollbar is always off, and the horizontal scrollbar is overlay/transient
  (FI-D19-1) so the laid-out toolbar height stays `<= ~40px`.
- **Correctness (controls stay reachable — B5 / `AC-D19.4`):** the toolbar keeps its full
  natural width inside the scroll content, so at a narrow window every control is reachable by
  horizontal scrolling; no control is removed, elided away permanently, or made unreachable.
- **Correctness (D17/D18 effective in a toolbar-visible window — `AC-D19.1`–`AC-D19.3`,
  `AC-D19.7`):** once the central widget can shrink, `_apply_dock_widths` (unchanged) can drive
  the watchlist to `floor(0.50 × chart_area)` and keep the right region on-screen with the
  chart `>= 400px`. The adopted probe measured the watchlist growing to **508px at chart_area
  1200** with the toolbar visible (pre-fix it stayed pinned at 150).
- **Performance:** O(1) layout change; the scroll area adds no per-frame cost and no
  bar/table iteration. No change to the dock clamp's cost profile.
- **High-DPI / font scaling:** the toolbar's minimum hint may grow with font scaling, but the
  wrapper still lets the central widget shrink (R34). The single-row height is enforced by the
  fixed container height.
- **Security / live-order path:** untouched; Q9 holds — no automated test connects to live TWS
  or transmits an order. The ladder/order signals are unaffected.
- **Regression (`AC-D19.7`):** D1–D18 stay frozen; the affected D17/D18 harnesses are updated
  in lockstep (masking removed) rather than left contradicting D19.

---

## Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| The overlay/transient horizontal scrollbar is not honoured on some platform/style, so the scrollbar lane grows the toolbar row past ~40px (`AC-D19.4`) | M | Fix the wrapper height at 36px and set vertical `ScrollBarAlwaysOff`; assert the laid-out height `<= ~40px` in the toolbar-visible test (FI-D19-1) |
| A control becomes unreachable at the narrowest feasible width (B5's "no control permanently unreachable") | M | Keep the toolbar's full natural width inside the scroll content; assert the horizontal scroll range `> 0` and that all controls remain descendants of the scroll content at a narrow window (`AC-D19.4`) |
| Removing the `toolbar.hide()` masking makes the existing D17/D18 suite fail until the fix lands; the suite is not green in between | M (expected) | R33: the harness change is part of the fix; demonstrate the pre-fix red then green after (Phase 2 / `AC-D19.6`) |
| The offscreen toolbar minimum width differs from the real macOS window, so a scroll fix that only works offscreen could still fail in the real app (R34) | M | `AC-D19.6` requires a toolbar-visible window; also verify in the real dev build (`python main.py`) manually (R34) |
| The five affected harnesses locate the toolbar via `centralWidget().layout().itemAt(0).widget()`, which after the fix is the **wrapper**; a stale lookup could hide the wrong widget or silently no-op | M | Give the toolbar and wrapper stable `objectName`s; update the five harnesses in lockstep to locate by name (or simply stop hiding) |
| The wrapper accidentally changes the chart-area denominator or dock caps, breaking D17/D18 | M | Do not touch `ui/dock_layout.py`, `_chart_area_width`, or `_apply_dock_widths`; B6 keeps the cap constant; D17/D18 tests stay green in a toolbar-visible window |
| `conn_badge`/trailing stretch placement changes when wrapped (e.g. badge pinned outside) | L | Keep `conn_badge` inside the scroll region (FI-D19-2); assert the toolbar's control set is unchanged |
| Full-suite flakiness (shared on-disk test DB / collection-order SIGSEGV) is mistaken for a D19 regression | L | Per project memory, confirm any non-reproducible failure with a clean full-suite run before treating it as a regression |
| A D1–D18 behaviour regresses because the central widget is now smaller in existing tests | M | Full offscreen suite re-run (Phase 3, `AC-D19.7`); no D1–D18 production file is modified |

---

## Implementation Phases (summary)

Full ordered phases, coverage map, `touches_files` sequencing, and plan-level assumptions are
in **`docs/plan_proposal.md`**.

1. **Phase 1 — Toolbar scroll/elide wrapper in place** `[new/changed]`: wrap the toolbar in the
   `QScrollArea` in `ui/main_window.py`; objectNames; fixed 36px row. Covers `AC-D19.4`,
   `AC-D19.5`.
2. **Phase 2 — Remove test masking + toolbar-visible regression guard** `[new/changed]`: update
   the five affected test harnesses to a toolbar-visible window and add the guard. Covers
   `AC-D19.1`–`AC-D19.3`, `AC-D19.6`.
3. **Phase 3 — Regression + real-app verification** `[new/changed]`: full offscreen suite green
   and manual dev-build confirmation. Covers `AC-D19.7`, R34.
