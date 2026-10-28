# LWC parity matrix — gate skeleton (P6-01)

Rows 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17 and 19 are **Done / accepted**
as of P6-12 (row 8 as of P6-06, rows 7/13/14 as of P6-07, row 12 as of P6-08,
row 11 as of P6-09, rows 6/9/10 as of P6-10, row 15 as of P6-11, rows 16/17/19
as of P6-12 — the cutover candidate, **declared not shipped**). Rows 1, 2, 4, 5
and 18 are **Done / accepted** as of Q-8, each on the named passing test
recorded in the Q-8 reconciliation below; rows 1/2/4/5 on
the same offscreen-parity standard rows 6–17 were accepted on, and row 18 with
its real-engine interceptor cases executing instead of skipping. **Rows 1 and
2 were re-proven on 2026-10-26 by Q-19**: that Q-8 evidence bypassed the
transport (envelopes were injected with `window.lwApplyOps`), so it did not
prove the shipped path. `tests/test_lwc_e2e_data.py` now drives the real view,
the real `QWebChannel` page and the real `update_chart`, and reads
`window.lwSnapshot().candles.length` through `runJavaScript` — history in all
five modes (row 1) and the live forming bar with no history rebuild (row 2).
**Row 3 is
Done / accepted as of Q-9**, on the named node suite
`chart_assets/lwc/volume_scale.test.js` (run by `node --test
chart_assets/lwc/`): the D21.2/AC-D21.2.1 ceiling — `1.10 ×` the visible max,
the `100` floor, Y minimum `0` — is ported to the LWC volume pane through the
series' `autoscaleInfoProvider`. **No row remains Open / pending.** A row
moves to Done/accepted only with its gate evidence; **a row regressing without
an escalation fails review (rule 10)**. No soak: the triple gate (owner
acceptance + full parity + Phase-0 perf) stands in for it (S59). Phase waves per
`docs/plan.md` § Phases (P6-01→P6-13).

| # | Row | pyqtgraph reference (today) | LWC target | Gate wave | Disposition |
|---|---|---|---|---|---|
| 1 | Candlestick history render (all 5 modes) | `CandlestickItem.set_data` | v5 candlestick series + `setData` | P6-05 | Done / accepted |
| 2 | Live forming-bar tick (no history rebuild) | live candle/volume layers (D28.4) | `series.update` per tick | P6-05 | Done / accepted |
| 3 | Volume pane (linear Y, nice ceiling, floor 100) | `_nice_volume_max` family (D8/RG-002) | histogram series + ceiling port | P6-05 | Done / accepted |
| 4 | Time axis + whitespace for non-trading time | `TimeCollapseMap` display-x (D21.4) | logical index + absent-data whitespace | P6-05 | Done / accepted |
| 5 | Timezone display (ET, DST-correct) | `tz_offset` axes (EST 18000 / EDT 14400) | custom `timeFormatter` | P6-05 | Done / accepted |
| 6 | Session shading bands (RTH/ETH) | `SessionOverlay` + `session_bands` | overlay/marker port | P6-10 | Done / accepted |
| 7 | Crosshair + price/time chips | `_update_crosshair`, D2/Q33 lane | library-native crosshair (Q63/A108) | P6-07 | Done / accepted |
| 8 | Studies (SMA/EMA/VWAP/BB/RSI/MACD) + cache | `indicator_service` + `_StudyCache` | shared model + LWC overlays | P6-06 | Done / accepted |
| 9 | Gap / VIX / ICT overlays | `RthGapOverlay`, `VixOverlay`, `ICTStudyOverlay` | LWC overlay port | P6-10 | Done / accepted |
| 10 | Event markers (dividends/earnings/splits) | `EventMarkerOverlay` (D38) | `setMarkers` port | P6-10 | Done / accepted |
| 11 | Drawings (all tools + D11 labels + D12/D15 dialogs) | `DrawingOverlay` | primitives lib (ts-to-fractional-index); Qt dialogs stay | P6-09 | Done / accepted |
| 12 | Alarms (lines, placement, preview) | `AlarmOverlay` + preview line (D21.10) | alarm lines on LWC; Qt dialogs stay | P6-08 | Done / accepted |
| 13 | Mouse router TR-1…TR-17 + JS mirror | `ChartMouseRouter` (frozen contract) | Python router + JS mirror (mirror never reinterprets) | P6-07 | Done / accepted |
| 14 | Zoom/magnifier + reset + volume toggle + controls | `ZoomOverlay`, `ChartControls` | in-HTML controls + Python shims | P6-07 | Done / accepted |
| 15 | Pop-out charts (cap 10, per-pop-out memory) | `popout_window.py`, `MAX_POPOUTS` (Q62/A107, DG90) | LWC views in pop-outs; memory accounted | P6-11 | Done / accepted |
| 16 | Perf parity (Phase-0 baseline holds) | perf baseline in `docs/lwc_spike_results.md` | cutover evidence vs baseline (triple gate) | P6-12 | Done / accepted |
| 17 | Bundle size + signing disposition | measured delta in `docs/lwc_spike_results.md` (Q61/A109) | vendored tree in `datas`; measured delta + signing disposition recorded | P6-12 | Done / accepted |
| 18 | Offline/airplane + deny-default network | new in P6-04 (DG88/DG91) | interceptor + offline case green | P6-04 | Done / accepted |
| 19 | pyqtgraph default retained through cutover | locked decision (D47 reversal) | pyqtgraph present + default until Phase 11 approval | P6-12/P6-13 | **Retired** (P6-T13 as-built 2026-10-28 — retention moot, nothing retained; see note above) |

