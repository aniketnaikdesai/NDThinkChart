# Plan Review — Phase P5 (D46 / Batch 21, revision 2 — scope EXPANDED)

> **Pass type:** `final_pass`, re-run as a **full validation**, not a delta. The prior `APPROVED` review of
> **revision 1** (five waves, no migration) is **SUPERSEDED**: it judged a narrowly-scoped draft written *before* the
> owner's Q56–Q59 answers widened `D46` to `D46.1`–`D46.13` / `A91`–`A104` / `R76`–`R85` / `DG78`–`DG87`.
> **Phase gate:** open — P4/D45 build ended `Status: READY_FOR_REVIEW` (build log, wave 105) and
> `docs/code_review/review_log_P4.md` ends `Status: REVIEW_COMPLETE`.
> `plan_lint.py --phase P5` → **PASS, 0 failures / 0 warnings** (re-run independently after every edit below).
> **Validator date:** 2026-10-25. **Requirements of record:** `Status: READY_FOR_PLAN` (`:5404`, batch footer
> `:5553`), no blocking question; Q56–Q59 owner-answered.
> **Independent checklist:** `docs/code_review/order_code_audit.md` used as the coverage matrix, not as a second
> opinion on the architecture.

**Status: APPROVED**

---

## Validation Summary

The revision is **sound and executable**, and its most load-bearing numbers reproduce when executed. It also carried
**revision-1 residue** (stale wave numbers, two unexecuted arithmetic claims) and two claims the audit had already
disproved. Those are corrected at activation (§ *Activation corrections*) — all editorial or requirement-directed,
**no new architectural decision, no scope change**.

What I executed rather than read:

- **The removal instrument, re-run on the pre-P5 tree** with the revision-2 token set
  (`_EXACT_ONLY = {"orders","Orders"}`, `reserve` absent, `stop_loss`/`take_profit` as substrings):
  **41 AST offences across 10 files** — `ui/main_window.py` 14, `ibkr/orders.py` 7, `services/sound_service.py` 5,
  `data/models.py` 3, `ibkr/bridge.py` 3, `ibkr/client.py` 3, `ibkr/account.py` 2, `ibkr/pacing.py` 2, `data/db.py` 1,
  `config/settings.py` 1 — and **40 raw-text twin hits on 27 lines, all `ui/main_window.py`** (`:36`, `:595`–`:597`,
  `:1546`–`:1547`, `:1551`, `:1559`, `:2951`–`:2952`, `:2954`, `:2957`, `:2959`, `:2965`, `:3093`–`:3094`,
  `:3133`–`:3134`, `:3164`–`:3165`, `:3186`, `:3198`–`:3199`, `:3216`–`:3217`, `:3226`–`:3227`). **Every one of the 41
  offending units lies inside a region waves 1–7 delete or edit** — so the plan's **0 / 0** post-P5 claim cannot be
  false unless a wave's specified edit is not performed. (I did **not** re-run the plan's copy-tree simulation; I
  verified its premise unit by unit, which is what the claim rests on.)
- **The token arithmetic:** `_SURVIVORS` is **26** today and the ten names `AC-D46.4` lists are exactly the ten
  removable ones → **16**; `_FORBIDDEN` is **53** and the plan's 27 new tokens are all absent from it → **80**
  (2 exact + 78 substring). Exact-match units measured: `orders` **2**, `Orders` **1**; substring units **5 / 2** — the
  plan's "5 / 2" are the substring counts, now labelled as such.
- **The migration (`S47`) executed on a synthetic pre-P5 database** in `.venv` (SQLite **3.53.1**, ≥ 3.35 as required):
  3 `positions` + 1 `trade_groups` rows preserved; `sqlite_sequence` **3 → 3**; `idx_positions_symbol_con_id` still in
  `sqlite_master` **and still enforcing** (a duplicate `(symbol, con_id)` insert raised `IntegrityError`);
  `foreign_key_list` still `trade_group_id → trade_groups.id`; `foreign_key_check` empty; `integrity_check` = `ok`;
  the seeded `trade_group_id` values (`1, NULL, 1`) preserved; the **13-column upsert + `ON CONFLICT` + `RETURNING id`**
  works; a **second open is a no-op**; `trade_group_id` lands at index **12**. Also verified that Python 3.11's
  `sqlite3` **autocommits DDL** (a second connection sees a `DROP COLUMN` made without `commit()`), so each `DROP` is
  atomic and durable and an interrupted open leaves only the not-yet-dropped columns — the guard converges. Fresh,
  pre-P5 and interrupted opens therefore all converge, and the DROP-vs-rebuild reasoning holds (a rebuild would need
  the `bars` salvage machinery *per table* plus hand-recreated index/FK for zero benefit).
