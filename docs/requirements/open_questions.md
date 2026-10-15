# Open Questions

> **2026-10-14 — Batches D24–D40 folded into `requirements.md`; Q41–Q45 ANSWERED (2026-10-14).**
> The D24–D40 requirements were authored on `origin/docs/d24-d28-requirements-architecture` and folded into
> `requirements.md` by the Requirements Analyst. **All five owner items (Q41–Q45, at the end of this file) were
> answered by the owner on 2026-10-14.** D24–D28 are re-statused **as-built / APPROVED** (Q41); the "gated in TWS"
> planning gate is retired (Q42); pop-out always-on-top defaults OFF (Q43); the D37 depth heatmap defaults ON (Q44);
> and the Analyst authored the missing D36–D40 acceptance criteria from the as-built behaviour (Q45). The
> `requirements.md` footer now reads a clean **`Status: READY_FOR_PLAN`**. D1–D23 are unaffected. See
> `design_gaps.md` DG46–DG52 (all resolved 2026-10-14).


> **2026-10-06 (later) — Batch 15 (D21): blocking questions B9–B13 are ANSWERED — D21 clarified and finalised.**
> The user reported **13 UI defects/issues** in one message after D20 was built and green (`04397d9`, 585 tests),
> captured as batch **D21** (sub-defects D21.1–D21.13) in `requirements.md`. All five questions (**B9–B13**) were
> **answered by the user on 2026-10-06** and are recorded verbatim in the **Batch 15 (D21)** section at the end of
> this file. **No blocking question remains**, so `requirements.md` carries `Status: READY_FOR_PLAN`.

