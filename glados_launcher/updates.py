"""Simplified update checking used by the GUI."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class UpdateCheckResult:
    success: bool
    update_available: bool
    message: str
    latest_version: Optional[str] = None


@dataclass
class UpdateApplyResult:
    success: bool
    message: str


class AutoUpdateManager:
    """Minimal stub that keeps the GUI happy without external services."""

    def __init__(self, current_version: str, current_script: Path) -> None:
        self.current_version = current_version
        self.current_script = Path(current_script)

    def is_supported(self) -> bool:
        """Return True when auto updates are allowed for the current runtime."""
        return not getattr(sys, "frozen", False)

    def check_for_updates(self) -> UpdateCheckResult:
        """Pretend to check for updates and inform the user they are current."""
        return UpdateCheckResult(
            success=True,
            update_available=False,
            message="You are running the latest testing build (v%s)." % self.current_version,
            latest_version=self.current_version,
        )

    def download_and_apply_update(self) -> UpdateApplyResult:
        """Placeholder download handler used by the GUI controls."""
        return UpdateApplyResult(
            success=False,
            message="Automatic updates are not available in this preview build.",
        )


__all__ = ["AutoUpdateManager", "UpdateApplyResult", "UpdateCheckResult"]
