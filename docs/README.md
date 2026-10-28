# NDThinkChart — documentation index

> **Role:** navigation index. **Status:** current as of 2026-10-28. **Canonical:** yes (index only — it confers no product facts; on any disagreement the authoritative document in the table below wins, and source code wins over all prose for implementation facts).

**Project status (one line):** PyQt6 desktop trading terminal (live TWS 7496, SQLite) whose chart stack is **Lightweight Charts only** since P6-T13 (2026-10-27, removal commit `6e35b27`); active work is the P7 data-path batch and the P8 (D48) weekly/monthly timeframes.

## Authority table

| Question | Authoritative document | Supporting records |
|---|---|---|
| Required product behavior and acceptance criteria | `docs/requirements/requirements.md` | `design_gaps.md` and `open_questions.md` track gaps and unresolved questions |
| Current system design and as-built technical state | `docs/architecture.md` | `docs/codebase-map.md` is only a navigation index; source code resolves implementation disagreements |
| Approved and proposed work sequencing | `docs/plan.md` | Phase reviews and task-manager notes are decision/decomposition records |
| What actually shipped and when | `docs/phase-changelog.md` | `docs/CHANGELOG.md` is a short index pointing here (see its header) |
| Current review findings | Current phase review and open escalation ledger (`docs/code_review/escalations.json`) | Older review logs and investigations are historical evidence |
| How to install and use the current application | `usage.md` — the canonical full user guide (`USAGE.txt` is only its short pointer + quick start) | `docs/phase-changelog.md` records per-phase user-doc changes |
| Third-party licence/attribution | `chart_assets/lwc/ATTRIBUTION.md` | Vendored library licence header |

Global rules (binding on every doc edit):

- "Current" means behavior in the checked-out source plus the newest accepted as-built record.
- Proposal/review approval does not mean code was built. Distinguish DRAFT, APPROVED FOR BUILD, BUILT, REMOVED, and WAIVED.
- A waived gate is not a satisfied gate. The P6-T13 live-session sign-off is **waived, not satisfied** (`docs/build/gate_P6_T13.md`) — never write "gate satisfied".
- Historical documents remain available for audit but are not current instructions.
- Generated graphs, build packs, worker logs, and memory notes are not sole authorities for product contracts.

## Current work (as of 2026-10-28)

- **Chart engine:** Lightweight Charts only. `ui/chart_view.py::create_chart_view` always returns the LWC view; `NDT_CHART_ENGINE` / `QSettings chart/engine` are read by deployment tooling but no longer select a renderer. Evidence: `docs/build/gate_P6_T13.md`, `docs/lwc_parity_matrix.md` (P6-T13 as-built note), `docs/architecture.md` § Phase P6 (as-built T13 outcome).
- **P7 data-path batch:** historical backfill + streaming correctness (see `docs/plan.md` § Phase P7, `docs/architecture.md` § Phase P7).
- **P8 (D48):** `1 week` (2Y) and `1 month` (10Y) timeframes, drafted 2026-10-28 (see `docs/architecture.md` § Phase P8).
- **Open Analyst debt (not rewritten here):** the `AC-D16.8` restatement — per-load cap vs 30-session floor (see `docs/architecture.md` S-P7-1, `docs/tasks/task_manager_notes_P7.md` RG-P7-1, `docs/plan_notes.md` 2026-10-27 note). The plan's proposed satisfiable reading stays separate from the requirement until the Analyst restates it.

## Historical — do not use as current guidance

- `docs/architecture_proposal.md`, `docs/plan_proposal.md` — superseded proposal lineage; canonical docs are `docs/architecture.md` / `docs/plan.md`.
- `dev_docs/` initial design set — original scope/design history, superseded.
- Older phase reviews (`docs/plan_review.md`, P5 and earlier) and older code-review logs — decision evidence; the pre-T13 P6 review scope sentence ("T13 not dispatched") is superseded by the 2026-10-28 addendum in `docs/code_review/review_log_P6.md`.
- `docs/lwc_spike_results.md`, `spikes/lwc/` — Phase 0 history: stub/call-shape checks, not v5.2.1 runtime proof.
- P6-era "pyqtgraph retained and default" sentences in `docs/architecture.md` § Phase P6 and `docs/codebase-map.md` header — plan-time wording, superseded by the as-built T13 outcome records appended in place.

## Ownership / update rules

- This index is owned by the doc-consolidation changesets (`docs/documentation_consolidation_plan.md`, changesets 1–2 applied 2026-10-28); keep it short — link, don't duplicate.
- Corrections to approval/gate records go in dated addenda appended to the record, never as rewrites of what the reviewer knew at the time.
- No product source/test change rides a documentation edit.
