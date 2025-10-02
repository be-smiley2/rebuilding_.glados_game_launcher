"""Configuration and filesystem paths for the GLaDOS game launcher."""
from __future__ import annotations

import os
import sys
from pathlib import Path

CURRENT_VERSION = "2.5"


def _default_data_dir() -> Path:
    """Return a platform appropriate directory for storing launcher data."""

    home = Path.home()
    if sys.platform.startswith("win"):
        root = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
        return root / "GLaDOS Game Launcher"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "GLaDOS Game Launcher"

    data_home = os.environ.get("XDG_DATA_HOME")
    if data_home:
        return Path(data_home) / "glados_game_launcher"
    return home / ".local" / "share" / "glados_game_launcher"


def _resolve_base_dir() -> Path:
    """Return directory for persistent data whether running from source or frozen."""

    package_root = Path(__file__).resolve().parent.parent
    data_dir = _default_data_dir()

    candidates = []
    if not getattr(sys, "frozen", False):
        candidates.append(package_root)
    candidates.append(data_dir)

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
        except Exception:
            continue
        if os.access(candidate, os.W_OK):
            return candidate

    # As a last resort fall back to the default data directory
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


SCRIPT_DIR = _resolve_base_dir()
if getattr(sys, "frozen", False):
    CURRENT_SCRIPT = Path(sys.executable).resolve()
else:
    CURRENT_SCRIPT = Path(sys.argv[0]).resolve()

FIRST_RUN_FLAG = SCRIPT_DIR / ".aperture_first_run_complete"
GAME_DATA_FILE = SCRIPT_DIR / "game_data.json"
USER_PREFS_FILE = SCRIPT_DIR / "user_preferences.json"
ICON_CACHE_DIR = SCRIPT_DIR / "icon_cache"
ACHIEVEMENT_CACHE_DIR = SCRIPT_DIR / "achievement_cache"

# Ensure persistent directories exist
for directory in (ICON_CACHE_DIR, ACHIEVEMENT_CACHE_DIR):
    try:
        directory.mkdir(exist_ok=True)
    except Exception:
        pass


__all__ = [
    "CURRENT_VERSION",
    "CURRENT_SCRIPT",
    "SCRIPT_DIR",
    "FIRST_RUN_FLAG",
    "GAME_DATA_FILE",
    "USER_PREFS_FILE",
    "ICON_CACHE_DIR",
    "ACHIEVEMENT_CACHE_DIR",
]
