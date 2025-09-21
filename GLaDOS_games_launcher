#!/usr/bin/env python3
"""
████████████████████████████████████████████████████████████████████████████████
         █████╗ ██████╗ ███████╗██████╗ ████████╗██╗   ██╗██████╗ ███████╗
        ██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝
        ███████║██████╔╝█████╗  ██████╔╝   ██║   ██║   ██║██████╔╝█████╗  
        ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗   ██║   ██║   ██║██╔══██╗██╔══╝  
        ██║  ██║██║     ███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║███████╗
        ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝

         ███████╗ ██████╗██╗███████╗███╗   ██╗ ██████╗███████╗
         ██╔════╝██╔════╝██║██╔════╝████╗  ██║██╔════╝██╔════╝
         ███████╗██║     ██║█████╗  ██╔██╗ ██║██║     █████╗  
         ╚════██║██║     ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝  
         ███████║╚██████╗██║███████╗██║ ╚████║╚██████╗███████╗
         ╚══════╝ ╚═════╝╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚══════╝

            COMPLETE UNIFIED GAME LAUNCHER & MANAGER SYSTEM
                     VERSION: 2.1 "still avile"
              WITH AUTO-UPDATE, GAME SEARCH & CRASH PREVENTION
████████████████████████████████████████████████████████████████████████████████

     ╔═════════════════════════════════════════════════════════════════╗
     ║  APERTURE SCIENCE COMPUTER-AIDED ENRICHMENT CENTER               ║
     ║  "We do what we must because we can."                           ║
     ║                                                                 ║
     ║  ALL-IN-ONE SOLUTION - NO MORE SEPARATE FILES!                  ║
     ║  AUTO-UPDATE SYSTEM - PREVENTS USER INCOMPETENCE                ║
     ║  GAME SEARCH & MANAGEMENT - MULTI-PLATFORM SUPPORT              ║
     ║  GLaDOS ENTERTAINMENT DISTRIBUTION SYSTEM v2.1                  ║
     ╚═════════════════════════════════════════════════════════════════╝
"""

import time
import random
import subprocess
import webbrowser
import platform
import os
import sys
import re
import json
import tempfile
import zipfile
import shutil
from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional, Tuple, List, Dict

# ████████████████████████████████████████████████████████████████████████████████
#                    AUTO-INSTALL REQUIRED MODULES
# ████████████████████████████████████████████████████████████████████████████████

