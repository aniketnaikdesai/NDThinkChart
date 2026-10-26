# LWC parity matrix — gate skeleton (P6-01)

Rows 7, 8, 11, 12, 13 and 14 are **Done / accepted** as of P6-09 (row 8 as of
P6-06, rows 7/13/14 as of P6-07, row 12 as of P6-08). Every other row is
**Open / pending**. A row moves to Done/accepted only with its gate evidence;
**a row regressing without an escalation fails review (rule 10)**. Phase waves
per `docs/plan.md` § Phases (P6-01→P6-13).

| # | Row | pyqtgraph reference (today) | LWC target | Gate wave | Disposition |
|---|---|---|---|---|---|
| 1 | Candlestick history render (all 5 modes) | `CandlestickItem.set_data` | v5 candlestick series + `setData` | P6-05 | Open / pending |
| 2 | Live forming-bar tick (no history rebuild) | live candle/volume layers (D28.4) | `series.update` per tick | P6-05 | Open / pending |
| 3 | Volume pane (linear Y, nice ceiling, floor 100) | `_nice_volume_max` family (D8/RG-002) | histogram series + ceiling port | P6-05 | Open / pending |
| 4 | Time axis + whitespace for non-trading time | `TimeCollapseMap` display-x (D21.4) | logical index + absent-data whitespace | P6-05 | Open / pending |
| 5 | Timezone display (ET, DST-correct) | `tz_offset` axes (EST 18000 / EDT 14400) | custom `timeFormatter` | P6-05 | Open / pending |
| 6 | Session shading bands (RTH/ETH) | `SessionOverlay` + `session_bands` | overlay/marker port | P6-10 | Open / pending |
| 7 | Crosshair + price/time chips | `_update_crosshair`, D2/Q33 lane | library-native crosshair (Q63/A108) | P6-07 | Done / accepted |
| 8 | Studies (SMA/EMA/VWAP/BB/RSI/MACD) + cache | `indicator_service` + `_StudyCache` | shared model + LWC overlays | P6-06 | Done / accepted |
| 9 | Gap / VIX / ICT overlays | `RthGapOverlay`, `VixOverlay`, `ICTStudyOverlay` | LWC overlay port | P6-10 | Open / pending |
| 10 | Event markers (dividends/earnings/splits) | `EventMarkerOverlay` (D38) | `setMarkers` port | P6-10 | Open / pending |
| 11 | Drawings (all tools + D11 labels + D12/D15 dialogs) | `DrawingOverlay` | primitives lib (ts-to-fractional-index); Qt dialogs stay | P6-09 | Done / accepted |
| 12 | Alarms (lines, placement, preview) | `AlarmOverlay` + preview line (D21.10) | alarm lines on LWC; Qt dialogs stay | P6-08 | Done / accepted |
| 13 | Mouse router TR-1…TR-17 + JS mirror | `ChartMouseRouter` (frozen contract) | Python router + JS mirror (mirror never reinterprets) | P6-07 | Done / accepted |
| 14 | Zoom/magnifier + reset + volume toggle + controls | `ZoomOverlay`, `ChartControls` | in-HTML controls + Python shims | P6-07 | Done / accepted |
| 15 | Pop-out charts (cap 10, per-pop-out memory) | `popout_window.py`, `MAX_POPOUTS` (Q62/A107, DG90) | LWC views in pop-outs; memory accounted | P6-11 | Open / pending |
| 16 | Perf parity (Phase-0 baseline holds) | perf baseline in `docs/lwc_spike_results.md` | cutover evidence vs baseline (triple gate) | P6-12 | Open / pending |
| 17 | Bundle size + signing disposition | measured delta in `docs/lwc_spike_results.md` (Q61/A109) | vendored tree in `datas`, signed; delta recorded | P6-12 | Open / pending |
| 18 | Offline/airplane + deny-default network | new in P6-04 (DG88/DG91) | interceptor + offline case green | P6-04 | Open / pending |
| 19 | pyqtgraph default retained through cutover | locked decision (D47 reversal) | pyqtgraph present + default until Phase 11 approval | P6-12/P6-13 | Open / pending |

Row count: 19. Dispositioned Open/pending: 13. Done/accepted: 6.

## Wave exit notes

### P6-09 — Phase 7 drawings (2026-10-26)

