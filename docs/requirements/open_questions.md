# Open Questions

> Owned by Requirements Analyst. Other agents may read; only Requirements Analyst edits.
>
> **2026-10-02 — D16 batch RESOLVED.** The new D16 report (historical bars missing
> 2026-09-19…2026-09-27 on `SPY 5 mins`, price **and** volume panels) has been
> clarified: **Q37–Q39 were answered by the user 2026-10-02** and are recorded below
> under "Answered (D16 intake)". No blocking question remains for D16, so
> `requirements.md` carries `Status: READY_FOR_PLAN`. Q1–Q36 remain closed for the
> D1–D15 run. **ESC-023 (Code Reviewer escalation, approved for correction 2026-10-02) is
> resolved and recorded as Q40 below** — Dec 31 is a trading day when New Year's Day falls on
> a Saturday (`AC-D16.7`); no blocking question remains.
>
> **Resolved and closed as of 2026-09-27 for the D1–D15 run:** Every question was closed and nothing
> dangled. **`Q36` (RG-003 — `ALARM_PLACING → ZOOMING`) was answered 2026-09-27 with
> option (b):** invoking the magnifier while `ALARM_PLACING` is active **REFUSES to enter
> `ZOOMING`** (the router stays in `ALARM_PLACING`) and shows a status-bar hint; alarm
> placement keeps priority and the pending alarm placement is **not** cancelled. It is
> recorded as requirement **`AC-D3.9`** in `requirements.md` (D3 / ESC-002), which makes
> the router transition table **total** — the `ALARM_PLACING → ZOOMING` cell is now
> **specified required behaviour**, no longer Plan assumption **PA-R1** / **RG-003**.
> All post-review questions **Q31–Q36** are answered and all four follow-up confirmations
> are closed.
> Q35 (ESC-002 magnifier/drawing transition semantics) is fully resolved: the forward
> direction is option **(a)** — invoking the magnifier while a drawing tool is active
> **cancels the in-progress drawing and enters `ZOOMING`** — and the **reverse direction** (a
> drawing tool selected while `ZOOMING` is active) was subsequently **CONFIRMED by the user
> on 2026-09-27**: it **exits `ZOOMING` and activates the drawing tool** (assumption A26 is
> now a requirement, folded into `AC-D3.7`; no provisional wording remains). The formerly
> **undecided** alarm-vs-zoom branch is also decided: **alarm-mode activation cancels
> `ZOOMING`** (now `AC-D3.8`; supplies the expected behaviour for
> `test_alarm_placement_blocks_zoom`). Q32's D10 placement (A23) and Q33's D2 visual
> reference (A25) were likewise **confirmed 2026-09-27**. Q31–Q34 were answered 2026-09-27
> (see below).
> **RG-002 (D8 nice-number family) was resolved by the Requirements Analyst on 2026-09-27**
> — the family is pinned to `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` (see `requirements.md`
> D8 / A24); no user question was needed because the contested values `750K` and `1.5M` are
> user-confirmed (Q20). **RG-003 is now resolved by Q36 option (b)** — the
> `ALARM_PLACING → ZOOMING` corner is a specified requirement (`AC-D3.9`), so Plan's
> assumption PA-R1 / derived transition TR-9 is superseded and the ESC-002 transition
> table is total. The post-review
> batch (Q31–Q36) was added 2026-09-27 as the Code Reviewer/Plan escalations arrived.
> Batches 2–9 (D4–D15) were clarified 2026-09-19/20. The ESC-002 fix (the
> `chart_mouse_router` transition table) is now specified in both drawing directions, for
> the `ZOOMING → ALARM_PLACING` alarm transition, **and for the `ALARM_PLACING → ZOOMING`
> refusal**, so it is **total and ready for Plan**.

## Answered

### Q1 — What is the actual goal for this run?
- **Status:** answered 2026-09-19
- **Answer:** Fixing issues and resolving UI bugs. This is a feedback-driven
  stabilization run, not a new-feature build.

### Q2 — Is the goal one of the known gaps, or something new?
- **Status:** answered 2026-09-19
- **Answer:** Something new. The user is giving feedback on the app and asking for
  fixes. (Candidates A/B from discovery are explicitly out of scope for this run.)

