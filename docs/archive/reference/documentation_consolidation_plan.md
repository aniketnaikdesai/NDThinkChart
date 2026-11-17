+# Documentation Consolidation and Update Plan

**Prepared:** 2026-10-28  
**Status:** Proposed plan only — no existing documentation changed by this plan.

> **Changesets 1–2 applied 2026-10-28 (Q-50; append-only, plan text above unedited):** authority/index +
> current-status fact sheet and P6 reconciliation landed in `docs/README.md` (new index),
> `docs/codebase-map.md` (as-built P6-T13 note), `docs/lwc_parity_matrix.md` (parity-vs-deletion separation,
> row 19 Retired), `docs/phase-changelog.md` (§ Phase P6 as-built entry), `docs/CHANGELOG.md` (index role +
> P6 pointer). **Not applied in this changeset:** the `docs/architecture.md` as-built T13 outcome subsection
> and the `docs/code_review/review_log_P6.md` dated addendum — both files reject worker edits (tool permission);
> their full texts ride in `docs/build/quick/results/Q-50.json` for the follow-up applier. Fact sheet behind
> the edits: chart-engine status from `ui/chart_view.py::create_chart_view` (LWC-only) +
> `docs/build/gate_P6_T13.md` (waived-not-satisfied preserved); connection from `config/settings.py`
> (`IBKR_HOST` 127.0.0.1 / `IBKR_PORT` 7496 / `IBKR_CLIENT_ID` 1, `LIVE_PORT` 7496 fail-fast,
> live-only); `AC-D16.8` restatement kept as open Analyst debt (S-P7-1 flagged, not rewritten).  
**Review scope:** 51 tracked Markdown/text files, plus current untracked review reports and the P8 review note. Generated build, distribution, cache, and graph reports are outside the canonical documentation set.

## 1. Purpose

Consolidate the project documentation so a developer or reviewer can quickly answer:

1. What does the application do today?
2. Which chart engine and data paths are active?
3. Which document is authoritative for requirements, architecture, implementation sequence, and as-built history?
4. Which files are historical records and should not guide current work?

This plan targets accuracy and discoverability. It does not propose deleting useful audit evidence just to reduce file count.

## 2. Current quality diagnosis

The documentation has strong engineering detail, decision traceability, acceptance criteria, and investigation evidence. Its main weaknesses are:

- User-facing setup guides describe a pyqtgraph-default, two-engine application, while the current chart factory and P6 records say P6-T13 removed pyqtgraph and the factory always creates the Lightweight Charts view.
- P6 state is inconsistent across the architecture, codebase map, parity matrix, P6 review log, and user guides. The live-session deletion gate is described variously as still required, waived, or satisfied.
- The P7 quarter-budget cap is stated as a request limit but not clearly as an upper bound. It should say that a one-request load makes one request; the cap does not force chunking, extra requests, or waiting to spend reserved capacity.
- The LWC spike is explicitly a call-shape stub, but some records describe it as proving v5 API behavior. Its use of legacy names such as addCandlestickSeries must not be represented as validation against the vendored v5.2.1 runtime.
- Very large cumulative files mix current decisions with history. They are comprehensive but difficult to navigate and easy to misread.
- Several top-level files duplicate content without a clear canonical-versus-summary rule.
- Some review records declare documentation consistent even when source and other status records disagree.

## 3. Authority model to establish

Add a short documentation index at docs/README.md that states this precedence explicitly:

| Question | Authoritative document | Supporting records |
|---|---|---|
| Required product behavior and acceptance criteria | docs/requirements/requirements.md | design_gaps.md and open_questions.md track gaps and unresolved questions |
| Current system design and as-built technical state | docs/architecture.md | docs/codebase-map.md is only a navigation index; source code resolves implementation disagreements |
| Approved and proposed work sequencing | docs/plan.md | Phase reviews and task-manager notes are decision/decomposition records |
| What actually shipped and when | docs/phase-changelog.md | docs/CHANGELOG.md should be a short index or be retired after reference checks |
| Current review findings | Current phase review and open escalation ledger | Older review logs and investigations are historical evidence |
| How to install and use the current application | One canonical user guide | Any second guide is a short pointer or generated equivalent |
| Third-party licence/attribution | chart_assets/lwc/ATTRIBUTION.md | Vendored library licence header |