Row count: 19. Dispositioned Open/pending: 0. Done/accepted: 18. Retired (retention moot post-removal): 1.

## P6-T13 as-built — parity vs deletion, separated (2026-10-28)

Source: `ui/chart_view.py::create_chart_view` always returns `LwcChartView` (verified 2026-10-28);
`NDT_CHART_ENGINE` / `QSettings chart/engine` no longer select a renderer. Removal commit `6e35b27`;
gate `docs/build/gate_P6_T13.md` (approval SATISFIED 2026-10-27; live-session sign-off **WAIVED, NOT
SATISFIED**; oracle RETIRE).

- **Feature parity (rows 1–18): unchanged, Done / accepted.** Every row keeps the named passing test
  recorded in its wave section / the Q-8 and Q-9 reconciliations above. Deleting the old engine does not
  un-prove what the LWC engine was proven to do.
- **Cutover/deletion (row 19): Retired.** Row 19 ("pyqtgraph present + default until Phase 11 approval")
  described a retention that no longer exists — nothing is retained, there is no default to hold, and Phase 11
  approval is moot. Evidence: removal commit `6e35b27`, `docs/build/gate_P6_T13.md` §2–§3, and the
  "Retired coverage" section below (the value-for-value oracle that went with the engine).
- **Waived, not satisfied, preserved.** The live-session deletion gate (AC-D47.8 / S59) stays recorded as
  waived per the gate file — no row in this matrix claims a live session validated the engine.

## Rule-10 entries — none open after Q-9

Rule 10: a row regressing without an escalation fails review. **No row is
Open / pending**, so no row needs an entry. Row 3's entry is kept below as a
**closed record** rather than deleted, so the evidence that closed it stays
next to the rule that demanded it.

- **Row 3 — closed by Q-9 (was a Rule-10 entry).** The histogram-series half
  was already green (`tests/test_lwc_time_parity.py::TestTimeParity::test_P6_T05_T11_all_modes_emit_valid_column_ops`
  and `::TestGeometryGuard::test_P6_T05_T12_volume_shares_the_price_rule`); the
  ceiling/floor half now has both a code path and a named test.
  `chart_assets/lwc/chart.js` attaches an `autoscaleInfoProvider` to the volume
  series which reads `chart.timeScale().getVisibleLogicalRange()` and prices
  `1.10 × max(volume of the visible bars)` from the snapshot the driver already
  sent (`VOLUME_NICE_FLOOR` 100 when no visible bar is non-zero, `minValue` 0 —
  `chart_model.visible_volume_ceiling` ported verbatim, ESC-028 band included).
  `chart_assets/lwc/volume_scale.test.js` proves the ceiling, the floor, the
  `0` minimum, and that the ceiling **changes** when the visible range narrows
  or pans — a static max-of-everything cannot pass. No value crosses the wire
  differently and no per-gesture round-trip to Python exists.

## Q-9 — the volume ceiling port, row 3 closed (2026-10-26)

