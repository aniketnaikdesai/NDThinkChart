# Plan Review — Phase P27 (D77–D83), planner / pacing / backfill hygiene

Plan-Section-SHA256: 3674ad63da55043f92308197e6dcf1645e9d494ab189d7b8bec1e4e75a49838f
Architecture-Section-SHA256: cffe89e489e95f9c5dbfbcdf8383a3992164c6b7f8923db1c6def12a9ad9c324

**Review Status:** `Status: APPROVED`

- **Pass type:** `retry_1_of_3` — targeted re-validation of Plan's revision against the three
  Required Changes of the previous cycle (`CHANGES_REQUIRED`, same file). Revision notes were
  present at the top of `docs/plan.md` § *Phase P27*, so each item was checked against the item
  rather than re-running steps 1–9 from scratch; the areas the revision touched (presence
  predicate, traceability labels, D78 quantification, AP-P27-2, the batch qualifier) were
  re-checked end to end, including a fresh empirical run.
- **Phase gate: OPEN.** `docs/code_review/review_log_P26.md` ends `Status: REVIEW_COMPLETE`
  (newer than `docs/build/build_log.md`'s last terminal status), `escalations.json` parses to
  **124 entries, 0 open** — no `routed_to: PLAN` entry open, and no PLAN-routed entry addressed
  during P26's review whose resolution this phase could depend on. **Activated** (see §
  Activation).
- `docs/requirements/requirements.md` § *Phase P27* ends `Status: READY_FOR_PLAN`;
  `docs/plan.md` § *Phase P27* now ends `Status: READY_FOR_TASK_MANAGER`.
