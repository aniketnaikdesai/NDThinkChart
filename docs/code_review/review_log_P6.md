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
