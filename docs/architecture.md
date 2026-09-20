# Architecture — NDThinkChart Stabilization (Batch 1–2 built; Batch 3–9 D7–D15 planned)

## Summary
A stabilization change-set against an existing PyQt6 + pyqtgraph + official `ibapi`
desktop trading terminal. **Built:** Batch 1 (D1–D3 — session shading, crosshair
chip, zoom controls/magnifier), Batch 2 (D4–D6 — zoom label/position, volume log,
pixel-stable wick), and a post-build `DrawingOverlay` drag-lifecycle stability fix.
**Planned:** Batch 3–9 (D7–D15) — a 35% inter-candle gap, a **linear** volume axis
with dynamic nice ticks and price-coloured bars, volume bars that track the price
body width, a volume-panel hide/show toggle, inner-right drawing price labels, two
double-click drawing settings popups (zone `Rectangle`, horizontal line), and a
resizable/persistent watchlist with double-click-to-load. Persistence, broker I/O,
and the live-order path remain untouched — no new tables, no new IBKR calls, no new
external integrations.

## Tech Stack Decisions
| Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|
| Language / UI stack | Unchanged: Python 3.11+, PyQt6, pyqtgraph | Stabilization run; changing the stack is a stated non-goal | New charting library or embedded web view |
| Session boundary math (Batch 1) | Pure `services/session_service.py` using `ZoneInfo("America/New_York")` | Qt-free, unit-testable, DST-correct | Inline math in `ChartPanel` (untestable); `pandas_market_calendars` (holidays unneeded) |
| Session shading primitive (Batch 1) | `pg.LinearRegionItem(orientation=Vertical, movable=False)` per band, z below candles | Full-height, no price range needed, one item per band | `StudyOverlay.add_band` (needs bottom/top); `fillBetween` (sentinel y); 2×`InfiniteLine` per band |
| Zoom controls / magnifier (Batch 1) | `ui/chart_controls.py` (signal-emitting `QFrame`) + `ui/zoom_overlay.py` with highest `ChartMouseRouter` precedence while active | Logic-free widget, testable; fits existing overlay-precedence pattern | Main-toolbar buttons; pyqtgraph ViewBox zoom modes (no persistent tool state) |
| Crosshair chip (Batch 1) | Right-align `TextItem` (`anchor=(1,0.5)`) inside the plot's right edge | Root-cause fix, minimal change | Widen the axis (dock still adjacent) |
| **D4 zoom label/position** | `-`/`+`/`Reset` 14px/700, `⌕` 21px/700 (14×1.5), button 28×24; cluster `x = panel.width - ctrl.width - axis_width - 12` (fallback 50, `x>=8`), `y=10` | `Reset` was legible at 14px but `⌕` looked small; a fixed margin still overlapped the axis, so position relative to the dynamic axis width keeps the outline inside | One size for all four; larger buttons; fixed 28px margin (clips) |
| **D5 volume log → superseded by D8** | D5 shipped volume log Y (`setLogMode('y',True)`, `0→1.0`, `yRange=(1, max*1.1)`); **D8 supersedes it** | D5 was confirmed Q17 but the new screenshot (D8/Q20) rejects log and negatives | n/a — D8 is the current decision |
| **D6 wick rendering** | Wick: body-coloured `QPen`, `widthF=1.0`, **`setCosmetic(True)`**, `FlatCap`, drawn **before** the body; body cosmetic 1px outline with data half-width **clamped to ≥4-device-px** via `ViewBox px_per_sec` | `CandlestickItem` paints into a `QPicture` in data coordinates; non-cosmetic pens scale with the ViewBox and go sub-pixel at high density. Cosmetic pens are device-pixel stable | Non-cosmetic pens with larger `w` (no pixel ratio); pixel-space drawing without `QPicture` (more invasive, loses caching) |
| **D7 inter-candle gap** | Body half-width `w = median_diff * 0.325` (gap 35%), keep `0.25` single-bar fallback, keep D6 ≥4-device-px minimum; `xRange` padding `-2*bar_w / +8*bar_w` unchanged | Q19 confirmed “go 35% gap for now” as a modest, testable increase from today’s `0.40` (20% gap); only inter-candle gap grows (~75% more gap) | `0.30` (40% gap, airier); widen `xRange` (adds outer framing, not gap) |
| **D8 volume scale (revises D5)** | Volume `ViewBox` **linear Y** (`setLogMode(y=False)`), `yRange=(0, nice_max)` where `nice_max = ceil(max_vol*1.1/step)*step` with next nice in `[10k,50k,100k,250k,500k,750k,1.0M,1.5M,2.0M,2.5M,5M,10M]`, `y0=0`, ticks `500.0K / 1.0M`, no negatives; bars **price-coloured** (`#34d399` / `#f87171` by `close>=open`) | Current log gives negative ticks and hides the desired `500.0K–2.5M` look; the reference is linear with a dynamic nice max and price-coloured bars (Q20). `0` lower bound matches “volume cannot go below zero” | Keep log with `0→1.0` floor (rejected); add a log/linear toggle (more UI than requested) |
| **D9 volume bar width** | `volume_bars.width = w*2` (same `w` as price post-D7 = 65% of `median_diff`), `y0=0`, X stays `setXLink`ed | Fixed `width=0.6` drifts from the price 35% gap; sharing `w` guarantees vertical alignment including the dense 4px minimum | Fixed `0.6`; `0.9×price` (subtly narrower, not requested) |
| **D10 volume toggle** | **Top left of the volume panel** (bottom-left of the price chart) — checkable `QToolButton` (eye icon) in the volume panel header, default **visible**, toggles `volume_plot.setVisible()` and rebalances the `QSplitter` so `price_plot` expands; **not persisted** | Q22 confirmed “Top left of the volume panel, which is the bottom left of the price chart panel”; not persisted was the proposal | Toolbar `Volume` button; `QSettings` persistence (future); splitter-handle-only hiding |
| **D11 drawing price labels** | Inside-plot `TextItem` at `x = view_rect.right() - 4`, `anchor=(1,0.5)`, `Z=10`, colour = drawing colour; one per price (zone top+bottom, trendline/Fib per level); stacked with a small vertical offset when nearby; added to the price plot scene | Q23 confirmed inner-right inside the plot (reference 757–764 labels); crosshair chip precedent | Axis-area labels (clipped by dock); left-side labels |
| **D12 zone settings popup** | Modal `Rectangle` dialog (pencil + `X`), 4 tabs **Style / Text / Coordinates / Visibility**; **Style: `Extend` omitted** (zone always both sides), `Border` + `Middle line` (unchecked) + `Background` (checked) remain; `#1/#2 (price, bar)` steppers; 8-row Visibility timeframes | Q24 “Extend is omitted” confirmed; the reference’s `Extend right` is the only control to drop | Keep `Extend right` (contradicts user); `Extend both` disabled |
| **D15 horizontal line popup** | Modal `Horizontal line` dialog, same 4-tab pattern; **Style:** `Line` (white solid); **Text:** `12`, `B`/`I`, `Add text`, `Top`/`Right`; **Coordinates:** single `#1 (price)` stepper; Visibility = same 8 rows as zone | Q30 confirmed — four screenshots are the spec; single coordinate is the only structural difference from the zone | Reuse the zone dialog with hidden `#2` (shows an irrelevant field) |
| **D13 watchlist width** | Docked Watchlist freely draggable to `min(floor(0.50×W), W−400)` with min `150px` and chart min `400px`; width persisted as an `int` pixel value via **`QSettings` `watchlist/width`** (default ~220px), clamped on restore and window resize; floating geometry unconstrained | Q25/Q26 confirmed the 50% cap and persistence; `QSettings` avoids a `watchlist` table migration and is per-user | Store width in SQLite (migration cost); no persistence (user asked for it) |
| **D14 watchlist double-click** | `cellDoubleClicked` → set `symbol_input` to the row symbol (uppercased) → call the existing `MainWindow.load_chart()` with current `tf_combo`/`ext_hours_btn`; no-op if same `_current_symbol` (case-insensitive) or IBKR disconnected (`status_bar` message); header/empty area no-op | Q27–Q29 confirmed “identical to Load Chart” semantics with no-ops | A separate load path (duplicates logic); single-click load (loses selection) |
| Drawing drag stability (runtime fix 2026-09-19) | `DrawingOverlay._apply_drag` mutates items **in place**; `_remove_items`/`_clear_all_items` defensively clear `GraphicsScene.dragItem` before `removeItem`; `fibonacci` rebuilds only on level-count change | Remove+rebuild mid-drag left `dragItem` dangling → `sendDragEvent` → `InfiniteLine.mouseDragEvent` on a deleted C++ object → `RuntimeError`. In-place mutation preserves C++ identity | Suppress the warning (hides bug); fork pyqtgraph (maintenance); retain refs (leaks) |
| Testing | pytest + pytest-qt, offscreen, no live TWS | Repo standard; confirmed Q8/Q9 | Manual-only (rejected) |

