# Implementation Plan Proposal — NDThinkChart Batch 18b (**D42**)

> **Status of this document:** a **proposal** by the Plan agent. It is **not** the canonical plan —
> `docs/plan.md` is written by Plan Artifact Editor & Validator after validation. Companion:
> `docs/architecture_proposal.md` (Codebase Summary first, then decisions `S1`–`S21`, components,
> data model, integrations, non-functional approach, risks `AR-D42-1`–`AR-D42-11`, and the
> requirements→architecture traceability table).
>
> **Run shape:** **legacy single-scope** — the invocation preamble carries no `phase: P<n>`, so these
> are the unsuffixed proposal files and the D42 increment merges into the cumulative canonical
> `docs/architecture.md` / `docs/plan.md` as a `## D42 increment` section (the D16–D41 precedent).
>
> **Scope: D42 only** — a **requirements-decision batch with no new feature**. It resolves the two
> **REQUIREMENTS-routed** Code Reviewer escalations (**ESC-042**, **ESC-038**) and the fixes for the
> two corresponding **BUILD** escalations fall out of it (**ESC-041**, **ESC-037**). `D41` is built,
> reviewed and committed (`b48133d`) and is **not reopened**; `docs/plan_proposal.md`'s stale D41
> draft is **replaced** by this file. Requirements of record: `requirements.md`
> (`Status: READY_FOR_PLAN`, revised 2026-10-15 19:06) — `### D42` (`:3529`–`:3617`),
> `AC-D6.4` (revised), `AC-D7.1` (revised), the `AC-D9.2` note, `AC-D16.8` (extended),
> **`AC-D16.9`** (new), `A72`–`A73`, `R63`–`R64`, `DG68` (resolved) + `DG72`,
> `open_questions.md` **Q51/Q52** (answered 2026-10-15). Baseline: `main` @ `b48133d`, full offscreen
> suite green.
>
> **Revision 2 (2026-10-15) — round 1 of 3, `CHANGES_REQUIRED` addressed.** The Validator ratified
> the substance (`FI-D42-1`–`FI-D42-4` accepted, `S18` ratified, `S13`/`S14` and `S15`–`S19` verified
> sound against source), so **nothing below is re-litigated** — only the three required changes are
> folded in, plus the Validator's own additions:
>
> - **RC-D42-1** — `ui/chart_panel.py::ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`,
>   the **third** `SESSION_BAR_CAP` site) is now **owned by Phase 2**, added to Phase 2's goal /
>   deliverable / file map, and the "**Phase 1 and Phase 2 are file-disjoint / shared files: none**"
>   claim is **replaced** by the correct statement: `ui/chart_panel.py` is the **one shared file**, so
>   the two `ui/chart_panel.py` tasks are sequenced into **different waves** (see *Phases* and the
>   per-file map). `AP-D42-1` is rewritten accordingly.
> - **RC-D42-2** — the D16 **load-path** assertions that `S17`/`S18` legitimately change are now
>   enumerated **with their cause** and stated to be **intent-preserving corrections** (new
>   *Corrected — D16 load-path* table); Phase 3's goal and `R64`'s mitigation wording are re-stated so
>   they are consistent with those changes.
> - **RC-D42-3** — the WS1 RED→GREEN evidence now **states the pixel unit** of `F` (ViewBox logical
>   px, the unit `px_per_sec` yields — 4 logical px = 8 device px at DPR 2), applies `F` in that unit,
>   and **measures** the repro pitch instead of hard-coding `3.83`.
> - Folded in: `FI-D42-2` extended to **five** enshrining suites; `FI-D42-1`'s cost stated as
>   **~8–16 MB**; `FI-D42-3` keeps its ratified reading **with** the `requirements.md:1957`–`:1958`
>   and `:1967`–`:1969` citations; `FI-D42-4`/`AP-D42-5` keep the shipped unit with the unit now
>   **stated** in the evidence; `AP-D42-3`'s "and pop-out charts" corrected.
>
> **Revision 3 (2026-10-16) — reviewer escalation `ESC-050` (PLAN-routed, `open`) addressed.** An
> **enumeration/accuracy fix to the two proposal documents only** — **no architectural decision
> (`S13`–`S21`), no `AC`, no phase boundary, no task and no canonical file changes.** The D42 impact
> analysis **under-enumerated** the suites changed by design in **two independent places**, and both
> under-counts surfaced only at reconciliation time (after the whole batch had been dispatched):
>
> - **(1) the load-path-*driving* suites.** `RC-D42-2`, `S21` and `AR-D42-6` named only the D16
>   **load-path** suites. **19 assertions in six further suites** also change by design —
>   `tests/test_d24_popouts.py` (7), `tests/test_phase3_fixpass.py` (7),
>   `tests/test_d24_alarm_full_chain.py` (2), `tests/test_d24_smoke_gate.py` (1),
>   `tests/test_d24_9_popout_persistence.py` (1), `tests/test_d28_tick_burst_baseline.py` (1) — all
>   because they **drive** `MainWindow.load_chart` with a **fixed-size** `req_historical_data` id
>   iterator while the floor span makes a load issue **many** chunks (the `ESC-048` defect class).
>   New table: *Corrected — load-path-**driving** suites (`ESC-050`)*.
> - **(2) four further sites inside the D16 files** (`t40_t03`, `t40_t05`, `t43_t03`, `t44_t03` —
>   the `P2-T15` footprint flag), plus **two more found by Plan re-verification** against the D42 diff
>   (`t39_t04`, `t39_t05`). The `RC-D42-2` table now names **all 14 changed test functions** in the
>   three D16 files.
> - **(3) the invariant + the generalisable rule.** A new section states the **invariant** (an
>   unbounded reqId stub for any test that drives the load path; exact-count and empty-cache-branch
>   assertions change by design) and the checkable **impact-analysis enumeration rule** — *enumerate by
>   call site of the changed entry point, not by the suites the design names* — which is why the two
>   under-counts happened and how the next increment avoids them.

**The two workstreams.**

- **WS1 — the candle/volume overlap (ESC-042 → unblocks ESC-041).** Rendered body width becomes
  `body = min( max(0.65 × pitch, F), pitch )` (one shared pure helper; `pitch` = inter-bar
  centre-to-centre distance, `F` = the existing 4-px legibility floor, all in the **same** unit);
  **`gap = pitch − body ≥ 0` always**; **`gap > 0` whenever `pitch > F`**; at `pitch ≤ F` bodies may
  **abut** (gap `0`, owner-confirmed Q51); the **wick stays a cosmetic 1-device-px line**; **volume
  inherits the same capped `w`** (`AC-D9.1`/`AC-D9.2` intent unchanged). Sites:
  `ui/candlestick_item.py::CandlestickItem._draw_candles` (the clamp, `:136`–`:138`) and the volume
  width math in `ui/chart_panel.py` (`::_clamp_half_width` `:1229`, `::_refresh_candles` `:1303`,
  `::_refresh_live_bar` `:1352`).
- **WS2 — the RTH/ETH intraday depth + present-but-empty day (ESC-038/ESC-037).** A **≥ 30 trading
  session** floor before the current session for each intraday timeframe in **both**
  `ext_hours=False` (RTH 09:30–16:00 ET) and `ext_hours=True` (ETH 04:00–20:00 ET), delivered as
  **backwards-extending chained fetches** through the existing wave pump; a **session counts only
  with a bar inside the current mode's window**; a **present-but-empty** trading day is a **missing
  span**; the bar cache/key is **mode-aware** in both directions. Sites:
  `services/backfill_service.py`, `data/bar_cache.py`, `data/db.py`, `config/settings.py`,
  `ui/ticker_session.py`, `ui/main_window.py`, and `ui/chart_panel.py` (the floor-aware `_bars` trim
  **only** — the third `SESSION_BAR_CAP` site, `RC-D42-1`).

