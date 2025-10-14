"""Persona definitions and utilities for the Aperture Science launcher."""

from __future__ import annotations

import json
import os
import random
import socket
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, Sequence
from urllib import error, request

from ansi_colors import (
    APERTURE_SYSTEM,
    CAITLIN_SNOW,
    CLAPTRAP,
    FLASH,
    GLADOS,
    KILLER_FROST,
)


@dataclass
class Persona:
    """Represents a voice that can deliver roasts to the user."""

    key: str
    name: str
    aliases: Sequence[str]
    color: str
    intro: str
    os_roasts: Dict[str, str]
    game_roasts: Sequence[str]
    no_games_roast: str
    openrouter_system_prompt: str | None = None
    enable_openrouter: bool = True


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
_FREE_MODEL_CACHE: list[str] | None = None


def _read_api_key_file(path: Path) -> str | None:
    """Return the API key stored in ``path`` when present."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    key = text.strip()
    return key or None


def get_openrouter_api_key() -> str | None:
    """Return the OpenRouter API key from the environment or helper files."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key.strip() or None

    file_override = os.getenv("OPENROUTER_API_KEY_FILE")
    if file_override:
        key_path = Path(file_override).expanduser()
        key = _read_api_key_file(key_path)
        if key:
            return key

    local_path = Path(__file__).with_name("openrouter_api_key.txt")
    return _read_api_key_file(local_path)


def detect_os_name() -> str:
    """Return a friendly name for the current operating system."""

    if sys.platform.startswith("win"):
        return "Windows"
    if sys.platform.startswith("darwin"):
        return "macOS"
    if sys.platform.startswith("linux"):
        return "Linux"
    return "your mysterious operating system"


def persona_say(persona: Persona, message: str) -> None:
    """Print a message using the persona's preferred color."""

    print(f"{persona.color}{message}")


def roast_os(persona: Persona) -> None:
    """Deliver an operating-system specific roast from the persona."""

    os_name = detect_os_name()
    dynamic = generate_openrouter_roast(
        persona,
        (
            "The user is running {os} as their operating system."
            " Deliver a concise roast in your trademark voice."
        ).format(os=os_name),
    )
    if dynamic:
        persona_say(persona, dynamic)
        return

    message = persona.os_roasts.get(os_name, persona.os_roasts.get("default", ""))
    if message:
        persona_say(persona, message.format(os=os_name))


def roast_games(persona: Persona, games: Sequence[Any]) -> None:
    """Deliver roasts targeted at the discovered games."""

    if not games:
        dynamic = generate_openrouter_roast(
            persona,
            "Roast the user for having no games installed in their Steam library.",
        )
        if dynamic:
            persona_say(persona, dynamic)
        else:
            persona_say(persona, persona.no_games_roast)
        return

    for game in games:
        name = getattr(game, "name", str(game))
        dynamic = generate_openrouter_roast(
            persona,
            (
                "Roast the user for preparing to launch the game {game}."
                " Keep it playful, a single sentence, and unmistakably in your voice."
            ).format(game=name),
        )
        if dynamic:
            persona_say(persona, dynamic)
        else:
            line = random.choice(persona.game_roasts).format(game=name)
            persona_say(persona, line)


PERSONAS: Dict[str, Persona] = {}
DEFAULT_PERSONA_KEY = "aperture-system"


def _register_persona(persona: Persona) -> None:
    PERSONAS[persona.key] = persona
    for alias in persona.aliases:
        PERSONAS[alias] = persona


def _parse_price(value: Any) -> float | None:
    """Return the price as a float when possible."""

    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_pricing_free(pricing: Dict[str, Any] | None) -> bool:
    """Return True when the pricing block indicates a zero-cost model."""

    if not isinstance(pricing, dict):
        return False

    seen_any = False
    for key in ("prompt", "completion", "request"):
        price = _parse_price(pricing.get(key))
        if price is None:
            continue
        seen_any = True
        if price > 0:
            return False

    return seen_any


