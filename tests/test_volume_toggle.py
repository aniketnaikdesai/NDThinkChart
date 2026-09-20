import pytest
from ui.chart_panel import ChartPanel

def test_volume_toggle_exists_and_default_visible(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    assert hasattr(panel, "_volume_toggle")
    toggle = panel._volume_toggle
    assert toggle.isVisible()
    assert toggle.isCheckable()
    assert toggle.isChecked() is True
    assert panel.volume_plot.isVisible()
    panel.hide()
    panel.close()

def test_volume_toggle_hides_and_expands_price(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    toggle = panel._volume_toggle
    price_h_before = panel.price_plot.height()
    # Hide
    toggle.setChecked(False)
    qapp.processEvents()
    assert not panel.volume_plot.isVisible()
    # Price should expand (height larger)
    price_h_hidden = panel.price_plot.height()
    assert price_h_hidden >= price_h_before
    # Show again
    toggle.setChecked(True)
    qapp.processEvents()
    assert panel.volume_plot.isVisible()
    panel.hide()
    panel.close()

def test_volume_toggle_with_no_bars(qapp):
    panel = ChartPanel()
    panel.resize(900,600)
    panel.show()
    qapp.processEvents()
    toggle = panel._volume_toggle
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
