# P30 — Review Log (phase-final pass)

**Phase:** P30 (D101–D104 + the three RG closure records) — **the last phase of the audit fold-in.**
**Pass type:** phase-final. **Tier: FULL** — required unconditionally for the phase-final pass, and
independently forced here because `ui/lwc_view.py` is a shared file (P30-T1, P30-T3, P30-T5).
**Build commits:** `9425555` (T1–T4), `f68b00b` (T3/T5/T6/T7 + requirements); phase base `956f9f8`.
**Facts consumed (not re-derived):** `precheck.json` (7 tasks, 16 entries, 4 `fail_fast`, `escalation_updates: []`,
`unattributed_working_tree_changes: []`, doc candidates `USAGE.txt` / `usage.md` / `tests/test_p25_usage_doc.py`,
all `touched: false`); `test_verification.json` — **verdict `pass`, exit 0, 262.55 s, TWS listening**, newer than
`build_log.md`. Per `build_log.md`: `Status: READY_FOR_REVIEW`, all seven tasks `done`, no blocked task. I did not
re-run the full suite (the Orchestrator run is ground truth); I re-ran only the eight phase-relevant suites
(74 passed, exit 0) to attribute the phase's own claims.

## 0. The four `fail_fast` flags are the known false positive — verified, nothing filed

`precheck.json` flags "claimed file but git shows no change" for every file claimed by T1–T4. Confirmed false
positive and confirmed *why*: those workers' edits were committed inside the phase (`9425555`), so the
working-tree comparison the check uses sees nothing, while `git diff --stat 956f9f8..HEAD` lists **every** claimed
path — `chart_assets/lwc/{chart.html,chart.js,interaction.js,controls.test.js,interaction.controls.test.js}`,
`ui/{chart_controls.py,lwc_bridge.py,watchlist_panel.py,drawing_groups_dialog.py,main_window.py,popout_window.py}`,
`services/chart_model.py`, `tests/test_d101_control_cluster.py`, `tests/test_d102_d103_surface_state.py`,
`tests/test_d104_stale_claims.py`, `tests/test_p30_fence.py` (all present, all changed vs base). Tree is clean.
**No `PRE-*` entry was filed and none is treated as real.** `escalations.json` has zero open entries of any kind.

## 1. P30-T1 — D101 / D101.2 (restore + latch) — **verified**

- **Mounted, not a mirror.** `chart.html` carries `<div id="controls" role="toolbar">` inside the reserved
  price-scale gutter; `chart.js::init()` calls `mountControlCluster()` (once per `init`, before `bindChannel`) →
  `LwInteraction.mountControls(container, controlPressed)`; `mountControls` builds `control-{id}` buttons in
  `CONTROL_SPECS` order. `CONTROL_IDS` is now `tuple(spec.id for spec in CONTROL_SPECS)`, so the mirror is derived
  from the one declaration (`ui/chart_controls.py`), not a second literal.
- **Python surface reachable in production.** `chart.js::controlPressed` → `window.lwBridge.controlPressed`
  (`@pyqtSlot(str)`) → `pageControlPressed` → `LwcChartView._on_page_control_pressed` → `handle_control`; the
  connection is made in the view's constructor and the AST test
  (`test_p30_t01_the_shim_has_a_production_caller`) proves the call graph, not just the symbol.
- **Latch is answer-driven.** `mountControls` computes `value` and **never** writes `aria-pressed` before the
  call; in production `controlPressed` returns `undefined`, so nothing is optimistically latched (node case (f) and
  `test_p30_t01_a_toggle_press_is_not_latched_ahead_of_the_answer` pin that). The authoritative state then arrives
  as the durable `router_mode` / `reset_view` op and `syncControlState` sets `aria-pressed` to
  `mode === "ZOOMING"`. With a synchronous shim, the three branches are: refused → pre-click value;
  mode → drive-from-return; no answer → leave it. Both starting states are exercised
  (`interaction.controls.test.js` (c) off→refused → stays `"false"`; (d) on→refused → stays `"true"`), and neither
  ever adopts the refused request.
