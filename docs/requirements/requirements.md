# NDThinkChart — Requirements

> Status: **D17/D18 (panel layout / resizing in full screen, reported 2026-10-03) — CLARIFIED 2026-10-03 (B1–B4 answered; see `open_questions.md` Q/B1–B4).** D16 (historical-bar hole, reported 2026-10-02) is **clarified and finalised** (Q37–Q39 answered 2026-10-02: backfill the whole gap so the chart is continuous; genuine closures stay empty; all timeframes and any symbol). **ESC-023 correction (2026-10-02):** the D16 trading-day calendar carries an explicit **New Year's year-end accounting exception** — Dec 31 is a **trading day** when Jan 1 of the next year falls on a Saturday (see D16 / `AC-D16.7`). D1–D15 remain built and green. The Existing Repository section (marker sentence + Current Tech Stack) is preserved and must not be dropped.

## Problem Statement
NDThinkChart is a feature-complete desktop trading terminal (PyQt6 + pyqtgraph +
official `ibapi`, live TWS port 7496) built through Phases 1–10 of
`PENDING_IMPLEMENTATION_PLAN.md`. It is now in a **feedback-driven stabilization
phase**: the user reviewed the running app and reported functional issues and UI
bugs, which this run must triage and fix. Batch 1 (D1–D3) was the complete list
for the first stabilization run and is clarified and built. Batch 2 (D4–D6) is now
fully clarified from post-build UI feedback 2026-09-19 (zoom label size with
magnifier +50% and position fine — Q15/Q16 — **volume log lower bound 1.0 — Q17 —
SUPERSEDED by D8 (linear, Q20); see D5** — and candlestick wick 1px vs body ≥4× —
Q18). Batch 3 (D7 35% gap) is a time-axis
spacing refinement confirmed 2026-09-19. Batch 4 (D8) is a volume-panel revision
(linear, no negatives, dynamic nice ticks, price-coloured) confirmed 2026-09-19.
Batch 5 (D9 volume spacing follow and D10 volume show/hide at top left of volume
panel) is now clarified 2026-09-19 (Q21 correct, Q22 top left). Batch 6 (D11
drawing price labels on inner right side) is clarified 2026-09-19 (Q23 correct).
Batch 7 (D12) zone double-click settings popup with 4 tabs is clarified 2026-09-19
(Q24 Extend omitted). Batch 8 (D13 watchlist resizable to 50% with persistence +
D14 double-click row to load chart) clarified 2026-09-20 per Q25–Q29. Batch 9
(D15) horizontal line double-click settings popup with 4 tabs is clarified 2026-09-20 per Q30.

**New work item — 2026-10-02 (defect D16) — CLARIFIED.** The user reported that historical bars are **missing across 2026-09-19…2026-09-27** on `SPY` `5 mins` (price candles) and that the **volume panel is empty over the same span**; 2026-09-21…2026-09-25 are normal trading weekdays, so this is a bar-data hole, not weekend session shading. The hole is an **internal** discontinuity in the cache: the screen shows bars 09/14–09/18, nothing 09/19–09/27, and bars 09/28–10/02 (validated live against `SPY 5 mins` in the user-space SQLite cache). D16 is captured in the Defect Register + Journey 17 and is the sole open requirement for this new batch. **Decisions (2026-10-02, Q37–Q39):** the app backfills the whole gap so the chart is continuous (chunking requests if needed); genuine market closures (weekend/holiday/overnight) stay **empty** and are not filled or compressed; the fix and its verification cover **all timeframes** (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and **any symbol**. **Correction (ESC-023, 2026-10-02):** the D16 trading-day calendar's New Year's observed-day shift is corrected to carry the **NYSE Rule 7.2 year-end accounting exception** — when Jan 1 falls on a Saturday, the preceding Friday (Dec 31) is a **trading day**, not a closure, and no New Year's holiday is observed; a genuine bar hole on such a day is therefore a missing trading session, not a genuine closure (see D16 / `AC-D16.7`). The corrected `T37-T03` acceptance criterion and the `market_calendar` observed-shift rule must both change (Task Manager / Build). All D1–D15 acceptance criteria are built and remain frozen/unchanged.


**New work item — 2026-10-03 (defects D17 + D18) — CLARIFIED 2026-10-03 (B1–B4 answered).** The user
reviewed the running app **in full screen** and reported two panel-layout problems (verbatim in the
Defect Register): **(D17)** the **Watchlist** dock on the left is too small and "does not extend or
reduce in width if user tries it"; the fix requested is to allow it to be extended **till 50% of the
chart area**, with the chart narrowing as the watchlist grows. **(D18)** the right-side **Active
Trader** section (which contains the ladder, with **Portfolio** below it) "does not even be visible
to user if the app is made full screen"; the fix requested is to reposition it so it fits the visible
full-screen area, allow it to be enlarged **till 40% of the chart area**, keep **Active Trader and
Portfolio at the same width**, and narrow the chart as it grows. D17 is diagnosed as a **likely defect
in the built D13 behaviour** (the 50% cap exists as helpers but is never enforced during a dock drag —
see D17), while D18 is a **new requirement** (no prior defect covers the right dock's width or
full-screen visibility — see D18). Both are captured in the Defect Register + Journeys 18–19 with
**final** acceptance criteria. **Decisions (2026-10-03, B1–B4 answered):** **(B1)** the watchlist cap
is **50% of the CHART AREA**, not of the window — this **supersedes and corrects D13's Q25
denominator** ("50% of MainWindow width"), and `AC-D13.1`–`AC-D13.3`, Journey 14, A17 and R15 are
updated in lockstep. **(B2)** Active Trader and Portfolio live in **ONE right-dock region** containing
both stacked sections, so they share equal width by construction; the **40%-of-chart-area** cap
applies to that one region. **(B3)** **independent caps + a chart-minimum rule**: each dock clamps
against its own % (watchlist 50%, right dock 40%) **and** against the remaining space so the chart
keeps a minimum (~400px); enlarging one can force the other to shrink. **(B4)** the watchlist handle
drags **both wider and narrower** between min (150px) and cap; min stays 150px, default ~220px, and
persistence (Q26) is **still required**. See `open_questions.md` (B1–B4 answered) and DG23–DG26.

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

## Existing Repository

This is an existing repository. NDThinkChart is a stabilization/extension run against an
already-built PyQt6 + pyqtgraph + `ibapi` desktop trading terminal (development build:
`python main.py`; bundled: PyInstaller windowed `.app`, bundle id `com.ndthinkchart.app`).
The D1–D15 work is built and green. This section is preserved through every rewrite because
Plan, the Plan Artifact Editor & Validator, and the Orchestrator key **existing-repo mode**
off of the marker sentence above.

**What is being built/changed in this run:** the **D16** historical-bar backfill (built and green,
2026-10-02) plus two **2026-10-03 panel-layout defects (D17 + D18), clarified 2026-10-03 (B1–B4
answered)**:
- **D17 — Watchlist resize in full screen (CLARIFIED):** the Watchlist dock must be draggable in
  **both directions** between its minimum (150px) and its cap of **50% of the chart area**, with the
  chart area narrowing as it grows and the cap enforced **during the drag** (not only on window
  `resizeEvent`); the width persists per Q26. Expected to live in the existing dock/splitter wiring
  (`ui/main_window.py` dock setup + resize handling; `ui/watchlist_panel.py` clamp helpers).
- **D18 — Active Trader/Portfolio right dock in full screen (CLARIFIED, new requirement):** a
  **single right-dock region** (Active Trader ladder + Portfolio stacked) must be fully visible in
  full screen, resizable up to **40% of the chart area**, with the two stacked sections inherently at
  equal width (one region) and the chart narrowing as it grows; combined with D17 under the
  chart-minimum rule (B3). Expected to live in `ui/main_window.py` (`RightDockWidgetArea` setup)
  and/or the panel classes (`ui/active_trader_panel.py`, `ui/active_portfolio_panel.py`).
No new product features beyond these layout fixes, and **no stack change**. Both are finalised by
B1–B4 (`open_questions.md`); D17 corrects D13's denominator in lockstep (B1).

**Repository mapping note (graphify).** A knowledge graph exists at `graphify-out/`
(`graph.json`, `GRAPH_REPORT.md`). Per `AGENTS.md`, downstream agents — Plan, Plan Artifact
Editor & Validator, Task Manager, Build/Build Worker, and Code Reviewer — **may use the
graphify tool** to map existing components, data models, integrations, and relationships.
Graphify findings are discovery inputs only and MUST be validated against the current
repository files, which remain authoritative if the two disagree.

**Current Tech Stack:**
- **Language/runtime:** Python 3.11+ (`.venv`), macOS Apple Silicon (arm64).
- **UI:** PyQt6 (`PyQt6>=6.6`), pyqtgraph (`>=0.13`).
- **Broker:** official `ibapi` (`>=9.81`), Interactive Brokers TWS, **live port 7496 only — no paper mode**.
- **Numerics:** numpy (`>=1.26`).
- **Persistence:** SQLite. `config/paths.get_db_path()` always resolves to the user-space
  database `~/Library/Application Support/NDThinkChart/charting_app.sqlite3` (the filename
  can be overridden with the `DB_PATH` env var). A stale repo-root `./charting_app.sqlite3`
  exists but is not the path `get_db_path()` returns.
- **Packaging:** PyInstaller windowed `.app`, bundle id `com.ndthinkchart.app`.
- **Tests:** pytest + pytest-qt, run offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS
  required by default.
- **Existing bar-load path (reference):** `ui/main_window.py::load_chart` →
  `BarCache.get_bars` → `MarketDataManager.req_historical_data` (`TIMEFRAME_CONFIG`
  duration/bar size) → `IBApiClient.historicalData` → `_on_historical_bar` /
  `_on_historical_data_end` → `BarCache.save_bars` → `ChartPanel.update_chart` →
  `ChartPanel._refresh_candles` (shared by the price **and** volume panels).

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
| Genuine closure | A market-closed interval that is legitimately non-trading (weekend, actual US-equity holiday, or overnight). Stays **empty** per D16 (`AC-D16.3`). **Dec 31 of a year whose next Jan 1 is a Saturday is NOT a genuine closure** — it is a trading day (`AC-D16.7`, ESC-023). |
| Chart area | The central region of `MainWindow` holding the chart, excluding the docked panels (Watchlist on the left; the single Active Trader + Portfolio right dock). Panel caps in D17/D18 are percentages of **this** region (B1/B2), not of the whole window. |
| Chart-minimum rule | The hard floor (~400px) the chart area must keep, independent of the two docks (B3): each dock clamps against its own % **and** against the space left so the chart never drops below the minimum. Enlarging one dock can force the other to shrink. |
| Right dock (D18) | The **single** `RightDockWidgetArea` region containing the Active Trader ladder and the Portfolio section stacked vertically (B2). Because it is one region, its two sections are inherently equal width; the 40%-of-chart-area cap applies to the region as a whole. |

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
- **Steps:** 1) Hover the cursor over the price plot. 2) Read the price chip in the
  Y-axis lane to the right of the plot's vertical axis line.
- **Postconditions:** The full price, including all decimal places, is visible as a
  grey pill with white text in the Y-axis lane; it is never covered by the right-hand
  dock. Overlapping the Y-axis price tick label at the same price is expected and
  permitted.
- **Edge Cases:** A long price (`123,456.78`) does not bleed under the dock while the
  chip remains in the axis lane; hovering at the top/bottom edge keeps the chip in view;
  the chip is hidden when the cursor leaves the plot; a Y-axis tick label at the same
  price may sit underneath the chip by design.

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
  ticked at 1e6/1e7. **(Superseded by Journey 9 / D8: Y is linear from `0` with a
  dynamic nice max; retained for history.)**
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
- **Edge Cases:** All-zero volumes show `0–100` (smallest nice value, no fixed `10k`
  floor) with minimal bars; a max just below a nice boundary rounds up; small and large
  volumes remain distinguishable.

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
- **Edge Cases:** Multiple zones at nearby prices stack without full overlap; zoom/pan
  keeps labels at the right edge and at the correct price; a crosshair hovering at a
  drawing's price no longer collides — the chip is in the Y-axis lane and the drawing
  label is inside the plot (D2/Q33), so `AC-D11.4` covers label-vs-label stacking only;
  no drawing → no label.

### Journey 13 — D12: edit a zone via double-click
- **Preconditions:** A zone (rectangle) drawing exists on the chart.
- **Steps:** 1) Double-click the zone body. 2) Observe the Zone Settings popup. 3) Switch between Style/Text/Coordinates/Visibility tabs. 4) Change a value and apply.
- **Postconditions:** Double-click opens the `Rectangle` popup with four tabs; Extend is not shown (zone always extends both sides); changes are applied to the zone and re-render.
- **Edge Cases:** Double-click on a non-zone drawing does not open the zone popup; double-click with no selection does nothing; Cancel/X closes without change.

