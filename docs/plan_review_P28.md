# Plan Review — Phase P28 (D84–D95) — pass 2

Plan-Section-SHA256: 91bd8378c23448c0378f63e67d7da4db78bc538e6460a15e41b775f8ac076264
Architecture-Section-SHA256: 85801886874898ffedbdf1647e31b2bdbdd9df83f58297bdf1009f50cc0c1c8b

- **Phase:** P28 — connection, startup and window lifecycle (D84–D95), Journeys 74–77, `AC-D84.1`–`AC-D95.3`, G5.
- **Pass type:** `retry_1_of_3` — targeted re-validation of the five `CHANGES_REQUIRED` items from pass 1. Revision notes were present (`docs/plan.md:8172-8178`), so the scope is: each required change verified against the tree, then consistency ripple on the areas the revision touched. Not a full re-validation.
- **State validated:** `docs/plan.md` § P28 (8146–8361) `Status: READY_FOR_VALIDATION`; `docs/architecture.md` § P28 (11420–11708) incl. the new S-P28-15. `plan_lint` PASS (0/0) per the preamble.
- **Evidence basis:** every site re-read in the working tree at HEAD `0ff7964` for the areas the revision touched; `verify_cache.py check --phase P28` was already `new`/`phase mismatch` for this surface in pass 1, and no cached claim was reused. P27's `REVIEW_COMPLETE` is the latest review log, so the phase gate remains open.

## 1. Review Status

`Status: CHANGES_REQUIRED`

Four of the five pass-1 items are resolved and verified. **RC-1 is only half resolved**: the extraction and the three call sites landed, but the deferred attach is still not set by the *drop* — so Journey 74's postcondition ("reconnect attaches once") and the plan's own case (d) cannot be produced by the specified code, and the architecture's AR-P28-3 now asserts a rule no deliverable states. Two small factual/label corrections ride along.

Three PLAN-owned items remain (one material, two editorial). No requirements escalation.

## 2. Validation Summary (per pass-1 item)

| Pass-1 item | Verdict | Evidence |
|---|---|---|
| RC-1 — `AC-D84.2` implementation | **PARTIAL** | The helper, the three call sites, the teardown flag clear and case (c) are specified and correct; the drop does not mark the invalidated load owed (see RC-A), and the "six statements exist twice" claim is wrong (RC-B). |
| RC-2 — attach-gate harness seam | **RESOLVED** | Seam is now the predicate the gate reads; seventeen suites enumerated correctly; the two dropped suites really do not reach the gate; `lambda: True` is a harness seam, not a hole (below). |
| RC-3 — `AC-D90.3` reload | **RESOLVED** | S-P28-15 + deliverable 6 sit on the real `ensure_rt_subscribed`; refcount and double-subscribe behaviour verified (below). |
| RC-4 — `_discard_popout` shape | **RESOLVED** | `None`-tolerant helper, both sites bind `popout = None` before the `try`, construction / `_ensure_restore_data_path` inside it, case (g) forces both shapes. |
| RC-5 — doc/label reconciliation | **RESOLVED except two targets** | (a)–(e) all applied; S-P28-15's `[extends P7: …]` points at the wrong frozen row (RC-C). |

## 3. Requirements Coverage

- `AC-D84.1`, `AC-D84.3`, `AC-D90.1`–`AC-D90.3`, `AC-D85.1`/`AC-D85.2`, `AC-D86.1`–`AC-D86.3`, `AC-D87.1`, `AC-D88.1`, `AC-D89.1`/`AC-D89.2`, `AC-D91.1`, `AC-D92.1`, `AC-D93.1`/`AC-D93.2`, `AC-D94.1`, `AC-D95.1`–`AC-D95.3` and Journeys 75–77 are delivered by a named wave and case.
- **`AC-D84.2`** is delivered as *clearing* (no timer survives, no post-drop attach). Its companion promise — Journey 74's "reconnect (the next step) attaches once, with an id allocated at that point" — is **not** delivered for the drop-during-prime case: `_clear_prime_state()` stops the backstop, so no refusal occurs during the outage, so `_rt_attach_pending` is never set, so `_on_connected` → `_attach_deferred_rt_feeds()` finds nothing (RC-A).
- `AC-D90.3`'s reload branch is now covered by S-P28-15 and is a genuine reset (`mark_subscribed(reset_backoff=True)` through `_subscribe_rt`), not a `resubscribe_rt` no-reset.

