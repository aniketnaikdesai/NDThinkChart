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
  **Related — fully specified 2026-09-27:** the magnifier ↔ drawing ↔ alarm transitions
  are now all requirements (no provisional/assumption wording remains) — the forward
  direction (Q35 option (a): magnifier cancels the drawing and enters `ZOOMING`) and the
  reverse direction (A26, **CONFIRMED**: selecting a tool exits `ZOOMING` and activates
  it) are both `AC-D3.7`; alarm-mode activation cancels `ZOOMING` (`AC-D3.8`); and
  invoking the magnifier while `ALARM_PLACING` is active **refuses to enter `ZOOMING`**,
  keeping alarm placement priority with a status-bar hint (Q36 option (b), answered
  2026-09-27; `AC-D3.9`). The `ALARM_PLACING → ZOOMING` corner (formerly Plan PA-R1 /
  TR-9, Q36) is therefore **specified required behaviour**, and the router transition
  table is total.
- **Status:** open (only the symbol/timeframe-change lifecycle sub-question remains; it is
  non-blocking — the transition-specification part is resolved)

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

## DG6 — ~~D5 volume log scale cannot display zero~~ SUPERSEDED by D8
- **Where it shows up:** D5 / AC-D5.2 — **superseded** (see D8 / `AC-D8.1`).
- **Why it matters:** This gap described the log `0 → 1.0` mapping. D8/Q20 replaced
  the log axis with a linear axis whose lower bound is `0`, so the zero-display
  problem no longer exists. Retained for history only.
- **Suggested resolution:** No action — implement D8 (linear) instead. See D8, Q20,
  A12; D5 is marked `SUPERSEDED BY D8` in `requirements.md`.
- **Status:** closed (superseded by D8)

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
- **Where it shows up:** D8 / AC-D8.1, AC-D8.3, AC-D8.4, AC-D8.5.
- **Why it matters:** The original fixed list (`[10k, …, 10M]`) was coarse above 10M
  and floored at 10k, flattening low-volume symbols (ESC-003/ESC-008). The live rule
  is now a continuous **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** scale (pinned by
  RG-002, 2026-09-27, to reproduce the user-confirmed Q20 values `750K` and `1.5M`);
  the old list is only a test fixture.
- **Suggested resolution:** `nice_max` = the smallest family value `>= max_vol*1.1`
  (no fixed `10k` floor, no fixed ceiling); format ticks as `500.0K / 1.0M` (one
  decimal for K and M). See Q20, A12 (revised by A24), R10, R20.
- **Status:** resolved (family pinned by RG-002; criteria updated 2026-09-27)

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
  chart) as confirmed Q22, no persistence; the toggle is a checkable text label
  **`Volume`** (Q31) and the placement is now **confirmed 2026-09-27** (A23). See Q22,
  Q31–Q32, A14, A22–A23, R12.
- **Status:** resolved (placement confirmed 2026-09-27, A23; D10 `CONFIRMED`)

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

## DG16 — ESC-006: crosshair chip and drawing labels shared the right-edge lane
- **Where it shows up:** D11 / AC-D11.4 / ESC-006.
- **Why it matters:** The crosshair chip (`anchor=(1,0.5)`, `x = right()-2`) and D11
  drawing labels (`anchor=(1,0.5)`, `x = right()-4`) previously occupied the same
  inside-plot lane, so hovering at a drawing's price could stack two chips and the
  overflow priority was a product choice.
- **Suggested resolution (resolved 2026-09-27, Q33):** the chip moved to the **Y-axis
  lane outside the plot** (see D2), while D11 labels stay inside the plot; the two are in
  different lanes, so the chip-vs-label overflow collision no longer applies. `AC-D11.4`
  is re-scoped to **label-vs-label** stacking (`>= 15 px`, clamped to
  `view_rect.bottom()`); the Code Reviewer must re-scope ESC-006 accordingly. See
  AC-D11.4, R21.
- **Status:** closed (resolved by Q33 lane separation, 2026-09-27)

## DG17 — ESC-011: repository doc drift (test counts, phase markers, orphaned `.pyc`)
- **Where it shows up:** Documentation Maintenance Requirements DOC-1..DOC-4.
- **Why it matters:** `usage.md:166` and `PENDING_IMPLEMENTATION_PLAN.md:364/:412/:458`
  state "269 tests" (measured: **339**); Phases 1–5 carry no completion marker though
  their files exist; a source-less `.pyc` remains. Stale docs mislead every later agent.
