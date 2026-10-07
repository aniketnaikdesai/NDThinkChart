"""Shared VIS-D21 visual conventions (Batch 15).

Single source of truth for the two D21 UI conventions, reused by the toolbar
(D21.7/D21.8), the watchlist (D21.11), the volume toggle (D21.12) and the right
dock (D21.13):

* :class:`DiagonalStrikeButton` -- ``VIS-D21.1``: a ``QPushButton`` that paints a
  single straight top-left -> bottom-right line over its text area when
  ``struck`` is set.  A checkable button strikes itself automatically while it
  is unchecked (the "hidden/off" state) and unstrikes when checked.
* :data:`VIS_D21_2_STYLESHEET` -- ``VIS-D21.2``: the shared toolbar stylesheet
  that gives an active/selected button a persistent, distinguishable highlight
  (a distinct filled background plus a border, per A41).  It is keyed off the
  toolbar's ``objectName`` (``#MainToolbar``) and the ``:checked`` pseudo-state /
  ``[active="true"]`` dynamic property, so it is independent of scroll position
  inside the D19 ``ToolbarScroll`` wrapper.
* :func:`set_button_active` -- the ``VIS-D21.2`` helper that toggles the
  ``active`` Qt dynamic property and repolishes the widget so the stylesheet
  re-evaluates.  The property is assertable independently of painting.

This module is intentionally a leaf: it imports only PyQt6 and has no
dependencies on other project modules.
"""

from __future__ import annotations

from PyQt6.QtCore import QLineF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPalette, QPen
from PyQt6.QtWidgets import QPushButton, QWidget

#: ``objectName`` of the toolbar that owns the ``VIS-D21.2`` stylesheet.  The
#: D19 wrapper puts the toolbar inside a ``QScrollArea``; selecting by this
#: objectName (rather than by position) keeps the highlight working at any
#: scroll position.
TOOLBAR_OBJECT_NAME = "MainToolbar"

#: ``VIS-D21.2`` dynamic property name (A41).  Assertable independently of
#: painting via ``button.property("active")``.
ACTIVE_PROPERTY = "active"

# ── A41 active-highlight colours (implementation detail; the outcome is the
#    requirement).  High contrast against the dark toolbar so the highlight is
#    clearly distinguishable from the inactive state (R40).
_ACTIVE_BACKGROUND = "#1f6feb"   # accent blue fill
_ACTIVE_BORDER = "#58a6ff"       # brighter accent border
_ACTIVE_TEXT = "#ffffff"         # readable text on the accent fill

#: The shared ``VIS-D21.2`` toolbar stylesheet.  Applied to the toolbar widget
#: (``#MainToolbar``) so it styles every descendant button:
#:
#: * ``:checked`` covers checkable toggles (sound / DOM / ext-hours / alarm mode)
#: * ``[active="true"]`` covers popup buttons driven by :func:`set_button_active`
#:
#: Inactive buttons are untouched, so the highlight is removed when inactive.
VIS_D21_2_STYLESHEET = (
    "#MainToolbar QPushButton:checked {\n"
    f"    background-color: {_ACTIVE_BACKGROUND};\n"
    f"    border: 1px solid {_ACTIVE_BORDER};\n"
    f"    color: {_ACTIVE_TEXT};\n"
    "}\n"
    '#MainToolbar QPushButton[active="true"] {\n'
    f"    background-color: {_ACTIVE_BACKGROUND};\n"
    f"    border: 1px solid {_ACTIVE_BORDER};\n"
    f"    color: {_ACTIVE_TEXT};\n"
    "}\n"
)

# Consumer-friendly aliases (the constant is the single source of truth).
TOOLBAR_ACTIVE_STYLESHEET = VIS_D21_2_STYLESHEET
ACTIVE_BUTTON_STYLESHEET = VIS_D21_2_STYLESHEET

#: Pen width (device pixels) of the ``VIS-D21.1`` strike line (A42: ~1-2px).
STRIKE_LINE_WIDTH = 2

#: Inset (px) of the strike line from the button edge so the line reads as a
#: strike across the label rather than sitting on the border.
_STRIKE_INSET = 3


