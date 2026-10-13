"""MD-line budget guard (D37 work item 37.5 — owns the §7 "Market-data lines"
accounting).

Pure logic: assess a projected market-data line count against IBKR's
100-line pool. Thresholds:

- ``ok``         — under 90 lines; subscribe freely
- ``approaching`` — 90–99 lines; subscribe, but warn (name the symbol)
- ``exceeded``    — 100+ lines; warn naming the symbol and refuse — the
  refusal is explicit, never a silent drop

The host (MainWindow) supplies the count and surfaces the warning; the
session gates new D37 subscriptions (depth feeds, S0 lines) on the verdict.
"""

MD_LINE_CAP = 100
MD_LINE_WARN_AT = 90


def assess(projected_count: int, symbol: str, purpose: str
           ) -> tuple[str, str]:
    """Assess a projected line count.

    Returns ``(level, message)`` with level in
    ``{"ok", "approaching", "exceeded"}``. The message names the symbol so
    the host can surface it verbatim.
    """
    if projected_count >= MD_LINE_CAP:
        return ("exceeded",
                f"Market-data line budget exceeded ({projected_count}/"
                f"{MD_LINE_CAP}) — not subscribing {purpose} for {symbol}.")
    if projected_count >= MD_LINE_WARN_AT:
        return ("approaching",
                f"Market-data lines near cap ({projected_count}/"
                f"{MD_LINE_CAP}) — subscribing {purpose} for {symbol}.")
    return ("ok", "")