`AC-D21.2.1` was the last unported behaviour in the matrix: the pyqtgraph
engine prices the volume pane from the *visible* x-range
(`ChartPanel._recompute_visible_volume_range` →
`chart_model.visible_volume_ceiling`), and the LWC pane had only the histogram
series plus `scaleMargins {top: 0.85, bottom: 0}`, so the library autoscaled to
whatever it decided and the `100` floor never applied.

- **The rule, ported verbatim (not the shorthand).** The ceiling is
  `1.10 × max(volume of the bars in the currently visible range)`; it falls back
  to `VOLUME_NICE_FLOOR` (100) only when **no** visible bar is non-zero (none
  visible, or every visible bar zero), and the Y minimum is always 0 (D21.1).
  The small positive band `0 < visible_max ≤ 90.9` keeps the literal
  `1.10 × max` (10 → 11, 50 → 55) per **ESC-028** — a second unconditional
  `< 100` clamp would be a regression, and the suite asserts that band
  explicitly.
- **Engine-side, recomputed on every autoscale.** `chart_assets/lwc/chart.js`
  attaches an `autoscaleInfoProvider` to the histogram series. It reads
  `chart.timeScale().getVisibleLogicalRange()` and scans the volume snapshot the
  driver already sent (the `ts` column is the logical index), so load, pan and
  zoom re-price inside the page — no op, signal or bridge call to Python was
  added, and the bar transport's series set is untouched. The price pane's
  autoscale, the `scaleMargins` pane split and the library's `barSpacing`
  behaviour are unchanged; the K/M tick formatting surface is untouched.
- **`ui/lwc_view.py` unchanged on the wire.** `build_series_ops` keeps shipping
  the raw `Bar.volume` values — the ceiling is a render-time decision made from
  them, so nothing is reformatted or pre-clamped on the way in (JS still
  receives numbers, per the renderer-only boundary).
- **Gate evidence.** `chart_assets/lwc/volume_scale.test.js` — 18 cases:
  `1.10 ×` the visible max per window, ceilings that **change** when the range
  narrows *and* when a fixed-width window pans (a static max-of-everything
  fails), the `100` floor for empty / all-zero / whitespace-only windows,
  `minValue` 0 in every case, the ESC-028 small band, fractional and reversed
  ranges, non-finite/negative rows ignored, plus a source assertion that exactly
  one `autoscaleInfoProvider` exists and it is the volume series' reading the
  live logical range. `node --test chart_assets/lwc/` = **43/43**.
- **Gate-harness repair, recorded because it changed what the command runs.**
  `node --test chart_assets/lwc/` resolves a directory through `package.json`'s
  `main`; that entry pointed at `envelope.test.js`, so the documented command
  ran **only the envelope suite (10 tests)** and the core-chart suite sat
  outside it — the P6-05…P6-12 "node 10/10" lines record that envelope-only
  run. `chart_assets/lwc/all.js` now loads every suite and is the `main`
  entry: the same command runs 43 tests (15 core-chart + 10 envelope + 18
  volume). Each suite remains runnable on its own file, and
  `tests/test_lwc_time_parity.py`'s explicit `chart.test.js` invocation is
  unaffected.
- Row 3 moves to **Done / accepted**; no Done row regressed. **19 Done / 0
  Open.**

## Q-19 — real-transport e2e: rows 1 and 2 re-proven (2026-10-26)

The LWC engine rendered a page but received no bars. Five independent causes,
each sufficient on its own, verified against the tree before fixing:

- **S3a layout.** `ui/lwc_view.py::ensure_host` built the `QWebEngineView`
  with `parent=self` but never added it to a layout, and neither module had a
  `resizeEvent`; the host kept Qt's default size. **Measured pre-fix:
  host 100x30 and `#chart` clientWidth/clientHeight 100x30 inside a 950x850
  view.** Fix: one zero-margin, zero-spacing `QVBoxLayout` owned by
  `LwcChartView`, with the host added once in `ensure_host` (every pop-out view
  owns its own, so the same change covers them). **Measured post-fix: view
  950x850 → host 950x850 → `#chart` 950x850** (`tests/test_lwc_host_layout.py`).
