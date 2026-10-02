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

## FS7 — Compress/collapse non-trading time (weekends, holidays, overnight)
- **Gap/opportunity:** D16 leaves genuine closures as empty spans (`AC-D16.3`). Some
  terminals collapse them to reduce dead space.
- **Why not in the original ask:** The user's complaint is missing *trading* data, not the
  weekend gap; compressing time is a separate x-axis design change.
- **Suggested priority:** low
