# Architecture Proposal — NDThinkChart Batch 14 (D20: toolbar scrollbar lane)

> **Scope.** An *incremental* change on top of the **already-built, green D1–D19** system
> (D1–D19 built at commit `4d8952a`; the D19 toolbar wrapper is in place and green). D1–D19 are
> **frozen** and are **not** re-planned. This is an **existing-repo** run: `requirements.md`
> contains the marker sentence `This is an existing repository.` and a Current Tech Stack;
> **PyQt6 + pyqtgraph is a hard constraint**. No stack change, no schema change, no new
> dependency, no new external integration, and no live-order-path change. Items are labelled
> `[existing]`, `[new]`, or `[new/changed]`.
>
> **Defect.** D20 — the D19 wrapper pins **both** the toolbar widget **and** its `ToolbarScroll`
> `QScrollArea` to `setFixedHeight(36)` (`ui/main_window.py:102`, `:233`). The `QScrollArea` lays
> its horizontal scrollbar out **inside** that same 36px and shrinks the viewport above it, so the
> bottom of the toolbar content (label descenders) is clipped / covered by the scrollbar.
> **Decision (B7, 2026-10-06, user-confirmed):** keep the **content row at ~36px** and give the
> horizontal scrollbar its **own reserved lane below** the content — the **total strip is
> ~50–52px** (not ~60px). **B8 (user-confirmed):** **reserve the lane** and show the horizontal
> scrollbar **as-needed** (only on overflow), never overlapping the labels; the strip height stays
> stable in both states. D20 **explicitly supersedes/relaxes `AC-D19.4`'s `<= ~40px`** bound to the
> new **~52px container bound** (recorded on `AC-D19.4`); D19's scroll/elide reachability and the
> D17/D18 criteria stand unchanged.
>
> **Chosen mechanism (RC-D20-1).** The strip height is **derived**, not hard-coded:
> `TOOLBAR_CONTENT_HEIGHT (36) + horizontalScrollBar().sizeHint().height()`. On the reference macOS
> platform the extent is ~16px (total ~52px, the B7 figure); on the offscreen test platform it is
> **18px** (total **54px**, viewport **36px**), so the viewport always equals the content row when
> the scrollbar is shown and the lane sits **entirely below** the content on every platform. The
> literal-52 variant is **not** used.
>
> Companion proposal: `docs/plan_proposal.md`. As-built baseline: `docs/architecture.md`
> (increment D19 toolbar scroll/elide wrapper, validated 2026-10-05). Requirements:
> `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D20 / Journey 21 /
> `AC-D20.1`–`AC-D20.6`; A39–A40; R35–R36; B7–B8 answered 2026-10-06; DG29–DG30).

---

## Codebase Summary (existing repository — D20 surface)

> Inventory gathered with the **graphify** skill (`graphify-out/graph.json`, 2370 nodes,
> refreshed 2026-10-06) and then **validated against the current source files** (the repository is
> authoritative). The graph surfaced the D19 concept node **“Toolbar scroll/elide wrapper
> (ToolbarScroll QScrollArea)”** and its edges to `AC-D19.4` / `AC-D19.5` / `PA-D19-1` / the
> “Known Gotcha — toolbar QWidget minimumSizeHint pinning (D19)”, and the `ui/main_window.py` /
> `tests/test_toolbar_scroll_d19.py` symbols. Every claim below was confirmed by direct inspection
> of the current tree on 2026-10-06 (the graph node `QScrollArea (no frame, setWidgetResizable
> False, fixed 36px)` matches the source exactly).

**Toolbar construction — `[existing] ui/main_window.py:100–211`**
- `toolbar = QWidget()`; `toolbar.setObjectName("MainToolbar")`; `toolbar.setFixedHeight(36)`
  (`:100–102`); inline stylesheet `background: #101218; border-bottom: 1px solid #232938;`
  (`:103`).
- `tb_layout = QHBoxLayout(toolbar)`, margins `(8, 0, 8, 0)`, spacing `6` (`:104–106`).
- Fixed-width controls: `symbol_input` 120, `tf_combo` 90, `mode_combo` 110, `sound_btn` 56,
  `ext_hours_btn` 80, `tz_combo` 110, `draw_combo` 110, `draw_set_combo` 140,
  `draw_delete_btn` 38; plus variable-width buttons/labels (`Load Chart`, `Studies…`,
  `Alarms (0)`, `Alarm Mode`, `DOM`, `Sets…`, `Symbol:`, `TF:`, `Mode:`, `Draw:`, `|`).
