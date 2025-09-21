#!/usr/bin/env python3
"""
████████████████████████████████████████████████████████████████████████████████
         █████╗ ██████╗ ███████╗██████╗ ████████╗██╗   ██╗██████╗ ███████╗
        ██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝
        ███████║██████╔╝█████╗  ██████╔╝   ██║   ██║   ██║██████╔╝█████╗  
        ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗   ██║   ██║   ██║██╔══██╗██╔══╝  
        ██║  ██║██║     ███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║███████╗
        ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝

         ███████╗ ██████╗██║███████╗███╗   ██╗ ██████╗███████╗
         ██╔════╝██╔════╝██║██╔════╝████╗  ██║██╔════╝██╔════╝
         ███████╗██║     ██║█████╗  ██╔██╗ ██║██║     █████╗  
         ╚════██║██║     ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝  
         ███████║╚██████╗██║███████╗██║ ╚████║╚██████╗███████╗
         ╚══════╝ ╚═════╝╚═╝╚══════╝╚═╝ ╚═══╝ ╚═════╝╚══════╝
████████████████████████████████████████████████████████████████████████████████

     APERTURE SCIENCE COMPREHENSIVE STYLING PROTOCOL & VISUAL STANDARDS
                        VERSION: 1.0 "rocket turret"
                   

████████████████████████████████████████████████████████████████████████████████
"""

# ╔════════════════════════════════════════════════════════════════════════════════╗
# ║                    APERTURE SCIENCE COLOR PROTOCOL DEFINITIONS                ║
# ║                                                                                ║
# ║  Standardized color codes for consistent visual branding across all            ║
# ║  Aperture Science Entertainment Distribution System components                 ║
# ║                                                                                ║
# ║  "These colors have been scientifically selected for maximum user confusion"  ║
# ╚════════════════════════════════════════════════════════════════════════════════╝

class ApertureColors:
    """
    ┌─ APERTURE SCIENCE OFFICIAL COLOR REGISTRY ────────────────────────────────────┐
    │ Standardized color definitions for consistent corporate branding              │
    │ All colors tested and approved by GLaDOS for optimal user disappointment     │
    └────────────────────────────────────────────────────────────────────────────────┘
    """
    
    # ┌─ CORE PERSONALITY PROTOCOLS ──────────────────────────────────────────────┐
    GLADOS_ORANGE = "\033[38;5;214m"              # Corporate Orange (Official GLaDOS)
    WHEATLEY_BLUE = "\033[38;5;117m"              # Intelligence Dampening Sphere Blue
    CAVE_JOHNSON_GOLD = "\033[38;5;220m"          # Founder's Gold (Cave Johnson Memorial)
    # └────────────────────────────────────────────────────────────────────────────┘

    # ┌─ SYSTEM PROTOCOLS ─────────────────────────────────────────────────────────┐
    SYSTEM_CYAN = "\033[38;5;45m"                 # Technical System Blue
    SECURITY_RED = "\033[38;5;196m"               # Lockdown Security Red
    TESTING_GREEN = "\033[38;5;46m"               # Portal Test Chamber Green
    # └────────────────────────────────────────────────────────────────────────────┘

    # ┌─ WARNING PROTOCOLS ────────────────────────────────────────────────────────┐
    ERROR_PINK = "\033[38;5;201m"                 # Neurotoxin Warning Pink
    NEUROTOXIN_MAGENTA = "\033[38;5;199m"         # Deadly Neurotoxin Alert
    EMERGENCY_ORANGE = "\033[38;5;208m"           # Emergency Alert Orange
    # └────────────────────────────────────────────────────────────────────────────┘

    # ┌─ COMMUNICATION PROTOCOLS ──────────────────────────────────────────────────┐
    CALLING_PINK = "\033[38;5;201m"               # Neurotoxin Warning Protocol
    CONNECTING_YELLOW = "\033[38;5;226m"          # Connection Establishment Yellow
    TRANSFERRING_CYAN = "\033[38;5;81m"           # Data Transfer Cyan
    # └────────────────────────────────────────────────────────────────────────────┘

    # ┌─ UNIVERSAL RESET PROTOCOL ─────────────────────────────────────────────────┐
    RESET = "\033[0m"                             # Clean Color Reset
    # └────────────────────────────────────────────────────────────────────────────┘

