"""
chart_mouse_router.py
Single routing point between the price plot's ViewBox and the chart overlays.

The router owns one explicit state, ``RouterMode`` (ESC-002, AC-D3.7–AC-D3.9).
Every high-level handler begins with a guard clause that dispatches on
``_active_mode`` — not on three independent overlay probes — and ``_active_mode``
is the sole source of truth for gesture precedence. Because a single enum value
can only hold one member, ``DRAWING`` and ``ZOOMING`` are mutually exclusive by
construction.

The overlay pointers (``drawing`` / ``alarm`` / ``zoom``) are properties whose
setters re-derive ``_active_mode`` from the wired overlays (RC-3); this keeps
the five preserved router tests — which wire overlays by direct attribute
assignment and never call an intent API — working verbatim.

Alarms get first refusal on a press in ``IDLE`` (so alarm lines can be dragged
and click-to-create works in alarm mode) unless a drawing tool is active, in
which case the drawing overlay owns the gesture.

``ui/drawing_overlay.py`` already handles tool-arm + draft-discard via
``set_tool(TOOL_CURSOR)``; the router simply calls it so no half-drawn artefact
is left behind (TR-4/TR-7).
"""

from enum import Enum, auto

from ui.drawing_overlay import DRAWING_TOOLS, TOOL_CURSOR


class RouterMode(Enum):
    IDLE = auto()            # default; cursor/pan; alarm & drawing still hit-tested
    DRAWING = auto()         # a drawing tool is armed (draft may be in progress)
    ZOOMING = auto()         # magnifier active; rubber-band selection armed
    ALARM_PLACING = auto()   # alarm placement mode armed


