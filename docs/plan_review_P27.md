# Plan Review — Phase P27 (D77–D83), planner / pacing / backfill hygiene

Plan-Section-SHA256: be386f6caba3d609cbf3de20a0967ee1c97122c1ef4ebc79756381c8ac0b544c
Architecture-Section-SHA256: 6236f9a822ac0a54f8239a4a3016d3995a38d9ff65b75d10fcb7f62f48d949cb

**Review Status:** `Status: CHANGES_REQUIRED`

- **Pass type:** first validation (`initial_validation`), invoked while P26's code review is
  still in flight (an open BUILD escalation, `ESC-129`, and its rework commit `bda354f` landed
  mid-review). The phase gate is therefore **closed** and **nothing was activated**: `docs/plan.md`
  § *Phase P27* still ends `Status: READY_FOR_VALIDATION`.
- **Not `PROVISIONAL`:** the full Validation Method was run and it does **not** pass — Required
  Change RC-1 below is a reproduced, PLAN-owned defect in a P27 deliverable, not a gate artifact.
- **Baseline drift (expected, covered):** Plan's stated baseline is `70b16f2`; HEAD is now
  `bda354f` (P26's `ESC-129` rework: an empty `generic_batch(0)` reservation reserves nothing
  and does not stamp; a batch of one admits its single send). That is exactly the
  "descendant carrying only P26 review fixes" `AP-P27-1` anticipates, and it does **not**
  disturb S-P27-4: `throttle`'s reservation branch is byte-identical at `bda354f`, `n ≥ 1`
  batches still consume one unit per send and stamp once at the `finally`, and no caller reads
  `throttle`'s (currently `None`) return.
- `docs/requirements/requirements.md` § *Phase P27* ends `Status: READY_FOR_PLAN` — ready.
- `plan_lint.py`: PASS (0 failures, 0 warnings), per the preamble; re-confirmed by inspection of
  the phase header / status line.
- `docs/pending_doc_sync.md`: absent (drained).

---

## 1. Validation Summary

The proposal is strong: four rules behind seven defects, a traceability table that covers every
AC and journey, verbatim frozen contracts that match the tree, labels and sizes inside the
standing boundaries, and three flagged issues raised deliberately rather than buried. Two of the
three flagged issues resolve in Plan's favour on inspection (FI-P27-2 removal branch;
FI-P27-3 band direction). One does not resolve in anyone's favour and is routed to Requirements
(FI-P27-1). One unreported defect was found by applying the plan's own edits and running the
plan's own exit-condition suites: the `present_days` half-open change makes the `1 day`
timeframe permanently "not present", so every load re-requests the whole daily history and the
AC-D16.4 shortfall report claims every day is short. That, plus a missing `[revises P17]`
supersession and one unquantified bound, is what keeps the phase from approval.

