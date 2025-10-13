"""Aperture Science Enrichment Center Game Launcher.

This simple command line tool can scan a computer for Steam libraries and
report the games that are installed without requiring the Steam client to be
running in the background.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


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
            if game is not None:
                games.append(game)

    return games


def print_game_report(games: Sequence[SteamGame]) -> None:
    """Display the discovered games to the user."""

    if not games:
        print("No Steam games were detected on this system.")
        print("Make sure your Steam libraries are installed on local drives.")
        return

    print(f"Found {len(games)} Steam game(s):\n")
    for game in games:
        print(f"- {game.pretty()}\n")


def main() -> None:
    """Entry point for the command line application."""

    print("\033[33mWelcome to the Aperture Science Enrichment Center Game Launcher!\033[0m")

    if input("what you want me to do?") == "check for games":
        libraries = discover_steam_libraries()
        games = find_installed_games(libraries)
        print_game_report(games)
    else:
        print("Unknown command. Try typing 'check for games'.")


if __name__ == "__main__":
    main()

