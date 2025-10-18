"""Utilities for ensuring required third-party packages are available."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import threading
from typing import Dict, Iterable, Tuple

DependencySpec = Tuple[str, bool]

# Map import names to (pip package, is_optional).
DEPENDENCIES: Dict[str, DependencySpec] = {
    "requests": ("requests", False),
    "webview": ("pywebview", True),
}

_lock = threading.Lock()
_checked = False


def _find_missing() -> Iterable[Tuple[str, DependencySpec]]:
    """Yield (import_name, spec) pairs for modules that are not importable."""
    for module_name, spec in DEPENDENCIES.items():
        if importlib.util.find_spec(module_name) is None:
            yield module_name, spec


def _install(package: str) -> None:
    """Install a package using pip via the running interpreter."""
    subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        timeout=15,
    )


def ensure_dependencies() -> None:
    """Install any missing dependencies on demand."""
    global _checked

    if _checked:
        return

    with _lock:
        if _checked:
            return

        required_failures = []
        optional_failures = []

        for module_name, (package, is_optional) in _find_missing():
            try:
                _install(package)
                if importlib.util.find_spec(module_name) is None:
                    raise ModuleNotFoundError(module_name)
            except (
                ModuleNotFoundError,
                subprocess.CalledProcessError,
                subprocess.TimeoutExpired,
            ) as exc:
                failure = (module_name, package, exc)
                if is_optional:
                    optional_failures.append(failure)
                else:
                    required_failures.append(failure)

        _checked = True

    if required_failures:
        details = "\n".join(
            f"- {module} (pip install {package})" for module, package, _ in required_failures
        )
        raise RuntimeError(
            "Failed to install required dependencies:\n"
            f"{details}"
        )

    if optional_failures:
        messages = ", ".join(package for _, package, _ in optional_failures)
        print(
            "Warning: optional packages could not be installed automatically: "
            f"{messages}"
        )