## 4. Architecture Findings

**Resolved / verified sound:**

- **RC-2 seam.** `_transport_ready()` reads `self.ib_client.api_ready`, which *is* the client's `_connected` (`ibkr/client.py:104-106`), and `MainWindow.ib_client` is a real `IBApiClient` (`ui/main_window.py:802`); every window suite leaves `_connected` False, so overriding the predicate (`win._transport_ready = lambda: True`) is the only seam that actually opens the gate. The two suites dropped from the inventory are correctly dropped: `test_d67_forming_candle`'s only window case loads no chart (`:572-590`, `get_or_create_session` + `_wall_now`), and `test_p7_w1_coalesce` patches `TickerSession.ensure_rt_subscribed` (`:121`) so the gate only skips the patch — it asserts no RT state. The fifteen real-window suites named all call `load_chart` and depend on the attach (`test_d24_popouts:39`, `test_d27_aggregator_priming:88`, `test_d27_phantom_alarms:89`, `test_d28_4_gate:65`, `test_d28_tick_burst_baseline:47`, `test_d27_reconnect:195-205`, `test_d68_hold_balance:78`, `test_p13_hold_fix:102-198`, `test_p13_restore:54`), or patch `rt_manager.subscribe` so the manager gate is bypassed and only the window gate remains.
  **Honesty of `lambda: True`:** it removes the gate from those cases by design, and it would also pass if the gate were deleted — but only those cases. The gate's existence is guarded by `tests/test_d84_d88_readiness.py` case (b), which sets the **real** predicate (`win._ibkr_connected` and `win.ib_client._connected`) and asserts zero subscribes; delete or neuter the gate and (b) reddens. So it is a seam, not a hole, provided case (b) is never weakened in the build — worth the Task Manager's attention because it is now the single guard.
- **RC-3 / S-P28-15.** Against the real `ensure_rt_subscribed` (`ui/ticker_session.py:465-473`): `_unsubscribe_rt()` clears `_rt_req_id` and unregisters routing/`sub_manager`; `_subscribe_rt(reset_backoff=True)` subscribes, re-registers and calls `mark_subscribed(True)` (`:597-616`), synchronously moving the state off EXHAUSTED. The branch sits before the existing `_rt_holders += 1`, so the caller's hold is preserved and the count is not reset. A second holder in the same tick sees a non-EXHAUSTED state and takes the plain `+= 1` path — one subscribe, no double. If the fresh subscribe raises `PacingExceeded`, nothing has been held and `_rt_req_id` is None, so the caller's existing deferral re-enters the ordinary path, which also resets (`reset_backoff` defaults True). `resubscribe_rt()`'s Fix-B `reset_backoff=False` is untouched, and the predicate is the terminal state rather than `retry_budget_spent`, so a FAILED stream mid-storm is not silently recovered.
- **RC-4.** `_discard_popout` is written to tolerate `None` and to report exactly once in both cases; `_open_popout`'s sequence (`ui/main_window.py:1224-1259`) and `_restore_popouts`' `try` (first statement `_ensure_restore_data_path`, `:1604`) are the two sites, and case (g) forces a constructor raise and a data-path raise.
- **RC-5.** One shorthand everywhere (`5/10/20/40/60/60 s`, plan `:8264`, `:8273`, `:8347`; architecture `:11508`, `:11626`, `:11669`); P28-01 is `[extends P4/D40]` (`plan.md:8233`); `DB_PATH` is an absolute temp **file** (`tmp_path / "p28_instance.sqlite3"`); `_transport_ready()` is scoped "for the realtime attach" and names the six direct readers.
- The four supersession targets still resolve and say what the plan claims: `architecture.md:5900-5902` (`RealtimeBarsManager`/`StreamHealth`, "the APIs do not change"), `:2714` ("Pop-outs are Qt children destroyed with the parent"), `:3321` (the D40 classification boundary — now correctly `[extends]`), S-P13-6 (`:6953`), D55.4 (`:7523`).
- Frozen Interfaces: unchanged in the areas the revision touched; `ensure_rt_subscribed`'s signature is frozen with its new branch declared under **Not frozen** (`:11652`, `:11663`), and no `[new]` interface is frozen. No new module beyond `config/instance_lock.py`, no dependency (`QLockFile` is QtCore), no migration, no settings key, no reconnect-policy change, sizes S/M, G5 owner-run and never claimed.

