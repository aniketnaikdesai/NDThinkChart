# Architecture vs. Code Audit — `docs/architecture.md`

**Owner:** Code Reviewer (ad-hoc user request, outside the pipeline flow).
**Baseline:** `docs/architecture.md` @ commit `286028a` ("Plan review fixes: router state machine,
volume nice-ticks, D2 chip relocation", 2026-09-28). Code @ `fe5a63f` ("Build revision 3",
2026-09-28). Working tree clean.
**Verification:** full offscreen suite re-run by this audit — `383 passed in 6.15s` (exit 0).
**Scope:** every decision row, component contract, state-machine transition (TR-1…TR-17),
data-model statement, and risk mitigation in `architecture.md`, checked against `ui/`, `services/`,
`data/`, `ibkr/`. No file outside `docs/code_review/` was modified.

> This file is a standalone audit artifact. It intentionally does **not** touch
> `review_log.md` or `escalations.md` (the pipeline review is closed at `Status: REVIEW_COMPLETE`,
> all ESC-001…ESC-022 `addressed`).

---

## Top-line verdict

**The design intent matches the code.** Every architectural decision that the document mandates is
implemented as specified — the router state machine (TR-1…TR-17), the D8 pinned nice-number family
and live ceiling, D2/Q33 chip lane, D7/D9 geometry, D10 toggle, D11 labels, D12/D15 dialogs, and
both watchlist behaviours all match. **There is no functional divergence** — no architectural
decision is contradicted by behaviour, and the suite is green.

What differs is almost entirely **documentation state**: `architecture.md` is the Validator-authored
design written *before* Build ran (its own header says "Batch 3–9 D7–D15 planned"), and the code has
since implemented all of it — plus a second wave of reworks (ESC-013, ESC-014, ESC-015, ESC-016,
ESC-017, ESC-020, ESC-021) that post-dates the document and is **not reflected in it**.

**Counts by class**

| Class | Meaning | Items | Needs code fix? |
|---|---|---|---|
| **A** | Stale-doc / expected drift — design intent matches, only tense/status stale | 8 | No — doc-only |
| **B** | Real divergence — code contradicts a mandated decision | 1 | No (behaviour-equivalent; consistency only) |
| **C** | Implemented-but-undocumented — code behaviour with no architectural basis | 4 | No — doc-only |

The one Class-B item (`D-11`) is a documentation-vs-code nuance with **no behavioural difference in
any reachable state**; no `blocking` or `should-fix` findings exist.

---

## Class A — Stale-doc / expected drift (8)

### D-1 — Document frame says D7–D15 are "planned"; they are all built
- **Class / severity:** A / doc-only
- **Architecture claim:** Header line 1 ("Batch 1–2 built; Batch 3–9 D7–D15 planned") and Summary
  lines 5–12 ("**Planned:** Batch 3–9 (D7–D15) …").
- **Code reality:** `docs/tasks/task-graph.json` T1–T36 all `done`; `docs/build/failures.json`
  records 36/36 done, 0 blocked; this audit re-ran the suite: `383 passed`. Every D7–D15 item is
  implemented (see "Confirmed accurate" below).
- **Assessment:** Expected drift — the document is a pre-build design. Design intent unaffected.

### D-2 — Router described as "currently a 51-line tri-boolean router"
- **Class / severity:** A / doc-only
- **Architecture claim:** §Built line 65 — `ui/chart_mouse_router.py` "currently a 51-line
  tri-boolean router (precedence by call order); **to be promoted** to the `RouterMode` state
  machine".
- **Code reality:** `ui/chart_mouse_router.py:31-35` defines `RouterMode`; the file is **271 lines**
  and is the promoted state machine (`:51-115` properties + `_reconcile_mode_from_overlays`,
  `:119-219` intent helpers, `:223-271` guard-clause dispatch).
- **Assessment:** Stale tense — the promotion is done.

### D-3 — `chart_panel` "currently log / inside-plot chip / fixed list" — all superseded
- **Class / severity:** A / doc-only
- **Architecture claim:** §Built line 66 — chip "currently `anchor=(1,0.5)` **inside** the plot (to
  be superseded by D2/Q33); volume `ViewBox` currently log (superseded by D8);
  `_nice_volume_max()` fixed list (to be replaced by the scaling generator)".
- **Code reality:** lane chip `ui/chart_panel.py:462` (`anchor=(0,0.5)`); linear volume
  `:301-305` (`setLogMode('y', False)`); scaling generator `:68-89`.