- **S3b subscription.** `chart_assets/lwc/chart.js::bindChannel` only assigned
  `window.lwBridge`; nothing subscribed to a bridge signal, so `applyOps` was
  reachable only from tests through `window.lwApplyOps`. Fix: inside the
  `QWebChannel` callback the page connects `opsJson`, `JSON.parse`s +
  `applyOps`, `console.warn`s a returned error and `console.error`s a throw.
- **S3c payload.** `LwBridge.opsEmitted(dict)` reaches a JS slot as a Python
  repr string (`{'v': 1, ...}`), which is not JSON and fails the page's
  envelope check. Fix: `opsJson = pyqtSignal(str)` emitted beside every
  `opsEmitted` crossing (flush and replay) with
  `json.dumps(env, separators=(',', ':'), allow_nan=False)`. **Measured
  33,000-bar replay on this machine: 1,411,535 bytes / 13.4 ms in
  `json.dumps` (13.6 ms for the whole `handle_page_ready` replay)** — no
  chunking or `runJavaScript` fallback needed.
- **S3d readiness race.** `_on_load_finished` replayed the op log before
  `QWebChannel`'s JS half existed, so the replay had no listener. Fix:
  `@pyqtSlot() pageReady` on `LwBridge` owns the drain + replay; the page
  calls it after subscribing, and `_on_load_finished` no longer replays.
- **S3e page→Python.** No `pyqtSlot` existed anywhere on the bridge; the
  page's `focusReleased()` call (the only page→Python call in the JS assets —
  `chart.js::bindKeyboard` and `interaction.js::releaseFocus` both target it)
  was silently dropped. Fix: `@pyqtSlot() focusReleased` re-emits
  `pageFocusReleased`, which the view connects to its existing
  `handle_focus_released` / `focusRoundTrip` controller signal; the host's Esc
  signal is connected to the same handler.

**Gate evidence.** `tests/test_lwc_e2e_data.py` — real `LwcChartView`, real
`ensure_host`, real `update_chart(bars)`, then
`window.lwSnapshot().candles.length` read through `runJavaScript` and asserted
equal to the plotted bar count. No `host.resize`, no `lwApplyOps`, no envelope
captured in Python. It **fails on the pre-Q-19 tree** (the snapshot stays
empty: no subscription, replay raced the handshake) and passes after the fix.
It also re-proves row 1 across all five modes (the page reports each mode
through the transport) and row 2 (an intra-bar tick changes the close with the
count unchanged; a new period appends exactly one candle).
`tests/test_lwc_host_layout.py` covers S3a structurally and by measurement.
`tests/test_lwc_bridge.py` stays green beside them.

Rows 1 and 2 remain **Done / accepted**, now on transport-crossing evidence
rather than injected envelopes. No row regressed; **19 Done / 0 Open.**



### P6-12 — Phase 10 packaging + CI + cutover candidate (2026-10-26)

- **The cutover candidate is declared, not shipped.** `NDT_CHART_ENGINE` unset
  or unknown still resolves to pyqtgraph through
  `ui/chart_view.create_chart_view`, so pyqtgraph remains present and the
  **default** engine; the LWC view is still the opt-in value, and **no
  pyqtgraph code was deleted** — the P6-13 deletion set is untouched
  and every retained engine module still exists (`ui/chart_panel.py`,
  `ui/candlestick_item.py`, the overlay/controls/router/pop-out modules). The
  removal wave stays separately owner-gated: explicit approval after one live
  trading session with no engine defect (AC-D47.8, S59), never riding along
  with cutover. No soak: the triple gate (owner acceptance + full parity +
  Phase-0 perf) replaces it, and the owner-acceptance leg is on record as
  Q61/A109 (measure-first, no fixed budget) plus the no-soak decision.
- **Bundle wiring, both specs.** `NDThinkChart.spec` and
  `packaging/build.spec` now carry `('chart_assets/lwc', 'chart_assets/lwc')`
  in `datas` — the whole vendored v5.2.1 tree (14 files) that the offline page
  resolves through `ndt://lwc/` (`ui/lwc_host.ASSET_DIR` is the same tree),
  including `chart.html`, the vendored
  `lightweight-charts.standalone.production.js`, `chart.js`, `envelope.js`, the
  channel modules, the `VERSION` pin and `ATTRIBUTION.md`. Both specs also
  name `PyQt6.QtWebEngineCore` / `PyQt6.QtWebEngineWidgets` /
  `PyQt6.QtWebChannel` in `hiddenimports`, so PyInstaller cannot prune the
  host/bridge (or the Chromium runtime they pull) from the app; `pyqtgraph`
  stays in the packaged spec's imports.
