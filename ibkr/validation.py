"""D26.7: order validation gate.

Pure function — no I/O, no Qt, no IBKR calls. Returns a list of human-readable
problems; an empty list means the order is valid. Wired at the top of
``MainWindow._close_position_by_id`` so invalid input is rejected in the UI and
can never reach ``placeOrder`` (and never raises).
"""

from config.settings import MAX_ORDER_NOTIONAL

_VALID_SIDES = ("BUY", "SELL")
_VALID_TYPES = ("MKT", "LMT", "STP", "BRACKET")


def validate_order(*, action: str, order_type: str, qty: float,
                   lmt_price: float = 0.0, stop_price: float = 0.0,
                   target_price: float = 0.0, symbol: str = "",
                   ref_price: float | None = None,
                   risk_reducing: bool = False) -> list[str]:
    """Validate a prospective order; return problems (empty == valid).

    ``ref_price`` is a best-effort market reference used for the notional
    check on price-less orders (MKT/STP). LMT/BRACKET always carry lmt_price.
    When no positive price basis exists the notional check is skipped —
    every other check still applies.

    ``risk_reducing`` marks an order that closes/reduces existing exposure
    (the Portfolio close/flatten path). When ``True`` **only** the
    notional-cap check is skipped — the cap exists to bound *new* exposure,
    so a position above the cap must still be closable. Every structural
    check (symbol, side, type, quantity, per-type prices, bracket geometry)
    applies unchanged.
    """
    problems: list[str] = []

    if not (symbol or "").strip():
        problems.append("Symbol is required.")
    if action not in _VALID_SIDES:
        problems.append(f"Unknown side {action!r}; expected BUY or SELL.")
    if order_type not in _VALID_TYPES:
        problems.append(f"Unknown order type {order_type!r}.")
    if not qty or qty <= 0:
        problems.append(f"Quantity must be greater than 0 (got {qty}).")

    # Prices required per type. A 0.0 stop/limit is not "unset" to TWS — a
    # 0.0 auxPrice on a STP triggers immediately as a market order.
    if order_type == "LMT" and not lmt_price > 0:
        problems.append("Limit price must be greater than 0 for LMT orders.")
    if order_type == "STP" and not stop_price > 0:
        problems.append("Stop price must be greater than 0 for STP orders.")
    if order_type == "BRACKET":
        for name, px in (("limit", lmt_price), ("stop", stop_price),
                         ("target", target_price)):
            if not px > 0:
                problems.append(
                    f"Bracket {name} price must be greater than 0.")

    # Bracket geometry: protective stop below entry, target above, for longs
    # (mirrored for shorts). Catches inverted stop/target entry.
    if (order_type == "BRACKET" and lmt_price > 0 and stop_price > 0
            and target_price > 0):
        if action == "BUY" and not (stop_price < lmt_price < target_price):
            problems.append(
                "Bracket geometry wrong for BUY: need stop < entry < target.")
        elif action == "SELL" and not (stop_price > lmt_price > target_price):
            problems.append(
                "Bracket geometry wrong for SELL: need stop > entry > target.")

    # Notional cap. Skipped for risk-reducing orders (they shrink existing
    # exposure rather than create it), so only when risk_reducing is False.
    price_basis = None
    if order_type in ("LMT", "BRACKET") and lmt_price > 0:
        price_basis = lmt_price
    elif ref_price and ref_price > 0:
        price_basis = ref_price
    if not risk_reducing and price_basis and qty and qty > 0:
        notional = qty * price_basis
        if notional > MAX_ORDER_NOTIONAL:
            problems.append(
                f"Notional ${notional:,.0f} exceeds the "
                f"${MAX_ORDER_NOTIONAL:,.0f} per-order cap.")

    return problems