### Q3 — Definition of done / success metric
- **Status:** answered 2026-09-19
- **Answer:** All test conditions pass. Test conditions are not fixed up front —
  they will be defined/updated per task as each defect is triaged.

### Q4 — Scope boundaries
- **Status:** answered 2026-09-19
- **Answer:** The normal live-order path is in scope to touch, but live orders are
  currently gated at the TWS API layer by the user, so no order can actually
  transmit during this work.

### Q5 — Confirm the stack
- **Status:** answered 2026-09-19
- **Answer:** Confirmed as documented (Python 3.11+/PyQt6/pyqtgraph/ibapi/SQLite,
  macOS arm64, live TWS port 7496 only).

---

## Answered (batch 1 intake)

## Q6 — What is the actual list of reported issues / UI bugs?
- **Status:** answered 2026-09-19
- **Answer:** Batch 1 supplied — three defects, D1 (RTH/ETH session shading),
  D2 (crosshair price label covered by right dock), D3 (missing zoom controls +
  area-zoom magnifier). Batch 1 is the complete list for this run.
- **Affected requirement section:** Problem Statement; Defect Register.

## Q7 — How will feedback arrive, and in what detail?
- **Status:** answered 2026-09-19
- **Answer:** One message at a time; follow-up questions are permitted as needed.
  The full requirements→build flow may repeat until the user is satisfied.

## Q8 — Regression-test policy per fix
- **Status:** answered 2026-09-19 (confirmed: "ok")
- **Answer:** Every fix ships with a check that fails before / passes after,
  runnable offscreen with no live TWS; the existing suite stays green.

## Q9 — Live-order safety boundary during this run
- **Status:** answered 2026-09-19 (confirmed: "ok")
- **Answer:** No automated test connects to live TWS or transmits. Order-path
  changes verified via generated-order-field unit tests; any live check is a manual
  user-run step.

---

# Defect Intake — Batch 1 (D1–D3)

## Q10 — D1: which sessions are shaded, and in what colours?
- **Status:** answered 2026-09-19
- **Answer:** Proposed sessions accepted. RTH left at default (no band). Pre-market
  = **orange at 10% opacity**; post-market = **blue at 10% opacity**.

## Q11 — D1: when should shading appear?
- **Status:** answered 2026-09-19
- **Answer:** Accept default, with the intraday range corrected to **1 min through
  4 hours**. (Exact set: `1 min, 5 mins, 15 mins, 1 hour, 4 hours`; `1 day` excluded.)

## Q12 — D2: where should the crosshair price label sit?
- **Status:** answered 2026-09-19; **SUPERSEDED 2026-09-27 by Q33**
- **Answer:** Option **(a)** — right-align the chip so it ends inside the plot's
  right edge, never under the axis or right dock.
- **Superseded:** Q33 (answered 2026-09-27) **revised the placement by design change** —
  the chip now renders in the **Y-axis lane outside the plot** as a grey pill with white
  text (see D2). The option-(a) inside-plot right-alignment no longer applies; retained
  for history only.

## Q13 — D3: where do the zoom controls live?
- **Status:** answered 2026-09-19
- **Answer:** Top-right of the chart area, inside a visible outline so it looks neat.
  Cluster contains `−`, `+`, magnifier, reset.

## Q14 — D3: how should the magnifier behave?
- **Status:** answered 2026-09-19
- **Answer:** Proposed behaviour accepted. Both axes. Magnifier stays active after
  one zoom. `+`/`−` zoom around the chart centre. A reset button is required.

---

# Defect Intake — Batch 2 (D4–D5) — proposed 2026-09-19, screenshot feedback

## Q15 — D4: zoom label size (proposed 14px/700, magnifier 50% larger)
- **Status:** answered 2026-09-19
- **Answer:** Correct, with the magnifying glass 50% larger. Final: `-`/`+`/`Reset` at
  **14px / 700**, `⌕` at **21px / 700** (14px × 1.5). Button size remains 28×24.

