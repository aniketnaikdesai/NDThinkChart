# Code Review — Phase P29 (D96–D100: persisted state and alarm evaluation)

**Pass:** phase-final — **tier: FULL** (a phase-final pass is always full; the light-pass conditions were not
consulted for the verdict). Scope: `P29-T1`…`P29-T5`, the slice the precheck scoped against the P28 marker.
**Tree:** build commit `dcfdd60`, base `3b92ce6`. 18 paths, +2874/−2570; 7 production files changed in place,
3 suites re-baselined, 4 suites added, no production module added.

## 0. Verification basis (consumed, not re-derived)

- `precheck.json` (06:26:47Z): 5 tasks in scope, all `done`, tests 8/8 · 5/5 · 10/10 · 6/6 · 5/5, **0 fail_fast**,
  0 overlaps, 0 unattributed working-tree changes, 0 escalation entries to append, 5 doc candidates **0 touched**.
- `test_verification.json`: **pass**, exit 0, 227.52 s, `.venv/bin/python -m pytest -q -m 'not webengine'`,
  no timeout. Ground truth for "the suite passed".
- Targeted re-run on the committed tree (mine): the four P29 suites + `test_d40_tws_lifecycle` +
  `test_alarm_service` → **98 passed**, including the fence (13/13) after the commit that turned the four new
  suites from untracked into tracked files.
- `escalations.json`: 132 entries, **0 open** — nothing to close out this pass (entry point C is empty).

Findings are three entry-point reviews of `done` work; there were no blocked tasks.

## 1. P29-T1 (D96/D100) — the write is atomic, the declaration is one list

**T1.1 — D96's exact shape is fixed, and I proved the split.** `StudyStore.save`
(`data/study_store.py:97`) builds `rows` (including `json.dumps(deepcopy(params))`) **before** it reaches
`db.conn`, then runs `DELETE` + `executemany` inside `with db.conn:` (line 115) with no trailing `commit()`.
`sqlite3.connect` is left at its default deferred isolation, so the context manager commits on success and
**rolls back on exception** — this is what makes the *between-statements* case work, not just the
serialization case.

Independent probe (temp `DB_PATH`, the real stores, nothing stubbed):

| case | result |
|---|---|
| `save` with `params={"bad": object()}` (TypeError) | exception surfaced once; `load` byte-identical; `in_transaction is False` |
| then an unrelated committed write | `load` still byte-identical |
| `save` with `type=None` (IntegrityError **after** the DELETE) | exception surfaced; `load` byte-identical; `in_transaction is False`; still identical after an unrelated commit |
| retry with a valid set | stores exactly the valid set |
| **RED control** — the pre-fix ordering (`DELETE` then serialize) replayed by hand | the DELETE survives an unrelated commit and the rows are gone (`[]`) |

So the fix is discriminating in the direction D96 requires, and `test_p29_t1_02` is a real rollback proof, not
"no exception escaped".

**T1.2 — the two-list drift is structurally unrepresentable.** In `update_group`
(`data/drawing_store.py:62`) the unknown-key check (`:72-76`) runs before any cursor exists; then **one**
`pairs` list (`:77`) feeds **both** `values` (`:78-87`) and `assigns` (`:88`). There is no second filter to
disagree with the first, and no way to reach `cursor.execute` with `len(values) != len(assigns)`: the loop
appends exactly one value per pair or raises. Bool coercion is keyed (`visible`/`locked` → `int`; `name`/`color`
+ bool → `ValueError`) and also precedes the cursor.

Probe: `update_group(gid, visible=False, bogus=1)` → `ValueError` naming `bogus`, `set_trace_callback` recorded
**zero** statements, row unchanged, `in_transaction is False`; `name=True` → `ValueError`, zero statements;
`visible=False, locked=True` → one `UPDATE` naming exactly those two columns and moving exactly those two values;
`{}` → no statement. The three shipped call sites (`ui/drawing_groups_dialog.py:184,197,272`) each pass one
allowed key; the checkbox path can only supply `visible`/`locked`, so the new bool rule cannot redden the UI.