> **2026-10-06 — Batch 14 (D20): blocking questions B7–B8 are ANSWERED — D20 clarified and finalised.** The user
> reported the D19 toolbar wrapper's horizontal scrollbar clipping the toolbar label descenders, and answered **B7**
> (verbatim: "Content row 36px + scrollbar lane (~52px total)") and **B8** (verbatim: "As-needed in a reserved
> lane") on 2026-10-06. D20 is now **clarified and finalised**; `requirements.md` carries
> `Status: READY_FOR_PLAN`. See the **Batch 14 (D20)** section at the end of this file.

> **2026-10-05 — Batch 13 (D19): blocking questions B5–B6 are ANSWERED — D19 clarified and finalised.** The user
> reported that **D17 still did not work in the real app** (watchlist would not grow at maximum drag). Repo-validated
> root cause: the toolbar's ~1716px `minimumSizeHint` pinned the central widget so the dock splitter had no slack
> (D19); the D17/D18 harnesses hid the toolbar, masking it. The user answered **B5** (toolbar behaviour when narrow
> — **"Horizontal scroll / elide in place"**) and **B6** (watchlist cap — **"Keep 50%"**) on 2026-10-05, so D19 is
> **clarified and finalised** and `requirements.md` carries `Status: READY_FOR_PLAN`. See the **Batch 13 (D19)**
> section at the end of this file.

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

## Q34 — Docs owner: should Phases 1–5 of `PENDING_IMPLEMENTATION_PLAN.md` be marked `✅ COMPLETE`, and who confirms it? *(that file was deleted 2026-10-15; Q34 remains closed)*
- **Status:** answered 2026-09-27
- **Answer:** **Option 1 — mark Phases 1–5 `✅ COMPLETE`.** Ownership split: the
  **Requirements Analyst owns closing `DOC-2`** (the mark-complete correction) and
  **Code Reviewer verification is the confirming step** (it confirms the drift, then verifies
  the correction was applied). Because `PENDING_IMPLEMENTATION_PLAN.md` was **not in the
  Analyst's file-ownership table**, the Analyst recorded the requirement and this ownership
  split in `requirements.md` (`DOC-2`) rather than editing that root doc (the owner has
  since deleted the file, 2026-10-15). Any residual
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


# Answered (D17/D18 intake — 2026-10-03, B1–B4)

> The user answered all four blocking questions **B1–B4** on **2026-10-03**. D17 and D18 are now
> **clarified and finalised** in `requirements.md` (Defect Register `### D17`/`### D18`, Journeys
> 18–19, `AC-D17.1`–`AC-D17.6` and `AC-D18.1`–`AC-D18.8`; assumptions A34–A36; risks R28–R31).
> **No blocking question remains.** The prior wording framed each question with a "(Recommended)"
> option; the user selected a specific decision for each, recorded verbatim below.

## B1 — D17: what is the denominator for the Watchlist "50%" cap — window width or chart area?
- **Status:** **answered 2026-10-03**
- **Answer (user-confirmed, verbatim: "Change to 50% of chart area"):** the watchlist maximum width
  is **`floor(0.50 × chart_area)`** — measured against the **chart area** (the central region excluding
  both docked panels), **not** `MainWindow` width. This **corrects/supersedes D13's Q25 denominator**
  ("~50% of MainWindow width"): `AC-D13.1`–`AC-D13.3`, Journey 14, **A17** and **R15** are updated in
  lockstep, and the D13 section carries an explicit **supersession note**. Option 1 (keep window-width)
  is **not adopted**.
- **Affected requirement section:** D17 / D13 / Journey 14 + 18 / `AC-D13.1`, `AC-D17.1`; A34; R15/R28.

## B2 — D18: are Active Trader and Portfolio **one dock** or **two docks** that must be equal width?
- **Status:** **answered 2026-10-03**
- **Answer (user-confirmed, verbatim: "One right-dock region, stacked (Recommended)"):** Active Trader
  and Portfolio live in **ONE right-dock region** containing both sections **stacked vertically**, so
  they are **inherently equal width by construction** (the region's width). The **40%-of-chart-area**
  cap applies to that **single region**. Option 2 (two separate docks forced equal) is **not adopted**.
  The current two-`QDockWidget` structure is a wrong shape and is expected to become one region/container
  with the two panels stacked inside (implementation is Plan/Build's call; behaviour must satisfy
  `AC-D18.1`–`AC-D18.8`).
- **Affected requirement section:** D18 / `AC-D18.1`, `AC-D18.3`; A35.

## B3 — D18/B1: how do the Watchlist 50% and Active Trader 40% caps combine?
- **Status:** **answered 2026-10-03**
- **Answer (user-confirmed, verbatim: "Independent caps + chart-minimum rule (Recommended)"):** the
  watchlist (50% of chart area) and the right region (40% of chart area) keep **independent caps**, each
  **additionally clamped against the remaining space** so the chart area keeps a **minimum (~400px)**.
  Consequently **enlarging one dock can force the other to shrink**; both cannot sit at their individual
  maxima if that would starve the chart. Option 2 (a single shared panel budget) is **not adopted**.
  This also settles that the D13 clamp must account for the right dock, not only the window.
- **Affected requirement section:** D17 + D18 / `AC-D13.1`, `AC-D17.1`, `AC-D17.5`, `AC-D18.2`,
  `AC-D18.5`; A34–A35; R29.

## B4 — D17: must the Watchlist handle move in **both** directions, and what are the exact min/cap?
- **Status:** **answered 2026-10-03**
- **Answer (user-confirmed, verbatim: "Confirm defaults (Recommended)"):** the handle must drag **both
  wider and narrower** between the minimum and the cap; the minimum stays **150px**; the default stays
  **~220px**; and the persisted width (D13, Q26) is **still required**. The cap itself is the B1 rule
  (`floor(0.50 × chart_area)`), enforced **during the drag** (the D17 root-cause fix), additionally
  bounded by the B3 chart-minimum rule.
- **Affected requirement section:** D17 / Journey 18 / `AC-D17.1`–`AC-D17.4`; A34; R31.

---

# Open Questions — Batch 12 (D17/D18) — status

> **No open (blocking) question remains for the D17/D18 batch.** All four (B1–B4) were answered
> 2026-10-03 and are recorded above. `requirements.md` is finalised and carries `Status: READY_FOR_PLAN`.
> Any **new** defect reported later starts a fresh intake pass (it does not silently extend this batch).


---

# Open Questions — Batch 13 (D19) — ANSWERED / finalised 2026-10-05

> The user reported **D19** on 2026-10-05: D17 (and D18) were not effective in the real, toolbar-visible app because
> the toolbar pinned the central widget. Both blocking questions (**B5–B6**) were **answered by the user on
> 2026-10-05** and are recorded verbatim below. **No blocking question remains**, so `requirements.md` carries
> `Status: READY_FOR_PLAN`.

## B5 — D19: when the window is too narrow to show every toolbar control, how must the toolbar behave?
- **Status:** **answered 2026-10-05** — resolved; no longer blocking.
- **Why it was blocking:** the toolbar's ~1716px `minimumSizeHint` is the root cause of D19 — it pins the central
  widget so the docks cannot grow. The fix requires choosing a toolbar behaviour that lets the central widget shrink
  while keeping the controls usable; the options have different user-visible trade-offs (extra toolbar row vs a
  horizontal scrollbar vs hidden controls vs moving the toolbar), so the Analyst must not decide it.
- **Options (candidate directions — user to choose; a combination is acceptable if it satisfies `AC-D19.4`):**
  1. **(a) Horizontal scroll / elide in place** — keep the toolbar inside the central widget but let it scroll
     horizontally (or elide labels) when narrow, so the central widget can shrink; the toolbar stays one row (~36px).
  2. **(b) Wrap to multiple rows** — the toolbar reflows onto 2+ rows when narrow; all controls stay visible but the
     toolbar takes vertical space (the chart gets shorter).
  3. **(c) Compress / overflow menu** — shrink control widths and/or move overflow controls into a `»`/overflow menu
     when narrow; keeps one row but some controls are one click deeper.
  4. **(d) Move the toolbar out of the central widget** — use the `QMainWindow` toolbar area (`addToolBar`) with Qt's
     built-in overflow affordance; removes the toolbar from the central widget's minimum, but the toolbar's own
     minimum may still apply and its overflow behaviour must be verified.
- **Affected requirement section:** D19 / `AC-D19.4`, `AC-D19.5`, `AC-D19.6`; Journey 20.
- **Answer (user-confirmed 2026-10-05, verbatim: "Horizontal scroll / elide in place"):** the toolbar **stays
  inside the central widget** — it is **NOT** moved to a `QMainWindow` toolbar area (`addToolBar`) — and remains a
  **single ~36px row**, but its effective minimum width must **no longer pin the central widget**. The chosen fix is
  a **horizontal scroll / elide wrapper around the existing toolbar widget**: when the window is narrower than the
  toolbar's natural width, the controls are reached by **horizontal scrolling** (and/or labels elide) instead of
  holding the central widget at ~1716px. **All controls must remain reachable** via that scroll/elide affordance —
  no control becomes permanently unreachable. Options (b) wrap-to-multiple-rows, (c) compress/overflow menu and
  (d) move the toolbar out of the central widget are **not adopted**.

## B6 — D19: does the watchlist cap stay at 50% of the chart area, or does the user want it raised?
- **Status:** **answered 2026-10-05** — resolved; no longer blocking.
- **Why it was blocking:** the user asked whether the max width is too small. The diagnosis says the **formula is
  correct** (50% of chart area → 858px at chart_area 1716) and the real cause is the toolbar pinning. But if the user
  still wants a **different cap**, the D17/D19 acceptance target changes and `AC-D13.1`/`AC-D17.1`/`AC-D19.1` must be
  updated. Confirming avoids silently keeping or changing a user-visible number.
- **Options:**
  1. **Keep 50% of the chart area** (B1 stands) — the fix is D19 only; the watchlist reaches 858px at the reported
     window size once the toolbar no longer pins the layout.
  2. **Raise the cap** (user names the new fraction, e.g. 60%) — update `AC-D13.1`, `AC-D17.1`, `AC-D19.1` and
     `watchlist_max_width` / `WATCHLIST_CAP_FRACTION` in lockstep.
- **Affected requirement section:** D17 / D19 / `AC-D13.1`, `AC-D17.1`, `AC-D19.1`; B1 (superseded if changed).
- **Answer (user-confirmed 2026-10-05, verbatim: "Keep 50%"):** the watchlist cap **stays at
  `floor(0.50 × chart_area)`** (B1 stands). The cap constant (`watchlist_max_width` / `WATCHLIST_CAP_FRACTION`) and
  `AC-D13.1`/`AC-D17.1` are **unchanged** — the formula is not the problem; D19 fixes only the toolbar pinning.
  Option 2 (raise the cap) is **not adopted**.

---

# Open Questions — Batch 14 (D20) — ANSWERED / finalised 2026-10-06

> The user reported **D20** on 2026-10-06: in the D19 toolbar wrapper the horizontal scrollbar covers the bottom
> of the toolbar labels; they want the toolbar **height increased** so labels read clearly. Repo-validated: the
> D19 wrapper fixes both the toolbar and the `ToolbarScroll` `QScrollArea` at **36px**
> (`ui/main_window.py:102`, `:233`), so the scrollbar is laid out within the same 36px and overlaps the content.
> Both blocking questions (**B7–B8**) were **answered by the user on 2026-10-06** and are recorded verbatim below.
> **No blocking question remains**, so `requirements.md` carries `Status: READY_FOR_PLAN`. **B7** decided: keep the
> content row at **~36px** and give the horizontal scrollbar its **own reserved lane below** it, so the total strip
> grows to **~50–52px** (this **supersedes/relaxes `AC-D19.4`'s `<= ~40px`** bound to a new ~52px container bound,
> keeping the content a single ~36px row and preserving D19's scroll/elide reachability). **B8** decided: reserve the
> scrollbar lane and show the horizontal scrollbar **as-needed** (only when the toolbar content overflows), never
> overlapping the labels.

## B7 — D20: how tall should the toolbar strip become, and how should that reconcile with D19's `AC-D19.4` (`<= ~40px`, one ~36px row)?
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "Content row 36px + scrollbar lane (~52px total)"):** keep the
  toolbar **content row at ~36px** and give the horizontal scrollbar its **own reserved lane below** the content,
  so the scrollbar no longer overlaps the labels and the **total strip grows to ~50–52px**. This **supersedes/
  relaxes `AC-D19.4`'s `<= ~40px` bound** to a new **~52px container-height bound**, while the **content row stays
  a single ~36px row**. Options (b) (grow the content row itself, total ~60px) and (c) (a user-named total height)
  are **not adopted**; the content row must **not** grow and the strip must **not** grow to ~60px.
- **Why it's blocking:** the user asked to "increase the height" but gave no target; the exact height is a
  UI-visual **size** decision (AC-G.1), and D19's `AC-D19.4` currently bounds the laid-out height at
  `<= ~40px` with the D19 test asserting exactly 36px. The requirements cannot be written — or the D19
  constraint responsibly superseded — without the user's target, and over/under-shooting is a user-visible
  layout change (chart vertical space vs label legibility).
- **Options:**
  1. **(a) Recommended — keep the content row ~36px and give the horizontal scrollbar its own reserved lane
     below it** (the scrollbar no longer overlaps the labels; total strip grows to ~50–52px). Supersedes
     `AC-D19.4`'s `<= ~40px` to a new container-height bound (~52px) while the content stays a single ~36px row.
  2. **(b) Grow the toolbar content row itself** (e.g. ~44–48px, more vertical padding) **with the scrollbar in
     its own lane below** (total ~60px). Supersedes both the "one ~36px row" and the `<= ~40px` wording.
  3. **(c) A specific total height in pixels that the user names.**
- **Affected requirement section:** D20 / `AC-D20.1`, `AC-D20.2`; supersession note on `AC-D19.4`; Journey 21; A39.

## B8 — D20: should the horizontal scrollbar be always visible in its lane, or only when the content overflows (or an auto-hiding overlay)?
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "As-needed in a reserved lane"):** **reserve the scrollbar lane**
  (its space is allocated as part of the ~50–52px strip) and show the horizontal scrollbar **only when the toolbar
  content overflows** — the same as-needed behaviour as today — so it **never overlaps the labels**. Options (b)
  (always-visible scrollbar) and (c) (overlay / auto-hiding macOS-style scrollbar) are **not adopted**.
  **Interpretation recorded:** because the lane is *reserved*, the strip's total height stays ~50–52px whether the
  scrollbar is shown or hidden; only the scrollbar widget's visibility changes with overflow (the lane does not
  collapse).
