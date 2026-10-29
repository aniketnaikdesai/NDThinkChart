# Review log — Phase P13 (D49 pop-out robustness + D49.6 timezone handoff)

- **Pass type:** incremental terminal-gate verification (Orchestrator-launched). Scope per `precheck.json`: P13-T1..T09.
- **Tier: FULL** — T09 is `blocked` in scope (light pass requires all-green) and overlaps exist on `ui/main_window.py` / `ui/popout_window.py` (info-only cross-task leads).
- **Ground truth consumed, not re-derived:** `precheck.json` (0 fail_fast, footprints verified, doc candidates), `test_verification.json` (verdict **pass**, exit 0, 71.77 s full offscreen suite). No full re-runs by me except flagged-task spot checks below. No code, test or config file modified by me.
- **Escalations opened this run:** ESC-095 (1). **Closed this run:** none — all 73 prior entries are `addressed` and `precheck.json` reports `escalation_updates: []`.
- **Q-62-adjacent items:** per dispatch, worker-verified source fixes were taken as given and re-verified only to the extent of confirming the gate holds; nothing closed or re-opened.

## T01–T08 verification (live tree)

Diff-first over the working-tree diff (`git diff`, uncommitted P13 work) restricted to each task's verified `files_changed`, plus targeted test runs. Full-suite green is carried by `test_verification.json`.

### P13-T1 — cold restore data-path ensure (`ui/main_window.py`, `tests/test_p13_restore.py`) — done, verified
- `_ensure_restore_data_path` is cache-first per S-P13-1/A121/R96: BarCache read → `prepare_load`/`set_bars` → `find_missing_spans` (with `MIN_INTRADAY_SESSIONS`) → existing `plan_requests`/`queue_wave_plans` wave. Live-session symbols early-return (no second aggregator/subscription); disconnected restore returns before any ensure with a status message and no request — matches AC-D49.1 incl. the D14-style no-op.
- Spot run: `tests/test_p13_restore.py` 3/3 pass.

### P13-T2 — transactional attach (`ui/popout_window.py`, `tests/test_p13_attach.py`) — done, verified
- `attach()` records per-step flags (connected signals, view, hold-only-where-`ensure_rt_subscribed`-returned, registration, resources) and unwinds in reverse with disconnect-signals-first (R97); `detach_view` reuse (frozen) and `_session=None` drop make post-failure `detach()` a safe no-op. `_retry_rt_subscribe` guards on membership in `_host._popouts`, so a failed-then-unregistered pop-out's retry is a no-op and no retry is scheduled on raising paths. Unwind targets (`_unregister_popout`, `detach_view`, `release_rt`, `_release_memory`, `_geometry_dict`) all resolve to real methods.
- Spot run: `tests/test_p13_attach.py` 2/2 pass.

### P13-T3 — host-failure error state (`ui/popout_window.py`, `tests/test_p13_host_error.py`) — done, verified
- Dedicated `PopoutEngineError` message area + `PopoutStatus` strip, text via `chart_engine_failure_message` verbatim (lazy import avoids the cycle), distinct object from the chart (unambiguous vs no-data), diagnostic `_LOG` retained in `_ensure_engine_host`. Matches S-P13-3/A123/A124.
- Spot run: `tests/test_p13_host_error.py` 2/2 pass.

### P13-T4 — single fan-out (`ui/ticker_session.py`, `ui/popout_window.py`, `tests/test_p13_fanout.py`) — done, verified
- Change point is emit-only (`reload_drawings` reloads + emits); all four commit paths in `main_window.py` pair reload + exactly one direct `sync_drawings_to_views()`; each pop-out `_on_drawings_changed` refreshes only its receiving view through the same `drawing_overlay.set_data(symbol, drawings, groups)` surface the LWC view exposes (property at `lwc_view.py:3075`), with a Q-43 warn-and-continue guard. Signal + wiring kept (A125). Only pop-outs consume the signal, so no consumer loses updates. Matches S-P13-4.
- Spot run: `tests/test_p13_fanout.py` 2/2 pass.

### P13-T5 — hold probe (`tests/test_p13_hold_probe.py`, `docs/p13_hold_probe_record.md`) — done, verified
- Record verdict: **no lasting effect** (holds == owners at every step incl. zero-owner). No production file touched by the task — confirmed in the diff.

### P13-T6 — conditional fix (`ui/ticker_session.py` footprint, `tests/test_p13_hold_fix.py`) — done, verified
- Tree matches the clean verdict: the `ticker_session.py` diff carries only T4's `drawings`/`drawing_groups` properties + `reload_drawings` docstring — no hold-accounting change, exactly as the record-gated rule (A126/R98) requires.
- Spot run: `tests/test_p13_hold_probe.py` + `tests/test_p13_hold_fix.py` 4/4 pass.

