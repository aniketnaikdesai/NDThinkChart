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
> opening a blocking item. Consequently `requirements.md` carries `Status: READY_FOR_PLAN`.

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


---

# Open Questions — 2026-10-15 (REQUIREMENTS escalations ESC-035 / ESC-038) — ANSWERED / MOOT (2026-10-15)

> Two Code Reviewer escalations from the 2026-10-15 live-TWS review were routed to **REQUIREMENTS**
> (`docs/code_review/escalations.json`; long-form evidence `docs/code_review/market_depth_permissions.md`
> and `docs/code_review/rth_single_day_investigation.md`). **Both are now resolved (2026-10-15):** **Q46**
> (ESC-035, depth error 2152) is **MOOT — superseded by D41** (the depth feed is being removed; no (a)/(b)/(c)
> choice is made), and **Q47** (ESC-038, minimum intraday history depth under RTH) is **ANSWERED — 30 trading
> sessions**, recorded as **`AC-D16.8`**. The code claims in both reports were independently re-verified against
> this tree (findings in `design_gaps.md` DG64/DG65).

## Q46 — ESC-035: what should the app do on IBKR depth error **2152** (a *partial* venue-permission report)?

- **Status:** **MOOT — superseded by D41 (2026-10-15).** No option (a)/(b)/(c) is chosen.
- **Resolution:** the D37 depth feed (and, per **Q48**, the Active Trader DOM ladder) is being **removed** by
  **D41**, so there is **no depth feed whose 2152 behaviour needs defining**. The owner did **not** pick options
  (a)/(b)/(c); the correct resolution is **supersession** — the behaviour no longer exists to specify.
- **Consequence:** `design_gaps.md` **DG64** is marked moot; the ESC-035 REQUIREMENTS item is routed to closure
  via the Code Reviewer once D41 lands (the Analyst does not edit `escalations.json`).
  `ui/ticker_session.py::TickerSession.on_depth_error` and `ibkr/error_codes.py`'s 2152 handling are removed
  with the feature.
- **Affected requirement section:** D37 / Journey 32; D41 (`### D41`).


## Q47 — ESC-038: what minimum history depth must each intraday timeframe show under **RTH**?

- **Status:** **answered 2026-10-15** — no longer blocking.
- **Answer (owner-confirmed 2026-10-15):** each intraday timeframe (`1 min`, `5 mins`, `15 mins`, `1 hour`,
  `4 hours`) must show **a minimum of 30 trading sessions** before the current session under **RTH** — 30
  **trading sessions** (not 30 calendar days). Recorded as acceptance criterion **`AC-D16.8`** in
  `requirements.md`. Option (a) (one session is acceptable) is **not adopted**.
- **Practical consequence (implementation — Plan/BUILD):** IBKR caps `1 min` at `1 D` per request and the D16
  backfill (`services/backfill_service.py::find_missing_spans`) anchors at the earliest cached day (never
  backwards), so delivering the floor needs **chained, paced, backwards-extending fetches** (a request-window
  strategy change in `ibkr/market_data.py::TIMEFRAME_CONFIG` / the backfill). If Plan judges this a strategic
  change rather than a constant, the downstream route is **Plan**; the requirement itself is settled here.
- **Closes:** `design_gaps.md` **DG65** (resolved).
- **Affected requirement section:** D16 / Journey 17 / **`AC-D16.8`** (new); `design_gaps.md` DG65.
- **(Distinct BUILD item ESC-037 — the mode-blind day-presence pass — remains routed to BUILD.)**


# Open Questions — 2026-10-15 (Batch 18 / D41 — D36/D37 + whole Active Trader panel removal) — ANSWERED (2026-10-15)

> The owner requested removal of the **D36** footprint and **D37** depth heatmap / imbalance / auction features
> and "all associated code" (Batch **D41**; `requirements.md`). The removal was initially recorded on the
> **conservative default** (see `requirements.md` A68/A69), so the questions below did **not** block Plan — each
> is an owner confirmation that may widen/narrow the removal. They are relayed verbatim because the Analyst
> cannot ask the owner interactively in this run. **Q48** widened the removal to the DOM ladder; **Q49** set the
> persisted-data disposition; **Q50** widened it again to the **entire Active Trader panel (order-entry UI
> included)** and made the **right dock Portfolio-only**. See `requirements.md` A68–A71 and `design_gaps.md`
> DG69/DG71.

## Q48 — D41: does "Depth" mean only the **D37 depth heatmap** floating control, or also the **Active Trader DOM ladder**?

- **Status:** **answered 2026-10-15** — no longer blocking.
- **Answer (owner-confirmed 2026-10-15): YES — the Active Trader DOM ladder is also removed.** "Depth" covers
  **both** the D37 heatmap **and** the DOM ladder. D41 is **widened** to remove the whole depth path:
  `ibkr/market_depth.py` (in full), `ibkr/order_book.py`, the ladder/book rendering in
  `ui/active_trader_panel.py`, `ibkr/bridge.py::update_mkt_depth`, `ibkr/client.py::updateMktDepth`/
  `updateMktDepthL2`, `MainWindow._on_mkt_depth`, the **`DOM` toolbar button** + `_on_dom_toggled` +
  `_subscribe_dom`, `ui/watchlist_panel.py::set_depth_manager`/`on_depth_update`, the `DEPTH` subscription tag,
  `tests/test_market_depth.py`, and the depth parts of `_md_line_count`/`_guard_depth_budget`/`DEPTH_FEED_CAP`.
  The safe-default wording (A68) is superseded; A68 is now **CONFIRMED (y)**.
- **Not removed (order-entry / D18 / D21.13):** `ui/active_trader_panel.py` is **not purely the ladder** — it
  also carries the **`OrderEntryWidget`** (kept **D26** order path), the **`ActiveTraderPanel` shell** (the
  **D18** right-dock section) and the **`header_bar`/`header_button`** (**D21.13** collapse toggle). These are
  **kept**; the removal is ladder-scoped, **not** a blind file delete (see `design_gaps.md` **DG69**). The order
  path's `ref_price` (`active_trader.last_price`, previously fed by the DOM feed) needs a new source (DG69).
  **→ SUPERSEDED by Q50 (2026-10-15):** the owner later confirmed the **whole panel is removed** (order entry
  included) and the **right dock becomes Portfolio-only**, so this "kept" composition no longer holds. See
  **Q50** below.
- **Consequence:** **ESC-039** (the DOM ladder's `SMART` + `isSmartDepth=False` request shape) becomes **moot**
  (no ladder request remains) — see `design_gaps.md` DG66 (updated).
- **Affected requirement section:** D41 (`### D41`, "Scope — REMOVE" DOM-ladder bullet; `AC-D41.1`–`AC-D41.6`);
  A68; Journey 36; `design_gaps.md` DG66/DG69.


## Q49 — D41: what happens to **persisted footprint data** — left in place, or cleaned up?

- **Status:** **answered 2026-10-15** — no longer blocking.
- **Answer (owner-confirmed 2026-10-15, verbatim: "delete"):** the persisted D36 footprint data is
  **removed**. Interpreted as **dropping the persisted footprint data — the `footprint_cache` table + its
  rows** — since the feature that owns it is also being removed. The `footprint_cache` DDL leaves `data/db.py`
  (fresh DBs never create it) **and** an existing user DB's `footprint_cache` table (with any rows) is
  **dropped/deleted** by a small migration. The "leave in place" default (A69) is **superseded**; A69 is now
  **CONFIRMED (y)** with the delete interpretation recorded.
- **Interpretation note (labelled):** the one-line distinction "delete rows only, keep the empty table" vs
  "`DROP TABLE`" is recorded as `design_gaps.md` **DG70**; the recorded default is the **full drop** (the whole
  table), matching "delete".
- **Affected requirement section:** D41 (`### D41`, "Persisted footprint data" bullet; Edge Cases); A69; DG70;
  `design_gaps.md` DG67 (shared inventory).
- **Follow-on:** a small BUILD data-migration step drops the `footprint_cache` table + rows.


## Q50 — D41: is the **whole Active Trader panel** removed (order-entry UI included), and does the **right dock become Portfolio-only**?

- **Status:** **answered 2026-10-15** — no longer blocking.
- **Answer (owner-confirmed 2026-10-15): YES / YES.** **(a)** the **in-app order-entry UI (MKT/LMT/STP/Bracket)
  is removed with the panel** — there will be **no in-app order ticket**; Portfolio's **Close / Close Group /
  Flatten All** and the **SL/TP dialogs** remain and place orders independently through the **retained order
  machinery**. **(b)** the **right dock becomes Portfolio-only** — the **40%-of-chart-area cap** (D18/B2) and the
  **dock title bar** (D21.13, which used the Active Trader header as the title-bar widget) are **re-derived** for
  a single-section dock.
- **Consequences recorded in `requirements.md`:**
  - **D41 scope widened to the whole panel:** **all of `ui/active_trader_panel.py`** (panel shell, ladder/book,
    `OrderEntryWidget`, `header_bar`/`header_button`, and `set_symbol`/`set_last_price`/`last_price`) is removed;
    the file no longer exists. **A70** records the decision; **A68**'s ladder-scoped composition clause is
    superseded.
  - **Retained order machinery KEPT:** `ibkr/orders.py`, `ibkr/validation.py`, the `validate_order()` gate,
    `bracket_order` side-correctness, order-ID reservation, the kill switch and the fail-fast port check stay —
    they guard the retained close/flatten/SL-TP order paths. **D26's safety requirements stay**; only the
    **order-entry UI surface** D26 described goes (see the D26 entry's D41-interaction note).
  - **`ref_price` re-sourced (Plan-level detail):** the retained order path's `ref_price` (was
    `active_trader.last_price`, fed by the DOM feed) **MUST** come from a **retained** source (session last price
    / watchlist price map) — **A71**, **DG71**.
  - **D18 / D21.13 superseded:** the two-section Active-Trader+Portfolio clauses are marked **superseded by D41**
    with reasons; the right dock is single-section with its cap + header re-derived — **AC-D41.7**, **DG71**.
- **Closes:** `design_gaps.md` **DG69** (resolved — whole-panel removal confirmed); **DG70** remains resolved
  (full table drop, Q49).
- **Affected requirement section:** D41 (`### D41`, "Scope — REMOVE"/"Scope — KEEP"; `AC-D41.1`, `AC-D41.3`,
  `AC-D41.4`, `AC-D41.7`); A68–A71; R61/R62; Journey 36; D18; D21.13; D26; `design_gaps.md` DG69/DG71.
- **No new blocking question arose:** the owner confirmed both the panel removal and the Portfolio-only dock; the
  retained `ref_price` source and the single-section cap/header are **Plan-level details** (DG71), not blocking.


> **Reminder:** answering the questions above does **not** reopen D1–D35/D38–D40; Q48 **widened** D41's removal
> scope (the DOM ladder), Q49 set the persisted-data disposition, and Q50 **widened it again** to the **entire
> Active Trader panel (order-entry UI included)** with the **right dock Portfolio-only**. **Q46 was resolved as
> moot** (superseded by D41), not by picking an option.


# Open Questions — 2026-10-15 (Batch 18b / D42 — ESC-042 + ESC-038 resolutions) — 2 non-blocking confirmations

> Two **REQUIREMENTS-routed** Code Reviewer escalations were resolved by a requirements decision on 2026-10-15
> (**D42** in `requirements.md`): **ESC-042** (the `AC-D6.4` vs `AC-D7.1` contradiction — the no-overlap
> guarantee wins, the body is capped at the inter-bar pitch, the 4-px floor is density-aware; supersedes the
> unconditional `AC-D6.4` / "positive gap" `AC-D7.1` wording and unblocks BUILD **ESC-041**) and **ESC-038**
> (RTH depth floor `AC-D16.8` clarified — sessions counted by RTH bars, all five intraday windows fall short —
> plus the new **`AC-D16.9`** for a present-but-RTH-empty trading day, the requirements side of BUILD
> **ESC-037**). Both are **evidence-derived**; the owner already required the 30-session floor (Q47). **No
> blocking question remains.** Both **non-blocking confirmations (Q51, Q52) were answered by the owner on
> 2026-10-15**: **Q51** confirmed the default (a **zero** gap is acceptable at the limit), and **Q52** **widened
> the scope** — the floor now applies to **Ext-Hours (ETH)** charts too, not RTH only (a recorded
> **supersession** of the RTH-only default). `requirements.md` carries `Status: READY_FOR_PLAN`.

## Q51 — ESC-042: at extreme density, is a **zero** gap (abutting bodies, no overlap) acceptable, or must the gap stay **strictly positive**?

- **Status:** **answered 2026-10-15 (owner-confirmed — default upheld).**
- **Answer (owner-confirmed 2026-10-15, verbatim: "Zero gap acceptable at the limit."):** a **zero** gap
  (bodies abutting, **no overlap**) **is** acceptable at the limit (`pitch <= F`, the D6 floor). The default
  adopted below is **upheld unchanged** — no criteria change: `AC-D6.4` (revised) / `AC-D7.1` (revised) already
  encode `gap >= 0` always, with `gap > 0` whenever the pitch exceeds the floor. The strictly-positive-gap
  alternative is **not adopted**.
- **Default adopted (D42.1):** the hard guarantee is **`gap >= 0`** (bodies never overlap). The gap is
  **positive whenever the inter-bar pitch exceeds the D6 floor** (`4` device px); at extreme density
  (`pitch <= F`) the floor yields to the pitch and the gap may be **`0`** (bodies abut) — a zero gap is
  acceptable there, a **negative** gap is never. This is the minimal change that removes the overlap the owner
  reported (ESC-041) while keeping bodies as legible as the density allows.
- **Alternative (not adopted):** require a **strictly positive** gap at all densities (body `< pitch`), which at
  extreme density makes bodies sub-pixel and effectively invisible — traded away because it removes legibility
  without adding information.
- **Affected requirement section:** `AC-D6.4` (revised), `AC-D7.1` (revised), D7 dense-view edge case; D42.1; A72.

## Q52 — ESC-038: does the **>= 30 trading sessions** floor apply to **Ext-Hours (ETH)** charts too, or only to **RTH**?

- **Status:** **answered 2026-10-15 (owner-confirmed: ETH included).**
- **Answer (owner-confirmed 2026-10-15, verbatim: "Extend it to Ext-Hours charts too."):** the **>= 30
  trading-session** floor **applies to Ext-Hours (ETH) charts too**, not RTH only. `AC-D16.8`/`AC-D16.9` are
  **extended** so the floor and the mode-aware present-but-empty-day rule hold for **both** `ext_hours=False`
  (RTH) and `ext_hours=True` (ETH); the two modes share **one** floor and must **not** cross-contaminate (the
  bar cache/key is **mode-aware** in both directions). This **supersedes the RTH-only default** recorded below
  (recorded, not silent).
- **Default adopted (D42.2 — SUPERSEDED 2026-10-15 by the answer above):** the floor was originally recorded
  **RTH-scoped**, exactly as the owner first required it (Q47 / `AC-D16.8`: "under RTH"); an ETH chart uses the
  same calendar-day windows and showed the same one-session symptom, but widening the floor to ETH was **not
  assumed**. **Q52 now supersedes this scoping — ETH is in scope.**
- **Affected requirement section:** `AC-D16.8` (both modes), `AC-D16.9` (both modes); D42.2; A73.

---

# Open Questions — 2026-10-16 (Batch 18c / D43 — ESC-036 second clause) — 1 decision (owner-confirmed-by-default)

> The **ESC-036 second clause** (a **REQUIREMENTS** question the owner directed here) is **DECIDED** on
> 2026-10-16 as **D43** in `requirements.md`. **D41/D42 are not reopened.** `D27.9`'s **"trailing 5-second
> history"** is **unsatisfiable** for the coarse intraday timeframes (`4 hours` = 14400 s, `1 day` = 86400 s —
> 5-sec bars cannot span them; IBKR caps `5 secs` at `3600 S`, so the built request `bar_size='5 secs'`/
> `duration='7200 S'` returns TWS **error 321**). **Decision (D43.1):** prime with a bar size chosen for the
> elapsed forming-period span — **`5 secs`** for `1 min`/`5 mins`/`15 mins`/`1 hour`, **`1 min`** (valid up to
> `1 D`) for **`4 hours`**/`1 day` — with `duration` = the elapsed span clamped into the selected bar size's
> IBKR-accepted range (`[60 S, 3600 S]` for `5 secs`; `[60 S, 1 D]` for `1 min`). This **supersedes D27.9's
> wording** and **revises `AC-D27.9`**. **No blocking question remains** (the decision follows the escalation's
> stated expectation — **owner-confirmed-by-default**); the **coarse-timeframe bar-size switch is a FOLLOW-UP**
> (P2-T30 does not deliver it). `requirements.md` carries `Status: READY_FOR_PLAN`.