class ChartMouseRouter:
    def __init__(self):
        self._drawing = None
        self._alarm = None
        self._zoom = None
        self._active_mode = RouterMode.IDLE

    # ── Overlay wiring (RC-3) ──────────────────────────────────────────────────
    #
    # ``drawing``/``alarm``/``zoom`` are properties backed by private fields; the
    # setters store the overlay and re-derive the mode. This is the wiring
    # boundary: hot handlers never re-derive, they only dispatch on the mode.

    @property
    def drawing(self):
        return self._drawing

    @drawing.setter
    def drawing(self, overlay):
        self._drawing = overlay
        self._reconcile_mode_from_overlays()

    @property
    def alarm(self):
        return self._alarm

    @alarm.setter
    def alarm(self, overlay):
        self._alarm = overlay
        self._reconcile_mode_from_overlays()

    @property
    def zoom(self):
        return self._zoom

    @zoom.setter
    def zoom(self, overlay):
        self._zoom = overlay
        self._reconcile_mode_from_overlays()

    @property
    def active_mode(self) -> RouterMode:
        return self._active_mode

    # ── Mode derivation / synchronisation (RC-3) ───────────────────────────────

    @staticmethod
    def _probe(overlay, *names) -> bool:
        """Call the first available accessor on ``overlay``, defensively.

        The preserved test ``FakeOverlay`` implements only ``tool_active()``, so
        every probe must tolerate a missing accessor (and a raising one).
        """
        if overlay is None:
            return False
        for name in names:
            fn = getattr(overlay, name, None)
            if callable(fn):
                try:
                    return bool(fn())
                except Exception:
                    return False
        return False

    def _drawing_active(self) -> bool:
        return self._probe(self._drawing, "tool_active")

    def _reconcile_mode_from_overlays(self) -> RouterMode:
        """Derive ``_active_mode`` with precedence DRAWING > ZOOMING > ALARM_PLACING > IDLE."""
        if self._drawing_active():
            self._active_mode = RouterMode.DRAWING
        elif self._probe(self._zoom, "is_active"):
            self._active_mode = RouterMode.ZOOMING
        elif self._probe(self._alarm, "is_alarm_mode"):
            self._active_mode = RouterMode.ALARM_PLACING
        else:
            self._active_mode = RouterMode.IDLE
        return self._active_mode

    # ── Overlay side-effect helpers ────────────────────────────────────────────

    def _set_tool(self, tool) -> None:
        drawing = self._drawing
        fn = getattr(drawing, "set_tool", None) if drawing is not None else None
        if callable(fn):
            try:
                fn(tool)
            except Exception:
                pass

    def _clear_drawing_tool(self) -> None:
        """Discard any in-progress draft and return the drawing tool to Cursor."""
        self._set_tool(TOOL_CURSOR)

    def _set_alarm_mode(self, enabled: bool) -> None:
        alarm = self._alarm
        fn = getattr(alarm, "set_alarm_mode", None) if alarm is not None else None
        if callable(fn):
            try:
                fn(bool(enabled))
            except Exception:
                pass

    def _deactivate_zoom(self) -> None:
        """Exit ZOOMING: ``zoom.set_active(False)`` plus an explicit ``cancel()``."""
        zoom = self._zoom
        if zoom is None:
            return
        set_active = getattr(zoom, "set_active", None)
        if callable(set_active):
            try:
                set_active(False)
            except Exception:
                pass
        cancel = getattr(zoom, "cancel", None)
        if callable(cancel):
            try:
                cancel()
            except Exception:
                pass

    # ── Intent helpers (normative transition table) ────────────────────────────

    def enter_zoom(self) -> bool:
        """TR-2 / TR-4 / TR-9.

        Returns ``False`` (no mode change, overlays untouched) when alarm
        placement is armed — the magnifier is refused (AC-D3.9). Otherwise any
        in-progress draw draft is discarded and the router enters ``ZOOMING``.
        """
        if self._active_mode == RouterMode.ALARM_PLACING:
            # TR-9 REFUSE: do not enter ZOOMING, do not touch the zoom overlay,
            # leave the pending alarm placement intact.
            return False
        if self._active_mode == RouterMode.DRAWING:
            # TR-4: cancel the in-progress drawing and discard the draft.
            self._clear_drawing_tool()
        if self._zoom is not None:
            self._zoom.set_active(True)
        self._active_mode = RouterMode.ZOOMING
        return True

    def enter_drawing(self, tool) -> RouterMode:
        """TR-1 / TR-5 / TR-8 / TR-10.

        A real drawing tool exits ``ZOOMING`` (``set_active(False)`` + ``cancel()``,
        TR-5) or ``ALARM_PLACING`` (TR-8) and enters ``DRAWING``. The Cursor merely
        disarms a drawing tool (TR-10) and never disturbs zoom or alarm placement.
        """
        tool = tool if tool in DRAWING_TOOLS else TOOL_CURSOR
        if tool == TOOL_CURSOR:
            self._clear_drawing_tool()
            if self._active_mode == RouterMode.DRAWING:
                self._active_mode = RouterMode.IDLE
            return self._active_mode
        if self._active_mode == RouterMode.ZOOMING:
            self._deactivate_zoom()
        elif self._active_mode == RouterMode.ALARM_PLACING:
            self._set_alarm_mode(False)
        self._set_tool(tool)
        self._active_mode = RouterMode.DRAWING
        return self._active_mode

    def enter_alarm_placing(self) -> RouterMode:
        """TR-3 / TR-6 / TR-7.

        Alarm placement exits ``ZOOMING`` (TR-6 — not blocked by an active zoom)
        or discards a drawing draft (TR-7) before arming.
        """
        if self._active_mode == RouterMode.ZOOMING:
            self._deactivate_zoom()
        elif self._active_mode == RouterMode.DRAWING:
            self._clear_drawing_tool()
        self._set_alarm_mode(True)
        self._active_mode = RouterMode.ALARM_PLACING
        return self._active_mode

    def exit_to_idle(self) -> RouterMode:
        """Deactivate the magnifier and return the router to ``IDLE`` (TR-11/12)."""
        self._deactivate_zoom()
        self._active_mode = RouterMode.IDLE
        return self._active_mode

    # ── Guard-clause dispatch ──────────────────────────────────────────────────

    def view_mouse_press(self, ev) -> bool:
        mode = self._active_mode
        if mode == RouterMode.ZOOMING:
            return bool(self._zoom is not None and self._zoom.view_mouse_press(ev))
        if mode == RouterMode.DRAWING:
            return bool(self._drawing is not None and self._drawing.view_mouse_press(ev))
        if mode == RouterMode.ALARM_PLACING:
            return bool(self._alarm is not None and self._alarm.view_mouse_press(ev))
        # IDLE — alarm first; a miss falls through to drawing.
        if not self._drawing_active() and self._alarm is not None:
            if self._alarm.view_mouse_press(ev):
                return True
        if self._drawing is not None:
            return bool(self._drawing.view_mouse_press(ev))
        return False

    def view_mouse_drag(self, ev) -> bool:
        mode = self._active_mode
        if mode == RouterMode.ZOOMING:
            return bool(self._zoom is not None and self._zoom.view_mouse_drag(ev))
        if mode == RouterMode.DRAWING:
            return bool(self._drawing is not None and self._drawing.view_mouse_drag(ev))
        if mode == RouterMode.ALARM_PLACING:
            return bool(self._alarm is not None and self._alarm.view_mouse_drag(ev))
        # IDLE — alarm first; a miss falls through to drawing.
        if not self._drawing_active() and self._alarm is not None:
            if self._alarm.view_mouse_drag(ev):
                return True
        if self._drawing is not None:
            return bool(self._drawing.view_mouse_drag(ev))
        return False

    def view_mouse_click(self, ev) -> bool:
        mode = self._active_mode
        if mode == RouterMode.ZOOMING:
            # zoom only (returns False; the view is unchanged)
            return bool(self._zoom is not None and self._zoom.view_mouse_click(ev))
        if mode == RouterMode.DRAWING:
            # RC-4b: a click in DRAWING reaches the drawing overlay only.
            return bool(self._drawing is not None and self._drawing.view_mouse_click(ev))
        if mode == RouterMode.ALARM_PLACING:
            return bool(self._alarm is not None and self._alarm.view_mouse_click(ev))
        # IDLE — prefers alarm, then drawing.
        if self._alarm is not None:
            if self._alarm.view_mouse_click(ev):
                return True
        if self._drawing is not None:
            return bool(self._drawing.view_mouse_click(ev))
        return False
