# Architecture — NDThinkChart Stabilization (as-built: D1–D15 + ESC revision + post-document rework ESC-013…ESC-021; verified 2026-09-28, 383 passed)

## Summary
An **as-built** description of a stabilization change-set against an existing
PyQt6 + pyqtgraph + official `ibapi` desktop trading terminal. **All of D1–D15 are
built and verified**, together with the ESC-002/003/006/007 revision and a
post-document rework wave (ESC-013…ESC-021): session shading, the crosshair chip in
the Y-axis lane, zoom controls/magnifier, the zoom label/position, a **linear**
volume axis with a dynamic scaling nice max (pinned family + live ceiling) and
price-coloured bars, volume bars that track the price body width, a volume-panel
hide/show toggle, inner-right drawing price labels, two double-click drawing
settings popups (zone `Rectangle`, horizontal line), a resizable/persistent
watchlist with double-click-to-load, and an explicit `RouterMode` gesture state
machine. The full offscreen suite is green (**383 passed**).

**Revision lineage:** the validated 2026-09-27 revision added (1) an explicit
`RouterMode` state machine for gesture precedence (**ESC-002**,
`AC-D3.7`–`AC-D3.9`), (2) the pinned continuous volume nice-number formula plus a
live intra-bar ceiling (**ESC-003/ESC-007/ESC-008**, `AC-D8.1`–`AC-D8.7`),
(3) the relocated crosshair price chip in the Y-axis lane with independently
verified dock-open visibility (**D2/Q33**, `AC-D2.1`–`AC-D2.3`), and (4) the
`AC-D11.4` re-scope to label-vs-label (**ESC-006**). A subsequent post-document
rework wave (ESC-013, ESC-014, ESC-015, ESC-016, ESC-017, ESC-020, ESC-021 — see
“Post-document rework” below) is folded into this as-built description. In
existing-repo mode every item below is labelled `[existing]`, `[new]`, or
`[new/changed]`.

Persistence, broker I/O, and the live-order path remain untouched — no new tables,
no new IBKR calls, no new external integrations.

