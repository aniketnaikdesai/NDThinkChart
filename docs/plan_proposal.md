# Implementation Plan Proposal — NDThinkChart Batch 15 (D21: 13 UI defects/issues)

> **Scope.** An *incremental* plan on top of the **already-built, green D1–D20** system
> (commit `04397d9`, 585 tests). D1–D20 are **frozen** and are **not** re-planned. This is an
> **existing-repo** run: `requirements.md` contains the marker sentence
> `This is an existing repository.` and a Current Tech Stack; **PyQt6 + pyqtgraph is a hard
> constraint**. No stack change, no schema change, no new dependency, no new external integration,
> and no live-order-path change. Items are labelled `[existing]`, `[new]`, or `[new/changed]`.
>
> **Companion architecture:** `docs/architecture_proposal.md` (Codebase Summary, tech-stack rows,
> system components, data model, integrations, non-functional, risks).
> **Requirements:** `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D21 /
> `AC-D21.*` / Journeys 22–26 / A41–A47 / R37–R44 / DG31–DG38; B9–B13 answered 2026-10-06).
> **As-built baseline:** `docs/architecture.md` (increment D20, validated 2026-10-06).
>
> **Graphify.** `graphify-out/graph.json` (2416 nodes, refreshed 2026-10-06) was used for
> discovery on the volume axis, watchlist, toolbar/right-dock, alarm, and session surfaces; every
> claim below was validated against the current source files.

---

## Coverage Map

| Requirement / journey / AC | What it demands | Phase | Verdict |
|---|---|---|---|
| **D21.1** — volume Y can be dragged below 0 | Volume Y min never below 0 | 1 | Covered |
| `AC-D21.1.1` | `viewRange()[1][0] >= 0` after any user y-interaction; no tick below 0 | 1 | Covered |
| **D21.2** — volume Y max does not update on zoom | On any visible-x-range change, `[0, 1.10 × max_volume_visible]`; min 0 | 1 | Covered |
| `AC-D21.2.1` | `viewRange()[1] == (0, ≈1.10 × max(visible volumes))`; all-zero → `[0,100]`; supersedes D8 nice-max + ESC-007 only-widen | 1 | Covered (supersession recorded) |
| **D21.3** — Ext Hours label does not change with RTH | Label `Ext Hours` when checked, `RTH` when unchecked | 2 | Covered |
| `AC-D21.3.1` | `ext_hours_btn.text()` switches immediately and after reload; 80px fits both | 2 | Covered |
| **D21.4** — empty space when market is closed | Collapse between-session non-trading time on intraday TFs; `1 day` no-op; RTH → only RTH bars + all non-RTH collapses; supersedes display part of `AC-D16.3` | 6 | Covered |
| `AC-D21.4.1`–`AC-D21.4.4` | Contiguous bars across sessions, within-session spacing preserved; `1 day` no-op; D1 bands still render; trading-session holes still visible (D16 unchanged). Predicate is coverage-adjusted (`session_windows(a + bar_period, b, ext_hours)` empty → collapse) so the last bar's own period is not mistaken for missing session time | 6 | Covered (boundary cases in the exit condition; lockstep D16/D1 test updates) |
| **D21.5** — watchlist columns fixed | Right-click header popup to add/remove/rearrange the existing 7; Symbol non-removable; layout persisted | 3 | Covered |
| `AC-D21.5.1`–`AC-D21.5.4` | Field-identity binding; immediate update; persisted across restarts | 3 | Covered |
| **D21.6** — volume pane cannot grow enough | Volume pane reaches ≥360px; price pane keeps ~200px min | 1 | Covered |
| `AC-D21.6.1` | Volume height `>= 360` in a tall-enough offscreen window; price `>= ~200` | 1 | Covered |
| **D21.7** — no visible active state for clicked buttons | Persistent `VIS-D21.2` highlight for active/selected toolbar buttons | 2 | Covered |
| `AC-D21.7.1` | Active style differs from inactive; applied while active, removed when inactive | 2 | Covered |
| **D21.8** — Alarm Mode not highlighted; message too brief | Alarm Mode highlight; status message persists until mode off | 2 | Covered |
| `AC-D21.8.1` / `AC-D21.8.2` | Highlight while active; message still shown after >4s; cleared/replaced on exit | 2 | Covered |
| **D21.9** — alarm popup cannot edit a set alarm | Row Edit button; Note widened to the Edit button; edit dialog (price/condition/sound/note, Save/Cancel, immediate persist); triggered alarms editable and keep state | 5 | Covered |
| `AC-D21.9.1`–`AC-D21.9.4` | Per-row Edit; Note stretched; Save persists via `AlarmStore`; state preserved | 5 | Covered |
| **D21.10** — alarm setup is not "smart" | Price from clicked level; yellow dashed preview line while popup open, follows price, removed on close; condition default on open (Cross Below/Above; Cross Above when unknown) | 5 | Covered |
| `AC-D21.10.1`–`AC-D21.10.5` | Prefill, preview lifecycle, live follow, replace-after-Add, condition default + override. Preview line is **chart-click path only** (`_on_alarm_create_requested`); the Alarms-button path has none | 5 | Covered |
| **D21.11** — no hide button; "Watchlist" appears twice | Delete duplicate dock title; in-panel header label becomes the toggle; stays visible when collapsed; `VIS-D21.1` strike when hidden | 3 | Covered |
| `AC-D21.11.1`–`AC-D21.11.3` | Exactly one "Watchlist" label; toggle visible when collapsed; strike when hidden | 3 | Covered |
| **D21.12** — volume button unchanged when pane hidden | `Volume` button struck when hidden, strike removed when shown | 2 | Covered |
| `AC-D21.12.1` | Strike on unchecked, removed on checked; default no strike | 2 | Covered |
| **D21.13** — cannot hide Active Trader / Account Summary | Title bar = Active Trader toggle; summary label = Account Summary toggle; one hidden → in-height collapse + other expands; both hidden → horizontal collapse to the button strip; `VIS-D21.1` strike when hidden | 4 | Covered |
| `AC-D21.13.1`–`AC-D21.13.4` | Toggle mapping, in-height/horizontal collapse (minimum relaxed + explicit dock resize to the button strip), strike, chart-minimum preserved | 4 | Covered |
| **`VIS-D21.1`** — diagonal strike-through | One straight TL→BR line over the text area when hidden/off | 2 (primitive) + 3/4 (consumers) | Covered |
| **`VIS-D21.2`** — active-button highlight | Persistent, distinguishable highlight while active | 2 | Covered |
| Journey 22 — read/adjust the volume pane | End-to-end volume drag/zoom/splitter behaviour | 1 | Covered |
| Journey 23 — collapse non-trading time | End-to-end x-axis behaviour incl. RTH and `1 day` | 6 | Covered |
| Journey 24 — configure/toggle the watchlist | End-to-end column config + header toggle | 3 | Covered |
| Journey 25 — active buttons + hide panels | End-to-end highlight/strike/right-dock collapse | 2 + 4 | Covered |
| Journey 26 — edit an alarm + place a smart alarm | End-to-end alarm edit + preview lifecycle | 5 | Covered |
| A41/A42 (`VIS-D21` confirmed) | Highlight + diagonal conventions | 2 | Covered |
| A43/A44 (alarm edit + preview, B13) | Edit dialog + preview lifecycle | 5 | Covered |
| A45 (collapse semantics, B9) | Between-session gaps only; `1 day` no-op | 6 | Covered |
| A46 (existing 7 columns, B10) | Addable set = existing 7; Symbol kept; persisted | 3 | Covered |
| A47 (volume ≥360px, B11) | Volume height target + price min | 1 | Covered |
| R37–R44 | The D21 risks (x-model, column persistence, volume height, highlight, right-dock collapse, alarm semantics, preview lifecycle, batch size) | 1/2/3/4/5/6 | Covered |
| DG31–DG38 | Design gaps (supersession, field binding, alarm semantics, preview lifecycle, right-dock collapse, highlight consistency, watchlist drag affordance, right-dock title-bar toggle) | 3/4/5/6 | Covered (DG37/DG38 mechanisms chosen here) |
| D1–D20 | Frozen, re-affirmed; not re-planned | — | Covered |

No requirement is narrowed, reinterpreted, or left unsatisfied. The one supersession
(`AC-D16.3`'s display part) and the D21.2 supersession of D8's nice-max / ESC-007's only-widen rule
are **recorded on the requirements** by the Requirements Analyst and are not silent changes.

---

## Phases

Each phase is a milestone, coarser than a task; the Task Manager decomposes each into tasks with
acceptance criteria and tests. Phases are ordered; a later phase depends on all earlier ones unless
stated. `touches_files` notes list the files a phase touches and flag the serialisation points the
Task Manager must respect when forming waves.

### Phase 1 — Volume pane axis and height (D21.1, D21.2, D21.6)

- **Goal.** The volume pane cannot be dragged below 0; its Y max tracks `1.10 × max visible volume`
  on any visible-x-range change; the pane can grow to ≥360px with the price pane keeping ~200px.
- **Covers.** D21.1 / `AC-D21.1.1`; D21.2 / `AC-D21.2.1`; D21.6 / `AC-D21.6.1`; Journey 22;
  A47; R39; parts of R44.
- **Depends on.** Nothing (first phase on the frozen D1–D20 baseline).
- **Deliverable.**
  - `volume_plot.getViewBox().setLimits(yMin=0)` (D21.1).
  - `_recompute_visible_volume_range()` computing `1.10 × max(volume of bars in the visible
    x-range)`, `0` visible → `VOLUME_NICE_FLOOR` (100), wired to
    `price_plot.getViewBox().sigXRangeChanged` and re-run on bar updates; the only-widen gate is
    removed for zoom (D21.2). `_nice_volume_max` is retained for the all-zero floor / fixtures.
  - `VOLUME_PANE_MAX_HEIGHT = 480` and `PRICE_PANE_MIN_HEIGHT = 200`; `volume_plot.setMaximumHeight`
    and `price_plot.setMinimumHeight`; splitter sizes/stretch tuned (D21.6).
  - Lockstep: update the volume tests that assert the D8 nice-max ceiling / only-widen rule.
- **Exit condition.** Offscreen: after any y-drag `viewRange()[1][0] >= 0`; after setting an
  x-range, `viewRange()[1] ≈ (0, 1.10 × max visible)`; the volume pane reaches `>= 360` in a
  tall-enough window while the price pane stays `>= 200`; full offscreen suite green.
- **`touches_files` notes.** `ui/chart_panel.py` (the whole phase is one production file — the
  three sub-defects **must share a wave/serialise** on this file);
  `tests/test_volume_linear.py`, `tests/test_volume_log.py`, `tests/test_volume_ceiling.py`
  (lockstep updates — same-file tasks serialise); a new `tests/test_volume_d21.py` (disjoint) for
  the D21.1/D21.2/D21.6 pre-fix-red/post-fix-green checks.

### Phase 2 — Shared `VIS-D21` primitives + toolbar state (D21.3, D21.7, D21.8, D21.12)

- **Goal.** One shared highlight and one shared diagonal-strike primitive; the Ext-Hours/RTH label
  swap; the persistent Alarm-Mode message; the Volume button struck when hidden.
- **Covers.** D21.3 / `AC-D21.3.1`; D21.7 / `AC-D21.7.1`; D21.8 / `AC-D21.8.1`–`AC-D21.8.2`;
  D21.12 / `AC-D21.12.1`; `VIS-D21.1`/`VIS-D21.2` (A41/A42); Journey 25 (highlight/strike);
  R40; DG36.
- **Depends on.** Phase 1 (both touch `ui/chart_panel.py`; sequential).
- **Deliverable.**
  - `[new] ui/visual_conventions.py`: `DiagonalStrikeButton` (painted cosmetic TL→BR line,
    auto-strike when a checkable button is unchecked), the `VIS-D21.2` stylesheet constant and
    `set_button_active(button, active)` (Qt dynamic property + repolish).
  - `ext_hours_btn` label switches `Ext Hours` ↔ `RTH` in `_on_ext_hours_toggled` and on init.
  - Toolbar highlight: `:checked` styling for `sound_btn`/`dom_btn`/`ext_hours_btn`/`alarm_mode_btn`;
    `set_button_active` around the modal Studies/Alarms dialogs.
  - Alarm Mode: persistent status message (no timeout) on enable, cleared/replaced on disable;
    `VIS-D21.2` highlight while active.
  - `_volume_toggle` → `DiagonalStrikeButton`, struck when unchecked (D21.12).
- **Exit condition.** Offscreen: `ext_hours_btn.text()` switches on toggle and after reload; each
  active button's style/property differs from inactive and clears on exit; the Alarm-Mode message is
  still present after >4s and gone after deactivation; the Volume button reports `struck` iff the
  pane is hidden; full suite green.
- **`touches_files` notes.** `[new] ui/visual_conventions.py` (create once — a prerequisite task);
  `ui/main_window.py`; `ui/chart_panel.py` (the volume strike; serialises with Phase 1 and any other
  chart task); new `tests/test_visual_conventions.py` and `tests/test_toolbar_d21.py` (disjoint).

### Phase 3 — Watchlist columns and single header toggle (D21.5, D21.11)

- **Goal.** Configurable watchlist columns (add/remove/rearrange over the existing 7, Symbol kept,
  persisted) and exactly one "Watchlist" toggle that stays visible and strikes when hidden.
- **Covers.** D21.5 / `AC-D21.5.1`–`AC-D21.5.4`; D21.11 / `AC-D21.11.1`–`AC-D21.11.3`; Journey 24;
  A46; R38; DG32, DG37.
- **Depends on.** Phase 2 (`DiagonalStrikeButton`).
- **Deliverable.**
  - `COLUMN_DEFS` (field key ↔ header) over the existing 7; ordered active-field list; cells built
    per active field; `_set_cell`/`on_tick_price`/`on_tick_size`/`_on_cell_double_clicked` address
    by **field key**; `Symbol` forced present; a right-click header popup (checkable add/remove +
    move left/right) rebuilds the table.
  - `QSettings watchlist/columns` persistence + sanitised restore on launch.
  - Duplicate dock title removed via `setTitleBarWidget(header_strip)`; the header label becomes a
    `DiagonalStrikeButton("Watchlist")`; hiding collapses the panel **body** while the header/title
    bar (and the button) stays visible; the strike reflects the hidden state.
- **Exit condition.** Offscreen: right-click header opens the popup; removing/reordering updates the
  table immediately with correct field binding (a reorder-then-live-tick test); `Symbol` removal is
  blocked; the layout survives a simulated restart; exactly one "Watchlist" label exists and the
  toggle stays visible + struck when the body is collapsed; D14 double-click still loads; full suite
  green.
- **`touches_files` notes.** `ui/watchlist_panel.py` (column model + header — one file, serialise
  its tasks); `ui/main_window.py` (dock title-bar widget + toggle wiring; serialises with Phase 2/4
  tasks on this file); new `tests/test_watchlist_columns_d21.py` (disjoint).

### Phase 4 — Right-dock panel toggles and collapse (D21.13)

- **Goal.** Active Trader (dock title bar) and Account Summary (portfolio summary label) become
  hide/show toggles with in-height and horizontal collapse, without breaking the D17/D18 width model.
- **Covers.** D21.13 / `AC-D21.13.1`–`AC-D21.13.4`; Journey 25 (right dock); R41; DG35, DG38.
- **Depends on.** Phase 2 (`DiagonalStrikeButton`); Phase 3 (shares `ui/main_window.py`; sequential).
- **Deliverable.**
  - The right dock's title-bar widget becomes a `DiagonalStrikeButton("Active Trader")` (drag
    preserved via Qt's title-bar event forwarding).
  - `ActivePortfolioPanel.summary_label` → `DiagonalStrikeButton("Account Summary")`.
  - Hiding a panel hides its **body**, keeping its button; one hidden → the other expands (layout
    stretch).
  - **Both hidden → horizontal collapse, driven explicitly.** Enter a *collapsed* state that
    (a) **relaxes the right dock's minimum width** to the button-strip minimum
    (`right_dock.setMinimumWidth(RIGHT_DOCK_COLLAPSED_MIN_WIDTH)`, computed from the two buttons'
    `sizeHint()` + margins) — replacing the pinned `RIGHT_DOCK_MIN_WIDTH = 200`
    (`ui/main_window.py:323`) — and (b) **explicitly resizes the dock** to that strip
    (`_resize_docks_guarded([right_dock], [collapsed_width])`). This is required because the hidden
    branch of `_apply_dock_widths` only resizes the watchlist and cannot shrink the right dock below
    its pinned 200px minimum. `_apply_dock_widths` **additionally treats the region as
    collapsed/hidden for the cross-clamp** (so the watchlist regains its own cap and the chart
    minimum holds). **Showing either panel restores `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)`
    and re-applies the normal B3 cross-clamp.**
  - Reconcile with `_on_dom_toggled` (whole-region hide) so per-panel states persist across a DOM
    toggle; the strike reflects each panel's hidden state.
- **Exit condition.** Offscreen: one panel hidden → its button remains and the other panel grows;
  both hidden → the dock's width is reduced to the **button strip (below `RIGHT_DOCK_MIN_WIDTH`)** with
  the minimum relaxed, and the chart keeps `>= CHART_MIN_WIDTH`; showing a panel restores the 200px
  minimum and the cross-clamp; each button reports `struck` iff its panel is hidden; DOM toggle still
  hides/shows the whole region; full suite green.
- **`touches_files` notes.** `ui/main_window.py` (right dock + `_apply_dock_widths` — serialise);
  `ui/active_portfolio_panel.py` (summary button); `ui/active_trader_panel.py` (body-hide support);
  new `tests/test_right_dock_d21.py` (disjoint). `ui/dock_layout.py` is **not** expected to change
  (the collapse predicate lives in `MainWindow`); if it does, it is a shared pure module — serialise.

### Phase 5 — Alarm row edit and smart setup (D21.9, D21.10)

- **Goal.** Per-row alarm editing with immediate persistence (triggered alarms keep state) and a
  smart alarm popup with a live yellow dashed preview line and an intuitive condition default.
- **Covers.** D21.9 / `AC-D21.9.1`–`AC-D21.9.4`; D21.10 / `AC-D21.10.1`–`AC-D21.10.5`;
  Journey 26; A43/A44; R42, R43; DG33, DG34.
- **Depends on.** Phases 1–4 (shares `ui/main_window.py`/`ui/chart_panel.py`; sequential).
- **Deliverable.**
  - Per-row `Edit` `QPushButton` at the row's right end; the Note column stretched up to it; clicking
    opens a small modal `AlarmEditDialog` (price/condition/sound/note + Save/Cancel) that calls the
    existing `AlarmStore.update(id, price=…, direction=…, sound=…, note=…)` on Save and reloads.
  - A yellow dashed preview `InfiniteLine` created **only on the chart-click path**
    (`_on_alarm_create_requested`) — the Alarms-button path (`_open_alarm_dialog`) creates **no**
    preview line (it uses the last chart price, per the D21.10 edge case). The line is connected to
    the dialog's `price_input.valueChanged` (live follow) and removed when **that** popup closes;
    after Add the real `AlarmOverlay` line replaces it.
  - Condition default on open only: `Cross Below` when current > alarm price, `Cross Above` when
    current < alarm price or current is unknown; user-overridable.
- **Exit condition.** Offscreen: after Save `AlarmStore.load(symbol)` returns the edited values and a
  triggered alarm stays `triggered`; Cancel discards; the preview line exists while the **chart-click**
  dialog is open, moves with the spinbox, and is removed on close; the **Alarms-button** dialog opens
  **without** a preview line; the condition default matches the three cases; full suite green.
- **`touches_files` notes.** `ui/alarm_dialog.py`; `[new] ui/alarm_edit_dialog.py` (or inline — one
  owner); `ui/alarm_overlay.py` (preview lifecycle, if owned there); `ui/chart_panel.py` (preview
  add/remove + price follow — serialise with any other chart task); `ui/main_window.py`
  (`_on_alarm_create_requested`/`_open_alarm_dialog` wiring); new `tests/test_alarm_d21.py`
  (disjoint).

### Phase 6 — Collapse non-trading time (D21.4)

- **Goal.** On intraday timeframes, between-session non-trading time (overnight/weekend/holiday) is
  not plotted as empty space; within-session spacing is preserved; `1 day` is a no-op; trading-session
  holes stay visible; D16's backfill/no-silent-hole rules are unchanged.
- **Covers.** D21.4 / `AC-D21.4.1`–`AC-D21.4.4`; Journey 23; A45; R37; DG31; the recorded
  `AC-D16.3` display-part supersession.
- **Depends on.** Phases 1–5 (shares `ui/chart_panel.py`; sequential). **Reconciles with Phase 1:**
  the D21.2 visible-max scan must use the collapse display-x after this phase.
- **Deliverable.**
  - `[new] services/time_collapse_service.py` (pure, Qt-free): `build_collapse_map(bars, timeframe,
    ext_hours)` → `TimeCollapseMap` (`to_display`, `to_ts`, `x_values`, `is_identity`);
    `gap_is_non_trading(a, b, ext_hours, bar_period)` returning True (collapse) iff
    `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty — i.e. no session window
    overlaps the gap **after accounting for bar coverage** (`[a, a + bar_period)`; bar timestamps are
    period starts, so the last RTH bar 15:55 / ext bar 19:55 covers exactly to the 16:00 / 20:00
    session close). `bar_period = TIMEFRAME_SECONDS[timeframe]`; `1 day` → identity.
  - `ChartPanel` stores the map and plots candles/volume at display-x; the ViewBox x-range uses
    display-x; a `CollapsedDateAxis` maps display-x → ts for labels; the crosshair time tag
    inverse-maps.
  - `SessionOverlay` bands, time-anchored `DrawingOverlay` anchors and the alarm label x are mapped
    through the same map (render) / inverse-mapped (drag).
  - Lockstep: update the D16/D1 tests that assert empty closures; the D21.2 visible-max scan uses
    display-x.