- **Why it's blocking:** the reported defect is the scrollbar **covering** the labels. Whether the lane is always
  reserved, shown only as-needed, or left as an overlay changes the criteria and the user-visible result (a
  permanently visible scrollbar vs one that appears only when narrow). This is a genuine user choice.
- **Options:**
  1. **(a) Recommended — reserve the lane; show the scrollbar only when the toolbar content overflows** (same
     as-needed behaviour as today, but never overlapping the labels).
  2. **(b) Always-visible scrollbar** in its reserved lane.
  3. **(c) Overlay / auto-hiding scrollbar (macOS style)** — **not recommended**: it can still cover the labels
     while scrolling.
- **Affected requirement section:** D20 / `AC-D20.1`, `AC-D20.2`, `AC-D20.3`; Journey 21.

---

# Open Questions — Batch 15 (D21) — ANSWERED / finalised 2026-10-06

> The user reported **13 UI defects/issues** in one message on 2026-10-06 (batch **D21**, sub-defects
> D21.1–D21.13). All five blocking questions (**B9–B13**) were **answered by the user on 2026-10-06** and are
> recorded verbatim below. **No blocking question remains**, so `requirements.md` carries
> `Status: READY_FOR_PLAN` and D21 is **clarified and finalised**. The D21 sub-defects that were already clear
> (D21.1, D21.2, D21.3, D21.7, D21.8, D21.12) were captured with criteria and needed no question.

