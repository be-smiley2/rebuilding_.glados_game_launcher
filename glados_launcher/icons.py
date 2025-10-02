"""Game icon helpers."""
from __future__ import annotations

from typing import Any, Dict

from .dependencies import Image, ImageTk, PIL_AVAILABLE


class GameIconManager:
    """Create and cache platform specific icons."""

    def __init__(self) -> None:
        self.icon_cache: Dict[str, Any] = {}
        self.default_icon: Any = None
        self.platform_icons: Dict[str, Any] = {}
        self.create_default_icons()

    def create_default_icons(self) -> None:
        try:
            if PIL_AVAILABLE and Image is not None and ImageTk is not None:
                img = Image.new("RGBA", (32, 32), (100, 100, 100, 255))
                self.default_icon = ImageTk.PhotoImage(img)

                platform_colors = {
                    "steam": (23, 26, 33, 255),
                    "epic": (242, 242, 242, 255),
                    "ubisoft": (0, 82, 165, 255),
                    "gog": (114, 36, 108, 255),
                }

                for platform_name, color in platform_colors.items():
                    img = Image.new("RGBA", (32, 32), color)
                    self.platform_icons[platform_name] = ImageTk.PhotoImage(img)
            else:
                self.default_icon = "[]"
                self.platform_icons = {
                    "steam": "S",
                    "epic": "E",
                    "ubisoft": "U",
                    "gog": "G",
                }
        except Exception:
            self.default_icon = "[]"
            self.platform_icons = {"steam": "S", "epic": "E", "ubisoft": "U", "gog": "G"}

    def get_game_icon(self, game_id: str, game_name: str, platform_name: str) -> Any:
        cache_key = f"{platform_name}_{game_id}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        icon = self.platform_icons.get(platform_name, self.default_icon)
        self.icon_cache[cache_key] = icon
        return icon


__all__ = ["GameIconManager"]