- **Exit condition.** Offscreen: with an intraday timeframe spanning a weekend, consecutive sessions
  are contiguous (no empty x-interval) while within-session spacing is preserved; `1 day` is
  identity; a synthetic trading-session hole is **not** collapsed; with Ext Hours ON the D1 pre/post
  bands render at the collapsed positions; drawings/alarms land on the correct bars; full suite green.
  **Boundary cases (all asserted against the real `market_calendar` helper):** the ordinary
  **RTH overnight** gap `[Fri 15:55 → Mon 09:30]` and the **ext-hours overnight** gap
  `[Fri 19:55 → Mon 04:00]` **collapse** (this is the regression the coverage-adjusted predicate
  fixes); a **weekend** gap and a **holiday** gap collapse; a **within-session hole**
  `[11:00 → 13:00]` stays **visible**; a **missing full trading session** (e.g. Mon close → Wed open
  with Tue absent) stays **visible**.
- **`touches_files` notes.** `[new] services/time_collapse_service.py` (create once — a prerequisite
  task); `ui/chart_panel.py` (x-model — serialise; the single largest change); 
  `ui/overlays/session_overlay.py`; `ui/drawing_overlay.py`; `ui/alarm_overlay.py` (label x);
  `services/session_service.py` (only if a helper is added); lockstep test updates
  (`tests/test_session_service.py`, `tests/test_session_overlay.py`, `tests/test_history_backfill.py`
  — serialise per file); new `tests/test_time_collapse_d21.py` (disjoint).

