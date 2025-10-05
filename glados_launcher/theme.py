"""Aperture Science inspired color palette."""
from __future__ import annotations

from typing import Dict


class ApertureTheme:
    """Centralized Aperture Science colour palette and typography."""

    # Typography remains constant across modes
    FONT_FAMILY = "Arial"
    FONT_BASE = (FONT_FAMILY, 10)
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_BUTTON = (FONT_FAMILY, 10, "bold")
    FONT_SUBHEADING = (FONT_FAMILY, 12, "bold")
    FONT_HEADING = (FONT_FAMILY, 17, "bold")

    _COLOR_MODES: Dict[str, Dict[str, str]] = {
        "dark": {
            "PRIMARY_BG": "#0f171f",
            "SECONDARY_BG": "#141f2a",
            "PANEL_BG": "#182532",
            "ACCENT_BG": "#1f3040",
            "GLADOS_ORANGE": "#ff9b42",
            "WHEATLEY_BLUE": "#4fc3f7",
            "PORTAL_BLUE": "#5ad1ff",
            "PORTAL_ORANGE": "#ffb76b",
            "TEXT_PRIMARY": "#f4f6f8",
            "TEXT_SECONDARY": "#c0ccd6",
            "TEXT_ACCENT": "#ffe4b5",
            "TEXT_MUTED": "#7f96aa",
            "SUCCESS_GREEN": "#5bd975",
            "ERROR_RED": "#ff6b6b",
            "WARNING_YELLOW": "#ffd166",
            "BUTTON_NORMAL": "#223447",
            "BUTTON_HOVER": "#2f4c66",
            "BUTTON_ACTIVE": "#3a5f7d",
            "BORDER_LIGHT": "#3c5064",
            "BORDER_DARK": "#0b1118",
        },
        "light": {
            "PRIMARY_BG": "#f4f7fb",
            "SECONDARY_BG": "#ffffff",
            "PANEL_BG": "#e7edf5",
            "ACCENT_BG": "#d0deed",
            "GLADOS_ORANGE": "#e37a1f",
            "WHEATLEY_BLUE": "#1c7cb6",
            "PORTAL_BLUE": "#268bd2",
            "PORTAL_ORANGE": "#f99b40",
            "TEXT_PRIMARY": "#17212b",
            "TEXT_SECONDARY": "#314355",
            "TEXT_ACCENT": "#8c4b00",
            "TEXT_MUTED": "#5a6a7a",
            "SUCCESS_GREEN": "#2f9e63",
            "ERROR_RED": "#c23b3b",
            "WARNING_YELLOW": "#e3a400",
            "BUTTON_NORMAL": "#d6e1ec",
            "BUTTON_HOVER": "#c5d3e1",
            "BUTTON_ACTIVE": "#b4c5d6",
            "BORDER_LIGHT": "#b9c6d3",
            "BORDER_DARK": "#8293a3",
        },
    }

    current_mode: str = "dark"

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Switch the active colour palette."""

        normalized = mode.lower()
        palette = cls._COLOR_MODES.get(normalized)
        if palette is None:
            raise ValueError(f"Unknown theme mode: {mode}")

        for attribute, value in palette.items():
            setattr(cls, attribute, value)

        cls.current_mode = normalized

    @classmethod
    def get_available_modes(cls) -> tuple[str, ...]:
        """Return the available theme mode names."""

        return tuple(cls._COLOR_MODES.keys())


# Initialize with the default dark mode palette.
ApertureTheme.set_mode(ApertureTheme.current_mode)


__all__ = ["ApertureTheme"]
