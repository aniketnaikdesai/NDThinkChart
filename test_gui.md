# GUI Testing — Comprehensive Test Suite

This document describes the full GUI test suite that should be added to the
project to provide automated coverage of all user-facing widgets and
interactions.

---

## Test Framework

- **pytest** + **pytest-qt** for Qt widget testing
- `QT_QPA_PLATFORM=offscreen` for headless execution
- All tests in `tests/test_gui_*.py`
- Run: `python -m pytest tests/test_gui_*.py -v`

---

## Test Files and Coverage

### `tests/test_gui_main_window.py` — MainWindow Integration

**Goal**: Verify that `MainWindow` creates, connects signals, and responds to
user interactions correctly.

| Test | Description |
|------|-------------|
| `test_main_window_creation` | `MainWindow` instantiates without error |
| `test_main_window_toolbar` | All toolbar widgets exist (symbol_input, tf_combo, load_btn, etc.) |
| `test_main_window_docks_present` | Watchlist, ActiveTrader, Portfolio docks exist |
| `test_main_window_status_bar` | Status bar shows "Connecting" initially |
| `test_main_window_signals_wired` | Bridge signals connected to MainWindow slots |
| `test_main_window_portfolio_signals` | Portfolio panel signals connected to handlers |
| `test_main_window_connect_disconnect` | `_on_connected` / `_on_disconnected` update conn_badge |
| `test_main_window_load_chart` | `load_chart()` creates aggregator, requests data |
| `test_main_window_close_event` | Unsubscribes and disconnects on close |
| `test_main_window_symbol_switch` | Loading new symbol cancels previous subscriptions |

### `tests/test_gui_portfolio_panel.py` — ActivePortfolioPanel Integration

**Goal**: Verify that the portfolio panel renders, handles context menus,
emits signals, and updates correctly.

| Test | Description |
|------|-------------|
| `test_portfolio_panel_creation` | `ActivePortfolioPanel` instantiates |
| `test_portfolio_positions_table` | Table has 10 columns with correct headers |
| `test_portfolio_set_positions` | `set_positions()` renders all rows |
| `test_portfolio_add_position` | `add_position()` upserts correctly |
| `test_portfolio_account_summary` | `set_account_summary()` renders summary label |
| `test_portfolio_context_menu` | Right-click opens context menu |
| `test_portfolio_context_menu_actions` | All actions (Set SL/TP, Close, Close Group, Ungroup, Flatten) present |
| `test_portfolio_sltp_position_signal` | `_on_set_sltp` opens dialog, emits `position_sltp_changed` |
| `test_portfolio_sltp_group_signal` | `update_group_sltp` emits `group_sltp_changed` |
| `test_portfolio_close_position_signal` | `_on_close_position` emits `position_close_requested` |
| `test_portfolio_close_group_signal` | `_on_close_group` emits `group_close_requested` |
| `test_portfolio_flatten_all_signal` | `_on_flatten_all` emits `flatten_all_requested` |
| `test_portfolio_ungroup` | `_on_ungroup` clears trade_group_id and re-renders |
| `test_portfolio_strategy_label` | `_group_and_render` detects option strategy labels |
| `test_portfolio_selection_changed` | Item selection updates `_selected_position` |
| `test_portfolio_update_sltp` | `update_position_sltp` updates model and emits signal |

### `tests/test_gui_watchlist_panel.py` — WatchlistPanel Integration

**Goal**: Verify watchlist symbol management and live tick updates.

| Test | Description |
|------|-------------|
| `test_watchlist_creation` | `WatchlistPanel` instantiates |
| `test_watchlist_add_symbol` | `add_symbol()` adds row to table |
| `test_watchlist_remove_symbol` | `remove_symbol()` removes row |
| `test_watchlist_set_market_data_manager` | `set_market_data_manager()` wires correctly |
| `test_watchlist_set_depth_manager` | `set_depth_manager()` wires correctly |
| `test_watchlist_tick_update` | `on_tick_price()` updates row price |
| `test_watchlist_tick_size_update` | `on_tick_size()` updates row size |
| `test_watchlist_clear` | `clear()` removes all rows |

### `tests/test_gui_chart_panel.py` — ChartPanel Integration

**Goal**: Verify chart panel renders bars, studies, drawings, and overlays.

