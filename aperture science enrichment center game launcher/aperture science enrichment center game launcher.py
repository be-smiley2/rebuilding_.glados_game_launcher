"""Aperture Science Enrichment Center Game Launcher.

This simple command line tool can scan a computer for Steam libraries and
report the games that are installed without requiring the Steam client to be
running in the background.
"""

from __future__ import annotations

import os
import random
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


EXCLUDED_APP_IDS = {"228980"}
RESET = "\033[0m"


@dataclass
class SteamGame:
    """Simple representation of a Steam game installation."""

    app_id: str
    name: str
    install_dir: Path
    library: Path

    def pretty(self) -> str:
        """Return a nicely formatted string for display to the user."""

        return f"{self.name} (AppID: {self.app_id})\n    Location: {self.install_dir}".strip()


def candidate_steam_roots() -> Sequence[Path]:
    """Return a list of plausible Steam installation roots for the host OS."""

    home = Path.home()
    env_path = os.environ.get("STEAM_PATH")
    candidates = []

    if env_path:
        candidates.append(Path(env_path))

    # Windows defaults
    for env in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        base = os.environ.get(env)
        if base:
            candidates.append(Path(base) / "Steam")

    candidates.append(Path("C:/Program Files (x86)/Steam"))
    candidates.append(Path("C:/Program Files/Steam"))

    # Linux defaults
    candidates.append(home / ".steam/steam")
    candidates.append(home / ".local/share/Steam")
    candidates.append(Path("/usr/lib/steam"))

    # macOS defaults
    candidates.append(home / "Library/Application Support/Steam")

    # Deduplicate while preserving order.
    seen = set()
    unique: List[Path] = []
    for path in candidates:
        norm = path.resolve() if path.exists() else path
        if norm not in seen:
            seen.add(norm)
            unique.append(path)

    return unique


def parse_libraryfolders(library_file: Path) -> List[Path]:
    """Parse ``libraryfolders.vdf`` to discover additional Steam libraries."""

    libraries: List[Path] = []
    text = library_file.read_text(encoding="utf-8", errors="ignore")

    for match in re.finditer(r"\"path\"\s*\"([^\"]+)\"", text):
        path = Path(match.group(1)).expanduser()
        libraries.append(path / "steamapps")

    return libraries


def discover_steam_libraries() -> List[Path]:
    """Return a list of Steam library ``steamapps`` directories."""

    libraries: List[Path] = []

    for root in candidate_steam_roots():
        steamapps = root / "steamapps"
        if steamapps.exists():
            libraries.append(steamapps)

            library_file = steamapps / "libraryfolders.vdf"
            if library_file.exists():
                libraries.extend(parse_libraryfolders(library_file))

    # Filter to directories that actually exist.
    unique: List[Path] = []
    seen = set()
    for lib in libraries:
        try:
            resolved = lib.resolve()
        except FileNotFoundError:
            continue
        if resolved not in seen and resolved.exists():
            seen.add(resolved)
            unique.append(resolved)

    return unique


def parse_manifest(manifest_path: Path) -> SteamGame | None:
    """Extract game information from a Steam ``appmanifest_*.acf`` file."""

    text = manifest_path.read_text(encoding="utf-8", errors="ignore")
    app_id_match = re.search(r"\"appid\"\s*\"(\d+)\"", text)
    name_match = re.search(r"\"name\"\s*\"([^\"]+)\"", text)
    install_match = re.search(r"\"installdir\"\s*\"([^\"]+)\"", text)

    if not (app_id_match and name_match and install_match):
        return None

    install_dir = manifest_path.parent / "common" / install_match.group(1)
    return SteamGame(
        app_id=app_id_match.group(1),
        name=name_match.group(1),
        install_dir=install_dir,
        library=manifest_path.parent,
    )


def find_installed_games(libraries: Iterable[Path]) -> List[SteamGame]:
    """Return a list of ``SteamGame`` objects for installed titles."""

    games: List[SteamGame] = []

    for library in libraries:
        manifest_paths = sorted(library.glob("appmanifest_*.acf"))
        for manifest in manifest_paths:
            game = parse_manifest(manifest)
            if game is not None and game.app_id not in EXCLUDED_APP_IDS:
                games.append(game)

    return games


def print_game_report(games: Sequence[SteamGame]) -> None:
    """Display the discovered games to the user."""

    if not games:
        print("No Steam games were detected on this system.")
        print("Make sure your Steam libraries are installed on local drives.")
        return

    print(f"Found {len(games)} Steam game(s):\n")
    for index, game in enumerate(games, start=1):
        print(f"{index}. {game.pretty()}\n")


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

    print(f"{persona.color}{message}{RESET}")