## B9 — D21.4: how exactly should non-trading time be collapsed, and does it supersede `AC-D16.3`?
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "Collapse between-session gaps"):** collapse only the **gaps
  between trading sessions** (overnight/weekend/holiday), on **intraday timeframes only**; `1 day` is a
  **no-op**; within-session spacing is preserved; D16's backfill/no-silent-hole rules are **unchanged**; with
  **Ext Hours ON** the D1 pre/post bands still render; with **RTH selected** only RTH bars show and **all
  non-RTH time collapses**. This **supersedes the display part of `AC-D16.3`** (recorded; D16's no-silent-hole
  rules `AC-D16.1`/`AC-D16.4` are unchanged). Options (b) (also collapse empty/partial sessions) and (c) (a
  user-named rule) are **not adopted**.
- **Affected requirement section:** D21.4 / `AC-D21.4.1`–`AC-D21.4.4`; supersession of `AC-D16.3`; Journey 23; A45; R37.

## B10 — D21.5: which columns can be added/removed, and is the column layout persisted?
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "Existing 7 columns, persisted"):** the addable set is the
  **existing 7 columns** (`Symbol, Last, Bid, Ask, Chg, Chg %, Vol`); "add" = **re-showing a removed column**;
  the **Symbol column cannot be removed**; the column layout (set + order) is **persisted across restarts**; a
  **right-click on a column header** opens the add/remove/rearrange popup. Options (b) (add new data fields)
  and (c) (a different set/behaviour) are **not adopted**.