Global rules for the index:

- “Current” means behavior in the checked-out source plus the newest accepted as-built record.
- Proposal/review approval does not mean code was built. Distinguish DRAFT, APPROVED FOR BUILD, BUILT, REMOVED, and WAIVED.
- A waived gate is not a satisfied gate. Preserve that distinction wherever the P6-T13 outcome appears.
- Historical documents remain available for audit but are not current instructions.
- Generated graphs, build packs, worker logs, and memory notes are not sole authorities for product contracts.

## 4. Detailed execution plan

### Phase 0 — Preserve working state and establish inventory

1. Record the existing working tree state before edits. The checkout already has modified canonical docs and untracked artifacts; do not reset, overwrite, or discard them.
2. Inventory tracked and untracked docs. Classify each as normative/current, user guidance, navigation, historical decision/review evidence, one-off diagnostic, or generated/vendored.
3. Search the repository for every filename and major heading that a proposed move, rename, replacement, or deletion affects. Include scripts, packaging, tests, and tooling that reads docs.
4. Do not delete files during this phase.

**Exit criteria:** an inventory and cross-reference map exist; pre-existing edits are preserved; no document is reclassified based only on its filename.

### Phase 1 — Resolve authoritative facts against source and decisions

Before editing prose, produce a fact sheet with one source citation per fact. Resolve at minimum:

1. **Chart-engine status**
   - Confirm P6-T13 removal in source and its commit/review/gate record.
   - State that the app currently uses Lightweight Charts only.
   - State whether NDT_CHART_ENGINE and persisted chart/engine values are ignored, accepted as compatibility settings, or affect behavior. Use ui/chart_view.py as code authority.
   - Distinguish parity criteria accepted from live-session sign-off satisfied. Record the exact waived/retired decision.
2. **User connection instructions**
   - Verify host, port, client ID, live/paper account behavior, and hard port guard against config/settings.py and the connection path.
   - Resolve the live-versus-paper contradiction between USAGE.txt and usage.md.
3. **P7 budget semantics**
   - Define the cap as a maximum request count per load, not a target spend.
   - State explicitly: if one wide request satisfies the load, issue one request and return; do not split it merely to consume the cap.
   - State what happens only if multiple requests are needed: stop at the cap, persist completed chunks, leave remaining floor work for a later load, and retain capacity for other work.
   - Clarify whether the cap reserves capacity or spends it; it must not imply that the load automatically consumes one-quarter.
   - Link the clarification to the pending AC-D16.8 restatement/escalation.
4. **LWC spike evidence**
   - Label the Phase 0 artifact as a stub/call-shape check if that is all it executed.
   - Do not call it proof that the real v5.2.1 runtime accepts v5 APIs.
   - Keep real-runtime evidence separate: vendored version, API calls, actual host, and pixel/interaction evidence.
5. **Current P7/P8 workflow**
   - P7 is approved/ready for Task Manager; P8 has a separate approval record. Neither approval proves implementation.
   - Keep status dated and link each phase to its review, task graph, and as-built result when available.

**Exit criteria:** product and workflow facts are reconciled before summary or user-guide updates. Unresolved facts remain explicitly open rather than guessed.

### Phase 2 — Create navigation and standard status labels

1. Add docs/README.md with a one-sentence project status; links to canonical docs; a current-work block; a historical/do-not-use block; and ownership/update rules.
2. Add short metadata to current normative docs: role, status/as-of date, canonical yes/no, and supersedes/superseded-by links.
3. Keep metadata short; do not repeat large narratives in every file.
4. Make codebase-map.md describe current modules and link to rationale; remove contradictory status prose rather than appending another correction block.

