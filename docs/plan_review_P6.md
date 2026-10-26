# Plan Review — Phase P6 (D47: chart stack migrates to Lightweight Charts)

> Pass type: full validation (gate open — P5 `REVIEW_COMPLETE` newer than the build terminal status; no provisional exists for P6).
> Proposal: `docs/plan.md` § *Phase P6* + `docs/architecture.md` § *Phase P6 — D47 increment* (both drafted 2026-10-26).
> Requirements: `docs/requirements/requirements.md` (`Status: READY_FOR_PLAN`; D47, Journey 40, `AC-D47.1`–`AC-D47.9`, A105–A112, R86–R92, DG88–DG96, Q60 answered-by-default YES, Q61–Q63 ANSWERED 2026-10-26).

**Status: APPROVED**

**Decision:** APPROVED — Task Manager may proceed. `docs/plan.md` § *Phase P6* now ends `Status: READY_FOR_TASK_MANAGER`.

- **Coverage:** every D47 item (`D47.1`–`D47.13`), Journey 40, A105–A112, R86–R92, DG88–DG96 and Q60–Q63 is traced to an architecture section (S51–S60) and a wave (P6-01→P6-13); D1–D46 frozen and re-affirmed, reopened only by the recorded Q60 density-cap supersession.
- **Completeness:** stack, components, responsibilities, relationships, data model, integrations, interfaces, security, performance, scalability, operational constraints and risks all addressed; every decision (S51–S60) carries rationale plus a rejected alternative and exactly one relationship label.
- **Consistency:** no contradictions; `S56 [revises D42: S13]` and `S59 [extends P5: end state]` classify cleanly; pyqtgraph-default-through-Phase-10 holds across every section.
- **Plan quality:** 13 waves (P6-01→P6-13) are ordered milestones with goals, coverage, dependencies and gates; one commit per wave; no task breakdown, no task graph, no per-task tests — Task Manager owns the T→task mapping and the 66-file classification per AP-P6-3.
- **Readiness:** Task Manager can build a task graph without inventing architecture — seam signatures, model contents, bridge envelope (`{v:1,ops:[]}`), cutover/removal gates and the spike fence are all explicit.
- **Existing-repo compliance:** marker sentence + Current Tech Stack intact in requirements; architecture tech-stack lists constrained choices first with the D47 row as extension; Codebase Summary substantive (5,135-line migration surface, untouched backend, not-yet-existing paths named); every component/entity/integration labelled `[existing]`/`[new]`/`[new/changed]`; additive-only, no P5 decision changed. Pass.
- **Frozen interfaces:** 9 rows, each with a verbatim signature verified against the tree (`req_historical_data`, `find_missing_spans`, `check_live_port` + tunables, `gap_is_non_trading`, `watchlist_max_width` + constants, `BarCache.save_bars`/`get_bars`, `RouterMode` + TR-1…TR-17, order-code absence, drawing/alarm persistence + Qt dialogs); all `[existing]` and unmodified by every P6 wave; owning modules resolve; no duplicates. Pass.
- **Map quality:** skeleton regenerated post-P5 (205 files); P6 rows carry `[new in P6]`/`[changed in P6]` with planned-but-not-landed paths named without backticks per the lint rule; P5-era statuses read as history per the stated rule; index-sized. Pass.
- **Doc sync:** `docs/pending_doc_sync.md` absent — nothing unapplied. Pass.

**Spot-checks executed against the tree (not claims):** all frozen-interface signatures resolve with matching parameters; `MAX_POPOUTS = 10`, `SESSION_BAR_CAP = 5000`, `MIN_INTRADAY_SESSIONS = 30` confirmed; `PopoutChartWindow(editable=False)` and `TickerSession.get_bars/set_bars/attach_view/s0_register*` confirmed; zero `ibkr.orders`/`order_status`/`open_order`/`exec_details` references in `ui/`+`ibkr/`; Q60 (density-cap retirement via T10 + DG94 restatement) / Q61 (measure-first, P6-01+P6-12) / Q62 (cap 10, P6-11) / Q63 (accept drift, no custom primitive, AP-P6-6) honoured; no-soak triple gate + separately-gated Phase 11 deletion intact; spike fenced by AP-P6-2; renderer-only boundary holds (no `ibkr/`/`db`/watchlist/dock edits; no CDN/npm; vendored v5.2.x + attribution). No open `routed_to: PLAN` escalations (ESC-050/063/066/069 all `addressed`).

**Required Changes:** none. **Requirements Escalations:** none.

**Task Manager Readiness:** ready — proceed to phase the P6-01→P6-13 waves.
