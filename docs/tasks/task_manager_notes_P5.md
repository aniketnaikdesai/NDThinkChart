# Task Manager notes — Phase P5 / D46 (Batch 21)

**Run:** `fresh_graph`, 2026-10-25. **Inputs of record:** `docs/plan.md` § *Phase P5* (revision 2, **ACTIVE**,
`Status: READY_FOR_TASK_MANAGER`), `docs/architecture.md` § *Phase P5 — D46 increment*, `docs/plan_review_P5.md`
(APPROVED, activation corrections C1–C15 applied), `docs/requirements/requirements.md` (`D46.1`–`D46.13`,
`AC-D46.1`–`.13`, Journey 39, A91–A104, R76–R85, DG78–DG87), `docs/codebase-map.md` (P5-refreshed),
`docs/code_review/order_code_audit.md` (used only to check no symbol was missed), `docs/memory.md`.
**Validator clean:** `check_tasks.py` → `OK: 10 tasks validated, execution_graph.json written`.

This file replaces nothing: `docs/tasks/task_manager_notes.md` keeps the D41–D45 record.

---

## 1. The graph

Ten tasks, **strictly sequential**, one per approved wave. `touches_files` are exactly the Orchestrator's
ten-wave table and the plan's per-file map.

| Wave | Task | Group | Files (write) |
|---|---|---|---|
| 1 | `P5-T01` | window consumers | `ui/main_window.py` (1st), `tests/test_order_rejections.py`, `tests/test_d45_removal.py` (1st) |
| 2 | `P5-T02` | broker boundary — **unsplittable** | `ibkr/client.py`, `ibkr/bridge.py` |
| 3 | `P5-T03` | module + data-model twin | `ibkr/orders.py` (delete), `tests/test_order_builders.py` (delete), `data/models.py` (1st), `tests/test_ui_smoke.py` |
| 4 | `P5-T04` | pacing + notional cap | `ibkr/pacing.py`, `config/settings.py`, `tests/conftest.py`, `tests/test_d28_pacing.py` |
| 5 | `P5-T05` | order-fill sound | `services/sound_service.py`, `tests/test_sound_service.py` |
| 6 | `P5-T06` | `IdManager.reserve` only | `ibkr/id_manager.py`, `tests/test_id_manager.py` |
| 7 | `P5-T07` | stop/target storage: schema **and every reader** | `data/db.py`, `data/models.py` (2nd), `ibkr/account.py`, `ui/main_window.py` (2nd), `tests/test_stop_loss_target.py` (delete), `tests/test_account.py`, `tests/test_strategy_detection.py`, `tests/test_d27_position_id.py`, `tests/test_d27_account_partial_window.py`, `tests/test_d27_account_scoping.py` |
| 8 | `P5-T08` | the instrument — one coherent edit | `tests/test_d45_removal.py` (2nd) |
| 9 | `P5-T09` | surviving prose | `ibkr/error_codes.py` (comment only), `usage.md`, `USAGE.txt`, `tests/test_dock_d18_region.py` |
| 10 | `P5-T10` | the gate (verification only) | — |

**Dependency edges (encoded, not prose):**

```
P5-T01 → P5-T02 → P5-T03 → P5-T04 → P5-T05 → P5-T06 → P5-T07 → P5-T08 → P5-T09 → P5-T10
```

Every edge exists for a stated reason, and the reasons are different edge by edge:

- `T01 → T02`: the three bridge signals may only die once their receivers (three `.connect` lines + three slots)
  are gone; the reverse order raises `AttributeError` **at window construction** (loud, every window suite).
- `T02 → T03`: the module may only die once its sole importer (`ui/main_window.py:36`) and every registry reader
  (`_update_order_status`, the `_on_error` branch) are gone — otherwise collection breaks or `_on_error` raises
  `NameError` on any non-session TWS error.
- `T03 → T07`: **shared file** `data/models.py` — wave 3 removes `UserOrder`, wave 7 removes the four stop/target
  fields; same file, disjoint regions, so the edge is required anyway (write overlap) *and* the logical order is
  the plan's.