---

## Assumptions

Plan-level assumptions not already captured in `requirements.md`'s Assumptions Log (A41–A47):

- **PA-D21-1 — Volume pane cap value.** `VOLUME_PANE_MAX_HEIGHT` is set to **480** (not exactly 360)
  so the `>= 360px` target is always reachable with splitter-distribution slack, while remaining
  bounded; `PRICE_PANE_MIN_HEIGHT` is **200**. The measurable remains "volume `>= 360`".
- **PA-D21-2 — Volume ceiling recompute cadence.** The visible-max scan runs on every
  `sigXRangeChanged` (coalesced by a 0-ms `QTimer` to at most one run per event-loop turn); the
  intra-bar path stays O(1) against the cached running max. `_nice_volume_max` is retained only for
  the all-zero floor (100) and as a test fixture.
- **PA-D21-3 — Watchlist column persistence store.** The layout is persisted in `QSettings`
  (`watchlist/columns`), matching the existing D13 `watchlist/width` precedent; no SQLite migration.
  The addable set is exactly the existing 7 fields and `symbol` is forced present on restore.
- **PA-D21-4 — Watchlist hide semantics.** "Hide the watchlist" collapses the panel **body** (table)
  while the header/title bar (the toggle button) stays visible, per `AC-D21.11.2`/`AC-D21.11.3`
  (B12: the button "stays visible when collapsed"). The dock's default title bar is removed and the
  in-panel header strip is used as the dock's title-bar widget so drag/float is preserved (DG37).