- **Assessment:** Stale tense — all three superseded.

### D-4 — Candlestick `w = 0.40 → 0.325`
- **Class / severity:** A / doc-only
- **Architecture claim:** §Built line 67 — "`w = median_diff*0.4` (to become `0.325` in D7)".
- **Code reality:** `ui/candlestick_item.py:98` — `w = median_diff * 0.325` (D7 applied).
- **Assessment:** Stale — D7 landed.

### D-5 — "Planned changes (Batch 3–9)" section describes work that is done
- **Class / severity:** A / doc-only
- **Architecture claim:** lines 70–77 list planned edits to router/chart_panel/main_window/
  candlestick/drawing_overlay/watchlist and line 76 declares the dialogs
  "**New dialogs** `[new]`".
- **Code reality:** all implemented — dialogs exist as `ui/zone_settings_dialog.py` and
  `ui/horizontal_line_settings_dialog.py`; watchlist helpers in `ui/watchlist_panel.py:36-83`.
- **Assessment:** Expected drift.

### D-6 — `db.py` duplicate `_init_schema` is **no longer true** (the doc's own "Observation")
- **Class / severity:** A / doc-only **← the explicitly requested check**
- **Architecture claim:** §Data Model lines 216–218 — "`data/db.py` defines `_init_schema` twice
  (lines 14–111 and 113–210); the second shadows the first (tracked as ESC-001, Build-owned).
  Flagged as latent hygiene debt — no behavior change in this run." Repeated in §Architecture Risks
  line 301 ("no change in this run") and referenced at line 5.
- **Code reality:** `data/db.py` is **154 lines** total. `_init_schema` is defined **once**, at
  `data/db.py:14-111`, followed by `_migrate_schema` at `:113-121` (then `_table_columns` at
  `:118`). Repo-wide `grep "def _init_schema"` returns exactly one hit. T26 deduplicated it.
- **Assessment:** Stale — the latent debt the doc flags was resolved by ESC-001/T26. **Doc-only**
  correction needed; no code action.

### D-7 — D11 stacking rule changed to measured-bbox height (ESC-014) — not reflected
- **Class / severity:** A / doc-only
- **Architecture claim:** D12/D11 row line 42 — labels "stacked with a **small vertical offset**
  when nearby"; §Architecture Risks line 291 — "Small vertical offset per overlapping label".
- **Code reality:** `ui/drawing_overlay.py:381-431` (`_update_inner_labels`) stacks by the
  **measured label bbox height**, `offset = max(15.0, height, last_height)` (`:424`), because a real
  ~23 px label overlaps a hard-coded 15 px offset. This is the ESC-014 rework (T33), which post-dates
  the document.
- **Assessment:** Doc drift; intent (non-overlapping labels) preserved. The doc's phrase is now
  inaccurate as an algorithm description.

### D-8 — D12/D15 payload description omits the new `style`/`text`/`visibility` sub-objects
- **Class / severity:** A / doc-only (minor)
- **Architecture claim:** §Data Model lines 207–209 — D12/D15 persist payload JSON
  "horizontal `{"y": …}`, zone `{"x1","x2","y1","y2"}`".
- **Code reality:** the dialogs also write `payload["style"]`, `payload["text"]`,
  `payload["visibility"]` (`ui/zone_settings_dialog.py:137-142`;
  `ui/horizontal_line_settings_dialog.py:80-84`), round-tripped via
  `_load_from_drawing`/`set_*_state`. `normalize_payload` still validates (unchanged), so the extra
  keys are additive.
- **Assessment:** Doc is incomplete but not wrong in behaviour; storage path and tables unchanged.

*(D-6's Risk-table duplicate at line 301 is subsumed above; the A25 process note at line 288 —
"independent Code Reviewer verification after Build, the Batch-1 fix is not assumed" — is likewise
stale process state: that verification was performed and closed in the pipeline via ESC-016/T35.)*

---

## Class B — Real divergence (1)

### D-11 — `view_mouse_click` in `IDLE` omits the documented defensive `not drawing.tool_active()` guard
- **Class / severity:** B / **nice-to-have** (behaviour-equivalent)
- **Architecture claim:** §Router state machine, RC-3 lines 143–145 — "The `IDLE` dispatch
  additionally keeps the existing `not drawing.tool_active()` guard around the alarm-first attempt
  as a defensive tie-break." The dispatch table (lines 100–105) presents the `IDLE` row uniformly
  across press/drag/click.