- **One primitives library, one mapping pair.** `chart_assets/lwc/primitives.js`
  renders the five drawing kinds (trendline, horizontal, zone, Fibonacci,
  measure) from `ui/lwc_view.py`'s `set_drawings` / `set_drawing_primitive`
  envelopes. Every anchor timestamp becomes a **fractional logical index** —
  the candles' own axis unit: a bar's timestamp maps to that bar's integer
  index, a between-bars point interpolates on the same display-x axis the
  reference engine draws on, and a display-x collision (DG93: two bars sharing
  one x) resolves to one deterministic index while the inverse returns the
  shared x for either. `fractional_index_from_display` +
  `display_from_fractional_index` are the whole contract; the inverse of a
  mapped anchor equals `DrawingOverlay._ts_to_x(ts)` value-for-value.
- **DG93 timestamp edge fixtures.** The parity suite parametrizes all five
  kinds × four fixtures: the 2024-11-03 EDT→EST fold, the 2025-03-09
  EST→EDT spring-forward, RTH/session boundaries with the overnight collapse
  and out-of-window anchors, and two display-x collisions. Collisions keep
  strictly rising indices (no bar is lost) and resolve identically on both
  engines.
- **Values cross; labels are composed engine-side.** Geometry is Python-owned
  from `services.drawing_service.py` (`normalize_payload`, `fib_levels`); the
  wire carries fractional indices, prices, colours, pen widths, Fibonacci
  ratios, the measure delta and handle anchors — no timestamp and no formatted
  string. JS composes the D11 inner-right labels (`100.50`,
  `61.8%  101.58`) and the measure `Δ` label, and stacks them with the
  reference measured-bbox rule (15 px floor, right inset 4 px). The reference
  `_build_items` final z override (every item z = 10) is mirrored exactly.
- **Groups, handles and drag-edit as primitives.** Group visibility/lock state
  mirrors `DrawingOverlay` (hidden groups publish nothing; locked groups never
  show handles); selection publishes the reference white 2.0 px pen plus the
  `#0ea5e9` handles; a body/endpoint drag is computed in Python
  (`drag_drawing_item`, the `_apply_drag` mirror) and published as validated
  replacement geometry, with the JS `dragItem` mirror for live feedback.
- **Zone / horizontal-line settings stay the same Qt dialogs.** No HTML dialog
  exists under `chart_assets/` (absence probe); the Qt dialog suites
  (`tests/test_zone_dialog.py`, `tests/test_horizontal_line_dialog.py`) are
  green unmodified. Persistence (`DrawingStore`), `drawing_service` and the
  reference overlay are untouched — the residue scan proves no LWC vocabulary
  entered them.
- **Cutover wiring, as for studies/interaction/alarms.** Including
  `primitives.js` in `chart.html` and forwarding `drawingOpsEmitted` are
  page/host wiring at cutover; the parity itself is engine-agnostic (node +
  Python, no Chromium needed).
- Gate evidence: `tests/test_lwc_drawings.py` (mapping round-trip per DG93
  fixture, kind × fixture parity against the drawn reference items, fib
  retr/ext levels, custom colour, replay/empty-clear, primitive validation,
  groups/handles/selection, endpoint and body drag vs `_apply_drag`,
  renderer-only residue + AST import boundary + bar-transport isolation, Qt
  dialog absence/green) + `node --test chart_assets/lwc/`. Row 11 moves to
  **Done / accepted**; no Done row regressed, 13/19 remain Open / pending.

### P6-08 — Phase 6 alarms (2026-10-26)

- **One alarm channel, values by reference.** `ui/lwc_view.py` publishes the
  unchanged alarm records as raw state columns (`id`, `price`, `direction`,
  `active`, `triggered`, `sound`, `note`) on `alarmOpsEmitted` — the same
  separate-envelope pattern as studies/interaction, because the bar transport
  pins its series set to candles/volume. `chart_assets/lwc/alarms.js` turns
  those columns into price lines on the candle series. The colour precedence
  (triggered → inactive → muted → armed), the direction glyph table, the
  `▲ 101.2500 (hit) · note` label composition, the 1.4 px pen and the z-order
  (line 6, label 7) are the reference `ui/alarm_overlay.py` values, asserted
  against that overlay's own `_color_for` / `_label_text` / drawn items on
  shared fixtures rather than restated here.
- **Labels are composed engine-side.** No formatted string crosses: the wire
  carries prices and state bits, and JS composes the same label string. The
  label rides the library-native right-edge price-line axis label
  (`axisLabelVisible` + `title`), the LWC equivalent of the D21.4 right-anchored
  `TextItem`.
- **One documented library concession.** LWC price lines accept an integer
  `lineWidth` (1..4); the reference 1.4 px width crosses unchanged in the op
  spec (`width: 1.4`) and the library call takes the nearest supported integer
  (1). Colour, label text, price level and z-order are exact.