- **Refusal reported exactly once on the shipped path.** Production has one report site: the Python slot emits
  `zoom_refused` once for `result["refused"]`, asserted by `test_p30_t01_a_refused_toggle_is_reported_exactly_once`
  (`refusals == [True]`, one op appended, router still `ALARM_PLACING`). The page's own `pageZoomRefused` is not
  reached from a button press in production (the JS report branch needs a returning shim), so there is no double
  report. The refused op carries the **actual** mode (`ALARM_PLACING`/`DRAWING`), which is what the following
  `syncControlState` latches — the attribute equals the state in effect.
- **Local action, durable state only.** The click applies `zoom(range, 0.8|1.25)` / `fitAndFollow()` in the page
  *before* reporting; Python publishes only `{"op":"router_mode"}` (magnifier), `{"op":"reset_view"}` (reset) or
  `{"op":"zoom","step":±1}` (the two step buttons). **No new consumer exists for `zoom`**: `chart.js::applyChannel`
  has no `op.op === "zoom"` branch and `gestures.applyRouterOp` ignores it (`nextRouterState` reads
  `mode`/`tool`/`intent` only), so a replayed step cannot re-fire. The `reset_view` branch is pre-existing (it only
  sets `routerState.mode/tool`; it does not re-frame), so a replay re-asserts state, not the viewport — the comment's
  claim holds on the live tree.
- **Residual, recorded not escalated:** `ChartControls` is still constructed nowhere. That is the declared
  Q118/A246 shape ("the page surface, not the widget") and satisfies AC-D101.5's second branch (signal names carried
  by `CONTROL_SPECS`, which production imports). It is not a test-only control surface in the page.

## 2. P30-T2 — D102 / D103 (popup + selection) — **verified**

- `_apply_collapsed_visual` is the one visual owner and now calls `clear_search_results()` whenever
  `collapsed`; every collapse entry point funnels through it (`set_collapsed` → `_on_header_toggled` →
  `_apply_collapsed_visual`; the header button, `toggle_collapsed` and the collapsed-handle `eventFilter` all call
  `set_collapsed`). No parallel hide path exists.
- **Late delivery cannot resurrect it:** `show_search_results` returns early (and clears) while `_collapsed`, so a
  debounced answer that lands after the collapse is refused — AC-D102.2; the test covers the in-flight case and
  proves the guard is not a permanent mute (a new query after expanding still shows).
- **Clearing the items is in scope, not a behaviour change.** AC-D102.1 says, verbatim, "the popup is hidden **and
  its items are cleared** (Measurable: `isVisible()` false + list count zero)", and Journey 83's postcondition adds
  "no stale items survive into the next query". Reporting it as a behaviour change would contradict the criterion.
- **Selection restored by identity.** `reload()` captures `set(self._selected_drawing_ids())` *before* the rebuild,
  then re-selects each item whose `UserRole` drawing id is in that set; a vanished id is simply absent, so the
  restored set is exactly the survivors. No index-based fallback and no "skip the reload" shortcut (the groups table
  and the drawings list are both rebuilt). The groups-table row selection is deliberately not restored, which is
  documented and independent (it is a different widget). `drawings_list` has no selection-changed connection, so
  restoring selection during the rebuild has no side effects on the actions.

## 3. P30-T3 — D104 (sweep + release) — **verified**

- **Counts re-derived independently.** `grep -ri pyqtgraph` over `ui/ services/ data/ ibkr/ *.py` now returns
  **12 hits in 10 files**; the eight eliminated hits are `ui/main_window.py` ×3 + `ui/popout_window.py` ×4 +
  `services/chart_model.py` ×1 (the "until P6-13" sentence) → **20 hits / 12 files**, exactly the declared split of
  12 allow-listed (8 negative assertions + 4 marked-history lines) and 8 eliminated. Each allow-list row is keyed by
  `(path, distinctive fragment)` and required to survive exactly once, so a new claim cannot hide behind an old one.
- `services/chart_model.py:273` now reads "the retired renderer's local copy went with it" — a positive assertion
  that the copy is gone, replacing a present-tense promise about a future phase that has already passed.
- `release_resources` clears the five `_channel_logs` buckets and `_channel_queue` in addition to the four
  `_op_log`/`_queued`/`_outbox`/`_live_buf` buckets; the docstring is the contract and now matches the body bucket
  by bucket.
