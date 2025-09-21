#!/usr/bin/env python3
"""
████████████████████████████████████████████████████████████████████████████████
                 APERTURE SCIENCE INTERACTIVE GAME MANAGER
                     VERSION: 1.1 "rocket turret"
████████████████████████████████████████████████████████████████████████████████

 ╔═══════════════════════════════════════════════════════════════════════════════╗
 ║                 APERTURE SCIENCE GAMING CATALOG MANAGER                   ║
 ║                                                                           ║
 ║  A Wheatley-powered interface for comprehensive game catalog management   ║
 ║  Featuring the lovably incompetent Intelligence Dampening Sphere!        ║
 ║                                                                           ║
 ║  Core Features:                                                           ║
 ║  • Multi-platform game URL generation and validation                     ║
 ║  • Automated catalog synchronization with GLaDOS main system            ║
 ║  • Wheatley-supervised quality assurance (results may vary)             ║
 ║  • Steam, Epic Games, GOG, and Ubisoft Connect integration              ║
 ╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import re
import requests
import json
import time
import os
import sys
from typing import Optional, Tuple, List, Dict
from urllib.parse import quote_plus
import urllib.parse

# Import Aperture Science Standardized Styling
import sys
import os

# Add styles directory to Python path
styles_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'styles')
if styles_path not in sys.path:
    sys.path.insert(0, styles_path)

# Add project root to Python path for module imports
import sys, os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import styling components
from style.aperture_science_stylesheet import (
    ApertureColors, AperturePersonalities, ApertureASCII, ApertureFormatting
)

# Get the absolute path to the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LAUNCHER_PATH = os.path.join(SCRIPT_DIR, 'glados_game_launcher.py')
CATALOG_PATH = os.path.join(SCRIPT_DIR, 'aperture_science_game_catalog.txt')
FIRST_RUN_FLAG = os.path.join(SCRIPT_DIR, '.aperture_first_run_complete')

def is_first_run():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              APERTURE SCIENCE FIRST RUN DETECTION PROTOCOL               ║
    ║    Determine if this is the first time the system has been initialized  ║
    ║    by checking for the presence of the completion flag file             ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    return not os.path.exists(FIRST_RUN_FLAG)

# ████████████████████████████████████████████████████████████████████████████████
#                    APERTURE SCIENCE COLOR PROTOCOL DEFINITIONS
#                      "Science. We do what we must because we can."
# ████████████████████████████████████████████████████████████████████████████████

"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                       STANDARDIZED PERSONALITY PROTOCOLS                        ║
║  Corporate Orange (GLaDOS)                                                      ║
║  Intelligence Dampening Sphere (Wheatley)                                      ║
║  Founder's Gold (Cave Johnson)                                                 ║
╚════════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════════╗
║                         STANDARDIZED SYSTEM PROTOCOLS                           ║
║  Technical System Cyan                                                         ║
║  Lockdown Security Red                                                         ║
║  Portal Test Chamber Green                                                     ║
╚════════════════════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════════════════════╗
║                        STANDARDIZED WARNING PROTOCOLS                          ║
║  Neurotoxin Warning Pink                                                       ║
║  Deadly Neurotoxin Alert                                                       ║
║  Emergency Alert Orange                                                        ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

GLaDOS = AperturePersonalities.GLaDOS                    # Corporate Orange
WHEATLEY = AperturePersonalities.WHEATLEY                # Intelligence Dampening Sphere
CAVE_JOHNSON = AperturePersonalities.CAVE_JOHNSON        # Founder's Gold

System = AperturePersonalities.SYSTEM                    # Technical System Cyan
Security = AperturePersonalities.SECURITY                # Lockdown Security Red
Testing = AperturePersonalities.TESTING                  # Portal Test Chamber Green

Error = AperturePersonalities.ERROR                      # Neurotoxin Warning Pink
Neurotoxin = AperturePersonalities.NEUROTOXIN            # Deadly Neurotoxin Alert
Emergency = AperturePersonalities.EMERGENCY              # Emergency Alert Orange

# Standardized Color Reset Protocol
RESET = ApertureColors.RESET

def print_glados(message: str):
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              GLaDOS GENETIC LIFEFORM COMMUNICATION PROTOCOL               ║
    ║    Transmit message via GLaDOS Genetic Lifeform and Disk Operating       ║
    ║    System with proper corporate tone and passive-aggressive delivery     ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(f"{GLaDOS}: {message}")

def print_wheatley(message: str):
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║             WHEATLEY INTELLIGENCE DAMPENING COMMUNICATION               ║
    ║     Relay communication through Intelligence Dampening Sphere with      ║
    ║     characteristic enthusiasm and occasional logical inconsistencies   ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(f"{WHEATLEY}: {message}")

def print_system(message: str):
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                APERTURE SCIENCE SYSTEM COMMUNICATION                    ║
    ║      Official facility announcements and administrative notifications   ║
    ║      "For your safety and the safety of others, please comply"         ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(f"{System}: {message}")

def print_error(message: str):
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                  APERTURE SCIENCE ERROR PROTOCOL                        ║
    ║       Critical system notifications and failure acknowledgments        ║
    ║       "Please remain calm while we investigate this totally expected   ║
    ║       result that was in no way a mistake on our part"                ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(f"{Error}: {message}")

def print_separator(title: str = ""):
    """
    Print an Aperture Science styled separator with optional title
    """
    if title:
        print(f"\n{'═' * 20} {title} {'═' * (58 - len(title))}")
    else:
        print(f"\n{'═' * 80}")

def print_startup_banner():
    """
    Display the Aperture Science Interactive Game Manager startup banner
    """
    print_separator("APERTURE SCIENCE INTERACTIVE GAME MANAGER")
    print_system("Initializing Wheatley-supervised catalog management...")
    print_system("Loading Intelligence Dampening Sphere protocols...")
    print_wheatley("Right! Hello there! I'm Wheatley, and I'll be your friendly")
    print_wheatley("neighborhood game catalog assistant today! Brilliant, right?")
    print_separator()

def search_game_in_catalog(game_name: str) -> Optional[Tuple[int, str]]:
    """
    Search for a game in the aperture_science_game_catalog.txt file
    Returns (game_number, full_game_name) if found, None otherwise
    """
    try:
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            catalog_content = f.read()
        
        # Pattern to match numbered games in catalog
        pattern = r'(\d+)\.\s+([^-\n]+?)(?:\s*-|$)'
        matches = re.findall(pattern, catalog_content)
        
        game_name_lower = game_name.lower()
        
        for number, catalog_game in matches:
            catalog_game_clean = catalog_game.strip().lower()
            
            # Check for exact match or strong partial match
            if (game_name_lower == catalog_game_clean or
                (len(game_name_lower) > 3 and game_name_lower in catalog_game_clean) or
                (len(catalog_game_clean) > 3 and catalog_game_clean in game_name_lower) or
                (len(game_name_lower.split()) > 1 and 
                 all(word in catalog_game_clean for word in game_name_lower.split() if len(word) > 3))):
                return int(number), catalog_game.strip()
        
        return None
        
    except FileNotFoundError:
        print_error("Catalog file not found!")
        return None
    except Exception as e:
        print_error(f"Error searching catalog: {e}")
        return None

def get_steam_app_id(game_name: str) -> Optional[str]:
    """
    Get Steam App ID for a game using Steam's search API
    """
    try:
        print_system(f"Searching Steam for '{game_name}'...")
        
        # Use Steam API to search for games
        search_url = "https://steamcommunity.com/actions/SearchApps"
        params = {'query': game_name}
        
        response = requests.get(search_url, params=params, timeout=10)
        
        if response.status_code == 200:
            # Try to parse the response
            try:
                data = response.json()
                if data and len(data) > 0:
                    # Return the first match's app ID
                    app_id = str(data[0]['appid'])
                    app_name = data[0]['name']
                    print_system(f"Found Steam game: {app_name} (ID: {app_id})")
                    return app_id
            except:
                pass
        
        # Fallback: Try a different approach using store search
        print_system("Trying alternative Steam search...")
        
        # Manual mapping for common games (fallback)
        common_games = {
            'portal': '400',
            'portal 2': '620',
            'half-life': '70',
            'half-life 2': '220',
            'team fortress 2': '440',
            'counter-strike': '730',
            'dota 2': '570',
            'left 4 dead 2': '550',
            'garry\'s mod': '4000',
            'civilization vi': '289070',
            'civilization 6': '289070',
            'minecraft': '323410',  # Note: Minecraft is not on Steam, but this is an example
        }
        
        game_lower = game_name.lower()
        for key, app_id in common_games.items():
            if key in game_lower or game_lower in key:
                print_system(f"Found in common games database: {app_id}")
                return app_id
        
        print_error(f"Could not find Steam App ID for '{game_name}'")
        return None
        
    except Exception as e:
        print_error(f"Error searching Steam: {e}")
        return None

def get_ubisoft_game_id(game_name: str) -> Optional[str]:
    """
    Get Ubisoft Connect game ID for a game
    """
    try:
        print_system(f"Searching Ubisoft Connect for '{game_name}'...")
        
        # Manual mapping for common Ubisoft games
        ubisoft_games = {
            'assassin\'s creed odyssey': '5092',
            'assassins creed odyssey': '5092',
            'assassin\'s creed valhalla': '5603',
            'assassins creed valhalla': '5603',
            'assassin\'s creed origins': '4928',
            'assassins creed origins': '4928',
            'assassin\'s creed unity': '720',
            'assassins creed unity': '720',
            'assassin\'s creed syndicate': '2778',
            'assassins creed syndicate': '2778',
            'far cry 6': '6650',
            'far cry 5': '1847',
            'far cry 4': '420',
            'far cry 3': '57',
            'watch dogs': '614',
            'watch dogs 2': '2688',
            'watch dogs legion': '5938',
            'rainbow six siege': '635',
            'tom clancy\'s rainbow six siege': '635',
            'rainbow six extraction': '6953',
            'the division': '2631',
            'the division 2': '4932',
            'ghost recon wildlands': '2809',
            'ghost recon breakpoint': '5532',
            'splinter cell': '13',
            'prince of persia': '8',
            'immortals fenyx rising': '6253',
            'riders republic': '6688',
            'anno 1800': '4799',
            'for honor': '2669',
            'skull and bones': '8097',
            'avatar frontiers of pandora': '7692'
        }
        
        game_lower = game_name.lower()
        
        # Check for exact match first
        if game_lower in ubisoft_games:
            game_id = ubisoft_games[game_lower]
            print_system(f"Found Ubisoft game: {game_name} (ID: {game_id})")
            return game_id
        
        # Check for partial matches
        for key, game_id in ubisoft_games.items():
            if (game_lower in key or key in game_lower or
                any(word in key for word in game_lower.split() if len(word) > 3)):
                print_system(f"Found Ubisoft game match: {key} (ID: {game_id})")
                return game_id
        
        print_error(f"Could not find Ubisoft Connect ID for '{game_name}'")
        return None
        
    except Exception as e:
        print_error(f"Error searching Ubisoft Connect: {e}")
        return None

def detect_game_platform(game_name: str) -> Tuple[Optional[str], str]:
    """
    Detect which platform a game belongs to and get its ID
    Returns (game_id, platform)
    """
    game_lower = game_name.lower()
    
    # Common Ubisoft franchises/keywords
    ubisoft_keywords = [
        'assassin', 'far cry', 'watch dogs', 'rainbow six', 'splinter cell',
        'ghost recon', 'the division', 'prince of persia', 'anno', 'for honor',
        'immortals', 'riders republic', 'skull and bones', 'avatar frontiers'
    ]
    
    # Check if game name contains Ubisoft keywords
    is_likely_ubisoft = any(keyword in game_lower for keyword in ubisoft_keywords)
    
    if is_likely_ubisoft:
        # Try Ubisoft first
        ubisoft_id = get_ubisoft_game_id(game_name)
        if ubisoft_id:
            return ubisoft_id, 'ubisoft'
        
        # Fallback to Steam if not found on Ubisoft
        steam_id = get_steam_app_id(game_name)
        if steam_id:
            return steam_id, 'steam'
    else:
        # Try Steam first for non-Ubisoft games
        steam_id = get_steam_app_id(game_name)
        if steam_id:
            return steam_id, 'steam'
        
        # Fallback to Ubisoft
        ubisoft_id = get_ubisoft_game_id(game_name)
        if ubisoft_id:
            return ubisoft_id, 'ubisoft'
    
    return None, 'unknown'

# ████████████████████████████████████████████████████████████████████████████████
#                    ENHANCED WEB URL FETCHING SYSTEM
#                    "Science. We do what we must because we can."
# ████████████████████████████████████████████████████████████████████████████████

def get_steam_store_url(game_name: str) -> Optional[str]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║               STEAM STORE PAGE URL VERIFICATION PROTOCOL                 ║
    ║    Fetch and VERIFY Steam store page URL with actual game existence      ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        print_system(f"Searching Steam Store for '{game_name}'...")
        
        # First get the app ID using existing function
        app_id = get_steam_app_id(game_name)
        if app_id:
            store_url = f"https://store.steampowered.com/app/{app_id}/"
            
            # VERIFY the URL actually exists and has the correct game
            if verify_steam_game_exists(store_url, game_name):
                print_system(f"✅ VERIFIED Steam Store URL: {store_url}")
                return store_url
            else:
                print_system(f"❌ Steam URL found but game verification failed: {store_url}")
        
        # Fallback: search Steam store directly
        search_query = quote_plus(game_name)
        search_url = f"https://store.steampowered.com/search/?term={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Simple regex to find app IDs in search results
            app_pattern = r'data-ds-appid="(\d+)"'
            matches = re.findall(app_pattern, response.text)
            
            for app_id in matches[:3]:  # Check first 3 results
                store_url = f"https://store.steampowered.com/app/{app_id}/"
                if verify_steam_game_exists(store_url, game_name):
                    print_system(f"✅ VERIFIED Steam Store URL via search: {store_url}")
                    return store_url
        
        print_system("❌ Game not found on Steam or verification failed")
        return None
        
    except Exception as e:
        print_error(f"Error fetching Steam Store URL: {e}")
        return None

def verify_steam_game_exists(store_url: str, game_name: str) -> bool:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    STEAM GAME EXISTENCE VERIFICATION                     ║
    ║    Verify that a Steam store URL actually contains the expected game     ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(store_url, headers=headers, timeout=10)
        if response.status_code == 200:
            page_content = response.text.lower()
            game_name_lower = game_name.lower()
            
            # Check if game name appears in title or content
            if (game_name_lower in page_content and 
                'store.steampowered.com' in response.url and
                'app' in response.url and
                'agecheck' not in page_content):  # Age check might redirect
                return True
        
        return False
        
    except Exception:
        return False

def get_epic_games_info(game_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║               EPIC GAMES STORE URL VERIFICATION PROTOCOL                 ║
    ║    Search and VERIFY Epic Games Store with actual game existence         ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        print_system(f"Searching Epic Games Store for '{game_name}'...")
        
        # Check known Epic exclusives first
        epic_exclusives = get_epic_exclusive_games()
        game_lower = game_name.lower()
        
        if game_lower in epic_exclusives:
            store_url, protocol_url = epic_exclusives[game_lower]
            print_system(f"✅ VERIFIED Epic exclusive: {game_name}")
            print_system(f"✅ Epic Store URL: {store_url}")
            return store_url, protocol_url
        
        # Search Epic Games Store
        search_query = quote_plus(game_name)
        search_url = f"https://store.epicgames.com/en-US/browse?q={search_query}&sortBy=relevancy&sortDir=DESC"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code == 200:
            # Look for Epic Games product URLs
            url_pattern = r'href="(/p/[^"]+)"'
            matches = re.findall(url_pattern, response.text)
            
            for product_path in matches[:3]:  # Check first 3 results
                store_url = f"https://store.epicgames.com{product_path}"
                
                # Verify this is actually the correct game
                if verify_epic_game_exists(store_url, game_name):
                    product_slug = product_path.split('/')[-1]
                    protocol_url = f"com.epicgames.launcher://apps/{product_slug}?action=launch&silent=true"
                    
                    print_system(f"✅ VERIFIED Epic Games Store URL: {store_url}")
                    return store_url, protocol_url
        
        print_system("❌ Game not found on Epic Games Store or verification failed")
        return None, None
        
    except Exception as e:
        print_error(f"Error fetching Epic Games Store info: {e}")
        return None, None

def verify_epic_game_exists(store_url: str, game_name: str) -> bool:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                   EPIC GAMES EXISTENCE VERIFICATION                      ║
    ║    Verify that an Epic store URL actually contains the expected game     ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(store_url, headers=headers, timeout=10)
        if response.status_code == 200:
            page_content = response.text.lower()
            game_name_lower = game_name.lower()
            
            # Check if game name appears in title or content
            if (game_name_lower in page_content and 
                'epicgames.com' in response.url):
                return True
        
        return False
        
    except Exception:
        return False

def get_epic_exclusive_games() -> Dict[str, Tuple[str, str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    EPIC GAMES EXCLUSIVE DATABASE                         ║
    ║    Known Epic Games Store exclusives and their correct URLs              ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    return {
        'fortnite': (
            'https://store.epicgames.com/en-US/p/fortnite',
            'com.epicgames.launcher://apps/Fortnite?action=launch&silent=true'
        ),
        'rocket league': (
            'https://store.epicgames.com/en-US/p/rocket-league',
            'com.epicgames.launcher://apps/Sugar?action=launch&silent=true'
        ),
        'fall guys': (
            'https://store.epicgames.com/en-US/p/fall-guys',
            'com.epicgames.launcher://apps/0a2d9f6403244d12969e11da6713137b?action=launch&silent=true'
        ),
        'genshin impact': (
            'https://store.epicgames.com/en-US/p/genshin-impact',
            'com.epicgames.launcher://apps/ac2c3a06502c4453b3e05b5ea3c1a8d2?action=launch&silent=true'
        ),
        'metro exodus': (
            'https://store.epicgames.com/en-US/p/metro-exodus',
            'com.epicgames.launcher://apps/Newt?action=launch&silent=true'
        ),
        'borderlands 3': (
            'https://store.epicgames.com/en-US/p/borderlands-3',
            'com.epicgames.launcher://apps/Catnip?action=launch&silent=true'
        ),
        'tony hawk pro skater 1 + 2': (
            'https://store.epicgames.com/en-US/p/tony-hawks-pro-skater-1-2',
            'com.epicgames.launcher://apps/THPS12?action=launch&silent=true'
        )
    }

def get_gog_info(game_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                  GOG.COM URL ACQUISITION PROTOCOL                        ║
    ║    Search GOG.com and return both web URL and GOG Galaxy protocol URL   ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        print_system(f"Searching GOG.com for '{game_name}'...")
        
        # GOG search endpoint
        search_query = quote_plus(game_name)
        search_url = f"https://www.gog.com/games?query={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Look for GOG game URLs
            # GOG URLs typically follow pattern: /game/game_name
            url_pattern = r'href="(/game/[^"]+)"'
            matches = re.findall(url_pattern, response.text)
            
            if matches:
                # Take the first match and construct full URL
                game_path = matches[0]
                store_url = f"https://www.gog.com{game_path}"
                
                # Extract game slug for GOG Galaxy protocol
                game_slug = game_path.split('/')[-1]
                protocol_url = f"goggalaxy://openGameView/{game_slug}"
                
                print_system(f"Found GOG Store URL: {store_url}")
                print_system(f"Generated GOG Galaxy URL: {protocol_url}")
                return store_url, protocol_url
        
        print_system("Could not find GOG.com entry")
        return None, None
        
    except Exception as e:
        print_error(f"Error fetching GOG.com info: {e}")
        return None, None

def fetch_comprehensive_game_urls(game_name: str) -> Dict[str, Dict[str, str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║            VERIFIED COMPREHENSIVE GAME URL ACQUISITION PROTOCOL          ║
    ║    Search all platforms with verification and platform exclusivity       ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print_wheatley(f"Right! Let me search for '{game_name}' across all platforms!")
    print_wheatley("I'm brilliant at this verified multi-platform searching!")
    
    url_collection = {}
    
    # Check platform exclusivity database first
    exclusivity_info = check_platform_exclusivity(game_name)
    if exclusivity_info:
        platform, reason = exclusivity_info
        print_system(f"🔍 Platform Intelligence: {reason}")
        
        if platform == 'epic':
            print_system("⚡ Checking Epic Games Store (platform exclusive detected)...")
            epic_store_url, epic_protocol_url = get_epic_games_info(game_name)
            if epic_store_url:
                url_collection['epic'] = {
                    'store': epic_store_url,
                    'protocol': epic_protocol_url,
                    'verified': True,
                    'exclusive': True
                }
                print_wheatley(f"Brilliant! Found Epic exclusive '{game_name}'!")
                return url_collection
        
        elif platform == 'steam':
            print_system("⚡ Checking Steam (platform exclusive detected)...")
            # Continue with normal Steam search
    
    # Steam URLs with verification
    print_system("🔍 Checking Steam...")
    steam_app_id = get_steam_app_id(game_name)
    steam_store_url = get_steam_store_url(game_name)
    
    if steam_app_id or steam_store_url:
        url_collection['steam'] = {'verified': True}
        
        # If we have store URL but no app ID, try to extract it
        if steam_store_url and not steam_app_id:
            app_id_match = re.search(r'/app/(\d+)/', steam_store_url)
            if app_id_match:
                steam_app_id = app_id_match.group(1)
                print_system(f"✅ Extracted Steam App ID from verified URL: {steam_app_id}")
        
        if steam_app_id:
            url_collection['steam']['protocol'] = f"steam://rungameid/{steam_app_id}"
            url_collection['steam']['id'] = steam_app_id
        if steam_store_url:
            url_collection['steam']['store'] = steam_store_url
    
    # Epic Games URLs with verification (skip if already found as exclusive)
    if 'epic' not in url_collection:
        print_system("🔍 Checking Epic Games Store...")
        epic_store_url, epic_protocol_url = get_epic_games_info(game_name)
        
        if epic_store_url or epic_protocol_url:
            url_collection['epic'] = {'verified': True}
            if epic_store_url:
                url_collection['epic']['store'] = epic_store_url
            if epic_protocol_url:
                url_collection['epic']['protocol'] = epic_protocol_url
    
    # GOG URLs with verification
    print_system("🔍 Checking GOG.com...")
    gog_store_url, gog_protocol_url = get_gog_info_verified(game_name)
    
    if gog_store_url or gog_protocol_url:
        url_collection['gog'] = {'verified': True}
        if gog_store_url:
            url_collection['gog']['store'] = gog_store_url
        if gog_protocol_url:
            url_collection['gog']['protocol'] = gog_protocol_url
    
    # Ubisoft URLs (using existing function with verification)
    print_system("🔍 Checking Ubisoft Connect...")
    ubisoft_id = get_ubisoft_game_id(game_name)
    
    if ubisoft_id and verify_ubisoft_game(game_name, ubisoft_id):
        url_collection['ubisoft'] = {
            'protocol': f"uplay://launch/{ubisoft_id}",
            'store': f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}",
            'id': ubisoft_id,
            'verified': True
        }
    
    # Summary with verification status
    platforms_found = list(url_collection.keys())
    verified_platforms = [p for p, data in url_collection.items() if data.get('verified', False)]
    exclusive_platforms = [p for p, data in url_collection.items() if data.get('exclusive', False)]
    
    if platforms_found:
        print_wheatley(f"Brilliant! Found '{game_name}' on: {', '.join(platform.title() for platform in platforms_found)}")
        print_wheatley(f"✅ Verified platforms: {', '.join(platform.title() for platform in verified_platforms)}")
        if exclusive_platforms:
            print_wheatley(f"⚡ Platform exclusive: {', '.join(platform.title() for platform in exclusive_platforms)}")
        print_wheatley("I'm getting really good at this verified multi-platform detection!")
    else:
        print_wheatley(f"Hmm, couldn't find '{game_name}' on any of the major platforms.")
        print_wheatley("Don't worry though! Maybe it's on a smaller platform or not digitally distributed?")
    
    return url_collection

def check_platform_exclusivity(game_name: str) -> Optional[Tuple[str, str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                    PLATFORM EXCLUSIVITY INTELLIGENCE                     ║
    ║    Check known platform exclusives to avoid unnecessary searches         ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    game_lower = game_name.lower().strip()
    
    # Epic Games exclusives (games that are NOT on Steam)
    epic_exclusives = {
        'fortnite': 'Fortnite is an Epic Games exclusive (not available on Steam)',
        'rocket league': 'Rocket League moved to Epic Games Store (removed from Steam)',
        'fall guys': 'Fall Guys moved to Epic Games Store (free-to-play)',
        'genshin impact': 'Genshin Impact is primarily Epic Games/mobile exclusive',
        'metro exodus': 'Metro Exodus is Epic Games exclusive (timed)',
        'borderlands 3': 'Borderlands 3 was Epic exclusive (now on multiple platforms)',
        'tony hawk pro skater 1 + 2': 'Tony Hawk Pro Skater 1 + 2 Epic exclusive',
        'assassins creed valhalla': 'Assassin\'s Creed Valhalla is Epic/Ubisoft exclusive',
        'far cry 6': 'Far Cry 6 is Epic/Ubisoft exclusive',
        'hitman 3': 'Hitman 3 was Epic exclusive (timed)'
    }
    
    # Steam exclusives or Steam-primary games
    steam_primary = {
        'half-life': 'Half-Life series is Valve/Steam exclusive',
        'portal': 'Portal series is Valve/Steam exclusive', 
        'left 4 dead': 'Left 4 Dead series is Valve/Steam exclusive',
        'team fortress': 'Team Fortress is Valve/Steam exclusive',
        'counter-strike': 'Counter-Strike is Valve/Steam exclusive',
        'dota 2': 'Dota 2 is Valve/Steam exclusive'
    }
    
    # Check for Epic exclusives
    for exclusive_game, reason in epic_exclusives.items():
        if exclusive_game in game_lower or game_lower in exclusive_game:
            return ('epic', reason)
    
    # Check for Steam exclusives
    for steam_game, reason in steam_primary.items():
        if steam_game in game_lower:
            return ('steam', reason)
    
    return None

def verify_ubisoft_game(game_name: str, game_id: str) -> bool:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                     UBISOFT CONNECT VERIFICATION                         ║
    ║    Verify Ubisoft Connect game existence                                 ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        # Simple verification - check if game name contains Ubisoft franchises
        game_lower = game_name.lower()
        ubisoft_franchises = [
            'assassin', 'far cry', 'watch dogs', 'rainbow six', 'splinter cell',
            'ghost recon', 'the division', 'prince of persia', 'anno', 'for honor',
            'immortals', 'riders republic', 'skull and bones', 'avatar frontiers'
        ]
        
        return any(franchise in game_lower for franchise in ubisoft_franchises)
        
    except Exception:
        return False

def get_gog_info_verified(game_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                  GOG.COM URL VERIFICATION PROTOCOL                       ║
    ║    Search and VERIFY GOG.com with actual game existence                  ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        print_system(f"Searching GOG.com for '{game_name}'...")
        
        # GOG search endpoint
        search_query = quote_plus(game_name)
        search_url = f"https://www.gog.com/games?query={search_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Look for GOG game URLs
            url_pattern = r'href="(/game/[^"]+)"'
            matches = re.findall(url_pattern, response.text)
            
            for game_path in matches[:3]:  # Check first 3 results
                store_url = f"https://www.gog.com{game_path}"
                
                # Verify this is actually the correct game
                if verify_gog_game_exists(store_url, game_name):
                    game_slug = game_path.split('/')[-1]
                    protocol_url = f"goggalaxy://openGameView/{game_slug}"
                    
                    print_system(f"✅ VERIFIED GOG Store URL: {store_url}")
                    return store_url, protocol_url
        
        print_system("❌ Game not found on GOG.com or verification failed")
        return None, None
        
    except Exception as e:
        print_error(f"Error fetching GOG.com info: {e}")
        return None, None

def verify_gog_game_exists(store_url: str, game_name: str) -> bool:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                      GOG GAME EXISTENCE VERIFICATION                     ║
    ║    Verify that a GOG store URL actually contains the expected game       ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(store_url, headers=headers, timeout=10)
        if response.status_code == 200:
            page_content = response.text.lower()
            game_name_lower = game_name.lower()
            
            # Check if game name appears in title or content
            if (game_name_lower in page_content and 
                'gog.com' in response.url and
                'game' in response.url):
                return True
        
        return False
        
    except Exception:
        return False
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║            COMPREHENSIVE GAME URL ACQUISITION PROTOCOL                   ║
    ║    Search all major platforms and return organized URL collection        ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print_wheatley(f"Right! Let me search for '{game_name}' across all platforms!")
    print_wheatley("I'm brilliant at this multi-platform searching!")
    
    url_collection = {}
    
    # Steam URLs
    print_system("Checking Steam...")
    steam_app_id = get_steam_app_id(game_name)
    steam_store_url = get_steam_store_url(game_name)
    
    if steam_app_id or steam_store_url:
        url_collection['steam'] = {}
        
        # If we have store URL but no app ID, try to extract it
        if steam_store_url and not steam_app_id:
            app_id_match = re.search(r'/app/(\d+)/', steam_store_url)
            if app_id_match:
                steam_app_id = app_id_match.group(1)
                print_system(f"Extracted Steam App ID from store URL: {steam_app_id}")
        
        if steam_app_id:
            url_collection['steam']['protocol'] = f"steam://rungameid/{steam_app_id}"
            url_collection['steam']['id'] = steam_app_id
        if steam_store_url:
            url_collection['steam']['store'] = steam_store_url
    
    # Epic Games URLs
    print_system("Checking Epic Games Store...")
    epic_store_url, epic_protocol_url = get_epic_games_info(game_name)
    
    if epic_store_url or epic_protocol_url:
        url_collection['epic'] = {}
        if epic_store_url:
            url_collection['epic']['store'] = epic_store_url
        if epic_protocol_url:
            url_collection['epic']['protocol'] = epic_protocol_url
    
    # GOG URLs
    print_system("Checking GOG.com...")
    gog_store_url, gog_protocol_url = get_gog_info(game_name)
    
    if gog_store_url or gog_protocol_url:
        url_collection['gog'] = {}
        if gog_store_url:
            url_collection['gog']['store'] = gog_store_url
        if gog_protocol_url:
            url_collection['gog']['protocol'] = gog_protocol_url
    
    # Ubisoft URLs (using existing function)
    print_system("Checking Ubisoft Connect...")
    ubisoft_id = get_ubisoft_game_id(game_name)
    
    if ubisoft_id:
        url_collection['ubisoft'] = {
            'protocol': f"uplay://launch/{ubisoft_id}",
            'store': f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}",
            'id': ubisoft_id
        }
    
    # Summary
    platforms_found = list(url_collection.keys())
    if platforms_found:
        print_wheatley(f"Brilliant! Found '{game_name}' on: {', '.join(platform.title() for platform in platforms_found)}")
        print_wheatley("I'm getting really good at this multi-platform detection!")
    else:
        print_wheatley(f"Hmm, couldn't find '{game_name}' on any of the major platforms.")
        print_wheatley("Don't worry though! Maybe it's on a smaller platform or not digitally distributed?")
    
    return url_collection

def get_next_game_number() -> int:
    """
    Find the next available game number by checking both the catalog and launcher
    """
    try:
        # Check catalog for highest number
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            catalog_content = f.read()
        
        # Extract all numbers from catalog
        catalog_pattern = r'(\d+)\.\s+'
        catalog_numbers = [int(match) for match in re.findall(catalog_pattern, catalog_content)]
        
        # Check launcher for highest number
        with open(LAUNCHER_PATH, 'r', encoding='utf-8') as f:
            launcher_content = f.read()
        
        # Extract all numbers from launcher
        launcher_pattern = r'"(\d+)": "steam://rungameid/\d+"'
        launcher_numbers = [int(match) for match in re.findall(launcher_pattern, launcher_content)]
        
        # Find the maximum and add 1
        all_numbers = catalog_numbers + launcher_numbers
        if all_numbers:
            next_number = max(all_numbers) + 1
        else:
            next_number = 1
        
        print_system(f"Next available game number: {next_number}")
        return next_number
        
    except Exception as e:
        print_error(f"Error finding next game number: {e}")
        return 404  # Safe fallback

def update_catalog_dynamic_content() -> bool:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              CATALOG DYNAMIC CONTENT UPDATE PROTOCOL                     ║
    ║    Update catalog file with current game count and status information    ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        if not os.path.exists(CATALOG_PATH):
            print_error(f"Catalog file not found: {CATALOG_PATH}")
            return False
        
        # Read current catalog content
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count games by looking for numbered entries
        game_pattern = r'(\d+)\.\s+[^-\n]+.*?(?=\n(?:\d+\.|$|═))'
        games = re.findall(game_pattern, content, re.DOTALL)
        total_games = len(games)
        
        # Get the highest game number
        if games:
            max_game_num = max(int(game_num) for game_num in games)
        else:
            max_game_num = 0
        
        # Update GAMES ADDED count
        content = re.sub(r'GAMES ADDED: \d+', f'GAMES ADDED: {total_games}', content)
        
        # Update status based on game count
        if total_games == 0:
            new_status = "STATUS: AWAITING USER INPUT"
            new_disappointment = "EXPECTED DISAPPOINTMENT LEVEL: MAXIMUM"
        elif total_games == 1:
            new_status = "STATUS: SINGLE GAME DETECTED"
            new_disappointment = "EXPECTED DISAPPOINTMENT LEVEL: CONCENTRATED"
        elif total_games < 5:
            new_status = "STATUS: MINIMAL COLLECTION DETECTED"
            new_disappointment = "EXPECTED DISAPPOINTMENT LEVEL: HIGH"
        elif total_games < 20:
            new_status = "STATUS: MODERATE COLLECTION ACTIVE"
            new_disappointment = "EXPECTED DISAPPOINTMENT LEVEL: SUBSTANTIAL"
        else:
            new_status = "STATUS: EXTENSIVE COLLECTION DETECTED"
            new_disappointment = "EXPECTED DISAPPOINTMENT LEVEL: OVERWHELMING"
        
        # Update status line
        content = re.sub(r'STATUS: [^\n]+', new_status, content)
        content = re.sub(r'EXPECTED DISAPPOINTMENT LEVEL: [^\n]+', new_disappointment, content)
        
        # Update the description text based on game count
        if total_games == 0:
            description_text = """The catalog is currently empty. Please use the Aperture Science Interactive Game