## Q53 — ESC-036 (second clause): how should the aggregator be primed for `4 hours`/`1 day`, where 5-second bars cannot cover the forming period at all?

- **Status:** **answered 2026-10-16 (owner-confirmed-by-default — decided from the escalation's stated intent; no owner question required).**
- **Answer (adopted, D43.1):** the priming request's **bar size is selected from the elapsed forming-period span**:
  - **`5 secs`** when the elapsed span is **<= 3600 S** — the **`1 min`**, **`5 mins`**, **`15 mins`** and
    **`1 hour`** timeframes; `duration` = the elapsed span clamped into **`[60 S, 3600 S]`**.
  - **`1 min`** when the elapsed span **exceeds 3600 S** — the **`4 hours`** and **`1 day`** timeframes;
    `duration` = the elapsed span clamped into **`[60 S, 1 D]`** (`1 min` is IBKR-valid up to `1 D`).
  This keeps a **partial current-period seed** and meets `AC-D27.9` on **every** selectable timeframe. It
  **supersedes `D27.9`'s "trailing 5-second history" wording** and **revises `AC-D27.9`**.
- **Why no owner question:** the escalation was **owner-directed** and its stated expectation is explicit —
  "`AC-D27.9` ('forming candle reflect primed history') must be met on every timeframe the user can select,
  including 4h/1d". The decision follows that intent and is recorded as **owner-confirmed-by-default**; the
  alternative ("drop priming for the coarse timeframes") was rejected because it leaves the forming 4h/daily
  candle fabricated from live ticks.
- **Alternatives considered and NOT adopted:**
  1. **Drop priming for `4 hours`/`1 day`** — stops the error-321 warning but leaves the forming candle
     fabricated from live ticks; does not meet the escalation's expectation.
  2. **Seed from the historical partial bar** (zero extra requests) — depends on IBKR returning a **partial
     current-period bar** as the last bar of the `4 hours`/`1 day` historical request, which is **unverified**
     in this environment and would silently degrade to a fabricated bar if IBKR returns only completed bars.
  3. **Prime a shorter `5 secs` span and accept a partial seed** (what P2-T30's clamp does) — the forming
     candle's open/high/low/volume would still be wrong for the coarse periods.
- **Follow-up (not a question):** the **coarse-timeframe bar-size switch is NOT delivered by P2-T30** (which
  only clamps the `5 secs` span into `[60 S, 3600 S]`); a **FOLLOW-UP BUILD task** is needed, and **P2-T30's
  `AC1`/`P2-T30-T11`** (asserting a `5 secs`/`3600 S` request for 4h/1d) become **stale once it lands** and
  must be revised by the Task Manager.
- **Affected requirement section:** D27.9 (revised), `AC-D27.9` (revised), D43.1; A74; R65; DG73.

---

# Open Questions — 2026-10-16 (Batch 19 / D44 — the collapsed Watchlist thin bar) — 1 owner-confirmation item (non-blocking)

> The owner requested (2026-10-16) that the collapsed Watchlist become a **thin vertical bar** that expands to
> the full panel on click, in the **app's own palette** (the mockup's white rounded pill is mockup-tool styling
> only, not a colour choice). **D44 changes the collapsed *appearance*** (the D21.11 collapse already exists) and
> **revises the `## Non-Goals`** (dated 2026-10-16) rather than leaving a Non-Goal standing that the feature
> contradicts. **Three owner-flagged choices are decided with recorded defaults (A75–A77)** and surfaced below
> as **Q54** for owner confirmation — **no blocking item remains**, so `requirements.md` carries
> `Status: READY_FOR_PLAN`. **D1–D43 are not reopened.**

## Q54 — D44: confirm the three decided defaults (bar width, persistence, `+` reachability while collapsed)?

- **Status:** **answered 2026-10-16 (owner-confirmation requested — non-blocking; defaults recorded A75–A77).** Not a blocking item: each default is justified and the pipeline is not halted; an owner override would revise D44 in place.
- **Why it was raised (not a guess):** the owner explicitly said the three points must not be silently assumed. Each is therefore decided **with a stated rationale** and surfaced here so the owner can confirm or override.
- **Decisions (defaults):**
  1. **Bar width (A75):** `WATCHLIST_COLLAPSED_WIDTH = 30px` — within the owner's ~28–32px range; ≥ the 28px header height, room for the rotated label + borders, reads as "a thin bar" and stays clickable.
  2. **Persistence (A76):** the collapsed/expanded state is **NOT persisted**; the app starts **expanded** — consistent with the existing D21.11 collapse (not persisted) and the D10/A36 precedent. No `QSettings` collapse key.
  3. **`+` reachability while collapsed (A77):** the horizontal header strip, the `+` add button (D22.1) and the column-header row are **hidden while collapsed** and **return on expand**; the thin bar's only interactive element is the expand affordance (a ~30px bar cannot hold a horizontal `+` plus a rotated label legibly).
- **Owner action (optional):** confirm the three defaults, or name an override — e.g. "persist the collapsed state", "show the `+` on the bar", or a specific width. An override revises `AC-D44.1`/`AC-D44.4`/`AC-D44.7` and the matching assumption.
- **Affected requirement section:** D44 / Journey 37 / `AC-D44.1`, `AC-D44.4`, `AC-D44.7`; A75–A77.

---

# Open Questions — 2026-10-16 (ESC-057, D44 — `AC-D44.2` measurable restated) — resolved, no blocking item

> **ESC-057** (Code Reviewer, `routed_to: REQUIREMENTS`, **nice-to-have**) found `AC-D44.2`'s measurable and its shipped
> guard disagreeing about what the expand path asserts. It is resolved **from evidence** (the reviewer's independent
> offscreen probe), so **no owner question is required**; recorded here as **Q55** for traceability. **No blocking item
> remains**; `requirements.md` carries `Status: READY_FOR_PLAN`.

## Q55 — ESC-057: what is the measurable for `AC-D44.2`'s expand-restore — the tracked width or the rendered dock width?

- **Status:** **answered 2026-10-16 (evidence-derived from ESC-057's independent probe; no owner question required — nice-to-have).** Not blocking.
- **Answer (adopted — the reviewer's recommended direction):** the measurable is **two-part**:
  1. the **tracked** width is restored **exactly** — `win._watchlist_width == clamp(W)` — which holds **by construction**
     (`_watchlist_width` is never assigned while collapsed, and `_apply_dock_widths` always stores the clamped value); and
  2. the **rendered** dock width is checked **tolerantly** — `watchlist_dock.width() >= WATCHLIST_MIN_WIDTH`,
     `<= watchlist_max_width(...)`, and `> WATCHLIST_COLLAPSED_WIDTH` — because the rendered width is a **Qt layout
     result**, not a value the app can guarantee to echo exactly.
- **Why no owner question:** the reviewer's independent offscreen probe reproduced an **exact** rendered restore for
  every in-range `W` in both clamp branches (150→150, 300→300, cap→cap), and the shipped guard already asserts the
  tolerant rendered bounds; the disagreement was purely about **wording**. The former exact-equality-on-rendered-width
  wording is **superseded** (recorded, not silent).
- **Not evidence:** the orchestrator's earlier residual note in `docs/build/logs/P3-T05.md` (a non-exact 300→314
  restore) was **not reproducible** and is **not treated as evidence** (the orchestrator has owned it as its own error).
- **Alternatives considered and NOT adopted:** **tighten the guard** to assert the exact **rendered** width — rejected as
  the more expensive fix: the guard is a **Build-stage artifact** and a rendered-width echo is a Qt layout result the app
  does not guarantee, so a requirements-side restatement is the correct and cheaper resolution.
- **Affected requirement section:** D44 / `AC-D44.2` (restated); Journey 37; R67; `design_gaps.md` DG74; ESC-057.

# Open Questions — 2026-10-25 (Batch 21 / D46 — `ibkr/orders.py` + the inert order-observation chain) — Q56–Q59 **ANSWERED 2026-10-25**; D46's scope EXPANDED

> The owner asked *"I dont want anything to do with orders so why is there orders.py ?"* and then **confirmed opening a
> batch** to delete it. D45-style lite lane: **no blocking question existed** (defaults recorded in `requirements.md`
> A91–A98). The four items below were surfaced because each is a **user-visible or scope-shaping** choice the analyst
> should not settle silently.
>
> **All four were answered by the owner on 2026-10-25 — verbatim:**
> **Q56** *"why is there any order related code left"* · **Q57** *"there should not be any order related coding. i want
> all of it deleted"* · **Q58** *"yes remove"* · **Q59** *"remove everything"*.
>
> **Q57/Q59 reject the premise of the questions rather than choose among the options offered.** The recorded defaults
> were not wrong about what they described; they answered a narrower question than the owner was asking. The consequence
> is a **scope EXPANSION of D46**, not a new batch: the whole order surface goes (module, observation chain, the three
> zero-consumer order utilities, `IdManager.reserve`, and the stop/target **storage** — the first destructive schema step,
> justified by ESC-060), **A87 / A97 are REVERSED IN PLACE**, and **A92 / A93 / A96 are confirmed**. `requirements.md` D46
> now carries `AC-D46.1`–`AC-D46.13`, A91–A104, R76–R85, and a closed **symbol inventory** (`D46.9`) that makes "all of
> it" auditable and protects the general code that merely carries an order name. **Q56 gets a recorded answer, not just
> a deletion** (see below). **D1–D45 are not reopened**; `requirements.md` carries `Status: READY_FOR_PLAN`.
> **No blocking question remains.**

## Q56 — D46: do the three `EWrapper` order overrides and the three `Bridge` signals go with the module, or stay as inert plumbing?

- **Status:** **ANSWERED 2026-10-25** — A92 is **confirmed**, and the answer widened the scope beyond the question.
- **Question:** the chain is `IBApiClient.orderStatus/openOrder/execDetails` → `Bridge.order_status/open_order/exec_details` → `MainWindow._on_open_order/_on_order_status/_on_exec_details` → `_update_order_status` → the registry. It is **provably** a no-op (nothing ever calls `register()`, so every `get()` returns `None`). Delete the whole chain, or keep it wired as an observation seam for the future?
- **Default:** **remove it all** (A92). With the registry deleted the observers have no target, so "keep them" would mean re-writing them against something that does not exist — and the owner's instruction is that the app should have nothing to do with orders.
- **What a different answer would change:** keeping the signals would leave ~40 lines of order plumbing plus four survivor allow-list entries in `tests/test_d45_removal.py`, and `AC-D46.2`/`AC-D46.4` would be rewritten to require them present-but-inert.
- **Affected requirement section:** D46 / `D46.2`, `AC-D46.2`, `AC-D46.4`; A92 (now owner-confirmed).
- **Answer (owner, 2026-10-25, verbatim):** *"why is there any order related code left"* — followed by Q57's *"i want
  all of it deleted"*. **What changed:** the question ("delete the chain, or keep it as an inert seam?") is **moot**;
  there is no seam to keep. A92 is recorded as **owner-confirmed**, and the deletion set grew (see Q59).
- **The recorded answer to Q56 itself — why any order code was left.** It was left because **D45's A80 and A90
  retained it deliberately** on the premise that the inbound observers needed the registry and could only *observe*.
  The premise was false in effect: `register()` is never called, so the registry is permanently empty, `_on_order_error`
  (the only handler that phrased a rejection) was guarded by a lookup that always returned `None`, and every observer
  wrote into that same empty dict. **The lesson:** a "retained and inert" decision was never audited for
  **reachability** — "it only observes" was treated as evidence when it was an assertion. D46's symbol inventory
  (`D46.9`) is the mechanism that makes the next such decision auditable.

## Q57 — D46: is `Error [<code>]: <TWS message>` (8 seconds) enough for 201/103/202, or should the app's own "Rejected"/"Cancelled" wording and the order number be restored in a reachable place?

- **Status:** **ANSWERED 2026-10-25** — the default (A93) stands **in substance**, but the owner **rejected the
  premise** of the question rather than choosing an option.
- **Question:** the richer message (`Order #<id> Rejected: …`, 12 s) exists only inside `_on_order_error`, which the always-empty registry made **unreachable** — so today the owner already sees the plain line: `Error [201]: Order rejected - reason: …`, `Error [103]: Duplicate order id`, `Error [202]: Order Canceled - reason: …`. Keep exactly that, or have the app add a verdict/order-id prefix so the line is easier to scan?
- **Default:** **keep exactly what is shown today** (A93): no new formatting, no order identity, same 8000 ms. The app no longer knows which order an error belongs to, so an order-number prefix would be a guess dressed as fact.
- **What a different answer would change:** it adds a small formatting requirement + a test per code; visibility itself is required either way (`AC-D46.3`), because the owner's constraint is *"TWS errors must still surface"*.
- **Related, same answer:** `tests/test_order_rejections.py` survives **reduced** (A95) — the two registry cases removed, the "unrelated error" case repointed at the generic line, both `classify_error` cases kept.
- **Affected requirement section:** D46 / `D46.3`, `AC-D46.3`, `AC-D46.5`; A93 (now owner-confirmed), A95.
- **Answer (owner, 2026-10-25, verbatim):** *"there should not be any order related coding. i want all of it
  deleted"*. **What changed:** the option set was wrong, not the choice within it. The owner does not want a **plainer
  order line** or a **richer** one — they want **no order coding at all**, so no order verdict, order number or
  order-specific formatting may be added anywhere. **A93's substance survives unchanged and is now owner-confirmed**:
  201/103/202 keep surfacing on the existing generic line (`Error [<code>]: <TWS's own message>`, 8000 ms) because that
  line is **not** order-specific — it is every TWS error's surface (`AC-D46.3`, A100). The question the owner actually
  asked ("why is there any order related code left") is answered in **Q56**, and its consequence is the D46 scope
  expansion recorded in Q59.

## Q58 — D46: there is a **second**, unused `UserOrder` dataclass in `data/models.py` — remove it too?

- **Status:** **ANSWERED 2026-10-25** — **"yes remove"**. A96 is **owner-confirmed**; `AC-D46.8` is no longer conditional.
- **Question:** `data/models.py::UserOrder` (`order_id`, `symbol`, `action`, `total_qty`, `order_type`, `lmt_price`, `aux_price`, `status`, `parent_id`, `oca_group`, `transmit`) is a **different class** from `ibkr/orders.py::UserOrder` and has **zero** consumers — its only reference in the repo is `tests/test_ui_smoke.py:48`'s `hasattr`. Deleting `ibkr/orders.py` does not delete it. Remove it as well, or leave it?
- **Default:** **remove it and the smoke assertion** (A96) — otherwise, after this batch, the app still contains an order-only data model with no purpose, which is precisely the question the owner asked.
- **What a different answer would change:** `AC-D46.8` becomes vacuous and `tests/test_ui_smoke.py` is untouched.
- **Affected requirement section:** D46 / `AC-D46.5`, `AC-D46.8`; A96 (now owner-confirmed); `design_gaps.md` DG79
  (**resolved**).
- **Answer (owner, 2026-10-25, verbatim):** *"yes remove"*. **What changed:** nothing narrow — the recorded default
  stands, now as an owner decision; the same task removes `data/models.py::UserOrder` and the
  `tests/test_ui_smoke.py:48` `hasattr` assertion together (R81).

## Q59 — D46: is there anything else order-named you want swept in this batch?

- **Status:** **ANSWERED 2026-10-25** — **"remove everything"**. This **REVERSES A97** and, with it, **A87**: both
  leftovers named in the question go.
- **Question:** two order-motivated leftovers are deliberately **out of scope** for D46: (a) `ibkr/id_manager.py::IdManager.reserve(n)` — the D26.2 contiguous-ID reservation for multi-leg orders, now with tests only (the rest of `id_manager` is shared with market-data reqId allocation and stays); (b) the retained `positions`/`trade_groups` `stop_loss`/`take_profit` **storage** (A87 — the UI columns and every setter are already gone, and per **ESC-060** a live position update still clears the values, so nothing may claim they persist). Name either if you want it removed now; otherwise both stay.
- **Default:** **leave both** (A97) — neither is part of `ibkr/orders.py` or the observation chain, and widening a delete-only batch is the pattern that has cost workers before (memory 2026-10-15).
- **What a different answer would change:** (a) would add `ibkr/id_manager.py::reserve` + the four pure `reserve` cases in `tests/test_id_manager.py` and force one mixed case to be rewritten; (b) would be a **destructive schema change** and needs its own migration requirement, not a deletion task.
- **Affected requirement section:** D46 "Scope — KEEP"; the new **D46.10 / D46.11 / D46.12** and `AC-D46.10`–
  `AC-D46.12`; **A87 (reversed → A99)**, **A97 (reversed in part → A100/A101)**, A102; `design_gaps.md` **DG80**
  (resolved), **DG84**, **DG85**, **DG86**.
- **Answer (owner, 2026-10-25, verbatim):** *"remove everything"* — having been shown A87's storage retention and
  A97's two named leftovers. **What changed (both halves, verified in-repo before being written down):**
  1. **`ibkr/id_manager.py` — the module is NOT order-only, so it stays; `reserve()` goes.** `get_id()` allocates
     **market-data and realtime reqIds** (`ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`) and
     `set_next_valid_id()` is called at `ibkr/client.py:184`, so deleting the module would take the chart's
     subscription machinery with it. Only **`IdManager.reserve`** (`ibkr/id_manager.py:19-30`, the D26.2 multi-leg
     allocation) is order-only: its callers are **tests only** (`tests/test_id_manager.py:12,23,34,41,62`). **Deleted**
     — A101 / D46.10. (Also checked: `IBApiClient.nextValidId` is the **connection-established** hook, not order
     plumbing, so it stays — A102 / DG82.)
  2. **The retained `positions` / `trade_groups` `stop_loss` / `take_profit` columns and the `Position` / `TradeGroup`
     (and `ibkr.account.Position`) fields are DROPPED.** This **reverses A87** (recorded in place, original wording
     kept) and makes **the first destructive schema step in the project** — the end state is fixed, the mechanism is
     Plan's (D46.12, DG86). **The honest justification is ESC-060, not preference:** the values were **already cleared
     by the first live update** of any row, and no setter has existed since D45, so the columns could only ever hold
     `NULL`. **The drop destroys nothing that survived** — but every **row** must be preserved (R82).
  **Consequence for the documents:** the statements corrected this morning under ESC-060 ("the columns are kept, but an
  update from TWS writes them empty") are **superseded** — the trail must read **kept → cleared → dropped** and must not
  stand as two live claims (`D46.13`, `design_gaps.md` **DG84**).

# Open Questions — 2026-10-26 (Batch 22 / D47 — migration-plan section-8 questions Q1–Q4)

> The attached migration plan (updated, no soak) left its **section-8 owner questions Q1–Q4** open (its Q5 was
> answered by the 2026-10-26 approvals above). Per the scope-question rule they blocked Plan, so they were recorded
> here as **Q60–Q63** — asked in this file **and** in the analyst's final reply with recommended defaults — and in
> `requirements.md` (D47 / A106–A109). **Q60 is answered-by-default** (the plan already justifies it, so no owner
> question was required); **Q61–Q63 were open (blocking) with a recommended default where one was safe (Q62, Q63)
> and none where the fact was not derivable (Q61) — all three ANSWERED by the owner on 2026-10-26 (verbatim below).**
> **No blocking question remains**; `requirements.md` carries `Status: READY_FOR_PLAN`.

## Q60 — D47 (plan §8 Q1): retire the density-cap ACs (D6/D9/D42/Q-4) for library `barSpacing`?

- **Status:** **answered-by-default 2026-10-26 — YES, retire the density-cap language for `barSpacing`** (no owner question required). Not blocking.
- **Answer (adopted, D47.6 / A106):** the pyqtgraph density-cap wording of `AC-D6.4` / `AC-D7.1` / `AC-D9.1` is
  **proposed for retirement** and the no-overlap guarantee is restated in `barSpacing` terms (DG94). The retirement
  lands only with this answer recorded here — the pyqtgraph engine keeps satisfying the old ACs until cutover.
- **Why no owner question:** the migration plan already states the replacement as an **owner-visible AC change**
  ("per-mode series, `barSpacing` replaces density caps"), so the default is plan-justified, not invented.
- **What a different answer would change:** keeping both wordings live forces every density case to pass on two
  contradictory spacings; rejecting retirement blocks T10 and the Phase 3 exit.
- **Affected requirement section:** D47.6 / `AC-D47.6`; A106 (proposed); T10; DG94; R89.

## Q61 — D47 (plan §8 Q2): what are the `.app` size and signing/notarisation plans?

- **Status:** **answered 2026-10-26** — owner-confirmed; no longer blocking.
- **Question:** Chromium + vendored JS grow the bundled `.app` by a measured delta, and the new binaries must pass
  through the existing signing/notarisation flow (or a stated change to it). What is the budgeted increase, and
  does the current signing identity/procedure cover the `QWebEngineView` + vendored tree unchanged?
- **Recommended direction:** none from the analyst — bundle size and signing identity are release facts, not
  derivable defaults (A109). Plan measures the delta and names the mechanism (DG89); the owner confirms.
- **What the answer changes:** `AC-D47.8`'s packaging phase, R87, and any Non-Goal/Constraints wording on bundle size.
- **Affected requirement section:** D47.8 / `AC-D47.8`; A109; DG89; R87.
- **Answer (owner, 2026-10-26, verbatim): "Measure first, no fixed budget"** — measure-first: Plan measures the Phase 0 size delta and reports; the owner sets the budget from the numbers. Note whether the current signing flow covers the Chromium/vendored tree as a Phase 0 finding.

## Q62 — D47 (plan §8 Q3): how many pop-outs may realistically stay open?

- **Status:** **answered 2026-10-26** — owner-confirmed; no longer blocking.
- **Question:** each LWC pop-out carries engine + bridge cost; what is the realistic concurrent-pop-out ceiling?
- **Recommended default (A107):** the cap **stays at the D24 10** unless the owner names another number. Rationale:
  preserves the approved D24 behaviour; raising it needs the memory/bridge evidence in DG90.
- **What a different answer would change:** a higher cap re-sizes DG90's per-pop-out memory accounting and the
  bridge backpressure counters (DG91); a lower cap revises the D24 pop-out ACs.
- **Affected requirement section:** D47.8 / Journey 40; A107; DG90/DG91.
- **Answer (owner, 2026-10-26, verbatim): "Keep 10 (Recommended)"** — keep D24 10; Phase 9 verifies 1, 3, 6 against it.

## Q63 — D47 (plan §8 Q4): crosshair style — accept drift, or reproduce the exact D2/Q33 pill via custom primitives?

- **Status:** **answered 2026-10-26** — owner-confirmed; no longer blocking.
- **Question:** the D2/Q33 crosshair chip (grey pill, white text, Y-axis lane) is an owner-confirmed visual
  reference; the library-native crosshair + axis label will not be pixel-identical. Accept the drift, or build the
  exact pill as a custom primitive driven per move?
- **Recommended default (A108):** **accept drift** (library-native crosshair + axis label). Rationale:
  pixel-exact reproduction needs a custom primitive driven on every cursor move; drift is the library-native
  outcome. The D2/Q33 ACs stand unchanged until the owner decides.
- **What a different answer would change:** exact-pill adds a custom-primitive work item to Phase 5 and a
  pixel-parity case to the matrix; drift keeps the matrix row as behaviour-parity only.
- **Affected requirement section:** D47.7 / `AC-D47.7`; A108; Journey 40.
- **Answer (owner, 2026-10-26, verbatim): "Accept drift (Recommended)"** — accept drift to the library-native crosshair (no exact-pill custom primitives); D2/Q33 stands only where still applicable.

# Open Questions — 2026-10-28 (Batch 24 / D49 — Q64–Q66 ANSWERED 2026-10-28; no blocking gap)

> All five D49 items are owner-ordered with concrete fix directions (`POPOUT_CHART_CODE_TRACE_REPORT.txt`, findings 1–5), so no scope or semantic question blocks Plan. Q64–Q66 were non-blocking confirmations and are now ANSWERED by the owner on 2026-10-28 (all three standing defaults accepted verbatim); `requirements.md` carries `Status: READY_FOR_PLAN`.

## Q64 — D49.3: is the default error-state presentation (in-pop-out message + status text, ESC-070 model) accepted, or do you want different copy/placement?

- **Status:** **answered 2026-10-28 — owner-confirmed (accepted the standing default verbatim).**
- **Answer (owner, 2026-10-28):** accept the in-pop-out message + status text (ESC-070 model).
- **Question:** the pop-out whose chart-host fails to start shows an in-pop-out message area + status text (visible, unambiguous, distinct from empty-data), keeping the debug-level diagnostic log. Accept, or name alternative copy/placement?
- **Recommended default (A124):** accept the ESC-070-model default — the testable outcome (error visible, never mistaken for no-data, log retained) does not depend on pixel details.
- **What a different answer would change:** `AC-D49.3`'s presentation clause and the D49.3 visual reference; no logic change.
- **Affected requirement section:** D49.3 / `AC-D49.3`; A123–A124.

## Q65 — D49: do you want to name a live-TWS validation step, or is offscreen-only acceptance enough?

- **Status:** **answered 2026-10-28 — owner-confirmed (accepted the standing default verbatim).**
- **Answer (owner, 2026-10-28):** offscreen-only acceptance; no live-TWS step named.
- **Question:** every D49 item is measurable offscreen (seeded cache, failure injection, broken host, signal spies, hold-lifecycle probe). If you want a live check (e.g. cold-start restore of a named symbol, or a named live pop-out session), name it and it becomes an owner-gated acceptance step; otherwise live behavior is not assumed and no live step is required.
- **Recommended default:** offscreen-only (no live step assumed) — no live gate is presumed; any live check must be owner-named.
- **What a different answer would change:** a named live step joins `AC-D49.1` (and only that AC) as an owner-gated clause.
- **Affected requirement section:** D49 / `AC-D49.1`; quality-bar note in the Batch 24 header.

## Q66 — D49.5: is a verified-close with no code change an acceptable delivered outcome (assuming the probe finds no lasting effect)?

- **Status:** **answered 2026-10-28 — owner-confirmed (accepted the standing default verbatim).**
- **Answer (owner, 2026-10-28):** YES — verified-close with no code change counts as delivered.
- **Question:** if the hold-count verification finds no lasting effect (count self-heals via session teardown), D49.5 closes with the verification record and no code change. Confirm that reads as delivered, not dropped — the batch was ordered as "explicitly nothing dropped," and this question exists so a zero-diff D49.5 is never misread as one.
- **Recommended default (A126):** YES — verified-close counts as delivered; the per-owner fix lands only on a confirmed lasting effect.
- **What a different answer would change:** a NO converts D49.5 into an unconditional fix work item (idempotent per-owner acquire/release regardless of probe outcome).
- **Affected requirement section:** D49.5 / `AC-D49.5`; A126; R98.

---

# Open Questions — 2026-10-28 (Batch 25 / D50 — drag-editing for LWC drawings; Q67–Q71 ANSWERED 2026-10-28)

> Owner-scheduled batch: drag-editing for LWC drawings. The render path (bind fix), the `PageDrawing` /
> `drawing_controller.created` commit surface and the `DrawingStore` update paths are settled inputs (A127–A129);
> creation is not re-specified. `requirements.md` carries the `### D50` block (`Status: READY_FOR_PLAN`, `AC-D50.1`–`AC-D50.5` final 2026-10-28),
> Journey 43, A127–A132 and R99–R101. **Q67–Q71 are answered owner-confirmed verbatim 2026-10-28 (Q70 = (c) Both previously recorded); no blocking question remains.** **D1–D49 are NOT reopened.**

## Q67 — D50.1: which edits exist — whole-drawing move vs anchor/handle drags — for each kind (trendline, horizontal, zone, fibonacci, measure)?

- **Status:** **answered 2026-10-28 — owner-confirmed verbatim ("both").**
- **Answer (owner, 2026-10-28):** **both** — whole-move for all five kinds **plus** anchor drags per kind's anchors.
- **Question:** for each of the five kinds, is the edit (a) whole-move **plus** anchor/endpoint drags where the kind has anchors, (b) whole-move only for every kind, or (c) an owner-named per-kind matrix?
- **Recommended default (R-a):** (a) — whole-move for all five kinds, plus anchor drags per kind's anchors (trendline/fibonacci/measure endpoints, zone edges/corners, horizontal price level). Rationale: matches the drawing kinds' geometry; whole-move-only would leave anchored drawings unreshapable.
- **What a different answer would change:** (b) removes every anchor-handle AC and test; (c) replaces `AC-D50.1` with the named matrix.
- **Why it's blocking:** the per-kind matrix, the handle set, and the geometry test matrix differ completely per answer — `AC-D50.1` cannot be written without it.
- **Affected requirement section:** D50.1 / `AC-D50.1` (provisional); Journey 43; R99.

## Q68 — D50.2: handle UI — which handles appear, in which selection state, and how do they behave on locked drawings?

- **Status:** **answered 2026-10-28 — owner-confirmed verbatim.**
- **Answer (owner, 2026-10-28):** handles appear **only while their drawing is selected**; a **locked drawing offers no draggable handle**.
- **Question:** which handles appear (endpoints/corners/edges/level per kind), and when — only while the drawing is selected, or also unselected? And what does a locked drawing show: no handles, or visible-but-not-draggable handles?
- **Recommended default:** handles appear **only while their drawing is selected** and hide on deselect; a **locked drawing offers no draggable handle** (selection highlight only). Rationale: selection-gated handles are the conventional affordance; a locked drawing must not present a drag affordance.
- **What a different answer would change:** `AC-D50.2` handle-visibility clauses; persistent handles add an AC-G.1 visual reference for the unselected state.
- **Why it's blocking:** handle visibility is UI-visual (AC-G.1 gate: confirmed reference or provisional assumption) and `AC-D50.2` cannot be finalized without the selection/locked rules.
- **Affected requirement section:** D50.2 / `AC-D50.2` (provisional); Journey 43.

## Q69 — D50.3: lock semantics — what exactly does a locked drawing forbid, operation by operation?

- **Status:** **answered 2026-10-28 — owner-confirmed verbatim (Recommended: (i)+(ii)+(iii); colour allowed).**
- **Answer (owner, 2026-10-28):** locked forbids **(i) + (ii) + (iii)** — no drag initiation, no move, no delete — while **(iv) colour/style change stays allowed**; consequently a group recolour repaints **all current members including a locked member's** stored colour (settled Q70 (c) interaction, stated explicitly as requested).
- **Question:** does a locked drawing forbid (i) drag **initiation**, (ii) move/commit, (iii) **delete**, (iv) **colour/style change** — each answered separately?
- **Recommended default:** locked forbids **(i) + (ii) + (iii)** — no drag initiation, no move, no delete — while **(iv) colour/style change stays allowed**, consistent with the settled Q70 stored-colour semantics. Rationale: lock protects geometry and existence; colour is not geometry. Note the interaction this leaves open: under (c) a group recolour repaints **all current members**, so it would also repaint a **locked** member's stored colour unless the Q69 answer forbids (iv) — say so explicitly when answering. Option "locked only hides handles" is explicitly NOT offered — `gestures.js` has no drag-initiation path, so handle-hiding alone cannot enforce anything at the `drag_drawing` operation surface.
- **What a different answer would change:** forbidding (iv) as well moves colour under the lock in `AC-D50.3`/`AC-D50.4`; allowing (iii) keeps delete available on locked drawings.
- **Why it's blocking:** `AC-D50.3` must assert refusal **at the operation surface with no store write**; a handle-level-only lock would leave locked drawings movable (R100).
- **Affected requirement section:** D50.3 / `AC-D50.3` (provisional); A129; R100.

## Q70 — D50.4 / 3.3: group colour — default-for-new, or override-for-all? (SETTLED 2026-10-28: (c) Both)

- **Status:** **answered 2026-10-28 — owner picked (c) Both; no longer blocking.**
- **Answer (owner, relayed 2026-10-28):** **(c) Both** — new drawings take the group colour **at creation** (stored on the drawing, surviving leave-group); recolouring a group repaints **all current members** (updating stored colours). Dragged/edited drawings keep their own stored colour; mid-drag recolour handling per A132 (analyst decision, as delegated).
- **Question:** the pending 3.3 decision: is group colour the **default for new drawings only** (an edit preserves the drawing's own colour), or an **override for all members** (an edit preserves group linkage and the group colour wins)?
- **Recommended default:** none from the analyst — this is a genuine owner choice, so **both readings are carried**: R-a (default-for-new → edit preserves own colour) / R-b (override-for-all → edit preserves linkage, group wins). Rationale for carrying both: building colour-preservation on an assumed reading risks a direct contradiction when 3.3 lands (R101).
- **What the answer changes:** `AC-D50.4` is written in exactly one reading; the other is retired in place (never silently dropped).
- **Why it was blocking (resolved):** `AC-D50.4` could not be finalized on an assumed reading (R101) — the pick settles it; `AC-D50.4` is now final, A130 resolved, A132 records the delegated mid-drag rule.
- **Affected requirement section:** D50.4 / `AC-D50.4` (blocked); A130; R101.

## Q71 — D50.5: confirm persistence + fan-out — store update, session-reload restore, single view sync, offscreen-measurable?

- **Status:** **answered 2026-10-28 — owner-confirmed verbatim ("yes").**
- **Answer (owner, 2026-10-28):** **yes** — every committed edit (a) updates the store, (b) survives session reload, (c) syncs to all views **exactly once per change** (the D49.4 pattern), and (d) is accepted **offscreen** (seeded store + committed coordinates + reload-restore + fan-out count, no live TWS).
- **Question:** confirm that every committed edit (a) updates the store, (b) survives session reload, (c) syncs to all views **exactly once per change** (the D49.4 pattern), and (d) is accepted **offscreen** (seeded store + committed coordinates + reload-restore + fan-out count, no live TWS)?
- **Recommended default (A131):** yes to all four. Rationale: store-update + reload-restore is the existing persistence contract; single fan-out reuses the D49.4 pattern; offscreen matches the D49 quality bar.
- **What a different answer would change:** a NO on (c) writes a multi-fan-out tolerance into `AC-D50.5`; a live-step requirement adds an owner-named live clause.
- **Why it's blocking:** finalizes the `AC-D50.5` measurable (fan-out count + reload equality); the default is safe but the fan-out clause touches D49.4 semantics, so it is asked rather than assumed.
- **Affected requirement section:** D50.5 / `AC-D50.5` (provisional); Journey 43; A131.

---

# Open Questions — 2026-10-29 (Batch 26 / D51 — follow-live viewport; Q72–Q76 ANSWERED 2026-10-29)

> New batch D51: the main-chart viewport must not be yanked to the newest bar on live updates while the user has scrolled back. All five questions below are answered-owner-confirmed 2026-10-29 — `AC-D51.1`–`AC-D51.5` are FINAL (Journey 44, A135, R103) and D51 carries `Status: READY_FOR_PLAN`. Repro-first measurables, offscreen where possible. **D1–D50 are NOT reopened.** (D49.6, the timezone handoff in the same batch, is fully derivable and asked no question.)

## Q72 — D51.1: what counts as "following the live edge" vs "scrolled back"?

- **Status:** **answered-owner-confirmed 2026-10-29.**
- **Answer (owner, 2026-10-29):** copy TradingView behavior — newest-bar-slot-visible = following (library shiftVisibleRangeOnNewBar semantic, verified in vendored 5.2.1); any pan/zoom away = scrolled back, viewport stays put on new bars; return only via explicit action (Fit/reset, scrollToRealTime, go-to-realtime affordance when new bars arrive while away).
- **Why it's blocking:** `AC-D51.1`'s pass/fail turns entirely on the rule — a last-bar-visible rule, a tolerance rule, and an edge-pinned rule produce different follow-state probes and different tests.
- **Question:** is the chart "following" iff the newest bar's slot is inside the visible range (and any user pan/zoom away means scrolled back) — or do you want a different rule (e.g. newest bar within N bars of the right edge, a pixel tolerance at the edge, or edge-pinned-only)?
- **Recommended default:** newest-bar-slot-visible = following; any user pan/zoom away = scrolled back. Rationale: the simplest testable rule, and it matches the complaint ("don't yank once I moved").
- **What a different answer would change:** `AC-D51.1`'s measurable and the follow-state probe (tolerance/threshold cases replace the binary visible-slot check).
- **Affected requirement section:** D51.1 / `AC-D51.1` (provisional); Journey 44.

## Q73 — D51.2: while scrolled back, do arriving new bars auto-resume follow, or does the viewport stay put?

- **Status:** **answered-owner-confirmed 2026-10-29 (option (a)).**
- **Answer (owner, 2026-10-29):** **(a)** — while scrolled back, new bars stay put, no auto-resume; follow returns only on pan-back-to-edge or Fit/reset.
- **Why it's blocking:** `AC-D51.2` must assert either "viewport unchanged until the user acts" or a resume trigger — the two are opposite tests.
- **Question:** while away, (a) stay put until the user pans back to the edge or invokes Fit/reset (no automatic resume on new bars), or (b) auto-resume follow when new bars arrive (with an owner-named trigger), or (c) an owner-named third rule (e.g. resume after N seconds idle)?
- **Recommended default:** (a) stay put; resume only on user pan-back-to-edge or Fit/reset. Rationale: the user scrolled back to look at something — moving the viewport under them on every tick is the reported defect.
- **What a different answer would change:** `AC-D51.2` gains the resume-trigger clause and its timing/count cases instead of the stay-put assertion.
- **Affected requirement section:** D51.2 / `AC-D51.2` (provisional); Journey 44.

## Q74 — D51.3: what does explicit Fit/reset do?

- **Status:** **answered-owner-confirmed 2026-10-29 (option (a)).**
- **Answer (owner, 2026-10-29):** **(a)** — explicit Fit/reset frames all loaded bars and re-engages follow, plus the go-to-realtime affordance.
- **Why it's blocking:** `AC-D51.3` must name the framing Fit produces and whether it re-engages follow — "frames all loaded bars" vs "frames the visible session" vs "returns to a stored view" are different assertions.
- **Question:** does Fit/reset (a) frame all loaded bars and re-engage follow, or (b) frame a different owner-named range, or (c) restore a stored pre-scroll view?
- **Recommended default:** (a) Fit frames all loaded bars and re-engages follow. Rationale: fits the existing Reset affordance (D3) and gives the user one explicit way back to the live edge.
- **What a different answer would change:** `AC-D51.3`'s range + follow-state assertions.
- **Affected requirement section:** D51.3 / `AC-D51.3` (provisional); Journey 44.

## Q75 — D51.4: is follow/scroll state remembered per symbol across switches?

- **Status:** **answered-owner-confirmed 2026-10-29 (option (a)).**
- **Answer (owner, 2026-10-29):** **(a)** — per-symbol memory — switching back restores viewport + follow state (deliberate improvement over TradingView for the multi-symbol alarm workflow; supersedes the earlier (b)).
- **Why it's blocking:** `AC-D51.4` must assert either per-symbol memory (restore viewport + follow state on switch-back) or a fresh follow on every switch — opposite tests.
- **Question:** (a) remember viewport + follow state per symbol (switching back restores where you were), or (b) every symbol switch starts following the live edge, or (c) an owner-named scope (e.g. memory only within the session)?
- **Recommended default:** (a) per-symbol memory across switches. Rationale: preserves the user's place per ticker; a fresh-follow default would re-introduce the yank on every switch-back.
- **What a different answer would change:** `AC-D51.4`'s per-symbol state assertions become fresh-follow assertions (or the named scope).
- **Affected requirement section:** D51.4 / `AC-D51.4` (provisional); Journey 44.

## Q76 — D51.5: on a full-series replacement, does the viewport behave differently for the same symbol vs a new symbol?

- **Status:** **answered-owner-confirmed 2026-10-29 (option (a)).**
- **Answer (owner, 2026-10-29):** **(a)** — same-symbol full-series replacement preserves viewport + follow state; new symbol starts following.
- **Why it's blocking:** `AC-D51.5` covers two cases whose rules may differ — same-symbol reload/backfill vs new-symbol load — and each needs its own stated expectation.
- **Question:** (a) same-symbol replacement preserves viewport + follow state while a new-symbol load starts following the live edge, or (b) both preserve, or (c) both reset to follow, or (d) an owner-named split?
- **Recommended default:** (a) same-symbol preserves, new-symbol follows. Rationale: a backfill/reload must not move the user; a new symbol has no prior viewport worth keeping.
- **What a different answer would change:** `AC-D51.5`'s same-vs-new assertions (preservation vs follow per case).
- **Affected requirement section:** D51.5 / `AC-D51.5` (provisional); Journey 44.

---

# Open Questions — 2026-10-29 (Batch 27 / D52 — `30 mins` interval; Q77 NON-BLOCKING, default recorded)

> New batch D52: add `30 mins` as a valid chart interval alongside the existing intraday set, following the D48 precedent. The single owner-choice input (the exact duration window) is recorded below as **Q77 answered-owner-confirmed as `30 D` (A136 owner decision)** — lite lane: the default is specified in `AC-D52.1` and verified by the `AC-D52.7` probe, so **no blocking question remains** and `requirements.md` carries `Status: READY_FOR_PLAN`. The owner overrode the `10 D` analyst default pre-Plan with `30 D`; the override changed only `AC-D52.1` / A136 and the probe combo. **D1–D51 are NOT reopened.**

## Q77 — D52.1: is the `30 mins` fetch duration `10 D`, or do you want a different window?

- **Status:** **answered-owner-confirmed 2026-10-29.** The owner overrode the `10 D` analyst default: duration is `30 D`. `AC-D52.1` specifies `30 D` and `AC-D52.7` verifies it against IBKR. Not blocking.
- **Why it could matter:** the window sets how much history one `30 mins` request covers (`10 D` ≈ 7 trading sessions — still short of the `AC-D16.8` floor, which the successive-loads mechanism then extends). A shorter window (`5 D`, matching `15 mins`) means more chained requests to reach the floor; a longer single window is bounded by IBKR's per-request acceptance (the probe decides).
- **Question:** keep the analyst default `duration='10 D'` for `30 mins`, or name a different window (e.g. `5 D` to match `15 mins`, or a longer span if the probe allows)?
- **Recommended default (analyst, OVERRIDDEN by owner 2026-10-29):** `10 D` was the analyst default (upper-neighbour duration: `15 mins` → `5 D`, `1 hour` → `10 D`). Rationale was fewer chained requests toward the 30-session floor than `5 D`, inside IBKR's accepted vocabulary for 30-minute bars pending probe confirmation.
- **Answer (owner-confirmed 2026-10-29):** `30 D` — the `30 mins` row uses duration `30 D`. `AC-D52.1`, A136 and the `AC-D52.7` probe combo read `30 mins` / `30 D`.
- **What a different answer would change:** `AC-D52.1`'s duration, A136, and the `AC-D52.7` probe combo only — planner stepping, the floor, and aggregation are unchanged.
- **Affected requirement section:** D52.1 / `AC-D52.1`; A136; Journey 45.

---

# Open Questions — 2026-11-03 (Batch 28 / D53 — persistent backfill indicator; Q78-Q80 NON-BLOCKING)

> Finding 2 of `NDThinkChart_TWS_probe_findings_20261103.txt` + owner directive "fix everything approved". The scope is fully derivable from the probe evidence (D53.1-D53.4 final; A142-A144 defaults logged; Journey 46; `AC-D53.1`-`AC-D53.4`). The three items below are **non-blocking confirmations** — build proceeds on the stated defaults whether or not they are answered; an answer refines D53 in place. **No blocking question remains** and D53 carries `Status: READY_FOR_PLAN`. Finding 1 needs NO code change (watchdog/shortfall behaved correctly) — watchdog tuning and TWS-side causes are out of scope and are not asked here. **D1-D52 are NOT reopened.**

## Q78 — D53.1: where should the persistent indicator live?

- **Status:** open (non-blocking).
- **Question:** should the persistent backfill indicator live as (a) a permanent status-bar widget (recommended default — closest to the overwritten message it replaces), (b) a toolbar/badge affordance, or (c) an owner-named surface?
- **Recommended default (A142):** (a) — a dedicated, non-transient status-bar element; Plan picks the exact widget. Rationale: it replaces the transient message in the user's existing glance path and no new dock/panel is introduced for a minimal batch.
- **What a different answer would change:** D53.1's surface clause and the `AC-D53.1` widget-identity assertion only — persistence content, lifecycle and guard are untouched.
- **Why it is not blocking:** `AC-D53.1` asserts the persistence property and minimum content set, both derivable without a placement pick.
- **Affected requirement section:** D53.1 / `AC-D53.1`; A142; Journey 46.

## Q79 — D53.1: is the minimum content set (in-flight count, queue count, elapsed, reqIds) the right set?

- **Status:** open (non-blocking).
- **Question:** is the probe-named set (active request count, queue count, elapsed time, current reqIds) sufficient as the at-least set, or should fields be added (e.g. per-request bar counts, current symbol/timeframe/mode) or removed?
- **Recommended default:** the probe-named set as the at-least set (A142/R106). Rationale: those are exactly the fields the probe observer had to reconstruct by hand at +60 s (queue=0, in-flight={2,5}, generation=1, 0 bars) — they are the minimum that would have made the stall legible.
- **What a different answer would change:** `AC-D53.1`'s content assertions gain/lose fields; nothing else moves.
- **Why it is not blocking:** the at-least set is evidence-backed; a refinement only widens or narrows it.
- **Affected requirement section:** D53.1 / `AC-D53.1`; A142; R106.

## Q80 — D53.3: is gating the "Cache current" claim class (with existing status-bar phrasing for the replacement) acceptable?

- **Status:** open (non-blocking).
- **Question:** confirm that (a) the guard covers "Cache current" plus any equivalent freshness claim (not one literal string), and (b) the replacement copy follows existing status-bar phrasing as a Plan detail rather than a user-confirmed string.
- **Recommended default (A144):** yes to both. Rationale: the probe never observed the literal string, so pinning one string would under-guard; copy without a confirmed reference is a Plan detail per the `AC-G.1` pattern.
- **What a different answer would change:** `AC-D53.3`'s claim wording (literal-string vs claim-class) and whether copy needs a confirmed reference.
- **Why it is not blocking:** either reading keeps the guard testable (absence-of-claim + shortfall-presence assertions).
- **Affected requirement section:** D53.3 / `AC-D53.3`; A144.

# Open Questions — P15 (Batch 29 / D54 — 10-second target on load chart; Q81–Q83 NON-BLOCKING — defaults carried per A148)

> Owner directive (verbatim 2026-11-04): *"max waiting can be 10 seconds once user clicks load chart."* Owner clarification 2026-11-04 (verbatim): *"i would ideally like to have the chart load in 10 seconds or less.."* — analyst default **A148** (`requirements.md` Phase P15): "ideally" reads as a performance **TARGET**, not a hard cap (optimize the common path to ≤10 s; Q81–Q83 expiry semantics apply only when the target is missed — graceful degradation). The 600 s figure is the probe harness's self-terminate ceiling, not app behaviour; the app's own wave watchdog is 120 s today. Standalone probes show legitimate single-request TWS latencies of 25–76 s for deep history (35D/45D/60D windows). **D1–P14 are NOT reopened.** Finding 1 / TWS-side silence causes are out of scope. Q81–Q83 are **non-blocking confirmations** — build proceeds on the stated defaults; P15 carries `Status: READY_FOR_PLAN`.

## Q81 — D54: what renders when the 10 s target is missed?

- **Status:** open (non-blocking).
- **Question:** at T0+10 s (T0 = Load Chart click / `load_chart` invocation) with the wave still incomplete, what must the user see — (a) whatever bars have arrived so far rendered on the chart plus the `AC-D16.4` shortfall marker for the missing remainder (recommended default — the chart is never blank when data exists, consistent with the no-silent-hole rule), (b) the pre-load / skeleton view held with only the shortfall + retry affordance (no partial bars), or (c) an owner-named variant (e.g. cached-bars-only render even when fresher partials exist)?
- **Recommended default (A148):** (a) — partial bars + shortfall. Rationale: never blank when data exists; consistent with `AC-D16.4` no-silent-hole.
- **What a different answer would change:** `AC-D54.1`'s render assertion (partial-bars-present vs skeleton-held) only — target, lifecycle and guard are untouched.
- **Why it is not blocking:** the target-miss path is graceful degradation; `AC-D54.1` asserts the at-least default (a) testably without the owner's explicit pick.
- **Affected requirement section:** Phase P15 / D54.1–D54.2 / `AC-D54.1`–`AC-D54.2`; Journey 47; R108.

## Q82 — D54: does the wave keep filling in the background after the 10 s target is missed?

- **Status:** open (non-blocking).
- **Question:** after the 10 s miss renders per Q81, does the in-flight wave (a) continue in the background with the D53 persistent indicator still running and the chart updating as further bars land (recommended default — no user data is discarded, D53 lifecycle unchanged, completion/shortfall finalizes normally), or (b) cancel at 10 s so the user must explicitly retry/extend (indicator finalizes as cancelled per `AC-D53.2`)?
- **Recommended default (A148):** (a) — background-continue. Rationale: no fetched data discarded; D53 lifecycle unchanged; no new 10 s cancel path invented.
- **What a different answer would change:** `AC-D54.2`'s wave-state assertion past T0+10 s (continue vs cancel) only.
- **Why it is not blocking:** either reading keeps the verdict testable (wave-state + indicator-state assertions); the default preserves the existing D53 lifecycle.
- **Affected requirement section:** Phase P15 / D54.2 / `AC-D54.2`; D53 `AC-D53.2` interaction; Journey 47.

## Q83 — D54: how is shortfall vs completion surfaced at/after a 10 s miss (on the D53 surface)?

- **Status:** open (non-blocking).
- **Question:** confirm that (a) the 10 s miss state is surfaced on the existing D53 persistent backfill-state indicator (no new surface — D53 is referenced, not redesigned), showing an explicit "partial @ 10 s" vs "complete" distinction, and (b) any still-missing spans at/after the miss keep the `AC-D16.4` shortfall (missing-days + reason) visible rather than any current-cache claim per `AC-D53.3` — or name the owner-preferred wording/surface if different.
- **Recommended default (A148):** yes to both — D53 indicator + `AC-D16.4` shortfall. Rationale: reuses the shipped surface; preserves honesty without a copy redesign.
- **What a different answer would change:** `AC-D54.3`'s surface/wording assertions only — D53 stays referenced, not reopened.
- **Why it is not blocking:** either reading keeps the guard testable (absence-of-claim + shortfall-presence assertions); the default avoids a D53 redesign.
- **Affected requirement section:** Phase P15 / D54.3 / `AC-D54.3`; D53 / `AC-D53.1`–`AC-D53.3` (referenced, not reworded); Journey 47; DG101.

---

# Open Questions — P16 (Batch 30 / D55 — documentation consolidation; all answered 2026-11-04 — no blocking item remains)

> FULL `docs/documentation_consolidation_plan.md` execution, docs-only. No product-code behaviour change: any step implying app behaviour is a question/escalation, never a silent decision. **D1–P15 are NOT reopened.** All four blocking questions answered 2026-11-04 — no blocking item remains; Phase P16 carries `Status: READY_FOR_PLAN`. (Inventory/reference-map work per `AC-D55.1` deletes nothing; the Q84 comment reword runs as a tracked micro-task pipeline change.)

## Q84 — D55: what should `services/sound_service.py:3` cite once `dev_docs/delta.md` §3 is dispositioned?

- **Status:** **answered 2026-11-04** — resolved; no longer blocking.
- **Answer (owner, 2026-11-04, verbatim direction):** *"Delete + reword the comment — one comment-only line in sound_service.py, e.g. 'numpy synthesis of the Web Audio alarm chime', no behavior change."* A shorter variant of option (a), NOT the full recipe inline. Pipeline condition: the edit runs as a tracked micro-task pipeline change, never a hand-edit.
- **Question:** the module docstring's design reference (`services/sound_service.py:3` cites `dev_docs/delta.md` §3 for the Web Audio alarm-chime recipe) dangles if `dev_docs/` is deleted or archived: should the reference become (a) the recipe inlined into the module docstring (self-contained, no doc dependency), (b) a pointer to a migrated note (e.g. `docs/archive/dev_docs/delta.md` §3 or its successor), (c) a citation to the current architecture/services note covering alert tones, or (d) an owner-named target?
- **Recommended default:** (a) inline the recipe into the module docstring. Rationale: a code comment depending on a deleted dev doc is the exact orphan the owner forbade leaving dangling; inlining removes the cross-tree dependency entirely, survives any `dev_docs/` disposition, and changes no behaviour.
- **What a different answer would change:** only the citation target of one comment (and whether a migration note must exist at that target) — `AC-D55.8`'s `dev_docs/` disposition follows Q86 regardless.
- **Why it was blocking (resolved 2026-11-04):** `dev_docs/` deletion was owner-approved in principle, but executing it with a live code comment pointing into the deleted tree would have violated the owner's explicit no-dangling-reference condition; the target had to be decided before the disposition.
- **Affected requirement section:** Phase P16 / D55.8 / `AC-D55.8`; `services/sound_service.py:3` (comment only — no code change); A149.

## Q85 — D55: live-only vs paper-on-7496 — which account truth do the guides get corrected to?

- **Status:** **answered 2026-11-04** — resolved; no longer blocking.
- **Answer (owner, 2026-11-04, verbatim):** *"we only work with live account. do not send any orders"* — **live-only is the truth** (aligns with the standing zero-order-interaction constraint, D45/D46). `usage.md`'s paper-on-7496 sentences are wrong and fall under `AC-D55.4` correction scope; guides are unfrozen on this point ONLY for the live-only fix.
- **Question:** the corpus contradicts itself on product behaviour: the stack/index lineage says **live TWS port 7496 only — no paper mode**, while `usage.md` (current canonical guide) says a **paper (DU) TWS login on that same port works** (connection badge shows amber `Paper`). Should the corrected guides state (a) live-only (paper unsupported — `usage.md`'s paper sentences are corrected away), (b) port-guard-only (paper on 7496 is supported — the stack/index "no paper mode" wording is corrected), or (c) an owner-named rule (e.g. live-only for trading surfaces, paper tolerated for charting)?
- **Recommended default:** none — no default is safe. Rationale: this is product behaviour, not prose; either correction rewrites a user-visible claim about what the app accepts, and the consolidation batch is explicitly forbidden from deciding product behaviour by silence.
- **What a different answer would change:** `AC-D55.2`'s connection fact row and `AC-D55.4`'s entire port/account correction (plus any stack/index wording on the losing side).
- **Why it was blocking (resolved 2026-11-04):** `AC-D55.4` could not correct the guides until the truth was pinned; correcting toward either side on a guess risked shipping a guide that misstates what the app accepts (R110).
- **Affected requirement section:** Phase P16 / D55.2 + D55.4 / `AC-D55.2`–`AC-D55.4`; Journey 50; R110.

## Q86 — D55: after Q84 is resolved, is `dev_docs/` deleted outright or archived with a pointer?

- **Status:** **answered 2026-11-04** — resolved; no longer blocking.
- **Answer (owner, 2026-11-04):** **(a)** — delete `dev_docs/` outright post-reference-check. Reference check on record: the only live reference is `services/sound_service.py:3`, resolved by the Q84 answer above; the five historical mentions stay as true history.
- **Question:** the owner approved `dev_docs/` deletion (5-file initial design set) subject to the sound-service reference being resolved (Q84): once Q84 lands, should the directory be (a) deleted outright (references checked, unique content migrated or intentionally retired per the disposition ledger), or (b) moved to `docs/archive/` with a HISTORICAL banner + canonical links (deletion deferred)?
- **Recommended default:** (b) archive-with-pointer first, delete only on a later explicit instruction. Rationale: the plan's own matrix counsels against deleting the initial design set first ("deletion is not recommended until unique context and references are checked; mark legacy first"); archiving preserves decision lineage while satisfying "do not use as current guidance".
- **What a different answer would change:** only the end state of one directory (and the ledger entry) — content treatment and reference checks are identical either way.
- **Why it was blocking (resolved 2026-11-04):** both options satisfied the plan only with the owner's explicit pick: outright deletion destroys the original scope/design history on an inference, while archiving retains a directory the owner had already approved deleting — either direction without the owner risked violating an explicit instruction.
- **Affected requirement section:** Phase P16 / D55.7–D55.8 / `AC-D55.7`–`AC-D55.8`; disposition matrix; R111.

## Q87 — D55: legacy unsuffixed logs + generated precheck output — delete or archive?

- **Status:** **answered 2026-11-04** — resolved; no longer blocking.
- **Answer (owner, 2026-11-04, verbatim):** *"delete"* — delete the legacy unsuffixed logs + generated precheck output, no archive.
- **Question:** the plan names the three untracked root review reports (`DEAD_CODE_REVIEW.txt`, `TEST_SUITE_RUNTIME_REPORT.txt`, `DRAWING_RENDER_DEBUG_REPORT.txt`) and generated precheck/cache text as deletion candidates (durable findings integrated or owner no longer needs the snapshots → delete; otherwise archive with date/evidence basis; generated text follows build/ignore policy and must never remove user data). Should each be (a) deleted (durable content confirmed integrated / snapshots no longer needed), or (b) archived under `docs/archive/reviews/` (or the plan's equivalent) with date + evidence basis?
- **Recommended default:** (b) archive-with-date first. Rationale: these are untracked snapshots the plan explicitly warns not to silently overwrite or treat as canonical — archiving preserves whatever durable evidence was never integrated, at near-zero cost; deletion is irreversible without a git object.
- **What a different answer would change:** only the end state of the named files (and their ledger entries) — the audit (durable-findings-integrated? owner-needs-snapshot?) runs identically either way.
- **Why it was blocking (resolved 2026-11-04):** deletion destroys evidence the owner may still want; archiving retains files the owner had already classed as candidates for removal — the owner picked per file or as a set.
- **Affected requirement section:** Phase P16 / D55.7–D55.8 / `AC-D55.7`–`AC-D55.8`; disposition matrix §6–§7; R111.

---

# Open Questions — P17 (Batch 31 / D56 — silence retry for historical chunks; Q88–Q91 BLOCKING)

> Owner-directed batch (verbatim brief): *"Silence retry"* over TWS-log join, smaller chunks, and accept-as-environment. The retry shape is settled (cancel the silent reqId + re-issue the same chunk exactly once inside the 120 s watchdog; second silence falls through to watchdog strand-finalization). All four blocking questions (Q88–Q91) were **answered by the owner on 2026-11-05** — `AC-D56.1`–`AC-D56.7` are FINAL and Phase P17 carries `Status: READY_FOR_PLAN`. **D1–P16 are NOT reopened.**

## Q88 — D56.1/D56.2: what is the silence bound N (seconds of zero-bar silence before cancel + re-issue)?

- **Status:** **answered 2026-11-05 — owner chose 30 s (aggressive; NOT the analyst-recommended 45 s).**
- **Answer (owner, 2026-11-05, verbatim):** *"30 s."* The false-retry tradeoff is accepted: legitimate 25–76 s single-request TWS latencies mean the 30 s bound will sometimes fire on merely-slow (not dead) responses, spending a pacing slot on the re-issue; the owner accepts that cost for faster recovery.
- **Question:** for an issued chunk with zero bars, no END, and no error, how many seconds of silence trigger the cancel + re-issue — (a) **45 s** (recommended default), (b) 30 s (aggressive), or (c) 60 s (conservative), or (d) an owner-named N?
- **Recommended default (a):** 45 s. Rationale: primes answer instantly and silence has been observed past 60 s, so 45 s fires on genuine silence without chasing normal variance; 45 s + a 45 s re-issue window + cancel/finalize margin still concludes inside the 120 s watchdog (Plan states the exact arithmetic per DG106).
- **What a different answer would change:** `AC-D56.1`/`AC-D56.2` timing assertions, the A157 fit-inside arithmetic, and R114's margin analysis — nothing else moves.
- **Why it is blocking:** N is the trigger predicate of the only two timing ACs; any value written without the owner is a guessed user-visible timing constant.
- **Affected requirement section:** Phase P17 / D56.1–D56.2 / `AC-D56.1`–`AC-D56.2`; A157; R114; DG106.

## Q89 — D56.1/D56.5: is the exactly-once retry budget per chunk or per wave?

- **Status:** **answered 2026-11-05 — owner chose (a) per-chunk.**
- **Answer (owner, 2026-11-05, verbatim):** *"(a) per-chunk."* Each silent chunk gets its own cancel + re-issue; no wave-level retry counter.
- **Question:** when several chunks of one wave go silent (4 silent reqIds across 2 waves on record), does (a) **each silent chunk get its own cancel + re-issue** (recommended default — "the same chunk exactly once" applied per chunk), or (b) **the wave get a single retry budget** (first silent chunk consumes it; later silent chunks go straight to watchdog finalization), or (c) an owner-named budget?
- **Recommended default (a):** per-chunk. Rationale: matches the brief's "re-issue the same chunk exactly once" and the evidence (multiple silent reqIds per wave would otherwise leave most of the wave unretried); pacing-gated per `AC-D56.5` so a silent wave cannot spend unboundedly.
- **What a different answer would change:** `AC-D56.1`/`AC-D56.5` counting assertions (per-chunk issue caps vs a wave-level retry counter) and R117's starvation analysis.
- **Why it is blocking:** the two readings assert opposite issue counts on the recorded 4-silent-reqId shape — the AC cannot be written without the pick.
- **Affected requirement section:** Phase P17 / D56.1 + D56.5 / `AC-D56.1` + `AC-D56.5`; R117.

## Q90 — D56.6: what must the D53 indicator show during a retry?

- **Status:** **answered 2026-11-05 — owner chose (a) explicit retry state, elapsed continuing.**
- **Answer (owner, 2026-11-05, verbatim):** *"(a) explicit, distinguishable retry state, elapsed continuing from wave baseline."* Exact widget/copy/layout remain Plan details per the DG100 pattern.
- **Question:** during a retry, must the D53 persistent indicator show (a) **an explicit, distinguishable retry state** (recommended default — e.g. retry identity such as chunk/attempt markers, with elapsed continuing from the wave baseline), or (b) **a silent continuation** (in-flight counts keep running with no retry marking)?
- **Recommended default (a):** explicit retry state with continuing elapsed. Rationale: Finding 2 was won on honesty — a retry that reads as first-issue flight hides the stall history, and one that reads as completion is worse; elapsed must continue (not reset) so the watchdog horizon stays legible. Exact widget/copy/layout remain Plan details per the DG100 pattern.
- **What a different answer would change:** `AC-D56.6`'s distinguishability assertion only — lifecycle, guard, and surface are untouched either way.
- **Why it is blocking:** the owner ordered the D53 honesty surface; whether a retry is explicitly visible on it is a user-visible outcome decision, not a derivable default — though the mechanism stays Plan-level.
- **Affected requirement section:** Phase P17 / D56.6 / `AC-D56.6`; A159; R118; DG100 (pattern).

## Q91 — D56 scope: zero-bar silence only, or also partial-then-stalled chunks?

- **Status:** **answered 2026-11-05 — owner EXPANDED scope: partial-then-stalled chunks included.**
- **Answer (owner, 2026-11-05, verbatim):** *"include partial-then-stalled chunks."* The trigger is two rules: the zero-bar rule stays the primary trigger, plus a trailing-silence rule for partials (no bars AND no END/error for a trailing 30 s window after the last received bar). Progress baseline is minimal and deterministic (see A156 override): per-reqId last-activity stamp derived from existing wave events only — registration/issue starts the clock, each accepted `on_historical_bar` re-stamps it (grounded in the repo's per-reqId bar counting, `TickerSession._req_bars[req_id]` + `on_historical_bar`); no new semantic tracking is invented.
- **Question:** does the retry trigger cover (a) **zero-bar silence only** (recommended default — zero bars + no END + no error for N s; a chunk that delivered some bars then stalled keeps the watchdog path), or (b) **also partial-then-stalled chunks** (bars arrived, then nothing for N s)?
- **Recommended default (a):** zero-bar only. Rationale: the evidence covers chunks silent from issue (server-side receipt proven by cancel-ack 162s, zero bars); a partial-stall predicate needs a per-chunk progress baseline the requirements have not defined, and widening it here would fork the trigger semantics.
- **What a different answer would change:** `AC-D56.1`'s trigger predicate (zero-bar vs progress-stall) and Journey 51's partial-stall edge case (which would graduate into a covered path with its own exactly-once accounting).
- **Why it is blocking:** the trigger predicate is the scope boundary of the whole batch — the AC cannot be written without it.
- **Affected requirement section:** Phase P17 / D56 scope / `AC-D56.1`; Journey 51 edge cases; A156.

# Open Questions — P18 (Batch 32 / D57 — viewport-UX: chevron + framing; Q92–Q95 BLOCKING)

> Owner-directed batch (two verbatim items, one batch): **(1)** go-to-latest chevron, TradingView behavior (screenshot reference: bottom-right of price axis) — visible ONLY when scrolled into past bars, hidden while following, click re-engages follow + jumps to latest; **(2)** new-ticker framing — fresh load re-centers x/y so data is visible (1 min → last 2 sessions, 5 min → last 1 week, higher intervals per TradingView defaults). **Reconciliation verified 2026-11-05:** `AC-D51.3` already required the affordance and P11 built the headless rule set only (`chart.js::goToRealtime/affordanceVisible`, no button DOM in `chart.html`) — the visible chevron is carried forward unbuilt, not new scope. All four questions below were **answered by the owner on 2026-11-05** — `AC-D57.1`/`AC-D57.2`/`AC-D57.4`/`AC-D57.5` are FINAL and Phase P18 carries `Status: READY_FOR_PLAN`. **D1–P17 are NOT reopened.**

## Q92 — D57.1: does the chevron show whenever away, or only when away AND new bars arrived?

- **Status:** **answered 2026-11-05 — owner chose (a) whenever away.**
- **Answer (owner, 2026-11-05, verbatim):** *"whenever away (your words + TradingView)."*
- **Question:** while the viewport is scrolled into past bars, is the chevron visible (a) **whenever away** (TradingView-exact per the owner statement — visible ONLY when away, hidden while following — regardless of whether new bars have arrived since), or (b) **only when away AND new bars arrived** (keep P11's `affordanceVisible` badge rule), or (c) an owner-named third rule?
- **Recommended default (a):** visible whenever away. Rationale: matches the owner statement verbatim and TradingView behavior; a badge-gated chevron leaves an away user with no visible way back until the next tick lands.
- **What a different answer would change:** `AC-D57.1`'s visibility matrix (away-alone cell shown vs hidden) and whether `affordanceVisible` is superseded or confirmed.
- **Why it is blocking:** the two readings assert opposite visibility in the away-with-no-new-bars cell — the AC cannot be written without the pick.
- **Affected requirement section:** Phase P18 / D57.1 / `AC-D57.1` (provisional); Journey 52; A162; R119; DG109.

## Q93 — D57.1: what does clicking the chevron do — scroll-to-edge preserving span, or full Fit?

- **Status:** **answered 2026-11-05 — owner chose (a) scroll-to-edge.**
- **Answer (owner, 2026-11-05, verbatim):** *"scroll to live edge preserving zoom — option (a), existing goToRealtime path."*
- **Question:** on chevron click, does the chart (a) **scroll to the live edge preserving the current span** (the existing `goToRealtime` path — TradingView behavior, "jumps to the latest bar"), or (b) **run a full Fit** (frame all loaded bars, the `fitAndFollow` path), or (c) an owner-named action?
- **Recommended default (a):** scroll-to-edge preserving span + follow re-engaged. Rationale: the owner said "jumps to the latest bar" (not "reframes everything"); preserves the user's zoom; reuses the built path with no new viewport math.
- **What a different answer would change:** `AC-D57.2`'s post-click range assertion (same span shifted to the edge vs full-series frame) only — follow re-engagement and chevron-hides hold either way.
- **Why it is blocking:** the two readings assert different post-click viewports — opposite test expectations on the same click.
- **Affected requirement section:** Phase P18 / D57.1 / `AC-D57.2` (provisional); Journey 52.

## Q94 — D57.2: what are the initial x-spans for the seven unspecified timeframes?

- **Status:** **answered 2026-11-05 — owner chose (a) accept the analyst table.**
- **Answer (owner, 2026-11-05, verbatim):** *"accept the analyst's table (15m→2w, 30m→1M, 1h→2M, 4h→6M, 1d→1Y, 1w→1Y, 1M→5Y) — option (a)."*
- **Question:** 1 min (last 2 sessions) and 5 min (last 1 week) are owner-decided. For `15 mins` / `30 mins` / `1 hour` / `4 hours` / `1 day` / `1 week` / `1 month`, (a) **accept the A164 analyst table** (`15m` → 2 weeks; `30m` → 1 month; `1h` → 2 months; `4h` → 6 months; `1d` → 1 year; `1w` → 1 year; `1M` → 5 years), or (b) **name owner spans per timeframe** (TradingView defaults as you read them), or (c) **a timeframe-agnostic rule** (e.g. always frame the newest N bars — owner names N)?
- **Recommended default (a):** the A164 table. Rationale: session-anchored like the two decided spans; keeps `AC-D57.4` testable per timeframe; any cell is correctable without moving the requirement shape.
- **What a different answer would change:** `AC-D57.4`'s per-timeframe range assertions (and A164) only — memory precedence, y-framing, and the data path are untouched.
- **Why it is blocking:** the initial window is the whole of D57.2's user-visible outcome; any span written without the owner is a guessed number on every timeframe.
- **Affected requirement section:** Phase P18 / D57.2 / `AC-D57.4` (provisional); Journey 53; A164; R120; DG110.

## Q95 — D57.2: on a switch to a previously-seen symbol, does memory or fresh framing win?

- **Status:** **answered 2026-11-05 — owner chose (b) fresh framing, OVERRIDING the recommended (a).**
- **Answer (owner, 2026-11-05, verbatim):** *"fresh framing every time — option (b)."* Scope per instruction: both symbol switches AND timeframe changes on the same symbol re-frame fresh. Lineage: Q75/`AC-D51.4` stand for **follow-state memory**; only the viewport-**range** restore is superseded (`AC-D57.5`, A165).
- **Question:** when the target symbol already has Q75 per-symbol memory (remembered viewport + follow state), does the load (a) **restore the memory** (Q75 stands unchanged; fresh framing applies only where no memory exists for the pair), or (b) **apply fresh framing anyway** (framing wins on every new-ticker load; memory kept for follow-state only, or dropped — owner says which), or (c) an owner-named split (e.g. memory wins within-session, framing wins across restarts)? Follow-up within the same answer: does a **timeframe change on the same symbol** take fresh framing or preserve the viewport?
- **Recommended default (a):** memory wins. Rationale: Q75 was a deliberate TradingView improvement for the multi-symbol alarm workflow; framing-wins would re-introduce a viewport yank on every switch-back that D51 removed.
- **What a different answer would change:** `AC-D57.5`'s switch-back assertions (restored-range vs fresh-frame) and whether `AC-D51.4` needs a recorded supersession note.
- **Why it is blocking:** the two readings assert opposite viewports on the same switch-back — and one of them rewrites a FINALISED D51 criterion, which cannot happen without an explicit owner decision.
- **Affected requirement section:** Phase P18 / D57.2 / `AC-D57.5` (provisional); Journey 53; A165; R121; `AC-D51.4` (stands unless the answer changes it).

# Open Questions — P19 (Batch 33 / D58 — scroll-triggered prefetch; analyst-decided per delegation — no blocking item)

> Owner-directed (verbatim 2026-11-05): *"also current when vieweing in 1min 30 sessions are populated. the chart should backfilling more if user scrolls to past i.e. user should not see blanks in place of price bars. that means for each interval, decide a position in past when you will start downloading more historical bars. decide and update to me."* The owner explicitly delegated the per-interval trigger positions ("decide and update to me") — so no question round was opened. The trigger table (one `AC-D57.4` frame span of lookahead per timeframe) and the wave-bounds decisions are logged as A166–A170; Phase P19 carries `Status: READY_FOR_PLAN`; this reply is the report-back. Owner corrections to any threshold cell land as in-place refinements without reopening. **D1–P18 are NOT reopened.** No blocking question remains.

# Open Questions — P20 (Batch 34 / D59 — index + futures contract support; Q96–Q99 BLOCKING)

> Owner-corrected scope (binding, 2026-11-09); Q96–Q99 ANSWERED 2026-11-09 — Phase P20 FINAL (`Status: READY_FOR_PLAN`). Original scope note retained below: *"SPX is S&P500 index ticker ID. why confuse it with ES futures"*. Recorded rule: **SPX (and the NDX/DJI/RUT index family) charts its OWN index data via IND-type contracts. The D36 INDEX_PROXY (SPX→ES etc.) applies ONLY to tape-dependent features (footprint/burst) and must NEVER substitute futures data for an index price series.** Observed failures: (1) SPX load builds STK/SMART (`get_contract_for_symbol` falls through), TWS answers error 200 on prime + wave + realtime, 300 s on the dead realtime reqIds, honest full-span shortfall — fix = correct IND resolution + graceful unknown-symbol handling; (2) ES loads with correct price but wrong-rendered timestamps — suspected session/timezone mapping (near-24 h futures sessions vs equity RTH calendar in `market_calendar`/`session_windows`) — diagnose from the code, do not guess. Out of scope: TWS-side silence, P19 prefetch, D1–P18 reopen. Phase P20 carries `Status: READY_FOR_PLAN` (Q96–Q99 answered 2026-11-09). **D1–P19 are NOT reopened.**

## Q96 — D59.1: which index family members are in scope for IND charting?

- **Status:** **answered 2026-11-09 — owner chose (b) SPX+NDX+DJI+RUT (recommended; NDX earlier-confirmed).**
- **Answer (owner, 2026-11-09):** SPX + NDX + DJI + RUT.
- **Question:** SPX is confirmed. Which other cash-index symbols must resolve to IND contracts and chart their own index data in this batch: (a) **SPX only**, or (b) **SPX + NDX + DJI + RUT** (the owner-named family), or (c) an owner-named list (e.g. plus VIX/SPXW/OEX — owner names each; note SPXW weekly options and VIX methodology differ from a plain price series)?
- **Recommended default (b):** SPX + NDX + DJI + RUT. Rationale: matches the owner-named family; one IND rule covers all four; SPY/QQQ/DIA/IWM are ETFs (STK) and stay out regardless.
- **What a different answer would change:** `AC-D59.1`'s symbol matrix (one row vs four rows vs custom list) and the unknown-symbol tests only — resolution mechanism and proxy-guard are untouched.
- **Why it is blocking:** the acceptance matrix cannot be written without the symbol list; any list written without the owner is a guessed universe.
- **Affected requirement section:** Phase P20 / D59.1 / `AC-D59.1` (provisional); Journey 55; A171; R125.

## Q97 — D59.2: which futures roots are in scope, and what are the contract defaults (exchange / currency / expiry rule)?

- **Status:** **answered 2026-11-09 — owner chose recommended: ES+NQ+YM+RTY, CME/USD, existing front-month auto-roll; rollover per existing `_front_month`.**
- **Answer (owner, 2026-11-09):** ES + NQ + YM + RTY on CME/USD with existing front-month auto-roll; rollover gap/overlap per existing `_front_month` behaviour.
- **Question:** (1) Which futures roots must load in this batch: (a) **ES only**, or (b) **ES + NQ + YM + RTY** (the equity-index-futures set matching Q96), or (c) an owner-named list? (2) For each in-scope root, confirm the TWS contract defaults: exchange (e.g. ES→CME — owner confirms vs analyst default), currency (e.g. USD), and expiry rule (e.g. **front-month auto-roll via `_front_month`** vs owner-pinned month vs continuous)? What should a load do at/after expiry-roll (roll to the new front month, and is a one-bar gap/overlap at roll acceptable)?
- **Recommended default:** (1)(b) ES + NQ + YM + RTY; (2) exchange CME, currency USD, front-month auto-roll (existing `_front_month` precedent per graph `ibkr/contracts.py::get_futures_contract` / `_front_month`). Rationale: reuses the repo's stated futures path; roll behaviour is the only honest default without a continuous-series requirement.
- **What a different answer would change:** `AC-D59.3`'s root matrix + contract-field assertions and the rollover edge case only — timestamp fix and proxy-guard are untouched.
- **Why it is blocking:** exchange/currency/expiry are TWS-rejected-or-accepted fields; any value written without the owner is an invented contract that TWS can refuse (the SPX STK/SMART failure is exactly this class).
- **Affected requirement section:** Phase P20 / D59.2 / `AC-D59.3` (provisional); Journey 56; A172; R126.

## Q98 — D59.3: what is "correct time" for overnight futures sessions?

- **Status:** **answered 2026-11-09 — owner chose recommended (a): render TWS timestamps as-is in ET; equity calendar never deletes overnight bars.**
- **Answer (owner, 2026-11-09):** render TWS timestamps as-is in ET; equity calendar never deletes overnight futures bars.
- **Question:** ES trades a near-24 h session while the equity calendar (`market_calendar` / `session_windows`) models RTH days. For a futures chart, what does correct mean: (a) **render every TWS timestamp as-is in ET** (full overnight session shown; equity RTH shading/bands and the `AC-D16.8`/`AC-D16.9` session-presence rules stay equity-scoped and do not delete overnight futures bars), or (b) **attribute overnight bars to the equity trading date** (e.g. Sunday-evening futures bars render under Monday — owner defines the session-boundary rule), or (c) an owner-named rule (e.g. CME 17:00–16:00 CT day split — owner names the boundary + timezone)?
- **Recommended default (a):** timestamps as-is in ET; no equity-calendar deletion of overnight bars. Rationale: the smallest honest fix (stop mis-mapping); any date-attribution rule is a new session model that must be owner-named.
- **What a different answer would change:** `AC-D59.4`'s timestamp assertions + which calendar/session module owns the futures rule only — contract resolution is untouched.
- **Why it is blocking:** (a) vs (b) assert opposite bar placement for the same overnight span — the AC cannot be written without the pick, and the suspected cause (equity calendar applied to futures sessions) must be confirmed by code diagnosis, not guessed.
- **Affected requirement section:** Phase P20 / D59.3 / `AC-D59.4` (provisional); Journey 56 edge cases; A173; R127.

## Q99 — D59.4: what must an unknown symbol do (matches no STK / IND / FUT rule)?

- **Status:** **answered 2026-11-09 — owner overrode the recommended (a): probe-first via live `reqContractDetails` (option (b)). Lineage + cost recorded.**
- **Answer (owner, 2026-11-09, override):** probe first via live `reqContractDetails` (NOT refuse-in-place). Exactly one probe before refusing; cost: one extra TWS round-trip on unknown symbols only (prime/wave/realtime legs still never fire for unknowns).
- **Question:** when a symbol matches nothing known (not a stock/ETF pattern, not a Q96 index, not a Q97 futures root), must the app (a) **refuse in place with no TWS request** (e.g. status-bar "Unknown symbol — no contract found", nothing persisted, no reqId spent), or (b) **attempt a live `reqContractDetails` probe first** and only refuse if TWS returns nothing, or (c) an owner-named behaviour (owner defines message/persistence/retry)?
- **Recommended default (a):** refuse in place, no request. Rationale: the SPX failure spent prime + wave + realtime reqIds plus 300 s on a contract TWS could never fill (error 200); a known-unknown must not burn pacing/watchdog budget.
- **What a different answer would change:** `AC-D59.2`'s no-request vs probe-first assertion only — IND/FUT resolution rows are untouched.
- **Why it is blocking:** no-request vs probe-first assert opposite wire behaviour (reqId count, pacing spend, error path) — the test cannot be written without the pick.
- **Affected requirement section:** Phase P20 / D59.4 / `AC-D59.2` (provisional); Journeys 55–56 edge cases; A174; R128.

# Open Questions — P21 (Batch 35 / D60 — follow-offset preservation on new-bar arrival; Q100–Q102 ANSWERED 2026-11-09)

> Owner-observed defect (binding, 2026-11-09, screenshots on record): SPY 5 min live — (image 1) last bar floating with empty space to its right while following; (image 2) when the next bar plots, the chart re-positions so the latest bar sits at the right edge. Owner: *"I don't want you to scroll the chart to right edge."* Required behavior (TradingView-like): while following with a right-edge gap, a new bar shifts the viewport by exactly the new-bar width — the gap is preserved, the chart never snaps the latest bar to the edge. Distinct from the no-yank rule (D51/`AC-D51.2`, scrolled-back case) and from P15's 10 s expiry framing — this is the FOLLOWING live path. Related evidence in the same screenshots (ES 5 min overnight session labels — 11/08 23:00, 11/09 05:35/06:15 gaps): the Q98 as-is-ET rendering is live in production; if the offset work touches session-boundary geometry, the interaction is noted but **Q98 is NOT reopened**. Phase P21 carries `Status: READY_FOR_PLAN` (Q100–Q102 answered 2026-11-09). **D1–P20 are NOT reopened.**

## Q100 — D60: do explicit return-to-edge actions still snap the latest bar to the edge, or do they preserve the gap?

- **Status:** **answered 2026-11-09 — owner chose (b) preserve (OVERRIDE of the recommended (a)).**
- **Answer (owner, 2026-11-09):** preserve gap on explicit return-to-edge actions — Fit/reset, chevron click, and right-edge double-click all preserve the current gap. Reasoning implication: "take me to live" means "resume following in place", and the ONLY way to zero the gap is manual scroll/pinch to the edge.
- **Question:** the following-path fix preserves the right-edge gap on new-bar arrival. When the user explicitly returns to the edge — Fit/reset (`fitAndFollow`), the P18 chevron click (`goToRealtime` scroll-to-edge per Q93), or a manual right-edge double-click/Fit gesture — does the chart (a) **snap the latest bar to the right edge** (gap zeroed — the explicit action means "take me to the edge"), or (b) **preserve the existing gap** (shift by the same offset rule, so an explicit action never changes the gap either), or (c) an owner-named split (e.g. Fit zeroes the gap, chevron preserves it)?
- **Recommended default (a):** snap-to-edge on explicit actions. Rationale: an explicit return-to-edge gesture is the user asking for the edge; TradingView's go-to-realtime lands the latest bar at the edge; the gap-preservation rule governs unsolicited live arrivals, not deliberate navigation.
- **What a different answer would change:** `AC-D60.2`'s post-action range assertions (gap-zeroed vs gap-preserved) only — the new-bar-arrival rule (`AC-D60.1`) is untouched.
- **Why it is blocking:** snap vs preserve assert opposite viewports after the same click — the test cannot be written without the pick.
- **Affected requirement section:** Phase P21 / D60 / `AC-D60.2` (FINAL per this answer); Journey 57; A178 (overridden default recorded with lineage).

## Q101 — D60: at session open (or any fresh frame) where the carried gap is huge, is the gap preserved as-is or clamped?

- **Status:** **answered 2026-11-09 — owner chose (c) reset (recommended default CONFIRMED).**
- **Answer (owner, 2026-11-09):** reset to the fresh-frame default at session open — no stale gap is carried across the open.
- **Question:** follow-state memory (Q75/`AC-D51.4`, follow-state component stands per Q95 lineage) can carry a right-edge gap across a session boundary into a fresh frame (`AC-D57.4` initial framing). When the carried gap is huge relative to the fresh frame (e.g. wider than the frame itself, or so large the newest bars would paint outside the visible window), does the chart (a) **preserve the gap as-is** (viewport = frame shifted by the full gap, even if newest bars start off-window), or (b) **clamp the gap to fit** (e.g. cap at N bars / a fraction of the frame — owner names the bound), or (c) **reset the gap to the fresh-frame default** at session open (gap applies only to intraday live arrivals, never carried across the open)?
- **Recommended default (c):** reset at session open / fresh frame. Rationale: the fresh frame (`AC-D57.4`) is defined to show recent action; carrying a stale multi-screen gap into it re-buries exactly what the frame was built to show — while intraday preservation keeps the reported defect fixed.
- **What a different answer would change:** `AC-D60.3`'s session-open assertions (gap value after open) and whether a clamp bound enters the criteria — nothing else moves.
- **Why it is blocking:** preserve vs clamp vs reset assert different first-paint viewports at the open — a user-visible framing decision that cannot be derived from the defect report (which covers only intraday live arrivals).
- **Affected requirement section:** Phase P21 / D60 / `AC-D60.3` (FINAL per this answer); Journey 57 edge cases; A179 (confirmed).

## Q102 — D60: does the preserve-offset rule apply to pop-out views, or main chart only?

- **Status:** **answered 2026-11-09 — owner chose (b) every view (recommended default CONFIRMED).**
- **Answer (owner, 2026-11-09):** every view, each with its own gap — main + each pop-out evaluates its own viewport and preserves its own gap per view.
- **Question:** D51 scoped the follow/away rules to the main-chart viewport only. Does the P21 preserve-offset rule on new-bar arrival apply (a) **main chart only** (pop-outs keep their current snap-to-edge following behaviour), or (b) **every chart view** (main + each pop-out evaluates its own viewport and preserves its own gap per view), or (c) an owner-named scope?
- **Recommended default (b):** every view, per-view gap. Rationale: P19 already evaluates prefetch per view against the shared cache (A170); a scrolled pop-out following with its own gap deserves the same no-snap treatment, and per-view state avoids cross-view interference.
- **What a different answer would change:** `AC-D60.1`'s view matrix (main-only cases vs per-view cases) and whether pop-out viewport cases enter the suite — the offset rule itself is untouched.
- **Why it is blocking:** main-only vs per-view is a scope boundary that changes which views the build touches and which tests are written; it cannot be assumed without the owner (D51's precedent was main-only).
- **Affected requirement section:** Phase P21 / D60 / `AC-D60.1` (FINAL per this answer); Journey 57; A177 (confirmed).
