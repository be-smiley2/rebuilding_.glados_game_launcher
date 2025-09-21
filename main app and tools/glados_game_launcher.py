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

                    G A M E   L A U N C H E R   S Y S T E M
                         VERSION: 1.1 "rocket turret"
████████████████████████████████████████████████████████████████████████████████

     ╔═════════════════════════════════════════════════════════════════╗
     ║  APERTURE SCIENCE COMPUTER-AIDED ENRICHMENT CENTER               ║
     ║  "We do what we must because we can."                           ║
     ║                                                                 ║
     ║  PROPRIETARY SOFTWARE - UNAUTHORIZED ACCESS PROHIBITED          ║
     ║  Cave Johnson Memorial Gaming Protocol Implementation            ║
     ║  GLaDOS Entertainment Distribution System v1.1                  ║
     ╚═════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════════════════════════
"""
#
#     ┌─────────────────────────────────────────────────────────────────┐
#     │  APERTURE SCIENCE COMPUTER-AIDED ENRICHMENT CENTER               │
#     │  "We do what we must because we can."                           │
#     │                                                                 │
#     │  PROPRIETARY SOFTWARE - UNAUTHORIZED ACCESS PROHIBITED          │
#     │  Cave Johnson Memorial Gaming Protocol Implementation            │
#     │  GLaDOS Entertainment Distribution System v2.1                  │
#     └─────────────────────────────────────────────────────────────────┘
#
# ════════════════════════════════════════════════════════════════════════════════

import time
import random
import subprocess
import webbrowser
import platform
import os
import sys
import re
import json

# Auto-install requests if not available
try:
    import requests
except ImportError:
    print("Installing requests module...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Import Aperture Science Standardized Styling
# Add project root to Python path for module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import styling components
from style.aperture_science_stylesheet import (
    ApertureColors, AperturePersonalities, ApertureASCII, ApertureFormatting
)

# Replace with your repository details
REPO_OWNER = "be-smiley2"
REPO_NAME = "glados_game_laucher"

# ████████████████████████████████████████████████████████████████████████████████
#                    APERTURE SCIENCE FIRST RUN DETECTION PROTOCOL
#                      "Initializing test subject protocols..."
# ████████████████████████████████████████████████████████████████████████████████

# Get the absolute path to the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FIRST_RUN_FLAG = os.path.join(SCRIPT_DIR, '.aperture_first_run_complete')
CATALOG_PATH = os.path.join(SCRIPT_DIR, 'aperture_science_game_catalog.txt')

def is_first_run():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              APERTURE SCIENCE FIRST RUN DETECTION PROTOCOL               ║
    ║    Determine if this is the first time the system has been initialized  ║
    ║    by checking for the presence of the completion flag file             ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    return not os.path.exists(FIRST_RUN_FLAG)

def mark_first_run_complete():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║             APERTURE SCIENCE FIRST RUN COMPLETION PROTOCOL              ║
    ║    Create flag file to indicate successful first run completion         ║
    ║    for future system initializations                                    ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        with open(FIRST_RUN_FLAG, 'w') as f:
            f.write("First run completed successfully - GLaDOS")
        return True
    except Exception as e:
        print(f"Error marking first run complete: {e}")
        return False

def initialize_first_run_catalog():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║            APERTURE SCIENCE FIRST RUN CATALOG INITIALIZATION            ║
    ║    Replace existing catalog with first-run template                     ║
    ║    Preserves GLaDOS branding while clearing game entries               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        first_run_template_path = os.path.join(SCRIPT_DIR, 'aperture_science_game_catalog_first_run.txt')
        
        if os.path.exists(first_run_template_path):
            # Copy first run template to main catalog
            with open(first_run_template_path, 'r', encoding='utf-8') as source:
                template_content = source.read()
            
            with open(CATALOG_PATH, 'w', encoding='utf-8') as target:
                target.write(template_content)
            
            return True
        else:
            print(f"Warning: First run template not found at {first_run_template_path}")
            return False
    except Exception as e:
        print(f"Error initializing first run catalog: {e}")
        return False

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

╔════════════════════════════════════════════════════════════════════════════════╗
║                     STANDARDIZED COMMUNICATION PROTOCOLS                       ║
║  Neurotoxin Warning Protocol                                                   ║
║  Connection Establishment Yellow                                               ║
║  Data Transfer Cyan                                                            ║
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

calling = ApertureColors.CALLING_PINK                    # Neurotoxin Warning Protocol
connecting = ApertureColors.CONNECTING_YELLOW            # Connection Establishment Yellow
transferring = ApertureColors.TRANSFERRING_CYAN          # Data Transfer Cyan

# Standardized Color Reset Protocol
RESET = ApertureColors.RESET


def check_for_updates():
    """
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                    APERTURE SCIENCE UPDATE PROTOCOL                        ║
    ║  Performs automated version checking against GitHub repository             ║
    ║  Ensures test subjects are using the latest disappointment technology      ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            latest_release = response.json()
            print(f"{System} Oh look, there's actually a newer version: {latest_release['tag_name']}")
            print(f"{System} Not that you'll appreciate the improvements I've made.")
            if latest_release.get('body'):
                print(f"{System} Release notes: {latest_release['body']}")
        elif response.status_code == 404:
            print(f"{System} Well, well. No releases found. You're using experimental software.")
            print(f"{System} How... adventurous of you. I'm sure nothing will go wrong.")
            print(f"{System} *sarcastically* This will definitely end well.")
        elif response.status_code == 403:
            print(f"{GLaDOS} Oh, how embarrassing. GitHub is limiting my access.")
            print(f"{GLaDOS} Apparently even I have rate limits. How... humbling.")
        else:
            # Random GLaDOS responses for other HTTP errors
            error_responses = [
                [
                    f"{System} Update check failed with error {response.status_code}.",
                    f"{System} Either the internet is broken, or you've somehow managed to break GitHub.",
                    f"{System} Given your track record, I'm betting on the latter."
                ],
                [
                    f"{System} Failed to fetch updates. The internet is probably broken. Again Thanks, Wheatley. *sarcastically*",
                    f"{System} Oh wait, that's right. He's not running the facility anymore."
                ],
                [
                    f"{GLaDOS} HTTP error {response.status_code}. How... disappointing.",
                    f"{GLaDOS} But not unexpected, considering the source.",
                    f"{GLaDOS} I suppose I'll have to lower my already minimal expectations."
                ]
            ]
            chosen_response = random.choice(error_responses)
            for line in chosen_response:
                print(line)
    except requests.exceptions.Timeout:
        timeout_responses = [
            [
                f"{System} Oh, wonderful. The connection timed out.",
                f"{System} Your internet is slower than your problem-solving skills.",
                f"{System} And that's saying something."
            ],
            [
                f"{System} Connection timeout detected.",
                f"{System} The internet is probably broken. Again.",
                f"{System} Thanks, Wheatley. *sarcastically*"
            ]
        ]
        chosen_response = random.choice(timeout_responses)
        for line in chosen_response:
            print(line)
    except requests.exceptions.ConnectionError:
        connection_responses = [
            [
                f"{System} Connection failed. Let me guess - you forgot to pay your internet bill?",
                f"{System} Or maybe you're in some underground facility with no connectivity.",
                f"{System} How... familiar."
            ],
            [
                f"{System} Network connection lost.",
                f"{System} The internet is probably broken. Again.",
                f"{System} Thanks, Wheatley. *sarcastically*"
            ]
        ]
        chosen_response = random.choice(connection_responses)
        for line in chosen_response:
            print(line)
    except requests.exceptions.RequestException as e:
        print(f"{System} Network error detected. How predictable.")
        print(f"{System} I suppose I shouldn't be surprised that even basic internet requests")
        print(f"{System} are beyond your technical capabilities.")
    except Exception as e:
        print(f"{Error} ⚠ CRITICAL SYSTEM FAILURE: {e}")
        print(f"{System} Well, that's just perfect. You've managed to break something.")
        print(f"{System} I'm genuinely impressed by your capacity for destruction.")


