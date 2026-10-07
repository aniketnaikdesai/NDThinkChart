# Architecture Proposal — NDThinkChart Batch 15 (D21: 13 UI defects/issues)

> **Scope.** An *incremental* change-set on top of the **already-built, green D1–D20** system
> (D1–D20 built at commit `04397d9`, 585 tests). D1–D20 are **frozen** and are **not** re-planned.
> This is an **existing-repo** run: `requirements.md` contains the marker sentence
> `This is an existing repository.` and a Current Tech Stack; **PyQt6 + pyqtgraph is a hard
> constraint**. No stack change, no schema change, no new dependency, no new external integration,
> and no live-order-path change. Every item below is labelled `[existing]`, `[new]`, or
> `[new/changed]`.
>
> **Defects.** Batch 15 (**D21**, sub-defects **D21.1–D21.13**), reported by the user in one message
> 2026-10-06 and **clarified and finalised** (B9–B13 answered 2026-10-06). A shared visual
> convention **`VIS-D21`** (diagonal strike-through `VIS-D21.1`, active-button highlight `VIS-D21.2`)
> is defined once and reused. **D21.4 supersedes only the display part of `AC-D16.3`**; D16's
> no-silent-hole rules (`AC-D16.1`/`AC-D16.4`) are unchanged.
>
> **Companion:** `docs/plan_proposal.md` (coverage map, ordered phases, `touches_files` notes,
> assumptions, flagged issues). **As-built baseline:** `docs/architecture.md` (increment D20,
> validated 2026-10-06). **Requirements:** `docs/requirements/requirements.md`
> (`Status: READY_FOR_PLAN`; D21 / `AC-D21.*` / Journeys 22–26 / A41–A47 / R37–R44 / DG31–DG38;
> B9–B13 answered).
>
> **Graphify.** The knowledge graph at `graphify-out/` (2416 nodes, refreshed 2026-10-06) was used
> as the discovery step (`graphify query` for the volume axis, watchlist, toolbar/right-dock, alarm,
> and session surfaces). Every graph finding below was **validated against the current source
> files** (the repository is authoritative). No conflict between graph and source was found for the
> D21 surface.

---

## Codebase Summary (existing repository — D21 surface)

> Factual inventory only (no proposal). Line numbers are the current tree; the repository is
> authoritative over the graph.

### Volume pane / volume axis — `[existing] ui/chart_panel.py`
- `ChartPanel.__init__` (`:185–344`) builds a **vertical `QSplitter`** holding `price_plot`,
  `volume_plot`, `osc_plot` (`:207`, `:317–321`), sized `setSizes([600, 120, 120])` (`:320`).
- `volume_plot = pg.PlotWidget()` with **`setMaximumHeight(120)`** (`:288`) — the D21.6 cap;
  `osc_plot` also `setMaximumHeight(120)` (`:309`); the price plot has **no minimum height**.
- The volume ViewBox is linear (`setLogMode('y', False)`, `:303`); right axis is `_VolumeAxisItem`
  (`:104–108`) with `_format_volume_tick` (`500.0K / 1.0M`, `:92–101`); `setXLink(price_plot)`
  (`:295`).
- Ceiling machinery: `_vol_max` cached running max (`:199`), `_volume_nice_max` (`:200`),
  `_recompute_vol_max` (`:876–883`, O(N) per load/new bar), `_ensure_volume_range` (`:885–896`,
  writes `setRange(yRange=(0, nice), padding=0)` **only-widen**), `_widen_volume_for`
  (`:898–906`, O(1) intra-bar), `_nice_volume_max` (`:68–89`, the D8 pinned family
  `1/1.5/2/2.5/5/7.5×10^k`, floor 100).
- **No mouse-y clamp exists** on the volume ViewBox, so the user can drag the volume Y below 0
  (D21.1). The ceiling is derived from the **whole** bar list and only widens, so zoom never lowers
  it (D21.2).
- Volume toggle `_volume_toggle = QPushButton("Volume")`, checkable, default checked
  (`:326–335`), positioned top-left of the volume pane (`_position_volume_toggle`, `:401–420`);
  `_on_volume_toggled` (`:422–436`) calls `volume_plot.setVisible`, axis visibility, splitter
  `refresh()`. The label/appearance does not change when unchecked (D21.12).

### Toolbar (inside the D19/D20 scroll wrapper) — `[existing] ui/main_window.py`
- `toolbar` `QWidget` `setFixedHeight(TOOLBAR_CONTENT_HEIGHT=36)` (`:86`, `:106–108`); wrapped in a
  frameless `QScrollArea` `objectName "ToolbarScroll"`, `setWidgetResizable(False)`, horizontal
  `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`, height
  `TOOLBAR_CONTENT_HEIGHT + horizontalScrollBar().sizeHint().height()` (`:232–246`), inserted into
  the central `QVBoxLayout` above `chart_panel` (`:248–254`).
- Buttons: `studies_btn` (`:135`, plain, opens a modal dialog), `alarms_btn` (`:138`, plain),
  `alarm_mode_btn` (`:141–143`, checkable), `sound_btn` (`:145–150`, checkable),
  `dom_btn` (`:153–157`, checkable), `ext_hours_btn = QPushButton("Ext Hours")` fixed width 80
  (`:160–165`, checkable, default checked). **No active/highlight styling** beyond Qt's default
  checked look (D21.7); `ext_hours_btn` text never changes (D21.3).
