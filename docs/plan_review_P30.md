# Plan review — Phase P30 (UI surface integrity, D101–D104) — retry 1 of 3

Plan-Section-SHA256: 8a8798be55ff5ee88a8fce97a92dcf434013411554a89550bcff822a4aed5ce9
Architecture-Section-SHA256: 6deb3e5ca70b0276f066d633a40fb57ac9737ac7d6ef978b6b25cb3d73513d1a

- **Pass type:** `retry_1_of_3` — targeted re-validation of the four Required Changes, plus a ripple check on what the revision touched, plus re-confirmation that the accepted judgements are undisturbed.
- **Phase gate:** **OPEN** (P29 `REVIEW_COMPLETE` over a terminal build log; no provisional review exists → this is the final pass).
- **Lint:** `plan_lint.py --phase P30` → PASS, 0 failures, 0 warnings (re-run after this pass's activation edits, so the stamp above is the linted text).
- **Revision notes present** at `docs/plan.md:8939-8968` and `docs/architecture.md` § Revision notes — all four RCs named and addressed.

## Review Status

**Status: APPROVED** — all four Required Changes are correctly and completely fixed; the arithmetic of the D104 enumeration checks out exactly against the tree; no accepted judgement was disturbed; no new defect was introduced. `docs/plan.md` § P30 is activated to `Status: READY_FOR_TASK_MANAGER`.

## Required Changes — verified closed

- **RC1 (D104 sweep allow-list) — CLOSED.** I re-enumerated the tree myself over `ui/`, `services/`, `data/`, `ibkr/`: **20 hits in 12 files**, exactly as claimed. Allow-listed **12** — 8 negative assertions (`ui/dock_layout.py:7`, `ui/lwc_view.py:2002`, `time_collapse_service.py:33`, `market_calendar.py:17`, `backfill_service.py:44`, `option_ladder.py:43`, `option_spread_engine.py:98`, `chart_model.py:11`) and 4 marked-history (`ui/chart_view.py:8`, `:12`, `ui/drawing_tools.py:3`, `chart_model.py:41`); must-disappear **8** — the 7 in `ui/main_window.py` (`:15,:305,:308`) / `ui/popout_window.py` (`:10,:64,:75,:96`) plus `services/chart_model.py:273`. 12 + 8 = 20 ✓. Every allow-listed fragment is genuinely a negative assertion or marked history — I checked each against its line. `chart_model.py:273` does assert a present item whose stated bound has passed ("the pyqtgraph item **keeps** its identical local copy **until P6-13**", and P6-13 shipped), so rewriting it to past tense instead of allow-listing is the right call and is now a deliverable with a positive assertion that the fragment is gone. **No hit is unclassified.** One literal imprecision remained (the `:41` fragment spanned a line break, so a per-line match would miss it) — corrected at activation, see *Editorial corrections* E2.
- **RC2 (`FI-P30-1` / deliverable 8(g)) — CLOSED.** The new case and the FI now say the precise thing the code does: with `getVisibleLogicalRange()` → `null`, `controlPressed` skips `zoom()` (the only guarded step) and still runs the unconditional report, and `handle_control`'s zoom branch sets `refused = False` — so "no viewport change, no `zoomRefused`, one report, `{"op":"zoom","step":±1}` with `refused: false`" is literally true. Buildable with the suite's own fake (the test owns the fake range, and non-toggle controls send `value: null` — `interaction.js::mountControls`).
- **RC3 (map suite count) — CLOSED.** The note now reads "**six** new suites … its **two** new `chart_assets/lwc/` node suites", names both (`interaction.controls.test.js`, `controls.test.js`), carries the `services/chart_model.py` row, and its stale-cells paragraph correctly counts the seven `ui/` files plus `chart_model` = **eight**.
- **RC4 (node mount needs a document) — CLOSED.** Deliverable 9(a) now requires `globalThis.document` to be defined before `interaction.js` is required, with the reason stated (`mountControls` returns `[]` when `typeof document === "undefined"` — matches the shipped guard at `interaction.js:314`), so the negative case removes a genuinely mounted button.

## New `touches_files` member — `services/chart_model.py`

The three places agree: P30-03 **Files** (`one docstring sentence`, comment-only), P30-03's diff allowlist (`… + services/chart_model.py + …`), and P30-04's recorded `git diff --name-only 3b92ce6` set. The change is docstring-only and fenced: P30-03's `Do not` forbids touching any function, signature or import there, and nothing pins `heikin_ashi`'s docstring text (no test asserts it; `tests/test_chart_model.py` exercises the recurrence only), while `ui/lwc_view.py:149` imports the module — so an import-level break would already redden the listed suites. The architecture was updated in step: the fourth rule bullet, the Codebase Summary row, System Components, the **not frozen** list and S-P30-5 all carry the seventh site, and `services/chart_model.py` appears under *not frozen*, never under Frozen Interfaces.

## Accepted judgements — undisturbed

- **The press seam (S-P30-1):** unchanged — page-local viewport action via the keyboard's own `zoom()`/`fitAndFollow()`, one reported intent, only `router_mode` returning; no consumer added for `zoom`/`reset_view`; `handle_control`'s shipped docstring still the warrant ("zoom in/out are pure view intents the page applies to its own time scale").
- **Q118 = RESTORE:** restoration built (container, idempotent mount, page→Qt slot, `CONTROL_IDS` from `CONTROL_SPECS`), delete arm still recorded declined, `AC-D101.2` still in scope with both starting states plus the TR-9 refusal on the Python side.
- **G7:** still owner-run and claimed nowhere (`tests/test_lwc_render_smoke.py`'s measured note is the basis); no new case paints.
- **D102 + D103:** still one wave, still two rules (S-P30-3 dismiss / S-P30-4 restore-by-identity), two test classes, no shared fixture.
- **D104 per-site split:** intact — seven wording sites (code right) and the one release site (code wrong) where `release_resources` clears `_channel_logs` + `_channel_queue`, with `memory_bytes` recorded as a named residual (AR-P30-6 / AP-P30-8). The revision widened the wording set; it did not move the release decision.
- **`FI-P30-1`'s reading of Journey 82 step 5:** unchanged in substance — TR-9 is the only refusal, no data-limit refusal is invented, and the FI now additionally states what a no-range press actually does.
- **Shape:** four waves `P30-01 ∥ P30-02 → P30-03 → P30-04`; six new suites (four `tests/`, two `chart_assets/lwc/`); sizes M/S/S/S; no new module, dependency, migration, settings key, envelope bump or order path.

## Editorial corrections applied at activation (disclosed)

No architectural decision, no added obligation; each is a count or a literal brought into line with what Plan itself wrote elsewhere.

- **E1** — `plan.md` traceability, `AC-D104.1` row: "the four sites" → **"the seven wording sites + the release"** (the wave body lists seven; architecture S-P30-5 says seven).
- **E2** — `plan.md` P30-03 allow-list, `services/chart_model.py:41` row: the fragment ran past the end of the line (the sentence continues at `:42`), so a per-line match would have missed it. Fragment truncated to the line's own text (`Moved here from ``ui/candlestick_item`` when the pyqtgraph engine was`) with a note that the sentence continues on the next line. Class and file unchanged.
- **E3** — `plan.md` companion header: `AR-P30-1…10` → **`AR-P30-1…11`** (eleven risks are written).
- **E4** — `architecture.md` S-P30-5 rationale: "six of the seven wording sites were stale prose… (and the seventh …)" → **"all seven wording sites were stale prose over correct code"**, with the release site named separately; the old sentence implied the seventh was not stale prose, which contradicts the same sentence's own account of it.

## Validation steps (short form)

- **Requirements coverage — PASS.** Every `AC-D101.1`–`AC-D104.3`, Journeys 82–85 and A246–A250 mapped to a wave; `AC-D104.1`'s mechanism now covers the whole scanned tree by construction.
- **Architecture completeness — PASS** (unchanged except the seventh D104 site, which is now present in every section that enumerates sites).
- **Architecture consistency — PASS.** Plan and architecture agree on 20/12/12/8, on seven wording sites, and on the release decision.
- **Plan quality — PASS.** Four coarse waves, no task-level breakdown, exit conditions offscreen and diff-fenced.
- **Task Manager readiness — PASS.** No wave requires a decision only Plan may make; the amended sweep and the new case are implementable as written.
- **Existing-repo compliance — PASS** (marker + Current Tech Stack present; stack respected; labels present; additive-only; summary consistent).
- **Frozen Interfaces — PASS.** Re-checked: the eight entries are `[existing]`, verbatim, and unchanged by the revision; `services/chart_model.py` is listed only under *not frozen*; nothing under construction is frozen.
- **Codebase Map — PASS.** Modules resolve, key files exist, nine `[changed in P30]` rows (the new `chart_model` row included), six suites, stale-cells paragraph consistent at eight files.
- **Pending doc sync — PASS.** `docs/pending_doc_sync.md` absent.

## Advisory (non-blocking, no action required before the build)

`P30-03`'s exit-condition suite list does not name `tests/test_chart_model.py` even though the wave now edits `services/chart_model.py`; the map's generated test-impact row does point there. It cannot hide a break: no test pins the changed docstring, `ui/lwc_view.py` imports the module so the listed suites already exercise the import path, and P30-04's exit runs the full offscreen suite. Adding it on a later touch is optional.

## Final Decision

**Status: APPROVED.** `docs/plan.md` § P30 now carries `Status: READY_FOR_TASK_MANAGER`; Task Manager may proceed. The four waves, the frozen contracts and the file fences are as reviewed.
