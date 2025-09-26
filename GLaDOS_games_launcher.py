#!/usr/bin/env python3
"""
GLaDOS Unified Game Launcher v2.2 - Complete All-in-One Solution with Smart Scanning
Auto-update, Game Management, Multi-platform Support, Crash Prevention, Auto Game Detection
Repository: https://github.com/be-smiley2/glados_game_launcher
"""

import time, random, subprocess, webbrowser, platform, os, sys, re, json, tempfile, zipfile, shutil, winreg
from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional, Tuple, List, Dict

def ensure_module(module_name):
    try:
        return __import__(module_name)
    except ImportError:
        print(f"Installing {module_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        return __import__(module_name)

requests = ensure_module('requests')

# Styling System
class ApertureColors:
    RESET = "\033[0m"
    GLADOS_ORANGE = "\033[38;5;214m"
    WHEATLEY_BLUE = "\033[38;5;117m"
    SYSTEM_CYAN = "\033[38;5;45m"
    ERROR_PINK = "\033[38;5;201m"
    CALLING_PINK = "\033[38;5;201m"
    CONNECTING_YELLOW = "\033[38;5;226m"
    TRANSFERRING_CYAN = "\033[38;5;81m"
    SCANNING_GREEN = "\033[38;5;82m"

class AperturePersonalities:
    GLaDOS = ApertureColors.GLADOS_ORANGE + "(GLaDOS)" + ApertureColors.RESET
    WHEATLEY = ApertureColors.WHEATLEY_BLUE + "(Wheatley)" + ApertureColors.RESET
    SYSTEM = ApertureColors.SYSTEM_CYAN + "(APERTURE-SYS)" + ApertureColors.RESET
    ERROR = ApertureColors.ERROR_PINK + "(ERROR)" + ApertureColors.RESET
    SCANNER = ApertureColors.WHEATLEY_BLUE + "(Wheatley)" + ApertureColors.RESET

# Configuration
REPO_OWNER = "be-smiley2"
REPO_NAME = "glados_game_launcher"
CURRENT_VERSION = "2.2"

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
FIRST_RUN_FLAG = SCRIPT_DIR / '.aperture_first_run_complete'
CATALOG_PATH = SCRIPT_DIR / 'aperture_science_game_catalog.txt'
VERSION_FILE = SCRIPT_DIR / 'version.json'
GAME_DATA_FILE = SCRIPT_DIR / 'game_data.json'
BACKUP_DIR = SCRIPT_DIR / 'backups'

# Smart Game Scanner
class SmartGameScanner:
    def __init__(self):
        self.detected_games = []
        self.steam_games = {}
        self.epic_games = {}
        self.ubisoft_games = {}
        self.gog_games = {}
        
    def scan_all_platforms(self) -> Dict[str, List[Dict]]:
        """Scan all supported platforms for installed games"""
        print(f"{AperturePersonalities.SCANNER} Right! Comprehensive game scan initiated!")
        print(f"{AperturePersonalities.SCANNER} This is brilliant! I'm going to find ALL your games!")
        
        results = {
            'steam': [],
            'epic': [],
            'ubisoft': [],
            'gog': []
        }
        
        if platform.system() == "Windows":
            print(f"{AperturePersonalities.SCANNER} Ooh, Windows! I know where everything is here!")
            results['steam'] = self.scan_steam_windows()
            results['epic'] = self.scan_epic_windows()
            results['ubisoft'] = self.scan_ubisoft_windows()
            results['gog'] = self.scan_gog_windows()
        elif platform.system() == "Darwin":
            print(f"{AperturePersonalities.SCANNER} Mac system detected! Scanning Steam...")
            results['steam'] = self.scan_steam_mac()
        else:
            print(f"{AperturePersonalities.SCANNER} Linux! Open source gaming, very impressive!")
            results['steam'] = self.scan_steam_linux()
        
        total_found = sum(len(games) for games in results.values())
        if total_found > 0:
            print(f"{AperturePersonalities.SCANNER} Fantastic! Found {total_found} games! I'm quite proud of that!")
        else:
            print(f"{AperturePersonalities.SCANNER} Hmm, no games found. That's... odd. Maybe they're hiding?")
        
        return results
    
    def scan_steam_windows(self) -> List[Dict]:
        """Scan Steam installation on Windows"""
        games = []
        try:
            # Check registry for Steam path
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                steam_path = Path(winreg.QueryValueEx(key, "InstallPath")[0])
            
            if not steam_path.exists():
                return games
            
            # Parse libraryfolders.vdf
            library_file = steam_path / "steamapps" / "libraryfolders.vdf"
            if library_file.exists():
                library_paths = self.parse_steam_library_folders(library_file)
            else:
                library_paths = [steam_path / "steamapps"]
            
            # Scan each library folder
            for lib_path in library_paths:
                if lib_path.exists():
                    games.extend(self.scan_steam_library(lib_path))
        
        except (WindowsError, FileNotFoundError, OSError):
            # Try common Steam locations
            common_paths = [
                Path(os.environ.get('PROGRAMFILES', '')) / "Steam",
                Path(os.environ.get('PROGRAMFILES(X86)', '')) / "Steam",
                Path.home() / "Steam"
            ]
            
            for steam_path in common_paths:
                if steam_path.exists():
                    lib_path = steam_path / "steamapps"
                    if lib_path.exists():
                        games.extend(self.scan_steam_library(lib_path))
                    break
        
        return games
    
    def scan_steam_mac(self) -> List[Dict]:
        """Scan Steam installation on macOS"""
        games = []
        steam_path = Path.home() / "Library/Application Support/Steam"
        
        if steam_path.exists():
            lib_path = steam_path / "steamapps"
            if lib_path.exists():
                games.extend(self.scan_steam_library(lib_path))
        
        return games
    
    def scan_steam_linux(self) -> List[Dict]:
        """Scan Steam installation on Linux"""
        games = []
        
        # Common Steam paths on Linux
        steam_paths = [
            Path.home() / ".steam/steam",
            Path.home() / ".local/share/Steam",
            Path("/usr/games/steam")
        ]
        
        for steam_path in steam_paths:
            if steam_path.exists():
                lib_path = steam_path / "steamapps"
                if lib_path.exists():
                    games.extend(self.scan_steam_library(lib_path))
                break
        
        return games
    
    def parse_steam_library_folders(self, library_file: Path) -> List[Path]:
        """Parse Steam's libraryfolders.vdf to find all game library locations"""
        library_paths = []
        
        try:
            with open(library_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find library paths in the VDF format
            import re
            path_matches = re.findall(r'"path"\s*"([^"]+)"', content)
            
            for path_str in path_matches:
                lib_path = Path(path_str.replace('\\\\', '\\')) / "steamapps"
                if lib_path.exists():
                    library_paths.append(lib_path)
        
        except Exception:
            pass
        
        return library_paths
    
    def scan_steam_library(self, steamapps_path: Path) -> List[Dict]:
        """Scan a Steam library folder for installed games"""
        games = []
        
        try:
            # Scan .acf files in steamapps folder
            for acf_file in steamapps_path.glob("*.acf"):
                game_info = self.parse_steam_acf(acf_file)
                if game_info:
                    games.append(game_info)
        
        except Exception:
            pass
        
        return games
    
    def parse_steam_acf(self, acf_file: Path) -> Optional[Dict]:
        """Parse Steam .acf file to extract game information"""
        try:
            with open(acf_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract app ID and name using regex
            app_id_match = re.search(r'"appid"\s*"(\d+)"', content)
            name_match = re.search(r'"name"\s*"([^"]+)"', content)
            
            if app_id_match and name_match:
                app_id = app_id_match.group(1)
                name = name_match.group(1)
                
                # Filter out Steam system components and non-games
                if self.is_steam_game(name, app_id):
                    return {
                        'name': name,
                        'platform': 'steam',
                        'game_id': app_id,
                        'store_url': f"https://store.steampowered.com/app/{app_id}/",
                        'detected': True,
                        'source': 'steam_library'
                    }
        
        except Exception:
            pass
        
        return None
    
    def is_steam_game(self, name: str, app_id: str) -> bool:
        """Filter to determine if a Steam entry is actually a game"""
        if not name:
            return False
            
        name_lower = name.lower().strip()
        
        # Exclude Steam system components
        steam_system_components = [
            'steamworks common redistributables',
            'steam linux runtime',
            'proton',
            'steam vr',
            'steam audio',
            'steam input',
            'directx',
            'visual c++',
            'vcredist',
            'microsoft visual c++',
            '.net framework',
            'xna framework',
            'steam controller configs'
        ]
        
        # Check if it's a known system component
        for component in steam_system_components:
            if component in name_lower:
                return False
        
        # Exclude obvious non-games by app ID ranges (Steam system apps are usually low numbers)
        try:
            app_id_num = int(app_id)
            # Most Steam system components have very low app IDs
            if app_id_num < 100 and 'half-life' not in name_lower and 'counter-strike' not in name_lower:
                return False
        except ValueError:
            pass
        
        # Additional filters for common non-game patterns
        non_game_patterns = [
            'redistributable', 'runtime', 'framework', 'library', 'driver',
            'system', 'tool', 'utility', 'sdk', 'api', 'plugin'
        ]
        
        for pattern in non_game_patterns:
            if pattern in name_lower:
                return False
        
        return True
    
    def scan_epic_windows(self) -> List[Dict]:
        """Scan Epic Games Store installation on Windows"""
        games = []
        
        try:
            epic_path = Path(os.environ.get('LOCALAPPDATA', '')) / "EpicGamesLauncher/Saved/Config/Windows"
            
            if epic_path.exists():
                # Look for game manifest files
                for manifest_file in epic_path.glob("*.item"):
                    game_info = self.parse_epic_manifest(manifest_file)
                    if game_info:
                        games.append(game_info)
        
        except Exception:
            pass
        
        return games
    
    def parse_epic_manifest(self, manifest_file: Path) -> Optional[Dict]:
        """Parse Epic Games manifest file"""
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'DisplayName' in data and 'CatalogItemId' in data:
                return {
                    'name': data['DisplayName'],
                    'platform': 'epic',
                    'game_id': data['CatalogItemId'],
                    'store_url': f"https://store.epicgames.com/en-US/p/{data.get('CatalogNamespace', '')}",
                    'detected': True,
                    'source': 'epic_manifest'
                }
        
        except Exception:
            pass
        
        return None
    
    def scan_ubisoft_windows(self) -> List[Dict]:
        """Scan Ubisoft Connect installation on Windows"""
        games = []
        
        try:
            # Check registry for Ubisoft games
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Ubisoft") as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as game_key:
                            try:
                                display_name = winreg.QueryValueEx(game_key, "DisplayName")[0]
                                
                                # Skip if it's clearly not a game
                                if self.is_definitely_game(display_name):
                                    games.append({
                                        'name': display_name,
                                        'platform': 'ubisoft',
                                        'game_id': subkey_name,
                                        'store_url': f"https://store.ubi.com/us/search/?q={quote_plus(display_name)}",
                                        'detected': True,
                                        'source': 'ubisoft_registry'
                                    })
                            except FileNotFoundError:
                                pass
                        i += 1
                    except OSError:
                        break
        
        except Exception:
            pass
        
        return games
    
    def scan_gog_windows(self) -> List[Dict]:
        """Scan GOG Galaxy installation on Windows"""
        games = []
        
        try:
            # Check registry for GOG games
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games") as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as game_key:
                            try:
                                game_name = winreg.QueryValueEx(game_key, "gameName")[0]
                                
                                # Skip if it's clearly not a game
                                if self.is_definitely_game(game_name):
                                    games.append({
                                        'name': game_name,
                                        'platform': 'gog',
                                        'game_id': subkey_name,
                                        'store_url': f"https://www.gog.com/game/{subkey_name}",
                                        'detected': True,
                                        'source': 'gog_registry'
                                    })
                            except FileNotFoundError:
                                pass
                        i += 1
                    except OSError:
                        break
        
        except Exception:
            pass
        
        return games
    
    def is_definitely_game(self, name: str) -> bool:
        """More restrictive filter - only includes items that are clearly games"""
        if not name:
            return False
            
        name_lower = name.lower().strip()
        
        # Exclude obvious non-games
        non_games = [
            'vlc', 'media player', 'steam', 'launcher', 'installer', 'uninstall',
            'setup', 'config', 'settings', 'preferences', 'cache', 'reset',
            'skinned', 'player', 'browser', 'chrome', 'firefox', 'edge',
            'office', 'word', 'excel', 'powerpoint', 'notepad', 'calculator',
            'control panel', 'task manager', 'registry', 'system'
        ]
        
        # If it contains any non-game keywords, reject it
        for non_game in non_games:
            if non_game in name_lower:
                return False
        
        # Additional checks for common launcher/utility patterns
        if any(pattern in name_lower for pattern in [
            'reset preferences', 'cache files', 'skinned', 'media player'
        ]):
            return False
        
        return True
    
    def is_likely_game(self, name: str) -> bool:
        """Heuristic to determine if an application is likely a game"""
        name_lower = name.lower()
        
        # Game-related keywords
        game_indicators = [
            'game', 'play', 'world', 'quest', 'adventure', 'battle', 'war',
            'craft', 'sim', 'tycoon', 'racing', 'sports', 'puzzle', 'rpg'
        ]
        
        # Non-game keywords (to filter out)
        non_game_indicators = [
            'office', 'word', 'excel', 'browser', 'player', 'viewer',
            'editor', 'manager', 'settings', 'config', 'tool', 'utility'
        ]
        
        has_game_keyword = any(keyword in name_lower for keyword in game_indicators)
        has_non_game_keyword = any(keyword in name_lower for keyword in non_game_indicators)
        
        return has_game_keyword and not has_non_game_keyword

# Enhanced Interactive Game Manager with Scanner Integration
class EnhancedInteractiveGameManager:
    def __init__(self, game_manager, searcher):
        self.game_manager = game_manager
        self.searcher = searcher
        self.scanner = SmartGameScanner()
        self.catalog_manager = CatalogManager(game_manager)
    
    def smart_scan_menu(self):
        """Smart scanning menu system"""
        while True:
            print(f"\n{'═' * 50}")
            print("SMART GAME SCANNING")
            print(f"{'═' * 50}")
            print(f"{AperturePersonalities.SCANNER} Hello! I'm your gaming detection specialist!")
            print(f"{AperturePersonalities.SCANNER} I can find games you didn't even know you had!")
            
            print("\n1. Full system scan (my specialty!)")
            print("2. Steam library scan")
            print("3. Epic Games scan")
            print("4. Ubisoft Connect scan")
            print("5. GOG Galaxy scan")
            print("6. View last scan results")
            print("7. Back to main menu")
            
            choice = input("\nChoice (1-7): ").strip()
            
            if choice == '1':
                self.perform_full_scan()
            elif choice == '2':
                self.perform_platform_scan('steam')
            elif choice == '3':
                self.perform_platform_scan('epic')
            elif choice == '4':
                self.perform_platform_scan('ubisoft')
            elif choice == '5':
                self.perform_platform_scan('gog')
            elif choice == '6':
                self.view_scan_results()
            elif choice == '7':
                break
    
    def perform_full_scan(self):
        """Perform comprehensive scan of all platforms"""
        print(f"\n{AperturePersonalities.SCANNER} Right! Full comprehensive scan coming up!")
        print(f"{AperturePersonalities.SCANNER} I'm going to find every single game on your system!")
        print(f"{AperturePersonalities.SCANNER} This might take a moment, but it'll be worth it!")
        
        scan_results = self.scanner.scan_all_platforms()
        self.process_scan_results(scan_results)
    
    def perform_platform_scan(self, platform: str):
        """Perform scan for specific platform"""
        platform_names = {
            'steam': 'Steam', 'epic': 'Epic Games Store', 'ubisoft': 'Ubisoft Connect',
            'gog': 'GOG Galaxy'
        }
        
        print(f"\n{AperturePersonalities.SCANNER} Brilliant! Let me scan {platform_names.get(platform, platform.upper())} for you!")
        
        if platform == 'steam':
            print(f"{AperturePersonalities.SCANNER} Steam! My absolute favorite! So many games to find!")
            if platform.system() == "Windows":
                games = self.scanner.scan_steam_windows()
            elif platform.system() == "Darwin":
                games = self.scanner.scan_steam_mac()
            else:
                games = self.scanner.scan_steam_linux()
        elif platform == 'epic':
            print(f"{AperturePersonalities.SCANNER} Epic Games! Free games everywhere!")
            games = self.scanner.scan_epic_windows() if platform.system() == "Windows" else []
        elif platform == 'ubisoft':
            print(f"{AperturePersonalities.SCANNER} Ubisoft Connect! Looking for those AAA titles!")
            games = self.scanner.scan_ubisoft_windows() if platform.system() == "Windows" else []
        elif platform == 'gog':
            print(f"{AperturePersonalities.SCANNER} GOG Galaxy! DRM-free goodness!")
            games = self.scanner.scan_gog_windows() if platform.system() == "Windows" else []
        else:
            games = []
        
        if games:
            scan_results = {platform: games}
            self.process_scan_results(scan_results)
        else:
            print(f"{AperturePersonalities.SCANNER} Hmm, no games found for {platform_names.get(platform, platform.upper())}.")
            print(f"{AperturePersonalities.SCANNER} Maybe they're installed somewhere unusual?")
    
    def process_scan_results(self, scan_results: Dict[str, List[Dict]]):
        """Process and display scan results, allow user to add games"""
        total_found = sum(len(games) for games in scan_results.values())
        
        if total_found == 0:
            print(f"\n{AperturePersonalities.SCANNER} Oh. Well, that's embarrassing.")
            print(f"{AperturePersonalities.SCANNER} I couldn't find any games. They must be very well hidden!")
            return
        
        print(f"\n{AperturePersonalities.SCANNER} Fantastic! I found {total_found} games for you!")
        print(f"{AperturePersonalities.SCANNER} Look at all these brilliant games I discovered:")
        
        # Display results by platform
        all_detected_games = []
        game_counter = 1
        
        for platform, games in scan_results.items():
            if not games:
                continue
                
            print(f"\n{platform.upper()} ({len(games)} games):")
            for game in games:
                existing_games = self.game_manager.get_games()
                already_added = any(
                    existing['name'].lower() == game['name'].lower() and 
                    existing['platform'] == game['platform']
                    for existing in existing_games.values()
                )
                
                status = " [ALREADY IN COLLECTION]" if already_added else ""
                print(f"  {game_counter}. {game['name']}{status}")
                all_detected_games.append((game, already_added))
                game_counter += 1
        
        # Add games interactively
        print(f"\n{AperturePersonalities.SCANNER} Now, which games would you like me to add to your library?")
        print(f"{AperturePersonalities.SCANNER} You can pick individual numbers, ranges, or just say 'all'!")
        print("Examples: '1,3,5' or '1-5' or 'all'")
        
        selection = input("Games to add: ").strip().lower()
        
        if not selection:
            print(f"{AperturePersonalities.SCANNER} No selection made. Maybe next time!")
            return
        
        games_to_add = []
        
        if selection == 'all':
            games_to_add = [game for game, already_added in all_detected_games if not already_added]
            print(f"{AperturePersonalities.SCANNER} All games! I like your enthusiasm!")
        else:
            # Parse selection
            try:
                indices = self.parse_selection(selection, len(all_detected_games))
                games_to_add = [
                    all_detected_games[i-1][0] 
                    for i in indices 
                    if not all_detected_games[i-1][1]  # Not already added
                ]
                print(f"{AperturePersonalities.SCANNER} Got it! Adding your selected games!")
            except ValueError:
                print(f"{AperturePersonalities.SCANNER} Oh dear, I didn't understand that selection format.")
                return
        
        if not games_to_add:
            print(f"{AperturePersonalities.SCANNER} No new games to add. Everything's already in your collection!")
            return
        
        # Add selected games
        added_count = 0
        for game in games_to_add:
            try:
                game_number = self.game_manager.add_game(
                    game['name'],
                    game['platform'],
                    game['game_id'],
                    game.get('store_url', ''),
                    {'detected': True, 'source': game.get('source', 'scan')}
                )
                print(f"{AperturePersonalities.SCANNER} Added: {game['name']} (#{game_number}) - Brilliant!")
                added_count += 1
            except Exception as e:
                print(f"{AperturePersonalities.SCANNER} Oh no! Failed to add {game['name']}: {e}")
        
        if added_count > 0:
            print(f"\n{AperturePersonalities.SCANNER} Success! I added {added_count} games to your collection!")
            print(f"{AperturePersonalities.SCANNER} I'm quite pleased with myself, actually!")
            self.catalog_manager.generate_catalog()
        else:
            print(f"{AperturePersonalities.SCANNER} Well, that didn't go as planned. No games were added.")
    
    def parse_selection(self, selection: str, max_count: int) -> List[int]:
        """Parse user selection string into list of indices"""
        indices = set()
        
        parts = selection.replace(' ', '').split(',')
        
        for part in parts:
            if '-' in part:
                # Range selection (e.g., "1-5")
                start, end = part.split('-', 1)
                start_idx = int(start)
                end_idx = int(end)
                
                if 1 <= start_idx <= max_count and 1 <= end_idx <= max_count:
                    indices.update(range(start_idx, end_idx + 1))
                else:
                    raise ValueError("Index out of range")
            else:
                # Single number
                idx = int(part)
                if 1 <= idx <= max_count:
                    indices.add(idx)
                else:
                    raise ValueError("Index out of range")
        
        return sorted(list(indices))
    
    def view_scan_results(self):
        """View results from last scan"""
        print(f"{AperturePersonalities.SCANNER} Oh, you want to see the last scan results!")
        print(f"{AperturePersonalities.SCANNER} Well, I would show you, but I haven't implemented memory yet.")
        print(f"{AperturePersonalities.SCANNER} Just run another scan - I don't mind doing it again!")

# Update the original classes to maintain compatibility
class GameDataManager:
    def __init__(self):
        self.game_data = self.load_game_data()
        self.migrate_old_data()
    
    def load_game_data(self) -> Dict:
        try:
            if GAME_DATA_FILE.exists():
                with open(GAME_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {
            'version': '2.2',
            'games': {},
            'next_id': 1,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'stats': {'total_games': 0, 'games_by_platform': {}, 'play_count': {}},
            'scan_history': []
        }
    
    def migrate_old_data(self):
        try:
            old_launcher = SCRIPT_DIR / "glados_game_launcher.py"
            if old_launcher.exists() and old_launcher != Path(__file__):
                print(f"{AperturePersonalities.SYSTEM} Migrating old data...")
                
                with open(old_launcher, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                pattern = r'"(\d+)": "((?:steam://rungameid/|uplay://launch/)[^"]+)"(?:,?\s*#\s*([^\n]+))?'
                matches = re.findall(pattern, content)
                
                migrated_count = 0
                for game_id, url, comment in matches:
                    if game_id not in self.game_data['games']:
                        if url.startswith('steam://rungameid/'):
                            platform = 'steam'
                            extracted_id = url.split('/')[-1]
                            store_url = f"https://store.steampowered.com/app/{extracted_id}/"
                        elif url.startswith('uplay://launch/'):
                            platform = 'ubisoft'
                            extracted_id = url.split('/')[-1]
                            store_url = f"https://store.ubi.com/us/search/?q={quote_plus(comment or 'game')}"
                        else:
                            platform = 'other'
                            extracted_id = url
                            store_url = ""
                        
                        game_name = comment.strip() if comment else f"Migrated Game {game_id}"
                        
                        self.game_data['games'][game_id] = {
                            'name': game_name,
                            'platform': platform,
                            'game_id': extracted_id,
                            'store_url': store_url,
                            'protocol_url': url,
                            'added_date': 'Migrated',
                            'migrated': True,
                            'play_count': 0
                        }
                        
                        if int(game_id) >= self.game_data['next_id']:
                            self.game_data['next_id'] = int(game_id) + 1
                        
                        migrated_count += 1
                
                if migrated_count > 0:
                    print(f"{AperturePersonalities.SYSTEM} Migrated {migrated_count} games")
                    self.save_game_data()
        
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Migration error: {e}")
    
    def save_game_data(self):
        try:
            self.game_data['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self.update_stats()
            
            with open(GAME_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.game_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Save failed: {e}")
    
    def update_stats(self):
        games = self.game_data.get('games', {})
        self.game_data['stats']['total_games'] = len(games)
        
        platform_counts = {}
        for game in games.values():
            platform = game.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        self.game_data['stats']['games_by_platform'] = platform_counts
    
    def add_game(self, name: str, platform: str, game_id: str, store_url: str = "", search_data: Dict = None) -> int:
        game_number = self.game_data['next_id']
        
        self.game_data['games'][str(game_number)] = {
            'name': name,
            'platform': platform.lower(),
            'game_id': game_id,
            'store_url': store_url,
            'protocol_url': self.generate_protocol_url(platform, game_id),
            'added_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'play_count': 0,
            'search_data': search_data or {}
        }
        
        self.game_data['next_id'] += 1
        self.save_game_data()
        return game_number
    
    def generate_protocol_url(self, platform: str, game_id: str) -> str:
        platform = platform.lower()
        if platform == 'steam':
            return f"steam://rungameid/{game_id}"
        elif platform == 'ubisoft':
            return f"uplay://launch/{game_id}"
        elif platform == 'epic':
            return f"com.epicgames.launcher://apps/{game_id}?action=launch&silent=true"
        elif platform == 'gog':
            return f"goggalaxy://openGameView/{game_id}"
        else:
            return game_id
    
    def remove_game(self, game_id: str) -> bool:
        try:
            if game_id in self.game_data['games']:
                game_name = self.game_data['games'][game_id]['name']
                del self.game_data['games'][game_id]
                self.save_game_data()
                print(f"{AperturePersonalities.SYSTEM} Removed '{game_name}'")
                return True
            return False
        except Exception:
            return False
    
    def update_play_count(self, game_id: str):
        try:
            if game_id in self.game_data['games']:
                self.game_data['games'][game_id]['play_count'] += 1
                self.game_data['games'][game_id]['last_played'] = time.strftime('%Y-%m-%d %H:%M:%S')
                self.save_game_data()
        except Exception:
            pass
    
    def get_games(self) -> Dict:
        return self.game_data.get('games', {})
    
    def get_game_count(self) -> int:
        return len(self.game_data.get('games', {}))
    
    def get_max_game_number(self) -> int:
        games = self.get_games()
        return max(int(game_id) for game_id in games.keys()) if games else 0

# Include all the remaining classes from the original code...

# Auto-Updater
class GLaDOSAutoUpdater:
    def __init__(self):
        self.current_version = self.get_current_version()
        self.backup_created = False
        self.backup_path = None
        
    def get_current_version(self) -> str:
        try:
            if VERSION_FILE.exists():
                with open(VERSION_FILE, 'r') as f:
                    return json.load(f).get('version', CURRENT_VERSION)
        except Exception:
            pass
        return CURRENT_VERSION
    
    def save_version(self, version: str):
        try:
            version_data = {
                'version': version,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
                'last_check': time.time()
            }
            with open(VERSION_FILE, 'w') as f:
                json.dump(version_data, f, indent=2)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Failed to save version: {e}")
    
    def should_skip_check(self) -> bool:
        try:
            if VERSION_FILE.exists():
                with open(VERSION_FILE, 'r') as f:
                    last_check = json.load(f).get('last_check', 0)
                    return (time.time() - last_check) < 3600  # 1 hour
        except Exception:
            pass
        return False
    
    def check_for_updates(self, force_check: bool = False, silent: bool = False) -> Optional[Dict]:
        if not force_check and self.should_skip_check():
            return None
            
        if not silent:
            print(f"{AperturePersonalities.GLaDOS} Checking for updates...")
        
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                
                if self.is_newer_version(latest_version, self.current_version):
                    if not silent:
                        print(f"{AperturePersonalities.GLaDOS} Version {latest_version} available.")
                    return release_data
                else:
                    if force_check and not silent:
                        print(f"{AperturePersonalities.GLaDOS} You're running the latest version.")
                    return None
                    
            elif response.status_code == 404:
                if not silent:
                    print(f"{AperturePersonalities.GLaDOS} No releases found.")
                return None
                
            elif response.status_code == 403:
                if not silent:
                    print(f"{AperturePersonalities.GLaDOS} Rate limit exceeded.")
                return None
                
        except Exception as e:
            if not silent:
                print(f"{AperturePersonalities.ERROR} Update check failed: {e}")
            return None
    
    def is_newer_version(self, latest: str, current: str) -> bool:
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            max_length = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_length - len(latest_parts))
            current_parts += [0] * (max_length - len(current_parts))
            
            return latest_parts > current_parts
        except ValueError:
            return latest != current
    
    def perform_update(self, auto_mode: bool = False) -> bool:
        print(f"{AperturePersonalities.GLaDOS} Checking for updates...")
        
        release_data = self.check_for_updates(force_check=True)
        if not release_data:
            print(f"{AperturePersonalities.GLaDOS} No updates available.")
            return False
        
        if not auto_mode:
            print(f"\n{AperturePersonalities.SYSTEM} Update: {release_data['tag_name']}")
            response = input(f"{AperturePersonalities.GLaDOS} Proceed? (y/N): ").strip().lower()
            if response != 'y':
                return False
        
        return True

# Multi-Platform Game Searcher (keeping original functionality)
class MultiPlatformGameSearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_steam(self, game_name: str) -> Optional[Dict]:
        try:
            common_games = {
                'portal': {'id': '400', 'name': 'Portal'},
                'portal 2': {'id': '620', 'name': 'Portal 2'},
                'half-life': {'id': '70', 'name': 'Half-Life'},
                'half-life 2': {'id': '220', 'name': 'Half-Life 2'},
                'team fortress 2': {'id': '440', 'name': 'Team Fortress 2'},
                'counter-strike 2': {'id': '730', 'name': 'Counter-Strike 2'},
                'dota 2': {'id': '570', 'name': 'Dota 2'},
                'left 4 dead 2': {'id': '550', 'name': 'Left 4 Dead 2'},
                'garrys mod': {'id': '4000', 'name': "Garry's Mod"},
                'civilization vi': {'id': '289070', 'name': 'Civilization VI'},
                'the witcher 3': {'id': '292030', 'name': 'The Witcher 3'},
                'gta 5': {'id': '271590', 'name': 'Grand Theft Auto V'},
                'cyberpunk 2077': {'id': '1091500', 'name': 'Cyberpunk 2077'},
                'skyrim': {'id': '489830', 'name': 'Skyrim Special Edition'},
                'fallout 4': {'id': '377160', 'name': 'Fallout 4'},
                'among us': {'id': '945360', 'name': 'Among Us'},
                'rocket league': {'id': '252950', 'name': 'Rocket League'},
                'terraria': {'id': '105600', 'name': 'Terraria'},
                'stardew valley': {'id': '413150', 'name': 'Stardew Valley'}
            }
            
            game_lower = game_name.lower().strip()
            
            if game_lower in common_games:
                game_info = common_games[game_lower]
                return {
                    'platform': 'steam',
                    'game_id': game_info['id'],
                    'store_url': f"https://store.steampowered.com/app/{game_info['id']}/",
                    'name': game_info['name'],
                    'verified': False
                }
            
            return None
        except Exception:
            return None
    
    def search_all_platforms(self, game_name: str) -> Dict[str, Dict]:
        results = {}
        
        print(f"{AperturePersonalities.WHEATLEY} Searching for '{game_name}'...")
        
        result = self.search_steam(game_name)
        if result:
            results['steam'] = result
        
        if results:
            platforms_found = list(results.keys())
            print(f"{AperturePersonalities.WHEATLEY} Found on: {', '.join(platforms_found)}")
        else:
            print(f"{AperturePersonalities.WHEATLEY} Not found automatically.")
        
        return results

# Game Launcher
class GameLauncher:
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
    
    def launch_game(self, game_url: str, platform_name: str = "unknown") -> bool:
        try:
            print(f"{AperturePersonalities.GLaDOS} Launching via {platform_name.title()}...")
            
            if platform.system() == "Windows":
                subprocess.run(f'start "" "{game_url}"', shell=True)
            elif platform.system() == "Darwin":
                subprocess.run(['open', game_url])
            else:
                subprocess.run(['xdg-open', game_url])
            
            return True
        except Exception:
            try:
                webbrowser.open(game_url)
                return True
            except Exception:
                return False
    
    def launch_game_with_commentary(self, game_choice: str):
        games = self.game_manager.get_games()
        
        if game_choice not in games:
            print(f"{AperturePersonalities.GLaDOS} Invalid selection. Learn to count.")
            return
        
        game = games[game_choice]
        game_url = game['protocol_url']
        platform_name = game['platform']
        
        print(f"{AperturePersonalities.GLaDOS} *Initializing launch for '{game['name']}'...*")
        time.sleep(1)
        
        if self.launch_game(game_url, platform_name):
            self.game_manager.update_play_count(game_choice)
            
            success_messages = [
                f"'{game['name']}' launched. Try not to disappoint me.",
                f"Game running. Your inevitable failure begins now.",
                f"Launch successful. Preparing disappointment systems.",
                f"'{game['name']}' started. I'll monitor your pathetic performance."
            ]
            print(f"{AperturePersonalities.GLaDOS} {random.choice(success_messages)}")
        else:
            failure_messages = [
                "Launch failed. Your technical incompetence strikes again.",
                "Unable to launch. System as broken as your skills.",
                "Launch error. Try being more competent.",
                "System failure. Much like everything you touch."
            ]
            print(f"{AperturePersonalities.GLaDOS} {random.choice(failure_messages)}")

# Catalog Manager
class CatalogManager:
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
    
    def generate_catalog(self):
        games = self.game_manager.get_games()
        game_count = len(games)
        
        if game_count == 0:
            self.create_empty_catalog()
        else:
            self.create_populated_catalog(games, game_count)
    
    def create_empty_catalog(self):
        catalog_content = """████████████████████████████████████████████████████████████████████████████████
                     APERTURE SCIENCE GAME CATALOG
                          VERSION: 2.2 "scanning vault"
████████████████████████████████████████████████████████████████████████████████

╔════════════════════════════════════════════════════════════════════════════════╗
║                 GLaDOS ENTERTAINMENT DISTRIBUTION CATALOG                     ║
║                                                                                ║
║  GAMES ADDED: 0                                                               ║
║  STATUS: AWAITING USER INPUT                                                  ║
║  EXPECTED DISAPPOINTMENT LEVEL: MAXIMUM                                       ║
║                                                                                ║
║  "The catalog is empty. Try the smart scanner, or add games manually."       ║
╚════════════════════════════════════════════════════════════════════════════════╝

Your catalog is currently empty. Use the game management system or smart scanner to add games.

═══════════════════════════════════════════════════════════════════════════════════
                                  END CATALOG
═══════════════════════════════════════════════════════════════════════════════════
"""
        try:
            with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
                f.write(catalog_content)
        except Exception:
            pass
    
    def create_populated_catalog(self, games: Dict, game_count: int):
        max_game_num = self.game_manager.get_max_game_number()
        detected_count = sum(1 for game in games.values() if game.get('search_data', {}).get('detected', False))
        
        catalog_content = f"""████████████████████████████████████████████████████████████████████████████████
                     APERTURE SCIENCE GAME CATALOG
                          VERSION: 2.2 "scanning vault"
████████████████████████████████████████████████████████████████████████████████

╔════════════════════════════════════════════════════════════════════════════════╗
║                 GLaDOS ENTERTAINMENT DISTRIBUTION CATALOG                     ║
║                                                                                ║
║  GAMES TOTAL: {game_count}                                                             ║
║  AUTO-DETECTED: {detected_count}                                                        ║
║  MANUAL ENTRIES: {game_count - detected_count}                                                      ║
║  STATUS: COLLECTION ACTIVE                                                    ║
╚════════════════════════════════════════════════════════════════════════════════╝

Your catalog of interactive disappointment:

"""
        
        # Group games by platform
        platforms = {}
        for game_id, game in games.items():
            platform = game.get('platform', 'other')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append((game_id, game))
        
        # Display games by platform
        for platform in ['steam', 'epic', 'ubisoft', 'gog', 'other']:
            if platform not in platforms:
                continue
                
            platform_games = sorted(platforms[platform], key=lambda x: int(x[0]))
            
            catalog_content += f"\n{platform.upper()} GAMES:\n"
            
            for game_id, game in platform_games:
                detected_marker = " [AUTO-DETECTED]" if game.get('search_data', {}).get('detected', False) else ""
                play_count = f" (Played {game['play_count']}x)" if game.get('play_count', 0) > 0 else ""
                
                catalog_content += f"{game_id}. {game['name']}{detected_marker}{play_count}\n"
        
        catalog_content += f"""
═══════════════════════════════════════════════════════════════════════════════════
Game Selection Range: 1 to {max_game_num}
Total Games: {game_count} | Auto-Detected: {detected_count}
Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}

"Your disappointments, now with automatic detection." - GLaDOS
═══════════════════════════════════════════════════════════════════════════════════
"""
        
        try:
            with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
                f.write(catalog_content)
        except Exception:
            pass
    
    def view_catalog(self):
        try:
            if CATALOG_PATH.exists():
                with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                    print(f.read())
            else:
                print(f"{AperturePersonalities.GLaDOS} No catalog found.")
        except Exception:
            print(f"{AperturePersonalities.ERROR} Error reading catalog.")

# Original Interactive Game Manager (for backward compatibility)
class InteractiveGameManager:
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
        self.searcher = MultiPlatformGameSearcher()
        self.catalog_manager = CatalogManager(game_manager)
    
    def add_game_interactive(self):
        print(f"{AperturePersonalities.WHEATLEY} Let's add a new game!")
        
        game_name = input(f"{AperturePersonalities.WHEATLEY} Game name: ").strip()
        if not game_name:
            return False
        
        search_choice = input(f"{AperturePersonalities.WHEATLEY} Search automatically? (y/N): ").strip().lower()
        
        if search_choice == 'y':
            return self.add_game_with_search(game_name)
        else:
            return self.add_game_manually(game_name)
    
    def add_game_with_search(self, game_name: str) -> bool:
        search_results = self.searcher.search_all_platforms(game_name)
        
        if not search_results:
            manual_choice = input(f"{AperturePersonalities.WHEATLEY} Add manually? (y/N): ").strip().lower()
            return self.add_game_manually(game_name) if manual_choice == 'y' else False
        
        print(f"\nFound '{game_name}' on:")
        choices = {}
        choice_num = 1
        
        for platform, data in search_results.items():
            print(f"{choice_num}. {platform.upper()} - {data['name']}")
            choices[str(choice_num)] = (platform, data)
            choice_num += 1
        
        choices[str(choice_num)] = ('manual', None)
        print(f"{choice_num}. Add manually")
        
        choice = input(f"{AperturePersonalities.WHEATLEY} Which? (1-{choice_num}): ").strip()
        
        if choice in choices:
            platform, data = choices[choice]
            
            if platform == 'manual':
                return self.add_game_manually(game_name)
            else:
                game_number = self.game_manager.add_game(
                    data['name'], 
                    platform, 
                    data['game_id'], 
                    data.get('store_url', ''),
                    data
                )
                
                print(f"{AperturePersonalities.WHEATLEY} Added '{data['name']}' as game #{game_number}!")
                self.catalog_manager.generate_catalog()
                return True
        return False
    
    def add_game_manually(self, game_name: str) -> bool:
        platforms = {
            '1': ('steam', 'Steam'),
            '2': ('ubisoft', 'Ubisoft Connect'),
            '3': ('epic', 'Epic Games Store'),
            '4': ('gog', 'GOG Galaxy'),
            '5': ('other', 'Other/Custom')
        }
        
        print("Platforms:")
        for key, (_, name) in platforms.items():
            print(f"{key}. {name}")
        
        choice = input(f"{AperturePersonalities.WHEATLEY} Platform (1-5): ").strip()
        
        if choice not in platforms:
            return False
        
        platform_id, platform_name = platforms[choice]
        
        if platform_id == 'steam':
            game_id = input("Steam App ID: ").strip()
            if not game_id.isdigit():
                print("Invalid App ID")
                return False
            store_url = f"https://store.steampowered.com/app/{game_id}/"
        elif platform_id == 'ubisoft':
            game_id = input("Ubisoft Game ID: ").strip()
            if not game_id.isdigit():
                print("Invalid Game ID")
                return False
            store_url = f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}"
        elif platform_id == 'epic':
            game_id = input("Epic catalog ID: ").strip()
            store_url = f"https://store.epicgames.com/en-US/p/{game_id}"
        elif platform_id == 'gog':
            game_id = input("GOG game slug: ").strip()
            store_url = f"https://www.gog.com/game/{game_id}"
        else:
            game_id = input("Launch URL/Command: ").strip()
            store_url = input("Store URL (optional): ").strip()
        
        if not game_id:
            return False
        
        game_number = self.game_manager.add_game(game_name, platform_id, game_id, store_url)
        print(f"{AperturePersonalities.WHEATLEY} Added '{game_name}' as #{game_number}!")
        self.catalog_manager.generate_catalog()
        return True
    
    def remove_game_interactive(self):
        games = self.game_manager.get_games()
        if not games:
            print(f"{AperturePersonalities.GLaDOS} No games to remove.")
            return
        
        print("Games:")
        for game_id, game in sorted(games.items(), key=lambda x: int(x[0])):
            print(f"{game_id}. {game['name']}")
        
        choice = input("Remove game #: ").strip()
        
        if choice in games:
            game_name = games[choice]['name']
            confirm = input(f"Remove '{game_name}'? (y/N): ").strip().lower()
            
            if confirm == 'y':
                if self.game_manager.remove_game(choice):
                    self.catalog_manager.generate_catalog()
    
    def view_all_games(self):
        games = self.game_manager.get_games()
        if not games:
            print(f"{AperturePersonalities.GLaDOS} No games found.")
            return
        
        print(f"\nGame Collection ({len(games)} games):")
        
        for game_id, game in sorted(games.items(), key=lambda x: int(x[0])):
            detected_marker = " [AUTO-DETECTED]" if game.get('search_data', {}).get('detected', False) else ""
            print(f"\n{game_id}. {game['name']}{detected_marker}")
            print(f"   Platform: {game['platform'].upper()}")
            if game.get('play_count', 0) > 0:
                print(f"   Played: {game['play_count']} times")
            print(f"   Added: {game.get('added_date', 'Unknown')}")
    
    def management_menu(self):
        while True:
            games = self.game_manager.get_games()
            game_count = len(games)
            
            print(f"\n{'═' * 50}")
            print("GAME MANAGEMENT")
            print(f"{'═' * 50}")
            
            if game_count == 0:
                print(f"{AperturePersonalities.GLaDOS} Empty collection.")
            else:
                detected_count = sum(1 for game in games.values() if game.get('search_data', {}).get('detected', False))
                print(f"{AperturePersonalities.GLaDOS} Managing {game_count} games ({detected_count} auto-detected).")
            
            print("\n1. Add game (with search)")
            print("2. Add game manually")
            print("3. Remove game")
            print("4. View all games")
            print("5. Smart game scanner")
            print("6. Update catalog")
            print("7. Back to main menu")
            
            choice = input("Choice (1-7): ").strip()
            
            if choice == '1':
                self.add_game_interactive()
            elif choice == '2':
                name = input("Game name: ").strip()
                if name:
                    self.add_game_manually(name)
            elif choice == '3':
                self.remove_game_interactive()
            elif choice == '4':
                self.view_all_games()
            elif choice == '5':
                enhanced_manager = EnhancedInteractiveGameManager(self.game_manager, self.searcher)
                enhanced_manager.smart_scan_menu()
            elif choice == '6':
                self.catalog_manager.generate_catalog()
                print("Catalog updated.")
            elif choice == '7':
                break

# First Run System and Utility Functions (unchanged)
def is_first_run() -> bool:
    return not FIRST_RUN_FLAG.exists()

def mark_first_run_complete():
    try:
        FIRST_RUN_FLAG.write_text("First run completed - GLaDOS v2.2")
        return True
    except Exception:
        return False

def handle_first_run(game_manager: GameDataManager, interactive_manager: InteractiveGameManager):
    print(f"\n{'═' * 50}")
    print(f"{AperturePersonalities.GLaDOS} First time setup detected.")
    print(f"{AperturePersonalities.GLaDOS} Your collection is empty. How predictable.")
    
    print(f"\n{AperturePersonalities.SCANNER} Hello there! I'm Wheatley, your gaming assistant!")
    print(f"{AperturePersonalities.SCANNER} I can automatically scan your entire system for games!")
    scan_choice = input(f"{AperturePersonalities.SCANNER} Shall I find all your games? It'll be brilliant! (Y/n): ").strip().lower()
    
    if scan_choice != 'n':
        enhanced_manager = EnhancedInteractiveGameManager(game_manager, MultiPlatformGameSearcher())
        enhanced_manager.perform_full_scan()
    
    # Check if games were added by scanner
    if game_manager.get_game_count() == 0:
        print(f"\n{AperturePersonalities.SCANNER} Hmm, couldn't find any games automatically.")
        setup_choice = input(f"{AperturePersonalities.WHEATLEY} Would you like to add some games manually instead? (y/N): ").strip().lower()
        
        if setup_choice == 'y':
            games_added = 0
            while True:
                print(f"\nGames added: {games_added}")
                
                if interactive_manager.add_game_interactive():
                    games_added += 1
                    
                    if games_added >= 2:
                        continue_choice = input("\nAdd another? (y/N): ").strip().lower()
                        if continue_choice != 'y':
                            break
                else:
                    retry = input("\nTry again? (Y/n): ").strip().lower()
                    if retry == 'n':
                        break
    else:
        print(f"\n{AperturePersonalities.SCANNER} Setup complete! Your games are ready to play!")
    
    mark_first_run_complete()

def show_system_info(game_manager: GameDataManager, updater: GLaDOSAutoUpdater):
    print(f"\n{'═' * 50}")
    print("SYSTEM INFORMATION")
    print(f"{'═' * 50}")
    
    print(f"Version: {updater.current_version}")
    
    games = game_manager.get_games()
    game_count = len(games)
    print(f"Total Games: {game_count}")
    
    if game_count > 0:
        detected_count = sum(1 for game in games.values() if game.get('search_data', {}).get('detected', False))
        print(f"Auto-detected: {detected_count}")
        print(f"Manual entries: {game_count - detected_count}")
        print(f"Game Range: 1-{game_manager.get_max_game_number()}")
        
        total_plays = sum(game.get('play_count', 0) for game in games.values())
        if total_plays > 0:
            print(f"Total Launches: {total_plays}")
    
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Repository: https://github.com/{REPO_OWNER}/{REPO_NAME}")

# Main Application
def main():
    print(f"\n{'═' * 50}")
    print(f"GLaDOS Game Launcher v{CURRENT_VERSION}")
    print("Initializing systems with smart scanning...")
    print(f"{'═' * 50}")
    
    # Initialize systems
    updater = GLaDOSAutoUpdater()
    game_manager = GameDataManager()
    interactive_manager = InteractiveGameManager(game_manager)
    catalog_manager = CatalogManager(game_manager)
    launcher = GameLauncher(game_manager)
    
    # Update check
    if is_first_run():
        print(f"{AperturePersonalities.GLaDOS} Checking for updates...")
        updater.check_for_updates(force_check=True, silent=False)
    else:
        updater.check_for_updates(silent=True)
    
    catalog_manager.generate_catalog()
    
    # Handle first run with smart scanning
    if is_first_run():
        handle_first_run(game_manager, interactive_manager)
    
    # Main loop
    while True:
        try:
            print(f"\n{'═' * 50}")
            print("MAIN MENU")
            print(f"{'═' * 50}")
            
            games = game_manager.get_games()
            game_count = len(games)
            max_game_num = game_manager.get_max_game_number()
            
            if game_count == 0:
                print(f"{AperturePersonalities.GLaDOS} No games found.")
                print(f"{AperturePersonalities.SCANNER} But don't worry! I can find your games for you!")
                print(f"{AperturePersonalities.SCANNER} Just check the Game Management menu!")
                print("\n1. Game Management")
                print("2. Check Updates")
                print("3. System Info")
                print("4. Quit")
                
                choice = input("Choice (1-4): ").strip()
                
                if choice == '1':
                    interactive_manager.management_menu()
                elif choice == '2':
                    updater.perform_update()
                elif choice == '3':
                    show_system_info(game_manager, updater)
                elif choice == '4':
                    break
            else:
                detected_count = sum(1 for game in games.values() if game.get('search_data', {}).get('detected', False))
                status_msg = f"{game_count} games available"
                if detected_count > 0:
                    status_msg += f" ({detected_count} auto-detected)"
                
                print(f"{AperturePersonalities.GLaDOS} {status_msg}.")
                print(f"\n1. Play game (1-{max_game_num})")
                print("2. Game Management")
                print("3. View Catalog")
                print("4. Check Updates")
                print("5. System Info")
                print("6. Quit")
                
                choice = input("Choice (1-6): ").strip()
                
                if choice == '1':
                    print(f"\nAvailable games:")
                    for game_id, game in sorted(games.items(), key=lambda x: int(x[0])):
                        play_info = f" ({game['play_count']}x)" if game.get('play_count', 0) > 0 else ""
                        detected_marker = " [AUTO]" if game.get('search_data', {}).get('detected', False) else ""
                        print(f"  {game_id}. {game['name']} [{game['platform'].upper()}]{detected_marker}{play_info}")
                    
                    game_choice = input(f"\nGame number: ").strip()
                    
                    if game_choice in games:
                        launcher.launch_game_with_commentary(game_choice)
                    else:
                        print(f"{AperturePersonalities.GLaDOS} Invalid selection.")
                
                elif choice == '2':
                    interactive_manager.management_menu()
                elif choice == '3':
                    catalog_manager.view_catalog()
                elif choice == '4':
                    updater.perform_update()
                elif choice == '5':
                    show_system_info(game_manager, updater)
                elif choice == '6':
                    break
        
        except KeyboardInterrupt:
            print(f"\n{AperturePersonalities.GLaDOS} Interrupted.")
            break
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error: {e}")
    
    print(f"\n{'═' * 50}")
    print(f"{AperturePersonalities.GLaDOS} Goodbye. Your games will miss your incompetence.")
    print(f"{'═' * 50}")

# Entry Point
if __name__ == "__main__":
    try:
        # Fix winreg import for non-Windows systems
        if platform.system() != "Windows":
            # Create dummy winreg module for cross-platform compatibility
            import types
            winreg = types.ModuleType('winreg')
            winreg.HKEY_LOCAL_MACHINE = None
            winreg.OpenKey = lambda *args: None
            winreg.QueryValueEx = lambda *args: (None, None)
            winreg.EnumKey = lambda *args: None
            sys.modules['winreg'] = winreg
        else:
            import winreg
        
        os.chdir(SCRIPT_DIR)
        BACKUP_DIR.mkdir(exist_ok=True)
        main()
        
    except KeyboardInterrupt:
        print(f"\n{AperturePersonalities.GLaDOS} Terminated by user.")
        
    except Exception as e:
        print(f"\n{AperturePersonalities.ERROR} Fatal error: {e}")
        
        try:
            emergency_log = SCRIPT_DIR / f"crash_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(emergency_log, 'w') as f:
                f.write(f"Crash Report\nTime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Version: {CURRENT_VERSION}\nError: {e}\n")
                f.write(f"Platform: {platform.system()}\nPython: {sys.version}\n")
            print(f"Crash log saved: {emergency_log}")
        except Exception:
            pass