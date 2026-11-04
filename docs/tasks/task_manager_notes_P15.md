# Task Manager Notes — P15 (Batch 29 / D54 10-second target on load chart)

## Decomposition

Three tasks mirror the three plan waves one-to-one (M/M/S), strict chain
P15-T1 -> P15-T2 -> P15-T3 per the plan's ordered-waves, one-commit-per-wave
rule. All three touch `ui/main_window.py` (the expiry hook, seams, and
surfacing all live there per S-P15-1…S-P15-3) plus one new test file each, so
the `DEPENDS_ON` chain — not file non-overlap — is what serializes them.

- P15-T1 owns the timer member, arm/disarm, `_on_backfill_expiry`, and the
  expiry render (partial bars + verbatim AC-D16.4 shortfall, single-sided
  T0+10.0 s bound, zero-bar edge).
- P15-T2 owns the continue semantics and the three seams (disconnect-wins,
  mode-switch/new-triple re-anchor, coalesced-keep). No new symbols: it wires
  T1's timer through the existing terminal paths, so its contracts are all
  existing refs (a forward ref to T1's new symbols would fail validation
  before T1 lands).
- P15-T3 owns the surfacing marker plus the AC-D54.4 history check and the
  suite gate. The partial-marker copy (`Backfill (partial): …`) is stated as a
  new contract so the worker implements the decision rather than
  reverse-engineering it from the test; the complete side reuses the unchanged
  clear/completion path with no new copy (D53 referenced, not reworded).

## Size reasoning

T1 and T2 are M: each touches ~5 main_window regions plus a new offscreen
suite with 4 clock-controlled cases — well within the ~20-step target. T3 is
S: one marker on existing writes plus a static history check. No task needed
the ~32-step exception.

## Deliberate non-splits

The timer-arm site (load_chart raise) and the disarm sites (finalize funnel)
stay in T1 rather than splitting arm vs disarm: an armed-but-undisarmed timer
is not independently verifiable, and T1's AC3 already pins the disarm
invariant. Session/planner/cache are read-only in all three tasks per S-P15-4.

## No escalation

No architectural decision was needed: T0 baseline, single-shot shape,
background-continue, and D53-surface defaults are all settled in the approved
plan/architecture (S-P15-1…S-P15-4, AP-P15-1…AP-P15-5). Q81–Q83 proceed on
their logged defaults per A148; nothing was flagged to Requirements Analyst.
D1–P14 are not reopened; Finding 1 / watchdog / TWS-side causes untouched.