## Q16 — D4: zoom cluster position (proposed left of price axis)
- **Status:** answered 2026-09-19
- **Answer:** Current is fine — fully inside the data area left of the price axis
  (`x = panel.width - ctrl.width - axis_width - 12`, fallback 50, `x >= 8`).

## Q17 — D5: volume Y logarithmic — always on? zero handling? (proposed)
- **Status:** answered 2026-09-19
- **Answer:** Lower bound **1.0** confirmed. Volume ViewBox always log on Y
  (`setLogMode(y=True)`), X remains linear; zero-volume bars map to `1.0`; auto-range
  `yRange=(1.0, max_vol*1.1)`.

---

# Defect Intake — Batch 2 extension (D6) — new screenshots 2026-09-19

## Q18 — D6: candlestick wick visibility
- **Status:** answered 2026-09-19
- **Answer:** Correct — wick ~1px thin line behind the body, body noticeably wider
  (≥4× wick, e.g., 6–8px at default zoom while wick stays 1px), colour follows
  direction (teal/pink), and wick extends beyond the body when a shadow exists.

---

# Defect Intake — Batch 3 (D7) — proposed 2026-09-19

## Q19 — D7: time-axis candle spacing — how much more?
- **Status:** answered 2026-09-19
- **Answer:** Go **35% gap** for now. Body half-width `0.40 → 0.325` of `median_diff`
  (full body 65% of spacing, gap 35%). `xRange` padding stays as-is; the 4px body
  minimum continues to apply.

---

# Defect Intake — Batch 4 (D8) — new volume screenshots 2026-09-19

## Q20 — D8: volume Y linear scale, no negatives, dynamic nice ticks, coloured bars
- **Status:** answered 2026-09-19
- **Answer:** Correct — linear Y starting at `0` with no negatives, dynamic nice max
  (`max_vol*1.1` rounded up via `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M,
  2.5M, 5M, 10M]`), and bars coloured green/red by price direction as proposed.

---

# Defect Intake — Batch 5 (D9–D10) — new volume feedback 2026-09-19

## Q21 — D9: volume candle spacing should follow price candle spacing
- **Status:** answered 2026-09-19
- **Answer:** Correct — volume width = same `w` as price (`width = w*2`, gap 35% of
  `median_diff`). The spacing matches the price panel exactly.

## Q22 — D10: volume panel show/hide toggle
- **Status:** answered 2026-09-19
- **Answer:** Top left of the volume panel, which is the bottom left of the price
  chart panel. Toggle is checkable, default visible, not persisted; clicking hides
  the volume plot and its axis and the price plot expands.

---

# Defect Intake — Batch 6 (D11) — new drawing screenshots 2026-09-19

## Q23 — D11: drawing price labels on inner side (right side) of chart
- **Status:** answered 2026-09-19
- **Answer:** Correct — inner-right-side inside the plot, near the right edge, is the
  correct placement for all drawing price labels as proposed.

---

# Defect Intake — Batch 7 (D12) — zone double-click settings popup 2026-09-19

## Q24 — D12: zone double-click should open settings popup with 4 tabs — is the tab content correct and is Extend omitted?
- **Status:** answered 2026-09-19
- **Answer:** Correct — Extend is omitted; zone always extends both sides. The four
  tabs (Style without Extend, Text, Coordinates, Visibility) as proposed are correct.

---

# Defect Intake — Batch 8 (D13–D14) — new watchlist feedback 2026-09-20

## Q25 — D13: watchlist panel should extend more — how far?
- **Status:** answered 2026-09-20
- **Answer:** Freely draggable up to **~50% of MainWindow width**. Chart central panel keeps minimum **400px** so effective max is `min(floor(0.50×W), W−400)`. On 1400px window this is ~700px; min watchlist ~150px. Clamped on window resize.
- **Affected requirement section:** D13 / Journey 14 / AC-D13.1–D13.3

## Q26 — D13: should watchlist width persist across restarts?
- **Status:** answered 2026-09-20
- **Answer:** **Yes** — persist integer pixels (e.g., QSettings `watchlist/width` or DB key) and restore on launch clamped to current 50%; default ~220px if none saved.
- **Affected requirement section:** D13 / Journey 14 / AC-D13.2