- `_on_ext_hours_toggled` (`:1443–1449`) reloads the chart; `_on_alarm_mode_toggled` (`:1030–1037`)
  shows `status_bar.showMessage("Alarm mode: click the chart to place a price alarm.", 4000)`
  — **4s timeout** (D21.8) — and relies on default checked styling.
- `_open_studies_dialog` (`:976`) and `_open_alarm_dialog` (`:984`) build a dialog and call
  `exec()`; no active state on the invoking button.

### Watchlist — `[existing] ui/watchlist_panel.py`, `[existing] ui/main_window.py`
- `HEADERS = ["Symbol","Last","Bid","Ask","Chg","Chg %","Vol"]` with fixed `COL_*` indices
  (`:10–19`); `QTableWidget(0, 7)` (`:127–141`); tick handlers write cells by **hard-coded index**
  (`_set_cell`, `on_tick_price` `:206–239`, `on_tick_size` `:241–247`).
- Internal header strip `header_bar` with `QLabel("Watchlist")` (`:117–124`).
- The dock itself is `QDockWidget("Watchlist", self)` with a **second** "Watchlist" title bar
  (`ui/main_window.py:258`) — the duplicate D21.11 removes. Dock is `Movable|Floatable`
  (`:260–263`); width model D13/D17 (`dock_layout.py`) is unchanged.
- Persistence precedent: `QSettings("NDThinkChart","NDThinkChart")` key `watchlist/width` via
  `load_watchlist_width`/`save_watchlist_width` (`:58–72`, `main_window.py:271`, `:280–284`).
- `row_double_clicked` → `MainWindow._on_watchlist_row_double_clicked` → `load_chart` (D14, `:293`).

### Right dock (Active Trader + Portfolio) — `[existing] ui/main_window.py`, `[existing] ui/active_trader_panel.py`, `[existing] ui/active_portfolio_panel.py`
- One `RightDockWidgetArea` region: `right_dock = QDockWidget("Active Trader")` with
  `setObjectName("Active Trader")` (`:313–314`), containing `right_dock_container` (a `QWidget`
  with a `QVBoxLayout` holding `ActiveTraderPanel` then `ActivePortfolioPanel`, `:305–311`).
- `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH=200)` (`:323`); in-memory `_right_dock_width`
  (`:327`); `visibilityChanged → _on_right_dock_visibility_changed` (`:335–337`, `:1290`).
- `ActivePortfolioPanel.summary_label = QLabel("Account summary — disconnected")` (`:68`) is the
  first widget of the portfolio panel (the "Account Summary" label that becomes a toggle in D21.13).
- `_on_dom_toggled` (`:1462–1471`) hides/shows the **whole** region via
  `findChild(QDockWidget, "Active Trader")`.
- Dock width model: `[existing] ui/dock_layout.py` (pure, Qt-free) — `plan_dock_widths`,
  `watchlist_max_width`, `right_dock_max_width`, `CHART_MIN_WIDTH=400`, `RIGHT_DOCK_MIN_WIDTH=200`;
  `MainWindow._apply_dock_widths` (`:1132–1199`) is the single apply entry point (uses
  `_right_dock_available()` `:1071–1084` to fall back to the watchlist-only rule when the region is
  hidden).

### Alarms — `[existing] ui/alarm_dialog.py`, `[existing] ui/alarm_overlay.py`, `[existing] data/alarm_store.py`, `[existing] ui/main_window.py`
- `AlarmDialog` (`:28–163`): `QTableWidget(0, 6)` columns
  `["Price","Condition","Active","Triggered","Sound","Note"]` (`:40–47`); an entry row with
  `price_input` (`QDoubleSpinBox`), `condition_input` (`QComboBox` of
  `Cross Above/Cross Below/Cross Either` → `cross_above/cross_below/cross_either`), `sound_input`,
  `note_input`, and Add/Rearm/Mute/Delete/Close buttons (`:49–89`). **No per-row Edit button** and
  no edit dialog (D21.9). `_reload`/`_append_row` rebuild rows (`:94–118`).
- `AlarmOverlay` (`:34–226`): renders each alarm as an `InfiniteLine` (price-only) + `TextItem`
  label at `_label_x() = max(bar_count-1, 0)`; emits `create_requested(price)` on a left click in
  alarm mode (`:148–162`); supports drag/right-click menu. **No preview line** (D21.10).
- `AlarmStore` (`data/alarm_store.py`) already exposes `load/add/update/set_price/set_sound/
  rearm/delete/mark_triggered`; `update(alarm_id, **fields)` (`:63–79`) edits
  `price/direction/active/triggered/triggered_at/sound/note` **atomically** — the D21.9 edit path
  needs **no new store method**.
- `MainWindow._on_alarm_create_requested(price)` (`:1502–1509`) unchecks alarm mode, opens the
  modal `AlarmDialog(symbol, price)` (price prefilled), `exec()`, then reloads. `_reload_current_alarms`
  updates `alarms_btn` text and `chart_panel.set_alarms`.

### Sessions / x-axis / non-trading time — `[existing] services/session_service.py`, `[existing] ui/overlays/session_overlay.py`, `[existing] services/market_calendar.py`, `[existing] ui/chart_panel.py`
- `session_bands(bars, timeframe)` (`session_service.py:33–86`) returns ET pre `04:00–09:30` and
  post `16:00–20:00` intervals clipped to the bar range; `[]` for `1 day`. Pure, Qt-free, DST-aware.
- `SessionOverlay.render(bands)` draws one `pg.LinearRegionItem(values=(start_ts, end_ts))` per
  band at `Z=-10` (`session_overlay.py:13–34`).