- **Code reality:** the guard is present in `view_mouse_press` (`ui/chart_mouse_router.py:232`) and
  `view_mouse_drag` (`:248`) but **absent** in `view_mouse_click`, which tests only
  `if self._alarm is not None:` (`:266`).
- **Why it is not a functional defect:** `_active_mode == IDLE` implies
  `_reconcile_mode_from_overlays()` found no `tool_active()` overlay (a drawing tool would have
  forced `DRAWING`, `:107-108`), so the guarded condition and the unguarded one are equal in every
  state the router can actually reach. The only way to reach `IDLE` with `tool_active()` true is to
  mutate `DrawingOverlay._tool` directly without going through the router — not a production path.
- **Assessment:** A literal documentation mandate not mirrored in one of three handlers; no observed
  behavioural difference. Optional tidy-up only — **not** a bug.

---

## Class C — Implemented-but-undocumented (4)

### D-12 — D6/D9 "generate-after-setRange" ordering requirement has no architectural basis
- **Class / severity:** C / doc-only
- **Code reality:** `ui/chart_panel.py:_refresh_candles` applies the real x-range (`vb.setRange`,
  `:827-828`) **before** generating the candle picture (`:860-862`) and derives the volume half-width
  `w_vol` from the **final** view range (`:830-858`) — because the D6 clamp in
  `ui/candlestick_item.py:118-127` reads `ViewBox px_per_sec` at generation time. These are the
  ESC-013 / ESC-020 fixes (T32 / T13).
- **Architecture claim:** D6 (line 37) and D9 (line 40) state the artefacts (cosmetic pen, 4 px
  clamp, `w*2`, shared `w`) but never state the ordering requirement that makes the clamp bind on a
  first (auto-range) load.
- **Assessment:** New contract with no architectural mention; document it (or accept as a bug-fix
  internal to D6/D9). No code action.

### D-13 — Price-chip lane reservation mechanism is undocumented
- **Class / severity:** C / doc-only
- **Code reality:** `ui/chart_panel.py:_reserve_price_tag_lane()` (`:470-488`) reserves Y-axis width
  up-front using a probe `TextItem` of `PRICE_TAG_LANE_SAMPLE = "123,456.78"`, storing
  `_price_lane_width`; `_position_zoom_controls` folds that width into the zoom-controls offset
  (`:389-391`) so the floating controls stay clear of the lane.
- **Architecture claim:** D2/Q33 (lines 34, 42) documents the chip's lane position and tick-overlap
  permission, but not the lane-width reservation or that the zoom cluster accounts for it.
- **Assessment:** Implementation detail not given an architectural basis; add or accept as D2
  refinement. No code action.

### D-14 — ESC-017 draw-combo synchronisation mechanism is undocumented
- **Class / severity:** C / doc-only (minor)
- **Code reality:** when the router clears the drawing tool (TR-4 / TR-17),
  `DrawingOverlay.set_tool(TOOL_CURSOR)` emits `mode_changed("cursor")`;
  `MainWindow._on_drawing_tool_mode_changed` → `_reset_draw_combo_to_cursor()` mirrors it back into
  the toolbar combo with `blockSignals` (`ui/main_window.py:269-274`, `:504-525`).
- **Architecture claim:** TR-4's side-effect list (line 114) documents the *outcome* "uncheck the
  draw combo"; the signal mechanism is not described (the doc predates ESC-017/T36).
- **Assessment:** Outcome documented, mechanism not. No code action.

### D-15 — D9 `y0=0` is implicit (BarGraphItem default), not explicit
- **Class / severity:** C / nice-to-have (minor)
- **Architecture claim:** D9 row line 40 — volume `BarGraphItem` has `y0=0`.
- **Code reality:** `ui/chart_panel.py:858` calls
  `self.volume_bars.setOpts(x=…, height=…, width=w_vol*2, brushes=…)` without an explicit `y0`. The
  installed pyqtgraph default is `y0=None`, which `BarGraphItem._getNormalizedCoords` resolves to
  `0` when `height` is supplied and `y`/`y1` are not
  (`…/pyqtgraph/graphicsItems/BarGraphItem.py:160-168`). Behaviour is therefore `y0=0` as documented.
- **Assessment:** Documented behaviour holds, but only implicitly. No code action.

---

## Confirmed accurate (design intent matches — selected evidence)

These are the decisions checked and **found correct**; listed so the audit is not read as only
catching drift.