### Journey 14 — D13: resize watchlist panel to see more symbols/columns
- **Preconditions:** App is running; Watchlist dock is docked on the left; window is at default 1400×900.
- **Steps:** 1) Hover over the vertical splitter handle between Watchlist and chart. 2) Drag right to widen.
- **Postconditions:** Watchlist width grows, chart narrows, handle remains draggable across
  `[150, floor(0.50×chart_area)]` (and the chart-minimum rule from B3), clamped both **during the drag**
  and on window resize. **Superseded denominator (B1, 2026-10-03):** the cap is 50% of the **chart
  area**, not of `MainWindow` width as originally stated in Q25 — see `AC-D13.1` and A17.
- **Edge Cases:** At max 50%-of-chart-area the handle stops; at min 150px it stops; floating Watchlist is unconstrained.

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

### Journey 17 — D16: reload after a cache gap shows continuous history
- **Preconditions:** The SQLite `bars` cache holds `SPY` `5 mins` bars in two blocks separated by a
  missing trading-session span (reported repro: bars through Fri 2026-09-18, nothing
  2026-09-19…2026-09-27, bars 2026-09-28…now); the closure exceeded the timeframe's IBKR fetch
  window (for `5 mins`, `5 D`); IBKR is connected; Ext Hours is ON.
- **Steps:** 1) Launch the app. 2) Load `SPY` on `5 mins`. 3) Wait for the historical request(s)
  to complete. 4) Inspect the price panel and the volume panel.
- **Postconditions:** The displayed bar series is continuous over the span it covers — bars exist
  for every trading session from the oldest displayed bar through now (including the missing
  2026-09-21…2026-09-25 weekdays); the app backfills the whole gap, issuing additional request(s)
  when the gap exceeds one IBKR request's duration. The price candles **and** the volume bars both
  render across that span; the only empty x-intervals are genuine market closures (weekend,
  holiday, overnight), which stay empty and are not filled, compressed, or interpolated.
- **Edge Cases:** weekend/holiday/overnight render as empty and are **not** treated as missing
  data; a cache gap larger than IBKR's maximum single-request duration is bridged with multiple
  requests (chunking) or the shortfall is surfaced explicitly, never left as a silent hole; an
  **internal hole** (newer cached bars separated from an older block by a missing span — the
  reported repro) is healed, not only a hole after the newest cached bar; an empty cache fetches
  the configured window; a cache newer than now is not redundantly re-requested; symbol/timeframe
  switch while a backfill request is in flight does not mix symbols/timeframes; the same behaviour
  holds on every timeframe (`1 min`…`1 day`) and any symbol (Q39); **Dec 31 of a year whose next Jan 1 is a Saturday is a trading session, not a closure (e.g. 2021-12-31, 2027-12-31, 2032-12-31, 2038-12-31), so a hole there must be backfilled/surfaced like any other trading day (`AC-D16.7`, ESC-023)**.

### Journey 18 — D17: resize the Watchlist in full screen
- **Preconditions:** App is running (dev build, `python main.py`) shown **full screen**; Watchlist dock
  is docked on the left; chart is loaded; a thin splitter handle sits between the Watchlist and the chart.
- **Steps:** 1) Drag the splitter handle to the right. 2) Observe the Watchlist widen and the chart
  narrow. 3) Drag back to the left. 4) Drag past the cap. 5) Restart the app.
- **Postconditions:** The Watchlist widens continuously up to **50% of the chart area** (B1) and the
  chart narrows correspondingly; dragging back reduces it (both directions work — B4); at the cap the
  handle stops without pushing the chart below its ~400px minimum (B3); the width survives a restart
  (Q26 persistence still required — B4). The cap is enforced **during the drag**, not only on
  `resizeEvent`.
- **Edge Cases:** Window is already full screen (no window resize fires during the drag → the cap must
  still be enforced during/after the drag, not only on `resizeEvent`); floating Watchlist unconstrained;
  dragging below the minimum stops at 150px; the right dock being enlarged shrinks the watchlist's
  available space so its effective cap drops (B3 cross-clamping); restart restores the persisted width
  clamped to the current cap (50% of the current chart area).

### Journey 19 — D18: use the Active Trader (+ Portfolio) dock in full screen
- **Preconditions:** App is running shown **full screen**; the **single right dock** (Active Trader
  ladder with Portfolio stacked below) is visible on the right; a chart is loaded.
- **Steps:** 1) Observe the right-hand region in full screen. 2) Enlarge the right dock. 3) Observe the
  chart narrow. 4) Compare Active Trader and Portfolio widths.
- **Postconditions:** The single right-dock region (Active Trader + Portfolio) is entirely within the
  visible window area (not clipped/off-screen); enlarging it grows it up to **40% of the chart area**
  (B2/B3) and the chart area narrows; Active Trader and Portfolio render at **equal width** because
  they are two stacked sections of one region (B2).
- **Edge Cases:** Both left (watchlist) and right docks enlarged at once must not squeeze the chart
  below its minimum — each clamps against the remaining space so the chart keeps ~400px, and enlarging
  one can force the other to shrink (B3); cross-clamping is exercised in the criteria; small full-screen
  display; docks hidden/floating; ladder content wider than the dock must not force the dock off-screen.

## Acceptance Criteria (feature-level)

### Global (applies to every defect in this run)
- **Given** the repository at its current state,
  **when** all registered defect fixes are applied,
  **then** every defect's per-task test condition passes **and** the pre-existing
  test suite remains green.
- **Given** a change touching the live-order path,
  **when** tests are run,
  **then** no test connects to live TWS or transmits an order.
- **AC-G.1 (Visual reference gate — ESC-004)** Given a defect whose fix depends on a
  **UI-visual** decision (icon shape, placement, colour, dialog layout/tab content,
  label position, size), **when** the decision is considered clarified, **then** the
  Defect Register entry MUST carry a `Visual reference:` line naming a concrete
  artifact (screenshot/video/annotated mock, with a path or attachment reference) and
  that reference MUST be marked **confirmed by the user** *before* the fix enters
  implementation.
  - A prose-only description, or a reference the user has not confirmed, does **not**
    satisfy the gate; the decision stays open and must be logged in
    `open_questions.md` (do not mark the entry "clarified").
  - If no reference can be provided, the entry MUST instead state, in the
    Assumptions Log, that the decision is a **provisional assumption** and record the
    user as the confirmer with a date — and the fix may proceed only on that explicit
    basis.
  - **Applies now to:** D10 (volume toggle icon + placement), D12 (zone `Rectangle`
    dialog), D15 (horizontal line dialog), D2 (crosshair chip appearance/lane placement),
    and any future UI-visual defect. See Assumptions Log A21–A26 for the per-defect
    reference status of this run.
  - **Per-defect status 2026-09-27 (all confirmed):** D12 `CONFIRMED` (screenshots
    supplied/confirmed 2026-09-19); D15 `CONFIRMED` (screenshots supplied/confirmed
    2026-09-20); **D10 `CONFIRMED`** — icon/affordance is the text label `Volume` (Q31) and
    the placement at the **top left of the volume panel (bottom left of the price chart)**
    was confirmed by the user 2026-09-27 (A23); **D2 `CONFIRMED`** for appearance and lane
    placement (A25, 2026-09-27) with a scoped carve-out — **dock-open visibility** is **not**
    covered by the reference and remains a separately verified acceptance criterion
    (`AC-D2.1`) + edge case requiring independent Code Reviewer verification after Build.
    Every UI-visual decision for this run is now confirmed.

### Per-defect criteria
Defects D1–D3 (Batch 1, built), D4–D8 (Batches 2–4, all confirmed 2026-09-19), D9–D11 (Batches 5–6), D12 (Batch 7), D13–D15 (Batches 8–9) and **D16 (Batch 10, 2026-10-02, clarified — Q37–Q39 answered)** each carry their own Given/When/Then criteria and documented edge cases in the **Defect Register** below. Those criteria are the authoritative acceptance tests and are the "test conditions" referenced throughout.

## Defect Register

> Batch 1 (built): three defects reported 2026-09-19 (D1–D3), all clarified and
> built. Batch 2 (clarified 2026-09-19): three refinements confirmed — D4 zoom
> label 21px/position left of axis, D5 volume log lower 1.0 (**SUPERSEDED by D8**),
> D6 wick 1px vs body ≥4×. Batch 3 (clarified 2026-09-19): D7 time-axis 35% gap. Batch 4 (clarified
> 2026-09-19): D8 volume linear, no negatives, dynamic nice ticks, price-coloured.
> Batch 5 (clarified 2026-09-19): D9 volume spacing follow + D10 volume show/hide at
> top left of volume panel. Batch 6 (clarified 2026-09-19): D11 drawing price labels
> on inner right side. Batch 7 (clarified 2026-09-19): D12 zone double-click settings popup (Extend omitted). Batch 8 (clarified 2026-09-20): D13 watchlist resizable to 50% with persistence + D14 double-click row to load chart (identical to Load Chart, no-op on same symbol/disconnected). Batch 9 (clarified 2026-09-20): D15 horizontal line double-click settings popup. Batch 10 (clarified 2026-10-02): D16 historical-bar cache-gap backfill (Q37–Q39; ESC-023 calendar correction). **Batch 11 (D17 + D18, panel layout / resizing in full screen) — CLARIFIED AND FINALISED 2026-10-03 (B1–B4 answered 2026-10-03):** D17 watchlist drag both directions up to **50% of the chart area** (min 150px, default ~220px, persisted, cap enforced during the drag); D18 one right-dock region (Active Trader + Portfolio stacked) up to **40% of the chart area**, equal width by construction, full-screen visible; combined under the **independent-caps + ~400px chart-minimum** rule (B3). See D13/D17/D18, `AC-D13.1`, `AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`, A34–A36, R28–R31, and `open_questions.md` B1–B4 (answered). D17 supersedes/corrects D13's Q25 denominator (B1). **No blocking question remains.**

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
- **Area:** Chart panel → price-axis lane / Active Trader / Portfolio dock
- **Status:** clarified — criteria defined 2026-09-19; **placement + styling revised
  2026-09-27 (Q33 — see below)**. This revision **re-opens** the original D2 defect
  surface ("decimals covered by the element to its right"), so it MUST be independently
  re-verified by the Code Reviewer after Build — the Batch-1 fix cannot be assumed to
  still hold.
- **Visual reference (ESC-004 gate):** **CONFIRMED (2026-09-27).** The reference is the
  agreed target for D2's **appearance and lane placement** — the Y-axis lane to the right
  of the plot's vertical axis line, a **grey pill**, **white text**, and axis-tick-label
  overlap permitted. **NOT covered by this reference/confirmation:** **dock-open
  visibility** — the chip must not be hidden by the Active Trader / Portfolio dock. That
  remains a **separately verified acceptance criterion** (`AC-D2.1`) and an edge case, and
  because it re-opens the original D2 defect surface it requires **independent Code
  Reviewer verification after Build**. Gate status: **CONFIRMED for appearance/lane
  placement only** (see A25).
- **Reported:** the crosshair price label's decimal places are hidden behind the
  element to its right (the Active Trader / Portfolio panels).
- **Observed in code:** `ChartPanel._price_tag` is a scene `TextItem`; the Batch-1 fix
  right-aligned it **inside** the plot at `view_rect.right() - 2` with a `#94a3b8` fill
  and dark `#0d0f14` text. `anchor=(0, 0.5)` originally; right-aligned to `anchor=(1,
  0.5)` in the fix.

**Decisions (2026-09-19; placement + styling revised 2026-09-27 — Q33):**
- The chip renders to the **RIGHT of the plot's vertical axis line, in the Y-axis lane**
  (the same strip where the Y-axis price tick labels are printed). It is therefore
  **OUTSIDE the data area** — the opposite of the Batch-1 decision, which placed it
  **INSIDE** the plot at `view_rect.right() - 2`.
- **Style:** a **grey background pill with WHITE text** (replacing the current
  `#94a3b8` fill with dark `#0d0f14` text).
- **Axis-tick-label overlap is EXPECTED and REQUIRED:** the chip MAY paint over the
  Y-axis price tick label at the same price. No separation between the chip and the
  Y-axis tick label is required — do **not** add a deconfliction offset between them.
- **Dock-open visibility is a required acceptance criterion:** with the Active Trader
  and/or Portfolio dock open, the chip must **not** be covered by the dock. Because this
  re-opens the original D2 defect surface, it is an edge case that requires independent
  Code Reviewer verification (the Batch-1 inside-plot fix no longer applies).

**Acceptance Criteria (Given/When/Then):**
- **AC-D2.1** Given a loaded symbol and the cursor inside the price plot, When the
  price chip renders with the Active Trader and/or Portfolio dock open, Then the
  complete label including all decimals is visible as a **grey pill with white text
  positioned in the Y-axis lane to the right of the plot's vertical axis line**, and is
  **not covered by the dock**. Painting over a Y-axis price tick label at the same price
  is permitted and is **not** a failure.