- **Preview line (D21.10)** — `show_alarm_preview` / `update_alarm_preview` /
  `hide_alarm_preview` mirror `ChartPanel`'s semantics (idempotent show, hide,
  update-while-hidden is a no-op): yellow `#ffff00`, dashed, below the alarm
  lines (`z` 5), no axis label.
- **Placement stays in the frozen router.** `set_alarm_mode` routes through
  `ChartMouseRouter` (TR-3/TR-6/TR-13) and is inert on a non-editable pop-out
  (D24); TR-9 still refuses the magnifier while placing. The alarm Qt dialogs
  (create/edit/rearm/mute/delete) and `AlarmStore` are untouched — the residue
  scan proves no LWC vocabulary entered `alarm_overlay.py`, `chart_panel.py` or
  `alarm_store.py`.
- **Cutover wiring, as for studies/interaction.** Including `alarms.js` in
  `chart.html` and forwarding `alarmOpsEmitted` are page/host wiring at
  cutover; the parity itself is engine-agnostic (node + Python, no Chromium
  needed), which is why row 12 carries green gate evidence now.
- Gate evidence: `tests/test_lwc_alarms.py` (five-state colour/label/price/z
  parity against the drawn reference items, empty-set clear, replay identity,
  preview line, router placement, non-editable no-op, renderer-only residue +
  AST import boundary + bar-transport isolation) + `node --test
  chart_assets/lwc/`. Row 12 moves to **Done / accepted**; no Done row
  regressed, 15/19 remain Open / pending.

### P6-07 — Phase 5 interaction (2026-10-26)

- **Router mirror, never a reimplementation.** `ui/lwc_view.py` carries
  `ROUTER_TRANSITIONS` — the transcription of the frozen TR-1…TR-17 table
  owned by `ui/chart_mouse_router.py` (one `RouterMode`, intent helpers,
  guard-clause dispatch) — and `chart_assets/lwc/interaction.js` carries the
  row-for-row mirror plus `resolveTransition()` (same precedence
  DRAWING > ZOOMING > ALARM_PLACING > IDLE, same TR-9 refusal, same TR-17
  reset) and `routeGesture()` (alarm first in IDLE, drawing-only click while
  DRAWING). The mirror suites drive **both** engines over all 17 rows *and*
  the full mode × gesture sweep: a mutated mirror row fails the suite.