- `plan_lint.py --phase P27`: **PASS**, 0 failures, 0 warnings (before and after activation).
- `docs/pending_doc_sync.md`: absent (drained).
- Baseline `623809e` = HEAD; `bda354f` / `d56a97f` / `623809e` re-checked by `git show`: the
  first's only production edit is `ibkr/pacing.py`, the second is docs-only, the third is
  test-only (`tests/test_d28_3_historical_pacing.py`, one of P27-02's exit-condition suites) —
  exactly `AP-P27-1`'s "descendant carrying only P26 review fixes".

---

## 1. Required Changes — verdicts

| RC | Owner | Verdict | Evidence (re-proved this pass, not taken from the revision notes) |
|---|---|---|---|
| **RC-1** — `present_days` must not become half-open | PLAN | **FIXED (confinement)** | The deliverable no longer edits `present_days` at all: P27-01 deliverable 2 states it is not touched, deliverable 3 restricts the edit to its **docstring**, and the *Do not* list pins "signature, equity membership expression, futures branch". `services/backfill_service.py:250` is unchanged in the plan. Reproduced on a `623809e` worktree with P27-01's three edits applied **as written**: ten close-stamped daily days (fixture convention `tests/test_history_backfill.py:110-112`) → `present_days` **10 of 10** in both modes, `find_missing_spans(now = last close, "1 day") == []`, `plan_requests` → `[]`; a locally written half-open variant of the same predicate returns **0 of 10** (§ 2). Exit-condition list: **144 passed, 0 failed**, including both `[1 day-T40SPY]` and `[1 day-T40AAPL]`. Mutation check: flipping `present_days` to `window_start <= ts < window_end` on top of the same edits reddens **exactly** those two params and nothing else in the list. |
| **RC-2** — missing `[revises P17]` | PLAN | **FIXED** | `docs/architecture.md` § *Phase P27* § *Relationship to prior phases* carries `[revises P17: mark_history_request_issued is deleted — its issue-time silence stamp is already made by _register_history_request]`, names all three earlier frozen entries, and states the marker text. Live-tree line references all real: P17's entry at `:7691-7694` (4 lines, incl. the "retry path relies on it" continuation), P26's `mark_history_request_issued` at `:10883`, P26's `refund_historical_slot` at `:10862`. S-P27-5's relationship cell carries the same label. |
| **RC-3** — D78's worst case unquantified | PLAN | **FIXED** | 600 s historical-wait ceiling → `retry_ms ≈ 600_000` → backstop ≈ **601 s** → refusal-to-attach ≈ **615 s** (`≤ 616 s` by `wait + grace + 15 s`) is stated in S-P27-3, AR-P27-4, the *Non-Functional Approach* "Bounded prime" bullet, the `AC-D78.3` traceability row and P27-02 case (e), each naming it as `AC-D78.3`'s "the reported wait plus the backstop" branch rather than a new stall, against today's flat 15 s fail-open. **Arithmetic consistent with the code**: `_prime_backstop_ms = max(15_000, retry_ms + 1_000)`, so `_prime_backstop_ms(600_000) == 601_000`, `(40_000) == 41_000`, `(2_000) == 15_000`, `(15_000) == 16_000` — matching P27-02 (a)(b)(c) and the P27-04 fence. **Reachable, not merely arithmetic**: `prime_aggregator`'s `wait_s` is `PacingExceeded.wait_seconds` (`ui/ticker_session.py:1804-1806`), and the historical branch reports `budget_wait = _hist_times[0] + 600 − now` (`ibkr/pacing.py:229-231`), which approaches 600 s whenever the 100-slot/600 s budget is exhausted — the very "load following a backfill wave" the code's own comment names. **No constant retuned**: `_PRIME_BACKSTOP_MS`/`_PRIME_RETRY_GRACE_MS` are new module constants in `ui/ticker_session.py`; `MAX_REQ_PER_SEC`, `HISTORICAL_MIN_INTERVAL_S`, `MAX_HISTORICAL_PER_600S` are pinned unchanged by the fence. |

**Smaller items — all applied, not reframed:** the batch contract is stated as **`n ≥ 1`** in
S-P27-4, AR-P27-5, the *Relationship* bullet, P27-03 case (f) and the `ESC-129` sentence
(an empty `generic_batch(0)` reserves and stamps nothing) — matching `ibkr/pacing.py:119-133`;
the "eight sites" count is now stated once and cross-referenced (no "six remaining sites"
survives); the `now`-cap membership form is written one way (`now_ts < we`) in both docs; the
baseline citation reads `623809e` everywhere a build starts, with `70b16f2` retained only in
explicitly historical comparisons.

## 2. Re-validation evidence (this pass)

Worktree at `623809e`, P27-01's deliverables 1–2 applied exactly as written (identity set +
`end_ts <= start_ts` skip + dropped `max(1, …)`; conditional `ws <= t <= bound` only when
`now_ts < we`, else `ws <= t < bound`; trailing `bound - in_window[-1] > gap_threshold`).

