# Plan Review — Phase P28 (D84–D95)

Plan-Section-SHA256: 95dc3bc593784825a5fecbea03b4e1fa9f51b90f8bba0d3cbbf81632096f2fa2
Architecture-Section-SHA256: f09a35e0db391ee606320210d2ca790f2425d10d6d274953eb9213ff84cc5e65

- **Phase:** P28 — connection, startup and window lifecycle (D84–D95), Journeys 74–77, `AC-D84.1`–`AC-D95.3`, G5.
- **Pass type:** `final_pass`, full Validation Method — no prior `PROVISIONAL` review existed for P28, so the delta-only path did not apply. P27's code review is `REVIEW_COMPLETE`, so the phase gate is open and this pass could have finalized.
- **Inputs read:** `requirements.md` § Phase P28 (README: `READY_FOR_PLAN`), `design_gaps.md` DG132/DG135/DG136, `code_review/escalations.json` (no `routed_to: PLAN` + `open` entries; the open entries are `ESC-130`/`ESC-131` BUILD and `ESC-132` TASK_MANAGER, not this phase's), `docs/plan.md` § P28 (ends 8347), `docs/architecture.md` § P28 (11420–11705), `docs/codebase-map.md`, `docs/pending_doc_sync.md` (absent), `plan_lint` PASS (0/0) per the preamble.
- **Evidence basis:** `verify_cache.py check --phase P28` reported `new`/`phase mismatch` for all eleven surveyed files, so every site below was read directly in the tree at HEAD `0ff7964`. No cached claim was reused.

## 1. Review Status

`Status: CHANGES_REQUIRED`

Five PLAN-owned items. Two are structural (a missing implementing task for `AC-D84.2`; an attach-gate test seam that does not open the gate and a suite inventory that misses most of the blast radius), one is a requirement-coverage gap (`AC-D90.3`'s reload branch has no delivering mechanism), one is a correctness defect in the `_discard_popout` shape as specified, and one is a bundle of documentation/label inconsistencies. No requirements escalation is raised: FI-P28-1, FI-P28-2 and FI-P28-3 are each judged a faithful reading (see § 10).

The D84 deferred-attach lifecycle, the D86 skip path, the D90 budget arithmetic and the D95 lock design are all sound as designed; the defects below are in how the plan instructs the work to be delivered, not in the architecture's intent.

## 2. Validation Summary

| Step | Result |
|---|---|
| 1. Requirements coverage | **FAIL** — `AC-D90.3`'s "reload resets the budget and issues a fresh subscribe" has no mechanism anywhere in the plan (RC-3). All other ACs and Journeys 74–77 map to a wave. |
| 2. Architecture completeness | **PASS** — stack, components, responsibilities, relationships, data model, integrations, interfaces, security/ops, risks and rationale all present; the one missing decision is the D90.3 reset (RC-3). |
| 3. Architecture consistency | **FAIL (minor)** — architecture states `_rt_attach_pending` is cleared "in `teardown`" and that `_on_disconnected` stops `_rt_retry_timer`; neither appears in any plan deliverable (RC-1, RC-5a). |
| 4. Plan quality | **PASS** — eight justified waves, logical ordering forced by two single-writer files, coarse enough for Task Manager, no task-level dependency graph, no per-task test specs. |
| 5. Task Manager readiness | **FAIL** — a worker could not implement `AC-D84.2` without inventing the deliverable, and could not make the attach suites green from the seam the plan names (RC-1, RC-2). |
| 6. Scope integrity | **PASS** — no scope added or removed; no requirement reinterpreted silently; FI items recorded. |
| 7. Existing-repo compliance | **PASS** — substantive Codebase Summary; constrained stack listed first; `[existing]`/`[new]`/`[new/changed]` labels present and consistent; additive-only. |
| 8. Frozen interfaces | **PASS** — sampled contracts match the tree verbatim; nothing `[new]` is frozen; owning modules all resolve; no duplicates. |
| 9. Codebase map | **PASS** — skeleton fresh at `0ff7964`, sections resolve, planned lock row is outside the skeleton and explicitly labelled planned. |
| 10. Pending doc sync drained | **PASS** — `docs/pending_doc_sync.md` absent. |

## 3. Requirements Coverage

Every AC in `AC-D84.1`–`AC-D95.3` and Journeys 74–77 appears in the plan's traceability table with a wave. Checked in detail:

- **D84 / D85 / D86 / D87 / D88 / D89 / D91 / D92 / D93 / D94 / D95** — each defect has an implementing deliverable and a suite case. D84's three arrivals (prime completes, prime times out, fail-open) all funnel through `_on_session_prime_complete` → `_attach_live_feed_if_current` → `_attach_live_feed` (`ui/main_window.py:3974`, `:3982`, `ui/ticker_session.py:1845`), so one gate covers all three; D84.3 is enforced at the manager.
- **`AC-D90.1`, `AC-D90.2`** — addressed (coalescing guard, finite budget, terminal state). `AC-D90.3`'s **reconnect** branch is addressed (`_reissue_rt` → `mark_subscribed(reset_backoff=True)` → `retry_attempt = 0`). Its **reload** branch is **not** — see RC-3.
- **`AC-D84.2`** — the architecture and the plan's own suite case require it; the plan has no deliverable that implements it. See RC-1.
- **`AC-D86.1`–`AC-D86.3`** — covered; the failure the plan catches is the only exception `db_backup.backup_before_drop` can raise for a copy/mkdir/verify failure (`data/db_backup.py:86-90` wraps `OSError`; `:106-134` wraps every SQLite/table failure), so Journey 76's read-only-directory and partial-copy edges are inside the handler.
- **`AC-D95.1`/`AC-D95.2`** — covered by the lock branch (FAITHFUL — see § 10).
- **Non-functional** — G5 is named owner-run and never claimed (`plan.md:8202`, P28-04 exit, P28-08 deliverable 5); every other criterion is offscreen. Correct.
- **NFR: "no polling storms"** — respected: no new timer (`QTimer`/`singleShot` are the shipped idioms already in the touched methods); the deferred attach rides `_on_connected`.

## 4. Architecture Findings

Verified sound (no action):

- **Deferred attach (S-P28-1).** The flag is load-bearing exactly as claimed: `SubscriptionManager.replay_all` only re-issues *registered* subscriptions, and a refused `_attach_live_feed` registers nothing (`_subscribe_rt` is what calls `sub_manager.subscribe`, `ui/ticker_session.py:597-616`). The three arrivals all pass through `_attach_live_feed` (above). Consumption in `_on_connected` after `_replay_subscriptions()` cannot double-attach: the flag is cleared while iterating a copy, and a second `_on_connected` finds nothing pending. `_on_connected` runs from `bridge.connected`, emitted at the end of `nextValidId` after `_connected = True` (`ibkr/client.py:117-125`, `:253-266`), so `_transport_ready()` is genuinely true for a ready client in production — `_ibkr_connected` and `api_ready` are set from the same handshake.
- **D90 budget.** `next_retry_delay_s` increments then returns `min(5·2^(n-1), 60)` (`ibkr/stream_health.py:76-80`), i.e. **5, 10, 20, 40, 60, 60 s = 195 s** — the plan's ≈195 s is correct, and `MAX_RETRY_ATTEMPTS = 6` sits on the count, leaving the frozen arithmetic untouched. The coalescing guard cannot suppress a legitimate reschedule: a fired single-shot `QTimer` is inactive, a successful attach stops the timer, and a reload marks health subscribed so `state != FAILED` disarms the retry anyway. The terminal state is unreachable while disconnected: only `_on_rt_stream_error` (a received TWS error) can mark it, and `_retry_rt_subscribe` no-ops outside FAILED. Six attempts is within A237's latitude (the requirement fixes the shape, not the number); R179 is the right risk and its mitigation becomes real only once RC-3 is fixed.
- **D86 skip path.** `startup_notices` initialised before `_init_schema` is recorded before any reader exists; the `try` around `backup_before_drop` with the drop in the `else` cannot drop on failure or retry in the same run; the success path stays commit → backup → drop, byte-identical. The notice channel is the only way to speak after an import-time failure without moving the `db = DB()` singleton (which `paths.opt_in_production_db()` and every `from data.db import db` assume).
- **D86 × LWC ordering (AR-P28-9).** Moving `from ui.main_window import MainWindow` into `main()` preserves the ordering contract: `_register_lwc_scheme_before_qapp()` stays at module scope above `app = QApplication(sys.argv)`, `ui/lwc_host.py` imports no DB (no `data.` import at module level), so the DB singleton is genuinely constructed inside `main()` and inside the lock. `tests/test_lwc_host_bootstrap.py`'s AST assertion (module-level registration above `QApplication`) stays true, and its subprocess probe still imports `main` for the scheme only. AR-P28-9's mitigation holds.
- **D95 lock.** `QLockFile` ships with PyQt6 (QtCore), so no dependency is added. `setStaleLockTime(0)` is the right call and for the right reason: Qt's Unix implementation decides staleness by PID liveness for a lock written on the local host and only falls back to file age when `staleLockTime > 0`, so 0 disables the age fallback (no 30 s post-crash block) without weakening the dead-PID break — which the plan's case (c) tests. The order QApplication → `check_live_port` → `acquire(paths.get_db_path())` → window import → notices → `MainWindow()` → `exec()` → `unlock()` in a `finally` really does construct the DB inside the lock, and `get_db_path()` is the same resolution the DB uses, so a `DB_PATH` override gets its own lock by construction. Declining the `UNIQUE` constraint on `popouts` is faithful to `AC-D95.2`'s wording (see § 10).
- **Revisions.** Each declared target exists and says what the plan claims: `architecture.md:5900-5902` (RealtimeBarsManager/StreamHealth frozen row, "the APIs do not change"), `:2714` ("Pop-outs are Qt children destroyed with the parent"), S-P13-6/D49.6 (`:6953`), D55.4 (`:7523`, and the guide text at `usage.md:6,16,108,285` — md5 of `usage.md`/`USAGE.md` matches the architecture's `3052950e…`).
- **Scope/naming.** One new production module (`config/instance_lock.py`), no new dependency, no migration, no settings key, no new env var, no reconnect-policy change, sizes S/M only, no order path. `RealtimeBarsManager.replay_all` really has no production caller (only `tests/test_p7_w4_streaming.py:255` pins it), and the `"13 cases"` comment plus the id tuple exist exactly as the plan describes (`tests/test_qt_app_import_invariant.py:49-53`).

Findings (see Required Changes):

- Architecture prose promises behavior no wave delivers: `_rt_attach_pending` cleared "in `teardown`" and `_on_disconnected` clearing every session's prime state / stopping `_rt_retry_timer` (RC-1, RC-5a).
- `_transport_ready()`'s docstring says it "is the only window-side readiness predicate"; `_ibkr_connected` is read directly at `ui/main_window.py:1574, 1951, 1975, 1998, 2035, 2816` for other gates (RC-5e).

## 5. Plan Findings

**RC-1 — `AC-D84.2` / S-P28-2 has no implementing deliverable (owner: PLAN).**
P28-02's field list names `ui/ticker_session.py` and `ui/main_window.py`, and its traceability row says "P28-02", but none of its seven deliverables extracts `TickerSession._clear_prime_state()` or changes `MainWindow._on_disconnected`. Evidence the behavior is required and untasked: the architecture's Codebase Summary row (`architecture.md:11553`, `:11556`), System Components (b) (`:11607`), S-P28-2 (`:11693`), and the plan's own suite case 7(c) ("a session with an armed `_prime_timer`, then `_on_disconnected()`: no session has an active `_prime_timer`, `_prime_req_id`/`_prime_retry_pending`/`_prime_retry_args`/`_prime_reserved` are cleared"). The six statements really do exist twice today (`ui/ticker_session.py:510-518` in `teardown`, `:953-960` in `prepare_load`), and `_on_disconnected` (`ui/main_window.py:2843`) stops neither a prime timer nor `_rt_retry_timer`. A worker building from P28-02 as written cannot make case 7(c) pass without inventing the design.

**RC-2 — AR-P28-2's seam does not open the gate, and the affected-suite inventory is wrong (owner: PLAN).**
`_transport_ready()` is specified as `bool(self._ibkr_connected and getattr(self.ib_client, "api_ready", True))`. `MainWindow.ib_client` is a real `IBApiClient` (`ui/main_window.py:802`), whose `api_ready` returns `_connected` (`ibkr/client.py:104-106`), and every window suite monkeypatches `IBApiClient.connect` to a no-op, so `_connected` stays `False`. **Setting `win._ibkr_connected = True` alone leaves the gate closed.** The two cited precedents (`test_d39_burst_search.py:501`, `test_p13_restore.py:54`) set the flag for `_restore_popouts`/search-add flows, not the attach gate, so they do not establish that the seam satisfies the new predicate.

Concrete consequences found in the tree:

- Suites that drive a real `MainWindow` attach and assert the subscription exists, none of which is in the nine: `test_d24_popouts.py:39` (`assert win._rt_req_id == 6001`), `test_d27_aggregator_priming.py:88,125,153,330,444` (`is not None`), `test_d27_phantom_alarms.py:89` (`== 4242`), `test_d28_4_gate.py:65` (`assert req_id is not None`), `test_d28_tick_burst_baseline.py:47` (same), and `test_d27_reconnect.py:195-205` (`assert fake.rt_bars, "load_chart issued no RT sub"`). `test_d27_reconnect` is named in **P28-01's** exit condition as green and unchanged, but it is P28-02's gate that reddens it and no later wave re-checks it — so the phase's own exit conditions never cover the suites that the phase's central change breaks.
- Two of the nine do not drive a real window at all: `test_p7_w4_deferral.py:294` and `test_p7_w4_streaming.py:570` call `MainWindow._attach_live_feed(stub, …)` on a `SimpleNamespace` that has neither `_ibkr_connected` nor `_transport_ready` — the new gate raises `AttributeError` there, so "give each one's window factory the connection seam" does not apply.
- One of the nine never reaches the window gate: `test_d67_forming_candle` drives session-level `ensure_rt_subscribed` through a stub host (`:165`) and a `FakeRTManager`.
- P28-02's `git diff --name-only` allowlist covers only the nine, so the fix for the suites above would breach the wave's own scope check.

Answering the specific question — *does the seam change what the tests assert?* — **no case asserts that a subscribe happened while disconnected.** The `_complete_priming` assertions (`test_d27_stream_health.py:88`, `test_d28_2_sessions.py:63-96`, `test_d24_alarm_full_chain.py:65-80`) assert that the attach *succeeded*, not that the transport was down; setting the flag only makes the window's model truthful, so this is a harness seam, not a re-baseline. No D84-encoding assertion was found, so no extra re-baseline beyond the two named ones is needed. What is needed is a seam the gate actually reads (`win.ib_client._connected = True` alongside `win._ibkr_connected`, or an overridden `_transport_ready`, or an explicitly injectable predicate), a corrected suite inventory, and a widened allowlist/exit condition.

**RC-3 — `AC-D90.3`'s reload branch has no delivering mechanism (owner: PLAN).**
`AC-D90.3` requires: from EXHAUSTED, "the user reloads the chart … the budget resets and a fresh subscribe is attempted". Today a same-symbol reload reuses the session (`get_or_create_session`, `ui/main_window.py:3170`) and `_attach_live_feed` → `ensure_rt_subscribed()` returns the existing `_rt_req_id` without ever calling `_subscribe_rt` (`ui/ticker_session.py:465-473`); `prepare_load` resets priming and the 200 latch but **not** health (`:940-965`). Only `_subscribe_rt` calls `mark_subscribed` (`:615`). So from EXHAUSTED a reload neither resets `retry_attempt` nor issues a subscribe. P28-03's case (c) asserts both ("a fresh load resets `retry_attempt` to 0 and issues one subscribe"), and none of P28-03's six deliverables adds the mechanism. Note also that `resubscribe_rt()` uses `reset_backoff=False` (Fix-B, `:649-652`), so it cannot deliver "the budget resets" on its own — the mechanism must be explicit (e.g. `prepare_load` resetting health, or an EXHAUSTED branch in the attach path using a reset subscribe). This is a new architectural decision; it must come back to Plan, not be invented downstream.

**RC-4 — `_discard_popout` as specified can mask the failure with `UnboundLocalError` (owner: PLAN).**
P28-04 deliverable 3 wraps "construct → `attach()` → `show()` → save" in one `try` and calls `self._discard_popout(popout, exc)` in the `except`; deliverable 4 does the same in `_restore_popouts`, whose `try` begins with `self._ensure_restore_data_path(record)` **before** construction (`ui/main_window.py:1604-1620`). If the constructor or `_ensure_restore_data_path` raises, `popout` is unbound and the handler raises `UnboundLocalError`, defeating `AC-D91.1`'s "a failed open leaves nothing … reports once" on exactly the failure shapes it exists to cover. Required: assign `popout = None` before each `try` and discard only when a window exists (or construct outside the `try`).

**RC-5 — documentation/label inconsistencies to reconcile in the same revision (owner: PLAN).**
(a) Architecture says `_rt_attach_pending` is "cleared … in `teardown`" (`architecture.md:11626`, `:11654`) but no deliverable states it; either add it to P28-02 deliverable 4 (the file is already editable there) or drop the claim.
(b) The D90 progression is written "5/10/20/40/60/60 s" in P28-03 deliverable 1 and "5/10/20/60 s" in AP-P28-4 and Non-Functional; the total (195 s) is right for the shipped sequence, so make the shorthand consistent (A237's phrase is "5/10/20/60 s").
(c) P28-01's `[revises P4: the D40 classification row's "only if a live session existed" …]` vs S-P28-8's `[extends P4/D40: the classification, unchanged]`. `architecture.md:3321` is a classification boundary P28 does not change; one label should be chosen (extend + note reads accurately).
(d) P28-06's harness says "a temp dir as `DB_PATH`". `config/paths.get_db_path()` joins `_USER_APP_SUPPORT_DIR / DB_PATH` (`config/paths.py:90-115`), so DB_PATH must be an absolute **file** path for the lock to land beside it and for the "no second DB file was created" probe to mean anything — the conftest pattern (`tests/conftest.py:16-18`) is the model.
(e) `_transport_ready()`'s docstring should say "the only window-side readiness predicate **for the realtime attach**" — `_ibkr_connected` is still read directly at `:1574`, `:1951`, `:1975`, `:1998`, `:2035`, `:2816`.

## 6. Existing Repo Compliance — PASS

| Check | Result |
|---|---|
| Codebase Summary substantive (entities, components, integrations) | PASS — per-site table with what each site encodes today and its P28 disposition, plus the module-index pointer and the new-module note. |
| Existing stack respected, listed first | PASS — constrained rows first; `ibapi`/PyQt6/SQLite/`db_backup` untouched; nothing replaced or deprecated. |
| `[existing]`/`[new]`/`[new/changed]` labels on System Components, Data Model, Integration Points | PASS — every item labelled; `ui/popout_window.py`, `db_backup`, `popout_store`, `paths` explicitly `[existing]`/untouched. |
| Additive-only | PASS — no redesign beyond the requirement; untouched modules enumerated. |
| Summary consistent with proposal | PASS — every `[existing]` item treated as existing appears in the Codebase Summary; `popouts`' `tz_offset` column is real (added by `PopoutStore._ensure_tz_column`). |
| Current Tech Stack in `requirements.md` | PASS — present, no placeholders. |

## 7. Frozen Interfaces — PASS

| Check | Result |
|---|---|
| Verbatim contracts | PASS — sampled against the tree: `IBKRNotReady` class + docstring, `classify_error(error_code: int) -> str`, `RealtimeBarsManager.subscribe/unsubscribe/cancel_all`, `MarketDataManager.req_historical_data`/`req_mkt_data`/`req_contract_details`/`req_sec_def_opt_params`/`req_matching_symbols`/`cancel_*`, `IBApiClient.error/nextValidId/connected/socket_connected/api_ready/connection_state/last_disconnect_class/start_polling/stop_polling`, `StreamHealth.mark_subscribed/mark_first_bar/mark_failed/is_live/next_retry_delay_s`, `ensure_rt_subscribed/release_rt/resubscribe_rt/_subscribe_rt/prime_aggregator/_reissue_rt/_rebind_rt_req_id`, `PopoutChartWindow.__init__`, `PopoutStore.save/delete/load_all/clear`, `backup_before_drop`, `check_live_port`, `paths.*`. All match. |
| Nothing under construction frozen | PASS — the changed bodies are listed under **Not frozen**; the edited `subscribe` keeps its signature and the gate is declared. |
| Nothing frozen missing | PASS — `db_backup`, `popout_store`, `paths`, `SubscriptionManager` are either frozen or explicitly out of scope, and no consumed-and-unmodified `[existing]` interface is absent. |
| Owning module resolves | PASS — every named module exists; the only planned file (`config/instance_lock.py`) is under **Not frozen**, not the frozen list. |
| No duplicates | PASS — `_retry_rt_subscribe` appears under both classes by design (different owners, not aliases). |

## 8. Codebase Map — PASS

- Skeleton re-run at `0ff7964` (289 code files, 11 module rows, 23 test-impact rows) and the region between the `MAP-SKELETON` markers agrees with the tree.
- Every module section resolves; spot-checked `main.py`, `chart_assets/lwc/`, `config/`, `data/`, `ibkr/`, `services/gap_vix_service.py`, `ui/overlays/`, `spikes/lwc/spike_probe.py`, `probe_D53_4phase.py`, `tests/test_d27_stream_health.py` — all present.
- The P28 note exists and is correctly placed: it labels `config/instance_lock.py` `[new in P28]` **outside** the generated skeleton, explains that the file is not yet on disk, and lists the stale P5-era status cells rows-by-note (this map's documented convention). No deleted-module entry remains.
- Note for P28-08: the note and the lock row are already written, so deliverable 4 is a verify-and-refresh step, not new writing.

## 9. Required Changes

1. **Add the `AC-D84.2` implementation deliverable to P28-02** — extract `TickerSession._clear_prime_state()` from the two inline copies (`ui/ticker_session.py:510-518`, `:953-960`), call it from `teardown`, `prepare_load` and `MainWindow._on_disconnected` for every session, and stop `_rt_retry_timer` there (as the architecture states). `owner: PLAN`
2. **Correct AR-P28-2's seam and inventory** — name a seam the gate actually reads (`win.ib_client._connected = True` with `win._ibkr_connected`, or an overridden `_transport_ready`, or an injectable predicate); add `_transport_ready` to the two `SimpleNamespace` stubs; re-enumerate every suite that drives a real window attach (at minimum add `test_d24_popouts`, `test_d27_aggregator_priming`, `test_d27_phantom_alarms`, `test_d27_reconnect`, `test_d28_4_gate`, `test_d28_tick_burst_baseline`; remove or re-scope `test_d67_forming_candle`); widen P28-02's `git diff` allowlist and make its exit condition consistent with the corrected list. No assertion re-baseline is needed — no case asserts a subscribe while disconnected. `owner: PLAN`
3. **State a mechanism for `AC-D90.3`'s reload reset** — e.g. reset `stream_health` on `prepare_load` (or an EXHAUSTED branch in the attach path) with `reset_backoff=True` plus one fresh subscribe, and note that `resubscribe_rt()`'s `reset_backoff=False` cannot deliver the reset. `owner: PLAN`
4. **Fix the `_discard_popout` call shape at both open sites** — `popout = None` before each `try`, discard only when a window exists, so a constructor/`_ensure_restore_data_path` failure reports once instead of raising `UnboundLocalError`. `owner: PLAN`
5. **Reconcile the documentation/labels** — (a) `_rt_attach_pending` teardown clear in a deliverable or removed from the architecture; (b) one shorthand for the D90 progression; (c) one relationship label for the P4/D40 row; (d) `DB_PATH` = an absolute temp **file** path in the D95 harness, not a directory; (e) scope `_transport_ready()`'s "only predicate" sentence to the attach. `owner: PLAN`

## 10. Requirements Escalations

None. The three flagged issues are faithful readings and are accepted as recorded:

- **FI-P28-1** (budget is per-session but only the primary session spends it) — true today: `_schedule_rt_retry` is reached only from the primary branch of `_on_rt_stream_error` (`ui/main_window.py:2793-2800`). `AC-D90.2` is about "the retrying stream", so the narrow reading is correct; per-background-session retries would be a new requirement.
- **FI-P28-2** (D92's grep scoped to six live files) — faithful. `AC-D92.1`'s measurable clause is "exact-string assertions … at the sources that produce them, plus a grep over the usage docs"; the three usage docs are in the scope and the other three are the producing sources. `docs/README.md:5` does still say "trading terminal", but it is an internal navigation index, not the app or a usage doc, and rewriting the D45/D55 historical records would breach their conventions. Worth an owner-facing one-line note, not a requirement change.
- **FI-P28-3** (declines the `UNIQUE` constraint) — faithful. `AC-D95.2` states the guard branch first and offers the constraint only as an alternative ("if Plan adds a uniqueness constraint **instead**"). The lock branch is the requirement's own permitted outcome, and the residual is exactly what the requirement leaves to Plan.

## 11. Task Manager Readiness

**No.** A worker given P28-02 as written cannot implement `AC-D84.2` (no deliverable) or make the attach suites green (the named seam does not open the gate, and the inventory/exit condition contradict the tree). `AC-D90.3`'s reload case would be written against behavior no wave specifies. Those are architectural/planning decisions that belong to Plan, not to Task Manager.

## 12. Final Decision

`Status: CHANGES_REQUIRED`

`docs/plan.md` § P28 remains `Status: READY_FOR_VALIDATION`; nothing was activated, and `docs/architecture.md` / `docs/plan.md` were not edited. On revision, Plan should answer the five Required Changes, and the next pass will be a targeted re-validation against this list (no full re-validation unless Revision notes are missing).
