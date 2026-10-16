# Architecture Proposal — NDThinkChart Batch 18b (**D42**): density-aware candle/volume width + mode-aware intraday history depth

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical
> architecture — `docs/architecture.md` is written by Plan Artifact Editor & Validator after
> validation. Companion: `docs/plan_proposal.md` (phases, per-file `touches_files` map, tests,
> assumptions, flagged issues, correction record).
>
> **Run shape:** this is a **legacy single-scope run** — the invocation preamble carries **no
> `phase: P<n>`**, so the proposal files are the unsuffixed `docs/architecture_proposal.md` /
> `docs/plan_proposal.md` (the D42 increment merges into the cumulative canonical docs as a
> `## D42 increment` section, exactly as D16–D41 did). Every decision below therefore carries an
> explicit **relationship label** (`[new in D42]` / `[extends D16: …]` / `[revises D6/D7: …]`)
> rather than a phase-relative one.
>
> **Scope: D42 only.** `requirements.md` carries `Status: READY_FOR_PLAN` (revised 2026-10-15
> 19:06), with `### D42` (`:3529`–`:3617`), `AC-D6.4` (revised `:1288`–`:1293`), `AC-D7.1`
> (revised `:1326`–`:1330`), the `AC-D9.2` note (`:1476`), `AC-D16.8` (extended `:1901`–`:1938`),
> **`AC-D16.9`** (new `:1940`–`:1972`), `A72`–`A73` (`:3694`–`:3695`), `R63`–`R64`
> (`:3813`–`:3814`), `DG68` (resolved) + `DG72`, and `open_questions.md` **Q51/Q52 answered**
> 2026-10-15. **D41 is built, reviewed and committed (`b48133d`) and is NOT reopened**; D1–D41 are
> otherwise unchanged.
>
> **What D42 is.** A **requirements-decision batch with no new feature**. It resolves the two
> **REQUIREMENTS-routed** Code Reviewer escalations, and the fixes for the two corresponding
> **BUILD** escalations fall out of it:
>
> 1. **ESC-042 → the candle/volume overlap** (unblocks BUILD **ESC-041**): the unconditional
>    `AC-D6.4` body floor contradicted `AC-D7.1`'s positive-gap clause; the resolution makes the
>    **no-overlap guarantee win** and the 4-px legibility floor **density-aware**.
> 2. **ESC-038 → RTH/ETH intraday history depth** (unblocks BUILD **ESC-037**): the "one session"
>    symptom is a **fetch-window** defect, not `useRTH`; the ≥ 30-trading-session floor and the
>    **present-but-empty trading day** rule apply to **both** session modes, with a mode-aware
>    day-presence pass and a mode-aware bar cache.
>
> **Out of scope (not planned here):** the other open BUILD escalations — ESC-032 (Position `id`),
> ESC-033 (Load Chart button), ESC-034 (watchlist flash timer), ESC-036 (priming `5 secs`),
> ESC-043 (`HELD`/`H` rows), ESC-044 (option contract fields), ESC-045 (Account Summary). They are
> separate work with no task yet. ESC-041/ESC-037 stay **BUILD-owned**; D42 does not absorb them —
> it supplies the normative target they are re-checked against. No `PLAN`-routed escalation is open
> (`escalations.json`: ESC-038/042 are `routed_to: REQUIREMENTS`), and `docs/plan_review.md` is the
> **APPROVED** D23 cycle (not `CHANGES_REQUIRED`), so this is a normal forward cycle.
>
> **Frozen baseline:** `main` after D41 (`b48133d`), full offscreen suite green. Suite invocation
> `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest` (the `pytest` entry point has a stale
> shebang).
>
> **Revision 2 (2026-10-15) — round 1 of 3, `CHANGES_REQUIRED` addressed.** The Validator ratified
> the substance (`FI-D42-1`–`FI-D42-4` accepted, `S18` ratified, `S13`/`S14` and `S15`–`S19` verified
> sound against source), so **no decision below is re-litigated**. Three required changes are folded
> in: **RC-D42-1** — the **third** `SESSION_BAR_CAP` site (`ui/chart_panel.py::ChartPanel.update_last_bar`'s
> `_bars` trim, `:1150`–`:1157`) is now named as a first-class `S18` consumer in the System
> Components / Data Model / traceability tables **and owned by a phase** in the plan (the one shared
> file between the two workstreams); **RC-D42-2** — the D16 **load-path** assertions that `S17`/`S18`
> legitimately change are now enumerated with their cause and stated to be **intent-preserving**
> corrections (`S21`, `AR-D42-6`); **RC-D42-3** — the pixel **unit** of `F` is stated explicitly in
> `S13` and in the plan's WS1 evidence. `FI-D42-2` is extended to the **five** enshrining suites,
> `FI-D42-1`'s cost is stated as **~8–16 MB**, and `FI-D42-3`/`FI-D42-4` keep their ratified readings
> (with the two `requirements.md` lines cited in the plan).
>
> **Revision 3 (2026-10-16) — reviewer escalation `ESC-050` (PLAN-routed, `open`) addressed.** An
> **enumeration/accuracy fix to this proposal and its companion only** — **no decision below is
> changed, added or re-litigated**, no `AC`, no phase boundary, no task and no canonical file. D42 is
> built, green and complete (26/26 tasks; full offscreen suite 1009 passed, exit 0) and its design was
> verified sound by the Validator and the Code Reviewer. `ESC-050` found that the D42 impact analysis
> **under-enumerated the suites changed by design**, in two independent places:
>
> - **`S21` / `RC-D42-2` / `AR-D42-6` named only the D16 load-path suites.** **19 assertions in six
>   further suites** also change by design — they **drive** `MainWindow.load_chart` with a
>   **fixed-size** `req_historical_data` reqId iterator while the floor span makes a load issue **many**
>   chunks (`ESC-048`'s defect class) — and **4 further sites** inside the D16 files were likewise
>   unnamed (2 more found by Plan re-verification).
> - **`AR-D42-6`'s mitigation asserted** that *"every load-path assertion that changes is enumerated in
>   `S21` and in the plan's correction record"* — an assertion that was **false as written**. It is now
>   **true** (the enumeration is complete) **and** replaced in form by the **invariant** + the
>   generalisable **enumeration rule** (`S21`, AR-D42-6), so completeness is checkable by a rule rather
>   than by a claim.
> - **One disclosure (checklist, not a decision):** a **Frozen Interfaces** section is added below,
>   restating **verbatim** the contracts this increment leaves read-only (`session_windows`,
>   `plan_requests`, `MissingSpan`, `RequestPlan`, `bar_period_seconds`, `Bar`, `TIMEFRAME_CONFIG`,
>   `popouts.ext_hours`), and explicitly **not** freezing the surfaces under construction. It adds no
>   decision — every contract is copied from the tree at `b48133d` and already reflected in the
>   `[existing]` rows of System Components / Data Model / Integration Points.

---

## Relationship to prior increments

| Prior decision / component | Relationship | Note |
|---|---|---|
| `AC-D6.4` unconditional 4-device-px body floor; `ui/candlestick_item.py::CandlestickItem._draw_candles` clamp (`:122`–`:140`); `AC-D7.1` "gap remains positive" | **`[revises D6/D7: the body-width clamp]`** | `S13`+`S14`: the floor becomes density-aware and the body is capped at the inter-bar pitch. Supersession is **recorded** (never silent) per the D42 correction record. |
| `AC-D9.1`/`AC-D9.2` volume width == price body width; `ui/chart_panel.py::ChartPanel._clamp_half_width` (`:1229`) / `::_refresh_candles` (`:1303`/`:1305`) / `::_refresh_live_bar` (`:1352`) | **`[extends D9: the volume width path]`** | Intent unchanged; the volume path consumes the **same** capped `w` from the one shared helper (`S13`). |
| D16 backfill planner (`services/backfill_service.py::find_missing_spans`), `data/bar_cache.py`, `services/market_calendar.py`, `ui/main_window.py::MainWindow.load_chart`/`_finalize_history_wave` | **`[extends D16: the missing-span / day-presence / cache path]`** | `S15`–`S19`. `AC-D16.1`/`AC-D16.3`/`AC-D16.4` (no-fill / genuine-closure / shortfall-report) are **unchanged**. |
| D27.7 bar-level trailing pass (`_bar_level_missing_spans`, `:239`–`:297`) | **`[extends D27: the bar-level pass]`** | Already `ext_hours`-aware; unchanged in shape, now fed by the mode-aware presence predicate for consistency (`S15`). |
| D28.3 pacing-aware waves (`TickerSession._issue_wave_chunks`, `:858`; `MAX_HISTORICAL_PER_600S = 60`) | **`[extends D28: the wave pump]`** | Unchanged. The depth floor is delivered as **more plans** through the existing wave cap + continuation timer — no new transport mechanism (`S17`). |
| D28.4 caps (`config/settings.py::SESSION_BAR_CAP = 5000`, `data/bar_cache.py::RETENTION_BARS = 5000`) and the D28.4 render split | **`[revises D28.4: the two 5000-bar caps]`** | `S18`: the caps become **floor-aware** (≥ the flat 5000, derived per timeframe × mode) at **all three** `SESSION_BAR_CAP` sites — `ui/ticker_session.py::TickerSession.set_bars` (`:300`), `::TickerSession._append_bar` (`:313`) and `ui/chart_panel.py::ChartPanel.update_last_bar` (`:1150`–`:1157`) — plus `BarCache.prune`'s `keep`. Recorded as a deliberate revision of a D28.4 bound, forced by `AC-D16.8`. |
| D24.9 pop-out `ext_hours` persistence (`popouts.ext_hours`) | **`[extends D24: pop-out mode]`** | The pop-out already knows its mode; it now passes it to the cache/planner (`S19`). |
| D41 removals | **no relationship** | D42 touches neither the removed surface nor its retained substrate. |

---

## Codebase Summary (existing repository — D42 surface, source-validated 2026-10-15)

The repo is **not** greenfield: a PyQt6 + pyqtgraph + official `ibapi` desktop trading terminal
(~4,920 graph nodes; full offscreen suite green after D41 @ `b48133d`). This section is a factual
inventory of the surface D42 touches; every item below was read in the tree during planning.

### Data models / schema `[existing]`

- **`data/db.py::DB`** — SQLite, one connection, `_init_schema()` (DDL script) + `_migrate_schema()`
  (additive `ALTER TABLE`, `CREATE UNIQUE INDEX`, one idempotent `DROP TABLE IF EXISTS
  footprint_cache` from D41). Tables: `bars`, `watchlist`, `alarms`, `zones`, `drawing_groups`,
  `drawings`, `studies`, `popouts`, `positions`, `trade_groups`, `position_group_map`,
  `yfinance_events_cache` (D38), `volume_baseline` (D39).
  - **`bars`** (`:16`–`:22`) — `(symbol TEXT, timeframe TEXT, ts INTEGER, open, high, low, close,
    volume)`, **`PRIMARY KEY (symbol, timeframe, ts)`**. **No `useRTH`/mode component** — this is
    the `useRTH`-blind cache key `AC-D16.9` names.
  - `popouts` (`:76`–`:84`) already persists `ext_hours INTEGER NOT NULL DEFAULT 1` per pop-out.
  - `config/paths.py::get_db_path()` returns the **user-space production DB** when `DB_PATH` is
    unset (`tests/conftest.py` sets it to a temp file).
- **`data/models.py::Bar`** — `@dataclass` with `symbol, timeframe, ts, open, high, low, close,
  volume` (no mode field; plain dataclass, no `__slots__`).
- **`data/bar_cache.py::BarCache`** — `RETENTION_BARS = 5000` (`:8`); `save_bars(bars)` (`:13`,
  `INSERT OR REPLACE`), `get_bars(symbol, timeframe)` (`:27`), `prune(symbol, timeframe,
  keep=RETENTION_BARS)` (`:39`), `get_last_timestamp` (`:55`, unused by the load path).
- **`services/backfill_service.py`** — pure, Qt-free planner: `MissingSpan`, `RequestPlan`,
  `bar_period_seconds` (`:104`), `_duration_to_seconds` (`:113`), `_et_date`/`_et_day_start_ts`/
  `_trading_days`/`_build_span` (`:139`–`:163`), **`find_missing_spans(cached_ts, now_ts, timeframe,
  trailing_days=TRAILING_BAR_GRANULARITY_DAYS, ext_hours=False)`** (`:169`), `_bar_level_missing_spans`
  (`:239`), `plan_requests(missing_spans, timeframe)` (`:299`).
- **`services/market_calendar.py`** — pure ET calendar: `is_trading_day`, `trading_days`,
  **`session_windows(start_ts, end_ts, ext_hours)`** (`:195`–`:216`) with `_EXT_OPEN/_EXT_CLOSE =
  04:00/20:00` and `_RTH_OPEN/_RTH_CLOSE = 09:30/16:00` ET (`:37`–`:40`), and the ESC-023 NYSE
  Rule 7.2 New-Year exception (`:117`–`:121`).
- **`services/time_collapse_service.py::TimeCollapseMap`** — the D21.4 display-only x-transform
  (`_to_display`), which the candle/volume width math is expressed in.
- **In-memory caps:** `config/settings.py::SESSION_BAR_CAP = 5000` (`:45`), applied in
  `TickerSession.set_bars` (`:300`), `TickerSession._append_bar` (`:313`) and
  `ChartPanel` (`:1150`/`:1157`); `config/settings.py::MAX_HISTORICAL_PER_600S = 60` (`:35`) and
  `ibkr/pacing.py::pacing_manager`.

### Major components and responsibilities (as-built)

| Component | Responsibility (D42-relevant) |
|---|---|
| `ui/candlestick_item.py` (~200 lines) | `CandlestickItem` 5 render modes; `_draw_candles` (`:100`–`:163`) computes the half-width (`median_diff * 0.325`, `:111`), reads the ViewBox range and applies the **unconditional 4-px floor** (`min_w = 2.0 / px_per_sec`, `:136`–`:138`), draws the cosmetic 1-px wick + body into a `QPicture`; `set_data(..., width=...)` carries the D28.4 cached half-width override (`:63`–`:71`). |
| `ui/chart_panel.py` (~1,800 lines) | `_compute_candle_half_width` (`:1215`, median of **display-x** diffs × 0.325, cached as `_candle_half_width`), `_clamp_half_width` (`:1229`, the volume-side mirror of the same 4-px floor), `_refresh_candles` (`:1249`; volume `w_vol` at `:1303`, `volume_bars.setOpts(width=w_vol*2)` `:1305`, live volume `:1310`/`:1314`, `candlestick.set_data(..., width=...)` `:1318`/`:1326`), `_refresh_live_bar` (`:1333`), `_bars` trim at `SESSION_BAR_CAP` (`:1150`–`:1157`). |
| `ui/ticker_session.py` (~1,800 lines) | Per-symbol session: `get_bars` (`:295`), `set_bars` (`:298`, capped), `_append_bar` (`:306`, capped), `_wave_extended_hours` (`:127`), `queue_wave_plans` (`:843`), `_issue_wave_chunks` (`:858`, `useRTH=1` + `extended_hours=` passed to `md_manager.req_historical_data`), `_schedule_wave_continuation` (`:886`), `_wave_may_complete` (`:900`). |
| `ui/main_window.py` (~3,700 lines) | `load_chart` (`:1560`–`:1705`): cached read (`:1630`), `find_missing_spans(..., ext_hours=extended_hours)` (`:1647`–`:1652`), `plan_requests` (`:1653`), wave queue (`:1662`), **empty-cache single-window branch** (`:1668`–`:1684`); `_finalize_history_wave` (`:1950`–`:2044`): `save_bars` (`:1970`), `prune` (`:1973`), `get_bars` (`:1974`), AC-D16.4 shortfall via `_missing_backfill_trading_days` (`:2046`–`:2060`); `_on_ext_hours_toggled` (`:2777`–`:2784`, relabels and re-loads). |
| `ibkr/market_data.py` | `TIMEFRAME_CONFIG` (`:7`–`:13`) — the **per-request** duration/bar-size caps (`1 min → 1 D`, `5 mins/15 mins → 5 D`, `1 hour → 10 D`, `4 hours → 30 D`, `1 day → 1 Y`); `req_historical_data(..., extended_hours=)` maps to `useRTH` (`:26`–`:58`). |
| `tests/` | pytest + pytest-qt offscreen; the **five** suites that enshrine the old rule are `test_candle_spacing.py` (`:4`–`:10`, a source-string check that never renders), `test_volume_width.py` (`:103`–`:104`), `test_chart_dpi.py` (`:245`–`:250`, `assert body_dev >= 4.0` on the dense 960-bar DPR-2 dataset), `test_d28_2_sessions.py` (`:166`) and `test_d28_4f_panel_bar_cap.py` (`:53`); the D16/D27 planner suites are `test_backfill_service.py`, `test_d27_backfill_granularity.py`, `test_history_backfill*.py`, `test_market_calendar.py`; the cap suites are `test_d28_2_sessions.py`, `test_d28_4e_bar_cache_retention.py`, `test_d28_4f_panel_bar_cap.py`; and the D16 **load-path** suites whose expectations `S17`/`S18` legitimately change are `test_history_backfill_loadpath.py` (`:202`/`:206`, `:238`, `:255`–`:257`, `:431`, `:477`), `test_history_backfill.py` (`:285`, `:451`–`:457`, `:590`) and `test_history_backfill_disconnect.py` (`:362`). **Load-path-*coupled* by stubbing the feed (`ESC-050` — every one of these boots a `MainWindow`, stubs `md_manager.req_historical_data` with a fixed-size reqId iterator and asserts downstream):** `test_d24_popouts.py`, `test_phase3_fixpass.py`, `test_d24_alarm_full_chain.py`, `test_d24_smoke_gate.py`, `test_d24_9_popout_persistence.py`, `test_d28_tick_burst_baseline.py` — they are **not** D16 suites, which is exactly why the D42 impact analysis missed them. |

### Key entry points / data flow (unchanged shape)

`MainWindow.load_chart` → `BarCache.get_bars` → `find_missing_spans` → `plan_requests` →
`TickerSession.queue_wave_plans`/`_issue_wave_chunks` → `MarketDataManager.req_historical_data`
(`useRTH`, `endDateTime`, `duration`, `bar_size`) → `IBApiClient.historicalData` →
`_on_historical_bar`/`_on_historical_data_end` → `_finalize_history_wave` → `BarCache.save_bars` →
`session.set_bars` → `ChartPanel.update_chart` → `_refresh_candles` (price **and** volume).

### External integrations already in use `[existing]`

IBKR TWS over `ibapi` (historical + realtime bars, market data, contract details, orders) on
**live port 7496 only**; SQLite persistence; `yfinance` (D38, unrelated); no message queue, no
cache server, no auth provider.

### What D42 changes, in one line

`AC-D16.9`'s two defects are **real and both mode-blind in the same code path**: `present_days =
{_et_date(ts) for ts in ts_values}` (`services/backfill_service.py:208`) decides day presence with
**no** session window, and `BarCache.get_bars/save_bars` key on `(symbol, timeframe)` with **no**
mode (`data/bar_cache.py:13`/`:27`, `data/db.py:21`). The width defect is the same shape:
`ui/candlestick_item.py:136`–`:138` applies `min_w` **unconditionally**, and
`ui/chart_panel.py:1242`–`:1244` mirrors it for volume — at a 3.83-px pitch the floor makes the gap
negative (ESC-041).

---

## Summary

D42 is a **two-workstream correctness increment** on existing paths, with **no new feature and no
stack change**. **(1)** The rendered candle body becomes `body = min( max(0.65 × pitch, F), pitch )`
computed by **one shared, pure helper** that both the candle `QPicture` and the volume
`BarGraphItem` width path call, so the **no-overlap guarantee (`gap >= 0`) wins** over the D6 4-px
legibility floor at extreme density while the floor still binds in the non-dense regime (the wick
stays a cosmetic 1-px line). **(2)** The intraday fetch gains a **backwards-extending depth floor**
(≥ 30 trading sessions before the current session, in **both** RTH and ETH) delivered through the
**existing** D28.3 wave pump as ordinary `RequestPlan`s, driven by a **mode-aware** day-presence
predicate and a **mode-aware** bar cache (`bars.ext_hours`), with **all three `SESSION_BAR_CAP` cap
sites plus `BarCache.prune`'s `keep`** made floor-aware so the floor survives pruning **and is not
trimmed out of the displayed series on the next live candle**. Every supersession
(`AC-D6.4` unconditional floor, `AC-D7.1` positive-gap wording, the RTH-only depth default) is
**recorded**, and the **five** suites that enshrine the old rule are **corrected, not weakened**.

---

## Tech Stack Decisions

Constrained (existing) choices first, then the D42 additions/changes. Every row carries a rationale
and the alternatives considered.

| # | Decision | Choice | Rationale | Alternatives considered |
|---|---|---|---|---|
| S1 | Language / UI stack `[existing]` | Unchanged: Python 3.11+ (`.venv`), PyQt6 (`>=6.6`), pyqtgraph (`>=0.13`), numpy (`>=1.26`) | Existing-repo hard constraint; "changing the tech stack" is an explicit non-goal in `requirements.md` | Any new UI/charting/numeric framework — rejected |
| S2 | Broker / persistence / packaging / tests `[existing]` | Unchanged: official `ibapi` (`ibapi-latest==10.51.1`), **live TWS 7496 only** (`check_live_port` fail-fast), SQLite via `config/paths.get_db_path()`, PyInstaller `.app`, pytest + pytest-qt offscreen, no live TWS and no transmitted orders | Existing-repo hard constraint; Q8/Q9 | Paper mode / new broker / new DB / new test framework — rejected |
| S3 | **Testing** `[existing]` | pytest + pytest-qt, `QT_QPA_PLATFORM=offscreen`, run as `.venv/bin/python -m pytest`; any **non-pytest** probe that can reach a DB-writing path exports `DB_PATH` to a temp file (ESC-043) | Repo standard + the repo's own recorded gotchas | Manual / live-TWS verification — rejected |
| S13 | **One shared capped-width helper** `[new in D42]` — **revises the D6/D7 clamp** | Add a **pure** module-level function in `ui/candlestick_item.py` (the module that owns the D6 formula): `capped_body_half_width(median_diff, base_half_width, px_per_sec, floor_px=4.0) -> float` implementing `w = min( max(base_half_width, floor_px / 2 / px_per_sec), median_diff / 2 )`, i.e. `body = min(max(0.65×pitch, F), pitch)` with `base_half_width = 0.325 × median_diff` and `F` the existing 4-px constant. **Unit of `F` (`FI-D42-4` / `AP-D42-5`, stated explicitly per RC-D42-3):** `floor_px = 4.0` is **4 ViewBox logical px** — the unit `px_per_sec` yields (`vb.width() / x_span`) and the unit the shipped `min_w = 2.0 / px_per_sec` already uses (`ui/candlestick_item.py:136`), i.e. **8 device px at DPR 2**; it is **not** the `AC-D6.4` literal's "4 device pixels at DPR 2". `AC-D6.4`'s operative clause is "measured in the **same** pixel unit" and the shipped constant is kept, so the criterion's outcomes hold unchanged — and the WS1 test evidence applies `F` in **this** unit and asserts the unit-free relations `body <= pitch` / `body == pitch` **Three call sites, one implementation:** `CandlestickItem._draw_candles` (`:136`–`:138`), `ChartPanel._clamp_half_width` (`:1229`, imported, so the volume path cannot drift), and therefore `_refresh_candles` (`:1303`) / `_refresh_live_bar` (`:1352`) automatically | `AC-D6.4`/`AC-D7.1` (revised) + `AC-D9.1`/`AC-D9.2`'s note require **one shared capped `w`** for candle and volume; **R63** names exactly the risk of the two paths diverging. A single pure function is directly unit-testable (three regimes: `pitch > F`, `pitch == F`, `pitch < F`) without a QApplication, and it keeps the 0.325 / 35 % intent visible in one place | (i) patch the two clamp sites independently — duplicates the rule, R63's failure mode — rejected; (ii) put the cap in `ChartPanel` and pass the capped `w` down to `CandlestickItem` — inverts the D28.4 ownership (`CandlestickItem` clamps at generation time using the ViewBox range; ESC-013 depends on that ordering) — rejected; (iii) a new `ui/candle_width.py` module — an extra module for one 3-line rule — rejected |
| S14 | **Pitch plumbing for the D28.4 width override** `[new in D42]` | `ChartPanel` caches the **pitch** alongside the half-width: `_compute_candle_half_width` (`:1215`) already computes `median_diff` over **display-x**; it returns/stores both (`_candle_pitch`). `CandlestickItem.set_data(..., width=…, pitch=…)` gains the optional `pitch`; `_draw_candles` uses the supplied pitch when `_width_override` is set, otherwise computes `median_diff` from `data` exactly as today. `ChartPanel` passes `pitch=self._candle_pitch` at `:1318`/`:1326`/`:1347` | The cap **needs the pitch**, and the D28.4 override exists precisely to skip the O(n log n) median sort on regeneration — recomputing it inside `_draw_candles` would undo D28.4's perf fix. Both the pitch and the width come from the same **display-x** series, so `median_diff`, `px_per_sec` (ViewBox units) and `F` are in the **same pixel unit** (`AC-D6.4`'s "same pixel unit" clause) | (i) always recompute the median inside `_draw_candles` — reintroduces the sort D28.4 removed — rejected; (ii) drop the override and let `CandlestickItem` own the width entirely — a D28.4 perf regression — rejected; (iii) cap in data units only (ignore the ViewBox) — the floor is a **device**-pixel rule and needs `px_per_sec` — rejected |
| S15 | **Mode-aware day presence** `[new in D42]` — **extends D16** | A pure predicate in `services/backfill_service.py`: a day is **present** iff ≥ 1 cached bar's timestamp falls inside that day's **current mode's** session window, via `market_calendar.session_windows(day_start, day_end, ext_hours)`. `find_missing_spans`'s `present_days = {_et_date(ts)}` (`:208`) is replaced by the window-membership set; `MainWindow._missing_backfill_trading_days` (`:2052`–`:2054`) — the **AC-D16.4 shortfall report** — calls the **same** exported predicate instead of its own mode-blind `present_days` | `AC-D16.9`'s normative rule and its measurable (a)/(b)/(c); the bar-level pass (`:276`) already uses `session_windows(..., ext_hours)`, so today **one** planner decides presence two different ways. Bar timestamps are period **starts** (recorded gotcha), so the window test applies to the bar's start timestamp — which is exactly why an RTH-empty day can look covered | (i) keep the mode-blind presence set and only fix the bar-level pass — leaves ESC-037's silent RTH hole — rejected; (ii) decide presence per day from the *first/last* bar only — wrong for a day whose bars straddle the window — rejected; (iii) filter the cached series by mode before the planner sees it — conflates cache scoping with presence and would break `AC-D16.9(c)`'s "RTH bars are ETH-present" — rejected |
| S16 | **Mode-aware cache key + migration** `[new in D42]` — **extends D16** | `bars` gains **`ext_hours INTEGER NOT NULL DEFAULT 1`** and its key becomes **`(symbol, timeframe, ext_hours, ts)`**; `BarCache.save_bars(bars, ext_hours=True)` / `get_bars(symbol, timeframe, ext_hours=True)` / `prune(symbol, timeframe, ext_hours=True, keep=…)` (the mode is a **keyword with the app's default**, so existing call sites and suites stay valid). SQLite cannot alter a primary key, so `data/db.py::_migrate_schema` **rebuilds** the table once, guarded by `PRAGMA table_info(bars)` (idempotent, crash-safe, the same mechanism D41 used for its drop): create `bars_new` with the new key, `INSERT OR IGNORE … SELECT symbol, timeframe, 1, ts, …`, drop `bars`, rename | `AC-D16.9` and `AC-D16.8`'s mode-isolation clause **explicitly require** a mode-aware cache/key ("keyed on symbol+timeframe+mode") so a mode switch cannot read the other mode's bars as coverage — `requirements.md:1957`–`:1958` ("The bar cache/key is **mode-aware** (RTH vs ETH) … This applies **in both directions**") together with `AC-D16.9`'s measurable (c) at `:1967`–`:1969` (a **presence predicate** on a given bar set: RTH bars lie inside `04:00–20:00 ET`, so the ETH call reports the day present), which is the ratified reading of `FI-D42-3`. `ext_hours` (0/1) is the vocabulary the whole pipeline already speaks (`useRTH`, `find_missing_spans(ext_hours=)`, `popouts.ext_hours`), so no new enum is introduced. Legacy rows are tagged **`ext_hours = 1` (ETH)**: the app's default is **Ext Hours ON** (`ext_hours_btn.setChecked(True)`, `:244`), so pre-existing rows were fetched with `useRTH=0`; an RTH load after the migration finds its own (empty) key and fetches the required floor — **no hole, and that fetch is required by `AC-D16.8` anyway** | (i) **no schema change** — keep one `(symbol, timeframe, ts)` cache and make only the *presence* predicate window-based. Passed over: it satisfies every measurable of `AC-D16.9` but fails its explicit "the bar cache/key is mode-aware" clause and `AC-D16.8`'s "in both directions" wording, and it cannot distinguish "the user never loaded ETH for this symbol" from "ETH is covered" — rejected; (ii) wipe the cache on migration — cheapest, but discards a valid cache and forces a full refetch of every symbol/timeframe/mode for no correctness gain (legacy rows are ETH-fetched, i.e. already the widest window) — rejected; (iii) a third `'LEGACY'` mode visible to both — more correct in principle, but adds a tri-state to every read/write/prune for one migration's benefit — rejected; (iv) store mode in a side table keyed by `(symbol, timeframe)` — loses per-bar truth after a mode switch — rejected |
| S17 | **Backwards depth floor through the existing planner** `[new in D42]` | `find_missing_spans(cached_ts, now_ts, timeframe, trailing_days=…, ext_hours=False, min_sessions=0)` gains **`min_sessions`** (default `0`). When `min_sessions > 0` **and** the timeframe is intraday, the planner computes the **floor day** = the `min_sessions`-th trading day before the current session and emits **at most one** `MissingSpan` covering `[floor_day_start, earliest_present_day_start)` (or `[floor_day_start, now]` when nothing is present), so the floor is fetched **backwards** and **collapses to empty once filled**. `MainWindow.load_chart` passes `min_sessions=MIN_INTRADAY_SESSIONS` for intraday timeframes in **both** the cached path (`:1647`) and the empty-cache path — the `elif not cached` single-window branch (`:1668`–`:1684`) is **removed** because the floor span already yields plans (the empty-cache case becomes "one span from the floor to now") — which requires that the `find_missing_spans(...) if cached else []` guard at `ui/main_window.py:1647`–`:1652` **and** the empty-cache early return at `services/backfill_service.py:205`–`:206` are both bypassed when `min_sessions > 0` | `AC-D16.8` requires the floor for **all five** intraday timeframes in **both** modes; IBKR caps `1 min` at `1 D` per request, so the depth must come from **chained** requests. Reusing `plan_requests` (`:299`, which already chunks a span newest-first by the configured duration) means the floor needs **no new transport path** and rides D28.3's wave cap + continuation timer unchanged. `min_sessions=0` is the default, so **every existing D16/D27 planner suite keeps its exact semantics**; R64's "the D16 suite stays green" is met by **intent-preserving correction** of the D16 **load-path** suites (enumerated with their cause in `S21` / the plan's correction record) — **and, per `ESC-050`, of every suite that merely *drives* that load path with a stubbed historical feed** (19 assertions in six suites; the **invariant** in `S21`) — never by weakening an assertion | (i) raise `TIMEFRAME_CONFIG` durations — `1 min` is hard-capped at `1 D` and the chaining is required regardless, so one mechanism serves all five timeframes — rejected; (ii) a separate `depth_service.py` — duplicates `plan_requests`/`_trading_days` — rejected; (iii) a new "floor" request kind in the session — bypasses the pacing accounting — rejected; (iv) keep the empty-cache special branch and add the floor only to the cached path — leaves the ESC-038 repro (fresh `1 min` RTH) at one session — rejected |
| S18 | **Floor-aware bar budget (all three `SESSION_BAR_CAP` sites + `prune`'s `keep`)** `[new in D42]` — **revises D28.4** | Add a pure helper (in `services/backfill_service.py`, next to `bar_period_seconds`/`session_windows`): `floor_bar_budget(timeframe, ext_hours) -> int` = `max(SESSION_BAR_CAP, ceil(min_sessions × window_seconds(timeframe, ext_hours) / bar_period) × 1.15)`, where `window_seconds` is 6.5 h (RTH) or 16 h (ETH); `1 day` returns the flat cap (not covered by the floor). The **three** cap sites use it — `TickerSession.set_bars` (`:300`), `TickerSession._append_bar` (`:313`), and **`ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`)** — and the load path passes `keep=floor_bar_budget(...)` to `BarCache.prune` (`:1973`). The panel trim is the site that matters most: `update_chart` seeds `ChartPanel._bars` from the session's (now up to 33,120-bar) series and `update_last_bar` would otherwise re-trim it to the flat 5,000 on the **next new-candle tick**, i.e. the `AC-D16.8` floor would be discarded from the **displayed** series after one live bar (`FI-D42-1`'s failure mode one layer up). **Ownership (RC-D42-1):** this edit is owned by the **same phase as `floor_bar_budget`** (Phase 2) and is **sequenced after** the `ui/chart_panel.py` width edit of the other workstream — `ui/chart_panel.py` is the **one** file shared by the two workstreams, so the two `ui/chart_panel.py` tasks must never be `in_progress` in the same wave (`build_wave.py`'s overlapping-`touches_files` rule); see the plan's per-file map. The **flat constants stay** as the default/floor (`RETENTION_BARS = 5000`, `SESSION_BAR_CAP = 5000`) | **`AC-D16.8` is otherwise unsatisfiable on this build.** A `1 min` RTH session is 390 bars, so 30 sessions = **11,700 bars** > the 5000 cap; `1 min` ETH is 960/session → **28,800**; `5 mins` ETH → **5,760**. Both the SQLite `prune` (`RETENTION_BARS`) and the in-memory caps would **delete the floor after fetching it**, so the displayed series could never cover 30 sessions. Keeping the flat constants as the default preserves `prune(sym, tf)`'s existing behaviour and `test_d28_4e_bar_cache_retention.py` unchanged | (i) leave the caps and accept a shortfall — directly contradicts `AC-D16.8`'s "the displayed bar series covers at least 30 trading sessions" — rejected; (ii) lower the floor for dense timeframes — `AC-D16.8` states 30 sessions for **all five** — rejected; (iii) raise the two constants unconditionally to 33,120 — inflates memory for `1 day`/`4 hours` charts that need 5,000 at most, and breaks the flat-cap suites for no reason — rejected; (iv) make the floor count **sessions** rather than bars and fetch lazily per viewport — the chart auto-frames the whole cached series, so the series itself must hold the floor — rejected |
| S19 | **Mode threading through the load path** `[new in D42]` | `TickerSession` already owns `_wave_extended_hours` (`:127`); it gains the same value as the **session's mode** for its own cache reads (`get_bars` `:295`, the D39 baseline preload `:684`) and writes (`_finalize_history_wave`'s `save_bars`). `MainWindow.load_chart` passes the mode explicitly at `:1630` (`get_bars`), `:1648` (`find_missing_spans`), `:1662`/`:1672` (wave queue) and `:1970`/`:1973`/`:1974` (finalize). `services/alarm_monitor.py:287`'s `BarCache.get_bars(symbol, "1m")` keeps the default (its prev-price seed is mode-neutral) | One place per hop, no globals, and the mode travels with the session that already owns the wave — so a pop-out (whose `ext_hours` is persisted in `popouts`) and the primary chart cannot cross-contaminate. `get_bars`'s existing `timeframe`-keyed session map is untouched | (i) a module-level "current mode" global — two charts with different modes would corrupt each other — rejected; (ii) re-key the session's `_bars` map by `(timeframe, mode)` — unnecessary: a session is loaded in one mode at a time and `load_chart` resets it — rejected; (iii) make `ext_hours` a required positional argument — forces every legacy test/caller to change for no benefit — rejected |
| S20 | **Config surface** `[new in D42]` | **One new constant:** `config/settings.py::MIN_INTRADAY_SESSIONS = 30` (the owner-required floor, `AC-D16.8`, A73). **`ibkr/market_data.py::TIMEFRAME_CONFIG` is NOT changed** — its durations are the **per-request** IBKR caps, and the depth comes from chaining (`S17`). `MAX_HISTORICAL_PER_600S = 60` and the pacing model are unchanged | The floor is an owner-required number that both the planner and the budget derive from, so it belongs in the settings module the pacing/cap constants already live in; changing `TIMEFRAME_CONFIG` would either be a no-op for `1 min` (hard cap) or a redundant second mechanism | (i) hard-code 30 in the planner — a magic number split from its rationale — rejected; (ii) change `TIMEFRAME_CONFIG` durations as the task brief anticipated — rejected for the reason above (recorded as an explicit non-change so the Validator sees the decision) |
| S21 | **Test surface** `[new in D42]` — **corrects five enshrining suites + the D16 load-path suites + the six load-path-*driving* suites (`ESC-050`), extends five, adds four** | **Corrected (never weakened, never deleted):** `tests/test_candle_spacing.py` (string-presence → regime/geometry assertions on the shared helper), `tests/test_volume_width.py` (the dense `≈ 4.0 px` legs → `body == pitch`, `gap >= 0`, volume == body), `tests/test_chart_dpi.py` (the dense `body_device_px >= 4.0` leg → the **non-dense** dataset carries the `>= F` claim; the dense dataset carries `body <= pitch`). **Corrected for the floor-aware caps:** `tests/test_d28_2_sessions.py::test_session_bar_cap` and `tests/test_d28_4f_panel_bar_cap.py` (assert the derived budget, keep the oldest-dropped/newest-kept invariant). **Corrected — D16 load-path (RC-D42-2; every correction intent-preserving, the cause named in the plan's correction record):** `tests/test_history_backfill_loadpath.py::test_t39_t02` (`:238` — the **floor span**: 5 seeded ETH sessions < 30), `::test_t39_t03` (`:255`–`:257` — the empty-cache branch `S17` **removes**), `::test_t39_t01` (`:202`/`:206` — the test's own planner call must pass the floor), `::test_t39_t06`/`::test_t39_t07` (`:431`/`:477` — the **floor-aware `keep`**), `tests/test_history_backfill.py` (`:285`, `:451`–`:457`, `:590` — the floor span and the removed empty-cache single-window branch) and `tests/test_history_backfill_disconnect.py` (`:362` — the same removed branch). Each keeps its guarantee: "no **redundant** request once the floor is satisfied and the cache reaches *now*"; an empty cache is covered **by the planner** as one floor span rather than by a special branch; the retention invariant becomes the **derived** budget with oldest-dropped/newest-kept. **`ESC-050` completes this enumeration (the `RC-D42-2` table named 9 sites; the D42 diff changes 14 test functions in these three files):** the **4** `ESC-050` records — `test_history_backfill.py::test_t40_t03` (`:362`, the "no shortfall message" form → the closure days are never **named** missing), `::test_t40_t05` (the same class; its correction is in fact `test_t40_t04`'s **second** assertion at `b48133d:484`–`:485` — `t40_t05` carries no shortfall assertion in either revision), `test_history_backfill_disconnect.py::test_t43_t03` (`:227`) and `::test_t44_t03` (`:459`) (the status bar previews only the **first five** missing days, now the floor days, while the log carries the full list → asserted against the **log**) — **plus 2** found by Plan re-verification: `test_history_backfill_loadpath.py::test_t39_t04` (`:269`, the `save_bars`/`get_bars` spies must forward `ext_hours` — `S19` mode threading) and `::test_t39_t05` (`:336`, the new session's **own** floor span means its in-flight id set is not empty → "the cancelled ids never leak"). **Corrected — load-path-*driving* suites (`ESC-050`; not D16 suites, enumerated nowhere before):** **19 assertions in six suites** that merely **drive** `MainWindow.load_chart` while stubbing `md_manager.req_historical_data` with a **fixed-size** reqId iterator — `tests/test_d24_popouts.py` (7), `tests/test_phase3_fixpass.py` (7), `tests/test_d24_alarm_full_chain.py` (2), `tests/test_d24_smoke_gate.py` (1), `tests/test_d24_9_popout_persistence.py` (1), `tests/test_d28_tick_burst_baseline.py` (1). **Cause:** the floor span makes one intraday load issue **many** chunks (an empty-cache `5 mins` load plans **9**), so the second `next(hids)` raises `StopIteration` — **fixture exhaustion, not a product defect**. **Correction:** test-only — widen each stub to an **unbounded** source (`itertools.count(<first>)`, the `P2-T19` precedent at `tests/test_d28_2_sessions.py:41`), the `lambda *a, **k: next(hids)` form unchanged, **no assertion weakened, skipped or xfailed**. **The invariant (`ESC-050`), stated so it is checkable before dispatch:** *any test that drives `MainWindow.load_chart` with a stubbed `req_historical_data` must use an **unbounded** reqId source (the floor span issues many requests); any test asserting the **exact number** of historical requests, **one** request/chunk per load, or the **empty-cache single-window branch** changes by design.* **The generalisable rule (`ESC-050`; the second under-count in this batch):** *enumerate the assertions an increment changes by **call site of the changed entry point**, not by the suites the design names* — including tests that only **drive** the changed path; a **fixed-size stub of a changed feed is a defect class** (grep the suite for `iter([...])` feeding `next(...)` and correct all of them in one scoped task); and an enumeration asserted to be complete must **be** complete or be **replaced by the invariant that generates it**. **Extended:** `tests/test_backfill_service.py` / `tests/test_d27_backfill_granularity.py` (mode-aware presence cases — their **existing** cases keep **exact** semantics because `min_sessions` defaults to `0`, `AP-D42-2`), `tests/test_history_backfill_loadpath.py` (the per-timeframe, per-mode session-count guard driving the real load path with a stubbed feed). **Added:** a mode-aware presence suite (`AC-D16.9` (a)/(b)/(c)), a mode-aware cache/migration suite, a **rendered candle-width geometry guard** and a depth-floor/budget suite. `tests/test_d28_4e_bar_cache_retention.py` stays **unchanged** (the flat default is preserved, `S18`) | The D42 correction record names two suites that enshrine the old **width** rule; **five** enshrine the old behaviour in total (`test_candle_spacing.py:4`–`:10`, `test_volume_width.py:103`–`:104`, `test_chart_dpi.py:245`–`:250`, `test_d28_2_sessions.py:166`, `test_d28_4f_panel_bar_cap.py:53`) and the D16 **load-path** suites change by design through `S17`/`S18`. Every change is a **correction to the new normative target**, with the intent of the original test preserved. **`ESC-050` corrected this row's *scope*, not its principle:** the row named 9 D16 sites where the diff changes **14 test functions**, and named no load-path-**driving** suite where **19 assertions in six** change — so the enumeration is now complete **and** generated by the **invariant** + the **call-site enumeration rule** (above), which is what `AR-D42-6`'s mitigation now rests on | (i) delete the enshrining tests — forbidden by the correction record — rejected; (ii) relax the assertions to "no exception raised" — that is exactly the "weakened" failure mode — rejected; (iii) leave `test_chart_dpi.py` alone and let it fail — the suite must be green — rejected |

---

## System Components

**Existing, unchanged** `[existing]`

`services/market_calendar.py` (windows + the ESC-023 New-Year exception), `services/time_collapse_service.py`,
`ibkr/market_data.py::TIMEFRAME_CONFIG` (`S20`), `ibkr/pacing.py`, `ui/candlestick_item.py`'s wick/body
drawing and the D28.4 render split, the D16 no-fill/no-silent-hole rules (`AC-D16.1`/`AC-D16.3`/
`AC-D16.4`), the D27.7 bar-level pass shape, the D28.3 wave pump, `services/session_service.py`, the
drawing/study/alarm overlays — i.e. **nothing D1–D41 depends on is redesigned**.

**New / changed** `[new/changed]`

| Component | Change |
|---|---|
| `ui/candlestick_item.py::capped_body_half_width` | **New pure helper** — the single source of the density-aware cap (`S13`) |
| `ui/candlestick_item.py::CandlestickItem._draw_candles` | Calls the helper (was the unconditional `min_w` clamp, `:136`–`:138`); reads the pitch from the override when present (`S14`) |
| `ui/candlestick_item.py::CandlestickItem.set_data` | Gains the optional `pitch` (`S14`) |
| `ui/chart_panel.py::ChartPanel._compute_candle_half_width` | Also returns/stores the **display-x pitch** (`S14`) |
| `ui/chart_panel.py::ChartPanel._clamp_half_width` | Delegates to the shared helper (was the mirrored 4-px floor, `:1242`–`:1244`) (`S13`) |
| `ui/chart_panel.py::ChartPanel._refresh_candles` / `::_refresh_live_bar` | Pass the pitch (`S14`); the volume width path delegates through `_clamp_half_width` (`S13`) |
| `ui/chart_panel.py::ChartPanel.update_last_bar` | The `_bars` trim (`:1150`–`:1157`) uses the floor-aware budget (`S18`) — the **third** `SESSION_BAR_CAP` site, without which the floor is re-trimmed out of the displayed series on the next new-candle tick. Owned by the same phase as `floor_bar_budget` and **sequenced after** the `ui/chart_panel.py` width edit of the other workstream (`ui/chart_panel.py` is the one shared file; RC-D42-1) |
| `services/backfill_service.py` | **New** mode-aware presence predicate + `floor_bar_budget` + `min_sessions` floor span in `find_missing_spans` (`S15`, `S17`, `S18`) |
| `data/bar_cache.py` | `save_bars`/`get_bars`/`prune` take `ext_hours` (default `True`) (`S16`, `S19`) |
| `data/db.py` | `bars` DDL gains `ext_hours`; `_migrate_schema` gains the guarded table rebuild (`S16`) |
| `ui/ticker_session.py` | Session mode for its own cache reads/writes; the two cap sites use the floor-aware budget (`S18`, `S19`) |
| `ui/main_window.py` | `load_chart` passes the mode + `min_sessions`, the empty-cache branch is removed; `_finalize_history_wave` passes the mode + the derived `keep`; `_missing_backfill_trading_days` uses the shared presence predicate (`S15`, `S17`, `S18`, `S19`) |
| `config/settings.py` | `MIN_INTRADAY_SESSIONS = 30` (`S20`) |

---

## Data Model

| Entity | Status | Key fields / change |
|---|---|---|
| `bars` (SQLite) | **`[new/changed]`** | `+ ext_hours INTEGER NOT NULL DEFAULT 1`; key `(symbol, timeframe, ext_hours, ts)` (was `(symbol, timeframe, ts)`). One guarded table rebuild in `_migrate_schema`; legacy rows → `ext_hours = 1` (`S16`) |
| `Bar` (`data/models.py`) | `[existing]` | **Unchanged** — the mode travels as a parameter, not a field, so the aggregator/overlay/study consumers are untouched (`S19`) |
| `MissingSpan` / `RequestPlan` (`services/backfill_service.py`) | `[existing]` | **Unchanged shape** — the floor is expressed as one more `MissingSpan`, so `plan_requests` needs no change (`S17`) |
| `TickerSession._bars[timeframe]` | **`[new/changed]`** | Cap becomes `floor_bar_budget(timeframe, ext_hours)` (`S18`); the map stays timeframe-keyed because a session loads one mode at a time (`S19`) |
| `ChartPanel._bars` | **`[new/changed]`** | Same floor-aware cap at `ChartPanel.update_last_bar`'s `:1150`–`:1157` trim (`S18`) — the **third** `SESSION_BAR_CAP` site, so the floor survives the next live candle |
| `popouts.ext_hours` | `[existing]` | Already persists the pop-out's mode; now consumed by the cache/planner (`S19`) |
| `footprint_cache` / other tables | `[existing]` | Untouched (D41's drop stands) |

**Migration semantics (recorded):** on an existing user DB the rebuild runs once at the next
`DB()` open; rows are preserved and tagged `ext_hours = 1`. A subsequent **RTH** load therefore
starts from an empty RTH key and issues its own floor fetch — which `AC-D16.8` requires anyway — and
a subsequent **ETH** load reads the legacy rows and re-derives presence by the ETH window. No row is
lost, no hole is created, and no silent re-classification occurs (`AC-D16.9`).

---

## Integration Points

| Integration | Status | Why needed / what changes |
|---|---|---|
| IBKR historical data — `MarketDataManager.req_historical_data(..., useRTH=1, extended_hours=…)` → `IBApiClient.historicalData` | `[existing]` | **Unchanged surface.** The depth floor is delivered as more requests with the **existing** `endDateTime`/`duration`/`bar_size` parameters (`S17`); `extended_hours` already selects the session window, so `AC-D16.8`'s two modes need no new API |
| IBKR pacing (`ibkr/pacing.py::pacing_manager`, `MAX_HISTORICAL_PER_600S = 60`) | `[existing]` | **Unchanged.** A 30-session `1 min` floor is ≤ ~42 `1 D` chunks, within one wave; the remainder defers through `_schedule_wave_continuation`. No new budget accounting (`S17`) |
| SQLite (`config/paths.get_db_path()`, `data/db.py`) | `[existing]` | One new column + one guarded rebuild (`S16`); no new table, no new store, no settings key |
| `services/market_calendar.py::session_windows` | `[existing]` | Now the **single** window authority for presence, the bar-level pass, and the floor arithmetic (`S15`, `S18`) |
| Live TWS / orders / news / burst baseline | `[existing]` | **Untouched** — no D42 path reaches the order machinery or the S0/yfinance surfaces |

---

## Frozen Interfaces

Interfaces this increment treats as **read-only**: already settled and unmodified by any D42 phase.
Contracts are **verbatim** from the tree at `b48133d` (never paraphrased), with the owning module, so
Task Manager can hand a worker the contract instead of the implementation. (D42's revised/new surfaces
— `find_missing_spans`, `BarCache.save_bars`/`get_bars`/`prune`, `ChartPanel.update_last_bar`,
`CandlestickItem.set_data`/`_draw_candles`, `TickerSession.set_bars`/`_append_bar`, `bars` — are
deliberately **not** listed: they are under construction this increment, and freezing them would
freeze a contract `S13`–`S19` change.)

| Interface | Verbatim contract | Owning module |
|---|---|---|
| `session_windows` `[existing]` | `def session_windows(start_ts: int, end_ts: int, ext_hours: bool) -> List[Dict[str, int]]` | `services/market_calendar.py` |
| `plan_requests` `[existing]` | `def plan_requests(missing_spans: Iterable[MissingSpan], timeframe: str) -> List[RequestPlan]` | `services/backfill_service.py` |
| `MissingSpan` `[existing]` | `@dataclass(frozen=True) class MissingSpan: start_ts: int` / `end_ts: int` | `services/backfill_service.py` |
| `RequestPlan` `[existing]` | `@dataclass(frozen=True) class RequestPlan: endDateTime: str` / `duration: str` / `bar_size: str` / `span_start_ts: int` / `span_end_ts: int` | `services/backfill_service.py` |
| `bar_period_seconds` `[existing]` | `def bar_period_seconds(timeframe: str) -> int` | `services/backfill_service.py` |
| `Bar` `[existing]` | `@dataclass class Bar: symbol: str` / `timeframe: str` / `ts: int` / `open: float` / `high: float` / `low: float` / `close: float` / `volume: float` | `data/models.py` |
| `TIMEFRAME_CONFIG` `[existing]` | `{"1 min": {"duration": "1 D", "bar_size": "1 min"}, "5 mins": {"duration": "5 D", "bar_size": "5 mins"}, "15 mins": {"duration": "5 D", "bar_size": "15 mins"}, "1 hour": {"duration": "10 D", "bar_size": "1 hour"}, "4 hours": {"duration": "30 D", "bar_size": "4 hours"}, "1 day": {"duration": "1 Y", "bar_size": "1 day"}}` | `ibkr/market_data.py` (`S20` explicit non-change) |
| `popouts.ext_hours` `[existing]` | `ext_hours INTEGER NOT NULL DEFAULT 1` on the `popouts` table | `data/db.py` |

---

## Non-Functional Approach

- **Correctness over legibility at the limit (from `AC-D6.4`/`AC-D7.1`).** The hard invariant is
  `gap >= 0`; `F` yields to the pitch. The guarantee is unit-consistent by construction because
  `median_diff`, `px_per_sec` and `F` all come from the same display-x series and the same ViewBox
  (`S13`, `S14`) — the property `AC-D6.4`'s "same pixel unit" clause demands. **That shared unit is
  the ViewBox logical px `px_per_sec` yields** (`floor_px = 4.0` logical px = **8 device px at DPR
  2**), so `F` is applied and measured in one unit throughout; the WS1 evidence asserts the unit-free
  relations `body <= pitch` / `body == pitch` and **measures** the repro pitch rather than
  hard-coding the requirement's indicative `3.83` (`RC-D42-3`).
- **Performance (from D28.4 / ESC-013 / ESC-020).** The cap is O(1) per regeneration and adds **no**
  sort: the pitch is cached beside the width (`S14`). The `generate-before-setRange` ordering that
  ESC-013/ESC-020 fixed is **preserved** — the candle picture is still generated *after* the real
  x-range is applied, so the cap reads a real `px_per_sec`. The volume width is still computed from
  the **final** view range (`:1303`), i.e. the same unit as the candle picture.
- **Performance / memory (from `AC-D16.8`).** The floor-aware budget (`S18`) is the **only** new
  memory consumer: ~33,120 bars for a `1 min` ETH chart (**~8–16 MB** — 33,120 `Bar` dataclasses
  without `__slots__` plus the two plot arrays), reached only for `1 min` (both modes) and
  `5 mins` (ETH); `1 day`/`4 hours` keep the flat 5,000. Mitigations: the budget is **per `(symbol, timeframe, ext_hours)`**, only **chart** sessions
  backfill (the D25 headless alarm sessions never request history), the D28.4 static-layer discipline
  (one `QPicture` per full rebuild, forming-bar ticks in the live layer only) is unchanged, and the
  single tunable is `MIN_INTRADAY_SESSIONS`.
- **Pacing (from D28.3, R64).** The floor is emitted **only when short** and collapses to empty once
  filled, so the steady-state cost is zero extra requests; the first load of each
  `(symbol, timeframe, mode)` costs one floor's worth of chained requests, and everything above the
  per-wave cap defers through the existing continuation timer. No new request kind, no sleep, no
  storm.
- **No-silent-hole (from `AC-D16.1`/`AC-D16.4`, unchanged).** A day that is present-but-empty for the
  mode is now a **missing span**, so the AC-D16.4 shortfall line and the WARNING record get *more*
  accurate (a genuine halt / IPO morning that IBKR has no bars for is re-probed and surfaced, never
  fabricated). This is a **user-visible** change to the status text and is recorded as such.
- **Test-suite fidelity (from `R64`; `RC-D42-2`, completed by `ESC-050`).** **Green** is required, but
  count parity is not, and no assertion may be **weakened or deleted**. The D16 **pure-planner** suites
  keep their **exact** semantics (`min_sessions` defaults to `0`). The D16 **load-path** suites change
  **by design** — because the default load mode is **ETH**
  (`ui/main_window.py::MainWindow.ext_hours_btn` checked at `:244`, with the `:1570` fallback) and
  because `S17` removes the empty-cache single-window branch while `S18` changes `prune`'s `keep` — and
  each such assertion is **corrected, intent-preserving**, with its cause named in the plan's correction
  record (`S21`, `AR-D42-6`). **`ESC-050`:** the set is not only the D16 suites — **19 assertions in six
  suites that merely *drive* `MainWindow.load_chart`** change by design too (a fixed-size
  `req_historical_data` stub cannot cover the floor span's many chunks), and they are enumerated in the
  same record. **The invariant** (an **unbounded** reqId source for any test that drives the load path
  with a stubbed feed; exact-request-count and empty-cache-branch assertions change by design) is stated
  so the set is checkable **by rule**, and the generalisable **enumeration rule** — *by call site of the
  changed entry point, not by the suites the design names* — is recorded for future increments.
- **Security / live-order safety.** No D42 path transmits an order, connects to TWS in a test, or
  touches the retained order machinery; `check_live_port` and the confirm dialogs are untouched. No
  new credential, endpoint or dependency.
- **Scalability.** The DB grows by one integer per bar and one floor's worth of rows per
  `(symbol, timeframe, mode)`; `prune` remains per-key and bounded. The graph of loaded chart
  sessions — not the watchlist — bounds the memory cost.

---

## Architecture Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| AR-D42-1 | **The cap is applied to one path only** (candle or volume), so the two diverge — exactly **R63** | H | One shared helper (`S13`) with three call sites, and `AC-D9.1`/`AC-D9.2`-driven tests that measure the **rendered** candle body from the `QPicture` bbox and compare the volume `BarOpts.width` against it (`tests/test_volume_width.py`, corrected) |
| AR-D42-2 | **The enshrining tests are weakened instead of corrected**, so the suite stays green on the bug | H | The correction record (plan proposal) names **each** of the five enshrining suites — and the D16 **load-path** suites — with the intent to preserve; the new geometry guard is **RED pre-fix** (body 4.00 px > 3.83 px pitch) and GREEN post-fix, asserts the unit-free relations (`body <= pitch`, `body == pitch`) and **measures** the repro pitch rather than hard-coding it (`RC-D42-3`); the DPR-2 probe's dense/non-dense split keeps both the `>= F` and the `<= pitch` claims |
| AR-D42-3 | **Floor-aware caps are missed**, so `prune`/the in-memory trim silently deletes the floor after fetching it (`AC-D16.8` unachievable) | H | `S18` + a per-timeframe, per-mode budget guard; **all three** `SESSION_BAR_CAP` sites are converted — including `ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`), the site that would re-trim the **displayed** series on the next live candle — plus `BarCache.prune`'s `keep`; the D28.4 cap suites are corrected to assert the derived budget; the retention suite (flat default) stays green |
| AR-D42-4 | **Chained floor fetches vs pacing** — a `1 min` floor is ~42 `1 D` chunks, consuming most of the 600 s budget; a second symbol/pop-out load defers | M | The floor collapses to empty once filled; the wave cap + continuation timer already handle deferral non-blockingly; the D25 headless sessions are out of the floor's scope; **R64**'s per-mode guard proves the floor is reached without starving the current-session path |
| AR-D42-5 | **Mode-aware cache migration of existing rows** — a wrong tag re-classifies real bars | M | One guarded, idempotent rebuild; legacy rows → `ext_hours = 1` (the app's default fetch mode) with the rationale recorded; **no row deleted**; presence stays window-based, so a mis-tagged row cannot manufacture coverage; a migration test asserts row preservation and per-mode reads |
| AR-D42-6 | **Mode-aware presence changes the AC-D16.4 shortfall text** (more days reported missing), and the D16 **load-path** assertions change **by design** (the floor span, the removed empty-cache branch, the floor-aware prune), so a legitimate correction can read as a regression. **`ESC-050`:** the impact analysis **under-enumerated** the affected set **twice** — the suites that merely **drive** the load path (**19 assertions in six suites**) and **4 further sites** inside the D16 files — and both under-counts surfaced only at reconciliation time, **after** the batch had been dispatched | M | `AC-D16.9` is the normative target; the D16 **pure-planner** suites seed complete days and keep their **exact** expectations (`min_sessions = 0`). **The enumeration is now complete *and* generated by a rule rather than asserted:** `S21` + the plan's correction record name **all 14 changed test functions** in the three D16 files **and the 19 assertions in the six load-path-*driving* suites**, each **with its cause**, and every correction is **intent-preserving** — the guarantee survives, only the expected value/branch changes — never weakened. **The former completeness assertion is replaced by the rule (and is now true as well):** enumerate **by call site of the changed entry point, not by the suites the design names**; treat a **fixed-size stub of a changed feed as a defect class** (grep the suite and correct **all** of them in one scoped task — the `ESC-048`/`ESC-050` pair); and state the **invariant** (`ESC-050`) so completeness is checkable **before dispatch**, not discovered by a reconciliation task. Any residual site not named is covered by the invariant, so the mitigation no longer rests on the enumeration being exhaustive by inspection |
| AR-D42-7 | **The D6 floor interacting with the volume pane / D9 volume math** — a capped `w` shrinks volume bars too, and a zero-volume bar's 1-unit tick could vanish at sub-pixel width | M | `AC-D9.1`/`AC-D9.2`'s note says volume inherits the **same** capped `w`; the zero-volume 1-unit tick and the D21.1/D21.2 ceiling rules are untouched; the dense volume test asserts `volume_width == body_width` and `gap >= 0` |
| AR-D42-8 | **`px_per_sec` is read before the real x-range is applied** (the ESC-013/ESC-020 ordering defect) — the cap would see a default range and mis-yield | M | The cap runs inside the **existing** post-`setRange` generation (`:1291` then `:1318`/`:1326`) and inside `_clamp_half_width` (called at `:1303`, after the auto-range branch); the ordering is explicitly preserved, not re-derived |
| AR-D42-9 | **`TIMEFRAME_CONFIG` is left unchanged** while the brief expected `config/` window edits, so the floor is believed to be "just a constant change" | L | `S20` records the non-change **with its reason** (per-request caps + required chaining); `MIN_INTRADAY_SESSIONS` is the one new constant and the floor's single tunable |
| AR-D42-10 | **Offscreen flakiness / DB contention** (recorded gotcha) masks a real regression | L | Full-suite clean run before declaring green; every non-pytest probe exports `DB_PATH` (ESC-043); the DPR-2 probe stays in its isolated `QT_SCALE_FACTOR=2` subprocess |
| AR-D42-11 | **Scope creep into ESC-041/ESC-037** (BUILD-owned) or into the other open BUILD escalations | M | D42 supplies the normative target only; the Code Reviewer flips ESC-041/ESC-037 after re-verification; ESC-032/033/034/036/043/044/045 are explicitly out of scope |

---

## Requirements → architecture traceability

| Requirement / journey | Architecture section | Phase (plan proposal) |
|---|---|---|
| `AC-D6.4` (revised: `body = min(max(0.65×pitch, F), pitch)`, `body <= pitch`, floor yields at `pitch < F`, wick stays 1 device px; the unit of `F` is the ViewBox logical px `px_per_sec` yields — 4 logical px = 8 device px at DPR 2, `S13`/`AP-D42-5`/`FI-D42-4`) | `S13`, `S14`, `S21`; components `ui/candlestick_item.py`, `ui/chart_panel.py`; AR-D42-1/2/8 | **Phase 1** |
| `AC-D7.1` (revised: `gap >= 0` hard, `> 0` whenever `pitch > F`, `0` acceptable at the limit, 35 % intent unchanged) | `S13`; Journey 8 edge case | **Phase 1** |
| `AC-D9.1` / `AC-D9.2` + note (volume == price body width, same capped `w`) | `S13`; component `ChartPanel._clamp_half_width`/`_refresh_candles`/`_refresh_live_bar`; AR-D42-7 | **Phase 1** |
| `AC-D16.8` (≥ 30 trading sessions, RTH **and** ETH; sessions counted by bars inside the mode's window; all five intraday windows fall short; mode isolation) | `S15`, `S17`, `S18`, `S19`, `S20`; components `services/backfill_service.py` (`floor_bar_budget`), `data/bar_cache.py`, `ui/ticker_session.py`, `ui/main_window.py`, and **`ui/chart_panel.py::ChartPanel.update_last_bar`** (the third `SESSION_BAR_CAP` site, `RC-D42-1`); AR-D42-3/4/9 | **Phase 2** — with the `ui/chart_panel.py` trim **sequenced after** Phase 1's `ui/chart_panel.py` width task (one shared file) |
| `AC-D16.9` (mode-aware day presence + mode-aware cache; present-but-empty = missing span; both directions; measurables (a)/(b)/(c)) | `S15`, `S16`, `S19`; Data Model `bars`; AR-D42-5 | **Phase 2** |
| Journey 7 / Journey 8 edge cases (dense view, high-DPI, doji, single-bar fallback) | `S13`, `S14` | **Phase 1** |
| Journey 17 edge cases (internal hole, no-fill, genuine closures, Ext Hours mode switch, empty cache, all timeframes/any symbol) | `S15`–`S19`; Non-Functional "No-silent-hole" | **Phase 2** |
| `AC-D16.1` / `AC-D16.3` / `AC-D16.4` (unchanged: no fill, genuine closures stay empty, shortfall surfaced) | `S15` (presence only), `S17` (`min_sessions=0` default), Non-Functional | **Phase 2** (non-regression) + **Phase 3** |
| `AC-D16.7` (ESC-023 New-Year exception) | `[existing]` `market_calendar._holidays_for_year`; untouched | **Phase 3** (non-regression) |
| `A72`, `R63`, `R64` | `S13`, `S21`, `S18`, `S17`; risks AR-D42-1/2/3/4/6 | Phases 1–2 |
| D42 correction record (Task Manager / Build / Code Reviewer) | `S21` + the plan proposal's correction record | Phases 1–3 |
| `ESC-050` — the load-path-**driving** suites (19 assertions in six suites) + the **enumeration invariant** and the generalisable **rule** (impact-analysis completeness) | `S21` (invariant + rule), `AR-D42-6`, Non-Functional test-fidelity bullet; the plan proposal's *Corrected — load-path-**driving** suites* table and *Impact-analysis enumeration rule* | Phase 2 (the suites) + Phase 3 (reconciliation) — and **every future increment** |
| D41 (built/committed) — not reopened | Relationship table (no relationship) | — |

---

## Supersessions and non-changes (recorded, never silent)

1. **`AC-D6.4`'s *unconditional* "body remains ≥ 4 device pixels wide"** → superseded by the
   **density-aware** rule (`S13`). The wick clause (cosmetic 1 device px) is **unchanged**.
2. **`AC-D7.1`'s "the gap remains positive"** (and the D7 dense-view edge case) → relaxed to
   **`gap >= 0`** with `gap > 0` whenever `pitch > F`; a **zero** gap at `pitch <= F` is acceptable
   (owner-confirmed **Q51**). The 35 %-gap intent in the non-dense regime is **unchanged**.
3. **The RTH-only default of the depth floor** → superseded: `AC-D16.8`/`AC-D16.9` cover
   `ext_hours=False` **and** `ext_hours=True` (owner-confirmed **Q52**), one floor, two modes, no
   cross-contamination.
4. **D28.4's flat `SESSION_BAR_CAP`/`RETENTION_BARS = 5000` as the universal bound** → revised to a
   **floor-aware budget** (`S18`), the flat values retained as the default/minimum, applied at **all
   three** `SESSION_BAR_CAP` sites (`TickerSession.set_bars` `:300`, `TickerSession._append_bar`
   `:313`, `ChartPanel.update_last_bar` `:1150`–`:1157`) plus `BarCache.prune`'s `keep` (`:1973`).
5. **Explicit non-changes (recorded so they are not read as omissions):**
   `ibkr/market_data.py::TIMEFRAME_CONFIG` durations, `MAX_HISTORICAL_PER_600S`, the D28.3 wave
   pump, `services/market_calendar.py`, `AC-D16.1`/`AC-D16.3`/`AC-D16.4`, the `Bar` dataclass, the
   order machinery, and the D41 removals.

Handoff: this proposal is checked by Plan Artifact Editor & Validator against
`docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`). Companion:
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`).
