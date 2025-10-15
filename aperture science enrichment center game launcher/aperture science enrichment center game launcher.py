"""Aperture Science Enrichment Center Game Launcher.

This command line tool scans Steam libraries and reports installed games
without requiring the Steam client to be running.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Sequence

from ansi_colors import APERTURE_SYSTEM, SYSTEM_ALERT, SYSTEM_PRIMARY, SYSTEM_SUCCESS
from steam_scanner import (
    SteamGame,
    discover_steam_libraries,
    find_installed_games,
    print_game_report,
)


def announce_system_welcome() -> None:
    """Display the Aperture Science system greeting."""

    message = (
        "Aperture Science Enrichment Centre System: "
        "Hello and welcome to the Aperture Science Enrichment Centre Game Launcher."
    )
    print(f"{APERTURE_SYSTEM}{message}")


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
        print(f"{SYSTEM_ALERT}Failed to launch {game.name}: {exc}")
        return False

    return True


def prompt_for_launch(games: Sequence[SteamGame]) -> None:
    """Prompt the user to pick a game to launch via Steam."""

    if not games:
        return

    while True:
        choice = input(
            f"{SYSTEM_PRIMARY}Enter the number of a game to launch it (or press Enter to exit):"
        ).strip()

        if choice == "":
            break

        if not choice.isdigit():
            print(f"{SYSTEM_ALERT}Please enter a valid number.")
            continue

        index = int(choice)
        if not 1 <= index <= len(games):
            print(f"{SYSTEM_ALERT}That number is out of range.")
            continue

        game = games[index - 1]
        print(f"{SYSTEM_PRIMARY}Launching {game.name}...")
        if launch_game(game):
            print(f"{SYSTEM_SUCCESS}Launch command sent to Steam. Enjoy your game!")
        break


def perform_scan() -> list[SteamGame]:
    """Discover Steam games and print the results to the console."""

    libraries = discover_steam_libraries()
    games = find_installed_games(libraries)
    print_game_report(games)
    return list(games)


def command_loop() -> None:
    """Main interactive loop for scanning libraries and launching games."""

    announce_system_welcome()
    print(
        f"{SYSTEM_PRIMARY}Type 'scan' to search for games, 'launch' to pick from the last scan,"
        " or 'exit' to quit."
    )

    cached_games: list[SteamGame] = []

    while True:
        command = input(f"{SYSTEM_PRIMARY}Command (scan/help/launch/exit): ").strip().lower()

        if command in {"exit", "quit"}:
            print(f"{SYSTEM_SUCCESS}Shutting down. See you next test cycle.")
            break

        if command in {"help", "?"}:
            print(
                f"{SYSTEM_PRIMARY}Available commands:\n"
                "  scan   - Search Steam libraries for installed games.\n"
                "  launch - Choose a game from the most recent scan to launch.\n"
                "  help   - Display this message.\n"
                "  exit   - Quit the launcher."
            )
            continue

        if command == "scan":
            cached_games = perform_scan()
            continue

        if command == "launch":
            if not cached_games:
                print(
                    f"{SYSTEM_ALERT}No games are cached yet. Run a scan before launching anything."
                )
                continue
            prompt_for_launch(cached_games)
            continue

        if command in {"games"}:
            cached_games = perform_scan()
            prompt_for_launch(cached_games)
            continue

        print(f"{SYSTEM_ALERT}Unrecognized command. Type 'help' for assistance.")


def main() -> None:
    """Entry point for the command line application."""

    command_loop()


if __name__ == "__main__":
    main()