def roast_os(persona: Persona) -> None:
    """Deliver an operating-system specific roast from the persona."""

    os_name = detect_os_name()
    message = persona.os_roasts.get(os_name, persona.os_roasts.get("default", ""))
    if message:
        persona_say(persona, message.format(os=os_name))


def roast_games(persona: Persona, games: Sequence[SteamGame]) -> None:
    """Deliver roasts targeted at the discovered games."""

    if not games:
        persona_say(persona, persona.no_games_roast)
        return

    for game in games:
        line = random.choice(persona.game_roasts).format(game=game.name)
        persona_say(persona, line)


PERSONAS: Dict[str, Persona] = {}


def _register_persona(persona: Persona) -> None:
    PERSONAS[persona.key] = persona
    for alias in persona.aliases:
        PERSONAS[alias] = persona


_register_persona(
    Persona(
        key="glados",
        name="GLaDOS",
        aliases=["glados", "g", "glad"],
        color="\033[33m",
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
        color="\033[36m",
        intro=(
            "Hi, I'm Caitlin. Let's keep things cool—unlike that operating system of"
            " yours."
        ),
        os_roasts={
            "Windows": (
                "Windows again? I've seen lab equipment with fewer crashes."
            ),
            "macOS": (
                "macOS—stylish, sure, but even Barry runs faster than its updates."
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
        color="\033[34m",
        intro=(
            "Killer Frost reporting in. Let's see what I can freeze solid—maybe"
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
            "Firing up {game}. Try not to slip—I'd hate to mop up the disaster.",
            "{game} again? Fine. I'll frost the bugs before they frost you.",
        ],
        no_games_roast=(
            "No games? Figures. Even digital entertainment wants nothing to do with that rig."
        ),
    )
)
def launch_game(game: SteamGame) -> bool:
    """Launch the given Steam game using the system Steam handler."""

    uri = f"steam://run/{game.app_id}"

    if sys.platform.startswith("win"):
        command = ["cmd", "/c", "start", "", uri]
    elif sys.platform.startswith("darwin"):
        command = ["open", uri]
    else:
        command = ["xdg-open", uri]

    try:
        subprocess.run(command, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"Failed to launch {game.name}: {exc}")
        return False

    return True


def prompt_for_launch(games: Sequence[SteamGame]) -> None:
    """Prompt the user to pick a game to launch via Steam."""

    if not games:
        return

    while True:
        choice = input(
            "Enter the number of a game to launch it (or press Enter to exit): "
        ).strip()

        if choice == "":
            break

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        index = int(choice)
        if not 1 <= index <= len(games):
            print("That number is out of range.")
            continue

        game = games[index - 1]
        print(f"Launching {game.name}...")
        if launch_game(game):
            print("Launch command sent to Steam. Enjoy your game!")
        break


def command_loop() -> None:
    """Main interactive loop supporting persona switching and roasting."""

    current = PERSONAS["glados"]
    persona_say(current, "Welcome to the Aperture Science Enrichment Center Game Launcher!")
    persona_say(current, current.intro)
    roast_os(current)

    while True:
        prompt = (
            "\nCommands: scan | games, glados, cs, kf, help, or exit.\n"
            f"{current.name} awaits your input: "
        )
        command = input(prompt).strip().lower()

        if command in {"exit", "quit"}:
            persona_say(current, "Shutting down observation. Try not to break anything.")
            break

        if command in {"help", "?"}:
            persona_say(
                current,
                "Type 'scan' to look for games, or switch personalities with"
                " 'glados', 'cs', or 'kf'.",
            )
            continue

        if command in PERSONAS:
            next_persona = PERSONAS[command]
            if next_persona is current:
                persona_say(current, "Still here. Your short-term memory needs calibration.")
            else:
                current = next_persona
                persona_say(current, f"Switched persona to {current.name}.")
                persona_say(current, current.intro)
                roast_os(current)
            continue

        if command in {"check for games", "scan", "games"}:
            libraries = discover_steam_libraries()
            games = find_installed_games(libraries)
            print_game_report(games)
            roast_games(current, games)
            prompt_for_launch(games)
            continue

        persona_say(
            current,
            "Unrecognized input. Either run a scan or pick a persona before the"
            " boredom sets in.",
        )


def main() -> None:
    """Entry point for the command line application."""

    command_loop()


if __name__ == "__main__":
    main()