def set_button_active(button: QWidget, active: bool) -> None:
    """Apply/remove the ``VIS-D21.2`` active highlight on *button*.

    Sets the ``active`` Qt dynamic property (so the state is assertable
    independently of painting) and repolishes the widget so the stylesheet
    re-evaluates.  The highlight is applied while *active* is true and removed
    when false.
    """
    button.setProperty(ACTIVE_PROPERTY, bool(active))
    style = button.style()
    style.unpolish(button)
    style.polish(button)
    button.update()


def apply_toolbar_stylesheet(toolbar: QWidget) -> None:
    """Append the shared ``VIS-D21.2`` stylesheet to *toolbar*'s own stylesheet.

    Idempotent, and preserves any existing stylesheet (e.g. the toolbar's dark
    background) instead of replacing it.  Prefer this over a bare
    ``setStyleSheet(VIS_D21_2_STYLESHEET)`` so the base look is not wiped.
    """
    current = toolbar.styleSheet()
    if VIS_D21_2_STYLESHEET.strip() in current:
        return
    combined = f"{current}\n{VIS_D21_2_STYLESHEET}".strip()
    toolbar.setStyleSheet(combined)


class DiagonalStrikeButton(QPushButton):
    """A ``QPushButton`` that can render the ``VIS-D21.1`` diagonal strike.

    When :attr:`struck` is true, :meth:`paintEvent` draws a single straight line
    from the top-left to the bottom-right of the button's text area, in the
    button's foreground colour, over the normal text/background.  The button
    stays fully interactive while struck.

    A **checkable** button strikes itself automatically while it is unchecked
    (the "hidden/off" state) and unstrikes when checked, so consumers only wire
    the normal ``toggled``/``clicked`` behaviour.
    """

    # Class-level default so paintEvent is safe even before __init__ completes.
    _struck: bool = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._struck = False
        self.toggled.connect(self._on_toggled)

    # ── struck state ─────────────────────────────────────────────────────────

    @property
    def struck(self) -> bool:
        """True while the diagonal strike is painted."""
        return self._struck

    @struck.setter
    def struck(self, value: bool) -> None:
        value = bool(value)
        if value != self._struck:
            self._struck = value
            self.update()

    def set_struck(self, value: bool) -> None:
        """Explicit setter mirroring the :attr:`struck` property."""
        self.struck = value

    def is_struck(self) -> bool:
        """Explicit getter mirroring the :attr:`struck` property."""
        return self._struck

    # ── auto-strike for checkable buttons ────────────────────────────────────

    def setCheckable(self, checkable: bool) -> None:  # noqa: N802 (Qt name)
        super().setCheckable(checkable)
        if checkable:
            self._sync_struck_to_checked()

    def setChecked(self, checked: bool) -> None:  # noqa: N802 (Qt name)
        super().setChecked(checked)
        # ``setChecked`` does not emit ``toggled`` when the state is unchanged
        # (e.g. an already-unchecked button), so sync explicitly as well.
        if self.isCheckable():
            self._sync_struck_to_checked()

    def _on_toggled(self, checked: bool) -> None:
        if self.isCheckable():
            self.struck = not checked

    def _sync_struck_to_checked(self) -> None:
        self.struck = not self.isChecked()

    # ── painting ─────────────────────────────────────────────────────────────

    def strike_line(self) -> QLineF:
        """Return the strike line in button-local coordinates (TL -> BR)."""
        rect = self.text_area_rect()
        return QLineF(rect.topLeft(), rect.bottomRight())

    def text_area_rect(self) -> QRectF:
        """The text area the strike spans (button rect inset from the border)."""
        return QRectF(self.rect()).adjusted(
            _STRIKE_INSET, _STRIKE_INSET, -_STRIKE_INSET, -_STRIKE_INSET
        )

    def strike_color(self) -> QColor:
        """The strike colour: the button's foreground (text) colour (A42)."""
        return self.palette().color(QPalette.ColorRole.ButtonText)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt name)
        super().paintEvent(event)
        if not self._struck:
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            pen = QPen(self.strike_color())
            pen.setWidth(STRIKE_LINE_WIDTH)
            pen.setCosmetic(True)  # device-pixel stable across DPI (High-DPI)
            painter.setPen(pen)
            painter.drawLine(self.strike_line())
        finally:
            painter.end()
