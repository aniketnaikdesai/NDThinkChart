# Code Review — Phase P16 (Batch 30, D55 docs consolidation), first pass 2026-11-04

## Pass header

- **Tier: FULL pass (forced, not dodged).** The Orchestrator's independent `test_verification.json` verdict is **FAIL** (exit 1, 3 failures), one task is `blocked` (P16-T4, fail_fast malformed result), and `precheck.json` reports shared-file overlaps (`docs/codebase-map.md` by T3+T5; `docs/architecture.md` + `docs/plan.md` by T6+T7). Light-pass conditions fail on every count. This is not the phase-final pass (P16-T8/T9 `not_started`, gated on T4) — no `CHECKPOINT_COMPLETE` was requested, so this log carries the standard marker.
- **Scope (incremental):** P16-T1 … P16-T7 — the exact precheck scope. No `review_log_P16.md` existed, so this first P16 pass reviews all seven. Ground truth consumed, not re-derived: `precheck.json` (fail_fast: P16-T4 only; footprints verified; doc candidates `USAGE.txt`/`docs/`/`usage.md`), `test_verification.json` (FAIL exit 1, 75.81 s), `build_log.md`, `failures.json`, per-task results JSON.
- **Scope guard honored:** D55 docs-only; D1–P15 NOT reopened; one plan.md / one architecture.md (no legacy-proposal edits by any task — verified, none touched); `docs/requirements/` untouched by every P16 build task.

## A. Failure diagnosis