**Out of scope — do NOT plan these.** The other open BUILD escalations: **ESC-032** (Position `id`),
**ESC-033** (Load Chart button), **ESC-034** (watchlist flash timer), **ESC-036** (priming
`5 secs`), **ESC-043** (`HELD`/`H` rows), **ESC-044** (option contract fields), **ESC-045** (Account
Summary), and — the D42-review follow-ups — **ESC-048** (the six fixed-size stub widenings; blocking),
**ESC-049** (the no-wave ETH session mode) and **ESC-051** (`t40_t01`'s exact-count restore). They are
separate work with no task yet. **ESC-050** is this proposal's own PLAN-routed enumeration fix
(Revision 3). **ESC-041** and **ESC-037** stay BUILD-owned —
D42 supplies the normative target they are re-checked against; D42 does not absorb them (the Code
Reviewer flips them after re-verification, and flips **ESC-038/ESC-042** from `open` on the same
pass). No D42 path reaches the order machinery, the D38/D39 substrate, or the D41 removals.

---

## Phases

Three phases. **Phase 1 and Phase 2 share exactly one file** — `ui/chart_panel.py` — so they are
**not** file-disjoint: Phase 1 edits its **width** path, Phase 2 edits
`ChartPanel.update_last_bar`'s **`_bars` trim** (`:1150`–`:1157`, the **third** `SESSION_BAR_CAP`
site, `RC-D42-1`). The two `ui/chart_panel.py` tasks are therefore **sequenced into different
waves** — Phase 2's trim runs **after** Phase 1's width edit (`build_wave.py` forbids two
`in_progress` tasks with overlapping `touches_files`). Phase 2's **other** files are disjoint from
Phase 1, so those tasks may still co-schedule with Phase 1. **Phase 3 depends on both.**

### Phase 1 — Density-aware candle/volume body width (WS1)

- **Goal:** at any bar density the rendered candle body never exceeds the inter-bar pitch, the
  inter-bar gap is never negative, the 4-px legibility floor still binds whenever the pitch allows
  it, and the volume bar width is the **same** capped width as the price body — while the wick stays
  a cosmetic 1-px line and the D28.4 render split / ESC-013 / ESC-020 ordering is preserved.
- **Covers:** `AC-D6.4` (revised), `AC-D7.1` (revised), the `AC-D9.2` note, Journey 7 and Journey 8
  edge cases; `A72`, `R63`.
- **Requirements/journeys:** Journey 7 (steps 1–2, edge cases "dense 1-min", "doji", "high-DPI"),
  Journey 8 (steps 1, edge case "dense intraday view keeps a **non-negative** gap"), `AC-D6.4`
  (i)/(ii)/(iii) + its measurable paragraph (the repro at ≈ 3.83 **ViewBox logical px** — **measured**,
  not hard-coded — and the ≈ 8.86 logical-px non-dense case; `F = 4.0` in that same unit),
  `AC-D7.1`'s three regimes, `AC-D9.1`/`AC-D9.2`.
- **Dependencies:** none on Phase 2 — but Phase 1's `ui/chart_panel.py` **width** task must complete
  before Phase 2's `ui/chart_panel.py` **trim** task (the one shared file; different waves).
- **Deliverable:** one pure helper + its three call sites (**the `ui/chart_panel.py` width path
  only** — the floor-aware `_bars` trim belongs to Phase 2) + the corrected/added suites (below).

### Phase 2 — Mode-aware intraday depth floor and day presence (WS2)

- **Goal:** each intraday timeframe in each mode loads **≥ 30 trading sessions before the current
  session**; a session counts only when it holds a bar inside the current mode's session window; a
  present-but-empty trading day is reported as a **missing span** (not filled); RTH and ETH never
  cross-contaminate, in the presence pass or in the cache; the floor is actually **retained and
  displayed** (all **three** `SESSION_BAR_CAP` sites become floor-aware — `TickerSession.set_bars`
  `:300`, `TickerSession._append_bar` `:313`, and **`ChartPanel.update_last_bar`'s `_bars` trim
  `:1150`–`:1157`** — plus `BarCache.prune`'s `keep`); and the D16 no-fill / genuine-closure /
  shortfall-report rules are unchanged.
- **Covers:** `AC-D16.8` (extended, both modes), `AC-D16.9` (new, both modes), Journey 17 edge cases
  (internal hole, no-fill, genuine closures, Ext Hours mode switch, empty cache, all timeframes/any
  symbol), `A73`, `R64`, `DG72`; `AC-D16.1`/`AC-D16.3`/`AC-D16.4` as the **non-regression contract**.
- **Dependencies:** **one ordering dependency on Phase 1** — the `ui/chart_panel.py` floor-aware
  `_bars` trim must land **after** Phase 1's `ui/chart_panel.py` width edit (the single shared file,
  so the two tasks sit in different waves). Phase 2's **other** files are disjoint from Phase 1.
  Internally ordered: `floor_bar_budget` must land **before** its consumers (the two session cap
  sites, the panel trim, and `prune`'s `keep`); the presence predicate and the cache key must land
  **before** the floor span is wired (the floor is measured against mode-aware presence).
- **Deliverable:** the mode-aware presence predicate + mode-aware `bars` key/migration + the
  `min_sessions` floor span + the floor-aware caps (**three cap sites + `prune`'s `keep`**) + the mode
  threading + the corrected/added suites.

### Phase 3 — Reconciliation, non-regression and the correction record

- **Goal:** the whole offscreen suite is green, with **every** existing D16/D27/D28/D41 assertion
  either keeping its **exact** expectation or **corrected intent-preserving** to the new normative
  target — **none weakened, none deleted** — and every such correction recorded **with its cause**
  (the floor span, the removed empty-cache branch, the floor-aware prune/budget), the enumeration being
  **complete by rule** rather than by the suites the design happened to name (the `ESC-050` invariant:
  every suite that merely **drives** the changed load path is in scope); the two superseded
  criteria and the three additional artifacts are recorded for Task Manager / Build / Code Reviewer;
  the D42 increment is ready to merge into the canonical docs.
- **Covers:** the D42 correction record; `AC-D16.7` (ESC-023) and `AC-D16.1`/`AC-D16.3`/`AC-D16.4` as
  regression guards; the four escalations' disposition (ESC-041/ESC-037 stay BUILD-owned and are
  re-checked against the revised criteria; ESC-038/ESC-042 are resolved on the requirements side).
- **Dependencies:** **both** Phase 1 and Phase 2 consolidated.
- **Deliverable:** the full-suite green run + the correction-record entries, including the enumerated
  D16 **load-path** corrections and the `ESC-050` load-path-**driving** suite corrections
  (intent-preserving; no new behaviour).

---

## Per-file `touches_files` map and sequencing constraint

**Sequencing constraint (binding).** Build runs a wave frontier: two tasks with overlapping
`touches_files` must never be `in_progress` in the same wave. The partition below **is** the
parallelism plan (one task per file). **The two workstreams share exactly one file —
`ui/chart_panel.py`** (Phase 1: the **width** path; Phase 2: `ChartPanel.update_last_bar`'s `_bars`
trim `:1150`–`:1157`, the third `SESSION_BAR_CAP` site). The two `ui/chart_panel.py` tasks therefore
**must sit in different waves**: Phase 2's trim is **sequenced after** Phase 1's width edit. Every
**other** Phase 2 file (`services/backfill_service.py`, `data/bar_cache.py`, `data/db.py`,
`config/settings.py`, `ui/ticker_session.py`, `ui/main_window.py`) is disjoint from Phase 1, so those
tasks may be co-scheduled with Phase 1's. `ui/main_window.py` stays a **single** Phase-2 task (hot
file); Phase 3 adds no production edit.

### Phase 1 — WS1 file map