**Exit criteria:** a new contributor can find the correct current document from docs/README.md without searching the repository.

### Phase 3 — Correct user-facing guides

1. Choose usage.md as the canonical full guide unless packaging/distribution requires USAGE.txt as primary.
2. Update from current code: one chart engine if source confirms P6-T13 final state; remove false opt-in/default instructions; clarify old NDT_CHART_ENGINE and QSettings behavior; correct paper/live and port guidance; refresh prerequisites, commands, packaging, database path, features, and limitations.
3. Make USAGE.txt a short plain-text quick start/pointer or generate it from the canonical guide. Do not maintain two independent full guides.
4. Remove or qualify “feature parity is complete” if parity records or known rendering defects contradict the claim.
5. Add an as-of date and link to troubleshooting/current status.

**Exit criteria:** launch/configuration instructions match source and agree across formats; no guide claims a removed engine is available.

### Phase 4 — Reconcile chart migration records (P6)

Update these together in one docs change set:

1. **docs/architecture.md:** add the as-built P6-T13 outcome and accurately state deletion-gate disposition. Separate planned design from delivered implementation.
2. **docs/codebase-map.md:** remove contradictory pyqtgraph-retained claims; update active engine, paths, counts, and deleted-file notes.
3. **docs/lwc_parity_matrix.md:** separate feature parity from cutover/deletion status. A row claiming the old engine remains present/default cannot stay accepted after deletion; state accepted, waived, or retired and link evidence.
4. **docs/code_review/review_log_P6.md:** append a dated addendum covering actual T13 outcome and gate record. Do not rewrite what the reviewer knew at the time.
5. **docs/phase-changelog.md:** add P6/T13 as-built outcome, commit, and gate disposition.
6. **docs/CHANGELOG.md:** add a concise P6/P7/P8 index or convert it to a pointer to phase-changelog.md.

**Exit criteria:** all records agree on the active engine, live-gate status, parity status, and location of decision evidence.

### Phase 5 — Clarify historical backfill plan (P7)

Update docs/plan.md, docs/architecture.md, docs/plan_review_P7.md, and docs/tasks/task_manager_notes_P7.md as a coordinated amendment/addendum:

1. State that the per-load cap is a maximum, never a target.
2. Add examples:
   - Need 1 request: issue 1; the cap does not create more work.
   - Need 10 requests with cap 25: issue at most 10.
   - Need 40 requests with cap 25: issue at most 25 in this load, persist progress, then continue later under the agreed resume/floor contract.
3. Define “per-load”: whether coalesced reloads share the allocation and how cancellation/refund applies to requests already sent to TWS.
4. Reconcile the 50-versus-100 rolling-budget figures against config/settings.py and relevant assertions without silently choosing a value in prose.
5. Append a delta note to the approved P7 review; preserve its original approval record.
6. Keep AC-D16.8 requirement status separate from the plan’s proposed satisfiable interpretation.

**Exit criteria:** a reader cannot interpret the cap as forced chunking, automatic consumption of reserved slots, or a promise of immediate full history.

### Phase 6 — Make cumulative specifications navigable

1. Keep requirements, architecture, and plan as canonical files initially for compatibility and traceability.
2. Add a short current-baseline section at the top linking current architecture, active phase, unresolved requirements, and as-built changelog.
3. Use consistent status metadata for each increment: status, commit, acceptance evidence, superseded decisions, and current relevance.
4. Move only self-contained completed history to docs/archive after verifying links and tooling references. Do not split active decisions from their requirements.
5. Replace repeated full summaries with cross-references; do not duplicate requirements in architecture or plan.
6. Run link/reference checks before moves/deletions.

**Exit criteria:** canonical docs retain stable identifiers and authority, while current state is visible near the top.

### Phase 7 — Classify duplicate, historical, and local docs