**My judgement on the test suite itself:** `test_p29_t1_07`'s parameter/placeholder assertion is honest, not
vacuous — it documents that `set_trace_callback` reports statements **post-expansion** (so it asserts no residual
`?`), and backs that with a structural column-list assertion. AC-D100.2's "binds as many parameters as it has
placeholders" is thereby read faithfully rather than tautologically. No assertion was weakened.

Minor, not routed (prose): architecture AR-P29-1's mitigation says the "callers must not hold uncommitted work"
invariant "is stated in `save`'s docstring"; the docstring (`:99-110`) states atomicity and "no transaction
pending" but not that caller-owned pending work would be absorbed by `with db.conn:`. The risk is real but
already gated by `test_p29_t1_03`'s before/after `in_transaction` assertions, and every store method in the repo
commits at the end of its own operation — recorded here for the next touch of that docstring, no action.

## 2. P29-T2 (D97) — one rule, both directions, no state added

`services/alarm_service.py:63-64` is exactly `prev <= level < curr` / `prev >= level > curr`; `cross_either` is
their disjunction (`:70`) and the guard, the skip clauses, the signature and the return type are untouched. The
rule is stated **once**, in the function docstring — there is no per-direction second statement to drift.

Behaviour, checked against AC-D97.1–.3 and Journey 79 (and confirmed by the shipped cases, which I ran):

| sequence (level 10.0) | expected | actual |
|---|---|---|
| 9.5 → 10.0 (arrival **at** the level) | no fire — arms | `[]` |
| 10.0 → 10.01 (strictly beyond) | fires once | `[alarm]` |
| 10.0 → 10.0 repeatedly | never fires | `[]` |
| 9.0 → 11.0 (gap straight past) | fires once | `[alarm]` |
| seed `prev is None` at the level | nothing | `[]` |
| touch then **opposite** move (10.0 → 9.4 for `cross_above`) | no fire | `[]` |
| return to the level after firing | no re-fire | `[]` (latch) |

**DG133 respected:** `Alarm`'s field set carries no touch/armed member (fence case, my read of
`data/models.py`), the touch is derived from `prev`, and no clock/cache/second path was introduced.

**Re-baseline:** exactly the one named case — `test_exactly_on_alert_price_above_counts` → 
`test_arrival_on_the_level_is_a_touch_not_a_cross` — with `AC-D97.1`/A242 in its docstring, and the new cases
added around it. Every other shipped assertion in the file is byte-identical in the diff. Note this is the
test name the map/fence still record under its retired spelling — see ESC-139 (cosmetic, P29-T5's fence).

## 3. P29-T3 (D98) — the gate is the session predicate, and the ledger has one owner

**T3.1 — the cold-start case is designed, not merely asserted.** `begin_outage`
(`services/alarm_monitor.py:180`) returns **before** touching any state when `self._host._sessions` is empty;
otherwise it sets `_outage_active` and `setdefault`s the per-symbol start for sessions with live alarms.
`resume_all` (`:224`) captures `resuming_from_outage` at entry (`:235`), reports/clears the ledger, and re-seeds
each session **only** when that flag was set (`:243`). `MainWindow._on_disconnected` calls `begin_outage()`
immediately after `_ibkr_connected = False` and **before** the TWS_GONE/other classification
(`ui/main_window.py:2977`); `_on_connected` is now one path — `reconcile()` then `resume_all()`
(`:1907-1908`).

Consequence, verified two ways: on an "app started before TWS" launch the failed pre-handshake
`connectionClosed()` finds no session, records nothing, and the first `nextValidId(1)` keeps the reconcile-seeded
1m close. `test_p29_t3_08` proves it with a seeded `BarCache` (`last_chart_price == 100.0` after the handshake,
no ledger entry, no `unmonitored` line) — and my read of `resume_all` confirms the only wipe (`None`) sits behind
the flag, so D25.2's seed survives by construction, not by luck.

**T3.2 — one setter, one clearer, `_go_live` untouched.** `grep -rn _outage_active --include=*.py` outside
`tests/` returns: init (`:56`), `begin_outage` → True (`:192`), `resume_all` → False (`:240`) and the two
comment references. `pause_all` explicitly does not set it (docstring `:205-209`; body unchanged in that
respect) — `test_p29_t3_05` asserts a `pause_all()`/`resume_all()` pair leaves every baseline alone.
`_go_live` does not appear in the diff at all. Inertness holds: a duplicate `nextValidId` runs `resume_all` over
an empty ledger and an already-False flag, changing nothing (`test_p29_t3_09`).

**T3.3 — the D40 re-baseline is exactly what RG-P29-1 authorised, and no more.** The diff of
`tests/test_d40_tws_lifecycle.py` contains four `_pause_start` → `_outage_start` renames with assertion content
unchanged (`:199`, `:364`, `:375`, `:402`) and one behavioural re-baseline, `test_d40_4_transient_drop_no_pause_ui`,
which flips **three** clauses: the drop's ledger assertion (`_pause_start == {}` → `SYM_A` recorded +
`_outage_active`), the re-seed assertion (`last_chart_price == before` → `is None`), and the gap line
(`"unmonitored" not in` → present). The **five surviving assertions are byte-identical**: no TWS_GONE
classification, the disconnected badge, `_tws_paused is False`, `is_paused is False`, `monitoring_paused is False`.
The file's remaining hunks are additive AC-D98.2 tick coverage inside that same case, not relaxations. The
`:445` value change the task predicted is the one that landed.