## Q27 — D14: watchlist click to load chart — single-click or double-click, and where?
- **Status:** answered 2026-09-20
- **Answer:** **Double-click anywhere on the row** (any of the 7 columns) triggers the load; single-click only selects the row (SelectRows behavior retained).
- **Affected requirement section:** D14 / Journey 15 / AC-D14.1

## Q28 — D14: what chart load semantics should double-click use?
- **Status:** answered 2026-09-20
- **Answer:** **Identical to typing symbol in Symbol input and pressing Load Chart** — set `symbol_input` to row’s Symbol (uppercased), then invoke existing `load_chart()` with current `tf_combo` and current `ext_hours_btn`; includes cancel previous RT, cached bars, delta fetch, RT subscription, DOM if enabled.
- **Affected requirement section:** D14 / AC-D14.1

## Q29 — D14: same symbol or disconnected — what should happen?
- **Status:** answered 2026-09-20
- **Answer:** **No-op** in both cases: if double-clicked symbol (case-insensitive) equals `_current_symbol`, no reload/new reqId/RT cancel/no flicker; if IBKR disconnected, no historical/RT request and `status_bar.showMessage("Disconnected — cannot load chart.", 3000)`; header/empty area also no-op.
- **Affected requirement section:** D14 / AC-D14.2–D14.3

---

# Defect Intake — Batch 9 (D15) — horizontal line double-click 2026-09-20

## Q30 — D15: horizontal line double-click should open settings popup with 4 tabs — is the tab content correct?
- **Status:** answered 2026-09-20
- **Answer:** Correct — the four tabs (Style with `Line`, Text, Coordinates with single `#1 (price)`, Visibility) as proposed are correct.
- **Affected requirement section:** D15 / AC-D15.1–D15.3

---

# Post-review requirements questions — added 2026-09-27 (Code Reviewer escalations)

## Q31 — D10: what icon represents the volume show/hide toggle?
- **Status:** answered 2026-09-27
- **Answer:** The user chose the **text label `Volume`** — a checkable text-label toggle
  (not an eye icon, not a bar glyph). This confirms the D10 icon/affordance decision;
  the *placement* was subsequently confirmed 2026-09-27 (see Q32 / A23).
- **Affected requirement section:** D10 (Visual reference line; AC-D10.1); Assumptions A22.

## Q32 — D10: is the Q22 placement (top-left of the volume panel) confirmed by a visual reference, or does D10 proceed as a provisional assumption?
- **Status:** answered 2026-09-27; **placement subsequently CONFIRMED 2026-09-27** (A23 flipped to confirmed)
- **Answer:** Originally **accepted as a provisional assumption (A23)**, then **CONFIRMED by the
  user on 2026-09-27**: the toggle sits at the **top left of the volume panel (bottom left of
  the price chart)**. With the icon (text label `Volume`, Q31) and this placement both
  confirmed, **D10 is now `CONFIRMED`** under AC-G.1 and no provisional wording remains.
- **Affected requirement section:** D10 (Visual reference line; AC-D10.1); Assumptions A23.

## Q33 — D11/ESC-006: when a drawing label run overflows the pane height, which element wins — the crosshair chip or the drawing label?
- **Status:** **answered 2026-09-27** — resolved by a **design/placement change**, not by
  choosing one of the options below.
- **Answer:** The crosshair price chip is relocated to the **Y-axis lane** — to the RIGHT
  of the plot's vertical axis line, **outside the data area** — as a **grey pill with
  white text**, and overlapping the Y-axis tick label at the same price is **permitted**
  (see the revised **D2**). D11's drawing price labels remain **INSIDE the plot** at
  `view_rect.right() - 4`. Because the chip and the labels now occupy **different lanes**,
  the crosshair-vs-label overflow collision no longer applies and **no priority rule is
  needed**.
- **Consequence for `AC-D11.4`:** it is **re-scoped to label-vs-label stacking inside the
  plot only** (`>= 15 px`, clamped to `view_rect.bottom()`); the chip is removed from the
  collision accounting. The **Code Reviewer MUST re-scope ESC-006** accordingly.
