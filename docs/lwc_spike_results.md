# Phase 0 LWC spike results + go/no-go record (P6-01)

Throwaway spike lives in `spikes/lwc/` (`README.md`, `index.html`,
`spike_probe.py`). Nothing under `spikes/` is imported by production or
tests and nothing there ships in the bundle. Static contract check:
`python3 spikes/lwc/spike_probe.py` → `SPIKE-PROBE-OK` (plain stdlib,
no Qt/DB). This doc is the evidence record the P6-12 cutover gate holds.

## Per-behaviour evidence (9/9)

### B1 — Chart creation inside a Qt `QWebEngineView` host (offline)
Evidence: `spikes/lwc/index.html` §B1 — `LightweightCharts.createChart(el,
{layout, rightPriceScale})` against the offline file URL. The real host
(`QWebEngineView` + deny-default interceptor + `ndt://` scheme) lands in
P6-04; Phase 0 proves the creation call shape only.

### B2 — Candlestick series + `setData` history render
Evidence: `index.html` §B2 — `addCandlestickSeries({priceFormat})` +
`setData()` of a 120-bar OHLC array. History path for `update_chart`.

### B3 — Live forming-bar tick via `series.update`
Evidence: `index.html` §B3 — `candles.update({time, open, high, low,
close})` with no second `setData`. Matches the D28.4 live-layer intent
(static history untouched per tick).

### B4 — Logical-index time scale + whitespace for non-trading time
Evidence: `index.html` §B4 — `timeScale().applyOptions({timeVisible})` +
`barSpacing`/`rightOffset`; nights/weekends absent from the data array
render as whitespace. This is the `gap_is_non_trading` authority surface
(currently `TimeCollapseMap` display-x).

### B5 — Custom timezone tick formatting (ET)
Evidence: `index.html` §B5 — `localization.timeFormatter` applying
`TZ_OFFSET_S = 18000` (EST), mirroring `ChartPanel` `tz_offset` semantics
(`utcfromtimestamp(ts - utcOffset)`). EDT (14400) is a constant change.

### B6 — Multi-pane layout v5 (price + volume + oscillator)
Evidence: `index.html` §B6 — `addHistogramSeries` (volume) +
`addLineSeries` (oscillator) with distinct `priceScaleId`s + `chart.panes()`.
Mirrors the current price/volume/osc splitter stack.

### B7 — Crosshair subscription + series markers
Evidence: `index.html` §B7 — `subscribeCrosshairMove(handler)` +
`setMarkers([{time, position: 'belowBar', shape: 'arrowUp', text: 'DIV'}])`.
Carries the D38 event-marker and alarm-line surface into P6-08/P6-10.

### B8 — Price lines + drawing primitives
Evidence: `index.html` §B8 — two `createPriceLine` calls (alarm red dashed,
zone-top green solid, `axisLabelVisible`). Full drawing-primitive library
(ts-to-fractional-index) is P6-09 work; Phase 0 proves the primitive exists.

### B9 — Batched bridge protocol `{v:1, ops:[]}`
Evidence: `index.html` §B9 — `bridgeBatch = {v:1, ops:[setData, update,
priceLine]}` envelope plus the documented Python-side contract
(queue-until-ready, ~33ms coalesce, replay after
`renderProcessTerminated`, backpressure counters). `LwBridge` lands P6-04.

## Measured `.app` size delta (measure-first, Q61/A109/DG89)

- Bundle baseline (measured 2026-10-26, this machine): `dist/NDThinkChart`
  = **378,400 KB** (`du -sk`), onedir PyInstaller build.
- Spike payload (measured): `spikes/lwc/` = **16 KB** (3 files).
- **Delta shipped by this task: +0 KB** — the spike adds no `datas` entry
  and `NDThinkChart.spec` is untouched (outside this task's footprint).
- Vendored `lightweight-charts.standalone.production.js` is **not**
  downloaded in Phase 0, so no vendored-byte figure is claimed here; P6-04
  must record the vendored size the same way before the bundle absorbs it.
  No fixed size budget is invented (measure-first).

## Signing-flow finding

Current flow is spec-driven PyInstaller (`NDThinkChart.spec`, per the module
index packaging row); macOS signing/notarization covers whatever the spec
collects. Finding: **today's flow covers today's tree, and this task changes
nothing** — the spike is not referenced by the spec so there is no new
unsigned content. When P6-04 vendors the LWC standalone build plus any
Chromium-adjacent assets, they must enter the spec `datas`/collect list (or
equivalent) so the signed `.app` contains them; that wiring — and its
re-measurement — is P6-04/P6-12 work, recorded here as an open obligation,
not a Phase-0 change.

## Phase-0 perf baseline (held by the P6-12 cutover gate)

Measured 2026-10-26, host Python 3.11 on this machine (serialization side;
render-side fps baseline lands with the P6-04 webengine probe, DG88):

- 5,000-bar OHLC Python build: **1.3 ms**
- Bridge payload JSON (`{candles[5000], envelope {v:1, ops}}`): **533,265
  bytes**, serialized in **5.5 ms**
- Bridge batch envelope for a full history + 1 live tick + 1 price line:
  **3 ops** (`setData`, `update`, `priceLine`)

Gate reading: P6-12 cutover must show the LWC path moving this (or a larger)
payload end-to-end without regressing the interactive feel of the pyqtgraph
path. No fixed budget is set in Phase 0 (measure-first); these figures are
the floor the cutover evidence is compared against.

## Go / no-go verdict

**GO — Phase 1 (P6-02) may proceed.** All 9 API behaviours have a named
evidence site above and in `spikes/lwc/`; the spike is unimported and
unshipped; size delta is measured (+0 KB); the perf baseline above is the
record P6-12 holds. A no-go would have required a behaviour with no v5 API
or a spike leak into production/tests — neither occurred.