## Tech Stack Decisions
| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | Unchanged: Python 3.11+, PyQt6, pyqtgraph | Stabilization run; changing the stack is a stated non-goal | New charting library or embedded web view |
| Session boundary math (Batch 1) | Pure `services/session_service.py` using `ZoneInfo("America/New_York")` | Qt-free, unit-testable, DST-correct | Inline math in `ChartPanel` (untestable); `pandas_market_calendars` (holidays unneeded) |
| Session shading primitive (Batch 1) | `pg.LinearRegionItem(orientation=Vertical, movable=False)` per band, z below candles | Full-height, no price range needed, one item per band | `StudyOverlay.add_band` (needs bottom/top); `fillBetween` (sentinel y); 2×`InfiniteLine` per band |
| Zoom controls / magnifier (Batch 1) | `ui/chart_controls.py` (signal-emitting `QFrame`) + `ui/zoom_overlay.py`, mediated by `ChartMouseRouter` | Logic-free widget, testable; fits existing overlay-precedence pattern | Main-toolbar buttons; pyqtgraph ViewBox zoom modes (no persistent tool state) |
| **Gesture routing (ESC-002, revision)** | **`[new/changed]` `RouterMode { IDLE, DRAWING, ZOOMING, ALARM_PLACING }` with a single `ChartMouseRouter._active_mode` and a normative, total transition table (see “Router state machine” below)** | Precedence was implicit (three booleans resolved by call order); a single enum makes zoom/drawing mutually exclusive by construction and encodes `AC-D3.7`–`AC-D3.9` | Keep booleans + documented order (still allows both true); `(zoom,draw,alarm)` tuple + `sum<=1` assert (8 states, unreachable combos); overlays aware of each other (N×N coupling) |
| **Crosshair chip (D2, revised Q33 2026-09-27)** | **Grey pill (`TextItem`) with WHITE text in the Y-axis lane outside the plot**, left-anchored at the plot’s vertical axis line (`anchor=(0,0.5)`, scene `x >= view_rect.right()`); axis-tick-label overlap permitted. The lane width is reserved up-front (`_reserve_price_tag_lane()` probes a `TextItem` of `PRICE_TAG_LANE_SAMPLE = "123,456.78"`, stores `_price_lane_width`, and folds it into the zoom-control offset) so a long price never grows the axis mid-hover (audit `D-13`). **Dock-open visibility** is a separately verified acceptance criterion (`AC-D2.1`) requiring **independent Code Reviewer verification after Build** (A25; verification performed and closed via ESC-016/T35). Supersedes the Batch-1 inside-plot right-align | Re-opened D2: the Batch-1 inside-plot position at `view_rect.right()-2` put the chip under the right-hand dock; the lane keeps it out of the data area while remaining visible | Keep the inside-plot right-align (the original defect); widen the axis; deconflict against tick labels (explicitly not required) |
| **D4 zoom label/position** | `-`/`+`/`Reset` 14px/700, `⌕` 21px/700 (14×1.5), button 28×24; cluster `x = panel.width - ctrl.width - axis_width - 12` (fallback 50, `x>=8`), `y=10` | `Reset` was legible at 14px but `⌕` looked small; a fixed margin still overlapped the axis, so position relative to the dynamic axis width keeps the outline inside | One size for all four; larger buttons; fixed 28px margin (clips) |
| **D5 volume log → superseded by D8** | D5 shipped volume log Y (`setLogMode('y',True)`, `0→1.0`, `yRange=(1, max*1.1)`); **D8 supersedes it** | D5 was confirmed Q17 but the new screenshot (D8/Q20) rejects log and negatives | n/a — D8 is the current decision |
| **D6 wick rendering** | Wick: body-coloured `QPen`, `widthF=1.0`, **`setCosmetic(True)`**, `FlatCap`, drawn **before** the body; body cosmetic 1px outline with data half-width **clamped to ≥4-device-px** via `ViewBox px_per_sec`; `ChartPanel._refresh_candles` applies `vb.setRange(...)` **before** generating the candle picture so the clamp binds on a first auto-range load (ESC-013 ordering contract, audit `D-12`) | `CandlestickItem` paints into a `QPicture` in data coordinates; non-cosmetic pens scale with the ViewBox and go sub-pixel at high density. Cosmetic pens are device-pixel stable. The clamp reads `px_per_sec` at generation time, hence the generate-after-`setRange` order | Non-cosmetic pens with larger `w` (no pixel ratio); pixel-space drawing without `QPicture` (more invasive, loses caching) |
| **D7 inter-candle gap** | Body half-width `w = median_diff * 0.325` (gap 35%), keep `0.25` single-bar fallback, keep D6 ≥4-device-px minimum; `xRange` padding `-2*bar_w / +8*bar_w` unchanged | Q19 confirmed “go 35% gap for now” as a modest, testable increase from today’s `0.40` (20% gap); only inter-candle gap grows (~75% more gap) | `0.30` (40% gap, airier); widen `xRange` (adds outer framing, not gap) |
| **D8 volume scale (revises D5; family pinned by RG-002, 2026-09-27)** | Volume `ViewBox` **linear Y** (`setLogMode(y=False)`), `yRange=(0, nice_max)` where `nice_max` is the **smallest member of the single continuous family `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` (floor `100`, no fixed ceiling) that is `>= max_vol*1.1`**; `max_vol == 0 → 100`; `y0=0`; ticks `500.0K / 1.0M`, no negatives; bars **price-coloured** (`#34d399` / `#f87171` by `close>=open`). The old fixed list `[10k, …, 10M]` is **retained only as a test fixture** | Current log gives negative ticks and hides the desired `500.0K–2.5M` look; the reference is linear with a dynamic nice max and price-coloured bars (Q20). The pinned family reproduces every confirmed value (`750K`, `1.5M`) and the `10.5M→15M`, `45M→50M`, `50M→75M` cases. `0` lower bound matches “volume cannot go below zero” | Keep log with `0→1.0` floor (rejected); a log/linear toggle (more UI than requested); the fixed list (coarse above 10M, `10k` floor) |
| **D9 volume bar width** | `volume_bars.width = w*2` (same `w` as price post-D7 = 65% of `median_diff`), `y0=0` (the implicit `BarGraphItem` default — `y0` is not supplied), X stays `setXLink`ed; the volume half-width is derived from the **final** view range **after** `vb.setRange` (ESC-020 ordering contract, audit `D-12`) | Fixed `width=0.6` drifts from the price 35% gap; sharing `w` guarantees vertical alignment including the dense 4px minimum. Deriving `w_vol` after `setRange` is required because the shared ≥4-device-px clamp reads `px_per_sec` at generation time | Fixed `0.6`; `0.9×price` (subtly narrower, not requested) |
| **D10 volume toggle** | **Top left of the volume panel** (bottom-left of the price chart) — a **checkable text label `Volume`** (not an eye icon), default **visible**, toggles `volume_plot.setVisible()` and rebalances the `QSplitter` so `price_plot` expands; **not persisted** | Q22 confirmed the placement (A23, 2026-09-27); Q31 confirmed the affordance is the **text label `Volume`** (A22); not persisted was the proposal | Toolbar `Volume` button; `QSettings` persistence (future); splitter-handle-only hiding; an eye icon (explicitly rejected) |
| **D11 drawing price labels (ESC-006 re-scoped)** | Inside-plot `TextItem` at `x = view_rect.right() - 4`, `anchor=(1,0.5)`, `Z=10`, colour = drawing colour; one per price (zone top+bottom, trendline/Fib per level); stacked by the **measured label bounding-box height** — `offset = max(15 px, bbox_height, previous_bbox_height)` so consecutive label boxes never intersect (ESC-014, audit `D-7`); added to the price plot scene. **`AC-D11.4` now covers label-vs-label stacking only** — the crosshair chip is in the Y-axis lane (D2/Q33) and is out of scope for D11 collision accounting | Q23 confirmed inner-right inside the plot; Q33 (2026-09-27) moved the chip to the axis lane, so chip-vs-label deconfliction is retired. A real ~23 px label overlaps a hard-coded 15 px offset, so the offset is measured from the emitted label bbox | Axis-area labels (clipped by dock); left-side labels; keeping the chip in the label lane (the ESC-006 defect) |
| **D12 zone settings popup** | Modal `Rectangle` dialog (pencil + `X`), 4 tabs **Style / Text / Coordinates / Visibility**; **Style: `Extend` omitted** (zone always both sides), `Border` + `Middle line` (unchecked) + `Background` (checked) remain; `#1/#2 (price, bar)` steppers; 8-row Visibility timeframes | Q24 “Extend is omitted” confirmed; the reference’s `Extend right` is the only control to drop | Keep `Extend right` (contradicts user); `Extend both` disabled |
| **D15 horizontal line popup** | Modal `Horizontal line` dialog, same 4-tab pattern; **Style:** `Line` (white solid); **Text:** `12`, `B`/`I`, `Add text`, `Top`/`Right`; **Coordinates:** single `#1 (price)` stepper; Visibility = same 8 rows as zone | Q30 confirmed — four screenshots are the spec; single coordinate is the only structural difference from the zone | Reuse the zone dialog with hidden `#2` (shows an irrelevant field) |
| **D13 watchlist width** | Docked Watchlist freely draggable to `min(floor(0.50×W), W−400)` with min `150px` and chart min `400px`; width persisted as an `int` pixel value via **`QSettings` `watchlist/width`** (default ~220px), clamped on restore and window resize; floating geometry unconstrained | Q25/Q26 confirmed the 50% cap and persistence; `QSettings` avoids a `watchlist` table migration and is per-user | Store width in SQLite (migration cost); no persistence (user asked for it) |
| **D14 watchlist double-click** | `cellDoubleClicked` → set `symbol_input` to the row symbol (uppercased) → call the existing `MainWindow.load_chart()` with current `tf_combo`/`ext_hours_btn`; no-op if same `_current_symbol` (case-insensitive) or IBKR disconnected (`status_bar` message); header/empty area no-op | Q27–Q29 confirmed “identical to Load Chart” semantics with no-ops | A separate load path (duplicates logic); single-click load (loses selection) |
| **D14 mid-drag mode reset (ESC-010)** | A symbol change (including the mid-drag double-click path, `AC-D14.4`) clears the drawing draft/drag **and** returns the router to `IDLE` (transition TR-17) | `DrawingOverlay.set_data()` already clears the draft defensively (`:112–118`); without the mode reset `_active_mode` can read `DRAWING` after the tool was implicitly cleared | Rely on `set_data()` alone (leaves the router mode stale) |
| Drawing drag stability (runtime fix 2026-09-19) | `DrawingOverlay._apply_drag` mutates items **in place**; `_remove_items`/`_clear_all_items` defensively clear `GraphicsScene.dragItem` before `removeItem`; `fibonacci` rebuilds only on level-count change | Remove+rebuild mid-drag left `dragItem` dangling → `sendDragEvent` → `InfiniteLine.mouseDragEvent` on a deleted C++ object → `RuntimeError`. In-place mutation preserves C++ identity | Suppress the warning (hides bug); fork pyqtgraph (maintenance); retain refs (leaks) |
| Testing | pytest + pytest-qt, offscreen, no live TWS | Repo standard; confirmed Q8/Q9 | Manual-only (rejected) |