- **The index shift (`S48`):** `trade_group_id` is `row[14]` today (15-name `columns` tuple) and becomes `row[12]` at
  13 names — confirmed in `ui/main_window.py`'s `_on_position_end` and `_upsert_position`; per-cursor
  `sqlite3.Row` works and `db.conn.row_factory` is `None` (no other caller is affected). **No test seeds a non-null
  `trade_group_id` today** (only `test_account.py:107` asserts it is `None` and `test_strategy_detection.py:32` passes
  the kwarg), so the plan's new case is the only guard against the silent shift.
- **Frozen interfaces, spot-verified verbatim against the tree:** `classify_error`'s four code sets;
  `def error(self, *args, **kwargs):` + the D40.1 502 early return; `error_msg = pyqtSignal(int, int, str)`;
  `on_historical_error(self, req_id, code, msg) -> None`; `_on_rt_stream_error(self, session, code, message)`;
  `check_live_port() -> None`; `IdManager.set_next_valid_id` / `get_id`; `nextValidId(self, orderId: int)`;
  `render_alarm_chime` / `ALARM_DURATION` / `ensure_sound_files(...) -> dict` / `play_alarm`;
  `_table_columns(self, table_name) -> set[str]`; the 13-name `Position` row shape. Owning modules all resolve; no
  duplicates; nothing under construction is frozen (`_on_error` is disclosed as edited with its surviving contract
  pinned in the plan, and the *Removal guard scope* row freezes the **split**, which is what must not move).

**Task Manager may proceed.** P5 is active below.

---

## Per-step results

- **1 Requirements coverage — pass.** Every `D46.1`–`D46.13`, `AC-D46.1`–`.13`, Journey 39 steps 1–10 and R76–R85 maps
  to a decision (`S39`–`S50`) and to at least one wave; the traceability table is complete. Nine requirements-text
  defects are recorded as `RG-D46-3`–`RG-D46-9` (§ *Requirements notes*) — none changes what gets built.
- **2 Architecture completeness — pass.** Stack (constrained first, no additions), components, responsibilities,
  relationships, data model (three DB ages), integrations, boundaries, security/blast radius, performance,
  operational constraints and twelve risks, each with rationale. The destructive step is stated as the batch's only
  byte-destroying one (corrected at activation).
- **3 Architecture consistency — pass after correction.** The migration (S47) and the readers (S48) agree with
  `D46.12`; the KEEP boundary (S46) is consistent with `A100`–`A103`; the wave split matches the callback graph. Three
  internal contradictions were found and fixed: stale revision-1 wave numbers (the instrument is wave **8**, the prose
  wave **9**), `AP-D46-9`'s "`USAGE.txt` is unchanged" against wave 9, and a duplicated supersession item.
- **4 Plan quality — pass.** Three phases / ten waves, each a meaningful body of work with goal, coverage, dependency
  and file set; no task-level dependency graph; the only per-assertion detail is the test book `D46.5` requires. Wave 7
  is correctly one task (schema + every reader + its whole test book).
- **5 Task Manager readiness — pass.** Ten tasks (`P5-T01`…`P5-T10`), forced order, per-name ownership table naming
  every removed symbol's single owner and every survivor; no wave needs an architectural decision. `ui/main_window.py`
  in waves 1 and 7, `data/models.py` in 3 and 7, `tests/test_d45_removal.py` in 1 and 8 (different lines, never
  concurrent). Wave 2 must not be split.
- **6 Scope integrity — pass.** No product scope added; `A91`/`A92`/`A93`/`A96`/`A99`/`A100`–`A104` are applied as
  written; no replacement order/cancel/protection surface (`ESC-061` moot); no registry under another name; `DG78`'s
  collision deliberately **not** fixed.
- **7 Existing-repo compliance — pass.** The marker sentence and Current Tech Stack are intact; the Codebase Summary
  is substantive (module facts, data models, integrations, each source-verified) and consistent with the proposal;
  every constrained stack item appears as `[existing]` before new decisions and nothing is replaced; labels complete
  (`[existing]` / `[new/changed]` / `[deleted]`), additive-only.
