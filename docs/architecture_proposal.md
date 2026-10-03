# Architecture Proposal — NDThinkChart D17 + D18 (incremental panel-layout change)

> Draft proposal owned by **Plan**. Not canonical. Plan Artifact Editor & Validator
> reads this, checks it against `docs/requirements/requirements.md` (Status:
> `READY_FOR_PLAN`, Batch 11 D17+D18), and writes the canonical
> `docs/architecture.md` / `docs/plan.md`.
>
> **Scope:** an *incremental* change on top of the already-built, green D1–D16
> system (commit `fd0bb0a`; full offscreen suite green). D1–D16 are **frozen** and
> are **not** re-planned. `docs/architecture.md` is the as-built baseline. This is an
> **existing-repo run** — the marker sentence and Current Tech Stack are preserved in
> `requirements.md`; PyQt6 + pyqtgraph is a **hard constraint**.
>
> Evidence note: the D17/D18 "diagnosed facts" in the brief were re-validated against
> the current source (`ui/main_window.py`, `ui/watchlist_panel.py`,
> `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py`, `tests/*`). Where the
> source is authoritative over the requirements narrative, that is noted.

---

## Codebase Summary (existing repository — D17/D18 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2175
> nodes, refreshed 2026-10-03) and then **validated against the current source files**
> (the repository is authoritative). The graph surfaced the relevant communities and
> symbols (`watchlist_max_width`, `clamp_watchlist_width`, `ActiveTraderPanel`,
> `ActivePortfolioPanel`, `MainWindow.__init__`, `test_d10_d13_integration`); every
> claim below was then confirmed by direct inspection of the current tree on
> 2026-10-03.

### Existing components (factual inventory — the D17/D18 surface only)

- **`[existing] ui/main_window.py` — `MainWindow.__init__` central + dock setup**
  (`:205–252`):
  - Central widget is a `QWidget` (`central`) with a `QVBoxLayout` holding the toolbar
    and `ChartPanel`. The **chart area** for D17/D18 purposes is this central region.
  - **Watchlist dock** (`:217–232`): `QDockWidget("Watchlist")` in `LeftDockWidgetArea`;
    `watchlist_panel.setMinimumWidth(150)` (`:225`); the width is restored via
    `load_watchlist_width(...)` and applied with **one** `resizeDocks([watchlist_dock],
    [width], Horizontal)` (`:229–230`). No `setMaximumWidth` anywhere.
  - **Right docks** (`:234–252`): **two separate `QDockWidget`s** —
    `QDockWidget("Active Trader")` and `QDockWidget("Portfolio")`, **both** in
    `RightDockWidgetArea`, with no min/max width and **no `resizeDocks` call**. This is
    the exact shape B2 says must become **one region**.
- **`[existing] ui/main_window.py` — `resizeEvent`** (`:959–970`): calls
  `watchlist_max_width(self.width())` and re-clamps **only when the dock is already
  wider than max**. `resizeEvent` fires on **window** resize, not on a dock-splitter
  drag; there is **no `splitterMoved` / `dockLocationChanged` handler**.
- **`[existing] ui/main_window.py` — `closeEvent`** (`:1379–1387`): persists the
  watchlist width via `save_watchlist_width(self._settings, watchlist_dock.width(),
  self.width())`. Persistence is `QSettings("NDThinkChart", "NDThinkChart")`,
  key `watchlist/width` — **no SQLite change**.
- **`[existing] ui/main_window.py` — DOM toggle** (`:1011–1020`): `_on_dom_toggled`
  finds the dock by `findChild(QDockWidget, "Active Trader")` and flips its visibility.
  This is a **title-based lookup** that the D18 reshaping must keep working.
- **`[existing] ui/main_window.py` — full-screen handling: NONE.** No
  `showFullScreen`, `setWindowState`, `WindowFullScreen`, or full-screen branch exists
  anywhere in `ui/` (confirmed by grep). Full screen is an OS window state.