Use the disposition matrix below. Preserve audit records by default. A file is eligible for deletion only after its unique information is migrated or intentionally retired and all references are checked.

### Phase 8 — Final consistency review

Documentation-only checks; no product test run is required:

- Search for stale claims: pyqtgraph default, dual-engine selection, T13 not dispatched, live session still owed, parity complete, obsolete account/port instructions, and legacy LWC API names represented as runtime evidence.
- Check links, filenames, phase IDs, commits, statuses, and cross-references.
- Compare user guidance with source/configuration and plans with requirements/current phase state.
- Confirm proposals and old reviews are labeled historical.
- Append corrections to approval/gate records instead of rewriting history.
- Review the diff; preserve pre-existing user changes and change no source/test files.

**Acceptance criteria:** current-state contradictions are resolved; each current doc has a clear role/date; historical records are non-normative; P6 deletion and P7 cap semantics are unambiguous.

## 5. Document disposition matrix

### Keep authoritative/current, with targeted updates

| Document | Future role | Action |
|---|---|---|
| docs/requirements/requirements.md | Product behavior and acceptance criteria | Keep canonical; add a status index; explicitly track pending AC-D16.8 restatement. |
| docs/architecture.md | Current architecture plus increment history | Keep canonical; reconcile P6 as-built and P7/P8 states; reduce repeated narrative gradually. |
| docs/plan.md | Approved/current work sequencing | Keep canonical; clarify P7 cap; distinguish approved-for-build from built. |
| docs/codebase-map.md | Navigation index only | Keep; synchronize to actual tree; no design authority. |
| docs/phase-changelog.md | As-built chronological history | Keep; add missing phase outcomes and links. |
| docs/requirements/design_gaps.md | Design-gap ledger | Keep; make open/closed/superseded status visible and linked. |
| docs/requirements/open_questions.md | Owner question/answer history | Keep; surface open questions at top. |
| docs/plan_notes.md | Planning escalation/notes ledger | Keep; index open items and visibly close resolved items. |
| Active phase task-manager notes | Current decomposition guidance | Keep only for active/approved phase and label status prominently. |
| docs/plan_review_P7.md and docs/plan_review_P8.md | Approval evidence | Keep as decision records; append deltas rather than rewriting approvals. |
| chart_assets/lwc/ATTRIBUTION.md | Third-party attribution | Keep; already concise. |
| requirements.txt and requirements-dev.txt | Dependency manifests | Keep as configuration, not user-facing prose. |

### Keep but mark “HISTORICAL — DO NOT USE AS CURRENT GUIDANCE”

| Documents | Reason and action |
|---|---|
| docs/architecture_proposal.md and docs/plan_proposal.md | Preserve proposal lineage. Add banner linking canonical architecture.md / plan.md; optionally move to archive after link audit. |
| dev_docs/trading_app_architecture.txt, detailed_technical_spec.md, development_phases_tasks.md, ibkr_TOS_trading_terminal_implementation_plan.md, delta.md | Preserve original scope/design history. Mark legacy/superseded and link current requirements, architecture, plan. |
| docs/plan_review.md and older P5/P6 review files | Preserve phase decisions; index the newest relevant review and never imply old status is current. |
| docs/code_review/review_log.md and P4/P5/P6 logs | Preserve audit trail; current status belongs in latest review/escalation ledger. Add scope/date/superseding links. |
| docs/code_review investigation, permission, and audit files | Keep unique evidence; label time-bounded and require re-verification before reuse as current facts. |
| docs/lwc_spike_results.md and spikes/lwc/README.md | Keep Phase 0 history, but label stub call-shape checks separately from real v5.2.1 runtime proof. |
| docs/memory.md | Keep as non-normative project context; decisions must link to requirements/architecture. |
| docs/debug/debug_log.md | Keep if useful for incident history; mark resolved and link the current fix. |
| docs/thinkorswim-feature-gap-analysis.md and docs/ibkr-api-data-inventory.md | Keep dated research; revalidate market/API claims before design use. |
| docs/lwc_parity_matrix.md | Keep acceptance evidence; update deletion/cutover disposition and avoid claims contradicted by current source. |

