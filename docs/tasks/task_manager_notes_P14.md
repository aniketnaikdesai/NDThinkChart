# Task Manager Notes — P14 (D53 persistent backfill-state indicator + cache-current guard)

## Decomposition
- 3 tasks over plan waves P14-W1...P14-W3: P14-T1 (M) indicator widget -> P14-T2 (M) terminal-path lifecycle + coalesced-keep -> P14-T3 (S) cache-current guard + history gate. Strict chain (each wave depends on all earlier per plan).
- Sizes M/M/S only, per orchestration constraint. No L: T2 keeps the 4-path case as one parametrized test rather than four tasks.
- Every task touches ui/main_window.py (the indicator, its hooks, and the guard all live there by architecture S-P14-1...S-P14-3); serialization comes from the DEPENDS_ON chain, not just file overlap. T2 additionally touches ui/ticker_session.py (the one additive in-memory wave-start field).
- New test files (tests/test_p14_*.py) are in touches_files but NOT in read_files (they do not exist yet; the checker fails read_files on missing paths). Existing convention suites are the read_files entries instead.

## Stated decisions (mine, within architecture bounds)
- Indicator API names (_backfill_indicator, set_backfill_state, clear_backfill_indicator), the session field name (_wave_start_ts), and the predicate name/signature (_is_cache_current(symbol, timeframe, extended_hours) -> bool) are Task-Manager-level implementation names, not architecture choices: S-P14-1...S-P14-3 pin the surface, hooks, and predicate semantics; the names only label them.
- AC-D53.4's "Current Tech Stack intact" is asserted as unchanged, not corrected: architecture notes the pyqtgraph line is stale but explicitly scopes it out of D53 (no wave reads or writes it).

## Flags / escalations
- None. No ambiguity, no undecided architecture, no escalation. Q78-Q80 proceed on defaults per AP-P14-1.