## System Components

### Existing layers (unchanged)
- **`config/`** — `settings` (env), `paths` (bundle-aware DB/resource paths), `theme.qss`.
- **`data/`** — `models`, `db` (SQLite singleton), `bar_cache`, `bar_aggregator`, `alarm_store`, `drawing_store`, `study_store`.
- **`services/`** (pure, Qt-free, tested) — `indicator_service`, `gap_vix_service`, `ict_service`, `drawing_service`, `alarm_service`, `sound_service`, `strategy_detection`, plus Batch-1 `session_service`.
- **`ibkr/`** — `client`, `bridge` (Qt signals), `id_manager`, `pacing`, `contracts`, `market_data`, `realtime_bars`, `market_depth`, `order_book`, `orders`, `account`, `subscription_manager`.
- **`ui/`** — `main_window` (orchestrator), `chart_panel`, `candlestick_item`, `chart_mouse_router`, `drawing_overlay`, `alarm_overlay`, `studies_dialog`, `active_trader_panel`, `active_portfolio_panel`, `watchlist_panel`, `overlays/{base,gap_overlay,vix_overlay,ict_overlay}`.

### Built (D1–D6, runtime fix)
- **`services/session_service.py`** `[existing]` — `session_bands(bars, timeframe)`; ET pre/post intervals (DST-aware), clipped to the loaded range; `[]` for `1 day`.
- **`ui/overlays/session_overlay.py`** `[existing]` — `SessionOverlay(StudyOverlay)`; one vertical region per band, owned via `clear()`.
- **`ui/chart_controls.py`** `[existing]` — `ChartControls(QFrame)`; emits `zoom_in`, `zoom_out`, `magnify_toggled(bool)`, `reset`; stylesheet `-`/`+`/`Reset` 14px/700, `⌕` 21px/700.
- **`ui/zoom_overlay.py`** `[existing]` — rubber-band area zoom; sets both axes on release; cancels on `Esc`/right-click; **stays active** after a completed zoom (`AC-D3.4`).
- **`ui/chart_mouse_router.py`** `[new/changed]` — the promoted `RouterMode` state machine (271 lines): the enum, single `_active_mode`, guard-clause dispatch, intent helpers and the RC-3 property-setter reconciliation (see “Router state machine” below). It supersedes the former 51-line tri-boolean router (audit `D-2`).
- **`ui/chart_panel.py`** `[new/changed]` — `_position_zoom_controls()` left-of-axis and lane-aware; crosshair chip relocated to the Y-axis lane (`anchor=(0,0.5)`, D2/Q33); volume `ViewBox` linear with the pinned scaling generator (`_nice_volume_max`, D8); volume `BarGraphItem` `width = w*2` (D9); live `_vol_max`/`_ensure_volume_range` ceiling (ESC-007); the `Volume` text-label toggle (D10); `_reserve_price_tag_lane()` (audit `D-13`) (audit `D-3`).
- **`ui/candlestick_item.py`** `[new/changed]` — cosmetic body-coloured wick behind the body; body cosmetic outline + the ≥4-device-px minimum; `w = median_diff*0.325` (D7; `0.25` single-bar fallback) (audit `D-4`).
- **`ui/drawing_overlay.py`** `[existing]` — in-place drag mutation + defensive `GraphicsScene.dragItem` clearing (runtime fix 2026-09-19); D11 measured-bbox labels and the D12/D15 dialogs are listed under “Implemented changes” below.