### P16-T4 (blocked) — implementation sound, two mechanical defects, both routed without re-diagnosis cost
- **Substance verified done on the live tree (not the worker's word).** `grep -c 'paper (DU)' usage.md USAGE.txt` → 0/0 hits in both files (the :106-107/:257 and :39-40 paper-on-7496 sentences are gone); `live` present 10×, `7496` present in both files, install/port/account claims agree (one full guide + one pointer); zero parity-complete language in either file. T41/T42 pass on substance.
- **Defect 1 (TM-owned, one-word fix) → ESC-097 (TASK_MANAGER, blocking).** The prescribed `test_command` (`test ! grep -q 'paper (DU)' …`) is invalid shell — `test` takes expressions, not a pipeline — so selfcheck exits 2 deterministically and no rework round can ever go green. Corrected form (leading `test ` dropped) verified on the live tree to print `T4_OK`. T8/T9 gate on T4, hence blocking.
- **Defect 2 (persistently malformed result) → PRE-015 stays open (BUILD).** Newest result `_archive/wave252_P16-T4.json` carries `task_id` only inside `selfcheck`, with no top-level `task_id` — still malformed after 2 rework rounds, confirmed by direct JSON read (the sole `MISSING` newest-per-task entry, which is exactly what `test_archived_results_carry_task_id` fails on). Per the rework guard the fix rides the ESC-097 re-run (fresh result), not another blind re-dispatch; PRE-015 flips only when the new result verifies.
- Classification: `bad_task_breakdown` (command string) + worker result-shape defect (covered by open PRE-015). Not a code bug, not architecture, not requirements.

### Full-suite VERIFY FAIL (3 failures) — attribution
- `test_archived_results_carry_task_id` → the PRE-015 condition above (newest P16-T4 result missing top-level `task_id`). No new escalation (PRE-015 already routes it).
- `test_t34_history_markers_intact` + `test_t33_history_markers_intact` → **not caused by any P16 build task.** Both fail on the `PRE_D53_SHA256` head hash because the Analyst-owned P16 requirements edit inserted the Batch-30 D55 banner at the top of `requirements.md` (plus appended A149–A155 / R110–R113 rows and the Phase P16 section — all additions; the D41–D52 region itself is byte-intact). Both guards hash the whole head before `\n### D53 `, so any legitimate pre-D53 insertion reddens them. Same invariant, one escalation → **ESC-098 (TASK_MANAGER, blocking)**: re-pin or (preferably) narrow the hashed region; never weaken the D41–D52/marker/stack/reversal assertions. No P16 task may claim those test files (all outside every footprint).

## B. Quality review (done tasks T1/T2/T3/T5/T6/T7 — diff-first, all verified on the live tree)

- **P16-T1 (inventory) — clean.** `docs/D55_inventory.md` exists (new, untracked — consistent with precedent, e.g. T26); cross-reference + generated-bucket greps pass. `files_changed` matches. No finding.
- **P16-T2 (fact sheet) — clean.** All four T21/T22 grep predicates pass on the live file (`create_chart_view`, 5× `waived, not satisfied`, live-only, 5× explicitly-open); the 50-vs-100 row is explicitly open with decider named (W1 records openness; reconciliation is W3 work per the sheet itself). No finding.
- **P16-T3 (README + map index) — clean with one judged clarification.** Touched only `codebase-map.md` (README blocks pre-landed via changesets 1–2, greps pass). The map carries the P16 note + LWC-only live header; the single in-place line edit (adding `(live-session sign-off waived, not satisfied)` inside the 2026-10-28 as-built note) is a live-note clarification mandated by A152, not a rewrite of historical prose — judged compliant with AC2's append-only rule. No finding.
- **P16-T4 — see section A (substance clean, mechanically blocked).**
- **P16-T5 (P6 reconciliation) — clean.** `P6-T13` greps hit in all six files (6/6/3/3/4/1); `waived, not satisfied` in `architecture.md`; parity matrix structurally separates parity from cutover (§ "parity vs deletion, separated", row 19 Retired); `review_log_P6.md` carries its dated 2026-10-28 addendum with original text intact. Editing 2 of 6 files is accepted — the other four already carried the required content. No P16-specific second addendum is owed (a restating addendum would create exactly the R112 third-narrative layer). No finding.
- **P16-T6 (P7 cap addendum) — clean.** `maximum` + `DG102` present in all four files; per-load definition, three examples, delta note, AC-D16.8 by reference only; diff is additions-only (approval record byte-identical). The 50-vs-100 reconciliation to 100 cites `config/settings.py:36` (`MAX_HISTORICAL_PER_600S = 100`, confirmed) plus P7 wave assertions, names both figures — the legitimate "reconciled with cited evidence" branch of AC2, consistent with T2's W1-openness (designed W1→W3 flow, not a contradiction). No finding.
- **P16-T7 (navigation blocks + link audit) — clean.** Baseline blocks + link-audit pass present atop both canonical files; P16 increments carry uniform Status/Commit/Evidence/Supersession metadata; `docs/requirements/` untouched by this task (the `T7_FAIL_REQS_TOUCHED` selfcheck tail reflects the tree-wide Analyst banner, pre-existing to the worker — the command exits 0 and the tail is informational, not a task defect). Zero moves executed (correct — moves run under T8). No finding.
- **Cross-task overlap check:** T3+T5 both touched `codebase-map.md`, T6+T7 both touched `architecture.md`/`plan.md` — serialized by wave order (W1→W3), and the live files carry all parties' content (P16 note + T13 clarification; D55.6 addendum + Phase P16 section + baseline block). No clobbering.
- **B.6 mock-endpoint scan (blocking invariant):** grepped the entire reviewed diff for `mock|fake|stub|simulat` — two hits, both false positives (`stub-labelled` spike prose per A155, no endpoint/client/service/server/api/harness pairing). No production module changed except one comment-only docstring line; no test fake imported anywhere. **Clean.**
- **Usage-doc coverage:** the changed surface is documentation itself; T4's guide correction IS the user-facing update (verified live-only agreement above). Precheck doc candidates `USAGE.txt`/`usage.md` show `touched: false` only because T4's result is malformed/unverified — the working-tree edits exist and are correct. No additional doc update owed; stated explicitly per the docs gate.
- **Result credibility (honesty-hole check):** my independent greps reproduce every done task's claimed predicates (T1_OK/T2_OK/T3_OK/T5_OK/T6_OK equivalents all re-derived live), and the full-suite FAIL is honestly explained by the two routed causes above — no worker hid a red suite. The one credibility wrinkle (T7's pass-verdict selfcheck with a `T7_FAIL…` tail) is the command's own tree-wide design, disclosed by the worker, not a concealed failure.
- **Repeat-invariant rule:** no prior escalation covers the requirements-banner-vs-hash-guard invariant (checked ESC-066/069 — different class) or the invalid-`test `-prefix command — both are first-instance findings, so BUILD/TASK_MANAGER routing stands (no third-patch accumulation).
- **Out-of-scope notes (no action):** `services/sound_service.py` Q84 docstring change and the `dev_docs/` deletion are pre-landed items outside every P16 task footprint (precheck `unattributed_working_tree_changes`); the docstring is verified self-contained, comment-only. `docs/requirements/*` modifications are Analyst-owned P16 requirements work. Neither is reopened here.

