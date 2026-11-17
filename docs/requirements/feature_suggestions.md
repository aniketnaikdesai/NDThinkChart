# Feature Suggestions

> Owned by Requirements Analyst. These are analyst-authored ideas noticed during
> discovery that the user did **not** request. They are **not in scope** until the
> user explicitly approves an entry. Priority is a suggestion only.

## FS1 — Keyboard shortcuts for zoom (`⌘+`, `⌘−`, `⌘0`)
- **Gap/opportunity:** D3 adds zoom buttons; power users expect keyboard access.
- **Why not in the original ask:** The user asked only for on-chart `+`/`−`,
  magnifier, and reset.
- **Suggested priority:** low

## FS2 — Double-click chart to reset zoom
- **Gap/opportunity:** A fast, discoverable way to return to the default framing.
- **Why not in the original ask:** Reset via the dedicated button already satisfies
  the request.
- **Suggested priority:** low

## FS3 — Persist zoom/view range per symbol + timeframe
- **Gap/opportunity:** Re-loading a chart currently resets the framing; users often
  return to the same view.
- **Why not in the original ask:** Not mentioned in D3.
- **Suggested priority:** medium

## FS4 — Legend / tooltip explaining session shading colours
- **Gap/opportunity:** Pre/post bands are unlabelled; a small legend would make the
  colours self-explanatory.
- **Why not in the original ask:** The user only asked for the bands.
- **Suggested priority:** low

## FS5 — Futures-specific session shading
- **Gap/opportunity:** Avoids the mis-shading flagged in `design_gaps.md` DG1.
- **Why not in the original ask:** Accepted default applies equity sessions for now.
- **Suggested priority:** medium


## FS6 — User-selectable date range / window for the chart
- **Gap/opportunity:** The chart auto-frames all cached bars with no date-range control
  (see `design_gaps.md` DG20). A range picker would let users request a specific window and
  make long backfills explicit.
- **Why not in the original ask:** D16 asks only that existing history stop showing holes.
- **Suggested priority:** medium

## FS7 — Compress/collapse non-trading time (weekends, holidays, overnight) — **PROMOTED to D21.4 (2026-10-06)**
- **Gap/opportunity:** D16 left genuine closures as empty spans (`AC-D16.3`). Some
  terminals collapse them to reduce dead space.
- **Why not in the original ask:** The user's complaint was missing *trading* data, not the
  weekend gap; compressing time is a separate x-axis design change.
- **Status:** **PROMOTED — now in scope** as defect **D21.4** (the user explicitly requested
  collapsing empty space when the market is not open / when RTH is selected, 2026-10-06). It
  **supersedes the display part of `AC-D16.3`**. See `requirements.md` D21.4 / Journey 23 and
  `open_questions.md` B9 (answered 2026-10-06: collapse between-session gaps on intraday timeframes only; `1 day` no-op).


## FS8 — "Add current chart symbol to watchlist" (toolbar/shortcut)
- **Gap/opportunity:** D22 adds an in-app add-symbol affordance on the watchlist. A common flow is "I am looking at
  MSFT on the chart; add it to my watchlist" — a one-click "Add to watchlist" from the toolbar (or a keyboard
  shortcut) reusing the D22 add path would avoid retyping the symbol.
- **Why not in the original ask:** The user asked only for a way to add tickers to the watchlist; the chart-symbol
  shortcut is a convenience not requested.
- **Suggested priority:** low

## FS9 — Watchlist import / export (CSV or text list)
- **Gap/opportunity:** D22 makes the watchlist editable in-app one symbol at a time. Importing/exporting a whole
  list would let users move watchlists between machines or seed a large list quickly.
- **Why not in the original ask:** The request is about adding a ticker in-app, not bulk list management.
- **Suggested priority:** low

## FS10 — Watchlist symbol reorder by drag-and-drop (only if B14 keeps reorder out of D22)
- **Gap/opportunity:** `watchlist.sort_order` already exists in the DB, but there is no in-app reorder. If B14
  scopes D22 to add-only (or add+remove), drag-and-drop reordering would be the natural follow-up.
- **Why not in the original ask:** The user asked about adding; reordering is a separate interaction.
- **Status (2026-10-07):** B14 answered **add + remove** — reorder is **out of scope**, so this remains a valid future suggestion (not part of D22).
- **Suggested priority:** medium

## FS11 — Show the company name in symbol-search results
- **Gap/opportunity:** D39's search box returns `symbol·secType·exchange` only; the Journey 34 as-built note
  records a reviewer-verified API limitation — `symbolSamples` (ibapi 10.51.1) carries `ContractDescription`
  with `contract` + `derivativeSecTypes` only, **no company name**. A short name would make the pick list far
  easier to scan.