- **In-HTML controls with Python shims.** `CONTROL_IDS`
  (`zoom-out`/`zoom-in`/`magnifier`/`reset`) mirrors `ui/chart_controls.py`'s
  signal surface (same labels and tooltips) and
  `LwcChartView.handle_control` is the shim: the magnifier and reset route
  through the frozen router, so alarm placement **refuses** the magnifier
  (TR-9) through the control path too, not only through the router API.
  Zoom in/out are pure view intents (`ZOOM_FACTORS` 0.8/1.25 — the numbers
  `chart.js`'s keyboard handler already uses). Interaction ops travel on
  their own `{"v":1, ops:[…]}` envelope (`interactionOpsEmitted`), for the
  same reason as the study channel: the bar transport pins its series set.
- **Crosshair drift (Q63 / A108 owner-confirmed accept-drift).** The crosshair
  and its price/time labels are the **library-native** crosshair + axis
  labels: `crosshairOptions()` sets `vertLine.labelVisible` /
  `horzLine.labelVisible` on `CrosshairMode.Normal`, applied through
  `chart.applyOptions({crosshair: …})`. There is no custom crosshair-label
  primitive in `chart_assets/` and none in the Python driver — the D2/Q33
  lane stops at the engine boundary. The zone / horizontal-line / alarm
  dialogs are untouched Qt dialogs (their suites are green in the same gate).
- **Focus round-trip (DG92).** `lwc-focus-forward-v1` is named in
  `interaction.js` (`releaseFocus` hands focus back through the bridge's
  `focusReleased` slot); `LwcChartView.handle_focus_released` records the
  round trip so the wave reports it.
- **Symbol change (TR-17).** `set_symbol` resets the interaction through
  `reset_router_for_symbol_change` — public router API only, so
  `ui/chart_mouse_router.py` stays byte-for-byte the frozen contract (the
  residue scan proves no LWC/mirror vocabulary entered it).
- **Cutover wiring, as for studies.** Including `interaction.js` in
  `chart.html`, mounting the buttons and forwarding `interactionOpsEmitted`
  / `focusReleased` are page/host wiring at cutover, like the study channel;
  the mirror itself is engine-agnostic (node + Python, no Chromium needed),
  which is why rows 7/13/14 carry green gate evidence now. The rendered
  control-surface confirmation on the engine box rides the P6-12 cutover
  gate.
- Gate evidence: `tests/test_lwc_router_mirror.py` (17/17 TR rows identical
  across engines, refusal TR-9 explicit, TR-17 reset from every mode, the
  mode × gesture dispatch sweep, control-id/signal mirror, the crosshair
  config + absence scan, the untouched-router residue scan, the
  renderer-only import boundary) + `tests/test_zone_dialog.py` +
  `tests/test_horizontal_line_dialog.py` + `node --test chart_assets/lwc/`.
  Rows 7/13/14 move to **Done / accepted**; row 8 unchanged; 15/19 remain
  Open / pending and no Done row regressed.

### P6-06 — Phase 4 studies (2026-10-26)

- `ui/lwc_view.py` gained the study surface: `set_studies(studies)` and the
  contracted `set_study_overlay(kind, series)`. Every value comes from
  `services/chart_model.py::compute_study_values` over the view's **one**
  `StudyCache` — the same source the default engine renders — so study
  parity is by construction, not by parallel logic.
- `chart_assets/lwc/studies.js` landed: the study channel's membrane
  (`studyRows` / `lineRows` / `paneFor` / `describeStudyOp` /
  `validateEnvelope`) plus the chart glue that puts those columns on
  line/histogram series. Nulls cross as whitespace rows (`{time}`), never
  as a fabricated 0; the JS side formats and renders, it never computes an
  indicator.
- **Transport.** Study ops carry a dedicated envelope
  (`{v:1, ops:[{op:"set_study", series:"studies", kind, pane, style,
  cols:{ts, value}}]}`) emitted on `LwcChartView.studyOpsEmitted`: the bar
  bridge (`ui/lwc_bridge.py` / `chart_assets/lwc/envelope.js`) pins its
  series set to candles/volume, so studies never ride the bar transport
  and the replay identity of that transport is untouched. Including
  `studies.js` in `chart.html` and forwarding the signal is part of the
  cutover wiring, like the driver's `ensure_host`/factory seam.
- **Cache reuse.** A repeated render of an identical state (same bars, same
  configuration) is a no-op: no computation and no traffic. A new candle is
  served by the `StudyCache` incremental path (0 full recomputes in the
  probe); an intra-bar tick takes the full path exactly as the default
  engine's D28.4 path does, because the forming bar's study value has no
  cached state to replay from.
- Gate evidence: `tests/test_lwc_studies.py` (per-overlay value equality
  against a cold shared-model computation, logical-index alignment, the
  node membrane returning the same numbers, the cache-reuse probe, the
  contract method, overlay/disabled studies, residue scan) +
  `node --test chart_assets/lwc/`. Row 8 moves to **Done / accepted**;
  18/19 remain Open / pending and no Done row regressed.

### P6-05 — Phase 3 core chart + T10 density-cap retirement (2026-10-26)

- `ui/lwc_view.py` landed: v5 panes (price + volume), logical-index time
  axis with whitespace for within-session holes, `gap_is_non_trading` as
  the authority in both engines, custom tz formatter
  (`local = t - offset`; `format_tz_label` in Python, `tzLabel` in JS),
  per-mode series (`candles` / `hollow` / `heikin` / `line` / `area`) and
  live `series.update` via single-element `update_bar` ops. The full-history
  `ts` column and the live `update_bar` `ts` share one unit — the logical
  index — so a tick advances the forming bar instead of appending a
  phantom one.
- `chart_assets/lwc/chart.js` landed: the DOM-free per-mode registry +
  `tzLabel` + `barGeometry` + `describeOp` the page glue builds on; the
  vendored v5.2.1 tree is untouched.
- **T10 density-cap retirement (Q60 answered-by-default YES / A106).**
  The density-cap wording of **`AC-D6.4`**, **`AC-D7.1`** and
  **`AC-D9.1`** is **retired for `barSpacing` only** — it is not withdrawn
  from the pyqtgraph engine, which keeps satisfying those ACs unchanged
  until cutover (P6-13, owner-gated). The retirement is recorded here, in
  the wave result, and in `docs/build/results/P6-T05.json` — never silent.
- **Restated no-overlap guarantee (DG94).** With library inter-bar spacing
  `S` px, the rendered body is `min(S, max(0.65*S, 4px))` and the gap is
  `S - body`: **`gap >= 0` always** (bodies never overlap) and **`gap > 0`
  whenever `S` exceeds the 4 px floor**. Enforced by
  `ui/lwc_view.py::bar_spacing_geometry` /
  `chart_assets/lwc/chart.js::barGeometry` and the rendered-geometry guard
  in `tests/test_lwc_time_parity.py` (`barSpacing` 0.5–100 px, plus the
  65/35 non-dense split and the shared price/volume rule).
- Gate evidence: `tests/test_lwc_time_parity.py` (DST fold,
  session-boundary, within-session hole, duplicate-display-x, tz labels,
  live `series.update`, geometry guard, Q60 record, residue scan) +
  `node --test chart_assets/lwc/` (10/10). The pyqtgraph density suites
  (`test_d42_candle_width`, `test_candle_spacing`) are untouched and green.
- Parity rows 1–5 (candle history, live tick, volume pane, time
  axis/whitespace, tz display) carry green offscreen gate evidence;
  their engine-box (Chromium) render confirmation is still pending —
  `PyQt6-WebEngine` is not installed in this venv, so the
  `@pytest.mark.webengine` cases skip per the P6-04 pattern. Rows keep
  **Open / pending**; 19/19 unchanged, Done/accepted 0.

### P6-04 — Phase 2 runtime + self-healing bridge (2026-10-26)

- `ui/lwc_host.py` landed (offline `QWebEngineView` host): vendored
  lightweight-charts v5.2.1 via `ndt://lwc/` (scheme registered before
  `QApplication`, ordering probe), deny-default interceptor (`ndt`/`qrc`/
  `data`/`blob` only), attribution in `chart_assets/lwc/ATTRIBUTION.md`,
  focus/keyboard model `lwc-focus-forward-v1` named in-code (DG92).
- `ui/lwc_bridge.py` landed (batched `QWebChannel` `LwBridge`): versioned
  `{v:1,ops:[]}` column-array ops, queue-until-ready, ~33 ms live coalesce,
  full op-log replay after `renderProcessTerminated`, backpressure counters
  instrumented from day one (DG91).
- `chart_assets/lwc/` holds the vendored v5.2.1 tree + `VERSION` pin +
  `envelope.js` contract (mirrored by the Python bridge) + `node --test`
  suite (offline/no-remote scan + envelope + idempotent-replay cases).
- `pytest.ini` registers the `webengine` marker (skip-never-red, DG88/A110);
  engine-gated cases skip here and name their manual counterparts.
- Gate evidence: `tests/test_lwc_bridge.py` (offline/interceptor, batch
  shape, replay identity, marker audit, renderer-only residue scan) +
  `node --test chart_assets/lwc/`.
- No parity row changes disposition in this wave: row 18 keeps
  **Open / pending** — its offscreen evidence is green but the engine-box
  confirmation (host load + interceptor + recovery on Chromium) is still
  pending per the skips above. No Done row regressed.

### P6-03 — Phase 1b shared model + delegation (2026-10-26)

- `services/chart_model.py` landed (Qt-free): plotted-index filtering,
  `floor_bar_budget` (re-exported single source), whitespace derivation
  (collapse map), candle/volume display rows + columns, median-spacing
  geometry, volume family/ceiling/tick formatting, Heikin-Ashi, studies +
  `StudyCache` (full/incremental, tail-exact).
- `ui/chart_panel.py` delegates every plotted value to the model with no
  behaviour change; pyqtgraph stays present and default.
- Gate evidence: `tests/test_chart_model.py` (delegation probe +
  renderer-only residue scan) + the named pre-D47 suites green unmodified
  (candles, volume, collapse, bands, crosshair, drawings, alarms, overlays).
- AP-P6-3 classification recorded in the wave result per
  `docs/tasks/task_manager_notes_P6.md`: 34 engine-specific (P6-13 deletion
  set), 32 retarget (must pass under both engines), 59 keep.
- No parity row changes disposition in this wave: 19/19 remain Open /
  pending; render parity is P6-05+ work. No Done row regressed.

### P6-02 — Phase 1a seam (2026-10-26)

- `ui/chart_view.py` landed: `ChartView` protocol (`update_bars` /
  `update_last_bar` / `set_symbol` / `set_timeframe`), `DrawingController` /
  `AlarmController` carrying the exact pre-D47 signal surface, and
  `create_chart_view(tz_offset, editable)` selecting the pyqtgraph view for
  unset/unknown/`pyqtgraph` values (and the `QSettings` equivalents) and the
  LWC stub view only for the `lwc` value — never a blank chart.
- Gate evidence: `tests/test_chart_view_seam.py` (factory cases +
  per-controller signal-signature assertions + renderer-only boundary scan).
- No parity row changes disposition in this wave: 19/19 remain Open /
  pending; render parity is P6-05+ work. No Done row regressed.
