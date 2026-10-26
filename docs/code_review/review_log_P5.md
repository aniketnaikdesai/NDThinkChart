# Code Review — Phase P5 (D46 / Batch 21) — the phase-final pass

**Pass:** full pass (mandatory for a phase-final review; a light pass was also unavailable — `ui/main_window.py`,
`data/models.py` and `tests/test_d45_removal.py` each carry two scoped tasks, and P5-T07/P5-T08 are size L).
**Scope:** `P5-T01 … P5-T10` (all ten `done`), `precheck.json` scope, 0 fail_fast, 0 pre-existing `PRE-*` entries.
**Ground truth consumed, not re-derived:** `precheck.json` (files/footprint/overlaps/doc candidates already
verified), `test_verification.json` (**pass**, exit 0, 79.63 s — this is the "did the suite pass" answer),
`build_log.md` (through wave 121, `Status: READY_FOR_REVIEW`), all ten `results/_archive/wave*_P5-*.json`,
`task-graph.json` § P5, `order_code_audit.md`, `requirements.md` (D46/A99 + the nine `SUPERSEDED BY D46/A99`
annotations), `architecture.md`/`plan.md`/`codebase-map.md` § P5 and `escalations.json`.

## Verdict

The batch does what it says. **The app is free of order interaction**: no `placeOrder`/`cancelOrder`/
`reqGlobalCancel` definition or call site, no order token anywhere in `ui/ services/ data/ ibkr/ config/ main.py`
(other than the authorised `data/db.py` migration subject), no order affordance, `ibkr.orders` unimportable, and
a walkthrough that drives every surviving affordance records zero transmits. **The migration is safe on a real
database** — I reproduced it on a hand-built pre-P5 file and on a half-applied one. **The row-index shift is
name-keyed**, not index-corrected. **The tests that were adjusted still assert what their names claim** and none
was weakened. **The instrument discriminates** — but it has one real hole at the single authorised exemption, and
the phase's own "suite green" node is flaky by construction. Four findings: two `should-fix` (instrument hole,
nested-suite flake), two `nice-to-have` (a Plan-owned doc contradiction, two stale section headers). `ESC-060`,
`ESC-061`, `ESC-062` and `ESC-063` are closed with verification; **`ESC-059` stays open** (its pack artefact was
never repaired).

## Findings

### ESC-064 — the one authorised exemption is file-wide; its required "named-not-used" assertion does not exist  (`P5-T08`, BUILD, quality, should-fix)

The Task Manager authorised `_ALLOWED_IN_FILE` **only** on condition that the exemption be *named-not-used*:
P5-T08 AC7 and description item (f) require the end-state test to prove that in `data/db.py` each token is a
string constant inside the `DROP COLUMN` loop's subject tuple — "never an identifier/attribute/argument, never
inside another SQL string constant (`CREATE`/`SELECT`/`PRAGMA`)".

The shipped instrument exempts by **file and token only**, so it exempts every shape:

- `tests/test_d45_removal.py:268-275` — `_allowed_in(rel, token)` keys on `(file, token)`, nothing else.
- `:303-310` `_token_offences()` returns identifiers **and** string constants; `:343-346` applies `_allowed_in`
  to both, so an `ast.Attribute` hit is exempted exactly like the migration's subject constant.
- `test_p5_end_state_all_removed_members_absent` (`:851-991`) never parses `data/db.py`; it asserts dataclass
  fields, the factory signature, module/suite absence and the migrated/fresh schema. The module docstring
  (`:16-18`) and the `_ALLOWED_IN_FILE` comment (`:214-216`) both *claim* "never as code" and "the end-state
  test's AST half asserts exactly that" — the claim is unbacked.
- P5-T08-T71 was defined as a one-off `python -c` probe, so nothing durable enforces the clause.

Proof, not argument: with `data/db.py` containing `return row.stop_loss` and
`SQL = 'SELECT stop_loss FROM positions'`, `_token_offences` reports three raw offences and the effective list
after `_allowed_in` is **empty**. A re-introduced read, or a `SELECT`/`PRAGMA` naming the column inside that file,
would pass the acceptance instrument. The DDL half *is* covered separately (the fresh-DB check at `:980-991`), so
the hole is exactly the code-use/non-`DROP`-SQL shapes.

The authorisation itself is honoured: **no second exemption** exists (`_ALLOWED_IN_FILE` = the two tokens ×
`{data/db.py}` only), the tokens do **not** escape the file (source grep over `ui services data ibkr config
main.py` → the single line `data/db.py:200`; only `data/__pycache__/db*.pyc` also matches), and
`_matches('stop_loss') == 'stop_loss'` still reports the token everywhere else. So this is not the "token escaping" finding — it is the missing assertion the
exemption was granted against.

### ESC-065 — `test_full_offscreen_suite_is_green` is flaky by construction and has cost four gate runs  (BUILD, quality, should-fix)

`tests/test_d42_nonregression.py::test_full_offscreen_suite_is_green` spawns `pytest` over the **whole** suite
(~70 s) in a subprocess and asserts `returncode == 0`. Any single flake in ~1022 tests reddens it, and the nested
run itself segfaults intermittently:

- first `verify_tests.py` run this batch: `/tmp/verify_run1_fail.json` — `verdict: fail`, `exit_code 1`,
  68.76 s, tail `FAILED tests/test_d42_nonregression.py::test_full_offscreen_suite_is_green` (one inner `F`);
- `build_log.md` P5-T10 (waves 120 **and** 121) records two invocations returning inner pytest `-11` (SIGSEGV)
  in the same node, with clean re-runs green;
- the independent clean run is green (`test_verification.json`: pass, exit 0), and P5-T10's own full-suite gate
  ran 1022 tests green (I re-counted: `1022 tests collected`).

**Decision: yes, this is a finding worth routing.** It is not a product regression and today's evidence is sound,
but the phase's "suite green" evidence is nondeterministic and each retry is a full-suite run. The invariant must
stay asserted — the question is which process owns it (in-suite stable subset vs the external gate that already
exists). Routed to BUILD with both directions stated, no decision made for them, and an explicit "do not delete
the invariant".

### ESC-066 — `architecture.md`'s D45 section still says the order module and two utilities survive, unmarked  (PLAN, consistency, nice-to-have)

`:4815-4828` (block headed "**Retained and deliberately inert (not leftovers — A90)**") lists `ibkr/orders.py`
(retained, one docstring note), `config/settings.py::MAX_ORDER_NOTIONAL` ("**not** deleted") and
`ibkr/pacing.py::order_limiter` ("**not** edited by this batch"); `:4868-4869` says `ibkr/orders.py` is "frozen
**at its API** with one permitted docstring note". All are contradicted by the tree and by the same file's P5
section (`S39`/`S45`/`S46`). The inconsistency is internal: the storage half (`:4648-4652`, `:4831-4834`), `S29`
(`:4664`), `S35` (`:4670`) and `AR-D45-10` (`:4957`) **do** carry markers, and the section banner
(`:4620-4622`) promises markers on "the two frozen rows below" — those are the unmarked ones. This is the
R85/DG84 hazard D46.13 exists to close, and S45's own warning about the map ("a Build worker reading [it] would
preserve what must go, and no token scan catches prose").