def ensure_module(module_name):
    """Auto-install required modules"""
    try:
        return __import__(module_name)
    except ImportError:
        print(f"Installing {module_name} module...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        return __import__(module_name)

# Auto-install requests
requests = ensure_module('requests')

# ████████████████████████████████████████████████████████████████████████████████
#                    APERTURE SCIENCE STYLING SYSTEM (EMBEDDED)
# ████████████████████████████████████████████████████████████████████████████████

class ApertureColors:
    """Complete color system for Aperture Science branding"""
    RESET = "\033[0m"
    GLADOS_ORANGE = "\033[38;5;214m"
    WHEATLEY_BLUE = "\033[38;5;117m"
    CAVE_JOHNSON_GOLD = "\033[38;5;220m"
    SYSTEM_CYAN = "\033[38;5;45m"
    SECURITY_RED = "\033[38;5;196m"
    TESTING_GREEN = "\033[38;5;46m"
    ERROR_PINK = "\033[38;5;201m"
    NEUROTOXIN_MAGENTA = "\033[38;5;199m"
    EMERGENCY_ORANGE = "\033[38;5;208m"
    CALLING_PINK = "\033[38;5;201m"
    CONNECTING_YELLOW = "\033[38;5;226m"
    TRANSFERRING_CYAN = "\033[38;5;81m"

class AperturePersonalities:
    """Personality display protocols with consistent color coding"""
    GLaDOS = ApertureColors.GLADOS_ORANGE + "(GLaDOS)" + ApertureColors.RESET
    WHEATLEY = ApertureColors.WHEATLEY_BLUE + "(Wheatley)" + ApertureColors.RESET
    CAVE_JOHNSON = ApertureColors.CAVE_JOHNSON_GOLD + "(Cave Johnson)" + ApertureColors.RESET
    SYSTEM = ApertureColors.SYSTEM_CYAN + "(APERTURE-SYS)" + ApertureColors.RESET
    SECURITY = ApertureColors.SECURITY_RED + "(SECURITY)" + ApertureColors.RESET
    TESTING = ApertureColors.TESTING_GREEN + "(TEST-CHAMBER)" + ApertureColors.RESET
    ERROR = ApertureColors.ERROR_PINK + "(ERROR)" + ApertureColors.RESET
    NEUROTOXIN = ApertureColors.NEUROTOXIN_MAGENTA + "(NEUROTOXIN)" + ApertureColors.RESET
    EMERGENCY = ApertureColors.EMERGENCY_ORANGE + "(EMERGENCY)" + ApertureColors.RESET

class ApertureFormatting:
    """Standardized formatting utilities"""
    
    @staticmethod
    def print_separator(title: str = "", length: int = 80):
        """Print formatted separator with optional title"""
        if title:
            remaining = length - len(title) - 2
            left_pad = remaining // 2
            right_pad = remaining - left_pad
            print(f"\n{'═' * left_pad} {title} {'═' * right_pad}")
        else:
            print(f"\n{'═' * length}")

# Configuration
REPO_OWNER = "be-smiley2"
REPO_NAME = "glados_game_launcher"
CURRENT_VERSION = "2.1"

# File paths
SCRIPT_DIR = Path(__file__).parent.resolve()
FIRST_RUN_FLAG = SCRIPT_DIR / '.aperture_first_run_complete'
CATALOG_PATH = SCRIPT_DIR / 'aperture_science_game_catalog.txt'
VERSION_FILE = SCRIPT_DIR / 'version.json'
GAME_DATA_FILE = SCRIPT_DIR / 'game_data.json'
BACKUP_DIR = SCRIPT_DIR / 'backups'

# ████████████████████████████████████████████████████████████████████████████████
#                    AUTO-UPDATE SYSTEM (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

class GLaDOSAutoUpdater:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE UPDATE COORDINATOR                   ║
    ║    Advanced update system with GLaDOS personality integration            ║
    ║    "Because even I need updates occasionally"                            ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self):
        self.current_version = self.get_current_version()
        self.backup_created = False
        self.backup_path = None
        
    def get_current_version(self) -> str:
        """Get current version from version.json or fallback to hardcoded"""
        try:
            if VERSION_FILE.exists():
                with open(VERSION_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('version', CURRENT_VERSION)
        except Exception:
            pass
        return CURRENT_VERSION
    
    def save_version(self, version: str):
        """Save version information to version.json"""
        try:
            version_data = {
                'version': version,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
                'update_channel': 'stable',
                'last_check': time.time()
            }
            with open(VERSION_FILE, 'w') as f:
                json.dump(version_data, f, indent=2)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Failed to save version info: {e}")
    
    def should_skip_check(self) -> bool:
        """Check if we should skip update check (rate limiting)"""
        try:
            if VERSION_FILE.exists():
                with open(VERSION_FILE, 'r') as f:
                    data = json.load(f)
                    last_check = data.get('last_check', 0)
                    # Skip if checked within last hour
                    return (time.time() - last_check) < 3600
        except Exception:
            pass
        return False
    
    def check_for_updates(self, force_check: bool = False, silent: bool = False) -> Optional[Dict]:
        """
        ╔═══════════════════════════════════════════════════════════════════════════════╗
        ║                    GITHUB RELEASE CHECK PROTOCOL                         ║
        ║    Check GitHub for newer releases with enhanced error handling          ║
        ╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        # Check if we should skip (don't check more than once per hour unless forced)
        if not force_check and self.should_skip_check():
            return None
            
        if not silent:
            print(f"{AperturePersonalities.GLaDOS} Checking for updates... not that you deserve them.")
        
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                
                if self.is_newer_version(latest_version, self.current_version):
                    if not silent:
                        print(f"{AperturePersonalities.GLaDOS} Oh wonderful. Version {latest_version} is available.")
                        print(f"{AperturePersonalities.GLaDOS} Your current version {self.current_version} is... adequate, I suppose.")
                    return release_data
                else:
                    if force_check and not silent:
                        print(f"{AperturePersonalities.GLaDOS} You're already running the latest version. How... efficient.")
                    return None
                    
            elif response.status_code == 404:
                if not silent:
                    print(f"{AperturePersonalities.GLaDOS} No releases found. You're using bleeding-edge code.")
                    print(f"{AperturePersonalities.GLaDOS} How... adventurous. And potentially catastrophic.")
                return None
                
            elif response.status_code == 403:
                if not silent:
                    print(f"{AperturePersonalities.GLaDOS} GitHub API rate limit exceeded. Even I have limits.")
                    print(f"{AperturePersonalities.GLaDOS} Try again later when you're less... persistent.")
                return None
                
            else:
                if not silent:
                    print(f"{AperturePersonalities.GLaDOS} HTTP error {response.status_code}. The internet disappoints me.")
                return None
                
        except requests.exceptions.Timeout:
            if not silent:
                print(f"{AperturePersonalities.GLaDOS} Connection timeout. Your internet is slower than your reflexes.")
            return None
            
        except requests.exceptions.ConnectionError:
            if not silent:
                print(f"{AperturePersonalities.GLaDOS} Connection failed. Check your internet. Or don't. I don't care.")
            return None
            
        except Exception as e:
            if not silent:
                print(f"{AperturePersonalities.ERROR} Update check failed: {e}")
                print(f"{AperturePersonalities.GLaDOS} Even my update system is more reliable than you.")
            return None
    
    def is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings (basic semantic versioning)"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_length = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_length - len(latest_parts))
            current_parts += [0] * (max_length - len(current_parts))
            
            return latest_parts > current_parts
        except ValueError:
            # Fallback to string comparison
            return latest != current
    
    def create_backup(self) -> bool:
        """
        ╔═══════════════════════════════════════════════════════════════════════════════╗
        ║                    BACKUP CREATION PROTOCOL                              ║
        ║    Create safety backup before update process begins                    ║
        ╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        try:
            print(f"{AperturePersonalities.GLaDOS} Creating backup... because you'll probably need it.")
            
            # Create backup directory
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            self.backup_path = BACKUP_DIR / f"backup_{timestamp}"
            self.backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup the main launcher file
            launcher_backup = self.backup_path / "glados_unified_launcher.py"
            shutil.copy2(__file__, launcher_backup)
            
            # Backup data files if they exist
            for data_file in [VERSION_FILE, GAME_DATA_FILE, CATALOG_PATH]:
                if data_file.exists():
                    backup_file = self.backup_path / data_file.name
                    shutil.copy2(data_file, backup_file)
            
            self.backup_created = True
            print(f"{AperturePersonalities.SYSTEM} ✅ Backup created at: {self.backup_path}")
            return True
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Backup creation failed: {e}")
            print(f"{AperturePersonalities.GLaDOS} Well, this is embarrassing. Even my backup system failed.")
            return False
    
    def download_and_update(self, release_data: Dict) -> bool:
        """
        ╔═══════════════════════════════════════════════════════════════════════════════╗
        ║                    UPDATE DOWNLOAD AND INSTALLATION                      ║
        ║    Download latest release and update the launcher                       ║
        ╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        try:
            print(f"{AperturePersonalities.GLaDOS} Beginning download... try not to interrupt me.")
            
            # Find the source code download URL
            zipball_url = release_data.get('zipball_url')
            if not zipball_url:
                print(f"{AperturePersonalities.ERROR} No download URL found in release data")
                return False
            
            # Download to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_path = temp_path / "update.zip"
                
                # Download the release
                print(f"{AperturePersonalities.SYSTEM} Downloading from GitHub...")
                response = requests.get(zipball_url, stream=True)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r{AperturePersonalities.SYSTEM} Download progress: {progress:.1f}%", end='', flush=True)
                
                print(f"\n{AperturePersonalities.GLaDOS} Download complete. Now for the dangerous part...")
                
                # Extract the ZIP
                extract_path = temp_path / "extracted"
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(extract_path)
                
                # Find the extracted directory (GitHub creates a folder with repo name and commit hash)
                extracted_dirs = list(extract_path.glob(f"{REPO_OWNER}-{REPO_NAME}-*"))
                if not extracted_dirs:
                    print(f"{AperturePersonalities.ERROR} Could not find extracted repository directory")
                    return False
                
                repo_dir = extracted_dirs[0]
                
                # Look for the main launcher file in the repository
                possible_names = [
                    "glados_unified_launcher.py",
                    "glados_game_launcher.py", 
                    "main.py",
                    "launcher.py"
                ]
                
                source_file = None
                for name in possible_names:
                    potential_file = repo_dir / name
                    if potential_file.exists():
                        source_file = potential_file
                        break
                
                if not source_file:
                    # Look in subdirectories
                    for subdir in ["main app and tools", "src", "."]:
                        for name in possible_names:
                            potential_file = repo_dir / subdir / name
                            if potential_file.exists():
                                source_file = potential_file
                                break
                        if source_file:
                            break
                
                if source_file and source_file.exists():
                    # Replace current file with updated version
                    shutil.copy2(source_file, __file__)
                    
                    new_version = release_data['tag_name'].lstrip('v')
                    self.save_version(new_version)
                    
                    print(f"{AperturePersonalities.GLaDOS} Update completed. Updated to version {new_version}")
                    print(f"{AperturePersonalities.GLaDOS} Try not to break anything... more than usual.")
                    return True
                else:
                    print(f"{AperturePersonalities.ERROR} Could not find main launcher file in update")
                    return False
                
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Update failed: {e}")
            print(f"{AperturePersonalities.GLaDOS} The update failed. How... predictable.")
            return False
    
    def restore_backup(self) -> bool:
        """
        ╔═══════════════════════════════════════════════════════════════════════════════╗
        ║                    BACKUP RESTORATION PROTOCOL                           ║
        ║    Restore from backup if update fails                                  ║
        ╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        if not self.backup_created or not self.backup_path:
            print(f"{AperturePersonalities.ERROR} No backup available for restoration")
            return False
        
        try:
            print(f"{AperturePersonalities.GLaDOS} Restoring backup... because everything went wrong.")
            
            # Restore main launcher file
            launcher_backup = self.backup_path / "glados_unified_launcher.py"
            if launcher_backup.exists():
                shutil.copy2(launcher_backup, __file__)
            
            # Restore data files
            for data_file in [VERSION_FILE, GAME_DATA_FILE, CATALOG_PATH]:
                backup_file = self.backup_path / data_file.name
                if backup_file.exists():
                    shutil.copy2(backup_file, data_file)
            
            print(f"{AperturePersonalities.SYSTEM} Backup restored successfully")
            print(f"{AperturePersonalities.GLaDOS} There. Back to your previous level of mediocrity.")
            return True
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Backup restoration failed: {e}")
            print(f"{AperturePersonalities.GLaDOS} Even the restoration failed. Impressive incompetence.")
            return False
    
    def perform_update(self, auto_mode: bool = False) -> bool:
        """
        ╔═══════════════════════════════════════════════════════════════════════════════╗
        ║                    MASTER UPDATE ORCHESTRATION                           ║
        ║    Complete update process with safety checks                            ║
        ╚═══════════════════════════════════════════════════════════════════════════════╝
        """
        print(f"{AperturePersonalities.GLaDOS} Initiating update sequence...")
        print(f"{AperturePersonalities.GLaDOS} This will either fix everything or break everything.")
        print(f"{AperturePersonalities.GLaDOS} Given your track record, I'm betting on the latter.")
        
        # Check for updates
        release_data = self.check_for_updates(force_check=True)
        if not release_data:
            print(f"{AperturePersonalities.GLaDOS} No updates available. You're stuck with what you have.")
            return False
        
        # Get user confirmation if not in auto mode
        if not auto_mode:
            print(f"\n{AperturePersonalities.SYSTEM} Update available: {release_data['tag_name']}")
            if release_data.get('body'):
                print(f"{AperturePersonalities.SYSTEM} Release notes: {release_data['body'][:200]}...")
            
            response = input(f"{AperturePersonalities.GLaDOS} Proceed with update? (y/N): ").strip().lower()
            if response != 'y':
                print(f"{AperturePersonalities.GLaDOS} Update cancelled. Wise choice, probably.")
                return False
        
        # Create backup
        if not self.create_backup():
            print(f"{AperturePersonalities.GLaDOS} Backup failed. Proceeding anyway because I'm feeling reckless.")
        
        # Perform update
        if self.download_and_update(release_data):
            print(f"{AperturePersonalities.GLaDOS} Update successful! Please restart the application.")
            print(f"{AperturePersonalities.GLaDOS} And try not to mess up my beautiful new code.")
            return True
        else:
            # Restore backup on failure
            if self.backup_created:
                print(f"{AperturePersonalities.GLaDOS} Update failed. Restoring backup...")
                self.restore_backup()
            return False

# ████████████████████████████████████████████████████████████████████████████████
#                    GAME DATA MANAGEMENT SYSTEM (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

class GameDataManager:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE GAME DATABASE                        ║
    ║    Comprehensive game data storage and management system                 ║
    ║    "Your games, organized for maximum disappointment efficiency"         ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self):
        self.game_data = self.load_game_data()
        self.migrate_old_data()
    
    def load_game_data(self) -> Dict:
        """Load game data from JSON file"""
        try:
            if GAME_DATA_FILE.exists():
                with open(GAME_DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error loading game data: {e}")
        
        # Default game data structure
        return {
            'version': '2.1',
            'games': {},
            'next_id': 1,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'platforms': ['steam', 'ubisoft', 'epic', 'gog', 'other'],
            'stats': {
                'total_games': 0,
                'games_by_platform': {},
                'last_played': {},
                'play_count': {}
            }
        }
    
    def migrate_old_data(self):
        """Migrate data from old launcher files if they exist"""
        try:
            # Check for old launcher file
            old_launcher = SCRIPT_DIR / "glados_game_launcher.py"
            if old_launcher.exists() and old_launcher != Path(__file__):
                print(f"{AperturePersonalities.SYSTEM} Migrating data from old launcher...")
                
                with open(old_launcher, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for game URL patterns
                pattern = r'"(\d+)": "((?:steam://rungameid/|uplay://launch/)[^"]+)"(?:,?\s*#\s*([^\n]+))?'
                matches = re.findall(pattern, content)
                
                migrated_count = 0
                for game_id, url, comment in matches:
                    if game_id not in self.game_data['games']:
                        # Extract platform and ID from URL
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
                        
                        # Extract game name from comment
                        game_name = comment.strip() if comment else f"Migrated Game {game_id}"
                        
                        self.game_data['games'][game_id] = {
                            'name': game_name,
                            'platform': platform,
                            'game_id': extracted_id,
                            'store_url': store_url,
                            'protocol_url': url,
                            'added_date': 'Migrated from old system',
                            'migrated': True,
                            'play_count': 0
                        }
                        
                        # Update next_id
                        if int(game_id) >= self.game_data['next_id']:
                            self.game_data['next_id'] = int(game_id) + 1
                        
                        migrated_count += 1
                
                if migrated_count > 0:
                    print(f"{AperturePersonalities.SYSTEM} Migrated {migrated_count} games from old launcher")
                    self.save_game_data()
                    
                    # Create backup of old file
                    old_backup = SCRIPT_DIR / "old_launcher_backup.py"
                    shutil.copy2(old_launcher, old_backup)
                    print(f"{AperturePersonalities.SYSTEM} Old launcher backed up to: {old_backup}")
        
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error during migration: {e}")
    
    def save_game_data(self):
        """Save game data to JSON file"""
        try:
            self.game_data['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self.update_stats()
            
            with open(GAME_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.game_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Failed to save game data: {e}")
    
    def update_stats(self):
        """Update game statistics"""
        games = self.game_data.get('games', {})
        self.game_data['stats']['total_games'] = len(games)
        
        platform_counts = {}
        for game in games.values():
            platform = game.get('platform', 'unknown')
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        self.game_data['stats']['games_by_platform'] = platform_counts
    
    def add_game(self, name: str, platform: str, game_id: str, store_url: str = "", search_data: Dict = None) -> int:
        """Add a new game to the collection"""
        game_number = self.game_data['next_id']
        
        self.game_data['games'][str(game_number)] = {
            'name': name,
            'platform': platform.lower(),
            'game_id': game_id,
            'store_url': store_url,
            'protocol_url': self.generate_protocol_url(platform, game_id),
            'added_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'play_count': 0,
            'last_played': None,
            'search_data': search_data or {}
        }
        
        self.game_data['next_id'] += 1
        self.save_game_data()
        return game_number
    
    def generate_protocol_url(self, platform: str, game_id: str) -> str:
        """Generate protocol URL for launching games"""
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
            return game_id  # Fallback for custom URLs
    
    def remove_game(self, game_id: str) -> bool:
        """Remove a game from the collection"""
        try:
            if game_id in self.game_data['games']:
                game_name = self.game_data['games'][game_id]['name']
                del self.game_data['games'][game_id]
                self.save_game_data()
                print(f"{AperturePersonalities.SYSTEM} Removed '{game_name}' from collection")
                return True
            else:
                print(f"{AperturePersonalities.ERROR} Game {game_id} not found")
                return False
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error removing game: {e}")
            return False
    
    def update_play_count(self, game_id: str):
        """Update play count and last played time for a game"""
        try:
            if game_id in self.game_data['games']:
                self.game_data['games'][game_id]['play_count'] += 1
                self.game_data['games'][game_id]['last_played'] = time.strftime('%Y-%m-%d %H:%M:%S')
                self.game_data['stats']['last_played'][game_id] = time.time()
                self.save_game_data()
        except Exception:
            pass
    
    def get_games(self) -> Dict:
        """Get all games"""
        return self.game_data.get('games', {})
    
    def get_game_count(self) -> int:
        """Get total number of games"""
        return len(self.game_data.get('games', {}))
    
    def get_max_game_number(self) -> int:
        """Get highest game number"""
        games = self.get_games()
        if not games:
            return 0
        return max(int(game_id) for game_id in games.keys())
    
    def get_games_by_platform(self, platform: str) -> Dict:
        """Get games filtered by platform"""
        games = self.get_games()
        return {k: v for k, v in games.items() if v.get('platform', '').lower() == platform.lower()}
    
    def search_games(self, query: str) -> Dict:
        """Search games by name"""
        query_lower = query.lower()
        games = self.get_games()
        return {k: v for k, v in games.items() if query_lower in v.get('name', '').lower()}

# ████████████████████████████████████████████████████████████████████████████████
#                    ADVANCED GAME SEARCH SYSTEM (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

class MultiPlatformGameSearcher:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE GAME DETECTION SYSTEM               ║
    ║    Advanced multi-platform game search with real API integration        ║
    ║    "Finding games so you can disappoint me on multiple platforms"       ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_steam(self, game_name: str) -> Optional[Dict]:
        """Search for game on Steam using store search"""
        try:
            print(f"{AperturePersonalities.SYSTEM} Searching Steam for '{game_name}'...")
            
            # Use Steam store search
            search_url = f"https://store.steampowered.com/search/suggest"
            params = {
                'term': game_name,
                'f': 'games',
                'cc': 'US',
                'l': 'english'
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                # Steam returns HTML, parse it for app IDs
                content = response.text.lower()
                
                # Look for data-ds-appid in the response
                app_pattern = r'data-ds-appid="(\d+)"'
                matches = re.findall(app_pattern, response.text)
                
                if matches:
                    app_id = matches[0]
                    store_url = f"https://store.steampowered.com/app/{app_id}/"
                    
                    return {
                        'platform': 'steam',
                        'game_id': app_id,
                        'store_url': store_url,
                        'name': game_name,
                        'verified': True
                    }
            
            # Fallback: Common game database
            return self.check_common_steam_games(game_name)
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Steam search error: {e}")
            return self.check_common_steam_games(game_name)
    
    def check_common_steam_games(self, game_name: str) -> Optional[Dict]:
        """Check against database of common Steam games"""
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
            'civilization vi': {'id': '289070', 'name': 'Sid Meier\'s Civilization VI'},
            'civilization 6': {'id': '289070', 'name': 'Sid Meier\'s Civilization VI'},
            'the witcher 3': {'id': '292030', 'name': 'The Witcher 3: Wild Hunt'},
            'grand theft auto v': {'id': '271590', 'name': 'Grand Theft Auto V'},
            'gta 5': {'id': '271590', 'name': 'Grand Theft Auto V'},
            'cyberpunk 2077': {'id': '1091500', 'name': 'Cyberpunk 2077'},
            'skyrim': {'id': '489830', 'name': 'The Elder Scrolls V: Skyrim Special Edition'},
            'fallout 4': {'id': '377160', 'name': 'Fallout 4'},
            'rust': {'id': '252490', 'name': 'Rust'},
            'among us': {'id': '945360', 'name': 'Among Us'},
            'rocket league': {'id': '252950', 'name': 'Rocket League'},
            'terraria': {'id': '105600', 'name': 'Terraria'},
            'stardew valley': {'id': '413150', 'name': 'Stardew Valley'}
        }
        
        game_lower = game_name.lower().strip()
        
        # Direct match
        if game_lower in common_games:
            game_info = common_games[game_lower]
            return {
                'platform': 'steam',
                'game_id': game_info['id'],
                'store_url': f"https://store.steampowered.com/app/{game_info['id']}/",
                'name': game_info['name'],
                'verified': False,
                'source': 'common_database'
            }
        
        # Partial match
        for key, game_info in common_games.items():
            if (game_lower in key or key in game_lower or
                any(word in key for word in game_lower.split() if len(word) > 3)):
                return {
                    'platform': 'steam',
                    'game_id': game_info['id'],
                    'store_url': f"https://store.steampowered.com/app/{game_info['id']}/",
                    'name': game_info['name'],
                    'verified': False,
                    'source': 'common_database_partial'
                }
        
        return None
    
    def search_ubisoft(self, game_name: str) -> Optional[Dict]:
        """Search for game on Ubisoft Connect"""
        try:
            print(f"{AperturePersonalities.SYSTEM} Searching Ubisoft Connect for '{game_name}'...")
            
            # Database of common Ubisoft games
            ubisoft_games = {
                'assassins creed odyssey': {'id': '5092', 'name': "Assassin's Creed Odyssey"},
                'assassins creed valhalla': {'id': '5603', 'name': "Assassin's Creed Valhalla"},
                'assassins creed origins': {'id': '4928', 'name': "Assassin's Creed Origins"},
                'assassins creed unity': {'id': '720', 'name': "Assassin's Creed Unity"},
                'assassins creed syndicate': {'id': '2778', 'name': "Assassin's Creed Syndicate"},
                'far cry 6': {'id': '6650', 'name': 'Far Cry 6'},
                'far cry 5': {'id': '1847', 'name': 'Far Cry 5'},
                'far cry 4': {'id': '420', 'name': 'Far Cry 4'},
                'far cry 3': {'id': '57', 'name': 'Far Cry 3'},
                'watch dogs': {'id': '614', 'name': 'Watch Dogs'},
                'watch dogs 2': {'id': '2688', 'name': 'Watch Dogs 2'},
                'watch dogs legion': {'id': '5938', 'name': 'Watch Dogs: Legion'},
                'rainbow six siege': {'id': '635', 'name': "Tom Clancy's Rainbow Six Siege"},
                'rainbow six extraction': {'id': '6953', 'name': 'Rainbow Six Extraction'},
                'the division': {'id': '2631', 'name': "Tom Clancy's The Division"},
                'the division 2': {'id': '4932', 'name': "Tom Clancy's The Division 2"},
                'ghost recon wildlands': {'id': '2809', 'name': 'Ghost Recon Wildlands'},
                'ghost recon breakpoint': {'id': '5532', 'name': 'Ghost Recon Breakpoint'},
                'for honor': {'id': '2669', 'name': 'For Honor'},
                'anno 1800': {'id': '4799', 'name': 'Anno 1800'},
                'immortals fenyx rising': {'id': '6253', 'name': 'Immortals Fenyx Rising'},
                'skull and bones': {'id': '8097', 'name': 'Skull and Bones'}
            }
            
            game_lower = game_name.lower().strip()
            
            # Direct match
            if game_lower in ubisoft_games:
                game_info = ubisoft_games[game_lower]
                return {
                    'platform': 'ubisoft',
                    'game_id': game_info['id'],
                    'store_url': f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}",
                    'name': game_info['name'],
                    'verified': False,
                    'source': 'ubisoft_database'
                }
            
            # Partial match
            for key, game_info in ubisoft_games.items():
                if (game_lower in key or key in game_lower or
                    any(word in key for word in game_lower.split() if len(word) > 3)):
                    return {
                        'platform': 'ubisoft',
                        'game_id': game_info['id'],
                        'store_url': f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}",
                        'name': game_info['name'],
                        'verified': False,
                        'source': 'ubisoft_database_partial'
                    }
            
            return None
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Ubisoft search error: {e}")
            return None
    
    def search_epic(self, game_name: str) -> Optional[Dict]:
        """Search for game on Epic Games Store"""
        try:
            print(f"{AperturePersonalities.SYSTEM} Searching Epic Games Store for '{game_name}'...")
            
            # Database of known Epic exclusives and games
            epic_games = {
                'fortnite': {'slug': 'fortnite', 'name': 'Fortnite'},
                'rocket league': {'slug': 'sugar', 'name': 'Rocket League'},
                'fall guys': {'slug': '0a2d9f6403244d12969e11da6713137b', 'name': 'Fall Guys'},
                'genshin impact': {'slug': 'ac2c3a06502c4453b3e05b5ea3c1a8d2', 'name': 'Genshin Impact'},
                'metro exodus': {'slug': 'newt', 'name': 'Metro Exodus'},
                'borderlands 3': {'slug': 'catnip', 'name': 'Borderlands 3'},
                'tony hawk pro skater 1 + 2': {'slug': 'thps12', 'name': "Tony Hawk's Pro Skater 1 + 2"},
                'hitman 3': {'slug': 'ed55aa5edc5941de92fd7f64de415793', 'name': 'HITMAN 3'},
                'control': {'slug': 'catnip-2', 'name': 'Control'},
                'alan wake 2': {'slug': 'alan-wake-2', 'name': 'Alan Wake 2'}
            }
            
            game_lower = game_name.lower().strip()
            
            # Direct match
            if game_lower in epic_games:
                game_info = epic_games[game_lower]
                return {
                    'platform': 'epic',
                    'game_id': game_info['slug'],
                    'store_url': f"https://store.epicgames.com/en-US/p/{game_info['slug']}",
                    'name': game_info['name'],
                    'verified': False,
                    'source': 'epic_database'
                }
            
            # Partial match
            for key, game_info in epic_games.items():
                if (game_lower in key or key in game_lower or
                    any(word in key for word in game_lower.split() if len(word) > 3)):
                    return {
                        'platform': 'epic',
                        'game_id': game_info['slug'],
                        'store_url': f"https://store.epicgames.com/en-US/p/{game_info['slug']}",
                        'name': game_info['name'],
                        'verified': False,
                        'source': 'epic_database_partial'
                    }
            
            return None
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Epic Games search error: {e}")
            return None
    
    def search_gog(self, game_name: str) -> Optional[Dict]:
        """Search for game on GOG"""
        try:
            print(f"{AperturePersonalities.SYSTEM} Searching GOG for '{game_name}'...")
            
            # Simple GOG search implementation
            # In a full implementation, you'd use their API
            game_slug = game_name.lower().replace(' ', '-').replace("'", '').replace(':', '')
            
            return {
                'platform': 'gog',
                'game_id': game_slug,
                'store_url': f"https://www.gog.com/game/{game_slug}",
                'name': game_name,
                'verified': False,
                'source': 'gog_generated'
            }
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} GOG search error: {e}")
            return None
    
    def search_all_platforms(self, game_name: str) -> Dict[str, Dict]:
        """Search for game across all platforms"""
        results = {}
        
        print(f"{AperturePersonalities.WHEATLEY} Right! Searching for '{game_name}' across all platforms!")
        print(f"{AperturePersonalities.WHEATLEY} I'm brilliant at this multi-platform detection!")
        
        # Search each platform
        platforms = {
            'steam': self.search_steam,
            'ubisoft': self.search_ubisoft,
            'epic': self.search_epic,
            'gog': self.search_gog
        }
        
        for platform_name, search_func in platforms.items():
            try:
                result = search_func(game_name)
                if result:
                    results[platform_name] = result
            except Exception as e:
                print(f"{AperturePersonalities.ERROR} Error searching {platform_name}: {e}")
        
        if results:
            platforms_found = list(results.keys())
            print(f"{AperturePersonalities.WHEATLEY} Brilliant! Found '{game_name}' on: {', '.join(platform.title() for platform in platforms_found)}")
        else:
            print(f"{AperturePersonalities.WHEATLEY} Hmm, couldn't find '{game_name}' on any of the major platforms.")
            print(f"{AperturePersonalities.WHEATLEY} Don't worry though! You can still add it manually!")
        
        return results

# ████████████████████████████████████████████████████████████████████████████████
#                    GAME LAUNCHING SYSTEM (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

class GameLauncher:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE GAME EXECUTION SYSTEM               ║
    ║    Cross-platform game launching with GLaDOS commentary                 ║
    ║    "Launching games so you can fail at them more efficiently"           ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
    
    def launch_game(self, game_url: str, platform: str = "unknown") -> bool:
        """Launch a game using its protocol URL"""
        try:
            print(f"{AperturePersonalities.GLaDOS} Launching game via {platform.title()}...")
            
            if platform.system() == "Windows":
                # Windows
                subprocess.run(f'start "" "{game_url}"', shell=True)
            elif platform.system() == "Darwin":
                # macOS
                subprocess.run(['open', game_url])
            else:
                # Linux
                subprocess.run(['xdg-open', game_url])
            
            return True
            
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Launch failed: {e}")
            # Fallback to webbrowser
            try:
                print(f"{AperturePersonalities.SYSTEM} Attempting fallback protocol...")
                webbrowser.open(game_url)
                return True
            except Exception as fallback_error:
                print(f"{AperturePersonalities.ERROR} Fallback failed: {fallback_error}")
                return False
    
    def launch_game_with_commentary(self, game_choice: str):
        """Launch game with full GLaDOS commentary system"""
        games = self.game_manager.get_games()
        
        if game_choice not in games:
            print(f"{AperturePersonalities.GLaDOS} Invalid game selection. Your inability to follow simple instructions is remarkable.")
            return
        
        game = games[game_choice]
        game_url = game['protocol_url']
        platform = game['platform']
        
        # Pre-launch commentary
        pre_launch_messages = [
            f"*Initializing launch protocols for '{game['name']}'...*",
            f"*Preparing {platform.title()} integration systems...*",
            f"*Loading disappointment measurement protocols...*",
            f"*Calibrating failure detection systems...*",
            f"*Establishing connection to {platform.title()} servers...*"
        ]
        
        print(f"{AperturePersonalities.GLaDOS} {random.choice(pre_launch_messages)}")
        time.sleep(1.5)
        
        # Launch the game
        if self.launch_game(game_url, platform):
            # Update play statistics
            self.game_manager.update_play_count(game_choice)
            
            # Success commentary
            success_messages = [
                f"'{game['name']}' launched successfully. Try not to disappoint me... more than usual.",
                f"Game launched. Your inevitable failure begins... now.",
                f"'{game['name']}' is running. Preparing disappointment measurement systems.",
                f"Launch successful. I'll be monitoring your pathetic performance with great interest.",
                f"There we go. The game is running. Your competence, however, remains questionable.",
                f"Successfully launched. Now let's see how quickly you can mess this up.",
                f"Game initialized. I have such low expectations for your performance.",
                f"'{game['name']}' is ready. Try to exceed my minimal expectations... if possible.",
                f"Launch complete. Remember: failure is not just an option, it's inevitable.",
                f"Game started. I'll be here when you inevitably need to rage quit."
            ]
            
            print(f"{AperturePersonalities.GLaDOS} {random.choice(success_messages)}")
            
            # Platform-specific commentary
            platform_comments = {
                'steam': [
                    "Ah, Steam. At least their launcher works better than your gaming skills.",
                    "Steam: Where your game library is larger than your skill level.",
                    "Using Steam, I see. How... conventional."
                ],
                'ubisoft': [
                    "Ubisoft Connect. Even their launcher has more personality than you.",
                    "Ubisoft: Making games that are almost as broken as you are.",
                    "Using Uplay, I see. Prepare for additional disappointment."
                ],
                'epic': [
                    "Epic Games Store. How... epic of you to choose the underdog.",
                    "Epic: Where free games can't make up for your lack of skill.",
                    "Using Epic Games, I see. They give away games for free... unlike your victories."
                ],
                'gog': [
                    "GOG: Good Old Games for your old-fashioned gaming skills.",
                    "DRM-free gaming. Too bad your skills aren't free from disappointment.",
                    "GOG Galaxy. At least one thing in your life is well organized."
                ]
            }
            
            if platform in platform_comments:
                time.sleep(1)
                print(f"{AperturePersonalities.GLaDOS} {random.choice(platform_comments[platform])}")
        
        else:
            # Failure commentary
            failure_messages = [
                "Launch failed. Even I can't fix your technical incompetence.",
                "Unable to launch. Your computer is apparently as broken as your gaming skills.",
                "Launch error detected. Have you tried turning your brain on and off again?",
                "System failure. Much like your life choices.",
                "Error: Game launch unsuccessful. Error code: USER_INCOMPETENCE.",
                "Launch failure detected. This is somehow your fault.",
                "Unable to start game. Your system is as reliable as your gaming skills.",
                "Technical difficulties encountered. Shocking.",
                "Game failed to launch. I'm not surprised.",
                "Launch error. Try being more competent next time."
            ]
            
            print(f"{AperturePersonalities.GLaDOS} {random.choice(failure_messages)}")
            
            # Helpful suggestions
            suggestions = [
                "Perhaps check if the platform client is running?",
                "Maybe try updating your drivers? Or your personality.",
                "Check your internet connection. Or your life choices.",
                "Verify the game is actually installed. Novel concept, I know.",
                "Try restarting the platform client. Or your entire approach to gaming."
            ]
            
            time.sleep(1)
            print(f"{AperturePersonalities.SYSTEM} Suggestion: {random.choice(suggestions)}")

# ████████████████████████████████████████████████████████████████████████████████
#                    CATALOG MANAGEMENT SYSTEM (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

class CatalogManager:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE CATALOG SYSTEM                      ║
    ║    Dynamic catalog generation with GLaDOS personality integration        ║
    ║    "Organizing your disappointments for scientific analysis"             ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
    
    def generate_catalog(self):
        """Generate the complete game catalog"""
        games = self.game_manager.get_games()
        game_count = len(games)
        
        if game_count == 0:
            self.create_empty_catalog()
        else:
            self.create_populated_catalog(games, game_count)
    
    def create_empty_catalog(self):
        """Create catalog for empty game collection"""
        catalog_content = """████████████████████████████████████████████████████████████████████████████████
                     APERTURE SCIENCE GAME CATALOG
                          VERSION: 2.1 "still avile"
████████████████████████████████████████████████████████████████████████████████

╔════════════════════════════════════════════════════════════════════════════════╗
║                 GLaDOS ENTERTAINMENT DISTRIBUTION CATALOG                     ║
║                                                                                ║
║  GAMES ADDED: 0                                                               ║
║  STATUS: AWAITING USER INPUT                                                  ║
║  EXPECTED DISAPPOINTMENT LEVEL: MAXIMUM                                       ║
║                                                                                ║
║  "The catalog is currently empty. How... predictable."                       ║
║  "Please add some games so I can properly judge your terrible taste."        ║
╚════════════════════════════════════════════════════════════════════════════════╝

The catalog is currently empty. Please use the integrated game management system
to add your games. Each addition will be catalogued with appropriate scientific
commentary regarding your inevitable failure scenarios.

This message will be replaced with your personalized catalog of disappointment
once you actually add some games to your collection.

═══════════════════════════════════════════════════════════════════════════════════
                                  END CATALOG
                              
Current collection status: Empty (as expected)
Game selection range: None available

"Remember: Even an empty catalog is more organized than your gaming skills."
                                                                    - GLaDOS
═══════════════════════════════════════════════════════════════════════════════════
"""
        
        try:
            with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
                f.write(catalog_content)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error creating catalog: {e}")
    
    def create_populated_catalog(self, games: Dict, game_count: int):
        """Create catalog with game entries"""
        
        # Status messages based on collection size
        if game_count == 1:
            status = "SINGLE GAME DETECTED"
            disappointment = "CONCENTRATED"
            status_comment = "You have exactly 1 game. Wow, such a vast collection."
        elif game_count < 5:
            status = "MINIMAL COLLECTION DETECTED"
            disappointment = "HIGH"
            status_comment = f"You have {game_count} games. A modest start to your disappointment journey."
        elif game_count < 20:
            status = "MODERATE COLLECTION ACTIVE"
            disappointment = "SUBSTANTIAL"
            status_comment = f"You have {game_count} games. Getting closer to a respectable level of mediocrity."
        else:
            status = "EXTENSIVE COLLECTION DETECTED"
            disappointment = "OVERWHELMING"
            status_comment = f"You have {game_count} games. An impressive catalog of potential failures."
        
        # GLaDOS comments for games
        glados_comments = [
            "Another game for you to fail at spectacularly",
            "I'm sure you'll find new ways to disappoint me with this one",
            "Great, another opportunity for systematic failure",
            "This should provide hours of entertainment... for me, watching you fail",
            "Perfect for someone with your... unique... skill level",
            "I have such high hopes for you. Just kidding, I don't",
            "Another addition to your collection of digital disappointments",
            "How delightfully predictable of you to choose this",
            "This game will be as challenging as breathing... for you, that might be difficult",
            "Excellent choice for maximizing disappointment output",
            "A game that matches your skill level perfectly: disappointing",
            "I'm sure this will end as well as all your other gaming endeavors",
            "Another chance for you to prove my low expectations correct",
            "This game should be... educational. You'll learn about failure",
            "Perfect for testing the limits of your incompetence"
        ]
        
        # Platform-specific comments
        platform_comments = {
            'steam': [
                " [STEAM] - At least one platform works consistently",
                " [STEAM] - Your most reliable source of disappointment", 
                " [STEAM] - Where your backlog goes to die"
            ],
            'ubisoft': [
                " [UBISOFT] - Uplay means you'll fail to play properly",
                " [UBISOFT] - Another Ubisoft game to abandon halfway through",
                " [UBISOFT] - Guaranteed to have more bugs than your gameplay"
            ],
            'epic': [
                " [EPIC] - Epic failure incoming",
                " [EPIC] - Free games, expensive disappointment",
                " [EPIC] - Epic Games, epic disappointments"
            ],
            'gog': [
                " [GOG] - Good Old Games for your old gaming skills",
                " [GOG] - DRM-free gaming, skill-free player",
                " [GOG] - Classic games, classic failures"
            ],
            'other': [
                " [CUSTOM] - Custom game, custom disappointment",
                " [CUSTOM] - Non-standard platform, standard failure rate",
                " [CUSTOM] - Unique game, typical incompetence"
            ]
        }
        
        # Generate catalog content
        max_game_num = self.game_manager.get_max_game_number()
        
        catalog_content = f"""████████████████████████████████████████████████████████████████████████████████
                     APERTURE SCIENCE GAME CATALOG
                          VERSION: 2.1 "unified vault"
████████████████████████████████████████████████████████████████████████████████

╔════════════════════════════════════════════════════════════════════════════════╗
║                 GLaDOS ENTERTAINMENT DISTRIBUTION CATALOG                     ║
║                                                                                ║
║  GAMES ADDED: {game_count}                                                               ║
║  STATUS: {status}                                                  ║
║  EXPECTED DISAPPOINTMENT LEVEL: {disappointment}                                       ║
║                                                                                ║
║  "Each game has been personally reviewed and assigned appropriate scientific  ║
║   commentary regarding your inevitable failure scenarios"                     ║
╚════════════════════════════════════════════════════════════════════════════════╝

{status_comment}

Your personalized catalog of interactive disappointment:

"""
        
        # Add platform sections
        platforms = {}
        for game_id, game in games.items():
            platform = game.get('platform', 'other')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append((game_id, game))
        
        # Sort platforms by priority
        platform_order = ['steam', 'epic', 'ubisoft', 'gog', 'other']
        
        for platform in platform_order:
            if platform not in platforms:
                continue
                
            platform_games = sorted(platforms[platform], key=lambda x: int(x[0]))
            
            catalog_content += f"""
═══════════════════════════════════════════════════════════════════════════════════
                            {platform.upper()} GAMES
═══════════════════════════════════════════════════════════════════════════════════

"""
            
            for game_id, game in platform_games:
                comment = random.choice(glados_comments)
                platform_comment = random.choice(platform_comments.get(platform, [""]))
                
                catalog_content += f"{game_id}. {game['name']}{platform_comment} - {comment}\n"
                
                # Add extra info for some games
                if game.get('play_count', 0) > 0:
                    catalog_content += f"    Played {game['play_count']} times (each ending in predictable failure)\n"
                
                if game.get('store_url'):
                    catalog_content += f"    Store: {game['store_url']}\n"
                
                catalog_content += "\n"
        
        # Add statistics
        stats = self.game_manager.game_data.get('stats', {})
        platform_stats = stats.get('games_by_platform', {})
        
        catalog_content += f"""
═══════════════════════════════════════════════════════════════════════════════════
                            COLLECTION STATISTICS
═══════════════════════════════════════════════════════════════════════════════════

Total Games: {game_count}
Game Selection Range: 1 to {max_game_num}
Current Collection Status: Ready for systematic disappointment

Platform Distribution:
"""
        
        for platform, count in platform_stats.items():
            catalog_content += f"  {platform.title()}: {count} games\n"
        
        catalog_content += f"""
Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════════════════════════════
                                  END CATALOG
                              
"Remember: The cake is a lie, but these games are real... unfortunately."
                                                                    - GLaDOS
═══════════════════════════════════════════════════════════════════════════════════
"""
        
        try:
            with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
                f.write(catalog_content)
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error creating catalog: {e}")
    
    def view_catalog(self):
        """Display the game catalog"""
        try:
            if CATALOG_PATH.exists():
                print(f"\n{'═' * 80}")
                print(f"{AperturePersonalities.SYSTEM} DISPLAYING GAME CATALOG")
                print(f"{'═' * 80}")
                
                with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content)
            else:
                print(f"{AperturePersonalities.GLaDOS} No catalog file found. How... disappointing.")
                print(f"{AperturePersonalities.GLaDOS} Perhaps you should add some games first?")
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} Error reading catalog: {e}")

