# Code Review — Phase P4 (Batch 20 / D45) — phase-final pass

- **Pass type:** phase-final (Orchestrator-launched, terminal `REVIEW_COMPLETE`)
- **Review tier:** **FULL** — mandatory at phase-final; also independently implied by scope (`P4-T01` and `P4-T06` are size **L**, and `ui/main_window.py` is shared by three tasks).
- **Scope (incremental: every P4 result is newer than the last marker; no prior `review_log_P4.md` existed):** `P4-T01`, `P4-T02`, `P4-T03`, `P4-T04`, `P4-T05`, `P4-T06` — all `done`.
- **Ground truth consumed, not re-derived:** `docs/code_review/precheck.json` (6 tasks scoped, **0 fail_fast**, **0 escalation_entries**, 3 doc candidates, 3 informational overlap flags, results coherent, `files_changed` == git reality, footprints verified) and `docs/code_review/test_verification.json` (**verdict `pass`**, exit 0, 81.12s, `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q --tb=no`). No task carried `"skeleton": true`.
- **Method:** diff-first over the cumulative batch diff (`git diff HEAD`, HEAD = `c702be9`) restricted to each task's verified `files_changed`; full read of the new `tests/test_d45_removal.py`; targeted greps over `ui/ services/ data/ ibkr/ config/ main.py`; a manifest-level read of the six P4 task definitions and their ACs; one behavioural offscreen reproduction (ESC-060). No code, test or config file was modified by me.
- **Escalations opened this run:** ESC-059 … ESC-063 (5). **Closed this run:** none (no open entry existed at run start).

---

## 1. Failure diagnosis (entry A)

None due. `docs/build/build_log.md` ends `Status: READY_FOR_REVIEW`; all six P4 tasks are `done` with per-task tests green, and the independent suite run agrees (`pass`, exit 0). `docs/build/failures.json` carries no P4 entry and `precheck.json` reports `fail_fast: []`. No `code_bug` / `bad_task_breakdown` / `bad_architecture_decision` / `requirements_gap` diagnosis was needed for a blocked task.

## 2. Findings

### ESC-059 — Wave-1 pack note contradicts its own task's ACs (route: `TASK_MANAGER`, `gap`, `should-fix`)

`docs/build/wave/P4-T01.md`'s inlined context note for `ui/main_window.py` lines 620–655 instructs "the five Portfolio `.connect` lines (:647–:651, **delete all five** — the panel still defines the signals until wave 3, so zero receivers is harmless)". `P4-T01` AC2 requires the window keep "the retained inbound observers", AC4 requires `tests/test_dock_d18_region.py` to pass with "its five-signal receiver loop left untouched (wave 2 owns that loop)", the plan excerpt inlined in the *same* pack file mentions only digest/news items, and `task-graph.json`'s `P4-T02` owns all five connections plus the five handlers ("This wave must NOT touch the panel"). Obeying the note would have deleted live wiring one wave early (the panel still defined the signals) and broken `test_T48_T03`'s five `receivers(...) >= 1` assertions. The worker correctly refused; the delivered tree is right (all five `.connect` lines survive through wave 1 and are gone only after wave 2, and the final tree has none). The wording ("the panel still defines the signals until wave 3") reads like a stale D44-era note re-derived by `build_wave.py`'s context inliner rather than a Task-Manager decision.

### ESC-060 — Retained SL/TP values are silently NULLed by the live upsert (route: `BUILD`, `bug`, `should-fix`)

**This is the one substantive finding of the phase.** `requirements.md:4224-4226` and `:1107` state that the retained stop/target columns "stay in SQLite" and are only "not settable and not displayed"; the docs `P4-T05` wrote say the same thing to the user (`USAGE.txt:88-89`, `usage.md:154`). They do not survive: `MainWindow._on_position_update` builds the `Position` with `stop_loss=None, take_profit=None` (`ui/main_window.py:3093-3094`) and `_upsert_position` writes both columns on the `ON CONFLICT ... DO UPDATE` branch (`:3198-3199`), so the next live update for a symbol/con_id that carries legacy values wipes them.

Reproduced offscreen over the real production chain (`DB_PATH=$(mktemp)`, `IBApiClient.connect` mocked, `_on_connected`, then `bridge.position_update.emit("DU123", contract, 10.0, 40.0)`):