- **Affected requirement section:** D21.5 / `AC-D21.5.1`–`AC-D21.5.4`; Journey 24; A46; R38.

## B11 — D21.6: what is the volume-pane height target (baseline + "at least 200% more")?
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "≥360px (3× the 120px cap)"):** the baseline is the current
  **120px** maximum cap, so the volume pane can grow to **at least 360px** (3×), with the **price pane keeping a
  ~200px minimum** and the oscillator unaffected. Options (b) (a fraction of the chart height) and (c) (a
  user-named pixel maximum) are **not adopted**.
- **Affected requirement section:** D21.6 / `AC-D21.6.1`; Journey 22; A47; R39.

## B12 — D21.11/D21.13: which labels become the hide/show buttons, and what is the collapsed geometry?
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "As recommended"):**
  - **Watchlist (D21.11):** keep the **in-panel header label** and turn it into the toggle (it **stays visible
    when collapsed**); **delete the duplicate dock title**.
  - **Right dock (D21.13):** **"Active Trader" = the dock title bar** and **"Account Summary" = the portfolio
    summary label**; both become **toggle buttons**.
  - **Collapsed geometry:** one hidden → collapses **in height** to just its button and the other **expands**;
    **both** hidden → the right dock collapses **horizontally** to the minimum width needed for the two buttons
    (the chart reclaims the width).
  - **Hidden panels' buttons** show the `VIS-D21.1` diagonal strike.
- **Affected requirement section:** D21.11 / `AC-D21.11.1`–`AC-D21.11.3`; D21.13 / `AC-D21.13.1`–`AC-D21.13.4`;
  Journeys 24–25; A41/A42 (`VIS-D21` confirmed); R41.

## B13 — D21.9/D21.10: alarm edit UX and the smart-setup preview lifecycle
- **Status:** **answered 2026-10-06** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-06, verbatim: "As recommended"):**
  - **D21.9 edit surface:** a row **Edit** button opens a small **edit dialog** (price, condition, sound, note)
    with **Save/Cancel**, persisted **immediately**; editing a **triggered/set** alarm is **allowed and keeps its
    state**; the **note column is widened to fill to the end of the popup**.
  - **D21.10 preview line:** the **yellow dashed preview line** is drawn **while the popup is open**, follows the
    price spinbox **live**, and is **removed when the popup closes** (replaced by the real alarm line after Add).
  - **D21.10 condition default:** the auto default (Cross Below when current > alarm price; Cross Above when
    current < alarm price) applies **only on popup open** and is **user-overridable**; when the current price is
    **unknown**, default to **Cross Above**.
- **Affected requirement section:** D21.9 / `AC-D21.9.1`–`AC-D21.9.4`; D21.10 / `AC-D21.10.1`–`AC-D21.10.5`;
  Journey 26; A43/A44; R42/R43.


---

# Open Questions — Batch 16 (D22) — ANSWERED / finalised 2026-10-07