- `market_calendar.py` (D16) is the pure ET trading-day/holiday calendar (`is_trading_day`,
  `trading_days`, `session_windows(start_ts, end_ts, ext_hours)`), consumed by `backfill_service`.
- The chart x-axis is **linear wall-clock time**: `_custom_date_axis(utc, tz_offset)` (`chart_panel.py:24`)
  wraps `pg.DateAxisItem`; `_refresh_candles` plots bars at `bar.ts` (`:802–874`); the ViewBox
  x-range is `(t0-2*bar_w, t1+8*bar_w)` (`:827`). So overnight/weekend/holiday spans render as
  empty horizontal space (D21.4).
- `_render_sessions` (`:722–734`) calls `session_bands(self._bars, tf)` then
  `_session_overlay.render(bands)`.
- `DrawingOverlay` anchors time-anchored drawings to bar timestamps (`self._bar_ts`, `:80`, `:110`,
  `:345`, `:816`) and maps scene↔view for drag (`:205`, `:491`, `:643`). Alarm lines are
  price-only; the alarm label x uses the bar count.

### Data models / tables — `[existing]`
`Bar {symbol, timeframe, ts, open, high, low, close, volume}`; SQLite tables `bars`
(PK `(symbol,timeframe,ts)`), `watchlist`, `alarms`, `zones`, `drawing_groups`, `drawings`,
`studies`, `positions`, `trade_groups`, `position_group_map`. `Alarm` model
(`data/models.py:17`) carries `id, symbol, price, direction, active, triggered, triggered_at,
sound, note, created_at`. **No D21 change requires a schema change.**

### Integrations in play — `[existing]`
IBKR historical/RT data via `ibkr/market_data.py` + `ibkr/client.py` + `ibkr/bridge.py` (Qt
signals `historical_bar`/`historical_data_end`/`error_msg`/market-data ticks); SQLite via
`data/db.py`; `QSettings` (watchlist width); Qt signal/slot bus; pyqtgraph `GraphicsScene`.

### Relevant existing tests (the D21 surface)
`tests/test_volume_linear.py`, `test_volume_log.py`, `test_volume_ceiling.py`,
`test_volume_toggle.py`, `test_volume_width.py` (volume axis/toggle);
`tests/test_watchlist.py`, `test_watchlist_d14_midrag.py` (watchlist);
`tests/test_alarm_interaction.py`, `test_alarm_overlay.py`, `test_alarm_store.py` (alarms);
`tests/test_dock_layout.py`, `test_dock_widths_d17.py`, `test_dock_widths_d18.py`,
`test_dock_widths_d18_impl.py`, `test_dock_d18_region.py` (dock model);
`tests/test_session_service.py`, `test_session_overlay.py` (session bands);
`tests/test_toolbar_scroll_d19.py`, `test_toolbar_d20.py` (toolbar wrapper);
`tests/test_history_backfill.py`, `test_backfill_service.py`, `test_market_calendar.py` (D16).
**Note:** `test_volume_linear.py`/`test_volume_log.py`/`test_volume_ceiling.py` assert the D8
**nice-max** ceiling and the ESC-007 **only-widen** rule, both of which **D21.2 supersedes** — they
must be updated in lockstep (see Architecture Risks / Non-Functional).

---

## Summary

D21 is a batch of 13 UI repairs to an already-built PyQt6/pyqtgraph terminal. The approach is
**additive and targeted**: the volume pane gets a hard `yMin=0` limit, a zoom-driven
`1.10 × max-visible` ceiling, and a larger height cap with a price-pane minimum; the toolbar gains a
single shared `VIS-D21.2` active-highlight mechanism (a Qt dynamic property + one stylesheet) and
the Ext-Hours/RTH label swap; a small reusable `DiagonalStrikeButton` (`VIS-D21.1`) is introduced
and consumed by the watchlist, volume, and right-dock toggles; the watchlist gains a field-identity
column model persisted in `QSettings` and a single header toggle; the right dock gains per-panel
hide/show with in-height and horizontal collapse; the alarm dialog gains a row Edit dialog and the
smart-setup preview line + condition default; and the x-axis gains a pure, gap-aware
**time-collapse map** that removes only between-session non-trading time on intraday timeframes
(`1 day` no-op), superseding the display part of `AC-D16.3`. **No stack change, no new dependency,
no schema change, and the live-order path is untouched.**

---

## Tech Stack Decisions

