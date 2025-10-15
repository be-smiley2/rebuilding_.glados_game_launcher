"""Helpers for interacting with the OpenRouter API from the GUI."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Sequence

import requests

from .constants import OPENROUTER_CHAT_URL, OPENROUTER_MODELS_URL

Scheduler = Callable[[int, Callable[[], None]], Any]


def verify_api_key(
    api_key: str,
    on_complete: Callable[[Exception | None], None],
    *,
    scheduler: Scheduler,
    timeout: float = 30.0,
) -> None:
    """Validate an OpenRouter API key on a background thread."""

    def worker() -> None:
        try:
            response = requests.get(
                OPENROUTER_MODELS_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                },
                timeout=timeout,
            )
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network dependent
            scheduler(0, lambda exc=exc: on_complete(exc))
            return

        scheduler(0, lambda: on_complete(None))

    threading.Thread(target=worker, daemon=True).start()


def request_chat_completion(
    api_key: str,
    model: str,
    messages: Sequence[Dict[str, str]],
    on_complete: Callable[[Exception | None, str | None], None],
    *,
    scheduler: Scheduler,
    timeout: float = 60.0,
) -> None:
    """Submit a chat completion request to OpenRouter asynchronously."""

    payload_messages: List[Dict[str, str]] = [dict(message) for message in messages]

    def worker() -> None:
        try:
            response = requests.post(
                OPENROUTER_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "HTTP-Referer": "https://aperture-science.local",
                    "X-Title": "Aperture Science Enrichment Center Launcher",
                },
                json={
                    "model": model,
                    "messages": payload_messages,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices")
            if not choices:
                raise ValueError("OpenRouter response did not include any choices.")
            message = choices[0].get("message", {})
            content = message.get("content")
            if not isinstance(content, str):
                raise ValueError("OpenRouter response did not include text content.")
            content = content.strip()
        except Exception as exc:  # pragma: no cover - network dependent
            scheduler(0, lambda exc=exc: on_complete(exc, None))
            return

        scheduler(0, lambda content=content: on_complete(None, content))

    threading.Thread(target=worker, daemon=True).start()