**G6 is owner-run and unclaimed.** The new suite's docstring says so and names what it proxies
(`tests/test_d98_outage_baseline.py:20-23`); the fence repeats it; no case opens a socket, drops a connection or
fires from live data. `tests/test_requirements`-style claims are absent. Correct.

## 4. P29-T4 (D99) — one source per transition, and the re-entrant case is really covered

`handle_page_ready` (`ui/lwc_bridge.py:693`) now clears `_queued`, `_outbox`, `_live_buf` (`:701-703`),
sets the flag, emits `{v:1, ops: list(_op_log)}` **once**, then `_replay_channels()`, returning the bar envelope or
`None`. `set_ready` (`:407`) is a pure flag setter — no emission, no drain. The `flush()` call is gone from the
transition. `_stage` has exactly one caller (`send_ops`, after `_op_log.extend`), so "discard, don't drain" cannot
lose an op that was never logged: every buffer member is already in the log.

**Discard vs drain is proven, not argued.** `test_p29_t4_01` sends 5 ops while not ready and asserts each
`(op, series, ts)` identity appears exactly once across the transition plus a full `apply_ops_to_bars`
reconstruction (the same fold the page applies). A duplicate or a loss fails the reconstruction, not just a count.

**The re-entrant op is neither lost nor doubled — for the path the criterion is about.** `test_p29_t4_op_during_
transition_is_logged_and_flushed_once` sends an `update_bar` **from the `opsEmitted` slot, mid-transition**: the
already-built replay envelope holds only the `set_bars`, the late op is the last `replay_log()` entry, the armed
`flush()` carries it exactly once, a second `flush()` is `None`, and the concatenated reconstruction equals the
expected series. I reproduced this independently (re-entrant send → replay `[ts=1]`, flush `[ts=2]`, one delivery
of `ts=2`). Two envelopes in one transition is the documented staging behaviour, not a duplicate of one op.

**A second corner, pre-existing and logged only (not routed):** a *channel* op sent re-entrantly **during**
`_replay_channels` is emitted twice in that transition — ready is already True inside the transition, so
`send_channel` emits immediately and the later full-log replay for that channel carries it again
(my probe: `overlays` envelope appears twice, `{'y':99}` twice). `_replay_channels` is unchanged by P29 and the
same trace exists at `3b92ce6`; channel envelopes are replace-all by contract, so the duplicate is idempotent on
the page, and no shipped caller emits a channel op from a channel slot. It does not contradict AC-D99.1 (bar ops)
and it is not a P29 regression, so I am recording it rather than attributing it to T4. Detail for whoever next
touches the channel path: `ui/lwc_bridge.py:721` clears `_channel_queue` once, then emits per channel from the
live log, while `send_channel` (`:553-565`) checks the already-True `_ready`.

