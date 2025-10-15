"""Persona definitions and utilities for the Aperture Science launcher."""

from __future__ import annotations

import json
import os
import random
import socket
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, Sequence, Tuple
from urllib import error, request

from ansi_colors import (
    APERTURE_SYSTEM,
    CAITLIN_SNOW,
    CLAPTRAP,
    FLASH,
    GLADOS,
    KILLER_FROST,
)

try:  # Optional dependency for secure key storage
    import keyring  # type: ignore[import]
except ImportError:  # pragma: no cover - optional dependency
    keyring = None  # type: ignore[assignment]


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
OPENROUTER_USAGE_URL = "https://openrouter.ai/api/v1/usage"
OPENROUTER_USER_URL = "https://openrouter.ai/api/v1/user"
FREE_MODELS_FILE = Path(__file__).with_name("openrouter ai models.py")
_FREE_MODEL_CACHE: list[str] | None = None
_HAS_WARNED_MISSING_KEY = False


def _read_api_key_file(path: Path) -> str | None:
    """Return the API key stored in ``path`` when present."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    key = text.strip()
    return key or None


def _read_key_from_env_file(key_name: str) -> str | None:
    """Return ``key_name`` from nearby dotenv files when present."""

    env_override = os.getenv("OPENROUTER_ENV_FILE")
    candidates = []
    if env_override:
        candidates.append(Path(env_override).expanduser())

    module_dir = Path(__file__).resolve().parent
    candidates.append(module_dir / ".env")
    parent_env = module_dir.parent / ".env"
    if parent_env not in candidates:
        candidates.append(parent_env)

    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            if name.strip() != key_name:
                continue
            candidate = value.strip().strip('"').strip("'")
            return candidate or None

    return None


def _read_key_from_keyring() -> str | None:
    """Attempt to fetch the API key using the OS keyring when available."""

    if keyring is None:
        return None

    service = os.getenv("OPENROUTER_KEYRING_SERVICE", "openrouter")
    username = os.getenv("OPENROUTER_KEYRING_USERNAME", "aperture_launcher")
    if not service or not username:
        return None

    try:
        secret = keyring.get_password(service, username)
    except Exception:
        return None

    return secret.strip() if secret else None


def keyring_available() -> bool:
    """Return True when the optional keyring backend is usable."""

    return keyring is not None


def keyring_has_openrouter_secret() -> bool:
    """Return True when the keyring already stores an OpenRouter API key."""

    return _read_key_from_keyring() is not None


def store_openrouter_api_key(secret: str) -> bool:
    """Persist the OpenRouter API key to the system keyring when supported."""

    if keyring is None:
        return False

    secret = secret.strip()
    if not secret:
        return False

    service = os.getenv("OPENROUTER_KEYRING_SERVICE", "openrouter")
    username = os.getenv("OPENROUTER_KEYRING_USERNAME", "aperture_launcher")
    if not service or not username:
        return False

    try:
        keyring.set_password(service, username, secret)
    except Exception:
        return False
    return True


def delete_openrouter_api_key() -> bool:
    """Remove the OpenRouter API key from the system keyring when supported."""

    if keyring is None:
        return False

    service = os.getenv("OPENROUTER_KEYRING_SERVICE", "openrouter")
    username = os.getenv("OPENROUTER_KEYRING_USERNAME", "aperture_launcher")
    if not service or not username:
        return False

    try:
        keyring.delete_password(service, username)
    except Exception:
        return False
    return True


def _stringify_usage_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"{value}"
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        items = [
            f"{key}={val}"
            for key, val in value.items()
            if isinstance(val, (int, float, str))
        ]
        if items:
            return ", ".join(items)
    return None


def _summarize_usage_payload(payload: Any) -> str | None:
    if isinstance(payload, dict):
        candidates = []
        for key in ("remaining", "balance", "credits", "total", "spent", "limit"):
            if key not in payload:
                continue
            text = _stringify_usage_value(payload[key])
            if text:
                candidates.append(f"{key}: {text}")
        if candidates:
            return "; ".join(candidates)
        for key in ("data", "usage", "totals"):
            if key in payload:
                summary = _summarize_usage_payload(payload[key])
                if summary:
                    return summary
    if isinstance(payload, list):
        for item in payload:
            summary = _summarize_usage_payload(item)
            if summary:
                return summary
    return None


def fetch_openrouter_usage_summary(api_key: str) -> str | None:
    """Return a human readable usage summary for the supplied API key."""

    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for url in (OPENROUTER_USAGE_URL, OPENROUTER_USER_URL):
        http_request = request.Request(url, headers=headers)
        try:
            with request.urlopen(http_request, timeout=10) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            if exc.code == 404:
                continue
            return None
        except (error.URLError, TimeoutError, socket.timeout):
            return None

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None

        summary = _summarize_usage_payload(payload)
        if summary:
            return summary

    return None


def _load_local_free_models() -> list[str]:
    """Return model slugs stored in the repository list when available."""

    try:
        text = FREE_MODELS_FILE.read_text(encoding="utf-8")
    except OSError:
        return []

    models: list[str] = []
    for line in text.splitlines():
        slug = line.strip()
        if not slug or slug.startswith("#"):
            continue
        models.append(slug)

    return models


def get_openrouter_api_key() -> str | None:
    """Return the OpenRouter API key from the environment or helper files."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key.strip() or None

    api_key = _read_key_from_keyring()
    if api_key:
        return api_key

    file_override = os.getenv("OPENROUTER_API_KEY_FILE")
    if file_override:
        key_path = Path(file_override).expanduser()
        key = _read_api_key_file(key_path)
        if key:
            return key

    api_key = _read_key_from_env_file("OPENROUTER_API_KEY")
    if api_key:
        return api_key

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


