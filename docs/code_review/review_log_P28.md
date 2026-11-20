# Code Review — Phase P28 (D84–D95: readiness gate and deferred attach, stream budget, window ownership, startup survivability, instance lock, honest description)

**Pass type:** phase-final → **full pass** (mandatory on a phase-final pass, and independently barred from light: `test_verification.json` is **verdict `fail`**, eight of the eleven scoped tasks are size M, and three files are shared across tasks — `ui/main_window.py` (T2+T6+T7), `ui/ticker_session.py` (T2+T6), `main.py` (T8+T9)).
**Scope (incremental):** P28-T1 … P28-T11 — `precheck.json` names exactly these eleven and its `review_marker` is `review_log_P27.md`, i.e. no prior P28 pass existed.
**Tree:** build commit `1404877` (*P28 build: readiness gate + deferred attach, stream budget, window ownership, startup survivability, instance lock, honest description (D84-D95)*) on plan commit `e88f96b`, phase base `ef04c5a`. Working tree at review time: three modified files (`docs/codebase-map.md`, `docs/architecture.md`, `docs/plan.md`), all carrying the **next** phase's draft (a P29 note dated 2026-11-20 that cites `HEAD 1404877`) — a concurrent Plan run, not the P28 build and not this review. `precheck.json`'s three `unattributed_working_tree_changes` (`USAGE.txt`, `tests/test_d92_honest_description.py`, `usage.md`) are all inside `1404877` and are resolved in §6.
**Inputs:** `precheck.json` (0 `fail_fast`, 0 escalation entries, 5 `overlap` info flags, 1 `doc_required_unmet` info flag, footprint verified with no violations); `test_verification.json` (**verdict `fail`, exit 1, 220.35 s, 4 failing cases** — the orchestrator reports each reproduces in isolation, which I confirmed); `build_log.md` waves 422–441 (7 blocked/skeleton entries, all subsequently re-run to `done`); the eleven archived results; `task-graph.json` P28 ACs/packs/test commands; `requirements.md` `#### D84`–`#### D95`; `plan.md` Phase P28 (`8291` is the D90 "do not" line quoted in ESC-135); `architecture.md` Phase P28 (`S-P28-1`…`S-P28-15`).
**Result: 4 findings — 2 `blocking`, 2 `nice-to-have`** (2 → BUILD, 2 → TASK_MANAGER); two `gap`, one `quality`, one `consistency`. The suite verdict for the phase is **FAIL**: four cases red — two real regressions of shipped coverage (`test_d41_removal`, `test_p13_hold_probe`), one shipped case whose fail-open attach silently stopped attaching (`test_p7_w2_prime`), and one task-vs-task contradiction (`test_d84_d88_readiness` vs `test_p28_fence`).

---

## 1. Findings

| id | task | route | category | severity | one line |
|---|---|---|---|---|---|
| ESC-133 | P28-T2 | BUILD | gap | blocking | `test_p28_t2_05_dead_replay_absent_everywhere` scans raw text over `ui/`+`ibkr/`+`tests/`, so it reddens on the P28 fence's **module docstring** (which legitimately states the symbol is gone). The scan must detect *usage* (attribute access/call) rather than any occurrence; the fence's `not hasattr` assertion and docstring stay. |
| ESC-134 | P28-T3 | TASK_MANAGER | gap | blocking | The deliverable-6 harness-seam inventory is a 17-file list and the predicate set is 21: three suites that assert the live RT line (`test_p13_hold_probe`, `test_d41_removal`, `test_p7_w2_prime`) reach `_attach_live_feed`, are refused by the new gate, and are red — and **none is in any task's `touches_files`**, so no BUILD re-dispatch can repair them. Seam-only, proven by experiment (§2.1). |
| ESC-135 | P28-T6 | BUILD | quality | nice-to-have | `plan.md:8291`'s "do not make the terminal state reachable while disconnected" is not structurally guaranteed: a post-drop RT error re-arms the retry loop (`_on_rt_stream_error` has no readiness guard), each re-arm spends a budget attempt, and the next late error takes the terminal branch — `EXHAUSTED` while disconnected. Self-heals on replay, but the badge/status line lie while disconnected. |
| ESC-136 | P28-T4 | TASK_MANAGER | consistency | nice-to-have | Pack-prose spot-check: `AC-P28-02-S1`'s "each changed file differs only by its seam assignment(s) — no assertion, expected value, case name or fixture is changed" is a stated guarantee with **no enforcing test** in any of T3/T4/T5 (the only test is "run the group's suites"). |

