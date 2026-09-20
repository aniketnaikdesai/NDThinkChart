# NDThinkChart — Requirements

> Status: READY_FOR_PLAN — Batch 1 built; Batches 2–9 (D4–D15) clarified 2026-09-19/20 and ready for the next plan pass. See Defect Register D4–D15 and open_questions Q15–Q30.

## Problem Statement
NDThinkChart is a feature-complete desktop trading terminal (PyQt6 + pyqtgraph +
official `ibapi`, live TWS port 7496) built through Phases 1–10 of
`PENDING_IMPLEMENTATION_PLAN.md`. It is now in a **feedback-driven stabilization
phase**: the user reviewed the running app and reported functional issues and UI
bugs, which this run must triage and fix. Batch 1 (D1–D3) was the complete list
for the first stabilization run and is clarified and built. Batch 2 (D4–D6) is now
fully clarified from post-build UI feedback 2026-09-19 (zoom label size with
magnifier +50% and position fine — Q15/Q16 — volume log lower bound 1.0 — Q17 —
and candlestick wick 1px vs body ≥4× — Q18). Batch 3 (D7 35% gap) is a time-axis
spacing refinement confirmed 2026-09-19. Batch 4 (D8) is a volume-panel revision
(linear, no negatives, dynamic nice ticks, price-coloured) confirmed 2026-09-19.
Batch 5 (D9 volume spacing follow and D10 volume show/hide at top left of volume
panel) is now clarified 2026-09-19 (Q21 correct, Q22 top left). Batch 6 (D11
drawing price labels on inner right side) is clarified 2026-09-19 (Q23 correct).
Batch 7 (D12) zone double-click settings popup with 4 tabs is clarified 2026-09-19
(Q24 Extend omitted). Batch 8 (D13 watchlist resizable to 50% with persistence +
D14 double-click row to load chart) clarified 2026-09-20 per Q25–Q29. Batch 9
(D15) horizontal line double-click settings popup with 4 tabs is clarified 2026-09-20 per Q30.

## Goals
- Collect and triage the user's reported functional issues and UI bugs.
- Fix each reported defect such that its per-task **test condition** passes.
- Keep the existing behavior and test suite intact — no regressions.
- Keep the live-order path safe while it is gated at the TWS API layer.

## Non-Goals
- Net-new feature development (this is bug-fix/UI repair only, unless a fix
  inherently requires small supporting work).
- Visual redesign / restyling beyond correcting the reported UI defects.
- The GUI test suite spec in `test_gui.md` as a standalone deliverable, and
  "Phase 12" combo/BAG multi-leg order placement — both explicitly out of scope
  for this run (from Q2).
- Introducing a paper/simulated trading mode, or changing the live-only port 7496
  model.
- Changing the tech stack.

## Constraints

### Observed from repository (confirmed, Q5)
- **Language/runtime:** Python 3.11+ (`.venv`), macOS Apple Silicon (arm64).
- **UI:** PyQt6 (`PyQt6>=6.6`), pyqtgraph (`>=0.13`) for charting.
- **Broker:** official `ibapi` (`>=9.81`), Interactive Brokers TWS.
- **Numerics:** numpy (`>=1.26`).
- **Persistence:** SQLite (dev: `./charting_app.sqlite3`; bundled:
  `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`).
- **Connectivity:** live TWS port **7496 only — no paper mode**.
- **Packaging:** PyInstaller windowed `.app`, bundle id `com.ndthinkchart.app`.
- **Tests:** pytest + pytest-qt, run offscreen (`QT_QPA_PLATFORM=offscreen`),
  no live TWS required by default.

### Confirmed for this run
- **Live-order path may be touched**, but live orders are currently gated at the
  TWS API layer by the user, so no order can actually transmit while this work
  proceeds (Q4).
- **Definition of done:** all test conditions pass; test conditions are defined
  and updated per task as defects are triaged (Q3).
- **Regression-test policy (Q8, confirmed):** every fix ships with a check that
  fails before the fix and passes after, runnable offscreen
  (`QT_QPA_PLATFORM=offscreen`, no live TWS). The pre-existing suite must stay green.
- **Live-order test safety (Q9, confirmed):** no automated test may connect to live
  TWS or transmit an order. Order-path changes are verified by unit-testing the
  generated order fields; any live check is a manual user-run step.
- **Feedback cadence (Q7, confirmed):** defects arrive one message at a time; the
  Analyst may ask follow-ups. The full requirements→build flow may repeat until the
  user is satisfied.

### Business / regulatory / timeline
- None stated. No deadline or compliance driver provided.

## Glossary
| Term | Meaning in this repo |
|---|---|
| Defect | A reported functional issue or UI bug to be fixed in this run. |
| Test condition | The per-task pass/fail check for a defect fix; must be independently testable (Q3). |
| Study | A technical indicator/overlay (SMA, EMA, VWAP, Bollinger, RSI, MACD, ICT, RTH gaps, VIX SD). |
| Drawing | A user chart annotation (trendline, horizontal, zone, fibonacci, measure), optionally in a group. |
| DOM / Ladder | Level II market-depth ladder with click-to-trade rows. |
| Live-order path | Code that builds/transmits orders via `ibkr/orders.py` + `IBApiClient`; gated in TWS for now. |

## User Journeys

### Journey 1 — Defect report → fix → verification (operational journey)
- **Preconditions:** App is runnable; user has observed a functional issue or UI
  bug in the application.
- **Steps:**
  1. User reports the defect (screen/area, steps, expected vs actual).
  2. Requirements Analyst records it in the Defect Register below with a testable
     acceptance criterion (the test condition).
  3. Plan/Task Manager/Build implement the fix.
  4. The test condition is executed; the full existing suite is re-run.
- **Postconditions:** Defect resolved, its test condition passes, and no existing
  test regresses.
- **Edge Cases:**
  - Report is not reproducible (missing environment/symbol/timeframe) → route back
    to the user for detail (see Q7) before accepting as a defect.
  - Report actually describes a new feature rather than a bug → reclassify to
    `feature_suggestions.md`, do not treat as in-scope.
  - Reported fix conflicts with an existing test's expected behavior → resolve
    explicitly; do not silently change the test to make it pass.

### Journey 2 — D1: distinguish sessions at a glance
- **Preconditions:** A symbol is loaded; Ext Hours is ON; timeframe is intraday.
- **Steps:** 1) Load chart. 2) Observe the background bands behind the candles.
- **Postconditions:** Pre-market appears orange @10%, post-market blue @10%; RTH and
  overnight are unshaded, so session context is readable without a tooltip.
- **Edge Cases:** On a `1 day` chart no bands appear; toggling Ext Hours OFF removes
  them; DST days keep boundaries at ET local time.

### Journey 3 — D2: read the exact price under the crosshair
- **Preconditions:** A symbol is loaded; the Active Trader and/or Portfolio dock is
  open on the right.
- **Steps:** 1) Hover the cursor over the price plot. 2) Read the price chip.
- **Postconditions:** The full price, including all decimal places, is visible and
  never overlapped by the axis or right-hand dock.
- **Edge Cases:** A long price (`123,456.78`) does not bleed under the dock; hovering
  at the top/bottom edge keeps the chip in view; the chip is hidden when the cursor
  leaves the plot.

