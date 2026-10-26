"""Phase 0 spike static contract check (throwaway, NOT part of tests/).

Verifies each of the 9 API behaviours B1..B9 has a named evidence site in
spikes/lwc/index.html by asserting the real v5-shaped call strings are
present. Plain stdlib python only: no Qt, no DB, no app imports.
Run: python3 spikes/lwc/spike_probe.py
"""
import pathlib
import sys

HTML = pathlib.Path(__file__).with_name("index.html").read_text()

# behaviour -> list of v5-shaped call tokens that must appear in index.html
BEHAVIOURS = {
    "B1-host-create": ["LightweightCharts.createChart"],
    "B2-candles-setData": ["addCandlestickSeries", "setData"],
    "B3-live-update": ["series.update", ".update({ time:"],
    "B4-timescale-whitespace": ["timeScale().applyOptions", "barSpacing"],
    "B5-tz-formatter": ["timeFormatter", "TZ_OFFSET_S"],
    "B6-multi-pane": ["addHistogramSeries", "addLineSeries", "chart.panes"],
    "B7-crosshair-markers": ["subscribeCrosshairMove", "setMarkers"],
    "B8-price-lines": ["createPriceLine"],
    "B9-bridge-batch": ["{ v: 1, ops:", "bridgeBatch"],
}

missing = {}
for behaviour, tokens in BEHAVIOURS.items():
    absent = [t for t in tokens if t not in HTML]
    if absent:
        missing[behaviour] = absent

if missing:
    for behaviour, absent in missing.items():
        print(f"MISSING {behaviour}: {absent}")
    sys.exit(1)
print(f"SPIKE-PROBE-OK: all {len(BEHAVIOURS)} behaviours evidenced in index.html")
