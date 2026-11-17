# Plan Review — Phase P23 (Option Spreads panel in the right dock, D65)

**Status: APPROVED**

**Pass type:** `retry_1_of_3` under the owner's decision on **RC-16 = MERGE** (Plan's pass-8 revision
notes, `docs/plan.md:5524-5595`). Scope run: the RC-16 landing check first (the four questions the
Orchestrator named), then the full Validation Method — coverage, completeness, consistency, plan
quality, readiness, existing-repo compliance, frozen interfaces, map quality, doc sync — because the
merge moved ten production deletions and two exit conditions, and this is the last gate before Task
Manager (no second implementation-plan review; owner-waived).

**Lint backstop:** the preamble carried no `plan_lint.py` result, so it was re-run here —
`plan_lint.py --phase P23` → `LINT PASS: P23 (canonical sections); 0 failure(s), 0 warning(s)`.

**Phase gate:** open — `docs/code_review/review_log_P22.md` ends `Status: REVIEW_COMPLETE` after
`docs/build/build_log.md`'s last terminal build status; no `PROVISIONAL` review is outstanding, so
this pass finalises. `docs/plan.md` § P23 ends `Status: READY_FOR_VALIDATION`; the P23 architecture
section carries the pass-8 revision note.

**Stamps (unavailable — tooling, not Plan):** `pipeline_state.py hash-section --file docs/plan.md
--phase P23` and the `architecture.md` twin still return `ERROR: no '## Phase P23' section`
(`PHASE_HDR_RE` does not match this repo's `## Phase P23 — …` headings; unchanged across four
passes, an Orchestrator-script observation, not routed). Freshness falls back to mtime and points
the right way: **`requirements.md` 16:03:34 → `architecture.md` 16:55:07 / `plan.md` 16:56:07** —
both canonical sections are newer than the requirements text they implement, and requirements.md has
not moved since the retry-3 review (no drift).

---

## RC-16 landing check (owner-decided MERGE)

