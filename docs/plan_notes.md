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

---

## RG-002 — D8 nice-number family contradicts its own examples and fixtures

**Requirement/Journey:** D8 (`AC-D8.1`, `AC-D8.4`, `AC-D8.5`, D8 edge cases),
Journey 9; A24; ESC-003/ESC-008. Also blocks the Plan revision's Phase-1 Amendment A.

**Problem:** `AC-D8.1` defines the volume ceiling as "a 1/2/2.5/5×10^k value that is
`>= max_vol*1.1`". But the requirement's own examples and the retained regression
fixture assert values that are **not** in that family:
- `AC-D8.4` low-volume edge case: `nice_max(3_000) = 5000` (fine), but the D8 edge
  cases state "a max just below a boundary (e.g., 1.05M) rounds up to the next
  1/2/2.5/5×10^k value (`1.5M`)". `1.5M` is `1.5×10^6`, i.e. a `1.5` mantissa — it is
  **not** a 1/2/2.5/5×10^k value.
- `AC-D8.5` high-end example: "`10.5M → 15M`". `15M` is a `1.5` mantissa — likewise
  **not** a 1/2/2.5/5×10^k value.
- The remaining fixture `tests/test_volume_linear.py:61`
  (`_nice_volume_max(1_050_000) == 1_500_000`) encodes the same `1.5M` value.

**Why it cannot be satisfied as currently written:** Under the stated formula
(smallest `1/2/2.5/5×10^k` candidate `>= max_vol*1.1`), the answers are
`1.05M → 2.0M` and `10.5M → 20.0M`. No generator can return `1.5M`/`15M` for these
inputs while also being the smallest `{1,2,2.5,5}` candidate. The Plan revision
(`architecture_proposal.md` §3.2) repeats the contradictory set — its candidate list
omits the `2` mantissa (`…, 100, 250, 500, 1000, 2500, …`) while both proposals retain
the `1_050_000 → 1_500_000` fixture. Task Manager cannot write a D8 test that satisfies
`AC-D8.1` and `AC-D8.4`/`AC-D8.5` simultaneously without inventing the family.

**Suggested Direction:** Decide the canonical nice family explicitly:
- **Option A — strictly `{1, 2, 2.5, 5} × 10^k`:** correct `AC-D8.4`/`AC-D8.5` and the
  D8 edge cases (`1.05M → 2M`, `10.5M → 20M`), and the retained
  `1_050_000 → 1_500_000` fixture is updated (Build-owned). Re-check the `50M` case
  (`50M → 100M` under this family).
- **Option B — a family that includes `1.5`/`7.5`** (as the old fixed list did): state
  it explicitly in `AC-D8.1` (e.g. `1/1.5/2/2.5/5/7.5 × 10^k`) so `1.05M → 1.5M` and
  `10.5M → 15M` are valid, and reconcile the `50M` case (next `7.5`-family value is
  `75M`, which is *coarser* than the `60M` the requirement rejects — decide the rule).

Once Requirements fixes the family, Plan re-validates Phase-1 Amendment A against it.

**Status:** RESOLVED — 2026-09-27. The Requirements Analyst pinned the family to
**`1 / 1.5 / 2 / 2.5 / 5 / 7.5 × 10^k`** (`AC-D8.1`, A24), reproducing every confirmed
value (`750K`, `1.5M`); the `10K` floor is removed (smallest generated value **`100`**)
and the old list is retained only as a test fixture. Revision 2 of the Plan proposal
(`docs/architecture_proposal.md` §3.2/§3.4) now uses the one formula and agrees on every
example and fixture — including `1_050_000 → 1_500_000` and `50M → 75M`. Validation
pass 2 confirms **RC-1** is closed. Block cleared.

**Escalation:** ESCALATED_TO_REQUIREMENTS — resolved 2026-09-27 (folded into
`AC-D8.1`/`A24`).

---

## RG-003 — `ALARM_PLACING → ZOOMING` transition is unspecified (PA-R1)

**Requirement/Journey:** D3 (`AC-D3.7`, `AC-D3.8`), Journey 4; Plan assumption PA-R1.

**Problem:** The Plan revision makes `ChartMouseRouter` a single-valued `RouterMode`
state machine whose transition table must be total. The requirements decide
`DRAWING↔ZOOMING` (`AC-D3.7`, both directions) and `ZOOMING → ALARM_PLACING`
(`AC-D3.8`), but are silent on the corner **invoking the magnifier while alarm
placement mode is active** (`ALARM_PLACING → ZOOMING`). Plan derived TR-9 (exit alarm
mode and enter `ZOOMING`) and flagged it as PA-R1 because the table must be total to be
testable.

**Why it matters:** TR-9 encodes required runtime behaviour that will be tested; it
should be a confirmed requirement rather than a plan-level assumption, so no reader
mistakes an invented transition for settled intent.