- `T04, T05, T06 → their predecessors`: **no logical dependency** — waves 4–6 touch files nothing else reads
  (plan § *Sequencing* says "independent"). The edges encode the plan's **forced strictly-sequential wave
  discipline** and the two mechanisms that depend on it: invariant **I-1** (the guard's token set may only name
  code that is already gone, and it lands once in wave 8) and the **mandatory per-wave residue grep**, which runs
  with the final token list from wave 1 onward and therefore presumes the earlier waves' end state. They are
  intentional serialisation, recorded here so a reviewer reads them as the owner's constraint, not as an oversight.
- `T07 → T08`: invariant I-1 — the ten names die across waves 1–6 and the storage dies in wave 7; the token
  migration lands only when every subject is gone.
- `T08 → T09`: the prose wave describes the end state the instrument asserts.
- `T09 → T10`: the gate closes the batch.

**Shared files with disjoint waves** (no two tasks in a wave share a file — there is only ever one task per wave):
`ui/main_window.py` in **1 and 7**; `data/models.py` in **3 and 7**; `tests/test_d45_removal.py` in **1 and 8**
(different line ranges: the walkthrough + docstring bullet in wave 1, `_SURVIVORS`/`_FORBIDDEN`/end-state
test/prose in wave 8).

**Wave 2 is one task by construction.** An emitter must never outlive its signal: `self.bridge.order_status.emit(...)`
against a deleted signal raises only when TWS sends an order callback, which no test produces — the suite would be
green while the app broke. If any future revision needs to split `P5-T02`, that is a stop-and-report, not a split.

---

## 2. Size, step-fit and the one exception

Targets honoured: `S`/`M` tasks are single-cluster; `L` marks deletion-heavy or judgment-heavy work, not a bigger
step budget. Step-count estimate per task (implement + test + report): T01 ~18, T02 ~12, T03 ~12, T04 ~12, T05 ~12,
T06 ~8, T08 ~16, T09 ~10, T10 ~16 — all inside the ~20 target.

**Exception — `P5-T07` (deliberate, ~32-step cap, not split).** Ten files (four production + six test), because
**R84/DG85 forbid splitting the schema from its readers**: a half-landed column drop does not fail loudly, it puts
a stop value in the Portfolio's **Group** column and reads as a strategy-detection bug. Measured size is ~40 edited
lines across the ten files, four of them mechanical (the three seeders, `test_account`, `test_strategy_detection`),
so it is not the D41 L-size *deletion* profile that killed three workers (memory 2026-10-15; R76). Splitting would
also leave the suite red between waves and destroy the single-owner property of the index-shift guard.

**Pack-budget exception — `P5-T07`'s context pack has 11 `read_files`** (budget ~8) for the same reason: every
`touches_files` entry must be readable before it is written, and the task cannot be split. All entries carry tight
line ranges and four are deletion/mechanical reads; the pack stays well under ~150 lines.

---

## 3. What each context pack protects (so Build does not "tidy" a survivor)

Encoded as ACs and pack text, not left to the plan:

- **`IdManager` + `get_id` (six callers)** survive — `P5-T06` is `reserve` only; AC2 requires the six call sites
  (`ui/main_window.py:1095`, `ibkr/market_data.py:42,74,90,103`, `ibkr/realtime_bars.py:31`) to still import.
- **`nextValidId` is the CONNECTED transition**, not order plumbing (A102) — frozen in `P5-T02`'s contracts and
  proven by `test_d40_tws_lifecycle`.
- **`classify_error` / `error_msg` / the generic 8000 ms line** — frozen; `P5-T01` and `P5-T10` assert the exact
  `Error [<code>]: <TWS string>` text and the 8000 ms duration per code (201/103/202).
- **`pacing_manager` / `PacingManager` / `PacingExceeded`** — frozen in `P5-T04`, with both conftest resets kept.
- **`play_alarm` / `render_alarm_chime` / the `"alarm"` key** — frozen in `P5-T05`; `_effect` collapses to the
  alarm effect only.
- **`TradeGroup` / `Position` / the Portfolio (8 columns)** — `P5-T07` drops only the four stop/target fields; the
  panel is not edited and `test_positions_table_is_eight_columns` must stay green.
- **False positives that must not be swept:** ICT `order_blocks`/`orderBlocks`/`_render_order_blocks` and watchlist
  `sort_order` are survivors (R83); `reserve` is deliberately **not** a guard token (13 units / 11 files, mostly
  "preserve(s/d)"); `orderStatus`/`openOrder`/`execDetails` are measured by `name not in IBApiClient.__dict__`,
  never `hasattr` (AP-D46-14).