- **`[existing] ui/watchlist_panel.py`** (`:29–62`): the D13 helpers —
  `WATCHLIST_MIN_WIDTH = 150`, `CHART_MIN_WIDTH = 400`, `DEFAULT_WATCHLIST_WIDTH = 220`,
  `WATCHLIST_WIDTH_KEY = "watchlist/width"`;
  `watchlist_max_width(window_width) = max(150, min(int(W*0.50), W-400))`;
  `clamp_watchlist_width(width, window_width) = max(150, min(width, max_width))`;
  `load_/save_watchlist_width`. **Note:** these are parameterised on **window width**,
  not the chart area, and do **not** account for the right docks — exactly the B1
  denominator defect and the DG24 unaccounted-consumer gap.
- **`[existing] ui/watchlist_panel.py` — `WatchlistPanel`**: emits
  `row_double_clicked` (D14). No width governance of its own.
- **`[existing] ui/active_trader_panel.py` — `ActiveTraderPanel(QWidget)`** (`:410`):
  `QVBoxLayout` (margins 6) with a header row (`QSpinBox` qty 1..100000), a `QTabWidget`
  (`LadderTable`, `BookTable`, `OrderEntryWidget`), and the ladder click wiring. **No
  `setMinimumWidth` / `setMaximumWidth` / `setMinimumSize` / `sizeHint` override** — so
  the ladder/book tables' natural size can demand unbounded width.
- **`[existing] ui/active_portfolio_panel.py` — `ActivePortfolioPanel(QWidget)`**
  (`:27`): `QVBoxLayout` with a summary label, a **10-column** `QTableWidget`
  (`horizontalHeader().setSectionResizeMode(Stretch)`) and a `Refresh` button. **No
  width governance** either.
- **`[existing] ui/chart_panel.py` — `ChartPanel`**: owns a vertical `QSplitter`
  (`price_plot`, `volume_plot`, `osc_plot`) — **inside** the chart area, unrelated to
  the dock widths. `resizeEvent` (`:438`) only repositions the zoom controls and the
  volume toggle. Unchanged by D17/D18.
- **`[existing] tests/`** — four integration/regression tests depend on the right docks:
  - `tests/test_d10_d13_integration.py` (`:33,50–52`): hides docks whose
    `windowTitle()` is `"Active Trader"` / `"Portfolio"`; asserts the **old window-width
    clamp math** (`:120–124`).
  - `tests/test_watchlist_d14_midrag.py`, `tests/test_history_backfill*.py`: hide the
    same two titles to isolate their own concern.
  - `tests/test_crosshair_axis_lane.py` (`:101–105`): resolves `docks["Active Trader"]`
    and `docks["Portfolio"]` by **`windowTitle()`** and asserts the D2 chip does not
    intersect either `frameGeometry()`.
  - `tests/test_watchlist.py`: asserts the helper maths `watchlist_max_width(1400)==700`,
    `watchlist_max_width(600)==200`-ish (`max(150,200)`), `watchlist_max_width(100)==150`.

### Existing data models / tables (unchanged by D17/D18)

`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`,
`OrderBookLevel`, `UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`,
`drawing_groups`, `drawings`, `studies`, `positions`, `trade_groups`,
`position_group_map`. **No schema change for D17/D18** — width is ephemeral view state
plus the existing `QSettings` key.

### Existing integrations in play (unchanged)

IBKR (historical/RT/depth), SQLite, Qt signal bus, **`QSettings`** (watchlist width),
`PyQt6.QtWidgets` dock geometry APIs. **No new external integration** is introduced.

### Key structural facts the D17/D18 design must respect

1. There is **no live width enforcement during a dock drag** anywhere — the cap runs
   only at construction and on window `resizeEvent` (DG23 confirmed).
2. The watchlist cap uses **window width** and **ignores the right docks** (DG24 /
   B1 denominator).
3. The two right docks are **un-owned horizontally** (no min/max, no `resizeDocks`,
   no cap) and are a **separate region each**, not one region (DG24).
4. **Title-based dock lookups** exist in production (`_on_dom_toggled`) and in four
   tests — the reshaping must not silently break `findChild(QDockWidget, "Active Trader")`
   or the `windowTitle()`-keyed test helpers, or, if it must, the tests are updated in
   lockstep (R28/`AC-D18.8`).

---

## Summary