**The webengine exclusion is honest.** P29 changed exactly one case in `tests/test_lwc_bridge.py` (the named
re-baseline); it added **no** skip and no marker, and the three gated ids
(`test_host_loads_ndt_chart_offline`, `test_render_terminated_recovery_wired`,
`test_interceptor_wired_blocks_non_ndt`) are untouched and still `@pytest.mark.webengine`. I ran
`test_host_loads_ndt_chart_offline` with the marker enabled: it **aborts (exit 134 / SIGABRT)** inside QtWebEngine
page construction, exactly as the BLOCKED attempt reported, and the pipeline's standard command
(`-m 'not webengine'`) deselects it. So the green verdict covers them as deselected, not as passed — a stated
environment limitation (DG88/AP-P6-4), not a hidden D99 failure. `set_ready`'s remaining production callers are
`_on_load_finished`/`handle_render_terminated` (False) and `handle_page_ready` (True); no caller expected the
deleted drain.

## 5. P29-T5 (the fence) and the delta record

**What it pins.** `tests/test_p29_fence.py` asserts, off live source: the requirements record's markers, the
D41–D95 per-id record, `#### D96`–`#### D100`, Journeys 78–81, `AC-D1.1`–`AC-D100.3`, A1–A245, R1–R185 and the
Current Tech Stack; `ENVELOPE_VERSION`/`COALESCE_MS`/`CHANNELS`/the three op-kind sets; the two store column sets
through `PRAGMA table_info`; `format_gap_report`'s signature and `SYM unmonitored HH:MM–HH:MM` shape; `Alarm`
with no touch/armed field; `evaluate_alarms`'s signature; and `update_group` accepting exactly four names, each
applying, with a fifth raising and the row untouched. No hash and no count is pinned, so a later phase can extend
the record without reddening it. I checked the "fails loudly" property of the map slicer: if the P29 note moved
after the skeleton marker the slice is empty and the file-name assertions fail — it cannot silently pass.

**Answer to the handoff's question — does it pin T1–T4 so a later phase cannot silently undo them?** Partly, and
honestly so. It pins the **invariant surfaces** (signatures, constants, schemas, the D100 rejection behaviour,
DG133) but **not** D96's ordering/transaction, D97's crossing direction, D98's session gate or D99's log-only
delivery. Those four live in the permanent suites (`test_d96_d100_store_atomicity`, the D97 cases in
`test_alarm_service`, `test_d98_outage_baseline`, `test_d99_page_ready_delivery`), which run on every full-suite
run; a later phase could rewrite an assertion inside one of them and the fence would not notice. That is exactly
what AC-P29-05-PINS enumerates ("the values P29 must not move"), and it matches the P27/P28 record-fence
precedent — so I am recording the limitation, not treating it as a miss.

**Read-only on the map, as required.** The fence only reads `docs/codebase-map.md`
(`test_the_map_carries_the_p29_note_and_every_prior_annotation`), and the P29-T5 result states no map edit was
made; the map's P29 note is Plan's content (it says it was regenerated against the build tree) and, like the
P28 `git add -A` sweep in `docs/memory.md`, rode into the build commit. Nothing in the fence writes or mutates it.

**The delta record is accurate for when it was taken.** `git diff --name-only 3b92ce6` yielded 13 tracked paths
(7 production + 3 re-baselined suites + `docs/codebase-map.md`, `docs/tasks/task-graph.json`,
`docs/tasks/execution_graph.json`); the four new suites and `docs/tasks/task_manager_notes_P29.md` were untracked
at that moment and are recorded as such. After `dcfdd60` the same command lists 18 (the four suites are now
tracked) — the record is not wrong, it is dated; and deliberately no test pins a diff, so the commit cannot
redden it. Every path is inside the phase allowlist; no scope breach.

