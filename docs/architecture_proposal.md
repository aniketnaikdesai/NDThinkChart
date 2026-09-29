# Architecture Proposal — NDThinkChart Stabilization (revision 2: RC-1…RC-4 fixes, D2/Q33, AC-D3.9)

> Status: `READY_FOR_VALIDATION` (see `docs/plan_proposal.md`).
> This proposal is a **revision of the existing canonical artifacts**
> (`docs/architecture.md`, `docs/plan.md`) triggered by the Orchestrator re-invoking
> Plan for the escalation routed to Plan (`ESC-002`), the companion wording
> escalations (`ESC-003`, `ESC-006`, `ESC-007`), the newly decided D2/Q33 relocation
> and `AC-D3.9`, and the new parallel-build contract (`touches_files` /
> `build_config.json`). It does **not** re-open Batches 1–9 wholesale; it adds the
> missing architectural definitions and rewrites the canonical rows that are now
> superseded. Everything else in the canonical artifacts remains valid and is
> re-affirmed by reference.
>
> **Revision 2** applies the Validator's `CHANGES_REQUIRED` items RC-1…RC-4
> (`docs/plan_review.md`) on top of revision 1. Every item is addressed below, and
> the two requirements escalations (RG-002, RG-003) are now **resolved in
> `requirements.md`** (2026-09-27), so the proposal consumes the settled text.

## 0. What this revision is for (escalation / change cross-reference)

| Escalation or change | Status | Where addressed here |
|---|---|---|
| **ESC-002** — implicit gesture precedence; magnifier vs active drawing undefined | `ESCALATED_TO_PLAN` | §2 (explicit `RouterMode` state machine + transition table, incl. `AC-D3.9`) |
| **RC-1 / ESC-003 / ESC-008 / RG-002** — volume nice-tick family | **RG-002 resolved**; family pinned to `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` | §3 (one family, one formula, every fixture agreeing) |
| **RC-2 / Q33 / A25** — crosshair chip relocated to the Y-axis lane (re-opened D2) | **decided 2026-09-27**; independent Code Reviewer verification required after Build | §5.1–§5.3 (chip relocation + dock-open `AC-D2.1`) |
| **RC-4a / Q31 / A22 / `AC-D10.1`** — D10 affordance is the checkable text label `Volume` | **confirmed** | §5.5 (canonical `architecture.md` D10 row rewrite) |
| **RC-4b / ESC-006** — `view_mouse_click` in `DRAWING`; D11 label re-scope | documented | §2.3 (click change) and §5.4 (`AC-D11.4` label-vs-label) |
| **ESC-007** — `nice_max` stale on intra-bar updates (companion wording) | routed to Build; composition decided in requirements | §4 (corrected live-ceiling statement; O(1) cached running max) |
| **RC-3** — `_active_mode` derivation when overlays are wired directly | fix specified | §2.5 (property setters + `_reconcile_mode_from_overlays()`) |
| **`AC-D3.9` / Q36 option (b)** — magnifier refused during `ALARM_PLACING` | **resolved / required**; supersedes TR-9 + PA-R1 | §2.4 (TR-9 rewritten) |
| **(no escalation)** — `touches_files` + `build_config.json` parallel-build contract | pipeline change | §7 (sequencing consequence) |

Nothing in this proposal invents new requirement ids. Where the requirements are
silent on an implementation detail (not on behaviour), a plan-level assumption
(`PA-R*`) is recorded and flagged in §9.

---

## 1. Codebase Summary (existing-repo mode — map before proposing)

`docs/requirements/requirements.md` states **"This is an existing repository"**, so
all items are labelled `[existing]`, `[new]`, or `[new/changed]`.

### 1.1 Files this revision touches

| Path | State | Relevance |
|---|---|---|
| `ui/chart_mouse_router.py` | `[new/changed]` | `[existing]` 51-line class; three independent overlay pointers (`drawing`, `alarm`, `zoom`) with precedence encoded **only by call order**. No `RouterMode`, no `_active_mode`, no transition table (ESC-002) |
| `ui/zoom_overlay.py` | `[existing]` | `ZoomOverlay.is_active()` / `set_active(bool)` / `cancel()`; owns the rubber-band drag. Consulted by the router per handler |
| `ui/drawing_overlay.py` | `[existing]` | `DrawingOverlay.tool_active()` → `self._tool != TOOL_CURSOR`; `set_tool(tool)` clears the draft (`_clear_draft()`) and emits `mode_changed(str)`; `_clear_draft()` discards in-progress preview items. D11 inner-right labels live here (`:335`, `:342`, `_update_inner_labels` `:358–393`) |
| `ui/alarm_overlay.py` | `[existing]` | `AlarmOverlay.set_alarm_mode(bool)` / `is_alarm_mode()`; press/drag/click handlers |
| `ui/chart_panel.py` | `[existing]` | Owns the router wiring (`self.mouse_router.zoom = self._zoom_overlay`, `:273`; `.drawing`/`.alarm` at `:188–189`), `set_zoom_mode()` (`:538–547`), `set_drawing_tool()`, `set_alarm_mode()`, `is_zoom_active()`, `keyPressEvent` Esc handling; `_nice_volume_max()` (`:45–55`); the volume range site (`:659–671`); the crosshair `_price_tag` (`:379`, positioned `:413–417`); the D10 toggle `_volume_toggle` (a checkable text label `Volume`, RC-4a) |
| `ui/main_window.py` | `[existing]` | `_on_alarm_mode_toggled` forces the drawing combo to `Cursor` (`:662–668`); `_on_draw_tool_changed` unchecks the alarm button (`:478–489`); `magnify_toggled` reaches `ChartPanel.set_zoom_mode` via `chart_panel.py:274`; `status_bar` (`:249–251`) |
| `tests/test_chart_mouse_router.py` | `[existing]` | 5 "precedence" tests that `build(drawing, alarm)` the router by **direct attribute assignment** (`:28–32`) and never set a mode. These remain valid and must keep passing **verbatim** (the RC-3 fence) |
| `tests/test_volume_linear.py` | `[existing]` | Encodes the old fixed-list fixture (`:57–61`). Only `_nice_volume_max(0) == 10_000` (`:57`) conflicts with the pinned family; the rest (`8_000→10_000`, `80_000→100_000`, `2_200_000→2_500_000`, `1_050_000→1_500_000`) stay valid (see §3.4) |
| `docs/architecture.md` | `[new/changed]` | Canonical rows updated by revision 2: the crosshair chip (now the Y-axis lane per D2/Q33) and the D10 toggle (now the checkable text label `Volume`) |

### 1.2 Existing data models / integrations (unchanged)

`Bar`, `Alarm`, `Drawing`, `DrawingGroup`, `Position`, `TradeGroup`,
`OrderBookLevel`, `UserOrder` and all tables are unchanged. No new IBKR calls, no
SQLite schema change, no new external integration. `reDrawings` payloads and
`DrawingStore.normalize_payload` are untouched. The router mode is ephemeral runtime
state; the volume running max is an in-memory field on `ChartPanel`.

### 1.3 Existing patterns to follow

- **`[existing]` overlay-precedence pattern** — a single `ChartMouseRouter` mediates
  ViewBox gestures so pan/zoom/draw/alarm do not fight each other. This revision
  *promotes* that pattern to an explicit state model rather than replacing it.
- **`[existing]` mode-forcing precedent** — alarm mode already forces the drawing
  tool back to `Cursor` (`main_window._on_alarm_mode_toggled` → `draw_combo` →
  `set_drawing_tool("cursor")`). `AC-D3.8`/`AC-D3.9` are the same shape applied to
  zoom, so the state machine must be the single arbiter rather than relying on
  widget-level side effects.
- **`[existing]` pure-function testing pattern** — testable geometry/math lives in
  Qt-free functions (e.g. `_nice_volume_max` is importable and unit-tested directly
  without a `qapp`). The new nice-number generator keeps this shape.
