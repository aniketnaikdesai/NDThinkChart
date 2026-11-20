# Plan Review — Phase P29 (D96–D100): persisted state and alarm evaluation

Plan-Section-SHA256: ef98484c6610060252cac0c8128107e073eb8fef04cd1c977be7136a62fc78ea
Architecture-Section-SHA256: 86a741d532803dbc9853193a1fbbd6e9cfcb0b0d703f6b6e48fb771c4eb00205

**Pass type:** `retry_1_of_3` — targeted re-validation of RC-1…RC-4 (judged against source, not the revision
note), then finalize. `plan_lint` PASS (0 failures, 0 warnings) per the preamble. Phase gate **open**
(`docs/code_review/review_log_P28.md` = `REVIEW_COMPLETE`), no P29 provisional review exists, and the last
full pass covered steps 1–9 — so this pass **activates**.

---

## Review Status

**Status: APPROVED**

`docs/plan.md` § P29 carries `Status: READY_FOR_TASK_MANAGER` (activated by this review). The canonical
`docs/architecture.md` § P29 was validated in place, with **one editorial correction** recorded below
(normalising a stale row to content the same section already states and this review already validated — no
new architectural decision).

---

## Revision verification (RC-1…RC-4)

| Item | Verdict |
|---|---|
| **RC-1 — the cold-start gate** | **FIXED, verified against the shipped call paths.** `begin_outage()` returns immediately when `self._host._sessions` is empty; `_outage_active` has one setter (`begin_outage`) and one clearer (`resume_all`); `pause_all` no longer touches it; `_go_live` is untouched. (a) Cold start walks clean: a failed/pre-handshake connect reaches `connectionClosed()` → `_set_state(DISCONNECTED)` → `bridge.disconnected` → `_on_disconnected` → `begin_outage()` with `_sessions` empty → returns, arming nothing; at the first `nextValidId`, `_on_connected` runs `reconcile()` (creates the monitor, seeds the 1m cache at `alarm_monitor.py:287-289`) then `resume_all()` with `_outage_active` False → no re-seed, no ledger, no line; the cached close survives. Confirmed no production path creates a session before the first handshake on an ordinary launch (`get_or_create_session` is reachable only from `load_chart`/pop-out restore (both refused while disconnected)/`reconcile`), so the ordinary "app started before TWS" launch is closed. (b) All four D40 cases still arm: each calls `reconcile()` (creating sessions) **before** the drop — `test_d40_1` at `:181`, `test_d40_2` at `:227`, `test_d40_3_gap_accounting_per_symbol` at `:360`, `test_d40_3_alarm_created_mid_pause_stays_paused` at `:390`, `test_d40_4` at `:430` — so the session predicate is true without editing `_go_live`, and the gate is not `MainWindow._ibkr_connected` (which `_go_live` never sets). The TWS-gone path is unaffected: `begin_outage` runs first on the same drop, and `pause_all`'s `setdefault` is redundant-but-harmless; `gaps` come from the ledger regardless of the flag, so a pause with no session still reports the staged interval via `_start_monitoring`. |
| **RC-1 residuals** | **Honest and acceptable; none reintroduces the silent miss.** (i) a poll-detected drop with no `connectionClosed()`: the plan states it; on the shipped ibapi the socket becomes `None` only inside `Connection.disconnect()`, which calls `wrapper.connectionClosed()` two statements later, so a real network pull always records the outage — only a clean first-attempt recovery inside that window is uncovered, and any failed attempt records it. (ii) late delivery: one extra re-seed + one interval line at the *following* connect, consumed by that resume — conservative (suppresses an evaluation), never a fabricated trigger. (iii) session created by alarm CRUD before the first handshake: the gate arms, so the first handshake re-seeds that session's cache seed **and** `begin_outage` records it (it carries the alarm), so a gap line *is* produced — the interval starts at the failed attempt rather than at the alarm's creation, i.e. at most one backoff delay of the window is understated, but nothing is claimed as detected and no crossing is silently swallowed. |
| **RC-2 — the fifth read** | **FIXED.** Plan now states five reads in four cases: `:199`, `:364`, `:375`, `:402` are renames with unchanged content; `:445` (inside `test_d40_4_transient_drop_no_pause_ui`) **changes value** to "`SYM_A` present in `_outage_start` at the drop, cleared after the resume" — and that is the right shape: the case's subject is the transient resume/baseline, not an empty map, and the ledger assertion is the mechanism S-P29-3 defines. The tick sequence is anchored to `AC-D98.2` and is correct under the shipped rule for a `cross_above` alarm at `100.5`: seed close `102` (`prev` becomes 102, no evaluation) → bar at/below `100.5` (no fire: `102 <= 100.5 < 100` false) → bar beyond (fires once: `100 <= 100.5 < 101`). AP-P29-7 and the codebase-map note carry the corrected count. |
| **RC-3 — the three frozen helpers** | **FIXED, verbatim against source.** `def _session_has_live_alarms(self, session) -> bool:` (`services/alarm_monitor.py:161`) · `def _emit(self, env: dict) -> None:` (`ui/lwc_bridge.py:520`) · `def _replay_channels(self) -> None:` (`ui/lwc_bridge.py:717`) — each with its owning module; all three `[existing]`/unmodified, none under construction. |
| **RC-4 — the group-dialog suites** | **FIXED.** P29-01's exit condition names `test_p9_group_dialog`, `test_p9_group_payload`, `test_p9_active_group`, `test_p10_groups_dialog_lock`; all four exist, and all stay green unchanged — the dialog only ever passes `visible`/`locked` (the two checkable columns' `UserRole` payloads, `ui/drawing_groups_dialog.py:120,128,270`), and the direct call site uses `locked=True`. |

