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
1. **[RESOLVED 2026-10-14 by `99fb8fa`] Four open pre-existing test failures** — `tests/test_toolbar_d20.py::test_T62_T02/T04/T05` and
   `tests/test_toolbar_scroll_d19.py::test_T53_T02` (offscreen viewport-vs-toolbar geometry). Unrelated
   to D24–D40; recorded as open in `architecture.md` (header + provenance note) and `plan.md` (D40
   status). If the owner wants them fixed, that is a small D19/D20 follow-up for Build — it is not a
   planning or architectural gap. **Fixed:** the commit declares the theme font inside the
   `#MainToolbar` rule and raises the D19/D20 `_WIDE_SIZE` fixture 2,400 → 2,600px; the suite is now
   **1,020 passed / 0 failed**, and both artifacts now state that (see the second-pass record below).
2. **[RESOLVED 2026-10-14 by `99fb8fa`] Stale in-code comment** — `ui/chart_panel.py:370` read `# default ON (owner to confirm)`
   although the owner had confirmed ON (Q44). Build-owned source, outside this agent's writable
   files; recorded here so it is not mistaken for a documentation contradiction. No artifact of mine
   asserts "pending" any longer. **Fixed:** the comment now reads
   `# default ON (owner-confirmed 2026-10-14, Q44/A67)`.

### Final Decision
Status: APPROVED (standing D23 approval unchanged; this append records the Q41–Q45 propagation, the
D24–D40 plan-vs-code verification, and that **no architectural decision changed**)

---

## Scoped as-built verification — D1–D40 artifacts vs the shipped code at `262ec81` (2026-10-14, second pass)

> **Scope.** A **scoped verification pass on an existing-repo run**, not a new Plan→Validator cycle:
> no `docs/plan_proposal*.md` / `docs/architecture_proposal*.md` was produced and no new
> architectural decision is available or was made. This record does **not** reopen or change the
> standing `APPROVED` decisions above. It exists because two commits landed *after* the previous
> refresh — `99fb8fa` (toolbar theme font declared inside the `#MainToolbar` rule; D19/D20
> `_WIDE_SIZE` fixture 2,400 → 2,600; D37 comment) and `262ec81` (three salvaged docs +
> `USAGE.txt`) — and the knowledge graph at `graphify-out/graph.json` was built at `b366b19`, i.e.
> behind both. Nothing was taken from the graph unverified; every claim below was re-checked
> against the source.

### Review Status
Status: APPROVED (standing decisions unchanged; this append records a verification pass)

### Validation Summary
The authoritative input is the source at `262ec81` (= `origin/main`), the previously validated
artifacts, and `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`). Existing-repo mode
holds (marker sentence + Current Tech Stack present; labels kept). No
`docs/code_review/escalations.json` entry is `routed_to: PLAN` and `open`, so there was nothing to
process (file not edited).

**Verdict: the artifacts are in sync with the shipped code.** Every D24–D40 work item, every
`RouterMode`/TR-1…TR-17 cell, the D2/Q33 chip lane, the D6/D9 ordering contract, D11 stacking, the
D37 depth default, the D24 pop-out cap / always-on-top default and the D40 pause/resume ordering
describe what the code does. **No behavioural drift was found.** Six *record/claim* corrections
were applied — all factual, none architectural. Two of the previous pass's residual items are
resolved by `99fb8fa`.