**One record defect: the fence pins a retired test id** — `REBASELINED_CASES` requires
`test_exactly_on_alert_price_above_counts`, which P29-T2 renamed, so the map's "three named re-baselines" names a
test that no longer exists and the fence will redden if Plan corrects the note. **ESC-139**, `nice-to-have`,
BUILD, with the constraint (map is Plan-owned) spelled out so the rework cannot flail.

## 6. Standing duties

- **Mock-endpoint scan (production diff, blocking if hit): clean.** `mock|fake|stub|simulat` × the production
  hunks in `data/ services/ ui/` → 0 added lines. The four new suites use fakes only at their own boundaries
  (fake windows/timers/clients), never in production, and no production module imports a test double.
- **No new module, dependency, migration, settings key or wire change:** `config/`, `requirements*.txt`,
  `pyproject.toml` untouched; the two new suites and the fence are tests only; the fence's `PRAGMA` pin asserts
  the column sets did not move; `ENVELOPE_VERSION`/`CHANNELS` unchanged.
- **`docs/requirements/**` untouched by the build:** `git diff --name-only 3b92ce6..dcfdd60 -- docs/requirements/`
  is empty. The `[revises P4/D40]` label and both RG-P29-1 supersession notes were already in the base (they were
  the P28 rework's owner-approved amendment), so D41–P29 was not reopened by this batch. FI-P29-1 is reflected
  in the D40 test docstring rather than hidden.
- **G6:** owner-run, never claimed (suite + fence docstrings; no live assertion). Correct.
- **User docs — stale, routed.** The alarm-crossing semantics need no line: `usage.md:172` already says an alarm
  "fires only if the live price then crosses its level", which is what D97 now actually does. The **outage
  baseline** does: every reconnect — including a brief transient drop that shows no pause badge — now re-seeds the
  first tick and can print an `unmonitored` interval, and the guide's TWS Daily Lifecycle section
  (`usage.md:170-172`) describes that only for the TWS-gone morning login. Precheck found 5 doc candidates and
  **0 touched**; no P29 task declares `usage.md` (`doc_required:false` on all five). **ESC-138**, `should-fix`,
  TASK_MANAGER (a small separate doc task — the file is in no P29 footprint and `USAGE.md` is the same inode, so
  one edit covers both).

## 7. Findings and routing

| id | task | route | category | severity | one-line |
|---|---|---|---|---|---|
| ESC-138 | P29-T3 | TASK_MANAGER | gap | should-fix | `usage.md`'s TWS lifecycle section does not state that a *brief* drop also re-seeds the first tick and reports an unmonitored interval |
| ESC-139 | P29-T5 | BUILD | consistency | nice-to-have | the fence requires the retired D97 test id in the map note, so the record names a phantom test and cannot be corrected without reddening the fence |

No blocking or should-fix code findings: T1–T4 implement their criteria, and every claim I could re-run
(reproduction, rollback, trace-zero-SQL, the crossing table, the cold-start seed, the delivery counts,
re-entrancy) held on the live tree.

**Not routed (recorded only):** the channel-path re-entrant duplicate of §4 (pre-existing, idempotent, no shipped
caller, outside AC-D99.1); AR-P29-1's docstring wording of §1 (already gated by `in_transaction` assertions); the
P29 fence pinning surfaces rather than the four behaviours of §5 (what AC-P29-05-PINS asks for).

## 8. Close-out

`escalations.json`: 132 entries before this pass, **0 open** — no `addressed` flip to make, and no `PRE-*`
entry was waiting. This pass opens **ESC-138** and **ESC-139**; both are new, not re-diagnoses of prior findings,
and neither reuses an invariant already escalated in this phase (this is P29's first review pass and
`review_log_P28.md` closed with 0 open).

Full-suite verdict stands: **pass**, exit 0, 227.52 s (`docs/code_review/test_verification.json`).

Status: REVIEW_COMPLETE

---

# P29 rework verification (`f7a8be4`) — ESC-138 / ESC-139 closed, and the P29-T6 hermetic connect guard

**Pass:** rework verification, phase-final follow-up. Not a fresh tier decision — each item was re-derived on the
live tree, not taken from the rework's report. **Tree:** `f7a8be4` (two commits since the build):
`7b32e02` (P29 docs corrections + P30 plan approval) and `f7a8be4` (P29-T6). The mechanical precheck on disk
predates the rework, so I checked the delta myself rather than claiming its coverage.
**Verification:** `test_verification.json` — **pass**, exit 0, 257.77 s, no timeout, with **TWS genuinely
listening** (`lsof -nP -iTCP:7496` → `JavaApplication 1283 … *:7496 (LISTEN)`, confirmed again during this pass).

## 1. ESC-138 — the guide now describes D98 as shipped, without internals

`usage.md:172` is one bullet: *"Resume never triggers alarms by itself, and this holds for every drop, brief or
long: on reconnect the first tick for each symbol only re-seeds the price and nothing is evaluated on it, the gap
is reported as an unmonitored interval on the status bar (as above), and an alarm fires only once a later live
price crosses its level; a brief intraday drop still reconnects in the background with no pause badge."*

Checked clause by clause **against the code, not the prose**:

| clause | what ships |
|---|---|
| "first tick … only re-seeds … nothing evaluated" | `resume_all` captures `resuming_from_outage` and sets `session.last_chart_price = None` for **every** session only when a drop was recorded (`services/alarm_monitor.py:235,243`); the tick then seeds (AC-D25.3 / AC-D98.1) |
| "every drop, brief or long" | `_on_disconnected` calls `begin_outage()` **before** the TWS_GONE/other classification (`ui/main_window.py:2977`), and `_on_connected` is one `reconcile()` → `resume_all()` path (`:1907-1908`) |
| "gap … unmonitored interval on the status bar" | `format_gap_report` over the `_gaps` returned by `resume_all` — the unchanged owner-approved formatter |
| "fires only once a later live price crosses" | the D97 rule, `prev <= level < curr` / mirrored (`services/alarm_service.py:63-64`) |
| "brief drop … no pause badge" | the pause flags stay TWS-gone-only (AC-D98.1; `test_d40_4` still asserts the badge/flags) |

**No internals named:** no function, class, flag or field appears — "re-seeds" is the guide's own pre-existing
wording (it was in the superseded line too). **Inode:** `ls -li` gives `70268344` for both `usage.md` and
`USAGE.md`, same size (16327) and mtime — still one inode, so the single edit covers both names.
**One residual, judged not a defect:** AR-P29-9's unsignalled poll-recovery drop (a half-dead socket that heals on
the first attempt, so `connectionClosed()` never fires) is not re-seeded, so "every drop" is true of every drop
the app **signals** and the user can see; the residual was accepted in the task and is invisible by construction.
**ESC-138 → addressed.**

