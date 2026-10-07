"""D21-04 / VIS-D21 — shared primitives (``ui/visual_conventions.py``).

Covers the two user-confirmed D21 conventions:

* ``VIS-D21.1`` — :class:`DiagonalStrikeButton` paints a single straight
  top-left -> bottom-right line over the text area when ``struck`` is set, and a
  checkable button auto-strikes while unchecked / unstrikes when checked.  The
  control stays clickable while struck.
* ``VIS-D21.2`` — :func:`set_button_active` toggles the ``active`` dynamic
  property and the resolved style differs between active and inactive; the
  shared :data:`VIS_D21_2_STYLESHEET` targets the toolbar ``objectName`` and the
  ``:checked`` / ``[active="true"]`` selectors, so it is independent of scroll
  position inside the D19 ``ToolbarScroll`` wrapper.

Runs on the offscreen Qt platform via the shared ``qapp`` fixture.  The paint
checks render the widget into an image and compare pixels, so they verify what
is actually drawn rather than only the ``struck`` flag.
"""

import pytest
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import (
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.visual_conventions import (
    ACTIVE_PROPERTY,
    TOOLBAR_ACTIVE_STYLESHEET,
    TOOLBAR_OBJECT_NAME,
    VIS_D21_2_STYLESHEET,
    DiagonalStrikeButton,
    set_button_active,
)


# ── render helpers ───────────────────────────────────────────────────────────

def _render(widget: QWidget) -> QImage:
    """Render *widget* into an ARGB image (offscreen, no show() needed)."""
    widget.ensurePolished()
    if widget.width() <= 0 or widget.height() <= 0:
        size = widget.sizeHint()
        widget.resize(max(size.width(), 80), max(size.height(), 28))
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    widget.render(image)
    return image


def _pixels(image: QImage) -> bytes:
    """Raw ARGB32 bytes for exact image comparison."""
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    ptr = image.constBits()
    ptr.setsize(image.sizeInBytes())
    return bytes(ptr)


def _images_differ(a: QImage, b: QImage) -> bool:
    if a.size() != b.size():
        return True
    return _pixels(a) != _pixels(b)


def _changed_near(a: QImage, b: QImage, x: int, y: int, radius: int = 2) -> int:
    """Count differing pixels within *radius* of (x, y) between two images."""
    changed = 0
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            px, py = x + dx, y + dy
            if 0 <= px < a.width() and 0 <= py < a.height():
                if a.pixelColor(px, py) != b.pixelColor(px, py):
                    changed += 1
    return changed


# ── D21-04-T01 / VIS-D21.1 — diagonal strike ─────────────────────────────────

def test_D21_04_T01_diagonal_strike(qapp):
    """T01 / VIS-D21.1: struck flag, painted TL->BR line, auto-strike, clickable."""
    btn = DiagonalStrikeButton("Volume")
    btn.resize(120, 32)

    # Default: not struck, and no diagonal line is painted.
    assert btn.struck is False
    assert btn.is_struck() is False
    unstruck = _render(btn)

    # Setting struck paints the line.
    btn.struck = True
    assert btn.struck is True
    struck = _render(btn)
    assert _images_differ(unstruck, struck), "struck button rendered identically"

    # The line runs top-left -> bottom-right and spans the text area.
    line = btn.strike_line()
    assert line.x1() < line.x2(), (line.x1(), line.x2())
    assert line.y1() < line.y2(), (line.y1(), line.y2())
    area = btn.text_area_rect()
    assert area.contains(line.p1()) and area.contains(line.p2()), (area, line)

    # The changed pixels follow that TL->BR line (not an arbitrary region).
    samples = 24
    hits = 0
    for i in range(samples + 1):
        t = i / samples
        x = round(line.x1() + (line.x2() - line.x1()) * t)
        y = round(line.y1() + (line.y2() - line.y1()) * t)
        if _changed_near(unstruck, struck, x, y) > 0:
            hits += 1
    assert hits >= int(samples * 0.75), (hits, samples)

    # Still clickable while struck.
    fired: list[bool] = []
    btn.clicked.connect(lambda: fired.append(True))
    btn.click()
    assert fired == [True], "struck button is no longer clickable"

    # Unstruck again -> back to the unstruck rendering.
    btn.struck = False
    assert btn.struck is False
    assert not _images_differ(unstruck, _render(btn))

    # Checkable auto-strike: unchecked -> struck, checked -> unstruck.
    chk = DiagonalStrikeButton("Volume")
    chk.resize(120, 32)
    chk.setCheckable(True)
    assert chk.struck is True, "unchecked checkable button should auto-strike"
    chk.setChecked(True)
    assert chk.struck is False, "checked checkable button should unstrike"
    chk.setChecked(False)
    assert chk.struck is True, "unchecked checkable button should re-strike"

    # Explicit set_struck alias works too.
    chk.set_struck(False)
    assert chk.struck is False


# ── D21-04-T02 / VIS-D21.2 — active highlight helper ─────────────────────────

def _toolbar_with_button(button: QPushButton) -> QWidget:
    """A ``#MainToolbar`` container carrying the shared stylesheet + *button*."""
    toolbar = QWidget()
    toolbar.setObjectName(TOOLBAR_OBJECT_NAME)
    toolbar.setStyleSheet(VIS_D21_2_STYLESHEET)
    layout = QVBoxLayout(toolbar)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.addWidget(button)
    toolbar.resize(160, 60)
    button.setFixedSize(140, 32)
    return toolbar


def test_D21_04_T02_set_button_active(qapp):
    """T02 / VIS-D21.2: dynamic property set/cleared and style differs."""
    toolbar = _toolbar_with_button(QPushButton("Studies"))
    btn = toolbar.findChild(QPushButton)
    assert btn is not None

    # Inactive by default: property unset, inactive rendering captured.
    assert not btn.property(ACTIVE_PROPERTY)
    inactive = _render(btn)

    # Active: property True and a visibly different resolved style.
    set_button_active(btn, True)
    assert btn.property(ACTIVE_PROPERTY) is True
    active = _render(btn)
    assert _images_differ(inactive, active), (
        "active style did not differ from inactive"
    )

    # Inactive again: property cleared and the style returns to inactive.
    set_button_active(btn, False)
    assert btn.property(ACTIVE_PROPERTY) is False
    restored = _render(btn)
    assert not _images_differ(inactive, restored), (
        "style did not return to the inactive form"
    )


# ── D21-04-T03 / VIS-D21.2 — shared stylesheet targets + scroll independence ─

def test_D21_04_T03_stylesheet_targets_toolbar_and_selectors(qapp):
    """T03 / VIS-D21.2: objectName + :checked / [active=true] selectors."""
    sheet = VIS_D21_2_STYLESHEET

    # Targets the toolbar objectName, not a positional/scroll structure.
    assert f"#{TOOLBAR_OBJECT_NAME}" in sheet
    assert ":checked" in sheet
    assert '[active="true"]' in sheet
    assert "QScrollArea" not in sheet, "stylesheet must not depend on scroll position"

    # The constant is the single source of truth for its aliases.
    assert TOOLBAR_ACTIVE_STYLESHEET == VIS_D21_2_STYLESHEET

    # :checked resolves on a descendant button even when nested in the D19
    # ToolbarScroll wrapper (objectName-keyed, so scroll position is irrelevant).
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    toolbar = QWidget()
    toolbar.setObjectName(TOOLBAR_OBJECT_NAME)
    toolbar.setStyleSheet(sheet)
    scroll.setWidget(toolbar)
    scroll.resize(220, 70)

    btn = QPushButton("Ext Hours")
    btn.setCheckable(True)
    layout = QVBoxLayout(toolbar)
    layout.addWidget(btn)
    toolbar.resize(200, 50)
    btn.setFixedSize(140, 32)

    btn.setChecked(False)
    unchecked = _render(btn)
    btn.setChecked(True)
    checked = _render(btn)
    assert _images_differ(unchecked, checked), (
        ":checked highlight not applied inside the scroll wrapper"
    )

    # ...and [active="true"] resolves on the same descendant button.
    plain = QPushButton("Alarms")
    layout.addWidget(plain)
    plain.setFixedSize(140, 32)
    inactive = _render(plain)
    set_button_active(plain, True)
    active = _render(plain)
    assert _images_differ(inactive, active), (
        '[active="true"] highlight not applied inside the scroll wrapper'
    )
