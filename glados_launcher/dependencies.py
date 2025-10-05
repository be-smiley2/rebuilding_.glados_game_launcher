"""Compatibility helpers for optional platform-specific modules."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from types import SimpleNamespace
from typing import Optional, Set

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

# Track installation attempts so we don't recurse endlessly if a package
# repeatedly fails to install at runtime.
_ATTEMPTED_INSTALLS: Set[str] = set()


def ensure_optional_dependency(
    module_name: str,
    package_name: Optional[str] = None,
    *,
    auto_install: bool = True,
) -> bool:
    """Return ``True`` if ``module_name`` can be imported, installing if needed.

    The helper tries to ``importlib.util.find_spec`` first to avoid the cost of a
    full import.  If the spec cannot be located and ``auto_install`` is enabled
    the function will attempt to install ``package_name`` (defaulting to the
    module name) using ``pip``.  Subsequent failures are memoised so we do not
    repeatedly invoke ``pip`` on every access.
    """

    if importlib.util.find_spec(module_name) is not None:
        return True

    if not auto_install or getattr(sys, "frozen", False):
        return False

    package = package_name or module_name
    if package in _ATTEMPTED_INSTALLS:
        return False

    _ATTEMPTED_INSTALLS.add(package)

    try:
        print(f"Attempting to install optional dependency '{package}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception:
        return False

    return importlib.util.find_spec(module_name) is not None


REQUESTS_AVAILABLE = ensure_optional_dependency("requests", auto_install=False)

__all__ = [
    "winreg",
    "REQUESTS_AVAILABLE",
    "ensure_optional_dependency",
]
