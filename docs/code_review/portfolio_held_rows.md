# Investigation — portfolio shows `HELD` and `H`; SPXW options read `STOCK`; Account shows `—`

**Reviewer:** Code Reviewer agent · **Date:** 2026-10-15 · **Repo:** `29067af` (+ uncommitted
`docs/code_review/*`, `docs/requirements/*`) · **No live TWS was used by this review** — every
observation below is a read-only DB dump or a static/`file:line` reading of the tree; nothing was
fixed and no code/requirements/plan/architecture/task/build file was touched.

**Owner report (verbatim):** *"In portfolio I can see `HELD` and `H` symbol."* with a screenshot of
Account Summary → positions table showing 6 `SPXW 261015P07…` rows (Qty 0.00, Type STOCK, Mult 100),
then `HELD` (10.00 @ 40.00, STOCK, 1) and `H` (1.00 @ 2.00, STOCK, 1), and `Account: —`.

**Headline answer.** `HELD` and `H` are **rows persisted in the production database**, not live
broker positions — they are test/probe fixtures that were written into
`~/Library/Application Support/NDThinkChart/charting_app.sqlite3` by a **non-hermetic offscreen run**,
and the panel renders the whole table. The six `SPXW` rows **are** real positions from the owner's
live account (`U13148604`); they read `STOCK` because the position→model mapping reads contract
fields by names `ibapi.Contract` does not have. `Account: —` is an independent one-line plumbing bug.

---

## 0. The screenshot is the database table (why this is the crux)

`ui/main_window.py::_on_position_end` (`:3319-3335`) — raised by `bridge.position_end`
(`:677`) when `reqPositions` completes — does:

```python
rows = db.conn.execute(
    "SELECT symbol, account, con_id, contract_type, qty, avg_cost, "
    "local_symbol, multiplier, expiry, strike, right, stop_loss, "
    "take_profit, trade_group_id FROM positions"          # :3323-3327 — the WHOLE table
).fetchall()
positions = [Position(...) for row in rows]               # data.models.Position (id defaults None)
self.portfolio_panel.set_positions(positions)             # :3335
```

So the panel displays **every row in `positions`**, unmodified. The screenshot shows **exactly 8
rows**; the production `positions` table holds **exactly 8 rows** (6 `SPXW` + `HELD` + `H`). That
one-to-one match is what tells us where the junk comes from: it is *in the table*.

(On this screen the render completed because `_on_position_end` builds `data.models.Position`, whose
`id` exists and defaults to `None`; the *live* `position_update` path crashes for the separate
reason ESC-032 documents. See §5.)

---

## 1. `HELD` and `H` are persisted rows in the production DB (PROVED)

Read-only dump (`config/paths.py::get_db_path` → user-space; DB opened `-readonly`):

```
id | symbol                    | account  | con_id     | contract_type | qty | avg_cost | local_symbol              | mult | expiry | strike               | right | updated_at
 1 | SPXW  261015P07685000     | U13148604| 928308014  | stock         | 0.0 | 0.0      | SPXW  261015P07685000     | 100  |        | 7685.0               |       | 1792090825
 2 | SPXW  261015P07625000     | U13148604| 921826029  | stock         | 0.0 | 0.0      | SPXW  261015P07625000     | 100  |        | 7625.0               |       | 1792090825
 3 | SPXW  261015P07665000     | U13148604| 928307992  | stock         | 0.0 | 0.0      | SPXW  261015P07665000     | 100  |        | 7665.0               |       | 1792090825
 4 | SPXW  261015C07780000     | U13148604| 925789713  | stock         | 0.0 | 0.0      | SPXW  261015C07780000     | 100  |        | 7780.0               |       | 1792090825
 5 | SPXW  261015C07760000     | U13148604| 925789692  | stock         | 0.0 | 0.0      | SPXW  261015C07760000     | 100  |        | 7760.0               |       | 1792090825
 6 | SPXW  261015P07605000     | U13148604| 928307894  | stock         | 0.0 | 0.0      | SPXW  261015P07605000     | 100  |        | 7605.0               |       | 1792090825
 7 | HELD                      | DU123    | 999        | stock         | 10.0| 40.0     | HELD                      | 1    |        | 1.7976931348623157e+308 |       | 1792086727
13 | H                         | DU1      | 1          | stock         | 1.0 | 2.0      | H                         | 1    |        | 1.7976931348623157e+308 |       | 1792086736
```