- **Measured `.app` size delta (measure-first, Q61/A109/DG89) — the number the
  owner's budget decision starts from.** Bundle baseline unchanged from P6-01:
  `dist/NDThinkChart` = **378,400 KB** (`du -sk`, onedir PyInstaller build on
  this machine, re-measured 2026-10-26). The vendored tree the `datas` entry
  now absorbs = **338,928 bytes across 14 files (331.0 KB of file data; 428 KB
  as allocated on disk)**, i.e. **+0.09 %** of the bundle (378,400 → 378,731 KB
  by file bytes). **The QtWebEngine/Chromium term is now measured:** on
  2026-10-26 `PyQt6-WebEngine` **6.11.0** was installed (owner-approved; owed
  by plan Phase 2.1), so `HAS_WEBENGINE` is True and the wheel's frameworks
  exist on this machine. Method: `du -sk` over the frameworks the wheel installs
  into `.venv/lib/python3.11/site-packages/PyQt6/Qt6/lib` —
  `QtWebEngineCore.framework` **291,972 KB (285 MB)**, `QtQml.framework`
  **4,688 KB (4.6 MB)**, `QtWebEngineQuick.framework` **724 KB**,
  `QtPositioning.framework` **584 KB**, `QtPrintSupport.framework` **476 KB**,
  `QtWebChannel.framework` **272 KB**, `QtWebEngineWidgets.framework`
  **216 KB** = **298,932 KB ≈ 292 MB**. Against the 378,400 KB baseline that is
  **+79 %** (369.5 MB → ~661 MB), before PyInstaller's own
  compression/packing. That packed contribution is still **unmeasured** — no
  build has been produced with the wheel present, so the shipped `.app` delta
  will differ from this raw on-disk sum and must be re-measured from a build;
  no number is invented for it. **No fixed size budget is set** (the P6-01
  record's "no fixed size budget" stands; this wave only adds measurement, and
  the owner sets the budget from this figure).
- **Signing-flow disposition.** Today's flow is spec-driven PyInstaller with
  `codesign_identity=None` and `entitlements=None` in both specs — an
  ad-hoc/unsigned development bundle, with no notarization step anywhere in the
  repo. The vendored tree changes nothing about that: it adds only text/web
  assets (`.js`, `.html`, `.json`, `.md`, `VERSION`), which any signature over
  the bundle covers. QtWebEngine's Chromium runtime is the change that matters:
  it brings **nested Mach-O binaries**, so a signed distribution will need
  nested-code signing plus hardened-runtime entitlements (JIT / unsigned
  executable memory) that the spec does not set today. That obligation is
  recorded, not guessed: no identity, entitlement set or budget is invented
  here, and no signing step is added this wave.
- **CI wiring (`.github/workflows/lwc_parity.yml`).** macOS runner, Python
  3.11, Node 22, job-level `QT_QPA_PLATFORM=offscreen`. Steps: the cutover gate
  suite (`tests/test_lwc_cutover_gate.py`), the offscreen suite
  (`-m "not webengine"`), a dedicated `-m webengine` step that fails only if a
  webengine case is red (skips stay skips, DG88/AP-P6-4), `node --test
  chart_assets/lwc/`, and the parity-matrix row-count gate (19 rows, all
  numbers 1–19 present).
- **Phase-0 perf holds (re-measured 2026-10-26, host Python 3.11).** 5,000-bar
  OHLC Python build **0.84 ms** against the 1.3 ms Phase-0 floor; the
  column-array history envelope serializes in **3.1 ms** (248,880 bytes for
  this fixture) against the 5.5 ms floor. The Phase-0 record itself is
  unchanged (`docs/lwc_spike_results.md` still holds 1.3 ms / 533,265 bytes /
  5.5 ms) — the floors are pinned by the gate suite, so relaxing them fails
  review. The render-side fps half still rides the engine-box checklist
  (rows 1–5/18 rule-10 entries).
- **Renderer-only boundary held.** No file under `ibkr/`, no DB schema or
  store API, no service signature, no watchlist/dock/persistence surface and
  no order surface was created, modified or reintroduced by this wave: the
  change set is the two PyInstaller specs, the CI workflow, this matrix and the
  gate suite. JS still receives timestamps and prices only (no channel changed
  in this wave), and the bundle change is asset shipping, not a wire contract.