**No `security` finding. No mock endpoint anywhere in the production diff (§4, "Standing invariants").**

---

## 2. The four failures — reproduced, classified, and corrected where the orchestrator's diagnosis was off

I reproduced all four in isolation (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q <nodeid>`), and separately ran the three attach-related ones with the seam injected at runtime.

### 2.1 No. 1, 2 and 3 — one cause: the missing harness seam (three suites), **not** a product defect

Reproduction (each red on its own):

| case | assertion | observed |
|---|---|---|
| `tests/test_p13_hold_probe.py::test_p13_hold_lifecycle_probe` | `first["holders"] == 1` | `0` |
| `tests/test_d41_removal.py::test_removed_requests_are_never_issued` | `assert issued["rt"] or fake.rt_bars` (`:383`, message "the RT bar line stopped issuing") | empty |
| `tests/test_p7_w2_prime.py::test_t12_skipped_prime_warns_counts_and_fails_open` | `assert sess.rt_req_id == 4242` (`:228`) | `None` |

**Correction to diagnosis 3 (the `_fail_open_prime` → `_clear_prime_state()` hypothesis): it is not a product defect.** I traced the interaction line by line:

- `TickerSession._clear_prime_state` (`ui/ticker_session.py:515-534`) clears exactly six prime markers — `_prime_timer`, `_prime_req_id`, `_prime_period_start`, `_prime_retry_pending`, `_prime_retry_args`, `_prime_reserved`. It does **not** touch `_rt_req_id`; the RT reqId lives in a different attribute and is written only by `_subscribe_rt`/`_reissue_rt`/`_rebind_rt_req_id`/`_unsubscribe_rt` (`:639`, `:667`, `:680`, `:688`).
- `_fail_open_prime` (`:1881-1903`) calls the clear **first**, then counts, logs, and calls `_host._on_session_prime_complete(self)` — so the attach is the *last* thing to happen, not something a clear can undo.
- `_on_session_prime_complete` → `_attach_live_feed_if_current` → `_attach_live_feed`, which refuses when `_transport_ready()` is false (`ui/main_window.py:3534-3536`) and sets `_rt_attach_pending`. In `test_p7_w2_prime` the window is a real `MainWindow` with `IBApiClient.connect` monkeypatched to a no-op, so `_ibkr_connected` is False and `api_ready` is False — the gate refuses, `rt_req_id` stays `None`. The test's `attached == [sess]` passes because it spies `_on_session_prime_complete`, which is *called* either way.

**Proof that the seam is the fix and nothing else is missing.** I injected the seam into every `MainWindow` instance (`self._transport_ready = lambda: True` in a wrapper around `__init__`, a pytest plugin outside the repo) and re-ran the three files unmodified:

```
PYTHONPATH=<probe-dir> QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q -p p28_seam_probe \
  tests/test_p13_hold_probe.py tests/test_d41_removal.py tests/test_p7_w2_prime.py
..........  [100%]      # 10 passed, zero edits
```

So all three are the same class as the eighteen suites the phase already repaired — the inventory simply did not reach them (§3). This is exactly `AC-D84.1`'s load-bearing arrangement: the window gate refuses, and the *harness* says "this case means a live transport" with the seam. Note the seam must be the predicate, not `_ibkr_connected`: `test_d41_removal` already calls `_on_connected()` (so `_ibkr_connected` is True) and is still refused, because the real `IBApiClient` never handshaked and `api_ready` — the client's `_connected` (`ibkr/client.py:109-112`) — is False.

### 2.2 No. 4 — `test_p28_t2_05_dead_replay_absent_everywhere`: a test-vs-fence contradiction, and the orchestrator's description needs one correction

Reproduced: `assert hits == []` reports exactly one hit, `tests/test_p28_fence.py: RealtimeBarsManager.replay_all`.

**Correction:** the hit is **not** the fence's `not hasattr(...)` assertion. `tests/test_p28_fence.py:256-257` reads `assert not hasattr(RealtimeBarsManager, "replay_all")`, which contains only the bare string `"replay_all"` and never matches either needle. The hit is the fence's **module docstring, `tests/test_p28_fence.py:19`**: "…the absence of ``RealtimeBarsManager.replay_all``, …" — i.e. prose that legitimately records the symbol as gone, in the one file whose job is to record what the phase pins.

The scan itself is `tests/test_d84_d88_readiness.py:325-338`: two needles built by string concatenation (`"rt_manager." + "replay_all"`, `"RealtimeBarsManager." + "replay_all"` — concatenated to keep the scanner from matching *itself*) searched as substrings over every `.py` under `ui/`, `ibkr/`, `tests/`. Concatenation defeats self-matching but not prose: any docstring, comment or negative assertion that names the symbol is a hit. `AC-D88.1`'s text ("a static scan … finds no `rt_manager.replay_all`/`RealtimeBarsManager.replay_all` reference") is what makes both deliverables defensible and therefore contradictory — this is the breakdown's problem as much as the scan's, but the smallest correct fix is the scan, so it is routed to BUILD (ESC-133) with the resolution spelled out: detect **usage** (an `ast.Attribute` with `attr == "replay_all"`, or an equivalent code-only check excluding string literals and comments), which still reddens on `mgr.replay_all()`, `RealtimeBarsManager.replay_all(...)` and `rt_manager.replay_all(...)`. Deleting or rewording the fence line is explicitly not the fix: that assertion plus `hasattr` is the phase's only guard against the dead replay returning.

---

## 3. The seam inventory, by predicate (the rework's true scope)

This is the phase family's third inventory miss, so I measured it instead of counting files. Method: a read-only pytest plugin (outside the repo, imported with `-p`) wraps `MainWindow._attach_live_feed`, records `self._transport_ready()` at every call with the test's nodeid, then calls through unchanged. Full suite, same command as the verifier (`.venv/bin/python -m pytest -q -m 'not webengine'`, `QT_QPA_PLATFORM=offscreen`); the run reproduced exactly the same four failures and nothing else, so the instrumentation is behaviour-neutral. Results: **90** test files construct a `MainWindow(`; **42** reach `_attach_live_feed` at runtime; **22** of those get at least one refusal.

| group | files | needs the seam? | has it? |
|---|---|---|---|
| audited groups 1–3 (T3/T4/T5) | `test_p7_w4_deferral`, `test_p7_w4_streaming`, `test_d24_alarm_full_chain`, `test_d24_popouts`, `test_d24_smoke_gate`, `test_d27_aggregator_priming`, `test_d27_phantom_alarms`, `test_d27_reconnect`, `test_d27_stream_health`, `test_d28_2_sessions`, `test_d28_4_gate`, `test_d28_pacing`, `test_d28_tick_burst_baseline`, `test_d68_hold_balance`, `test_p13_hold_fix`, `test_p13_restore`, `test_phase3_fixpass` (17) + `test_p13_attach` (T7) | **yes** — every attach call is allowed and asserted | **yes** (1 added line each; `git diff --numstat` = `1+/0-` on all 18) |
| P28's own suites | `test_d85_d91_popout_ownership`, `test_d89_d90_stream_budget` | **no** — they exercise the real predicate with a ready fake (`_ibkr_connected` + fake `_connected=True`), per `AC-D84.1` | n/a (0 refusals, 7 + 11 calls) |
| predicate-refusal suite | `test_d84_d88_readiness` | **no, by design** — case (b) is the case that keeps the seam a stub | n/a (6 refusals on purpose: `[False-False-*]` and `[True-False-*]`) |
| **missing seam, red** | **`test_p13_hold_probe`** (1 call, refused; asserts `rt_req_id`, `_rt_holders` ×4) · **`test_p7_w2_prime`** (1; asserts `rt_req_id`) · **`test_d41_removal`** (2; asserts RT issuance) | **yes** | **no** |
| missing seam, inert (18) | `test_d24_9_popout_persistence`, `test_d28_2_load_chart_button`, `test_d42_depth_floor` (17 calls), `test_d45_removal`, `test_d48_mode_parity`, `test_history_backfill` (24), `test_history_backfill_disconnect` (11), `test_history_backfill_loadpath` (10), `test_p13_host_error`, `test_p14_cache_guard`, `test_p14_indicator`, `test_p14_lifecycle`, `test_p15_continue`, `test_p15_expiry`, `test_p15_surfacing`, `test_p19_prefetch_wave`, `test_p7_w1_persist`, `test_p7_w3_wide` | **no** — none asserts that an RT line was issued (`rt_req_id`, `_rt_holders`, `ensure_rt_subscribed`, or an RT-bars count). The group's only RT-shaped code is `test_d45_removal`'s recording client (`self.rt_bars`, `:452`) which is never asserted on. The refused attach is outside their subject, and their history-wave assertions are green and unaffected | n/a |

So the seam set is **21 suites, 18 present, 3 missing** — the "seventeen + `test_p13_attach`" count was short by three, exactly as the failures show, and the eighteen inert ones cannot redden on this gate. The three missing ones are in no task's `touches_files`, which is why ESC-134 goes to TASK_MANAGER (a BUILD re-dispatch would trip the footprint check) and why its AC text is restated as the invariant, not as a longer file list.

---

## 4. Phase-final duty checks (each verified on the live tree, not taken from a worker's prose)

**D84 — the gate cannot false-negative a ready production client, and the drop marks before clearing.**
`_transport_ready()` (`ui/main_window.py:3505-3518`) = `_ibkr_connected and getattr(ib_client, "api_ready", True)`. In production `api_ready` *is* `client._connected` (`ibkr/client.py:109-112`), `_ibkr_connected` is assigned True only in `_on_connected` (`:1874`), and `_on_connected` is the handler for `bridge.connected` (`:917`), which `_set_state` emits **only** on the transition to `CONNECTED` (`ibkr/client.py:123-131`) — reached from `nextValidId` after `_connected = True` (`:259-263`). So whenever the window has been told "connected", the client is handshaked, and the two terms agree: no false negative on the production path. `_on_disconnected` (`:2946-2996`) runs the mark loop **before** the clear in the same pass, with all three terms (`_rt_req_id is None`, `symbol == _current_symbol`, and armed backstop ∨ prime reqId ∨ deferred retry), then `session._clear_prime_state()`, then `_rt_retry_timer.stop()` — the "mark first, then clear, because `_attach_live_feed` is the only other setter" reasoning holds: the clear would otherwise erase the only evidence that an in-flight load was killed.

**D88 — one seam, two call sites, one replay path.** `market_data.require_api_ready is error_codes.require_api_ready is realtime_bars.require_api_ready` (pinned by `test_p28_t2_06`); `RealtimeBarsManager.subscribe`'s first statement is `require_api_ready(self.client)` (`ibkr/realtime_bars.py:38`), before pacing (`:39`) and before the id; `replay_all` is gone and the class docstring states the single path. The only text that still names the symbol is the fence's docstring (§2.2).

**D90 — budget, coalescing, and the one gap.** `MAX_RETRY_ATTEMPTS = 6`, `EXHAUSTED`, `mark_exhausted`, `retry_budget_spent`, `describe() == "stopped"` all in `ibkr/stream_health.py`; `next_retry_delay_s` untouched (`5/10/20/40/60/60` re-read by the fence test and by `test_d27_stream_health`, green). The coalescing guard (`if self._rt_retry_timer.isActive(): return`, `:2890-2898`) **does not** suppress a legitimate reschedule after a reload: a successful attach stops the timer (`:3553`) and the reload's own subscribe resets health, so the new line arms its own deadline; the only case where an old deadline survives is a reload whose attach is *pacing-deferred* (`:3539-3548` returns before the stop), and there the retry acts on the current line at the earlier instant — no retry is lost. `_retry_rt_subscribe` is FAILED-only, reuses `_transport_ready()`, and folds `IBKRNotReady` into the not-ready branch instead of escaping a Qt slot. The one thing not held shut is "terminal unreachable while disconnected" → **ESC-135**.

**D86 — skip the drop and start.** `data/db.py:35-40` sets `startup_notices` before `_init_schema` (so a notice exists before any reader — `main.py` imports the singleton, then reads `startup_notices()`); the retired-table block wraps only the backup call and drops in the `else:` (`:190-207`) — one drop, once, on success; no force-drop path. The re-baselined case (`tests/test_db_backup.py::test_migrate_schema_aborts_drop_when_backup_fails`) replaces only the `pytest.raises` with "construction completes + exactly one notice", and I read the remaining assertions: `_RETIRED_TABLES` all present, `idx_positions_symbol_con_id` present, `positions` 2 rows, `trade_groups` 1, `position_group_map` 1 — so it still reddens if a DROP runs or a row is lost. The other `backup_before_drop` cases are byte-identical to `ef04c5a`.

**D94 — the import cannot raise.** `config/settings.py` keeps the raw text in `_PORT_PARSE_ERROR` / `_CLIENT_ID_PARSE_ERROR`, `IBKR_PORT` is `int | None` only until the guard, and `check_live_port()` refuses malformed values first, naming the offending string, before the unchanged `IBKR_PORT != LIVE_PORT` comparison. `main()` calls it after `QApplication`, so the refusal is a dialog (`test_d86_d94_startup` runs this in a subprocess with `IBKR_PORT=abc`).

**D95 — the lock.** `config/instance_lock.py` is the only new production module; the path is `<resolved db>.lock` (`lock_path_for`, so a `DB_PATH` override is a different lock by construction — `test_lock_path_is_derived_from_the_db_path`); `setStaleLockTime(0)` makes staleness PID liveness (`test_dead_pid_lock_is_broken_without_the_30s_timer`); `main()` acquires it after `check_live_port` and **before** `from data import db` / `from ui.main_window import MainWindow` (`main.py:63-77`), refuses with a pid/hostname message, and `finally: lock.unlock()`. The two-process test asserts the second instance never creates the DB file — the property that matters (no second SQLite writer), not just "a dialog appeared".

**D85 / D91 — ownership and the failed open.** `closeEvent` (`:5364-5392`) latches `_closing`, then closes pop-outs first through `popout.close()` (their own `closeEvent` → `detach`), iterating a copy, each in its own guard with an unregister belt in the `except` — sessions are still alive when each pop-out releases its hold. `_discard_popout` (`:1282-1330`) is `None`-safe and is called with `popout = None` bound before the `try` at **both** sites (`_open_popout:1224-1280`, `_restore_popouts:1611-1680`), so a constructor raise reports once instead of raising `UnboundLocalError` inside the handler that exists to cover it. `ui/popout_window.py` is untouched (`git diff --name-only ef04c5a 1404877` does not list it).

**D92 — words only.** The title is `NDThinkChart — read-only market data` (`ui/main_window.py:357`); the guard's refusal names read-only / places no orders / configured port; `usage.md` carries the same wording and `USAGE.md` is the **same inode** (`ls -li`: both `70268344`, 16121 bytes) on this case-insensitive volume, so byte-identity holds by construction and `test_p28_t10_04` asserts it on bytes anyway. No historical record was rewritten: the retired-claim grep is scoped to the six live files (`FI-P28-2`), and `docs/README.md`, `docs/archive/**`, `docs/D55_*`, `docs/build/**` are untouched. The D65 badge wording is pinned unchanged.

**Standing invariants.** Mock-endpoint scan of the production diff (`ibkr/ ui/ config/ data/ main.py`, all added lines, `mock|fake|stub|simulat`): **zero hits** — the only matches in the phase's diff are inside `docs/tasks/task-graph.json` prose and test files. `G5` is recorded as owner-run and never claimed (`tests/test_p28_fence.py:41`; build log wave 441). No new dependency, no migration, no settings key, `config/instance_lock.py` the only new module, `docs/requirements/**` untouched by the build (`git diff --name-only … -- docs/requirements/` empty), and D1–P27 unopened apart from the declared `[revises P4/P7/P13/P16]` labels.

---

## 5. Task-by-task (diff-first: `git diff ef04c5a 1404877 -- <files_changed>`)

**P28-T1 (D87, D93) — clean.** `connectionClosed` keeps the classification inside `was_connected` and moves `_schedule_reconnect()` out of it (`ibkr/client.py:354-380`), so a pre-handshake close retries through the same backoff and records no `TWS_GONE`; `close()` sets `ConnectionState.DISCONNECTED` **directly** and resets the three bookkeeping fields (`:382-400`), so no `disconnected` signal runs the outage path in teardown; `connect()` cancels a pending timer before storing params (`:74-92`). `_do_reconnect` still calls `super().connect` and never cancels its own timer. Six cases pin exactly these, including the "no signal" leg with a counting slot.

**P28-T2 (D84, D88) — the production half is sound; one test is over-broad (ESC-133).** `require_api_ready` is the verbatim lift (duck-typing identical, exception identity preserved), the realtime gate sits first, `_transport_ready` and the deferred attach are as specified, `_clear_prime_state` is genuinely the one clear (four call sites: `teardown:550`, `prepare_load:996`, `_fail_open_prime:1894`, `MainWindow._on_disconnected:2991`; the two surviving `_prime_reserved = False` writes at `:1309` and `:1874` are the *different* rules — the timeout release and the issue release — not copies), and the two named re-baselines are the only assertion changes (`test_p7_w4_streaming`'s dead-replay case deleted, `STREAMING_IDS` 13 → 12, comment updated).

**P28-T3 / T4 / T5 — clean as delivered, incomplete as scoped (ESC-134, ESC-136).** Every changed file in all three groups is `1+/0-`: one added `win._transport_ready = lambda: True` (or `_transport_ready=lambda: True` on the two `SimpleNamespace` stubs) inside the existing `_make_window`, no assertion, fixture or case touched. The suite counts in the build log match what I re-ran. The miss is upstream of the edit quality: the packs enumerate 17 files and the predicate set is 21.

**P28-T6 (D89, D90) — clean except ESC-135.** Health reset on replay (`_reissue_rt` → `mark_subscribed(reset_backoff=True)` + signal), timer stop at the top of `_on_connected`, coalesced scheduling, distinct terminal badge/branch, FAILED-only retry with `_transport_ready`/`IBKRNotReady`, and the terminal-only recovery in `ensure_rt_subscribed` (predicate is the *state*, not `retry_budget_spent`; `resubscribe_rt` still `reset_backoff=False`; `prepare_load` still resets no health — I checked both). The nine cases cover the connected-path budget, the reload/reconnect recoveries and the superseded-callback negatives. Note the naming inconsistency only: this suite's cases are `test_P28_T6_NN_…` while every other P28 suite uses `test_p28_tN_NN_…` — cosmetic, no action.

**P28-T7 (D85, D91) — clean.** See §4. The eight cases include the two subtle ones: a raising pop-out close does not stop the main close, and the main chart's hold survives a pop-out close.

**P28-T8 (D86, D94) — clean.** See §4. The blocked round was resolved correctly: the worker refused to edit `tests/test_db_backup.py` outside its footprint, and the re-baseline landed under the task that owns it.

**P28-T9 (D95) — clean.** See §4. `main()`'s ordering (port guard → lock → DB/window import → notice loop → theme → window → `app.exec()`) is asserted by `inspect.getsource` in `test_lock_precedes_the_window_import_and_popout_save_is_idempotent`, and the second-instance test is a real two-process test, not a mock.

**P28-T10 (D92) — clean; the `doc_required_unmet` flag is an attribution artefact, not a doc gap.** See §6.

**P28-T11 (D88 fence) — clean, and the only file that trips T2's scan.** The fence pins the requirements record's markers, the module-read values (including `MAX_RETRY_ATTEMPTS`, the EXHAUSTED/FAILED distinction, the progression, `_rt_attach_pending`'s default, the three in-file `_clear_prime_state` sites plus the window's, the frozen signatures, the lock-before-import ordering) and the D92 strings, and its delta allowlist is a subset of the phase's names. Its 13 cases pass; it contradicts nothing except a text scanner.

---

## 6. Doc ruling (`doc_required_unmet`, P28-T10) and the unattributed changes

**Ruling: no doc gap.** `usage.md` in the build commit carries exactly the D92 wording ("read-only market-data client that places no orders", "configuration check", "refuses any other port", "live TWS session") and `test_p28_t10_04` asserts it on bytes against `USAGE.md`; `USAGE.txt`'s short form says the same three things and is untouched. The flag fires because P28-T10's archived result lists only `tests/test_d86_d94_startup.py` in `files_changed` while `usage.md` was also edited (its repair pass rewrote the result). The content is right and the guidance is in place — this is a result-record inaccuracy, not a documentation miss, and re-dispatching a done task to amend a result file would be churn, so I am not escalating it. Noted for the record: `USAGE.txt`, `tests/test_d92_honest_description.py` and `usage.md` (precheck's `unattributed_working_tree_changes`) are all inside `1404877`; nothing of the build is left uncommitted.

---

## 7. Escalation close-out

`escalations.json` holds 127 entries at the start of this pass, **all `addressed`, none `open`**, and `precheck.json` reports `escalation_entries: []` with `escalation_updates: []` — so entry point C (close-out) had nothing to re-verify this pass, and I opened no `PRE-*` equivalents. No entry was flipped by me: nothing to flip.

---

## 8. What the rework has to achieve

1. **ESC-133** (BUILD, P28-T2): usage-based dead-replay scan; fence untouched. One file, `tests/test_d84_d88_readiness.py`.
2. **ESC-134** (TASK_MANAGER, P28-T3): a repair task (or an AC restatement plus a task) covering `tests/test_p13_hold_probe.py`, `tests/test_d41_removal.py`, `tests/test_p7_w2_prime.py` — one seam line each, nothing else — with those three in `touches_files` and the three files as its `test_command`; and the invariant written into the seam ACs so the next inventory starts from a rule.
3. **ESC-135** (BUILD, P28-T6): stop the disconnected retry loop from entering the terminal state.
4. **ESC-136** (TASK_MANAGER, P28-T4): enforce or drop the "no assertion line changed" guarantee.

Until 1 and 2 are fixed the phase is **not** gate-ready: the suite is red with two genuine coverage regressions, so this pass's marker records that the review happened, not that the phase may advance.

Status: REVIEW_COMPLETE