- **`[existing]` offscreen pytest + pytest-qt** — all new tests run with
  `QT_QPA_PLATFORM=offscreen`, no live TWS (Q8/Q9).
- **`[existing]` scene-item chip pattern** — `_price_tag` is a scene `TextItem`
  (`chart_panel.py:379–385`), so it can be positioned in the Y-axis lane without
  affecting auto-range. D2/Q33 keeps this pattern and only changes position, anchor
  and colours.

---

## 2. ESC-002 — Explicit gesture state machine

### 2.1 Problem statement

`ChartMouseRouter` currently resolves precedence **implicitly, three times, one per
handler**, by nesting `if` blocks over three independent booleans:
`ZoomOverlay.is_active()`, `DrawingOverlay.tool_active()`, `AlarmOverlay.is_alarm_mode()`.
Nothing prevents `zoom.is_active()` and `drawing.tool_active()` being true at the
same instant — in fact `ChartPanel.set_zoom_mode(True)` never clears the drawing
tool — so the "precedence" is an accident of statement order, and the draw+zoom
interaction has no defined behaviour or test. `AC-D3.7` (both directions), `AC-D3.8`
and `AC-D3.9` now *decide* those interactions; they need an explicit model to encode.

### 2.2 Decision — one `RouterMode`, one `_active_mode`

Introduce an explicit, single-valued state in `[new/changed] ui/chart_mouse_router.py`:

```python
from enum import Enum, auto

class RouterMode(Enum):
    IDLE = auto()            # default; cursor/pan; alarm & drawing still hit-tested
    DRAWING = auto()         # a drawing tool is armed (draft may be in progress)
    ZOOMING = auto()         # magnifier active; rubber-band selection armed
    ALARM_PLACING = auto()   # alarm placement mode armed
```

- `ChartMouseRouter._active_mode: RouterMode` is the **single source of truth**. An
  enum value is mutually exclusive by construction: `DRAWING` and `ZOOMING` can
  never both be true. This is the architectural fix for ESC-002.
- Every high-level handler (`view_mouse_press`, `view_mouse_drag`, `view_mouse_click`)
  begins with a **guard clause** on `_active_mode` (a `match`/dispatch at the top of
  the method), not with three independent `is_active()`/`tool_active()` probes.
- A **transition table** (§2.4) is the normative specification of mode changes. It
  is implemented as a small `set_mode(...)` / intent API on the router and
  documented in the module docstring so the code and the table cannot drift.
- The existing overlay pointers (`drawing`, `alarm`, `zoom`) are retained as the
  **handlers** the router dispatches to; the overlays keep their own `is_active()` /
  `tool_active()` / `is_alarm_mode()` accessors as implementation detail. Precedence
  is decided **only** by `_active_mode` (with one defensive tie-break, §2.5).

### 2.3 Router mode vs cursor-mode fall-through (important distinction, incl. RC-4b)

`AC-D3.7` requires `ZOOMING` and `DRAWING` to be mutually exclusive. It does **not**
require `IDLE` to mean "nothing handles the gesture". The pre-existing semantics the
existing suite encodes must be preserved:

- In `IDLE`, **alarm gets first refusal** on press/drag (alarm lines are draggable;
  click-to-create works in alarm mode), and a **drawing tool armed at the router
  level** (i.e. `DRAWING`) owns the gesture instead.
- An **alarm miss falls through to drawing**; a **click prefers alarm then drawing**;
  **missing overlays are safe**.

The dispatch inside each handler is a decision over `_active_mode`, not a raw "call
order" chain:

| `_active_mode` | `view_mouse_press` dispatch order | `view_mouse_drag` | `view_mouse_click` |
|---|---|---|---|
| `IDLE` | alarm → drawing (preserves alarm-first, miss-falls-through) | alarm → drawing | alarm → drawing (prefers alarm then drawing) |
| `DRAWING` | drawing only | drawing only | **drawing only** (RC-4b, documented below) |
| `ZOOMING` | zoom only | zoom only | zoom only (returns `False`; view unchanged — `AC-D3.3`) |
| `ALARM_PLACING` | alarm only | alarm only | alarm only |

**RC-4b — documented behaviour change: `view_mouse_click` in `DRAWING`.**
Today `view_mouse_click` (`ui/chart_mouse_router.py:42–51`) tries alarm **then**
drawing with no drawing-active guard. Under mode-based dispatch, `DRAWING` owns click
(`drawing` only). This is **intentional**, not accidental:

- Alarm placement mode is force-cleared whenever a drawing tool is armed
  (`ui/main_window.py:487–489`, `_on_draw_tool_changed` unchecks the alarm button),
  so `ALARM_PLACING`/alarm can never be armed while `_active_mode == DRAWING`.
  Alarm click is therefore unreachable in `DRAWING` in production wiring, and the old
  alarm→drawing click order had no observable effect.
- Routing click by mode is the whole point of ESC-002 (precedence must not depend on
  call order).
- The change is currently untested. Build adds `test_click_in_drawing_reaches_only_drawing`
  (a `DRAWING`-mode click asserts `alarm.calls == []` and `drawing.calls == ["click"]`)
  so the behaviour is pinned rather than silent. `IDLE` click keeps
  `test_click_prefers_alarm_then_drawing` passing unchanged.

The one intentional asymmetry carried over from the existing suite remains: in
`IDLE`, a *click* prefers alarm then drawing, but in `DRAWING` the press is consumed
by the drawing overlay so alarm never sees it. That asymmetry is exactly
`test_click_prefers_alarm_then_drawing` + `test_drawing_tool_blocks_alarm_press`.

### 2.4 Transition table (normative, incl. `AC-D3.9`)

Legend: **from** = `_active_mode` before the trigger; **trigger** = the user action;
**to** = `_active_mode` after; **side effects** = what must happen in the overlays.

| # | From | Trigger | To | Side effects (required) | AC |
|---|---|---|---|---|---|
| TR-1 | `IDLE` | drawing tool selected | `DRAWING` | `drawing.set_tool(tool)`; `zoom.set_active(False)` (already the case); alarm mode off | — (existing) |
| TR-2 | `IDLE` | magnifier toggled on | `ZOOMING` | `zoom.set_active(True)` | AC-D3.2/3.4 |
| TR-3 | `IDLE` | alarm placement activated | `ALARM_PLACING` | `alarm.set_alarm_mode(True)`; drawing tool forced to `Cursor` | — (existing) |
| TR-4 | `DRAWING` | **magnifier invoked** | `ZOOMING` | **cancel the in-progress drawing and discard the draft** (`no half-drawn artefact`); clear the drawing tool; `zoom.set_active(True)`; uncheck the draw combo | **AC-D3.7 forward (Q35 option (a))** |
| TR-5 | `ZOOMING` | **drawing tool selected** | `DRAWING` | **exit `ZOOMING`** (`zoom.set_active(False)` + `zoom.cancel()`); activate the tool | **AC-D3.7 reverse (A26, confirmed)** |
| TR-6 | `ZOOMING` | **alarm placement activated** | `ALARM_PLACING` | **exit `ZOOMING`** (`zoom.set_active(False)` + `zoom.cancel()`); enter alarm placement (**not blocked/deferred by zoom**) | **AC-D3.8** |
| TR-7 | `DRAWING` | alarm placement activated | `ALARM_PLACING` | drawing tool forced to `Cursor` (draft discarded); `alarm.set_alarm_mode(True)` | existing precedent |
| TR-8 | `ALARM_PLACING` | drawing tool selected | `DRAWING` | alarm mode off; `drawing.set_tool(tool)` | existing (`_on_draw_tool_changed` unchecks alarm) |
| **TR-9** | **`ALARM_PLACING`** | **magnifier invoked** | **unchanged (`ALARM_PLACING`)** | **REFUSE:** do **NOT** enter `ZOOMING`; do **not** touch the zoom overlay; the **pending alarm placement is NOT cancelled**; a **status-bar hint** is shown (e.g. "Finish or cancel alarm placement before zooming"); the magnifier control is left **unchecked** | **AC-D3.9 (Q36 option (b))** |
| TR-10 | `DRAWING` | tool set back to `Cursor` | `IDLE` | `drawing.set_tool(TOOL_CURSOR)` | existing |
| TR-11 | `ZOOMING` | magnifier toggled off | `IDLE` | `zoom.set_active(False)` + `zoom.cancel()` | AC-D3.3/3.4 |
| TR-12 | `ZOOMING` | symbol change / timeframe change | `IDLE` | `zoom.set_active(False)` (A6 — already implemented in `set_symbol`/`set_timeframe`) | A6 |
| TR-13 | `ALARM_PLACING` | alarm mode off | `IDLE` | `alarm.set_alarm_mode(False)` | existing |
| TR-14 | any | **Esc during a magnifier drag** | **unchanged** (`ZOOMING`) | `zoom.cancel()` only — the *selection* is cancelled, the **mode stays active** | **AC-D3.3 + AC-D3.4** (sub-state reset, not a mode transition) |
| TR-15 | any | right-click during a magnifier drag | unchanged (`ZOOMING`) | `zoom.cancel()` only (same as TR-14) | AC-D3.3 |
| TR-16 | any | Reset clicked | unchanged | view refit only; mode not changed by Reset | AC-D3.5 |
| TR-17 | `DRAWING` | symbol change (incl. D14 mid-drag double-click) | `IDLE` | clear the drawing draft/drag; reset router mode to `IDLE` (see §6 Phase 4) | AC-D14.4 / D3 edge case |

