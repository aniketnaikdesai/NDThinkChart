# NDThinkChart — Requirements

> Status: **D17/D18 (panel layout / resizing in full screen, reported 2026-10-03) — CLARIFIED 2026-10-03 (B1–B4 answered; see `open_questions.md` Q/B1–B4).** D16 (historical-bar hole, reported 2026-10-02) is **clarified and finalised** (Q37–Q39 answered 2026-10-02: backfill the whole gap so the chart is continuous; genuine closures stay empty; all timeframes and any symbol). **ESC-023 correction (2026-10-02):** the D16 trading-day calendar carries an explicit **New Year's year-end accounting exception** — Dec 31 is a **trading day** when Jan 1 of the next year falls on a Saturday (see D16 / `AC-D16.7`). D1–D15 remain built and green. The Existing Repository section (marker sentence + Current Tech Stack) is preserved and must not be dropped. **2026-10-05:** new defect **D19** — the toolbar pinned the central widget, so the D17/D18 fix was not effective in the real app — is **clarified and finalised** (B5–B6 answered 2026-10-05: the toolbar gets a **horizontal scroll / elide wrapper in place**, staying one ~36px row inside the central widget so its minimum width no longer pins the layout; the watchlist cap **stays at 50% of the chart area**). See `open_questions.md` B5–B6 (answered) and D19 / `AC-D19.1`–`AC-D19.7`. **2026-10-06:** new defect **D20** — the D19 wrapper's horizontal scrollbar clipped the toolbar label descenders — is **clarified and finalised** (B7–B8 answered 2026-10-06: the content row stays **~36px** with the horizontal scrollbar in its **own reserved lane below**, total strip **~50–52px**, superseding `AC-D19.4`'s `<= ~40px`; the scrollbar is **as-needed** in its reserved lane). See `open_questions.md` B7–B8 (answered) and D20 / `AC-D20.1`–`AC-D20.6`.

> **2026-10-06 (later) — Batch 15 (D21) CLARIFIED AND FINALISED 2026-10-06 (B9–B13 answered).** After D20 was
> built and green (commit `04397d9`, 585 tests), the user reported **13 UI defects/issues** in one message. They
> are captured as batch **D21** with sub-defects **D21.1–D21.13** (D1–D20 are **not** reopened; D20's `AC-D19.4`
> supersession stands). All five blocking questions (**B9–B13**) were **answered by the user on 2026-10-06**
> (`open_questions.md`), so the D21 criteria are **final** (no *provisional* wording remains). A shared visual
> convention (`VIS-D21`) is defined once for the "hidden/off" diagonal strike-through and the active-button
> highlight (A41/A42 now user-confirmed). D21.4 supersedes only the **display** part of `AC-D16.3`. The batch
> status footer below reflects this and `requirements.md` carries `Status: READY_FOR_PLAN`.

> **2026-10-07 (later) — Batch 16 (D22) CLARIFIED AND FINALISED 2026-10-07 (B14–B16 incl. B15a/B15b/B16b answered).**
> The user asked "how do I add tickers to the watchlist"; repo-validated, there was no in-app way (the watchlist is
> populated at startup from the SQLite `watchlist` table / seeded from `DEFAULT_WATCHLIST` on first run). **D22** is a
> **new feature** (not a defect) and does **not** reopen D1–D21: an in-app **add** and **remove** affordance on the
> watchlist. All blocking questions (**B14–B16**, including the placement/input split **B15a/B15b** and the
> disconnected sub-question **B16b**) were **answered by the user on 2026-10-07** (`open_questions.md`), so D22's
> criteria are **final** (no *provisional* wording remains). **Decisions:** scope **add + remove** (no reorder); a
> **`+` button on the watchlist header strip plus a right-click "Add symbol…"** (and a "Remove symbol" entry); a
> **small modal input dialog**; **live IBKR contract validation** (`reqContractDetails`) before add, rejecting
> unresolved symbols with nothing persisted; and **adding is disallowed while IBKR is disconnected**. A new IBKR
> contract-details request/callback path is required (none exists today). See D22, Journey 27, `AC-D22.1`–`AC-D22.9`,
> A48–A52, R45–R48, and `open_questions.md` B14–B16 (answered). The batch status footer below reflects this and
> `requirements.md` carries `Status: READY_FOR_PLAN`.


> **2026-10-07 (Batch 17, D23) — CLARIFIED AND FINALISED 2026-10-07; no blocking question required.**
> After the **D22** build (712 tests green), Code Review raised **two nice-to-have quality findings**
> (**ESC-030**, **ESC-031**) that the user **approved fixing** and asked to take through the full pipeline.
> They are captured as batch **D23** (sub-defects **D23.1 = ESC-030**, **D23.2 = ESC-031**) and **do not reopen
> D22** (D22 stays built; only the two implementation/task-level defects are corrected). **D23.1** corrects the
> D22 requirement that the cancel call `client.cancelContractDetails`: the pinned `ibapi` (**9.81.1.post1** at D23 report time; the pin is **10.51.1** now, where the capability is still absent — see the Current Tech Stack, and the pin change itself is recorded in `phase-changelog.md` Phase D36 item 38a.0)
> exposes **no** `EClient.cancelContractDetails` (verified in-repo: `hasattr(EClient,'cancelContractDetails') is
> False`), so the required behaviour is a **capability-guarded, documented** cancel with `ContractLookupService`'s
> local invalidation as the real safety net. This **supersedes the task-level `AC-D22.2.3`** wire-cancel mandate
> and **reconciles architecture `S3`**. **D23.2** requires `WatchlistPanel.remove_symbol` to leave **no stale row
> key** (`_row_data` keys exactly `range(rowCount())`) for first/middle/last/only-row removals, with the missing
> coverage added. See D23, Journey 28, `AC-D23.1.*`/`AC-D23.2.*`, A53–A55, R49–R50, and `open_questions.md`
> (Batch 17). No blocking question remains; `requirements.md` carries `Status: READY_FOR_PLAN`.

> **[NEW v1.2] 2026-10-12 — Batches D24–D28 (pop-out charts + deep-dive bug review) — USER-SPECIFIED, built,
> merged, and OWNER-APPROVED 2026-10-14.** The user specified two new features and commissioned a five-track
> adversarial code review (~30k lines, critical claims hand-verified) whose bugs are captured here as corrective
> requirements:
> **D24** — pop-out chart windows (max 10, chrome-free, per-ticker pinned, per-ticker sync of
> bars/studies/zones/lines/alarms, drawing main-chart-only, all real-time);
> **D25** — headless alarm price monitoring (every ticker with a live alarm is price-tracked at 1-minute
> granularity via headless `TickerSession`s, so alarms fire regardless of the main-chart symbol);
> **D26** — corrective batch, P0 real-money safety (9 order-path bugs incl. inverted bracket children,
> unreserved order IDs, phantom stop-loss dialog, crashing MKT buttons);
> **D27** — corrective batch, P1 correctness (10 bugs incl. phantom alarm triggers, four invisible study
> overlays, dead reconnect/replay);
> **D28** — corrective batch, P2 robustness/scale (5 bugs incl. GUI-thread pacing sleep, single-symbol data
> plane → `TickerSession` extraction, unbounded growth). D1–D23 are **not** reopened; D24–D28 are additive.
> See D24–D28, Journeys 29–35, `AC-D24.*`–`AC-D40.*`, A56–A67, R51–R60, DG46–DG52. **Owner decision 2026-10-14
> (Q41): D24–D28 approved as-built; D36–D40 as-built/APPROVED (see the Status block).**

## Problem Statement
NDThinkChart is a feature-complete desktop trading terminal (PyQt6 + pyqtgraph +
official `ibapi`, live TWS port 7496) built through Phases 1–10. (That roadmap,
`PENDING_IMPLEMENTATION_PLAN.md`, was deleted by the owner on 2026-10-15;
`docs/phase-changelog.md` is the surviving phase-by-phase record.) It is now in a
**feedback-driven stabilization phase**: the user reviewed the running app and reported functional issues and UI
bugs, which this run must triage and fix. Batch 1 (D1–D3) was the complete list
for the first stabilization run and is clarified and built. Batch 2 (D4–D6) is now
fully clarified from post-build UI feedback 2026-09-19 (zoom label size with
magnifier +50% and position fine — Q15/Q16 — **volume log lower bound 1.0 — Q17 —
SUPERSEDED by D8 (linear, Q20); see D5** — and candlestick wick 1px vs body ≥4× —
Q18). Batch 3 (D7 35% gap) is a time-axis
spacing refinement confirmed 2026-09-19. Batch 4 (D8) is a volume-panel revision
(linear, no negatives, dynamic nice ticks, price-coloured) confirmed 2026-09-19.
Batch 5 (D9 volume spacing follow and D10 volume show/hide at top left of volume
panel) is now clarified 2026-09-19 (Q21 correct, Q22 top left). Batch 6 (D11
drawing price labels on inner right side) is clarified 2026-09-19 (Q23 correct).
Batch 7 (D12) zone double-click settings popup with 4 tabs is clarified 2026-09-19
(Q24 Extend omitted). Batch 8 (D13 watchlist resizable to 50% with persistence +
D14 double-click row to load chart) clarified 2026-09-20 per Q25–Q29. Batch 9
(D15) horizontal line double-click settings popup with 4 tabs is clarified 2026-09-20 per Q30.

**New work item — 2026-10-02 (defect D16) — CLARIFIED.** The user reported that historical bars are **missing across 2026-09-19…2026-09-27** on `SPY` `5 mins` (price candles) and that the **volume panel is empty over the same span**; 2026-09-21…2026-09-25 are normal trading weekdays, so this is a bar-data hole, not weekend session shading. The hole is an **internal** discontinuity in the cache: the screen shows bars 09/14–09/18, nothing 09/19–09/27, and bars 09/28–10/02 (validated live against `SPY 5 mins` in the user-space SQLite cache). D16 is captured in the Defect Register + Journey 17 and is the sole open requirement for this new batch. **Decisions (2026-10-02, Q37–Q39):** the app backfills the whole gap so the chart is continuous (chunking requests if needed); genuine market closures (weekend/holiday/overnight) stay **empty** and are not filled or compressed; the fix and its verification cover **all timeframes** (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and **any symbol**. **Correction (ESC-023, 2026-10-02):** the D16 trading-day calendar's New Year's observed-day shift is corrected to carry the **NYSE Rule 7.2 year-end accounting exception** — when Jan 1 falls on a Saturday, the preceding Friday (Dec 31) is a **trading day**, not a closure, and no New Year's holiday is observed; a genuine bar hole on such a day is therefore a missing trading session, not a genuine closure (see D16 / `AC-D16.7`). The corrected `T37-T03` acceptance criterion and the `market_calendar` observed-shift rule must both change (Task Manager / Build). All D1–D15 acceptance criteria are built and remain frozen/unchanged.


**New work item — 2026-10-03 (defects D17 + D18) — CLARIFIED 2026-10-03 (B1–B4 answered).** The user
reviewed the running app **in full screen** and reported two panel-layout problems (verbatim in the
Defect Register): **(D17)** the **Watchlist** dock on the left is too small and "does not extend or
reduce in width if user tries it"; the fix requested is to allow it to be extended **till 50% of the
chart area**, with the chart narrowing as the watchlist grows. **(D18)** the right-side **Active
Trader** section (which contains the ladder, with **Portfolio** below it) "does not even be visible
to user if the app is made full screen"; the fix requested is to reposition it so it fits the visible
full-screen area, allow it to be enlarged **till 40% of the chart area**, keep **Active Trader and
Portfolio at the same width**, and narrow the chart as it grows. D17 is diagnosed as a **likely defect
in the built D13 behaviour** (the 50% cap exists as helpers but is never enforced during a dock drag —
see D17), while D18 is a **new requirement** (no prior defect covers the right dock's width or
full-screen visibility — see D18). Both are captured in the Defect Register + Journeys 18–19 with
**final** acceptance criteria. **Decisions (2026-10-03, B1–B4 answered):** **(B1)** the watchlist cap
is **50% of the CHART AREA**, not of the window — this **supersedes and corrects D13's Q25
denominator** ("50% of MainWindow width"), and `AC-D13.1`–`AC-D13.3`, Journey 14, A17 and R15 are
updated in lockstep. **(B2)** Active Trader and Portfolio live in **ONE right-dock region** containing
both stacked sections, so they share equal width by construction; the **40%-of-chart-area** cap
applies to that one region. **(B3)** **independent caps + a chart-minimum rule**: each dock clamps
against its own % (watchlist 50%, right dock 40%) **and** against the remaining space so the chart
keeps a minimum (~400px); enlarging one can force the other to shrink. **(B4)** the watchlist handle
drags **both wider and narrower** between min (150px) and cap; min stays 150px, default ~220px, and
persistence (Q26) is **still required**. See `open_questions.md` (B1–B4 answered) and DG23–DG26.

**New work item — 2026-10-05 (defect D19) — CLARIFIED 2026-10-05 (B5–B6 answered).** The user reported that **D17 still did not work in the real app** — the watchlist would not grow much even at maximum drag — and asked whether the maximum width was too small. Repo-validated diagnosis: **the 50%-of-chart-area formula is correct** (`ui/dock_layout.watchlist_max_width(1716)` = **858px**); the real root cause was that the toolbar (`ui/main_window.py:100–211`) has a **~1716px `minimumSizeHint`** and sits **inside the central widget** (`:217–223`), so `QMainWindow` could not shrink the central area and the dock splitter had **no slack** — the watchlist was pinned at its 150px minimum and the right Active-Trader region was pushed off-screen. **Both the D17 and D18 symptoms share this one root cause.** The D17/D18 test harnesses hid the toolbar (`toolbar.hide()`), so the offscreen suite exercised a window unlike the real app and could not catch this. D19 is a **new defect** (Defect Register + Journey 20) that makes the D17/D18 criteria hold **in a toolbar-visible window** and removes the test masking. **D17/D18 are not silently reopened** — their criteria stand; D19 adds the real-app condition and the regression guard. **Decisions (2026-10-05, B5–B6 answered):** **(B5)** the toolbar gets a **horizontal scroll / elide wrapper in place** — it stays **inside the central widget** (NOT moved to a `QMainWindow` toolbar area) as a **single ~36px row**, and its effective minimum width no longer pins the central widget; all controls stay reachable via horizontal scroll/elide. **(B6)** the watchlist cap **stays `floor(0.50 × chart_area)`** (B1 stands); the cap constant and `AC-D13.1`/`AC-D17.1` are unchanged. See `open_questions.md` (B5–B6 answered) and DG27/DG28.

**New work item — 2026-10-06 (defect D20) — CLARIFIED 2026-10-06 (B7–B8 answered).** The user reviewed the running app and reported that in the D19 toolbar wrapper the **bottom of the letters in the toolbar labels is slightly covered by the horizontal scrollbar**, so the labels are not clearly readable; the requested fix is to **increase the toolbar height** so the labels read clearly. Repo-validated: the D19 wrapper fixes **both** the toolbar and the `ToolbarScroll` QScrollArea at **36px** (`ui/main_window.py:102`, `:233`), so the horizontal scrollbar is laid out within that same 36px and overlaps the content's descenders. D20 is a **new defect** (Defect Register + Journey 21) that **explicitly supersedes/relaxes `AC-D19.4`'s `<= ~40px` height bound** (recorded on `AC-D19.4`); D19's scroll/elide reachability and the D17/D18 criteria stand unchanged. **Decisions (2026-10-06, B7–B8 answered):** **(B7)** keep the toolbar **content row at ~36px** and give the horizontal scrollbar its **own reserved lane below** the content, so the **total strip grows to ~50–52px** — the content row does **not** grow and the strip does **not** grow to ~60px. **(B8)** **reserve the scrollbar lane** and show the horizontal scrollbar **as-needed** (only when the toolbar content overflows), so it never overlaps the labels; the reserved lane keeps the total height stable at ~50–52px in both states. See `open_questions.md` (Batch 14, D20, B7–B8 answered) and `AC-D20.1`–`AC-D20.6`.

**New work item — 2026-10-06 (Batch 15, defects D21.1–D21.13) — CLARIFIED AND FINALISED 2026-10-06 (B9–B13
answered).** The user reported **13 UI defects/issues** in a single message after the D20 batch was built and
green (`04397d9`, 585 tests). They are captured as batch **D21** (sub-defects **D21.1–D21.13**); **D1–D20 are NOT
reopened** and D20's `AC-D19.4` supersession stands. The batch groups into: **volume axis/pane (D21.1, D21.2,
D21.6)**, **Ext-Hours/RTH label (D21.3)**, **empty-space collapse (D21.4)**, **watchlist columns + header (D21.5,
D21.11)**, **button active-highlight + hide affordances (D21.7, D21.8, D21.12, D21.13)**, and **alarm edit +
smart setup (D21.9, D21.10)**. A **shared visual convention** — the "hidden/off" diagonal strike-through
(`VIS-D21.1`) and the active-button highlight (`VIS-D21.2`) — is defined once as **`VIS-D21`** and referenced by
each affected defect. **Decisions (2026-10-06, B9–B13 answered):** **(B9)** collapse only the **gaps between
trading sessions** (overnight/weekend/holiday) on **intraday** timeframes, `1 day` a no-op, within-session spacing
preserved; with RTH selected only RTH bars show and all non-RTH time collapses — D21.4 **supersedes the display
part of `AC-D16.3`** (D16's no-silent-hole rules unchanged). **(B10)** the addable column set is the **existing 7
columns**, Symbol cannot be removed, and the layout **persists**; a header right-click opens the add/remove/
rearrange popup. **(B11)** the volume pane can grow to **≥360px** (3× the 120px cap) with a **~200px price-pane
minimum**. **(B12)** the watchlist keeps its **in-panel header label** as the toggle (duplicate dock title
deleted); the right dock's **"Active Trader" title bar** and the portfolio's **"Account Summary" summary label**
become toggles; one hidden collapses **in height**, both hidden collapse the right dock **horizontally** to the
button strip. **(B13)** the alarm row **Edit** button opens a small edit dialog (price/condition/sound/note,
Save/Cancel, immediate persist; triggered alarms editable and keep state); the smart-alarm **yellow dashed
preview line** is drawn while the popup is open, follows the price live, is removed on close, and the condition
defaults **only on open** (Cross Below/Above by current vs alarm price; **Cross Above** when unknown). See
`open_questions.md` B9–B13 (answered), D21, Journeys 22–26, `AC-D21.*`, A41–A47, and R37–R44.

**New work item — 2026-10-07 (Batch 16, feature D22) — CLARIFIED AND FINALISED 2026-10-07 (B14–B16 answered).** The
user asked "how do I add tickers to the watchlist"; repo-validated, there is currently **no in-app way** — the
watchlist is populated at startup from the SQLite `watchlist` table (`data/db.py::get_watchlist`) or seeded from
`DEFAULT_WATCHLIST = ["AAPL","TSLA","SPY","QQQ","NVDA"]` on first run (`ui/main_window.py::_restore_watchlist`), and
the only watchlist context menu today is the **D21.5 column** manager (right-click a *column header* →
add/remove/rearrange columns). The user asked to capture this as a new feature requirement. **D22** is therefore a
**new feature** (not a defect) and does **not** reopen D1–D21: an **in-app "Add symbol" / "Remove symbol" affordance
on the watchlist** so a ticker can be added/removed without editing the database by hand, appended to the table,
subscribed live, and **persisted across restarts**. **Decisions (2026-10-07, B14–B16 answered):** **(B14)** scope is
**add + remove** (no reordering); **(B15a)** a small **`+` button on the watchlist header strip** (next to the
"Watchlist" toggle) **plus a right-click "Add symbol…"** entry (and a **"Remove symbol"** entry); **(B15b)** a
**small modal input dialog** (QInputDialog-style, text field + OK/Cancel); **(B16)** the add must perform a **live
IBKR contract lookup** (e.g. `reqContractDetails`) before adding, **blocking/holding the add when the contract can't
be resolved** and surfacing an error (today `ibkr/contracts.get_contract_for_symbol` builds a stock contract for any
string with no IBKR lookup — this changes the add flow); **(B16b)** adding is **disallowed while IBKR is
disconnected**. See D22, Journey 27, `AC-D22.1`–`AC-D22.9`, A48–A52, R45–R48, and `open_questions.md` B14–B16.

## Goals
- Collect and triage the user's reported functional issues and UI bugs.
- Fix each reported defect such that its per-task **test condition** passes.
- Keep the existing behavior and test suite intact — no regressions.
- Keep the live-order path safe: the per-run "gated in TWS" planning assumption is **retired** (owner decision
  2026-10-14, Q42), so D26 may be planned against the live-order path, but the safety behaviour stands —
  `IBKR_PORT != 7496` fails fast, every order requires explicit user action, confirm dialogs remain, and no
  automated test transmits an order.

## Non-Goals
- Net-new feature development (this is bug-fix/UI repair only, unless a fix
  inherently requires small supporting work).
- Visual redesign / restyling beyond correcting the reported UI defects.
- The GUI test suite spec in `test_gui.md` as a standalone deliverable, and
  "Phase 12" combo/BAG multi-leg order placement — both explicitly out of scope
  for this run (from Q2).
- Introducing a paper/simulated trading mode, or changing the live-only port 7496
  model.
- Changing the tech stack.

## Existing Repository

This is an existing repository. NDThinkChart is a stabilization/extension run against an
already-built PyQt6 + pyqtgraph + `ibapi` desktop trading terminal (development build:
`python main.py`; bundled: PyInstaller windowed `.app`, bundle id `com.ndthinkchart.app`).
The D1–D15 work is built and green. This section is preserved through every rewrite because
Plan, the Plan Artifact Editor & Validator, and the Orchestrator key **existing-repo mode**
off of the marker sentence above.

**What is being built/changed in this run:** the **D16** historical-bar backfill (built and green,
2026-10-02) plus two **2026-10-03 panel-layout defects (D17 + D18), clarified 2026-10-03 (B1–B4
answered)**:
- **D17 — Watchlist resize in full screen (CLARIFIED):** the Watchlist dock must be draggable in
  **both directions** between its minimum (150px) and its cap of **50% of the chart area**, with the
  chart area narrowing as it grows and the cap enforced **during the drag** (not only on window
  `resizeEvent`); the width persists per Q26. Expected to live in the existing dock/splitter wiring
  (`ui/main_window.py` dock setup + resize handling; `ui/watchlist_panel.py` clamp helpers).
- **D18 — Active Trader/Portfolio right dock in full screen (CLARIFIED, new requirement):** a
  **single right-dock region** (Active Trader ladder + Portfolio stacked) must be fully visible in
  full screen, resizable up to **40% of the chart area**, with the two stacked sections inherently at
  equal width (one region) and the chart narrowing as it grows; combined with D17 under the
  chart-minimum rule (B3). Expected to live in `ui/main_window.py` (`RightDockWidgetArea` setup)
  and/or the panel classes (`ui/active_trader_panel.py`, `ui/active_portfolio_panel.py`).
No new product features beyond these layout fixes, and **no stack change**. Both are finalised by
B1–B4 (`open_questions.md`); D17 corrects D13's denominator in lockstep (B1).
- **D19 — toolbar pinned the central widget (NEW, 2026-10-05, CLARIFIED 2026-10-05):** the D17/D18 fix was not observable in a toolbar-visible window because the toolbar's ~1716px `minimumSizeHint` pinned the central widget and starved the dock splitter; the D17/D18 harnesses hid the toolbar, masking the constraint. **Fix (B5, 2026-10-05):** wrap the existing toolbar in a **horizontal scroll / elide** container so it stays **inside the central widget** as a **single ~36px row** while its minimum width no longer pins the layout; all controls remain reachable. The watchlist cap is unchanged at **50% of the chart area** (B6). See D19, Journey 20, `AC-D19.1`–`AC-D19.7`, A37–A38, R32–R34, and `open_questions.md` B5–B6 (answered).
- **D20 — toolbar label descenders clipped by the horizontal scrollbar (NEW, 2026-10-06, CLARIFIED 2026-10-06):** the D19 scroll wrapper fixed the toolbar and its `QScrollArea` at **36px**, so the horizontal scrollbar overlapped the label descenders; the user wants the toolbar **height increased** so labels read clearly. **Fix (B7, 2026-10-06):** keep the toolbar **content row at ~36px** and give the horizontal scrollbar its **own reserved lane below**, so the **total strip is ~50–52px** (the content row does not grow and the strip does not reach ~60px); the scrollbar is **as-needed** in that reserved lane (B8). D20 **explicitly supersedes/relaxes `AC-D19.4`'s `<= ~40px`** bound to the new **~52px container bound** (recorded on `AC-D19.4`) while preserving D19's scroll/elide reachability and the D17/D18 criteria. See D20, Journey 21, `AC-D20.1`–`AC-D20.6`, A39–A40, R35–R36, and `open_questions.md` B7–B8 (answered).

- **D21 — Batch 15, 13 UI defects/issues (NEW, 2026-10-06, CLARIFIED AND FINALISED 2026-10-06):** the user's 13
  reported UI defects/issues (D21.1–D21.13). **Fixes:** volume Y min never below `0` (D21.1); volume Y max
  `[0, 1.10 × max visible]` on any visible-x-range change (D21.2); `Ext Hours` button relabels to `RTH` when off
  (D21.3); collapse non-trading **between-session** gaps on intraday timeframes (D21.4, superseding the display
  part of `AC-D16.3`); watchlist column add/remove/rearrange via a header right-click popup over the **existing 7
  columns** with **persistence** and **Symbol non-removable** (D21.5); volume pane can grow to **≥360px** with a
  **~200px price-pane minimum** (D21.6); persistent active-button highlight (`VIS-D21.2`) (D21.7/D21.8); alarm row
  **Edit** dialog (price/condition/sound/note, immediate persist; triggered alarms keep state) (D21.9); smart
  alarm **yellow dashed preview line** + auto condition default (D21.10); watchlist **in-panel header label**
  becomes the hide/show toggle with the duplicate dock title deleted (D21.11); volume button diagonal strike when
  hidden (D21.12); **Active Trader** (dock title bar) + **Account Summary** (portfolio summary label) become
  hide/show toggles with in-height / horizontal collapse geometry (D21.13). See D21, Journeys 22–26, `AC-D21.*`,
  A41–A47, R37–R44, and `open_questions.md` B9–B13 (answered).


- **D22 — in-app "Add symbol" / "Remove symbol" affordance on the Watchlist (NEW FEATURE, 2026-10-07, CLARIFIED
  AND FINALISED 2026-10-07):** there is no in-app way to add/remove a ticker today (the symbol list is populated
  from the SQLite `watchlist` table at startup, seeded from `DEFAULT_WATCHLIST` on first run, or configured only for
  **columns** via the D21.5 header popup). D22 adds an in-app **add** affordance (a small **`+` button on the
  watchlist header strip** next to the "Watchlist" toggle, **plus a right-click "Add symbol…"** entry — B15a) opening
  a **small modal input dialog** (B15b), which **validates the symbol with a live IBKR contract lookup**
  (`reqContractDetails`) before adding (B16), appends a row to `WatchlistPanel` (reusing `add_symbol` → live
  `req_mkt_data`), and **persists it across restarts** via the existing `watchlist` table (`db.get_watchlist` /
  `db.set_watchlist`). Adding is **disallowed while IBKR is disconnected** (B16b). D22 also adds **removal** (a
  per-row delete / right-click **"Remove symbol"**) that cancels the subscription, removes the row, and persists
  (B14). **No reordering.** A new IBKR contract-details request/callback path is required — none exists today.
  Expected to live in `ui/watchlist_panel.py` (affordances + add/remove path), `ui/main_window.py` (connection-gated
  wiring + persistence), `data/db.py` (persistence), and `ibkr/` (contract-details request/callback). The D21.5
  **column** layout (QSettings `watchlist/columns`) is a separate concern and must not be conflated with the symbol
  list.
- **D23 — Batch 17, D22 post-build quality corrections (NEW, 2026-10-07, CLARIFIED AND FINALISED
  2026-10-07):** two **nice-to-have** Code Reviewer findings on the just-built D22 work, approved by the user for
  correction. **(D23.1 = ESC-030)** `MarketDataManager.cancel_contract_details` calls
  `self.client.cancelContractDetails(req_id)` inside `try/except`, but the pinned `ibapi` **9.81.1.post1** (the pin at D23 report time; **10.51.1** now) `EClient`
  has **no** `cancelContractDetails` (verified: `hasattr(EClient,'cancelContractDetails') is False`; only
  `reqContractDetails` exists), so on the real TWS path the call raises `AttributeError` that is silently swallowed
  → the cancel is a wire no-op. The fix is a **capability-guarded, documented** cancel (call the method only if
  present; document that TWS's own `contractDetailsEnd`/error ends the request and `ContractLookupService`'s bounded
  QTimer + `cancel_all` invalidation is the real safety net), **superseding the task-level `AC-D22.2.3`** wire-cancel
  mandate and **reconciling architecture `S3`**. **(D23.2 = ESC-031)** `WatchlistPanel.remove_symbol` re-indexes
  `_row_data` but never drops the removed row's own key, so removing the **last** row leaves a stale `_row_data[row]`
  entry; the fix requires `_row_data` keys to be exactly `range(rowCount())` after any removal and adds the missing
  last/first/only-row coverage. Both are **quality fixes** — no D22 behaviour depends on the wire cancel, and the
  stale key is currently benign — so D23 does **not** reopen D22's feature criteria (`AC-D22.1`–`AC-D22.9` stand).
  See D23, Journey 28, `AC-D23.1.*`/`AC-D23.2.*`, A53–A55, R49–R50.

**Repository mapping note (graphify).** A knowledge graph exists at `graphify-out/`
(`graph.json`, `GRAPH_REPORT.md`). Per `AGENTS.md`, downstream agents — Plan, Plan Artifact
Editor & Validator, Task Manager, Build/Build Worker, and Code Reviewer — **may use the
graphify tool** to map existing components, data models, integrations, and relationships.
Graphify findings are discovery inputs only and MUST be validated against the current
repository files, which remain authoritative if the two disagree.

**Current Tech Stack:**
- **Language/runtime:** Python 3.11+ (`.venv`), macOS Apple Silicon (arm64).
- **UI:** PyQt6 (`PyQt6>=6.6`), pyqtgraph (`>=0.13`).
- **Broker:** official `ibapi` — pinned `ibapi-latest==10.51.1` (PyPI dist name; provides the `ibapi` module), Interactive Brokers TWS, **live port 7496 only — no paper mode**.
- **Numerics:** numpy (`>=1.26`).
- **Secondary data source (D38):** `yfinance==1.7.0` (pinned; the sole secondary source for corporate events/news — owner decision 2026-10-13; quarterly re-pin policy).
- **Persistence:** SQLite. `config/paths.get_db_path()` always resolves to the user-space
  database `~/Library/Application Support/NDThinkChart/charting_app.sqlite3` (the filename
  can be overridden with the `DB_PATH` env var). A stale repo-root `./charting_app.sqlite3`
  exists but is not the path `get_db_path()` returns.
- **Packaging:** PyInstaller windowed `.app`, bundle id `com.ndthinkchart.app`.
- **Tests:** pytest + pytest-qt, run offscreen (`QT_QPA_PLATFORM=offscreen`), no live TWS
  required by default.
- **Existing bar-load path (reference):** `ui/main_window.py::load_chart` →
  `BarCache.get_bars` → `MarketDataManager.req_historical_data` (`TIMEFRAME_CONFIG`
  duration/bar size) → `IBApiClient.historicalData` → `_on_historical_bar` /
  `_on_historical_data_end` → `BarCache.save_bars` → `ChartPanel.update_chart` →
  `ChartPanel._refresh_candles` (shared by the price **and** volume panels).

## Constraints

### Observed from repository (confirmed, Q5)
- **Language/runtime:** Python 3.11+ (`.venv`), macOS Apple Silicon (arm64).
- **UI:** PyQt6 (`PyQt6>=6.6`), pyqtgraph (`>=0.13`) for charting.
- **Broker:** official `ibapi` — pinned `ibapi-latest==10.51.1` (provides the `ibapi` module), Interactive Brokers TWS.
- **Numerics:** numpy (`>=1.26`).
- **Secondary data source (D38):** `yfinance==1.7.0` (pinned; sole secondary source for corporate events/news).
- **Persistence:** SQLite — always the user-space database returned by `config/paths.get_db_path()` (`~/Library/Application Support/NDThinkChart/charting_app.sqlite3`; filename overridable via the `DB_PATH` env var). `config/settings.py::DB_PATH` is **unused**, and the stale repo-root `./charting_app.sqlite3` is **not** the live path (see Current Tech Stack).
- **Connectivity:** live TWS port **7496 only — no paper mode**.
- **Packaging:** PyInstaller windowed `.app`, bundle id `com.ndthinkchart.app`.
- **Tests:** pytest + pytest-qt, run offscreen (`QT_QPA_PLATFORM=offscreen`),
  no live TWS required by default.

### Confirmed for this run
- **Live-order path may be touched.** The original per-run assumption that live orders are gated
  at the TWS API layer (Q4) is **retired** by owner decision 2026-10-14 (Q42), so D26 may be planned
  against the live-order path. Retained safety behaviour: `config/settings.py::check_live_port` fails
  fast unless `IBKR_PORT == 7496`; every order requires explicit user action; confirm dialogs remain;
  and no automated test transmits an order or connects to live TWS (Q9).
- **Definition of done:** all test conditions pass; test conditions are defined
  and updated per task as defects are triaged (Q3).
- **Regression-test policy (Q8, confirmed):** every fix ships with a check that
  fails before the fix and passes after, runnable offscreen
  (`QT_QPA_PLATFORM=offscreen`, no live TWS). The pre-existing suite must stay green.
- **Live-order test safety (Q9, confirmed):** no automated test may connect to live
  TWS or transmit an order. Order-path changes are verified by unit-testing the
  generated order fields; any live check is a manual user-run step.
- **Feedback cadence (Q7, confirmed):** defects arrive one message at a time; the
  Analyst may ask follow-ups. The full requirements→build flow may repeat until the
  user is satisfied.

### Business / regulatory / timeline
- None stated. No deadline or compliance driver provided.

## Glossary
| Term | Meaning in this repo |
|---|---|
| Defect | A reported functional issue or UI bug to be fixed in this run. |
| Test condition | The per-task pass/fail check for a defect fix; must be independently testable (Q3). |
| Study | A technical indicator/overlay (SMA, EMA, VWAP, Bollinger, RSI, MACD, ICT, RTH gaps, VIX SD). |
| Drawing | A user chart annotation (trendline, horizontal, zone, fibonacci, measure), optionally in a group. |
| DOM / Ladder | Level II market-depth ladder with click-to-trade rows. |
| Live-order path | Code that builds/transmits orders via `ibkr/orders.py` + `IBApiClient`. The per-run "gated
  in TWS" planning assumption is **retired** (owner decision 2026-10-14, Q42); D26 may be planned/decomposed
  against this path. Safety behaviour is unchanged: `IBKR_PORT != 7496` fails fast
  (`config/settings.py::check_live_port`), every order needs explicit user action, confirm dialogs remain, and
  no automated test transmits an order. |
| Genuine closure | A market-closed interval that is legitimately non-trading (weekend, actual US-equity holiday, or overnight). Stays **empty** per D16 (`AC-D16.3`). **Dec 31 of a year whose next Jan 1 is a Saturday is NOT a genuine closure** — it is a trading day (`AC-D16.7`, ESC-023). |
| Chart area | The central region of `MainWindow` holding the chart, excluding the docked panels (Watchlist on the left; the single Active Trader + Portfolio right dock). Panel caps in D17/D18 are percentages of **this** region (B1/B2), not of the whole window. |
| Chart-minimum rule | The hard floor (~400px) the chart area must keep, independent of the two docks (B3): each dock clamps against its own % **and** against the space left so the chart never drops below the minimum. Enlarging one dock can force the other to shrink. |
| Right dock (D18) | The **single** `RightDockWidgetArea` region containing the Active Trader ladder and the Portfolio section stacked vertically (B2). Because it is one region, its two sections are inherently equal width; the 40%-of-chart-area cap applies to the region as a whole. |

## User Journeys

### Journey 1 — Defect report → fix → verification (operational journey)
- **Preconditions:** App is runnable; user has observed a functional issue or UI
  bug in the application.
- **Steps:**
  1. User reports the defect (screen/area, steps, expected vs actual).
  2. Requirements Analyst records it in the Defect Register below with a testable
     acceptance criterion (the test condition).
  3. Plan/Task Manager/Build implement the fix.
  4. The test condition is executed; the full existing suite is re-run.
- **Postconditions:** Defect resolved, its test condition passes, and no existing
  test regresses.
- **Edge Cases:**
  - Report is not reproducible (missing environment/symbol/timeframe) → route back
    to the user for detail (see Q7) before accepting as a defect.
  - Report actually describes a new feature rather than a bug → reclassify to
    `feature_suggestions.md`, do not treat as in-scope.
  - Reported fix conflicts with an existing test's expected behavior → resolve
    explicitly; do not silently change the test to make it pass.

### Journey 2 — D1: distinguish sessions at a glance
- **Preconditions:** A symbol is loaded; Ext Hours is ON; timeframe is intraday.
- **Steps:** 1) Load chart. 2) Observe the background bands behind the candles.
- **Postconditions:** Pre-market appears orange @10%, post-market blue @10%; RTH and
  overnight are unshaded, so session context is readable without a tooltip.
- **Edge Cases:** On a `1 day` chart no bands appear; toggling Ext Hours OFF removes
  them; DST days keep boundaries at ET local time.

### Journey 3 — D2: read the exact price under the crosshair
- **Preconditions:** A symbol is loaded; the Active Trader and/or Portfolio dock is
  open on the right.
- **Steps:** 1) Hover the cursor over the price plot. 2) Read the price chip in the
  Y-axis lane to the right of the plot's vertical axis line.
- **Postconditions:** The full price, including all decimal places, is visible as a
  grey pill with white text in the Y-axis lane; it is never covered by the right-hand
  dock. Overlapping the Y-axis price tick label at the same price is expected and
  permitted.
- **Edge Cases:** A long price (`123,456.78`) does not bleed under the dock while the
  chip remains in the axis lane; hovering at the top/bottom edge keeps the chip in view;
  the chip is hidden when the cursor leaves the plot; a Y-axis tick label at the same
  price may sit underneath the chip by design.

### Journey 4 — D3: zoom into a chosen area
- **Preconditions:** A symbol is loaded.
- **Steps:** 1) Click the magnifier. 2) Drag a rectangle over the region of
  interest. 3) Release. 4) (Optionally) press `Esc` on a later drag; click Reset.
- **Postconditions:** On release the selected rectangle expands to fill the chart
  (both axes); magnifier stays active for another selection; Reset restores the
  default framing.
- **Edge Cases:** A near-zero-area drag is ignored; a drag starting outside the plot
  does nothing; with no bars loaded the controls are disabled; `Esc`/right-click
  cancels without changing the view.

### Journey 5 — D4: see and use the zoom controls
- **Preconditions:** A symbol is loaded.
- **Steps:** 1) Observe the top-right cluster. 2) Read the `-` / `+` / `⌕` / `Reset`
  labels. 3) Resize the window.
- **Postconditions:** Glyphs are legibly 14px/700; the cluster’s right edge is left of
  the price axis and never clipped, regardless of window size.
- **Edge Cases:** Narrow window or wide axis (5-digit prices) keeps the cluster
  inside with `x >= 8`; magnifier checkability unchanged.

### Journey 6 — D5: read volume distribution
- **Preconditions:** A symbol is loaded with mixed small and large volumes (e.g., a
  spike at 16:00).
- **Steps:** 1) Observe the volume histogram. 2) Note small-volume bars vs the
  spike.
- **Postconditions:** Small volumes are visibly distinct; Y is logarithmic and
  ticked at 1e6/1e7. **(Superseded by Journey 9 / D8: Y is linear from `0` with a
  dynamic nice max; retained for history.)**
- **Edge Cases:** Zero-volume bars appear as a 1-unit minimal tick, not a gap;
  max-volume spike does not collapse the rest; X remains linked to price.

### Journey 7 — D6: distinguish wick from body
- **Preconditions:** A symbol is loaded with candles that have shadows.
- **Steps:** 1) Observe any candle with a high/low shadow. 2) Compare wick vs body.
- **Postconditions:** The wick is a thin 1px line distinct from the wider body and
  extends beyond the body when a shadow exists; direction colour is consistent.
- **Edge Cases:** Dense 1-min chart with hundreds of candles keeps wick thin
  (body narrows but wick stays 1px); Doji `open==close` still shows wick behind
  body; High-DPI does not merge wick and body.

### Journey 8 — D7: see spacing between candles
- **Preconditions:** A symbol is loaded on an intraday timeframe (e.g., 5-min).
- **Steps:** 1) Observe the gap between adjacent candle bodies at default zoom.
- **Postconditions:** The gap is visibly larger than the current 20% of spacing
  (about 35% of spacing), so individual candles are distinct.
- **Edge Cases:** Dense 1-min view keeps a positive gap even when the 4px body
  minimum applies; single-bar fallback unchanged; studies and session bands
  continue to frame correctly.

### Journey 9 — D8: read volume at a glance
- **Preconditions:** A symbol is loaded with varied volumes (e.g., spikes and quiet periods).
- **Steps:** 1) Observe the volume histogram’s Y axis. 2) Note the bar colours vs the price candles above.
- **Postconditions:** Y is linear starting at `0` with no negatives; the max is a nice value like `500.0K / 1.0M / 2.5M` that contains the tallest bar; bars are green when the price candle was up and red when down.
- **Edge Cases:** All-zero volumes show `0–100` (smallest nice value, no fixed `10k`
  floor) with minimal bars; a max just below a nice boundary rounds up; small and large
  volumes remain distinguishable.

### Journey 10 — D9: see aligned price and volume spacing
- **Preconditions:** A symbol is loaded on an intraday timeframe with both price and volume visible.
- **Steps:** 1) Observe the gap between price bodies. 2) Observe the gap between volume bars at the same x positions.
- **Postconditions:** The inter-bar gaps are identical (volume width `w*2` matches price body width, 35% gap), so price and volume bars are vertically aligned.
- **Edge Cases:** Dense 1-min view keeps gaps aligned even when the 4px minimum applies; single-bar fallback aligns; Line/Area modes still align volume.

### Journey 11 — D10: show/hide volume to reclaim space
- **Preconditions:** App is running with a loaded chart; the volume panel is visible.
- **Steps:** 1) Toggle the volume control. 2) Observe the price plot height. 3) Toggle again.
- **Postconditions:** Toggling hides the volume plot and its axis, the price plot expands; toggling again shows it; the app does not error with no bars.
- **Edge Cases:** Oscillator visibility is independent; splitter restores correctly; hidden state resets to visible on restart (no persistence in this proposal).

### Journey 12 — D11: read drawing price on the inner right side
- **Preconditions:** A symbol is loaded and a drawing (horizontal line or zone) exists.
- **Steps:** 1) Observe the right edge of the price plot interior.
- **Postconditions:** The drawing’s price(s) are visible as labels inside the plot near the right edge, not on the axis.
- **Edge Cases:** Multiple zones at nearby prices stack without full overlap; zoom/pan
  keeps labels at the right edge and at the correct price; a crosshair hovering at a
  drawing's price no longer collides — the chip is in the Y-axis lane and the drawing
  label is inside the plot (D2/Q33), so `AC-D11.4` covers label-vs-label stacking only;
  no drawing → no label.

### Journey 13 — D12: edit a zone via double-click
- **Preconditions:** A zone (rectangle) drawing exists on the chart.
- **Steps:** 1) Double-click the zone body. 2) Observe the Zone Settings popup. 3) Switch between Style/Text/Coordinates/Visibility tabs. 4) Change a value and apply.
- **Postconditions:** Double-click opens the `Rectangle` popup with four tabs; Extend is not shown (zone always extends both sides); changes are applied to the zone and re-render.
- **Edge Cases:** Double-click on a non-zone drawing does not open the zone popup; double-click with no selection does nothing; Cancel/X closes without change.

### Journey 14 — D13: resize watchlist panel to see more symbols/columns
- **Preconditions:** App is running; Watchlist dock is docked on the left; window is at default 1400×900.
- **Steps:** 1) Hover over the vertical splitter handle between Watchlist and chart. 2) Drag right to widen.
- **Postconditions:** Watchlist width grows, chart narrows, handle remains draggable across
  `[150, floor(0.50×chart_area)]` (and the chart-minimum rule from B3), clamped both **during the drag**
  and on window resize. **Superseded denominator (B1, 2026-10-03):** the cap is 50% of the **chart
  area**, not of `MainWindow` width as originally stated in Q25 — see `AC-D13.1` and A17.
- **Edge Cases:** At max 50%-of-chart-area the handle stops; at min 150px it stops; floating Watchlist is unconstrained.

### Journey 15 — D14: double-click watchlist row to load chart
- **Preconditions:** Watchlist has symbols; IBKR may be connected or not; current chart may be `SPY`.
- **Steps:** 1) Double-click any cell in the `AAPL` row.
- **Postconditions:** If connected and `AAPL != SPY`, `symbol_input` becomes `AAPL` and chart loads for `AAPL` with current timeframe/ext-hours; if same symbol or disconnected, no-op with status message.
- **Edge Cases:** Double-click header/empty area → no-op; single-click only selects; same-symbol → no flicker/new reqId.

### Journey 16 — D15: edit a horizontal line via double-click
- **Preconditions:** A horizontal line drawing exists on the chart.
- **Steps:** 1) Double-click the line. 2) Observe the Horizontal line popup. 3) Switch tabs. 4) Change price/text and apply.
- **Postconditions:** Double-click opens `Horizontal line` popup with four tabs and current price pre-filled; changes update the line.
- **Edge Cases:** Double-click on a zone/non-horizontal does not open this popup; Cancel discards; single line coordinate only.

### Journey 17 — D16: reload after a cache gap shows continuous history
- **Preconditions:** The SQLite `bars` cache holds `SPY` `5 mins` bars in two blocks separated by a
  missing trading-session span (reported repro: bars through Fri 2026-09-18, nothing
  2026-09-19…2026-09-27, bars 2026-09-28…now); the closure exceeded the timeframe's IBKR fetch
  window (for `5 mins`, `5 D`); IBKR is connected; Ext Hours is ON.
- **Steps:** 1) Launch the app. 2) Load `SPY` on `5 mins`. 3) Wait for the historical request(s)
  to complete. 4) Inspect the price panel and the volume panel.
- **Postconditions:** The displayed bar series is continuous over the span it covers — bars exist
  for every trading session from the oldest displayed bar through now (including the missing
  2026-09-21…2026-09-25 weekdays); the app backfills the whole gap, issuing additional request(s)
  when the gap exceeds one IBKR request's duration. The price candles **and** the volume bars both
  render across that span; the only empty x-intervals are genuine market closures (weekend,
  holiday, overnight), which stay empty and are not filled, compressed, or interpolated.
- **Edge Cases:** weekend/holiday/overnight render as empty and are **not** treated as missing
  data; a cache gap larger than IBKR's maximum single-request duration is bridged with multiple
  requests (chunking) or the shortfall is surfaced explicitly, never left as a silent hole; an
  **internal hole** (newer cached bars separated from an older block by a missing span — the
  reported repro) is healed, not only a hole after the newest cached bar; an empty cache fetches
  the configured window; a cache newer than now is not redundantly re-requested; symbol/timeframe
  switch while a backfill request is in flight does not mix symbols/timeframes; the same behaviour
  holds on every timeframe (`1 min`…`1 day`) and any symbol (Q39); **Dec 31 of a year whose next Jan 1 is a Saturday is a trading session, not a closure (e.g. 2021-12-31, 2027-12-31, 2032-12-31, 2038-12-31), so a hole there must be backfilled/surfaced like any other trading day (`AC-D16.7`, ESC-023)**.

### Journey 18 — D17: resize the Watchlist in full screen
- **Preconditions:** App is running (dev build, `python main.py`) shown **full screen**; Watchlist dock
  is docked on the left; chart is loaded; a thin splitter handle sits between the Watchlist and the chart.
- **Steps:** 1) Drag the splitter handle to the right. 2) Observe the Watchlist widen and the chart
  narrow. 3) Drag back to the left. 4) Drag past the cap. 5) Restart the app.
- **Postconditions:** The Watchlist widens continuously up to **50% of the chart area** (B1) and the
  chart narrows correspondingly; dragging back reduces it (both directions work — B4); at the cap the
  handle stops without pushing the chart below its ~400px minimum (B3); the width survives a restart
  (Q26 persistence still required — B4). The cap is enforced **during the drag**, not only on
  `resizeEvent`.
- **Edge Cases:** Window is already full screen (no window resize fires during the drag → the cap must
  still be enforced during/after the drag, not only on `resizeEvent`); floating Watchlist unconstrained;
  dragging below the minimum stops at 150px; the right dock being enlarged shrinks the watchlist's
  available space so its effective cap drops (B3 cross-clamping); restart restores the persisted width
  clamped to the current cap (50% of the current chart area).

### Journey 19 — D18: use the Active Trader (+ Portfolio) dock in full screen
- **Preconditions:** App is running shown **full screen**; the **single right dock** (Active Trader
  ladder with Portfolio stacked below) is visible on the right; a chart is loaded.
- **Steps:** 1) Observe the right-hand region in full screen. 2) Enlarge the right dock. 3) Observe the
  chart narrow. 4) Compare Active Trader and Portfolio widths.
- **Postconditions:** The single right-dock region (Active Trader + Portfolio) is entirely within the
  visible window area (not clipped/off-screen); enlarging it grows it up to **40% of the chart area**
  (B2/B3) and the chart area narrows; Active Trader and Portfolio render at **equal width** because
  they are two stacked sections of one region (B2).
- **Edge Cases:** Both left (watchlist) and right docks enlarged at once must not squeeze the chart
  below its minimum — each clamps against the remaining space so the chart keeps ~400px, and enlarging
  one can force the other to shrink (B3); cross-clamping is exercised in the criteria; small full-screen
  display; docks hidden/floating; ladder content wider than the dock must not force the dock off-screen.

### Journey 20 — D19: resize the watchlist in the real (toolbar-visible) app
- **Preconditions:** App running (dev build, `python main.py`) with the **toolbar visible**; Watchlist docked on the
  left; a chart is loaded; the window is large enough that `floor(0.50 × chart_area) > 150px`.
- **Steps:** 1) Drag the watchlist splitter handle to the **right** to maximum. 2) Observe the watchlist widen and the
  chart narrow. 3) Observe the right Active-Trader/Portfolio region. 4) Resize the window narrower and repeat.
- **Postconditions:** The watchlist **actually reaches `floor(0.50 × chart_area)`** (not pinned at its 150px
  minimum); the right region stays **fully visible**; the chart keeps `>= 400px`; the toolbar remains **usable**
  (horizontal scroll / elide in place, one ~36px row — B5).
- **Edge Cases:** Window narrower than the toolbar's natural width → the toolbar scrolls horizontally / elides **in
  place** (B5: one ~36px row, still inside the central widget) and **no control becomes permanently unreachable**;
  full screen (no window `resizeEvent` during the drag) → the cap is still enforced during the drag (D17
  `AC-D17.3`); both docks enlarged → the chart minimum is preserved (`AC-D19.3`); right region hidden/floating → the
  watchlist-only rule applies.

### Journey 21 — D20: read the toolbar labels without the scrollbar covering them
- **Preconditions:** App running (dev build, `python main.py`) with the toolbar visible; the window is narrow
  enough that the toolbar's horizontal scrollbar is shown, or wide enough that it is hidden.
- **Steps:** 1) Observe the toolbar strip. 2) Read the labels (`Symbol:`, `TF:`, `Load Chart`, `Mode:`,
  `Studies…`, `Alarms (0)`, `Alarm Mode`, `Sound`, `DOM`, …). 3) Narrow the window so the toolbar scrolls
  horizontally and scroll it. 4) Widen the window again.
- **Postconditions:** Every toolbar label is **fully readable** — the horizontal scrollbar does **not** overlap
  or clip any label's descenders; the toolbar content stays a **single ~36px row** and the horizontal scrollbar
  occupies a **reserved lane below** it, so the **total strip is ~50–52px**; all controls remain reachable
  (directly when wide, via horizontal scroll when narrow).
- **Edge Cases:** Narrow window with the scrollbar shown → labels still unclipped (the scrollbar sits in its
  reserved lane below the content, never over it); wide window with the scrollbar hidden → labels unclipped and
  the reserved lane keeps the strip height stable at ~50–52px; high-DPI/font scaling → labels still unclipped;
  extremely small window → the chart-minimum/dock rule still applies; the toolbar never wraps to multiple rows.
### Journey 22 — D21.1 / D21.2 / D21.6: read and adjust the volume pane
- **Preconditions:** A symbol is loaded with bars; the volume pane is visible; the price and volume panes share the vertical splitter.
- **Steps:** 1) Drag the volume Y-axis downward. 2) Zoom into a low-volume region (and out again). 3) Drag the price/volume splitter upward to grow the volume pane.
- **Postconditions:** The volume Y minimum never goes below `0` (D21.1); on any visible-x-range change the volume Y range is `[0, 1.10 × max volume visible]` — 10% above the tallest visible volume candle (D21.2); the volume pane can grow to **at least 360px** (3× the former 120px cap) while the price pane keeps a **~200px minimum** (D21.6, B11).
- **Edge Cases:** All-zero visible volumes keep the D8 `[0, 100]` floor; a huge spike just outside the view does not inflate the max; the forming bar growing intra-bar still widens the max (ESC-007 preserved); very short window; oscillator pane present; volume hidden then shown; splitter restored; the price pane never drops below its minimum.

### Journey 23 — D21.4: collapse non-trading time
- **Preconditions:** An **intraday** timeframe (`1 min`…`4 hours`) is loaded with bars spanning at least one overnight/weekend closure; Ext Hours is ON or OFF (RTH).
- **Steps:** 1) Load the symbol. 2) Observe the x-axis between trading sessions. 3) Toggle Ext Hours OFF (RTH). 4) Load a `1 day` chart.
- **Postconditions:** The **gaps between trading sessions** (overnight, weekend, holiday) are **not** rendered as empty space — plotted bars are contiguous across consecutive sessions, while within-session spacing is preserved (B9); with **RTH selected**, only RTH bars are shown and **all non-RTH time collapses**; with Ext Hours ON, the D1 pre/post bands still render for the sessions shown; the `1 day` timeframe is a **no-op**. D16's backfill/no-silent-hole behaviour is unchanged (collapse is a display change only).
- **Edge Cases:** weekend/holiday/half-day; DST; the `1 day` timeframe (no-op); drawings, session bands and alarm lines stay correctly positioned after collapse; a single session with no closure; a trading-session data hole is still a defect (not collapsed away); only between-session gaps collapse — a partial/half-day missing afternoon is **not** collapsed.

### Journey 24 — D21.5 / D21.11: configure the watchlist and toggle it
- **Preconditions:** The watchlist is docked on the left and visible; symbols are listed.
- **Steps:** 1) Right-click a watchlist column header. 2) Add/remove/rearrange columns (the existing 7). 3) Restart the app. 4) Click the "Watchlist" toggle button to hide, then show the watchlist.
- **Postconditions:** The right-click popup adds/removes/rearranges columns over the **existing 7 columns** (`Symbol, Last, Bid, Ask, Chg, Chg %, Vol`), the **Symbol column cannot be removed**, the layout is **persisted** across restarts, and the table updates with values bound to the correct fields (D21.5, B10); exactly **one** "Watchlist" label remains — the **in-panel header label** turned into a toggle button (the duplicate dock title deleted) — and it toggles the watchlist, showing the `VIS-D21.1` diagonal strike-through when hidden while **staying visible** (D21.11, B12).
- **Edge Cases:** all other columns removed (only Symbol remains); Symbol-column removal is blocked; live ticks after a reorder; D14 double-click still loads the chart; collapsed-width geometry; width persistence (D13) when re-shown; floating watchlist.

### Journey 25 — D21.7 / D21.8 / D21.12 / D21.13: see active buttons and hide panels
- **Preconditions:** The toolbar and the right dock (Active Trader + Account Summary) are visible; the volume pane is visible.
- **Steps:** 1) Click Studies (open/close). 2) Toggle Alarm Mode on/off. 3) Hide the volume pane. 4) Hide the Active Trader panel, then the Account Summary panel, then both.
- **Postconditions:** Buttons in an active/selected state show a persistent, clearly visible highlight (`VIS-D21.2`, A41 confirmed); Alarm Mode's status-bar message persists until Alarm Mode is switched off; the Volume button shows the `VIS-D21.1` strike when the pane is hidden; hiding one right panel collapses it **in height** (its button remains) and the other **expands**; hiding **both** collapses the right dock **horizontally** to the button strip (chart reclaims the width); each hidden panel's button shows the strike (D21.13, B12). The **Active Trader** toggle is the right dock's **title bar** and the **Account Summary** toggle is the portfolio **summary label** (B12).
- **Edge Cases:** multiple toggles on at once; Studies dialog open then closed; placing an alarm or selecting a drawing tool exits Alarm Mode; both right panels hidden then re-shown; the DOM button hides the whole region — reconcile with per-panel hide; the collapsed right dock must not break the D17/D18 chart-minimum rule.

### Journey 26 — D21.9 / D21.10: edit an alarm and place a "smart" alarm
- **Preconditions:** A symbol is loaded; at least one alarm exists; Alarm Mode is available.
- **Steps:** 1) Open the alarm popup. 2) Click a row's Edit button and change price/condition/sound/note. 3) Activate Alarm Mode and click a price level on the chart. 4) Change the price in the popup.
- **Postconditions:** Each alarm row has an Edit button at the right end, the Note column fills the width up to it, clicking Edit opens a small edit dialog (price, condition, sound, note) with Save/Cancel that persists immediately, and editing a triggered/set alarm is allowed and keeps its state (D21.9, B13); the smart alarm popup pre-fills the clicked price, draws a **yellow dashed preview line** at that level **while the popup is open**, moves the line live as the price changes, **removes it when the popup closes** (replaced by the real alarm line after Add), and defaults the condition to **Cross Below when the current price is above the alarm price / Cross Above when below**, applied **only on popup open** and user-overridable — with **Cross Above** when the current price is unknown (D21.10, B13).
- **Edge Cases:** editing a triggered alarm (keeps its state); user overrides the auto condition; price equal to current price; current price unknown → Cross Above; popup opened from the Alarms button (no chart click); popup closed removes the preview line; editing while the chart is live.

### Journey 27 — D22: add or remove a ticker on the watchlist in-app
- **Preconditions:** The app is running; the watchlist is docked on the left and visible; the SQLite `watchlist` table
  holds the current symbols (or is empty and seeded from `DEFAULT_WATCHLIST`); IBKR connection state is known.
- **Steps:** 1) Invoke the add affordance (the `+` button on the watchlist header strip, or right-click → "Add
  symbol…" — B15a). 2) Type a symbol (e.g. `MSFT`) in the small modal dialog and confirm OK (B15b). 3) Observe the
  watchlist table. 4) Invoke remove on a row (per-row delete or right-click → "Remove symbol" — B14). 5) Restart the
  app.
- **Postconditions:** On a **validated** add, the symbol is **appended** to the watchlist table (row added; live
  subscription requested via `add_symbol` → `req_mkt_data`) and **persisted** so it reappears after a restart (read
  back from the `watchlist` table on launch). On a **remove**, the row is deleted, its live subscription is
  cancelled, and the removal is **persisted** so it stays gone after a restart. No database edit by hand is required.
  The D21.5 column layout is unaffected.
- **Edge Cases:** empty/whitespace input is rejected; a case-insensitive duplicate is a no-op with a message (A50);
  an unknown/unresolvable symbol is **rejected with an error and nothing is persisted** (B16 live validation);
  adding while IBKR is disconnected is **disallowed** (B16b); removing the last symbol leaves an empty watchlist
  that stays empty on restart (A52); the app restarts and `_restore_watchlist` reads the persisted list; the D21.5
  column header right-click menu still works and is not shadowed by the new affordances (DG42); the symbol is
  added/removed **without** loading its chart (distinct from the D14 double-click load and the toolbar Load Chart);
  the contract-details lookup is asynchronous, so the add completes (row appears) on resolution and is rejected on
  failure/timeout (no indefinite hang).

### Journey 28 — D23: post-build quality corrections on the D22 watchlist add/remove work
- **Preconditions:** D22 is built and green; the app is running with the watchlist visible; at least one symbol
  has been added. For D23.1, IBKR may be connected or not.
- **Steps:** 1) Add/remove symbols so the watchlist has 3 rows. 2) Remove the **last** row. 3) Inspect the panel's
  row-keyed state. 4) (D23.1) Let an `add` contract lookup time out or drop the connection mid-lookup; confirm the
  contract-details cancel is capability-guarded and that correct behaviour needs no wire cancel.
- **Postconditions:** After a last-row removal, `remove_symbol` leaves `_row_data` with keys exactly
  `range(rowCount())` (no stale key) and the table/rows remain correct; the contract-lookup cancel is
  capability-guarded and documented, so no `AttributeError` is raised or silently swallowed on the pinned `ibapi`,
  and `ContractLookupService`'s local invalidation (bounded QTimer + `cancel_all` on disconnect) is the safety net.
- **Edge Cases:** first-row / only-row / middle-row removal; removing from an empty table; re-add after a removal
  (vacated index reused cleanly); a live tick for a surviving reqId after a last-row removal; a client with no
  `cancelContractDetails`; a client whose capability-guarded cancel raises; `req_id is None`; lookup
  timeout / disconnect mid-flight.

**[NEW v1.2]**
### Journey 29 — D24: pop out chart windows and keep them per ticker
- **Preconditions:** IBKR connected; the main chart shows ticker X (e.g. `AAPL`, 5m, Candles); no pop-outs open.
- **Steps:** 1) Click **Pop out** (toolbar button / hotkey). 2) A chrome-free window opens showing X's chart —
  no toolbar, no docks, just a slim header (`X · 5m · Candles`) and the chart. 3) In the main chart, load
  ticker Y. 4) Pop Y out too. 5) In the main chart (still on Y), draw a zone and add a price alarm for Y.
  6) Switch the main chart back to X and draw a horizontal line.
- **Postconditions:** Two pop-out windows exist (X and Y), each resizable and draggable to another monitor.
  The Y pop-out shows the new zone and alarm line within the same event-loop pass; the X pop-out shows the new
  horizontal line. All windows tick in real time. Pop-outs offer no drawing tools, no alarm placement, no
  timeframe/mode/study controls — the main chart is the sole editor.
- **Edge Cases:** 11th pop-out refused with a message; pop-out with no symbol loaded (ignored + message); same
  ticker popped out 3× (one session, one subscription); pop-out while disconnected (cached bars + "connecting"
  indicator, subscription starts on connect); main chart showing the same ticker as a pop-out (all stay in
  sync); closing a pop-out (slot freed, session torn down only if no views and no live alarms remain); app quit
  with pop-outs open (all close with the main window).

**[NEW v1.2]**
### Journey 30 — D25: an alarm fires for a ticker with no chart open
- **Preconditions:** IBKR connected; no chart open on X; one live (active, untriggered) price alarm set on X
  (e.g. `cross_above 150.00`); the main chart shows ticker Y.
- **Steps:** 1) Note the app holds exactly one realtime-bar subscription for X (headless monitoring at 1-minute
  granularity). 2) Drive X's price through 150.00 (or wait for the market to do it). 3) Observe the alarm
  toast + sound from the main window — exactly once. 4) Delete the alarm.
- **Postconditions:** The alarm fired even though no X chart was visible; `AlarmStore` shows it triggered;
  after deletion the headless X session tears down (subscription cancelled); Y's chart was never disturbed.
- **Edge Cases:** alarm added while disconnected (monitored on next connect); price already beyond the alarm
  level when monitoring starts (no phantom trigger — only genuine subsequent crosses fire); alarm re-armed
  (re-enters monitoring); more alarmed tickers than the pacing budget allows (most-recently-active win, warning
  names the unmonitored ones).

**[NEW 2026-10-13]**
### Journey 31 — D36: footprint charts (bid×ask volume-at-price)
- **Preconditions:** IBKR connected; the main chart shows ticker X (e.g. `ES` front-month, 5m); footprint is
  OFF by default (owner decision 2026-10-13).
- **Steps:** 1) Enable footprint from the chart's footprint toggle. 2) The chart shows per-level bid×ask
  volume bars beside each candle (**classic** mode) once the bounded backfill completes (≤60 requests/wave,
  viewport-newest-first; bars still loading show a "loading" state, never block the chart). 3) Switch the
  display toggle to **heatmap** — the candles shade by per-level volume. 4) In heatmap mode, switch the
  metric selector to **tick count** — shading now reflects per-level trade count from the same tick pages.
  5) Switch the timeframe to Daily — footprint recomputes for daily bars. 6) Load `SPX` — footprint renders
  from the ES front-month tape and is labelled as such; the cache key uses the resolved contract (`ESZ6`).
- **Postconditions:** Classic mode renders bid/ask volume per level; heatmap-volume renders the same numbers
  shaded; heatmap-count renders per-level trade count. Completed bars are static (no per-tick regen —
  AC-D28.4 discipline holds); the forming bar updates incrementally. Cached symbols (SPX/SPY/QQQ/ES-front/
  NQ-front) reload with zero IBKR requests; other symbols re-fetch per session.
- **Edge Cases:** symbol with no tick history → clear "no tick data" state (never an empty chart); pacing
  exhaustion mid-backfill (defer via `PacingExceeded` + singleShot, "loading" persists); timeframe change
  (recompute, no stale levels); disconnect mid-wave (wave state resets, no zombie); bar completing with zero
  levels → "unavailable" state (never stuck "loading"); daily rollover (cache keys are per resolved contract,
  old entries untouched).
- **As-built note:** the planned `reqHistogramData` path was removed — the method takes no date parameter
  and cannot address individual bars. Tick count comes from the same TRADES tick pages as volume (one
  dataset, two metrics). `AC-D36.1`–`AC-D36.5` verified; 927 tests green; Code Reviewer APPROVED 2026-10-13.

### Journey 32 — D37: depth heatmap + auction imbalance
- **Preconditions:** IBKR connected; the main chart shows ticker X (e.g. `SPY`, 5m); the user holds a
  depth subscription (e.g. NASDAQ TotalView) for the full heatmap — otherwise the 354 path applies.
- **Steps:** 1) The depth heatmap renders as a price-aligned overlay strip at the chart's right edge
  (Bookmap-style: rows = price levels, columns = time buckets, intensity = size), updating on every
  depth op. 2) The headline label shows book imbalance `(bidVol−askVol)/(bidVol+askVol)` over the **top-5**
  levels; click the label to toggle to **top-10** (both are recomputed on every op). 3) The auction chip
  in the chart header shows imbalance side + paired shares + indicative price from ticks 34/35/36
  (tick 61 regulatory imbalance when present); the chip highlights during 9:25–9:35 / 15:55–16:05 ET;
  click it to expand a popover with the raw values. 4) Without a depth subscription, the panel shows a
  clear "Depth subscription required" state and the status bar shows `Depth [354]: <server message>`.
  5) Approach the 100-line market-data cap — a warning names the symbols that would exceed it; depth
  feeds stay within the 3–60 simultaneous budget or a status-bar warning names the symbols without depth.
- **Postconditions:** Heatmap rows align to the price axis; imbalance is sign-correct for both N=5 and
  N=10; auction chip shows explicit "no auction data" when ticks are absent; the S0 generic-tick union
  ("225"+"292"+"456") rides the single per-symbol subscription — one IBKR subscription per symbol is
  preserved; depth replays on reconnect via the D27 path.
- **Edge Cases:** depth requested without entitlement (354 → explicit state, feed cancelled, never
  silently empty); depth budget exceeded (warning names symbols); MD-line cap approached/exceeded
  (warning/refusal names the symbol); auction ticks outside auction windows; reconnect mid-session
  (depth replays); MPID vs exchange rows in SMART depth (disambiguated via `isSmartDepth`); symbol
  with no views (feed lives only while `views > 0` — no headless depth).
- **As-built note:** `AC-D37.1`–`AC-D37.5` verified; 947 tests green; Code Reviewer APPROVED 2026-10-13
  (no blocking findings). Drive-by fix: latent `primary_session` bug (26 references, never defined)
  fixed with a backed property. **Owner-confirmed 2026-10-14 (Q44): the depth heatmap defaults ON**
  (`ui/chart_panel.py::ChartPanel.__init__` adds `DepthHeatmapItem` unconditionally; `_depth_enabled_ui = True` — `ui/chart_panel.py:370`, indicative),
  overriding the reviewer's OFF suggestion. Known limitation: delayed-depth-instead-of-354 would render
  unlabeled (recorded in code; follow-up if ever observed).

### Journey 33 — D38: event markers + news-for-holdings digest
- **Preconditions:** IBKR connected; the main chart shows ticker X (e.g. `AAPL`, 1m); the user holds
  positions (for the digest); the user has an API news subscription for the full digest — otherwise
  the 354-style honesty applies to news; `yfinance==1.7.0` installed (the sole secondary source).
- **Steps:** 1) Earnings/dividend/split events for the charted symbol render as markers on the time
  axis with distinct icon/color per type — earnings gold ◆E, dividend green ●D, split blue ▲S — and
  a countdown label ("Earnings in 3d") shows for the next upcoming event. 2) Source priority is
  **IBKR tick-59 dividends first** (live, free, from generic tick `"456"` on the symbol's existing
  subscription), yfinance for earnings/splits and as dividend fallback (IBKR-first merge drops
  same-date yfinance dividends); futures are skipped for dividends. 3) Open the digest via
  `View → News Digest` (`Ctrl+Shift+N`) — a repositionable, closable dock listing recent headlines
  grouped by currently held position; click a headline to fetch the article body
  (`reqNewsArticle`). 4) The digest backfills on open, then prepends headlines live (tick `"292"`
  push via S0 is primary), with a 15-min periodic re-query as backstop while the digest is open;
  non-charted holdings get lightweight headless `TickerSession`s while the digest is open, torn
  down on close (their S0 lines count in the MD-line budget).
- **Postconditions:** Three synthetic events (one earnings, one dividend, one split) → three
  distinctly-styled markers at the correct dates + countdown to the next; 2 holdings + synthetic
  headlines → digest groups headlines under each holding; headline click → article body fetched;
  headline fetches are sequential (one symbol at a time — no storm on digest open); the S0
  generic-tick union is `"225,292,456"` on the single per-symbol subscription — one IBKR
  subscription per symbol is preserved.
- **Edge Cases:** no API news subscription → explicit "No API news subscription" state (never
  silently empty); zero positions → empty state; yfinance outage/rate-limit → explicit "event
  data unavailable" state, chart unaffected (cached data served if fresh); event date corrections
  → marker moves (keyed by event id, not date); symbol with no upcoming events (countdown hidden);
  per-symbol headline fetch failure (others still show); both sources empty → explicit "no event
  data" state, logged for the owner — the owner decides on feature removal; no third source is
  ever added silently (yfinance is the sole secondary source).
- **As-built note:** `AC-D38.1`–`AC-D38.6` verified; 970 tests green (947 pre-existing + 23 new
  `tests/test_d38_events_news.py`); Code Reviewer APPROVED 2026-10-13 (no blocking findings).
  Drive-bys: self-fixed duplicated `_on_auction_tick` tail; digest signal wiring deferred to first
  open (init-order fix); minimal View-only menubar added (`View → News Digest`, `Ctrl+Shift+N`).
  Reviewer advisories: A1 applied post-review (two merge tests re-pointed at the real
  `TickerSession._merge_events`); A2 harmless double `events_updated` emit noted; A3
  `get_earnings_dates(limit=12)` validated. B.6 mock-endpoint invariant PASSED; single-source rule
  PASSED (no other external API in the tree); 4 new news overrides verified arg-for-arg against
  the 10.51.1 wheel. yfinance hygiene (binding): SQLite per-symbol cache (24h TTL, 6h revalidation
  for events within 7 days), single-QThread sequential worker ≥1s between calls, own connections
  (never on the IBKR pacing budget), pinned `yfinance==1.7.0` with quarterly re-pin policy.

### Journey 34 — D39: volume-burst alerts + symbol search
- **Preconditions:** IBKR connected; the main chart shows ticker X (e.g. `SPY`, 1m); a few
  days of session-bar history exist (for the persisted baseline) or at least 5 warm-up bars
  in the current session.
- **Steps:** 1) Type "AA" in the search box in the **watchlist header** — at most ~1
  `reqMatchingSymbols` per 300ms of typing returns ≤16 samples shown as symbol·secType·exchange;
  selecting one resolves the contract and loads its chart. 2) Create a `volume_burst` alarm
  (default z-threshold 4.0, tunable ≥1.0) — it is evaluated on every aggregator push
  (forming bars evaluated conservatively, completed bars recorded) by `evaluate_volume_burst()`
  against the robust median/MAD baseline for the current ET minute-of-day over the last
  30 samples; a bar whose per-minute volume scores z ≥ threshold fires the alarm exactly once
  (toast + sound + `AlarmStore` triggered; re-arm re-enables it). 3) Alarms on indices
  (e.g. `SPX`) evaluate the **proxy tape's** bars — SPX→ES front-month via D36's `INDEX_PROXY`
  (reused, not duplicated) — and the toast is labelled proxy-derived ("Volume burst on ES
  tape (z=9.4)"); the proxy session is ensured headless, no session is created for the index
  itself. 4) Three-tier baseline: persisted `volume_baseline` table (`samples` JSON column for
  exact recomputation) → one-time local `BarCache` prime (zero IBKR requests) → rolling-30
  fallback; contract rolls invalidate the baseline (keyed on the resolved front month,
  tombstoned in-session so old rows cannot resurrect).
- **Postconditions:** "AA" → ≤16 samples, select → contract resolution + `load_chart`;
  10 keystrokes in 500ms → ≤2 `reqMatchingSymbols` calls; synthetic skewed volume then a
  z≈6 bar → burst fires exactly once; flat data never fires; fired → store shows triggered,
  re-arm works, headless monitored set includes it; 5-bar warm-up shows "warming up (n/5)";
  volume <1.0/min → no evaluation; flat baseline → z=0, real bursts fire finite (no infinity).
- **Edge Cases:** search with no matches → clear state; search while disconnected → disabled +
  message; z-threshold below 1.0 rejected (fires on normal variance); illiquid symbol
  (baseline near zero) → 1.0/min floor applies, no dust triggers; session open (<5 bars) →
  no evaluation, documented warm-up; contract roll → baseline invalidated, new contract starts
  fresh; **no company name in search results** (10.51.1's `ContractDescription` carries only
  `contract` + `derivativeSecTypes` — reviewer-verified API limitation; details resolve on
  selection).
- **As-built note:** `AC-D39.1`–`AC-D39.5` verified; 1009 tests green (970 pre-existing + 39 new
  `tests/test_d39_burst_search.py`); Code Reviewer APPROVED 2026-10-13 (no blocking findings).
  Drive-by: `evaluate_alarms` kind-filtering (a price=0.0 burst alarm can never fire as a price
  alarm — genuine pre-fix bug). Reviewer advisories applied post-review: A1 z-threshold floor
  0.5→1.0 in both alarm dialogs + tooltip caution; A2 tombstone symmetry guard in `record()`.
  B.6 mock-endpoint invariant PASSED; `symbolSamples` verified arg-for-arg against the 10.51.1
  wheel. Search box: expanding, capped 180px, zero minimum width (a 110px minimum broke D17
  dock tests). Two load flakes in reviewer runs (`test_attach_live_feed_defers_with_status_and_retries`,
  `test_smoke_gate_three_popouts`) — pass in isolation, not regressions.

### Journey 35 — D40: TWS daily-lifecycle pause/resume
- **Preconditions:** TWS connected; one or more symbols have live alarms (headless or charted).
- **Steps:** 1) Close TWS (nightly shutdown): the client classifies the disconnect as
  TWS-gone (via `connectionClosed`, per ibapi's own docstring) and `AlarmMonitor.pause_all()`
  marks every alarmed symbol paused — per-symbol pause-start recorded, evaluation gated off
  (no triggers, no phantoms). The connection badge shows **"Monitoring paused — TWS disconnected"**
  in amber `#fbbf24`, never green. The backoff reconnect loop keeps a gentle ~1 attempt/16s
  overnight; error 502 during the pause logs at debug (no status-bar spam). 2) Morning: log
  into TWS — the app detects TWS back and reconnects **without an app restart**; the D27 replay
  re-issues subscriptions, then `reconcile()`, then `resume_all()`: pause flags clear,
  `prev_price` re-seeds to None per session (AC-D25.3 first-tick-no-eval guard — resume alone
  fires nothing), staged subscribes finish, and the status bar reports the per-symbol gap
  (e.g. "ES, NQ unmonitored 22:14–09:40"). 3) A transient drop (poll-driven / 1100/1101/1102)
  takes the fast D27 path — no pause UI, no gap accounting.
- **Postconditions:** TWS-gone → badge shows the paused state and all symbols marked paused
  (asserted); reconnect after pause → subscriptions resume, a price driven through an alarm
  level fires exactly once, resume alone fires nothing; gap report names symbols + durations;
  transient drop → fast reconnect, no paused state.
- **Edge Cases:** alarms created while TWS is down are staged (`_monitor_subscribe_pending`)
  and covered on resume; a stale `TWS_GONE` classification cannot downgrade a later transient
  drop (`_last_disconnect_class` reset on connect); reconnect timer is cancel-then-armed
  (no double-arm); backfill waves in flight keep generation fencing; TWS daily auto-restart
  classifies as TWS-gone; 502 at startup with no prior connection still surfaces.
- **As-built note:** `AC-D40.1`–`AC-D40.5` verified; 1020 tests green (1009 pre-existing + 11 new
  `tests/test_d40_tws_lifecycle.py`); Code Reviewer CHANGES REQUIRED (B1: resume_all-before-reconcile
  let reconcile-created sessions take the normal path with a stale seed — phantom-trigger hole;
  fixed by the call-order swap + regression test `test_d40_2_resume_session_recreated_mid_pause_no_phantom`,
  verified fails-on-old-order / passes-on-fix) → re-check **APPROVED** 2026-10-13. Drive-by fix:
  the old code stopped polling after `connectionClosed` and scheduled nothing — the app could
  never notice a morning login without a restart (reviewer-verified real). B.6 mock-endpoint
  re-grep PASSED. One load flake in the reviewer's run (`test_place_order_defers_when_limiter_empty`,
  wall-clock timing — order path untouched) — passes in isolation, not a regression.


## Acceptance Criteria (feature-level)

### Global (applies to every defect in this run)
- **Given** the repository at its current state,
  **when** all registered defect fixes are applied,
  **then** every defect's per-task test condition passes **and** the pre-existing
  test suite remains green.
- **Given** a change touching the live-order path,
  **when** tests are run,
  **then** no test connects to live TWS or transmits an order.
- **AC-G.1 (Visual reference gate — ESC-004)** Given a defect whose fix depends on a
  **UI-visual** decision (icon shape, placement, colour, dialog layout/tab content,
  label position, size), **when** the decision is considered clarified, **then** the
  Defect Register entry MUST carry a `Visual reference:` line naming a concrete
  artifact (screenshot/video/annotated mock, with a path or attachment reference) and
  that reference MUST be marked **confirmed by the user** *before* the fix enters
  implementation.
  - A prose-only description, or a reference the user has not confirmed, does **not**
    satisfy the gate; the decision stays open and must be logged in
    `open_questions.md` (do not mark the entry "clarified").
  - If no reference can be provided, the entry MUST instead state, in the
    Assumptions Log, that the decision is a **provisional assumption** and record the
    user as the confirmer with a date — and the fix may proceed only on that explicit
    basis.
  - **Applies now to:** D10 (volume toggle icon + placement), D12 (zone `Rectangle`
    dialog), D15 (horizontal line dialog), D2 (crosshair chip appearance/lane placement),
    and any future UI-visual defect. See Assumptions Log A21–A26 for the per-defect
    reference status of this run.
  - **Per-defect status 2026-09-27 (all confirmed):** D12 `CONFIRMED` (screenshots
    supplied/confirmed 2026-09-19); D15 `CONFIRMED` (screenshots supplied/confirmed
    2026-09-20); **D10 `CONFIRMED`** — icon/affordance is the text label `Volume` (Q31) and
    the placement at the **top left of the volume panel (bottom left of the price chart)**
    was confirmed by the user 2026-09-27 (A23); **D2 `CONFIRMED`** for appearance and lane
    placement (A25, 2026-09-27) with a scoped carve-out — **dock-open visibility** is **not**
    covered by the reference and remains a separately verified acceptance criterion
    (`AC-D2.1`) + edge case requiring independent Code Reviewer verification after Build.
    Every UI-visual decision for this run is now confirmed.

### Per-defect criteria
Defects D1–D3 (Batch 1, built), D4–D8 (Batches 2–4, all confirmed 2026-09-19), D9–D11 (Batches 5–6), D12 (Batch 7), D13–D15 (Batches 8–9) and **D16 (Batch 10, 2026-10-02, clarified — Q37–Q39 answered)** each carry their own Given/When/Then criteria and documented edge cases in the **Defect Register** below. Those criteria are the authoritative acceptance tests and are the "test conditions" referenced throughout.

## Defect Register

> Batch 1 (built): three defects reported 2026-09-19 (D1–D3), all clarified and
> built. Batch 2 (clarified 2026-09-19): three refinements confirmed — D4 zoom
> label 21px/position left of axis, D5 volume log lower 1.0 (**SUPERSEDED by D8**),
> D6 wick 1px vs body ≥4×. Batch 3 (clarified 2026-09-19): D7 time-axis 35% gap. Batch 4 (clarified
> 2026-09-19): D8 volume linear, no negatives, dynamic nice ticks, price-coloured.
> Batch 5 (clarified 2026-09-19): D9 volume spacing follow + D10 volume show/hide at
> top left of volume panel. Batch 6 (clarified 2026-09-19): D11 drawing price labels
> on inner right side. Batch 7 (clarified 2026-09-19): D12 zone double-click settings popup (Extend omitted). Batch 8 (clarified 2026-09-20): D13 watchlist resizable to 50% with persistence + D14 double-click row to load chart (identical to Load Chart, no-op on same symbol/disconnected). Batch 9 (clarified 2026-09-20): D15 horizontal line double-click settings popup. Batch 10 (clarified 2026-10-02): D16 historical-bar cache-gap backfill (Q37–Q39; ESC-023 calendar correction). **Batch 11 (D17 + D18, panel layout / resizing in full screen) — CLARIFIED AND FINALISED 2026-10-03 (B1–B4 answered 2026-10-03):** D17 watchlist drag both directions up to **50% of the chart area** (min 150px, default ~220px, persisted, cap enforced during the drag); D18 one right-dock region (Active Trader + Portfolio stacked) up to **40% of the chart area**, equal width by construction, full-screen visible; combined under the **independent-caps + ~400px chart-minimum** rule (B3). See D13/D17/D18, `AC-D13.1`, `AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`, A34–A36, R28–R31, and `open_questions.md` B1–B4 (answered). D17 supersedes/corrects D13's Q25 denominator (B1). **Batch 11 had no blocking question remaining.** **New (2026-10-05): Batch 13 (D19)** — CLARIFIED AND FINALISED 2026-10-05 (B5–B6 answered): the D17/D18 fix was not effective in the real (toolbar-visible) app because the toolbar pinned the central widget; the fix wraps the toolbar in a **horizontal scroll / elide** container in place (B5, one ~36px row) and keeps the watchlist cap at **50% of the chart area** (B6). See `open_questions.md` B5–B6 (answered); this batch is **ready for Plan**. **New (2026-10-06): Batch 14 (D20)** — CLARIFIED AND FINALISED 2026-10-06 (B7–B8 answered): the D19 wrapper's horizontal scrollbar clipped the toolbar label descenders; the fix keeps the content row **~36px** with the scrollbar in its **own reserved lane below** (total strip **~50–52px**), superseding `AC-D19.4`'s `<= ~40px` bound, with the scrollbar **as-needed** in that lane. See `open_questions.md` B7–B8 (answered); this batch is **ready for Plan**.

> **New (2026-10-06): Batch 15 (D21)** — CLARIFIED AND FINALISED 2026-10-06 (B9–B13 answered): the user's 13 UI
> defects/issues (D21.1–D21.13) are finalised with the `VIS-D21` shared visual conventions (A41/A42 confirmed),
> the `AC-D16.3` display supersession (D21.4), the volume-axis rules (D21.1 min 0; D21.2 `1.10 × max visible` on
> zoom; D21.6 ≥360px with a ~200px price-pane minimum), the watchlist column popup/persistence (D21.5), the
> label→button + collapsed geometry (D21.11/D21.13), and the alarm edit/preview lifecycle (D21.9/D21.10). See
> `open_questions.md` B9–B13 (answered); **this batch is ready for Plan** and `requirements.md` carries
> `Status: READY_FOR_PLAN`.

> **New (2026-10-07): Batch 16 (D22)** — CLARIFIED AND FINALISED 2026-10-07 (B14–B16, incl. B15a/B15b/B16b,
> answered): an in-app **add + remove** affordance for the watchlist. The `+` button on the watchlist header strip
> plus a right-click "Add symbol…"/"Remove symbol"; a **small modal input dialog**; **live IBKR contract validation**
> before add (reject unresolved, nothing persisted); **adding disallowed while disconnected**; persistence across
> restarts via the SQLite `watchlist` table. See D22, Journey 27, `AC-D22.1`–`AC-D22.9`, A48–A52, R45–R48, and
> `open_questions.md` B14–B16 (answered); **this batch is ready for Plan** and `requirements.md` carries
> `Status: READY_FOR_PLAN`.


### D1 — No RTH / ETH session shading on chart
- **Area:** Chart panel (price plot)
- **Status:** clarified — criteria defined 2026-09-19
- **Reported:** Chart background does not shade the different trading sessions —
  pre-market, regular hours (RTH), post-market (ETH) are not visually distinct.
- **Observed in code:** no session-shading items exist in `chart_panel.py`. There
  *is* an "Ext Hours" toggle (`main_window.py`) controlling whether pre/post data
  is fetched, and `_custom_date_axis` handles the Eastern-time DST offset.

**Decisions (2026-09-19):**
- Sessions: Pre `04:00–09:30 ET`, RTH `09:30–16:00 ET`, Post `16:00–20:00 ET`,
  overnight `20:00–04:00 ET` unshaded. US Eastern, DST-aware.
- Bands are full-height behind candles. RTH is left at default (no band).
  Pre = **orange at 10% opacity**; Post = **blue at 10% opacity**.
- Render only when **Ext Hours** is ON and only on intraday timeframes:
  `1 min, 5 mins, 15 mins, 1 hour, 4 hours`. Not on `1 day`.
- All symbols use equity ET sessions (accepted default, incl. futures caveat).

**Acceptance Criteria (Given/When/Then):**
- **AC-D1.1** Given Ext Hours ON and an intraday timeframe, When the chart
  renders, Then pre-market is orange @10% and post-market is blue @10%, RTH and
  overnight are unshaded.
- **AC-D1.2** Given Ext Hours OFF, When the chart renders, Then no pre/post bands.
- **AC-D1.3** Given timeframe `1 day`, When the chart renders, Then no session bands.
- **AC-D1.4** Given chart timezone is `UTC`, Then bands stay pinned to the actual
  ET session instants (e.g. 13:30–20:00 UTC during EST), not fixed wall-clock hours.

**Edge Cases:**
- DST transition days (2nd Sun Mar / 1st Sun Nov) keep boundaries at ET local time.
- A bar at exactly `09:30 ET` counts as RTH; at exactly `16:00 ET` counts as post-market.
- No bands painted outside the loaded data range.
- Toggling Ext Hours / changing timeframe or symbol removes stale bands and redraws.

### D2 — Crosshair price label decimals covered by right-side panels
- **Area:** Chart panel → price-axis lane / Active Trader / Portfolio dock
- **Status:** clarified — criteria defined 2026-09-19; **placement + styling revised
  2026-09-27 (Q33 — see below)**. This revision **re-opens** the original D2 defect
  surface ("decimals covered by the element to its right"), so it MUST be independently
  re-verified by the Code Reviewer after Build — the Batch-1 fix cannot be assumed to
  still hold.
- **Visual reference (ESC-004 gate):** **CONFIRMED (2026-09-27).** The reference is the
  agreed target for D2's **appearance and lane placement** — the Y-axis lane to the right
  of the plot's vertical axis line, a **grey pill**, **white text**, and axis-tick-label
  overlap permitted. **NOT covered by this reference/confirmation:** **dock-open
  visibility** — the chip must not be hidden by the Active Trader / Portfolio dock. That
  remains a **separately verified acceptance criterion** (`AC-D2.1`) and an edge case, and
  because it re-opens the original D2 defect surface it requires **independent Code
  Reviewer verification after Build**. Gate status: **CONFIRMED for appearance/lane
  placement only** (see A25).
- **Reported:** the crosshair price label's decimal places are hidden behind the
  element to its right (the Active Trader / Portfolio panels).
- **Observed in code:** `ChartPanel._price_tag` is a scene `TextItem`; the Batch-1 fix
  right-aligned it **inside** the plot at `view_rect.right() - 2` with a `#94a3b8` fill
  and dark `#0d0f14` text. `anchor=(0, 0.5)` originally; right-aligned to `anchor=(1,
  0.5)` in the fix.

**Decisions (2026-09-19; placement + styling revised 2026-09-27 — Q33):**
- The chip renders to the **RIGHT of the plot's vertical axis line, in the Y-axis lane**
  (the same strip where the Y-axis price tick labels are printed). It is therefore
  **OUTSIDE the data area** — the opposite of the Batch-1 decision, which placed it
  **INSIDE** the plot at `view_rect.right() - 2`.
- **Style:** a **grey background pill with WHITE text** (replacing the current
  `#94a3b8` fill with dark `#0d0f14` text).
- **Axis-tick-label overlap is EXPECTED and REQUIRED:** the chip MAY paint over the
  Y-axis price tick label at the same price. No separation between the chip and the
  Y-axis tick label is required — do **not** add a deconfliction offset between them.
- **Dock-open visibility is a required acceptance criterion:** with the Active Trader
  and/or Portfolio dock open, the chip must **not** be covered by the dock. Because this
  re-opens the original D2 defect surface, it is an edge case that requires independent
  Code Reviewer verification (the Batch-1 inside-plot fix no longer applies).

**Acceptance Criteria (Given/When/Then):**
- **AC-D2.1** Given a loaded symbol and the cursor inside the price plot, When the
  price chip renders with the Active Trader and/or Portfolio dock open, Then the
  complete label including all decimals is visible as a **grey pill with white text
  positioned in the Y-axis lane to the right of the plot's vertical axis line**, and is
  **not covered by the dock**. Painting over a Y-axis price tick label at the same price
  is permitted and is **not** a failure.
- **AC-D2.2** Given pan or zoom, Then the chip stays in the Y-axis lane and continues
  to track the cursor's price; it is not covered by the right dock.
- **AC-D2.3** Given the cursor leaves the plot, Then the chip is hidden (existing
  behaviour retained).

**Edge Cases:**
- Long price strings (e.g. `123,456.78`) must not bleed under the dock while remaining
  in the axis lane.
- **Dock-open edge case (re-opened D2 — requires independent Code Reviewer
  verification):** with the dock open/expanded, the chip's full decimals stay visible —
  the chip is not covered by the dock, even though it now sits outside the plot.
- A Y-axis tick label at the same price is expected to be overlapped by the chip — this
  is by design, not a defect.
- Cursor near the top/bottom of the view keeps the chip vertically in-view.
- Dock closed, floating, or hidden still renders the chip correctly.
- Small window widths / narrow plot do not clip the label.

### D3 — Missing zoom controls and area-zoom magnifier
- **Area:** Chart panel / toolbar
- **Status:** clarified — criteria defined 2026-09-19
- **Reported:** zoom tools are missing — a `+` and `−`, plus a magnifying glass
  that lets the user select a rectangular area which then expands to fill the
  chart.
- **Observed in code:** no zoom buttons exist; the toolbar has symbol/TF/mode/
  studies/alarms/DOM/ext-hours/timezone/drawing controls only. pyqtgraph's default
  ViewBox wheel-zoom and drag-pan still function.

**Decisions (2026-09-19):**
- Controls sit **top-right of the chart area** inside a visible **outlined
  container** (neat border): `−`, `+`, magnifier, reset.
- Magnifier: activate → crosshair cursor → click-drag a rectangle → on release the
  view sets **both x and y range** to that rectangle (selection expands to fill the
  chart). `Esc` or right-click cancels. **Magnifier stays active** after one zoom.
- `+`/`−` zoom around the **chart centre**. **Reset** button restores the default
  framing.

**ESC-002 transition semantics (magnifier ↔ drawing tool ↔ alarm) — decided/confirmed 2026-09-27 (Q35 + follow-up confirmations):**
- **Forward direction — CONFIRMED (Q35 option (a)):** invoking the magnifier while a
  drawing tool is active **cancels the in-progress drawing and enters `ZOOMING`**. The
  active drawing tool / in-progress draft is cleared and **discarded** — **no half-drawn
  artefact is left behind** (the draft is not silently committed). `ZOOMING` and
  `DRAWING` are therefore mutually exclusive router modes, and the explicit
  `RouterMode` state machine (`IDLE/DRAWING/ZOOMING/ALARM_PLACING`) with a single
  `_active_mode` encodes this as a requirement (`AC-D3.7`, forward).
- **Reverse direction — CONFIRMED 2026-09-27 (was provisional A26):** selecting a
  drawing tool while `ZOOMING` is active **exits `ZOOMING` and activates the drawing
  tool**. This mirrors the forward rule (one precedence rule both ways) and the existing
  precedent that alarm mode forces the draw tool back to `Cursor`. It is now a
  **requirement** (folded into `AC-D3.7`, reverse), **not** an assumption; Plan MUST
  encode it in the router transition table as required behaviour.
- **Alarm-mode activation cancels `ZOOMING` — CONFIRMED (decided 2026-09-27):** when alarm
  placement mode is activated while the router is in `ZOOMING`, the app **exits `ZOOMING`
  and enters alarm placement**. This supplies the expected behaviour for the named test
  `test_alarm_placement_blocks_zoom` — alarm placement **blocks/ends** an active zoom
  rather than being blocked **by** it. Recorded as `AC-D3.8`.
- **Magnifier invoked while `ALARM_PLACING` is active — REFUSE (Q36 option (b), answered
  2026-09-27):** invoking the magnifier while alarm placement mode is active does **NOT**
  enter `ZOOMING`. The router **stays in `ALARM_PLACING`**, alarm placement keeps priority,
  the pending alarm placement is **not cancelled**, and a **status-bar hint** is shown
  (e.g. "Finish or cancel alarm placement before zooming"). Recorded as **`AC-D3.9`**. This
  is the final cell required to make the `chart_mouse_router` **transition table total**
  (`ALARM_PLACING + magnifier → ALARM_PLACING`, no mode change) and is **REQUIRED
  behaviour** — it supersedes Plan's derived transition **TR-9** and assumption **PA-R1**
  (RG-003, now closed).

**Acceptance Criteria (Given/When/Then):**
- **AC-D3.1** Given a loaded chart, When `+` is clicked, Then the view zooms in
  around the centre; `−` zooms out around the centre.
- **AC-D3.2** Given magnifier mode is active, When the user drags a rectangle and
  releases, Then the view sets x and y range to that rectangle so it fills the
  chart.
- **AC-D3.3** Given magnifier mode, When `Esc` or right-click occurs before
  release, Then the selection is cancelled and the view is unchanged.
- **AC-D3.4** Given one completed magnifier zoom, Then magnifier mode remains
  active for another selection.
- **AC-D3.5** Given Reset is clicked, Then the view returns to the default framing
  equivalent to a fresh chart load (price x/y and volume Y refit).
- **AC-D3.6** Then the zoom control cluster is rendered top-right of the chart
  area inside a visible outline.
- **AC-D3.7 (ESC-002 — both directions, confirmed 2026-09-27)** Given a drawing tool and
  the zoom magnifier can both be activated, When a transition between them occurs, Then
  drawing and zoom are **never simultaneously active**:
  - **Forward (Q35 option (a)):** Given a drawing tool is active with an in-progress
    draft, When the magnifier is invoked, Then the drawing tool is cleared, the
    in-progress draft is discarded with **no half-drawn artefact left behind**, and the
    router enters `ZOOMING`.
  - **Reverse (A26 — now CONFIRMED; was provisional):** Given the router is in `ZOOMING`,
    When a drawing tool is selected, Then the router **exits `ZOOMING`** and activates the
    drawing tool. (Measurable: after selecting the tool, `_active_mode == DRAWING` and no
    zoom-selection gesture is active.)
- **AC-D3.8 (ESC-002 — alarm placement cancels `ZOOMING`; decided 2026-09-27)** Given the
  router is in `ZOOMING`, When alarm placement mode is activated, Then the router **exits
  `ZOOMING`** and enters **alarm placement**, and alarm placement is **not** blocked or
  deferred by the active zoom. (Measurable: after activating alarm placement,
  `_active_mode == ALARM_PLACING`; the named test `test_alarm_placement_blocks_zoom`
  encodes that alarm placement **blocks/ends** zoom rather than being blocked **by** it.)
- **AC-D3.9 (ESC-002 — magnifier is refused during alarm placement; Q36 option (b),
  answered 2026-09-27)** Given alarm placement mode is active (`_active_mode ==
  ALARM_PLACING`), When the magnifier is invoked, Then the router **stays in
  `ALARM_PLACING`**, it does **NOT** enter `ZOOMING`, the pending alarm placement is
  **not cancelled**, and a **status-bar hint** is shown. (Measurable: after the magnifier
  is invoked, `_active_mode == ALARM_PLACING`, no zoom-selection gesture is active, the
  pending alarm placement is unchanged, and the status bar displays the hint.) This is the
  cell that makes the ESC-002 router transition table **total** — the
  **`ALARM_PLACING → ZOOMING`** cell is **specified required behaviour**
  (`ALARM_PLACING + magnifier → ALARM_PLACING`), superseding Plan's derived **TR-9** /
  assumption **PA-R1**.

**Edge Cases:**
- Degenerate selection (near-zero width/height) → ignored, no zoom.
- Drag starting outside the plot → no selection.
- No bars loaded → controls are disabled / no-op.
- Zoom at range limits → clamped, app remains stable.
- Changing symbol/timeframe while magnifier is active resets mode to default cursor.
- Activating the magnifier while a drawing tool is active **cancels the in-progress
  drawing** (the draft is discarded, no half-drawn artefact is left behind) and enters
  `ZOOMING` — Q35 option (a); selecting a drawing tool while the magnifier is active
  **exits `ZOOMING` and activates the tool** — **CONFIRMED 2026-09-27** (A26; `AC-D3.7`
  reverse). Both rules keep `DRAWING` and `ZOOMING` mutually exclusive.
- Activating alarm placement mode while `ZOOMING` is active **exits `ZOOMING`** and enters
  alarm placement (decided 2026-09-27, `AC-D3.8`) — alarm placement is never blocked by an
  active zoom (`test_alarm_placement_blocks_zoom`).
- Invoking the magnifier while `ALARM_PLACING` is active **does not enter `ZOOMING`** — the
  router stays in `ALARM_PLACING`, keeps the pending alarm placement, and shows a
  status-bar hint (Q36 option (b), answered 2026-09-27; `AC-D3.9`). This makes the ESC-002
  transition table total.
- Reset also refits the linked volume (and oscillator) panes consistently.

### D4 — Zoom control cluster refinement: glyphs too small and outline clipped outside chart area
- **Area:** Chart panel / `ui/chart_controls.py`, `ui/chart_panel.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q15 (magnifier +50%) and Q16 (current fine) confirmed
- **Reported:** Post-build UI feedback with screenshot 2026-09-19: zoom tools looked too
  small — button size was enough but the `-` / `+` / `⌕` glyphs and `Reset` label were
  too small; and the toolbox outline was slightly outside the chart area (the `Reset`
  border was clipped at the window/axis edge).
- **Observed in code at time of report:** `ChartControls` buttons used default 11px;
  `ChartPanel.resizeEvent` positioned the cluster at `panel.width - width - 10`,
  which placed it over the price axis rather than fully inside the data area.

**Decisions confirmed 2026-09-19 (Q15 with magnifier +50%, Q16 current fine):**
- `-` / `+` / `Reset` at **14px / 700**, `⌕` (magnifier) at **21px / 700** (14px × 1.5),
  button size remains 28×24; only the glyphs scale.
- Cluster positioned **fully inside the data area, left of the price axis**: `x =
  panel.width - ctrl.width - axis_width - 12` where `axis_width` is the right price
  axis width (fallback 50). Top offset remains `10px` (confirmed fine).

**Acceptance Criteria (Given/When/Then):**
- **AC-D4.1** Given any loaded chart, When the zoom cluster renders, Then `-` / `+`
  / `Reset` are at 14px / 700 and `⌕` is at 21px / 700.
- **AC-D4.2** Given any window size, When the cluster renders, Then its right edge
  is left of the price axis (`ctrl.right() <= panel.width() - axis_width`) and fully
  inside the panel (`ctrl.right() <= panel.width()`), with `y <= 15`.

**Edge Cases:**
- Narrow window or large axis width (e.g., 5-digit prices) keeps the cluster from
  overlapping the axis or being clipped; `x` is clamped to `>= 8`.
- Magnifier remains checkable; button signals unchanged.

### D5 — Volume panel Y axis is linear and compresses small volumes
- **Area:** Chart panel volume plot / `ui/chart_panel.py`
- **Status:** **SUPERSEDED BY D8** (2026-09-19) — originally clarified 2026-09-19 with Q17 (log lower bound 1.0) confirmed; retained for history only.
- **Authoritative decision:** D8 (below) revises this defect to a **linear** Y axis with
  `yRange=(0, nice_max)` and bars coloured by price direction. **Do not implement D5 as
  written.** The details below are the superseded log proposal and are kept solely to
  record why it was changed; no criterion in this section is a live test condition.
- **Reported:** Volume panel linear Y makes small volumes invisible when a spike is
  present (see screenshot: spike at 16:00 dominates; 3e7 scale). User requested
  logarithmic Y.
- **Observed in code at time of report:** `volume_plot.getViewBox()` used linear mode
  (`yRange 0.0 .. max*1.1`) and `vol_h` used raw volume including `0`.

**Decisions confirmed 2026-09-19 (Q17) — SUPERSEDED by D8/Q20; do not implement:**
- Volume `ViewBox` is **always log on Y** (`setLogMode(y=True)`), X remains linear
  and linked to the price plot.
- Zero-volume bars mapped to **`1.0`** (minimal tick, not a gap) — confirmed lower
  bound `1.0`.
- Auto-range is **`yRange=(1.0, max_vol*1.1)`** where `max_vol` is the maximum of
  mapped volumes.

**Acceptance Criteria (Given/When/Then) — SUPERSEDED, not live test conditions:**
- **AC-D5.1 (superseded by AC-D8.1)** Given any loaded chart with volumes, When the volume panel renders,
  Then the ViewBox is in log mode on Y (`getViewBox().logMode == (False, True)`).
- **AC-D5.2** Given bars with zero volume, When `vol_h` is computed, Then the height
  is `1.0` and the volume `yRange` lower bound is `1.0`, not `0.0`.
- **AC-D5.3** Given a max volume, When auto-ranged, Then the upper bound is
  `max_vol*1.1` and small-volume bars are visibly distinct from the spike.

**Edge Cases (superseded — see D8 edge cases for the live ones):**
- All bars have zero volume → `max_vol` floor is `1.0`; range becomes `(1.0, 1.1)`.
- Very small vs very large volumes remain distinguishable on log scale; X remains
  linked to price plot and is unaffected; Reset refits the volume pane consistently.

> **Note:** Journey 6 (above) describes the superseded log behaviour and is retained
> only for historical traceability. The live journey is Journey 9 (D8) and the live
> criteria are `AC-D8.1`–`AC-D8.7`. The Batch-2 register header and Assumption A9 are
> annotated `SUPERSEDED by D8`.

### D6 — Candlestick wick not clearly distinguishable from body
- **Area:** Chart panel / `ui/candlestick_item.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q18 confirmed
- **Reported:** Two screenshots 2026-09-19: current app’s wick is almost the same
  thickness as the body so wick vs body is indistinguishable (first screenshot, tall
  thin candles with faint wicks); reference screenshot shows a thin, clearly visible
  wick extending beyond the body (second screenshot, high-contrast wicks). User wants
  wick and body drawn clearly so the wick is visible.
- **Observed in code at time of report:** `CandlestickItem` renders body as a
  filled rectangle and wick as a line of similar thickness to the body at default
  zoom, so at typical bar counts the two are not visually distinct.

**Decisions confirmed 2026-09-19 (Q18):**
- Wick (shadow) rendered as a **thin line ~1px** centred on the candle, spanning
  `low` to `high` and drawn behind the body; body width noticeably larger (e.g.,
  ~6–8px at default zoom while wick stays 1px).
- Wick colour follows the candle direction (same as body, e.g., teal `#34d399` for
  up, pink `#f87171` for down); distinction is by **thickness**, not colour.
- At any zoom/timeframe, the wick remains visibly thinner than the body and extends
  beyond the body’s top/bottom whenever a shadow exists (`high > max(open,close)` or
  `low < min(open,close)`).

**Acceptance Criteria (Given/When/Then):**
- **AC-D6.1** Given a loaded chart with candles, When candles render at default
  zoom, Then each wick is ~1px and each body is noticeably wider (body width ≥
  4× wick width), and the wick passes behind the body.
- **AC-D6.2** Given a candle has a shadow, When rendered, Then the wick extends
  beyond the body’s top/bottom by at least 1px and is fully visible.
- **AC-D6.3** Given up vs down candles, When rendered, Then body and wick share the
  candle’s direction colour.
- **AC-D6.4 (ESC-009 — high-DPI coverage)** Given the app renders at a device pixel
  ratio of `2` (`QT_SCALE_FACTOR=2` / `devicePixelRatio == 2`), When the candles
  render, Then the wick stays a cosmetic 1-device-pixel line and the body remains
  `>= 4` device pixels wide, so wick and body do not merge. Measurable: at DPR 2, the
  body’s device-pixel width is `>= 4` and strictly greater than the wick’s, with no
  rounding collapse to a single line.

**Edge Cases:**
- Very dense bars (e.g., 1-min over multiple days, hundreds of candles) keep the
  wick thin (never thickens with the body); body may narrow but wick stays 1px.
- Doji (`open == close`) still shows a wick distinct from the body line.
- High-DPI / narrow window does not cause wick and body to merge visually.

### D7 — Time-axis candle spacing slightly too tight
- **Area:** Chart panel / `ui/candlestick_item.py` (candle width) and `ui/chart_panel.py` (xRange)
- **Status:** clarified 2026-09-19 — criteria defined, Q19 (35% gap) confirmed
- **Reported:** New screenshot 2026-09-19 shows the **current app’s** very little
  spacing between bodies (attached chart area, 09:00–18:00, dense 1-min candles with
  almost no gap). The earlier screenshot (09:15–11:30 area with wider gaps) was the
  **sample of how the user wants it to be**.
- **Observed in code at time of report:** `CandlestickItem._draw_candles` uses
  `w = median_diff * 0.4` (body is 80% of bar spacing, gap is 20% of spacing) and
  `ChartPanel._refresh_candles` frames `xRange=(t0 - 2*bar_w, t1 + 8*bar_w)` with
  `bar_w` = one bar’s time diff. Both determine the on-screen gap.

**Decisions confirmed 2026-09-19 (Q19: 35% gap):**
- Increase the inter-candle gap from **20% to ~35%** of bar spacing by reducing the
  body half-width from `0.40` to **`0.325`** of `median_diff` (full body 65% of
  spacing, gap 35% — ~75% more gap in relative terms, but still compact). No change
  to `xRange` padding (`-2*bar_w / +8*bar_w`); if a larger framing change is
  preferred it can be added as an alternative.
- The existing device-pixel minimum for the body (from D6, ≥4px) continues to apply
  so the slightly narrower body never collapses below legibility.

**Acceptance Criteria (Given/When/Then):**
- **AC-D7.1** Given a loaded chart at default zoom, When candles render, Then the
  gap between adjacent bodies is ~35% of bar spacing (body half-width is 0.325×
  `median_diff`), visibly larger than the current 20% gap.
- **AC-D7.2** Given the same data, When compared to the current rendering, Then the
  on-screen distance between bodies is larger by ~15–18% of bar spacing (the gap
  grows from 0.20 to 0.35 of spacing).

**Edge Cases:**
- Very dense 1-min view (hundreds of candles) keeps the gap proportional (35% of
  spacing) but the 4px body minimum may override — the gap remains positive and the
  chart does not become empty.
- Single-bar chart (`w = 0.25` fallback) is unchanged.
- All chart modes (Candles, Hollow, Heikin) use the same `w` factor; Line/Area are
  unaffected.

### D8 — Volume panel shows negatives, log scale not desired, bars not price-coloured
- **Area:** Chart panel volume plot / `ui/chart_panel.py`
- **Status:** clarified 2026-09-19 — criteria defined, Q20 confirmed — revises D5’s prior log decision; **criteria revised 2026-09-27** for the ESC-003/ESC-007/ESC-008 build fix (scaling nice formula, no `10k` floor, live ceiling)
- **Reported:** New volume screenshots 2026-09-19: current app shows **negative**
  ticks (e.g., `-200`) on the right axis — volume cannot be negative; and the log
  scale "looks" not desired. The desired look (second screenshot) has **no
  negatives**, a **linear** Y with ticks like `10k / 100k / 500.0K / 1.0M / 1.5M /
  2.0M / 2.5M`, a **dynamic max** based on the visible max volume, and bars
  **coloured green/red by price candle** (green `#34d399` when `close >= open`,
  red `#f87171` otherwise).
- **Observed in code at time of report:** `volume_plot.getViewBox()` was switched
  to log on Y in the prior D5 patch (`setLogMode('y', True)` with `0→1.0` floor
  and `yRange=(1, max*1.1)`); `volume_bars` were set with `height=vol` and
  `y0=1`. The current screenshot still shows a linear-looking axis with negatives,
  indicating the log change did not produce the desired look and the yRange still
  dips below zero.

**Decisions confirmed 2026-09-19 (Q20); nice-number family pinned 2026-09-27 (RG-002):**
- Volume `ViewBox` is **linear on Y** (`setLogMode(y=False)`, X stays linear/linked);
  `yRange=(0, nice_max)` where `nice_max` is `max_vol*1.1` rounded up to the next
  **nice value generated by a continuous scaling formula whose mantissa set is
  `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (`10 × 10^k` is the next decade's `1` and needs
  no separate mantissa) so the axis shows 3–5 ticks (e.g., max ~2.2M → `0, 500.0K, 1.0M,
  1.5M, 2.0M, 2.5M` as in the desired screenshot; max ~80K → `0, 25K, 50K, 75K, 100K`).
  - **RG-002 (resolved 2026-09-27):** the earlier `1 / 2 / 2.5 / 5 × 10^k` wording was
    **internally inconsistent** with this defect's own examples and the retained fixture
    — `1.5M`, `15M` and `750K` are `1.5×` and `7.5×` mantissas that the strict set
    **cannot produce**. Because **`1.5M` (the screenshot's `500.0K / 1.0M / 1.5M / 2.0M /
    2.5M` run) and `750K` are user-confirmed (Q20)**, the family is pinned to
    **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`**, which reproduces every confirmed value
    exactly. `AC-D8.1`, `AC-D8.4`, `AC-D8.5` and the D8 edge cases all use this one
    family. **Still true:** **no fixed `10k` floor** (smallest generated value `100`),
    **no fixed ceiling** (it scales as `10^k`), and the old fixed list is retained
    **only** as a regression-test fixture.
  - **Revises A12 (2026-09-27; family pinned by RG-002):** the earlier fixed list
    `[10k, 50k, 100k, 250k, 500k, 750k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]` is **no
    longer the live rule** — it is retained only as a regression-test fixture. Every
    entry in it is a member of the pinned family, so the fixture stays valid for those
    values. Its `10k` floor and its coarse rounding above 10M are corrected by the
    scaling formula (ESC-003 / ESC-008). The floor is no longer `10k`; the smallest
    generated nice value is `100` (see the low-volume edge case below).
- Volume bars are **coloured by price candle direction** (`#34d399` when `close >=
  open`, `#f87171` otherwise) — matching `CandlestickItem` bodies. This revises the
  prior log decision; no toggle is proposed — linear is the sole mode.
- Y ticks are formatted as `500.0K / 1.0M` (one decimal for K, same for M) via the
  right-axis tick formatter; no negative ticks are ever shown.

> **Fixture note (RG-002 — retained regression fixture, `tests/test_volume_linear.py`):**
> with the family pinned, the retained fixture values that are **valid and stay** are
> `_nice_volume_max(80_000) == 100_000`, `_nice_volume_max(2_200_000) == 2_500_000`,
> `_nice_volume_max(1_050_000) == 1_500_000` (the RG-002 contested case — it **is**
> correct under the pinned family), and `_nice_volume_max(8_000) == 10_000`. The only
> **stale** expectation is `_nice_volume_max(0) == 10_000`, which must become **`100`**
> per `AC-D8.4` (smallest nice value, no `10k` floor). Build owns the test edit.

**Acceptance Criteria (Given/When/Then):**
- **AC-D8.1** Given any loaded chart, When the volume panel renders, Then the Y is
  linear (`logMode == (False, False)`), lower bound is `0`, no negative tick is
  shown, and the upper bound is the dynamic nice max — the **smallest value of the
  form `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (the pinned RG-002 family) that is
  `>= max_vol*1.1`, so it reproduces the user-confirmed `750K` and `1.5M`.
- **AC-D8.2** Given volumes, When bars render, Then each bar is green when its price
  candle has `close >= open` and red otherwise, and the yRange upper covers the max
  with the nice tick above it.
- **AC-D8.3** Given a max volume, When formatted, Then ticks appear as `10k / 100k /
  500.0K / 1.0M / 1.5M` etc., with `0` at the bottom and no `-200`.
- **AC-D8.4 (ESC-008 — fine low end)** Given a low-volume symbol, When the volume
  axis is computed, Then `nice_max` uses the **smallest value of the AC-D8.1 family
  (`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`)** that is `>= max_vol*1.1`, so for any
  `max_vol > 0` the ceiling satisfies `nice_max <= max_vol*1.1 * (1 + tolerance)`
  (tight, i.e. `nice_max / (max_vol*1.1) <= 2`), and no fixed `10k` floor is applied.
  - `nice_max(800) = 1000` (not `10_000`), `nice_max(3_000) = 5000` (not `10_000`);
    an 800–3,000 share symbol fills `>= 30%` of the pane (currently `< 30%`).
  - The floor for `max_vol == 0` is the smallest nice value, **`100`** (not `10k`).
- **AC-D8.5 (ESC-003 — fine high end)** Given a very large max volume (`40M–50M`),
  When `nice_max` is computed, Then it uses the same
  **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** family (AC-D8.1) with tight coverage — the
  smallest family value `>= max_vol*1.1`. Worked examples (each verified against the
  family): `10.5M → 15M`, `45M → 50M`, and `50M → 75M` (since `50M×1.1 = 55M` and the
  next family value is `75M`). A coarser ceiling such as `100M` is **not** acceptable
  while the tighter family value `75M` exists — this is precisely why the family keeps
  the `7.5` mantissa: the strict `1/2/2.5/5` set would overshoot `50M` to `100M`. The
  result is monotonic non-decreasing in `max_vol`, and the old fixed list is retained
  **only** as a test fixture.
- **AC-D8.6 (ESC-007 — live ceiling)** Given a loaded chart, When the forming last
  bar's volume grows past the initially computed `nice_max`, Then either the ceiling is
  recomputed/widened so the bar is not clipped, or the bound is explicitly documented
  and the bar never exceeds the Y range. (Measurable: after the live max doubles, the
  forming bar's rendered height is `<=` the pane top and `> 0`.)
- **AC-D8.7 (ESC-007 — timezone/refresh)** Given `set_timezone()` or any
  `_refresh_candles()` path with `auto_range=False`, When the volume range would be
  stale, Then the volume Y range is refit consistently with `AC-D8.6`.

**Edge Cases:**
- All bars have zero volume → `max_vol` floor is the smallest nice value **`100`**
  (not `10k`); yRange becomes `(0, 100)` and bars are minimal/gaps.
- Single bar with very small max (e.g., 800) → `nice_max = 1000`; ticks
  `0, 250, 500, 750, 1000`.
- Max just below a boundary (e.g., 1.05M) rounds up to the next
  `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` value (`1.5M`), not down; a max of exactly
  `10_000` no longer jumps to `50_000` (it rounds to `15_000`).
- Very large max (40M–50M) keeps a tight ceiling and stays monotonic (e.g.,
  `45M → 50M`, `50M → 75M`).
- Volume bars remain green/red even when price is a Doji (`open==close` → green).
- A live tick that grows the forming bar past the initial ceiling must not clip the
  bar (see `AC-D8.6`).

### D9 — Volume bar spacing should follow price candle spacing
- **Area:** Chart panel volume plot / `ui/chart_panel.py` (`volume_bars` width)
- **Status:** clarified 2026-09-19 — criteria defined, Q21 correct
- **Reported:** User feedback 2026-09-19: spacing between volume candles should
  follow the spacing of the price candles. Volume bars currently use a fixed
  `width=0.6` (data units) while price bodies use `w = median_diff * 0.325`
  (Batch 3, 35% gap, full body 65% of spacing) plus a 4px minimum. The two can
  drift — volume gaps look different from price gaps.
- **Observed in code at time of report:** `volume_bars = pg.BarGraphItem(x=vol_x,
  height=vol_h, width=0.6, y0=1)` in `chart_panel.py`; price `w` is computed from
  `median_diff` and clamped to a device-pixel minimum. X remains linked
  (`setXLink`).

**Decisions confirmed 2026-09-19 (Q21 correct):**
- Volume `BarGraphItem` width is the **same `w`** as the price candles (`width =
  w*2`, full body 65% of `median_diff`), so the gap is exactly the same as the
  price panel (35%).

**Acceptance Criteria (Given/When/Then):**
- **AC-D9.1** Given a loaded chart, When volume and price render at the same
  timeframe/zoom, Then the volume bar width equals the price body width (`w*2`)
  and the inter-bar gaps are identical.
- **AC-D9.2** Given a dense 1-min view where the 4px body minimum applies, When
  rendered, Then volume bars follow the same clamped `w` so gaps stay aligned with
  price gaps.

**Edge Cases:**
- Single-bar fallback (`w=0.25`) is used for both price and volume; single volume
  bar still aligns.
- All volume bars follow the price `w`; Line/Area modes (no price bodies) still use
  the same `w` for volume.

### D10 — Volume panel show/hide toggle
- **Area:** Chart panel volume plot / `ui/chart_panel.py` — top left of volume panel (bottom left of price chart)
- **Status:** clarified 2026-09-19 — criteria defined, Q22 top left of volume panel; **updated 2026-09-27** — icon confirmed as the text label `Volume` (Q31) and **placement CONFIRMED** (A23, 2026-09-27)
- **Visual reference (ESC-004 gate):** **CONFIRMED (2026-09-27).** The **icon/affordance**
  is the **text label `Volume`** (Q31 — a checkable text-label toggle, not an eye icon or a
  bar glyph) and the **placement** — **top left of the volume panel (bottom left of the
  price chart)** — is likewise user-confirmed (A23, 2026-09-27). Gate status: **CONFIRMED**
  (see AC-G.1).
- **Reported:** User feedback 2026-09-19: allow the user to show/hide (toggle) the
  volume panel to maximize price-chart vertical space. No toggle exists today; the
  volume `PlotWidget` is always visible in the splitter.
- **Observed in code at time of report:** `volume_plot` is a `PlotWidget` in a
  vertical `QSplitter` with `price_plot` and `osc_plot`; it is always added and
  shown. No user-facing visibility control exists.

**Decisions confirmed 2026-09-19 (Q22 top left of volume panel); icon + placement confirmed 2026-09-27 (Q31, A23):**
- The toggle is a **checkable text-label control showing `Volume`** (Q31), default **visible**
  — not an eye icon or a bar glyph.
- **Placement (CONFIRMED 2026-09-27 — A23):** **top left of the volume panel** (bottom left of
  the price chart).
- Toggling hides/shows `volume_plot` (and its axis) and the `QSplitter` is rebalanced so the
  price plot expands when hidden. The toggle state is **not persisted** in this proposal
  (resets to visible on launch).

**Acceptance Criteria (Given/When/Then):**
- **AC-D10.1** Given the volume panel is visible, When the user toggles the `Volume`
  control (a checkable text label, Q31) at its **confirmed placement** (top left of the
  volume panel / bottom left of the price chart, A23 confirmed 2026-09-27), Then
  `volume_plot` becomes hidden and the price plot expands to fill the freed vertical
  space; toggling again shows it.
- **AC-D10.2** Given the app is restarted, When launched, Then the volume panel is
  visible by default (no persistence in this proposal).

**Edge Cases:**
- Toggling with no bars loaded hides/shows without error.
- Oscillator `osc_plot` visibility is independent; hiding volume does not affect it.
- Splitter sizes are restored correctly after hide/show cycles.

### D11 — Drawing price labels should be on inner right side of chart
- **Area:** Chart panel drawings / `ui/drawing_overlay.py`, `ui/overlays/*`
- **Status:** clarified 2026-09-19 — criteria defined, Q23 correct
- **Reported:** Two screenshots 2026-09-19: the app’s zones (first screenshot,
  blue/teal horizontal zones at ~332–336 with no price label on the right
  interior) vs the reference app (second screenshot, green/brown zone at
  757–764 with prices on the right interior: `757.67`, `760.63`, `762.39`,
  `764.48`, etc.). User wants for any drawing the price to be on the inner side
  of the chart (right side) — i.e., inside the plot near the right edge, not on
  the axis or left side.
- **Observed in code at time of report:** `DrawingOverlay` renders horizontal
  lines/zones with labels that are not consistently anchored to the inner right;
  some labels are outside or not visible on the right interior.

**Decisions confirmed 2026-09-19 (Q23 correct):**
- For any drawing type (horizontal line at price `y`, zone `y1`/`y2`, trendline
  `p1`/`p2`, Fibonacci level), the price label is a `TextItem` anchored **inside
  the plot** at the right edge: `anchor=(1, 0.5)`, `x = view_rect.right() - 4`,
  `y = price`, `Z=10`, with the same colour as the drawing. For zones, the top
  and bottom edges each get a label; for trendlines/Fibonacci, each level’s
  right-edge label is placed similarly.
- Labels are children of the price plot’s scene (like the crosshair chip), so they
  are never clipped by the right axis/dock and remain visible at any zoom.
- When multiple drawings share a similar price, labels stack with a small vertical
  offset to avoid overlap (or the topmost remains). **Revised 2026-09-27 (Q33 —
  ESC-006 re-scoped):** the crosshair price chip now lives in the **Y-axis lane outside
  the plot** (see D2), while D11 drawing labels remain **inside the plot at `x =
  view_rect.right() - 4`**. The two occupy **different lanes**, so the chip is **no
  longer included** in the label collision accounting; `AC-D11.4` now applies only to
  **label-vs-label stacking inside the plot**.

**Acceptance Criteria (Given/When/Then):**
- **AC-D11.1** Given any drawing with a price, When rendered, Then a price label
  is visible **inside the plot near the right edge** (`x = view_rect.right() - 4`,
  `anchor=(1,0.5)`) and is not clipped by the axis/dock.
- **AC-D11.2** Given a zone with top/bottom prices, When rendered, Then two labels
  are visible at the zone’s top and bottom edges on the inner right.
- **AC-D11.3** Given multiple drawings at nearby prices, When rendered, Then
  labels remain legible (small vertical offset, not fully overlapping).
- **AC-D11.4 (ESC-006 — re-scoped to label-vs-label; Q33 answered 2026-09-27)** Given
  multiple drawing price labels at (or within the label band of) each other's prices,
  When those labels render **inside the plot** near the right edge
  (`anchor=(1,0.5)`, `x = view_rect.right() - 4`), Then their text bounding boxes MUST
  NOT overlap: consecutive labels are offset by `>= 15 px` (the existing stacking
  threshold) and each remains fully inside `view_rect` on the right edge.
  - Measurable: for each consecutive pair of drawing labels,
    `abs(label_a_bbox.center().y() - label_b_bbox.center().y()) >= bbox_height`
    (their scene bounding rects do not intersect).
  - **The crosshair chip is out of scope for this criterion.** It now lives in the
    Y-axis lane outside the plot (see D2), so crosshair-vs-label overflow collision no
    longer applies; the earlier `>= 15 px` chip-vs-label requirement is retired. The
    Code Reviewer MUST **re-scope ESC-006** accordingly (label-vs-label only).
  - A label run longer than the pane height is still clamped to `view_rect.bottom()`;
    with lane separation this is a pure label-vs-label stacking concern, not a
    chip-vs-label priority question.

- **AC-D11.5 (ESC-009 — high-DPI coverage)** Given the app renders at device pixel
  ratio `2`, When drawing price labels render, Then each label’s scene bounding rect
  remains fully inside `view_rect` on the right edge (`x + width <= view_rect.right()`)
  and is not clipped by the axis/dock. Measurable at DPR 2: the label bbox is on-screen
  and within `view_rect`.

**Edge Cases:**
- Very narrow window or wide axis keeps labels inside (clamped to `view_rect`).
- Zooming/panning keeps labels at the right edge and at the correct price.
- High-DPI (DPR 2) keeps labels inside the plot and legible (AC-D11.5).
- No drawing → no label.
- Crosshair resting exactly on a drawing price is no longer a collision: the chip is in
  the Y-axis lane and the drawing label is inside the plot (D2 / Q33). The remaining
  label-vs-label stacking when a run exceeds the pane height stays as `AC-D11.4`.

### D12 — Zone double-click should open settings popup with 4 tabs (Extend omitted)
- **Area:** Drawings / `ui/drawing_overlay.py` + new `ui/drawings_dialog.py` (or `ui/zone_settings_dialog.py`)
- **Status:** clarified 2026-09-19 — criteria defined, Q24 Extend omitted confirmed — revises prior popup assumptions
- **Visual reference (ESC-004 gate):** Q24 confirmed the four attached screenshots as
  the spec (Style with `Extend` omitted, Text, Coordinates, Visibility). The visual
  reference for this defect is the **user-confirmed screenshots**; the one deliberate
  divergence from the reference (`Extend` dropped) is explicitly user-directed. Gate
  status: **CONFIRMED** (screenshots supplied and confirmed 2026-09-19).
- **Reported:** User wants double-click on a zone (rectangle) to open the zone
  settings popup as per the four attached screenshots. The Style tab in the
  reference shows an `Extend` dropdown (`Extend right`), but the user says
  `Extend` is not required because **extend both sides** is the required
  behaviour.
- **Observed in code at time of report:** `DrawingOverlay` handles single-click
  selection and drag, but double-click does not open a zone settings popup; no
  4-tab dialog exists for zones.

**Decisions confirmed 2026-09-19 (Q24 Extend omitted):**
- Double-click on a zone (rectangle) drawing opens a **modal Zone Settings popup**
  titled `Rectangle` with a pencil icon and an `X` close button, showing four tabs:
  **Style / Text / Coordinates / Visibility** as in the attachments.
- **Style tab:** `Extend` control is **omitted** (zone always extends both sides);
  `Border` (color swatch green + solid line), `Middle line` (unchecked checkbox +
  purple swatch + dashed line), `Background` (checked + checker swatch) remain.
- **Text tab:** text colour swatch (white), font size `14`, `B`/`I` toggles, `Add
  text` multi-line field, `Text alignment` `Top` / `Right` dropdowns.
- **Coordinates tab:** `#1 (price, bar)` `7623.89` and `#2 (price, bar)` `7614.81`
  with up/down steppers, pre-filled from the zone’s current `x1/y1/x2/y2`.
- **Visibility tab:** checkboxes for `Ticks`, `Seconds` (1–59 slider), `Minutes`
  (1–59), `Hours` (1–24), `Days` (1–366), `Weeks` (1–52), `Months` (1–12),
  `Ranges` (no value) — as shown.
- OK/Apply updates the zone and re-renders; Cancel/X closes without change.

**Acceptance Criteria (Given/When/Then):**
- **AC-D12.1** Given a zone exists, When the user double-clicks the zone body, Then
  the `Rectangle` popup opens with four tabs and the zone’s current values
  pre-filled, and `Extend` is not shown.
- **AC-D12.2** Given the popup is open, When the user changes Style/Text/Coordinates
  and confirms, Then the zone updates and re-renders with the new values.
- **AC-D12.3** Given the popup is open, When the user opens the Visibility tab,
  Then the time-frame checkboxes/sliders match the attachments and are
  interactable.

**Edge Cases:**
- Double-click on a non-zone drawing does not open the zone popup.
- Double-click with no selection does nothing.
- Cancel/X discards changes; the zone remains as before.

### D13 — Watchlist dock resizable to 50% of the **chart area** with persistence
- **Area:** Watchlist dock / `ui/main_window.py`, `ui/watchlist_panel.py`
- **Status:** clarified 2026-09-20 (Q25/Q26) — **denominator SUPERSEDED/CORRECTED 2026-10-03 by B1**
  to **50% of the chart area** (was "50% of `MainWindow` width"); enforced during the drag (D17).
- **Supersession note (B1, 2026-10-03):** D17's report ("extend till **50% of the chart area**") is
  authoritative. The Q25 answer ("~50% of `MainWindow` width") is **corrected** so the cap is measured
  against the **chart area** (the central region excluding both docks), which matters once the right
  dock (D18) is visible. `AC-D13.1`–`AC-D13.3`, Journey 14, A17 and R15 are updated in lockstep; the
  D13 intent (freely draggable up to the cap, persisted) is unchanged.
- **Reported:** The watchlist panel should extend more so the user can see more
  symbols/columns; the current width is limited and is not remembered.
- **Observed in code at time of report:** the Watchlist is a `QDockWidget` in
  `LeftDockWidgetArea` (`ui/main_window.py`); its width was not explicitly bounded
  to a percentage and was not persisted across restarts.

**Decisions confirmed 2026-09-20 (Q26 persist yes); denominator corrected 2026-10-03 (B1):**
- Docked Watchlist is freely draggable **in both directions** up to **`floor(0.50 × chart_area)`**,
  additionally clamped by the **chart-minimum rule (B3)** so the chart area keeps **≥400px**; minimum
  watchlist `150px`; the clamp is applied **during the drag** as well as on window resize; floating
  geometry is unconstrained. Default width **~220px**.
- Watchlist width persists across restarts as an **integer pixel** value (e.g.,
  `QSettings watchlist/width` or a DB key); default **~220px** if none saved;
  restore is clamped to the current cap.

**Acceptance Criteria (Given/When/Then):**
- **AC-D13.1 (denominator corrected by B1)** Given a docked Watchlist at default width and a loaded
  chart, When the user drags the vertical splitter **either direction**, Then the watchlist width is
  clamped to `[150, floor(0.50 × chart_area)]`, further limited by the chart-minimum rule (`chart_area
  ≥ 400px`), the chart width adjusts, and the handle remains draggable across the range — **including
  during the drag** (not only on window resize).
- **AC-D13.2** Given a persisted width, When the app restarts, Then the watchlist
  restores to the persisted integer width clamped to the current
  `floor(0.50 × chart_area)` (default ~220px if none saved, never <150).
- **AC-D13.3** Given a wide watchlist and the width available to it shrinks (main window narrowed, or
  the right dock enlarged per B3), When the width would exceed the current cap, Then the watchlist is
  auto-clamped to the cap without error and remains resizable.

**Edge Cases:**
- Floating Watchlist is not constrained to 50%; docking it again re-applies the
  clamp.
- Extremely narrow windows keep `150px` watchlist and the chart minimum; if the window
  is smaller than the sum, the watchlist yields to the chart minimum.
- No saved width on first run uses ~220px.
- The right dock (D18) grows while the watchlist is at its cap → the watchlist is re-clamped
  (effective cap shrinks) per `AC-D18.5`/B3.

### D14 — Double-click Watchlist row loads chart (identical to Load Chart)
- **Area:** Watchlist dock / `ui/watchlist_panel.py` + `ui/main_window.py`
- **Status:** clarified 2026-09-20 — criteria defined, Q27–Q29 confirmed
- **Reported:** Clicking a watchlist row should load that symbol’s chart.
- **Observed in code at time of report:** the watchlist table selected rows but had
  no double-click handler to trigger chart loading; chart loading is centralised in
  `MainWindow.load_chart()`.

**Decisions confirmed 2026-09-20 (Q27 double-click row; Q28 identical to Load
Chart; Q29 no-op semantics):**
- **Double-click anywhere on the row** (any of the 7 columns) triggers the load;
  single-click only selects the row (existing `SelectRows` behaviour retained).
- Load is **identical to typing the symbol in the Symbol input and pressing Load
  Chart**: set `symbol_input` to the row’s Symbol (uppercased), then invoke the
  existing `load_chart()` with the current `tf_combo` and `ext_hours_btn` — this
  includes cancelling the previous RT subscription, showing cached bars, fetching
  the delta, starting the RT subscription, and subscribing DOM if enabled.
- **No-op** when the double-clicked symbol (case-insensitive) equals
  `_current_symbol` — no reload, no new `reqId`, no RT cancel, no flicker; and when
  IBKR is disconnected — no historical/RT request and
  `status_bar.showMessage("Disconnected — cannot load chart.", 3000)`.
- Double-click on the header or an empty area is also a no-op.

**Acceptance Criteria (Given/When/Then):**
- **AC-D14.1** Given the Watchlist has symbols, IBKR is connected, and the current
  chart is `SPY`, When the user double-clicks any cell in the `AAPL` row, Then
  `symbol_input` becomes `AAPL` and the chart loads for `AAPL` with the current
  timeframe/ext-hours via the same sequence as manual Load Chart (cached bars
  shown, delta fetched, RT started).
- **AC-D14.2** Given the current chart is `AAPL`, When the user double-clicks the
  `AAPL` row, Then no reload occurs — no new `reqId` is issued, the RT subscription
  for `AAPL` remains, and the chart does not flicker.
- **AC-D14.3** Given IBKR is disconnected, When the user double-clicks any watchlist
  row, Then no historical/RT request is made and the status bar shows
  `Disconnected — cannot load chart.` Double-click on the header or an empty area
  also does nothing.
- **AC-D14.4 (ESC-010 — mid-drag symbol change)** Given a drawing is being dragged
  (a drag gesture is in progress on the chart), When the user double-clicks a watchlist
  row for a **different** symbol, Then the chart loads for the new symbol and **no
  `RuntimeError` / `RuntimeWarning` is raised** (the overlay's drag/draft state is
  cleared before the items are detached), and the chart renders normally afterward.
  - Measurable: running the mid-drag double-click against a drag-active overlay
    produces zero unhandled exceptions in the app's exception hook / pytest-qt
    `qt_log` and the new symbol's chart is displayed.

**Edge Cases:**
- Symbol case differences (`aapl` vs `AAPL`) are treated as the same symbol
  (case-insensitive comparison).
- Double-click during an in-flight load for a different symbol cancels that RT and
  loads the new symbol (existing `load_chart` behaviour).
- No symbols in the watchlist → double-click does nothing.
- Double-click a different symbol while a drawing drag is in progress → no crash
  (`AC-D14.4`); the defensive `dragItem` clearing must be exercised, not assumed.

### D15 — Double-click horizontal line should open settings popup with 4 tabs
- **Area:** Drawings / `ui/drawing_overlay.py` + new `ui/horizontal_line_settings_dialog.py` (or `ui/drawing_settings_dialog.py`)
- **Status:** clarified 2026-09-20 — criteria defined, Q30 correct
- **Visual reference (ESC-004 gate):** Q30 confirmed the four attached `Horizontal line`
  screenshots as the spec (Style `Line`, Text 12, Coordinates single `#1 (price)`,
  Visibility). Gate status: **CONFIRMED** (screenshots supplied and confirmed
  2026-09-20).
- **Reported:** User double-click on a horizontal line should open the line settings
  popup as per the four attached screenshots for `Horizontal line`.
- **Observed in code at time of report:** `DrawingOverlay` handles single-click
  selection/drag for horizontal lines but double-click does not open a settings
  popup; no 4-tab dialog exists for horizontal lines.

**Decisions confirmed 2026-09-20 (Q30 correct):**
- Double-click on a horizontal line drawing opens a **modal Horizontal line settings
  popup** titled `Horizontal line` with a pencil icon and an `X` close button,
  showing four tabs: **Style / Text / Coordinates / Visibility** as in the
  attachments.
- **Style tab:** `Line` (color swatch white + solid line style) — as shown.
- **Text tab:** text colour swatch (white), font size `12`, `B`/`I` toggles,
  `Add text` multi-line field, `Text alignment` `Top` / `Right` dropdowns.
- **Coordinates tab:** `#1 (price)` `7548.85` with up/down steppers, pre-filled
  from the line’s current price `y`.
- **Visibility tab:** checkboxes for `Ticks`, `Seconds` (1–59 slider), `Minutes`
  (1–59), `Hours` (1–24), `Days` (1–366), `Weeks` (1–52), `Months` (1–12),
  `Ranges` — as shown.
- OK/Apply updates the line and re-renders; Cancel/X closes without change.

**Acceptance Criteria (Given/When/Then):**
- **AC-D15.1** Given a horizontal line exists, When the user double-clicks the
  line, Then the `Horizontal line` popup opens with four tabs and the line’s
  current values pre-filled.
- **AC-D15.2** Given the popup is open, When the user changes Style/Text/Coordinates
  and confirms, Then the line updates and re-renders with the new values.
- **AC-D15.3** Given the popup is open, When the user opens the Visibility tab,
  Then the timeframe checkboxes/sliders match the attachments and are
  interactable.

**Edge Cases:**
- Double-click on a non-horizontal drawing does not open the horizontal-line popup.
- Double-click with no selection does nothing.
- Cancel/X discards changes; the line remains as before.

### D16 — Historical bars missing across a cache/reopen gap (price **and** volume panels)
- **Area:** Bar-load path — `ui/main_window.py::load_chart` / `_on_historical_bar` /
  `_on_historical_data_end`; `ibkr/market_data.py::MarketDataManager.req_historical_data`;
  `ibkr/client.py::IBApiClient.historicalData`; `data/bar_cache.py`; rendered by
  `ui/chart_panel.py::update_chart` / `_refresh_candles` (shared by price + volume).
- **Status:** **clarified — criteria finalised 2026-10-02 (Q37–Q39 answered).**
- **Visual reference (ESC-004 gate):** **N/A** — D16 is a data/behaviour defect, not a UI-visual
  decision; no visual reference is required and AC-G.1 does not apply.
- **Reported (2026-10-02, screenshot):** symbol `SPY`, TF `5 mins`, Mode `Candles`, Extended Hours
  ON, Eastern Time. Price candles are present 09/14–09/18, **entirely absent 09/19–09/27**, and
  resume 09/28–10/02. The **volume panel** is absent over the same span. 09/21–09/25 are normal
  trading weekdays, so this is not merely weekend session shading.
- **Observed in repository (validated against the current files, 2026-10-02):**
  - `load_chart()` shows cached bars, then issues **one** `req_historical_data` with
    `endDateTime=""` (up to now) and the fixed `TIMEFRAME_CONFIG` duration (`5 mins` → `5 D`);
    `_on_historical_data_end` then saves the fetched bars and re-reads **all** cached bars
    (`BarCache.get_bars`) — the union of the old cache and the last 5 days.
  - `_refresh_candles` frames `xRange` from `_bars[0].ts` to `_bars[-1].ts` and drives **both** the
    candle item and the volume bars from the same `self._bars` list, so a hole in the bar list
    shows as a hole in **both** panels. No separate volume fix is needed once the bar list is
    continuous.
  - `BarCache.get_last_timestamp(symbol, timeframe)` (`data/bar_cache.py::BarCache.get_last_timestamp`; cited `:33`, now `:55` — indicative) returns `MAX(ts)` but
    is **not** used by `load_chart` (`ui/main_window.py::MainWindow.load_chart` does not read it; cited `:430–444` — indicative); the fetch is
    neither anchored to, nor sized to reach, the cached span.
  - **Empirically confirmed against the live SQLite cache** (read-only inspection of
    `~/Library/Application Support/NDThinkChart/charting_app.sqlite3`, 2026-10-02): `SPY 5 mins`
    has 192 bars/day for 2026-09-14…09-18, then **no bars for 2026-09-19…2026-09-27**, then
    192/day for 2026-09-28…10-01 and 110 for 10-02. The hole is a real missing-bar span in the
    cache, not a rendering artefact, and it is **internal** (newer bars are already cached after
    it). (`AAPL 5 mins` similarly ends at 2026-09-18.)
  - **Root cause (diagnosis):** the delta fetch is anchored to **now** with a fixed duration and is
    **not** anchored to (or sized to reach) the cached span, so any closure longer than that
    duration leaves an unfetched span between the cache and `now − duration`. For `5 mins`
    (`5 D`) a >5-day closure produces exactly the observed hole. Git history shows the path:
    commit `2c5616c` changed Step 2 from `end_dt=last_ts+60` to `end_dt=""` (fixing a stale-cache
    *tail* gap) but did not enlarge the window to reach the cache or detect an internal hole. See
    `design_gaps.md` DG21.

**Decisions (2026-10-02 — Q37, Q38, Q39 answered):**
- **Q37 — backfill the whole gap.** On load, the app determines the missing span from the cached
  series to now and fetches enough history to make the bar list continuous, issuing **additional
  request(s) (chunking)** when the span exceeds one IBKR request's duration. Options (b) (drop/limit
  old cached bars so no hole shows) and (c) (fixed larger window on every load) are **not adopted**.
  It is not acceptable to display a range wider than the data fetched in a way that leaves a silent
  hole. Because the reported repro is an **internal** hole, "from the last cached bar" is
  implemented as filling the missing span **between cached blocks within the displayed range** (not
  merely the span after the newest cached bar) — see DG21.
- **Q38 — closures stay empty.** Genuine market closures (weekend/holiday/overnight) render
  **empty** and are **not** filled, compressed, or interpolated. D16 is scoped to missing
  **trading-session** bars only. (**Display part superseded 2026-10-06 by D21.4/B9:** the app may now **collapse between-session non-trading time** for display; the no-fill/no-interpolate and no-silent-hole rules remain.)
- **Q39 — all timeframes + any symbol.** The fix and verification cover **all** timeframes
  (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and **any symbol**; `SPY 5 mins`
  is the reported repro only.
- **ESC-023 — trading-day calendar correction (2026-10-02):** the US-equity observed-day convention applies to New Year's Day **except** when the Saturday→preceding-Friday shift would place the closure on **Dec 31**, the year-end accounting date. Per **NYSE Rule 7.2**'s explicit year-end accounting-period exception, when Jan 1 is a Saturday **no New Year's holiday is observed** and **Dec 31 stays open**; no substitute closure is created (the Saturday Jan 1 itself is non-trading as a weekend). All other observed-shift cases are unchanged (Independence Day Sat→Fri, Christmas Sat→Fri / Sun→Mon, Juneteenth Sat→Fri, New Year's Sun→Mon). See `AC-D16.7`.

**Acceptance Criteria (Given/When/Then) — FINAL:**
- **AC-D16.1 (backfill the whole gap — all timeframes and any symbol; Q37/Q39)** Given a seeded
  `bars` cache whose series has a missing **trading-session** span between cached bars and now
  (tail gap **or** internal hole) and the elapsed closure exceeds the timeframe's fetch window,
  When the symbol/timeframe is loaded and all historical request(s) complete, Then the resulting
  bar list is continuous over the span from the oldest displayed bar through now — bars exist for
  every trading session, including every weekday in the missing span, with no artificial hole.
  - Measurable (offscreen, no live TWS): drive the real load path with a seeded cache and a
    stubbed historical feed; assert the resulting `ChartPanel._bars` (and `BarCache.get_bars`)
    contain the expected per-trading-day bar counts for the missing weekdays and that the maximum
    inter-bar gap **within** a trading session does not exceed one bar period. Run the assertion
    **parameterized over all six timeframes** (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`,
    `1 day`) and at least two symbols (Q39) — not `SPY 5 mins` alone.
- **AC-D16.2 (both panels; Q37)** Given the same scenario, When the chart renders, Then **both**
  the price candles and the volume bars are present across the backfilled span (the volume panel is
  not empty where the price panel has bars).
  - Measurable: the candle item data and the `volume_bars` `x`/`height` arrays both span the
    backfilled timestamps with non-zero heights; a bar-list hole and a volume-panel hole fail
    together.
- **AC-D16.3 (genuine breaks stay empty; Q38)** Given a genuine market closure (weekend, holiday,
  or overnight), When the chart renders, Then that interval is **empty** and is **not** counted as
  a missing-bar defect; no bar is fabricated or interpolated across it and the time axis is **not**
  compressed/collapsed. Only trading-session bars are required. **Dec 31 of a year whose next Jan 1 is a Saturday is NOT a genuine closure** and must not be treated as one — it is a trading day (`AC-D16.7`, ESC-023).
  - **Superseded (display part) by D21.4 (2026-10-06, B9 answered):** genuine closures may now be **collapsed for display** (non-trading between-session gaps are no longer plotted as empty space on intraday timeframes); the **no-fill/no-interpolate** rule above and D16's no-silent-hole requirements (`AC-D16.1`/`AC-D16.4`) are **unchanged**. See D21.4 / `AC-D21.4.*`.
- **AC-D16.4 (bounded by IBKR availability; chunking; Q37/Q39)** Given the requested span exceeds
  what a single IBKR historical request returns (or exceeds IBKR retention), Then the app bridges
  it with additional request(s) where possible (respecting `pacing_manager`), and where data
  genuinely cannot be obtained the chart shows only the available bars and the shortfall is
  **surfaced explicitly** (e.g., status-bar message and/or log) — never a silent hole. No bar is
  ever fabricated to hide an unfillable gap.
- **AC-D16.5 (reported repro — date range spanning 2026-09-19→2026-09-28)** Given a seeded
  `SPY 5 mins` cache holding bars for 2026-09-14…2026-09-18 **and** bars for 2026-09-28…2026-10-02
  with the span 2026-09-19…2026-09-27 missing, and "now" = 2026-10-02, When `SPY` `5 mins` is
  loaded and requests complete, Then the bar list contains trading-session bars for **2026-09-21,
  09-22, 09-23, 09-24 and 09-25** (the missing weekdays), contains **no** bars for the weekend days
  2026-09-19/20 and 2026-09-26/27, and both the price candles and the volume bars render
  continuously across 2026-09-19→2026-09-28 modulo those genuine closures.
  - Measurable: per-weekday bar counts for 09/21–09/25 match the expected intraday cadence;
    `get_bars` for the weekend timestamps returns none; the volume `height` array is non-zero
    wherever a candle exists in the span.
- **AC-D16.6 (no regression)** Given the fix, When the full offscreen suite runs, Then it remains
  green and no existing acceptance criterion (D1–D15) regresses.
- **AC-D16.7 (trading-day calendar — New Year's year-end accounting exception; ESC-023, corrected
  2026-10-02)** Given the US-equity ET trading-day calendar, When `is_trading_day(date)` is
  evaluated for the last calendar day of a year whose next January 1 is a **Saturday** (i.e. Dec 31
  is that year's last trading day and the naive Saturday→preceding-Friday New Year's shift would
  otherwise close it — e.g. `2021-12-31`, `2027-12-31`, `2032-12-31`, `2038-12-31`), Then it
  returns **True**: that Friday is a **trading day**. The New Year's observed-day shift carries an
  explicit **year-end accounting-period exception** (NYSE Rule 7.2) and MUST NOT mark Dec 31
  closed, and MUST NOT substitute any other closure for it.
  - Measurable (offscreen, no live TWS): `is_trading_day(date(2021, 12, 31)) is True`, and likewise
    for `2027-12-31`, `2032-12-31` and `2038-12-31`; the following Monday of the Jan-1-Saturday
    year (e.g. `2022-01-03`) remains a trading day.
  - Unchanged (regression guard): the other weekend-falling fixed-date observed shifts remain
    closures — Independence Day Sat `2026-07-04` → Fri `2026-07-03` closed; Christmas Sun
    `2022-12-25` → Mon `2022-12-26` closed; Juneteenth Sat `2027-06-19` → Fri `2027-06-18` closed;
    and New Year's Day on a Sunday (e.g. `2023-01-01`) is still observed the following Monday
    (`2023-01-02` closed).
  - Consequence binding `AC-D16.1`/`AC-D16.4`: a genuine missing-bar hole on such a Dec 31 is a
    **missing trading session**, so it must be backfilled (`AC-D16.1`) or its shortfall surfaced
    explicitly (`AC-D16.4`) — **never** classified as a genuine closure and left as a silent hole.

**Correction record (ESC-023, 2026-10-02) — artifacts that must change:**
- **Task Manager:** the `T37-T03` acceptance criterion in `docs/tasks/task-graph.json` currently
  encodes "New Year's 2022-01-01 Saturday gives 2021-12-31 Friday closed" — this is **wrong** and
  must be corrected to the year-end accounting exception (`AC-D16.7`); its test description and
  expected result must change accordingly, and `2021-12-31`, `2027-12-31`, `2032-12-31`,
  `2038-12-31` must be asserted **trading days**.
- **Build:** `services/market_calendar.py::_observed` (as applied to New Year's Day) must not shift
  the closure onto Dec 31, and the `T37-T03` assertions in `tests/test_market_calendar.py` (which
  currently assert `is_trading_day(date(2021, 12, 31)) is False`, around `:105`–`:124`) must be
  updated to the corrected convention. The remaining observed-shift cases and their assertions stay
  unchanged.
- **Code Reviewer:** re-verify ESC-023 on the next pass.

**Edge Cases:**
- Internal hole (**the reported repro**) — newer cached bars separated from an older block by a
  missing trading-session span — must be healed, not only a tail gap after `MAX(ts)` (DG21).
- App closed for less than the fetch window → no hole today; must stay that way.
- App closed much longer than IBKR retention → the span cannot be filled; the chart must not
  fabricate or interpolate bars and must surface the shortfall (`AC-D16.4`).
- Ext Hours OFF vs ON changes `useRTH`; the backfill must respect the current setting and not
  leave a hole because of a mode switch.
- Symbol/timeframe switched while a backfill request is in flight → no cross-contamination
  (`_current_req_id` filtering already exists — verify), and the new symbol/timeframe still gets its
  own continuity treatment.
- Empty cache / brand-new symbol → fetch the configured window and render it.
- Cache end already at now (fresh) → no redundant requests; `INSERT OR REPLACE` dedupes any
  overlap.
- Weekend-only gap (cache ends Fri, reopened Mon) → must **not** be "filled"; renders as an empty
  weekend (`AC-D16.3`).
- A cache with a hole whose newest bar is older than the fetch window → covered by the same
  mechanism (tail gap).
- All timeframes and any symbol must behave identically (Q39), including `1 day` (which has a much
  wider configured duration).

### D17 — Watchlist dock will not extend/reduce in full screen (D13 resize not effective)
- **Area:** Watchlist dock / `ui/main_window.py` (`resizeEvent` clamp, `resizeDocks`, dock drag hook),
  `ui/watchlist_panel.py` (`watchlist_max_width` / `clamp_watchlist_width`).
- **Status:** **clarified 2026-10-03 — final criteria (B1, B4 answered).** D17 is a **defect in the
  built D13 behaviour**: the D13 intent is correct but not enforced. B1 **corrects D13's denominator**
  to 50% of the chart area (see D13 supersession note); B4 confirms the handle moves both directions,
  min 150px, default ~220px, persistence still required.
- **Visual reference (ESC-004 gate):** the user supplied a full-screen screenshot of the running app
  (2026-10-03) showing the narrow watchlist on the left with a thin drag handle and the chart occupying
  almost the whole width. This is accepted as evidence of the **reported state**; the target geometry is
  now **specified numerically** by B1/B4 (50% of chart area, min 150px, default ~220px, both drag
  directions) so no further visual reference is required — the target is a measurable geometry, not a
  visual-design choice (AC-G.1 does not require a screenshot for a numeric layout rule). Gate: **N/A
  for a visual reference**; geometry resolved by B1/B4 (see A34).
- **Reported (verbatim intent):** "the watch list section (left side) is too small and does not extend
  or reduce in width if user tries it. Fix: allow watch list section to be extended till 50% of the
  chart area. the chart area should become smaller if watch list is made bigger."
- **Observed in repository (validated 2026-10-03 against the current files):**
  - `WatchlistPanel.setMinimumWidth(WATCHLIST_MIN_WIDTH)` = 150px is set (`ui/main_window.py:225`, `[historical]` 2026-10-03);
    **no maximum width is ever set on the dock** and there is no `setMaximumWidth` anywhere.
  - The clamp helpers exist and are correct in isolation (`watchlist_max_width` = `max(150, min(int(W*0.50),
    W-400))`, `clamp_watchlist_width`), but they are applied **only** at construction and inside
    `resizeEvent`, and `resizeEvent` re-clamps **only when the dock is already wider than max**
    (`if self.watchlist_dock.width() > max_w`, `ui/main_window.py:962-968`, `[historical]` 2026-10-03; now `ui/main_window.py::MainWindow.resizeEvent`). `resizeEvent` fires on
    *window* resize, **not** on a dock-splitter drag, so a user drag that stays within the window can
    move the dock freely and the cap is not enforced during the drag.
  - No `splitterMoved`/`dockLocationChanged` handler exists; nothing wires the dock's internal splitter
    handle to the clamp helpers, so D13's "handle remains draggable across the range" is **not actually
    enforced** — the likely root cause of "does not extend".
  - **Full-screen interaction:** `MainWindow` never calls `showFullScreen`; full screen is an OS window
    state. Because there is no width cap during a drag and no handler on drag completion, "in full
    screen" does not by itself disable resizing — but the reported symptom (narrow, non-resizing
    watchlist) is consistent with the drag not being clamped/bounded and the restore only running at
    construction/`resizeEvent`.
  - **Diagnosis:** a **defect in the built D13 behaviour**, not a wrong D13 intent — the D13 intent
    (freely draggable to the cap, persisted) stands; the built code does not enforce it during a drag.
    B1 additionally **corrects** D13's denominator from window width to chart area (superseded in D13).

**Decisions confirmed 2026-10-03 (B1 + B4):**
- **Cap denominator (B1):** the watchlist maximum width is `floor(0.50 × chart_area)` — measured against
  the **chart area**, not `MainWindow` width. This **supersedes D13's Q25 denominator** and is applied
  in `AC-D13.1`.
- **Both drag directions (B4):** the splitter handle must drag **wider and narrower** between the
  minimum and the cap. Minimum stays **150px**; default stays **~220px**; the persisted width (D13/Q26)
  is **still required**.
- **Enforcement during the drag (D17 root cause):** the cap must be enforced **while the user drags**
  (reusing `watchlist_max_width` / `clamp_watchlist_width` as the single source of truth), not only in
  `resizeEvent`.
- **Chart-minimum coupling (B3):** the effective cap is additionally bounded so the chart area keeps
  **≥400px** and the right dock (D18) is accounted for — see `AC-D18.5`.

**Acceptance Criteria (Given/When/Then) — FINAL:**
- **AC-D17.1 (drag wider; 50%-of-chart-area cap; B1)** Given a docked Watchlist and a loaded chart,
  When the user drags the splitter handle to the **right**, Then the watchlist width grows continuously
  up to `floor(0.50 × chart_area)` and the chart area narrows correspondingly. (Measurable: watchlist
  width `<= floor(0.50 × chart_area)` at all times during and after the drag; the width increases
  monotonically with the drag.)
- **AC-D17.2 (drag narrower; both directions work; B4)** Given the watchlist is wider than its minimum,
  When the user drags the handle to the **left**, Then the watchlist width **reduces** continuously down
  to **150px** and stops there, with the chart area growing correspondingly. (Measurable: the width
  decreases with a leftward drag, and never goes below `150px`.)
- **AC-D17.3 (cap enforced during the drag in full screen; the D17 root cause)** Given the app is shown
  **full screen** (no window `resizeEvent` fires during the drag), When the user drags past the cap,
  Then the width **stops at the cap** during the drag itself — not merely re-clamped later on a window
  resize — and the app remains stable with no overshoot into the chart. (Measurable: perform the drag
  without any window resize and assert the final width equals the cap, not the pre-clamp width.)
- **AC-D17.4 (persistence; Q26 still required; B4)** Given a Watchlist width persisted by a previous
  session, When the app restarts, Then the width is restored as the persisted integer pixel value,
  clamped to the current `floor(0.50 × chart_area)` and the chart minimum (default ~220px if none saved,
  never <150px).
- **AC-D17.5 (re-clamp on available-space change; B3)** Given the watchlist is at/near its cap, When the
  available chart-area width shrinks (main window narrowed **or** the right dock enlarged), Then the
  watchlist is re-clamped to the new cap without error and remains resizable.
- **AC-D17.6 (regression)** Given the fix, Then the pre-existing D13 acceptance criteria
  (`AC-D13.1`–`AC-D13.3`, updated in lockstep per B1) and `test_d10_d13_integration.py` remain green
  (or are updated in lockstep where B1 changes the denominator — never left contradicting D17).

**Edge Cases:**
- Floating watchlist: **unconstrained** (per D13); re-docking re-applies the cap.
- Extremely narrow window keeps the watchlist min (150px) and the chart minimum (~400px); if the window
  is smaller than the sum, the watchlist yields to the chart minimum.
- Dragging below the minimum stops at **150px**.
- Restart restores the persisted width clamped to the current cap.
- Right dock (D18) enlarged while the watchlist is at its cap → the watchlist is re-clamped (its
  effective cap shrinks) so the chart keeps its minimum (`AC-D18.5`/B3).
- Cap sits between min and default-invalid cases: a window/chart area so small that `floor(0.50 ×
  chart_area) < 150px` → the 150px minimum wins, and the chart-minimum rule still applies.

### D18 — Active Trader (+ Portfolio) right dock not visible in full screen; 40% / equal-width sizing (NEW)
- **Area:** Active Trader / Portfolio right dock / `ui/main_window.py` (`RightDockWidgetArea` setup),
  `ui/active_trader_panel.py`, `ui/active_portfolio_panel.py`.
- **Status:** **clarified 2026-10-03 — final criteria (B2, B3 answered). NEW requirement (not covered
  by any existing defect).** B2 makes Active Trader + Portfolio **one right-dock region** (both sections
  stacked), so the 40% cap applies to that region and the two sections are equal width by construction.
  B3 gives the combined rule: independent caps + chart minimum, so enlarging one dock can force the
  other to shrink.
- **Visual reference (ESC-004 gate):** the user supplied a full-screen screenshot (2026-10-03) showing
  the right side clipped off-screen — "Active Trader" title truncated at the far right ("Active Tra..."),
  with "Ladder / Ask Size" headers and a mostly empty ladder, then a "Portfolio" section ("Account
  su..." + column headers). This is accepted as evidence of the **reported state**. The target is a
  measurable layout (one region, 40% cap, on-screen, equal width), specified numerically by B2/B3, so
  no further visual reference is required (AC-G.1 N/A for a numeric layout rule). Gate: **N/A for a
  visual reference**; geometry resolved by B2/B3 (see A35).
- **Reported (verbatim intent):** "the right side is the active trader section, it does not even be
  visible to user if the app is made full screen. fix: active trader section should reposition so that
  it fits in the visible area of the full screen. also, if user wants the user should be able to
  increase the size of active trader section till 40% of the chart area. active trader section and
  portfolio should have same width. The chart area should become smaller if active trader section is
  made bigger."
- **Observed in repository (validated 2026-10-03 against the current files):**
  - `ActiveTraderPanel` and `ActivePortfolioPanel` are currently added as **two separate `QDockWidget`s**
    in `RightDockWidgetArea` (`ui/main_window.py:234-252`, `[historical]` 2026-10-03). Neither panel sets any
    `setMinimumWidth`/`setMaximumWidth`/`setMinimumSize`/`sizeHint`, and **no `resizeDocks` call is
    made for either right dock** — unlike the watchlist, they get no explicit width at all.
  - There is **no 40% rule, no equal-width rule, no chart-shrink coupling, and no full-screen
    reposition/visibility handling** anywhere in the codebase (searched: no `showFullScreen`,
    `setWindowState`, `WindowFullScreen`, or full-screen branch exists in `ui/`).
  - Both docks are user-hidden by default in the existing integration tests
    (`tests/test_d10_d13_integration.py` dock-hide setup at `:33,50-52` when written — indicative), confirming they are an **independent horizontal
    consumer** that the current D13 clamp does not account for — the existing clamp uses the whole
    window width, not the width left after the right region.
  - This is a **new requirement**, distinct from D13.

**Decisions confirmed 2026-10-03 (B2 + B3):**
- **One right-dock region (B2):** Active Trader and Portfolio are **one right-dock region** containing
  both sections **stacked vertically**. They are therefore **inherently equal width** (the region's
  width); the **40%-of-chart-area cap applies to that single region**. The current two-`QDockWidget`
  structure is a wrong shape for this requirement and is expected to become a single region/container
  (with the two panels stacked inside) — the exact implementation is Plan/Build's call, but the
  behaviour must satisfy the criteria below.
- **Combined width rule (B3):** the watchlist (50% of chart area) and the right region (40% of chart
  area) have **independent caps**, each **additionally clamped against the remaining space** so the
  chart area keeps a **minimum (~400px)**. Consequently, enlarging one dock **can force the other to
  shrink**; both cannot sit at their individual maxima if that would starve the chart.
- **Full-screen visibility (reported defect):** the right region must be fully within the visible
  window in full screen (not clipped/off-screen), and content minimums (ladder/portfolio) must not
  force it off-screen.

**Acceptance Criteria (Given/When/Then) — FINAL:**
- **AC-D18.1 (full-screen visibility; reported defect)** Given the app is shown **full screen**, When
  the chart and the right region render, Then the right region (Active Trader ladder + Portfolio) is
  **fully within the visible window area** — its left edge `>= chart area right edge` and its right edge
  `<= window right edge`, with a **non-zero visible width** — and is on-screen **without manual
  repositioning**. (Measurable: assert the dock's `geometry()` lies within the window's `rect()` and
  `width() > 0` in an offscreen full-screen-sized window.)
- **AC-D18.2 (grow up to the 40%-of-chart-area cap; chart shrinks)** Given the right region is visible,
  When the user enlarges it (drag the handle / `resizeDocks`), Then its width grows continuously up to
  `floor(0.40 × chart_area)` and the **chart area narrows correspondingly**. (Measurable: right-region
  width `<= floor(0.40 × chart_area)` during and after the resize; chart width decreases as the region
  grows.)
- **AC-D18.3 (equal width by construction; B2)** Given the single right region is visible, Then the
  Active Trader ladder section and the Portfolio section render at **equal width** — i.e. each section's
  width equals the region's content width (they are stacked in one region). (Measurable: `active_trader
  section width ≤ region content width` and `portfolio section width ≤ region content width`, and the
  two sections' widths are equal within a 1px tolerance.)
- **AC-D18.4 (reduce direction + stop at cap and minimum)** Given the right region is at/near its cap,
  When the user drags further to enlarge, Then the width **stops at the cap** with no overshoot; When
  the user drags to shrink, Then the region reduces down to its minimum and stops. (Measurable: no
  resize leaves the width above the cap or below the minimum.)
- **AC-D18.5 (combined cross-clamping; chart minimum; B3)** Given both the watchlist and the right
  region are enlarged, When their combined width would push the chart area below its **~400px**
  minimum, Then **both** docks are clamped so the chart area stays `>= 400px`; enlarging one dock
  **forces the other to shrink** rather than letting the chart collapse. (Measurable: set both docks
  near their individual maxima, then enlarge one; assert `chart_area >= 400px` and the other dock's
  width decreased.)
- **AC-D18.6 (content must not push the dock off-screen)** Given the ladder/portfolio content is wider
  than the region (e.g. a wide ladder), When the region renders, Then the region's own geometry still
  satisfies `AC-D18.1`/`AC-D18.2` — content minimums do not force it past the window edge or past the
  cap. (Measurable: with wide content, the region's `width()` and right edge still satisfy the
  visibility + cap assertions; content scrolls/clips internally instead.)
- **AC-D18.7 (persistence — non-blocking default)** Given the app restarts, Then the right region's
  width/visibility is restored **only if persistence is specified**; the **default is not persisted**
  (A36), matching D10's volume-toggle precedent. *(Non-blocking default — see A36; not a blocking
  question.)*
- **AC-D18.8 (regression)** Given the fix, Then the pre-existing suite remains green and D13's
  watchlist behaviour is unchanged except where B3 explicitly couples the two.

**Edge Cases:**
- Both left (watchlist) and right docks enlarged at once → each clamps against the remaining space so
  the chart keeps its minimum; enlarging one can force the other to shrink (`AC-D18.5`, B3).
- Full screen on a small display (e.g. laptop) → the region still fits (`AC-D18.1`) and the chart keeps
  its minimum; on a very small window the chart minimum wins and the dock is capped accordingly.
- Docks hidden/detached (floating) → floating geometry is **unconstrained**; re-docking re-applies the
  cap. Content minimums must not force the dock off-screen (`AC-D18.6`).
- Ladder/portfolio content wider than the dock → dock must not be forced off-screen (`AC-D18.6`); the
  screenshot's clipped ladder suggests an unbounded content width today.
- A window small enough that `floor(0.40 × chart_area) < region minimum` → the region minimum wins, and
  the chart-minimum rule still applies.

### D19 — Toolbar minimum width pins the central widget, starving the dock splitter (D17/D18 still not effective in the real app)
- **Area:** `ui/main_window.py` toolbar construction + central-widget composition (lines ~100–223); the D17/D18 test
  harnesses (`tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`,
  `tests/test_dock_d18_region.py`, `tests/test_dock_layout.py`).
- **Status:** **clarified and finalised 2026-10-05 (B5–B6 answered).** Reported 2026-10-05; diagnosed; the fix is a horizontal scroll/elide wrapper around the existing toolbar (B5) with the watchlist cap unchanged at 50% of the chart area (B6). `AC-D19.1`–`AC-D19.7` are final.
- **Relation to D17/D18 (recorded — not a silent reopen):** D17 (watchlist resize) and D18 (right-dock full-screen
  visibility) were built and verified green (566 tests) at commit `5bd7c93`, but the user reports **D17 still does not
  work in the real app**. D19 is a **distinct defect** that (a) prevents D17 and D18 from being observable in a
  **toolbar-visible** window and (b) was **masked by the D17/D18 test harnesses**. D17/D18 remain built and their
  criteria stand unchanged; D19 adds the real-app condition and the test-masking regression guard.
- **Reported (verbatim intent):** "D17 still does not work in the real app — the watchlist will not grow much even at
  max drag"; the user asks "is the max width too small?"
- **Answer to the user's question (repo-validated 2026-10-05):** **No — the max-width formula is not too small.**
  `ui/dock_layout.watchlist_max_width(chart_area=1716)` returns **858px** (= `floor(0.50 × 1716)`), which is correct.
  The cap is not the problem.
- **Observed in repository (validated against source 2026-10-05; the Orchestrator's offscreen probe agrees):**
  - `ui/main_window.py:100–211` `[historical]` 2026-10-05 — builds `toolbar = QWidget()` with a `QHBoxLayout` of fixed-width controls
    (`symbol_input` 120, `tf_combo` 90, `mode_combo` 110, `sound_btn` 56, `ext_hours_btn` 80, `tz_combo` 110,
    `draw_combo` 110, `draw_set_combo` 140, `draw_delete_btn` 38, plus buttons/labels), giving it a
    **`minimumSizeHint` of ~1716px** at D19 report time (2026-10-05). **Re-measured 2026-10-14:** the toolbar has since gained controls (pop-out / footprint / depth / symbol-search, etc.), so its intrinsic minimum is now **~1965px offscreen** (offscreen value; platform/font dependent) — the figure illustrates the pinning mechanism, it is not a current constant.
  - `ui/main_window.py:217–223` `[historical]` 2026-10-05 — puts the toolbar **inside the central widget**:
    `central = QWidget(); vbox.addWidget(toolbar); vbox.addWidget(self.chart_panel); self.setCentralWidget(central)`.
    So the central widget's `minimumSizeHint` becomes ~1716px and `QMainWindow` refuses to shrink the central area
    below it.
  - Therefore the dock-area splitter has **no slack**: the watchlist is pinned at its minimum (150px; ~200 in the
    user's screenshot) and the right region is squeezed off-screen. **Both the D17 and D18 symptoms share this one
    root cause.**
  - Probe evidence (offscreen, toolbar visible): window 2078px → `centralWidget().width()` 1716,
    `centralWidget().minimumSizeHint().width()` 1716; central item 0 (toolbar) min hint 1716, item 1 (ChartPanel)
    min hint 88; after driving the watchlist to its cap the watchlist width stayed **150**; the right dock stayed 200
    but was pushed to the window edge.
- **Why review missed it (test-masking — part of the defect):** `tests/test_dock_widths_d17.py::_make_window`
  explicitly hides the toolbar (`toolbar.hide()`), and its own docstring admits the toolbar "pins the central widget
  and caps the left dock far below the 50% rule — masking the very behaviour under test."
  `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py` and
  `tests/test_dock_layout.py` do the same. The offscreen suite therefore exercised a window **unlike the real app**,
  so a real-app regression could not be caught. Removing this masking is part of D19.

**Decisions (B5–B6 answered 2026-10-05):**
- **B5 — toolbar behaviour when narrow (user-confirmed, verbatim: "Horizontal scroll / elide in place"):** the
  toolbar **stays inside the central widget** — it is **NOT** moved to a `QMainWindow` toolbar area (`addToolBar`)
  — and remains a **single ~36px row**, but its effective minimum width must **no longer pin the central widget**.
  The chosen fix is a **horizontal scroll / elide wrapper around the existing toolbar widget**: when the window is
  narrower than the toolbar's natural width, the controls are reached by **horizontal scrolling** (and/or labels
  elide) instead of holding the central widget at ~1716px. **All controls must remain reachable** via that
  scroll/elide affordance — no control becomes permanently unreachable. Options (b) wrap-to-multiple-rows,
  (c) compress/overflow menu, and (d) move the toolbar out of the central widget are **not adopted**.
- **B6 — watchlist cap (user-confirmed, verbatim: "Keep 50%"):** the cap **stays `floor(0.50 × chart_area)`** (B1
  stands). The cap constant (`watchlist_max_width` / `WATCHLIST_CAP_FRACTION`) and `AC-D13.1`/`AC-D17.1` are
  **unchanged** — the formula was never the problem; D19 fixes only the toolbar pinning. Raising the cap is **not
  adopted**.
- The acceptance criteria below are the **final** required outcome.

**Acceptance Criteria (Given/When/Then) — final (B5–B6 answered 2026-10-05):**
- **AC-D19.1 (real-app watchlist can reach its cap — cap unchanged at 50%, B6)** Given a shown window with the
  **toolbar visible** and large enough that `floor(0.50 × chart_area) > WATCHLIST_MIN_WIDTH`, When the user drags
  the watchlist handle to its maximum, Then the watchlist width reaches `floor(0.50 × chart_area)` (within the 1px
  re-issue tolerance) and is **not** pinned at `WATCHLIST_MIN_WIDTH`. (Measurable: in a toolbar-visible offscreen
  window, `watchlist_dock.width() > WATCHLIST_MIN_WIDTH` and
  `abs(watchlist_dock.width() - floor(0.50 × chart_area)) <= 1` after driving to cap.)
- **AC-D19.2 (real-app right dock fully visible)** Given a shown full-screen-sized window with the **toolbar
  visible**, Then the single right region is fully within the window — its left edge `>= chart-area right edge`, right
  edge `<= window right edge`, with a non-zero visible width (`AC-D18.1`), not squeezed off-screen.
- **AC-D19.3 (chart minimum preserved)** Given both docks driven toward their caps with the **toolbar visible**,
  Then `chart_area >= CHART_MIN_WIDTH` (400px).
- **AC-D19.4 (toolbar no longer pins the central widget; controls stay usable — B5 scroll/elide in place)** Given
  the toolbar is visible, Then (i) the toolbar stays **inside the central widget** as a **single ~36px row** (NOT
  moved to a `QMainWindow` toolbar area) wrapped so its **minimum width no longer pins the central widget**, and
  (ii) all its controls remain **reachable/usable** — directly at a wide window and via the **horizontal
  scroll/elide** affordance at the narrowest window in which the dock minima + chart minimum are feasible.
  (Measurable: `centralWidget().minimumSizeHint().width() <= CHART_MIN_WIDTH + WATCHLIST_MIN_WIDTH +
  RIGHT_DOCK_MIN_WIDTH` (i.e. the toolbar no longer dominates that minimum), the toolbar's laid-out height stays
  `<= ~40px` (one row), and every toolbar control is reachable at a narrow width — via scrolling/eliding if not
  directly visible.)
  - **Superseded by D20 (2026-10-06, B7–B8 answered):** the `<= ~40px` laid-out-height bound is **relaxed to a new ~52px container bound** so the toolbar can fit a dedicated horizontal-scrollbar lane below the ~36px content row and its labels are no longer clipped — see `AC-D20.1`/`AC-D20.2` and the supersession note below. The D19 **reachability** intent (toolbar stays inside the central widget, single content row, controls reachable via scroll/elide) is preserved and is **not** superseded.
- **AC-D19.5 (central widget can shrink)** Given the toolbar is visible, When the window is resized down toward the
  feasible minimum, Then `centralWidget().width()` decreases accordingly and does not remain pinned at the toolbar's intrinsic minimum width (~1716px at D19 report time; re-measured ~1965px offscreen on 2026-10-14 — see the note above).
- **AC-D19.6 (test-masking regression guard — REQUIRED)** Given the D17 and D18 acceptance tests, When they run,
  Then they exercise a **toolbar-visible** window (or otherwise reproduce the toolbar's real minimum-width
  constraint), so this exact regression cannot recur. (Measurable: the harness no longer hides the toolbar to
  sidestep the constraint; at least one D17 test and one D18 test **fail against the pre-fix code** with the toolbar
  visible and **pass after** the fix. The masking `toolbar.hide()` in `tests/test_dock_widths_d17.py`,
  `tests/test_dock_widths_d18.py`, `tests/test_dock_widths_d18_impl.py`, `tests/test_dock_d18_region.py` and
  `tests/test_dock_layout.py` must be removed or paired with a toolbar-visible variant.)
- **AC-D19.7 (regression)** Given the fix, Then the pre-existing suite remains green and the D13/D17/D18 criteria
  (`AC-D13.1`–`AC-D13.3`, `AC-D17.1`–`AC-D17.6`, `AC-D18.1`–`AC-D18.8`) hold **in a toolbar-visible window**.

**Edge Cases:**
- Window narrower than the toolbar's natural width → the toolbar scrolls horizontally / elides **in place** (B5,
  one ~36px row inside the central widget), never leaving a control permanently unreachable; the chart/dock minima
  rule still applies.
- Window so small that dock minima + chart minimum are infeasible → the chart minimum yields before the dock
  minimums (existing `plan_dock_widths` rule).
- Full screen (no window `resizeEvent` during a drag) → the live clamp must still bind (D17 `AC-D17.3`).
- Right region hidden/floating → the watchlist-only rule applies (existing `_right_dock_available` path).
- High-DPI / font scaling → the toolbar min hint may grow; the chosen mechanism must still allow the central widget
  to shrink (B5-dependent).

### D20 — Toolbar label descenders clipped by the horizontal scrollbar (height increase)
- **Area:** `ui/main_window.py` toolbar + D19 scroll wrapper (lines ~100–242); `tests/test_toolbar_scroll_d19.py`.
- **Status:** **clarified and finalised 2026-10-06 (B7–B8 answered).** Reported 2026-10-06; the fix keeps the
  toolbar **content row at ~36px** with the horizontal scrollbar in its **own reserved lane below** (total strip
  **~50–52px**), and the scrollbar is **as-needed** in that reserved lane. `AC-D20.1`–`AC-D20.6` are final.
- **Relation to D19 (recorded supersession — not a silent contradiction):** D19 (`AC-D19.4`) required the
  toolbar to stay a **single ~36px row** with a laid-out height `<= ~40px`, and B5 chose "horizontal
  scroll/elide in place". The D19 implementation sets **both** the toolbar widget and the `ToolbarScroll`
  QScrollArea to a **fixed 36px** (`ui/main_window.py:102`, `:233`, `[historical]` — D19 implementation snapshot; the content-row constant is now `ui/main_window.py::TOOLBAR_CONTENT_HEIGHT`, `:120`). Because the scroll area's horizontal
  scrollbar is laid out **within** that same 36px, it overlaps the bottom of the toolbar content, clipping
  label descenders. D20 **explicitly revises/relaxes** `AC-D19.4`'s `<= ~40px` height bound (see the
  supersession note on `AC-D19.4`); the D19 scroll/elide reachability behaviour and the D17/D18 criteria are
  otherwise unchanged. This is a **recorded supersession**, not a silent reopen.
- **Visual reference (ESC-004 gate):** the user supplied a screenshot (2026-10-06) of the running app's toolbar
  strip showing the horizontal scrollbar overlapping the label descenders (`Symbol`, `Load Chart`, etc.). It is
  accepted as evidence of the **reported state**. The **target height is a UI-visual size decision**; it was a
  blocking question (**B7**) and was **confirmed by the user on 2026-10-06** (verbatim: "Content row 36px +
  scrollbar lane (~52px total)"), so the size decision is now **user-confirmed** and A39 is **confirmed**, not
  provisional. The scrollbar-visibility choice (**B8**) was likewise **user-confirmed 2026-10-06** (verbatim:
  "As-needed in a reserved lane"). Gate: **CONFIRMED** (B7/B8 answered).
- **Reported (verbatim):** "UI Edit: see attachment. I want the height increased so that the label can be clearly
  read. current state: the bottom of the alphabets in the labels gets covered slightly by the horizontal scroll."
- **Observed in repository (validated against source 2026-10-06):**
  - `ui/main_window.py:100–102` `[historical]` 2026-10-06 — `toolbar = QWidget(); toolbar.setObjectName("MainToolbar");
    toolbar.setFixedHeight(36)`.
  - `ui/main_window.py:223–234` `[historical]` 2026-10-06 — `toolbar_scroll = QScrollArea()` (`objectName "ToolbarScroll"`, `NoFrame`,
    `setWidgetResizable(False)`, horizontal `ScrollBarAsNeeded`, vertical `ScrollBarAlwaysOff`,
    `setFixedHeight(36)`), wrapping the toolbar and added to the central `QVBoxLayout` (D19/B5).
  - The container is fixed at **36px** and the horizontal scrollbar is laid out within that 36px, so it
    **covers the bottom of the 36px toolbar content** — the label descenders. This is the reported defect.
  - Affected tests: `tests/test_toolbar_scroll_d19.py` asserts `wrapper.height() == 36` and
    `minimumHeight() == 36 and maximumHeight() == 36` (`T53-T04`, lines 199–200) and `toolbar.height() <= 40`
    (`T53-T02`, lines 130/156). Raising the height requires updating these assertions in lockstep.

**Decisions (B7–B8 answered 2026-10-06):**
- **B7 — target height / reconciliation with `AC-D19.4` (user-confirmed, verbatim: "Content row 36px + scrollbar
  lane (~52px total)"):** keep the toolbar **content row at ~36px** and give the horizontal scrollbar its **own
  reserved lane below** the content, so the **total strip grows to ~50–52px**. The content row itself does **not**
  grow and the strip does **not** grow to ~60px. This **supersedes/relaxes `AC-D19.4`'s `<= ~40px` bound** to a
  new **~52px container bound** (recorded on `AC-D19.4`). Options (b) (grow the content row) and (c) (a user-named
  total height) are **not adopted**.
- **B8 — scrollbar-lane visibility (user-confirmed, verbatim: "As-needed in a reserved lane"):** **reserve the
  scrollbar lane** and show the horizontal scrollbar **only when the toolbar content overflows** (the same
  as-needed behaviour as today), so it **never overlaps the labels**. Because the lane is reserved, the strip's
  total height stays ~50–52px in both states; only the scrollbar widget's visibility changes with overflow.
  Options (b) (always-visible scrollbar) and (c) (overlay / auto-hiding macOS-style scrollbar) are **not adopted**.
- The acceptance criteria below are the **final** required outcome.

**Acceptance Criteria (Given/When/Then) — final (B7–B8 answered 2026-10-06):**
- **AC-D20.1 (labels fully readable; no descender clipped by the scrollbar)** Given a shown window with the
  toolbar visible, When the toolbar renders (whether the horizontal scrollbar is shown or hidden), Then every
  toolbar label's glyphs (including descenders) are **fully visible** — no pixel of a label's text bounding box
  is overlapped by the horizontal scrollbar or clipped by the container — and the toolbar content remains a
  **single row** (not wrapped).
  - Measurable: in a toolbar-visible offscreen window, for every toolbar `QLabel`/button text, the text's
    bounding rect lies fully within the toolbar's visible content area and does **not** intersect the
    horizontal scrollbar's geometry (assert in both the overflow/shown and non-overflow/hidden states).
- **AC-D20.2 (height supersession — ~52px total, content row ~36px)** Given the fix, Then the toolbar strip's
  laid-out height is **~50–52px** total, composed of the **content row at ~36px** plus a **reserved horizontal-
  scrollbar lane below** it; the **content row does not grow** and the strip does **not** reach ~60px.
  `AC-D19.4`'s `<= ~40px` bound is **explicitly superseded** by this criterion (to a ~52px container bound)
  rather than silently contradicted.
  - Measurable: the `ToolbarScroll` container height is `<= ~52px` and `>= ~50px`; the toolbar content widget
    height remains `~36px` (unchanged from D19); the reserved scrollbar lane is present below the content.
- **AC-D20.3 (scrollbar as-needed in its reserved lane; B8)** Given the fix, When the toolbar content fits
  (wide window), Then the horizontal scrollbar is **hidden** but its **lane remains reserved** (the strip height
  is unchanged); When the toolbar content overflows (narrow window), Then the horizontal scrollbar is **shown in
  its reserved lane below** the content and **never overlaps** the labels.
  - Measurable: at a wide width `horizontalScrollBar().isVisible()` is `False` and the strip height is still
    ~50–52px; at a narrow width it is `True`, sits in the lane below the content row, and `AC-D20.1` still holds.
- **AC-D20.4 (D19 behaviour preserved)** Given the fix, Then the D19 scroll/elide reachability holds: at a
  narrow window the toolbar scrolls horizontally and **all controls remain reachable**; at a wide window every
  control is directly visible. (Measurable: `wrapper.horizontalScrollBar().maximum() > 0` at a narrow width;
  every control is a descendant of the scroll content.)
- **AC-D20.5 (single row, no wrap; stays inside the central widget)** Given any window width, Then the toolbar
  **content** stays a single row (not wrapped onto multiple lines) and remains inside the central widget (not
  moved to a `QMainWindow` toolbar area); only the horizontal scrollbar occupies the lane below it.
- **AC-D20.6 (D17/D18 unaffected; regression)** Given the fix, Then the D17/D18 criteria hold in a
  toolbar-visible window and the chart minimum is preserved (only vertical space changes — the chart is slightly
  shorter — not the horizontal dock model), and the pre-existing suite remains green, with the D19 height
  assertions (`tests/test_toolbar_scroll_d19.py::T53-T04` `height() == 36`, `T53-T02` `<= 40`) updated in lockstep
  to the B7-confirmed ~50–52px container / ~36px content target (never left contradicting D20).

**Edge Cases:**
- High-DPI / font scaling → the scrollbar and text heights may grow; the lane must be derived so labels are
  still not clipped (reserved lane, not an overlay).
- Window narrow enough to show the scrollbar vs wide enough to hide it → labels must be unclipped in **both**
  states; the lane is **reserved** so the strip height stays ~50–52px whether the scrollbar is shown or hidden.
- Extremely small window where dock minima + chart minimum are infeasible → the existing chart-minimum rule
  still applies; the toolbar height change does not alter the horizontal model.
- Right region hidden/floating → the watchlist-only rule applies (unchanged).

### D21 — Batch 15 (2026-10-06): 13 reported UI defects/issues (D21.1–D21.13) — CLARIFIED AND FINALISED 2026-10-06

> Reported by the user in one message on 2026-10-06 after D20 was built and green (commit `04397d9`, 585
> tests). Each sub-defect carries its own Given/When/Then criteria and edge cases. **D1–D20 are not reopened.**
> All five blocking questions **B9–B13 were answered by the user on 2026-10-06** (`open_questions.md`); every
> criterion below is **final** (no *provisional* wording remains). **D21.4 supersedes the display part of
> `AC-D16.3`** (recorded explicitly below and on `AC-D16.3`). D21 is **ready for Plan**.

#### VIS-D21 — Shared visual conventions (defined once, referenced by D21.7/D21.8/D21.11/D21.12/D21.13)
- **VIS-D21.1 "Hidden/off" diagonal strike-through (CONFIRMED 2026-10-06):** when a toggle/panel is in its
  hidden/off state, its label/button is rendered with a single straight **diagonal line from the top-left
  corner to the bottom-right corner** of the label/button's text area (a "crossed-out" look), clearly visible
  against the button background. Applied by D21.11 (watchlist hidden), D21.12 (volume pane hidden) and D21.13
  (a right panel hidden).
- **VIS-D21.2 "Active/selected" button highlight (CONFIRMED 2026-10-06):** a button currently active/selected
  (e.g. Alarm Mode on, a toggled-on toolbar toggle, or a button whose popup is open) MUST be visually
  distinguishable from its inactive state by a **persistent highlight** (a distinct filled background and/or
  border), applied while active and removed when inactive. Applied by D21.7 and D21.8.
- **Visual reference (ESC-004 gate) — CONFIRMED 2026-10-06:** the user described the diagonal convention and
  the "highlight" in the D21 report and **confirmed both conventions on 2026-10-06** (B12 "As recommended",
  plus the D21.7/D21.8/D21.12 answers). A41 (active highlight) and A42 (diagonal line) are therefore
  **user-confirmed conventions**; the exact colours/line width are implementation detail, while the outcome
  (a visible diagonal line / a persistent, distinguishable active highlight) is the testable requirement.

#### D21.1 — Volume Y-axis can be dragged below 0
- **Area:** `ui/chart_panel.py` volume ViewBox / `_ensure_volume_range` (`:885–896`).
- **Status:** clarified — criteria final 2026-10-06.
- **Reported (verbatim):** "current state: user is able to drag volume y-axis to below 0. fix: user should not be allowed to drag the volume y-axis below 0".
- **Observed in repo:** the volume ViewBox is linear and `_ensure_volume_range` writes `setRange(yRange=(0, nice), padding=0)`, but no code clamps the **mouse y-drag**; pyqtgraph's default ViewBox interaction lets the user drag the y-range below 0.
- **AC-D21.1.1** Given the volume pane is visible, When the user drags the volume Y-axis (or otherwise changes the volume Y range by mouse), Then the volume Y minimum **never goes below 0** at any time.
  - Measurable: after any user y-interaction, `volume_plot.getViewBox().viewRange()[1][0] >= 0` (float tolerance), and no volume-axis tick below 0 is rendered.
- **Edge Cases:** repeated downward drag stays at 0; zoom-out keeps min 0; all-zero volumes keep `[0, 100]` (D8); symbol/timeframe switch re-applies min 0; Y-drag must remain usable for the max.

#### D21.2 — Volume Y max does not update on zoom
- **Area:** `ui/chart_panel.py` `_recompute_vol_max` / `_ensure_volume_range` / `_widen_volume_for` (`:876–905`).
- **Status:** clarified — criteria final 2026-10-06.
- **Reported (verbatim):** "when user zooms in the volume y-axis does not update the max range. fix: volume y-axis does not update the max range to show the volume candles appropriately. min should always be zero, max should be 10 % above the max volume candle visible in the volume pane".
- **Observed in repo:** the ceiling is derived from the **whole** cached bar list (`_vol_max = max over _bars`) and is **only-widen** (`if force or nice > self._volume_nice_max`), so zooming into a lower-volume region never lowers the max and the bars appear squashed; the axis max is a D8 "nice" value, not `1.10 × visible max`.
- **AC-D21.2.1** Given the volume pane is visible and bars are loaded, When the visible x-range changes (zoom in/out, pan, magnifier area-zoom), Then the volume Y range is `[0, 1.10 × max_volume_visible]`, where `max_volume_visible` is the largest volume of the bars whose x lies within the currently visible x-range; the min is always `0`.
  - Measurable: after setting a view x-range, `viewRange()[1] == (0, approx(1.10 * max(visible volumes)))`.
- **Supersession note (recorded):** D21.2 **supersedes** D8's "dynamic nice **max**" for the volume **range ceiling** (the ceiling is now `1.10 × visible max`) and **supersedes ESC-007's only-widen rule** for zoom; ESC-007's core intent (a growing forming bar must not be clipped) is preserved by recomputing on bar updates as well. D8's linear scale, no-negatives, min-0 and price-coloured bars all remain.
- **Edge Cases:** zoom-out to all bars → `1.10 ×` global max; all-zero visible → D8 `[0, 100]` floor; a spike just outside the view does not inflate the max; intra-bar growth still widens (ESC-007 preserved); panning recomputes; empty load.

#### D21.3 — Ext Hours button label does not change with RTH selection
- **Area:** `ui/main_window.py` `ext_hours_btn` (`:160–165`) + `_on_ext_hours_toggled` (`:1443–1449`).
- **Status:** clarified — criteria final 2026-10-06.
- **Reported (verbatim):** "'Ext hours' button in the top does not change based on the user selection. Fix: 'Ext hours' button in the top should change to RTH if regular trading hours is selected".
- **Observed in repo:** the button is a fixed-text checkable `QPushButton("Ext Hours")`; its text never changes.
- **AC-D21.3.1** Given the toolbar is visible, When Ext Hours is ON (checked), Then the button label reads `Ext Hours`; When the user toggles it OFF (regular trading hours), Then the button label reads `RTH`.
  - Measurable: `ext_hours_btn.text() == "Ext Hours"` when checked and `== "RTH"` when unchecked; the label updates immediately on toggle and reflects the state after a chart reload.
- **Edge Cases:** the button's fixed 80px width must fit both labels; the tooltip still explains the toggle; toggling triggers a chart reload (existing behaviour retained).

#### D21.4 — Empty space when market is not open (collapse non-trading time) — FINAL (B9)
- **Area:** x-axis / bar layout (`ui/chart_panel.py` `_refresh_candles`, `_custom_date_axis`), session handling (`services/session_service.py`, `ui/overlays/session_overlay.py`), Ext Hours toggle.
- **Status:** **clarified and finalised 2026-10-06 (B9 answered).** Former feature suggestion **FS7**, now explicitly requested and in scope. **Supersedes the display part of `AC-D16.3`** (see supersession note).
- **Reported (verbatim):** "Current state: empty space when market is not open. Fix: do not plot empty space (i.e. collapse it) when market is not open for the plotted security; also do not plot empty space (i.e. collapse it) if user has selected RTH".
- **Observed in repo:** the x-axis is linear in wall-clock time (`_custom_date_axis`), so overnight/weekend/holiday spans between trading sessions render as empty horizontal space; with Ext Hours OFF only RTH bars are fetched, but the overnight/weekend gaps remain.
- **AC-D21.4.1 (final — B9)** Given an **intraday** timeframe (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`) with bars loaded, When the chart renders, Then the **gaps between trading sessions** (overnight, weekend, holiday) are **not plotted as empty space**: the plotted bars are **contiguous** across consecutive sessions (no empty x-interval between them), while normal inter-bar spacing **within** a session is preserved.
- **AC-D21.4.2 (final — B9)** Given the timeframe is `1 day`, Then collapse is a **no-op** — the chart already renders one bar per trading day and no between-session gap is plotted.
- **AC-D21.4.3 (final — B9)** Given **RTH selected** (Ext Hours OFF), Then only RTH bars are shown and **all non-RTH time collapses**; Given Ext Hours ON, Then the D1 pre/post-market bands still render for the sessions shown.
- **AC-D21.4.4 (final)** Given a genuine **trading-session data hole** (D16), Then it is still a defect — collapse is a **display** change only; it does not fabricate or drop trading-session bars and does not weaken D16's backfill/no-silent-hole requirements (`AC-D16.1`/`AC-D16.4`).
- **Supersession note (recorded, not silent):** `AC-D16.3` currently requires genuine closures to "stay empty and are not filled, compressed, or interpolated". D21.4 **supersedes the display part** of `AC-D16.3` (between-session closures may now be collapsed for display); `AC-D16.1`/`AC-D16.4` (no silent trading-session holes) are unchanged.
- **Edge Cases:** weekend/holiday/half-day; DST; the `1 day` timeframe is a no-op (B9); drawings, session bands and alarm lines must remain correctly positioned after collapse; the x-axis date labels must stay readable; a single session with no closure; a trading-session hole must not be collapsed away; only **between-session** gaps collapse — a partial/half-day missing afternoon is **not** collapsed (B9 option (a), not (b)).

#### D21.5 — Watchlist columns fixed (reorder / add / remove via right-click) — FINAL (B10)
- **Area:** `ui/watchlist_panel.py` (table, `HEADERS`, `COL_*`), persistence (`data/db.py` / QSettings).
- **Status:** **clarified and finalised 2026-10-06 (B10 answered).**
- **Reported (verbatim):** "current state: columns in the watchlist are fixed. fix: allow the user the re-arrange their location and allow the user to add and remove columns. A right click on the columns should open a popup to add or remove or rearrange columns."
- **Observed in repo:** the table has a fixed 7-column schema (`HEADERS = ["Symbol","Last","Bid","Ask","Chg","Chg %","Vol"]`) with fixed resize modes; there is no column configuration.
- **AC-D21.5.1** Given the watchlist is visible, When the user right-clicks a column header, Then a popup opens offering to **add**, **remove**, and **rearrange** columns.
- **AC-D21.5.2 (B10)** Given the popup, Then the **addable set is the existing 7 columns** (`Symbol, Last, Bid, Ask, Chg, Chg %, Vol`) — "add" means **re-showing a previously removed column** (no new data fields are introduced).
- **AC-D21.5.3 (B10)** Given a column is to be removed, Then the **`Symbol` column cannot be removed** (it always remains in the layout).
- **AC-D21.5.4 (B10)** Given a changed column set/order, Then the table updates immediately to the chosen columns in the chosen order, each cell value remains bound to the correct field, and the layout is **persisted across restarts** (restored on launch).
- **Edge Cases:** all other columns removed → only `Symbol` remains; Symbol-column removal is blocked; duplicate columns not allowed; right-click on an empty header area; live ticks continue after reorder; D14 double-click-anywhere still loads the chart after reorder; a symbol added after reorder binds to the new layout.

#### D21.6 — Volume panel cannot grow enough in height — FINAL (B11)
- **Area:** `ui/chart_panel.py` `volume_plot.setMaximumHeight(120)` (`:288`) and `_splitter.setSizes([600, 120, 120])` (`:320`).
- **Status:** **clarified and finalised 2026-10-06 (B11 answered).**
- **Reported (verbatim):** "current state: the volume panel does not increase much in height. fix: allow the user to increase the volume panel height by at least 200% more".
- **Observed in repo:** `volume_plot.setMaximumHeight(120)` caps the volume pane at 120px, so the vertical splitter cannot grow it beyond 120px.
- **AC-D21.6.1 (final — B11)** Given the volume pane is visible, When the user drags the price/volume splitter, Then the volume pane can grow to **at least 360px** (3× the current 120px maximum cap), and the **price pane keeps a minimum of ~200px** (the oscillator pane is unaffected).
  - Measurable: the volume pane height can reach `>= 360px` in an offscreen window tall enough, and the price pane height stays `>= ~200px`.
- **Edge Cases:** very short window (price minimum wins and the volume target yields); oscillator pane also present; volume hidden then shown; splitter restore; no regression to the price pane minimum; interaction with D10.

#### D21.7 — No visible "active" state for clicked buttons
- **Area:** `ui/main_window.py` toolbar buttons (`studies_btn`, `alarms_btn`, `alarm_mode_btn`, `sound_btn`, `dom_btn`, `ext_hours_btn`).
- **Status:** clarified — criteria final 2026-10-06 (visual style = `VIS-D21.2`, A41 confirmed 2026-10-06).
- **Reported (verbatim):** "it is difficult to identify which buttons are active selected example: If studies is clicked on by the user, the studies pop up comes up, but user is not able to tell that the studies button was clicked. fix: when the user clicks a button, highlight the button in some way such that it is visible that the button is has been clicked".
- **Observed in repo:** `studies_btn`/`alarms_btn` are plain buttons with no active style; toggle buttons rely on Qt's default checked look, which the user reports as indistinguishable.
- **AC-D21.7.1** Given a toolbar button that represents an active/selected state (a checkable toggle that is ON, or a button whose popup is currently open), When that state is active, Then the button shows a **persistent, clearly visible highlight** distinct from its inactive state (per `VIS-D21.2`), removed when the state ends.
  - Measurable: for each such button the active style differs from the inactive style and is applied while active / removed while inactive.
- **Edge Cases:** multiple toggles active at once; theme/contrast; the Studies/Alarms highlight persists while the dialog is open and clears when it closes; highlight visible at any scroll position in the D19 wrapper.

#### D21.8 — Alarm Mode not highlighted; status message disappears too soon
- **Area:** `ui/main_window.py` `alarm_mode_btn` + `_on_alarm_mode_toggled` (`:1030–1037`); status bar.
- **Status:** clarified — criteria final 2026-10-06 (visual style = `VIS-D21.2`, A41 confirmed 2026-10-06).
- **Reported (verbatim):** "current state: The alarm mode when clicked does not get highlighted, and the message at the bottom left, alarm mode, click… it disappears within a few seconds. Fix: the alarm mode button should be highlighted when it is active, and the message at the bottom left, should remain till the alarm mode has been switched off."
- **Observed in repo:** `_on_alarm_mode_toggled` shows `status_bar.showMessage(..., 4000)` (4s timeout) and relies on default checked styling.
- **AC-D21.8.1** Given the toolbar is visible, When Alarm Mode is activated, Then the Alarm Mode button shows the persistent active highlight (`VIS-D21.2`).
- **AC-D21.8.2** Given Alarm Mode is active, Then the status-bar message ("Alarm mode: click the chart to place a price alarm.") **remains visible with no timeout** until Alarm Mode is switched off; When Alarm Mode ends (button toggled off, an alarm is placed, or the mode is otherwise exited), Then the message is cleared/replaced.
  - Measurable: while active the alarm-mode text is still shown after > 4s; after deactivation it is no longer shown.
- **Edge Cases:** placing an alarm exits Alarm Mode → message clears; selecting a drawing tool exits Alarm Mode → clears; chart reload while Alarm Mode active; the persistent message must not permanently mask other status messages after deactivation.

#### D21.9 — Alarm popup cannot edit an active/set alarm — FINAL (B13)
- **Area:** `ui/alarm_dialog.py` (table, `_append_row`, `AlarmStore`).
- **Status:** **clarified and finalised 2026-10-06 (B13 answered).**
- **Reported (verbatim):** "Current state: the alarms pop up does not allow to edit the alarm once active/Set. Fix: … At the row level for each alarm, there should be a small edit button clickable on the right side end of the pop up, make the width of the note column big enough to fill till end of the pop up. If edit is clicked, the price, condition, sound and note should be allowed to be changed."
- **Observed in repo:** the alarm table has 6 fixed columns (`Price, Condition, Active, Triggered, Sound, Note`) and no Edit affordance; alarms can only be added/rearmed/muted/deleted.
- **AC-D21.9.1** Given the alarm popup is open with at least one alarm, Then each alarm **row** has a small **Edit** button at the right-hand end of the row.
- **AC-D21.9.2** Given the Note column and the Edit button, Then the Note column is widened to fill the popup width up to the Edit button (to the end of the popup; no large empty gap between the note text and the Edit button).
- **AC-D21.9.3 (B13)** Given the user clicks a row's Edit button, Then a small **edit dialog** opens for that alarm allowing **price, condition, sound, and note** to be changed, with **Save / Cancel**; **Save persists immediately** and the change is reflected on the chart / alarm badge; **Cancel discards**.
  - Measurable: after Save, `AlarmStore.load(symbol)` returns the updated values.
- **AC-D21.9.4 (B13)** Given the alarm is a **triggered/set** alarm, Then it **may still be edited** and the edit **keeps its state** — editing does not re-arm, reset, or silently disable it.
- **Edge Cases:** editing a triggered alarm keeps its state (B13); invalid price; Cancel discards; editing while the chart is live; empty note; the Edit button stays reachable when the table scrolls.

#### D21.10 — Alarm setup is not "smart" (price from clicked level, yellow dashed line, intuitive condition) — FINAL (B13)
- **Area:** `ui/main_window.py` `_on_alarm_create_requested` (`:1502–1509`) / `_open_alarm_dialog`; `ui/alarm_dialog.py`; `ui/alarm_overlay.py`; `ui/chart_panel.py`.
- **Status:** **clarified and finalised 2026-10-06 (B13 answered).**
- **Reported (verbatim):** "Current state: when user clicks on alarm mode and th alarm pop-up comes up the setup to add the alarm is not smart. Fix: the price should be taken directly from the level. click on by the user that level should be highlighted by a – yellow line so that user is able to see it if the user changes the price, the dash line should move up and down along with the price. The condition should be intuitive, as in if current price is higher than the alarm price, then the condition should be cross below, if the current price is below the alarm price then the condition should be cross above."
- **Observed in repo:** clicking the chart in alarm mode emits `create_requested(price)` → `_on_alarm_create_requested` opens the modal `AlarmDialog` with `last_price=price`, which prefills `price_input`; there is no chart line preview and the condition is not auto-selected.
- **AC-D21.10.1** Given the user activates Alarm Mode and clicks a price level on the chart, Then the alarm popup opens with the **price pre-filled from that clicked level**.
- **AC-D21.10.2 (B13)** Given the alarm popup is open from a chart click, Then a **yellow dashed horizontal preview line** is drawn on the chart at the selected price level and is visible **while the popup is open**.
- **AC-D21.10.3 (B13)** Given the yellow dashed line and the popup, When the user changes the price in the popup, Then the dashed line **moves up/down to follow the price** live.
- **AC-D21.10.4 (B13)** Given the popup closes, Then the preview line is **removed**; after **Add**, the real alarm line **replaces** the preview at the alarm's price.
- **AC-D21.10.5 (B13)** Given the popup opens, Then the condition defaults **only at open** to **Cross Below** when the current price is **higher** than the alarm price and **Cross Above** when the current price is **lower** than the alarm price; the default is **user-overridable**; when the **current price is unknown**, the default is **Cross Above**.
  - Measurable: `last_price=100`, alarm price `110` → `Cross Below`; alarm price `90` → `Cross Above`; unknown current price → `Cross Above`.
- **Edge Cases:** current price unknown/None → `Cross Above` (B13); the user overrides the auto-selected condition (allowed); price equal to current price (boundary); popup opened from the Alarms button rather than a chart click (no preview line; uses the last chart price); popup closed removes the preview line; repeated opens; line colour/width per A44.
- **Note:** the dialog is currently **modal** (`exec()`), and the preview line is drawn on the chart behind it — B13 confirms this visibility/lifecycle.

#### D21.11 — No button to hide the watchlist; "Watchlist" header appears twice — FINAL (B12)
- **Area:** `ui/main_window.py` watchlist dock title (`:258`) + `ui/watchlist_panel.py` header strip (`:117–124`).
- **Status:** **clarified and finalised 2026-10-06 (B12 answered).**
- **Reported (verbatim):** "current state: there is no button to hide the watchlist, also, the watchlist header is mentioned twice in the UI. Screenshot attached. Fix: the label watch list, besides the yellow – – should be deleted. and the watch list besides the red – – should be kept, the kept label should be turned into a button which user can click to show or hide the watch list. If watch list is hidden, that label should be updated to watch list over which there is a diagonal line crossing from top left to right bottom."
- **Observed in repo** `[historical]` 2026-10-06 (pre-D21.11 state): two "Watchlist" texts existed — the `QDockWidget("Watchlist")` **title bar** (`main_window.py:258`) and the `WatchlistPanel` internal **header_bar** (`ui/watchlist_panel.py::WatchlistPanel.header_bar`, cited `:122`).
- **AC-D21.11.1 (B12)** Given the app is running, Then exactly **one** "Watchlist" label is shown — the **in-panel header label** is **kept** and turned into a **clickable toggle button**, and the duplicate **dock title bar** is **deleted**.
- **AC-D21.11.2 (B12)** Given the watchlist is hidden via that button, Then the retained button **stays visible** (it must not disappear with the dock) and is rendered with the `VIS-D21.1` diagonal strike-through; clicking it again shows the watchlist (strike removed).
- **AC-D21.11.3 (B12)** Given the watchlist is hidden/collapsed, Then the collapsed state still shows the button.
- **Edge Cases:** collapsed-width geometry; D14 double-click still works when shown; width persistence (D13) when re-shown; floating watchlist; the D17/D18 width model unaffected when hidden; the deleted dock title means the in-panel button is the retained affordance (see DG37).

#### D21.12 — Volume button does not change when the volume pane is hidden
- **Area:** `ui/chart_panel.py` `_volume_toggle` (`:327–335`) + `_on_volume_toggled` (`:422–434`).
- **Status:** clarified — criteria final 2026-10-06.
- **Reported (verbatim):** "current state: there is no change to the volume hide button if volume panel is hidden. fix: if volume is hidden, then the volume hide show button. should be updated to volume over which there is a diagonal line crossing from top left to right bottom."
- **Observed in repo:** the checkable text button `Volume` toggles visibility but its label/appearance does not change when unchecked (it only loses the subtle checked background).
- **AC-D21.12.1** Given the volume pane is hidden (toggle unchecked), Then the `Volume` button is rendered with the `VIS-D21.1` diagonal strike-through; When the volume pane is shown (checked), Then the strike-through is removed.
- **Edge Cases:** default state visible (no strike); strike visible in the real app and offscreen; D10 placement unchanged; the button remains clickable while struck.

#### D21.13 — Cannot hide Active Trader / Account Summary panels; collapse behaviour — FINAL (B12)
- **Area:** `ui/main_window.py` right dock region (`:295–337`) + `ui/active_trader_panel.py` + `ui/active_portfolio_panel.py` (`summary_label`, `:68`).
- **Status:** **clarified and finalised 2026-10-06 (B12 answered).**
- **Reported (verbatim):** "Current state: user is unable to hide the active trader and account summary panels. fix: change the active trader label to active trader button, if a user clicks on the active trader button then the panel should be hidden. Change the account summary label to account summary button, if you set clicks on account summary button, then the account summary panel should be hidden. Is both the active trader panel and account summary panel are hidden, then the should call apps completely to the right and only occupy the width required to show the buttons. If only one panel is hidden and the other panel is open among active trader and account summary, then the hidden panel should collapse in height, and only occupy the space required to display the button. The other panel should expand to cover the space vacated by the hidden panel. If any panel is hidden, active trader or account summary that particular button should have a diagonal line crossing from top left to right bottom."
- **Observed in repo:** the right dock is one region containing `ActiveTraderPanel` (tabs) and `ActivePortfolioPanel` (whose first widget is `summary_label = QLabel("Account summary — disconnected")`); neither has a hide button; the region's title bar reads "Active Trader".
- **AC-D21.13.1 (B12)** Given the right dock is visible, Then **"Active Trader" = the right dock's title bar** and **"Account Summary" = the portfolio's summary label**, and **both become toggle buttons**: the Active Trader button hides/shows the Active Trader panel, and the Account Summary button hides/shows the Account Summary (portfolio) panel.
- **AC-D21.13.2 (B12)** Given **one** of the two panels is hidden, Then that panel collapses **in height** to just its button, and the other panel **expands** to fill the vacated vertical space.
- **AC-D21.13.3 (B12)** Given **both** panels are hidden, Then the right dock collapses **horizontally** to the minimum width required to show the two buttons (the chart reclaims the width).
- **AC-D21.13.4 (B12)** Given a panel is hidden, Then its button shows the `VIS-D21.1` diagonal strike-through; when shown, the strike is removed.
- **Edge Cases:** both shown (default); one hidden then the other; re-show restores; the collapsed right dock must not break the D17/D18 chart-minimum rule (`_apply_dock_widths`); the DOM button (`_on_dom_toggled`) hides the whole region — reconcile with per-panel hide; floating region; ladder/portfolio content sizing after expansion; the dock title bar is the Active Trader button, so its drag/hide affordance must still work (see DG38).

### D22 — In-app "Add symbol" / "Remove symbol" affordance on the Watchlist (NEW FEATURE) — CLARIFIED AND FINALISED 2026-10-07
- **Area:** `ui/watchlist_panel.py` (header strip + add/remove affordances + add/remove path), `ui/main_window.py`
  (`_restore_watchlist`, connection-gated wiring, persistence), `data/db.py` (`get_watchlist`/`set_watchlist`),
  `ibkr/` (new contract-details request/callback), `ibkr/contracts.py::get_contract_for_symbol`.
- **Status:** **CLARIFIED AND FINALISED 2026-10-07 (B14–B16, incl. B15a/B15b/B16b, answered).** This is a **new
  feature**, not a defect; D1–D21 are **not** reopened.
- **Visual reference (ESC-004 gate):** **SATISFIED BY EXPLICIT USER DECISION (2026-10-07).** The user chose the
  affordance/placement (**B15a**: a `+` button on the watchlist header strip plus a right-click "Add symbol…", and a
  "Remove symbol" entry) and the input surface (**B15b**: a small modal dialog). No screenshot artifact was supplied;
  as with `VIS-D21` (A41/A42), the exact styling is an implementation detail while the **placement/behaviour** the
  user named is the testable requirement (see A48).
- **Reported (verbatim context):** "can you tell me how to add tickers to the watchlist" — and, when told there is no
  in-app way, the user chose to start this requirements run to specify an in-app add/remove affordance.
- **Observed in repository (validated against source 2026-10-07; graphify used for the initial map, source is
  authoritative):**
  - `ui/watchlist_panel.py::WatchlistPanel` has a 28px `header_bar` whose only control is the D21.11 "Watchlist"
    `DiagonalStrikeButton` (`header_button`); the table's **column** header has the D21.5
    `customContextMenuRequested` → `_on_header_context_menu` (add/remove/rearrange **columns**). There is **no**
    add-symbol affordance anywhere on the panel. `header_bar` is set as the dock's title bar
    (`ui/main_window.py:303` when written; now `setTitleBarWidget(self.watchlist_panel.header_bar)` — `ui/main_window.py:400`).
  - `WatchlistPanel.add_symbol(symbol, contract)` appends a row and calls `md_manager.req_mkt_data(contract)`; it
    **early-returns when `_md_manager` is None** and does **not** persist anything. `clear()` cancels subscriptions
    and empties the table (called on disconnect, `ui/main_window.py::MainWindow._on_disconnected`; cited `:2107`, now `:1546` — indicative). There is **no** `remove_symbol` helper.
  - `ui/main_window.py::_restore_watchlist` reads `db.get_watchlist()`, seeds `DEFAULT_WATCHLIST` via
    `db.set_watchlist(symbols)` **only when the DB list is empty**, then calls `add_symbol` per symbol; it runs on
    `_on_connected` only. `_on_disconnected` sets `load_btn` disabled and does not restore the panel until reconnect.
  - `data/db.py::get_watchlist() -> [(symbol, category)]` (ordered by `sort_order`); `set_watchlist(symbols,
    category="EQUITIES", sort_order=None)` **replaces the whole list** (DELETE + INSERT). The `watchlist` table is
    `(symbol TEXT PRIMARY KEY, category TEXT NOT NULL, sort_order INTEGER NOT NULL)`. There is **no**
    `add_watchlist_symbol` / `remove_watchlist_symbol` helper today.
  - `ibkr/contracts.py::get_contract_for_symbol(sym)` builds a stock contract for **any** string (only a small
    `FUTURES_SCHEDULE` set is special-cased); it performs **no IBKR lookup and raises no error** for an unknown
    symbol. **There is no `reqContractDetails` request and no `contractDetails` callback anywhere in the codebase**
    — the live-validation requirement (B16) therefore needs a **new** IBKR request + callback path (see DG43).
  - The toolbar `symbol_input` + `Load Chart` load a chart but do **not** add to the watchlist.
- **Requirements (final):**
  - **Add affordance/placement (B15a):** a small **`+` button on the watchlist header strip** next to the
    "Watchlist" collapse toggle, **and** a **right-click "Add symbol…"** entry on the watchlist header strip. The
    affordance must **not** shadow the D21.5 column-header popup and must **not** remove or replace the D21.11
    collapse toggle.
  - **Input surface (B15b):** invoking the add affordance opens a **small modal input dialog** (QInputDialog-style)
    with a text field and **OK/Cancel**; OK confirms, Cancel/Esc aborts with no change.
  - **Normalisation + guards:** trim + uppercase the input; **reject empty/whitespace-only** input (no row, no
    persistence, message); treat a **case-insensitive duplicate** of an existing watchlist symbol as a **no-op with
    a message** (no duplicate row, no extra subscription, no DB change).
  - **Live validation before add (B16):** for a non-empty, non-duplicate symbol with IBKR **connected**, the add
    performs a **live IBKR contract lookup** (e.g. `reqContractDetails`) before adding. On **success** (IBKR resolves
    at least one matching contract) the row is appended, the live subscription requested, and the symbol persisted.
    On **failure/unresolvable** (no contract, an IBKR error, or a bounded timeout) the add is **rejected with an
    error surfaced to the user**, and **nothing is added, subscribed, or persisted**. The lookup may be
    **asynchronous** — the requirement is the observable outcome (added on success, rejected on failure), not the
    async mechanism; the UI must not hang indefinitely (bounded wait).
  - **Require connection (B16b):** adding is **disallowed while IBKR is disconnected** — the add affordance
    reflects/denies this (disabled, and/or the confirm is refused with a message); nothing is added, subscribed, or
    persisted while disconnected.
  - **Remove (B14):** a per-row delete affordance **and/or** a right-click **"Remove symbol"** entry on the
    watchlist row removes that symbol: its live subscription is **cancelled**, the row is removed, and the removal is
    **persisted**. (Exact delete-control placement/styling is Plan/Build's call; the outcome is fixed.) Reordering is
    **not** in scope.
  - **Persistence:** the symbol list (adds and removes) is **persisted across restarts** through the existing SQLite
    `watchlist` table (`get_watchlist`/`set_watchlist`); the mechanism (replace-all `set_watchlist` with the full
    desired list vs new add/remove helpers) is **Plan's call** — the requirement is the persisted outcome. The D21.5
    **column** layout (QSettings `watchlist/columns`) is separate and unaffected.
  - **Non-regression:** the D21.5 column-header popup, the D21.11 collapse toggle, the D14 double-click row-to-load,
    and the D21.13 right-dock behaviour all remain unchanged.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D22.1 (add affordance + placement — B15a)** Given the watchlist is visible, Then a small **`+` button** is
    present on the watchlist header strip next to the "Watchlist" toggle **and** a right-click on the watchlist
    header strip offers an **"Add symbol…"** entry; neither shadows the D21.5 column-header popup nor removes the
    D21.11 collapse toggle.
  - **AC-D22.2 (modal input — B15b)** Given the user invokes the add affordance, Then a **small modal dialog** with a
    text field and **OK/Cancel** opens; **OK** confirms the entered symbol, **Cancel/Esc** closes it with no change.
  - **AC-D22.3 (normalisation + empty/duplicate guards)** Given input with surrounding whitespace or lower-case
    (e.g. `" msft "`), When confirmed, Then it is trimmed and uppercased (`MSFT`); an **empty/whitespace-only** input
    is **rejected** with no row and no persistence; a **case-insensitive duplicate** of an existing watchlist symbol
    is a **no-op with a message** (no duplicate row, no extra subscription, no DB change).
  - **AC-D22.4 (live IBKR validation before add — B16)** Given IBKR is connected and the user confirms a non-empty,
    non-duplicate symbol, When the add runs, Then the app performs a **live IBKR contract lookup** before adding:
    on **success** a row for the symbol is appended, a live market-data subscription is requested
    (`add_symbol` → `req_mkt_data`), and the symbol is persisted; on **failure/unresolvable** (no contract, IBKR
    error, or bounded timeout) the add is **rejected with an error surfaced to the user** and **nothing is added,
    subscribed, or persisted**. (The lookup may be asynchronous; the observable outcome is what is asserted.)
  - **AC-D22.5 (require connection — B16b)** Given IBKR is **disconnected**, When the user attempts to add a symbol,
    Then the add is **denied** (the affordance is disabled and/or the confirm is refused with a message) and
    **nothing is added, subscribed, or persisted**.
  - **AC-D22.6 (remove — B14)** Given an existing watchlist row, When the user invokes remove (per-row delete and/or
    right-click **"Remove symbol"**), Then that symbol's live subscription is **cancelled**, the row is **removed**,
    and the removal is **persisted** (the symbol is absent after a restart). Reordering is not offered.
  - **AC-D22.7 (persisted across restarts)** Given a symbol was added (and/or removed) via the affordances, When the
    app is restarted (and IBKR connects), Then the watchlist matches the persisted set — the added symbol is present
    and the removed symbol is absent — read from the `watchlist` table with **no manual DB edit**.
  - **AC-D22.8 (non-regression — D21.5 / D21.11 / D14 / D21.13)** Given the new affordances, When the user
    right-clicks a **column header**, Then the D21.5 add/remove/rearrange **column** popup still opens unchanged;
    the D21.11 "Watchlist" collapse toggle still hides/shows the panel; D14 double-click row-to-load still works; and
    the D21.13 right-dock hide/show behaviour is unchanged.
  - **AC-D22.9 (regression suite)** Given the feature, Then the pre-existing offscreen suite remains green and no
    D1–D21 acceptance criterion regresses.
- **Edge Cases:** empty/whitespace input (rejected); case-insensitive duplicate (no-op + message); unknown/
  unresolvable symbol (rejected, nothing persisted — B16); IBKR disconnected (add denied — B16b); contract-details
  lookup asynchronous / slow / times out (bounded wait, rejected on failure, no hang); removing the **last** symbol
  leaves an empty watchlist that **stays empty** on restart (A52 — the seed-if-empty branch must not re-seed after an
  explicit removal); restart restores the persisted set; D21.5 column menu not shadowed (DG42); add/remove do **not**
  load the chart (distinct from D14/Load Chart); symbol with leading/trailing spaces; futures symbols (`ES`, `NQ`,
  …) go through the contract-lookup path; adding to an empty watchlist; very long / invalid characters; removing a
  symbol while a live subscription is active; `clear()` on disconnect must not corrupt the persisted set (DG40).

### D23 — Batch 17 (2026-10-07): two D22 post-build quality corrections (D23.1 = ESC-030, D23.2 = ESC-031) — CLARIFIED AND FINALISED 2026-10-07

> Two **nice-to-have** Code Reviewer findings on the D22 build (green at 712 tests), both `routed_to: BUILD`,
> `status: open`. The user **approved fixing both** and asked to take them through the full pipeline. **D22 is not
> reopened**: its feature criteria (`AC-D22.1`–`AC-D22.9`) stand; D23 corrects only the two implementation/task-level
> defects. Both are **quality / behaviour-and-documentation** fixes, not new features. **No blocking question was
> required** — the correct outcome is unambiguous from the source evidence (see the D23.1 correction record and A53).

#### D23.1 — ESC-030: `cancel_contract_details` is a silently-swallowed `AttributeError` no-op on the pinned ibapi
- **Area:** `ibkr/market_data.py::MarketDataManager.cancel_contract_details` (`:108` as of 2026-10-14; `:78–84` at D23 report time); the pinned `ibapi` `EClient`
  surface (`ibkr/client.py::IBApiClient`); `services/contract_lookup_service.py` (the real safety net);
  `tests/test_ibkr_contract_details_d22.py` (`_FakeClient`); task-level `AC-D22.2.3`; architecture `S3`.
- **Status:** clarified and finalised 2026-10-07 — **quality fix** (nice-to-have). No D22 behaviour depends on the
  wire cancel.
- **Observed (source-validated 2026-10-07; repo is authoritative):**
  - At D23 report time (`ibkr/market_data.py:78–84`, `[historical]`) the code called `self.client.cancelContractDetails(req_id)` inside `try/except Exception: pass`; the method now lives at `ibkr/market_data.py::MarketDataManager.cancel_contract_details` (`:108`) and performs the capability-guarded cancel required below.
  - The pinned dependency was `ibapi` **9.81.1.post1** at D23 report time and is `ibapi-latest==10.51.1` now (re-verified 2026-10-14); in both, `hasattr(EClient, 'cancelContractDetails')
    is False` while `hasattr(EClient, 'reqContractDetails') is True`. On the real TWS path the call therefore raises
    `AttributeError`, which is swallowed → the cancel is a **no-op on the wire**.
  - `tests/test_ibkr_contract_details_d22.py::_FakeClient` **defines** `cancelContractDetails` (`:127`), so the D22
    tests pass against a surface the pinned dependency does not provide.
  - Task-level `AC-D22.2.3` (in `docs/tasks/task-graph.json`, task `D22-02`) mandates "it calls
    `client.cancelContractDetails(req_id)`"; architecture `S3` adds `MarketDataManager.cancel_contract_details(req_id)`.
    Both describe a call the pinned dependency cannot make.
  - **The method is not called by any production path** (source-validated 2026-10-07): `ContractLookupService.cancel`
    / `services/contract_lookup_service.py::ContractLookupService.cancel_all` (cited `:114–125`, now `:122` — indicative) drop the pending entry and stop the bounded
    `QTimer` — they do **not** call `md_manager.cancel_contract_details`; `ui/main_window.py` uses
    `self._contract_lookup.cancel_all()` (`:724`). The wire cancel is therefore currently write-only/dead code,
    which is why the defect is benign.
  - **Safety net already present:** TWS ends a `reqContractDetails` request on its own (`contractDetailsEnd`, or an
    `error` for an unknown reqId), and `ContractLookupService` invalidates locally — it drops the pending entry
    **before** emitting `lookup_finished` (exactly-once) and ignores late/unknown reqIds, with a bounded `QTimer`
    (`CONTRACT_LOOKUP_TIMEOUT_MS = 5000`) and `cancel_all()` on disconnect (`ui/main_window.py::_on_disconnected`).
- **Required behaviour (final):**
  - `cancel_contract_details(req_id)` MUST perform a **capability-guarded best-effort cancel**: resolve the client
    call via `getattr(self.client, 'cancelContractDetails', None)` and call it **only if present**; when absent (the
    pinned `ibapi`) it returns **without raising** and **without** a swallowed `AttributeError`.
  - The pinned-`ibapi` absence MUST be **documented in code** (comment/docstring): (a) the pinned `ibapi` (`9.81.1.post1` at D23 report time, `10.51.1` now) exposes no `EClient.cancelContractDetails`; (b) the wire-side `reqContractDetails` is ended by TWS's own
    `contractDetailsEnd`/error; (c) `ContractLookupService`'s local invalidation (bounded QTimer + `cancel_all` on
    disconnect) is the real safety net.
  - `req_id is None` remains a no-op (unchanged); a client whose capability-guarded cancel **is** present but
    **raises** must not propagate.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D23.1.1 (capability-guarded cancel — no raised/swallowed `AttributeError`)** Given a `MarketDataManager`
    whose client **lacks** `cancelContractDetails` (the pinned-`ibapi` shape), When `cancel_contract_details(req_id)`
    is called, Then it returns **without raising** and **without** touching a missing attribute (no `AttributeError`
    occurs at all). Given a client that **does** expose `cancelContractDetails`, When called, Then that method is
    invoked with `req_id`.
    - Measurable (offscreen, no live TWS): with a client object that does **not** define the attribute (e.g.
      `types.SimpleNamespace(reqContractDetails=...)`), `cancel_contract_details(7)` completes with no exception; with
      a spy client that defines it, `cancel_calls == [7]`.
  - **AC-D23.1.2 (documented absence + safety net)** Given the source, Then `cancel_contract_details` carries a
    comment/docstring documenting that the pinned `ibapi` has no `EClient.cancelContractDetails`, that the wire
    request is ended by TWS's `contractDetailsEnd`/error, and that `ContractLookupService`'s local invalidation
    (bounded QTimer + `cancel_all` on disconnect) is the safety net.
    - Measurable: the named facts appear in the method's comment/docstring (review-verified).
  - **AC-D23.1.3 (None-safe + containment preserved)** Given `req_id is None`, Then the method is a no-op; Given a
    client whose capability-guarded cancel raises, Then no exception escapes.
  - **AC-D23.1.4 (supersession + reconciliation recorded — correction record)** Given task-level `AC-D22.2.3`'s
    `client.cancelContractDetails` mandate and architecture `S3`, Then the Task Manager corrects `AC-D22.2.3` (in
    `docs/tasks/task-graph.json`) to the capability-guarded, documented cancel above, and architecture `S3` is
    reconciled (the cancel is best-effort/unavailable on the pinned `ibapi`; the local invalidation is the safety
    net) — **without** reopening D22's feature criteria.
    - **Correction record (binding artifacts):** **Task Manager** rewrites `AC-D22.2.3` and its test description in
      `docs/tasks/task-graph.json` (task `D22-02`) to the guard; **Build** implements the guard + comment in
      `ibkr/market_data.py` and updates `tests/test_ibkr_contract_details_d22.py::TestD22_02_T03` (add a
      missing-capability case; pair the method-defining fake with a fake that does not define it, so the guard is
      exercised); **Plan/Validator** records the `S3` reconciliation in `docs/architecture.md`. **Code Reviewer**
      re-verifies ESC-030 after Build.
- **Edge Cases:** client lacks the attribute (pinned `ibapi`) → return without raising; client attribute present →
  called once with `req_id`; client attribute present but raises → contained; `req_id is None` → no-op; the method
  stays uncalled by production today (make it correct **if/when** a caller is added); the test's fake client must
  reflect the pinned surface (a method-defining fake must be paired with a fake that does not define it).

#### D23.2 — ESC-031: `remove_symbol` leaves a stale `_row_data` key when the last row is removed
- **Area:** `ui/watchlist_panel.py::WatchlistPanel.remove_symbol` (`:682–728`), specifically the `_row_data`
  re-index (`:716–719`); `tests/test_watchlist_add_remove_d22.py` (`test_D22_05_T02`).
- **Status:** clarified and finalised 2026-10-07 — **quality fix** (nice-to-have). Impact currently benign.
- **Observed (source-validated + reproduced 2026-10-07):** `remove_symbol` re-indexes `_row_data` with
  `{(r-1 if r > row else r): values …}` but never drops the removed row's own `_row_data` key. When the removed row
  is the **last** (max-index) row, no later key overwrites it, so a stale `_row_data[row]` entry survives: a 3-row
  panel (AAPL/MSFT/TSLA), `remove_symbol('TSLA')` → `table.rowCount() == 2` but `sorted(_row_data.keys()) ==
  [0, 1, 2]` (stale key 2). Removing a **middle** row leaves `[0, 1]` (the shifted-up row overwrites the removed
  key), which is why `test_D22_05_T02` (middle-row removal) misses it.
  - `_req_to_row` (its removed row's reqIds are popped first), `_prev_close`/`_last_price` (reqId-keyed) and
    `_flash_timers` (the removed row's timers are stopped first) are handled explicitly, so **only `_row_data`**
    carries the stale key.
  - Impact is currently benign: a key `>= rowCount()` is never read (every read goes through `table.item(row, col)`
    for `row in range(rowCount())`), is overwritten by the next `add_symbol` at that index, and `clear()` drops it.
- **Required behaviour (final):** after `remove_symbol` returns `True`, every row-keyed structure MUST be keyed
  exactly over the surviving rows — `set(_row_data.keys()) == set(range(table.rowCount()))` (no stale key), mirroring
  the explicit `_req_to_row` / `_prev_close` / `_last_price` / flash-timer handling. The same invariant holds for
  `_req_to_row` values and `_flash_timers` keys (no key for a removed row survives).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D23.2.1 (no stale row key — last-row removal)** Given a panel with `n >= 2` rows, When the **last** row's
    symbol is removed, Then `table.rowCount() == n-1` **and** `set(_row_data.keys()) == set(range(n-1))` (the removed
    row's key is dropped, not merely overwritten by a later key).
    - Measurable (offscreen): 3-row panel, `remove_symbol(last)` → `sorted(_row_data.keys()) == [0, 1]`.
  - **AC-D23.2.2 (first / middle / only-row removal)** Given a panel with rows, When the **first**, a **middle**, or
    the **only** row's symbol is removed, Then `set(_row_data.keys()) == set(range(table.rowCount()))` in every case
    (only-row case → `rowCount() == 0` and `_row_data == {}`). The same invariant holds for `_req_to_row` values and
    `_flash_timers` keys. (These branches already hold pre-fix; the **last-row** branch is the one that fails
    pre-fix — see AC-D23.2.1 / AC-D23.2.3.)
  - **AC-D23.2.3 (coverage added)** Given the D22-05 remove tests, Then a **last-row** (and/or **first-row** /
    **only-row**) removal assertion is added so the stale-key branch is actually covered — the existing middle-row
    check (`test_D22_05_T02`) passes even with the defect and cannot be the only guard.
    - Measurable: the new assertion **fails against the pre-fix `remove_symbol`** and passes after the fix.
  - **AC-D23.2.4 (regression)** Given the fix, Then `test_D22_05_T02` (middle-row re-index, reqId cancellation,
    flash-timer re-index, later-tick routing) and `test_D22_05_T03` (absent/blank no-op) remain green, and
    `_row_data` remains a valid dict for `_rebuild_table`/`_set_cell` after any removal.
- **Edge Cases:** remove the **last** row (the reported branch); remove the **first** row; remove the **only** row
  (table empty, `_row_data == {}`); remove a middle row (unchanged); removing from an empty table / absent symbol /
  blank symbol (no-op, nothing re-indexed); re-adding a symbol after a removal reuses the vacated index cleanly; a
  live tick for a surviving reqId after a last-row removal lands on the correct row; `clear()` still empties
  `_row_data`.

**[NEW v1.2]**
### D24 — Pop-out chart windows (NEW FEATURE) — as-built / APPROVED 2026-10-14
- **Area:** new `ui/ticker_session.py` (`TickerSession` per-symbol model), new `ui/popout_window.py`
  (chrome-free window), `ui/chart_panel.py` (read-only flag), `ui/main_window.py` (session registry, pop-out
  action, extraction of chart-state ownership), `ibkr/subscription_manager.py` (refcounted realtime subs).
- **Status:** **as-built / APPROVED (owner decision 2026-10-14, Q41).** User-specified 2026-10-12; built and
  merged to `main` (Phase 1–4, as-built at `b366b19`); the earlier "DRAFT, owner review required" marker is
  cleared. This is a **new feature**; D1–D23 are **not** reopened.
- **Visual reference (ESC-004 gate):** **SATISFIED BY EXPLICIT USER DECISION (2026-10-12).** The user described
  the pop-out chrome precisely: resizable window, **no toolbars**, minimal screen waste (a slim header with
  symbol/timeframe/mode + close button is acceptable), native OS frame retained for resize/drag across monitors.
  As with D22 (A48), placement/behaviour is the testable requirement; exact header styling is an implementation
  detail.
- **Reported (verbatim context):** "i want to pop out and keep it for ticker 'x' then i want to open ticker y in
  main chart then I want to pop out and keep the new pop out chart for ticker 'y'. like this pop out charts are
  available for ticker 'x' and 'y'. each chart would be re-sizable and have minimal wastage of screen space i.e.
  no tool bars. each ticker symbol alerts/zones/lines would sync across all the pop out charts. i.e. if x is open
  in 3 pop out charts then all of them would be in sync for alerts/zones/lines. Pop out charts won't have the
  drawing facility. that is limited to main chart." / "max 10 pop out charts" / "all updated real time".
- **Observed in repository (validated against source 2026-10-12):**
  - `ui/main_window.py::MainWindow` (~2291 lines) owns **all** chart state: `load_chart` (`:813`) reads toolbar
    widgets directly; `_on_realtime_bar` (`:1173`) filters on the single `self._rt_req_id`; singletons
    `self._aggregator` (`:537`), `_current_symbol/_current_tf` (`:534-535`), `_current_alarms` (`:553`),
    `_last_chart_price` (`:554`); the history-wave apparatus (`_history_req_ids`, `_history_generation`,
    watchdog timer, `:538-552`) assumes exactly one chart. **There is no per-symbol model** — a second
    `ChartPanel` has nowhere to attach.
  - `ui/chart_panel.py::ChartPanel` instances are already view-isolated (own `_bars`, router, overlays,
    `_StudyCache`); overlays communicate via signals (`drawing_overlay.created/updated/deleted`,
    `alarm_overlay.create_requested/...`). `IBBridge` marshals ibapi callbacks to the main thread (queued).
    `RealtimeBarsManager`, `MarketDataManager`, `PacingManager` are window-agnostic.
  - `SubscriptionManager.subscribe()` has **zero callers**; `RealtimeBarsManager.replay_all()` has zero
    callers — reconnect replay is dead code (see D27/B-1.3).
  - Studies persist per symbol (`StudyStore.load/save(symbol)`); drawings/alarms persist per symbol
    (`DrawingStore.drawings_for_symbol`, `AlarmStore.load(symbol)`). `PacingManager` enforces
    `config/settings.py::MAX_REALTIME_BARS_PER_10_MIN = 60` (cited `:12`, now `:30` — indicative); IBKR realtime bars are 5-second only.
- **Requirements (final):**
  - **Session model:** a `TickerSession` keyed by symbol owns that symbol's bar series, studies config,
    drawings/groups, alarms, IBKR realtime subscription, and history-wave lifecycle (req-id registry, watchdog,
    generation fencing — moved out of `MainWindow` unchanged in semantics). It emits Qt signals
    `bar_updated` (incremental tick) / `bars_refreshed` (full series replace) / `studies_changed` /
    `drawings_changed` / `alarms_changed` / `alarm_triggered` (verified against `ui/ticker_session.py::TickerSession` signals; cited `:65–73`, now `:65–84` — indicative — and grown `stream_health_changed` / `footprint_updated` / `depth_state_changed` / `auction_updated` / `dividend_updated` / `events_updated`).
    `MainWindow` holds a `dict[symbol, TickerSession]` registry; views attach/detach; attaching performs an
    initial full sync (bars → studies → drawings → alarms) with **no** extra IBKR request when the session
    already holds the data. A session is destroyed when its last view detaches **and** it is not
    alarm-monitored (D25) — i.e. it stays alive while `views > 0 OR monitored`.
  - **Pop-out lifecycle:** toolbar **"Pop out"** action (button + hotkey, e.g. `Ctrl/Cmd+P`) snapshots the main
    chart's current symbol/timeframe/chart-mode/extended-hours into a new pop-out. **Cap: 10 pop-out windows**
    (`MAX_POPOUTS = 10`, `config/settings.py`); at the cap the action is disabled with a status-bar message;
    closing frees the slot immediately. Popping out never disturbs the main chart. The same ticker may be
    popped out multiple times (one session, one subscription); the main chart may show the same ticker as
    pop-outs. Pop-outs are parented `QWidget`s with `Qt.Window` — independent top-level windows that close with
    the main window. If disconnected at pop-out time, cached bars render immediately from the session cache
    and the subscription starts on connect via the existing reconnect path. **[VERIFIED 2026-10-14 — text
    corrected:** the shipped code has **no** per-pop-out "connecting" indicator (the only connecting
    affordance is the main window's `ui/main_window.py::MainWindow.conn_badge` (cited `:290`, now `:295` — indicative)); the requirement no longer asserts
    behaviour the code does not have. A per-window indicator would be a new request.]**
  - **Chrome-free window:** each pop-out contains exactly a slim header strip (symbol · timeframe · mode + close
    button, ~28px) and a `ChartPanel`; no toolbar row, no docks, no watchlist, no status bar. Native OS frame
    retained. `ChartPanel` gains a read-only mode (`editable=False`): drawing tools, alarm placement, and
    studies/timeframe/mode controls are disabled — **interaction only**; `drawing_overlay`/`alarm_overlay`
    still render everything, and crosshair/zoom/pan work normally. Timeframe/mode/extended-hours are **frozen
    at pop-out creation** (A56).
  - **Always-on-top:** pop-out windows are **standard windows by default** — always-on-top defaults **OFF**;
    the user can enable it per window via the header context menu ("Always on top"), which applies
    `Qt.WindowStaysOnTopHint` at runtime. **Owner-confirmed 2026-10-14 (Q43)**; matches
    `ui/popout_window.py::PopoutWindow` (`self._always_on_top = False` — cited `:56`; `_toggle_always_on_top` — cited `:289`; both indicative).
  - **Main chart:** keeps its full UI and becomes view #0 on the current symbol's session. Loading a new ticker
    detaches the primary view from the old session and attaches to (or creates) the new one; the old session
    persists while pop-outs remain. Watchlist double-click still targets the main chart only. The toolbar alarm
    badge reflects the main-chart symbol only. `load_chart` is parameterised
    (`load_chart(symbol, timeframe, extended_hours)`) instead of reading toolbar widgets, so pop-outs, the
    alarm monitor, and tests can reuse it.
  - **Sync:** one `reqRealTimeBars` per symbol regardless of view count (refcounted — first holder subscribes,
    last holder releases; never two subs for one symbol). Each aggregated bar fans out via the existing
    incremental `update_last_bar(bar, is_new_candle)` path — no full rebuilds on ticks. Drawings: the main
    chart is the **sole writer**; create/update/delete/group changes persist via `DrawingStore` then emit
    `drawings_changed`; every attached view re-renders its overlay in the same event-loop pass. Alarms:
    definitions shared per symbol; **evaluation moves into the session** (every aggregated bar runs the
    existing `evaluate_alarms(last_price, close, alarms)`), so X's alarms fire even when the main chart shows
    Y — a behaviour change vs today. On trigger: `AlarmStore.mark_triggered`, `alarm_triggered` signal,
    `MainWindow` toast + sound **exactly once per trigger event**. Studies: per-symbol shared (matching
    `StudyStore` keying); the `_StudyCache` (keyed `(symbol, timeframe, studies-hash)`) moves into the session
    so views share computed arrays.
  - **Constraints:** reuse `ChartPanel`, overlays, router, `BarCache`, `BarAggregator`, `RealtimeBarsManager`,
    `PacingManager`, stores, `evaluate_alarms`, backfill planners unchanged; same process, Qt signals, no IPC;
    **no new IBKR API call types**; **no DB schema changes**; concurrent history waves across sessions must
    respect IBKR historical-data pacing (D28/B-2.3).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D24.1 (one subscription per symbol)** Given X popped out 3×, Then exactly one `reqRealTimeBars` exists
    for X; closing all three cancels it (assert via `SubscriptionManager`/`RealtimeBarsManager`).
  - **AC-D24.2 (drawing sync)** Given X in the main chart + 2 pop-outs, When a zone is drawn in the main chart,
    Then all X pop-out overlays contain the zone within the same event-loop pass (no timers); deleting it
    removes it everywhere.
  - **AC-D24.3 (alarm sync + cross-symbol firing)** Given an X alarm set in the main chart and the main chart
    then switched to Y, When X's price crosses the alarm level (bars fed to X's session), Then toast + sound
    fire exactly once and every X pop-out shows triggered styling.
  - **AC-D24.4 (study sync)** Given studies edited for X in the main chart, Then all X pop-outs re-apply them;
    study arrays are computed once per `(symbol, timeframe, studies-hash)`.
  - **AC-D24.5 (cap)** Given 10 pop-outs open, When an 11th is attempted, Then it is refused with a status-bar
    message and the pop-out action is disabled until a slot frees. **[VERIFIED 2026-10-14 — narrower:** the
    shipped code refuses the 11th with a status-bar message (`ui/main_window.py::MainWindow._open_popout`; `:845–851` as of 2026-10-14, `:840–846` when verified — indicative) but does **not**
    `setEnabled(False)` the pop-out affordance; the "disabled" clause is not literally implemented.]**
  - **AC-D24.6 (read-only pop-outs)** Given a pop-out, When chart clicks/draw gestures are simulated, Then no
    drawing, alarm-placement, study, timeframe, or mode affordance activates (router modes never arm). *[VERIFICATION 2026-10-14: the shipped read-only test (`tests/test_d24_popouts.py::test_popout_readonly`) is labelled **AC-D24.3** (an AC-numbering mismatch) and only asserts `_editable is False` plus "no exception" — the "router modes never arm" clause is **not** asserted. `AC-D24.2` (drawing sync), `AC-D24.4` (study sync), `AC-D24.7` (reconnect) and `AC-D24.10` (always-on-top) have **no** backing test. See `design_gaps.md` DG58.]*
  - **AC-D24.7 (reconnect)** Given live sessions + pop-outs, When TWS drops and reconnects, Then all
    subscriptions replay (reqIds rebound to sessions) and every view resumes ticking with no manual reload
    (depends on D27/B-1.3 fix; assert with mocked client).
  - **AC-D24.8 (regression)** Given the feature, Then the pre-existing offscreen suite stays green and no
    D1–D23 criterion regresses.
  - **AC-D24.9 (restore)** [owner-confirmed 2026-10-12; DG48 reconciled 2026-10-14] The open pop-out set
    **SHALL** be persisted per pop-out (symbol, timeframe, chart mode, extended-hours flag, window geometry) in
    SQLite (`popouts` table, `data/popout_store.py`) on every open/close/geometry change, and re-created on app
    launch after TWS connects (sessions attach lazily; views render from cache first, then live). Given 3
    pop-outs open with known snapshots (X, Y, Z), When the app restarts, Then 3 pop-outs are re-created with
    identical symbol/timeframe/mode/ext-hours and approximate geometry; **no duplicate subscriptions** are
    issued for symbols already covered.
  - **AC-D24.10 (always-on-top default off)** Given a pop-out is opened, Then it is a standard window with
    always-on-top **OFF** (`Qt.WindowStaysOnTopHint` not set) until the user enables "Always on top" from the
    header context menu; the toggle applies/clears the hint at runtime. Owner-confirmed 2026-10-14 (Q43).
- **Edge Cases:** pop-out with no symbol loaded (disabled/ignored + message); pop-out of the same symbol twice;
  main chart loads X while X pop-outs exist (primary joins the existing session — no duplicate backfill wave
  for data already held); last view of X closed via main-chart switch (session teardown cancels X's RT sub;
  reopening X starts cold from cache); rapid open/close (refcount never negative, no double-subscribe); TWS
  disconnect with N sessions (all replay on reconnect); alarm triggers while only a pop-out shows X
  (toast+sound still fire from the main window); `load_chart` re-entrancy guards work per-session (two views
  attaching never start two waves); quitting with pop-outs open (all close, all subs cancelled, client
  disconnects).

**[NEW v1.2]**
### D25 — Headless alarm price monitoring (NEW FEATURE) — as-built / APPROVED 2026-10-14
- **Area:** new `services/alarm_monitor.py::AlarmMonitor` (owned by `MainWindow`, wired to the session
  registry); new `AlarmStore.symbols_with_active_alarms()` query; `TickerSession` monitored flag.
- **Status:** **as-built / APPROVED (owner decision 2026-10-14, Q41).** User-specified 2026-10-12; built and
  merged. New feature; D1–D24 not reopened.
- **Visual reference (ESC-004 gate):** **NOT APPLICABLE** — no UI-visual decision (headless by design; the only
  user-visible surface is the existing alarm toast/sound).
- **Reported (verbatim context):** "Also ensure that, the app tracks prices of all tickers which have an alarm.
  It should be tracked on a 1 min interval to ensure alarm fires even if some other ticker is open in main chart"
  (typo "tickets" corrected to "tickers" by the user).
- **Observed in repository (validated against source 2026-10-12):** alarm evaluation lives in
  `MainWindow._on_aggregated_bar` (`:1179-1197`) and runs only for the main-chart symbol
  (`self._current_alarms`); a ticker with alarms but no open chart is never evaluated. `evaluate_alarms`
  (`services/alarm_service.py`) is pure and direction-aware (`cross_above`/`cross_below`/`cross_either`),
  skipping inactive/triggered alarms; `AlarmStore.mark_triggered` + in-memory `triggered=True` prevent
  refire; `AlarmStore.rearm` clears both. `BarCache.get_bars(symbol, "1m")` can seed a previous price.
- **Requirements (final):**
  - A new `AlarmMonitor` maintains the **monitored set**: all symbols with ≥1 alarm where
    `active and not triggered` (new `AlarmStore.symbols_with_active_alarms()`:
    `SELECT DISTINCT symbol FROM alarms WHERE active=1 AND triggered=0`).
  - For each monitored symbol with **no open view**, the monitor ensures a **headless `TickerSession`**
    (`views == 0`, `monitored == True`): one `reqRealTimeBars` (5-sec bars) aggregated by the existing
    `BarAggregator` at a fixed **1-minute** timeframe. Headless sessions are ordinary sessions — no parallel
    data path.
  - Evaluation runs on every 5-second push via the existing `evaluate_alarms(prev_price, curr_price, alarms)`
    (prev = last evaluated price): **1-minute tracking granularity, second-level firing latency**
    (~12 evaluations/min/symbol — trivial cost).
  - Seed: `prev_price` comes from `BarCache.get_bars(symbol, "1m")` last close when available; otherwise the
    first realtime tick seeds it with **no** evaluation until the second tick (existing `prev_price is None`
    guard). **Headless sessions issue zero historical requests** (cache-seed only) to avoid burning IBKR
    historical pacing.
  - Reconcile (diff desired vs actual monitored set) on: TWS connect, alarm add/update/delete/rearm/trigger,
    view attach/detach. A symbol gaining a view keeps its session (view-backed; no duplicate monitor). A symbol
    whose last live alarm is deleted/triggered/deactivated is unmonitored; with no views its session tears down
    (D24/FR-1.5). Re-armed alarms re-enter on the next reconcile.
  - Trigger path identical to D24: `AlarmStore.mark_triggered` → `alarm_triggered` signal → `MainWindow`
    toast + sound exactly once.
  - Pacing guard: each monitored symbol costs one realtime-bar sub against `MAX_REALTIME_BARS_PER_10_MIN =
    60`. If the monitored set would exceed the budget, monitor most-recently-active symbols first and surface a
    status-bar warning naming the unmonitored symbols.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D25.1 (headless firing)** Given no chart open on X and one live X alarm, Then exactly one realtime-bar
    subscription exists for X; driving X's price through the alarm level fires toast + sound exactly once;
    `AlarmStore` shows triggered; deleting the alarm with no view open tears the session down (sub cancelled).
  - **AC-D25.2 (no historical requests)** Given headless monitoring starts for X, Then zero historical-data
    requests are issued (assert on the request registry); `prev_price` seeds from the 1m cache when present. *[VERIFICATION 2026-10-14: the shipped `tests/test_d25_alarm_monitor.py` does **not** assert on the request registry — the zero-historical-request check is a comment only. See `design_gaps.md` DG57.]*
  - **AC-D25.3 (no phantom trigger)** Given monitoring starts while X's price is already beyond the alarm level,
    Then no trigger fires — only a genuine subsequent cross triggers (documented; no "catch-up" of stale
    crosses).
  - **AC-D25.4 (rearm + disconnect)** Given a triggered alarm is re-armed, Then X re-enters monitoring on the
    next reconcile; given an alarm is added while disconnected, Then X is monitored on the next connect
    reconcile with no error and no silent drop. *[VERIFICATION 2026-10-14: no shipped test covers the re-arm + disconnected-add case. See `design_gaps.md` DG57.]*
  - **AC-D25.5 (regression)** Given the feature, Then the pre-existing offscreen suite stays green. *[VERIFICATION 2026-10-14: no dedicated test function exists (the batch regression convention applies, cf. AC-D39.5/AC-D40.5). The `tests/test_d25_alarm_monitor.py` docstrings label its five tests AC-D25.1–AC-D25.5 **in test order**, which does not match this numbering — see `design_gaps.md` DG57.]*
- **Edge Cases:** alarm added while disconnected; price beyond level at monitor start (A62); re-armed alarm;
  triggered-then-deleted alarm (never re-monitored); monitored set exceeding the pacing budget (A63); symbol
  with a view open (view-backed evaluation, no duplicate); app quit with headless sessions (teardown like any
  session).

**[NEW v1.2]**
### D26 — Corrective batch: P0 real-money safety (deep-dive 2026-10-12) — as-built / APPROVED 2026-10-14
- **Area:** `ibkr/orders.py`, `ui/main_window.py` (order path), `ui/active_trader_panel.py`,
  `ui/active_portfolio_panel.py`, `config/settings.py`, `ibkr/error_codes.py`, tests.
- **Status:** **as-built / APPROVED (owner decision 2026-10-14, Q41; DEC-4 resolved, Q42).** Five-track
  adversarial review (~30k lines, critical claims hand-verified); the P0 order-path fixes have shipped. The
  live-order path is no longer covered by a per-run "gated in TWS" assumption, so D26 is planned against it.
  Not a feature; D1–D23 not reopened.
- **Visual reference (ESC-004 gate):** NOT APPLICABLE — behaviour/correctness fixes, no UI-visual decisions
  (any label changes, e.g. D26.3's dialog labelling, are text-only).
- **Requirements (final — corrective, SHALL language):**
  - **D26.1 (B-0.1):** bracket-order stop-loss and take-profit children **SHALL** be placed on the **opposite**
    side of the entry (`BUY` entry → `SELL` STP + `SELL` LMT; `SELL` entry → `BUY` STP + `BUY` LMT).
    `tests/test_order_builders.py::test_bracket_order_structure` / `::test_bracket_order_sell` (cited `:83-104` — indicative; they assert the buggy same-side behaviour) **SHALL** be rewritten
    to assert the protective direction.
  - **D26.2 (B-0.2):** all three bracket order IDs **SHALL** be reserved from `id_manager` before transmit
    (e.g. `reserve(3)` or three `get_id()` calls); no subsequent order or reqId may reuse a live order ID.
  - **D26.3 (B-0.3):** "Set Stop-Loss / Take-Profit" **SHALL** transmit real STP/LMT legs and reflect live
    `orderStatus`; until it does, the dialog **SHALL** be labelled as not placing orders.
  - **D26.4 (B-0.4):** Buy/Sell MKT buttons **SHALL NOT** crash; quantity **SHALL** come from the quantity
    input with a qty>0 guard.
  - **D26.5 (B-0.5):** the app **SHALL** fail fast unless `IBKR_PORT == 7496`; the "Live" badge **SHALL** derive
    from the verified port and the account's `AccountType`, never a hardcoded string.
  - **D26.6 (B-0.6):** order entry **SHALL** offer an explicit Buy/Sell side; an ask-click SELL intent **SHALL
    NOT** become a buy; the dead `_pending_ladder` path is consumed or deleted.
  - **D26.7 (B-0.7):** a single `validate_order()` gate **SHALL** run before transmit: qty>0, notional cap,
    price>0, stop/target on the correct side for the side, non-empty symbol — rejections surfaced in the UI,
    never a traceback.
  - **D26.8 (B-0.8):** a real kill switch **SHALL** exist (`reqGlobalCancel()` + cancel every registry ID);
    Close-All/Flatten **SHALL** invoke it and show pre/post open-order counts.
  - **D26.9 (B-0.9):** order rejections/cancels **SHALL** update the order registry and ticket state (not just
    an 8-second status message); order/connection error codes **SHALL** be promoted from "warning" to
    first-class alerts; order entry **SHALL** be blocked while disconnected.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D26.1** Given a BUY bracket built by `bracket_order`, Then stop.action == "SELL" and limit.action ==
    "SELL" (and mirrored for SELL entries); the rewritten builder tests assert this for both directions.
  - **AC-D26.2** Given a bracket placed, Then the three order IDs are distinct, sequential, and never reissued
    by a later `get_id()` (mocked client).
  - **AC-D26.3** Given the SL/TP dialog, Then either real legs transmit (assert `placeOrder` calls) or the
    dialog text states it places no orders.
  - **AC-D26.4** Given the MKT buttons, Then clicking transmits with the spinbox quantity (mocked client, no
    `TypeError`); qty ≤ 0 is refused.
  - **AC-D26.5** Given `IBKR_PORT=7497`, Then the app refuses to start trading (fail-fast); the badge never
    reads "Live" on a non-7496 port.
  - **AC-D26.6** Given ask-click then Place with Sell selected, Then the transmitted action is SELL.
  - **AC-D26.7** Given invalid order input (qty 0/negative, price 0 stop, empty symbol, 100k qty), Then
    `validate_order()` rejects with a UI message and no `placeOrder` call, no traceback.
  - **AC-D26.8** Given open orders + positions, When the kill switch fires, Then `reqGlobalCancel` (or per-ID
    cancels) is issued and the UI shows pre/post counts.
  - **AC-D26.9** Given a TWS rejection (e.g. 201/103) for a tracked orderId, Then the registry/ticket shows
    Rejected with the TWS message; no order can be placed while disconnected.
  - **AC-D26.10 (regression)** Given the fixes, Then the full offscreen suite is green and **no test transmits
    an order or connects to live TWS** (existing AC-Global invariant).

**[NEW v1.2]**
### D27 — Corrective batch: P1 correctness (deep-dive 2026-10-12) — as-built / APPROVED 2026-10-14
- **Area:** `ui/main_window.py`, `ui/chart_panel.py`, `ui/overlays/`, `ibkr/client.py`,
  `ibkr/subscription_manager.py`, `ibkr/realtime_bars.py`, `data/bar_aggregator.py`,
  `services/indicator_service.py`, `data/drawing_store.py`, `services/backfill_service.py`.
- **Status:** **as-built / APPROVED (owner decision 2026-10-14, Q41).** Not a feature; D1–D23 not reopened.
- **Visual reference (ESC-004 gate):** NOT APPLICABLE — correctness fixes; the overlay coordinate fixes restore
  already-specified visuals (no new visual decisions).
- **Requirements (final — corrective):**
  - **D27.1 (B-1.1):** `_last_chart_price` **SHALL NEVER** move backward: on history-wave finalize, the
    assignment is skipped if any realtime bar was observed since load (also re-apply the aggregator's forming
    bar after `update_chart` so the live candle is not wiped). **[blocks D24/D25]**.
  - **D27.2 (B-1.2):** the MACD histogram **SHALL** plot at display-x (`bar_x.append(xs[i])`); the ICT overlay,
    RTH-gap overlay, and VIX sigma labels **SHALL** plot in display-x (index→display-x via the collapse map,
    as `DrawingOverlay._ts_to_x` does). Overlay tests **SHALL** assert rendered x-coordinates fall inside the
    panel's view range.
  - **D27.3 (B-1.3):** reconnect **SHALL** work: `_do_reconnect` uses `self.connect(host, port, clientId)`
    (never the nonexistent `eConnect`); `_poll` SHALL NOT re-arm timers while a reconnect is pending; every
    live subscription (chart RT bars, DOM, watchlist mkt-data) **SHALL** be registered with type tags and
    replayed on connect with reqIds rebound to their sessions. **[blocks D24]**.
  - **D27.4 (B-1.4):** each session **SHALL** carry stream-health state
    (subscribed/awaiting-first-bar/live/failed+code) with a persistent, non-transient indicator; failed RT
    subs **SHALL** retry with backoff — "Live stream active" SHALL NOT be declared unconditionally.
    **[blocks D24]**.
  - **D27.5 (B-1.5):** position market prices **SHALL** come from a `symbol → last_price` map lookup for the
    position's own symbol, never the chart's `_last_chart_price`.
  - **D27.6 (B-1.6):** the app **SHALL** subscribe `reqPositions` + `reqAccountSummary` on connect and populate
    the portfolio panel; an "account data unavailable" state **SHALL** show when unsubscribed.
  - **D27.7 (B-1.7):** backfill gap detection **SHALL** run at bar-period granularity for trailing N trading
    days (expected vs cached bar count), or record per-chunk completion — a stranded wave's partial day
    SHALL be repairable by a later load.
  - **D27.8 (B-1.8):** `"1 day"` (and `"4 hours"`) aggregation **SHALL** anchor to `America/New_York` wall time,
    not UTC midnight; session-anchored VWAP **SHALL** reset on ET date change (verify IBKR's 4h anchor first).
  - **D27.9 (B-1.9):** on chart load the aggregator **SHALL** be primed with trailing 5-second history before
    the live feed attaches, so the forming candle's OHLCV is not fabricated.
  - **D27.10 (B-1.10):** drawing style edits (colour, label, group) **SHALL** persist via the store and survive
    reload.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D27.1** Given a backfill wave finalising after live ticks advanced the price, Then no alarm between
    the historical close and the live price fires (no phantom trigger); the live forming bar survives finalize.
  - **AC-D27.2** Given MACD/ICT/gaps/VIX studies enabled, Then every rendered element's x-coordinate lies
    inside the panel's view x-range (offscreen assertion).
  - **AC-D27.3** Given a simulated TWS drop/reconnect (mocked client), Then the app reconnects without restart
    and all live subscriptions are re-issued with rebound reqIds; bars flow with no manual reload.
  - **AC-D27.4** Given a failed `reqRealTimeBars`, Then a persistent stream-failed indicator shows (with the
    error code) and a backoff retry is scheduled.
  - **AC-D27.5** Given positions in symbols other than the charted one, Then each shows its own symbol's last
    price and correct unrealized P&L.
  - **AC-D27.6** Given connect, Then `reqPositions` + `reqAccountSummary` are issued and the portfolio panel
    populates; given no subscription, Then the "unavailable" state shows.
  - **AC-D27.7** Given a stranded partial-day backfill, Then a later load detects the bar-level gap and
    completes it.
  - **AC-D27.8** Given a daily chart, Then the live forming daily bar ts-matches the historical daily series
    (ET session days); VWAP resets at the ET session boundary with ext-hours on.
  - **AC-D27.9** Given a fresh chart load mid-period, Then the forming candle's open/volume reflect the
    primed 5-sec history, not just the first live tick.
  - **AC-D27.10** Given a drawing colour edit, Then reload shows the edited colour.
  - **AC-D27.11 (regression)** Given the fixes, Then the full offscreen suite is green; no D1–D23 criterion
    regresses.

**[NEW v1.2]**
### D28 — Corrective batch: P2 robustness & scale (deep-dive 2026-10-12) — as-built / APPROVED 2026-10-14
- **Area:** `ibkr/pacing.py`, `ui/main_window.py` (extraction), `ibkr/market_data.py`, `ui/chart_panel.py`,
  `ui/candlestick_item.py`, `data/bar_cache.py`, `services/indicator_service.py`, tests.
- **Status:** **as-built / APPROVED (owner decision 2026-10-14, Q41).** Not a feature; D1–D23 not reopened.
  This batch carries the structural enablers for D24/D25 (extracted into `TickerSession`).
- **Visual reference (ESC-004 gate):** NOT APPLICABLE.
- **Requirements (final — corrective):**
  - **D28.1 (B-2.1):** `PacingManager` **SHALL NEVER** sleep on the GUI thread: throttlers return a wait
    duration or raise `PacingExceeded`; subscribes/orders defer via `QTimer.singleShot` with a persistent
    "pacing-limited, retrying in Ns" status. Throttling is **removed from the order path entirely**; orders get
    their own rate limiter. **[blocks D24]** (10 pop-outs + reconnect replays make the freeze likely).
  - **D28.2 (B-2.2):** the single-symbol data plane **SHALL** be extracted into `TickerSession` per D24's
    session model: session owns `BarAggregator`, RT reqId, last price, alarms, history-wave state + watchdog;
    `_on_realtime_bar` / `_on_historical_bar` / `_on_historical_data_end` / `_on_error` route by
    reqId → session; `MainWindow` keeps the registry. `load_chart(symbol, timeframe, extended_hours)` is
    parameterised. **[blocks D24/D25]**.
  - **D28.3 (B-2.3):** `reqHistoricalData` **SHALL** have a rolling 600-second pacing window (non-blocking);
    chunks per wave are capped (~60) with continuation across waves; on IBKR error 162 the failed chunks back
    off and retry once before finalising short.
  - **D28.4 (B-2.4):** in-memory `_bars` **SHALL** be bounded (~5k, lazy-load on scroll-back) with a cache
    retention policy per (symbol, timeframe); rendering splits into static-history + live-bar layers (no full
    QPicture regen per tick); the study cache **SHALL** actually be read (shift arrays, compute only the new
    bar); crosshair/volume-ceiling use bisection over cached display-x arrays; collapse-map updates are
    incremental at the tail. **[blocks D24]** (per-tick costs multiply by chart count).
  - **D28.5 (B-2.5):** `closeEvent` **SHALL** tear down explicitly: `_closing` flag (slots early-return),
    cancel lookups, disarm timers, cancel subs, then disconnect, then clear UI; the `ibkr-reader` thread is
    joined with a timeout.
  - **D28.6 (test hardening — highest value only):** alarm end-to-end
    (`_on_aggregated_bar` → `mark_triggered` → badge/toast/sound); order path with mocked `ib_client`
    (exact `placeOrder` args, ID uniqueness, contract reconstruction); reconnect replay; drawing
    store→overlay round-trip; `id_manager` behavioural tests; pacing window math with monkeypatched time;
    delete doc-asserting tests (`test_d23_nonregression.py` markdown-string asserts) and the phantom
    `validate_sltp` test; fix shared-DB cross-test contamination.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D28.1** Given pacing budget exhausted, When a chart loads or an order is placed, Then the GUI thread
    never blocks (assert no `time.sleep` on the main thread; deferred retry shown in status).
  - **AC-D28.2** Given two symbols with live sessions, Then each routes its own bars/alarms/waves with no
    cross-talk (reqId→session routing test); `load_chart` works without toolbar widgets.
  - **AC-D28.3** Given rapid symbol switching, Then no error-162 storm occurs; historical pacing stays within
    budget and failed chunks retry once.
  - **AC-D28.4** Given a long live session, Then memory stays bounded (bar cap + retention) and a 5-second tick
    performs no full chart rebuild (assert via render-call counters).
  - **AC-D28.5** Given app close mid-backfill, Then teardown completes without touching cleared widgets and
    the reader thread joins within the timeout.
  - **AC-D28.6** Given the new tests, Then T-1..T-6 behaviours above are covered and the doc-assert/phantom
    tests are gone; the suite is green. *[VERIFICATION 2026-10-14: **satisfied as intended** — Phase 4 item 4d (commit `3363422`; `docs/phase-changelog.md:166`) deleted the three doc-text tests inside `tests/test_d23_nonregression.py` **and** the phantom `validate_sltp` test, deliberately keeping the file's behavioural guard/invariant checks (see the commit message). The only residue is `tests/test_d23_nonregression.py::test_D23_03_T03_guard_source_shape` (`assert "9.81.1.post1" in src` at `:61`), which pins the pre-D36 `ibapi` version literal and must move with DG54's docstring fix. See `design_gaps.md` DG61.]*
  - **AC-D28.7 (regression)** Given the fixes, Then the full offscreen suite is green; no D1–D23 criterion
    regresses.

### D36 — Footprint charts (bid×ask volume-at-price) — as-built / APPROVED 2026-10-13
- **Area:** `services/footprint_service.py` (`FootprintService`), `data/footprint_cache.py`
  (`FootprintCache`, `is_cacheable`), `ui/footprint_item.py` (`FootprintItem`),
  `ibkr/tick_history.py` (`TickHistoryManager.req_historical_ticks`), `ibkr/contracts.py`
  (`resolve_footprint_contract`, `footprint_cache_key`, `INDEX_PROXY`), `ui/ticker_session.py`
  (footprint wave / forming / snapshot), `ui/chart_panel.py` (`refresh_footprint`).
- **Status:** **as-built / APPROVED 2026-10-13** (927 tests green; Code Reviewer approved). Feature; D1–D35 not
  reopened. Default **OFF** (owner decision 2026-10-13). Acceptance criteria **authored 2026-10-14 (Q45/DG46)**
  from the shipped behaviour and `tests/test_d36_footprint.py`.
- **Backing tests:** `tests/test_d36_footprint.py` (`test_ac_d36_1..4`, plus the session/UI tests).
- **Requirements (as-built):** backfill prior bars from per-session TRADES **historical tick pages**
  (`reqHistoricalTicks`; the planned `reqHistogramData` path was removed — the method takes no date parameter
  and cannot address individual bars), classic + heatmap styles, volume + tick-count metrics, viewport-newest-
  first waves capped at 60 requests, index proxy (SPX→ES front month, labelled), and a resolved-contract cache.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D36.1 (bid×ask bucketing + delta)** Given BID_ASK ticks, Then bid volume accrues at the bid price and
    ask volume at the ask price (per-level `[bidVol, askVol]`); Given TRADES ticks, Then each level carries
    trade volume **and** trade count; ticks outside the bar window are excluded (out-of-range → no level).
  - **AC-D36.2 (contiguous 1000-tick pages)** Given a completed bar, When its footprint is backfilled, Then the
    backward tick pages are **contiguous with no gaps or overlaps** (page k ends exactly 1000s after page k+1);
    a full page keeps the phase open (`loading`), a short final page finishes the bar (`ready`), and the BID_ASK
    + TRADES phases merge into one level set `[bidVol, askVol, tradeVol, count]`.
  - **AC-D36.3 (no tick-by-tick; no mock endpoints)** Given the footprint path, Then it uses `reqHistoricalTicks`
    only — **zero** `reqTickByTickData`/`tickByTick` anywhere (including `ibkr/tick_history.py`) — and no
    faked/mocked/stubbed endpoint exists in the production tree (`ibkr`, `services`, `ui`, `data`).
  - **AC-D36.4 (zero static-layer regens on a tick burst)** Given a rendered footprint, When 100 same-bar
    (`is_new_candle=False`) ticks are applied, Then the static footprint layer regenerates **zero** times
    (D28 discipline; `footprint_static.regen_count == 0`).
  - **AC-D36.5 (style × metric rendering)** Given classic vs heatmap style and the volume vs count metric, Then
    the `FootprintItem` re-renders on a style or metric change (metric change → re-render); a daily timeframe
    backfills daily bars (the forming bar reads `loading`, never `unavailable`).
- **Edge Cases:** symbol with no tick history → `unavailable` "no tick data" state (never an empty chart);
  pacing exhaustion mid-backfill (defer via `PacingExceeded` + `singleShot`, `loading` persists); timeframe
  change (recompute, no stale levels); disconnect mid-wave (wave resets, no zombie); forming refresh yields to
  backfill and **replaces** (never accumulates) ticks; index proxy labelled "ES tape"; front-month rollover
  produces a different cache key so an old tape never serves the new contract.

### D37 — Depth heatmap + auction imbalance — as-built / APPROVED 2026-10-13
- **Area:** `services/depth_heatmap.py` (`DepthHeatmapService`), `ui/depth_heatmap_item.py`
  (`DepthHeatmapItem`), `services/md_line_guard.py` (`assess`), `ui/chart_panel.py`
  (`DepthHeatmapItem`, `set_depth_state`, auction chip), `ui/ticker_session.py` (S0 union subscription,
  depth refcount, auction ticks), `ibkr/bridge.py` (`tick_generic`/`tick_string`/`tick_news`), `ibkr/client.py`
  (10.51.1 callback signatures).
- **Status:** **as-built / APPROVED 2026-10-13** (947 tests green; no blocking findings). Feature; D1–D36 not
  reopened. Depth heatmap default **ON** (owner-confirmed 2026-10-14, Q44 — overrides the reviewer's OFF
  suggestion). Acceptance criteria **authored 2026-10-14 (Q45/DG46)** from the shipped behaviour and
  `tests/test_d37_microstructure.py`.
- **Backing tests:** `tests/test_d37_microstructure.py` (`test_ac_d37_1..4`).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D37.1 (book bookkeeping)** Given synthetic insert/update/delete depth ops, Then the heatmap level sizes
    match the book exactly (insert sets a side, update changes size, delete removes the level); matrix snapshots
    carry resting sizes and are bounded to 60 buckets.
  - **AC-D37.2 (imbalance sign + top-N)** Given a book, Then the headline imbalance =
    `(bidVol − askVol) / (bidVol + askVol)` over the top-5 levels, sign-correct (bid-heavy positive, ask-heavy
    negative); the top-10 toggle recomputes on every op and changes the headline; an empty book → `0.0`
    (never NaN).
  - **AC-D37.3 (auction chip)** Given synthetic ticks 34 (size→volume), 35 (price), 36 (imbalance), Then the
    auction chip shows volume/price/imbalance (side label flips on sign); absent ticks → an explicit
    "no auction data" chip (`AUC —`); the ticks are routed on the session's single S0 `reqMktData` (generic-tick
    union includes `"225"`; a wrong reqId is ignored).
  - **AC-D37.4 (error 354 → explicit state)** Given the depth feed returns error 354 (no entitlement), Then the
    panel shows the explicit "Depth subscription required" state, the state signal fires, and the feed is
    released (`cancelMktDepth`) — never a silent empty panel.
  - **AC-D37.5 (regression)** Given the feature, Then the full offscreen suite is green and no D1–D36 criterion
    regresses.
- **Edge Cases:** depth budget / MD-line cap exceeded → status-bar warning naming symbols (never silent);
  auction ticks outside auction windows; reconnect mid-session (depth replays via D27); MPID vs exchange rows in
  SMART depth (`isSmartDepth`); symbol with no views → no headless depth (feed lives only while `views > 0`);
  delayed-depth instead of 354 renders unlabelled (known limitation, recorded).

### D38 — Event markers + news-for-holdings digest — as-built / APPROVED 2026-10-13
- **Area:** `data/events/provider.py` (`Event`, `EVENT_TYPES`, corporate-events-only guard,
  `parse_ib_dividend_string`), `data/events/ibkr_source.py`, `data/events/yfinance_source.py` (`YFinanceCache`,
  TTL), `ibkr/news.py` (`NewsManager`), `ui/news_digest_dock.py` (`NewsDigestDock`),
  `ui/event_marker_overlay.py` (`EventMarkerOverlay`, `EVENT_STYLE`), `ui/ticker_session.py`
  (`_merge_events`, tick-59 dividend merge).
- **Status:** **as-built / APPROVED 2026-10-13** (970 tests green; no blocking findings). Feature; D1–D37 not
  reopened. Acceptance criteria **authored 2026-10-14 (Q45/DG46)** from the shipped behaviour and
  `tests/test_d38_events_news.py` (which states AC-D38.1–AC-D38.6 in its own header).
- **Backing tests:** `tests/test_d38_events_news.py`.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D38.1 (markers + countdown)** Given 1 earnings + 1 dividend + 1 split event, Then three markers render
    with distinct per-type styling at the correct dates and a countdown names the next upcoming event
    ("Split in 4d"); no upcoming event → the countdown is hidden; events unavailable → "Event data unavailable";
    a date correction moves the marker (id-keyed) rather than duplicating it.
  - **AC-D38.2 (digest groups + article fetch)** Given 2 held symbols + synthetic headlines, Then the digest
    groups headlines under each holding and clicking a headline fetches that article (`reqNewsArticle`).
  - **AC-D38.3 (no news entitlement)** Given no API news subscription, Then the digest shows the explicit
    "No API news subscription" state (never silently empty).
  - **AC-D38.4 (corporate-events-only guard)** Given a non-corporate event type, Then it is rejected at the
    provider boundary; the yfinance layer only calls the approved corporate-events endpoints (one secondary
    source only).
  - **AC-D38.5 (IBKR-first merge under a yfinance outage)** Given an IBKR tick-59 dividend and yfinance down,
    Then the dividend marker still renders while earnings/splits show "event data unavailable"; a yfinance
    dividend on the same date as an IBKR dividend is dropped (IBKR wins), other yfinance events survive.
  - **AC-D38.6 (regression)** Given the feature, Then the full offscreen suite is green and no D1–D37 criterion
    regresses.
- **Edge Cases:** no API news subscription → explicit state; zero positions → empty state; yfinance
  outage/rate-limit → "event data unavailable", chart unaffected; both sources empty → "no event data" state
  logged for the owner; per-symbol headline fetch failure (others still show); tick-59 parse garbage never
  raises; futures are skipped for dividends.

### D39 — Volume-burst alerts + symbol search — as-built / APPROVED 2026-10-13
- **Area:** `services/symbol_search.py` (`SymbolSearchService`, `MAX_SAMPLES=16`),
  `services/volume_baseline.py` (`VolumeBaselineService`, `robust_z`, `bucket_for_ts`,
  `DEFAULT_Z_THRESHOLD=4.0`, `MIN_WARMUP_BARS`, `N_BASELINE_BARS=30`), `services/alarm_service.py`
  (`evaluate_volume_burst`), `data/alarm_store.py`, `ui/watchlist_panel.py` (search box), `ui/ticker_session.py`
  (per-push burst eval, proxy sessions, `volume_baseline` table), `ibkr/market_data.py`
  (`req_matching_symbols`/`symbolSamples`).
- **Status:** **as-built / APPROVED 2026-10-13** (1009 tests green, 39 new). Feature; D1–D38 not reopened.
  Acceptance criteria **authored 2026-10-14 (Q45/DG46)** from the shipped behaviour and
  `tests/test_d39_burst_search.py`.
- **Backing tests:** `tests/test_d39_burst_search.py` (`test_ac_d39_1..4`).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D39.1 (search samples + select; z semantics)** Given a typed pattern, Then at most 16 samples
    (`symbol·secType·exchange`) are returned and selecting one resolves the contract and loads its chart; the
    burst z-threshold defaults to 4.0 and is tunable ≥ 1.0 (z-score semantics throughout — no K-multiple
    language).
  - **AC-D39.2 (debounce)** Given typing, Then at most one `reqMatchingSymbols` per 300ms window is issued;
    10 keystrokes in 500ms → ≤2 requests (only the final text is searched); a disconnected box refuses and
    issues nothing.
  - **AC-D39.3 (burst fires exactly once)** Given a warmed baseline, When a bar's per-minute volume scores
    z ≥ threshold, Then the burst alarm fires exactly once (toast + sound + `AlarmStore.triggered`); flat data
    never fires; a flat (zero-MAD) baseline yields a finite z above threshold on a real burst (never infinity).
  - **AC-D39.4 (re-arm + headless + index proxy)** Given a fired burst alarm re-armed, Then it re-enables; a
    burst alarm keeps its symbol in the headless monitored set; a burst alarm on an index (SPX) evaluates the
    **proxy tape's** bars (ES front month via D36's `INDEX_PROXY`) with the toast labelled proxy-derived
    ("Volume burst on ES tape (z=…)") and no session created for the index itself.
  - **AC-D39.5 (baseline integrity + regression)** Given the three-tier baseline (persisted `volume_baseline`
    table → one-time local `BarCache` prime → rolling-30 fallback), Then a baseline is never compared across
    contracts (front-month roll invalidates/tombstones the old key) and the warm-up gap is documented
    ("warming up (n/5)"); Given the feature, Then the full offscreen suite is green and no D1–D38 criterion
    regresses. *[AMBIGUITY 2026-10-14: the shipped tests explicitly label only AC-D39.1–AC-D39.4; AC-D39.5 has
    no dedicated test function, so it is authored here from the shipped baseline behaviour plus the batch
    regression convention (cf. AC-D37.5/AC-D38.6).]*
- **Edge Cases:** search with no matches → clear state; search while disconnected → disabled + message;
  z-threshold below 1.0 rejected; illiquid symbol (baseline near zero) → 1.0/min floor applies, no dust
  triggers; session open (<5 bars) → no evaluation, documented warm-up; contract roll → baseline invalidated;
  no company name in search results (10.51.1 API limitation — `ContractDescription` carries contract +
  derivativeSecTypes only).

### D40 — TWS daily-lifecycle pause/resume — as-built / APPROVED 2026-10-13
- **Area:** `ibkr/client.py` (`DisconnectClass`, `connectionClosed` classification, backoff loop,
  `ConnectionState`), `services/alarm_monitor.py` (`pause_all`/`resume_all`/`format_gap_report`, per-symbol
  pause start), `ui/ticker_session.py` (`monitoring_paused`, `_monitor_subscribe_pending`, `prev_price`
  re-seed), `ui/main_window.py` (`_tws_paused`, conn badge, gap report).
- **Status:** **as-built / APPROVED 2026-10-13** (1020 tests green, 11 new; Code Reviewer CHANGES REQUIRED →
  re-check APPROVED after the resume/reconcile call-order fix). Feature; D1–D39 not reopened. Acceptance
  criteria **authored 2026-10-14 (Q45/DG46)** from the shipped behaviour and `tests/test_d40_tws_lifecycle.py`.
- **Backing tests:** `tests/test_d40_tws_lifecycle.py` (`test_d40_1..4`).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D40.1 (disconnect classification + pause)** Given a live connection, When `connectionClosed()` fires,
    Then the disconnect is classified `TWS_GONE`, all alarmed symbols are marked paused, and the badge shows
    "Monitoring paused — TWS disconnected" in amber (never green); no prior connect → unclassified; a
    poll-driven drop → not classified; error 502 during paused backoff logs at debug (but surfaces at startup).
  - **AC-D40.2 (resume without phantoms)** Given a morning login after a pause, Then the app reconnects
    **without a restart**, runs the D27 subscription replay, then reconciles, then resumes; every session's
    `prev_price` is re-seeded to None (first-tick-no-eval guard) so resume alone fires nothing while a genuine
    live crossing fires exactly once; a session torn down mid-pause is re-created by reconcile and re-seeded.
  - **AC-D40.3 (gap report + staging)** Given the pause, Then per-symbol pause starts are recorded and the
    resume surfaces a gap report naming the symbols and the interval ("ES, NQ unmonitored 22:14–09:40"); an
    alarm created while TWS is down is staged paused and completes its subscribe on resume.
  - **AC-D40.4 (transient drops unaffected)** Given a non-TWS-gone disconnect, Then it keeps the fast D27 path —
    no paused badge, no pause flags, no gap accounting — and reconnect leaves `prev_price` untouched.
  - **AC-D40.5 (regression)** Given the feature, Then the full offscreen suite is green and no D1–D39 criterion
    regresses. *[AMBIGUITY 2026-10-14: the shipped tests explicitly label only AC-D40.1–AC-D40.4; AC-D40.5 has
    no dedicated test function, so it is authored here from the batch regression convention
    (cf. AC-D37.5/AC-D38.6).]*
- **Edge Cases:** stale `TWS_GONE` cannot downgrade a later transient drop (`_last_disconnect_class` reset on
  connect); reconnect timer cancel-then-armed (no double-arm); backfill waves in flight keep generation
  fencing; TWS daily auto-restart classifies as TWS-gone; 502 at startup with no prior connection surfaces.

## Assumptions Log
| # | Assumption | Rationale | Confirmed? | Date |
|---|---|---|---|---|
| A1 | This repo is the Python reimplementation of the React reference app | Consistent across `dev_docs/delta.md` and the since-deleted `PENDING_IMPLEMENTATION_PLAN.md` | n | 2026-09-19 |
| A2 | Phases 1–10 are effectively implemented | All referenced modules and tests exist on disk (the roadmap that defined them was deleted 2026-10-15) | n | 2026-09-19 |
| A3 | Defects are diagnosed against the dev build (`python main.py`), not the packaged `.app` | Dev build is the working target; bundle untested per-defect unless stated | n | 2026-09-19 |
| A4 | "Test conditions pass" means the existing offscreen suite plus new per-defect checks | Q3 + Q8 confirmed + repo test conventions | y | 2026-09-19 |
| A5 | D2 chip keeps current 2-decimal format, or matches axis tick precision if that differs | Decimals still unspecified; **placement since revised by Q33** (chip moved to the Y-axis lane, grey pill + white text) — see D2/A25. The original "option (a)" inside-plot right-alignment no longer applies | n | 2026-09-19 (placement revised 2026-09-27) |
| A6 | D3 magnifier reverts to Cursor when symbol/timeframe changes | Not stated by user; safety default | n | 2026-09-19 |
| A7 | D1 exact orange/blue hex picked to match the app theme at 10% alpha | User specified colour name + opacity only | n | 2026-09-19 |
| A8 | D4 glyph size is 14px/700 for `-`/`+`/`Reset` and 21px/700 for `⌕` (magnifier 50% larger), and the inside-data-area position is `panel.width - ctrl.width - axis_width - 12` | Q15 confirmed with magnifier +50% (21px vs 14px); Q16 confirmed current fine | y | 2026-09-19 |
| A10 | D6 wick is ~1px thin line behind the body (body ≥4× wick), colour follows direction, wick extends beyond body when shadow exists | Q18 confirmed 2026-09-19 | y | 2026-09-19 |
| A9 | ~~D5 volume log is always on, X stays linear, zero-volume bars map to 1.0 with yRange lower 1.0~~ **SUPERSEDED by A12 (D8 linear)** | User said "y-axis needs to be logarithmic" without specifying toggle or zero handling — later rejected in favour of linear (Q20) | n (superseded) | 2026-09-19 |
| A11 | D7 gap is 35% of bar spacing (body half-width 0.325× median_diff) rather than the current 20% (0.40) | Q19 confirmed "go 35% gap for now" | y | 2026-09-19 |
| A12 | D8 volume is linear on Y with `yRange=(0, nice_max)` where `nice_max` is `max_vol*1.1` rounded to the next nice tick from `[10k, 50k, 100k, 250k, 500k, 1.0M, 1.5M, 2.0M, 2.5M, 5M, 10M]`, no negatives, and bars are green/red by `close>=open` | Q20 confirmed 2026-09-19 | y | 2026-09-19 |
| A13 | D9 volume bar width follows price candle width (`width = w*2`, gap 35% of `median_diff`) | Q21 correct — matching price 35% gap | y | 2026-09-19 |
| A14 | D10 volume toggle is a checkable control (default visible), hides/shows `volume_plot` via the splitter, and is not persisted | Q22 Top left of the volume panel (bottom left of price chart) confirmed, no persistence specified | y | 2026-09-19 |
| A15 | D11 drawing price labels are inside the plot at the right edge (`anchor=(1,0.5)`, `x = view_rect.right() - 4`) with the drawing’s colour, one per price, stacking when nearby | Q23 correct — inner right side as proposed | y | 2026-09-19 |
| A16 | D12 zone settings popup is titled `Rectangle` with 4 tabs Style/Text/Coordinates/Visibility, Extend omitted (always both sides), double-click on zone opens it | Q24 Extend omitted confirmed | y | 2026-09-19 |
| A17 | D13 watchlist dock width is freely draggable [150, floor(0.50×W)] (chart ≥400px ⇒ max = min(0.50×W, W−400)), persisted across restarts (QSettings or DB), default ~220px, clamped on restore/resize; floating not constrained | Q25 50% freely draggable + Q26 persist yes confirmed 2026-09-20 | y | 2026-09-20 |
| A18 | D14 watchlist double-click anywhere on row (any column) triggers chart load identical to manual Load Chart with current timeframe/ext-hours, updates symbol_input | Q27 double-click row + Q28 identical to Load Chart confirmed 2026-09-20 | y | 2026-09-20 |
| A19 | D14 no-op when double-clicked symbol equals _current_symbol (case-insensitive) or when IBKR disconnected (status message only, no request); header/empty area also no-op | Q29 no-op confirmed 2026-09-20 | y | 2026-09-20 |
| A20 | D15 horizontal line settings popup is titled `Horizontal line` with 4 tabs Style (Line) / Text (12, B/I, Add text, Top/Right) / Coordinates #1 (price) 7548.85 / Visibility (Ticks–Ranges) | Q30 correct — four tabs as per attachments | y | 2026-09-20 |
| A21 | **ESC-004 visual gate applied:** a UI-visual decision is only "clarified" once its Defect-Entry `Visual reference:` line names a concrete artifact and the user has confirmed it; otherwise it is a provisional assumption recorded here | Process fix for the D5→D8 rework (screenshot arrived after build); see AC-G.1 | n | 2026-09-27 |
| A22 | D10 volume toggle **icon/affordance** is the **text label `Volume`** (a checkable text-label control), confirmed by the user — not an eye icon or a bar glyph | Q31 answered 2026-09-27 (user chose the text label `Volume`) | y | 2026-09-27 |
| A23 | D10 volume toggle **placement** is the **top left of the volume panel (bottom left of the price chart)** — **CONFIRMED 2026-09-27** (flipped from provisional) | Q22 named the location; Q32 originally accepted it as provisional; the user confirmed the placement on 2026-09-27 | y | 2026-09-27 |
| A24 | D8 volume `nice_max` is generated by a continuous scaling formula whose mantissa set is **`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (pinned by RG-002, resolved 2026-09-27, to reproduce the user-confirmed Q20 values `750K` and `1.5M`), not the original fixed list. **No fixed `10k` floor** (smallest generated value `100`) and **no fixed ceiling** (scales as `10^k`). The old list is retained **only** as a test fixture. | ESC-003/ESC-008 fix; RG-002 resolved 2026-09-27 — the family is pinned by confirmed Q20 evidence, so no further user confirmation is needed for the value set. Supersedes A12's list and removes the D8 10k floor | n | 2026-09-27 |
| A25 | D2 chip **appearance and lane placement** (Y-axis lane outside the plot, right of the vertical axis line; grey pill with white text; axis-tick-label overlap permitted) is **CONFIRMED 2026-09-27** — the reference is the agreed target. **Scoped carve-out:** **dock-open visibility** (the chip must not be hidden by the Active Trader / Portfolio dock) is **NOT** covered by this reference and remains a separately verified acceptance criterion (`AC-D2.1`) + edge case requiring independent Code Reviewer verification after Build | Q33 answered 2026-09-27 by a design change; the user confirmed the appearance/placement reference on 2026-09-27 | y (appearance/placement) — dock-open visibility separately verified | 2026-09-27 |
| A26 | **ESC-002 reverse direction (Q35):** selecting a drawing tool while the router is in `ZOOMING` **exits `ZOOMING` and activates the drawing tool**. Now a **requirement** (folded into `AC-D3.7` together with the forward direction), **CONFIRMED 2026-09-27** (flipped from provisional) | Originally carried as an assumption because only the forward direction had been answered; the user confirmed the reverse rule on 2026-09-27. Plan MUST encode it in the router transition table as required behaviour, not as an assumption | y | 2026-09-27 |
| A27 | **D16 diagnosis:** the hole is caused by the delta fetch being anchored to *now* with the fixed `TIMEFRAME_CONFIG` duration instead of reaching the cached span / detecting a missing span; both the price and volume panels consume the same `_bars` list, so one bar-list fix serves both | Validated against the live `SPY 5 mins` cache (internal hole 2026-09-19…09-27 with newer bars 09/28+) and the current `load_chart`/`_refresh_candles` code; `get_last_timestamp` exists but is unused | y (repo-validated 2026-10-02) | 2026-10-02 |
| A28 | IBKR will actually return the missing 5-min bars for 2026-09-21…2026-09-25 (the hole is within IBKR's intraday retention), so the backfill can fill it; if not, `AC-D16.4` applies (shortfall surfaced, no fabrication) | The span is ~1–2 weeks old at report time; IBKR normally retains 5-min data far longer. Not user-confirmable — a data-availability risk, not a requirements ambiguity | n | 2026-10-02 |
| A29 | Genuine non-trading spans (weekend/holiday/overnight) render **empty** and are **not** compressed or filled; only missing **trading-session** bars count as the defect | **Q38 answered 2026-10-02** — user confirmed "stay empty"; collapsing non-trading time is out of scope (FS7) | y | 2026-10-02 |
| A30 | The D16 fix and its verification apply to **all** timeframes (`1 min`, `5 mins`, `15 mins`, `1 hour`, `4 hours`, `1 day`) and **any symbol**, not only `SPY 5 mins` | **Q39 answered 2026-10-02** — user confirmed "all timeframes + any symbol"; the fetch-window mechanism is timeframe-generic (`TIMEFRAME_CONFIG`) | y | 2026-10-02 |
| A31 | Live/real-time bars are not persisted to the cache (only historical fetches call `BarCache.save_bars`); this is not the cause of the reported hole but is a related latent gap (see `design_gaps.md` DG18) and does not change D16, because the load-time backfill covers it | Code inspection: `_on_aggregated_bar` → `update_last_bar` only touches the in-memory `_bars`; only `_on_historical_data_end` calls `save_bars` | n | 2026-10-02 |
| A32 | The Q37 phrase "from the last cached bar up to now" is implemented as an **outcome** requirement — the bar series is continuous over its displayed span — which necessarily heals the reported **internal** hole, not only a tail gap after `MAX(ts)` (a tail-only anchor would leave the reported hole unfixed) | The user's own goal in Q37 was "so the chart is continuous"; the reported repro is an internal discontinuity; recorded in `design_gaps.md` DG21 and observed by `AC-D16.1`/`AC-D16.5` | y (derived from Q37) | 2026-10-02 |
| A33 | **ESC-023 correction — New Year's year-end accounting exception:** the US-equity New Year's observed-day shift does not apply when the preceding Friday is Dec 31; **Dec 31 is a trading day** when Jan 1 of the next year is a Saturday, and **no New Year's holiday is observed**. Only **actual** market holidays (shifted normally) and weekends are genuine closures | Code Reviewer ESC-023 (a naive Saturday→preceding-Friday shift closed Dec 31; wrong for US equities — NYSE Rule 7.2 year-end accounting-period exception; NYSE's own calendar states no New Year's Day holiday is observed when Jan 1 is a Saturday); user approved the correction 2026-10-02 | y (approved for correction 2026-10-02) | 2026-10-02 |
| A34 | **D17 target geometry — RESOLVED (B1, B4).** The watchlist cap is `floor(0.50 × chart_area)` (B1; **supersedes D13's Q25 window-width denominator**), the handle drags **both directions** (B4), min **150px**, default **~220px**, persistence still required (Q26), and the cap is enforced **during the drag** (not only on `resizeEvent`). Chart minimum ~400px per B3. | B1/B4 answered by the user 2026-10-03; B1 explicitly corrected the Q25 denominator | y | 2026-10-03 |
| A35 | **D18 grouping — RESOLVED (B2).** Active Trader and Portfolio are **one right-dock region** containing both sections stacked vertically, so they are inherently equal width; the **40%-of-chart-area** cap applies to that single region. The current two-`QDockWidget` structure is re-shaped into one region. | B2 answered by the user 2026-10-03 ("one right-dock region, stacked — Recommended") | y | 2026-10-03 |
| A36 | **D18 persistence default (non-blocking, UNCHANGED):** the right region's width/visibility is **not persisted** unless the user asks, matching D10's volume-toggle precedent (Q22: not persisted). B3/B4 did not add a persistence requirement for the right dock (only the watchlist keeps Q26 persistence, per B4). | D13 explicitly required persistence for the watchlist (Q26) and B4 re-confirmed it, but the user did not request it for the right region; recorded as a non-blocking default (not a blocking question) | n | 2026-10-03 |
| A37 | **D19 diagnosis:** the root cause of "D17 does not work in the real app" is the toolbar's ~1716px `minimumSizeHint` pinning the central widget (not the 50% cap, which computes correctly to 858px at chart_area 1716). **Resolution (B5, 2026-10-05):** wrap the existing toolbar in a **horizontal scroll / elide** container **in place** (one ~36px row, still inside the central widget) so its minimum width no longer pins the layout | Repo-validated against `ui/main_window.py:100–223` (`[historical]` 2026-10-05); the Orchestrator's offscreen probe agrees (watchlist stayed 150 after driving to cap with the toolbar visible); B5 chose scroll/elide 2026-10-05 | y (repo-validated 2026-10-05; fix chosen by B5) | 2026-10-05 |
| A38 | **D19 covers both D17 and D18 symptoms** (they share the one toolbar-pinning root cause), and the fix must make the D17/D18 criteria hold in a **toolbar-visible** window; the D17/D18 criteria themselves are unchanged. **B6:** the watchlist cap **stays `floor(0.50 × chart_area)`** — no cap change | Both symptoms are produced by the same no-slack splitter; the probe shows the watchlist pinned and the right dock pushed to the window edge; B6 answered "Keep 50%" 2026-10-05 | y (derived from the validated diagnosis; B6 answered 2026-10-05 |
| A39 | **D20 target — RESOLVED (B7/B8, 2026-10-06):** the toolbar strip keeps the **content row at ~36px** and adds a **reserved horizontal-scrollbar lane below** it, so the **total strip is ~50–52px** and label descenders are no longer overlapped; the content row does **not** grow and the strip does **not** reach ~60px. The scrollbar is **as-needed** in that reserved lane (shown only on overflow), and the reserved lane keeps the strip height stable in both states. | B7 answered by the user 2026-10-06 (verbatim: "Content row 36px + scrollbar lane (~52px total)"); B8 answered 2026-10-06 (verbatim: "As-needed in a reserved lane"). Supersedes `AC-D19.4`'s `<= ~40px` bound to a ~52px container bound | y (B7/B8 answered 2026-10-06) | 2026-10-06 |
| A41 | **D21.7/D21.8 active-button highlight (`VIS-D21.2`) — RESOLVED (user-confirmed 2026-10-06).** An active/selected button uses a distinct filled background (accent tint) plus a border, clearly distinguishable from the inactive state, applied while active and removed when inactive. The user confirmed the highlight convention on 2026-10-06 (D21.7/D21.8, B12 "As recommended"); exact colours remain an implementation detail while the outcome is the testable requirement. | The user asked to "highlight the button in some way"; the convention is confirmed and the outcome (a persistent, distinguishable highlight) is testable. See `VIS-D21.2`, `AC-D21.7.1`/`AC-D21.8.1` | y | 2026-10-06 |
| A42 | **`VIS-D21.1` diagonal strike-through — RESOLVED (user-confirmed 2026-10-06).** A single straight line from the top-left to the bottom-right of the label/button text area, ~1–2px, in the label's foreground colour, clearly visible against the button background. The user confirmed the diagonal convention on 2026-10-06 (B12; D21.11/D21.12/D21.13); exact line width is implementation detail. | The user described the diagonal direction and confirmed it; the outcome (a visible diagonal line when hidden/off) is testable. See `VIS-D21.1`, `AC-D21.11.2`/`AC-D21.12.1`/`AC-D21.13.4` | y | 2026-10-06 |
| A43 | **D21.9 alarm edit UX — RESOLVED (B13, 2026-10-06).** Clicking a row's **Edit** button opens a small **edit dialog** (price, condition, sound, note) with **Save/Cancel**; **Save persists immediately** via `AlarmStore`; a **triggered/set alarm may also be edited and keeps its state** (not re-armed/reset); Cancel discards. | B13 answered by the user 2026-10-06 ("As recommended") | y | 2026-10-06 |
| A44 | **D21.10 smart-alarm preview line + condition default — RESOLVED (B13, 2026-10-06).** The yellow dashed line is drawn **while the popup is open**, follows the price spinbox **live**, and is **removed when the popup closes** (replaced by the real alarm line after Add); the auto condition default (Cross Below when current > alarm price; Cross Above when current < alarm price) is applied **only when the popup opens** and is **user-overridable**; when the current price is **unknown**, default to **Cross Above**. | B13 answered by the user 2026-10-06 ("As recommended") | y | 2026-10-06 |
| A45 | **D21.4 collapse semantics — RESOLVED (B9, 2026-10-06).** Collapse only the **gaps between trading sessions** (overnight/weekend/holiday) on **intraday timeframes**; `1 day` is a **no-op**; within-session spacing is preserved; D16 backfill/no-silent-hole rules unchanged; with Ext Hours ON the D1 pre/post bands still render; with **RTH selected** only RTH bars show and all non-RTH time collapses. Supersedes the **display** part of `AC-D16.3`. | B9 answered by the user 2026-10-06 ("Collapse between-session gaps") | y | 2026-10-06 |
| A46 | **D21.5 addable columns — RESOLVED (B10, 2026-10-06).** The addable set is the **existing 7 columns** (`Symbol, Last, Bid, Ask, Chg, Chg %, Vol`); "add" = re-showing a removed column; the **Symbol column cannot be removed**; the column layout is **persisted** across restarts; a right-click on a column header opens the add/remove/rearrange popup. | B10 answered by the user 2026-10-06 ("Existing 7 columns, persisted") | y | 2026-10-06 |
| A47 | **D21.6 volume-height baseline — RESOLVED (B11, 2026-10-06).** Baseline is the current **120px** maximum cap; the volume pane can grow to **at least 360px** (3×), with the price pane keeping a **~200px minimum**. | B11 answered by the user 2026-10-06 ("≥360px (3× the 120px cap)") | y | 2026-10-06 |
| A40 | **D20 — D17/D18 unaffected:** raising the toolbar strip's height changes only vertical space (slightly shorter chart) and does not alter the horizontal dock-width model, so the `AC-D13`/`AC-D17`/`AC-D18`/`AC-D19` horizontal criteria stand. | The reported defect is vertical (scrollbar overlapping text); the D19 wrapper's horizontal minimum-width behaviour is unchanged. B7/B8 answer only the vertical/scrollbar-lane question | y (B7/B8 answered 2026-10-06) | 2026-10-06 |

| A48 | **D22 add/remove affordance + placement — RESOLVED (B15a/B15b, 2026-10-07).** The add affordance is a small **`+` button on the watchlist header strip** next to the "Watchlist" toggle **plus a right-click "Add symbol…"** entry; the input surface is a **small modal dialog** (text field + OK/Cancel); removal is a per-row delete and/or a right-click **"Remove symbol"** entry. The user chose these explicitly (B15a/B15b); exact styling is an implementation detail. | B15a/B15b answered by the user 2026-10-07; consistent with the `VIS-D21` precedent (A41/A42) that the user-named placement/behaviour is the requirement while exact styling is an implementation detail | y | 2026-10-07 |
| A49 | **D22 add while IBKR is disconnected — RESOLVED (B16b, 2026-10-07):** adding is **disallowed while disconnected** (the affordance is disabled/denied and nothing is added, subscribed, or persisted). Live validation (B16) therefore only runs when connected; on reconnect `_restore_watchlist` repopulates from the DB. | B16b answered by the user 2026-10-07 ("Require connection to add"); supersedes the earlier provisional "add-while-disconnected persists" default | y | 2026-10-07 |
| A50 | **D22 input normalisation:** trim + uppercase; reject empty/whitespace-only input; treat a case-insensitive duplicate as a no-op with a message (no duplicate row). **CONFIRMED** as the intended behaviour (non-blocking default, now recorded final). | Reasonable defaults that need no user decision; logged per the Quality Bar rather than silently baked in; no contrary user direction | y | 2026-10-07 |
| A51 | **D22 scope — RESOLVED (B14, 2026-10-07):** scope is **add + remove**; **reordering is NOT in scope** (a future suggestion, FS10). | B14 answered by the user 2026-10-07 ("Add + remove") | y | 2026-10-07 |
| A52 | **D22 empty-watchlist persistence (non-blocking default):** if the user removes **every** symbol, the watchlist stays **empty** across restarts — the `_restore_watchlist` seed-if-empty branch must **not** re-seed `DEFAULT_WATCHLIST` after an explicit removal (otherwise "remove" cannot empty the list). | The seed-if-empty behaviour exists today for a first run; D22's remove makes an explicitly-emptied list meaningful. Logged as a default rather than a blocking question because it is a corner case and the sensible outcome is clear; the user can override | n | 2026-10-07 |
| A53 | **D23.1 — capability-guarded, documented cancel (ESC-030):** the pinned `ibapi` (`9.81.1.post1` at D23 report time; `10.51.1` now — `hasattr` still **False**, re-verified 2026-10-14) exposes **no** `EClient.cancelContractDetails`, so the required behaviour is a capability-guarded best-effort cancel plus an in-code note; the task-level `AC-D22.2.3` wire-cancel mandate is **superseded/corrected** and architecture `S3` is reconciled. The local invalidation (`ContractLookupService` bounded QTimer + `cancel_all`) is the safety net. | Repo-validated: `hasattr(EClient,'cancelContractDetails') is False` on the pinned dep; `ContractLookupService.cancel`/`cancel_all` already drop the pending entry + stop the timer; no production path calls `cancel_contract_details`. The user approved fixing ESC-030; capturing the guard as the requirement needs no blocking question | y (evidence-derived; user approved the fix 2026-10-07) | 2026-10-07 |
| A54 | **D23.1 — the wire cancel is dead code today:** `MarketDataManager.cancel_contract_details` is not called by any production path (only by its own D22 test). Making it capability-guarded + documented is a forward-correctness fix; it changes no D22 observable behaviour. | Source-validated 2026-10-07 (grep: only the definition + `tests/` references); `_on_disconnected` uses `ContractLookupService.cancel_all` | y (source-validated) | 2026-10-07 |
| A55 | **D23.2 — only `_row_data` carries a stale row key after `remove_symbol`:** `_req_to_row` (removed row's reqIds popped first), `_prev_close`/`_last_price` (reqId-keyed) and `_flash_timers` (removed row stopped first) are already explicit; the stale-key branch is the **last-row** removal, where no later key overwrites the removed index. | Reproduced 2026-10-07: 3-row panel, `remove_symbol(last)` → `_row_data.keys() == [0,1,2]` while `rowCount()==2`; middle-row removal leaves `[0,1]` | y (reproduced) | 2026-10-07 |
| A56 **[NEW v1.2]** | **D24 — pop-out timeframe/mode/extended-hours frozen at creation:** no per-pop-out switcher; the snapshot comes from the main chart at pop-out time. Studies stay per-symbol shared, so a study edit propagates to pop-outs even on different timeframes (the `(symbol, timeframe, studies-hash)` cache handles it). | User demanded "no tool bars" in pop-outs; a switcher would need chrome. Flagged as an open question in the v1.2 feature doc — frozen is the specified default | y (user-specified 2026-10-12) | 2026-10-12 |
| A57 **[NEW v1.2]** | **D24/D25 — toast + sound fire exactly once per trigger event from `MainWindow`**, regardless of which session fired or how many views show the symbol; pop-outs show the visual alarm marker only, never sound. | User's flow has many windows per ticker; exactly-once notification is the only sane semantic | y (user-specified 2026-10-12) | 2026-10-12 |
| A58 **[NEW v1.2]** | **D25 — headless monitoring is event-driven, not a literal 1-minute poll:** 1-minute tracking granularity via `BarAggregator("1m")`, evaluation on every 5-sec push → second-level firing latency. | "Tracked on a 1 min interval" read as resolution, not latency; prompt firing strictly dominates a 60s poll. Flagged as open question 5 in the v1.2 feature doc | y (analyst interpretation; user asked for the outcome) | 2026-10-12 |
| A59 **[NEW v1.2]** | **D25 — no phantom trigger when monitoring starts beyond the alarm level:** only genuine subsequent crosses fire; stale crosses are never "caught up". | Matches the existing `evaluate_alarms` prev/curr cross semantics; avoids false triggers on monitor start | y (specified in feature doc §4.7/AC-D25.3) | 2026-10-12 |
| A60 **[NEW v1.2]** | **D25 — headless sessions issue zero historical requests** (cache-seed only) to protect IBKR historical pacing. | Monitoring needs only a seed price; backfill waves are for charts | y (specified in feature doc FR-7.4) | 2026-10-12 |
| A61 **[NEW v1.2]** | **D24/D25 — session teardown rule:** a session is destroyed only when `views == 0 AND NOT monitored`. | Follows from the pop-out keep-alive flow and headless monitoring; replaces the implicit "one chart = one lifecycle" model | y (user-specified flows 2026-10-12) | 2026-10-12 |
| A62 **[NEW v1.2]** | **D24 — one realtime-bar subscription per symbol**, enforced by refcounting (first holder subscribes, last holder releases). | IBKR pacing budget (`MAX_REALTIME_BARS_PER_10_MIN = 60`) and the 10-pop-out design both require it | y (specified in feature doc FR-6.1) | 2026-10-12 |
| A63 **[NEW v1.2]** | **D25 — monitored-set pacing guardrail:** if alarmed tickers would exceed the realtime-bar budget, most-recently-active symbols win and a status-bar warning names the unmonitored ones. | Typical use is far below the cap; this is a guardrail, not a feature | n (analyst default) | 2026-10-12 |
| A64 **[NEW v1.2]** | **D24 — single-writer invariant:** the main chart is the sole writer of a symbol's drawings/alarms/studies; stores stay last-writer-wins with no versioning, and the invariant is documented where the session work lands. | User-specified "drawing limited to main chart"; avoids silent cross-view clobbering | y (user-specified 2026-10-12) | 2026-10-12 |
| A65 **[NEW v1.2]** | **D26–D28 are corrective batches:** they fix documented defects and change no D1–D23 feature criterion; D1–D23 are not reopened. | Deep-dive review 2026-10-12; user directed documenting all identified bugs | y (user-directed 2026-10-12) | 2026-10-12 |
| A66 **[NEW v1.2]** | **D24 — pop-out always-on-top defaults OFF (standard windows):** the user can toggle it per window via the header context menu. | Owner-confirmed 2026-10-14 (Q43); matches `ui/popout_window.py::PopoutWindow` (`self._always_on_top = False` — `:56`; `_toggle_always_on_top` applies `Qt.WindowStaysOnTopHint` — `:289`; indicative) | y | 2026-10-14 |
| A67 **[NEW v1.2]** | **D37 — depth heatmap defaults ON:** the `DepthHeatmapItem` is created unconditionally, overriding the reviewer's OFF suggestion (D36 footprint stays OFF). | Owner-confirmed 2026-10-14 (Q44); matches `ui/chart_panel.py::ChartPanel.__init__` (unconditional add — `:368`; `_depth_enabled_ui = True` — `:370`; indicative) | y | 2026-10-14 |
## Documentation Maintenance Requirements

> Added 2026-09-27 to resolve **ESC-011** (documentation drift) and to carry the
> ESC-004 process gate. These are requirements on the *repository's own docs*, not on
> shipped code; the Requirements Analyst records them here because the owning files
> (`usage.md`, and formerly `PENDING_IMPLEMENTATION_PLAN.md`) are root-level docs the Analyst does
> not edit.

> **Update 2026-10-15 — `PENDING_IMPLEMENTATION_PLAN.md` was deleted by the owner.**
> DOC-1's correction had been applied and DOC-2 was closed (all ten phases marked
> `✅ COMPLETE`) *before* the deletion, so both are **satisfied and now moot** — the file
> they governed no longer exists. DOC-3 (orphaned bytecode) was closed separately via
> ESC-001. `docs/phase-changelog.md` is the surviving phase-by-phase record.

- **DOC-1 (test count/timing accuracy, ESC-011):** `usage.md` and
  `PENDING_IMPLEMENTATION_PLAN.md` MUST NOT state a test count or runtime that
  differs from a measured run at the current revision.
  - **Measured 2026-09-27 at `09070e8`:** `QT_QPA_PLATFORM=offscreen python -m pytest
    tests/` → **339 passed in 2.87s**.
  - **Stale values to correct** (`[historical]` 2026-10-02 figures): `usage.md:166` "Full suite (269 tests, ~1.5s)";
    `PENDING_IMPLEMENTATION_PLAN.md:364`, `:412`, `:458` "269 passed" *(that file was deleted 2026-10-15;*
    *`usage.md` now points the reader at `pytest` rather than a hard-coded total).*
  - **Recommended correction:** update each to **339 tests / ~2.9s** (or replace the
    hard-coded numbers with a pointer to the CI/build log so they cannot drift again).
- **DOC-2 (phase completion markers, ESC-011):** `PENDING_IMPLEMENTATION_PLAN.md`
  MUST carry a completion marker that matches reality for every phase whose target
  files exist. Phases 1–5 (`:69`, `:129`, `:172`, `:213`, `:243`) currently have **no
  marker** although `ui/drawing_overlay.py`, `ibkr/market_depth.py`, `ibkr/orders.py`,
  `ui/active_trader_panel.py`, `ui/stop_loss_target_dialog.py` exist.
  - **Correction (decided 2026-09-27, Q34):** mark Phases 1–5 as `✅ COMPLETE` (matching
    the `Phase 6`/`Phase 7` style).
  - **Ownership split (Q34):** the **Requirements Analyst owns closing DOC-2** (this
    requirement and the mark-complete correction); **Code Reviewer verification is the
    confirming step** — Code Reviewer confirms the drift and then verifies the correction
    was applied (see ESC-011).
  - **Dependency note:** `PENDING_IMPLEMENTATION_PLAN.md` is **not in the Analyst's
    file-ownership table**, so the Analyst records the requirement and the ownership split
    here rather than editing that root doc. If a user/owner action is still needed to
    physically apply the `✅ COMPLETE` markers, that is a **recorded dependency**, not a
    blocking open question (Q34 is answered; DOC-2 is Analyst-owned to close).
  - **Resolution (2026-10-15):** the `✅ COMPLETE` markers were applied in commit `fe5a63f`
    and verified; the owner has since **deleted `PENDING_IMPLEMENTATION_PLAN.md`**, so DOC-2
    is satisfied and moot.
- **DOC-3 (no orphaned build artifacts, ESC-011):** the source-less
  `tests/__pycache__/test_db_schema.cpython-311-*.pyc` must be removed and the
  corresponding `tests/test_db_schema.py` committed as source (tracked by **ESC-001**,
  owned by BUILD).
- **DOC-4 (markdown-history retention):** superseded requirement sections (e.g., D5)
  are kept for history but MUST carry an explicit `SUPERSEDED BY <defect>` marker and
  a one-line pointer to the authoritative section, so no reader can mistake them for
  live criteria (this is the fix applied for **ESC-012**).

## Risks / Unknowns
| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | More defects may be reported after batch 1, expanding scope mid-build | M | M | Batch 1 declared complete; new feedback triggers a fresh requirements pass, not silent scope growth |
| R2 | Plan doc checkmarks are stale (many unchecked phases are actually built) | M | H | Verify actual behavior before treating any plan phase as open |
| R3 | Any change may touch the live-order path (real money) | H | M | The per-run "gated in TWS" assumption is **retired** (owner decision 2026-10-14, Q42); retained guards: `IBKR_PORT == 7496` fail-fast (`check_live_port`), explicit user action per order, confirm dialogs, and `validate_order()`; no automated test may transmit an order or connect to live TWS (Q9) |
| R4 | Vague UI defects ("looks wrong") yield untestable criteria | M | H | Every defect must have measurable Given/When/Then criteria and an edge case |
| R5 | Fixing one UI defect may regress another (shared chart/dock code) | M | M | Re-run full suite per fix; note regression risk per defect |
| R6 | D4 axis width varies with price magnitude; fixed 28px margin may still clip | M | M | Position left of dynamic `getAxis('right').width()` with 12px margin and `x>=8` clamp |
| R7 | ~~D5 log scale cannot display 0~~ **Resolved by D8** (linear axis, lower bound `0`); retained for history | — | — | Superseded by D8/Q20: linear `yRange=(0, nice_max)` has no zero-display problem |
| R8 | D6 wick/body thickness ratio may still be indistinct at extreme zoom/density | M | M | Fix wick at 1px regardless of zoom; body narrows with density but wick does not |
| R9 | D7 slightly narrower bodies could reduce legibility at very high density | L | M | Keep 4px body minimum from D6; gap remains positive; verify at 1-min dense view |
| R10 | D8 nice-max rounding could still leave little headroom if max is just above a nice boundary | L | M | Use `max*1.1` before rounding up; verify tick count stays 3–5 |
| R11 | D9 volume and price widths could diverge on Line/Area modes where price has no bodies | L | L | Define volume width from the same `w` even when price mode has no bodies; keep XLink |
| R12 | D10 toggle placement/affordance may not match user expectation | L | L | Icon = text label `Volume` confirmed (Q31); placement = top left of volume panel (bottom left of price chart) **confirmed 2026-09-27** (A23), not persisted; D10 is `CONFIRMED` under AC-G.1 |
| R13 | D11 price labels could overlap when many drawings share a similar price | L | M | Stack with small vertical offset or show topmost; verify at 09:00–10:00 dense zones |
| R14 | D12 zone popup with 4 tabs adds non-trivial UI surface; Extend omission may surprise users expecting the control | L | M | Omit Extend per user’s "extend both sides is required"; keep the other Style controls as shown |
| R15 | D13 50% max may still crowd chart on small screens; persistence restore could exceed new window size | L | M | Enforce chart ≥400px via `min(0.50×W, W−400)` and clamp on restore/resize; min watchlist 150px |
| R16 | D14 double-click could be mistaken for single-click row selection; accidental reloads | L | M | Require double-click (not single), any column; same-symbol and disconnected are no-ops; status message for disconnected |
| R17 | D13 floating vs docked width confusion — 50% rule mismatch | L | L | Apply 50% only when docked in LeftDockWidgetArea; floating geometry unconstrained |
| R18 | D15 horizontal line popup duplicates zone popup structure; Text tab font size 12 vs zone 14 may confuse | L | L | Keep D15 Style as Line only and Text size 12 as per attachment; keep D12 Style with Border/Middle/Background |
| R19 | A UI-visual decision implemented without a confirmed visual reference (the D5→D8 failure mode) | M | M | AC-G.1 visual gate: no UI-visual fix proceeds until its `Visual reference:` line names a user-confirmed artifact; otherwise it is a provisional assumption (A21–A26) |
| R20 | D8 `nice_max` scaling formula changes the axis values of already-built (Batch 4) behaviour, invalidating the old fixed-list test | L | M | Keep the old list only as a fixture; update `tests/test_volume_linear.py` to the pinned `1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k` scale (AC-D8.4/8.5) — `1_050_000 → 1_500_000` and `2_200_000 → 2_500_000` are already correct, but `_nice_volume_max(0)` must become `100` (not `10_000`) per AC-D8.4 |
| R21 | D11 drawing price labels (inside the plot) can stack when a label run overflows the pane; the crosshair chip no longer shares that lane | L | M | Chip moved to the Y-axis lane (D2/Q33), so `AC-D11.4` is **label-vs-label only** (`>= 15 px` stacking, clamped to `view_rect.bottom()`); chip-vs-label priority no longer applies (ESC-006 re-scope by Code Reviewer) |
| R22 | D16 backfill of a very long closure could exceed IBKR pacing/bar limits if requested in one call | M | M | Chunk requests, respect `pacing_manager`, and bound each request's duration; surface any shortfall (`AC-D16.4`) |
| R23 | Backfilling/displaying a much larger cached range could degrade chart load/render performance for large caches | M | M | Keep the load O(N) and verify offscreen with a large seeded cache; bound displayed bars if needed; chunk backfill asynchronously |
| R24 | A naive "no gaps" rule could wrongly try to fill genuine closures/holidays | M | L | `AC-D16.3` scopes the requirement to trading-session bars only (Q38 confirmed): weekends/holidays/overnight stay empty and are not interpolated |
| R25 | ~~`requirements.md` was missing the literal existing-repo marker, so downstream agents could treat this repo as greenfield~~ **Fixed and stable** — the **Existing Repository** section (marker sentence + **Current Tech Stack**) is present and preserved on every rewrite | — | — | Retained as a standing rule: never drop, reword, or restructure away the marker sentence or the Current Tech Stack |
| R26 | D16's reported repro is an **internal** cache hole (newer bars cached after an older block); a tail-only "anchor to `MAX(ts)`" implementation would leave it unfixed and the defect would appear unresolved | M | M | `AC-D16.1`/`AC-D16.5` require continuity across the displayed span including internal holes; DG21 directs Plan to detect the missing span from the cached series, not just `MAX(ts)` |
| R27 | A naive Saturday→preceding-Friday observed shift can mark a genuine trading day (Dec 31) as a market closure, so a real bar hole there is misclassified as a "genuine closure" and left as a silent hole (ESC-023) | M | L | `AC-D16.7` states the explicit year-end accounting exception and `AC-D16.3` excludes Dec 31 of a Jan-1-Saturday year from "genuine closure"; Task Manager corrects `T37-T03`, Build updates `market_calendar` and its test, and Code Reviewer re-verifies ESC-023 |
| R28 | D17: fixing the watchlist to clamp during the drag could regress the existing D13 integration tests (`test_d10_d13_integration.py`) that assert the **old window-width** clamp math | M | M | Keep the `watchlist_max_width`/`clamp_watchlist_width` helpers as the single source of the cap; add a drag/dock-change hook that reuses them; **update D13's denominator to 50%-of-chart-area in lockstep (B1)** — update `AC-D13.1` and the integration tests to the chart-area cap rather than leaving them contradicting D17 |
| R29 | D18: raising the right-dock width could push the chart below its 400px minimum when the watchlist is also enlarged | M | H | **Resolved by B3 rule (`AC-D18.5`):** independent caps (watchlist 50%, right region 40% of chart area) each clamped against the remaining space with a hard ~400px chart minimum; clamp on resize **and on every dock change**; enlarging one dock can force the other to shrink, and the criteria assert `chart_area >= 400px` |
| R30 | D18: full-screen "reposition so it fits" could hide the right dock entirely on small displays | M | M | Made measurable by `AC-D18.1`: the region's geometry must lie within the window rect with a non-zero visible width; cap it at 40% of the chart area, keep the chart minimum (B3), and do not let content `sizeHint` force it off-screen (`AC-D18.6`) |
| R31 | D17: enforcing a cap during the drag could make the handle feel "stuck"; the user's report says it currently does not move at all, so both over- and under-enforcement are failure modes | L | M | Verify the handle moves **freely in both directions** between min (150px) and cap (`AC-D17.1`/`AC-D17.2`); only clamp past the cap (`AC-D17.3`). B4 confirmed both drag directions are required |
| R32 | D19: the **scroll/elide** toolbar fix could change the toolbar's height or make controls hard to reach, affecting chart space or usability | M | M | B5 selects **horizontal scroll / elide in place** (one ~36px row); `AC-D19.4` requires all controls reachable via the scroll/elide affordance and the central widget able to shrink; verify at wide and narrow widths |
| R33 | D19: removing the `toolbar.hide()` masking will make the existing D17/D18 tests fail until the fix lands; the suite is not green in between | M | H | Expected: the harness change is part of the fix; demonstrate the pre-fix failure (`AC-D19.6`) then green after; treat the intermediate red as intentional, not a regression |
| R34 | D19: the toolbar's minimum width differs between the offscreen platform and the real macOS window; a **scroll/elide** fix that only works offscreen could still fail in the real app | M | M | `AC-D19.6` requires a toolbar-visible window; also verify in the real dev build (`python main.py`) manually, not only offscreen |
| R35 | D20: raising the toolbar height takes vertical space from the chart and, if overdone, reduces chart height noticeably | L | M | **Resolved by B7:** the minimal change is the content row kept at ~36px plus a reserved scrollbar lane, total ~50–52px (not ~60px); the content stays a single row and the chart loses only a few pixels of height |
| R36 | D20: updating `AC-D19.4`'s height bound without updating the D19 test assertions leaves the suite red / contradictory | M | H | Update `tests/test_toolbar_scroll_d19.py` height assertions in lockstep (`AC-D20.6`) to the B7-confirmed ~50–52px container / ~36px content target; the supersession is recorded explicitly on `AC-D19.4` |
| R37 | D21.4 collapsing non-trading time is an x-axis model change: it supersedes `AC-D16.3`'s display rule and can affect session shading (D1), drawings (time-anchored), alarm positioning and the D7/D9 spacing | H | M | **Scope fixed by B9:** collapse only **between-session** gaps on **intraday** timeframes (`1 day` no-op); keep D16 backfill/no-silent-hole unchanged; update the D16/D1 tests that assert empty closures in lockstep; verify drawings/bands/alarms after collapse |
| R38 | D21.5 column configuration can break D14 double-click binding or lose values after reorder, and needs a persistence store | M | M | **Resolved by B10:** bind columns by field identity (not index); keep the Symbol column; persist the layout (QSettings or DB); test a reorder then a live tick and a double-click |
| R39 | D21.6 raising the volume pane's max height can squeeze the price pane below a usable height, especially on short windows with the oscillator present | M | M | **Resolved by B11:** target **≥360px** with a **~200px price-pane minimum** and a bounded splitter; verify at the target height and at a short window; no regression to D10 |
| R40 | D21.7/D21.8 highlight may be low-contrast in the dark theme or clipped in the D19 scroll wrapper | L | M | A41 confirmed 2026-10-06; use a high-contrast accent style; verify in the real dev build and offscreen; assert active vs inactive style differs |
| R41 | D21.13 collapsing the right dock to a button strip can conflict with the D17/D18 width model and `_apply_dock_widths` (chart-minimum rule, cross-clamp) | M | M | **Geometry fixed by B12:** one hidden → in-height collapse + other expands; both hidden → horizontal collapse to the button strip. Treat the collapsed region as hidden for the cross-clamp (as the existing `visibilityChanged` path does); assert the chart keeps its minimum in collapsed and expanded states |
| R42 | D21.9 editing a set/triggered alarm changes its semantics; a wrong edit could silently re-arm or disable a live alarm | M | M | **Semantics fixed by B13:** edit via a Save/Cancel dialog, persist immediately via `AlarmStore`, and a triggered/set alarm keeps its state; re-render the overlay/badge after the edit; test editing a triggered alarm |
| R43 | D21.10 the yellow dashed preview line must coexist with the modal dialog and must not leak onto the chart after the popup closes | L | M | **Lifecycle fixed by B13:** draw the preview while the popup is open, follow the spinbox live, remove it on close, and replace it with the real alarm line after Add; test open/close and live price changes |
| R44 | Batch 15 is large (13 sub-defects) and touches shared chart/toolbar/dock/alarm code; a single fix can regress another | M | H | Keep every fix independently tested (pre-fix red / post-fix green); re-run the full offscreen suite per wave; treat D1–D20 criteria as frozen |
| R45 | D22 scope is now fixed (**add + remove**, B14 answered) but removal interacts with the replace-all `set_watchlist`/seed-if-empty path and `clear()` on disconnect, and reordering stays out of scope | M | M | B14 answered 2026-10-07 (add + remove; no reorder); `AC-D22.6`/`AC-D22.7` assert the remove + restart outcomes; A52/DG40/DG41 record the persistence interactions; reorder remains FS10 |
| R46 | D22 unknown/invalid symbols cannot be validated offline (`get_contract_for_symbol` accepts any string), and the repo has **no** `reqContractDetails`/`contractDetails` path, so B16's live validation needs new IBKR request+callback plumbing and can fail on IBKR errors/timeouts | M | M | B16 answered 2026-10-07 (live `reqContractDetails` before add; reject unresolved with nothing persisted); `AC-D22.4` asserts added-on-success / rejected-on-failure; DG43 records the missing request path for Plan; a bounded wait avoids hangs |
| R47 | D22 persisting via the replace-all `set_watchlist` could race with `_restore_watchlist` seeding or with `clear()` on disconnect, losing or duplicating symbols (including re-seeding defaults after the list is emptied by removal) | M | M | Plan chooses the persistence mechanism (replace-all with the full desired list vs new add/remove helpers); `AC-D22.7` asserts the restart outcome; A52/DG40/DG41 record the seed-if-empty and disconnect interactions |
| R48 | D22 adding a context menu / `+` button to the watchlist header strip could shadow or break the D21.5 **column** header menu or the D21.11 collapse toggle | M | M | B15a answered 2026-10-07; `AC-D22.1`/`AC-D22.8` require the D21.5 column popup and the D21.11 collapse toggle (and D14 double-click) to remain unchanged; DG42 records the interaction; add the affordances without removing the header toggle |
| R49 | D23.1: correcting the task-level `AC-D22.2.3` mandate and its `_FakeClient`-based test could conflict with the (already-built) D22 tests, leaving the suite red if not updated in lockstep | L | M | Update `AC-D22.2.3` (task-graph) and `tests/test_ibkr_contract_details_d22.py` **in lockstep** with the guard; add a missing-capability case; keep the None/raises cases; the pre-existing suite stays green (712 tests) |
| R50 | D23.2: re-indexing `_row_data` incorrectly could shift a symbol's cached values onto the wrong row | L | M | Use the narrow fix (`self._row_data.pop(row, None)` around the existing shift) and assert `set(_row_data.keys()) == set(range(rowCount()))` for first/middle/last/only-row removals; keep `_rebuild_table`/`_set_cell` field-key binding (DG32) unchanged |
| R51 **[NEW v1.2]** | D24: extracting `TickerSession` from the 2291-line `MainWindow` touches the live bar/alarm/drawing paths; a wrong move breaks the one working chart | H | M | Extract in cluster order (data plane first), one cluster per change, full offscreen suite green between each; no big-bang rewrite (see architecture draft target sections) |
| R52 **[NEW v1.2]** | D24/D28: per-tick costs multiply by chart count — 10 live charts × full QPicture regen per 5-sec tick can stall the main thread in lockstep with the feed | H | H | D28.4 bounds bars, splits render layers, and wires the study cache **before** pop-outs ship; assert via render-call counters (AC-D28.4). **[RECONCILIATION 2026-10-12 — plan deviation accepted:** Phase 3 ships D24/D25 functionally on a feature branch with a measurable smoke gate (baseline tick-burst cost recorded at end of 3b; 3c asserts ≤2× baseline across 3 pop-outs + zero full QPicture regens per tick); **merge to main requires the Phase 4 AC-D28.4 gate.** The "before pop-outs ship" contract is thus enforced at merge time, not at feature-branch time. Validator-approved.] |
| R53 **[NEW v1.2]** | D24: fixing reconnect replay without fixing `eConnect` (or vice versa) changes nothing — the two halves of D27.3 are coupled | M | H | Plan them as one work item with a single drop/reconnect acceptance test (AC-D27.3) |
| R54 **[NEW v1.2]** | D25: headless sessions add realtime-bar subscriptions per alarmed ticker; a large alarm book could exhaust the 60/10-min pacing budget | M | L | FR-7.7 guardrail (most-recently-active first + warning); typical use far below cap |
| R55 **[NEW v1.2]** | D26: any order-path change touches real money; the existing suite **asserts the bracket bug** (`tests/test_order_builders.py::test_bracket_order_structure` / `::test_bracket_order_sell`; cited `:83-104` — indicative) and must be rewritten, not just extended | H | H | Rewrite those tests to assert the protective direction first (pre-fix-red), mocked `ib_client` everywhere, no test transmits an order (AC-Global invariant) |
| R56 **[NEW v1.2]** | D27: the overlay coordinate fixes (MACD/ICT/gaps/VIX) are one-liners, but the tests that missed them assert counts not positions — the same blind spot could hide other invisible-render bugs | M | M | AC-D27.2's x-in-view-range assertion pattern becomes the standard for every overlay test going forward |
| R57 **[NEW v1.2]** | D26.3/D26.8: transmitting real SL/TP legs and a kill switch are new live-order surface; partial implementation is worse than none (user believes they are protected) | H | M | Each ships only with mocked-client `placeOrder` assertions and explicit UI labelling of what is/isn't transmitted |
| R58 **[NEW v1.2]** | D24: `load_chart` parameterisation changes the signature every caller uses; missed call sites silently keep the old widget-reading path | M | M | Grep all callers (`_on_ext_hours_toggled`, watchlist double-click, tests); offscreen test loads without toolbar widgets (AC-D28.2) |
| R59 **[NEW v1.2]** | D27.7/D28.3: backfill and pacing changes alter IBKR request patterns; error-162 storms are timing-dependent and hard to reproduce offscreen | M | M | Pacing math unit-tested with monkeypatched time (AC-D28.6); chunk-cap + retry-once keeps worst case bounded |
| R60 **[NEW v1.2]** | D24–D28 are specified from a read-only review; behaviour on live TWS (real reconnects, real pacing errors) cannot be fully verified offscreen | M | H | Manual live-TWS verification checklist per batch before merge; no batch ships on offscreen-green alone |


---

## Status

**Status: READY_FOR_PLAN** — Batch 17 (**D23**, two D22 post-build quality corrections) was captured 2026-10-07
and is **CLARIFIED AND FINALISED 2026-10-07**. **D23.1 (ESC-030)** requires the contract-details cancel to be
**capability-guarded and documented** (the pinned `ibapi` — `9.81.1.post1` at D23 report time, **10.51.1** now — has no `EClient.cancelContractDetails`; the
local `ContractLookupService` invalidation is the safety net) and **supersedes/corrects the task-level
`AC-D22.2.3`** wire-cancel mandate, reconciling architecture `S3`. **D23.2 (ESC-031)** requires
`WatchlistPanel.remove_symbol` to leave **no stale row key** (`_row_data` keys exactly `range(rowCount())`) for
first/middle/last/only-row removals, with the missing last/first/only-row coverage added. Both are **nice-to-have
quality fixes the user approved**; **no blocking question was required**. **D22 is not reopened** — its feature
criteria (`AC-D22.1`–`AC-D22.9`) stand; D1–D22 are otherwise unchanged. The Existing Repository section
(marker sentence + Current Tech Stack) is preserved.

Status: READY_FOR_PLAN

**[NEW v1.2] Batches D24–D28 — as-built / OWNER-APPROVED 2026-10-14; Batches D36–D40 — as-built / APPROVED.**
Batches **D24–D28** are user-specified / analyst-drafted, built and merged to `main` (Phase 1–4, as-built at
`b366b19`), and **approved by the owner on 2026-10-14 (Q41)** — the earlier "DRAFT, owner review required"
marker is cleared. Owner decisions recorded 2026-10-12, with the 2026-10-14 resolutions:
- **DEC-1:** Per-session alarm evaluation approved as an intentional behavior change — X's alarms fire while
  viewing Y, and with zero X views open (headless). D25 conflict resolved.
- **DEC-2:** D25 evaluation is event-driven (A58): 1-minute tracking granularity, evaluation on every 5-sec
  push → second-level firing latency. The literal once-per-minute poll is rejected.
- **DEC-3:** D24.9 persists the pop-out set across restarts (symbol/timeframe/mode/ext-hours/geometry in
  SQLite; re-created on launch). Alarms/drawings/studies already persist via existing stores — no change needed
  there. Pop-out timeframe/mode frozen at creation is accepted long-term (A56 confirmed).
- **DEC-4 (RESOLVED 2026-10-14, Q42):** the old per-run "gated in TWS, don't worry" planning assumption is
  **retired** so **D26 may be planned/decomposed against the live-order path**. The safety behaviour that still
  holds is unchanged: `config/settings.py::check_live_port` fails fast unless `IBKR_PORT == 7496`; every order
  requires explicit user action; confirm dialogs remain; and no automated test
  transmits an order or connects to live TWS (Q9). The former "**G5**" reference in DEC-4 is **dangling** (no
  such item exists in the tree) and is recorded here as resolved.
- **RESOLVED 2026-10-14 (Q43):** pop-out always-on-top default is **OFF** (standard windows); the user may
  toggle it per window. Recorded as requirement **AC-D24.10** (resolves the former footer "Open:" item).
D1–D23 are not reopened.

**Batches D36–D40** are as-built and Code-Reviewer APPROVED (2026-10-13, per their Journey "As-built" notes).
Their acceptance criteria (`AC-D36.*`–`AC-D40.*`) are now **defined** in this file (feature sections `### D36`
through `### D40` in the Defect Register), authored 2026-10-14 from the shipped behaviour and its backing tests
(owner-directed, Q45; resolves DG46/FI-D24-1).

**D29–D35 are intentionally unassigned:** the batch numbering jumps `D28` → `D36`. There is no `### D29`–`### D35`
requirement text, journey, or downstream reference; this is a deliberate numbering gap (recorded 2026-10-14,
DG50), not missing content.

**Flagged Issues (all resolved 2026-10-14):**
- **FI-D24-1 / DG46** — resolved: D36–D40 feature sections + acceptance criteria added (Q45).
- **FI-D24-2 / DG48** — resolved: D24.9 reconciled into a single `AC-D24.9` block.
- **FI-D24-3 / DG49** — resolved: the intro cross-references corrected (Journeys 29–35, `AC-D24.*`–`AC-D40.*`,
  A56–A67, DG46–DG52).
- **FI-D24-4 / DG50** — resolved: the D29–D35 gap is recorded explicitly (above).
- **FI-D24-5 / DG47** — resolved: D24–D28 re-statused as-built/APPROVED (Q41).

**Source-citation convention (adopted 2026-10-14; resolves `design_gaps.md` DG56).** Code references in
this file and in `design_gaps.md` cite a **symbol** as the primary pointer — `path::symbol`, e.g.
`ui/main_window.py::MainWindow._open_popout`, `config/settings.py::MAX_POPOUTS`,
`ibkr/market_data.py::MarketDataManager.cancel_contract_details`. A symbol is what a reader should trust:
it survives line insertions, where a `file:NNN` / `file:NNN–MMM` range does not (commit `99fb8fa`, a
5-line toolbar insertion, invalidated roughly ten ranges in this file). A bare line number or range is
therefore **indicative only** — it records where the code sat when the sentence was written and may have
drifted since; resolve by symbol, not by line. References that describe code **as it was at their own
commit** (the dated "Observed in repository (validated …)" diagnoses for D17–D22, the D19/D20
implementation snapshots, the DG17 doc-drift figures) are kept verbatim and tagged `[historical]`; they
are deliberately **not** re-pointed at current lines. Where a stale range was load-bearing for a live
criterion it has been re-pointed at the symbol, with any companion line marked indicative.

**Requirements-vs-shipped-code audit (2026-10-14, advisory).** The acceptance criteria for D1–D40 were
spot-checked against the shipped code on this checkout (`262ec81`, 1020 passed / 0 failed): the numeric and named
facts (ports, caps, thresholds, timeframes, pinned dependencies), the D8 volume family, the D21 UI rules and the
D24–D40 criteria were re-verified against source, and every gap was then re-checked against
`docs/phase-changelog.md` (the as-built record of intent). Result: **in sync except for the items recorded as
`design_gaps.md` DG54–DG62** — pinned-`ibapi` version figures (DG54, explained and dated by the changelog's D36
item 38a.0), one stale DB-path bullet (DG55), drifted line citations (DG56 — **resolved 2026-10-14:** the `path::symbol`
convention adopted above was applied to the load-bearing citations), the D25 AC↔test mapping (DG57), D24
test coverage/mislabelling (DG58), the D19/D20 toolbar geometry figures (DG59), a duplicate `DG14` id (DG60), the
`AC-D28.6` doc-assert residue (DG61 — resolved-with-reference: the file was kept deliberately, only the version
literal remains) and the changelog's own stale phase/branch statuses (DG62 — **resolved 2026-10-14:** all six
stale claims are corrected in the changelog by commit `96b72c4`, verified against the file). The requirements-side figures are corrected in place;
the test/code-side items are Build's to fix. **No new blocking question; no requirement was invented.**

Status: READY_FOR_PLAN — D24–D40 owner-decided/as-built (D24–D28 approved and code-verified 2026-10-14;
D36–D40 as-built/APPROVED with acceptance criteria now authored); D1–D23 unchanged.