- Layout ends with `tb_layout.addStretch()` then `conn_badge` (`QLabel("● Connecting")`,
  `:187–188`, `:210–212`). The toolbar's natural `minimumSizeHint().width()` is ≈ **1716px**.

**D19 toolbar scroll wrapper — `[existing] ui/main_window.py:223–234`**
- `toolbar_scroll = QScrollArea()`; `setObjectName("ToolbarScroll")`;
  `setFrameShape(QFrame.Shape.NoFrame)`; `setWidgetResizable(False)`;
  horizontal `ScrollBarAsNeeded`; vertical `ScrollBarAlwaysOff`;
  **`setFixedHeight(36)`** (`:233`); `toolbar_scroll.setWidget(toolbar)` (`:234`).
- **Consequence (the reported defect):** the `QScrollArea` is fixed at the **same 36px** as the
  content widget, and its horizontal scrollbar is laid out within that 36px, shrinking the
  viewport and clipping the bottom of the toolbar content (label descenders).

**Central-widget composition — `[existing] ui/main_window.py:236–242`**
- `central = QWidget()`; `vbox = QVBoxLayout(central)` (margins `0`, spacing `0`);
  `vbox.addWidget(toolbar_scroll)` (`:240`); `vbox.addWidget(self.chart_panel)` (`:241`);
  `self.setCentralWidget(central)` (`:242`).