**Finding — the deferred-attach rule is contradicted inside the architecture (RC-A):**
`AR-P28-3` now claims "no state is cleared that a reconnect needs (**`_rt_attach_pending` is set before the clear**)" (`architecture.md:262`), and the Deferred-attach decision row says the flag is "set where the gate refuses" (`:173`); the Data Model row says the same (`:209`). The first statement is not true of any deliverable, and the other two say why not — the flag is only set by a refusal, and a drop with an outstanding prime never reaches `_attach_live_feed`.

**Finding — wrong frozen-row target (RC-C):** S-P28-15 carries `[extends P7: ensure_rt_subscribed's frozen signature, one added branch]` (`architecture.md:11708`), but `ensure_rt_subscribed`'s frozen contract is P25's (`architecture.md:10471`), not P7's RealtimeBarsManager/StreamHealth row (`:5900-5902`). The relation is `[extends P25: D68's session API — signature unchanged, one added branch]`.

## 5. Plan Findings

**RC-A (material) — the drop must owe the attach: `_rt_attach_pending` is never set on the drop path.**
P28-02 deliverable 5 makes `_on_disconnected` clear every session's prime state and stop `_rt_retry_timer` — correctly. But deliverable 4 sets `_rt_attach_pending` only inside `_attach_live_feed` when the gate refuses. Trace a Journey-74 drop:

1. `load_chart` issues the prime and arms `_prime_timer` (`ui/ticker_session.py:1828-1842`); no RT subscription exists yet.
2. The socket drops → `_on_disconnected` → `_clear_prime_state()` stops the timer and clears `_prime_req_id`.
3. The clock advances: nothing fires (correct, `AC-D84.2`), so no refusal, so no flag.
4. Reconnect → `_replay_subscriptions()` re-issues only *registered* subscriptions (there are none) → `_attach_deferred_rt_feeds()` finds no session owed → **no subscribe**.

The chart therefore stays feedless after the reconnect. That is precisely the "R175's real risk, in the other direction" the S-P28-1 rationale names, and it is a regression against today's accidental recovery (the old backstop attached on a dead socket, which registered the line, which the replay then re-issued). It also makes the plan's own case (d) unimplementable: after case (c)'s drop there is nothing for `_on_connected()` to consume, yet (d) requires "attaches exactly once … one subscribe". A worker would have to invent both the rule and its scope.

The fix is a decision Plan must state, not one Task Manager may take: in `_on_disconnected`, before `_clear_prime_state()`, mark the session whose in-flight load the drop invalidated (`_prime_timer.isActive()` or `_prime_req_id is not None`), scoped so it cannot (i) attach a non-current session that `_on_session_prime_complete` would never have attached, or (ii) add a holder for a session that already has a live line (a reload mid-prime leaves `_rt_req_id` non-None — an unconditional flag would call `_attach_live_feed` on a session whose replayed line exists and bump `_rt_holders` again). Then update the flag's meaning in the Data Model ("refused **or invalidated by a drop that removed the line**") and make AR-P28-3's sentence true. Case (d) should then be written as the drop → reconnect path, not as a pre-set flag.

**RC-B (editorial) — "the six statements exist twice" is wrong; there are three full copies.**
The tree has the six statements at `teardown` (`ui/ticker_session.py:510-518`), at `prepare_load` (`:953-960`), **and** at `_fail_open_prime` (`:1858-1863`). The deliverable says the helper holds "the six statements now copied at `teardown` … and `prepare_load`", while the same wave's **Do not** says "leave a third copy of the six prime statements anywhere". A worker following the deliverable literally leaves the third copy and breaches the Do-not; a worker following the Do-not touches a site the deliverable never names. Name `_fail_open_prime` as a call site (the six are identical and the helper is safe there — it is called from `_on_prime_retry` when the retry cannot issue, `:1897`), or state explicitly why it is excluded. The architecture's "the same six statements twice" (`:136`, `:174`) carries the same error.

**RC-C (editorial) — retarget S-P28-15's relationship label** from P7 to P25 (see § 4).

## 6. Existing Repo Compliance — PASS

Codebase Summary substantive; constrained stack listed first; `[existing]`/`[new]`/`[new/changed]` labels complete; additive-only; `ui/popout_window.py`, `db_backup`, `popout_store`, `paths` correctly `[existing]`. The new `data` rows are consistent with the tree (`popouts.tz_offset` exists via `PopoutStore._ensure_tz_column`). No change since pass 1.

## 7. Frozen Interfaces — PASS

Pass-1 verbatim checks stand (all sampled contracts matched the tree). The revision changed only `ensure_rt_subscribed`'s body status and added S-P28-15; the signature stays frozen and the body is declared under **Not frozen**. Nothing `[new]` is in the frozen list; owning modules resolve; no duplicates. The only nit is the `[extends P7]` label target (RC-C).

## 8. Codebase Map — PASS

Unchanged since pass 1: skeleton at `0ff7964`, all module sections resolve, the planned `config/instance_lock.py` row sits outside the skeleton and is labelled `[new in P28]` with the not-yet-on-disk note, and no deleted-module entry remains. P28-08 remains a verify-and-refresh step.

## 9. Required Changes

1. **Make the drop owe the attach** — in `_on_disconnected`, set `_rt_attach_pending` for the session whose outstanding prime/load the drop invalidated **before** calling `_clear_prime_state()`, with a stated condition that (a) does not attach non-current sessions and (b) does not bump a holder for a session that already has a live line; rewrite case (d) as the drop → reconnect path; update the flag's meaning in the Data Model and AR-P28-3 so the architecture and the deliverable agree. `owner: PLAN`
2. **Correct the prime-copy count and name the third site** — `_fail_open_prime` (`ui/ticker_session.py:1858-1863`) holds the same six statements; name it as a call site (or exclude it with a reason) in P28-02 deliverable 5 and in the architecture rows that say "twice". `owner: PLAN`
3. **Retarget S-P28-15's relationship label** from `[extends P7]` to `[extends P25]` (the frozen `ensure_rt_subscribed` contract lives at `architecture.md:10471`). `owner: PLAN`

## 10. Requirements Escalations

None. FI-P28-1/2/3 remain faithful readings (unchanged from pass 1); no requirement needs redefinition for any item above.

## 11. Task Manager Readiness

**No.** A pack built from P28-02 as written would omit the rule that makes `_rt_attach_pending` true after a drop, and case (d) would either be written to pre-set the flag (testing nothing about the drop) or fail. Items 2 and 3 are one-line corrections that should land in the same revision.

## 12. Final Decision

`Status: CHANGES_REQUIRED`

`docs/plan.md` § P28 remains `Status: READY_FOR_VALIDATION`; nothing was activated and neither canonical file was edited. RC-2 through RC-5 are verified resolved and need no further work. On revision, item 1 is the only substantive change; the next pass will be a targeted re-validation of items 1–3.