- **PA-D21-5 — Right-dock collapse mechanism.** A right region with both panels hidden enters a
  *collapsed* state that (a) **relaxes the dock's minimum width** to the button strip
  (`right_dock.setMinimumWidth(RIGHT_DOCK_COLLAPSED_MIN_WIDTH)` — replacing the pinned
  `RIGHT_DOCK_MIN_WIDTH = 200` at `ui/main_window.py:323`, which otherwise makes the collapse
  unreachable) and (b) **explicitly resizes the dock** to that strip
  (`_resize_docks_guarded([right_dock], [collapsed_width])`), since the hidden branch of
  `_apply_dock_widths` only resizes the watchlist. The region is **also** treated as
  **hidden/collapsed** by `_apply_dock_widths` (so the watchlist regains its own cap and the chart
  minimum holds), mirroring the existing `visibilityChanged` path (DG35/R41). The collapsed width is
  the two buttons' width (`sizeHint`) plus margins. Showing either panel restores
  `right_dock.setMinimumWidth(RIGHT_DOCK_MIN_WIDTH)` and the normal B3 cross-clamp.
- **PA-D21-6 — DOM reconciliation.** `_on_dom_toggled` remains the whole-region show/hide and does
  **not** reset the per-panel hidden states; the per-panel buttons operate within a visible region.
