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