## System Components

### Existing layers (unchanged)
- **`config/`** — `settings` (env), `paths` (bundle-aware DB/resource paths), `theme.qss`.
- **`data/`** — `models`, `db` (SQLite singleton), `bar_cache`, `bar_aggregator`, `alarm_store`, `drawing_store`, `study_store`.
- **`services/`** (pure, Qt-free, tested) — `indicator_service`, `gap_vix_service`, `ict_service`, `drawing_service`, `alarm_service`, `sound_service`, `strategy_detection`, plus Batch-1 `session_service`.
- **`ibkr/`** — `client`, `bridge` (Qt signals), `id_manager`, `pacing`, `contracts`, `market_data`, `realtime_bars`, `market_depth`, `order_book`, `orders`, `account`, `subscription_manager`.
- **`ui/`** — `main_window` (orchestrator), `chart_panel`, `candlestick_item`, `chart_mouse_router`, `drawing_overlay`, `alarm_overlay`, `studies_dialog`, `active_trader_panel`, `active_portfolio_panel`, `watchlist_panel`, `overlays/{base,gap_overlay,vix_overlay,ict_overlay}`.

### Built (Batch 1, Batch 2, runtime fix)
- **`services/session_service.py`** — `session_bands(bars, timeframe)`; ET pre/post intervals (DST-aware), clipped to the loaded range; `[]` for `1 day`.
- **`ui/overlays/session_overlay.py`** — `SessionOverlay(StudyOverlay)`; one vertical region per band, owned via `clear()`.
- **`ui/chart_controls.py`** — `ChartControls(QFrame)`; emits `zoom_in`, `zoom_out`, `magnify_toggled(bool)`, `reset`; stylesheet `-`/`+`/`Reset` 14px/700, `⌕` 21px/700.
- **`ui/zoom_overlay.py`** — rubber-band area zoom; sets both axes on release; cancels on `Esc`/right-click; stays active.
- **`ui/chart_panel.py`** — `_position_zoom_controls()` left-of-axis; crosshair chip `anchor=(1,0.5)`; volume `ViewBox` currently log (to be superseded by D8).
- **`ui/candlestick_item.py`** — cosmetic body-coloured wick behind the body; body cosmetic outline + device-pixel minimum; `w = median_diff*0.4` (to become `0.325` in D7).
- **`ui/drawing_overlay.py`** — in-place drag mutation + defensive `GraphicsScene.dragItem` clearing (runtime fix 2026-09-19).

