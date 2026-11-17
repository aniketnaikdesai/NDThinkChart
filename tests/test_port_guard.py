"""D26.5 fail-fast: IBKR_PORT must be the live port (7496).

S-P23-24: the badge states the connection, not the account. The account
id/type arrived on the account-summary stream the P23 account-path removal
deletes (AC-D65.13), so the badge's paper/live derivation retires with it.
The fail-fast live-port rule is the half of AC-D26.5 that survives —
untouched — and it proves only the port, never the account, so it licenses no
"Live" label.
"""

import inspect

import pytest

from config import settings


def test_check_live_port_rejects_paper_port(monkeypatch):
    monkeypatch.setattr(settings, "IBKR_PORT", 7497)
    with pytest.raises(SystemExit):
        settings.check_live_port()


def test_check_live_port_accepts_live_port(monkeypatch):
    monkeypatch.setattr(settings, "IBKR_PORT", 7496)
    settings.check_live_port()  # must not raise


def test_badge_text_connected():
    from ui.main_window import conn_badge_text

    text, color = conn_badge_text()
    assert text == "● Connected"
    assert color == "#34d399"


def test_badge_text_paused_keeps_d40_wording():
    from ui.main_window import conn_badge_text

    text, color = conn_badge_text(monitoring_paused=True)
    assert text == "Monitoring paused — TWS disconnected"
    assert color == "#fbbf24"


def test_badge_text_takes_no_account_parameter():
    from ui.main_window import conn_badge_text

    assert list(inspect.signature(conn_badge_text).parameters) == [
        "monitoring_paused"
    ]
    # No replacement account source is invented: a port-derived label is the
    # hardcoded claim AC-D26.5 forbids.
    text, _color = conn_badge_text()
    assert "Live" not in text
    assert "Paper" not in text


def test_update_conn_badge_reads_no_account_state():
    from ui import main_window

    source = inspect.getsource(main_window.MainWindow._update_conn_badge)
    # The retired account reads were getattr() probes on window state; the
    # badge now reads only the window's own pause flag.
    assert "getattr(" not in source
    assert "conn_badge_text(monitoring_paused=self._tws_paused)" in source


def test_connecting_and_disconnected_texts_untouched():
    from ui import main_window

    assert 'QLabel("● Connecting")' in inspect.getsource(
        main_window.MainWindow.__init__
    )
    assert '"● Disconnected"' in inspect.getsource(
        main_window.MainWindow._on_disconnected
    )