### ESC-067 — two stale section headers survived the prose sweep  (BUILD, consistency, nice-to-have)

`ibkr/bridge.py:42` still reads `# Account & Orders` above the four account/position signals (no order signal
exists — asserted `hasattr(IBBridge, …) is False`); `tests/test_dock_d18_region.py:153` still reads
`# ── T48-T03 — panel present, signal wiring intact ─────` above the case ESC-062 renamed to
`…_summary_signals_exposed`. Neither is visible to the guard by design (AST ignores comments; the raw-text twin
is `ui/`-only). Prose-only, one line each.

## Verified with evidence — no finding

**Order interaction is genuinely gone (independent re-derivation).** `grep` over `ui/ services/ data/ ibkr/
config/ main.py` for `placeOrder|cancelOrder|reqGlobalCancel` and for every P5 token (`order_status`, `open_order`,
`exec_details`, `_on_order_*`, `order_registry`, `UserOrder`, `OrderRateLimiter`, `order_limiter`,
`MAX_ORDER_NOTIONAL`, `render_fill_blip`, `play_fill`, `order_fill`, `.reserve(`) → **zero hits**; `import
ibkr.orders` → `ModuleNotFoundError`; no order affordance remains in the UI (`Flatten|Close Position|Kill` →
only ICT `showKillzones`). The two halves of the chain were removed together (wave 2 deleted the three
`EWrapper` overrides and the three bridge signals in one task, so no emitter outlived its signal — verified by
reading `ibkr/bridge.py` and `ibkr/client.py`).

