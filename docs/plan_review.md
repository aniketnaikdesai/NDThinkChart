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
