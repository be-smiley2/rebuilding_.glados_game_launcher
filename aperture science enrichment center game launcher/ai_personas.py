"""Persona definitions and utilities for the Aperture Science launcher."""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import Any, Dict, Sequence

from ansi_colors import CAITLIN_SNOW, GLADOS, KILLER_FROST


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
    message = persona.os_roasts.get(os_name, persona.os_roasts.get("default", ""))
    if message:
        persona_say(persona, message.format(os=os_name))


def roast_games(persona: Persona, games: Sequence[Any]) -> None:
    """Deliver roasts targeted at the discovered games."""

    if not games:
        persona_say(persona, persona.no_games_roast)
        return

    for game in games:
        name = getattr(game, "name", str(game))
        line = random.choice(persona.game_roasts).format(game=name)
        persona_say(persona, line)


PERSONAS: Dict[str, Persona] = {}
DEFAULT_PERSONA_KEY = "glados"


def _register_persona(persona: Persona) -> None:
    PERSONAS[persona.key] = persona
    for alias in persona.aliases:
        PERSONAS[alias] = persona


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
    )
)