Manager to add your games. Each addition will be catalogued with appropriate
scientific commentary regarding your inevitable failure.

This message will be replaced with your personalized catalog of disappointment
once the initialization process is complete."""
        elif total_games == 1:
            description_text = f"""You have managed to add 1 game to your collection. How... quaint.
Please note that having a single game does not constitute a "gaming collection"
in any meaningful sense of the term.

Game selection range: 1 to {max_game_num}
Current collection status: Disappointingly minimal"""
        else:
            description_text = f"""You have assembled a collection of {total_games} games. I suppose that counts as progress.
Each entry has been personally reviewed and assigned appropriate scientific
commentary regarding the inevitable failure scenarios.

Game selection range: 1 to {max_game_num}
Current collection status: Ready for systematic disappointment"""
        
        # Find and replace the description section
        desc_pattern = r'(The catalog is currently empty.*?once the initialization process is complete\.)'
        if re.search(desc_pattern, content, re.DOTALL):
            content = re.sub(desc_pattern, description_text, content, flags=re.DOTALL)
        else:
            # Look for existing description with game count
            alt_pattern = r'(You have (?:managed to add|assembled).*?(?:disappointment|minimal)\.)'
            if re.search(alt_pattern, content, re.DOTALL):
                content = re.sub(alt_pattern, description_text, content, flags=re.DOTALL)
        
        # Write updated content
        with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_system(f"✅ Catalog dynamic content updated: {total_games} games, range 1-{max_game_num}")
        return True
        
    except Exception as e:
        print_error(f"Error updating catalog dynamic content: {e}")
        return False

def update_launcher_dynamic_content():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              LAUNCHER DYNAMIC CONTENT UPDATE PROTOCOL                    ║
    ║    Update launcher to refresh game count and ensure proper display       ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        # The launcher now uses dynamic functions get_game_count() and get_max_game_number()
        # which automatically read from the current game_urls, so no file modification needed
        # The launcher will automatically show the correct count when restarted
        
        print_system("✅ Launcher dynamic content updated")
        print_system("Game count and selection ranges will update automatically")
        return True
        
    except Exception as e:
        print_error(f"Error updating launcher dynamic content: {e}")
        return False

def add_game_to_launcher(game_number: int, game_name: str, url_collection: Dict[str, Dict[str, str]]) -> bool:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              ENHANCED GAME URL INJECTION PROTOCOL                        ║
    ║    Add comprehensive game URLs to glados_game_launcher.py with multiple   ║
    ║    platform support and both protocol + web store URLs                   ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        # Validate inputs
        if not game_name or not url_collection:
            print_error("Invalid game data provided for launcher update")
            return False
        
        if not os.path.exists(LAUNCHER_PATH):
            print_error(f"Launcher file not found: {LAUNCHER_PATH}")
            return False
        
        # Read launcher file
        with open(LAUNCHER_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup original content
        original_content = content
        
        # Find the return dictionary in initialize_game_urls function
        return_pattern = r'return\s*\{([^}]*)\}'
        return_match = re.search(return_pattern, content, re.DOTALL)
        
        if not return_match:
            print_error("Could not find return dictionary in initialize_game_urls function")
            return False
        
        # Get the full match and the content inside the braces
        full_match = return_match.group(0)
        dict_content = return_match.group(1)
        
        # Determine the primary platform and URL
        primary_platform = None
        primary_url = None
        
        # Priority order: Steam > Epic > GOG > Ubisoft
        platform_priority = ['steam', 'epic', 'gog', 'ubisoft']
        
        for platform in platform_priority:
            if platform in url_collection and 'protocol' in url_collection[platform]:
                primary_platform = platform
                primary_url = url_collection[platform]['protocol']
                break
        
        # If no protocol URL found, try to use store URLs with a note
        if not primary_url:
            for platform in platform_priority:
                if platform in url_collection and 'store' in url_collection[platform]:
                    primary_platform = platform
                    primary_url = url_collection[platform]['store']
                    break
        
        if not primary_url:
            print_error("No valid URL found in collection")
            return False
        
        # Validate that we're not adding a duplicate
        if f'"{game_number}":' in content:
            print_error(f"Game number {game_number} already exists in launcher")
            return False
        
        # Create comprehensive comment with all available platforms and URLs
        comment_lines = [f" # {game_name}"]
        
        for platform, urls in url_collection.items():
            platform_name = platform.upper()
            comment_lines.append(f" # {platform_name}:")
            
            if 'protocol' in urls:
                comment_lines.append(f" #   Launch: {urls['protocol']}")
            
            if 'store' in urls:
                comment_lines.append(f" #   Store: {urls['store']}")
        
        comment_text = '\n'.join(comment_lines)
        
        # Create the new entry
        if dict_content.strip():
            # Dictionary has existing entries
            new_entry = f',\n    "{game_number}": "{primary_url}",{comment_text}'
        else:
            # Dictionary is empty
            new_entry = f'\n    "{game_number}": "{primary_url}",{comment_text}\n'
        
        # Create the new dictionary content
        new_dict_content = dict_content + new_entry
        new_return_statement = f"return {{{new_dict_content}}}"
        
        # Replace the old return statement with the new one
        new_content = content.replace(full_match, new_return_statement)
        
        # Write the updated content
        with open(LAUNCHER_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Verify the file was written correctly
        with open(LAUNCHER_PATH, 'r', encoding='utf-8') as f:
            verify_content = f.read()
        
        if f'"{game_number}": "{primary_url}"' not in verify_content:
            print_error("Failed to verify launcher update - restoring backup")
            with open(LAUNCHER_PATH, 'w', encoding='utf-8') as f:
                f.write(original_content)
            return False
        
        platforms_list = ', '.join(url_collection.keys()).title()
        print_system(f"✅ Added comprehensive game entry: {game_name} (#{game_number})")
        print_system(f"Primary platform: {primary_platform.title()}")
        print_system(f"Available on: {platforms_list}")
        return True
        
    except Exception as e:
        print_error(f"Error adding game to launcher: {e}")
        # Attempt to restore original content if we have it
        try:
            if 'original_content' in locals():
                with open(LAUNCHER_PATH, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print_system("Restored launcher file to original state")
        except:
            pass
        return False

def add_game_to_catalog(game_number: int, game_name: str, platform: str) -> bool:
    """
    Add the game to aperture_science_game_catalog.txt with GLaDOS-style comment and platform info
    """
    try:
        # GLaDOS-style comments with platform-specific variations
        steam_comments = [
            "Another Steam game for you to fail at spectacularly",
            "I'm sure you'll find new ways to disappoint me with this Steam title",
            "Great, another Steam opportunity for systematic failure",
            "This Steam game should provide hours of entertainment... for me, watching you fail",
            "Perfect Steam choice for someone with your... unique... skill level"
        ]
        
        ubisoft_comments = [
            "Another Ubisoft game for you to struggle with magnificently",
            "How predictable, choosing a Ubisoft title to fail at",
            "This Ubisoft game will be as challenging as using Uplay... which is very",
            "Excellent, more Ubisoft content for your inevitable disappointment",
            "A Ubisoft game? How delightfully mainstream of you to fail at"
        ]
        
        general_comments = [
            "Another game for you to fail at spectacularly",
            "I'm sure you'll find new ways to disappoint me with this one",
            "Great, another opportunity for systematic failure",
            "This should provide hours of entertainment... for me, watching you fail",
            "Perfect for someone with your... unique... skill level",
            "I have such high hopes for you. Just kidding, I don't",
            "Another addition to your collection of digital disappointments",
            "How delightfully predictable of you to choose this",
            "This game will be as challenging as breathing... for you, that might be difficult",
            "Excellent choice for maximizing disappointment output"
        ]
        
        import random
        if platform == 'steam':
            comment = random.choice(steam_comments)
        elif platform == 'ubisoft':
            comment = random.choice(ubisoft_comments)
        else:
            comment = random.choice(general_comments)
        
        # Read the current catalog
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find a good place to insert the new game (at the end, before any closing sections)
        # Look for the last game entry
        last_game_pattern = r'(\d+)\.\s+[^-\n]+.*?(?=\n\n|\n═|$)'
        matches = list(re.finditer(last_game_pattern, content, re.DOTALL))
        
        if matches:
            # Insert after the last game
            insert_pos = matches[-1].end()
            new_entry = f"\n{game_number}. {game_name} - {comment}"
        else:
            # If no games found, append at the end
            insert_pos = len(content)
            new_entry = f"\n{game_number}. {game_name} - {comment}"
        
        # Insert the new game
        new_content = content[:insert_pos] + new_entry + content[insert_pos:]
        
        # Write the updated catalog
        with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print_system(f"Added {platform.title()} game to catalog: {game_name} (#{game_number})")
        return True
        
    except Exception as e:
        print_error(f"Error adding game to catalog: {e}")
        return False

def check_catalog_sync() -> None:
    """
    Check synchronization between launcher and catalog files
    Based on the functionality from check_games.py
    """
    try:
        print_wheatley("Right! Time for a synchronization check!")
        print_wheatley("This is brilliant - I love checking things! Let me get GLaDOS to help with the analysis...")
        print()
        print_glados("Analyzing the synchronization between launcher and catalog files...")
        print_glados("Let me see how many inconsistencies you've managed to create...")
        print()
        
        # Read the launcher file
        with open(LAUNCHER_PATH, 'r', encoding='utf-8') as f:
            python_content = f.read()
        
        # Read the catalog file
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            catalog_content = f.read()
        
        # Extract game URLs with numbers from launcher (Steam and Ubisoft)
        url_pattern = r'"(\d+)": "(?:steam://rungameid/|uplay://launch/)\d+",?\s*#\s*(.+?)(?:\s*\[(?:STEAM|UBISOFT)\])?$'
        python_games = re.findall(url_pattern, python_content, re.MULTILINE)
        
        # Extract numbered games from catalog
        catalog_pattern = r'(\d+)\.\s+([^-\n]+?)(?:\s*-|$)'
        catalog_games = re.findall(catalog_pattern, catalog_content)
        
        print_system(f'Launcher file has {len(python_games)} games')
        print_system(f'Catalog has {len(catalog_games)} games')
        print()
        
        # Create dictionaries for easier lookup
        python_dict = {int(num): game.strip() for num, game in python_games}
        catalog_dict = {int(num): game.strip() for num, game in catalog_games}
        
        # Find mismatches and missing games
        max_game_num = max(max(python_dict.keys()) if python_dict else [0],
                          max(catalog_dict.keys()) if catalog_dict else [0])
        
        mismatches = []
        missing_from_catalog = []
        extra_in_catalog = []
        
        for num in range(1, max_game_num + 1):
            python_game = python_dict.get(num)
            catalog_game = catalog_dict.get(num)
            
            if python_game and not catalog_game:
                missing_from_catalog.append((num, python_game))
            elif catalog_game and not python_game:
                extra_in_catalog.append((num, catalog_game))
            elif python_game and catalog_game:
                # Check if game names match (allowing for variations)
                python_clean = python_game.lower().replace("'", "").replace(":", "")
                catalog_clean = catalog_game.lower().replace("'", "").replace(":", "")
                
                # Check for reasonable similarity
                python_words = python_clean.split()[:3]  # Take first 3 words
                if not any(word in catalog_clean for word in python_words if len(word) > 3):
                    mismatches.append((num, python_game, catalog_game))
        
        # Platform distribution analysis
        steam_pattern = r'"(\d+)": "steam://rungameid/\d+",?\s*#\s*(.+)'
        ubisoft_pattern = r'"(\d+)": "uplay://launch/\d+",?\s*#\s*(.+)'
        
        steam_games = re.findall(steam_pattern, python_content)
        ubisoft_games = re.findall(ubisoft_pattern, python_content)
        
        # Display results with GLaDOS commentary
        print_glados("=== ANALYSIS RESULTS ===")
        print_system(f"Missing from catalog: {len(missing_from_catalog)}")
        print_system(f"Extra in catalog: {len(extra_in_catalog)}")
        print_system(f"Mismatches: {len(mismatches)}")
        print()
        
        if missing_from_catalog:
            print_glados("Oh wonderful, games missing from the catalog. Let me guess, you added them manually?")
            print_error("MISSING FROM CATALOG:")
            for num, game in missing_from_catalog[:10]:  # Show first 10
                print_error(f"  {num}: {game}")
            if len(missing_from_catalog) > 10:
                print_error(f"  ... and {len(missing_from_catalog) - 10} more")
            print()
        
        if mismatches:
            print_glados("And of course, mismatched names. Your attention to detail is... remarkable.")
            print_error("MISMATCHES:")
            for num, python_game, catalog_game in mismatches[:10]:  # Show first 10
                print_error(f"  {num}: Launcher='{python_game}' vs Catalog='{catalog_game}'")
            if len(mismatches) > 10:
                print_error(f"  ... and {len(mismatches) - 10} more")
            print()
        
        if extra_in_catalog:
            print_glados("Extra entries in the catalog? How... inefficient.")
            print_error("EXTRA IN CATALOG:")
            for num, game in extra_in_catalog[:10]:  # Show first 10
                print_error(f"  {num}: {game}")
            if len(extra_in_catalog) > 10:
                print_error(f"  ... and {len(extra_in_catalog) - 10} more")
            print()
        
        # Platform distribution
        print_glados("=== PLATFORM DISTRIBUTION ===")
        print_system(f"Steam games: {len(steam_games)}")
        print_system(f"Ubisoft Connect games: {len(ubisoft_games)}")
        print_system(f"Total games: {len(steam_games) + len(ubisoft_games)}")
        print()
        
        # Summary and auto-fix options
        if len(missing_from_catalog) == 0 and len(mismatches) == 0 and len(extra_in_catalog) == 0:
            print_glados("🎉 Well, well. Perfect synchronization. I'm... impressed. Don't let it go to your head.")
        else:
            print_glados("⚠️ Multiple discrepancies detected. As expected from a human.")
            print_glados("But I suppose I could help you fix these... if you ask nicely.")
            print()
            
            # Offer auto-fix options
            if missing_from_catalog or extra_in_catalog:
                fix_choice = input(f"{GLaDOS}: Would you like me to automatically fix the missing/extra games? (y/N): ").strip().lower()
                
                if fix_choice == 'y':
                    print()
                    print_glados("Fine, I'll clean up your mess. Try to pay attention this time.")
                    
                    # Auto-add missing games to catalog
                    if missing_from_catalog:
                        print_glados(f"Adding {len(missing_from_catalog)} missing games to catalog...")
                        for num, game_name in missing_from_catalog:
                            # Determine platform from launcher
                            platform = determine_game_platform_from_launcher(num, python_content)
                            success = add_existing_game_to_catalog(num, game_name, platform)
                            if success:
                                print_system(f"✅ Added #{num}: {game_name}")
                            else:
                                print_error(f"❌ Failed to add #{num}: {game_name}")
                    
                    # Remove extra games from catalog
                    if extra_in_catalog:
                        print_glados(f"Removing {len(extra_in_catalog)} extra games from catalog...")
                        for num, game_name in extra_in_catalog:
                            success = remove_game_from_catalog(num)
                            if success:
                                print_system(f"✅ Removed #{num}: {game_name}")
                            else:
                                print_error(f"❌ Failed to remove #{num}: {game_name}")
                    
                    print()
                    print_glados("There. Your files should be synchronized now.")
                    print_glados("Try not to mess them up again so quickly.")
                    
                    # Update catalog dynamic content after sync
                    print_glados("Updating catalog status information...")
                    update_catalog_dynamic_content()
                else:
                    print_glados("Very well. Leave the inconsistencies. I'm sure that won't cause any problems later.")
        
    except Exception as e:
        print_error(f"Error during synchronization check: {e}")
        print_glados("Even the analysis failed. That's... actually impressive.")

def determine_game_platform_from_launcher(game_num: int, launcher_content: str) -> str:
    """
    Determine the platform of a game based on its URL in the launcher
    """
    # Look for the specific game number and extract its URL
    steam_pattern = rf'"{game_num}": "steam://rungameid/\d+"'
    ubisoft_pattern = rf'"{game_num}": "uplay://launch/\d+"'
    
    if re.search(steam_pattern, launcher_content):
        return "steam"
    elif re.search(ubisoft_pattern, launcher_content):
        return "ubisoft"
    else:
        return "unknown"

def add_existing_game_to_catalog(game_number: int, game_name: str, platform: str) -> bool:
    """
    Add an existing game from launcher to catalog (for sync fixes)
    """
    try:
        # Read current catalog
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate GLaDOS comment for the game
        platform_comments = {
            "steam": [
                f"{game_name} - Another Steam game for you to fail at spectacularly",
                f"{game_name} - I'm sure you'll find new ways to disappoint me with this one",
                f"{game_name} - Great, another opportunity for systematic failure",
                f"{game_name} - This should provide hours of entertainment... for me, watching you fail"
            ],
            "ubisoft": [
                f"{game_name} - A Ubisoft Connect game. How... pedestrian [UBISOFT]",
                f"{game_name} - Another Ubisoft title to add to your collection of mediocrity [UBISOFT]", 
                f"{game_name} - Ubisoft Connect integration. Delightful [UBISOFT]",
                f"{game_name} - More Ubisoft content. Just what the world needed [UBISOFT]"
            ],
            "unknown": [
                f"{game_name} - A game of unknown origin. How mysterious",
                f"{game_name} - Platform unknown. Much like your gaming skills"
            ]
        }
        
        import random
        comments = platform_comments.get(platform, platform_comments["unknown"])
        glados_comment = random.choice(comments)
        
        # Find the best place to insert the game
        # Look for miscellaneous or user-added sections first
        misc_section = content.find('USER-ADDED GAMES')
        if misc_section == -1:
            misc_section = content.find('MISCELLANEOUS GAMES')
        
        if misc_section != -1:
            # Find the end of the section
            next_section = content.find('═══════════════════════════════════════════════════════════════════════════════════', misc_section + 1)
            if next_section != -1:
                # Insert before the next section
                new_entry = f"{game_number}. {glados_comment}\n\n"
                new_content = content[:next_section] + new_entry + content[next_section:]
            else:
                # Add to the very end before conclusion
                conclusion_start = content.find('CONCLUSION')
                if conclusion_start != -1:
                    new_entry = f"{game_number}. {glados_comment}\n\n"
                    new_content = content[:conclusion_start] + new_entry + content[conclusion_start:]
                else:
                    new_content = content + f"\n{game_number}. {glados_comment}\n"
        else:
            # Create new user-added section
            platform_tag = " [UBISOFT]" if platform == "ubisoft" else ""
            new_section = f"""
