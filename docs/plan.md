# Implementation Plan — NDThinkChart Stabilization (Batch 3–9: D7–D15)

Scope: the Batch 3–9 refinements in `docs/requirements/requirements.md`
(D7–D15), all clarified 2026-09-19/20. This is a stabilization run; no new
features, no schema changes, no new integrations.

## Completed — Batch 1 and Batch 2
Batch 1 (D1–D3: session shading, crosshair chip, zoom controls/magnifier) and
Batch 2 (D4–D6: zoom label/position, volume log, pixel-stable wick) were approved,
built, and verified, plus the 2026-09-19 `DrawingOverlay` drag-lifecycle runtime
stability fix (see `docs/build/build_log.md` and `docs/debug/debug_log.md`). Note:
**D8 supersedes D5’s log decision** — the volume axis returns to linear.

## Phases

### Phase 1 — Chart geometry: inter-candle gap and volume axis (D7, D9, D8)
- **Goal:** Increase the price inter-candle gap to ~35% of bar spacing
  (`w = median_diff * 0.325`, single-bar `0.25` fallback, D6 4px minimum kept,
  `xRange` padding unchanged); make the volume bars use the **same `w`** as the
  price bodies (`volume_bars.width = w*2`, `y0=0`, X linked); and revert the volume
  `ViewBox` to **linear Y** (`setLogMode(y=False)`) with `yRange=(0, nice_max)`
  where `nice_max = ceil(max_vol*1.1/step)*step` using the nice set
  `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]`, bars
  coloured `#34d399`/`#f87171` by `close>=open`, and ticks formatted
  `500.0K / 1.0M` with `0` lower bound and no negatives.
- **Requirements / journeys covered:** D7 (AC-D7.1–D7.2, Journey 8), D9
  (AC-D9.1–D9.2, Journey 10), D8 (AC-D8.1–D8.3, Journey 9); `A11`, `A12`, `R9`,
  `R10`, `DG8`, `DG9`, and D8’s supersession of D5.
- **Dependencies on earlier phases:** None. Isolated to `ui/candlestick_item.py`
  (`w` factor + 4px minimum) and `ui/chart_panel.py` (volume `BarGraphItem`,
  `ViewBox` mode, `yRange`/`y0`, colour logic, tick formatter).

### Phase 2 — Drawing visuals: inner-right labels and double-click settings (D11, D12, D15)
- **Goal:** Render an inner-right price label for **any** drawing at
  `x = view_rect.right() - 4`, `anchor=(1,0.5)`, `Z=10`, colour-matched, one per
  price (zone top+bottom; trendline/Fibonacci per level) with a small vertical
  offset when nearby; and open settings popups on double-click — **zone** →
  `Rectangle` dialog (4 tabs Style/Text/Coordinates/Visibility, **`Extend`
  omitted**, `Border`/`Middle line`/`Background`, `#1/#2 (price, bar)` steppers,
  8-row Visibility) and **horizontal line** → `Horizontal line` dialog (4 tabs,
  `Line` style, Text size `12`, single `#1 (price)` stepper, same Visibility).
  Apply updates the drawing and re-renders; Cancel/X discards.
- **Requirements / journeys covered:** D11 (AC-D11.1–D11.3, Journey 12), D12
  (AC-D12.1–D12.3, Journey 13), D15 (AC-D15.1–D15.3, Journey 16); `A15`, `A16`,
  `A17`, `R13`, `R14`, `R15`, `DG12`, `DG13`, `DG14`.
- **Dependencies on earlier phases:** None technically. Shares `ui/chart_panel.py`
  and `ui/drawing_overlay.py` with Phase 1, so build serially after it.

### Phase 3 — Volume panel visibility toggle (D10)
- **Goal:** Add a checkable control at the **top left of the volume panel**
  (bottom-left of the price chart), default **visible**, which hides/shows
  `volume_plot` and its axis and rebalances the `QSplitter` so the price plot
  expands; state is **not persisted** (resets to visible on launch).
- **Requirements / journeys covered:** D10 (AC-D10.1–D10.2, Journey 11); `A14`,
  `R12`, `DG11`.