D17/D18 are **pure UI-layout changes within the existing PyQt6 dock architecture** —
no new stack, no new dependency, no schema change, no new integration, and no
touch to the live-order path. The change introduces **one shared, chart-area-relative
width model** and applies it **live, during dock drags and dock/resize events**, to two
regions: the **left watchlist dock** (cap

`floor(0.50 × chart_area)`, min 150px, default ~220px, persisted) and a **single right
dock region** holding the Active Trader ladder and the Portfolio section **stacked
vertically** (cap `floor(0.40 × chart_area)`, inherently equal width by construction).
Both caps are further clamped by a **shared chart-minimum rule** (~400px) so that
enlarging one region can force the other to shrink (`AC-D18.5` / B3), and the right
region is made **fully visible in full screen** (`AC-D18.1`) by bounding its content
minimum width and by an explicit full-screen/`resizeEvent` normalize step. D1–D16
modules are untouched; the D13 helpers are **re-parameterised from window width to
chart area** as the single source of the cap (B1), and the affected D13 tests are
updated in lockstep.

---

## Tech Stack Decisions

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | **Unchanged** `[existing]`: Python 3.11+, PyQt6 (≥6.6), pyqtgraph (≥0.13). "Changing the tech stack" is a stated Non-Goal | Existing-repo hard constraint; D17/D18 are layout fixes only | A nested `QSplitter` layout replacing docks entirely — rejected (out of scope, would re-open D2/D14/QSettings behaviour) |
| Where the live clamp is enforced | **`[new/changed]`** a single `MainWindow._apply_dock_widths()` that reads the **current chart-area width** from `centralWidget().width()` and calls `resizeDocks(...)` for both regions; invoked from a **`QSplitter.splitterMoved`** handler on the dock areas' internal splitter **and** from `MainWindow.resizeEvent`, plus a one-shot `QTimer.singleShot(0, …)` normalize on show. Reuses the D13 helpers as the cap source | The D17 root cause is that nothing hooks the *dock-splitter drag* — only `resizeEvent`. Connecting the actual handle signal enforces the cap **during** the drag (`AC-D17.3`), and one shared function makes left/right cross-clamping coherent (`AC-D18.5`) | A per-dock `eventFilter` on the splitter handle (more fragile, duplicate wiring); a custom `QDockWidget` subclass that overrides `resizeEvent` (Qt’s internal splitter still drives the dock, so the cap would still be missed mid-drag); `setMaximumWidth` only (**rejected as sole mechanism** — it does not implement the *chart-minimum* cross-clamp, and it constrains the widget but not the drag behaviour that D18 needs) |
| Cap denominator | **`[new/changed]`** both caps measured against **`chart_area` = the central widget width** (the region holding the chart, excluding both dock regions), per B1/B2 — **not** `MainWindow.width()` as in D13’s Q25 | B1 corrects D13’s denominator in lockstep; once the right region exists, the point the cap is measured from must exclude both dock regions or the chart starves | Keep window-width denominator (R28: contradicts D17, starves chart with a visible right dock) |
| Watchlist cap formula | **`[new/changed]`** `watchlist_max_width(chart_area_w)` = `max(150, min(floor(0.50 × chart_area_w), chart_area_w − 400))`; the **400px chart minimum is the shared constant** `CHART_MIN_WIDTH` | Preserves the D13 helper name/signature shape (one-arg → int) so tests update minimally; keeps the chart-minimum clamp | A two-argument `(width, chart_area, right_dock_w)` — more call sites to thread; preferred alternative is the *shared* function below |
| Right region cap | **`[new]`** `right_dock_max_width(chart_area_w)` = `max(RIGHT_MIN, min(floor(0.40 × chart_area_w), chart_area_w − 400))` with a small min (e.g. `RIGHT_DOCK_MIN_WIDTH = 200`) | New requirement (D18); symmetric with the watchlist helper; same chart-minimum rule | A hard-coded 40% of window (ignores cross-clamp) |
| Combined cross-clamp (B3) | **`[new]`** one pure function `plan_dock_widths(chart_area_w, requested_left, requested_right)` → `(left, right)` that applies each cap, subtracts both from the chart area, and **shrinks whichever dock is over budget** (preferring to shrink the dock being resized less) until `chart_area ≥ 400` | Makes `AC-D18.5` (“enlarging one forces the other to shrink”) a **pure, unit-testable** rule rather than emergent Qt behaviour; the D13/D17 cap helpers remain the per-dock cap source | Rely on Qt’s own `resizeDocks` negotiation (non-deterministic across platforms; cannot guarantee `chart_area ≥ 400`); clamp only the resized dock (fails `AC-D18.5`) |
| Single right region shape (B2) | **`[new/changed]`** replace the two right `QDockWidget`s with **one** `QDockWidget` containing a `QWidget` whose `QVBoxLayout` stacks **ActiveTraderPanel** over **ActivePortfolioPanel** (optionally via a `QSplitter(Vertical)` so the user can adjust the vertical split, with equal **width** guaranteed by the single region) | B2: one region ⇒ the two sections are **inherently equal width** (`AC-D18.3`) and the 40% cap applies to the region; keeps D2/D10 title lookups working by keeping an identifiable title and a stable object name | Keep two docks and force equal widths via `resizeDocks` on both (fragile; a drag on one still leaves the other ungoverned; violates the “one region” intent) |
| Full-screen visibility (D18) | **`[new]`** (a) bound the **content minimum** of both right panels so the ladder/portfolio tables cannot demand unbounded width (`AC-D18.6`); (b) an explicit **full-screen / `changeEvent(WindowStateChange)` + `resizeEvent` normalize** that re-applies the cap against the *visible* window rect and calls `resizeDocks` so the region is on-screen with non-zero width (`AC-D18.1`) | The reported defect is the region being clipped off-screen; `AC-D18.6` requires content not to force it off-screen; a measurable geometry assertion (dock `geometry()` within window `rect()`, `width() > 0`) is the test condition | Pure content-size-hint change (does not guarantee on-screen geometry); auto-hide (violates “visible in full screen”) |
| Persistence | **`[existing]` for the watchlist** (`QSettings watchlist/width`, re-clamped to the new chart-area cap); **`[new]` explicit “not persisted” for the right region** (A36/`AC-D18.7`) | Q26 still required for the watchlist (B4); the user did not request right-region persistence | Persist the right region too (not requested; broader than the requirement) |
| Tests | **`[existing]`** pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS; add pure-function unit tests for the new helpers + offscreen `MainWindow` geometry tests; **update the D13 clamp-math assertions in lockstep** | Repo standard (Q8/Q9); `AC-D17.6`/`AC-D18.8` require the existing suite green (or updated where B1 changes the denominator) | Manual-only (rejected) |