> The user asked how to add tickers to the watchlist; **D22** is a **NEW FEATURE** (in-app "Add symbol" / "Remove
> symbol" affordances) captured 2026-10-07. It is **not** a defect and does **not** reopen D1–D21. All blocking
> questions (**B14–B16**, including the placement/input split **B15a/B15b** and the disconnected sub-question
> **B16b**) were **answered by the user on 2026-10-07** and are recorded verbatim below. **No blocking question
> remains**, so D22's criteria are **final** and `requirements.md` carries `Status: READY_FOR_PLAN`.

## B14 — D22: is the scope add-only, or should the watchlist also support **removing** (and/or **reordering**) symbols?
- **Status:** **answered 2026-10-07** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-07, verbatim: "Add + remove"):** the watchlist editor supports **adding** and
  **removing** symbols — a per-row delete / right-click **"Remove symbol"** that cancels the subscription, removes
  the row, and persists. **Reordering is NOT in scope** (remains a future suggestion, FS10). Options 1 (add-only)
  and 3 (add + remove + reorder) are **not adopted**.
- **Affected requirement section:** D22 / `AC-D22.6`, `AC-D22.7`; Journey 27; A51; FS10.

## B15 — D22: what is the add affordance and where does it live, and what is the input surface?
- **Status:** **answered 2026-10-07** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-07):**
  - **B15a — placement (verbatim: "+ button on header (+ right-click)"):** a small **`+` button on the watchlist
    header strip** (next to the "Watchlist" toggle), **plus** a right-click **"Add symbol…"** entry on the header
    strip (and a **"Remove symbol"** entry, per B14). It must **not** shadow the D21.5 column-header popup and must
    **not** remove the D21.11 collapse toggle. Options that omit the header `+`/right-click (table-body-only or
    toolbar-level) are **not adopted**.
  - **B15b — input surface (verbatim: "Small modal prompt"):** a **small modal dialog** (QInputDialog-style) with a
    text field and **OK/Cancel**; OK confirms, Cancel/Esc aborts. The inline-editable-row option is **not adopted**.
- **Affected requirement section:** D22 / `AC-D22.1`, `AC-D22.2`; Journey 27; A48; DG42.

## B16 — D22: what should happen for an **unknown / invalid** symbol (there is no offline validation)?
- **Status:** **answered 2026-10-07** — resolved; no longer blocking.
- **Answer (user-confirmed 2026-10-07, verbatim: "Require live IBKR validation"):** the add must perform a **live
  IBKR contract lookup** (e.g. `reqContractDetails`) **before** adding; the add is **blocked/held** when the contract
  cannot be resolved, and an **error is surfaced**. On success the symbol is added + subscribed + persisted; on
  failure/unresolvable (no contract, IBKR error, or bounded timeout) **nothing is persisted** and no row is added.
  Options 1 (accept any non-empty symbol) and 3 (accept + flag unknown) are **not adopted**. **Note:** the repo has
  **no** `reqContractDetails`/`contractDetails` path today (see DG43), so this is new plumbing.
- **B16b — adding while IBKR is disconnected (verbatim: "Require connection to add"):** adding is **disallowed while
  IBKR is disconnected** — the add affordance must reflect/deny this (disabled, and/or the confirm refused with a
  message); nothing is added, subscribed, or persisted while disconnected. (This supersedes the earlier provisional
  "add-while-disconnected persists" default, A49.)
- **Affected requirement section:** D22 / `AC-D22.4`, `AC-D22.5`; Journey 27; A49; R46; DG39; DG43.


---

# Open Questions — Batch 17 (D23) — NO BLOCKING QUESTION (2026-10-07)

> After the **D22** build (712 tests green), Code Review raised two **nice-to-have quality** findings
> (**ESC-030**, **ESC-031**) which the user **approved fixing** and asked to run through the full pipeline.
> They are captured as batch **D23** (sub-defects **D23.1 = ESC-030**, **D23.2 = ESC-031**) in
> `requirements.md`. **Neither required a blocking question**, because the correct outcome is unambiguous
> from the source evidence and the user's explicit approval — recorded here for traceability **without**
> opening a `Status: open (blocking)` item. Consequently `requirements.md` carries `Status: READY_FOR_PLAN`.