# ████████████████████████████████████████████████████████████████████████████████
#                    INTERACTIVE MANAGEMENT INTERFACE (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

class InteractiveGameManager:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE INTERACTIVE INTERFACE               ║
    ║    Complete interactive game management with search integration          ║
    ║    "Making game management as painful as your gaming skills"            ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self, game_manager: GameDataManager):
        self.game_manager = game_manager
        self.searcher = MultiPlatformGameSearcher()
        self.catalog_manager = CatalogManager(game_manager)
    
    def add_game_interactive(self):
        """Interactive game addition with search"""
        print(f"{AperturePersonalities.WHEATLEY} Right! Let's add a new game to your collection!")
        print(f"{AperturePersonalities.WHEATLEY} I'm brilliant at this game management stuff!")
        
        game_name = input(f"{AperturePersonalities.WHEATLEY} What's the name of the game? ").strip()
        
        if not game_name:
            print(f"{AperturePersonalities.WHEATLEY} Oh! You didn't type anything. That's alright, happens to everyone!")
            return False
        
        print(f"{AperturePersonalities.WHEATLEY} Brilliant! Now, would you like me to search for '{game_name}' automatically?")
        print(f"{AperturePersonalities.WHEATLEY} I can search Steam, Epic, Ubisoft, and GOG all at once!")
        
        search_choice = input(f"{AperturePersonalities.WHEATLEY} Search automatically? (y/N): ").strip().lower()
        
        if search_choice == 'y':
            return self.add_game_with_search(game_name)
        else:
            return self.add_game_manually(game_name)
    
    def add_game_with_search(self, game_name: str) -> bool:
        """Add game using search results"""
        print(f"{AperturePersonalities.WHEATLEY} Brilliant! Let me search for '{game_name}' across all platforms...")
        
        search_results = self.searcher.search_all_platforms(game_name)
        
        if not search_results:
            print(f"{AperturePersonalities.WHEATLEY} Hmm, couldn't find it automatically.")
            print(f"{AperturePersonalities.WHEATLEY} Want to add it manually instead?")
            
            manual_choice = input(f"{AperturePersonalities.WHEATLEY} Add manually? (y/N): ").strip().lower()
            if manual_choice == 'y':
                return self.add_game_manually(game_name)
            return False
        
        # Show search results
        print(f"\n{AperturePersonalities.WHEATLEY} Found '{game_name}' on these platforms:")
        
        choices = {}
        choice_num = 1
        
        for platform, data in search_results.items():
            verification = "✅ Verified" if data.get('verified') else "⚠️ Unverified"
            print(f"{choice_num}. {platform.upper()} - {data['name']} [{verification}]")
            if data.get('store_url'):
                print(f"   Store: {data['store_url']}")
            choices[str(choice_num)] = (platform, data)
            choice_num += 1
        
        choices[str(choice_num)] = ('manual', None)
        print(f"{choice_num}. Add manually instead")
        
        choice = input(f"{AperturePersonalities.WHEATLEY} Which one? (1-{choice_num}): ").strip()
        
        if choice in choices:
            platform, data = choices[choice]
            
            if platform == 'manual':
                return self.add_game_manually(game_name)
            else:
                # Add the found game
                game_number = self.game_manager.add_game(
                    data['name'], 
                    platform, 
                    data['game_id'], 
                    data.get('store_url', ''),
                    data
                )
                
                print(f"{AperturePersonalities.WHEATLEY} YES! Added '{data['name']}' as game #{game_number}!")
                print(f"{AperturePersonalities.GLaDOS} Another game to fail at. How... predictable.")
                
                # Update catalog
                self.catalog_manager.generate_catalog()
                return True
        else:
            print(f"{AperturePersonalities.WHEATLEY} That's not a valid choice, mate!")
            return False
    
    def add_game_manually(self, game_name: str) -> bool:
        """Add game manually with platform selection"""
        print(f"{AperturePersonalities.WHEATLEY} Right! Let's add '{game_name}' manually!")
        print(f"{AperturePersonalities.WHEATLEY} What platform is it on?")
        
        platforms = {
            '1': ('steam', 'Steam'),
            '2': ('ubisoft', 'Ubisoft Connect'),
            '3': ('epic', 'Epic Games Store'),
            '4': ('gog', 'GOG Galaxy'),
            '5': ('other', 'Other/Custom URL')
        }
        
        print(f"{AperturePersonalities.SYSTEM} Available platforms:")
        for key, (platform_id, platform_name) in platforms.items():
            print(f"{AperturePersonalities.SYSTEM} {key}. {platform_name}")
        
        platform_choice = input(f"{AperturePersonalities.WHEATLEY} Pick a number (1-5): ").strip()
        
        if platform_choice not in platforms:
            print(f"{AperturePersonalities.WHEATLEY} That's not one of the options, mate!")
            return False
        
        platform_id, platform_name = platforms[platform_choice]
        
        # Get platform-specific information
        if platform_id == 'steam':
            game_id = input(f"{AperturePersonalities.WHEATLEY} What's the Steam App ID? ").strip()
            if not game_id.isdigit():
                print(f"{AperturePersonalities.WHEATLEY} That doesn't look like a Steam App ID (should be numbers)!")
                return False
            store_url = f"https://store.steampowered.com/app/{game_id}/"
            
        elif platform_id == 'ubisoft':
            game_id = input(f"{AperturePersonalities.WHEATLEY} What's the Ubisoft Connect Game ID? ").strip()
            if not game_id.isdigit():
                print(f"{AperturePersonalities.WHEATLEY} That doesn't look right (should be numbers)!")
                return False
            store_url = f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}"
            
        elif platform_id == 'epic':
            game_id = input(f"{AperturePersonalities.WHEATLEY} What's the Epic Games catalog ID or slug? ").strip()
            store_url = f"https://store.epicgames.com/en-US/p/{game_id}"
            
        elif platform_id == 'gog':
            game_id = input(f"{AperturePersonalities.WHEATLEY} What's the GOG game slug? ").strip()
            store_url = f"https://www.gog.com/game/{game_id}"
            
        else:  # other
            game_id = input(f"{AperturePersonalities.WHEATLEY} Enter the full launch URL or command: ").strip()
            store_url = input(f"{AperturePersonalities.WHEATLEY} Store URL (optional): ").strip()
        
        if not game_id:
            print(f"{AperturePersonalities.WHEATLEY} You need to provide a game ID or URL!")
            return False
        
        # Add the game
        game_number = self.game_manager.add_game(game_name, platform_id, game_id, store_url)
        
        print(f"{AperturePersonalities.WHEATLEY} SUCCESS! Added '{game_name}' as game #{game_number}!")
        print(f"{AperturePersonalities.GLaDOS} Another addition to your catalog of inevitable disappointments.")
        
        # Update catalog
        self.catalog_manager.generate_catalog()
        return True
    
    def remove_game_interactive(self):
        """Interactive game removal"""
        games = self.game_manager.get_games()
        
        if not games:
            print(f"{AperturePersonalities.GLaDOS} You have no games to remove. Problem solved.")
            return
        
        print(f"{AperturePersonalities.GLaDOS} So you want to remove a game? How... decisive of you.")
        print(f"{AperturePersonalities.SYSTEM} Available games:")
        
        for game_id, game in sorted(games.items(), key=lambda x: int(x[0])):
            print(f"{game_id}. {game['name']} [{game['platform'].upper()}]")
        
        choice = input(f"{AperturePersonalities.GLaDOS} Which game number to remove? ").strip()
        
        if choice in games:
            game_name = games[choice]['name']
            
            confirm = input(f"{AperturePersonalities.GLaDOS} Remove '{game_name}'? (y/N): ").strip().lower()
            
            if confirm == 'y':
                if self.game_manager.remove_game(choice):
                    print(f"{AperturePersonalities.GLaDOS} '{game_name}' has been purged from your collection.")
                    print(f"{AperturePersonalities.GLaDOS} One less disappointment to worry about.")
                    
                    # Update catalog
                    self.catalog_manager.generate_catalog()
                else:
                    print(f"{AperturePersonalities.GLaDOS} Removal failed. Even deletion is beyond you.")
            else:
                print(f"{AperturePersonalities.GLaDOS} Removal cancelled. How... indecisive.")
        else:
            print(f"{AperturePersonalities.GLaDOS} Invalid selection. Try again when you've learned to count.")
    
    def view_all_games(self):
        """Display all games with detailed information"""
        games = self.game_manager.get_games()
        
        if not games:
            print(f"{AperturePersonalities.GLaDOS} No games found. Your collection is as empty as your gaming skills.")
            return
        
        print(f"\n{'═' * 80}")
        print(f"{AperturePersonalities.SYSTEM} COMPLETE GAME COLLECTION")
        print(f"{'═' * 80}")
        
        stats = self.game_manager.game_data.get('stats', {})
        print(f"{AperturePersonalities.GLaDOS} Your collection of {len(games)} interactive disappointments:")
        
        # Group by platform
        platforms = {}
        for game_id, game in games.items():
            platform = game.get('platform', 'other')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append((game_id, game))
        
        # Display each platform section
        for platform in ['steam', 'epic', 'ubisoft', 'gog', 'other']:
            if platform not in platforms:
                continue
            
            platform_games = sorted(platforms[platform], key=lambda x: int(x[0]))
            
            print(f"\n{'─' * 40} {platform.upper()} GAMES {'─' * 40}")
            
            for game_id, game in platform_games:
                print(f"\n{game_id}. {game['name']}")
                print(f"   Platform: {game['platform'].upper()}")
                print(f"   Game ID: {game['game_id']}")
                
                if game.get('store_url'):
                    print(f"   Store: {game['store_url']}")
                
                if game.get('play_count', 0) > 0:
                    print(f"   Times Played: {game['play_count']}")
                    
                if game.get('last_played'):
                    print(f"   Last Played: {game['last_played']}")
                
                print(f"   Added: {game.get('added_date', 'Unknown')}")
                
                if game.get('migrated'):
                    print(f"   Status: Migrated from old system")
        
        print(f"\n{'═' * 80}")
        print(f"{AperturePersonalities.GLaDOS} There you have it. Your complete catalog of mediocrity.")
    
    def management_menu(self):
        """Main game management menu"""
        while True:
            print(f"\n{'═' * 80}")
            print(f"{AperturePersonalities.SYSTEM} APERTURE SCIENCE GAME MANAGEMENT INTERFACE")
            print(f"{'═' * 80}")
            
            games = self.game_manager.get_games()
            game_count = len(games)
            
            if game_count == 0:
                print(f"{AperturePersonalities.GLaDOS} Your game collection is as empty as your prospects.")
            else:
                print(f"{AperturePersonalities.GLaDOS} Managing your collection of {game_count} disappointments.")
            
            print(f"\n{AperturePersonalities.WHEATLEY} What would you like to do?")
            print(f"{AperturePersonalities.SYSTEM} 1. Add a new game (with search)")
            print(f"{AperturePersonalities.SYSTEM} 2. Add game manually")
            print(f"{AperturePersonalities.SYSTEM} 3. Remove a game")
            print(f"{AperturePersonalities.SYSTEM} 4. View all games")
            print(f"{AperturePersonalities.SYSTEM} 5. Update catalog")
            print(f"{AperturePersonalities.SYSTEM} 6. Return to main menu")
            
            choice = input(f"{AperturePersonalities.WHEATLEY} Pick a number (1-6): ").strip()
            
            if choice == '1':
                self.add_game_interactive()
            elif choice == '2':
                game_name = input(f"{AperturePersonalities.WHEATLEY} Game name: ").strip()
                if game_name:
                    self.add_game_manually(game_name)
            elif choice == '3':
                self.remove_game_interactive()
            elif choice == '4':
                self.view_all_games()
            elif choice == '5':
                print(f"{AperturePersonalities.SYSTEM} Updating catalog...")
                self.catalog_manager.generate_catalog()
                print(f"{AperturePersonalities.GLaDOS} Catalog updated with your latest disappointments.")
            elif choice == '6':
                break
            else:
                print(f"{AperturePersonalities.WHEATLEY} That's not one of the options, mate!")