| # | What the decision required | Verdict | Evidence verified this pass |
|---|---|---|---|
| (a) | All **ten** call sites are **P23-01's**, each with a **per-site disposition** | **YES** | Per-site table at `plan.md:5538-5546` (revision note) and again in the wave's deliverable (`:5710-5718`), ten statements at the ten named lines. Tree-verified: `grep -n "portfolio_panel" ui/main_window.py` returns **18** occurrences — the import `:76`, the dock block `:638,641,642,662`, the three probes `:3591,3606,3638`, and exactly ten API calls at `:849,850,852,1731,2072,4349,4350,4357,4468,4538`. The five methods are spelled nowhere else in the window (`set_account_summary` ×3, `set_account_unavailable` ×3, `set_positions` ×2, `set_account_id` ×1, `add_position` ×1 = the same ten). Each disposition is *delete, not re-point*, with the surviving owner named: nothing at `__init__`; the subscription body at `:1731` → P23-06; the state clears at `:2066-2071` → P23-06; each handler's own body → P23-06; the stranded `positions` local → P23-06. |
| (b) | **P23-06 no longer claims them**, and its exit is **true when it fires** | **YES** | P23-06's goal/deliverable now open with "the panel that consumed it is already gone (P23-01, which also removed every panel call the window made)" and say so explicitly (`plan.md:6238-6254`); its audit row records the narrowing (`:6622`). Exit re-grepped token by token against the tree: `reqPositions`/`reqAccountSummary` survive only at `main_window` `:1716-1729` + the `:890-913` comment block (both this wave's) and in `test_d45_removal._stub_account_calls` (`:494,496`, removed here) and the four D27 suites (deleted in P23-01); `_account_id` only at `:1653,4336` (this wave's badge edit + handler); `_live_accounts`/`_positions_rendered` only in `main_window`; `_symbol_last_prices` at `:893,3385,4460`; `_record_symbol_price`'s five test stubs are the exact five named in RC-13; `set_price_sink`/`_price_sink` have no test carrier. The bridge/client `account_summary`/`position_update` and `data/db.py:189` are excluded **by name** and owned by P23-07/-08. No row reads a panel symbol. |
| (c) | The window stays **constructible between the two waves**, and the named proof suites really execute `:1731` and `:2072` | **YES** | `_subscribe_account_data` (`:1701-1731`) has no early return, so its tail runs on every connect; `_on_disconnected` (`:2063-2072`) has no return before the panel line. `tests/test_d27_reconnect.py:170-172` is the hide-loop row this wave re-points, and its body `:183-215` calls `win._on_connected()` → `_subscribe_account_data` → `win._on_disconnected()` → `win._on_connected()` on a real `MainWindow` — both lines executed. `tests/test_d41_removal.py:356` and `tests/test_d40_tws_lifecycle.py:437` confirmed as the two further connect/disconnect walks; `tests/test_d45_removal.py:556` confirms `walkthrough` calls `_on_connected()`. **Ran it:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_d27_reconnect.py -q` → **7 passed** on today's tree, so the harness that proves the wave's connect/drop path is live, not hypothetical. After P23-01 the only change on that path is the deleted tail line, so the same suites construct and walk the window. The four handlers' call sites are driven by no surviving test — all `account_summary`/`position_update`/`position_end` emitters in `tests/` are inside the four D27 suites this wave deletes plus `test_d45_removal.py:605,617`, whose emits this wave removes. |
| (d) | **No handler deleted that still has behaviour to remove later** | **YES** | P23-01 deletes *calls only*; all four handlers survive with their account-path bodies intact, verified in the tree: `_on_account_summary` keeps `_account_id`/`_live_accounts`/summary collection/`_update_conn_badge`; `_on_account_summary_end` keeps the status line and the ESC-052 prune guard; `_on_position_update` keeps the build + `_upsert_position`; `_on_position_end` keeps the bulk read and `_positions_rendered`. The one deliberate intermediate — `_on_position_end`'s `positions` local left with no reader — is recorded (`plan.md:5555-5560`, `:5721-5724`) and assigned to P23-06 with the read it dies with (`:6251`); it is a local name, not a forbidden token, no exit reads it, and the repo has no F841-class lint gate (no ruff/flake8 config in the tree — `pytest.ini` only), so it cannot redden a wave. |

Nothing else moved: the forbidden-token sweep's `portfolio_panel` row is now **P23-01-only** with
every carrier line named (`:5488`), both exit-audit rows record the merge (`:6617`, `:6622`), the
serialisation note states P23-01 leaves no dereference behind and P23-06 introduces none
(`:6571-6579`), and the deletion inventory's panel row carries the ten sites with the reason they are
deletions (`:6642`). Architecture side: `S-P23-1`, `S-P23-12` wave (0), the `[revises D41]` bullet,
the `ui/main_window.py` component entry and the Codebase Summary all name the ten sites, and the
failure mode is **AR-P23-24**.

**Coverage closed, not just claimed.** Every `"Portfolio"` string literal in `tests/` today sits in a
file the plan schedules: the 8 book files, the 20 lookup modules, and the 6 D27 suites
(deleted) + `test_d41_portfolio_dock.py` (deleted) — enumerated one by one against
`grep -rn '"Portfolio"' tests/ --include='*.py'`, no orphan. Likewise `grep "Account Summary" ui/`
returns exactly `ui/main_window.py:3586` (the RC-15 docstring) and the panel module (deleted), and
`grep "ActivePortfolioPanel"` outside `tests/` returns only `main_window:76,638`, the class itself and
`ibkr/account.py:39`'s comment (P23-07).

## Validation Summary

The merge landed and it is mechanically sound, which is the point the last three reviews kept failing
on: a rename is a definition, so every surviving dereference of it had to die in the same wave — and
now it does, at ten sites, each with a named surviving owner. The reasoning in the revision note is
the right one and is stated where a worker will read it (the new panel has none of the five methods,
so "renaming" those lines would raise on the *new* panel instead), and the window-constructibility
claim is backed by suites that actually walk connect→drop→reconnect rather than by prose. The
badge decision from retry 3 is intact and still coherent with `AC-D26.5`. Everything else in the
phase is unchanged from the retry-3 pass, where it was verified sound.

## Requirements Coverage

All nineteen criteria and both journeys remain represented; the merge changed one wave mapping and
nothing else. Re-read the changed row and spot-checked the rest against the waves.

| Criterion | Waves | Verdict |
|---|---|---|
| `AC-D65.1` shell/columns/toggle/no-Portfolio dock | P23-01, P23-05, P23-09 | COVERED |
| `AC-D65.2` geometry/naming/fixtures | P23-01, P23-02 | COVERED |
| `AC-D65.3` anchor on credit bases + three tie-breaks | P23-03 | COVERED |
| `AC-D65.4` one step / stop rules / tick band | P23-01, P23-03, P23-04 | COVERED |
| `AC-D65.5` displayed formulas + greek precedence | P23-01, -02, -04, -05 | COVERED |
| `AC-D65.6` ≤16 option lines, shared legs, guard | P23-03, -04, -05 | COVERED |
| `AC-D65.7` maintenance, zero orders | P23-05, P23-09 | COVERED |
| `AC-D65.8` degraded/empty/cutoff | P23-02, -03, -04, -05 | COVERED |
| `AC-D65.9` 360 px launch, elide+tooltip, two re-baselines | P23-01, P23-09 | COVERED — both re-baseline sites verified in the tree (`test_dock_widths_d18.py:437-438`, `test_dock_widths_d18_impl.py:328-329`) |
| `AC-D65.10` coalesced repaint | P23-05 | COVERED |
| `AC-D65.11` history intact + the three recorded edits + S-P23-24's consequence | P23-09 | COVERED |
| `AC-D65.12` residue gate, seeded-red | P23-08, P23-09 | COVERED |
| `AC-D65.13` displaced stack absent; **panel + its ten call sites** in P23-01, residue in P23-06 | P23-01, -06, -07, -08; gate P23-09 | COVERED — the traceability row now names the ten call sites (`plan.md:5613`) |
| `AC-D65.14` lifecycle, replay, four error classes | P23-04, P23-05 | COVERED |
| `AC-D65.15` seed ladder, spot 3a/3b/3c, 3 s, 10 s/12-pair | P23-03, P23-05 | COVERED |
| `AC-D65.16` quote validity/sentinels | P23-01, P23-03 | COVERED |
| `AC-D65.17` Target `0.05…19.95` | P23-01, P23-05 | COVERED |
| `AC-D65.18` verified backup + full file set | P23-06, P23-08 | COVERED |
| `AC-D65.19` owner-run paper-TWS gate | P23-10; P23-09 records it open | COVERED |
| Journeys 62, 63 | 62 → P23-01/03/05; 63 → P23-02/04/05 | COVERED |

## Architecture Findings

**Completeness — passes.** Tech stack (four `Constrained:` rows first), labelled components, data
model, integration points, frozen interfaces, non-functional approach, 24 architecture risks
(`AR-P23-24` added for the merge), 24 decision rows each with rationale and rejected alternatives,
every one relationship-labelled. The pass-8 revision note (`architecture.md:9002-9012`) states the
merge's design consequence and its failure mode.

**Consistency — passes.** The merge reads identically in six places: `S-P23-1`, `S-P23-12` wave (0),
the `[revises D41]` bullet (`:9029-9032`), the `ui/main_window.py` component entry
(`:9504-9519`), `AR-P23-24`, and the plan's own tables. `S-P23-12`'s rejected-alternatives list now
carries both escape hatches by name (leave the name until P23-06; re-point the calls). The badge
decision (`S-P23-24`) is unchanged and its `[revises D26]` label is present. No new contradiction
between the architectures's account-path inventory and the plan's wave split.

## Plan Findings

Ten milestone-level waves, S/M, dependencies declared, no task-level decomposition, no dependency
graph, no per-task test specs. The exit-condition audit's P23-01 row now checks what a wave *breaks*
as well as what it reads (`plan.md:6617`); the P23-06 row is narrowed to the residue and says so. The
serialisation note is exact about the three `ui/main_window.py` waves and which blocks each owns.
P23-10 remains correctly shaped (docs-only, owner-run, exit = the record or a recorded waiver; P23-09
forbidden from claiming it).

## Existing Repo Compliance

| Check (step 7) | Verdict |
|---|---|
| Codebase Summary present and substantive | **PASS** — `architecture.md:9072-9360`, updated for the merge; key anchors re-verified this pass (`main_window:76,638,849-852,1731,2072,4349-4358,4468,4538`) |
| Existing stack respected; nothing replaced unforced; current stack first | **PASS** — four `Constrained:` rows open the table; only Q110(a)/A200-authorised replacements |
| `[existing]`/`[new]`/`[new/changed]` labels present | **PASS** |
| Additive-only; nothing redesigned beyond the requirement | **PASS** — `ui/dock_layout.py`, `ui/visual_conventions.py`, `subscription_manager` (one constant), `MarketDataManager` (one method) explicitly untouched |
| Codebase Summary consistent with the proposal's `[existing]` claims | **PASS** |
| Current Tech Stack present in `requirements.md` | **PASS** — no requirements escalation |

## Frozen Interfaces

| Check (step 8) | Verdict |
|---|---|
| Verbatim contracts, not prose | **PASS** — grep-verified this pass against the tree: `req_mkt_data` (`market_data.py:93`), `cancel_mkt_data` (`:112`), `assess` (`md_line_guard.py:20`; caps `:16-17`), `right_dock_max_width` (`dock_layout.py:56`), `plan_dock_widths` (`:92`), constants `:21,34,40`, `subscribe`/`unsubscribe`/`replay_all` (`subscription_manager.py:54,68,94`; tags `:35-37`), `get_bars` (`ticker_session.py:428`), `ContractLookupService.request` (`:101`), `get_index_contract`/`get_contract_for_symbol` (`contracts.py:166,262`), `throttle` (`pacing.py:68`), `classify_error` (`error_codes.py:10`), `get_user_data_path`/`get_db_path` (`paths.py:90,102`), `DiagonalStrikeButton`/`set_button_active` (`visual_conventions.py:109,80`) |
| Nothing under construction is frozen | **PASS** — every entry `[existing]`/unmodified; the panel, the renamed attribute, the ladder/engine, `db_backup`, the tag and the badge are all in the **NOT frozen** list (`:9719-9731`) |
| Nothing frozen is missing | **PASS** — the badge and its two fields are correctly *not* frozen (deleted); `get_bars` present with its "not read by the panel" note |
| Owning module resolves | **PASS** |
| No duplicates | **PASS** |

## Codebase Map

| Check (step 9) | Verdict |
|---|---|
| Every module section resolves | **PASS** — P23 note (`:156-183`), 20 lookup harnesses (`:500`), the six deleted suites (`:498`), three new modules named without backticks (`:162-167`) |
| Key files exist | **PASS** — `ui/active_portfolio_panel.py`, `ibkr/subscription_manager.py`, `data/models.py`, `services/strategy_detection.py` |
| No stale entries for deleted modules | **PASS** — `:231` carries `[deleted in P23]`; `:491` lists the deletions |
| Status labels current | **PASS** — `[deleted in P23]`, `[new in P23]` (`data/db_backup.py`), `[changed in P23]` on the edited modules |
| Index-sized | **PASS** |

## Pending Doc Sync

`docs/pending_doc_sync.md` is **absent** — nothing unapplied between phases.

## Required Changes

None.

## Requirements Escalations

None. No new question is raised; `AC-D65.13`/A194/R143 already license the deletion, and the badge
retirement is a recorded consequence, not a requirements edit.

## Findings owned outside Plan

None. Two observations, neither routed and neither a defect:

- `docs/implementation_plan_P23.md`'s **SUPERSEDED banner is honest, not a fig leaf.** It states that
  the owner's 2026-11-17 review folded into `AC-D65.14`–`AC-D65.19` and then into the 10-wave
  revision including RC-16's merge, that `docs/plan.md`/`docs/architecture.md` are authoritative, and
  that the file is the record of what was reviewed. Its content matches that description: it *is* the
  8-wave document the owner reviewed (its own line 12 says "8 waves"), and the one way a reader
  could be misdirected — following its now-stale wave numbers (its P23-04 is today's P23-05, etc.) or
  its flat-0.05 band — is warned against in bold before the first sentence of content, and the banner
  is the first thing in the file. No reader who reads the top of the file can follow it as guidance.
  Kept as-is; the file is the Orchestrator's, and nothing in it contradicts the approved plan
  silently.
- `architecture.md`'s `S-P23-15` parenthetical token list is a **shorter subset** of `plan.md`'s
  P23-08 `_FORBIDDEN` additions (it omits `_parse_contract_type`, `OptionLeg`, `Account Summary`,
  `_account_id`, `_price_sink`). The operative list is the plan's, which is complete and matches the
  sweep table; the decision row is a summary, not the schedule, and no wave reads the architecture for
  its token set. Cosmetic, not a blocker — recording it so a later reader does not mistake it for a
  contradiction.

## Task Manager Readiness

**Ready.** The gate is *"can Task Manager create a valid task graph without making a new architectural
decision?"* — yes. Every wave names its files, its tests, its decisions and its exit; the ten call-site
deletions are site-by-site with the surviving owner named, so no task has to choose between deleting
another wave's subject, keeping an alias that resurrects a displaced token, or leaving a broken
constructor. The token→carrier→wave sweep, the exit-condition audit, the serialisation note, the
deletion inventory by member group and the frozen interfaces are all sufficient to decompose from.

## Final Decision

**Status: APPROVED.** No PLAN-owned, REQUIREMENTS, BUILD or TASK_MANAGER items are open. Activation
performed: `docs/plan.md` § *Phase P23* now ends `Status: READY_FOR_TASK_MANAGER`; the architecture
section needed no editorial change (its cumulative entries are already under § Phase P23 with their
relationship labels). No `plan_notes.md` entry is added — the phase's only note
(`RG-P23-1`) is already `addressed`.
