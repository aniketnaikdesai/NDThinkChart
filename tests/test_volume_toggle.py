import pytest
from ui.chart_panel import ChartPanel

# RC-4a: the D10 volume affordance is the checkable text label "Volume" at the
# top left of the volume panel — not an eye icon or bar glyph.

def test_T27_T01_volume_toggle_is_checkable_text_label(qapp):
    """T27-T01 / RC-4a: affordance is the text label 'Volume', and checkable."""
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    assert hasattr(panel, "_volume_toggle")
    toggle = panel._volume_toggle
    assert toggle.text() == "Volume"
    # No eye icon or bar glyph in the user-facing label (RC-4a).
    assert "👁" not in toggle.text()
    assert toggle.isCheckable()
    panel.hide()
    panel.close()


def test_T27_T02_volume_toggle_hides_and_expands_price(qapp):
    """T27-T02 / AC-D10.1: toggling off hides volume + expands price; on restores."""
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    toggle = panel._volume_toggle
    price_h_before = panel.price_plot.height()
    # Hide
    toggle.setChecked(False)
    qapp.processEvents()
    assert not panel.volume_plot.isVisible()
    assert not panel.volume_plot.getAxis('right').isVisible()
    # Price should expand (height larger)
    price_h_hidden = panel.price_plot.height()
    assert price_h_hidden > price_h_before
    # Show again
    toggle.setChecked(True)
    qapp.processEvents()
    assert panel.volume_plot.isVisible()
    assert panel.volume_plot.getAxis('right').isVisible()
    assert panel.price_plot.height() < price_h_hidden
    panel.hide()
    panel.close()


def test_T27_T03_volume_toggle_default_visible_no_bars(qapp):
    """T27-T03 / AC-D10.2: default checked/visible and no error with empty bars."""
    panel = ChartPanel()
    panel.resize(900, 600)
    panel.show()
    qapp.processEvents()
    toggle = panel._volume_toggle
    assert toggle.isChecked() is True
    assert panel.volume_plot.isVisible()
    # No bars loaded, toggling should not error
    try:
        toggle.setChecked(False)
        qapp.processEvents()
        assert not panel.volume_plot.isVisible()
        toggle.setChecked(True)
        qapp.processEvents()
        assert panel.volume_plot.isVisible()
    except Exception as e:
        pytest.fail(f"should not raise {e}")
    panel.hide()
    panel.close()
