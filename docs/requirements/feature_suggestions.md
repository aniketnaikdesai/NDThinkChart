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
- **Gap/opportunity:** D36 removed the planned `reqHistogramData` path because the method takes **no date
  parameter** and cannot address individual bars (see `docs/architecture.md:218`), so footprint history is built
  from per-session TRADES tick pages. An alternative source (e.g. `reqHistoricalTicks` or a dedicated
  volume-profile endpoint, if ever offered) could fill prior bars more cheaply and reduce IBKR request pressure.
- **Why not in the original ask:** the user asked for footprint charts as they render today; the sourcing strategy
  is an implementation choice the analyst flagged, not a user requirement.
- **Suggested priority:** low

## FS13 — Label delayed (non-real-time) depth distinctly in the heatmap
- **Gap/opportunity:** D37's Journey 32 as-built note records a known limitation — if a delayed-depth feed is
  used **instead of** error 354, the heatmap would render **unlabelled** as if real-time. A small "delayed"
  badge/tint would prevent a user mistaking stale depth for live depth.
- **Why not in the original ask:** the user asked for the heatmap; the 354-vs-delayed distinction is an edge the
  reviewer recorded in code, not a requested surface.
- **Suggested priority:** low