- **Cannot break the replay contract.** The only caller is the pop-out close path
  (`ui/popout_window.py:337`), *after* the view detaches from the session; `_replay_channels()` runs on a page-ready
  transition of a live view and always reads the same dict it would read before. Once released the view is being
  destroyed, so no replay can observe an emptied log mid-life.
- `memory_bytes` is untouched (still `replay_log()` = `_op_log` only). The under-report is recorded as **AR-P30-6**
  (`docs/architecture.md:12284` + the release docstring). **One wording finding remains** — see ESC-142.

## 4. P30-T5 — `QWebChannel` literal — **verified**

`grep -n QWebChannel ui/lwc_view.py` → **no hits**. The docstring now states both shipped facts: the page cannot
read the shim's answer (a slot returns nothing), so the refusal is reported once on the Python side, and the router
op the shim publishes is what drives the pressed state. The fence is untouched by P30
(`tests/test_lwc_overlays.py` last changed in `153c317`) and still lists `"QWebChannel"` in
`TestRendererBoundary.FORBIDDEN` for `ui/lwc_view.py` — so the removal satisfies the fence rather than weakening it.
The full suite (and my targeted re-run) is green.

## 5. P30-T6 — batch-gate base compare — **verified**

`_phase_graph` reads `docs/tasks/task-graph.json:meta.baseline_commit` and **asserts** it is a non-empty string with
the explicit message "HEAD is never a substitute". The base is then resolved with `git rev-parse --verify` and
ancestor-checked with `git merge-base --is-ancestor`; `_git` asserts `returncode == 0`, so a bogus or non-ancestor
base raises instead of silently comparing. The allowlist is the union of every task's `touches_files` filtered to
`tests/` (self-inclusive — `tests/test_d64_batch_gate.py` is asserted present) and is asserted disjoint from the
D19/D20 fixtures; `git diff --name-only <base> -- tests/` keeps untracked files out of scope exactly as before.
Live `meta.baseline_commit` is `956f9f8`, an ancestor of `HEAD`; the scratch-repo case proves an allowlisted edit is
admitted committed **and** uncommitted, and an unlisted edit is named.
**A future phase that forgets the key fails loudly** (AssertionError) — it cannot pass vacuously or fall back to
HEAD. Residual, not a finding: a valid-but-too-old base would widen the window rather than fail; that is a wrong
*value*, not a forgotten one.

## 6. P30-T7 — digest re-pin — **verified independently**

