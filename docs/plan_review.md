# Plan Review — NDThinkChart Batch 17 (D23: two D22 post-build quality corrections)

## Review Status
Status: APPROVED

## Validation Summary
Validation **pass 2 (retry 1 of 3)** for the **D23 increment**. It validates
`docs/plan_proposal.md` (`Status: READY_FOR_VALIDATION`) and `docs/architecture_proposal.md` against
`docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised 2026-10-07 with D23 /
Journey 28 / `AC-D23.1.1`–`AC-D23.2.4` / A53–A55 / R49–R50 / `DG45`). Existing-repo mode (marker
sentence + Current Tech Stack present; **PyQt6 + pyqtgraph + official `ibapi` + SQLite** is a hard
constraint). D1–D22 are not re-planned.

**Escalation routing note.** `docs/code_review/escalations.json` holds **ESC-030** and **ESC-031**
with `"routed_to": "BUILD"` (not `PLAN`), both `status: open`; there is **no** `PLAN`-routed entry, so
this is a normal forward validation cycle (I did not edit the escalations file). The Requirements
Analyst captured both as **D23**, and the proposal addresses them.

**RC-1 (blocking, previous pass) — resolved.** Plan adopted option (a): the pre-fix-red evidence for
D23.1 is now a **code-shape/source assertion**. The Validator independently re-ran the check on the
current tree: `inspect.getsource(MarketDataManager.cancel_contract_details)` yields an `ast.Attribute`
node with `attr == 'cancelContractDetails'`, the substring `self.client.cancelContractDetails(` is
present, and `getattr(self.client, …)` is **absent** → the assertion is genuinely **red pre-fix** and
green after the guard. The behavioural no-exception case is honestly reclassified as a **post-fix
guard** (independently confirmed: `MarketDataManager(SimpleNamespace(reqContractDetails=…))
.cancel_contract_details(7)` returns normally on the current pre-fix tree, because the retained
`try/except Exception: pass` swallows the bare `AttributeError`). Phase 1's exit condition, PA-D23-3,
S16, the Non-Functional Q8 bullet, AR-D23-2 and the Coverage Map are all updated; the "D23.1
verification note (RC-1 closure — not a gap)" is recorded in Flagged Issues. Q8 is now honestly met
for D23.1.

**RC-2 (minor, previous pass) — resolved.** The stale Codebase-Summary line references are refreshed
and were re-verified against source: `WatchlistPanel` **816 lines**, `add_symbol :664`, header strip
`:282–289`, D21.5 column menu `:605` (the D23 targets `remove_symbol :682–728`,
`cancel_contract_details :78–84`, `clear() :730` remain correct).

**Verdict.** All three phases are fully specified and implementable without any new architectural
decision; both fixes are correct, additive and behaviour-preserving; D23.2's fix and pre-fix-red
evidence are sound; no D1–D22 re-plan; no new dependency/schema/live-order-path change. **Approved.**

## Requirements Coverage (one line per step)
- **Coverage:** every `AC-D23.1.1`–`AC-D23.1.4`, `AC-D23.2.1`–`AC-D23.2.4`, Journey 28, A53–A55,
  R49–R50 and `DG45` is mapped to a phase with a verdict — **PASS**.
- **Completeness:** Tech Stack (existing S1/S2/S14 first, then `[new/changed]` S3/S15/S16), Codebase
  Summary, Summary, System Components, Data Model, Integration Points, Non-Functional Approach and
  Architecture Risks are all present, each decision carrying rationale + alternatives — **PASS**.
- **Consistency:** no contradiction — the guard satisfies the requirement's "no raised/swallowed
  `AttributeError`"; the retained containment keeps `AC-D23.1.3`; the narrow `_row_data.pop` yields
  `set(_row_data.keys()) == set(range(rowCount()))` for first/middle/last/only (traced n=1…3) and
  keeps `_prev_close`/`_last_price` reqId-keyed; phases depend only on defined work — **PASS**.
- **Plan quality:** three ordered milestone phases (guarded cancel + test; `remove_symbol` key fix +
  test; reconciliation + non-regression), each with goal / covered ACs / dependencies / deliverables /
  exit condition; no per-task or per-criterion test spec; no task-level dependency graph — **PASS**.
- **Task Manager readiness:** can Task Manager build a valid task graph without a new architectural
  decision? **Yes** — guard shape, docstring facts, fake shapes, narrow pop fix, test shapes, and the
  `S3`/`AC-D22.2.3` reconciliation owners are all fixed — **PASS**.
- **Scope integrity:** D23 supersedes only the task-level `AC-D22.2.3` and reconciles `S3`; adds/
  removes no product scope; `AC-D22.1`–`AC-D22.9` stand — **PASS**.
- **Existing-repo compliance (step 7):** all six checks **PASS** (see below).

## Architecture Findings
- The D23.1 fix is correct as a capability-guarded no-op (`getattr(self.client,
  'cancelContractDetails', None)` + call-if-present inside the retained containment): correct on the
  pinned dep today, forward-correct if a future `ibapi` exposes the method. `S3` is reconciled in
  `docs/architecture.md` (written this cycle in `## D23 increment` S3, with a cross-reference note on
  the D22 `S3` row).