### Journey 4 — D3: zoom into a chosen area
- **Preconditions:** A symbol is loaded.
- **Steps:** 1) Click the magnifier. 2) Drag a rectangle over the region of
  interest. 3) Release. 4) (Optionally) press `Esc` on a later drag; click Reset.
- **Postconditions:** On release the selected rectangle expands to fill the chart
  (both axes); magnifier stays active for another selection; Reset restores the
  default framing.
- **Edge Cases:** A near-zero-area drag is ignored; a drag starting outside the plot
  does nothing; with no bars loaded the controls are disabled; `Esc`/right-click
  cancels without changing the view.

### Journey 5 — D4: see and use the zoom controls
- **Preconditions:** A symbol is loaded.
- **Steps:** 1) Observe the top-right cluster. 2) Read the `-` / `+` / `⌕` / `Reset`
  labels. 3) Resize the window.
- **Postconditions:** Glyphs are legibly 14px/700; the cluster’s right edge is left of
  the price axis and never clipped, regardless of window size.
- **Edge Cases:** Narrow window or wide axis (5-digit prices) keeps the cluster
  inside with `x >= 8`; magnifier checkability unchanged.

### Journey 6 — D5: read volume distribution
- **Preconditions:** A symbol is loaded with mixed small and large volumes (e.g., a
  spike at 16:00).
- **Steps:** 1) Observe the volume histogram. 2) Note small-volume bars vs the
  spike.
- **Postconditions:** Small volumes are visibly distinct; Y is logarithmic and
  ticked at 1e6/1e7.
- **Edge Cases:** Zero-volume bars appear as a 1-unit minimal tick, not a gap;
  max-volume spike does not collapse the rest; X remains linked to price.

### Journey 7 — D6: distinguish wick from body
- **Preconditions:** A symbol is loaded with candles that have shadows.
- **Steps:** 1) Observe any candle with a high/low shadow. 2) Compare wick vs body.
- **Postconditions:** The wick is a thin 1px line distinct from the wider body and
  extends beyond the body when a shadow exists; direction colour is consistent.
- **Edge Cases:** Dense 1-min chart with hundreds of candles keeps wick thin
  (body narrows but wick stays 1px); Doji `open==close` still shows wick behind
  body; High-DPI does not merge wick and body.

### Journey 8 — D7: see spacing between candles
- **Preconditions:** A symbol is loaded on an intraday timeframe (e.g., 5-min).
- **Steps:** 1) Observe the gap between adjacent candle bodies at default zoom.
- **Postconditions:** The gap is visibly larger than the current 20% of spacing
  (about 35% of spacing), so individual candles are distinct.
- **Edge Cases:** Dense 1-min view keeps a positive gap even when the 4px body
  minimum applies; single-bar fallback unchanged; studies and session bands
  continue to frame correctly.

### Journey 9 — D8: read volume at a glance
- **Preconditions:** A symbol is loaded with varied volumes (e.g., spikes and quiet periods).
- **Steps:** 1) Observe the volume histogram’s Y axis. 2) Note the bar colours vs the price candles above.
- **Postconditions:** Y is linear starting at `0` with no negatives; the max is a nice value like `500.0K / 1.0M / 2.5M` that contains the tallest bar; bars are green when the price candle was up and red when down.
- **Edge Cases:** All-zero volumes show `0–10k` with minimal bars; a max just below a nice boundary rounds up; small and large volumes remain distinguishable.

### Journey 10 — D9: see aligned price and volume spacing
- **Preconditions:** A symbol is loaded on an intraday timeframe with both price and volume visible.
- **Steps:** 1) Observe the gap between price bodies. 2) Observe the gap between volume bars at the same x positions.
- **Postconditions:** The inter-bar gaps are identical (volume width `w*2` matches price body width, 35% gap), so price and volume bars are vertically aligned.
- **Edge Cases:** Dense 1-min view keeps gaps aligned even when the 4px minimum applies; single-bar fallback aligns; Line/Area modes still align volume.

### Journey 11 — D10: show/hide volume to reclaim space
- **Preconditions:** App is running with a loaded chart; the volume panel is visible.
- **Steps:** 1) Toggle the volume control. 2) Observe the price plot height. 3) Toggle again.
- **Postconditions:** Toggling hides the volume plot and its axis, the price plot expands; toggling again shows it; the app does not error with no bars.
- **Edge Cases:** Oscillator visibility is independent; splitter restores correctly; hidden state resets to visible on restart (no persistence in this proposal).

### Journey 12 — D11: read drawing price on the inner right side
- **Preconditions:** A symbol is loaded and a drawing (horizontal line or zone) exists.
- **Steps:** 1) Observe the right edge of the price plot interior.
- **Postconditions:** The drawing’s price(s) are visible as labels inside the plot near the right edge, not on the axis.
- **Edge Cases:** Multiple zones at nearby prices stack without full overlap; zoom/pan keeps labels at the right edge and at the correct price; no drawing → no label.

### Journey 13 — D12: edit a zone via double-click
- **Preconditions:** A zone (rectangle) drawing exists on the chart.
- **Steps:** 1) Double-click the zone body. 2) Observe the Zone Settings popup. 3) Switch between Style/Text/Coordinates/Visibility tabs. 4) Change a value and apply.
- **Postconditions:** Double-click opens the `Rectangle` popup with four tabs; Extend is not shown (zone always extends both sides); changes are applied to the zone and re-render.
- **Edge Cases:** Double-click on a non-zone drawing does not open the zone popup; double-click with no selection does nothing; Cancel/X closes without change.

### Journey 14 — D13: resize watchlist panel to see more symbols/columns
- **Preconditions:** App is running; Watchlist dock is docked on the left; window is at default 1400×900.
- **Steps:** 1) Hover over the vertical splitter handle between Watchlist and chart. 2) Drag right to widen.
- **Postconditions:** Watchlist width grows, chart narrows, handle remains draggable across `[150, floor(0.50×W)]` (and `W−400`), clamped on window resize.
- **Edge Cases:** At max 50% the handle stops; at min 150px it stops; floating Watchlist is unconstrained.

### Journey 15 — D14: double-click watchlist row to load chart
- **Preconditions:** Watchlist has symbols; IBKR may be connected or not; current chart may be `SPY`.
- **Steps:** 1) Double-click any cell in the `AAPL` row.
- **Postconditions:** If connected and `AAPL != SPY`, `symbol_input` becomes `AAPL` and chart loads for `AAPL` with current timeframe/ext-hours; if same symbol or disconnected, no-op with status message.
- **Edge Cases:** Double-click header/empty area → no-op; single-click only selects; same-symbol → no flicker/new reqId.

### Journey 16 — D15: edit a horizontal line via double-click
- **Preconditions:** A horizontal line drawing exists on the chart.
- **Steps:** 1) Double-click the line. 2) Observe the Horizontal line popup. 3) Switch tabs. 4) Change price/text and apply.
- **Postconditions:** Double-click opens `Horizontal line` popup with four tabs and current price pre-filled; changes update the line.
- **Edge Cases:** Double-click on a zone/non-horizontal does not open this popup; Cancel discards; single line coordinate only.

## Acceptance Criteria (feature-level)