---

## System Components

Each item is labelled `[existing]`, `[new]`, or `[new/changed]`.

### Central + dock layout
- **`[existing]` central chart area** — `QWidget` + `QVBoxLayout(toolbar, ChartPanel)`;
  its `width()` **is** `chart_area` for all D17/D18 maths. Unchanged structurally.
- **`[existing]` left watchlist dock** — `QDockWidget("Watchlist")` in
  `LeftDockWidgetArea`, min 150px. Kept; gains no new widget of its own.
- **`[new/changed]` single right dock region** — one `QDockWidget` (e.g.
  `QDockWidget("Active Trader")`, with the Portfolio section inside it) whose widget is
  a container `QWidget` with a vertical layout stacking `ActiveTraderPanel` over
  `ActivePortfolioPanel`. This **replaces** the two separate right `QDockWidget`s
  (`ui/main_window.py:234–252`). The container sets a bounded `minimumWidth` and,
  inside it, each panel’s scrollable content is width-bounded so neither can force the
  region off-screen.

### Width governance (the D17/D18 core)
- **`[new]` `ui/dock_layout.py`** (pure, Qt-free where possible) — the shared width
  model:
  - constants `CHART_MIN_WIDTH = 400` (re-exported/kept in agreement with
    `watchlist_panel`), `WATCHLIST_MIN_WIDTH = 150`, `DEFAULT_WATCHLIST_WIDTH = 220`,
    `RIGHT_DOCK_MIN_WIDTH`, right cap fraction `0.40`, watchlist cap fraction `0.50`;
  - `watchlist_max_width(chart_area_w) -> int`;
  - `right_dock_max_width(chart_area_w) -> int`;
  - `plan_dock_widths(chart_area_w, requested_left, requested_right) -> (left, right)`
    — the **B3 cross-clamp** (`AC-D18.5`), pure and exhaustively unit-testable.
  Rationale: keeps the chart-minimum rule in one place and off the widget layer,
  matching the repo’s established **pure-service** pattern (`session_service`,
  `backfill_service`).