- The D23.2 fix is correct (pop the removed key before the existing shift); FieldKey-bound values are
  untouched, so `_rebuild_table`/`_set_cell` do not regress.
- No new dependency, no schema change, no new integration, no live-order-path change; the pinned
  `ibapi` version is not changed.

## Plan Findings
- Phases are correctly structured and coarse enough for Task Manager; Phases 1 and 2 touch **fully
  disjoint** file sets (`ibkr/market_data.py` + its test vs `ui/watchlist_panel.py` + its test) and
  may share one wave; Phase 3 follows.
- D23.1's pre-fix-red evidence is now genuine (code-shape/source assertion) and its behavioural
  tests are honestly labelled post-fix guards. D23.2's last-row assertion is genuinely red pre-fix.
- Assumptions PA-D23-1…PA-D23-10 are plan-level and encode no requirements decision.

## Existing Repo Compliance
Run against an existing PyQt6 + pyqtgraph + official `ibapi` + SQLite terminal (`requirements.md`
contains the literal marker sentence and a Current Tech Stack). Checks:

- **Codebase Summary present and substantive — PASS.** Inventories the SQLite `watchlist` table and
  access helpers, the `WatchlistPanel` in-memory row-keyed state, `MarketDataManager`,
  `IBApiClient`/`IBBridge`, `ContractLookupService._pending`, `MainWindow`, `data/db.py`, the key
  entry points, the existing integrations, and five source-validated facts.
- **Existing stack respected — PASS.** S1/S2/S14 keep Python 3.11+ / PyQt6 / pyqtgraph / official
  `ibapi` (pinned `9.81.1.post1`, live 7496 only) / numpy / SQLite / PyInstaller / pytest-qt
  unchanged and **listed before** the D23 rows; nothing is replaced or deprecated; no version bump.
- **Labels present — PASS.** System Components, Data Model and Integration Points each mark every
  item `[existing]` / `[new]` / `[new/changed]`.
- **Additive-only — PASS.** Only two method bodies are corrected (`cancel_contract_details`,
  `remove_symbol`) plus their tests; the D22 change set is not reopened; the request/persistence
  paths are untouched.
- **Codebase Summary consistent with the proposal — PASS.** Every `[existing]` item named appears in
  the Codebase Summary and was confirmed in source; the `[new/changed]` items are exactly the two
  methods, their docstrings and the two test modules.

## Required Changes
**None.** RC-1 and RC-2 from pass 1 are resolved and independently re-verified.

## Requirements Escalations
**None.** The RC-1 closure is a plan-level verification correction, not a requirements defect;
`AC-D23.1.1`'s stated behaviour is implementable and is implemented by S3. No
`ESCALATED_TO_REQUIREMENTS` entry is added to `docs/plan_notes.md`.

## Task Manager Readiness
**Yes.** Task Manager can decompose the three phases into tasks with acceptance criteria and tests
without inventing any architecture. The canonical artifacts (`docs/architecture.md` `## D23
increment`, `docs/plan.md`, `docs/plan_notes.md` RG-D23-1) carry the reconciled `S3`, the phased D23
plan, and the reconciliation record. Phase 3's Task-Manager-owned `AC-D22.2.3` rewrite (task
`D22-02` in `docs/tasks/task-graph.json`) is directed by `AC-D23.1.4` and is the only task-graph
edit expected.