**Suggested Direction:** Requirements Analyst confirms (or corrects) PA-R1: activating
the magnifier while `ALARM_PLACING` exits alarm mode and enters `ZOOMING`, consistent
with the "one mode at a time" precedent (`main_window._on_draw_tool_changed` unchecks
alarm). If confirmed, fold it into D3's transition semantics alongside `AC-D3.7`/
`AC-D3.8`.

**Status:** RESOLVED — 2026-09-27. The Requirements Analyst answered Q36 with **option
(b)** and recorded it as **`AC-D3.9`**: invoking the magnifier while `ALARM_PLACING` is
active is **REFUSED** — the router stays in `ALARM_PLACING`, the pending placement is
**not** cancelled, and a status-bar hint is shown (the `ALARM_PLACING + magnifier →
ALARM_PLACING` cell that makes the transition table total). This supersedes Plan's
derived TR-9 and **retires PA-R1**; revision 2 rewrites TR-9 accordingly. Validation
pass 2 confirms the cell is total and refuses zoom. Block cleared.

**Escalation:** ESCALATED_TO_REQUIREMENTS — resolved 2026-09-27 (folded into `AC-D3.9`).

---

## FI-D16-1 — AC-D16.1's per-bar cadence measurable cannot hold for illiquid symbols

**Requirement/Journey:** `AC-D16.1` (measurable clause), against Q39 / A30 ("any symbol");
D16, Journey 17; raised by Plan as Flagged Issue FI-D16-1.

**Problem:** `AC-D16.1`'s measurable clause requires that "the maximum inter-bar gap
**within** a trading session does not exceed one bar period", asserted parameterized over
all six timeframes and at least two symbols. IBKR omits bars for periods with no trades, so
a thinly traded symbol (or an empty pre-market period) legitimately has inter-bar gaps
larger than one bar period even with a complete, correct bar list. Asserting cadence for
"any symbol" against real illiquid data would fail on correct data and would push the fix
toward fabricating/interpolating bars — which `AC-D16.3` and `AC-D16.4` explicitly forbid.

**Why it cannot be satisfied as currently written:** taken literally over live illiquid
symbols, the cadence clause contradicts the requirement's own no-fabrication clauses
(`AC-D16.3`/`AC-D16.4`). However, the measurable procedure in `AC-D16.1` is explicitly an
**offscreen test with a seeded cache and a stubbed historical feed**, so the test controls
the bar series and cadence is assertable there.

**Resolution (accepted by Validator, 2026-10-02 — no Requirements escalation):** the
cadence assertion is applied to the **stubbed/liquid test scenarios** (the `SPY 5 mins`
repro and a liquid second symbol per timeframe), and for illiquid symbols the requirement is
satisfied by **session-presence** continuity (every trading session has ≥1 bar). The
mechanism stays symbol-generic (Q39). This keeps the fix honest and matches the defect
class. Carried into `docs/plan.md` as `PA-D16-7` and into `docs/architecture.md`
(detection granularity + risks).

**Status:** addressed — accepted interpretation; no escalation.

**Escalation:** none (satisfiable under `AC-D16.1`'s offscreen stubbed-feed measurable
clause).

---

## FI-D16-2 — "any symbol" vs an equity holiday calendar for instruments that trade US equity holidays

**Requirement/Journey:** Q39 / A30 ("any symbol"), `AC-D16.3` (holidays are closures);
D16, Journey 17; also `design_gaps.md` DG1 (open); raised by Plan as Flagged Issue FI-D16-2.

**Problem:** a calendar that treats a US equity holiday as non-trading is wrong for futures
(which trade some of those days), while a per-instrument calendar is not feasible from the
current contract model. One calendar cannot be simultaneously correct for equities and for
all futures. So the literal "any symbol" continuity guarantee cannot hold for every
instrument under a single equity calendar.

**Why it cannot be satisfied as currently written:** a single equity holiday calendar is
not simultaneously correct for equities and futures. But the requirement does not ask for
per-instrument session modelling; Q39/A30 asks that the **fix and its verification be
symbol-generic**, and D1 already accepted the equity-session model as the default for every
symbol (A7 / DG1 / `services/session_service.py`).

**Resolution (accepted by Validator, 2026-10-02 — no Requirements escalation):** D16's
continuity guarantee is scoped to the **accepted equity-session model** (the existing
DG1/A7/D1 default), which is a standing accepted decision, not a new one. The futures
caveat is recorded (PA-D16-3, architecture risk row, DG1 remains the tracked open design
gap). If truly symbol-generic per-instrument session handling is ever required, that is a
separate requirements change for the Requirements Analyst — it is not needed to satisfy
`AC-D16.1`–`AC-D16.6` for the reported defect and the accepted model.

**Status:** addressed — accepted interpretation; no escalation.

**Escalation:** none (satisfiable under the accepted equity-session default; futures caveat
recorded, DG1 retained).