- `updated_at` decoded: `1792090825` = **2026-10-15 19:00:25 UTC** (the six `SPXW`);
  `1792086727` = **17:52:07 UTC** and `1792086736` = **17:52:16 UTC** (`HELD`/`H`). The two junk rows
  landed ~2 minutes before today's live-session escalations (ESC-032 opened 17:54 UTC) — the same
  offscreen investigation session.
- **Row 7 (`HELD`) matches a committed test arg-for-arg.** `tests/test_d27_account_subs.py::
  test_d27_6_positions_populate_panel` (`:78-94`) builds `Contract()` with `symbol="HELD"`,
  `localSymbol="HELD"`, `conId=999`, `multiplier="1"` and emits
  `position_update.emit("DU123", contract, 10.0, 40.0)`. The stored row is
  `HELD | DU123 | 999 | 10.0 | 40.0 | HELD | 1.0` — an exact match. (`HELD` also appears in
  `tests/test_d27_position_prices.py`.)
- **Row 13 (`H` / account `DU1` / `con_id 1`) matches no committed test** — `grep` finds no
  `symbol="H"` / account `DU1` anywhere in `tests/` or the tree. It is an **ad-hoc probe** row (e.g.
  a hand-run `python -c` that called `_on_position_update("DU1", …, 1.0, 2.0)`).

Neither row is anything a broker would send. `DU123`/`DU1` are IBKR **demo** account numbers and
`con_id 999`/`1` are synthetic; the live account in the same table is `U13148604`.

### Why a test/probe could write to the *user's real* DB (PROVED)

- `config/paths.py::get_db_path` (`:68-81`) returns the **user-space production path** whenever
  `DB_PATH` is unset. Verified:
  `unset DB_PATH → ~/Library/Application Support/NDThinkChart/charting_app.sqlite3`;
  `DB_PATH=/tmp/x.sqlite3 → /tmp/x.sqlite3`.
- `tests/conftest.py` (`:8-13`) sets `DB_PATH` to a temp file at import, so **under pytest** the DB is
  hermetic. Verified: the temp DB exists and its `positions` table is **empty**
  (`sqlite_sequence.seq = 1`, i.e. tests used *that* file). So pytest did not write these rows.
- Therefore only a **non-pytest process** — a manual offscreen script / REPL that imported
  `ui.main_window` and drove `_on_position_update` (which calls `_upsert_position`,
  `ui/main_window.py:3337-3363`) — writes fixture rows into the owner's real DB. `_upsert_position`
  is called from nowhere else (`_on_position_update` only), and there is no seeding/demo path
  (`grep` for any `seed`/`DEFAULT_POSITIONS` in `data/`/`ui/` → none).

**Verdict for (a): the junk is in the DB, at insert time — not generated live at render time.**

---

## 2. Why the six `SPXW` rows show `Type STOCK` (PROVED) — real positions, mislabelled

These are genuine live rows (account `U13148604`, real SPX strikes 7605–7780, IBKR SPXW
`localSymbol` format `SPXW  261015P07685000` with the two-space padding). The type is wrong because
`ui/main_window.py::_on_position_update` reads contract fields by **names `ibapi.Contract` does not
have**. Introspection of the installed `ibapi` (`9.81.1.post1`) confirms:

| code reads (`_on_position_update`) | `hasattr` on real `Contract`? | real attribute | effect |
|---|---|---|---|
| `getattr(contract,"class_","stock")` `:3286` | **False** | `secType` | **always `"stock"`** → every option/future renders & persists as STOCK |
| `getattr(contract,"lastDateOrMonth",None)` `:3288` | **False** | `lastTradeDateOrContractMonth` | expiry always `None` (DB expiry column blank even though `localSymbol` carries `261015`) |
| `getattr(contract,"putCall",None)` `:3290` | **False** | `right` | right always `None` (DB `right` blank for P and C options) |
| `getattr(contract,"strike",None)` `:3289` | True | `strike` | returns ibapi's **`UNSET_DOUBLE`** sentinel when unset |

`ibapi.contract.UNSET_DOUBLE == 1.7976931348623157e+308 == sys.float_info.max` — verified equal to
the raw value stored in the `HELD`/`H` `strike` column.

**Consequences beyond the label.** `_parse_contract_type` (`ibkr/account.py:42-44`,
`s.strip().lower()`) is fine *given the right input*; the input is wrong. Since `contract_type` is
always `"stock"`, `ActivePortfolioPanel._group_and_render` (`ui/active_portfolio_panel.py:271`)
never classifies an option leg (`p.contract_type == "option"` is never true), so option-spread
detection / the Strategy+Group columns never fire for real options. This is the same root cause the
project already recorded as an **open follow-up** — `docs/phase-changelog.md:176` and
`docs/architecture.md:2524-2525, 2711` say verbatim: *"`contract.class_` is never populated
(`_on_position_update` always stores `"stock"` … fix = derive from `contract.secType`, own
commit)"*. It had **no escalation and no task**.

