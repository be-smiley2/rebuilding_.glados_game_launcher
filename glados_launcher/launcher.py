"""Utilities for launching games via platform URLs."""
from __future__ import annotations

import platform
import subprocess
import webbrowser

from .data_manager import GameDataManager


class GameLauncher:
    def __init__(self, game_manager: GameDataManager) -> None:
        self.game_manager = game_manager

    def launch_game(self, game_url: str, platform_name: str = "unknown") -> bool:
        try:
            if platform.system() == "Windows":
                subprocess.run(f'start "" "{game_url}"', shell=True, check=False)
            elif platform.system() == "Darwin":
                subprocess.run(["open", game_url], check=False)
            else:
                subprocess.run(["xdg-open", game_url], check=False)
            return True
        except Exception:
            try:
                webbrowser.open(game_url)
                return True
            except Exception:
                return False


__all__ = ["GameLauncher"]
