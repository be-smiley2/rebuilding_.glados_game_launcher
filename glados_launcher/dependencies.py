"""Compatibility helpers for optional platform-specific modules."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Sequence

try:  # pragma: no cover - exercised only on Windows
    import winreg  # type: ignore
except ImportError:  # pragma: no cover - Windows only module
    class _WinRegStub(SimpleNamespace):
        """Minimal stub mirroring the winreg API used in the project."""

        def __init__(self) -> None:
            super().__init__(
                HKEY_LOCAL_MACHINE=None,
            )

        def __getattr__(self, name: str):  # noqa: D401 - simple passthrough
            raise AttributeError(
                "winreg is not available on this platform (sys.platform="
                f"{sys.platform!r})."
            )

    winreg = _WinRegStub()  # type: ignore

REQUESTS_AVAILABLE = importlib.util.find_spec("requests") is not None
PYGLET_AVAILABLE = importlib.util.find_spec("pyglet") is not None
<<<<<<< HEAD

__all__ = ["winreg", "REQUESTS_AVAILABLE", "PYGLET_AVAILABLE"]
=======
_PYGLET_INSTALL_ATTEMPTED = False


def _find_repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _run_pip(arguments: Sequence[str]) -> bool:
    try:
        subprocess.check_call(list(arguments))
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


def _candidate_install_commands() -> Iterable[Sequence[str]]:
    requirements = _find_repository_root() / "requirements-3d.txt"
    if requirements.is_file():
        yield (sys.executable, "-m", "pip", "install", "-r", str(requirements))
    yield (sys.executable, "-m", "pip", "install", "pyglet>=2.0")


def ensure_pyglet(auto_install: bool = True) -> bool:
    """Return whether pyglet is importable, optionally installing it."""

    global PYGLET_AVAILABLE, _PYGLET_INSTALL_ATTEMPTED

    if importlib.util.find_spec("pyglet") is not None:
        PYGLET_AVAILABLE = True
        return True

    if not auto_install:
        PYGLET_AVAILABLE = False
        return False

    if not _PYGLET_INSTALL_ATTEMPTED:
        _PYGLET_INSTALL_ATTEMPTED = True
        for command in _candidate_install_commands():
            if _run_pip(command):
                break

    PYGLET_AVAILABLE = importlib.util.find_spec("pyglet") is not None
    return PYGLET_AVAILABLE


__all__ = ["winreg", "REQUESTS_AVAILABLE", "PYGLET_AVAILABLE", "ensure_pyglet"]
>>>>>>> d8f0ee082c5b33c62e19510008cec4ac784ff659
