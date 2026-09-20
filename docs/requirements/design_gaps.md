# Design Gaps

> Owned by Requirements Analyst. Non-blocking inconsistencies or missing pieces in
> the requested design that should be resolved before/while building, but do not
> halt progress.

## DG1 — D1 session shading applies equity sessions to every symbol
- **Where it shows up:** D1 / Journey 2.
- **Why it matters:** Futures trade nearly 24 hours and have different session
  boundaries; applying the equity `04:00–20:00 ET` model may mis-shade them.
- **Suggested resolution:** Keep the accepted default for this run; if futures are
  ever charted with shading, add a per-contract session map.
- **Status:** open

## DG2 — D2 chip decimal precision is unspecified
- **Where it shows up:** D2 / AC-D2.1.
- **Why it matters:** "Complete label including all decimals" is only objectively
  testable once the precision source is fixed, and it should match the price axis.
- **Suggested resolution:** Reuse the axis tick precision (current tag uses
  `f"{y:,.2f}"`); confirm during build. See assumption A5.
- **Status:** open

## DG3 — D3 magnifier mode lifecycle on symbol/timeframe change
- **Where it shows up:** D3 / AC-D3.4 and its edge cases.
- **Why it matters:** "Stays active after one zoom" is specified, but behaviour
  when the chart reloads for a new symbol/timeframe is not.
- **Suggested resolution:** Adopt assumption A6 (revert to Cursor) as the default.
- **Status:** open

## DG4 — No GUI-level regression tests exist despite the `test_gui.md` spec
- **Where it shows up:** Test coverage for all D1–D3 UI changes.
- **Why it matters:** The spec describes 11 `tests/test_gui*.py` files; none exist.
  UI-only fixes risk having no GUI-level regression guard beyond import smoke tests.
- **Suggested resolution:** Add targeted `pytest-qt` offscreen checks per defect
  (e.g. overlay band geometry, chip bounds, zoom button signals). A full GUI suite
  remains out of scope for this run.
- **Status:** open

## DG5 — D4 zoom cluster position depends on dynamic price-axis width
- **Where it shows up:** D4 / AC-D4.2.
- **Why it matters:** The right price axis width varies with price magnitude (e.g.,
  5-digit prices are wider); a fixed 28px margin still overlaps the axis, while a
  fixed 12px left-of-axis offset may be too conservative on narrow axes.
- **Suggested resolution:** Position as `panel.width - ctrl.width - axis_width - 12`
  with `axis_width = price_plot.getAxis('right').width()` (fallback 50) and `x >= 8`
  clamp. See Q16, R6, A8.
- **Status:** open

## DG6 — D5 volume log scale cannot display zero
- **Where it shows up:** D5 / AC-D5.2.
- **Why it matters:** Logarithmic Y cannot show `0`; the mapping `0 → 1.0` is a
  visual interpretation — a minimal tick at the bottom could be mistaken for data.
- **Suggested resolution:** Keep the proposed `0 → 1.0` floor and document it as a
  minimal tick, not a gap; keep `yRange=(1.0, max*1.1)`. See Q17, R7, A9.
- **Status:** open

## DG7 — D6 wick/body thickness distinction
- **Where it shows up:** D6 / AC-D6.1.
- **Why it matters:** At high bar density the body narrows; if the wick thickens
  with it the two become indistinguishable, defeating the requested clarity.
- **Suggested resolution:** Keep wick fixed at ~1px regardless of zoom/density;
  let body width scale with density (≥4× wick). See Q18, A10, R8.
- **Status:** open

## DG8 — D7 gap vs framing — inter-candle gap vs outer padding
- **Where it shows up:** D7 / AC-D7.1, AC-D7.2.
- **Why it matters:** "More spacing" could be achieved by narrowing bodies (larger
  inter-candle gap) or by widening `xRange` (more outer padding). The two have
  different effects on density and session-band framing.
- **Suggested resolution:** Use inter-candle gap (body half-width `0.325` instead of
  `0.40`, gap 35% of spacing, confirmed Q19) as proposed in Q19; keep `xRange`
  `-2*bar_w / +8*bar_w` unchanged. See Q19, A11, R9.
- **Status:** open

## DG9 — D8 volume nice-max and tick formatting — which set?
- **Where it shows up:** D8 / AC-D8.1, AC-D8.3.
- **Why it matters:** "Like 10k, 100k, 500k, 1.0M, 1.5M, 2.0M" covers different max
  ranges; the exact nice values and the rounding rule determine whether the max bar
  fits with headroom and whether ticks look clean.