- **AC-D2.2** Given pan or zoom, Then the chip stays in the Y-axis lane and continues
  to track the cursor's price; it is not covered by the right dock.
- **AC-D2.3** Given the cursor leaves the plot, Then the chip is hidden (existing
  behaviour retained).

**Edge Cases:**
- Long price strings (e.g. `123,456.78`) must not bleed under the dock while remaining
  in the axis lane.
- **Dock-open edge case (re-opened D2 — requires independent Code Reviewer
  verification):** with the dock open/expanded, the chip's full decimals stay visible —
  the chip is not covered by the dock, even though it now sits outside the plot.
- A Y-axis tick label at the same price is expected to be overlapped by the chip — this
  is by design, not a defect.
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

**ESC-002 transition semantics (magnifier ↔ drawing tool ↔ alarm) — decided/confirmed 2026-09-27 (Q35 + follow-up confirmations):**
- **Forward direction — CONFIRMED (Q35 option (a)):** invoking the magnifier while a
  drawing tool is active **cancels the in-progress drawing and enters `ZOOMING`**. The
  active drawing tool / in-progress draft is cleared and **discarded** — **no half-drawn
  artefact is left behind** (the draft is not silently committed). `ZOOMING` and
  `DRAWING` are therefore mutually exclusive router modes, and the explicit
  `RouterMode` state machine (`IDLE/DRAWING/ZOOMING/ALARM_PLACING`) with a single
  `_active_mode` encodes this as a requirement (`AC-D3.7`, forward).
- **Reverse direction — CONFIRMED 2026-09-27 (was provisional A26):** selecting a
  drawing tool while `ZOOMING` is active **exits `ZOOMING` and activates the drawing
  tool**. This mirrors the forward rule (one precedence rule both ways) and the existing
  precedent that alarm mode forces the draw tool back to `Cursor`. It is now a
  **requirement** (folded into `AC-D3.7`, reverse), **not** an assumption; Plan MUST
  encode it in the router transition table as required behaviour.
- **Alarm-mode activation cancels `ZOOMING` — CONFIRMED (decided 2026-09-27):** when alarm
  placement mode is activated while the router is in `ZOOMING`, the app **exits `ZOOMING`
  and enters alarm placement**. This supplies the expected behaviour for the named test
  `test_alarm_placement_blocks_zoom` — alarm placement **blocks/ends** an active zoom
  rather than being blocked **by** it. Recorded as `AC-D3.8`.
- **Magnifier invoked while `ALARM_PLACING` is active — REFUSE (Q36 option (b), answered
  2026-09-27):** invoking the magnifier while alarm placement mode is active does **NOT**
  enter `ZOOMING`. The router **stays in `ALARM_PLACING`**, alarm placement keeps priority,
  the pending alarm placement is **not cancelled**, and a **status-bar hint** is shown
  (e.g. "Finish or cancel alarm placement before zooming"). Recorded as **`AC-D3.9`**. This
  is the final cell required to make the `chart_mouse_router` **transition table total**
  (`ALARM_PLACING + magnifier → ALARM_PLACING`, no mode change) and is **REQUIRED
  behaviour** — it supersedes Plan's derived transition **TR-9** and assumption **PA-R1**
  (RG-003, now closed).

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
- **AC-D3.7 (ESC-002 — both directions, confirmed 2026-09-27)** Given a drawing tool and
  the zoom magnifier can both be activated, When a transition between them occurs, Then
  drawing and zoom are **never simultaneously active**:
  - **Forward (Q35 option (a)):** Given a drawing tool is active with an in-progress
    draft, When the magnifier is invoked, Then the drawing tool is cleared, the
    in-progress draft is discarded with **no half-drawn artefact left behind**, and the
    router enters `ZOOMING`.
  - **Reverse (A26 — now CONFIRMED; was provisional):** Given the router is in `ZOOMING`,
    When a drawing tool is selected, Then the router **exits `ZOOMING`** and activates the
    drawing tool. (Measurable: after selecting the tool, `_active_mode == DRAWING` and no
    zoom-selection gesture is active.)
- **AC-D3.8 (ESC-002 — alarm placement cancels `ZOOMING`; decided 2026-09-27)** Given the
  router is in `ZOOMING`, When alarm placement mode is activated, Then the router **exits
  `ZOOMING`** and enters **alarm placement**, and alarm placement is **not** blocked or
  deferred by the active zoom. (Measurable: after activating alarm placement,
  `_active_mode == ALARM_PLACING`; the named test `test_alarm_placement_blocks_zoom`
  encodes that alarm placement **blocks/ends** zoom rather than being blocked **by** it.)
- **AC-D3.9 (ESC-002 — magnifier is refused during alarm placement; Q36 option (b),
  answered 2026-09-27)** Given alarm placement mode is active (`_active_mode ==
  ALARM_PLACING`), When the magnifier is invoked, Then the router **stays in
  `ALARM_PLACING`**, it does **NOT** enter `ZOOMING`, the pending alarm placement is
  **not cancelled**, and a **status-bar hint** is shown. (Measurable: after the magnifier
  is invoked, `_active_mode == ALARM_PLACING`, no zoom-selection gesture is active, the
  pending alarm placement is unchanged, and the status bar displays the hint.) This is the
  cell that makes the ESC-002 router transition table **total** — the
  **`ALARM_PLACING → ZOOMING`** cell is **specified required behaviour**
  (`ALARM_PLACING + magnifier → ALARM_PLACING`), superseding Plan's derived **TR-9** /
  assumption **PA-R1**.

**Edge Cases:**
- Degenerate selection (near-zero width/height) → ignored, no zoom.
- Drag starting outside the plot → no selection.
- No bars loaded → controls are disabled / no-op.
- Zoom at range limits → clamped, app remains stable.
- Changing symbol/timeframe while magnifier is active resets mode to default cursor.
- Activating the magnifier while a drawing tool is active **cancels the in-progress
  drawing** (the draft is discarded, no half-drawn artefact is left behind) and enters
  `ZOOMING` — Q35 option (a); selecting a drawing tool while the magnifier is active
  **exits `ZOOMING` and activates the tool** — **CONFIRMED 2026-09-27** (A26; `AC-D3.7`
  reverse). Both rules keep `DRAWING` and `ZOOMING` mutually exclusive.
- Activating alarm placement mode while `ZOOMING` is active **exits `ZOOMING`** and enters
  alarm placement (decided 2026-09-27, `AC-D3.8`) — alarm placement is never blocked by an
  active zoom (`test_alarm_placement_blocks_zoom`).
- Invoking the magnifier while `ALARM_PLACING` is active **does not enter `ZOOMING`** — the
  router stays in `ALARM_PLACING`, keeps the pending alarm placement, and shows a
  status-bar hint (Q36 option (b), answered 2026-09-27; `AC-D3.9`). This makes the ESC-002
  transition table total.
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
- **Status:** **SUPERSEDED BY D8** (2026-09-19) — originally clarified 2026-09-19 with Q17 (log lower bound 1.0) confirmed; retained for history only.
- **Authoritative decision:** D8 (below) revises this defect to a **linear** Y axis with
  `yRange=(0, nice_max)` and bars coloured by price direction. **Do not implement D5 as
  written.** The details below are the superseded log proposal and are kept solely to
  record why it was changed; no criterion in this section is a live test condition.
- **Reported:** Volume panel linear Y makes small volumes invisible when a spike is
  present (see screenshot: spike at 16:00 dominates; 3e7 scale). User requested
  logarithmic Y.
- **Observed in code at time of report:** `volume_plot.getViewBox()` used linear mode
  (`yRange 0.0 .. max*1.1`) and `vol_h` used raw volume including `0`.

**Decisions confirmed 2026-09-19 (Q17) — SUPERSEDED by D8/Q20; do not implement:**
- Volume `ViewBox` is **always log on Y** (`setLogMode(y=True)`), X remains linear
  and linked to the price plot.
- Zero-volume bars mapped to **`1.0`** (minimal tick, not a gap) — confirmed lower
  bound `1.0`.
- Auto-range is **`yRange=(1.0, max_vol*1.1)`** where `max_vol` is the maximum of
  mapped volumes.

**Acceptance Criteria (Given/When/Then) — SUPERSEDED, not live test conditions:**
- **AC-D5.1 (superseded by AC-D8.1)** Given any loaded chart with volumes, When the volume panel renders,
  Then the ViewBox is in log mode on Y (`getViewBox().logMode == (False, True)`).
- **AC-D5.2** Given bars with zero volume, When `vol_h` is computed, Then the height
  is `1.0` and the volume `yRange` lower bound is `1.0`, not `0.0`.
- **AC-D5.3** Given a max volume, When auto-ranged, Then the upper bound is
  `max_vol*1.1` and small-volume bars are visibly distinct from the spike.

**Edge Cases (superseded — see D8 edge cases for the live ones):**
- All bars have zero volume → `max_vol` floor is `1.0`; range becomes `(1.0, 1.1)`.
- Very small vs very large volumes remain distinguishable on log scale; X remains
  linked to price plot and is unaffected; Reset refits the volume pane consistently.

> **Note:** Journey 6 (above) describes the superseded log behaviour and is retained
> only for historical traceability. The live journey is Journey 9 (D8) and the live
> criteria are `AC-D8.1`–`AC-D8.7`. The Batch-2 register header and Assumption A9 are
> annotated `SUPERSEDED by D8`.

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
- **AC-D6.4 (ESC-009 — high-DPI coverage)** Given the app renders at a device pixel
  ratio of `2` (`QT_SCALE_FACTOR=2` / `devicePixelRatio == 2`), When the candles
  render, Then the wick stays a cosmetic 1-device-pixel line and the body remains
  `>= 4` device pixels wide, so wick and body do not merge. Measurable: at DPR 2, the
  body’s device-pixel width is `>= 4` and strictly greater than the wick’s, with no
  rounding collapse to a single line.

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
- **Status:** clarified 2026-09-19 — criteria defined, Q20 confirmed — revises D5’s prior log decision; **criteria revised 2026-09-27** for the ESC-003/ESC-007/ESC-008 build fix (scaling nice formula, no `10k` floor, live ceiling)
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

**Decisions confirmed 2026-09-19 (Q20); nice-number family pinned 2026-09-27 (RG-002):**
- Volume `ViewBox` is **linear on Y** (`setLogMode(y=False)`, X stays linear/linked);
  `yRange=(0, nice_max)` where `nice_max` is `max_vol*1.1` rounded up to the next
  **nice value generated by a continuous scaling formula whose mantissa set is
  `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (`10 × 10^k` is the next decade's `1` and needs
  no separate mantissa) so the axis shows 3–5 ticks (e.g., max ~2.2M → `0, 500.0K, 1.0M,
  1.5M, 2.0M, 2.5M` as in the desired screenshot; max ~80K → `0, 25K, 50K, 75K, 100K`).
  - **RG-002 (resolved 2026-09-27):** the earlier `1 / 2 / 2.5 / 5 × 10^k` wording was
    **internally inconsistent** with this defect's own examples and the retained fixture
    — `1.5M`, `15M` and `750K` are `1.5×` and `7.5×` mantissas that the strict set
    **cannot produce**. Because **`1.5M` (the screenshot's `500.0K / 1.0M / 1.5M / 2.0M /
    2.5M` run) and `750K` are user-confirmed (Q20)**, the family is pinned to
    **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`**, which reproduces every confirmed value
    exactly. `AC-D8.1`, `AC-D8.4`, `AC-D8.5` and the D8 edge cases all use this one
    family. **Still true:** **no fixed `10k` floor** (smallest generated value `100`),
    **no fixed ceiling** (it scales as `10^k`), and the old fixed list is retained
    **only** as a regression-test fixture.
  - **Revises A12 (2026-09-27; family pinned by RG-002):** the earlier fixed list
    `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]` is **no
    longer the live rule** — it is retained only as a regression-test fixture. Every
    entry in it is a member of the pinned family, so the fixture stays valid for those
    values. Its `10k` floor and its coarse rounding above 10M are corrected by the
    scaling formula (ESC-003 / ESC-008). The floor is no longer `10k`; the smallest
    generated nice value is `100` (see the low-volume edge case below).
- Volume bars are **coloured by price candle direction** (`#34d399` when `close >=
  open`, `#f87171` otherwise) — matching `CandlestickItem` bodies. This revises the
  prior log decision; no toggle is proposed — linear is the sole mode.
- Y ticks are formatted as `500.0K / 1.0M` (one decimal for K, same for M) via the
  right-axis tick formatter; no negative ticks are ever shown.