---

## 4. Deviation records (all graph-level, none changes a requirement)

1. **`P5-T10` is `task_type: "doc"` with an empty `touches_files`.** The gate writes no code and no test; that is
   the only non-code `task_type` the validator's "code-writing tasks need a non-empty `touches_files`" rule
   accepts. Its artefacts are the recorded numbers in its result file. Flagged here so nobody reads "doc" as "a
   documentation task": the AC set is the eight verification measurables.
2. **`P5-T01` carries one test the register's book does not list** — the parametrised 201/103/202 case. The plan
   requires it (`AP-D46-4`) because `AC-D46.3` needs a *positive per-code* proof and the book forbids a new file;
   the register's `D46.5`/`A95` under-count it (`RG-D46-5`). No new file, no new dependency.
3. **`P5-T07` also owns the `ui/main_window.py:3065` comment** ("…the exact mirror of the D28.6 inverse on the
   **close-order path**") — assigned at activation (C11) as requirements DELETE row 22's third site, which no other
   wave owns. It is in `P5-T07`'s AC8.
4. **Plan citation correction (no decision changed):** the plan cites `data/models.py`'s `Study` as the live
   `field(default_factory=dict)` user. `Study` is **not** in that module; `Alarm.params` (`:37`) is the live user.
   `P5-T03`'s AC2/contracts/memory note say `Alarm.params`, so the worker keeps the `dataclass`/`field` imports for
   the real reason.
5. **Wave 4–6 edges are serialisation, not logic** (see § 1). Recorded because a reviewer comparing `dependencies`
   against the plan's "independent of 1–3" sentence would otherwise read them as spurious.

---

## 5. Flags and escalations

- **No `ESCALATED_TO_PLAN`.** Decomposition needed no architectural decision the canonical artifacts do not
  settle: the migration mechanism (`S47`), the name-keyed read and index shift (`S48`), the guard's token
  mechanism and exact-match rule (`S44`), the KEEP boundary and its consumers (`S46`) and the forced wave order
  (`S43`) are all decided and were carried into the packs verbatim.
- **Requirements flags: none raised by this run.** The six plan Flagged Issues are already adjudicated and recorded
  as `RG-D46-3`–`RG-D46-9` (`docs/plan_notes.md`, open, non-blocking) — they are requirements-*text* corrections,
  not blockers, and every AC as written is satisfiable via the plan's stated interpretation. **Do not task**
  `AC-D46.2`'s literal `hasattr(IBApiClient, …) is False` (unsatisfiable through `EWrapper`), `AC-D46.10`'s
  "keeps the concurrent case" (it is rewritten), or `D46.12`'s SQLite 3.54.0 citation (the app links 3.53.1; both
  support `DROP COLUMN`).
- **`ESC-061` is moot** (the module it wanted annotated is deleted) — **no task implements it**; the Code Reviewer
  closes it as moot. **`ESC-062` is folded into waves 1/7/9** (four comment sites + one test rename), **no new
  task**. **`ESC-063` is satisfied** by the map refresh; `ESC-059`/`ESC-060` stay BUILD-owned and are not absorbed
  (ESC-060's behavioural half is moot once the columns go; its documentation half is superseded by wave 9's trail).
- **`DG78` item (2) stays open by decision** — an orderId colliding with a live session reqId keeps taking the
  session path. No task may reorder `_on_error` and no test may pin the collision as desired behaviour (A94).

---

## 6. Notes for the Build wave runner / reviewer

- `tests/test_d45_removal.py` is written twice by design (waves 1 and 8). It must never be dispatched concurrently
  with itself; the chain makes that impossible.
- Every delete-only task (`T03`, `T07`) ends with a `git status` of its file list plus an import check — the D41
  worker-death failure mode is a half-edited file reported as done.
- Detail that the plan measured and the packs state, so no worker re-derives it: `trade_group_id` moves from
  `row[14]` to `row[12]`; the three seeders go 11/11/11 → 9/9/9 names/placeholders/values; `test_sound_service`
  is **9 → 7** cases (not 8 → 6); `test_id_manager` is 8 → 4 with **two** cases rewritten.