class AperturePersonalities:
    """
    ┌─ APERTURE SCIENCE PERSONALITY DISPLAY PROTOCOLS ──────────────────────────────┐
    │ Standardized personality prefixes with consistent color coding                │
    │ "Each personality has been carefully calibrated for maximum user annoyance"  │
    └────────────────────────────────────────────────────────────────────────────────┘
    """
    
    GLaDOS = ApertureColors.GLADOS_ORANGE + "(GLaDOS)" + ApertureColors.RESET
    WHEATLEY = ApertureColors.WHEATLEY_BLUE + "(Wheatley)" + ApertureColors.RESET
    CAVE_JOHNSON = ApertureColors.CAVE_JOHNSON_GOLD + "(Cave Johnson)" + ApertureColors.RESET
    
    # System Personalities
    SYSTEM = ApertureColors.SYSTEM_CYAN + "(APERTURE-SYS)" + ApertureColors.RESET
    SECURITY = ApertureColors.SECURITY_RED + "(SECURITY)" + ApertureColors.RESET
    TESTING = ApertureColors.TESTING_GREEN + "(TEST-CHAMBER)" + ApertureColors.RESET
    
    # Warning Personalities
    ERROR = ApertureColors.ERROR_PINK + "(ERROR)" + ApertureColors.RESET
    NEUROTOXIN = ApertureColors.NEUROTOXIN_MAGENTA + "(NEUROTOXIN)" + ApertureColors.RESET
    EMERGENCY = ApertureColors.EMERGENCY_ORANGE + "(EMERGENCY)" + ApertureColors.RESET

class ApertureASCII:
    """
    ┌─ APERTURE SCIENCE ASCII ART TEMPLATE LIBRARY ─────────────────────────────────┐
    │ Standardized ASCII art headers and formatting templates                      │
    │ "Scientifically designed for maximum visual impact and user intimidation"   │
    └────────────────────────────────────────────────────────────────────────────────┘
    """
    
    @staticmethod
    def main_header():
        """Primary Aperture Science logo header for main applications"""
        return """████████████████████████████████████████████████████████████████████████████████
         █████╗ ██████╗ ███████╗██████╗ ████████╗██╗   ██╗██████╗ ███████╗
        ██╔══██╗██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝
        ███████║██████╔╝█████╗  ██████╔╝   ██║   ██║   ██║██████╔╝█████╗  
        ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗   ██║   ██║   ██║██╔══██╗██╔══╝  
        ██║  ██║██║     ███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║███████╗
        ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝

         ███████╗ ██████╗██║███████╗███╗   ██╗ ██████╗███████╗
         ██╔════╝██╔════╝██║██╔════╝████╗  ██║██╔════╝██╔════╝
         ███████╗██║     ██║█████╗  ██╔██╗ ██║██║     █████╗  
         ╚════██║██║     ██║██╔══╝  ██║╚██╗██║██║     ██╔══╝  
         ███████║╚██████╗██║███████╗██║ ╚████║╚██████╗███████╗
         ╚══════╝ ╚═════╝╚═╝╚══════╝╚═╝ ╚═══╝ ╚═════╝╚══════╝
████████████████████████████████████████████████████████████████████████████████"""

    @staticmethod
    def section_header(title: str, subtitle: str = ""):
        """Standardized section header with title and optional subtitle"""
        title_bar = "█" * 80
        subtitle_text = f'                      "{subtitle}"' if subtitle else ""
        
        return f"""# {title_bar}
#                        {title.upper().center(48)}
#{subtitle_text}
# {title_bar}"""

    @staticmethod
    def documentation_box(title: str, content: list, quote: str = ""):
        """Professional documentation box with content and optional quote"""
        border_top = "╔" + "═" * 78 + "╗"
        border_bottom = "╚" + "═" * 78 + "╝"
        title_line = f"║{title.center(78)}║"
        empty_line = "║" + " " * 78 + "║"
        
        lines = [f"# {border_top}", f"# {title_line}", f"# {empty_line}"]
        
        for line in content:
            content_line = f"║  {line.ljust(74)}  ║"
            lines.append(f"# {content_line}")
        
        if quote:
            lines.extend([f"# {empty_line}", f"# ║  \"{quote}\".ljust(74)  ║"])
            
        lines.extend([f"# {border_bottom}"])
        return "\n".join(lines)

    @staticmethod
    def technical_specs_box(specs: list):
        """Technical specifications box with bullet points"""
        border_top = "┌─ TECHNICAL SPECIFICATIONS " + "─" * 51 + "┐"
        border_bottom = "└" + "─" * 78 + "┘"
        
        lines = [f"# {border_top}"]
        for spec in specs:
            spec_line = f"│  • {spec.ljust(70)} │"
            lines.append(f"# {spec_line}")
        lines.append(f"# {border_bottom}")
        
        return "\n".join(lines)

    @staticmethod
    def simple_separator(length: int = 80, char: str = "═"):
        """Simple separator line for content division"""
        return char * length