**Empirical check performed** (validator, not the worker's word): a worktree at `70b16f2` with
P27-01's three edits applied as written.

| Edits applied | Result on P27-01's declared exit-condition suites |
|---|---|
| all three (identity de-dup, zero-span guard, trailing `> 1.5p`, `present_days` half-open) | **2 FAILED** — `tests/test_history_backfill.py::test_t40_t04_chunked_multi_request_continuity[1 day-T40SPY]` and `[1 day-T40AAPL]` |
| identity de-dup + zero-span guard + trailing `> 1.5p` only (`present_days` left inclusive) | **133 passed**, 0 failed |
| `present_days` half-open alone reverted/restored | isolates the failure to the `present_days` edit alone (18/18 of that test's params pass without it) |

A/B on the presence predicate itself (10 consecutive trading days of cached daily bars,
timestamped as the tree's own daily fixtures do — 16:00 ET, `tests/test_history_backfill.py:111`):

| | `present_days(...)` | `find_missing_spans(...)` |
|---|---|---|
| today (inclusive close) | **10 of 10 days present** | **0 spans** — nothing to fetch |
| with P27-01 deliverable 2c | **0 of 10 days present** | **1 span covering all 10 days** — the whole history re-requested |

---

## 2. Requirements Coverage

| Requirement | Where the proposal treats it | Verdict |
|---|---|---|
| **D77 / AC-D77.1–3** | S-P27-1, *System Components* item 1, P27-01 deliverable 1 + suite cases (a)(b)(c)(g) | Covered. Identity key is exactly the tuple `req_historical_data` receives; first-occurrence-wins; detector untouched. |
| **D82 / AC-D82.1–2** | S-P27-2, deliverable 2 + cases (e)(f) | **Partly unsound** — the bar-level half-open rule and the one 1.5-period threshold are right and verified green; the `present_days` extension (deliverable 2c) is not required by D82 and breaks daily presence (RC-1). |
| **D83 / AC-D83.1** | S-P27-1 (`end_ts <= start_ts` guard, `max(1, …)` removed) | Covered; `ceil` of a positive span is already ≥ 1. |
| **D78 / AC-D78.1–3** | S-P27-3, P27-02 deliverables 1–3 + cases (a)–(f) | Covered; arithmetic verified reachable for every `wait_s` (see §3). Worst-case hold is bounded by the AC but is not quantified (RC-3). |
| **D79 / AC-D79.1** | S-P27-6, P27-03 deliverable 5 | Covered; zero callers verified repo-wide. |
| **D80 / AC-D80.1** | S-P27-5 (retirement branch) | Covered; the AC's `or`-branch is taken and its two-request measurable still holds literally (§3). |
| **D81 / AC-D81.1–2** | S-P27-4, P27-03 deliverables 1–3 | Covered; default path behaviour-identical verified (§3). |
| **Journey 71** | P27-01 cases (a)(b)(g) | Covered, except its postcondition's "union equals" clause (FI-P27-1 → Requirements). |
| **Journey 72** | P27-02 cases (a)–(f) | Covered; the "retry itself refused → fail open, no third attempt" edge is the code's existing `retrying=True` contract (verified `ui/ticker_session.py:1793-1797`). |
| **Journey 73** | P27-03 (d)(e) | Covered; the two refund edge cases become vacuous once the path is retired, which the retirement branch permits. |
| A230–A234, R170–R174, DG135 | traceability table; DG135 exists and says what the plan quotes | Covered. |
| Non-functional (offscreen only, no live gate) | *Non-Functional Approach*; AP-P27-8 | Covered; requirements declare no live gate. |

No requirement is weakened, reinterpreted or silently dropped. One requirement sentence is
unsatisfiable as written and is escalated, not "fixed" by architecture: **FI-P27-1** (§9).

**AC-D16.\* / D42.\* / D48.\* / D52.\* boundary:** the *declared* boundary holds for the
bar-level pass and the futures branches, but deliverable 2c changes `AC-D16.9`'s presence
predicate for the `1 day` timeframe while P27 declares those criteria not reopened — a second,
independent reason RC-1 must be resolved by Plan rather than re-baselined.

---

## 3. Architecture Findings

Architecture completeness: technology stack, components and responsibilities, relationships,
data model, integrations, frozen boundaries, non-functional approach, risks and relationship-
labelled decisions are all present; every decision carries a rationale and named alternatives;
no decision is left implicit. Consistency: no phase depends on architecture defined nowhere; no
component depends on an unavailable service; no new module, dependency, migration or settings
key (the two new constants live in `ui/ticker_session.py`, which the plan states).

**FI-P27-2 — D80 as a removal: sound, and not a P26 re-decision.** Verified independently:
`refund_historical_slot` has exactly one production reference (`ui/ticker_session.py:1040`),
`_history_req_issued` exactly one *reader* (that same branch) plus writes at `:995` (inside
`mark_history_request_issued`), clears at `:1043`/`:1312`, `discard` at `:1222`, and
`mark_history_request_issued` two call sites (`:1263`, `:1379`). **Nothing still depends on the
symbols:** the two test files Plan names (`tests/test_p7_w1_coalesce.py:202,213`,
`tests/test_d56_taxonomy_pacing.py:218,225,245`) are the **only** test references repo-wide, so
"exactly two re-baselined cases" is exact. **No invariant is lost:** P17's issue-time silence
stamp inside `mark_history_request_issued` (`:997`) is duplicated microseconds earlier by
`_register_history_request` (`:977`), and the two mark call sites sit immediately after
registration (`:1375`→`:1379`; `:1261`→`:1263`), so no queued gap exists between register and
issue. That matters because *queued* plans are only registered when issued. The pre-issue
refund's own invariant ("a request that never crossed the wire holds no slot") becomes true by
construction once D81 is uniform, so retirement is stronger than repair, not weaker.
`AC-D80.1`'s measurable still holds literally: after cancelling a pre-issue and a post-issue id,
the slot count is unchanged (2), so "the other request's slot survives" is asserted, not waived.
`refund`'s "pops the newest" defect is unreachable in production today (`:1039` guards on
`_history_req_issued`, which every issued id is in) — latent, as the requirement itself says.

**FI-P27-1 — AC-D77.1's "union equals": faithful reading, wrong requirement.** Verified
numerically on the unmodified tree: `plan_requests([MissingSpan(0, 3*86400)], "5 mins")` returns
one plan of duration `"30 D"` — plan coverage 30 days for a 3-day span (§1 A/B). Literal
equality is therefore false *before* P27, cannot be produced without truncating the oldest chunk
(a chunking model P27's Non-Goals and the frozen `TIMEFRAME_CONFIG` exclude), and the prose the
plan does assert (D77 *Expected behaviour*, P27 *Constraints*) is satisfiable and is what the
suite asserts. This is a criterion bending to nothing — the criterion is simply false; routed to
Requirements (`RG-P27-1`), not treated as an architecture finding.

**FI-P27-3 — trailing band (1.5p, 2p): inside D82's mandate, quantified.**
Old rule `bound - (last + period) >= period` ≡ `bound - last >= 2p`; new rule
`bound - last > 1.5p`. Newly reported band: **(1.5p, 2p)** only — exactly 1.5p and exactly 2p
are unchanged. Cost: `session_windows` emits **one window per ET trading day**
(`services/market_calendar.py:209-215`), and the trailing span is < 2 periods, which is far
below every configured chunk duration (`30 D` = 2 592 000 s for the finest timeframe), so the
chunk count is exactly **1 extra request per affected day-load**, and only on days whose
trailing hole falls in that half-period band. It does not conflict with D77's goal: D77 removes
*duplicate* requests (saving ≥ 1 request in the reported common case), D82 adds coverage at one
window edge — and D82's own *Expected behaviour* mandates the single 1.5-period threshold
("the trailing edge uses the same 1.5-period threshold as the leading and internal edges"), with
R171's opposite worry explicitly not arising. Not scope creep; correctly flagged.

**D78 arithmetic — retry reachable for every `wait_s`, no loop, fail-open preserved.** Against the
real code: `retry_ms = max(1000, int(wait_s*1000))` is computed once and drives both the
`QTimer.singleShot` (`:1833-1835`) and `_prime_backstop_ms(retry_ms) = max(15_000, retry_ms +
1_000)`. Since `retry_ms + 1_000 > retry_ms` and `15_000 > retry_ms` whenever `retry_ms < 15_000`,
the backstop is **strictly later than the retry for every `wait_s`** — including `wait = 15 s`
(16 000 ms) and `wait < 14 s` (15 000 ms, today's value preserved). A retry that is itself
refused returns `False` from the `retrying=True` branch (`:1793-1797`) and `_on_prime_retry`
fails open once (`:1901-1902`) — **no retry-of-retry, no loop**. Fail-open is preserved:
`_on_prime_timeout` is untouched and still attaches exactly once; on a successful retry the
issued-prime bound is re-armed at the flat 15 000 ms (`:1847`). **Worst-case hold:** refusal →
attach ≤ `retry_ms + 15 s` (retry issues, prime never answers) = `wait + 15 s`; with the
historical wait ceiling (`MAX_HISTORICAL_PER_600S` window) that is **≈ 615 s of no live feed**
where today the backstop attaches at 15 s. `AC-D78.3` sanctions a bound of "reported wait plus
the backstop", so this is inside the requirement — but the architecture quantifies only the
40 s → 41 s example (RC-3).

**S-P27-7 — one wave for D77/D82/D83: genuinely one family, but the bundle hid RC-1.** All three
land in `services/backfill_service.py`'s pure planner functions, with overlapping fixtures
(the out-of-mode cache exercises identity and membership). `plan_requests` stays pure: its
imports are `math`, `dataclasses`, `datetime`, `typing`, `zoneinfo`, `config.settings`,
`data.bar_aggregator`, `ibkr.market_data` (for `TIMEFRAME_CONFIG`), `services.market_calendar` —
no DB, no clock, no Qt. De-duplication cannot change *which* data is fetched: the key is exactly
the request tuple the wire receives, so a dropped plan is byte-identical to a kept one; verified
empirically (all 133 exit-condition tests green with de-duplication applied, including the
chunk-continuity and planner-probe suites). The bundling is defensible; the cost is that one
deliverable's failure reddens a single aggregate exit condition, which is how RC-1 escaped
notice. RC-1's fix should give the presence rule its own assertion.

**D81 — `throttle(*, stamp=False)` split: default path behaviour-identical, refusal stamps
nothing.** Verified in `ibkr/pacing.py:135-159`: the reservation branch is untouched and returns
before the gate; the gate path raises before any stamp; `record_request_slot()` is exactly
"stamp `_last_req_time` after a send" (`:63-71`). `stamp=True` therefore reproduces today's
behaviour and today's `PacingExceeded` shape (`tests/test_d28_pacing.py:219-226`,
`test_throttle_success_stamps_interval_gate`), and no caller reads the return (repo-wide grep:
zero). Inside `generic_batch(n ≥ 1)` the caller skips the post-send stamp, so `_last_req_time`
stays untouched for the burst and the `finally` stamps once (`:94-131`) — the P26 contract.
`stamp=False` raises **before** `id_manager.get_id()`, so a refused throttle consumes neither a
stamp nor an id — AC-D81.2's no-gap condition, on the refusal path as well as the raise path.
Only two test doubles define `throttle` (`tests/test_d65_option_chain.py:108`,
`tests/test_ibkr_contract_details_d22.py:114`) — Plan's count is exact.

**D79 — `get_last_timestamp` deletion: endorsed.** Repo-wide grep (excluding `.venv`) returns
exactly one hit: the definition itself (`data/bar_cache.py:75`). Zero production callers, zero
test callers, zero probe scripts. `Optional` is used only by that signature (lines 3 and 75), so
the import removal Plan states is correct.

---

## 4. Plan Findings

**RC-1 (blocking, reproduced): `present_days` half-open membership breaks the `1 day`
timeframe.** P27-01 deliverable 2c changes the equity presence predicate from
`window_start <= ts <= window_end` to `window_start <= ts < window_end`
(`services/backfill_service.py:250`). Daily bars in this tree are stamped at the session **close**
— 16:00 ET, the RTH window end (`tests/test_history_backfill.py:110-112`, the fixture the whole
load-path continuity suite drives). Half-open membership therefore puts every cached daily bar
*outside* every window: `present_days` returns the empty set (§1 A/B: 10 of 10 → 0 of 10), the
day-presence pass reports **every** day missing, and the planner re-requests the entire daily
history on every load (bounded only by `per_load_historical_cap()` = 25 and the 30-session
floor). Consequences: (i) P27-01's own exit condition — "`tests/test_history_backfill.py` …
green, **unchanged**" — reddens on exactly the two `1 day` params; (ii) it is the
**over-requesting** direction D82's own note forbids ("over-requesting is budget waste"), the
inverse of D77's goal; (iii) `MainWindow._missing_backfill_trading_days` reads the same function,
so the AC-D16.4 shortfall line would claim every daily session is short every time — i.e.
`AC-D16.9`'s presence predicate is changed while P27 declares `AC-D16.*` not reopened; (iv)
AR-P27-2's mitigation ("the day becomes a presence span") is self-defeating once the presence
predicate itself is half-open. `tests/test_d42_day_presence.py` does not catch it (its fixtures
use intraday start-stamps), which is why the aggregate exit condition is the only witness.
**Not resolvable by re-baselining** (AP-P27-4 forbids it, and §2's boundary forbids it). Plan
must choose the resolution — e.g. keep `present_days` inclusive at the window end and confine
D82's half-open rule to `_bar_level_missing_spans`; or make presence period-aware
(`ts - period` as the bar's coverage start); or scope the half-open rule to timeframes whose
bars are period-start-stamped. Any choice must keep AC-D77.1/AC-D82.\*/AC-D16.9 satisfied and
`test_history_backfill.py` green unchanged, with its own assertion for the presence rule.

**RC-2 (traceability): P27 deletes an interface frozen by P17 and declares no `[revises P17]`.**
`mark_history_request_issued` is frozen in **two** earlier frozen lists — P26's
(`docs/architecture.md:10883`) *and* P17's (`:7691-7693`, "Seam unchanged; the retry path relies
on it for both the cancelled and the re-issued reqId"). Plan labels `[revises P26: …]` and
`[revises P7-W1: S-P7-2's pre-issue refund is retired]`, but not P17, and P17's entry would
continue to read as a live contract for a symbol the phase deletes — the exact defect class this
repo's own convention names (S-P24-6 / DG127: "a canonical doc sentence superseded without a
marker is a defect"). `refund_historical_slot` is likewise frozen in P26's list (`:10862`) and
covered only by the P7-W1 label. Plan should declare the P17 supersession and annotate the
earlier entries (P17's and P26's) as superseded; the activation step then verifies the markers.

**RC-3 (quantification): D78's worst-case hold is not stated.** S-P27-3 / AR-P27-4 quantify a
40 s wait (→ 41 s). The binding case is the wait **ceiling**: the historical wait is the 600 s
rolling window, so `retry_ms ≈ 600 s`, the deferral backstop arms at ≈ 601 s, and the chart
carries no live feed for ≈ 615 s (retry issues, prime never answers) where today it fails open
at 15 s. That is inside `AC-D78.3`'s "reported wait plus the backstop", but a reader of the
phase will read 41 s, and the requirement's Constraints say the backstop "must not be lengthened
into a new stall". State the worst case numerically, name the ceiling it derives from, and say
why it is the sanctioned branch (a retry that can deliver the forming bar, bounded, vs. today's
dead retry) — or cap the deferral if Plan judges 10 minutes unacceptable. No constant is
retuned either way.

**Editorial (I will normalise at activation; not Required Changes):**
- `docs/architecture.md:11079` says the deleted ledger spans "8 sites" while *System Components*
  (`:11150-11151`) says "six remaining sites"; the enumeration in `plan.md` P27-03 deliverable 4
  is the authoritative list.
- *System Components* writes the `now`-cap test as `bound < we`; `plan.md` writes `now_ts < we`.
  Equivalent (`bound = min(we, now_ts)`), but one form should be kept.
- S-P27-4's "the batch's `finally` still stamps once" now needs the qualifier `n ≥ 1`: at
  `bda354f` an empty `generic_batch(0)` deliberately stamps nothing (ESC-129). AP-P27-1 already
  says to re-read the batch; fold the qualifier in so the worker does not assert the old shape.

---

## 5. Existing Repo Compliance (existing-repository run)

| Check | Result |
|---|---|
| Codebase Summary present and substantive (data models, components, integrations) | **PASS** — site-by-site table with what each site encodes today and its P27 disposition, pointing at `docs/codebase-map.md`; every `[existing]` claim matched the tree. |
| Existing stack respected; nothing replaced or deprecated | **PASS** — constrained choices listed first (Python/`.venv`, `ibapi`, `PacingManager`, SQLite `BarCache`, pytest offscreen); no replacement; no new dependency. |
| `[existing]` / `[new]` / `[new/changed]` labels on Components, Data Model, Integration Points | **PASS** — every row/item labelled; test suites marked `[new]`. |
| Additive-only; new/changed work separated from what exists | **PASS** — six existing files edited in place, four new test suites, three deletions all declared and flagged (`FI-P27-2`). |
| Codebase Summary consistent with the proposal | **PASS** — components treated `[existing]` all appear in the summary. |
| Current Tech Stack unchanged in `requirements.md` | **PASS** — no requirement edit proposed; the fence suite pins it. |

---

## 6. Frozen Interfaces

| Check | Result |
|---|---|
| Verbatim contracts (signature/shape, not prose) | **PASS** — spot-checked against the tree: `find_missing_spans`, `plan_requests`, `present_days`, `bar_period_seconds`, `floor_bar_budget`, `MissingSpan`/`RequestPlan` fields, `TRAILING_BAR_GRANULARITY_DAYS = 5`, `TIMEFRAME_CONFIG`'s nine rows, `req_historical_data`/`req_mkt_data`/`req_contract_details`/`req_sec_def_opt_params`/`req_matching_symbols`/the three cancels, every pacing member, `IdManager.set_next_valid_id`/`get_id`, `BarCache.save_bars`/`get_bars`/`prune`/`RETENTION_BARS`, the fourteen `ticker_session` members, `session_windows`/`first_session_open`, `_missing_backfill_trading_days`, and the five settings values — all match. |
| Nothing under construction is frozen | **PASS** — every entry is `[existing]` and unmodified; changed bodies/signatures are listed under **not frozen**, including `throttle`'s new parameter and every deleted symbol. |
| Nothing frozen is missing | **PASS** — every `[existing]` interface the phase consumes appears (planner, calendar, pacing, id manager, cache, session members, report). `_register_history_request`'s one-line `discard` deletion is recorded in the Data Model table rather than the frozen list, which is adequate. |
| Owning modules resolve (`docs/codebase-map.md`) | **PASS** — all named modules exist; no module is added or removed. |
| No duplicates | **PASS**. |

Note for activation: three earlier-phase frozen entries name contracts this phase retires
(`throttle`, `refund_historical_slot`, `mark_history_request_issued`); the P27 labels cover two
of the three places they are written and RC-2 covers the third.

---

## 7. Codebase Map

| Check | Result |
|---|---|
| Every module section resolves | **PASS** — no production module added/renamed/deleted by P27. |
| Key files exist | **PASS** — spot-checked the planner, pacing and cache rows against the tree. |
| No stale entries | **PASS** — nothing removed this phase; the P27 note declares the deletions as in-place edits. |
| Status labels current | **PASS** — the `P27 note` (2026-11-19) carries `[new in P27]`-equivalent wording for the changed sites and lists the four planned suites as "do not look for them yet". |
| Index-sized | **PASS (borderline)** — the P27 note is ~18 lines, in line with the P26 note. If RC-1 changes the presence decision, the note's "half-open session windows" phrase must be updated with it. |

---

## 8. Required Changes

**RC-1 — owner: PLAN.** `present_days`' equity membership must not become half-open as written
in P27-01 deliverable 2c (`docs/plan.md` P27-01 deliverable 2 step 2 final sentence;
`docs/architecture.md` *System Components* item 3, *Relationship to prior phases* "half-open
`[start, end)` in both `present_days` (equity branch) and `_bar_level_missing_spans`", S-P27-2,
*Non-Functional Approach* "No silent hole", and the `docs/codebase-map.md` P27 note). Reproduced:
daily bars are stamped at the 16:00 ET window end, so half-open presence reports **0 of 10**
cached days present and `find_missing_spans` returns one span covering all of them; this reddens
`tests/test_history_backfill.py::test_t40_t04_chunked_multi_request_continuity[1 day-T40SPY]`
and `[1 day-T40AAPL]`, which P27-01's exit condition requires green and unchanged, re-requests
the whole daily history every load, breaks the AC-D16.4 shortfall report, and constitutes a
bar-level over-fetch — the direction D82's own note forbids. Plan chooses the resolution (confine
the half-open rule to `_bar_level_missing_spans`; period-aware membership; or timeframe-scoped
application), keeps AC-D77.\*/AC-D82.\*/AC-D16.9 satisfied, keeps the 133 exit-condition tests
green unchanged, and gives the presence rule its own assertion so the failure cannot hide behind
an aggregate wave. Re-baselining the test is not a resolution (AP-P27-4; `AC-D16.*` not
reopened).

**RC-2 — owner: PLAN.** Declare and apply the P17 supersession: `mark_history_request_issued`
is frozen in P17's Frozen Interfaces (`docs/architecture.md:7691-7693`) as well as P26's
(`:10883`), and `refund_historical_slot` in P26's (`:10862`). Add the missing `[revises P17: …]`
label in `docs/architecture.md` § *Phase P27* § *Relationship to prior phases* (and, if Plan
prefers, name all three earlier frozen-list entries there), so the earlier entries can be
annotated as superseded at activation per the S-P24-6/DG127 convention. Deletion of the symbols
themselves is validated above and needs no change.

**RC-3 — owner: PLAN.** Quantify D78's worst-case hold in S-P27-3 and AR-P27-4: `retry_ms` at the
600 s historical-wait ceiling → deferral backstop ≈ 601 s → newest-case refusal-to-attach ≈ 615 s
(`wait + 15 s` when the retry issues and the prime never answers), against today's flat 15 s
fail-open; state that this is the `AC-D78.3` branch ("reported wait plus the backstop") rather
than a new stall, or state the cap Plan prefers. No pacing constant may be retuned.

---

## 9. Requirements Escalations

**FI-P27-1 → `RG-P27-1` (recorded in `docs/plan_notes.md`, `Status: ESCALATED_TO_REQUIREMENTS`).**
`AC-D77.1`'s "the union of the plans' covered intervals equals the union of the input spans"
(and Journey 71's identical postcondition) is unsatisfiable before and after P27: a plan covers
one configured duration ending at its anchor, so a span shorter than one duration over-fetches by
up to a full duration — measured: a 3-day span on `"5 mins"` becomes one `"30 D"` request. Exact
equality is only reachable with a chunking model P27's Non-Goals and its frozen
`TIMEFRAME_CONFIG` exclude. Suggested: reword to "unchanged by the change and containing every
input span", matching D77's *Expected behaviour* and P27's *Constraints*. Non-blocking for the
architecture — Plan's AP-P27-2 asserts the enforceable half — but the criterion cannot be
approved as written.

Note: one requirement sentence is stale rather than wrong and is recorded, not escalated —
`AC-D83.2` reads "`### D41`–`### D76`" while P27 itself adds D77–D83; the fence suite covers the
range plus P27's own entries, so the assertion is honest either way.

---

## 10. Task Manager Readiness

**No — not yet.** The architecture is complete and internally consistent, the frozen contracts
are verbatim and verified, and Task Manager could decompose P27-02/P27-03/P27-04 today. It could
**not** decompose P27-01 without making a new architectural decision: RC-1 leaves
"does `present_days` participate in the half-open rule, and how does a close-stamped daily bar
count?" open, and RC-2 leaves a frozen contract contradicting the phase's own deletions. Both are
Plan decisions, both are small, and neither reopens D1–P26 beyond the declared revisions.

---

## Final Decision

`Status: CHANGES_REQUIRED`

Task Manager may **not** proceed. Plan must revise RC-1, RC-2 and RC-3. Nothing was activated:
`docs/plan.md` § *Phase P27* remains `Status: READY_FOR_VALIDATION`, and on approval it will be
flipped directly to `READY_FOR_TASK_MANAGER` (this review's stamps cover the sections validated
here). The phase gate is still closed behind P26 (`ESC-129` rework), so the next pass will also
re-read the batch contract before finalising.