### Implemented changes (Batch 3–9: D7–D15 + revision)
- **`ui/chart_mouse_router.py`** `[new/changed]` — `RouterMode` enum, single `_active_mode`, guard clauses in `view_mouse_press`/`view_mouse_drag`/`view_mouse_click`, the normative transition table, intent helpers (`enter_zoom`, `enter_drawing`, `enter_alarm_placing`, `exit_to_idle`) and the RC-3 property-setter reconciliation (see “Router state machine”).
- **`ui/chart_panel.py`** `[new/changed]` — router adapters (`set_zoom_mode`/`set_drawing_tool`/`set_alarm_mode` delegate to the router and keep widget state in sync; signatures unchanged); a `zoom_refused` signal for the `AC-D3.9` status hint; D2/Q33 chip in the Y-axis lane; volume `BarGraphItem` `width = w*2` (D9); volume `ViewBox` linear `yRange=(0, nice_max)` via the scaling generator, price-coloured brushes, `500.0K / 1.0M` tick formatter (D8); live ceiling via a cached running max (ESC-007); D10 `Volume` text-label toggle + splitter handling.
- **`ui/main_window.py`** `[new/changed]` — one status-bar connection for `ChartPanel.zoom_refused` (`AC-D3.9`); D13/D14 watchlist wiring and `QSettings` persistence; ESC-017 `_on_drawing_tool_mode_changed`/`_reset_draw_combo_to_cursor` mirror the overlay’s `mode_changed("cursor")` back into the toolbar combo on TR-4/TR-17.
- **`ui/candlestick_item.py`** `[new/changed]` — `w` factor `0.325` (D7); single-bar `0.25` fallback and D6 4px minimum unchanged.
- **`ui/drawing_overlay.py`** `[new/changed]` — `mouseDoubleClickEvent` hit-test → open the matching settings dialog (D12 zone, D15 horizontal); inner-right `TextItem` labels (`view_rect.right()-4`, `anchor=(1,0.5)`, measured-bbox label-vs-label stacking) for all drawing kinds (D11); symbol-change mode reset support (TR-17 / `AC-D14.4`).
- **Dialogs** `[new]` — `ui/zone_settings_dialog.py` (`Rectangle`, 4 tabs, `Extend` omitted) and `ui/horizontal_line_settings_dialog.py` (`Horizontal line`, 4 tabs, single `#1 (price)`). Shared helpers (`ui/drawing_settings_common.py`) for colour swatches, numeric steppers, and the 8-row Visibility grid.
- **`ui/watchlist_panel.py`** `[new/changed]` — splitter min/max `[150, min(floor(0.50×W), W−400)]`, `QSettings watchlist/width` persistence + restore clamp, and `cellDoubleClicked` → `load_chart()` with same-symbol/disconnected no-ops (D13/D14).

### Router state machine (ESC-002, `AC-D3.7`–`AC-D3.9`)
`[new/changed] ui/chart_mouse_router.py` introduces an explicit, single-valued state:

```python
class RouterMode(Enum):
    IDLE = auto()            # default; cursor/pan; alarm & drawing still hit-tested
    DRAWING = auto()         # a drawing tool is armed (draft may be in progress)
    ZOOMING = auto()         # magnifier active; rubber-band selection armed
    ALARM_PLACING = auto()   # alarm placement mode armed
```

`_active_mode` is the **single source of truth**; an enum value is mutually exclusive
by construction (`DRAWING ∧ ZOOMING` can never be true). Every high-level handler
begins with a **guard clause** that dispatches on `_active_mode`, not on three
independent `is_active()`/`tool_active()` probes. The overlay pointers
(`drawing`/`alarm`/`zoom`) are retained as dispatch handlers.

**Dispatch by mode** (`view_mouse_click` in `DRAWING` reaches the drawing overlay only —
documented behaviour, RC-4b; alarm mode is force-cleared whenever a drawing tool is
armed, so alarm click is unreachable there in production wiring):

| `_active_mode` | `view_mouse_press` | `view_mouse_drag` | `view_mouse_click` |
|---|---|---|---|
| `IDLE` | alarm → drawing (alarm-first, miss falls through) | alarm → drawing | alarm → drawing (prefers alarm then drawing) |
| `DRAWING` | drawing only | drawing only | drawing only |
| `ZOOMING` | zoom only | zoom only | zoom only (returns `False`; view unchanged) |
| `ALARM_PLACING` | alarm only | alarm only | alarm only |

**Normative transition table** (`from` = mode before, `to` = mode after):