## D23-Q1 (ESC-030) — can a `reqContractDetails` request be cancelled on the pinned ibapi, and does `AC-D22.2.3` need correcting?
- **Status:** **resolved without a user question** (evidence-derived; the user approved the fix 2026-10-07). Not blocking.
- **Resolution:** No — the pinned `ibapi` (**9.81.1.post1** at D23 report time; the pin is now `ibapi-latest==10.51.1`, and `hasattr(EClient, 'cancelContractDetails')` is still **False** as re-verified 2026-10-14) exposes **no** `EClient.cancelContractDetails`
  (`hasattr(EClient,'cancelContractDetails') is False`; only `reqContractDetails` exists), so on the real TWS path
  the current call raises an `AttributeError` that is silently swallowed and the cancel is a wire no-op. The
  method is also **not called by any production path** (`ContractLookupService.cancel`/`cancel_all` only drop the
  pending entry + stop the bounded QTimer; `_on_disconnected` calls `cancel_all`), so the wire cancel is dead
  code. The correct requirement is therefore a **capability-guarded, documented** cancel: call the client method
  only if present; document that TWS ends the request via its own `contractDetailsEnd`/error and that
  `ContractLookupService`'s local invalidation (bounded QTimer + `cancel_all` on disconnect) is the real safety
  net. **`AC-D22.2.3` (task-level) is superseded/corrected** and architecture `S3` is reconciled — recorded as
  the D23.1 correction record in `requirements.md`. No user decision was needed (the Orchestrator directed
  capturing the capability-guard as the requirement; the user had approved fixing ESC-030).
- **Affected requirement section:** D23.1 / `AC-D23.1.1`–`AC-D23.1.4`; Journey 28; A53/A54; R49; D22 `AC-D22.2.3`
  correction record.

## D23-Q2 (ESC-031) — should `remove_symbol` drop the removed row's own `_row_data` key (`AC-D23.2.*`)?
- **Status:** **resolved without a user question** (evidence-derived + reproduced 2026-10-07). Not blocking.
- **Resolution:** Yes. `remove_symbol` re-indexes `_row_data` with `{(r-1 if r > row else r): values …}` but never
  drops the removed row's own key; removing the **last** row leaves a stale `_row_data[row]` (reproduced: 3-row
  panel, `remove_symbol(last)` → `sorted(_row_data.keys()) == [0,1,2]` while `rowCount() == 2`). The requirement
  is that `_row_data` keys are exactly `range(rowCount())` after any removal, with the missing last/first/only-row
  coverage added. This is a mechanical correctness fix with no user-visible choice. Recorded as D23.2.
- **Affected requirement section:** D23.2 / `AC-D23.2.1`–`AC-D23.2.4`; Journey 28; A55; R50.


---

# Open Questions — Batches D24–D40 — ANSWERED (2026-10-14)

> Folded in from `origin/docs/d24-d28-requirements-architecture` on 2026-10-14. **D24–D28 now read "as-built /
> APPROVED"** in `requirements.md` (Q41); **D36–D40 are as-built / Code-Reviewer APPROVED** and their acceptance
> criteria are now defined (Q45). The items below were relayed to the owner and **all five are answered
> (2026-10-14)** — `requirements.md` carries `Status: READY_FOR_PLAN`.
>
> **2026-10-14 (audit pass):** a requirements-vs-shipped-code audit found **no open question** that the code
> has since settled — Q1–Q45 remain correctly statused. Drift found in that pass (pinned-`ibapi` version,
> stale line references, D24/D25 backing-test mapping) is recorded in `design_gaps.md` DG54–DG58, not here.

## Q41 — Are Batches D24–D28 approved for Plan, or do they remain DRAFT?
- **Status:** **answered 2026-10-14** — no longer blocking.
- **Why it's blocking:** the five section bodies (`requirements.md:2583` D24, `:2698` D25, `:2757` D26, `:2809` D27,
  `:2869` D28) all read "DRAFT … owner review required", while the code is **built and merged to `main`** (Phase 1–4,
  as-built at `b366b19`, 855→898 tests green) and the branch's former footer claimed "owner-approved … READY_FOR_PLAN
  (batches D24–D28)". A clean `READY_FOR_PLAN` cannot be asserted until the owner confirms.
- **Affected requirement section:** D24–D28 (`requirements.md:2583`–`:2917`); the file footer status line.
- **Answer (owner, 2026-10-14):** **Approved — D24–D28 are already developed/coded.** The five section headers/status lines are re-statused **as-built / APPROVED** (consistent with D36–D40), the earlier "DRAFT, owner review required" markers are cleared, and the footer reads `Status: READY_FOR_PLAN`. The owner also asked the Analyst to **verify each D24–D28 section against the shipped code** (see the D24–D28 verification result in `design_gaps.md` DG47 and the requirements sections).