- Gate evidence: `tests/test_lwc_cutover_gate.py` (spec `datas`/`hiddenimports`
  parsed from source, offline asset canary, measured-delta + signing
  disposition, structurally validated CI workflow, 19-row matrix with rule-10
  coverage and count-line agreement, candidate declared/not shipped, env
  unset/unknown → pyqtgraph, pyqtgraph modules present, Phase-0 perf floor
  pinned and met, deletion-set + backend residue scan) +
  `.github/workflows/lwc_parity.yml` + `node --test chart_assets/lwc/`.
  Rows 16/17/19 move to **Done / accepted**; no Done row regressed; 6/19 remain
  Open / pending, each with its rule-10 entry. (Superseded by the Q-8
  reconciliation above: 18 Done / 1 Open, row 3 alone.)

## Q-8 reconciliation — each disposition against a named passing test (2026-10-26)

The stale six were reconciled one row at a time, never as a block. Evidence
command per row: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
tests/test_lwc_time_parity.py -q` (15 passed) and `... tests/test_lwc_bridge.py
-q` (21 passed), plus `node --test chart_assets/lwc/`.
`PyQt6-WebEngine` is installed in this venv (Q-7), so the
`@pytest.mark.webengine` cases **execute**: `pytest tests/test_lwc_bridge.py -m
webengine -q` is 3 passed / 0 skipped.

- **Row 1 — Done / accepted.** `test_lwc_time_parity.py::TestTimeParity::test_P6_T05_T11_all_modes_emit_valid_column_ops`
  proves all five modes emit valid candle/volume column ops (the per-mode series
  set), and `...::TestGeometryGuard::test_P6_T05_T12_node_chart_suite_is_green`
  runs the node suite that pins the per-mode registry / `describeOp`.
- **Row 2 — Done / accepted.** `...::TestTimeParity::test_P6_T05_T11_live_update_advances_the_forming_bar`
  proves a same-`ts` tick crosses as one-element `update_bar` ops on candles +
  volume (count unchanged, close/volume applied) and a new-`ts` bar grows the
  series by exactly one — no history rebuild.
- **Row 3 — Open / pending.** Only the histogram payload is proven by
  `...::test_P6_T05_T11_all_modes_emit_valid_column_ops` and
  `...::TestGeometryGuard::test_P6_T05_T12_volume_shares_the_price_rule`; no
  named test and no code path proves the ceiling/floor. See its rule-10 entry
  above — the missing half is the port itself.
- **Row 4 — Done / accepted.** `...::test_P6_T05_T11_within_session_hole_is_whitespace`
  proves the logical index + one 3-slot whitespace run for the midday hole (both
  `ext_hours` modes) and `...::test_P6_T05_T11_session_boundary_collapses_both_modes`
  proves the weekend collapse/keep split via `gap_is_non_trading` agreement.
- **Row 5 — Done / accepted.** `...::test_P6_T05_T11_tz_labels_equal_t_minus_offset_per_mode`
  proves the EDT/EST `t - offset` labels per mode and
  `...::test_P6_T05_T11_dst_fold_stays_continuous` proves the 2026-11-01 fold
  stays continuous rather than losing or duplicating a bar.
- **Row 18 — Done / accepted.** `test_lwc_bridge.py::test_interceptor_wired_blocks_non_ndt`
  now runs against the **real** engine (not a skip): `ndt://lwc/chart.html` is
  allowed and every non-ndt URL is blocked (deny-default, zero non-ndt allow
  verdicts); `::TestOfflineInterceptor::test_airplane_run_no_network_surface`
  proves no remote/network surface; `::test_host_loads_ndt_chart_offline` and
  `::test_render_terminated_recovery_wired` execute on Chromium; and
  `::TestReplayIdentity::test_replay_identity_no_dup_no_loss` proves the full
  op-log replay after `renderProcessTerminated` has no duplicate and no lost
  bar.

