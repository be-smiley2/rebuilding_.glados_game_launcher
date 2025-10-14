#!/usr/bin/env python3
"""Utility script to refresh the list of free OpenRouter models.

The script downloads the latest model metadata using the OpenRouter public
API, filters for models that are free to use (prompt/completion/request/image
pricing are all zero), and writes the results to ``openrouter ai models.py`` in
this directory.
"""
from __future__ import annotations

import json
import pathlib
import sys
from decimal import Decimal
from urllib import request

API_URL = "https://openrouter.ai/api/v1/models?fmt=cards&max_price=0"
TARGET_FILE = pathlib.Path(__file__).with_name("openrouter ai models.py")

def _is_free(pricing: dict) -> bool:
    required_keys = ("prompt", "completion", "request", "image")
    for key in required_keys:
        value = pricing.get(key)
        if value is None:
            return False
        try:
            price = Decimal(str(value))
        except Exception:
            return False
        if price != 0:
            return False
    return True


def main() -> int:
    with request.urlopen(API_URL) as response:  # nosec: B310 - trusted URL
        payload = json.load(response)

    models = payload.get("data", [])
    free_ids = sorted(
        model["id"]
        for model in models
        if isinstance(model, dict) and _is_free(model.get("pricing", {}))
    )

    if not free_ids:
        print("No free models found in API response.", file=sys.stderr)
        return 1

    TARGET_FILE.write_text(
        "\n".join(
            model_id if model_id.endswith(":free") else f"{model_id}:free"
            for model_id in free_ids
        )
        + "\n"
    )
    print(f"Updated {TARGET_FILE.name} with {len(free_ids)} free model IDs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
