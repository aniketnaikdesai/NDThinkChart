# Debug Log

## Issue: RuntimeError: wrapped C/C++ object of type InfiniteLine has been deleted

**Date:** 2026-09-19
**Linked Task:** T2 (Render pre/post session shading in chart) - related to drawing overlay interactions
**Root Cause Classification:** `code_bug`

### Diagnosis

The error occurs in pyqtgraph's `GraphicsScene.sendDragEvent()` when it tries to call `mouseDragEvent` on an `InfiniteLine` that has been deleted:

```
File ".../pyqtgraph/graphicsItems/InfiniteLine.py", line 398, in mouseDragEvent
    self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))
RuntimeError: wrapped C/C++ object of type InfiniteLine has been deleted
```

**Root Cause:** In `DrawingOverlay._apply_drag()` (line 567-610), when dragging a drawing (horizontal line, fibonacci levels), the code calls `_restore_drawing_style(drawing)` at line 607. This method:
1. Calls `_remove_items(key)` which removes all pyqtgraph items for that drawing from the plot
2. Calls `_build_items(drawing)` which creates new items

However, pyqtgraph's `GraphicsScene` internally tracks the currently dragged item in its `dragItem` attribute. When the old `InfiniteLine` is removed from the plot and its Python references are cleared, the C++ object gets deleted. But the scene's `dragItem` still points to the now-deleted object. On the next mouse move event, the scene tries to call `mouseDragEvent` on the deleted object, causing the RuntimeError.

**Affected Drawing Types:**
- `horizontal` - uses `pg.InfiniteLine`
- `fibonacci` - uses multiple `pg.InfiniteLine` items (one per level)

**Unaffected Drawing Types:**
- `trendline`, `measure` - use `pg.PlotDataItem` (updated via `setData`)
- `zone` - uses `pg.LinearRegionItem` (updated via `setRegion`)

**Note:** `AlarmOverlay._restyle_alarm()` correctly updates items in place using `line.setValue()` and doesn't have this issue.

### Fix Applied

Modified `DrawingOverlay._apply_drag()` to update existing items in place instead of calling `_restore_drawing_style()` which removes and recreates them. For each drawing kind:
- `horizontal`: Update the existing `InfiniteLine` position via `setPos()`
- `fibonacci`: Update each `InfiniteLine` position via `setPos()`
- `trendline`, `measure`: Update `PlotDataItem` via `setData()`
- `zone`: Update `LinearRegionItem` via `setRegion()`

Also added safety checks in `_remove_items()` and `_clear_all_items()` to clear the scene's `dragItem` if it matches an item being removed.

### Tests Re-run

- All existing tests in `tests/test_drawing_overlay.py` and `tests/test_drawing_interaction.py` pass (26 tests)
- Full pytest suite: 311 tests passed
- Manual runtime verification: Application starts without the "wrapped C/C++ object has been deleted" error

### Result

**Status: READY_FOR_BUILD_RESUME**