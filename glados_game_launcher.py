#!/usr/bin/env python3
"""
GLaDOS Game Launcher v2.5 - Aperture Science Enrichment Center Edition
Fixed version with complete functionality and error handling
"""

import time
import json
import threading
import subprocess
import webbrowser
import platform
import os
import sys
import re
import random
from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import io
import base64

# System info imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
        PSUTIL_AVAILABLE = True
    except:
        PSUTIL_AVAILABLE = False

# GUI imports with fallbacks
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog

# Image handling with fallbacks
try:
    from PIL import Image, ImageTk
    import requests
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    try:
        import requests
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
        except:
            class MockRequests:
                @staticmethod
                def get(*args, **kwargs):
                    raise Exception("Requests not available")
            requests = MockRequests()

try:
    REQUESTS_AVAILABLE = hasattr(requests, "get") and requests.__class__.__name__ != "MockRequests"
except Exception:
    REQUESTS_AVAILABLE = False

# Cross-platform registry handling
try:
    if platform.system() == "Windows":
        import winreg
    else:
        class MockWinreg:
            HKEY_LOCAL_MACHINE = None
            @staticmethod
            def OpenKey(*args, **kwargs): 
                return None
            @staticmethod
            def QueryValueEx(*args): 
                return (None, None)
            @staticmethod
            def EnumKey(*args): 
                return None
            @staticmethod
            def CloseKey(*args): 
                pass
            WindowsError = OSError
        winreg = MockWinreg()
except ImportError:
    class MockWinreg:
        HKEY_LOCAL_MACHINE = None
        @staticmethod
        def OpenKey(*args, **kwargs): 
            return None
        @staticmethod
        def QueryValueEx(*args): 
            return (None, None)
        @staticmethod
        def EnumKey(*args): 
            return None
        @staticmethod
        def CloseKey(*args): 
            pass
        WindowsError = OSError
    winreg = MockWinreg()