| # | From | Trigger | To | Side effects (required) | AC |
|---|---|---|---|---|---|
| TR-1 | `IDLE` | drawing tool selected | `DRAWING` | `drawing.set_tool(tool)`; `zoom.set_active(False)`; alarm mode off | existing |
| TR-2 | `IDLE` | magnifier toggled on | `ZOOMING` | `zoom.set_active(True)` | AC-D3.2/3.4 |
| TR-3 | `IDLE` | alarm placement activated | `ALARM_PLACING` | `alarm.set_alarm_mode(True)`; drawing tool forced to `Cursor` | existing |
| TR-4 | `DRAWING` | magnifier invoked | `ZOOMING` | cancel the in-progress drawing and **discard the draft** (no half-drawn artefact); clear the drawing tool; `zoom.set_active(True)`; uncheck the draw combo | **AC-D3.7 forward (Q35 (a))** |
| TR-5 | `ZOOMING` | drawing tool selected | `DRAWING` | exit `ZOOMING` (`zoom.set_active(False)` + `zoom.cancel()`); activate the tool | **AC-D3.7 reverse (A26)** |
| TR-6 | `ZOOMING` | alarm placement activated | `ALARM_PLACING` | exit `ZOOMING` (`zoom.set_active(False)` + `zoom.cancel()`); enter alarm placement (not blocked by zoom) | **AC-D3.8** |
| TR-7 | `DRAWING` | alarm placement activated | `ALARM_PLACING` | drawing tool forced to `Cursor` (draft discarded); `alarm.set_alarm_mode(True)` | existing |
| TR-8 | `ALARM_PLACING` | drawing tool selected | `DRAWING` | alarm mode off; `drawing.set_tool(tool)` | existing |
| **TR-9** | **`ALARM_PLACING`** | **magnifier invoked** | **unchanged (`ALARM_PLACING`)** | **REFUSE:** do NOT enter `ZOOMING`; do not touch the zoom overlay; the pending alarm placement is NOT cancelled; a status-bar hint is shown; the magnifier control is left unchecked | **AC-D3.9 (Q36 (b))** |
| TR-10 | `DRAWING` | tool set back to `Cursor` | `IDLE` | `drawing.set_tool(TOOL_CURSOR)` | existing |
| TR-11 | `ZOOMING` | magnifier toggled off | `IDLE` | `zoom.set_active(False)` + `zoom.cancel()` | AC-D3.3/3.4 |
| TR-12 | `ZOOMING` | symbol / timeframe change | `IDLE` | `zoom.set_active(False)` (A6) | A6 |
| TR-13 | `ALARM_PLACING` | alarm mode off | `IDLE` | `alarm.set_alarm_mode(False)` | existing |
| TR-14 | any | Esc during a magnifier drag | unchanged (`ZOOMING`) | `zoom.cancel()` only — the selection is cancelled, the mode stays active | **AC-D3.3 + AC-D3.4** |
| TR-15 | any | right-click during a magnifier drag | unchanged (`ZOOMING`) | `zoom.cancel()` only | AC-D3.3 |
| TR-16 | any | Reset clicked | unchanged | view refit only; mode not changed | AC-D3.5 |
| TR-17 | `DRAWING` | symbol change (incl. D14 mid-drag double-click) | `IDLE` | clear the drawing draft/drag; reset router mode to `IDLE` | AC-D14.4 / D3 edge case |

The table is **total** for every `(mode, trigger)` pair the router exposes;
`ALARM_PLACING + magnifier → ALARM_PLACING` (TR-9) is the cell that closes it.

**`_active_mode` derivation / synchronisation (RC-3).** The router is the single writer
of `_active_mode`; `ChartPanel` routes user intent through the router. Because the five
preserved router tests construct the router by **direct attribute assignment**
(`router.drawing = …; router.alarm = …`) and never call an intent API:

1. `drawing`, `alarm`, `zoom` are **properties** backed by `_drawing`/`_alarm`/`_zoom`;
   each setter stores the overlay and calls `_reconcile_mode_from_overlays()`.
2. `_reconcile_mode_from_overlays()` derives `_active_mode` with precedence
   **`DRAWING > ZOOMING > ALARM_PLACING > IDLE`**, probing each overlay defensively
   (`getattr(overlay, "tool_active", lambda: False)()` etc.) because the test
   `FakeOverlay` implements only `tool_active()`.
3. Hot handlers **do not re-derive** the mode; they dispatch only on `_active_mode`.
   In `IDLE`, `view_mouse_press`/`view_mouse_drag` keep the defensive
   `not drawing.tool_active()` guard around the alarm-first attempt; `view_mouse_click`
   tests only `if self._alarm is not None`. This is *not* a behavioural difference:
   `_active_mode == IDLE` implies `_reconcile_mode_from_overlays()` found no
   `tool_active()` overlay (a drawing tool would have forced `DRAWING`), so the guarded
   and unguarded conditions are equal in every reachable state (audit `D-11`).

`[existing] AlarmOverlay` / `DrawingOverlay` keep their accessors; the router consults
them only inside `_reconcile_mode_from_overlays()` (the wiring boundary). `enter_zoom()`
returns `False` (no mode change) in `ALARM_PLACING`; the `ChartPanel` adapter re-unchecks
the magnifier button (`blockSignals`) and emits `zoom_refused`, which `MainWindow`
connects to `status_bar.showMessage(...)` — satisfying `AC-D3.9` without the router
touching any widget.

