# D55 Fact Sheet — source-cited reconciliation (D55.2 / AC-D55.2)

> Status: record of Phase P16-W1. Every fact carries one verifiable source
> citation. Anything the source does not decide stays explicitly open with
> its decider named — nothing is guessed in prose. P6-T13 references preserve
> the gate disposition verbatim: waived, not satisfied (never paraphrased as
> satisfied).

## 1. LWC-only engine status

| # | Fact | Source citation |
|---|---|---|
| F1 | `create_chart_view` always returns the LWC view; `NDT_CHART_ENGINE` / `chart/engine` no longer select a renderer. The stack is LWC-only. | `ui/chart_view.py:121-125` — `def create_chart_view(tz_offset: float = 0.0, editable: bool = True) -> ChartView:` returns `LwcChartView(...)`; module docstring lines 15-17 confirm no renderer switch remains. |
| F2 | pyqtgraph removal executed 2026-10-27 under explicit owner approval (SATISFIED) with the live-session sign-off recorded as waived, not satisfied. Returning to pyqtgraph is a `git revert` of the removal commit, not a runtime switch. | `docs/build/gate_P6_T13.md:5-21` — §1 approval SATISFIED (owner "ok delete pyqtgraph", 2026-10-27); §2 live-session sign-off **WAIVED, NOT SATISFIED**, i.e. waived, not satisfied — "no claim is made that the engine was validated against live TWS". |
| F3 | Removal commit is `6e35b27`; the oracle (value-for-value pyqtgraph comparison suites) was retired by owner choice (RETIRE), not frozen. LWC keeps only tests that stand on their own. | `docs/lwc_parity_matrix.md:52-67` (P6-T13 as-built: removal commit `6e35b27`, gate approval SATISFIED 2026-10-27, live-session sign-off **WAIVED, NOT SATISFIED** — waived, not satisfied preserved; oracle RETIRE) + `docs/build/gate_P6_T13.md:29-41` (§3 oracle decision RETIRE). |
| F4 | Parity rows 1–18 remain Done / accepted after the deletion; row 19 (pyqtgraph present + default retention) is Retired (retention moot, nothing retained). The deletion does not un-prove what LWC was proven to do. | `docs/lwc_parity_matrix.md:59-67` (feature parity unchanged; cutover/deletion retired; "no row in this matrix claims a live session validated the engine" — waived, not satisfied preserved). |

## 2. Connection truth — live-only per answered Q85

| # | Fact | Source citation |
|---|---|---|
| F5 | Connection endpoint is fixed: `IBKR_HOST 127.0.0.1`, `IBKR_PORT 7496`, `IBKR_CLIENT_ID 1`; the only trade port is `LIVE_PORT 7496` (TWS live; 7497 is paper). `check_live_port()` fail-fasts on any non-live port. | `config/settings.py:3-24` — `IBKR_HOST`/`IBKR_PORT`/`IBKR_CLIENT_ID` defaults + `LIVE_PORT = 7496` + `check_live_port()` refusing to start unless `IBKR_PORT == LIVE_PORT`. |
| F6 | Account mode is live-only per answered Q85: the app trades live only; any paper-on-7496 prose is a contradiction corrected in P16-W2. This sheet states live-only and invents no paper path. | `config/settings.py:20-24` (`Refusing to start ... NDThinkChart trades live only`) as source truth for the live-only stack; mode decided by answered Q85 (owner answer, 2026-11-04) — the guide correction follows this fact sheet, never precedes it. |

## 3. P7 cap as a per-load maximum (requirement vs plan separation)