def compose_os_roast(
    persona: Persona,
    allow_dynamic: bool = True,
    model: str | None = None,
) -> str:
    """Return the roast a persona would deliver for the current operating system."""

    os_name = detect_os_name()
    dynamic = None
    if allow_dynamic:
        dynamic = generate_openrouter_roast(
            persona,
            (
                "The user is running {os} as their operating system."
                " Deliver a concise roast in your trademark voice."
            ).format(os=os_name),
            model=model,
        )
    if dynamic:
        return dynamic

    template = persona.os_roasts.get(os_name) or persona.os_roasts.get("default")
    if template:
        return template.format(os=os_name)
    return f"{persona.name} is temporarily speechless about {os_name}."


def compose_game_roasts(
    persona: Persona,
    games: Sequence[Any],
    allow_dynamic: bool = True,
    model: str | None = None,
) -> list[str]:
    """Return the roast lines a persona would deliver for the supplied games."""

    if not games:
        dynamic = None
        if allow_dynamic:
            dynamic = generate_openrouter_roast(
                persona,
                "Roast the user for having no games installed in their Steam library.",
                model=model,
            )
        if dynamic:
            return [dynamic]
        return [persona.no_games_roast]

    lines: list[str] = []
    for game in games:
        name = getattr(game, "name", str(game))
        dynamic = None
        if allow_dynamic:
            dynamic = generate_openrouter_roast(
                persona,
                (
                    "Roast the user for preparing to launch the game {game}."
                    " Keep it playful, a single sentence, and unmistakably in your voice."
                ).format(game=name),
                model=model,
            )
        if dynamic:
            lines.append(dynamic)
        else:
            template = random.choice(persona.game_roasts)
            lines.append(template.format(game=name))

    return lines


def compose_chat_reply(
    persona: Persona,
    user_message: str,
    allow_dynamic: bool = True,
    model: str | None = None,
    history: Sequence[Tuple[str, str]] | None = None,
) -> str:
    """Return a short persona-flavoured reply for the given chat message."""

    cleaned = user_message.strip() or "..."
    history_text = ""
    if history:
        recent = history[-6:]
        formatted = [
            f"{speaker}: {text}" for speaker, text in recent if speaker and text
        ]
        if formatted:
            history_text = "\n".join(formatted)

    if allow_dynamic:
        if history_text:
            prompt = (
                "Maintain this chat as {name}. Previous dialogue:\n{history}\n"
                "User: \"{message}\".\nReply in one or two sentences in character,"
                " keeping the conversation coherent."
            ).format(history=history_text, message=cleaned, name=persona.name)
        else:
            prompt = (
                "The user says: \"{message}\"."
                " Reply as {name} in one or two sentences, keeping your signature tone."
            ).format(message=cleaned, name=persona.name)
        dynamic = generate_openrouter_roast(persona, prompt, model=model)
        if dynamic:
            return dynamic

    fallback_templates = [
        "{name}: Noted. Try not to let '{topic}' trigger the turret defenses.",
        "{name} contemplates '{topic}' and files it under 'interesting test results'.",
        "Regarding '{topic}', {name} recommends minimal property damage.",
        "{name} heard '{topic}'. Laboratory sarcasm buffer engaged.",
        "Message '{topic}' received. {name} assures you the neurotoxin emitters remain offline. For now.",
    ]
    if history_text:
        fallback_templates.append(
            "{name} reviews the earlier test logs and decides '{topic}' ranks above cake in priority."
        )
    template = random.choice(fallback_templates)
    return template.format(name=persona.name, topic=cleaned)


def roast_os(persona: Persona) -> None:
    """Deliver an operating-system specific roast from the persona."""

    persona_say(persona, compose_os_roast(persona))


def roast_games(persona: Persona, games: Sequence[Any]) -> None:
    """Deliver roasts targeted at the discovered games."""

    for line in compose_game_roasts(persona, games):
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
    for key in ("prompt", "completion", "request", "image"):
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

    local_models = _load_local_free_models()

    api_key = get_openrouter_api_key()
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    http_request = request.Request(OPENROUTER_MODELS_URL, headers=headers)

    try:
        with request.urlopen(http_request, timeout=10) as response:
            raw = response.read().decode("utf-8")
    except (error.HTTPError, error.URLError, TimeoutError, socket.timeout):
        if _FREE_MODEL_CACHE is None:
            _FREE_MODEL_CACHE = local_models
        return _FREE_MODEL_CACHE or []

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        if _FREE_MODEL_CACHE is None:
            _FREE_MODEL_CACHE = local_models
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
    elif _FREE_MODEL_CACHE is None:
        _FREE_MODEL_CACHE = local_models

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

        fallback = next((slug for slug in candidates if slug.endswith(":free")), None)
        if fallback:
            return fallback

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
        global _HAS_WARNED_MISSING_KEY
        if not _HAS_WARNED_MISSING_KEY:
            print(
                "OpenRouter API key not found. Set OPENROUTER_API_KEY to enable dynamic roasts.",
                file=sys.stderr,
            )
            _HAS_WARNED_MISSING_KEY = True
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