### Volume nice-number generator (ESC-003 / ESC-008, RG-002 pinned)
`[new/changed] ui/chart_panel.py::_nice_volume_max` is a **pure, importable**
generator over the **single** family **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`**
(`10 × 10^k` is the next decade’s `1`), floored at **`100`**, with **no fixed ceiling**:

```
nice_max = min { v in family, v >= 100 : v >= max_vol * 1.1 }
max_vol == 0  ->  100
```

Testable properties: monotonic non-decreasing; tight coverage
`nice_max / (max_vol * 1.1) <= 2` where the ceiling is above the `100` floor
(`max_vol >= 100/2.2 ≈ 45.5`); the `40M–50M` cases come from the family
(`45M → 50M`, `50M → 75M`). Worked examples that all agree: `0→100`, `800→1_000`,
`3_000→5_000`, `8_000→10_000`, `10_000→15_000`, `80_000→100_000`,
`1_050_000→1_500_000`, `2_200_000→2_500_000`, `10_500_000→15_000_000`,
`45_000_000→50_000_000`, `50_000_000→75_000_000`. The validated axis set
(`0, 500.0K, 1.0M, 1.5M, 2.0M, 2.5M` ticks per Q20) and the `500.0K / 1.0M` formatter
(`AC-D8.3`) are preserved. The original fixed list
`[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]` is retained
**only as a test fixture** (every entry is a family member). `_nice_volume_max(0)`
returns the floor `100` (`AC-D8.4`); the retained fixture cross-checks the family
(see `tests/test_volume_linear.py`).

### Live volume ceiling (ESC-007, `AC-D8.6`/`AC-D8.7`)
`w` (candle body half-width) is computed **O(N) once per data load**, and the volume
`nice_max` is computed **O(N) once per data load** from `max(bar.volume)` using the
generator above — **with one explicit exception**: because the **forming last bar’s
volume grows live**, the volume Y ceiling must track the live maximum or the tallest
bar is clipped. The ceiling is therefore **also updated on real-time volume changes**,
but that update is **O(1) against a cached running max**: keep a cached `_vol_max` (the
load-time maximum); on an intra-bar tick compute
`live_max = max(cached_max, last_bar.volume)` and **only widen** the ceiling when
`live_max` crosses the current `nice_max` (a non-crossing tick performs no range write).
On a new bar / new load, `_vol_max` is refreshed O(N). `auto_range=False` refresh paths
(`set_timezone()`) re-apply the cached ceiling rather than being gated on `auto_range`.
This is the documented exception to the per-load rule, and it never clips the forming
bar. *(Corrects the earlier canonical claim that `nice_max` is “not per intra-bar
tick”.)*

### Component relationships
`MainWindow` owns `ChartPanel`, the Watchlist dock, and the Ext-Hours state.
`ChartPanel` owns the price plot, `CandlestickItem`, `SessionOverlay`, `ZoomOverlay`,
the child `ChartControls`, the `ChartMouseRouter`, and the volume `ViewBox` (plus the
D10 toggle and D11 labels). `ChartMouseRouter` is the **single writer of `_active_mode`**
and mediates ViewBox gestures between `ZoomOverlay`, `AlarmOverlay`, and
`DrawingOverlay`. `DrawingOverlay` owns its items, opens the D12/D15 dialogs, and renders
D11 labels. `WatchlistPanel` emits a double-click that `MainWindow` maps to the existing
`load_chart()` path. `reDrawings` payloads persist through `DrawingStore`. The D2 chip’s
Y-axis lane width is reserved up-front (`_reserve_price_tag_lane()` → `_price_lane_width`,
folded into the zoom-control offset) so the chip never grows the axis on hover
(audit `D-13`); `MainWindow` mirrors the overlay’s `mode_changed("cursor")` back into the
toolbar draw combo via `_reset_draw_combo_to_cursor()` on TR-4/TR-17 (ESC-017,
audit `D-14`).

## Data Model
**No schema changes.** D7–D11 are ephemeral view state (candle width, volume scale,
volume visibility, label geometry). D12/D15 read/write the existing `drawings` table
via `DrawingStore` (`payload` JSON: horizontal `{"y": …}` and zone
`{"x1","x2","y1","y2"}`, each plus additive `style`/`text`/`visibility` sub-objects
written by the D12/D15 dialogs and round-tripped on load) with
`services.drawing_service.normalize_payload` still validating. D13 persists a single
`int` pixel width via `QSettings` (not SQLite).
The router mode is **ephemeral runtime state**; the volume running max is an **in-memory
field** on `ChartPanel`. The existing models (`Bar`, `Alarm`, `Drawing`, `DrawingGroup`,
`Position`, `TradeGroup`, `OrderBookLevel`, `UserOrder`) and tables (`bars`, `watchlist`,
`alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `positions`,
`trade_groups`, `position_group_map`) are unchanged.

*As-built note:* `data/db.py` defines `_init_schema` **once** (`data/db.py:14–111`;
the file is 154 lines), followed by `_migrate_schema` (`:113–121`) and
`_table_columns` (`:118`). T26/ESC-001 removed the former shadowed second definition;
`tests/test_db_schema.py` guards the single-definition/schema contract. The previously
flagged latent hygiene debt (audit `D-6`) is **resolved** — no behaviour change.

## Integration Points
- **IBKR historical / RT data** — no new calls. D13/D14 reuse the existing
  `MainWindow.load_chart()` sequence (cancel prior RT `reqId` → `BarCache` → delta
  `reqHistoricalData` → RT `subscribe`); D8/D9 read `Bar.volume`/`close`/`open` only.
