# Design Gaps

> Owned by Requirements Analyst. Non-blocking inconsistencies or missing pieces in
> the requested design that should be resolved before/while building, but do not
> halt progress.

> **Source-citation convention (adopted 2026-10-14; resolves DG56 — the full statement is in
> `requirements.md`'s Status/audit block).** Cite a **symbol** as the primary pointer — `path::symbol`,
> e.g. `ui/main_window.py::MainWindow._open_popout`, `config/settings.py::MAX_POPOUTS`. A bare line
> number or range is **indicative only**: it records where the code sat when the entry was written and
> may drift (commit `99fb8fa`, a 5-line insert, invalidated ~10 such ranges). Resolve by symbol, not by
> line. Entries that describe code **as it was at their own commit** keep their line references and are
> tagged `[historical]`; they are deliberately *not* re-pointed at current lines.

## DG1 — D1 session shading applies equity sessions to every symbol
- **Where it shows up:** D1 / Journey 2.
- **Why it matters:** Futures trade nearly 24 hours and have different session
  boundaries; applying the equity `04:00–20:00 ET` model may mis-shade them.
- **Suggested resolution:** Keep the accepted default for this run; if futures are
  ever charted with shading, add a per-contract session map.
- **Status:** **closed 2026-10-14 — accepted default, not a defect.** Verified: `services/session_service.py`
  is explicitly an **equity** RTH/ETH model (pre-market 04:00–09:30 ET, post-market 16:00–20:00 ET) with no
  `secType`/per-contract handling — i.e. exactly the "keep the accepted default for this run" disposition this
  entry proposed. Futures charted with shading therefore follow the equity bands; that is a **known limitation**,
  deferred as feature suggestion **FS16** (per-contract session map), not an open gap.

## DG2 — D2 chip decimal precision is unspecified
- **Where it shows up:** D2 / AC-D2.1.
- **Why it matters:** "Complete label including all decimals" is only objectively
  testable once the precision source is fixed, and it should match the price axis.
- **Suggested resolution:** Reuse the axis tick precision (current tag uses
  `f"{y:,.2f}"`); confirm during build. See assumption A5.
- **Status:** resolved 2026-10-14 — the precision source is fixed in code: the D2 chip formats `f"{y:,.2f}"` (`ui/chart_panel.py:1093`), matching A5. (No test asserts chip-vs-axis precision equality; cosmetic only.)

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
- **Status:** **resolved 2026-10-14** — the residual sub-question is answered by the shipped code: the
  magnifier reverts to Cursor on **both** a symbol change and a timeframe change, exactly as assumption **A6**
  proposed. `ui/chart_panel.py::ChartPanel.set_symbol` carries "Reset magnifier on symbol change (A6)" and
  calls `set_zoom_mode(False)`; `::ChartPanel.set_timeframe` does the same on the timeframe path. Recorded as
  **TR-12** in the router transition table (`ZOOMING` + symbol/timeframe change → `IDLE`). The
  transition-specification part was already resolved (see above), so nothing remains.

## DG4 — No GUI-level regression tests exist despite the `test_gui.md` spec
- **Where it shows up:** Test coverage for all D1–D3 UI changes.
- **Why it matters:** The spec describes 11 `tests/test_gui*.py` files; none exist.
  UI-only fixes risk having no GUI-level regression guard beyond import smoke tests.
- **Suggested resolution:** Add targeted `pytest-qt` offscreen checks per defect
  (e.g. overlay band geometry, chip bounds, zoom button signals). A full GUI suite
  remains out of scope for this run.
- **Status:** resolved 2026-10-14 — the `test_gui.md` 11-file suite is still absent, but GUI-level offscreen pytest-qt coverage now exists extensively (e.g. `tests/test_toolbar_d20.py`, `tests/test_dock_widths_d17.py`, `tests/test_d24_popouts.py`, `tests/test_d37_microstructure.py`), so the "no GUI-level regression guard" concern no longer holds.

## DG5 — D4 zoom cluster position depends on dynamic price-axis width
- **Where it shows up:** D4 / AC-D4.2.
- **Why it matters:** The right price axis width varies with price magnitude (e.g.,
  5-digit prices are wider); a fixed 28px margin still overlaps the axis, while a
  fixed 12px left-of-axis offset may be too conservative on narrow axes.
- **Suggested resolution:** Position as `panel.width - ctrl.width - axis_width - 12`
  with `axis_width = price_plot.getAxis('right').width()` (fallback 50) and `x >= 8`
  clamp. See Q16, R6, A8.
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q16 answered):
  `ui/chart_panel.py::ChartPanel._position_zoom_controls` derives the axis width live —
  `axis_w = self.price_plot.getAxis('right').width()` — and positions the cluster relative to it, so the cluster
  stays left of a dynamically-sized price axis.

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
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q18 answered): in `ui/candlestick_item.py`
  the wick and body outline are drawn with `setWidthF(1.0)` + `setCosmetic(True)` (device-pixel stable at any
  density), while the body half-width is clamped to a 4-device-pixel minimum (`min_w = 2.0 / px_per_sec`;
  `if w < min_w: w = min_w`). The body therefore stays ≥4× the 1px wick at high bar density.

## DG8 — D7 gap vs framing — inter-candle gap vs outer padding
- **Where it shows up:** D7 / AC-D7.1, AC-D7.2.
- **Why it matters:** "More spacing" could be achieved by narrowing bodies (larger
  inter-candle gap) or by widening `xRange` (more outer padding). The two have
  different effects on density and session-band framing.
- **Suggested resolution:** Use inter-candle gap (body half-width `0.325` instead of
  `0.40`, gap 35% of spacing, confirmed Q19) as proposed in Q19; keep `xRange`
  `-2*bar_w / +8*bar_w` unchanged. See Q19, A11, R9.
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q19 answered):
  `ui/candlestick_item.py:111` — `w = median_diff * 0.325  # half-width = 32.5% of spacing (gap 35%)`, with the
  `xRange` framing (`-2*bar_w / +8*bar_w`) unchanged. The gap is achieved by narrowing bodies, not by widening
  the frame, as decided.

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
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q21 answered): `ui/chart_panel.py:1690` —
  `self.volume_bars.setOpts(x=vol_x, height=vol_h, width=w_vol*2, brushes=vol_colors)` — the volume bars share
  the price body's `w` (width `w*2`, 35% gap) with X still `setXLink`ed, so price and volume columns align.

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
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q23 answered): `ui/drawing_overlay.py`
  places the inner-right labels **inside the plot** — `anchor=(1, 0.5)` (`:385`) at
  `view_rect_scene.right() - 4` (`:392`) — with positioning and stacking finalised by
  `_update_inner_labels()` (`:377`).

## DG13 — D12 zone popup — Extend omitted, 4 tabs
- **Where it shows up:** D12 / AC-D12.1, Style tab.
- **Why it matters:** The reference Style tab shows an `Extend` dropdown, but the
  requirement says the zone must always extend both sides. Omitting the control is a
  deliberate divergence that should be explicit.
- **Suggested resolution:** Omit `Extend` entirely (zone always both-sides) and
  keep `Border`, `Middle line`, `Background` as shown; double-click is the only
  opener. See Q24, A16, R14.
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q24 answered):
  `ui/zone_settings_dialog.py` provides four tabs (Style / Text / Coordinates / Visibility) and carries an
  explicit `# NOTE: no "Extend" control — zone always extends both sides (Q24)`; `Border`, `Middle line` and
  `Background` remain as shown in the reference.

## DG14 — D15 horizontal line popup — single coordinate vs zone
- **Where it shows up:** D15 / AC-D15.1, Coordinates tab.
- **Why it matters:** Zones need `#1 / #2 (price, bar)` while a horizontal line
  needs only `#1 (price)`; reusing the zone dialog could show an irrelevant second
  coordinate.
- **Suggested resolution:** Keep a dedicated `Horizontal line` dialog with single
  `#1 (price)` stepper (as per the attachment) or hide `#2` when `kind ==
  "horizontal"`. See Q30, A17, R15.
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q30 answered):
  `ui/horizontal_line_settings_dialog.py` is a **dedicated** horizontal-line dialog (not the zone dialog) with
  four tabs (Style / Text / Coordinates / Visibility) and a single `#1 (price)` field — no bar, no `#2`.

## DG63 — D13 watchlist width 50% + persistence — mechanism and clamping  *(renumbered from DG14, 2026-10-14 — see DG60)*
- **Where it shows up:** D13 / AC-D13.1–D13.3 / Journey 14.
- **Why it matters:** "Freely draggable to 50%" needs an explicit min/max and a concrete persistence store; without it the build may pick a different store or miss the `W−400` chart-minimum clamp, causing chart collapse on small windows or loss of width on restart.
- **Suggested resolution:** Enforce `[150, min(floor(0.50×W), W−400)]` for docked watchlist (chart ≥400px) with resize-time clamping; persist via `QSettings("NDThinkChart","watchlist/width")` (or DB key) as integer pixels, restore clamped to current 50%, default 220px; floating dock not constrained. See Q25–Q26, A17, R15, R17.
- **Status:** **resolved 2026-10-14** — implemented as proposed (Q25–Q26 answered):
  `ui/dock_layout.py::watchlist_max_width` returns
  `max(WATCHLIST_MIN_WIDTH, min(floor(0.50 * chart_area_w), chart_area_w - CHART_MIN_WIDTH))` — precisely the
  proposed `[150, min(floor(0.50×W), W−400)]` clamp, with `CHART_MIN_WIDTH = 400`; the width persists via
  `QSettings` under `WATCHLIST_WIDTH_KEY = "watchlist/width"` (`ui/watchlist_panel.py:96`) and is clamped on
  restore by `load_watchlist_width(...)`.

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
  *(The `PENDING_IMPLEMENTATION_PLAN.md` half of this entry is now moot: the owner deleted
  that file on 2026-10-15, after both corrections below had been applied.)*
- **Suggested resolution:** DOC-1 correction is mechanical (use measured 339 / ~2.9s).
  DOC-2 ownership is decided (Q34, answered 2026-09-27): the **Requirements Analyst owns
  closing DOC-2** (mark Phases 1–5 `✅ COMPLETE`); **Code Reviewer verification** is the
  confirming step. Because `PENDING_IMPLEMENTATION_PLAN.md` is outside the Analyst's
  file-ownership table, the Analyst records the requirement/ownership in `requirements.md`
  rather than editing the root doc; any residual owner action is a recorded dependency. DOC-3
  is covered by ESC-001 (BUILD).
