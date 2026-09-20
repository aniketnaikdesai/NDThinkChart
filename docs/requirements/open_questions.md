# Open Questions

> Owned by Requirements Analyst. Other agents may read; only Requirements Analyst edits.
>
> **No open blocking questions remain.** Batch 1 (D1–D3) is built. Batches 2–9
> (D4–D15) are now fully clarified 2026-09-19/20 and awaiting the next plan pass.

## Answered

### Q1 — What is the actual goal for this run?
- **Status:** answered 2026-09-19
- **Answer:** Fixing issues and resolving UI bugs. This is a feedback-driven
  stabilization run, not a new-feature build.

### Q2 — Is the goal one of the known gaps, or something new?
- **Status:** answered 2026-09-19
- **Answer:** Something new. The user is giving feedback on the app and asking for
  fixes. (Candidates A/B from discovery are explicitly out of scope for this run.)

### Q3 — Definition of done / success metric
- **Status:** answered 2026-09-19
- **Answer:** All test conditions pass. Test conditions are not fixed up front —
  they will be defined/updated per task as each defect is triaged.

### Q4 — Scope boundaries
- **Status:** answered 2026-09-19
- **Answer:** The normal live-order path is in scope to touch, but live orders are
  currently gated at the TWS API layer by the user, so no order can actually
  transmit during this work.

### Q5 — Confirm the stack
- **Status:** answered 2026-09-19
- **Answer:** Confirmed as documented (Python 3.11+/PyQt6/pyqtgraph/ibapi/SQLite,
  macOS arm64, live TWS port 7496 only).

---

## Answered (batch 1 intake)

## Q6 — What is the actual list of reported issues / UI bugs?
- **Status:** answered 2026-09-19
- **Answer:** Batch 1 supplied — three defects, D1 (RTH/ETH session shading),
  D2 (crosshair price label covered by right dock), D3 (missing zoom controls +
  area-zoom magnifier). Batch 1 is the complete list for this run.
- **Affected requirement section:** Problem Statement; Defect Register.

## Q7 — How will feedback arrive, and in what detail?
- **Status:** answered 2026-09-19
- **Answer:** One message at a time; follow-up questions are permitted as needed.
  The full requirements→build flow may repeat until the user is satisfied.

## Q8 — Regression-test policy per fix
- **Status:** answered 2026-09-19 (confirmed: "ok")
- **Answer:** Every fix ships with a check that fails before / passes after,
  runnable offscreen with no live TWS; the existing suite stays green.

## Q9 — Live-order safety boundary during this run
- **Status:** answered 2026-09-19 (confirmed: "ok")
- **Answer:** No automated test connects to live TWS or transmits. Order-path
  changes verified via generated-order-field unit tests; any live check is a manual
  user-run step.

---

# Defect Intake — Batch 1 (D1–D3)

## Q10 — D1: which sessions are shaded, and in what colours?
- **Status:** answered 2026-09-19
- **Answer:** Proposed sessions accepted. RTH left at default (no band). Pre-market
  = **orange at 10% opacity**; post-market = **blue at 10% opacity**.

## Q11 — D1: when should shading appear?
- **Status:** answered 2026-09-19
- **Answer:** Accept default, with the intraday range corrected to **1 min through
  4 hours**. (Exact set: `1 min, 5 mins, 15 mins, 1 hour, 4 hours`; `1 day` excluded.)

## Q12 — D2: where should the crosshair price label sit?
- **Status:** answered 2026-09-19
- **Answer:** Option **(a)** — right-align the chip so it ends inside the plot's
  right edge, never under the axis or right dock.

## Q13 — D3: where do the zoom controls live?
- **Status:** answered 2026-09-19
- **Answer:** Top-right of the chart area, inside a visible outline so it looks neat.
  Cluster contains `−`, `+`, magnifier, reset.

## Q14 — D3: how should the magnifier behave?
- **Status:** answered 2026-09-19
- **Answer:** Proposed behaviour accepted. Both axes. Magnifier stays active after
  one zoom. `+`/`−` zoom around the chart centre. A reset button is required.

---

# Defect Intake — Batch 2 (D4–D5) — proposed 2026-09-19, screenshot feedback

## Q15 — D4: zoom label size (proposed 14px/700, magnifier 50% larger)
- **Status:** answered 2026-09-19
- **Answer:** Correct, with the magnifying glass 50% larger. Final: `-`/`+`/`Reset` at
  **14px / 700**, `⌕` at **21px / 700** (14px × 1.5). Button size remains 28×24.

## Q16 — D4: zoom cluster position (proposed left of price axis)
- **Status:** answered 2026-09-19
- **Answer:** Current is fine — fully inside the data area left of the price axis
  (`x = panel.width - ctrl.width - axis_width - 12`, fallback 50, `x >= 8`).

## Q17 — D5: volume Y logarithmic — always on? zero handling? (proposed)
- **Status:** answered 2026-09-19
- **Answer:** Lower bound **1.0** confirmed. Volume ViewBox always log on Y
  (`setLogMode(y=True)`), X remains linear; zero-volume bars map to `1.0`; auto-range
  `yRange=(1.0, max_vol*1.1)`.

---