- **SQLite** — D12/D15 use `DrawingStore.update_drawing`; no schema change.
- **Qt signal bus / QSettings** — D10 toggle `toggled(bool) → volume_plot.setVisible`;
  `ChartPanel.zoom_refused → status_bar.showMessage` (`AC-D3.9`); D13 uses
  `QSettings("watchlist/width")`; `DrawingOverlay.mode_changed("cursor") →
  MainWindow._reset_draw_combo_to_cursor()` (ESC-017); `IBBridge` unchanged.
- **pyqtgraph GraphicsScene** — `DrawingOverlay` touches `scene.dragItem` only via
  defensive nulling before `removeItem` (runtime fix). No fork.

## Non-Functional Approach
- **Correctness (gesture routing):** the `RouterMode` enum makes `DRAWING` and
  `ZOOMING` mutually exclusive; the transition table is total and implemented as
  router intent helpers so code and table cannot drift; the five preserved router tests
  pass verbatim via the property-setter reconciliation.
- **Correctness (chart geometry):** D7’s 35% gap is proportional (`0.325× median_diff`)
  with the D6 4px minimum so dense 1-min stays positive; D9 shares the same `w`;
  D8 ticks are `0`-based linear with nice rounding (3–5 ticks) and no negatives.
  Because both the D6 body clamp and the D9 shared-width minimum read
  `ViewBox px_per_sec` at generation time, `ChartPanel._refresh_candles` applies
  `vb.setRange(...)` **before** generating the candle picture and derives `w_vol` from
  the **final** view range (ESC-013/ESC-020 ordering contract, audit `D-12`).
- **Correctness (drawings):** D11 labels are `anchor=(1,0.5)` inside
  `view_rect.right()-4`, repositioned on `sigRangeChanged`, so they are never clipped
  by the right axis/dock; nearby labels are stacked by their **measured bbox height**
  (`max(15, height, previous height)`, ESC-014 — audit `D-7`) so consecutive boxes never
  intersect; D12/D15 dialogs pre-fill from the drawing payload and
  persist via `DrawingStore`. D2 chip renders in the Y-axis lane (grey pill, white
  text) with axis-tick overlap permitted (`AC-D2.1`–`AC-D2.3`).
- **Correctness (watchlist):** D13 clamps `[150, min(floor(0.50×W), W−400)]` on
  restore and resize; D14 mirrors `load_chart` exactly and no-ops on same
  symbol/disconnected; a mid-drag symbol change also resets the router mode
  (`AC-D14.4`).
- **Performance:** `w` is O(N) once per data load; volume `nice_max` is O(N) once per
  data load **with the documented live-ceiling exception** (`AC-D8.6`) where the
  intra-bar update is O(1) against a cached running max (see “Live volume ceiling”).
  Router dispatch is O(1) (one enum compare per handler); mode reconciliation runs only
  at wiring boundaries; dialog creation is on demand; labels are bounded by drawing
  count.
- **High-DPI:** D6 cosmetic pens and D11 label placement are device-pixel aware
  (`AC-D6.4`, `AC-D11.5`); the D2 chip is a scene `TextItem` and inherits existing
  scaling.
- **Security:** live-order path untouched; Q9 holds — no automated test connects to
  live TWS or transmits an order.
- **Scalability:** overlay/label counts bound to drawing count; volume/price item
  counts bound to bar count; no per-frame allocation added.

## Parallel-Build Sequencing Constraint (`touches_files`)
The pipeline now runs Build as a **Lead + Worker pair**: the Lead dispatches only tasks
whose per-task `touches_files` do not overlap within a wave, up to `max_parallel_tasks`
(default **4**; optional user-owned `docs/build/build_config.json`), and is the sole
writer of task status. This is an architecture-level constraint on the task graph:

- `ui/chart_panel.py` is touched by **R1, R2, Phase 1, and Phase 3** → **serial chain**
  (they must not share a wave).
- `ui/main_window.py` is touched by **R1** (status-bar connection) and **Phase 4**
  (watchlist wiring) → serial with each other.
- `ui/chart_mouse_router.py` is touched by **R1 only**.
- `ui/drawing_overlay.py` is touched by **Phase 2** and the Phase-4 mode-reset
  amendment → serial.
- `ui/candlestick_item.py` (Phase 1, D7) may run in parallel with `chart_panel`-based
  tasks; Phase-2 new dialog files may run in parallel; Phase-4
  `watchlist_panel.py`/`QSettings` work may run in parallel (its `main_window.py` part
  serializes with R1).
- Verification tasks touching the same test file must be serialized per file.

This constraint was honoured through Build: tasks **T1–T36** all completed `done`, with
no two overlapping-file tasks in the same wave.

## Post-document rework (ESC-013…ESC-021)
After the 2026-09-27 revision was written, Build executed a second rework wave; this
as-built description folds it in. Each item refines D6/D9/D11
(or their tests) **without altering any decision’s intent**:

| Rework | Nature | Where it lands | Doc basis |
|---|---|---|---|
| ESC-013 (T32) | D6 dense-view clamp ordering — apply `vb.setRange(...)` before generating the candle picture | `ui/chart_panel.py:_refresh_candles`; `ui/candlestick_item.py` clamp | D6 ordering contract (audit `D-12`) |
| ESC-014 (T33) | D11 stacking by **measured bbox height**, `offset = max(15, height, last_height)` | `ui/drawing_overlay.py:_update_inner_labels` | D11 (audit `D-7`) |
| ESC-015 (T34) | test expectation update only (volume log) | `tests/test_volume_log.py` | n/a |
| ESC-016 (T35) | test assertions retargeted to the lane contract | `tests/test_chart_crosshair.py`, `tests/test_crosshair_chip_bounds.py` | D2/Q33 |
| ESC-017 (T36) | `draw_combo` sync on router tool-clear (TR-4/TR-17) via `mode_changed("cursor")` | `ui/main_window.py` | “Component relationships” (audit `D-14`) |
| ESC-020 (T13 rework) | D9 volume-width ordering — derive `w_vol` from the final view range after `setRange` | `ui/chart_panel.py:_refresh_candles` | D9 ordering contract (audit `D-12`) |
| ESC-021 (T13 rework) | D9 test measures the rendered body | `tests/test_volume_width.py` | n/a |

