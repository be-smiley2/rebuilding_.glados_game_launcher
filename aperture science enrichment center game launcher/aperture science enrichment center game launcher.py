"""Aperture Science Enrichment Center Game Launcher.

This command line tool scans Steam libraries and reports installed games
without requiring the Steam client to be running.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Sequence

from ai_personas import (
    DEFAULT_PERSONA_KEY,
    PERSONAS,
    Persona,
    persona_say,
    roast_games,
    roast_os,
)
from ansi_colors import SYSTEM_ALERT, SYSTEM_HEADER, SYSTEM_PRIMARY, SYSTEM_SUCCESS
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
    print(f"{SYSTEM_HEADER}{message}")


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


def command_loop() -> None:
    """Main interactive loop supporting persona switching and roasting."""

    current: Persona = PERSONAS[DEFAULT_PERSONA_KEY]
    announce_system_welcome()
    persona_say(current, "Welcome to the Aperture Science Enrichment Center Game Launcher!")
    persona_say(current, current.intro)
    roast_os(current)

    while True:
        prompt = (
            "\nCommands: scan | games, glados, cs, kf, barry, flash, claptrap, help, or exit.\n"
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
                " 'glados', 'cs', 'kf', 'barry', 'flash', or 'claptrap'.",
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