```
seeded:            (id=1, qty=10.0, stop_loss=1.5, take_profit=3.5)
after live update: (id=1, qty=10.0, stop_loss=None, take_profit=None)
```

Honest provenance: the write-through **predates** D45 (identical construction and identical `DO UPDATE` at `c702be9`), so this is not a D45 regression. But D45 deleted the only setter, renamed the storage's justification into an explicit requirement, and shipped two user-facing documents promising preservation — so from this batch forward the loss is permanent and the shipped text is false. No test pins the invariant: `tests/test_d27_position_id.py::test_p2_t27_t11` checks one surviving row and a populated `id`, never the retained columns; the deleted `test_p2_t27_t31` was the only reader; `tests/test_stop_loss_target.py` (kept per A87) asserts the model fields only.

### ESC-061 — The plan's one permitted `ibkr/orders.py` edit was not made (route: `BUILD`, `consistency`, `should-fix`)

`S29` (`architecture.md:4656`, `:4810`, `:4858`) keeps `ibkr/orders.py` "with a module-docstring note", and risk row `AR-D45-10` (`:4944`) exists precisely because "`ibkr/orders.py` retained-but-unused invites a future reconnection". The docstring is byte-identical to `c702be9` — `"""Pure order builders and open-order tracking for Phase 5 Order Entry."""` — advertising a feature D41 deleted and saying nothing about unreachability; `git diff HEAD -- ibkr/orders.py` is empty. The rest of `S29` holds: the `orders` singleton is imported at `ui/main_window.py:36` and read only by the inert observers; no production code calls `register()` or any builder; the AST scan cannot catch this because the docstring contains no forbidden token.

### ESC-062 — Stale prose naming the deleted SL/TP dialog and the deleted order ticket (route: `BUILD`, `quality`, `nice-to-have`)