Constrained (existing) choices first, then the D21 additions.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+, PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`) | Stabilization run; changing the stack is a stated Non-Goal | New charting library / embedded web view — rejected |
| S2 | Broker / numerics / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` live port 7496 only; numpy; SQLite (`config/paths.get_db_path()`); PyInstaller `.app`; pytest + pytest-qt offscreen | Existing-repo hard constraint; live-order path gated at TWS | Paper mode / new broker / new DB — rejected |
| S3 | **Volume Y lower clamp (D21.1)** `[new]` | `volume_plot.getViewBox().setLimits(yMin=0)` | pyqtgraph enforces `yMin` in `_checkBounds` on **interactive** drag/zoom, so the min never goes below 0 without a custom event handler; programmatic `setRange(yRange=(0, …))` stays inside the limit | Override `ViewBox.mouseDragEvent`/`wheelEvent` to clamp (more code, easy to miss a path); a custom ViewBox subclass (heavier) |
| S4 | **Volume ceiling formula (D21.2)** `[new/changed]` | `ceiling = 1.10 × max(volume of bars whose x lies in the visible x-range)`; `0` visible → D8 floor `100`; recompute on **every visible-x-range change** (and on bar updates). Supersedes D8's nice-max ceiling and ESC-007's only-widen-for-zoom | Requirement is explicit (`AC-D21.2.1`); recomputing both directions is what fixes "bars squashed on zoom" | Keep the D8 nice max (does not follow the visible max); keep only-widen (the reported defect); nice-round the `1.10×` value (violates the literal measurable) |
| S5 | **Volume ceiling trigger** `[new]` | Connect `price_plot.getViewBox().sigXRangeChanged` → `_recompute_visible_volume_range()` (O(N) numpy scan over bar x), coalesced by a 0-ms `QTimer` if needed | `sigXRangeChanged` fires for zoom, pan and the magnifier area-zoom (which sets the x-range); the price ViewBox is the x master (`volume_plot.setXLink`) | Poll `viewRange()` on a timer (laggy); per-overlay hooks (misses pan) |
| S6 | **Volume pane height (D21.6)** `[new]` | `volume_plot.setMaximumHeight(VOLUME_PANE_MAX_HEIGHT)` with `VOLUME_PANE_MAX_HEIGHT = 480` (≥ 360 headroom) and `price_plot.setMinimumHeight(PRICE_PANE_MIN_HEIGHT = 200)`; splitter stays vertical, `osc_plot` cap unchanged | `AC-D21.6.1` requires the volume pane to reach **≥360px** while the price pane keeps **~200px**; a 480 cap gives margin so 360 is always reachable; the price minimum bounds the squeeze (R39) | Cap exactly 360 (no headroom; may fail to reach if the splitter distributes unevenly); remove the cap entirely (price pane can be starved) |
| S7 | **Shared active highlight (D21.7/D21.8)** `[new]` | One stylesheet on the toolbar (`#MainToolbar QPushButton:checked {…}` for checkable toggles, `#MainToolbar QPushButton[active="true"] {…}` for popup buttons) + a helper `set_button_active(btn, active)` that sets the Qt dynamic property and repolishes | `VIS-D21.2` requires one persistent, distinguishable highlight; a dynamic property + a single stylesheet is consistent, testable (property + style), and independent of scroll position in the D19 wrapper | Per-button ad-hoc `setStyleSheet` (inconsistent, hard to clear); a custom button class per toggle (duplication) |
| S8 | **Shared diagonal strike-through (D21.11/D21.12/D21.13)** `[new]` | A small reusable `DiagonalStrikeButton(QPushButton)` (new `ui/visual_conventions.py`) overriding `paintEvent` to draw a top-left→bottom-right line over the text area when a `struck` flag is set (checkable buttons auto-strike when unchecked) | `VIS-D21.1` is one convention reused by three defects; Qt stylesheets cannot draw a diagonal line, so a painted line is the reliable primitive; cosmetic pen keeps it device-pixel stable | A `QStyledItemDelegate`/`border-image` (stylesheets do not support diagonals); a separate overlay `QWidget` line (fragile, geometry-dependent) |
| S9 | **Watchlist column model (D21.5)** `[new/changed]` | A `COLUMN_DEFS` list of `(field_key, header_label)` over the existing 7 fields; an ordered `active_field_keys` list; cells created per active field; tick handlers address cells by **field key** (index resolved through the layout); `Symbol` cannot be removed; a right-click header popup (checkable add/remove + move left/right) rebuilds the table | `AC-D21.5.1`–`AC-D21.5.4` (B10): reorder/remove must not corrupt values (`DG32`); the existing 7 fields are the whole addable set | Keep index-based writes (corrupts on reorder — the DG32 failure mode); introduce new data fields (explicitly not adopted, B10) |
| S10 | **Watchlist column persistence (D21.5)** `[new]` | `QSettings("NDThinkChart","NDThinkChart")` key `watchlist/columns` (ordered, comma-joined field keys), restored on launch and sanitised (drop unknown keys, force `symbol` present) | Matches the existing D13 width persistence (`watchlist/width`); avoids a SQLite migration, consistent with the repo's "no schema change" norm | A `watchlist_columns` SQLite table (migration cost, no benefit); per-symbol layouts (not requested) |
| S11 | **Watchlist single header toggle (D21.11)** `[new/changed]` | The in-panel header strip becomes the dock's **title-bar widget** (`watchlist_dock.setTitleBarWidget(header_strip)`) and its label becomes a `DiagonalStrikeButton("Watchlist")`; "hide" collapses the panel **body** (table) while the header/title bar stays visible; Qt forwards mouse events from a custom title-bar widget to the dock, preserving drag/float | `AC-D21.11.1`–`AC-D21.11.3` (B12): exactly one "Watchlist" label, kept as the toggle, **visible when collapsed**, duplicate dock title deleted (`DG37`); a title-bar widget keeps the dock movable without a bespoke drag handle | `setTitleBarWidget(QWidget())` blank + an in-panel header (loses the drag affordance, `DG37`); hide the whole dock (the button would disappear — violates `AC-D21.11.2`) |
| S12 | **Right-dock panel toggles + collapse (D21.13)** `[new/changed]` | "Active Trader" = a `DiagonalStrikeButton` placed as the right dock's **title-bar widget**; "Account Summary" = the portfolio's `summary_label` replaced by a `DiagonalStrikeButton`. Hiding a panel hides its **body** and keeps its button; one hidden → the other expands (layout stretch). **Both hidden → horizontal collapse, driven explicitly:** `MainWindow` enters a *collapsed* state in which it (a) **relaxes the right dock's minimum width** (`right_dock.setMinimumWidth(RIGHT_DOCK_COLLAPSED_MIN_WIDTH)`, computed from the two buttons' `sizeHint()` + margins, replacing the pinned `RIGHT_DOCK_MIN_WIDTH = 200` at `ui/main_window.py:323`) and (b) **explicitly resizes the dock to the button strip** (`_resize_docks_guarded([right_dock], [collapsed_width])`), because the hidden branch of `_apply_dock_widths` only resizes the watchlist and cannot shrink the right dock. `_apply_dock_widths` **additionally treats the collapsed region as hidden for the cross-clamp** (so the watchlist regains its own cap and the chart minimum holds). **Showing either panel restores `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)` and re-applies the normal B3 cross-clamp.** | `AC-D21.13.1`–`AC-D21.13.4` (B12) and `DG35`/`DG38`: in-height collapse with a surviving button, horizontal collapse to the button strip when both are hidden, and the D17/D18 chart-minimum rule preserved. The pinned 200px minimum (`:323`) is why the collapse must relax the minimum and resize the dock explicitly — outcome-only wording is unreachable | Hide the whole region (that is the DOM button's job; loses per-panel control); a fixed narrow width without cross-clamp integration (breaks R41); rely on `_apply_dock_widths`' hidden branch alone (it never shrinks the right dock — the pinned minimum keeps it at ≥200) |
| S13 | **Alarm row edit (D21.9)** `[new]` | A per-row `Edit` `QPushButton` cell at the row's right end (Note column stretched up to it); clicking opens a small modal `AlarmEditDialog` (price/condition/sound/note + Save/Cancel) that calls the **existing** `AlarmStore.update(id, price=…, direction=…, sound=…, note=…)` on Save | `AC-D21.9.1`–`AC-D21.9.4` (B13); `AlarmStore.update` already exists and edits only the four fields, leaving `active`/`triggered`/`triggered_at` untouched, so a triggered alarm **keeps its state** (R42) | Reuse the inline entry row (cannot target a row); add a new store method (unnecessary) |
| S14 | **Smart-alarm preview line (D21.10)** `[new]` | A dedicated yellow dashed `pg.InfiniteLine` owned by `ChartPanel` (or the alarm overlay), created **only on the chart-click path** (`_on_alarm_create_requested`) — **not** on the Alarms-button path (`_open_alarm_dialog`) — and **removed on popup close**; connected to the dialog's `price_input.valueChanged` so it follows live; after Add the real `AlarmOverlay` line replaces it | `AC-D21.10.2`–`AC-D21.10.4` (B13); the preview line is required only "Given the alarm popup is open **from a chart click**", and the D21.10 edge case gives the Alarms-button popup **no** preview line (it uses the last chart price). A dedicated item with an explicit add/remove lifecycle tied to that path cannot leak onto the chart (R43) | Reuse an `AlarmOverlay` line (would be re-rendered by `set_data` and could leak); add the line on every popup open (wrong for the Alarms-button path — violates the D21.10 edge case) |
| S15 | **Smart-alarm condition default (D21.10)** `[new]` | On popup open only: `Cross Below` if `last_price > alarm_price`, `Cross Above` if `last_price < alarm_price` or `last_price is None`; user-overridable | `AC-D21.10.5` (B13), including the unknown-current-price case | Recompute on every spinbox change (contradicts "only on open") |
| S16 | **Time-collapse mechanism (D21.4)** `[new]` | A new pure, Qt-free `services/time_collapse_service.py` building a **piecewise-linear display-x map** from bar ts: a gap between consecutive bars `a < b` is collapsed **iff** `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty — i.e. no session window overlaps the gap **after accounting for bar coverage**. A bar at `ts` covers `[ts, ts + bar_period)`; bar timestamps are period **starts** (`data/bar_aggregator.py:30–32,93`), so the last RTH bar is at **15:55** and the last ext-hours bar at **19:55**, whose coverage ends exactly at the **16:00 / 20:00** session close. Testing the raw interval `[a, b]` would let the closing session's window overlap the ordinary overnight/weekend/holiday gap and wrongly keep it; testing `[a + bar_period, b]` removes the last bar's own period from the tested interval, so the ordinary between-session gap collapses while a within-session hole or a missing trading session (session time strictly between `a + bar_period` and `b`) is kept. `bar_period` is read from the existing `data/bar_aggregator.TIMEFRAME_SECONDS` map (single source of truth). `1 day` → identity. The chart plots at display-x and a `CollapsedDateAxis` maps display-x → ts for labels | `AC-D21.4.1`–`AC-D21.4.4` (B9): collapse only **between-session** non-trading time on intraday timeframes, preserve within-session spacing, keep trading-session holes visible (`AC-D16.4`), `1 day` no-op. A pure map is unit-testable and keeps `Bar.ts` (the SQLite key) untouched | Pure index-based x (collapses within-session holes too — violates the "partial/half-day missing afternoon is not collapsed" edge case and D16 no-silent-hole); mutate `Bar.ts` (corrupts persistence/drawings/backfill); a per-timeframe axis hack (no hole awareness); the un-coverage-adjusted `session_windows(a, b)` predicate (fails the ordinary overnight/weekend/holiday case — see the Risk row) |
| S17 | **Collapse consumers** `[new/changed]` | `ChartPanel` stores the map and uses display-x for candles/volume/x-range; `SessionOverlay` bands, time-anchored drawings (`DrawingOverlay._bar_ts`) and the alarm label x are mapped through it; the date axis and crosshair time tag inverse-map to ts | `AC-D21.4.1` edge cases require drawings/bands/alarms to land on the correct bars (`DG31`, R37) | Leave drawings/bands in wall-clock ts (they would misalign after collapse) |
| S18 | Testing `[existing]` | pytest + pytest-qt, offscreen, no live TWS; each fix ships a pre-fix-red/post-fix-green check | Repo standard (Q8/Q9) | Manual-only — rejected |

**No new dependency is introduced by D21.**

---

## System Components

### Existing components touched (unchanged responsibilities)
- `[existing] ui/main_window.py` — toolbar construction, Ext-Hours/Alarm-Mode slots, watchlist dock,
  single right dock region, `_apply_dock_widths` / `_chart_area_width` / `_right_dock_available`,
  alarm-dialog and DOM slots.
- `[existing] ui/chart_panel.py` — price/volume/oscillator splitter, volume ViewBox + ceiling,
  volume toggle, x-axis, `_refresh_candles`, `_render_sessions`.
- `[existing] ui/watchlist_panel.py` — table, header strip, tick handlers, D14 double-click.
- `[existing] ui/alarm_dialog.py`, `[existing] ui/alarm_overlay.py`, `[existing] data/alarm_store.py`.
- `[existing] ui/active_trader_panel.py`, `[existing] ui/active_portfolio_panel.py`.
- `[existing] ui/dock_layout.py` (pure width model), `[existing] services/session_service.py`,
  `[existing] ui/overlays/session_overlay.py`, `[existing] services/market_calendar.py`,
  `[existing] ui/drawing_overlay.py`.

### New components
- `[new] ui/visual_conventions.py` — the shared `VIS-D21` primitives: `DiagonalStrikeButton`
  (`VIS-D21.1`), the `VIS-D21.2` toolbar stylesheet string/constant, and `set_button_active(button,
  active)`. Consumed by D21.7/D21.8 (toolbar), D21.11 (watchlist), D21.12 (volume), D21.13 (right
  dock).
- `[new] ui/alarm_edit_dialog.py` — the small modal `AlarmEditDialog` (price/condition/sound/note,
  Save/Cancel) used by D21.9. (May instead live inside `alarm_dialog.py`; the module split is a
  Build detail — either way it is `[new]`.)
- `[new] services/time_collapse_service.py` — the pure, Qt-free collapse map for D21.4:
  `build_collapse_map(bars, timeframe, ext_hours) -> TimeCollapseMap` with
  `to_display(ts)`, `to_ts(x)`, `x_values`, `is_identity`; and
  `gap_is_non_trading(a, b, ext_hours, bar_period) -> bool` returning True (collapse) iff
  `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty — i.e. the gap, after
  accounting for bar coverage (`[a, a + bar_period)`), contains only non-trading time.
  `bar_period` is `TIMEFRAME_SECONDS[timeframe]`.

### Changed components
- `[new/changed] ui/chart_panel.py` — volume ViewBox `setLimits(yMin=0)` (D21.1); visible-max
  ceiling + `sigXRangeChanged` hook (D21.2); `VOLUME_PANE_MAX_HEIGHT`/`PRICE_PANE_MIN_HEIGHT`
  (D21.6); `_volume_toggle` → `DiagonalStrikeButton` (D21.12); preview-line add/remove + price-follow
  (D21.10, chart-click path only); display-x plotting + `CollapsedDateAxis` + map storage (D21.4).
- `[new/changed] ui/main_window.py` — Ext-Hours/RTH label (D21.3); active-highlight wiring for
  `studies_btn`/`alarms_btn` and `:checked` styling for the toggles (D21.7); persistent Alarm-Mode
  status message (D21.8); watchlist dock title-bar widget + toggle wiring (D21.11); right-dock
  title-bar toggle + per-panel hide/show + the **collapsed-state minimum-width relaxation and
  explicit dock resize** (D21.13); alarm edit wiring (D21.9) and preview-line creation **only on the
  `_on_alarm_create_requested` chart-click path** (D21.10).
- `[new/changed] ui/watchlist_panel.py` — field-identity column model, header context popup,
  `QSettings watchlist/columns`, `DiagonalStrikeButton` header toggle (D21.5/D21.11).
- `[new/changed] ui/alarm_dialog.py` — per-row Edit button + stretched Note column; condition
  default on open; preview-line signal (D21.9/D21.10).
- `[new/changed] ui/alarm_overlay.py` — expose the preview-line add/remove lifecycle if the item is
  owned there (D21.10); label x uses the display-x of the last bar (D21.4).
- `[new/changed] ui/active_trader_panel.py`, `[new/changed] ui/active_portfolio_panel.py` —
  `summary_label` → `DiagonalStrikeButton`; body-hide support (D21.13).
- `[new/changed] ui/overlays/session_overlay.py` — accept display-x band values (D21.4).
- `[new/changed] ui/drawing_overlay.py` — map ts anchors ↔ display-x for time-anchored drawings
  (D21.4).
- `[new/changed] services/session_service.py` — may gain a helper to expose session windows for the
  collapse rule; the existing `session_bands` contract is otherwise unchanged (D21.4).

### Component relationships (D21)
`MainWindow` remains the orchestrator: it owns the toolbar (inside the D19/D20 wrapper), the
watchlist dock, the single right dock region, and the Ext-Hours/Alarm-Mode/DOM state.
`ChartPanel` owns the price/volume/oscillator splitter, the volume ViewBox (now `yMin=0` + the
visible-max ceiling), the volume strike toggle, the x-axis and the collapse map, and the alarm
preview line. `WatchlistPanel` owns the column model and the header strike toggle.
`AlarmDialog`/`AlarmEditDialog` write through the existing `AlarmStore`; `AlarmOverlay` renders the
result. `visual_conventions` is a leaf module consumed by the toolbar, watchlist, volume, and
right-dock components. `dock_layout` + `_apply_dock_widths` remain the single width-clamp entry
point and gain a "right region collapsed" input.

---

## Data Model

- `[existing]` `Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`,
  `OrderBookLevel`, `UserOrder`; tables `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`,
  `drawings`, `studies`, `positions`, `trade_groups`, `position_group_map` — **unchanged**.
- `[existing]` `alarms` row via `AlarmStore.update` — D21.9 edits `price/direction/sound/note` and
  deliberately leaves `active/triggered/triggered_at` untouched (state preserved).
- `[new]` **Watchlist column layout** — persisted as a single `QSettings` string key
  `watchlist/columns` (ordered field keys from the fixed 7). Not a SQLite table; no migration.
- `[new]` **Time-collapse map** — an in-memory value object (`TimeCollapseMap`) on `ChartPanel`;
  ephemeral, rebuilt per load/ext-hours change; `Bar.ts` (the persisted key) is never mutated.
- `[new]` **D21 view state** — `DiagonalStrikeButton.struck`, per-panel visibility flags
  (Active Trader / Account Summary), the alarm preview line, and the volume ceiling/height
  constants are ephemeral view state (no persistence), consistent with D10's volume-visibility
  precedent.

---

## Integration Points

- `[existing]` **IBKR historical/RT data** — no new call type, no signature change, no new request
  shape. D21.4 is a **display** change only; the D16 backfill/no-silent-hole path is untouched.
- `[existing]` **SQLite (`AlarmStore`)** — D21.9 uses the existing `update()`; no schema change.
- `[existing]` **QSettings** — D21.5 adds the `watchlist/columns` key alongside `watchlist/width`.
- `[existing]` **Qt signal bus** — D21.2 adds a `sigXRangeChanged` connection on the price ViewBox;
  D21.10 connects the alarm dialog's `price_input.valueChanged` to the preview line; D21.7/D21.13
  use `toggled`/`clicked` as today. No new bus.
- `[existing]` **pyqtgraph GraphicsScene** — the D21.10 preview line is a normal scene item
  (add/remove); no fork.
- **No new external service, dependency, or persisted table is introduced.**

---

## Non-Functional Approach

- **Correctness — volume axis (D21.1/D21.2).** The lower bound is enforced structurally by
  `setLimits(yMin=0)` (pyqtgraph `_checkBounds` on every interactive range change), so
  `viewRange()[1][0] >= 0` holds after any drag/zoom; the ceiling is `1.10 × max visible` computed
  from the visible x-range, with the D8 `[0, 100]` floor when no visible bar has positive volume.
  D8's linear scale, no-negatives, min-0 and price-coloured bars are preserved; the D8 **nice-max**
  ceiling and the ESC-007 **only-widen-for-zoom** rule are superseded (recorded), while ESC-007's
  core intent (a growing forming bar must not be clipped) is preserved by recomputing on bar
  updates too.
- **Performance (D21.2).** The visible-max recompute is an O(N) numpy scan over the bar x array per
  x-range change; a 0-ms `QTimer` coalesces bursts of pan events so at most one recompute runs per
  event-loop turn. The intra-bar path stays O(1) against the cached running max. N is the loaded bar
  count (thousands), so the scan is negligible.
- **Correctness — collapse (D21.4).** The map is a pure function, unit-testable without Qt; a gap
  between consecutive bars `a < b` is collapsed **iff** `session_windows(a + bar_period, b, ext_hours)`
  is empty. Because bar timestamps are period **starts** and a bar at `ts` covers `[ts, ts + bar_period)`,
  the tested interval starts at the **end of the last bar's coverage**, not at the bar's own timestamp —
  so the previous session's window (which closes exactly at `a + bar_period` for the last bar) no longer
  overlaps the ordinary overnight/weekend/holiday gap and that gap **is** collapsed. A genuine
  trading-session hole (session time strictly between `a + bar_period` and `b`) keeps its window and
  stays as empty space (D16 `AC-D16.1`/`AC-D16.4` unchanged); a within-session hole is likewise kept.
  `1 day` is identity. Drawings, session bands, alarm labels and the date axis all consume the same map
  so they stay aligned (R37).
- **Correctness — watchlist (D21.5).** Columns bind by field identity, not index, so a reorder or
  removal cannot misroute a tick (the `DG32` failure mode); `Symbol` is forced present; the layout
  is sanitised on restore; D14's double-click resolves the Symbol field by key.
- **Correctness — toggles (D21.7/D21.8/D21.11/D21.12/D21.13).** One highlight mechanism and one
  strike primitive keep the states consistent; the highlight is a property/stylesheet (scroll-
  independent); the strike is a painted cosmetic line (device-pixel stable); the right dock's
  collapsed state **relaxes the dock's minimum width and resizes it to the button strip** (so
  `AC-D21.13.3`'s horizontal collapse is reachable despite the pinned `RIGHT_DOCK_MIN_WIDTH = 200`)
  and **also** feeds `_apply_dock_widths` as hidden/collapsed for the cross-clamp, so the D17/D18
  chart-minimum rule still holds (R41).
- **Security.** The live-order path is untouched; Q9 holds — no automated test connects to live TWS
  or transmits an order.
- **High-DPI.** The `VIS-D21.1` strike uses a cosmetic pen (device-pixel width); the volume toggle
  and strike buttons inherit existing scaling.
- **Scalability.** No per-frame allocation added beyond the O(N) scan and the per-load map build;
  overlay/label counts remain bound to drawing/bar counts.

---

## Architecture Risks

| Risk | Severity | Mitigation |
|---|---|---|
| D21.4 collapse is an x-axis model change: it supersedes `AC-D16.3`'s display rule and can affect session shading (D1), time-anchored drawings, alarm positioning and D7/D9 spacing (R37). A collapse predicate that ignores bar coverage would keep the ordinary overnight/weekend/holiday gap (the last bar's own session window overlaps the gap start) | **H** | Collapse only **between-session** gaps on intraday timeframes (`1 day` no-op); define the predicate on **bar coverage** — `session_windows(a + bar_period, b, ext_hours)` empty — so the last bar's own period is not mistaken for missing session time; keep D16 backfill/no-silent-hole unchanged; route drawings/bands/alarm labels/date axis through the same pure map; update the affected D16/D1 tests in lockstep; verify drawings/bands/alarms after collapse |
| D21.2 supersedes D8's nice-max ceiling and ESC-007's only-widen rule; stale volume tests (`test_volume_linear.py`, `test_volume_log.py`, `test_volume_ceiling.py`) assert the old behaviour | **M** | Update those tests in lockstep (assert `≈ 1.10 × visible max`); keep `_nice_volume_max` as the all-zero-floor/fixture helper; record the supersession (already on `AC-D21.2.1`) |
| D21.5 column configuration can break D14 double-click binding or lose values after reorder (R38) | **M** | Bind by field identity (not index); force `Symbol` present; persist/sanitise via `QSettings`; test reorder-then-live-tick and double-click-after-reorder |
| D21.6 raising the volume cap can squeeze the price pane below a usable height on short windows (R39) | **M** | `price_plot.setMinimumHeight(200)` + a bounded `VOLUME_PANE_MAX_HEIGHT`; verify at the target height and at a short window; no regression to D10 |
| D21.13 collapsing the right dock can conflict with the D17/D18 width model and `_apply_dock_widths` (R41) | **M** | Relax `right_dock.setMinimumWidth(...)` to the button-strip minimum and explicitly resize the dock to that strip when both panels are hidden (the hidden branch of `_apply_dock_widths` only resizes the watchlist); treat the fully-collapsed region as hidden for the cross-clamp (as `visibilityChanged` does); restore the 200px minimum and the normal cross-clamp when a panel is shown; assert the chart minimum in collapsed and expanded states; reconcile with `_on_dom_toggled` |
| D21.9 editing a set/triggered alarm could silently re-arm or disable a live alarm (R42) | **M** | Edit via Save/Cancel; persist via `AlarmStore.update` (leaves `active/triggered/triggered_at`); re-render the overlay/badge; test editing a triggered alarm |
| D21.7/D21.8 highlight may be low-contrast or clipped in the D19 wrapper (R40) | **L** | High-contrast accent style (A41); verify in the dev build and offscreen; assert active vs inactive style differs |
| D21.10 preview line must coexist with the modal dialog and not leak after close (R43), and must appear **only** on the chart-click path | **L** | Dedicated item with an explicit add-on-open/remove-on-close lifecycle **tied to `_on_alarm_create_requested`** (the chart-click path); the Alarms-button path (`_open_alarm_dialog`) creates **no** preview line (D21.10 edge case); replace with the real alarm line after Add; test open/close on both paths and live price changes |
| Batch size (13 sub-defects) touching shared chart/toolbar/dock/alarm code — one fix can regress another (R44) | **M** | Keep every fix independently tested (pre-fix red / post-fix green); re-run the full offscreen suite per wave; treat D1–D20 criteria as frozen |
| `setLimits(yMin=0)` could interfere with programmatic volume range writes | **L** | Programmatic `setRange(yRange=(0, ceiling))` stays inside the limit (min == 0); assert `viewRange()` after load, zoom and drag in the D21.1 tests |
| Removing the watchlist dock title bar removes the drag/float affordance (DG37) | **L** | Use the in-panel header strip as the dock's title-bar widget so Qt forwards drag events; assert the dock stays movable and the button stays visible when the body is collapsed |
| The right dock title bar becomes the "Active Trader" toggle (DG38) | **L** | Custom title-bar widget containing the strike button; keep a drag region (Qt forwarding); reconcile with the DOM button; treat a fully-collapsed region as hidden for the cross-clamp |
| Existing offscreen suite intermittently reports spurious failures (shared test DB) — known gotcha | **L** | Confirm with clean full-suite runs; isolate DB per test where the repo already does |
| D21.4 + D21.2 interaction: the visible-max scan must use display-x after collapse | **M** | Phase 6 must reconcile the D21.2 scan with the collapse map (both read the visible x-range); assert the ceiling after collapse |

---

## Implementation Sequencing (architecture-level)

Detailed phases, dependencies and `touches_files` notes are in `docs/plan_proposal.md`. At the
architecture level the sequence is: (1) volume axis/pane, (2) shared `VIS-D21` primitives + toolbar
state, (3) watchlist columns/header, (4) right-dock panel toggles/collapse, (5) alarm edit/smart
setup, (6) time collapse (the x-model change, sequenced last to minimise churn on the chart while
keeping the earlier volume work correct under the final x model). D1–D20 are frozen throughout.