| File | Change | Existing tests touching it |
|---|---|---|
| `ui/candlestick_item.py` | New pure `capped_body_half_width(...)`; `_draw_candles` calls it (replacing the unconditional `min_w` clamp, `:136`–`:138`); `set_data(..., pitch=…)` | `tests/test_candlestick_wick.py` (stays green — wick/cosmetic assertions only), `tests/test_candle_spacing.py` (**correct**), `tests/test_chart_dpi.py` (**correct**) |
| `ui/chart_panel.py` | **Width path only** (`RC-D42-1`; the `_bars` trim is Phase 2): `_compute_candle_half_width` also returns/stores the display-x pitch; `_clamp_half_width` delegates to the shared helper; `_refresh_candles`/`_refresh_live_bar` pass the pitch | `tests/test_volume_width.py` (**correct**), `tests/test_chart_dpi.py` (**correct**), `tests/test_d28_4a_render_layers.py`, `tests/test_volume_ceiling.py`, `tests/test_volume_d21.py` (stay green — no width-formula assertions) |
| `tests/test_candle_spacing.py` | **Correct**: string-presence → regime/geometry assertions on the shared helper (`pitch > F`, `pitch == F`, `pitch < F`) while preserving the 0.325 / 35 % intent | — |
| `tests/test_volume_width.py` | **Correct**: the dense `≈ 4.0 px` legs → `body == pitch`, `gap >= 0`, `volume_width == body_width`; the non-dense equality test unchanged | — |
| `tests/test_chart_dpi.py` | **Correct**: the dense `body_device_px >= 4.0` leg moves to the **non-dense** dataset; the dense dataset asserts `body_device_px <= pitch_device_px` (and `== pitch` at the repro) | — |
| `tests/test_d42_candle_width.py` **(new)** | **Add**: the ESC-041 repro geometry guard (192-bar SPY 5-min Ext-Hours, 900 px pane, DPR 2; the pitch is **measured** from the rendered series — ≈ 3.83 **ViewBox logical px**, `F = 4.0` in the **same** unit, i.e. 8 device px at DPR 2) asserting `body <= pitch` and `body == pitch`; and the non-dense case (78 bars, measured pitch ≈ 8.86 logical px → `body == max(0.65×pitch, F) > F`), measuring the body from the `QPicture` bbox. No assertion on `F` in device px (`RC-D42-3`) | — |

### Phase 2 — WS2 file map

| File | Change | Existing tests touching it |
|---|---|---|
| `services/backfill_service.py` | Mode-aware presence predicate (window membership) used by `find_missing_spans` **and** exported for `MainWindow`; `min_sessions` floor span (backwards, collapses when filled); `floor_bar_budget(timeframe, ext_hours)`; empty-cache case returns the floor span when `min_sessions > 0` | `tests/test_backfill_service.py` (**extend** — existing cases keep exact semantics, `min_sessions=0`), `tests/test_d27_backfill_granularity.py` (**extend**), `tests/test_history_backfill*.py` (**correct** — load path) |
| `data/bar_cache.py` | `save_bars`/`get_bars`/`prune` take `ext_hours` (keyword, default `True`); the flat `RETENTION_BARS` stays the default | `tests/test_d28_4e_bar_cache_retention.py` (stays green — flat default preserved), `tests/test_d25_alarm_monitor.py`, `tests/test_d27_phantom_alarms.py`, `tests/test_watchlist_d14_midrag.py` (stays green — default mode) |
| `data/db.py` | `bars` DDL gains `ext_hours`; `_migrate_schema` gains the guarded, idempotent table rebuild (legacy rows → `ext_hours = 1`) | `tests/test_db_schema.py` (**extend**), `tests/test_d42_mode_cache.py` (**new**) |
| `config/settings.py` | `MIN_INTRADAY_SESSIONS = 30` (the floor's single tunable) | — |
| `ui/ticker_session.py` | Session mode for its own cache reads/writes (`get_bars` `:295`, D39 preload `:684`); the two cap sites use `floor_bar_budget(...)` (`:300`, `:313`) | `tests/test_d28_2_sessions.py::test_session_bar_cap` (**correct**), `tests/test_d28_2_sessions.py` (rest green), `tests/test_d39_burst_search.py` (re-verify — the baseline preload path) |
| `ui/chart_panel.py` | **The third `SESSION_BAR_CAP` site (`RC-D42-1`):** `ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`) uses `floor_bar_budget(timeframe, ext_hours)` instead of the flat `settings.SESSION_BAR_CAP`; the head-prune still rebuilds the collapse map + invalidates the study cache. **This task must sit in a different wave from Phase 1's `ui/chart_panel.py` task** (one shared file) and lands **after** `floor_bar_budget` exists | `tests/test_d28_4f_panel_bar_cap.py` (**correct**), `tests/test_d28_4a_render_layers.py` / `tests/test_volume_ceiling.py` (stay green) |
| `ui/main_window.py` | `load_chart`: pass the mode + `min_sessions` at `:1630`/`:1648`/`:1662`; **remove** the empty-cache single-window branch (`:1668`–`:1684`) — which requires bypassing the `find_missing_spans(...) if cached else []` guard at `:1647`–`:1652` and the empty-cache early return at `services/backfill_service.py:205`–`:206` when `min_sessions > 0`; `_finalize_history_wave`: mode at `:1970`/`:1973`/`:1974` + `keep=floor_bar_budget(...)`; `_missing_backfill_trading_days` uses the shared presence predicate (`:2052`–`:2054`) | `tests/test_history_backfill_loadpath.py` (**correct** — the floor span, the removed branch, the floor-aware `keep`), `tests/test_history_backfill.py` (**correct**), `tests/test_history_backfill_disconnect.py` (**correct**), **and — `ESC-050` — the six suites that merely *drive* this load path with a stubbed feed:** `tests/test_d24_popouts.py`, `tests/test_phase3_fixpass.py`, `tests/test_d24_alarm_full_chain.py`, `tests/test_d24_smoke_gate.py`, `tests/test_d24_9_popout_persistence.py`, `tests/test_d28_tick_burst_baseline.py` (**correct** — widen each fixed-size reqId stub to an unbounded `itertools.count`; the invariant below), `tests/test_dock_widths_d17.py` etc. (unaffected — no dock/geometry change) |
| `tests/test_d28_4f_panel_bar_cap.py` | **Correct**: assert the derived budget (monkeypatch/assert against the helper) while keeping the "cap is enforced / oldest dropped" invariant | — |
| `tests/test_d42_day_presence.py` **(new)** | **Add**: `AC-D16.9` measurables (a)/(b)/(c) — pre/post-only day → non-empty **RTH** span and **no** ETH span; RTH-only day → present in **both** modes | — |
| `tests/test_d42_mode_cache.py` **(new)** | **Add**: the migration (rows preserved, tagged, per-mode reads) and no-cross-contamination (write ETH, read RTH → empty, and the reverse) | — |
| `tests/test_d42_depth_floor.py` **(new)** | **Add**: the per-timeframe, per-mode session-count guard — drive the real load path with a stubbed historical feed and assert `≥ 30` distinct mode-valid sessions **before** the current one, for each intraday timeframe in **both** modes; plus the budget guard (the floor survives `prune`/the in-memory trim) | — |

**Shared files across phases: exactly one — `ui/chart_panel.py`.** Phase 1 owns its **width** path;
Phase 2 owns `ChartPanel.update_last_bar`'s floor-aware `_bars` trim (`:1150`–`:1157`, the third
`SESSION_BAR_CAP` site). Those two tasks must be in **different waves** — Phase 2's trim is
**sequenced after** Phase 1's width edit (`RC-D42-1`). Every other file is single-phase:
`ui/candlestick_item.py` is Phase 1 only; `services/backfill_service.py`, `data/bar_cache.py`,
`data/db.py`, `config/settings.py`, `ui/ticker_session.py` and `ui/main_window.py` are Phase 2 only.
Phase 3 adds no production edit (reconciliation + docs only).

---

## Tests: corrected vs added, and the RED→GREEN evidence