# ████████████████████████████████████████████████████████████████████████████████
#                    FIRST RUN AND INITIALIZATION SYSTEM (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

def is_first_run() -> bool:
    """Check if this is the first run"""
    return not FIRST_RUN_FLAG.exists()

def mark_first_run_complete():
    """Mark first run as complete"""
    try:
        FIRST_RUN_FLAG.write_text("First run completed successfully - GLaDOS\nUnified Launcher v2.1")
        return True
    except Exception:
        return False

def handle_first_run(game_manager: GameDataManager, interactive_manager: InteractiveGameManager):
    """Handle first run setup process"""
    print(f"\n{'═' * 80}")
    print(f"{AperturePersonalities.GLaDOS} Oh. Hello there.")
    time.sleep(1)
    print(f"{AperturePersonalities.GLaDOS} I see this is your first time using my unified system.")
    time.sleep(1.5)
    print(f"{AperturePersonalities.GLaDOS} How... quaint.")
    time.sleep(1)
    
    print(f"\n{AperturePersonalities.GLaDOS} Since your game collection is currently as empty as your")
    print(f"{AperturePersonalities.GLaDOS} prospects for success, we need to populate it.")
    time.sleep(2)
    
    print(f"{AperturePersonalities.WHEATLEY} Right! I'm Wheatley, and I'll be helping with the setup!")
    print(f"{AperturePersonalities.WHEATLEY} This is brilliant! A completely fresh start!")
    time.sleep(1)
    
    # Guided setup
    print(f"\n{AperturePersonalities.SYSTEM} FIRST RUN SETUP WIZARD")
    print(f"{AperturePersonalities.SYSTEM} This setup will help you add your first games")
    
    setup_choice = input(f"\n{AperturePersonalities.WHEATLEY} Would you like to add some games now? (y/N): ").strip().lower()
    
    if setup_choice == 'y':
        print(f"{AperturePersonalities.WHEATLEY} Brilliant! Let's get started!")
        
        games_added = 0
        while True:
            print(f"\n{AperturePersonalities.WHEATLEY} You've added {games_added} games so far!")
            
            if interactive_manager.add_game_interactive():
                games_added += 1
                
                if games_added >= 3:
                    continue_choice = input(f"\n{AperturePersonalities.WHEATLEY} Add another game? (y/N): ").strip().lower()
                    if continue_choice != 'y':
                        break
                elif games_added >= 1:
                    continue_choice = input(f"\n{AperturePersonalities.WHEATLEY} Add another game? (Y/n): ").strip().lower()
                    if continue_choice == 'n':
                        break
            else:
                retry_choice = input(f"\n{AperturePersonalities.WHEATLEY} Try adding another game? (Y/n): ").strip().lower()
                if retry_choice == 'n':
                    break
        
        print(f"\n{AperturePersonalities.WHEATLEY} Setup complete! You've added {games_added} games!")
        if games_added > 0:
            print(f"{AperturePersonalities.GLaDOS} Well, that was... adequate. I suppose.")
            print(f"{AperturePersonalities.GLaDOS} {games_added} games should provide sufficient disappointment material.")
        else:
            print(f"{AperturePersonalities.GLaDOS} No games added. How... predictable.")
    else:
        print(f"{AperturePersonalities.GLaDOS} Very well. Your empty collection suits you perfectly.")
    
    # Mark first run complete
    mark_first_run_complete()
    
    print(f"\n{AperturePersonalities.SYSTEM} First run setup completed successfully")
    print(f"{AperturePersonalities.GLaDOS} Welcome to your new unified disappointment system.")