### Planned changes (Batch 3–9: D7–D15)
- **`ui/candlestick_item.py`** — `w` factor `0.40 → 0.325` (D7); single-bar `0.25` fallback and D6 4px minimum unchanged.
- **`ui/chart_panel.py`** — volume `BarGraphItem` `width = w*2` and `y0=0` (D9); volume `ViewBox` linear `yRange=(0, nice_max)`, price-coloured brushes, `500.0K / 1.0M` tick formatter (D8); volume toggle control + splitter handling (D10); expose `w`/`nice_max` for reuse.
- **`ui/drawing_overlay.py`** — `mouseDoubleClickEvent` hit-test → open the matching settings dialog (D12 zone, D15 horizontal); inner-right `TextItem` labels (`view_rect.right()-4`, `anchor=(1,0.5)`, stacking) for all drawing kinds (D11).
- **New dialogs** — `ui/zone_settings_dialog.py` (`Rectangle`, 4 tabs, `Extend` omitted) and `ui/horizontal_line_settings_dialog.py` (`Horizontal line`, 4 tabs, single `#1 (price)`). Shared helpers for colour swatches, numeric steppers, and the 8-row Visibility grid; a single parameterized `ui/drawing_settings_dialog.py` is an acceptable alternative.
- **`ui/watchlist_panel.py` + `ui/main_window.py`** — splitter min/max `[150, min(floor(0.50×W), W−400)]`, `QSettings watchlist/width` persistence + restore clamp, and `cellDoubleClicked` → `load_chart()` with same-symbol/disconnected no-ops (D13/D14).

### Component relationships
`MainWindow` owns `ChartPanel`, the Watchlist dock, and the Ext-Hours state.
`ChartPanel` owns the price plot, `CandlestickItem`, `SessionOverlay`, `ZoomOverlay`,
the child `ChartControls`, and the volume `ViewBox` (plus the D10 toggle and D11
labels). `ChartMouseRouter` mediates ViewBox gestures between `ZoomOverlay`,
`AlarmOverlay`, and `DrawingOverlay`. `DrawingOverlay` owns its items, opens the
D12/D15 dialogs, and renders D11 labels. `WatchlistPanel` emits a double-click that
`MainWindow` maps to the existing `load_chart()` path. `reDrawings` payloads persist
through `DrawingStore`.