### P13-T7 — tz create threading (`ui/main_window.py`, `ui/popout_window.py`, `tests/test_p13_tz_create.py`) — done, verified
- `_open_popout` passes `self._tz_offset`; the hardcoded `tz_offset=0.0` at the creation call site is gone; `create_chart_view` seam signature unchanged; no new timezone source. Matches S-P13-6/A133.
- Spot run: `tests/test_p13_tz_create.py` 2/2 pass.

### P13-T8 — tz persist/restore (`data/popout_store.py`, `ui/main_window.py`, `tests/test_p13_tz_restore.py`) — done, verified
- Additive nullable `tz_offset` column via `_ensure_tz_column` (idempotent; lives in the store, not `data/db.py`); `save` preserves on UPDATE-when-None / stores NULL on INSERT-when-None; `load_all` always surfaces the key (NULL → None); restore applies stored offset with the A134 main-chart-current fallback, never silent UTC. Matches S-P13-6/A134 and the documented contract addition.
- Spot run: `tests/test_p13_tz_restore.py` 2/2 pass.

### Non-escalated observation (no action needed)
- `_open_popout` saves twice per open (attach's tz-less save, then the tz-stamping upsert on the same row). Harmless same-row upsert; noted for awareness, not routed.

## P13-T9 — batch gate — blocked, rework routed (ESC-095)
- `failures.json` records 2/3 with two deterministic, out-of-footprint failures (archived `wave220_P13-T6.json` missing `task_id`; `test_lwc_popouts` residue expectation predating the P13-T7 `tz_offset` column), both reproduced with the gate file stashed, plus pacing flakes that pass 19/19 in isolation.
- Re-verified on the live tree: `wave220_P13-T6.json` now carries `task_id` (direct read); `tests/test_lwc_popouts.py` expects the 6-param signature (live diff); spot runs green — all P13 suites 32/32 and both former blockers (`test_lwc_failure_visibility.py`, `test_lwc_popouts.py`) green; full suite green per `test_verification.json` (verdict pass, exit 0).
- Root cause of the remaining `blocked` is procedural, not code: only a fresh BUILD re-dispatch re-stamps the gate. Filed **ESC-095 → BUILD (blocking)**: re-run P13-T9 as a gate re-stamp, no code change expected.

## Standing checks
- **B.6 mock-endpoint scan (blocking invariant):** grepped the reviewed diff for `mock|fake|stub|simulat` × `endpoint|client|service|server|api|harness` — the single hit is a pre-existing comment (`ticker_session.py:156`, "tests / stub hosts" fallback note), not a production mock endpoint and not an import of a test fake. **Clean.**
- **Usage-doc coverage:** `precheck.json` doc candidates are `USAGE.txt` (untouched), `docs/` (touched = the `p13_hold_probe_record.md` probe record, not a user doc), `usage.md` (untouched). Judgment: P13 adds no user-facing surface — no new feature/CLI/API/config/workflow, only internal robustness plus a correctness fix that restores identical time labels. No doc update owed; the `touched` flag on `docs/` does not satisfy user-doc coverage and none is required. Stated explicitly per the docs gate.
- **Consistency:** implementation matches `architecture.md` S-P13-1…S-P13-6 / A121–A126 / A133–A134 (spot-checked); `requirements.md` AC-D49.1–AC-D49.6 paths verified above; AC-D49.7 history/intactness is the T9 gate's own T92 check (13/13 in isolation per the worker report).
- **Escalation close-out (entry C):** no open entries at run start (73/73 `addressed`, `escalation_updates: []`) — nothing to re-verify or flip.

## Final close-out (2026-10-29T21:16:12Z) — T9 gate re-stamp verified, ESC-095 closed

- **Scope:** terminal close-out per dispatch. Ground truth consumed, not re-derived: `precheck.json` (0 fail_fast, scope P13-T1..T9 all `done`, footprints verified, overlaps info-only) and `test_verification.json` (verdict **pass**, exit 0, full offscreen suite). No code, test or config file modified by me.
- **T9 re-stamp verified on the live tree (entry C, not the worker's word):** archived `wave225_P13-T9.json` status=`done`, `task_id`=`P13-T9` present, `footprint_flags`=[], selfcheck verdict=`pass` exit 0 (gate 13/13 + full suite 1329 passed / 3 pre-existing webengine skips); `task-graph.json` P13-T9 status=`done`; `build_log.md` ends `Status: READY_FOR_REVIEW`. My own runs: `tests/test_p13_gate.py` 13/13 pass; gate + both former blockers (`tests/test_lwc_popouts.py`, `tests/test_lwc_failure_visibility.py`) 30/30 pass. The procedural `blocked` is resolved — no code change, as predicted.
- **ESC-095 → addressed** (verified string above). Only open entry in `escalations.json`; no other open escalations to close.
- **New findings:** none. T1–T8 verification stands from the prior pass; B.6 mock-endpoint scan re-run on the P13 production diff — clean; usage-doc judgment unchanged (no user-facing surface, no doc update owed); full suite green per `test_verification.json`.
- **Escalations opened this run:** 0. **Closed this run:** ESC-095 (1).

Status: REVIEW_COMPLETE