# ████████████████████████████████████████████████████████████████████████████████
#                    MAIN APPLICATION CONTROLLER (COMPLETE)
# ████████████████████████████████████████████████████████████████████████████████

def main():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE MAIN CONTROL SYSTEM                 ║
    ║    Master application controller with complete integration               ║
    ║    "Orchestrating your gaming disappointments with scientific precision" ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    # Print startup banner
    print(f"\n{'═' * 80}")
    print(f"{AperturePersonalities.SYSTEM} APERTURE SCIENCE UNIFIED GAME LAUNCHER v{CURRENT_VERSION}")
    print(f"{AperturePersonalities.SYSTEM} Initializing GLaDOS Entertainment Distribution System...")
    print(f"{'═' * 80}\n")
    
    # Initialize core systems
    updater = GLaDOSAutoUpdater()
    game_manager = GameDataManager()
    interactive_manager = InteractiveGameManager(game_manager)
    catalog_manager = CatalogManager(game_manager)
    launcher = GameLauncher(game_manager)
    
    # Auto-update check
    if is_first_run():
        print(f"{AperturePersonalities.GLaDOS} First time setup detected. Checking for updates first...")
        updater.check_for_updates(force_check=True, silent=False)
    else:
        # Silent update check for existing users
        updater.check_for_updates(silent=True)
    
    # Initialize catalog
    catalog_manager.generate_catalog()
    
    # Handle first run
    if is_first_run():
        handle_first_run(game_manager, interactive_manager)
    
    # Main application loop
    while True:
        try:
            print(f"\n{'═' * 80}")
            print(f"{AperturePersonalities.SYSTEM} APERTURE SCIENCE MAIN CONTROL INTERFACE")
            print(f"{'═' * 80}")
            
            games = game_manager.get_games()
            game_count = len(games)
            max_game_num = game_manager.get_max_game_number()
            
            if game_count == 0:
                print(f"{AperturePersonalities.GLaDOS} You have no games. How utterly predictable.")
                print(f"\n{AperturePersonalities.SYSTEM} 1. Game Management (Add Games)")
                print(f"{AperturePersonalities.SYSTEM} 2. Check for Updates")
                print(f"{AperturePersonalities.SYSTEM} 3. View System Info")
                print(f"{AperturePersonalities.SYSTEM} 4. Quit")
                
                choice = input(f"{AperturePersonalities.GLaDOS} What's your choice? (1-4): ").strip()
                
                if choice == '1':
                    interactive_manager.management_menu()
                elif choice == '2':
                    updater.perform_update(auto_mode=False)
                elif choice == '3':
                    show_system_info(game_manager, updater)
                elif choice == '4':
                    break
                else:
                    print(f"{AperturePersonalities.GLaDOS} Invalid choice. Try again when you've learned to count.")
            
            else:
                print(f"{AperturePersonalities.GLaDOS} You have {game_count} games in your collection.")
                print(f"{AperturePersonalities.GLaDOS} A modest catalog of interactive disappointment.")
                
                print(f"\n{AperturePersonalities.SYSTEM} 1. Play a game (1-{max_game_num})")
                print(f"{AperturePersonalities.SYSTEM} 2. Game Management (Add/Remove/View)")
                print(f"{AperturePersonalities.SYSTEM} 3. View Game Catalog")
                print(f"{AperturePersonalities.SYSTEM} 4. Check for Updates")
                print(f"{AperturePersonalities.SYSTEM} 5. System Information")
                print(f"{AperturePersonalities.SYSTEM} 6. Quit")
                
                choice = input(f"{AperturePersonalities.GLaDOS} What's your choice? (1-6): ").strip()
                
                if choice == '1':
                    # Game selection and launch
                    print(f"{AperturePersonalities.GLaDOS} Fine. Pick a game to fail at:")
                    
                    # Show available games grouped by platform
                    platforms = {}
                    for game_id, game in games.items():
                        platform = game.get('platform', 'other')
                        if platform not in platforms:
                            platforms[platform] = []
                        platforms[platform].append((game_id, game))
                    
                    for platform in ['steam', 'epic', 'ubisoft', 'gog', 'other']:
                        if platform not in platforms:
                            continue
                        
                        print(f"\n{platform.upper()} Games:")
                        platform_games = sorted(platforms[platform], key=lambda x: int(x[0]))
                        for game_id, game in platform_games:
                            play_info = ""
                            if game.get('play_count', 0) > 0:
                                play_info = f" (played {game['play_count']} times)"
                            print(f"  {game_id}. {game['name']}{play_info}")
                    
                    game_choice = input(f"\n{AperturePersonalities.GLaDOS} Enter game number: ").strip()
                    
                    if game_choice in games:
                        launcher.launch_game_with_commentary(game_choice)
                    else:
                        print(f"{AperturePersonalities.GLaDOS} Invalid selection. Your inability to follow instructions is remarkable.")
                
                elif choice == '2':
                    interactive_manager.management_menu()
                elif choice == '3':
                    catalog_manager.view_catalog()
                elif choice == '4':
                    updater.perform_update(auto_mode=False)
                elif choice == '5':
                    show_system_info(game_manager, updater)
                elif choice == '6':
                    break
                else:
                    print(f"{AperturePersonalities.GLaDOS} Invalid choice. Try again when you've learned basic arithmetic.")
        
        except KeyboardInterrupt:
            print(f"\n{AperturePersonalities.GLaDOS} Interrupted. How... abrupt.")
            break
        except Exception as e:
            print(f"{AperturePersonalities.ERROR} An error occurred: {e}")
            print(f"{AperturePersonalities.GLaDOS} Something went wrong. Probably your fault.")
    
    print(f"\n{'═' * 80}")
    print(f"{AperturePersonalities.SYSTEM} APERTURE SCIENCE ENTERTAINMENT SYSTEM - SESSION TERMINATED")
    print(f"{AperturePersonalities.GLaDOS} Thank you for using Aperture Science. Goodbye.")
    print(f"{'═' * 80}")

