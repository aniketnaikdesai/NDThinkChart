# Plan Review — Phase P26

Plan-Section-SHA256: 0dd2cc7795a9cc26d84454fe68efec719854d878781c31c0c5075febbdb79189
Architecture-Section-SHA256: 9fae9d43898fe0117972029bb8de7906d6f8b1c913fa3390d1ae8d9d04715066

**Review status:** `APPROVED`
**Pass type:** `final_pass` — no prior `plan_review_P26.md` existed, so the full Validation Method ran to
completion and then finalised in the same pass. Phase gate: open (`review_log_P25.md` ends
`Status: REVIEW_COMPLETE`, newer than the P25 build's terminal `READY_FOR_REVIEW`).
**Inputs:** `docs/requirements/requirements.md` § P26 (`Status: READY_FOR_PLAN`), `design_gaps.md`
DG130/DG131, `docs/plan.md` § P26, `docs/architecture.md` § P26, `docs/codebase-map.md`.
`docs/code_review/escalations.json`: **no open entry** (0 open, none routed to PLAN).
`plan_lint.py --phase P26`: **PASS, 0 failures, 0 warnings** (re-run by this pass).
`docs/pending_doc_sync.md`: absent.

---

## Validation summary

1. **Requirements coverage — PASS.** All 15 criteria (`AC-D71.1`–`AC-D76.3`), Journeys 68–70, A225–A229,
   DG130/DG131 and R165–R169 appear in the traceability table with a named architecture seam and a wave.
   Gates **G3/G4** are named as owner-run and never claimed; `AC-D76.3` is carried by P26-04's fence.
2. **Architecture completeness — PASS.** Existing-first tech stack (no new dependency, `contextlib` is
   stdlib), four changed components with responsibilities, in-memory-only data model, five `[existing]`
   integration points, Frozen Interfaces, Non-Functional Approach, eight risks. Every S-P26-1…S-P26-7
   carries a rationale **and** the rejected alternatives.
3. **Consistency — PASS.** Each claimed present-tense defect was re-read in the code and matches the
   requirements' verified ledger: the replay pre-check counts `RT_BARS` only and then loops every entry;
   `_option_reissue_leg`/`_option_reissue_spot` never cancel; `_replay_subscriptions` re-runs the whole
   pass; `_issue_wave_chunks`' cap branch returns with the watchdog armed (`ui/ticker_session.py:1266-1278`);
   `on_historical_data_end` returns at `_wave_may_complete` without disarming (`:1448`);
   the 162 branch never pops `_req_bars` (`:1486-1511`); `_cancelled_history_req_ids` is only ever added to;
   `queue_wave_plans` omits `_backfill_failed_req_ids` (`:1199-1215`); the coalesce gate requires
   `_history_req_ids` (`ui/main_window.py:3073`); `IBKRNotReady` falls back to `wait = 1.0` and re-arms.
4. **Plan quality — PASS.** Four sequential waves (M/M/S/S) with covers / depends-on / files / ordered
   deliverables / exit condition / do-not list. No task-level dependency graph, no per-task test specs, no
   individual-task decomposition — each wave is one body of work (a seam plus its suite).
5. **Task Manager readiness — PASS.** The decisions a task graph would otherwise have to invent are all
   explicit: the union pre-check arithmetic, the batch reservation's admit/stamp rule, the two resolvers
   and their retire order, the settle predicate, the resume step list, the two-generation tag prune, the
   per-wave failure reset, and the epoch-guarded deferral.
6. **Existing-repo compliance — PASS** (all five checks; detail below).
7. **Frozen Interfaces — PASS** (all five checks; detail below).
8. **Codebase map — PASS** (all five checks; detail below).
9. **Doc sync drained — PASS.** `docs/pending_doc_sync.md` is absent.

### Existing Repo Compliance (step 6)

- **Codebase Summary present and substantive — PASS.** A 17-row site table stating what each site *encodes
  today* (including the exact current defect), not a restatement of the fix.
- **Existing stack respected — PASS.** Every current-stack item appears as `[existing]` before any addition;
  nothing is replaced or deprecated; no new dependency, module, migration or settings constant.
- **Labels — PASS.** System Components, Data Model and Integration Points each label every item
  `[existing]` / `[new]` / `[new/changed]`.
- **Additive-only — PASS.** Existing behaviour is not redesigned beyond the six defects; the changed work is
  separated from what stays (`_wave_may_complete`, the bound formula, the planner, the D54 block, §7).
- **Summary ↔ proposal consistency — PASS.** Every entity the proposal treats as `[existing]` appears in the
  Codebase Summary.

### Frozen Interfaces (step 7)

- **Verbatim — PASS.** Checked token-for-token against the repo: `subscribe` / `unsubscribe` /
  `unsubscribe_all_of_type` / `has_subscription` / `entries_of_type` / `replay_all`, the four tags, `_Entry`'s
  field set (`ibkr/subscription_manager.py`); `PacingExceeded.wait_seconds`, `request_wait_seconds`,
  `throttle`, `realtime_available_slots`, `realtime_wait_for_slots`, `realtime_wait_seconds`,
  `record_realtime_slot`, `historical_wait_seconds`, `record_historical_slot`, `refund_historical_slot`,
  `reset_for_tests`, the `pacing_manager` singleton (`ibkr/pacing.py`); `per_load_historical_cap` (body
  `max(1, MAX_HISTORICAL_PER_600S // 4)`), `queue_wave_plans`, `_issue_wave_chunks`, `_wave_may_complete`,
  `_schedule_wave_continuation`, `_history_wave_watchdog_bound_ms` (formula, 1/5 and 1/20, `_hist_window`),
  `_arm_`/`_disarm_history_wave_watchdog`, `on_historical_bar` / `_data_end` / `_error`, `is_superseded`,
  `flush_pending_bars`, `mark_history_request_issued`, `register_history_request` (the public wrapper at
  `ui/ticker_session.py:1352` — the entry is not a dangling private name) (`ui/ticker_session.py`);
  `_replay_subscriptions`, `_finalize_stranded_history_wave`, `_on_session_history_wave_timeout`,
  `set_backfill_state`, `clear_backfill_indicator`, `_is_superseded_history_req`, `_finalize_history_wave`
  (`ui/main_window.py`); `subscribe` / `unsubscribe` / `cancel_all` (`ibkr/realtime_bars.py`);
  `req_mkt_data` / `cancel_mkt_data` / `req_historical_data` / `cancel_historical_data`
  (`ibkr/market_data.py`); `IBKRNotReady` / `classify_error` (`ibkr/error_codes.py`).
- **Nothing under construction frozen — PASS.** Every frozen entry is `[existing]`; `replay_all`'s *behaviour*,
  the new pacing members, the appended keyword-only parameter and every changed branch are explicitly under
  **NOT frozen**.
- **Nothing missing — PASS.** Every cross-module `[existing]` interface the new code calls is listed. The two
  intra-module calls the new code adds (`record_request_slot` inside `pacing.py`, `_unregister_req_id` inside
  `main_window.py`) are named verbatim in the wave deliverables, so no worker builds against them sight-unseen.
- **Owning modules resolve, no duplicates — PASS.**

### Codebase Map (step 8)

- **Sections resolve — PASS** (main.py, `chart_assets/lwc/`, `config/`, `data/`, `ibkr/`, `services/`,
  `spikes/lwc/`, `tests/`, `ui/`, `ui/overlays/` all exist).
- **Key files exist — PASS** (spot-checked `spikes/lwc/spike_probe.py`, `ui/overlays/__init__.py`,
  `services/option_spread_engine.py`, `ui/option_spreads_panel.py`).
- **No stale entries — PASS** (P26 adds no module, so no entry is created or removed; the 23 generated
  test-impact rows stand).
- **Status labels — PASS** (no row is touched by P26, so every cell keeps its `[existing]`-equivalent P6-legend
  reading; the P26 note names only planned suites, backtick-free per the file's own naming rule).
- **Index-sized — PASS** with one observation (below).

---

## Deliberate judgments

### FI-P26-1 — `AC-D75.1`'s "no new request" vs `AC-D72.3`'s "the oldest queued plan is issued"

**Adjudicated: Plan's reading is faithful, not a silent reinterpretation.** The conflicting sentences are, on
the resume side, *three* statements — `D72`'s Expected behaviour ("A subsequent load resumes issuing
oldest-first"), Journey 69's postcondition ("the next load issues the oldest queued chunk first") and
`AC-D72.3` — against one outlier clause in `AC-D75.1`. The tie-break is measurable, not rhetorical:
`AC-D72.3`'s measurable is "issued-plan order + pacing-manager call log" (the resume), while `AC-D75.1`'s own
measurable is "cancel spy not called; queue identity/contents; pending-prefetch flag" and **does not test its
last clause**. The literal alternative ("issue nothing") makes the park a permanent silent stop — the outcome
`D72`'s defect text explicitly rejects — and leaves `AC-D72.3` unsatisfiable.

Therefore this is **not** escalated to REQUIREMENTS. There is no product decision left for the analyst: every
measurable is satisfied under exactly one reading, and the surviving question is a wording confirmation Plan
has already recorded (FI-P26-1, suggested direction: "no *duplicate* request"). If the owner instead means
"issue nothing", `AC-D72.3` and Journey 69 must be restated first — which is the analyst's act, not Plan's and
not this review's.

### AP-P26-3 / S-P26-4 — the settle rule (parked is marked at cap-yield, bound released at last end)

Verified against the real call order, not the prose:

| Case | Code path | Outcome |
|---|---|---|
| last chunk **ENDs normally** | `:1437` discards the reqId **before** `:1448`'s check, so a settle call there sees the updated in-flight set | settle true → disarm + stop continuation; `_wave_may_complete()` false (queue non-empty) → **no finalise**. This is R-04's failure at exactly the site the requirement names. |
| last chunk **errors 162** | `:1486-1511` re-queues the plan and re-arms the continuation/watchdog and returns — no settle site is reached | retry stays bounded; if the retry 162s again it falls to the final error path (`:1521` discard, `:1530` check), settles (parked + idle) and leaves the remainder parked with no bound — correct, not stranded. |
| last chunk **stranded** | `_history_req_ids` keeps the id, so settle is false; the handler's `parked and not _history_req_ids` guard is false | finalised once with the stranded reason and the `AC-D16.4` shortfall — `AC-D72.2`/R166 hold. A premature disarm cannot hide this: the disarm and the guard test the **same** predicate. |
| **disconnect** | `_cancel_history_requests` clears `_wave_parked`; `_on_disconnected` → `_finalize_stranded_history_wave` clears the queue (`:2849`) and advances the generation | queue dropped — Journey 69's documented edge, unchanged. The guard lives in the timeout handler only, so it cannot block the disconnect path. |

**Verdict: airtight for the four named cases.** Residual, not a defect: `prime_aggregator`'s pacing-slip
re-entry (`:1652-1659`) re-arms the bound through the default continuation path while a pacing deferral is
live — legitimate for that deferral, and per-load, not per-tick, so it cannot produce D76's unbounded loop.

### S-P26-1 / S-P26-2 — union pre-check + `generic_batch` against `ibkr/pacing.py`

- `throttle()` is `request_wait_seconds()` → `record_request_slot()`; `_min_interval` is fixed at construction
  as `1/MAX_REQ_PER_SEC` (20 ms at 50/s), so the plan's `1.0 / settings.MAX_REQ_PER_SEC` is the same number.
- The reservation is a **token-bucket borrow**, and the arithmetic is sound: admit when
  `elapsed >= (n-1)·interval`, n sends inside, **one** stamp at close. Long-run rate is conserved (the n
  sends are paid for by prior idle plus one interval of future spacing), and because `__enter__` raising means
  the `finally` never runs, a refused batch stamps nothing.
- `generic_n = len(pending) - rt_n` counts exactly the entries that will pass through `throttle()`: RT sends
  do **not** hit the 20 ms gate (`RealtimeBarsManager.subscribe` calls `record_realtime_slot`, not
  `throttle`), and `S0_TICKS` has no production registration (only the import, the `include_types` literal and
  tests reference it), so it contributes 0 and the count stays correct if a hook is ever added.
- `_batch_remaining` needs an `__init__` initialiser — forced by the new branch and inferable; recorded as an
  observation, not a decision left to a worker.

Frozen `subscribe` + the four doubles: the per-type resolver keeps `subscribe` at five arguments, and the two
pre-existing replay suites stay green **in principle**, verified:
`_FakeClient.rt_bars` is append-only with a no-op `cancelRealTimeBars`, so the new RT retire step does not
change `len(fake.rt_bars)` (`n_before + 2` still holds); `test_p7_t07_t13…` builds a `SimpleNamespace` stub
with no `_replay_serial` and asserts one scheduled `(2000, fn)` — the plan's `getattr` read makes that work;
`test_p7_w2_watchdog::test_t11…` calls `_schedule_wave_continuation(wait)` positionally and still gets an
arm, so the appended keyword-only default is safe.

### R-01 completeness — both halves, not just the loop

The duplicate-subscription half is the retire phase, and it is real: `RT_BARS` → `_unregister_req_id` +
`rt_manager.unsubscribe` (verified: `_reissue_rt` already unregisters routing, so the resolver cancels the
TWS line exactly once); `OPTION_LEGS` → `_option_req_ids.pop` + `cancel_mkt_data` (verified:
`_option_reissue_leg` only repoints its own maps and never cancels — exactly the leak). Retire runs only after
every reissue succeeds; on a mid-pass raise the unwind retires the **new** ids and rebinds the old ones, and
because the registry key now moves only in the retire phase, the registry is byte-identical on the error path.

### R-11 / R-13 / R-14 / R-16, and R-04 + R-14 as one lifecycle

R-01 → P26-01, R-04 → P26-02, R-11 → P26-03 (D73), R-13 → P26-03 (D74), R-14 → P26-02 (D75), R-16 → P26-02
(D76). Every criterion has a named red-first case (P26-01 (a)/(b)/(d), P26-02 (a)/(b)/(c)/(e), P26-03
(a)/(b)/(d)/(e), P26-04's fence). The R-04+R-14 grouping is **substantive, not cosmetic**: the park is what
creates a queue-only session, and the coalesce gate is the only path by which a park ever terminates, so a
park-only or a coalesce-only fix leaves the other criterion measurably red. P26-02's case (c) asserts the joint
contract in one fixture (cancel spy silent, queue head identity preserved, `_pending_prefetch` intact,
indicator leaves `parked`, issued count inside the pacing budget).

### FI-P26-2 / FI-P26-3 boundaries

Both are stated, with their reason and their owner-facing consequence:
`FI-P26-2` — a parked wave still gets the D54 T0+10 s verdict and its missing-days line, because `AC-D54.*`
is out of scope by this phase's Non-Goals; it is a different statement from the watchdog reason `AC-D72.1`
measures, and the AC's measurable (finalise spy + queue length) is unaffected. Not a blocked contradiction —
the requirement set itself resolves it.
`FI-P26-3` — parked work survives a same-triple reload, not a teardown/disconnect; verified against
`_finalize_stranded_history_wave` and Journey 69's edge, and extending it would need persisted wave state
(the migration this phase forbids).

No Requirements Escalations were raised; `docs/plan_notes.md` is unchanged.

---

## Editorial corrections made at activation (no architectural decision introduced)

1. **System Components (a):** "three `set_cancel_hook` registrations" → **"two"** — only `RT_BARS` and
   `OPTION_LEGS` are replayed, and they are the two S-P26-3, the Data Model table and the P26-01 deliverable
   name.
2. **System Components (d):** the parked guard was attributed to `_finalize_stranded_history_wave` /
   `_on_session_history_wave_timeout` jointly, which would have stopped a disconnect from stranding a parked
   wave and contradicted Journey 69's edge. Aligned to S-P26-4 and P26-02 deliverable 3: the guard lives in
   the timeout handler; `_finalize_stranded_history_wave` is unchanged. The NOT-frozen phrase "the parked
   guard in the stranded path" now reads "in the watchdog-timeout path".
3. **S-P26-2 + the pacing component:** "falls through to the unchanged gate **and raises**" replaced with the
   precise rule — the extra send is admitted only if the interval has genuinely elapsed since the last real
   stamp (no stamp occurs inside a batch), so the **reservation** can never be spent twice. As written before
   the edit, an over-spend assertion could not fail the way the text described.

No settled content needed trimming; no change to plan.md § P26 beyond the status flip.

## Observations (recorded, not fixed, not blocking)

- `_batch_remaining` and `_replay_serial` are new instance attributes whose `__init__` initialisation is
  implied rather than spelled out — forced by the new `throttle()` branch and the `getattr` read.
- "A successful issue clears the reason and the announced latch" (P26-02 deliverable 2) must be read as
  covering both issue sites (`_issue_wave_chunks` and `_retry_silent_chunk`); that is the only reading under
  which a stale `_wave_deferral_reason` cannot mislabel a later timeout.
- Map `(root)` row: the 2026-11-19 generator run emits a slash-suffixed `(root)` token that `plan_lint` reads
  as a path; Plan kept the previous slash-free form and recorded the generator fault in the P26 note. **Noted,
  not fixed** — the owner of that fix is `update_codebase_map.py`, not Plan.
- The map's P26 note is ~17 lines, above the index rule's ~5; it matches every prior phase's note in that
  file, so no change is requested.
- P26-01's `Files`/exit condition includes `tests/test_history_backfill.py` (P26-02's list), which drives a
  cap-yielded wave through identical reloads. Under the resume change it should still converge (the queue
  drains oldest-first and per-chunk persist is idempotent), and AP-P26-6 provides the escalation path if an
  existing expectation must move.

## Task Manager readiness

**Yes.** Task Manager can build a valid task graph without making a new architectural decision: the union
pre-check, the batch reservation, the two resolvers and their order, the settle predicate, the resume steps,
the tag-prune window, the per-wave failure reset, the epoch deferral and the fence's pinned values are all
stated. No new module, dependency, migration or settings constant; sizes M/M/S/S; D1–P25 unopened apart from
the labelled `[revises P7]` / `[revises P23]` behaviour those decisions themselves describe.

## Final decision

**`Status: APPROVED`** — `docs/plan.md` § Phase P26 flipped to `READY_FOR_TASK_MANAGER` at activation
(see the section's closing line). Required Changes: **none**. Requirements Escalations: **none**.
Task Manager may proceed.