- **`[new/changed]` `ui/watchlist_panel.py`** — the D13 helpers
  (`watchlist_max_width` / `clamp_watchlist_width` / `load_/save_watchlist_width`) are
  **re-parameterised to the chart-area denominator** (B1), delegating to
  `ui/dock_layout`. Their one-argument signature shape is preserved so callers and
  tests update minimally.
- **`[new/changed]` `ui/main_window.py`**:
  - `_apply_dock_widths()` — reads `centralWidget().width()`, computes the plan via
    `plan_dock_widths`, and issues `resizeDocks([watchlist_dock], [left], Horizontal)` +
    `resizeDocks([right_dock], [right], Horizontal)`. Idempotent; guarded with
    `blockSignals`/re-entrancy flags so an applied resize does not recurse.
  - A **`splitterMoved` connection** to the dock areas’ internal `QSplitter` (obtained
    after `show()` via the dock’s child splitter, or via a `QDockWidget`-hosted
    `QMainWindow` splitter hook) → `_apply_dock_widths`. This is the piece that makes
    the cap bind **during** the drag (`AC-D17.3`).
  - `resizeEvent` — re-clamps **both** regions (not only when already over max) and in
    **both directions** (`AC-D17.2`/B4), via `_apply_dock_widths`.
  - `changeEvent(WindowStateChange)` — a full-screen normalize step (`AC-D18.1`).
  - `closeEvent` — persists the watchlist width (`[existing]` behaviour retained,
    re-clamped to the new cap).
  - `_on_dom_toggled` — keeps the title-based `findChild(QDockWidget, "Active Trader")`
    lookup valid against the new single region (D18 reshaping must not break it).
- **`[new/changed]` `ui/active_trader_panel.py` / `ui/active_portfolio_panel.py`** —
  add a **bounded minimum/ideal width** to each panel (and make the tables’
  horizontal sizing respect the available width rather than demanding the sum of
  column widths) so content cannot push the region off-screen (`AC-D18.6`). No
  behavioural change to ladder/portfolio logic or signals.

### Unchanged
- **`[existing]` `ui/chart_panel.py`** — the in-chart vertical `QSplitter` is a
  separate concern; no change. The D2 chip’s Y-axis-lane geometry is unaffected by
  dock *width* beyond the already-verified “not covered by the dock” property.
- **`[existing]` D1–D16 modules and the live-order path** — untouched.

---

## Data Model

**No schema change.** D17/D18 are ephemeral view state.

- `[existing]` `QSettings("NDThinkChart", "NDThinkChart")` key `watchlist/width`
  (int, px) — retained; restore is re-clamped to the **new chart-area cap**
  (`AC-D17.4`). No new key is required for the watchlist.
- `[new]` Right region width/visibility is **explicitly not persisted** (A36 /
  `AC-D18.7`).
- `[new]` In-memory-only runtime fields on `MainWindow`: `_watchlist_width`,
  `_right_dock_width`, and re-entrancy guards for `_apply_dock_widths` (no model/table
  changes).
- Existing models/tables (`Bar`, `Position`, …; `bars`, `positions`, …) are unchanged.

---

## Integration Points

- **`[existing]` `QSettings`** — watchlist width persistence; re-clamped on restore.
- **`[existing]` Qt signal bus / dock geometry APIs** — `QSplitter.splitterMoved`,
  `QMainWindow.resizeEvent`, `changeEvent(WindowStateChange)`, `QMainWindow.resizeDocks`
  drive the live clamp. No new external service.
- **`[new]` `MainWindow._apply_dock_widths` ↔ dock widgets** — the single wiring point
  connecting drag/resize/full-screen events to the shared width model.
- **`[existing]` test dock lookups** — `findChild(QDockWidget, "Active Trader")` and the
  `windowTitle()`-keyed helpers in four tests must keep resolving the right region (or
  the tests are updated in lockstep).
- **`[existing]` IBKR / SQLite / pyqtgraph** — unchanged; no new call type, no schema,
  no dependency.

---

## Non-Functional Approach

- **Correctness (live cap, D17):** the cap binds **during the drag** because the width
  plan is recomputed from `centralWidget().width()` on every `splitterMoved`, using the
  D13 helpers as the cap source (`AC-D13.1`, `AC-D17.1`–`AC-D17.3`). Both directions
  work because the clamp is two-sided (min 150px, cap) (`AC-D17.2`/B4).