> **Fixture note (RG-002 — retained regression fixture, `tests/test_volume_linear.py`):**
> with the family pinned, the retained fixture values that are **valid and stay** are
> `_nice_volume_max(80_000) == 100_000`, `_nice_volume_max(2_200_000) == 2_500_000`,
> `_nice_volume_max(1_050_000) == 1_500_000` (the RG-002 contested case — it **is**
> correct under the pinned family), and `_nice_volume_max(8_000) == 10_000`. The only
> **stale** expectation is `_nice_volume_max(0) == 10_000`, which must become **`100`**
> per `AC-D8.4` (smallest nice value, no `10k` floor). Build owns the test edit.

**Acceptance Criteria (Given/When/Then):**
- **AC-D8.1** Given any loaded chart, When the volume panel renders, Then the Y is
  linear (`logMode == (False, False)`), lower bound is `0`, no negative tick is
  shown, and the upper bound is the dynamic nice max — the **smallest value of the
  form `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (the pinned RG-002 family) that is
  `>= max_vol*1.1`, so it reproduces the user-confirmed `750K` and `1.5M`.
- **AC-D8.2** Given volumes, When bars render, Then each bar is green when its price
  candle has `close >= open` and red otherwise, and the yRange upper covers the max
  with the nice tick above it.
- **AC-D8.3** Given a max volume, When formatted, Then ticks appear as `10k / 100k /
  500.0K / 1.0M / 1.5M` etc., with `0` at the bottom and no `-200`.
- **AC-D8.4 (ESC-008 — fine low end)** Given a low-volume symbol, When the volume
  axis is computed, Then `nice_max` uses the **smallest value of the AC-D8.1 family
  (`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`)** that is `>= max_vol*1.1`, so for any
  `max_vol > 0` the ceiling satisfies `nice_max <= max_vol*1.1 * (1 + tolerance)`
  (tight, i.e. `nice_max / (max_vol*1.1) <= 2`), and no fixed `10k` floor is applied.
  - `nice_max(800) = 1000` (not `10_000`), `nice_max(3_000) = 5000` (not `10_000`);
    an 800–3,000 share symbol fills `>= 30%` of the pane (currently `< 30%`).
  - The floor for `max_vol == 0` is the smallest nice value, **`100`** (not `10k`).
- **AC-D8.5 (ESC-003 — fine high end)** Given a very large max volume (`40M–50M`),
  When `nice_max` is computed, Then it uses the same
  **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** family (AC-D8.1) with tight coverage — the
  smallest family value `>= max_vol*1.1`. Worked examples (each verified against the
  family): `10.5M → 15M`, `45M → 50M`, and `50M → 75M` (since `50M×1.1 = 55M` and the
  next family value is `75M`). A coarser ceiling such as `100M` is **not** acceptable
  while the tighter family value `75M` exists — this is precisely why the family keeps
  the `7.5` mantissa: the strict `1/2/2.5/5` set would overshoot `50M` to `100M`. The
  result is monotonic non-decreasing in `max_vol`, and the old fixed list is retained
  **only** as a test fixture.
- **AC-D8.6 (ESC-007 — live ceiling)** Given a loaded chart, When the forming last
  bar's volume grows past the initially computed `nice_max`, Then either the ceiling is
  recomputed/widened so the bar is not clipped, or the bound is explicitly documented
  and the bar never exceeds the Y range. (Measurable: after the live max doubles, the
  forming bar's rendered height is `<=` the pane top and `> 0`.)
- **AC-D8.7 (ESC-007 — timezone/refresh)** Given `set_timezone()` or any
  `_refresh_candles()` path with `auto_range=False`, When the volume range would be
  stale, Then the volume Y range is refit consistently with `AC-D8.6`.

**Edge Cases:**
- All bars have zero volume → `max_vol` floor is the smallest nice value **`100`**
  (not `10k`); yRange becomes `(0, 100)` and bars are minimal/gaps.
- Single bar with very small max (e.g., 800) → `nice_max = 1000`; ticks
  `0, 250, 500, 750, 1000`.
- Max just below a boundary (e.g., 1.05M) rounds up to the next
  `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` value (`1.5M`), not down; a max of exactly
  `10_000` no longer jumps to `50_000` (it rounds to `15_000`).
- Very large max (40M–50M) keeps a tight ceiling and stays monotonic (e.g.,
  `45M → 50M`, `50M → 75M`).
- Volume bars remain green/red even when price is a Doji (`open==close` → green).
- A live tick that grows the forming bar past the initial ceiling must not clip the
  bar (see `AC-D8.6`).

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
- **Status:** clarified 2026-09-19 — criteria defined, Q22 top left of volume panel; **updated 2026-09-27** — icon confirmed as the text label `Volume` (Q31) and **placement CONFIRMED** (A23, 2026-09-27)
- **Visual reference (ESC-004 gate):** **CONFIRMED (2026-09-27).** The **icon/affordance**
  is the **text label `Volume`** (Q31 — a checkable text-label toggle, not an eye icon or a
  bar glyph) and the **placement** — **top left of the volume panel (bottom left of the
  price chart)** — is likewise user-confirmed (A23, 2026-09-27). Gate status: **CONFIRMED**
  (see AC-G.1).
- **Reported:** User feedback 2026-09-19: allow the user to show/hide (toggle) the
  volume panel to maximize price-chart vertical space. No toggle exists today; the
  volume `PlotWidget` is always visible in the splitter.
- **Observed in code at time of report:** `volume_plot` is a `PlotWidget` in a
  vertical `QSplitter` with `price_plot` and `osc_plot`; it is always added and
  shown. No user-facing visibility control exists.

**Decisions confirmed 2026-09-19 (Q22 top left of volume panel); icon + placement confirmed 2026-09-27 (Q31, A23):**
- The toggle is a **checkable text-label control showing `Volume`** (Q31), default **visible**
  — not an eye icon or a bar glyph.
- **Placement (CONFIRMED 2026-09-27 — A23):** **top left of the volume panel** (bottom left of
  the price chart).
- Toggling hides/shows `volume_plot` (and its axis) and the `QSplitter` is rebalanced so the
  price plot expands when hidden. The toggle state is **not persisted** in this proposal
  (resets to visible on launch).

**Acceptance Criteria (Given/When/Then):**
- **AC-D10.1** Given the volume panel is visible, When the user toggles the `Volume`
  control (a checkable text label, Q31) at its **confirmed placement** (top left of the
  volume panel / bottom left of the price chart, A23 confirmed 2026-09-27), Then
  `volume_plot` becomes hidden and the price plot expands to fill the freed vertical
  space; toggling again shows it.
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
  offset to avoid overlap (or the topmost remains). **Revised 2026-09-27 (Q33 —
  ESC-006 re-scoped):** the crosshair price chip now lives in the **Y-axis lane outside
  the plot** (see D2), while D11 drawing labels remain **inside the plot at `x =
  view_rect.right() - 4`**. The two occupy **different lanes**, so the chip is **no
  longer included** in the label collision accounting; `AC-D11.4` now applies only to
  **label-vs-label stacking inside the plot**.

**Acceptance Criteria (Given/When/Then):**
- **AC-D11.1** Given any drawing with a price, When rendered, Then a price label
  is visible **inside the plot near the right edge** (`x = view_rect.right() - 4`,
  `anchor=(1,0.5)`) and is not clipped by the axis/dock.
- **AC-D11.2** Given a zone with top/bottom prices, When rendered, Then two labels
  are visible at the zone’s top and bottom edges on the inner right.
- **AC-D11.3** Given multiple drawings at nearby prices, When rendered, Then
  labels remain legible (small vertical offset, not fully overlapping).
- **AC-D11.4 (ESC-006 — re-scoped to label-vs-label; Q33 answered 2026-09-27)** Given
  multiple drawing price labels at (or within the label band of) each other's prices,
  When those labels render **inside the plot** near the right edge
  (`anchor=(1,0.5)`, `x = view_rect.right() - 4`), Then their text bounding boxes MUST
  NOT overlap: consecutive labels are offset by `>= 15 px` (the existing stacking
  threshold) and each remains fully inside `view_rect` on the right edge.
  - Measurable: for each consecutive pair of drawing labels,
    `abs(label_a_bbox.center().y() - label_b_bbox.center().y()) >= bbox_height`
    (their scene bounding rects do not intersect).
  - **The crosshair chip is out of scope for this criterion.** It now lives in the
    Y-axis lane outside the plot (see D2), so crosshair-vs-label overflow collision no
    longer applies; the earlier `>= 15 px` chip-vs-label requirement is retired. The
    Code Reviewer MUST **re-scope ESC-006** accordingly (label-vs-label only).
  - A label run longer than the pane height is still clamped to `view_rect.bottom()`;
    with lane separation this is a pure label-vs-label stacking concern, not a
    chip-vs-label priority question.

- **AC-D11.5 (ESC-009 — high-DPI coverage)** Given the app renders at device pixel
  ratio `2`, When drawing price labels render, Then each label’s scene bounding rect
  remains fully inside `view_rect` on the right edge (`x + width <= view_rect.right()`)
  and is not clipped by the axis/dock. Measurable at DPR 2: the label bbox is on-screen
  and within `view_rect`.

**Edge Cases:**
- Very narrow window or wide axis keeps labels inside (clamped to `view_rect`).
- Zooming/panning keeps labels at the right edge and at the correct price.
- High-DPI (DPR 2) keeps labels inside the plot and legible (AC-D11.5).
- No drawing → no label.
- Crosshair resting exactly on a drawing price is no longer a collision: the chip is in
  the Y-axis lane and the drawing label is inside the plot (D2 / Q33). The remaining
  label-vs-label stacking when a run exceeds the pane height stays as `AC-D11.4`.

### D12 — Zone double-click should open settings popup with 4 tabs (Extend omitted)
- **Area:** Drawings / `ui/drawing_overlay.py` + new `ui/drawings_dialog.py` (or `ui/zone_settings_dialog.py`)
- **Status:** clarified 2026-09-19 — criteria defined, Q24 Extend omitted confirmed — revises prior popup assumptions
- **Visual reference (ESC-004 gate):** Q24 confirmed the four attached screenshots as
  the spec (Style with `Extend` omitted, Text, Coordinates, Visibility). The visual
  reference for this defect is the **user-confirmed screenshots**; the one deliberate
  divergence from the reference (`Extend` dropped) is explicitly user-directed. Gate
  status: **CONFIRMED** (screenshots supplied and confirmed 2026-09-19).
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

### D13 — Watchlist dock resizable to 50% of the **chart area** with persistence
- **Area:** Watchlist dock / `ui/main_window.py`, `ui/watchlist_panel.py`
- **Status:** clarified 2026-09-20 (Q25/Q26) — **denominator SUPERSEDED/CORRECTED 2026-10-03 by B1**
  to **50% of the chart area** (was "50% of `MainWindow` width"); enforced during the drag (D17).
- **Supersession note (B1, 2026-10-03):** D17's report ("extend till **50% of the chart area**") is
  authoritative. The Q25 answer ("~50% of `MainWindow` width") is **corrected** so the cap is measured
  against the **chart area** (the central region excluding both docks), which matters once the right
  dock (D18) is visible. `AC-D13.1`–`AC-D13.3`, Journey 14, A17 and R15 are updated in lockstep; the
  D13 intent (freely draggable up to the cap, persisted) is unchanged.
- **Reported:** The watchlist panel should extend more so the user can see more
  symbols/columns; the current width is limited and is not remembered.
- **Observed in code at time of report:** the Watchlist is a `QDockWidget` in
  `LeftDockWidgetArea` (`ui/main_window.py`); its width was not explicitly bounded
  to a percentage and was not persisted across restarts.

**Decisions confirmed 2026-09-20 (Q26 persist yes); denominator corrected 2026-10-03 (B1):**
- Docked Watchlist is freely draggable **in both directions** up to **`floor(0.50 × chart_area)`**,
  additionally clamped by the **chart-minimum rule (B3)** so the chart area keeps **≥400px**; minimum
  watchlist `150px`; the clamp is applied **during the drag** as well as on window resize; floating
  geometry is unconstrained. Default width **~220px**.
- Watchlist width persists across restarts as an **integer pixel** value (e.g.,
  `QSettings watchlist/width` or a DB key); default **~220px** if none saved;
  restore is clamped to the current cap.

**Acceptance Criteria (Given/When/Then):**
- **AC-D13.1 (denominator corrected by B1)** Given a docked Watchlist at default width and a loaded
  chart, When the user drags the vertical splitter **either direction**, Then the watchlist width is
  clamped to `[150, floor(0.50 × chart_area)]`, further limited by the chart-minimum rule (`chart_area
  ≥ 400px`), the chart width adjusts, and the handle remains draggable across the range — **including
  during the drag** (not only on window resize).
- **AC-D13.2** Given a persisted width, When the app restarts, Then the watchlist
  restores to the persisted integer width clamped to the current
  `floor(0.50 × chart_area)` (default ~220px if none saved, never <150).
- **AC-D13.3** Given a wide watchlist and the width available to it shrinks (main window narrowed, or
  the right dock enlarged per B3), When the width would exceed the current cap, Then the watchlist is
  auto-clamped to the cap without error and remains resizable.

**Edge Cases:**
- Floating Watchlist is not constrained to 50%; docking it again re-applies the
  clamp.
- Extremely narrow windows keep `150px` watchlist and the chart minimum; if the window
  is smaller than the sum, the watchlist yields to the chart minimum.
- No saved width on first run uses ~220px.
- The right dock (D18) grows while the watchlist is at its cap → the watchlist is re-clamped
  (effective cap shrinks) per `AC-D18.5`/B3.

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
- **AC-D14.4 (ESC-010 — mid-drag symbol change)** Given a drawing is being dragged
  (a drag gesture is in progress on the chart), When the user double-clicks a watchlist
  row for a **different** symbol, Then the chart loads for the new symbol and **no
  `RuntimeError` / `RuntimeWarning` is raised** (the overlay's drag/draft state is
  cleared before the items are detached), and the chart renders normally afterward.
  - Measurable: running the mid-drag double-click against a drag-active overlay
    produces zero unhandled exceptions in the app's exception hook / pytest-qt
    `qt_log` and the new symbol's chart is displayed.

**Edge Cases:**
- Symbol case differences (`aapl` vs `AAPL`) are treated as the same symbol
  (case-insensitive comparison).
- Double-click during an in-flight load for a different symbol cancels that RT and
  loads the new symbol (existing `load_chart` behaviour).
- No symbols in the watchlist → double-click does nothing.
- Double-click a different symbol while a drawing drag is in progress → no crash
  (`AC-D14.4`); the defensive `dragItem` clearing must be exercised, not assumed.

### D15 — Double-click horizontal line should open settings popup with 4 tabs
- **Area:** Drawings / `ui/drawing_overlay.py` + new `ui/horizontal_line_settings_dialog.py` (or `ui/drawing_settings_dialog.py`)
- **Status:** clarified 2026-09-20 — criteria defined, Q30 correct
- **Visual reference (ESC-004 gate):** Q30 confirmed the four attached `Horizontal line`
  screenshots as the spec (Style `Line`, Text 12, Coordinates single `#1 (price)`,
  Visibility). Gate status: **CONFIRMED** (screenshots supplied and confirmed
  2026-09-20).
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

