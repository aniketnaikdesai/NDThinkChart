# D65 paper-TWS acceptance record (AC-D65.19, P23-T14)

Status: **PENDING — owner-run gate. No result recorded yet; every item below is unchecked.**
Build commit: `4bb01e9` (`4bb01e9227d49a9806ef34820fa3106b9677d148`) — the build that produced this checklist.
Paper account: __________________________________ — owner records the paper TWS account the run was performed on (this build asserts none).
Date (UTC): ____________________________________ — owner records the run date at sign-off.

**AC-D65.19 is OPEN.** This file is the checklist and the evidence container: the checkbox
results, the evidence fields, the line counts and the closing statement belong to the owner.
No automated suite and nothing in this build satisfies the criterion. Nothing on this page
may be read as a pass until the owner has checked the box and filled the evidence field.

## Method (paper TWS only, owner-run)

- Paper TWS (or IB Gateway paper) on its **paper** port only — never the live port.
  One client session, the application's normal startup path; no throwaway scripts, no
  extra subscriptions beyond what the panel opens.
- Note TWS's own **market-data line count** *before* switching the spread panel ON
  (the baseline), *while* it is ON, and *after* switching it OFF. TWS displays this count
  in its data-connection/status area; write the three numbers into the table below.
- Work through the six items in the recorded order (1)–(6) and capture a screenshot for each
  numbered item where the evidence is visual.
- This run is observational. If the run exposes a code defect, **record it here and escalate
  it as a build finding** — do not patch code from this record, and do not mark the item
  passing on the strength of a later fix.

## Fixed numbers this run verifies

These are the phase's fixed numbers and must match the suites and the canonical documents
exactly; a run that sees different numbers has found a defect, not a variant.

- **Subscriptions while ON:** at most **16 option lines** plus at most **one spot line**
  = **at most 17** TWS market-data lines. After OFF the count must return to the pre-ON
  baseline.
- **Strike band half-width:** `h = max(0.05, one_tick)` — never narrower than one tick,
  with the `0.05` floor.
- **Displayed sign convention:** `ASK = long.ask - short.bid`; `BID = long.bid - short.ask`;
  `Delta/Gamma = long - short`. Delta/Gamma are **negative by design** for the displayed
  spread - a negative value is correct, not a defect.
- **Fixtures:** `7425/7445` and `7340/7320` — the pair layouts the suites use. The ladder
  read off TWS must reflect the same numbers.

## AC-D65.19 items (all PENDING)

### (1) Eight rows populate for today's SPXW expiry

- [ ] **Eight rows are populated for today's SPXW expiry.**
  **Evidence:** _(empty — owner records what was seen and where)_

**Result:** PENDING

### (2) Delta/Gamma arrive from model greeks

- [ ] **Delta and Gamma arrive from model greeks** (not blank, not stale, not a placeholder),
  displayed per the sign convention above - `Delta/Gamma = long - short`, negative by design.
  **Evidence:** _(empty — owner records the two values seen, the row(s) they appeared on, and where they came from)_

**Result:** PENDING

### (3) A Target change steps the ladder and re-reads the Target

- [ ] **Changing the Target steps the ladder and the Target is re-read**, i.e. the ladder
  re-centres on the new Target and the Target field shows the value that was entered
  (no silent revert, no drift).
  **Evidence:** _(empty — owner records the old Target, the new Target, the strikes before/after, and the re-read Target value)_

**Result:** PENDING

### (4) OFF cancels every option line

- [ ] **Switching the panel OFF cancels every option line**, verified against TWS's own
  line count — the after-OFF count returns to the pre-ON baseline recorded in the table
  below, and no option line lingers.
  **Evidence:** _(empty — owner records the three line counts from the table and any lingering line)_

**Result:** PENDING

### (5) Forced disconnect marks values STALE and freezes the walk; reconnect replays and recovers

- [ ] **A forced disconnect marks the values `STALE` and freezes the walk**; **reconnect
  replays and recovers** (values refresh, the walk resumes, no duplicate lines left behind).
  **Evidence:** _(empty — owner records how the disconnect was forced, what the display showed while down, and what recovery looked like)_

**Result:** PENDING

### (6) No order code is touched — zero orders, zero transmit

- [ ] **No order code is touched.** Collect and record all four pieces of evidence:
  - TWS **Orders** pane / trade log shows **zero order lines** for the whole session
    (empty before and after the run, no order row, no `Transmitted` status);
  - the application log for the session shows **no `placeOrder` / `cancelOrder` / transmit
    call** — record the log path and the matching line count (**0**);
  - the account's order count at sign-off equals the count recorded before the run;
  - a screenshot of the empty **Orders** pane, taken at sign-off.
  **Evidence:** _(empty — owner records the four items above: pane state, log path + grep count, before/after order count, screenshot file)_

**Result:** PENDING

## TWS market-data line count

TWS's own count, not the application's. Baseline is whatever TWS showed **before** the panel
was switched ON; the after-OFF count must equal it.

| Phase | Observed line count (owner) | Expectation |
|---|---|---|
| Before ON (baseline) | — | baseline `B` — record `B` here |
| While ON | — | at most 17 (at most 16 option lines + at most 1 spot line) |
| After OFF | — | returns to the pre-ON baseline `B` |

## Screenshots and notes

Attach or link each capture; keep the file names stable so the evidence is auditable.

| # | Capture | File / link |
|---|---|---|
| baseline | TWS line count before ON | — |
| (1) | eight populated rows, today's SPXW expiry | — |
| (2) | Delta/Gamma values | — |
| (3) | ladder after the Target change | — |
| while ON | TWS line count while ON | — |
| (4) | TWS line count after OFF | — |
| (5) | `STALE` state while disconnected | — |
| (5) | recovered state after reconnect | — |
| (6) | empty Orders pane at sign-off | — |

**Notes:** _(empty — owner records anything unexpected, including a suspected defect escalated as a build finding)_

## Closing statement

Fill exactly one outcome. A waiver is **not** a pass: if the gate is waived, AC-D65.19 stays
recorded as waived, not satisfied.

**Run date (UTC):** ____________________
**Owner (name / handle):** ____________________

- [ ] **ACCEPTED** — all six items checked, every evidence field filled, and the after-OFF
  line count equals the pre-ON baseline.
- [ ] **REJECTED** — item(s) failed; the failing item, its evidence and the escalated build
  finding are recorded above.
- [ ] **WAIVED** — the owner's explicit waiver, recorded verbatim with date and reason:
  ______________________________________________________________________________
  ______________________________________________________________________________

**Sign-off:** ____________________ (date: ______________)

---

_Recorded by Build Worker P23-T14 on 2026-11-17: docs only, no production or test code
edited, no result fabricated. The phase gate stays open until this file carries a filled
sign-off or an explicit recorded waiver._
