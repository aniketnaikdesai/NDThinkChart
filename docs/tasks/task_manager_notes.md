# Task Manager Notes — Batch 3–9 revision (T21–T31)

Revision date: 2026-09-27. Source of truth: `docs/plan.md` (APPROVED, validation pass 2)
and `docs/architecture.md`.

## Scope added
T21–T31 extend the existing T1–T20 graph (all `done`, unchanged) with the approved
revision work and the Code Reviewer escalations that the plan now covers:
ESC-002 (T21), ESC-003/ESC-008 (T22), ESC-007 (T23), ESC-006/D2 (T24, T25),
ESC-001 (T26), RC-4a D10 (T27), ESC-005 (T28), ESC-009 (T29), ESC-010 (T30),
plus a revision-wide verification task (T31).

## Sequencing / `touches_files`
- `ui/chart_panel.py` is touched by T21, T22, T23, T24, T27, T28 and T30. Because the
  Lead must not run two tasks with overlapping `touches_files` in one wave, the chain is
  encoded as explicit dependency edges — `T21 → T22 → T23 → T24 → T27 → T28 → T30` — in
  addition to the per-task `touches_files` field, so wave scheduling is deterministic.
- T25 (`tests/test_drawing_labels.py`), T26 (`data/db.py`, `tests/test_db_schema.py`) and
  T29 (`tests/test_chart_dpi.py`, `tests/conftest.py`) share no file with the
  `chart_panel.py` chain and may be scheduled concurrently with it.
- T28 also depends on the already-built T17 (watchlist clamp); T30 on the already-built
  T18 (D14 double-click path). Done tasks are treated as satisfied dependencies.
- T31 (`touches_files: []`) depends on all of T21–T30 and is the single terminal
  verification node for this revision.

## Flagged items (no requirements gap)
1. **A25 — D2 dock-open visibility needs independent Code Reviewer verification.** T24's
   Build tests cover the chip lane/style/tracking and a dock-open layout assertion, but
   per `Architecture Risks` and `requirements.md#D2/A25` the re-opened D2 defect surface
   (decimals covered by the right-hand dock) must be **independently verified by the Code
   Reviewer after Build**. The task graph cannot make this a Build-only pass; T24's
   acceptance criteria record the requirement so the Code Reviewer can key off it.
2. **ESC-005 may need a minimal rebalance change.** T28 is scoped as a combined
   integration test, but `ui/chart_panel.py` is included in its `touches_files` so Build
   may add a single rebalance helper if hiding the volume panel plus a max-clamp watchlist
   drag can drop the price panel below its 400px minimum. No architecture decision beyond
   the plan's "consider a single `rebalance()` helper" is required.
3. **TR-17 ownership.** The Phase-4 symbol-change mode reset (router → `IDLE`) is wired in
   T30 (`ui/chart_panel.py`), which depends on T21's `exit_to_idle()` API. `DrawingOverlay.set_data()`
   already clears the draft/drag defensively (`:112–118`); T30 only adds the router reset
   and the ESC-010 regression test.

No architecture assumptions were invented and no requirements ambiguity was found; the
items above are coordination/verification notes carried from the approved plan and the
escalations file.