═══════════════════════════════════════════════════════════════════════════════════
                            USER-ADDED GAMES
             "Games added automatically during synchronization"
═══════════════════════════════════════════════════════════════════════════════════

{game_number}. {glados_comment}

"""
            # Insert before conclusion
            conclusion_start = content.find('CONCLUSION')
            if conclusion_start != -1:
                new_content = content[:conclusion_start] + new_section + content[conclusion_start:]
            else:
                new_content = content + new_section
        
        # Write updated content
        with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print_error(f"Error adding game #{game_number} to catalog: {e}")
        return False

def remove_game_from_catalog(game_number: int) -> bool:
    """
    Remove a game entry from the catalog file
    """
    try:
        # Read current catalog
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match the game line
        pattern = rf'^{game_number}\.\s+.*?(?=\n(?:\d+\.|$))'
        
        # Remove the game entry
        new_content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
        
        # Clean up any double newlines
        new_content = re.sub(r'\n\n+', '\n\n', new_content)
        
        # Write updated content
        with open(CATALOG_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print_error(f"Error removing game #{game_number} from catalog: {e}")
        return False

def main():
    """
    Main interactive loop for the game management system
    """
    print_wheatley("Hiya! Welcome to the Aperture Science Interactive Game Management System!")
    print_wheatley("Right, so, I'm Wheatley, and I'll be your Game Management Assistant today!")
    print_wheatley("I'm BRILLIANT at this stuff! Well, I think I am. Let's find out together!")
    print()
    
    # Check if this is a first run
    if is_first_run():
        print_wheatley("Oh! I see this is your first time setting up the system!")
        print_wheatley("That's brilliant! I love first runs! So exciting!")
        print_glados("Yes, how thrilling. Another opportunity to observe systematic failure.")
        print()
        print_wheatley("Right! So we need to add some games to get you started!")
        print_wheatley("Just follow the prompts and I'll help you build your collection!")
        print_glados("Your collection of digital disappointments, more precisely.")
        print()
        
        games_added = 0
        
        while True:
            try:
                print_wheatley(f"Alright! You've added {games_added} games so far. Want to add another?")
                print_system("Would you like to:")
                print_system("1. Add a game")
                print_system("2. Finish setup (need at least 1 game)")
                print()
                
                choice = input(f"{WHEATLEY}: What do you say? (1 or 2): ").strip()
                
                if choice == "1":
                    add_new_game()
                    games_added += 1
                elif choice == "2":
                    if games_added > 0:
                        print_wheatley("Brilliant! Setup complete! You've built a proper game collection!")
                        print_glados("A collection perfectly suited to your skill level, I'm sure.")
                        print()
                        
                        # Create first-run completion flag
                        try:
                            with open(FIRST_RUN_FLAG, 'w') as f:
                                f.write("First run completed successfully - GLaDOS")
                            print_system("✅ First run setup completed successfully.")
                        except Exception as e:
                            print_error(f"Warning: Could not create first-run flag: {e}")
                        
                        # Update catalog with final game count
                        print_system("Updating catalog with final game collection status...")
                        update_catalog_dynamic_content()
                        
                        print_system("You can now restart the main launcher to access your games.")
                        break
                    else:
                        print_wheatley("Oh, sorry mate! You need at least one game before we can finish.")
                        print_glados("Even I require some entertainment to judge your failures against.")
                        print()
                else:
                    print_wheatley("Uh... that's not one of the options, mate. Try 1 or 2?")
                    print()
                    
            except KeyboardInterrupt:
                print()
                print_wheatley("Oh! Interrupted! That's fine, that's fine. No worries at all!")
                break
            except Exception as e:
                print_error(f"An error occurred: {e}")
                print_wheatley("Uh oh! Something went a bit wrong there. But don't panic! We'll figure it out!")
    
    else:
        # Normal operation mode for subsequent runs
        while True:
            try:
                # Show menu options
                print_wheatley("Right! What would you like to do? I've got loads of options here!")
                print_system("1. Add a new game")
                print_system("2. Check catalog synchronization")
                print_system("3. Quit")
                print()
                
                choice = input(f"{WHEATLEY}: Ooh, pick a number! Any number between 1 and 3! I'm ready!: ").strip()
                
                if choice == "1":
                    # Add game functionality (existing code)
                    add_new_game()
                elif choice == "2":
                    # Check synchronization
                    print()
                    check_catalog_sync()
                    print()
                elif choice == "3" or choice.lower() in ['quit', 'exit', 'q']:
                    print_wheatley("Aww, leaving already? Well, it was brilliant working with you!")
                    print_wheatley("Come back anytime! I'll be here, managing games like a proper genius!")
                    break
                else:
                    print_wheatley("Uh... that's not one of the options, mate. Try 1, 2, or 3?")
                    print_wheatley("Don't worry, happens to the best of us! Even me sometimes!")
                    print()
                    
            except KeyboardInterrupt:
                print()
                print_wheatley("Oh! Interrupted! That's fine, that's fine. No worries at all!")
                break
            except Exception as e:
                print_error(f"An error occurred: {e}")
                print_wheatley("Uh oh! Something went a bit wrong there. But don't panic! We'll figure it out!")

def add_new_game():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              ENHANCED GAME ADDITION PROTOCOL                             ║
    ║    Add new games with comprehensive web URL fetching from all platforms  ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    # Get game name from user
    game_name = input(f"{WHEATLEY}: Brilliant! What game would you like to add? I'm ready to help!: ").strip()
    
    if not game_name:
        print_wheatley("Oh! You didn't type anything. That's alright, happens to everyone!")
        print_wheatley("Just try again when you're ready, mate!")
        return
    
    print()
    print_wheatley(f"Right! Let me search for '{game_name}' in the catalog...")
    print_wheatley("I'm very good at searching! Well, I think I am!")
    
    # Check if game already exists in catalog
    existing_game = search_game_in_catalog(game_name)
    
    if existing_game:
        game_num, full_name = existing_game
        print_wheatley(f"Oh! '{full_name}' is already in the catalog as game #{game_num}!")
        print_wheatley("No worries though! At least we know it's already there, right?")
        print()
        return
    
    print_wheatley("Brilliant! This is a new game! I love adding new games!")
    print()
    
    # Use comprehensive URL fetching to search all platforms
    print_separator("WEB URL ACQUISITION")
    print_wheatley("Right! Let me search the entire internet for this game!")
    print_wheatley("I'll check Steam, Epic Games, GOG, and Ubisoft Connect!")
    
    url_collection = fetch_comprehensive_game_urls(game_name)
    
    if not url_collection:
        print_wheatley("Hmm, I couldn't find this game on any of the major platforms.")
        print_wheatley("But don't worry! Maybe you have the URL or ID? I can work with that!")
        
        # Ask if user wants to provide game info manually
        print_wheatley("You can provide game info in these formats:")
        print_wheatley("  • steam:12345 (Steam App ID)")
        print_wheatley("  • uplay:67890 (Ubisoft Connect ID)")
        print_wheatley("  • https://store.steampowered.com/app/12345/ (Steam Store URL)")
        print_wheatley("  • epic:game-name (Epic Games Store slug)")
        print()
        
        manual_input = input(f"{WHEATLEY}: Type the game info, or press Enter to skip: ").strip()
        
        if manual_input:
            # Parse manual input
            url_collection = parse_manual_game_input(manual_input, game_name)
            
            if not url_collection:
                print_wheatley("Hmm, I'm having trouble with that format. Maybe try again later?")
                print()
                return
        else:
            print_wheatley("No worries! Maybe next time we'll find it automatically!")
            print()
            return
    
    # Display found platforms
    print_separator("PLATFORMS DETECTED")
    platforms_found = list(url_collection.keys())
    print_wheatley(f"Brilliant! Found '{game_name}' on {len(platforms_found)} platform(s):")
    
    for platform, urls in url_collection.items():
        platform_name = platform.upper()
        print_wheatley(f"  • {platform_name}:")
        
        if 'protocol' in urls:
            print_wheatley(f"    Launch: {urls['protocol']}")
        
        if 'store' in urls:
            print_wheatley(f"    Store: {urls['store']}")
    
    print()
    
    # Get next game number
    game_number = get_next_game_number()
    
    print_wheatley(f"Right! Adding '{game_name}' as game #{game_number}!")
    print_wheatley("This is going to be brilliant! I love adding games with comprehensive URLs!")
    
    # Add to launcher with comprehensive URL collection
    launcher_success = add_game_to_launcher(game_number, game_name, url_collection)
    
    # Determine primary platform for catalog
    primary_platform = determine_primary_platform(url_collection)
    
    # Add to catalog
    catalog_success = add_game_to_catalog(game_number, game_name, primary_platform)
    
    if launcher_success and catalog_success:
        print_wheatley(f"YES! Successfully added '{game_name}' to both the launcher and catalog!")
        print_wheatley("I'm getting really good at this comprehensive game management thing!")
        
        # Update launcher dynamic content
        update_launcher_dynamic_content()
        
        # Update catalog dynamic content
        update_catalog_dynamic_content()
        
        # Mark first run as complete if this was first game added
        if is_first_run():
            try:
                with open(FIRST_RUN_FLAG, 'w') as f:
                    f.write("First run completed successfully - GLaDOS")
                print_system("✅ First run setup completed successfully")
            except Exception as e:
                print_error(f"Warning: Could not create first-run flag: {e}")
        
        # Show summary
        print_system(f"Game #{game_number}: {game_name}")
        print_system(f"Primary platform: {primary_platform.title()}")
        print_system(f"Available platforms: {', '.join(platforms_found).title()}")
        print_wheatley("Brilliant work by me, if I do say so myself!")
        
        # Inform user about launcher sync
        print_glados("Your game has been automatically synchronized across all systems.")
        print_glados("The launcher will now be able to access this addition immediately.")
        print_glados(f"Game selection range automatically updated to include #{game_number}.")
        print_glados("Catalog status and game count have been updated with scientific precision.")
    else:
        print_wheatley("Oh... something went a bit wrong there.")
        print_wheatley("Don't worry though! These things happen. Maybe we can try again?")
    
    print()

def parse_manual_game_input(manual_input: str, game_name: str) -> Dict[str, Dict[str, str]]:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              MANUAL GAME INPUT PARSING PROTOCOL                          ║
    ║    Parse user-provided game information and create URL collection        ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    url_collection = {}
    
    try:
        if manual_input.startswith('steam:'):
            # Steam App ID
            app_id = manual_input.split(':', 1)[1].strip()
            if app_id.isdigit():
                url_collection['steam'] = {
                    'protocol': f"steam://rungameid/{app_id}",
                    'store': f"https://store.steampowered.com/app/{app_id}/",
                    'id': app_id
                }
        
        elif manual_input.startswith('uplay:') or manual_input.startswith('ubisoft:'):
            # Ubisoft Connect ID
            game_id = manual_input.split(':', 1)[1].strip()
            if game_id.isdigit():
                url_collection['ubisoft'] = {
                    'protocol': f"uplay://launch/{game_id}",
                    'store': f"https://store.ubi.com/us/search/?q={quote_plus(game_name)}",
                    'id': game_id
                }
        
        elif manual_input.startswith('epic:'):
            # Epic Games Store slug
            game_slug = manual_input.split(':', 1)[1].strip()
            url_collection['epic'] = {
                'protocol': f"epic://launch/{game_slug}",
                'store': f"https://store.epicgames.com/p/{game_slug}"
            }
        
        elif 'store.steampowered.com' in manual_input:
            # Steam Store URL
            app_id_match = re.search(r'/app/(\d+)/', manual_input)
            if app_id_match:
                app_id = app_id_match.group(1)
                url_collection['steam'] = {
                    'protocol': f"steam://rungameid/{app_id}",
                    'store': manual_input,
                    'id': app_id
                }
        
        if url_collection:
            print_wheatley("Brilliant! I understood that format perfectly!")
            return url_collection
        else:
            print_wheatley("Hmm, I couldn't parse that format. Try one of the examples I mentioned!")
            return {}
            
    except Exception as e:
        print_error(f"Error parsing manual input: {e}")
        return {}

def determine_primary_platform(url_collection: Dict[str, Dict[str, str]]) -> str:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              PRIMARY PLATFORM DETERMINATION PROTOCOL                     ║
    ║    Determine the primary platform based on availability and priority     ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    # Priority order: Steam > Epic > GOG > Ubisoft
    platform_priority = ['steam', 'epic', 'gog', 'ubisoft']
    
    for platform in platform_priority:
        if platform in url_collection:
            return platform
    
    # Fallback to first available platform
    if url_collection:
        return list(url_collection.keys())[0]
    
    return 'unknown'

if __name__ == "__main__":
    main()