### Why the six rows show `Qty 0.00`

`_on_position_update` passes `qty=pos` through untouched (`:3304`) and `_upsert_position` stores it
raw; there is **no `qty == 0` filter anywhere** and `_render_table`
(`ui/active_portfolio_panel.py:295-314`) renders every element of `_positions`. The stored `0.0` is
therefore what IBKR reported on the `position()` callback. Most consistent read: these are 0DTE
SPXW legs (`expiry 261015` = today) the account went flat on, and TWS emitted a final `position`
callback with `qty 0` which the app persisted and then displays. I cannot confirm IBKR's exact
emit-timing offscreen; what **is** proved is that the app neither zeroes nor filters it. Flat rows
are not holdings and should not read as positions — flagged, with the "hide `qty == 0`?" choice
called out as a small product decision rather than assumed.

(The `Multiplier 100` on those rows is **correct** for SPX options — only the Type label is wrong.)

---

## 3. `Account: —` (PROVED) — an independent one-line plumbing bug

`ui/active_portfolio_panel.py::_render_summary` (`:262`) reads
`self._summary.get("Account", "—")`. But the only tags ever requested are
`ui/main_window.py::_subscribe_account_data` (`:1219-1224`):
`"AccountType,AvailableFunds,BuyingPower,TotalCashValue,NetLiquidation"` — **there is no `"Account"`
tag**, and IBKR's `reqAccountSummary` has no tag named `Account` (the account id arrives as the
**callback's `account` argument**, which `_on_account_summary`, `:3263-3270`, stores in
`self._account_id` — used by the connection badge at `:1155` — **not** in `_summary`). So the
`"Account"` key is never present and the field is permanently the `—` fallback. That is exactly why
`Net Liq` and `Cash` populate while `Account` does not.

---

## 4. Full trace of every `symbol`-producing path (so `HELD`/`H` cannot hide elsewhere)

| Path | `symbol` derivation | verdict |
|---|---|---|
| live `_on_position_update` `:3294` | `getattr(contract,"localSymbol",None) or getattr(contract,"symbol","")` | correct for real contracts (`localSymbol` = full `SPXW  261015P…`, **not truncated**; the screenshot truncation is only the narrow column). For a synthetic `Contract()` in a probe, `localSymbol`/`symbol` are whatever the probe set → `"HELD"`/`"H"`. |
| bulk `_on_position_end` `:3328` | `row[0]` from `positions.symbol` | echoes whatever was persisted |
| account summary | `_summary["Account"]` only feeds the header text | never a position symbol |
| any string split / fixed-width parse / message parse | none found — `grep` shows no `localSymbol` slicing | none |

No mis-slice, no IBKR-message parse, no fixed-width parse. The two rows come from the **insert side**
(§1).

---

## 5. Relationship to the already-open ESC-032 (NOT duplicated)

ESC-032 is the two-`Position`-classes / missing-`id` defect (the **live** path raises
`AttributeError` at `active_portfolio_panel.py:308`). The rows in this report are visible via the
**bulk** path, which is unaffected by ESC-032 (it builds `data.models.Position`, `id=None`, so
`strategy_by_id.get(None,"—")` works). This investigation does **not** re-open or overlap ESC-032;
its own second half (the bulk `SELECT` omitting `id`, `:3323`) is already recorded there and is
deliberately left untouched here.

---

## 6. Impact & routing decision

- **`HELD`/`H` (ESC-043).** Cosmetic today (junk rows shown as holdings; the table is not scoped to
  the live account). It is **not** merely cosmetic if left: the rows are selectable, and once
  ESC-032 populates `id`, a user could act on a junk row (Set SL/TP, Close). Fix is two-part —
  **delete the rows** (owner/data action; I did not touch the DB) **and** stop a non-hermetic run
  from writing to the user-space DB, with account-scoping so foreign rows never render.
  → **BUILD** (`bug` / `should-fix`).
- **Option fields mis-read (ESC-044).** Same panel, different root cause: `_on_position_update`'s
  contract mapping. Already documented as an open follow-up but never escalated/tasked. One coherent
  change (derive from `secType` / `lastTradeDateOrContractMonth` / `right` / sentinel-normalized
  `strike`). → **BUILD** (`bug` / `should-fix`).
- **`Account: —` (ESC-045).** Independent plumbing bug in the summary tags/reader. → **BUILD**
  (`bug` / `should-fix`).