`ui/main_window.py:3101-3104` and `:3128-3130` both justify `pos.id` with "the SL/TP dialog persists via `WHERE id=?` / early-returns"; `ibkr/account.py:40-43` repeats it on the `Position.id` field; `ui/main_window.py:1545-1547` still says the order registry routing makes "the ticket reflect reality instead of reading 'Submitted' forever" (ticket deleted in D41). In `tests/test_dock_d18_region.py`, `test_T48_T03_panel_present_and_signals_wired` no longer asserts any wiring and its comment claims "MainWindow consumes their effect via other slots", which is false (`positions_changed` / `account_summary_changed` have **zero** receivers repo-wide — exactly what the test's own `_receiver_count(...) == 0` probe at `:176-178` proves); `_receiver_count`'s docstring still cites a `>= 1` caller that no longer exists. Behaviour is correct throughout; these four sites are the last places in the tree that describe a live protection dialog / order ticket, and they sit outside D45's residue token list, so no wave grep could flag them. Suggested edits must avoid re-introducing residue tokens (the `ui/`-only grep twin would fail).

### ESC-063 — `docs/codebase-map.md` D45 header under-counts the adjusted suites (route: `PLAN`, `consistency`, `nice-to-have`)

`docs/codebase-map.md:25-27` says "deletes five whole test files and **adjusts six**". `git diff --stat HEAD -- tests/` shows five deletions (correct) and **seven** modified files: `test_d27_flat_rows.py`, `test_d27_position_id.py`, `test_d27_position_prices.py`, `test_d28_pacing.py`, `test_d38_events_news.py`, `test_dock_d18_region.py`, `test_order_rejections.py`. The plan's own book says seven three times (`plan.md:1970` "5 deleted / 7 adjusted / 1 added", `:2214`, `:2342` AP-D45-13) and `plan.md:2387` records "map's book updated to 7 adjusted" — so the edit was intended and did not land. The header also omits the one added suite (`tests/test_d45_removal.py`). The rest of the header's arithmetic checks out (5 deleted production modules, 3 edited production modules); the map is Plan-owned, hence PLAN rather than BUILD.

---

## 3. Quality review of the whole batch (what I checked and cleared)

**Cross-wave coherence — "observes but cannot act".** Verified on the live tree, not from the results JSONs:
- zero occurrences of `placeOrder` / `cancelOrder` / `reqGlobalCancel` / `kill` / `news`+`digest` / `sltp` / `TradeContextMenu` / `StopLossTargetDialog` / `_s0_headless` / `news_push_listener` / `validate_order` over `ui/ services/ data/ ibkr/ config/` and `main.py` (`main.py` checked separately — the static guard does not scan it; it is clean);
- the five inbound observers (`_on_open_order`, `_on_order_status`, `_on_exec_details`, `_on_order_error`, `_update_order_status`) write only to `order_registry` and the status bar — read them line by line, no transmit/cancel/persist;
- `ibkr/client.py` and `ibkr/bridge.py` are **unmodified** (`git status --porcelain`), so the `tick_news` override and its signal remain inert as decided (S35/A90);
- `ui/ticker_session.py`'s two `want = ...` sites now read `self._s0_union_str() if self.view_count > 0 else ""`; tick 59 / `_dividend_info` / `dividend_updated` / `_merge_*` are byte-identical, and `tests/test_d45_removal.py::test_dividend_path_still_alive` drives the real `"456"` → tick-59 → overlay chain;
- positions table is 8 columns with headers `Symbol, Qty, Avg Price, Type, Multiplier, P/L, Strategy, Group`, right alignment `(1, 2, 4, 5)`, `Strategy`/`Group` at 6/7 (`ui/active_portfolio_panel.py:102-113`, `_render_table:266-287`), and the panel's `set_positions`/`add_position`/`refresh`/`_unrealized_pnl`/collapse API is untouched (AC4/A87 preserved);
- **toolbar separator sanity:** the kill-switch cluster's preceding `QLabel("|")` is gone and the surviving separators still bracket real clusters (`Symbol|TF|Load | Mode…` and `… | Draw:`), with `addStretch()` last and the two badges at the right (`ui/main_window.py:290-320`). No dangling separator, no orphan `addWidget` gap;
- **no leftover `objectName`/style/tooltip strings:** `KillSwitchButton`, `NewsDigest`, `TradeContextMenu`, `StopLossTargetDialog` appear nowhere in `ui/ config/theme.qss` outside the new guard's own token list;
- **no orphaned imports:** `pacing_manager`, `order_limiter`, `validate_order`, `UserOrder` left `ui/main_window.py` with the code that used them; every surviving import is still referenced (`deepcopy`, `QShortcut`, `id_manager`, `PacingExceeded`, `order_registry`, `S0_TICKS` all have live call sites).

**Test-adjustment audit (did the removals weaken anything beyond need?).** All seven adjusted files reviewed line by line against the ACs that authorised each edit:
- `test_d27_flat_rows.py` — only the AC-3 tail (`selectRow` / `_selected_position`) dropped, docstring restated; the index-alignment assertions `rowCount() == len(panel._positions)` and per-row symbol check remain. Corresponds exactly to `P4-T03` AC5. Not weakened.
- `test_d27_position_id.py` — AC-3 case `test_p2_t27_t31_sltp_persists_...` removed whole (its only passing path is the deleted window connection) and `item(0, 8/9)` → `item(0, 6/7)`; AC1/AC2 cases intact, `_seed_position` still used. Not weakened — **but** the removal is what leaves the retained-columns invariant unguarded (ESC-060).
- `test_d27_position_prices.py` — two index literals changed, nothing else. Not weakened.
- `test_d28_pacing.py` — `test_close_position_defers_when_limiter_empty` (order-path pacing/validation ordering) removed with the order path; `_capture_gui_sleeps` still used by two surviving tests; every historical-pacing case intact. Not weakened.
- `test_d38_events_news.py` — NewsManager section and the whole `AC-D38.2`/`AC-D38.3` digest section removed (their modules are deleted); tick-59, `AC-D38.1`/`.4`/`.5`, yfinance cache/TTL, no-mock-endpoint and md-line-guard cases kept, module + md-line docstrings corrected (they are string constants and the AST scan reads them). Not weakened; note the surviving `test_ac_d38_production_tree_has_no_mock_endpoint` was left untouched.
- `test_dock_d18_region.py` — `NewsDigest` filter dropped (only one right dock now), five-signal loop removed with the signals, `container is win.portfolio_panel` and the zero-receiver probe kept. Contents are right; the **name/comment** are now inaccurate (ESC-062).
- `test_order_rejections.py` — `test_close_blocked_while_disconnected` removed with the close path; `_on_order_error` / `classify_error` cases and the `pytest` import (still used by the parametrize) kept; module docstring moved to the D41/D45 truth. Not weakened.
- Deleted suites (`test_d28_6_close_contracts.py`, `test_d41_retained_order_path.py`, `test_order_validation.py`, `test_sltp_honesty.py`, `test_kill_switch.py`) each tested only removed behaviour — correct whole-file deletions, not "deleted to pass". `tests/test_d41_removal.py` and `tests/test_stop_loss_target.py` are unchanged as decided (`git status` clean for both).

**The new acceptance instrument** (`tests/test_d45_removal.py`, read in full): the three nets are genuinely independent (AST over five source dirs with a documented survivor allow-list; a `ui/`-only raw-text twin that also sees comments; and a behavioural walkthrough with a recording `sys.excepthook`, `placeOrder`/`cancelOrder`/`reqGlobalCancel` recorders, and a real `MainWindow`). The walkthrough drives chart load, timeframe/mode/ext-hours, watchlist add/remove/column popup, alarms, studies, drawings, pop-outs, Portfolio selection/`refresh`/collapse, an external position update, an external TWS-side close, `_on_order_error` and `closeEvent`, and asserts the Portfolio table still renders the position and reflects the TWS-side close — so it pins "observes" and "cannot act" in the same test. The worker's RED evidence on pristine `c702be9` (7 of 8 fail, with the 10-column table and the full offence list) matches the recorded failures and is not tautological; the one case that passes on both trees (`test_dividend_path_still_alive`) is a *retention* guard by design and the result JSON says so. Two scope limits are documented rather than hidden (comments invisible to AST; `tests/` covered by neither static instrument, hence the direct `hasattr` probes). I found no false-negative path in the token matcher (`<6`-char tokens match exactly or as delimited components; longer tokens match as substrings; allow-listed names win).

### 3.1 Mock-endpoint containment (B.6 — standing, blocking, not severity-downgradable)

Run over the reviewed production diff: `git diff HEAD -- ui services data ibkr config main.py | grep -iE "mock|fake|stub|simulat"` → **no hits**; and no production module imports a test fake (`grep "from tests|import tests"` over the same set → none). The only new fake/recorder code is inside `tests/test_d45_removal.py` (`_RecordingClient`, `_RecordingExcepthook`, `_install_transmit_recorders`), which is test-only and injects at the `IBApiClient` boundary — the sanctioned pattern. **No finding.**

### 3.2 Usage docs (doc candidates)

`precheck.json` listed 3 candidates: `USAGE.txt` (`touched: true`), `docs/` (a directory, `touched: false` — not a doc surface), `usage.md` (`touched: true`). The project's user-facing docs are exactly those two files (confirmed by their own per-batch section convention and by `docs/phase-changelog.md`), and D45 is user-visible, so a doc update was owed — `P4-T05` paid it. I read the full diff and checked the claims against the code rather than the task's word: the "places, cancels and closes nothing / do it in TWS" statements, the view-only Portfolio description, the Database note, the `Portfolio (view-only)` workflow section and the `Safety` bullet all match the shipped tree, and no removed capability is still advertised (`grep -iE "kill switch|ctrl\+shift\+n|news digest|close all positions|close group|stop-loss / take-profit"` → 0 hits in both files). **One documented claim is false**: "stop and target values saved by an earlier version … stay in the database" (ESC-060). No `doc_required_unmet` flags were present in `precheck.json`.

---

## 4. Escalation close-out (entry C)

At run start `escalations.json` held **29 entries (ESC-030 … ESC-058), all `"status": "addressed"`**, and `precheck.json` reported `escalation_entries: []` with `escalation_updates: []` — i.e. nothing open, and no previously-closed entry whose linked artifact changed this phase. I re-read the tail of the file (ESC-055 … ESC-058, the D44 batch) to confirm the closed set includes the D44 usage-doc drift entry (ESC-058) whose successor class reappeared here and is now covered by ESC-063/ESC-060. **No entry required flipping this pass, and none was re-opened.** Two previously-closed D45-adjacent decisions were re-checked against the live tree because this batch is the one that could invalidate them: ESC-035/ESC-039/ESC-040 (D41 depth/footprint removals) remain moot — `on_depth_error`, `MarketDepthManager`, `FootprintService`, `mark_no_tick_data` still have zero occurrences; ESC-043/ESC-052/ESC-054 (account-scoping, prune-on-complete, pre-completion persistence) remain in force — `_live_accounts` / `_account_summary_complete` / `_prune_foreign_positions` are unchanged by D45 and `tests/test_d27_account_scoping.py` + `tests/test_d27_account_partial_window.py` are green in the verified suite run.

---

## 5. Deliberate decisions checked, not reported

| Decision | Verification performed |
|---|---|
| `ibkr/client.py` untouched; `reqGlobalCancel`/`cancelOrder` are ibapi's own | `git status` clean for the file; the AST scan is scoped to repo definitions/call sites and `IBApiClient.__dict__` is asserted free of all three names |
| `tick_news` survives in `ibkr/client.py:326` / `ibkr/bridge.py:28` | Both files unmodified; signal has no receiver (`b.tick_news.connect` removed); the `EWrapper` override must stay |
| `ibkr/orders.py` retained, not orphaned | `ui/main_window.py:36` imports it; consumers are the four inert observers only; no `register()`/builder call in production. (Its **docstring note** is a separate, plan-mandated item — ESC-061.) |
| `tests/test_d41_removal.py`, `tests/test_stop_loss_target.py` unchanged | `git status` clean; `test_stop_loss_target` green in the suite run |
| `positions`/`trade_groups` `stop_loss`/`take_profit` columns + model fields kept (A87) | Schema and `data/models.py` unchanged; no migration in the diff. (Their **preservation behaviour** is ESC-060.) |
| No replacement order/cancel/protection UI | No new widget/action/dialog anywhere in the diff; the toolbar ends with `addStretch()` + two badges; `tests/test_d45_removal.py` asserts the panel members and signals are absent |

**Considered and deliberately NOT escalated** (each is explicitly decided upstream, so a BUILD patch would contradict the plan):
- `ibkr/orders.py`'s builders, `ibkr/pacing.py::OrderRateLimiter`/`order_limiter`, `config/settings.py::MAX_ORDER_NOTIONAL` and the duplicate unused `data.models.UserOrder` are now production-unreachable — kept on purpose by `S29` ("the builders keep unit coverage"), `T06` AC2's survivor allow-list (`order_limiter`, `pacing_manager`, `PacingExceeded`, `MAX_ORDER_NOTIONAL`, `UserOrder`) and `tests/test_ui_smoke.py:48`. None of them can transmit; only the missing docstring note (ESC-061) is a genuine gap.
- `positions_changed` / `account_summary_changed` have no receivers — pre-existing at `c702be9` (`git grep ... HEAD`), untouched by D45, and now explicitly probed as zero-receiver by `test_T48_T03`. Only the misleading prose about them is flagged (ESC-062).
- `_upsert_position` writes `stop_loss`/`take_profit` from the live object — the *wrong-value* aspect is ESC-060; the "position upsert is retained" part is A87 and correct.

---

## 6. Verdict

| Task | Result | Review verdict |
|---|---|---|
| `P4-T01` | done, 7/7 | **Accepted** — news digest / `View` menubar / `"292"` / headless S0 / push-listener API all gone; dividend substrate byte-identical. Pack defect routed (ESC-059). |
| `P4-T02` | done, 6/6 | **Accepted** — window order path severed, `ibkr/validation.py` + three suites deleted, observers retained. S29 note missing (ESC-061); retained-SL/TP behaviour flagged (ESC-060). |
| `P4-T03` | done, 6/6 | **Accepted** — menu/signals/setter chain/selection tracker gone, 8-column view model exactly as specified, storage untouched. |
| `P4-T04` | done, 4/4 | **Accepted** — kill switch + its separator + `_kill_switch` gone; zero `reqGlobalCancel`/`cancelOrder` anywhere; toolbar still coherent. |
| `P4-T05` | done, 4/4 | **Accepted** — both user docs rewritten to the view-only truth and verified claim-by-claim, except the one false preservation promise routed as ESC-060. |
| `P4-T06` | done, 10/10 | **Accepted** — the acceptance instrument is independent, discriminating (RED on `c702be9`), and covers the AC-D45.3 measurables directly. |

**Phase-level judgement:** the D45 end state is coherent — the app observes, renders and never acts. No blocking finding, no test weakened to obtain green, no mock endpoint in production, no footprint violation, suite independently green. Five findings are routed: one build-quality gap in a docstring the plan explicitly mandated (ESC-061), one genuine requirements-vs-code contradiction about the retained columns (ESC-060, `should-fix`), one stale-prose cluster (ESC-062), one pack-generator defect (ESC-059), and one Plan-owned documentation count (ESC-063).

Status: REVIEW_COMPLETE
