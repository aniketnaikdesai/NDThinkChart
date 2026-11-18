# Code Review — Phase P23 (D65 Option Spreads, Portfolio-stack removal)

**Pass:** phase-final, **full pass** (phase-final always full; the independent suite run is also red).
**Scope (incremental):** all 14 tasks with results newer than the P22 `REVIEW_COMPLETE` marker —
P23-T1..T14 (`docs/code_review/precheck.json`, `review_marker.log = review_log_P22.md`).
**Inputs consumed as ground truth:** `precheck.json` (0 fail_fast, 0 unattributed tree changes,
overlaps informational only), `test_verification.json` (verdict **fail**, exit 1, 85.31 s,
exactly two failing cases), `build_log.md` (P23 waves 330–349), every S/M task (no size L), and
the committed tree `82b82fd`.

**Verdict:** the phase's production work, deletions, residue gate and consistency claims hold.
Three findings are open: one breakdown gap (the two red contracts, ESC-116) and two code
findings (ESC-117 blocking, ESC-118 should-fix). `REVIEW_COMPLETE` is written with these open —
they are listed for the Orchestrator's pause/approval step, not waived.

---

## ESC-116 — `tests/test_d65_option_chain.py`: two wave-scoped contracts are false at phase end

- **Linked task:** P23-T6 (owns the file and its AC5). **Category:** consistency. **Severity:** blocking.
- **Root cause:** `bad_task_breakdown` — P23-T6-AC5 is worded "**Given this wave**, Then no
  production module outside `ibkr/` calls the new helpers **yet**, the four account/position
  EWrapper overrides and their four bridge signals **are still present** (they are P23-T11's
  deletions)". Both clauses were true at P23-T6's wave and are deliberately false at phase end:
  P23-T9's `ui/main_window.py` wiring is the **designed** first caller, and P23-T11 deleted the
  overrides/signals by owner decision. No task owned re-pointing the two cases: P23-T13's AC
  ("the full offscreen suite is green") had a `touches_files` (residue gate, `usage.md`,
  `option_ladder.py`) that cannot reach `test_d65_option_chain.py`, and its embedded gate record
  honestly logs `3 failed, 1682 passed` and defers them to "that contract's owner".
- **Adjudication:** these are **stale contracts, not regressions**. Neither is a Build defect in
  the code they fail on.
  - `test_no_production_caller_outside_ibkr` — reproduced: `assert offenders == []` with 7 hits,
    first `ui/main_window.py:get_option_contract`. The sweep (`_NEW_HELPERS` × `_production_modules`,
    skipping `.venv/.git/tests/docs/graphify-out/...`) only exempts `ibkr/`, so it forbids the
    wiring P23-T9-AC1..AC5 require. **Fix: re-point (allow `ibkr/` + the named live wiring in
    `ui/main_window.py`), never delete** — the caller-discipline guard is real.
  - `test_account_and_position_overrides_and_signals_remain` — reproduced: `account_summary` signal
    missing (`hasattr` False) because P23-T11-AC1 mandates absence. The case asserts the inverse of
    its own phase. **Fix: invert to the absence assertions** that `tests/test_ui_smoke.py:48-49`
    and `tests/test_d45_removal.py` block (d) already make.
- **Routing:** `TASK_MANAGER` (ESC-116) — rewrite P23-T6-AC5 (graph + suite docstring/banner) to the
  two phase-final invariants, extend the footprint, then re-dispatch Build for the test edit.
  Folding in the third red item P23-T13 recorded (`test_d64_batch_gate.py::test_p22_t5_ac2_shared_seam_record`):
  it is **already green on the committed tree** (an artefact of the uncommitted wave) — no action.

## ESC-117 — OFF → ON leaves the engine believing the pre-OFF legs are live (stale values shown as current)

- **Linked task:** P23-T9. **Category:** bug. **Severity:** blocking.
- **Reproduced** with the real `MainWindow` against the suite's fake TWS (`_make_window` /
  `_toggle_on` / `_deliver_chain` / `_settle`), offscreen, temp `DB_PATH`:

  | step | `_md_line_count()` | `_option_leg_req` | engine `live_legs()` | CCS row 0 |
  |---|---|---|---|---|
  | ON, settled | 16 | 16 | 16 | `SPX 20261117 7360/7380 −1.00 −1.20 −0.020 0.0004` |
  | OFF | 0 | 0 | 16 | cleared |
  | ON again (chain re-delivered, full settle) | **1 (spot only)** | **0** | **16** | **same pre-OFF values** |

  Zero option subscribes are issued on the second ON (`stale_legs()` empty), so the ladders render
  dead prices as live values with no line behind them.