Notes on the table:

- **TR-4 is the crux of ESC-002.** "Invoking the magnifier while `DRAWING` is active"
  must *cancel the in-progress drawing and discard the draft*, leaving no half-drawn
  artefact. `DrawingOverlay.set_tool(TOOL_CURSOR)` already calls `_clear_draft()`
  (which removes the preview items) and drops `_drag`, so the implementation reuses
  the existing discard path; the *architectural* requirement is that the router must
  perform this transition **before** entering `ZOOMING`, so the two modes cannot
  overlap even for one event.
- **TR-9 is now required behaviour, not an assumption.** `AC-D3.9` (Q36 option (b))
  specifies that the magnifier is **refused** while alarm placement is active: the
  router stays in `ALARM_PLACING`, the pending placement is untouched, and a
  status-bar hint is shown. This **supersedes revision 1's TR-9** (which had entered
  `ZOOMING`) and **retires assumption `PA-R1`**; RG-003 is closed. TR-9 is the final
  cell that makes the transition table **total** for every `(mode, trigger)` pair the
  router exposes.
- **TR-14 is the subtle one.** Because `ZoomOverlay` currently keeps `_active=True`
  after a completed zoom (`AC-D3.4` — "magnifier stays active"), Esc/right-click
  cancel the pending *rectangle*, not the *mode*. The `RouterMode` model must not
  "fix" this by dropping to `IDLE`, or `AC-D3.4` regresses.
- **Totality check.** The four modes × the four user triggers (drawing tool selected,
  magnifier on, magnifier off, alarm on/off) plus Esc/right-click/Reset/symbol-change
  cover the table; there is no `(mode, trigger)` pair left unspecified. In
  particular `ALARM_PLACING + magnifier → ALARM_PLACING` (TR-9) is specified here.

### 2.5 Where the mode is owned and how it is derived (RC-3)

Currently `ChartPanel` holds the overlays and the router pointer, and three separate
`ChartPanel` methods (`set_zoom_mode`, `set_drawing_tool`, `set_alarm_mode`) mutate
one overlay each. That is exactly the shape that lets two modes be true at once.

**Decision:** the router is the **single writer of `_active_mode`**, and `ChartPanel`
routes user intent through it:

- `[new/changed] ChartMouseRouter` gains `set_mode(mode, *, source)` plus small
  intent helpers (`enter_zoom() -> bool`, `enter_drawing(tool)`,
  `enter_alarm_placing()`, `exit_to_idle()`), each of which applies the transition
  table row and mutates the affected overlays. It exposes `active_mode` for tests and
  for UI state sync. `enter_zoom()` returns `False` (and performs no mode change)
  when called in `ALARM_PLACING` — the TR-9 refusal.
- `[new/changed] ChartPanel.set_zoom_mode/set_drawing_tool/set_alarm_mode` become
  thin adapters that call the router intent helpers and then keep the existing
  widget state in sync (magnifier `QToolButton` checked state, drawing `QComboBox`,
  alarm button). They keep their current public signatures so `MainWindow` is
  unchanged apart from the one status-hint connection below.

**RC-3 — explicit derivation/synchronisation for directly-wired overlays.** The five
preserved router tests (`tests/test_chart_mouse_router.py:35–68`) construct the router
with
`router.drawing = drawing; router.alarm = alarm` (`build(...)`, `:28–32`) and **never
call a router intent API or set a mode**. With `_active_mode` defaulting to `IDLE`,
`test_drawing_tool_blocks_alarm_press` would dispatch alarm-first and fail. The
mechanism that reconciles this is pinned as follows (no hidden hot-handler magic):

1. `drawing`, `alarm`, `zoom` become **properties** backed by `_drawing`/`_alarm`/
   `_zoom`. Each **setter** stores the overlay and then calls
   `_reconcile_mode_from_overlays()`. Direct attribute assignment therefore becomes an
   explicit, supported **wiring boundary** — exactly what the preserved tests use.
2. `_reconcile_mode_from_overlays()` derives `_active_mode` with the precedence
   **`DRAWING > ZOOMING > ALARM_PLACING > IDLE`**, probing each overlay defensively
   (e.g. `getattr(overlay, "tool_active", lambda: False)()`), because the test
   `FakeOverlay` implements only `tool_active()`. When called from the real
   `ChartPanel` wiring (`chart_panel.py:188–189`, `:273`) nothing is active yet, so it
   resolves to `IDLE`.
3. Effect on the fence: assigning `router.drawing = FakeOverlay(tool_active=True)`
   sets `_active_mode = DRAWING`; the subsequent `router.alarm = ...` re-derives to
   `DRAWING` (drawing wins the tie-break, consistent with `AC-D3.7` mutual
   exclusivity). `view_mouse_press` then dispatches **drawing only**, so
   `test_drawing_tool_blocks_alarm_press` passes **verbatim**, and
   `test_alarm_press_wins_in_cursor_mode` (tool not active → `IDLE` → alarm first)
   passes too.