- **Correctness (single right region + equal width, D18):** one region ⇒ the stacked
  Active Trader and Portfolio sections share the region width by construction
  (`AC-D18.3`); the 40% cap applies to the region (`AC-D18.2`).
- **Correctness (chart minimum / cross-clamp, B3):** `plan_dock_widths` guarantees
  `chart_area ≥ 400px`; enlarging one region shrinks the other when needed
  (`AC-D18.5`). The rule is a pure function, so it is unit-testable independent of Qt.
- **Correctness (full-screen visibility, D18):** `AC-D18.1` is made measurable — the
  right region’s `geometry()` lies within the window `rect()` with `width() > 0`, and
  content minimums cannot force it off-screen (`AC-D18.6`). **No `showFullScreen` call
  is added**; the normalize hook reacts to the OS full-screen/WM state change and to
  resize.
- **Persistence (`AC-D17.4`):** the watchlist width survives restart, restored as an
  int px value clamped to the current chart-area cap (default ~220px, never <150px);
  the right region is not persisted (`AC-D18.7`).
- **Performance:** `_apply_dock_widths` is O(1) (no bar/table iteration); it runs on
  drag/resize events only, and is guarded against recursive resize loops. No per-frame
  cost added to chart rendering.
- **High-DPI / small displays:** the ~400px chart minimum plus the per-dock minimum
  yields gracefully on a small full-screen display (edge case in D18); when
  `floor(0.40 × chart_area) < region minimum`, the region minimum wins and the
  chart-minimum rule still applies.
- **Security / live-order path:** untouched; Q9 holds — no automated test connects to
  live TWS or transmits an order. D18’s reshaping changes only the container around the
  ladder, not any order signal or handler.
- **Regression (`AC-D17.6`/`AC-D18.8`):** D1–D16 stay frozen; the D13 clamp-math
  assertions in `tests/test_watchlist.py` and `tests/test_d10_d13_integration.py` are
  updated **in lockstep** to the chart-area denominator (never left contradicting D17),
  and the title-based dock helpers keep working.

---

## Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Hooking the dock-area internal `QSplitter.splitterMoved` is Qt-version-layout dependent and may not fire as expected | M | Obtain the splitter defensively after `show()`; **fall back to a `QDockWidget.eventFilter` on the dock/its handle** and to `resizeEvent`; unit-test the pure `plan_dock_widths` independently of the event source so the *rule* is verified even if a wiring path is Qt-dependent |
| `_apply_dock_widths` calling `resizeDocks` re-triggers `splitterMoved`/`resizeEvent` → recursion / jitter | M | Re-entrancy guard flag around the apply; only call `resizeDocks` when the computed sizes differ from current by >1px; `blockSignals` on the splitter during application |
| Re-shaping two docks into one region breaks title-based lookups (`_on_dom_toggled`, `test_crosshair_axis_lane.py`, `test_d10_d13_integration.py`, `test_watchlist_d14_midrag.py`, `test_history_backfill*.py`) (R28/`AC-D18.8`) | M | Keep a stable, identifiable dock title (and an `objectName`); update the four tests in lockstep where the shape genuinely changes; assert the D2 chip/dock non-overlap (`test_crosshair_axis_lane`) still holds against the single region |
| Content minimum width (wide ladder / 10-column portfolio table) forces the region off-screen despite the cap (`AC-D18.6`) | M | Bound each panel’s `minimumWidth`/`sizeHint` and let the tables scroll/clip internally; the geometry test asserts the region stays within the window and within the cap with wide content |
| `chart_area ≥ 400px` cannot be honoured on a tiny window when both dock minimums plus chart minimum exceed the width | L | Document the precedence (chart minimum wins; docks yield to their minimums) as the D13/D18 edge case already allows; assert no crash and stable geometry |
| Existing D13 tests encode the **old window-width** clamp math and could be left contradicting D17 (R28) | M | Update the assertions in `tests/test_watchlist.py` and `tests/test_d10_d13_integration.py` to the chart-area denominator as part of the same change set; treat “green but contradicting” as a failure |
| Full-screen normalize fires before the window is laid out and computes against a stale rect | L | Use a one-shot `QTimer.singleShot(0, …)` after the state change plus the `resizeEvent` path; the geometry assertion catches a missed normalize |
