"""Helpers for interacting with a Jellyfin media server."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping
from urllib.parse import urljoin

import requests

from .constants import JELLYFIN_DEFAULT_TIMEOUT, JELLYFIN_RECENT_LIMIT

__all__ = [
    "JellyfinError",
    "normalize_base_url",
    "fetch_system_info",
    "fetch_user_views",
    "fetch_recent_media",
]


class JellyfinError(RuntimeError):
    """Raised when a Jellyfin request fails."""


def normalize_base_url(base_url: str) -> str:
    """Return a normalized Jellyfin base URL without a trailing slash."""

    value = (base_url or "").strip()
    if not value:
        return ""
    if not value.lower().startswith(("http://", "https://")):
        value = f"https://{value}"
    return value.rstrip("/")


def _build_headers(api_key: str | None) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "Accept": "application/json",
        "User-Agent": "ApertureLauncher/1.0",
    }
    token = (api_key or "").strip()
    if token:
        headers["X-Emby-Token"] = token
    return headers


def _request_json(
    method: str,
    base_url: str,
    path: str,
    *,
    api_key: str | None,
    params: Mapping[str, Any] | None = None,
    timeout: float = JELLYFIN_DEFAULT_TIMEOUT,
) -> Any:
    """Perform a JSON request against the Jellyfin API."""

    normalized = normalize_base_url(base_url)
    if not normalized:
        raise JellyfinError("Jellyfin server URL is required.")

    url = urljoin(f"{normalized}/", path.lstrip("/"))

    response = requests.request(
        method.upper(),
        url,
        headers=_build_headers(api_key),
        params=params,
        timeout=timeout,
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network dependent
        raise JellyfinError(f"Jellyfin request failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:  # pragma: no cover - defensive
        raise JellyfinError("Jellyfin response did not contain JSON data.") from exc


def fetch_system_info(
    base_url: str,
    *,
    api_key: str | None = None,
    timeout: float = JELLYFIN_DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Retrieve basic server information."""

    data = _request_json(
        "GET",
        base_url,
        "/System/Info/Public",
        api_key=api_key,
        timeout=timeout,
    )

    if not isinstance(data, dict):  # pragma: no cover - defensive
        raise JellyfinError("Unexpected payload when fetching system information.")
    return data


def fetch_user_views(
    base_url: str,
    *,
    api_key: str,
    user_id: str,
    timeout: float = JELLYFIN_DEFAULT_TIMEOUT,
) -> List[Dict[str, Any]]:
    """Return the libraries available to the specified user."""

    if not user_id.strip():
        raise JellyfinError("Jellyfin user ID is required to fetch libraries.")

    data = _request_json(
        "GET",
        base_url,
        f"/Users/{user_id}/Views",
        api_key=api_key,
        timeout=timeout,
    )

    items = data.get("Items") if isinstance(data, dict) else None
    if not isinstance(items, list):  # pragma: no cover - defensive
        raise JellyfinError("Unexpected payload when fetching Jellyfin libraries.")
    return [item for item in items if isinstance(item, dict)]


def fetch_recent_media(
    base_url: str,
    *,
    api_key: str,
    user_id: str,
    limit: int = JELLYFIN_RECENT_LIMIT,
    timeout: float = JELLYFIN_DEFAULT_TIMEOUT,
) -> List[Dict[str, Any]]:
    """Retrieve recently added media for the specified user."""

    if not user_id.strip():
        raise JellyfinError("Jellyfin user ID is required to fetch recent media.")

    data = _request_json(
        "GET",
        base_url,
        f"/Users/{user_id}/Items",
        api_key=api_key,
        params={
            "SortBy": "DateCreated",
            "SortOrder": "Descending",
            "IncludeItemTypes": "Movie,Series,Episode,Audio",
            "Recursive": "true",
            "Limit": str(max(1, limit)),
        },
        timeout=timeout,
    )

    items = data.get("Items") if isinstance(data, dict) else None
    if not isinstance(items, list):  # pragma: no cover - defensive
        raise JellyfinError("Unexpected payload when fetching Jellyfin media.")
    return [item for item in items if isinstance(item, dict)]