### Global (applies to every defect in this run)
- **Given** the repository at its current state,
  **when** all registered defect fixes are applied,
  **then** every defect's per-task test condition passes **and** the pre-existing
  test suite remains green.
- **Given** a change touching the live-order path,
  **when** tests are run,
  **then** no test connects to live TWS or transmits an order.

### Per-defect criteria
Defects D1–D3 (Batch 1, built), D4–D8 (Batches 2–4, all confirmed 2026-09-19), D9–D11 (Batches 5–6, D9–D10 clarified, D11 clarified), D12 (Batch 7, clarified) and D13–D15 (Batches 8–9, D13–D14 clarified, D15 clarified 2026-09-20) each carry their own Given/When/Then criteria and documented edge cases in the **Defect Register** below. Those criteria are the authoritative acceptance tests and are the "test conditions" referenced throughout.

## Defect Register

> Batch 1 (built): three defects reported 2026-09-19 (D1–D3), all clarified and
> built. Batch 2 (clarified 2026-09-19): three refinements confirmed — D4 zoom
> label 21px/position left of axis, D5 volume log lower 1.0, D6 wick 1px vs body
> ≥4×. Batch 3 (clarified 2026-09-19): D7 time-axis 35% gap. Batch 4 (clarified
> 2026-09-19): D8 volume linear, no negatives, dynamic nice ticks, price-coloured.
> Batch 5 (clarified 2026-09-19): D9 volume spacing follow + D10 volume show/hide at
> top left of volume panel. Batch 6 (clarified 2026-09-19): D11 drawing price labels
> on inner right side. Batch 7 (clarified 2026-09-19): D12 zone double-click settings popup (Extend omitted). Batch 8 (clarified 2026-09-20): D13 watchlist resizable to 50% with persistence + D14 double-click row to load chart (identical to Load Chart, no-op on same symbol/disconnected). Batch 9 (clarified 2026-09-20): D15 horizontal line double-click settings popup.

### D1 — No RTH / ETH session shading on chart
- **Area:** Chart panel (price plot)
- **Status:** clarified — criteria defined 2026-09-19
- **Reported:** Chart background does not shade the different trading sessions —
  pre-market, regular hours (RTH), post-market (ETH) are not visually distinct.
- **Observed in code:** no session-shading items exist in `chart_panel.py`. There
  *is* an "Ext Hours" toggle (`main_window.py`) controlling whether pre/post data
  is fetched, and `_custom_date_axis` handles the Eastern-time DST offset.

**Decisions (2026-09-19):**
- Sessions: Pre `04:00–09:30 ET`, RTH `09:30–16:00 ET`, Post `16:00–20:00 ET`,
  overnight `20:00–04:00 ET` unshaded. US Eastern, DST-aware.
- Bands are full-height behind candles. RTH is left at default (no band).
  Pre = **orange at 10% opacity**; Post = **blue at 10% opacity**.
- Render only when **Ext Hours** is ON and only on intraday timeframes:
  `1 min, 5 mins, 15 mins, 1 hour, 4 hours`. Not on `1 day`.
- All symbols use equity ET sessions (accepted default, incl. futures caveat).

**Acceptance Criteria (Given/When/Then):**
- **AC-D1.1** Given Ext Hours ON and an intraday timeframe, When the chart
  renders, Then pre-market is orange @10% and post-market is blue @10%, RTH and
  overnight are unshaded.
- **AC-D1.2** Given Ext Hours OFF, When the chart renders, Then no pre/post bands.
- **AC-D1.3** Given timeframe `1 day`, When the chart renders, Then no session bands.
- **AC-D1.4** Given chart timezone is `UTC`, Then bands stay pinned to the actual
  ET session instants (e.g. 13:30–20:00 UTC during EST), not fixed wall-clock hours.

**Edge Cases:**
- DST transition days (2nd Sun Mar / 1st Sun Nov) keep boundaries at ET local time.
- A bar at exactly `09:30 ET` counts as RTH; at exactly `16:00 ET` counts as post-market.
- No bands painted outside the loaded data range.
- Toggling Ext Hours / changing timeframe or symbol removes stale bands and redraws.

### D2 — Crosshair price label decimals covered by right-side panels
- **Area:** Chart panel → Active Trader / Portfolio dock
- **Status:** clarified — criteria defined 2026-09-19
- **Reported:** the crosshair price label's decimal places are hidden behind the
  element to its right (the Active Trader / Portfolio panels).
- **Observed in code:** `ChartPanel._price_tag` is a scene `TextItem` with
  `anchor=(0, 0.5)` positioned at `view_rect_scene.right()`; the text therefore
  extends rightward past the plot viewport, under the right-hand axis/dock region.

**Decisions (2026-09-19):**
- Fix = **option (a)**: right-align the chip so it ends *inside* the plot's right
  edge and can never be covered by the axis or a right-hand dock.

**Acceptance Criteria (Given/When/Then):**
- **AC-D2.1** Given a loaded symbol and the cursor inside the price plot, When the
  price chip renders with the Active Trader and/or Portfolio dock open, Then the
  complete label including all decimals is visible and not overlapped.
- **AC-D2.2** Given pan or zoom, Then the chip stays fully within the plot's right
  edge and continues to track the cursor's price.
- **AC-D2.3** Given the cursor leaves the plot, Then the chip is hidden (existing
  behaviour retained).

**Edge Cases:**
- Long price strings (e.g. `123,456.78`) must not bleed under the dock or axis.
- Cursor near the top/bottom of the view keeps the chip vertically in-view.
- Dock closed, floating, or hidden still renders the chip correctly.
- Small window widths / narrow plot do not clip the label.

### D3 — Missing zoom controls and area-zoom magnifier
- **Area:** Chart panel / toolbar
- **Status:** clarified — criteria defined 2026-09-19
- **Reported:** zoom tools are missing — a `+` and `−`, plus a magnifying glass
  that lets the user select a rectangular area which then expands to fill the
  chart.
- **Observed in code:** no zoom buttons exist; the toolbar has symbol/TF/mode/
  studies/alarms/DOM/ext-hours/timezone/drawing controls only. pyqtgraph's default
  ViewBox wheel-zoom and drag-pan still function.

**Decisions (2026-09-19):**
- Controls sit **top-right of the chart area** inside a visible **outlined
  container** (neat border): `−`, `+`, magnifier, reset.
- Magnifier: activate → crosshair cursor → click-drag a rectangle → on release the
  view sets **both x and y range** to that rectangle (selection expands to fill the
  chart). `Esc` or right-click cancels. **Magnifier stays active** after one zoom.
- `+`/`−` zoom around the **chart centre**. **Reset** button restores the default
  framing.

**Acceptance Criteria (Given/When/Then):**
- **AC-D3.1** Given a loaded chart, When `+` is clicked, Then the view zooms in
  around the centre; `−` zooms out around the centre.
- **AC-D3.2** Given magnifier mode is active, When the user drags a rectangle and
  releases, Then the view sets x and y range to that rectangle so it fills the
  chart.
- **AC-D3.3** Given magnifier mode, When `Esc` or right-click occurs before
  release, Then the selection is cancelled and the view is unchanged.
- **AC-D3.4** Given one completed magnifier zoom, Then magnifier mode remains
  active for another selection.
