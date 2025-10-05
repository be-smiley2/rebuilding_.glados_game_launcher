"""Utility helpers for working with cached game icons."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from .config import ICON_CACHE_DIR


class GameIconManager:
    """Track icon cache paths for games.

    The real project downloads platform icons from the network.  For the
    educational version we simply provide deterministic cache locations so the
    rest of the code can operate without import errors.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir or ICON_CACHE_DIR
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _build_icon_name(self, game_id: str, platform: str) -> str:
        token = f"{platform}:{game_id}".encode("utf-8", "ignore")
        digest = hashlib.sha1(token).hexdigest()
        return f"{platform}_{digest}.ico"

    def get_cached_icon(self, game_id: str, platform: str) -> Optional[Path]:
        """Return the expected cache file for a game if it exists."""
        candidate = self.cache_dir / self._build_icon_name(game_id, platform)
        return candidate if candidate.exists() else None

    def expected_icon_path(self, game_id: str, platform: str) -> Path:
        """Return the location where an icon should be stored."""
        return self.cache_dir / self._build_icon_name(game_id, platform)

    def clear_cache(self) -> None:
        for file in list(self.cache_dir.glob("*")):
            try:
                if file.is_file():
                    file.unlink()
            except Exception:
                pass


__all__ = ["GameIconManager"]
