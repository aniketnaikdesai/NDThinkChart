# GUI Test Plan — NDThinkChart

## 1. Purpose

This document defines the scope, organization, and execution strategy for the
automated GUI test suite of the NDThinkChart application. All tests are designed
to run under `QT_QPA_PLATFORM=offscreen` — no display server or live TWS
connection is required.

The goal is to achieve high confidence in user-facing widget behavior while
maintaining fast, deterministic test runs suitable for CI.

---

## 2. Objectives

| Objective | Description |
|-----------|-------------|
| **Widget correctness** | Verify that all PyQt6 widgets create, render, and function as designed |
| **Signal propagation** | Ensure IBKR callbacks → bridge → MainWindow slots → portfolio/watchlist/chart updates correctly |
| **User interaction** | Simulate clicks, context menus, drags, key presses, combobox changes |
| **Integration coverage** | Test end-to-end paths (e.g., chart load → study apply → alarm trigger) |
| **No TWS dependency** | All tests run without Interactive Brokers TWS running |
| **Fast CI runs** | Target < 5 seconds for the full GUI suite; < 1 second for unit-proximate tests |
| **Regression guard** | Protect against import breaks, signal wiring errors, and layout regressions |

---

## 3. Test Organization

All GUI test files live in `tests/` and are named `test_gui_*.py`.

| Test File | Test Count | Primary Focus |
|-----------|------------|---------------|
| `test_gui_main_window.py` | 10 | MainWindow creation, toolbar, docks, connect/disconnect, load chart, close event, symbol switch |
| `test_gui_portfolio_panel.py` | 16 | ActivePortfolioPanel rendering, positions table, account summary, context menu actions, SL/TP signals, ungroup, strategy labels, selection |
| `test_gui_watchlist_panel.py` | 7 | Symbol management, tick/size updates, market data manager wiring, clear |
| `test_gui_chart_panel.py` | 10 | ChartPanel creation, symbol/timeframe, studies, bar updates, zoom/pan, study cache |
| `test_gui_alarm_overlay.py` | 8 | Alarm line creation/removal/drag/mute/rearm/trigger/reach |
| `test_gui_order_entry.py` | 10 | ActiveTraderPanel buy/sell, quantity stepper, order types, LMT price, safety gate, confirmation dialog |
| `test_gui_context_menu.py` | 7 | TradeContextMenu actions (Set SL/TP, Close Position, Close Group, Ungroup, Flatten), action enabled state |
| `test_gui_stop_loss_target.py` | 9 | StopLossTargetDialog creation, position/group apply, long/short validation, equality rejection, min-tick, confirmed signal |
| `test_gui_main_window_signals.py` | 10 | Bridge signal propagation: connected/disconnected/tick price/realtime bar/position update/account summary/update mkt depth/order status/open order |
| `test_gui_drawings.py` | 10 | Drawing overlay: create each type (trendline/horizontal/zone/fibonacci/measure), selection, delete, drag, lock, visibility |
| `test_gui_reconnect.py` | 7 | Reconnect state machine, polling timer, exponential backoff, subscription replay, watchlist restore, status bar messages, SubscriptionManager |

**Total: 98 automated GUI tests**

---

## 4. Test Execution

### 4.1 Run All GUI Tests

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_*.py -v
```

### 4.2 Run Specific Modules

```bash
# MainWindow + Portfolio
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_main_window.py tests/test_gui_portfolio_panel.py -v

# Alarm + SL/TP
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_alarm_overlay.py tests/test_gui_stop_loss_target.py -v

# Quick import + logic only
python -m pytest tests/test_ui_smoke.py -v
```

### 4.3 Run Full Test Suite (all tests)

```bash
python -m pytest tests/ -v
# → 269 passed in ~1.5s (all phases)
```

### 4.3 Run With Coverage

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/ --cov=ui --cov=ibkr --cov=data --cov=services
```

---

## 5. Fixtures (conftest.py)

### Already Exists:

- `qapp` — Single offscreen `QApplication` for the whole session
- `chart_panel` — `ChartPanel` instance (created → yielded → closed)
- `sample_bars` — 200 one-minute bars with monotonically rising closes
- `impulse_bars` — 300-bar alternating impulse dataset (ICT concepts)
- `gap_bars` — Two sessions with an up gap + fill bar
- `BASE_TS = 1_700_000_000`, `DAY = 86_400`
- `DB_PATH` override to temp file in `system.tempdir()`

### To Add:

- `main_window` — `MainWindow` instance (using `qapp` fixture)
- `portfolio_panel` — `ActivePortfolioPanel` instance
- `watchlist_panel` — `WatchlistPanel` instance
- `depth_manager` — mock `MarketDepthManager` (or real, since it uses offscreen Qt)