Rows 1, 2, 4 and 5 are accepted on the named offscreen parity tests — the same
standard rows 6–17 were accepted on; their rendered-surface confirmation rides
the cutover gate's manual checklist, not a row-specific blocker. Row 18's
real-engine interceptor case is no longer a skip and passes against Chromium's
own request dispatch. Row 3 is deliberately not flipped: its ceiling/floor half
is a port that does not exist, and the count line above (19 / 1 / 18) is derived
from the table. The P6-05 "Rows keep Open / pending" and P6-12 "6/19 remain
Open / pending" statements describe those waves; after Q-8 the matrix state is
**18 Done / 1 Open**.

## Wave exit notes

### P6-11 — Phase 9 pop-outs (2026-10-26)

- **Pop-outs re-host on the resolved engine.** `ui/popout_window.py` builds its
  read-only view through `ui.chart_view.create_chart_view` (the single engine
  selection authority: env, then the persisted override; anything but `"lwc"` →
  pyqtgraph, still present and **default**). The factory's LWC branch is still
  the Phase-1a seam stub, so on `"lwc"` the pop-out re-hosts the real driver
  (`ui/lwc_view.py`) — the same composition the phase suites use. The pop-out
  keeps D24's read-only contract on both engines: `editable=False`, no drawing
  tool, alarm placement inert (`set_alarm_mode` → IDLE), router IDLE.
- **One session fan-out, main chart the sole writer.** The LWC driver gained the
  session-facing surface the fan-out already calls: `update_chart` (the
  `ChartPanel` spelling of `update_bars`) and a `drawing_overlay` proxy whose
  single entry point, `set_data(symbol, drawings, groups)`, maps onto
  `set_drawings`. `ui/ticker_session.py` and `data/popout_store.py` are
  **untouched** — bars, live ticks, studies, drawings and alarms reach 1/3/6
  pop-outs through exactly the D24 path, and the RT subscription stays
  refcounted to one reqId per symbol.
- **Per-pop-out memory accounted (DG90).** Every window holds a ledger entry
  (`POPOUT_MEMORY_LEDGER`, keyed by pop-out serial) with its own buckets —
  private series copy, plotted/logical columns, study value arrays, drawing and
  marker wire items, and the bridge replay log (the one structure that grows
  with traffic). Totals are per window and aggregate
  (`popout_memory_total()`), never a single opaque number. On close the entry is
  dropped and the LWC view's arrays/logs are released
  (`LwcChartView.release_resources`) — no pop-out's state outlives its window.
- **Cap stays 10 (Q62/A107).** `MAX_POPOUTS = 10` unchanged; the refusal lives in
  `MainWindow._open_popout` **before** the window (and therefore the engine
  view) is constructed, so neither engine can bypass it — the 11th request gets
  the same `Pop-out limit reached (10). Close one to open another.` status line
  and constructs nothing.
- **Persistence semantics unchanged.** `PopoutStore` keeps its four-entry API
  and signature (save on open, delete on close, geometry on move/resize end,
  restore on connect); only the view behind the header changed.
- Renderer-only boundary held: no `ibkr/` file, DB schema/store API, service
  signature, watchlist/dock surface or order-code path was created, modified or
  reintroduced; JS still receives timestamps and prices only (none of the
  P6-05…P6-10 channels changed).
- Gate evidence: `tests/test_lwc_popouts.py` (1/3/6 LWC pop-outs open → sync
  bars/studies/drawings/alarms → close with per-pop-out accounting and release;
  cap 10 asserted and the 11th refused on **both** engines with no view
  constructed; residue/AST scan of sessions, persistence, settings and the
  renderer boundary) + `tests/test_d24_popouts.py` green unmodified. Row 15
  moves to **Done / accepted**; no Done row regressed, 9/19 remain
  Open / pending.

### P6-10 — Phase 8 overlays + event markers (2026-10-26)

- **Four overlays, one axis, unchanged services.** `ui/lwc_view.py` gained
  `set_overlay(name, regions)` for `session` / `rth_gaps` / `vix_sd` / `ict`
  and `set_event_markers(events)`. Every value comes from the **unchanged**
  service the default engine calls — `services.session_service.session_bands`,
  `services.gap_vix_service.calculate_rth_gaps` /
  `calculate_vix_standard_deviation` (+ `infer_ticker_context`) and
  `services.ict_service.calculate_ict_concepts`, with the ICT trailing window
  from `chart_model.trailing_bars` — and every position from the same
  display-x authority, mapped into the candles' **fractional logical index**,
  so a band lands on the identical bar on both engines
  (`display_from_fractional_index` is the inverse of the reference overlays'
  `_index_to_x` / `_ts_to_x`).