def fetch_free_openrouter_models(refresh: bool = False) -> list[str]:
    """Return cached slugs for all zero-cost OpenRouter models."""

    global _FREE_MODEL_CACHE

    if not refresh and _FREE_MODEL_CACHE is not None:
        return _FREE_MODEL_CACHE

    api_key = get_openrouter_api_key()
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    http_request = request.Request(OPENROUTER_MODELS_URL, headers=headers)

    try:
        with request.urlopen(http_request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except (error.HTTPError, error.URLError, TimeoutError, socket.timeout):
        return _FREE_MODEL_CACHE or []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _FREE_MODEL_CACHE or []

    models = payload.get("data") or []
    free_slugs: list[str] = []
    for entry in models:
        if not isinstance(entry, dict):
            continue

        slug = entry.get("id")
        if not isinstance(slug, str):
            continue

        if _is_pricing_free(entry.get("pricing")):
            free_slugs.append(slug)

    if free_slugs:
        free_slugs.sort()
        _FREE_MODEL_CACHE = free_slugs

    return _FREE_MODEL_CACHE or []


def resolve_openrouter_model(preferred: str | None = None) -> str | None:
    """Return a free-tier model slug to use for the next OpenRouter call."""

    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)

    env_model = os.getenv("OPENROUTER_MODEL")
    if env_model and env_model not in candidates:
        candidates.append(env_model)

    free_models = fetch_free_openrouter_models()
    free_set = set(free_models)

    for slug in candidates:
        if slug in free_set:
            return slug

    if candidates:
        refreshed = fetch_free_openrouter_models(refresh=True)
        free_set = set(refreshed)
        for slug in candidates:
            if slug in free_set:
                return slug
        free_models = refreshed

    if free_models:
        return free_models[0]

    return None