- **8 Frozen interfaces — pass.** Verbatim contracts (spot-checked above), nothing under construction frozen, the
  consumed-but-unmodified contracts present (`_table_columns`, `on_historical_error`, `_on_rt_stream_error`, alarm
  path), owning modules resolve, no duplicates.
- **9 Codebase map — pass after correction.** Every module section resolves; key files spot-checked
  (`ibkr/id_manager.py`, `data/db.py`, `services/sound_service.py`, `ui/ticker_session.py`, `ui/overlays/ict_overlay.py`);
  no section for a deleted module; status labels current; P5 book **2 / 13 / 0**; the D45 book **5 / 7 / 1**
  (`ESC-063` satisfied). Two stale artefacts were found and fixed at activation (§ *Activation corrections*): the header
  still carried revision-1 arithmetic (4 edited / 1 deleted / 3 adjusted) and a live "storage untouched (A87)" claim in
  the Portfolio row contradicted both the map's own P5 row and `D46.13`.
- **10 Pending doc sync — pass.** `docs/pending_doc_sync.md` does not exist.
- **Escalations — not edited.** `ESC-063` (open, PLAN) is satisfied from the Plan side (map now reads 5/7/1 with the
  `ESC-063` note) and stays open for the Code Reviewer to close. `ESC-061` is moot (module deleted; no task implements
  it). `ESC-059`/`ESC-060` stay BUILD-owned; `ESC-062` is folded into waves 1/7/9 with four sites, zero new tasks.

---

## Independent audit checklist

**1. Every audit DELETE row has exactly one owner.** Requirements rows 1–21 and 23 are each owned by one wave
(1/7 → wave 1; 4/5 → wave 2; 1/2/3/10 → wave 3; 11/12 → wave 4; 13 → wave 5; 14 → wave 6; 15–21 → wave 7; 23 → wave 9);
row 25's files are split across waves 1, 3, 4, 5, 6, 7, 8, 9 with no file edited by two waves. Row 24 is RETAIN by
design. **One site had no owner: row 22's third comment** (`ui/main_window.py:3065`, "…the exact mirror of the D28.6
inverse on the **close-order path** (see below)") — assigned to wave 7 at activation (C11). **No row is deleted twice.**

**2. No audit RETAIN row is deleted.** `IdManager` + `get_id` (six callers, incl. `ui/main_window.py:1095`) is frozen in
`S46` and present in the plan's survivor list; `nextValidId` survives as the CONNECTED transition (A102, driven by
`test_d40_tws_lifecycle` / `test_d25_alarm_monitor`); `classify_error` / `error_msg` / the 8000 ms line are frozen and
the **only** prose change to `ibkr/error_codes.py` is its 202 comment; ICT order blocks, `_order_by_recency`,
`sort_order`, `advancedOrderRejectJson` and the dividend path are all in the survivor set with consumers named. The
plan's `ibkr/bridge.py:42` decision (keep the `# Account & Orders` section header above the retained account/position
signals) is dispositioned and reasoned, not swept.

**3. The audit's seven gaps.** `(a)` `tests/test_d45_removal.py:523` — **covered** (wave 1 repoints it to
`_on_error`; the call site verified at `:523`). `(b)` `usage.md:167` — **covered** (wave 9; the command does name the
deleted suite). `(c)` `ibkr/account.py:39-42` — **covered** (wave 7 rewords the `Position.id` comment; verified live).
`(d)` `ibkr/bridge.py:42` — **covered as a documented keep** (Incidentally-affected), with the audit's own "harmless if
left" note. `(e)` `tests/test_d41_removal.py:97` — **covered as a keep** (file untouched) but it makes `D46.9`'s
absolute sentence literally false → `RG-D46-3`. `(f)` stale `.pyc` / `(g)` stale `dist/` + dev DB — **covered as
measurement/out-of-scope**, not as tasks: `DG87` scopes the scan to tracked `*.py` (the guard's `rglob("*.py")` does
exactly that, so `ibkr/__pycache__/orders*.pyc` cannot satisfy `find_spec`), `dist/` is a release rebuild, the dev DB is
a sample superseded by the legacy-fixture test. Recorded for the Code Reviewer: a per-wave **textual** grep over a
directory can still print `Binary file … matches` for a stale `.pyc` — that is residue, not a live symbol, and no task
should "fix" it by editing `__pycache__`.