- **Suggested resolution:** Use `nice_max = ceil(max_vol*1.1 / step) * step` with the
  next nice from `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]`
  and format ticks as `500.0K / 1.0M` (one decimal for K, same for M). See Q20, A12,
  R10.
- **Status:** open

## DG10 — D9 volume width — should it be exactly price width?
- **Where it shows up:** D9 / AC-D9.1.
- **Why it matters:** "Follow price spacing" could mean volume bars are exactly the
  same width as price bodies (35% gap) or slightly narrower/wider for visual
  separation.
- **Suggested resolution:** Use exactly the same `w` (width `w*2`, gap 35%) as
  proposed in Q21; keep XLink. See Q21, A13, R11.
- **Status:** open

## DG11 — D10 volume toggle — where and should it persist?
- **Where it shows up:** D10 / AC-D10.1, AC-D10.2.
- **Why it matters:** "Allow the user to show/hide" is vague on affordance and
  persistence; the current proposal is a toolbar toggle that resets to visible.
- **Suggested resolution:** **Top left of the volume panel** (bottom left of price
  chart) as confirmed Q22, no persistence. See Q22, A14, R12.
- **Status:** open

## DG12 — D11 drawing price labels — inner right side placement
- **Where it shows up:** D11 / AC-D11.1, AC-D11.2.
- **Why it matters:** "Inner side (right side)" could be the price axis area vs the
  data area interior; the label must be inside the plot to be visible at any zoom,
  not on the axis.
- **Suggested resolution:** Place labels inside the plot at `view_rect.right() - 4`,
  `anchor=(1, 0.5)`, same colour as the drawing, one per price, stacking when
  nearby. See Q23, A15, R13.
- **Status:** open

## DG13 — D12 zone popup — Extend omitted, 4 tabs
- **Where it shows up:** D12 / AC-D12.1, Style tab.
- **Why it matters:** The reference Style tab shows an `Extend` dropdown, but the
  requirement says the zone must always extend both sides. Omitting the control is a
  deliberate divergence that should be explicit.
- **Suggested resolution:** Omit `Extend` entirely (zone always both-sides) and
  keep `Border`, `Middle line`, `Background` as shown; double-click is the only
  opener. See Q24, A16, R14.
- **Status:** open

## DG14 — D15 horizontal line popup — single coordinate vs zone
- **Where it shows up:** D15 / AC-D15.1, Coordinates tab.
- **Why it matters:** Zones need `#1 / #2 (price, bar)` while a horizontal line
  needs only `#1 (price)`; reusing the zone dialog could show an irrelevant second
  coordinate.
- **Suggested resolution:** Keep a dedicated `Horizontal line` dialog with single
  `#1 (price)` stepper (as per the attachment) or hide `#2` when `kind ==
  "horizontal"`. See Q30, A17, R15.
- **Status:** open

## DG14 — D13 watchlist width 50% + persistence — mechanism and clamping
- **Where it shows up:** D13 / AC-D13.1–D13.3 / Journey 14.
- **Why it matters:** "Freely draggable to 50%" needs an explicit min/max and a concrete persistence store; without it the build may pick a different store or miss the `W−400` chart-minimum clamp, causing chart collapse on small windows or loss of width on restart.
- **Suggested resolution:** Enforce `[150, min(floor(0.50×W), W−400)]` for docked watchlist (chart ≥400px) with resize-time clamping; persist via `QSettings("NDThinkChart","watchlist/width")` (or DB key) as integer pixels, restore clamped to current 50%, default 220px; floating dock not constrained. See Q25–Q26, A17, R15, R17.
- **Status:** open

## DG15 — D14 double-click row to load chart — scope and no-ops
- **Where it shows up:** D14 / AC-D14.1–D14.3 / Journey 15.
- **Why it matters:** "Double-click anywhere on the row" must be distinguished from header/empty-area clicks and from same-symbol/disconnected no-ops; otherwise single-click selection could be mistaken for a load or a disconnected double-click could queue a request.
- **Suggested resolution:** Wire `QTableWidget.cellDoubleClicked(int,int)` and resolve row Symbol via `COL_SYMBOL`; ignore when `row<0` or `symbol` empty/header; case-insensitive compare to `_current_symbol` for no-op; check `ConnectionState` / `load_btn.isEnabled()` before issuing `req_historical_data`; show status message on disconnected as specified. See Q27–Q29, A18–A19, R16.
- **Status:** open
