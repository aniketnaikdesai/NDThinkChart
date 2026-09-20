# Plan Notes

> Owned by the Plan Artifact Editor & Validator. The Requirements Analyst reads this
> file. Entries record requirements or planning gaps found during validation.

## RG-001 — D13/D14 Defect Register entries are missing from `requirements.md`

**Requirement/Journey:** D13 (watchlist resizable to 50% with persistence) and D14
(watchlist double-click loads chart); Journeys 14 and 15; `AC-D13.1`–`AC-D13.3` and
`AC-D14.1`–`AC-D14.3`.

**Problem:** `docs/requirements/requirements.md` contains the D13/D14 user journeys
(Journey 14 and Journey 15), but the **Defect Register has no `### D13` or `### D14`
block**. As a result the authoritative acceptance criteria (`AC-D13.1`–`AC-D13.3`,
`AC-D14.1`–`AC-D14.3`), the Q25–Q29 decisions, and the watchlist assumptions and
risks are absent. The Assumptions Log now reuses `A17` for D15 and the Risks table
reuses `R15` for D15, so the numbering also collides. The D13/D14 content was
present earlier (referenced by the canonical plan and architecture) and was lost in
a subsequent requirements rewrite.

**Why it cannot be satisfied as currently written:** `docs/plan.md` (Phase 4) and
`docs/architecture.md` cite `AC-D13.1`–`AC-D14.3` and the watchlist assumptions as
authoritative. Task Manager is required to link every task to a real acceptance
criterion; those criteria do not currently exist in the requirements document, so
Task Manager could not build valid D13/D14 tasks without inventing them — which
would violate the "no invented requirements" rule.

**Suggested Direction:** restore the D13 and D14 Defect Register blocks (Reported,
Observed, Decisions from Q25–Q29, `AC-D13.1`–`AC-D13.3` / `AC-D14.1`–`AC-D14.3`,
Edge Cases) into `docs/requirements/requirements.md` after D12 and before D15.
Restore the watchlist assumptions as `A17` (D13 width, Q25/Q26), `A18` (D14
double-click, Q27/Q28), `A19` (D14 no-op, Q29), and move the D15 assumption to
`A20`. Restore risks `R15`–`R17` (D13 crowding, D14 accidental reload, D13
floating-vs-docked) and renumber the D15 risk to `R18`. The substance is recoverable
from `docs/plan.md` Phase 4 and from this conversation's requirements history.

**Status:** addressed — resolved 2026-09-20. The Requirements Analyst restored the
D13 and D14 Defect Register blocks (`### D13`, `### D14`) with `AC-D13.1`–`AC-D13.3`
and `AC-D14.1`–`AC-D14.3`, restored the watchlist assumptions as `A17`–`A19`, moved
the D15 assumption to `A20`, and restored risks `R15`–`R17` (D15 risk now `R18`).
Validation re-run passes; the block is cleared.

**Escalation:** ESCALATED_TO_REQUIREMENTS — resolved 2026-09-20.