- **Suggested resolution:** DOC-1 correction is mechanical (use measured 339 / ~2.9s).
  DOC-2 ownership is decided (Q34, answered 2026-09-27): the **Requirements Analyst owns
  closing DOC-2** (mark Phases 1–5 `✅ COMPLETE`); **Code Reviewer verification** is the
  confirming step. Because `PENDING_IMPLEMENTATION_PLAN.md` is outside the Analyst's
  file-ownership table, the Analyst records the requirement/ownership in `requirements.md`
  rather than editing the root doc; any residual owner action is a recorded dependency. DOC-3
  is covered by ESC-001 (BUILD).
- **Status:** open — DOC-2 decided/owned (Analyst closes; Code Reviewer verifies); physical root-doc edit remains a recorded dependency

## DG15 — D14 double-click row to load chart — scope and no-ops
- **Where it shows up:** D14 / AC-D14.1–D14.4 / Journey 15.
- **Why it matters:** "Double-click anywhere on the row" must be distinguished from header/empty-area clicks and from same-symbol/disconnected no-ops; otherwise single-click selection could be mistaken for a load or a disconnected double-click could queue a request.
- **Suggested resolution:** Wire `QTableWidget.cellDoubleClicked(int,int)` and resolve row Symbol via `COL_SYMBOL`; ignore when `row<0` or `symbol` empty/header; case-insensitive compare to `_current_symbol` for no-op; check `ConnectionState` / `load_btn.isEnabled()` before issuing `req_historical_data`; show status message on disconnected as specified. See Q27–Q29, A18–A19, R16.
- **Status:** open


---

## DG18 — D16: live/real-time bars are never persisted to the cache
- **Where it shows up:** D16 / Journey 17; `ui/main_window.py::_on_aggregated_bar` →
  `ChartPanel.update_last_bar` vs `_on_historical_data_end` → `BarCache.save_bars`.
- **Why it matters:** only historical fetches call `BarCache.save_bars`; bars aggregated
  from the live stream update the in-memory `_bars` but are lost on restart. This is not the
  cause of the reported 09/20–09/27 hole (the app was most likely closed), but if the app
  *was* running across those days, live bars would not have survived a restart. The
  load-time backfill (D16) covers the visible hole either way.
- **Suggested resolution:** out of D16's minimal scope; if live-bar persistence is wanted,
  add a periodic/on-close `save_bars` of the current session's bars as a separate item.
- **Status:** open (non-blocking; surfaced for awareness)

## DG19 — D16: IBKR per-request duration/bar limits vs a long backfill
- **Where it shows up:** D16 / `AC-D16.4`; `TIMEFRAME_CONFIG` is a single fixed duration per
  timeframe.
- **Why it matters:** if the cache gap exceeds what one IBKR request returns for that bar
  size, a single enlarged request may still leave a hole. The fix must chunk or the
  shortfall must be surfaced.
- **Suggested resolution:** chunk backfill requests (respecting `pacing_manager`) or size a
  single request to the gap when within IBKR limits; document the bound.
- **Status:** open (non-blocking; implementation detail for Plan, but it constrains
  `AC-D16.4`)

## DG20 — D16: no user-facing date-range control exists
- **Where it shows up:** D16 / Journey 17.
- **Why it matters:** the chart auto-frames all cached bars; there is no way for the user to
  request a specific window. This is why a cache hole is immediately visible and why the
  fix is about the load/backfill path rather than a display filter.
- **Suggested resolution:** keep auto-framing; D16 backfills the underlying bar list. A
  date-range selector, if wanted, is a feature suggestion (see `feature_suggestions.md`
  FS6), not part of D16.
- **Status:** open (non-blocking; informational)

## DG21 — D16: the literal "last cached bar" anchor does not heal the reported internal hole
- **Where it shows up:** D16 / Journey 17 / `AC-D16.1`, `AC-D16.5`; `ui/main_window.py::load_chart`.
- **Why it matters:** The Q37 answer says "backfill the whole gap from the last cached bar up to
  now", but the reported repro cache is an **internal** discontinuity: `SPY 5 mins` holds bars
  through Fri 2026-09-18 **and** bars for 2026-09-28…now, with 2026-09-19…2026-09-27 missing. A fix
  anchored only to `BarCache.get_last_timestamp` (`MAX(ts)` = the 09/28+ block) would see no gap and
  leave the reported hole unfixed. `get_last_timestamp` exists (`data/bar_cache.py:33`) but is not
  used by `load_chart`, which fetches `endDateTime=""` with the fixed `TIMEFRAME_CONFIG` duration
  (`ui/main_window.py:430–444`).
