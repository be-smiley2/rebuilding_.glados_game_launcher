"""Optional dependency handling for the GLaDOS game launcher."""
from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

# psutil is optional but useful for system information
try:  # pragma: no cover - best effort import
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except Exception:  # pragma: no cover - best effort installation
    PSUTIL_AVAILABLE = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import psutil  # type: ignore  # noqa: WPS433
        PSUTIL_AVAILABLE = True
    except Exception:
        psutil = SimpleNamespace()  # type: ignore
        PSUTIL_AVAILABLE = False

# Image handling with graceful degradation
try:  # pragma: no cover - optional dependency
    from PIL import Image, ImageTk  # type: ignore
    import requests  # type: ignore
    PIL_AVAILABLE = True
except Exception:  # pragma: no cover - best effort fallbacks
    Image = None  # type: ignore
    ImageTk = None  # type: ignore
    PIL_AVAILABLE = False
    try:
        import requests  # type: ignore
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import requests  # type: ignore
        except Exception:
            requests = SimpleNamespace()  # type: ignore

try:
    REQUESTS_AVAILABLE = callable(getattr(requests, "get", None))
except Exception:  # pragma: no cover - extremely defensive
    REQUESTS_AVAILABLE = False

# Cross platform winreg access
try:  # pragma: no cover - depends on platform
    if sys.platform.startswith("win"):
        import winreg  # type: ignore
    else:
        raise ImportError
except Exception:  # pragma: no cover - provide lightweight fallback
    class _MockWinreg:  # noqa: WPS431 - simple namespace style class
        HKEY_LOCAL_MACHINE = None

        @staticmethod
        def OpenKey(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            return None

        @staticmethod
        def QueryValueEx(*_args):  # type: ignore[no-untyped-def]
            return (None, None)

        @staticmethod
        def EnumKey(*_args):  # type: ignore[no-untyped-def]
            return None

        @staticmethod
        def CloseKey(*_args):  # type: ignore[no-untyped-def]
            return None

        WindowsError = OSError

    winreg = _MockWinreg()  # type: ignore


__all__ = [
    "psutil",
    "PSUTIL_AVAILABLE",
    "Image",
    "ImageTk",
    "PIL_AVAILABLE",
    "requests",
    "REQUESTS_AVAILABLE",
    "winreg",
]