# Defect Intake — Batch 2 extension (D6) — new screenshots 2026-09-19

## Q18 — D6: candlestick wick visibility
- **Status:** answered 2026-09-19
- **Answer:** Correct — wick ~1px thin line behind the body, body noticeably wider
  (≥4× wick, e.g., 6–8px at default zoom while wick stays 1px), colour follows
  direction (teal/pink), and wick extends beyond the body when a shadow exists.

---

# Defect Intake — Batch 3 (D7) — proposed 2026-09-19

## Q19 — D7: time-axis candle spacing — how much more?
- **Status:** answered 2026-09-19
- **Answer:** Go **35% gap** for now. Body half-width `0.40 → 0.325` of `median_diff`
  (full body 65% of spacing, gap 35%). `xRange` padding stays as-is; the 4px body
  minimum continues to apply.

---

# Defect Intake — Batch 4 (D8) — new volume screenshots 2026-09-19

## Q20 — D8: volume Y linear scale, no negatives, dynamic nice ticks, coloured bars
- **Status:** answered 2026-09-19
- **Answer:** Correct — linear Y starting at `0` with no negatives, dynamic nice max
  (`max_vol*1.1` rounded up via `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M,
  2.5M, 5M, 10M]`), and bars coloured green/red by price direction as proposed.

---

# Defect Intake — Batch 5 (D9–D10) — new volume feedback 2026-09-19

## Q21 — D9: volume candle spacing should follow price candle spacing
- **Status:** answered 2026-09-19
- **Answer:** Correct — volume width = same `w` as price (`width = w*2`, gap 35% of
  `median_diff`). The spacing matches the price panel exactly.

## Q22 — D10: volume panel show/hide toggle
- **Status:** answered 2026-09-19
- **Answer:** Top left of the volume panel, which is the bottom left of the price
  chart panel. Toggle is checkable, default visible, not persisted; clicking hides
  the volume plot and its axis and the price plot expands.

---

# Defect Intake — Batch 6 (D11) — new drawing screenshots 2026-09-19

## Q23 — D11: drawing price labels on inner side (right side) of chart
- **Status:** answered 2026-09-19
- **Answer:** Correct — inner-right-side inside the plot, near the right edge, is the
  correct placement for all drawing price labels as proposed.

---

# Defect Intake — Batch 7 (D12) — zone double-click settings popup 2026-09-19

## Q24 — D12: zone double-click should open settings popup with 4 tabs — is the tab content correct and is Extend omitted?
- **Status:** answered 2026-09-19
- **Answer:** Correct — Extend is omitted; zone always extends both sides. The four
  tabs (Style without Extend, Text, Coordinates, Visibility) as proposed are correct.

---

# Defect Intake — Batch 8 (D13–D14) — new watchlist feedback 2026-09-20

## Q25 — D13: watchlist panel should extend more — how far?
- **Status:** answered 2026-09-20
- **Answer:** Freely draggable up to **~50% of MainWindow width**. Chart central panel keeps minimum **400px** so effective max is `min(floor(0.50×W), W−400)`. On 1400px window this is ~700px; min watchlist ~150px. Clamped on window resize.
- **Affected requirement section:** D13 / Journey 14 / AC-D13.1–D13.3

## Q26 — D13: should watchlist width persist across restarts?
- **Status:** answered 2026-09-20
- **Answer:** **Yes** — persist integer pixels (e.g., QSettings `watchlist/width` or DB key) and restore on launch clamped to current 50%; default ~220px if none saved.
- **Affected requirement section:** D13 / Journey 14 / AC-D13.2

## Q27 — D14: watchlist click to load chart — single-click or double-click, and where?
- **Status:** answered 2026-09-20
- **Answer:** **Double-click anywhere on the row** (any of the 7 columns) triggers the load; single-click only selects the row (SelectRows behavior retained).
- **Affected requirement section:** D14 / Journey 15 / AC-D14.1

## Q28 — D14: what chart load semantics should double-click use?
- **Status:** answered 2026-09-20
- **Answer:** **Identical to typing symbol in Symbol input and pressing Load Chart** — set `symbol_input` to row’s Symbol (uppercased), then invoke existing `load_chart()` with current `tf_combo` and current `ext_hours_btn`; includes cancel previous RT, cached bars, delta fetch, RT subscription, DOM if enabled.
- **Affected requirement section:** D14 / AC-D14.1

## Q29 — D14: same symbol or disconnected — what should happen?
- **Status:** answered 2026-09-20
- **Answer:** **No-op** in both cases: if double-clicked symbol (case-insensitive) equals `_current_symbol`, no reload/new reqId/RT cancel/no flicker; if IBKR disconnected, no historical/RT request and `status_bar.showMessage("Disconnected — cannot load chart.", 3000)`; header/empty area also no-op.
- **Affected requirement section:** D14 / AC-D14.2–D14.3

---

# Defect Intake — Batch 9 (D15) — horizontal line double-click 2026-09-20

## Q30 — D15: horizontal line double-click should open settings popup with 4 tabs — is the tab content correct?
- **Status:** answered 2026-09-20
- **Answer:** Correct — the four tabs (Style with `Line`, Text, Coordinates with single `#1 (price)`, Visibility) as proposed are correct.