- **Suggested resolution:** State the requirement as an outcome (continuous bar series over the
  displayed span) — already done in `AC-D16.1`/`AC-D16.5` — and have Plan detect the missing span
  from the cached series (e.g., the largest gap between consecutive cached blocks, or between the
  last pre-gap bar and now) rather than only `MAX(ts)`, then backfill that span in chunks. The
  tail-gap case is a special case of the same mechanism.
- **Status:** open (non-blocking; recorded so Plan does **not** implement a tail-only anchor that
  silently leaves the reported hole in place).

---

## DG22 — D16 calendar encoded the wrong New Year's observed-day convention (ESC-023)
- **Where it shows up:** D16 / Journey 17 / `services/market_calendar.py::_observed` →
  `is_trading_day`; the `T37-T03` acceptance criterion in `docs/tasks/task-graph.json`; and
  `tests/test_market_calendar.py`.
- **Why it matters:** the naive Saturday→preceding-Friday shift marked **Dec 31** (the year-end
  accounting date) as closed in every year whose Jan 1 is a Saturday, so a genuine missing-bar hole
  on that day would be misclassified as a "genuine closure" and left as a **silent hole**
  (`AC-D16.1`/`AC-D16.4`). Latent; next occurrence `2027-12-31`.
- **Suggested resolution:** state the explicit year-end accounting-period exception (`AC-D16.7`):
  when Jan 1 is a Saturday, no New Year's holiday is observed and Dec 31 stays a trading day; Task
  Manager corrects `T37-T03`; Build updates the observed-shift rule and its test; Code Reviewer
  re-verifies ESC-023.
- **Status:** resolved (requirement corrected 2026-10-02 — `AC-D16.7`; implementation change tracked
  under ESC-023).

---

## DG23 — D17: the D13 watchlist cap is enforced only on window resize, not during a dock drag
- **Where it shows up:** D17 / D13 / `ui/main_window.py::resizeEvent` (lines ~962-968),
  `ui/watchlist_panel.py::watchlist_max_width` / `clamp_watchlist_width`; `tests/test_d10_d13_integration.py`.
- **Why it matters:** D13's "freely draggable up to 50%" is **not actually enforced** — the clamp
  helpers run only at construction and inside `resizeEvent`, which fires on *window* resize, not on a
  dock-splitter drag, and only when the dock is already wider than the max. In full screen the window
  is already maximized, so a drag may not trigger any clamp at all. This is the diagnosed root cause
  of the reported "does not extend or reduce" symptom. It is a build defect against the existing D13
  requirement, **not** (yet) a wrong requirement — but see B1 (denominator may change to "chart area").
- **Suggested resolution:** keep `watchlist_max_width`/`clamp_watchlist_width` as the single source of
  the cap and apply it on a **dock-resize/drag-completion hook** (or enforce a `maximumWidth` derived
  from the cap so the handle cannot be dragged past it), not only in `resizeEvent`. Reuse the existing
  helpers so the D13 tests stay valid. Decide B1 (window width vs chart area) before wiring.
- **Status:** open (blocking on B1; diagnosed)

## DG24 — D18: the right docks have no width governance at all and are an unaccounted horizontal consumer
- **Where it shows up:** D18 / `ui/main_window.py:234-252` (`RightDockWidgetArea` setup);
  `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py`.
- **Why it matters:** neither right panel sets a min/max width, and no `resizeDocks` call is made for
  them, so their width is entirely at Qt's discretion — which is why they can be squeezed off-screen in
  full screen (the reported clipping). The D13 watchlist clamp also reserves the chart minimum against
  the **whole window width**, ignoring the right docks entirely (the existing integration tests hide
  the right docks precisely to sidestep this). A single combined width model is needed.
- **Suggested resolution:** give the right dock a defined min/max and an initial visible width, make it
  fit within the full-screen window, and fold left+right dock widths into one combined budget that
  preserves the chart minimum (B3). If Active Trader/Portfolio are one dock (B2), a single width rule
  covers both.
- **Status:** open (blocking on B2/B3; diagnosed)