### Replace with pointer or merge after reference audit

| Document(s) | Proposed treatment | Conditions |
|---|---|---|
| USAGE.txt and usage.md | Use usage.md as canonical full guide; make USAGE.txt a short text quick start/pointer or generated equivalent. | Check packaging, scripts, external references, and whether plain text is required. |
| docs/CHANGELOG.md | Make a short index to phase-changelog.md or merge unique P4/P5 entries and remove. | Check release tooling and references first. |
| DEAD_CODE_REVIEW.txt, TEST_SUITE_RUNTIME_REPORT.txt, DRAWING_RENDER_DEBUG_REPORT.txt | Archive under docs/archive/reviews with date/scope or delete after durable findings are integrated. | These are untracked snapshots; do not silently overwrite or treat as canonical. |

## 6. Conditional deletion candidates

No high-value tracked document should be deleted as the first cleanup action.

1. **USAGE.txt:** removable only if usage.md is canonical, no packaging/reference depends on it, and plain-text distribution is unnecessary. Safer default: replace with a pointer.
2. **docs/CHANGELOG.md:** removable only after unique entries are preserved and consumers are checked. Safer default: make it an index.
3. **Proposal docs:** deletion is not recommended; mark historical and optionally archive because they preserve decision lineage.
4. **dev_docs initial design set:** deletion is not recommended until unique context and references are checked; mark legacy first.
5. **Three untracked root review reports:** may be deleted after durable findings are integrated and the owner no longer needs the snapshots; otherwise archive with date and evidence basis.
6. **Generated build/dist/graphify/cache text:** outside canonical docs. Cleanup must follow build/ignore policy and must not remove user data.

## 7. “Do not read” policy

Avoid blanket labels that hide historical decisions. Use precise guidance:

- **Do not use as current guidance:** superseded proposals, old user guides, old codebase snapshots, old phase reviews.
- **Read only for historical evidence:** investigations, review logs, spike records, and worker/build logs.
- **Current source of truth:** docs/README.md points to requirements, architecture, plan, current changelog, and active phase.
- **On conflict:** source code decides implementation facts; requirements decide intended behavior; unresolved disagreement is recorded as a gap, not inferred.

## 8. Suggested change-set boundaries

Keep integration reviewable with separate documentation-only changesets:

1. Authority/index and current-status fact sheet.
2. P6 reconciliation: architecture, map, parity, review addendum, changelog.
3. P7 wording clarification: plan, architecture, P7 review addendum, task-manager notes.
4. User guides and duplicate reduction.
5. Historical labels/archive moves after reference checks.
6. Final link and contradiction audit.

Each changeset should state the canonical facts it updates and avoid rewriting unrelated history. Do not mix source-code edits or test execution into this consolidation.

## 9. Completion checklist

- [ ] docs/README.md identifies canonical sources and active phase.
- [ ] User instructions match source, configuration, and supported account modes.
- [ ] P6-T13 is consistently recorded as removed, with waiver/live-session status accurate.
- [ ] P6 feature parity is not conflated with a defect-free live session.
- [ ] P7 per-load cap is explicitly a maximum, never forced chunking or a budget-spend target.
- [ ] The 50/100 request-budget discrepancy is resolved or explicitly left open with an owner/source.
- [ ] LWC spike claims distinguish stub checks from real v5.2.1 runtime evidence.
- [ ] docs/CHANGELOG.md and docs/phase-changelog.md have distinct roles or one is a pointer.
- [ ] Proposals, memory, reviews, and old phase docs are marked non-normative rather than silently deleted.
- [ ] Every moved/deleted path passes reference checks.
- [ ] Existing user edits and untracked files are preserved unless explicitly dispositioned.
- [ ] No product source/test files changed as part of this documentation-only integration.