| Decision | Architecture ref | Code evidence |
|---|---|---|
| `RouterMode { IDLE, DRAWING, ZOOMING, ALARM_PLACING }`, single `_active_mode` | §Router SM, lines 79–94 | `ui/chart_mouse_router.py:31-35`, `:43` |
| `drawing`/`alarm`/`zoom` properties + `_reconcile_mode_from_overlays()` precedence `DRAWING > ZOOMING > ALARM_PLACING > IDLE`, defensive probes | lines 132–145 | `:51-115` (`_probe` at `:84-100`) |
| Guard-clause dispatch table (IDLE alarm-first→drawing; DRAWING/ZOOMING/ALARM only) | lines 96–105 | `:223-271` |
| TR-1…TR-17 intent helpers | lines 109–127 | `:119-219` (`enter_zoom` `:161`, refuse at `:168-171`; `enter_drawing` `:180`; `enter_alarm_placing` `:201`; `exit_to_idle` `:215`) |
| TR-9 refusal: no mode change, overlay untouched, `zoom_refused` + status bar | lines 119, 147–152 | `:168-171`; `ui/chart_panel.py:697-717`; `ui/main_window.py:276-281` |
| TR-14/15 Esc / right-click cancel selection only, mode stays `ZOOMING` | lines 124–125 | `ui/chart_panel.py:779-786`; `ui/zoom_overlay.py:44-53`; test `test_chart_mouse_router.py::test_esc_cancels_selection_not_mode` |
| Zoom stays active after a completed zoom (AC-D3.2/3.4) | line 64 | `ui/zoom_overlay.py:84-101` (`_active` untouched) |
| D8 pinned family `1/1.5/2/2.5/5/7.5 × 10^k`, floor 100, no ceiling, `>= max*1.1`, `0→100` | lines 39, 154–176 | `ui/chart_panel.py:45-89`; **all 11 worked examples reproduced** by this audit; monotonic + coverage ≤ 2 verified |
| D8 linear Y, `yRange=(0, nice_max)`, price-coloured bars, `500.0K/1.0M` ticks | lines 39, 172 | `:301-305`, `:808`, `:885-896`, `:92-108` |
| Live ceiling O(1) only-widen against cached `_vol_max`; refresh O(N) on load/new bar; `set_timezone` re-applies force | lines 178–192 | `:876-906`; `:664-666`; test `test_volume_ceiling.py` |
| D7 `w = median_diff*0.325`, `0.25` single-bar fallback, `xRange -2*bar_w/+8*bar_w` | lines 38, 74 | `ui/candlestick_item.py:98,100`; `ui/chart_panel.py:827` |
| D6 cosmetic body-coloured wick behind body; ≥4-device-px body clamp | line 37 | `ui/candlestick_item.py:106-107`, `:118-127` |
| D9 `volume_bars.width = w*2`, shared `w`, X-linked | line 40 | `ui/chart_panel.py:842`, `:858`, `:295` |
| D2/Q33 chip `anchor=(0,0.5)`, scene `x >= view_rect.right()`, grey pill `#4b5563`/white text | lines 34, 170 | `ui/chart_panel.py:175-178`, `:462`, `:490-512`; tests `test_crosshair_axis_lane.py`, `test_crosshair_chip_bounds.py` |
| D10 checkable text label `Volume` (no eye icon), top-left of volume panel, default visible, not persisted, rebalances splitter | line 41 | `ui/chart_panel.py:323-335`, `:401-436`; tests `test_volume_toggle.py`, `test_d10_d13_integration.py` |
| D11 inner-right labels `view_rect.right()-4`, `anchor=(1,0.5)`, Z=10, drawing colour, scene-added, label-vs-label stacking | line 42 | `ui/drawing_overlay.py:329-348`, `:309`, `:315-320`, `:381-431` |
| D12 zone dialog: 4 tabs, `Extend` omitted, Border/Middle/Background, `#1/#2 (price,bar)` | line 43 | `ui/zone_settings_dialog.py:31-34`, `:51-109` |
| D15 horizontal dialog: 4 tabs, single `#1 (price)`, Line/12/B/I/Add text/Top/Right | line 44 | `ui/horizontal_line_settings_dialog.py:28-31`, `:45-70`; `ui/drawing_settings_common.py:64-105` |
| D12/D15 8-row Visibility (Ticks + 6 timeframes + Ranges) | lines 43–44 | `ui/drawing_settings_common.py:21-28`, `:135-174` |
| D12/D15 persist via `DrawingStore.update_drawing` | line 224 | `ui/chart_panel.py:355-371`; `ui/main_window.py:535-536` |
| D13 clamp `min(floor(0.50×W), W−400)`, min 150, chart ≥400, `QSettings watchlist/width` default 220, clamp on restore+resize | line 45 | `ui/watchlist_panel.py:36-62`; `ui/main_window.py:221-224`, `:712-723`, `:1132-1140` |
| D13 **floating geometry unconstrained** | line 284 | verified at runtime: a floating dock at 900 px stays 900 px after a main-window resize (Qt `resizeDocks` is a no-op for floating docks) — **matches** |
| D14 `cellDoubleClicked`→uppercased symbol→`load_chart()`; no-op same-symbol / disconnected; header/empty no-op | line 46 | `ui/watchlist_panel.py:65-83`, `:139-145`; `ui/main_window.py:725-741` |
| TR-17 / ESC-010 symbol change → clear draft + router `IDLE` | line 47 | `ui/chart_panel.py:620-634`; `ui/drawing_overlay.py:112-118` |
| Data model: **no schema changes**, table/model set unchanged | lines 204–214 | `data/db.py:15-108` (same 10 tables); no new tables in D7–D15 |
| No new IBKR calls; live-order path untouched | lines 220–229, 257 | `ui/main_window.py` D13/D14 reuse `load_chart()`; no new `placeOrder` sites |
| Testing: pytest + pytest-qt offscreen, no live TWS | line 49 | `tests/conftest.py:5`; suite `383 passed` |
| Existing layers/services/ibkr module lists | lines 53–58 | all modules present on disk (`data/`, `services/`, `ibkr/`, `ui/overlays/`) |