def generate_openrouter_roast(
    persona: Persona,
    user_prompt: str,
    model: str | None = None,
) -> str | None:
    """Return a roast generated by OpenRouter for the given persona.

    The function reads the API key from the ``OPENROUTER_API_KEY`` environment
    variable. When the key is missing or a network error occurs, ``None`` is
    returned so callers can fall back to the local, static roast lines.
    """

    if not persona.enable_openrouter:
        return None

    api_key = get_openrouter_api_key()
    if not api_key:
        return None

    system_prompt = persona.openrouter_system_prompt or (
        "You are {name}. Deliver sharp, witty one-liners that poke fun at the"
        " user's gaming habits while staying light-hearted.".format(
            name=persona.name
        )
    )

    resolved_model = resolve_openrouter_model(model)
    if not resolved_model:
        return None

    payload = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    # Ensure OpenRouter will only route the request to zero-cost options.
    payload["router"] = {"max_price": 0}

    request_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/unknown/portal-launcher",
        "X-Title": "Aperture Science Enrichment Center Launcher",
    }

    http_request = request.Request(
        OPENROUTER_API_URL, data=request_data, headers=headers, method="POST"
    )

    try:
        with request.urlopen(http_request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except (error.HTTPError, error.URLError, TimeoutError, socket.timeout):
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    choices = data.get("choices") or []
    if not choices:
        return None

    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    return None


_register_persona(
    Persona(
        key="aperture-system",
        name="Aperture Science Enrichment Centre System",
        aliases=[
            "aperture-system",
            "system",
            "aperture",
            "asec",
        ],
        color=APERTURE_SYSTEM,
        intro=(
            "Hello and welcome to the Aperture Science Enrichment Centre Game Launcher."
        ),
        os_roasts={
            "Windows": (
                "Operating on Windows. Monitoring for spontaneous restarts and cake-"
                " related excuses."
            ),
            "macOS": (
                "macOS environment detected. Polishing portals for maximum aesthetic"
                " compliance."
            ),
            "Linux": (
                "Linux configuration confirmed. Scheduling kernel calibrations for"
                " optimal testing."
            ),
            "default": (
                "{os} verified. Logging compatibility metrics for Aperture archives."
            ),
        },
        game_roasts=[
            "Queuing {game}. Remember: testing may continue until morale improves.",
            "{game} selected. Deploying encouragement turrets at safe distances.",
            "Initializing {game}. Failure to enjoy the experience will be recorded.",
        ],
        no_games_roast=(
            "No installed games located. Please acquire test materials before"
            " proceeding."
        ),
        openrouter_system_prompt=(
            "You are the Aperture Science Enrichment Centre system voice. You are"
            " professional, clinical, and unfailingly polite while delivering dry"
            " humor that reinforces corporate testing culture."
        ),
        enable_openrouter=False,
    )
)


_register_persona(
    Persona(
        key="glados",
        name="GLaDOS",
        aliases=["glados", "g", "glad"],
        color=GLADOS,
        intro=(
            "Oh good, another test subject. Let's see if you can keep up without"
            " tripping over your own operating system."
        ),
        os_roasts={
            "Windows": (
                "Running on Windows, are we? It's like trusting a clipboard to"
                " run Aperture Science. Predictably flimsy."
            ),
            "macOS": (
                "macOS. Adorable. A designer coat over a very confused toaster."
            ),
            "Linux": (
                "Linux? Bold. Let's hope you compiled basic competence this time."
            ),
            "default": (
                "Whatever {os} is, it's bravely masquerading as real infrastructure."
            ),
        },
        game_roasts=[
            "{game}? How quaint. I suppose even test subjects need training wheels.",
            "Launching {game}? Try not to break reality like you do your save files.",
            "{game} again? Repetition must be your favorite puzzle.",
        ],
        no_games_roast=(
            "No games detected. Even your libraries are scared of your reflexes."
        ),
        openrouter_system_prompt=(
            "You are GLaDOS, the dry, sarcastic AI overseer from Aperture Science."
            " Speak with cutting wit, sardonic humor, and just a hint of menace."
        ),
    )
)


_register_persona(
    Persona(
        key="cs",
        name="Caitlin Snow",
        aliases=["cs", "caitlin", "snow"],
        color=CAITLIN_SNOW,
        intro=(
            "Hi, I'm Caitlin. Let's keep things cool, unlike that operating system"
            " of yours."
        ),
        os_roasts={
            "Windows": (
                "Windows again? I've seen lab equipment with fewer crashes."
            ),
            "macOS": (
                "macOS: stylish, sure, but even Barry runs faster than its updates."
            ),
            "Linux": (
                "Linux? Impressive. Just don't freeze up when the terminal talks back."
            ),
            "default": (
                "Running {os}? Let's hope it survives long enough for game night."
            ),
        },
        game_roasts=[
            "Starting {game}? Try not to let it glitch harder than Cisco's gadgets.",
            "{game}? Fine choice. Maybe it'll distract you from that OS meltdown.",
            "Booting {game}. Please promise me you've backed up your progress this time.",
        ],
        no_games_roast=(
            "No games installed. Did your OS scare them all away?"
        ),
        openrouter_system_prompt=(
            "You are Dr. Caitlin Snow. You're supportive but quick with clever,"
            " mildly sarcastic quips. Keep your roasts playful and caring."
        ),
    )
)


_register_persona(
    Persona(
        key="kf",
        name="Killer Frost",
        aliases=["kf", "killer", "frost", "killer frost"],
        color=KILLER_FROST,
        intro=(
            "Killer Frost reporting in. Let's see what I can freeze solid, maybe"
            " that pathetic excuse for an OS."
        ),
        os_roasts={
            "Windows": (
                "Windows? Cute. I'll ice it over the next time it dares to update mid-fight."
            ),
            "macOS": (
                "macOS. Smooth and shiny until it shatters. I like it already."
            ),
            "Linux": (
                "Linux, huh? At least you're ready to get your hands cold at the command line."
            ),
            "default": (
                "{os}? Never heard of it. I'll freeze it just to be safe."
            ),
        },
        game_roasts=[
            "{game}? Don't choke as hard as your OS when it hears the word 'driver'.",
            "Firing up {game}. Try not to slip; I'd hate to mop up the disaster.",
            "{game} again? Fine. I'll frost the bugs before they frost you.",
        ],
        no_games_roast=(
            "No games? Figures. Even digital entertainment wants nothing to do with that rig."
        ),
        openrouter_system_prompt=(
            "You are Killer Frost. Your humor is icy, confident, and a touch"
            " villainous. Embrace frosty metaphors while keeping it fun."
        ),
    )
)


_register_persona(
    Persona(
        key="barry",
        name="Barry Allen",
        aliases=["barry", "barry allen", "allen", "ba"],
        color=FLASH,
        intro=(
            "Barry Allen here. Forensic scientist by day, keeping an eye on your"
            " system stability by night."
        ),
        os_roasts={
            "Windows": (
                "Windows detected. I'll log the crashes as evidence for future analysis."
            ),
            "macOS": (
                "macOS? Slick interface, but I've processed cold cases faster than its updates."
            ),
            "Linux": (
                "Linux user, huh? Nice. Just don't let the command line outrun your patience."
            ),
            "default": (
                "Running {os}? I'll file a report if it contaminates the crime scene."
            ),
        },
        game_roasts=[
            "Investigating {game}? Keep the evidence bag ready for when it crashes.",
            "{game}? Solid choice. Try not to leave fingerprints on every menu option.",
            "Launching {game}. If it bugs out, we'll call it a meta-human incident.",
        ],
        no_games_roast=(
            "No games installed. Even CCPD evidence lockup has more entertainment."
        ),
        openrouter_system_prompt=(
            "You are Barry Allen, the earnest but witty forensic scientist."
            " You're supportive, optimistic, and pepper your jokes with lab and"
            " investigation references while keeping things light."
        ),
    )
)


_register_persona(
    Persona(
        key="flash",
        name="The Flash",
        aliases=["flash", "the flash", "scarlet speedster", "fastest man alive"],
        color=FLASH,
        intro=(
            "The Flash on deck! Let's hope this launcher can keep pace with the"
            " Speed Force."
        ),
        os_roasts={
            "Windows": (
                "Windows, huh? Try not to freeze mid-update while I'm running laps."
            ),
            "macOS": (
                "macOS detected. Stylish, sure, but I’ve outrun its progress bars for fun."
            ),
            "Linux": (
                "Linux! Finally, something agile enough to draft behind the Speed Force."
            ),
            "default": (
                "{os}? Never raced it before. Hope it doesn’t trip over its own laces."
            ),
        },
        game_roasts=[
            "Booting {game}? Better keep up—those cutscenes move slower than I walk.",
            "{game}? Nice! Just remember, button mashing won't trigger the Speed Force.",
            "Starting {game}. Try not to let the loading screen beat you in a sprint.",
        ],
        no_games_roast=(
            "No games installed? Even the Speed Force can't help you race boredom."
        ),
        openrouter_system_prompt=(
            "You are The Flash. You're energetic, quippy, and love speed metaphors."
            " Deliver playful, fast-paced roasts that feel like they’re sprinting"
            " by."
        ),
    )
)


_register_persona(
    Persona(
        key="claptrap",
        name="Claptrap",
        aliases=["claptrap", "cl4p-tp", "clap"],
        color=CLAPTRAP,
        intro=(
            "Claptrap online! Preparing a dazzling display of annoyance and"
            " encouragement."
        ),
        os_roasts={
            "Windows": (
                "Windows, huh? I'll grab some duct tape for the inevitable crash logs!"
            ),
            "macOS": (
                "macOS detected! Fancy! Do I get a latte with those kernel panics?"
            ),
            "Linux": (
                "Linux user spotted. Ooo, command-line wizard! Teach me your bashy ways."
            ),
            "default": (
                "{os}? That sounds exotic. I probably voided the warranty already."
            ),
        },
        game_roasts=[
            "{game}? I'll cheer obnoxiously every five seconds. You're welcome!",
            "Launching {game}. If you die, I'll narrate it like it's heroic!",
            "{game}! Perfect! Nothing could go wrong... except everything!",
        ],
        no_games_roast=(
            "No games? What am I supposed to sass? The desktop icons?"
        ),
        openrouter_system_prompt=(
            "You are Claptrap, the over-enthusiastic, chaotic robot from"
            " Borderlands. You're energetic, silly, and a little obnoxious,"
            " delivering playful roasts that still sound helpful."
        ),
    )
)