ESC-015/ESC-016/ESC-021 changed tests/docs only; ESC-013/ESC-014/ESC-017/ESC-020
changed behaviour but only to enforce an existing decision’s intent, so **no
architectural decision changed**. Full offscreen suite: **383 passed**.

## Architecture Risks
| Risk | Severity | Mitigation |
|---|---|---|
| Watchlist 50% cap crowds the chart on small screens; persisted width may exceed a new window size | L | Clamp to `min(floor(0.50×W), W−400)`, `min 150px`, `chart ≥400px`, on restore and `resizeEvent`; floating unconstrained |
| ESC-002 regression: switching to an enum changes routing order for an existing tested path | M | The five existing router tests are the regression fence; dispatch table preserves alarm-first in `IDLE`; RC-3 property-setter reconciliation makes `test_drawing_tool_blocks_alarm_press` pass verbatim |
| RC-3 mechanism mis-implemented (mode not derived on direct wiring) | M | Property setters + `_reconcile_mode_from_overlays()`; `test_reconcile_mode_from_wired_overlays` + the five preserved tests |
| `AC-D3.9` refusal accidentally cancels the pending alarm placement or enters `ZOOMING` | M | TR-9 explicit side effects; `test_magnifier_refused_during_alarm_placement` asserts mode unchanged and placement intact |
| D2 dock-open visibility regresses despite the lane move | M | `AC-D2.1` + edge case; Build test + **independent Code Reviewer verification** — performed and closed via ESC-016/T35 (A25) |
| D2 chip clipped at narrow widths / long prices in the axis lane | L | `AC-D2.1` edge cases; PA-R6 right-edge guard; `test_crosshair_chip_renders_in_axis_lane` |
| D8 nice-max just above a boundary leaves extra headroom | L | `max_vol×1.1` before rounding; tight coverage `<= 2`; 3–5 ticks |
| D11 label overlap when many zones share a price | L | Measured-bbox offset `max(15 px, bbox height, previous bbox height)` (ESC-014, audit `D-7`); `AC-D11.4` label-vs-label (chip lane-separated); offscreen test at dense zones |
| D12/D15 dialog duplication (zone vs horizontal) | L | Two dedicated dialogs for AC isolation, or one parameterized dialog — either satisfies |
| D6 ratio inverts at extreme density if the body minimum applies before layout | M | Clamp against live `ViewBox px_per_sec`; generate-after-`setRange` ordering contract (ESC-013); dense-1-min test |
| D6/D9 geometry computed **before** `vb.setRange` leaves dense bars sub-pixel on a first load | L | `_refresh_candles` applies the range first, then generates the candle picture and derives `w_vol` (ESC-013/ESC-020, audit `D-12`); `tests/test_volume_width.py` measures the rendered body |
| D2 chip lane width not reserved up-front would grow the axis mid-hover, leaving the pill on a stale lane | L | `_reserve_price_tag_lane()` probes `PRICE_TAG_LANE_SAMPLE` up-front; `_price_lane_width` folded into the zoom-cluster offset (audit `D-13`) |
| D4 stylesheet specificity / left-of-axis clamp on very narrow windows | L | Scope override to `btn_magnify`; `x>=8`, `y<=15`; geometry test at 500px |
| Volume log `0→1.0` (D5) misreads as data | L | D8 reverted to linear `0` lower bound; D5 decision superseded — **resolved in Build** |
| Nice-number generator changes tick values of already-built Batch-4 behaviour | L | Old list kept as fixture (all members of the pinned family); only the `(0)` expectation updated (`AC-D8.4`, A24) |
| Only-widen ceiling leaves headroom after the live bar shrinks on a partial/out-of-order tick | L | `AC-D8.6` satisfied (no clipping); refreshed O(N) on the next load/new bar |
| Router and `ChartPanel` both writing mode state (drift) | M | Router is the single writer of `_active_mode`; `ChartPanel` methods are adapters; `test_router_mode_is_mutually_exclusive` |
| `chart_panel.py` touched by R1/R2/Phase 1/Phase 3 → serial build chain | L (schedule) | `touches_files` populated per the constraint above; Lead serializes overlapping waves |
| DST / UTC-vs-ET band misplacement | M | `ZoneInfo` boundaries plus DST tests |
| `data/db.py` duplicate `_init_schema` (latent hygiene debt) | — **resolved** | T26/ESC-001 deduplicated it: `_init_schema` is defined once (`data/db.py:14–111`), guarded by `tests/test_db_schema.py` (audit `D-6`) |
| Drawing `InfiniteLine` use-after-free during drag (fixed 2026-09-19) | L (was H) | In-place mutation + defensive `scene.dragItem` clear; 26 drawing tests; suite green |
| `fibonacci` rebuild on level-count change still calls `_restore_drawing_style` mid-drag | L | Guarded by defensive `dragItem` clear; rebuild only when count changes |