- **AC-D3.5** Given Reset is clicked, Then the view returns to the default framing
  equivalent to a fresh chart load (price x/y and volume Y refit).
- **AC-D3.6** Then the zoom control cluster is rendered top-right of the chart
  area inside a visible outline.

**Edge Cases:**
- Degenerate selection (near-zero width/height) → ignored, no zoom.
- Drag starting outside the plot → no selection.
- No bars loaded → controls are disabled / no-op.
- Zoom at range limits → clamped, app remains stable.
- Changing symbol/timeframe while magnifier is active resets mode to default cursor.
- Reset also refits the linked volume (and oscillator) panes consistently.

### D4 — Zoom control cluster refinement: glyphs too small and outline clipped outside chart area
- **Area:** Chart panel / `ui/chart_controls.py`, `ui/chart_panel.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q15 (magnifier +50%) and Q16 (current fine) confirmed
- **Reported:** Post-build UI feedback with screenshot 2026-09-19: zoom tools looked too
  small — button size was enough but the `-` / `+` / `⌕` glyphs and `Reset` label were
  too small; and the toolbox outline was slightly outside the chart area (the `Reset`
  border was clipped at the window/axis edge).
- **Observed in code at time of report:** `ChartControls` buttons used default 11px;
  `ChartPanel.resizeEvent` positioned the cluster at `panel.width - width - 10`,
  which placed it over the price axis rather than fully inside the data area.

**Decisions confirmed 2026-09-19 (Q15 with magnifier +50%, Q16 current fine):**
- `-` / `+` / `Reset` at **14px / 700**, `⌕` (magnifier) at **21px / 700** (14px × 1.5),
  button size remains 28×24; only the glyphs scale.
- Cluster positioned **fully inside the data area, left of the price axis**: `x =
  panel.width - ctrl.width - axis_width - 12` where `axis_width` is the right price
  axis width (fallback 50). Top offset remains `10px` (confirmed fine).

**Acceptance Criteria (Given/When/Then):**
- **AC-D4.1** Given any loaded chart, When the zoom cluster renders, Then `-` / `+`
  / `Reset` are at 14px / 700 and `⌕` is at 21px / 700.
- **AC-D4.2** Given any window size, When the cluster renders, Then its right edge
  is left of the price axis (`ctrl.right() <= panel.width() - axis_width`) and fully
  inside the panel (`ctrl.right() <= panel.width()`), with `y <= 15`.

**Edge Cases:**
- Narrow window or large axis width (e.g., 5-digit prices) keeps the cluster from
  overlapping the axis or being clipped; `x` is clamped to `>= 8`.
- Magnifier remains checkable; button signals unchanged.

### D5 — Volume panel Y axis is linear and compresses small volumes
- **Area:** Chart panel volume plot / `ui/chart_panel.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q17 (lower bound 1.0) confirmed
- **Reported:** Volume panel linear Y makes small volumes invisible when a spike is
  present (see screenshot: spike at 16:00 dominates; 3e7 scale). User requested
  logarithmic Y.
- **Observed in code at time of report:** `volume_plot.getViewBox()` used linear mode
  (`yRange 0.0 .. max*1.1`) and `vol_h` used raw volume including `0`.

**Decisions confirmed 2026-09-19 (Q17):**
- Volume `ViewBox` is **always log on Y** (`setLogMode(y=True)`), X remains linear
  and linked to the price plot.
- Zero-volume bars mapped to **`1.0`** (minimal tick, not a gap) — confirmed lower
  bound `1.0`.
- Auto-range is **`yRange=(1.0, max_vol*1.1)`** where `max_vol` is the maximum of
  mapped volumes.

**Acceptance Criteria (Given/When/Then):**
- **AC-D5.1** Given any loaded chart with volumes, When the volume panel renders,
  Then the ViewBox is in log mode on Y (`getViewBox().logMode == (False, True)`).
- **AC-D5.2** Given bars with zero volume, When `vol_h` is computed, Then the height
  is `1.0` and the volume `yRange` lower bound is `1.0`, not `0.0`.
- **AC-D5.3** Given a max volume, When auto-ranged, Then the upper bound is
  `max_vol*1.1` and small-volume bars are visibly distinct from the spike.

**Edge Cases:**
- All bars have zero volume → `max_vol` floor is `1.0`; range becomes `(1.0, 1.1)`.
- Very small vs very large volumes remain distinguishable on log scale; X remains
  linked to price plot and is unaffected; Reset refits the volume pane consistently.

### D6 — Candlestick wick not clearly distinguishable from body
- **Area:** Chart panel / `ui/candlestick_item.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q18 confirmed
- **Reported:** Two screenshots 2026-09-19: current app’s wick is almost the same
  thickness as the body so wick vs body is indistinguishable (first screenshot, tall
  thin candles with faint wicks); reference screenshot shows a thin, clearly visible
  wick extending beyond the body (second screenshot, high-contrast wicks). User wants
  wick and body drawn clearly so the wick is visible.
- **Observed in code at time of report:** `CandlestickItem` renders body as a
  filled rectangle and wick as a line of similar thickness to the body at default
  zoom, so at typical bar counts the two are not visually distinct.

**Decisions confirmed 2026-09-19 (Q18):**
- Wick (shadow) rendered as a **thin line ~1px** centred on the candle, spanning
  `low` to `high` and drawn behind the body; body width noticeably larger (e.g.,
  ~6–8px at default zoom while wick stays 1px).
- Wick colour follows the candle direction (same as body, e.g., teal `#34d399` for
  up, pink `#f87171` for down); distinction is by **thickness**, not colour.
- At any zoom/timeframe, the wick remains visibly thinner than the body and extends
  beyond the body’s top/bottom whenever a shadow exists (`high > max(open,close)` or
  `low < min(open,close)`).

**Acceptance Criteria (Given/When/Then):**
- **AC-D6.1** Given a loaded chart with candles, When candles render at default
  zoom, Then each wick is ~1px and each body is noticeably wider (body width ≥
  4× wick width), and the wick passes behind the body.
- **AC-D6.2** Given a candle has a shadow, When rendered, Then the wick extends
  beyond the body’s top/bottom by at least 1px and is fully visible.
- **AC-D6.3** Given up vs down candles, When rendered, Then body and wick share the
  candle’s direction colour.

**Edge Cases:**
- Very dense bars (e.g., 1-min over multiple days, hundreds of candles) keep the
  wick thin (never thickens with the body); body may narrow but wick stays 1px.
- Doji (`open == close`) still shows a wick distinct from the body line.
- High-DPI / narrow window does not cause wick and body to merge visually.

### D7 — Time-axis candle spacing slightly too tight
- **Area:** Chart panel / `ui/candlestick_item.py` (candle width) and `ui/chart_panel.py` (xRange)
- **Status:** clarified 2026-09-19 — criteria defined, Q19 (35% gap) confirmed
- **Reported:** New screenshot 2026-09-19 shows the **current app’s** very little
  spacing between bodies (attached chart area, 09:00–18:00, dense 1-min candles with
  almost no gap). The earlier screenshot (09:15–11:30 area with wider gaps) was the
  **sample of how the user wants it to be**.