## DG25 — D18: "fits in the visible area of the full screen" is not yet a testable condition
- **Where it shows up:** D18 / provisional `AC-D18.1`.
- **Why it matters:** "reposition so that it fits in the visible area" can be satisfied many ways
  (reduce width, reduce content minimum, auto-hide, re-dock). Without a concrete condition the
  criterion is not independently testable (violates the Quality Bar's "no vague terms" rule).
- **Suggested resolution:** express as a measurable condition — e.g. the Active Trader/Portfolio dock's
  right edge `<= window right edge` and left edge `>= chart right edge` in full screen, with a
  non-zero visible width, and the chart still ≥ its minimum. Confirm once B2/B3 are answered.
- **Status:** open (blocking on B2/B3; will be made measurable when answered)


## DG27 — D19: toolbar minimumSizeHint pins the central widget (root cause of the D17/D18 real-app failure)
- **Where it shows up:** D19 / D17 / D18; `ui/main_window.py:100–223` (toolbar inside the central widget's
  `QVBoxLayout`); the dock splitter has no slack.
- **Why it matters:** the D17 50%-of-chart-area cap computes correctly but can never be reached in a toolbar-visible
  window; the right region is squeezed off-screen. Both the D17 and D18 acceptance criteria are unobservable in the
  real app.
- **Suggested resolution (decided B5, 2026-10-05):** wrap the existing toolbar in a **horizontal scroll / elide**
  container **in place** (one ~36px row, still inside the central widget) so its minimum width no longer pins the
  central widget and the docks can reach their caps; add the toolbar-visible acceptance criteria
  (`AC-D19.1`–`AC-D19.5`).
- **Status:** resolved (B5 answered 2026-10-05 — scroll/elide in place; `AC-D19.4`/`AC-D19.5` capture the outcome)

## DG28 — D19: the D17/D18 test harnesses hide the toolbar, masking the real constraint
- **Where it shows up:** `tests/test_dock_widths_d17.py::_make_window`, `tests/test_dock_widths_d18.py`,
  `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`.
- **Why it matters:** the suite exercises a window **unlike the real app**, so this regression cannot be caught; the
  harnesses' own docstrings admit the toolbar masks the very behaviour under test.
- **Suggested resolution:** remove the `toolbar.hide()` masking (or add a toolbar-visible variant) and require a
  pre-fix failure (`AC-D19.6`).
- **Status:** resolved (B5/B6 answered 2026-10-05 — the masking removal is settled and carried by `AC-D19.6`)

## DG29 — D20: the D19 wrapper's fixed 36px height leaves no lane for the horizontal scrollbar, so it overlaps the toolbar labels
- **Where it shows up:** D20 / D19 / `AC-D19.4`; `ui/main_window.py:102` (`toolbar.setFixedHeight(36)`), `:233`
  (`toolbar_scroll.setFixedHeight(36)`); `tests/test_toolbar_scroll_d19.py`.
- **Why it matters:** the scroll area's horizontal scrollbar is laid out inside the same 36px as the toolbar
  content, so it covers the bottom of the labels (descenders), making them hard to read — the reported defect.
  The 36px value was chosen by D19/B5 to keep the toolbar a single compact row; it does not account for the
  scrollbar's own height.
- **Suggested resolution:** raise the `ToolbarScroll` height (or both) so the content row and the scrollbar each
  have their own space (content ~36px + scrollbar lane), per B7; keep the content a single row and preserve the
  scroll/elide reachability. Update the D19 height assertions in lockstep.
- **Status:** resolved (B7/B8 answered 2026-10-06 — content row ~36px + reserved scrollbar lane below, total strip
  ~50–52px; scrollbar as-needed in the lane; `AC-D20.1`–`AC-D20.3` capture the outcome)

## DG30 — D20: `AC-D19.4`'s `<= ~40px` height bound conflicts with the requested height increase and must be explicitly superseded
- **Where it shows up:** D20 / D19 / `AC-D19.4` (measurable clause: "the toolbar's laid-out height stays
  `<= ~40px` (one row)"); B5 ("one ~36px row"); `tests/test_toolbar_scroll_d19.py::T53-T04` (`height() == 36`,
  `min/max == 36`).
- **Why it matters:** raising the height directly contradicts the D19 criterion as written; if it is not
  explicitly superseded, D19 and D20 would contradict each other and the D19 test would fail. The D19
  scroll/elide **reachability** intent is unaffected and must be preserved.
- **Suggested resolution:** add an explicit supersession note on `AC-D19.4` (recorded) relaxing the `<= ~40px`
  bound to the B7-confirmed target, and update the D19 height assertions in lockstep (`AC-D20.6`). Do not
  silently change the D19 test to pass.
- **Status:** resolved (B7 answered 2026-10-06 — the `<= ~40px` bound is explicitly superseded to a ~52px container
  bound on `AC-D19.4`; the D19 height assertions are updated in lockstep per `AC-D20.6`)

---

## DG31 — D21.4: collapsing non-trading time supersedes `AC-D16.3` and touches D1 shading / drawings / alarms
- **Where it shows up:** D21.4 / Journey 23; `ui/chart_panel.py` `_refresh_candles` / `_custom_date_axis`;
  `services/session_service.py`; `ui/overlays/session_overlay.py`; D16 `AC-D16.3`; D1 session bands.
- **Why it matters:** the x-axis is currently linear wall-clock time, so collapsing overnight/weekend/holiday
  gaps changes the bar x-mapping. `AC-D16.3` currently requires genuine closures to stay empty — the D21.4
  request supersedes that **display** rule, so the D16/D1 tests that assert empty closures must be updated in
  lockstep or they will contradict D21.4. Time-anchored drawings, session bands and alarm lines must still land
  on the correct bars after collapse.
- **Suggested resolution:** state the supersession explicitly (done in D21.4's supersession note); after B9 is
  answered, update the affected D16/D1 tests and verify drawings/bands/alarms. Non-blocking beyond B9.
- **Status:** resolved (B9 answered 2026-10-06 — collapse only **between-session** gaps on **intraday**
  timeframes; `1 day` no-op; the `AC-D16.3` display-part supersession is recorded and the affected D16/D1
  tests are updated in lockstep)

## DG32 — D21.5: watchlist column configuration needs field-identity binding and a persistence store
- **Where it shows up:** D21.5 / `ui/watchlist_panel.py` (`HEADERS`, `COL_*`, `_set_cell`, `on_tick_*`).
- **Why it matters:** cell updates use hard-coded column indices (`COL_LAST`, `COL_BID`, …). If columns are
  reordered or removed, index-based writes would corrupt values. A persistence store (QSettings or DB) must be
  chosen and the D14 double-click (any column) must still resolve the Symbol.
- **Suggested resolution:** bind columns by a stable field key rather than index; keep the Symbol column (per
  B10); persist the layout; add a reorder-then-tick test. Non-blocking beyond B10.
- **Status:** resolved (B10 answered 2026-10-06 — existing 7 columns, `Symbol` kept, layout persisted;
  bind columns by field identity and add a reorder-then-tick test)

## DG33 — D21.9: alarm edit semantics for a triggered/set alarm
- **Where it shows up:** D21.9 / `ui/alarm_dialog.py`; `data/alarm_store.py`; `data/models.py` (`Alarm`).
- **Why it matters:** editing a set or triggered alarm changes its meaning. Whether an edit re-arms the alarm,
  keeps it triggered, or is disallowed affects the overlay colour and the alarm badge. `AlarmStore` currently
  exposes add/rearm/set_sound/set_price/delete — an update path may be needed.
- **Suggested resolution:** define the semantics (B13), add an atomic `AlarmStore` update, and re-render the
  overlay/badge after the edit. Non-blocking beyond B13.
- **Status:** resolved (B13 answered 2026-10-06 — edit dialog with price/condition/sound/note + Save/Cancel,
  immediate persist via `AlarmStore`; a triggered/set alarm may be edited and keeps its state)

## DG34 — D21.10: yellow dashed preview line lifecycle vs the modal alarm popup
- **Where it shows up:** D21.10 / `ui/main_window.py::_on_alarm_create_requested`; `ui/alarm_dialog.py`;
  `ui/chart_panel.py` alarm overlay.
- **Why it matters:** the alarm popup is modal (`dialog.exec()`), so the preview line must be drawn on the chart
  while the dialog is up, follow the price spinbox live, and be removed when the dialog closes — without leaking
  onto the chart or colliding with the real alarm line after Add.
- **Suggested resolution:** use a dedicated preview item removed on dialog close/finish; confirm the lifecycle
  with B13; test open/close and live price changes. Non-blocking beyond B13.
- **Status:** resolved (B13 answered 2026-10-06 — preview drawn while the popup is open, follows the price
  live, removed on close, replaced by the real alarm line after Add)

## DG35 — D21.13: right-dock collapse vs the D17/D18 width model and the DOM button
- **Where it shows up:** D21.13 / `ui/main_window.py` right dock region, `_apply_dock_widths`,
  `_on_right_dock_visibility_changed`, `_on_dom_toggled`.
- **Why it matters:** collapsing the right region to a button strip changes its width demand and can interact
  with the B3 cross-clamp / chart-minimum rule; the DOM button already hides the whole region, which must be
  reconciled with per-panel hide/show. The panels' content sizing after expansion must not force the region wider.
- **Suggested resolution:** treat the fully-collapsed region like a hidden region for the cross-clamp (as the
  existing `visibilityChanged` path does); assert the chart minimum in collapsed and expanded states; reconcile
  with the DOM toggle. Non-blocking beyond B12.
- **Status:** resolved (B12 answered 2026-10-06 — Active Trader = dock title bar, Account Summary =
  portfolio summary label; one hidden → in-height collapse + other expands; both hidden → horizontal
  button-strip collapse)

## DG36 — D21.7/D21.8: consistent active-highlight across every toolbar toggle
- **Where it shows up:** D21.7/D21.8 / `ui/main_window.py` toolbar (`studies_btn`, `alarms_btn`,
  `alarm_mode_btn`, `sound_btn`, `dom_btn`, `ext_hours_btn`) inside the D19 scroll wrapper.
- **Why it matters:** a per-button ad-hoc style would be inconsistent; the highlight must be visible at any
  scroll position in the D19 wrapper and must clear reliably when the state ends (including when a dialog is
  closed or the mode is exited by another action).
- **Suggested resolution:** define one shared highlight style (`VIS-D21.2`) applied to every active/selected
  toolbar button; test active vs inactive and clear-on-exit. A41/A42 confirmed 2026-10-06 (`VIS-D21`).
- **Status:** resolved (A41/A42 confirmed 2026-10-06 — one shared `VIS-D21.2` highlight across every active/selected toolbar button)

---

## DG37 — D21.11: deleting the watchlist dock title bar removes the dock's drag/float affordance
- **Where it shows up:** D21.11 / `ui/main_window.py` watchlist dock title (`:258`), `ui/watchlist_panel.py`
  in-panel header strip (`:117–124`).
- **Why it matters:** B12 keeps the **in-panel header label** as the hide/show toggle and deletes the duplicate
  **dock title bar**. A `QDockWidget`'s title bar is normally what the user drags to move/float the dock, so
  removing it may leave the watchlist un-draggable unless an equivalent handle is provided. The toggle button must
  stay visible when the watchlist is hidden, which a title bar could not do.
- **Suggested resolution:** keep the in-panel header button as the toggle; if the dock must remain movable, give
  the header strip a drag handle (or retain a frameless/title-bar drag region) so docking still works. Plan/Build
  to choose the exact mechanism; the requirement outcome (single toggle that stays visible when hidden) is fixed.
- **Status:** open (non-blocking; affordance detail for Plan/Build)

## DG38 — D21.13: the right dock's title bar becomes the "Active Trader" toggle button
- **Where it shows up:** D21.13 / `ui/main_window.py` right dock region (`:295–337`).
- **Why it matters:** B12 makes the right dock's **title bar** the "Active Trader" hide/show button. The title bar
  is also the region's drag/hide affordance, so making it a toggle must not break moving the dock or reconcile
  badly with the existing DOM button (which hides the whole region).
- **Suggested resolution:** make the title-bar label a clickable toggle while keeping a drag region; treat a
  fully-collapsed region as hidden for the D17/D18 cross-clamp (`DG35`); reconcile with `_on_dom_toggled`.
- **Status:** open (non-blocking; affordance/reconciliation detail for Plan/Build)


---

## DG39 — D22: no offline symbol validation exists, so an unknown/invalid ticker cannot be rejected locally
- **Where it shows up:** D22 / `AC-D22.4`; `ibkr/contracts.py::get_contract_for_symbol` (`:169`); `data/db.py`
  `watchlist` table; the add path.
- **Why it matters:** `get_contract_for_symbol` builds a **stock contract for any string** and only special-cases a
  small `FUTURES_SCHEDULE` set; it performs **no IBKR lookup and raises no error** for an unknown symbol. Without a
  live contract-details request there is no way to tell a valid ticker from a typo, so an add path that "just works"
  could silently persist `APPL` (typo) as if it were valid. This is why unknown-symbol handling is a genuine user
  decision (B16), not an implementation detail.
- **Suggested resolution:** decide B16 — (a) accept any non-empty symbol (basic format only), subscribe, and surface
  a later subscription/`contractDetails` failure; or (b) require a live IBKR `reqContractDetails` lookup before
  adding (only when connected; block/hold when disconnected). Whichever is chosen, `AC-D22.4` forbids silent
  success.
- **Status:** resolved (B16 answered 2026-10-07 — the add performs a live IBKR `reqContractDetails` lookup before adding; unresolved symbols are rejected with nothing persisted). **New plumbing required:** the repo has no `reqContractDetails`/`contractDetails` path today — see DG43.

## DG40 — D22: adding a symbol while IBKR is disconnected may not survive because the panel is cleared on disconnect
- **Where it shows up:** D22 / Journey 27 edge cases; `ui/main_window.py` (`_on_disconnected` → `watchlist_panel.clear()`
  `:2107`; `_restore_watchlist` runs on `_on_connected` only); `ui/watchlist_panel.py::clear()` / `add_symbol()`.
- **Why it matters:** `clear()` cancels subscriptions and **empties the table** on disconnect, and the panel is only
  repopulated by `_restore_watchlist` on connect. A symbol added while disconnected would be appended to the
  (possibly empty) table and persisted, but the visible state is governed by the DB on the next connect. If the add
  path writes the DB **before** `clear()` or relies on the table's current rows to rebuild the list, the persisted
  set could be wrong (e.g. seeding `DEFAULT_WATCHLIST` again because the in-memory list looks empty).
- **Suggested resolution:** make the DB the source of truth for the symbol list and have the add path persist the
  **union of the persisted list and the new symbol** (not the table's transient rows); confirm the disconnected-add
  behaviour per B16/A49. Non-blocking beyond B14/B16.
- **Status:** resolved (B16b answered 2026-10-07 — adding is **disallowed while IBKR is disconnected**, so the add-while-disconnected persistence question no longer arises; on reconnect `_restore_watchlist` repopulates from the DB. The `clear()`/`_restore_watchlist` interaction is still recorded here for Plan).

## DG41 — D22: persistence via the replace-all `set_watchlist` vs new add/remove DB helpers
- **Where it shows up:** D22 / `AC-D22.2`; `data/db.py::get_watchlist` (`:125`) / `set_watchlist` (`:131`).
- **Why it matters:** `set_watchlist` **replaces the whole list** (DELETE + INSERT), and `_restore_watchlist` uses it
  to seed `DEFAULT_WATCHLIST` only when the DB list is empty. An add (or remove) path must not accidentally trigger
  the seed-again branch or drop `category`/`sort_order`. There is no `add_watchlist_symbol`/`remove_watchlist_symbol`
  helper today.
- **Suggested resolution:** Plan chooses the mechanism — reuse `set_watchlist` with the full desired list (preserving
  `category` and contiguous `sort_order`), or add explicit `add`/`remove` helpers — but the requirement is the
  persisted outcome (`AC-D22.2`), and the seed-if-empty guard must not re-seed after an add. Non-blocking beyond B14.
- **Status:** open (non-blocking; implementation detail for Plan — B14 answered add + remove, so Plan must pick a mechanism that preserves `category`/contiguous `sort_order` and does not re-seed `DEFAULT_WATCHLIST` after an add/remove).

## DG42 — D22: the new add affordance must not shadow the D21.5 column header menu or the D21.11 collapse toggle
- **Where it shows up:** D22 / `AC-D22.5`; `ui/watchlist_panel.py` header strip (`header_bar`/`header_button`,
  `:254`–`:280`) vs the **table** column header context menu (`_on_header_context_menu`, `:422`).
- **Why it matters:** the D21.5 add/remove/rearrange **column** popup is wired to the *table's* horizontal header
  (`customContextMenuRequested`), while the D21.11 "Watchlist" toggle lives in the *panel* header strip. Adding a
  `+` button or a right-click → "Add symbol…" to the panel header strip must not intercept the column header's
  right-click, must not remove the collapse toggle, and must remain reachable when the watchlist body is collapsed
  (the header strip is the dock title bar). The word "add" is overloaded (add **column** vs add **symbol**) — the
  menu labels must be unambiguous.
- **Suggested resolution:** keep the column menu on the table header untouched; place the add-symbol affordance on
  the panel header strip (or a table-body context menu) with a distinct label ("Add symbol…"); verify the collapse
  toggle and the column popup still work. Non-blocking beyond B15.
- **Status:** resolved (B15a answered 2026-10-07 — the `+` button and the right-click "Add symbol…"/"Remove symbol" live on the **panel header strip** and must not shadow the D21.5 column popup or remove the D21.11 collapse toggle; verified by `AC-D22.1`/`AC-D22.8`).

---

## DG43 — D22: no IBKR contract-details request/callback path exists for the B16 live validation
- **Where it shows up:** D22 / `AC-D22.4`; `ibkr/client.py` (callback surface), `ibkr/contracts.py::get_contract_for_symbol`; the add flow.
- **Why it matters:** B16 requires a **live IBKR contract lookup** before adding, but the codebase has **no**
  `reqContractDetails` call and **no** `contractDetails` / `contractDetailsEnd` callback on `IBApiClient` (a repo
  grep returns none). The live-validation requirement therefore needs a **new** request + callback + result routing
  (with error/timeout handling) before it can be implemented — it is not a change to an existing path.
- **Suggested resolution:** Plan adds a contract-details request path (request, `contractDetails`/`contractDetailsEnd`
  callbacks, an error/timeout path, and a result the add flow can await) that resolves a symbol to at least one
  contract; the add proceeds on resolution and is rejected (nothing persisted) on failure/timeout. Non-blocking
  beyond B16 (answered 2026-10-07); the requirement outcome is fixed by `AC-D22.4`.
- **Status:** open (non-blocking; implementation path for Plan — the requirement is settled)

## DG44 — D22: the `_restore_watchlist` seed-if-empty branch can re-seed `DEFAULT_WATCHLIST` after the user removes every symbol
- **Where it shows up:** D22 / `AC-D22.6`, `AC-D22.7`; `ui/main_window.py::_restore_watchlist` (`if not symbols: symbols = list(DEFAULT_WATCHLIST); db.set_watchlist(symbols)`); `data/db.py::get_watchlist`/`set_watchlist`.
- **Why it matters:** D22's **remove** makes an explicitly-emptied watchlist meaningful, but the existing
  seed-if-empty branch re-seeds the five defaults whenever the DB list is empty — so removing the last symbol would
  appear to "come back" after a restart, contradicting `AC-D22.7`'s persisted outcome.
- **Suggested resolution (non-blocking default A52):** distinguish "never configured" from "explicitly emptied" (e.g.
  a persisted sentinel/flag, or seed only on a genuine first run) so an emptied watchlist stays empty; otherwise the
  seed-if-empty branch must not fire after an explicit removal. Plan's call; recorded so the persistence outcome is
  not silently violated.
- **Status:** open (non-blocking; default A52, interaction to settle in Plan)


## DG45 — D23.1 (ESC-030): the contract-details cancel requirement conflicts with the pinned ibapi surface
- **Where it shows up:** D22 task-level `AC-D22.2.3` (`docs/tasks/task-graph.json`, task `D22-02`) and architecture
  `S3` (`docs/architecture.md:1863`) vs the pinned dependency `ibapi` **9.81.1.post1**; the implementation
  `ibkr/market_data.py::MarketDataManager.cancel_contract_details` (`:78–84`).
- **Why it matters:** `AC-D22.2.3` mandates that `cancel_contract_details` call `client.cancelContractDetails(req_id)`,
  but the pinned `EClient` exposes **no** `cancelContractDetails` (`hasattr(EClient,'cancelContractDetails') is
  False`; only `reqContractDetails` exists). As written, the implemented call raises `AttributeError`, which the
  enclosing `try/except Exception: pass` silently swallows → the cancel is a **no-op on the wire** and the D22 test
  passes only because `tests/test_ibkr_contract_details_d22.py::_FakeClient` defines the missing method. This is an
  inconsistency between a stated requirement/architecture and the actual dependency surface, so Task Manager could
  not write an honest task against it without inventing the behaviour.
- **Suggested resolution:** make the cancel a **capability-guarded, documented** best-effort call (call the client
  method only if present; document that TWS's own `contractDetailsEnd`/error ends the request and that
  `ContractLookupService`'s local invalidation — bounded QTimer + `cancel_all` on disconnect — is the safety net),
  and correct `AC-D22.2.3` + reconcile architecture `S3` accordingly. Captured as requirement **D23.1**
  (`AC-D23.1.1`–`AC-D23.1.4`, correction record).
- **Status:** addressed — captured as the D23.1 requirement (2026-10-07); the correction record directs the Task
  Manager (`AC-D22.2.3`), Build (guard + comment + test), and Plan/Validator (`S3` reconciliation) to apply it.
  No blocking user question was required (evidence-derived; user approved the fix).
