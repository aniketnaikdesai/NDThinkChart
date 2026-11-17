# Code Review — Phase P6 (D47: pyqtgraph → Lightweight Charts)

**Reviewer:** Orchestrator acting as Code Reviewer (the delegated pass was cancelled twice at the owner's request).
**Date:** 2026-10-27
**Scope:** waves `P6-T01`…`P6-T12` and the hotfix trail `Q-1`…`Q-17`. **`P6-T13` (pyqtgraph deletion) is gated on owner approval + one clean live session and was deliberately not dispatched — not counted as unfinished work.**
**Inputs:** `test_verification.json` (pass, exit 0, 116.8 s), `precheck.json` (11 tasks, 2 entries), the committed tree at `2361c07`.

---

## Verdict

The migration is real and the parity book is honest, but the batch has one structural weakness that produced every one of today's live failures: **failures are silent**. A host that cannot start, a page that throws, and a bridge that never connects all render the same blank canvas with no message, no log and no failing test. Four independent defects each shipped green because of it.

No blocking code defect was found in the delivered state. Five findings follow: one `should-fix` (silent failure), three `nice-to-have` (JS console capture, text-level residue scans, a malformed result record), and one process note for the Task Manager.

---

## What I verified, and how

**1. The four black-chart causes each have a fix at the root.**

| Cause | Fix | Pinned by |
|---|---|---|
| `ndt://` registered after `QApplication` | `main.py` registers at module import, before the app exists | `tests/test_lwc_host_bootstrap.py` — 3 cases incl. an AST ordering assertion |
| `QWebEngineProfile` imported from `QtWebEngineWidgets` | imported from `QtWebEngineCore` | `tests/test_lwc_bridge_handshake.py` constructs the host for real, so a wrong import fails it |
| v4 series API on the vendored 5.2.1 tree | v5-primary `addSeries` with a v4 fallback | **indirect but sound** — `init()` calls `bindChannel()` at its end (chart.js:349), so a throw in `init` leaves `window.lwBridge` undefined and the handshake test fails |
| no `QWebChannel` set on the page | channel built, bridge registered as `lwBridge`, set before every load, strong reference, re-attached on renderer restart | `tests/test_lwc_bridge_handshake.py` (offscreen, no display needed) |

The third row is the one I checked hardest: it is caught *indirectly*, because the bridge binding is the last thing `init()` does. That is acceptable but fragile — a future reorder that binds the channel earlier would silently drop the only offscreen coverage of the page's series API. Recorded as context, not a finding, since it is currently sound.

**2. The parity book is honest.** Rows 1, 2, 4, 5 and 18 were flipped by Q-8 and row 3 by Q-9, each naming the passing test that proves it; rows 1/2/4/5 map to the time-parity suites and row 18 to the real-engine interceptor plus host/recovery cases. Row 3's volume ceiling is the one I checked against the reference rather than the prose: `chart.js` implements `visibleMax > 0 ? 1.10 × visibleMax : 100` with `minValue: 0`, which matches `chart_model.visible_volume_ceiling` / ESC-028 — the naive `max(1.1m, 100)` would have inflated a 10-lot bar to 100, and Q-9 avoided it. 19/19 is supported.

**3. The pacing fixes compose.** Q-2 (1 s interval), Q-3 (defer rather than skip priming), Q-12 (the retry looped because `_on_prime_retry` omitted `retrying=True`) and Q-17 (the wave stalled 1 ms short of the gate and printed "0s"). The final state makes the reported wait authoritative (interval + 50 ms, capped, never shortening the 600 s budget), schedules with `ceil + 50 ms`, retries a near-zero residual on a 50 ms tick, and — this is the part that matters — `tests/test_backfill_progress.py` asserts **N plans issue N requests** over a live event loop, which is the property all three earlier attempts lacked. That test fails against the previous code (9 attempts for 4 chunks).

**4. Containment holds.** Lightweight Charts 5.2.1 vendored with its licence and attribution; the request interceptor is deny-default and Q-7 replaced the ordering assumption with a property assertion (ndt page allowed, every non-ndt URL blocked, none ever permitted); no CDN or npm in the runtime path; JS receives timestamps, prices and fractional indices only, never SQL or persistence.

**5. No scan was weakened to make a fix land.** Four guards were edited across the phase — the parity open-count (made derived rather than literal), the stdlib allowlist (now `sys.stdlib_module_names`), the `session_service` token (removed because P6-10 legitimately consumes it), and the `pyqtgraph` word (see ESC-072). Each was widened to admit a *legitimate* input, not to hide a violation; I re-read the assertions and none lost its ability to fail.

---

## Findings

| id | route | sev | finding |
|---|---|---|---|
| **ESC-070** | BUILD | **should-fix** | **A failed engine start is silent** — `main_window.py:354-359` swallows `ensure_host()`'s exception into `None`, so a blank canvas is indistinguishable from an empty chart. Log it and surface it. |
| ESC-071 | BUILD | nice-to-have | No `javaScriptConsoleMessage` override: page-level JS errors never reach Python, so today's "qt is not defined" and the v4/v5 throw were visible only in the terminal. |
| ESC-072 | BUILD | nice-to-have | Five residue scans forbid the literal word `pyqtgraph` in `ui/lwc_view.py`, so P6-T11 reworded a docstring. Assert the property (no import/instantiation), not the word. |
| ESC-073 | BUILD | nice-to-have | `P6-T03`'s result carries no `task_id` (PRE-001) — a malformed record, not a code defect. |
| ESC-074 | TASK_MANAGER | nice-to-have | Commit history no longer matches the wave structure: 17 quick tasks landed between waves and wave commits were folded (1df6668, aad8285). Decide and record the rule. |

---

## Judgement

The four live failures were not caused by the library. They were caused by betting a renderer swap on a stack whose failures are invisible: no host, no channel, wrong import, wrong API all look identical from the outside. The code that fixes them is now correct and, for three of the four, provably so offscreen.

Two things I would insist on before `P6-T13` deletes pyqtgraph: **ESC-070** (so the next failure is not another silent black screen), and the owner's one clean live session — because every check that has ever caught these defects was either run by the owner or run on a real display, never by CI.

Status: REVIEW_COMPLETE

---

# Ad-hoc investigation — 2026-10-27 (owner-reported, not a scoped phase pass)

Scope: the owner's live defect report — "1 min chart won't plot beyond 10/15 and error message … I
don't know if they are limited." Full write-up: `docs/code_review/one_min_backfill_starvation.md`.
Tier: **full** (live-defect diagnosis; no precheck slice involved).

## What was observed (verified first-hand)

* Production DB (`~/Library/Application Support/NDThinkChart/charting_app.sqlite3`, read-only):
  `SPY 1 min ext_hours=1` = **601 bars, 2026-10-15 04:00 → 2026-10-15 14:00 ET**, nothing newer;
  `SPY 5 mins` = current through 2026-10-26 19:55. So the right edge of the 1-min chart *is* 10/15 —
  a data-starved series, not a renderer defect, and **not** a market-data permission limit.
* ONE 1-min load plans **42** historical requests (43 cold) vs 9 (5 mins/15 mins), 5 (1 hour),
  2 (4 hours) — measured with the real planner against that cache.
* Driven through the real `TickerSession` + `PacingManager` with a fake transport: the 42 requests issue
  1.04–1.10 s apart, the wave completes at **t+44.7 s**, spending **42 of the app's 50 per 600 s** slots.
* With 9 slots already spent, a fresh 42-chunk load is 1 short and must wait **~590 s** for the oldest
  slot to expire.

## Findings

| id | task | route | category | root cause | sev | finding |
|---|---|---|---|---|---|---|
| **ESC-075** | — | BUILD | bug | code_bug | **blocking** | **The 1-min cache can never advance.** Bars are only saved/rendered when the whole 42-chunk wave finishes (`ui/main_window.py:2039-2073`, `ui/ticker_session.py:953-956`), and every `load_chart` cancels the wave and sets `_pending_bars = []` (`main_window.py:1705-1712` → `ticker_session.py:833-842`), while cancelled requests are never refunded against the 50/600 s budget (`ibkr/market_data.py:63-64`). One attempt = 86 % of the budget + 45 s of silence; any retry discards the attempt and leaves the budget short. |
| ESC-076 | — | BUILD | bug | code_bug | should-fix | The owner's nine `162 … API historical data query cancelled` lines are our own mass cancel on reload — one per in-flight reqId (`ticker_session.py:833-842`) — surfaced as user-facing errors (`main_window.py:1668`) and paid for twice against the budget. Coalesce same-target reloads; treat a cancel-acknowledged 162 as expected. |
| ESC-077 | — | BUILD | bug | code_bug | should-fix | Watchdog 120 s (`ticker_session.py:144`) is shorter than a legitimate budget deferral (up to ~600 s): `_schedule_wave_continuation` re-arms it while scheduling a longer timer, so a waiting wave is "stranded", mass-cancelled, and later resurrects for a second finalise. |
| ESC-078 | — | BUILD | quality | code_bug | nice-to-have | `Aggregator priming pacing-limited` is structural: the prime is issued after the wave's first chunk, shares the single 1 s interval gate, and its one retry races the wave's continuation — so D27.9 priming is silently skipped on cold loads. |
| ESC-079 | — | PLAN | gap | bad_architecture_decision | should-fix | No artifact bounds what one load may cost: AC-D16.8's 30-session floor × `1 D` chunks for `1 min` = ~42 requests against a 50/600 s budget shared by every session/pop-out/prime. State the budget invariant (per-load cap; floor filled across loads) instead of patching per timeframe. |

## Judgement

The three pacing fixes from Q-2/Q-3/Q-12/Q-17 are all present and correct in isolation, and
`tests/test_backfill_progress.py` genuinely pins "N plans issue N requests". What no test pins is **how
many plans a 1-min load produces**, nor that an interrupted wave must not lose fetched bars — which is
why the suite is green while the live chart has been frozen at 10/15 for eleven days. ESC-075 is the
owner-visible defect and it needs the *invariant* test ("at most N requests per load; an interrupted wave
leaves the cache no smaller than before it started"), not another timing tweak. ESC-079 exists so the
same invariant is stated upstream rather than re-derived per timeframe.

Status: REVIEW_COMPLETE

# Dated addendum — P6-T13 executed (2026-10-28; appended, nothing above rewritten) / The scope sentence at the top of this log (P6-T13 was deliberately not dispatched) and the ESC-070 close-out condition (before P6-T13 deletes pyqtgraph) describe the review-time state and are superseded by the outcome below — preserved as the reviewers contemporaneous record. / - Executed 2026-10-27 as removal commit 6e35b27 (owner-approved). ui/chart_panel.py, ui/candlestick_item.py, the pyqtgraph overlay/control/router-companion modules and the ui/overlays/ contents are deleted; the tree is LWC-only behind ui/chart_view.py::create_chart_view. / - Gate disposition (record: docs/build/gate_P6_T13.md): owner approval SATISFIED; the one-clean-live-session sign-off (AC-D47.8/S59) WAIVED, NOT SATISFIED; oracle decision RETIRE. / - Matrix state after T13: feature-parity rows 1–18 stay Done/accepted; row 19 Retired — see the P6-T13 as-built note in docs/lwc_parity_matrix.md. / - Still owed downstream: ESC-070 remains open work; the owners one clean live session is still owed as live validation; ESC-075…ESC-079 feed P7 with the AC-D16.8 restatement open as Analyst debt. / Status: REVIEW_COMPLETE (addendum appended 2026-10-28)