- **Observed in code at time of report:** `CandlestickItem._draw_candles` uses
  `w = median_diff * 0.4` (body is 80% of bar spacing, gap is 20% of spacing) and
  `ChartPanel._refresh_candles` frames `xRange=(t0 - 2*bar_w, t1 + 8*bar_w)` with
  `bar_w` = one bar’s time diff. Both determine the on-screen gap.

**Decisions confirmed 2026-09-19 (Q19: 35% gap):**
- Increase the inter-candle gap from **20% to ~35%** of bar spacing by reducing the
  body half-width from `0.40` to **`0.325`** of `median_diff` (full body 65% of
  spacing, gap 35% — ~75% more gap in relative terms, but still compact). No change
  to `xRange` padding (`-2*bar_w / +8*bar_w`); if a larger framing change is
  preferred it can be added as an alternative.
- The existing device-pixel minimum for the body (from D6, ≥4px) continues to apply
  so the slightly narrower body never collapses below legibility.

**Acceptance Criteria (Given/When/Then):**
- **AC-D7.1** Given a loaded chart at default zoom, When candles render, Then the
  gap between adjacent bodies is ~35% of bar spacing (body half-width is 0.325×
  `median_diff`), visibly larger than the current 20% gap.
- **AC-D7.2** Given the same data, When compared to the current rendering, Then the
  on-screen distance between bodies is larger by ~15–18% of bar spacing (the gap
  grows from 0.20 to 0.35 of spacing).

**Edge Cases:**
- Very dense 1-min view (hundreds of candles) keeps the gap proportional (35% of
  spacing) but the 4px body minimum may override — the gap remains positive and the
  chart does not become empty.
- Single-bar chart (`w = 0.25` fallback) is unchanged.
- All chart modes (Candles, Hollow, Heikin) use the same `w` factor; Line/Area are
  unaffected.

### D8 — Volume panel shows negatives, log scale not desired, bars not price-coloured
- **Area:** Chart panel volume plot / `ui/chart_panel.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q20 confirmed — revises D5’s prior log decision
- **Reported:** New volume screenshots 2026-09-19: current app shows **negative**
  ticks (e.g., `-200`) on the right axis — volume cannot be negative; and the log
  scale "looks" not desired. The desired look (second screenshot) has **no
  negatives**, a **linear** Y with ticks like `10k / 100k / 500.0K / 1.0M / 1.5M /
  2.0M / 2.5M`, a **dynamic max** based on the visible max volume, and bars
  **coloured green/red by price candle** (green `#34d399` when `close >= open`,
  red `#f87171` otherwise).
- **Observed in code at time of report:** `volume_plot.getViewBox()` was switched
  to log on Y in the prior D5 patch (`setLogMode('y', True)` with `0→1.0` floor
  and `yRange=(1, max*1.1)`); `volume_bars` were set with `height=vol` and
  `y0=1`. The current screenshot still shows a linear-looking axis with negatives,
  indicating the log change did not produce the desired look and the yRange still
  dips below zero.

**Decisions confirmed 2026-09-19 (Q20):**
- Volume `ViewBox` is **linear on Y** (`setLogMode(y=False)`, X stays linear/linked);
  `yRange=(0, nice_max)` with `nice_max` as `max_vol*1.1` rounded up to the next
  nice value from `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]`
  so the axis shows 3–5 ticks (e.g., max ~2.8M → `0, 500.0K, 1.0M, 1.5M, 2.0M, 2.5M`
  as in the desired screenshot; max ~80K → `0, 25K, 50K, 75K, 100K`).
- Volume bars are **coloured by price candle direction** (`#34d399` when `close >=
  open`, `#f87171` otherwise) — matching `CandlestickItem` bodies. This revises the
  prior log decision; no toggle is proposed — linear is the sole mode.
- Y ticks are formatted as `500.0K / 1.0M` (one decimal for K, same for M) via the
  right-axis tick formatter; no negative ticks are ever shown.

**Acceptance Criteria (Given/When/Then):**
- **AC-D8.1** Given any loaded chart, When the volume panel renders, Then the Y is
  linear (`logMode == (False, False)`), lower bound is `0`, no negative tick is
  shown, and the upper bound is the dynamic nice max (`max_vol*1.1` rounded up).
- **AC-D8.2** Given volumes, When bars render, Then each bar is green when its price
  candle has `close >= open` and red otherwise, and the yRange upper covers the max
  with the nice tick above it.
- **AC-D8.3** Given a max volume, When formatted, Then ticks appear as `10k / 100k /
  500.0K / 1.0M / 1.5M` etc., with `0` at the bottom and no `-200`.

**Edge Cases:**
- All bars have zero volume → `max_vol` floor is `10k`; yRange becomes `(0, 10k)` and
  bars are minimal/gaps.
- Single bar with very small max (e.g., 8K) still picks a sensible nice max (10k) and
  shows ticks `0, 2.5K, 5K, 7.5K, 10K`.
- Max just below a boundary (e.g., 1.05M with nice 1.0M/1.5M) correctly rounds up to
  `1.5M`, not `1.0M`.
- Volume bars remain green/red even when price is a Doji (`open==close` → green).

### D9 — Volume bar spacing should follow price candle spacing
- **Area:** Chart panel volume plot / `ui/chart_panel.py` (`volume_bars` width)
- **Status:** clarified 2026-09-19 — criteria defined, Q21 correct
- **Reported:** User feedback 2026-09-19: spacing between volume candles should
  follow the spacing of the price candles. Volume bars currently use a fixed
  `width=0.6` (data units) while price bodies use `w = median_diff * 0.325`
  (Batch 3, 35% gap, full body 65% of spacing) plus a 4px minimum. The two can
  drift — volume gaps look different from price gaps.
- **Observed in code at time of report:** `volume_bars = pg.BarGraphItem(x=vol_x,
  height=vol_h, width=0.6, y0=1)` in `chart_panel.py`; price `w` is computed from
  `median_diff` and clamped to a device-pixel minimum. X remains linked
  (`setXLink`).

**Decisions confirmed 2026-09-19 (Q21 correct):**
- Volume `BarGraphItem` width is the **same `w`** as the price candles (`width =
  w*2`, full body 65% of `median_diff`), so the gap is exactly the same as the
  price panel (35%).

**Acceptance Criteria (Given/When/Then):**
- **AC-D9.1** Given a loaded chart, When volume and price render at the same
  timeframe/zoom, Then the volume bar width equals the price body width (`w*2`)
  and the inter-bar gaps are identical.
- **AC-D9.2** Given a dense 1-min view where the 4px body minimum applies, When
  rendered, Then volume bars follow the same clamped `w` so gaps stay aligned with
  price gaps.

**Edge Cases:**
- Single-bar fallback (`w=0.25`) is used for both price and volume; single volume
  bar still aligns.
- All volume bars follow the price `w`; Line/Area modes (no price bodies) still use
  the same `w` for volume.

### D10 — Volume panel show/hide toggle
- **Area:** Chart panel volume plot / `ui/chart_panel.py` — top left of volume panel (bottom left of price chart)
- **Status:** clarified 2026-09-19 — criteria defined, Q22 top left of volume panel
- **Reported:** User feedback 2026-09-19: allow the user to show/hide (toggle) the
  volume panel to maximize price-chart vertical space. No toggle exists today; the
  volume `PlotWidget` is always visible in the splitter.