## Final Decision
Status: APPROVED


---

## As-built documentation refresh — D24–D40 promotion (2026-10-14, `b366b19`)

> **Scope.** This is a **documentation refresh (as-built promotion)**, **not** a new design
> cycle and **not** a new Plan→Validator revision loop. The D23 decision above is unchanged.
> `docs/architecture.md` was refreshed from the as-built branch draft
> (`origin/docs/d24-d28-requirements-architecture`) so the canonical artifact describes the
> merged D24–D40 work; `docs/plan.md` was refreshed to keep its as-built D36–D40 record and to
> add a D24–D28 as-built pointer section. **No architectural decision changed**, no escalation
> was reopened, and no requirements gap was opened.

**Why the refresh (staleness).** The canonical `docs/architecture.md` header/body stopped at the
D22 baseline (`286341e`) and carried a D16-era “graphify staleness” note; `docs/plan.md` stopped
at D23. Both are now current as-built at `b366b19`.

**Validation performed (existing-repo rule).** The promoted Codebase Summary and the D24–D40
increment sections were validated against the **current source** (the repository is
authoritative), with `graphify` used for discovery only. Graph state: **4,776 nodes / 10,509
edges / 251 communities**, `built_at_commit = b366b19` (rebuilt 2026-10-14) — the D16 staleness
is cleared. Verified in source (spot list): `ui/ticker_session.py::TickerSession` (`:61`),
`ui/popout_window.py::PopoutChartWindow` (`editable=False`), `data/popout_store.py` + the
`popouts` table, `services/alarm_monitor.py::AlarmMonitor` (`pause_all`/`resume_all`/
`_pause_start`), `AlarmStore.symbols_with_active_alarms`, `ibkr/pacing.py` (rolling-600 s
`PacingManager` + `OrderRateLimiter`), `ibkr/stream_health.py`, `ibkr/tick_history.py`,
`ibkr/subscription_manager.py` (`DEPTH_HEATMAP`/`S0_TICKS`), `services/{footprint_service,
depth_heatmap,volume_baseline,symbol_search,time_collapse_service,md_line_guard}.py`,
`data/footprint_cache.py`, `data/events/{provider,ibkr_source,yfinance_source}.py`,
`ibkr/news.py`, `ui/{footprint_item,depth_heatmap_item,news_digest_dock,event_marker_overlay}.py`,
`ibkr/contracts.py` (`INDEX_PROXY`/`footprint_cache_key`), `ibkr/client.py` (`DisconnectClass`,
`_do_reconnect`, the multi-signature `error()` shim), `ibkr/validation.py`, and the additive
tables `popouts`/`footprint_cache`/`yfinance_events_cache`/`volume_baseline`.
`config/settings.py` line refs corrected (`MAX_POPOUTS` `:42`, `SESSION_BAR_CAP` `:45`).

**Suite figure.** **1,020 tests** is the last recorded green figure, at `b366b19` (the D40
as-built record on `origin/docs/d24-d28-requirements-architecture`); it is consistent with the
lineage (1009 at D39 + 11 D40 tests). Independently, this checkout **collects 1,020 tests**
(2026-10-14). A green run was **not** re-observed here — four modules (46 tests) cannot import
under the venv's `ibapi 9.81.1.post1`, which predates the pinned `ibapi-latest==10.51.1`.

**Validation steps (short form).**
- **Coverage — PASS.** Every D24–D40 increment in the promoted architecture maps to source and a
  requirement reference; no requirement is weakened or reinterpreted. (Whole-document D1–D23
  coverage was established in the earlier cycles and is unchanged.)
- **Completeness — PASS.** Tech Stack (now including the D36–D40 dependency pins and the
  pinned-`ibapi` capability facts), System Components, Data Model, Integration Points,
  Non-Functional Approach and Architecture Risks are all present, each decision carrying
  rationale and alternatives.
- **Consistency — PASS.** No contradiction; as-built tense/status now matches `main` (D1–D40 all
  merged and ancestors of `b366b19`).