---

## Post-document reworks not reflected in `architecture.md` (umbrella note)

The following were performed **after** the document's last revision (commit `286028a`) and are
**not reflected** in it. They surface above as `D-7` (ESC-014), `D-12` (ESC-013/ESC-020), and
`D-14` (ESC-017); ESC-015/ESC-016/ESC-021 changed tests/docs only, not architecture-relevant
behaviour:

| Rework | Nature | Where it appears in code | Reflected in `architecture.md`? |
|---|---|---|---|
| ESC-013 (T32) | D6 dense-view clamp ordering fix | `ui/chart_panel.py:813-828`, `:860-862` | **No** (see D-12) |
| ESC-014 (T33) | D11 stacking by measured bbox height | `ui/drawing_overlay.py:358-431` | **No** (see D-7) |
| ESC-015 (T34) | test expectation update only | `tests/test_volume_log.py` | n/a |
| ESC-016 (T35) | test assertions retargeted to lane contract | `tests/test_chart_crosshair.py`, `tests/test_crosshair_chip_bounds.py` | n/a |
| ESC-017 (T36) | `draw_combo` sync on router tool-clear | `ui/main_window.py:269-274`, `:504-525` | **No** (see D-14) |
| ESC-020 (T13 rework) | D9 volume-width ordering fix | `ui/chart_panel.py:830-858` | **No** (see D-12) |
| ESC-021 (T13 rework) | D9 test measures rendered body | `tests/test_volume_width.py` | n/a |

The document's own revision stanza (line 14) only claims to carry ESC-002/003/006/007 — correct as
of its revision date, but it predates ESC-013…ESC-021 entirely.

---

## Conclusion

- **Design intent differs from the code at all?** No. Every mandated decision is implemented as
  specified; there is **no behavioural divergence**.
- **What differs is the document's tense/status** (Classes A and C) plus one literal, non-functional
  guard-clause nuance (`D-11`, Class B).
- **Most important finding:** `D-6` — `architecture.md`'s §Data Model "Observation" (lines 216–218)
  and Risk row (line 301) claim `data/db.py` still defines `_init_schema` twice; it does not.
  `_init_schema` is defined once at `data/db.py:14-111` (file is 154 lines; T26/ESC-001 fixed it).
- **No code fix is required** by this audit. All items are documentation drift (`A`/`C`) or,
  for `D-11`, an optional literal-consistency tidy-up with no observable effect. If the team wants
  `architecture.md` to be an accurate description of the current build, it needs an editorial
  revision covering Classes A and C and the post-document reworks; that is a Plan/Validator
  concern, not a Build task.

*No code, `architecture.md`, requirements, plan, or tasks were modified by this audit. Findings are
recorded here rather than in `escalations.md`, per the ad-hoc-request scope.*
