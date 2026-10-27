"""P6-T13 removal gate — the pyqtgraph engine is gone, not merely unused.

Written by the Orchestrator at the owner's instruction to close the removal.
Asserts the *removal*, so a future revert or a half-applied deletion fails here
rather than being discovered in the running app.

Scope note: this is a static/import gate. It deliberately does not assert chart
behaviour — that lives in the LWC suites. The coverage this phase retired is
recorded in docs/lwc_parity_matrix.md under "Retired coverage (P6-T13)".
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

#: Modules deleted with the engine. Each was pyqtgraph-only.
DELETED_MODULES = (
    "ui.chart_panel",
    "ui.candlestick_item",
    "ui.alarm_overlay",
    "ui.drawing_overlay",
    "ui.event_marker_overlay",
    "ui.zoom_overlay",
    "ui.overlays.base",
    "ui.overlays.gap_overlay",
    "ui.overlays.ict_overlay",
    "ui.overlays.session_overlay",
    "ui.overlays.vix_overlay",
)

#: Suites retired with the engine or with the oracle they depended on.
RETIRED_SUITES = (
    "test_d24_chart_quality.py",
    "test_candle_spacing.py",
    "test_candlestick_wick.py",
    "test_chart_dpi.py",
    "test_crosshair_chip_bounds.py",
    "test_crosshair_axis_lane.py",
    "test_chart_crosshair.py",
    "test_volume_width.py",
    "test_zoom_overlay.py",
    "test_zoom_behavior.py",
)


def test_pyqtgraph_is_not_importable():
    """The dependency is gone, not just unreferenced."""
    assert importlib.util.find_spec("pyqtgraph") is None, (
        "pyqtgraph is still importable — it must be uninstalled, not merely "
        "removed from requirements.txt"
    )


def test_pyqtgraph_not_in_requirements():
    text = (REPO / "requirements.txt").read_text(encoding="utf-8")
    assert "pyqtgraph" not in text


@pytest.mark.parametrize("module", DELETED_MODULES)
def test_deleted_modules_are_absent(module):
    assert importlib.util.find_spec(module) is None, f"{module} still resolves"


@pytest.mark.parametrize("suite", RETIRED_SUITES)
def test_retired_suites_are_absent(suite):
    assert not (REPO / "tests" / suite).exists(), f"{suite} still present"


def test_no_production_module_imports_pyqtgraph():
    """A stray import would fail at runtime even though the package is gone."""
    offenders = []
    for path in list((REPO / "ui").rglob("*.py")) + list(
        (REPO / "services").rglob("*.py")
    ):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "import pyqtgraph" in text or "from pyqtgraph" in text:
            offenders.append(str(path.relative_to(REPO)))
    assert not offenders, offenders


def test_the_seam_resolves_the_lwc_engine(qapp):
    """The single engine that remains is the LWC driver."""
    from ui.chart_view import create_chart_view

    view = create_chart_view(tz_offset=0, editable=True)
    try:
        assert getattr(view, "ENGINE_NAME", None) == "lwc"
    finally:
        view.deleteLater()