**4. The audit's two corrections are applied.** `R10`'s false consumer evidence is corrected in the plan's survivor
table, architecture `S46` and the map (dead storage, retained to avoid widening the batch; grouping is
`strategy_detection` over `Position.id`) — **the plan no longer claims a display consumer**. `A99`'s "could only ever
hold `NULL`" is replaced by the byte-level truth in the plan and in four architecture sites; the drop is stated as the
batch's **only byte-destroying step**, still justified (invisible, unsettable, destroyed by the first update).

---

## Instrument (wave 8) and invariant I-1

The token migration lands **once**, in wave 8, after the last name dies (wave 7) — I-1 is coherent at every boundary
because the tokens are not in `_FORBIDDEN` until they are already gone, and the interim net is the mandatory per-wave
grep with the **final** list. The three token-mechanics claims are all verified:

- **`stop_loss`/`take_profit` must be substring** — the `positions`/`trade_groups` column list lives in one whole
  string constant (`data/db.py`'s `schema`), which whole-unit matching cannot see. Confirmed (one offending unit).
- **`reserve` must be `hasattr`, not a token** — 13 units across 11 files: `id_manager.py`'s own two, ten
  "preserve(s/d)" docstrings, and `ui/chart_panel.py`'s `_reserve_price_tag_lane`; the `reserve(` grep is clean
  (2 lines, both in `id_manager.py`). (The "all preserve" wording is corrected at activation.)
- **`_effect` must collapse to alarm-only** — `services/sound_service.py:151` carries the **string constant**
  `"_fill_effect"`, which the AST scan sees; `_effect` has exactly two callers (`play_alarm`, `play_fill`), so the
  collapse is safe and necessary for 0/0.

Discrimination: pre-P5 **41 / 10 files** and **40 twin hits**; simulated post-P5 **0 / 0** per the plan (whose premise
I verified per unit). `_SURVIVORS` 26 → 16 and `_FORBIDDEN` 53 → 80 are exact.

---

## Test book — 2 deleted / 13 adjusted / 0 added

Each adjusted file names its invalidated assertion. The four most likely to be wrong were spot-checked by execution:

| Check | Result |
|---|---|
| `test_sound_service` **8 → 6** | **Wrong — it is 9 → 7.** `--collect-only` reports **9** cases (4 alarm + 2 fill + 2 wav + 1 ensure-files); only `TestFillBlip`'s two go. `:76`'s `paths["fill"]` assertion is real and the only `paths["fill"]` reader in the tree. Corrected in the plan, architecture and map (C9/C13/C23). |
| `test_id_manager` **8 → 4**, six of eight touch `reserve` | **Correct.** 8 collected; `:10/:18/:32/:56` pure `reserve`, `:39` monotonic-with-reserve, `:74` concurrent (calls `reserve(3)` at `:85`, asserts `8 * 203` at `:97`) → 4 survive, two rewritten. |
| `test_order_rejections` **5 → 3 + 1 parametrised** | **Correct.** 5 functions (10 collected via a 6-code parametrize); wave 1 deletes the two registry cases + `_fresh_registry`/`_register` + the `ibkr.orders` import, repoints/renames the third, keeps both `classify_error` cases and `_make_window`, adds the 201/103/202 case with a reqId that matches no session. |
| three raw-SQL seeders | **Arithmetic was wrong — fixed.** Each has **11** column names / **11** `?` / **11** values (8 shared + `stop_loss` + `take_profit` + `updated_at`), so the removal is **two** names, **two** placeholders and the two `None` values → 9 / 9 / 9. The plan said "one placeholder", which would raise `ProgrammingError`. Corrected in four places (C12). |

Book scope confirmed: a `tests/`-wide grep finds the removed names only in the files the book lists (`UserOrder`:
order-rejections/ui-smoke/order-builders/d45-removal; `OrderRateLimiter`: d28-pacing; `order_limiter`: conftest +
d28-pacing + the guard; fill names: sound-service; `stop_loss`/`take_profit`: the five named files + the deleted
suite + the guard), so "no other test file changes" holds.

---

## Flagged issues — adjudicated

None changes what gets built, so **no requirements round is created** (owner policy); each is either ratified with the
plan's reading or corrected in the plan text, and the requirements-side wording is logged in `plan_notes.md`.

| # | Issue | Ruling |
|---|---|---|
| 1 | `AC-D46.10` calls the `reserve`-dependent concurrent case "kept" | **Plan-level correction ratified.** Six of eight cases touch `reserve`; the case survives **rewritten** (reserve block out, `8 * 203` → `8 * 200`), 8 → 4. AC wording → `RG-D46-4`. |
| 2 | `D46.5` omits `test_sound_service.py:76` | **Plan-level:** the plan's book is operative and names the site; the **count** it inherited (8 → 6) is wrong and is corrected to 9 → 7. → `RG-D46-5`. |
| 3 | `D46.12` cites SQLite 3.54.0 (app links 3.53.1) | **Plan-level:** capability holds (≥ 3.35); `S47` cites the measured version. → `RG-D46-6`. |
| 4 | `D46.13` depends on the Validator marking activated sections | **Executed this activation** — markers attached at all **13** architecture sites and at **every** plan site the plan's own *Document trail* table enumerates (plus `AP-D45-9` and the D45 test-book line) (plus the frozen rows and the two traceability rows). → `RG-D46-9` covers the residual `requirements.md` sites. |
| 5 | `AC-D46.2`'s `hasattr` measurable is unsatisfiable | **Plan-level:** `__dict__` membership is the AC's substance measured more strongly; re-verified (`EWrapper` defines all three → `hasattr` is `True` before and after). Already `RG-D46-2`. |
| 6 | `D46.9`'s `reserve(` is a grep pattern, not a token | **Plan-level:** measured 13 units / 11 files; `hasattr(IdManager, "reserve")` is the instrument; grep keeps the paren. → `RG-D46-3` covers the sibling "no order-named symbol" overreach. |

Also adjudicated: `ESC-061` **moot** (no task implements it); `ESC-063` **satisfied** by the map; `DG78` item (2)
**open by decision** (no task may reorder the error path, no test may pin the collision); `DG80` **resolved** by
deleting `reserve`; `DG84`–`DG86` handled by `S50`/`S48`/`S47`; `DG87` handled by the guard's `*.py` scope.

---

## Activation corrections (editorial / requirement-directed — no new decision)

Applied by the Validator at activation; each is a fact, a citation, or a requirement's own instruction. Plan's drafts
should not repeat them.

1. **C1 — `D46.13` markers (architecture):** a supersession banner on the D45 section and a `SUPERSEDED BY D46 / A99`
   note at every storage claim — `S33`'s row, the `test_stop_loss_target` row, the three data-model bullets, the D45
   Data Model paragraph and its five rows, the SQLite integration row, the three frozen SL/TP rows (**VOID from P5**),
   the data-safety bullet, acceptance row (d), the `AC-D45.10` traceability row, and the A80 row.
2. **C2 — `D46.13` markers (plan):** a banner on the D45 section and markers at the eight storage claims
   (`:2004`–`:2005`, `:2085`, `:2188`, `:2189`, `:2251`, `:2337`, `:2422`–`:2423`) plus `AP-D45-9`.
3. **C3 — A99 byte-truth** (architecture ×4, plan ×1): "could only ever hold `NULL`" replaced by "the only
   byte-destroying step; a row that never updates again keeps its legacy bytes and loses them here".
4. **C4 — R10 rationale** (plan survivor table, `S46`, map): `TradeGroup`/`trade_groups`/`position_group_map` are dead
   storage retained to avoid widening the batch; grouping is `strategy_detection` over `Position.id`.
5. **C5 — stale wave numbers:** the instrument is wave **8** (was "wave 3" in two architecture places, one plan place
   and the flagged note) and the `classify_error` prose is wave **9** (was "wave 4"); AR-D46-3's reproduction is wave
   **10** (was "wave 5").
6. **C6 — duplicate supersession item 17** (same deviation record as item 9) merged into item 9; numbering kept stable.
7. **C7 — interrupted migration wording:** "at most one column is still present" → "only the columns not yet dropped
   remain" (measured: DDL autocommits, so a crash can leave any not-yet-dropped column).
8. **C8 — `reserve` measurement precision:** 13 units = `id_manager.py`'s two + ten "preserve(s/d)" + `_reserve_price_tag_lane`.
9. **C9 — exact vs substring units:** `orders` 5 substring / 2 exact; `Orders` 2 substring / 1 exact.
10. **C10 — `AP-D46-9` corrected:** `USAGE.txt` **is** edited in wave 9 (its stop/target bullet), as `D46.13` requires.
11. **C11 — row 22's third site assigned:** the `:3065` "close-order path" comment is rewritten in wave 7 (its only
    coherent owner — the same method, the same wave that edits its neighbours).