class ApertureMessages:
    """
    ┌─ APERTURE SCIENCE STANDARD MESSAGE LIBRARY ───────────────────────────────────┐
    │ Pre-approved corporate messages for consistent user communication             │
    │ "All messages have been tested for maximum passive-aggressive impact"        │
    └────────────────────────────────────────────────────────────────────────────────┘
    """
    
    # GLaDOS Standard Responses
    GLADOS_STARTUP = "Initializing GLaDOS Entertainment Distribution System..."
    GLADOS_READY = "GLaDOS is now online. Prepare for disappointment."
    GLADOS_ERROR = "An error occurred. This is somehow your fault."
    
    # System Messages
    SYSTEM_INIT = "APERTURE SCIENCE COMPUTER-AIDED ENRICHMENT CENTER"
    SYSTEM_READY = "Welcome to the Aperture Science Gaming Protocol."
    SYSTEM_DIAGNOSTICS = "Performing mandatory system diagnostics..."
    
    # Error Messages
    ERROR_GENERIC = "⚠ SYSTEM EXCEPTION: Something went wrong, as expected"
    ERROR_CONNECTION = "Connection failed. Your networking skills need work."
    ERROR_PERMISSION = "Access denied. Even the computer doesn't trust you."

class ApertureFormatting:
    """
    ┌─ APERTURE SCIENCE FORMATTING UTILITIES ───────────────────────────────────────┐
    │ Standardized formatting functions for consistent output presentation          │
    │ "Formatting so good, even the test subjects might understand it"             │
    └────────────────────────────────────────────────────────────────────────────────┘
    """
    
    @staticmethod
    def print_glados(message: str):
        """Print message with GLaDOS personality formatting"""
        print(f"{AperturePersonalities.GLaDOS}: {message}")
    
    @staticmethod
    def print_wheatley(message: str):
        """Print message with Wheatley personality formatting"""
        print(f"{AperturePersonalities.WHEATLEY}: {message}")
    
    @staticmethod
    def print_system(message: str):
        """Print message with system formatting"""
        print(f"{AperturePersonalities.SYSTEM}: {message}")
    
    @staticmethod
    def print_error(message: str):
        """Print message with error formatting"""
        print(f"{AperturePersonalities.ERROR}: {message}")
    
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
    
    @staticmethod
    def format_colored_text(text: str, color_code: str, reset: bool = True):
        """Apply color formatting to text with optional reset"""
        return f"{color_code}{text}{ApertureColors.RESET if reset else ''}"

# ╔════════════════════════════════════════════════════════════════════════════════╗
# ║                        STYLESHEET USAGE GUIDELINES                            ║
# ║                                                                                ║
# ║  Import this module and use the standardized classes for consistent styling:  ║
# ║                                                                                ║
# ║  from styles.aperture_science_stylesheet import (                             ║
# ║      ApertureColors, AperturePersonalities, ApertureASCII, ApertureFormatting ║
# ║  )                                                                             ║
# ║                                                                                ║
# ║  Example Usage:                                                                ║
# ║  ApertureFormatting.print_glados("This is a GLaDOS message")                  ║
# ║  print(ApertureASCII.main_header())                                           ║
# ║  color_text = ApertureFormatting.format_colored_text("Text", Colors.CYAN)     ║
# ║                                                                                ║
# ║  "Remember: Consistency is the key to scientific excellence"                  ║
# ╚════════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    """
    Demonstration of Aperture Science Stylesheet capabilities
    """
    print(ApertureASCII.main_header())
    print("\n" + ApertureASCII.simple_separator())
    
    ApertureFormatting.print_system("Aperture Science Stylesheet loaded successfully")
    ApertureFormatting.print_glados("All styling protocols initialized and ready for disappointment")
    ApertureFormatting.print_wheatley("Brilliant! This should make everything much more... stylish!")
    
    print("\n" + ApertureASCII.section_header("COLOR DEMONSTRATION", "Showing all available colors"))
    
    print(f"\n{AperturePersonalities.GLaDOS} - Corporate Orange")
    print(f"{AperturePersonalities.WHEATLEY} - Intelligence Dampening Sphere Blue")
    print(f"{AperturePersonalities.CAVE_JOHNSON} - Founder's Gold")
    print(f"{AperturePersonalities.SYSTEM} - Technical System Cyan")
    print(f"{AperturePersonalities.SECURITY} - Security Alert Red")
    print(f"{AperturePersonalities.TESTING} - Test Chamber Green")
    print(f"{AperturePersonalities.ERROR} - Error Warning Pink")
    print(f"{AperturePersonalities.NEUROTOXIN} - Neurotoxin Alert Magenta")
    print(f"{AperturePersonalities.EMERGENCY} - Emergency Orange")
    
    ApertureFormatting.print_separator("END DEMONSTRATION")
    ApertureFormatting.print_glados("Stylesheet demonstration complete. You may now proceed to disappoint me in full color.")