- **Consequence:** the wrapper — not the bare toolbar — is `layout.itemAt(0).widget()`; the
  toolbar's ~1716px width lives inside the scroll content, so `centralWidget().minimumSizeHint()
  .width()` is small (D19 probe: **1716 → 88**) and the central widget can shrink. The wrapper's
  **height** has no effect on that horizontal minimum.

**D17/D18 width model — `[existing]` (unchanged by D20)**
- `MainWindow._chart_area_width()` returns `centralWidget().width()` (fallback `self.width()`);
  `MainWindow._apply_dock_widths()` is the single apply entry point (dock event filter,
  `resizeEvent`, `changeEvent(WindowStateChange)`, deferred normalize, right-dock visibility).
- `ui/dock_layout.py` (`[existing]`, pure, Qt-free): `CHART_MIN_WIDTH = 400`,
  `WATCHLIST_MIN_WIDTH = 150`, `RIGHT_DOCK_MIN_WIDTH = 200`, `WATCHLIST_CAP_FRACTION = 0.50`,
  `RIGHT_DOCK_CAP_FRACTION = 0.40`; `watchlist_max_width`, `right_dock_max_width`,
  `plan_dock_widths` (B3 cross-clamp). **Not touched by D20.**

**Affected test — `[existing] tests/test_toolbar_scroll_d19.py`**
- `T53-T02` (`:106–158`) asserts `toolbar.height() <= 40` at both the narrow (`:130`) and wide
  (`:156`) sizes — this bounds the **content widget**, which D20 keeps at 36px.
- `T53-T04` (`:183–211`) asserts `wrapper.height() == 36` (`:199`) and
  `wrapper.minimumHeight() == 36 and wrapper.maximumHeight() == 36` (`:200`) — this bounds the
  **container**, which D20 raises to the derived `TOOLBAR_CONTENT_HEIGHT + scrollbar extent`
  (offscreen 54px) and therefore **must** be updated in lockstep
  (`AC-D20.6` / R36).
- `T53-T01` (`:72–101`) asserts `centralWidget().minimumSizeHint().width() <= 750` and that
  `layout.itemAt(0).widget()` is the `"ToolbarScroll"` `QScrollArea` — **unchanged** by D20.
- `T53-T03` (`:163–178`) asserts the central width tracks the window — **unchanged** by D20.

**D17/D18 harnesses — `[existing] tests/` (unchanged by D20)**
- `tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`,
  `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`
  locate the toolbar by the stable `"MainToolbar"` objectName and assert it is **visible** and
  that no `toolbar.hide()` / `itemAt(0)` masking remains. They assert **widths / visibility**, not
  heights, so D20's vertical change does not touch them (A40); only the chart's *height* shrinks by
  the reserved lane (~16px macOS / ~18px offscreen).

**Existing data models / tables — unchanged by D20**
`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`, `OrderBookLevel`,
`UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`,
`studies`, `positions`, `trade_groups`, `position_group_map`. **No schema change.**

**Existing integrations in play — unchanged by D20**
IBKR historical/RT data, SQLite, the Qt signal bus, `QSettings("NDThinkChart","NDThinkChart")` key
`watchlist/width`, and `PyQt6.QtWidgets` layout/scroll-area APIs. **No new external integration.**

**Key structural fact the D20 design must respect.**
A `QScrollArea` lays its horizontal scrollbar out **inside its own geometry** and shrinks the
viewport above it. The D19 overlap exists purely because the wrapper's height equals the content
widget's height (36px). Giving the wrapper a height of **content row + the scrollbar's own
extent** makes the scrollbar occupy a lane *below* the content in both states — the scrollbar is
never drawn over the content, and `setWidgetResizable(False)` keeps the toolbar at its full natural
width so the central widget's minimum width (the D19 benefit) is untouched.

---

## Summary

D20 is a **minimal, in-place height change** to the D19 wrapper. The toolbar **content widget stays
fixed at 36px**; the `ToolbarScroll` `QScrollArea`'s fixed height is changed from the literal
**36px** to the **derived strip height `TOOLBAR_CONTENT_HEIGHT +
horizontalScrollBar().sizeHint().height()`** (36px content row + the scrollbar's own reserved lane),
so its horizontal scrollbar has a **reserved lane entirely below** the content. When the content
overflows the scrollbar is shown in that lane (viewport = strip − scrollbar extent = exactly the
36px content height); when it fits, the scrollbar is hidden and the lane stays reserved but empty,
so the strip height is stable in both states (B8). Measured offscreen: extent **18px → strip 54px**;
the requirement's `~50–52px` is the macOS figure (extent ~16px → 52px). The wrapper keeps `NoFrame`,
`setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`, so the
toolbar's ~1716px width is still held inside the scroll content and the **central widget's
horizontal minimum is unchanged from D19** (the D19 benefit is preserved). Nothing else changes:
`ui/dock_layout.py`, `_chart_area_width`, `_apply_dock_widths`, the watchlist cap, the single
right dock region, and all D1–D19 behaviour are untouched.

---

## Tech Stack Decisions

Existing constrained choices first, then the D20 additions/changes.

| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | **Unchanged `[existing]`:** Python 3.11+, PyQt6 (`≥6.6`), pyqtgraph (`≥0.13`). "Changing the tech stack" is a stated Non-Goal | Existing-repo hard constraint; D20 is a layout-height fix only | A new toolbar/scroll framework or web view (out of scope; no new dependency allowed) |
| Dock width model | **Unchanged `[existing]`** `ui/dock_layout.py` — cap constants and `plan_dock_widths` are **not** touched | A40/B6: D20 is vertical-only and does not alter the horizontal dock model | Change a cap (explicitly not adopted) |
| Test stack | **Unchanged `[existing]`** pytest + pytest-qt, offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS | Repo standard (Q8/Q9); the D20 legibility/lane checks are offscreen | Manual-only (rejected) |
| Toolbar overflow mechanism | **Unchanged `[existing]`** the D19 `QScrollArea` wrapper (`NoFrame`, `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`) | D20 does not change the mechanism; it only changes the wrapper's height | Replacing the wrapper — not adopted; D19/B5 settled it |
| **Toolbar content-row height** | **Unchanged `[existing]`** `toolbar.setFixedHeight(36)` (`ui/main_window.py:102`) | B7: the **content row does not grow**; `AC-D20.2` requires the content widget to stay ~36px | (b) grow the content row to ~44–48px — **explicitly rejected by B7** |
| **Scrollbar-lane height / wrapper height** | **`[new/changed]`** raise `toolbar_scroll.setFixedHeight(36)` → **`TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()`** (`ui/main_window.py:233`) — the **36px content row + the horizontal scrollbar's own reserved lane**, derived at construction time; keep `setWidgetResizable(False)`. Named constant `TOOLBAR_CONTENT_HEIGHT = 36`; the strip height is a derived value (`36 + extent`), so the code and the test share one source of truth | The `QScrollArea` lays its horizontal scrollbar inside its own geometry; sizing the wrapper to `content + scrollbar extent` gives the scrollbar its own lane **entirely below** the content, so the viewport always equals the content row when the scrollbar is shown and no glyph can be clipped (`AC-D20.1`–`AC-D20.3`). **Measured offscreen (2026-10-06): `sizeHint().height()` = 18px → strip 54px, viewport 36px; the requirement's `~50–52px` is the macOS figure (extent ~16px → 52px).** One-line change; no new widget | **Literal 52px fixed height** — **not adopted (RC-D20-1):** offscreen the scrollbar is 18px, so a 52px wrapper leaves a 34px viewport — the lane still overlaps the content row's bottom 2px and `viewport().height() >= toolbar.height()` is false. **Explicit separate lane widget** below the scroll area — **passed over:** the scrollbar belongs to the `QScrollArea` and is laid out inside it, so a separate widget cannot move the scrollbar out of the scroll area; the scroll area would still have to be `36 + extent` (redundant widget + second layout). **`setWidgetResizable(True)`** — rejected (lets the toolbar reflow/resize, breaks the single row). **Always-visible scrollbar** — rejected (B8 option b). **Overlay / auto-hiding macOS-style scrollbar** — rejected (B8 option c; can still cover the labels). **User-named total height** — rejected (B7 option c) |
| **Scrollbar visibility** | **`[new/changed]`** keep horizontal `ScrollBarAsNeeded`; the **lane is reserved** regardless of visibility so the strip height stays the derived value (offscreen 54px; macOS ~52px) in both states | B8: show the scrollbar only on overflow, never overlapping the labels; reserving the lane keeps the strip height stable (`AC-D20.3`) | Always-visible (B8 b) / overlay (B8 c) — **not adopted** |
| **Wrapper background (cosmetic, optional)** | **`[new]`** optionally style the `ToolbarScroll` background to match the toolbar strip (`#101218`) so the empty reserved lane is not a differently-coloured band | Keeps the reserved lane visually seamless; not required by any AC (D20's requirement is legibility + no overlap) | Leave the default palette background (a visible band below the toolbar) — acceptable but less coherent |
| Persistence | **No change:** `[existing]` `QSettings watchlist/width`; no new key | D20 adds no user-visible persisted state | Persist the toolbar scroll position — not requested |