- **The reference visuals, value-for-value.** Session: the orange pre / blue
  post bands at 10 % alpha, z -10, gated exactly as `_render_sessions` (no
  extended hours, no `1 day`, empty load). RTH gaps: one band per staircase
  step, the `#089981` / `#f23645` borders, the darker `#064e3b` / `#7f1d1d`
  brushes at the 0.55 (open) / 0.32 (fully filled) alpha, 0.8 px border dotted
  once filled, z -5, clamped to the last bar. VIX: one line per sigma level
  with its colour, style and width, right-edge labels at the last bar's
  display-x, z 0. ICT: market structures (dashed 1.2 px, z 3), order blocks
  (0.18, z -3, breaker colour), fair value gaps (0.14 / 0.06 mitigated, dotted
  when broken, z -4), liquidity pools (0.07, z -6) with their level segments
  (z -2), volume imbalances (±1 index window, 0.35, z -4), opening gaps (0.10,
  z -5) with dotted midpoints (z -2), displacements (z 4) and killzones (z -8).
- **Markers (D38 `setMarkers` port).** Dividends/earnings/splits render from
  the unchanged event records, keyed by **event id** (a date correction moves
  the marker instead of duplicating it), positioned by the reference rule (the
  first bar on/after the event date; one bar past the last bar for a future
  event), z 10, anchor `(0.5, 1.0)`, plus the countdown label naming the next
  upcoming event (`Earnings in 3d`, `Split today`) and the explicit
  `Event data unavailable` state.
- **Numbers cross; glyphs and labels are composed engine-side.**
  `chart_assets/lwc/overlays.js` mirrors every reference constant table
  (`EVENT_STYLE`, the session/gap/VIX/ICT style tables) and composes the VIX
  sigma labels, the D38 glyphs/tooltips and the countdown wording itself. The
  wire carries fractional indices, prices and raw event fields — no timestamp,
  no formatted label. Both channels travel on their own envelopes
  (`overlayOpsEmitted` / `markerOpsEmitted`), never on the bar transport,
  which stays pinned to candles/volume.
- **Cutover wiring, as for studies/interaction/alarms/drawings.** Including
  `overlays.js` in `chart.html` and forwarding the two signals are page/host
  wiring at cutover; the parity itself is engine-agnostic (node + Python, no
  Chromium needed), which is why rows 6/9/10 carry green gate evidence now.
- Gate evidence: `tests/test_lwc_overlays.py` (constant parity against every
  reference module, session/gap/VIX/ICT geometry compared value-for-value
  against the shipped overlays on shared fixtures, marker positions + glyphs +
  tooltips + countdown against `EventMarkerOverlay`, the reference gating
  cases, replay/clear identity, the renderer-only residue + AST import
  boundary + no-timestamp scan + bar-transport isolation) + `node --test
  chart_assets/lwc/`. Rows 6/9/10 move to **Done / accepted**; no Done row
  regressed, 10/19 remain Open / pending.

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

## Retired coverage (P6-T13, 2026-10-27)

The owner retired the oracle rather than freezing golden fixtures: cases whose
expected value was computed by the deleted pyqtgraph implementation are gone, not
skipped. Recorded here so the 19/19 rows above are not read as protection that no
longer exists.

| Area | What was lost |
|---|---|
| Drawing geometry | value-for-value comparison against `DrawingOverlay._ts_to_x`; fibre/zone/measure coordinate parity |
| Alarm rendering | overlay pen/dash styling, line-item labels, pop-out drag/menu guards |
| Overlay geometry | session bands, RTH gaps, VIX levels, ICT shapes compared against the shipped overlays |
| Volume affordance | the D21-08 strike-through toggle and the D10 hide/splitter restore |
| Candle rendering | density-cap, wick, DPI and crosshair-chip suites (engine-specific by nature) |
| D38 markers | per-type colour and "Split in 4d" text assertions |
| Dock geometry | fixed-pixel convergence cases that relied on the pyqtgraph price-panel minimum width |

**Still guarded independently:** the LWC e2e transport tests, the time-axis and
whitespace tests, the studies/alarms/drawings envelope tests, the removal gate
(`tests/test_lwc_removal_gate.py`), and the full suite.
