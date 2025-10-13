"""Aperture Science Enrichment Center Game Launcher.

This simple command line tool can scan a computer for Steam libraries and
report the games that are installed without requiring the Steam client to be
running in the background.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


EXCLUDED_APP_IDS = {"228980"}


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


def main() -> None:
    """Entry point for the command line application."""

    print("\033[33mWelcome to the Aperture Science Enrichment Center Game Launcher!")

    command = input("What you want me to do? ").strip().lower()

    if command in {"check for games", "scan", "games"}:
        print("\033[32m")
        libraries = discover_steam_libraries()
        games = find_installed_games(libraries)
        print_game_report(games)
        prompt_for_launch(games)
        print("\033[0m")
    else:
        print("Unknown command. Try typing 'check for games'.")


if __name__ == "__main__":
    main()