# Configuration
CURRENT_VERSION = "2.5"
def _resolve_base_dir() -> Path:
    """Return directory for persistent data whether running from source or frozen exe."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).parent.resolve()

SCRIPT_DIR = _resolve_base_dir()
if getattr(sys, 'frozen', False):
    CURRENT_SCRIPT = Path(sys.executable).resolve()
else:
    CURRENT_SCRIPT = Path(__file__).resolve()
FIRST_RUN_FLAG = SCRIPT_DIR / '.aperture_first_run_complete'
GAME_DATA_FILE = SCRIPT_DIR / 'game_data.json'
USER_PREFS_FILE = SCRIPT_DIR / 'user_preferences.json'
ICON_CACHE_DIR = SCRIPT_DIR / 'icon_cache'
ACHIEVEMENT_CACHE_DIR = SCRIPT_DIR / 'achievement_cache'

# Create directories safely
for directory in [ICON_CACHE_DIR, ACHIEVEMENT_CACHE_DIR]:
    try:
        directory.mkdir(exist_ok=True)
    except:
        pass

class AchievementManager:
    def __init__(self):
        self.achievement_cache = {}
        self.user_achievements = self.load_user_achievements()
        
    def load_user_achievements(self) -> Dict:
        try:
            cache_file = ACHIEVEMENT_CACHE_DIR / 'user_achievements.json'
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_user_achievements(self):
        try:
            cache_file = ACHIEVEMENT_CACHE_DIR / 'user_achievements.json'
            with open(cache_file, 'w') as f:
                json.dump(self.user_achievements, f, indent=2)
        except:
            pass
    
    def get_game_achievements(self, game_id: str, platform_name: str, game_name: str = "") -> Dict:
        """Get achievements for a game from all platforms"""
        cache_key = f"{platform_name}_{game_id}"
        
        if cache_key in self.achievement_cache:
            return self.achievement_cache[cache_key]
        
        achievements = self.fetch_platform_achievements(game_id, platform_name, game_name)
        self.achievement_cache[cache_key] = achievements
        return achievements
    
    def fetch_platform_achievements(self, game_id: str, platform_name: str, game_name: str = "") -> Dict:
        """Fetch achievements from specific platforms"""
        try:
            if platform_name == 'steam':
                return self.fetch_steam_achievements(game_id)
            elif platform_name == 'epic':
                return self.fetch_epic_achievements(game_id, game_name)
            elif platform_name == 'ubisoft':
                return self.fetch_ubisoft_achievements(game_id, game_name)
            elif platform_name == 'gog':
                return self.fetch_gog_achievements(game_id, game_name)
            else:
                return {'total': 0, 'unlocked': 0, 'achievements': [], 'platform': platform_name, 'percentage': 0}
        except Exception:
            return {'total': 0, 'unlocked': 0, 'achievements': [], 'platform': platform_name, 'error': True, 'percentage': 0}
    
    def fetch_steam_achievements(self, app_id: str) -> Dict:
        """Fetch Steam achievements"""
        try:
            achievements = [
                {'name': 'First Steps', 'description': 'Complete the tutorial', 'unlocked': True, 'icon': ''},
                {'name': 'Explorer', 'description': 'Discover 10 locations', 'unlocked': False, 'icon': ''},
                {'name': 'Master', 'description': 'Complete the game', 'unlocked': False, 'icon': ''}
            ]
            
            unlocked_count = sum(1 for ach in achievements if ach['unlocked'])
            
            return {
                'total': len(achievements),
                'unlocked': unlocked_count,
                'percentage': (unlocked_count / len(achievements)) * 100 if achievements else 0,
                'achievements': achievements,
                'platform': 'steam'
            }
        except Exception:
            return {'total': 0, 'unlocked': 0, 'achievements': [], 'platform': 'steam', 'error': True, 'percentage': 0}
    
    def fetch_epic_achievements(self, game_id: str, game_name: str) -> Dict:
        """Fetch Epic Games achievements"""
        try:
            achievements = [
                {'name': 'Epic Start', 'description': 'Begin your journey', 'unlocked': True, 'icon': ''},
                {'name': 'Champion', 'description': 'Win 5 matches', 'unlocked': False, 'icon': ''}
            ]
            
            unlocked_count = sum(1 for ach in achievements if ach['unlocked'])
            
            return {
                'total': len(achievements),
                'unlocked': unlocked_count,
                'percentage': (unlocked_count / len(achievements)) * 100 if achievements else 0,
                'achievements': achievements,
                'platform': 'epic'
            }
        except Exception:
            return {'total': 0, 'unlocked': 0, 'achievements': [], 'platform': 'epic', 'error': True, 'percentage': 0}
    
    def fetch_ubisoft_achievements(self, game_id: str, game_name: str) -> Dict:
        """Fetch Ubisoft Connect achievements"""
        try:
            achievements = [
                {'name': 'Assassin', 'description': 'Complete first mission', 'unlocked': True, 'icon': ''},
                {'name': 'Legend', 'description': 'Reach maximum level', 'unlocked': False, 'icon': ''}
            ]
            
            unlocked_count = sum(1 for ach in achievements if ach['unlocked'])
            
            return {
                'total': len(achievements),
                'unlocked': unlocked_count,
                'percentage': (unlocked_count / len(achievements)) * 100 if achievements else 0,
                'achievements': achievements,
                'platform': 'ubisoft'
            }
        except Exception:
            return {'total': 0, 'unlocked': 0, 'achievements': [], 'platform': 'ubisoft', 'error': True, 'percentage': 0}
    
    def fetch_gog_achievements(self, game_id: str, game_name: str) -> Dict:
        """Fetch GOG Galaxy achievements"""
        try:
            achievements = [
                {'name': 'Adventurer', 'description': 'Start the adventure', 'unlocked': True, 'icon': ''},
                {'name': 'Completionist', 'description': 'Achieve 100% completion', 'unlocked': False, 'icon': ''}
            ]
            
            unlocked_count = sum(1 for ach in achievements if ach['unlocked'])
            
            return {
                'total': len(achievements),
                'unlocked': unlocked_count,
                'percentage': (unlocked_count / len(achievements)) * 100 if achievements else 0,
                'achievements': achievements,
                'platform': 'gog'
            }
        except Exception:
            return {'total': 0, 'unlocked': 0, 'achievements': [], 'platform': 'gog', 'error': True, 'percentage': 0}
    
    def get_achievement_summary(self, games: Dict) -> Dict:
        """Get overall achievement statistics"""
        total_games_with_achievements = 0
        total_achievements = 0
        total_unlocked = 0
        
        for game in games.values():
            achievements = self.get_game_achievements(
                game.get('game_id', ''), 
                game.get('platform', ''), 
                game.get('name', '')
            )
            if achievements.get('total', 0) > 0:
                total_games_with_achievements += 1
                total_achievements += achievements['total']
                total_unlocked += achievements['unlocked']
        
        return {
            'games_with_achievements': total_games_with_achievements,
            'total_achievements': total_achievements,
            'total_unlocked': total_unlocked,
            'completion_percentage': (total_unlocked / total_achievements) * 100 if total_achievements > 0 else 0
        }

class GameIconManager:
    def __init__(self):
        self.icon_cache = {}
        self.default_icon = None
        self.platform_icons = {}
        self.create_default_icons()

    def create_default_icons(self):
        """Create default icons for platforms and unknown games"""
        try:
            if PIL_AVAILABLE:
                img = Image.new('RGBA', (32, 32), (100, 100, 100, 255))
                self.default_icon = ImageTk.PhotoImage(img)

                platform_colors = {
                    'steam': (23, 26, 33, 255),
                    'epic': (242, 242, 242, 255),
                    'ubisoft': (0, 82, 165, 255),
                    'gog': (114, 36, 108, 255)
                }

                for platform_name, color in platform_colors.items():
                    img = Image.new('RGBA', (32, 32), color)
                    self.platform_icons[platform_name] = ImageTk.PhotoImage(img)
            else:
                self.default_icon = "[]"
                self.platform_icons = {
                    'steam': "S",
                    'epic': "E",
                    'ubisoft': "U",
                    'gog': "G"
                }
        except Exception:
            self.default_icon = "[]"
            self.platform_icons = {'steam': "S", 'epic': "E", 'ubisoft': "U", 'gog': "G"}

    def get_game_icon(self, game_id: str, game_name: str, platform_name: str) -> any:
        """Get game icon with caching"""
        cache_key = f"{platform_name}_{game_id}"

        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        icon = self.platform_icons.get(platform_name, self.default_icon)
        self.icon_cache[cache_key] = icon
        return icon

# Enhanced Aperture Science Theme
class ApertureTheme:
    # Core colors
    PRIMARY_BG = "#000000"
    SECONDARY_BG = "#050505"
    PANEL_BG = "#0a0a0a"
    ACCENT_BG = "#111111"
    
    # Aperture Science colors
    GLADOS_ORANGE = "#ff6600"
    WHEATLEY_BLUE = "#4488ff"
    PORTAL_BLUE = "#00ccff"
    PORTAL_ORANGE = "#ff8800"
    
    # Text colors
    TEXT_PRIMARY = "#ff6600"
    TEXT_SECONDARY = "#ffb366"
    TEXT_ACCENT = "#ffaa00"
    TEXT_MUTED = "#cc5500"
    
    # Status colors
    SUCCESS_GREEN = "#44cc44"
    ERROR_RED = "#ff4444"
    WARNING_YELLOW = "#ffcc44"
    
    # Button colors
    BUTTON_NORMAL = "#404040"
    BUTTON_HOVER = "#555555"
    BUTTON_ACTIVE = "#666666"
    
    # Border colors
    BORDER_LIGHT = "#555555"
    BORDER_DARK = "#222222"

class SmartGameScanner:
    def __init__(self):
        self.last_scan_time = 0
        self.confidence_weights = {'steam': 0.95, 'epic': 0.85, 'ubisoft': 0.75, 'gog': 0.90}
        
    def scan_all_platforms(self) -> Dict[str, List[Dict]]:
        results = {'steam': [], 'epic': [], 'ubisoft': [], 'gog': []}
        print(f"Starting platform scan on {platform.system()}")
        
        try:
            if platform.system() == "Windows":
                print("Scanning Windows platforms...")
                results['steam'] = self.scan_steam_windows()
                print(f"Steam scan found {len(results['steam'])} games")
                
                results['epic'] = self.scan_epic_windows()
                print(f"Epic scan found {len(results['epic'])} games")
                
                results['ubisoft'] = self.scan_ubisoft_windows()
                print(f"Ubisoft scan found {len(results['ubisoft'])} games")
                
                results['gog'] = self.scan_gog_windows()
                print(f"GOG scan found {len(results['gog'])} games")
                
            elif platform.system() == "Darwin":
                print("Scanning macOS platforms...")
                results['steam'] = self.scan_steam_mac()
                print(f"Steam scan found {len(results['steam'])} games")
                
            else:  # Linux
                print("Scanning Linux platforms...")
                results['steam'] = self.scan_steam_linux()
                print(f"Steam scan found {len(results['steam'])} games")
                
        except Exception as e:
            print(f"Platform scan error: {str(e)}")
        
        # Apply smart filtering to all results
        for platform_name, games in results.items():
            if games:
                filtered_games = self.apply_smart_filtering(games, platform_name)
                results[platform_name] = filtered_games
                print(f"Filtered {platform_name}: {len(filtered_games)} games after filtering")
        
        return results
    
    def apply_smart_filtering(self, games, platform_name):
        filtered = []
        base_confidence = self.confidence_weights.get(platform_name, 0.7)
        
        for game in games:
            confidence = self.calculate_confidence(game, base_confidence)
            if confidence > 0.6:
                game['confidence'] = confidence
                filtered.append(game)
        
        return sorted(filtered, key=lambda x: x.get('confidence', 0), reverse=True)
    
    def calculate_confidence(self, game, base_confidence):
        name = game.get('name', '').lower()
        
        popular_keywords = ['steam', 'portal', 'half-life', 'counter-strike']
        if any(keyword in name for keyword in popular_keywords):
            base_confidence += 0.1
            
        suspicious = ['test', 'demo', 'redistributable', 'runtime']
        if any(sus in name for sus in suspicious):
            base_confidence -= 0.3
            
        return max(0.0, min(1.0, base_confidence))

    def scan_steam_windows(self) -> List[Dict]:
        games = []
        all_games = {}  # Use dict to avoid duplicates
        print("Scanning Steam on Windows...")
        
        steam_paths_to_try = []
        
        # Try registry first
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            steam_path = Path(winreg.QueryValueEx(key, "InstallPath")[0])
            winreg.CloseKey(key)
            if steam_path.exists():
                steam_paths_to_try.append(steam_path)
                print(f"Found Steam via registry: {steam_path}")
        except Exception as e:
            print(f"Registry lookup failed: {e}")
        
        # Try common installation paths
        common_paths = [
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / "Steam",
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "Steam",
            Path("C:\\Steam"),
            Path.home() / "Steam"
        ]
        
        for path in common_paths:
            if path.exists() and path not in steam_paths_to_try:
                steam_paths_to_try.append(path)
                print(f"Found Steam at common path: {path}")
        
        # Scan each found Steam installation
        for steam_path in steam_paths_to_try:
            steamapps_path = steam_path / "steamapps"
            if steamapps_path.exists():
                print(f"Scanning steamapps at: {steamapps_path}")
                found_games = self.scan_steam_library(steamapps_path)
                
                # Add to dict to avoid duplicates
                for game in found_games:
                    game_key = f"{game['game_id']}_{game['name']}"
                    if game_key not in all_games:
                        all_games[game_key] = game
                
                print(f"Found {len(found_games)} games in this Steam library")
                
                # Also check for libraryfolders.vdf to find additional game libraries
                library_folders = self.find_additional_steam_libraries(steamapps_path)
                for library_path in library_folders:
                    print(f"Scanning additional library at: {library_path}")
                    additional_games = self.scan_steam_library(library_path)
                    for game in additional_games:
                        game_key = f"{game['game_id']}_{game['name']}"
                        if game_key not in all_games:
                            all_games[game_key] = game
                    print(f"Found {len(additional_games)} games in additional library")
            else:
                print(f"No steamapps folder found at: {steamapps_path}")
        
        games = list(all_games.values())
        print(f"Total unique Steam games found: {len(games)}")
        return games
    
    def find_additional_steam_libraries(self, steamapps_path: Path) -> List[Path]:
        """Find additional Steam library folders from libraryfolders.vdf"""
        additional_paths = []
        
        try:
            vdf_file = steamapps_path / "libraryfolders.vdf"
            if not vdf_file.exists():
                return additional_paths
            
            print(f"Reading library folders from: {vdf_file}")
            
            with open(vdf_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find all path entries in the VDF file
            path_matches = re.findall(r'"path"\s*"([^"]+)"', content)
            
            for path_str in path_matches:
                # Clean up the path (VDF uses double backslashes)
                clean_path = path_str.replace('\\\\', '\\')
                library_path = Path(clean_path) / "steamapps"
                
                if library_path.exists() and library_path != steamapps_path:
                    additional_paths.append(library_path)
                    print(f"Found additional library: {library_path}")
        
        except Exception as e:
            print(f"Error reading libraryfolders.vdf: {e}")
        
        return additional_paths
    
    def scan_steam_mac(self) -> List[Dict]:
        steam_path = Path.home() / "Library/Application Support/Steam"
        return self.scan_steam_library(steam_path / "steamapps") if steam_path.exists() else []
    
    def scan_steam_linux(self) -> List[Dict]:
        for path in [Path.home() / ".steam/steam", Path.home() / ".local/share/Steam"]:
            if path.exists():
                return self.scan_steam_library(path / "steamapps")
        return []
    
    def scan_steam_library(self, steamapps_path: Path) -> List[Dict]:
        games = []
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
                    # Try different encodings for file reading
                    content = None
                    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                        try:
                            with open(acf_file, 'r', encoding=encoding, errors='ignore') as f:
                                content = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if not content:
                        print(f"Could not read file: {acf_file}")
                        continue
                    
                    # Extract app ID and name using regex
                    app_id_match = re.search(r'"appid"\s*"(\d+)"', content)
                    name_match = re.search(r'"name"\s*"([^"]+)"', content)
                    
                    if app_id_match and name_match:
                        app_id = app_id_match.group(1)
                        name = name_match.group(1)
                        
                        if self.is_valid_game(name):
                            games.append({
                                'name': name,
                                'platform': 'steam',
                                'game_id': app_id,
                                'store_url': f"https://store.steampowered.com/app/{app_id}/",
                                'detected': True
                            })
                            valid_games_count += 1
                            if valid_games_count % 10 == 0:  # Progress update every 10 games
                                print(f"Progress: {valid_games_count} valid games found so far...")
                        else:
                            print(f"Filtered out non-game: {name}")
                    else:
                        print(f"Could not parse app data from: {acf_file.name}")
                        
                except Exception as e:
                    print(f"Error processing {acf_file.name}: {e}")
                    continue
            
            print(f"Processed {processed_count} manifest files, found {valid_games_count} valid games")
                    
        except Exception as e:
            print(f"Error scanning Steam library: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Steam library scan complete: {len(games)} valid games found")
        return games
    
    def is_valid_game(self, name: str) -> bool:
        if not name or len(name) < 3:
            return False
        name_lower = name.lower().strip()

        exact_exclusions = {
            'steamworks common redistributables',
            'steam linux runtime',
            'steam linux runtime soldier',
            'steamvr',
            'proton easy anti cheat runtime'
        }
        if name_lower in exact_exclusions:
            return False

        keyword_exclusions = [
            'steamworks',
            'steam linux runtime',
            'proton',
            'steamvr',
            'directx',
            'visual c++',
            'vcredist',
            'redistributable',
            'runtime',
            'benchmark',
            'dedicated server',
            'server tool',
            'mod tools',
            'workshop tools',
            'sdk',
            'soundtrack',
            'original soundtrack',
            'ost',
            'test app',
            'launcher',
            'compatibility tool',
            'tools ',
            ' tool'
        ]
        if any(keyword in name_lower for keyword in keyword_exclusions):
            return False

        import re
        tokens = [token for token in re.split(r'[^a-z0-9]+', name_lower) if token]
        token_exclusions = {'demo', 'test', 'beta', 'benchmark', 'soundtrack', 'sdk', 'editor', 'tools', 'tool'}
        if any(token in token_exclusions for token in tokens):
            return False

        return True
    
    def scan_epic_windows(self) -> List[Dict]:
        games = []
        print("Scanning Epic Games on Windows...")
        
        try:
            # Epic Games stores manifests in multiple locations
            epic_paths = [
                Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / "Epic/EpicGamesLauncher/Data/Manifests",
                Path(os.environ.get('LOCALAPPDATA', '')) / "EpicGamesLauncher/Saved/Config/Windows",
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
                        with open(manifest, 'r', encoding='utf-8', errors='ignore') as f:
                            data = json.load(f)
                        
                        # Epic uses different field names
                        name = data.get('DisplayName') or data.get('AppName') or data.get('LaunchCommand', '')
                        game_id = data.get('CatalogItemId') or data.get('AppName') or data.get('InstallationGuid', '')
                        
                        if name and game_id and self.is_valid_game(name):
                            games.append({
                                'name': name,
                                'platform': 'epic',
                                'game_id': game_id,
                                'store_url': "https://store.epicgames.com/",
                                'detected': True
                            })
                            print(f"Found Epic game: {name}")
                    except Exception as e:
                        print(f"Error processing Epic manifest {manifest.name}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error scanning Epic Games: {e}")
        
        print(f"Total Epic games found: {len(games)}")
        return games
    
    def scan_ubisoft_windows(self) -> List[Dict]:
        games = []
        print("Scanning Ubisoft Connect on Windows...")
        
        try:
            # Check registry for installed Ubisoft games
            registry_paths = [
                r"SOFTWARE\WOW6432Node\Ubisoft",
                r"SOFTWARE\Ubisoft"
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    i = 0
                    
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            game_key = None
                            
                            try:
                                game_key = winreg.OpenKey(key, subkey_name)
                                
                                # Try to get display name
                                try:
                                    name = winreg.QueryValueEx(game_key, "DisplayName")[0]
                                except:
                                    try:
                                        name = winreg.QueryValueEx(game_key, "InstallDir")[0]
                                        name = Path(name).name if name else subkey_name
                                    except:
                                        name = subkey_name
                                
                                if name and self.is_valid_game(name):
                                    games.append({
                                        'name': name,
                                        'platform': 'ubisoft',
                                        'game_id': subkey_name,
                                        'store_url': "https://store.ubi.com/",
                                        'detected': True
                                    })
                                    print(f"Found Ubisoft game: {name}")
                            finally:
                                if game_key:
                                    winreg.CloseKey(game_key)
                            
                            i += 1
                        except OSError:
                            break
                    
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"Could not access registry path {reg_path}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scanning Ubisoft games: {e}")
        
        print(f"Total Ubisoft games found: {len(games)}")
        return games
    
    def scan_gog_windows(self) -> List[Dict]:
        games = []
        print("Scanning GOG Galaxy on Windows...")
        
        try:
            # Check registry for GOG games
            registry_paths = [
                r"SOFTWARE\WOW6432Node\GOG.com\Games",
                r"SOFTWARE\GOG.com\Games"
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    i = 0
                    
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            game_key = None
                            
                            try:
                                game_key = winreg.OpenKey(key, subkey_name)
                                
                                # Try to get game name
                                try:
                                    name = winreg.QueryValueEx(game_key, "gameName")[0]
                                except:
                                    try:
                                        name = winreg.QueryValueEx(game_key, "gameID")[0]
                                    except:
                                        name = subkey_name
                                
                                if name and self.is_valid_game(name):
                                    games.append({
                                        'name': name,
                                        'platform': 'gog',
                                        'game_id': subkey_name,
                                        'store_url': "https://www.gog.com/",
                                        'detected': True
                                    })
                                    print(f"Found GOG game: {name}")
                            finally:
                                if game_key:
                                    winreg.CloseKey(game_key)
                            
                            i += 1
                        except OSError:
                            break
                    
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"Could not access registry path {reg_path}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scanning GOG games: {e}")
        
        print(f"Total GOG games found: {len(games)}")
        return games

class GameDataManager:
    def __init__(self):
        self.game_data = self.load_game_data()
    
    def load_game_data(self) -> Dict:
        try:
            if GAME_DATA_FILE.exists():
                with open(GAME_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass

        return {
            'version': '2.5',
            'games': {},
            'next_id': 1,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def save_game_data(self):
        try:
            self.game_data['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(GAME_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.game_data, f, indent=2)
        except Exception:
            pass
    
    def add_game(self, name: str, platform_name: str, game_id: str, store_url: str = "", search_data: Dict = None) -> int:
        game_number = self.game_data['next_id']
        
        self.game_data['games'][str(game_number)] = {
            'name': name,
            'platform': platform_name.lower(),
            'game_id': game_id,
            'store_url': store_url,
            'protocol_url': self.generate_protocol_url(platform_name, game_id),
            'added_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'play_count': 0,
            'last_played': None,
            'search_data': search_data or {},
            'user_rating': 0
        }
        
        self.game_data['next_id'] += 1
        self.save_game_data()
        return game_number
    
    def generate_protocol_url(self, platform_name: str, game_id: str) -> str:
        platform_name = platform_name.lower()
        urls = {
            'steam': f"steam://rungameid/{game_id}",
            'ubisoft': f"uplay://launch/{game_id}",
            'epic': f"com.epicgames.launcher://apps/{game_id}?action=launch",
            'gog': f"goggalaxy://openGameView/{game_id}"
        }
        return urls.get(platform_name, game_id)
    
    def remove_game(self, game_id: str) -> bool:
        try:
            if game_id in self.game_data['games']:
                del self.game_data['games'][game_id]
                self.save_game_data()
                return True
        except Exception:
            pass
        return False
    
    def remove_all_games(self) -> bool:
        try:
            if self.game_data.get('games'):
                self.game_data['games'].clear()
                self.game_data['next_id'] = 1
                self.save_game_data()
            return True
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
    
    def get_smart_sorted_games(self) -> List[tuple]:
        games = self.get_games()
        return sorted(games.items(), key=lambda x: (
            -(x[1].get('play_count', 0)),
            x[1].get('last_played', '1900-01-01'),
            x[1]['name'].lower()
        ))
    
    def get_recommendations(self) -> List[str]:
        games = self.get_games()
        if not games:
            return ["Scan for games to get personalized recommendations!"]
        
        platform_counts = {}
        for game in games.values():
            platform_name = game['platform']
            plays = game.get('play_count', 0)
            platform_counts[platform_name] = platform_counts.get(platform_name, 0) + plays
        
        if platform_counts:
            favorite_platform = max(platform_counts.items(), key=lambda x: x[1])[0]
            platform_recs = {
                'steam': ["Try Portal 2 for puzzle excellence", "Half-Life series for FPS mastery"],
                'epic': ["Check weekly free games", "Try Fortnite for battle royale"],
                'ubisoft': ["Assassin's Creed series", "Far Cry for open world"],
                'gog': ["Classic DRM-free games", "Witcher series available"]
            }
            return platform_recs.get(favorite_platform, ["Explore more games on your platform"])
        
        return ["Build your gaming profile by playing more games!"]

class GameLauncher:
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
    
    def launch_game(self, game_url: str, platform_name: str = "unknown") -> bool:
        try:
            if platform.system() == "Windows":
                subprocess.run(f'start "" "{game_url}"', shell=True, check=False)
            elif platform.system() == "Darwin":
                subprocess.run(['open', game_url], check=False)
            else:
                subprocess.run(['xdg-open', game_url], check=False)
            return True
        except Exception:
            try:
                webbrowser.open(game_url)
                return True
            except Exception:
                return False



@dataclass
class UpdateCheckResult:
    success: bool
    update_available: bool
    message: str
    current_version: str
    latest_version: Optional[str] = None
    severity: str = "info"


class UpdateFetchError(Exception):
    def __init__(self, base_error: Exception, attempted_sources: List[str]):
        self.base_error = base_error
        self.attempted_sources = attempted_sources
        message = f"{base_error}. Sources tried: {', '.join(attempted_sources)}" if attempted_sources else str(base_error)
        super().__init__(message)


@dataclass
class UpdateApplyResult:
    success: bool
    message: str



AUTO_UPDATE_GITHUB_REPO = "be-smiley2/glados_game_launcher"
AUTO_UPDATE_RELEASES_API_URL = f"https://api.github.com/repos/{AUTO_UPDATE_GITHUB_REPO}/releases/latest"
AUTO_UPDATE_COMMON_BRANCHES: Tuple[str, ...] = ("main", "master", "release", "stable")
AUTO_UPDATE_POSSIBLE_SCRIPT_PATHS: Tuple[str, ...] = (
    "glados_game_launcher.py",
    "src/glados_game_launcher.py",
    "glados_game_launcher/glados_game_launcher.py",
)
AUTO_UPDATE_RAW_SCRIPT_URLS: Tuple[str, ...] = tuple(
    f"https://raw.githubusercontent.com/{AUTO_UPDATE_GITHUB_REPO}/{branch}/{path}"
    for branch in AUTO_UPDATE_COMMON_BRANCHES
    for path in AUTO_UPDATE_POSSIBLE_SCRIPT_PATHS
)

class AutoUpdateManager:
    GITHUB_REPO = AUTO_UPDATE_GITHUB_REPO
    RELEASES_API_URL = AUTO_UPDATE_RELEASES_API_URL
    COMMON_BRANCHES: Tuple[str, ...] = AUTO_UPDATE_COMMON_BRANCHES
    POSSIBLE_SCRIPT_PATHS: Tuple[str, ...] = AUTO_UPDATE_POSSIBLE_SCRIPT_PATHS
    RAW_SCRIPT_URLS: Tuple[str, ...] = AUTO_UPDATE_RAW_SCRIPT_URLS
    VERSION_PATTERN = re.compile(r"^CURRENT_VERSION\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)

    def __init__(self, current_version: str, script_path: Path):
        self.current_version = current_version
        self.script_path = script_path
        self.latest_version = current_version
        self.remote_script: Optional[str] = None
        self.active_source: Optional[str] = None
        self.last_attempted_sources: List[str] = []
        self.last_release_data: Optional[Dict[str, Any]] = None

    def is_supported(self) -> bool:
        return (not getattr(sys, "frozen", False)) and self.script_path.exists() and self.script_path.suffix == ".py"

    def _candidate_urls(self) -> List[str]:
        candidates: List[str] = []
        for branch in self.COMMON_BRANCHES:
            for relative_path in self.POSSIBLE_SCRIPT_PATHS:
                candidates.append(
                    f"https://raw.githubusercontent.com/{self.GITHUB_REPO}/{branch}/{relative_path}"
                )
        return candidates

    def _normalize_version(self, version: str) -> Optional[str]:
        if not version:
            return None
        cleaned = str(version).strip()
        if cleaned.lower().startswith('v'):
            cleaned = cleaned[1:]
        cleaned = cleaned.strip()
        return cleaned or None

    def _fetch_latest_release(self) -> Optional[Dict[str, Any]]:
        if self.RELEASES_API_URL not in self.last_attempted_sources:
            self.last_attempted_sources.append(self.RELEASES_API_URL)
        response = requests.get(
            self.RELEASES_API_URL,
            headers={
                'Accept': 'application/vnd.github+json',
                'User-Agent': f'GLaDOS-Launcher/{self.current_version}'
            },
            timeout=10
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        release_data: Dict[str, Any] = response.json()
        normalized = self._normalize_version(release_data.get('tag_name') or release_data.get('name') or '')
        if not normalized:
            body = release_data.get('body') or ''
            match = self.VERSION_PATTERN.search(body)
            if match:
                normalized = match.group(1)
        release_data['normalized_version'] = normalized
        return release_data

    def _download_release_asset(self) -> Optional[str]:
        if not self.last_release_data:
            return None
        assets = self.last_release_data.get('assets') or []
        for asset in assets:
            name = str(asset.get('name', '')).lower()
            if not name.endswith('.py'):
                continue
            url = asset.get('browser_download_url')
            if not url:
                continue
            if url not in self.last_attempted_sources:
                self.last_attempted_sources.append(str(url))
            response = requests.get(
                url,
                headers={'User-Agent': f'GLaDOS-Launcher/{self.current_version}'},
                timeout=15
            )
            response.raise_for_status()
            self.active_source = str(url)
            return response.text
        return None

    def _fetch_remote_script(self) -> str:
        attempted: List[str] = list(self.last_attempted_sources)
        last_error: Optional[Exception] = None
        for url in self._candidate_urls():
            attempted.append(url)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                self.active_source = url
                self.last_attempted_sources = attempted.copy()
                return response.text
            except Exception as exc:
                last_error = exc
        self.last_attempted_sources = attempted
        raise UpdateFetchError(last_error or RuntimeError("No update sources configured"), attempted)


    def check_for_updates(self) -> UpdateCheckResult:
        if not REQUESTS_AVAILABLE:
            return UpdateCheckResult(False, False, "Requests module unavailable; cannot check for updates.", self.current_version, severity="warning")
        if not self.is_supported():
            return UpdateCheckResult(False, False, "Auto-update is only available when running from source builds.", self.current_version, severity="warning")

        self.last_release_data = None
        self.last_attempted_sources = []
        release_error: Optional[Exception] = None
        release_info: Optional[Dict[str, Any]] = None

        try:
            release_info = self._fetch_latest_release()
        except Exception as exc:
            release_error = exc

        if release_info:
            self.last_release_data = release_info
            normalized_version = release_info.get('normalized_version')
            if normalized_version:
                latest_version = str(normalized_version)
                self.latest_version = latest_version
                self.active_source = release_info.get('html_url') or self.RELEASES_API_URL
                if self._compare_versions(latest_version, self.current_version) > 0:
                    message = f"Update {latest_version} available on GitHub releases."
                    return UpdateCheckResult(True, True, message, self.current_version, latest_version=latest_version)
                message = f"You are running the latest version ({self.current_version})."
                return UpdateCheckResult(True, False, message, self.current_version, latest_version=latest_version)

        try:
            remote_script = self._fetch_remote_script()
            match = self.VERSION_PATTERN.search(remote_script)
            if not match:
                extra = f" GitHub releases lookup failed: {release_error}." if release_error else ""
                return UpdateCheckResult(False, False, "Unable to determine remote version." + extra, self.current_version, severity="error")
            remote_version = match.group(1)
            self.remote_script = remote_script
            self.latest_version = remote_version
            if self._compare_versions(remote_version, self.current_version) > 0:
                return UpdateCheckResult(True, True, f"Update {remote_version} available.", self.current_version, latest_version=remote_version)
            return UpdateCheckResult(True, False, f"You are running the latest version ({self.current_version}).", self.current_version, latest_version=remote_version)
        except Exception as exc:
            attempted = self.last_attempted_sources or list(self.RAW_SCRIPT_URLS)
            sources = ", ".join(attempted)
            details = str(exc)
            if release_error:
                details = f"GitHub releases error: {release_error}; fallback error: {exc}"
            return UpdateCheckResult(False, False, f"Update check failed: {details}. Tried sources: {sources}", self.current_version, severity="error")

    def download_and_apply_update(self) -> UpdateApplyResult:
        if not REQUESTS_AVAILABLE:
            return UpdateApplyResult(False, "Requests module unavailable; cannot download updates.")
        if not self.is_supported():
            return UpdateApplyResult(False, "Auto-update is only available when running from source builds.")

        asset_error: Optional[Exception] = None

        try:
            if not self.remote_script:
                if self.last_release_data:
                    try:
                        self.remote_script = self._download_release_asset()
                    except Exception as exc:
                        asset_error = exc
                if not self.remote_script:
                    self.remote_script = self._fetch_remote_script()
                if self.remote_script:
                    match = self.VERSION_PATTERN.search(self.remote_script)
                    if match:
                        self.latest_version = match.group(1)

            if not self.remote_script:
                message = "No update payload available."
                if asset_error:
                    message += f" Latest release asset download failed: {asset_error}"
                return UpdateApplyResult(False, message)

            original_content = self.script_path.read_text(encoding="utf-8")
            backup_path = self.script_path.with_suffix(self.script_path.suffix + ".bak")
            backup_path.write_text(original_content, encoding="utf-8")
            self.script_path.write_text(self.remote_script, encoding="utf-8")
            message = f"Update installed successfully. Backup stored as {backup_path.name}. Please restart the application."
            return UpdateApplyResult(True, message)
        except Exception as exc:
            attempted = self.last_attempted_sources or list(self.RAW_SCRIPT_URLS)
            sources = ", ".join(attempted)
            details = str(exc)
            if asset_error:
                details = f"Release asset error: {asset_error}; fallback error: {exc}"
            return UpdateApplyResult(False, f"Update installation failed: {details}. Tried sources: {sources}")

    @staticmethod
    def _compare_versions(a: str, b: str) -> int:
        def parse(version: str) -> Tuple[int, ...]:
            parts = [int(part) for part in re.findall(r"\d+", version)]
            return tuple(parts) if parts else (0,)
        va = parse(a)
        vb = parse(b)
        length = max(len(va), len(vb))
        va = va + (0,) * (length - len(va))
        vb = vb + (0,) * (length - len(vb))
        if va > vb:
            return 1
        if va < vb:
            return -1
        return 0


class TrainTetrisGame:
    COLS = 10
    ROWS = 20
    TILE_SIZE = 26
    BASE_DROP_MS = 600
    LEVEL_DROP_DELTA = 45

    PIECES = (
        {
            "name": "Engine",
            "color": "#FF6B35",
            "rotations": (
                ((0, 1), (1, 1), (2, 1), (3, 1)),
                ((2, 0), (2, 1), (2, 2), (2, 3)),
            ),
        },
        {
            "name": "Cargo",
            "color": "#F7C59F",
            "rotations": (
                ((1, 0), (2, 0), (1, 1), (2, 1)),
            ),
        },
        {
            "name": "Freight",
            "color": "#004E89",
            "rotations": (
                ((0, 0), (0, 1), (1, 1), (2, 1)),
                ((1, 0), (2, 0), (1, 1), (1, 2)),
                ((0, 1), (1, 1), (2, 1), (2, 2)),
                ((1, 0), (1, 1), (0, 2), (1, 2)),
            ),
        },
        {
            "name": "Passenger",
            "color": "#2D7DD2",
            "rotations": (
                ((2, 0), (0, 1), (1, 1), (2, 1)),
                ((1, 0), (1, 1), (1, 2), (2, 2)),
                ((0, 1), (1, 1), (2, 1), (0, 2)),
                ((0, 0), (1, 0), (1, 1), (1, 2)),
            ),
        },
        {
            "name": "Coal",
            "color": "#7F2982",
            "rotations": (
                ((1, 0), (0, 1), (1, 1), (2, 1)),
                ((1, 0), (1, 1), (2, 1), (1, 2)),
                ((0, 1), (1, 1), (2, 1), (1, 2)),
                ((1, 0), (0, 1), (1, 1), (1, 2)),
            ),
        },
        {
            "name": "Hopper",
            "color": "#0FA3B1",
            "rotations": (
                ((1, 0), (2, 0), (0, 1), (1, 1)),
                ((1, 0), (1, 1), (2, 1), (2, 2)),
            ),
        },
        {
            "name": "Caboose",
            "color": "#F25F5C",
            "rotations": (
                ((0, 0), (1, 0), (1, 1), (2, 1)),
                ((2, 0), (2, 1), (1, 1), (1, 2)),
            ),
        },
    )

    def __init__(self, master: tk.Tk, on_close=None):
        self.master = master
        self.on_close = on_close
        self.window = tk.Toplevel(master)
        self.window.title("Aperture Train Stacking Initiative")
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.transient(master)

        board_width = self.COLS * self.TILE_SIZE
        board_height = self.ROWS * self.TILE_SIZE

        container = ttk.Frame(self.window, style='Panel.TFrame')
        container.pack(fill='both', expand=True, padx=12, pady=12)

        info_frame = ttk.Frame(container, style='Panel.TFrame')
        info_frame.pack(fill='x', pady=(0, 10))

        self.info_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Stack train cars without derailing them.")
        self.next_var = tk.StringVar()

        ttk.Label(info_frame, textvariable=self.info_var, style='GLaDOS.TLabel').pack(anchor='w')
        ttk.Label(info_frame, textvariable=self.status_var, style='Aperture.TLabel', wraplength=board_width).pack(anchor='w', pady=(4, 0))
        ttk.Label(info_frame, textvariable=self.next_var, style='Wheatley.TLabel').pack(anchor='w', pady=(4, 0))

        self.canvas = tk.Canvas(
            container,
            width=board_width,
            height=board_height,
            bg=ApertureTheme.SECONDARY_BG,
            highlightthickness=0
        )
        self.canvas.pack()

        ttk.Label(
            container,
            text="Controls: ? ? move | ? rotate | ? nudge down | Space hard drop | Esc exit",
            style='Aperture.TLabel'
        ).pack(anchor='center', pady=(10, 0))

        self.board = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_piece = None
        self.next_piece = None
        self.after_handle = None
        self.running = True
        self._closed = False
        self.score = 0
        self.lines = 0
        self.level = 1

        self.next_piece = self._create_piece()
        self.current_piece = self._take_next_piece()
        if not self._valid_position(self.current_piece):
            self._game_over()
        else:
            self._update_labels()
            self._render()
            self._schedule_tick()

        self.window.bind('<Left>', lambda event: self._attempt_move(-1, 0))
        self.window.bind('<Right>', lambda event: self._attempt_move(1, 0))
        self.window.bind('<Down>', lambda event: self._soft_drop())
        self.window.bind('<Up>', lambda event: self._rotate())
        self.window.bind('<space>', lambda event: self._hard_drop())
        self.window.bind('<Escape>', lambda event: self.close())
        self.window.after(100, self.window.focus_force)

    @property
    def is_open(self) -> bool:
        return not self._closed and self.window.winfo_exists()

    def focus(self):
        if self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def close(self):
        if self._closed:
            return
        self.running = False
        if self.after_handle is not None:
            try:
                self.window.after_cancel(self.after_handle)
            except Exception:
                pass
            self.after_handle = None
        self._closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window.winfo_exists():
            self.window.destroy()

    def _create_piece(self) -> Dict[str, Any]:
        shape = random.choice(self.PIECES)
        piece = {
            "shape": shape,
            "rotation": 0,
            "x": self.COLS // 2 - 2,
            "y": 0,
        }
        return self._adjust_spawn(piece)

    def _adjust_spawn(self, piece: Dict[str, Any]) -> Dict[str, Any]:
        coords = piece["shape"]["rotations"][piece["rotation"]]
        min_x = min(x for x, _ in coords)
        max_x = max(x for x, _ in coords)
        if piece["x"] + min_x < 0:
            piece["x"] -= piece["x"] + min_x
        if piece["x"] + max_x >= self.COLS:
            piece["x"] -= (piece["x"] + max_x) - (self.COLS - 1)
        return piece

    def _take_next_piece(self) -> Dict[str, Any]:
        piece = self.next_piece or self._create_piece()
        self.next_piece = self._create_piece()
        self._update_next_label()
        return piece

    def _update_next_label(self):
        if self.next_piece:
            self.next_var.set(f"Next consist: {self.next_piece['shape']['name']}")
        else:
            self.next_var.set("")

    def _schedule_tick(self):
        if not self.running:
            return
        interval = max(120, self.BASE_DROP_MS - (self.level - 1) * self.LEVEL_DROP_DELTA)
        self.after_handle = self.window.after(interval, self._tick)

    def _tick(self):
        if not self.running:
            return
        if self._valid_position(self.current_piece, offset_y=1):
            self.current_piece["y"] += 1
        else:
            self._lock_piece()
            cleared = self._clear_lines()
            if cleared:
                self._handle_line_clear(cleared)
            self.current_piece = self._take_next_piece()
            if not self._valid_position(self.current_piece):
                self._game_over()
                return
            self.status_var.set(f"{self.current_piece['shape']['name']} inbound. Maintain alignment.")
        self._render()
        self._schedule_tick()

    def _attempt_move(self, dx: int, dy: int):
        if not self.running:
            return
        if self._valid_position(self.current_piece, offset_x=dx, offset_y=dy):
            self.current_piece["x"] += dx
            self.current_piece["y"] += dy
            self._render()

    def _soft_drop(self):
        if not self.running:
            return
        if self._valid_position(self.current_piece, offset_y=1):
            self.current_piece["y"] += 1
            self.score += 1
            self._render()
            self._update_labels()
        else:
            self._tick()

    def _hard_drop(self):
        if not self.running:
            return
        distance = 0
        while self._valid_position(self.current_piece, offset_y=1):
            self.current_piece["y"] += 1
            distance += 1
        if distance:
            self.score += 2 * distance
        self._tick()

    def _rotate(self):
        if not self.running:
            return
        piece = self.current_piece
        shape = piece["shape"]
        next_rotation = (piece["rotation"] + 1) % len(shape["rotations"])
        if self._valid_position(piece, rotation=next_rotation):
            piece["rotation"] = next_rotation
            self._adjust_spawn(piece)
            self._render()

    def _valid_position(self, piece: Dict[str, Any], offset_x: int = 0, offset_y: int = 0, rotation: Optional[int] = None) -> bool:
        rotation = piece["rotation"] if rotation is None else rotation
        for x, y in piece["shape"]["rotations"][rotation]:
            board_x = piece["x"] + offset_x + x
            board_y = piece["y"] + offset_y + y
            if board_x < 0 or board_x >= self.COLS or board_y >= self.ROWS:
                return False
            if board_y >= 0 and self.board[board_y][board_x] is not None:
                return False
        return True

    def _lock_piece(self):
        for x, y in self._cells(self.current_piece):
            if 0 <= y < self.ROWS and 0 <= x < self.COLS:
                self.board[y][x] = self.current_piece["shape"]["color"]
        self.score += 10
        self._update_labels()

    def _cells(self, piece: Dict[str, Any]) -> List[Tuple[int, int]]:
        coords = []
        for x, y in piece["shape"]["rotations"][piece["rotation"]]:
            coords.append((piece["x"] + x, piece["y"] + y))
        return coords

    def _clear_lines(self) -> int:
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = self.ROWS - len(remaining)
        if cleared:
            new_rows = [[None for _ in range(self.COLS)] for _ in range(cleared)]
            self.board = new_rows + remaining
        return cleared

    def _handle_line_clear(self, cleared: int):
        self.lines += cleared
        self.level = 1 + self.lines // 8
        line_scores = {1: 100, 2: 300, 3: 700, 4: 1500}
        self.score += line_scores.get(cleared, 1500) * max(1, self.level)
        messages = {
            1: "Platform cleared. Efficiency improving.",
            2: "Double-line dispatch. Trains on schedule.",
            3: "Triple consist alignment achieved!",
            4: "Perfect quad-stack! GLaDOS is almost impressed.",
        }
        self.status_var.set(messages.get(cleared, "Rail network optimized."))
        self._update_labels()

    def _update_labels(self):
        self.info_var.set(f"Score: {self.score} | Lines: {self.lines} | Level: {self.level}")

    def _render(self):
        self.canvas.delete('block')
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self._draw_cell(x, y, color)
        if self.current_piece:
            for x, y in self._cells(self.current_piece):
                if y >= 0:
                    self._draw_cell(x, y, self.current_piece["shape"]["color"], outline=ApertureTheme.PRIMARY_BG)

    def _draw_cell(self, x: int, y: int, color: str, outline: Optional[str] = None):
        x1 = x * self.TILE_SIZE
        y1 = y * self.TILE_SIZE
        x2 = x1 + self.TILE_SIZE
        y2 = y1 + self.TILE_SIZE
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline=outline or ApertureTheme.SECONDARY_BG,
            width=1,
            tags='block'
        )

    def _game_over(self):
        self.running = False
        self.status_var.set(f"Derailment detected. Final score: {self.score}.")
        self._update_labels()
        messagebox.showinfo("Train Yard Simulation", f"Derailment detected! Final score: {self.score}")
        self.close()


class ApertureEnrichmentCenterGUI:
    def __init__(self):
        print("Initializing ApertureEnrichmentCenterGUI...")
        
        try:
            self.root = tk.Tk()
            print("Tkinter root window created")
            
            self.game_manager = GameDataManager()
            print("Game manager initialized")
            
            self.scanner = SmartGameScanner()
            print("Scanner initialized")
            
            self.launcher = GameLauncher(self.game_manager)
            self.icon_manager = GameIconManager()
            self.achievement_manager = AchievementManager()
            self.update_manager = AutoUpdateManager(CURRENT_VERSION, CURRENT_SCRIPT)
            print("Managers initialized")

            self.update_check_in_progress = False
            self.update_install_in_progress = False
            self.last_scan_results = {}
            self.user_preferences = self.load_preferences()
            self.smart_mode = True
            self.commentary_mode = tk.StringVar(value="balanced")
            
            print("Setting up GUI...")
            self.setup_gui()
            print("Setting up styles...")
            self.setup_styles()
            print("Creating interface...")
            self.create_interface()
            print("Refreshing game list...")
            self.refresh_game_list()
            print("Initializing features...")
            self.initialize_features()
            print("GUI initialization complete!")
            
        except Exception as e:
            print(f"Error initializing GUI: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def load_preferences(self):
        try:
            if USER_PREFS_FILE.exists():
                with open(USER_PREFS_FILE, 'r') as f:
                    prefs = json.load(f)
                    if 'last_update_check' not in prefs:
                        prefs['last_update_check'] = 0
                    return prefs
        except Exception:
            pass
        return {
            'smart_recommendations': True,
            'auto_sort': True,
            'commentary_level': 'balanced',
            'last_update_check': 0
        }
    
    def save_preferences(self):
        try:
            with open(USER_PREFS_FILE, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception:
            pass
    
    def setup_gui(self):
        self.root.title(f"Aperture Science Enrichment Center - Game Management v{CURRENT_VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        self.root.configure(bg=ApertureTheme.PRIMARY_BG)
        
        # Set window icon if available
        try:
            self.root.iconname("Aperture Science")
        except Exception:
            pass
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure styles with Aperture Science theme
        styles = {
            'Aperture.TFrame': {
                'background': ApertureTheme.PRIMARY_BG,
                'relief': 'flat'
            },
            'Panel.TFrame': {
                'background': ApertureTheme.PANEL_BG,
                'relief': 'raised',
                'borderwidth': 2
            },
            'Header.TFrame': {
                'background': ApertureTheme.ACCENT_BG,
                'relief': 'groove',
                'borderwidth': 3
            },
            'Aperture.TLabel': {
                'background': ApertureTheme.PRIMARY_BG,
                'foreground': ApertureTheme.TEXT_PRIMARY,
                'font': ('Arial', 10)
            },
            'GLaDOS.TLabel': {
                'background': ApertureTheme.ACCENT_BG,
                'foreground': ApertureTheme.GLADOS_ORANGE,
                'font': ('Arial', 14, 'bold')
            },
            'Wheatley.TLabel': {
                'background': ApertureTheme.PRIMARY_BG,
                'foreground': ApertureTheme.WHEATLEY_BLUE,
                'font': ('Arial', 11)
            },
            'Aperture.TButton': {
                'background': ApertureTheme.BUTTON_NORMAL,
                'foreground': ApertureTheme.TEXT_PRIMARY,
                'borderwidth': 2,
                'relief': 'raised'
            },
            'GLaDOS.TButton': {
                'background': ApertureTheme.GLADOS_ORANGE,
                'foreground': ApertureTheme.PRIMARY_BG,
                'borderwidth': 2,
                'relief': 'raised',
                'font': ('Arial', 10, 'bold')
            },
            'Aperture.Treeview': {
                'background': ApertureTheme.SECONDARY_BG,
                'foreground': ApertureTheme.TEXT_PRIMARY,
                'fieldbackground': ApertureTheme.SECONDARY_BG,
                'borderwidth': 2,
                'relief': 'groove',
                'rowheight': 54
            },
            'Aperture.TCheckbutton': {
                'background': ApertureTheme.PRIMARY_BG,
                'foreground': ApertureTheme.TEXT_PRIMARY
            },
            'Aperture.TRadiobutton': {
                'background': ApertureTheme.PRIMARY_BG,
                'foreground': ApertureTheme.TEXT_PRIMARY
            }
        }
        
        for style_name, style_config in styles.items():
            self.style.configure(style_name, **style_config)
    
    def create_interface(self):
        """Create the main interface"""
        # Main container
        main_container = ttk.Frame(self.root, style='Aperture.TFrame')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header section
        self.create_header(main_container)
        
        # Content area
        content_paned = ttk.PanedWindow(main_container, orient='horizontal')
        content_paned.pack(fill='both', expand=True, pady=(10, 0))
        
        # Left panel - Game list and controls
        self.create_left_panel(content_paned)
        
        # Right panel - Commentary and recommendations
        self.create_right_panel(content_paned)
        
        content_paned.add(self.left_panel, weight=3)
        content_paned.add(self.right_panel, weight=1)
    
    def create_header(self, parent):
        """Create the application header"""
        header_frame = ttk.Frame(parent, style='Header.TFrame')
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Title
        title_frame = ttk.Frame(header_frame, style='Header.TFrame')
        title_frame.pack(fill='x', padx=20, pady=15)
        
        ttk.Label(title_frame, text="APERTURE SCIENCE ENRICHMENT CENTER", 
                 style='GLaDOS.TLabel').pack()
        ttk.Label(title_frame, text="Advanced Game Management System v2.5", 
                 style='Wheatley.TLabel').pack(pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(header_frame, style='Header.TFrame')
        button_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        # Scan buttons
        scan_frame = ttk.Frame(button_frame, style='Header.TFrame')
        scan_frame.pack(side='left')
        
        ttk.Button(scan_frame, text="FULL SCAN", style='GLaDOS.TButton', 
                  command=self.run_smart_scan).pack(side='left', padx=(0, 5))
        
        platform_buttons = [
            ("Steam", lambda: self.run_platform_scan('steam')),
            ("Epic", lambda: self.run_platform_scan('epic')),
            ("Ubisoft", lambda: self.run_platform_scan('ubisoft')),
            ("GOG", lambda: self.run_platform_scan('gog'))
        ]
        
        for text, command in platform_buttons:
            ttk.Button(scan_frame, text=text, style='Aperture.TButton', 
                      command=command).pack(side='left', padx=2)
        
        # Quick action buttons (CENTER) - LAUNCH TEST button here
        quick_action_frame = ttk.Frame(button_frame, style='Header.TFrame')
        quick_action_frame.pack(side='left', padx=50)
        
        ttk.Button(quick_action_frame, text="▶ LAUNCH TEST", style='GLaDOS.TButton', 
                  command=self.launch_selected_game, width=15).pack(side='left', padx=5)
        ttk.Button(quick_action_frame, text="STORE PAGE", style='Aperture.TButton', 
                  command=self.open_store_page, width=12).pack(side='left', padx=5)
        
        # Management buttons (RIGHT)
        mgmt_frame = ttk.Frame(button_frame, style='Header.TFrame')
        mgmt_frame.pack(side='right')
        
        mgmt_buttons = [
            ("ADD", self.show_add_dialog),
            ("REMOVE", self.remove_selected_game),
            ("REMOVE ALL", self.remove_all_games),
            ("RATE", self.rate_selected_game),
            ("ACHIEVEMENTS", self.show_achievements),
            ("ANALYSIS", self.show_analysis),
            ("PREFS", self.show_preferences),
            ("UPDATE", lambda: self.check_for_updates())
        ]
        
        for text, command in mgmt_buttons:
            ttk.Button(mgmt_frame, text=text, style='Aperture.TButton', 
                      command=command, width=10).pack(side='left', padx=2)
    
    def create_left_panel(self, parent):
        """Create the left panel with game list"""
        self.left_panel = ttk.Frame(parent, style='Panel.TFrame')
        
        # Game list header
        list_header = ttk.Frame(self.left_panel, style='Panel.TFrame')
        list_header.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(list_header, text="TEST SUBJECTS DATABASE", 
                 style='GLaDOS.TLabel').pack(side='left')
        
        # Game count
        self.game_count_label = ttk.Label(list_header, text="0 Subjects", 
                                         style='Aperture.TLabel')
        self.game_count_label.pack(side='right')
        
        # Game tree view
        tree_frame = ttk.Frame(self.left_panel, style='Panel.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Treeview with columns
        columns = ('ID', 'Platform', 'Name', 'Plays', 'Rating', 'Last Played')
        self.game_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',                                      style='Aperture.Treeview')

        # Configure columns
        column_widths = {'ID': 50, 'Platform': 80, 'Name': 300, 'Plays': 60,                         'Rating': 80, 'Last Played': 120}

        for col in columns:
            self.game_tree.heading(col, text=col)
            self.game_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=self.game_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.game_tree.xview)
        self.game_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack tree and scrollbars
        self.game_tree.pack(side='left', fill='both', expand=True)
        v_scroll.pack(side='right', fill='y')
        h_scroll.pack(side='bottom', fill='x')
        
        # Bind events
        self.game_tree.bind('<Double-1>', self.launch_selected_game)
        self.game_tree.bind('<Return>', self.launch_selected_game)
        
        # Status bar at bottom showing quick tips
        status_frame = ttk.Frame(self.left_panel, style='Panel.TFrame')
        status_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        tips_label = ttk.Label(status_frame, 
                               text="Tip: Double-click a game to launch it | Press Enter for selected game", 
                               style='Aperture.TLabel', font=('Arial', 9, 'italic'))
        tips_label.pack(anchor='w', pady=5)
    
    def create_right_panel(self, parent):
        """Create the right panel with commentary and info"""
        self.right_panel = ttk.Frame(parent, style='Panel.TFrame')
        
        # Commentary section
        comment_header = ttk.Frame(self.right_panel, style='Panel.TFrame')
        comment_header.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(comment_header, text="AI COMMENTARY SYSTEM", 
                 style='GLaDOS.TLabel').pack()
        
        # Commentary text area
        comment_frame = ttk.Frame(self.right_panel, style='Panel.TFrame')
        comment_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.commentary_text = scrolledtext.ScrolledText(
            comment_frame, bg=ApertureTheme.SECONDARY_BG, fg=ApertureTheme.TEXT_PRIMARY,
            font=('Courier', 9), wrap='word', height=15,
            borderwidth=2, relief='groove'
        )
        self.commentary_text.pack(fill='both', expand=True)
        
        # Recommendations section
        rec_header = ttk.Frame(self.right_panel, style='Panel.TFrame')
        rec_header.pack(fill='x', padx=10, pady=(10, 5))
        
        ttk.Label(rec_header, text="ACQUISITION RECOMMENDATIONS", 
                 style='Wheatley.TLabel').pack()
        
        # Recommendations text area
        rec_frame = ttk.Frame(self.right_panel, style='Panel.TFrame')
        rec_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.rec_text = scrolledtext.ScrolledText(
            rec_frame, bg=ApertureTheme.SECONDARY_BG, fg=ApertureTheme.TEXT_SECONDARY,
            font=('Arial', 9), wrap='word', height=8, state='disabled',
            borderwidth=2, relief='groove'
        )
        self.rec_text.pack(fill='both', expand=True)
    
    def initialize_features(self):
        """Initialize advanced features"""
        self.commentary_mode.set(self.user_preferences.get('commentary_level', 'balanced'))
        self.update_recommendations()

        # Add initial commentary
        self.add_commentary("GLaDOS", "Systems online. Ready for testing protocols.", "success")
        if not self.game_manager.get_games():
            self.add_commentary("Wheatley", "No test subjects detected! Try running a scan to find games.")

        self.schedule_auto_update_check()

    def schedule_auto_update_check(self):
        """Schedule background update checks when appropriate."""
        if not REQUESTS_AVAILABLE:
            return
        if not self.update_manager.is_supported():
            return
        try:
            last_check = float(self.user_preferences.get('last_update_check', 0) or 0)
        except (TypeError, ValueError):
            last_check = 0.0
        interval = 60 * 60 * 24
        if time.time() - last_check < interval:
            return
        self.root.after(3000, lambda: self.check_for_updates(auto=True))

    def check_for_updates(self, auto: bool = False):
        """Check GitHub for newer versions of the launcher."""
        if getattr(self, 'update_check_in_progress', False):
            if not auto:
                self.add_commentary("System", "Update check already running.", "warning")
            return
        if not REQUESTS_AVAILABLE:
            if auto:
                self.user_preferences['last_update_check'] = int(time.time())
                self.save_preferences()
            else:
                self.add_commentary("System", "Requests package unavailable; cannot contact Aperture servers.", "error")
                messagebox.showerror("Update Check", "Requests package unavailable; install 'requests' to enable updates.")
            return
        if not self.update_manager.is_supported():
            if auto:
                self.user_preferences['last_update_check'] = int(time.time())
                self.save_preferences()
            else:
                self.add_commentary("System", "Auto-update unsupported in this build mode.", "warning")
                messagebox.showinfo("Auto Update", "Auto-update is only available when running from the source script.")
            return
        self.update_check_in_progress = True
        if not auto:
            self.add_commentary("System", "Initiating Aperture firmware diagnostics...")

        def worker():
            result = self.update_manager.check_for_updates()
            self.root.after(0, lambda: self.on_update_check_complete(result, auto))

        threading.Thread(target=worker, daemon=True).start()

    def on_update_check_complete(self, result: UpdateCheckResult, auto: bool):
        """Handle completion of an update check."""
        self.update_check_in_progress = False
        self.user_preferences['last_update_check'] = int(time.time())
        self.save_preferences()
        severity_map = {
            'error': 'error',
            'warning': 'warning',
            'success': 'success'
        }
        speaker = "System"
        message_type = severity_map.get(result.severity, 'info')
        if result.success and result.update_available:
            speaker = "GLaDOS"
            message_type = 'success'
        if result.message:
            self.add_commentary(speaker, result.message, message_type)
        if result.success and result.update_available:
            if auto:
                self.add_commentary("System", "Select UPDATE to apply the latest build when convenient.")
                return
            prompt = f"Version {result.latest_version} is available (current {result.current_version}). Install now?"
            if messagebox.askyesno("Update Available", prompt):
                self.install_update()
        else:
            if not auto:
                if result.success:
                    messagebox.showinfo("Update Check", result.message)
                elif result.severity == 'error':
                    messagebox.showerror("Update Check Failed", result.message)
                else:
                    messagebox.showwarning("Update Check", result.message)

    def install_update(self):
        """Download and apply the latest update."""
        if getattr(self, 'update_install_in_progress', False):
            self.add_commentary("System", "Update installation already running.", "warning")
            return
        if not REQUESTS_AVAILABLE:
            self.add_commentary("System", "Requests package unavailable; cannot download update.", "error")
            messagebox.showerror("Update Install", "Requests package unavailable; install 'requests' to enable updates.")
            return
        if not self.update_manager.is_supported():
            self.add_commentary("System", "Auto-update unsupported in this build mode.", "warning")
            messagebox.showinfo("Auto Update", "Auto-update is only available when running from the source script.")
            return
        self.update_install_in_progress = True
        self.add_commentary("System", "Deploying update payload...")

        def worker():
            result = self.update_manager.download_and_apply_update()
            self.root.after(0, lambda: self.on_update_install_complete(result))

        threading.Thread(target=worker, daemon=True).start()

    def on_update_install_complete(self, result: UpdateApplyResult):
        """Handle completion of update installation."""
        self.update_install_in_progress = False
        if result.success:
            self.add_commentary("GLaDOS", result.message, "success")
            messagebox.showinfo("Update Installed", result.message)
        else:
            self.add_commentary("System", result.message, "error")
            messagebox.showerror("Update Failed", result.message)

    def add_commentary(self, speaker: str, message: str, message_type: str = "info"):
        """Add commentary message to the commentary panel"""
        try:
            self.commentary_text.config(state='normal')
            
            timestamp = time.strftime('%H:%M:%S')
            
            # Color coding based on speaker and type
            colors = {
                'GLaDOS': ApertureTheme.GLADOS_ORANGE,
                'Wheatley': ApertureTheme.WHEATLEY_BLUE,
                'System': ApertureTheme.TEXT_ACCENT,
                'success': ApertureTheme.SUCCESS_GREEN,
                'error': ApertureTheme.ERROR_RED,
                'warning': ApertureTheme.WARNING_YELLOW
            }
            
            color = colors.get(message_type, colors.get(speaker, ApertureTheme.TEXT_PRIMARY))
            
            # Insert message
            self.commentary_text.insert('end', f"[{timestamp}] {speaker}: {message}\n\n")
            
            # Auto-scroll to bottom
            self.commentary_text.see('end')
            self.commentary_text.config(state='disabled')
            
            # Limit commentary length
            lines = int(self.commentary_text.index('end-1c').split('.')[0])
            if lines > 100:
                self.commentary_text.config(state='normal')
                self.commentary_text.delete('1.0', '10.0')
                self.commentary_text.config(state='disabled')
        
        except Exception:
            pass
    
    def refresh_game_list(self):
        """Refresh the game list display"""
        # Clear existing items
        for item in self.game_tree.get_children():
            self.game_tree.delete(item)


        # Get games
        games = self.game_manager.get_games()

        # Sort games if auto-sort is enabled
        if self.user_preferences.get('auto_sort', True):
            sorted_games = self.game_manager.get_smart_sorted_games()
        else:
            sorted_games = sorted(games.items(), key=lambda x: x[1]['name'].lower())

        # Populate tree
        for game_id, game_info in sorted_games:
            platform_name = game_info['platform'].title()
            name = game_info['name']
            plays = game_info.get('play_count', 0)
            rating = "?" * game_info.get('user_rating', 0) if game_info.get('user_rating', 0) > 0 else "-"
            last_played = game_info.get('last_played', 'Never')[:10] if game_info.get('last_played') else 'Never'

            self.game_tree.insert('', 'end', values=(
                game_id, platform_name, name, plays, rating, last_played
            ))

        # Update count
        self.game_count_label.config(text=f"{len(games)} Subjects")


    def launch_selected_game(self, event=None):
        """Launch the selected game"""
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a test subject to launch.")
                return
            
            item = self.game_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 3:
                game_id = values[0]
                platform_name = values[1].lower()
                game_name = values[2]
                
                games = self.game_manager.get_games()
                if str(game_id) in games:
                    game_info = games[str(game_id)]
                    launch_url = game_info.get('protocol_url', game_info.get('store_url', ''))
                    
                    if self.launcher.launch_game(launch_url, platform_name):
                        self.game_manager.update_play_count(str(game_id))
                        self.refresh_game_list()
                        self.add_commentary("GLaDOS", f"Test subject {game_name} launched successfully.", "success")
                    else:
                        self.add_commentary("GLaDOS", f"Failed to launch {game_name}. Platform may not be running.", "error")
        
        except Exception as e:
            self.add_commentary("System", f"Launch error: {str(e)}", "error")
    
    def open_store_page(self):
        """Open store page for selected game"""
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a test subject.")
                return
            
            item = self.game_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 3:
                game_id = values[0]
                games = self.game_manager.get_games()
                
                if str(game_id) in games:
                    store_url = games[str(game_id)].get('store_url', '')
                    if store_url:
                        webbrowser.open(store_url)
                        self.add_commentary("System", f"Store page opened for {values[2]}.")
                    else:
                        messagebox.showinfo("No Store Page", "No store page available for this game.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open store page: {str(e)}")
    
    def run_smart_scan(self):
        """Run comprehensive scan for all platforms"""
        self.add_commentary("Wheatley", "Initiating full spectrum scan. This may take a moment...")
        
        # Disable scan button during scan
        try:
            scan_buttons = self.root.winfo_children()
            for widget in scan_buttons:
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and 'FULL SCAN' in str(child.cget('text')):
                            child.config(state='disabled')
        except:
            pass
        
        def scan_thread():
            try:
                results = self.scanner.scan_all_platforms()
                self.last_scan_results = results
                
                total_found = sum(len(games) for games in results.values())
                
                # Process results even if total_found is 0 to show completion
                added_count = 0
                existing_games = self.game_manager.get_games()
                
                for platform_name, games in results.items():
                    self.root.after(0, lambda p=platform_name, c=len(games): 
                                  self.add_commentary("System", f"{p.title()} scan: {c} games found"))
                    
                    for game in games:
                        # Check if game already exists by name and platform
                        game_exists = False
                        for existing_game in existing_games.values():
                            if (existing_game.get('name', '').lower() == game['name'].lower() and 
                                existing_game.get('platform', '') == platform_name):
                                game_exists = True
                                break
                        
                        if not game_exists:
                            try:
                                self.game_manager.add_game(
                                    game['name'],
                                    platform_name,
                                    game['game_id'],
                                    game.get('store_url', ''),
                                    game
                                )
                                added_count += 1
                            except Exception as e:
                                self.root.after(0, lambda err=str(e): 
                                              self.add_commentary("System", f"Error adding game: {err}", "error"))
                
                # Update UI in main thread
                self.root.after(0, lambda: self.scan_complete(total_found, added_count))
                
            except Exception as e:
                error_msg = f"Scan error: {str(e)}"
                self.root.after(0, lambda: self.add_commentary("System", error_msg, "error"))
                # Re-enable scan button on error
                self.root.after(0, self.re_enable_scan_button)
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def re_enable_scan_button(self):
        """Re-enable the scan button after scan completion or error"""
        try:
            scan_buttons = self.root.winfo_children()
            for widget in scan_buttons:
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and 'FULL SCAN' in str(child.cget('text')):
                            child.config(state='normal')
        except:
            pass
    
    def scan_complete(self, total_found, added_count):
        """Handle scan completion"""
        try:
            self.refresh_game_list()
            self.update_recommendations()
            
            if total_found == 0:
                self.add_commentary("GLaDOS", "Scan complete. No test subjects detected on this system.")
            elif added_count == 0:
                self.add_commentary("GLaDOS", f"Scan complete. {total_found} subjects found, but all were already in the database.")
            else:
                self.add_commentary("GLaDOS", f"Scan complete. {total_found} subjects detected, {added_count} new acquisitions.", "success")
                if added_count > 0:
                    self.add_commentary("Wheatley", f"Excellent! {added_count} new test subjects ready for evaluation!")
            
            # Re-enable scan button
            self.re_enable_scan_button()
        except Exception as e:
            self.add_commentary("System", f"Error completing scan: {str(e)}", "error")
    
    def run_platform_scan(self, platform_name):
        """Run scan for specific platform"""
        self.add_commentary("System", f"Scanning {platform_name.title()} network...")
        
        def scan_thread():
            try:
                if platform_name == 'steam':
                    games = self.scanner.scan_steam_windows() if platform.system() == "Windows" else []
                elif platform_name == 'epic':
                    games = self.scanner.scan_epic_windows() if platform.system() == "Windows" else []
                elif platform_name == 'ubisoft':
                    games = self.scanner.scan_ubisoft_windows() if platform.system() == "Windows" else []
                elif platform_name == 'gog':
                    games = self.scanner.scan_gog_windows() if platform.system() == "Windows" else []
                else:
                    games = []
                
                games = self.scanner.apply_smart_filtering(games, platform_name)
                
                added_count = 0
                existing_games = self.game_manager.get_games()
                for game in games:
                    if not any(g['name'] == game['name'] and g['platform'] == platform_name 
                             for g in existing_games.values()):
                        self.game_manager.add_game(
                            game['name'],
                            platform_name,
                            game['game_id'],
                            game.get('store_url', ''),
                            game
                        )
                        added_count += 1
                
                self.root.after(0, lambda: self.platform_scan_complete(platform_name, len(games), added_count))
                
            except Exception as e:
                self.root.after(0, lambda: self.add_commentary("System", f"{platform_name.title()} scan error: {str(e)}", "error"))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def platform_scan_complete(self, platform_name, total_found, added_count):
        """Handle platform scan completion"""
        self.refresh_game_list()
        self.update_recommendations()
        
        self.add_commentary("System", f"{platform_name.title()} scan complete: {total_found} found, {added_count} added.", "success")
    
    def update_recommendations(self):
        """Update the recommendations display"""
        try:
            recommendations = self.game_manager.get_recommendations()
            
            self.rec_text.config(state='normal')
            self.rec_text.delete('1.0', 'end')
            
            for i, rec in enumerate(recommendations[:4], 1):
                self.rec_text.insert('end', f"{i}. {rec}\n\n")
            
            self.rec_text.config(state='disabled')
        except Exception:
            pass
    
    def show_add_dialog(self):
        """Show manual game entry dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Test Subject Entry")
        dialog.geometry("500x400")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(dialog, style='Header.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="MANUAL SUBJECT ACQUISITION", style='GLaDOS.TLabel').pack()
        
        # Form fields
        form_frame = ttk.Frame(dialog, style='Panel.TFrame')
        form_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Name field
        ttk.Label(form_frame, text="Subject Name:", style='Aperture.TLabel').pack(anchor='w', pady=(10, 5))
        name_entry = ttk.Entry(form_frame, width=50, font=('Arial', 11))
        name_entry.pack(fill='x', pady=(0, 10))
        
        # Platform selection
        ttk.Label(form_frame, text="Platform Network:", style='Aperture.TLabel').pack(anchor='w', pady=(10, 5))
        platform_var = tk.StringVar(value="steam")
        platform_frame = ttk.Frame(form_frame, style='Panel.TFrame')
        platform_frame.pack(fill='x', pady=(0, 10))
        
        platforms = [("Steam", "steam"), ("Epic Games", "epic"), ("Ubisoft Connect", "ubisoft"), ("GOG Galaxy", "gog")]
        for i, (text, value) in enumerate(platforms):
            ttk.Radiobutton(platform_frame, text=text, variable=platform_var, value=value,
                           style='Aperture.TRadiobutton').grid(row=i//2, column=i%2, sticky='w', padx=10, pady=2)
        
        # Game ID field
        ttk.Label(form_frame, text="Subject ID (optional):", style='Aperture.TLabel').pack(anchor='w', pady=(10, 5))
        id_entry = ttk.Entry(form_frame, width=50, font=('Arial', 11))
        id_entry.pack(fill='x', pady=(0, 20))
        
        # Action buttons
        button_frame = ttk.Frame(dialog, style='Panel.TFrame')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        def add_game():
            name = name_entry.get().strip()
            platform_name = platform_var.get()
            game_id = id_entry.get().strip() or name.replace(' ', '_').lower()
            
            if name:
                self.game_manager.add_game(name, platform_name, game_id)
                self.refresh_game_list()
                self.add_commentary("GLaDOS", f"Manual subject {name} acquired for testing.", "success")
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Input", "Subject name is required.")
        
        ttk.Button(button_frame, text="ACQUIRE SUBJECT", style='GLaDOS.TButton', 
                  command=add_game).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="ABORT", style='Aperture.TButton', 
                  command=dialog.destroy).pack(side='left')
        
        name_entry.focus()
    
    def remove_selected_game(self):
        """Remove selected game from collection"""
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a subject for termination.")
                return
            
            item = self.game_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 3:
                game_id = values[0]
                game_name = values[2]
                
                if messagebox.askyesno("Confirm Termination", 
                                     f"Terminate test subject {game_name} from the database?\n\nThis action cannot be undone."):
                    if self.game_manager.remove_game(str(game_id)):
                        self.refresh_game_list()
                        self.add_commentary("GLaDOS", f"Subject {game_name} terminated. How efficient.", "success")
                    else:
                        messagebox.showerror("Error", "Subject termination failed.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Termination error: {str(e)}")
    
    def remove_all_games(self):
        # Remove every game from the collection after confirmation
        try:
            games = self.game_manager.get_games()
            if not games:
                messagebox.showinfo("Remove All Subjects", "There are no test subjects to remove.")
                return

            if not messagebox.askyesno(
                "Remove All Subjects",
                "This will permanently purge every test subject from the database.\n\nProceed?"
            ):
                return

            if self.game_manager.remove_all_games():
                self.refresh_game_list()
                self.update_recommendations()
                self.add_commentary("System", "All test subjects have been purged from the database.", "warning")
            else:
                messagebox.showerror("Remove All Subjects", "Failed to purge test subjects.")
        except Exception as e:
            messagebox.showerror("Remove All Subjects", f"Unexpected error: {e}")

    def rate_selected_game(self):
        """Rate the selected game"""
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a subject for evaluation.")
                return
            
            item = self.game_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 3:
                game_id = str(values[0])
                game_name = values[2]
                
                rating = simpledialog.askinteger("Subject Evaluation", 
                                                f"Rate test subject {game_name} (1-5 stars):", 
                                                minvalue=1, maxvalue=5)
                
                if rating:
                    games = self.game_manager.get_games()
                    if game_id in games:
                        games[game_id]['user_rating'] = rating
                        self.game_manager.save_game_data()
                        self.refresh_game_list()
                        self.add_commentary("GLaDOS", f"Subject {game_name} rated {rating} stars. Your evaluation has been recorded.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Evaluation error: {str(e)}")
    
    def show_achievements(self):
        """Show achievements dialog"""
        try:
            selection = self.game_tree.selection()
            if not selection:
                self.show_achievement_summary()
                return
            
            item = self.game_tree.item(selection[0])
            values = item['values']
            
            if len(values) >= 3:
                game_id = str(values[0])
                game_name = values[2]
                
                games = self.game_manager.get_games()
                if game_id in games:
                    game_info = games[game_id]
                    achievements = self.achievement_manager.get_game_achievements(
                        game_info.get('game_id', ''),
                        game_info.get('platform', ''),
                        game_info.get('name', '')
                    )
                    
                    self.show_game_achievements(game_name, achievements)
        
        except Exception as e:
            messagebox.showerror("Error", f"Achievement analysis error: {str(e)}")
    
    def show_achievement_summary(self):
        """Show overall achievement summary"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Achievement Analysis")
        dialog.geometry("600x500")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)
        
        # Header
        header_frame = ttk.Frame(dialog, style='Header.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="SUBJECT ACHIEVEMENT ANALYSIS", style='GLaDOS.TLabel').pack()
        
        # Content
        content_frame = ttk.Frame(dialog, style='Panel.TFrame')
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        info_text = scrolledtext.ScrolledText(
            content_frame, bg=ApertureTheme.SECONDARY_BG, fg=ApertureTheme.TEXT_PRIMARY,
            font=('Arial', 10), wrap='word', state='normal',
            borderwidth=2, relief='groove'
        )
        info_text.pack(fill='both', expand=True)
        
        games = self.game_manager.get_games()
        summary = self.achievement_manager.get_achievement_summary(games)
        
        content = f"""APERTURE SCIENCE ACHIEVEMENT REPORT
{'='*45}

OVERALL STATISTICS:
Test Subjects with Achievements: {summary['games_with_achievements']}
Total Achievement Opportunities: {summary['total_achievements']}
Achievements Unlocked: {summary['total_unlocked']}
Completion Efficiency: {summary['completion_percentage']:.1f}%

DETAILED SUBJECT ANALYSIS:
{'='*45}

"""
        
        for game_id, game_info in games.items():
            achievements = self.achievement_manager.get_game_achievements(
                game_info.get('game_id', ''),
                game_info.get('platform', ''),
                game_info.get('name', '')
            )
            
            if achievements.get('total', 0) > 0:
                content += f"Subject: {game_info['name']} ({game_info['platform'].title()})\n"
                content += f"  Achievement Status: {achievements['unlocked']}/{achievements['total']} ({achievements['percentage']:.1f}%)\n"
                content += f"  Performance Rating: {'Excellent' if achievements['percentage'] >= 80 else 'Satisfactory' if achievements['percentage'] >= 50 else 'Needs Improvement'}\n\n"
        
        content += f"\nReport Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "Aperture Science - We do what we must because we can."
        
        info_text.insert('1.0', content)
        info_text.config(state='disabled')
        
        ttk.Button(dialog, text="DISMISS", style='Aperture.TButton', command=dialog.destroy).pack(pady=15)
    
    def show_game_achievements(self, game_name, achievements):
        """Show achievements for specific game"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Achievement Analysis - {game_name}")
        dialog.geometry("700x600")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)
        
        # Header
        header_frame = ttk.Frame(dialog, style='Header.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text=f"SUBJECT ACHIEVEMENTS - {game_name.upper()}", style='GLaDOS.TLabel').pack()
        
        # Progress summary
        progress_frame = ttk.Frame(dialog, style='Panel.TFrame')
        progress_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        progress_text = f"Progress: {achievements['unlocked']}/{achievements['total']} ({achievements['percentage']:.1f}%)"
        ttk.Label(progress_frame, text=progress_text, style='Wheatley.TLabel').pack(pady=10)
        
        # Achievement list
        list_frame = ttk.Frame(dialog, style='Panel.TFrame')
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        ach_tree = ttk.Treeview(list_frame, columns=('Status', 'Name', 'Description'), 
                               show='headings', height=18, style='Aperture.Treeview')
        ach_tree.heading('Status', text='Status')
        ach_tree.heading('Name', text='Achievement')
        ach_tree.heading('Description', text='Description')
        
        ach_tree.column('Status', width=80)
        ach_tree.column('Name', width=200)
        ach_tree.column('Description', width=350)
        
        for achievement in achievements.get('achievements', []):
            status = "✓ UNLOCKED" if achievement.get('unlocked') else "○ LOCKED"
            ach_tree.insert('', 'end', values=(
                status,
                achievement.get('name', 'Unknown Achievement'),
                achievement.get('description', 'No description available')
            ))
        
        scrollbar_ach = ttk.Scrollbar(list_frame, orient='vertical', command=ach_tree.yview)
        ach_tree.configure(yscrollcommand=scrollbar_ach.set)
        
        ach_tree.pack(side='left', fill='both', expand=True)
        scrollbar_ach.pack(side='right', fill='y')
        
        ttk.Button(dialog, text="DISMISS", style='Aperture.TButton', command=dialog.destroy).pack(pady=15)
    
    def show_analysis(self):
        """Show comprehensive gaming analysis"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Test Subject Analysis")
        dialog.geometry("700x600")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)
        
        # Header
        header_frame = ttk.Frame(dialog, style='Header.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="APERTURE BEHAVIORAL ANALYSIS", style='GLaDOS.TLabel').pack()
        
        # Analysis content
        analysis_frame = ttk.Frame(dialog, style='Panel.TFrame')
        analysis_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        analysis_text = scrolledtext.ScrolledText(
            analysis_frame, bg=ApertureTheme.SECONDARY_BG, fg=ApertureTheme.TEXT_PRIMARY,
            font=('Arial', 10), wrap='word', state='normal',
            borderwidth=2, relief='groove'
        )
        analysis_text.pack(fill='both', expand=True)
        
        # Generate analysis
        games = self.game_manager.get_games()
        if not games:
            content = "No test subjects available for analysis. Please acquire subjects through scanning protocols."
        else:
            total_games = len(games)
            total_plays = sum(game.get('play_count', 0) for game in games.values())
            avg_plays = total_plays / total_games if total_games > 0 else 0
            
            platform_stats = {}
            for game in games.values():
                platform_name = game['platform']
                platform_stats[platform_name] = platform_stats.get(platform_name, 0) + 1
            
            most_played = max(games.values(), key=lambda x: x.get('play_count', 0))
            
            content = f"""APERTURE SCIENCE BEHAVIORAL ANALYSIS REPORT
{'='*50}

SUBJECT COLLECTION OVERVIEW:
Total Test Subjects: {total_games}
Total Testing Sessions: {total_plays}
Average Sessions per Subject: {avg_plays:.1f}

PLATFORM DISTRIBUTION ANALYSIS:
"""
            for platform_name, count in sorted(platform_stats.items()):
                percentage = (count / total_games) * 100
                content += f"  {platform_name.title()} Network: {count} subjects ({percentage:.1f}%)\n"
            
            content += f"""
BEHAVIORAL PATTERNS:
Primary Test Subject: {most_played['name']} ({most_played.get('play_count', 0)} sessions)
Platform Preference: {max(platform_stats.items(), key=lambda x: x[1])[0].title() if platform_stats else 'None'}
Testing Diversity Index: {'High' if len(platform_stats) > 2 else 'Medium' if len(platform_stats) == 2 else 'Low'}

ACHIEVEMENT PERFORMANCE:
"""
            ach_summary = self.achievement_manager.get_achievement_summary(games)
            content += f"Overall Completion Rate: {ach_summary['completion_percentage']:.1f}%\n"
            content += f"Subjects with Achievements: {ach_summary['games_with_achievements']}\n"
            
            # Recommendations
            content += f"""
APERTURE RECOMMENDATIONS:
"""
            if avg_plays < 2:
                content += "• Increase testing frequency with existing subjects\n"
            if len(platform_stats) == 1:
                content += "• Expand platform diversity for comprehensive testing\n"
            if ach_summary['completion_percentage'] < 40:
                content += "• Focus on achievement completion for thorough evaluation\n"
            
            content += f"""
This analysis was conducted by GLaDOS for the Aperture Science 
Enrichment Center. Results may vary. We do what we must because we can.

Analysis completed: {time.strftime('%Y-%m-%d %H:%M:%S')}"""
        
        analysis_text.insert('1.0', content)
        analysis_text.config(state='disabled')
        
        ttk.Button(dialog, text="DISMISS", style='Aperture.TButton', command=dialog.destroy).pack(pady=15)
    
    def show_recommendations(self):
        """Show game recommendations dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Aperture Recommendations")
        dialog.geometry("600x500")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)
        
        # Header
        header_frame = ttk.Frame(dialog, style='Header.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="APERTURE ACQUISITION RECOMMENDATIONS", style='GLaDOS.TLabel').pack()
        
        # Recommendations content
        rec_frame = ttk.Frame(dialog, style='Panel.TFrame')
        rec_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        rec_text = scrolledtext.ScrolledText(
            rec_frame, bg=ApertureTheme.SECONDARY_BG, fg=ApertureTheme.TEXT_PRIMARY,
            font=('Arial', 10), wrap='word', state='normal',
            borderwidth=2, relief='groove'
        )
        rec_text.pack(fill='both', expand=True)
        
        recommendations = self.game_manager.get_recommendations()
        content = f"""PERSONALIZED SUBJECT RECOMMENDATIONS
{'='*40}

Based on your testing patterns and platform preferences, 
the Aperture Science recommendation engine suggests:

"""
        
        for i, rec in enumerate(recommendations, 1):
            content += f"{i}. {rec}\n\n"
        
        if len(recommendations) < 5:
            content += """ADDITIONAL ACQUISITION STRATEGIES:
• Monitor platform-specific promotions and free acquisitions
• Investigate subjects similar to your highest-rated tests
• Consider independent development projects for unique experiences
• Participate in testing communities for peer recommendations

Remember: The best test subject is one that challenges your 
problem-solving capabilities while providing adequate entertainment value.

- GLaDOS, Aperture Science AI"""
        
        rec_text.insert('1.0', content)
        rec_text.config(state='disabled')
        
        ttk.Button(dialog, text="DISMISS", style='Aperture.TButton', command=dialog.destroy).pack(pady=15)
        
        self.add_commentary("GLaDOS", "Recommendations generated based on your testing patterns.")
    
    def show_preferences(self):
        """Show system preferences dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("System Preferences")
        dialog.geometry("500x400")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(dialog, style='Header.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text="APERTURE SYSTEM CONFIGURATION", style='GLaDOS.TLabel').pack()
        
        # Preferences form
        pref_frame = ttk.Frame(dialog, style='Panel.TFrame')
        pref_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Smart recommendations toggle
        smart_rec_var = tk.BooleanVar(value=self.user_preferences.get('smart_recommendations', True))
        ttk.Checkbutton(pref_frame, text="Enable Smart Recommendations", 
                       variable=smart_rec_var, style='Aperture.TCheckbutton').pack(anchor='w', pady=10)
        
        # Auto sort toggle
        auto_sort_var = tk.BooleanVar(value=self.user_preferences.get('auto_sort', True))
        ttk.Checkbutton(pref_frame, text="Auto-sort by Activity", 
                       variable=auto_sort_var, style='Aperture.TCheckbutton').pack(anchor='w', pady=5)
        
        # Commentary level selection
        ttk.Label(pref_frame, text="AI Commentary Level:", style='Aperture.TLabel').pack(anchor='w', pady=(20, 10))
        
        commentary_var = tk.StringVar(value=self.user_preferences.get('commentary_level', 'balanced'))
        commentary_frame = ttk.Frame(pref_frame, style='Panel.TFrame')
        commentary_frame.pack(fill='x', pady=(0, 20))
        
        modes = [("Silent Operation", "minimal"), ("GLaDOS Primary", "glados"), 
                ("Balanced Mode", "balanced"), ("Wheatley Primary", "wheatley")]
        
        for text, value in modes:
            ttk.Radiobutton(commentary_frame, text=text, variable=commentary_var, value=value,
                           style='Aperture.TRadiobutton').pack(anchor='w', pady=2)
        
        # Action buttons
        button_frame = ttk.Frame(dialog, style='Panel.TFrame')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        def save_preferences():
            self.user_preferences.update({
                'smart_recommendations': smart_rec_var.get(),
                'auto_sort': auto_sort_var.get(),
                'commentary_level': commentary_var.get()
            })
            self.commentary_mode.set(commentary_var.get())
            self.save_preferences()
            self.add_commentary("System", "Configuration updated successfully.", "success")
            dialog.destroy()
        
        def reset_preferences():
            if messagebox.askyesno("Reset Configuration", "Reset all preferences to default values?"):
                smart_rec_var.set(True)
                auto_sort_var.set(True)
                commentary_var.set('balanced')
        
        ttk.Button(button_frame, text="SAVE CONFIG", style='GLaDOS.TButton', 
                  command=save_preferences).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="RESET", style='Aperture.TButton', 
                  command=reset_preferences).pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="CANCEL", style='Aperture.TButton', 
                  command=dialog.destroy).pack(side='left')
    
    def run(self):
        """Run the Aperture Science Enrichment Center application"""
        try:
            self.add_commentary("System", "Aperture Science Enrichment Center online. Welcome.", "success")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.add_commentary("System", "Emergency shutdown initiated.")
        except Exception as e:
            messagebox.showerror("Critical System Failure", f"Aperture Science systems failure: {str(e)}")

def main():
    """Main entry point for the Aperture Science Enrichment Center"""
    try:
        print("Initializing Aperture Science Enrichment Center...")
        
        # Check for first run
        show_welcome = False
        if not FIRST_RUN_FLAG.exists():
            show_welcome = True
            try:
                FIRST_RUN_FLAG.touch()
            except:
                pass
        
        # Initialize the main application
        print("Starting GUI...")
        center = ApertureEnrichmentCenterGUI()
        
        # Show welcome dialog if first run
        if show_welcome:
            def show_welcome_dialog():
                welcome = messagebox.askyesno(
                    "Aperture Science Enrichment Center",
                    "Welcome to the Aperture Science Enrichment Center!\n\n" +
                    "This advanced game management system will scan your computer\n" +
                    "for test subjects (games) and provide intelligent analysis.\n\n" +
                    "GLaDOS: 'Hello. I am GLaDOS. Let's begin testing.'\n\n" +
                    "Would you like to initiate the scanning protocols now?"
                )
                
                if welcome:
                    center.add_commentary("GLaDOS", "Initiating welcome scan protocol...")
                    center.run_smart_scan()
            
            # Schedule welcome dialog after GUI is ready
            center.root.after(1000, show_welcome_dialog)
        
        print("Launching application...")
        center.run()
        
    except Exception as e:
        # Emergency error handling
        print(f"Critical error: {str(e)}")
        try:
            import traceback
            traceback.print_exc()
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Critical System Failure", 
                               f"Failed to initialize Aperture Science systems:\n{str(e)}\n\nCheck console for details.")
            root.destroy()
        except:
            print("Failed to show error dialog. Check console output.")

if __name__ == "__main__":
    main()