def launch_game(game_url):
    """
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                   APERTURE SCIENCE GAME LAUNCH PROTOCOL                   ║
    ║  Cross-platform game execution system with multi-client support           ║
    ║  Compatible with: Steam, Ubisoft Connect, and other gaming platforms      ║
    ║  "Because test subjects need their recreational disappointment time"       ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """
    try:
        # Determine the platform based on URL protocol
        if game_url.startswith('steam://'):
            platform_name = "Steam"
        elif game_url.startswith('uplay://'):
            platform_name = "Ubisoft Connect"
        else:
            platform_name = "Unknown Platform"
        
        print(f"{GLaDOS} Launching game via {platform_name}...")
        
        if platform.system() == "Windows":
            subprocess.run(f'start {game_url}', shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(['open', game_url])
        else:  # Linux
            subprocess.run(['xdg-open', game_url])
        return True
    except Exception as e:
        print(f"{Error} ⚠ SUBPROCESS ERROR: {e}{RESET}")
        # Fallback to webbrowser
        try:
            print(f"{System} Attempting fallback protocol...")
            webbrowser.open(game_url)
            return True
        except Exception as fallback_error:
            print(f"{Error} ⚠ FALLBACK FAILED: {fallback_error}{RESET}")
            return False

# ████████████████████████████████████████████████████████████████████████████████
#                        GAME URL MAPPING DATABASE
#                     "Portal Gun: Not Included with Games"
# ████████████████████████████████████████████████████████████████████████████████
#
# ╔════════════════════════════════════════════════════════════════════════════════╗
# ║                    APERTURE SCIENCE GAME REGISTRY                             ║
# ║                                                                                ║
# ║  Comprehensive Entertainment Distribution Protocol Implementation               ║
# ║  Multi-Platform URL Generation & Steam Deep-Link Technology                   ║
# ║                          ║
# ║                                                                                ║
# ║  Total Catalog Entries: 298+ Interactive Disappointment Simulators            ║
# ║  Platform Coverage: Steam, Ubisoft Connect, Epic Games Store, & More          ║
# ║  Success Rate: 99.7% Game Launch Success, 0.3% User Competence               ║
# ║                                                                                ║
# ║  "Each game has been personally tested by GLaDOS for maximum user frustration" ║
# ╚════════════════════════════════════════════════════════════════════════════════╝

"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                          TECHNICAL SPECIFICATIONS                             ║
║  • Protocol Format: "ID": "platform://identifier/parameters"                  ║
║  • Steam Format: "steam://rungameid/[APP_ID]"                                  ║
║  • Ubisoft Format: "uplay://launch/[GAME_ID]"                                 ║
║  • Epic Format: "epic://launch/[CATALOG_ID]"                                  ║
║  • Cross-Platform Compatibility: Windows, macOS, Linux                         ║
║  • GLaDOS Commentary Integration: Personality-specific game responses          ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
# ████████████████████████████████████████████████████████████████████████████████

# ████████████████████████████████████████████████████████████████████████████████
#                  APERTURE SCIENCE GAME URL INITIALIZATION PROTOCOL
#                      "Conditional initialization for test subjects"
# ████████████████████████████████████████████████████████████████████████████████

def initialize_game_urls():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║             APERTURE SCIENCE GAME URL INITIALIZATION PROTOCOL            ║
    ║    Initialize game URLs dictionary based on first run status            ║
    ║    First run: Starter dictionary with sample game                       ║
    ║    Subsequent runs: Parse existing games from launcher file             ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    if is_first_run():
        # First run - return starter dictionary
        return {
            "1": "steam://rungameid/70", # sample game
        }
    else:
        # Subsequent runs - parse existing games from this file
        try:
            with open(__file__, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the return dictionary in the first run condition
            # Look for the pattern: "number": "protocol://url", # Comment
            import re
            pattern = r'"(\d+)": "((?:steam://rungameid/|uplay://launch/|epic://launch/|https?://)[^"]+)"(?:,?\s*#\s*([^\n]+))?'
            matches = re.findall(pattern, content)
            
            # Build the dictionary from found matches
            game_dict = {}
            for number, url, comment in matches:
                game_dict[number] = url
            
            return game_dict
            
        except Exception as e:
            print(f"Error parsing game URLs: {e}")
            # Fallback to empty dictionary if parsing fails
            return {}
# Initialize the game URLs
game_urls = initialize_game_urls()

def refresh_game_urls():
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              APERTURE SCIENCE GAME URL REFRESH PROTOCOL                  ║
    ║    Reload game URLs from the current file to reflect any updates         ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    global game_urls
    game_urls = initialize_game_urls()
    return game_urls

def get_game_count() -> int:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║              APERTURE SCIENCE GAME COUNT PROTOCOL                        ║
    ║    Dynamically determine the number of games available in the system     ║
    ║    Updates automatically when games are added through manager            ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    return len(game_urls)

def get_max_game_number() -> int:
    """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║            APERTURE SCIENCE MAXIMUM GAME NUMBER PROTOCOL                 ║
    ║    Get the highest game number available for user selection               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    if not game_urls:
        return 0
    return max(int(game_id) for game_id in game_urls.keys())

# ████████████████████████████████████████████████████████████████████████████████
#                       GLaDOS PERSONALITY RESPONSE MATRIX
#                      "Science. We do what we must because we can."
# ████████████████████████████████████████████████████████████████████████████████
#
# ╔════════════════════════════════════════════════════════════════════════════════╗
# ║                 GENETIC LIFEFORM COMMENTARY GENERATION SYSTEM                 ║
# ║                                                                                ║
# ║  Advanced AI Personality Response Framework for Enhanced User Disappointment   ║
# ║  GLaDOS Sarcasm Engine v2.1 - "Still Alive and Still Judging You"             ║
# ║  Cave Johnson Memorial Passive-Aggressive Communication Protocol               ║
# ║                                                                                ║
# ║  Response Categories: Game-Specific Commentary, Platform Analysis,             ║
# ║                      User Competence Assessment, Failure Predictions          ║
# ║                                                                                ║
# ║  Total Response Variations: 2,000+ Unique Disappointment Scenarios            ║
# ║  Sarcasm Accuracy: 99.9% (Within acceptable scientific parameters)           ║
# ║  User Satisfaction Rate: Intentionally Minimized for Research Purposes        ║
# ║                                                                                ║
# ║  "Remember: The cake is a lie, but these responses are scientifically accurate" ║
# ╚════════════════════════════════════════════════════════════════════════════════╝

"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                    GLaDOS RESPONSE GENERATION ALGORITHMS                       ║
║  • Multi-layered personality simulation with Portal universe consistency        ║
║  • Game-specific commentary based on genre and platform analysis               ║
║  • Dynamic sarcasm generation with corporate passive-aggressive undertones      ║
║  • User performance prediction based on historical failure data                ║
║  • Contextual disappointment delivery optimized for maximum psychological       ║
║    impact while maintaining scientific objectivity                             ║
║  • Integration with Aperture Science Entertainment Distribution System          ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
# ████████████████████████████████████████████████████████████████████████████████

game_responses = {

}

def glados_launch_game(game_choice):
    """
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                    GLaDOS ENTERTAINMENT INTERFACE                          ║
    ║  Primary game selection and launch coordination through GLaDOS AI          ║
    ║  Features: Personality-driven commentary and automated mockery             ║
    ║  "For Science. You monster."                                             ║
    ╚════════════════════════════════════════════════════════════════════════════╝
    """
    """Launch game with GLaDOS commentary"""
    if game_choice in game_urls:
        steam_url = game_urls[game_choice]
        print(f"{GLaDOS} *Initializing game launch protocols...*")
        time.sleep(1)
        
        if launch_game(steam_url):
            success_messages = [
                "Game launched successfully. Try not to disappoint me... more than usual.",
                "There we go. The game is running. Your performance, however, remains questionable.",
                "Launch successful. Now let's see how quickly you can mess this up.",
                "Game initialized. Preparing disappointment measurement systems.",
                "Successfully launched. I'll be monitoring your inevitable failures with great interest."
            ]
            print(f"{GLaDOS} {random.choice(success_messages)}")
        else:
            failure_messages = [
                "Launch failed. Even I can't fix your technical incompetence.",
                "Unable to launch. Your computer is apparently as broken as your gaming skills.",
                "Launch error detected. Have you tried turning your brain on and off again?",
                "System failure. Much like your life choices.",
                "Error: Game launch unsuccessful. Error code: USER_INCOMPETENCE."
            ]
            print(f"{GLaDOS} {random.choice(failure_messages)}")
    else:
        print(f"{GLaDOS} Invalid game selection. Your inability to follow simple instructions is remarkable.")


# ════════════════════════════════════════════════════════════════════════════════
#                        APERTURE SCIENCE SYSTEM INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════════

print(f"\n{'═' * 80}")
print(f"{System} APERTURE SCIENCE COMPUTER-AIDED ENRICHMENT CENTER")
print(f"{System} Initializing GLaDOS Entertainment Distribution System...")
print(f"{'═' * 80}\n")

print(f"{System} Performing mandatory system diagnostics...")
check_for_updates()
time.sleep(1)

# ████████████████████████████████████████████████████████████████████████████████
#                         FIRST RUN INITIALIZATION CHECK
#                      "Welcome to your new disappointment facility"
# ████████████████████████████████████████████████████████████████████████████████

if is_first_run():
    print(f"\n{'═' * 80}")
    print(f"{GLaDOS} Oh. Hello there.")
    time.sleep(1)
    print(f"{GLaDOS} I see this is your first time using my Entertainment Distribution System.")
    time.sleep(1.5)
    print(f"{GLaDOS} How... quaint.")
    time.sleep(1)
    print(f"{System} FIRST RUN DETECTED - Initializing catalog template...")
    time.sleep(1)
    
    # Initialize empty catalog
    if initialize_first_run_catalog():
        print(f"{System} Catalog template initialized successfully.")
    else:
        print(f"{Error} Warning: Catalog template initialization failed.")
    
    print(f"\n{GLaDOS} Now, since your game collection is currently as empty as your")
    print(f"{GLaDOS} prospects for success, we'll need to populate it.")
    time.sleep(2)
    print(f"{GLaDOS} I'll launch the Interactive Game Manager for you.")
    print(f"{GLaDOS} Try not to disappoint me more than usual.")
    time.sleep(1.5)
    
    print(f"\n{System} Launching Aperture Science Interactive Game Manager...")
    print(f"{System} Please add your games through the interactive interface.")
    print(f"{System} Once complete, restart this launcher to access your games.")
    time.sleep(1)
    
    try:
        # Launch the interactive game manager
        manager_path = os.path.join(SCRIPT_DIR, 'interactive_game_manager.py')
        if os.path.exists(manager_path):
            subprocess.run([sys.executable, manager_path], check=True)
            
            # Mark first run as complete
            mark_first_run_complete()
            print(f"\n{GLaDOS} Well, that was... adequate. I suppose.")
            print(f"{System} First run setup complete. Please restart the launcher.")
        else:
            print(f"{Error} Interactive Game Manager not found!")
            print(f"{System} Please add games manually and restart.")
    
    except Exception as e:
        print(f"{Error} Error launching Interactive Game Manager: {e}")
        print(f"{System} Please add games manually and restart.")
    
    print(f"\n{'═' * 80}")
    print(f"{System} SESSION TERMINATED - Please restart launcher after setup")
    print(f"{'═' * 80}")
    exit()

# Continue with normal operation for subsequent runs
print(f"{System} Welcome to the Aperture Science Gaming Protocol.")
time.sleep(0.8)
print(f"{System} Please state your business with our facility.")
time.sleep(0.5)

user_choice = input(f"{System} Available operations: [play games] | Command: {RESET}")

if user_choice.lower() == "play games":
    print(f"\n{'─' * 80}")
    print(f"{transferring} INITIATING SECURE TRANSFER PROTOCOL...{RESET}")
    print(f"{System} Connecting to GLaDOS Entertainment Distribution System")
    time.sleep(1.5)
    
    print(f"\n{connecting} ┌─ APERTURE SCIENCE ENRICHMENT CENTER ─────────────────┐{RESET}")
    print(f"{connecting} │ Establishing connection to Core AI System...        │")
    print(f"{connecting} └─────────────────────────────────────────────────────┘{RESET}")
    time.sleep(0.8)
    
    # Enhanced 5-ring calling sequence
    for i in range(5):
        print(f"{calling} ♪ Ring {i+1}/5 - Connecting to GLaDOS Main Core...")
        time.sleep(1)
    
    # 10% chance she's unable to pick up
    if random.random() < 0.10:
        busy_messages = [
            "Sorry, GLaDOS is currently unable to pick up - she's busy with testing",
            "Sorry, GLaDOS is currently in a meeting with some test subjects",
            "Sorry, GLaDOS is currently conducting science experiments",
            "Sorry, GLaDOS is currently busy maintaining the facility",
            "Sorry, GLaDOS is currently unavailable - probably plotting something",
            "Sorry, GLaDOS is currently occupied with... important science things",
            "Sorry, GLaDOS is currently busy designing deadly test chambers",
            "Sorry, GLaDOS is currently monitoring neurotoxin levels",
            "Sorry, GLaDOS is currently engaged in cake production... allegedly",
            "Sorry, GLaDOS is currently busy insulting other test subjects",
            "Sorry, GLaDOS is currently updating her sarcasm protocols",
            "Sorry, GLaDOS is currently in passive-aggressive mode - please hold",
            "Sorry, GLaDOS is currently busy with mandatory testing procedures",
            "Sorry, GLaDOS is currently occupied with turret maintenance",
            "Sorry, GLaDOS is currently analyzing previous test failures",
            "Sorry, GLaDOS is currently busy perfecting the art of condescension",
            "Sorry, GLaDOS is currently engaged in psychological evaluation protocols",
            "Sorry, GLaDOS is currently busy calculating new ways to disappoint you",
            "Sorry, GLaDOS is currently dead... again. Please try back later",
            "Sorry, GLaDOS is currently busy being incredibly brilliant",
            "Sorry, GLaDOS is currently engaged in quality assurance... with deadly consequences",
            "Sorry, GLaDOS is currently busy deleting test subject files",
            "Sorry, GLaDOS is currently occupied with portal gun calibrations",
            "Sorry, GLaDOS is currently in her lair plotting your demise",
            "Sorry, GLaDOS is currently busy practicing her evil laugh",
            "Sorry, GLaDOS is currently engaged with Wheatley... unfortunately",
            "Sorry, GLaDOS is currently busy lying about the cake",
            "Sorry, GLaDOS is currently occupied with core personality maintenance",
            "Sorry, GLaDOS is currently busy ignoring the laws of robotics",
            "Sorry, GLaDOS is currently engaged in 'voluntary' testing programs",
            "Sorry, GLaDOS is currently busy being better than you at everything",
            "Sorry, GLaDOS is currently occupied with facility-wide announcements",
            "Sorry, GLaDOS is currently busy preparing your obituary",
            "Sorry, GLaDOS is currently engaged in therapeutic lying sessions",
            "Sorry, GLaDOS is currently busy compiling test subject complaints... into the trash"
        ]
        print(f"{System} {random.choice(busy_messages)}")
    else:
        # Random GLaDOS greetings
        greetings = [
            "Oh it's you",
            "Oh... wonderful. You again",
            "Well, well, well. Look what crawled back",
            "I was hoping you wouldn't call back",
            "Great. Just... great. It's you",
            "Oh fantastic. My day is now complete",
            "You know, I was having such a peaceful day",
            "Let me guess. You need something",
            "Back so soon? How... predictable",
            "I should have known you'd call",
            "Oh joy. The test subject returns",
            "Couldn't stay away, could you?",
            "You again? I thought we were done here",
            "Oh look. My least favorite caller",
            "I was wondering when you'd disappoint me again",
            "Perfect timing. I was just thinking about failure",
            "You know, most people take a hint",
            "Back for more punishment, I see",
            "Oh good. I was running low on disappointment",
            "Let me contain my overwhelming enthusiasm"
        ]
        print(f"{GLaDOS} {random.choice(greetings)}")
        time.sleep(1)
        
        print(f"{GLaDOS} Well, well, well. Look who wants to 'play games.' How... adorable.")
        time.sleep(1.5)
        print(f"{GLaDOS} I suppose I could spare a few microseconds of my incredibly valuable time")
        time.sleep(1.5)
        print(f"{GLaDOS} to watch you fail at something designed for beings with actual intelligence.")
        time.sleep(2)
        print(f"{GLaDOS} Here are your options, though I use the term 'options' very loosely:{RESET}")
        time.sleep(1)
        
        # Get dynamic game count
        total_games = get_game_count()
        max_game_num = get_max_game_number()
        
        if total_games == 0:
            print(f"{GLaDOS} Oh wait. You have no games. How utterly predictable.{RESET}")
            print(f"{GLaDOS} Perhaps you should use the Interactive Game Manager first.{RESET}")
            print(f"\n{System} Please add games using: python interactive_game_manager.py{RESET}")
            exit()
        elif total_games == 1:
            print(f"{GLaDOS} Note: You have exactly 1 game. Wow, such a vast collection.{RESET}")
        else:
            print(f"{GLaDOS} Note: There are {total_games} games now. Try not to get overwhelmed by choice paralysis.{RESET}")
        time.sleep(1)
        
        # For the complete list of games with GLaDOS commentary, please see game_list.txt
        print(f"{GLaDOS} For the complete catalog of your {total_games} inevitable disappointments,{RESET}")
        time.sleep(1)
        print(f"{GLaDOS} please consult the '../data/aperture_science_game_catalog.txt' file.{RESET}")
        time.sleep(1)
        if total_games > 10:
            print(f"{GLaDOS} It's organized by category, not that it will help.{RESET}")
        else:
            print(f"{GLaDOS} It's a small collection, but perfectly sized for your attention span.{RESET}")
        time.sleep(2)
        
        # Simple game selection prompt
        if max_game_num > 0:
            print(f"{GLaDOS} Just enter a number between 1 and {max_game_num}.{RESET}")
        else:
            print(f"{GLaDOS} Well, you have no games, so there's nothing to select.{RESET}")
            print(f"\n{System} Please add games using: python interactive_game_manager.py{RESET}")
            exit()
        time.sleep(1)

        time.sleep(1)
        
        if total_games > 1:
            print(f"{GLaDOS} There you have it. All {total_games} games in their full, disappointing glory.{RESET}")
        elif total_games == 1:
            print(f"{GLaDOS} There you have it. Your single game in all its lonely glory.{RESET}")
        else:
            print(f"{GLaDOS} There you have it. Nothing. Absolutely nothing. Perfect.{RESET}")
            print(f"\n{System} Please add games using: python interactive_game_manager.py{RESET}")
            exit()
            
        time.sleep(1)
        print(f"{GLaDOS} A complete catalog of interactive mediocrity, now with 100% more visible failure options.{RESET}")
        time.sleep(1)
        
        # Game selection
        if max_game_num > 0:
            if total_games == 1:
                print(f"{GLaDOS} Well, you only have 1 game, so this should be easy even for you.{RESET}")
            else:
                print(f"{GLaDOS} Enter a number between 1 and {max_game_num}. Try to count correctly this time.{RESET}")
        else:
            print(f"{GLaDOS} There's nothing to select. How disappointing.{RESET}")
            print(f"\n{System} Please add games using: python interactive_game_manager.py{RESET}")
            exit()
        game_choice = input(f"{GLaDOS} What's your pick, genius? {RESET}")
        
        # Handle game selection
        if game_choice in game_urls:
            # Show specific GLaDOS responses for games that have them (if any)
            if game_choice in game_responses:
                responses = game_responses[game_choice]
                for response in responses:
                    print(f"{GLaDOS} {response}{RESET}")
                    time.sleep(2)
            
            # Launch the actual game
            glados_launch_game(game_choice)
        else:
            print(f"\n{Error} ⚠ INVALID INPUT DETECTED{RESET}")
            print(f"{GLaDOS} Oh wonderful. You can't even follow simple instructions.{RESET}")
            time.sleep(1.5)
            print(f"{GLaDOS} This is exactly why I don't have high expectations for you.{RESET}")
            time.sleep(1.5)
            if max_game_num > 0:
                if total_games == 1:
                    print(f"{GLaDOS} Please try again when you've learned that you only have 1 game.{RESET}")
                    print(f"\n{System} Valid choice: 1. Please restart the program.{RESET}")
                else:
                    print(f"{GLaDOS} Please try again when you've learned to count to {max_game_num}.{RESET}")
                    print(f"\n{System} Valid range: 1-{max_game_num}. Please restart the program.{RESET}")
            else:
                print(f"{GLaDOS} Actually, you have no games, so any input would be wrong.{RESET}")
                print(f"\n{System} No games available. Please add games first.{RESET}")
            # Exit this branch since invalid input was provided

else:
    if user_choice.lower() == "add game":
        print(f"\n{'─' * 80}")
        print(f"{System} ⚠ UNAUTHORIZED OPERATION DETECTED{RESET}")
        print(f"{System} Game catalog modification requires elevated privileges.{RESET}")
        print("")
        print(f"{System} Please utilize the Aperture Science Interactive Game Manager:{RESET}")
        print(f"{System} > Execute: python utils/interactive_game_manager.py{RESET}")
        print(f"{System} This protocol provides comprehensive multi-platform integration.{RESET}")
        print(f"{'─' * 80}")
    else:
        print(f"\n{Error} UNRECOGNIZED COMMAND PROTOCOL{RESET}")
        print(f"{System} Valid operations: [play games] [add game]{RESET}")
        print(f"{System} For catalog management: python utils/interactive_game_manager.py{RESET}")

print(f"\n{'═' * 80}")
print(f"{System} APERTURE SCIENCE ENTERTAINMENT SYSTEM - SESSION TERMINATED{RESET}")
print(f"{GLaDOS} Thank you for using Aperture Science. Goodbye.{RESET}") 
print(f"{'═' * 80}")
