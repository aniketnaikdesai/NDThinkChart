# Delta: What the `NDThinkChart` Repo Audit Added to the Implementation Plan

This document isolates everything that changed in the implementation plan **because
of reviewing `github.com/aniketnaikdesai/NDThinkChart`**, separate from the earlier
`ibapi`-vs-`ib_insync` and TWS-vs-Gateway corrections (which came from your answers,
not the repo). Use this as a quick "what's new and why" reference alongside the full
plan.

---

## 1. What the repo turned out to be

A **Vite + React 19 + TypeScript** single-page app (Tailwind, `lightweight-charts`
for charting, `lucide-react` icons) — **no backend, no broker connection**. All
market data is procedurally generated (`services/marketData.ts`: a hardcoded ticker
list and a synthetic candle generator). It's a **UI/UX and business-logic spec**,
not code to run as-is. Every behavior in it needs re-expressing in PyQt6 +
pyqtgraph + real `ibapi` data.

This matters because it reframed the task: the architecture doc alone described a
fairly generic ToS-style chart (candles, volume, zones, one alarm overlay, basic
SMAs). The repo revealed a much larger, more specific feature set was actually
wanted.

---

## 2. File → Python module map

| Repo file | What it does | Python equivalent |
|---|---|---|
| `App.tsx` | Top-level state/orchestration wiring every panel together | `ui/main_window.py` |
| `components/TitleBar.tsx` | Custom window chrome + **demo-only** mock-data controls (streaming on/off, stream speed, "flash spike", "reset data") | **Not ported** — these only exist to drive the fake data generator. Native macOS window chrome used instead. |
| `components/Sidebar.tsx` | Left dock, tabbed: Watchlist / Active Trader / Depth | `ui/watchlist_panel.py` + `ui/active_trader_panel.py` |
| `components/ChartHeader.tsx` | Symbol search, timeframe buttons, chart-type selector, studies button, zones toggle, drawing-tool picker, crosshair toggle, fullscreen toggle, alarm-mode toggle + count badge, drawing-sets button, live OHLC/indicator readout | `ui/chart_panel.py` sub-toolbar |
| `components/TradingViewChart.tsx` | Candlestick + volume rendering, indicator overlays, price lines, hand-drawn tools with hit-testing/drag-edit, alarm price drag-to-adjust | `ui/chart_panel.py`, `candlestick_item.py`, `zone_overlay.py`, `alarm_overlay.py`, new `drawing_overlay.py` |
| `components/BottomToolbar.tsx` | Zoom in/out/reset, magnet-mode toggle, drawing count + clear, active group name, drawing-sets button | `ui/chart_panel.py` bottom bar |
| `components/DrawingActionBar.tsx` | Contextual bar when drawings selected: group/ungroup/delete/rename/recolor | Contextual toolbar in `chart_panel.py` |
| `components/DrawingGroupsModal.tsx` | Manage drawing "sets" per symbol | New `ui/drawing_groups_dialog.py` |
| `components/StudiesModal.tsx` | Indicator picker/settings incl. ICT, RTH Gaps, VIX SD | New `ui/studies_dialog.py` + `services/indicator_service.py` |
| `components/AlarmModal.tsx` | Full alarm CRUD + mute/rearm | New `ui/alarm_dialog.py` + `services/alarm_service.py` |
| `components/MarketDepth.tsx` | DOM ladder, cumulative size, flash animation, click-to-trade | `ui/active_trader_panel.py` (Depth tab) + `ibkr/market_depth.py` |
| `components/ActivePortfolio.tsx` | Positions panel, auto-detects option spread strategy, per-position/group stop/target | `ui/active_trader_panel.py` (Positions tab) + new `services/options_strategy.py` |
| `components/StopLossTargetModal.tsx` | Set/edit stop-loss & take-profit for a position or group | New `ui/stop_loss_target_dialog.py` |
| `components/TradeContextMenu.tsx` | Right-click: group/ungroup, set stop/target, close position(s)/group | Qt `QMenu` on the positions table |
| `services/marketData.ts` | Mock tickers + candle generator + indicator math | Mock generator **not ported**; indicator math (SMA/EMA/VWAP/Bollinger/RSI/MACD) ported to `services/indicator_service.py` |
| `services/ictStudies.ts` | ICT concepts: market structure (MSS/BOS), order blocks, FVG/BPR, liquidity pools, volume imbalance, NWOG/NDOG, displacement, kill zones | New `services/ict_service.py` |
| `services/gapAndVixStudies.ts` | RTH gap tracker + VIX-derived expected-move SD bands | New `services/gap_vix_service.py` |
| `services/drawingService.ts` | Drawing-group naming/numbering/color helpers | Folded into `services/drawing_service.py` |
| `services/alarmStorage.ts` | LocalStorage persistence + demo default alarms | Replaced by SQLite `alarms` table; no demo defaults needed |
| `services/soundAlert.ts` | Two synthesized alert tones (Web Audio oscillators) | New `services/sound_service.py` |

---

## 3. New feature scope this added (not in the original architecture doc)

- **Multiple chart render modes**: candles, hollow candles, Heikin-Ashi, line, area
  (the architecture doc only implied plain candlesticks).
- **A full drawing-tools system**: trendline, horizontal, zone, fibonacci, measure —
  selectable, drag-editable, groupable into named/colored/lockable "sets" per
  symbol, persisted.