---

## System Components

Each item is labelled `[existing]`, `[new]`, or `[new/changed]`.

- **`[existing]` central chart area** — `QWidget` + `QVBoxLayout` in `ui/main_window.py`
  (`:236–242`). Structurally unchanged; it holds the (now taller) scroll wrapper above the chart.
  Its `width()` remains `chart_area` for the D17/D18 maths; only its height loses the reserved lane
  (~16px macOS / ~18px offscreen).
- **`[new/changed]` toolbar scroll wrapper** — the D19 `ToolbarScroll` `QScrollArea` created in
  `ui/main_window.py` (`:223–234`). **Changed:** fixed height `36 → TOOLBAR_CONTENT_HEIGHT +
  horizontalScrollBar().sizeHint().height()` (the 36px content row + the scrollbar's own reserved
  lane; measured **54px offscreen**, **~52px on macOS**). **Unchanged:** `NoFrame`,
  `setWidgetResizable(False)`, horizontal
  `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`, `objectName "ToolbarScroll"`, the toolbar as
  its widget. This is the whole D20 mechanism.
- **`[existing]` toolbar `QWidget` and controls** (`ui/main_window.py:100–211`) — construction,
  fixed widths, `setFixedHeight(36)`, stylesheet, signal wiring, and `conn_badge` are **unchanged**;
  the widget stays the scroll area's content at its full natural width.
- **`[existing]` D17/D18 width model** — `ui/dock_layout.py`, `MainWindow._chart_area_width`,
  `MainWindow._apply_dock_widths`, the dock event filter, `resizeEvent`,
  `changeEvent(WindowStateChange)`. **Unchanged.** D20's height change does not affect the
  horizontal minimum or the clamp.
- **`[existing]` watchlist dock** and **`[existing]` single right dock region** — unchanged.
- **`[new/changed]` D19 test module + D20 assertions** — `tests/test_toolbar_scroll_d19.py`:
  `T53-T04`'s container-height assertions (`height() == 36`, `min/max == 36`) are updated in
  lockstep to the **derived relation** (`height() == toolbar.height() +
  horizontalScrollBar().sizeHint().height()`; `min/max == height()`), with the content row asserted
  at `TOOLBAR_CONTENT_HEIGHT` (36px); D20 adds the label-legibility / reserved-lane / as-needed
  assertions (`AC-D20.1`–`AC-D20.5`).