- **Supersedes:** the earlier (a)/(b)/(c)-style priority framing below (options 1–4); that
  framing was predicated on the chip and drawing labels sharing one lane.
- **Re-opened defect (independent verification required):** because D2's chip placement
  changed, the original D2 defect surface — chip decimals covered by the Active Trader /
  Portfolio dock — is **re-opened**. It MUST be independently verified by the Code Reviewer
  after Build; the Batch-1 inside-plot fix cannot be assumed to still hold. See D2
  (AC-D2.1 + dock-open edge case).
- **Confirmed 2026-09-27 (A25):** the D2 **appearance and lane placement** reference is now
  **CONFIRMED** as the agreed target. **Scoped carve-out:** **dock-open visibility** is
  **not** covered by that reference and remains a separately verified acceptance criterion
  (`AC-D2.1`) + edge case requiring independent Code Reviewer verification after Build.
- **Affected requirement section:** D2 (revised placement/style); D11 / `AC-D11.4`
  (re-scoped); ESC-006.

*(Original question, context and options retained for history — not adopted:)*
- **Blocks (historical):** `AC-D11.4` (crosshair-chip vs drawing-label separation) for the
  overflow case.
- **Context (historical):** Chip and drawing labels shared the right-edge lane and were
  deconflicted to `>= 15 px` vertical separation. When many drawings sat at nearby prices
  and the run exceeded the pane height (labels clamped to `view_rect.bottom()`), two labels
  could still land on the same y, so the "must not overlap" rule needed a priority choice.
- **Options (historical, none adopted):**
  1. **Crosshair chip has priority** — always full opacity/on top; the drawing label at
     the same price is hidden or dimmed while the cursor is there.
  2. **Drawing label has priority** — the chip is offset/hidden when a label occupies the lane.
  3. **Both stack** — keep offsetting both, allowing the run to clamp at the pane bottom
     (accept possible coincidence in extreme cases).
  4. **Hide labels at the exact price under the cursor** — show only the chip there.

## Q34 — Docs owner: should Phases 1–5 of `PENDING_IMPLEMENTATION_PLAN.md` be marked `✅ COMPLETE`, and who confirms it?
- **Status:** answered 2026-09-27
- **Answer:** **Option 1 — mark Phases 1–5 `✅ COMPLETE`.** Ownership split: the
  **Requirements Analyst owns closing `DOC-2`** (the mark-complete correction) and
  **Code Reviewer verification is the confirming step** (it confirms the drift, then verifies
  the correction was applied). Because `PENDING_IMPLEMENTATION_PLAN.md` is **not in the
  Analyst's file-ownership table**, the Analyst records the requirement and this ownership
  split in `requirements.md` (`DOC-2`) rather than editing that root doc. Any residual
  user/owner action needed to physically apply the markers is a **recorded dependency**, not
  a blocking question. **Not blocking — closed.**
- **Affected requirement section:** Documentation Maintenance Requirements (`DOC-2`); ESC-011.

## Q35 — ESC-002: when the magnifier is invoked while a drawing tool is active, does zoom cancel the drawing or refuse to activate? (and the reverse)
- **Status:** **answered + confirmed 2026-09-27** — the **forward direction** is resolved
  (option (a)); the **reverse direction** was subsequently **CONFIRMED 2026-09-27** (A26 is
  now a requirement, `AC-D3.7` reverse); the formerly-undecided **alarm-vs-zoom branch** is
  also decided (`AC-D3.8`). Fully closed — nothing dangles. **Not blocking.**
- **Answer (forward direction — user-confirmed, option (a)):** invoking the magnifier while
  a drawing tool is active **CANCELS the in-progress drawing and enters `ZOOMING`**.
  Option (b) (refuse and show a status-bar hint) is **not adopted**. Consequence: the active
  drawing tool and any in-progress draft are cleared/discarded — **no half-drawn artefact is
  left behind** — and `ZOOMING` and `DRAWING` can never be active together. This is recorded
  as a requirement-side note and acceptance criterion **AC-D3.7** in `requirements.md` (D3,
  ESC-002 transition semantics). The explicit `RouterMode` state machine
  (`IDLE/DRAWING/ZOOMING/ALARM_PLACING`, single `_active_mode`) encodes it as a requirement.