4. **Hot handlers do not re-derive the mode.** They dispatch only on `_active_mode`.
   The `IDLE` dispatch additionally keeps the existing `not drawing.tool_active()`
   guard around the alarm-first attempt as a **defensive tie-break** (it mirrors
   today's semantics and makes the fence pass via two independent mechanisms), but
   the mode itself is derived **only** at the property-setter wiring boundary (or an
   explicit `reconcile_mode_from_overlays()` call).
5. Because the router is the single writer, any *later* direct overlay mutation that
   should change the mode (legacy paths) must call the public
   `reconcile_mode_from_overlays()`; the router intent API covers all production
   paths, so no hot path needs it.

`[existing] AlarmOverlay` / `DrawingOverlay` keep their own accessors; the router
calls `is_alarm_mode()` / `tool_active()` / `is_active()` only inside
`_reconcile_mode_from_overlays()` (the wiring boundary), never inside the hot
handlers. `enter_zoom()`'s refusal is surfaced to the user through the `ChartPanel`
adapter: when `set_zoom_mode(True)` is refused, the adapter re-unchecks the magnifier
button (`blockSignals`) and emits a `ChartPanel.zoom_refused` signal that
`MainWindow` connects to `status_bar.showMessage("Finish or cancel alarm placement
before zooming", 3000)` — satisfying `AC-D3.9`'s hint without the router touching any
widget.

This keeps the blast radius small: the overlay classes need no signature changes; the
new logic is concentrated in the router plus the three `ChartPanel` adapters plus one
`MainWindow` connection.

### 2.6 Required named tests (enumerated, not "router precedence tests")

**New (ESC-002 named tests):**
- `test_zoom_during_draw_cancels_draw` — from `DRAWING` with an in-progress draft,
  invoke the magnifier; assert `_active_mode == RouterMode.ZOOMING`, the drawing tool
  is back to `TOOL_CURSOR`, `_draft is None`, and no preview item remains on the plot
  (`AC-D3.7` forward, "no half-drawn artefact").
- `test_draw_blocked_during_zoom` — from `ZOOMING`, select a drawing tool; assert
  `_active_mode == RouterMode.DRAWING`, `zoom.is_active() is False`, and no
  zoom-selection gesture is active (`AC-D3.7` reverse / A26). *(Name retained from the
  escalation even though the confirmed rule is "draw exits zoom"; the assertion
  encodes the confirmed reverse direction.)*
- `test_alarm_placement_blocks_zoom` — from `ZOOMING`, activate alarm placement;
  assert `_active_mode == RouterMode.ALARM_PLACING`, `zoom.is_active() is False`, and
  `alarm.is_alarm_mode() is True` (`AC-D3.8` — alarm placement **blocks/ends** zoom).
- **`test_magnifier_refused_during_alarm_placement`** — from `ALARM_PLACING`, invoke
  the magnifier; assert `enter_zoom()` returns `False`, `_active_mode` is **unchanged
  (`ALARM_PLACING`)**, `zoom.is_active() is False`, the pending alarm placement is
  untouched, and the `zoom_refused` hint fires (`AC-D3.9`). *(New in revision 2;
  test name is a plan-level addition, the behaviour is `AC-D3.9`.)*
- **`test_click_in_drawing_reaches_only_drawing`** — from `DRAWING`, a click dispatches
  to the drawing overlay only (RC-4b).

**Preservation (existing semantics that must not regress — must pass verbatim):**
- `test_alarm_press_wins_in_cursor_mode`
- `test_drawing_tool_blocks_alarm_press`
- `test_alarm_miss_falls_through_to_drawing`
- `test_click_prefers_alarm_then_drawing`
- `test_missing_overlays_are_safe`

**Mode-model tests (new, cheap):**
- `test_router_mode_is_mutually_exclusive` — entering any mode leaves exactly one
  non-`IDLE` mode true (proves the enum replaced three booleans).
- `test_zoom_stays_active_after_completed_zoom` — a completed selection leaves
  `_active_mode == RouterMode.ZOOMING` (`AC-D3.4` must not regress via TR-14).
- `test_esc_cancels_selection_not_mode` — Esc mid-drag resets the sub-state but
  `_active_mode` stays `ZOOMING` (`AC-D3.3` + `AC-D3.4`).
- `test_reconcile_mode_from_wired_overlays` — a router whose overlays are assigned
  directly (never via intents) derives the right mode: `tool_active=True → DRAWING`,
  `is_active=True → ZOOMING`, `is_alarm_mode=True → ALARM_PLACING` (the RC-3
  mechanism itself).

### 2.7 Why not the alternatives

| Alternative | Rejected because |
|---|---|
| Keep the three booleans but document an order | Does not prevent `ZOOMING ∧ DRAWING`; ESC-002 was filed precisely because precedence was implicit. No single value to assert in tests |
| Add a 3-state `(zoom, draw, alarm)` tuple + `assert sum(...) <= 1` | Equivalent safety, but the transition table (`AC-D3.7`/`AC-D3.8`/`AC-D3.9`) becomes a matrix over 8 states with unreachable combinations; the enum is smaller and self-documenting |
| Make the overlays mutually aware (each checks the others) | N×N coupling; the router exists to prevent exactly this |
| Re-derive `_active_mode` inside every hot handler | Works for the fence but makes precedence implicit again (the original defect) and adds per-event work; RC-3 pins derivation at the wiring boundary instead |
| Use `QActionGroup` (exclusive actions) for the toolbar only | Fixes the *widget* state, not the *gesture routing*; the overlays can still both be armed programmatically |

---

## 3. ESC-003 companion — scaling nice-tick formula (RC-1 rewrite)

### 3.1 Current state and the problem

`[existing] ui/chart_panel.py::_nice_volume_max` (`:45–55`) is a **fixed list**
`[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]` with a
coarse fallback `((target // 5_000_000) + 1) * 5_000_000` above 10M and a hard
`10_000` floor. Above 10M the steps are coarse (`10.5M→15M`, `45M→50M`,
`50M→60M`); below 10k the floor flattens low-volume symbols
(`_nice_volume_max(800) == 10_000`). This is `AC-D8.1`/`AC-D8.4`/`AC-D8.5`
territory. RG-002 resolved the family conflict in the requirements on 2026-09-27.

### 3.2 Decision — one family, one formula: `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`

Replace the fixed list with a **single scaling "nice number" formula** with **no
fixed ceiling and no 10K floor**. This is the family **pinned by RG-002**
(`AC-D8.1`, `A24`), reproduced here as the one and only candidate set:

- **Candidate family (mantissas):** `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` for integer
  `k`. `10 × 10^k` is the next decade's `1` and needs **no separate mantissa**. The
  generator is **floored at `100`** (`AC-D8.4`/A24: "smallest generated value `100`"),
  i.e. candidates below `100` are not generated; the effective domain is
  `k >= 2`, so the smallest output is **`100`** (`1 × 10^2`). The old `10k` floor is
  gone, but the `100` floor remains.
- **Formula (one formula):** `nice_max = min { v in family, v >= 100 : v >= max_vol * 1.1 }`,
  i.e. the **smallest** generated family value that is `>= max_vol * 1.1`. Special case
  `max_vol == 0` → the smallest generated value **`100`** (`AC-D8.4`).
- The generator is a **pure, importable function** (same shape as today's
  `_nice_volume_max`) so it is unit-testable without a `qapp`.
- **Coverage property (testable):** for `max_vol` where the ceiling is **above the
  `100` floor** — i.e. `max_vol * 1.1 >= 50`, equivalently `max_vol >= 100 / 2.2 ≈ 45.5`
  — `nice_max / (max_vol * 1.1) <= 2`. (Worst case is the `2.5 → 5` step: a target just
  above `1.1 × 2.5` rounds to `5`, giving a ratio `≈ 5 / (1.1 × 2.5) ≈ 1.82`.)
  Below that threshold `nice_max` is the required floor `100`, so the ratio can exceed
  `2` for tiny `max_vol` — that is the requirement's own floor (`AC-D8.4`), not a
  formula violation. `nice_max` is monotonic non-decreasing in `max_vol` across the
  whole domain.
- **Values to preserve:** the validated axis set from the Q20 reference — the
  `0, 500.0K, 1.0M, 1.5M, 2.0M, 2.5M`-style ticks and the `500.0K / 1.0M` formatter
  (`AC-D8.3`) stay exactly as the canonical architecture specifies. The 1.5M tick is
  now a **member of the pinned family** (not a separate axis-ticker-only value).

**The confirmed set is a subset of the family.** Every value in the previously
shipped fixed list is a member of `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`:
`10K (1×10^4)`, `50K (5×10^4)`, `100K (1×10^5)`, `250K (2.5×10^5)`, `500K
(5×10^5)`, `750K (7.5×10^5)`, `1M (1×10^6)`, `1.5M (1.5×10^6)`, `2M (2×10^6)`,
`2.5M (2.5×10^6)`, `5M (5×10^6)`, `10M (1×10^7)`. The old list is therefore
consistent with the pinned family — it was only **coarse** (it omitted `1.5`, `2`,
`7.5` at some decades and had a `10K` floor and a `5M` fallback).

**Worked examples (all agree with the one formula):**

| `max_vol` | `max_vol × 1.1` | `nice_max` | Note |
|---|---|---|---|
| `0` | — | **`100`** | smallest family value (`AC-D8.4`) |
| `800` | `880` | **`1_000`** | `AC-D8.4` (`nice_max(800) = 1000`) |
| `3_000` | `3_300` | **`5_000`** | `2_500 < 3_300 ≤ 5_000` |
| `8_000` | `8_800` | **`10_000`** | fixture stays valid |
| `10_000` | `11_000` | **`15_000`** | no longer jumps to `50_000` |
| `80_000` | `88_000` | **`100_000`** | fixture stays valid |
| `1_050_000` | `1_155_000` | **`1_500_000`** | RG-002 contested case — **valid** under the pinned family |
| `2_200_000` | `2_420_000` | **`2_500_000`** | fixture stays valid |
| `10_500_000` | `11_550_000` | **`15_000_000`** | `AC-D8.5` |
| `45_000_000` | `49_500_000` | **`50_000_000`** | `AC-D8.5` |
| `50_000_000` | `55_000_000` | **`75_000_000`** | `AC-D8.5` (the `7.5` mantissa is exactly why the family keeps it) |

The `50M → 75M` case is the reason the family includes `7.5`: strictly
`{1, 2, 2.5, 5}` would overshoot `50M` to `100M`, which `AC-D8.5` rejects.

### 3.3 Fixture retention (ESC-003, RC-1)

The **original fixed list is retained only as a test fixture** — a module-level
constant in `tests/` (e.g. `_LEGACY_NICE_LIST`) used to assert that the generator
reproduces every member of the confirmed set and the RG-002-contested answer:
`80_000 → 100_000`, `8_000 → 10_000`, `2_200_000 → 2_500_000`,
`1_050_000 → 1_500_000`. It must **not** remain a live code path. Because every
legacy value is a family member, this cross-check is consistent with §3.2 — there is
**no** retained fixture that contradicts the formula.

### 3.4 Consequence for the existing test file (flagged)

`tests/test_volume_linear.py:57–61` asserts:

- `_nice_volume_max(0) == 10_000` — **stale**: must become **`100`** (`AC-D8.4`, no
  `10k` floor). This is the **only** Build-owned test edit.
- `_nice_volume_max(8_000) == 10_000` — **stays valid** (`8_000 × 1.1 = 8_800 → 10_000`
  under the pinned family).
- `_nice_volume_max(80_000) == 100_000` — **stays valid**.
- `_nice_volume_max(2_200_000) == 2_500_000` — **stays valid**.
- `_nice_volume_max(1_050_000) == 1_500_000` — **stays valid** (the RG-002 case; now
  consistent because the family includes the `1.5` mantissa).

This is a deliberate, requirement-backed test change for the single stale floor
assertion, not a "silently change a test to make it pass" (Journey 1 edge case). The
old proposal's claim that the `(8_000) == 10_000` assertion also had to change was
**wrong** and is corrected here.

---

## 4. ESC-007 companion — live-ceiling exception (corrected statement)

### 4.1 The inaccurate canonical claim

The pre-revision `docs/architecture.md` (performance section) read:

> **Performance:** `w` and `nice_max` are O(N) per data load over bars (**not per
> intra-bar tick**); dialogs are created on demand; labels are bounded by drawing count.

The *first half* is true (`nice_max` is computed once per `update_chart`). The
parenthetical **"not per intra-bar tick"** is **misleading**: the volume Y ceiling
currently is set only under `if auto_range:` inside `_refresh_candles`
(`:659–671`), and `update_last_bar` (`:584–600`) calls `_refresh_candles()` with
`auto_range=False`. Therefore the ceiling **never updates** as the forming bar's
volume grows, and once the live volume passes the initial `nice_max` the tallest bar
is **clipped**. So the ceiling is "per data load" *by omission*, and that omission is
the defect (`AC-D8.6`, `AC-D8.7`).

### 4.2 Corrected architecture statement (this is the wording to carry into `architecture.md`)

> **Performance / volume auto-range (revised).** `w` (candle body half-width) is
> computed **O(N) once per data load**, and the volume `nice_max` is computed **O(N)
> once per data load** from `max(bar.volume)` using the §3 `1 / 1.5 / 2 / 2.5 / 5 /
> 7.5 × 10^k` generator — **with one explicit exception**: because the **forming last
> bar's volume grows live**, the volume Y ceiling must track the live maximum or the
> tallest bar is clipped (`AC-D8.6`). The ceiling is therefore **also updated on
> real-time volume changes**, but that update is **O(1) against a cached running
> max**, not O(N) over the bar list per tick. Concretely: keep a cached `_vol_max`
> (the load-time maximum) plus the live bar's volume; on an intra-bar tick compute
> `live_max = max(cached_max, last_bar.volume)` and **only widen** the ceiling when
> `live_max` crosses the current `nice_max` (monotonic non-decreasing within a load,
> so a tick that does not cross a boundary performs no range write at all). On a new
> bar / new load, `_vol_max` is refreshed O(N) as before. This is the **documented
> exception** to the per-load rule; it is bounded (one comparison per tick, at most
> one `nice_max` recompute per boundary crossing) and it never clips the forming bar
> (`AC-D8.6`).

### 4.3 Design notes

- **Monotonic widening is deliberate.** `AC-D8.6` says "recomputed/**widened**" and
  requires the rendered height `<=` pane top and `> 0`. Only-widen avoids the pane
  visibly rescaling on every tick (a jitter regression) while guaranteeing no
  clipping. The trade-off — the ceiling can stay one step above the final max until
  the next load — is acceptable and is exactly the "explicitly documented" option
  the escalation permits instead of recomputing every tick.
- **Interaction with `auto_range=False` paths.** `set_timezone()` calls
  `_refresh_candles()` with `auto_range=False` (`AC-D8.7`). After the cached
  `_vol_max` exists for the current bars, that path must re-apply the cached ceiling
  (so the axis is not left stale after an axis rebuild) — the `AC-D8.7` requirement
  is satisfied by having the volume-range application read from the cached state
  rather than being gated on `auto_range`.
- **No O(N) per tick anywhere.** The running max is updated in `update_last_bar`
  with the single new bar, so the hot path is O(1). A full O(N) recompute happens
  only on `update_chart` (new load/new symbol), and the ceiling value it produces
  comes from the §3 generator.

### 4.4 Required tests (named)

- `test_volume_ceiling_tracks_live_bar` — load bars whose initial `nice_max` is
  computed from a small max, then feed `update_last_bar` with a volume that doubles
  past the ceiling; assert the volume `ViewBox` upper bound **grew** and the forming
  bar's rendered height is `> 0` and `<=` the pane top (no clipping). This is the
  measurable form of `AC-D8.6`.
- `test_volume_ceiling_refit_on_timezone_refresh` — call `set_timezone()` (an
  `auto_range=False` path) after a load and assert the volume Y range still matches
  the current `nice_max` (`AC-D8.7`).

---

## 5. Re-opened / re-scoped surfaces and canonical-doc corrections (RC-2, RC-4a)

### 5.1 Root problem — D2 was re-opened by Q33 (2026-09-27)

`requirements.md` D2 was revised 2026-09-27: the crosshair price chip moves to the
**Y-axis lane outside the plot** (right of the plot's vertical axis line), as a
**grey pill with white text**, and **axis-tick-label overlap is permitted**. Because
this re-opens the original D2 defect ("decimals covered by the element to its
right"), **dock-open visibility** is a separately verified acceptance criterion
(`AC-D2.1`) + edge case that requires **independent Code Reviewer verification after
Build** (A25 carve-out). The pre-revision `docs/architecture.md` documented the
**superseded** inside-plot chip (revision 2 replaces that row with the D2/Q33
Y-axis-lane design), and revision 1 of this proposal addressed neither D2 nor its
verification. RC-2 corrects both.

### 5.2 Decision — chip renders in the Y-axis lane (supersedes the Batch-1 inside-plot chip)

The `[existing]` `_price_tag` (`ui/chart_panel.py:379`, updated at `:413–417`) is
repositioned:

- **Lane:** the chip renders in the **Y-axis lane, outside the data area**, to the
  **right of the plot's vertical axis line** — i.e. scene `x >= view_rect_scene.right()`
  (the plot's right edge / axis line), the opposite of the Batch-1
  `view_rect_scene.right() - 2` **inside** the plot.
- **Anchor:** left-anchored at the axis line (`anchor=(0, 0.5)`), so the pill grows
  rightward into the axis lane. (The exact `+N` px pad and any right-edge clamp to
  keep a long price unclipped is plan-level geometry — see PA-R6.)
- **Style:** a **grey background pill with WHITE text** (`setColor('#ffffff')`),
  replacing the current `#94a3b8` fill with dark `#0d0f14` text. The grey fill is
  retained (`#94a3b8` or an equivalent mid-grey).
- **Axis-tick-label overlap is EXPECTED and REQUIRED:** the chip MAY paint over the
  Y-axis price tick label at the same price. **Do not** add a deconfliction offset
  between the chip and the Y-axis tick label.
- The chip remains a scene `TextItem` added to the price plot's scene (so it does not
  affect auto-range and can draw over the axis lane); `Z` above the axis.
- Existing presence/clamping behaviour is retained: the chip is shown only while the
  cursor is inside the price plot and is hidden when the cursor leaves (`AC-D2.3`);
  it tracks the cursor's price under pan/zoom (`AC-D2.2`).

### 5.3 Dock-open visibility — required, independently verified (`AC-D2.1`)

- **Requirement to verify:** with the Active Trader and/or Portfolio dock open, the
  chip's complete label (all decimals) must be **visible and not covered by the
  dock**, even though it now sits outside the plot. Painting over a Y-axis tick label
  is permitted and is not a failure.
- **Edge case:** long price strings (`123,456.78`) must not bleed under the dock;
  narrow plots / small windows must not clip the label.
- **Independent verification (mandatory).** This re-opens a previously fixed defect,
  so **the Batch-1 fix cannot be assumed to still hold**. The **Code Reviewer must
  independently verify dock-open visibility after Build** (A25). Build's own test is
  necessary but not sufficient.
- **Build test (measurable, offscreen):** `test_crosshair_chip_renders_in_axis_lane`
  — with a loaded panel and the cursor inside the plot, assert the `_price_tag`'s scene
  `x` is `>= view_rect_scene.right()`, its anchor is left-anchored, the fill is grey
  and the text colour is white. A second assertion (or a light integration test) that
  the chip's scene bounding rect lies within the chart panel's right edge while a
  right dock is open covers the "not under the dock" property as far as offscreen
  allows; the **visual/dock-open verification is the Code Reviewer's independent
  step** (A25).

### 5.4 D11 re-scope — `AC-D11.4` is label-vs-label only (ESC-006)

D11 drawing price labels stay **inside the plot** at `x = view_rect.right() - 4`,
`anchor=(1, 0.5)`, `Z=10` (`ui/drawing_overlay.py:335`, `:342`). The crosshair chip
now occupies a **different lane** (the Y-axis lane, §5.2), so:

- `AC-D11.4` applies **only to label-vs-label stacking inside the plot** (consecutive
  labels offset by `>= 15 px`, each fully inside `view_rect`). The retired
  chip-vs-label `>= 15 px` requirement **no longer applies**; the chip is **out of
  scope** for `AC-D11.4`.
- ESC-006 is therefore resolved by **lane separation** (the Q33 design change), not by
  adding chip-vs-label deconfliction code. `_update_inner_labels` continues to stack
  drawing labels against each other only; it does **not** include the chip.
- The Code Reviewer must **re-scope ESC-006** to label-vs-label only when it
  re-checks its own escalations.

### 5.5 Canonical `docs/architecture.md` rows (RC-2 + RC-4a) — required wording

The Validator must ensure these two canonical rows carry the wording below
(revision 2's validated `docs/architecture.md` already reflects this):

1. **`docs/architecture.md` — crosshair chip row** (pre-revision Batch-1 wording:
   "Right-align `TextItem` (`anchor=(1,0.5)`) inside the plot's right edge").
   **Required wording:**
   > **Crosshair chip (D2, revised Q33 2026-09-27)** — grey pill (`TextItem`) with
   > **white** text in the **Y-axis lane outside the plot**, left-anchored at the
   > plot's vertical axis line (`anchor=(0,0.5)`, scene `x >= view_rect.right()`);
   > axis-tick-label overlap permitted. **Dock-open visibility** is a separately
   > verified acceptance criterion (`AC-D2.1`) requiring **independent Code Reviewer
   > verification after Build** (A25). Supersedes the Batch-1 inside-plot right-align.

2. **`docs/architecture.md` — "D10 volume toggle" row.** **Required affordance
   wording:**
   > a **checkable text label `Volume`** (Q31/A22; `AC-D10.1`) at the **top left of
   > the volume panel (bottom left of the price chart)** (A23 confirmed 2026-09-27),
   > default **visible**, toggles `volume_plot.setVisible()` and rebalances the
   > `QSplitter` so `price_plot` expands; **not persisted**.
   >
   > *(Shipped as the checkable text label `Volume` — `QPushButton("Volume")` at
   > `ui/chart_panel.py:327` (RC-4a/T27) — so the affordance and the implementation
   > agree.)*

---

## 6. Phased implementation plan (delta)

The existing `docs/plan.md` Phases 1–5 remain the backbone. This revision inserts
**two** new phases — **Phase R1** (router state machine) and **Phase R2** (D2/Q33
chip relocation) — and **amends** Phase 1, Phase 4 and Phase 5. Phase numbering is
prefixed `R` to avoid colliding with the canonical phases; the Validator may renumber.

### Phase R1 (NEW) — Router state machine (ESC-002, AC-D3.9, RC-3, RC-4b)

- **Goal:** Replace implicit tri-boolean precedence in `ui/chart_mouse_router.py`
  with `RouterMode { IDLE, DRAWING, ZOOMING, ALARM_PLACING }` and a single
  `_active_mode`; implement the §2.4 transition table (incl. the **TR-9 refusal**);
  implement the §2.5 property-setter reconciliation (RC-3); add the §2.6 named tests;
  keep the five existing router tests passing **verbatim**.
- **Requirements covered:** `AC-D3.7` (forward Q35 option (a) + reverse A26),
  `AC-D3.8`, **`AC-D3.9`**, `AC-D3.3`, `AC-D3.4`; Journey 4 edge cases.
- **Files:** `ui/chart_mouse_router.py` `[new/changed]`; `ui/chart_panel.py`
  (adapters → router intents + `zoom_refused` signal) `[new/changed]`;
  `ui/main_window.py` (one `status_bar` connection for `AC-D3.9`) `[new/changed]`;
  `tests/test_chart_mouse_router.py` `[new/changed]`.
- **Dependencies:** none.

### Phase R2 (NEW) — D2/Q33 crosshair chip relocation (RC-2)

- **Goal:** Move `_price_tag` into the Y-axis lane per §5.2 (grey pill, white text,
  axis-tick overlap permitted), and add the `AC-D2.1` dock-open verification surface.
- **Requirements covered:** D2 (`AC-D2.1`–`AC-D2.3`), Q33/A25; ESC-006 re-scope
  (§5.4).
- **Files:** `ui/chart_panel.py` (`_create_crosshair`/`_update_crosshair`) `[new/changed]`;
  new/updated crosshair test `[new]`.
- **Verification:** Build's `test_crosshair_chip_renders_in_axis_lane` + **independent
  Code Reviewer dock-open verification after Build** (`AC-D2.1`/A25).
- **Dependencies:** none, but **shares `ui/chart_panel.py`** with R1/Phase 1/Phase 3
  (serial chain — §7).

### Phase 1 (AMENDED) — Chart geometry: gap, volume width, volume axis

- **Amendment A (ESC-003 / RC-1):** the volume `nice_max` is the **§3 pinned
  `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` generator** (smallest value `>= max_vol × 1.1`,
  floor `100`, no fixed ceiling); the old fixed list becomes a **test fixture only**.
  Update `tests/test_volume_linear.py` per §3.4 — **only** the
  `_nice_volume_max(0) == 10_000` assertion changes (→ `100`).
- **Amendment B (ESC-007):** the volume ceiling is applied from a **cached running
  max** and is **updated on intra-bar ticks in O(1)** (only-widen), with the
  `auto_range=False` refresh paths re-applying the cached ceiling — see §4.
- **Requirements covered:** D7, D9, `AC-D8.1`–`AC-D8.7`.
- **Files:** `ui/candlestick_item.py` `[existing]`, `ui/chart_panel.py` `[new/changed]`,
  `tests/test_volume_linear.py` (+ new volume-ceiling tests) `[new/changed]`.

### Phase 2 (UNCHANGED) — Drawing visuals: inner-right labels + double-click dialogs

No change to the canonical Phase 2. `AC-D11.4` remains scoped to **label-vs-label**
stacking (§5.4 — the chip is in a different lane). Files: `ui/drawing_overlay.py` +
the two dialogs.

### Phase 3 (UNCHANGED) — Volume panel visibility toggle (D10)

No change to the canonical Phase 3, **with one documentation correction** (RC-4a,
§5.5): the affordance is the checkable **text label `Volume`** (Q31/A22), not an eye
icon. Files: `ui/chart_panel.py` (volume plot + splitter). **Note the
`chart_panel.py` overlap** with R1/R2/Phase 1 (serial chain, §7).

### Phase 4 (AMENDED) — Watchlist resize + double-click load

- **Amendment:** a symbol change while a drawing drag/draft is in progress (including
  the D14 mid-drag double-click path, `AC-D14.4`) must bring the router back to
  `IDLE` in addition to clearing the overlay draft/drag state (`TR-17`;
  `DrawingOverlay.set_data()` already clears it defensively at `:112–118`). Otherwise
  `_active_mode` can read `DRAWING` after the tool was implicitly cleared.
- **Soft dependency:** the mode-reset clause is only verifiable once Phase R1 lands,
  but the watchlist/QSettings work itself is independent.
- **Files:** `ui/watchlist_panel.py`, `ui/main_window.py`, `QSettings` read/write
  site, `tests/` (watchlist + `AC-D14.4` regression).

### Phase 5 (AMENDED) — Verification and regression (all batches)

- Router mode transitions — the §2.6 named tests (new incl. `AC-D3.9` + preserved +
  mode-model + reconciliation).
- Nice-number generator — §3.2 family/formula, monotonic, tight coverage
  (`<= 2`), floor `100`, the `40M–50M` cases, and the legacy-list fixture
  cross-checks (§3.3).
- Live ceiling — `test_volume_ceiling_tracks_live_bar`,
  `test_volume_ceiling_refit_on_timezone_refresh`.
- D2 chip — `test_crosshair_chip_renders_in_axis_lane`; **Code Reviewer's independent
  dock-open verification** for `AC-D2.1`.
- `touches_files`-aware sequencing honoured (no two built tasks in a wave share a
  file).
- Global criteria unchanged: the pre-existing suite stays green offscreen
  (`QT_QPA_PLATFORM=offscreen`), no live-TWS connection or order transmission (Q8/Q9).

---

## 7. Parallel-build sequencing consequence (`touches_files`)

The pipeline contract requires the Task Manager to add a **`touches_files`** field to
every task, and `docs/build/build_config.json` (optional, user-owned,
`max_parallel_tasks`, **default 4**) now exists. Build is a **Lead + Worker pair**:
the Lead computes which tasks are ready and dispatches only tasks whose
`touches_files` do **not overlap** within a wave, up to `max_parallel_tasks`; it is the
sole writer of task status, so concurrent workers never race on the graph.

**Sequencing consequence for this revision** — the file map (§1.1) produces hot files
that **must not be scheduled in the same wave**:

1. `ui/chart_panel.py` — touched by **Phase R1** (router adapters + `zoom_refused`),
   **Phase R2** (crosshair chip), **Phase 1** (volume axis/ceiling/width), and
   **Phase 3** (volume toggle + splitter). `touches_files` for all of these includes
   `ui/chart_panel.py`, so they form a **serial chain** even though the phases are
   logically independent.
2. `ui/main_window.py` — touched by **Phase R1** (the `AC-D3.9` status-bar connection)
   and **Phase 4** (watchlist wiring). They are now **serial with each other** (a
   change from revision 1, which had Phase 4 fully parallel).
3. `ui/chart_mouse_router.py` — touched by **Phase R1** only.
4. `ui/drawing_overlay.py` — touched by **Phase 2** and the Phase-4 mid-drag
   amendment. Serial with each other.

Practical scheduling implication for the Task Manager:

- **Phase R1 must be its own wave** (or share a wave only with tasks that touch
  neither `ui/chart_panel.py` nor `ui/main_window.py`).
- **Phase R2 must be serial** with R1/Phase 1/Phase 3 (same `ui/chart_panel.py`).
- **Phase 4's `ui/watchlist_panel.py`/`QSettings` work can run in parallel**, but its
  `ui/main_window.py` changes must not share a wave with R1.
- **Phase 2** dialog tasks (new files) can run in parallel with Phase 1/R1, *provided*
  the `DrawingOverlay` task does not overlap `chart_panel`.
- **Phase 1's** `ui/candlestick_item.py` work can run in parallel with `chart_panel`-
  based tasks; the `ui/chart_panel.py` part is on the serial chain.
- Verification tasks touching the same test file must be serialized per file.

This is an **architecture-level constraint on the task graph**, not a task
decomposition: the Task Manager populates `touches_files` accurately and the Lead
enforces the wave rule.

---

## 8. Non-Functional / data model / integration deltas

- **Data model:** unchanged. No new tables/columns; no
  `DrawingStore`/`normalize_payload` change. Router mode is ephemeral runtime state;
  the volume running max is an in-memory field on `ChartPanel`.
- **Integration points:** no new IBKR calls. `QSettings` (D13) and the existing Qt
  signal bus only; Phase R1 adds one `ChartPanel` signal (`zoom_refused`) for the
  `AC-D3.9` status hint.
- **Performance:** §4.2 is the corrected statement. Router dispatch is O(1) (one
  enum compare per handler). Nice-number generation is O(1) (a log10 + a small
  mantissa table). Mode reconciliation runs only at wiring boundaries.
- **Security:** live-order path untouched; Q9 holds.
- **High-DPI:** no change to D6/D11 device-pixel claims in this revision; D2's chip
  is a scene `TextItem` and inherits existing scaling.

---

## 9. Plan-level assumptions (flagged)

Inherited and confirmed from `docs/requirements/requirements.md`: A8, A10–A20,
A22–A26 (and the canonical `PA1-batch3`…`PA8-batch3`), all unchanged.

Revision-2 assumptions:

| # | Assumption | Why it is needed | Status |
|---|---|---|---|
| **PA-R2** | `RouterMode.DRAWING` is synonymous with `DrawingOverlay.tool_active()`; an unarmed drawing tool is `IDLE`, not a separate state. | Keeps existing widget state sync unchanged. | Plan-level; no requirements gap |
| **PA-R3** | `test_draw_blocked_during_zoom` keeps its escalation-assigned name while asserting the **confirmed reverse** rule (draw exits zoom). | The escalation named the test but the requirements later confirmed the direction; renaming would break named-test traceability. | Plan-level naming note; no requirements gap |
| **PA-R4** | Only-widen (not re-shrink) on intra-bar ceiling updates is acceptable under `AC-D8.6`'s "recomputed/**widened** … or the bound is explicitly documented" clause. | The requirement permits either; only-widen avoids per-tick axis jitter. | Plan-level; consistent with `AC-D8.6` |
| **PA-R5** | The original fixed list is retained **as a test fixture only**; of the existing `tests/test_volume_linear.py` assertions, **only** `_nice_volume_max(0) == 10_000` is updated (→ `100`) — `(8_000)`, `(80_000)`, `(2_200_000)` and `(1_050_000)` remain valid under the pinned family. | Requirement-backed test change (`AC-D8.4`/A24), not a silent edit. | Plan-level; no requirements gap |
| **PA-R6** | D2 chip implementation geometry: left-anchored at the axis line (`anchor=(0,0.5)`, scene `x = view_rect_scene.right()` + small pad), extending right into the Y-axis lane, with the existing top/bottom in-view clamp and a right-edge guard so a long price is not clipped. | The requirements fix the lane/style/overlap but not the pixel anchor/pad. | Plan-level implementation detail; no requirements gap |
| **PA-R7** | `AC-D3.9`'s status-bar hint is surfaced by a new `ChartPanel.zoom_refused` signal connected in `MainWindow` to `status_bar.showMessage(...)`; the exact hint string is a plan-level choice ("Finish or cancel alarm placement before zooming"). | The requirement mandates *a* status-bar hint but not the wiring or exact text. | Plan-level implementation detail; no requirements gap |
| **PA-R8** | The `<= 2` tightness bound in `AC-D8.4` is asserted only where the ceiling is above the required `100` floor (equivalently `max_vol >= 100 / 2.2 ≈ 45.5`); below that threshold `nice_max` is the floor `100`, so the ratio can exceed `2`. The generator's floor is `100` per `AC-D8.4`/A24. | `AC-D8.4` states both the `<= 2` bound and the `100` floor; taken literally the bound is unachievable for tiny `max_vol` (e.g. `max_vol = 1 → nice_max = 100 → ratio ≈ 91`). Build must not write a test that contradicts the required floor. | Plan-level test-scoping detail; consistent with `AC-D8.4` |
| ~~**PA-R1**~~ | ~~TR-9: magnifier during `ALARM_PLACING` exits alarm and enters `ZOOMING`.~~ | **Superseded by `AC-D3.9` (Q36 option (b)) — the router refuses and stays in `ALARM_PLACING`. RG-003 is closed.** | **Retired** |

**Requirements gaps surfaced:** **none.** RG-002 (nice-number family) and RG-003
(`ALARM_PLACING → ZOOMING`) are both **resolved in `requirements.md` (2026-09-27)**:
the family is pinned to `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`, and the magnifier is
refused during alarm placement (`AC-D3.9`). Every remaining assumption above is an
implementation detail, not a behaviour gap.

---

## 10. Architecture risks (delta)

| Risk | Severity | Mitigation |
|---|---|---|
| ESC-002 regression: switching to an enum changes routing order for an existing tested path | M | The five existing router tests are the regression fence; §2.3 dispatch table preserves alarm-first in `IDLE`, drawing-first in `DRAWING`, click-prefers-alarm in `IDLE`; §2.5 reconciliation makes `test_drawing_tool_blocks_alarm_press` pass verbatim |
| RC-3 mechanism mis-implemented (mode not derived on direct wiring) | M | Property setters + `_reconcile_mode_from_overlays()` (§2.5); `test_reconcile_mode_from_wired_overlays` + the five preserved tests |
| `AC-D3.9` refusal accidentally cancels the pending alarm placement or enters `ZOOMING` | M | TR-9 explicit side effects; `test_magnifier_refused_during_alarm_placement` asserts mode unchanged and placement intact |
| D2 dock-open visibility regresses despite being moved to the lane | M | `AC-D2.1` + edge case; Build test + **independent Code Reviewer verification after Build** (A25) — the Batch-1 fix is not assumed |
| D2 chip clipped at narrow widths / long prices in the axis lane | L | `AC-D2.1` edge cases; PA-R6 right-edge guard; `test_crosshair_chip_renders_in_axis_lane` |
| `chart_panel.py` touched by R1/R2/Phase 1/Phase 3 → serial build chain | L (schedule) | `touches_files` populated per §7; Lead serializes overlapping waves |
| Only-widen ceiling leaves headroom after the live bar shrinks on a partial/out-of-order tick | L | `AC-D8.6` satisfied (no clipping); refreshed O(N) on the next load/new bar |
| Nice-number generator changes tick values of already-built Batch-4 behaviour | L | Old list kept as fixture (all members of the pinned family); only `(0)` expectation updated (§3.4, A24) |
| Router and `ChartPanel` both writing mode state (drift) | M | Router is the single writer of `_active_mode`; `ChartPanel` methods are adapters (§2.5); `test_router_mode_is_mutually_exclusive` |

---

## 11. Requirements coverage (this revision)

| Requirement / AC | Architectural treatment | Phase |
|---|---|---|
| `AC-D3.7` forward (Q35 (a)) | TR-4: magnifier during `DRAWING` cancels draft + discards it, enters `ZOOMING` (§2.4) | R1 |
| `AC-D3.7` reverse (A26) | TR-5: drawing tool during `ZOOMING` exits zoom, activates tool (§2.4) | R1 |
| `AC-D3.8` | TR-6: alarm placement during `ZOOMING` exits zoom, enters `ALARM_PLACING` (§2.4) | R1 |
| **`AC-D3.9`** (Q36 (b)) | **TR-9: magnifier during `ALARM_PLACING` is REFUSED — mode unchanged, placement intact, status-bar hint (§2.4/§2.5)** | R1 |
| `AC-D3.3` / `AC-D3.4` | TR-14/TR-15: Esc/right-click reset the selection sub-state, not the mode (§2.4) | R1 |
| `AC-D8.1`–`AC-D8.5` (ESC-003/008, RG-002) | §3: one pinned family `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`, floor `100`, no ceiling; old list = fixture | 1 (amend) |
| `AC-D8.6` / `AC-D8.7` (ESC-007) | §4: live ceiling O(1) via cached running max, only-widen; `auto_range=False` paths re-apply cached ceiling | 1 (amend) |
| **`AC-D2.1`–`AC-D2.3` / Q33 / A25** | **§5.1–§5.3: chip in the Y-axis lane, grey pill + white text, overlap permitted; dock-open visibility independently verified** | **R2** |
| `AC-D11.4` (ESC-006 re-scope) | §5.4: label-vs-label inside the plot only; chip lane-separated | 2 |
| `AC-D10.1` / Q31 / A22 | §5.5: canonical D10 affordance wording = checkable text label `Volume` | 3 (doc correction) |
| `AC-D14.4` (ESC-010) | TR-17 + §6 Phase 4: symbol change mid-drag also resets router mode to `IDLE` | 4 (amend) |
| `AC-D8.1`–`AC-D8.3`, D7, D9 | Unchanged from canonical Architecture (re-affirmed) | 1 |
| D11, D12, D13, D14, D15 | Unchanged from canonical Architecture (re-affirmed) | 2, 3, 4 |

---

Status: READY_FOR_VALIDATION — see `docs/plan_proposal.md`.