- **Observed in code at time of report:** `volume_plot` is a `PlotWidget` in a
  vertical `QSplitter` with `price_plot` and `osc_plot`; it is always added and
  shown. No user-facing visibility control exists.

**Decisions confirmed 2026-09-19 (Q22 top left of volume panel):**
- **Top left of the volume panel** (bottom left of price chart) hosts a
  **checkable toggle**, default **visible**. Toggling hides/shows `volume_plot`
  (and its axis) and the `QSplitter` is rebalanced so the price plot expands when
  hidden. The toggle state is **not persisted** in this proposal (resets to visible
  on launch).

**Acceptance Criteria (Given/When/Then):**
- **AC-D10.1** Given the volume panel is visible, When the user toggles the
  control, Then `volume_plot` becomes hidden and the price plot expands to fill the
  freed vertical space; toggling again shows it.
- **AC-D10.2** Given the app is restarted, When launched, Then the volume panel is
  visible by default (no persistence in this proposal).

**Edge Cases:**
- Toggling with no bars loaded hides/shows without error.
- Oscillator `osc_plot` visibility is independent; hiding volume does not affect it.
- Splitter sizes are restored correctly after hide/show cycles.

### D11 — Drawing price labels should be on inner right side of chart
- **Area:** Chart panel drawings / `ui/drawing_overlay.py`, `ui/overlays/*`
- **Status:** clarified 2026-09-19 — criteria defined, Q23 correct
- **Reported:** Two screenshots 2026-09-19: the app’s zones (first screenshot,
  blue/teal horizontal zones at ~332–336 with no price label on the right
  interior) vs the reference app (second screenshot, green/brown zone at
  757–764 with prices on the right interior: `757.67`, `760.63`, `762.39`,
  `764.48`, etc.). User wants for any drawing the price to be on the inner side
  of the chart (right side) — i.e., inside the plot near the right edge, not on
  the axis or left side.
- **Observed in code at time of report:** `DrawingOverlay` renders horizontal
  lines/zones with labels that are not consistently anchored to the inner right;
  some labels are outside or not visible on the right interior.

**Decisions confirmed 2026-09-19 (Q23 correct):**
- For any drawing type (horizontal line at price `y`, zone `y1`/`y2`, trendline
  `p1`/`p2`, Fibonacci level), the price label is a `TextItem` anchored **inside
  the plot** at the right edge: `anchor=(1, 0.5)`, `x = view_rect.right() - 4`,
  `y = price`, `Z=10`, with the same colour as the drawing. For zones, the top
  and bottom edges each get a label; for trendlines/Fibonacci, each level’s
  right-edge label is placed similarly.
- Labels are children of the price plot’s scene (like the crosshair chip), so they
  are never clipped by the right axis/dock and remain visible at any zoom.
- When multiple drawings share a similar price, labels stack with a small vertical
  offset to avoid overlap (or the topmost remains).

**Acceptance Criteria (Given/When/Then):**
- **AC-D11.1** Given any drawing with a price, When rendered, Then a price label
  is visible **inside the plot near the right edge** (`x = view_rect.right() - 4`,
  `anchor=(1,0.5)`) and is not clipped by the axis/dock.
- **AC-D11.2** Given a zone with top/bottom prices, When rendered, Then two labels
  are visible at the zone’s top and bottom edges on the inner right.
- **AC-D11.3** Given multiple drawings at nearby prices, When rendered, Then
  labels remain legible (small vertical offset, not fully overlapping).

**Edge Cases:**
- Very narrow window or wide axis keeps labels inside (clamped to `view_rect`).
- Zooming/panning keeps labels at the right edge and at the correct price.
- No drawing → no label.

### D12 — Zone double-click should open settings popup with 4 tabs (Extend omitted)
- **Area:** Drawings / `ui/drawing_overlay.py` + new `ui/drawings_dialog.py` (or `ui/zone_settings_dialog.py`)
- **Status:** clarified 2026-09-19 — criteria defined, Q24 Extend omitted confirmed — revises prior popup assumptions
- **Reported:** User wants double-click on a zone (rectangle) to open the zone
  settings popup as per the four attached screenshots. The Style tab in the
  reference shows an `Extend` dropdown (`Extend right`), but the user says
  `Extend` is not required because **extend both sides** is the required
  behaviour.
- **Observed in code at time of report:** `DrawingOverlay` handles single-click
  selection and drag, but double-click does not open a zone settings popup; no
  4-tab dialog exists for zones.

**Decisions confirmed 2026-09-19 (Q24 Extend omitted):**
- Double-click on a zone (rectangle) drawing opens a **modal Zone Settings popup**
  titled `Rectangle` with a pencil icon and an `X` close button, showing four tabs:
  **Style / Text / Coordinates / Visibility** as in the attachments.
- **Style tab:** `Extend` control is **omitted** (zone always extends both sides);
  `Border` (color swatch green + solid line), `Middle line` (unchecked checkbox +
  purple swatch + dashed line), `Background` (checked + checker swatch) remain.
- **Text tab:** text colour swatch (white), font size `14`, `B`/`I` toggles, `Add
  text` multi-line field, `Text alignment` `Top` / `Right` dropdowns.
- **Coordinates tab:** `#1 (price, bar)` `7623.89` and `#2 (price, bar)` `7614.81`
  with up/down steppers, pre-filled from the zone’s current `x1/y1/x2/y2`.
- **Visibility tab:** checkboxes for `Ticks`, `Seconds` (1–59 slider), `Minutes`
  (1–59), `Hours` (1–24), `Days` (1–366), `Weeks` (1–52), `Months` (1–12),
  `Ranges` (no value) — as shown.
- OK/Apply updates the zone and re-renders; Cancel/X closes without change.

**Acceptance Criteria (Given/When/Then):**
- **AC-D12.1** Given a zone exists, When the user double-clicks the zone body, Then
  the `Rectangle` popup opens with four tabs and the zone’s current values
  pre-filled, and `Extend` is not shown.
- **AC-D12.2** Given the popup is open, When the user changes Style/Text/Coordinates
  and confirms, Then the zone updates and re-renders with the new values.
- **AC-D12.3** Given the popup is open, When the user opens the Visibility tab,
  Then the time-frame checkboxes/sliders match the attachments and are
  interactable.

**Edge Cases:**
- Double-click on a non-zone drawing does not open the zone popup.
- Double-click with no selection does nothing.
- Cancel/X discards changes; the zone remains as before.

### D13 — Watchlist dock resizable to 50% of window width with persistence
- **Area:** Watchlist dock / `ui/main_window.py`, `ui/watchlist_panel.py`
- **Status:** clarified 2026-09-20 — criteria defined, Q25/Q26 confirmed
- **Reported:** The watchlist panel should extend more so the user can see more
  symbols/columns; the current width is limited and is not remembered.
- **Observed in code at time of report:** the Watchlist is a `QDockWidget` in
  `LeftDockWidgetArea` (`ui/main_window.py`); its width was not explicitly bounded
  to a percentage of the window and was not persisted across restarts.

