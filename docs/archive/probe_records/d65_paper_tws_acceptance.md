# D65 live-TWS read-only acceptance record (AC-D65.19, P23-T26)

Status: **PENDING — owner-run gate. No result recorded yet; every item below is unchecked.**
Build commit: `db21672` (`db216721b7f45f42cfb92d3f968de58093e238e9`) — the build tree this checklist describes.
Date (UTC): ____________________________________ — owner records the run date at sign-off.

**AC-D65.19 is OPEN.** This file is the checklist and the evidence container: the checkbox
results, the evidence fields, the line counts and the closing statement belong to the owner.
No automated suite and nothing in this build satisfies the criterion. Nothing on this page
may be read as a pass until the owner has checked the box and filled the evidence field.

_File-name note: the `d65_paper_tws_acceptance.md` path is retained so existing references
resolve. Its content describes AC-D65.19 as amended on 2026-11-18: the owner's live TWS,
read-only, on `127.0.0.1:7496`._

## Environment (owner's live TWS, 127.0.0.1:7496)

- **Venue:** the owner's **live TWS on `127.0.0.1:7496`** — the same endpoint the application
  is normally run against. There is no paper account and no alternate venue for this
  acceptance run; the checklist is written for the live session, and every step below is
  safe to perform there because the run is read-only by construction.
- **Read-only by construction.** The application holds **zero order code**:
  `placeOrder`, `cancelOrder`, `reqGlobalCancel` and every order-shaped call are absent from
  the tree, so the run cannot transmit an order even by mistake. The Option Spreads panel
  issues exactly three requests — `reqSecDefOptParams` (the chain skeleton), `reqMktData`
  (one line per displayed leg, plus at most one SPX spot line) and `cancelMktData` (releasing
  a line) — and nothing else.
- **The only cancel in the run is a market-data line.** `cancelMktData` cancels a quote
  subscription; it is not, and cannot be, an order cancel. Nothing in the checklist asks the
  owner to place, modify or cancel an order: the run is **observation-only**, and no step
  below requires any trading action of any kind. The Orders pane and the session log are
  read, never exercised.
- **Precedent:** the D48 and D52 probes (`d48_probe_record.md`, `d52_probe_record.md`) ran
  read-only against live TWS on `127.0.0.1:7496` — a live port, a requests-only client, and
  no orders. AC-D65.19 follows that shape: the live gateway, an observation-only checklist,
  and a recorded result.

## Method (live TWS, read-only, owner-run)

- Connect the application to the live TWS session on `127.0.0.1:7496` — one client session,
  the application's normal startup path; no throwaway scripts, no extra subscriptions beyond
  what the panel opens.
- Note TWS's own **market-data line count** *before* switching the Option Spreads panel ON
  (the baseline), *while* it is ON, and *after* switching it OFF. TWS displays this count
  in its data-connection/status area; write the three numbers into the table below.
- Work through the six items in the recorded order (1)–(6) and capture a screenshot for each
  numbered item where the evidence is visual.
- Every step is an observation. Nothing on this page asks the owner to place, modify or
  cancel an order; the only cancel the run performs is a `cancelMktData` market-data line,
  issued by the panel itself when it releases a leg or the spot line.
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
  below, and no option line lingers. OFF cancels market-data lines only (`cancelMktData`);
  no order is involved on this path.
  **Evidence:** _(empty — owner records the three line counts from the table and any lingering line)_

**Result:** PENDING

### (5) Forced disconnect marks values STALE and freezes the walk; reconnect replays and recovers

- [ ] **A forced disconnect marks the values `STALE` and freezes the walk**; **reconnect
  replays and recovers** (values refresh, the walk resumes, no duplicate lines left behind).
  Force the disconnect at the connection (stop TWS, or drop the socket) — an observation
  step, never a trading action.
  **Evidence:** _(empty — owner records how the disconnect was forced, what the display showed while down, and what recovery looked like)_

**Result:** PENDING

### (6) No order code is touched — zero orders, zero transmit

- [ ] **No order code is touched.** Collect and record all four pieces of evidence, all of
  them read-only observations:
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

_Recorded by Build Worker P23-T26 on 2026-11-18: checklist rewrite only, no result
fabricated. Every item remains PENDING; the phase gate stays open until this file carries a
filled sign-off or an explicit recorded waiver._
