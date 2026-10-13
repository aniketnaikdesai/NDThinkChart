from ibapi.contract import Contract
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# ── US Eastern timezone (market hours / rollover timing) ─────────────────────
_EASTERN = ZoneInfo("America/New_York")

# ── Futures rollover schedule ────────────────────────────────────────────────
# Each entry maps a futures symbol to its rollover rule:
#   "quarterly" → rollover on Thursday before 3rd Friday of Mar/Jun/Sep/Dec
#   "monthly"   → rollover ~1 week before expiry (expiry in PRIOR month)
#   "seasonal"  → rollover ~1 week before expiry (expiry in PRIOR month)

FUTURES_SCHEDULE = {
    # E-mini equity index futures (quarterly: Mar/Jun/Sep/Dec)
    "ES":  ("FUT", "CME", "USD", "quarterly"),
    "NQ":  ("FUT", "CME", "USD", "quarterly"),
    "YM":  ("FUT", "CME", "USD", "quarterly"),
    "RTY": ("FUT", "CME", "USD", "quarterly"),

    # Metals / Energy (monthly: expiry in PRIOR month)
    # CL Jan expires ~Dec 19, so front month on Jan 10 = Feb contract
    "CL":  ("FUT", "NYMEX", "USD", "monthly"),
    "GC":  ("FUT", "NYMEX", "USD", "monthly"),
    "SI":  ("FUT", "NYMEX", "USD", "monthly"),
    "NG":  ("FUT", "NYMEX", "USD", "monthly"),

    # Agricultural (seasonal: expiry in PRIOR month)
    # ZC (Corn): Mar, May, Jul, Sep, Dec
    "ZC":  ("FUT", "CBOT", "USD", "seasonal"),
    # ZW (Wheat): Mar, May, Jul, Sep, Dec
    "ZW":  ("FUT", "CBOT", "USD", "seasonal"),
    # ZS (Soybeans): Jan, Mar, May, Jul, Aug, Sep, Nov
    "ZS":  ("FUT", "CBOT", "USD", "seasonal"),
}

# ── Contract months per symbol (the DELIVERY months, not expiry months) ──────
# These are the months that appear in the contract symbol (YYYYMM)
_CONTRACT_MONTHS = {
    "quarterly": [3, 6, 9, 12],      # Mar, Jun, Sep, Dec
    "monthly":   list(range(1, 13)),  # All 12 months
    "seasonal": {
        "ZC": [3, 5, 7, 9, 12],       # Corn: Mar, May, Jul, Sep, Dec
        "ZW": [3, 5, 7, 9, 12],       # Wheat: Mar, May, Jul, Sep, Dec
        "ZS": [1, 3, 5, 7, 8, 9, 11], # Soybeans: Jan, Mar, May, Jul, Aug, Sep, Nov
    },
}


def _third_friday(year: int, month: int) -> datetime:
    """Return the 3rd Friday of the given month/year (quarterly futures expiry)."""
    first = datetime(year, month, 1, tzinfo=_EASTERN)
    days_until_friday = (4 - first.weekday()) % 7
    first_friday = first.replace(day=1 + days_until_friday)
    return first_friday.replace(day=first_friday.day + 14)


def _last_trading_day(year: int, month: int) -> datetime:
    """Return last trading day (Thursday before 3rd Friday) for quarterly futures."""
    third_fri = _third_friday(year, month)
    # Last trading day = Thursday before 3rd Friday
    return third_fri.replace(day=third_fri.day - 1)


def _expiry_date(symbol: str, contract_year: int, contract_month: int) -> datetime:
    """Return the approximate expiry date for a given contract month."""
    schedule = FUTURES_SCHEDULE.get(symbol)
    if schedule is None:
        raise ValueError(f"Unknown futures symbol: {symbol}")
    _secType, _exchange, _currency, rollover = schedule

    if rollover == "quarterly":
        # Quarterly: expiry = 3rd Friday of contract month
        return _third_friday(contract_year, contract_month)

    # Monthly & Seasonal: expiry is in the MONTH PRIOR to contract month
    # Approximate: 3rd business day before 25th of prior month
    # Use 20th of prior month as safe proxy
    exp_month = contract_month - 1
    exp_year = contract_year
    if exp_month == 0:
        exp_month = 12
        exp_year -= 1
    return datetime(exp_year, exp_month, 20, tzinfo=_EASTERN)


def _is_past_rollover(now: datetime, expiry: datetime, rollover: str) -> bool:
    """Check if current date is past the rollover date for the given expiry."""
    if rollover == "quarterly":
        # Rollover typically 1 week before last trading day (Thursday)
        last_td = _last_trading_day(expiry.year, expiry.month)
        rollover_date = last_td.replace(day=last_td.day - 7)
        return now >= rollover_date
    else:
        # Monthly/Seasonal: rollover ~1 week before expiry
        rollover_date = expiry.replace(day=expiry.day - 7)
        return now >= rollover_date