| Test | Description |
|------|-------------|
| `test_chart_panel_creation` | `ChartPanel` instantiates |
| `test_chart_panel_set_symbol` | `set_symbol()` updates chart title |
| `test_chart_panel_set_timeframe` | `set_timeframe()` updates timeframe label |
| `test_chart_panel_set_studies` | `set_studies()` applies study config |
| `test_chart_panel_update_chart` | `update_chart()` renders bar data |
| `test_chart_panel_update_last_bar` | `update_last_bar()` updates only last candle |
| `test_chart_panel_drawing_overlay` | Drawing overlay initialized |
| `test_chart_panel_alarm_overlay` | Alarm overlay initialized |
| `test_chart_panel_zoom` | Zoom in/out works |
| `test_chart_panel_pan` | Pan works |
| `test_chart_panel_study_cache` | `_StudyCache` stores and retrieves arrays |

### `tests/test_gui_alarm_overlay.py` — AlarmOverlay Interaction

**Goal**: Verify alarm lines render, respond to drag, and trigger correctly.

| Test | Description |
|------|-------------|
| `test_alarm_overlay_creation` | `AlarmOverlay` instantiates |
| `test_alarm_overlay_add_alarm` | `create_alarm()` adds line |
| `test_alarm_overlay_remove_alarm` | `remove_alarm()` removes line |
| `test_alarm_overlay_drag` | Dragging line updates price |
| `test_alarm_overlay_mute_toggle` | Mute toggles sound flag |
| `test_alarm_overlay_rearm` | Rearm resets triggered state |
| `test_alarm_overlay_trigger` | Crossing price triggers alarm |
| `test_alarm_overlay_reach` | Alarm line visibility based on active/muted |

### `tests/test_gui_order_entry.py` — ActiveTraderPanel Integration

**Goal**: Verify order entry UI, safety gates, and order placement.

| Test | Description |
|------|-------------|
| `test_order_entry_creation` | `ActiveTraderPanel` instantiates |
| `test_order_entry_buy_sell` | Buy/Sell buttons toggle action |
| `test_order_entry_qty_stepper` | Quantity stepper increments/decrements |
| `test_order_entry_order_type` | MKT/LMT/STP/Bracket tabs switch |
| `test_order_entry_lmt_price` | Limit price field accepts input |
| `test_order_entry_stop_price` | Stop price field accepts input |
| `test_order_entry_target_price` | Target price field accepts input |
| `test_order_entry_safety_gate` | Safety gate default OFF |
| `test_order_entry_confirm_dialog` | Confirmation dialog appears on send |
| `test_order_entry_order_place` | `order_place_requested` signal emitted |

### `tests/test_gui_context_menu.py` — TradeContextMenu Interaction

**Goal**: Verify context menu actions and their signal connections.

| Test | Description |
|------|-------------|
| `test_context_menu_creation` | `TradeContextMenu` instantiates |
| `test_context_menu_actions_present` | All actions (Set SL/TP, Close, Close Group, Ungroup, Flatten) present |
| `test_context_menu_set_sltp_signal` | `set_sltp_action.triggered` emits correctly |
| `test_context_menu_close_position_signal` | `close_position_action.triggered` emits correctly |
| `test_context_menu_close_group_signal` | `close_group_action.triggered` emits correctly |
| `test_context_menu_ungroup_signal` | `ungroup_action.triggered` emits correctly |
| `test_context_menu_flatten_all_signal` | `flatten_all_action.triggered` emits correctly |
| `test_context_menu_actions_enabled` | `set_actions_enabled()` enables/disables actions |

### `tests/test_gui_stop_loss_target.py` — StopLossTargetDialog Integration

**Goal**: Verify SL/TP dialog validates input and emits confirmation signal.

| Test | Description |
|------|-------------|
| `test_dialog_creation` | `StopLossTargetDialog` instantiates |
| `test_dialog_position_apply` | Apply-to Position combo works |
| `test_dialog_group_apply` | Apply-to Group combo works |
| `test_dialog_long_validation` | Long: stop < market < target validated |
| `test_dialog_short_validation` | Short: stop > market > target validated |
| `test_dialog_equality_rejection` | stop==market / target==market rejected |
| `test_dialog_min_tick` | Min-tick multiplier-aware validation |
| `test_dialog_confirmed_signal` | `confirmed` signal emits with correct args |
| `test_dialog_set_target_info` | `set_target_info()` updates dialog label |

