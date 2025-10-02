"""Auto-update management for the launcher."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import CURRENT_VERSION, CURRENT_SCRIPT
from .dependencies import REQUESTS_AVAILABLE, requests


@dataclass
class UpdateCheckResult:
    success: bool
    update_available: bool
    message: str
    current_version: str
    latest_version: Optional[str] = None
    severity: str = "info"


class UpdateFetchError(Exception):
    def __init__(self, base_error: Exception, attempted_sources: List[str]):
        self.base_error = base_error
        self.attempted_sources = attempted_sources
        message = f"{base_error}. Sources tried: {', '.join(attempted_sources)}" if attempted_sources else str(base_error)
        super().__init__(message)


@dataclass
class UpdateApplyResult:
    success: bool
    message: str


AUTO_UPDATE_GITHUB_REPO = "be-smiley2/glados_game_launcher"
AUTO_UPDATE_RELEASES_API_URL = f"https://api.github.com/repos/{AUTO_UPDATE_GITHUB_REPO}/releases/latest"
AUTO_UPDATE_COMMON_BRANCHES: Tuple[str, ...] = ("main", "master", "release", "stable")
AUTO_UPDATE_POSSIBLE_SCRIPT_PATHS: Tuple[str, ...] = (
    "glados_game_launcher.py",
    "src/glados_game_launcher.py",
    "glados_game_launcher/glados_game_launcher.py",
)
AUTO_UPDATE_RAW_SCRIPT_URLS: Tuple[str, ...] = tuple(
    f"https://raw.githubusercontent.com/{AUTO_UPDATE_GITHUB_REPO}/{branch}/{path}"
    for branch in AUTO_UPDATE_COMMON_BRANCHES
    for path in AUTO_UPDATE_POSSIBLE_SCRIPT_PATHS
)


class AutoUpdateManager:
    GITHUB_REPO = AUTO_UPDATE_GITHUB_REPO
    RELEASES_API_URL = AUTO_UPDATE_RELEASES_API_URL
    COMMON_BRANCHES: Tuple[str, ...] = AUTO_UPDATE_COMMON_BRANCHES
    POSSIBLE_SCRIPT_PATHS: Tuple[str, ...] = AUTO_UPDATE_POSSIBLE_SCRIPT_PATHS
    RAW_SCRIPT_URLS: Tuple[str, ...] = AUTO_UPDATE_RAW_SCRIPT_URLS
    VERSION_PATTERN = re.compile(r"^CURRENT_VERSION\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)

    def __init__(self, current_version: str = CURRENT_VERSION, script_path: Path = CURRENT_SCRIPT):
        self.current_version = current_version
        self.script_path = script_path
        self.latest_version = current_version
        self.remote_script: Optional[str] = None
        self.active_source: Optional[str] = None
        self.last_attempted_sources: List[str] = []
        self.last_release_data: Optional[Dict[str, Any]] = None

    def is_supported(self) -> bool:
        return (not getattr(__import__("sys"), "frozen", False)) and self.script_path.exists() and self.script_path.suffix == ".py"

    def _candidate_urls(self) -> List[str]:
        candidates: List[str] = []
        for branch in self.COMMON_BRANCHES:
            for relative_path in self.POSSIBLE_SCRIPT_PATHS:
                candidates.append(
                    f"https://raw.githubusercontent.com/{self.GITHUB_REPO}/{branch}/{relative_path}"
                )
        return candidates

    def _normalize_version(self, version: str) -> Optional[str]:
        if not version:
            return None
        cleaned = str(version).strip()
        if cleaned.lower().startswith("v"):
            cleaned = cleaned[1:]
        cleaned = cleaned.strip()
        return cleaned or None

    def _fetch_latest_release(self) -> Optional[Dict[str, Any]]:
        if self.RELEASES_API_URL not in self.last_attempted_sources:
            self.last_attempted_sources.append(self.RELEASES_API_URL)
        response = requests.get(
            self.RELEASES_API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"GLaDOS-Launcher/{self.current_version}",
            },
            timeout=10,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        release_data: Dict[str, Any] = response.json()
        normalized = self._normalize_version(release_data.get("tag_name") or release_data.get("name") or "")
        if not normalized:
            body = release_data.get("body") or ""
            match = self.VERSION_PATTERN.search(body)
            if match:
                normalized = match.group(1)
        release_data["normalized_version"] = normalized
        return release_data

    def _download_release_asset(self) -> Optional[str]:
        if not self.last_release_data:
            return None
        assets = self.last_release_data.get("assets") or []
        for asset in assets:
            name = str(asset.get("name", "")).lower()
            if not name.endswith(".py"):
                continue
            url = asset.get("browser_download_url")
            if not url:
                continue
            if url not in self.last_attempted_sources:
                self.last_attempted_sources.append(str(url))
            response = requests.get(
                url,
                headers={"User-Agent": f"GLaDOS-Launcher/{self.current_version}"},
                timeout=15,
            )
            response.raise_for_status()
            self.active_source = str(url)
            return response.text
        return None

    def _fetch_remote_script(self) -> str:
        attempted: List[str] = list(self.last_attempted_sources)
        last_error: Optional[Exception] = None
        for url in self._candidate_urls():
            attempted.append(url)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                self.active_source = url
                self.last_attempted_sources = attempted.copy()
                return response.text
            except Exception as exc:
                last_error = exc
        self.last_attempted_sources = attempted
        raise UpdateFetchError(last_error or RuntimeError("No update sources configured"), attempted)

    def check_for_updates(self) -> UpdateCheckResult:
        if not REQUESTS_AVAILABLE:
            return UpdateCheckResult(
                False,
                False,
                "Requests module unavailable; cannot check for updates.",
                self.current_version,
                severity="warning",
            )
        if not self.is_supported():
            return UpdateCheckResult(
                False,
                False,
                "Auto-update is only available when running from source builds.",
                self.current_version,
                severity="warning",
            )

        self.last_release_data = None
        self.last_attempted_sources = []
        release_error: Optional[Exception] = None
        release_info: Optional[Dict[str, Any]] = None

        try:
            release_info = self._fetch_latest_release()
        except Exception as exc:
            release_error = exc

        if release_info:
            self.last_release_data = release_info
            normalized_version = release_info.get("normalized_version")
            if normalized_version:
                latest_version = str(normalized_version)
                self.latest_version = latest_version
                self.active_source = release_info.get("html_url") or self.RELEASES_API_URL
                if self._compare_versions(latest_version, self.current_version) > 0:
                    message = f"Update {latest_version} available on GitHub releases."
                    return UpdateCheckResult(True, True, message, self.current_version, latest_version=latest_version)
                message = f"You are running the latest version ({self.current_version})."
                return UpdateCheckResult(True, False, message, self.current_version, latest_version=latest_version)

        try:
            remote_script = self._fetch_remote_script()
            match = self.VERSION_PATTERN.search(remote_script)
            if not match:
                extra = f" GitHub releases lookup failed: {release_error}." if release_error else ""
                return UpdateCheckResult(
                    False,
                    False,
                    "Unable to determine remote version." + extra,
                    self.current_version,
                    severity="error",
                )
            remote_version = match.group(1)
            self.remote_script = remote_script
            self.latest_version = remote_version
            if self._compare_versions(remote_version, self.current_version) > 0:
                return UpdateCheckResult(
                    True,
                    True,
                    f"Update {remote_version} available.",
                    self.current_version,
                    latest_version=remote_version,
                )
            return UpdateCheckResult(
                True,
                False,
                f"You are running the latest version ({self.current_version}).",
                self.current_version,
                latest_version=remote_version,
            )
        except Exception as exc:
            attempted = self.last_attempted_sources or list(self.RAW_SCRIPT_URLS)
            sources = ", ".join(attempted)
            details = str(exc)
            if release_error:
                details = f"GitHub releases error: {release_error}; fallback error: {exc}"
            return UpdateCheckResult(
                False,
                False,
                f"Update check failed: {details}. Tried sources: {sources}",
                self.current_version,
                severity="error",
            )

    def download_and_apply_update(self) -> UpdateApplyResult:
        if not REQUESTS_AVAILABLE:
            return UpdateApplyResult(False, "Requests module unavailable; cannot download updates.")
        if not self.is_supported():
            return UpdateApplyResult(False, "Auto-update is only available when running from source builds.")

        asset_error: Optional[Exception] = None

        try:
            if not self.remote_script:
                if self.last_release_data:
                    try:
                        self.remote_script = self._download_release_asset()
                    except Exception as exc:
                        asset_error = exc
                if not self.remote_script:
                    self.remote_script = self._fetch_remote_script()
                if self.remote_script:
                    match = self.VERSION_PATTERN.search(self.remote_script)
                    if match:
                        self.latest_version = match.group(1)

            if not self.remote_script:
                message = "No update payload available."
                if asset_error:
                    message += f" Latest release asset download failed: {asset_error}"
                return UpdateApplyResult(False, message)

            original_content = self.script_path.read_text(encoding="utf-8")
            backup_path = self.script_path.with_suffix(self.script_path.suffix + ".bak")
            backup_path.write_text(original_content, encoding="utf-8")
            self.script_path.write_text(self.remote_script, encoding="utf-8")

            return UpdateApplyResult(True, f"Updated to version {self.latest_version} from {self.active_source}.")
        except Exception as exc:
            return UpdateApplyResult(False, f"Update failed: {exc}")

    @staticmethod
    def _compare_versions(version_a: str, version_b: str) -> int:
        def _tokenize(version: str) -> List[int]:
            return [int(part) for part in re.findall(r"\d+", version)]

        tokens_a = _tokenize(version_a)
        tokens_b = _tokenize(version_b)
        length = max(len(tokens_a), len(tokens_b))
        tokens_a.extend([0] * (length - len(tokens_a)))
        tokens_b.extend([0] * (length - len(tokens_b)))

        for part_a, part_b in zip(tokens_a, tokens_b):
            if part_a > part_b:
                return 1
            if part_a < part_b:
                return -1
        return 0


__all__ = [
    "AutoUpdateManager",
    "UpdateCheckResult",
    "UpdateApplyResult",
    "UpdateFetchError",
]