### D16 — Historical bars missing across a cache/reopen gap (price **and** volume panels)
- **Area:** Bar-load path — `ui/main_window.py::load_chart` / `_on_historical_bar` /
  `_on_historical_data_end`; `ibkr/market_data.py::MarketDataManager.req_historical_data`;
  `ibkr/client.py::IBApiClient.historicalData`; `data/bar_cache.py`; rendered by
  `ui/chart_panel.py::update_chart` / `_refresh_candles` (shared by price + volume).
- **Status:** **clarified — criteria finalised 2026-10-02 (Q37–Q39 answered).**
- **Visual reference (ESC-004 gate):** **N/A** — D16 is a data/behaviour defect, not a UI-visual
  decision; no visual reference is required and AC-G.1 does not apply.
- **Reported (2026-10-02, screenshot):** symbol `SPY`, TF `5 mins`, Mode `Candles`, Extended Hours
  ON, Eastern Time. Price candles are present 09/14–09/18, **entirely absent 09/19–09/27**, and
  resume 09/28–10/02. The **volume panel** is absent over the same span. 09/21–09/25 are normal
  trading weekdays, so this is not merely weekend session shading.
- **Observed in repository (validated against the current files, 2026-10-02):**
  - `load_chart()` shows cached bars, then issues **one** `req_historical_data` with
    `endDateTime=""` (up to now) and the fixed `TIMEFRAME_CONFIG` duration (`5 mins` → `5 D`);
    `_on_historical_data_end` then saves the fetched bars and re-reads **all** cached bars
    (`BarCache.get_bars`) — the union of the old cache and the last 5 days.
  - `_refresh_candles` frames `xRange` from `_bars[0].ts` to `_bars[-1].ts` and drives **both** the
    candle item and the volume bars from the same `self._bars` list, so a hole in the bar list
    shows as a hole in **both** panels. No separate volume fix is needed once the bar list is
    continuous.
  - `BarCache.get_last_timestamp(symbol, timeframe)` (`data/bar_cache.py:33`) returns `MAX(ts)` but
    is **not** used by `load_chart` (`ui/main_window.py:430–444` does not read it); the fetch is
    neither anchored to, nor sized to reach, the cached span.
  - **Empirically confirmed against the live SQLite cache** (read-only inspection of
    `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`, 2026-10-02): `SPY 5 mins`
    has 192 bars/day for 2026-09-14…09-18, then **no bars for 2026-09-19…2026-09-27**, then
    192/day for 2026-09-28…10-01 and 110 for 10-02. The hole is a real missing-bar span in the
    cache, not a rendering artefact, and it is **internal** (newer bars are already cached after
    it). (`AAPL 5 mins` similarly ends at 2026-09-18.)
  - **Root cause (diagnosis):** the delta fetch is anchored to **now** with a fixed duration and is
    **not** anchored to (or sized to reach) the cached span, so any closure longer than that
    duration leaves an unfetched span between the cache and `now − duration`. For `5 mins`
    (`5 D`) a >5-day closure produces exactly the observed hole. Git history shows the path:
    commit `2c5616c` changed Step 2 from `end_dt=last_ts+60` to `end_dt=""` (fixing a stale-cache
    *tail* gap) but did not enlarge the window to reach the cache or detect an internal hole. See
    `design_gaps.md` DG21.

**Decisions (2026-10-02 — Q37, Q38, Q39 answered):**
- **Q37 — backfill the whole gap.** On load, the app determines the missing span from the cached
  series to now and fetches enough history to make the bar list continuous, issuing **additional
  request(s) (chunking)** when the span exceeds one IBKR request's duration. Options (b) (drop/limit
  old cached bars so no hole shows) and (c) (fixed larger window on every load) are **not adopted**.
  It is not acceptable to display a range wider than the data fetched in a way that leaves a silent
  hole. Because the reported repro is an **internal** hole, "from the last cached bar" is
  implemented as filling the missing span **between cached blocks within the displayed range** (not
  merely the span after the newest cached bar) — see DG21.
- **Q38 — closures stay empty.** Genuine market closures (weekend/holiday/overnight) render
  **empty** and are **not** filled, compressed, or interpolated. D16 is scoped to missing
  **trading-session** bars only; no x-axis compressing/collapsing change is in scope (FS7).
- **Q39 — all timeframes + any symbol.** The fix and verification cover **all** timeframes
  (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and **any symbol**; `SPY 5 mins`
  is the reported repro only.
- **ESC-023 — trading-day calendar correction (2026-10-02):** the US-equity observed-day convention applies to New Year's Day **except** when the Saturday→preceding-Friday shift would place the closure on **Dec 31**, the year-end accounting date. Per **NYSE Rule 7.2**'s explicit year-end accounting-period exception, when Jan 1 is a Saturday **no New Year's holiday is observed** and **Dec 31 stays open**; no substitute closure is created (the Saturday Jan 1 itself is non-trading as a weekend). All other observed-shift cases are unchanged (Independence Day Sat→Fri, Christmas Sat→Fri / Sun→Mon, Juneteenth Sat→Fri, New Year's Sun→Mon). See `AC-D16.7`.