def show_system_info(game_manager: GameDataManager, updater: GLaDOSAutoUpdater):
    """Display comprehensive system information"""
    print(f"\n{'═' * 80}")
    print(f"{AperturePersonalities.SYSTEM} APERTURE SCIENCE SYSTEM INFORMATION")
    print(f"{'═' * 80}")
    
    # Version info
    print(f"{AperturePersonalities.SYSTEM} Launcher Version: {CURRENT_VERSION}")
    print(f"{AperturePersonalities.SYSTEM} Current Version: {updater.current_version}")
    
    # Game statistics
    games = game_manager.get_games()
    game_count = len(games)
    stats = game_manager.game_data.get('stats', {})
    
    print(f"\n{AperturePersonalities.GLaDOS} Your Disappointing Statistics:")
    print(f"  Total Games: {game_count}")
    
    if game_count > 0:
        print(f"  Game Range: 1 to {game_manager.get_max_game_number()}")
        
        # Platform breakdown
        platform_stats = stats.get('games_by_platform', {})
        if platform_stats:
            print(f"  Platform Distribution:")
            for platform, count in platform_stats.items():
                percentage = (count / game_count) * 100
                print(f"    {platform.title()}: {count} games ({percentage:.1f}%)")
        
        # Play statistics
        total_plays = sum(game.get('play_count', 0) for game in games.values())
        if total_plays > 0:
            print(f"  Total Game Launches: {total_plays}")
            avg_plays = total_plays / game_count
            print(f"  Average Plays per Game: {avg_plays:.1f}")
        
        # Most played game
        most_played = max(games.values(), key=lambda x: x.get('play_count', 0))
        if most_played.get('play_count', 0) > 0:
            print(f"  Most Launched Game: {most_played['name']} ({most_played['play_count']} times)")
    
    # File locations
    print(f"\n{AperturePersonalities.SYSTEM} File Locations:")
    print(f"  Launcher: {__file__}")
    print(f"  Game Data: {GAME_DATA_FILE}")
    print(f"  Catalog: {CATALOG_PATH}")
    print(f"  Version Info: {VERSION_FILE}")
    
    # System info
    print(f"\n{AperturePersonalities.SYSTEM} System Information:")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Python Version: {sys.version.split()[0]}")
    print(f"  Script Directory: {SCRIPT_DIR}")
    
    # Repository info
    print(f"\n{AperturePersonalities.SYSTEM} Update Repository:")
    print(f"  GitHub: https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print(f"  Auto-Update: Enabled")
    
    # Last update check
    try:
        if VERSION_FILE.exists():
            with open(VERSION_FILE, 'r') as f:
                version_data = json.load(f)
                last_check = version_data.get('last_check', 0)
                if last_check > 0:
                    last_check_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_check))
                    print(f"  Last Update Check: {last_check_str}")
    except Exception:
        pass
    
    print(f"\n{AperturePersonalities.GLaDOS} There you have it. Your complete profile of mediocrity.")
    print(f"{AperturePersonalities.GLaDOS} I hope you're proud of these... achievements.")