- **Plan quality — PASS.** The plan keeps its D23 phases and records D24–D28 as-built pointers
  plus the D36–D40 work items; no task-level breakdown, no task dependency graph.
- **Task Manager readiness — no new decision.** The refresh introduces nothing Task Manager must
  decide; **no Task Manager action is required** by this refresh.
- **Existing-repo compliance — PASS.** Marker sentence + Current Tech Stack preserved; the
  existing stack is listed before new additions; `[existing]`/`[new]`/`[new/changed]` labels kept
  throughout; the Codebase Summary is substantive and graph-consistent; no unflagged stack
  replacement (the `ibapi` pin bump is the D36-flagged 38a.0 alignment, recorded in Tech Stack
  and in `plan.md`).

**Required changes.** None.

**Requirements escalations.** None — a documentation refresh opens no requirements gap.


## Final Decision
Status: APPROVED (unchanged — the D23 approval above stands; this refresh changes no
architectural decision and requires no Task Manager action)

---

## Scoped refresh — owner decisions Q41–Q45 propagated; D24–D40 plan-vs-code verification (2026-10-14)

> **Scope.** A **scoped documentation refresh on an existing-repo run**, not a new Plan→Validator
> cycle: no new `docs/plan_proposal*.md` / `docs/architecture_proposal*.md` was produced and no new
> architectural decision is available or was made. The input is the **Requirements Analyst's
> 2026-10-14 update** to `docs/requirements/requirements.md` (+ `open_questions.md` `Q41`–`Q45`,
> `design_gaps.md` `DG46`–`DG53`), which settles the items the previous refresh had left as
> owner-open. **This record does not reopen or change the standing `APPROVED` decisions above.**

### Review Status
Status: APPROVED (standing decision unchanged; this append is a scoped propagation + verification record)

