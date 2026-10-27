# Task Manager Notes — Phase P6 (D47: chart stack migrates to Lightweight Charts)

## Wave → task map (approved 13; strictly sequential, no re-derivation)

| Task | Wave / D47 phase (effort) | Goal |
|---|---|---|
| P6-T01 | P6-01 Phase 0 spike (S) | Throwaway `spikes/lwc/` 9-API proof + `docs/lwc_spike_results.md` go/no-go + size/perf baseline + 19-row matrix skeleton |
| P6-T02 | P6-02 Phase 1a seam (M) | `ui/chart_view.py` protocol + controllers + `create_chart_view` (pyqtgraph default) |
| P6-T03 | P6-03 Phase 1b model (M) | `services/chart_model.py` + `ChartPanel` delegation, no behaviour change + AP-P6-3 classification in result |
| P6-T04 | P6-04 Phase 2 host+bridge (L) | `ui/lwc_host.py` + `ui/lwc_bridge.py` + `chart_assets/lwc/` + webengine marker + DG92 focus model |
| P6-T05 | P6-05 Phase 3 core chart (L*, XL effort) | `ui/lwc_view.py` + `chart.js` time/pane/series parity + **T10 Q60 density-cap retirement on the Q60 record** |
| P6-T06 | P6-06 Phase 4 studies (M) | Studies through model+cache on LWC |
| P6-T07 | P6-07 Phase 5 interaction (L*, XL effort) | Controls+shims, JS router mirror, crosshair drift (Q63) |
| P6-T08 | P6-08 Phase 6 alarms (M) | Alarm lines/overlays on LWC; Qt dialogs stay |
| P6-T09 | P6-09 Phase 7 drawings (L*, largest) | `primitives.js` ts-to-fractional-index library + DG93 edge fixtures |
| P6-T10 | P6-10 Phase 8 overlays (M) | Session/gap/ICT/VIX + event markers on LWC |
| P6-T11 | P6-11 Phase 9 pop-outs (L) | LWC re-host; cap stays 10 (Q62); per-pop-out memory (DG90) |
| P6-T12 | P6-10 packaging/CI/candidate (M) | Specs + CI + signing disposition + triple-gate declaration, pyqtgraph present+default |
| P6-T13 | P6-11 removal (S, **gated**) | pyqtgraph deletion ONLY on explicit owner approval + one clean live session |

## Dependency edges (logical ordering, not file overlap)

`P6-T01 → P6-T02 → … → P6-T13`, each task depending on its predecessor only.
Single chain, no branches — exactly the plan's one-commit-per-wave order. Shared
files across sequential waves (`services/chart_model.py` reads, `ui/lwc_view.py`,
`chart_assets/lwc/*` globs, `docs/lwc_parity_matrix.md` wave exits) are safe
because the chain serializes them; no two tasks in the same wave exist.

## Size exceptions (step-fit rule, ~32 cap)

- **P6-T05 (plan XL → size L):** panes + logical-index axis + tz formatters +
  per-mode series + live update + T10 retirement + geometry guard. Kept whole
  because splitting the time mapping from its own retirement record would fork
  the one authority (`gap_is_non_trading`) across two owners.
- **P6-T07 (plan XL → size L):** controls + shims + 17-row mirror + drift.
  Kept whole because the mirror's single-owner property (one suite asserting
  all TR rows identically on both engines) is the invariant; a split mirror
  suite could pass half-green while the engines diverge.
- **P6-T09 (plan XL, largest → size L):** whole primitives library +
  parametrized DG93 fixtures. Kept whole because the ts-to-fractional-index
  mapping is one function family; parametrized kind×fixture cases count as one
  test-writing action, and splitting by drawing kind would duplicate the
  collision-fixture harness per task. If the worker reports step pressure, the
  Orchestrator may finish in place (D41 precedent) — never silently drop a kind.

## P6-T13 DISPATCH GATE (S59 / AC-D47.8)

