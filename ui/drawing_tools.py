"""ui/drawing_tools.py — the drawing tool names shared by the router and the views.

A leaf module: no Qt, no renderer. The names survive the pyqtgraph removal
(P6-13) because the LWC router and driver need the same vocabulary the old
drawing overlay used (``DRAWING_TOOLS`` / ``TOOL_CURSOR``). Keeping them here
lets ``ui/chart_mouse_router.py`` and ``ui/lwc_view.py`` share one source
without importing a deleted renderer.
"""

TOOL_CURSOR = "cursor"
DRAWING_TOOLS = ("trendline", "horizontal", "zone", "fibonacci", "measure")