---

## Validation lines

- **Requirements coverage** — PASS: `AC-D96.1`–`AC-D100.3`, Journeys 78–81, A241–A245, R181–R185 and G6 each
  map to an S-P29 decision and a wave; `AC-D98.3` recorded as not activated (its condition is false); D98's
  absent numbered journey stated (`requirements.md` P29 carries none). Unchanged by the revision.
- **Architecture completeness** — PASS: stack, components, data model, integrations, Frozen Interfaces, NFR,
  AR-P29-1…9 with rationale and rejected alternatives.
- **Architecture consistency** — PASS: the gate now holds on the shipped path; `begin_outage`'s early return
  is described identically in S-P29-3, the Codebase Summary row, the `_outage_active` Data Model row,
  AR-P29-9 and the D98 NFR bullet; `pause_all` "does not set `_outage_active`" agrees in all five places.
- **Plan quality** — PASS: five milestones (M/S/M/M/S), dependency shape `01 ∥ 02 ∥ 04 → 03 → 05` justified
  on the harness/layer split, no task graph, no per-task test specs.
- **Task Manager readiness** — **PASS**: the wave that owns the gate now carries a decidable rule and a
  pinning case that drives the failing ordering (pre-handshake `connectionClosed()` → `nextValidId` → cached
  close preserved), plus an inert-duplicate-`connected` case; no architectural choice is left to a worker.
- **Existing-repo compliance** — PASS: substantive Codebase Summary (per-site today→disposition), existing
  stack first and unchanged, `[existing]`/`[new]`/`[new/changed]` labels on System Components, Data Model and
  Integration Points, additive-only edits.
- **Frozen interfaces** — PASS: every entry verbatim against source with a resolving owning module; the three
  previously missing `[existing]` members are now frozen; nothing under construction is frozen (every changed
  body, incl. `begin_outage`, sits under **Not frozen**).
- **Codebase map** — PASS: P29 note at `:625` states no new production module; `(root)` row slash-free; the
  read-rename count now reads "five reads in four D40 cases — four renames and one value change"; the
  selection hints name the four group-dialog suites.