| Check | Result |
|---|---|
| ten close-stamped daily days, `present_days` (both modes) | **10 of 10** present; the day set is exactly the ten days |
| `find_missing_spans(now = last close, "1 day")` | **`[]`** — no day-presence span, no bar-level span |
| local half-open variant of the same predicate | **0 of 10** — the regression case (h) forbids |
| intraday pre/post-only day under RTH | **not present** (case (h)'s third clause) |
| a `present_days` call whose only bar is the window end | **present** (case (h)'s fourth clause) |
| trailing edges (`> 1.5p`) | 1.0p not reported; 1.5p not reported; 1.5001p, 1.7p, 2.0p reported — the FI-P27-3 band `(1.5p, 2p)` exactly |
| complete 5-min session + a 16:00 close-instant bar | **0 spans**; the close-instant bar is not accounted in the closing window |
| full P27-01 exit-condition list | **144 passed, 0 failed** |
| same, with `present_days` mutated to half-open | 2 failed — **exactly** `[1 day-T40SPY]`, `[1 day-T40AAPL]` |
| same, with case (h)'s assertions | the "10 of 10" assertion fails at 0 of 10 under the mutation, passes unmutated |

**Is case (h) genuinely discriminating, and not a restatement of the implementation?**
Discriminating: yes — demonstrated by mutation above; its first assertion fails the moment
half-open membership returns to `present_days`, and its `find_missing_spans == []` clause adds the
downstream consequence (a re-requested daily history) that the aggregate suites only witness
indirectly. Not a restatement: every clause is a value assertion over the public predicate
(counts, set membership, an empty span list), not a shape assertion over the code; the
test-local half-open variant is a *fixture guard* (it proves the series is end-stamped, so a
future bar source that moves the stamp would surface here rather than pass silently). One
requirement on the worker worth stating: the case is only as good as its fixture, so the ten
days must be generated with the tree's own `_et_ts(..., 16, 0)` convention, not injected
midday.

## 3. Is "one stated rule" (D82) still honest with the rule on one of two predicates?

**Yes — a legitimate distinction, not the drift D82 removes.** D82 removes *two numbers and two
memberships for one question*: assigning a bar to one window of one day (a partition, so no
instant may count twice). `present_days` answers a different question ("did this day's data
arrive in this mode?") and returns `Set[date]` — it assigns no bar to any window, so `AC-D82.1`'s
measurable ("belongs to exactly one window — never two") has no referent there. D82's own
*Expected behaviour* consequence ("a single missing bar at the close is not requested, a
two-period hole is") is bar-level. Both predicates are now stated once each **with the reason
they differ** — *Relationship to prior phases*, the Codebase Summary row, S-P27-2, the *Tech
Stack* row, *System Components* item 3, *Non-Functional Approach*, AR-P27-2, and the two
docstrings (P27-01 deliverable 3) — which is strictly more than "one number"; nothing is silently
dropped. The rejected alternative is also right: a **timeframe**-keyed second rule would be the
drift, because the distinction would be invisible at the call site; the question asked is visible.
Two consequences checked: no silent hole (a day with no in-window bar is still reported missing by
the day-presence pass, and `_bar_level_missing_spans` returns `[]` for `period >= 86_400`, so a
close-stamped daily bar never reaches the bar-level pass), and no double-request (de-duplication
is unchanged by the confinement).

## 4. One line per validation step

- **Requirements coverage — PASS (delta):** every P27 AC/journey still maps to one wave (traceability
  table unchanged in coverage); the only requirement drift since the previous cycle is `RG-P27-1`'s
  rewording, and the plan tracks it in three places: the `AC-D77.1` traceability row, `AP-P27-2`
  (now asserting the criterion **literally** — identity multiset, before/after coverage identity
  against an independently computed set of the input spans, containment — which is word-for-word
  AC-D77.1's measurable), and `FI-P27-1` marked **CLOSED**. `D77`, `Journey 71`, `A230` and `R170`
  now carry "unchanged by the change and containing every input span"; no stale union-equality
  claim remains outside `FI-P27-1`'s history note.
- **Architecture completeness — PASS:** stack, components/responsibilities/relationships, data model,
  integrations, frozen boundaries, non-functional approach, risks (AR-P27-1…9) and labelled
  decisions (S-P27-1…7) all present, each with a rationale and named alternatives; RC-3's item is
  now quantified where it is discussed, not in a footnote.
- **Architecture consistency — PASS:** no phase depends on undefined architecture; no new module,
  dependency, migration or settings key; `plan_requests` imports unchanged (`math`, `dataclasses`,
  `datetime`, `typing`, `zoneinfo`, `config.settings`, `data.bar_aggregator`,
  `ibkr.market_data`, `services.market_calendar` — no DB, clock or Qt); the D80 retirement's
  invariants check out against the tree (P17's issue-time stamp duplicated at `:977` before the
  deleted `:997`; mark call sites adjacent to registration at `:1375→:1379` / `:1261→:1263`).
- **Plan quality — PASS:** four waves ordered by file ownership (P27-01 ∥ P27-02 → P27-03 → P27-04),
  each stating goal, covered ids, dependencies, deliverables and an exit condition; sizes M/S/M/S;
  no task-level breakdown, no dependency graph, no per-task test spec.
- **Task Manager readiness — PASS:** the presence question is decided (inclusive, confined, with
  case (h)) and the P17 supersession is declared and marked — the two decisions that previously
  blocked decomposition. Nothing in the four waves requires a new architectural decision.
- **Existing-repo compliance — PASS:** Codebase Summary substantive and site-by-site; the
  `present_days` row, the *Summary*, *Tech Stack*, *System Components*, *Integration Points*,
  *Non-Functional* and AR-P27-2/9 all updated consistently with the confinement; existing stack
  listed first, nothing replaced or deprecated; `[existing]`/`[new]`/`[new/changed]` labels present
  on Components, Data Model and Integration Points; `docs/codebase-map.md`'s P27 note updated
  ("half-open *window membership* in the bar-level gap pass … day presence keeps its inclusive
  close") so the stale phrase the last cycle warned about is gone.
- **Frozen interfaces — PASS:** 45 entries spot-checked against the tree; the five apparent misses
  are line-wrapping only (`BarCache.prune`, `queue_wave_plans`, `_schedule_wave_continuation`,
  `prime_aggregator`, `_missing_backfill_trading_days`). Every entry is `[existing]`; every changed
  or deleted item is under **not frozen**; no duplicates; every owning module resolves.
- **Codebase map — PASS:** no production module added/renamed/deleted; the P27 note's key files
  exist; status labels current; no duplicate or dangling module reference.
- **Pending doc sync — PASS:** file absent.

## 5. Activation (what changed in the canonical docs)

1. `docs/plan.md` § *Phase P27*: closing `Status: READY_FOR_VALIDATION` → **`Status:
   READY_FOR_TASK_MANAGER`** (the entire activation).
2. `docs/architecture.md` — the four supersession markers the declared labels direct (old
   sentences kept visible, none rewritten, no earlier status changed):
   - P17 `:7691-7694` `mark_history_request_issued` → `[superseded by P27 — S-P27-5; see § Phase P27]`;
   - P26 `:10883` `mark_history_request_issued` → the same marker;
   - P26 `:10862` `refund_historical_slot` → the same marker;
   - P26's frozen `def throttle(self):` in the same pacing bullet → `[superseded by P27 — S-P27-4;
     see § Phase P27]` (the signature this phase revises; the plan declared the `[revises P26]`
     label but named only the deleted symbols, so the marker is added here under the same
     S-P24-6/DG127 convention).
3. `docs/architecture.md` § *Phase P27* § *Not frozen*: added `present_days`' **docstring statement
   only** (signature / equity membership / futures branch stay frozen) — restating P27-01
   deliverable 3 and its *Do not* list, so a worker is not left with a frozen entry and an
   instruction to edit the docstring.
4. Editorial trims (no decision content): the `_history_req_issued` table row now points at the
   "eight sites enumerated in `docs/plan.md` P27-03 deliverable 4" instead of restating a second,
   slightly different enumeration.

## 6. Observations (non-blocking, no action required of any agent)

- D82 *Expected behaviour* reads "Session/day windows are half-open `[start, end)`" without
  qualifying that the rule is window *membership*. Every AC it owns (`AC-D82.1`, `AC-D82.2`) is
  satisfied and `AC-D16.9` is preserved, so this is a compression in the prose, not a criterion
  bending — worth a one-clause qualifier the next time that requirement is touched, not worth an
  escalation.
- `AC-D77.1`'s "coverage unchanged by the change" is strict about coverage *gain*; D83's removal of
  a zero-length span's plan removes a degenerate coverage. The two are consistent as read (AC-D77.1
  is D77's criterion, AC-D83.1 is D83's, and an empty interval is contained in any coverage), and
  `AP-P27-2` scopes the coverage-identity assertion to the coinciding/partially-overlapping
  fixtures. Recorded so the next reader does not have to rediscover the reading.
- P27-01 case (f)'s "1.7-period trailing hole" needs an off-grid timestamp (or a finer timeframe)
  because 1.7 × 300 s is not a multiple of the 5-minute grid; verified constructible and that the
  rule reports it while 1.0p and exactly 1.5p are not reported. The worker should not quantise the
  fixture onto the grid and lose the distinguishing point.

## Final Decision

`Status: APPROVED`

Task Manager may proceed: `docs/plan.md` § *Phase P27* is `READY_FOR_TASK_MANAGER`, the
architecture's P27 material is active with the supersession markers in place, and no PLAN-owned
item remains open. `RG-P27-1` is `addressed` in `docs/plan_notes.md`; nothing is escalated.