- **Dependencies on earlier phases:** Phase 1 (shares `ui/chart_panel.py` volume
  plot), so build serially after it.

### Phase 4 — Watchlist resize and double-click load (D13, D14)
- **Goal:** Make the docked Watchlist freely draggable up to **~50% of the
  `MainWindow` width** — clamped to `[150, min(floor(0.50×W), W−400)]` so the
  chart keeps ≥400px — and **persist** the width as an `int` pixel value
  (`QSettings watchlist/width`, default ~220px), clamped on restore and window
  resize (floating geometry unconstrained). Double-click **anywhere on a row**
  (any of the 7 columns) loads the chart **identically to `Load Chart`**: set
  `symbol_input` to the row symbol (uppercased) and invoke `MainWindow.load_chart()`
  with the current timeframe and Ext-Hours; **no-op** when the symbol equals
  `_current_symbol` (case-insensitive) or IBKR is disconnected (status message);
  header/empty area is a no-op.
- **Requirements / journeys covered:** D13 (AC-D13.1–D13.3, Journey 14), D14
  (AC-D14.1–D14.3, Journey 15); `A17`–`A19` in the requirements log (`A17`–`A19`
  as numbered in `requirements.md`), `R15`–`R17`, `DG14`–`DG15`.
- **Dependencies on earlier phases:** None. Isolated to `ui/watchlist_panel.py`,
  `ui/main_window.py`, and the `QSettings` read/write site.

### Phase 5 — Verification and regression (Batches 3–9)
- **Goal:** Confirm every Batch 3–9 per-defect test condition passes offscreen and
  the pre-existing suite stays green, with no live-TWS connection or order
  transmission.
- **Coverage:** D7 (35% gap incl. dense and single-bar), D8 (linear `0–nice_max`,
  nice rounding, no negatives, coloured bars), D9 (volume width alignment), D10
  (hide/show + splitter), D11 (inner-right labels incl. stacking), D12/D15
  (double-click popups, pre-fill, `Extend` absent for zones), D13 (50% cap,
  persistence, restore clamp), D14 (load semantics + same-symbol/disconnected
  no-ops), plus the Global Acceptance Criteria.
- **Dependencies on earlier phases:** Phases 1, 2, 3, and 4.

## Assumptions
Plan-level assumptions not already captured in the requirements Assumptions Log:

- **PA1-batch3** D7 is exactly `w = median_diff * 0.325` (35% gap); `xRange`
  padding stays `-2*bar_w / +8*bar_w` (confirmed Q19).
- **PA2-batch3** D9 volume width follows price exactly (`w*2`, 35% gap) in all
  chart modes, including the dense 4px minimum (confirmed Q21).
- **PA3-batch3** D10 toggle lives at the top-left of the volume panel
  (bottom-left of the price chart) and is not persisted (confirmed Q22).
- **PA4-batch3** D11 inner-right label origin is `view_rect.right() - 4` with
  `anchor=(1,0.5)` and small-offset stacking (confirmed Q23).
- **PA5-batch3** D12 zone dialog always extends both sides; `Extend` is omitted
  (confirmed Q24).
- **PA6-batch3** D13 cap is `min(floor(0.50×W), W−400)` with watchlist min `150px`
  and chart min `400px`; floating unconstrained; width persisted as `int` px via
  `QSettings` (confirmed Q25–Q26).
- **PA7-batch3** D14 double-click anywhere on a row triggers `load_chart`
  identically to manual `Load Chart`; same-symbol and disconnected are no-ops
  (confirmed Q27–Q29).
- **PA8-batch3** D15 uses a single `#1 (price)` coordinate and Text size `12`, as
  distinct from D12’s `#1/#2` and size `14` (confirmed Q30).
- Inherited and confirmed from `docs/requirements/requirements.md`: `A8`–`A17`
  (including `A11` 35% gap, `A12` volume linear nice-max, `A13` volume `w*2`,
  `A14` toggle top-left/not persisted, `A15` inner-right labels, `A16` zone popup,
  `A17` horizontal line popup, and the watchlist assumptions).

---

Status: READY_FOR_TASK_MANAGER