### Validation Summary
The authoritative input is `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, revised
2026-10-14: D24–D28 `as-built / APPROVED`, `AC-D24.10`, A66/A67, D36–D40 feature sections with
authored `AC-D36.*`–`AC-D40.*`, retired gate, DG53). Existing-repo mode (marker sentence + Current
Tech Stack present; PyQt6 + pyqtgraph + official `ibapi` + SQLite is a hard constraint; labels kept).
**No `docs/code_review/escalations.json` entry is `routed_to: PLAN` and `open`** — ESC-030/ESC-031 are
`routed_to: BUILD` and `addressed`; nothing to process (file not edited).

Propagated (all settled by the owner; none re-litigated):

1. **Q41 — D24–D28 as-built / APPROVED.** Both artifacts now state it; no residual "DRAFT" /
   "unmerged" / "pending owner review" wording remains for D24–D28. The owner's explicit ask — a
   **feature-by-feature plan-vs-code cross-check of D24–D28 and D36–D40** — was performed and its
   result is recorded in `docs/plan.md` (§ *Plan-vs-code verification — D24–D40*).
2. **Q42 — the "gated in TWS" planning constraint is retired.** Removed/rewritten in both artifacts
   (including the `DEC-4` reference and the `architecture.md` D21 `S2` row, the only surviving
   "gated at TWS" wording). The still-binding safety facts are retained verbatim:
   `IBKR_PORT != 7496` fail-fast (`check_live_port`), explicit user action per order, confirm dialogs,
   no automated test transmits an order.
3. **Q43 — pop-outs default always-on-top OFF.** Reflected as `AC-D24.10` / A66 in both artifacts,
   citing `ui/popout_window.py:56` and `:289`.
4. **Q44 — D37 depth heatmap default ON.** The stale plan line ("owner decision pending … awaiting
   owner confirmation 2026-10-13") is rewritten as **owner-confirmed ON (2026-10-14)**; A67 recorded
   in both artifacts; the reviewer's OFF recommendation is kept as an **accepted, overridden
   trade-off** under the D37 architecture risks (not an open question).
5. **Q45 — D36–D40 acceptance criteria now exist.** Every `AC-D36.*`–`AC-D40.*` citation in both
   artifacts was re-checked against the authored text — see *AC citations checked* below; each is
   consistent and none needed changing.
6. **DG53 — the three D24 requirement-vs-code corrections** were mirrored: the session emits
   **`bar_updated` + `bars_refreshed`** (not `bars_updated`); there is **no per-pop-out "connecting"
   indicator** (main-window `conn_badge` only); the 10-cap **refuses the 11th with a status-bar
   message** and does **not** `setEnabled(False)` the affordance.

### D24–D40 plan-vs-code verification (owner-directed, Q41/DG53)
Cross-checked against the merged code at `b366b19` (= `origin/main`); **the plan/architecture describe
what shipped**, after the drift corrections below. Verified in source: `MAX_POPOUTS = 10`
(`config/settings.py:42`), `SESSION_BAR_CAP = 5000` (`:45`), `LIVE_PORT = 7496` + `check_live_port`
(`:11`/`:20`), `MAX_ORDER_NOTIONAL = 25000` (`:39`), `_always_on_top = False`
(`ui/popout_window.py:56`) + toggle (`:289`), `DepthHeatmapItem` added unconditionally
(`ui/chart_panel.py:368`) with `_depth_enabled_ui = True` (`:370`), `TickerSession` signal pair
(`ui/ticker_session.py:65–73`), pop-out cap refusal (`ui/main_window.py:840–846`),
`CACHEABLE_SYMBOLS = {"SPX","SPY","QQQ","ES","NQ"}` (`data/footprint_cache.py:26`),
`MD_LINE_CAP = 100` / `MD_LINE_WARN_AT = 90` (`services/md_line_guard.py:16–17`),
`DEFAULT_Z_THRESHOLD = 4.0` / `MIN_WARMUP_BARS = 5` / `N_BASELINE_BARS = 30` /
`MAD_FLOOR_RATIO = 0.05` (`services/volume_baseline.py:58–66`), and the merge ancestry of
`89fe152` / `efffc51` / `9958891` / `8599ce4` / `83f792a` under `b366b19`.

**Drift found and corrected (five items — no architectural decision involved):**

| # | Drift | Artifact(s) corrected |
|---|---|---|
| 1 | Pop-out cap described as "the affordance is **disabled** at the cap" | `architecture.md` (§ Pop-out window architecture, delta-table row), `plan.md` (D24 feature row) |
| 2 | Session signal list named a single **`bars_updated`** | `architecture.md` (§ The session object) |
| 3 | D24 disconnected pop-out implied a per-pop-out "connecting" indicator | `architecture.md` (§ Pop-out window architecture, delta-table row), `plan.md` (D24 feature row) |
| 4 | D37 depth-heatmap default "pending owner confirmation" | `architecture.md` (D37 Non-Functional + Architecture Risks), `plan.md` (D37 deviation 1 + status) |
| 5 | Retired "gated in TWS" wording still present | `architecture.md` (D21 `S2` row; Q42 note added to the D24/D25/D28 header) |

Two further factual corrections were applied at the owner's direction, neither architectural:
the **suite figure** is now the **verified** current number (1,020 collected → **1,016 passed /
4 failed**, the 4 being pre-existing offscreen D19/D20 toolbar-geometry assertions, stated as
**open, not silently green**) rather than the unverified "last recorded green" note; and the
**D23 capability guard** is now described **version-neutrally** (absent on `9.81.1.post1` **and**
on the current `ibapi-latest==10.51.1`, re-verified 2026-10-14) instead of as a `9.81.1.post1`-only
fact. **Dependency pins re-checked:** `requirements.txt` reads `ibapi-latest==10.51.1` and
`yfinance==1.7.0` exactly as recorded.

### AC citations checked (`AC-D36.*`–`AC-D40.*`, plus the D24/D25/D28 IDs touched)
- **`AC-D36.3`** (`architecture.md` § D36 Integration Points; `plan.md` D36 status) — authored text:
  "no tick-by-tick; no mock endpoints" → `reqHistoricalTicks` only, zero `reqTickByTickData`, no
  faked/stubbed endpoint in the production tree. **Consistent.**
- **`AC-D38.4`** (`architecture.md` § D38 Codebase Summary; `plan.md` D38 status) — authored text:
  corporate-events-only guard rejecting non-corporate types at the provider boundary; yfinance the
  sole secondary source. **Consistent.**
- **`AC-D40.1`, `AC-D40.2`, `AC-D40.3`, `AC-D40.4`** (`plan.md` D40 work-item "Tests → AC" column) —
  authored text: `.1` disconnect classification + pause, `.2` resume without phantoms, `.3` gap report
  + staging, `.4` transient drops unaffected. **Consistent** (classification/pause → `.1`; resume →
  `.2`+`.3`; transient → `.4`).
- **`AC-D24.5` / `AC-D24.9` / `AC-D24.10`** — `.5` cap (re-checked against the narrower shipped
  behaviour, see drift #1), `.9` restore (the merged single block per DG48), `.10` always-on-top OFF
  (Q43). **Consistent.**
- `AC-D25.3` and `AC-D28.4` (pre-existing citations) re-checked as unresolved references — both are
  defined in `requirements.md` and match the surrounding text. **Consistent.**
- No citation was found to contradict the authored criteria, so **none was changed**; the only edits
  were the drift corrections tabulated above.

### Validation steps (short form) — Coverage / Completeness / Consistency / Plan quality / Readiness
- **Coverage — PASS.** Every owner decision Q41–Q45 and every DG53 correction is represented in both
  artifacts; the D24–D40 features in `plan.md` map to the shipped code and to defined ACs; no
  requirement was weakened, reinterpreted, or silently removed.
- **Completeness — PASS.** Tech Stack Decisions (with the D36–D40 dependency pins and the
  version-neutral pinned-`ibapi` capability facts), System Components, Data Model, Integration Points,
  Non-Functional Approach and Architecture Risks are all present, each decision carrying rationale.
- **Consistency — PASS.** No contradiction: the retired gate is gone while the safety behaviour is
  retained; as-built tense/status matches `main`; the depth-heatmap default (ON, owner-confirmed) and
  the D36 footprint default (OFF) are stated distinctly; the suite figure is stated as
  **1016 passed / 4 failed**, never as fully green.
- **Plan quality — PASS.** The plan keeps its D23 phases + the as-built D24–D40 records; the new
  feature table and the verification table stay at milestone level — no per-task breakdown, no task
  dependency graph, no per-task test specification.
- **Task Manager readiness — no new decision.** Nothing in this refresh introduces a decision Task
  Manager must make; **no Task Manager action is required** (every D24–D40 feature is already built and
  merged, and the D23 phases were already approved).
- **Existing-repo compliance (step 7) — PASS.** Marker sentence + Current Tech Stack preserved;
  existing/constrained choices listed before new additions; `[existing]` / `[new]` / `[new/changed]`
  labels kept throughout System Components / Data Model / Integration Points; the Codebase Summary is
  substantive, source-validated and consistent with the proposal; no unflagged stack replacement (the
  `ibapi` pin bump remains the D36-flagged 38a.0 alignment, recorded in Tech Stack and `plan.md`).

### Required Changes
**None.**

### Requirements Escalations
**None.** All five owner items are settled in `requirements.md`; DG46–DG53 are `resolved`/
`addressed`. `docs/plan_notes.md` was **not** touched in this cycle — no requirements or planning gap
remains open, so no new `RG-*`/`FI-*` entry was warranted and no `ESCALATED_TO_REQUIREMENTS` marker
was added.

### Residual items (recorded, non-blocking, no decision required)
1. **Four open pre-existing test failures** — `tests/test_toolbar_d20.py::test_T62_T02/T04/T05` and
   `tests/test_toolbar_scroll_d19.py::test_T53_T02` (offscreen viewport-vs-toolbar geometry). Unrelated
   to D24–D40; recorded as open in `architecture.md` (header + provenance note) and `plan.md` (D40
   status). If the owner wants them fixed, that is a small D19/D20 follow-up for Build — it is not a
   planning or architectural gap.
2. **Stale in-code comment** — `ui/chart_panel.py:370` still reads `# default ON (owner to confirm)`
   although the owner has now confirmed ON (Q44). Build-owned source, outside this agent's writable
   files; recorded here so it is not mistaken for a documentation contradiction. No artifact of mine
   asserts "pending" any longer.

### Final Decision
Status: APPROVED (standing D23 approval unchanged; this append records the Q41–Q45 propagation, the
D24–D40 plan-vs-code verification, and that **no architectural decision changed**)