Do NOT dispatch P6-T13 until BOTH artifacts exist on record:
(1) explicit owner approval of pyqtgraph deletion, and
(2) sign-off of one live trading session with no engine defect.
Gated-closed, the worker MUST refuse before editing (AC1 — refusal is green).
Phase 11 never rides along with cutover. Proposed gate probes:
`docs/lwc_removal_approval.md` + `docs/lwc_live_session_signoff.md`
(the task's `test_command` asserts GATE-OPEN vs GATE-CLOSED).

## AP-P6-3 classification — chart-adjacent test files (keep / retarget / engine-specific)

Rule: **keep** = backend/pure/dock/watchlist/dialog/guard suites (engine-blind,
green throughout); **retarget** = suites driving `MainWindow`/load path that
must pass under BOTH engines (P6-T03 keeps them green; parity waves re-point
them); **engine-specific** = suites asserting pyqtgraph items/geometry (stay on
pyqtgraph; P6-13 deletes per this list; LWC twins land per wave).
Counted 66 chart-adjacent of 125 (delta vs plan's 66: none — 34 + 32 = 66).

ENGINE-SPECIFIC (34 — P6-13 deletion set): test_candle_spacing,
test_candlestick_wick, test_volume_width, test_volume_linear, test_volume_log,
test_volume_ceiling, test_volume_d21, test_volume_toggle, test_chart_crosshair,
test_crosshair_axis_lane, test_crosshair_chip_bounds, test_chart_dpi,
test_chart_controls, test_zoom_overlay, test_zoom_behavior,
test_drawing_overlay, test_drawing_interaction, test_drawing_labels,
test_d27_drawing_colours, test_alarm_overlay, test_alarm_interaction,
test_session_overlay, test_study_overlays, test_d27_overlay_coords,
test_time_collapse_d21, test_collapse_resync_fix, test_d28_4a_render_layers,
test_d28_4f_panel_bar_cap, test_d28_4_bisect, test_d42_candle_width,
test_d28_4d_collapse_tail, test_draw_combo_sync, test_d28_4f_study_invalidate,
test_d28_4b_study_cache.
RETARGET (32 — must pass under both engines): test_d24_chart_quality,
test_d24_smoke_gate, test_d24_alarm_full_chain, test_d24_popouts,
test_d24_9_popout_persistence, test_phase3_fixpass, test_history_backfill,
test_history_backfill_disconnect, test_history_backfill_loadpath,
test_d28_2_sessions, test_d28_2_load_chart_button, test_d27_reconnect,
test_d42_depth_floor, test_d42_day_presence, test_d42_mode_cache,
test_d27_backfill_granularity, test_d27_et_anchoring,
test_d27_aggregator_priming, test_d28_3_historical_pacing,
test_d28_tick_burst_baseline, test_d38_events_news, test_d39_burst_search,
test_d28_4_gate, test_d42_nonregression, test_d23_nonregression,
test_ui_smoke, test_alarm_d21, test_d10_d13_integration,
test_d28_5_teardown, test_d27_phantom_alarms, test_d21_flash_lifetime,
test_d28_6_drawing_roundtrip.
KEEP (all other 59): untouched by the renderer migration; any failure there
during P6 is a regression, never an engine difference.

## Constraints encoded (as dependencies / ACs, not prose)

- Renderer-only: every task P6-T02→P6-T12 carries the residue AC (no `ibkr/`,
  schema, service-signature, watchlist/dock, order-code change; JS gets
  timestamps+prices only) with a diff-scan test.
- Spike fence: P6-T01 AC2 + fence `test_command`; packaging exclusion verified
  in P6-T12 (spec names only the vendored tree).
- Q60 retirement ONLY in P6-T05 with the Q60 record (matrix + result); the
  pyqtgraph engine keeps satisfying the old ACs until cutover.
- Q61 measure-first: P6-T01 AC3 (measured delta + signing finding + perf
  baseline) → P6-T12 disposition cites those numbers; no invented budget.
- Q62 keep-10: P6-T11 AC2 (cap refused identically on both engines).
- Q63 accept-drift: P6-T07 AC2 (library-native crosshair, no custom
  primitive; AP-P6-6 — no visual-reference artifact required).
- Engine-specific suites are never "fixed" to pass on LWC; a red one is a
  regression until P6-T13 deletes it per the list above.

## Deviations (tasking choices within approved waves, not scope changes)

1. New-file paths chosen by Task Manager where the plan/architecture name
   components without paths: `ui/lwc_host.py`, `ui/lwc_bridge.py`,
   `ui/lwc_view.py`, `chart_assets/lwc/*.js`, `pytest.ini` marker,
   `.github/workflows/lwc_parity.yml` (no CI dir exists in-repo; Phase 10
   "CI wiring" needs a home — this file is it).
2. `docs/lwc_parity_matrix.md` is created by P6-T01 (not Plan) so every wave
   exit has a file to update; per-wave row updates are in each task's
   `touches_files`.
3. Density-cap retirement is recorded in the matrix + wave result (no
   `requirements.md` edit — that file is Requirements Analyst territory; the
   Q60 record lives with the gate it governs).
4. Check-tooling findings applied: contract refs use single-colon
   `path:symbol` (the checker partitions on the first colon); `read_files`
   names only files existing at graph time (later tasks read earlier outputs
   at runtime — noted in their `why` where relevant); new files live in
   `touches_files` as pure-output (checker WARNs, accepted).

## Pack-fix — read-visibility sweep (P6-T07…P6-T12, 2026-10-26)

Trigger: the P6-T07 report showed `ui/lwc_view.py` in `touches_files` but **not**
in `read_files` (a worker told to edit a file it was never told to read). P6-T06
hit the same gap (`services/chart_model.py`, `ui/lwc_bridge.py`,
`chart_assets/lwc/envelope.js`) and only coped by reading them unprompted.

Scope: `context.read_files` only. `touches_files`, ACs, tests, dependencies and
`status` are unchanged (T06/T07 statuses moved independently by `build_wave.py`
during this pass and were preserved, not reverted). Every pack now contains
every existing `touches_files` entry plus the shared surface it consumes, each
with a `lines` range and a `why` that marks read-only entries explicitly.
Structural defect fixed across all six: the parity matrix is edited by every
wave but was in none of their packs.

| Task | Added (beyond its previous pack) | Deliberately not added |
|---|---|---|
| P6-T07 | `lwc_view`, `lwc_bridge`, `envelope.js`, `chart_model` (71-134, index↔ts), `chart.js` (bindKeyboard/focus DG92, channel), matrix | `chart.html` (27 lines, not writable here — controls must be built by `interaction.js` at runtime), `chart_view.py` (protocol unchanged); `drawing_overlay.py` **removed** — its 926 lines are the rendering surface T09 owns; the TR-4/7 draft semantics are in the frozen router table |
| P6-T08 | `lwc_view`, `lwc_bridge`, `envelope.js`, `studies.js` (channel/module precedent), matrix | `chart_model` (alarms are price-keyed, no ts mapping), `chart.js` (the module binds a chart handle) |
| P6-T09 | `lwc_view` incl. 81-140 (ts→index helpers), `chart_model`, `studies.js`, matrix; `chart_panel` re-pointed 726-830 (mapping authority) | `envelope.js` / `lwc_bridge` (the studies precedent states the pinning; the emit pattern is in `lwc_view`) |
| P6-T10 | `lwc_view`, `chart_model`, `studies.js`, `gap_vix_service` (gap/VIX results), `ict_overlay` (ICT geometry/colours), matrix; `chart_panel` re-pointed to the overlay call sites | `envelope.js` (redundant with `studies.js`'s header), `chart.js`, the style-only `session_overlay`/`vix_overlay` |
| P6-T11 | `lwc_view`, `lwc_host` (per-pop-out host), `chart_view` (factory seam), `config/settings.py:MAX_POPOUTS`, matrix | `chart_panel` (replaced in the re-host by `chart_view`) |
| P6-T12 | `chart_view` (pyqtgraph-default assertion), `lwc_host` (vendored tree/ndt://), `chart.html`, `pytest.ini` (webengine marker), matrix | `main.py` **removed** (entry point already named by the spec; zero decision value) |

Budget exceptions (per the ~8-file rule): **P6-T07 = 9** (XL: four
control/mirror references + the frozen router table + four shared surfaces +
matrix) and **P6-T10 = 9** (four overlay families + markers in one approved M
wave; the family data shapes would otherwise be a silent gap). No pack exceeds
9. Residual, not fixed here: family-specific pyqtgraph renderers beyond those
listed (e.g. `vix_overlay`, `session_overlay`) — the data-shape source is in
the pack; if a worker names one, that is a thinner-than-this-sweep pack, not a
scope change.

## Escalations / flags

None. No `routed_to: TASK_MANAGER` open entry (0 open escalations);
`requirements.md` D47 unambiguous as written (Q60 answered-by-default YES,
Q61–Q63 owner-confirmed); no architecture decision missing (S51–S60 +
frozen interfaces settle seam, model, envelope, gates, fence).