### Fixture Dependencies:

```
qapp
  → main_window
      → portfolio_panel
      → watchlist_panel
      → chart_panel
          → drawing_overlay
          → alarm_overlay
```

---

## 6. Test Execution Environment

| Requirement | Value |
|-------------|-------|
| Python | 3.11+ |
| PyQt6 | 6.x (tested with 6.6+) |
| pytest | 7.x+ |
| pytest-qt | 4.x+ |
| pyqtgraph | 0.13+ |
| ibapi | 2.1+ (official IBKR package) |
| OS | macOS 11+ (ARM64) primary; Linux/Windows offscreen-capable |
| Display | `QT_QPA_PLATFORM=offscreen` (no X11/Wayland needed) |

### Environment Setup

```bash
# In project root
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # includes pytest, pytest-qt, pyqtgraph, ibapi
```

---

## 7. Acceptance Criteria

| Criterion | Description |
|-----------|-------------|
| **All 98 GUI tests pass** | No failures on `main` branch |
| **Zero TWS dependency** | Tests run on CI without TWS |
| **< 5s full suite runtime** | On CI runner (macOS ARM64) |
| **Import regression guard** | `test_ui_smoke.py` passes after any refactor |
| **Signal wiring confidence** | `test_gui_main_window_signals.py` confirms bridge → widget propagation |
| **User interaction parity** | `test_gui_portfolio_panel.py`, `test_gui_order_entry.py`, `test_gui_context_menu.py` reflect real workflow |
| **No visual regression** | `test_gui_drawings.py` confirms all drawing types render and interact |

### Passing Threshold

- All 98 tests: **must pass**
- Any failure: block merge until resolved
- Flaky tests: investigate and fix; if unfixable, disable with `@pytest.mark.xfail(reason=...)`

---

## 8. Phasing / Rollout Plan

| Phase | Tests | Goal |
|-------|-------|------|
| **Phase A** | `test_ui_smoke.py` (4 tests) | Confirm all module imports under offscreen Qt |
| **Phase B** | `test_gui_main_window.py` (10 tests) + `test_gui_main_window_signals.py` (10 tests) | MainWindow creation, toolbar, docks, connect/disconnect, signal wiring |
| **Phase C** | `test_gui_portfolio_panel.py` (16 tests) + `test_gui_context_menu.py` (7 tests) | Portfolio panel rendering, context menus, SL/TP signals, ungroup, strategy labels |
| **Phase D** | `test_gui_chart_panel.py` (10 tests) + `test_gui_alarm_overlay.py` (8 tests) + `test_gui_stop_loss_target.py` (9 tests) | Chart panel studies/updates, alarm overlay, SL/TP dialog validation |
| **Phase E** | `test_gui_order_entry.py` (10 tests) + `test_gui_reconnect.py` (7 tests) | Order entry UI + reconnect behavior |
| **Phase F** | `test_gui_watchlist_panel.py` (7 tests) + `test_gui_drawings.py` (10 tests) | Watchlist tick updates + drawing overlay interaction |
| **Phase FULL** | All 98 tests | Complete GUI test suite in CI |

---

## 8. Notes

- **All tests run offscreen** — no X11/Wayland display required. The `conftest.py` already sets `QT_QPA_PLATFORM=offscreen`.
- **No live TWS** — all tests use mock/stub data; `conftest.py` overrides `DB_PATH` to a temp file.
- **Existing `test_ui_smoke.py`** guards against import regressions and should remain the first test run in CI.
- **`pytest-qt`** is the only new dependency needed (add to `requirements-dev.txt`).
- The test suite is **additive** — new tests can be added without breaking existing ones, as long as fixtures are respected.
- See `test_gui.md` for individual test case specifications.
- Run `python -m pytest tests/test_ui_smoke.py -v` before any refactor to confirm import stability.

---

## 9. Glossary

| Term | Meaning |
|------|---------|
| `offscreen` | `QT_QPA_PLATFORM=offscreen` — headless Qt mode, no windows displayed |
| `bridge` | `IBBridge` — forwards `EWrapper` callbacks from `IBApiClient` to PyQt signals |
| `conftest.py` | pytest shared fixtures and session-wide setup |
| `pytest-qt` | pytest plugin for Qt widget testing (`qtbot`, `qapp`, etc.) |
| `signal` | PyQt `pyqtSignal` — callback mechanism between IBKR layer and UI layer |
| `fixture` | Reusable test setup object (e.g., `qapp`, `main_window`) |
| `xfail` | pytest marker for expected failures (used for known-known issues) |