- **Answer (reverse direction — CONFIRMED 2026-09-27; A26):** selecting a drawing tool while
  `ZOOMING` is active **exits `ZOOMING` and activates the drawing tool** (mirroring the
  forward precedence and the alarm-mode precedent that forces the draw tool back to
  `Cursor`). This is now a **requirement**, folded into `AC-D3.7` (reverse), not an
  assumption; Plan MUST encode it in the router transition table as required behaviour.
- **Blocks (resolved):** the ESC-002 fix — the explicit `RouterMode` state machine
  (`IDLE/DRAWING/ZOOMING/ALARM_PLACING`), single `_active_mode`, guard clauses and the
  **router transition table** in `ui/chart_mouse_router.py`, currently routed to **PLAN**.
  Both directions are now user-specified (`AC-D3.7`) and the alarm transition is decided
  (`AC-D3.8`); Plan must not invent them from the architecture alone.
- **Context:** Today the magnifier and a drawing tool can both be active at once; activating
  the magnifier does **not** clear the drawing tool (`ui/chart_panel.py:538–548` — `set_zoom_mode`
  only syncs the overlay/button), and zoom simply wins by handler call order in the router.
  The existing tests cover only alarm-vs-drawing precedence; the draw+zoom interaction is
  undefined (ESC-002; review finding F2). **Precedent:** alarm mode already forces the draw
  tool back to `Cursor` (`ui/main_window.py:487–488`, `:664–665`) and selecting a drawing tool
  turns alarm mode off.
- **Forward direction — magnifier invoked while a drawing tool is active (answered
  2026-09-27 — option (a)):** option 1 below was adopted; option 2 was not.
  1. **Cancel the drawing** — activating the magnifier clears the active drawing tool/draft
     and enters `ZOOMING` (consistent with the alarm-mode precedent). Consequence: the
     in-progress draft on the chart is discarded with no half-drawn artefact left behind,
     so zoom and drawing can never be active together. **← ADOPTED (option (a)); AC-D3.7.**
  2. **Refuse to enter `ZOOMING`** — keep the drawing tool active and show a status-bar hint
     (e.g. "Finish or cancel the current drawing before zooming"). Consequence: zoom is blocked
     until the user returns to `Cursor`; no draft is ever silently lost. **← NOT adopted.**
- **Reverse direction — a drawing tool selected while `ZOOMING` is active (CONFIRMED
  2026-09-27; A26):** behaviour is **exit `ZOOMING` and activate the drawing tool**, mirroring
  the forward precedence. Alternative (keep `ZOOMING` and refuse the tool selection with a
  hint) is not adopted. Now a requirement (`AC-D3.7` reverse) — see A26.
- **Alarm-mode activation cancels `ZOOMING` — DECIDED 2026-09-27:** activating alarm
  placement mode while the router is in `ZOOMING` **exits `ZOOMING` and enters alarm
  placement** (mirroring the alarm-vs-drawing precedent; named test
  `test_alarm_placement_blocks_zoom`). Now a requirement (`AC-D3.8`); no longer undecided.
- **Affected requirement section:** ESC-002 companion / **router transition table**
  (`docs/code_review/escalations.md` ESC-002; `docs/code_review/review_log.md` F2); D3 zoom
  edge cases; task `T6`.

---

# Answered (post-review)