- **Status:** **partially resolved 2026-10-14 — DOC-2 and DOC-3 resolved; DOC-1 re-drifted (owner).**
- **DOC-2 — resolved.** `PENDING_IMPLEMENTATION_PLAN.md` marked **all ten** phases `✅ COMPLETE`
  (Phases 1–5 were added in commit **`fe5a63f`**; 6–10 already carried their markers) —
  verified before the file was deleted on 2026-10-15.
- **DOC-3 — resolved.** The source-less bytecode is gone: `tests/test_db_schema.py` was added in
  commit **`952a083`**, so the previously orphaned `test_db_schema*.pyc` now has a matching source.
  (Same workstream as ESC-001.)
- **DOC-1 — re-drifted.** The counts were corrected "269" → "383" in `fe5a63f`, but the suite is now
  **1028**, so any hard-coded total goes stale on the next batch. **Fix applied 2026-10-14:** the
  *current-use* figure in `usage.md` no longer hard-codes a total (it points the reader at `pytest`),
  and `PENDING_IMPLEMENTATION_PLAN.md` stated up front that its per-phase "N passed" figures are
  **historical records of that phase's run**, not the current number. This ended the drift class —
  and the file itself was deleted on 2026-10-15, removing the last surface for it.
- **Residual:** none expected. The root docs remain outside the Analyst's file-ownership table, so a
  future owner edit there is a recorded dependency rather than an agent action.

## DG15 — D14 double-click row to load chart — scope and no-ops
- **Where it shows up:** D14 / AC-D14.1–D14.4 / Journey 15.
- **Why it matters:** "Double-click anywhere on the row" must be distinguished from header/empty-area clicks and from same-symbol/disconnected no-ops; otherwise single-click selection could be mistaken for a load or a disconnected double-click could queue a request.
- **Suggested resolution:** Wire `QTableWidget.cellDoubleClicked(int,int)` and resolve row Symbol via `COL_SYMBOL`; ignore when `row<0` or `symbol` empty/header; case-insensitive compare to `_current_symbol` for no-op; check `ConnectionState` / `load_btn.isEnabled()` before issuing `req_historical_data`; show status message on disconnected as specified. See Q27–Q29, A18–A19, R16.
- **Status:** resolved 2026-10-14 — D14 is built: `ui/watchlist_panel.py::WatchlistPanel` wires `cellDoubleClicked` (cited `:432` — indicative); `AC-D14.1`–`AC-D14.4` are final per Q27–Q29.


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
- **Status:** **closed 2026-10-14 — not a defect; recorded as an out-of-scope enhancement
  (`docs/requirements/feature_suggestions.md` FS15).** Re-verified against the tree:
  `BarCache.save_bars` has exactly **one** caller, `ui/main_window.py::MainWindow._finalize_history_wave`
  (the historical path), so bars aggregated from the live stream still update only the in-memory `_bars` and
  are lost on restart. That is a **deliberate scope boundary** of D16 — which heals *visible* holes by
  load-time backfill — not a defect, so it is an enhancement suggestion rather than an open gap. The original
  analysis above is kept for the record.

## DG19 — D16: IBKR per-request duration/bar limits vs a long backfill
- **Where it shows up:** D16 / `AC-D16.4`; `TIMEFRAME_CONFIG` is a single fixed duration per
  timeframe.
- **Why it matters:** if the cache gap exceeds what one IBKR request returns for that bar
  size, a single enlarged request may still leave a hole. The fix must chunk or the
  shortfall must be surfaced.
- **Suggested resolution:** chunk backfill requests (respecting `pacing_manager`) or size a
  single request to the gap when within IBKR limits; document the bound.
- **Status:** resolved 2026-10-14 — chunked waves are implemented: `ui/ticker_session.py::TickerSession._issue_wave_chunks` (`:1529`) issues ~60 `reqHistoricalData` chunks per wave against the rolling 600s budget (`config/settings.py::MAX_HISTORICAL_PER_600S = 60`, `:35`), with continuation across waves (D28.3).

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
  leave the reported hole unfixed. `data/bar_cache.py::BarCache.get_last_timestamp` exists (cited `:33`, now `:55` — indicative) but is not
  used by `load_chart`, which fetches `endDateTime=""` with the fixed `TIMEFRAME_CONFIG` duration
  (`ui/main_window.py::MainWindow.load_chart`; cited `:430–444` — indicative).
- **Suggested resolution:** State the requirement as an outcome (continuous bar series over the
  displayed span) — already done in `AC-D16.1`/`AC-D16.5` — and have Plan detect the missing span
  from the cached series (e.g., the largest gap between consecutive cached blocks, or between the
  last pre-gap bar and now) rather than only `MAX(ts)`, then backfill that span in chunks. The
  tail-gap case is a special case of the same mechanism.
- **Status:** resolved 2026-10-14 — the shipped detector handles internal holes, not only a tail anchor: `services/backfill_service.py:239` `_bar_level_missing_spans` finds "Internal gaps between consecutive cached bars" (`:285`) as well as session-window gaps, at bar-period granularity (D27.7).

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
- **Where it shows up:** D17 / D13 / `ui/main_window.py::MainWindow.resizeEvent` (line range `~962-968` when written — indicative),
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
- **Status:** resolved 2026-10-14 — B1 was answered 2026-10-03 (cap = **50% of the chart area**), so this was never left blocking; D17 is built and merged (`ui/dock_layout.py`, `ui/main_window.py` dock hooks, `AC-D17.1`–`AC-D17.6`).

## DG24 — D18: the right docks have no width governance at all and are an unaccounted horizontal consumer
- **Where it shows up:** D18 / `ui/main_window.py:234-252` (`[historical]` 2026-10-03; the `RightDockWidgetArea` setup, now `ui/main_window.py::MainWindow` init ~`:464–523`);
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
- **Status:** resolved 2026-10-14 — B2/B3 were answered 2026-10-03 (one right-dock region, 40% of the chart area, combined cross-clamp); built as `ui/dock_layout.py::plan_dock_widths` + `MainWindow._apply_dock_widths` (`AC-D18.1`–`AC-D18.8`).