def _front_month(symbol: str, now: datetime | None = None) -> tuple[int, int]:
    """Return (year, month) for the front-month CONTRACT month of a futures symbol."""
    if now is None:
        now = datetime.now(_EASTERN)

    schedule = FUTURES_SCHEDULE.get(symbol)
    if schedule is None:
        raise ValueError(f"Unknown futures symbol: {symbol}")

    _, _, _, rollover = schedule
    months = _CONTRACT_MONTHS[rollover]
    if isinstance(months, dict):
        months = months.get(symbol, months.get("default", []))

    # Check current year first, then next year
    for year_offset in (0, 1):
        contract_year = now.year + year_offset
        for contract_month in months:
            expiry = _expiry_date(symbol, contract_year, contract_month)
            if not _is_past_rollover(now, expiry, rollover):
                return (contract_year, contract_month)

    # All rolled → first contract month next year
    next_year = now.year + 1
    return (next_year, months[0])


# ── D36 footprint: index → futures-tape proxy ────────────────────────────────
# Indices have no tape. Footprint/burst features resolve an index to its
# front-month futures contract and label the output accordingly.
INDEX_PROXY = {
    "SPX": "ES",
    "NDX": "NQ",
    "DJI": "YM",
    "RUT": "RTY",
}

# IBKR futures month codes: F G H J K M N Q U V X Z = Jan..Dec.
_FUTURE_MONTH_CODES = "FGHJKMNQUVXZ"


def footprint_cache_key(symbol: str, now: datetime | None = None) -> str:
    """Resolved cache key for footprint data (C36.3, binding everywhere).

    Futures resolve to ``<root><month-code><year-digit>`` (e.g. ``ESZ6`` for
    ES Dec 2026); stocks resolve to the uppercase symbol. Never the bare
    continuous symbol — after a quarterly roll "ES" is a different contract.
    """
    base = symbol.split()[0].upper()
    proxied = INDEX_PROXY.get(base, base)
    schedule = FUTURES_SCHEDULE.get(proxied)
    if schedule is None:
        return base
    year, month = _front_month(proxied, now)
    return f"{proxied}{_FUTURE_MONTH_CODES[month - 1]}{year % 10}"


def resolve_footprint_contract(
    symbol: str, now: datetime | None = None
) -> tuple[str, Contract, str]:
    """Resolve the contract whose tape feeds footprint for ``symbol``.

    Returns ``(cache_key, contract, label)`` where ``label`` is the
    human-readable tape attribution ("" when the symbol uses its own tape —
    the UI shows a proxy label like "ES tape" only for proxied indices).
    SPY/QQQ use their own tape; SPX/NDX resolve to ES/NQ front-month.
    """
    base = symbol.split()[0].upper()
    key = footprint_cache_key(symbol, now)
    proxied = INDEX_PROXY.get(base)
    if proxied is not None:
        contract = get_contract_for_symbol(proxied, now)
        return key, contract, f"{proxied} tape"
    if base in FUTURES_SCHEDULE:
        return key, get_contract_for_symbol(base, now), ""
    return key, get_stock_contract(base), ""


def get_stock_contract(symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = exchange
    contract.currency = currency
    return contract


def get_futures_contract(symbol: str, lastTradeDateOrContractMonth: str, exchange: str, currency: str = "USD") -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "FUT"
    contract.exchange = exchange
    contract.currency = currency
    contract.lastTradeDateOrContractMonth = lastTradeDateOrContractMonth
    
    # Futures specs (multiplier & tradingClass still useful for disambiguation)
    specs = {
        "ES": {"multiplier": "50", "tradingClass": "ES"},
        "NQ": {"multiplier": "20", "tradingClass": "NQ"},
        "YM": {"multiplier": "5", "tradingClass": "YM"},
        "RTY": {"multiplier": "50", "tradingClass": "RTY"},
        "CL": {"multiplier": "1000", "tradingClass": "CL"},
        "GC": {"multiplier": "100", "tradingClass": "GC"},
        "SI": {"multiplier": "5000", "tradingClass": "SI"},
        "NG": {"multiplier": "10000", "tradingClass": "NG"},
        "ZC": {"multiplier": "5000", "tradingClass": "ZC"},
        "ZW": {"multiplier": "5000", "tradingClass": "ZW"},
        "ZS": {"multiplier": "5000", "tradingClass": "ZS"},
    }
    
    if symbol in specs:
        contract.multiplier = specs[symbol]["multiplier"]
        contract.tradingClass = specs[symbol]["tradingClass"]
    
    return contract


def get_contract_for_symbol(symbol: str, now: datetime | None = None) -> Contract:
    """Auto-detect stock vs futures by symbol.

    For futures, the front-month contract is computed dynamically from the
    current date using proper rollover dates (US Eastern time), so the contract
    rolls forward automatically without manual updates to the symbol table.

    Args:
        symbol: e.g. "ES", "NQ", "CL", or "AAPL"
        now: optional datetime for testing; defaults to datetime.now(US/Eastern)

    Returns:
        Contract with secType, exchange, currency, and lastTradeDateOrContractMonth set.
    """
    base = symbol.split()[0].upper()
    schedule = FUTURES_SCHEDULE.get(base)
    if schedule is None:
        return get_stock_contract(symbol)

    secType, exchange, currency, _rollover = schedule
    year, month = _front_month(base, now)
    contract_month = f"{year}{month:02d}"
    return get_futures_contract(base, contract_month, exchange, currency)
