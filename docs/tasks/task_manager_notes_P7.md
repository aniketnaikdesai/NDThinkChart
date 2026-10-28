# Task Manager notes — P7 (data-path batch)

## Scope
Decomposed `docs/plan.md` Phase P7 only (waves P7-W1…P7-W4). Task IDs are `P7-T<m>`;
`docs/tasks/task-graph.json` holds this phase's 8 tasks and replaces any prior phase file.
No tasks for other phases.

## Wave → task map
- P7-W1 (budget invariant + persist/resume core): P7-T01 (per-load cap + oldest-first floor across loads), P7-T02 (per-chunk persist+render + resume-not-restart), P7-T03 (same-chart coalesce + cancel-slot refund + superseded-162 at debug).
- P7-W2 (watchdog/prime coherence): P7-T04 (window-relative watchdog + strand-clears), P7-T05 (prime precedence + counted skipped-prime warning).
- P7-W3 (gated widening): P7-T06 (measurement record + owner gate; durations change only with approval on record; no automated live step).
- P7-W4 (streaming close-out + gate): P7-T07 (reconnect replay + burst integrity + no-sleep), P7-T08 (watchlist deferral + Q-41 cross-path + manual batch gate).

## ESC-079 (routed_to PLAN) — NOT a build task
ESC-079 asks for the architectural budget invariant and an AC-D16.8 restatement
(floor as an invariant over successive loads). The invariant is answered by S-P7-1
and carried into code by P7-T01; the requirements restatement is Requirements
Analyst territory (plan Flagged Issue 1, tracked as RG-P7-1). No P7 task rewrites
requirements. If the Analyst restates AC-D16.8, P7-T01's AC2 already matches the
satisfiable reading and needs no change.

## Non-blocking requirements debt (for Requirements Analyst, no escalation status)
- RG-P7-1: restate AC-D16.8 as floor-met-monotonically-across-loads (S-P7-1 wording) or confirm it (plan Flagged Issue 1).
- Budget-number drift (plan Flagged Issue 3): ESC-075 cites a 50-slot budget, the tree carries MAX_HISTORICAL_PER_600S=100. P7-T01 states its cap as floor(B/4) so it survives either value; the Validator should confirm which value the suite asserts. No requirement change needed.

## Owner-gated live steps (no automated live step in any task)
P7-T06-T11/T13/T14 and P7-T07/P7-T08 suites are offscreen-only. P7-T06-T12 and
P7-T08-T13 are `manual`-type gate checks: duration values change only with an
owner-approval record naming the timeframe, and any live validation runs only by
the method the owner names (AP-P7-5). A declined widening still completes P7-T06
(chained path stands) per plan Flagged Issue 2.

## Sizing
No size-exception tasks: the largest tasks (P7-T01/T02/T03/T07, size M) stay
within the ~20-step target — each touches at most 3 production files plus one new
test file, with contracts pinned to existing symbols. Serialisation is honest:
the history-wave lifecycle lives in ui/ticker_session.py + ui/main_window.py, so
W1 tasks chain (T01→T02→T03) and W2 tasks follow W1 per the plan's wave order.

## Frozen-interface compliance
No task touches req_historical_data/req_mkt_data signatures, planner contracts,
pacing tunables, error ingress, RealtimeBars/StreamHealth APIs, BarCache APIs,
the Qt-free boundary, the order-code absence, the LWC seam, or the bars schema.
P7-T06 is the single permitted exception (TIMEFRAME_CONFIG duration *values*
only, owner-gated). Pacing refunds (P7-T03) go through pacing_manager, the single
budget owner (AR-P7-4: pre-issue cancels only).

## Addendum 2026-10-28 (Q-51 doc-consolidation — no task or requirement changed)

- **Per-load cap = maximum, never target:** a load issues at most `min(needed, floor(B/4))`
  (`B` = current `MAX_HISTORICAL_PER_600S`); the cap never creates work. Examples at cap 25:
  need 1 -> issue 1; need 10 -> at most 10; need 40 -> at most 25 this load, persist and resume later.
  Per-load = one wave for one symbol + timeframe + mode; same-chart reloads coalesce and share the
  allocation; refunds cover pre-issue cancels only.
- **Budget numbers reconciled:** tree = 100 (`config/settings.py`, owner-set); ESC-075's 50 is stale
  prose named here, not silently chosen; the fraction-based invariant holds under either value.
- **AC-D16.8** stays open Analyst debt (RG-P7-1) — no P7 task rewrites requirements; if the Analyst
  restates it, P7-T01's AC2 already matches the satisfiable reading.