## Data Model
**No schema changes.** D7–D11 are ephemeral view state (candle width, volume scale,
volume visibility, label geometry). D12/D15 read/write the existing `drawings` table
via `DrawingStore` (`payload` JSON: horizontal `{"y": …}`, zone
`{"x1","x2","y1","y2"}`) with `services/drawing_service.normalize_payload` still
validating. D13 persists a single `int` pixel width via `QSettings` (not SQLite).
The existing models (`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`,
`TradeGroup`, `OrderBookLevel`, `UserOrder`) and tables (`bars`, `watchlist`,
`alarms`, `zones`, `drawing_groups`, `drawings`, `studies`, `positions`,
`trade_groups`, `position_group_map`) are unchanged.

*Observation (out of scope):* `data/db.py` defines `_init_schema` twice (lines
14–111 and 113–210); the second shadows the first. Flagged as latent hygiene debt —
no behavior change in this run.

## Integration Points
- **IBKR historical / RT data** — no new calls. D13/D14 reuse the existing
  `MainWindow.load_chart()` sequence (cancel prior RT `reqId` → `BarCache` → delta
  `reqHistoricalData` → RT `subscribe`); D8/D9 read `Bar.volume`/`close`/`open` only.
- **SQLite** — D12/D15 use `DrawingStore.update_drawing`; no schema change.
- **Qt signal bus / QSettings** — D10 toggle `toggled(bool) → volume_plot.setVisible`;
  D13 uses `QSettings("watchlist/width")`; `IBBridge` unchanged.
- **pyqtgraph GraphicsScene** — `DrawingOverlay` touches `scene.dragItem` only via
  defensive nulling before `removeItem` (runtime fix). No fork.

## Non-Functional Approach
- **Correctness (chart geometry):** D7’s 35% gap is proportional (`0.325× median_diff`)
  with the D6 4px minimum so dense 1-min stays positive; D9 shares the same `w`;
  D8 ticks are `0`-based linear with nice rounding (3–5 ticks) and no negatives.
- **Correctness (drawings):** D11 labels are `anchor=(1,0.5)` inside
  `view_rect.right()-4`, repositioned on `sigRangeChanged`, so they are never clipped
  by the right axis/dock; D12/D15 dialogs pre-fill from the drawing payload and
  persist via `DrawingStore`.
- **Correctness (watchlist):** D13 clamps `[150, min(floor(0.50×W), W−400)]` on
  restore and resize; D14 mirrors `load_chart` exactly and no-ops on same
  symbol/disconnected.
- **Performance:** `w` and `nice_max` are O(N) per data load over bars (not per
  intra-bar tick); dialogs are created on demand; labels are bounded by drawing count.
- **High-DPI:** D6 cosmetic pens and D11 label placement are device-pixel aware.
- **Security:** live-order path untouched; Q9 holds — no automated test connects to
  live TWS or transmits an order.
- **Scalability:** overlay/label counts bound to drawing count; volume/price item
  counts bound to bar count; no per-frame allocation added.

## Architecture Risks
| Risk | Severity | Mitigation |
|---|---|---|
| Watchlist 50% cap crowds the chart on small screens; persisted width may exceed a new window size | L | Clamp to `min(floor(0.50×W), W−400)`, `min 150px`, `chart ≥400px`, on restore and `resizeEvent`; floating unconstrained |
| D8 nice-max just above a boundary (e.g., 1.05M → 1.5M) leaves extra headroom | L | `max_vol×1.1` before rounding; 3–5 ticks |
| D11 label overlap when many zones share a price | L | Small vertical offset per overlapping label; offscreen test at dense zones |
| D12/D15 dialog duplication (zone vs horizontal) | L | Two dedicated dialogs for AC isolation, or one parameterized dialog — either satisfies |
| D6 ratio inverts at extreme density if the body minimum applies before layout | M | Clamp against live `ViewBox px_per_sec`; dense-1-min test |
| D4 stylesheet specificity / left-of-axis clamp on very narrow windows | L | Scope override to `btn_magnify`; `x>=8`, `y<=15`; geometry test at 500px |
| Volume log `0→1.0` (D5) misreads as data until D8 lands | L | D8 reverts to linear `0` lower bound; D5 decision superseded |
| Magnifier gesture conflicts with drawing/alarm/pan | H | Zoom top precedence only while active; router precedence tests |
| DST / UTC-vs-ET band misplacement | M | `ZoneInfo` boundaries plus DST tests |
| `data/db.py` duplicate `_init_schema` | L | Flagged only; no change in this run |
| Drawing `InfiniteLine` use-after-free during drag (fixed 2026-09-19) | L (was H) | In-place mutation + defensive `scene.dragItem` clear; 26 drawing tests; 311 suite green |
| `fibonacci` rebuild on level-count change still calls `_restore_drawing_style` mid-drag | L | Guarded by defensive `dragItem` clear; rebuild only when count changes |