## 2. ESC-139 — the record can no longer be mistaken for a live test

`docs/codebase-map.md:649` now reads: *"…::test_exactly_on_alert_price_above_counts (P29-T2 renamed it to
`test_arrival_on_the_level_is_a_touch_not_a_cross` — 9.5 → 10.0 is a touch, 10.0 → 10.01 fires; the retired id
stays listed because `tests/test_p29_fence.py`'s `REBASELINED_CASES` pins this literal), …"*.

Both facts hold: the retired literal is present (so the fence is not reddened) **and** the live id with its exact
semantics is named. The parenthetical states *why* the retired id is still listed and *why* it must stay, so a
reader cannot mistake it for a live test — the ambiguity I reported ("a reader following it finds nothing") is
closed by disambiguation rather than by deletion. **No fence edit was made**: `git diff dcfdd60..f7a8be4 --
tests/` contains only `tests/conftest.py` and the new guard suite, and I ran `tests/test_p29_fence.py` → **13/13
pass**. **Residual, now stated in the record itself:** the fence still pins the retired literal, so a future
cleanup of that note must update `REBASELINED_CASES` in the same change; because the note says exactly that where
the next editor will read it, escalating the coupling a second time would be churn. **ESC-139 → addressed.**

## 3. P29-T6 — the hermetic connect guard (the reason the gate runs again)