## DG25 — D18: "fits in the visible area of the full screen" is not yet a testable condition
- **Where it shows up:** D18 / provisional `AC-D18.1`.
- **Why it matters:** "reposition so that it fits in the visible area" can be satisfied many ways
  (reduce width, reduce content minimum, auto-hide, re-dock). Without a concrete condition the
  criterion is not independently testable (violates the Quality Bar's "no vague terms" rule).
- **Suggested resolution:** express as a measurable condition — e.g. the Active Trader/Portfolio dock's
  right edge `<= window right edge` and left edge `>= chart right edge` in full screen, with a
  non-zero visible width, and the chart still ≥ its minimum. Confirm once B2/B3 are answered.
- **Status:** resolved 2026-10-14 — B2/B3 answered 2026-10-03 and `AC-D18.1` is the measurable condition (right region within the window rect, non-zero visible width, chart >= 400px).


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
- **Where it shows up:** D20 / D19 / `AC-D19.4`; `ui/main_window.py:102` (`toolbar.setFixedHeight(36)`), `:233` — `[historical]` D19/D20 snapshot 2026-10-06
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
- **Where it shows up:** D21.11 / `ui/main_window.py` watchlist dock title (`:258`, `[historical]` 2026-10-06), `ui/watchlist_panel.py`
  in-panel header strip (`:117–124`).
- **Why it matters:** B12 keeps the **in-panel header label** as the hide/show toggle and deletes the duplicate
  **dock title bar**. A `QDockWidget`'s title bar is normally what the user drags to move/float the dock, so
  removing it may leave the watchlist un-draggable unless an equivalent handle is provided. The toggle button must
  stay visible when the watchlist is hidden, which a title bar could not do.
- **Suggested resolution:** keep the in-panel header button as the toggle; if the dock must remain movable, give
  the header strip a drag handle (or retain a frameless/title-bar drag region) so docking still works. Plan/Build
  to choose the exact mechanism; the requirement outcome (single toggle that stays visible when hidden) is fixed.
- **Status:** resolved 2026-10-14 — the header strip itself is the dock's title-bar widget (`ui/main_window.py::MainWindow` — `setTitleBarWidget(self.watchlist_panel.header_bar)`, `:400`) with `DockWidgetMovable` retained (`:401–403`), so the toggle stays visible when hidden and the dock is still movable.

## DG38 — D21.13: the right dock's title bar becomes the "Active Trader" toggle button
- **Where it shows up:** D21.13 / `ui/main_window.py` right dock region (`:295–337` — indicative).
- **Why it matters:** B12 makes the right dock's **title bar** the "Active Trader" hide/show button. The title bar
  is also the region's drag/hide affordance, so making it a toggle must not break moving the dock or reconcile
  badly with the existing DOM button (which hides the whole region).
- **Suggested resolution:** make the title-bar label a clickable toggle while keeping a drag region; treat a
  fully-collapsed region as hidden for the D17/D18 cross-clamp (`DG35`); reconcile with `_on_dom_toggled`.
- **Status:** resolved 2026-10-14 — the right dock's title-bar widget is the Active Trader header button (`ui/main_window.py::MainWindow` — `setTitleBarWidget(self.active_trader.header_bar)`, `:493`; `setFeatures` `:494`) with the toggle wired at `:531` (indicative), and `Movable` retained.


---

## DG39 — D22: no offline symbol validation exists, so an unknown/invalid ticker cannot be rejected locally
- **Where it shows up:** D22 / `AC-D22.4`; `ibkr/contracts.py::get_contract_for_symbol` (cited `:169`, now `:220` — indicative); `data/db.py`
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
- **Where it shows up:** D22 / `AC-D22.2`; `data/db.py::get_watchlist` (cited `:125`, now `:188`) / `data/db.py::set_watchlist` (cited `:131`, now `:235`) — both indicative.
- **Why it matters:** `set_watchlist` **replaces the whole list** (DELETE + INSERT), and `_restore_watchlist` uses it
  to seed `DEFAULT_WATCHLIST` only when the DB list is empty. An add (or remove) path must not accidentally trigger
  the seed-again branch or drop `category`/`sort_order`. There is no `add_watchlist_symbol`/`remove_watchlist_symbol`
  helper today.
- **Suggested resolution:** Plan chooses the mechanism — reuse `set_watchlist` with the full desired list (preserving
  `category` and contiguous `sort_order`), or add explicit `add`/`remove` helpers — but the requirement is the
  persisted outcome (`AC-D22.2`), and the seed-if-empty guard must not re-seed after an add. Non-blocking beyond B14.
- **Status:** resolved 2026-10-14 — dedicated helpers now exist: `data/db.py::add_watchlist_symbol` (`:194`) and `remove_watchlist_symbol` (`:213`); `set_watchlist` (`:235`) keeps `category` + explicit `sort_order`. D22 is built (`AC-D22.1`–`AC-D22.9`).

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
- **Status:** resolved 2026-10-14 — the path is built: `ibkr/market_data.py::MarketDataManager.req_contract_details` (cited `:85`, now `:88` — indicative) + `contractDetails`/`contractDetailsEnd` callbacks + `services/contract_lookup_service.py` (bounded `QTimer`, `cancel_all`). D22's add validates live per B16.

## DG44 — D22: the `_restore_watchlist` seed-if-empty branch can re-seed `DEFAULT_WATCHLIST` after the user removes every symbol
- **Where it shows up:** D22 / `AC-D22.6`, `AC-D22.7`; `ui/main_window.py::_restore_watchlist` (`if not symbols: symbols = list(DEFAULT_WATCHLIST); db.set_watchlist(symbols)`); `data/db.py::get_watchlist`/`set_watchlist`.
- **Why it matters:** D22's **remove** makes an explicitly-emptied watchlist meaningful, but the existing
  seed-if-empty branch re-seeds the five defaults whenever the DB list is empty — so removing the last symbol would
  appear to "come back" after a restart, contradicting `AC-D22.7`'s persisted outcome.
- **Suggested resolution (non-blocking default A52):** distinguish "never configured" from "explicitly emptied" (e.g.
  a persisted sentinel/flag, or seed only on a genuine first run) so an emptied watchlist stays empty; otherwise the
  seed-if-empty branch must not fire after an explicit removal. Plan's call; recorded so the persistence outcome is
  not silently violated.
- **Status:** resolved 2026-10-14 — implemented via the persisted sentinel `ui/main_window.py::WATCHLIST_CONFIGURED_KEY = "watchlist/configured"` (`:114` — indicative), so an explicitly emptied watchlist is not re-seeded with `DEFAULT_WATCHLIST` (A52).


## DG45 — D23.1 (ESC-030): the contract-details cancel requirement conflicts with the pinned ibapi surface
- **Where it shows up:** D22 task-level `AC-D22.2.3` (`docs/tasks/task-graph.json`, task `D22-02`) and architecture
  `S3` (`docs/architecture.md:1863`) vs the pinned dependency `ibapi` **9.81.1.post1**; the implementation
  `ibkr/market_data.py::MarketDataManager.cancel_contract_details` (`:78–84` — `[historical]` D23 report time; now `:108`).
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

---

## DG46 — D36–D40 acceptance criteria are cited everywhere but never defined
- **Where it shows up:** `requirements.md` Journeys 31–35 (`:640`, `:663`, `:691`, `:732`, `:773`) each carry an
  "As-built note" naming `AC-D36.1`–`AC-D36.5`, `AC-D37.1`–`AC-D37.5`, `AC-D38.1`–`AC-D38.6`, `AC-D39.1`–`AC-D39.5`,
  `AC-D40.1`–`AC-D40.5` as "verified", and downstream `docs/architecture.md` cites `AC-D36.3`/`AC-D38.4` while
  `docs/plan.md` cites `AC-D38.4`/`AC-D40.1`–`AC-D40.4`. **No `### D36 —`…`### D40 —` feature sections exist**,
  and no Given/When/Then text for these IDs exists anywhere in `requirements.md`.
- **Why it matters:** the Quality Bar requires every acceptance criterion to be independently testable, and the
  Task Manager / Code Reviewer trace work to AC IDs. As written, these IDs are **dangling references** — the IDs
  are asserted "verified" but have no normative statement to verify against. The tests that back them do exist
  (`tests/test_d36_footprint.py` `test_ac_d36_1..3`, `tests/test_d37_microstructure.py` `test_ac_d37_1..3`,
  `tests/test_d38_events_news.py` `test_ac_d38_1..5`, `tests/test_d39_burst_search.py` `test_ac_d39_1..4`,
  `tests/test_d40_tws_lifecycle.py`), so the criteria are implicitly testable but not written down.
- **Suggested resolution:** author `### D36`–`### D40` feature sections whose numbered ACs mirror the shipped
  tests, copying the behavioural assertions out of the Journey "As-built note"s. Not a silent fix — requires the
  owner's sign-off that the as-built behaviour is the intended requirement.
- **Status:** resolved 2026-10-14 (Q45) — D36–D40 feature sections and `AC-D36.*`–`AC-D40.*` authored from the shipped behaviour and its backing tests (`tests/test_d36_footprint.py` … `tests/test_d40_tws_lifecycle.py`).

## DG47 — D24–D28 are marked "DRAFT, owner review required" in the body while the code is built and merged
- **Where it shows up:** `requirements.md` `:2583` (D24), `:2698` (D25), `:2757` (D26), `:2809` (D27), `:2869` (D28)
  each read "DRAFT … owner review required"; but the code ships on `main` (`ui/ticker_session.py`,
  `ui/popout_window.py`, `data/popout_store.py`, `services/alarm_monitor.py`, order-path fixes) and
  `docs/architecture.md` records Phase 1–4 as-built and merged at `b366b19` (855→898 tests green). The branch's
  former footer asserted "Status: READY_FOR_PLAN — owner-approved 2026-10-12 (batches D24–D28)".
- **Why it matters:** the two statements contradict. Either the batches are owner-approved (so the DRAFT markers
  are stale and should be flipped) or they still await owner review (so no footer may claim `READY_FOR_PLAN`).
  This merge keeps the DRAFT markers and makes the footer `Status: DRAFT` accordingly; a clean READY_FOR_PLAN
  cannot be asserted until the owner confirms.
- **Suggested resolution:** owner confirms D24–D28 → flip the five section headers and the footer.
- **Status:** resolved 2026-10-14 (Q41) — the owner approved D24–D28 as already-developed/coded; the five sections are re-statused as-built/APPROVED and the footer reads `Status: READY_FOR_PLAN`. The owner also asked for a section-by-section code cross-check (below).

## DG48 — D24.9 is stated twice (`D24.9` and `AC-D24.9`)
- **Where it shows up:** `requirements.md` `:2680` (`**D24.9 (pop-out restore across restarts) [NEW v1.2,
  owner-confirmed 2026-10-12]**`) is immediately followed at `:2685` by `**AC-D24.9 (restore)**`. The first
  statement omits the `AC-` prefix; the second restates the same criterion in slightly different words.
  `docs/architecture.md` and `docs/plan.md` both cite the bare `D24.9`.
- **Why it matters:** an AC number must map to exactly one testable statement. Two paragraphs share the number,
  with different wording ("approximate geometry" vs "identical symbol/timeframe/mode/ext-hours and approximate
  geometry; no duplicate subscriptions"), so a reader cannot tell which is normative.
- **Suggested resolution:** merge into one numbered `AC-D24.9 (restore)` block; keep the "no duplicate
  subscriptions" clause (it is the stronger, more testable form).
- **Status:** resolved 2026-10-14 (Q41) — the two D24.9 statements are merged into a single normative `AC-D24.9 (restore)` block (keeping the stronger "no duplicate subscriptions" clause).

## DG49 — the D24–D28 intro note cross-references identifiers that do not exist
- **Where it shows up:** `requirements.md` `:56` — "See D24–D28, **Journeys 29–30**, `AC-D24.*`–`AC-D28.*`,
  **A56–A66**, R51–R60, **DG46–DG52**."
- **Why it matters:** `A66` does **not** exist (the Assumptions Log ends at `A65`); `DG46–DG52` did not exist
  before this merge (design_gaps.md ended at `DG45` — this run adds DG46–DG52); and "Journeys 29–30" is stale
  (the file now carries Journeys 29–35). Dangling identifiers make downstream tracing unreliable.
- **Suggested resolution:** correct the list to "Journeys 29–35, `AC-D24.*`–`AC-D40.*`, A56–A65, R51–R60,
  DG46–DG52" (or add the missing `A66` if an assumption is intended). Partially resolved here: DG46–DG52 now exist.
- **Status:** resolved 2026-10-14 (Q41) — the intro cross-references are corrected to "Journeys 29–35, `AC-D24.*`–`AC-D40.*`, A56–A67, R51–R60, DG46–DG52"; A66/A67 now exist (added for the Q43/Q44 defaults).

## DG50 — Batches D29–D35 have no requirement text anywhere
- **Where it shows up:** the batch numbering jumps from `D28` (`requirements.md:2869`) straight to `D36`
  (Journey 31, `:640`). There is no `### D29`–`### D35` section, no journey, and no reference to them in
  `docs/architecture.md` or `docs/plan.md`.
- **Why it matters:** readers and the Validator cannot tell whether D29–D35 were folded, renumbered, or simply
  never written. Not blocking (nothing downstream cites them), but it leaves an unexplained hole in the audit
  trail and invites a future mis-numbering.
- **Suggested resolution:** record an explicit note (e.g. "D29–D35 intentionally unassigned / folded") or
  backfill the batches if they exist.
- **Status:** resolved 2026-10-14 (Q41) — the D29–D35 gap is now recorded explicitly in the `requirements.md` Status block as an intentional numbering gap (not missing content). *(Corroborated 2026-10-14 against the changelog: `docs/phase-changelog.md:53` records D26.3's real-leg transmission as a follow-up "proposed **D29**", i.e. D29+ were reserved for planned follow-up batches rather than lost.)*

## DG51 — D37 depth-heatmap default ON is unconfirmed and conflicts with the D36 OFF precedent
- **Where it shows up:** `requirements.md` Journey 32 `:687` — "**Pending owner confirmation:** depth heatmap
  default ON (reviewer recommends OFF, consistent with D36)". Code: `ui/chart_panel.py::ChartPanel.__init__` (cited `:368-369`) unconditionally
  constructs `DepthHeatmapItem()` and adds it to `price_plot`; D36 footprint, by contrast, is **OFF by default**
  (owner decision 2026-10-13).
- **Why it matters:** a default-visible panel is user-visible behaviour shipped without the owner's confirmation,
  and it is inconsistent with the adjacent D36 default. The reviewer's recommendation (OFF) contradicts the
  as-built state.
- **Suggested resolution:** owner confirms the default; if OFF, gate the item's creation/visibility on an explicit
  enable (matching D36).
- **Status:** resolved 2026-10-14 (Q44) — the owner confirmed the depth heatmap defaults **ON**, matching the shipped code (`ui/chart_panel.py::ChartPanel.__init__` — `:368`/`:370`, indicative); assumption A67 added and the "pending owner confirmation" wording removed from Journey 32.

## DG52 — D24–D40 owner-open items live only in footer prose, with no AC or test
- **Where it shows up:** `requirements.md:3131` — "**DEC-4 (pending owner nod)**" and "**Open:** always-on-top
  default for pop-outs …"; DEC-4 references a "G5" that has no location in this file.
- **Why it matters:** two owner decisions remain genuinely unresolved, yet they appear only as prose in the status
  block — there is no acceptance criterion, edge case, or test tied to them, so neither Plan nor Build can act on
  them, and nothing will fail if they are ignored. The "G5" reference is itself dangling.
- **Suggested resolution:** promote each to an explicit open question / assumption with an owner decision, then
  either add an AC or drop the item.
- **Status:** resolved 2026-10-14 — DEC-4 is resolved (Q42: the "gated in TWS" planning gate is retired) and the always-on-top default is resolved (Q43: OFF, `AC-D24.10`); both are now carried as requirements, not footer prose, and the dangling "G5" is recorded as resolved.

---

## DG53 — D24–D28 requirement-vs-code verification (owner-directed 2026-10-14, Q41)
- **Where it shows up:** D24–D28 (`requirements.md`) cross-checked against the merged code.
- **Result:** all shipped behaviours are captured as requirements/ACs, with three findings flagged (none silently
  deleted):
  - **D24 signal list corrected** — the requirement named a single `bars_updated` signal; the shipped
    `ui/ticker_session.py::TickerSession` signals (cited `:65–73`, now `:65–84` — indicative) emit `bar_updated` (incremental tick) **and** `bars_refreshed` (full series
    replace). The text now names both.
  - **D24 "connecting" indicator corrected** — the requirement asserted a per-pop-out "connecting" indicator
    when opened while disconnected; the shipped code renders cached bars but has **no** per-pop-out indicator
    (only the main window's `ui/main_window.py::MainWindow.conn_badge`, cited `:290`, now `:295` — indicative). The requirement text is corrected rather than
    asserting behaviour the code lacks; a per-window indicator would be a new request.
  - **D24 cap "disabled" clause flagged (AC-D24.5)** — the requirement says the pop-out action is **disabled** at
    the 10-cap; the shipped code refuses the 11th with a status-bar message (`ui/main_window.py::MainWindow._open_popout`, cited `:840–846` — indicative) but does
    **not** `setEnabled(False)` the affordance. Recorded as a narrower shipped behaviour (AC-D24.5 carries the note);
    a literal disable would be a small follow-up if wanted.
  - **No silently-deleted requirements.** Verified shipped and matching: `MAX_POPOUTS = 10`
    (`config/settings.py::MAX_POPOUTS`, `:42`); `config/settings.py::check_live_port` fail-fast + `LIVE_PORT = 7496` (`:11–24`);
    D26.1 bracket children opposite-side (`ibkr/orders.py:91` — `child_action`); D26.2 `id_manager.reserve(3)`
    (`ui/main_window.py:3181`, cited `:3176` — indicative); D26.7 `validate_order` gate (`ibkr/validation.py`, wired at
    `ui/main_window.py:3112`, cited `:3107` — indicative); D26.8 kill switch `reqGlobalCancel` (`ui/main_window.py:3228`, cited `:3223` — indicative); D28.1
    `PacingExceeded`/`historical_wait_seconds` never sleeps (`ibkr/pacing.py`); D28.2 `TickerSession` extraction;
    D28.4 `SESSION_BAR_CAP = 5000` (`config/settings.py:45`); D24.9 `popouts` persistence (`data/popout_store.py`).
- **Status:** resolved 2026-10-14.

---

## DG54 — the pinned `ibapi` version has moved (9.81.1.post1 → 10.51.1) but the D23 record still names the old pin
- **Where it shows up:** `requirements.md:34` (D23 intro), `:232` (D23 overview), `:2484–2516` (D23.1, esp.
  `:2492` "The pinned dependency is `ibapi` **9.81.1.post1**" and `:2513` "`ibapi 9.81.1.post1` exposes no
  `EClient.cancelContractDetails`"), `:3172` (A53), `:3300` (Status); `open_questions.md:831`;
  `design_gaps.md:523` (DG45). The shipped code perpetuates it too: `ibkr/market_data.py:110–137`
  (docstring "The pinned ``ibapi 9.81.1.post1``") and `tests/test_ibkr_contract_details_d22.py:234–236` (indicative).
- **Why it matters:** `requirements.txt:3` pins **`ibapi-latest==10.51.1`** (installed `ibapi 10.51.01`), and
  D37/D38 already cite "the 10.51.1 wheel". A reader (or the Validator) checking a "pinned `ibapi`" claim gets
  the wrong version, and the D23.1 requirement's own "document it in code" clause names a version the tree no
  longer pins. **The behaviour is unaffected:** re-verified 2026-10-14 that
  `hasattr(EClient, 'cancelContractDetails') is False` on **10.51.1**, so `AC-D23.1.*` stands unchanged.
- **Changelog cross-reference (2026-10-14):** the pin change is **recorded and dated** — `docs/phase-changelog.md:376`
  (Phase D36, item **38a.0**): "`requirements.txt`: `ibapi>=9.81` → `ibapi-latest==10.51.1` (plain
  `ibapi==10.51.01` is not on PyPI — verified). Full suite re-run green on the aligned version before any D36
  code." So the D23-era figures were **correct when written** (2026-10-07) and the D36 upgrade (2026-10-13,
  after D22/D23) simply did not sweep the D23 prose, the code docstring or the test literal. The requirement text
  now cites the pin and the changelog rather than being re-worded per site.
- **Suggested resolution:** requirements/open_questions/design_gaps figures corrected 2026-10-14 (done, citing the
  changelog). **Re-routed to Build:** update `ibkr/market_data.py:110–137` (docstring "The pinned
  ``ibapi 9.81.1.post1``") and `tests/test_ibkr_contract_details_d22.py:234–236` — **only in the same change as
  `tests/test_d23_nonregression.py:61`**, which asserts the literal `"9.81.1.post1"` is present in that source
  (see DG61). Tests/code are not the Analyst's to edit.
- **Status:** **resolved 2026-10-14** — the Build-side residue is fixed. Commit **`bb7f667`** made the
  `ibkr/market_data.py::MarketDataManager.cancel_contract_details` docstring version-neutral (it states the
  pinned-API absence and records the verification on both `9.81.1.post1` and the current pin
  `ibapi-latest==10.51.1`) and retargeted both assertions off the literal `"9.81.1.post1"`
  (`tests/test_ibkr_contract_details_d22.py`, `tests/test_d23_nonregression.py`). The requirements-side figures
  were corrected in the same pass. Behaviour unchanged — `AC-D23.1.*` stands. This also closes the DG61 residue
  (the survivor test that pinned the literal), per DG61's own hand-off.

## DG55 — the Constraints "Observed from repository" block contradicted the code on the database path
- **Where it shows up:** `requirements.md` Constraints (pre-2026-10-14 `:277–278`: "SQLite (dev:
  `./charting_app.sqlite3`; bundled: `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`)").
- **Why it matters:** the code has one path: `config/paths.py::get_db_path()` (`:68–81`) **always** returns the
  user-space file (`~/Library/Application Support/NDThinkChart/charting_app.sqlite3`, filename overridable with
  `DB_PATH`); `data/db.py:8` uses it. `config/settings.py:26` `DB_PATH` is **unused**, and the repo-root
  `charting_app.sqlite3` is stale. The bullet contradicted both the code and the Current Tech Stack, which
  states the same thing correctly.
- **Suggested resolution:** state the user-space path only (done 2026-10-14).
- **Status:** resolved 2026-10-14 (documentation only) — no cross-reference available: the changelog begins at
  Phase 1 / D26 (2026-10-12) and does not cover the D1–D23 era (`docs/phase-changelog.md:24–26`), so it records
  nothing about this bullet.

## DG56 — embedded line references drifted by +5 after commit `99fb8fa`
- **Where it shows up:** `requirements.md` `AC-D24.5` (cited `ui/main_window.py:840–846`; actual **`:845–850`**),
  D24's conn-badge reference (`:290`; actual **`:295`** — the badge is built at `ui/main_window.py:295`,
  `conn_badge_text` at `:141`), DG53 (`:3176` → actual **`:3181`** `id_manager.reserve(3)`; `:3107` → actual
  **`:3112`** `validate_order(`; `:3223` → actual **`:3228`** `reqGlobalCancel()`), D23.1
  (`ibkr/market_data.py:78–84` → actual **`:108`**), and D19's `ui/main_window.py:100–211` / `:217–223`.
- **Why it matters:** `99fb8fa` ("apply the theme font to the toolbar") inserted **5 lines** into
  `ui/main_window.py` around line 190, shifting every later reference by +5. Validator / Code Reviewer /
  Task Manager trace acceptance criteria by these citations; an off-by-five range silently points at unrelated
  code (e.g. `:290` is now `draw_delete_btn`, not the connection badge).
- **Suggested resolution:** cite a symbol/function name alongside — or instead of — a line range, so
  insertions cannot invalidate the citation. The two references that sit *inside* acceptance criteria and were
  verified in this pass (`AC-D24.5`, the D24 signal block) are corrected; the rest are dated/annotated rather
  than rewritten.
- **Changelog check (2026-10-14):** the changelog does **not** discuss line-number churn; its own convention is
  **symbol-first with the line as a secondary pointer** (`ibkr/client.py::DisconnectClass`,
  `services/alarm_monitor.py::AlarmMonitor.pause_all()`, `tests/test_order_builders.py:83-104`), which supports
  the recommendation below.
- **Adopted 2026-10-14 — `path::symbol` is the primary citation.** The convention is stated once in
  `requirements.md`'s Status/audit block (and repeated in this file's header): cite a **symbol**
  (`path::symbol`) as the primary pointer and treat a bare line number/range as **indicative only**.
  Applied as a bounded sweep, not an exhaustive rewrite:
  - **Converted (symbol-first, line demoted to indicative):** every citation that is load-bearing for a
    live/normative criterion — 17 sites in `requirements.md` (D16 `bar_cache`/`load_chart`, D22 `clear`/
    `header_bar`, D23.1 cancel path, D24 signal block / conn-badge / pop-out cap / always-on-top, D26
    bracket tests, D28.6 guard test, A66/A67, R55) and ~27 reference-level sites in `design_gaps.md` (DG15, DG19, DG21,
    DG23, DG37, DG38, DG39, DG41, DG43, DG44, DG51, DG53, DG54, DG59). Where a cited line had already
    drifted it is corrected and marked indicative (e.g. `data/bar_cache.py` `:33`→`:55`,
    `config/settings.py` `:12`→`:30`, `conn_badge` `:290`→`:295`, DG53's `:3176`/`:3107`/`:3223` →
    `:3181`/`:3112`/`:3228`).
  - **Bounded as historical (kept verbatim, tagged `[historical]`):** references that describe code **as it
    was at their own commit** — the dated "Observed in repository (validated 2026-10-03/05/06/07)"
    diagnoses for D17–D22, the D19/D20 implementation snapshots, the D23-era `ibapi` figures, the DG17
    doc-drift figures and A37's 2026-10-05 validation. 12 such sites in `requirements.md` and 4 in
    `design_gaps.md`. Their line numbers are deliberately **not** re-pointed at current lines.
  - **Out of scope (deliberately not swept):** requirements.md *section/section-line* references used as
    document anchors (e.g. DG47/DG48/DG50/DG54's `requirements.md:2583`-style figures) — these point at a
    prose document, not code, and are accurate for the revision they name.
- **Status:** resolved 2026-10-14 — convention adopted and applied (see `requirements.md` Status/audit
  block for the normative statement). Residual bare line numbers are all either `[historical]`-tagged or
  explicitly marked indicative.

## DG57 — D25 acceptance criteria and their backing tests use different AC→behaviour mappings
- **Where it shows up:** `requirements.md` `AC-D25.1`–`AC-D25.5` (`:2763–2774`) vs
  `tests/test_d25_alarm_monitor.py` (`:1` header, and the docstrings at `:49`, `:70`, `:95`, `:134`, `:168`).
- **Why it matters:** the test docstrings assign the AC numbers in **test order**, which maps differently to the
  criteria: the test labelled `AC-D25.1` asserts the *store query* (a D25 requirements bullet, not AC-D25.1);
  the one labelled `AC-D25.3` asserts *headless firing* (that is AC-D25.1); the one labelled `AC-D25.4` asserts
  the *no-phantom* rule (that is AC-D25.3); the one labelled `AC-D25.5` asserts *monitor stand-down*. As a
  result three criteria have **no** matching test: `AC-D25.2` ("assert on the request registry" — in
  `test_d25_2` the zero-historical-request check is a **comment**, `:86–88`, not an assertion), `AC-D25.4`
  (re-arm + alarm added while disconnected) and `AC-D25.5` (regression).
- **Suggested resolution:** either relabel the tests to the criteria they actually verify and add tests for
  `AC-D25.2`/`.4`/`.5`, or renumber the criteria to match the tests. Renumbering changes AC traceability, so
  this is an owner/Build call; annotated in `requirements.md` in the meantime (same convention as
  `AC-D39.5`/`AC-D40.5`).
- **Changelog check (2026-10-14):** the changelog confirms the **behaviour** shipped — Phase 3 item **3d**
  (`docs/phase-changelog.md:120`) records D25's "`prev_price` seeded from 1m cache, else first-tick seed with NO
  evaluation (no phantom). Zero history requests", and D40 item **40.3** (`:245`) re-affirms the same guard on
  resume — but it names **no D25 test** and gives no AC→test mapping, so it neither explains nor resolves this gap.
- **Status:** **resolved 2026-10-14** — commit **`ada080d`** took the "relabel the tests" option (the criteria
  are unchanged, so AC traceability is preserved). The five existing tests were relabelled to the criteria they
  actually verify, and the three uncovered criteria gained coverage: `AC-D25.2`
  (`test_d25_2_no_history_and_cache_seed` now asserts the request registry instead of only commenting on it),
  `AC-D25.4` (`test_d25_4_rearm_reenables_monitoring`, `test_d25_4_alarm_added_while_disconnected` — the latter
  asserts the intermediate staged state) and `AC-D25.1`
  (`test_d25_1_delete_alarm_tears_down_headless_session`). `AC-D25.5` remains the batch-regression convention
  (cf. `AC-D39.5`/`AC-D40.5`) and is verified by the full suite. All new tests are break-verified.

## DG58 — D24 acceptance criteria: four have no backing test, and one is mislabelled
- **Where it shows up:** `requirements.md` `AC-D24.*` (`:2681–2711`); `tests/test_d24_popouts.py`
  (`:30`, `:65`, `:89`), `tests/test_d24_alarm_full_chain.py`, `tests/test_d24_9_popout_persistence.py`,
  `tests/test_d24_smoke_gate.py`.
- **Why it matters:** `AC-D24.2` (drawing sync), `AC-D24.4` (study sync), `AC-D24.7` (reconnect with pop-outs)
  and `AC-D24.10` (always-on-top defaults OFF) have **no** backing test — a tree-wide grep finds no test
  referencing `drawings_changed`/`studies_changed`, no pop-out reconnect test, and no
  `WindowStaysOnTop`/`always_on_top` assertion anywhere. Separately,
  `tests/test_d24_popouts.py::test_popout_readonly` is labelled **AC-D24.3** (which is the *alarm-sync*
  criterion) while it actually exercises **AC-D24.6** (read-only), and its mode-guard check is effectively
  vacuous: it calls `set_drawing_tool(...)` / `set_alarm_mode(True)` and asserts nothing about the router modes
  ("verified by `_editable` guard" is a comment, `:99–102`) — so `AC-D24.6`'s "router modes never arm" clause
  is not verified either.
- **Suggested resolution:** add tests for `AC-D24.2`/`.4`/`.7`/`.10`; correct the mislabelled docstring; assert
  the router mode is unchanged after the read-only no-op attempts.
- **Changelog check + correction (2026-10-14):** two of my claims are narrower than first stated. (a) The
  changelog's Phase 3 fix-pass entry **MODERATE** (`docs/phase-changelog.md:126`, commit `8ef0342`) records the
  read-only pop-out guard work, and `tests/test_phase3_fixpass.py` (fix2a–2e, `:129`–`:246`) does exercise the
  pop-out overlay guards (alarm drag/no-menu/delete, drawing-drag no-payload-mutation) — so **AC-D24.6's
  behaviour is covered**, though no test cites the AC id and `test_popout_readonly`'s own assertions remain weak.
  (b) The changelog's Phase 4 item **4d** (`:166`) notes T-1 alarm E2E coverage lives in
  `test_d24_alarm_full_chain.py`, which covers **AC-D24.3**. What remains untested is unchanged:
  **AC-D24.2** (drawing sync to pop-outs), **AC-D24.4** (study sync), **AC-D24.7** (reconnect with pop-outs),
  **AC-D24.10** (always-on-top default OFF) — no test references any of them.
- **Status:** **resolved 2026-10-14** — commit **`ada080d`** implements the suggested resolution in full.
  `AC-D24.2` (`test_popout_drawing_sync`), `AC-D24.4` (`test_popout_study_sync`), `AC-D24.7`
  (`test_popout_reconnect_replays_and_resumes`) and `AC-D24.10` (`test_popout_always_on_top_default_off`) now
  have backing tests. `test_popout_readonly`'s label is corrected to `AC-D24.6`, and it now asserts the router
  stays `RouterMode.IDLE` and that neither a drawing tool nor alarm mode arms. A latent defect was fixed in
  passing: the test passed `"Trendline"` where `DRAWING_TOOLS` is lowercase, so the call had been asserting
  nothing. Each new test is break-verified (disabling the guarded behaviour makes it fail).

## DG59 — toolbar geometry figures: the `~1716px` intrinsic minimum is stale, and D20's `~50–52px` band is macOS-only
- **Where it shows up:** `requirements.md` D19 (`:2040`, `:2043`, `:2048–2049`, `:2065`, `AC-D19.5`) and A37
  ("`~1716px minimumSizeHint`"); D20 `AC-D20.2`/A39 (total strip "~50–52px"). Code:
  `ui/main_window.py::TOOLBAR_CONTENT_HEIGHT` (`:120`) and `:374–377` (wrapper height =
  `36 + horizontalScrollBar().sizeHint().height()`), measured through
  `tests/test_toolbar_d20.py:8` and `:250–251`.
- **Why it matters:** the toolbar's intrinsic minimum was re-measured **~1965px** offscreen on 2026-10-14
  (27 layout items, incl. pop-out / footprint / depth / search controls added after D19), so "~1716px" no
  longer describes the code — it is a 2026-10-05 observation. Likewise the D20 strip is *derived*, and the
  offscreen value is **54px**, outside the stated "~50–52px" band (macOS ≈52px); the D20 test deliberately
  refuses a literal `[50, 52]` bound for exactly this reason.
- **Suggested resolution:** annotate the figures as report-time/macOS figures (done 2026-10-14) and, if a hard
  requirement is wanted, state it platform-neutrally as "content row 36px + the horizontal scrollbar's own
  height" rather than a pixel band. No behavioural change to `AC-D19.4`/`AC-D20.*`.
- **Changelog check (2026-10-14):** the changelog has **no D19/D20 entry** (it starts at Phase 1 / D26,
  `docs/phase-changelog.md:24–26`), so there is no cross-reference to cite for these figures; the annotations
  stand on the code measurement alone (`ui/main_window.py::TOOLBAR_CONTENT_HEIGHT`, `:374–377`).
- **Status:** resolved 2026-10-14 (documentation annotated; the underlying behaviour is unchanged)

## DG60 — two different gaps share the identifier `DG14`
- **Where it shows up:** `design_gaps.md:146` ("DG14 — D15 horizontal line popup — single coordinate vs zone")
  and `design_gaps.md:156` ("DG14 — D13 watchlist width 50% + persistence — mechanism and clamping"; when DG60
  was written it sat at `:148` — markers move, cite the symbol).
- **Why it matters:** any downstream citation of "DG14" is ambiguous (the D15 gap and the D13 gap are
  unrelated). Pre-existing doc defect, not opened by the recent work.
- **Suggested resolution:** renumber the D13 entry to the next free id (nothing else in the tree cites
  `DG14`); left un-renumbered here deliberately, to avoid a gratuitous identifier change inside an audit pass —
  flagged for the owner.
- **Status:** **resolved 2026-10-14** — the D13 entry was renumbered to the next free id, **`DG63`**, and now
  carries a back-reference to this gap; the D15 entry keeps `DG14`. Verified nothing else in the tree cited the
  D13-side `DG14`, so no downstream citation needed updating.

## DG61 — AC-D28.6's doc-assert deletion: the *file* was kept deliberately; the real residue is a version literal pinning the stale `ibapi`
- **Where it shows up:** `requirements.md` D28.6 / `AC-D28.6` ("the doc-assert/phantom tests are gone") vs
  `tests/test_d23_nonregression.py` (still present) and `tests/test_stop_loss_target.py`.
- **Changelog check — this largely resolves it (2026-10-14):** Phase 4 item **4d**, commit **`3363422`**
  (`docs/phase-changelog.md:166`: "Deleted 3 doc-asserting tests + phantom `validate_sltp` (kept behavioural
  guards)"), whose own commit message is explicit: *"Delete the three doc-asserting tests in
  test_d23_nonregression.py (they asserted on docs/tasks/task-graph.json, docs/architecture.md,
  docs/requirements text); the behavioural T03 guard/invariant checks stay."* Verified against the tree:
  `git show 3363422 -- tests/` removes **three** `T01` doc-text tests (`-143` lines) and the `TestValidateSLTP`
  block (`-122` lines) while leaving `test_D23_03_T03_guard_source_shape`. So **AC-D28.6 is satisfied in
  intent**: the doc-text assertions and the phantom test are gone, and the surviving file is the *behavioural*
  guard the changelog says was kept on purpose. *(My earlier reading — "the AC is falsified because the file
  exists" — was wrong, and is corrected here.)*
- **What genuinely remains open:** the surviving guard asserts on the live **source text** of
  `MarketDataManager.cancel_contract_details` (`tests/test_d23_nonregression.py:52`, `:61`–`:64`), including
  `assert "9.81.1.post1" in src` at **`:61`** — the only remaining hard-coded reference to the pre-D36 pin. It is
  a legitimate code-shape check, but it **couples the suite to the stale version**: applying DG54's docstring fix
  fails this test unless both change together.
- **Secondary (wording) nit:** `AC-D28.6` names the *file* (`test_d23_nonregression.py` markdown-string asserts)
  where the change deleted three *tests* inside it — which is what invited the misreading above. Low priority.
- **Suggested resolution:** **Re-routed to Build:** update `ibkr/market_data.py:110–137` + `:61` (and the
  `test_ibkr_contract_details_d22.py:234–236` prose) in one change. Owner/Build may optionally reword
  `AC-D28.6` to name the deleted tests rather than the file.
- **Status:** resolved-with-reference 2026-10-14 — explained by `docs/phase-changelog.md:166` (Phase 4, 4d,
  `3363422`) and verified against the tree; the residual version literal is carried by DG54 and re-routed to
  Build.

## DG62 — the changelog's own branch/merge/push status (and one SHA) disagrees with the current tree
- **Where it shows up:** `docs/phase-changelog.md:110` (Phase 3: "NOT pushed and NOT merged"), `:151` (Phase 4:
  "NOT pushed and NOT merged"), `:364` (D36: "NOT pushed and NOT merged to `main`"), `:322`/`:275`/`:192`/`:236`
  (D37/D38/D39/D40: "merged to `main` @ <sha>, NOT pushed", each with "Docs gate (this entry) on
  `docs/d24-d28-requirements-architecture`"), and `:236` (D40 "review fixes `d6f38e8` — hashes per git history").
- **Why it matters:** it is the **record of intent**, not the state. Verified against the tree 2026-10-14:
  `HEAD == main == origin/main == 262ec81`, **no other branches exist** (local or remote), and every phase's code
  is merged into `main` (`efffc51` D36, `9958891` D37, `8599ce4` D38, `83f792a` D39, `b366b19` D40) and pushed.
  So every "NOT pushed"/"NOT merged" status is stale, the branch names it cites no longer exist, and the
  docs-gate branch was folded in by `262ec81`. Separately, the D40 review-fix SHA **`d6f38e8` does not exist in
  this history** (`git cat-file -t d6f38e8` → missing); the D40 B1 fix and its regression test
  (`test_d40_2_resume_session_recreated_mid_pause_no_phantom`) are present, committed under `4ac2453`.
- **Also stale inside it:** the D37 entry (`:340`) records the depth-heatmap default as "**PENDING owner
  confirmation** (reviewer recommends OFF)", and the D38/D39/D40 follow-up lists (`:313`, `:227`, `:265`) still
  carry "depth heatmap default ON pending owner confirmation" — **resolved 2026-10-14 by Q44** (owner confirmed
  ON; `requirements.md` A67 / DG51). The changelog predates that decision.
- **Suggested resolution:** the changelog is **not the Analyst's file** — reported, not edited. The owner (or
  whoever owns `docs/phase-changelog.md`) should refresh the phase statuses/SHAs and drop the resolved
  "pending" item; a short "status as of 2026-10-14: all phases merged and pushed" header note would
  stop the next reader re-deriving it. **Actioned upstream in `96b72c4`** — see Status below.
- **Status:** resolved 2026-10-14 — **verified against the file** (not just the commit message) and against
  the tree at commit **`96b72c4`** ("docs(changelog): correct six stale claims in phase-changelog.md").
  All six items DG62 named are corrected in `docs/phase-changelog.md`:
  1. **Phase statuses** — `grep` finds no remaining "NOT pushed"/"NOT merged"; all seven sites DG62 named
     now read merged/pushed (`:110` Phase 3, `:151` Phase 4, `:192` D39, `:236` D40, `:275` D38, `:322`
     D37, `:364` D36). `HEAD == main == origin/main` and only `main` exists, so this matches the tree.
  2. **The non-existent review-fix SHA `d6f38e8`** is gone from `:236` and from the review row at `:247`
     (both now name `b366b19`, which exists); `git cat-file -t d6f38e8` fails as DG62 reported.
  3. **The D37 "depth heatmap default ON is PENDING owner confirmation" decision** (`:340`) and the three
     carried follow-up lists (`:227` D39, `:265` D40, `:313` D38) no longer carry the pending item; `:340`
     now reads "CONFIRMED by the owner 2026-10-14 (Q44 / assumption A67)".
  4. **The D36 36.1 row** (`:371`) now says **2 new signals / 2 overrides**, noting the removed histogram
     pair — verified against the tree: `ibkr/bridge.py` declares exactly `historical_ticks_bid_ask` /
     `historical_ticks_last`, and `ibkr/client.py` has exactly **2** `historicalTicks*` overrides.
  5. **The D38 38a.1 row** (`:282`) now lists all **four** bridge signals — `news_providers` /
     `historical_news` / `historical_news_end` / `news_article` — matching `ibkr/bridge.py`.
  6. **`:151` "the last phase of the plan"** is corrected (it now notes D36–D40 followed).
  Line count is unchanged (401), so the ~87 citations into the changelog remain valid. **Deliberately left
  alone** (correct as history, not drift): the branch names and the per-phase "Docs gate (this entry) on
  `docs/d24-d28-requirements-architecture`" provenance notes. The changelog is not the Analyst's file —
  reported, not edited. **No item remains stale.**


---

## DG64 — ESC-035: IBKR depth error 2152 (partial venue permissions) has no defined behaviour; a warning-band code tears the feed down — **MOOT (superseded by D41)**

- **Where it shows up:** D37 / Journey 32 / `AC-D37.4`; `ui/ticker_session.py::TickerSession.on_depth_error`
  (`:786-798`) + `::TickerSession._cancel_depth` (`:748-759`); `ui/main_window.py::MainWindow._on_error`
  (`reqId == session.depth_req_id` → `on_depth_error`, `:1664-1671`); `ibkr/error_codes.py::classify_error`
  (2152 falls to the default `'warning'`, `:22`).
- **Why it matters:** error **2152** ("Market depth smart depth exchanges") is a **partial** venue-permission
  report — it lists venues the account cannot reach while the account still holds other venue depth — yet the
  handler maps **every** non-354 depth error to `depth_state = "unavailable"` and cancels the **shared**
  feed, blanking the **default-ON** heatmap. Only the hard no-entitlement **354** path is specified
  (`requirements.md:692`; `AC-D37.4`, `:3004-3006`); `classify_error` classes 2152 as an informational
  `'warning'`, contradicting the fatal teardown. This is a **requirements gap** (behaviour undefined) and an
  internal consistency gap (error band vs handling) — the fix is a product decision.
- **Suggested resolution (optional):** decide **Q46** — (a) keep streaming entitled venues, (b) a distinct
  "partial permissions" state, or (c) keep it fatal and record 2152 as specified behaviour; whether IBKR
  keeps streaming after 2152 (unverified by the reviewer) informs (a). Then BUILD adds a 2152 branch distinct
  from 354 (or the panel learns a new state).
- **Evidence `file:line` (indicative):** `ui/ticker_session.py:786-798`, `:748-759`;
  `ui/main_window.py:1664-1671`; `ibkr/error_codes.py:22`; `docs/requirements/requirements.md:692`,
  `:3004-3006`.
- **Status:** **MOOT (2026-10-15)** — superseded by **D41** (the D37 depth feed is removed; Q48 also removes the DOM ladder), so no depth feed remains to define 2152 behaviour for. **Q46** is resolved as moot (no option chosen). The ESC-035 REQUIREMENTS item is routed to closure via the Code Reviewer on D41.

## DG65 — ESC-038: no minimum intraday history depth under RTH; the D16 backfill cannot extend history backwards — **RESOLVED (Q47, 2026-10-15)**

- **Where it shows up:** D16 / Journey 17 / `AC-D16.1` and the D16 edge cases;
  `ibkr/market_data.py::TIMEFRAME_CONFIG` (`"1 min" → "1 D"`, `:7-14`);
  `services/backfill_service.py::find_missing_spans` (`first_day = min(present_days)`, `:208-215`).
- **Why it matters:** under **RTH** (`extended_hours=False` → `useRTH=1`) a single `D` duration is exactly
  **one RTH session**, and the day-presence backfill anchors at the **earliest cached day**, so it never
  extends history **backwards** — a fresh `1 min` chart is permanently one session. **No written requirement
  sets a minimum history depth**; `AC-D16.1` (`requirements.md:1739-1750`) requires only continuity *from the
  oldest displayed bar through now*, and the empty-cache edge case (`:1824`, `:491`) is satisfied because
  `1 min`'s configured window is `1 D`. The one-session result is therefore **unfiled**, not a violation.
- **Suggested resolution (optional):** decide **Q47** — is one session acceptable, or must each intraday
  timeframe guarantee a minimum depth (a session count or calendar span)? Encoding the answer as an AC lets
  BUILD widen/adjust the request window, or routes to PLAN if the window strategy is redesigned.
- **Evidence `file:line` (indicative):** `ibkr/market_data.py:7-14`; `services/backfill_service.py:204-215`,
  `:276-281`; `docs/requirements/requirements.md:1739-1750`, `:1813-1832`, `:1824`/`:491`.
- **Status:** **RESOLVED (2026-10-15, Q47 answered).** The minimum intraday history depth under **RTH** is now
  **30 trading sessions** before the current session for each intraday timeframe, recorded as **`AC-D16.8`** in
  `requirements.md`. Delivering the floor (chained, paced, backwards-extending fetches, since `1 min` is capped
  at `1 D` per request and the backfill never extends backwards) is a **Plan/BUILD** window-strategy concern — see
  `open_questions.md` **Q47**.
  (Distinct **BUILD** escalation **ESC-037** — the mode-blind day-presence pass at
  `services/backfill_service.py:276-281`, which silently treats a present-but-RTH-empty day as filled — remains
  routed to **BUILD**.)


## DG66 — D41: which open Code Reviewer escalations does the D36/D37/DOM-ladder removal make moot, and which stay?

- **Where it shows up:** `docs/code_review/escalations.json` — **ESC-035, ESC-039, ESC-040** (candidates);
  the D41 removal (`requirements.md` `### D41`).
- **Why it matters:** removing D36/D37 **and (Q48, 2026-10-15) the Active Trader DOM ladder** removes the code
  several escalations concern; each had to be checked against what it *actually* points at, not its name.
- **Disposition (verified against the escalation text and the code 2026-10-15; updated for Q48 = YES):**
  - **ESC-035 — MOOT on D41.** It concerns **depth error 2152** tearing down the **shared heatmap feed**
    (`ui/ticker_session.py::TickerSession.on_depth_error`, `_cancel_depth`; `ui/main_window.py::MainWindow._on_error`
    session branch) — i.e. D37. With D37 removed there is no heatmap to degrade; **Q46** and **DG64** are moot too.
  - **ESC-040 — MOOT on D41.** It concerns the **D36 footprint** tick-request error path
    (`ui/ticker_session.py::TickerSession.on_fp_error`; `services/footprint_service.py::mark_no_tick_data`).
    D41 removes the footprint wholesale.
  - **ESC-039 — MOOT on D41 (Q48 = YES).** It concerns the **Active Trader DOM ladder** pairing a SMART contract
    with `isSmartDepth=False` in `ibkr/market_depth.py::MarketDepthManager.subscribe`. **Q48 (2026-10-15) widens
    D41 to remove the DOM ladder too**, so there is no ladder request whose shape needs correcting.
  - **ESC-036 (aggregator priming), ESC-037 (mode-blind RTH day presence) — STAY** as recorded (the **D27/D16**
    backfill/aggregation paths, unrelated to D36/D37); **ESC-038 / Q47 is now RESOLVED via `AC-D16.8`** — see DG65.
- **Suggested resolution (optional):** on D41 landing, the Code Reviewer flips **ESC-035 / ESC-039 / ESC-040** to
  `addressed` (resolved-by-removal) after re-verifying; Q46/DG64 are marked moot here.
- **Status:** **resolved (2026-10-15)** — disposition recorded; all three escalations routed to closure on D41.

## DG67 — D41: D36/D37 code is entangled with KEPT features; the removal must be surgical

- **Where it shows up:** `requirements.md` `### D41` "Scope — KEEP"; `ui/ticker_session.py` (S0 substrate),
  `ibkr/contracts.py` (`footprint_cache_key`/`INDEX_PROXY`), `services/md_line_guard.py`,
  `ibkr/market_depth.py`, `services/volume_baseline.py`, `data/db.py`.
- **Why it matters:** "remove all associated code" cannot mean module-wide deletion — several D36/D37-named
  symbols are load-bearing for features the owner **kept**:
  - `ibkr/contracts.py::footprint_cache_key` → **D39** burst baseline (`ui/ticker_session.py::TickerSession`) — KEEP.
  - `ibkr/contracts.py::INDEX_PROXY` → **D39** (`services/alarm_monitor.py`, `ui/alarm_dialog.py`) — KEEP.
  - `services/md_line_guard.py::assess` + `MainWindow._guard_md_lines` + the RT/S0/watchlist terms of
    `_md_line_count` → **D38** S0 lines — KEEP (remove only the `depth` term + `_guard_depth_budget`/`DEPTH_FEED_CAP`).
  - S0 substrate (`s0_register_many`/`S0_TICKS`/`tick_generic`/`tick_string`/`tick_news`) → **D38** — KEEP
    (remove only the `"225"` auction need).
  - `services/volume_baseline.py` + `volume_baseline` table → **D39** — KEEP.
  - `data/db.py` — remove only the `footprint_cache` DDL; keep `volume_baseline` (D39) and `yfinance_events_cache` (D38).
  - `config/settings.py` has **no** `DEPTH_HEATMAP`/`S0_TICKS` constants — those tags live in
    `ibkr/subscription_manager.py::DEPTH_HEATMAP` (D37, remove) and `::S0_TICKS` (D38, keep); the `DEPTH` tag is
    removed too (DOM ladder, Q48).
  - `ibkr/market_depth.py` (**both** halves) + `ibkr/order_book.py` + **all of `ui/active_trader_panel.py`**
    (ladder/book **and** the `OrderEntryWidget` order ticket, plus the panel shell and header) → **REMOVED**
    (Q48 = YES; **widened by Q50** to the whole panel) — see **DG69**. The **order execution/safety machinery**
    (`ibkr/orders.py`, `ibkr/validation.py`, the `validate_order()` gate, `bracket_order`, the kill switch) is
    **kept** for the retained Portfolio close/flatten/SL-TP paths.
- **Also:** a footprint-named symbol kept for D39 (`footprint_cache_key`) is a naming smell after D36 removal —
  a neutral rename is a non-requested refactor recorded as feature suggestion **FS17** (not part of D41).
- **Suggested resolution (optional):** implement D41 per the "Scope — KEEP" list; treat "no dangling import" +
  the D38/D39/D26-order/D18/D21.13 test suites as the guard (AC-D41.3/AC-D41.4/AC-D41.5).
- **Status:** **resolved (2026-10-15; updated for Q50)** — the KEEP list is finalised: the DOM ladder moved from
  KEEP to REMOVE (Q48), and **Q50 widened the removal to the whole `ui/active_trader_panel.py`** (order-entry UI
  included — the panel shell/header/ticket all go); the **order machinery** it drove is **kept** for the retained
  close/flatten/SL-TP paths (DG69).


## DG68 — D41: does the D36/D37 removal resolve the currently-running wide-candle / volume-overlap investigation?
- **Where it shows up:** an in-flight Code Reviewer investigation (2026-10-15) into whether the **footprint
  overlay** causes **wide, overlapping candles / volume**; `ui/chart_panel.py` (`FootprintItem` layers
  `footprint_static`/`footprint_live` added to `price_plot`).
- **Why it matters:** if the footprint render layer is the cause, D41's removal resolves the symptom by
  construction; if the cause is elsewhere (candlestick/volume width code, `ui/candlestick_item.py`, `ChartPanel`
  width math), D41 leaves the bug live. The investigation had not concluded when D41 was recorded.
- **Suggested resolution (optional):** keep the investigation **open** until it concludes; if it names the
  footprint overlay, record the symptom as **resolved-by-D41** on `AC-D41.1`/`AC-D41.5`; if it names shared
  candle/volume code, D41 does **not** resolve it and it must be filed as its own defect (separate from D41).
- **Status:** **resolved (2026-10-15) — NOT the footprint overlay; the cause is the `AC-D6.4`/`AC-D7.1`
  contradiction, and the bug SURVIVES D41.** The investigation concluded (ESC-041/ESC-042, 2026-10-15): the
  candle **and** volume overlap at high density comes from the **unconditional 4-device-pixel body floor**
  (`ui/candlestick_item.py::CandlestickItem._draw_candles`; volume via
  `ui/chart_panel.py::ChartPanel._clamp_half_width`), **not** the removed `FootprintItem` layer — measured
  3.83 px pitch / 4.00 px body on a 192-bar SPY 5-min Ext-Hours view. So D41 does **not** resolve the symptom; it
  is filed as its own defect and resolved at the requirements level by **D42.1 / ESC-042** (the body is capped at
  the pitch; the 4-px floor is density-aware), which is the root-cause fix that unblocks BUILD **ESC-041**.
  (This corroborates `AC-D41.1`'s "no D36/D37 control renders" but does **not** credit D41 with the overlap fix.)

---

## DG69 — D41: `ui/active_trader_panel.py` is not purely the DOM ladder — removing it wholesale would break kept D26/D18/D21.13
- **Where it shows up:** D41 "Scope — REMOVE" (DOM ladder); `ui/active_trader_panel.py`; `ui/main_window.py`
  (`active_trader` usage, `_on_order_place_requested`, `ref_price=self.active_trader.last_price`); **D26** order
  path; **D18** right-dock region; **D21.13** collapse toggle; `tests/test_dock_d18_region.py`,
  `tests/test_right_dock_d21.py`, `tests/test_order_entry_mkt.py`, `tests/test_order_validation.py`.
- **Why it matters:** Q48 (2026-10-15) widens D41 to remove the **Active Trader DOM ladder**, and the prior
  inventory listed `ui/active_trader_panel.py` under KEEP. But that file is **not purely the ladder** — it also
  contains:
  - `OrderEntryWidget` (Buy/Sell MKT, live-orders gate, confirmation, status) → the **D26** order path
    (`MainWindow._on_order_place_requested`, `active_trader.order_entry.status_label`, `order_place_requested`).
  - the `ActiveTraderPanel` shell → the **D18** right-dock section (`test_dock_d18_region.py` asserts
    `isinstance(win.active_trader, ActiveTraderPanel)`).
  - `header_bar`/`header_button` → the **D21.13** right-dock collapse toggle (`test_right_dock_d21.py`).
  - `set_symbol`/`set_last_price`/`last_price` — `MainWindow` passes `ref_price=self.active_trader.last_price` to
    `validate_order` for the MKT notional cap; `last_price` was populated from the **DOM depth feed**
    (`_on_mkt_depth` → `active_trader.set_last_price(price)`).
  A blind `ui/active_trader_panel.py` file delete would therefore break **D26** (orders), **D18** (right dock)
  and **D21.13** (collapse) — features the owner did **not** remove (D41 keeps D1–D35).
- **Suggested resolution (optional):** remove the **ladder/book depth rendering only** (`LadderTable`, `BookTable`,
  `on_depth_callback`, the ladder/book tabs, `update_from_snapshot`); **keep** `OrderEntryWidget`, the panel shell,
  `header_bar`/`header_button`, and the order-path methods. Give the order path a new `last_price` source (the live
  RT-bar price) so `ref_price` keeps resolving after the DOM feed is gone. If the owner actually wants the **whole**
  Active Trader panel removed (order entry included), that is a **scope extension** and a new owner question — the
  conservative, reversible default is ladder-scoped. **→ Resolved 2026-10-15 (Q50):** the owner confirmed the
  **whole panel is removed** (order entry included) and the **right dock becomes Portfolio-only**; the
  ladder-scoped default is **superseded** (see the Status below).
- **Status:** **resolved (2026-10-15) — owner confirmed the whole panel is removed (order entry included).** Q50
  (2026-10-15) answered **YES / YES**: the **entire Active Trader panel** — including the `OrderEntryWidget`
  order ticket — is removed (`ui/active_trader_panel.py` is deleted), and the **right dock becomes Portfolio-only**.
  The ladder-scoped conservative default is **superseded**. The retained order path's `ref_price` **MUST** be
  re-sourced from a **retained** price (session last price / watchlist price map) — a Plan-level detail (DG71) —
  and the **order execution/safety machinery** (`ibkr/orders.py`, `ibkr/validation.py`, `validate_order()`,
  `bracket_order`, order-ID reservation, the kill switch) is **kept** for Portfolio's **Close / Close Group /
  Flatten All** and the **SL/TP dialogs**. The affected `D18`/`D21.13` clauses are **superseded by D41** (the
  right dock is single-section; cap + header re-derived — DG71).

## DG70 — D41: persisted `footprint_cache` — drop the whole table, or delete rows only?
- **Where it shows up:** D41 (Q49 = "delete"); `data/db.py` (`footprint_cache` DDL); `data/footprint_cache.py`;
  the user DB `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`.
- **Why it matters:** the owner chose **delete** (not "leave in place"). Two equally easy readings exist: **(a)**
  delete the rows but keep the (now empty) table, or **(b)** `DROP TABLE` the whole table. Both remove the data;
  (b) is marginally cleaner (no orphan schema) but slightly more destructive/irreversible.
- **Suggested resolution (optional):** the **recorded default is (b) — full drop** (drop the `footprint_cache`
  table + rows), since the feature that owns the data is removed and "delete" is the owner's word. If a future
  reader prefers the milder (a), it is a one-line change; DG70 records the distinction explicitly rather than
  silently baking it in.
- **Status:** **resolved (2026-10-15)** — recorded as **full drop** (A69/D41); the alternative is noted, not
  adopted. **Confirmed by Q49/Q50 (2026-10-15):** Q49 chose "delete" and Q50 does not change the persisted-data
  disposition, so the full drop of the `footprint_cache` table + rows stands.


## DG71 — D41: the Portfolio-only right dock's re-derived cap/header and the retained order-path `ref_price` source

- **Where it shows up:** D41 "Scope — KEEP" (retained order machinery + `ref_price`); the superseded `D18`
  (right-dock model) and `D21.13` (dock title bar / collapse) clauses; `ui/main_window.py`
  (`right_dock_max_width`, `_apply_dock_widths`, the right dock's title-bar widget), `ui/dock_layout.py`.
- **Why it matters:** two consequences of removing the whole Active Trader panel (Q50) are **Plan-level
  details**, not blocking requirements: **(1)** the **retained order path's `ref_price`** was the panel's
  `last_price`, fed by the DOM depth feed, so with both removed it **MUST** be re-sourced from a **retained**
  price — the session's last price (live RT-bar / aggregator last) or the `symbol → last_price` watchlist price
  map (as `D27.5` mandates for position market prices) — and must keep resolving; **(2)** the **right dock is now
  a single Portfolio section**, so its **40%-of-chart-area cap** (was for the two-section region) and its **dock
  header / collapse affordance** (the title bar used the removed Active Trader header) must be **re-derived** for
  one section.
- **Suggested resolution (optional):** Plan re-derives the single-section dock's cap (an upper bound — keeping
  `floor(0.40 × chart_area)` is a safe default until narrowed) and picks the Portfolio dock's header/collapse
  mechanism (the `Account Summary` summary-label toggle survives; a new title-bar widget replaces the removed
  Active Trader header); Plan sources `ref_price` from the session last price / watchlist price map. `AC-D41.7`
  is the acceptance criterion; the outcome (single-section Portfolio dock, resolving `ref_price`) is fixed while
  the mechanism is Plan/Build's call.
- **Status:** **open (non-blocking)** — a Plan-level detail recorded so neither re-derivation is silently lost;
  the owner confirmed the *shape* (Q50) and left the mechanism to Plan.

## DG72 — D42/ESC-038+ESC-037: the RTH/ETH day-presence pass and the bar cache are mode-blind, so a present-but-RTH-empty trading day is silently "filled" — **RESOLVED (D42, 2026-10-15)**

- **Where it shows up:** D16 / Journey 17 / `AC-D16.8`/`AC-D16.9`; `services/backfill_service.py::find_missing_spans` (the day-presence pass decides per-day presence without the current `ext_hours` mode); `data/bar_cache.py` / `data/db.py` (a `useRTH`-blind cache key).
- **Why it matters:** under **RTH** (`ext_hours=False`) a trading day whose cached bars are **all outside RTH** (e.g. `04:00–09:25` + `16:05–19:55`) yields **no** span, so the day-presence pass treats it as **filled** and the RTH hole is never requested (reproduced: `find_missing_spans(pre_and_post_bars(today), now, '5 mins', ext_hours=False) -> []`). Compounded by the mode-blind cache key, a mode switch can also read the other mode's bars as coverage. This violates the D16 edge case "the backfill must respect the current setting and not leave a hole because of a mode switch", and it silently under-counts the `AC-D16.8` RTH-session floor. It is the **same code path** as the ESC-038 symptom from the other side (BUILD escalation **ESC-037**).
- **Suggested resolution (adopted):** make day presence **mode-aware** (decide presence against the **same session window the load uses**, `ext_hours`) and make the bar cache/key **mode-aware**, so a present-but-RTH-empty day is reported as a **missing RTH span** rather than assumed filled — recorded as **`AC-D16.9`** in `requirements.md`. The fix is **BUILD** (ESC-037); the requirement is the normative target.
- **Status:** **RESOLVED (2026-10-15, D42)** — `AC-D16.9` states the mode-aware day-presence + mode-aware-cache requirement; BUILD escalation **ESC-037** implements it (RED pre-fix: the `ext_hours=False` case returns `[]`).
  **Scope widened (Q52, owner-confirmed 2026-10-15):** the rule now covers **both** modes — `AC-D16.9` states it for `ext_hours=False` (RTH) **and** `ext_hours=True` (ETH, extended window `04:00–20:00 ET`), and `AC-D16.8`'s 30-session floor likewise applies to both; the two modes share one floor and must not cross-contaminate.

## DG73 — D43/ESC-036: D27.9's "trailing 5-second history" is unsatisfiable for `4 hours`/`1 day`, and P2-T30's in-flight fix only clamps the 5-sec span — **RESOLVED (D43, 2026-10-16)**

- **Where it shows up:** D27.9 / `AC-D27.9`; `ui/ticker_session.py::TickerSession.prime_aggregator` (hardcodes `bar_size='5 secs'` and builds `duration=f'{min(span_s, _PRIME_MAX_SPAN_S)} S'` with `_PRIME_MAX_SPAN_S = 7200`); `data/bar_aggregator.py::TIMEFRAME_SECONDS` (`4 hours` = 14400 s, `1 day` = 86400 s); `ibkr/market_data.py::TIMEFRAME_CONFIG`.
- **Why it matters:** for `4 hours`/`1 day` the elapsed forming-period span exceeds IBKR's `3600 S` ceiling for `5 secs` bars, so the built request (`bar_size='5 secs'`, `duration='7200 S'`) is rejected with TWS **error 321** and the aggregator is left **unprimed** — the forming 4h/daily candle is fabricated from live ticks (the defect D27.9 exists to prevent) and the warning is emitted on every load. D27.9's wording ("primed with trailing 5-second history") is therefore **unsatisfiable** for those timeframes, and **P2-T30's clamp** (5-sec span into `[60 S, 3600 S]`, keeping `bar_size='5 secs'`) **does not fix it** — it only avoids the error while accepting a partial seed whose open/high/low/volume are wrong.
- **Suggested resolution (adopted):** select the priming bar size from the elapsed span — `5 secs` when `span_s <= 3600` (the `1 min`/`5 mins`/`15 mins`/`1 hour` timeframes) and `1 min` when it exceeds `3600 S` (the `4 hours`/`1 day` timeframes, valid up to `1 D`), with `duration` clamped into the selected bar size's IBKR range (`[60 S, 3600 S]` / `[60 S, 1 D]`); recorded as **D27.9 (revised)** / **`AC-D27.9` (revised)** in `requirements.md` (D43). The "seed from the historical partial bar" alternative is not adopted (it depends on unverified IBKR partial-bar behaviour).
- **Status:** **RESOLVED (2026-10-16, D43)** — the requirement is the normative target; **BUILD** implements it. The **coarse-timeframe bar-size switch is a FOLLOW-UP** not covered by P2-T30, and **P2-T30's `AC1`/`P2-T30-T11`** (which assert a `5 secs`/`3600 S` request for 4h/1d) become **stale once it lands** and must be revised by the Task Manager.