## Q42 — DEC-4 / G5: does the "gated in TWS" constraint get retired for D26?
- **Status:** **answered 2026-10-14** — resolved; no longer blocking.
- **Why it's blocking:** D26 operates on the **live-order path**. The recorded decision (DEC-4) proposes replacing
  the old "gated in TWS, don't worry" per-run constraint with "D26 must land before any live order use" plus dev
  guardrails (mocked `ib_client` only; no live transmission during development; the `IBKR_PORT == 7496` fail-fast
  guard — confirmed in `config/settings.py:20`). The proposal also cites a **"G5"** that has no location in the tree
  (dangling reference — see DG52). Plan/Build must not proceed on an unconfirmed live-order-safety decision.
- **Affected requirement section:** D26 (`requirements.md:2757`); Assumption/Risk entries R55/R57; footer DEC-4.
- **Answer (owner, 2026-10-14):** **Retire the "gated in TWS" planning gate.** The old per-run "gated in TWS, don't worry" assumption is retired so **D26 may be planned/decomposed against the live-order path**. DEC-4 is resolved and recorded in `requirements.md`; the retained safety behaviour (`IBKR_PORT != 7496` fail-fast, explicit user action per order, confirm dialogs, no test transmits) is unchanged. The dangling "**G5**" reference is recorded as resolved (no such item exists).

## Q43 — Pop-outs: always-on-top by default, or standard windows?
- **Status:** **answered 2026-10-14** — resolved (owner-confirmed default: OFF).
- **Why it matters:** it is a user-visible window-manager behaviour recorded only as "Open:" in the footer prose
  (`requirements.md:3131`) with no AC. The draft default (off, standard windows) can stand until the owner rules.
- **Affected requirement section:** D24 (`requirements.md:2583`); footer "Open:" line; DG52.
- **Answer (owner, 2026-10-14):** **Always-on-top default OFF** (standard windows) — confirmed to match the code (`ui/popout_window.py:56` `self._always_on_top = False`; user toggle at `:289`). Recorded as requirement **AC-D24.10** and assumption **A66**.

## Q44 — D37 depth heatmap: default ON or OFF?
- **Status:** **answered 2026-10-14** — resolved (owner-confirmed default: ON).
- **Why it matters:** Journey 32 (`requirements.md:687`) records the depth heatmap as default **ON** "pending owner
  confirmation", while the reviewer recommends **OFF** "consistent with D36" (footprint is OFF by default, owner
  decision 2026-10-13). The code currently adds the item unconditionally (`ui/chart_panel.py:368-369`). See DG51.
- **Affected requirement section:** D37 (Journey 32, `requirements.md:663`/`:687`).
- **Answer (owner, 2026-10-14):** **Depth heatmap default ON** — confirmed to match the code (`ui/chart_panel.py:368` adds `DepthHeatmapItem` unconditionally; `:370` `_depth_enabled_ui = True`). The "default ON (owner decision pending)" wording is removed from Journey 32; the default is recorded as owner-confirmed ON (assumption **A67**). DG51 resolved.

## Q45 — Who authors the missing D36–D40 acceptance criteria, and is the as-built behaviour the requirement?
- **Status:** **answered 2026-10-14** — resolved (Analyst authored the ACs from the as-built behaviour).
- **Why it's blocking:** `AC-D36.*`–`AC-D40.*` are cited as "verified" in Journeys 31–35 and by
  `docs/architecture.md`/`docs/plan.md`, but no Given/When/Then text exists in `requirements.md` (DG46). The
  Quality Bar requires every AC to be independently testable; the owner must confirm the shipped behaviour is the
  intended requirement before the ACs are written from it.
- **Affected requirement section:** D36–D40 (Journeys 31–35, `requirements.md:640`–`:806`); DG46; FI-D24-1.
- **Answer (owner, 2026-10-14):** **The Requirements Analyst authors the missing D36–D40 acceptance criteria from the as-built behaviour.** Written as `AC-D36.1`–`.5`, `AC-D37.1`–`.5`, `AC-D38.1`–`.6`, `AC-D39.1`–`.5`, `AC-D40.1`–`.5` (the IDs Journeys 31–35 cite), sourced from the shipped behaviour and its backing tests (`tests/test_d36_footprint.py` … `tests/test_d40_tws_lifecycle.py`). Where a backing test is narrower than the cited ID it is marked with an **AMBIGUITY** note (AC-D39.5, AC-D40.5). DG46/FI-D24-1 resolved.