- No PLAN / REQUIREMENTS / TASK_MANAGER route is warranted: the code contradicts its own documented
  contract (`security` is not at stake; no AC is contradicted; the fix is inside the existing
  methods), so it is a code bug, not a design/requirements gap.

I did **not** fix anything. The production DB was opened **read-only**.

---

## 7. Warranted regression tests (invariant form)

1. **DB hygiene / panel scoping (ESC-043).** Seed `positions` with (a) a row for a **foreign**
   account (`DU123`, symbol `HELD`) and (b) a row for the subscribed account; drive the real
   `_on_position_end`; assert the **foreign row is not rendered** and only the real account's row is.
   Companion guard: a test (or a DB-layer assertion) proving a probe/test context cannot open the
   user-space production DB.
2. **Position model from real Contract (ESC-044).** Build a **real `ibapi.contract.Contract`** (not
   a `SimpleNamespace`) with `secType="OPT"`, `lastTradeDateOrContractMonth`, `right`, `strike`,
   drive `_on_position_update`, and assert the resulting `Position.contract_type == "option"`,
   expiry/right populated, and `strike` not the `UNSET_DOUBLE` sentinel. Replace
   `tests/test_d27_position_prices.py::_held_contract()`'s fake — whose
   `SimpleNamespace(…, lastDateOrMonth="", putCall="")` mirrors the **production code's wrong
   attribute names** and therefore cannot fail.
3. **Account field (ESC-045).** After an `account_summary` update, assert the panel text contains
   `Account: <id>` (not `Account: —`).

### Why the suite is green on all of this today

- **No test drives `_on_position_end`** (`grep _on_position_end tests/` → 0 hits), so the
  whole-table render is never exercised with a foreign row.
- **No test asserts the `Account:` text** (`grep "Account:" tests/` → 0 hits).
- The one test that uses a **real** `ibapi Contract` (`test_d27_account_subs.py:80-94`) asserts only
  `any(p.symbol == "HELD" …)` — nothing about `contract_type`, expiry, right, or the Account field.
  It is also the source of the `HELD` row when run non-hermetically.
- The nearest position test (`test_d27_position_prices.py`) mocks the contract with the **same wrong
  attribute names** the production code uses, so the expiry/right/type defects are invisible to it.
- `test_d28_6_close_contracts.py` inserts positions directly with an explicit `contract_type` and
  never routes through `_on_position_update`, so it cannot see the mapping bug either.

---

## 8. Proved vs inferred

**Proved (repo `file:line` / live read-only DB / installed-wheel introspection):**
- `HELD` (id 7) and `H` (id 13) exist in the production `positions` table; row 7 matches
  `test_d27_account_subs.py` arg-for-arg; row 13 matches no committed test (§1).
- `get_db_path()` returns the prod path with `DB_PATH` unset; pytest is hermetic (temp DB empty) (§1).
- `_on_position_end` renders the whole table (§0).
- `Contract` lacks `class_`/`lastDateOrMonth`/`putCall`; `strike` default == `UNSET_DOUBLE`
  (`1.7976931348623157e+308`) (§2).
- `_render_summary` reads `"Account"`, which is never requested (§3).
- Coverage gaps: no `_on_position_end` test, no `Account:` assertion, the position test's wrong-attr
  fake (§7).

**Inferred / not locally verifiable:**
- That IBKR emitted `qty 0` for the six SPXW legs (the app passes `pos` through untouched, so the
  `0.0` is IBKR's value, but the emit-timing/why is not reproducible offscreen) (§2).
- That the two junk rows were written by a specific manual offscreen/REPL probe (the *path selection*
  and the *fixture values* are proved; the exact invoking command is not recorded) (§1).

---

## 9. Open-escalation close-out check (this pass)

All previously open entries (`ESC-032`…`ESC-042`) were re-checked against the tree: none links to a
task that has since moved to `done`, and no `architecture.md`/`plan.md`/`requirements.md` version
relevant to them changed this cycle (the two blocking ones — ESC-032/ESC-033 — are today's fresh
live-run defects). Nothing was closed; no re-diagnosis performed beyond recording the residual.

---

## 10. Housekeeping

- Wrote this file; appended `ESC-043`, `ESC-044`, `ESC-045` to `docs/code_review/escalations.json`;
  appended the matching entry to `docs/code_review/review_log.md` (ending `Status: REVIEW_COMPLETE`).
- **No** code, requirements, plan, architecture, task, or build file was modified.
- The production DB was opened **read-only**; the two junk rows were **not** deleted (that is the
  owner/data action in ESC-043).
