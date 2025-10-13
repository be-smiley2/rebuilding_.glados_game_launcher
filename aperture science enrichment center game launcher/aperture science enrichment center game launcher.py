"""Aperture Science Enrichment Center Game Launcher.

This simple command line tool can scan a computer for Steam libraries and
report the games that are installed without requiring the Steam client to be
running in the background.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


EXCLUDED_APP_IDS = {"228980"}

EXECUTABLE_SUFFIXES = {
    ".exe",
    ".bat",
    ".cmd",
    ".sh",
    ".appimage",
    ".x86",
    ".x86_64",
    ".bin",
}


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
    for idx, game in enumerate(games, start=1):
        print(f"{idx}. {game.pretty()}\n")


def is_launchable(path: Path) -> bool:
    """Return ``True`` if *path* looks like a launchable executable."""

    if path.suffix.lower() in EXECUTABLE_SUFFIXES:
        return True

    if path.is_file() and os.access(path, os.X_OK) and not path.suffix:
        return True

    return False


def discover_game_executables(install_dir: Path, max_depth: int = 2, limit: int = 20) -> List[Path]:
    """Return a list of plausible executables within *install_dir*."""

    if not install_dir.exists():
        return []

    executables: List[Path] = []

    for root, dirs, files in os.walk(install_dir):
        try:
            rel_parts = Path(root).relative_to(install_dir).parts
        except ValueError:
            rel_parts = ()

        if len(rel_parts) > max_depth:
            dirs[:] = []
            continue

        for file in files:
            candidate = Path(root) / file
            if is_launchable(candidate):
                executables.append(candidate)
                if len(executables) >= limit:
                    return sorted(executables)

    return sorted(executables)


def choose_from_list(options: Sequence[str], prompt: str) -> int | None:
    """Prompt the user to pick from *options* and return the index or ``None``."""

    while True:
        response = input(prompt).strip()
        if not response or response.lower() in {"q", "quit", "exit"}:
            return None

        if response.isdigit():
            idx = int(response) - 1
            if 0 <= idx < len(options):
                return idx

        print("Please enter a valid number from the list or press Enter to cancel.")


def launch_game(game: SteamGame) -> None:
    """Attempt to launch *game* by running one of its executables."""

    executables = discover_game_executables(game.install_dir)

    if not executables:
        print("No launchable executables were found in this game's installation directory.")
        print("Try launching it manually from:")
        print(f"    {game.install_dir}")
        return

    if len(executables) == 1:
        selection = executables[0]
    else:
        print("Select an executable to run:")
        for idx, option in enumerate(executables, 1):
            rel = option.relative_to(game.install_dir)
            print(f"  [{idx}] {rel}")

        if len(executables) >= 20:
            print("  ... list truncated. Refine your search if your desired executable is missing.")

        choice = choose_from_list(
            [str(path) for path in executables],
            "Enter the number of the executable to launch (or press Enter to cancel): ",
        )

        if choice is None:
            print("Launch cancelled.")
            return

        selection = executables[choice]

    try:
        subprocess.Popen([str(selection)], cwd=selection.parent)
    except OSError as exc:
        print(f"Failed to launch the game: {exc}")
        return

    print(f"Launching '{game.name}' using {selection}... Enjoy!")


def main() -> None:
    """Entry point for the command line application."""

    print("\033[33mWelcome to the Aperture Science Enrichment Center Game Launcher!")
    print("Type 'scan' to search for installed games, or press Enter to exit.\033[0m")

    while True:
        command = input("What do you want me to do? ").strip().lower()

        if not command:
            print("Goodbye.")
            return

        if command in {"scan", "check", "check for games", "games"}:
            print("\033[32mScanning for Steam libraries...\033[0m")
            libraries = discover_steam_libraries()
            games = find_installed_games(libraries)

            if not games:
                print("No games were found. Make sure your Steam libraries are accessible.")
                continue

            print_game_report(games)

            print("Enter the number of a game to launch it, or press Enter to skip.")
            options = [game.pretty() for game in games]
            selection = choose_from_list(options, "Launch which game? ")

            if selection is None:
                print("No game selected.")
                continue

            launch_game(games[selection])
        else:
            print("Unknown command. Try typing 'scan' to search for games or press Enter to exit.")


if __name__ == "__main__":
    main()