12. **C12 — seeder arithmetic:** "one placeholder" → **two placeholders and the two `None` values** (11 → 9 of each).
13. **C13 — sound-service count:** 8 → 6 corrected to **9 → 7** (executed `--collect-only`).
14. **C14 — map reconciled** (Plan-owned; corrected per the Orchestrator's instruction): header arithmetic to
    **11 production modules touched / 2 suites deleted / 13 adjusted / 0 added**, decisions `S39`–`S50` / risks
    `AR-D46-1`–`AR-D46-12`, current register in the docs table, `plan_review_P5.md`, the Portfolio row's "storage
    untouched (A87)" replaced by the dropped end state, the D45 summary marker, the "overturned by P5" list, the
    sound count, and the R10 survivor line.
15. **C15 — activation:** `docs/plan.md` § P5 → `Status: READY_FOR_TASK_MANAGER`; the plan and architecture status
    preambles/handoffs now state activation (no "draft / demoted / not active" text remains).

---

## Requirements notes (recorded, none escalated)

`docs/plan_notes.md` gains **`RG-D46-3`–`RG-D46-9`**, all **open, non-blocking, no escalation** — none would change
what gets built, which is the owner's stated bar for a requirements round:

- **RG-D46-3** `D46.9`'s "no order-named symbol outside the two sets" vs `test_d41_removal.py:97` and
  `bridge.py:42` (both deliberately kept).
- **RG-D46-4** `AC-D46.10`'s "keeps" vs the concurrent case (rewritten, not untouched).
- **RG-D46-5** the four book omissions (sound `:76`, id-manager concurrent, seeder placeholders, guard sub-edits).
- **RG-D46-6** `D46.12`'s SQLite version citation (3.54.0 vs the app's 3.53.1).
- **RG-D46-7** `A99`'s "could only hold `NULL`" overstatement (byte-level truth substituted).
- **RG-D46-8** `R10`'s consumer evidence (dead storage, corrected rationale).
- **RG-D46-9** **`requirements.md`'s own seven live pre-D46 claims** (`:1183`, `:4337`, `:4399`, `:4539`, `:4565`,
  `:4584`, `:5515`) contradicting its `D46.13` correction record. The other five documents are clean. This is
  analyst-owned text and **must not be charged to Build or Plan**; it needs seven `SUPERSEDED BY D46 / A99`
  annotations at the next requirements revision (the pattern already used at `:223`, `:483`, `:1171`, `:4345`,
  `:4508`).