- **Why not in the original ask:** the user asked for a symbol search; the missing company name is an API
  limitation, not a requested field.
- **Suggested priority:** low

## FS12 — A true per-bar historical volume profile (alternative to per-session tick fetches)
> **MOOT as of 2026-10-15 (D41):** D36 footprint is being removed, so this D36-sourcing suggestion no longer applies. Retained for history.
- **Gap/opportunity:** D36 removed the planned `reqHistogramData` path because the method takes **no date
  parameter** and cannot address individual bars (see `docs/architecture.md:218`), so footprint history is built
  from per-session TRADES tick pages. An alternative source (e.g. `reqHistoricalTicks` or a dedicated
  volume-profile endpoint, if ever offered) could fill prior bars more cheaply and reduce IBKR request pressure.
- **Why not in the original ask:** the user asked for footprint charts as they render today; the sourcing strategy
  is an implementation choice the analyst flagged, not a user requirement.
- **Suggested priority:** low

## FS13 — Label delayed (non-real-time) depth distinctly in the heatmap
> **MOOT as of 2026-10-15 (D41):** the D37 depth heatmap is being removed, so this suggestion no longer applies. Retained for history.
- **Gap/opportunity:** D37's Journey 32 as-built note records a known limitation — if a delayed-depth feed is
  used **instead of** error 354, the heatmap would render **unlabelled** as if real-time. A small "delayed"
  badge/tint would prevent a user mistaking stale depth for live depth.
- **Why not in the original ask:** the user asked for the heatmap; the 354-vs-delayed distinction is an edge the
  reviewer recorded in code, not a requested surface.
- **Suggested priority:** low

## FS15 — Persist live/aggregated bars to the cache
- **Gap/opportunity:** `BarCache.save_bars` is called only from the historical path
  (`ui/main_window.py::MainWindow._finalize_history_wave`), so bars aggregated from the real-time stream update
  the in-memory `_bars` but never reach SQLite. After a restart those bars are refetched rather than restored,
  and any span the app ran through but the historical window did not cover shows a hole until the load-time
  backfill re-requests it.
- **Why not in the original ask:** D16's scope was the *visible* historical hole, healed by load-time backfill;
  live-bar persistence was explicitly deferred ("out of D16's minimal scope") in `design_gaps.md` DG18.
- **Suggested priority:** low–medium (a periodic/on-close `save_bars` of the current session's bars is small and
  self-contained, and would trim some redundant historical traffic on restart).

## FS16 — Per-contract session boundaries for futures
- **Gap/opportunity:** `services/session_service.py` implements an **equity** RTH/ETH model (pre-market
  04:00–09:30 ET, post-market 16:00–20:00 ET). Futures trade nearly 24 hours with different session boundaries,
  so charting a futures symbol with session shading enabled produces mis-shaded bands.
- **Why not in the original ask:** DG1 was disposed as "keep the accepted default for this run"; a
  per-contract session map was explicitly deferred.
- **Suggested priority:** low (matters only when futures are charted with shading on).

## FS14 — Per-pop-out connection indicator
- **Gap/opportunity:** a pop-out opened while IBKR is disconnected renders cached bars but shows **no**
  per-window connection state — the only connecting affordance is the main window's `conn_badge`
  (`ui/main_window.py:295`). With up to 10 pop-outs on separate monitors, the user cannot tell from the
  pop-out whether its feed is live or the subscription is merely pending.
- **Why not in the original ask:** D24's requirement text explicitly records the shipped behaviour (no
  per-pop-out indicator) and states that "a per-window indicator would be **a new request**" — it is not part
  of the approved D24 scope.
- **Suggested priority:** low