**Decisions confirmed 2026-09-20 (Q25 50% freely draggable; Q26 persist yes):**
- Docked Watchlist is freely draggable up to **~50% of `MainWindow` width**,
  clamped to `[150, min(floor(0.50×W), W−400)]` so the chart central panel keeps
  **≥400px**; minimum watchlist `150px`; clamped on window resize; floating geometry
  is unconstrained.
- Watchlist width persists across restarts as an **integer pixel** value (e.g.,
  `QSettings watchlist/width` or a DB key); default **~220px** if none saved;
  restore is clamped to the current 50%.

**Acceptance Criteria (Given/When/Then):**
- **AC-D13.1** Given a docked Watchlist at default width, When the user drags the
  vertical splitter right/left, Then watchlist width is clamped to
  `[150, floor(0.50×W)]` (and also `W−400` for the chart minimum) and the chart
  width adjusts, with the handle remaining draggable across the range.
- **AC-D13.2** Given a persisted width, When the app restarts, Then the watchlist
  restores to the persisted integer width clamped to the current `floor(0.50×W)`
  (default ~220px if none saved, never <150).
- **AC-D13.3** Given a wide watchlist and the main window is narrowed, When the
  width would exceed 50%, Then the watchlist is auto-clamped to 50% without error
  and remains resizable.

**Edge Cases:**
- Floating Watchlist is not constrained to 50%; docking it again re-applies the
  clamp.
- Extremely narrow windows keep `150px` watchlist and `≥400px` chart; if the window
  is smaller than the sum, the watchlist yields to the chart minimum.
- No saved width on first run uses ~220px.

### D14 — Double-click Watchlist row loads chart (identical to Load Chart)
- **Area:** Watchlist dock / `ui/watchlist_panel.py` + `ui/main_window.py`
- **Status:** clarified 2026-09-20 — criteria defined, Q27–Q29 confirmed
- **Reported:** Clicking a watchlist row should load that symbol’s chart.
- **Observed in code at time of report:** the watchlist table selected rows but had
  no double-click handler to trigger chart loading; chart loading is centralised in
  `MainWindow.load_chart()`.

**Decisions confirmed 2026-09-20 (Q27 double-click row; Q28 identical to Load
Chart; Q29 no-op semantics):**
- **Double-click anywhere on the row** (any of the 7 columns) triggers the load;
  single-click only selects the row (existing `SelectRows` behaviour retained).
- Load is **identical to typing the symbol in the Symbol input and pressing Load
  Chart**: set `symbol_input` to the row’s Symbol (uppercased), then invoke the
  existing `load_chart()` with the current `tf_combo` and `ext_hours_btn` — this
  includes cancelling the previous RT subscription, showing cached bars, fetching
  the delta, starting the RT subscription, and subscribing DOM if enabled.
- **No-op** when the double-clicked symbol (case-insensitive) equals
  `_current_symbol` — no reload, no new `reqId`, no RT cancel, no flicker; and when
  IBKR is disconnected — no historical/RT request and
  `status_bar.showMessage("Disconnected — cannot load chart.", 3000)`.
- Double-click on the header or an empty area is also a no-op.

**Acceptance Criteria (Given/When/Then):**
- **AC-D14.1** Given the Watchlist has symbols, IBKR is connected, and the current
  chart is `SPY`, When the user double-clicks any cell in the `AAPL` row, Then
  `symbol_input` becomes `AAPL` and the chart loads for `AAPL` with the current
  timeframe/ext-hours via the same sequence as manual Load Chart (cached bars
  shown, delta fetched, RT started).
- **AC-D14.2** Given the current chart is `AAPL`, When the user double-clicks the
  `AAPL` row, Then no reload occurs — no new `reqId` is issued, the RT subscription
  for `AAPL` remains, and the chart does not flicker.
- **AC-D14.3** Given IBKR is disconnected, When the user double-clicks any watchlist
  row, Then no historical/RT request is made and the status bar shows
  `Disconnected — cannot load chart.` Double-click on the header or an empty area
  also does nothing.

**Edge Cases:**
- Symbol case differences (`aapl` vs `AAPL`) are treated as the same symbol
  (case-insensitive comparison).
- Double-click during an in-flight load for a different symbol cancels that RT and
  loads the new symbol (existing `load_chart` behaviour).
- No symbols in the watchlist → double-click does nothing.

### D15 — Double-click horizontal line should open settings popup with 4 tabs
- **Area:** Drawings / `ui/drawing_overlay.py` + new `ui/horizontal_line_settings_dialog.py` (or `ui/drawing_settings_dialog.py`)
- **Status:** clarified 2026-09-20 — criteria defined, Q30 correct
- **Reported:** User double-click on a horizontal line should open the line settings
  popup as per the four attached screenshots for `Horizontal line`.
- **Observed in code at time of report:** `DrawingOverlay` handles single-click
  selection/drag for horizontal lines but double-click does not open a settings
  popup; no 4-tab dialog exists for horizontal lines.

**Decisions confirmed 2026-09-20 (Q30 correct):**
- Double-click on a horizontal line drawing opens a **modal Horizontal line settings
  popup** titled `Horizontal line` with a pencil icon and an `X` close button,
  showing four tabs: **Style / Text / Coordinates / Visibility** as in the
  attachments.
- **Style tab:** `Line` (color swatch white + solid line style) — as shown.
- **Text tab:** text colour swatch (white), font size `12`, `B`/`I` toggles,
  `Add text` multi-line field, `Text alignment` `Top` / `Right` dropdowns.
- **Coordinates tab:** `#1 (price)` `7548.85` with up/down steppers, pre-filled
  from the line’s current price `y`.
- **Visibility tab:** checkboxes for `Ticks`, `Seconds` (1–59 slider), `Minutes`
  (1–59), `Hours` (1–24), `Days` (1–366), `Weeks` (1–52), `Months` (1–12),
  `Ranges` — as shown.
- OK/Apply updates the line and re-renders; Cancel/X closes without change.

**Acceptance Criteria (Given/When/Then):**
- **AC-D15.1** Given a horizontal line exists, When the user double-clicks the
  line, Then the `Horizontal line` popup opens with four tabs and the line’s
  current values pre-filled.
- **AC-D15.2** Given the popup is open, When the user changes Style/Text/Coordinates
  and confirms, Then the line updates and re-renders with the new values.
- **AC-D15.3** Given the popup is open, When the user opens the Visibility tab,
  Then the timeframe checkboxes/sliders match the attachments and are
  interactable.

**Edge Cases:**
- Double-click on a non-horizontal drawing does not open the horizontal-line popup.
- Double-click with no selection does nothing.
- Cancel/X discards changes; the line remains as before.