- **Cause:** `SpreadEngine.toggle_off()` (`services/option_spread_engine.py:364-366`) clears only
  `_on`/`_seed_active`; `_subscribed`, `_leased`, `_window_legs`, `_anchors`, `_session_anchor`,
  `_seed_bounded`, `_quotes`, `_stale` survive, and `on_chain()` (:389-405) only resets on an expiry
  **change** — a same-session ON re-requests the same 0DTE expiry. `MainWindow._option_stop()`
  (`ui/main_window.py:2061-2085`) cancels the real lines but never tells the engine. Same stale set:
  `_option_subscribe_leg()` (:2276-2280) gates on `leg in live_legs()` and `_option_cutoff` but not
  `_option_active`, so a `PacingExceeded` `singleShot` retry (:2291-2296) firing after OFF opens a
  line while the panel is OFF (AC-D65.9's "zero reqIds" is then violated).
- **Why the suite missed it:** no case toggles ON twice in one window; the OFF case asserts only the
  off-state. Routed to `BUILD` (ESC-117) with the reset + guard + regression case.

## ESC-118 — the residue gate's sole allowlist entry excuses an unused alias via a document citation

- **Linked task:** P23-T13. **Category:** quality. **Severity:** should-fix.
- `services/option_spread_engine.py:1637` `OptionSpreadEngine = SpreadEngine` has **no production
  reader**; `tests/test_d65_residue.py:108-122` allowlists it citing
  "`docs/tasks/task-graph.json` P23-T7 signature `class OptionSpreadEngine`" — a document mention,
  not a registration site. `test_census_allowlist_cites_a_live_site` only checks the file exists.
  It is the **only** entry in `CENSUS_ALLOWLIST`, so the allowlist currently exists to keep this one
  dead symbol green: a narrow-looking carve-out that is convenient in substance, and it makes
  clause (i) passable by any symbol with a doc mention.
- **Checked and not a violation:** clause (iii)'s scoping to P23-authored files hides nothing today —
  I ran the gate's own `scan_unused_imports` / `scan_noqa_imports` / `scan_unreachable` over
  `ui/main_window.py`, `ui/watchlist_panel.py`, `ibkr/{bridge,client,contracts,market_data}.py`,
  `data/{db,models}.py`, `ui/ticker_session.py`, `tests/conftest.py`: all empty.
- Routed to `BUILD` (ESC-118): delete the alias + entry (or make the citation a real code site) and
  tighten the allowlist check.

---

## Verified clean (full pass duties)

**Escalation close-out.** `escalations.json` has **no open entries** (106 total, all addressed);
`precheck.json` `escalation_updates` is empty. Nothing to re-verify or close.

**Owner-confirmed deletions are complete.** No production module reads the dropped tables:
`positions` / `trade_groups` / `position_group_map` appear only in `data/db.py:164-179` (the guarded
child-first `DROP`, after `db_backup.backup_before_drop`) and in `data/db_backup.py` (copy
verification, read-only `mode=ro`, integrity + row counts, raises `BackupVerificationError` before
any drop). No `SELECT/INSERT/UPDATE` against them survives. `ibkr/account.py`,
`services/strategy_detection.py`, `ibkr/account` imports, `account_summary`/`position_update`
signals, `build_position_from_ib`, `data.models.Position`/`TradeGroup` appear only inside
absence assertions and forbidden-token tables. `ui/active_portfolio_panel.py` and its seven suites
are deleted; the surviving suites are re-pointed, not weakened (diff scan: no added
`skip`/`xfail`/`assert True`; every deleted test belongs to a deleted subject; 928 asserts added vs
283 removed, the removed ones tracking deleted subjects).

**S-P23-24 badge re-point is as recorded, not drift.** `conn_badge_text(monitoring_paused=False)`
returns `● Connected` / `#34d399`, paused keeps D40's amber wording, `_update_conn_badge` reads no
account state, no port-derived "Live" label invented; the port guard is untouched and the gate
record names it as the one phase-internal consequence (no requirements text edited).

**Numbers and formulas are identical everywhere.**
`display_bases` = `(long.ask − short.bid, long.bid − short.ask)`; `credit_bases` their exact
negatives with `credit_mid` the mean; credit spreads render negative by design (asserted).
`match_band = max(0.05, option_tick)` with the 0.05/0.10 break at 3.00. Target gate
`0.05 ≤ T ≤ 19.95` (`ui/option_spreads_panel.py:54-56,360`). Line accounting: `MAX_OPTION_LINES = 16`
in the engine lease pool + one spot line in `_md_line_count()` = 17. Canonical fixtures
`7425/7445`, `7340/7320`; `7425/7435` and `7315/7435` appear only as rejected examples, `7435/7455`
as the legal 20-wide non-banned pair. `docs/plan.md`, `docs/architecture.md`, the five phase suites,
`usage.md` and the T14 record state all of it identically.

**Residue gate is real.** `tests/test_d65_residue.py` 35 passed on the tree. It is proven red on its
seeded fixture by exercising the *same* scanner functions (`test_gate_is_red_on_a_seeded_dead_symbol`,
`test_gate_is_red_on_a_seeded_unconnected_signal`, and the red-then-green pair). Carve-outs: the
token carve-out is machine-checked (`test_every_carve_out_entry_is_earned`) and its stated rationale
matches its entries except `tests/test_d65_option_chain.py` — which is exactly ESC-116's residue, not
an independent hole. The single census-allowlist entry is ESC-118.

**Mock/fake/stub scan (B.6, blocking invariant).** Grepped the P23 diff's production files
(`ui/`, `services/`, `data/`, `ibkr/`, `config/`) for `mock|fake|stub|simulat` ×
`endpoint|client|service|server|api|harness`: three hits, all **comments** about test-host stubs
(`ui/main_window.py:273` describes the LWC factory seam; `ui/ticker_session.py:163,1054` note that
tests may pass a stub host). No mock/fake/stub/simulated endpoint, client, service or harness in
production code, and no production module imports a test fake. Clean.

**Usage docs.** The user-facing change (Portfolio panel → Option Spreads; account plane and strategy
auto-detection gone; three tables dropped after a verified backup) is documented in `usage.md`
(UI overview row, the "Option Spreads (view-only)" workflow, the tables section, the test command
list). `USAGE.txt` is a quick-start pointer with no panel inventory — correctly untouched. No
`doc_required_unmet` flags.

**P23-T14 record.** `docs/archive/probe_records/d65_paper_tws_acceptance.md`: all six AC-D65.19 items
unchecked with `Result: PENDING`, an empty evidence field each, header/line-count table, sign-off vs
explicit-waiver field; no fabricated result, and it states the six numbers identically. Docs-only
diff, as its AC requires.

**Pack-prose spot-check** (first task in the graph + tasks whose description carries a guarantee
word — P23-T1, P23-T8 "never", P23-T10 "never", P23-T12 "always"). No prose/AC contradiction and no
guarantee without an enforcing test in those four. P23-T6's prose "with none of it reachable from the
panel yet" *is* the stale phase-time guarantee behind ESC-116 and is covered there.

**Test re-baselines.** The twenty dock-lookup re-keys and the D18 suites are re-points (identity,
panel-fills, width) with no numeric tightening/loosening except the two owner-authorised A201
re-baselines; the `test_d65_option_panel.py` block T10 rewrote became a stricter absence test. No
case was weakened to make the build green.

---

## For the Orchestrator / owner

Open at handoff: **ESC-116** (TASK_MANAGER, blocking — the two red contracts), **ESC-117** (BUILD,
blocking — OFF→ON engine state), **ESC-118** (BUILD, should-fix — unused alias / gate allowlist).
The phase's other open gate is the **owner-run paper-TWS acceptance** (`AC-D65.19`, owned by
P23-T14): the checklist is created and every result pending — the phase cannot be called complete
until the owner runs it or records an explicit waiver. The repository documentation gate
(`docs/phase-changelog.md` has no D65/P23 entry yet; `plan.md`/`architecture.md` as-built sync) is
also owner-gated and outside this review.

Status: REVIEW_COMPLETE