## FS17 — Rename the D36-named shared helper `footprint_cache_key` to a neutral name
- **Gap/opportunity:** after D41 removes the D36 footprint feature, `ibkr/contracts.py::footprint_cache_key`
  survives only because the **kept D39** burst baseline uses it as its resolved-contract key
  (`ui/ticker_session.py:922`). A helper named for a removed feature is misleading to future readers (the same
  applies to `resolve_footprint_contract`'s now-dangling name, which D41 deletes).
- **Why not in the original ask:** the owner asked to remove D36/D37, not to rename shared survivors; a rename
  touches D39 call sites, `services/volume_baseline.py` docstrings and tests, i.e. beyond the removal.
- **Suggested priority:** low (cosmetic/naming; no behaviour change). Defer until after D41 lands.


## FS18 — Generated static doc-index page from the README authority table
- **Gap/opportunity:** `docs/README.md` is the navigation index, but it is still a markdown file a newcomer must know to open; a tiny generated index page (built from the same authority table, never hand-maintained) would make "which doc owns my question" clickable from the repo root.
- **Why not in the original ask:** the owner ordered consolidation of existing docs, not a new navigational surface; D55's navigation goal is satisfied by the README + metadata without new tooling.
- **Suggested priority:** low

## FS19 — Continuous (back-adjusted) futures series
- **Gap/opportunity:** P20 pins per-load front-month auto-roll with rollover gap/overlap per existing `_front_month` behaviour (Q97). A scrolled-back futures chart will therefore show a splice at each roll (price-level step, volume break) rather than a stitched continuous series.
- **Why not in the original ask:** the owner accepted rollover per existing behaviour; a back-adjusted continuous series (ratio/difference adjustment, roll-date markers) is new product scope with its own honesty rules (adjusted vs actual prices).
- **Suggested priority:** low

## FS20 — Magnet snap mode for the crosshair (TradingView magnet)
- **Gap/opportunity:** if Q104 is answered (a) free-only, the TradingView-style magnet (snap crosshair to OHLC on demand) remains unavailable — some users rely on it for exact level placement.
- **Why not in the original ask:** the owner explicitly asked for free cursor-price tracking (magnet-off behaviour); a snap toggle is additional UI scope beyond the defect.
- **Suggested priority:** low

## FS21 — Per-row spread economics (credit, max risk, breakeven, distance from spot)
- **Gap/opportunity:** the eight rows show `ASK`, `BID`, `Delta`, `Gamma` and the instrument name — enough to place the ladder, not enough to judge it. The credit at each rung, the 20-wide max risk, the breakeven and the distance from the underlying's last price are all derivable from data the panel already streams.
- **Why not in the original ask:** the owner named exactly five columns and a Target; adding computed risk columns is new display scope with its own formatting and rounding decisions.
- **Suggested priority:** med (after D65 ships and the owner has used the ladder live)

## FS22 — Underlying spot price and Target-vs-actual readout in the panel header
- **Gap/opportunity:** spread 3 is matched to the Target numerically, but the user cannot see *which* rung was chosen or how far it sits from the Target without reading the ASK/BID columns and doing the arithmetic. A header line — underlying last, spread 3's current mid, the delta to Target, and the strike pair chosen — makes the panel self-explaining.
- **Why not in the original ask:** the owner specified the panel's table, Target field and toggle only; a status line is new layout in a dock that already has a narrow default width.
- **Suggested priority:** med

## FS23 — Ladder shape as a user setting (spread count, width, step)
- **Gap/opportunity:** "4 spreads, all 20 wide, ±5/±10" is hard-coded by the spec. A trader running a different width (10 or 25) or a longer ladder (5–6 rungs) has to edit the code; exposing the three numbers turns one fixed layout into a small but genuinely more useful tool.
- **Why not in the original ask:** the owner gave exact numbers (four spreads, 20 wide, 5-point steps); making them settings adds validation, persistence and layout questions.
- **Suggested priority:** low

## FS24 — Copy / export the ladder as text
- **Gap/opportunity:** the panel's output is a table the user will re-key into TWS. A "copy ladder" action (`SPX Nov17 7435/7455  ask 1.15  bid 1.05  Δ −0.04  Γ −0.002`) removes the transcription step.
- **Why not in the original ask:** the owner asked for display and maintenance, not export; clipboard format is its own small design.
- **Suggested priority:** med (cheap, and the app has no other export surface)

## FS25 — Persist the Target (per underlying) across restarts
- **Gap/opportunity:** A192 deliberately does not persist the Target or the ON state, so every launch starts at `1.00`/OFF. A trader who always works a `0.80` or `1.20` target re-types it daily; remembering the last Target (per underlying) with OFF on launch is the low-risk half of persistence.
- **Why not in the original ask:** persistence was not mentioned, and a stale ON state would subscribe 16 lines at startup before the user looks — so the safe default is "persist nothing".
- **Suggested priority:** low

## FS26 — A positions/account view again (tab or pop-out), if losing it proves painful
- **Gap/opportunity:** Q110(a) replaces the Portfolio panel with Option Spreads, and the owner's no-unused-code rule then deletes the whole account/position stack with it (A198/A200) — so the app shows **no** positions, P/L or account summary anywhere. If the owner misses that view, it has to come back as a deliberate feature rather than by keeping dead code alive.
- **Why not in the original ask:** the owner asked for the right dock to become Option Spreads and chose "replace" over a tab; per the same rule, a view with no home cannot be parked "for later".
- **Suggested priority:** low (revisit only if the owner asks; the cheapest shape is a read-only tab that re-establishes `reqPositions` + a table, with no order surface)