Two earlier notes stay as they were: **`RG-D46-1`** (rejection-file shape) **addressed**; **`RG-D46-2`**
(`AC-D46.2`'s measurable) **open, non-blocking**, satisfied by `AP-D46-14`.

---

## Survivals, boundaries, and what must not happen

- **No replacement UI, no registry under another name, no dormant helper, no `pass` stubs, no compat aliases.** The
  plan states this three times (Build's rules, `S39`, supersession item 13) and the guard's forbidden set enforces it.
- **`ESC-061` is moot** — no task implements the docstring note; the Code Reviewer closes it as moot.
- **No DB file copy**, no error-path reordering (A94/DG78), no new dependency, no stack change; `pyqtgraph` stays locked.
- **Wave 2 is one task** (emitter + signal); if the graph has to split it, that is a stop-and-report, not a split.
- **Wave 7 owns the schema and every reader** and is the only wave that is red until its own test edits land.
- **Wave 10** must record the pre-P5 guard failure set (41 / 40) beside the post-P5 numbers, and reproduce 201/103/202
  per code on a real offscreen `MainWindow`.

## Task Manager Readiness

**YES.** Ten tasks, `P5-T01 → … → P5-T10`, strictly sequential, with `touches_files` exactly as the per-file map says
(`ui/main_window.py` in waves **1 and 7**, `data/models.py` in **3 and 7**, `tests/test_d45_removal.py` in **1 and 8**).
Wave 7 now also carries the `:3065` comment rewrite (C11) and the corrected seeder arithmetic (C12); wave 5's sound
book is 9 → 7 (C13). No task requires a new architectural decision.

## Final Decision

**Status: APPROVED** — `docs/architecture.md` § *Phase P5* is active and internally consistent; `docs/plan.md` §
*Phase P5* is `READY_FOR_TASK_MANAGER`; `docs/codebase-map.md` is current for P5 (2 / 13 / 0); the D45 storage claims in
both canonical documents carry `SUPERSEDED BY D46 / A99` markers; `docs/plan_notes.md` records `RG-D46-3`–`RG-D46-9`
as open and non-blocking. No blocker remains for this phase.
