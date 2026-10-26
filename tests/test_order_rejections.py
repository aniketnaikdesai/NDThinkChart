"""D26.9 / AC-D46.3: TWS order errors surface on the status bar; codes
promoted.

D41/D45: the order-entry ticket and the order registry are gone. A reported
error that matches no live session reqId reaches the retained generic line
``Error [<code>]: <text>`` on the status bar (``MainWindow._on_error``), which
is the owner's error visibility.
"""

import pytest

from ibkr.error_codes import classify_error


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient
    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow
    win = MainWindow()
    win.show()
    qapp.processEvents()
    return win


def test_non_order_error_shows_generic_line(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        win._on_error(reqId=9999, errorCode=2105,
                      errorString="Data farm connection is broken")
        msg = win.status_bar.currentMessage()
        assert "[2105]" in msg, f"code missing from status: {msg!r}"
        assert "Data farm connection is broken" in msg, (
            f"TWS message missing from status: {msg!r}")
    finally:
        win.close()


@pytest.mark.parametrize(
    ("code", "tws_message"),
    [
        (201, "Order rejected - reason: price violates tick"),
        (103, "Duplicate order id"),
        (202, "Order Canceled - reason:"),
    ],
    ids=["201", "103", "202"],
)
def test_order_error_codes_surface_on_status_bar(monkeypatch, qapp,
                                                 code: int,
                                                 tws_message: str) -> None:
    win = _make_window(monkeypatch, qapp)
    try:
        win._on_error(reqId=987654, errorCode=code, errorString=tws_message)
        msg = win.status_bar.currentMessage()
        assert f"[{code}]" in msg, f"code {code} not surfaced: {msg!r}"
        assert tws_message in msg, (
            f"TWS message missing from status: {msg!r}")
    finally:
        win.close()


@pytest.mark.parametrize("code", [201, 103, 1100, 502, 503, 509])
def test_order_and_connection_codes_promoted(code):
    assert classify_error(code) == "fatal", f"{code} must be fatal"


def test_info_codes_still_info():
    assert classify_error(2104) == "info"
    assert classify_error(2106) == "info"
