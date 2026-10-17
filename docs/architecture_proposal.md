# Architecture Proposal — NDThinkChart Batch 19 (**D44**): the collapsed Watchlist becomes a thin vertical bar that expands back to the full panel

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical architecture —
> `docs/architecture.md` is written by Plan Artifact Editor & Validator after validation. Companion:
> `docs/plan_proposal.md` (phases, per-file `touches_files` map, tests, assumptions, flagged issues, the
> correction record). Module index: `docs/codebase-map.md` (refreshed for this batch).
>
> **Run shape:** **legacy single-scope** — the invocation preamble carries **no `phase: P<n>`**, so the
> proposal files are the unsuffixed `docs/architecture_proposal.md` / `docs/plan_proposal.md`, and the D44
> increment merges into the cumulative canonical docs as a `## D44 increment` section (the D16–D42 precedent).
> Every decision below therefore carries an explicit **relationship label** (`[new in D44]` /
> `[extends D21.11: …]` / `[revises D13/D17: …]`) rather than a phase-relative one.
>
> **This file replaces the stale D42 draft** (the previous contents of `docs/architecture_proposal.md`). The
> D42 batch is **delivered** — 26/26 tasks, full offscreen suite green, review `REVIEW_COMPLETE`, committed —
> and its Validator cycle ended `Status: APPROVED` (`docs/plan_review.md`, D42 cycle 3 of 3). **D1–D43 are
> settled and are NOT re-planned or reopened here**; this is a new increment on the same repository.
>
> **Scope: D44 only** — an **owner-requested net-new UI feature** (recorded 2026-10-16, Batch 19). Requirements
> of record: `requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-16 17:28) — the D44 status/audit
> block (`:118`–`:136`), the revised `## Non-Goals` (`:258`–`:267`), the D44 work item (`:353`–`:365`),
> **Journey 37** (`:976`–`:989`), **`### D44`** (`:3782`–`:3925`), **`AC-D44.1`–`AC-D44.8`**
> (`:3854`–`:3891`), the supersession/revision record (`:3892`–`:3905`), the edge cases (`:3906`–`:3913`),
> the correction record (`:3914`–`:3925`), **A75–A78** (`:4005`–`:4008`), **R66–R67**
> (`:4129`–`:4130`), the Batch-19 summary (`:4239`–`:4246`); `design_gaps.md` **DG74**; `open_questions.md`
> **Q54** (answered 2026-10-16 — owner confirmation requested, non-blocking defaults recorded).
>
> **Frozen baseline:** `main` @ **`0c4d478`** (D43 + the D42/Stage-C follow-ups complete; full offscreen suite
> green). Suite invocation: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point
> has a stale shebang).
>
> **Escalation state at planning time:** **no escalation is open against this increment's decisions** — no
> `PLAN`-, `BUILD`- or `REQUIREMENTS`-routed entry is open (`ESC-050` is `addressed`). The single open entry in
> `docs/code_review/escalations.json` is **ESC-055** (`routed_to: TASK_MANAGER`, the D42/ESC-050 enumeration
> rule's *ownership remedy*), which D44 **applies** (`AP-D44-8`) without absorbing it.
> `docs/plan_review.md` is the **APPROVED** D42 cycle (not `CHANGES_REQUIRED`), so this is a normal forward
> cycle.
>
> **Revision record.** **Revision 1 (2026-10-16) — the D44 draft.** No `CHANGES_REQUIRED` cycle precedes it:
> the D42 review ended APPROVED and the requirements were then extended with D44 (Batch 19), so this is a
> fresh increment rather than a revision of a rejected one.
>
> **Out of scope (not planned here):** every earlier defect/feature (D1–D43) and their delivered artifacts.
> No D44 path reaches the chart renderer, the load path, the backfill/planner, the bar cache, the alarms, the
> drawings/studies, the orders machinery, the right dock, or the D42/D43 data paths. **No new dependency, no
> stack change** — in particular the **pyqtgraph chart stack is a locked decision** (`docs/memory.md`
> Orchestrator Log, 2026-10-16: the Lightweight Charts migration was evaluated and **declined**; do not
> re-propose it) and D44 does not touch the rendering stack at all.

---

## Relationship to prior increments

| Prior decision / component | Relationship | Note |
|---|---|---|
| **D21.11 collapse** — `WatchlistPanel.header_bar` + `header_button` + `_on_header_toggled` (`ui/watchlist_panel.py:294`–`:317`, `:435`–`:445`), the public `set_collapsed`/`toggle_collapsed`/`is_collapsed` (`:447`–`:461`), `setTitleBarWidget(self.watchlist_panel.header_bar)` (`ui/main_window.py:381`), `AC-D21.11.2`/`AC-D21.11.3` (collapsed = the struck header button stays visible) | **`[revises D21.11: the collapsed appearance]`** | D44 **changes the collapsed *appearance*, not the collapse mechanism**: the collapsed state renders the thin bar instead of the struck header button. `AC-D21.11.2`/`.3` are **superseded for the collapsed state** (recorded, never silent); `AC-D21.11.1` (single "Watchlist" label; the header strip is the title bar) is **unchanged**, and the `set_collapsed`/`toggle_collapsed`/`is_collapsed` API is **preserved**. |
| **D13/D17 width model** — `WATCHLIST_MIN_WIDTH = 150` (`ui/dock_layout.py:24`), `plan_dock_widths`'s unconditional clamp (`:89`), `_apply_dock_widths`'s direct clamp in the right-dock-hidden branch (`ui/main_window.py:2527`), `AC-D13.1`/`AC-D17.2`'s 150px minimum, `AC-D13.2`/`.3`/`AC-D17.1`/`.3`–`.6` (cap, persistence, drag enforcement, re-clamp) | **`[revises D13/D17: the 150px minimum's scope]`** | The **150px minimum becomes expanded-state only**; while collapsed the width is `WATCHLIST_COLLAPSED_WIDTH`. The cap (`floor(0.50 × chart_area)`), the `CHART_MIN_WIDTH` cross-clamp, the persistence (`watchlist/width`), the drag enforcement and the re-clamp are **unchanged for the expanded state**. |
| **D21.13 collapsed-region pin** — `_sync_right_dock_collapse` (`ui/main_window.py:2374`–`:2411`): relax the dock's **and** the panel's minimum width, `_resize_docks_guarded`, then re-apply on the next event-loop turn because "the dock's layout minimum is recomputed on the next layout pass, so the immediate resize above can be clamped back to the pre-collapse minimum" | **`[extends D21.13: the collapsed-min-width pin pattern]`** | D44's collapsed watchlist reuses **that proven mechanism** (`S24`) instead of inventing a second one — the same defect class (a stale Qt layout minimum re-imposing the expanded minimum) with the same remedy. |
| **D17/D18/B3 pure dock model** — `ui/dock_layout.py` (`plan_dock_widths`, `watchlist_max_width`, `right_dock_max_width`), `MainWindow._plan_dock_widths`'s fixed-point iteration, the `CHART_MIN_WIDTH` cross-module invariant | **`[extends D17/D18: the pure width model]`** | The collapsed rule lives **in the pure model** (`S23`), for the repo's recorded reason (`docs/memory.md` 2026-10-03: the pure helper is the single source of truth; a consumer-side workaround masks helper defects — the ESC-026 lesson). The new parameter defaults to today's expanded behaviour, so every existing caller and suite is untouched. |
| **D21.11's dock title bar (DG37)** — the header strip **is** the dock's title bar; deleting the duplicate title would otherwise leave the dock un-draggable; `DockWidgetMovable | DockWidgetFloatable` are retained | **`[extends D21.11: the title-bar/drag affordance]`** | While collapsed the title-bar slot must still hold a draggable widget, so D44 keeps a 30px handle there (`S25`); the dock's `objectName`/window title and features are unchanged (title-keyed dock lookups stay valid — `docs/memory.md` 2026-10-03). |
| **D21.5 columns / D22.1 `+` / D39.1 search** — all live inside `header_bar`; the table's `horizontalHeader()` is the column-header row | **`[extends D21.5/D22/D39: the header strip's contents]`** | A77: while collapsed the strip, the `+` and the column-header row are hidden and return on expand. **No D22/D39/D21.5 behaviour changes** — they are reachable the instant the user expands. |
| **VIS-D21 conventions** — `ui/visual_conventions.py::set_button_active` (VIS-D21.2), `DiagonalStrikeButton` (VIS-D21.1), `ACTIVE_PROPERTY = "active"` | **`[extends D21.7/D21.8: the shared highlight convention]`** | The bar's hover/pressed feedback goes through **`set_button_active`** (`AC-D44.6`) — no hand-rolled highlight; `set_button_active` itself is **unchanged** (frozen, below). VIS-D21.1 keeps applying to genuinely hidden/off **buttons** elsewhere (D21.12 volume, D21.13 portfolio). |
| **D14 double-click / D21.5 popup / D22 add-remove / D39 search** | **`[no relationship]`** | Untouched; the frozen-interface list pins their contracts. |
| **D42 (width/cache/depth) and D43 (priming bar size)** | **`[no relationship]`** | D44 touches neither the chart renderer, the load path, the planner, the bar cache nor the priming path. |
| **D41 (right dock = Portfolio-only) / D40 (TWS lifecycle)** | **`[no relationship]`** | The right dock's cap/header/collapse model is unchanged; D44 only feeds a **fixed** collapsed left width into the existing cross-clamp. |

---

## Codebase Summary (existing repository — the D44 surface, source-validated 2026-10-16 @ `0c4d478`)

The repo is **not** greenfield: a PyQt6 + pyqtgraph + official `ibapi` desktop trading terminal (live TWS
7496, SQLite persistence, PyInstaller `.app`; ~4,859 graphify nodes). This section is a factual inventory of
the surface D44 touches — every line below was read in the tree during planning (`graphify-out/graph.json`
was used for the initial map; **the source is authoritative**).

### Data models / persisted state `[existing]`

- **No SQLite change.** D44 touches **no table, no column, no migration**. The persisted surface it reads is
  `QSettings("NDThinkChart", "NDThinkChart")` only:
  - `ui/watchlist_panel.py::WATCHLIST_WIDTH_KEY = "watchlist/width"` (`:96`) — the **expanded** dock width,
    written by `save_watchlist_width` (`:126`) from `MainWindow.closeEvent` (`ui/main_window.py:3363`) and read
    by `load_watchlist_width` (`:116`) / `MainWindow._read_persisted_width` (`:2300`).
  - `ui/watchlist_panel.py::WATCHLIST_COLUMNS_KEY = "watchlist/columns"` (`:77`) — the D21.5 column layout
    (`load_watchlist_columns` `:179` / `save_watchlist_columns` `:188`, sanitised by
    `sanitise_watchlist_columns` `:150`).
  - **There is no collapse key** — D21.11's collapse is in-memory only (`WatchlistPanel._collapsed`, `:280`),
    and A76 keeps it that way.
- **In-memory state D44 touches:** `WatchlistPanel._collapsed` (`:280`), `MainWindow._watchlist_width`
  (`:421`, the "current/requested" dock width), `MainWindow._persisted_watchlist_width` (`:420`),
  `MainWindow._applying_dock_widths` (`:412`, the re-entrancy guard), `MainWindow._dock_clamp_scheduled`
  (`:413`), `MainWindow._dock_splitter` (`:414`, the defensively acquired dock-area splitter).

### Major components and responsibilities (as-built)

| Component | Responsibility (D44-relevant) |
|---|---|
| `ui/watchlist_panel.py::WatchlistPanel` (`:239`) | `header_bar` — a 28px `QWidget`, `objectName "WatchlistHeader"`, `background: #141822; border-bottom: 1px solid #232938` (`:294`–`:297`), holding `header_button = DiagonalStrikeButton("Watchlist")` (checkable, checked by default, `:301`–`:318`), `add_button` = the D22.1 `+` (`:323`–`:336`) and `search_box` = the D39.1 search field (`:340`–`:361`); `table` (7 configurable columns, `:402`–`:414`) with `body = self.table` (`:417`) and its `horizontalHeader()` = the column-header row; `_on_header_toggled` (`:435`–`:445`) sets `self._collapsed = not visible` and `self.body.setVisible(visible)`; `is_collapsed` / `set_collapsed` / `toggle_collapsed` (`:447`–`:461`). **Today: collapsed = the horizontal header strip stays (struck), the table hides, the dock keeps its ~220px width.** |
| `ui/main_window.py` dock wiring (`:369`–`:431`) | `self.watchlist_panel = WatchlistPanel()`; `self.watchlist_dock.setObjectName("Watchlist")`, `setWindowTitle("")` (the duplicate title is deleted, AC-D21.11.1), `setWidget(self.watchlist_panel)`, **`setTitleBarWidget(self.watchlist_panel.header_bar)`**, `setFeatures(DockWidgetMovable \| DockWidgetFloatable)`, **`self.watchlist_panel.setMinimumWidth(WATCHLIST_MIN_WIDTH)`**, `addDockWidget(LeftDockWidgetArea, …)`, `installEventFilter(self)`, the persisted-width restore (`:420`–`:424`), `QTimer.singleShot(0, self._deferred_dock_setup)` (`:431`). |
| `ui/main_window.py::MainWindow._apply_dock_widths` (`:2459`) | **The single apply entry point** (`D17/D18`), wired to `resizeEvent` (`:2787`–`:2796`), the acquired splitter's `splitterMoved` (`_on_dock_splitter_moved`, `:2725`), the event-filter fallback (`eventFilter` `:2756`–`:2769` → `_on_dock_drag_event` `:2729` → `_schedule_dock_clamp` `:2741`), `changeEvent(WindowStateChange)` (`:2771`), the deferred normalizes (`_deferred_dock_setup` `:2619`, `_deferred_dock_clamp` `:2677`), `_on_right_dock_visibility_changed` (`:2663`) and `closeEvent` (`:3349`). **Two clamp branches:** the right-dock-visible branch calls `_plan_dock_widths` (`:2413`) → the pure `plan_dock_widths`; the right-dock-hidden branch clamps directly — `desired = max(WATCHLIST_MIN_WIDTH, min(base_left, cap))` (`:2527`). **Both clamp to 150 unconditionally today** (DG74). |
| `ui/dock_layout.py` | The pure, Qt-free width model: `CHART_MIN_WIDTH = 400` (`:21`), `WATCHLIST_MIN_WIDTH = 150` (`:24`), `DEFAULT_WATCHLIST_WIDTH = 220` (`:27`), `RIGHT_DOCK_MIN_WIDTH = 200` (`:30`), the cap fractions (`:33`/`:36`), `watchlist_max_width` (`:41`), `right_dock_max_width` (`:52`), `plan_dock_widths` (`:64`, the B3 cross-clamp: `left = max(WATCHLIST_MIN_WIDTH, min(int(requested_left), left_max))` at `:89`, the combined-budget loop at `:100`–`:137`). |
| `ui/watchlist_panel.py` width helpers (`:93`–`:130`) | `WATCHLIST_MIN_WIDTH` / `CHART_MIN_WIDTH` / `DEFAULT_WATCHLIST_WIDTH` **aliased** from `dock_layout` (`:93`–`:95`); `watchlist_max_width` (`:99`, delegates), `clamp_watchlist_width` (`:110`, `max(WATCHLIST_MIN_WIDTH, min(width, cap))`), `load_watchlist_width` (`:116`), `save_watchlist_width` (`:126`). The `CHART_MIN_WIDTH` duplication is documented as an invariant (`ui/dock_layout.py:12`–`:14`). |
| `ui/visual_conventions.py` | `set_button_active(button, active)` (`:80`) — sets the `active` dynamic property and repolishes; `ACTIVE_PROPERTY = "active"` (`:39`); `DiagonalStrikeButton` (`:109`) with `struck` / `set_struck` / `is_struck` / `strike_line` / `text_area_rect` / `strike_color` and the auto-strike for checkable buttons. |
| `tests/` | The suites that reach this surface are enumerated **by call site** in the plan proposal (`AP-D44-8`, the `ESC-050`/`ESC-055` rule): 7 suites drive `_apply_dock_widths`/`plan_dock_widths` (all **expanded**), 3 suites assert the collapsed appearance, 4 suites read `dock_layout` constants. |

### Key entry points / data flow (unchanged shape)

Collapse: `header_button.toggled` → `WatchlistPanel._on_header_toggled` → `body.setVisible(False)` (D21.11) —
**D44 adds**: the collapsed visual sync → `collapsed_changed` → `MainWindow` (title-bar swap + min-width pin) →
`_apply_dock_widths()` → `plan_dock_widths`/the direct clamp → `resizeDocks`. Resize/drag:
`resizeEvent` / the splitter hook / the event-filter fallback → `_apply_dock_widths` → the same clamp.

### External integrations already in use `[existing]`

IBKR TWS over `ibapi` (live port 7496 only), SQLite (`config/paths.get_db_path()`, `DB_PATH`-overridable),
`QSettings` (INI/registry), `yfinance` (D38). **D44 adds no integration and no dependency** — it is a
dock-layout + widget-paint change using Qt APIs the repo already uses (`QDockWidget.setTitleBarWidget`,
`resizeDocks`, the event filter, a `QWidget.paintEvent`).

### What D44 changes, in one line

The collapse mechanism already exists; **what is missing is (a) a collapsed *width* the layout model will
honour and (b) a collapsed *appearance***. Today the width is clamped unconditionally to 150px at **two**
sites inside the single apply entry point (`ui/dock_layout.py:89` via `plan_dock_widths`, and
`ui/main_window.py:2527` in the right-dock-hidden branch) and the panel's minimum width is pinned to 150
(`ui/main_window.py:386`), so a 30px bar is snapped back on the next `resizeEvent` or drag (R66/DG74); and the
collapsed state renders the struck horizontal header button instead of a thin bar (`AC-D21.11.2`/`.3`).

---

## Summary

D44 turns the **already-existing** watchlist collapse (D21.11) into a **thin vertical bar**: the dock is pinned
to `WATCHLIST_COLLAPSED_WIDTH = 30px`, renders a rotated `WATCHLIST` label in the app palette (`#141822` /
`#232938` / `#cbd5e1`), and expands back to the **previous** width when the bar is clicked. The core fix is a
**collapsed-aware width rule in the pure `ui/dock_layout.py` model** (the 150px minimum becomes
expanded-state only) consumed by **both** clamp branches of the single apply entry point
`MainWindow._apply_dock_widths`, plus the **D21.13-style minimum-width relaxation** so Qt's own layout minimum
cannot re-impose 150px on the next resize or drag. The visual is a small custom `QWidget` with a `paintEvent`
drawing the rotated label (Qt cannot rotate a `QPushButton`'s text), carried as the panel's full-height
collapsed body while the dock's **title-bar slot** keeps a 30px handle so the dock stays movable (DG37). The
collapse state is **not persisted** (A76), the header strip / `+` (D22.1) / column-header row are hidden while
collapsed (A77), and every supersession (`AC-D21.11.2`/`.3`, the 150px minimum's scope, the `## Non-Goals`
restyling bullet) is **recorded** — the affected suites are **corrected, never weakened** (R67).

---

## Tech Stack Decisions

Constrained (existing) choices first, then the D44 decisions. Every row carries a rationale and the
alternatives considered.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S22 | **Language / UI stack / broker / persistence / packaging / tests** `[existing]` | Unchanged: Python 3.11+ (`.venv`), **PyQt6** (`>=6.6`), **pyqtgraph** (`>=0.13`), numpy, official `ibapi` (live TWS 7496 only), SQLite via `config/paths.get_db_path()`, `QSettings`, PyInstaller `.app`, pytest + pytest-qt offscreen (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`). **No new dependency, no new Qt module, no stack change.** | Existing-repo hard constraint (`requirements.md`'s Current Tech Stack; changing it is a Non-Goal). The **pyqtgraph chart stack is a locked decision** — the Lightweight Charts migration was evaluated and declined (`docs/memory.md`, 2026-10-16). D44 is a dock-layout + `paintEvent` change and needs **no** renderer work. | Any new UI/charting/dependency (e.g. a CSS-animated vertical label, a new widget library, the web-chart migration) — rejected. |
| S23 | **The collapsed-width rule — one pure helper, `WATCHLIST_COLLAPSED_WIDTH = 30`** `[new in D44]` — **revises D13/D17's 150px minimum scope** | In **`ui/dock_layout.py`** (the pure, Qt-free model): add **`WATCHLIST_COLLAPSED_WIDTH = 30`**; add a pure **`plan_watchlist_width(chart_area_w: int, requested_left: int, collapsed: bool = False) -> int`** returning `WATCHLIST_COLLAPSED_WIDTH` when collapsed, else `max(WATCHLIST_MIN_WIDTH, min(int(requested_left), watchlist_max_width(chart_area_w)))`; extend **`plan_dock_widths(chart_area_w, requested_left, requested_right, left_collapsed: bool = False)`** so a collapsed left is **fixed at the collapsed width**: `left = plan_watchlist_width(..., collapsed=left_collapsed)`, the left's own floor becomes `WATCHLIST_COLLAPSED_WIDTH` (`left_min`), the cross-clamp loop may shrink **only** the right dock (`left_can_shrink = not left_collapsed and left > WATCHLIST_MIN_WIDTH`), the combined budget keeps `chart_area_w - left - right >= CHART_MIN_WIDTH`, and the infeasible branch returns `(left_min, RIGHT_DOCK_MIN_WIDTH)` — i.e. **today's `(150, 200)` is preserved exactly** for the expanded state. `clamp_watchlist_width(width, chart_area_w)` **delegates** to `plan_watchlist_width(..., collapsed=False)` (one formula, three consumers). | DG74 names this resolution; the repo's recorded lesson is that **the pure helper is the single source of truth and a consumer-side workaround masks helper defects** (`docs/memory.md` 2026-10-03; the ESC-026 round). The rule must serve **three** consumers — `plan_dock_widths`, `_apply_dock_widths`'s right-dock-hidden branch (which does **not** call `plan_dock_widths` at all), and the persistence clamp — so putting it in the model avoids a second divergent implementation. The default `False` keeps **every existing 3-argument call** and the whole D17/D18/T52 suite green, which is what makes the expanded-state criteria verifiably unaffected (`AC-D44.8`). | (i) Clamp only inside `_apply_dock_widths` — leaves `plan_dock_widths`'s own `max(WATCHLIST_MIN_WIDTH, …)` at `:89` to fight it and duplicates the rule in the two branches (ESC-026's failure mode) — rejected. (ii) Flip `WATCHLIST_MIN_WIDTH` to 30 while collapsed (a global constant mutation) — the cap arithmetic, `watchlist_max_width`, the persistence clamp and every imported alias would change meaning mid-flight; a state-dependent *constant* is a defect generator — rejected. (iii) `dock.setMaximumWidth(30)` while collapsed — Qt does not honour a maximum width for a dock-area splitter section consistently, and the max would have to be cleared exactly on expand or the dock could never grow again — rejected. (iv) A separate `ui/collapsed_layout.py` — a second model beside the one the whole dock system already imports — rejected. |
| S24 | **The collapsed-aware apply path + the minimum-width relaxation + the tracked previous width** `[new in D44]` — **extends D17/D18 (the single apply entry point) and D21.13 (the pin pattern)** | **`ui/main_window.py`:** `_apply_dock_widths` reads `collapsed = bool(self.watchlist_panel.is_collapsed())` and (a) in the **right-dock-visible** branch forwards it to `_plan_dock_widths(chart_area, base_left, base_right, left_collapsed=collapsed)` (which forwards it to the pure helper and keeps its fixed-point iteration), (b) in the **right-dock-hidden** branch computes `desired = plan_watchlist_width(chart_area, base_left, collapsed=collapsed)`. **`self._watchlist_width` is never assigned while collapsed** — it is the **tracked previous width** that `AC-D44.2` restores (`MainWindow._watchlist_width` already carries it, `:421`). On the collapse transition (`panel.collapsed_changed`) the window **relaxes the minimum width** — `panel.setMinimumWidth(WATCHLIST_COLLAPSED_WIDTH)` and `dock.setMinimumWidth(WATCHLIST_COLLAPSED_WIDTH)`, restored to `WATCHLIST_MIN_WIDTH` on expand — then `_resize_docks_guarded` + **`QTimer.singleShot(0, self._apply_dock_widths)`**, exactly the `_sync_right_dock_collapse` sequence (`:2392`–`:2411`) whose comment records why ("the dock's layout minimum is recomputed on the next layout pass, so the immediate resize above can be clamped back to the pre-collapse minimum"). `_dock_widths_consistent` (`:2698`) becomes collapsed-aware (a collapsed dock is settled when its width equals the collapsed width) so the deferred clamp does not spin. | `_apply_dock_widths` **is** the single apply entry point, wired to both `resizeEvent` and the drag hook — so `AC-D44.5` ("the collapsed width survives a resize or a drag") is exactly a requirement on this path (R66/DG74). The minimum-width relaxation is **not optional**: Plan verified by offscreen probe (2026-10-16) that a left dock's width is pinned by its **widget minimums**, not by `resizeDocks` — a title-bar widget of minimum width 40 plus a content label of minimum width 78 held the dock at 78px when asked for 30; with every visible widget at 30 the same call yields exactly 30. `_watchlist_width`'s meaning is therefore *tightened, not changed*: it is the **expanded/requested** width, and keeping it is what makes the previous-width restore a one-liner instead of new state. | (i) A second "collapsed clamp" entry point beside `_apply_dock_widths` — two paths fighting on every resize/drag is the D17 defect class — rejected. (ii) A new `MainWindow._watchlist_expanded_width` and letting `_watchlist_width` mean "applied" — inverts a field the close-time persistence, the deferred-consistency check and existing tests already read, for no gain — rejected. (iii) `setMaximumWidth`/`setFixedWidth` on the panel while collapsed — a fixed width blocks the splitter entirely and must be undone exactly; the D21.13 minimum relaxation is the repo's proven equivalent — rejected. (iv) Skip the deferred re-apply — the probe/D21.13 evidence says the immediate resize can be clamped back by the next layout pass — rejected. |
| S25 | **The collapsed bar widget + the collapsed title-bar handle** `[new in D44]` — **extends D21.11 (the collapse mechanism/API) and DG37 (dock movability)** | **`ui/watchlist_panel.py`** gains **`class CollapsedWatchlistBar(QWidget)`**: fixed width `WATCHLIST_COLLAPSED_WIDTH`, `Qt.WidgetAttribute.WA_StyledBackground` set, an object-name-keyed stylesheet (`#WatchlistCollapsedBar { background: #141822; border-right: 1px solid #232938; color: #cbd5e1; }` plus a `[active="true"]` variant), and a **`paintEvent`** that fills the styled background (via `super().paintEvent`) and then draws the text **`WATCHLIST` rotated 90° counter-clockwise** (bottom-to-top) centred, in the palette colour; `mousePressEvent`/`mouseReleaseEvent` drive `set_button_active(self, True/False)` and emit **`expand_requested`**; `enterEvent`/`leaveEvent` drive `set_button_active`. **Two instances of the family, two roles:** `panel.collapsed_bar` — the panel's **full-height** collapsed body (a layout child of the panel, shown only while collapsed); `panel.collapsed_handle` — a 30px-wide, 28px-tall styled `QWidget` that is the **dock's title-bar widget while collapsed** (`dock.setTitleBarWidget(panel.collapsed_handle)` on collapse, `dock.setTitleBarWidget(panel.header_bar)` on expand — the current, D21.11 wiring), so the dock stays movable/floatable (DG37). Clicking **either** expands (`AC-D44.2`). The collapse API (`set_collapsed`/`toggle_collapsed`/`is_collapsed`) keeps its signatures and semantics. | Qt cannot rotate a `QPushButton`'s text, so the label needs a custom `paintEvent` (the requirement records this). **Plan-verified offscreen probe (2026-10-16):** for a dock in `LeftDockWidgetArea`, `setTitleBarWidget(w)` lays `w` out at the **top of the dock, at the dock's full width and `w`'s own `sizeHint` height** — with `w.sizeHint() == QSize(30, 120)` the bar occupied `QRect(0, 0, 30, 120)` and the content widget sat at `QRect(0, 120, 30, 780)`, **even with `setWidget(None)`** (i.e. the title bar never fills the dock). A *full-height* vertical bar is therefore impossible in the title-bar slot, so the full-height bar is the dock's **content** and the title-bar slot keeps a small handle for the drag affordance — which is what `A78` means by "the dock's title-bar widget presents the bar **while keeping the dock movable (DG37)**". `WA_StyledBackground` is required for a custom `QWidget` subclass to honour a stylesheet background (the classic Qt gotcha) and keeps the palette in one declared place. | (i) **The bar as the title-bar widget only** (A78's option (i) read literally) — the rotated label would be confined to a ~90px box at the top of the column with bare panel below; recorded as the **fallback** if the handle proves problematic, but it makes the label's position depend on title-bar geometry — rejected as the primary. (ii) **Reorient the existing `header_bar` in place** (A78's option (ii)) — the same title-bar geometry limit applies, and `header_bar` is the widget whose `+`/search contents must hide (A77) — rejected. (iii) **`dock.setWidget(bar)` while collapsed, `setWidget(panel)` on expand** — reparents the live table (subscriptions, flash timers, persisted columns) on every toggle and risks a stray top-level window — rejected. (iv) Painting the label in the **panel's** own `paintEvent` instead of a child widget — spreads the visual across two widgets and makes the "rotated-label widget exists" measurable (`AC-D44.1`) vague — rejected. (v) `set_button_active` on hover/pressed — **chosen** (not an alternative): it is the repo's established convention (`AC-D44.6`). |
| S26 | **The collapsed visual state (A77) + the transition signal + the palette** `[new in D44]` — **extends D21.11** | `WatchlistPanel._apply_collapsed_visual()` runs inside `_on_header_toggled` and **explicitly** `hide()`/`show()`s the strip and the body: while collapsed `header_bar.hide()` (which also hides the D22.1 `+` and the D39.1 search box, its children) and `table.hide()` (whose `horizontalHeader()` is the column-header row), and `collapsed_bar.show()` with the collapsed panel styling (`#141822` + a 1px `#232938` right border so the 30px column reads as one panel, not a bare widget); on expand the reverse. A new **`collapsed_changed = pyqtSignal(bool)`** is emitted from `_on_header_toggled` so `MainWindow` does the **dock-level** work (title-bar swap, minimum-width pin, width apply) — `S24`. Palette: background `#141822`, border `#232938`, text `#cbd5e1` (A75/D44's own palette list — **not** the mockup's white pill, which the owner explicitly clarified as mockup-tool styling). Hover/pressed via `set_button_active`. | `AC-D44.4`'s measurable is `isVisible()` on the strip, the `+` and the column-header row — which requires **explicit** hide/show (a title-bar swap alone does not hide `header_bar` deterministically, and a hidden widget is skipped by the layout so it cannot pin the minimum either — the probe's second half). The signal keeps the layering honest: the panel owns widget state, the window owns the dock. | (i) The panel reaching into its parent dock for `setTitleBarWidget` — a widget doing its owner's job, and it breaks the bare-panel harness (`tests/test_watchlist_add_remove_d22.py`) — rejected. (ii) `MainWindow` polling `is_collapsed()` in `resizeEvent` only — no transition hook, so the minimum pin and the title-bar swap would never happen — rejected. (iii) `QStackedLayout` swapping the strip for the bar — the strip is the *title bar*, not a stack page; the swap is still needed — rejected. (iv) Leaving the strip visible but empty while collapsed — contradicts A77/`AC-D44.4` — rejected. |
| S27 | **No persistence of the collapse state (A76)** `[new in D44]` | **No new `QSettings` key.** `WatchlistPanel._collapsed` starts `False` (the app starts **expanded**). The D13/D17 key `watchlist/width` keeps holding the **expanded** width: `closeEvent`'s `save_watchlist_width(self._settings, self._watchlist_width, self._chart_area_width())` (`ui/main_window.py:3363`) is **unchanged**, and because `_watchlist_width` is never overwritten while collapsed (`S24`), a session that ends **collapsed** still persists the user's expanded width. | A76 (owner-flagged #2, decided) + the D10/A36 precedent that UI show/hide toggles are not persisted. Recording the **expanded** width is the only choice that keeps "the app starts expanded" meaningful: persisting 30 would make the next launch's expanded dock clamp to the 150px minimum, silently losing the user's width. A76 is silent on the close-while-collapsed case, so the decision is recorded as `AP-D44-2`/`FI-D44-3` rather than assumed silently. | (i) Persist a `watchlist/collapsed` key — contradicts A76 and needs a restore-time visual sync before the first layout pass — rejected. (ii) Persist the applied (30px) width while collapsed — the silent-width-loss failure above — rejected. (iii) Persist the collapse state in the existing width key as a sentinel (e.g. `0`) — overloads a documented numeric key and breaks `_read_persisted_width`'s `max(WATCHLIST_MIN_WIDTH, width)` — rejected. |
| S28 | **Test surface** `[new in D44]` — **corrects 3 suites (4 sites + 1 docstring), extends 2, adds 2, verifies the rest unchanged by call site** | **Corrected (never weakened, never deleted — R67):** `tests/test_watchlist_columns_d21.py::test_D21_10_T02` (the collapsed appearance), `::test_D21_10_T03` (the collapsed appearance **and** the collapsed-width leg **and** the title-bar/drag leg), `tests/test_watchlist_nonregression_d22.py`'s D21.11 block **plus its module docstring** (`:10`), `tests/test_watchlist_add_remove_d22.py::test_D22_04_T01` (`hb.isVisible()` while collapsed). **Extended:** `tests/test_dock_layout.py` (the collapsed pure cases + the constants/agreement test) and `tests/test_watchlist.py` (the collapsed delegate case). **Added:** `tests/test_dock_widths_collapsed_d44.py` (`AC-D44.5`'s pinning guard, `AC-D44.2`'s previous-width restore, `AC-D44.7`'s no-key assertion, `AC-D44.1`'s width measurable) and `tests/test_watchlist_collapsed_bar_d44.py` (`AC-D44.1`/`.3`/`.4`/`.6` — the bar, the rotated label, the palette, the hidden strip/`+`/header row, `set_button_active`). **Verified unchanged (enumerated by call site):** `test_dock_widths_d17.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`, `test_right_dock_d21.py`, `test_dock_d18_region.py`, `test_d10_d13_integration.py`, `test_dock_layout.py::test_T52_T04`, `test_toolbar_scroll_d19.py` — all drive the changed entry points with the watchlist **expanded**, and the new parameters default to the expanded rule. **The new guard must be RED at `0c4d478` for the right reason** — the collapsed dock staying at ~220px / the 150px minimum, **not** an `ImportError` on the new constant (so the guard asserts the observable outcome through the existing `set_collapsed` API, with the constant referenced defensively). | R67 names exactly this regression surface; `AC-D44.8` requires the guard to fail pre-fix and the expanded suites to stay green (or be updated in lockstep). The enumeration is by **call site of the changed entry point, not by the suites the design names** — the recorded `ESC-050` rule and `ESC-055`'s ownership remedy (`AP-D44-8`) — because this repo has twice been burned by an under-enumerated impact analysis (`FI-D42-2`, `ESC-050`) and once by an invalidated assertion outside the changing task's file (`ESC-055`). | (i) Delete the collapse-appearance assertions — forbidden (correct, do not weaken) — rejected. (ii) Relax them to "no exception raised" — the exact "weakened" failure mode — rejected. (iii) Leave `test_dock_widths_d17.py`/`d18*` alone *and unverified* — the plan enumerates them explicitly instead, so a green suite is evidence rather than luck — rejected. (iv) Put the new guard in an existing suite — a new file makes the RED-at-`0c4d478` demonstration clean and keeps the D44 evidence in one place — rejected. |

---

## System Components

**Existing, unchanged** `[existing]`

`ui/chart_panel.py` and the whole pyqtgraph render stack (locked), `ui/candlestick_item.py`,
`ui/ticker_session.py`, `services/*` (the planner, the calendar, the collapse map, the alarms, the search),
`data/*` (no schema change), `ibkr/*`, `ui/active_portfolio_panel.py` and the D18/D21.13/D41 right-dock model,
`ui/popout_window.py`, the D14/D21.5/D22/D39 watchlist behaviour, `ui/visual_conventions.py`'s conventions
(consumed, not modified), `ui/dock_layout.py`'s existing constants and cap arithmetic — i.e. **nothing
D1–D43 depends on is redesigned**.

**New / changed** `[new/changed]`

| Component | Change |
|---|---|
| `ui/dock_layout.py::WATCHLIST_COLLAPSED_WIDTH` | **New constant** `= 30` (the collapsed bar width, A75) (`S23`) |
| `ui/dock_layout.py::plan_watchlist_width` | **New pure helper** — the single collapsed/expanded width rule; three consumers (`S23`) |
| `ui/dock_layout.py::plan_dock_widths` | Gains `left_collapsed: bool = False`; a collapsed left is fixed at the collapsed width, its floor becomes 30, the cross-clamp shrinks only the right; the expanded behaviour (including the infeasible `(150, 200)` branch) is **bit-for-bit preserved** (`S23`) |
| `ui/dock_layout.py::clamp_watchlist_width` | Now **delegates** to `plan_watchlist_width(..., collapsed=False)` — the same formula in one place (`S23`) |
| `ui/watchlist_panel.py::CollapsedWatchlistBar` | **New widget** — rotated `WATCHLIST` label, app palette, `WA_StyledBackground`, `expand_requested`, `set_button_active` hover/pressed (`S25`) |
| `ui/watchlist_panel.py::WatchlistPanel.collapsed_bar` / `::collapsed_handle` | **New widgets** — the full-height collapsed body and the 30×28 collapsed title-bar handle (`S25`) |
| `ui/watchlist_panel.py::WatchlistPanel.collapsed_changed` | **New signal** `pyqtSignal(bool)` emitted from `_on_header_toggled` (`S26`) |
| `ui/watchlist_panel.py::WatchlistPanel._apply_collapsed_visual` | **New** — explicit hide/show of `header_bar` + `table`, show/hide of the bar, the collapsed panel styling (`S26`) |
| `ui/watchlist_panel.py::WATCHLIST_COLLAPSED_WIDTH` | **New alias** of `dock_layout.WATCHLIST_COLLAPSED_WIDTH` (the same pattern as the other width constants, `:93`–`:95`) (`S23`) |
| `ui/main_window.py::MainWindow._apply_dock_widths` | Collapsed-aware in **both** branches; `_watchlist_width` never overwritten while collapsed (`S24`) |
| `ui/main_window.py::MainWindow._plan_dock_widths` | Forwards `left_collapsed` to the pure helper (`S24`) |
| `ui/main_window.py::MainWindow._dock_widths_consistent` | Collapsed-aware (settles in one pass) (`S24`) |
| `ui/main_window.py::MainWindow._on_watchlist_collapsed_changed` | **New** — the title-bar swap + the minimum-width pin + the deferred re-apply; wired to `panel.collapsed_changed` (`S24`, `S25`) |
| `tests/test_dock_widths_collapsed_d44.py`, `tests/test_watchlist_collapsed_bar_d44.py` | **New suites** (`S28`) |

---

## Data Model

| Entity | Status | Key fields / change |
|---|---|---|
| `watchlist/width` (`QSettings`, `ui/watchlist_panel.py:96`) | `[existing]` | **Unchanged** — still the **expanded** width; written by `save_watchlist_width` from `closeEvent`; **never written while collapsed** (`S27`) |
| Collapse state | `[existing]` | In-memory only — `WatchlistPanel._collapsed` (`:280`), starts `False` (the app starts expanded); **no new key** (A76/`S27`) |
| `MainWindow._watchlist_width` | **`[new/changed]`** | **Semantics tightened, not changed:** it is the **expanded/requested** dock width and is **never assigned while collapsed** — it *is* the "width held immediately before collapsing" that `AC-D44.2` restores (`S24`) |
| `MainWindow._persisted_watchlist_width` | `[existing]` | Unchanged — the raw persisted request re-applied post-`show()` (`:420`, `_deferred_dock_setup` `:2632`) |
| `ui/dock_layout` constants | **`[new/changed]`** | `+ WATCHLIST_COLLAPSED_WIDTH = 30`; `WATCHLIST_MIN_WIDTH = 150` keeps its value but is now **expanded-state only**; `CHART_MIN_WIDTH` and its cross-module invariant are unchanged (`S23`) |
| `WatchlistPanel.collapsed_bar` / `::collapsed_handle` | **`[new/changed]`** | Two new widgets with no persisted state (`S25`) |
| `bars`, `watchlist`, `alarms`, `zones`, `drawings*`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`, `yfinance_events_cache`, `volume_baseline` (SQLite) | `[existing]` | **Untouched** — no DDL, no migration, no row change |
| `Bar` / `MissingSpan` / `RequestPlan` (`data/models.py`, `services/backfill_service.py`) | `[existing]` | Untouched |

---

## Integration Points

| Integration | Status | Why needed / what changes |
|---|---|---|
| IBKR TWS over `ibapi` (`ibkr/client.py`, `ibkr/market_data.py`) | `[existing]` | **Untouched.** Collapse/expand is **pure UI state** and works disconnected (Journey 37's precondition); no request, no subscription, no order is affected |
| SQLite (`config/paths.get_db_path()`, `data/db.py`) | `[existing]` | **Untouched** — no schema, no migration, no write |
| `QSettings("NDThinkChart", "NDThinkChart")` | `[existing]` | **Unchanged surface:** `watchlist/width` + `watchlist/columns` only. **No collapse key is added or written** (`AC-D44.7`/A76) |
| Qt dock layout (`QDockWidget.setTitleBarWidget`, `resizeDocks`, `setMinimumWidth`, the dock-area splitter + event filter) | `[existing]` | The same APIs D17/D21.11/D21.13 already use; D44 introduces **no new dependency and no new module import**. `QWidget.paintEvent` + `QPainter` are already in the repo (`ui/visual_conventions.py::DiagonalStrikeButton.paintEvent` `:190`; `ui/candlestick_item.py::CandlestickItem._draw_candles` paints into a `QPicture`, `:121`); `QPainter.rotate` is **new to this codebase** but is a standard Qt painter transform (no import beyond `QtGui`, already imported) |
| `yfinance` (D38), the D39 burst baseline, the D25 alarm monitor, the order machinery | `[existing]` | **Untouched** — no D44 path reaches them |

---

## Frozen Interfaces

Interfaces this increment treats as **read-only**: already settled and modified by **no** D44 task. Contracts
are **verbatim** from the tree at `0c4d478` (never paraphrased), with the owning module, so Task Manager can
hand a worker the contract instead of the implementation. (D44's revised/new surfaces — `plan_dock_widths`,
`plan_watchlist_width`, `clamp_watchlist_width`, `MainWindow._apply_dock_widths`/`::_plan_dock_widths`/
`::_dock_widths_consistent`, `WatchlistPanel._on_header_toggled`/`::_apply_collapsed_visual` and the two new
widgets — are deliberately **not** listed: they are under construction this increment, and freezing them would
freeze a contract `S23`–`S26` change.)

| Interface | Verbatim contract | Owning module |
|---|---|---|
| `set_button_active` `[existing]` | `def set_button_active(button: QWidget, active: bool) -> None` | `ui/visual_conventions.py` |
| `ACTIVE_PROPERTY` `[existing]` | `ACTIVE_PROPERTY = "active"` | `ui/visual_conventions.py` |
| `DiagonalStrikeButton` (VIS-D21.1) `[existing]` | `class DiagonalStrikeButton(QPushButton)` with `struck` (property), `def set_struck(self, value: bool) -> None`, `def is_struck(self) -> bool`, `def strike_line(self) -> QLineF`, `def text_area_rect(self) -> QRectF`, `def strike_color(self) -> QColor` | `ui/visual_conventions.py` |
| `WatchlistPanel` signals `[existing]` | `row_double_clicked = pyqtSignal(str)` · `symbol_add_requested = pyqtSignal(str)` · `symbol_remove_requested = pyqtSignal(str)` · `search_text_changed = pyqtSignal(str)` · `search_sample_selected = pyqtSignal(object)` | `ui/watchlist_panel.py` |
| `WatchlistPanel` collapse API `[existing]` | `def is_collapsed(self) -> bool` · `def set_collapsed(self, collapsed: bool) -> None` · `def toggle_collapsed(self) -> None` — **signatures and semantics preserved**; the *collapsed appearance* they gate is revised by D44 (`AC-D21.11.2`/`.3`) | `ui/watchlist_panel.py` |
| `WatchlistPanel` data API `[existing]` | `def active_row_count(self) -> int` · `def add_symbol(self, symbol: str, contract)` · `def remove_symbol(self, symbol: str) -> bool` · `def clear(self)` · `def set_market_data_manager(self, md_manager)` · `def set_subscription_manager(self, sub_manager)` · `def set_price_sink(self, sink)` · `def set_add_enabled(self, enabled: bool) -> None` · `def set_search_enabled(self, enabled: bool) -> None` | `ui/watchlist_panel.py` |
| Panel width/persistence helpers `[existing]` | `def watchlist_max_width(chart_area_w: int) -> int` · `def load_watchlist_width(settings: QSettings, chart_area_w: int) -> int` · `def save_watchlist_width(settings: QSettings, width: int, chart_area_w: int) -> int` · `WATCHLIST_WIDTH_KEY = "watchlist/width"` | `ui/watchlist_panel.py` |
| Panel pure helpers (D14/D21.5/D22) `[existing]` | `def should_load_on_double_click(current_symbol: str, requested_symbol: str, connected: bool) -> str` · `def normalise_symbol(text) -> str` · `def symbol_in_list(symbol, symbols) -> bool` · `def ensure_symbol_present(fields) -> list[str]` · `def sanitise_watchlist_columns(raw) -> list[str]` · `def load_watchlist_columns(settings: QSettings) -> list[str]` · `def save_watchlist_columns(settings: QSettings, fields) -> list[str]` · `WATCHLIST_COLUMNS_KEY = "watchlist/columns"` | `ui/watchlist_panel.py` |
| Dock-width model constants `[existing]` | `CHART_MIN_WIDTH = 400` · `WATCHLIST_MIN_WIDTH = 150` · `DEFAULT_WATCHLIST_WIDTH = 220` · `RIGHT_DOCK_MIN_WIDTH = 200` · `WATCHLIST_CAP_FRACTION = 0.50` · `RIGHT_DOCK_CAP_FRACTION = 0.40` | `ui/dock_layout.py` |
| Dock-width model helpers `[existing]` | `def watchlist_max_width(chart_area_w: int) -> int` · `def right_dock_max_width(chart_area_w: int) -> int` | `ui/dock_layout.py` |
| `plan_dock_widths`'s **expanded contract** `[existing]` | `def plan_dock_widths(chart_area_w: int, requested_left: int, requested_right: int) -> tuple` — **the 3-argument positional call keeps today's behaviour exactly** (the new `left_collapsed` defaults to `False`); the guarantees it documents (`each returned width within its own [min, max] cap`, the chart minimum preserved where feasible, neither width below its dock minimum, stable ints, never raises) are unchanged | `ui/dock_layout.py` |
| `CHART_MIN_WIDTH` invariant `[existing]` | `ui/dock_layout.py:12`–`:14`: "Constants here are kept in agreement with the pre-existing D13 constants in `ui/watchlist_panel` — in particular `CHART_MIN_WIDTH` must equal `ui/watchlist_panel.CHART_MIN_WIDTH`." | `ui/dock_layout.py` ↔ `ui/watchlist_panel.py` |
| `MainWindow` dock helpers `[existing]` | `def _chart_area_width(self) -> int` · `def _read_persisted_width(self) -> int` · `def _resize_docks_guarded(self, docks, sizes) -> None` | `ui/main_window.py` |
| Watchlist dock identity `[existing]` | `self.watchlist_dock.setObjectName("Watchlist")` · `self.watchlist_dock.setWindowTitle("")` · `setFeatures(DockWidgetMovable \| DockWidgetFloatable)` — title/objectName-keyed lookups and the dock's movability depend on these (`docs/memory.md` 2026-10-03; DG37) | `ui/main_window.py` |

---

## Non-Functional Approach

- **Correctness of the width invariant (from `AC-D44.5`, R66).** The hard requirement is that the collapsed
  width **survives both drivers** — a window `resizeEvent` **and** a dock drag — because `_apply_dock_widths`
  is the single apply point for both. The rule is pure and unit-testable (`S23`), and the minimum-width
  relaxation + deferred re-apply (`S24`) is what stops Qt's own layout minimum from re-imposing 150px. The
  `CHART_MIN_WIDTH` invariant holds in **both** states (the cross-clamp still guarantees
  `chart_area_w - left - right >= CHART_MIN_WIDTH` where feasible, and on an infeasible window the dock
  minimums still win — with the collapsed left's floor at 30, the window's own minimum drops by 120px, which
  is a *gain*, not a regression).
- **Measurement and tolerance (from the repo's own convention).** `_apply_dock_widths` re-issues `resizeDocks`
  only when the delta exceeds 1px, and the D17 suite records that "a residual of at most 1px is expected and
  asserted with `+1`" (`tests/test_dock_widths_d17.py:17`–`:21`). The new guard asserts the **dock** equality
  directly (probe-verified exact: `resizeDocks([dock], [30])` yields 30 once the widget minimums allow it) and
  keeps the `+1` convention for inner/derived measurements — recorded as `AP-D44-4`/`FI-D44-1`.
- **Performance (no regression).** Collapse/expand is **O(1)**: no fetch, no re-render, no table rebuild, no
  sort, no new timer beyond the existing single-shot coalescer; the bar's paint is one rotated `drawText` per
  expose. The dock-width change triggers a Qt layout pass only — the D28.4 render discipline (one `QPicture`
  per full rebuild; live ticks in the live layer) is untouched, and no chart data path is entered.
- **Visual and accessibility (from `AC-D44.1`/`AC-D44.6`, A75).** 30px is ≥ the 28px header height, so the bar
  is a comfortable click target; the label is rotated 90° **counter-clockwise** (bottom-to-top) and centred in
  the column; the palette is the app's (`#141822` background, `#232938` border, `#cbd5e1` text) so the bar
  reads as **a panel, not the mockup's white pill** (the owner's explicit clarification); hover/pressed
  feedback goes through `set_button_active` so the affordance is discoverable and consistent with the D21
  conventions; the whole column — not just the label — is the click target (`AC-D44.2`).
- **No persistence, no state leakage (A76).** No new settings key; the collapse state is in-memory and starts
  `False`; the persisted width stays the expanded one (`S27`).
- **Test-suite fidelity (R67; the `ESC-050`/`ESC-055` enumeration rule).** **Green** is required; the
  *collapsed-appearance* and collapsed-width assertions change **by design** and are **corrected with their
  cause**, never weakened or deleted; every suite that merely *drives* a changed entry point is enumerated **by
  call site** and verified unchanged (`S28`, `AP-D44-8`); and the new guard is **RED at `0c4d478` for the right
  reason** (the collapsed dock at ~220px/150px, not an `ImportError`) — the repo's own credibility rule
  (`docs/memory.md` 2026-10-05: "a regression guard is only credible if it fails on the pre-fix tree and
  passes post-fix").
- **Live-order safety / security.** No D44 path transmits an order, connects to TWS in a test, touches the DB,
  or reaches the retained order machinery; `check_live_port` and the confirm dialogs are untouched; **no new
  credential, endpoint, dependency or module import**.
- **Scalability.** None to speak of: a single widget, two integers, one 30px-wide column. The dock model stays
  O(1) per apply, and the fixed-point iteration in `_plan_dock_widths` converges exactly as before (the cap
  contraction is unchanged).

---

## Architecture Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D44-1 | **The collapsed width is snapped back to `WATCHLIST_MIN_WIDTH`** by the clamp on the next `resizeEvent`/drag, so the thin bar never sticks — the **R66** defect class (and the D17/D19 defect class: a clamp that is not wired to every driver) | H | The collapsed rule lives in the pure model and is consumed by **both** clamp branches of the single apply entry point (`S23`, `S24`); the minimum-width relaxation + deferred re-apply mirrors the proven D21.13 sequence; and `AC-D44.5`/`AC-D44.8` demand a **RED-at-`0c4d478`** guard that drives **both** a `resizeEvent` and the drag-event path |
| AR-D44-2 | **A stale Qt layout minimum re-imposes 150px** on the layout pass after the transition (the D21.13 comment's exact failure) | M | Relax the panel's **and** the dock's minimum in the transition, then `QTimer.singleShot(0, self._apply_dock_widths)` (`S24`); the guard processes the event loop and re-asserts the collapsed width; the probe establishes that widget minimums (not `resizeDocks`) decide whether 30 is reachable |
| AR-D44-3 | **The title-bar swap breaks the dock's drag/float affordance (DG37)** or the title/objectName-keyed dock lookups | M | The collapsed title-bar slot holds a real widget (`panel.collapsed_handle`), the same mechanism D21.11 proved works; `DockWidgetMovable \| DockWidgetFloatable`, the `objectName` and the empty window title are **unchanged** (frozen list); the corrected `test_D21_10_T03` re-points the double-click-to-float assertion at the handle instead of deleting it |
| AR-D44-4 | **The enshrining suites are weakened instead of corrected**, so the suite stays green while the behaviour regresses (R67) | H | The correction record names **each** site with its **cause** and the intent it preserves; the collapsed-appearance assertions move to the collapsed state and the expanded-state width assertions move to the expanded state — none deleted; the VIS-D21.1 strike assertions are re-pointed to the buttons where the convention still applies (D21.12/D21.13) rather than dropped |
| AR-D44-5 | **A real splitter drag on a 30px dock does not deliver the events the fallback watches** (the event filter is installed on the dock; the handle sits at the chart's left edge), so the drag-time clamp misses | M | The acquired splitter's `splitterMoved` hook (when reachable) + `MouseButtonRelease` + the `resizeEvent` path + the coalescing deferred clamp all route to the same collapsed-aware apply; the guard drives `resizeEvent` **and** `_on_dock_drag_event` explicitly (the `AC-D44.8` measurable's own words: "a simulated resize/drag") |
| AR-D44-6 | **The expand path restores the wrong width** — `_watchlist_width` overwritten by the collapsed plan, so expanding lands on 30 (clamped to 150) instead of the previous width | M | `_watchlist_width` is never assigned while collapsed (`S24`, `S27`); the guard collapses from a known width `W` and asserts `dock.width() == clamp(W)` on expand, including the min-150 and at-cap edge cases (`AC-D44.2` + D44's edge cases) |
| AR-D44-7 | **Scope creep** into the D21.11 API, the D22.1 `+`, the D39.1 search box, the D14 double-click, the D21.5 column popup, or the D18/D21.13/D41 right dock | M | The frozen-interface list pins those contracts; the relationship table records the explicit non-changes; the corrected suites keep asserting them |
| AR-D44-8 | **Offscreen flakiness / `QSettings` leakage between tests** masks a regression (the recorded gotcha class) | L | Full offscreen suite run before declaring green; the D22 harness's per-test `QSettings` ini for the new suites; the palette/hover assertions read the widget's stylesheet and the `active` property rather than rendered pixels (DPI-independent) |
| AR-D44-9 | **The 30px bar is not legible/clickable on a HiDPI display** (the 1px borders and the rotated text at 30px) | L | The width is a named constant (tunable), the whole column is the click target, the label is centred with a 1px right border (29px of fill), and the palette is asserted from the stylesheet rather than from pixels; a strict visual check is left to the Code Reviewer's independent verification |
| AR-D44-10 | **D42's width/`_bars`-trim and D43's priming work are disturbed** by an edit above their cited lines in `ui/main_window.py` (the docs cite line numbers; the file is edited often — `docs/memory.md`) | L | D44 edits no data path; the plan cites **symbols** as the primary pointer (the repo's source-citation convention) and any doc line reference in this proposal is **indicative only** |

---

## Requirements → architecture traceability

| Requirement / journey | Architecture section | Phase (plan proposal) |
|---|---|---|
| **`AC-D44.1`** (collapsed form — a thin vertical bar of `WATCHLIST_COLLAPSED_WIDTH` in `LeftDockWidgetArea` with the rotated `WATCHLIST` label and the app palette, not white) | `S23` (the width), `S25` (the bar widget), `S26` (the palette/visual state); components `ui/dock_layout.py`, `ui/watchlist_panel.py`; AR-D44-1/2/9 | **Phase 1** (width) + **Phase 1** (widget) — one phase, ordered tasks |
| **`AC-D44.2`** (click the bar → expand to the **previous** width, re-clamped) | `S24` (`_watchlist_width` = the tracked previous width; the apply path), `S25` (`expand_requested`), `S26` (the transition); AR-D44-6 | **Phase 1** |
| **`AC-D44.3`** (collapse from the retained header button — the existing D21.11 path) | `S26` (the preserved API + `_apply_collapsed_visual`), frozen `set_collapsed`/`toggle_collapsed`/`is_collapsed` | **Phase 1** |
| **`AC-D44.4`** (header strip / `+` (D22.1) / column-header row hidden while collapsed, visible on expand) | `S26` (explicit `hide()`/`show()` of `header_bar` + `table`); AR-D44-7 | **Phase 1** |
| **`AC-D44.5`** (**the core fix** — the collapsed width survives a `resizeEvent` **or** a dock drag) | `S23` (the pure rule), `S24` (both clamp branches + the minimum relaxation + the deferred re-apply); AR-D44-1/2/5 | **Phase 1** |
| **`AC-D44.6`** (palette + hover/pressed via `ui/visual_conventions.py::set_button_active`) | `S25`, `S26`; frozen `set_button_active`/`ACTIVE_PROPERTY`; AR-D44-9 | **Phase 1** |
| **`AC-D44.7`** (collapse state **not** persisted; no `QSettings` key) | `S27`; Data Model; `AC-D44.7`'s measurable in the new width guard | **Phase 1** |
| **`AC-D44.8`** (regression guard **RED pre-fix**; the expanded-state width suites green or corrected in lockstep) | `S28`; AR-D44-4; the plan's *Corrected* / *Verified unchanged* / *RED→GREEN* sections | **Phase 1** (the guard + the corrections) + **Phase 2** (the reconciliation + the RED-at-`0c4d478` evidence) |
| **Journey 37** (steps 1–5; postconditions; the edge cases: collapse from the min → restore 150; from the cap → restore the cap; resize/drag while collapsed does not expand; floating dock still clickable; disconnected/empty watchlist; first launch expanded; the `CHART_MIN_WIDTH` invariant in both states) | `S23`–`S28`; Non-Functional (the invariant, the tolerance, the visual); the plan's *Assumptions* `AP-D44-3`/`AP-D44-4` | **Phase 1** + **Phase 2** (the edge cases re-checked) |
| **`AC-D21.11.2` / `AC-D21.11.3`** (REVISED — the collapsed appearance) | `S25`, `S26`; the *Supersessions* section; AR-D44-4 | **Phase 1** |
| **`AC-D21.11.1`** (unchanged — one "Watchlist" label; the duplicate dock title deleted; the header strip is the title bar **while expanded**) | Frozen *Watchlist dock identity* + `S25` (the single label stays; the bar's painted text is not a label widget); `test_D21_10_T01` verified unchanged | **Phase 1** (non-regression) |
| **`AC-D13.1` / `AC-D17.2`** (REVISED — the 150px minimum is **expanded-state only**) | `S23`; the *Supersessions* section | **Phase 1** |
| **`AC-D13.2` / `AC-D13.3` / `AC-D17.1` / `AC-D17.3`–`AC-D17.6`** (cap, persistence, drag enforcement, re-clamp — unchanged for the expanded state) | `S23` (the default `False` keeps the expanded rule), `S24`, `S27`; the *Verified unchanged* suite table | **Phase 1** (non-regression) + **Phase 2** |
| **`AC-D18.*` / D21.13 (right dock)** (unchanged — the cross-clamp with a fixed collapsed left) | `S23` (the collapsed left in the B3 cross-clamp); `[no relationship]` for the right dock's own model | **Phase 1** + **Phase 2** (non-regression) |
| **`AC-D22.1`** (the `+` on the header strip — unchanged **expanded**) | `S26` (hidden while collapsed, restored on expand); AR-D44-7 | **Phase 1** |
| **`AC-D14.*` / `AC-D21.5.*` / `AC-D39.*`** (double-click, columns, search — unchanged) | Frozen *WatchlistPanel data API* / *pure helpers*; the *Verified unchanged* suites | **Phase 2** (non-regression) |
| **`A75`** (the 30px bar width) · **`A76`** (no persistence; starts expanded) · **`A77`** (strip/`+`/column-header hidden while collapsed) · **`A78`** (the mechanism is a Plan-level detail) | `S23` · `S27` · `S26` · `S25` (+ `FI-D44-2`) | **Phase 1** |
| **`R66`** (the collapsed width snapped back) · **`R67`** (the collapsed-appearance change regresses D21.11/D13/D17) | AR-D44-1/2/5 · AR-D44-4 + `S28` | **Phase 1** + **Phase 2** |
| **`DG74`** (the clamp fights the collapsed width) | `S23`, `S24` (the resolution DG74 suggests, with the pure model as the owner) | **Phase 1** |
| **`Q54`** (owner confirmation of A75–A77; non-blocking) | A75–A77 are the recorded defaults; no blocking item; an owner override would revise `AC-D44.1`/`.4`/`.7` + `S23`/`S26`/`S27` | — (recorded) |
| **The `## Non-Goals` revision (2026-10-16)** | The *Supersessions* section item 3 (permitted **only** for the D44 bar, in the app palette) | **Phase 1** |
| **D42 / D43 / D41 / D40** | `[no relationship]` — not reopened | — |

---

## Supersessions and non-changes (recorded, never silent)

1. **`AC-D21.11.2` / `AC-D21.11.3`'s collapsed-appearance clause** ("the collapsed state still shows the
   button", with the `VIS-D21.1` diagonal strike on the retained button) → **superseded for the collapsed
   watchlist state**: the collapsed form is the **thin bar with rotated text**, not a struck-through
   horizontal header button. `VIS-D21.1` **still applies** to any genuinely hidden/off **button** state
   elsewhere (D21.12 volume, D21.13 portfolio) and to the header button whenever it is *shown* — it is simply
   not the collapsed-watchlist indicator. **`AC-D21.11.1` is unchanged** (a single "Watchlist" label; the
   duplicate dock title deleted). One **clarification** (not a supersession): the *title-bar widget identity*
   is `panel.header_bar` in the **expanded** state (as today, and as `test_D21_10_T01` asserts) and
   `panel.collapsed_handle` in the **collapsed** state — the swap D44's own correction record explicitly
   authorises ("`setTitleBarWidget` swaps to the bar, or the header widget reorients", `A78`).
2. **The 150px minimum of `AC-D13.1` / `AC-D17.2`** → scoped to the **expanded** watchlist only; while
   collapsed the width is `WATCHLIST_COLLAPSED_WIDTH` (~30px). `AC-D13.2`/`AC-D13.3`/`AC-D17.1`/
   `AC-D17.3`–`AC-D17.6` (cap, persistence, drag enforcement, re-clamp) are **unchanged for the expanded
   state**; `AC-D21.11`'s "collapsed-width geometry" edge case is **now specified** by `AC-D44.1`/`AC-D44.5`.
3. **The `## Non-Goals` "no restyling" bullet** → **revised by the owner** (D44, dated 2026-10-16) to permit
   **only** the collapsed-bar styling, in the **app palette** (`#141822` / `#232938` / `#cbd5e1`) — the
   mockup's white rounded pill is explicitly **not** the target (the owner's clarification).
4. **Explicit non-changes (recorded so they are not read as omissions):** `WATCHLIST_MIN_WIDTH = 150` (value),
   `DEFAULT_WATCHLIST_WIDTH`, the cap fractions, `CHART_MIN_WIDTH` and its cross-module invariant, the D21.11
   collapse API, the D13/D17 persistence key and re-clamp rules, the D14/D21.5/D22/D39 watchlist behaviour,
   the D18/D21.13/D41 right-dock model, the pyqtgraph rendering stack (a **locked** decision), the D42/D43
   data paths, and `ui/visual_conventions.py` (consumed, never modified).

---

Handoff: this proposal is checked by Plan Artifact Editor & Validator against
`docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`). Companion: `docs/plan_proposal.md`
(`Status: READY_FOR_VALIDATION`). Module index: `docs/codebase-map.md`.
