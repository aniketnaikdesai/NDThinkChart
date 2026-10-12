"""D26.5: fail fast unless IBKR_PORT is the live port (7496); the connection
badge derives from the verified port + account type, never a hardcoded string.

AC-D26.5: IBKR_PORT=7497 -> fail-fast; the badge never reads "Live" for a
non-live configuration.
"""

import pytest

from config import settings


def test_check_live_port_rejects_paper_port(monkeypatch):
    monkeypatch.setattr(settings, "IBKR_PORT", 7497)
    with pytest.raises(SystemExit):
        settings.check_live_port()


def test_check_live_port_accepts_live_port(monkeypatch):
    monkeypatch.setattr(settings, "IBKR_PORT", 7496)
    settings.check_live_port()  # must not raise


def test_badge_text_paper_account():
    from ui.main_window import conn_badge_text

    text, _color = conn_badge_text(account_id="DU123456", account_type="INDIVIDUAL")
    assert text == "● Paper"


def test_badge_text_demo_account_type():
    from ui.main_window import conn_badge_text

    text, _color = conn_badge_text(account_id="U123456", account_type="DEMO")
    assert text == "● Paper"


def test_badge_text_live_account():
    from ui.main_window import conn_badge_text

    text, _color = conn_badge_text(account_id="U123456", account_type="INDIVIDUAL")
    assert text == "● Live"


def test_badge_text_unknown_account_type_still_live():
    # Port 7496 is fail-fast verified at startup, so an unknown account type
    # on the live port is still live — never paper.
    from ui.main_window import conn_badge_text

    text, _color = conn_badge_text(account_id="U123456", account_type=None)
    assert text == "● Live"