**Migration: safe on a real database, idempotent, cannot half-apply (my own probes, not the worker's word).**
`data/db.py:188-204` guards each `DROP COLUMN` with `_table_columns(table)` inside `_migrate_schema`.
- Pre-P5 fixture (16-column `positions` with rows + unique index + FK + `sqlite_sequence`, and the 8-column
  `trade_groups`) opened through `DB()`: both tables end without the four columns; rows `[(1,'SPXW',1),
  (2,'AAPL',None)]` preserved; `trade_groups` row preserved; `sqlite_sequence` `[('positions',2),('trade_groups',1)]`
  preserved; `idx_positions_symbol_con_id` still enforces the unique pair (duplicate insert raises
  `IntegrityError`); `PRAGMA foreign_key_list` keeps `trade_group_id → trade_groups.id`;
  `foreign_key_check` empty; `integrity_check` `ok`; second `DB()` open leaves `sqlite_master` byte-identical.
- Half-applied state (simulated crash: `positions.stop_loss` already dropped, `trade_groups` untouched, one row):
  the next open finishes the job and keeps rows/index.
- Statement-atomicity claim in the comment is **true**: with this connection's `isolation_level == ''`, DDL is
  autocommitted (`in_transaction` is False after `ALTER TABLE`, True only after DML), so each of the four
  statements lands independently and the next open completes an interrupted sequence. No index/trigger on the
  dropped columns ever existed in this repo (`git log -S stop_loss -- data/db.py`), so `DROP COLUMN` cannot fail
  on a legacy file for that reason. Environment: Python 3.11.15 / SQLite 3.53.1 (≥ 3.35 required).

**Row-index shift is name-keyed, not index-corrected.** `ui/main_window.py:3065-3134` reads the bulk path
through `cursor.row_factory = sqlite3.Row` with an explicit 13-name column tuple and constructs `Position` by
name (`trade_group_id=row["trade_group_id"], id=row["id"]`); no positional reader of `positions` exists anywhere
(`grep "FROM positions"` → the two name-keyed selects, the prune's `account` filter, and tests' explicit column
lists). `_upsert_position` (13 columns incl. `updated_at`) is name-listed in both the INSERT and the `DO UPDATE`.
The new guard `tests/test_d27_position_id.py::test_p5_t07_bulk_load_maps_trade_group_id_by_name` seeds a
non-null `trade_group_id` and asserts it survives with the right `id` — a maintained `row[12]` would return the
id value and fail, a stale `row[14]` would raise.

**Docs say "dropped", not "kept"/"cleared".** `USAGE.txt:86-90` ("The app stores no stop or target at all: the
database columns are dropped the first time this version opens the database"), `usage.md:154` ("dropped by a
one-time migration … every row intact and only those two values lost") and `usage.md:203`; the deleted
`tests/test_order_builders.py` line is gone from the test command (`usage.md:164-167`). Wording matches the code
(guarded, effectively once) and the row-preserving behaviour I measured.

**The nine `SUPERSEDED BY D46/A99` annotations are accurate and consistent.** Each sits on the stale
"kept / no migration / unchanged / retained" claim it supersedes (`requirements.md:591, 1184, 4337, 4399, 4540,
4566, 4584, 5017-5022`), including the two places where the tail sentence still describes ESC-060's
"cleared by the next live update" mechanism (`:4337-4343`, `:4399-4400`) — those tails are covered by the file's
declared convention ("D45's text is left as written so the reversal is visible", `:5017-5022`, which also states
"the behavioural half of ESC-060 is moot — there is no column to write") and by the A99 row at `:5230`
("kept → cleared → dropped"). `architecture.md`/`plan.md` carry the equivalent section banner
(`architecture.md:4604-4607`, `plan.md:1960-1962`). No annotation overstates: all say dropped-by-migration, none
claims the values survive.

**The adjusted tests test what their names claim; none was weakened.**
- `test_sound_service.py` 9 → 7: the two fill-blip cases died with `render_fill_blip`; `test_creates_both_files_once`
  → `test_creates_alarm_file_once` keeps the idempotence assertions (path exists, second call returns the same
  mapping, mtime unchanged) and drops only the deleted `fill` key; `test_write_wav_is_valid_pcm16` now renders the
  alarm chime. Coverage preserved; no assertion removed from a surviving subject.
- `test_id_manager.py`: four `reserve` cases deleted with the method; the monotonic case rewritten on `get_id()`,
  the concurrency case re-based (8 × 200) and still asserting no duplicate ids across threads.
- `test_order_rejections.py`: registry cases deleted with the registry; the non-order case still asserts the
  generic line; a new parametrised 201/103/202 case asserts **both** `[code]` and TWS's own text (the AC-D46.3
  substance), and the `classify_error` cases stand.
- `test_dock_d18_region.py`, `test_d27_flat_rows.py`, `test_d27_position_prices.py`, `test_account.py`,
  `test_strategy_detection.py`, the three `positions` seeders, `tests/conftest.py`, `test_d28_pacing.py`: every
  edit is the removal of a deleted subject or a column/index shift forced by D45/D46; the assertions that remain
  are unchanged or (the new bulk-load case) stronger. No `skip`/`xfail` was added anywhere in the phase
  (`git diff` scan).
- `test_d45_removal.py` grew: the ten named survivors moved into `_FORBIDDEN` — loading the module gives 16
  survivors and 80 tokens, with exactly those ten names present in `_FORBIDDEN` and absent from `_SURVIVORS` —
  `_EXACT_ONLY` is tested **before** the substring branch and `reserve` is absent (covered by
  `hasattr(IdManager, 'reserve') is False`), the three absence pools grew, and the new end-state test measures each
  removed half by the right instrument (`hasattr` / `__dict__` / `find_spec` / `__dataclass_fields__` /
  `inspect.signature`).

**The instrument would catch a regression (probed, not assumed).** A synthetic resurrection in `ui/`
(`from ibkr.orders import orders`, `position.stop_loss`, `'order_limiter'`) produces 3 offences; the pre-removal
tree scores hard (my run of the final guard over a `git worktree` at HEAD: 131 AST offences across 16 files and
287 twin hits across 6 files). The phase's recorded pre-P5 baseline (41 offences / 10 files, 40 twin hits) is
arithmetically self-consistent — the ten enumerated per-file counts sum to exactly 41. The residual gap is
ESC-064 only.

**P5-T10's orchestrator-finalised result is honest.** Its numbers check out: `1022 tests collected` matches; the
guard is 9 cases ("Guard green: 9 passed"); 201/103/202 do reach the generic 8000 ms line
(`ui/main_window.py::_on_error`); `ibkr.orders` is unimportable; the migration claims reproduce. It discloses
`finalized_by: orchestrator (worker hit step limit post-verification)` and carries the two selfcheck footprint
flags including the nested SIGSEGV. Its `files_changed` names `docs/build/results/P5-T10.json`, which the precheck
reports as "not on disk" — that is the archive step (all ten results now live under
`docs/build/results/_archive/`), not a missing artefact. Note for the record: declaring the task's footprint as its
own result artefact makes `footprint_ok: true` vacuous for a verification-only task; harmless here because the
task writes nothing else, but it is not evidence of footprint discipline.

**Mock-endpoint containment (standing invariant): clean.** Every added production line was scanned for
`mock|fake|stub|simulat` crossed with `endpoint|client|service|server|api|harness`; all hits are planning prose
describing test doubles (`architecture.md`/`plan.md`/`requirements.md`: "mocked-client walkthrough",
`_StubNewsManager` in already-deleted test code). No production module gains a mock endpoint and none imports a
test fake. `IBApiClient.connect` mocking in the walkthrough stays inside `tests/`, injected at the boundary.

**Precheck's `unattributed_working_tree_changes` are the delivered D45 batch, not unreported P5 edits.**
`ui/active_portfolio_panel.py`, `ui/ticker_session.py`, `tests/test_d27_flat_rows.py`,
`tests/test_d27_position_prices.py`, `tests/test_d38_events_news.py` are all D45-adjusted files (they appear in
the D45 record and in no P5 task's `touches_files`); HEAD is pre-D45, so the working tree carries both batches.
The `.openchamber/screenshots/*.jpg` are tool artefacts.

**Not escalated, noted:** stale untracked bytecode for deleted subjects remains (`ibkr/__pycache__/orders*.pyc`,
`tests/__pycache__/test_order_builders*`, `test_kill_switch*`, `test_stop_loss_target*`) — not importable
(CPython 3.11 does not import `__pycache__`-only modules), and DG87's disposition for it is "ignore"; the audit's
M-6 recommendation to delete it is a cleanup, not a requirement. The audit's other named misses are closed:
M-1 (`ibkr/account.py` comment reworded), M-2 (the walkthrough now calls `_on_error`), M-3 (`usage.md:167`).

## Escalation close-out

| id | route | outcome |
|---|---|---|
| ESC-059 | TASK_MANAGER | **stays open** — see below |
| ESC-060 | BUILD | **addressed (moot by design change)** — the columns are dropped (probe: `PRAGMA table_info` on a migrated pre-P5 fixture has neither column on either table) and `_upsert_position` no longer writes them; `requirements.md`'s D46 record says the behavioural half is moot; USAGE/usage now say dropped |
| ESC-061 | BUILD | **addressed (moot)** — `ibkr/orders.py` absent, `import ibkr.orders` raises `ModuleNotFoundError`, `find_spec` is None, the guard asserts it; `S29`/`AR-D45-10` carry SUPERSEDED markers saying the note is moot |
| ESC-062 | BUILD | **addressed** — all five items verified individually (grouping-only `id` comments, the "`—`" consequence named, `ibkr/account.py` reworded, the ticket/registry comment gone with the branch, the d18 case renamed with the `== 0` docstring); the one residual (section header) is ESC-067 |
| ESC-063 | PLAN | **addressed** — `codebase-map.md:24-30` now reads five deleted / seven adjusted / one added with the ESC-063 note; I re-counted the book from `git diff --stat HEAD -- tests/` and it matches |

**ESC-059 — why it is not closed.** precheck reports `task-graph.json` changed since the last review, but the
change is the P4 → P5 graph replacement, not a repair. The contradictory instruction is still on disk at
`docs/build/wave/P4-T01.md:86` — "the five Portfolio `.connect` lines (:647–:651, **delete all five** …)" — while
the same pack's AC4 (`:13`) says that loop is "left untouched (wave 2 owns that loop)". The current graph holds no
P4 task, so no future P4 dispatch can regenerate the note (the immediate risk is gone), but the artefact itself
still contradicts itself and the inline-notes derivation in `build_wave.py` was **not** examined
(`~/.config/opencode/scripts/build_wave.py` mtime 2026-10-22, before the escalation was opened). Since the pack
mechanism is unchanged, the class can recur in a later phase; leaving it open keeps it visible rather than
declaring a finding resolved on the strength of a graph that merely moved on.

## Deliberate — reviewed and NOT reported

`stop_loss`/`take_profit` surviving only as the `DROP COLUMN` subject tuple in `data/db.py` (authorised exemption;
its *missing assertion* is ESC-064, not the exemption itself); `IdManager`/`get_id`/`nextValidId`,
`classify_error`/`error_msg`/the 8000 ms line, `pacing_manager`/`PacingExceeded`, `play_alarm`, `TradeGroup`;
ICT order blocks and watchlist `sort_order` (false positives); the historical comments at
`ui/main_window.py:441`/`:608-612` (D46 inventory row 24 dispositions them RETAIN); `dist/` and the dev
`charting_app.sqlite3` (release/judgement, not code).

---

# Pass 2 — post-rework verification of the five open escalations (2026-10-26T01:14Z)

**Tier:** full pass — this is the same phase's final pass re-run after rework, and `P5-T11` touches a shared
CI-surface guard.
**Scope:** `precheck.json` incremental slice = **`P5-T08`, `P5-T11`** (both reworked after the verdict above; both
`done`, `files_verified` = `tests/test_d45_removal.py` / `tests/test_d42_nonregression.py`, no flags, no overlaps,
0 fail_fast, 0 `PRE-*` entries). `test_verification.json`: **pass**, exit 0, 78.12 s — the independent full-suite
answer, not re-run by me.
**Close-out candidates:** `ESC-059`, `ESC-064`, `ESC-065`, `ESC-066`, `ESC-067` (`precheck` marked 059/064/066
changed; 065/067 carry no linked artefact, so both were re-verified from scratch).

## Verdict

Three escalations hold exactly as fixed (`ESC-064`, `ESC-065`, `ESC-067`) and two are repaired as instances
(`ESC-059`, `ESC-066`) — all four closings rest on my own reproduction or measurement, not on the owner's or the
worker's report. `ESC-066`'s named claims are fixed but the same class survives in four other spots in that
section, so it closes with the residual routed forward (`ESC-069`). **Two new findings, neither blocking:**
`ESC-068` (`P5-T11` ships six inner exclusions while AC1/AC2/AC4 say "exactly the five named modules", and the
durable test was authored to assert six) and `ESC-069` (residual unmarked retained-claims in `architecture.md`).
`ESC-060`–`ESC-063` remain closed and I re-checked their substance.

## ESC-064 — closed: the assertion constrains *shape*, not just existence (`P5-T08`, BUILD, quality, should-fix)

Both halves discriminate, proved by mutation on the live tree (not the worker's probe report):

- **Identifier half.** Appending only `def _esc064_probe(row): return row.stop_loss` to `data/db.py` →
  `test_allowed_in_file_is_narrow_and_named_not_used` **FAILS**: `data/db.py uses a dropped column token as code,
  not as the migration's subject: data/db.py:335: Attribute names 'stop_loss'`.
- **Other-string half.** Appending only `_ESC064_SQL = "SELECT stop_loss FROM positions"` → **FAILS**:
  `data/db.py names a dropped column outside the DROP COLUMN subject tuple ... string 'SELECT stop_loss FROM
  positions' names ['stop_loss']`.
- Each mutation restored **byte-identically** (`sha256 609ae82b…d794ed` before and after), and
  `tests/test_d45_removal.py` is **10/10 green** again. `_drop_column_subject_nodes` still finds the migration's
  subject tuple, so the check has not been narrowed into a false red.

Shape logic read directly (`tests/test_d45_removal.py:1043-1140`): (a) exact `_ALLOWED_IN_FILE == {stop_loss:
{data/db.py}, take_profit: {data/db.py}}`; (b) `_allowed_in` True for no other (file, token) pairing; (c) an AST
parse of `data/db.py` requiring every naming string constant to be an element of the tuple iterated by a `for`
whose body holds a `DROP COLUMN` constant, plus zero `Name`/`Attribute`/`arg`/`keyword`/`def`/`class`/`alias` uses.
A future re-introduced read, SELECT, PRAGMA or `getattr(..., "stop_loss")` all redden it.

The comments now describe what enforces the guarantee instead of asserting it: module docstring `:16-20` ("the
`DROP COLUMN` subject-tuple shape is asserted by `test_allowed_in_file_is_narrow_and_named_not_used`, not merely
stated") and the `_ALLOWED_IN_FILE` comment `:214-221` (names the test and the parsed shape).

## ESC-065 — closed: measured coverage, measured stability, real red probe (`P5-T11`, BUILD, quality, should-fix)

**(a) Six exclusions out of ~124 modules / 1022 tests is still the suite.** The child collects **1000 of 1022**
tests in **27.50 s** (118 of 124 modules; the six exclusions carry ~17 tests and this file's own 5 are not
collected). `pytest tests/test_d42_nonregression.py -q` = **5 passed in 27.8 s** (the node alone was ~70 s).

The sixth (`test_watchlist_addflow_d22.py`) **is not covering a product failure**: it passes standalone (10 passed,
1.06 s) and is inside the external gate's full 1022-test run (`test_verification.json` pass), so no assertion left
the gate's sight — only the in-suite subset. Its crash class is the same as the other two Qt-teardown exclusions
(`qapp.processEvents()` + a widget-lambda slot, observed only in the nested subprocess; I did **not** reproduce the
SIGSEGV on demand and the claim rests on the worker's three-run record plus the nested `-11`s already in
`build_log.md` P5-T10). The reasoning holds, but see `ESC-068`: it contradicts three ACs that say "five".

**(b) Break/restore still proves a red tree is caught — end-to-end, not only via the monkeypatch.**
`tests/test_zz_probe_fail.py` (`assert False`) → node **fails** `rc=1`, record line
`inner suite: 1001 collected outcomes in 27.50s (rc=1)`, the child's own traceback (`1 failed, 1000 passed`, naming
`test_zz_esc065_probe_red`). Probe deleted, node green again (`tests/test_zz_probe_fail.py` absent). The durable
half (`test_red_inner_child_is_caught`) asserts the same at unit level. The D42 guards themselves were not touched:
`git diff -U2` shows the only hunks are the docstring, imports and the node region — `AC-D16.7` and
`AC-D16.1/3/4` bodies are context-only.

## ESC-066 — the five named claims are fixed; four more of the same class are not (`PLAN`, consistency, nice-to-have)

Fixed and verified: `architecture.md:4819` (orders bullet), `:4822` (observer bullet), `:4825`
(`MAX_ORDER_NOTIONAL`), `:4826-4827` (`order_limiter`) and `:4869` (the Frozen Interfaces sentence) each carry an
inline `[SUPERSEDED BY D46/P5 … S39/S46]` clause — none of those reads as live.

**Not fixed** (all false on the tree, none marked, none covered by the section banner, which supersedes only the
*storage* half generically and points at S29/S35/AR-D45-10 and the two frozen rows): `:4779` the Constrained-choices
row `ibkr/orders.py [new in D45] | **Retain** …`; `:4791` "**Retained in the same file (A90):** `order_registry`,
`_on_open_order`, …"; `:4799` "the `_fresh_registry`/`_register` helpers and the `_on_order_error`/`classify_error`
cases **stay** (they cover the retained observer path)"; `:5014-5018` item 9 "Explicit non-changes … `ibkr/orders.py`'s
API, `ibkr/pacing.py`, … `MAX_ORDER_NOTIONAL` … is **not** deleted". Routed forward as **`ESC-069`**, and this entry
closes on the five it named — the same partial-then-residual pattern `ESC-062` → `ESC-067` used.

## ESC-067 — closed: both headers confirmed, `ui/` twin path clean (`BUILD`, consistency, nice-to-have)

`ibkr/bridge.py:42` now reads `# Account & positions` over the four account/position signals (the bridge carries no
order signal — the end-state test asserts `hasattr` False for `order_status`/`open_order`/`exec_details`);
`tests/test_dock_d18_region.py:154` now reads `# ── T48-T03 — panel present, summary signals exposed`. No order word
was reintroduced into the `ui/` raw-text twin's path: grep over `ui/` for
`stop_loss|take_profit|placeOrder|cancelOrder|reqGlobalCancel|order_status|open_order|exec_details|orders` → zero
hits; guard 10/10 green.

## ESC-059 — closed: the pack is repaired, the script is exonerated, the class is decided (`TASK_MANAGER`)

The pack's single JSON block still parses (`json.loads` OK: `id/title/description/acceptance_criteria/tests/
touches_files/context/size`), and its `context.read_files` "why" now reads "The five Portfolio `.connect` lines
(:647-:651) are **OUT OF SCOPE** for this task and must be LEFT IN PLACE — wave 2 (P4-T02) owns them; AC4 requires
`test_dock_d18_region.py`'s five-signal receiver loop to stay untouched, and **this task's ACCEPTANCE CRITERIA
OVERRIDE THIS NOTE**", followed by a dated `[ESC-059 CORRECTION 2026-10-26: …]` record of the old wording.

The script is not at fault, confirmed by reading it rather than by assertion: `build_wave.py:74-82` documents that
packs carry pointers (`architecture_ref`/`plan_ref`/`memory_refs`/`contracts`) and the script contains no `why`
literal at all — the note is author text copied from the task JSON. No P4 task remains in `task-graph.json`, so no
re-dispatch can regenerate the note.

**Class decision:** close the instance; do **not** open a control round-trip. There is no mechanical check for
"prose contradicts its own ACs", and the two controls that do exist are real: workers report `pack_deficiency` on
every result (P4-T01's worker refused this note on exactly that basis) and the reviewer reads the pack. The
advisory authoring rule — *a pack note may not restate scope; it may only defer to the ACs* — is recorded here for
the Task Manager to adopt in its checklist; it is not escalated because no artefact is now wrong and no P4 task can
be re-dispatched.

## New findings

### ESC-068 — `P5-T11` ships six inner exclusions; its ACs say "exactly the five named modules"  (`P5-T11`, TASK_MANAGER, consistency, should-fix)

AC1 enumerates five modules and says "exactly"; AC2 says "the five modules are not collected"; AC4 says "state the
five exclusions". `tests/test_d42_nonregression.py:188-205` defines six, both docstrings say six, and the task's own
durable test asserts the six-element set — the persisted assertion was written to match the code, not the AC. The
result JSON carries no notes and `pack_deficiency: []`, so the deviation lives only in a code comment. The *code* is
right (the sixth is standalone-green and gate-covered, above); the *book* is wrong. Route: amend the ACs to the
invariant plus the six named modules and record the sixth's evidence — do **not** send it to BUILD, since deleting
the exclusion to satisfy a literal AC would restore the `-11` flake. Per the repeat-invariant rule this is a
TASK_MANAGER escalation, not a third BUILD patch on the same node.

### ESC-069 — four more unmarked "retained / not deleted / stay" claims in `architecture.md`'s D45 section  (PLAN, consistency, nice-to-have)

`:4779`, `:4791`, `:4799`, `:5014-5018` — text quoted in the escalation entry. All four contradict the live tree
(`ibkr/orders.py` absent; `order_registry`/`_on_order_*` absent from `ui/`; `test_order_rejections.py` has no
`_fresh_registry`/`_register`/`_on_order_error` — only 4 classify_error cases; `MAX_ORDER_NOTIONAL` and
`order_limiter` gone). Four one-line `[SUPERSEDED BY D46/P5 …]` markers, wording only.

## Also re-checked (rework disturbed nothing)

| Check | Result |
|---|---|
| Guard suite | `tests/test_d45_removal.py` **10 passed** (was 9 at the P5-T10 gate; the rework added exactly the one test) |
| Migration end state | fresh `DB()` probe: `positions` = `id,symbol,account,con_id,contract_type,qty,avg_cost,local_symbol,multiplier,expiry,strike,right,trade_group_id,updated_at`; `trade_groups` = `id,name,strategy_type,underlying,collapsed,created_at` — neither table has `stop_loss`/`take_profit` |
| Zero transmit/cancel | grep `placeOrder|cancelOrder|reqGlobalCancel` over `ui/ services/ data/ ibkr/ config/ main.py` → **no matches** |
| `ESC-060` | still closed — no column left to clobber (schema probe above; `_upsert_position` name-lists 13 columns) |
| `ESC-061` | still closed — `ibkr/orders.py` absent (`ls` → No such file) |
| `ESC-062` | still closed — d18 case still named `…_summary_signals_exposed` with the `== 0` probe and docstring |
| `ESC-063` | still closed — `codebase-map.md:24-30` still reads five deleted / **seven** adjusted / one added |
| `P5-T11` guards | D42's `AC-D16.7` / `AC-D16.1/3/4` assertions byte-untouched (`git diff -U2`: docstring + imports + node region only) |

## Documentation

No usage-doc duty attaches to this pass: both scoped tasks are test-only (`tests/test_d45_removal.py`,
`tests/test_d42_nonregression.py`), and the only production-file edit in the close-outs is a **comment** at
`ibkr/bridge.py:42`. The user-facing pair (`USAGE.txt`, `usage.md`) already says the columns are dropped (P5-T09,
verified last pass); `doc_candidates` flagged none of the scoped tasks `doc_required_unmet`.

## Mock-endpoint containment (standing invariant) — clean

Scanned the reworked diffs for `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness`. All hits are
inside `tests/`: `_fake_run_inner_suite` (a monkeypatched seam in `test_d42_nonregression.py`) and the guard's
`_RecordingClient`/`fake`/`_stub_account_calls` walkthrough doubles. `ibkr/bridge.py`'s change is a comment; no
production module gains a mock endpoint or imports a test fake. No production path was rewired.

## Escalation close-out

| id | route | outcome |
|---|---|---|
| ESC-059 | TASK_MANAGER | **addressed** — pack repaired, JSON parses, `why` now defers to the ACs with a dated correction record; `build_wave.py` exonerated by reading it; class decision recorded above |
| ESC-064 | BUILD | **addressed** — both mutation halves redden the new test, restores sha256-identical, 10/10 green, comments name the enforcer |
| ESC-065 | BUILD | **addressed** — child = 1000/1022 tests in 27.5 s; file 5 passed in 27.8 s; real red probe caught and named the failing test; sixth exclusion checked for concealment (none) and routed to `ESC-068` |
| ESC-066 | PLAN | **addressed** — five named claims carry markers; four same-class claims remain → `ESC-069` |
| ESC-067 | BUILD | **addressed** — both headers confirmed, `ui/` twin path clean, guard green |
| ESC-068 | TASK_MANAGER | **new, open** — ACs say five exclusions, file ships six with a durable test asserting six |
| ESC-069 | PLAN | **new, open** — four unmarked retained-claims left in `architecture.md`'s D45 section |

## Deliberate — reviewed and NOT reported

`tests/test_watchlist_addflow_d22.py`'s exclusion *itself* (its AC bookkeeping is `ESC-068`; the module is green
standalone and inside the gate, and its crash class matches two already-accepted Qt-teardown exclusions); the
private `_drop_column_subject_nodes` helper (correct and confined to the guard); `architecture.md:4774`'s "A87 keeps
the SL/TP columns" (storage half, covered by the section banner's generic supersession sentence, unlike the four
order-module claims in `ESC-069`); `order_code_audit.md`, `review_log.md` (legacy) and the `.openchamber/
screenshots/*` tool artefacts.

Status: REVIEW_COMPLETE

# Pass 3 — close-out verification of ESC-068 and ESC-069 (2026-10-26T01:27Z)

**Tier:** full pass for the prose sweep — no build slice is in scope, and the whole point is an *exhaustive*
read of one document section, which a diffstat cannot give. No task was re-reviewed; no code was re-run beyond
the verification greps below.
**Scope:** the two open escalations only (`ESC-068` TASK_MANAGER, `ESC-069` PLAN). `test_verification.json`
(verdict **pass**, exit 0, 78.12 s) stands as the independent suite answer and was not re-run; the only `.py`
edited after that run is `data/db.py`, and I confirmed it holds no probe residue (`grep esc064` → none; only the
`("stop_loss", "take_profit")` migration subject at `:200`), i.e. `ESC-064`'s sha256-identical restore.

## Verdict

**Neither closes.** The three ACs in `ESC-068` and three of the four markers in `ESC-069` are exactly as
described and true on the tree, but **both artefacts still carry the defect the escalation named**, in places the
fix did not reach: `P5-T11`'s book still restates *five* in five other fields (including the context pack a Build
worker reads), and `architecture.md`'s D45 section still has five unmarked claims that read as live retention of
P5-deleted code — plus one marker that is rendered invisible because it sits in an orphan table cell. Details and
exact locations below; both entries stay `open` with a `residual` field naming what is left.

## ESC-068 — the ACs hold, the rest of the book does not (`P5-T11`, TASK_MANAGER, consistency, should-fix)

**Verified against the shipped file** (`tests/test_d42_nonregression.py:193-201`), not against the report:

- `_INNER_EXCLUDED` = `test_d24_smoke_gate.py`, `test_d28_4_gate.py`, `test_d28_tick_burst_baseline.py`,
  `test_session_overlay.py`, `test_d28_5_teardown.py`, `test_watchlist_addflow_d22.py` — **six, in that order**.
  AC1's list is the same six in the same order, with the sixth's reason matching the code comment at `:200-201`
  (SIGSEGV at `test_D22_07_T03_seed_guard`, caught by the task's own three-run AC2 check) and AC1's
  "still passes standalone and inside the gate's full run" matching `ESC-065`'s measurement.
- AC4's reasons map 1:1 onto the file's inline comments (three wall-clock, three Qt teardown) and onto both
  docstrings (`:20-29`, `:279-286`), which also name `verify_tests.py` → `test_verification.json` and `P5-T10` as
  the owners of whole-suite-green evidence. AC2's figures (1000 of 1022 collected, 118/124 modules, ~27.5 s) are
  the numbers I measured myself last pass. The durable assertion at `:338-348` pins the six-element set.
- `python3 ~/.config/opencode/scripts/check_tasks.py` → **OK: 11 tasks validated**, exit **0** (WARNs are the
  pre-existing "touches_files not in context read_files" kind, none on `P5-T11`).

**Still says five, in `docs/tasks/task-graph.json` `P5-T11`:**

1. `description` item **(a)**: "`_INNER_EXCLUDED: tuple[str, ...]` = exactly `("test_d24_smoke_gate.py",
   "test_d28_4_gate.py", "test_d28_tick_burst_baseline.py", "test_session_overlay.py",
   "test_d28_5_teardown.py")` … and the **two** Qt-teardown-sensitive ones" — the literal tuple and the "two"
   count both predate the sixth.
2. `context.contracts[1].signature`: `_INNER_EXCLUDED: tuple[str, ...] = (… five names …)`. This is the pack a
   Build worker is handed; it is the most load-bearing of the five.
3. `context.memory_notes[0]`: "that is why the **two** Qt-teardown-sensitive modules are excluded".
4. `tests[P5-T11-T11].description`: "`set(_INNER_EXCLUDED) == {the five names}`" — a worker regenerating that
   assertion from the book would author a test that fails against the shipped code.
5. `tests[P5-T11-T41].expected_result`: "the subset, the **five** exclusions with reasons".

(`docs/build/wave/P5-T11.md` also prints the old five, but it is the frozen dispatch snapshot of the wave, not the
book — do not edit it.)

**Invariant for the fix, so this is the last round of it:** the exclusion set is stated in one place only — the
description's tuple, the contract signature, the memory note, and every test spec that names it must all say six,
with the sixth's reason, or must defer to AC1 instead of restating the list. Amending the three ACs alone leaves
four contradicting statements in the same object.

## ESC-069 — three of four markers correct, one invisible, five same-class claims still unmarked (`architecture.md`, PLAN, nice-to-have)

**The four named claims:**

| # | Location | Result |
|---|---|---|
| 1 | `:4778` D45 decision row | **Marker present and factually right** (`[REVERSED BY D46/P5 S39 …]`: module, `tests/test_order_builders.py`, `data.models.UserOrder` all deleted — verified absent) — **but it is a fifth cell in a four-column table row** (`| Decision | Choice | Rationale | Alternatives considered |`), so GFM drops or misaligns it on render. The one row whose whole purpose is to stop a reader acting on "Retain" is the one row whose marker a reader may not see. Move it inside the *Alternatives considered* cell. |
| 2 | `:4791` `ui/main_window.py` row | **Correct.** Marker inside the cell; the five observer names and `order_registry` are named as deleted, and the survivors it keeps are real on the tree (`_symbol_last_prices` ×3, `def closeEvent` at `:3191`). |
| 3 | `:4799` `tests/test_order_rejections.py` row | **Correct.** Verified: no `_fresh_registry`/`_register`/`_on_order_error` in the file; the `classify_error` cases survive (3 test functions, one parametrized over 6 codes). |
| 4 | `:5014-5019` item 9 | **Correct.** Marker covers exactly the four superseded items + the storage pair, and the genuine non-changes it affirms are genuinely untouched: `services/alarm_service.py`, `services/drawing_service.py`, `ui/studies_dialog.py`, `ui/popout_window.py` all present; no dependency-file change. **Not over-marked.** |

**Five unmarked claims of the same class still in the D45 section** (each read on the line, not grepped — the
markers that wrap do so at sentence end, and none of these five has a marker in its own sentence or paragraph):

- `:4725` — the Major-components paragraph lists `ibkr/*` "… **orders (kept, no transmit caller)** …". The module
  is gone (`ls ibkr/orders.py` → no such file).
- `:4857` — Integration Points, "IBKR inbound order/execution callbacks (`openOrder`, `orderStatus`,
  `execDetails`, `error`) … **Retained observers (A90): they surface TWS state and order errors on the status
  bar**". The observers and the overrides are both gone (`grep 'def openOrder|def orderStatus|def execDetails'`
  over `ibkr/` → none; the only `error` override left is `ibkr/client.py:195`).
- `:4891` — Frozen Interfaces, "Error classification … **drives the retained `_on_order_error` / connection-alert
  path**". Half of that path was deleted; only the connection-alert half is real.
- `:4994-4996` — Supersessions item 3: "… **`ibkr/orders` retained without a caller (`S29`, A80/A90); only the
  fail-fast port check and the inert inbound observers remain.**" Two false clauses in the one section whose job
  is "recorded, never silent" — and the item's own first sentence ("No order-related surface is retained")
  contradicts it.
- `:4693` and `:4694` — Codebase-Summary facts rows: "keep the module; the registry stays read/written by the
  **inert** observers" and "`ibkr/orders.py` keeps **real** unit coverage" (that suite is deleted). Same table as
  `:4696`, which *is* marked — which is what makes these look like a missed sweep rather than a convention.

Borderline, listed for completeness, not counted: `:5038-5039` handoff item (g) "the intentional survivors (A90's
observers, the ibapi news boundary, the dividend path) were not deleted" — it reads as a D45 verification record,
but a reader can take it as the current survivor list.

**Invariant for the fix:** the unit of work is *the section*, not a count of instances. Every sentence in
`docs/architecture.md:4601-5041` that calls a P5-deleted subject retained / kept / stays / frozen / inert /
surviving carries a one-line marker naming `S39`/`S40`/`S46`, or the section banner is widened to name that class
explicitly. Three passes have now each found "the four/five named ones are fixed, four/five more remain"; a
keyword sweep of the whole section, judged against `git`-verified absence, ends it.

**Not reported, deliberately:** `:4952` `AR-D45-5` (a risk record about D45 residue, not a retention claim);
`:4957` `AR-D45-10` and `:4964`/`:4966` traceability rows (already marked / historical traceability);
`:4774` "A87 keeps the SL/TP columns" (storage half, covered by the section banner by name); `:4911-4916`
non-functional data-safety bullet (marked two lines above at `:4911`).

## Escalation close-out

| id | route | outcome |
|---|---|---|
| ESC-068 | TASK_MANAGER | **stays open** — AC1/AC2/AC4 verified correct and matching the shipped six; five other fields of the same task still state five (`description` (a), `context.contracts[1]`, `context.memory_notes[0]`, `P5-T11-T11`, `P5-T11-T41`). `residual` recorded on the entry |
| ESC-069 | PLAN | **stays open** — `:4791`/`:4799`/`:5014-5019` verified; `:4778`'s marker is in an orphan fifth table cell (dropped on render); five unmarked same-class claims remain (`:4725`, `:4857`, `:4891`, `:4994-4996`, `:4693`/`:4694`). `residual` recorded on the entry |
| ESC-060–ESC-067 | — | untouched this pass and not re-opened; nothing they cover changed (no code edit since pass 2 except the `data/db.py` restore noted above) |

Status: REVIEW_COMPLETE

# Pass 4 — close-out verification of ESC-068 and ESC-069 (2026-10-26T01:34Z)

**Tier:** full — no build slice is in scope; the work is an exhaustive read of one task object and one document
section, which a diffstat cannot give. No task was re-reviewed and the suite was not re-run.
**Scope:** the two open escalations (`ESC-068` TASK_MANAGER, `ESC-069` PLAN). The independent suite answer is
unchanged: `test_verification.json` verdict **pass**, exit 0, 78.12 s. Everything it covered is byte-identical to
that run — `tests/test_d42_nonregression.py` (sha256 `25cd18cc…`, 21:06) and `tests/test_d45_removal.py`
(`b004b7dd…`, 20:56); the only `.py` touched after it was `data/db.py` (21:11, the `ESC-064` probe restore), whose
sha256 is still `609ae82b…` with no probe residue and only the migration subject at `:200`. Everything changed since
pass 3 is documentation (`task-graph.json`, `architecture.md`, `escalations.json`), so no verdict here rests on a
stale artefact.

## Verdict

**Both close.** All six `P5-T11` replacements hold, the contract tuple the worker is handed matches the shipped
`_INNER_EXCLUDED` **in order**, and `check_tasks.py` exits 0. In `architecture.md` the `:4778` row renders as four
cells with the marker visible, the five `ESC-069` sites and the two facts rows are factually true on the tree, and
my own sweep of the section — run with the escalation's criterion rather than against the list — leaves no unmarked
claim that names a P5-deleted subject and reads as live retention; the two borderlines it does surface (the
mid-word splice, and the generically-named handoff item at `:5038-5039`) are documented below and deliberately not
escalated. I agree with leaving the `AR-D45-5` risk row unmarked, and I explain below why. Both entries flip to
`addressed` with what I verified.

## ESC-068 — closed: six restatements, one order check, one frozen snapshot (`P5-T11`, TASK_MANAGER)

Read from `docs/tasks/task-graph.json`, not from the report. Machine checks first: `json.dumps(task)` for `P5-T11`
gives `count("five") == 0` and `count("six") == 5`; no "two Qt-teardown" survives anywhere in the object.

| # | Field | Now reads |
|---|---|---|
| 1 | `description` (a) | the literal tuple with all six names, the sixth carrying its provenance ("reproduced a real SIGSEGV at `test_D22_07_T03_seed_guard` — it still passes standalone and inside the gate's full run") |
| 2 | `description` (a) | "the **THREE** Qt-teardown-sensitive ones", with the third's evidence |
| 3 | `context.contracts[1].signature` | the tuple a Build worker is actually handed, six names |
| 4 | `context.memory_notes[0]` | "the three Qt-teardown-sensitive modules … (the third, test_watchlist_addflow_d22.py, was added after …)" |
| 5 | `tests[P5-T11-T11].description` | "`set(_INNER_EXCLUDED) == {the six names}`" |
| 6 | `tests[P5-T11-T41].expected_result` | "the six exclusions with reasons" |

**The order check you asked for, since a count cannot catch it.** Contract tuple order is
`d24_smoke_gate → d28_4_gate → d28_tick_burst_baseline → session_overlay → d28_5_teardown →
watchlist_addflow_d22`; the shipped tuple at `tests/test_d42_nonregression.py:193-201` is the same six in the same
order — element-by-element equal, not just equal as a set. The docstring at `:279-286` and the inline exclusion
comments (`:194-201`) agree with both, and `_inner_pytest_args` appends `len(_INNER_EXCLUDED) + 1` ignores (the +1
being this module), which is what T11's assertion pins. The sixth's claim was re-measured, not trusted:
`pytest tests/test_watchlist_addflow_d22.py -q` → **10 passed**.
`python3 ~/.config/opencode/scripts/check_tasks.py` → **OK: 11 tasks validated, exit 0**; the WARNs are the
pre-existing pure-output kind (`P5-T03`/`P5-T07` deletions, `P5-T10`'s own result file) and none names `P5-T11`.

**Where "five" still prints — checked, and deliberately not edited.** Only two dated records, neither of them the
book: `docs/build/wave/P5-T11.md` (the dispatch snapshot printed at 20:54, before this amendment; `build_wave.py`
rewrites a pack from the graph at dispatch — `:716` — and `P5-T11` is `done`, so it can never be handed to a worker
again) and `docs/tasks/task_manager_notes_P5.md:283` (§7d, the authoring record written before the sixth existed).
Rewriting either would falsify what was decided and what was dispatched; the two live artefacts that carry the
book — `task-graph.json` and `wave.json` — are both clean (`wave.json` is `CONSOLIDATED` with no tasks and no
`five`/`_INNER_EXCLUDED` text).

## ESC-069 — closed: five sites true, `:4778` renders, sweep exhausted (`architecture.md`, PLAN)

**The row.** `:4778` splits on unescaped pipes into exactly **four** content cells, and the
`[REVERSED BY D46/P5 S39 …]` marker sits inside the fourth (*Alternatives considered*) — the orphan fifth cell is
gone, so GFM renders it. **The five named sites** were re-read against the tree, not just for the presence of a
marker: `:4725` "orders (DELETED by D46/P5 `S39`)" and `ibkr/orders.py` is absent; `:4857` names the three deleted
overrides/observers and keeps only `IBApiClient.error` — `grep 'def openOrder|def orderStatus|def execDetails' ibkr/`
returns nothing, `error` is the only override left (`ibkr/client.py:195`), and `ibkr/bridge.py` carries no order
signal; `:4891` "`_on_order_error` is deleted — D46/P5 `S40`"; `:4994-4996` item 3 says `ibkr/orders` is deleted with
the observers and three bridge signals; `:4693`/`:4694` carry `[REVERSED …]`/`[SUPERSEDED …]` like `:4696` in the
same table.

**My own sweep, so this is not a list-check.** Criterion: a line in `:4601-:5042` with a retention verb
(retain/keep/stay/surviv/not deleted/untouched/inert/frozen/A90/A87) and no marker on the line or within ±3 lines →
78 verb lines, of which six name a P5-deleted subject unmarked. Each was read:

- `:4837`, `:4839`, `:4841` — **already marked**: each ends its own cell with an inline "P5: … DROPPED (§ P5
  `S47`)" / "… DELETED (§ P5 wave 7)" clause. Worth knowing for future sweeps: that wording does not contain
  `SUPERSEDED`/`VOID`, so a marker-keyword pass counts them as unmarked when they are not. Not a finding.
- `:4774` — the `Persistence … A87 keeps the SL/TP columns` row: storage, and the section banner at `:4603-4605`
  supersedes "every sentence below that says the storage is kept / unchanged / retained / migration-free" by name.
  Covered, as pass 3 judged.
- `:4966` — `AC-D45.4` traceability pointing at Frozen *Order registry API* / *Broker boundary*: the API row at
  `:4884` itself reads "VOID from P5 (`S39`)", so following the reference lands on a marked row. Not a claim.
- `:4952` — `AR-D45-5`. **I agree with your judgement.** Its subject is the failure mode (a half-removed path
  *surviving*, and a later worker restoring it), not an assertion that anything is retained now; its mitigation
  names `S29`/`S35`, both of which carry markers; and marking a genuine risk would be exactly the over-marking
  defect you named. Leave it.

**Genuine non-changes confirmed unmarked and still true:** `:4721-:4724` chart/render stack, watchlist/dock,
`services/*`, `data/*` (the storage clause there is the banner's, and data's only P5 delta is that clause);
`:4791`'s marker explicitly keeps `_symbol_last_prices`, the connect path, the badges and `closeEvent`; `:5019`
keeps chart/alarms/drawings/studies/pop-outs/D39-D44 and the dependency set. Checks: `services/alarm_service.py`,
`services/drawing_service.py`, `ui/studies_dialog.py`, `ui/popout_window.py`, `ui/chart_panel.py`,
`ui/candlestick_item.py` all present; no dependency-file diff in `git status`; the survivors named in `:4791` are in
the tree.

**Two things read, judged, and NOT escalated** (so neither is a silent skip):

1. The `:4778` marker was spliced mid-word: the cell now reads "… the **inert** observe **[REVERSED …]**rs, so it is
   neither unreferenced code nor a transmit path." The marker is fully visible and the row renders as four cells,
   which is what the escalation asked; the cost is cosmetic — "observers" is split. If the row is ever edited
   again, move the clause to the end of the sentence. Not worth another Plan round on its own.
2. `:5038-5039` handoff item (g), "the intentional survivors (A90's observers, the ibapi news boundary, the dividend
   path) were not deleted" — a past-tense record of what the D45 reviewer verified, whose subject is named
   generically rather than as a removed symbol (which is why a symbol-crossed sweep cannot see it), and which the
   section banner covers when it reverses "S35's order half". Pass 3 listed it as borderline and did not count it;
   I keep that reading rather than flip the judgement at close-out. **If the D45 section is touched again, add the
   `S40` clause here too** — it is the last sentence in the section that would read as a current survivor list.

## Escalation close-out

| id | route | outcome |
|---|---|---|
| ESC-068 | TASK_MANAGER | **closed** — six restatements verified in `task-graph.json`, contract tuple order matches the shipped `_INNER_EXCLUDED` element for element, `check_tasks.py` exit 0, the sixth's standalone pass re-measured; residual five-module text lives only in the frozen dispatch snapshot and the dated authoring note |
| ESC-069 | PLAN | **closed** — five named sites true on the tree, `:4725`/`:4857`/`:4891`/`:4994-4996`/`:4693`+`:4694` all marked and factually right, `:4778` renders four cells with the marker visible, sweep re-run with the escalation's criterion leaves no unmarked retention claim naming a deleted subject (two cosmetic/borderline items documented above, not escalated) |
| ESC-060–ESC-067, `PRE-*` | — | untouched and not re-opened; nothing they cover changed (no code edit since pass 3 except the `data/db.py` restore, hash-checked above) |

## Documentation

No user-facing behaviour changed in this pass — the edits were `task-graph.json` prose and `architecture.md` prose.
`precheck.json`'s `doc_candidates` (`USAGE.txt`, `usage.md`, `docs/`) are all `touched: false`, which is correct:
the P5 user-facing docs were updated in the build waves (`ESC-058` verified as-built), and nothing here adds or
changes a user-visible surface.

## Mock-endpoint containment (standing invariant) — clean

Scanned the two reviewed task files for `mock|fake|stub|simulat` crossed with
`endpoint|client|service|server|api|harness`: every hit is a test double inside `tests/` injected at the boundary
(`_RecordingClient`, `_FakeSession`, `_fake_run_inner_suite` in `test_d42_nonregression.py`'s seam test). No
production module imports `tests/` (`grep '^from tests|^import tests'` over `ui/ services/ data/ ibkr/ config/
main.py` → none), and no production code path was touched by either task.

Status: REVIEW_COMPLETE