- **PA-D21-7 — Alarm edit dialog placement.** The edit dialog may live in a new
  `ui/alarm_edit_dialog.py` or inside `ui/alarm_dialog.py`; either way it is `[new]` and owns its own
  test. `AlarmStore.update` is used as-is (no new store method).
- **PA-D21-8 — Preview-line ownership and path scope.** The yellow dashed preview line is owned by
  `ChartPanel` (or the alarm overlay) with an explicit add-on-open/remove-on-close lifecycle **tied to
  the chart-click path `_on_alarm_create_requested` only**. The Alarms-button path
  (`_open_alarm_dialog`) creates **no** preview line (it uses the last chart price, per the D21.10
  edge case). After Add the real alarm line replaces it. The dialog stays modal (`exec()`), as today.
- **PA-D21-9 — Collapse rule (coverage-adjusted).** A gap between consecutive bars `a < b` is
  collapsed **iff** `market_calendar.session_windows(a + bar_period, b, ext_hours)` is empty. Because
  bar timestamps are period **starts** (`data/bar_aggregator.py:30–32,93`) and a bar at `ts` covers
  `[ts, ts + bar_period)`, the tested interval starts at the **end of bar `a`'s coverage**, not at its
  timestamp — so the previous session's window (which closes exactly at `a + bar_period` for the last
  bar of a session) no longer overlaps the ordinary overnight/weekend/holiday gap, and that gap **is**
  collapsed. A gap with session time strictly between `a + bar_period` and `b` (a within-session hole,
  or a missing trading session) keeps its window and stays visible. `bar_period` is
  `TIMEFRAME_SECONDS[timeframe]`. Only intraday timeframes collapse; `1 day` is identity.