## Q36 — ESC-002 / RG-003: what happens when the magnifier is invoked while alarm placement mode (`ALARM_PLACING`) is active?
- **Status:** **answered 2026-09-27 — the user chose option (b).** No blocking questions remain.
- **Answer (user-confirmed 2026-09-27, option (b)):** invoking the magnifier while
  `ALARM_PLACING` is active **REFUSES to enter `ZOOMING`** — the router **stays in
  `ALARM_PLACING`** and shows a **status-bar hint** (e.g. "Finish or cancel alarm
  placement before zooming"). Alarm placement keeps priority and the pending alarm
  placement is **not cancelled**. Option (a) (magnifier cancels the pending alarm
  placement and enters `ZOOMING`) was **not adopted**.
  - **Consequence:** the transition table encodes `ALARM_PLACING + magnifier →
    ALARM_PLACING` (no mode change); a pending alarm placement — a trading action — is
    never silently discarded; the magnifier is blocked while `ALARM_PLACING` is active.
  - **Requirement record:** this is now **`AC-D3.9`** in `requirements.md` (D3 / ESC-002),
    cross-referenced from the ESC-002 transition area as **REQUIRED behaviour**. It makes
    the router transition table **total**, superseding Plan's derived **TR-9** /
    assumption **PA-R1**.
- **Blocks (resolved):** the ESC-002 fix — the explicit `RouterMode` state machine and the
  **router transition table** in `ui/chart_mouse_router.py`. That table must be
  **total** (every mode × event cell defined) to be testable and implementable without
  invention. The requirements previously left the **`ALARM_PLACING → ZOOMING`** cell
  unspecified; it is now **specified by `AC-D3.9`**, so nothing must be invented.
- **Context:** The other ESC-002 corners are decided — `AC-D3.7` forward (magnifier invoked
  while a drawing tool is active → cancel the in-progress draft, enter `ZOOMING`);
  `AC-D3.7` reverse (a drawing tool selected while `ZOOMING` → exit `ZOOMING`, activate the
  tool); `AC-D3.8` (`ZOOMING → ALARM_PLACING`: activating alarm placement while `ZOOMING`
  exits `ZOOMING` and enters `ALARM_PLACING`). The final corner — **invoking the magnifier
  while `ALARM_PLACING` is active** — was the open question; the "one mode at a time"
  precedent suggested zoom could win, but the user instead chose option (b) to protect a
  pending alarm order. See
  `docs/plan_notes.md` RG-003; `docs/plan_review.md` (PA-R1; transition-table totality);
  `docs/code_review/escalations.md` ESC-002.
- **Options (historical — option (b) was chosen by the user; option (a) was not adopted):**
  1. **(a) Magnifier cancels the pending alarm placement and enters `ZOOMING`** —
     symmetric with the drawing rule in `AC-D3.7` forward: the in-progress/pending alarm
     placement is cleared/discarded and `ZOOMING` becomes the active mode. Consequence:
     `ZOOMING` and `ALARM_PLACING` are mutually exclusive with one precedence rule in both
     directions (`ZOOMING` wins over `ALARM_PLACING`); the transition table stays total;
     no half-placed alarm is left behind. This matched Plan's derived TR-9.
     **← NOT adopted (would have silently discarded a pending alarm order).**
  2. **(b) Refuse to enter `ZOOMING`; show a status-bar hint** (alarm placement keeps
     priority — e.g. "Finish or cancel alarm placement before zooming"). Consequence: the
     magnifier is blocked while `ALARM_PLACING` is active, a pending alarm placement is
     never silently discarded, and the transition table encodes `ALARM_PLACING + magnifier
     → ALARM_PLACING` (no mode change). **← ADOPTED (option (b)); `AC-D3.9`.**
- **Why the user decided (b):** both were defensible product behaviours — (a) follows the
  drawing-cancels precedent and keeps a single "zoom wins" precedence, while (b) protects
  a pending alarm order (a trading action) from being silently dropped. The requirements
  contained **no evidence** that settled it, so the user chose: **protect the pending
  alarm placement** (option (b)).
- **Affected requirement section:** D3 ESC-002 transition semantics (`AC-D3.7`,
  `AC-D3.8`, and the new **`AC-D3.9`** recording this answer); the
  `chart_mouse_router` **transition table** (now total; `ALARM_PLACING + magnifier →
  `ALARM_PLACING`); `docs/plan_notes.md` RG-003 (resolved); `docs/plan_review.md` PA-R1
  (superseded).


---
# Answered (D16 intake — 2026-10-02)

> All three D16 blocking questions were answered by the user on 2026-10-02. D16 is now
> clarified in `requirements.md` (Defect Register `### D16`, Journey 17,
> `AC-D16.1`–`AC-D16.6`; assumptions A27–A32; risks R22–R26). **No blocking question
> remains.**

## Q37 — D16: when the app is reopened after a closure longer than the fetch window, what should the chart show?
- **Status:** answered 2026-10-02
- **Answer (user-confirmed, option (a)):** **Backfill the whole gap.** When the app is
  reopened after a closure longer than the fetch window, the chart must backfill the whole
  gap from the last cached bar up to now — requesting enough history (chunking if needed) —
  so the chart is continuous. Options (b) (drop/limit old cached bars so no hole shows) and
  (c) (fetch a fixed larger window on every load) are **not adopted**.
  - **Interpretation recorded (A32 / DG21):** the reported repro is an **internal** hole
    (older block through 2026-09-18, newer block 2026-09-28…now, hole 2026-09-19…2026-09-27),
    so "from the last cached bar" is implemented as filling the missing span **between cached
    blocks within the displayed range** — a tail-only anchor on `MAX(ts)` would leave the
    reported hole unfixed.
- **Affected requirement section:** D16 / Journey 17 / `AC-D16.1`, `AC-D16.4`, `AC-D16.5`.

## Q38 — D16: how should genuine market closures (weekend/holiday/overnight) render?
- **Status:** answered 2026-10-02
- **Answer (user-confirmed):** **Stay empty.** Genuine market closures render **empty** as
  today and are **not** filled, compressed, or interpolated. D16 is scoped to missing
  **trading-session** bars only. (Collapsing non-trading time remains an out-of-scope feature
  suggestion — `feature_suggestions.md` FS7.)
- **Affected requirement section:** D16 / `AC-D16.3`.

## Q39 — D16: which symbols and timeframes must the fix and verification cover?
- **Status:** answered 2026-10-02
- **Answer (user-confirmed):** **All timeframes + any symbol.** The fix and its verification
  must cover all timeframes (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and
  any symbol, not just `SPY 5 mins`.
- **Affected requirement section:** D16 / `AC-D16.1`, `AC-D16.5`, `AC-D16.6`.

---

# Answered (ESC-023 — Code Reviewer escalation, 2026-10-02)

> ESC-023 (`docs/code_review/escalations.md`) was raised by the Code Reviewer and **approved by
> the user for correction on 2026-10-02**. The correct behaviour is unambiguous from the
> escalation's diagnosis and authoritative sources (NYSE Rule 7.2 year-end accounting-period
> exception; NYSE's own calendar: "Because the holiday falls on Saturday, January 1, 2028, no New
> Year's Day holiday is observed"; the market was open Fri 2021-12-31), so **no blocking question
> was required**. Recorded here as **Q40** for traceability.

## Q40 — ESC-023: is Dec 31 a trading day when New Year's Day falls on a Saturday?
- **Status:** answered 2026-10-02 (resolved from ESC-023's domain evidence; user approved the
  correction). **Not blocking.**
- **Answer:** **Yes — Dec 31 is a trading day.** The Saturday→preceding-Friday observed-day shift
  for New Year's Day carries an explicit **year-end accounting-period exception** (NYSE Rule 7.2):
  when the preceding Friday is Dec 31, the closure is **not** shifted onto it, **no New Year's
  holiday is observed**, and no substitute closure is created (the Saturday Jan 1 is itself
  non-trading as a weekend). `is_trading_day` must return **True** for `2021-12-31`, `2027-12-31`,
  `2032-12-31` and `2038-12-31`.
- **Requirement record:** recorded as **`AC-D16.7`** in `requirements.md`; `AC-D16.3` now excludes
  Dec 31 of a Jan-1-Saturday year from "genuine closure"; assumption **A33** and risk **R27** added;
  `design_gaps.md` **DG22** records the defect's resolution.
- **Downstream (both must change):** the **Task Manager** corrects the wrong `T37-T03` acceptance
  criterion in `docs/tasks/task-graph.json` (which currently asserts "New Year's 2022-01-01 Saturday
  gives 2021-12-31 Friday closed"); the **Build** agent updates `services/market_calendar.py::_observed`
  (New Year's case) and the `T37-T03` assertions in `tests/test_market_calendar.py`. The **Code
  Reviewer** re-verifies ESC-023 on its next pass.
- **Affected requirement section:** D16 / Journey 17 / `AC-D16.3`, new `AC-D16.7`; A33; R27.
