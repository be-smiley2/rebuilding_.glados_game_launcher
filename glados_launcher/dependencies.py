"""Compatibility helpers for optional platform-specific modules."""
from __future__ import annotations

import importlib.util
import sys
from types import SimpleNamespace

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

__all__ = ["winreg", "REQUESTS_AVAILABLE", "PYGLET_AVAILABLE"]