## C. Escalation close-out

- **PRE-013 → addressed (verified).** Newest P16-T1 result carries top-level `task_id`, `done`, clean footprint, selfcheck exit 0; file substance re-verified live. Condition resolved.
- **PRE-014 → addressed (verified).** Newest P16-T3 result carries top-level `task_id`, `done`, clean footprint; map/README substance re-verified live. Condition resolved.
- **PRE-015 → stays open.** Re-verified the fix did NOT hold: newest P16-T4 result still lacks top-level `task_id` (only `selfcheck.task_id`). Cures with the ESC-097 re-run; flipping only then.
- No other open entries existed at pass start (ESC-001…ESC-096 and PRE-011/012 all `addressed`).

## Findings summary

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| ESC-097 | P16-T4 | TASK_MANAGER | bug / blocking | `test_command` has invalid leading `test ` — one-word fix, gates T4→T8→T9 |
| ESC-098 | — (guards) | TASK_MANAGER | consistency / blocking | Analyst's legitimate requirements banner invalidates the over-broad P14/P15 history-hash guards — re-pin/narrow, never weaken |

## Pipeline state for the Orchestrator

P16-W1…W3 substance is **sound**: six done tasks meet their ACs against requirements and architecture with genuine checks, and T4's guide correction is complete on substance. What stands between the batch and green is entirely mechanical: (1) the one-word `test_command` fix (ESC-097) plus the T4 re-run it unlocks (which also cures PRE-015); (2) the history-guard update for the legitimate requirements banner (ESC-098). **3 open escalations remain (PRE-015, ESC-097, ESC-098)** — all verified live, none re-diagnosable by the owners. T8/T9 stay correctly gated until T4 lands.

Status: REVIEW_COMPLETE

---

# Code Review — Phase P16, second pass (rework verification) 2026-11-04

## Pass header

