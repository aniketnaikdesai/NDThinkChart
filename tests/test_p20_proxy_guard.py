"""P20-T3 — Proxy-never-for-price guard + P20 batch gate (AC-D59.5 / AC-D59.6).

Offscreen structural guard for S-P20-6 / S-P20-7. No production code is
touched by this task; this module only pins behaviour:

* AC1a (P20-T3-AC1a) — every index chart-series bar traces to its own IND
  contract; no index load ever resolves to a futures contract; the
  tape-only burst-proxy use (INDEX_PROXY / footprint_cache_key /
  _proxy_targets) is preserved. The existing burst-proxy suite
  (tests/test_d39_burst_search.py) runs in the same command and stays green.
* AC1b (P20-T3-AC1b) — source-shape assertion: the chart load/history path
  is INDEX_PROXY-free; a future re-coupling fails here, not in production.
* AC2 (P20-T3-AC2) — history-intact gate: the D41-D58 requirement sections,
  the Existing Repository marker and Current Tech Stack are present, and no
  pre-P20 wording in docs/requirements/requirements.md is touched.
  (Full-suite-green is the runner gate: this file runs together with the
  burst-proxy suite via the task test_command.)
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess
from datetime import datetime

import pytest

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo

from data.models import Bar
from ibkr.contracts import (
    FUTURES_SCHEDULE,
    IND_CONTRACTS,
    INDEX_PROXY,
    footprint_cache_key,
    get_contract_for_symbol,
    get_index_contract,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent

# IND family rows, Plan-stated per the TWS IND spec (AP-P20-1).
EXPECTED_IND = {
    "SPX": ("IND", "CBOE", "USD"),
    "NDX": ("IND", "NASDAQ", "USD"),
    "DJI": ("IND", "CME", "USD"),
    "RUT": ("IND", "CME", "USD"),
}

# Futures roots that back the index tapes (INDEX_PROXY values).
EXPECTED_PROXY = {
    "SPX": "ES",
    "NDX": "NQ",
    "DJI": "YM",
    "RUT": "RTY",
}

# Chart load/history path: contracts resolution (asserted separately at
# function granularity in AC1b) plus the load_chart history legs, which must
# contain zero INDEX_PROXY references at file granularity.
CHART_PATH_FILES = [
    "ui/main_window.py",
    "ui/ticker_session.py",
    "services/backfill_service.py",
    "services/contract_lookup_service.py",
    "services/time_collapse_service.py",
    "ui/lwc_view.py",
]

# Chart-resolution functions in ibkr/contracts.py: must never consult the
# tape-only proxy. get_probe_contract is included — the Q99 probe builds a
# bare symbol-only contract, never a proxied one.
CHART_RESOLUTION_FNS = {
    "_base_symbol",
    "is_index_symbol",
    "is_futures_root",
    "get_index_contract",
    "get_probe_contract",
    "get_stock_contract",
    "get_futures_contract",
    "get_contract_for_symbol",
}


def _bar(symbol: str, ts: int = 1_760_000_000) -> Bar:
    return Bar(symbol=symbol, timeframe="1 min", ts=ts, open=100.0,
               high=100.0, low=100.0, close=100.0, volume=1000.0)


# ── AC1a: index chart-series provenance (never a futures contract) ────────

@pytest.mark.parametrize("symbol", sorted(EXPECTED_IND))
def test_p20_t3_ac1a_index_chart_series_never_futures(symbol):
    """Every index chart-series bar traces to its IND contract (AC-D59.5)."""
    contract = get_contract_for_symbol(symbol)
    sec_type, exchange, currency = EXPECTED_IND[symbol]
    assert contract.secType == sec_type == "IND"
    assert contract.exchange == exchange
    assert contract.currency == currency
    assert contract.symbol == symbol
    # A futures contract carries YYYYMM; an IND chart contract must not.
    assert getattr(contract, "lastTradeDateOrContractMonth", "") in ("", None)
    # Structural pin: the chart contract IS the IND-table contract and is
    # never the futures shape, whatever the front-month roll computes.
    ind = get_index_contract(symbol)
    assert (contract.secType, contract.exchange, contract.currency) == \
        (ind.secType, ind.exchange, ind.currency)
    assert not getattr(contract, "lastTradeDateOrContractMonth", "")


@pytest.mark.parametrize("symbol", sorted(EXPECTED_IND))
def test_p20_t3_ac1a_index_bar_symbol_is_never_a_futures_root(symbol):
    """Chart bars labelled with an index symbol never originate from futures."""
    bar = _bar(symbol)
    assert bar.symbol == symbol
    # The bar's own symbol resolves to IND, not to any FUTURES_SCHEDULE root.
    contract = get_contract_for_symbol(bar.symbol)
    assert contract.secType == "IND"
    assert bar.symbol.upper() not in FUTURES_SCHEDULE
    # The proxy tape for this index IS a futures root — that is where the
    # tape-only burst path reads, never the chart series.
    proxy = INDEX_PROXY[symbol]
    assert proxy in FUTURES_SCHEDULE
    assert get_contract_for_symbol(proxy).secType == "FUT"


def test_p20_t3_ac1a_index_and_proxy_tapes_stay_distinct():
    """Index chart contracts and their proxy futures contracts differ in kind."""
    for symbol, proxy in EXPECTED_PROXY.items():
        chart = get_contract_for_symbol(symbol)
        tape = get_contract_for_symbol(proxy)
        assert chart.secType == "IND"
        assert tape.secType == "FUT"
        assert tape.exchange == "CME"
        assert tape.currency == "USD"
        assert getattr(tape, "lastTradeDateOrContractMonth", "")
        assert chart.symbol != tape.symbol


def test_p20_t3_ac1a_tape_only_proxy_use_preserved():
    """INDEX_PROXY stays a 4-row tape-only map; footprint keys stay proxied."""
    assert INDEX_PROXY == EXPECTED_PROXY
    assert IND_CONTRACTS == EXPECTED_IND
    et = ZoneInfo("America/New_York")
    now = datetime(2026, 10, 13, tzinfo=et)
    for symbol, proxy in EXPECTED_PROXY.items():
        key = footprint_cache_key(symbol, now=now)
        assert key.startswith(proxy)
        assert not key.startswith(symbol)
    # Front-month rollover still isolates the tape (D36 KEEP behaviour).
    later = datetime(2027, 2, 1, tzinfo=et)
    assert footprint_cache_key("SPX", now=now) != \
        footprint_cache_key("SPX", now=later)


# ── AC1b: source-shape assertion (chart path INDEX_PROXY-free) ────────────

def test_p20_t3_ac1b_chart_resolution_never_consults_proxy():
    """Chart-resolution functions contain no INDEX_PROXY reference (AC-D59.5)."""
    src = (ROOT / "ibkr" / "contracts.py").read_text()
    tree = ast.parse(src)
    fns = {n.name: n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    missing = CHART_RESOLUTION_FNS - set(fns)
    assert not missing, f"chart-resolution fns gone from contracts.py: {missing}"
    for name in sorted(CHART_RESOLUTION_FNS):
        assert "INDEX_PROXY" not in ast.dump(fns[name]), \
            f"{name} consults INDEX_PROXY — chart path re-coupled to the proxy"
    # Tape-only use preserved: the proxy survives exactly where it belongs.
    assert re.search(r"(?m)^INDEX_PROXY\s*=\s*\{", src)
    assert "INDEX_PROXY" in ast.dump(fns["footprint_cache_key"])


def test_p20_t3_ac1b_proxy_reference_lives_only_in_proxy_targets():
    """services/alarm_monitor.py mentions INDEX_PROXY only in _proxy_targets."""
    src = (ROOT / "services" / "alarm_monitor.py").read_text()
    tree = ast.parse(src)
    target = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "_proxy_targets")
    assert "INDEX_PROXY" in ast.dump(target)
    start, end = target.lineno - 1, target.end_lineno
    lines = src.splitlines()
    strays = [i + 1 for i, line in enumerate(lines)
              if "INDEX_PROXY" in line and not (start <= i < end)]
    assert not strays, \
        f"INDEX_PROXY outside _proxy_targets (tape-only burst path): lines {strays}"


def test_p20_t3_ac1b_chart_load_history_path_is_proxy_free():
    """No chart load/history leg references INDEX_PROXY (structural S-P20-6)."""
    for rel in CHART_PATH_FILES:
        path = ROOT / rel
        assert path.is_file(), f"chart-path file missing: {rel}"
        text = path.read_text()
        assert "INDEX_PROXY" not in text, \
            f"{rel} references INDEX_PROXY — chart path re-coupled to the proxy"


# ── AC2: history-intact gate (AC-D59.6) ───────────────────────────────────

def test_p20_t3_ac2_history_intact():
    """D41-D58 sections + markers present; no pre-P20 wording touched."""
    req = ROOT / "docs" / "requirements" / "requirements.md"
    assert req.is_file(), "docs/requirements/requirements.md missing"
    text = req.read_text()
    # D41-D53 land as `### D<N> — …` sections; D54+ land as
    # `## Phase P<N> — … (D<N>)` + `#### Journey … — D<N>: …` headings.
    missing = [n for n in range(41, 59)
               if not re.search(rf"(?m)^#{{2,4}}\s+.*\bD{n}\b", text)]
    assert not missing, f"requirement sections missing: {missing}"
    assert re.search(r"(?i)reversal", text), "reversal record missing"
    assert "Existing Repository" in text, "Existing Repository marker missing"
    assert "Current Tech Stack" in text, "Current Tech Stack section missing"
    # No pre-P20 wording touched: the frozen requirements input is
    # byte-identical to HEAD (P20 adds code + tests, never requirements prose).
    proc = subprocess.run(
        ["git", "diff", "HEAD", "--", "docs/requirements/requirements.md"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"git diff failed: {proc.stderr.strip()}"
    assert proc.stdout.strip() == "", \
        "docs/requirements/requirements.md differs from HEAD — " \
        "pre-P20 wording was touched"