- **Doc sync** — PASS: `docs/pending_doc_sync.md` absent.
- **Boundaries re-confirmed** — G6 owner-run and explicitly unclaimed (P29-03 exit condition + P29-05 record,
  no case asserts a live socket drop/fire/TWS price); **no new module, dependency, migration, settings key or
  wire change** (file set unchanged: `data/study_store.py`, `data/drawing_store.py`,
  `services/alarm_service.py`, `services/alarm_monitor.py`, `ui/main_window.py`, `ui/lwc_bridge.py`,
  `ui/lwc_host.py`, three re-baselined suites, four new suites, docs); sizes M/S/M/M/S; exactly **one**
  `[revises …]` label in the phase (`[revises P4/D40: AC-D40.4's gap/baseline clauses]`), the rest
  `[new in P29]`/`[extends …]`.
- **Re-baseline inventory — now complete (no fourth member).** Re-enumerated from source rather than from the
  plan: all 14 `evaluate_alarms` call sites are in `tests/test_alarm_service.py` and only
  `test_exactly_on_alert_price_above_counts` changes; the downstream tick-driven alarm suites have no
  arrival-at-level fixture; all 18 `set_ready(True)` test sites have an empty queue except
  `test_queue_until_ready_holds_pre_ready_ops`; the `_pause_start` reads are five in four cases, all disclosed.
  The fix's own ripple was checked too — `pause_all`'s flag removal affects only the staged path, which
  re-seeds itself (`_start_monitoring` sets `None`), so `test_d25_4_alarm_added_while_disconnected` and
  `test_d40_3_alarm_created_mid_pause_stays_paused` pass unmodified and need no re-baseline.
- **Requirements escalation** — `RG-P29-1` (`AC-D40.4` / Journey 35 step 3 vs `AC-D98.1`) remains open in
  `docs/plan_notes.md` with the requirements analyst; `requirements.md` is unchanged (still
  `READY_FOR_PLAN`), FI-P29-1 still describes it accurately, and it does not gate the build (P29 builds
  `AC-D98.1`'s default; `AC-D98.3` not activated).

---

## Editorial correction applied at activation (recorded)

`docs/architecture.md` § P29 § *Codebase Summary*, the `tests/test_d40_tws_lifecycle.py` row, still carried
the **pre-revision** count ("four further reads" / "the four reads become `_outage_start` (assertion semantics
unchanged)") while P29-03 deliverable 6, AP-P29-7, the revision notes, S-P29-3 and the codebase-map note all
state five reads in four cases with `:445` changing value. Normalised the row to that already-validated
content ("five reads … that case's own at `:445` … **its `:445` assertion changes value** … the other **four**
reads … unchanged"). No decision was introduced and no wave changes; the stale cell was the only remaining
inconsistency found in the cumulative files.

---

## Non-blocking observations (recorded, not gates)

1. `begin_outage()` now runs `_session_has_live_alarms()` (an `AlarmStore` read) on **every** drop rather than
   only on TWS-gone drops. That widens an existing exposure (the same helper already ran on the classified
   path and in `pause_all`) — a raising DB call inside `_on_disconnected` would skip the rest of that slot.
   Pre-existing pattern, worth one sentence if the file is touched again.
2. Residual (iii)'s understated interval start (at most one backoff delay) is noted in the review table above;
   the plan's wording ("never a lost trigger") is accurate about triggers, and a gap line is still produced.
3. The `:445` replacement should assert the ledger **before** `nextValidId(1)` (where `begin_outage` recorded
   it) and emptiness after the resume — the plan's deliverable 6 says exactly that ordering, so a worker
   following it lands correctly.

---

## Final Decision

**Status: APPROVED**

- `docs/plan.md` § P29 → `Status: READY_FOR_TASK_MANAGER` (flipped by this review; the only activation).
- `docs/architecture.md` § P29 validated in place, with the one editorial correction above.
- `docs/plan_review_P29.md` this file; section stamps re-taken for this cycle.
- `RG-P29-1` stays open with the requirements analyst and does not gate the build; `docs/plan_notes.md`
  untouched by this pass.
- Task Manager may proceed. No other agent is invoked from here.