- **Tier: FULL pass (forced).** The Orchestrator's independent `test_verification.json` verdict is **FAIL** (exit 1) with exactly **one** failure, and `precheck.json` carries a fail_fast flag (P16-T4 malformed result). Light-pass conditions fail. This pass reviews only the incremental scope below; D55 docs-only, D1–P15 NOT reopened, single-doc directive honored.
- **Scope (incremental):** P16-T4, P16-T8, P16-T9 — the exact precheck scope (results newer than the first pass's `REVIEW_COMPLETE`). T1/T2/T3/T5/T6/T7 unchanged since review — not re-opened. Ground truth consumed: `precheck.json` (0 new entries; T4 flag persists as PRE-015 open), `test_verification.json` (FAIL exit 1, single failure `test_archived_results_carry_task_id` on `wave256_P16-T4.json`), `build_log.md`, archived results, `task-graph.json`.
- **Result:** 3 escalations verified and flipped to `addressed` (ESC-097, ESC-098, PRE-016); 1 stays open (PRE-015). No new findings.

## A. Failure diagnosis

### P16-T4 — substance done, command fixed, result still malformed
- **Fixed command verified live (not the worker's word).** `docs/build/wave/P16-T4.md:104` carries the corrected command (leading `test ` dropped); the wave256 selfcheck ran it with exit 0 / `T4_OK`. I re-ran it independently on the live tree: prints `T4_OK`, exit 0. T41/T42 substance (live-only guides, zero parity-complete claims) stands from the prior pass.
- **But the fresh result is malformed a third time:** `wave256_P16-T4.json` carries `task_id` only inside `selfcheck`, with no top-level `task_id` (confirmed by direct JSON read; it is the sole `missing` newest-per-task entry, exactly what `test_archived_results_carry_task_id` fails on). The ESC-097 re-run therefore did NOT cure PRE-015. Classification unchanged: worker result-shape defect, already routed via PRE-015 (BUILD, blocking). No duplicate escalation opened (repeat-invariant rule — one invariant, one escalation); the repeat is recorded here so the owner knows a blind fourth re-dispatch is unlikely to converge — the T4 worker path drops the top-level key while T8/T9 workers (wave257/wave260) write it correctly.

### Full-suite VERIFY FAIL (1 failure) — attribution
- `test_archived_results_carry_task_id` → the PRE-015 condition above (newest P16-T4 result missing top-level `task_id`). No new escalation (PRE-015 already routes it).
- The two history-guard failures from the prior pass are **gone** from the suite (see ESC-098 close-out below).

## B. Quality review (T8, T9 — diff-first, verified on the live tree)

- **P16-T8 (ledger + Q87 deletions) — clean.** `docs/D55_disposition_ledger.md` exists with every in-scope file in exactly one bucket plus verifier-reproducible condition evidence (spot-read all 7 rows, including the 16-investigation-files keep-current row and the zero-archive-moves record). Deletions verified live: `docs/code_review/review_log.md`, `docs/tasks/task_manager_notes.md`, `dev_docs/` all absent; `docs/code_review/precheck.md` present is the Orchestrator-regenerated replacement (generated artifact, expected). AC2's successor conditions check out (suffixed per-phase chains present). `touches_files` match the Q87 targets exactly — no scope creep.
- **P16-T9 (final review + guard narrowing) — clean.** `docs/D55_final_review.md` exists; the guard diff (reviewed line-by-line) implements exactly the escalation's preferred direction — span narrowed to marker-through-D52 with a re-pinned hash, every protected assertion (D41–D52 headings, marker, stack, reversals) byte-intact in the assertion logic. The `T9_FAIL_NON_DOCS` selfcheck echo is the recorded pre-landed Q84 comment-only `sound_service.py` exception, exit 0 — accepted per the prior pass, not a task defect. `requirements.md` untouched by the task (Analyst-owned; only test files + the final-review doc changed).
- **B.6 mock-endpoint scan:** grepped the reviewed diff (guides + ledger + final review + guard tests) for `mock|fake|stub|simulat` — zero hits. No production module touched by any in-scope task. **Clean.**
- **Usage-doc coverage:** T4's guide correction IS the user-facing update (re-verified live above); T8/T9 are docs-only with no user-facing behavior change. Nothing further owed; stated explicitly per the docs gate.
- **Result credibility:** independent re-runs reproduce every claim (T4_OK exit 0; guards 14/14 green; deletions present/absent as claimed). No worker hid a red suite — the single remaining suite failure is the openly-reported PRE-015 condition.
- **Repeat-invariant rule:** the T4 malformed result is the same case as open PRE-015 (no new entry); the guard narrowing is the first and only patch for that invariant (no accumulation). No prior escalation covers the T8 deletions (first-instance, clean — no finding at all).
- **Out-of-scope notes (no action):** `services/sound_service.py` Q84 docstring and `docs/requirements/*` Analyst additions unchanged since the prior pass; `USAGE.txt`/`usage.md` show as precheck `unattributed_working_tree_changes` only because T4's result is malformed — the edits are T4's declared footprint and correct.

## C. Escalation close-out

- **ESC-097 → addressed (verified).** Command fix landed (`wave/P16-T4.md:104`), T4 re-ran done on substance, corrected command independently re-run live (T4_OK, exit 0). The PRE-015 ride-along did not hold — recorded under PRE-015, not here.
- **ESC-098 → addressed (verified).** Guards narrowed per the preferred direction with all protected assertions intact (diff reviewed); live re-run `test_p14_cache_guard.py` + `test_p15_surfacing.py` → 14 passed; full-suite VERIFY no longer reports either guard.
- **PRE-016 → addressed (verified).** Newest P16-T9 result (`wave260`) carries top-level `task_id`, `done`, clean footprint — well-formed by direct JSON read.
- **PRE-015 → stays open.** Re-verified the fix did NOT hold: newest P16-T4 result (`wave256`, third attempt) still lacks top-level `task_id`. Cures only when a well-formed T4 result lands.

## Findings summary

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| (none) | — | — | — | No new findings; all rework verified except the persistently malformed T4 result (already routed as PRE-015) |

## Pipeline state for the Orchestrator

P16 substance is **complete and sound**: all nine doc tasks meet their ACs, the two history guards are green on the narrowed span, the ledger/final-review close the batch, and the full suite is one failure away from green — that failure being purely mechanical (the T4 result envelope, not any doc content). **1 open escalation remains (PRE-015, BUILD, blocking)** — needs a well-formed P16-T4 result; note the caveat above that three consecutive T4 dispatches have all dropped the top-level `task_id`, so the owner should fix the worker path (or hand-write the envelope) rather than blindly re-dispatching. ESC-097, ESC-098, PRE-016 are closed with live verification. Scope guard held throughout.

Status: REVIEW_COMPLETE

---

# Code Review — Phase P16, final pass (T4 worker-path fix) 2026-11-04

## Pass header

- **Tier: LIGHT (all conditions hold).** Scoped slice is exactly one task (P16-T4, size S): `test_verification.json` verdict **pass** exit 0; `precheck.json` 0 fail_fast, 0 overlaps, no flags beyond informational; no shared/core file touched (`usage.md`, `USAGE.txt` only). No re-review of D1–P15 or P16-T1/T2/T3/T5/T6/T7/T8/T9 — unchanged since review, scope guard held (D55 docs-only, single-doc directive).
- **Scope (incremental):** P16-T4 — the exact precheck scope (result `docs/build/results/_archive/wave263_P16-T4.json` newer than the last `REVIEW_COMPLETE`). Ground truth consumed, not re-derived: `precheck.json`, `test_verification.json` (pass, exit 0, 72.98 s), `build_log.md`, archived result, `task-graph.json`.

## A. Failure diagnosis — nothing blocked

- No task is `blocked`. The former T4 envelope defect is cured (see close-out). Full-suite VERIFY is green, so there is no failure to attribute.

## B. Quality review — P16-T4 (diff-first, verified on the live tree)

- **Result well-formed (not the worker's word).** Direct JSON read of `wave263_P16-T4.json`: top-level `task_id=P16-T4`, `status=done`, `files_changed=[usage.md, USAGE.txt]`, `footprint_flags=[]`, selfcheck `exit_code 0` / tail `T4_OK` on the corrected command (no leading `test `).
- **Substance re-verified live.** `git diff HEAD -- usage.md USAGE.txt`: removes the two `paper (DU)` sentences, states live-only (`live` TWS login, paper-trading not supported, `config/settings.py::check_live_port`), keeps 7496/install/account claims agreeing across both files. Independently re-ran the task command: prints `T4_OK`, exit 0.
- **B.6 mock-endpoint scan:** grepped the reviewed diff for `mock|fake|stub|simulat` — zero hits. No production module touched (docs-only task). **Clean.**
- **Usage-doc coverage:** the changed surface IS the user-facing docs (guide correction); nothing further owed — stated explicitly per the docs gate.
- **Result credibility:** independent re-runs reproduce every claim (T4_OK exit 0; suite pass exit 0). No hidden red.
- **Repeat-invariant rule:** no new invariant — the envelope defect is the already-routed PRE-015/PRE-017 condition, now cured (no new entry).
- **Out-of-scope notes (no action):** precheck `unattributed_working_tree_changes` (`services/sound_service.py`, `tests/test_p14_cache_guard.py`, `tests/test_p15_surfacing.py`) are pre-landed / previously-reviewed items outside every P16 footprint — not reopened. T8's Q87 deletions + T9's final record (ESC-097/098 addressed last pass) confirmed still closed: corrected `test_command` still present in `docs/build/wave/P16-T4.md:104`, both history guards pass (`tests/test_p14_cache_guard.py` + `tests/test_p15_surfacing.py` 14 passed), full suite green — no new evidence, not reopened.

## C. Escalation close-out

- **PRE-015 → addressed (verified).** See verified field on the entry: well-formed wave263 result + live substance + green suite.
- **PRE-017 → addressed (verified).** See verified field on the entry: consolidation-stamped re-run landed well-formed.
- **ESC-097 / ESC-098 → remain addressed.** Confirmed still closed per the cross-checks above; no new evidence, not reopened.
- Zero open entries remain.

## Findings summary

| New id | Linked task | Route | Category / severity | One-line |
|---|---|---|---|---|
| (none) | — | — | — | No new findings; T4 envelope cured, substance sound, suite green |

## Pipeline state for the Orchestrator

P16 is **complete and green**: all doc tasks meet their ACs, the T4 guide correction is live-only and agreeing, the worker-path envelope defect is cured (well-formed wave263 result), and the full offscreen suite passes (exit 0). **0 open escalations remain.** Scope guard held throughout.

Status: REVIEW_COMPLETE