Recomputed on the live tree: `sha256(requirements.md[text.index("This is an existing repository.") :
text.index("\n### D53 ")])` = **`4de9f5642c8eb4ce497478380635f1f6e165d5216690d85c1974ea7a0b845ede`**, **532,623
bytes** (byte count matches AC-P30-07-PIN's figure; character count is 528,776). All three literals carry that value
(the two `PROTECTED_SPAN_SHA256` assignments and the `expected` in `test_p28_t14_pin_matches_live_span`). The diff
touches literals and comments only; boundaries, the span-extraction expressions and the exact-equality comparison are
unchanged, and `test_p28_t14_repin_is_pin_only` (green) forbids the containment/`startswith` relaxations. Each audit
comment names the 2026-11-20 RG-P7-1 / RG-P7-2 / RG-D23-1 closure and says pyqtgraph's **name survives in the span as
decision lineage** — truthful: I measured **36** `pyqtgraph` occurrences inside the span, so the comment neither
claims absence nor sanitises history.

## 7. Requirements edits (analyst, owner-approved) — **verified, with one wording finding**

- **Shipped facts check out.** `pyqtgraph` is not installed (`.venv` `find_spec` → `None`) and absent from
  `requirements.txt`; `PyQt6-WebEngine==6.11.0` is pinned; the vendored tree is `chart_assets/lwc/VERSION` = 5.2.1;
  no `ui/ services/ data/ ibkr/` module imports pyqtgraph. So "LWC only, vendored, in-page behind the
  `QWebChannel` bridge, pyqtgraph not installed/imported/selected/retained" is accurate.
- **The three neighbouring corrections are mutually consistent** and consistent with the tree: the Problem
  Statement parenthetical (now "PyQt6, `ibapi`, in-page LWC — no pyqtgraph"), the marker-adjacent preamble sentence,
  and the Constraints → *Observed from repository* UI row; the dated D47 line now carries an explicit
  "superseded 2026-10-27 by P6-T13 — retained as decision lineage" marker rather than quietly contradicting the new
  record. No new inaccuracy in those three.
- **No criterion touched:** the diff changes the baseline note, the Problem Statement, the preamble, Current Tech
  Stack and the Constraints/observed rows only — no `AC-*`, Journey, A/R line and no phase status. D1–P29 remain
  unopened apart from the declared labels.
- **One wording finding** — AC-D104.3's literal "Current Tech Stack are unchanged" clause and one residual P16 line
  still asserting RG-P7-1 open — see ESC-141.

## Findings (all routed; none blocking)

| id | route | severity | task | finding |
|---|---|---|---|---|
| **ESC-140** | PLAN | should-fix | P30-T4 | `docs/codebase-map.md:690` states "no existing suite is edited / no existing case is re-baselined", and `tests/test_p30_fence.py:615` pins that sentence — false at the end state: T6 rewrote `tests/test_d64_batch_gate.py`'s DG116 leg (+2 cases) and T7 edited `tests/test_p14_cache_guard.py` + `tests/test_p15_surfacing.py`. The note also still says the six suites are "planned, not yet on disk". |
| **ESC-141** | REQUIREMENTS | nice-to-have | P30-T3 | AC-D104.3 says the Current Tech Stack is "unchanged", but the owner-approved RG-P7-2 correction changed it in the same phase (the fence checks presence only, and T7's re-pin authorises the movement); `requirements.md:6045` still says "RG-P7-1 stays open"; the T7 comment's "marker sentence was restated" is imprecise (the marker sentence is byte-identical). |
| **ESC-142** | BUILD | nice-to-have | P30-T3 | `memory_bytes`' docstring still calls the bridge replay log "the one structure that grows with traffic", contradicting D104's own rationale (the five channel logs grow with traffic) and AR-P30-6. Bucket set stays untouched. |
| **ESC-143** | TASK_MANAGER | nice-to-have | P30-T1 | The restored control cluster is user-visible but `usage.md` documents no cluster and no chart pan/zoom affordance (precheck candidate, `touched: false`); no P30 task owns the guide and the phase allowlist excludes it. |

## Standing duties

- **Mock-endpoint containment (B.6):** clean. No `mock` / `fake` / `stub` / `simulat` crossed with
  `endpoint|client|service|server|api|harness` anywhere in the production diff (`ui/`, `services/`, `data/`,
  `ibkr/`, `chart.js`, `interaction.js`, `chart.html`). Every hit is inside `chart_assets/lwc/controls.test.js`
  (the node harness). No production module imports a test fake.
- **G7:** owner-run and never claimed. No P30 suite starts a `QWebEngineView`/`QWebEnginePage`, and none asserts a
  painted page or a Chromium click; the phase fence records the boundary and `tests/test_d101_control_cluster.py`'s
  docstring repeats it. The cluster's rendered placement is therefore owner-verified, not asserted here.
- **No new module / dependency / migration / settings key:** the only new files are four pytest suites and two node
  suites; `requirements.txt`, the schema, `QSettings` keys and `ENVELOPE_VERSION` are untouched.
- **D1–P29:** unopened apart from the declared record labels (see §7). The seven `pyqtgraph` present-tense claims
  removed are the pre-existing prose defects D104 targets, not history rewrites; the marked-history lines and all
  negative assertions survive.
- **Precheck fail_fast:** all four are the known committed-file false positive (§0); no `PRE-*` escalation exists.

## Escalation close-out

Nothing to close: `escalations.json` had **134 entries, all `addressed`, zero open** before this pass, and
`precheck.json`'s `escalation_updates` is empty. The four entries added by this pass (ESC-140…143) are new and open.

**Verdict:** all seven tasks meet their acceptance criteria on the live tree; the full suite passes; the four
findings are record/consistency gaps (one should-fix PLAN, three nice-to-have) that do not invalidate the shipped
behaviour. The Orchestrator should summarise the open escalations to the user before closing the fold-in.

Status: REVIEW_COMPLETE