### `tests/test_gui_main_window_signals.py` — Signal Propagation

**Goal**: Verify end-to-end signal propagation from IBKR callbacks through
bridge to UI widgets.

| Test | Description |
|------|-------------|
| `test_bridge_connected_signal` | `connected` signal emitted on `nextValidId` |
| `test_bridge_disconnected_signal` | `disconnected` signal emitted on `connectionClosed` |
| `test_bridge_tick_price_signal` | `tick_price` signal forwarded to watchlist |
| `test_bridge_realtime_bar_signal` | `realtime_bar` signal forwarded to aggregator |
| `test_bridge_position_update_signal` | `position_update` signal forwarded to portfolio |
| `test_bridge_position_end_signal` | `position_end` signal loads persisted positions |
| `test_bridge_account_summary_signal` | `account_summary` signal updates portfolio |
| `test_bridge_update_mkt_depth_signal` | `update_mkt_depth` signal forwarded to depth panel |
| `test_bridge_order_status_signal` | `order_status` signal updates order status |
| `test_bridge_open_order_signal` | `open_order` signal updates open order registry |

### `tests/test_gui_drawings.py` — Drawing Overlay Interaction

**Goal**: Verify drawing tools respond to mouse events and create items.

| Test | Description |
|------|-------------|
| `test_drawing_overlay_create_trendline` | Trendline tool creates 2-point line |
| `test_drawing_overlay_create_horizontal` | Horizontal tool creates `InfiniteLine` |
| `test_drawing_overlay_create_zone` | Zone tool creates `LinearRegionItem` |
| `test_drawing_overlay_create_fibonacci` | Fibonacci tool creates stacked lines |
| `test_drawing_overlay_create_measure` | Measure tool creates delta label |
| `test_drawing_overlay_selection` | Click selects drawing, shows handles |
| `test_drawing_overlay_delete` | Delete key removes selected drawing |
| `test_drawing_overlay_drag` | Drag moves drawing endpoints |
| `test_drawing_overlay_lock` | Locked drawings ignore drag |
| `test_drawing_overlay_visibility` | Hidden group drawings not rendered |

### `tests/test_gui_reconnect.py` — Reconnect Behavior Integration

**Goal**: Verify that reconnect behavior properly restores subscriptions
and updates UI state.

| Test | Description |
|------|-------------|
| `test_reconnect_state_machine` | State transitions: DISCONNECTED → RECONNECTING → CONNECTED |
| `test_reconnect_polling` | `start_polling` creates timer |
| `test_reconnect_backoff` | Exponential backoff increases delay |
| `test_reconnect_subscription_replay` | `_replay_subscriptions` replays subscriptions |
| `test_reconnect_watchlist_restore` | `_restore_watchlist` called on connect |
| `test_reconnect_status_bar` | Status bar shows reconnect message |
| `test_reconnect_subscription_manager` | `SubscriptionManager.subscribe/unsubscribe` work |
| `test_reconnect_bar_aggregator_dedup` | `BarAggregator._last_pushed_ts` prevents duplicates |

---

## Test Execution

```bash
# All GUI tests
python -m pytest tests/test_gui_*.py -v

# Specific module
python -m pytest tests/test_gui_main_window.py tests/test_gui_portfolio_panel.py -v

# With offscreen Qt
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_*.py -v

# Full suite (all tests including non-GUI)
python -m pytest tests/ -v
```

---

## Test Infrastructure

### `conftest.py` additions:

```python
# Already exists:
# - qapp fixture (offscreen QApplication)
# - chart_panel fixture (ChartPanel)
# - sample_bars, impulse_bars, gap_bars fixtures
# - DB_PATH override to temp file

# Additional fixtures needed:
# - main_window fixture (MainWindow instance)
# - portfolio_panel fixture (ActivePortfolioPanel)
# - watchlist_panel fixture (WatchlistPanel)
# - depth_manager fixture (MarketDepthManager mock)
```

### Required dependencies:

```
# requirements-dev.txt additions
pytest-qt
```

---

## Notes

- All GUI tests run **offscreen** — no display server required
- All tests use **mock data** — no live TWS connection needed
- The `conftest.py` already sets `QT_QPA_PLATFORM=offscreen`
- Existing test infrastructure (`pytest.ini`, `conftest.py`) supports the
  new test files
- Tests should not modify the persistent DB — use temp DB from `conftest.py`
