"""Roasting persona helpers."""

from __future__ import annotations

import random
from typing import Dict, Mapping, Sequence

from .constants import ROASTING_SCRIPTS


def generate_roast(
    persona: str,
    prompt: str,
    *,
    rng: random.Random | None = None,
    scripts: Mapping[str, Dict[str, Sequence[str]]] = ROASTING_SCRIPTS,
) -> str:
    """Create a persona-themed roast without contacting external services."""

    script = scripts.get(persona) or scripts["GLaDOS"]
    target = " ".join(prompt.split())
    target = target.strip(" .,!?:;\"'")
    if not target:
        target = "this test subject"
    elif len(target) > 120:
        target = target[:117].rstrip() + "..."

    chooser = rng.choice if rng is not None else random.choice

    intro = chooser(script["intro"])
    template = chooser(script["templates"])
    outro = chooser(script["outro"])

    segments = [intro.strip(), template.format(target=target).strip(), outro.strip()]
    return " ".join(segment for segment in segments if segment)
