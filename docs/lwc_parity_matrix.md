# LWC parity matrix — gate skeleton (P6-01)

Row 8 (studies) is **Done / accepted** as of P6-06. Every other row is
**Open / pending**. A row moves to Done/accepted only with its gate
evidence; **a row regressing without an escalation fails review (rule 10)**.
Phase waves per `docs/plan.md` § Phases (P6-01→P6-13).

| # | Row | pyqtgraph reference (today) | LWC target | Gate wave | Disposition |
|---|---|---|---|---|---|
| 1 | Candlestick history render (all 5 modes) | `CandlestickItem.set_data` | v5 candlestick series + `setData` | P6-05 | Open / pending |
| 2 | Live forming-bar tick (no history rebuild) | live candle/volume layers (D28.4) | `series.update` per tick | P6-05 | Open / pending |
| 3 | Volume pane (linear Y, nice ceiling, floor 100) | `_nice_volume_max` family (D8/RG-002) | histogram series + ceiling port | P6-05 | Open / pending |
| 4 | Time axis + whitespace for non-trading time | `TimeCollapseMap` display-x (D21.4) | logical index + absent-data whitespace | P6-05 | Open / pending |
| 5 | Timezone display (ET, DST-correct) | `tz_offset` axes (EST 18000 / EDT 14400) | custom `timeFormatter` | P6-05 | Open / pending |
| 6 | Session shading bands (RTH/ETH) | `SessionOverlay` + `session_bands` | overlay/marker port | P6-10 | Open / pending |
| 7 | Crosshair + price/time chips | `_update_crosshair`, D2/Q33 lane | library-native crosshair (Q63/A108) | P6-07 | Open / pending |
| 8 | Studies (SMA/EMA/VWAP/BB/RSI/MACD) + cache | `indicator_service` + `_StudyCache` | shared model + LWC overlays | P6-06 | Done / accepted |
| 9 | Gap / VIX / ICT overlays | `RthGapOverlay`, `VixOverlay`, `ICTStudyOverlay` | LWC overlay port | P6-10 | Open / pending |
| 10 | Event markers (dividends/earnings/splits) | `EventMarkerOverlay` (D38) | `setMarkers` port | P6-10 | Open / pending |
| 11 | Drawings (all tools + D11 labels + D12/D15 dialogs) | `DrawingOverlay` | primitives lib (ts-to-fractional-index); Qt dialogs stay | P6-09 | Open / pending |
| 12 | Alarms (lines, placement, preview) | `AlarmOverlay` + preview line (D21.10) | alarm lines on LWC; Qt dialogs stay | P6-08 | Open / pending |
| 13 | Mouse router TR-1…TR-17 + JS mirror | `ChartMouseRouter` (frozen contract) | Python router + JS mirror (mirror never reinterprets) | P6-07 | Open / pending |
| 14 | Zoom/magnifier + reset + volume toggle + controls | `ZoomOverlay`, `ChartControls` | in-HTML controls + Python shims | P6-07 | Open / pending |
| 15 | Pop-out charts (cap 10, per-pop-out memory) | `popout_window.py`, `MAX_POPOUTS` (Q62/A107, DG90) | LWC views in pop-outs; memory accounted | P6-11 | Open / pending |
| 16 | Perf parity (Phase-0 baseline holds) | perf baseline in `docs/lwc_spike_results.md` | cutover evidence vs baseline (triple gate) | P6-12 | Open / pending |
| 17 | Bundle size + signing disposition | measured delta in `docs/lwc_spike_results.md` (Q61/A109) | vendored tree in `datas`, signed; delta recorded | P6-12 | Open / pending |
| 18 | Offline/airplane + deny-default network | new in P6-04 (DG88/DG91) | interceptor + offline case green | P6-04 | Open / pending |
| 19 | pyqtgraph default retained through cutover | locked decision (D47 reversal) | pyqtgraph present + default until Phase 11 approval | P6-12/P6-13 | Open / pending |

Row count: 19. Dispositioned Open/pending: 18. Done/accepted: 1.

## Wave exit notes

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
