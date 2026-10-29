# NDThinkChart — Requirements

> **Current baseline (appended 2026-10-28, Q-52 — navigation only, no criteria changed).** Chart engine: **Lightweight Charts only** — P6-T13 removed pyqtgraph 2026-10-27 (removal commit `6e35b27`, owner-approved; gate `docs/build/gate_P6_T13.md` records owner approval SATISFIED and the one-clean-live-session sign-off **WAIVED, NOT SATISFIED** — never write it satisfied). Active phases: **P7** (data-path batch, `docs/plan.md` § Phase P7) and **P8** (D48 weekly/monthly, drafted 2026-10-28, `Status: READY_FOR_PLAN`). Open requirements debt: `AC-D16.8` restatement (RG-P7-1, `ESCALATED_TO_REQUIREMENTS`), RG-D46-2…RG-D46-9 and RG-P7-2 (open, non-blocking, analyst-owned — see the open-items index in `docs/plan_notes.md`). Authority: `docs/README.md`. As-built history: `docs/phase-changelog.md` (indexed by `docs/CHANGELOG.md`). The D47 plan-time sentences in this file ("pyqtgraph retained and default", dual-engine selection, deletion gated on a future live session) describe the 2026-10-26 plan as drafted and are **superseded by the P6-T13 outcome above** — preserved as decision lineage, not current guidance.


> **[NEW 2026-10-28] Batch 23 (D48) — P8 lite: add `1 week` (2Y) and `1 month` (10Y) timeframes — OWNER-REQUESTED; lite lane (defaults A113–A120, no question round).** The owner asked for weekly bars covering 2 years and monthly bars covering 10 years (IBKR bar sizes `1 week` / `1 month` exist; today's picker stops at `1 day`). D48 adds the two `TIMEFRAME_CONFIG` rows (`1 week` → `1 week` / `2 Y`; `1 month` → `1 month` / `10 Y`), Monday-anchored weekly + calendar-month aggregation, planner/backfill treatment (daily+ timeframes skip the `AC-D16.8` intraday floor; day-presence is already bar-granular), UI picker inclusion, and RTH/ETH irrelevance for weekly/monthly; acceptance is **standalone-probe-verified durations + suite green**. Week-anchor day, month-span durations and the year-unit duration spelling are **analyst defaults** (A113–A120). **D1–D47 are NOT reopened** beyond the recorded timeframe-enumeration extension (`AC-D16.1`'s "all six timeframes" now reads eight). No blocking question remains (lite lane; no `open_questions.md` entry); `requirements.md` carries `Status: READY_FOR_PLAN`.

> **[NEW 2026-10-28] Batch 24 (D49) — pop-out robustness (5 findings + D49.6 timezone handoff, nothing dropped) — OWNER-ORDERED, EXTENDED 2026-10-29.** The owner ordered the full `POPOUT_CHART_CODE_TRACE_REPORT.txt` batch (repo root; static trace, no tests run): **D49.1** restored pop-outs for symbols without an in-memory session reopen empty and stay stale → route restore through cached bars + aggregator creation + realtime subscribe (existing history/backfill/pacing path where cache is incomplete; reproduce-first test); **D49.2** attachment not exception-safe → transactional attach (disconnect signals, detach view, release only holds actually acquired, unregister, release resources; explicit acquisition-state tracking); **D49.3** chart-host startup failure is silent → clear in-pop-out error state/status message while retaining the diagnostic log (main-window ESC-070 is the model, different site); **D49.4** drawing notifications cause repeated all-view fan-out → synchronize once at the change point (handler stays a notification or updates only the receiving view; pin current behavior in tests first, then de-duplicate without changing update semantics); **D49.5** shared realtime hold count may overstate owners → verify FIRST whether a lasting effect exists (main-chart reload path re-subscribing without release is the suspect), fix (idempotent per-owner acquire/release) only if confirmed, otherwise record the verification and close with no code change. **D49.6 (NEW 2026-10-29)** pop-out creation passes the main chart's timezone offset into the new view (no hardcoded `tz_offset=0.0`) and persists/restores it with the saved pop-out set. Quality bar: each item measurable without a live TWS session where possible; live behavior gated behind owner-named validation (Q65). See D49, Journey 42, `AC-D49.1`–`AC-D49.7`, A121–A126/A133–A134, R96–R98/R102. **D1–D48 are NOT reopened.** No blocking question remains for D49 (Q64–Q66 answered 2026-10-28; D49.6 fully derivable, no question asked); D49 carries `Status: READY_FOR_PLAN`.


> **[NEW 2026-10-29] Batch 26 (D49.6 + D51) — timezone handoff CLARIFIED (no question round); follow-live viewport batch FINALISED 2026-10-29 (Q72–Q76 answered-owner-confirmed).** **D49.6** (addition to D49, owner-ordered 2026-10-29): pop-out creation passes the main chart's timezone offset (no hardcoded `tz_offset=0.0`) and persists/restores it, so a restored pop-out renders identical time labels for the same bars. Fully derivable — no open question; D49 carries `Status: READY_FOR_PLAN`. **D51** (new batch): the main-chart viewport must not be yanked to the newest bar on live updates while the user has scrolled back — follow-vs-away definition, auto-resume, Fit/reset, per-symbol memory and same-vs-new-symbol replacement are decided as Q72–Q76 (answered-owner-confirmed 2026-10-29); `AC-D51.1`–`AC-D51.5` are FINAL and D51 carries `Status: READY_FOR_PLAN`. **D1–D50 are NOT reopened** (the pre-existing D49.6 `history intact` guard is renumbered to D49.7/`AC-D49.7` to free the number — recorded in place, no criterion changed).

> **[NEW 2026-10-29] Batch 27 (D52) — add `30 mins` as a valid chart interval — OWNER-ORDERED; lite lane (defaults A136–A141, one non-blocking confirmation Q77).** The owner ordered `30 mins` alongside the existing intraday set (`1 min`, `5 mins`, `15 mins`), following the D48 weekly/monthly precedent. D52 adds the single `TIMEFRAME_CONFIG` row (`30 mins` → bar size `30 mins` / duration `30 D`, owner decision A136 verified by probe), 30-minute aggregator buckets on ET clock half-hours, intraday planner/backfill treatment (the `AC-D16.8` 30-session floor **applies**, successive-loads reading, mode-aware per `AC-D16.9`), UI picker inclusion between `15 mins` and `1 hour`, RTH/ETH handling identical to the other intraday timeframes, and priming coverage in the D43 `5 secs` group (elapsed span 1800 s fits the `3600 S` ceiling — no new bar size). Acceptance is **standalone-probe-verified duration + suite green**. **D1–D51 are NOT reopened** beyond the recorded timeframe-enumeration extension (`AC-D16.1` now reads nine; `AC-D16.8` Given now reads six intraday timeframes; the D43/`AC-D27.9` per-span table gains the `30 mins` row). Q77 (duration window) answered-owner-confirmed as `30 D`; no blocking question remains; `requirements.md` carries `Status: READY_FOR_PLAN`.

> > Status: **D17/D18 (panel layout / resizing in full screen, reported 2026-10-03) — CLARIFIED 2026-10-03 (B1–B4 answered; see `open_questions.md` Q/B1–B4).** D16 (historical-bar hole, reported 2026-10-02) is **clarified and finalised** (Q37–Q39 answered 2026-10-02: backfill the whole gap so the chart is continuous; genuine closures stay empty; all timeframes and any symbol). **ESC-023 correction (2026-10-02):** the D16 trading-day calendar carries an explicit **New Year's year-end accounting exception** — Dec 31 is a **trading day** when Jan 1 of the next year falls on a Saturday (see D16 / `AC-D16.7`). D1–D15 remain built and green. The Existing Repository section (marker sentence + Current Tech Stack) is preserved and must not be dropped. **2026-10-05:** new defect **D19** — the toolbar pinned the central widget, so the D17/D18 fix was not effective in the real app — is **clarified and finalised** (B5–B6 answered 2026-10-05: the toolbar gets a **horizontal scroll / elide wrapper in place**, staying one ~36px row inside the central widget so its minimum width no longer pins the layout; the watchlist cap **stays at 50% of the chart area**). See `open_questions.md` B5–B6 (answered) and D19 / `AC-D19.1`–`AC-D19.7`. **2026-10-06:** new defect **D20** — the D19 wrapper's horizontal scrollbar clipped the toolbar label descenders — is **clarified and finalised** (B7–B8 answered 2026-10-06: the content row stays **~36px** with the horizontal scrollbar in its **own reserved lane below**, total strip **~50–52px**, superseding `AC-D19.4`'s `<= ~40px`; the scrollbar is **as-needed** in its reserved lane). See `open_questions.md` B7–B8 (answered) and D20 / `AC-D20.1`–`AC-D20.6`.

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

> **2026-10-15 — Batch 18 (D41): remove D36 (footprint) + D37 (depth heatmap / imbalance / auction) + the Active Trader DOM ladder — USER-REQUESTED; scope FINALISED 2026-10-15 (Q48/Q49 answered).**
> The owner requested (verbatim): *"I want to remove footprint, Depth, Imbalance (IMB), Auction (AUC) and all
> associated code from the app. There is no need for them when it does not work properly."* These are the
> **D36** (footprint charts) and **D37** (depth heatmap + auction imbalance) features — both **built/merged**
> and previously APPROVED — surfaced by the four floating controls in `ui/chart_panel.py` (`Footprint` +
> `Classic`/`Tick count`, `Depth`, `IMB —`, `AUC —`). The owner's rationale ("does not work properly") is
> corroborated by open Code Reviewer findings (**ESC-040** footprint never leaves `loading` on error 162 / no
> not-subscribed state; **ESC-035** depth error 2152 blanks the default-ON heatmap; **ESC-039** the DOM ladder
> pairs a SMART contract with `isSmartDepth=False`; plus a pending overlap investigation). **D41 is a removal
> work item, not a fix.** `AC-D36.*` and `AC-D37.*` are **SUPERSEDED BY D41** (retained for history per DOC-4).
> **D1–D35 and D38–D40 are NOT reopened**, and the shared substrate they reuse — D38 (news/dividends) and D39
> (burst/search) — is **explicitly preserved** (S0 generic ticks, `INDEX_PROXY`, `footprint_cache_key`,
> `md_line_guard`, `volume_baseline`).
> **All owner confirmations are ANSWERED (2026-10-15):** **Q48 = YES** — D41 removes the **Active Trader DOM
> ladder** (the whole depth path, not just the heatmap); **Q49 = "delete"** — the persisted D36 footprint data
> (`footprint_cache` table + rows) is **removed**; and **Q50 = YES / YES** — D41 is **widened to the entire
> Active Trader panel**: the **in-app order-entry UI** (MKT/LMT/STP/Bracket ticket) is removed with it (there is
> **no in-app order ticket** afterwards), and the **right dock becomes Portfolio-only**. Portfolio's
> **Close / Close Group / Flatten All** and the **SL/TP dialogs** remain — they place orders through the
> **retained order machinery** (`ibkr/orders.py`, `ibkr/validation.py`, the validate-order gate, bracket
> construction, kill switch). **[REVERSED BY D45 on 2026-10-25 (incl. its later extension): every one of those
> retained surfaces — closes, SL/TP dialog, kill switch, `ibkr/validation.py` — is now removed; the app has zero
> order interaction. This paragraph records D41 as it was decided, not the current end state.]** All of `ui/active_trader_panel.py` (panel shell, ladder/book, order-entry widget,
> its `header_bar`/`header_button`, `set_symbol`/`set_last_price`/`last_price`) is **REMOVED**, and the **D18
> right-dock model** and **D21.13 dock-title-bar / collapse** clauses that assumed the two-section
> Active-Trader+Portfolio region are **superseded by D41** (the right dock is now a single Portfolio section
> with its width cap and header **re-derived**). The kept order path's `ref_price` (previously the panel's
> `last_price`, fed by the DOM feed) now takes a **retained source** (the session's last price / watchlist
> price map) — recorded as a Plan-level detail. Consequences: **ESC-039** is **moot** (no ladder request
> remains); **ESC-035 / Q46 + DG64** (depth error 2152) are **moot — superseded by D41** (no depth feed
> remains; the owner did not pick options (a)/(b)/(c)). See A68–A71 and `open_questions.md` Q48–Q50
> (answered).

> **2026-10-15 (later) — Batch 18b (D42): two REQUIREMENTS-routed Code Reviewer escalations resolved (ESC-042, ESC-038).**
> **D41 is built/reviewed/committed and is NOT reopened.** **ESC-042 (the important one)** resolves a genuine
> **contradiction between `AC-D6.4` (unconditional body >= 4 device px at DPR 2) and `AC-D7.1` / the D7 dense-view
> edge case (inter-bar gap stays positive)** — at high bar density (measured 3.83 device px pitch) the 4-px floor makes
> adjacent bodies overlap and the gap negative, which is the **root cause of the still-open BUILD escalation
> ESC-041** (candle **and** volume overlap on a 5-min chart with Extended Hours ON). The resolution makes the
> **no-overlap guarantee win**: the body width is capped at the inter-bar pitch and the 4-px legibility floor
> becomes **density-aware** (it yields to the pitch when they collide); the hard guarantee is `gap >= 0` and the gap
> is **positive whenever the pitch exceeds the floor**. This **supersedes the unconditional wording of `AC-D6.4`**
> and the **"gap remains positive" wording of `AC-D7.1`** + the D7 dense-view edge case (recorded, not silent).
> **ESC-038** (RTH intraday chart shows only the current session) is a **fetch-window** defect, not `useRTH`;
> the owner's floor is recorded as **`AC-D16.8`** (>= 30 trading sessions before the current session), which
> **every intraday timeframe currently violates** (all `TIMEFRAME_CONFIG` durations are calendar-day windows
> yielding fewer than 30 sessions). A **present-but-empty trading day** — cached bars all outside the current
> mode's session window — MUST be treated as a **missing span**, not as filled: **`AC-D16.9`** (the requirement
> side of the same code path as BUILD escalation **ESC-037**). **Owner answers (2026-10-15):** **Q51** confirmed
> the zero-gap-at-the-limit default (no criteria change); **Q52** **widened the depth floor and the
> present-but-empty rule to Ext-Hours (ETH) charts too** — `AC-D16.8`/`AC-D16.9` now cover **both**
> `ext_hours=False` and `ext_hours=True`, with a **mode-aware** bar cache/key in both directions (this
> **supersedes the RTH-only default**, recorded not silent). See **D42**, `AC-D6.4` (revised), `AC-D7.1`
> (revised), `AC-D16.8` (extended), **`AC-D16.9`** (extended), A72-A73, R63-R64, `design_gaps.md` DG68
> (resolved) + DG72, and `open_questions.md` Q51-Q52 (answered 2026-10-15). `requirements.md` carries
> `Status: READY_FOR_PLAN`.

> **2026-10-16 — Batch 18c (D43): the ESC-036 second clause (a REQUIREMENTS question) is DECIDED — D27.9's "trailing 5-second history" is unsatisfiable for the coarse intraday timeframes and is SUPERSEDED.**
> **D41/D42 are delivered, reviewed and committed and are NOT reopened.** **ESC-036** (recorded `routed_to: BUILD`) has **two clauses**: its **first clause** (the priming request asks IBKR for `bar_size='5 secs'` with `duration='7200 S'` → TWS **error 321**) is being built (**P2-T30**, in flight: clamp the 5-sec priming span into `[60 S, 3600 S]`); its **second clause** is a **requirements question** the owner directed here — `requirements.md`'s **D27.9** mandated priming with **"trailing 5-second history"**, but **5-second bars cannot span a 4-hour (14400 s) or 1-day (86400 s) forming period at all** (IBKR caps `5 secs` at `3600 S`), so D27.9 was **unsatisfiable** for `4 hours`/`1 day`. **Decision (D43, owner-confirmed-by-default — the escalation's stated expectation is "`AC-D27.9` met on every timeframe the user can select, including 4h/1d"):** the priming bar size is chosen **per the elapsed forming-period span** — **`5 secs`** for the timeframes whose span fits IBKR's `3600 S` ceiling (`1 min`, `5 mins`, `15 mins`, `1 hour`) and **`1 min`** for **`4 hours`** and **`1 day`** (valid up to `1 D`) — with `duration` = the elapsed span clamped into the selected bar size's IBKR-accepted range. This **SUPERSEDES D27.9's "trailing 5-second history" wording** (recorded, never silent) and **revises `AC-D27.9`**. **P2-T30's first-clause clamp remains correct and required for the fine timeframes**, but it does **not** deliver the coarse-timeframe bar-size switch — that is an explicit **FOLLOW-UP** (see D43), and P2-T30's `AC1`/`P2-T30-T11` (which assert a `5 secs`/`3600 S` request for 4h/1d) become **stale once the follow-up lands** and must be revised by the Task Manager. See D43, `AC-D27.9` (revised), A74, R65, `design_gaps.md` **DG73**, and `open_questions.md` **Q53** (answered, owner-confirmed-by-default). `requirements.md` carries `Status: READY_FOR_PLAN`.

> **2026-10-16 — Batch 19 (D44): the collapsed Watchlist becomes a thin vertical bar — OWNER-REQUESTED; the `## Non-Goals` are explicitly revised (dated 2026-10-16).**
> A NEW owner request arrives after the D41/D42/Stage-C run completed (all 37 tasks done, review `REVIEW_COMPLETE`,
> tree clean at `0c4d478`); **nothing is blocking**. The owner asked (verbatim intent): *"When the watchlist is
> collapsed by clicking on the Watchlist button, it should become a thin bar on the left side. When the user
> clicks on the thin panel, it should open up into a full panel like before. Keep the colour scheme consistent
> with the app and make it look like a panel."* Repo-validated, the collapse mechanism **already exists**
> (D21.11 — the `WatchlistPanel.header_bar` + `header_button` toggle hides the table via `_on_header_toggled`;
> `set_collapsed`/`toggle_collapsed`/`is_collapsed` are the public API), so **D44 changes the collapsed
> *appearance*, not the collapse mechanism**. The owner explicitly clarified that the mockup's **white rounded
> pill is mockup-tool styling only, NOT a colour choice** — the bar must use the **app palette** (`#141822`
> background, `#cbd5e1` text, `#232938` border). D44 requires a thin vertical bar (~**30px**) with rotated
> `WATCHLIST` text, click-the-bar to expand to the **previous** width, click the header button to collapse (as
> today), and layout rules (`WATCHLIST_MIN_WIDTH` / `plan_dock_widths` / `_apply_dock_widths`) that **honour a
> collapsed width** rather than snapping back to 150px. This **revises the `## Non-Goals`** (recorded above,
> dated) and **supersedes/revises** `AC-D21.11.2`/`AC-D21.11.3` (collapsed appearance) and the 150px-minimum
> clause of `AC-D13.1`/`AC-D17.2` (the minimum now applies to the **expanded** state only). See D44, Journey 37,
> `AC-D44.1`–`AC-D44.8`, A75–A78, R66–R67, `design_gaps.md` **DG74**, and `open_questions.md` **Q54** (owner
> confirmation requested; non-blocking defaults recorded). **D1–D43 are NOT reopened.** `requirements.md`
> carries `Status: READY_FOR_PLAN`.

> **2026-10-16 (later) — ESC-057 (D44 `AC-D44.2` measurable restated — WORDING-ONLY, nice-to-have; no criteria substance changed).**
> The Code Reviewer's **ESC-057** found `AC-D44.2`'s measurable ("assert `watchlist_dock.width() == clamp(W)`") demanded
> an exact echo on the **rendered** dock width, which the shipped guard
> (`tests/test_dock_widths_collapsed_d44.py::test_P3_T05_T21_expand_restores_the_tracked_width`) does not assert (it
> checks tolerant bounds) — while the reviewer's **independent offscreen probe reproduced an EXACT restore**
> (150→150, 300→300, cap→cap in both clamp branches). The AC and the guard therefore disagreed about **what is asserted**.
> **Resolution (the reviewer's recommended direction, adopted):** `AC-D44.2`'s measurable now names the **tracked**
> `win._watchlist_width == clamp(W)` (**exactly satisfiable by construction**) **plus** a **tolerant** check on the
> **rendered** dock width (floor / cap / `> collapsed width`). The **orchestrator's earlier residual note** in
> `docs/build/logs/P3-T05.md` (a non-exact 300→314 restore) is **NOT reproducible and is NOT treated as evidence** (the
> orchestrator has owned it as its own error); **no requirement depends on a rendered-width echo**. **No code change is
> required** — the shipped guard already satisfies the restated measurable. The D44 register's "Expand on click" bullet,
> Journey 37's postcondition, R67's mitigation and `design_gaps.md` **DG74** carry the same clarification. **D1–D43 are
> NOT reopened**; `requirements.md` carries `Status: READY_FOR_PLAN` (unchanged).

> **2026-10-25 — Batch 20 (D45): remove the News Digest dock (and the `View` menubar), the Trade Context Menu, the Kill switch and the SL-TP dialog — the app has ZERO order interaction afterwards. OWNER-REQUESTED; full removal; no blocking question (lite lane — defaults A79–A90).**
> A NEW owner request arrives after D44 was delivered (`bb903a1`), reviewed (29/29 escalations addressed), with a
> clean tree and a green suite. The owner asked, verbatim, *"I want both removed."* — referring to the two components
> they had asked about and then confirmed for removal: (1) the **News Digest Dock** (`ui/news_digest_dock.py`,
> D38a.2); (2) the **Trade Context Menu** (`ui/trade_context_menu.py`). Both are **full removals**. **Owner
> confirmations (all explicit, 2026-10-25):** `ibkr/news.py` is **deleted** (its only consumer is the digest + its
> tests); the **View menubar** may go (it exists **solely** for `View → News Digest`, Ctrl+Shift+N; the app had **no
> menubar** before D38 and returns to **none**); generic tick **`"292"` is removed** while the **dividend tick
> `"456"` MUST stay** (same `s0_register` mechanism, but it feeds the chart's **dividend event markers**, which are
> staying); **Portfolio becomes view-only** (closes happen **in TWS directly**; **no replacement UI**); and
> `USAGE.txt` / `usage.md` / `docs/codebase-map.md` are cleaned **in the same batch**. **Consequence stated
> plainly:** after D45 the app **places no orders at all** — no notional cap, pacing or disconnected order guard is
> in play — and the suite's meaning shrinks (three order-safety test files are deleted; **five** in total after
> the later extension adds `test_kill_switch.py` and `test_sltp_honesty.py`) even as it stays green.
> `AC-D38.2`/`AC-D38.3` are **SUPERSEDED BY D45**, `AC-D38.6` and the portfolio-close clauses of
> `AC-D41.1`/`AC-D41.4` are **REVISED**, and D26's order-entry clauses are moot.
> **EXTENSION (2026-10-25, later — the owner widened the same batch).** Verbatim: *"remove: Kill switch — it only
> cancels orders, never places one / SL-TP dialog — local-only targets, never transmitted"*, in the context of
> *"i dont need to place any order from the app"*. The intent is that the app has **no order interaction of any
> kind** — not placing, **not cancelling, not closing** — so D45's end state moves from "the app places no orders"
> to **"zero order interaction"**: the **Kill switch** (**Group C**, the cancel path) and the **SL-TP dialog**
> (**Group B**) are **also removed in full**, and the Portfolio table's **Stop / Target columns** go with the dialog
> (A87). **A82/A83 are REVERSED** (recorded as reversals, never silently rewritten), the "Scope — KEEP" list now
> holds **no order-related surface at all**, and the **owner-accepted consequences are rewritten** to that end
> state. `AC-D45.6` is **INVERTED** (it asserted the switch and dialog *still work*; it now asserts they are
> **gone**), `AC-D45.10` is added, and **D26.3/D26.8** become **moot/superseded**.
> **Consequence stated plainly:** after D45 the app **places, cancels and closes nothing** — no notional cap,
> pacing, disconnected order guard or **panic cancel** is in play — the whole ordering machinery (`ibkr/orders.py`,
> `ibkr/validation.py`, bracket construction, the registry's only producer, every `placeOrder`/`cancelOrder`/
> `reqGlobalCancel` call site) is **orphaned together**, and the suite's meaning shrinks (**five** order/protection
> test files are deleted) even as it stays green.
> **D1–D44 are NOT reopened.** See D45, Journey 38, `AC-D45.1`–`AC-D45.10`, A79–A90, R68–R75, `design_gaps.md`
> **DG75** / **DG77**. `requirements.md` carries `Status: READY_FOR_PLAN`.

> **2026-10-25 (later) — Batch 21 (D46): delete `ibkr/orders.py` and the inert order-observation chain. OWNER-REQUESTED; lite lane (defaults A91–A98; owner confirmations Q56–Q59, non-blocking).**
> Asked after D45 delivered zero order interaction, verbatim: *"I dont want anything to do with orders so why is there orders.py ?"* —
> and, on being told the module has no production caller and no populated registry, the owner **confirmed opening this batch**.
> Repo-validated 2026-10-25: `ibkr/orders.py`'s four builders have **zero** production callers and `register()` is never called, so
> the registry is permanently empty and every read returns `None`; the inbound `orderStatus`/`openOrder`/`execDetails` chain
> (client overrides → three bridge signals → three `MainWindow` slots → `_update_order_status`) therefore terminates in a
> **guaranteed no-op**, and `_on_order_error` — which phrased 201/103 "Rejected" and 202 "Cancelled" — is **unreachable**.
> D46 deletes the module, the chain and the unreachable handler, and **keeps TWS error visibility** on the existing generic
> status-bar line (`AC-D46.3`). **D1–D45 are NOT reopened**; **A80 and A90 are REVERSED in place** (A91/A92), **ESC-061 becomes
> MOOT**, and `design_gaps.md` **DG76 is resolved by the deletion**. See D46, Journey 39, `AC-D46.1`–`AC-D46.8`, A91–A98,
> R76–R81, `design_gaps.md` DG78–DG81, and `open_questions.md` Q56–Q59 (defaults recorded; no blocking item).
> `requirements.md` carries `Status: READY_FOR_PLAN`.

> **2026-10-25 (later still) — Batch 21 (D46) scope EXPANDED: the owner answered Q56–Q59 verbatim and reversed the
> retention decisions. The register, the inventory, the acceptance criteria and the A/R/DG numbers below supersede the
> earlier D46 wording in every place the two differ.**
> The owner's answers, verbatim: **Q56** *"why is there any order related code left"*; **Q57** *"there should not be any
> order related coding. i want all of it deleted"*; **Q58** *"yes remove"*; **Q59** *"remove everything"*. **Q57/Q59 reject
> the premise** of the earlier recorded defaults rather than choosing among the options offered, so the scope is now the
> **whole order surface**, not `ibkr/orders.py` plus its observers. **What the expansion adds** (each verified in-repo
> before being written down): (1) three **zero-consumer order utilities** — `ibkr/pacing.py::OrderRateLimiter` /
> `order_limiter` (no production reader), `config/settings.py::MAX_ORDER_NOTIONAL` (no reader; its `validate_order()` gate
> died in D45) and the **order-fill sound** (`render_fill_blip`, `play_fill`, `order_fill.wav` — `play_fill` has no
> caller); (2) **`IdManager.reserve`** — the module itself **stays**, because `get_id()` allocates **market-data and
> realtime reqIds** (`ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`), and only `reserve()` is order-only
> (tests only); (3) the **stop/target storage** — `positions`/`trade_groups` `stop_loss`/`take_profit` **columns and the
> `Position`/`TradeGroup`/`ibkr.account.Position` fields are DROPPED** (A99), **reversing A87**, the first **destructive**
> schema step in the project. **The honest justification is ESC-060, not preference:** the values were **already cleared by
> the first live update** of any row and no setter has existed since D45, so the drop destroys **nothing that survived** —
> only rows must be preserved. **Reversals recorded in place, original wording kept:** A87 (→ A99), A97 (→ A100/A101),
> A92/A93/A96 **confirmed** by the owner. **Q56 also has a recorded answer, not just a deletion:** order code survived
> because D45's A80/A90 retained it on the premise that the observers needed the registry — a registry **nothing ever
> populated**, so the premise was false; the lesson is that *"retained and inert"* was never checked for **reachability**,
> and `D46.9`'s inventory is the mechanism that prevents a repeat. **Second documentation correction:** the statements
> rewritten this morning under ESC-060 ("the columns are kept, but a live update clears them") are **superseded by A99** —
> the trail must read **kept → cleared → dropped** (`D46.13`, `design_gaps.md` **DG84**). **No blocking question
> remains.** D1–D45 are **not** reopened. See D46, Journey 39, `AC-D46.1`–`AC-D46.13`, A91–A104, R76–R85,
> `design_gaps.md` DG78–DG87. `requirements.md` carries `Status: READY_FOR_PLAN`.

> **2026-10-26 — Batch 22 (D47): the chart stack migrates to Lightweight Charts behind a `ChartView` interface — OWNER-DIRECTED REVERSAL of the 2026-10-16 decline; no soak, one live-session sign-off; Phase 0 spike allowed as a single exception.**
> The owner **reversed** the 2026-10-16 Locked Decision declining the LWC migration (recorded in `docs/memory.md` 2026-10-16; the reversal is recorded in `### D47` below with the original rationale kept beside it, A80/A90 pattern — `docs/memory.md` itself is Orchestrator-appended and is flagged for the matching append). The chart stack migrates **via strangler behind a `ChartView` protocol** (`ui/chart_view.py`), with **pyqtgraph retained until parity is accepted** — the sanctioned route the decline itself named. **Three owner approvals, verbatim (decided 2026-10-26):** (1) *"Reverse the 2026-10-16 decision declining the LWC migration"* — YES; (2) *"No soak, but one live session sign-off before any delete"* — YES: **no calendar soak**; cutover when the owner accepts **and** the parity matrix is all Done/accepted **and** Phase 0 perf holds; **pyqtgraph deletion is a separate wave on explicit owner approval only**, gated on **one live trading session with no engine defect**; (3) *"Phase 0 spike as single exception to no-prototype"* — YES: `spikes/lwc/` throwaway only, proving the 9 API behaviours, results in `docs/lwc_spike_results.md` with a go/no-go gate. The attached migration plan (updated, no soak) is the primary input: strangler seam + `DrawingController`/`AlarmController` signal preservation, `create_chart_view(tz_offset, editable)` on `NDT_CHART_ENGINE` (pyqtgraph default, lwc) or `QSettings`; shared Qt-free `ChartModel`; `QWebEngineView` + vendored lightweight-charts v5.2.x via `ndt://` scheme handler; `QWebChannel` `LwBridge` batched transport; panes (v5), logical-index time axis, custom tz formatters; in-HTML controls with Python shims; Python `RouterMode` + JS mirror; primitives library; Qt dialogs stay; **Phases 0–11** (effort S/M/L/XL as stated); **19-row parity matrix** (`docs/lwc_parity_matrix.md`, kept updated); pyramid test strategy; **66 chart-adjacent test files** classified keep/retarget/engine-specific; 10 risks; explicit out-of-scope list. **D1–D46 are NOT reopened** beyond the recorded supersessions/reversals (density-cap AC retirement is **proposed, pending Q60**; the 2026-10-16 decline is **reversed**). **Section-8 owner questions Q1–Q4** are recorded as **Q60–Q63** (`open_questions.md`): Q60 answered-by-default (the plan already justifies it); Q61–Q63 open with recommended defaults. `requirements.md` carries `Status: READY_FOR_PLAN`.

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

**New work item — 2026-10-16 (Batch 19, feature D44) — OWNER-REQUESTED; scope recorded 2026-10-16 (no blocking question).**
The owner requested (verbatim): *"When the watchlist is collapsed by clicking on the Watchlist button, it should
become a thin bar on the left side. When the user clicks on the thin panel, it should open up into a full panel
like before. Keep the colour scheme consistent with the app and make it look like a panel."* Repo-validated, the
**collapse already exists** (D21.11 — `ui/watchlist_panel.py::WatchlistPanel` has a 28px `header_bar` holding
`header_button = DiagonalStrikeButton("Watchlist")`; `_on_header_toggled()` does `self.body.setVisible(visible)`;
`set_collapsed()`/`toggle_collapsed()`/`is_collapsed()` are the public API), and today the collapsed state keeps
the **horizontal header strip** while the table hides — the dock retains its ~220px width. **D44 is therefore a
change to the collapsed *appearance***, not a new collapse mechanism: the collapsed watchlist becomes a **thin
vertical bar** (~30px, rotated `WATCHLIST` text, app palette) that expands back to the **previous** width on
click. D44 is an **owner-authorized net-new UI feature**, so the `## Non-Goals` bullets that excluded net-new
feature work and restyling are **explicitly revised (dated 2026-10-16)** rather than left standing. D1–D43 are
**not reopened**; D44 **revises** the collapsed-state clauses of D21.11 and the 150px-minimum clause of D13/D17
(the minimum applies to the **expanded** state). See D44, Journey 37, `AC-D44.1`–`AC-D44.8`, A75–A78, R66–R67,
`design_gaps.md` DG74, and `open_questions.md` Q54 (owner confirmation requested; non-blocking).

## Goals
- Collect and triage the user's reported functional issues and UI bugs.
- Fix each reported defect such that its per-task **test condition** passes.
- Keep the existing behavior and test suite intact — no regressions.
- Keep the live-order path safe: the per-run "gated in TWS" planning assumption is **retired** (owner decision
  2026-10-14, Q42), so D26 may be planned against the live-order path, but the safety behaviour stands —
  `IBKR_PORT != 7496` fails fast, every order requires explicit user action, confirm dialogs remain, and no
  automated test transmits an order. **D45 (2026-10-25) revises the operative content of this goal:**
  the app now **places no orders at all** — there is no in-app order path — so "every order requires explicit
  user action" means **no order can be placed from the app**. **D45 extension (2026-10-25, later) revises it
  again:** the app has **zero order interaction** — it places, cancels and closes nothing — so the **kill switch**
  (the only in-app cancel path) and the **local-only SL/TP dialog** are **removed too**. What remains is the
  fail-fast port check (`config/settings.py::check_live_port`), the connection badge, the inbound
  order-status/execution callbacks (**observers only** — the registry they read is never populated) and the
  no-test-transmits rule. **D46 (2026-10-25) removes even the observers and the module they read:** the app keeps
  the fail-fast port check, the connection badge, the no-test-transmits rule and the **generic TWS error line**
  (`Error [<code>]: <message>` — the surface for 201/103/202, `AC-D46.3`); it holds no order code at all.

## Non-Goals
- **Net-new feature development — OWNER-DIRECTED REVISION 2026-10-16.** As originally written this
  Non-Goal excluded net-new feature work ("bug-fix/UI repair only"). The owner has since directed a
  net-new UI feature — **D44** (the collapsed Watchlist becomes a thin vertical bar that expands to the
  full panel) — so this Non-Goal is **revised, not silently dropped**: net-new feature work remains out of
  scope **except** for the explicitly owner-authorized **D44** (Batch 19, 2026-10-16). Every other
  unrequested feature stays out of scope and, if noticed, goes to `feature_suggestions.md`.
- **Visual redesign / restyling beyond correcting the reported UI defects — OWNER-DIRECTED REVISION
  2026-10-16.** As originally written this Non-Goal excluded restyling. The owner's **D44** request is
  itself a deliberate change to the collapsed watchlist's appearance (a thin vertical panel bar in the
  app's own palette), so this Non-Goal is **revised** to permit **only** the D44 collapsed-bar
  presentation; no other restyling is authorized. The mockup's white rounded pill is explicitly **NOT**
  the target colour — the bar uses the app palette (see D44).
- A standalone GUI test-suite spec (the documents describing one were deleted 2026-10-16 — the suite was never implemented), and
  "Phase 12" combo/BAG multi-leg order placement — both explicitly out of scope
  for this run (from Q2).
- Introducing a paper/simulated trading mode, or changing the live-only port 7496
  model.
- **Changing the tech stack — OWNER-DIRECTED REVISION 2026-10-26 (D47).** As originally written this
  Non-Goal excluded stack changes. The owner has since directed the **D47** chart-stack migration, so this
  Non-Goal is **revised, not silently dropped**: the **chart renderer only** may change (pyqtgraph →
  Lightweight Charts v5.2.x vendored, hosted in `QWebEngineView`, Python/IBKR backend unchanged),
  **exactly** as D47 specifies — pyqtgraph is **retained until parity is accepted**, and its deletion is a
  **separate wave on explicit owner approval only**. No other stack change is authorized. The
  **Phase 0 spike** (`spikes/lwc/`, throwaway, results in `docs/lwc_spike_results.md`) is a **single
  owner-authorized exception** to the no-prototype convention.

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

- **D41 — remove the D36 footprint + D37 depth heatmap / imbalance / auction + the ENTIRE Active Trader panel (DOM ladder + order-entry UI) (NEW, 2026-10-15, USER-REQUESTED; scope FINALISED 2026-10-15 — Q48/Q49/Q50 answered):** the four chart-panel cluster controls (`Footprint` + `Classic`/`Tick count`, `Depth`, `IMB —`, `AUC —`) and **all of `ui/active_trader_panel.py`** (`ActiveTraderPanel` shell, the DOM ladder/book, and the in-app **order-entry widget** MKT/LMT/STP/Bracket) are removed, along with the **`DOM` toolbar button**; the persisted D36 footprint data (`footprint_cache` table + rows) is **deleted**; the **right dock becomes Portfolio-only**. The **retained order machinery** (`ibkr/orders.py`, `ibkr/validation.py`, the validate-order gate, bracket construction, kill switch) was to stay and guard Portfolio's **Close / Close Group / Flatten All** and the **SL/TP dialogs**; the kept order path's `ref_price` takes a **retained source** — **REVERSED BY D45 (2026-10-25, incl. its later extension): every one of those surfaces is now removed** (closes, kill switch, SL/TP dialog; `ibkr/validation.py` deleted), so the app has **zero order interaction**. The shared substrate reused by the **kept** D38 (news/dividends) and D39 (burst/search) is preserved. See D41, Journey 36, `AC-D41.1`–`AC-D41.7`, A68–A71, R61–R62, and `open_questions.md` Q48–Q50 (answered).

- **D42 — REQUIREMENTS resolutions for the two REQUIREMENTS-routed Code Reviewer escalations (ESC-042 candle/volume overlap precedence; ESC-038 intraday history depth + present-but-empty trading day) (NEW, 2026-10-15; Q51/Q52 answered 2026-10-15):** a **requirements-decision** batch (no code of its own). **ESC-042:** `AC-D6.4`'s unconditional 4-device-pixel body floor **contradicts** `AC-D7.1`'s "gap remains positive" at high density; the resolution caps the rendered body width at the **inter-bar device-pixel pitch** and makes the 4-px floor **density-aware** (it yields to the pitch when they collide), so **`gap >= 0` always** (no overlap) and **`gap > 0` whenever the pitch exceeds the floor** — this **supersedes the unconditional `AC-D6.4` wording** and the **`AC-D7.1` "positive gap" wording** + the D7 dense-view edge case, and is what unblocks BUILD **ESC-041**. **ESC-038:** the one-session symptom is a **fetch-window** defect (not `useRTH`); the owner's floor **`AC-D16.8`** (>= 30 trading sessions before the current session, each intraday timeframe) is **extended/clarified** (sessions are counted by bars **inside the current mode's session window**, not calendar-day presence; all current `TIMEFRAME_CONFIG` windows fall short and must extend history backwards), and a **present-but-empty trading day** (cached bars all outside the current mode's session window) is required to be treated as a **missing span** (**`AC-D16.9`**, the requirements side of BUILD **ESC-037**). **Owner answers (2026-10-15):** **Q51** confirmed the zero-gap default (no criteria change); **Q52** **widened `AC-D16.8`/`AC-D16.9` to Ext-Hours (ETH) charts too** (`ext_hours=True` shares the one floor with RTH and must not cross-contaminate — the bar cache/key is mode-aware in both directions), **superseding the RTH-only default** (recorded, not silent). See D42, `AC-D6.4`/`AC-D7.1` (revised), `AC-D16.8` (extended), `AC-D16.9` (extended), A72–A73, R63–R64, and `open_questions.md` Q51–Q52 (answered 2026-10-15).

- **D44 — the collapsed Watchlist becomes a thin vertical bar (NEW FEATURE, 2026-10-16, OWNER-REQUESTED; no
  blocking question — non-blocking defaults recorded A75–A77):** the D21.11 collapse already exists, so D44
  changes the **collapsed appearance**: while collapsed the watchlist dock shrinks to a **thin vertical bar**
  (~30px) on the left, rendering the **rotated** text `WATCHLIST` in the **app palette** (`#141822` /
  `#cbd5e1` / `#232938`), and **clicking the bar expands** the panel to its **previous** width; clicking the
  retained "Watchlist" header button collapses it (as today). Qt cannot rotate a `QPushButton`'s text, so the
  bar needs a small custom widget with a `paintEvent` drawing rotated text (Plan-level mechanism). The layout
  rules (`ui/dock_layout.py::plan_dock_widths` — currently `left = max(WATCHLIST_MIN_WIDTH, min(int(requested_left),
  left_max))` — plus `MainWindow._apply_dock_widths`, wired to `resizeEvent` and the dock-drag hook) must learn a
  **collapsed width** so a ~30px bar is not snapped back to `WATCHLIST_MIN_WIDTH` (150) on the next resize/drag.
  Expected to live in `ui/watchlist_panel.py` (the collapsed bar widget + collapse/expand state) and
  `ui/dock_layout.py` + `ui/main_window.py` (collapsed-aware width clamp). See D44, Journey 37,
  `AC-D44.1`–`AC-D44.8`, A75–A78, R66–R67, `design_gaps.md` DG74.

- **D45 — remove the News Digest dock (+ the `View` menubar), the Trade Context Menu, the Kill switch and the
  SL-TP dialog; the app has zero order interaction
  (NEW, 2026-10-25, OWNER-REQUESTED; full removal, no blocking question — lite lane, defaults A79–A90):** the
  **News Digest** half of D38 is removed end-to-end (`ui/news_digest_dock.py`, `ibkr/news.py`/`NewsManager`, the
  `View → News Digest` menubar and its `Ctrl+Shift+N` shortcut, `MainWindow._on_news_digest_visibility`, and the
  news **`"292"`** S0 fan-out in `ui/ticker_session.py`); the **Trade Context Menu** order path is removed
  end-to-end (`ui/trade_context_menu.py`, `ibkr/validation.py`, the Portfolio `position_close_requested` /
  `group_close_requested` / `flatten_all_requested` signals and their three `MainWindow` handlers, and
  `_close_position_by_id`); and — **owner extension, 2026-10-25 (later)** — the **Kill switch**
  (`kill_btn`/`_on_kill_switch_clicked`/`_kill_switch`, `reqGlobalCancel` + per-ID `cancelOrder`) and the
  **SL/TP dialog** (`ui/stop_loss_target_dialog.py`, its two signals, both `MainWindow` handlers and the
  Portfolio **Stop / Target** columns) are removed as well, because the owner wants **no order interaction of
  any kind** (not placing, **not cancelling, not closing**). **Retained deliberately:** the **dividend** S0 line
  `"456"`, tick 59, `_dividend_info`/`dividend_updated`, the **chart event markers**, the D39 substrate, the
  Portfolio **observation** path (account summary + positions, **view-only**), and the `positions` /
  `trade_groups` `stop_loss` / `take_profit` **DB columns + model fields** (no longer settable or displayed —
  A87). **Portfolio becomes view-only** — closes happen in TWS, no replacement UI.
  **[D46 NOTE 2026-10-25 — SUPERSEDED: A87 is reversed. The `stop_loss`/`take_profit` storage is now DROPPED —
  columns and model fields both go (A99 / D46.12). The trail is kept → cleared → dropped.]**
  **Accepted consequence:** the app **places, cancels and closes nothing**, every piece of ordering machinery is
  orphaned together, and **five** test files (three order-safety + `test_kill_switch.py` + `test_sltp_honesty.py`)
  are deleted, so a green suite proves less about order safety and protection than before (recorded in D45, not
  hidden). See D45, Journey 38, `AC-D45.1`–`AC-D45.10`, A79–A90, R68–R75, and `design_gaps.md` DG75 / DG77.
- **D46 — delete **every** order-related coding path (NEW, 2026-10-25, OWNER-REQUESTED; lite lane, then **scope EXPANDED
  the same day by Q56–Q59**):** `ibkr/orders.py` (141 L — `UserOrder`, the `Orders` builders/registry and the `orders`
  singleton) is **deleted**, together with the inbound observation chain that is its only reader (`IBApiClient`'s
  `orderStatus`/`openOrder`/`execDetails` overrides → `ibkr/bridge.py` signals → `MainWindow._on_open_order` /
  `_on_order_status` / `_on_exec_details` → `_update_order_status`) and the **unreachable** `_on_order_error`. **The
  expansion adds:** the three **zero-consumer order utilities** (`OrderRateLimiter`/`order_limiter`,
  `MAX_ORDER_NOTIONAL`, the order-fill sound), **`IdManager.reserve`** (the module stays — `get_id` allocates market-data
  reqIds), and the **stop/target storage** — the `positions`/`trade_groups` `stop_loss`/`take_profit` **columns and model
  fields are dropped** (A99, **reverses A87**; the first destructive schema step, justified by ESC-060: the values were
  already cleared by the first live update, so the drop destroys nothing that survived). `tests/test_order_builders.py` and
  `tests/test_stop_loss_target.py` are deleted whole; `tests/test_order_rejections.py` is **kept in reduced form** (the
  surfacing cases repointed at the generic error path plus an added per-code case, and the `classify_error` cases). The
  vestigial second `UserOrder` in `data/models.py` goes (A96). **TWS order errors still surface** — 201/103/202 reach the
  status bar exactly as today (`AC-D46.3`). A **symbol-by-symbol inventory** with a disposition for every order-named member
  — including the general code that must **not** be cut (`classify_error`, `error_msg`, `nextValidId`, `IdManager`, the ICT
  "order blocks") — makes "all of it" auditable (`D46.9`/`AC-D46.9`). See D46, Journey 39, `AC-D46.1`–`AC-D46.13`,
  A91–A104, R76–R85, DG78–DG87.


- **D47 — migrate the chart stack to Lightweight Charts behind a `ChartView` seam (NEW, 2026-10-26, OWNER-DIRECTED REVERSAL of the 2026-10-16 decline).** Strangler migration: `ui/chart_view.py` protocol, `create_chart_view(tz_offset, editable)` on `NDT_CHART_ENGINE` (pyqtgraph default, lwc) or `QSettings`; shared Qt-free `services/chart_model.py` (ChartPanel delegates, no behaviour change); `QWebEngineView` host + vendored lightweight-charts v5.2.x via `ndt://` scheme handler + interceptor; `QWebChannel` `LwBridge` batched `{v:1,ops:[]}` transport with queue-until-ready, ~33ms live coalesce and replay after `renderProcessTerminated`; panes (v5), logical-index time axis with whitespace for within-session holes (`gap_is_non_trading` stays source of truth), custom tz formatters, per-mode series; in-HTML controls with Python shims; Python `RouterMode` + JS mirror; drawings via a primitives library (ts-to-fractional-index); Qt dialogs stay. **Phases 0–11** (0 spike + decision record; 1 seam+model; 2 runtime+bridge; 3 core chart XL; 4 studies; 5 interaction XL; 6 alarms; 7 drawings XL largest; 8 overlays/markers; 9 pop-outs; 10 packaging/CI/cutover candidate; 11 removal S on owner approval). **Parity matrix** (19 rows, `docs/lwc_parity_matrix.md`, kept updated; rule 10: unmeetable ACs → escalations + parity row). **Cutover with no soak:** owner accept + parity all Done/accepted + Phase 0 perf holds; **pyqtgraph deletion is a separate wave on explicit owner approval only**, gated on one live trading session with no engine defect. **Out of scope:** ibkr, db schemas, drawing/alarm persistence, watchlist, dock, order code, paid library, aggregation/backfill (unchanged). The 2026-10-16 decline's sanctioned route ("a second chart mode behind the existing interface, keeping pyqtgraph until parity") is what D47 executes. See D47, Journey 40, `AC-D47.1`–`AC-D47.9`, A105–A112, R86–R92, `design_gaps.md` DG88–DG96, and `open_questions.md` Q60–Q63.

- **D48 — add `1 week` (2Y) and `1 month` (10Y) timeframes (NEW, 2026-10-28, OWNER-REQUESTED, P8 lite).** Two new picker timeframes backed by IBKR `1 week` / `1 month` bar sizes with `2 Y` / `10 Y` durations; aggregator gains Monday-anchored weekly buckets + calendar-month buckets; the `AC-D16.8`/`AC-D16.9` intraday floor stays intraday-only; the RTH/ETH toggle is a no-op (as for `1 day`); session bands (D1) and collapse (D21.4) stay no-ops; acceptance is a standalone IBKR duration probe + green suite. See D48, Journey 41, `AC-D48.1`–`AC-D48.7`, A113–A120, R93–R95, `design_gaps.md` DG97–DG98. **D1–D47 are NOT reopened.**
- **D49 — pop-out robustness (NEW, 2026-10-28, OWNER-ORDERED; 5 findings + D49.6 timezone handoff (NEW 2026-10-29), nothing dropped).** Restored pop-outs route through the data path (cached bars + aggregator + realtime subscribe); attach is transactional with explicit acquisition-state tracking; a failed chart-host shows an in-pop-out error state (ESC-070 model) with the diagnostic log retained; drawing sync fans out once at the change point (behavior pinned in tests first); the realtime-hold over-count is verified before any fix (idempotent per-owner acquire/release only if a lasting effect is confirmed, else verified close with no code change). Acceptance is offscreen-first; any live check is owner-named (Q65). See D49, Journey 42, `AC-D49.1`–`AC-D49.7`, A121–A126/A133–A134, R96–R98/R102, `open_questions.md` Q64–Q66 (answered 2026-10-28). **D1–D48 are NOT reopened.**

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
- **D47 chart-migration stack (NEW 2026-10-26, owner-directed; pyqtgraph retained until parity accepted):**
  `QWebEngineView` host + **vendored lightweight-charts v5.2.x** (no CDN/npm at runtime; attribution kept),
  `QWebChannel` bridge, shared Qt-free `services/chart_model.py`.
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
  **D45 revision (2026-10-25, incl. its later extension):** the order-facing clauses of this constraint are
  **vacuous, not deleted** — the app offers **no order interaction at all** (no place, cancel or close), so
  "every order requires explicit user action" and "confirm dialogs remain" have no surface left to govern. The
  **still-operative** parts are the fail-fast port check, the no-test-transmits rule and the regression-test
  policy. **D46 (2026-10-25)** removes the last order-named code (`ibkr/orders.py` + the order-observation chain)
  and **keeps error visibility**: TWS order errors **201/103/202** still reach the status bar via the generic
  `Error [<code>]: <TWS message>` line — the richer per-order wording lived in a handler that was already
  unreachable (`AC-D46.3`).
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
| DOM / Ladder | Level II market-depth ladder with click-to-trade rows. **REMOVED by D41 (2026-10-15)** — retained for history. |
| Live-order path | Code that builds/transmits orders via `ibkr/orders.py` + `IBApiClient`. The per-run "gated
  in TWS" planning assumption is **retired** (owner decision 2026-10-14, Q42); D26 may be planned/decomposed
  against this path. Safety behaviour is unchanged: `IBKR_PORT != 7496` fails fast
  (`config/settings.py::check_live_port`), every order needs explicit user action, confirm dialogs remain, and
  no automated test transmits an order. **After D41 (2026-10-15)** the in-app order-entry ticket is removed. **After D45 (2026-10-25, incl. its later extension)** the app has **zero order interaction** — it **places, cancels and closes nothing**: the Portfolio Close / Close Group / Flatten All paths, `ui/trade_context_menu.py`, `ibkr/validation.py`, the **kill switch** and the **SL/TP dialog** are all removed. What survives is **observation only** (fail-fast port check, connection badge, account/position render path) — see the two rows below. **After D46 (2026-10-25)** even the observation half of ordering is gone: `ibkr/orders.py`, the three inbound order callbacks, `_update_order_status` and the bridge's three order signals are deleted; TWS order errors still surface on the status bar as `Error [<code>]: <TWS's own message>` (`AC-D46.3`, A93). |
| Kill switch | The red `#KillSwitchButton` toolbar control (D26.8) that issued `reqGlobalCancel` + a per-ID `cancelOrder` for every tracked order and reported pre/post counts. **REMOVED by D45 (2026-10-25, later extension)** — the app has **no cancel path**; TWS-placed orders are cancelled **in TWS**. Retained for history. |
| SL/TP dialog | `ui/stop_loss_target_dialog.py` (`StopLossTargetDialog`, D26.3) — a **local-only** dialog that saved stop/target prices onto the `positions` / `trade_groups` rows and **never transmitted**. **REMOVED by D45 (2026-10-25, later extension)** together with its **Stop / Target** table columns; the DB columns and model fields are **retained but unsettable** (A87). **[SUPERSEDED BY D46/A99 — both are dropped by migration]** Retained for history. |
| Order observation chain | The inbound order plumbing D26.9 added and D45 kept inert: `IBApiClient`'s `orderStatus`/`openOrder`/`execDetails` `EWrapper` overrides → `Bridge.order_status`/`open_order`/`exec_details` → `MainWindow._on_open_order`/`_on_order_status`/`_on_exec_details` → `_update_order_status` → the `ibkr/orders.py` registry. **REMOVED by D46 (2026-10-25)** together with the module: it had no behavioural effect because nothing ever populated the registry. TWS error surfacing is unaffected (`AC-D46.3`). |
| News Digest Dock | The D38 dock (`ui/news_digest_dock.py`) that listed headlines for held positions, opened from `View → News Digest` (Ctrl+Shift+N). **REMOVED by D45 (2026-10-25)** with `ibkr/news.py` and the `View` menubar; the **event markers** it sat beside are retained. |
| Trade Context Menu | The Portfolio right-click order menu (`ui/trade_context_menu.py`): Close Position / Close Group / Close All Positions. **REMOVED by D45 (2026-10-25)**; the Portfolio panel is **view-only** and closes happen in TWS. |
| Genuine closure | A market-closed interval that is legitimately non-trading (weekend, actual US-equity holiday, or overnight). Stays **empty** per D16 (`AC-D16.3`). **Dec 31 of a year whose next Jan 1 is a Saturday is NOT a genuine closure** — it is a trading day (`AC-D16.7`, ESC-023). |
| Chart area | The central region of `MainWindow` holding the chart, excluding the docked panels (Watchlist on the left; the **Portfolio-only** right dock, after D41). Panel caps in D17/D18 are percentages of **this** region (B1/B2), not of the whole window. |
| Chart-minimum rule | The hard floor (~400px) the chart area must keep, independent of the two docks (B3): each dock clamps against its own % **and** against the space left so the chart never drops below the minimum. Enlarging one dock can force the other to shrink. |
| Right dock (D18) | The **single** `RightDockWidgetArea` region on the right. **After D41 (2026-10-15) it contains the Portfolio section only** — the Active Trader ladder/panel is removed, so the former two-section "Active Trader + Portfolio" model is **superseded by D41** and its 40%-of-chart-area cap and header are **re-derived for the single section**. |
| ChartView (D47) | The `ui/chart_view.py` protocol behind which the chart stack migrates (strangler). `create_chart_view(tz_offset, editable)` returns the pyqtgraph view by default (`NDT_CHART_ENGINE` unset/pyqtgraph, or `QSettings`) or the LWC view; `DrawingController`/`AlarmController` keep their exact signal signatures across both engines. |
| ChartModel (D47) | The shared Qt-free `services/chart_model.py`: plotted-index filtering, `floor_bar_budget`, whitespace derivation, studies + `_StudyCache`, Heikin-Ashi, volume formatting. Both engines render from it; `ChartPanel` delegates with no behaviour change. |
| Parity matrix (D47) | The 19-row `docs/lwc_parity_matrix.md` checklist (kept updated) that gates cutover: every row must read Done/accepted, or carry an escalation + parity-row entry per rule 10. |
| Spike (D47) | The Phase 0 throwaway in `spikes/lwc/` proving the 9 API behaviours; results + go/no-go gate in `docs/lwc_spike_results.md`. The single owner-authorized exception to the no-prototype convention. |
| barSpacing (D47) | The library-native inter-bar spacing control that **replaces** the pyqtgraph density-cap ACs (`AC-D6.4`/`AC-D7.1`/`AC-D9.1` density language) — an owner-visible AC change, pending Q60. |

| Hold owner (D49) | The entity on whose behalf a shared realtime hold is counted: the main chart, each pop-out, or the alarm monitor (D49.5). Acquire/release is per-owner and idempotent once D49.5's fix lands. |
| Follow-live (D51) | The viewport state in which the main chart tracks the newest bar on live updates: following iff the newest bar's slot is inside the visible range (TradingView shiftVisibleRangeOnNewBar semantic, verified in vendored 5.2.1, owner-confirmed Q72 2026-10-29); any user pan/zoom away means scrolled back. |
| `30 mins` (D52) | The half-hour intraday timeframe: `TIMEFRAME_CONFIG` row `30 mins` → bar size `30 mins` / duration `30 D` (A136); ET half-hour buckets (A137); intraday for planner/backfill (the `AC-D16.8` floor applies), RTH/ETH-relevant (unlike weekly/monthly). |
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
- **Edge Cases:** Dense intraday view keeps a **non-negative** gap (bodies never
  overlap) even when the 4px body minimum applies — the 4px floor is **density-aware**
  and yields to the inter-bar pitch when they collide (D42/ESC-042; see `AC-D7.1`
  revised); single-bar fallback unchanged; studies and session bands
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
- **Edge Cases:** Dense intraday view keeps gaps aligned even when the 4px minimum
  applies (volume inherits the same **density-aware** cap as price — `width = body`,
  `AC-D9.1`/`AC-D9.2` unchanged); single-bar fallback aligns; Line/Area modes still align volume.

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


### Journey 36 — D41: the D36/D37 controls and the whole Active Trader panel are gone and nothing D36/D37/DOM/order-ticket ever runs
- **Preconditions:** IBKR connected; a symbol is loaded (e.g. `SPY`, 5m); a checkout where D36/D37 and the whole
  Active Trader panel (DOM ladder + order-entry ticket) were previously present; an existing user DB that may
  carry a `footprint_cache` table.
- **Steps:** 1) Inspect the chart's floating control cluster and the toolbar. 2) Load several symbols/timeframes
  and watch the IBKR request log. 3) Exercise every remaining control (volume, zoom, alarms, studies, and the
  **Portfolio** Close / Close Group / Flatten All + SL/TP dialogs). 4) Run the full offscreen suite. 5) Start the
  app and load a chart. 6) Look at the right dock.
- **Postconditions:** No `Footprint`, `Classic`/`Tick count`, `Depth`, `IMB —`, or `AUC —` control renders
  anywhere, **no `DOM` toolbar button exists**, and **no Active Trader panel renders** — the **in-app
  order-entry ticket** and the ladder/book tables are gone; **no** D36/D37/DOM-ladder IBKR request is ever
  issued (no `reqHistoricalTicks`/`reqTickByTickData`, **no `reqMktDepth`/`cancelMktDepth` at all** — heatmap or
  ladder, no generic-tick **`"225"`** auction line); the **right dock is Portfolio-only** (re-derived width cap
  + header); the app starts and charts normally, the **retained order machinery** still builds/validates orders
  for the Portfolio / SL-TP paths, and the full offscreen suite is green.
- **Edge Cases:** the **DOM ladder is removed too** (Q48) — `MarketDepthManager`, `ibkr/order_book.py`,
  `_subscribe_dom`, `_on_mkt_depth` and the ladder/book rendering all go, so **ESC-039** (the ladder's `SMART` +
  `isSmartDepth=False` shape) is **moot**; the **whole Active Trader panel — including the `OrderEntryWidget`
  order ticket — is removed** (Q50), so `ui/active_trader_panel.py` no longer exists and there is **no in-app
  order ticket** (DG69); the **order execution/safety machinery** (`ibkr/orders.py`, `ibkr/validation.py`,
  validate-order gate, bracket construction, kill switch) is **kept** for the retained **Close / Close Group /
  Flatten All** and **SL/TP** order paths, and the retained path's `ref_price` comes from a **retained source**
  (session last price / watchlist price map — Plan-level detail, DG71) **[D45 NOTE 2026-10-25: superseded — these paths, the kill switch and the SL/TP dialog are all removed; the app has zero order interaction. See D45 / `AC-D45.6`.]**; the **right dock is Portfolio-only** and
  the `D18`/`D21.13` two-section clauses are **superseded by D41** (DG71); the **D38** news digest + dividend
  markers still work (S0 `"292"`/`"456"`); the **D39** burst/search still works (`INDEX_PROXY` /
  `footprint_cache_key` / `volume_baseline`); the persisted `footprint_cache` table + rows are **removed** (Q49,
  A69, DG70); the **order-entry tests** are re-pointed at the retained machinery or removed with the widget; the
  `DOM` button's deletion changes the D19/D20 toolbar control set, so those geometry fixtures are re-checked.
  **D45 (2026-10-25, incl. its later extension) note:** the **Portfolio Close / Close Group / Flatten All**
  controls, the retained-order-path assertion, **and the kill switch + SL/TP dialog** named in this journey are
  **themselves removed** by D45 — the Portfolio panel is **view-only**, and the app places, cancels and closes
  **nothing** (zero order interaction). The only order-related code that survives is **observation** (the inbound
  order-status / execution callbacks, whose registry is never populated). See Journey 38.

### Journey 37 — D44: collapse the watchlist to a thin vertical bar and click it to expand
- **Preconditions:** IBKR connected (or not — collapse/expand is pure UI state); the Watchlist dock is visible
  and expanded on the left; a symbol may or may not be loaded.
- **Steps:** 1) Click the retained "Watchlist" header button. 2) Observe the left edge. 3) Click the thin bar.
  4) Resize the window / drag the dock splitter while collapsed. 5) Restart the app.
- **Postconditions:** Collapsing replaces the full panel with a **thin vertical bar** (~30px) on the left showing
  the **rotated** text `WATCHLIST` in the **app palette**; clicking the bar **expands** the watchlist to its
  **previous** width with the full panel (header strip, table, `+`) restored (the restored value is the **tracked**
  `MainWindow._watchlist_width` — exactly `clamp(W)` — while the rendered dock width is a Qt layout result
  checked tolerantly; see `AC-D44.2`); the collapsed width **survives** a
  window resize and a dock drag (it is not snapped back to 150px); after a **restart** the watchlist is
  **expanded** (collapse is not persisted).
- **Edge Cases:** collapse from the 150px minimum → expand restores 150px; collapse from the cap → expand
  restores the cap (re-clamped); resize/drag while collapsed does not expand it; floating watchlist (D13) still
  clickable to expand; disconnected/empty watchlist still collapses/expands; first launch starts expanded;
  `CHART_MIN_WIDTH` invariant holds in both states.

### Journey 38 — D45: the news dock, the View menu, the trade context menu, the kill switch and the SL/TP dialog are gone, and nothing in the app touches an order
- **Preconditions:** IBKR connected (and, for the disconnected edge case, disconnected); a symbol loaded (e.g.
  `SPY` 5m); positions visible in the Portfolio panel; open orders resting in TWS; an existing user config/DB that
  may reference the removed News Digest dock or carry saved stop/target values.
- **Steps:** 1) Look for a menubar and press `Ctrl+Shift+N`. 2) Look for a News Digest dock or any control that
  opens one. 3) Load a dividend-paying symbol and check the chart's dividend event markers. 4) Right-click a
  Portfolio position row, a group row, and empty space in the panel. 5) Look for **any** order-related control:
  Close / Close Group / Close All, the **Kill Switch** button, **Set Stop-Loss / Take-Profit**. 6) Exercise
  everything that remains (chart, timeframes, extended hours, watchlist add/remove, alarms, studies, drawings,
  pop-outs, dialogs). 7) Close/cancel in TWS and watch the Portfolio panel. 8) Inspect the positions table's
  columns. 9) Run the full offscreen suite; start the app.
- **Postconditions:** **No menubar** exists and `Ctrl+Shift+N` does nothing; **no News Digest dock** renders and
  no news **`"292"`** line is ever requested; the **dividend** path (`"456"`, tick 59) still works and the chart's
  **dividend/earnings/split markers** still render. Right-clicking a position, a group, or empty space produces
  **no** menu; `ui/trade_context_menu.py` no longer exists and the panel exposes none of the three close signals.
  **No order-related control exists anywhere** — no Close/Close Group/Close All, **no Kill Switch button**, and
  **no SL/TP dialog or entry point**; `ui/stop_loss_target_dialog.py` no longer exists, `ibkr/validation.py` no
  longer exists, and with a mocked client the app issues **zero** `placeOrder`, **zero** `cancelOrder` and
  **zero** `reqGlobalCancel` calls across every remaining affordance. The **Portfolio panel renders
  positions/account summary view-only**, its table shows **8 columns with no Stop / Target column**, and it
  reflects a TWS-side close on the next position update; **[D46 2026-10-25 — SUPERSEDED: the stop/target columns
  and model fields were retained with no migration under A87, but A87 is now REVERSED — they are DROPPED
  (A99 / D46.12); see D46 / Journey 39.]** ~~they are no longer settable or displayed, and a live position update
  writes them empty~~
  — so legacy values do not survive an update (**ESC-060**, corrected 2026-10-25). The suite is green with the
  recorded deletions/adjustments, and `USAGE.txt` / `usage.md` / `docs/codebase-map.md` advertise nothing that
  was removed.
- **Edge Cases:** the `View` menu's shortcut must not survive as an orphan `QAction`; a saved dock state that names
  the removed digest dock is ignored (no error, no dock recreated); a saved `QSettings`/layout entry naming the
  removed toolbar button or dialog is ignored; right-click on a **watchlist** row or column header still opens the
  D21.5 column popup / D22 add-remove (unaffected); right-click on the **chart** is unchanged; **open orders in
  TWS are left untouched by the app** (nothing cancels them — that happens in TWS) and the app must not acquire a
  cancel path on teardown/disconnect; a position row carrying legacy `stop_loss` / `take_profit` values renders
  normally without those columns; the DB schema is **unchanged** (no migration, no destructive schema change) and an old DB
  opens cleanly **[SUPERSEDED BY D46/A99: the two columns are now dropped by migration; rows, indexes and FKs preserved]**; **disconnected** — the Portfolio panel shows "unavailable" and no order path exists to block;
  dividend-free or futures symbols skip dividends as today; a yfinance outage still leaves the IBKR tick-59
  dividend marker rendering (`AC-D38.5` stands); `tests/test_d41_removal.py` mentions `NewsManager`'s
  `queue_depth` in its allow-list (string/comment only) and must stay green after `ibkr/news.py` is deleted.

### Journey 39 — D46: the app has no order module and no order plumbing, and a TWS order error still shows up
- **Preconditions:** IBKR connected (mocked client offscreen, or live TWS); an order resting in TWS placed **outside** the app;
  a chart loaded (e.g. `SPY` 5m); `ibkr/orders.py` absent from the tree.
- **Steps:** 1) `import ibkr.orders` in a REPL. 2) Grep the tree for the module and its symbols. 3) Trigger a TWS **order
  rejection** (201), a **duplicate order id** (103) and an **order cancellation** (202) with the app connected. 4) Exercise
  every remaining affordance (chart, timeframes, extended hours, watchlist add/remove, alarms, studies, drawings, pop-outs,
  Portfolio). 5) Disconnect and reconnect. 6) Run the full offscreen suite; start the app.
- **Postconditions:** `ibkr/orders.py` **does not exist** and `import ibkr.orders` raises `ModuleNotFoundError`; no module
  under `ui/ services/ data/ ibkr/ config/ main.py` imports it, and none of `Orders`, `market_order`, `limit_order`,
  `stop_order`, `bracket_order`, `order_registry`, `_on_open_order`, `_on_order_status`, `_on_exec_details`,
  `_update_order_status`, `_on_order_error` occurs anywhere in the tree — the D45 static scan now **rejects** those names
  instead of allow-listing them. **A TWS order error still appears on the status bar as `Error [<code>]: <TWS's own
  message>` for 8 seconds**: 201 and 103 (severity `fatal`) and 202 (severity `warning`) are all emitted by
  `IBApiClient.error` because none is `info`-classified, and `_on_error` shows the line on its non-session path. The app
  itself no longer adds an order number, a "Rejected"/"Cancelled" verdict or a 12-second duration, because it no longer
  tracks orders. Nothing the app does places, cancels or closes an order (D45's zero-transmit guard stays green). The suite is
  green with exactly the recorded test book, and the app launches and charts normally.
- **Edge Cases:** an order error arriving while `_closing` is set is still dropped by that guard (unchanged); an order error
  whose numeric id coincides with a **live session reqId** takes the session error path first — **pre-existing** (the registry
  lookup already sat after the session branch), **unchanged** by D46, recorded as **DG78**; **202** is a normal cancellation
  (`warning`, not `info`) so it is **not** suppressed; an error with `reqId = -1` (no order id) still shows the generic line;
  a disconnected TWS keeps D40.1's `502` backoff suppression untouched; a stale `__pycache__/orders.*.pyc` cannot make
  `import ibkr.orders` succeed (CPython 3.11 does not import bare cache files) — verify at build time; no `QSettings`/dock
  state ever bound to this chain, so saved layouts are unaffected; the Portfolio table and the retained
  `stop_loss`/`take_profit` **storage** are **gone** (A99 — the columns and model fields are dropped, every row preserved;
  see the expansion below), so there are no values to clear or to persist.
- **Expansion (2026-10-25, Q56–Q59) — steps added:** 7) Open a database created **before** D46 (both stop/target columns
  present, rows seeded) and confirm the app opens it, keeps every row, and no longer has the columns; open it a **second**
  time and confirm the migration is a no-op. 8) Open a **fresh** database and confirm the schema is created without the
  columns and nothing raises. 9) Grep the tree for **every** identifier in D46's inventory and confirm the DELETE set is
  empty while the RETAIN set is present with its named consumer. 10) Add a `UserOrder`, an `order_registry`, an `IBBridge`
  order signal or a stop/target column back, and confirm the guard/scan goes red.
- **Expansion — postconditions added:** `OrderRateLimiter`, `order_limiter`, `MAX_ORDER_NOTIONAL`, `render_fill_blip`,
  `BLIP_DURATION`, `SoundService.play_fill`, the `"fill"` key and `order_fill.wav` **do not exist**, while the alarm chime
  still plays; `IdManager.get_id` / `set_next_valid_id` **still exist and are still called** from the market-data and
  realtime paths, and `IdManager.reserve` is **gone**; `IBApiClient.nextValidId` and `classify_error` **still exist** (they
  are the connection hook and every TWS error's severity gate, not order code); `PRAGMA table_info(positions)` and
  `(trade_groups)` list **no** `stop_loss`/`take_profit`; the Portfolio table still renders **8** columns; the documentation
  trail reads **kept → cleared → dropped** with no surviving counter-claim.
- **Expansion — edge cases added:** a pre-D46 row carrying legacy stop/target values loses **only those two values** and
  keeps its row; an interrupted migration must not strand a half-built table (the `bars` rebuild precedent salvages and
  retries); a stale `__pycache__/order_book.*.pyc` or `test_order_entry_*` cache file is untracked residue, not a live
  symbol; a symbol scan that matches `sort_order` or the ICT `order blocks` is a **false positive** and must be matched
  against the inventory's RETAIN set rather than "fixed".

### Journey 40 — D47: the chart stack migrates behind `ChartView` with parity, and pyqtgraph stays until accepted
- **Preconditions:** IBKR connected (mocked offscreen, or live TWS); a chart loaded (e.g. `SPY` 5m) with studies, drawings, alarms, session bands and event markers; `NDT_CHART_ENGINE` unset (pyqtgraph default).
- **Steps:** 1) Set `NDT_CHART_ENGINE=lwc` (or the `QSettings` equivalent) and reload the chart. 2) Pan, zoom, hover the crosshair, switch timeframes and Ext-Hours/RTH. 3) Add, drag and delete drawings and alarms; open the zone/horizontal-line settings dialogs. 4) Open pop-outs (up to the Q62 cap). 5) Kill the render process (or disconnect/reconnect) and observe recovery. 6) Run the full offscreen suite; open `docs/lwc_parity_matrix.md`. 7) During a live trading session, run one session on the LWC engine and confirm no engine defect.
- **Postconditions:** The LWC chart shows the same bars, studies, drawings, alarms, bands and markers at the same prices/times (parity matrix all Done/accepted); `DrawingController`/`AlarmController` signal signatures are unchanged; pan/zoom/crosshair/timeframe/mode switches behave per the matrix; drawings/alarms edit through the same Qt dialogs; pop-outs sync; the bridge replays after a render-process crash without duplicating or losing bars; the suite is green with exactly the D47 test book; **pyqtgraph is still present** — nothing is deleted in this batch.
- **Edge Cases:** `NDT_CHART_ENGINE` unset/unknown value → pyqtgraph default (never a blank chart); render process terminated mid-session → Python replays the full op log (no partial state); within-session holes render as whitespace while genuine closures stay empty (`gap_is_non_trading` is the source of truth either way); DST/session-boundary bars land on the same logical index in both engines; a 4-hour/`1 day` forming bar primes per `AC-D27.9` on either engine; offscreen/CI with no web-engine → the `@pytest.mark.webengine` cases report skipped, never red, and the manual checklist covers them; an unmeetable AC is escalated with a parity-row entry (rule 10), never silently dropped; pyqtgraph deletion attempted without explicit owner approval + a clean live session → refused.

### Journey 41 — D48: load weekly and monthly charts spanning multi-year history
- **Preconditions:** IBKR connected (mocked offscreen, or live TWS); the timeframe picker lists `1 week` and `1 month` after `1 day`.
- **Steps:** 1) Select `1 week`; confirm two years of weekly bars load. 2) Select `1 month`; confirm ten years of monthly bars load. 3) Toggle Ext Hours ON/OFF on each — the bars are unchanged. 4) Switch symbols; confirm cache separation by (symbol, timeframe). 5) Run the full offscreen suite.
- **Postconditions:** Weekly bars are Monday-anchored (ET), monthly bars calendar-anchored (ET); RTH and ETH return identical bars; no session bands and no collapse are applied; durations `2 Y` / `10 Y` are verified against IBKR by the standalone probe; the suite is green.
- **Edge Cases:** a DST-fold week still opens its bucket on Monday ET; February and 30/31-day months anchor on the calendar boundary (never fixed-seconds); a week/month containing a market holiday aggregates only the sessions that exist (no fabrication); a Monday-anchored week spanning Dec 31/Jan 1 stays one bucket; a disconnected load keeps the D14 no-op semantics (status message, no request).

### Journey 42 — D49: restore a saved pop-out cold, survive attach/host failures, and keep drawing/hold accounting exact
- **Preconditions:** IBKR disconnected or mocked offscreen; a saved pop-out set including a symbol with no in-memory session; a seeded `BarCache` (full for one symbol, gapped for another).
- **Steps:** 1) Cold-start restore: the no-session symbol's pop-out shows cached bars and subscribes; the gapped symbol backfills through the existing pacing path. 2) Inject each `attach()` failure: no stale view, no leaked hold, no ghost registration. 3) Break the chart-host startup: the pop-out shows its error state, and the log keeps the diagnostic entry. 4) Open N pop-outs, change a drawing: one fan-out, end state identical to baseline. 5) Run the hold-count verification probe across main-chart reload + pop-out attach/close: record lasting-effect or clean, and apply the per-owner fix only on the former. 6) Create a pop-out from a non-UTC main chart and restore a saved set: offsets match, labels match.
- **Postconditions:** No restored pop-out is empty-or-stale when cache/backfill can serve it; every failed attach cleans up fully; host failure is never mistaken for missing data; drawing end state is unchanged with 1/Nth of the sync work; the hold count equals active owners, by fix or by verified-close. A created/restored pop-out carries the main chart's offset with identical time labels for the same bars.
- **Edge Cases:** restore of the already-loaded main-chart symbol adds no second aggregator/subscription; restore while disconnected is a D14-style no-op (status message, no request); attach failure on a shared live session never disturbs other views; a mid-session host crash stays outside D49.3 (existing crash handling owns it); zero-pop-out drawing change is a single no-op sync; verification with zero owners asserts a zero count; a restored pre-change save without an offset field falls back to the main chart's current offset (never silent UTC).

### Journey 43 — D50: drag-edit an LWC drawing (whole-move / anchor drag), locked behaviour, reload persistence
- **Preconditions:** A symbol is loaded on the LWC engine and drawings exist (one per kind: trendline, horizontal, zone, fibonacci, measure); one drawing is locked.
- **Steps:** 1) Select a drawing — handles appear while selected (a locked drawing offers no draggable handle). 2) Drag the body (whole-move, all five kinds) and drag an anchor/handle (trendline/fibonacci/measure endpoints, zone edges/corners, horizontal price level). 3) Attempt to drag the locked drawing at the `drag_drawing` surface. 4) Reload the session and check geometry on every view.
- **Postconditions:** Edits apply per the settled matrix (whole-move all five + per-kind anchor drags); the locked drawing's geometry is unchanged with no store write; reloaded geometry matches the committed store state on every view with one fan-out per change.
- **Edge Cases:** drag on a locked drawing is a no-op (no geometry change, no store write); mid-drag cancel leaves the original geometry with no store write; a zero-view edit still persists to the store; a group-coloured drawing keeps its stored colour per the settled (c) rule (Q70 answered), including a locked member repainted by group recolour; former members keep their leave-group colour.

### Journey 44 — D51: scroll back on the main chart, then let live bars arrive — FINALISED 2026-10-29 (Q72–Q76 answered-owner-confirmed)
- **Preconditions:** A symbol is loaded on the main chart with live updates flowing (mocked offscreen); the viewport starts following the live edge.
- **Steps:** 1) Pan/zoom away from the newest bar. 2) Let live bars arrive. 3) Observe the viewport. 4) Invoke Fit/reset. 5) Switch symbols and switch back. 6) Trigger a full-series replacement on the same symbol and on a new symbol.
- **Postconditions (FINAL, Q72–Q76 answered-owner-confirmed 2026-10-29):** the viewport does not move while scrolled back (Q73(a)); follow resumes only on pan-back-to-edge or Fit/reset; Fit/reset frames all loaded bars and re-engages follow, plus the go-to-realtime affordance (Q74(a)); switching back restores viewport + follow state per symbol (Q75(a)); a same-symbol replacement preserves viewport + follow state while a new symbol starts following (Q76(a)).
- **Edge Cases:** live bars arriving mid-pan gesture; replacement landing while scrolled back; symbol switch while disconnected (D14 no-op semantics preserved); zero-bar series (Fit is a no-op with no error).
- **Edge Cases:** live bars arriving mid-pan gesture; replacement landing while scrolled back; symbol switch while disconnected (D14 no-op semantics preserved); zero-bar series (Fit is a no-op with no error).

### Journey 45 — D52: load a 30-minute chart, switch modes, and span multi-week history
- **Preconditions:** IBKR connected (mocked offscreen, or live TWS); the timeframe picker lists `30 mins` between `15 mins` and `1 hour`.
- **Steps:** 1) Select `30 mins`; confirm half-hour bars load with the `09:30` RTH open on a bucket boundary. 2) Toggle Ext Hours ON/OFF — each mode shows its own session-window bars (unlike weekly/monthly). 3) Reload across successive loads; confirm history extends backwards toward the 30-session floor. 4) Switch symbols; confirm cache separation by (symbol, timeframe, mode). 5) Run the full offscreen suite.
- **Postconditions:** Buckets are ET half-hour-anchored; RTH and ETH bar sets differ per their session windows; the `30 D` duration is verified against IBKR by the standalone probe; the suite is green.
- **Edge Cases:** a DST-fold half-hour still opens its bucket on the ET clock; a holiday-shortened session aggregates only the sessions that exist (no fabrication); a disconnected load keeps the D14 no-op semantics (status message, no request); a mode switch neither leaves a hole nor presents the other mode's bars as coverage (`AC-D16.9`).

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
- **AC-D6.4 (ESC-009 — high-DPI coverage; REVISED 2026-10-15 by D42/ESC-042 — the floor is density-aware, superseding the former *unconditional* form)** Given the app renders candles at any bar density, When the candles render, Then the body's rendered width is `min( max(0.65 × pitch, F), pitch )`, where `pitch` is the inter-bar centre-to-centre distance and `F` is the D6 legibility floor (`4` device pixels at DPR `2`; the wick stays a cosmetic 1-device-pixel line), with `body`, `pitch` and `F` measured in the **same pixel unit**. Consequences, all required:
  - **(i) No overlap, at any density:** `body <= pitch` always — adjacent bodies never overlap and the inter-bar gap is never negative. This is the **winning guarantee** when the floor and the pitch collide (see `AC-D7.1`).
  - **(ii) Legibility floor holds in the non-dense regime:** when `pitch >= F`, `body = max(0.65 × pitch, F) >= F`, so the D6 intent (wick 1 device px; body `>= 4` device px at DPR 2, strictly wider than the wick, no rounding collapse to one line) is **unchanged**.
  - **(iii) The floor yields at extreme density:** when `pitch < F`, `body = pitch` (the 4-px floor **relaxes to the pitch**; bodies may abut, `gap == 0`, but never overlap).
  - Measurable (offscreen, no live TWS): render the real `CandlestickItem` at DPR 2 for a dense view (e.g. SPY 5 mins, 192 bars, Ext Hours ON, 900 px pane — the ESC-041/ESC-042 repro, pitch ~ 3.83 device px) and measure the **rendered** body from the `QPicture` bounding box (never re-derive the formula); assert `body <= pitch` (and `body == pitch` in this dense case), i.e. a pixel scan shows at least one non-body device pixel between adjacent bodies' centres — a contiguous run with zero gap is the failure ESC-041 reports. In the non-dense regime (e.g. 78 bars, pitch ~ 8.86 px) assert `body == max(0.65 × pitch, F) > F`.
  - **Supersession (recorded, not silent):** the former clause "the body remains `>= 4` device pixels wide" was **unconditional** and is **superseded** by the density-aware rule above. The wick clause (cosmetic 1 device px) is **unchanged**.

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
- The existing device-pixel minimum for the body (from D6, >=4px) continues to apply
  **as a density-aware floor** (revised 2026-10-15 by D42/ESC-042): it holds whenever
  the inter-bar pitch is `>= 4` device px, and **yields to the pitch** (body capped at
  the pitch) when the pitch is smaller, so bodies never overlap. See `AC-D6.4` (revised)
  and `AC-D7.1` (revised).

**Acceptance Criteria (Given/When/Then):**
- **AC-D7.1 (REVISED 2026-10-15 by D42/ESC-042 — precedence when the gap and the 4-px floor collide)** Given a loaded chart at any bar density, When candles render, Then the gap between adjacent bodies is `pitch - body >= 0` (a **hard no-overlap guarantee**; the gap is **never negative**) and:
  - in the **normal regime** (`pitch >= F`, `F` = the D6 4-device-pixel floor) the gap is `~35%` of bar spacing (body half-width `0.325 × median_diff`, `body = max(0.65 × pitch, F)`), visibly larger than the current 20% gap;
  - the gap is **positive (`> 0`) whenever `pitch > F`**;
  - in the **extreme-density regime** (`pitch <= F`) the gap may reach **`0`** (bodies abut) because the D6 floor has yielded to the pitch — a **zero** gap is acceptable there, a **negative** gap (overlap) is **never** acceptable.
  - **Supersession (recorded, not silent):** the former "the gap remains positive" wording in this criterion and in the D7 dense-view edge case is **relaxed to `gap >= 0`** by D42/ESC-042 (see `AC-D6.4` revised). The 35%-gap intent in the non-dense regime is **unchanged**.
- **AC-D7.2** Given the same data, When compared to the current rendering, Then the
  on-screen distance between bodies is larger by ~15–18% of bar spacing (the gap
  grows from 0.20 to 0.35 of spacing).

**Edge Cases:**
- Very dense intraday view (hundreds of candles) keeps the gap proportional (35% of
  spacing) while the pitch allows, but the density-aware 4px body floor may bind — the
  gap is **never negative** (`>= 0`) and the chart does not become empty; at extreme
  density (pitch `<= 4` device px) the floor yields and bodies may abut (D42/ESC-042).
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
  - **Note (2026-10-15, D42/ESC-042):** the "4px body minimum" here is the **density-aware** floor of `AC-D6.4` (revised) — the clamped `w` is capped at the inter-bar pitch, so volume bars never overlap either; volume width stays **equal** to the price body width (`AC-D9.1`).

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
    **parameterized over all nine timeframes** (`1 min`, `5 mins`, `15 mins`, `30 mins`, `1 hour`, `4 hours`,
    `1 day`, `1 week`, `1 month`) and at least two symbols (Q39) — not `SPY 5 mins` alone.
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

- **AC-D16.8 (minimum intraday history depth — 30 trading sessions, RTH **and** Ext-Hours; Q47/ESC-038, answered 2026-10-15; EXTENDED 2026-10-15 by D42/ESC-038; EXTENDED TO ETH 2026-10-15 by Q52)**
  - **Restatement (RG-P7-1 / ESC-079, 2026-10-28 — settled P7 direction S-P7-1/S-P7-2, implemented and green):**
    the 30-session floor is satisfied **monotonically across successive loads** — persist-and-resume with a
    **per-load cap** of at most one quarter of the `MAX_HISTORICAL_PER_600S` rolling slots and an **oldest-first**
    floor fill (per-chunk persist+render; same-chart reloads coalesce) — **never necessarily inside one load**;
    there is no single-load deadline. The single-load implication in the Given/When/Then and Measurable below is
    **SUPERSEDED as a reading** (original wording preserved beneath as history); the normative target is the
    successive-loads floor fill.
  Given an intraday timeframe (`1 min`, `5 mins`, `15 mins`, `30 mins`, `1 hour`, `4 hours`) in **either** session mode —
  **RTH** (`extended_hours=False` → `useRTH=1`, session window `09:30–16:00 ET`) **or** **Ext-Hours (ETH)**
  (`extended_hours=True`, extended window `04:00–20:00 ET`) — When the symbol is loaded and all historical
  request(s) complete, Then the displayed bar series covers **at least 30 trading sessions before the current
  session** — 30 **trading sessions** (not 30 calendar days) — so the fetch/backfill must exceed one IBKR request
  window and extend history **backwards**, not merely carry the current session. (`1 day` is not covered by this
  floor.) The floor is **one** floor shared by both modes; the mode selects only **which session window** a bar
  must fall inside to count (below). The RTH-only scoping that the D42 default assumed is **superseded by Q52**
  (owner-confirmed 2026-10-15: "Extend it to Ext-Hours charts too.").
  - **Clarification (ESC-038) — a "session" is counted by bars inside the current mode's session window, not by
    calendar-day presence.** A trading day contributes to the 30-session floor **only if the series holds at
    least one bar inside the current mode's session window for that day** — `09:30–16:00 ET` under RTH
    (`ext_hours=False`), `04:00–20:00 ET` under ETH (`ext_hours=True`). A day present in the cache with bars only
    **outside** that window does **not** count and must be treated as a **missing span** (`AC-D16.9`). This is what
    makes "shows only the current session" a measurable shortfall rather than an unfiled behaviour.
  - **Clarification (ESC-038) — every intraday timeframe currently falls short.** `TIMEFRAME_CONFIG` windows are
    **calendar-day** durations (`1 min → 1 D`, `5 mins → 5 D`, `15 mins → 5 D`, `30 mins → 30 D`, `1 hour → 10 D`,
    `4 hours → 30 D`); under `useRTH=1` these yield roughly **1 / 3–4 / 3–4 / ~21 / 7 / ~21** RTH sessions respectively
    — all **fewer than 30** — so the floor requires **chained, paced, backwards-extending fetches** on
    **all six** intraday timeframes, not only `1 min`. Under ETH the same calendar-day windows still fall short
    of 30 **extended-session** days for the shorter timeframes, so the backwards-extending fetch is required in
    both modes.
  - **Mode isolation (Q52).** The two modes **share one floor** but must **not cross-contaminate**: a session
    counted under RTH (>= 1 RTH bar) is **not** automatically satisfied under ETH, and vice versa. Because the
    session window differs, the **bar cache/key must be mode-aware** in **both** directions so a mode switch
    (Ext Hours ON ↔ OFF) neither leaves a hole nor reads the other mode's bars as the current mode's coverage
    (`AC-D16.9`).
  - Measurable (offscreen, no live TWS): drive the real load path with a stubbed historical feed and assert the
    resulting bar series spans **>= 30 distinct trading sessions before the current one** for each intraday
    timeframe in **both** modes, where a session is counted only when it has **>= 1 bar inside that mode's
    session window**. The ESC-038 repro (`1 min` RTH → a single `1 D` request, 601 cached bars over one day) must
    be **RED** pre-fix; the same assertion under `ext_hours=True` must also hold.
  - **Practical consequence (implementation matter — Plan/Build, not a requirements gap):** IBKR caps `1 min`
    at `1 D` per request, so the floor requires **chained, paced, backwards-extending fetches** — the D16
    backfill today anchors at `min(present_days)` and heals only holes *inside* `[earliest_cached_day, now]`,
    never backwards (DG65). If Plan judges this a **request-window strategy** change rather than a constant, the
    downstream route is **Plan**; the requirement itself is settled here.

- **AC-D16.9 (mode-aware day presence + mode-aware cache — a present-but-empty day is a missing span, for **both** RTH and ETH; ESC-038/ESC-037, NEW 2026-10-15 by D42; EXTENDED TO ETH 2026-10-15 by Q52)**
  Given the D16 backfill's day-presence pass (`services/backfill_service.py::find_missing_spans`) and the current
  RTH/ETH mode, When the cache holds bars for a **trading day** but **none of them fall inside the current mode's
  session window**, Then that day **MUST be reported as a missing span** for the current mode — it is **not**
  "present"/filled — so the load issues the request that fills it. What "empty" means is **mode-specific**:
  - **Under RTH (`ext_hours=False`, window `09:30–16:00 ET`):** a day whose cached bars are **all outside RTH**
    (e.g. only pre-market `04:00–09:30` and/or post-market `16:00–20:00` ET bars) is a **missing RTH span** — the
    RTH request that fills it must be issued.
  - **Under ETH (`ext_hours=True`, extended window `04:00–20:00 ET`):** a trading day with **no bar inside the
    extended session window** for that day — i.e. no cached bar whose timestamp falls in `04:00–20:00 ET` on that
    day — is a **missing ETH span** (the trading day has no bars at all, or none inside the extended window).
    Note bar timestamps are period **starts** (`data/bar_aggregator.py`), so the window test applies to a bar's
    start timestamp, not its end.
  Equivalently:
  - Day presence is decided against the **same session window the load uses** (`ext_hours`), not against the
    calendar day's mere presence in the cache; a mode switch (Ext Hours ON ↔ OFF) must **not** leave a hole and
    must **not** present the other mode's bars as satisfying the current mode.
  - The bar cache/key is **mode-aware** (RTH vs ETH) so a mode switch cannot read the other mode's bars as the
    current mode's coverage (the `useRTH`-blind cache key is the compounding defect ESC-037 names). This applies
    **in both directions**: a day filled only with extended-window (pre/post) bars is not RTH-covered, and a day
    filled only with RTH bars is still ETH-covered (RTH lies inside `04:00–20:00 ET`).
  - The **no-fill/no-silent-hole** rules (`AC-D16.1`/`AC-D16.4`) and the **genuine-closure** rule (`AC-D16.3`)
    are **unchanged**; this criterion only fixes how **presence** is decided.
  - Measurable (offscreen, no live TWS): (a) seed a trading day with only pre/post (ETH) bars, call
    `find_missing_spans(cached_ts, now, timeframe, ext_hours=False)` and assert it returns a **non-empty** span
    covering that day's **RTH** window (today it returns `[]` — the ESC-037 RED); (b) with the **same** seed, call
    `find_missing_spans(cached_ts, now, timeframe, ext_hours=True)` and assert it returns **no** missing span for
    that day (its bars lie inside the ETH window — the ETH day is present); (c) seed a trading day with **only RTH
    bars** and assert **both** the RTH call and the ETH call report it present (RTH bars lie inside
    `04:00–20:00 ET`), i.e. the two modes do not cross-contaminate.
  - **Scope note:** this is the **requirements** side of BUILD escalation **ESC-037** (same code path from the
    other side) — the fix is BUILD; the criterion above is its normative target. It also protects `AC-D16.8`'s
    30-session count (a present-but-empty day must not be counted as a session, in **either** mode).

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

**Resolved (2026-10-15 — ESC-038 / Q47 answered; EXTENDED 2026-10-15 by D42/ESC-038; ETH scope added by Q52):** the
minimum intraday history depth — **a minimum of 30 trading sessions before the current session** for each
intraday timeframe (`1 min`…`4 hours`) — is now specified and recorded as **`AC-D16.8`**, for **both RTH and
Ext-Hours (ETH)** (`ext_hours=False` and `ext_hours=True`). `ibkr/market_data.py::TIMEFRAME_CONFIG` gives `1 min` a
`"1 D"` window (exactly one RTH session under `useRTH=1`) and `services/backfill_service.py::find_missing_spans`
anchors at the earliest cached day (never backwards), so a fresh `1 min` RTH chart shows one session — now a
**shortfall against `AC-D16.8`**, no longer an unfiled behaviour. Delivering the floor needs chained, paced,
backwards-extending fetches (IBKR caps `1 min` at `1 D` per request) — an implementation matter for
**Plan/Build** (window strategy), not a requirements gap. See `design_gaps.md` **DG65** (resolved) and **DG72**.
**D42/ESC-038 extension (2026-10-15):** `AC-D16.8` now also states that a **session is counted by bars inside
the current mode's session window** (a present-but-empty day does not count) and that **all five** intraday
windows fall short; the present-but-empty treatment is recorded as the new **`AC-D16.9`** (the requirements side
of BUILD **ESC-037**). **Q52 (owner-confirmed 2026-10-15)** extended the floor and the present-but-empty rule to
**ETH** (`ext_hours=True`), superseding the RTH-only default.


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
> **SUPERSEDED (partially) BY D41 — 2026-10-15.** The owner confirmed (Q50 = YES) that the **right dock becomes
> Portfolio-only**: the **whole Active Trader panel** (its DOM ladder **and** its order-entry widget) is removed
> by **D41**, so the two-section "Active Trader + Portfolio" model below no longer describes the shipped shape.
> **Superseded clauses:** `AC-D18.3` (Active-Trader/Portfolio **equal width** — no longer two sections), the
> **"Active Trader ladder + Portfolio"** wording in `AC-D18.1`/`AC-D18.2`, and the **ladder content** references
> in `AC-D18.6`/edge cases. **Still in force:** the right dock must remain **fully visible in full screen** with
> a **non-zero width** and remain **clamped against the chart minimum** (`AC-D18.1`/`AC-D18.4`/`AC-D18.5`/
> `AC-D18.7`/`AC-D18.8`), now applied to a **single Portfolio section**. The **40%-of-chart-area cap (B2)** and
> the **dock header** are **re-derived for the single-section dock** (see `### D41` and `design_gaps.md` DG71) —
> the numeric cap and header mechanism are Plan-level details. The old clauses are kept below for history
> (DOC-4), not silently deleted.
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
- **AC-D18.1 (full-screen visibility; reported defect)** *(The "Active Trader ladder + Portfolio" wording is
  **superseded by D41** — the region is now **Portfolio-only**; the visibility requirement stands.)* Given the
  app is shown **full screen**, When the chart and the right region render, Then the right region (Portfolio;
  **was** Active Trader ladder + Portfolio) is
  **fully within the visible window area** — its left edge `>= chart area right edge` and its right edge
  `<= window right edge`, with a **non-zero visible width** — and is on-screen **without manual
  repositioning**. (Measurable: assert the dock's `geometry()` lies within the window's `rect()` and
  `width() > 0` in an offscreen full-screen-sized window.)
- **AC-D18.2 (grow up to the cap; chart shrinks)** *(The **40%-of-chart-area cap is re-derived for the single
  Portfolio section** by D41 — the numeric cap is a Plan-level detail; the grow/chart-shrink requirement
  stands.)* Given the right region is visible,
  When the user enlarges it (drag the handle / `resizeDocks`), Then its width grows continuously up to
  `floor(0.40 × chart_area)` and the **chart area narrows correspondingly**. (Measurable: right-region
  width `<= floor(0.40 × chart_area)` during and after the resize; chart width decreases as the region
  grows.)
- **AC-D18.3 (equal width by construction; B2)** — **SUPERSEDED BY D41 (2026-10-15):** with the Active Trader
  panel removed, the right dock is **Portfolio-only**, so there are no longer two sections to keep equal. (Kept
  for history; the D18 visibility/clamp clauses still apply to the single Portfolio section.) Given the single
  right region is visible, Then the Active Trader ladder section and the Portfolio section render at **equal
  width** — i.e. each section's width equals the region's content width (they are stacked in one region).
  (Measurable: `active_trader section width ≤ region content width` and `portfolio section width ≤ region
  content width`, and the two sections' widths are equal within a 1px tolerance.)
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
- **AC-D18.6 (content must not push the dock off-screen)** *(The **ladder content** reference is
  **superseded by D41** — the region is Portfolio-only; the portfolio content rule stands.)* Given the
  portfolio content is wider than the region, When the region renders, Then the region's own geometry still
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
> **SUPERSEDED (partially) BY D41 — 2026-10-15.** The owner confirmed (Q50 = YES) that the **whole Active Trader
> panel is removed** and the **right dock becomes Portfolio-only**, so the **two-toggle / two-section collapse
> model** below no longer describes the shipped shape: **`AC-D21.13.1`** (making **"Active Trader" = the right
> dock's title bar** one of the two toggles) is **superseded** — the right dock's title-bar widget can no longer
> be the (removed) Active Trader header — and **`AC-D21.13.2`/`AC-D21.13.3`** (one-hidden-collapses-in-height
> **of two** panels; both-hidden-collapses-horizontally) are **superseded** because only **one** section
> (Portfolio) remains. The **`AC-D21.13.4`** strike-through convention **still applies** to the retained
> Portfolio toggle. The **single-section** dock's **header / collapse affordance is re-derived** (see `### D41`
> and `design_gaps.md` DG71) — the exact mechanism is a Plan-level detail. The DOM button referenced in the edge
> cases below is **removed by D41**, so that reconciliation is moot. Old clauses kept below for history.
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
> **D41 interaction (2026-10-15, Q50 = YES).** The **order-entry UI** that D26 hardened — the `OrderEntryWidget`
> MKT/LMT/STP/Bracket ticket (`ui/active_trader_panel.py`) and the DOM-ladder click-to-order (ask/bid) path — is
> **REMOVED** by **D41**. **What goes:** the order-entry **UI surface** (those controls). **What stays:** **all
> D26 safety requirements and machinery** — the single `validate_order()` gate (D26.7), bracket side-correctness
> (D26.1), order-ID reservation (D26.2), the fail-fast port check (D26.5), the kill switch (D26.8),
> rejection/registry/error handling and blocked-while-disconnected (D26.9) — because they **also guard the
> retained order paths**: Portfolio's **Close / Close Group / Flatten All** and the **SL/TP dialogs** (D26.3)
> place orders through the same `ibkr/orders.py` + `ibkr/validation.py` machinery. **[D45 NOTE 2026-10-25: superseded — these paths, the kill switch and the SL/TP dialog are all removed; the app has zero order interaction. See D45 / `AC-D45.6`.]** The **control-specific**
> clauses that name the removed ticket — **`AC-D26.4`** (MKT buttons) and the order-entry/ask-click half of
> **`AC-D26.6`** (its `_pending_ladder` ask-click path is on the removed ladder) — have **no control to exercise**
> after D41; the **safety invariant they guarded** (validate with the spinbox quantity, `qty>0`, no traceback,
> correct side) **remains required** for the retained controls. **Do not delete the safety machinery** when
> removing the order-entry UI.
>
> **D45 interaction (2026-10-25, incl. its later extension).** With the Portfolio close / close-group / flatten-all
> path **also removed**, the app has **no order path at all**; and with the **kill switch** and the **SL/TP dialog**
> removed too (owner extension, 2026-10-25 later), it has **no order interaction at all**. Of D26, only the
> **fail-fast port check + badge** (D26.5) and the **connection half** of the error alerts (D26.9) still have a live
> surface; the order registry that D26.9's rejection half reads is **never populated**, so it is inert.
> **Moot / superseded after D45:** `AC-D26.3` (the SL/TP dialog's labelling branch — the dialog **no longer
> exists**), `AC-D26.7` (the `validate_order()` gate), **all of `AC-D26.8`** (D26.8's kill switch is **removed**;
> its pre/post counts have no caller) and `AC-D26.9`'s order-entry/registry clauses. `AC-D26.4`/`AC-D26.6` were
> already control-less after D41. **Do not delete `AC-D26.5`** — the fail-fast port check is **not** an order path.
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
  - **D27.9 (B-1.9; REVISED 2026-10-16 by D43/ESC-036 — the former "trailing 5-second history" wording is
    SUPERSEDED):** on chart load the aggregator **SHALL** be primed with trailing history covering the
    **elapsed portion of the forming period** before the live feed attaches, so the forming candle's OHLCV is
    not fabricated. The priming request **SHALL** use a bar size valid for that elapsed span and a `duration`
    inside that bar size's IBKR-accepted range:
    - **elapsed span <= 3600 S** — the **`1 min`**, **`5 mins`**, **`15 mins`**, **`30 mins`** and **`1 hour`** timeframes →
      `bar_size='5 secs'`, `duration` = the elapsed span clamped into **`[60 S, 3600 S]`**;
    - **elapsed span > 3600 S** — the **`4 hours`** (span up to 14400 S) and **`1 day`** (span up to 86400 S)
      timeframes → `bar_size='1 min'`, `duration` = the elapsed span clamped into **`[60 S, 1 D]`**.
    Bars returned whose `ts` precedes the current period's start **SHALL NOT** fabricate a completed
    previous-period candle. *(Rationale: 5-second bars cannot span a 4-hour or 1-day forming period at all —
    IBKR caps `5 secs` at `3600 S`, so the former request `bar_size='5 secs'`/`duration='7200 S'` returned TWS
    error 321 and left `4 hours`/`1 day` unprimed. `1 min` bars cover the whole elapsed span in one request and
    reuse the existing priming/aggregator path. See D43.)*
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
  - **AC-D27.9 (REVISED 2026-10-16 by D43/ESC-036)** Given a fresh chart load mid-period on **any selectable
    timeframe**, Then a priming request is issued whose `bar_size` is valid for the elapsed forming-period span
    (`5 secs` for `1 min`/`5 mins`/`15 mins`/`30 mins`/`1 hour`; `1 min` for `4 hours`/`1 day`) with a `duration` inside
    that bar size's IBKR-accepted range (`[60 S, 3600 S]` for `5 secs`; `[60 S, 1 D]` for `1 min`) — never
    `5 secs` with a `duration` outside `[60 S, 3600 S]` — and the forming candle's open/high/low/close/volume
    reflect the primed history over the elapsed period, not just the first live tick.
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
> **SUPERSEDED BY D41 (2026-10-15)** — the D36 footprint feature is being **removed** at the owner's
> 2026-10-15 request (see `### D41`). This section and `AC-D36.*` are retained **for history only** and are
> no longer live criteria. The related ESC-040 open item (the footprint tick-request error path stuck in
> `loading` on error 162 / no not-subscribed state) is made **moot** by D41 (the footprint is removed wholesale).
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
> **SUPERSEDED BY D41 (2026-10-15)** — the D37 depth heatmap / imbalance / auction feature is being
> **removed** at the owner's 2026-10-15 request (see `### D41`). This section and `AC-D37.*` are retained
> **for history only** and are no longer live criteria. The related open items — **ESC-035** (depth error 2152;
> Q46/DG64) and, because **Q48 (2026-10-15) also removes the Active Trader DOM ladder**, **ESC-039** (the ladder's
> `SMART` + `isSmartDepth=False` request shape) — are both made **moot** by D41 (no depth feed remains).
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

**Moot (2026-10-15 — D41 / Q46 supersession):** the ESC-035 question about IBKR depth error **2152**
("Market depth smart depth exchanges" — a *partial* venue-permission report) is **moot**. The D37 depth feed is
being **removed** by **D41** (and Q48 also removes the DOM ladder), so there is **no depth feed whose 2152
behaviour needs defining**. The owner did **not** choose options (a)/(b)/(c); the correct resolution is
**supersession by D41**. `ibkr/error_codes.py::classify_error`'s 2152 handling and
`ui/ticker_session.py::TickerSession.on_depth_error` are removed with the feature.


### D38 — Event markers + news-for-holdings digest — as-built / APPROVED 2026-10-13
- **Area:** `data/events/provider.py` (`Event`, `EVENT_TYPES`, corporate-events-only guard,
  `parse_ib_dividend_string`), `data/events/ibkr_source.py`, `data/events/yfinance_source.py` (`YFinanceCache`,
  TTL), `ibkr/news.py` (`NewsManager`), `ui/news_digest_dock.py` (`NewsDigestDock`),
  `ui/event_marker_overlay.py` (`EventMarkerOverlay`, `EVENT_STYLE`), `ui/ticker_session.py`
`ui/ticker_session.py` (`_merge_events`, tick-59 dividend merge). **D45 (2026-10-25): `ibkr/news.py`
  (`NewsManager`) and `ui/news_digest_dock.py` (`NewsDigestDock`) are REMOVED, together with the news `"292"`
  S0 line, the `View` menubar and `reqNewsArticle`; everything else listed here (the event provider,
  `EventMarkerOverlay`, `_merge_events`, the tick-59 dividend merge, the S0 `"456"` line) is RETAINED.**
- **Status:** **as-built / APPROVED 2026-10-13** (970 tests green; no blocking findings). Feature; D1–D37 not
  reopened. Acceptance criteria **authored 2026-10-14 (Q45/DG46)** from the shipped behaviour and
  `tests/test_d38_events_news.py` (which states AC-D38.1–AC-D38.6 in its own header).
- **Backing tests:** `tests/test_d38_events_news.py`.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D38.1 (markers + countdown)** Given 1 earnings + 1 dividend + 1 split event, Then three markers render
    with distinct per-type styling at the correct dates and a countdown names the next upcoming event
    ("Split in 4d"); no upcoming event → the countdown is hidden; events unavailable → "Event data unavailable";
    a date correction moves the marker (id-keyed) rather than duplicating it.
  - **AC-D38.2 (digest groups + article fetch)** — **SUPERSEDED BY D45 (2026-10-25): the News Digest dock,
    `NewsManager` and `ibkr/news.py` are removed, so there is no digest to group or fetch into.** Given 2 held
    symbols + synthetic headlines, Then the digest
    groups headlines under each holding and clicking a headline fetches that article (`reqNewsArticle`).
  - **AC-D38.3 (no news entitlement)** — **SUPERSEDED BY D45 (2026-10-25): with no digest there is no such
    state to show.** Given no API news subscription, Then the digest shows the explicit
    "No API news subscription" state (never silently empty).
  - **AC-D38.4 (corporate-events-only guard)** Given a non-corporate event type, Then it is rejected at the
    provider boundary; the yfinance layer only calls the approved corporate-events endpoints (one secondary
    source only).
  - **AC-D38.5 (IBKR-first merge under a yfinance outage)** Given an IBKR tick-59 dividend and yfinance down,
    Then the dividend marker still renders while earnings/splits show "event data unavailable"; a yfinance
    dividend on the same date as an IBKR dividend is dropped (IBKR wins), other yfinance events survive.
  - **AC-D38.6 (regression)** Given the feature, Then the full offscreen suite is green and no D1–D37 criterion
    regresses. **REVISED BY D45 (2026-10-25):** the green-suite rule stands, but
    `AC-D38.2`/`AC-D38.3` are no longer live criteria; the surviving D38 surface is the **corporate-event
    markers + dividend merge** (`AC-D38.1`/`AC-D38.4`/`AC-D38.5`).
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

### D41 — Remove D36 (footprint) + D37 (depth heatmap / imbalance / auction) + the **entire Active Trader panel** (DOM ladder + order-entry UI) — USER-REQUESTED 2026-10-15
- **Area (REMOVE):** the D36/D37 feature code across `ui/chart_panel.py` (floating cluster + render layers),
  `ui/ticker_session.py` (footprint / depth / auction), `ui/main_window.py` (wiring), and the feature-exclusive
  modules `ui/footprint_item.py`, `ui/depth_heatmap_item.py`, `services/footprint_service.py`,
  `services/depth_heatmap.py`, `data/footprint_cache.py`, `ibkr/tick_history.py`; plus the D36/D37 halves of
  `ibkr/bridge.py` (historical-tick signals), `ibkr/client.py` (`historicalTicks*` overrides),
  `ibkr/subscription_manager.py` (`DEPTH_HEATMAP` tag), `ibkr/contracts.py` (`resolve_footprint_contract`),
  `data/db.py` (`footprint_cache` DDL), and the two feature test files `tests/test_d36_footprint.py` /
  `tests/test_d37_microstructure.py`. **Scope widened 2026-10-15 (Q48 = YES):** the **Active Trader DOM
  ladder** depth path is **also removed** (see "Scope — REMOVE", DOM ladder bullet). **Scope widened again
  2026-10-15 (Q50 = YES / YES):** the removal now covers the **entire Active Trader panel** — the ladder/DOM
  **and** the in-app **order-entry widget** — and the **right dock becomes Portfolio-only** (see "Scope —
  REMOVE", the "Active Trader panel — whole" bullet, and "Scope — KEEP").
- **Status:** **NEW / USER-REQUESTED 2026-10-15; scope FINALISED 2026-10-15 (Q48/Q49/Q50 answered)** — a
  **removal** work item that **SUPERSEDES `AC-D36.*` and `AC-D37.*`** (retained for history per DOC-4) **and
  supersedes the affected `D18` and `D21.13` clauses** (the two-section Active-Trader+Portfolio dock model; see
  those entries' supersession notes). D1–D35 and D38–D40 are **not** reopened; the **retained order machinery**
  (execution/safety) is **not** removed.
- **Rationale (owner, verbatim 2026-10-15):** *"I want to remove footprint, Depth, Imbalance (IMB), Auction
  (AUC) and all associated code from the app. There is no need for them when it does not work properly."*
  Corroborated by open findings ESC-040 (footprint), ESC-035 (depth 2152), ESC-039 (DOM ladder SMART /
  `isSmartDepth`), and a pending overlap investigation (DG68). **Owner follow-ups (Q50, 2026-10-15):** remove
  the **whole Active Trader panel** — the in-app **order-entry UI** goes with it (there is **no in-app order
  ticket** afterwards) — and make the **right dock Portfolio-only**. Portfolio's **Close / Close Group /
  Flatten All** and the **SL/TP dialogs** remain and place orders through the retained order machinery.
  **[REVERSED BY D45 (2026-10-25, incl. its later extension): the closes, the SL/TP dialog and the kill switch
  are removed — see D45. This line records the D41 decision, not the current end state.]**
- **Scope — REMOVE (feature-exclusive):**
  - **D36:** `FootprintItem` (`ui/footprint_item.py`), `FootprintService` (`services/footprint_service.py`),
    `FootprintCache`/`is_cacheable` (`data/footprint_cache.py`), `TickHistoryManager` (`ibkr/tick_history.py`),
    the `historical_ticks_bid_ask`/`historical_ticks_last` bridge signals + `historicalTicksBidAsk`/
    `historicalTicksLast` overrides, the `footprint_cache` DB table DDL, the session footprint
    wave/forming/snapshot/cache, the chart `Footprint`/`Classic`/`Tick count` controls + render/status layer, and
    `ibkr/contracts.py::resolve_footprint_contract`.
  - **D37:** `DepthHeatmapItem` (`ui/depth_heatmap_item.py`), `DepthHeatmapService` (`services/depth_heatmap.py`),
    the chart `Depth`/`IMB —`/`AUC —` controls + heatmap strip + state text, the session depth
    refcount/shared-feed/error-state (`ui/ticker_session.py` `subscribe_shared`/`release_shared`/
    `resubscribe_shared`/`on_depth_update`/`on_depth_error`, session `depth_req_id`), the auction S0 **`"225"`**
    need + `auction_state`, and the `DEPTH_HEATMAP` subscription tag.
  - **DOM ladder (widened 2026-10-15, Q48 = YES):** the whole Active Trader depth path —
    `ibkr/market_depth.py` (`MarketDepthManager` in full: `subscribe`/`cancel`/`cancel_all`/`has_subscription`/
    `on_update`/`snapshot` **and** the D37 shared-feed half `subscribe_shared`/`release_shared`/`shared_req_id`/
    `resubscribe_shared`/`_shared`), `ibkr/order_book.py` (`OrderBook`, `apply_operation`, `Level`, `SIDE_*`),
    the ladder/book rendering in `ui/active_trader_panel.py` (`LadderTable`, `BookTable`, `on_depth_callback`,
    the ladder/book tabs, `update_from_snapshot`), `ibkr/bridge.py::update_mkt_depth`,
    `ibkr/client.py::updateMktDepth`/`updateMktDepthL2`, `MainWindow._on_mkt_depth` (the DOM-reqId branch **and**
    the D37 session-heatmap branch), the **`DOM` toolbar button** + `MainWindow._on_dom_toggled` +
    `_subscribe_dom` + `_depth_req_id`/`_rebind_depth_req_id`, the depth error branch (`reqId ==
    self._depth_req_id` in `_on_error`), `ui/watchlist_panel.py::set_depth_manager`/`on_depth_update`/
    `_depth_manager` (dead wiring — no caller), the `DEPTH` subscription tag (`ibkr/subscription_manager.py`),
    `tests/test_market_depth.py`, and the depth parts of `MainWindow._md_line_count` (the `depth` term) /
    `_guard_depth_budget` / `DEPTH_FEED_CAP`.
  - **Active Trader panel — whole (widened 2026-10-15, Q50 = YES):** the remainder of `ui/active_trader_panel.py`
    not already listed is removed too — the `ActiveTraderPanel` shell, the **`OrderEntryWidget`** in-app order
    ticket (Buy/Sell MKT + LMT/STP/Bracket controls, the live-orders gate, the confirmation step, `status_label`,
    the `order_place_requested` signal), its `header_bar`/`header_button`, and `set_symbol`/`set_last_price`/
    `last_price`. `MainWindow._on_order_place_requested` and every other ticket-only helper go with it, and
    **`ui/active_trader_panel.py` no longer exists** after D41. The **order machinery** those controls drove
    (`ibkr/orders.py`, `ibkr/validation.py`, the `validate_order()` gate, `bracket_order`, the kill switch) is
    **retained** (see "Scope — KEEP") because Portfolio's **Close / Close Group / Flatten All** and the
    **SL/TP dialogs** place orders through it.
  - **Persisted footprint data (Q49 = "delete"):** the **`footprint_cache` table + its rows are removed** from
    the user DB — the DDL leaves `data/db.py` (fresh DBs never create it) **and** an existing DB's
    `footprint_cache` table (with any rows) is dropped/deleted by a small migration. **Interpretation recorded
    (A69):** the owner's word was "delete"; the feature that owns the data is removed, so the table + rows go
    with it rather than being left as dead data. The one-line alternative ("delete rows only, keep the empty
    table") is recorded as **DG70**; the chosen default is the **full drop** (the whole table).
- **Scope — KEEP (shared with features the owner did NOT remove — MUST NOT break):**
  - `ibkr/contracts.py::footprint_cache_key` + `::INDEX_PROXY` — **D39** uses them
    (`ui/ticker_session.py::TickerSession` burst-baseline key; `services/alarm_monitor.py`,
    `ui/alarm_dialog.py` — `INDEX_PROXY`). Keep both; only D36-only `resolve_footprint_contract` goes.
  - `services/md_line_guard.py::assess` + `MainWindow._guard_md_lines` + the RT/S0/watchlist terms of
    `_md_line_count` — **D38** news S0 lines use them (`ui/ticker_session.py::TickerSession` "S0 ticks" guard).
    Keep the guard; remove only the `depth` term from `_md_line_count` and delete `_guard_depth_budget` /
    `DEPTH_FEED_CAP`.
  - The **S0 generic-tick substrate** (`s0_register_many`/`s0_deregister_many`, `S0_TICKS` tag, the
    `tick_generic`/`tick_string`/`tick_news` signals and their `client.py` overrides) — **D38**
    news/dividends (`"292"`/`"456"`). Remove only the **`"225"` auction** need registration.
  - `services/volume_baseline.py` + the `volume_baseline` DB table — **D39**. Keep.
  - `data/db.py` — remove the `footprint_cache` DDL; keep `volume_baseline` (D39) and `yfinance_events_cache` (D38).
  - **Order execution / safety machinery — KEEP (retained order paths).** The in-app order ticket is removed,
    but the **order machinery it used is retained** because Portfolio's **Close / Close Group / Flatten All** and
    the **SL/TP dialogs** (`ui/stop_loss_target_dialog.py`) place orders **independently** through it:
    `ibkr/orders.py` (incl. `bracket_order`), `ibkr/validation.py` + the `validate_order()` gate, order-ID
    reservation (`id_manager`), the **kill switch** (`reqGlobalCancel` + per-ID cancels), the order registry /
    order-error handling, and the fail-fast port check (`config/settings.py::check_live_port`). **Do not delete the
    safety machinery** while removing the order-entry UI (DG69).
    **REVISED BY D45 (2026-10-25, incl. its later extension):** the close / close-group / flatten-all paths are now
    **removed too**, and so are the **kill switch** and the **SL/TP dialog** — this bullet is **superseded** as a
    whole. `ibkr/validation.py` + the `validate_order()` gate are **deleted**; `ibkr/orders.py` (builders +
    registry), `bracket_order`, order-ID reservation and the registry/order-error handling remain only as
    **unreferenced / inert** code with no app-placed orders to track (A80). **Nothing in the app builds, transmits
    or cancels an order.** The **fail-fast port check** (`config/settings.py::check_live_port`) is **retained** —
    it is not an order path.
  - **Retained order-path `ref_price` — KEEP with a NEW source (Plan-level detail).** `MainWindow` passed
    `ref_price=self.active_trader.last_price` to the MKT notional cap, and `last_price` was populated from the
    **DOM depth feed** (`_on_mkt_depth` → `active_trader.set_last_price(price)`). Both the panel and the DOM feed
    are now removed, so `ref_price` **MUST** be sourced from a **retained** price — the session's last price (the
    live RT-bar / aggregator last) or the `symbol → last_price` watchlist price map (the same source D27.5
    mandates for position market prices) — and **must keep resolving** for the retained order paths. The exact
    source is a **Plan-level detail** (DG71). **REVISED BY D45 (2026-10-25, incl. its later extension):** this
    clause is **moot** — no retained order path builds an order, so `ref_price` has **no consumer**; the
    `_ref_price_for` helper may be deleted with the order path or left unused (Plan's call).
  - **D18 / D21.13 — superseded, not deleted.** The right-dock model (D18) and the dock-title-bar / collapse
    behaviour (D21.13) assumed a **two-section Active Trader + Portfolio region**. With the Active Trader panel
    removed, the **right dock is a single Portfolio section**; the **40%-of-chart-area cap (D18/B2)** and the
    **dock header / collapse affordance** are **re-derived for a single section** (Plan-level detail, DG71). The
    affected D18/D21.13 clauses are marked **superseded by D41** with a reason; their outcomes that still apply
    (the dock is on-screen in full screen, non-zero width, clamped against the chart minimum) carry over to the
    Portfolio-only dock.
  - **D26 — safety KEPT; order-entry UI surface superseded.** D26's **safety requirements and machinery stay**
    (they guard the **retained** close/flatten/SL-TP order paths); only the **order-entry UI surface** D26
    hardened — the ticket and the DOM-ladder click-to-order path — goes. See the D26 entry's D41-interaction
    note.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D41.1 (no D36/D37/DOM-ladder/Active-Trader/order-entry control renders)** Given a loaded chart in the
    running app, Then no `Footprint`, `Classic`/`Tick count`, `Depth`, `IMB —`, or `AUC —` control exists in
    `ChartPanel` or its floating cluster; **no `DOM` toolbar button exists**; and **no Active Trader panel
    renders** — no ladder/book table, **no in-app order-entry (Buy/Sell MKT/LMT/STP/Bracket) control**, and no
    Active-Trader title-bar button; `ChartPanel`/`MainWindow` expose no `footprint_*`/`depth_*`/`auction_*`
    signal or attribute and no `active_trader` attribute. The zoom cluster, `Volume` toggle and every other
    **retained** control are unchanged, and the **Portfolio section** still renders — **REVISED BY D45
    (2026-10-25, incl. its later extension):** it is **view-only**, i.e. **no** Close / Close Group / Flatten All
    control exists, **and no SL/TP dialog or entry point exists either** (both removed; see `AC-D45.6`).
  - **AC-D41.2 (no D36/D37/DOM-ladder request is ever issued)** Given any symbol/timeframe load and any control
    interaction while connected, Then the app issues **zero** `reqHistoricalTicks`/`reqTickByTickData`, **zero**
    `reqMktDepth`/`cancelMktDepth` of any kind (heatmap or ladder), and **zero** `reqMktData` with generic
    **`"225"`** (auction). (D38's S0 `"292"`/`"456"` lines and D39's `reqMatchingSymbols`/burst path are
    unaffected.)
  - **AC-D41.3 (D36/D37/DOM-ladder + `ui/active_trader_panel.py` modules/tests are gone; no dangling import)**
    Given the repository after the change, Then `ui/footprint_item.py`, `ui/depth_heatmap_item.py`,
    `services/footprint_service.py`, `services/depth_heatmap.py`, `data/footprint_cache.py`,
    `ibkr/tick_history.py`, `ibkr/market_depth.py`, `ibkr/order_book.py`, **`ui/active_trader_panel.py`**,
    `tests/test_d36_footprint.py`, `tests/test_d37_microstructure.py` and `tests/test_market_depth.py` no longer
    exist, and no remaining production or test module imports them or references `FootprintItem`/
    `DepthHeatmapItem`/`FootprintService`/`DepthHeatmapService`/`TickHistoryManager`/`resolve_footprint_contract`/
    `DEPTH_HEATMAP`/`MarketDepthManager`/`OrderBook`/`ActiveTraderPanel`/`OrderEntryWidget`.
  - **AC-D41.4 (shared substrate + retained order machinery intact)** Given the change, Then the **shared
    substrate for the kept D38/D39 and the D27–D28/chart paths stays intact** — the D38 news digest + dividend
    markers and the D39 volume-burst alerts + symbol search still work and their tests stay green;
    `footprint_cache_key`, `INDEX_PROXY`, `md_line_guard.assess`, `S0_TICKS` and `volume_baseline` all remain and
    remain exercised by their tests — **and** the **retained order machinery** still functions: `ibkr/orders.py`,
    `ibkr/validation.py`/`validate_order()`, `bracket_order` side-correctness, order-ID reservation, the kill
    switch and the fail-fast port check are present and exercised; the retained order paths (**Close / Close
    Group / Flatten All**, SL/TP dialogs) still build and validate orders with a **resolving `ref_price`**.
    **REVISED BY D45 (2026-10-25, incl. its later extension):** **no** order-related surface is retained — the
    kill switch and the SL/TP dialog are **removed too**, so the app builds, transmits and cancels **nothing**; the
    `ref_price` clause is **moot** because no UI path builds an order and `ibkr/validation.py` is deleted. The D38
    **dividend/event-marker** half and the D39 substrate remain in force.
  - **AC-D41.5 (app starts and charts normally; suite green)** Given the change, Then the app launches, loads
    and renders a chart (candles + volume), and the full offscreen suite (`QT_QPA_PLATFORM=offscreen`) is green
    with no D1–D35/D38–D40 criterion regressed.
  - **AC-D41.6 (history preserved)** Given `requirements.md`, Then the `### D36` and `### D37` sections and
    `AC-D36.*`/`AC-D37.*` remain in the file, each carrying an explicit **`SUPERSEDED BY D41`** marker (per
    DOC-4); the affected `D18`/`D21.13` clauses carry an explicit **superseded-by-D41** note with a reason; and
    the Existing Repository marker sentence + Current Tech Stack are unchanged.
  - **AC-D41.7 (right dock is Portfolio-only; D18/D21.13 re-derived)** Given the running app, Then the right
    dock contains **only the Portfolio section** (no Active Trader panel/ladder/ticket), is **fully visible in
    full screen** with a **non-zero width**, and remains **clamped against the chart minimum**; its **width
    cap** and its **header / collapse affordance** are **re-derived for the single section** (not the old
    two-section Active-Trader+Portfolio model). (Measurable: no Active Trader widget exists in the right dock;
    the Portfolio dock satisfies the surviving D18 visibility/clamp assertions; the cap and header are the
    re-derived single-section values, documented by Plan.)
- **Edge Cases:** the **DOM ladder is removed too** (Q48) — the `DOM` button, `_subscribe_dom`, `_on_mkt_depth`,
  `MarketDepthManager` and the ladder/book tables all go, so **ESC-039** (ladder `SMART` + `isSmartDepth=False`)
  becomes **moot** (no ladder request remains); the **entire Active Trader panel — including the order-entry
  widget — is removed** (Q50), so `ui/active_trader_panel.py` no longer exists and there is **no in-app order
  ticket**, while **D26's safety machinery stays** for the retained close/flatten/SL-TP order paths (DG69); the
  retained order path's `ref_price` comes from a **retained source** (session last price / watchlist price map)
  — Plan-level detail (DG71); the **right dock is Portfolio-only** and the `D18`/`D21.13` two-section clauses
  are **superseded by D41** (cap + header re-derived, DG71); D38/D39 sharing must not break; the persisted
  `footprint_cache` table + rows are **removed** (Q49, A69, DG70); `tests/test_d27_reconnect.py` drops both its
  D37 session-depth assertions **and** its DOM-depth assertions (keeping its RT/S0/watchlist reconnect/replay
  assertions); `tests/test_d38_events_news.py`'s D36 references are comment-only; the **order-entry tests**
  (`tests/test_order_entry_mkt.py`, `tests/test_order_validation.py`, and any `OrderEntryWidget`/`active_trader`
  reference in `tests/test_dock_d18_region.py` / `tests/test_right_dock_d21.py`) are **re-pointed at the retained
  machinery or removed with the widget** — they must not be deleted wholesale if they also guard the retained
  order paths; the `DOM` button's deletion changes the D19/D20 toolbar control set, so
  `tests/test_toolbar_scroll_d19.py` / `tests/test_toolbar_d20.py` geometry fixtures are re-checked;
  `services/volume_baseline.py` docstring references to the D36 key rule are comment-only.

### D42 — REQUIREMENTS resolutions: candle/volume overlap precedence (ESC-042) + RTH intraday history depth / RTH-empty trading day (ESC-038) — 2026-10-15
- **Area:** `ui/candlestick_item.py::CandlestickItem._draw_candles` (body half-width + 4-px clamp),
  `ui/chart_panel.py::ChartPanel._clamp_half_width` / `::ChartPanel._refresh_candles` (volume width);
  `ibkr/market_data.py::TIMEFRAME_CONFIG`, `services/backfill_service.py::find_missing_spans`,
  `data/bar_cache.py` / `data/db.py` (cache key).
- **Status:** **NEW 2026-10-15 — two REQUIREMENTS-routed Code Reviewer escalations resolved by a requirements
  decision** (this section carries no code of its own). **D41 is built/reviewed/committed (`b48133d`) and is NOT
  reopened.** The resolutions **supersede** the *unconditional* wording of `AC-D6.4` and the *"gap remains
  positive"* wording of `AC-D7.1` + the D7 dense-view edge case, and **extend** `AC-D16.8`/`AC-D16.9` to **both**
  session modes. **Both owner confirmations are ANSWERED (2026-10-15): Q51 = confirmed** (a **zero** gap is
  acceptable at the limit — no criteria change) and **Q52 = ETH included** (the floor and the present-but-empty
  rule now cover `ext_hours=True` too — a recorded **supersession** of the RTH-only default). D1–D41 are otherwise
  unchanged; the D6/D7/D9/D16 criteria are revised **only** as stated, with every supersession recorded (never
  silent).
- **Rationale — why these are requirements, not build fixes:**
  - **ESC-042** is a genuine **contradiction inside `requirements.md`**: `AC-D6.4` required an **unconditional**
    "candle body `>= 4` device px at DPR 2", while `AC-D7.1` and the D7 dense-view edge case required the
    inter-bar gap to remain **positive**. Once the pitch falls below the 4-px floor (measured **3.83 device px**
    on a 192-bar SPY 5-min Ext-Hours view) both cannot hold, and the shipped code applies the floor
    **unconditionally** (`ui/candlestick_item.py::CandlestickItem._draw_candles`; volume reuses it via
    `ui/chart_panel.py::ChartPanel._clamp_half_width`), so bodies overlap and the gap goes negative. This is the
    **root cause of the still-open BUILD escalation ESC-041** (candle **and** volume overlap on a 5-min chart
    with Extended Hours ON). The overlap is **not** the removed footprint overlay and **survives D41** — it is a
    live defect independent of the D36/D37 removal.
  - **ESC-038** is an **unfiled behaviour**: with RTH selected an intraday chart shows only the current session.
    The cause is the **historical fetch window**, not `useRTH` (correctly `1` under RTH): `TIMEFRAME_CONFIG`
    gives `1 min` a `1 D` window and with `useRTH=1` one `D` is exactly **one** RTH session, while
    `services/backfill_service.py::find_missing_spans` anchors at the earliest cached day and never extends
    history **backwards**. Nothing written pinned the expected depth (now `AC-D16.8`), and the day-presence pass
    decides per-day presence **without** the current RTH/ETH mode, so a present-but-RTH-empty trading day is
    silently treated as filled (the same code path from the other side — BUILD escalation **ESC-037**).
- **Resolution D42.1 — candle/volume overlap precedence (ESC-042): the no-overlap guarantee wins.**
  The rendered candle body width is **capped at the inter-bar device-pixel pitch**; the D6 4-device-pixel
  legibility floor becomes **density-aware** (a *soft* floor that yields to the pitch when they collide).
  Precisely: `body = min( max(0.65 × pitch, F), pitch )`, where `pitch` is the inter-bar centre-to-centre
  distance and `F` is the D6 floor (`4` device px at DPR 2) — all measured in the **same pixel unit**. The
  **hard guarantee is `gap = pitch − body >= 0`** (bodies never overlap, at any density / timeframe / pane
  width / Ext-Hours setting); the gap is **positive whenever `pitch > F`**; at extreme density (`pitch <= F`)
  the floor has already yielded and the gap may be **`0`** (abutting bodies) — a **zero** gap is acceptable
  there, a **negative** gap is never. "Positive gap" at the limit therefore means `> 0` where the pitch admits
  it, with `>= 0` as the inviolable floor. **Volume width == price body width** (`AC-D9.1`/`AC-D9.2` unchanged;
  volume inherits the same capped `w`). See `AC-D6.4` (revised), `AC-D7.1` (revised), the D7 dense-view edge
  case, and the `AC-D9.2` note.
- **Resolution D42.2 — intraday history depth + present-but-empty day, for RTH **and** Ext-Hours (ESC-038 /
  ESC-037; ETH scope widened by Q52).** In **either** session mode — **RTH** (`extended_hours=False` →
  `useRTH=1`, window `09:30–16:00 ET`) or **ETH** (`extended_hours=True`, window `04:00–20:00 ET`) — each
  intraday timeframe (`1 min`…`4 hours`) must load **>= 30 trading sessions before the current session**
  (`AC-D16.8`, owner-required via Q47; **extended to ETH by Q52**), where a **session is counted only if the
  series holds >= 1 bar inside the current mode's session window** for that day — so **all five** intraday windows
  (calendar-day durations that yield ~1 / 3–4 / 3–4 / 7 / ~21 sessions) fall short and must extend history
  **backwards** (chained, paced). A trading day present in the cache with **no bar inside the current mode's
  window** is a **missing span**, not a filled day, and is reported by a **mode-aware** day-presence pass with a
  **mode-aware cache** (`AC-D16.9`) — the requirements side of BUILD **ESC-037**. **Mode isolation:** the two
  modes share one floor but must not cross-contaminate (a day with only pre/post ETH bars is RTH-missing but
  ETH-present; a day with only RTH bars is ETH-present). This **reconciles ESC-038 with `AC-D16.8`**: the "one
  session" symptom is a **shortfall against `AC-D16.8`** (not an unfiled behaviour), and the fetch-window
  strategy that delivers the floor is a **Plan/Build** matter (DG65/DG72). **Supersession (Q52, 2026-10-15):**
  the RTH-only scoping in the earlier D42 default is **superseded** — ETH is now in scope (recorded, not
  silent).
- **Correction record (artifacts that must change — Task Manager / Build / Code Reviewer):**
  - **Task Manager:** the D42 work items are (a) the **density-aware body/volume cap** (ESC-042 → unblocks
    ESC-041) and (b) the **intraday history-depth + mode-aware day-presence** change **for both RTH and ETH**
    (ESC-038/ESC-037, ETH scope per Q52). Write them against `AC-D6.4`/`AC-D7.1`/`AC-D9.2` (revised) and
    `AC-D16.8`/`AC-D16.9` (both modes).
  - **Build:** apply the cap in `ui/candlestick_item.py::CandlestickItem._draw_candles` **and** in the volume
    width path (`ui/chart_panel.py::ChartPanel._clamp_half_width` / `::ChartPanel._refresh_candles` /
    `::ChartPanel._refresh_live_bar`); make `services/backfill_service.py::find_missing_spans` (and the bar-level
    pass) **mode-aware** — the day-presence pass must decide presence against the **current mode's session
    window** (`ext_hours`), not the calendar day's mere presence (`present_days = {_et_date(ts)}` is currently
    mode-blind); make the bar cache/key **mode-aware** (`data/bar_cache.py` / `data/db.py`, keyed on
    symbol+timeframe+mode) so RTH and ETH do not cross-contaminate; **correct (do not merely weaken)** the tests
    that enshrine the old rule — `tests/test_candle_spacing.py` (a string-presence check that never renders) and
    `tests/test_volume_width.py` (asserts body==volume and ~4 px but never relates width to pitch) — and add a
    rendered-geometry guard (`body <= pitch`, measured from the `QPicture` bbox) plus
    `find_missing_spans(..., ext_hours=False)` **and** `find_missing_spans(..., ext_hours=True)` RED→GREEN cases
    (the ETH case: a day with no bar inside `04:00–20:00 ET` is a missing ETH span; a day with only pre/post ETH
    bars is RTH-missing but ETH-present).
  - **Code Reviewer:** on the ESC-041 re-check, verify against the **revised** `AC-D6.4`/`AC-D7.1` (a contiguous
    zero-gap pixel run at pitch ~ 3.83 px is the failure); on **ESC-037**, verify `AC-D16.9` **in both modes**
    (the RTH-missing / ETH-present split and the reverse); **ESC-038** is resolved by `AC-D16.8`/`AC-D16.9`
    (requirements side) for both modes.
- **Edge Cases:** extreme density (`pitch <= F`) → bodies abut, gap `0`, **never** overlap (a **zero** gap is
  not a defect at this density; a **negative** gap always is); `1 day` is **not** covered by the 30-session
  floor (`AC-D16.8`); genuine closures stay empty (`AC-D16.3` unchanged); a **trading halt / no-bar day**
  that IBKR genuinely has no bars for is re-probed and its shortfall surfaced (`AC-D16.4`) — never fabricated;
  a mode switch (Ext Hours ON ↔ OFF) must not leave a hole and must not read the other mode's bars as coverage
  (`AC-D16.9`) — **in either direction** (RTH-only bars are not ETH coverage; pre/post-only bars are not RTH
  coverage); under **ETH** the present-but-empty rule uses the `04:00–20:00 ET` window, not the RTH window
  (`AC-D16.9`, Q52).

### D43 — REQUIREMENTS resolution: D27.9 aggregator priming for the coarse intraday timeframes (ESC-036 second clause) — 2026-10-16
- **Area:** `ui/ticker_session.py::TickerSession.prime_aggregator` (the priming request shape);
  `data/bar_aggregator.py::BarAggregator.period_start` / `::TIMEFRAME_SECONDS`; `ibkr/market_data.py::TIMEFRAME_CONFIG`;
  `tests/test_d27_aggregator_priming.py`.
- **Status:** **NEW 2026-10-16 — a REQUIREMENTS-routed decision** (this section carries no code of its own).
  **D41/D42 are delivered, reviewed and committed and are NOT reopened.** **ESC-036** has two clauses: the
  **first** (an IBKR request shape — `bar_size='5 secs'` + `duration='7200 S'` → TWS error 321) is **BUILD**
  work already in flight (**P2-T30**: clamp the 5-sec priming span into `[60 S, 3600 S]`); the **second** is
  the **requirements question decided here** — **D27.9 mandated priming with "trailing 5-second history"**, which
  is **unsatisfiable** for the coarse timeframes. This section **supersedes D27.9's "trailing 5-second history"
  wording** and **revises `AC-D27.9`** (recorded, never silent).
- **Rationale — why this is a requirements decision, not a build fix:**
  - The priming's purpose is to seed the **forming** candle's OHLCV over the **elapsed portion of the current
    period** so it is not fabricated from the first live tick (`D27.1` re-applies the aggregator's forming bar
    over the historical series, so the forming bar's OHLCV comes from the aggregator). For **`4 hours`**
    (period 14400 s) and **`1 day`** (period 86400 s) the elapsed span exceeds IBKR's **`3600 S` ceiling for
    `5 secs` bars**, so **no 5-second request can cover the period** — the request the code built
    (`bar_size='5 secs'`, `duration='7200 S'`) is exactly the one IBKR rejects with **error 321**
    (`Aggregator priming request 144 failed [321]`). D27.9's wording therefore cannot be met as written.
  - The consequence today is that `4 hours`/`1 day` loads are **unprimed** (`on_historical_error` fails open),
    so the forming 4h/daily candle's open/high/low/volume are built **only from live ticks** — the fabricated
    bar D27.9 exists to prevent — and the warning is emitted on **every** load.
- **Resolution D43.1 — prime with a bar size chosen for the elapsed forming-period span (the affected
  timeframe set is `4 hours` and `1 day`).** The priming request's bar size is selected from the elapsed span:
  - **`5 secs`** when the elapsed span is **<= 3600 S** — the **`1 min`**, **`5 mins`**, **`15 mins`** and
    **`1 hour`** timeframes (their spans are up to 60 / 300 / 900 / 3600 S, all within IBKR's `5 secs` ceiling);
    `duration` = the elapsed span clamped into **`[60 S, 3600 S]`**.
  - **`1 min`** when the elapsed span **exceeds 3600 S** — the **`4 hours`** and **`1 day`** timeframes;
    `duration` = the elapsed span clamped into **`[60 S, 1 D]`** (`1 min` is IBKR-valid up to a `1 D` duration;
    a 4h span is up to 14400 S and a daily span is up to 86399 S, both within `1 D`).
  This keeps a **partial current-period seed** (the whole elapsed period is covered by the `1 min` bars) and
  therefore **meets `AC-D27.9` on every selectable timeframe**, including `4 hours`/`1 day`. Bars returned whose
  `ts` precedes the current period's start must **not** fabricate a completed previous-period candle (the same
  replay guard the first-clause clamp needs).
  - **Alternative considered and NOT adopted — "seed from the historical partial bar".** The normal historical
    load could in principle seed the aggregator's forming state instead of a separate priming request (zero
    extra requests). It is **rejected as the normative target** because it depends on IBKR returning a
    **partial current-period bar** as the last bar of the `4 hours`/`1 day` historical request — a behaviour
    that is **unverified** here (no live TWS in the test environment) and would silently degrade to a fabricated
    bar if IBKR returns only completed bars. The explicit `1 min` priming request does not depend on that.
  - **Alternative considered and NOT adopted — "drop priming for the coarse timeframes".** It would stop the
    error-321 warning but leave the forming 4h/daily candle **fabricated from live ticks** (the very defect
    D27.9 addresses), so it does **not** meet the escalation's stated expectation that `AC-D27.9` hold on
    every timeframe.
- **Correction record (artifacts that must change — Task Manager / Build / Code Reviewer):**
  - **Task Manager:** the priming **bar-size selection** (the coarse-timeframe branch) is **NOT delivered by
    P2-T30** (which only clamps the `5 secs` span into `[60 S, 3600 S]` and keeps `bar_size='5 secs'` for
    **all** timeframes) — write a **FOLLOW-UP** task against **D27.9 (revised)** / **`AC-D27.9` (revised)**
    covering `4 hours`/`1 day`. **P2-T30's `AC1` and `P2-T30-T11`** currently assert a **`5 secs`/`3600 S**
    request for the 4h/1d loads and become **stale once the follow-up lands** — revise them (or let the
    follow-up's tests supersede them) so the suite does not encode the superseded behaviour.
  - **Build:** in `ui/ticker_session.py::TickerSession.prime_aggregator`, select `bar_size` from the elapsed
    span (`5 secs` when `span_s <= 3600`, else `1 min`) and clamp `duration` into the selected bar size's
    range (`[60 S, 3600 S]` / `[60 S, 1 D]`); keep the existing fail-open / 15 s-backstop / replay-guard
    behaviour. **Correct (do not merely weaken)** the priming tests — `tests/test_d27_aggregator_priming.py`
    (its module docstring still says "trailing 5-sec history"; `test_d27_9_prime_span_bounded` must assert the
    accepted `1 min`/`1 D`-bounded combination for `1 day`, not the enshrined `5 secs`/`7200 S`) — and add a
    RED→GREEN case proving the `4 hours`/`1 day` loads issue a **`1 min`** request whose duration is inside
    `[60 S, 1 D]`.
  - **Code Reviewer:** on the ESC-036 re-check, verify **both** clauses — the fine timeframes issue a
    `5 secs` request with `duration` in `[60 S, 3600 S]` **and** `4 hours`/`1 day` issue a `1 min` request
    with `duration` in `[60 S, 1 D]` — and that the forming 4h/daily candle reflects the primed history
    (not the first live tick) once priming completes.
- **Edge Cases:** a load **at a period boundary** (`span_s < 5`) primes nothing (unchanged); a load in the
  **first minute** of a coarse period floors the duration to `60 S` (the `[60 S, 1 D]` minimum) — the replay
  guard must keep such a bar from fabricating the previous period; a **pacing-exhausted** prime still
  **fails open** (attaches the live feed unprimed — `D28.3`, unchanged); a priming request that never answers
  still trips the **15 s backstop** (unchanged); `1 day` uses the **ET-anchored** period grid (`D27.8`), so a
  `1 min` bar at the ET-midnight boundary belongs to the new daily period.

### D44 — Collapsed Watchlist becomes a thin vertical bar that expands to the full panel (NEW FEATURE) — OWNER-REQUESTED 2026-10-16

- **Area:** `ui/watchlist_panel.py` (`WatchlistPanel.header_bar` / `header_button` / `_on_header_toggled` /
  `set_collapsed` / `toggle_collapsed` / `is_collapsed`; the new collapsed-bar widget), `ui/dock_layout.py`
  (`WATCHLIST_MIN_WIDTH`, `plan_dock_widths`), `ui/main_window.py` (`setTitleBarWidget(self.watchlist_panel.header_bar)`,
  `LeftDockWidgetArea`, `_apply_dock_widths`), `ui/visual_conventions.py` (`set_button_active`).
- **Status:** **NEW 2026-10-16 — OWNER-REQUESTED; scope recorded and the `## Non-Goals` explicitly revised
  (dated 2026-10-16). No blocking question: the three owner-flagged choices (bar width, persistence, `+`
  reachability) are decided with recorded defaults (A75–A77) and surfaced to the owner as **Q54** (confirmation
  requested; non-blocking).** **D1–D43 are NOT reopened.** D44 **revises** the collapsed-appearance clauses of
  D21.11 (`AC-D21.11.2`/`AC-D21.11.3`) and the 150px-minimum clause of D13/D17 (`AC-D13.1`/`AC-D17.2`).
- **Reported (verbatim intent):** "When the watchlist is collapsed by clicking on the Watchlist button, it
  should become a thin bar on the left side. When the user clicks on the thin panel, it should open up into a
  full panel like before. Keep the colour scheme consistent with the app and make it look like a panel."
- **Owner clarification (explicit):** the mockup showed the bar as a **white rounded pill** — that was
  **mockup-tool styling only, NOT a colour choice**. The bar must use the **app's own palette**.
- **Observed in repository (validated 2026-10-16 against source; graphify used for the initial map, source is
  authoritative):**
  - **The collapse already exists (D21.11).** `ui/watchlist_panel.py::WatchlistPanel` builds a 28px `header_bar`
    (`setObjectName("WatchlistHeader")`, `background: #141822; border-bottom: 1px solid #232938`) holding
    `header_button = DiagonalStrikeButton("Watchlist")` (`setObjectName("WatchlistHeaderButton")`, checkable,
    checked by default). `header_button.toggled` → `_on_header_toggled(checked)` sets `self._collapsed = not
    visible` and does `self.body.setVisible(visible)`. The public API is `set_collapsed()` / `toggle_collapsed()`
    / `is_collapsed()`. **Today collapsed = the horizontal header strip stays, the table hides, and the dock
    keeps its ~220px width.**
  - **The header bar IS the dock's title bar.** `ui/main_window.py` calls
    `self.watchlist_dock.setTitleBarWidget(self.watchlist_panel.header_bar)` and the dock lives in
    `Qt.DockWidgetArea.LeftDockWidgetArea`.
  - **The blocker to a thin bar is the width clamp.** `ui/dock_layout.py` sets `WATCHLIST_MIN_WIDTH = 150` and
    `plan_dock_widths()` clamps **unconditionally** — `left = max(WATCHLIST_MIN_WIDTH, min(int(requested_left),
    left_max))`. `MainWindow._apply_dock_widths` is the single apply entry point and is wired to **both**
    `resizeEvent` and the dock-drag hook, so a ~30px bar is snapped back to 150px on the next resize or drag
    unless the layout rules learn about a collapsed width.
  - **Cross-module invariant:** `CHART_MIN_WIDTH` is duplicated between `ui/dock_layout.py` and
    `ui/watchlist_panel.py` (`ui/watchlist_panel.py` binds `CHART_MIN_WIDTH = dock_layout.CHART_MIN_WIDTH`) and
    must stay equal (`ui/dock_layout.py` documents this).
  - **Palette to use:** background `#141822`, text `#cbd5e1`, border `#232938` — the same family as the existing
    `WatchlistHeader` strip and the portfolio's `AccountSummaryHeaderButton`. Hover/pressed use the established
    `set_button_active()` convention in `ui/visual_conventions.py`, not a hand-rolled highlight.
  - **Qt cannot rotate a `QPushButton`'s text**, so the vertical bar needs a small **custom widget with a
    `paintEvent`** drawing rotated text.
- **Requirements (final):**
  - **Collapsed form (owner-flagged #1 — decided A75):** while collapsed, the watchlist dock renders a **thin
    vertical bar** of width `WATCHLIST_COLLAPSED_WIDTH = 30px` (within the owner's ~28–32px range; 30px is
    ≥ the 28px header height and leaves room for the rotated label + 1px borders without clipping). The bar shows
    the **rotated** text `WATCHLIST` (reading bottom-to-top, i.e. rotated 90° counter-clockwise) in the **app
    palette** (`#141822` background, `#cbd5e1` text, `#232938` border); it must **look like a panel** (a bounded,
    filled bar), **not** a white pill.
  - **Expand on click:** clicking **anywhere on the thin bar** (or its rotated label) expands the watchlist to
    its **previous** width — the width the dock held immediately before it was collapsed (the layout already
    tracks `MainWindow._watchlist_width`), re-clamped to the current cap/min rules for the expanded state.
    The restored value is the **tracked** `MainWindow._watchlist_width`, which equals `clamp(W)` **exactly** (it
    is never assigned while collapsed); the **rendered** dock width is a Qt layout result checked **tolerantly**
    (floor/cap/collapsed bounds) — see `AC-D44.2` (restated 2026-10-16 per ESC-057).
  - **Collapse from the header button (as today):** in the expanded state the retained "Watchlist" header button
    collapses the panel (unchanged behaviour); collapsing switches the dock to the thin bar.
  - **Header strip, `+` (D22.1) and column-header row while collapsed (owner-flagged #3 — decided A77):** the
    **horizontal header strip, the `+` add button (D22.1) and the table's column-header row are all hidden** while
    collapsed — they belong to the expanded panel and **return on expand**. The thin bar's **only** interactive
    element is the expand affordance. (The `+` remains reachable the instant the user expands, so no affordance is
    lost; a ~30px bar cannot hold a horizontal `+` plus a rotated label legibly.)
  - **Persistence across restarts (owner-flagged #2 — decided A76):** the collapsed/expanded state is **NOT
    persisted** — the app starts **expanded** every launch, consistent with the existing D21.11 collapse (which
    is not persisted) and the D10/A36 precedent that UI show/hide toggles are not persisted. The `WatchlistPanel`
    `QSettings` is **not** used for collapse state.
  - **Layout must honour the collapsed width (the core new requirement):** while collapsed, the watchlist dock's
    width is governed by `WATCHLIST_COLLAPSED_WIDTH`, **not** by `WATCHLIST_MIN_WIDTH`; `plan_dock_widths` (or
    `_apply_dock_widths`) must treat a collapsed watchlist as **fixed at the collapsed width** so a `resizeEvent`
    or a dock drag does **not** snap it back to 150px. The expanded-state minimum stays **150px**
    (`AC-D13.1`/`AC-D17.2` revised to say the 150px minimum applies to the **expanded** state). The
    `CHART_MIN_WIDTH` invariant is preserved in both states.
  - **Non-regression:** expanding restores the previous width; D14 double-click row-to-load, D21.5 column popup,
    D22 add/remove, the D13/D17 width model in the **expanded** state, and the D18/D41 right-dock model are
    unchanged.
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D44.1 (collapsed form — thin vertical bar)** Given a docked Watchlist is expanded, When the user
    collapses it (via the header button), Then the watchlist dock renders a **thin vertical bar** of width
    `WATCHLIST_COLLAPSED_WIDTH` (~30px, within 28–32px) in `LeftDockWidgetArea` showing the **rotated** text
    `WATCHLIST`, and the bar's background/border/text use the app palette (`#141822` / `#232938` / `#cbd5e1`),
    **not** white. (Measurable: `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`; a rotated-label widget
    exists; its rendered background/border colours match the app palette.)
  - **AC-D44.2 (click to expand — previous width restored)** Given the watchlist is collapsed to the thin bar,
    When the user clicks the bar, Then the watchlist expands to the **width it held immediately before
    collapsing** (the tracked previous width), re-clamped to the current expanded cap/min rules, and the full
    panel (header strip, table, `+`) is visible again. (Measurable: collapse from a known width W, expand, and
    assert the **tracked** width is restored exactly — `win._watchlist_width == clamp(W)`, which holds **by
    construction** (`_watchlist_width` is never assigned while collapsed, and `_apply_dock_widths` always stores
    the clamped value) — **plus** a **tolerant** check on the **rendered** dock width (`watchlist_dock.width()`
    is `>= WATCHLIST_MIN_WIDTH`, `<= watchlist_max_width(...)`, and `> WATCHLIST_COLLAPSED_WIDTH`), because the
    rendered width is a Qt layout result and is **not** required to echo `clamp(W)` exactly.) *(Restated
    2026-10-16 per ESC-057 — the former rendered-width exact-equality wording is superseded: the recorded
    300→314 non-exact restore was not reproducible, and no requirement depends on a rendered-width echo.)*
  - **AC-D44.3 (click to collapse from the header button — unchanged)** Given the watchlist is expanded, When
    the user clicks the retained "Watchlist" header button, Then the panel collapses to the thin bar (the
    existing D21.11 toggle path). (Measurable: `is_collapsed()` is True and the dock width is the collapsed
    width.)
  - **AC-D44.4 (header strip / `+` / column-header row hidden while collapsed)** Given the watchlist is
    collapsed, Then the **horizontal header strip, the `+` add button (D22.1) and the table's column-header row
    are not visible**; When the user expands, Then they are visible again. (Measurable: their `isVisible()` is
    False while collapsed and True while expanded.)
  - **AC-D44.5 (layout honours the collapsed width — the core fix)** Given the watchlist is collapsed, When a
    window `resizeEvent` fires **or** the dock splitter is dragged, Then the watchlist dock **stays at the
    collapsed width** and is **not** snapped back to `WATCHLIST_MIN_WIDTH` (150px). (Measurable: after driving a
    resize/drag with the watchlist collapsed, `watchlist_dock.width() == WATCHLIST_COLLAPSED_WIDTH`.)
  - **AC-D44.6 (palette + hover/pressed convention)** Given the thin bar, Then its colours come from the app
    palette (`#141822` / `#232938` / `#cbd5e1`) and its hover/pressed feedback uses the established
    `ui/visual_conventions.py::set_button_active` convention (no hand-rolled highlight). (Measurable: the
    hover/active style differs from the idle style and is applied via the shared helper.)
  - **AC-D44.7 (collapse state not persisted)** Given the user leaves the app with the watchlist collapsed, When
    the app is restarted, Then the watchlist is **expanded** (the collapsed state is not persisted); no
    `QSettings` key is written for collapse state. (Measurable: after a restart the dock is expanded; no
    collapse-state key exists in `QSettings`.)
  - **AC-D44.8 (regression guard — pre-fix RED)** Given the fix, Then a regression check exists that **fails on
    the pre-fix tree** and passes after: collapsing the watchlist must yield the **collapsed width** (not the
    pre-fix ~220px dock width / 150px minimum) and that width must **survive a simulated resize/drag**; and the
    existing D13/D17 width suites and the D21.11 collapse behaviour remain green (or are updated in lockstep
    where the 150px-minimum clause now applies to the expanded state only — never left contradicting D44).
    (Measurable: the new guard is RED at the pre-fix commit and GREEN after; the expanded-state width suites
    pass unchanged.)
- **Supersession / revision record (recorded, not silent):**
  - **`AC-D21.11.2` / `AC-D21.11.3` — REVISED by D44.** Their collapsed-appearance clause ("the collapsed state
    still shows the button", with the `VIS-D21.1` diagonal strike-through on the retained button) is
    **superseded for the collapsed state**: the collapsed watchlist now shows a **thin vertical bar with rotated
    text**, not a struck-through horizontal header button. `VIS-D21.1` still applies to any genuinely
    hidden/off **button** state elsewhere (D21.12 volume, D21.13 portfolio); it is **not** the collapsed
    watchlist indicator. `AC-D21.11.1` (single "Watchlist" label, duplicate dock title deleted) is unchanged.
  - **`AC-D21.11` edge case "collapsed-width geometry" — now specified** by `AC-D44.1`/`AC-D44.5`.
  - **`AC-D13.1` / `AC-D17.2` — REVISED by D44.** Their **150px minimum** applies to the **expanded** watchlist
    only; while collapsed the width is `WATCHLIST_COLLAPSED_WIDTH` (~30px). `AC-D13.2`/`AC-D13.3`/
    `AC-D17.1`/`AC-D17.3`–`AC-D17.6` (cap, persistence, drag-enforcement, re-clamp) are unchanged **for the
    expanded state**.
  - **`AC-D22.1` (the `+` on the header strip) — unchanged in the expanded state**; `AC-D44.4` records that the
    `+` (and the column-header row) are hidden while collapsed.
- **Edge Cases:** collapse from the **minimum** width (150px) → expand restores 150px; collapse from the **cap**
  → expand restores the cap (re-clamped); a **window resize while collapsed** must not change the collapsed
  width (`AC-D44.5`); a **dock drag while collapsed** must not expand it; **floating** watchlist (D13) —
  collapse behaviour in a floating dock is a Plan-level detail but the bar must still be clickable to expand;
  **IBKR disconnected** — collapse/expand is a pure UI state and works disconnected; **empty watchlist** —
  collapse/expand still works; **`1 day`/any symbol** — the bar is symbol-independent; **first launch** — the
  watchlist starts **expanded** (A76); the `CHART_MIN_WIDTH` invariant holds in both states; a very narrow
  window where `WATCHLIST_COLLAPSED_WIDTH` still fits.
- **Correction record (artifacts that must change — Plan / Task Manager / Build / Code Reviewer):**
  - **Plan:** choose the collapsed-bar **mechanism** — a small custom widget with a `paintEvent` drawing rotated
    text, and how the dock's **title-bar widget** presents the bar while collapsed (`setTitleBarWidget` swaps to
    the bar, or the header widget reorients) — keeping the dock movable (DG37). Re-derive the collapsed-aware
    width path in `plan_dock_widths` / `_apply_dock_widths`.
  - **Build:** add `WATCHLIST_COLLAPSED_WIDTH` to `ui/dock_layout.py` (and keep `CHART_MIN_WIDTH` in lockstep
    with `ui/watchlist_panel.py`); make the collapsed width honoured by the single apply entry point; add the
    rotated-text bar widget in the app palette; wire click-to-expand to restore the tracked previous width; hide
    the header strip / `+` / column-header row while collapsed.
  - **Code Reviewer:** independently verify the collapsed width **survives** a resize/drag (the core defect
    class), that the palette matches the app (no white pill), and that the **expanded** D13/D17 width criteria
    are unaffected.

### D45 — Remove the News Digest dock (+ the `View` menubar), the Trade Context Menu, the **Kill switch** and the **SL/TP dialog** — the app has **zero order interaction** afterwards — OWNER-REQUESTED 2026-10-25

- **Area (REMOVE):** `ui/news_digest_dock.py` (`NewsDigestDock`), `ibkr/news.py` (`NewsManager`), the `View`
  menubar in `ui/main_window.py` (`menuBar()` / `view_menu` / `_on_news_digest_visibility` /
  `self.news_digest_dock`), the news `"292"` fan-out in `ui/ticker_session.py`; `ui/trade_context_menu.py`
  (`TradeContextMenu`), `ibkr/validation.py` (`validate_order`), the Portfolio close path in
  `ui/active_portfolio_panel.py` (`position_close_requested` / `group_close_requested` /
  `flatten_all_requested`, `_on_flatten_all`, the context-menu policy and its handler) and its three
  `MainWindow` handlers (`_on_portfolio_close_position`, `_on_portfolio_close_group`,
  `_on_portfolio_flatten_all`, `_close_position_by_id`); **`ui/stop_loss_target_dialog.py`**
  (`StopLossTargetDialog`), the Portfolio SL/TP chain (`position_sltp_changed` / `group_sltp_changed`,
  `_on_set_sltp`, `_on_sltp_confirmed`, `update_position_sltp`, `update_group_sltp`) and the two
  `MainWindow` handlers (`_on_portfolio_sltp_changed`, `_on_portfolio_group_sltp_changed`) plus the table's
  **Stop / Target columns**; the **Kill switch** (`kill_btn`, `_on_kill_switch_clicked`, `_kill_switch`, the
  `reqGlobalCancel()` + per-ID `cancelOrder()` calls); the named test files/cases; and three docs.
- **Status:** **NEW / OWNER-REQUESTED 2026-10-25 — full removal; no blocking question (lite lane: every open
  default is recorded as A79–A90).** **D1–D44 are NOT reopened.** D45 **supersedes** `AC-D38.2`/`AC-D38.3`,
  **revises** `AC-D38.6` and the portfolio-close clauses of `AC-D41.1`/`AC-D41.4`, makes the D26 order-entry
  clauses **moot**, and — after the **2026-10-25 (later) extension** — makes **`AC-D26.3` moot** and
  **supersedes `AC-D26.8`**.
  **Extension (owner-requested, 2026-10-25 later):** verbatim *"remove: Kill switch — it only cancels orders,
  never places one / SL-TP dialog — local-only targets, never transmitted"*, given in the context of *"i dont
  need to place any order from the app"*. The intent is **no order interaction of any kind** — not placing, not
  cancelling, not closing. **Nothing is retained on the order side** except observation; the "Scope — KEEP" list
  below contains **no order-related surface**.
  **No `## Non-Goals` bullet needs revision:** D45 **removes** features and adds none, and the existing
  order-placement Non-Goal only becomes **vacuous** (there is no order interaction left to govern).
- **Reported (verbatim, first request):** *"I want both removed."* — referring to the two components the owner had
  asked about and then confirmed for removal: (1) the **News Digest Dock** (`ui/news_digest_dock.py`, D38a.2);
  (2) the **Trade Context Menu** (`ui/trade_context_menu.py`).
- **Reported (verbatim, later extension):** *"remove: Kill switch — it only cancels orders, never places one /
  SL-TP dialog — local-only targets, never transmitted"*; context: *"i dont need to place any order from the
  app"*.
- **Owner confirmations (explicit, 2026-10-25 — all confirmed):**
  - **`ibkr/news.py` — DELETE.** Its only consumer is the digest and its tests.
  - **The `View` menubar — fine to lose.** It exists **solely** for `View → News Digest` (`Ctrl+Shift+N`); the
    app had **no menubar** before D38 and returns to **none**.
  - **Generic tick `"292"` — REMOVE.** The **dividend tick `"456"` MUST STAY** — the same `s0_register`
    mechanism, but it feeds the chart's **dividend event markers**, which are **staying**.
  - **Portfolio becomes view-only.** Closes happen **in TWS directly**. **No replacement UI.**
  - **Kill switch — REMOVE (later extension).** The owner's reason is exact: it **only cancels**, it never
    places. With no in-app order placement, a cancel-only control is out of scope for the app.
  - **SL/TP dialog — REMOVE (later extension).** The owner's reason is exact: its targets are **local-only and
    never transmitted** — they protect nothing, so the dialog is a dead setter.
  - **Docs** (`USAGE.txt`, `usage.md`, `docs/codebase-map.md`) are cleaned **in the same batch**.
- **Observed in repository (validated 2026-10-25 against source; the invoking session's inventory, spot-checked
  here — source is authoritative). Line numbers are indicative; resolve by symbol:**
  - **Group A — News Digest (≈8 files)**
    - delete `ui/news_digest_dock.py`, `ibkr/news.py`.
    - `ui/main_window.py`: the import, `self.news_digest_dock` (479–493), `_on_news_digest_visibility`
      (2757–2763), the `menuBar()`/`view_menu` block (486–491), the `NewsManager` use (529).
    - `ui/ticker_session.py`: the news `"292"` fan-out (≈176, 526) — **leave dividends `"456"` / tick 59 /
      `_dividend_info` / `dividend_updated` untouched.**
    - `tests/test_d38_events_news.py`: remove the digest + `NewsManager` cases (≈149, 170, 190, 482–493);
      **keep the event-marker cases.**
    - `tests/test_dock_d18_region.py:147`: drop the `objectName() != "NewsDigest"` filter.
    - `USAGE.txt:140` (the `View → News Digest` section), `docs/codebase-map.md:45`.
  - **Group B — Trade Context Menu + the whole order path + the SL/TP dialog (≈15 files)**
    - delete `ui/trade_context_menu.py`, `ibkr/validation.py`, **`ui/stop_loss_target_dialog.py`**
      (`StopLossTargetDialog`, 180 L; its `set_sltp_action` is the **only** entry point that ever opened it).
    - `ui/active_portfolio_panel.py`: the imports (25 `StopLossTargetDialog`, 26 `TradeContextMenu`), the menu
      construction (155–160) and the context-menu policy + handler (144–145, 370–373), the signals
      `position_close_requested` / `group_close_requested` / `flatten_all_requested` **and**
      `position_sltp_changed` / `group_sltp_changed` (42–51), `_on_flatten_all` (415–417),
      `_on_set_sltp` (375–389), `_on_sltp_confirmed` (391–396), `update_position_sltp` (249–260),
      `update_group_sltp` (262–275), `self._sltp_dialog` (168), and the **Stop / Target table columns**
      (115–127: the table becomes **8 columns**; `_render_table` drops the two values and re-indexes the
      right-aligned set from `(1,2,4,5,6,7)` to `(1,2,4,5)`; the `RIGHT_DOCK_MIN_WIDTH` docstring's
      "10-column" wording is corrected).
    - `ui/main_window.py`: the 3 close connections (647–649), `_on_portfolio_close_position` (3366),
      `_on_portfolio_close_group` (3370), `_on_portfolio_flatten_all` (3381), `_close_position_by_id`
      (3394…), the `validate_order` import (37), **and** the two SL/TP connections (650–651) with
      `_on_portfolio_sltp_changed` (3342–3352) / `_on_portfolio_group_sltp_changed` (3354–3368) — the two
      `UPDATE positions SET stop_loss=…` / `UPDATE trade_groups SET stop_loss=…` statements die with them
      (the position **upsert** in `_persist_position` still writes both fields — unchanged).
    - tests: **delete** `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`,
      `tests/test_order_validation.py`, **`tests/test_sltp_honesty.py`** (both cases assert the deleted
      dialog's disclosure labels); **adjust** `tests/test_order_rejections.py`, `tests/test_d28_pacing.py`,
      **`tests/test_dock_d18_region.py`** (`:147` digest filter, `:176` close path, **`:177-178` the two SL/TP
      signals in the five-signal receiver loop → a three-signal loop**),
      **`tests/test_d27_position_id.py`** (remove `test_p2_t27_t31_sltp_persists_to_exactly_the_addressed_row`
      — its subject is the deleted `update_position_sltp → _on_portfolio_sltp_changed` row UPDATE; **keep** the
      rest, including the position-id AC2 case), and
      **`tests/test_d27_position_prices.py`** (Strategy/Group column indexes `8`/`9` → **`6`/`7`** after the two
      columns are dropped), plus `tests/test_d27_position_id.py:164-165` (same `8`/`9` → `6`/`7`).
      **Keep** `tests/test_stop_loss_target.py` — it asserts only the `Position`/`TradeGroup` model fields,
      which are retained (A87).
    - docs: `USAGE.txt` (the close / close-group / close-all text, **and the SL/TP bullet at :94-96**),
      `usage.md` (`### Portfolio & SL/TP` heading + steps 2–3; the line-102 table row's "SL/TP, close/flatten
      actions"), `docs/codebase-map.md`.
  - **Group C — Kill switch (the cancel path, ≈3 files)**
    - `ui/main_window.py` (toolbar block, `__init__` ≈318–330): `self.kill_btn = QPushButton("Kill Switch")`,
      `setObjectName("KillSwitchButton")`, its tooltip, the red `#b91c1c` style, the
      `clicked.connect(self._on_kill_switch_clicked)` line, **and the `QLabel("|")` separator immediately
      preceding it** — the toolbar's remaining widgets and its trailing `addStretch()` stay.
    - `ui/main_window.py` handlers: `_on_kill_switch_clicked` (3059–3061) and `_kill_switch`
      (3028–3057) — the `self.ib_client.reqGlobalCancel()` call (3042), the per-tracked-order
      `self.ib_client.cancelOrder(oid)` loop (3046–3051), the terminal-status pre-count, the
      `order_registry.update_status(oid, "Cancelled")` marking, and the pre/post status-bar message.
      **`_kill_switch` has exactly two callers: the toolbar button and `_on_portfolio_flatten_all` (3385) —
      the latter is already removed by Group B, so both callers go.**
    - **`reqGlobalCancel` / `cancelOrder` — no other caller exists (verified 2026-10-25), so nothing needs
      re-pointing.** There is **no** `reqGlobalCancel`/`cancelOrder` wrapper anywhere in `ibkr/` (no such method
      on `MarketDataManager`, `RealtimeBarManager`, `Orders` or the client bridge), and **no disconnect /
      teardown / `closeEvent` / reconnect path issues either call** — the only production call sites in the
      whole tree are the two lines inside `_kill_switch`. Removing the kill switch therefore removes the app's
      **entire cancel capability**; nothing is left pointing at a deleted wrapper, and nothing may be added
      back (A88).
    - `tests/test_kill_switch.py` — **whole file** (166 L, 4 cases): `test_kill_switch_cancels_all_legs`,
      `test_kill_switch_reports_counts`, `test_flatten_all_kills_first`, and
      `test_bracket_builder_registers_all_three_legs` (which also drives `win._kill_switch()` and asserts it
      cancels all three registered legs — the button it tests is gone).
    - `USAGE.txt:90-93` (the "Kill switch" bullet) **and** `:97-98` ("Orders cannot be placed while
      disconnected") — both describe controls/paths that no longer exist.
    - `docs/codebase-map.md` rows that name `_kill_switch` as retained (Plan-owned; refresh in this batch).
- **Scope — KEEP (deliberate; MUST NOT be removed with the above):**
  - **Dividend path (D38):** the S0 generic tick **`"456"`**, tick **59** handling, `_dividend_info`,
    `dividend_updated`, the dividend merge (`_merge_events`), the **event-marker overlay** and the yfinance
    corporate-events provider. Only the news `"292"` line and its digest fan-out go. *(Because both features
    share one `s0_register` mechanism, this is the single most likely accidental deletion — R68.)*
  - **Account-summary / positions data path:** retained at requirements level — the Portfolio panel stays,
    **view-only**, rendering positions and account summary as today, **minus** the Stop/Target columns (A87).
  - **Stop/target storage (NOT the UI):** `positions.stop_loss` / `take_profit` and `trade_groups.stop_loss` /
    `take_profit` **DB columns**, the `Position` / `TradeGroup` **model fields**, and the **`_persist_position`
    upsert round-trip** are **retained** — no schema change, no migration (A87). **[SUPERSEDED BY D46/A99 — the columns and model fields are dropped by a migration]** **Legacy values are NOT
    preserved, though:** with the setter gone nothing ever sets them, and `_on_position_update` builds
    `Position(stop_loss=None, take_profit=None)` while the upsert's `DO UPDATE` writes both columns, so a row's
    legacy values are cleared the first time it updates (ESC-060, corrected 2026-10-25). They are **not settable
    and not displayed**; they are also **not durable**, and every document that touches them says so.
  - **Observation-only order plumbing:** the **inbound** callbacks `_on_open_order`, `_on_order_status`,
    `_on_exec_details`, `_update_order_status`, `_on_order_error` and the `order_registry` import stay wired
    (they **observe** TWS; they neither place nor cancel). The registry is **never populated** by the app any
    more, so these are **inert** — recorded, not silently deleted (A90). **[D46 NOTE 2026-10-25: superseded — the
    observers, the three bridge signals, the three client overrides and `ibkr/orders.py` itself are now
    **removed**, because an inert chain that still looks live is the fossil the owner asked about; see D46 /
    A91–A92. TWS error surfacing is unchanged (`AC-D46.3`).]**
  - **Fail-fast port check** (`config/settings.py::check_live_port`), the **connection badge** (D26.5) and the
    global **no-test-transmits** rule — retained; none of them is an order path.
  - **D39** (burst alerts / symbol search), the chart, alarms, drawings, studies, pop-outs, D40 and D44 —
    untouched.
- **Owner-accepted consequences (stated plainly, not implied):**
  1. **The app has zero order interaction.** After D45 there is **no UI path to `placeOrder`, `cancelOrder` or
     `reqGlobalCancel`**: no in-app order ticket (gone since D41), no Close / Close Group / Flatten All, **no
     kill switch**, **no SL/TP setter** and **no replacement UI**. The app **places, cancels and closes
     nothing** — trades and their protection are managed in TWS; the app observes.
  2. **There is no panic cancel any more.** The kill switch was the app's **only** cancel control; with TWS
     holding the orders, **TWS is the cancel surface**. This is accepted because the app can no longer create an
     order that would need one (R73).
  3. **No order-safety behaviour is in play.** The notional cap, the order **pacing** guard, the
     **disconnected order-entry** guard and the `validate_order()` gate no longer gate anything, because nothing
     places orders. They are not "retained protections" — they are **moot**.
  4. **The ordering machinery is orphaned together.** `ibkr/orders.py` (builders **and** the registry, whose
     only producer was the app), `ibkr/validation.py` (**deleted**), bracket construction, OCA grouping,
     order-ID reservation (`id_manager` for orders), `ref_price`, `_ref_price_for`, and **every**
     `placeOrder`/`cancelOrder`/`reqGlobalCancel` call site are now **dead or inert in one and the same
     change**. The app is **purely read-only for trading**: it renders account, positions, bars and alerts.
     Whether `ibkr/orders.py` is deleted or left unreferenced remains a Plan/Build choice (A80/A90).
  5. **The suite's meaning shrinks even though it stays green.** **Five** whole test files are **deleted** —
     `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`,
     `tests/test_order_validation.py` (the three that were the only coverage of the close/flatten order path and
     its validation), **plus `tests/test_kill_switch.py`** (the only coverage of the cancel path, of the
     `Orders` registry's open-order enumeration and of `bracket_order`'s three-leg registration) **and
     `tests/test_sltp_honesty.py`** (the only assertion that the SL/TP dialog transmitted nothing). Case-level
     coverage also goes: the D27.1 SL/TP row-addressing case, the D38 digest cases and the two SL/TP signal
     checks in the D18 receiver loop. A green suite after D45 therefore proves **less** about order safety and
     protection than a green suite before it. This is recorded, not hidden.
  6. **The owner closes positions and cancels orders in TWS**, and the panel reflects the result on the next
     position update; local stop/target values saved before D45 are no longer shown, and the next live update
     for that row clears them (ESC-060) — nothing preserves them.
- **Requirements (final):**
  - **D45.1 — remove all three groups completely.** No News Digest dock, no `View` menubar, no news `"292"`
    request, no `ibkr/news.py`/`NewsManager`; no Trade Context Menu, no close/close-group/flatten-all signal or
    handler, no `ibkr/validation.py`; **no Kill switch button/handler/`_kill_switch`**, no `reqGlobalCancel` or
    `cancelOrder` call; **no SL/TP dialog, no SL/TP signals or handlers, no Stop/Target columns**.
  - **D45.2 — no order path and no cancel path remain.** `placeOrder`, `cancelOrder` and `reqGlobalCancel` are
    **unreachable from any UI path**. Whether the now-unreferenced `ibkr/orders.py` is deleted or left is a
    Plan/Build detail (A80/A90); the requirement is **unreachability and zero transmitted/cancelled orders**.
  - **D45.3 — dividends keep working.** The S0 `"456"` line, tick 59, `_dividend_info`/`dividend_updated` and
    the chart's dividend event markers are unchanged and still exercised by tests.
  - **D45.4 — retained surfaces keep working.** The Portfolio panel renders positions/account summary
    **view-only** with **8 columns**; the dividend markers, D39, the chart, alarms, drawings, studies, pop-outs,
    D40 and D44 behave as today. **The kill switch and the SL/TP dialog no longer exist** (they are no longer
    "retained surfaces").
  - **D45.5 — docs cleaned in the same batch** (`USAGE.txt`, `usage.md`, `docs/codebase-map.md`), with no doc
    advertising a removed feature, an app-placed order, an in-app cancel, or settable SL/TP.
  - **D45.6 — stop/target storage survives the UI.** The `positions` / `trade_groups` `stop_loss` /
    `take_profit` columns and the model fields are **retained unchanged** (no migration) **[SUPERSEDED BY D46/A99 — dropped by migration]** while
    the two **display** columns and every setter are removed (A87); the values themselves are **not** preserved — a live update writes them empty (ESC-060).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D45.1 (no News Digest dock; no menubar)** Given the running app, Then **no News Digest dock**
    exists and no control opens one, `MainWindow` has **no** `news_digest_dock` attribute and **no**
    `_on_news_digest_visibility`, and the window creates **no `QMenuBar`** at all — so **no `View` menu**
    and no `Ctrl+Shift+N` action exist. (Context menus such as the D21.5 watchlist column popup may still
    exist and are **not** affected.) (Measurable: `hasattr(win, "news_digest_dock") is False`;
    `win.findChildren(QMenuBar)` is empty; no `QMenu` titled `View`; no `QAction` whose text is
    `News Digest`; `ui/news_digest_dock.py` and `ibkr/news.py` do not exist; `import ibkr.news` /
    `import ui.news_digest_dock` fail.)
  - **AC-D45.2 (news `"292"` gone; dividends `"456"` retained and markers still work)** Given a dividend-paying
    symbol with earnings/dividend/split events and a mocked client, Then the session **never** requests generic
    tick `"292"` and **does** register `"456"` for dividends, tick 59 still updates `_dividend_info` and emits
    `dividend_updated`, and the **event markers + countdown still render**. (Measurable: the fake client's
    `reqMktData` generic tick strings never contain `"292"` and contain `"456"`; the surviving
    `tests/test_d38_events_news.py` event-marker/dividend cases pass; `AC-D38.1`/`AC-D38.5` still hold.)
  - **AC-D45.3 (no Trade Context Menu; no close affordances)** Given positions in the Portfolio panel, When the
    user right-clicks a position row, a group row and empty space, Then **no menu appears**, and the panel
    exposes **no** `position_close_requested` / `group_close_requested` / `flatten_all_requested` signal, no
    `_on_flatten_all`, no `_show_context_menu`, and no Close / Close Group / Close All control anywhere in the
    app. (Measurable: the table's context-menu policy is not `CustomContextMenu` (or a simulated
    `customContextMenuRequested` pops no `QMenu`); `hasattr` checks on the panel and window are False;
    `ui/trade_context_menu.py` does not exist; a source scan finds none of the three signal names or
    `TradeContextMenu`.)
  - **AC-D45.4 (no order interaction at all; `placeOrder`/`cancelOrder`/`reqGlobalCancel` unreachable)** Given
    the app connected to a mocked client, When **every** remaining UI affordance is exercised (chart loads,
    timeframe/mode switches, watchlist add/remove, watchlist column popup, alarms, studies, drawings, pop-outs,
    Portfolio selection/refresh, dialogs), Then **zero** orders are built, **zero** are transmitted and **zero**
    cancellations are issued — `placeOrder.call_count == 0`, `cancelOrder.call_count == 0` and
    `reqGlobalCancel.call_count == 0` — and no `ui/` module calls `placeOrder`/`cancelOrder`/`reqGlobalCancel`,
    imports `ui.trade_context_menu` or `ui.stop_loss_target_dialog`, or imports
    `ibkr.validation`/`validate_order`; `ibkr/validation.py` does not exist. (Measurable: mocked-client
    walkthrough asserting all three call counts are `0`; a static scan of `ui/` for `placeOrder`, `cancelOrder`,
    `reqGlobalCancel`, `validate_order`, `trade_context_menu`, `stop_loss_target_dialog`,
    `_close_position_by_id` returns nothing.)
  - **AC-D45.5 (Portfolio is view-only; the data path is retained)** Given account-summary and position updates
    from IBKR, Then the Portfolio panel still renders and live-updates its rows exactly as today (8 columns, no
    Stop/Target — `AC-D45.10`), offers **no** close/flatten/modify action, and reflects a **TWS-side** close on
    the next position update. (Measurable: position rows render from `_on_position_update`/`_on_position_end`;
    no action affordance or menu exists; a simulated external close updates/removes the row.)
  - **AC-D45.6 (INVERTED — the kill switch and the SL/TP dialog are GONE)** Given the running app, Then **no
    Kill Switch control or cancel path exists**: `MainWindow` has **no** `kill_btn` attribute, no widget with
    `objectName() == "KillSwitchButton"`, no `_on_kill_switch_clicked` and no `_kill_switch`; **and** the
    **SL/TP dialog no longer exists**: `ui/stop_loss_target_dialog.py` does not exist,
    `import ui.stop_loss_target_dialog` fails, the Portfolio panel exposes **no** `position_sltp_changed` /
    `group_sltp_changed`, no `_on_set_sltp`, no `_on_sltp_confirmed`, no `update_position_sltp`, no
    `update_group_sltp` and no `_sltp_dialog`, and `MainWindow` has no `_on_portfolio_sltp_changed` /
    `_on_portfolio_group_sltp_changed`. With open orders resting in TWS and a mocked client, **no interaction
    with the app cancels them** — `reqGlobalCancel` and `cancelOrder` are **never** called by the app.
    (Measurable: `hasattr` checks False for every named member; `findChildren(QPushButton)` on the toolbar
    contains no "Kill Switch"/`#KillSwitchButton`; a static scan of `ui/` for `reqGlobalCancel`, `cancelOrder`,
    `_kill_switch`, `StopLossTargetDialog`, `position_sltp_changed`, `group_sltp_changed` returns nothing;
    mocked-client walkthrough asserting both cancel call counts are `0`. **This criterion replaces the former
    "kill switch and SL/TP still work" assertion — it is a deliberate inversion, recorded in A88/A89.**)
  - **AC-D45.7 (docs updated in the same batch)** Given the repository, Then `USAGE.txt` contains **no**
    `View → News Digest` / digest description, **no** Close / Close Group / Close All description, **no**
    kill-switch description and **no** SL/TP-dialog description (nor an app-placed-order notional cap /
    "orders placed while disconnected" claim); `usage.md`'s `### Portfolio & SL/TP` section and its
    Portfolio table row advertise **no** SL/TP setter and **no** close/flatten actions, while its Database
    section still lists the `positions` / `trade_groups` tables (with a note that the SL/TP **columns** are retained but are no
    longer settable in-app, and a live update writes their values empty — ESC-060); `docs/codebase-map.md` no longer lists `ui/news_digest_dock.py`,
    `ui/trade_context_menu.py` or `ui/stop_loss_target_dialog.py` and no longer names `_kill_switch` or
    `StopLossTargetDialog` as retained. (Measurable: a grep for `News Digest`, `Ctrl+Shift+N`,
    `Close All Positions`, `Close Group`, `Close Position`, `Kill switch`, `Stop-Loss` over the three files
    returns nothing except text that explicitly says the app does **not** place/cancel orders and that closes
    and cancels happen in TWS.)
  - **AC-D45.8 (no dangling references; suite green; test book as recorded)** Given the change, Then the app
    launches and charts normally, no module imports `ui.news_digest_dock`, `ibkr.news`,
    `ui.trade_context_menu`, `ui.stop_loss_target_dialog` or `ibkr.validation`, and the full offscreen suite is
    green with exactly the recorded test-book change: **deleted (5)** `tests/test_d28_6_close_contracts.py`,
    `tests/test_d41_retained_order_path.py`, `tests/test_order_validation.py`, `tests/test_kill_switch.py`,
    `tests/test_sltp_honesty.py`; **adjusted** `tests/test_order_rejections.py`, `tests/test_d28_pacing.py`,
    `tests/test_dock_d18_region.py` (`:147` digest filter, `:176` close path, `:177-178` SL/TP signals),
    `tests/test_d27_position_id.py` (the SL/TP row-addressing case removed; the `8`/`9` column indexes →
    `6`/`7`), `tests/test_d27_position_prices.py` (`8`/`9` → `6`/`7`), and `tests/test_d38_events_news.py`
    (digest/`NewsManager` cases removed, **event-marker cases kept**); **kept** `tests/test_stop_loss_target.py` **[DELETED BY D46 — its four model fields go with the columns]**
    (model fields only) and `tests/test_d41_removal.py` (its `queue_depth` reference is an allow-list string).
    (Measurable: import/compile check + full-suite run; the residue grep of AC-D45.4/AC-D45.6.)
  - **AC-D45.9 (history preserved; marker + tech stack intact)** Given `requirements.md`, Then `### D38`,
    `### D41` and `### D26` remain with explicit **superseded-by/revised-by D45** notes on the clauses named
    below, and the **Existing Repository marker sentence + Current Tech Stack are unchanged**. (Measurable:
    the markers are present; the literal existing-repo sentence still occurs; D45 is registered.)
  - **AC-D45.10 (Stop / Target columns gone; storage and no-migration guarantee)** Given a Portfolio with
    positions — including rows carrying legacy `stop_loss`/`take_profit` values — When the table renders, Then
    it shows exactly **8 columns** (`Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`) with **no**
    `Stop` and **no** `Target` header, the legacy values are **not** displayed, and the underlying
    `positions`/`trade_groups` columns and `Position`/`TradeGroup` fields still exist (no schema change, no
    migration run). **This AC does not assert value preservation** — a live update clears both columns (ESC-060),
    so a test that seeds legacy values and expects them to survive an update asserts the wrong thing.
    (Measurable: `positions_table.columnCount() == 8`; the header texts contain neither `Stop` nor `Target`;
    a DB opened from a pre-D45 file keeps its `stop_loss`/`take_profit` values; the Strategy/Group cells are
    at indexes `6`/`7`.)
- **Supersession / revision record (recorded, not silent):**
  - **`AC-D38.2` (digest groups + article fetch) — SUPERSEDED BY D45.** The digest, `NewsManager`,
    `ibkr/news.py` and `reqNewsArticle` are removed; there is nothing to group or fetch into.
  - **`AC-D38.3` (no news entitlement state) — SUPERSEDED BY D45.** With no digest there is no such state.
  - **`AC-D38.6` (regression) — REVISED BY D45.** The green-suite rule stands; the D38 surface that survives is
    the **corporate-event markers + dividend merge** (`AC-D38.1`, `AC-D38.4`, `AC-D38.5`).
  - **`AC-D41.1` — the Portfolio clause REVISED BY D45.** Its "Portfolio section (Close / Close Group /
    Flatten All + the SL/TP dialogs) still renders" becomes: the Portfolio section still renders **view-only**
    (no close/flatten controls, **no SL/TP dialog**, no Stop/Target columns).
  - **`AC-D41.4` — the retained-order-path/`ref_price` clause REVISED BY D45.** **No** order-related surface is
    retained: the SL/TP dialog is **removed** as well, nothing builds or transmits an order, and the `ref_price`
    clause is **moot**.
  - **D41 "Scope — KEEP" order-machinery bullet — SUPERSEDED BY D45.** `ibkr/validation.py` is **deleted**; the
    close/flatten paths, the **kill switch** and the **SL/TP dialog** are gone; `ibkr/orders.py` (and the order
    registry/error handling) may remain but has **no caller and no app-placed orders** (A80/A90). Only the
    **fail-fast port check** and the **inert inbound order callbacks** remain. **[D46 NOTE 2026-10-25: the
    inbound callbacks are removed too — see D46 / A92; only the fail-fast port check, the connection badge and the
    generic error line remain.]**
  - **D41 retained-order-path `ref_price` bullet — MOOT (D45).** No order is built, so `ref_price` has no
    consumer.
  - **D26 — order-entry clauses MOOT; `AC-D26.3` MOOT; `AC-D26.8` SUPERSEDED.** `AC-D26.4`/`AC-D26.6` were
    already control-less after D41. After D45: **`AC-D26.3`** (the SL/TP dialog's "labelled as not placing
    orders" branch) has **no dialog**; **`AC-D26.8`** (the kill switch, `reqGlobalCancel` + per-ID cancels,
    pre/post counts) has **no switch and no control** — superseded in full; `AC-D26.7` (validate-order gate) and
    `AC-D26.9`'s order-entry/registry clauses have **no control to exercise**. **Retained:** the **fail-fast
    port check + badge** (`AC-D26.5`) and the **connection** half of the error alerts.
  - **`D21.13` — reviewed, NOT superseded.** It governs the right dock / Portfolio "Account Summary" toggle;
    the Portfolio panel **remains** (view-only). **No** `AC-D21.13.*` clause names a close/flatten, kill-switch
    or SL/TP control.
  - **`AC-D18.6` / D18 width model — not superseded; re-derived.** The positions table drops from 10 to 8
    columns, which only **reduces** its width demand; the dock-cap/visibility criteria stand as written.
  - **Glossary "Live-order path" — REVISED BY D45**, with new **"Kill switch"** and **"SL/TP dialog"** rows
    recording both as removed.
  - **Untouched:** `AC-D44.*`, D39, D40, D42, D43, and every D1–D37 criterion not named above.
  - **Historical passages left un-annotated (2026-10-25):** the D41 retained-order-path wording also
    survives, as history, at Journey 36 *Steps* step 3 (≈1041) and *Postconditions* (≈1048–1049); D41 *Status*
    (≈3621–3622), *Scope — REMOVE* Active-Trader bullet (≈3664–3665) and *Edge Cases* (≈3772–3774); and the
    Batch 18 narrative (≈4811). These are superseded by D45; they are not annotated individually because the
    project keeps reversals visible in the history rather than rewriting it. The authoritative statement of the
    end state is the D45 register + this supersession record.
- **Edge Cases:** right-click on a **watchlist** row/column header still opens the D21.5 column popup and the
  D22 add/remove entries (unaffected); right-click on the **chart** is unchanged; right-click anywhere in
  **Portfolio** now does nothing (no menu at all — the context-menu policy goes with the menu); a stale saved
  dock state that names the removed digest dock is ignored (no error, no dock recreated) and an orphan
  `Ctrl+Shift+N` `QAction` must not survive; a stale saved `QSettings`/layout entry naming the removed toolbar
  button or the dialog is ignored; **open orders resting in TWS are never cancelled by the app** (no kill
  switch, no teardown cancel) — the owner cancels in TWS; a position row carrying legacy `stop_loss` /
  `take_profit` values renders normally without those columns; the **DB schema is unchanged** (no migration, no
  data deletion) and a pre-D45 database opens cleanly **[SUPERSEDED BY D46/A99 — the two columns are dropped by migration; rows preserved]**; the SL/TP dialog is gone even for a position that is
  still open (there is no "read-only" fallback dialog in this batch); **disconnected** — the Portfolio panel
  shows "unavailable" and there is no order path left to block; dividend-free/futures symbols skip dividends as
  today; a yfinance outage still leaves the IBKR tick-59 dividend marker rendering (`AC-D38.5`); **no menubar**
  means the app adds no macOS app-menu items; `tests/test_d41_removal.py`'s allow-list entry (`queue_depth`) must
  survive the `ibkr/news.py` deletion.
- **Assumptions (lite) — D45 (lite lane: no question was asked; every default is A79–A90):**
  - **A79** the digest half of D38 goes while the **event-marker/dividend half stays** (owner-confirmed).
  - **A80** `ibkr/orders.py` **may remain unreferenced**; the requirement is that **no UI path reaches
    `placeOrder`** — deleting it is a Plan/Build choice (default: leave it, delete only the callers).
  - **A81** whole-file test deletions are **five and all named** (three order-safety + `test_kill_switch.py` +
    `test_sltp_honesty.py`); the digest/`NewsManager` cases are **trimmed from**
    `tests/test_d38_events_news.py` (file kept) and the case-level trims are enumerated in `AC-D45.8`.
  - **A82** ~~the **kill switch** is retained and covered by its own path; only its flatten-all coupling goes.~~
    **REVERSED 2026-10-25 (D45 extension) — the kill switch is REMOVED in full; see A88.**
  - **A83** ~~the **SL/TP dialog** is retained unchanged and stays **local-only**.~~ **REVERSED 2026-10-25
    (D45 extension) — the dialog is REMOVED in full, with its columns; see A89.**
  - **A84** the Portfolio panel is **view-only** with the account-summary/positions data path retained; **no**
    replacement close UI, hotkey or TWS-API bridge.
  - **A85** documentation scope is the **three owner-named files**; `docs/architecture.md`/`docs/plan.md` are
    Plan/Validator-owned and synced there.
  - **A86** **no menubar replaces the removed `View` menu**, and `Ctrl+Shift+N` goes with it.
  - **A87** **Stop / Target columns decision: REMOVE the columns with the dialog; KEEP the storage.** The
    positions table goes **10 → 8 columns** and the two headers/values/alignment slots go; the
    `positions.stop_loss` / `take_profit` and `trade_groups.stop_loss` / `take_profit` **DB columns**, the
    `Position`/`TradeGroup` **model fields** and the `_persist_position` upsert **stay**, with **no migration
    and no destructive schema change**. **[SUPERSEDED BY D46/A99 — the columns and fields are dropped by migration]** *Why:* (a) with the dialog gone there is **no setter anywhere**, so the columns
    would be permanently dead display — and a "Stop"/"Target" header on a trading panel implies a control that
    no longer exists (the owner has declined replacement UI twice, so no read-only fallback dialog either);
    (b) the storage is cheap to keep and deleting it would mean a destructive schema migration plus edits to
    the position upsert and four D27 model/persistence tests, for **zero** user-visible gain — keeping it also
    means a pre-D45 database opens without a migration. **It does not preserve the values**, though: the live
    update writes both columns empty (ESC-060, corrected 2026-10-25), so the old "values are preserved" rationale
    was never true at runtime and every document now says what the code actually does. **Rejected alternative:**
    keep the columns as read-only display of legacy values — it advertises a feature the app cannot perform and
    costs two of a width-constrained table's columns.
  - **A88** **Kill-switch removal is total, and no cancel capability is left or re-pointed.** `reqGlobalCancel`
    and `cancelOrder` each have **exactly one** production call site — inside `MainWindow::_kill_switch` — and
    **no** disconnect/teardown/reconnect caller and **no** `ibkr/` wrapper exist, so the removal deletes the
    app's whole cancel capability and nothing needs to be re-homed. Cancel surface after D45 = **TWS**.
  - **A89** **SL/TP removal is total** — dialog file, `confirmed` signal, Portfolio signals/import/handlers,
    the two `MainWindow` persistence slots with their row-`UPDATE`s, and the two display columns. The dialog had
    **already lost its only entry point** when Group B removed `TradeContextMenu.set_sltp_action` (the Plan map
    records this as `FI-D45-1`), so Groups B and the extension agree about the end state rather than
    contradicting. The **model fields/DB columns stay** (A87) because they are not UI. **[SUPERSEDED BY D46/A99 — both are dropped by migration]**
  - **A90** **Observation-only order plumbing stays, inert.** The inbound callbacks (`_on_open_order`,
    `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`) and the `order_registry`
    import remain wired — they **observe** TWS and surface errors; they place/cancel nothing, and the registry
    is never populated, so they are inert. Deleting them is **not** part of this batch (they sit on the
    connection/error path D26.5's badge depends on). `ibkr/orders.py` keeps A80's default (leave it); if Plan
    deletes it instead, these callbacks must be made registry-safe in the same task. **No replacement cancel or
    protection UI is authorized.**
- **Correction record (artifacts that must change — Plan / Task Manager / Build / Code Reviewer):**
  - **Plan:** refresh `docs/codebase-map.md` (Plan-owned) to drop all three modules **and** the order path,
    **and to stop naming `_kill_switch` / `StopLossTargetDialog` as retained** (its D45 rows currently do);
    this is a **substantive** requirements change, so sync `docs/plan.md`/`docs/architecture.md` (the standing
    `plan_proposal.md` staleness flag is **not** benign here — memory 2026-10-23).
  - **Task Manager:** enumerate the assertions invalidated **outside** the edited files (memory 2026-10-23
    item 4) — `tests/test_d41_removal.py`, `tests/test_dock_d18_region.py`, `tests/test_d38_events_news.py`,
    **`tests/test_d27_position_id.py` (`8`/`9` column indexes + the SL/TP case)** and
    **`tests/test_d27_position_prices.py` (`8`/`9` column indexes)**; do **not** task a deletion of
    `ibkr/orders.py` unless Plan chooses it (A80/A90).
  - **Build:** split the deletions **by member group** (memory 2026-10-15: delete-only tasks are what kill
    workers); after each file, run a syntax/import check and a residue grep for `292`, `NewsManager`,
    `news_digest`, `TradeContextMenu`, `position_close_requested`, `group_close_requested`,
    `flatten_all_requested`, `validate_order`, `_close_position_by_id`, `placeOrder`, **`kill_btn`**,
    **`KillSwitchButton`**, **`_kill_switch`**, **`reqGlobalCancel`**, **`cancelOrder`**,
    **`StopLossTargetDialog`**, **`stop_loss_target_dialog`**, **`position_sltp_changed`**,
    **`group_sltp_changed`**, **`_on_set_sltp`**, **`_sltp_dialog`** in `ui/`.
  - **Code Reviewer:** independently confirm **zero** `placeOrder`, **zero** `cancelOrder` and **zero**
    `reqGlobalCancel` call sites, that the **dividend markers still render**, that the positions table has
    **8 columns** with no `Stop`/`Target`, that a pre-D45 DB still opens with its stored values intact, and
    that the three docs advertise nothing removed.

### D46 — Delete **every** order-related coding path — the module, the observation chain, the zero-consumer order utilities and the stops/targets storage — OWNER-REQUESTED 2026-10-25 (scope **EXPANDED** 2026-10-25 by Q56–Q59)

- **Area (REMOVE):**
  1. **`ibkr/orders.py`** — the whole file (`UserOrder`; `Orders` with `market_order`/`limit_order`/`stop_order`/
     `bracket_order` and `register`/`get`/`update_status`/`clear_filled`/`all`; the `orders` singleton; the
     `from ibapi.order import Order` import — the **last** production use of `ibapi.order` in the tree).
  2. **The inbound observation chain** — `IBApiClient.orderStatus` / `openOrder` / `execDetails`;
     `IBBridge.order_status` / `open_order` / `exec_details`; their three `__init__` connects;
     `MainWindow._on_open_order` / `_on_order_status` / `_on_exec_details` / `_update_order_status` /
     `_on_order_error`; the `order_registry` import and the registry branch in `_on_error`.
  3. **`data/models.py::UserOrder`** and the `tests/test_ui_smoke.py` `hasattr` that is its only reference.
  4. **Zero-consumer order utilities** (new in the expansion): `ibkr/pacing.py::OrderRateLimiter` +
     `order_limiter`; `config/settings.py::MAX_ORDER_NOTIONAL`; the **order-fill sound**
     (`services/sound_service.py::render_fill_blip`, `BLIP_DURATION`, `SoundService._fill_effect`,
     `SoundService.play_fill`, the `"fill"` key of `ensure_sound_files`, `order_fill.wav`, the module-docstring
     bullet).
  5. **`ibkr/id_manager.py::IdManager.reserve`** (+ its D26.2 docstring). **The module stays** — see A101.
  6. **The stop/target storage** (A99, **reverses A87**): the `positions.stop_loss` / `positions.take_profit` and
     `trade_groups.stop_loss` / `trade_groups.take_profit` **DB columns**; the `data/models.py`
     `Position` / `TradeGroup` fields; the `ibkr/account.py` `Position` fields and the two `build_position_from_ib`
     parameters; `MainWindow._persist_position`'s `stop_loss=None, take_profit=None`; `_upsert_position`'s column
     list, `VALUES` placeholders and `DO UPDATE SET` pair; `_on_position_end`'s `columns` tuple, its
     `row[12]/row[13]/row[14]` indices and its `Position(...)` kwargs.
  7. **Comments/docstrings that assert any of the above is retained**, and the test book in D46.5/D46.12.
- **Status:** **NEW / OWNER-REQUESTED 2026-10-25 — lite lane, then EXPANDED the same day when the owner answered
  Q56–Q59 verbatim.** The original scope (module + observation chain) is A91–A98. The expansion is A99–A104:
  **A87 is REVERSED** (storage dropped, not kept — first destructive schema step in the project),
  **A97 is REVERSED IN PART** (its `reserve()` half) and **CONFIRMED IN PART** (`classify_error` → A100),
  **A92 / A93 / A96 are CONFIRMED by the owner** (no longer recorded defaults), and **A80 / A90 stay reversed**
  (A91/A92, recorded earlier today). **D1–D45 are NOT reopened**; **ESC-061 is MOOT**; **DG76 is resolved** by the
  deletion; **DG79 / DG80 are resolved by the owner's answers**. No blocking question remains. This is a
  **destructive** batch by owner instruction (D46.12) and *not* a delete-only one.
- **Reported (verbatim):** *"I dont want anything to do with orders so why is there orders.py ?"* — asked after D45
  delivered zero order interaction; the owner then confirmed opening this batch. On being shown the recorded
  defaults the owner answered:
  - **Q56** *"why is there any order related code left"*
  - **Q57** *"there should not be any order related coding. i want all of it deleted"*
  - **Q58** *"yes remove"*
  - **Q59** *"remove everything"*
- **Why order code was still there — the Q56 answer, recorded (not just deleted).** Two decisions produced it and
  both rested on a premise nobody checked. D45's **A80** left `ibkr/orders.py` "unreferenced but retained" and
  **A90** left the observers "wired, inert, for the future", reasoning that the chain only *observes* and can
  never place or cancel — which was true as written and **wrong in effect**, because "inert" was never audited for
  **reachability**. The only handler that phrased a rejection, `_on_order_error`, was guarded by
  `if order_registry.get(reqId) is not None:` against a registry **nothing ever populates**, so it was dead at
  entry; every observer wrote into that same permanently-empty dict. **The lesson for this pipeline:** a
  "retained and inert" decision must name the code that proves the path is unreachable **and** the test that would
  fail if it became reachable — "it only observes" is not evidence. Q56 was not a scope question with an answer; it
  was the observation that the retention decision had never been audited. **D46.9's inventory is the mechanism that
  stops the same audit from being skipped again.**
- **Owner constraints:**
  1. **Nothing to do with orders.** No replacement order, cancel or protection UI — declined three times now;
     **not re-proposed anywhere in this batch**.
  2. **TWS errors must still surface.** The status bar is the surface; this batch must not remove error visibility
     and must state what happens to **201 / 103 / 202**, whose "Rejected" / "Cancelled" phrasing lives inside the
     unreachable `_on_order_error` (`D46.3` / `AC-D46.3`).
  3. **"All of it" is the ask** (Q57/Q59). The retention decisions this supersedes (A80, A87, A90, A93's premise,
     A96, A97) are **reversed in place, never rewritten**, so a reader can follow kept → cleared → dropped.
  4. **Nothing innocent may be cut** (Q56 asks *why*, so the answer must show the audit). General code that merely
     carries an order name is listed in the inventory's **RETAIN** set with the evidence that keeps it.
- **Observed in repository (validated 2026-10-25; symbol-first — line numbers indicative):**
  - **`ibkr/orders.py` (141 L)** — `UserOrder` (:11); `Orders` (:27) with builders
    `market_order` / `limit_order` / `stop_order` / `bracket_order` (:34–115) and registry
    `register` / `get` / `update_status` / `clear_filled` / `all` (:118–137); singleton `orders` (:141).
    **The builders have zero production callers** (grep across `ui/ services/ data/ ibkr/ config/ main.py` finds no
    hit outside the module). **`register()` is never called in production**, so `_orders` is permanently empty and
    every read returns `None`. The bracket builder still carries a D26.1 comment about protective children trading
    opposite the entry side — a comment about a feature that no longer exists.
  - **The inbound chain terminates in that no-op:** `IBApiClient`'s `orderStatus` / `openOrder` / `execDetails`
    overrides each call `super()` (a no-op on `EWrapper`) and then emit an `IBBridge` signal
    (`order_status` / `open_order` / `exec_details`); `MainWindow.__init__` connects all three to
    `_on_open_order` / `_on_exec_details` / `_on_order_status`; each calls `_update_order_status` and nothing else;
    `_update_order_status` is `order = order_registry.get(orderId); if order: order.status = status` — always
    `None`. **No other consumer exists anywhere in the tree** (repo-wide grep).
  - **`_on_order_error` is unreachable.** In `_on_error` the order branch is guarded by
    `if order_registry.get(reqId) is not None:` — always false — so control falls through to the generic
    `self.status_bar.showMessage(f"Error [{error_code}]: {error_string}", 8000)`. The unreachable handler mapped
    **201/103 → "Rejected"**, **202 → "Cancelled"**, anything else → `f"Error {code}"`, and showed
    `f"Order #{id} {status}: {error_string}"` for **12000 ms**.
  - **Order errors still reach the generic line.** `ibkr/error_codes.py::classify_error` rates **201, 103 fatal**
    and **202 warning**; `IBApiClient.error` emits `error_msg` unless the severity is `info`, so all three codes
    reach `_on_error`. **What the owner sees today is therefore already the generic line** — this removal changes
    nothing user-visible.
  - **A second vestige:** `data/models.py::UserOrder` (:105) is a **different, unused** dataclass; its only
    reference in the tree is `tests/test_ui_smoke.py:48` (`hasattr`). `ibkr/orders.py` carries its own copy of the
    same class — two `UserOrder` classes, both order-only.
  - **The three zero-consumer order utilities (new, expansion):** `OrderRateLimiter` / `order_limiter`
    (`ibkr/pacing.py:128-172`) has **no production reader anywhere** — its only consumers are
    `tests/conftest.py:143,146` (`reset_for_tests`), one case in `tests/test_d28_pacing.py:97-101` and a survivor
    string in `tests/test_d45_removal.py:149`. `MAX_ORDER_NOTIONAL` (`config/settings.py:39`) has **zero**
    readers; its comment still points at `validate_order()`, deleted in D45. `SoundService.play_fill`
    (`services/sound_service.py:170`) has **zero** callers — only `play_alarm` is ever played
    (`ui/main_window.py:2114`) — so `render_fill_blip`, `BLIP_DURATION` (:22), `_fill_effect`, the `"fill"` key and
    `order_fill.wav` are an order-fill path with no order to fill.
  - **`IdManager` is NOT order-only — checked before writing it down.** `get_id()` is called at
    `ibkr/market_data.py:42,74,90,103` and `ibkr/realtime_bars.py:31` (market-data/realtime reqIds), and
    `set_next_valid_id()` at `ibkr/client.py:184`. Only **`reserve()`** (`ibkr/id_manager.py:19-30`) is
    order-only: it exists for D26.2 multi-leg IDs and its callers are **tests only**
    (`tests/test_id_manager.py:12,23,34,41,62`). **Verdict: the module stays, `reserve()` goes** (A101).
  - **`nextValidId` is NOT order-only either — checked.** `IBApiClient.nextValidId` (`ibkr/client.py:182-193`)
    is the **connection-established** transition (`_connected = True`, reconnect-attempt reset, disconnect-class
    clear, `_set_state(CONNECTED)`) and is exactly what D40's lifecycle tests drive
    (`tests/test_d40_tws_lifecycle.py:239,311,368,407,450`; `tests/test_d25_alarm_monitor.py:397`). Its name is
    IBKR's (`EWrapper.nextValidId`) and cannot be renamed. **Verdict: retained** (A102, DG82).
  - **Tests:** `tests/test_order_builders.py` (200 L, **17 cases**) covers only the zero-caller builders and the
    never-populated registry. `tests/test_order_rejections.py` (88 L, **5 cases**): two assert the unreachable
    registry branch (201 → `Rejected`, 202 → `Cancelled`), one asserts an unrelated error leaves the registry
    alone, two pin `classify_error` (`201/103/1100/502/503/509` fatal; `2104/2106` info).
    `tests/test_d45_removal.py::_SURVIVORS` (:145-147) allow-lists `order_registry`, `orders`, `UserOrder`,
    `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`,
    `order_limiter`, `MAX_ORDER_NOTIONAL` — **A90's end state plus A97's two leftovers**, all of which must now
    move from the survivor allow-list to the **forbidden** set.
  - **The expansion's test book:** `tests/test_stop_loss_target.py` (whole file, 3 cases) asserts only the four
    model fields, so it dies with them; `tests/test_account.py` has **four** `build_position_from_ib` calls
    carrying `stop_loss=None, take_profit=None` plus two asserts (:108-109); `tests/test_strategy_detection.py:30-31`
    passes the two names as `Position(...)` kwargs; **three** SQL seeders name the columns in their `INSERT`
    (`tests/test_d27_position_id.py:99`, `tests/test_d27_account_partial_window.py:68`,
    `tests/test_d27_account_scoping.py:68`); `tests/test_sound_service.py` has `TestFillBlip` (2 cases) and a
    `render_fill_blip` use in `TestWavOutput`; `tests/test_d28_pacing.py:97-101` and `tests/conftest.py:143,146`
    are `OrderRateLimiter`'s only survivors.
  - **Docs that contradict the owner (Plan-owned, and the D45/ESC-060 statements now contradicted again):**
    `docs/codebase-map.md:97` states `ibkr/orders.py` "**is NOT orphaned and must NOT be deleted**", `:177-179`
    lists the observers as "retained by decision … do not 'clean up'", `:193` / `:204` keep the module in the index;
    `docs/architecture.md` `S29` / `AR-D45-10` require a **module-docstring note** on the retained module.
    **Second correction (this batch):** the stop/target statements **rewritten this morning under ESC-060** now say
    the columns are *kept but cleared* — the opposite of A99. They are at least `USAGE.txt:88` ("The database
    columns are kept, but an update from TWS writes them empty"), `usage.md:154` ("The stop-loss / take-profit …
    columns are kept (no migration)"), at least five `docs/architecture.md` sites (`:4645`, `:4822`, `:4848`,
    `:4901`, and the P5 block `:5127-5129` / `:5331-5332`), at least three `docs/plan.md` sites (`:2004`,
    `:2551-2552`, `:2916`, `:2954-2955`), and eight `requirements.md` sites (D45's KEEP list, its
    `AC-D45.6` / `AC-D45.10` retention halves, Journey 38's postcondition and edge case, D46's now-superseded KEEP
    list, and Journey 39's edge case — all amended or annotated in place in this revision). The trail must read
    **kept → cleared → dropped**; two live claims must not stand side by side (**D46.13**, DG84).
- **Order-symbol inventory — exhaustive, with a disposition for every item (this table IS the acceptance
  instrument for D46.9; ambiguous items are flagged in `design_gaps.md` rather than guessed).**

  **DELETE — order code and order-motivated code (nothing here survives D46):**

  | # | Symbol(s) | Where | What it is | Disposition |
  |---|---|---|---|---|
  | 1 | `ibkr/orders.py` (whole file) | `ibkr/orders.py` | Builders + registry, zero production callers | **DELETE** (D46.1) |
  | 2 | `UserOrder` (module copy), `Orders`, `market_order`, `limit_order`, `stop_order`, `bracket_order`, `register`, `get`, `update_status`, `clear_filled`, `all`, `orders` | `ibkr/orders.py` | Order construction + open-order registry | **DELETE** (D46.1) |
  | 3 | `from ibapi.order import Order` | `ibkr/orders.py:5` | Last production `ibapi.order` import | **DELETE** (D46.1) |
  | 4 | `orderStatus`, `openOrder`, `execDetails` (repo overrides) | `ibkr/client.py:394-416` | Inbound overrides → `IBBridge` signals → empty registry | **DELETE** (D46.2) |
  | 5 | `order_status`, `open_order`, `exec_details` (+ their `# orderId, …` comments) | `ibkr/bridge.py:47-55` | Signals whose only consumers write `None` | **DELETE** (D46.2) |
  | 6 | `b.open_order/_on_open_order`, `b.exec_details/_on_exec_details`, `b.order_status/_on_order_status` connects | `ui/main_window.py:595-597` | Wiring of the dead chain | **DELETE** (D46.2) |
  | 7 | `_on_open_order`, `_on_exec_details`, `_on_order_status`, `_update_order_status` | `ui/main_window.py:2951-2965, 3226-3229` | Slots writing `order.status` on `None` | **DELETE** (D46.2) |
  | 8 | `_on_order_error`, the `order_registry.get(reqId)` branch and its D26.9 comment | `ui/main_window.py:1543-1561` | **Unreachable** "Rejected"/"Cancelled" wording (12 s) | **DELETE** (D46.2, D46.3) |
  | 9 | `order_registry` import | `ui/main_window.py:36` | Import of the deleted module | **DELETE** (D46.1) |
  | 10 | `data.models.UserOrder` (+ `order_id`, `order_type`, `oca_group`, `transmit`) | `data/models.py:105-120` | Second, unused order dataclass; only reference is a smoke `hasattr` | **DELETE** (D46.8) |
  | 11 | `OrderRateLimiter`, `order_limiter` | `ibkr/pacing.py:128-172` | Order-path token bucket; **zero production readers** | **DELETE** (D46.11) |
  | 12 | `MAX_ORDER_NOTIONAL` (+ the `validate_order()` comment) | `config/settings.py:37-39` | Per-order notional cap; **zero readers**; its gate died in D45 | **DELETE** (D46.11) |
  | 13 | `render_fill_blip`, `BLIP_DURATION`, `_fill_effect`, `play_fill`, the `"fill"` key, `order_fill.wav`, the module-docstring bullet | `services/sound_service.py:9, 22, 75-76, 118-123, 135, 151, 170-174` | Order-fill sound; **`play_fill` has zero callers** | **DELETE** (D46.11) |
  | 14 | `IdManager.reserve` + its D26.2 docstring | `ibkr/id_manager.py:19-30` | Contiguous block for multi-leg orders; tests only | **DELETE** (D46.10) |
  | 15 | `positions.stop_loss`, `positions.take_profit` | `data/db.py:120-121` | Stop/target storage, first table | **DELETE via migration** (D46.12, A99) |
  | 16 | `trade_groups.stop_loss`, `trade_groups.take_profit` | `data/db.py:130-131` | Stop/target storage, second table | **DELETE via migration** (D46.12, A99) |
  | 17 | `Position.stop_loss/take_profit`, `TradeGroup.stop_loss/take_profit` | `data/models.py:86-87, 98-99` | Model fields | **DELETE** (D46.12, A99) |
  | 18 | `ibkr.account.Position.stop_loss/take_profit`, `build_position_from_ib(stop_loss=…, take_profit=…)` | `ibkr/account.py:32-33, 64-65, 79-80` | Third copy of the fields + its factory params | **DELETE** (D46.12, A99) |
  | 19 | `Position(stop_loss=None, take_profit=None)` + its D27.5 comment | `ui/main_window.py:3090-3094` | Live path that already cleared the values | **DELETE** (D46.12) |
  | 20 | `stop_loss, take_profit` columns / placeholders / `DO UPDATE SET` pair | `ui/main_window.py:3132-3134, 3186, 3198-3199, 3216-3217` | Upsert round-trip | **DELETE** (D46.12) |
  | 21 | `columns` tuple's two names, `row[12]/row[13]`, the `trade_group_id=row[14]` index and the two kwargs | `ui/main_window.py:3127-3166` | Bulk load (indices shift — DG85) | **DELETE + RE-INDEX** (D46.12) |
  | 22 | "the SL/TP dialog early-returns" (`:3123`), "the SL/TP dialog persists via `WHERE id=?`" (`:3096`), "the D28.6 inverse on the close-order path" (`:3065`) | `ui/main_window.py` comments | Comments asserting removed code is live | **DELETE/REWRITE** (D46.6) |
  | 23 | "order and connectivity failures are first-class… `_on_error` still routes it to the registry as Cancelled" | `ibkr/error_codes.py:14-17` | Comment naming the deleted registry route | **REWRITE comment only** (D46.6) — the code stays (item R3) |
  | 24 | "The Active Trader panel (DOM ladder + order-entry ticket)… are removed" / "the order path is gone" | `ui/main_window.py:442-443, 612` | Historical comments recording a removal | **RETAIN** — they describe what is *gone*; no live claim (D46.6) |
  | 25 | Test book: `test_order_builders.py` (17), registry cases of `test_order_rejections.py`, `test_stop_loss_target.py` (3), `TestFillBlip` (2), the `OrderRateLimiter` case, the four `test_account` kwargs + 2 asserts, `test_strategy_detection` kwargs, three SQL seeders, `test_ui_smoke`'s `UserOrder`, the ten `_SURVIVORS`/forbidden entries | `tests/*` | Assertions on the removed surface | **DELETE/REDUCE/REPOINT** (D46.5) |

  **RETAIN — general code that merely carries an order name (cutting any of these breaks something the app still
  does; each entry is here so a symbol scan cannot mistake it for residue):**

  | # | Symbol(s) | Where | Why it looks order-related | Why it stays |
  |---|---|---|---|---|
  | R1 | `_on_error`'s final `status_bar.showMessage(f"Error [{code}]: {string}", 8000)` | `ui/main_window.py:1550` | The **only** place 201/103/202 appear | **Every** non-session TWS error ends here; `AC-D46.3`'s surface (A100) |
  | R2 | `IBApiClient.error` (`severity != 'info'` gate, `error_msg.emit`) + `IBBridge.error_msg` | `ibkr/client.py:195-246`, `ibkr/bridge.py` | Carries `advancedOrderRejectJson` | General error entry point for all TWS errors (A100) |
  | R3 | `classify_error` (+ its 201/103/202 classification) | `ibkr/error_codes.py:1-27` | Names order codes in a comment | Severity gate for **every** TWS error; 202 must stay `warning` (A100) |
  | R4 | `advancedOrderRejectJson` parameter | `ibkr/client.py:199-221` | Literally "Order" | Part of the IB 5-arg `error` callback signature — not app order code (DG83) |
  | R5 | `IBApiClient.nextValidId` + `IdManager.set_next_valid_id` | `ibkr/client.py:182-193`, `ibkr/id_manager.py:8-11` | IBKR's order-ID callback | The **CONNECTED** transition + reconnect reset + disconnect-class clear; driven by D40/D25 tests; name is IBKR-mandated (A102, DG82) |
  | R6 | `IdManager` (module), `get_id`, `id_manager` singleton | `ibkr/id_manager.py:1-33` | Its neighbour `reserve()` goes | `get_id()` allocates **market-data / realtime reqIds** (`market_data.py:42,74,90,103`, `realtime_bars.py:31`) (A101) |
  | R7 | `PacingManager`, `PacingExceeded`, `pacing_manager` | `ibkr/pacing.py` | Sits beside `OrderRateLimiter` | Historical/realtime pacing — the chart's data path |
  | R8 | `order blocks`, `_render_order_blocks`, `orderBlocks` | `services/ict_service.py:114-159, 258`, `ui/overlays/ict_overlay.py:4, 27, 44` | The word "order" | ICT **price-structure** concept (order blocks, fair-value gaps) — not a trading order |
  | R9 | `sort_order` | `data/db.py:48, 249-312`, `ui/watchlist_panel.py` | The word "order" | Watchlist sequencing column (false positive) |
  | R10 | `TradeGroup`, `trade_group_id`, strategy grouping | `data/models.py`, `ui/active_portfolio_panel.py` | Historically carried stop/target | Display-only strategy grouping; **only** its four stop/target fields go (A99) |
  | R11 | `Position`, `positions` table, Portfolio view | `data/models.py`, `data/db.py`, `ui/active_portfolio_panel.py` | Holds the removed columns | The D45 view-only portfolio readout — still required |
  | R12 | `render_alarm_chime`, `play_alarm`, `ensure_sound_files`'s `"alarm"` key | `services/sound_service.py` | Shares the module with the fill blip | D21 alarms' sound |
- **Scope — KEEP (deliberate; MUST NOT be removed with the above):**
  - **The generic error path** — items **R1–R3**: `_on_error`'s session routing and its final
    `status_bar.showMessage(f"Error [{code}]: {string}", 8000)`; `IBApiClient.error` (`classify_error` gating plus
    the D40.1 `502` backoff suppression); `ibkr/error_codes.py::classify_error`; the `error_msg` signal.
    **201/103/202 keep surfacing through this path** (`AC-D46.3`, now owner-confirmed).
  - **`ibkr/id_manager.py` minus `reserve`** (**R5, R6**) — evidence in the observations above; `reserve` alone goes.
  - **`nextValidId` / `set_next_valid_id`** (**R5**) — the connection hook, not an order path.
  - **`advancedOrderRejectJson`** (**R4**) — an IB signature parameter, not app code.
  - **ICT order blocks** (**R8**), **`sort_order`** (**R9**) — false positives, documented so no worker "tidies" them.
  - The fail-fast port check, the connection badge, the no-test-transmits rule, `PacingExceeded` /
    `pacing_manager`, the D38 dividend path, D39, the chart, alarms, drawings, studies, pop-outs and D44 — all
    untouched.
- **Owner-accepted consequences (stated plainly, not implied):**
  1. **The app no longer observes order lifecycle events at all.** It will not know that an order filled, was
     rejected or was cancelled; the **status bar** is the only trace (an 8-second line carrying TWS's own text, no
     order identity, no history). The owner keeps watching order state in TWS. Accepted because the app never
     places an order, so it holds no order it could reflect (R77).
  2. **The order-error wording shrinks to what TWS says.** The app contributes no "Rejected"/"Cancelled" verdict,
     no `Order #<id>` prefix and no 12-second duration. **201/103/202 still surface** — code plus TWS message — but
     a user comparing with the old (unreachable) wording sees a plainer line (A93, owner-confirmed by Q57).
  3. **Two same-named `UserOrder` classes disappear** — the module's copy with the file, `data/models.py`'s unused
     copy per A96 (owner-confirmed by Q58). Nothing else in the repo reads either.
  4. **The suite's meaning shrinks again, and the book is recorded.** `tests/test_order_builders.py` is
     **deleted** (17 cases); `tests/test_order_rejections.py` keeps **3 of 5** in repointed form plus one added
     per-code surfacing case; `tests/test_stop_loss_target.py` is **deleted** (3 cases); the fill-blip and
     order-limiter cases go. A green suite now proves less about order construction and stop/target storage — which
     is the point: neither exists any more (R80).
  5. **`ibkr/orders.py` cannot be "restored" as a dormant helper.** D45 left it "unreferenced but retained"; D46
     makes the absence explicit, so a future reconnection needs a **new requirement**, not an un-comment (R79).
  6. **A destructive schema step runs on the owner's real database at app launch (A99).** The two tables lose two
     columns each. **What is destroyed is nothing that survived:** per ESC-060 the values were already cleared by
     the first live update of any row, and no setter existed after D45, so the columns could only ever hold `NULL`.
     **What must not be destroyed is a row** — the migration must preserve every `positions` and `trade_groups` row,
     `idx_positions_symbol_con_id` and the `trade_group_id` foreign key (D46.12, R82).
- **Requirements (final):**
  - **D46.1 — the module is gone.** `ibkr/orders.py` does not exist; `import ibkr.orders` fails; no module under
    `ui/ services/ data/ ibkr/ config/ main.py` imports it or names `Orders`, `market_order`, `limit_order`,
    `stop_order`, `bracket_order`, `order_registry`, `UserOrder` or the `orders` singleton. (Unchanged from the
    original scope; the scan list is extended by D46.9/D46.11.)
  - **D46.2 — the observation chain is gone.** No `order_status` / `open_order` / `exec_details` signal on
    `IBBridge`; **no repo-defined** `EWrapper` override for `orderStatus` / `openOrder` / `execDetails` on
    `IBApiClient` (the inherited `EWrapper` no-ops are what remains — see `AC-D46.2`'s restated measurable); no
    `_on_open_order` / `_on_order_status` / `_on_exec_details` / `_update_order_status` / `_on_order_error` on
    `MainWindow`; and `_on_error` contains no registry lookup (A92, owner-confirmed).
  - **D46.3 — TWS errors still surface (the owner's constraint).** An error carrying **201**, **103** or **202**
    still produces the status-bar line `Error [<code>]: <TWS's own message>` on the non-session path, for
    **8000 ms** — **exactly as today** — and a test proves it per code. The app adds no order identity and no
    verdict of its own; the codes' severity classification (`201/103` fatal, `202` warning) and the
    `severity != 'info'` emission gate are **unchanged** (A93, owner-confirmed).
  - **D46.4 — no order interaction is introduced.** Zero `placeOrder` / `cancelOrder` / `reqGlobalCancel` call sites
    remain; D45's static scan and mocked-client walkthrough stay green and are **strengthened** by D46 — the
    removed names move from the survivor allow-list to the **forbidden** set.
  - **D46.5 — the suite is green with exactly the recorded test book.** Deleted: `tests/test_order_builders.py`,
    `tests/test_stop_loss_target.py`. Reduced/repointed: `tests/test_order_rejections.py` (5 → 3 cases **plus the
    added per-code surfacing case**, per RG-D46-1), `tests/test_d28_pacing.py` (`OrderRateLimiter` case and import),
    `tests/test_sound_service.py` (`TestFillBlip` (2 cases) + the `render_fill_blip` use in `TestWavOutput` + the `paths["fill"]` `KeyError` site — 3 sites, RG-D46-5), `tests/conftest.py` (the two `order_limiter` resets). Adjusted: `tests/test_d45_removal.py` (four sub-edits across two waves: the allow-list shrink + token migration + absence pools + end-state test and its prose, RG-D46-5), `tests/test_ui_smoke.py` (`UserOrder` `hasattr` dropped), `tests/test_account.py`,
    `tests/test_strategy_detection.py`, `tests/test_d27_position_id.py` (raw-SQL seeder: 11 names / 11 `?` / 11 values → 9 / 9 / 9, RG-D46-5),
    `tests/test_d27_account_partial_window.py`, `tests/test_d27_account_scoping.py` (the column names; same 11→9 seeder shape).
    `tests/test_id_manager.py` **keeps three, rewrites two** (RG-D46-4). **No other test file changes.**
  - **D46.6 — the prose matches the tree.** `docs/codebase-map.md` no longer says `ibkr/orders.py` is retained /
    NOT to be deleted and no longer lists the observers as retained; `classify_error`'s comment no longer claims
    `_on_error` "still routes it to the registry as Cancelled"; `MAX_ORDER_NOTIONAL`'s `validate_order()` comment,
    `sound_service`'s order-fill docstring bullet and the `_on_position_end` / `_persist_position` "SL/TP dialog"
    comments are gone or rewritten; the surviving test docstrings name the status bar as the surface; no
    user-facing doc mentions the module, an order registry *or* retained stop/target columns (D46.13).
  - **D46.7 — history preserved.** `### D45`, `### D41`, `### D26` and the D45 register stay, with explicit
    **reversed-by / superseded-by D46** notes on A80/A90/A87/A97 and the codebase-map claims; the
    **Existing Repository marker sentence and Current Tech Stack are unchanged**.
  - **D46.8 — no second `UserOrder` (now unconditional).** `data/models.py` defines **no** `UserOrder`,
    `tests/test_ui_smoke.py` asserts `Position` / `Drawing` only, and `from data.models import UserOrder` raises
    `ImportError` (A96, owner-confirmed by Q58).
  - **D46.9 — the inventory is the spec, and it is closed.** Every identifier the inventory lists under **DELETE**
    is absent from `ui/ services/ data/ ibkr/ config/ main.py` and from the surviving tests; every identifier under
    **RETAIN** is still present and still has its documented consumer. **No live order-named symbol/identifier exists outside those
    two sets (RG-D46-3).** The two documented non-violations are the D41 historical guard list (`tests/test_d41_removal.py:97`, kept as a guard, not a live symbol) and the `ibkr/bridge.py:42` `# Account & Orders` section comment over the retained signals. Any item that is genuinely ambiguous is recorded in `design_gaps.md` (DG82–DG87) **before** it is
    deleted, never guessed at build time (A103).
  - **D46.10 — `IdManager` keeps its reqId allocator and loses `reserve`.** `IdManager`, `get_id`,
    `set_next_valid_id` and the `id_manager` singleton remain and keep their market-data/realtime callers;
    `IdManager.reserve` and its D26.2 docstring are gone; `tests/test_id_manager.py` **keeps three, rewrites two** (RG-D46-4): `test_get_id_allocates_sequentially`, `test_set_next_valid_id_equal_is_noop` and `test_concurrent_allocations_never_duplicate` survive; the four pure
    `reserve` cases (`test_reserve_returns_contiguous_block`, `test_reserve_never_overlaps_later_allocations`,
    `test_reserve_one_matches_get_id_semantics`, `test_reserve_rejects_non_positive`) are deleted, and **two** cases are rewritten without `reserve` — `test_set_next_valid_id_still_monotonic_with_reserve` (its monotonic assertion is about `set_next_valid_id`, which stays) and `test_concurrent_allocations_never_duplicate` (its `reserve` block removed, `8 * 203` → `8 * 200`) (A101).
  - **D46.11 — the zero-consumer order utilities are gone.** `OrderRateLimiter` and `order_limiter` do not exist;
    `MAX_ORDER_NOTIONAL` does not exist; `render_fill_blip`, `BLIP_DURATION`, `SoundService._fill_effect`,
    `SoundService.play_fill`, the `"fill"` key of `ensure_sound_files` and the `order_fill.wav` write do not exist;
    the alarm chime path is untouched and still played by the D21 alarm.
  - **D46.12 — the stop/target storage is gone (reverses A87; the first destructive schema step).** **End state,
    not mechanism:** `PRAGMA table_info(positions)` and `PRAGMA table_info(trade_groups)` return **no**
    `stop_loss` and **no** `take_profit`; `data/models.py::Position` / `TradeGroup` and `ibkr/account.py::Position`
    define neither field; `build_position_from_ib` takes neither; `_persist_position`, `_upsert_position` and
    `_on_position_end` name neither; no production or test SQL names either; the Portfolio table stays the
    **8 columns** of `AC-D45.10` (its UI half stands unchanged). **Constraints on the mechanism (Plan's choice):**
    idempotent on a fresh DB (where `CREATE TABLE IF NOT EXISTS` already omits the columns — so a naive
    `ALTER TABLE … DROP COLUMN` must be guarded by `_table_columns()`, the helper that already exists) and on every
    subsequent open; **every row preserved** in both tables; `idx_positions_symbol_con_id` and the
    `trade_group_id` foreign key preserved; ordered inside `_migrate_schema()` after the table's creation/index and
    before any read; crash-safe in the same sense as the `bars` rebuild (`data/db.py:203-236`) if a rebuild is
    chosen instead of `ALTER TABLE … DROP COLUMN` (this env is SQLite **≥ 3.35** — the app measures 3.53.1 — so both are available; RG-D46-6).
  - **D46.13 — the document trail reads kept → cleared → dropped, with no two live claims.** Given the repository,
    Then `USAGE.txt`, `usage.md`, `docs/codebase-map.md`, `docs/architecture.md`, `docs/plan.md` and
    `requirements.md` contain **no live statement** that the `stop_loss` / `take_profit` columns or fields are
    "kept (no migration)", "retained", "unchanged" or that a pre-D46 database "opens unchanged with its stored
    stop/target values"; each corrected site states the final end state, and the earlier ESC-060 wording ("kept,
    values cleared by the next live update") is recorded as **superseded by D46 / A99** so the trail is readable
    in one direction. Historical D45 text is kept verbatim behind that supersession note (A99, DG84).
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D46.1 (module absent; no importers)** Given the repository, Then `ibkr/orders.py` does not exist,
    `import ibkr.orders` raises `ModuleNotFoundError`, and a static scan of `ui/ services/ data/ ibkr/ config/ main.py`
    finds none of `ibkr.orders`, `order_registry`, `Orders(`, `market_order`, `limit_order`, `stop_order`,
    `bracket_order`, `UserOrder`; and no production module imports `ibapi.order`. (Measurable:
    `Path("ibkr/orders.py").exists() is False`; `pytest.raises(ModuleNotFoundError)` on the import; an identifier
    scan over the production packages returns an empty set.)
  - **AC-D46.2 (chain absent — measurable restated per RG-D46-2)** Given `MainWindow`, Then it has **no**
    `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_update_order_status`, `_on_order_error` attribute;
    **`IBBridge`** (the real class name) has no `order_status`, `open_order`, `exec_details` signal; `IBApiClient`
    defines **no** override for `orderStatus` / `openOrder` / `execDetails`; and `_on_error`'s source names neither
    `order_registry` nor `_on_order_error`. (Measurable: `hasattr` checks for the five `MainWindow` members;
    `hasattr(IBBridge, "order_status") is False` (and the other two); **`"orderStatus" not in
    IBApiClient.__dict__`** (and the other two) — **not** `hasattr`, which is `True` before *and* after because
    `ibapi.wrapper.EWrapper` defines all three as no-op stubs (verified in `.venv`); a token scan of the three
    modules.)
  - **AC-D46.3 (201/103/202 still surface — the owner's constraint)** Given a `MainWindow` with a mocked client and
    no live session reqId matching the id, When `win._on_error(reqId=<id>, errorCode=201,
    errorString="Order rejected - reason: price violates tick")` is called — and likewise for **103** and **202** —
    Then the status-bar message contains the code **and** TWS's own text (e.g. `Error [201]: Order rejected - reason:
    price violates tick`, `Error [103]: Duplicate order id`, `Error [202]: Order Canceled - reason:`), the message is
    **not** empty, and nothing raises. The three codes are still emitted by `IBApiClient.error` because
    `classify_error(201) == classify_error(103) == "fatal"` and `classify_error(202) == "warning"` — none `"info"`.
    (Measurable: three parametrised offscreen cases asserting `status_bar.currentMessage()` contains `[201]` /
    `[103]` / `[202]` and the TWS string; the `classify_error` assertions retained.)
  - **AC-D46.4 (no order interaction; D45's guard strengthened)** Given the change, Then a static scan of `ui/`
    finds **zero** `placeOrder` / `cancelOrder` / `reqGlobalCancel`, the mocked-client walkthrough still reports all
    three call counts `0`, and `tests/test_d45_removal.py`'s survivor allow-list contains **none** of
    `order_registry`, `orders`, `UserOrder`, `_on_open_order`, `_on_order_status`, `_on_exec_details`,
    `_on_order_error`, `_update_order_status`, `order_limiter`, `MAX_ORDER_NOTIONAL` — those names are **forbidden**
    by the scan instead, while `classify_error`, `pacing_manager` and `PacingExceeded` stay survivors. (Measurable:
    the shrunk `_SURVIVORS` set; the extended `_FORBIDDEN` tuple; the scan going red on a re-added name.)
  - **AC-D46.5 (test book + green suite)** Given the change, Then the full offscreen suite is green with exactly
    the D46.5 book: **deleted** `tests/test_order_builders.py` and `tests/test_stop_loss_target.py`; **reduced**
    `tests/test_order_rejections.py` (the two registry cases removed, `test_non_order_error_untouched` repointed at
    the generic line, both `classify_error` cases kept, **plus the parametrised per-code surfacing case added**),
    `tests/test_d28_pacing.py`, `tests/test_sound_service.py`, `tests/conftest.py`; **adjusted**
    `tests/test_d45_removal.py`, `tests/test_ui_smoke.py`, `tests/test_account.py`,
    `tests/test_strategy_detection.py`, `tests/test_d27_position_id.py`,
    `tests/test_d27_account_partial_window.py`, `tests/test_d27_account_scoping.py`. No other test file changes.
    (Measurable: `git diff --stat HEAD -- tests/`; a clean full-suite run.)
  - **AC-D46.6 (prose matches the tree)** Given the repository, Then `docs/codebase-map.md` contains no claim that
    `ibkr/orders.py` is retained / NOT to be deleted and no "retained observers" row naming the removed callbacks;
    `ibkr/error_codes.py`'s `classify_error` comment no longer says `_on_error` routes a cancelled order to a
    registry; `services/sound_service.py`'s docstring no longer advertises an order-fill tone; the
    `_on_position_end` / `_persist_position` comments no longer name the SL/TP dialog; and no `USAGE.txt` /
    `usage.md` line mentions the module, an order registry or retained stop/target columns. (Measurable: grep for
    `ibkr/orders.py`, `order registry`, `NOT be deleted`, `routes it to the registry`, `Order-fill`, `SL/TP dialog`
    over the six files.)
  - **AC-D46.7 (history preserved; marker + tech stack intact)** Given `requirements.md`, Then `### D45`, `### D41`
    and `### D26` remain, A80/A90/A87/A97 carry explicit **REVERSED by D46** notes **and keep their original
    wording**, ESC-061 is recorded moot, and the **existing-repo marker sentence + Current Tech Stack** are
    unchanged. (Measurable: the marker sentence occurs; the A80/A90/A87/A97 original text is still present beside
    each reversal; D46 is registered.)
  - **AC-D46.8 (no second `UserOrder`; smoke green)** Given the repository, Then `data/models.py` defines **no**
    `UserOrder`, `tests/test_ui_smoke.py` asserts `Position` / `Drawing` only, and `from data.models import
    UserOrder` raises `ImportError`. (Measurable: `hasattr(data.models, "UserOrder") is False`; the smoke case
    passes.)
  - **AC-D46.9 (the inventory is closed)** Given the repository, Then a static scan of
    `ui/ services/ data/ ibkr/ config/ main.py` and `tests/` for every **DELETE**-set identifier returns **only**
    the documented **RETAIN**-set survivors (`error_msg`, `classify_error`, `advancedOrderRejectJson`,
    `nextValidId`, `set_next_valid_id`, `get_id`, `id_manager`, `pacing_manager`, `PacingExceeded`,
    `order_blocks`/`_render_order_blocks`/`orderBlocks`, `sort_order`, `trade_group`/`TradeGroup`, `Position`,
    `play_alarm`, `render_alarm_chime`), and each RETAIN entry still has its named consumer. (Measurable: one
    parametrised test importing the inventory as data — a dict of name → disposition — and asserting
    `found ⊆ retained`; the Code Reviewer independently reproduces the scan and reports any name it cannot
    classify.)
  - **AC-D46.10 (`IdManager` intact minus `reserve`)** Given `ibkr.id_manager`, Then `IdManager.get_id` and
    `set_next_valid_id` exist and are still called from `ibkr/market_data.py` and `ibkr/client.py`, and
    `hasattr(IdManager, "reserve") is False`. (Measurable: the two `hasattr`s; the market-data call sites; the
    reduced `tests/test_id_manager.py` — 8 cases → 4, with the monotonic case rewritten rather than dropped.)
  - **AC-D46.11 (zero-consumer order utilities gone)** Given the repository, Then `ibkr.pacing` defines no
    `OrderRateLimiter` and no `order_limiter`, `config.settings` defines no `MAX_ORDER_NOTIONAL`,
    `services.sound_service` defines no `render_fill_blip` / `BLIP_DURATION` and `SoundService` has no
    `play_fill` / `_fill_effect`, the `"fill"` key is absent from `ensure_sound_files`' return, and
    `SoundService.play_alarm` still plays the alarm chime. (Measurable: `hasattr`/`import` checks; the surviving
    alarm test unchanged; no `order_fill.wav` is written.)
  - **AC-D46.12 (storage gone; rows preserved; Portfolio unchanged)** Given a database created **before** D46
    (both columns present, some rows), When the app opens it, Then `PRAGMA table_info(positions)` and
    `PRAGMA table_info(trade_groups)` list **no** `stop_loss` / `take_profit`, **both tables keep every row they
    had**, `idx_positions_symbol_con_id` still exists, the `trade_group_id` foreign key still resolves, and a
    **second** open is a no-op (idempotent). On a **fresh** database the schema is created without the columns and
    the migration does not raise. The Portfolio table renders the same **8** columns with Strategy/Group at
    indexes `6`/`7` and the live-update / TWS-side-close walkthrough stays green. (Measurable:
    `_table_columns("positions")` / `("trade_groups")` exclude both names; a row-count comparison before/after;
    `sqlite_master` still lists the unique index; `AC-D45.10`'s 8-column assertions unchanged; two consecutive
    `DB()` constructions on the same file.)
  - **AC-D46.13 (one-directional doc trail)** Given the six documents, Then no sentence within three lines of
    `stop_loss` / `take_profit` / `Stop/Target` claims the columns are kept, retained, unchanged or
    migration-free, and the ESC-060 wording carries a supersession note naming D46 / A99. (Measurable: grep for
    `kept`, `no migration`, `no schema change`, `retained`, `cleared`, `unchanged` near those tokens over the six
    files, with each hit either removed or reading `dropped`; the Code Reviewer reproduces the grep and reports the
    kept → cleared → dropped sequence.)
- **Supersession / reversal record (recorded, not silent):**
  - **A80 (D45) — REVERSED by A91** (recorded earlier 2026-10-25). Its "`ibkr/orders.py` may remain unreferenced"
    default is superseded; the row stays verbatim with the reversal appended.
  - **A90 (D45) — REVERSED by A92** (recorded earlier 2026-10-25, now **owner-confirmed** by Q56/Q57) — the
    observers go rather than stay inert.
  - **A87 (D45) — REVERSED by A99 (2026-10-25, Q59).** The "keep the storage, no migration" decision is superseded:
    the columns and model fields are **dropped**. A87's row stays verbatim with the reversal appended. **The trail
    is kept → cleared → dropped:** D45 kept the storage; ESC-060 (this morning) established that a live update
    **cleared** the values and the docs were corrected to say so; D46 now **drops** the storage because there is
    nothing left to preserve.
  - **A97 (D46) — REVERSED IN PART by Q59 / A101 (2026-10-25).** Its `reserve()` half is superseded (deleted); its
    `classify_error` half is **confirmed** and restated as A100. Row kept verbatim.
  - **A92 / A93 / A96 — CONFIRMED by the owner (Q56/Q57, Q57, Q58).** No longer recorded defaults.
  - **A93's premise is rejected, not its substance.** Q57 declined the *question* of restoring order-shaped wording
    rather than choosing an option: the app adds **no** order identity and **no** verdict, and the generic line
    stays. `AC-D46.3` is unchanged in substance and now owner-confirmed.
  - **D45 consequence 4's** "whether `ibkr/orders.py` is deleted or left unreferenced remains a Plan/Build choice"
    — **decided: deleted** (D45's own text is left as written; this entry is the decision of record).
  - **`AC-D45.6` / `AC-D45.10`'s retention halves — SUPERSEDED BY D46.** Their *UI* halves stand (8 columns, no
    Stop/Target header, no setters); their *storage* halves ("columns and fields retained, no migration") are
    superseded by A99/D46.12. D45's text is left as written so the reversal is visible.
  - **ESC-060's documentation half — SUPERSEDED BY D46.** Its correction ("columns kept; values cleared by the
    live update") was right when written and is now one step behind; D46.13 records the second correction. The
    **behavioural** half of ESC-060 (`_on_position_update` writes nulls) is moot — there is no column to write.
  - **ESC-061 (open BUILD escalation) — MOOT.** It asks for a module-docstring note on `ibkr/orders.py` saying it is
    retained deliberately; the module is deleted, so no note can be owed. **Recorded as superseded by D46, not
    solved** — Code Reviewer closes it as moot.
  - **DG76 — resolved** by the deletion. **DG79 / DG80 — resolved by Q58 / Q59 + A101.**
  - **`AC-D45.4` / `AC-D45.8`** — unchanged in substance; revised only where they name the observers as retained or
    allow-listed.
  - **D26.9 (`AC-D26.9`)** — its registry half is now vacuous; its **surfacing** half is carried forward as
    `AC-D46.3`.
  - **RG-D46-1 / RG-D46-2 (Validator findings, `docs/plan_notes.md`)** — both folded in: the added per-code case is
    in `D46.5`/`AC-D46.5`, and `AC-D46.2`'s measurable is restated as `__dict__` membership with the class name
    corrected to `IBBridge`.
- **Correction record (artifacts that must change — Plan / Task Manager / Build / Code Reviewer):**
  - **Plan:** supersede `docs/architecture.md` `S29` / `AR-D45-10` (the "retained, read-only, one docstring note"
    decision), refresh `docs/codebase-map.md` (remove the `ibkr/orders.py` row's "NOT orphaned and must NOT be
    deleted" claim ≈:97, the retained-observers list ≈:177-179, the "(docstring note only)" row ≈:193 and the
    module-index entry ≈:204), **re-plan P5 for the expanded scope** (the in-flight draft is stale), add the
    destructive-migration step to the architecture's data-model section and to `docs/plan.md`, and **supersede the
    stop/target retention statements** in `docs/architecture.md` (:4645, :4822, :4848, :4901, the P5 block
    :5127-5129 / :5331-5332) and `docs/plan.md` (:2004, :2551-2552, :2916, :2954-2955) so they read **dropped**.
    **ESC-061 is moot — do not implement its docstring note.**
  - **Task Manager:** enumerate the assertions invalidated **outside** the edited files (memory 2026-10-23 item 4):
    `tests/test_d45_removal.py` (`_SURVIVORS` + `_FORBIDDEN`), `tests/test_ui_smoke.py` (`UserOrder`),
    `tests/test_order_rejections.py` (imports + 2 cases + 1 added case), `tests/test_stop_loss_target.py` (whole
    file), `tests/test_account.py`, `tests/test_strategy_detection.py`, the three SQL seeders
    (`test_d27_position_id`, `test_d27_account_partial_window`, `test_d27_account_scoping`),
    `tests/test_d28_pacing.py`, `tests/test_sound_service.py`, `tests/conftest.py`. Do **not** task
    `nextValidId`/`set_next_valid_id`, `get_id`, `classify_error`, the ICT order blocks or `sort_order` (A100–A103);
    resolve symbols, not line numbers.
  - **Build:** split **by member group**, because delete-only tasks are what kill workers (memory 2026-10-15) —
    and this batch is larger than the original: (1) `ibkr/orders.py` deletion + importer cleanup;
    (2) `ibkr/client.py` overrides + `ibkr/bridge.py` signals + the three `__init__` connects (one task — a signal
    and its only connect must not be split across waves); (3) the `MainWindow` slots + `_update_order_status` +
    the `_on_error` branch; (4) the zero-consumer utilities (`pacing`, `settings`, `sound_service`, `id_manager`);
    (5) the storage migration + model/account/persistence edits (one task — schema and its readers must land
    together); (6) the stop/target test book; (7) the order test book; (8) comments/docstrings. After each file run
    a syntax/import check **and** a residue grep for `ibkr.orders`, `order_registry`, `order_status`, `open_order`,
    `exec_details`, `_on_order_status`, `_update_order_status`, `_on_order_error`, `OrderRateLimiter`,
    `order_limiter`, `MAX_ORDER_NOTIONAL`, `play_fill`, `render_fill_blip`, `reserve(`, `stop_loss`, `take_profit`.
  - **Code Reviewer:** independently reproduce `AC-D46.3` for **201, 103 and 202** — not merely "the suite is
    green" — confirm the chain's absence **by symbol and by `__dict__`/`hasattr`**, confirm `ibkr/orders.py` is
    gone with no importer, confirm the map no longer claims retention, confirm the migration preserved the row
    counts/index/FK **and** is idempotent on a second open, and confirm the doc trail reads kept → cleared →
    dropped with no surviving counter-claim.
- **Edge Cases:** an order error arriving while `_closing` is set is still dropped (unchanged); an order error whose
  numeric id coincides with a **live session reqId** takes the session error path first — **pre-existing** and
  **unchanged** by D46 (DG78); **202** is a normal cancellation, severity `warning`, so it is **not** suppressed;
  an error with `reqId = -1` still shows the generic line; a disconnected TWS keeps D40.1's `502` backoff
  suppression untouched; a stale `__pycache__/orders.*.pyc` (or `order_book.*.pyc`) cannot make
  `import ibkr.orders` succeed — CPython 3.11 does not import bare cache files (DG87); no UI ever bound to this
  chain, so saved layouts and `QSettings` are unaffected; **a pre-D46 database whose `positions` rows carry legacy
  stop/target values loses only those two values and keeps every row** (`AC-D46.12`); **a fresh database never runs
  the drop twice** (the `_table_columns()` guard); **an interrupted rebuild** must not strand a half-built table
  (the `bars` precedent's salvage branch, DG86); the Portfolio table and the strategy grouping are untouched apart
  from the two fields; a Build worker must not "tidy" `classify_error`, `nextValidId`, `id_manager`,
  `pacing_manager`, the ICT order blocks or `sort_order` while removing the order surface (A100–A103).
- **Assumptions (lite) — D46 (no blocking question remains: every default is A91–A104, and the four owner answers
  Q56–Q59 are recorded verbatim in `open_questions.md`):**
  - **A91 (reverses A80)** `ibkr/orders.py` is **DELETED in full**. Owner-requested 2026-10-25 and the batch
    confirmed. A80's "may remain unreferenced" is superseded; A80 stays verbatim so the reversal is visible.
  - **A92 (reverses A90)** the **observation chain is removed**, not kept inert: the three `EWrapper` overrides,
    the three bridge signals, the three `MainWindow` slots, `_update_order_status`, `_on_order_error` and the
    `_on_error` registry branch. Rationale: the chain's only effect is a write into a registry nothing populates,
    so it cannot change behaviour; keeping it would contradict the owner's explicit instruction. **Owner-confirmed
    by Q56/Q57** (was the recorded default).
  - **A93** 201/103/202 keep surfacing via the **existing generic line** (`Error [<code>]: <TWS message>`, 8000 ms);
    **no** order-id prefix, **no** "Rejected"/"Cancelled" verdict and **no** 12-second duration is restored.
    Rationale: that is already what the owner sees (the richer branch is unreachable), it satisfies *"TWS errors must
    still surface"* without new formatting code, and the app no longer knows which order it was. **Owner-confirmed
    by Q57** — which rejected the premise of the question rather than choosing an option (`AC-D46.3` unchanged).
  - **A94** error routing is **not** reordered: the session-reqId branch stays first, so a numeric collision between
    an orderId and a live session reqId behaves exactly as today (DG78). Rationale: D46 is a removal; changing the
    error path's ordering is a behaviour change nobody asked for.
  - **A95** `tests/test_order_rejections.py` **survives in reduced form** — file kept (renaming is churn), the two
    registry cases removed, `test_non_order_error_untouched` repointed to the generic line, both `classify_error`
    cases kept, **and the parametrised per-code surfacing case added** (RG-D46-1). Rationale: the surfacing
    assertions are exactly what `AC-D46.3` needs, and `classify_error` is **not** order-specific.
  - **A96** `data/models.py::UserOrder` is **removed**, and `tests/test_ui_smoke.py`'s
    `hasattr(data.models, "UserOrder")` assertion with it. **Owner-confirmed by Q58** (*"yes remove"*).
  - **A97** — **REVERSED IN PART.** Its `IdManager.reserve` half is superseded (A101: deleted); its
    `classify_error` severity table half is confirmed and restated as A100. Row kept verbatim with the reversal
    appended.
  - **A98** docs scope is `docs/codebase-map.md` (Plan-owned — supersede `S29`/`AR-D45-10` and the "NOT to be
    deleted" rows) plus **comment-level** fixes in `ibkr/error_codes.py`, `services/sound_service.py`, the
    `_on_position_end`/`_persist_position` comments and the surviving tests; **plus** the stop/target statements in
    `USAGE.txt` / `usage.md` (D46.13). Rationale: matches D45's A85 split — Plan owns the map/architecture, Build
    owns code comments and the two user-facing files.
  - **A99 (reverses A87)** the `positions` / `trade_groups` `stop_loss` / `take_profit` **columns are DROPPED** and
    the `Position` / `TradeGroup` / `ibkr.account.Position` model fields with them. Owner: Q59 verbatim
    *"remove everything"*, having been shown A87's retention and A97's out-of-scope note. **Why the reversal is
    safe — the honest justification, stronger than "we don't want them":** per **ESC-060** (corrected in these docs
    earlier the same day) the values were **already destroyed by the first live update** of any row —
    `_on_position_update` builds `Position(stop_loss=None, take_profit=None)` and the upsert's `DO UPDATE` writes
    both columns — and with every setter removed in D45 nothing could ever write a non-null value again. **The drop destroys nothing the app can reach (correction RG-D46-7, 2026-10-26 — the earlier "destroys nothing that survived" overstated for an inherited database): a row from a pre-D45 file that never receives another live update keeps its legacy bytes and loses them at the drop — the batch's only byte-destroying step; rows, indexes and FKs are preserved**; it removes two columns that could only hold `NULL` after one live update.
    Mechanism is Plan's (D46.12, DG86); the **end state** is fixed.
  - **A100** `classify_error` and the generic error surface **stay**: `ibkr/error_codes.py::classify_error`, the
    `error_msg` signal, `IBApiClient.error`'s `severity != 'info'` gate and the D40.1 `502` backoff suppression,
    `_on_error`'s session routing and its final `showMessage(..., 8000)`. Rationale: none of it is order-specific —
    it gates **every** TWS error — and removing it would delete the visibility the owner requires. Confirms A97's
    second half after Q59.
  - **A101** **`IdManager` stays; only `reserve()` goes.** Evidence, checked before writing it down:
    `get_id()` is called at `ibkr/market_data.py:42,74,90,103` and `ibkr/realtime_bars.py:31` (market-data and
    realtime reqIds) and `set_next_valid_id()` at `ibkr/client.py:184`, so the module is **shared, not order-only**;
    `reserve()` (`ibkr/id_manager.py:19-30`) has **tests only** — four pure `reserve` cases plus one mixed
    `set_next_valid_id` case (`tests/test_id_manager.py:10,18,32,39,56`) — and its docstring cites multi-leg orders. Deleting the module would take the chart's subscription machinery with it.
  - **A102** `IBApiClient.nextValidId` and `IdManager.set_next_valid_id` are **retained** (DG82): `nextValidId` is
    the connection-established transition and the only reconnect-success hook the app has (`ibkr/client.py:182-193`,
    driven by `tests/test_d40_tws_lifecycle.py:239,311,368,407,450` and `tests/test_d25_alarm_monitor.py:397`), and
    its name is IBKR's, not ours. The single order-semantic line inside it (the ID-counter sync) stays because it is
    what keeps the reqId allocator monotonic against TWS's own counter; only order-worded **comments** are removed.
  - **A103** **The D46 inventory is the acceptance instrument** (`AC-D46.9`): every order-named symbol is either in
    the DELETE set or in the RETAIN set with its consumer named, and anything genuinely ambiguous is recorded in
    `design_gaps.md` **before** it is touched rather than guessed at build time. This is the mechanism the Q56
    lesson asks for.
  - **A104** the expanded test book is exactly `D46.5`'s list — nothing else changes — and the two deleted suites
    (`test_order_builders.py`, `test_stop_loss_target.py`) are deleted **whole**, not trimmed.

### D47 — Migrate the chart stack to Lightweight Charts behind a `ChartView` seam (strangler; pyqtgraph retained until parity accepted) — OWNER-DIRECTED 2026-10-26 (REVERSAL of the 2026-10-16 decline)

- **Area (MIGRATE):** the chart rendering stack only — `ui/chart_panel.py` + `ui/candlestick_item.py` + `ui/drawing_overlay.py` + `ui/alarm_overlay.py` + `ui/event_marker_overlay.py` + `ui/overlays/*` + `ui/chart_mouse_router.py` + `ui/popout_window.py` (≈ 4,244 lines per the graphify-assisted 2026-10-16 assessment) and the 75 chart-adjacent test files. The Python/IBKR backend (`ibkr/`, `data/`, most of `services/`, `data/events/provider.py`'s `EventProvider` ABC) is **unchanged**.
- **Status:** **NEW / OWNER-DIRECTED 2026-10-26 — the 2026-10-16 decline is REVERSED (see the reversal record below).** The three owner approvals are verbatim: (1) reverse the decline — YES; (2) no soak, one live-session sign-off before any delete — YES; (3) Phase 0 spike as a single no-prototype exception — YES. **D1–D46 are NOT reopened** beyond the recorded supersessions/reversals. **No blocking question remains — Q61–Q63 ANSWERED 2026-10-26** (section-8 scope questions, owner-confirmed; Q60 answered-by-default YES).
- **Reported (the reversal, verbatim + record):** the owner directed all three approvals on 2026-10-26 after reviewing the updated migration plan (no soak). The 2026-10-16 Locked Decision (`docs/memory.md` 2026-10-16: *"evaluated replacing the pyqtgraph chart layer … and **declined it on 2026-10-16 — do not re-propose the migration**"*) is **SUPERSEDED BY D47**. Its rationale is kept, not rewritten: the *transport* half is cheap (`MainWindow` → `ChartPanel`: ~14 call sites, ~20 public methods; `ibkr/`/`data/`/most of `services/` renderer-agnostic), the *chart* half is not a renderer (≈ 4,244 lines; 75 of 129 test files chart-adjacent; LWC covers the candle/volume/crosshair third natively; Chromium + a JS toolchain join a pure-Python repo). What changed is the **decision**, not the analysis: the decline's own sanctioned route — *"a second chart mode behind the existing `ChartPanel` interface, ported feature-by-feature, keeping pyqtgraph until parity"* — is what D47 executes. **The original decline wording stays in `docs/memory.md`; the matching memory append is flagged for the Orchestrator** (Requirements Analyst does not own that file).
- **Owner constraints:**
  1. **The decline is reversed, not relitigated.** The graphify-assisted assessment stands; do not re-derive it.
  2. **No soak.** Cutover needs all three at once: owner acceptance **and** parity matrix all Done/accepted **and** Phase 0 perf holds. A calendar soak is explicitly declined.
  3. **One live trading session with no engine defect gates any delete**, and **pyqtgraph deletion is a separate wave on explicit owner approval only** — Phase 11 (S) does not ride along with cutover.
  4. **Phase 0 spike is a single exception to no-prototype:** `spikes/lwc/` throwaway only, proving the 9 API behaviours, with results + go/no-go gate in `docs/lwc_spike_results.md`. No other prototype is authorized.
- **Observed in repository (graphify map, 2026-10-26 — discovery input only, repo wins on conflict):** god nodes `MainWindow` (280 edges), `ChartPanel` (166), `TickerSession`, `DrawingOverlay`, `AlarmOverlay`, `ChartMouseRouter`, `CandlestickItem`; collapse/time-axis logic in `services/time_collapse_service.py` (`TimeCollapseMap` — the display-only x-remap every overlay honours); session bands in `services/session_service.py`; the bar path `MainWindow::load_chart` → `BarCache` → `MarketDataManager` → `ChartPanel.update_chart` → `_refresh_candles`. The seam (`MainWindow` → `ChartPanel`) stays the strangler boundary; `gap_is_non_trading` stays the non-trading source of truth.
- **Requirements (final):**
  - **D47.1 — the `ChartView` seam.** `ui/chart_view.py` defines the protocol; `DrawingController`/`AlarmController` keep their **exact signal signatures**; `create_chart_view(tz_offset, editable)` selects the engine on `NDT_CHART_ENGINE` (pyqtgraph default, lwc) or `QSettings`. (`AC-D47.1`.)
  - **D47.2 — the shared Qt-free `ChartModel`.** `services/chart_model.py` carries plotted-index filtering, `floor_bar_budget`, whitespace derivation, studies + `_StudyCache`, Heikin-Ashi and volume formatting. `ChartPanel` delegates with **no behaviour change** — the existing chart suites stay green throughout. (`AC-D47.2`.)
  - **D47.3 — the host is vendored and offline.** `QWebEngineView` + vendored lightweight-charts **v5.2.x** via a custom `ndt://` scheme handler registered **before** `QApplication`; an interceptor **blocks non-ndt** traffic; **no CDN/npm at runtime**; attribution kept. (`AC-D47.3`.)
  - **D47.4 — the bridge is batched and self-healing.** `QWebChannel` `LwBridge`, batched `{v:1,ops:[]}`, queue-until-ready, column arrays, ~33ms live coalesce, gestures local in JS; Python **replays after `renderProcessTerminated`**. (`AC-D47.4`.)
  - **D47.5 — time, panes and series match the app model.** Panes (v5); **logical-index** time axis + whitespace for within-session holes; `gap_is_non_trading` stays the source of truth; custom tz formatters (`local = t - offset`); per-mode series; `series.update` for the live bar. (`AC-D47.5`.)
  - **D47.6 — `barSpacing` replaces the density caps (owner-visible AC change; T10).** The library control governs inter-bar spacing; the pyqtgraph density-cap language of `AC-D6.4`/`AC-D7.1`/`AC-D9.1` is **proposed for retirement — pending Q60**. The no-overlap guarantee is restated in `barSpacing` terms (DG94). (`AC-D47.6`.)
  - **D47.7 — controls, router and drawings keep their contracts.** In-HTML controls with Python shims; Python `RouterMode` + JS mirror; drawings through a primitives library with ts-to-fractional-index; **Qt dialogs stay** (zone/horizontal-line settings, alarm edit). (`AC-D47.7`.)
  - **D47.8 — delivery in Phases 0–11, in order.** 0 spike + decision record; 1 seam+model; 2 runtime+bridge; 3 core chart XL; 4 studies; 5 interaction XL; 6 alarms; 7 drawings XL (largest); 8 overlays/markers; 9 pop-outs; 10 packaging/CI/cutover candidate; 11 removal S on owner approval. Effort S/M/L/XL as stated in the plan. (`AC-D47.8`.)
  - **D47.9 — parity is the gate, and rule 10 governs the unmeetable.** The **19-row parity matrix** (`docs/lwc_parity_matrix.md`) is **kept updated**; an AC that cannot be met on LWC is **escalated + recorded as a parity row** (never silently dropped). (`AC-D47.9`.)
  - **D47.10 — pyramid tests; the 66 files are classified.** Pure-Python tests, `node --test` JS tests, a few `@pytest.mark.webengine` cases, and the manual checklist; the 66 chart-adjacent test files are dispositioned keep/retarget/engine-specific. (`AC-D47.10`.)
  - **D47.11 — cutover and removal gates.** Cutover = owner accept **and** parity all Done/accepted **and** Phase 0 perf holds (no soak). **Removal (Phase 11) needs explicit owner approval** and is separately gated on **one live trading session with no engine defect**. (`AC-D47.6` cutover half + `AC-D47.8`.)
  - **D47.12 — out of scope stays out.** `ibkr/`, db schemas, drawing/alarm persistence, watchlist, dock, order code, the paid library, aggregation/backfill — unchanged. (`AC-D47.7` second half.)
  - **D47.13 — history preserved.** `### D41`–`### D46` stay with their reversals; the **Existing Repository marker sentence and Current Tech Stack are intact** (the stack is **extended** by the D47 row, not replaced); `ESC-061` stays moot; no D1–D46 criterion is edited except by the recorded supersessions (density caps pending Q60). (`AC-D47.9` history half.)
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D47.1 (seam selects; signatures unchanged)** Given `NDT_CHART_ENGINE` unset (or an unknown value), Then `create_chart_view(tz_offset, editable)` returns the pyqtgraph view; given `=lwc` (or the `QSettings` equivalent), it returns the LWC view; and `DrawingController`/`AlarmController` expose the exact pre-D47 signal signatures on both engines. (Measurable: factory unit cases for unset/unknown/pyqtgraph/lwc + a signal-signature assertion per controller.)
  - **AC-D47.2 (model delegates; no behaviour change)** Given any chart load, Then `ChartPanel` renders from `services/chart_model.py` with the pre-D47 pixel/logic outcomes — the full pre-D47 chart suite (candles, volume, collapse, bands, crosshair, drawings, alarms, overlays) stays green unmodified. (Measurable: the named suites green; a delegation probe for plotted-index filtering + `floor_bar_budget`.)
  - **AC-D47.3 (vendored and offline)** Given the running app, Then no chart asset loads from CDN/npm; lightweight-charts resolves to the vendored **v5.2.x** tree; the `ndt://` handler is registered before `QApplication`; and a non-`ndt` request is blocked by the interceptor. (Measurable: version pin assertion + an interceptor case for `https:`/`http:` blocked and `ndt:` allowed + attribution present.)
  - **AC-D47.4 (batched bridge; replay after crash)** Given a live session, Then transport emits batched `{v:1,ops:[]}` ops over `QWebChannel` (`LwBridge`), queues while not ready, coalesces live ticks (~33ms), and after a `renderProcessTerminated` Python replays the full op log with no duplicated or lost bars. (Measurable: batch-shape unit cases + a replay case asserting bar-identity after a simulated termination.)
  - **AC-D47.5 (time/panes/series parity)** Given identical bars in RTH and ETH, Then the LWC view shows the same sessions, whitespace-for-holes, per-mode series and tz labels (`local = t - offset`) as the pyqtgraph view, with `gap_is_non_trading` as the authority in both. (Measurable: parity-matrix time rows + a DST/session-boundary logical-index case.)
  - **AC-D47.6 (cutover gate; density-cap retirement pending Q60)** Given the cutover decision, Then it is taken only when the owner has accepted **and** every parity-matrix row reads Done/accepted (or carries a rule-10 escalation entry) **and** Phase 0 perf holds — with **no calendar soak**; and the pyqtgraph density-cap ACs (`AC-D6.4`/`AC-D7.1`/`AC-D9.1` density language) are retired for `barSpacing` only as Q60 decides. (Measurable: the matrix state + the dated owner acceptance + the Q60 answer.)
  - **AC-D47.7 (contracts kept; out-of-scope untouched)** Given the migrated app, Then zone/horizontal-line/alarm dialogs are the same Qt dialogs, `RouterMode` transitions match the pre-D47 table, and `ibkr/`, db schemas, persistence, watchlist, dock, order-code surfaces and aggregation/backfill behave exactly as before. (Measurable: dialog/router suites green + the out-of-scope residue scan clean.)
  - **AC-D47.8 (phased delivery; removal gated)** Given the plan's Phases 0–11, Then Phase 0 lands `spikes/lwc/` + `docs/lwc_spike_results.md` with a go/no-go record before Phase 1 starts; each phase's exit updates the parity matrix; and **Phase 11 executes only on explicit owner approval after one live trading session with no engine defect**. (Measurable: spike doc + gate record + the approval + the session sign-off.)
  - **AC-D47.9 (matrix current; history intact)** Given the repository, Then `docs/lwc_parity_matrix.md` lists all 19 rows with current dispositions, every unmeetable AC has an escalation + parity-row entry (rule 10), `### D41`–`### D46` and their reversals are unchanged, and the Existing Repository marker sentence + Current Tech Stack are intact. (Measurable: row count + the marker grep + the D46 reversal rows present.)
- **Supersession / reversal record (recorded, not silent):**
  - **2026-10-16 LWC decline (`docs/memory.md` Locked Decision) — REVERSED by D47 (2026-10-26, owner: *"Reverse the 2026-10-16 decision declining the LWC migration"*).** The analysis stands; the decision is superseded. Original wording kept in `docs/memory.md`; the matching memory append is flagged for the Orchestrator.
  - **`AC-D6.4` / `AC-D7.1` / `AC-D9.1` density-cap language — PROPOSED for retirement by D47.6/T10, pending Q60.** Not yet superseded; the pyqtgraph engine still satisfies them until cutover. (DG94 records the mechanics.)
  - **Non-Goals "Changing the tech stack" — REVISED (dated 2026-10-26)** for the chart renderer only; pyqtgraph retention + gated removal are part of the revision.
  - **RG-D46-2 — applied:** `AC-D46.2`'s measurable is the `__dict__`-membership form with the `IBBridge` name (plan `AP-D46-14` recorded the substitution; this revision makes the requirements-side restatement).
  - **RG-D46-3 — applied:** `D46.9`'s "no order-named symbol exists outside those two sets" is scoped to **live symbols/identifiers** — the D41 historical guard list (`tests/test_d41_removal.py:97`) and the `ibkr/bridge.py:42` section comment are retained-and-documented, not violations.
  - **RG-D46-4 — applied:** `D46.10`/`AC-D46.10` read "**keeps three, rewrites two**" — the concurrent case is rewritten without its `reserve` block (`8 * 203` → `8 * 200`), alongside the rewritten monotonic case.
  - **RG-D46-5 — applied:** `D46.5`/`A104` fold the four measured sites (sound-service `"fill"` `KeyError` ×3, the id-manager concurrent rewrite, seeder 11→9 placeholders, `test_d45_removal.py` four sub-edits across two waves); the plan's book stays operative.
  - **RG-D46-6 — applied:** `D46.12` states SQLite **≥ 3.35** (the app measures 3.53.1), not 3.54.0.
  - **RG-D46-7 — applied:** `A99`'s justification reads "**destroys nothing the app can reach**" with the byte-level truth (a row that never updates again keeps its legacy bytes and loses them at the drop) — the drop stays the batch's only byte-destroying step.
  - **RG-D46-9 — applied:** the `:5548` batch-summary line ("retained stop/target storage (A87 …)") and the `:5521` summary line ("inert inbound order callbacks (A90)") carry explicit **SUPERSEDED BY D46** notes below; the seven cited sites are now all annotated or reversed in place.
- **Correction record (artifacts that must change — Plan / Task Manager / Build / Code Reviewer):**
  - **Plan:** ingest the attached migration plan whole (do not re-derive the seam/model/bridge/panes); own `docs/lwc_parity_matrix.md` (19 rows, kept updated) and the Phase 0 go/no-go record; state the `barSpacing` restatement of the no-overlap guarantee (DG94) for Q60; name the per-pop-out memory cap, bridge backpressure counters and focus/keyboard forwarding (DG88–DG96 are Plan details); refresh `docs/codebase-map.md` for `ui/chart_view.py` + `services/chart_model.py` without dropping the pyqtgraph rows until Phase 11.
  - **Task Manager:** phase the graph as 0–11 in delivery order (Phase 0 spike first, with the results doc as its exit); classify the 66 chart-adjacent test files keep/retarget/engine-specific per the plan; assign T10 (density-cap AC retirement) to land only with the Q60 answer; never task pyqtgraph deletion before the Phase 11 gate (`AC-D47.8`).
  - **Build:** keep `spikes/lwc/` throwaway (never imported by production or tests); register the `ndt://` handler before `QApplication`; keep the interceptor deny-default; replay the full op log after `renderProcessTerminated`; run `node --test` for the JS side and mark webengine cases `@pytest.mark.webengine` (skipped, never red, where no engine exists).
  - **Code Reviewer:** verify parity per row (not "suite green" alone); reproduce `AC-D47.3` offline (airplane test) and `AC-D47.4` replay; confirm no CDN/npm import survives; confirm pyqtgraph still fully present at cutover-candidate time.
- **Edge Cases:** `NDT_CHART_ENGINE` set to an unknown value falls back to pyqtgraph (never blank); the spike directory imported by production code fails the build; a parity row regressing after Done re-opens the row (never the D1–D46 ACs); webengine missing offscreen → skip + manual checklist (DG88); an unmeetable AC without an escalation + parity-row entry fails review (rule 10).
- **Assumptions (D47 — Q60 answered-by-default YES; Q61–Q63 ANSWERED 2026-10-26, owner-confirmed, A105–A112):**
  - **A105** Phase 0 is a throwaway spike in `spikes/lwc/` only — nothing there is imported by production or tests, and its only deliverables are the 9-API-behaviour proof + `docs/lwc_spike_results.md` with a go/no-go gate. Owner-authorized 2026-10-26 (single no-prototype exception).
  - **A106 (answered-by-default 2026-10-26, Q60 — YES)** `barSpacing` replaces the pyqtgraph density-cap ACs (`AC-D6.4`/`AC-D7.1`/`AC-D9.1` density language); the no-overlap guarantee is restated in `barSpacing` terms (DG94). Rationale: the plan states the replacement as an owner-visible AC change (Q60 stays answered-by-default YES).
  - **A107 (owner-confirmed 2026-10-26, Q62)** the pop-out cap stays at the D24 **10**. Rationale: preserves the approved D24 behaviour; raising it needs the memory/bridge evidence in DG90. Owner verbatim: "Keep 10 (Recommended)"; Phase 9 verifies 1, 3, 6 against it.
  - **A108 (owner-confirmed 2026-10-26, Q63)** the LWC crosshair **drifts** to the library-native crosshair + axis label (no exact-pill custom primitives); D2/Q33 stands only where still applicable. Rationale: pixel-exact reproduction needs a custom primitive driven per move; drift is the library-native outcome. Owner verbatim: "Accept drift (Recommended)".
  - **A109 (owner-confirmed 2026-10-26, Q61 — measure-first)** no fixed `.app` size budget; Plan measures the Phase 0 size delta and reports, the owner sets the budget from the numbers; note whether the current signing flow covers the Chromium/vendored tree as a Phase 0 finding. Rationale: bundle size + signing identity are release facts. Owner verbatim: "Measure first, no fixed budget".
  - **A110** webengine cases are `@pytest.mark.webengine` and **skip (never red)** where no engine exists; the manual checklist is the gate there (DG88). Rationale: offscreen viability is unproven — a red webengine case must mean a real regression, not a missing Chromium.
  - **A111** timestamp edge cases (DST folds, session-boundary bars, ts-to-fractional-index collisions) are **DG93**, verified against both engines on the same fixtures. Rationale: logical-index parity is where silent divergence hides.
  - **A112** bridge backpressure counters, per-pop-out memory accounting and focus/keyboard forwarding are **DG91/DG90/DG92** — instrumented from Phase 2, not retrofitted. Rationale: queue-until-ready + replay can mask growth until it hurts.

### D48 — Add `1 week` (2Y) and `1 month` (10Y) timeframes — OWNER-REQUESTED 2026-10-28 (P8 lite)

- **Area (ADD):** the timeframe surface only — `ibkr/market_data.py::TIMEFRAME_CONFIG` (+2 rows), `data/bar_aggregator.py` (+ weekly/monthly bucketing), `services/backfill_service.py` (planner rows for the two new spans; no detection-logic change), the timeframe picker (`tf_combo` +2 entries), and the forming-bar priming table (`AC-D27.9`/D43 gains two rows — Plan detail, DG98). Nothing else moves: cache schema, session math, bands, collapse, pop-outs, studies, drawings, alarms are unchanged.
- **Status:** **NEW / OWNER-REQUESTED 2026-10-28 — P8 lite (no question round; every default is A113–A120).** **D1–D47 are NOT reopened** beyond the recorded timeframe-enumeration extension below.
- **Reported (verbatim intent):** weekly bars covering 2 years and monthly bars covering 10 years (IBKR bar sizes `1 week` / `1 month` exist; today's picker stops at `1 day`).
- **Requirements (final):**
  - **D48.1 — bar-size/duration mapping.** `TIMEFRAME_CONFIG` gains exactly two rows: `1 week` → `bar_size='1 week'`, `duration='2 Y'`; `1 month` → `bar_size='1 month'`, `duration='10 Y'`. (`AC-D48.1`.)
  - **D48.2 — aggregator period support.** Weekly buckets open **Monday 00:00 America/New_York** (A114); monthly buckets open on the **calendar-month boundary** (A115). Live forming-bar aggregation follows the same buckets. (`AC-D48.2`.)
  - **D48.3 — planner/backfill treatment.** Weekly/monthly loads request the configured durations (chunked per the existing `TIMEFRAME_CONFIG`-stepping rule when one window cannot cover the span); the **`AC-D16.8` 30-session intraday floor does NOT extend** to weekly/monthly (as with `1 day` — A117); `find_missing_spans` day-presence already operates at bar granularity and needs no logic change. (`AC-D48.3`.)
  - **D48.4 — RTH/ETH irrelevance.** `useRTH`/`ext_hours` is a **no-op** for `1 week`/`1 month`: identical bars under both modes with one shared cache treatment (A118); D1 session bands and D21.4 collapse stay **no-ops** (as for `1 day`). (`AC-D48.4`.)
  - **D48.5 — UI picker inclusion.** The timeframe picker gains `1 week` and `1 month` entries (after `1 day`); selection, persistence, pop-out and drawing/alarm-visibility behaviour treat them as ordinary timeframes (A119–A120). (`AC-D48.5`.)
  - **D48.6 — acceptance gate.** A **standalone probe** verifies IBKR accepts both duration/bar-size combos (no 321-class rejection), **and** the full offscreen suite stays green. (`AC-D48.6`.)
  - **D48.7 — history preserved.** `### D41`–`### D47` and their reversals stay; the Existing Repository marker sentence + Current Tech Stack are intact; the only edits to pre-D48 criteria are the recorded timeframe-enumeration extension (`AC-D16.1`'s "all six timeframes" now reads eight; the D43/Q53 `AC-D27.9` per-span table gains two rows). (`AC-D48.7`.)
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D48.1 (mapping)** Given `TIMEFRAME_CONFIG`, Then it contains `1 week` (`1 week` / `2 Y`) and `1 month` (`1 month` / `10 Y`) and no other row changes. (Measurable: config assertion on both rows.)
  - **AC-D48.2 (aggregation)** Given daily bars across a DST fold, a February, and a Dec/Jan boundary, Then weekly buckets open Monday ET and monthly buckets open on the calendar-month boundary ET. (Measurable: unit cases incl. DST fold, Feb, cross-year week.)
  - **AC-D48.3 (planner/backfill)** Given a weekly/monthly load, Then the planner requests the configured duration (chunked as needed), never applies the `AC-D16.8` floor, and detects missing spans at bar granularity. (Measurable: planner cases for full-span, chunked, and hole-in-middle.)
  - **AC-D48.4 (RTH/ETH no-op)** Given either new timeframe, Then RTH and ETH loads return identical bars, and no session band or collapse is applied. (Measurable: mode-parity case + band/collapse-absent assertions.)
  - **AC-D48.5 (picker)** Given the toolbar picker, Then `1 week` and `1 month` follow `1 day` and select/load/persist like every other timeframe. (Measurable: picker-order case + select-restore case.)
  - **AC-D48.6 (probe + suite)** Given live TWS (or the standalone probe harness), Then both IBKR requests complete without a 321-class rejection, and the full offscreen suite is green. (Measurable: probe record + suite count.)
  - **AC-D48.7 (history intact)** Given `requirements.md`, Then `### D41`–`### D47` with reversals, the marker sentence and the Current Tech Stack are unchanged, and the only pre-D48 wording touched is the recorded enumeration extension. (Measurable: marker grep + the `### D4[1-7]` sections present.)
- **Assumptions (lite) — D48 (no blocking question remains: every default is A113–A120, logged below in the Assumptions Log):**
  - **A113** the two `TIMEFRAME_CONFIG` rows read exactly `1 week` → `1 week` / `2 Y` and `1 month` → `1 month` / `10 Y` (owner-specified spans).
  - **A114** weekly buckets open **Monday 00:00 America/New_York** (the conventional US-equity week).
  - **A115** monthly buckets open on the **calendar-month boundary**; a nominal 30-day (2592000 s) period is used only where an API demands fixed seconds, never for bucketing.
  - **A116** durations use IBKR **year units** (`2 Y`, `10 Y`), not day counts.
  - **A117** the `AC-D16.8` floor stays intraday-only; `find_missing_spans` needs no logic change (bar-granular already).
  - **A118** RTH/ETH is a no-op for weekly/monthly with one shared cache treatment; bands and collapse stay no-ops.
  - **A119** picker labels read `1 week` / `1 month`, ordered immediately after `1 day`.
  - **A120** the new timeframes default to **visible** in drawing/alarm visibility grids; the 8-row grid gains rows (DG97).
- **Edge Cases:** covered by Journey 41 (DST-fold week, short months, holiday weeks, cross-year weeks, disconnected load).

### D49 — Pop-out robustness: restore, attach, host-failure signal, drawing fan-out, hold-count verification — OWNER-ORDERED 2026-10-28 (5 findings, nothing dropped)

- **Area:** the pop-out lifecycle only — `ui/main_window.py::_restore_popouts` (+ the restore data path), `ui/popout_window.py::attach` (+ retry/close paths), `ui/ticker_session.py::attach_view` / `ensure_rt_subscribed` / `release_rt` / `sync_drawings_to_views`. D24's pop-out criteria stand and are **not** reopened; D49 corrects the implementation paths behind them.
- **Status:** **NEW / OWNER-ORDERED 2026-10-28; EXTENDED 2026-10-29 with D49.6 (timezone handoff).** All five trace findings plus the timezone handoff are in scope; none is dropped. **D1–D48 are NOT reopened.**
- **Source (read-only):** `POPOUT_CHART_CODE_TRACE_REPORT.txt` (repo root) — static code trace, no tests run. Finding numbers below are the report's Findings 1–5.
- **Requirements (final):**
  - **D49.1 — restore through the data path (finding 1, High).** Restoring a saved pop-out for a symbol with no in-memory session MUST load cached bars, create the timeframe's `BarAggregator`, and subscribe realtime — using the existing history/backfill/pacing path where cache coverage is incomplete — so the window neither opens empty nor misses chart-bar updates. Reproduce-first: the empty/stale restore is pinned by a failing test before the fix. (`AC-D49.1`.)
  - **D49.2 — transactional attach (finding 2, Medium).** `attach()` MUST be atomic in effect: on ANY failure (sync raise, registration/save raise), it disconnects connected signals, detaches the view, releases ONLY a realtime hold it actually acquired (explicit acquisition-state tracking — never another view's hold), unregisters the pop-out, and releases its resources, leaving no stale view in the session and no registered-but-never-shown window. (`AC-D49.2`.)
  - **D49.3 — host-startup error state (finding 3, Medium).** If the chart-host cannot start, the pop-out MUST show a clear, visible error state/status message — unambiguous and distinct from "no data" — while retaining the diagnostic log at its current level. The main-window ESC-070 fix is the behavioral model; this is a different site. Exact copy/layout is owner-confirmed 2026-10-28 (A124; Q64 answered). (`AC-D49.3`.)
  - **D49.4 — single drawing fan-out (finding 4, Low).** Drawing changes/reloads perform the all-view synchronization ONCE at the change point; each pop-out's `drawings_changed` handler stays a notification (or updates only its receiving view). Perf-work order: pin the current behavior in tests FIRST (fan-out count + update semantics), THEN de-duplicate without changing update semantics. (`AC-D49.4`.)
  - **D49.5 — verify-first hold count (finding 5, observation).** FIRST verify whether the shared realtime hold count has a LASTING effect (suspect: the main-chart same-symbol reload path re-subscribing without releasing the previous hold). Fix — idempotent per-owner acquire/release (owners: main chart, each pop-out, alarm monitor) — ONLY if a lasting effect is confirmed; otherwise record the verification and CLOSE D49.5 with no code change. No code is built on an unproven premise. (`AC-D49.5`.)
  - **D49.6 — timezone handoff on pop-out create + persist/restore (NEW 2026-10-29, OWNER-ORDERED).** Pop-out creation MUST pass the main chart's current timezone offset into the new view (the hardcoded `tz_offset=0.0` is removed at the creation call site) and the offset MUST be persisted with the saved pop-out set and restored with it, so a restored window renders the same time labels for the same bars as the main chart. (`AC-D49.6`.)
  - **D49.7 — history preserved (renumbered 2026-10-29 to free D49.6 for the timezone handoff; no criterion changed).** `### D41`–`### D48` with reversals stay; the Existing Repository marker sentence + Current Tech Stack are intact; no pre-D49 criterion is reworded. (`AC-D49.7`.)
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D49.1 (restore)** Given a saved pop-out for a symbol with no in-memory session and a seeded `BarCache`, When the restore path runs offscreen, Then the window shows the cached bars, owns a timeframe aggregator, and holds a realtime subscription; an incomplete cache triggers the existing backfill/pacing path. (Measurable: reproduce-first failing test — empty session + saved pop-out → bars present + aggregator exists + subscribed; incomplete-cache case issues the backfill request.)
  - **AC-D49.2 (transactional attach)** Given each failure-injection point in `attach()` (sync raise, registration raise, save raise), When attach fails offscreen, Then the session holds no stale view, no realtime hold leaked by the failed attach (hold count unchanged unless the test itself holds one), the pop-out is unregistered, and signals are disconnected. (Measurable: per-injection-point cases asserting session-view membership, hold count, registry membership.)
  - **AC-D49.3 (error state)** Given a chart-host that raises on startup, When the pop-out opens offscreen, Then it shows the error state (not an empty chart), and the diagnostic log entry is retained. (Measurable: error-state-visible assertion + log-capture assertion; a blank chart mistaken for no-data is the rejected outcome.)
  - **AC-D49.4 (single fan-out)** Given N open pop-outs on one symbol, When drawings change, Then the all-view sync executes once per change (not N times) with end state identical to the pinned baseline. (Measurable: pinning test records fan-out count + end state first; post-fix case asserts count == 1 per change and end-state equality.)
  - **AC-D49.5 (verify-first)** Given the shared-hold lifecycle (main-chart same-symbol reload + pop-out attach/close), When the verification probe runs offscreen, Then it records whether the hold count exceeds active owners with a lasting effect (a duplicate live subscription surviving session use) or not; the idempotent per-owner fix lands ONLY on a confirmed lasting effect, otherwise the verification record closes D49.5 with no code change. (Measurable: probe record present either way; code change iff lasting effect confirmed.)
  - **AC-D49.6 (timezone handoff)** Given a main chart with a non-zero timezone offset, When a pop-out is created offscreen, Then the new view is constructed with the main chart's current offset (never the hardcoded `0.0`); Given a saved pop-out set carrying a persisted offset, When it is restored, Then the restored view carries that offset and renders identical time labels for the same bars as the main chart. (Measurable: creation case asserts the new view's `tz_offset ==` the main chart's offset with a non-zero offset configured; restore case asserts the restored view's offset plus label-equality of the same seeded bars in main vs pop-out; a pre-change save without the field falls back per A134.)
  - **AC-D49.7 (history intact — renumbered 2026-10-29; was AC-D49.6)** Given `requirements.md`, Then `### D41`–`### D48` with reversals, the marker sentence and the Current Tech Stack are unchanged, and no pre-D49 wording is touched. (Measurable: marker grep + the `### D4[1-8]` sections present.)
- **Assumptions — D49:** A121–A126 + A133–A134 (logged in the Assumptions Log; Q64–Q66 answered 2026-10-28; D49.6 asked no question — fully derivable).
- **Edge Cases:** covered by Journey 42 (main-symbol restore parity, disconnected no-op, shared-session attach failure, post-start host crash out of scope, zero-pop-out sync, zero-owner count, restored offset kept, pre-change save falls back per A134).


### D50 — Drag-editing for LWC drawings (whole-move + anchor/handle drags, handle UI, lock semantics, recolor interplay, persistence/fan-out) — OWNER-SCHEDULED 2026-10-28 (CLARIFIED AND FINALISED 2026-10-28 — Q67–Q71 answered owner-confirmed)

- **Area (EDIT):** the LWC drawing edit path only — `gestures.js` (which today has **NO** drag-initiation path), the `drag_drawing` operation surface in the view, the `PageDrawing` / `drawing_controller.created` commit surface, and the `DrawingStore` update paths. **Creation is NOT re-specified** — only the edit of already-created drawings.
- **Status:** **CLARIFIED AND FINALISED 2026-10-28 — Q67–Q71 answered** (owner-confirmed verbatim 2026-10-28: Q67 both; Q68 handles only while selected, locked offers no draggable handle; Q69 (i)+(ii)+(iii) forbidden, colour allowed; Q71 yes; Q70 = (c) Both previously recorded 2026-10-28). **D1–D49 are NOT reopened.**
- **Settled inputs (not re-asked):** the LWC primitives render path is proven working (bind fix); the `PageDrawing` / `drawing_controller.created` commit surface exists; the `DrawingStore` update paths exist (A127–A129).
- **Requirements (FINAL — Q67–Q71 answered owner-confirmed 2026-10-28):**
  - **D50.1 — edit operations per kind (SETTLED 2026-10-28, Q67 = both).** Whole-drawing move for all five kinds **plus** anchor/handle drags per kind's anchors: trendline/fibonacci/measure endpoints, zone edges/corners, horizontal price level.
  - **D50.2 — handle UI (SETTLED 2026-10-28, Q68).** Handles appear **only while their drawing is selected** and hide on deselect; a **locked drawing offers no draggable handle** (selection highlight only). Handle rendering is UI-visual, so the ESC-004 / AC-G.1 visual gate applies (confirmed reference or provisional assumption).
  - **D50.3 — lock semantics, operation-level (SETTLED 2026-10-28, Q69 = (i)+(ii)+(iii); colour allowed).** A locked drawing forbids (i) drag **initiation**, (ii) move/commit and (iii) **delete**; (iv) **colour/style change stays allowed** — including a group recolour repainting a locked member's stored colour per the settled Q70 (c) rule. Hard constraint: lock is enforced at the `drag_drawing` initiation/move surface in the view (where the operation happens), never by handle visibility alone — `gestures.js` currently has no drag-initiation path, so hiding handles there cannot be the lock.
  - **D50.4 — recolor interplay (SETTLED 2026-10-28, Q70 = (c) Both).** Owner decision: new drawings take the group colour **at creation**, stored on the drawing (**survives leave-group**); recolouring a group repaints **all current members**, updating stored colours. Consequence for drag/edit: a dragged/edited drawing keeps its own stored colour — geometry commits never overwrite colour. A group recolour applies to stored colours including a member with an in-flight drag: the drag ghost keeps the colour sampled at drag start and the stored (possibly recoloured) colour wins at commit (A132). Former members keep the colour they held when they left.
  - **D50.5 — persistence + fan-out of edited geometry (SETTLED 2026-10-28, Q71 = yes).** Every committed edit updates the store, survives session reload, and syncs to all views exactly once per change (the D49.4 single-fan-out pattern); acceptance measurable offscreen where possible (owner-confirmed).
- **Acceptance Criteria (Given/When/Then — FINAL 2026-10-28):**
  - **AC-D50.1 (FINAL, Q67 = both)** Given a drawing of each kind, When whole-move and per-kind anchor drags are applied (trendline/fibonacci/measure endpoints, zone edges/corners, horizontal price level), Then the committed geometry matches the drag (measurable offscreen: geometry assertions on committed coordinates).
  - **AC-D50.2 (FINAL, Q68)** Given selection-state changes, When a drawing is selected, Then its handles appear; When it is deselected, Then its handles hide; and a locked drawing offers no draggable handle (selection highlight only).
  - **AC-D50.3 (FINAL, Q69)** Given a locked drawing, When a drag is initiated at the `drag_drawing` surface, Then the attempt is refused: geometry unchanged, no store write; When delete is invoked on it, Then delete is refused; When its colour/style is changed (including group recolour), Then the change applies.
  - **AC-D50.4 (SETTLED, Q70 = (c))** Given a drawing created in a group, Then its stored colour equals the group colour at creation and survives leave-group; Given a group recolour, Then every current member's stored colour is repainted (including a member with an in-flight drag, per A132); Given a drag-edit commit, Then geometry writes and the stored colour is untouched. (Measurable offscreen: stored-colour assertions across create / leave-group / recolour / drag-commit, plus the mid-drag recolour case.)
  - **AC-D50.5 (FINAL, Q71 = yes)** Given a committed edit, When the session reloads and all views sync, Then every view shows the edited geometry with exactly one fan-out per change (offscreen-measurable: seeded store + committed coordinates + reload-restore + fan-out count).
- **Assumptions:** A127–A132 (logged below; Q70 settled, Q71 owner-confirmed 2026-10-28).
- **Risks:** R99–R101.
- **Edge Cases:** covered by Journey 43 (locked-drag no-op, mid-drag cancel, zero-view persist, group-colour per the settled (c) rule, including locked-member recolour).

Status: READY_FOR_PLAN

### D51 — Main-chart viewport follow-live: no yank to the newest bar while scrolled back — FINALISED 2026-10-29 (Q72–Q76 answered-owner-confirmed)

- **Area:** the main-chart viewport only — live bar updates, user pan/zoom, explicit Fit/reset, symbol switch and full-series replacement. Pop-outs, alarms, drawings and the data path are **not** in scope; D1–D50 are **NOT** reopened.
- **Status:** **READY_FOR_PLAN 2026-10-29 — Q72–Q76 answered-owner-confirmed.** Every requirement and AC below is **FINAL** per the recorded owner answers.
- **Requirements (FINAL 2026-10-29):**
  - **D51.1 — follow vs scrolled-back (FINAL, Q72 answered-owner-confirmed 2026-10-29).** The chart distinguishes "following the live edge" from "scrolled back" by the TradingView rule: following iff the newest bar's slot is inside the visible range (library shiftVisibleRangeOnNewBar semantic, verified in vendored 5.2.1); any user pan/zoom away means scrolled back. (`AC-D51.1`.)
  - **D51.2 — no yank while away; resume rule (FINAL, Q73(a) answered-owner-confirmed 2026-10-29).** While scrolled back, arriving live bars MUST NOT move the viewport; follow resumes only when the user pans back to the edge or invokes Fit/reset — no automatic resume on new bars. (`AC-D51.2`.)
  - **D51.3 — explicit Fit/reset (FINAL, Q74(a) answered-owner-confirmed 2026-10-29).** An explicit Fit/reset frames all loaded bars and re-engages follow, plus the go-to-realtime affordance. (`AC-D51.3`.)
  - **D51.4 — per-symbol memory (FINAL, Q75(a) answered-owner-confirmed 2026-10-29).** Follow/scroll state (viewport + follow state) is remembered per symbol: switching back restores where the user was — a deliberate improvement over TradingView for the multi-symbol alarm workflow (supersedes the earlier (b)). (`AC-D51.4`.)
  - **D51.5 — full-series replacement, same vs new symbol (FINAL, Q76(a) answered-owner-confirmed 2026-10-29).** A same-symbol full-series replacement preserves viewport + follow state; a new-symbol load starts following the live edge. (`AC-D51.5`.)
- **Acceptance Criteria (Given/When/Then — ALL FINAL 2026-10-29):**
  - **AC-D51.1 (FINAL, Q72 answered-owner-confirmed 2026-10-29)** Given a loaded main chart at the live edge and a chart scrolled back by pan/zoom, When the follow-state is queried offscreen, Then the former reports following (newest bar's slot visible) and the latter reports scrolled back. (Measurable offscreen: seeded series + scripted viewport; repro-first.)
  - **AC-D51.2 (FINAL, Q73(a) answered-owner-confirmed 2026-10-29)** Given a scrolled-back viewport, When live bars arrive offscreen, Then the visible range is unchanged and follow stays disengaged until the user pans back to the edge or invokes Fit/reset. (Measurable offscreen: viewport-slot assertions before/after injected bars.)
  - **AC-D51.3 (FINAL, Q74(a) answered-owner-confirmed 2026-10-29)** Given any viewport state, When Fit/reset is invoked offscreen, Then the viewport frames all loaded bars, follow is re-engaged, and the go-to-realtime affordance is available. (Measurable offscreen: range + follow-state assertions.)
  - **AC-D51.4 (FINAL, Q75(a) answered-owner-confirmed 2026-10-29)** Given symbols switched offscreen and back, When the follow/scroll state is queried, Then the restored symbol shows its remembered viewport + follow state. (Measurable offscreen: per-symbol state assertions.)
  - **AC-D51.5 (FINAL, Q76(a) answered-owner-confirmed 2026-10-29)** Given a full-series replacement offscreen, When the symbol is the same vs a new one, Then the same-symbol case keeps viewport + follow state and the new-symbol case starts following the live edge. (Measurable offscreen: same-symbol viewport-preservation + new-symbol follow assertions.)
- **Assumptions — D51:** A135 (logged below; FINAL — Q72–Q76 answered-owner-confirmed 2026-10-29).
- **Edge Cases:** covered by Journey 44 (mid-pan arrivals, replacement while away, disconnected switch, zero-bar Fit).

Status: READY_FOR_PLAN

### D52 — Add `30 mins` as a valid chart interval — OWNER-ORDERED 2026-10-29 (lite lane)

- **Area (ADD):** the timeframe surface only — `ibkr/market_data.py::TIMEFRAME_CONFIG` (+1 row), `data/bar_aggregator.py` (+ 1800 s bucketing on ET clock half-hours), `services/backfill_service.py` (planner row for the new span; no detection-logic change), the timeframe picker (`tf_combo` +1 entry between `15 mins` and `1 hour`), and the forming-bar priming table (`AC-D27.9`/D43 gains the `30 mins` row in the `5 secs` group — Plan detail, DG99). Nothing else moves: cache schema, session math, bands, collapse, pop-outs, studies, drawings, alarms are unchanged.
- **Status:** **NEW / OWNER-ORDERED 2026-10-29 — lite lane (no blocking question; A136 owner-decided per Q77 answered-owner-confirmed; A137–A141 defaults).** **D1–D51 are NOT reopened** beyond the recorded timeframe-enumeration extension below.
- **Reported (verbatim intent):** add `30 mins` as a valid chart interval alongside the existing intraday set (`1 min`, `5 mins`, `15 mins`), following the D48 weekly/monthly precedent.
- **Requirements (final):**
  - **D52.1 — bar-size/duration mapping.** `TIMEFRAME_CONFIG` gains exactly one row: `30 mins` → `bar_size='30 mins'`, `duration='30 D'` (A136). (`AC-D52.1`.)
  - **D52.2 — aggregator period support.** 30-minute buckets open on ET clock half-hours (`HH:00`/`HH:30 America/New_York`, which contains the `09:30` RTH open) (A137); live forming-bar aggregation follows the same buckets. (`AC-D52.2`.)
  - **D52.3 — planner/backfill treatment.** `30 mins` is intraday: the `AC-D16.8` 30-session floor **applies** (successive-loads reading per the restated `AC-D16.8`, counted mode-aware per `AC-D16.9`) (A138); loads request the configured duration, chunked per the existing `TIMEFRAME_CONFIG`-stepping rule when one window cannot cover the span; `find_missing_spans` needs no logic change (bar-granular already). (`AC-D52.3`.)
  - **D52.4 — RTH/ETH relevance.** `useRTH`/`ext_hours` applies exactly as for the other intraday timeframes: distinct RTH (`09:30–16:00 ET`) and ETH (`04:00–20:00 ET`) bar sets under a mode-aware cache (A139); D1 session bands and D21.4 collapse apply as for the other intraday timeframes (unlike D48's no-op). (`AC-D52.4`.)
  - **D52.5 — UI picker inclusion.** The timeframe picker gains the `30 mins` entry ordered between `15 mins` and `1 hour` (A140); selection, persistence, pop-out and drawing/alarm-visibility behaviour treat it as an ordinary intraday timeframe (visible by default). (`AC-D52.5`.)
  - **D52.6 — priming coverage.** The forming-bar priming table (`AC-D27.9`/D43) gains the `30 mins` row in the `5 secs` group (elapsed forming span 1800 s fits the `3600 S` ceiling — derived, no new bar size); `duration` = the elapsed span clamped into `[60 S, 3600 S]`. (`AC-D52.6`.)
  - **D52.7 — acceptance gate.** A **standalone probe** verifies IBKR accepts the `30 mins` / `30 D` combo (no 321-class rejection), **and** the full offscreen suite stays green. (`AC-D52.7`.)
  - **D52.8 — history preserved.** `### D41`–`### D51` with reversals stay; the Existing Repository marker sentence + Current Tech Stack are intact; the only edits to pre-D52 criteria are the recorded timeframe-enumeration extension (`AC-D16.1` now reads nine with `30 mins`; `AC-D16.8` Given now reads six intraday timeframes incl. `30 mins` with its `30 D` window/yield row; the D43/`AC-D27.9` per-span table gains the `30 mins` row in the `5 secs` group). (`AC-D52.8`.)
- **Acceptance Criteria (Given/When/Then):**
  - **AC-D52.1 (mapping)** Given `TIMEFRAME_CONFIG`, Then it contains `30 mins` (`30 mins` / `30 D`) and no other row changes. (Measurable: config assertion on the new row + row count +1.)
  - **AC-D52.2 (aggregation)** Given 30-minute bars across a DST fold and an RTH open, Then buckets open on ET clock half-hours (`HH:00`/`HH:30`), the `09:30` RTH open lands on a bucket boundary, and the forming bar aggregates into the current half-hour bucket. (Measurable: unit cases incl. DST-fold 30-min boundaries + forming-bar bucket case.)
  - **AC-D52.3 (planner/backfill)** Given a `30 mins` load, Then the planner requests the configured duration (chunked as needed), applies the `AC-D16.8` floor (mode-aware per `AC-D16.9`), and detects missing spans at bar granularity. (Measurable: planner cases for full-span, chunked, and hole-in-middle + a per-mode 30-session session-count case.)
  - **AC-D52.4 (RTH/ETH relevance)** Given `30 mins` under each mode, Then RTH and ETH loads return their mode's bars (not identical sets), and session bands + collapse apply as for the other intraday timeframes. (Measurable: mode-split case + band/collapse-applied assertions.)
  - **AC-D52.5 (picker)** Given the toolbar picker, Then `30 mins` sits between `15 mins` and `1 hour` and selects/loads/persists like every other intraday timeframe. (Measurable: picker-order case + select-restore case.)
  - **AC-D52.6 (priming)** Given a fresh `30 mins` load mid-period, Then the priming request uses `bar_size='5 secs'` with `duration` inside `[60 S, 3600 S]` — never `5 secs` outside that range and never the `1 min` coarse branch. (Measurable: priming-shape case for a mid-period `30 mins` load.)
  - **AC-D52.7 (probe + suite)** Given live TWS (or the standalone probe harness), Then the `30 mins` / `30 D` request completes without a 321-class rejection, and the full offscreen suite is green. (Measurable: probe record + suite count.)
  - **AC-D52.8 (history intact)** Given `requirements.md`, Then `### D41`–`### D51` with reversals, the marker sentence and the Current Tech Stack are unchanged, and the only pre-D52 wording touched is the recorded enumeration extension. (Measurable: marker grep + the `### D4[1-9]` / `### D5[012]` sections present.)
- **Assumptions (lite) — D52 (no blocking question remains: A136 owner-decided per Q77 answered-owner-confirmed; A137–A141 defaults logged below in the Assumptions Log):**
  - **A136** the `TIMEFRAME_CONFIG` row reads `30 mins` → `bar_size='30 mins'`, `duration='30 D'` (owner decision per Q77 answered-owner-confirmed; advances toward the `AC-D16.8` floor; verified by the `AC-D52.7` probe).
  - **A137** 30-minute buckets open on ET clock half-hours (`HH:00`/`HH:30 America/New_York`).
  - **A138** `30 mins` is intraday for planner/backfill: the `AC-D16.8` floor applies (successive-loads reading, mode-aware); `find_missing_spans` needs no logic change.
  - **A139** RTH/ETH applies as for the other intraday timeframes with a mode-aware cache; bands and collapse apply (the D48-style no-op does NOT extend to `30 mins`).
  - **A140** picker label reads `30 mins`, ordered between `15 mins` and `1 hour`; visible by default in drawing/alarm visibility grids (grid gains a row, DG99).
  - **A141** priming uses the D43 `5 secs` branch (elapsed span 1800 s fits the `3600 S` ceiling) — derived from the D43 rule, not a new default.
- **Edge Cases:** covered by Journey 45 (DST-fold half-hour boundary, holiday-shortened session aggregating only existing bars, disconnected load keeps the D14 no-op semantics, mode switch neither leaves a hole nor reads the other mode's bars).

Status: READY_FOR_PLAN

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
| A68 **[NEW 2026-10-15; CONFIRMED 2026-10-15 — Q48 = YES; composition clause SUPERSEDED by A70 2026-10-15]** | **D41 — "Depth" ALSO includes the Active Trader DOM ladder** (toolbar `DOM` button; `ibkr/market_depth.py`, `ibkr/order_book.py`, and the ladder/book rendering in `ui/active_trader_panel.py`), which is **removed** along with the D37 heatmap. *(Originally recorded as a **ladder-scoped** removal keeping the `OrderEntryWidget`/D18 shell/D21.13 header — that composition clause is **superseded by A70**, Q50.)* | Owner answered **Q48 = YES** on 2026-10-15 (the ladder goes too). Consequence: **ESC-039** becomes moot. | y | 2026-10-15 |
| A69 **[NEW 2026-10-15; CONFIRMED 2026-10-15 — Q49 = "delete"]** | **D41 — persisted D36 footprint data is DELETED.** The `footprint_cache` DB table's DDL is removed from `data/db.py` (so fresh DBs never create it) **and** an existing user DB's `footprint_cache` table + rows are **dropped/deleted** by a small migration. | Owner answered **Q49 = "delete"** on 2026-10-15; the feature that owns the data is removed, so the table + rows go with it. Interpretation recorded; the one-line alternative ("delete rows only, keep the empty table") is noted as **DG70**, but the chosen default is the full drop. | y | 2026-10-15 |
| A70 **[NEW 2026-10-15; CONFIRMED 2026-10-15 — Q50 = YES/YES]** | **D41 scope widened to the ENTIRE Active Trader panel: the in-app order-entry UI is removed with it (no in-app order ticket), and the right dock becomes Portfolio-only.** All of `ui/active_trader_panel.py` (panel shell, ladder/book, `OrderEntryWidget`, `header_bar`/`header_button`, `set_symbol`/`set_last_price`/`last_price`) is **removed**. The **retained order machinery** (`ibkr/orders.py`, `ibkr/validation.py`, `validate_order()`, `bracket_order`, order-ID reservation, the kill switch, the fail-fast port check) is **kept** and guards Portfolio's **Close / Close Group / Flatten All** and the **SL/TP dialogs**. **D18** (right-dock model) and **D21.13** (dock title bar / collapse) clauses that assumed the two-section Active-Trader+Portfolio region are **superseded by D41**; the single Portfolio dock's width cap and header are re-derived. **[D45 NOTE 2026-10-25: superseded — these paths, the kill switch and the SL/TP dialog are all removed; the app has zero order interaction. See D45 / `AC-D45.6`. A88/A89 supersede this row's retained-machinery clause; the `ibkr/orders.py` singleton itself stays for the inert observers (A90).]** | Owner answered **Q50 = YES / YES** on 2026-10-15 (whole panel removed incl. order entry; right dock Portfolio-only). Supersedes A68's ladder-scoped composition clause and DG69's conservative default. | y | 2026-10-15 |
| A71 **[NEW 2026-10-15; Plan-level detail (non-blocking)]** | **D41 — retained order-path `ref_price` source and the Portfolio-only dock's re-derived cap/header.** The kept order path's `ref_price` (previously `active_trader.last_price`, fed by the DOM depth feed) **MUST** come from a **retained** source — the session's last price (live RT-bar / aggregator last) or the `symbol → last_price` watchlist price map (as D27.5 mandates for position market prices) — and must keep resolving. The right dock's width cap (was `floor(0.40 × chart_area)` for the two-section region) and its dock header / collapse affordance are **re-derived for the single Portfolio section**. | Owner confirmed the outcomes (Q50); the exact source/cap/header are implementation choices → **Plan-level details** (DG71), not blocking questions. Logged per the Quality Bar rather than silently baked in. | n | 2026-10-15 |
| A72 **[NEW 2026-10-15 — D42/ESC-042; requirement decision (owner-confirmed via Q51)]** | **The no-overlap guarantee wins over the 4-px body floor at high density.** The candle body width is capped at the inter-bar device-pixel pitch and the D6 4-device-pixel legibility floor becomes **density-aware** (`body = min(max(0.65×pitch, F), pitch)`, `F` = 4 device px at DPR 2); the hard guarantee is `gap >= 0` (never overlap), the gap is `> 0` whenever `pitch > F`, and `0` is acceptable at extreme density (`pitch <= F`). This **supersedes the unconditional `AC-D6.4` wording** and the **`AC-D7.1` "positive gap" wording**. | The escalation is a genuine in-document contradiction and the owner-visible defect (ESC-041: candle/volume overlap on a 5-min Ext-Hours chart) is caused by the unconditional floor; a zero gap (abutting bodies) is not "overlap" and preserves legibility where it can, while a negative gap is never acceptable. Evidence-derived (measured 3.83 px pitch / 4.00 px body); the zero-gap-at-the-limit default was **confirmed by the owner 2026-10-15 (Q51, verbatim: "Zero gap acceptable at the limit.")** — no criteria change. | y (owner-confirmed 2026-10-15, Q51) | 2026-10-15 |
| A73 **[NEW 2026-10-15 — D42/ESC-038; owner-required floor (Q47) + ETH scope owner-confirmed (Q52) + evidence-derived clarifications]** | **Intraday depth (RTH and ETH) = >= 30 trading sessions before the current session, counted by bars inside the current mode's session window; a present-but-empty trading day is a missing span (not filled).** The floor is `AC-D16.8` (owner-required, Q47); the "session = >= 1 bar inside the current mode's window" and "all five intraday windows fall short" clarifications and the new `AC-D16.9` (mode-aware day presence + mode-aware cache) are evidence-derived from the ESC-038/ESC-037 diagnosis. **Q52 (owner-confirmed 2026-10-15: "Extend it to Ext-Hours charts too.") widened the floor and the present-but-empty rule to ETH (`ext_hours=True`)** — one floor, two modes, no cross-contamination. The fetch-window strategy that delivers the floor is a **Plan/Build** matter. | The owner already required the 30-session floor (Q47) and then extended it to ETH (Q52); the present-but-empty rule is the only consistent reading of "a day with no bars in the session window is not a session" and is required for the floor to be measurable. ETH scope owner-confirmed; the remaining clarifications evidence-derived. | y (floor + ETH scope owner-confirmed, Q47/Q52; clarifications evidence-derived) | 2026-10-15 |
| A74 **[NEW 2026-10-16 — D43/ESC-036; requirement decision (owner-confirmed-by-default)]** | **Aggregator priming selects its bar size from the elapsed forming-period span: `5 secs` when the span is <= 3600 S (`1 min`/`5 mins`/`15 mins`/`1 hour`), `1 min` when it exceeds 3600 S (`4 hours`/`1 day`), with `duration` clamped into the selected bar size's IBKR range (`[60 S, 3600 S]` / `[60 S, 1 D]`).** This **supersedes D27.9's "trailing 5-second history" wording** and **revises `AC-D27.9`**. | 5-second bars cannot span a 4h/1d forming period at all (IBKR caps `5 secs` at `3600 S`; the built `5 secs`/`7200 S` request returns TWS error 321), so D27.9 was unsatisfiable for those timeframes; `1 min` covers the whole elapsed span in one request and reuses the existing priming/aggregator path, while the "seed from the historical partial bar" alternative depends on unverified IBKR partial-bar behaviour. The escalation's stated expectation ("`AC-D27.9` met on every timeframe the user can select, including 4h/1d") is the owner-directed intent — **owner-confirmed-by-default** (no owner question required; recorded as Q53). | y (owner-confirmed-by-default 2026-10-16) | 2026-10-16 |
| A75 | **D44 — collapsed bar width is `WATCHLIST_COLLAPSED_WIDTH = 30px`.** The owner bounded the bar to ~28–32px and delegated the exact value; 30px is ≥ the 28px header height, leaves room for the rotated label plus 1px borders, and reads as "a thin bar" while staying clickable. | Owner described "a thin bar"; a numeric geometry (like D17's B1/B4) needs no screenshot; 30px sits mid-range and is implementation-tunable. Logged per the Quality Bar rather than silently baked in. | n | 2026-10-16 |
| A76 | **D44 — the collapsed/expanded state is NOT persisted; the app starts expanded.** Consistent with the existing D21.11 collapse (not persisted) and the D10/A36 precedent that UI show/hide toggles are not persisted; no `QSettings` collapse key. | Owner gave no persistence signal; the consistent default mirrors the existing collapse behaviour. Surfaced to the owner as Q54 (an override would add persistence). | n | 2026-10-16 |
| A77 | **D44 — while collapsed, the horizontal header strip, the `+` add button (D22.1) and the table's column-header row are hidden; the thin bar's only interactive element is the expand affordance.** They return on expand, so no affordance is lost. | A ~30px bar cannot hold a horizontal `+` plus a rotated label legibly; the `+` belongs to the expanded panel (D22.1). Surfaced to the owner as Q54. | n | 2026-10-16 |
| A78 | **D44 — the collapsed-bar mechanism is a Plan-level detail:** a small custom widget with a `paintEvent` drawing rotated text (Qt cannot rotate a `QPushButton`'s text), and the dock's title-bar widget presents the bar while collapsed while keeping the dock movable (DG37). | The outcome (a thin, clickable, app-palette bar) is fixed by `AC-D44.1`/`AC-D44.6`; the widget/title-bar mechanism is an implementation choice, logged per the Quality Bar. | n | 2026-10-16 |
| A79 | **D45 — the digest half of D38 goes; the event-marker half stays.** `ibkr/news.py` (`NewsManager`), `ui/news_digest_dock.py` and the news `"292"` S0 line are removed; the corporate-events provider, `EventMarkerOverlay`, `_merge_events`, the `"456"` dividend S0 line, tick 59, `_dividend_info` and `dividend_updated` are retained. | Owner confirmed 2026-10-25: `ibkr/news.py` delete ("its only consumer is the digest + its tests") and `"456"` must stay "because it feeds the chart's dividend event markers". Recorded so no worker deletes the dividend path with the news path (R68). | y | 2026-10-25 |
| A80 | **D45 — `ibkr/orders.py` may remain as unreferenced code; the requirement is that no UI path reaches `placeOrder`.** `ibkr/validation.py` is **deleted** (named in the owner's inventory); deleting `ibkr/orders.py` (and the order registry/error handling) is optional and a Plan/Build choice — if kept it must have **no importer** and no reachable path. **REVERSED 2026-10-25 (D46) — the module is DELETED in full, not kept; see A91. This row's original wording is kept so the reversal is visible.** | The owner asked for the two components to be removed and for no order-placement path to remain; the inventory names only `ui/trade_context_menu.py` and `ibkr/validation.py` for deletion. AC-D45.4 measures **unreachability / zero transmits**, which holds either way; inventing an `orders.py` deletion would exceed the stated scope. | n (reversed by D46; see A91) | 2026-10-25 |
| A81 | **D45 — whole-file test deletions are exactly the three named** (`tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py`, `tests/test_order_validation.py`); the digest/`NewsManager` cases are **removed from** `tests/test_d38_events_news.py` while the **file is kept** for the event-marker cases. | The brief's consequence line says "four test files are deleted, three of which were the only coverage of order safety", while the inventory names three whole-file deletions plus one case-level trim. The "fourth" is read as the digest half of `tests/test_d38_events_news.py` (trimmed, not deleted). A fourth **whole-file** deletion is **not named** and is not guessed — DG75 records it. | n (default) | 2026-10-25 |
| A82 | **D45 — the kill switch is retained and still meaningful.** It cancels TWS-placed orders (`reqGlobalCancel` + per-ID cancels) and shows pre/post counts; only its `test_flatten_all_kills_first` coupling is dropped (flatten-all is gone), and the switch keeps its own coverage. **REVERSED 2026-10-25 (D45 extension, later the same day): the kill switch is REMOVED in full** — owner: *"remove: Kill switch — it only cancels orders, never places one"*. Superseded by **A88**; this row is kept verbatim so the reversal is visible, not silent. | Owner explicitly retained "the kill switch (cancels TWS-placed orders; still useful)". With orders placed in TWS it is the only in-app protective control. **Reversal rationale:** the owner wants **zero order interaction** — a cancel-only control is still order interaction, and with no in-app placement there is nothing for the app to protect itself from. | n (reversed) | 2026-10-25 |
| A83 | **D45 — the SL/TP dialog is retained unchanged and local-only.** It never placed orders (D26.3's "labelled as not placing orders" branch) and keeps saving targets locally. **REVERSED 2026-10-25 (D45 extension, later the same day): the dialog is REMOVED in full with its Stop/Target columns** — owner: *"remove: ... SL-TP dialog — local-only targets, never transmitted"*. Superseded by **A89**; kept verbatim so the reversal is visible. | Owner explicitly retained "the SL/TP dialog (local-only, never placed orders)"; its label already says it places no orders, so keeping it introduces no order path. **Reversal rationale:** a **local-only target protects nothing**, and once the Trade Context Menu (its only entry point) is removed it is an unreachable setter whose columns could never show a settable value. | n (reversed) | 2026-10-25 |
| A84 | **D45 — Portfolio stays view-only with the account-summary/positions data path retained; no replacement close UI, hotkey or TWS-API bridge.** Closing happens in TWS; the panel reflects it on the next position update. | Owner: "Portfolio becomes view-only: closes happen in TWS directly. No replacement UI." | y | 2026-10-25 |
| A85 | **D45 — documentation scope is the three owner-named files** (`USAGE.txt`, `usage.md`, `docs/codebase-map.md`), cleaned in the same batch; `docs/architecture.md`/`docs/plan.md` are Plan/Validator-owned and synced there. | Owner named the docs; `docs/codebase-map.md` is a Plan-owned per-batch artifact (memory 2026-10-23) and is refreshed by Plan, verified by the Code Reviewer. | y | 2026-10-25 |
| A86 | **D45 — no menubar replaces the removed `View` menu**, and `Ctrl+Shift+N` is removed with it (no orphan `QAction`). | Owner: the View menubar is "fine to lose"; it existed solely for the dock, and the app had no menubar before D38. | y | 2026-10-25 |
| A87 | **D45 — Stop/Target columns decision: remove the two columns with the SL/TP dialog; keep the storage.** The positions table goes **10 → 8 columns** (`Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`) and the header/value/alignment slots go; the `positions.stop_loss`/`take_profit` and `trade_groups.stop_loss`/`take_profit` **DB columns**, the `Position`/`TradeGroup` **model fields** and the `_persist_position` upsert **stay** — no migration, no destructive schema change, **but the values are not preserved**: `_on_position_update` passes `stop_loss=None, take_profit=None` and the upsert's `DO UPDATE` writes both columns, so the next live update clears them (ESC-060, corrected 2026-10-25). | With the dialog gone there is **no setter anywhere**, so the columns would be permanently dead display and a `Stop`/`Target` header implies a control that no longer exists (the owner has declined replacement UI twice, so no read-only fallback dialog either). Keeping the storage costs nothing, opens a pre-D45 DB without a migration, avoids a destructive schema change and keeps `tests/test_stop_loss_target.py` (model fields) meaningful. **Rejected:** keep the columns as legacy read-only display — it advertises an impossible feature and costs two columns of a width-constrained table. **REVERSED 2026-10-25 (D46, Q59 — owner: *"remove everything"*): the columns and the model fields are DROPPED, not kept (A99 / D46.12), so the trail reads kept → cleared → dropped. This row's original wording is kept verbatim so the reversal is visible.** | n (reversed by D46; see A99) | 2026-10-25 |
| A88 | **D45 — the kill switch goes completely and no cancel capability is re-pointed.** `kill_btn` (+ its preceding separator), `_on_kill_switch_clicked`, `_kill_switch`, the `reqGlobalCancel()` call and the per-ID `cancelOrder()` loop are deleted; the app keeps **no** cancel path. `reqGlobalCancel`/`cancelOrder` each have **exactly one** production call site (inside `_kill_switch`), **no** `ibkr/` wrapper and **no** disconnect/teardown caller. | Verified in-repo 2026-10-25: the only call sites are in `ui/main_window.py::MainWindow._kill_switch`; its other caller (`_on_portfolio_flatten_all`) is removed by Group B, so nothing needs re-homing. Cancel surface after D45 is **TWS**. | y (owner-requested; call-site fact verified) | 2026-10-25 |
| A89 | **D45 — the SL/TP dialog goes completely.** `ui/stop_loss_target_dialog.py`, its `confirmed` signal, `position_sltp_changed`/`group_sltp_changed`, `_on_set_sltp`/`_on_sltp_confirmed`, `update_position_sltp`/`update_group_sltp`, `_sltp_dialog`, both `MainWindow` persistence slots (with their row-`UPDATE`s) and the two display columns are deleted. | The dialog already had **no entry point** once Group B removed `TradeContextMenu.set_sltp_action` (the Plan map records `FI-D45-1`), so removal completes an already-severed path rather than conflicting with Group B; its targets never transmitted, so nothing protective is lost. | y (owner-requested) | 2026-10-25 |
| A90 | **D45 — observation-only order plumbing stays, inert; no replacement UI.** The inbound `_on_open_order`/`_on_order_status`/`_on_exec_details`/`_on_order_error`/`_update_order_status` callbacks and the `order_registry` import remain wired (they observe; they never place/cancel) and the registry is never populated, so they are inert. `ibkr/orders.py` keeps A80's default (leave unreferenced); if Plan deletes it, these callbacks must be made registry-safe in the same task. **REVERSED 2026-10-25 (D46) — the observers are REMOVED, not kept inert, and the module is deleted; see A92. This row's original wording is kept so the reversal is visible.** The **fail-fast port check**, the connection badge and the no-test-transmits rule are retained. **No replacement cancel/protection UI is authorized.** | Deleting the inbound callbacks would touch the connection/error path the D26.5 badge depends on for no reachability gain (`AC-D45.4` measures zero calls, not the absence of observers); the owner declined replacement UI twice. | n (reversed by D46; see A92) | 2026-10-25 |
| A91 | **D46 (reverses A80) — `ibkr/orders.py` is DELETED in full.** The module (`UserOrder`, the four `Orders` builders, the five registry methods and the `orders` singleton) is removed; nothing imports it and `import ibkr.orders` fails. | Owner-requested 2026-10-25 (*"I dont want anything to do with orders so why is there orders.py ?"*), batch confirmed after being told the module has **zero** production callers and a registry nothing populates. A80's "may remain unreferenced" was a scope-conservative default, not an owner preference; the owner has now decided the opposite. D45's consequence 4 called this a Plan/Build choice — D46 makes it the requirement. | y | 2026-10-25 |
| A92 | **D46 (reverses A90) — the inert order-observation chain is REMOVED.** The three `EWrapper` overrides (`orderStatus`/`openOrder`/`execDetails`), the three `Bridge` signals, the three `MainWindow` slots, `_update_order_status`, `_on_order_error` and the `order_registry` lookup in `_on_error` are deleted. | Verified in-repo 2026-10-25: every one of them ends in `order_registry.get(id)` against a registry nothing ever writes, so the whole chain has **no behavioural effect** — removing it cannot change what the user sees. Keeping it would contradict the owner's explicit instruction, keep order names alive in the tree, and force `tests/test_d45_removal.py` to keep allow-listing them. Owner-confirmable (Q56); the only loss is the observation seam itself, which has no consumer. | y (**owner-confirmed 2026-10-25**, Q56/Q57 — *"i want all of it deleted"*) | 2026-10-25 |
| A93 | **D46 — 201/103/202 keep surfacing on the existing generic line.** The status bar shows `Error [<code>]: <TWS's own message>` for **8000 ms** on the non-session path. **No** order-id prefix, **no** "Rejected"/"Cancelled" verdict and **no** 12-second duration is restored: the richer wording lived in `_on_order_error`, which the always-empty registry made **unreachable**, so this is what the owner already sees today. | The owner's constraint is *"TWS errors must still surface"* — satisfied without new formatting code. `classify_error` rates 201/103 `fatal` and 202 `warning`, so `IBApiClient.error`'s `severity != 'info'` gate emits all three; nothing is suppressed. The app no longer knows which order an error belongs to, so inventing an order-identity format would be a false signal. Owner-confirmable (Q57). | y (**owner-confirmed 2026-10-25**, Q57 — the owner rejected the premise of the question; the substance stands unchanged) | 2026-10-25 |
| A94 | **D46 — error routing is not reordered.** `_on_error`'s session-reqId branch stays first, so an order error whose numeric id collides with a live session reqId behaves exactly as it does today (routed to the session's handler, which also shows the generic line). | D46 is a removal. Reordering the error path is a behaviour change nobody asked for, and the collision is **pre-existing** (the registry lookup already sat after the session branch). Recorded as **DG78** so it is a visible decision rather than an unnoticed one. | n (default) | 2026-10-25 |
| A95 | **D46 — `tests/test_order_rejections.py` survives in reduced form (3 of 5 cases).** File kept (renaming is churn): the two registry cases (`201 → Rejected`, `202 → Cancelled`) are removed, `test_non_order_error_untouched` is **repointed** at the generic status-bar line, and both `classify_error` cases are kept. `tests/test_order_builders.py` is deleted whole (17 cases, all for zero-caller builders). | `classify_error` is **not** order-specific — it gates every TWS error through `IBApiClient.error` — so its coverage must stay. The repointed surfacing case is exactly `AC-D46.3`'s positive proof that 201/202 still reach the status bar, which is the owner's stated constraint; deleting the file would leave that constraint unguarded. Owner-confirmable (Q57/Q59). | n (default) | 2026-10-25 |
| A96 | **D46 — the vestigial second `UserOrder` in `data/models.py` is removed**, and `tests/test_ui_smoke.py`'s `hasattr(data.models, "UserOrder")` assertion with it. | Repo-verified 2026-10-25: `data/models.py::UserOrder` is a **different** dataclass from `ibkr/orders.py::UserOrder` and has **zero** consumers in the tree (its only reference is the smoke `hasattr`). Two same-named order classes, neither used, is the same fossil the owner is asking about; leaving one behind would make the answer to *"why is there order code?"* incomplete. Owner-confirmable (Q58). | y (**owner-confirmed 2026-10-25**, Q58 — *"yes remove"*) | 2026-10-25 |
| A97 | **D46 — `IdManager.reserve` and `classify_error`'s severity table are LEFT.** `ibkr/id_manager.py` stays whole (`get_id`/`set_next_valid_id` are shared with market-data reqId allocation); `reserve()` is order-motivated (D26.2 bracket IDs) with tests only. `ibkr/error_codes.py::classify_error` is untouched. | Neither is part of the named ask or the observation chain. `reserve()` is a generic contiguous-ID allocator (a test-covered utility, not an order path) and `classify_error` gates **every** TWS error, including the visibility the owner requires. Removing either would widen a delete-only batch (the pattern that kills workers — memory 2026-10-15) for no user-visible gain. Recorded as **DG80** so the leftover is a decision, not an oversight. **REVERSED IN PART 2026-10-25 (D46, Q59 — owner: *"remove everything"*): the `reserve()` half is superseded — `reserve` is DELETED (A101, its only callers are tests) — while the `classify_error` half is CONFIRMED and restated as A100 (it gates every TWS error). Original wording kept verbatim.** | n (reversed in part by D46; see A100/A101) | 2026-10-25 |
| A98 | **D46 — docs scope is `docs/codebase-map.md` (Plan-owned, incl. superseding `S29`/`AR-D45-10`) plus comment-level fixes in `ibkr/error_codes.py` and the surviving tests.** No user-facing doc change is expected, because no `USAGE.txt`/`usage.md` line describes this module — verify by grep. | Matches D45's A85 split: Plan owns the map/architecture/plan, Build owns code comments and docstrings. `docs/codebase-map.md:97` currently states `ibkr/orders.py` "is NOT orphaned and must NOT be deleted", which is the single most dangerous line for a Build worker reading the map (**DG81**). **D46 EXPANSION NOTE (2026-10-25): the scope also covers the stop/target statements in `USAGE.txt` / `usage.md` (D46.13 / A99)** — the module half needed no user-facing change, but the storage half did, because those two files were corrected this morning under ESC-060 to say the columns are *kept*. | n (default) | 2026-10-25 |
| A99 **[NEW 2026-10-25 — D46 expansion; REVERSES A87]** | **The `positions` / `trade_groups` `stop_loss` / `take_profit` DB columns are DROPPED, and the `Position` / `TradeGroup` / `ibkr.account.Position` model fields with them.** End state fixed; the migration mechanism is Plan's (D46.12). **Owner: Q59 verbatim *"remove everything"*,** having been shown A87's retention and A97's out-of-scope note. **Justification (honest, and stronger than preference):** per **ESC-060** — corrected in these docs earlier the same day — the values were **already destroyed by the first live update** of any row (`_on_position_update` builds `Position(stop_loss=None, take_profit=None)`; the upsert's `DO UPDATE` writes both columns), and every setter was removed in D45, so the columns could only ever hold `NULL`. **The drop destroys nothing that survived.** What must NOT be destroyed is a **row** (D46.12 / R82). | Owner instruction 2026-10-25. Keeping dead `NULL`-only columns was the only thing A87 bought, and it bought it on the premise that values persisted — which ESC-060 disproved. **Correction (RG-D46-7, 2026-10-26):** the justification reads "destroys nothing the app can reach" — a never-updated pre-D45 row keeps its legacy bytes until the drop. | y (owner-requested, Q59) | 2026-10-25 |
| A100 **[NEW 2026-10-25 — D46 expansion]** | **`classify_error` and the generic error surface STAY** after Q59's *"remove everything"*: `ibkr/error_codes.py::classify_error` (incl. 201/103 `fatal`, 202 `warning`), the `error_msg` signal, `IBApiClient.error`'s `severity != 'info'` gate with the D40.1 `502` backoff suppression, `_on_error`'s session routing and its final `statusBar.showMessage(f"Error [{code}]: {string}", 8000)`. | None of it is order-specific — it gates **every** TWS error — and deleting it would remove the error visibility the owner explicitly requires *("TWS errors must still surface")*. This confirms A97's second half after Q59 and is the reason `AC-D46.3` survives the expansion unchanged. | y (owner constraint) | 2026-10-25 |
| A101 **[NEW 2026-10-25 — D46 expansion; REVERSES A97's first half]** | **`IdManager` STAYS; only `reserve()` goes.** `IdManager`, `get_id`, `set_next_valid_id` and the `id_manager` singleton remain and keep their callers; `IdManager.reserve` (`ibkr/id_manager.py:19-30`) and its D26.2 docstring are deleted, and `tests/test_id_manager.py` loses its four pure `reserve` cases while the mixed `set_next_valid_id_still_monotonic_with_reserve` case is rewritten without `reserve`. | **Checked before writing it down, because deleting the module would take the chart with it:** `get_id()` is called at `ibkr/market_data.py:42,74,90,103` and `ibkr/realtime_bars.py:31` (market-data + realtime reqIds) and `set_next_valid_id()` at `ibkr/client.py:184`, so the module is **shared, not order-only**; `reserve()`'s only callers are `tests/test_id_manager.py:10,18,32,39,56`. | y (owner-requested, Q59; reachability verified 2026-10-25) | 2026-10-25 |
| A102 **[NEW 2026-10-25 — D46 expansion]** | **`IBApiClient.nextValidId` and `IdManager.set_next_valid_id` are RETAINED.** Only order-worded **comments** inside them are removed. | `nextValidId` is not an order path in effect: it is the **connection-established** transition (`_connected = True`, reconnect-attempt reset, disconnect-class clear, `_set_state(CONNECTED)` — `ibkr/client.py:182-193`) and it is what the D40/D25 lifecycle tests drive (`tests/test_d40_tws_lifecycle.py:239,311,368,407,450`; `tests/test_d25_alarm_monitor.py:397`). Its name is IBKR's (`EWrapper.nextValidId`) and cannot be renamed, so it stays in the inventory's RETAIN set with this note (DG82). | y (evidence-derived, DG82) | 2026-10-25 |
| A103 **[NEW 2026-10-25 — D46 expansion]** | **D46's symbol inventory is the acceptance instrument** (`D46.9` / `AC-D46.9`): every order-named class, function, method, signal, constant, column, field and docstring is in exactly one of the **DELETE** or **RETAIN** sets, and anything genuinely ambiguous is recorded in `design_gaps.md` **before** it is touched rather than guessed at build time. | This is the mechanism Q56's answer asks for: the earlier failure was a "retained and inert" decision that was never audited for **reachability**. A closed inventory makes "all of it" checkable and equally makes "nothing innocent was cut" checkable. | y (analyst decision; serves the owner's Q56 question) | 2026-10-25 |
| A104 **[NEW 2026-10-25 — D46 expansion]** | **The expanded test book is exactly D46.5's list** and nothing else changes; `tests/test_order_builders.py` and `tests/test_stop_loss_target.py` are deleted **whole**, not trimmed. | The expansions are consequences of deleting the surface, and the two files have no other subject: builders for zero callers, and model fields that no longer exist. Trimming them would leave tests asserting a removed design. | n (default) | 2026-10-25 |
| A105 **[NEW 2026-10-26 — D47]** | **Phase 0 is a throwaway spike in `spikes/lwc/` only** — nothing there is imported by production or tests; its only deliverables are the 9-API-behaviour proof + `docs/lwc_spike_results.md` with a go/no-go gate. | Single owner-authorized exception to the no-prototype convention (2026-10-26 approval 3); everything else in D47 is production code behind the seam. | y (owner-authorized) | 2026-10-26 |
| A106 **[NEW 2026-10-26 — D47; answered-by-default, Q60 YES]** | **`barSpacing` replaces the pyqtgraph density-cap ACs** (`AC-D6.4`/`AC-D7.1`/`AC-D9.1` density language); the no-overlap guarantee is restated in `barSpacing` terms (DG94). | The migration plan states the replacement as an owner-visible AC change (Q60 answered-by-default YES). | n (proposed; Q60 answered-by-default) | 2026-10-26 |
| A107 **[NEW 2026-10-26 — D47; owner-confirmed, Q62]** | **The pop-out cap stays at the D24 10** (owner verbatim 2026-10-26: "Keep 10 (Recommended)"; Phase 9 verifies 1, 3, 6 against it). | Preserves the approved D24 behaviour; raising it needs the memory/bridge evidence in DG90. | y (owner-confirmed 2026-10-26, Q62) | 2026-10-26 |
| A108 **[NEW 2026-10-26 — D47; owner-confirmed, Q63]** | **The LWC crosshair drifts to the library-native crosshair + axis label** (no exact-pill custom primitives; D2/Q33 stands only where still applicable; owner verbatim 2026-10-26: "Accept drift (Recommended)"). | Pixel-exact reproduction needs a custom primitive driven per move; drift is the library-native outcome. | y (owner-confirmed 2026-10-26, Q63) | 2026-10-26 |
| A109 **[NEW 2026-10-26 — D47; owner-confirmed, Q61 measure-first]** | **No fixed `.app` size budget — measure first** (owner verbatim 2026-10-26: "Measure first, no fixed budget"); Plan measures the Phase 0 size delta and reports, the owner sets the budget from the numbers; note whether the current signing flow covers the Chromium/vendored tree as a Phase 0 finding. | Bundle size + signing identity are release facts, not derivable defaults. | y (owner-confirmed 2026-10-26, Q61) | 2026-10-26 |
| A110 **[NEW 2026-10-26 — D47]** | **Webengine cases are `@pytest.mark.webengine` and skip (never red)** where no engine exists; the manual checklist is the gate there (DG88). | Offscreen viability is unproven — a red webengine case must mean a real regression, not a missing Chromium. | n (default) | 2026-10-26 |
| A111 **[NEW 2026-10-26 — D47]** | **Timestamp edge cases (DST folds, session-boundary bars, ts-to-fractional-index collisions) are DG93**, verified against both engines on the same fixtures. | Logical-index parity is where silent divergence hides. | n (default) | 2026-10-26 |
| A112 **[NEW 2026-10-26 — D47]** | **Bridge backpressure counters, per-pop-out memory accounting and focus/keyboard forwarding are DG91/DG90/DG92** — instrumented from Phase 2, not retrofitted. | Queue-until-ready + replay can mask growth until it hurts. | n (default) | 2026-10-26 |
| A113 **[NEW 2026-10-28 — D48; lite default]** | **`TIMEFRAME_CONFIG` gains exactly two rows:** `1 week` → `bar_size='1 week'`, `duration='2 Y'`; `1 month` → `bar_size='1 month'`, `duration='10 Y'`. | Owner-specified spans (2 years weekly, 10 years monthly); IBKR `1 week` / `1 month` bar sizes exist. | n (default) | 2026-10-28 |
| A114 **[NEW 2026-10-28 — D48; lite default]** | **Weekly buckets open Monday 00:00 America/New_York.** | Conventional US-equity week; matches the ET session calendar the repo already uses. | n (default) | 2026-10-28 |
| A115 **[NEW 2026-10-28 — D48; lite default]** | **Monthly buckets open on the calendar-month boundary (ET);** a nominal 30-day (2592000 s) period is used only where an API demands fixed seconds, never for bucketing. | Months vary 28–31 days; fixed-seconds bucketing would drift month boundaries. | n (default) | 2026-10-28 |
| A116 **[NEW 2026-10-28 — D48; lite default]** | **Durations use IBKR year units (`2 Y`, `10 Y`),** not day counts. | Clearer at multi-year spans and inside IBKR's accepted duration vocabulary; the probe (`AC-D48.6`) verifies. | n (default) | 2026-10-28 |
| A117 **[NEW 2026-10-28 — D48; lite default]** | **The `AC-D16.8` 30-session floor stays intraday-only** (weekly/monthly join the `1 day` exclusion); `find_missing_spans` day-presence needs no logic change. | Daily+ bars are one-per-session-or-coarser by construction; presence detection already operates at bar granularity. | n (default) | 2026-10-28 |
| A118 **[NEW 2026-10-28 — D48; lite default]** | **RTH/ETH is a no-op for weekly/monthly:** identical bars under both modes, one shared cache treatment; D1 bands and D21.4 collapse stay no-ops. | A weekly/monthly bar aggregates whole sessions regardless of mode, exactly as `1 day` already does. | n (default) | 2026-10-28 |
| A119 **[NEW 2026-10-28 — D48; lite default]** | **Picker labels read `1 week` / `1 month`, ordered immediately after `1 day`.** | Extends the existing ascending-granularity picker order; matches the `TIMEFRAME_CONFIG` key strings. | n (default) | 2026-10-28 |
| A120 **[NEW 2026-10-28 — D48; lite default]** | **The new timeframes default to visible** in drawing/alarm visibility grids; the 8-row grid gains rows (or an equivalent control) at Plan/Build discretion. | Drawings/alarms have no reason to hide on the new timeframes by default; see DG97. | n (default) | 2026-10-28 |
| A121 **[NEW 2026-10-28 — D49]** | **Restore reuses the existing history/backfill/pacing path** (cache → missing-span detection → paced fetch → aggregator → realtime subscribe); no new fetch machinery. | The report's recommended fix names that path; a second fetch path would split the `AC-D16.8`/`AC-D16.9` semantics. | n (default) | 2026-10-28 |
| A122 **[NEW 2026-10-28 — D49]** | **Attach tracks acquisition state explicitly** (a hold-acquired flag set only where `ensure_rt_subscribed` actually added a hold) so failure cleanup releases only its own hold — never another view's. | The report requires "release only a realtime hold actually acquired"; without a flag, cleanup cannot tell whose hold it is. | n (default) | 2026-10-28 |
| A123 **[NEW 2026-10-28 — D49]** | **ESC-070 (main window) is the behavioral model for D49.3**, adapted to the pop-out site: visible error state + retained diagnostic log. | The batch order names ESC-070 as the model and this site as different; the mechanism transfer is analyst-recorded. | n (default) | 2026-10-28 |
| A124 **[NEW 2026-10-28 — D49; owner-confirmed Q64 2026-10-28]** | **D49.3's copy/layout is owner-confirmed:** an in-pop-out message area + status text, unmistakable vs empty-data (ESC-070 model). | Owner accepted the standing default verbatim 2026-10-28; the outcome (visible, unambiguous, distinct from no-data) is testable without pixel details. | y (owner-confirmed 2026-10-28, Q64) | 2026-10-28 |
| A125 **[NEW 2026-10-28 — D49]** | **D49.4 keeps the `drawings_changed` signal and per-pop-out handler wiring** (notification role); de-duplication happens at the sync call site, and update semantics do not change. | Removing the signal would change the session contract beyond the perf fix; the report's recommended fix keeps the handler as a notification. | n (default) | 2026-10-28 |
| A126 **[NEW 2026-10-28 — D49; owner-confirmed Q66 2026-10-28]** | **A verified-close with no code change is a legitimate delivered outcome for D49.5** (not dropped scope), provided the verification record exists; the fix shape, if needed, is idempotent per-owner acquire/release. | Owner confirmed YES verbatim 2026-10-28 — verified-close counts as delivered. | y (owner-confirmed 2026-10-28, Q66) | 2026-10-28 |
| A127 **[NEW 2026-10-28 — D50; settled input]** | **The LWC primitives render path is proven working (bind fix).** D50 takes it as a settled input and specifies no render-path change. | Owner-scheduled brief: "LWC primitives render path proven working (bind fix)". | y (brief-stated) | 2026-10-28 |
| A128 **[NEW 2026-10-28 — D50; settled input]** | **The `PageDrawing` / `drawing_controller.created` surface and the `DrawingStore` update paths exist.** D50 specifies the edit behaviour that commits through them; it does not re-specify creation. | Owner-scheduled brief: "Do not re-specify creation." | y (brief-stated) | 2026-10-28 |
| A129 **[NEW 2026-10-28 — D50; settled fact]** | **`gestures.js` has NO drag-initiation path; `drag_drawing` in the view is the operation surface.** Any lock or edit behaviour MUST be specified (and later enforced) at the operation surface, not at handle visibility. | Owner-scheduled brief states both halves; recorded here so no worker "fixes" lock by hiding handles. | y (brief-stated) | 2026-10-28 |
| A130 **[NEW 2026-10-28 — D50; dependency — RESOLVED Q70 = (c) Both]** | **New drawings take the group colour at creation, stored on the drawing (survives leave-group); recolouring a group repaints all current members (stored colours updated).** A dragged/edited drawing keeps its own stored colour. (Lineage: this row previously carried both readings pending the 3.3 pick.) | Owner decision relayed 2026-10-28: recolour semantics (c) Both. | y (owner-decided 2026-10-28, Q70) | 2026-10-28 |
| A131 **[NEW 2026-10-28 — D50; Q71 default]** | **Edited-geometry acceptance is measurable offscreen where possible** (seeded store + committed coordinates + reload-restore + fan-out count, no live TWS). | Matches the D49 offscreen-first quality bar; a live check needs an owner-named step. | n (default) | 2026-10-28 |
| A132 **[NEW 2026-10-28 — D50; analyst decision per Q70]** | **Mid-drag group recolour: the recolour updates the member's stored colour immediately; the in-flight drag ghost keeps the colour sampled at drag start; at commit, geometry writes and colour is read from the store — the drag never overwrites colour.** | Owner delegated mid-drag handling ("as you see fit", Q70 relay); geometry and colour are independent channels and the commit path writes geometry only, so a recolour cannot be lost to a concurrent drag nor can a drag clobber a recolour. | n (default) | 2026-10-28 |
| A133 **[NEW 2026-10-29 — D49.6]** | **Pop-out creation passes the main chart's current timezone offset** into the new view; no new timezone source is introduced and the hardcoded `tz_offset=0.0` is removed at the creation call site. | Owner-ordered handoff; the main chart's offset is the only correct source for "same view". | n (default) | 2026-10-29 |
| A134 **[NEW 2026-10-29 — D49.6]** | **The offset is persisted with the saved pop-out set; a pre-change save without the field falls back to the main chart's current offset at restore** — never silent UTC. | Restored windows must keep the same view; older saves carry no field, so the fallback must be stated rather than assumed. | n (default) | 2026-10-29 |
| A135 **[NEW 2026-10-29 — D51; FINALISED 2026-10-29]** | **D51 decided by the owner (Q72–Q76 answered-owner-confirmed 2026-10-29):** follow = newest-bar slot visible (TradingView shiftVisibleRangeOnNewBar, vendored 5.2.1); no auto-resume while away (resume only on pan-back-to-edge or Fit/reset); Fit frames all loaded bars + re-engages follow, plus go-to-realtime affordance; per-symbol viewport + follow memory (deliberate TradingView improvement for the multi-symbol alarm workflow; supersedes the earlier (b)); same-symbol replacement preserves, new-symbol load follows. | Owner decisions recorded verbatim in `open_questions.md` Q72–Q76; nothing assumed. | y | 2026-10-29 |
| A136 **[NEW 2026-10-29 — D52; owner decision per Q77]** | **`TIMEFRAME_CONFIG` gains exactly one row:** `30 mins` → `bar_size='30 mins'`, `duration='30 D'`. | Owner decision (Q77 answered-owner-confirmed 2026-10-29 as `30 D`): advances toward the `AC-D16.8` 30-session floor while staying inside IBKR's per-request vocabulary for a 30-minute bar size; verified by the `AC-D52.7` probe rather than assumed. | y (owner-confirmed 2026-10-29) | 2026-10-29 |
| A137 **[NEW 2026-10-29 — D52; lite default]** | **30-minute buckets open on ET clock half-hours** (`HH:00`/`HH:30 America/New_York`). | The `09:30` RTH open sits on a half-hour so clock alignment and session anchoring coincide; matches the sub-hourly convention. | n (default) | 2026-10-29 |
| A138 **[NEW 2026-10-29 — D52; lite default]** | **`30 mins` is intraday for planner/backfill:** the `AC-D16.8` 30-session floor applies (successive-loads reading, counted mode-aware per `AC-D16.9`); `find_missing_spans` needs no logic change (bar-granular already). | Owner ordered it "alongside the existing intraday set"; only `1 day` and coarser are excluded from the floor. | n (default) | 2026-10-29 |
| A139 **[NEW 2026-10-29 — D52; lite default]** | **RTH/ETH applies as for the other intraday timeframes** (distinct RTH/ETH bar sets, mode-aware cache); D1 bands and D21.4 collapse apply. | A 30-minute bar aggregates part of a session, so mode filtering is meaningful — unlike weekly/monthly (A118). | n (default) | 2026-10-29 |
| A140 **[NEW 2026-10-29 — D52; lite default]** | **Picker label reads `30 mins`, ordered between `15 mins` and `1 hour`;** visible by default in drawing/alarm visibility grids (grid gains a row, DG99). | Extends the existing ascending-granularity picker order and the `TIMEFRAME_CONFIG` key strings; drawings/alarms have no reason to hide on the new timeframe by default (as A120). | n (default) | 2026-10-29 |
| A141 **[NEW 2026-10-29 — D52; derived]** | **Priming uses the D43 `5 secs` branch** (`duration` = elapsed span clamped into `[60 S, 3600 S]`); no `1 min` coarse-branch row is added for `30 mins`. | Elapsed forming span (1800 s) fits the `3600 S` ceiling — the D43 rule decides the branch, not a new default. | n (derived) | 2026-10-29 |
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
| R61 **[NEW 2026-10-15; updated for Q50]** | Removing D36/D37, the DOM ladder (Q48), **and the whole Active Trader panel incl. the order-entry UI** (Q50) could silently break a feature the owner did **not** remove: (a) D38 (S0 ticks `"292"`/`"456"`, `md_line_guard`) and D39 (`INDEX_PROXY`, `footprint_cache_key`, `volume_baseline`); (b) the **retained order machinery** (validation, bracket construction, kill switch, `ibkr/orders.py`, `ibkr/validation.py`) that Portfolio's **Close / Close Group / Flatten All** and the **SL/TP dialogs** still use; (c) the order path's `ref_price` (was fed by the DOM depth feed) losing its source; (d) accidentally deleting the retained order machinery **with** the order-entry UI | H | M | `AC-D41.4` + the D41 "Scope — KEEP" list pin every shared symbol and the order machinery; the order-entry **UI** is removed but the **safety machinery is explicitly KEPT** (DG69); `AC-D41.4` requires retained order paths to still validate with a **resolving `ref_price`** (new retained source — A71); `AC-D41.5` requires the full suite green; the D38/D39/order/D27–D28 suites stay green as the regression guard | **NOTE 2026-10-25 (D45 extension):** the mitigation's premise — that the order machinery is **retained** for the close/flatten/SL-TP paths — no longer holds: those paths, the kill switch and the SL/TP dialog are all removed, so there is **no retained order path left to break** (see R73–R75 for the risks that replace this one). |
| R62 **[NEW 2026-10-15]** | The Portfolio-only right dock's **re-derived width cap and header/collapse** could be left unspecified, so the single-section dock might inherit the old two-section assumptions (equal-width clause in `AC-D18.3`, Active-Trader title-bar widget) | M | M | `AC-D41.7` requires the right dock to be Portfolio-only with a re-derived cap/header; `D18`/`D21.13` carry explicit **superseded-by-D41** notes; DG71 records the re-derivation as the Plan/Build detail |
| R63 **[NEW 2026-10-15 — D42/ESC-042]** | The density-aware cap could be implemented inconsistently between the candle body and the volume width, or the tests that encode the old unconditional rule (`tests/test_candle_spacing.py`, `tests/test_volume_width.py`) could be left asserting the defect, so candles and volume diverge or the suite stays green on the bug | M | H | `AC-D6.4`/`AC-D7.1` (revised) + `AC-D9.1`/`AC-D9.2` pin one shared capped `w`; D42's correction record requires the two enshrining tests be **corrected** (not weakened) and a rendered-geometry guard (`body <= pitch`, from the `QPicture` bbox) added; ESC-041's re-check measures the rendered pixel run |
| R64 **[NEW 2026-10-15 — D42/ESC-038; ETH scope added by Q52]** | Delivering the 30-session floor **in both RTH and ETH** needs backwards-extending chained fetches across all five intraday timeframes; a partial implementation could meet `1 min` but leave `5 mins`…`4 hours` short, could cover RTH but not ETH (or vice versa), or the mode-aware day-presence change could regress the D16 no-silent-hole behaviour | M | M | `AC-D16.8` states the floor for **all five** timeframes **in both modes** and `AC-D16.9` scopes the change to **presence** only (no-fill/no-silent-hole `AC-D16.1`/`AC-D16.4` unchanged); D42's correction record adds `find_missing_spans(..., ext_hours=False)` **and** `find_missing_spans(..., ext_hours=True)` RED→GREEN cases plus a per-timeframe, per-mode session-count guard and a no-cross-contamination check; the D16 suite stays green |
| R65 **[NEW 2026-10-16 — D43/ESC-036]** | The `1 min` priming request for `4 hours`/`1 day` could be built inconsistently (e.g. the bar size switched but the duration left at the `5 secs` ceiling, or the switch applied to the wrong timeframe set), leaving the coarse timeframes still rejected by IBKR or over-fetching; the priming tests could also be left asserting the superseded `5 secs`/`7200 S` shape, so the suite stays green on the defect | M | M | `AC-D27.9` (revised) pins the per-span bar size **and** the per-bar-size duration range; D43's correction record requires the priming tests be **corrected** (not weakened) with a RED→GREEN `4 hours`/`1 day` case (a `1 min` request whose duration is inside `[60 S, 1 D]`); P2-T30's stale `AC1`/`P2-T30-T11` are flagged for revision |
| R66 **[NEW 2026-10-16 — D44]** | The collapsed width could be **snapped back to `WATCHLIST_MIN_WIDTH` (150px)** by `plan_dock_widths`/`_apply_dock_widths` on the next `resizeEvent` or dock drag, so the thin bar never sticks (the same clamp-during-drag defect class as D17/D19) | M | H | `AC-D44.5` requires the layout to honour the collapsed width; `AC-D44.8` requires a **pre-fix-RED** guard that the collapsed width survives a resize/drag; `plan_dock_widths`/`_apply_dock_widths` are the single apply entry points and must learn the collapsed state |
| R67 **[NEW 2026-10-16 — D44]** | D44's change to the collapsed appearance could **regress** the D21.11 collapse behaviour, the `VIS-D21.1` strike-through convention, or the **expanded-state** D13/D17 width criteria and their suites (`tests/test_dock_widths_d17.py`, `tests/test_dock_widths_d18.py`, `tests/test_dock_layout.py`, `tests/test_watchlist_columns_d21.py`) | M | M | D44 **revises** only the collapsed-appearance clauses (`AC-D21.11.2`/`.3`) and the 150px-minimum clause (`AC-D13.1`/`AC-D17.2`, now expanded-only); the expanded-state width suites must stay green or be updated in lockstep (never left contradicting D44); `AC-D44.8` names the non-regression requirement; the `AC-D44.2` expand-restore measurable is the **tracked** `_watchlist_width` (exactly `clamp(W)`), with a **tolerant** rendered-width check — restated 2026-10-16 per ESC-057, so no suite asserts a rendered-width echo |
| R68 **[NEW 2026-10-25 — D45]** | The news half and the dividend half share one `s0_register` mechanism, so removing the news `"292"` line could silently take the **dividend `"456"`** path (and the chart's dividend markers) with it | H | M | `AC-D45.2` + A79 pin both sides: `"292"` never requested, `"456"` still registered, tick 59 / `_dividend_info` / `dividend_updated` / markers exercised; the surviving event-marker cases in `tests/test_d38_events_news.py` are the regression guard; Build runs a residue grep for `292` and keeps the `"456"` registration untouched |
| R69 **[NEW 2026-10-25 — D45]** | A half-finished deletion (dangling import, a signal connected to a deleted handler, a call to the removed validation module) leaves the app non-importable or crashes at runtime — the D41 worker-death pattern, which is most likely on delete-only tasks spread across many members | H | M | Build splits the work **by member group**, and after each file runs a syntax/import check plus a residue grep for `NewsManager`, `news_digest`, `TradeContextMenu`, `position_close_requested`, `group_close_requested`, `flatten_all_requested`, `validate_order`, `_close_position_by_id`, `placeOrder`; `AC-D45.8` requires the app to launch and the full suite green |
| R70 **[NEW 2026-10-25 — D45]** | Deleting `tests/test_d28_6_close_contracts.py`, `tests/test_d41_retained_order_path.py` and `tests/test_order_validation.py` removes the **only** order-safety coverage; the suite stays green while proving less, and a future change could reintroduce an order path unnoticed | H | M | `AC-D45.4` replaces the removed coverage with a **static invariant** (no `ui/` module calls `placeOrder`, imports `ibkr.validation` or `ui.trade_context_menu`) plus a mocked-client walkthrough asserting **zero** transmits; the coverage loss is recorded in D45's consequences and A81, never presented as "no change" |
| R71 **[NEW 2026-10-25 — D45]** | Docs drift: `USAGE.txt` / `usage.md` / `docs/codebase-map.md` keep advertising the digest, the View menu, or app-placed closes (and a notional cap/validation that no longer gates anything) | M | M | `AC-D45.7` is a grep-checkable doc criterion; A85 scopes the three files; Plan refreshes the Plan-owned map and the Code Reviewer verifies |
| R72 **[NEW 2026-10-25 — D45]** | An **unlisted** test or assertion depends on the removed components (e.g. `tests/test_d41_removal.py`'s `NewsManager` `queue_depth` allow-list, the `tests/test_dock_d18_region.py` fixtures, or a D38 header comment) and turns red or silently stops testing anything | M | M | Enumerate the **assertions** a change invalidates, not just the files it edits (memory 2026-10-23 item 4); run the full suite; `AC-D45.8` names `tests/test_d41_removal.py` explicitly and requires the retained event-marker cases to stay green; DG75 records the unnamed "fourth" deletion |
| R73 **[NEW 2026-10-25 — D45 extension]** | **No in-app panic cancel.** The kill switch was the only way to cancel a TWS-placed order from the app; after D45 a runaway or mistyped order in TWS cannot be stopped from NDThinkChart | H | M | Accepted by the owner (*"it only cancels orders, never places one"*) and recorded in the consequences: **TWS is the cancel surface**; the app cannot create the order it would need to cancel; `USAGE.txt`/`usage.md` say so plainly (`AC-D45.7`); `AC-D45.6` forbids re-adding a cancel path without a new requirement |
| R74 **[NEW 2026-10-25 — D45 extension]** | A **half-removed cancel/protection path** survives (an `order_registry` read in `_on_order_error`, a leftover `_ref_price_for`, an orphan `set_sltp` string) and a later worker "restores" the kill switch or the SL/TP setter because the code still looks live | M | M | The residue-grep list in D45's correction record now includes `kill_btn`, `KillSwitchButton`, `_kill_switch`, `reqGlobalCancel`, `cancelOrder`, `StopLossTargetDialog`, `stop_loss_target_dialog`, `position_sltp_changed`, `group_sltp_changed`, `_on_set_sltp`, `_sltp_dialog`; `AC-D45.4`/`AC-D45.6` are static-scan criteria; A90 records the intentional inert observers so they are not mistaken for leftovers; DG77 |
| R75 **[NEW 2026-10-25 — D45 extension]** | Dropping the **Stop / Target** columns shifts every later column index, so code/tests addressing Strategy/Group by number silently assert the wrong cell — `tests/test_d27_position_id.py:164-165` and `tests/test_d27_position_prices.py:290-291` currently use `8`/`9` | M | H | `AC-D45.10` fixes the 8-column shape; `AC-D45.8` names both files for the `8`/`9` → `6`/`7` adjustment; Task Manager must enumerate invalidated assertions outside the edited files (memory 2026-10-23 item 4), not just the files it edits |
| R76 **[NEW 2026-10-25 — D46]** | A **half-removed chain**: a `connect()` left pointing at a deleted slot, or an `emit` of a deleted signal, raises `AttributeError`/`RuntimeError` at startup — the D41 worker-death pattern, most likely on delete-only tasks spread across many members | H | M | Build splits **by member group** (client → bridge → window → tests → comments) and after each file runs a syntax/import check plus a residue grep for `ibkr.orders`, `order_registry`, `order_status`, `open_order`, `exec_details`, `_on_order_status`, `_update_order_status`, `_on_order_error`; `AC-D46.1`/`AC-D46.2`; `AC-D46.4`'s walkthrough constructs the real window, so an import/connect error cannot pass |
| R77 **[NEW 2026-10-25 — D46]** | **The owner's explicit worry:** the batch silently removes TWS **error visibility** — in particular the 201/103/202 "Rejected"/"Cancelled" wording that lived in the unreachable `_on_order_error` | H | M | `AC-D46.3` is a **positive, per-code assertion** (201, 103, 202 each surface, with TWS's text), not an absence test; the generic line, `classify_error` and the `error_msg` gate are explicitly **KEPT** (not in the removal list); D46 writes the exact message the owner sees instead of implying "no change" |
| R78 **[NEW 2026-10-25 — D46]** | A surviving importer of `ibkr.orders` (or of the `orders` singleton) turns the deletion into an `ImportError` at launch — possibly in a module nobody edited | H | L | `AC-D46.1`'s scanner covers `ui/ services/ data/ ibkr/ config/ main.py`; the D45 mocked-client walkthrough constructs the real `MainWindow`, so an unresolved import cannot pass the suite; Build runs the app (or an import-all probe) before reporting |
| R79 **[NEW 2026-10-25 — D46]** | The D45 static scan's survivor allow-list drifts the wrong way: **not shrunk**, so a resurrected `order_registry`/`_on_order_status` passes silently; or **over-shrunk**, so `classify_error`/`pacing` false-positives | M | M | `AC-D46.4` names the exact **eight** tokens to drop (`order_registry`, `orders`, `UserOrder`, `_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`) and the one to keep (`classify_error`); the scan going red on a re-added name is itself the guard |
| R80 **[NEW 2026-10-25 — D46]** | The suite's meaning shrinks **again** (17 builder cases + 2 registry cases) and a later reader treats a green suite as "order code is fine" | M | H | Recorded as an accepted consequence plus A95: the deleted cases covered code that is itself deleted, so there is **no untested surface left** — that is the point, and it is stated rather than implied |
| R81 **[NEW 2026-10-25 — D46]** | `data/models.UserOrder` is removed but `tests/test_ui_smoke.py` is not adjusted, producing a red suite that looks like a regression from the module deletion | M | L | `AC-D46.5`/`AC-D46.8` name the file and the assertion **together**; A96 records the pairing |
| R82 **[NEW 2026-10-25 — D46 expansion]** | The **first destructive schema step** runs on the owner's **real** database at app launch: a botched `positions`/`trade_groups` migration loses **rows** (not just the two dead columns), or drops `idx_positions_symbol_con_id` / the `trade_group_id` FK and silently breaks the upsert and strategy grouping | **H** | L | `AC-D46.12` states the end state **and** the constraints (row-count preservation, index + FK preserved, idempotent on a fresh and re-opened DB, crash-safe like the `bars` rebuild); two consecutive opens are asserted; the Code Reviewer reproduces the migration on a pre-D46 fixture and compares row counts. **Plan should state whether the DB is copied before the rebuild** — the values are worthless but the rows are not |
| R83 **[NEW 2026-10-25 — D46 expansion]** | An **innocent general symbol is cut** with the order sweep — `classify_error` / `error_msg` (all TWS error visibility), `nextValidId` (connection detection), `IdManager.get_id` (market-data reqIds), the ICT "order blocks" or `sort_order` — and the loss surfaces as an unrelated-looking regression | **H** | L | The inventory's **RETAIN** set names each one **with its consumer** (R1–R12) and `AC-D46.9` asserts the retained set is still present; D40/D25 lifecycle tests and the market-data suite are explicitly unchanged; `D46.10` pins `IdManager`; DG82/DG83 record the two IB-signature cases |
| R84 **[NEW 2026-10-25 — D46 expansion]** | The **widened delete-only scope** exhausts worker step budgets, leaving a file non-importable mid-edit (the D41 pattern: three workers died on L-size deletions) — now with a **schema** task in the same batch | **H** | M | Build splits by **member group** (eight groups in D46's correction record), never by file; after **each** file a syntax/import check **and** the extended residue grep; the storage step (schema + model + account + persistence) is **one** task so the schema and its readers land together (memory 2026-10-15) |
| R85 **[NEW 2026-10-25 — D46 expansion]** | The **documentation trail contradicts itself**: "kept (no migration)" (this morning's ESC-060 correction) and "dropped" (A99) live side by side in `USAGE.txt`, `usage.md`, `docs/architecture.md`, `docs/plan.md` and `docs/codebase-map.md`, and a reader picks the wrong one | M | **H** | `D46.13` is a **grep** criterion over the six files; the trail is required to read **kept → cleared → dropped** with the ESC-060 wording carrying a supersession note; Plan owns architecture/plan/map, Build owns `USAGE.txt`/`usage.md` and comments; DG84 lists the sites |
| R86 **[NEW 2026-10-26 — D47]** | The strangler seam leaks: the two engines diverge (different bar mapping, different study values, different drawing coordinates) and parity is declared on looks, not on values | H | M | `AC-D47.2` (shared `ChartModel` — one value source) + `AC-D47.5` (logical-index parity cases incl. DST/session boundaries) + the kept-updated matrix (`AC-D47.9`); both engines render from the same model, never from parallel logic |
| R87 **[NEW 2026-10-26 — D47]** | Chromium + vendored JS bloat the `.app` past an acceptable size, or signing/notarisation breaks (pending Q61) | M | M | Plan states the measured delta + mechanism; the owner approves (A109); `AC-D47.8` packaging phase is a cutover candidate, not a silent ship |
| R88 **[NEW 2026-10-26 — D47]** | Bridge backpressure: queue-until-ready grows unbounded on a slow renderer, replay-after-crash duplicates bars, or 10 pop-outs exhaust memory (pending Q62) | H | M | `AC-D47.4` (batch shape + replay identity) + DG91/DG90 counters and caps from Phase 2; per-pop-out memory accounted, not assumed |
| R89 **[NEW 2026-10-26 — D47]** | Retiring the density-cap ACs for `barSpacing` (T10/Q60) silently drops the no-overlap guarantee the owner reported under ESC-041 | M | H | `AC-D47.6` retires the language only as Q60 decides; DG94 restates the guarantee in `barSpacing` terms; the rendered-geometry guard survives the engine change |
| R90 **[NEW 2026-10-26 — D47]** | Offscreen QtWebEngine is non-viable in CI, so webengine cases are skipped everywhere and regressions hide behind the manual checklist | M | M | A110/DG88: skipped-never-red marking + the manual checklist as an explicit gate; a skipped case must still name its manual counterpart |
| R91 **[NEW 2026-10-26 — D47]** | Cutover without a soak ships a same-day defect to the owner's live session | H | L | Owner-accepted: no soak is the explicit decision; the triple gate (accept + all-Done/accepted + perf holds) plus the one-clean-live-session delete gate (`AC-D47.8`) is the replacement; Phase 11 needs separate explicit approval |
| R92 **[NEW 2026-10-26 — D47]** | An unmeetable AC is discovered mid-build and is "handled" by weakening it | M | H | Rule 10 (`D47.9`/`AC-D47.9`): escalate + record as a parity row; Code Reviewer fails any phase whose matrix row regresses without an escalation |
| R93 **[NEW 2026-10-28 — D48]** | IBKR rejects one of the new combos (a 321-class duration/bar-size rejection, as in ESC-036) | M | L | `AC-D48.6`: the standalone probe verifies both combos before build completes; a rejection escalates to Requirements — durations are never silently shrunk |
| R94 **[NEW 2026-10-28 — D48]** | Fixed-seconds month bucketing drifts month boundaries (28–31-day months, February) | M | L | A115: calendar-month anchoring; nominal 30-day seconds only where an API demands them; `AC-D48.2` Feb unit case |
| R95 **[NEW 2026-10-28 — D48]** | Hardcoded "six timeframes" enumerations (visibility grids, picker tests, docs) miss the two new entries | M | M | A120 default-visible + DG97; Plan inventories timeframe enumerations; `AC-D48.5`/`AC-D48.7` are the gates |
| R96 **[NEW 2026-10-28 — D49]** | Cold-start restore replays a full backfill per saved pop-out and pressures the IBKR pacing budget | M | M | D49.1 is cache-first through the existing paced path; Plan staggers restores if the saved set is large |
| R97 **[NEW 2026-10-28 — D49]** | Transactional cleanup races a concurrent session update iterating the detaching view | L | M | Disconnect-signals-first ordering (D49.2); an offscreen attach-failure-under-update case |
| R98 **[NEW 2026-10-28 — D49]** | D49.5 verification is read as license to build the per-owner fix unconditionally | M | L | `AC-D49.5` gates the fix on a confirmed lasting effect; Code Reviewer fails a D49.5 diff with no probe record |
| R99 **[NEW 2026-10-28 — D50]** | The per-kind edit matrix (whole-move vs anchor drags across 5 kinds) is genuinely undecided; guessing it writes ACs the owner never asked for | M | H | `AC-D50.1` stays PROVISIONAL until Q67 is answered; no build proceeds on an assumed matrix |
| R100 **[NEW 2026-10-28 — D50]** | Lock enforced only at handle visibility (not at the `drag_drawing` initiation/move surface) leaves locked drawings movable — a silent safety failure | H | M | Q69 pins operation-level semantics; `AC-D50.3` asserts refusal at the operation surface with no store write |
| R101 **[NEW 2026-10-28 — D50]** | The 3.3 recolor decision lands after a D50 build and contradicts the built colour-preservation behaviour | M | M | **RESOLVED 2026-10-28:** owner picked (c) Both (Q70); `AC-D50.4` settled on stored-colour semantics (A130/A132) — residual risk is a later 3.3 change, which would arrive as a new requirements decision, not a silent contradiction |
| R102 **[NEW 2026-10-29 — D49.6]** | Pre-change saved pop-out sets carry no offset field; a wrong fallback silently renders UTC against a non-UTC main chart | L | M | A134 states the fallback (main chart's current offset); `AC-D49.6` asserts the restored offset, not just label output |
| R103 **[NEW 2026-10-29 — D51; RESOLVED 2026-10-29]** | The follow-vs-away threshold or resume rule is guessed before the owner answers, writing ACs and tests the owner never asked for | M | H | **RESOLVED 2026-10-29:** Q72–Q76 answered-owner-confirmed; `AC-D51.1`–`AC-D51.5` FINAL with `Status: READY_FOR_PLAN`; no build proceeds except on the decided rules |
| R104 **[NEW 2026-10-29 — D52]** | IBKR rejects the `30 mins` / `30 D` combo (a 321-class duration/bar-size rejection, as in ESC-036) or the `30 mins` bar-size spelling differs from the picker's key | M | L | `AC-D52.7`: the standalone probe verifies the exact combo before build completes; a rejection escalates to Requirements — durations are never silently shrunk (R93 pattern) |
| R105 **[NEW 2026-10-29 — D52]** | Hardcoded intraday-timeframe enumerations (picker order, visibility grids, `AC-D16.1`/`AC-D16.8` lists, priming table) miss the new entry, so `30 mins` loads but is unselectable, invisible-on, or excluded from backfill/priming coverage | M | M | A140 default-visible + DG99; Plan inventories timeframe enumerations; `AC-D52.5`/`AC-D52.6`/`AC-D52.8` are the gates |

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

**REQUIREMENTS escalations (2026-10-15) — both resolved:**
- **ESC-035 / Q46 / DG64 — MOOT, superseded by D41.** The depth error **2152** (partial venue-permission)
  behaviour no longer needs defining: the D37 depth feed (and, per Q48, the DOM ladder) is being **removed**, so
  there is no depth feed to degrade. No option (a)/(b)/(c) was chosen — the correct resolution is supersession.
  The related **ESC-040** (footprint stuck in `loading`) is likewise **moot** (footprint removed wholesale), and
  **ESC-039** (DOM ladder `SMART` + `isSmartDepth=False`) is **moot** (ladder removed).
- **ESC-038 / Q47 / DG65 — RESOLVED (Q47 answered 2026-10-15; EXTENDED 2026-10-15 by D42/ESC-038; ETH scope added by Q52).** The minimum
  intraday history depth — **30 trading sessions** before the current session — is recorded as
  **`AC-D16.8`** (clarified: a session is counted by bars inside the **current mode's** session window; **all
  five** intraday windows fall short and must extend history backwards) and applies to **both RTH and Ext-Hours
  (ETH)** (`ext_hours=False` and `ext_hours=True`), per **Q52**. Delivering it (chained, paced,
  backwards-extending fetches, since IBKR caps `1 min` at `1 D`) is a **Plan/BUILD** window-strategy concern. The
  **present-but-empty trading day** treatment is recorded as the new **`AC-D16.9`** (mode-aware day presence +
  mode-aware cache, both directions).
- **ESC-042 (NEW 2026-10-15) — RESOLVED by requirements decision (D42.1).** The `AC-D6.4` (unconditional 4-px
  body floor) vs `AC-D7.1` ("gap remains positive") contradiction is decided: the **no-overlap guarantee wins**,
  the body is **capped at the inter-bar pitch**, and the 4-px floor is **density-aware**. This **supersedes** the
  unconditional `AC-D6.4` / "positive gap" `AC-D7.1` wording and is what unblocks BUILD **ESC-041**.
The silent-hole item **ESC-037** remains routed to **BUILD** (its normative target is now **`AC-D16.9`**, for **both** RTH and ETH).

**[NEW 2026-10-15] Batch 18 (D41)** — the owner requested removal of the **D36 footprint**, the **D37 depth heatmap / imbalance / auction** features and "all associated code"; **scope FINALISED 2026-10-15 (Q48/Q49/Q50 answered)**: the **Active Trader DOM ladder** is **also removed** (Q48 = YES), the persisted **`footprint_cache` table + rows are deleted** (Q49 = "delete"), and the **entire Active Trader panel — including the in-app order-entry UI — is removed with the right dock becoming Portfolio-only** (Q50 = YES/YES). D41 carries acceptance criteria `AC-D41.1`–`AC-D41.7`; `AC-D36.*`/`AC-D37.*` are **SUPERSEDED BY D41** (retained for history, DOC-4), and the affected **D18**/**D21.13** clauses are **superseded by D41** with reasons. The **retained order machinery** (`ibkr/orders.py`, `ibkr/validation.py`, the validate-order gate, bracket construction, kill switch) is **kept** for the Portfolio close/flatten/SL-TP paths, and the kept order path's `ref_price` takes a **retained source** (Plan-level detail); the shared substrate reused by the **kept** D38 (news/dividends) and D39 (burst/search) is **explicitly preserved** (see D41 "Scope — KEEP"); **ESC-039 / ESC-035 / ESC-040** are moot. No **blocking** question remains; **Q47** is answered as **`AC-D16.8`** (30 trading sessions). This document carries `Status: READY_FOR_PLAN`.

**[NEW 2026-10-16] Batch 18c (D43)** — the **ESC-036 second clause** (a **REQUIREMENTS** question the owner directed here) is **DECIDED**: D27.9's **"trailing 5-second history"** is **unsatisfiable** for the coarse intraday timeframes (`4 hours` = 14400 s, `1 day` = 86400 s — 5-sec bars cannot span them; IBKR caps `5 secs` at `3600 S`, so the built request `bar_size='5 secs'`/`duration='7200 S'` returns TWS **error 321**). **Resolution (D43.1):** prime with a bar size chosen for the elapsed forming-period span — **`5 secs`** for `1 min`/`5 mins`/`15 mins`/`1 hour`, **`1 min`** (valid up to `1 D`) for **`4 hours`**/`1 day` — with `duration` = the elapsed span clamped into the selected bar size's IBKR-accepted range (`[60 S, 3600 S]` for `5 secs`; `[60 S, 1 D]` for `1 min`). This **SUPERSEDES D27.9's "trailing 5-second history" wording** and **revises `AC-D27.9`**. **P2-T30's first-clause clamp remains correct/required for the fine timeframes**; the **coarse-timeframe bar-size switch is an explicit FOLLOW-UP** (P2-T30 does not deliver it), and P2-T30's `AC1`/`P2-T30-T11` (asserting a `5 secs`/`3600 S` request for 4h/1d) become **stale once the follow-up lands**. See D43, `AC-D27.9` (revised), A74, R65, **DG73**, **Q53** (answered, owner-confirmed-by-default). No blocking question remains.

**[NEW 2026-10-16] Batch 19 (D44) — the collapsed Watchlist becomes a thin vertical bar (OWNER-REQUESTED).** The owner asked that the collapsed
watchlist become a **thin bar** on the left that **expands to the full panel** on click, in the **app's own colour scheme** (the mockup's white rounded pill is
mockup-tool styling only, not a colour choice). The D21.11 collapse already exists, so **D44 changes the collapsed *appearance***: a **thin vertical bar**
(~30px) with **rotated** `WATCHLIST` text in the **app palette** (`#141822`/`#cbd5e1`/`#232938`), click-to-expand restoring the **previous** width, and
click-to-collapse from the retained header button (as today). The layout rules (`WATCHLIST_MIN_WIDTH` / `plan_dock_widths` / `_apply_dock_widths`) must
**honour a collapsed width** instead of snapping back to 150px. D44 **revises** `AC-D21.11.2`/`AC-D21.11.3` (collapsed appearance) and the 150px-minimum
clause of `AC-D13.1`/`AC-D17.2` (now **expanded-state only**), and **revises the `## Non-Goals`** (dated 2026-10-16) rather than leaving a Non-Goal standing
that the feature contradicts. `AC-D44.1`–`AC-D44.8`, A75–A78, R66–R67, `design_gaps.md` **DG74**, and `open_questions.md` **Q54** (owner confirmation
requested; non-blocking defaults recorded). **D1–D43 are NOT reopened.** No blocking question remains.

**[NEW 2026-10-25] Batch 20 (D45) — the News Digest dock (+ the `View` menubar), the Trade Context Menu, the Kill switch and the SL/TP dialog are removed; the app has zero order interaction.**
The owner asked, verbatim, *"I want both removed."* Both are **full removals**: `ui/news_digest_dock.py` + `ibkr/news.py` +
the `View` menubar + the news `"292"` S0 line, and `ui/trade_context_menu.py` + `ibkr/validation.py` + the Portfolio
Close / Close Group / Flatten All wiring.
**Extension (2026-10-25, later — same batch, owner-requested):** *"remove: Kill switch — it only cancels orders,
never places one / SL-TP dialog — local-only targets, never transmitted"*, in the context of *"i dont need to place
any order from the app"*. The end state is therefore **zero order interaction** — the app **places, cancels and
closes nothing**. The **Kill switch** (`kill_btn`, `_on_kill_switch_clicked`, `_kill_switch`, `reqGlobalCancel` +
per-ID `cancelOrder`) and the **SL/TP dialog** (`ui/stop_loss_target_dialog.py`, its two signals, both `MainWindow`
persistence slots, the Portfolio **Stop / Target** columns) are **removed in full**; the `positions`/`trade_groups`
`stop_loss`/`take_profit` **DB columns + model fields are retained but unsettable/unrendered** (A87, no migration). **[D46/A99 REVERSES THIS: both are dropped by a migration — the first destructive schema step in the project; rows, indexes and FKs are preserved.]**
**A82/A83 are REVERSED** (recorded as reversals), and `AC-D45.6` is **INVERTED** — it asserted the switch and dialog
*still work*, and now asserts they are **gone**; `AC-D45.10` is added. Verified in-repo: `reqGlobalCancel`/
`cancelOrder` each had **exactly one** caller (inside the removed `_kill_switch`) and **no** disconnect/teardown
caller, so **no cancel capability is left or re-pointed** (A88).
The **dividend path** (`"456"`, tick 59, `_dividend_info`/`dividend_updated`, chart event markers) is **kept
deliberately**, as are the Portfolio **observation** path (view-only) and the fail-fast port check. **SUPERSEDED BY D46/A92 — the inbound order observers (`_on_open_order`/`_on_order_status`/`_on_exec_details`/`_update_order_status`/`_on_order_error`, bridge signals, client overrides) are REMOVED, not kept inert.** **Accepted consequences:** the app **places, cancels and closes nothing** — no
notional cap, pacing, disconnected guard **or panic cancel** is in play; the whole ordering machinery is
**orphaned together**; and **five** test files are deleted (`test_d28_6_close_contracts.py`,
`test_d41_retained_order_path.py`, `test_order_validation.py`, `test_kill_switch.py`, `test_sltp_honesty.py`), so a
green suite proves less while it stays green. `AC-D38.2`/`AC-D38.3` are **SUPERSEDED BY D45**; `AC-D38.6` and the
portfolio-close clauses of `AC-D41.1`/`AC-D41.4` are **REVISED**; **`AC-D26.3` is MOOT** and **`AC-D26.8`
SUPERSEDED** (no dialog, no switch); the remaining D26 order-entry clauses are moot; `D21.13` is reviewed and
**not** superseded. See D45, Journey 38, `AC-D45.1`–`AC-D45.10`, A79–A90, R68–R75, DG75 / DG77. **D1–D44 are NOT
reopened.** No blocking question remains (lite lane; no `open_questions.md` entry).

**[NEW 2026-10-25 (later)] Batch 21 (D46) — `ibkr/orders.py` and the inert order-observation chain are DELETED; TWS order errors still surface.**
The owner asked, verbatim, *"I dont want anything to do with orders so why is there orders.py ?"* — after D45 had already
removed every order-interaction surface — and, told the module was a fossil with **zero** production callers and a registry
nothing populates, **confirmed opening this batch**. D46 deletes `ibkr/orders.py` (whole file), the **inert inbound chain**
that is its only reader (`IBApiClient`'s `orderStatus`/`openOrder`/`execDetails` overrides → the three `Bridge` signals → the
three `MainWindow` slots → `_update_order_status`) and the **unreachable** `_on_order_error`, so the app holds no order code at
all. `tests/test_order_builders.py` is **deleted** (17 cases for zero-caller builders) while `tests/test_order_rejections.py`
**survives in reduced form** (3 of 5 cases: the surfacing cases repointed at the generic error path, plus `classify_error`,
which gates every TWS error and is **not** order-specific). **TWS error visibility is preserved and specified:** 201 and 103
(severity `fatal`) and 202 (`warning`) still reach the status bar as `Error [<code>]: <TWS's own message>` for 8 seconds —
the richer `Order #<id> Rejected/Cancelled` wording lived in the unreachable handler, so **what the owner sees does not
change**; the app adds no order identity and no verdict (`AC-D46.3`, A93). **A80 and A90 are REVERSED in place**
(A91/A92 — recorded as reversals, original wording kept), **ESC-061 is MOOT** (it asked for a "retained deliberately"
docstring on a module that no longer exists), and **DG76 is resolved** by the deletion. **Plan-owned docs must be corrected
in this batch:** `docs/codebase-map.md` currently states the module "is NOT orphaned and must NOT be deleted" and lists the
observers as retained, and `docs/architecture.md` `S29`/`AR-D45-10` mandate the docstring note (DG81). **KEPT:** the generic
error path and `classify_error`, `id_manager`, the **dropped** stop/target **storage** (**SUPERSEDED BY D46/A99** — the columns and model fields are dropped by migration; rows preserved — the A87 retention and the ESC-060 "cleared" wording are both superseded), the D38 dividend path, D39, the chart, alarms, drawings and D44.
See D46, Journey 39, `AC-D46.1`–`AC-D46.13`, A91–A104, R76–R85, `design_gaps.md` DG78–DG87, and
`open_questions.md` Q56–Q59 (**answered by the owner 2026-10-25**; no blocking item). **D1–D45 are NOT reopened.**

**[NEW 2026-10-26] Batch 22 (D47) — the chart stack migrates to Lightweight Charts behind a `ChartView` seam (strangler; pyqtgraph retained until parity accepted) — OWNER-DIRECTED REVERSAL of the 2026-10-16 decline.** The owner reversed the decline and approved (verbatim 2026-10-26): reverse the decline — YES; no soak, one live-session sign-off before any delete — YES; Phase 0 spike as a single no-prototype exception — YES. See D47, Journey 40, `AC-D47.1`–`AC-D47.9`, A105–A112, R86–R92, `design_gaps.md` DG88–DG96, and `open_questions.md` Q60–Q63 (Q60 answered-by-default YES; Q61–Q63 ANSWERED 2026-10-26, owner-confirmed). **D1–D46 are NOT reopened** beyond the recorded supersessions/reversals (RG-D46-2–RG-D46-7 + RG-D46-9 applied in this revision). No blocking item remains — Q61–Q63 ANSWERED 2026-10-26 (no scope change; the recommended defaults the phase already planned against, now owner-confirmed); `requirements.md` carries `Status: READY_FOR_PLAN`.

Status: READY_FOR_PLAN — D24–D41 owner-decided/as-built (D24–D28 approved and code-verified 2026-10-14; D36–D40 as-built with acceptance criteria authored, **D36/D37 now SUPERSEDED BY D41**); **D41 (Batch 18)** — the D36/D37 **+ the entire Active Trader panel (DOM ladder + order-entry UI)** removal is specified with `AC-D41.1`–`AC-D41.7` (Q48/Q49/Q50 answered 2026-10-15), the **right dock is Portfolio-only** (D18/D21.13 clauses superseded by D41), the **retained order machinery** is kept for Portfolio's close/flatten/SL-TP paths, and the shared substrate is preserved — **REVERSED BY D45 (2026-10-25, incl. its later extension): those paths, the kill switch and the SL/TP dialog are all removed**; **`AC-D16.8`** records the 30-trading-session intraday depth floor (Q47), now covering **both RTH and Ext-Hours (ETH)** per **Q52**; **Batch 18b (D42)** resolves the two REQUIREMENTS-routed Code Reviewer escalations — **ESC-042** (the `AC-D6.4` vs `AC-D7.1` contradiction: the **no-overlap guarantee wins**, the body is capped at the inter-bar pitch and the 4-px floor is **density-aware**, superseding the unconditional `AC-D6.4` / "positive gap" `AC-D7.1` wording — unblocks BUILD **ESC-041**) and **ESC-038** (intraday depth floor `AC-D16.8` clarified — sessions counted by bars inside the **current mode's** session window, all five intraday windows fall short — plus the new **`AC-D16.9`** for a present-but-empty trading day; the requirements side of BUILD **ESC-037**) — with A72–A73, R63–R64, DG68 resolved + DG72, and **Q51/Q52 answered 2026-10-15 (Q51 confirmed the zero-gap default; Q52 widened `AC-D16.8`/`AC-D16.9` to Ext-Hours, superseding the RTH-only default)**; D1–D41 otherwise unchanged; **Batch 20 (D45)** adds the removal of the **Kill switch** and the **SL/TP dialog** (owner extension 2026-10-25) so the app has **zero order interaction** — `AC-D45.6` inverted, `AC-D45.10` added, A82/A83 reversed (A87–A90), DG77; **Batch 21 (D46 — scope EXPANDED 2026-10-25 by the owner's Q56–Q59 answers)** deletes **every order-related coding path**: `ibkr/orders.py` and the inert order-observation chain (client order overrides → three bridge signals → three `MainWindow` slots → `_update_order_status`) plus the unreachable `_on_order_error`; the three **zero-consumer order utilities** (`OrderRateLimiter`/`order_limiter`, `MAX_ORDER_NOTIONAL`, the order-fill sound); **`IdManager.reserve`** (the module and `get_id` stay — they allocate market-data reqIds); and the **stop/target storage** — the `positions`/`trade_groups` `stop_loss`/`take_profit` **columns and model fields are DROPPED** (A99, **reverses A87**; the first destructive schema step, justified by ESC-060: the values were already cleared by the first live update, so nothing that survived is destroyed), with **A87/A97 reversed in place** and **A92/A93/A96 owner-confirmed**. `AC-D46.1`–`AC-D46.13`, A91–A104, R76–R85, DG78–DG87, **ESC-061 moot**, **DG76 resolved**, and **201/103/202 still surfacing** on the status bar (`AC-D46.3`). A closed **symbol inventory** (`D46.9`) makes "all of it" auditable and protects the general code that merely carries an order name. No blocking question remains.


**[NEW 2026-10-28] Batch 23 (D48) — add `1 week`
 (2Y) and `1 month` (10Y) timeframes (OWNER-REQUESTED; P8 lite).** The owner asked for weekly bars covering 2 years and monthly bars covering 10 years (IBKR `1 week` / `1 month` bar sizes; the picker stops at `1 day`). D48 adds the two `TIMEFRAME_CONFIG` rows (`1 week` → `1 week` / `2 Y`; `1 month` → `1 month` / `10 Y`), Monday-anchored weekly + calendar-month aggregation, planner/backfill treatment (daily+ timeframes skip the `AC-D16.8` intraday floor; day-presence is already bar-granular), UI picker inclusion, and RTH/ETH irrelevance, with acceptance on a **standalone IBKR duration probe + green suite**. Week-anchor day, month-span durations and the year-unit spelling are **analyst lite defaults** (A113–A120). See D48, Journey 41, `AC-D48.1`–`AC-D48.7`, A113–A120, R93–R95, `design_gaps.md` DG97–DG98. **D1–D47 are NOT reopened** beyond the recorded timeframe-enumeration extension (`AC-D16.1`'s "all six timeframes" now reads eight; the `AC-D27.9` per-span table gains two rows). No blocking question remains (lite lane; no `open_questions.md` entry).

**[NEW 2026-10-28] Batch 24 (D49) — pop-out robustness (5 findings + D49.6 timezone handoff, nothing dropped) — OWNER-ORDERED, EXTENDED 2026-10-29.** Restore routes through cached bars + aggregator creation + realtime subscribe (existing history/backfill/pacing path; reproduce-first test); attach is transactional with explicit acquisition-state tracking; host-startup failure shows an in-pop-out error state with the diagnostic log retained (ESC-070 model, different site); drawing sync fans out once at the change point (behavior pinned in tests first); the hold-count over-statement is verified before any fix (idempotent per-owner acquire/release only if a lasting effect is confirmed, else verified close); D49.6 passes the main chart's timezone offset at creation (no `tz_offset=0.0`) and persists/restores it (pre-change saves fall back per A134). See D49, Journey 42, `AC-D49.1`–`AC-D49.7`, A121–A126/A133–A134, R96–R98/R102, and `open_questions.md` Q64–Q66 (answered 2026-10-28). **D1–D48 are NOT reopened.** No blocking question remains for D49; D49 carries `Status: READY_FOR_PLAN`.

**[NEW 2026-10-29] Batch 26 (D49.6 + D51) — timezone handoff READY; follow-live viewport FINALISED 2026-10-29.** **D49.6** adds the owner-ordered timezone handoff to D49 (creation passes the main chart's offset, no `tz_offset=0.0`; persisted/restored with the pop-out set; pre-change saves fall back per A134). Fully derivable — no question asked; the pre-existing `history intact` guard is renumbered D49.7/`AC-D49.7` (recorded in place, no criterion changed). D49 carries `Status: READY_FOR_PLAN`. **D51** (new): the main-chart viewport must not yank to the newest bar on live updates while scrolled back — follow-vs-away (Q72), auto-resume (Q73), Fit/reset (Q74), per-symbol memory (Q75) and same-vs-new-symbol replacement (Q76) are answered-owner-confirmed 2026-10-29 in `open_questions.md`; `AC-D51.1`–`AC-D51.5` are FINAL (Journey 44, A135, R103). D51 carries `Status: READY_FOR_PLAN`. **D1–D50 are NOT reopened.**


Status: READY_FOR_PLAN