- **PA-D21-10 — Collapse consumers.** `ChartPanel` stores the map and passes display-x to
  `DrawingOverlay` (its `_bar_ts` becomes display-x) and to `SessionOverlay` bands; `Bar.ts` (the
  SQLite key) is never mutated; alarm lines are price-only and the alarm label x uses the display-x
  of the last bar.
- **PA-D21-11 — Active-highlight mechanism.** One toolbar stylesheet (`:checked` for checkable
  toggles, a dynamic `active` property for popup buttons) plus `set_button_active`; exact colours are
  implementation detail (A41), the outcome (active ≠ inactive, persistent) is the requirement.
- **PA-D21-12 — Strike mechanism.** `DiagonalStrikeButton` draws a single cosmetic TL→BR line over
  the text area; exact width is implementation detail (A42), the outcome (a visible diagonal when
  hidden/off) is the requirement.
- **PA-D21-13 — Lockstep volume tests.** `tests/test_volume_linear.py`, `test_volume_log.py` and
  `test_volume_ceiling.py` encode the D8 nice-max ceiling / ESC-007 only-widen rule and are updated
  in lockstep with D21.2 (recorded supersession); the D8 linear/min-0/price-colour behaviour stays.

---

## Flagged Issues

None. All 13 D21 sub-defects and the `VIS-D21` conventions are satisfiable as written with the
architecture above; B9–B13 are answered and every criterion is final. The two recorded supersessions
(`AC-D16.3`'s display part by D21.4; D8's nice-max ceiling and ESC-007's only-widen-for-zoom by
D21.2) are explicitly recorded on the requirements by the Requirements Analyst and are **not**
reinterpretations — they are the user-confirmed intent (B9; `AC-D21.2.1`'s supersession note).

Two design-gap items (`DG37` watchlist drag affordance, `DG38` right-dock title-bar toggle) are
explicitly left to Plan/Build by the Requirements Analyst; this proposal resolves them
(header-strip-as-title-bar widget; title-bar-widget toggle with Qt drag forwarding) rather than
flagging them. No requirement is unsatisfiable.

---

## Handoff

Both `docs/architecture_proposal.md` and this `docs/plan_proposal.md` are complete. The Validator
(`Plan Artifact Editor & Validator`) reads them, checks them against `requirements.md`, and — if
they pass — writes the canonical `docs/architecture.md` and `docs/plan.md` itself. D1–D20 remain
frozen throughout.

Status: READY_FOR_VALIDATION