**Corrected (never weakened, never deleted — the D42 correction record's mandate).**

| Suite | What is corrected | Why it must change |
|---|---|---|
| `tests/test_candle_spacing.py` | The string-presence check (`"median_diff * 0.325"` / `"gap 35%"` in the source) → **regime/geometry assertions** on the shared helper | It "never renders" (the correction record's words) and cannot distinguish the old unconditional floor from the capped rule |
| `tests/test_volume_width.py` | The dense legs `measured_body * px_per_sec ≈ 4.0` and `vol_width * px_per_sec ≈ 4.0` → `body == pitch`, `gap >= 0`, `vol_width == body_width` | It "asserts body == volume and ~4 px but never relates width to pitch" (the correction record's words); at the revised criterion the dense body is the pitch, not 4 px |
| `tests/test_chart_dpi.py` | The dense `body_device_px >= 4.0` leg → the **non-dense** dataset carries the `>= F` and `> wick` claims; the dense dataset asserts `body_device_px <= pitch_device_px` | **Added by Plan** — the D42 correction record names only the two width suites, but this DPR-2 probe asserts the same **unconditional** floor in device pixels and would fail against the revised criterion |
| `tests/test_d28_2_sessions.py::test_session_bar_cap` | `len(kept) == SESSION_BAR_CAP` → the derived budget for `(timeframe, ext_hours)`, invariant "oldest dropped / newest kept" preserved | **Added by Plan** — `AC-D16.8`'s floor exceeds the flat 5000 for `1 min` (both modes) and `5 mins` (ETH), so the session cap must be floor-aware |
| `tests/test_d28_4f_panel_bar_cap.py` | `len(panel._bars) == settings.SESSION_BAR_CAP` → the derived budget for `(timeframe, ext_hours)`, invariant "oldest dropped / newest kept" preserved | **Added by Plan** — same reason as the session cap, for the **third** `SESSION_BAR_CAP` site (`ChartPanel.update_last_bar`'s `_bars` trim, `:1150`–`:1157`). Its **production subject is Phase 2**, so this correction sits in **Phase 2** too (`RC-D42-1`) |

**Corrected — D16 load-path (`RC-D42-2`).** These change **by design**, because the default load mode
is **ETH** (`ui/main_window.py::MainWindow.ext_hours_btn` checked at `:244`; the `:1570` fallback)
and because `S17` removes the empty-cache single-window branch while `S18` changes `prune`'s `keep`.
Every one is **intent-preserving**: the assertion's guarantee survives, only its expected
value/branch changes — **none weakened, none deleted**.

**`ESC-050` (2026-10-16, PLAN-routed) corrected this table's *scope*, not its principle.** The table
originally named **9** sites; the D42 diff against `b48133d` changes **14 test functions** in the three
D16 files — the **9** named, the **4** `ESC-050` records (`t40_t03`, `t40_t05`, `t43_t03`, `t44_t03`)
and **2** found by Plan re-verification (`t39_t04`, `t39_t05`) — **plus 19 assertions in six further
suites that merely *drive* the load path** (next table). No correction changes; only the enumeration is
now complete, and the **invariant** and the generalisable **impact-analysis enumeration rule** (both
below) replace "the named suites are the whole set".

| Suite / case | Assertion today | Cause of the correction | Intent preserved |
|---|---|---|---|
| `tests/test_history_backfill_loadpath.py::test_t39_t02` (`:238`) | `assert stub.calls == []` | **The floor span** — 5 seeded ETH sessions < 30, so the floor issues requests | "A cache that **satisfies the floor** and reaches *now* issues no **redundant** request" |
| `::test_t39_t03` (`:255`–`:257`) | `len(stub.calls) == 1`, `endDateTime == ""` | **The empty-cache branch `S17` removes** (`ui/main_window.py:1668`–`:1684`) | "An empty cache is covered by the **planner**" — now one floor span from the floor day to *now*, not a special branch |
| `::test_t39_t01` (`:202`/`:206`) | `len(stub.calls) == len(plans)` where `plans` come from the test's own `find_missing_spans(cached_ts, NOW, tf)` (no `min_sessions`) | The load path now passes the floor; the test's own planner call must pass it too | "One request per planned chunk, `endDateTime` non-empty, reqIds tracked" |
| `::test_t39_t06` (`:431`) / `::test_t39_t07` (`:477`) | `assert len(bars) == RETENTION_BARS` | **The floor-aware `keep`** — `5 mins`/ETH derives 6,624 (> 5,000) | The retention invariant at the **derived** budget: oldest dropped, newest kept, no fabricated bar |
| **Added by Plan (re-verification)** — `tests/test_history_backfill_loadpath.py::test_t39_t04` (`:269`) | the `save_bars`/`get_bars` spies declared `def spy_save(bars)` / `def spy_get(s, t)` | **`S19` mode threading** — the load path now passes `ext_hours` to `BarCache.save_bars`/`get_bars`, so the spies must forward it (`**kwargs`) or the forwarded call raises | The spies still count the save/get calls and the bar counts they carry |
| **Added by Plan (re-verification)** — `tests/test_history_backfill_loadpath.py::test_t39_t05` (`:336`) | `assert win._history_req_ids == set()` | **The floor span** — the new session starts its **own** wave (its floor span), so its in-flight id set is not empty | "The cancelled session's ids never leak into the new wave" — `isdisjoint(old_ids)` / `stale not in …` |
| `tests/test_history_backfill.py::test_t40_t01` (`:285`) | `assert len(stub.calls) == 1` | **The floor span** (the seed covers one internal hole only) | The AC-D16.5 hole is filled by its own chunk; the floor is separate work |
| **`ESC-050`** — `tests/test_history_backfill.py::test_t40_t03` (`:362`) | `assert "incomplete" not in msg and "missing" not in msg and "failed" not in msg` | **The floor span** — a floor shortfall **is** now legitimately reported, so "no shortfall message" is wrong | "A genuine closure is never a shortfall" — asserted precisely: the closure days (**2026-09-05/06/07**) are never **named** missing |
| **`ESC-050`** — `tests/test_history_backfill.py::test_t40_t04` (`:451`–`:457` **and** `:480`–`:485`) | `len(wave_calls) == len(plans)` **and** the same "no shortfall message" form | Same as `t39_t01` — **plus** the floor shortfall (`t40_t04` carries **two** corrected assertions) | Multiple requests, continuous result, no silent hole; and "no **answered** day is reported as missing" (the floor's own further-back days may be) |
| **`ESC-050`** — `tests/test_history_backfill.py::test_t40_t05` (`:511`) | the same "no shortfall message" class (see the verification note below) | Same (the floor span) — the correction landed in **`t40_t04`'s tail assertion** | "No **answered** day is reported as missing" |
| `tests/test_history_backfill.py::test_t40_t06` (`:590`) | `len(stub.calls) == 1`, `endDateTime == ""` | **The removed empty-cache branch** | An empty cache renders cleanly from the planner's floor span |
| **`ESC-050`** — `tests/test_history_backfill_disconnect.py::test_t43_t03` (`:227`) | `assert any(date(y, m, d).isoformat() in msg for y, m, d in MISSING_DAYS)` | **The floor span** — the status bar previews only the **first five** missing days (now the floor days), while `_LOG.warning` carries the full list | "Every seeded missing day is surfaced" — asserted against the **log**, and `"incomplete"` is still required |
| **`ESC-050`** — `tests/test_history_backfill_disconnect.py::test_t44_t03` (`:459`) | the same status-message form | Same as `t43_t03` | Same — asserted against the **log**; the timeout/disconnect distinction is kept |
| `tests/test_history_backfill_disconnect.py::test_t43_t06` (`:362`) | `len(stub.calls) == 1` | **The removed empty-cache branch** | The wave finalises once and a later disconnect is a no-op |
| `tests/test_d28_4f_panel_bar_cap.py` (`:53`) | `len(panel._bars) == settings.SESSION_BAR_CAP` | **`S18`**, not the presence predicate — the panel trim is floor-aware | "The cap is enforced / the oldest bars are pruned", asserted against the **derived** budget |

**Verification note on `t40_t05` (`ESC-050` / the `P2-T15` footprint flag).** `ESC-050` names
`t40_t05` among the four extra sites. Re-verified against `git diff b48133d` on the live tree: the
"no shortfall message" → "no **answered** day reported as missing" correction lands in
**`test_t40_t04`'s tail assertion** (`b48133d:484`–`:485`, inside `test_t40_t04`, which spans
`:438`–`:492`) — the very assertion `P2-T15`'s log splits into its `t40_t04`/`t40_t05` rows.
`test_t40_t05` carries **no** shortfall-message assertion in either revision and is green unchanged.
The site is kept in the list (same defect class, and `ESC-050` names it) with the correction located
precisely; `test_t40_t04` therefore carries **two** corrected assertions, and the three D16 files
carry **14** changed test functions in total.

**Corrected — load-path-**driving** suites (`ESC-050`).** These suites are **not** D16 suites and were
enumerated nowhere. They change **by design** for one reason only: each **drives
`MainWindow.load_chart`** (directly or through a pop-out / reconnect / smoke-gate path) while stubbing
`md_manager.req_historical_data` with a **fixed-size** reqId iterator. `S17`'s floor span makes one
intraday load issue **many** chunks (an empty-cache `5 mins` load plans **9**), so the **second**
`next(hids)` raises `StopIteration` — a **fixture-exhaustion** failure, **not** a product defect. The
correction is **test-only** and mechanical: widen each stub to an **unbounded** id source
(`itertools.count(<first>)`, the `P2-T19` precedent at `tests/test_d28_2_sessions.py:41`), leaving
`lambda *a, **k: next(hids)` unchanged so the ids stay deterministic and distinct. **No assertion is
weakened, skipped or xfailed.** (Build-side fix: **`ESC-048`**, BUILD, blocking.)

| Suite | Assertions that change | Cause of the correction | Intent preserved |
|---|---|---|---|
| `tests/test_d24_popouts.py` | **7** | the floor span — the stub was `hids = iter([6101, 6102, 6103])` | Every pop-out/reconnect assertion is untouched; the stub only has to cover **every** request the load path makes |
| `tests/test_phase3_fixpass.py` | **7** | the floor span — `hids = iter([7101, 7102, 7103])` | Same — the `_restore_popouts` no-duplicate behaviour is asserted unchanged |
| `tests/test_d24_alarm_full_chain.py` | **2** | the floor span — `hids = iter([8101, 8102])` | Same — the alarm full chain is asserted unchanged |
| `tests/test_d24_smoke_gate.py` | **1** | the floor span — `hids = iter([9601, 9602])` | Same — the smoke gate is asserted unchanged |
| `tests/test_d24_9_popout_persistence.py` | **1** | the floor span — `hids = iter([7101])` (a **single** id: the first `next` already exhausts it) | Same — the pop-out persistence assertions are unchanged |
| `tests/test_d28_tick_burst_baseline.py` | **1** | the floor span — `hids = iter([9101, 9102])` | Same — the ≤2×/≤5× tick-burst baseline ratio is asserted unchanged |

**Total changed by design: 19 assertions in these six suites + 14 changed test functions in the three
D16 files.** All six suites pass at `b48133d` (pre-D42) and are red post-D42 **only** on the stub
exhaustion — the same mechanism `ESC-048` reports.

**The invariant (`ESC-050`).** Stated so it can be checked **before** dispatch, not discovered by a
reconciliation task:

> **Any test that drives `MainWindow.load_chart` with a stubbed `req_historical_data` must use an
> unbounded reqId source** — `itertools.count(...)`, never a fixed-size `iter([...])` — **because the
> floor span makes a load issue many requests.** Any test asserting the **exact number** of historical
> requests, **one** request/chunk per load, or the **empty-cache single-window branch** changes **by
> design** and belongs in this correction record **with its cause**.

### Impact-analysis enumeration rule (generalisable — `ESC-050`, applies to every future increment)

This is the **second** under-count in this batch (the first was round 1's `FI-D42-2`: the D42
correction record named two enshrining suites where **five** exist). Both had the same cause, so the
rule is recorded rather than the incident:

1. **Enumerate by call site of the changed entry point — not by the suites the design names.** For each
   production symbol the increment changes (here: `MainWindow.load_chart`, `TickerSession.set_bars` /
   `_append_bar`, `BarCache.save_bars` / `get_bars` / `prune`, `ChartPanel.update_last_bar`,
   `find_missing_spans`), find **every** test that reaches it — **including tests that only *drive* it**
   (stub the feed, boot a `MainWindow`, click a toolbar button, restore a pop-out, run a smoke gate)
   and assert something downstream.
2. **The suites the design names are a *seed*, never the answer.** In D42 the seed was the three D16
   suites; the real set was **14 changed test functions in those three files** *plus* **19 assertions
   in six further suites** that merely drive the load path.
3. **A fixed-size stub of a changed feed is a defect *class*, not a one-off.** Grep the whole suite for
   fixed-size stubs of the changed call (`iter([...])` feeding `next(hids)` / `lambda *a, **k: next(...)`)
   and correct **all** of them in one scoped task, before dispatch — the `ESC-048`/`ESC-050` pair.
4. **State the invariant in the correction record** so the enumeration is verifiable by a rule, not by
   re-reading the diff: an enumeration that is asserted to be complete must either **be** complete or be
   replaced by the rule that generates it.


**Re-verified — exact semantics kept:** `tests/test_d39_burst_search.py` (the D39 baseline preload now
passes the mode), `tests/test_backfill_service.py` + `tests/test_d27_backfill_granularity.py` (their
seeds are complete days and `min_sessions` defaults to `0`, so their exact expectations hold; the new
mode-aware cases are additions), `tests/test_d28_4e_bar_cache_retention.py` (flat default preserved).

**Added (new suites).** `tests/test_d42_candle_width.py` (WS1 geometry guard),
`tests/test_d42_day_presence.py` (`AC-D16.9` (a)/(b)/(c)), `tests/test_d42_mode_cache.py`
(migration + no cross-contamination), `tests/test_d42_depth_floor.py` (the per-timeframe, per-mode
session-count guard + the budget guard).

**RED→GREEN evidence each workstream must produce (both runnable offscreen, no live TWS).**

- **WS1 (Phase 1).** **Unit, stated explicitly (`RC-D42-3`):** every width below is in the **ViewBox
  logical-pixel unit that `px_per_sec` yields** (`vb.width() / x_span` — the unit
  `ui/candlestick_item.py:136`'s `min_w = 2.0 / px_per_sec` already uses). `F = 4.0` in that unit is
  **8 device px at DPR 2**; the requirement's literal "4 device pixels at DPR 2" is the same
  legibility intent and `AC-D6.4`'s operative clause is "measured in the **same** pixel unit"
  (`FI-D42-4`/`AP-D42-5`). The requirement's `3.83` / `8.86` figures are **indicative only** (they
  depend on the ViewBox width the probe actually gets), so the test **measures** the repro pitch from
  the rendered series instead of hard-coding it, and the load-bearing assertions are the unit-free
  relations `body <= pitch` and `body == pitch` — **not** `F == 4.0` device px.
  Render the **real** `CandlestickItem` at **DPR 2** for the ESC-041 repro (192 bars, 5-min, Ext
  Hours ON, 900 px pane; pitch ≈ 3.83 logical px, **measured**) and measure the **rendered** body
  from the `QPicture` bounding box (never re-derive the formula): **RED pre-fix** — the body is the
  flat 4.0-logical-px floor, which **exceeds the measured pitch**, i.e. a contiguous zero-gap pixel
  run between adjacent body centres; **GREEN post-fix** — `body <= pitch` (and `body == pitch` at
  this density). Non-dense case (78 bars; pitch **measured**, ≈ 8.86 logical px):
  `body == max(0.65 × pitch, F) > F`, wick still 1 device px. Volume: the rendered candle body and
  `volume_bars.opts['width']` are equal within `rel=0.02` at **both** densities.
- **WS2 (Phase 2).** (a) Seed a trading day with only pre/post bars → `find_missing_spans(cached,
  now, tf, ext_hours=False)` returns a **non-empty** span covering that day's RTH window (**RED
  pre-fix**: returns `[]`), and `ext_hours=True` returns **no** span for that day. (b) Seed a day with
  only RTH bars → **both** the `ext_hours=False` and the `ext_hours=True` calls report it present.
  (c) Drive the real load path with a **stubbed** historical feed and assert the resulting series
  spans **≥ 30** distinct sessions before the current one for each of the five intraday timeframes in
  **both** modes (**RED pre-fix**: `1 min` RTH yields one session — the ESC-038 repro). (d) The floor
  survives retention: after the wave, the cached and in-memory series still hold ≥ 30 mode-valid
  sessions. (e) Mode isolation: a bar set written under `ext_hours=True` is not read as
  `ext_hours=False` coverage and vice versa.

---

## Assumptions

Plan-level assumptions **not** already in `requirements.md`'s Assumptions Log (`A1`–`A73`).

- **AP-D42-1 (Phase 1 and Phase 2 overlap in exactly one file, so they are sequenced there).** The two
  workstreams share **one** file — `ui/chart_panel.py` (Phase 1: the width path; Phase 2:
  `ChartPanel.update_last_bar`'s `_bars` trim, `:1150`–`:1157`). Their two `ui/chart_panel.py` tasks
  therefore sit in **different waves** — Phase 2's trim runs **after** Phase 1's width edit — because
  `build_wave.py` forbids two `in_progress` tasks with overlapping `touches_files`. Every **other**
  file is single-phase, so the remaining Phase 1 / Phase 2 tasks **may** be co-scheduled. The phase
  split is kept because each phase's wave must be individually green. Phase 3 waits for both.
- **AP-D42-2 (`min_sessions` defaults to 0).** The floor is **opt-in per call**, so every existing
  planner suite keeps its exact semantics and the D16 no-fill/no-silent-hole behaviour is unchanged
  when the floor is not requested. `R64`'s "the D16 suite stays green" is met by **exact** semantics in
  the pure-planner suites plus **intent-preserving** corrections in the D16 **load-path** suites
  (enumerated with their cause below) — never by weakening an assertion.
- **AP-D42-3 (the floor is scoped to chart loads).** `AC-D16.8` speaks of the **displayed** series of
  a loaded chart, so the floor is requested by `MainWindow.load_chart` — the primary chart's load
  path (pop-outs **attach a view** to the shared session and issue **no history** of their own,
  `ui/popout_window.py:131`; the pop-out's persisted `ext_hours` reaches the cache only through the
  session it attaches to) — and **not** by the D25 headless alarm-monitor sessions
  (`services/alarm_monitor.py:287`), which never request history. This is a faithful reading, not a
  narrowing — but it is a decision, recorded for the Validator.
- **AP-D42-4 (legacy cache rows are tagged ETH).** Justified by the app's default
  (`ext_hours_btn.setChecked(True)`); no row is deleted; presence stays window-based, so a tag can
  never manufacture coverage; an RTH load after the migration simply performs the floor fetch
  `AC-D16.8` requires anyway.
- **AP-D42-5 (the unit of `F`/`pitch`/`body`).** The requirement says "all in the same pixel unit";
  the shipped clamp's unit is the ViewBox logical-pixel unit that `px_per_sec` yields (which scales
  with DPR at render). The cap keeps **that** unit and the existing `F` constant, so the requirement's
  outcomes hold (`body ≤ pitch` at the repro; `body ≥ F` in the non-dense regime). No requirements
  change is implied. Per `RC-D42-3` the WS1 evidence **states** this unit, applies `F` in it, and
  asserts no `F == 4.0` device-px equality at DPR 2.
- **AP-D42-6 (`TIMEFRAME_CONFIG` is not changed).** Its durations are the **per-request** IBKR caps;
  the depth comes from chaining (`AC-D16.8` itself calls the window strategy a Plan/Build matter).
  `MIN_INTRADAY_SESSIONS = 30` is the one new constant.
- **AP-D42-7 (test invocation + probe isolation).** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m
  pytest` (the `pytest` entry point has a stale shebang); the DPR-2 probe stays in its isolated
  `QT_SCALE_FACTOR=2` subprocess; every non-pytest probe exports `DB_PATH` to a temp file (ESC-043).
- **AP-D42-8 (D41 is not reopened).** No Phase-1/2 file is a D41-removed file, and no D42 path
  touches the retained order machinery or the D38/D39 substrate.
- **AP-D42-9 (the suite total moves).** **Five** enshrining suites, the D16 **load-path** suites and —
  `ESC-050` — the **six load-path-*driving* suites** (19 assertions) are corrected, five are extended
  and four added, so the count changes; the requirement is **green** with every assertion either
  **exact** or corrected **intent-preserving** — not count parity (any docs figure quoting a total must
  be re-measured). The corrected set is **complete by rule** (the `ESC-050` invariant), not by the
  suites the design named.

---

## Flagged Issues

Requirements I could not satisfy with the architecture **as written**, or decisions a Task Manager
could not have made without inventing architecture. Each is surfaced here (not filed): the Validator
turns these into the official `docs/plan_notes.md` escalation.

- **FI-D42-1 — `AC-D16.8`'s floor is unsatisfiable while the D28.4 caps stay at 5000 (decided, needs
  ratification; no Requirements escalation).** A `1 min` RTH session is 390 bars, so 30 sessions =
  **11,700 bars**; `1 min` ETH = **28,800**; `5 mins` ETH = **5,760** — all above
  `config/settings.py::SESSION_BAR_CAP = 5000` and `data/bar_cache.py::RETENTION_BARS = 5000`, which
  would **delete the floor after fetching it**. The requirement is satisfiable, but only by revising
  a D28.4-blessed bound: `S18` makes the caps **floor-aware** (the flat values stay the
  default/minimum) at a memory cost of **~8–16 MB** per loaded `1 min` ETH chart (33,120 `Bar`
  dataclasses without `__slots__`, plus the two plot arrays). This is an architecture
  decision the requirements do not make, so it is recorded rather than assumed. **Disposition
  proposed:** ratified as `S18` (**the Validator ratified it in round 1, independently re-deriving the
  arithmetic and the prune/trim behaviour**); no Requirements escalation (the requirement's *outcome*
  is achievable and unchanged).
- **FI-D42-2 — the D42 correction record's artifact list is incomplete (Plan addition; no escalation).
  **CONFIRMED and EXTENDED by the Validator (round 1): five suites enshrine the old behaviour, not
  two.** The record names `tests/test_candle_spacing.py` (`:4`–`:10`, a source-string check that never
  renders) and `tests/test_volume_width.py` (`:103`–`:104`). **`tests/test_chart_dpi.py:245`–`:250`**
  (`assert body_dev >= 4.0` on the dense 960-bar DPR-2 dataset — **this one will FAIL post-fix**, since
  the capped body ≈ the pitch), **`tests/test_d28_2_sessions.py:166`** and
  **`tests/test_d28_4f_panel_bar_cap.py:53`** enshrine the same old rule. All five are **corrections**
  (the intent preserved), not weakenings; the D16 **load-path** suites (see the *Corrected — D16
  load-path* table) are the same kind of intent-preserving correction. **Disposition proposed:** the
  correction record now names **all five** suites plus the load-path set.
- **FI-D42-3 — `AC-D16.9`'s "RTH bars are ETH coverage" vs the mode-aware cache key (reading
  recorded).** With a strictly mode-keyed cache, an ETH load cannot **see** bars stored under the RTH
  key, so a day covered only by an RTH-mode fetch is **re-fetched** under ETH rather than read as
  present. I read `AC-D16.9`'s measurable (c) as a statement about the **presence predicate** on a
  given bar set (satisfied: RTH bars lie inside the ETH window, so the ETH call reports the day
  present) and **not** a requirement that an RTH-keyed row satisfy an ETH load. The cost is one extra
  fetch per mode switch; there is **no** hole and **no** cross-contamination. **Disposition
  proposed:** ratified as read (**the Validator ratified this reading in round 1**); if a later reader
  takes it otherwise, the alternative (a `'LEGACY'` mode visible to both) is the recorded fallback.
  **Citations:** `AC-D16.9`'s measurable (c) is phrased as a **presence predicate** on a given bar set
  (`requirements.md:1967`–`:1969`: "seed a trading day with **only RTH bars** and assert **both** the
  RTH call and the ETH call report it present (RTH bars lie inside `04:00–20:00 ET`)"), while
  `requirements.md:1957`–`:1958` separately requires the mode-aware key ("The bar cache/key is
  **mode-aware** (RTH vs ETH) … This applies **in both directions**") — the two are satisfied together
  by this reading, which is exactly why the strict mode-keyed cache (`S16`) is consistent with the
  measurable.
- **FI-D42-4 — the `F` unit wording (observation; no escalation).** `AC-D6.4` says "`4` device pixels
  at DPR `2`" while the shipped clamp's constant is 4 px in the ViewBox unit (8 device px at DPR 2).
  The requirement's operative clause is "measured in the **same** pixel unit", so keeping the shipped
  constant and capping in that same unit satisfies the criterion's outcomes. Recorded as `AP-D42-5`
  so the discrepancy is not read as a silent reinterpretation. **RATIFIED in round 1** with `AP-D42-5`
  (the shipped unit is kept; `AC-D6.4`'s "same pixel unit" clause resolves it) — and, per **RC-D42-3**,
  the WS1 evidence now **states** the unit (ViewBox logical px = `px_per_sec`'s unit; 4 logical px = 8
  device px at DPR 2), applies `F` in it, and asserts no `F == 4.0` device-px equality.

---

## Correction record — for Task Manager / Build / Code Reviewer

The two **superseded** criteria and the artifacts that must change (mirrors `### D42`'s correction
record, plus Plan's three additions):

1. **`AC-D6.4`'s *unconditional* "the body remains `>= 4` device pixels wide"** is **superseded** by
   the density-aware rule `body = min( max(0.65 × pitch, F), pitch )`; the wick clause (cosmetic
   1 device px) is **unchanged**. (`F = 4.0` is in the **ViewBox logical-px** unit `px_per_sec`
   yields — 8 device px at DPR 2 — and `AC-D6.4`'s operative clause is "measured in the **same** pixel
   unit"; the shipped constant and unit are kept, `FI-D42-4`/`AP-D42-5`.)
2. **`AC-D7.1`'s "the gap remains positive"** (and the D7 dense-view edge case) is **relaxed to
   `gap >= 0`** — `> 0` whenever `pitch > F`, `0` acceptable at `pitch <= F` (owner-confirmed
   **Q51**); the 35 %-gap intent in the non-dense regime is **unchanged**.
3. **The RTH-only default of the depth floor** is **superseded** — `AC-D16.8`/`AC-D16.9` cover both
   `ext_hours=False` and `ext_hours=True` (owner-confirmed **Q52**), one floor, two modes.
4. **Task Manager:** write the two work items against `AC-D6.4`/`AC-D7.1`/`AC-D9.2` (revised) and
   `AC-D16.8`/`AC-D16.9` (both modes); the phase/file map above is the `touches_files` partition —
   **note the one shared file, `ui/chart_panel.py`**: Phase 1 owns its width path, Phase 2 owns
   `ChartPanel.update_last_bar`'s floor-aware `_bars` trim (`:1150`–`:1157`), and those two tasks must
   sit in **different waves** (Phase 2's trim sequenced after Phase 1's width edit).
5. **Build:** apply the cap in `ui/candlestick_item.py::CandlestickItem._draw_candles` **and** the
   volume width path (`::_clamp_half_width` / `::_refresh_candles` / `::_refresh_live_bar`); make
   `find_missing_spans` (and the exported presence predicate) **mode-aware**; make the bar cache/key
   **mode-aware** (`data/bar_cache.py` / `data/db.py`, keyed `symbol+timeframe+ext_hours`); deliver
   the floor as chained backwards requests and make the floor-aware budget apply at **all three**
   `SESSION_BAR_CAP` sites — `ui/ticker_session.py::TickerSession.set_bars` (`:300`),
   `::TickerSession._append_bar` (`:313`) **and** `ui/chart_panel.py::ChartPanel.update_last_bar`
   (`:1150`–`:1157`, the third site, `RC-D42-1`) — plus `BarCache.prune`'s `keep`; **correct (do not
   merely weaken)** the five enshrining suites named in `S21`/FI-D42-2, the D16 **load-path** suites
   enumerated in the *Corrected — D16 load-path* table (each intent-preserving, its cause named), **and
   — `ESC-050` — the six load-path-*driving* suites** enumerated in the *Corrected — load-path-**driving**
   suites* table (test-only: widen each fixed-size `req_historical_data` reqId stub to an unbounded
   `itertools.count` source; **no assertion weakened, skipped or xfailed** — the production multi-request
   behaviour is requirements-mandated, so do **not** reduce the request count), and add the four new ones.
6. **Code Reviewer:** on the **ESC-041** re-check, verify against the **revised** `AC-D6.4`/`AC-D7.1`
   (a contiguous zero-gap pixel run at pitch ≈ 3.83 px is the failure); on **ESC-037**, verify
   `AC-D16.9` **in both modes** (the RTH-missing / ETH-present split **and** the reverse); **ESC-038**
   and **ESC-042** are resolved on the requirements side by `AC-D16.8`/`AC-D16.9` and
   `AC-D6.4`/`AC-D7.1` and may be flipped from `open` after re-verification. **ESC-041/ESC-037 stay
   BUILD-owned** — D42 does not close them. **`ESC-050`** is this proposal's own enumeration fix (no
   code); the code/test fix it points at is **`ESC-048`** (BUILD, blocking) — the six stub widenings.
7. **Every future increment (`ESC-050` — the enumeration rule, generalisable).** The impact analysis
   must enumerate the assertions an increment changes **by call site of the changed entry point, not by
   the suites the design names** — including the suites that merely **drive** the changed path — and must
   state the **invariant** that generates the enumeration, so the set is checkable by a rule before
   dispatch instead of discovered by a reconciliation task afterwards. D42's two under-counts (round 1's
   `FI-D42-2`: two suites named where five exist; `ESC-050`: the D16 suites named where 14 changed test
   functions **plus 19 assertions in six load-path-driving suites** exist) are the recorded precedents.

---

## Incidentally affected (noted, not absorbed)

- **ESC-041** (candle **and** volume overlap on a 5-min Ext-Hours chart) and **ESC-037** (the
  mode-blind day-presence pass) are the BUILD escalations D42 unblocks; their fixes are Phase 1 and
  Phase 2 respectively, but closing the escalations is the Code Reviewer's action after
  re-verification.
- **ESC-043** (offscreen probes must set `DB_PATH`) is a *test-harness* rule D42's new suites must
  honour, not a D42 work item.
- **DOC-1** (any doc figure quoting a suite total) goes stale again because four suites are added;
  the owner/Analyst follow-up, not a Build task.
- Nothing in D42 touches ESC-032/033/034/036/044/045 or the D41 removals.

---

## Revision 2 — disposition of the round-1 Required Changes (checkable without re-deriving)

| Required change | Disposition | Where to check |
|---|---|---|
| **RC-D42-1** (blocking) — the partition claim is false; an owned edit is missing | **Fixed.** `ui/chart_panel.py::ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`) — the **third** `SESSION_BAR_CAP` site — is now **owned by Phase 2** and appears in Phase 2's goal, dependencies, deliverable and file map, and in `S18`, the System Components / Data Model tables and the traceability row. The "file-disjoint / parallel-safe / shared files: none" claim is **replaced**: `ui/chart_panel.py` is the **one shared file**, and the two `ui/chart_panel.py` tasks are **sequenced into different waves** (Phase 2's trim after Phase 1's width edit). `AP-D42-1` rewritten. The `tests/test_d28_4f_panel_bar_cap.py` correction now sits in the **same phase** as its production subject (`ui/chart_panel.py`, Phase 2) | *Phases* (intro, Phase 1 & Phase 2 blocks), *Per-file `touches_files` map* (both tables + the shared-file paragraph), *Assumptions* `AP-D42-1`, *Correction record* items 4–5; `architecture_proposal.md` `S18`, System Components, Data Model, traceability, AR-D42-3 |
| **RC-D42-2** (blocking) — the "no existing assertion weakened" framing contradicts the plan's own edits | **Fixed.** A *Corrected — D16 load-path* table now names **each** changed assertion with its **cause** (the floor span, the removed empty-cache branch, the floor-aware prune/budget) and states the correction is **intent-preserving** (guarantee survives; only the expected value/branch changes). Phase 3's goal and `R64`'s mitigation are re-worded; the pure-planner suites keep **exact** semantics (`min_sessions = 0`, `AP-D42-2`). `FI-D42-2` records the **five** enshrining suites | *Tests* (the load-path table + the re-verified paragraph), *Phases* Phase 3 goal, *Assumptions* `AP-D42-2`, *Flagged Issues* `FI-D42-2`; `architecture_proposal.md` `S21`, `S17`'s rationale, AR-D42-6, the Non-Functional test-fidelity bullet |
| **RC-D42-3** (required) — the WS1 evidence must not hard-code the unit or the repro | **Fixed.** The WS1 evidence **states the pixel unit** (ViewBox logical px — `px_per_sec`'s unit; `F = 4.0` = 8 device px at DPR 2), applies `F` in that unit, **measures** the repro pitch instead of hard-coding `3.83`, and asserts the unit-free relations `body <= pitch` / `body == pitch` — with an explicit "no `F == 4.0` device px" note. `S13` states the unit; `AC-D6.4`'s traceability row carries it | *Tests* → WS1 evidence; Phase 1's `tests/test_d42_candle_width.py` row; *Assumptions* `AP-D42-5`; `architecture_proposal.md` `S13`, the Non-Functional correctness bullet, AR-D42-2 |
| Fold-in — `FI-D42-2` extended to **five** suites | **Applied** (`test_candle_spacing.py:4`–`:10`, `test_volume_width.py:103`–`:104`, `test_chart_dpi.py:245`–`:250`, `test_d28_2_sessions.py:166`, `test_d28_4f_panel_bar_cap.py:53`) | *Flagged Issues* `FI-D42-2`, *Correction record* item 5; `architecture_proposal.md` Codebase Summary, `S21`, AR-D42-2 |
| Fold-in — `FI-D42-1` cost **~8–16 MB** | **Applied** | *Flagged Issues* `FI-D42-1`; `architecture_proposal.md` Non-Functional memory bullet |
| Fold-in — `FI-D42-3` ratified reading **with** the `requirements.md:1957`–`:1958` and `:1967`–`:1969` citations | **Applied** | *Flagged Issues* `FI-D42-3`; `architecture_proposal.md` `S16`'s rationale |
| Fold-in — `FI-D42-4` ratified; the evidence must **state** the unit | **Applied** | *Flagged Issues* `FI-D42-4`, *Assumptions* `AP-D42-5`, WS1 evidence; `architecture_proposal.md` `S13` |
| Fold-in — `AP-D42-3`'s "and pop-out charts" overstated the callers | **Corrected** — pop-outs attach a view to the shared session and issue no history (`ui/popout_window.py:131`) | *Assumptions* `AP-D42-3` |
| Fold-in — `S17`'s "empty-cache branch is removed" should also name the guards | **Applied** — the `find_missing_spans(...) if cached else []` guard (`ui/main_window.py:1647`–`:1652`) and the empty-cache early return (`services/backfill_service.py:205`–`:206`) are both named | Phase 2's `ui/main_window.py` row; `architecture_proposal.md` `S17` |

**Not re-litigated (the Validator ratified these in round 1):** `S13`/`S14`, `S15`–`S19`, `S18`, and
`FI-D42-1`/`FI-D42-3`/`FI-D42-4`. **No Requirements escalation** was raised then and none is added
now; `docs/plan_notes.md` and `docs/code_review/escalations.json` were not touched.

---

## Revision 3 — disposition of `ESC-050` (checkable without re-deriving)

An **accuracy fix to the two proposal documents**: no architectural decision (`S13`–`S21`), no `AC`, no
phase boundary, no task and no canonical file changed. D42 is built, green and complete (26/26 tasks;
full offscreen suite 1009 passed, exit 0), and its design was verified sound — nothing below re-opens it.

| `ESC-050` item | Disposition | Where to check |
|---|---|---|
| **(1) the six load-path-*driving* suites** (`test_d24_popouts.py` 7, `test_phase3_fixpass.py` 7, `test_d24_alarm_full_chain.py` 2, `test_d24_smoke_gate.py` 1, `test_d24_9_popout_persistence.py` 1, `test_d28_tick_burst_baseline.py` 1 = **19 assertions**) were enumerated nowhere | **Fixed.** New table *Corrected — load-path-**driving** suites (`ESC-050`)* names each suite, its assertion count, the cause (a **fixed-size** `req_historical_data` reqId stub + the floor span's many chunks → `StopIteration`) and the preserved intent; Phase 2's `ui/main_window.py` file-map row and the correction record (item 5) carry the same set | *Tests* → the new table; *Per-file `touches_files` map* → Phase 2 `ui/main_window.py` row; *Phases* → Phase 3 goal + deliverable; *Assumptions* `AP-D42-9`; *Correction record* items 5 and 7; `architecture_proposal.md` Codebase Summary, `S21`, AR-D42-6, Non-Functional test-fidelity bullet |
| **(2) `RC-D42-2`'s own table under-counted the D16 files** — 4 named, 4 more needed correcting (`t40_t03`, `t40_t05`, `t43_t03`, `t44_t03`) | **Fixed, and re-verified.** The table now names **all 14 changed test functions** in the three D16 files: the 9 originally named, the 4 `ESC-050` records, and 2 Plan re-verification adds (`t39_t04`, `t39_t05`). A **verification note** records that `t40_t05`'s correction is in fact `t40_t04`'s **second** corrected assertion (`b48133d:484`–`:485`; `test_t40_t05` carries no shortfall assertion in either revision) — so the enumeration is exact, not merely longer | *Tests* → the *Corrected — D16 load-path* table + the verification note; *Correction record* item 5 |
| **(3) state the invariant** | **Fixed.** Stated verbatim-in-substance (tightened, meaning unchanged) in a dedicated block: *any test that drives `MainWindow.load_chart` with a stubbed `req_historical_data` must use an **unbounded** reqId source; any test asserting the **exact number** of historical requests, **one** request/chunk per load, or the **empty-cache single-window branch** changes by design* | *Tests* → **The invariant (`ESC-050`)**; *Correction record* item 5; `architecture_proposal.md` `S21` |
| **(4) `AR-D42-6`'s mitigation asserts complete enumeration — make it true or replace it by the rule** | **Fixed (both).** The enumeration **is** now complete (14 + 19), **and** the mitigation is re-worded so completeness is a **rule**, not a claim: *enumerate by call site of the changed entry point; the invariant generates the set* — with the two D42 under-counts named as precedents | `architecture_proposal.md` AR-D42-6; *Tests* → **Impact-analysis enumeration rule**; *Correction record* item 7 |
| **(5) generalisable lesson** (the second under-count in this batch) | **Added.** A checkable **impact-analysis enumeration rule** (4 numbered steps) applies to every future increment, and is cross-referenced from Phase 3's goal and the correction record | *Tests* → **Impact-analysis enumeration rule (generalisable …)**; *Correction record* item 7; `architecture_proposal.md` `S21`, AR-D42-6 |
| **Out of scope (not absorbed)** | **`ESC-048`** is the BUILD-side fix (widen the six stubs; blocking) and stays BUILD-owned; **`ESC-049`**, **`ESC-051`** and the seven pre-existing BUILD escalations are untouched. `docs/code_review/escalations.json` was **not** edited (Code Reviewer owns it) | — |

Status: READY_FOR_VALIDATION
