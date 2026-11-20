"""D92 / S-P28-13 — the app describes what it does, honestly.

NDThinkChart is a read-only market-data client that places no orders. The
window title, the port guard's refusal message and the three guide files say
so, and the port guard is described as a *configuration* check — it verifies
the configured port only, never the TWS account behind it. The port policy is
unchanged: ``LIVE_PORT`` is 7496 and any other port is refused (A239: words
only — no behaviour, no account check).

DG136 names the class this suite fences: four places describing one thing,
drifting independently. Each statement is asserted where it is produced, and
the retired-claim grep is scoped to the six live files (FI-P28-2) — historical
records (``docs/README.md``, ``docs/archive/**``, ``docs/D55_*``,
``docs/build/**``) are not read as failures and are not edited.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from config import settings

REPO_ROOT = Path(__file__).resolve().parents[1]

TITLE = "NDThinkChart \u2014 read-only market data"
GUIDES = ("usage.md", "USAGE.md", "USAGE.txt")
# FI-P28-2: exactly these six live files — the grep's scope is the contract.
LIVE_FILES = (
    "usage.md",
    "USAGE.md",
    "USAGE.txt",
    "ui/main_window.py",
    "config/settings.py",
    "main.py",
)
RETIRED_CLAIMS = ("trades live only", "trading terminal")


def test_p28_t10_01_window_title_is_the_one_owner_string(qapp):
    """Case (a): the exact title, at its source and on a real window."""
    from ui.main_window import MainWindow

    source = inspect.getsource(MainWindow.__init__)
    assert f'setWindowTitle("{TITLE}")' in source

    window = MainWindow()
    try:
        assert window.windowTitle() == TITLE
    finally:
        window.deleteLater()
        qapp.processEvents()


def test_p28_t10_02_port_guard_states_what_the_app_is(monkeypatch):
    """Case (b): the refusal is produced by check_live_port, not a doc."""
    monkeypatch.setattr(settings, "IBKR_PORT", 7497)
    monkeypatch.setattr(settings, "_PORT_PARSE_ERROR", None)

    with pytest.raises(SystemExit) as excinfo:
        settings.check_live_port()

    message = str(excinfo.value)
    assert "read-only" in message
    assert "places no orders" in message
    assert "configured port" in message

    # The port policy and the SystemExit shape are unchanged (A239).
    assert settings.LIVE_PORT == 7496
    assert isinstance(excinfo.value.code, str)


def test_p28_t10_03_no_retired_claim_in_the_six_live_files():
    """Case (c): the scoped grep — zero occurrences, exactly six files."""
    for name in LIVE_FILES:
        text = (REPO_ROOT / name).read_text(encoding="utf-8").lower()
        for claim in RETIRED_CLAIMS:
            assert claim not in text, f"{claim!r} still in {name}"


def test_p28_t10_04_guides_are_byte_identical_and_say_what_the_app_is():
    """Case (d): one wording in three files; the port truth kept."""
    assert (REPO_ROOT / "usage.md").read_bytes() == (
        REPO_ROOT / "USAGE.md"
    ).read_bytes()

    for name in GUIDES:
        text = (REPO_ROOT / name).read_text(encoding="utf-8")
        assert "places no orders" in text, name
        assert "refuses any other port" in text, name
        assert "live TWS session" in text, name
        assert "configuration check" in text, name


def test_p28_t10_05_d65_badge_wording_untouched():
    """Case (e): the D65 connection badge is outside this task's edits."""
    from ui import main_window

    assert list(inspect.signature(main_window.conn_badge_text).parameters) == [
        "monitoring_paused"
    ]
    assert main_window.conn_badge_text() == ("\u25cf Connected", "#34d399")
    assert main_window.conn_badge_text(monitoring_paused=True) == (
        "Monitoring paused \u2014 TWS disconnected",
        "#fbbf24",
    )

    source = inspect.getsource(main_window.conn_badge_text)
    assert "\u25cf Connected" in source
    assert "Monitoring paused \u2014 TWS disconnected" in source
