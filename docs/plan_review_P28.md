# Plan Review — Phase P28 (D84–D95) — pass 3

Plan-Section-SHA256: dd530773cd56f81491174b9b5f3769a8d107259af36a90b08612493d711e7748
Architecture-Section-SHA256: 28d10ddc139266e133925608c66fd228afb75a12acd8d87efeb2db2fd7647b3b

**Review Status:** `Status: APPROVED`

- **Phase:** P28 — connection, startup and window lifecycle (D84–D95), Journeys 74–77,
  `AC-D84.1`–`AC-D95.3`, G5.
- **Pass type:** `retry_2_of_3` — targeted re-validation of the three PLAN-owned items from
  pass 2 (`RC-1b`, `RC-1c`, `RC-5b`). Revision notes were present
  (`docs/plan.md:8182-8185`), so scope was: each required change verified against the tree,
  then consistency ripple on the areas the revision touched (the `_on_disconnected` marking
  rule, the prime-clear call sites, S-P28-15's label and every row restating them). Not a
  full re-validation.
- **State validated:** `docs/plan.md` § P28 (8146–8379) `Status: READY_FOR_TASK_MANAGER`
  (flipped by this review — was `READY_FOR_VALIDATION`); `docs/architecture.md` § P28
  (11420–11708) with S-P28-1/S-P28-2/AR-P28-1/AR-P28-3/Data Model/Codebase Summary updated.
- **Phase gate: OPEN.** `docs/code_review/review_log_P27.md` ends `Status: REVIEW_COMPLETE`
  (mtime 23:08:16) after `docs/build/build_log.md`'s last terminal status (22:59:43);
  `docs/code_review/escalations.json` parses to **127 records, 0 open** (nothing
  `routed_to: PLAN`). P27 is closed at `ef04c5a`; the P28 baseline `0ff7964` and HEAD agree
  apart from the Plan's own two doc edits.
- `docs/requirements/requirements.md` § *Phase P28* ends `Status: READY_FOR_PLAN` and is
  **unchanged since the pass-2 review** (mtime 22:59:20 < the pass-2 review's 23:08:28), so
  there is no requirements drift to re-check.
- `plan_lint.py --phase P28`: **PASS**, 0 failures, 0 warnings (before and after activation).
- `docs/pending_doc_sync.md`: absent (drained).
- Evidence basis: every site below was re-read in the working tree at `ef04c5a` for the areas
  the revision touched. No cached claim was reused for the three items under review.

---

## 1. Required Changes — verdicts

| RC | Owner | Verdict | Evidence (re-proved this pass, not taken from the revision notes) |
|---|---|---|---|
| **RC-1b** — the drop must owe the attach | PLAN | **FIXED** | P28-02 deliverable 5 now marks before it clears, with the stated three-term condition (`docs/plan.md:8253-8265`); S-P28-2 carries it (`docs/architecture.md:11695`); AR-P28-3 (`:11681`), AR-P28-1 (`:11679`), the Data Model row (`:11628`), the Codebase Summary rows (`:11556-11558`), the Deferred-attach and Prime-lifetime decision rows (`:11592-11593`), AP-P28-2 (`docs/plan.md:8363`) and the `AC-D84.2` traceability row (`:8190`) now all describe that rule. Each term verified below; case (d) is rewritten as the drop → reconnect path with both negatives (`:8272`). |
| **RC-1c** — three full copies, `_fail_open_prime` named | PLAN | **FIXED** | The deliverable, the architecture rows and the fence assertion all say **three** copies and name `_fail_open_prime` (`5276`/`8253`, `11555`, `11608`, `11695`; fence at `8353`); case (c) asserts the helper call at all three sites via `inspect.getsource` (`:8272`); the Do-not is narrowed to "any other **full** copy" and exempts the two ingress handlers with a stated reason (`:8274`). Counts verified in the tree (below). |
| **RC-5b** — S-P28-15's label target | PLAN | **FIXED** | S-P28-15 now reads `[extends P25: the frozen ensure_rt_subscribed contract (architecture.md:10471) — signature and refcount unchanged, one branch added]` (`docs/architecture.md:11708`). `docs/architecture.md:10471` is the P25 section's `def ensure_rt_subscribed(self) -> int:` line (P25 header at `:10214`), and the label is the same `[extends P<m>: <component>]` form every other row uses. |

No item remains PLAN-owned. Nothing was added to the Required Changes list.

## 2. RC-1b — the drop-owes-the-attach rule, term by term

- **Term 2 is the gate's own predicate.** `_on_session_prime_complete` (`ui/main_window.py:3974-3980`)
  attaches only when `session.symbol == self._current_symbol` (`:3979`), and
  `_attach_live_feed_if_current` repeats the comparison (`:3420`). `self._current_symbol` is
  always uppercase (`load_chart` normalises at `:3052` before assigning at `:3229`) and
  `session.symbol` is the uppercase registry key (`get_or_create_session`, `:1095-1108`), so
  the planned comparison cannot misfire on case. A background session is therefore genuinely
  excluded, exactly as the rationale says.
- **Term 1 ("no live line") cannot miss a live line.** `_rt_req_id` is the session's only
  subscription handle: it is assigned only by `_subscribe_rt` (`ui/ticker_session.py:597-601`)
  and `_reissue_rt`, cleared only by `_unsubscribe_rt` (`:608-623`, which unregisters the
  routing entry, `sub_manager` and the manager line before nulling it), and `release_rt`
  reaches that clear only at zero holders (`:475-480`). A pop-out displaying the same symbol
  shares the same `TickerSession` (`ui/popout_window.py:371`), so its hold also keeps
  `_rt_req_id` non-None. There is no second "live" representation the predicate could miss;
  flagging such a session would indeed attach on a live line and add a second holder, which
  is what the term prevents.
- **Term 3 is the right three states.** The attach is reachable from exactly: the prime's end
  marker (`on_historical_data_end:1577-1582`), its error fail-open (`on_historical_error:1610-1632`),
  the backstop (`_on_prime_timeout` → `_on_session_prime_timeout` → `_on_session_prime_complete`),
  the deferred retry's failure (`_on_prime_retry:1885-1898` → `_fail_open_prime`), and the
  immediate attach in `load_chart:3376-3379`. The first two are covered by `_prime_req_id`,
  the backstop by `_prime_timer.isActive()` (single-shot `QTimer`, `:361-363`), and the
  deferred retry by `_prime_retry_pending` — and that last one really does reach the attach:
  `_on_prime_retry` clears the flag, re-enters `prime_aggregator(retrying=True)`, and on
  `False` calls `_fail_open_prime` (`:1893-1898`), which calls
  `self._host._on_session_prime_complete(self)`. A retry that *succeeds* instead leaves a
  prime reqId/backstop, i.e. the states terms 3 already names. `_prime_retry_pending` and
  `_prime_retry_args` are always set together when the retry is scheduled (`:1802-1803`), so
  the term cannot fire on a retry that would return early with no args.
- **The immediate-attach path adds no hole.** When `prime_aggregator` returns `False` the
  attach happens synchronously; if the gate refuses it sets the flag itself, and the drop's
  loop neither clears an existing flag nor needs to, which the deliverable states.
- **Placement is safe.** The new loop runs before the stranded-wave loop; nothing in
  `_finalize_stranded_history_wave` (`:2912-2950`) reads prime state, and
  `_clear_prime_state()` per session is the same helper a reload already uses.
- **Case (d) tests the true path, both negatives included.** Positive: flag set, prime
  cleared, no subscribe on the drop, then `_on_connected()` attaches exactly once (one
  subscribe, flag False, `_rt_holders` raised by one). Negative (i): a background session
  with an armed prime is not flagged, its prime still cleared. Negative (ii): a live line
  (`_rt_req_id` set) is not flagged; after `_on_connected` `_replay_subscriptions`
  (`:2093-2142` → `SubscriptionManager.replay_all`, `ibkr/subscription_manager.py:135-170`)
  re-issues it once through `_reissue_rt` and the deferred pass adds nothing —
  `_rt_holders` unchanged, one subscribe recorded. That is the real mechanism, not a
  pre-set flag.

## 3. RC-1c — the copy count is now accurate

- Full six-statement copies in the tree: `teardown` (`ui/ticker_session.py:510-519`),
  `prepare_load` (`:953-961`), `_fail_open_prime` (`:1858-1863`). Three, as stated; the other
  `_prime_timer.stop()` sites are not full copies (`on_historical_data_end:1577-1582` and
  `on_historical_error:1610-1617` clear `_prime_req_id`, `_prime_period_start`, the timer —
  three statements — and then route an answer; `_on_prime_timeout:1266-1274` clears three
  and delegates the rest to the host; `prime_aggregator:1838` releases the reservation only).
- The narrowed Do-not is honest: "any other **full** copy" leaves `_fail_open_prime` in the
  call-site set, exempts the two request transitions for the reason given, and does not
  require touching the partial clears. `_fail_open_prime` becoming the fourth call site
  keeps its `+= 1`, its warning and its `_on_session_prime_complete` — the helper only
  replaces the six statements above them, so no behaviour moves.
- Fence and case (c) pin the three call sites (`docs/plan.md:8353`, `:8272`), so a later
  worker cannot quietly leave one inline.

## 4. RC-5b — label target verified

`docs/architecture.md:10471` is `  \`def ensure_rt_subscribed(self) -> int:\` (refcounted;
returns the reqId; may raise \`PacingExceeded\`)` inside P25's Frozen Interfaces (header at
`:10214`). P28's own frozen entry (`:11652`) keeps the signature frozen and declares the
terminal branch under **Not frozen** (`:11663`), so the label and the freeze are consistent:
`[extends]` here means "same contract, one added branch".

## 5. No-regression checks

- **Four supersession targets still resolve as claimed:** `:5900-5902` (P7
  `RealtimeBarsManager`/`StreamHealth` — `subscribe` precondition, `replay_all` deletion,
  `EXHAUSTED`/`MAX_RETRY_ATTEMPTS`/`mark_exhausted`), `:2714` (P4 Teardown row, "Pop-outs are
  Qt children destroyed with the parent"), `:6953` (S-P13-6 / D49.6 second save),
  `:7523` (S-P16-2 / D55.4 guide phrasing). P4/D40 stays `[extends]` (`S-P28-8`).
- **Frozen Interfaces:** still all `[existing]`, nothing under construction frozen, owning
  modules resolve, no duplicate entries; the revision touched none of them. `subscribe`'s
  signature stays frozen with the body under **Not frozen**.
- **Scope envelope intact:** one new module (`config/instance_lock.py`); no new dependency
  (`QLockFile` is QtCore); no migration, no `UNIQUE` on `popouts` (FI-P28-3); no new settings
  key (S-P28-6 only makes the two existing env parses non-raising); no reconnect-policy
  change (AP-P28-10); sizes S/M only (S, M, M, M, M, M, S, S); G5 owner-run and never claimed
  (`:8216`, `:8305`, `:8356`, AP-P28-8).
- **RC-2 / RC-3 / RC-4 untouched:** deliverable 6's seventeen-suite seam, the two named
  re-baselines, P28-03 deliverable 6's terminal branch, and P28-04's `_discard_popout`
  (None-tolerant, both sites pre-binding `popout = None`, case (g)) are unchanged in this
  revision — the plan diff touches only deliverable 5, cases (c)/(d), the Do-not, the
  `AC-D84.2` traceability row, the fence assertion, AP-P28-2 and the pass-3 notes.
- **Existing-repo compliance / codebase map:** unchanged since pass 2 (both PASS then); the
  architecture's Codebase Summary, labels and `[new in P28]` map row stand, and
  `docs/codebase-map.md` was not touched by this revision.

## 6. Validation steps — status

| Step | Status | Basis |
|---|---|---|
| 1. Requirements coverage | PASS | `AC-D84.1`–`AC-D95.3`, Journeys 74–77, A235–A240, R175–R180 each map to a named wave and case; `AC-D84.2`'s postcondition is now delivered by code the plan specifies (RC-1b), and `AC-D90.3`'s reload branch by S-P28-15 (RC-5b). Requirements file unchanged since pass 2. |
| 2. Architecture completeness | PASS | All sections present; the revised rows (S-P28-1/-2, AR-P28-1/-3, Data Model, Codebase Summary, decision rows) carry rationale and alternatives for the new rule. |
| 3. Architecture consistency | PASS | The drop rule, the flag's two setters, AR-P28-3, the Data Model and AP-P28-2 agree; the copy count agrees across plan, architecture and the fence; S-P28-15 points at P25's row. No contradiction remains in this area. |
| 4. Plan quality | PASS | Eight coarse waves with goals, coverage, dependencies and exit conditions; no task-level breakdown; the revised case (d) is a scenario, not a task. |
| 5. Task Manager readiness | PASS | The missing rule (who sets the flag on a drop) is now stated; the three-term predicate, the call sites and the test are explicit, so no architectural decision is left to Task Manager. |
| 6. Scope integrity | PASS | No product scope added or removed; the D90 budget and D95 lock branch are the requirements' own delegated choices; flagged issues stay non-blocking. |
| 7. Existing repo compliance | PASS | Unchanged from pass 2 (Codebase Summary substantive, constrained stack first, labels complete, additive-only). |
| 8. Frozen interfaces | PASS | Unchanged from pass 2; the one label defect (RC-5b) is fixed; nothing `[new]` frozen. |
| 9. Codebase map | PASS | Unchanged; `config/instance_lock.py` row is `[new in P28]` and flagged planned. |
| 10. Pending doc sync | PASS | `docs/pending_doc_sync.md` absent. |

## 7. Build attention (non-blocking — no Plan change required)

- **Case (d)'s last clause.** "A second `_on_connected()` adds nothing" means the **deferred
  pass** adds nothing (the flag is false, no new hold). It cannot mean "no subscribe at
  all": a second connect runs `_replay_subscriptions` and re-issues the now-registered line
  (as the case's own negative (ii) states). Scope that assertion to the deferred pass /
  `_rt_holders`, not to the fake manager's total subscribe count.
- **Cited line ranges are one line short.** `teardown`'s six statements span `:510-519`
  (the plan says `:510-518`) and `prepare_load`'s span `:953-961` (the plan says `:953-960`);
  `_fail_open_prime`'s `:1858-1863` is exact. The instruction is by site name and case (c)
  asserts the helper call, so nothing depends on the ranges — noted so a worker reading the
  ranges literally does not stop on the final `_prime_reserved = False`.

## 8. Requirements Escalations

None. FI-P28-1/2/3 remain faithful readings of the requirements' own delegated choices.

## 9. Findings owned outside Plan

None.

## 10. Task Manager Readiness

**Yes.** A pack built from P28-02 now contains the rule that makes `_rt_attach_pending` true
after a drop, its exact three-term scope, the four call sites of `_clear_prime_state()` and a
case that fails if any of them is invented differently. No architectural decision is left to
Task Manager.

## 11. Activation

- `docs/plan.md` § P28's closing line flipped `READY_FOR_VALIDATION` → `READY_FOR_TASK_MANAGER`
  (line 8379). That flip is the whole activation; nothing was copied or regenerated.
- Cumulative updates verified as labelled: every `[new in P28]` / `[revises P…]` /
  `[extends P…]` row sits in the P28 section (or, for the four supersessions, is recorded for
  the earlier row at activation per the S-P24-6 marker convention), the Frozen Interfaces
  entries are present with verbatim contracts, and no restated settled content needed
  trimming.
- Header stamps above are the post-activation section hashes (the P27 precedent), so
  `pipeline_state.py` compares them against the current sections.

## 12. Final Decision

`Status: APPROVED`

All three Required Changes are resolved and verified against the tree, the revision's ripple
is internally consistent, and the phase-gate is open, so this is a final approval rather than
a provisional one. Task Manager may proceed.