---

## Data Model

**No schema change. No new persisted state.**

- `[existing]` `QSettings("NDThinkChart", "NDThinkChart")` key `watchlist/width` (int, px) —
  retained unchanged.
- `[new]` none. D20 adds only in-memory widget geometry (the wrapper's fixed height) and named
  height constants — ephemeral view state, not a model.
- `[existing]` Right-region width/visibility is still not persisted (A36); no new key.
- Existing models/tables (`Bar`, `Position`, …; `bars`, `positions`, …) are unchanged.

---

## Integration Points

- **`[new]` none.** D20 adds no external service, dependency, IBKR call shape, or signal.
- **`[existing]` Qt layout / scroll-area APIs** — `QScrollArea.setFixedHeight`, the scroll area's
  own horizontal scrollbar extent (`horizontalScrollBar().sizeHint().height()`) and **mapped**
  position (`horizontalScrollBar().mapTo(wrapper, QPoint(0, 0)).y()` — offscreen `geometry()`
  reports `top == 0`, so `geometry()` must **not** be used for the lane assertion), `QVBoxLayout`,
  `QMainWindow.setCentralWidget` — the only APIs involved.
- **`[existing]` D17/D18 clamp path** — `_chart_area_width()` → `_apply_dock_widths()` unchanged;
  the central widget's **width** is unchanged by D20.
- **`[existing]` `QSettings`** — unchanged.
- **`[existing]` test toolbar/wrapper lookups** — the D19 `"MainToolbar"` / `"ToolbarScroll"`
  objectNames are retained; the D17/D18 harnesses need no change.
- **`[existing]` IBKR / SQLite / pyqtgraph** — unchanged; no new call type, no schema, no
  dependency.

---

## Non-Functional Approach

- **Correctness (labels not clipped — `AC-D20.1`):** the wrapper is sized to the content row plus
  the horizontal scrollbar's own extent, so the scrollbar is laid out **entirely below** the content
  and the viewport equals the content row (`>= 36px`) when the scrollbar is shown; no label glyph
  (including descenders) intersects the scrollbar's lane. Measured offscreen: strip 54px, viewport
  36px, scrollbar mapped to y = 36 (`>= toolbar.height()`). Verify in **both** states (scrollbar
  shown and hidden).
- **Correctness (height supersession — `AC-D20.2`):** container height is the **derived**
  `content row + scrollbar extent` (offscreen **54px**, macOS **~52px** — the requirement's
  `~50–52px` figure); content widget height `TOOLBAR_CONTENT_HEIGHT` = **36px** (unchanged from
  D19); the reserved lane (equal to the scrollbar's extent) is present **entirely below** the
  content; the strip stays `< 60px` (R35). `AC-D19.4`'s `<= ~40px` bound is explicitly superseded,
  not silently contradicted.
- **Correctness (as-needed in a reserved lane — `AC-D20.3`):** horizontal `ScrollBarAsNeeded`
  retained; at a wide width `horizontalScrollBar().isVisible()` is `False` while the strip height
  is **unchanged** (still the derived height — offscreen 54px); at a narrow width it is `True` and
  its **mapped** lane sits below the content row.
- **Correctness (D19 behaviour preserved — `AC-D20.4`, `AC-D20.5`):** the toolbar keeps its full
  natural width inside the scroll content, so at a narrow window every control stays reachable via
  horizontal scrolling (scroll range `> 0`); the content stays a **single row** and inside the
  central widget. The central-widget minimum-width benefit (D19 probe 1716 → 88) is unchanged —
  D20 changes only the wrapper's **height**.
- **Correctness (D17/D18 unaffected — `AC-D20.6`, A40):** only vertical space changes (~16px macOS
  / ~18px offscreen shorter chart); the horizontal dock model, caps, and clamp are untouched; the
  D17/D18 criteria hold in a toolbar-visible window.
- **Performance:** O(1) layout change; no per-frame cost, no bar/table iteration, no change to the
  dock clamp's cost profile.
- **High-DPI / font scaling:** the reserved lane is a real reserved space (not an overlay), so
  labels stay unclipped as fonts grow. The lane is **not** a fixed ~16px constant: the strip height
  is derived from `horizontalScrollBar().sizeHint().height()` (`content + extent`), so a taller
  scrollbar on a high-DPI/font-scaled platform automatically widens the lane and the viewport still
  equals the content row when the scrollbar is shown.
- **Security / live-order path:** untouched; Q9 holds — no automated test connects to live TWS or
  transmits an order.
- **Regression (`AC-D20.6`):** D1–D19 stay frozen; the D19 height assertions are updated in
  lockstep rather than left contradicting D20 (R36).

---

## Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| A platform's horizontal scrollbar extent exceeds a fixed reserved lane, so the viewport is < 36px when shown and clips the content | L | **Mitigated by the chosen mechanism:** the strip height is derived from `horizontalScrollBar().sizeHint().height()` (`content + extent`), so the lane always equals the scrollbar's own extent and the viewport equals the content row when shown; the test asserts `viewport().height() >= toolbar.height()` and the **mapped** lane position (`AC-D20.1` edge case) |
| The D19 height assertions (`T53-T04` `height() == 36`, `min/max == 36`) are left stale, leaving the suite red / contradictory (R36) | M (H impact) | Update them in lockstep to the **derived relation** (`height() == toolbar.height() + horizontalScrollBar().sizeHint().height()`; `min/max == height()`) with the content row asserted at 36px (`AC-D20.6`); the supersession is recorded explicitly on `AC-D19.4` |
| The reserved lane is visible as a differently-coloured band below the toolbar when the scrollbar is hidden | L | Optional: style the `ToolbarScroll` background to match the strip (`#101218`); not required by any AC, and the B7/B8 reserved lane is the accepted outcome |
| The offscreen scrollbar extent (18px) differs from the real macOS window (~16px), so an offscreen-only check misses a real clip (R34-style) | L | The chosen derivation uses the **actual** `sizeHint().height()`, so the strip adapts per platform (54px offscreen, ~52px macOS); the assertions test the viewport/content relation (not a literal height); record a manual `python main.py` check with the scrollbar both hidden and shown |
| The +extent wrapper height shrinks the chart and a D17/D18 assertion is height-sensitive | L | The D17/D18 harnesses assert widths/visibility only; re-run the full offscreen suite (Phase 3) and confirm no horizontal-model change |
| A D1–D19 behaviour regresses because the central widget is a scrollbar-lane shorter | L | No D1–D19 production file other than the D19 wrapper height is modified; full offscreen suite re-run (`AC-D20.6`) |
| Full-suite flakiness (shared on-disk test DB / collection-order SIGSEGV) is mistaken for a D20 regression | L | Per project memory, confirm any non-reproducible failure with a clean full-suite run before treating it as a regression |

---

## Implementation Phases (summary)

Full ordered phases, coverage map, `touches_files` sequencing, and plan-level assumptions are in
**`docs/plan_proposal.md`**.

1. **Phase 1 — Reserve the scrollbar lane in the D19 wrapper** `[new/changed]`: keep
   `toolbar.setFixedHeight(TOOLBAR_CONTENT_HEIGHT)` (36px); change `toolbar_scroll.setFixedHeight(36)`
   → `TOOLBAR_CONTENT_HEIGHT + toolbar_scroll.horizontalScrollBar().sizeHint().height()` (derived;
   offscreen 54px, macOS ~52px); keep `setWidgetResizable(False)` and the scrollbar policies. Covers
   `AC-D20.1`, `AC-D20.2`, `AC-D20.3`, `AC-D20.4`, `AC-D20.5` (implementation).
2. **Phase 2 — Update D19 height assertions + add D20 legibility/lane tests** `[new/changed]`:
   update `tests/test_toolbar_scroll_d19.py::T53-T04` in lockstep to the derived relation and add
   the D20 assertions (label bounding boxes vs the **mapped** scrollbar lane in both states;
   `height() == toolbar.height() + sizeHint().height()` / content 36px; as-needed in the reserved
   lane; D19 reachability preserved). Covers `AC-D20.1`–`AC-D20.5` (assertions), `AC-D20.6`
   (lockstep).
3. **Phase 3 — Regression + real-app verification** `[new/changed]`: full offscreen suite green
   (D17/D18 in a toolbar-visible window) and a manual `python main.py` check with the scrollbar
   hidden and shown. Covers `AC-D20.6`, R35.