## Assumptions Log
| # | Assumption | Rationale | Confirmed? | Date |
|---|---|---|---|---|
| A1 | This repo is the Python reimplementation of the React reference app | Consistent across `dev_docs/delta.md` and `PENDING_IMPLEMENTATION_PLAN.md` | n | 2026-09-19 |
| A2 | Phases 1–10 of `PENDING_IMPLEMENTATION_PLAN.md` are effectively implemented | All referenced modules and tests exist on disk | n | 2026-09-19 |
| A3 | Defects are diagnosed against the dev build (`python main.py`), not the packaged `.app` | Dev build is the working target; bundle untested per-defect unless stated | n | 2026-09-19 |
| A4 | "Test conditions pass" means the existing offscreen suite plus new per-defect checks | Q3 + Q8 confirmed + repo test conventions | y | 2026-09-19 |
| A5 | D2 chip keeps current 2-decimal format, or matches axis tick precision if that differs | User chose placement "(a)" only; decimals unspecified | n | 2026-09-19 |
| A6 | D3 magnifier reverts to Cursor when symbol/timeframe changes | Not stated by user; safety default | n | 2026-09-19 |
| A7 | D1 exact orange/blue hex picked to match the app theme at 10% alpha | User specified colour name + opacity only | n | 2026-09-19 |
| A8 | D4 glyph size is 14px/700 for `-`/`+`/`Reset` and 21px/700 for `⌕` (magnifier 50% larger), and the inside-data-area position is `panel.width - ctrl.width - axis_width - 12` | Q15 confirmed with magnifier +50% (21px vs 14px); Q16 confirmed current fine | y | 2026-09-19 |
| A10 | D6 wick is ~1px thin line behind the body (body ≥4× wick), colour follows direction, wick extends beyond body when shadow exists | Q18 confirmed 2026-09-19 | y | 2026-09-19 |
| A9 | D5 volume log is always on, X stays linear, zero-volume bars map to 1.0 with yRange lower 1.0 | User said "y-axis needs to be logarithmic" without specifying toggle or zero handling | n | 2026-09-19 |
| A11 | D7 gap is 35% of bar spacing (body half-width 0.325× median_diff) rather than the current 20% (0.40) | Q19 confirmed "go 35% gap for now" | y | 2026-09-19 |
| A12 | D8 volume is linear on Y with `yRange=(0, nice_max)` where `nice_max` is `max_vol*1.1` rounded to the next nice tick from `[10k, 50k, 100k, 250k, 500k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]`, no negatives, and bars are green/red by `close>=open` | Q20 confirmed 2026-09-19 | y | 2026-09-19 |
| A13 | D9 volume bar width follows price candle width (`width = w*2`, gap 35% of `median_diff`) | Q21 correct — matching price 35% gap | y | 2026-09-19 |
| A14 | D10 volume toggle is a checkable control (default visible), hides/shows `volume_plot` via the splitter, and is not persisted | Q22 Top left of the volume panel (bottom left of price chart) confirmed, no persistence specified | y | 2026-09-19 |
| A15 | D11 drawing price labels are inside the plot at the right edge (`anchor=(1,0.5)`, `x = view_rect.right() - 4`) with the drawing’s colour, one per price, stacking when nearby | Q23 correct — inner right side as proposed | y | 2026-09-19 |
| A16 | D12 zone settings popup is titled `Rectangle` with 4 tabs Style/Text/Coordinates/Visibility, Extend omitted (always both sides), double-click on zone opens it | Q24 Extend omitted confirmed | y | 2026-09-19 |
| A17 | D13 watchlist dock width is freely draggable [150, floor(0.50×W)] (chart ≥400px ⇒ max = min(0.50×W, W−400)), persisted across restarts (QSettings or DB), default ~220px, clamped on restore/resize; floating not constrained | Q25 50% freely draggable + Q26 persist yes confirmed 2026-09-20 | y | 2026-09-20 |
| A18 | D14 watchlist double-click anywhere on row (any column) triggers chart load identical to manual Load Chart with current timeframe/ext-hours, updates symbol_input | Q27 double-click row + Q28 identical to Load Chart confirmed 2026-09-20 | y | 2026-09-20 |
| A19 | D14 no-op when double-clicked symbol equals _current_symbol (case-insensitive) or when IBKR disconnected (status message only, no request); header/empty area also no-op | Q29 no-op confirmed 2026-09-20 | y | 2026-09-20 |
| A20 | D15 horizontal line settings popup is titled `Horizontal line` with 4 tabs Style (Line) / Text (12, B/I, Add text, Top/Right) / Coordinates #1 (price) 7548.85 / Visibility (Ticks–Ranges) | Q30 correct — four tabs as per attachments | y | 2026-09-20 |

## Risks / Unknowns
| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | More defects may be reported after batch 1, expanding scope mid-build | M | M | Batch 1 declared complete; new feedback triggers a fresh requirements pass, not silent scope growth |
| R2 | Plan doc checkmarks are stale (many unchecked phases are actually built) | M | H | Verify actual behavior before treating any plan phase as open |
| R3 | Any change may touch the live-order path (real money) | H | M | TWS-side gating active (Q4); no automated test may transmit orders (Q9) |
| R4 | Vague UI defects ("looks wrong") yield untestable criteria | M | H | Every defect must have measurable Given/When/Then criteria and an edge case |
| R5 | Fixing one UI defect may regress another (shared chart/dock code) | M | M | Re-run full suite per fix; note regression risk per defect |
| R6 | D4 axis width varies with price magnitude; fixed 28px margin may still clip | M | M | Position left of dynamic `getAxis('right').width()` with 12px margin and `x>=8` clamp |
| R7 | D5 log scale cannot display 0; zero-volume handling may be interpreted as data | L | M | Map 0→1.0 with documented minimal tick; keep yRange lower 1.0 |
| R8 | D6 wick/body thickness ratio may still be indistinct at extreme zoom/density | M | M | Fix wick at 1px regardless of zoom; body narrows with density but wick does not |
| R9 | D7 slightly narrower bodies could reduce legibility at very high density | L | M | Keep 4px body minimum from D6; gap remains positive; verify at 1-min dense view |
| R10 | D8 nice-max rounding could still leave little headroom if max is just above a nice boundary | L | M | Use `max*1.1` before rounding up; verify tick count stays 3–5 |
| R11 | D9 volume and price widths could diverge on Line/Area modes where price has no bodies | L | L | Define volume width from the same `w` even when price mode has no bodies; keep XLink |
| R12 | D10 toggle placement/persistence may not match user expectation | L | M | Top left of volume panel (bottom left of price chart) as confirmed Q22, not persisted |
| R13 | D11 price labels could overlap when many drawings share a similar price | L | M | Stack with small vertical offset or show topmost; verify at 09:00–10:00 dense zones |
| R14 | D12 zone popup with 4 tabs adds non-trivial UI surface; Extend omission may surprise users expecting the control | L | M | Omit Extend per user’s "extend both sides is required"; keep the other Style controls as shown |
| R15 | D13 50% max may still crowd chart on small screens; persistence restore could exceed new window size | L | M | Enforce chart ≥400px via `min(0.50×W, W−400)` and clamp on restore/resize; min watchlist 150px |
| R16 | D14 double-click could be mistaken for single-click row selection; accidental reloads | L | M | Require double-click (not single), any column; same-symbol and disconnected are no-ops; status message for disconnected |
| R17 | D13 floating vs docked width confusion — 50% rule mismatch | L | L | Apply 50% only when docked in LeftDockWidgetArea; floating geometry unconstrained |
| R18 | D15 horizontal line popup duplicates zone popup structure; Text tab font size 12 vs zone 14 may confuse | L | L | Keep D15 Style as Line only and Text size 12 as per attachment; keep D12 Style with Border/Middle/Background |

---

Status: READY_FOR_PLAN