### Corrections applied (all factual — no architectural decision)
| # | Was wrong | Now reads | Evidence |
|---|---|---|---|
| 1 | Suite "1,020 collected, **1,016 passed / 4 failed** … open, not silently green" (architecture header + Suite-figure provenance; `plan.md` D40 status) | **1,020 passed / 0 failed** (re-run: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -o addopts="" -q` → `1020 passed in 26.06s`); the four assertions were fixed by `99fb8fa` | measured run; `git show 99fb8fa` |
| 2 | D36 "Bridge: **3 signals**; `ibkr/client.py`: **3 overrides**" / "3 new signals + 3 overrides" | **2 + 2** (`historical_ticks_bid_ask`, `historical_ticks_last`; `historicalTicksBidAsk`, `historicalTicksLast`) — the third pair was the histogram path deleted under D36 deviation 1 | `ibkr/bridge.py:15–17`; `ibkr/client.py:314–318`; the same section's deviation note |
| 3 | D36 `footprint_cache` blob "`{bar_ts: {level: [bid, ask]}}`" | "`{bar_ts: {level: [bidVol, askVol, tradeVol, tradeCount]}}`" (4 values — the trade-count metric reads the last two) | `data/footprint_cache.py:3–4`; `services/footprint_service.py:177`, `:409` |
| 4 | D24.9 `popouts` DDL "`geometry BLOB`" | "`geometry TEXT`" (JSON) | `data/db.py:76–84`; `data/popout_store.py:27` |
| 5 | Data-Model as-built note "`_init_schema :14–111`; the file is 154 lines; `_migrate_schema :113–121`; `_table_columns :118`" (and the same ref in the risk table) | "`:14–157`; 258 lines; `_migrate_schema :159–179`; `_table_columns :181`" | `data/db.py` (258 lines) |
| 6 | `origin/main` presented as `b366b19` (architecture header + D40 sections; `plan.md` doc-state, D40/verification headers) | `b366b19` is the **D40 merge**; `origin/main` is now **`262ec81`**. Also corrected `:840–846` → `:845–851` (pop-out cap refusal) and `conn_badge :290` → `:295`, both shifted +5 by `99fb8fa`, and the four stale "`(NOT pushed)`" notes (the branches are on `origin/main`) | `git rev-parse origin/main` = `262ec81`; `ui/main_window.py:295`, `:845–851` |

Two editorial additions, no architecture: a **"Line-citation currency"** note in `architecture.md`
(bounding the pre-D24 line numbers in the frozen D16–D23 sections — the cited *symbols* are verified
present; `ui/main_window.py` is now 3,569 lines and `ui/watchlist_panel.py` 994, so e.g. the D23
`remove_symbol` refs `:682–728`/`:716–719` are now `:841–897`/`:884` and
`ibkr/market_data.py:78–84` is now `:108`), and a **Data Model pointer** to the four additive
tables (`popouts`, `footprint_cache`, `yfinance_events_cache`, `volume_baseline`) plus the
D27/D39 column additions, which the pre-D24 "no schema change" framing did not name.

### Verified in this pass (spot list — all confirmed against source)
`MAX_POPOUTS = 10` (`config/settings.py:42`), `SESSION_BAR_CAP = 5000` (`:45`),
`MAX_REALTIME_BARS_PER_10_MIN = 60` (`:30`), `MAX_HISTORICAL_PER_600S = 60` (`:35`),
`LIVE_PORT = 7496` + `check_live_port` (`:11`/`:14–24`), `MAX_ORDER_NOTIONAL = 25000` (`:39`);
`_always_on_top = False` (`ui/popout_window.py:56`) + `_toggle_always_on_top` (`:289`),
`ChartPanel(editable=False)` (`:99`), 500 ms geometry debounce (`:121`);
`DepthHeatmapItem` added unconditionally (`ui/chart_panel.py:368`) + `_depth_enabled_ui = True`
(`:370`); `TickerSession` signal pair (`ui/ticker_session.py:65–73`); pop-out refusal text
(`ui/main_window.py:845–851`); `AlarmStore.symbols_with_active_alarms` (`data/alarm_store.py:27`);
`AlarmMonitor.pause_all`/`resume_all`/`_pause_start` (`services/alarm_monitor.py:52`, `:176`,
`:198`) incl. the reconcile-then-`resume_all` order (`ui/main_window.py:1189–1196`) and staged
`_monitor_subscribe_pending` (`services/alarm_monitor.py:274–283`); `DisconnectClass`
`TRANSIENT`/`TWS_GONE` + `_last_disconnect_class` reset on connect + 2 s/16 s backoff
(`ibkr/client.py:20–59`, `:47–48`, `:192`); 11 new D40 tests (`tests/test_d40_tws_lifecycle.py`);
`conn_badge_text(..., monitoring_paused=)` amber `#fbbf24` (`ui/main_window.py:141–163`);
`CACHEABLE_SYMBOLS` + `is_cacheable` (`data/footprint_cache.py:26`, `:29`);
`BUCKET_COUNT = 60`/`BUCKET_SECONDS = 30` + top-5/top-10 imbalance (`services/depth_heatmap.py:30–31`,
`:98–99`); `MD_LINE_CAP = 100`/`MD_LINE_WARN_AT = 90` (`services/md_line_guard.py:16–17`);
`N_BASELINE_BARS = 30`/`MIN_WARMUP_BARS = 5`/`VOLUME_FLOOR_PER_MIN = 1.0`/`MAD_FLOOR_RATIO = 0.05`/
`DEFAULT_Z_THRESHOLD = 4.0` (`services/volume_baseline.py:58–66`); `evaluate_alarms` kind-filtered
(`services/alarm_service.py:21`) + `evaluate_volume_burst` (`:39`); z-threshold spinbox floor 1.0
(`ui/alarm_dialog.py:106`, `ui/alarm_edit_dialog.py:48`); search debounce 300 ms / 5 s timeout /
16 samples (`services/symbol_search.py:35–39`) and the 180px-capped, zero-minimum search box
(`ui/watchlist_panel.py:349–350`); `TickHistoryManager` 1000-tick windows (`ibkr/tick_history.py:35`)
with zero `reqTickByTickData`; `INDEX_PROXY` + `footprint_cache_key`/`resolve_footprint_contract`
(`ibkr/contracts.py:133`, `:144`, `:160`); S0 union `"225"/"292"/"456"` + `s0_register_many`
(`ui/ticker_session.py:266–269`, `:447`); auction ticks 34/35/36/61 (`:541`) and the 9:25–9:35 /
15:55–16:05 highlight window (`ui/chart_panel.py:917–924`); news overrides ×4 + `news_providers`/
`historical_news`/`historical_news_end`/`news_article` signals (`ibkr/client.py:346–361`,
`ibkr/bridge.py:41–45`); `yfinance==1.7.0` + `ibapi-latest==10.51.1` (`requirements.txt`);
`parse_ib_dividend_string` never raises (`data/events/provider.py:53–82`); yfinance 24 h/6 h/7 d
TTL + ≥1 s gap + `failed_at` (`data/events/yfinance_source.py:33–37`); event-marker icons/colours
(`ui/event_marker_overlay.py:20–22`); `_in_auction_window`; the RouterMode machine (271 lines;
TR-9 refusal at `ui/chart_mouse_router.py:168`; TR-17 `exit_to_idle` at `ui/chart_panel.py:1362`);
the D2 chip lane (`PRICE_TAG_LANE_SAMPLE` `ui/chart_panel.py:238`, `_reserve_price_tag_lane`
`:1024`, lane folded into the zoom offset `:620`, `anchor=(0,0.5)` + `x = right + PRICE_TAG_PAD`
`:1014`/`:1056`); the ESC-013/ESC-020 ordering contract (`vb.setRange` `:1676` before `w_vol`
`:1688`); D11 stacking `max(15.0, height, last_height)` + `right() - 4`
(`ui/drawing_overlay.py:476`, `:481`); `BarCache.prune(keep=RETENTION_BARS=5000)`
(`data/bar_cache.py:8`, `:39`); the ESC-023 New-Year's rule (`services/market_calendar.py:105–120`).

### Salvaged docs (`262ec81`) — reference material, deliberately *not* wired into the architecture
- `docs/ibkr-api-data-inventory.md` (IBKR TWS API inventory, 10.51.01) — **referenced** from
  `architecture.md` in one place: the preamble to the "Pinned-`ibapi` capability facts", where it is
  named as the confidence-tagged research source behind those facts (each of which is independently
  re-verified against the installed wheel, so the architecture does not depend on the inventory).
  It is evidence, not a decision, so it needs no section of its own.
- `docs/phase-changelog.md` — a phase-by-phase narrative. It is **not** wired in as a structural
  reference (no section of its own; the canonical as-built record stays `architecture.md`/`plan.md`),
  but per the owner's standing instruction ("whenever an agent raises a gap or drift it must review
  the changelog") it is now **cited for provenance at four specific points** where it records the
  change in question — the D40 test figure, D36 item 36.2's two-metric footprint shape, D36's
  histogram-removal decision (which explains the 2 + 2 API surface), and the four additive tables.
  See the cross-check record below. (Its own header already points *to* `requirements.md` and
  `architecture.md`.)
- `docs/thinkorswim-feature-gap-analysis.md` — a ThinkOrSwim feature-gap analysis, i.e. **forward
  product scope**. **Not referenced from the architecture**: the architecture must not imply
  unapproved scope. Handed to the Requirements Analyst (see *Requirements-side observations* below),
  not to a planning artifact.
- **`USAGE.txt`** — confirmed the retired instruction is gone: it now reads "do NOT set
  `IBKR_PORT=7497`; for paper trading log into your paper (DU) account and keep the port at 7496",
  consistent with `config/settings.py::check_live_port`. Neither `architecture.md` nor `plan.md`
  asserts a `7497`/paper-port instruction anywhere (grep: `7497` appears only in
  `requirements.md`'s `AC-D26.5` and in build/review logs).

### Requirements-side observations (not edited here — for the Requirements Analyst)
Recorded only; none of these blocks the standing decision, and none is mine to change:
1. `docs/thinkorswim-feature-gap-analysis.md` (salvaged `262ec81`) is unratified product scope —
   it needs an owner decision on whether any of it enters `requirements.md` as a future phase.
2. `requirements.md` `AC-D26.5` cites `IBKR_PORT=7497` only as the fail-fast negative case — correct
   — but the D26 prose should not be read as offering a paper-port mode (it does not).
3. Pre-existing wording imprecisions already tracked in `docs/plan_notes.md` (FI-D22-1's
   "clear() on disconnect" prose) remain open-but-informational; unchanged by this pass.

### Validation steps (short form)
- **Coverage — PASS.** Every D24–D40 work item maps to shipped code; no requirement is weakened or
  reinterpreted; no requirement lost its architectural treatment.
- **Completeness — PASS.** Every component/module/constant named exists and behaves as described;
  the corrections above are record fidelity, not missing architecture.
- **Consistency — PASS.** No internal contradiction remains: `origin/main` is `262ec81`, the suite
  figure is 1,020/0 in both artifacts, and the D37 default-ON / D36 default-OFF pair is stated
  distinctly.
- **Plan quality — PASS (unchanged).** No task-level breakdown or dependency graph is introduced;
  the added material is correction + a verification record.
- **Existing-repo compliance — PASS.** Marker sentence + Current Tech Stack preserved; labels kept;
  Codebase Summary substantive and source-consistent; the `ibapi` pin bump remains the D36-flagged
  38a.0 alignment.
- **Task Manager readiness — no new decision, no action.** Nothing here introduces a decision Task
  Manager must make; every D1–D40 item is already built and merged, and the D23 phases were already
  approved. `docs/plan.md` keeps `Status: READY_FOR_TASK_MANAGER` (unchanged — this pass corrected
  records, it did not invalidate the plan).

### Required Changes
**None.**

### Requirements Escalations
**None** raised from this pass. `docs/plan_notes.md` was **not** modified: nothing here is a
requirements or planning *gap* (the strictly-factual corrections above are the Validator's own
artifacts, and the two requirements-side observations are informational, non-blocking, and recorded
here and in the reply for the Requirements Analyst's parallel audit).

### Final Decision
Status: APPROVED (2026-10-14, second pass — standing D23 approval unchanged; six factual
corrections applied, **no architectural decision changed**; `docs/plan.md` keeps
`Status: READY_FOR_TASK_MANAGER`)

---

## Scoped append — changelog cross-check of the second-pass drifts (2026-10-14, owner's standing instruction)

> **Scope.** A read-only cross-check of `docs/phase-changelog.md` (read in full, 401 lines,
> salvaged by `262ec81`) against the ten drifts corrected in the second pass and the two editorial
> additions. No new Plan→Validator cycle; no architectural decision; the standing `APPROVED`
> decisions are unchanged. The changelog is **not mine** and was **not edited**. Findings already
> recorded as **DG62** in `docs/requirements/design_gaps.md` are **not duplicated** — only the
> architecture/plan-angle additions are recorded here.

### Review Status
Status: APPROVED (standing decisions unchanged; this append records a changelog cross-check)

### Per-drift disposition — explained by the changelog, or changelog-silent
| # | Second-pass correction | Changelog verdict | Entry |
|---|---|---|---|
| 1 | Suite figure 1,016/4 → **1,020/0** | **Corroborated** (not "explained": the changelog never states 1,016/4). It records the green figure for every phase, ending `1020 passing, 0 failing` for D40 | Phase D40 — `:238`; also `:31`/`:68`/`:112`/`:153`/`:366`/`:324`/`:277`/`:194` |
| 2 | `origin/main` was `b366b19` → **`262ec81`** | **Silent** (the changelog says "NOT pushed") — and this is the DG62 class; not duplicated | DG62 |
| 3 | The `+5` line shifts (`ui/main_window.py:845–851`, `conn_badge :295`) | **Silent** — the changelog predates `99fb8fa` and cites no `ui/main_window.py` line numbers for these | — |
| 4 | `popouts.geometry` `BLOB` → **`TEXT`** | **Silent** on the column type; **corroborates** the table's additive existence and SQLite (not QSettings) implementation | Phase 3 — D24.9 at `:119`/`:137` |
| 5 | `footprint_cache` blob `[bid, ask]` → **4 values** | **Recorded** — the changelog states the two-metric shape (per-level trade volume + trade count from the same `TRADES` pages), which the doc had dropped | Phase D36 item 36.2 at `:372` |
| 6 | D36 "3 signals + 3 overrides" → **2 + 2** | **Partially explained AND itself wrong** — the changelog records the histogram removal that invalidates the count, yet its own 36.1 row still says "3 new signals / 3 overrides". See the disagreement below | Phase D36 — `:371` (count) vs `:386` (removal) |
| 7 | D38 bridge list 2-of-4 → **4 signals** | **Same error present** — the changelog's own 38a.1 row names only `historical_news`/`news_article`. See the disagreement below | Phase D38 — `:282` |
| 8 | `data/db.py` line numbers / file length | **Silent** — the changelog cites no `data/db.py` lines | — |
| 9 | Four stale "`(NOT pushed)`" notes in `plan.md` | **Explained — and the changelog is their source.** The changelog's per-phase status lines say "NOT pushed" (D37 `:322`, D38 `:275`, D39 `:192`, D40 `:236`), so `plan.md` inherited it. The status drift itself is DG62; not duplicated | DG62 (+ origin noted) |
| 10 | Editorial: "Line-citation currency" note | **Silent** — no relevant line cites | — |
| 11 | Editorial: Data Model pointer to the four additive tables | **Corroborated** — each table is recorded in its phase entry | Phase 3 D24.9 `:137`; D36 36.4 `:374`; D38 38b.1 `:284`; D39 39.2 `:200` |

### Changelog-vs-tree disagreements **beyond DG62** (architecture/plan angle)
DG62 already covers the stale phase statuses ("NOT pushed"/"NOT merged"), the non-existent D40 fix
SHA `d6f38e8`, and the "depth heatmap default ON is PENDING owner confirmation" wording. Two
**additional** disagreements were found and are **not** in DG62 — both are counting claims that the
architecture and the plan had inherited verbatim, which is why they matter to this artifact set:

1. **D36 signal/override count (`docs/phase-changelog.md:371`):** the changelog's own 36.1 row says
   "Bridge: **3 new signals**; `ibkr/client.py`: **3 overrides**", but the tree has **2 + 2**
   (`ibkr/bridge.py:15–17` — `historical_ticks_bid_ask`, `historical_ticks_last`;
   `ibkr/client.py:314–318` — `historicalTicksBidAsk`, `historicalTicksLast`). The changelog
   *self-contradicts*: its own Phase D36 Decisions entry (`:386`) and review finding A1 record that
   "the planned histogram path was REMOVED from code and docs" and that the "dead histogram plumbing
   [was] deleted", which is precisely the third signal/override pair. So the `:371` count is a
   pre-removal leftover inside a document that elsewhere records the removal.
2. **D38 bridge signal list (`docs/phase-changelog.md:282`):** the changelog's 38a.1 row names only
   "Bridge: `historical_news` / `news_article` signals" (its "`ibkr/client.py`: 4 new overrides" is
   correct), but `ibkr/bridge.py:41–45` defines **four** D38 signals — `news_providers`,
   `historical_news`, `historical_news_end`, `news_article`. The architecture and the plan had the
   same two-of-four list.
3. *(Low severity, also not in DG62)* **Phase 4 is described as the last phase while the same file
   carries four later phase entries:** `docs/phase-changelog.md:151` ("This is the last phase of the
   plan") is a leftover from before D36–D40 were appended to the same document. Not a tree
   disagreement, but a reader following the file top-to-bottom gets a false "the plan is done at
   Phase 4" signal — worth the same refresh DG62 asks for.

**Checked and found consistent** (no disagreement): the changelog's per-phase test figures
(779/819/855/898/927/947/970/1009/1020) match the architecture lineage and the current run;
`MAX_ORDER_NOTIONAL == 25000` regression test (`tests/test_order_validation.py:128`); the
`test_ac_d36_3_production_tree_has_no_mock_endpoint` test (`tests/test_d36_footprint.py:208`); the
OPT/FUT secType mapping (`ui/main_window.py:3480`); `READER_JOIN_TIMEOUT_S = 5.0`
(`ui/main_window.py:3511`); the single `detach_view` (`ui/ticker_session.py:275` — the shadowing
second one is indeed gone); the D37 `"225"`/`"292"`/`"456"` union and its `3 new signals`
(changelog `:329`, correct for D37); `zoom_manager`-independent claims aside, no `7497`/paper-port
instruction appears in the changelog at all. The gate timings (`:119` "1.27ms/tick"; `:164`
"4.45ms/tick") differ from this checkout's run (0.39ms and 1.31ms per tick) — **wall-clock
measurement variance inside the same bounds, not a disagreement** (the deterministic counters,
0 static regens and 990/990 live regens, match exactly).

### Citations changed to reference the changelog
Per the owner's instruction, four claims whose change the changelog records now cite it (the same
pattern the Requirements Analyst used for the `ibapi` pin, "Phase D36 item 38a.0"):
1. `architecture.md` Suite-figure provenance → cites Phase D40's "1020 passing, 0 failing".
2. `architecture.md` D36 Data Model (`footprint_cache` blob) → cites Phase D36 item 36.2.
3. `architecture.md` D36 "Histogram removal" → cites Phase D36 Decisions + review finding A1, and
   explains the 2 + 2 surface.
4. `architecture.md` Data Model additive-tables pointer → cites Phase 3 (D24.9), D36 (36.4),
   D38 (38b.1), D39 (39.2).
`plan.md` mirrors 1–3 (its D36 deviation 1, its D40 status, its follow-up table) and carries a short
**"Changelog cross-check"** paragraph. Where the changelog is itself the source of an error (#6, #7)
the artifacts keep the **tree** as the citation and the changelog is named as the origin instead —
citing a wrong entry as authority would defeat the correction.

### Required Changes
**None.**

### Requirements Escalations
**None.** The changelog is not the Analyst's file and not mine; the two new disagreements are
reported here for the file's owner (see also DG62). `docs/plan_notes.md` remains **unmodified** —
these are documentation-currency findings routed to the changelog's owner, not requirements or
planning gaps.

### Final Decision
Status: APPROVED (2026-10-14, changelog cross-check append — standing decisions unchanged; four
changelog provenance citations added to `architecture.md` and mirrored in `plan.md`'s
"Changelog cross-check" paragraph, two further changelog-vs-tree count disagreements reported for
the changelog's owner, **no architectural decision changed**; `docs/plan.md` keeps
`Status: READY_FOR_TASK_MANAGER`)

---

## Scoped review append — citation convention, `DG56` (2026-10-14)

**Trigger.** A citation-form task on the canonical planning artifacts: adopt and enforce the
**symbol-first citation convention** recommended in `docs/requirements/design_gaps.md` **DG56**
(open, non-blocking), which records that `99fb8fa` inserted 5 lines into `ui/main_window.py`
around ~`:190` and invalidated every later reference by +5 (`ui/main_window.py:840–846` →
`:845–851`, the pop-out cap refusal; `conn_badge` `:290` → `:295`; etc.).

**Not a new Plan proposal.** `docs/plan_proposal.md` / `docs/architecture_proposal.md` are the
D23-era proposals and were **not** re-validated (no new proposal was required or offered); the
approved D23 architecture and its phases are unchanged. This append records an **editorial**
change to the canonical artifacts — permitted because it introduces **no architectural decision**.

**No architectural decision, requirement, phase, assumption or scope item changed.** Every edit
is either (a) a citation's *form* — bare `file:line` → `path::symbol`, with the line retained as
an indicative parenthetical where it helps — or (b) a statement about *which* line numbers are
historical. No constant, behaviour, component, boundary, dependency, acceptance criterion,
phase, assumption or risk claim was altered, and `docs/requirements/*` and
`docs/phase-changelog.md` were not touched.

### Convention text and where it was placed
Stated **once**, prominently, in `docs/architecture.md`: the block
**"Citation convention — symbol-first (adopted 2026-10-14; formalizes `DG56` …)"** at the top of
the provenance area (immediately after the owner-decisions paragraph) — the position the earlier
scoped "Line-citation currency" note occupied, which it replaces. It states:

- **`path::symbol` is the durable form** (e.g. `ui/main_window.py::MainWindow._open_popout`,
  `config/settings.py::MAX_POPOUTS`, `ui/ticker_session.py::TickerSession.bar_updated`) — a
  symbol survives any edit above it and is the contract; and
- **a bare `file:line` is *indicative only*.** Any edit above a cited line can drift it, nothing
  catches it, and where a line is kept it follows the symbol, in parentheses.
- **Historical line numbers are bounded, not renumbered.**

A short mirror (**"Citation convention (mirrors `docs/architecture.md` …)"**) sits in
`docs/plan.md` under the Document-state block, pointing at the architecture section.

### Citations converted — 18 edit sites, 30 line-bearing citations
`architecture.md` (9 sites / 17 citations): header owner-decision block
(`ui/popout_window.py:56` → `::PopoutChartWindow._always_on_top`; `ui/chart_panel.py:368`/`:370` →
`::ChartPanel.depth_heatmap_item` / `::ChartPanel._depth_enabled_ui`); Data Model as-built note and
Architecture Risks row (`data/db.py:14–157`/`:159–179`/`:181` → `::_init_schema` /
`::_migrate_schema` / `::_table_columns`); D24 session signals (`ui/ticker_session.py:65–73` →
`::TickerSession.bar_updated` / `::TickerSession.bars_refreshed`); D24 pop-out cap and the D24
delta row (`config/settings.py:42` → `::MAX_POPOUTS`; `ui/main_window.py:845–851` →
`::MainWindow._open_popout`); the D24 disconnected-pop-out `conn_badge` (`ui/main_window.py:295` →
`::MainWindow.conn_badge`); always-on-top (`ui/popout_window.py:56`/`:289` →
`::PopoutChartWindow._always_on_top` / `::PopoutChartWindow._toggle_always_on_top`);
`config/settings.py:45` → `::SESSION_BAR_CAP`; D37 depth-heatmap default
(`ui/chart_panel.py:368`/`:370` → the two `ChartPanel` symbols).

`plan.md` (9 sites / 13 citations): the Q43 always-on-top line, the D24 as-built feature row, the
D37 deviation 1, the four plan-vs-code verification rows (D24 cap, D24 signals, D24 disconnected,
D37 default), and the two "pop-out refusal" anchors in the second-pass verification list.

Each converted symbol was verified against the current source (`ui/main_window.py`,
`ui/popout_window.py`, `config/settings.py`, `data/db.py`, `ui/ticker_session.py`,
`ui/chart_panel.py`) before it was written — the repository is authoritative.

### Citations bounded as historical — not renumbered
The convention block names both bounded regions explicitly, and the `plan.md` mirror repeats them:

1. **The frozen D16–D23 increment sections** of `architecture.md` — D16 additions/changes,
   D17+D18, D19, D20, D21, D22, D23 — plus the D16/D17/D18/D19 increment paragraphs in the
   header area. These keep their at-that-commit numbers; **36 bare `file:line` citations remain
   in them as written** (e.g. `ui/main_window.py:100–211`, `:102`, `:233`, `:258`, `:323`,
   `ui/watchlist_panel.py:682–728`/`:716–719`, `ibkr/market_data.py:78–84`, `data/db.py:23–27`
   …), together with the symbol-preceded parenthetical refs (e.g. `remove_symbol` (`:682–728`) in
   `plan.md`'s D23 phases). Renumbering a past state would itself mislead.
2. **The "Moved from (as-built)" column** of the D24/D25/D28 session-extraction table
   (§ *The session object*) — its symbol-preceded `(:537)`-style refs cite the **pre-extraction**
   `MainWindow` as it was when D28.2 was planned (today `MainWindow._aggregator` is a property,
   not a `:537` field), not today's file.

The stale examples quoted inside the convention block itself
(`ui/main_window.py:100–211`/`:217–223`/`:223–234`/`:236–242`, `:290`, `:840–846`,
`ui/watchlist_panel.py:682–728`/`:716–719`, `ibkr/market_data.py:78–84`) are intentionally kept
verbatim as the bound's worked examples.

### Requirements Escalations
**None.** `DG56` is an open, non-blocking documentation-hygiene item owned by the docs owners and
is **not** a requirements or planning gap — no `docs/plan_notes.md` entry is warranted, and
`plan_notes.md` is unmodified. The residual stale references DG56 names are in
`docs/requirements/requirements.md` prose (D19/D24/DG53), i.e. the Requirements Analyst's file —
reported there by DG56 itself, not edited here.

### Final Decision
Status: APPROVED (2026-10-14, citation-convention append — the symbol-first convention is stated
once in `architecture.md` and mirrored in `plan.md`; 30 current citations converted to
`path::symbol`; the D16–D23 increment sections and the D24/D25/D28 "Moved from (as-built)" column
are bounded as historical, not renumbered; **no architectural decision, requirement, phase or
scope claim changed**; `docs/plan.md` keeps `Status: READY_FOR_TASK_MANAGER`)

---

# Plan Review — Batch 18 (**D41**) removal proposal — 2026-10-15 (initial validation)

> Legacy single-scope run (no `Phase: P<n>` header in the preamble; inputs are the unsuffixed
> `docs/plan_proposal.md` / `docs/architecture_proposal.md`), so no phase gate applies and this
> review is final for the cycle. Validation method run in full (no provisional pass existed).

## Review Status
`Status: CHANGES_REQUIRED` — round **1** of the 3-retry cap. The three architecture decisions and
the order-path finding all **verify against source**; the phases are well-formed. The proposal is
**not promotable**: both `touches_files` maps are **incomplete** (7 test files, 3 of which fail
deterministically) and two KEEP-listed symbols lose their **only** test coverage, so Task Manager
would have to invent file/test scope and Phase 2/3 acceptance cannot be met as mapped.
`docs/architecture.md` and `docs/plan.md` were **not modified** by this cycle.

## Validation Summary
**Inputs read.** `requirements.md` (`Status: READY_FOR_PLAN`; `### D41` `:3263`–`:3426`;
`AC-D41.1`–`AC-D41.7`; Journey 36 `:855`–`:882`; `A68`–`A71` `:3499`–`:3502`; the surviving
D18 outcomes `:2060`–`:2129`; D21.13 `:2467`–`:2486`; the `AC-D41.6` markers at `:69`, `:83`,
`:2074`, `:2088`, `:3075`, `:3116` — all present, Requirements-owned ✓). `design_gaps.md`
DG66–DG71 `:1012`–`:1153`. `escalations.json`: 16 entries, 14 `open`, **zero** `routed_to: PLAN`
→ the escalation-validation path does not apply. `memory.md` (120 lines) — including the
title-keyed-dock gotcha (`:44`) and the D19 masking trap (`:64`), both load-bearing here.
`docs/plan_proposal.md` (316 lines, `READY_FOR_VALIDATION`, 16:03) and
`docs/architecture_proposal.md` (317 lines, 16:03). The previous `plan_proposal.md` held a stale
Batch-17/D23 draft; it was replaced and **no D22/D23 content survives** in the new proposal ✓
(nothing of it was carried into the canonical files — they were not touched).

**Source verification.** Every load-bearing claim was checked against the working tree
(`ui/main_window.py`, `ui/ticker_session.py`, `ui/chart_panel.py`, `ui/watchlist_panel.py`,
`ui/active_portfolio_panel.py`, `ui/active_trader_panel.py`, `ui/dock_layout.py`,
`ibkr/validation.py`, `data/db.py`, `data/models.py`, `tests/*`). Freshness: proposal (16:03) ≥
requirements (15:25) ✓.

## Requirements Coverage
| Criterion / journey | Plan treatment | Verdict |
|---|---|---|
| `AC-D41.1` (no D36/D37/DOM/Active-Trader/order-entry control or `active_trader` attribute renders) | Phase 1 (footprint/depth controls) + Phase 2 (DOM button, panel, Portfolio-only dock); render/attribute probe in Phase 3 | **Covered** |
| `AC-D41.2` (zero `reqHistoricalTicks`/`reqTickByTickData`/`reqMktDepth`/`cancelMktDepth`/generic `"225"`) | Phase 1 (ticks/heatmap/`"225"`) + Phase 2 (depth/ladder); request probe in Phase 3; removal also enforced at the client edge (S9) | **Covered** |
| `AC-D41.3` (9 modules + 3 suites gone, no dangling import/reference) | Deletions in Phases 1–2; `find_spec` + token scan in Phase 3 | **Covered**, but the guard's token set is incomplete → **R3** |
| `AC-D41.4` (D38/D39/D27–D28 substrate intact **and** retained order machinery + resolving `ref_price`) | Phase 1 preserves the substrate; Phase 2 re-homes the gates (S5, S4); Phase 3 evidence | **Partially covered** — two KEEP symbols lose their only tests → **R2**; the kill-switch/bracket half rests on an unmapped suite → **R1** |
| `AC-D41.5` (app starts and charts; full offscreen suite green) | Phase 3 (+ Phases 1–2 as prerequisites) | **Cannot be met as mapped** — 3 unlisted suites fail deterministically → **R1** |
| `AC-D41.6` (`SUPERSEDED BY D41` markers; D18/D21.13 notes; tech-stack sentence intact) | Requirements-owned, already applied; no code work (AP-5) | **Covered** (verified present at the six lines above) |
| `AC-D41.7` (right dock Portfolio-only, visible in full screen, non-zero width, clamped; cap/header re-derived) | S6 + Phase 2 implementation + Phase 3 `test_d41_portfolio_dock.py` | **Covered**, subject to **R1** (dock-title consumers) |
| Journey 36 (6 steps + edge cases) | Steps spread across Phases 1–3 | **Covered** (the per-phase step attribution is inconsistent but all six are addressed) |
| KEEP-list protections (D38 news/dividends, D39 bursts/search, D27/D28, the chart, the retained order machinery, `footprint_cache_key`/`INDEX_PROXY`/`md_line_guard.assess`/`S0_TICKS`/`volume_baseline`) | Phases 1–2 preservation + Phase 3 evidence | **Hold**, except the two coverage losses → **R2** |
| DG66/DG69/DG70/DG71 (escalations moot; panel scope; table drop; `ref_price` + cap/header re-derivation) | S7/S8/S9/S10, AP-7 | **Covered** — DG71(1) by S4, DG71(2) by S6, DG69 by S3/S5, DG70 by S7 |

## Architecture Findings
**(a) `ref_price` re-sourced to `_symbol_last_prices` — VERIFIED.** `ui/main_window.py:727` is the
D27.5 map; `:2263`–`:2266` `_record_symbol_price` normalises to upper case; `:609` wires the
watchlist sink; `ui/watchlist_panel.py:919`–`:937` feeds it from each row's `reqMktData`
subscription (`ui/watchlist_panel.py:241`); `ui/ticker_session.py:862`–`:863` feeds it from **every
aggregated chart bar**; `:3313` is the existing D27.5 consumer. `_ref_price_for` does not exist yet
(new) and its upper-case normalisation matches the map's keys ✓. `None` for an unknown symbol is
safe (`ibkr/validation.py:62`–`:72` skips the notional check with no positive price basis) and S4
states exactly that. **One rationale overstatement to soften:** the map resolves for a symbol that
is on the **watchlist** or has a **live session**; a position in neither returns `None`, so the
phrase "resolves for a position whose symbol has no live chart session — the exact case a
multi-symbol portfolio close hits" is stronger than the code supports. The decision itself is
unchanged and is one of the two sources A71/DG71 bless.

**(b) Portfolio-only dock — VERIFIED, including "by construction".** As-built:
`ui/main_window.py:485`–`:493` (one `QDockWidget`, title **and** `objectName` `"Active Trader"`,
`setTitleBarWidget(self.active_trader.header_bar)`); `:471`–`:483` (`RightDockContainer` with both
panels stacked); `:2455`–`:2475` (collapsed floor over **both** buttons); `:2477`–`:2485`
(`_right_region_is_collapsed` = AND of both); `:2494`+ (per-panel stretch juggling).
`ui/active_portfolio_panel.py:80`–`:97` — `summary_label` is a checkable `DiagonalStrikeButton`
wired `toggled → _on_header_toggled → body.setVisible`, with `is_collapsed()` at `:179` — the
**identical** shape to `ActiveTraderPanel.header_bar` (`ui/active_trader_panel.py:491`–`:518`,
which the dock already re-parents today). So S6's "`ui/active_portfolio_panel.py` — not modified"
holds ✓. `ui/dock_layout.py` is pure Qt-free (`:8`–`:10`), `RIGHT_DOCK_CAP_FRACTION = 0.40`
(`:36`), `RIGHT_DOCK_MIN_WIDTH = 200` (`:30`), `right_dock_max_width`/`plan_dock_widths`
(`:58`–`:113`) — unchanged, as S6 claims ✓. The surviving D18 outcomes hold by construction:
AC-D18.1 visibility (`requirements.md:2073`–`:2080`), AC-D18.2's **0.40** cap (`:2081`–`:2087` —
the numeric cap survives *in the AC itself*, so keeping it is not a weakening), AC-D18.4
(`:2095`), AC-D18.5 (`:2099`), AC-D18.6 (`:2105`), AC-D18.7 no persistence (`:2111`); AC-D21.13.4's
strike-through survives on the retained Portfolio toggle (`:2478`). **But the consumer list is
wrong** (`architecture_proposal.md:109` says "8 files" and lists 9; there are **14** title/objectName
consumers) → **R1**.

**(c) `footprint_cache` drop — VERIFIED.** `data/db.py:6`–`:12` `DB.__init__` → `_init_schema()`;
`:155`–`:156` the DDL script then `_migrate_schema()`; `:159`–`:179` `_migrate_schema()` **is** this
repo's migration mechanism — it runs unconditionally on every open and is already additive and
idempotent (`ALTER TABLE` guards, `CREATE UNIQUE INDEX IF NOT EXISTS`). A `DROP TABLE IF EXISTS
footprint_cache` there is a one-time, crash-safe, operator-free step ✓ (S7 correct; DG70's
recorded default = full drop ✓). The DDL to remove is `:118`–`:127` ✓. `tests/test_db_schema.py:13`
/`:47`–`:49` **subset-asserts** `EXPECTED_TABLES`, so removing the DDL is silent — the Phase-3
absence/drop assertion the proposal adds is genuinely required ✓.

**(d) The order-path finding (FI-1's load-bearing claim) — VERIFIED EXACTLY (source-verified
independently).**
- `validate_order(` has **exactly one** production call site: `ui/main_window.py:3112` (all other
  matches are in `tests/test_order_validation.py`).
- `_place_order`'s production callers: `_on_order_place_requested` (`:3097`) and its own
  `QTimer.singleShot` retry (`:3135`); `_on_order_place_requested` is wired **only** to
  `active_trader.order_place_requested` (`:693`) ⇒ ticket-only ✓.
- `_close_position_by_id` (`:3446`–`:3508`) builds the offsetting MKT order and calls
  `self.ib_client.placeOrder(order_id, contract, order)` at `:3505` with **no** `validate_order`
  and **no** connection guard ✓.
- The only order-transmit guard is `:3105` (`if not self._ibkr_connected`) inside `_place_order` ✓.
- `placeOrder(` sites: six inside `_place_order` (`:3146`, `:3157`, `:3169`, `:3185`–`:3187`) + one
  at `:3505` ⇒ after D41 the close/flatten path is the app's **sole** emitter ✓.
- `bracket_order`'s only production caller is `:3182` (inside `_place_order`) ✓ — retained and
  exercised by `tests/test_order_builders.py`.
⇒ **The claim is right and Phase 2's re-homing target is right.** `validate_order`/`_ref_price`
would otherwise become production-dead; S5's `risk_reducing` carve-out (skip only the notional
cap) is additive and default-off, so no existing caller's behaviour changes.

**(e) Run mode / promotion shape.** The proposal is a **legacy single-scope** proposal: no
`Phase: P<n>` header, decisions labelled `[existing]`/`[new]`/`[new/changed]` — the phased template
check does not apply, and there is no `docs/plan_review_P<n>.md` in play. When it is eventually
approved, promotion must **append** a `## D41 increment` to the cumulative `docs/architecture.md`
(after the D40 increment at `:3268`) and a D41 section to `docs/plan.md` (which today is explicitly
`Scope: D23 only` + as-built D24–D40). A literal `cp` over either file would destroy the D1–D40
as-built record.

**(f) Internal cross-reference and factual defects that must not reach the canonical files
(editorial, no new decision).**
- `architecture_proposal.md:93` cites **`S19`** — no such decision exists; it means **`S5`**
  (corroborated by the same paragraph's AR-D41-6 and by `plan_proposal.md:104`).
- `:109` "**8** test files" then lists **9**, while the tree has **14** title/`objectName`
  consumers (`test_dock_widths_d17.py:37`+`:73`; `test_watchlist_d14_midrag.py:35`+`:82`;
  `test_crosshair_axis_lane.py:101`–`:106`; `test_d27_position_prices.py:30`;
  `test_history_backfill.py:199`; `test_history_backfill_disconnect.py:136`;
  `test_watchlist_columns_d21.py:308`+`:322`; `test_d10_d13_integration.py:35`+`:53`;
  `test_d27_stream_health.py:67`; `test_d27_account_subs.py:27`; `test_d27_phantom_alarms.py:56`;
  `test_dock_d18_region.py:107`+`:110`; `test_d27_reconnect.py:163`;
  `test_history_backfill_loadpath.py:165`) + 2 title-bar-text assertions
  (`test_right_dock_d21.py:64`, `test_watchlist_nonregression_d22.py:142`).
- `architecture_proposal.md:180` and `:206` attribute `OrderBookLevel` to **FI-1** — it is
  **FI-2**; `:284` (AR-D41-9) attributes the wide-candle issue to **FI-2** — it is **FI-3**.
- `:284` calls ESC-041 "should-fix"; `docs/code_review/escalations.json` records ESC-041 as
  **blocking**, routed BUILD (corroborated by `docs/orchestrator_state.json.blocking_bugs`).
- `plan_proposal.md:29` "**14** escalations stay open and untouched" contradicts AP-7: ESC-035 /
  ESC-039 / ESC-040 are mooted by removal (DG66), leaving **11** open and untouched
  (ESC-032/033/034/036/037/038/041/042/043/044/045; ESC-038 is open/routed REQUIREMENTS and is
  D41-neutral).
- `ui/dock_layout.py` is listed in Phase 1 as an optional comment edit, but its only
  "Active-Trader" references (`:4`, `:29`) belong to the **Phase 2** rename.
- The descriptive file counts ("Phase 1 (16 file entries)", "Phase 2 (21)") do not match the maps
  (≈22 and ≈31 enumerated files).
- Every line range in the maps is a bare `file:line`, while the repo adopted the `path::symbol`
  citation convention (DG56; `docs/plan.md` header) — pair each range with its symbol when the
  canonical artifacts are written.

**(g) Load-bearing anchors spot-checked** (within 1–2 lines of the cited ranges):
`ui/chart_panel.py:355`–`:358` (`footprint_static`/`footprint_live`), `:370`/`:758`/`:775`
(`_depth_enabled_ui`), `:560`–`:563` (`_depth_refresh_timer` 500 ms), `:699` (`refresh_footprint`),
`:827` (`bind_d37_session`), `:852` (`bind_d38_session` — kept); `ui/main_window.py:99`
(`DEPTH_FEED_CAP`), `:351`–`:355`, `:557`–`:558`, `:654`–`:655`, `:790` (`_md_line_count`), `:817`
(`_guard_depth_budget`), `:965`/`:988`/`:1004`; `ibkr/subscription_manager.py:37`–`:38` (`DEPTH`,
`DEPTH_HEATMAP`); `data/models.py:105`–`:110` (`OrderBookLevel`, **zero** references — verified).

## Plan Findings
- **Phase structure ✓.** Three phases, strictly ordered, each with a goal, the requirements/journeys
  it covers and its dependencies; one task per file; `ui/main_window.py` a single task per phase;
  no two entries of a phase share a file (intra-phase `touches_files` sets are disjoint), and the
  only cross-phase file overlap is the six shared production files, which AP-1's strict sequencing
  covers.
- **Granularity ✓.** Each phase is a meaningful body of work ("remove the D36/D37 feature trees",
  "remove the Active Trader panel and make the dock Portfolio-only", "non-regression verification"),
  not a task list: no acceptance criteria per task, no test specifications per task, no task graph.
  The per-file line-range tables are sequencing/partition support (this repo's established
  convention) and are acceptable at that level.
- **Map completeness ✗** — the decisive finding. Seven test files reference symbols or titles D41
  removes and appear in **neither** map; three of them fail deterministically
  (`tests/test_d28_pacing.py:130`, `tests/test_kill_switch.py:90` → `AttributeError` on the deleted
  `_place_order`; `tests/test_crosshair_axis_lane.py:105` → `KeyError` on the renamed dock). The
  other four silently stop hiding the right dock (the D19/D21 masking trap that `memory.md:44`/`:64`
  records and that AR-D41-3 claims to neutralise). See **R1**.
- **Coverage carried by the deletions ✗** — `footprint_cache_key` and `md_line_guard.assess` each
  have exactly one test, both inside suites this plan deletes. See **R2**.
- **Verification design ✓** (phases 1–2 per-phase evidence, phase 3 the three new suites + full
  offscreen run; AP-3's invocation is right, and `tests/conftest.py:13` does export `DB_PATH`).
  The guard's credibility rests on a complete file map, which is why R1/R3 matter.
- **Assumptions AP-1–AP-9** are plan-level, not requirements gaps, and are consistent with
  `A68`–`A71`/DG66–DG71 ✓ (AP-4/A36 no-new-QSettings-key is asserted by the new dock suite ✓).

## Existing Repo Compliance
Run is an existing repository (`requirements.md` carries the marker sentence). Per check:
- **Codebase Summary present and substantive — PASS.** Field-level data-model inventory, a
  components table with responsibilities and sizes, key entry points with signal/wiring paths, the
  integration surface with the pinned `ibapi`/live-7496 constraint, and ten numbered
  source-validated facts. Not a placeholder.
- **Existing stack respected — PASS.** S1/S2/S12 list the constrained choices first (Python 3.11+
  `.venv`, PyQt6 ≥6.6, pyqtgraph ≥0.13, `ibapi` `9.81.1.post1`, live port 7496 fail-fast, numpy,
  SQLite via `config/paths.get_db_path()`, PyInstaller, pytest + pytest-qt offscreen). Nothing
  existing is replaced or deprecated and no new dependency/integration is added
  (`Integration Points` = "New integrations: none") ✓.
- **Labels present — PASS.** Tech Stack: `[existing]` S1/S2/S12, `[new]` S3/S4, `[new/changed]`
  S5–S11. System Components: `[existing → deleted]`, `[existing]`, `[new/changed]` on every row.
  Data Model and Integration Points label every entry (`[existing]`, `[existing → removed]`,
  `[new/changed]`).
- **Additive-only — PASS.** No existing component is redesigned beyond a requirement: the single
  behaviour addition (S5's additive `risk_reducing` keyword + re-homed gates on the retained close
  path) is required by `AC-D41.4`/`A71`/DG71; `ui/active_portfolio_panel.py` is deliberately
  untouched; `footprint_cache_key` is deliberately **not** renamed (S10, FS17).
- **Codebase Summary consistent with the proposal — PASS.** Every `[existing]` item exists as
  described (`RightDockContainer` + two-section dock, `_symbol_last_prices` `:727`,
  `DEPTH`/`DEPTH_HEATMAP`, `MarketDepthManager`, `OrderBook`/`Level`, `OrderBookLevel`,
  `FootprintCache`, the `footprint_cache` DDL) and every `[existing → removed]` item was verified
  in source; the five KEEP-list survivors were verified present
  (`ibkr/contracts.py:144` `footprint_cache_key`, `INDEX_PROXY`; `services/md_line_guard.py:13`
  `assess`; `S0_TICKS`; `volume_baseline`).
- **Requirements-side marker:** `Current Tech Stack` is present and placeholder-free — no
  requirements escalation on that count.

## Required Changes
**R1 — complete both `touches_files` maps (blocking).** Add these seven test files, with the edit
each needs, to the phase shown:
1. `tests/test_d28_pacing.py` → **Phase 2**: `test_place_order_defers_when_limiter_empty`
   (`:117`–`:140`) calls the deleted `win._place_order(...)` (`:130`). Re-point it at the retained
   emitter (`_close_position_by_id` with a seeded `positions` row) so the D28.1 order-path
   deferral guarantee stays exercised.
2. `tests/test_kill_switch.py` → **Phase 2**: `test_bracket_place_registers_all_three_legs`
   (`:77`–`:100`) calls `win._place_order(order_type="BRACKET", …)` (`:90`) — this is D26.8's
   **only** test that all three bracket legs are registered at transmit time (`AC-D41.4`'s
   "retained machinery … exercised"). Re-point it to build the legs via
   `order_registry.bracket_order` + `order_registry.register` (or via the retained path) rather
   than deleting the assertion.
3. `tests/test_crosshair_axis_lane.py` → **Phase 2**: `docks = {d.windowTitle(): d …}` then
   `region = docks["Active Trader"]` (`:101`–`:105`) raises `KeyError` after the rename, and
   `assert "Portfolio" not in docks` (`:106`) **inverts**. Re-point to the single `"Portfolio"`
   dock and invert that assertion.
4. `tests/test_watchlist_d14_midrag.py` (`:35` `_RIGHT_DOCKS = ("Active Trader",)`, used `:82`)
   → **Phase 2**: dock-hide helper must hide the renamed dock or the D14 gesture harness runs
   against a different chart width.
5. `tests/test_d27_position_prices.py` (`:29`–`:31`) → **Phase 2**: same hide-helper.
6. `tests/test_history_backfill.py` (`:199`) → **Phase 2**: same hide-helper.
7. `tests/test_history_backfill_disconnect.py` (`:136`) → **Phase 2**: same hide-helper.

Also correct the stated consumer count ("8 test files" / "9 test files" → the verified **14**
title/`objectName` consumers + the 2 title-bar-text assertions) and enumerate them, so the
AR-D41-3 mitigation ("a stale tuple is then detectable, not silent") is actually true.

**R2 — re-home the coverage the deletions take with them (blocking; `AC-D41.4`).**
- `ibkr/contracts.py::footprint_cache_key` — its **only** test is
  `tests/test_d36_footprint.py::test_rollover_key_change_isolates_tape` (`:389`–`:395`); no other
  test in the tree names the symbol.
- `services/md_line_guard.py::assess` — its **only** test is
  `tests/test_d37_microstructure.py::test_md_line_guard_thresholds` (`:336`–`:342`); no other test
  imports `assess`.
`AC-D41.4` requires both to "remain **and remain exercised by their tests**". Move these assertions
into a surviving suite (e.g. the D39 burst/`volume_baseline` suite for the roll-over key rule, and a
retained-substrate assertion for the guard thresholds), or assert them inside
`tests/test_d41_removal.py`, and record that in the map and in the `AC-D41.4` traceability row.

**R3 — widen the Phase-3 removal guard's token set (blocking for its own claim).** AR-D41-3 /
AR-D41-8 promise that every reference is enumerated and that a stale one is detectable, but
`tests/test_d41_removal.py`'s scan omits identifiers Phase 2 deletes that **are referenced today**
outside it: `_place_order` (`ibkr/validation.py:5`; `tests/test_d28_pacing.py:130`;
`tests/test_kill_switch.py:90`), `_on_order_place_requested`, `_on_dom_toggled`, `_on_mkt_depth`,
`_rebind_depth_req_id`, `_on_fp_*`/`_fp_host_managers`, `active_feed_count`, `has_subscription`,
`apply_operation`, `is_cacheable`, `LadderTable`, `BookTable`, `right_dock_container`,
`_right_dock_layout`, and the literal removed dock title `"Active Trader"` in `tests/` (with an
allow-list for the new negative assertions in `tests/test_d41_portfolio_dock.py`).

**R4 — correct the FI-1/FI-3 evidence and severity (low).** FI-1's SL/TP claim should be evidenced
by `ui/stop_loss_target_dialog.py` containing **no** `placeOrder` (verified repo-wide) —
`tests/test_sltp_honesty.py:16`/`:24` asserts the dialog's **label text**, not non-transmission.
FI-3 should cite `docs/code_review/candle_overlap_investigation.md` (concluded; rules the footprint
overlay **out**; cause is `ui/candlestick_item.py:122`–`:138` + `ui/chart_panel.py:1688`–`:1690`)
and record ESC-041's true severity (**blocking**, per `escalations.json`).

**R5 — fold in the internal cross-reference corrections (low).** All of Architecture Findings (f) —
none of it may reach the canonical artifacts, and the `S19` → `S5` reference must be fixed or the
canonical architecture would name a decision that does not exist.

**R6 — re-point the `validate_order` module docstring (low).** `ibkr/validation.py:5` says the gate
is "Wired at the top of `MainWindow._place_order`"; after Phase 2 that symbol is gone — the docstring
must name the retained emitter (S5 already says the docstring is updated; make it explicit that this
sentence is included).

## Requirements Escalations
**One recorded, not escalated** — `docs/plan_notes.md` **RG-D41-1** (`Status: open`,
`Escalation: none`): `AC-D41.4`'s "the retained order paths … still build and **validate** orders
with a resolving `ref_price`" carries the two readings FI-1 identifies, and its "SL/TP dialogs"
clause is **vacuous** — `ui/stop_loss_target_dialog.py` transmits no orders at all (verified
repo-wide; `tests/test_sltp_honesty.py` asserts only the disclosure label).
**Ruling (this cycle): ratify the proposal's reading (a)** — re-homing the D26.9 disconnected guard
and the `validate_order()` gate onto `_close_position_by_id`, fed by `_ref_price_for` and with the
additive `risk_reducing` keyword, is what `AC-D41.4` and the KEEP list ask for ("must keep
resolving for the retained order paths"), and `DG71`/`A71` bless both the source and the mechanism.
It is **not** scope addition and **not** an invention, so **no `ESCALATED_TO_REQUIREMENTS`** and no
Requirements Analyst action is required.

## Task Manager Readiness
**Not ready — do not start Task Manager.** Two independent blockers:
1. The `touches_files` maps are incomplete (R1/R2/R3), so Task Manager would have to decide which
   further files and tests to edit — a scope decision that is not its own.
2. With the maps as written, Phase 2's acceptance ("the re-pointed dock/toolbar/order suites green")
   and Phase 3's (`AC-D41.5` full suite green) are unreachable: `tests/test_d28_pacing.py`,
   `tests/test_kill_switch.py` and `tests/test_crosshair_axis_lane.py` fail deterministically, and
   four more suites would be silently masked.

Everything else is decision-complete: the three architecture decisions are explicit, reasoned and
source-verified; the D18/AC-D18.3/D21.13/D26 outcomes are preserved or explicitly re-derived; and
no requirement clause is left without architectural treatment.

**Artifact state.** `docs/architecture.md` and `docs/plan.md` were **not modified** this cycle —
`docs/plan.md` carries no D41 content, its `Status: READY_FOR_TASK_MANAGER` line belongs to the
already-built D23 increment whose handoff block scopes itself to "the three phases above", and the
authoritative gate for this cycle is this review. No `READY_FOR_TASK_MANAGER` marker anywhere
represents D41, so none had to be removed to prevent an unsafe handoff. `docs/plan.md` must **not**
gain one until R1–R3 are addressed and the proposal is re-validated.

## Final Decision
Status: CHANGES_REQUIRED (2026-10-15, D41 initial validation — round 1 of 3. The three substantive
architecture decisions (S4 `ref_price` source, S6 Portfolio-only dock, S7 `footprint_cache` drop)
and FI-1's order-path finding all **verify against source**; the phases are well-formed and
correctly scoped. The proposal is blocked by an **incomplete test/file map** (7 files, 3 of them
deterministically failing) and by **two KEEP-listed symbols losing their only test coverage**,
which would force Task Manager to invent file/test scope. Fix R1–R3 (R4–R6 alongside), re-issue
`docs/plan_proposal.md` / `docs/architecture_proposal.md`, and re-run validation.)

---

# Plan Review — Batch 18 (**D41**) removal proposal — 2026-10-15 (round 2: R1–R6 verification, **APPROVED**)

> Legacy single-scope run (no `Phase: P<n>` header in the preamble; inputs are the unsuffixed
> `docs/plan_proposal.md` / `docs/architecture_proposal.md`), so no phase gate applies and this
> review is final for the cycle. Round **2** of the 3-retry cap: the proposal was re-issued in place
> (`docs/plan_proposal.md`, `docs/architecture_proposal.md`, both `Status: READY_FOR_VALIDATION`,
> 16:21) and re-marked for validation.

## Review Status
`Status: APPROVED` — R1, R2 and R3 (the three blockers) are **fixed and independently verified
against the tree**, and R4–R6 are folded in. No new defect was introduced by the revision: the
previously-verified architecture decisions (`S4`, `S6`, `S7`) and the order-path finding are
unchanged and re-verified. The canonical artifacts were written from this cycle.

## Validation Summary

**Inputs read.** `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`, last line `:3717`;
`### D41` `:3263`, `AC-D41.1`–`AC-D41.7`; the `SUPERSEDED BY D41` markers at `:69`, `:83`, `:2088`,
`:3075`, `:3116` ✓). `docs/requirements/design_gaps.md` (DG66–DG71). `docs/code_review/
escalations.json` — **16 entries, 14 `open`, zero `routed_to: PLAN`** ⇒ the escalation-validation
path does not apply, and no PLAN escalation was addressed during the round-1 gap. `docs/plan_proposal.md`
(443 lines) and `docs/architecture_proposal.md` (352 lines), both `Status: READY_FOR_VALIDATION`,
both **newer than `requirements.md`** (16:21 ≥ 15:25 — freshness ✓). `docs/plan.md`,
`docs/plan_notes.md` (RG-D41-1) and this file's own round-1 review were read as the retry context.

**Source verification (all independent, this cycle).** Every R1–R3 claim was re-checked against the
working tree with `grep`/`read` — not accepted from the proposal. Files touched by the checks:
`tests/*` (the 17 dock consumers, the seven formerly-unmapped suites, the two re-home targets, the
toolbar/order/dock suites), `ui/main_window.py`, `ui/chart_panel.py`, `ui/ticker_session.py`,
`ui/watchlist_panel.py`, `ui/validation…`→`ibkr/validation.py`, `ibkr/{market_depth,order_book,
subscription_manager,contracts,orders}.py`, `data/{db,models}.py`, `services/md_line_guard.py`, and
`docs/code_review/escalations.json`.

## Required Changes — verdicts

| # | Required change | Verdict | Evidence checked |
|---|---|---|---|
| **R1.1** | `tests/test_d28_pacing.py` called the deleted `_place_order` | **FIXED** | `tests/test_d28_pacing.py:130` is `win._place_order(contract=object(), symbol="AAPL", …)` inside `test_place_order_defers_when_limiter_empty` (`:117`–`:140`) ✓. The Phase-2 row re-points it at `win._close_position_by_id(<seeded id>)` with a seeded `positions` row and keeps all **four** D28.1 guarantees, which the test does assert: no immediate transmit (`:134`), no GUI-thread sleep (`:135`), the `pacing-limited` status (`:136`), exactly one deferred transmit after `QTest.qWait(1200)` at `:137` (`:138`) ✓ |
| **R1.2** | `tests/test_kill_switch.py:90` called the deleted `_place_order` — D26.8's only all-three-legs test | **FIXED** | `tests/test_kill_switch.py:90` is `win._place_order(… order_type="BRACKET" …)` ✓; the assertions at `:93`–`:98` (ids `[1,2,3]`, parent `BUY`, both children `SELL`) and the `IdManager` patch at `:87`–`:89` are as described ✓. **"Only all-three-legs-at-transmit test" confirmed independently**: `bracket_order`'s consumers are `ui/main_window.py:3182` (inside the deleted `_place_order`) and `tests/test_order_builders.py` (builder-level structure/transmit-flag tests), neither of which drives a place and asserts transmit-time registration of all three legs. The re-point at `order_registry.bracket_order` + `register` keeps the property ✓ |
| **R1.3** | `tests/test_crosshair_axis_lane.py:105`/`:106` | **FIXED** | `:105 region = docks["Active Trader"]`, `:106 assert "Portfolio" not in docks`, with the D18 comment at `:102`–`:104` and the f-string at `:123` — exactly as the plan states ✓. The proposed replacement (positive `"Portfolio" in docks` **and** `"Active Trader" not in docks`) preserves the original intent ✓ |
| **R1.4–R1.7** | Four silently-masked dock-hide helpers | **FIXED** | `tests/test_watchlist_d14_midrag.py:35` (`_RIGHT_DOCKS = ("Active Trader",)`, used `:82`) ✓; `tests/test_d27_position_prices.py:30` ✓; `tests/test_history_backfill.py:199` ✓; `tests/test_history_backfill_disconnect.py:136` ✓ — all four now have a Phase-2 row → `("Portfolio",)` |
| **R1 (count)** | "8/9" consumers → the verified number | **FIXED — verified independently at 15 + 2 = 17** | See the dedicated count verification below |
| **R2** | `footprint_cache_key` and `md_line_guard.assess` lose their only tests | **FIXED** | `footprint_cache_key`: its only test is `tests/test_d36_footprint.py::test_rollover_key_change_isolates_tape` (`:389` def; calls `:394`–`:395`; assertions `:396`–`:398`) — no other test in the tree names the symbol ✓. `services/md_line_guard.py::assess`: its only test is `tests/test_d37_microstructure.py::test_md_line_guard_thresholds` (`:336`–`:344`) ✓. Both **re-homes land in Phase 1**, the phase that deletes the two suites ✓ (`tests/test_d39_burst_search.py`, `tests/test_d38_events_news.py` both exist and are Phase-1 rows). The re-home targets are the right homes: `ui/ticker_session.py:922` is inside `_evaluate_burst_alarms` (D39.3, surviving — the section boundary `# ── Footprint (D36) ──` is at `:955`, so `:922` is genuinely a D39 use) ✓; the D38 suite is what `_guard_md_lines` still gates ✓. The re-purposed guard assertions match the surviving suite's content — `assess(50) == ("ok","")`, `assess(90)` → `"approaching"` with `"SPX"`/`"90/100"`, `assess(100)` → `"exceeded"` with `"not subscribing"` (the existing assertions at `:337`–`:344`), only the purpose label changes from `"depth"` to `"S0 ticks"`, which is faithful (the label is not asserted) ✓ |
| **R3** | Widen the Phase-3 removal guard's token scan | **FIXED** | Every token in the widened set **fires pre-D41** (counted repo-wide over `ui ibkr services data config tests main.py`): `active_feed_count` 3, `apply_operation` 11, `is_cacheable` 13, `LadderTable` 3, `BookTable` 2, `OrderEntryWidget` 6, `_rebind_depth_req_id` 4, `_on_dom_toggled` 11, `_on_mkt_depth` 2, `_on_order_place_requested` 4, `_place_order` 15, `_fp_host_managers` 6, `resolve_footprint_contract` 11, `historical_ticks_` 6, `update_mkt_depth` 4, `DEPTH_HEATMAP` 5, `reqMktDepth` 16, `reqHistoricalTicks` 7, `reqTickByTickData` 4, `RightDockContainer` 1, `right_dock_container` 7, `_right_dock_layout` 2, `dom_btn` 10, `set_depth_manager` 2, `_depth_manager` 7, `bind_d37_session` 4, `update_auction_chip` 5, `DEPTH_FEED_CAP` 4, `OrderBookLevel` 1 (its own definition — the inert claim holds), `active_trader` 63 ⇒ the "red before the change" proof is achievable for the whole set ✓. **`has_subscription` scoping is correct**: bare occurrences today are `ibkr/market_depth.py:45` (deleted with the module) and `ibkr/subscription_manager.py:81` (retained) plus `tests/test_market_depth.py:164`/`:168`–`:170` (deleted with that suite) ⇒ after D41 the **only** surviving bare occurrence is `ibkr/subscription_manager.py:81`, exactly as the allow-list documents ✓; the module-absence check covers `MarketDepthManager.has_subscription` since the whole module goes ✓. `"Active Trader"` allow-listing is consistent (negative assertions only in the two guard files) ✓ |
| **R4** | FI-1/FI-3 evidence + ESC-041 severity | **FIXED** | FI-1 now cites `ui/stop_loss_target_dialog.py` (no `placeOrder` — re-confirmed repo-wide) and `tests/test_sltp_honesty.py`'s label-only assertion ✓. FI-3 cites `docs/code_review/candle_overlap_investigation.md` + `ui/candlestick_item.py:122`–`:138` / `ui/chart_panel.py:1688`–`:1690` ✓. ESC-041 recorded **`blocking`** ✓ — independently confirmed in `escalations.json`: ESC-041 = `blocking`/BUILD/`open` (the only blocking entry besides ESC-032/033) |
| **R5** | Internal cross-reference corrections | **FIXED** | `S19` appears **nowhere** in either proposal except the R5 changelog row itself; the decision reference is `S5` ✓. `OrderBookLevel` → **FI-2** in Components (`:200`) and Data Model (`:233`) ✓; AR-D41-9 → **FI-3** (`:311`) ✓; ESC-041 `blocking` ✓. Escalations count corrected: header `:34` and AP-7 both say **11** stay open (14 open − ESC-035/039/040 moot) and list `ESC-032/033/034/036/037/038/041/042/043/044/045` — 11 IDs ✓ (verified against `escalations.json`: 14 `open`, and ESC-035/039/040 are all `should-fix`). File counts **20** (Phase 1) / **39** (Phase 2) — **recounted independently row by row: 20 ✓ and 37 rows / 39 entries ✓**. `ui/dock_layout.py` now a **Phase-2** row ✓. Line ranges are paired with their symbols (`path::symbol`) per the citation convention ✓. The `S4` rationale is softened to the accurate "resolves for a symbol that is on the watchlist **or** has a live chart session" ✓ |
| **R6** | `ibkr/validation.py:5`'s `_place_order` docstring reference | **FIXED** | `ibkr/validation.py:5` says "Wired at the top of ``MainWindow._place_order``" ✓ (as cited), and the Phase-2 `ibkr/validation.py` row + `S5`'s decision text both re-point it at `MainWindow._close_position_by_id` ✓ |

## Independent consumer-count verification (R1's count claim)

**The claim "15 `windowTitle()`/`objectName()` consumers + 2 title-bar-text files = 17" is CORRECT —
verified from the tree, not accepted.** Sweeping every `*.py` under `tests/` for title/`objectName`
keys on the right dock yields exactly these 15 files:

`tests/test_dock_widths_d17.py` (`:37`+`:73`), `tests/test_watchlist_d14_midrag.py` (`:35`+`:82`),
`tests/test_crosshair_axis_lane.py` (`:101`–`:106`, `:123`), `tests/test_d27_position_prices.py:30`,
`tests/test_history_backfill.py:199`, `tests/test_history_backfill_disconnect.py:136`,
`tests/test_dock_widths_d18.py:177`, `tests/test_d10_d13_integration.py` (`:35`+`:53`),
`tests/test_d27_account_subs.py:27`, `tests/test_watchlist_columns_d21.py` (`:308`+`:322`),
`tests/test_d27_phantom_alarms.py:56`, `tests/test_d27_stream_health.py:67`,
`tests/test_history_backfill_loadpath.py:165`, `tests/test_dock_d18_region.py` (`:107`+`:110`),
`tests/test_d27_reconnect.py:163` — **15** ✓.

Plus the two title-bar-**text** assertion files: `tests/test_right_dock_d21.py` (`assert at_btn.text()
== "Active Trader"` at `:67`) and `tests/test_watchlist_nonregression_d22.py:142` — **2** ✓.
**Total 17** ✓, and **all 17 appear in the Phase-2 map with the edit each needs** (rows at
`docs/plan_proposal.md:133`–`:151` / the canonical `docs/plan.md` Phase-2 table) ✓.

The delta from the round-1 enumeration is explained and honest: the round-1 list of 14 omitted
`tests/test_dock_widths_d18.py:177` (`assert win.right_dock.objectName() == "Active Trader"`), which
the proposal notes was already inside the Phase-2 map — hence 15 keyed consumers.

**No other consumer is missing.** Cross-checks: (a) every `active_trader` reference in `tests/` is in
the map (`test_right_dock_d21.py`, `test_dock_widths_d18.py`, `test_dock_widths_d18_impl.py`,
`test_dock_d18_region.py`, `test_watchlist_nonregression_d22.py`, `test_order_validation.py`,
`test_order_rejections.py`, `test_d27_position_prices.py`, and the two deleted order-entry suites);
(b) `right_dock_container` consumers are only `test_dock_d18_region.py:88`/`:173` and
`test_dock_widths_d18.py:279` — all in the map; (c) no test asserts a *different* dock title that the
rename would newly collide with (only `test_crosshair_axis_lane.py:106`'s `"Portfolio" not in docks`,
which the plan inverts); (d) `tests/test_dock_layout.py` uses `win.right_dock` and pure
`plan_dock_widths` geometry only — it does **not** key on a title, so it correctly does not appear,
and the canonical map lists it explicitly under "Phase-2 files checked and *not* changed".

## Regression check — nothing the round-1 approval rested on was broken

- **`S4` (`ref_price` source) — unchanged and still verifies.** `ui/main_window.py:727`
  `self._symbol_last_prices: dict[str, float] = {}`; written at `:2266`
  (`self._symbol_last_prices[symbol.upper()] = float(price)`, `_record_symbol_price`); already the
  D27.5 consumer's source at `:3313` (`position.market_price = self._symbol_last_prices.get(...)`).
  `_ref_price_for` does **not** exist yet (grep-negative ⇒ genuinely new) ✓. The rationale sentence
  was **softened** to the code's actual reach (watchlist **or** live session), removing the round-1
  overstatement ✓.
- **`S6` (Portfolio-only dock) — unchanged.** Still `windowTitle()` **and** `objectName()` =
  `"Portfolio"`, widget = `ActivePortfolioPanel` directly, title bar = `summary_label`,
  `RIGHT_DOCK_MIN_WIDTH` 200, collapsed floor over **one** button, `RIGHT_DOCK_CAP_FRACTION` 0.40,
  `ui/dock_layout.py` + `plan_dock_widths` unchanged; `ui/active_portfolio_panel.py` not modified.
  The as-built shape it replaces is as described (`:485`–`:502` one dock titled/`objectName`d
  "Active Trader", `:471`–`:487` container + `_right_dock_layout`, `:2494` stretch juggling) ✓.
- **`S7` (`footprint_cache` drop) — unchanged.** DDL removal from `_init_schema` + idempotent
  `DROP TABLE IF EXISTS` in `_migrate_schema()`, which runs on every `DB()` open ✓. Confirmed the
  silent-removal risk is real: `tests/test_db_schema.py` `EXPECTED_TABLES` (`:13`–`:24`, ten tables)
  never listed `footprint_cache` and asserts `EXPECTED_TABLES <= tables`, so the Phase-3 absence/drop
  assertion is genuinely required ✓.
- **The order-path finding (FI-1's load-bearing claim) — unchanged.** `validate_order(`'s only
  production call site is still `ui/main_window.py:3112`; `_place_order` is at `:3100` with its
  `placeOrder` calls at `:3146`/`:3157`/`:3169`/`:3185`–`:3187`; `_close_position_by_id` (`:3446`)
  still calls `self.ib_client.placeOrder(order_id, contract, order)` at `:3505` with no validation
  and no connection guard; `_on_order_place_requested` is at `:3092` ✓. `S5`'s target and the
  `risk_reducing` carve-out are unchanged ✓.
- **The Phase-1/Phase-2 `tests/test_d27_reconnect.py` split — re-verified line by line**, since a
  wrong split would be a new defect: `:163` dock-title tuple ✓ (Phase 2), `:200`–`:203` DOM-depth
  assertions to keep ✓, `:204`–`:208` D37 session-depth to drop ✓, `:220` RT reissue keep ✓,
  `:221`–`:223` the `len(fake.mkt_data) == 4` count to re-derive ✓, `:224`–`:227` rebinding keep ✓,
  `:228`–`:229` DOM-depth rebound keep ✓, `:230`–`:232` session-depth rebound drop ✓, `:233`–`:236`
  S0 + watchlist keep ✓.

**Newly broken: nothing.** No previously-verified claim regressed; the revision only completed the
maps, the coverage re-homes, the token set and the cross-references.

## Validation steps (short form)

- **Requirements coverage** — **PASS.** All seven `AC-D41.1`–`AC-D41.7`, Journey 36's six steps and
  its edge cases, and `DG66`–`DG71` have an architecture home and a phase; the KEEP list (D38/D39,
  D27/D28, the chart, the retained order machinery, `footprint_cache_key`/`INDEX_PROXY`/
  `md_line_guard.assess`/`S0_TICKS`/`volume_baseline`) is preserved **and** now retains its test
  coverage (R2). `AC-D41.6` is correctly marked Requirements-owned/no code work.
- **Architecture completeness** — **PASS.** Stack, components, responsibilities, relationships,
  data model, integrations, boundaries, security/safety, performance, scalability, operational
  constraints and risks are all present, each decision with rationale and rejected alternatives.
- **Architecture consistency** — **PASS.** No contradiction found: no component depends on a
  removed service without an explicit re-home; the removed surface has no remaining caller; the
  D18/D21.13 outcomes survive on the renamed dock by construction; the request surface is closed at
  both the call sites and the client edge (`S9`).
- **Plan quality** — **PASS.** Three ordered, coarse phases with goals, requirement/journey coverage
  and dependencies; per-file partition (no implementation task list, no task graph, no per-task test
  spec); the only cross-phase overlap is the six shared production files + the one deliberately
  two-phase test file, both covered by strict sequencing (AP-1/AP-11).
- **Task Manager readiness** — **PASS.** No architectural decision is left to Task Manager. One
  mechanical gap was found and closed by the Validator without a decision (below).
- **Existing-repo compliance** — **PASS**, all five checks (see below).

## Existing Repo Compliance

- **Codebase Summary present and substantive — PASS.** The D41 increment carries its own
  Codebase Summary (data models + schema with the D41-relevant tables, a components table with
  responsibilities, key entry points with the wiring paths, the integration surface, and ten
  numbered source-validated facts).
- **Existing stack respected — PASS.** `S1`/`S2`/`S12` list the constrained choices first (Python
  3.11+ `.venv`, PyQt6, pyqtgraph, official `ibapi`, live-7496 fail-fast, numpy, SQLite via
  `config/paths.get_db_path()`, PyInstaller, pytest + pytest-qt offscreen) and **nothing existing is
  replaced or deprecated** — D41 only deletes. No new dependency; "New integrations: none".
- **Labels present — PASS.** `[existing]`/`[existing → deleted]`/`[existing → removed]`/`[new]`/
  `[new/changed]` on every Tech Stack, Components, Data Model and Integration Points entry.
- **Additive-only — PASS.** The single behaviour addition (`S5`'s additive `risk_reducing` keyword
  plus the re-homed gates) is what `AC-D41.4`/A71/DG71 require; the existing components it touches
  are otherwise untouched (`ui/active_portfolio_panel.py` explicitly not modified;
  `footprint_cache_key` deliberately not renamed).
- **Codebase Summary consistent with the proposal — PASS.** Every `[existing]` item exists as
  described and every `[existing → removed]` item was verified in source (`DEPTH`/`:37`,
  `DEPTH_HEATMAP`/`:38`, `MarketDepthManager.has_subscription`/`:45`, `OrderBookLevel`/`:105`–`:110`
  with zero references, the `footprint_cache` DDL, the single "Active Trader" dock);
  `footprint_cache_key` (`ibkr/contracts.py:144`) and `INDEX_PROXY` (`:133`) verified present as
  required survivors.
- **Requirements-side marker:** `Current Tech Stack` is present and placeholder-free — no
  requirements escalation on that count.

## Non-blocking observations (recorded, no decision required)

1. **One mechanical map gap, closed in the canonical plan without a new decision.** The Phase-2
   `ui/main_window.py` row did not name the now-dead `MarketDepthManager` import
   (`ui/main_window.py:35`) and the `self.depth_manager` construction (`:560`). Phase 1 deliberately
   keeps both (`:560`'s "last consumers are Phase 2's DOM path"); once Phase 2 removes those
   consumers the import would raise `ModuleNotFoundError` — loudly, so no silent failure, and
   AR-D41-2 already names `MarketDepthManager` among the dead imports the guard catches. The
   canonical plan's Phase-2 row now says so explicitly (marked *Validator completion, no new
   decision*), so Task Manager needs no inference.
2. **Two citation bounds tightened while carrying the map into the canonical plan** (editorial,
   per the citation convention): `tests/test_order_validation.py`'s transmits-valid test is
   `:109`–`:121` (the proposal wrote `:109`–`?`), and the `footprint_cache_key` re-home source is
   `tests/test_d36_footprint.py:389`–`:398` (the proposal's `:389`–`:395` covered the def + the two
   calls but stopped before the three assertions).
3. `tests/test_dock_layout.py` reads `win.right_dock` and pure `plan_dock_widths` geometry but keys
   on no title — the canonical map now names it under "files checked and *not* changed" so no worker
   "fixes" it.

## Requirements Escalations

**None this cycle.** `docs/plan_notes.md` **RG-D41-1** is recorded (`Status: addressed`,
`Escalation: none`): `AC-D41.4`'s two readings are resolved by the Validator's ruling in favour of
reading (1) (the re-homed gates), on the basis of the requirement's own KEEP list and `DG71`/`A71`.
No `ESCALATED_TO_REQUIREMENTS`; no Requirements Analyst action is required, and Task Manager may
proceed. `AC-D41.6`'s markdown markers are already present in `requirements.md` (Requirements-owned;
`AP-5` correctly forbids Build editing that file).

## Task Manager Readiness

**Ready.** The architecture is decision-complete (no stack, boundary, integration, data-model or
dependency decision is left open), the three phases are coarse, ordered and partitioned by file, both
`touches_files` maps are complete and independently verified, the KEEP-list coverage survives with
re-homed tests, and no requirement clause is left without architectural treatment. Task Manager can
build a valid task graph — including meaningful `touches_files` sets for wave scheduling — without
making any architectural decision.

## Artifacts written this cycle

- `docs/architecture.md` — `## D41 increment` appended (Codebase Summary, `S1`–`S12`, components,
  data model, integration points, non-functional approach, `AR-D41-1`–`AR-D41-12`, sequencing,
  supersessions, FI-1–FI-6 dispositions); supersession markers added under the `## D36 increment` and
  `## D37 increment` headings; a D41 clause added to the title line. The D1–D40 as-built record is
  preserved unchanged.
- `docs/plan.md` — `## D41 — Batch 18 removal …` appended with the coverage/traceability table, the
  three phases and their full `touches_files` maps, the sequencing/wave shape, `AP-1`–`AP-11`, the
  FI dispositions and the handoff; the document-state block updated. Terminal status line:
  `Status: READY_FOR_TASK_MANAGER`.
- `docs/plan_notes.md` — `RG-D41-1` status updated to `addressed` (ruling recorded; no escalation).
- `docs/plan_review.md` — this review.

## Final Decision
Status: APPROVED (2026-10-15, D41 cycle 2 of 3 — R1–R6 verified fixed against the tree; the
architecture decisions `S4`/`S6`/`S7` and the order-path finding are unchanged and re-verified; the
17-consumer dock-rename count is independently confirmed; no new defect was introduced. Task Manager
may proceed; `docs/plan.md` carries `Status: READY_FOR_TASK_MANAGER`.)

---

# Plan Review — Batch 18b (**D42**) — 2026-10-15 (initial validation)

## Review Status
Status: CHANGES_REQUIRED

## Validation Summary
Full Validation Method (no provisional pass exists for D42). Validates `docs/plan_proposal.md`
(mtime 19:19, `Status: READY_FOR_VALIDATION`) and `docs/architecture_proposal.md` (19:17) against
`docs/requirements/requirements.md` (19:06, `Status: READY_FOR_PLAN`) — `### D42` (`:3529`–`:3617`),
`AC-D6.4` revised (`:1288`–`:1293`), `AC-D7.1` revised (`:1326`–`:1330`), the `AC-D9.2` note
(`:1476`), `AC-D16.8` extended (`:1901`–`:1938`), `AC-D16.9` new (`:1940`–`:1972`), `A72`–`A73`,
`R63`–`R64`, `DG68` (resolved) + `DG72`, `open_questions.md` **Q51/Q52** (answered 2026-10-15).

**Run shape.** The invocation preamble carries **no** `phase: P<n>`, so this is a **legacy
single-scope** run: the proposal files are the unsuffixed ones, the review file is
`docs/plan_review.md` (not `plan_review_P<n>.md`), and there is **no phase gate** (no earlier phase to
wait on) — approval would be direct, merging the D42 increment into the cumulative
`docs/architecture.md` / `docs/plan.md`.

**Escalation routing.** `docs/code_review/escalations.json` holds **no** `"routed_to": "PLAN"` entry
(ESC-038/ESC-042 are `routed_to: REQUIREMENTS`, `open`; ESC-037/ESC-041 are `routed_to: BUILD`,
`open`; ESC-032/033/034/036/043/044/045 are BUILD-owned and out of scope). This is a normal forward
cycle; the escalations file was **not** edited.

**Outcome.** The proposal is **substantively sound** — the two workstreams are correct, the two core
decisions (`S13`/`S14`; `S15`–`S19`) are verified against the source, all four flagged issues are
honest, and the three supersessions are recorded rather than silent. It is **not approvable as
written** for two checkable reasons: an unresolved phasing/`touches_files` contradiction (RC-D42-1)
and an under-stated correction set (RC-D42-2), plus one required precision fix (RC-D42-3). Both
blocking items need a Plan decision, not a Validator guess, so **nothing was promoted** — no D42
content was written to `docs/architecture.md` / `docs/plan.md`.

**Stale-marker handling.** `docs/plan.md`'s terminal line carried the **D41** cycle's
`Status: READY_FOR_TASK_MANAGER`. Since this cycle is `CHANGES_REQUIRED`, that marker was replaced so
the plan cannot read as ready for Task Manager on the D42 cycle (the D41 record above it is
untouched).

## Requirements Coverage (one line per step)
Every revised/extended criterion has a plan treatment, and the three required supersessions are
recorded as supersessions:

| Criterion | Plan treatment | Supersession recorded? |
|---|---|---|
| `AC-D6.4` (revised: `body = min(max(0.65×pitch, F), pitch)`, `body <= pitch`, floor yields at `pitch < F`, wick stays cosmetic 1 device px) | Phase 1, `S13`+`S14`; `ui/candlestick_item.py::_draw_candles` (`:136`–`:138`), `ui/chart_panel.py::_clamp_half_width` (`:1229`/`:1242`–`:1244`) | **Yes** — the former *unconditional* "body remains `>= 4` device pixels wide" is recorded as superseded (`plan_proposal.md` correction record item 1; `architecture_proposal.md` supersessions item 1) |
| `AC-D7.1` (revised: `gap = pitch − body >= 0` hard; `> 0` whenever `pitch > F`; `0` acceptable at `pitch <= F`; 35 % intent unchanged) | Phase 1, `S13`; Journey 8 edge case | **Yes** — the former "the gap remains positive" wording + the D7 dense-view edge case recorded as relaxed (`Q51`) |
| `AC-D9.1`/`AC-D9.2` + the `:1476` note (volume width == price body width, same capped `w`) | Phase 1, `S13` (one shared helper; volume consumes the same capped `w`) | n/a (intent unchanged) |
| `AC-D16.8` (extended: ≥ 30 trading sessions, **RTH and ETH**; a session counts only with a bar inside the current mode's window; all five intraday windows fall short; mode isolation) | Phase 2, `S15`, `S17`, `S18`, `S19`, `S20` | **Yes** — the RTH-only default recorded as superseded by `Q52` |
| `AC-D16.9` (new: mode-aware day presence + mode-aware cache; present-but-empty = missing span, both directions; measurables (a)/(b)/(c)) | Phase 2, `S15`, `S16`, `S19`; Data Model `bars` | n/a (new criterion) |
| `AC-D16.1`/`AC-D16.3`/`AC-D16.4` (unchanged) | Phase 2 non-regression + Phase 3 | n/a — preserved |
| `AC-D16.7` (ESC-023 New-Year exception) | Phase 3 non-regression | n/a — untouched |
| `A72`, `R63`, `R64`, `DG72` | Phases 1–2 (`S13`, `S17`, `S18`, `S21`; risks `AR-D42-1`–`AR-D42-6`) | n/a |
| Out-of-scope escalations (ESC-032/033/034/036/043/044/045; ESC-041/ESC-037 BUILD-owned) | Explicitly excluded in both proposal files | n/a — correct |

Both workstreams' `ext_hours=True` limbs are covered (WS1 via the ESC-041 Ext-Hours-ON repro; WS2
via `S15`–`S19` for both modes), and each workstream states its own RED→GREEN evidence.

## Architecture Findings
Independent source verification (each cited line was read in the tree this cycle):

**Verified as claimed (no change required).**
- `ui/candlestick_item.py:122`–`:140` applies `min_w = 2.0 / px_per_sec` **unconditionally** with no
  pitch cap (`:136`–`:138`) — the ESC-041/ESC-042 defect shape, confirmed.
- `ui/chart_panel.py:1229` `_clamp_half_width` mirrors it at `:1242`–`:1244`; `_refresh_candles`
  takes `w_vol = self._clamp_half_width(self._candle_half_width)` (`:1303`) and
  `_refresh_live_bar` the same at `:1352` — so candle and volume share the floor today, and a single
  shared helper (`S13`) is the right single-source fix for `R63`'s divergence risk.
- `_compute_candle_half_width` (`:1215`–`:1227`) already computes the **display-x** median diff
  (`self._to_display(...)`, `:1223`) and caches it; `_draw_candles`' clamp reads the ViewBox at
  generation time (`px_per_sec = vb.width() / x_span`). So the pitch, the base half-width and
  `px_per_sec` are all in the **same** display-x/ViewBox unit — `S13`/`S14`'s "same pixel unit" claim
  is **sound**, and carrying the pitch as a second cached value adds **no** sort (the D28.4 override
  is preserved; `set_data(..., width=...)` at `:1318`/`:1326`/`:1347`).
- `services/backfill_service.py:208` `present_days = {_et_date(ts) for ts in ts_values}` is
  **mode-blind**, while the bar-level pass (`:276`) already calls
  `session_windows(day_start, day_end, ext_hours)` — one planner deciding presence two ways,
  confirmed. `:205`–`:206` returns `[]` for an empty cache and `:209`–`:215` anchors at
  `min(present_days)`, so history is **never** extended backwards (the ESC-038 mechanism), confirmed.
- `data/bar_cache.py:8` `RETENTION_BARS = 5000`; `:13` `save_bars` / `:27` `get_bars` key on
  `(symbol, timeframe)` only; `:39`–`:52` `prune` deletes everything outside the newest `keep`.
  `data/db.py:16`–`:22` `bars` `PRIMARY KEY (symbol, timeframe, ts)` with no mode column.
  `config/settings.py:45` `SESSION_BAR_CAP = 5000`. `ui/ticker_session.py:295`/`:300`/`:313`
  (session reads + the two `SESSION_BAR_CAP` trims) and `ui/chart_panel.py:1150`–`:1157` (the panel
  trim). `ui/main_window.py:1630`/`:1647`–`:1652`/`:1662`/`:1668`–`:1684`/`:1970`/`:1973`/`:1974`/
  `:2046`–`:2054`. `ui/ticker_session.py:127` (`_wave_extended_hours`), `:684` (D39 preload),
  `:843`/`:858`/`:870` (`queue_wave_plans`/`_issue_wave_chunks`, `extended_hours=` passed through).
  `ibkr/market_data.py:7`–`:13` `TIMEFRAME_CONFIG`. All confirmed at the cited lines.
- `ui/main_window.py:2052`–`:2054` (`_missing_backfill_trading_days`' own mode-blind `present_days`)
  is the AC-D16.4 shortfall report — confirmed mode-blind, so `S15`'s export-and-reuse is correct.

**`S18` (floor-aware bar budget) is sound and necessary — ratified.** Independent arithmetic and
trim check, per timeframe × mode:

| timeframe | bars / session (RTH 6.5 h) | bars / session (ETH 16 h) | 30 sessions, RTH | 30 sessions, ETH |
|---|---|---|---|---|
| `1 min` | 390 | 960 | **11,700** | **28,800** |
| `5 mins` | 78 | 192 | 2,340 | **5,760** |
| `15 mins` | 26 | 64 | 780 | 1,920 |
| `1 hour` | 6.5 | 16 | ~195 | 480 |
| `4 hours` | 1.625 | 4 | ~60 | 120 |

Three cells exceed the flat 5,000 — `1 min` RTH, `1 min` ETH, `5 mins` ETH — exactly as the proposal
states. And the floor would genuinely be destroyed after fetching it: `BarCache.prune`
(`data/bar_cache.py:39`–`:52`, `keep=RETENTION_BARS` at `ui/main_window.py:1973` today) deletes every
row outside the newest 5,000, and `TickerSession.set_bars` (`:300`)/`_append_bar` (`:313`) and
`ChartPanel._bars` (`:1150`–`:1157`) trim in memory to `SESSION_BAR_CAP`. So `AC-D16.8`'s "the
displayed bar series covers at least 30 trading sessions" is **unsatisfiable** while those bounds
stay flat. `S18` (`max(SESSION_BAR_CAP, ceil(min_sessions × window_seconds / bar_period) × 1.15)`,
flat values kept as default/minimum) is the right shape and is compatible with the *normative* part
of `AC-D28.4` ("memory stays bounded (bar cap + retention)", `requirements.md:3166`) — it revises the
`D28.4` description's soft "~5k" figure for the three dense cells only, and it is recorded as a
supersession (`S18`, supersessions item 4). **No Requirements escalation.** The only accuracy note:
`~8 MB per loaded 1 min ETH chart` is the right order but optimistic — 33,120 `Bar` dataclasses
(plain dataclass, `__dict__` per instance) plus the two plot arrays is realistically **~8–16 MB**;
state it as a range (non-blocking, see observations).

**`S16` (mode-aware cache) is required by the AC text, not a choice.** `AC-D16.9` states "the bar
cache/key is **mode-aware** (RTH vs ETH)" and `AC-D16.8` states the modes "must not cross-contaminate
… the **bar cache/key must be mode-aware** in **both** directions". The migration semantics (guarded
idempotent rebuild; legacy rows → `ext_hours = 1`, justified by the app's own default
`ui/main_window.py:244` `ext_hours_btn.setChecked(True)`; no row deleted) are sound.

**`S15`'s exported predicate + `S19`'s mode threading are correct and minimal** (no global; one place
per hop; the session already owns `_wave_extended_hours`, `ui/ticker_session.py:127`).

**The three supersessions are recorded, never silent** — `AC-D6.4`'s unconditional floor,
`AC-D7.1`'s positive gap, and the RTH-only depth default; plus explicit non-changes
(`TIMEFRAME_CONFIG`, `MAX_HISTORICAL_PER_600S`, the D28.3 wave pump, `market_calendar`,
`AC-D16.1`/`AC-D16.3`/`AC-D16.4`, the `Bar` dataclass, the order machinery, the D41 removals).

## Plan Findings
**Phase structure is right in shape** — three coarse phases (`Phase 1` WS1 width, `Phase 2` WS2 depth
+ mode-aware presence/cache, `Phase 3` reconciliation/non-regression), each with a goal, the criteria
and journeys it covers, its dependencies, and a deliverable; no per-task breakdown, no task-level
dependency graph, no per-task test specification. Phases 1–3 ordering is logical.

**The two core decisions are verified sound (task item 3).**
- **(a) `S13`/`S14`** — one pure `capped_body_half_width(median_diff, base_half_width, px_per_sec,
  floor_px=4.0)` in `ui/candlestick_item.py`, called by **both** `_draw_candles` and
  `ChartPanel._clamp_half_width` (and therefore by `_refresh_candles`/`_refresh_live_bar`). Checked:
  `w = min(max(base_half_width, floor_px/2/px_per_sec), median_diff/2)` is **exactly** the current
  `min_w = 2.0/px_per_sec` when the cap does not bind, and `body = 2w = min(max(0.65×pitch,
  floor_px/px_per_sec), pitch)` — `body <= pitch` **by construction**, at any density. The D28.4
  width override can carry the display-x pitch **without a sort** (`_compute_candle_half_width`
  already computes `median_diff` over display-x at `:1223`) and in the **same pixel unit** as
  `px_per_sec`. Candle and volume widths therefore cannot diverge. ✔
- **(b) `S15`–`S19`** — a window-membership presence predicate exported from `backfill_service` and
  used by **both** `find_missing_spans` (`:208`) and `MainWindow._missing_backfill_trading_days`
  (`:2052`, the AC-D16.4 shortfall report, confirmed mode-blind today); `bars` gaining `ext_hours`
  with key `(symbol, timeframe, ext_hours, ts)` via a guarded idempotent rebuild; the floor delivered
  **backwards** as one `MissingSpan` through the **existing** `plan_requests` (`:299`, which already
  chunks newest-first by `TIMEFRAME_CONFIG` duration) and the D28.3 wave pump
  (`ui/ticker_session.py:858`, `MAX_HISTORICAL_PER_600S = 60`), with `min_sessions=0` as the default
  so the pure planner suites keep their exact semantics (verified: `tests/test_backfill_service.py:210`/
  `:218`/`:226`/`:319` and `tests/test_d27_backfill_granularity.py:60`–`:106` all call
  `find_missing_spans` without `min_sessions`); and the removal of the empty-cache single-window
  branch (`ui/main_window.py:1668`–`:1684`, confirmed present and confirmed to be the ESC-038 repro).
  All four elements verified against the source. ✔

**Sequencing / `touches_files` — the claim fails (RC-D42-1).** The plan asserts "Phase 1 and Phase 2
are file-disjoint and therefore parallel-safe … **Shared files across phases: none** … `ui/chart_panel.py`
and `ui/candlestick_item.py` are Phase 1 only". That is **false as written**, because `S18` (and the
architecture's System Components and Data Model tables) requires a **third** cap site to become
floor-aware — `ui/chart_panel.py:1150`–`:1157` (`ChartPanel._bars`' `settings.SESSION_BAR_CAP` trim).
The plan's Phase 1 `ui/chart_panel.py` row does not mention it, Phase 2's map does not list
`ui/chart_panel.py`, and yet Phase 2's map assigns `tests/test_d28_4f_panel_bar_cap.py` to Phase 2 for
correction — a suite that tests **only** that `:1150` trim (`assert len(panel._bars) ==
settings.SESSION_BAR_CAP`, `tests/test_d28_4f_panel_bar_cap.py:53`, with `SESSION_BAR_CAP`
monkeypatched to 100 at `:43`). So Phase 2 would correct a test whose production subject it does not
touch. This is not cosmetic: `update_chart` seeds `ChartPanel._bars` from the session's (now up to
33,120-bar) series and `update_last_bar` trims it back to 5,000 on the next new-candle tick
(`ui/chart_panel.py:1150`–`:1157`) — i.e. the AC-D16.8 floor is discarded from the **displayed**
series after one live bar, which is FI-D42-1's own failure mode one layer up. Task Manager cannot
choose the phase/owner of that edit without making an architectural decision.

**Correction record under-states the affected suites (RC-D42-2).** `S17` flows the floor through
`load_chart`, whose default mode is **ETH** (`ui/main_window.py:244` `setChecked(True)`,
`:1570` fallback), and `S18` changes `prune`'s `keep`. Several D16 load-path assertions therefore
change **by design**, not by the presence predicate — and the plan's "Re-verified (corrected only
where the mode-aware predicate legitimately changes the outcome; never weakened)" framing plus
Phase 3's "**no** existing D16/D27/D28/D41 assertion weakened" are inconsistent with them. Named
below in RC-D42-2 with file:line.

**Assumptions are honest.** `AP-D42-1`–`AP-D42-9` are plan-level and each is checkable; `AP-D42-2`
(`min_sessions` default 0), `AP-D42-4` (legacy rows → ETH), `AP-D42-5` (the `F` unit), `AP-D42-6`
(`TIMEFRAME_CONFIG` unchanged) and `AP-D42-8` (D41 not reopened) are all verified against the tree.
One inaccuracy, non-blocking: `AP-D42-3`'s parenthetical "the primary chart **and pop-out charts**"
overstates the callers — pop-outs do not issue history at all (`ui/popout_window.py:131` attaches a
view to the shared session); the substantive claim (the floor is requested by `MainWindow.load_chart`
and **not** by the D25 headless alarm sessions, `services/alarm_monitor.py:287`) is correct.

**Flagged issues — dispositions (task item 5).**
- **FI-D42-1 — `AC-D16.8` is unsatisfiable while the D28.4 caps stay at 5000. ACCEPTED as recorded;
  `S18` RATIFIED; no Requirements escalation.** Arithmetic and prune/trim behaviour independently
  re-derived above (11,700 / 28,800 / 5,760 vs 5,000; `prune` + the three in-memory trims all discard
  the floor). The requirement's *outcome* is achievable and unchanged, so this is an architecture
  revision of a prior bound (recorded as a supersession), which is Plan's to make and mine to ratify.
  Cost note: restate `~8 MB` as `~8–16 MB`.
- **FI-D42-2 — the correction record names two width suites but five enshrine the old behaviour.
  ACCEPTED; the Validator extends the record.** Independently verified, all five exist and all five
  enshrine it: `tests/test_candle_spacing.py:4`–`:10` (a **source-string** check — `"median_diff *
  0.325" in text`, `"gap 35%"` — that never renders and fails once the literal moves into the
  helper); `tests/test_volume_width.py:103`–`:104` (dense legs `measured_body * px_per_sec ≈ 4.0` and
  `vol_width * px_per_sec ≈ 4.0`); `tests/test_chart_dpi.py:245`–`:250` (`assert body_dev >= 4.0` on
  the 960-bar DPR-2 dense dataset — post-fix the capped body is ≈ the pitch, so this **will** fail);
  `tests/test_d28_2_sessions.py:166` (`len(kept) == settings.SESSION_BAR_CAP`);
  `tests/test_d28_4f_panel_bar_cap.py:53`. The planned corrections are intent-preserving
  (regime/geometry assertions on the shared helper; `body == pitch` + `gap >= 0` + `volume == body`;
  the `>= F` claim moved to the non-dense dataset; the derived budget with the oldest-dropped /
  newest-kept invariant), not weakenings. ✔
- **FI-D42-3 — `AC-D16.9`'s "RTH bars are ETH coverage" read as a presence-predicate clause.
  ACCEPTED (ratified).** `AC-D16.9`'s own measurable (c) is phrased as
  `find_missing_spans(cached_ts, …, ext_hours=…)` on a **given bar set** — a predicate statement —
  so the strictly mode-keyed cache (`S16`, which the AC's explicit "the bar cache/key is mode-aware"
  sentence requires) is consistent with it; the cost is one extra fetch per mode switch, with no hole
  and no cross-contamination. The `'LEGACY'` fallback is recorded. Reading is faithful.
- **FI-D42-4 — the `F` unit wording. ACCEPTED; `AP-D42-5` is the right reading.** `AC-D6.4` says "4
  device pixels at DPR 2" while the shipped constant is 4 px in the `px_per_sec` (ViewBox logical-px)
  unit — measured evidence: `tests/test_volume_width.py:103`–`:104` asserts `body * px_per_sec ≈ 4.0`
  and `ui/candlestick_item.py:136` is `min_w = 2.0 / px_per_sec`. The criterion's operative clause is
  "measured in the **same** pixel unit", and `S13` keeps that unit, so the outcomes hold. RC-D42-3
  requires the plan's test evidence to state the unit explicitly.

## Existing Repo Compliance
Existing-repo mode is on (`requirements.md` carries "This is an existing repository", `:229`).
Pass/fail per check (Validation Method step 7):

- **Codebase Summary present and substantive — PASS.** `architecture_proposal.md` § *Codebase
  Summary* inventories the `bars`/`popouts` schema, the `Bar` dataclass, `BarCache`, the backfill
  planner, `market_calendar` windows, `TimeCollapseMap`, the in-memory caps, a component/
  responsibility table with line ranges, the entry-point data flow, and the existing integrations.
  Every cited line was read this cycle and matches (see Architecture Findings). Not a placeholder.
- **Existing stack respected — PASS.** `S1`/`S2`/`S3` list the existing choices **first** (Python
  3.11+/PyQt6/pyqtgraph/numpy; `ibapi` live-7496/SQLite/PyInstaller/pytest-qt offscreen) and nothing
  existing is replaced or deprecated. The only new constant is
  `config/settings.py::MIN_INTRADAY_SESSIONS = 30` (`S20`); `TIMEFRAME_CONFIG` is deliberately
  **unchanged** with its reason recorded. No flagged requirement demands any replacement.
- **Labels present — PASS.** System Components marks `[existing]` vs `[new/changed]` per item; Data
  Model marks each entity `[existing]` / `[new/changed]`; Integration Points marks each `[existing]`;
  every decision `S1`–`S21` carries `[existing]` / `[new in D42]` / `[extends D16: …]` /
  `[revises D6/D7: …]` / `[revises D28.4: …]`.
- **Additive-only — PASS.** No D1–D41 component is redesigned beyond what D42's criteria call for;
  the new/changed work is separated (the `ui/candlestick_item.py` helper; the
  `services/backfill_service.py` predicate + budget; `bars.ext_hours`; the cap sites).
- **Codebase Summary consistent with the proposal — PASS.** Everything the proposal treats as
  `[existing]` appears in the summary and exists in the tree (verified: `bars` PK, `RETENTION_BARS`,
  `SESSION_BAR_CAP`, `_clamp_half_width`, `present_days`, `session_windows`, `popouts.ext_hours`).

No requirements problem with the Current Tech Stack (it is present, complete and placeholder-free).

## Required Changes

**RC-D42-1 (blocking) — assign `ChartPanel._bars`' floor-aware cap and fix the `touches_files` /
parallel-safety claim.**
`S18` (and the architecture's System Components + Data Model) requires `ui/chart_panel.py:1150`–`:1157`
to use `floor_bar_budget(...)`, but no phase in `docs/plan_proposal.md` owns that edit, and the plan
claims Phase 1 and Phase 2 "share zero files". Required:
1. Add the `ui/chart_panel.py:1150`–`:1157` trim to the phase/file map (so all **three**
   `SESSION_BAR_CAP` sites — `ui/ticker_session.py:300`, `:313`, `ui/chart_panel.py:1150` — plus
   `BarCache.prune`'s `keep` are covered) and to Phase 2's goal/deliverable (which currently says
   "the **two** D28.4 caps become floor-aware").
2. Reconcile the parallelism claim: either (a) **drop** "Phase 1 and Phase 2 are file-disjoint and
   therefore parallel-safe" / "Shared files across phases: none" and sequence the phases (or place
   the two `ui/chart_panel.py` tasks in different waves), or (b) restructure the partition so the
   claim holds (e.g. land `floor_bar_budget` in a phase before the panel trim that consumes it, and
   state the resulting ordering dependency). Task Manager cannot make this choice; it is a phasing
   decision, and `build_wave.py` forbids two `in_progress` tasks with overlapping `touches_files`.
3. Update `AP-D42-1` and the `tests/test_d28_4f_panel_bar_cap.py` row so the test's correction and
   its production subject sit in the same phase.

**RC-D42-2 (blocking) — name the load-path suites that `S17`/`S18` legitimately change, and re-state
Phase 3's "no assertion weakened" goal so it is achievable.**
`S17` routes the floor through `load_chart` (default mode **ETH**, `ui/main_window.py:244`/`:1570`)
and removes the empty-cache branch; `S18` changes `prune`'s `keep`. The following assertions change
by design and must be **corrected (intent preserved)**, not merely "extended"/"re-verified":
- `tests/test_history_backfill_loadpath.py::test_t39_t02_cache_current_issues_no_request` —
  `assert stub.calls == []` (`:238`): with 5 seeded sessions < 30, the floor span issues requests.
  Intent to preserve: "a cache that satisfies the floor and reaches *now* issues no **redundant**
  request".
- `tests/test_history_backfill_loadpath.py::test_t39_t03_empty_cache_fallback_single_request` —
  asserts the very fallback `S17` **removes** (`len(stub.calls) == 1`, `endDateTime == ""`, `:255`–`:257`;
  branch at `ui/main_window.py:1668`–`:1684`). Intent to preserve: an empty cache is covered by the
  planner (now one floor span from the floor day to *now*), not by a special branch.
- `tests/test_history_backfill_loadpath.py::test_t39_t01_issues_one_request_per_planned_chunk` —
  compares the load's issued calls to its own `find_missing_spans(cached_ts, NOW, tf)` (no
  `min_sessions`) plan list (`:202`, `:206`); the test's own planner call must pass the floor.
- `tests/test_history_backfill_loadpath.py::test_t39_t06` / `::test_t39_t07` —
  `assert len(bars) == RETENTION_BARS` (`:431`, `:477`); the floor-aware `keep` for `5 mins`/ETH is
  6,624, so the invariant becomes the derived budget.
- `tests/test_history_backfill.py::test_t40_t01…` (`assert len(stub.calls) == 1`, `:285`) and `:590`;
  and the chunk-scenario test's `len(wave_calls) == len(plans)` (`:451`–`:457`).
- `tests/test_history_backfill_disconnect.py:362` (`assert len(stub.calls) == 1`).
- `tests/test_d28_4f_panel_bar_cap.py:53` (the flat-cap assertion) — cause is `S18`, not the
  presence predicate (see RC-D42-1).
Required: extend the correction record and `S21` to name these cases **and their cause** (the floor
span, the removed empty-cache branch, the floor-aware prune/budget), require intent-preserving
correction, and re-word Phase 3's goal ("no existing D16/D27/D28/D41 assertion **weakened**") plus
`R64`'s mitigation ("the D16 suite stays green") so they are consistent with these legitimate changes.
The pure-planner suites keep their exact semantics (`AP-D42-2` is correct as far as it goes —
verified at `tests/test_backfill_service.py:210`/`:218`/`:226`/`:319`,
`tests/test_d27_backfill_granularity.py:60`–`:106`); the gap is the **load-path** suites.

**RC-D42-3 (required, lower severity) — state the pixel unit in the WS1 test evidence.**
`AC-D6.4`'s non-dense measurable (`body == max(0.65 × pitch, F) > F`) holds only when `F` is applied
in the **same** unit as the measurement; at DPR 2 the shipped constant is 4 px in the `px_per_sec`
unit, i.e. 8 device px, not the AC's literal "4 device pixels at DPR 2". Required: (a) state the unit
explicitly in the WS1 RED→GREEN evidence and in `S13`'s `floor_px`; (b) ensure
`tests/test_d42_candle_width.py` applies `F` in that same unit (do **not** assert `F == 4.0` device px
at DPR 2) — the load-bearing assertions are the unit-free relations `body <= pitch` and `body == pitch`
at the dense repro; (c) **measure** the repro pitch in the test rather than hard-coding the
requirement's stated `3.83` (the exact figure depends on the ViewBox width the probe actually gets),
and assert the relation. Optionally note the same in the `AC-D6.4` measurable's paraphrase in the
plan so a later reader does not read `F` as a device-px literal at DPR 2.

**Non-blocking observations (recorded; no decision required).**
- FI-D42-1's `~8 MB per loaded 1 min ETH chart` → state as `~8–16 MB` (33,120 `Bar` dataclasses
  without `__slots__`, plus the two plot arrays).
- `AP-D42-3`'s "and pop-out charts" — pop-outs attach views to the session and issue no history
  (`ui/popout_window.py:131`); the substantive claim (load_chart only; D25 headless sessions excluded)
  is correct.
- `S17`'s "the empty-cache branch is removed" should also name the guard at
  `ui/main_window.py:1647`–`:1652` (`find_missing_spans(...) if cached else []`) and
  `services/backfill_service.py:205`–`:206` (the empty-cache early return), both of which must be
  bypassed when `min_sessions > 0` for the "one span from the floor day to *now*" case to exist.

## Requirements Escalations
**None.** Every flagged issue is resolvable at the architecture/plan level (FI-D42-1/2/4) or is a
faithful reading of the criterion as written (FI-D42-3), and `S18`'s revision of the D28.4 flat bound
leaves `AC-D28.4`'s normative clause ("memory stays bounded (bar cap + retention)") intact. No
`docs/plan_notes.md` entry is created this cycle and no `ESCALATED_TO_REQUIREMENTS` status is raised.
ESC-038 and ESC-042 stay `open` and `routed_to: REQUIREMENTS` in `escalations.json` (Code Reviewer's
to flip after re-verification); ESC-037/ESC-041 stay BUILD-owned; the escalations file was not edited.

## Task Manager Readiness
**Not ready.** Two blocking required changes must be resolved by Plan first: `ui/chart_panel.py`'s
floor-aware `_bars` trim is unowned in the phase/file map and the "file-disjoint / parallel-safe"
claim is false (RC-D42-1), and the correction set for the D16 load-path suites is under-stated so
Phase 3's "green with no assertion weakened" goal is not achievable as written (RC-D42-2). Until
those are fixed, Task Manager would have to choose a phase owner for a production edit, decide
whether `ui/chart_panel.py` may be shared between phases, and decide which existing assertions may be
corrected — all architectural/phasing decisions it must not make. Everything else is decision-complete
(the width cap, the presence predicate, the cache key/migration, the floor delivery through the
existing wave pump, the budget, the mode threading, the test surface).

## Final Decision
Status: CHANGES_REQUIRED (2026-10-15, D42 initial validation — round 1 of 3. The architecture is
substantively sound and both core decisions (`S13`/`S14`, `S15`–`S19`) are verified against the tree;
FI-D42-1/2/4 are accepted and FI-D42-3 is ratified; `S18` is ratified with no Requirements escalation.
Three required changes are listed: **RC-D42-1** (blocking — assign `ui/chart_panel.py:1150`'s
floor-aware cap to a phase and fix the `touches_files`/parallel-safety claim), **RC-D42-2** (blocking
— name the D16 load-path suites that `S17`/`S18` legitimately change and re-state Phase 3's goal),
**RC-D42-3** (required — state the pixel unit for `F` in the WS1 test evidence). Nothing was promoted
to the canonical `docs/architecture.md` / `docs/plan.md`; `docs/plan.md`'s terminal status is no longer
`READY_FOR_TASK_MANAGER`. Task Manager may **not** proceed. The user/Orchestrator re-invokes Plan.)

---

# Plan Review — Batch 18b (**D42**) — 2026-10-15 (cycle 2 of 3: RC-D42-1/2/3 verification, **APPROVED**)

## Review Status
Status: APPROVED

## Validation Summary
Cycle-2 validation of the **revised in place** proposal — `docs/plan_proposal.md` (19:38,
`Status: READY_FOR_VALIDATION`) and `docs/architecture_proposal.md` (19:38) against
`docs/requirements/requirements.md` (19:06, `Status: READY_FOR_PLAN`). Freshness holds (proposal ≥
requirements). **Legacy single-scope run** (no `phase: P<n>` in the invocation preamble): the
proposal files are the unsuffixed ones, the review file is `docs/plan_review.md`, and there is **no
phase gate** (no earlier phase to wait on) — so this is a **direct approval**, merging the D42
increment into the cumulative canonical artifacts.

**Escalation routing.** `docs/code_review/escalations.json` has **no** `"routed_to": "PLAN"` entry.
ESC-038/ESC-042 are `routed_to: REQUIREMENTS`, `open`; ESC-037/ESC-041 and
ESC-032/033/034/036/043/044/045 are `routed_to: BUILD`, `open` (all out of D42's scope by the
proposal's own statement). Normal forward cycle; the escalations file was **not** edited.

**Outcome.** All three required changes are genuinely fixed (verdicts below, each with `file:line`),
and nothing the round-1 approval rested on was broken. The plan is decision-complete: Task Manager can
write the two work items, the three phases and the `touches_files` partition without inventing any
architecture. **Approved**; the D42 increment is promoted into `docs/architecture.md` (§ *D42
increment*) and `docs/plan.md` (§ *D42 — Batch 18b*), and `docs/plan.md` ends
`Status: READY_FOR_TASK_MANAGER`.

## Required Changes — verdicts

**RC-D42-1 (blocking) — the third `SESSION_BAR_CAP` site is owned and the partition claim is
corrected. FIXED.**
- The site is now owned by **Phase 2**: `docs/plan_proposal.md` Phase 2 file map (`:179`) assigns
  `ui/chart_panel.py` → `ChartPanel.update_last_bar`'s `_bars` trim (`:1150`–`:1157`), and Phase 2's
  **goal** (`:111`–`:115`), **dependencies** (`:119`–`:124`) and **deliverable** (`:125`–`:127`) all
  name the third cap site. `S18`'s title **and** body carry it (`architecture_proposal.md:187`), as
  do the System Components row (`:214`), the Data Model row (`:232`), `AR-D42-3` (`:309`), the
  `AC-D16.8` traceability row (`:328`) and supersession 4 (`:350`–`:353`).
- The **false claim is gone**: "file-disjoint / parallel-safe / **Shared files across phases: none**"
  is replaced by "**Phase 1 and Phase 2 share exactly one file** — `ui/chart_panel.py` … the two
  `ui/chart_panel.py` tasks are therefore **sequenced into different waves**" (plan `:80`–`:86`,
  `:146`–`:157`, `:186`–`:192`), and `AP-D42-1` is rewritten to match (`:272`–`:278`).
- **Internal Phase-2 ordering** is stated: "`floor_bar_budget` must land **before** its consumers (the
  two session cap sites, the panel trim, and `prune`'s `keep`)" (plan `:122`–`:124`), and the panel
  trim task itself "lands **after** `floor_bar_budget` exists" (`:179`).
- The production edit and its test correction are in the **same** phase: both
  `ui/chart_panel.py` (trim) and `tests/test_d28_4f_panel_bar_cap.py` are Phase-2 rows (plan `:179`,
  `:181`), and the correction table says so explicitly (`:206`, `:224`).
- Independently re-verified in the tree: `ui/chart_panel.py:1150` and `:1157` both read
  `settings.SESSION_BAR_CAP` inside `ChartPanel.update_last_bar` (`:1138`); the other two sites are
  `ui/ticker_session.py:300` / `:313`; `config/settings.py:45` is `SESSION_BAR_CAP = 5000`;
  `data/bar_cache.py:39` is `prune(..., keep: int = RETENTION_BARS)`. The corrected suite tests
  **only** that trim (`tests/test_d28_4f_panel_bar_cap.py:53`, `SESSION_BAR_CAP` monkeypatched to 100
  at `:43`) — so the phase assignment is the right one.

**RC-D42-2 (blocking) — the D16 load-path corrections are named with cause, and the framing is
re-worded. FIXED.**
- A dedicated *Corrected — D16 load-path* table (plan `:208`–`:224`) names all **nine** cases, each
  with its **cause** (the floor span / the removed empty-cache branch / the floor-aware
  prune/budget) and its **preserved guarantee**: `test_history_backfill_loadpath.py::test_t39_t02`
  (`:238`), `::test_t39_t03` (`:255`–`:257`), `::test_t39_t01` (`:202`/`:206`),
  `::test_t39_t06` (`:431`) / `::test_t39_t07` (`:477`), `test_history_backfill.py::test_t40_t01`
  (`:285`), `::test_t40_t04` (`:451`–`:457`), `::test_t40_t06` (`:590`),
  `test_history_backfill_disconnect.py::test_t43_t06` (`:362`), `test_d28_4f_panel_bar_cap.py`
  (`:53`).
- The framing is now consistent everywhere: Phase 3's goal — "**either** keeping its **exact**
  expectation **or corrected intent-preserving** … **none weakened, none deleted**" (plan `:131`–`:136`);
  `AP-D42-2` (`:279`–`:283`); `S17`'s rationale (`architecture_proposal.md:186`); `AR-D42-6`
  (`:312`); the Non-Functional test-fidelity bullet (`:287`–`:293`); `S21` (`:190`). `R64`'s
  mitigation is satisfied in the architecture/plan (the Validator cannot edit `requirements.md`; the
  requirements' own `R64` text is untouched and its claim "the D16 suite stays green" is met by exact
  planner semantics + intent-preserving load-path corrections).
- **Independent spot-checks (three-plus, all against the actual test bodies — not the list on
  trust):**
  1. `tests/test_history_backfill_loadpath.py::_seed` (`:79`–`:100`) — its docstring states the
     "ext-hours toggle (**default ON: 04:00-20:00 ET**)" and the body seeds `04:00 → 19:59` ET bars
     per day; `_load` (`:179`–`:186`) drives the real `load_chart()` with no mode argument. So the
     load-path suites really do run in **ETH** by default — the stated cause is correct.
  2. `::test_t39_t02` (`:227`–`:241`) seeds **five** days (`2026-11-02…11-06`) and asserts
     `stub.calls == []` at `:238`; with a 30-session floor five sessions is short, so the floor span
     must issue requests — the assertion changes by design. `::test_t39_t03` (`:247`–`:263`) asserts
     `len(stub.calls) == 1` with `endDateTime == ""` (`:255`–`:257`) — i.e. it exercises **exactly**
     the `elif not cached` empty-cache single-window branch (`ui/main_window.py:1668`–`:1684`,
     confirmed present in the tree) that `S17` removes.
  3. `::test_t39_t01` (`:192`–`:221`) builds `plans` from its **own** `find_missing_spans(cached_ts,
     NOW, tf)` call (`:202`) — no `min_sessions` (and no `ext_hours`, so the signature default
     `False`) — then asserts `len(stub.calls) == len(plans)` (`:206`); that planner call must indeed
     be updated in lockstep with the load path. `::test_t39_t06`/`::test_t39_t07` assert
     `len(bars) == RETENTION_BARS` at `:431` / `:477` — the floor-aware `keep` for `5 mins`/ETH
     (6,624) makes the derived budget the right invariant.
  4. `tests/test_history_backfill.py`: `:285` (`len(stub.calls) == 1`), `:457`
     (`len(wave_calls) == len(plans)`) and `:590`/`:592` (`len(stub.calls) == 1`,
     `endDateTime == ""`) all match the table; `tests/test_history_backfill_disconnect.py:362`
     (`len(stub.calls) == 1`, empty cache) matches too.
  The five enshrining suites were also re-checked in the tree: `test_candle_spacing.py:4`–`:10`
  (`"median_diff * 0.325" in text`, `"gap 35%"`), `test_volume_width.py:103`–`:104`
  (`measured_body * px_per_sec ≈ 4.0`, `vol_width * px_per_sec ≈ 4.0`), `test_chart_dpi.py:245`–`:250`
  (`assert body_dev >= 4.0`), `test_d28_2_sessions.py:166` (`len(kept) == settings.SESSION_BAR_CAP`),
  `test_d28_4f_panel_bar_cap.py:53` — all five confirmed, all five will fail or mis-describe the
  revised criterion, and none is proposed for weakening.

**RC-D42-3 (required) — the WS1 evidence states the unit, applies `F` in it, measures the pitch.
FIXED.** The WS1 RED→GREEN evidence (plan `:238`–`:254`) states the unit as "the **ViewBox
logical-pixel unit that `px_per_sec` yields**" with "`F = 4.0` in that unit is **8 device px at DPR
2**", declares the requirement's `3.83`/`8.86` figures **indicative only**, **measures** the repro
pitch "from the rendered series instead of hard-coding it", and asserts only the unit-free relations
`body <= pitch` / `body == pitch` — with an explicit "**not** `F == 4.0` device px". The same holds in
Phase 1's `tests/test_d42_candle_width.py` row (`:168`), `AP-D42-5` (`:295`–`:300`), the correction
record item 1 (`:376`–`:380`), `S13` (`architecture_proposal.md:182`), the Non-Functional correctness
bullet (`:258`–`:265`) and `AR-D42-2` (`:308`). **No `F == 4.0` device-px assertion remains anywhere**
in the plan (the only `4.0` device-px occurrence left is the *illustrative* RED description "body
4.00 logical px > the measured ≈ 3.83 logical-px pitch", which is unit-labelled).

## Regression check — nothing the round-1 approval rested on was broken
- **`S13`/`S14`** unchanged in substance (the only addition is the stated unit of `F`, which is the
  RC-D42-3 fix); the arithmetic, the three call sites, the "same display-x unit" argument and the
  no-extra-sort property all still hold.
- **`S15`–`S19`** unchanged: the exported presence predicate, the guarded idempotent `bars` rebuild
  with key `(symbol, timeframe, ext_hours, ts)`, the `min_sessions=0` default, the floor span through
  the **existing** `plan_requests` + D28.3 wave pump, and the per-hop mode threading. **`S18`** keeps
  its shape and now names the third site, the ownership and the sequencing.
- **`FI-D42-1`/`FI-D42-3`/`FI-D42-4`** unchanged in substance and still verified; all four flagged
  issues remain honest, and none converts an unresolved decision into an assumption.
- **Fold-ins landed:** the five width suites with line refs (`FI-D42-2`, `S21`); `~8–16 MB`
  (`FI-D42-1`, Non-Functional); the `requirements.md:1957`–`:1958` and `:1967`–`:1969` citations for
  the ratified `FI-D42-3` reading — **independently verified against the file** (line 1958 carries
  "The bar cache/key is **mode-aware** (RTH vs ETH) … This applies", and measurable (c) is exactly at
  `:1967`–`:1969`); `AP-D42-5`; and the `AP-D42-3` pop-out correction (`ui/popout_window.py:131` is
  `session.attach_view(...)` — pop-outs issue no history, confirmed in the tree).
- **Nothing else regressed:** both workstreams still cover `ext_hours=False` **and** `ext_hours=True`
  (WS1 via the Ext-Hours-ON ESC-041 repro; WS2's per-mode guard for all five timeframes);
  ESC-032/033/034/036/043/044/045 are still explicitly out of scope; and all four supersessions
  (`AC-D6.4` unconditional floor, `AC-D7.1` positive gap, the RTH-only depth default, D28.4's flat
  5000 bound) are still recorded **as supersessions**, never silent.

## Validation steps (short form)
- **Coverage — PASS.** Every revised/extended criterion and journey maps to a phase: `AC-D6.4`,
  `AC-D7.1`, the `AC-D9.2` note, Journey 7/8 → Phase 1; `AC-D16.8`, `AC-D16.9`, Journey 17 →
  Phase 2; `AC-D16.1`/`AC-D16.3`/`AC-D16.4` (non-regression) and `AC-D16.7` → Phases 2–3. No
  requirement is weakened, reinterpreted or silently removed; the three required supersessions are
  recorded as supersessions.
- **Completeness — PASS.** Codebase Summary, Summary, Tech Stack Decisions (`S1`–`S3` existing first,
  then `S13`–`S21`), System Components, Data Model, Integration Points, Non-Functional Approach,
  Architecture Risks (`AR-D42-1`–`AR-D42-11`) and the traceability table are all present, each
  decision carrying a rationale and the alternatives considered.
- **Consistency — PASS.** No contradiction: the one shared file and its wave sequencing are stated
  identically in the phases, the per-file map, `AP-D42-1` and the correction record; the cap
  arithmetic (11,700 / 28,800 / 5,760 > 5,000) matches the tree (`SESSION_BAR_CAP = 5000`,
  `RETENTION_BARS = 5000`, `prune` deleting outside `keep`); the mode-aware cache is consistent with
  `AC-D16.9`'s measurables under the ratified `FI-D42-3` reading; the revised unit of `F` is stated
  in one place and referenced, not re-derived.
- **Plan quality — PASS.** Three coarse, logically ordered milestone phases (width; depth/presence;
  reconciliation), each with goal / covered criteria / dependencies / deliverable; no per-task
  breakdown, no task-level dependency graph, no per-task test specification. The one cross-phase
  ordering constraint is expressed as a wave rule, which is Build's own vocabulary.
- **Task Manager readiness — YES.** Task Manager can build the graph without a new architectural
  decision: the owner of the third cap site, the shared file and its wave sequencing, the budget
  helper's position relative to its consumers, the cache key/migration, the floor's delivery path,
  the mode threading, the corrected/extended/added test surface and the supersession record are all
  fixed.
- **Existing-repo compliance (step 7) — PASS.** Marker sentence + Current Tech Stack preserved;
  `S1`/`S2`/`S3` list the existing choices **first** and nothing existing is replaced or deprecated
  (the only new constant is `MIN_INTRADAY_SESSIONS`; `TIMEFRAME_CONFIG` is deliberately unchanged with
  its reason); System Components / Data Model / Integration Points label every item `[existing]` /
  `[new/changed]`; the Codebase Summary is substantive, source-validated this cycle, and consistent
  with the proposal (every `[existing]` item named was found in the tree at the cited symbol); the
  change set is additive apart from the two explicitly superseded bounds.

## Non-blocking observations (recorded; no decision required)
1. **`architecture_proposal.md:40`–`:41`** still says "`docs/plan_review.md` is the **APPROVED** D23
   cycle (not `CHANGES_REQUIRED`), so this is a normal forward cycle". That was true at the start of
   the D42 cycle but is stale now (the file ended `CHANGES_REQUIRED` for D42 round 1). It is a
   proposal-header claim about cycle state, **not** an architectural decision, and it was **not**
   carried into the canonical artifacts — the canonical review (this file) and the canonical
   `architecture.md`/`plan.md` describe the cycle correctly. Recorded so a later reader does not
   mistake the proposal's header for the current state.
2. **Suite-count wording.** `S21`'s title says "extends **five**" and `AP-D42-9` says "**five** are
   extended"; the enumerated sets in the per-file map are `tests/test_backfill_service.py`,
   `tests/test_d27_backfill_granularity.py` and `tests/test_db_schema.py` (three), with
   `tests/test_history_backfill_loadpath.py` named as *extended* in `S21` but as *corrected* in the
   per-file map. The canonical artifacts state the concrete sets rather than the count (an editorial
   normalization — no decision involved); `AP-D42-9`'s substantive point ("the total moves; **green**
   with every assertion either exact or corrected intent-preserving — not count parity") stands.
3. `S17`'s `test_t39_t01` note says the test's own planner call "must pass the floor"; it should also
   pass the **mode** (the call at `:202` omits `ext_hours`, so it currently uses the signature default
   `False` while the load path runs ETH). Same class as `t40_t04`. This is Build-side test detail
   inside an already-identified correction, not a missing decision.
4. `FI-D42-1`'s `~8–16 MB` and `FI-D42-2`'s five-suite list are both now in the canonical artifacts;
   `DOC-1` (doc figures quoting a suite total) will go stale again once the four new suites land —
   owner/Analyst follow-up, recorded in the plan.

## Requirements Escalations
**None.** Every flagged issue is resolved at the architecture/plan level (`FI-D42-1` by `S18`,
ratified; `FI-D42-2` as a plan-level correction-set extension; `FI-D42-4` by `AP-D42-5`, ratified) or
is a faithful reading of the criterion as written (`FI-D42-3`, ratified with both
`requirements.md` lines cited). `S18`'s revision of the D28.4 flat bound leaves `AC-D28.4`'s
normative clause ("memory stays bounded (bar cap + retention)") intact, and `AC-D16.8`'s outcome is
unchanged. `docs/plan_notes.md` was **not modified** this cycle: no requirements or planning gap
remains open, so no `RG-*`/`FI-*` entry was warranted and no `ESCALATED_TO_REQUIREMENTS` status was
raised. ESC-038/ESC-042 stay `open`/`routed_to: REQUIREMENTS` and ESC-041/ESC-037 stay BUILD-owned in
`escalations.json` (Code Reviewer's to flip after re-verification); the escalations file was not
edited.

## Task Manager Readiness
**Yes.** Task Manager can decompose the three phases into tasks with acceptance criteria and matching
tests without inventing architecture. The canonical artifacts carry the reconciled `S18` (third cap
site + wave sequencing), the corrected `touches_files` partition (one shared file,
`ui/chart_panel.py`), the enumerated load-path corrections with their causes, and the stated unit of
`F`. The only task-graph-shaping rule the plan imposes is the **different-wave** requirement for the
two `ui/chart_panel.py` tasks, which is Build's own `touches_files` rule, not a new decision.

## Final Decision
Status: APPROVED (2026-10-15, D42 cycle 2 of 3 — **RC-D42-1**, **RC-D42-2** and **RC-D42-3** are
verified fixed against the tree, including independent spot-checks of the load-path test bodies and
the five enshrining suites; `S13`/`S14`, `S15`–`S19`, `S18` and `FI-D42-1`/`FI-D42-3`/`FI-D42-4` are
unchanged and still sound; no new architectural decision is required. The D42 increment was merged —
not regenerated — into `docs/architecture.md` (§ *D42 increment*, with supersession cross-reference
markers on the D6/D7/D9 and D28.4 rows it revises) and `docs/plan.md` (§ *D42 — Batch 18b*, ending
`Status: READY_FOR_TASK_MANAGER`). `docs/plan_notes.md` unmodified — no requirements gap. **Task
Manager may proceed.**)

---

# Plan Review — Batch 18b (**D42**) — 2026-10-16 (cycle 3 of 3: the `ESC-050` enumeration amendment, **APPROVED**)

## Review Status
Status: APPROVED

## Validation Summary
**Targeted re-validation** (invocation reason `retry_1_of_3`, legacy single-scope run): the Plan agent's
**Revision 3** amendment to `docs/plan_proposal.md` / `docs/architecture_proposal.md` addressing the
**PLAN-routed** Code Reviewer escalation **`ESC-050`** (`status: open`) — an **enumeration/accuracy**
fix to the two proposal documents with **no design change**. D42 is **built, verified and complete**
(26/26 tasks; full offscreen suite 1009 passed, exit 0; `docs/build/build_log.md` = `READY_FOR_REVIEW`),
so nothing of the ratified design (`S13`–`S21`, the `AC`s, the phase boundaries, the tasks) was
re-opened or re-litigated. `ESC-050`'s substantive asks were re-verified **against the live tree, not on
trust** (below). The amendment is **accurate and complete in substance** and closes both under-counts;
three residual wording/citation slips were normalized **editorially** in the canonical artifacts — the
same treatment cycle 2 gave the suite-count wording — and are recorded under *Non-blocking
observations*. **No new architectural decision is required.**

`docs/code_review/escalations.json` was **not** edited (Code Reviewer owns it; `ESC-050` stays `open`
for it to flip after re-verifying). `docs/plan_notes.md` was **not** modified (no requirements gap).

## Independent verification (this cycle — `ESC-050`'s claims vs the tree)

1. **The six load-path-*driving* suites really do drive the load path with a fixed-size stub — PASS.**
   Each of the six has `win.md_manager.req_historical_data = lambda *a, **k: next(hids)` and the
   pre-fix values `ESC-048`/`ESC-050` cite: `tests/test_d24_popouts.py:22-23` `iter([6101,6102,6103])`,
   `tests/test_phase3_fixpass.py:33-34` `iter([7101,7102,7103])`,
   `tests/test_d24_alarm_full_chain.py:39-40` `iter([8101,8102])`,
   `tests/test_d24_smoke_gate.py:37-38` `iter([9601,9602])`,
   `tests/test_d24_9_popout_persistence.py:54-55` `iter([7101])`,
   `tests/test_d28_tick_burst_baseline.py:31-32` `iter([9101,9102])`. On the live tree each is now the
   `itertools.count(<first>)` form (`ESC-048`'s BUILD fix has landed), so the amendment's past-tense
   description is correct.
2. **The counts sum to 19 — PASS, and independently corroborated.** 7+7+2+1+1+1 = **19**, matching
   `ESC-048`'s reproduced 20 failures (19 + `test_d42_nonregression.py::test_full_offscreen_suite_is_green`)
   and `review_log.md`'s D42 section. **My own census** (spot-check of all six, not two):
   `test_d24_popouts.py` has exactly **7** test functions (all drive the load);
   `test_d24_alarm_full_chain.py` **2**; `test_d24_smoke_gate.py` **1**;
   `test_d28_tick_burst_baseline.py` **1**; `test_d24_9_popout_persistence.py` **2**, of which **1**
   (`test_popout_window_persists_on_open_close`) drives the load and `test_popout_save_load_delete`
   never boots a `MainWindow`; `test_phase3_fixpass.py` **9**, of which **7** drive the load
   (`fix2a`–`fix2e` are pop-out drag/click tests). The per-suite figures are therefore **failing test
   cases**, which is why the canonical artifacts say "cases" where the proposal says "assertions"
   (editorial precision, see observation 1).
3. **The four extra D16 sites — PASS (3 changed, 1 correctly disclosed as unchanged).** `git diff -U0
   b48133d` shows changed hunks for `test_t40_t03` (`b48133d:388`–`:390`), `test_t43_t03`
   (`:249`–`:255`) and `test_t44_t03` (`:481`–`:485`), each matching the amendment's "assertion today"
   (`"incomplete"/"missing"/"failed" not in msg`; `assert any(date(...).isoformat() in msg for ... in
   MISSING_DAYS)`; the same status-message form). **`test_t40_t05` has no hunk at all.**
4. **The `t40_t05`-vs-`t40_t04` claim — TRUE as stated.** `git show b48133d:tests/test_history_backfill.py`
   at `:484`–`:485` is `msg = win.status_bar.currentMessage().lower()` followed by
   `assert "incomplete" not in msg and "missing" not in msg and "failed" not in msg`, **inside
   `test_t40_t04_chunked_multi_request_continuity`** (which spans `:446`–`:490`);
   `test_t40_t05_switch_mid_flight_isolated` (`:495`–`:585`) contains **no** shortfall-message
   assertion in either revision. The amendment therefore **correctly contradicts** `ESC-050`'s own
   naming rather than copying it, and relocates the correction precisely.
5. **`t39_t04` / `t39_t05` (the two Plan re-verification adds) — substantively PASS.** In `b48133d`
   `t39_t04` declares `def spy_save(bars)` / `def spy_get(s, t)`; on the live tree they are
   `def spy_save(bars, **kwargs)` / `def spy_get(s, t, **kwargs)` (S19 threads `ext_hours` into
   `BarCache.save_bars`/`get_bars`). In `b48133d` `t39_t05` asserts
   `assert win._history_req_ids == set()`; on the live tree it is `isdisjoint(old_ids)` (the new
   session's own floor span). Both rows describe real, intent-preserving corrections. (Their **line
   citations** are off — see observation 2.)
6. **"14 changed test functions" — PASS, verified exactly.** `git diff -U0 b48133d` hunk headers give
   `test_history_backfill_loadpath.py` **7** (`t39_t01`…`t39_t07`), `test_history_backfill.py` **4**
   (`t40_t01`, `t40_t03`, `t40_t04`, `t40_t06`), `test_history_backfill_disconnect.py` **3**
   (`t43_t03`, `t43_t06`, `t44_t03`) = **14**.
7. **`AR-D42-6` no longer rests on an exhaustiveness claim — PASS.** The mitigation now states that the
   enumeration is complete **and** generated by a rule, and adds: *"Any residual site not named is
   covered by the invariant, so the mitigation no longer rests on the enumeration being exhaustive by
   inspection."* That satisfies "be true or be replaced by the generalisable rule" — it is **both**.
8. **The enumeration rule is checkable — PASS (judgement).** The four steps map onto mechanically
   executable actions that **would have caught both of D42's under-counts**: step 1 (enumerate by call
   site of the changed entry point, including tests that only *drive* it) is exactly what finds the six
   suites; step 3 (`grep` the whole suite for a fixed-size stub of the changed feed —
   `iter([...])` feeding `next(hids)`) is a one-command mechanical sweep that locates all six stubs
   (verified: the grep returns precisely those six sites); step 4 (state the invariant — an unbounded
   reqId source; exact-request-count / one-request-per-load / empty-cache-branch assertions change by
   design) is a decision procedure that generates the 14-function D16 set; step 2 is the diagnosis of
   *why* the seed set was wrong. The one soft edge: step 1 is manual unless paired with step 3's grep —
   which is why step 3 is the load-bearing one, and it is stated as a rule ("correct **all** of them in
   one scoped task, before dispatch"). Judged **checkable**.
9. **`Frozen Interfaces` — PASS (a checklist addition, not a decision).** It freezes **only** `[existing]`
   read-only surfaces, and every contract is **verbatim** against the tree at `b48133d`: I re-read each
   one — `session_windows(start_ts: int, end_ts: int, ext_hours: bool) -> List[Dict[str, int]]`
   (`services/market_calendar.py:195`), `plan_requests(missing_spans: Iterable[MissingSpan], timeframe:
   str) -> List[RequestPlan]` (`services/backfill_service.py:459`), `MissingSpan` (`:91`) and
   `RequestPlan` (`:104`, five fields), `bar_period_seconds(timeframe: str) -> int` (`:117`),
   `@dataclass class Bar` with the eight fields (`data/models.py:4`–`:13`), `TIMEFRAME_CONFIG`
   (`ibkr/market_data.py:7`–`:14`, all six entries) and `popouts.ext_hours INTEGER NOT NULL DEFAULT 1`
   (`data/db.py:86`). Every owning module exists; there are **no duplicates**; and the section
   **explicitly excludes everything under construction this increment** (`find_missing_spans`,
   `BarCache.save_bars`/`get_bars`/`prune`, `ChartPanel.update_last_bar`,
   `CandlestickItem.set_data`/`_draw_candles`, `TickerSession.set_bars`/`_append_bar`, `bars`) — the
   right discrimination, since `services/backfill_service.py` is modified while four of its interfaces
   are frozen and one is not. It adds no decision.

## Validation steps (short form)
- **Coverage — PASS (unchanged).** No requirement, journey or `AC` is touched by the amendment; the
  D42 coverage map (`AC-D6.4`/`AC-D7.1`/`AC-D9.2` note → Phase 1; `AC-D16.8`/`AC-D16.9`/Journey 17 →
  Phase 2; `AC-D16.1`/`AC-D16.3`/`AC-D16.4`/`AC-D16.7` → Phases 2–3) is intact.
- **Completeness — PASS.** The amendment adds the six-suite set with its cause, the D16 completion
  (14 functions), the invariant and the rule, the `Frozen Interfaces` checklist, and cross-references
  in `S21`, `AR-D42-6`, the Codebase Summary, the Non-Functional test-fidelity bullet, the traceability
  table, the Phase-2 file map, Phase 3 and `AP-D42-9`.
- **Consistency — PASS.** No contradiction: the same six suites, the same 14 D16 functions, the same
  invariant and the same 19 figure appear in the plan and the architecture with one meaning; `ESC-050`
  is consistently *not* absorbed by `ESC-048` (BUILD) or by `ESC-041`/`ESC-037` (BUILD-owned).
- **Plan quality — PASS.** Still three coarse phases with goal / covered criteria / dependencies /
  deliverable; the amendment adds **no** task-level detail, no task graph and no per-task test spec.
- **Task Manager readiness — YES.** Nothing task-graph-shaping changed; the only rule the plan imposes
  (the two `ui/chart_panel.py` tasks in different waves) is Build's own `touches_files` rule.
- **Existing-repo compliance (step 7) — PASS (unchanged).** Marker sentence + Current Tech Stack
  preserved; the Codebase Summary is substantive and now also names the load-path-coupled suites;
  nothing existing is replaced; `[existing]` / `[new/changed]` labels are intact.
- **Frozen Interfaces (step 8) — PASS.** See verification 9: verbatim contracts, `[existing]` and
  unmodified only, owning modules resolve, no duplicates, nothing under construction frozen.
- **Codebase map (step 9) — N/A / observation.** `docs/codebase-map.md` **does not exist** and has
  never existed in this repo's pipeline (no prior cycle referenced it, including the D41 and D42
  cycle-1/2 approvals). Its role for D42 is filled by the § *Codebase Summary (D42 surface)* in
  `docs/architecture.md`, which is substantive, source-validated and re-verified this cycle. Recorded
  as a standing observation (observation 3) rather than a blocker: introducing the artifact now would
  be new scope on a completed, verified batch.

## Required Changes
**None.** All `ESC-050` items are addressed; every enumeration claim was re-verified against the tree
and the substantive set is complete and correct. The three residual items below are wording/citation
slips that require **no** architectural decision and were normalized **editorially** in the canonical
artifacts I own (they do not change any `S`-decision, `AC`, phase, task or test outcome).

## Non-blocking observations (recorded; no decision required)
1. **The proposal's decomposition arithmetic is off by one — normalized editorially.** Revision 3 says
   the D42 diff "changes **14 test functions** in the three D16 files — the **9** named, the **4**
   `ESC-050` records (`t40_t03`, `t40_t05`, `t43_t03`, `t44_t03`) and **2** found by Plan
   re-verification" (9+4+2 = 15, not 14) and repeats the same decomposition in the Revision-3
   disposition table. The **total (14) is correct** (verified exactly — see verification 6); the slip
   is that `t40_t05` is counted as changed when the diff shows **no hunk for it** — which the same
   document discloses three lines later. The canonical artifacts state the correct decomposition
   (**9 + 3 changed `ESC-050` sites + 2 re-verification adds = 14**, with `t40_t05` listed as
   **unchanged** and its correction located in `t40_t04`'s tail assertion), i.e. the concrete sets
   rather than a count — the same editorial normalization cycle 2 applied to the suite-count wording.
2. **Two line citations are wrong — corrected in the canonical artifacts.** The amendment cites
   `t39_t04` at `:269` and `t39_t05` at `:336`; neither matches either revision (at `b48133d` the two
   sites are `:286`–`:293` and `:363`/`:370`; on the live tree the functions start at `:318` and
   `:387`). The canonical artifacts carry the verified `b48133d` citations, and the D16 table states
   once that its citations are at the D42 baseline. The **substance** of both rows is correct
   (verification 5). Also noted: the proposal mixes citation conventions across the table (some
   `b48133d` change lines, some live-tree `def` lines) — the canonical table uses `b48133d` throughout.
3. **`docs/codebase-map.md` is still absent** (standing). Not created by this cycle — it is Plan-owned
   and would be new scope for a completed batch. D42's module index is the architecture Codebase
   Summary. Flagged so a future increment can decide whether to adopt the artifact.
4. **"assertions" vs "cases".** `ESC-050` and the proposal say "19 **assertions**"; the reproduced
   evidence is 19 **failing test cases** (pytest reports per-test failures, and my census of the six
   files matches the per-suite figures exactly). The canonical artifacts say "19 load-path-driving
   **cases**" — an editorial precision, not a change of set.

## Requirements Escalations
**None.** `ESC-050` is a plan-document enumeration defect, not a requirements gap: no requirement is
redefined, reinterpreted or left unsatisfied, and the fix is entirely inside the planning artifacts.
`docs/plan_notes.md` was **not modified** — no `RG-*` entry is warranted and no
`ESCALATED_TO_REQUIREMENTS` status was raised. `docs/code_review/escalations.json` was not edited.

## Task Manager Readiness
**Yes.** The task graph for D42 already exists and is built (26/26); the amendment changes no task, no
acceptance criterion and no `touches_files` entry. The canonical artifacts remain a valid basis for any
re-dispatch (e.g. `ESC-048`'s six stub widenings) without Task Manager inventing architecture.

## Artifacts written this cycle
- `docs/plan.md` — § *D42 — Batch 18b*: round-3 note; Phase 2 `ui/main_window.py` file-map row (the six
  suites); Phase 3 goal + deliverable; the D16 load-path table completed to all 14 changed functions
  with the `t40_t05` verification note; the new *Corrected — load-path-**driving** suites* table; the
  **invariant**; the **impact-analysis enumeration rule**; `AP-D42-9`; correction-record items 5 and 7;
  handoff. Ends `Status: READY_FOR_TASK_MANAGER`.
- `docs/architecture.md` — § *D42 increment*: `ESC-050` header note; Codebase Summary `tests/` row;
  `S21`; `AR-D42-6`; the Non-Functional test-fidelity bullet; the traceability table; the new
  § *Frozen Interfaces (D42 increment)*; handoff.
- `docs/plan_review.md` — this cycle-3 section.
- `docs/plan_notes.md` — **not modified** (no requirements or planning gap).

## Final Decision
Status: APPROVED (2026-10-16, D42 cycle 3 of 3 — the `ESC-050` amendment is verified **accurate and
complete in substance** against the live tree: the six load-path-*driving* suites are real
(fixed-size `req_historical_data` stubs), their counts sum to **19** (corroborated by `ESC-048`'s
reproduction and by my own census of the six files), the three further changed D16 sites are correctly
described, `t40_t05` is correctly disclosed as **unchanged** with its correction located in
`t40_t04`'s tail assertion (`b48133d:484`–`:485` — the amendment rightly contradicts `ESC-050`'s own
naming), the two Plan re-verification rows (`t39_t04` spies / `t39_t05` floor span) are real, all
**14** changed test functions in the three D16 files are now named, `AR-D42-6` no longer rests on an
exhaustiveness claim, the enumeration rule is checkable, and the new `Frozen Interfaces` section
freezes only `[existing]` read-only surfaces with **verbatim** contracts (all eight re-verified) while
explicitly excluding everything under construction. **No architectural decision, `AC`, phase or task
changed.** The amendment was **merged into** the existing canonical sections (§ *D42 — Batch 18b* and
§ *D42 increment*) — not appended as a new increment — with three wording/citation slips normalized
editorially and recorded above. `docs/plan_notes.md` unmodified; `docs/code_review/escalations.json`
untouched (`ESC-050` remains the Code Reviewer's to flip after its own re-verification). **Task Manager
may proceed; `docs/plan.md` ends `Status: READY_FOR_TASK_MANAGER`.**)
