"""Configuration and filesystem paths for the GLaDOS game launcher."""
from __future__ import annotations

import sys
from pathlib import Path

CURRENT_VERSION = "2.5"


def _resolve_base_dir() -> Path:
    """Return directory for persistent data whether running from source or frozen."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    # When running from the package use the repository root (one level up)
    return Path(__file__).resolve().parent.parent


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
