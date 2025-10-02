"""Platform scanning utilities."""
from __future__ import annotations

import json
import os
import platform
import re
from pathlib import Path
from typing import Dict, List

from .dependencies import winreg


class SmartGameScanner:
    def __init__(self) -> None:
        self.last_scan_time = 0
        self.confidence_weights = {"steam": 0.95, "epic": 0.85, "ubisoft": 0.75, "gog": 0.90}

    def scan_all_platforms(self) -> Dict[str, List[Dict]]:
        results = {"steam": [], "epic": [], "ubisoft": [], "gog": []}
        print(f"Starting platform scan on {platform.system()}")

        try:
            if platform.system() == "Windows":
                print("Scanning Windows platforms...")
                results["steam"] = self.scan_steam_windows()
                print(f"Steam scan found {len(results['steam'])} games")

                results["epic"] = self.scan_epic_windows()
                print(f"Epic scan found {len(results['epic'])} games")

                results["ubisoft"] = self.scan_ubisoft_windows()
                print(f"Ubisoft scan found {len(results['ubisoft'])} games")

                results["gog"] = self.scan_gog_windows()
                print(f"GOG scan found {len(results['gog'])} games")

            elif platform.system() == "Darwin":
                print("Scanning macOS platforms...")
                results["steam"] = self.scan_steam_mac()
                print(f"Steam scan found {len(results['steam'])} games")

            else:  # Linux
                print("Scanning Linux platforms...")
                results["steam"] = self.scan_steam_linux()
                print(f"Steam scan found {len(results['steam'])} games")
        except Exception as exc:
            print(f"Platform scan error: {exc}")

        for platform_name, games in results.items():
            if games:
                filtered_games = self.apply_smart_filtering(games, platform_name)
                results[platform_name] = filtered_games
                print(f"Filtered {platform_name}: {len(filtered_games)} games after filtering")

        return results

    def apply_smart_filtering(self, games: List[Dict], platform_name: str) -> List[Dict]:
        filtered: List[Dict] = []
        base_confidence = self.confidence_weights.get(platform_name, 0.7)

        for game in games:
            confidence = self.calculate_confidence(game, base_confidence)
            if confidence > 0.6:
                game["confidence"] = confidence
                filtered.append(game)

        return sorted(filtered, key=lambda game: game.get("confidence", 0), reverse=True)

    def calculate_confidence(self, game: Dict, base_confidence: float) -> float:
        name = game.get("name", "").lower()

        popular_keywords = ["steam", "portal", "half-life", "counter-strike"]
        if any(keyword in name for keyword in popular_keywords):
            base_confidence += 0.1

        suspicious = ["test", "demo", "redistributable", "runtime"]
        if any(sus in name for sus in suspicious):
            base_confidence -= 0.3

        return max(0.0, min(1.0, base_confidence))

    def scan_steam_windows(self) -> List[Dict]:
        games: List[Dict] = []
        all_games: Dict[str, Dict] = {}
        print("Scanning Steam on Windows...")

        steam_paths_to_try = []

        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam")
            steam_path = Path(winreg.QueryValueEx(key, "InstallPath")[0])
            winreg.CloseKey(key)
            if steam_path.exists():
                steam_paths_to_try.append(steam_path)
                print(f"Found Steam via registry: {steam_path}")
        except Exception as exc:
            print(f"Registry lookup failed: {exc}")

        common_paths = [
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Steam",
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Steam",
            Path("C:\\Steam"),
            Path.home() / "Steam",
        ]

        for path in common_paths:
            if path.exists() and path not in steam_paths_to_try:
                steam_paths_to_try.append(path)
                print(f"Found Steam at common path: {path}")

        for steam_path in steam_paths_to_try:
            steamapps_path = steam_path / "steamapps"
            if steamapps_path.exists():
                print(f"Scanning steamapps at: {steamapps_path}")
                found_games = self.scan_steam_library(steamapps_path)

                for game in found_games:
                    game_key = f"{game['game_id']}_{game['name']}"
                    if game_key not in all_games:
                        all_games[game_key] = game

                print(f"Found {len(found_games)} games in this Steam library")

        games = list(all_games.values())
        print(f"Steam scan complete: {len(games)} unique games found")
        return games

    def scan_steam_mac(self) -> List[Dict]:
        steam_path = Path.home() / "Library/Application Support/Steam"
        return self.scan_steam_library(steam_path / "steamapps") if steam_path.exists() else []

    def scan_steam_linux(self) -> List[Dict]:
        for path in [Path.home() / ".steam/steam", Path.home() / ".local/share/Steam"]:
            if path.exists():
                return self.scan_steam_library(path / "steamapps")
        return []

    def scan_steam_library(self, steamapps_path: Path) -> List[Dict]:
        games: List[Dict] = []
        print(f"Scanning Steam library at: {steamapps_path}")

        try:
            acf_files = list(steamapps_path.glob("appmanifest_*.acf"))
            print(f"Found {len(acf_files)} .acf manifest files")

            if len(acf_files) == 0:
                print("No .acf files found in this library")
                return games

            processed_count = 0
            valid_games_count = 0

            for acf_file in acf_files:
                processed_count += 1

                try:
                    content = None
                    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                        try:
                            with open(acf_file, "r", encoding=encoding, errors="ignore") as handle:
                                content = handle.read()
                            break
                        except UnicodeDecodeError:
                            continue

                    if not content:
                        print(f"Could not read file: {acf_file}")
                        continue

                    app_id_match = re.search(r'"appid"\s*"(\d+)"', content)
                    name_match = re.search(r'"name"\s*"([^"]+)"', content)

                    if app_id_match and name_match:
                        app_id = app_id_match.group(1)
                        name = name_match.group(1)

                        if self.is_valid_game(name):
                            games.append(
                                {
                                    "name": name,
                                    "platform": "steam",
                                    "game_id": app_id,
                                    "store_url": f"https://store.steampowered.com/app/{app_id}/",
                                    "detected": True,
                                }
                            )
                            valid_games_count += 1
                            if valid_games_count % 10 == 0:
                                print(f"Progress: {valid_games_count} valid games found so far...")
                        else:
                            print(f"Filtered out non-game: {name}")
                    else:
                        print(f"Could not parse app data from: {acf_file.name}")

                except Exception as exc:
                    print(f"Error processing {acf_file.name}: {exc}")
                    continue

            print(f"Processed {processed_count} manifest files, found {valid_games_count} valid games")

        except Exception as exc:
            print(f"Error scanning Steam library: {exc}")
            import traceback

            traceback.print_exc()

        print(f"Steam library scan complete: {len(games)} valid games found")
        return games

    def is_valid_game(self, name: str) -> bool:
        if not name or len(name) < 3:
            return False
        name_lower = name.lower().strip()

        exact_exclusions = {
            "steamworks common redistributables",
            "steam linux runtime",
            "steam linux runtime soldier",
            "steamvr",
            "proton easy anti cheat runtime",
        }
        if name_lower in exact_exclusions:
            return False

        keyword_exclusions = [
            "steamworks",
            "steam linux runtime",
            "proton",
            "steamvr",
            "directx",
            "visual c++",
            "vcredist",
            "redistributable",
            "runtime",
            "benchmark",
            "dedicated server",
            "server tool",
            "mod tools",
            "workshop tools",
            "sdk",
            "soundtrack",
            "original soundtrack",
            "ost",
            "test app",
            "launcher",
            "compatibility tool",
            "tools ",
            " tool",
        ]
        if any(keyword in name_lower for keyword in keyword_exclusions):
            return False

        tokens = [token for token in re.split(r"[^a-z0-9]+", name_lower) if token]
        token_exclusions = {"demo", "test", "beta", "benchmark", "soundtrack", "sdk", "editor", "tools", "tool"}
        if any(token in token_exclusions for token in tokens):
            return False

        return True

    def scan_epic_windows(self) -> List[Dict]:
        games: List[Dict] = []
        print("Scanning Epic Games on Windows...")

        try:
            epic_paths = [
                Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Epic/EpicGamesLauncher/Data/Manifests",
                Path(os.environ.get("LOCALAPPDATA", "")) / "EpicGamesLauncher/Saved/Config/Windows",
            ]

            for epic_path in epic_paths:
                if not epic_path.exists():
                    print(f"Epic path does not exist: {epic_path}")
                    continue

                print(f"Scanning Epic path: {epic_path}")
                manifest_files = list(epic_path.glob("*.item")) + list(epic_path.glob("*.manifest"))
                print(f"Found {len(manifest_files)} Epic manifest files")

                for manifest in manifest_files:
                    try:
                        with open(manifest, "r", encoding="utf-8", errors="ignore") as handle:
                            data = json.load(handle)

                        name = data.get("DisplayName") or data.get("AppName") or data.get("LaunchCommand", "")
                        game_id = data.get("CatalogItemId") or data.get("AppName") or data.get("InstallationGuid", "")

                        if name and game_id and self.is_valid_game(name):
                            games.append(
                                {
                                    "name": name,
                                    "platform": "epic",
                                    "game_id": game_id,
                                    "store_url": "https://store.epicgames.com/",
                                    "detected": True,
                                }
                            )
                            print(f"Found Epic game: {name}")
                    except Exception as exc:
                        print(f"Error processing Epic manifest {manifest.name}: {exc}")
                        continue

        except Exception as exc:
            print(f"Error scanning Epic Games: {exc}")

        print(f"Total Epic games found: {len(games)}")
        return games

    def scan_ubisoft_windows(self) -> List[Dict]:
        games: List[Dict] = []
        print("Scanning Ubisoft Connect on Windows...")

        try:
            registry_paths = [r"SOFTWARE\\WOW6432Node\\Ubisoft", r"SOFTWARE\\Ubisoft"]

            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    index = 0

                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, index)
                            game_key = None

                            try:
                                game_key = winreg.OpenKey(key, subkey_name)

                                try:
                                    name = winreg.QueryValueEx(game_key, "DisplayName")[0]
                                except Exception:
                                    try:
                                        name = winreg.QueryValueEx(game_key, "InstallDir")[0]
                                        name = Path(name).name if name else subkey_name
                                    except Exception:
                                        name = subkey_name

                                if name and self.is_valid_game(name):
                                    games.append(
                                        {
                                            "name": name,
                                            "platform": "ubisoft",
                                            "game_id": subkey_name,
                                            "store_url": "https://store.ubi.com/",
                                            "detected": True,
                                        }
                                    )
                                    print(f"Found Ubisoft game: {name}")
                            finally:
                                if game_key:
                                    winreg.CloseKey(game_key)

                            index += 1
                        except OSError:
                            break

                    winreg.CloseKey(key)
                except Exception as exc:
                    print(f"Could not access registry path {reg_path}: {exc}")
                    continue

        except Exception as exc:
            print(f"Error scanning Ubisoft games: {exc}")

        print(f"Total Ubisoft games found: {len(games)}")
        return games

    def scan_gog_windows(self) -> List[Dict]:
        games: List[Dict] = []
        print("Scanning GOG Galaxy on Windows...")

        try:
            registry_paths = [r"SOFTWARE\\WOW6432Node\\GOG.com\\Games", r"SOFTWARE\\GOG.com\\Games"]

            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    index = 0

                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, index)
                            game_key = None

                            try:
                                game_key = winreg.OpenKey(key, subkey_name)

                                try:
                                    name = winreg.QueryValueEx(game_key, "gameName")[0]
                                except Exception:
                                    try:
                                        name = winreg.QueryValueEx(game_key, "gameID")[0]
                                    except Exception:
                                        name = subkey_name

                                if name and self.is_valid_game(name):
                                    games.append(
                                        {
                                            "name": name,
                                            "platform": "gog",
                                            "game_id": subkey_name,
                                            "store_url": "https://www.gog.com/",
                                            "detected": True,
                                        }
                                    )
                                    print(f"Found GOG game: {name}")
                            finally:
                                if game_key:
                                    winreg.CloseKey(game_key)

                            index += 1
                        except OSError:
                            break

                    winreg.CloseKey(key)
                except Exception as exc:
                    print(f"Could not access registry path {reg_path}: {exc}")
                    continue

        except Exception as exc:
            print(f"Error scanning GOG games: {exc}")

        print(f"Total GOG games found: {len(games)}")
        return games


__all__ = ["SmartGameScanner"]
