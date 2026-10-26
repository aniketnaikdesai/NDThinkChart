# Phase 0 LWC spike (THROWAWAY — `spikes/lwc/`)

> **Never import this directory from production or tests.** No module under
> `ui/`, `ibkr/`, `services/`, `data/`, `config/`, `main.py` or `tests/`
> may reference `spikes/`. This directory is excluded from packaging
> (no `NDThinkChart.spec` `datas` entry — nothing here ships in the `.app`).
> It exists for exactly one purpose: prove the 9 Lightweight Charts v5 API
> behaviours Phase 1–10 depend on, then get deleted or left to rot.
> Allowed by the D47 locked decision as the single no-prototype exception.

## What it proves (the 9 API behaviours, B1–B9)

| # | Behaviour | Later phase | Demonstrated in |
|---|---|---|---|
| B1 | Chart creation inside a Qt `QWebEngineView` host, offline file URL | P6-04 | `index.html` §B1 + results doc |
| B2 | Candlestick series `addCandlestickSeries` + `setData` history render | P6-05 | `index.html` §B2 |
| B3 | Live forming-bar update via `series.update` (no full `setData`) | P6-05 | `index.html` §B3 |
| B4 | Logical-index time scale + whitespace gaps for non-trading time | P6-05 | `index.html` §B4 |
| B5 | Custom timezone tick formatting (`tickMarkFormatter`, ET display) | P6-05 | `index.html` §B5 |
| B6 | Multi-pane layout v5 (price + volume + oscillator panes) | P6-05 | `index.html` §B6 |
| B7 | Crosshair-move subscription + series markers (event/alarm surface) | P6-06/08/10 | `index.html` §B7 |
| B8 | Price lines + drawing primitives (alarm/drawing overlays) | P6-08/09 | `index.html` §B8 |
| B9 | Batched bridge protocol `{v:1, ops:[]}`: queue-until-ready, ~33ms coalesce, replay, backpressure counters | P6-04 | `index.html` §B9 + `spike_probe.py` |

## How to view

```sh
# static only — no server, no Qt, no DB needed:
open spikes/lwc/index.html            # or: python3 -m http.server
# static contract check (plain python, no Qt/DB imports):
python3 spikes/lwc/spike_probe.py
```

`index.html` ships a **call-shape stub** of the v5 API (`window.__lwcCalls`
recorder) because Phase 0 vendors nothing and downloads nothing; the demo
script issues the real v5-shaped calls (`createChart`, `addCandlestickSeries`,
`setData`, `update`, `applyOptions`, `setSeriesMarkers`, `createPriceLine`,
`subscribeCrosshairMove`, …) so the shapes Phase 1–10 will rely on are on
record. Swapping the stub for the vendored `lightweight-charts.standalone.production.js`
is a one-`<script>`-tag change and is explicitly a Phase-2 (P6-04) job.

## Fence

```sh
! grep -rn "spikes" --include="*.py" ui ibkr services data config main.py
```

must print nothing (exit 0 via the negation). `tests/` holds no spike suite.