**Acceptance Criteria (Given/When/Then) — FINAL:**
- **AC-D16.1 (backfill the whole gap — all timeframes and any symbol; Q37/Q39)** Given a seeded
  `bars` cache whose series has a missing **trading-session** span between cached bars and now
  (tail gap **or** internal hole) and the elapsed closure exceeds the timeframe's fetch window,
  When the symbol/timeframe is loaded and all historical request(s) complete, Then the resulting
  bar list is continuous over the span from the oldest displayed bar through now — bars exist for
  every trading session, including every weekday in the missing span, with no artificial hole.
  - Measurable (offscreen, no live TWS): drive the real load path with a seeded cache and a
    stubbed historical feed; assert the resulting `ChartPanel._bars` (and `BarCache.get_bars`)
    contain the expected per-trading-day bar counts for the missing weekdays and that the maximum
    inter-bar gap **within** a trading session does not exceed one bar period. Run the assertion
    **parameterized over all six timeframes** (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`,
    `1 day`) and at least two symbols (Q39) — not `SPY 5 mins` alone.
- **AC-D16.2 (both panels; Q37)** Given the same scenario, When the chart renders, Then **both**
  the price candles and the volume bars are present across the backfilled span (the volume panel is
  not empty where the price panel has bars).
  - Measurable: the candle item data and the `volume_bars` `x`/`height` arrays both span the
    backfilled timestamps with non-zero heights; a bar-list hole and a volume-panel hole fail
    together.
- **AC-D16.3 (genuine breaks stay empty; Q38)** Given a genuine market closure (weekend, holiday,
  or overnight), When the chart renders, Then that interval is **empty** and is **not** counted as
  a missing-bar defect; no bar is fabricated or interpolated across it and the time axis is **not**
  compressed/collapsed. Only trading-session bars are required. **Dec 31 of a year whose next Jan 1 is a Saturday is NOT a genuine closure** and must not be treated as one — it is a trading day (`AC-D16.7`, ESC-023).
- **AC-D16.4 (bounded by IBKR availability; chunking; Q37/Q39)** Given the requested span exceeds
  what a single IBKR historical request returns (or exceeds IBKR retention), Then the app bridges
  it with additional request(s) where possible (respecting `pacing_manager`), and where data
  genuinely cannot be obtained the chart shows only the available bars and the shortfall is
  **surfaced explicitly** (e.g., status-bar message and/or log) — never a silent hole. No bar is
  ever fabricated to hide an unfillable gap.
- **AC-D16.5 (reported repro — date range spanning 2026-09-19→2026-09-28)** Given a seeded
  `SPY 5 mins` cache holding bars for 2026-09-14…2026-09-18 **and** bars for 2026-09-28…2026-10-02
  with the span 2026-09-19…2026-09-27 missing, and "now" = 2026-10-02, When `SPY` `5 mins` is
  loaded and requests complete, Then the bar list contains trading-session bars for **2026-09-21,
  09-22, 09-23, 09-24 and 09-25** (the missing weekdays), contains **no** bars for the weekend days
  2026-09-19/20 and 2026-09-26/27, and both the price candles and the volume bars render
  continuously across 2026-09-19→2026-09-28 modulo those genuine closures.
  - Measurable: per-weekday bar counts for 09/21–09/25 match the expected intraday cadence;
    `get_bars` for the weekend timestamps returns none; the volume `height` array is non-zero
    wherever a candle exists in the span.
- **AC-D16.6 (no regression)** Given the fix, When the full offscreen suite runs, Then it remains
  green and no existing acceptance criterion (D1–D15) regresses.
- **AC-D16.7 (trading-day calendar — New Year's year-end accounting exception; ESC-023, corrected
  2026-10-02)** Given the US-equity ET trading-day calendar, When `is_trading_day(date)` is
  evaluated for the last calendar day of a year whose next January 1 is a **Saturday** (i.e. Dec 31
  is that year's last trading day and the naive Saturday→preceding-Friday New Year's shift would
  otherwise close it — e.g. `2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31`), Then it
  returns **True**: that Friday is a **trading day**. The New Year's observed-day shift carries an
  explicit **year-end accounting-period exception** (NYSE Rule 7.2) and MUST NOT mark Dec 31
  closed, and MUST NOT substitute any other closure for it.
  - Measurable (offscreen, no live TWS): `is_trading_day(date(2021, 12, 31)) is True`, and likewise
    for `2027-12-31`, `2032-12-31` and `2038-12-31`; the following Monday of the Jan-1-Saturday
    year (e.g. `2022-01-03`) remains a trading day.
  - Unchanged (regression guard): the other weekend-falling fixed-date observed shifts remain
    closures — Independence Day Sat `2026-07-04` → Fri `2026-07-03` closed; Christmas Sun
    `2022-12-25` → Mon `2022-12-26` closed; Juneteenth Sat `2027-06-19` → Fri `2027-06-18` closed;
    and New Year's Day on a Sunday (e.g. `2023-01-01`) is still observed the following Monday
    (`2023-01-02` closed).
  - Consequence binding `AC-D16.1`/`AC-D16.4`: a genuine missing-bar hole on such a Dec 31 is a
    **missing trading session**, so it must be backfilled (`AC-D16.1`) or its shortfall surfaced
    explicitly (`AC-D16.4`) — **never** classified as a genuine closure and left as a silent hole.

**Correction record (ESC-023, 2026-10-02) — artifacts that must change:**
- **Task Manager:** the `T37-T03` acceptance criterion in `docs/tasks/task-graph.json` currently
  encodes "New Year's 2022-01-01 Saturday gives 2021-12-31 Friday closed" — this is **wrong** and
  must be corrected to the year-end accounting exception (`AC-D16.7`); its test description and
  expected result must change accordingly, and `2021-12-31`, `2027-12-31`, `2032-12-31`,
  `2038-12-31` must be asserted **trading days**.
- **Build:** `services/market_calendar.py::_observed` (as applied to New Year's Day) must not shift
  the closure onto Dec 31, and the `T37-T03` assertions in `tests/test_market_calendar.py` (which
  currently assert `is_trading_day(date(2021, 12, 31)) is False`, around `:105`–`:124`) must be
  updated to the corrected convention. The remaining observed-shift cases and their assertions stay
  unchanged.
- **Code Reviewer:** re-verify ESC-023 on the next pass.

**Edge Cases:**
- Internal hole (**the reported repro**) — newer cached bars separated from an older block by a
  missing trading-session span — must be healed, not only a tail gap after `MAX(ts)` (DG21).
- App closed for less than the fetch window → no hole today; must stay that way.
- App closed much longer than IBKR retention → the span cannot be filled; the chart must not
  fabricate or interpolate bars and must surface the shortfall (`AC-D16.4`).
- Ext Hours OFF vs ON changes `useRTH`; the backfill must respect the current setting and not
  leave a hole because of a mode switch.
- Symbol/timeframe switched while a backfill request is in flight → no cross-contamination
  (`_current_req_id` filtering already exists — verify), and the new symbol/timeframe still gets its
  own continuity treatment.
- Empty cache / brand-new symbol → fetch the configured window and render it.
- Cache end already at now (fresh) → no redundant requests; `INSERT OR REPLACE` dedupes any
  overlap.
- Weekend-only gap (cache ends Fri, reopened Mon) → must **not** be "filled"; renders as an empty
  weekend (`AC-D16.3`).
- A cache with a hole whose newest bar is older than the fetch window → covered by the same
  mechanism (tail gap).
- All timeframes and any symbol must behave identically (Q39), including `1 day` (which has a much
  wider configured duration).

### D17 — Watchlist dock will not extend/reduce in full screen (D13 resize not effective)
- **Area:** Watchlist dock / `ui/main_window.py` (`resizeEvent` clamp, `resizeDocks`, dock drag hook),
  `ui/watchlist_panel.py` (`watchlist_max_width` / `clamp_watchlist_width`).
- **Status:** **clarified 2026-10-03 — final criteria (B1, B4 answered).** D17 is a **defect in the
  built D13 behaviour**: the D13 intent is correct but not enforced. B1 **corrects D13's denominator**
  to 50% of the chart area (see D13 supersession note); B4 confirms the handle moves both directions,
  min 150px, default ~220px, persistence still required.
- **Visual reference (ESC-004 gate):** the user supplied a full-screen screenshot of the running app
  (2026-10-03) showing the narrow watchlist on the left with a thin drag handle and the chart occupying
  almost the whole width. This is accepted as evidence of the **reported state**; the target geometry is
  now **specified numerically** by B1/B4 (50% of chart area, min 150px, default ~220px, both drag
  directions) so no further visual reference is required — the target is a measurable geometry, not a
  visual-design choice (AC-G.1 does not require a screenshot for a numeric layout rule). Gate: **N/A
  for a visual reference**; geometry resolved by B1/B4 (see A34).
- **Reported (verbatim intent):** "the watch list section (left side) is too small and does not extend
  or reduce in width if user tries it. Fix: allow watch list section to be extended till 50% of the
  chart area. the chart area should become smaller if watch list is made bigger."
- **Observed in repository (validated 2026-10-03 against the current files):**
  - `WatchlistPanel.setMinimumWidth(WATCHLIST_MIN_WIDTH)` = 150px is set (`ui/main_window.py:225`);
    **no maximum width is ever set on the dock** and there is no `setMaximumWidth` anywhere.
  - The clamp helpers exist and are correct in isolation (`watchlist_max_width` = `max(150, min(int(W*0.50),
    W-400))`, `clamp_watchlist_width`), but they are applied **only** at construction and inside
    `resizeEvent`, and `resizeEvent` re-clamps **only when the dock is already wider than max**
    (`if self.watchlist_dock.width() > max_w`, `ui/main_window.py:962-968`). `resizeEvent` fires on
    *window* resize, **not** on a dock-splitter drag, so a user drag that stays within the window can
    move the dock freely and the cap is not enforced during the drag.
  - No `splitterMoved`/`dockLocationChanged` handler exists; nothing wires the dock's internal splitter
    handle to the clamp helpers, so D13's "handle remains draggable across the range" is **not actually
    enforced** — the likely root cause of "does not extend".
  - **Full-screen interaction:** `MainWindow` never calls `showFullScreen`; full screen is an OS window
    state. Because there is no width cap during a drag and no handler on drag completion, "in full
    screen" does not by itself disable resizing — but the reported symptom (narrow, non-resizing
    watchlist) is consistent with the drag not being clamped/bounded and the restore only running at
    construction/`resizeEvent`.
  - **Diagnosis:** a **defect in the built D13 behaviour**, not a wrong D13 intent — the D13 intent
    (freely draggable to the cap, persisted) stands; the built code does not enforce it during a drag.
    B1 additionally **corrects** D13's denominator from window width to chart area (superseded in D13).

**Decisions confirmed 2026-10-03 (B1 + B4):**
- **Cap denominator (B1):** the watchlist maximum width is `floor(0.50 × chart_area)` — measured against
  the **chart area**, not `MainWindow` width. This **supersedes D13's Q25 denominator** and is applied
  in `AC-D13.1`.
- **Both drag directions (B4):** the splitter handle must drag **wider and narrower** between the
  minimum and the cap. Minimum stays **150px**; default stays **~220px**; the persisted width (D13/Q26)
  is **still required**.
- **Enforcement during the drag (D17 root cause):** the cap must be enforced **while the user drags**
  (reusing `watchlist_max_width` / `clamp_watchlist_width` as the single source of truth), not only in
  `resizeEvent`.
- **Chart-minimum coupling (B3):** the effective cap is additionally bounded so the chart area keeps
  **≥400px** and the right dock (D18) is accounted for — see `AC-D18.5`.

**Acceptance Criteria (Given/When/Then) — FINAL:**
- **AC-D17.1 (drag wider; 50%-of-chart-area cap; B1)** Given a docked Watchlist and a loaded chart,
  When the user drags the splitter handle to the **right**, Then the watchlist width grows continuously
  up to `floor(0.50 × chart_area)` and the chart area narrows correspondingly. (Measurable: watchlist
  width `<= floor(0.50 × chart_area)` at all times during and after the drag; the width increases
  monotonically with the drag.)
- **AC-D17.2 (drag narrower; both directions work; B4)** Given the watchlist is wider than its minimum,
  When the user drags the handle to the **left**, Then the watchlist width **reduces** continuously down
  to **150px** and stops there, with the chart area growing correspondingly. (Measurable: the width
  decreases with a leftward drag, and never goes below `150px`.)
- **AC-D17.3 (cap enforced during the drag in full screen; the D17 root cause)** Given the app is shown
  **full screen** (no window `resizeEvent` fires during the drag), When the user drags past the cap,
  Then the width **stops at the cap** during the drag itself — not merely re-clamped later on a window
  resize — and the app remains stable with no overshoot into the chart. (Measurable: perform the drag
  without any window resize and assert the final width equals the cap, not the pre-clamp width.)
- **AC-D17.4 (persistence; Q26 still required; B4)** Given a Watchlist width persisted by a previous
  session, When the app restarts, Then the width is restored as the persisted integer pixel value,
  clamped to the current `floor(0.50 × chart_area)` and the chart minimum (default ~220px if none saved,
  never <150px).
- **AC-D17.5 (re-clamp on available-space change; B3)** Given the watchlist is at/near its cap, When the
  available chart-area width shrinks (main window narrowed **or** the right dock enlarged), Then the
  watchlist is re-clamped to the new cap without error and remains resizable.
- **AC-D17.6 (regression)** Given the fix, Then the pre-existing D13 acceptance criteria
  (`AC-D13.1`–`AC-D13.3`, updated in lockstep per B1) and `test_d10_d13_integration.py` remain green
  (or are updated in lockstep where B1 changes the denominator — never left contradicting D17).

**Edge Cases:**
- Floating watchlist: **unconstrained** (per D13); re-docking re-applies the cap.
- Extremely narrow window keeps the watchlist min (150px) and the chart minimum (~400px); if the window
  is smaller than the sum, the watchlist yields to the chart minimum.
- Dragging below the minimum stops at **150px**.
- Restart restores the persisted width clamped to the current cap.
- Right dock (D18) enlarged while the watchlist is at its cap → the watchlist is re-clamped (its
  effective cap shrinks) so the chart keeps its minimum (`AC-D18.5`/B3).
- Cap sits between min and default-invalid cases: a window/chart area so small that `floor(0.50 ×
  chart_area) < 150px` → the 150px minimum wins, and the chart-minimum rule still applies.

### D18 — Active Trader (+ Portfolio) right dock not visible in full screen; 40% / equal-width sizing (NEW)
- **Area:** Active Trader / Portfolio right dock / `ui/main_window.py` (`RightDockWidgetArea` setup),
  `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py`.
- **Status:** **clarified 2026-10-03 — final criteria (B2, B3 answered). NEW requirement (not covered
  by any existing defect).** B2 makes Active Trader + Portfolio **one right-dock region** (both sections
  stacked), so the 40% cap applies to that region and the two sections are equal width by construction.
  B3 gives the combined rule: independent caps + chart minimum, so enlarging one dock can force the
  other to shrink.
- **Visual reference (ESC-004 gate):** the user supplied a full-screen screenshot (2026-10-03) showing
  the right side clipped off-screen — "Active Trader" title truncated at the far right ("Active Tra..."),
  with "Ladder / Ask Size" headers and a mostly empty ladder, then a "Portfolio" section ("Account
  su..." + column headers). This is accepted as evidence of the **reported state**. The target is a
  measurable layout (one region, 40% cap, on-screen, equal width), specified numerically by B2/B3, so
  no further visual reference is required (AC-G.1 N/A for a numeric layout rule). Gate: **N/A for a
  visual reference**; geometry resolved by B2/B3 (see A35).
- **Reported (verbatim intent):** "the right side is the active trader section, it does not even be
  visible to user if the app is made full screen. fix: active trader section should reposition so that
  it fits in the visible area of the full screen. also, if user wants the user should be able to
  increase the size of active trader section till 40% of the chart area. active trader section and
  portfolio should have same width. The chart area should become smaller if active trader section is
  made bigger."
- **Observed in repository (validated 2026-10-03 against the current files):**
  - `ActiveTraderPanel` and `ActivePortfolioPanel` are currently added as **two separate `QDockWidget`s**
    in `RightDockWidgetArea` (`ui/main_window.py:234-252`). Neither panel sets any
    `setMinimumWidth`/`setMaximumWidth`/`setMinimumSize`/`sizeHint`, and **no `resizeDocks` call is
    made for either right dock** — unlike the watchlist, they get no explicit width at all.
  - There is **no 40% rule, no equal-width rule, no chart-shrink coupling, and no full-screen
    reposition/visibility handling** anywhere in the codebase (searched: no `showFullScreen`,
    `setWindowState`, `WindowFullScreen`, or full-screen branch exists in `ui/`).
  - Both docks are user-hidden by default in the existing integration tests
    (`tests/test_d10_d13_integration.py:33,50-52`), confirming they are an **independent horizontal
    consumer** that the current D13 clamp does not account for — the existing clamp uses the whole
    window width, not the width left after the right region.
  - This is a **new requirement**, distinct from D13.

**Decisions confirmed 2026-10-03 (B2 + B3):**
- **One right-dock region (B2):** Active Trader and Portfolio are **one right-dock region** containing
  both sections **stacked vertically**. They are therefore **inherently equal width** (the region's
  width); the **40%-of-chart-area cap applies to that single region**. The current two-`QDockWidget`
  structure is a wrong shape for this requirement and is expected to become a single region/container
  (with the two panels stacked inside) — the exact implementation is Plan/Build's call, but the
  behaviour must satisfy the criteria below.
- **Combined width rule (B3):** the watchlist (50% of chart area) and the right region (40% of chart
  area) have **independent caps**, each **additionally clamped against the remaining space** so the
  chart area keeps a **minimum (~400px)**. Consequently, enlarging one dock **can force the other to
  shrink**; both cannot sit at their individual maxima if that would starve the chart.
- **Full-screen visibility (reported defect):** the right region must be fully within the visible
  window in full screen (not clipped/off-screen), and content minimums (ladder/portfolio) must not
  force it off-screen.

**Acceptance Criteria (Given/When/Then) — FINAL:**
- **AC-D18.1 (full-screen visibility; reported defect)** Given the app is shown **full screen**, When
  the chart and the right region render, Then the right region (Active Trader ladder + Portfolio) is
  **fully within the visible window area** — its left edge `>= chart area right edge` and its right edge
  `<= window right edge`, with a **non-zero visible width** — and is on-screen **without manual
  repositioning**. (Measurable: assert the dock's `geometry()` lies within the window's `rect()` and
  `width() > 0` in an offscreen full-screen-sized window.)
- **AC-D18.2 (grow up to the 40%-of-chart-area cap; chart shrinks)** Given the right region is visible,
  When the user enlarges it (drag the handle / `resizeDocks`), Then its width grows continuously up to
  `floor(0.40 × chart_area)` and the **chart area narrows correspondingly**. (Measurable: right-region
  width `<= floor(0.40 × chart_area)` during and after the resize; chart width decreases as the region
  grows.)
- **AC-D18.3 (equal width by construction; B2)** Given the single right region is visible, Then the
  Active Trader ladder section and the Portfolio section render at **equal width** — i.e. each section's
  width equals the region's content width (they are stacked in one region). (Measurable: `active_trader
  section width ≤ region content width` and `portfolio section width ≤ region content width`, and the
  two sections' widths are equal within a 1px tolerance.)
- **AC-D18.4 (reduce direction + stop at cap and minimum)** Given the right region is at/near its cap,
  When the user drags further to enlarge, Then the width **stops at the cap** with no overshoot; When
  the user drags to shrink, Then the region reduces down to its minimum and stops. (Measurable: no
  resize leaves the width above the cap or below the minimum.)
- **AC-D18.5 (combined cross-clamping; chart minimum; B3)** Given both the watchlist and the right
  region are enlarged, When their combined width would push the chart area below its **~400px**
  minimum, Then **both** docks are clamped so the chart area stays `>= 400px`; enlarging one dock
  **forces the other to shrink** rather than letting the chart collapse. (Measurable: set both docks
  near their individual maxima, then enlarge one; assert `chart_area >= 400px` and the other dock's
  width decreased.)
- **AC-D18.6 (content must not push the dock off-screen)** Given the ladder/portfolio content is wider
  than the region (e.g. a wide ladder), When the region renders, Then the region's own geometry still
  satisfies `AC-D18.1`/`AC-D18.2` — content minimums do not force it past the window edge or past the
  cap. (Measurable: with wide content, the region's `width()` and right edge still satisfy the
  visibility + cap assertions; content scrolls/clips internally instead.)
- **AC-D18.7 (persistence — non-blocking default)** Given the app restarts, Then the right region's
  width/visibility is restored **only if persistence is specified**; the **default is not persisted**
  (A36), matching D10's volume-toggle precedent. *(Non-blocking default — see A36; not a blocking
  question.)*
- **AC-D18.8 (regression)** Given the fix, Then the pre-existing suite remains green and D13's
  watchlist behaviour is unchanged except where B3 explicitly couples the two.

**Edge Cases:**
- Both left (watchlist) and right docks enlarged at once → each clamps against the remaining space so
  the chart keeps its minimum; enlarging one can force the other to shrink (`AC-D18.5`, B3).
- Full screen on a small display (e.g. laptop) → the region still fits (`AC-D18.1`) and the chart keeps
  its minimum; on a very small window the chart minimum wins and the dock is capped accordingly.
- Docks hidden/detached (floating) → floating geometry is **unconstrained**; re-docking re-applies the
  cap. Content minimums must not force the dock off-screen (`AC-D18.6`).
- Ladder/portfolio content wider than the dock → dock must not be forced off-screen (`AC-D18.6`); the
  screenshot's clipped ladder suggests an unbounded content width today.
- A window small enough that `floor(0.40 × chart_area) < region minimum` → the region minimum wins, and
  the chart-minimum rule still applies.

## Assumptions Log
| # | Assumption | Rationale | Confirmed? | Date |
|---|---|---|---|---|
| A1 | This repo is the Python reimplementation of the React reference app | Consistent across `dev_docs/delta.md` and `PENDING_IMPLEMENTATION_PLAN.md` | n | 2026-09-19 |
| A2 | Phases 1–10 of `PENDING_IMPLEMENTATION_PLAN.md` are effectively implemented | All referenced modules and tests exist on disk | n | 2026-09-19 |
| A3 | Defects are diagnosed against the dev build (`python main.py`), not the packaged `.app` | Dev build is the working target; bundle untested per-defect unless stated | n | 2026-09-19 |
| A4 | "Test conditions pass" means the existing offscreen suite plus new per-defect checks | Q3 + Q8 confirmed + repo test conventions | y | 2026-09-19 |
| A5 | D2 chip keeps current 2-decimal format, or matches axis tick precision if that differs | Decimals still unspecified; **placement since revised by Q33** (chip moved to the Y-axis lane, grey pill + white text) — see D2/A25. The original "option (a)" inside-plot right-alignment no longer applies | n | 2026-09-19 (placement revised 2026-09-27) |
| A6 | D3 magnifier reverts to Cursor when symbol/timeframe changes | Not stated by user; safety default | n | 2026-09-19 |
| A7 | D1 exact orange/blue hex picked to match the app theme at 10% alpha | User specified colour name + opacity only | n | 2026-09-19 |
| A8 | D4 glyph size is 14px/700 for `-`/`+`/`Reset` and 21px/700 for `⌕` (magnifier 50% larger), and the inside-data-area position is `panel.width - ctrl.width - axis_width - 12` | Q15 confirmed with magnifier +50% (21px vs 14px); Q16 confirmed current fine | y | 2026-09-19 |
| A10 | D6 wick is ~1px thin line behind the body (body ≥4× wick), colour follows direction, wick extends beyond body when shadow exists | Q18 confirmed 2026-09-19 | y | 2026-09-19 |
| A9 | ~~D5 volume log is always on, X stays linear, zero-volume bars map to 1.0 with yRange lower 1.0~~ **SUPERSEDED by A12 (D8 linear)** | User said "y-axis needs to be logarithmic" without specifying toggle or zero handling — later rejected in favour of linear (Q20) | n (superseded) | 2026-09-19 |
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
| A21 | **ESC-004 visual gate applied:** a UI-visual decision is only "clarified" once its Defect-Entry `Visual reference:` line names a concrete artifact and the user has confirmed it; otherwise it is a provisional assumption recorded here | Process fix for the D5→D8 rework (screenshot arrived after build); see AC-G.1 | n | 2026-09-27 |
| A22 | D10 volume toggle **icon/affordance** is the **text label `Volume`** (a checkable text-label control), confirmed by the user — not an eye icon or a bar glyph | Q31 answered 2026-09-27 (user chose the text label `Volume`) | y | 2026-09-27 |
| A23 | D10 volume toggle **placement** is the **top left of the volume panel (bottom left of the price chart)** — **CONFIRMED 2026-09-27** (flipped from provisional) | Q22 named the location; Q32 originally accepted it as provisional; the user confirmed the placement on 2026-09-27 | y | 2026-09-27 |
| A24 | D8 volume `nice_max` is generated by a continuous scaling formula whose mantissa set is **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (pinned by RG-002, resolved 2026-09-27, to reproduce the user-confirmed Q20 values `750K` and `1.5M`), not the original fixed list. **No fixed `10k` floor** (smallest generated value `100`) and **no fixed ceiling** (scales as `10^k`). The old list is retained **only** as a test fixture. | ESC-003/ESC-008 fix; RG-002 resolved 2026-09-27 — the family is pinned by confirmed Q20 evidence, so no further user confirmation is needed for the value set. Supersedes A12's list and removes the D8 10k floor | n | 2026-09-27 |
| A25 | D2 chip **appearance and lane placement** (Y-axis lane outside the plot, right of the vertical axis line; grey pill with white text; axis-tick-label overlap permitted) is **CONFIRMED 2026-09-27** — the reference is the agreed target. **Scoped carve-out:** **dock-open visibility** (the chip must not be hidden by the Active Trader / Portfolio dock) is **NOT** covered by this reference and remains a separately verified acceptance criterion (`AC-D2.1`) + edge case requiring independent Code Reviewer verification after Build | Q33 answered 2026-09-27 by a design change; the user confirmed the appearance/placement reference on 2026-09-27 | y (appearance/placement) — dock-open visibility separately verified | 2026-09-27 |
| A26 | **ESC-002 reverse direction (Q35):** selecting a drawing tool while the router is in `ZOOMING` **exits `ZOOMING` and activates the drawing tool**. Now a **requirement** (folded into `AC-D3.7` together with the forward direction), **CONFIRMED 2026-09-27** (flipped from provisional) | Originally carried as an assumption because only the forward direction had been answered; the user confirmed the reverse rule on 2026-09-27. Plan MUST encode it in the router transition table as required behaviour, not as an assumption | y | 2026-09-27 |
| A27 | **D16 diagnosis:** the hole is caused by the delta fetch being anchored to *now* with the fixed `TIMEFRAME_CONFIG` duration instead of reaching the cached span / detecting a missing span; both the price and volume panels consume the same `_bars` list, so one bar-list fix serves both | Validated against the live `SPY 5 mins` cache (internal hole 2026-09-19…09-27 with newer bars 09/28+) and the current `load_chart`/`_refresh_candles` code; `get_last_timestamp` exists but is unused | y (repo-validated 2026-10-02) | 2026-10-02 |
| A28 | IBKR will actually return the missing 5-min bars for 2026-09-21…2026-09-25 (the hole is within IBKR's intraday retention), so the backfill can fill it; if not, `AC-D16.4` applies (shortfall surfaced, no fabrication) | The span is ~1–2 weeks old at report time; IBKR normally retains 5-min data far longer. Not user-confirmable — a data-availability risk, not a requirements ambiguity | n | 2026-10-02 |
| A29 | Genuine non-trading spans (weekend/holiday/overnight) render **empty** and are **not** compressed or filled; only missing **trading-session** bars count as the defect | **Q38 answered 2026-10-02** — user confirmed "stay empty"; collapsing non-trading time is out of scope (FS7) | y | 2026-10-02 |
| A30 | The D16 fix and its verification apply to **all** timeframes (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and **any symbol**, not only `SPY 5 mins` | **Q39 answered 2026-10-02** — user confirmed "all timeframes + any symbol"; the fetch-window mechanism is timeframe-generic (`TIMEFRAME_CONFIG`) | y | 2026-10-02 |
| A31 | Live/real-time bars are not persisted to the cache (only historical fetches call `BarCache.save_bars`); this is not the cause of the reported hole but is a related latent gap (see `design_gaps.md` DG18) and does not change D16, because the load-time backfill covers it | Code inspection: `_on_aggregated_bar` → `update_last_bar` only touches the in-memory `_bars`; only `_on_historical_data_end` calls `save_bars` | n | 2026-10-02 |
| A32 | The Q37 phrase "from the last cached bar up to now" is implemented as an **outcome** requirement — the bar series is continuous over its displayed span — which necessarily heals the reported **internal** hole, not only a tail gap after `MAX(ts)` (a tail-only anchor would leave the reported hole unfixed) | The user's own goal in Q37 was "so the chart is continuous"; the reported repro is an internal discontinuity; recorded in `design_gaps.md` DG21 and observed by `AC-D16.1`/`AC-D16.5` | y (derived from Q37) | 2026-10-02 |
| A33 | **ESC-023 correction — New Year's year-end accounting exception:** the US-equity New Year's observed-day shift does not apply when the preceding Friday is Dec 31; **Dec 31 is a trading day** when Jan 1 of the next year is a Saturday, and **no New Year's holiday is observed**. Only **actual** market holidays (shifted normally) and weekends are genuine closures | Code Reviewer ESC-023 (a naive Saturday→preceding-Friday shift closed Dec 31; wrong for US equities — NYSE Rule 7.2 year-end accounting-period exception; NYSE's own calendar states no New Year's Day holiday is observed when Jan 1 is a Saturday); user approved the correction 2026-10-02 | y (approved for correction 2026-10-02) | 2026-10-02 |
| A34 | **D17 target geometry — RESOLVED (B1, B4).** The watchlist cap is `floor(0.50 × chart_area)` (B1; **supersedes D13's Q25 window-width denominator**), the handle drags **both directions** (B4), min **150px**, default **~220px**, persistence still required (Q26), and the cap is enforced **during the drag** (not only on `resizeEvent`). Chart minimum ~400px per B3. | B1/B4 answered by the user 2026-10-03; B1 explicitly corrected the Q25 denominator | y | 2026-10-03 |
| A35 | **D18 grouping — RESOLVED (B2).** Active Trader and Portfolio are **one right-dock region** containing both sections stacked vertically, so they are inherently equal width; the **40%-of-chart-area** cap applies to that single region. The current two-`QDockWidget` structure is re-shaped into one region. | B2 answered by the user 2026-10-03 ("one right-dock region, stacked — Recommended") | y | 2026-10-03 |
| A36 | **D18 persistence default (non-blocking, UNCHANGED):** the right region's width/visibility is **not persisted** unless the user asks, matching D10's volume-toggle precedent (Q22: not persisted). B3/B4 did not add a persistence requirement for the right dock (only the watchlist keeps Q26 persistence, per B4). | D13 explicitly required persistence for the watchlist (Q26) and B4 re-confirmed it, but the user did not request it for the right region; recorded as a non-blocking default (not a blocking question) | n | 2026-10-03 |

## Documentation Maintenance Requirements

> Added 2026-09-27 to resolve **ESC-011** (documentation drift) and to carry the
> ESC-004 process gate. These are requirements on the *repository's own docs*, not on
> shipped code; the Requirements Analyst records them here because the owning files
> (`usage.md`, `PENDING_IMPLEMENTATION_PLAN.md`) are root-level docs the Analyst does
> not edit.

- **DOC-1 (test count/timing accuracy, ESC-011):** `usage.md` and
  `PENDING_IMPLEMENTATION_PLAN.md` MUST NOT state a test count or runtime that
  differs from a measured run at the current revision.
  - **Measured 2026-09-27 at `09070e8`:** `QT_QPA_PLATFORM=offscreen python -m pytest
    tests/` → **339 passed in 2.87s**.
  - **Stale values to correct:** `usage.md:166` "Full suite (269 tests, ~1.5s)";
    `PENDING_IMPLEMENTATION_PLAN.md:364`, `:412`, `:458` "269 passed".
  - **Recommended correction:** update each to **339 tests / ~2.9s** (or replace the
    hard-coded numbers with a pointer to the CI/build log so they cannot drift again).
- **DOC-2 (phase completion markers, ESC-011):** `PENDING_IMPLEMENTATION_PLAN.md`
  MUST carry a completion marker that matches reality for every phase whose target
  files exist. Phases 1–5 (`:69`, `:129`, `:172`, `:213`, `:243`) currently have **no
  marker** although `ui/drawing_overlay.py`, `ibkr/market_depth.py`, `ibkr/orders.py`,
  `ui/active_trader_panel.py`, `ui/stop_loss_target_dialog.py` exist.
  - **Correction (decided 2026-09-27, Q34):** mark Phases 1–5 as `✅ COMPLETE` (matching
    the `Phase 6`/`Phase 7` style).
  - **Ownership split (Q34):** the **Requirements Analyst owns closing DOC-2** (this
    requirement and the mark-complete correction); **Code Reviewer verification is the
    confirming step** — Code Reviewer confirms the drift and then verifies the correction
    was applied (see ESC-011).
  - **Dependency note:** `PENDING_IMPLEMENTATION_PLAN.md` is **not in the Analyst's
    file-ownership table**, so the Analyst records the requirement and the ownership split
    here rather than editing that root doc. If a user/owner action is still needed to
    physically apply the `✅ COMPLETE` markers, that is a **recorded dependency**, not a
    blocking open question (Q34 is answered; DOC-2 is Analyst-owned to close).
- **DOC-3 (no orphaned build artifacts, ESC-011):** the source-less
  `tests/__pycache__/test_db_schema.cpython-311-*.pyc` must be removed and the
  corresponding `tests/test_db_schema.py` committed as source (tracked by **ESC-001**,
  owned by BUILD).
- **DOC-4 (markdown-history retention):** superseded requirement sections (e.g., D5)
  are kept for history but MUST carry an explicit `SUPERSEDED BY <defect>` marker and
  a one-line pointer to the authoritative section, so no reader can mistake them for
  live criteria (this is the fix applied for **ESC-012**).

## Risks / Unknowns
| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | More defects may be reported after batch 1, expanding scope mid-build | M | M | Batch 1 declared complete; new feedback triggers a fresh requirements pass, not silent scope growth |
| R2 | Plan doc checkmarks are stale (many unchecked phases are actually built) | M | H | Verify actual behavior before treating any plan phase as open |
| R3 | Any change may touch the live-order path (real money) | H | M | TWS-side gating active (Q4); no automated test may transmit orders (Q9) |
| R4 | Vague UI defects ("looks wrong") yield untestable criteria | M | H | Every defect must have measurable Given/When/Then criteria and an edge case |
| R5 | Fixing one UI defect may regress another (shared chart/dock code) | M | M | Re-run full suite per fix; note regression risk per defect |
| R6 | D4 axis width varies with price magnitude; fixed 28px margin may still clip | M | M | Position left of dynamic `getAxis('right').width()` with 12px margin and `x>=8` clamp |
| R7 | ~~D5 log scale cannot display 0~~ **Resolved by D8** (linear axis, lower bound `0`); retained for history | — | — | Superseded by D8/Q20: linear `yRange=(0, nice_max)` has no zero-display problem |
| R8 | D6 wick/body thickness ratio may still be indistinct at extreme zoom/density | M | M | Fix wick at 1px regardless of zoom; body narrows with density but wick does not |
| R9 | D7 slightly narrower bodies could reduce legibility at very high density | L | M | Keep 4px body minimum from D6; gap remains positive; verify at 1-min dense view |
| R10 | D8 nice-max rounding could still leave little headroom if max is just above a nice boundary | L | M | Use `max*1.1` before rounding up; verify tick count stays 3–5 |
| R11 | D9 volume and price widths could diverge on Line/Area modes where price has no bodies | L | L | Define volume width from the same `w` even when price mode has no bodies; keep XLink |
| R12 | D10 toggle placement/affordance may not match user expectation | L | L | Icon = text label `Volume` confirmed (Q31); placement = top left of volume panel (bottom left of price chart) **confirmed 2026-09-27** (A23), not persisted; D10 is `CONFIRMED` under AC-G.1 |
| R13 | D11 price labels could overlap when many drawings share a similar price | L | M | Stack with small vertical offset or show topmost; verify at 09:00–10:00 dense zones |
| R14 | D12 zone popup with 4 tabs adds non-trivial UI surface; Extend omission may surprise users expecting the control | L | M | Omit Extend per user’s "extend both sides is required"; keep the other Style controls as shown |
| R15 | D13 50% max may still crowd chart on small screens; persistence restore could exceed new window size | L | M | Enforce chart ≥400px via `min(0.50×W, W−400)` and clamp on restore/resize; min watchlist 150px |
| R16 | D14 double-click could be mistaken for single-click row selection; accidental reloads | L | M | Require double-click (not single), any column; same-symbol and disconnected are no-ops; status message for disconnected |
| R17 | D13 floating vs docked width confusion — 50% rule mismatch | L | L | Apply 50% only when docked in LeftDockWidgetArea; floating geometry unconstrained |
| R18 | D15 horizontal line popup duplicates zone popup structure; Text tab font size 12 vs zone 14 may confuse | L | L | Keep D15 Style as Line only and Text size 12 as per attachment; keep D12 Style with Border/Middle/Background |
| R19 | A UI-visual decision implemented without a confirmed visual reference (the D5→D8 failure mode) | M | M | AC-G.1 visual gate: no UI-visual fix proceeds until its `Visual reference:` line names a user-confirmed artifact; otherwise it is a provisional assumption (A21–A26) |
| R20 | D8 `nice_max` scaling formula changes the axis values of already-built (Batch 4) behaviour, invalidating the old fixed-list test | L | M | Keep the old list only as a fixture; update `tests/test_volume_linear.py` to the pinned `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` scale (AC-D8.4/8.5) — `1_050_000 → 1_500_000` and `2_200_000 → 2_500_000` are already correct, but `_nice_volume_max(0)` must become `100` (not `10_000`) per AC-D8.4 |
| R21 | D11 drawing price labels (inside the plot) can stack when a label run overflows the pane; the crosshair chip no longer shares that lane | L | M | Chip moved to the Y-axis lane (D2/Q33), so `AC-D11.4` is **label-vs-label only** (`>= 15 px` stacking, clamped to `view_rect.bottom()`); chip-vs-label priority no longer applies (ESC-006 re-scope by Code Reviewer) |
| R22 | D16 backfill of a very long closure could exceed IBKR pacing/bar limits if requested in one call | M | M | Chunk requests, respect `pacing_manager`, and bound each request's duration; surface any shortfall (`AC-D16.4`) |
| R23 | Backfilling/displaying a much larger cached range could degrade chart load/render performance for large caches | M | M | Keep the load O(N) and verify offscreen with a large seeded cache; bound displayed bars if needed; chunk backfill asynchronously |
| R24 | A naive "no gaps" rule could wrongly try to fill genuine closures/holidays | M | L | `AC-D16.3` scopes the requirement to trading-session bars only (Q38 confirmed): weekends/holidays/overnight stay empty and are not interpolated |
| R25 | ~~`requirements.md` was missing the literal existing-repo marker, so downstream agents could treat this repo as greenfield~~ **Fixed and stable** — the **Existing Repository** section (marker sentence + **Current Tech Stack**) is present and preserved on every rewrite | — | — | Retained as a standing rule: never drop, reword, or restructure away the marker sentence or the Current Tech Stack |
| R26 | D16's reported repro is an **internal** cache hole (newer bars cached after an older block); a tail-only "anchor to `MAX(ts)`" implementation would leave it unfixed and the defect would appear unresolved | M | M | `AC-D16.1`/`AC-D16.5` require continuity across the displayed span including internal holes; DG21 directs Plan to detect the missing span from the cached series, not just `MAX(ts)` |
| R27 | A naive Saturday→preceding-Friday observed shift can mark a genuine trading day (Dec 31) as a market closure, so a real bar hole there is misclassified as a "genuine closure" and left as a silent hole (ESC-023) | M | L | `AC-D16.7` states the explicit year-end accounting exception and `AC-D16.3` excludes Dec 31 of a Jan-1-Saturday year from "genuine closure"; Task Manager corrects `T37-T03`, Build updates `market_calendar` and its test, and Code Reviewer re-verifies ESC-023 |
| R28 | D17: fixing the watchlist to clamp during the drag could regress the existing D13 integration tests (`test_d10_d13_integration.py`) that assert the **old window-width** clamp math | M | M | Keep the `watchlist_max_width`/`clamp_watchlist_width` helpers as the single source of the cap; add a drag/dock-change hook that reuses them; **update D13's denominator to 50%-of-chart-area in lockstep (B1)** — update `AC-D13.1` and the integration tests to the chart-area cap rather than leaving them contradicting D17 |
| R29 | D18: raising the right-dock width could push the chart below its 400px minimum when the watchlist is also enlarged | M | H | **Resolved by B3 rule (`AC-D18.5`):** independent caps (watchlist 50%, right region 40% of chart area) each clamped against the remaining space with a hard ~400px chart minimum; clamp on resize **and on every dock change**; enlarging one dock can force the other to shrink, and the criteria assert `chart_area >= 400px` |
| R30 | D18: full-screen "reposition so it fits" could hide the right dock entirely on small displays | M | M | Made measurable by `AC-D18.1`: the region's geometry must lie within the window rect with a non-zero visible width; cap it at 40% of the chart area, keep the chart minimum (B3), and do not let content `sizeHint` force it off-screen (`AC-D18.6`) |
| R31 | D17: enforcing a cap during the drag could make the handle feel "stuck"; the user's report says it currently does not move at all, so both over- and under-enforcement are failure modes | L | M | Verify the handle moves **freely in both directions** between min (150px) and cap (`AC-D17.1`/`AC-D17.2`); only clamp past the cap (`AC-D17.3`). B4 confirmed both drag directions are required |


---

## Status

**Status: READY_FOR_PLAN.** The 2026-10-03 batch — **D17** (Watchlist dock resize not effective in
full screen) and **D18** (Active Trader + Portfolio right dock not visible in full screen; new 40% /
equal-width sizing) — is **clarified and finalised**. All four blocking questions **B1–B4 were
answered by the user on 2026-10-03** (recorded in `open_questions.md`):
**(B1)** the watchlist cap is **50% of the chart area** (supersedes/corrects D13's Q25 window-width
denominator — D13, `AC-D13.1`–`AC-D13.3`, Journey 14, A17 and R15 updated in lockstep);
**(B2)** Active Trader + Portfolio are **one right-dock region** (stacked, inherently equal width)
with the 40%-of-chart-area cap on that single region;
**(B3)** **independent caps + ~400px chart-minimum rule** (each dock clamps against its own % **and**
the remaining space; enlarging one can force the other to shrink);
**(B4)** the watchlist handle drags **both directions** between min **150px** and cap, default
**~220px**, persistence (Q26) still required.
D17/D18 now carry **final** criteria (`AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`), Journeys 18–19,
assumptions A34–A36 and risks R28–R31. D16 remains clarified and finalised (Q37–Q39, ESC-023);
D1–D15 remain built and green. **No blocking open question remains.** The Existing Repository section
(marker sentence + Current Tech Stack) is preserved.

Status: READY_FOR_PLAN