- **Three advanced studies** beyond the basics:
  - **ICT Concepts** — market structure (MSS/BOS), bullish/bearish order blocks,
    fair value gaps & balanced price ranges, buy/sell-side liquidity pools, volume
    imbalance, weekly/daily opening gaps (NWOG/NDOG), displacement candles, and
    fixed kill-zone time windows (NY / London open / London close / Asian).
  - **RTH Gap Tracker** — detects session gaps and tracks "staircase" mitigation as
    price fills them.
  - **VIX Standard-Deviation bands** — daily expected-move bands from an
    anchor price and an annualized volatility input, at ±0.5σ/1σ/2σ/3σ.
- **A real alarm manager**, not a single overlay: create/list/mute/rearm/delete,
  condition = cross above/below/either, optional sound, optional note, persisted
  per symbol.
- **Two specific synthesized alert tones**, extracted with exact parameters so
  they can be reproduced without re-reading the repo:
  - *Alarm chime*: three overlapping oscillators — 880Hz sine (decaying to 875Hz
    over 0.35s), a 1318.5Hz triangle wave starting at +80ms, and a 1760Hz sine
    "echo" starting at +220ms.
  - *Order-fill blip*: a single sine sweep from 987.77Hz to 1318.51Hz over ~190ms.
  - Recommended Python approach: pre-render both to `.wav` once (via `numpy`) and
    play through `QSoundEffect`, rather than synthesizing live.
- **DOM with click-to-trade**: clicking a ladder row places a limit order at that
  price, with cumulative bid/ask size and a flash animation on size changes.
- **A positions panel that auto-detects options spread strategies**: given 2 or 4
  option legs sharing an underlying, it labels and groups them as Put/Call
  Credit/Debit Spreads (PCS/PDS/CCS/CDS) or an Iron Condor (IC), or "Custom"
  otherwise — this is a direct, pure-logic port of `detectOptionStrategy()`, no
  IBKR dependency.
- **Per-position and per-group stop-loss/take-profit**, mapped to IBKR bracket
  orders (parent + `STP` child + `LMT` child linked by `parentId`).
- **Right-click context menu** on positions: group/ungroup, set stop/target, close
  position(s)/group.

---

## 4. New modules added to the project structure

```
ui/
├── drawing_overlay.py          # trendline/horizontal/fib/measure tools, selection, hit-testing
├── drawing_groups_dialog.py    # manage drawing "sets"
├── studies_dialog.py           # indicator/study picker incl. ICT, RTH Gaps, VIX SD
├── alarm_dialog.py             # alarm CRUD + mute/rearm
├── stop_loss_target_dialog.py  # bracket order stop/target editor
└── trade_context_menu.py       # right-click position/group menu

services/
├── ict_service.py              # port of ictStudies.ts
├── gap_vix_service.py          # port of gapAndVixStudies.ts
├── drawing_service.py          # port of drawingService.ts
├── options_strategy.py         # port of detectOptionStrategy()
└── sound_service.py            # port of soundAlert.ts tone envelopes
```

`ibkr/orders.py` also gained bracket-order and (later-phase) `BAG`/`ComboLeg`
combo-order responsibilities it didn't previously have.

---

## 5. New SQLite tables

The original schema had `bars`, `watchlist`, `alarms`, and `zones`. The repo audit
added:

- **`drawing_groups`** — per-symbol named/colored/lockable drawing "sets"
- **`drawings`** — now includes a `group_id` foreign key (didn't exist before)
- **`positions`** — mirrors live IBKR positions plus locally-managed `stop_loss`,
  `take_profit`, and `group_id`
- **`trade_groups`** — groups of positions with a detected `strategy_type`
  (PCS/PDS/CCS/CDS/IC/CUSTOM)

The `alarms` table was also expanded from a simple price/direction pair to match
the repo's actual `PriceAlarm` shape: `condition` (cross_above/below/either),
`triggered` + `triggered_at`, `sound`, `note`, `created_at`.

---

## 6. New implementation phases

The original 8-phase plan (connection → historical → live → zones/alarms → DOM →
orders → reconnect/packaging) became an 11-phase plan (plus a 12th extension
phase), to accommodate the added scope without bundling too much into one phase:

| # | Added because of the repo audit |
|---|---|
| 4 | Split "zones + alarms" into standard-indicators-only, since studies turned out to be much larger |
| 5 | New phase: drawing tools + groups (didn't exist before) |
| 6 | Alarms now a dedicated phase with sound, not folded into zones |
| 7 | New phase: RTH Gaps / VIX SD / ICT studies (didn't exist before) |
| 10 | New phase: stop-loss/target bracket orders + options-strategy auto-grouping |
| 12 | New extension phase: multi-leg combo order placement, deliberately deferred (see Section 7 below) |

---

## 7. New open item raised by the repo audit

The reference app's positions panel groups multi-leg option positions into named
spread strategies (credit/debit spreads, iron condors) — but that's just client-
side labeling over positions that already exist. **Actually placing** such a spread
as one order ticket requires building an IBKR `BAG` contract with `ComboLeg`s,
which is materially more complex than single-leg order placement. The plan
recommends: port the strategy-detection/grouping *display* logic early (pure
math, Phase 10), and treat combo-order *placement* as a later, separate extension
(Phase 12) — flagged for you to confirm rather than assumed silently.