---

## 7. Amendment log — P5-T08 pack fix (2026-10-25b, wave 8 re-dispatch)

**Trigger.** Wave 7 delivered the D45-column drop and wave 8's guard reddened on it: with `_FORBIDDEN` at 80
substring tokens, the end-state scan reported exactly two offences, both against the removal mechanism itself —
`data/db.py:200`, `for _column in ("stop_loss", "take_profit")` inside `_migrate_schema`. The worker stopped
instead of widening its footprint or inventing an exemption, which was the right call.

**Decision (Task Manager, not a Plan escalation): authorised a file-scoped exemption**, mirroring the shipped
`tests/test_d41_removal.py:108-110` / `:180-182` precedent:

```python
_ALLOWED_IN_FILE = {"stop_loss": {"data/db.py"}, "take_profit": {"data/db.py"}}
def _allowed_in(rel: str, token: str) -> bool:
    return rel in _ALLOWED_IN_FILE.get(token, ())
```

consulted **only where the repo-relative path is known** (`_token_offences` and the raw-text twin's line loop),
never inside `_matches`. Rationale: a migration that removes a column must name it; that is the one legitimate
occurrence, and the alternative resolutions cost more than they buy —

- **AST function-scoped allowance limited to `_migrate_schema`** — rejected. The instruments are flat set-based
  (`_scan_file` returns `set[str]` identifiers/strings, shared by three tests), so enclosure tracking would mean
  redesigning a frozen helper and the twin's line-based loop to fix one line of migration. It buys no extra
  strictness on the dimension that matters: the compensating in-file assertion below already catches a use anywhere
  in `data/db.py`, in any function.
- **Restructuring/removing the tokens** — rejected. Dropping `stop_loss`/`take_profit` from `_FORBIDDEN` would lose
  the net over `ui/`, `ibkr/`, `services/`, `config/` and `data/models.py`, which is precisely what AC2 requires;
  the plan measured these as substring tokens for that reason.

**AC-text consequence (recorded plainly, per instruction).** AC2's original parenthetical — "do not add
`_MIN_SUBSTRING` exemptions for them" — survives verbatim: the two tokens are still substring-matched, and
`_matches("stop_loss") == "stop_loss"` is unchanged, which is why they are still caught in every other file and in
any longer unit. What AC2 as originally written did **not** say, and is now true, is that the net has one scoped
hole. AC6 previously claimed "zero AST offences … over `data/`" — that sentence **contradicted the delivered
design** and has been amended to name the carve-out rather than left asserting something false. A new **AC7** (with
**T71**) states the exemption's exact shape, its one-file scope, and the guarantee that keeps AC2's *intent* intact:
in `data/db.py` the two tokens may appear **only** as string constants that are elements of the tuple iterated by
the loop whose body contains a `DROP COLUMN` statement — no identifier/attribute use anywhere in the module, and no
other SQL string (`CREATE TABLE`, `SELECT`, `PRAGMA`) may name them. So: the migration *names* the columns; nothing
*uses* them; the DDL never names them.

**Scope of the amendment.** Description part (f), AC6 wording, AC7 + T71, one `expected_artifacts` line, two
`read_files` entries (`data/db.py:167-205` and `tests/test_d41_removal.py:100-115`, both marked read-only) and two
`new` contracts. `touches_files` is unchanged (`tests/test_d45_removal.py` only) — **`data/db.py` is not edited**: it
is already correct. Dependencies unchanged (`P5-T07`). No other task, AC, test or token count touched; `_SURVIVORS`
16 and `_FORBIDDEN` 80 stand as measured. `metadata.status` stays `READY_FOR_BUILD`.

### 7a. Downstream read-across flagged (not changed)

- **`P5-T10` AC2 must be read as "the guard reports 0", not "an ad-hoc grep reports 0."** After wave 8 the
  guard is green because of the scoped exemption; a *fresh* sweep written inside wave 10 (same 80 tokens, same five
  dirs) will see `data/db.py:200`'s two subject strings again and re-create this exact stop. T10's pack is untouched
  here (out of pack-fix scope): whoever dispatches it should either rely on `tests/test_d45_removal.py` as the
  instrument or, if it re-implements the sweep, apply the same `_ALLOWED_IN_FILE` scope. `P5-T09`/`P5-T10`'s
  doc-trail greps (AC5 / AC7) are unaffected — they inspect prose around `stop_loss`/`take_profit` in `USAGE.txt`
  and `usage.md`, not the source tree.
- **Pre-existing validator noise, unrelated to this fix.** `check_tasks.py` exits 1 on three `read_files` entries in
  already-`done` tasks whose target files waves 3 and 7 deleted: `P5-T03` -> `ibkr/orders.py`,
  `tests/test_order_builders.py`; `P5-T07` -> `tests/test_stop_loss_target.py`. They were accurate when those waves
  were dispatched and are harmless now (those tasks never re-run). Left as-is per the pack-fix rule that no task other
  than `P5-T08` is altered; `P5-T08` itself validates clean and `execution_graph.json` regenerated with it.

### 7b. Second amendment — P5-T10 gate repointed, stale packs pruned (2026-10-25c)

**`P5-T10` AC2 (and T21, description (b), two `read_files` whys, one pack memory note, `expected_artifacts`).**
The wave-10 gate previously said the residue sweep must report "0 offences" over an 80-token list it would run
itself — which would have re-created the T08 stop against `data/db.py:200`. It now names the guard as the
instrument (`pytest tests/test_d45_removal.py -q`: AST net, `ui/` twin, end-state test) and states the carve-out
explicitly: `stop_loss`/`take_profit` are permitted in `data/db.py` only, as the `DROP COLUMN` loop's subject tuple,
via `_ALLOWED_IN_FILE`/`_allowed_in`; every other file still forbids all 80 tokens. Any per-file breakdown must call
the guard's own helpers (`_source_files`, `_token_offences`, `_allowed_in`), never a re-implemented sweep — and a
hand-rolled sweep that reports those two is residue-free, not failing. No AC count, test count, dependency or
footprint changed; the numbers recorded in AC8 (pre-P5 41 / 40 vs post-P5 0 / 0) are untouched and still true.

**Stale `read_files` pruned.** Files deleted by waves 3 and 7 were still listed on done tasks, so
`check_tasks.py` only validated by tolerance. Removed: `P5-T03` -> `ibkr/orders.py`, `tests/test_order_builders.py`
(pack 5 -> 3 files); `P5-T07` -> `tests/test_stop_loss_target.py` (pack 11 -> 10). Their `touches_files` entries stay:
those deletions are the tasks' real output footprint, and the validator correctly warns rather than errors on them.
`check_tasks.py` now exits **0** (3 benign "pure-output file" warnings, no errors), 10 tasks validated.

**`P5-T08` untouched in this round** — its pack (part (f), AC6, AC7 + T71, 8 read files) is frozen as dispatched.

### 7c. P5-T10 footprint — a verification-only task's declared footprint is its result artifact (2026-10-25d)

**Symptom.** The gate ran every check green, then could not be stamped: `worker_selfcheck.py` reported
`"footprint_ok": false, "violations": ["docs/build/results/P5-T10.json"]`. Cause, read from the script: the
footprint comparison is `declared --files` vs `touches_files` and nothing else — `pats = []` makes *every* declared
path a violation. Omitting `--files` is no better: the `git status` fallback exempts `docs/build/` but still sees the
~64 in-flight sibling edits from other waves.

**Fix (one field, plus pack consistency).** `P5-T10.touches_files` is now `["docs/build/results/P5-T10.json"]`;
`task_type` stays `doc` (it writes no code and no test — `check_tasks.py:99` only exempts `doc` tasks from the
*touches_files must be non-empty* rule, and `worker_selfcheck.py` never looks at `task_type`, so changing it would
fix nothing). The same path was added to `context.read_files` (`1-21`, the existing skeleton, overwritten) so the
pack obeys the every-`touches_files`-entry-is-read rule, and `expected_artifacts` now names the file and its
`status: done`. Nothing else changed: every `P5-T10` check, AC, test, dependency and `test_command` is exactly as
it passed.

**Why this shape, not a self-check exemption.** A `task_type`/`--files`-side carve-out would let a *real* code task
sneak unlisted edits past the footprint check; declaring the one file the task is allowed to write keeps the check
strict for every other task. Recorded as the rule for this phase: **a verification-only task's footprint is its own
result artifact, and it must pass it to the stamp.** Verified by replaying the script's comparison: the declared
path yields no violations, while an undeclared sibling path (`data/db.py`) still violates.

`check_tasks.py` exits **0** (same three benign pure-output warnings on the done tasks `P5-T03`/`P5-T07`, which record
their deletions).

### 7d. New task `P5-T11` — ESC-065, an unowned file gets an owner (2026-10-25e)

**Why a new task.** ESC-065 (`routed_to: BUILD`, `task_id: null`) is about
`tests/test_d42_nonregression.py::test_full_offscreen_suite_is_green`, which nests a whole-suite pytest in a
subprocess (~70 s) and has cost four gate runs across two batches, twice dying `-11`. No P5 task owned the file, so
the rework path had nothing to route to. `P5-T11` now owns **that file only** (`touches_files` and `test_command`
both scoped to it). Owner's decision recorded: **option (a)** — keep the invariant in-suite and stabilise the child;
do not delete it, do not move it out of the repo.

**Shape (translation of the escalation's `suggested_direction`, not a re-diagnosis).** `_INNER_EXCLUDED` = the three
wall-clock gate modules (`test_d24_smoke_gate.py`, `test_d28_4_gate.py` — `GATE_PER_TICK_MS = 50.0`,
`test_d28_tick_burst_baseline.py` — `per_tick_ms < 50.0`) plus the two Qt-teardown-sensitive ones
(`test_session_overlay.py`, the documented SIGSEGV at its `panel` fixture; `test_d28_5_teardown.py`, which closes
windows mid-reader-thread and pumps `processEvents`). The child gets `-p no:cacheprovider`, a unique `DB_PATH`, a
unique `--basetemp`, `PYTHONDONTWRITEBYTECODE=1`, and **both** `--ignore` and `--deselect` for this module/test so
recursion is impossible even if one flag is edited away.

**Deliberate deviation from the suggested "unique temp cwd", with evidence.** Three suite modules read
**repo-relative** paths — `tests/test_candlestick_wick.py:13,40,65` (`Path("ui/candlestick_item.py")`) and
`tests/test_dock_layout.py:68` (`Path("ui/dock_layout.py")`) — and `pytest.ini` sets `testpaths = tests`. A temp cwd
would make the stabilised node **deterministically red**, re-creating the very nondeterminism ESC-065 reports. So the
child keeps `cwd = repo` and gets its isolation from the four flags/env above. This is stated in the task description
as "do not 'fix' it", in the pack's memory notes, and in AC1, so a reviewer does not read it as an omission.

**Discrimination is a deliverable, not a hope.** AC3/T31 require both a durable unit test (monkeypatch
`_run_inner_suite` -> `returncode=1` with a stdout tail, assert `AssertionError` carries it) and a real-tree check
(a scratch `tests/test_zz_inner_discriminator.py` with `assert False` must redden the node, then be deleted; the
result records both outcomes and `git status --porcelain` shows only the edited file). A stabilised invariant that
can no longer fail would be worse than the flake.

**Sequencing.** `dependencies: ["P5-T10"]` — one edge, so it runs after the phase gate; **nothing depends on
`P5-T11`** (verified: zero dependents), so it gates no rework and cannot delay `P5-T08`'s ESC-064 rework. Eleven
tasks, ten edges, a single chain T01→…→T11; `check_tasks.py` exits 0. Execution graph: 11 nodes / 10 edges.

**Traceability note (no escalation).** The in-suite node's domain narrows from "whole suite" to a stable subset;
AC4/T41 therefore require the module and node docstrings to name the owners of whole-suite-green evidence — the
external gate (`verify_tests.py` -> `docs/code_review/test_verification.json`) and `P5-T10`. The old "runs the rest
of the offscreen suite" sentence exists only inside that test file (checked: no `requirements.md` text uses it), so
no Requirements flag is raised; the Code Reviewer should count the external gate's result, not a nested flake.

**Incidental.** The reset archived every `docs/build/results/*.json` into `_archive/`, so `P5-T10`'s result-file
`read_files` entry was dropped (the file no longer exists to read); its declared footprint stays in `touches_files`
as a pure-output file. `check_tasks.py`: 4 benign "pure-output file" warnings, 0 errors, exit 0.
