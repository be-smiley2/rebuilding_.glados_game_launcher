"""Aperture Science inspired color palette."""
from __future__ import annotations


class ApertureTheme:
    """Centralized Aperture Science colour palette and typography."""

    # Core surfaces
    PRIMARY_BG = "#0f171f"
    SECONDARY_BG = "#141f2a"
    PANEL_BG = "#182532"
    ACCENT_BG = "#1f3040"

    # Brand accents
    GLADOS_ORANGE = "#ff9b42"
    WHEATLEY_BLUE = "#4fc3f7"
    PORTAL_BLUE = "#5ad1ff"
    PORTAL_ORANGE = "#ffb76b"

    # Text colours
    TEXT_PRIMARY = "#f4f6f8"
    TEXT_SECONDARY = "#c0ccd6"
    TEXT_ACCENT = "#ffe4b5"
    TEXT_MUTED = "#7f96aa"

    # Status colours
    SUCCESS_GREEN = "#5bd975"
    ERROR_RED = "#ff6b6b"
    WARNING_YELLOW = "#ffd166"

    # Interactive states
    BUTTON_NORMAL = "#223447"
    BUTTON_HOVER = "#2f4c66"
    BUTTON_ACTIVE = "#3a5f7d"

    BORDER_LIGHT = "#3c5064"
    BORDER_DARK = "#0b1118"

    # Typography
    FONT_FAMILY = "Arial"
    FONT_BASE = (FONT_FAMILY, 10)
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_BUTTON = (FONT_FAMILY, 10, "bold")
    FONT_SUBHEADING = (FONT_FAMILY, 12, "bold")
    FONT_HEADING = (FONT_FAMILY, 17, "bold")


__all__ = ["ApertureTheme"]
