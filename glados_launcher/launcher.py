"""Helpers to start games or open their launcher URLs."""
from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path


class GameLauncher:
    """Launch platform URLs or local executables with gentle fallbacks."""

    def __init__(self, data_manager) -> None:
        self.data_manager = data_manager

    def launch_game(self, launch_target: str, platform: str = "") -> bool:
        """Launch the provided URI or executable path.

        Returns ``True`` if the action appears to have succeeded.  The method is
        intentionally defensive so that UI calls do not explode on unsupported
        platforms.
        """

        if not launch_target:
            return False

        launch_target = launch_target.strip()
        try:
            if self._looks_like_uri(launch_target):
                return webbrowser.open(launch_target)

            path = Path(launch_target).expanduser()
            if not path.exists():
                return webbrowser.open(launch_target)

            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception:
            return False

    @staticmethod
    def _looks_like_uri(target: str) -> bool:
        prefixes = ("http://", "https://", "steam://", "epic://", "gog://", "uplay://")
        return target.startswith(prefixes) or "://" in target


__all__ = ["GameLauncher"]