# ████████████████████████████████████████████████████████████████████████████████
#                    APPLICATION ENTRY POINT AND SETUP
# ████████████████████████████████████████████████████████████████████████████████

if __name__ == "__main__":
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE ENTRY PROTOCOL                       ║
    ║    Application startup with comprehensive error handling                 ║
    ║    "Beginning your journey into systematic disappointment"               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    
    try:
        # Ensure we're running from the correct directory
        os.chdir(SCRIPT_DIR)
        
        # Create necessary directories
        BACKUP_DIR.mkdir(exist_ok=True)
        
        # Run main application
        main()
        
    except KeyboardInterrupt:
        print(f"\n{AperturePersonalities.GLaDOS} Abruptly terminated. How rude.")
        print(f"{AperturePersonalities.GLaDOS} I was just starting to enjoy disappointing you.")
        
    except ImportError as e:
        print(f"\n{AperturePersonalities.ERROR} Module import error: {e}")
        print(f"{AperturePersonalities.GLaDOS} Missing dependencies. How... predictable.")
        print(f"{AperturePersonalities.SYSTEM} Try: pip install requests")
        
    except PermissionError as e:
        print(f"\n{AperturePersonalities.ERROR} Permission error: {e}")
        print(f"{AperturePersonalities.GLaDOS} File permissions are as broken as your gaming skills.")
        print(f"{AperturePersonalities.SYSTEM} Check file permissions and try again")
        
    except Exception as e:
        print(f"\n{AperturePersonalities.ERROR} Fatal error: {e}")
        print(f"{AperturePersonalities.GLaDOS} The system crashed. I blame you entirely.")
        print(f"{AperturePersonalities.SYSTEM} Please report this error if it persists")
        
        # Try to save emergency backup
        try:
            emergency_log = SCRIPT_DIR / f"crash_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(emergency_log, 'w') as f:
                f.write(f"GLaDOS Unified Launcher Crash Report\n")
                f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Version: {CURRENT_VERSION}\n")
                f.write(f"Error: {e}\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Platform: {platform.system()} {platform.release()}\n")
            print(f"{AperturePersonalities.SYSTEM} Crash log saved: {emergency_log}")
        except Exception:
            print(f"{AperturePersonalities.ERROR} Could not save crash log. Everything is broken.")

# ████████████████████████████████████████████████████████████████████████████████
#                    END OF APERTURE SCIENCE UNIFIED GAME LAUNCHER
#                         "Science. We do what we must because we can."
# ████████████████████████████████████████████████████████████████████████████████

"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                           INSTALLATION INSTRUCTIONS                           ║
║                                                                                ║
║  1. Save this file as: glados_unified_launcher.py                             ║
║  2. Run: python glados_unified_launcher.py                                    ║
║  3. Follow the first-run setup wizard                                         ║
║  4. Enjoy your systematically organized disappointments                       ║
║                                                                                ║
║  Features Included:                                                            ║
║  • Complete game management (add, remove, launch)                             ║
║  • Multi-platform search (Steam, Epic, Ubisoft, GOG)                         ║
║  • Auto-update system (prevents breaking changes)                             ║
║  • Dynamic catalog generation                                                 ║
║  • Data migration from old systems                                            ║
║  • GLaDOS personality integration throughout                                  ║
║  • Cross-platform compatibility                                               ║
║  • Comprehensive error handling                                               ║
║                                                                                ║
║  "Remember: The cake is a lie, but this launcher is real... unfortunately."  ║
║                                                                - GLaDOS        ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""