| # | Fact | Source citation |
|---|---|---|
| F7 | The P7 cap is a per-load **maximum, never a target**. The maximum reading lives in the W3 addendum; the approved P7 record itself stays byte-identical. | Approved P7 plan text (`docs/plan.md` § Phase P7) as authority, cited via `docs/architecture.md` § Phase P16 Frozen Interfaces ("P7 per-load cap plan text (approved) — *maximum, never a target* reading lives in the W3 addendum; the approved P7 record itself is byte-identical"). The three plan examples are in that approved plan text and are referenced here, not restated, so this sheet cannot drift from them. |
| F8 | Per-load means coalesced/cancel-refund accounting: the load that counts against the cap is the coalesced per-load request set after cancel-refunds, not every issued call. | `docs/architecture.md` § Phase P16 Codebase Summary + `docs/plan.md` § Phase P16 P16-W1 deliverables ("per-load (coalesced/cancel-refund) definition") as the definition authority; pacing source `config/settings.py:29-44` (`MAX_HISTORICAL_PER_600S = 100` rolling-600s budget comment + `HISTORICAL_MIN_INTERVAL_S = 0.5` cancel/succession comment) as the enforcing code both deciders reconcile against. |
| F9 | `AC-D16.8` requirement text (the owner-required intraday depth floor) is referenced, never restated (RG-P7-1 stays Analyst debt). The floor is distinct from the P7 plan's per-request IBKR caps: the floor's single tunable is `MIN_INTRADAY_SESSIONS`; the per-request caps chain requests (S17). Requirement-vs-plan-interpretation separation holds. | `config/settings.py:52-58` (`MIN_INTRADAY_SESSIONS = 30` comment: floor's single tunable; `ibkr/market_data.py::TIMEFRAME_CONFIG` durations deliberately NOT changed — per-request caps, depth from chaining) + owning requirement `docs/requirements/requirements.md` (AC-D16.8 text referenced, not restated). |

## 4. Spike stub labelling — runtime evidence kept separate

| # | Fact | Source citation |
|---|---|---|
| F10 | The `spikes/lwc/` probe is a labelled stub / call-shape throwaway: never imported by production, never a parity proof. What is proven (renderer paints — 7 pixel-level assertions on a real display; bridge handshake works; full suite green with the engine installed) is runtime evidence recorded separately, not spike output. | `docs/lwc_parity_matrix.md:660-683` (P6-04: vendored lightweight-charts v5.2.1 tree via `ndt://lwc/`, `LwBridge` batched ops, offline/interceptor evidence) as the runtime-evidence side + `docs/build/gate_P6_T13.md:21` ("What has been proven is: the renderer paints (7 pixel-level assertions on a real display), the bridge handshake works, and the full suite is green") kept distinct from the never-imported spike per A155. |
| F11 | Vendored runtime is v5.2.1 (14 files) shipped in both specs' `datas`; the Chromium/QtWebEngine term is measured separately (≈292 MB frameworks on disk, packed contribution unmeasured until a build). No fixed size budget is set. | `docs/lwc_parity_matrix.md:208-252` (P6-12 bundle wiring + measured delta + signing disposition, Q61/A109 measure-first). |

## 5. P7/P8 approval-vs-built dating

| # | Fact | Source citation |
|---|---|---|
| F12 | **P7 BUILT** (data-path batch): feature commit `7cba534`, 2026-10-28. **P8 BUILT** (D48 weekly/monthly timeframes): feature commit `09761fb`, 2026-10-28. Neither date is an approval date; approvals live in the review/task-graph records linked from the changelog. | `docs/codebase-map.md:9-15` (header: P7 BUILT feature commit `7cba534` 2026-10-28; P8 BUILT feature commit `09761fb` 2026-10-28; detail in `docs/phase-changelog.md` Phase P6/P7/P8 + `docs/lwc_parity_matrix.md`). |
| F13 | As-built outcomes (P6/T13 + P7 + P8) are indexed in `docs/phase-changelog.md` (Phase P6/P7/P8) with the removal gate and parity-vs-cutover separation; `docs/CHANGELOG.md` carries the concise index/pointer. Approval records are never reworded — deltas land as dated addenda. | `docs/codebase-map.md:113` + `docs/architecture.md` § Phase P16 S-P16-3 (six-file reconciliation + addenda-only rule; approvals byte-identical). |

## 6. Explicitly open items (source does not decide — never guessed)

| # | Fact | Status + decider |
|---|---|---|
| O1 | **50-vs-100 figures: explicitly open.** The source pair that decides is `config/settings.py` (pacing constants) plus the P7 assertions; until reconciled against both, this sheet picks no value in prose. | Status: explicitly open. Decider: `config/settings.py` (`MAX_REQ_PER_SEC = 50`, `MAX_HISTORICAL_PER_600S = 100` with owner-set comments at lines 29-36) + P7 assertions, per A154/DG102. Reconciliation-or-explicit-open is W3 work; W1 records openness only. |
| O2 | Any further fact the cited sources do not decide: explicitly open with owner/source named, never silently chosen. | Status: explicitly open by rule. Decider: named per row at reconciliation time (source file + assertion, or owner Q&A). |

## Cross-check notes (for the T21/T22 reviewer)

- T21: for each F-row above, open the cited `path:lines` and confirm the claim. Grep this sheet for `waived, not satisfied` (lowercase, this line and F2/F3/F4 rows) and confirm zero bare "satisfied" T13 paraphrases: every T13 reference carries the waived-not-satisfied distinction verbatim.
- T22: O1 names its decider (`config/settings.py` + P7 assertions, A154/DG102) and records explicitly open without choosing a value in prose; no other row silently chooses an undecided value.