The rework adds one session-scoped autouse fixture (`tests/conftest.py:161`) and one self-check module
(`tests/test_p29_hermetic_connect_guard.py`, 3 cases — P29-T6-01 plus the two-parameter precedence case), no
production change. My checks:

**(a) It is the socket layer, and that is the whole point.** The fixture replaces
`ibapi.connection.Connection.connect` with a raiser; `EClient.connect` allocates `Connection(...)` and then calls
`self.conn.connect()`, so the raise lands inside EClient's own `except socket.error` → `wrapper.error(…, 502,
"Couldn't connect to TWS")` → `self.disconnect()` → `wrapper.connectionClosed()` → `reset()` → `conn = None`,
`DISCONNECTED`. I read the pinned `ibapi` 9.81.1.post1 source to confirm that branch, and `iba_client.connect`
(`ibkr/client.py`) sets `ConnectionState.CONNECTING` **before** `super().connect(...)` — which is precisely why an
`EClient.connect` no-op would be wrong: it would leave `IBApiClient` stuck in **CONNECTING** with no 502, no
`connectionClosed()` and no reset, i.e. a third environment no green run has ever occupied, and the window's
disconnect handling would never run during construction. Raising at the socket layer instead drives the real
refused-connect path end to end, which is exactly what every prior green run did with TWS stopped.

**(b) A test's own patch wins; the guard returns.** The guard writes the **base-class** attribute, so a test that
patches `EClient.connect` (as `test_d87_d93_client_lifecycle.py` does) or `IBApiClient.connect` (as
`test_d98_outage_baseline.py::_make_window` does) replaces a different attribute and is effective immediately;
`monkeypatch` restores the value it saw (the guard) on exit. `test_a_test_own_patch_wins_and_the_guard_returns`
proves both sites — recorder receives the call, **no** 502 is emitted inside the patch — and then a fresh real
`EClient` is refused again with `conn is None` and `DISCONNECTED`. The fixture's `finally` restores the real
function at session end.

**(c) The four connect-asserting suites are byte-identical.** `git hash-object` against `git show dcfdd60:<path>`
for `test_d27_reconnect.py`, `test_d87_d93_client_lifecycle.py`, `test_d98_outage_baseline.py`,
`test_ibkr_handshake_gate.py` → four `IDENTICAL`. Run together with the guard suite: **32 passed**. (I also
re-ran the five P29 suites + fence under the guard: **49 passed**.)

**(d) No skip, no deselection, no pytest config change.** `pytest.ini` is absent from the rework diff; the only
`skip` token in the new module is the sentence "Nothing here is skipped or relaxed"; the verify command is the
pre-existing standard `-q -m 'not webengine'` (the same five gated cases as before, excluded by marker, not by a
new skip). The reworks's claim is accurate.

**Could the guard hide a real connect-path bug?** Not in any path the suite ever covered, and I can be specific
about the boundary. Before this change the suite's connect behaviour depended on the machine: with TWS down the
refused path ran (what the assertions were written for); with TWS up the socket opened and the ibapi reader thread
then **hung `threading._shutdown`** — so the success path never produced a passing assertion either way. The guard
turns "sometimes refused, sometimes hangs" into "always refused", deterministically, and it makes the refused
branch (502 → disconnect → connectionClosed → reset → state) load-bearing for every `MainWindow` construction, so
a regression **in that branch** now fails loudly across dozens of tests. Two honest residuals:
(i) a defect that only manifests **after a successful socket connect** (greeting parse, `EReader` startup,
`nextValidId` promotion) cannot be caught by the suite — it was never caught by it, and it is the owner's live run
(G6 / normal app use) that covers it; (ii) there is no opt-out: the real function is captured in the fixture's
closure and not exported, and patching `socket.socket` cannot help because the guard sits above it — a future test
that genuinely needs a real socket must edit `tests/conftest.py`. Neither hides a shipped bug; (ii) is a
maintainability sharp edge worth knowing, not a defect to fix now. Nothing here is "worse than the disease": the
disease was a suite that silently required the backend to be **down**.

## 4. Scope of the rework, and the standing duties

Per-commit attribution (the handoff's "nothing else moved" checked commit by commit, not on the range):

- `f7a8be4` — `tests/conftest.py`, `tests/test_p29_hermetic_connect_guard.py`, `docs/memory.md`,
  `docs/tasks/{task-graph,execution_graph}.json`, `docs/tasks/task_manager_notes_P29.md`. **No production path**
  (`git diff --name-only dcfdd60..f7a8be4 -- config/ data/ services/ ui/ ibkr/ main.py` is empty), no dependency
  file, no `data/db.py` schema, no settings key.
- `7b32e02` — docs only: `usage.md`, `docs/codebase-map.md`, my own `escalations.json`/`review_log_P29.md`
  (swept in), plus the **P30** plan artifacts (`docs/plan.md`, `docs/architecture.md`,
  `docs/plan_review_P30.md`) that belong to the approved P30 plan. Bundling a plan approval with a P29 doc-fix
  commit is the `git add -A` hygiene pattern already in `docs/memory.md`; it changed no P29 content and I am
  noting it, not escalating it.

Standing duties still hold: **G6** owner-run and unclaimed (the guard suite makes no live claim; the D98 and fence
docstrings still say so; the range's only G6 mentions are my own log text); **no new module/dependency/migration/
settings key** (the only new file is a test module); **`docs/requirements/**` untouched by the build**
(`git diff --name-only dcfdd60..f7a8be4 -- docs/requirements/` empty). The mock-endpoint invariant is untouched by
this rework (no production line added; the guard is a test-layer injector, not a production fake).

## 5. One finding, orchestrator-owned — `docs/memory.md` records the wrong mechanism

`docs/memory.md:289` (appended in `f7a8be4`) ends: *"The durable fix is an autouse conftest fixture that stubs
`EClient.connect`; the general rule is that an offscreen suite must never depend on the BACKEND BEING DOWN."* The
diagnosis and the general rule are right, but the mechanism is wrong: the shipped guard replaces
`ibapi.connection.Connection.connect` (`tests/conftest.py:161`), and an `EClient.connect` no-op is the shape this
task's AC-P29-06-GUARD and design note **explicitly rejected** (it leaves `IBApiClient` in CONNECTING with no 502
— see §3(a), which I confirmed from `ibkr/client.py`). This matters because `docs/memory.md` is read as established
fact by every agent and is marked "don't rediscover or contradict": a future worker could "restore" the rejected
no-op shape and cite memory for it. **No entry was added to `escalations.json`:** the schema routes only to
`BUILD` / `TASK_MANAGER` / `PLAN` / `REQUIREMENTS`, and `docs/memory.md` is user-primary / Orchestrator-append —
routing it to BUILD would violate file ownership, and I will not fabricate an invalid route. Owner: **the
Orchestrator**; the sentence should read "replaces `ibapi.connection.Connection.connect` with a raiser so EClient's
own 502 → disconnect → connectionClosed → reset path runs (a no-op on `EClient.connect` is NOT equivalent)". It is
a one-clause factual correction, not a gate blocker.

## 6. Close-out

| id | route | verdict |
|---|---|---|
| ESC-138 | TASK_MANAGER | **addressed** — `usage.md:172` states every clause of D98 as shipped, names no internals, one inode with `USAGE.md` |
| ESC-139 | BUILD | **addressed** — the map note names the live case and says why the retired literal stays; fence unchanged and 13/13 green |

`escalations.json`: 134 entries, **zero open**. No `PRE-*` entry outstanding. Full suite **pass**, exit 0,
257.77 s, with TWS listening. **P29 is gate-ready to close**, subject only to the Orchestrator correcting the one
`memory.md` clause in §5.

Status: REVIEW_COMPLETE
