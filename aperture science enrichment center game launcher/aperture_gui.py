"""Portal-inspired GUI for the Aperture Science Enrichment Center launcher."""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Sequence

from ai_personas import (
    DEFAULT_PERSONA_KEY,
    PERSONAS,
    Persona,
    compose_chat_reply,
    compose_game_roasts,
    compose_os_roast,
    fetch_openrouter_usage_summary,
    fetch_free_openrouter_models,
    get_openrouter_api_key,
    keyring_available,
    keyring_has_openrouter_secret,
    store_openrouter_api_key,
    delete_openrouter_api_key,
    resolve_openrouter_model,
)
from steam_scanner import (
    SteamGame,
    discover_steam_libraries,
    find_installed_games,
)


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
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

    return True


def unique_personas() -> List[Persona]:
    """Return the distinct persona objects registered in the system."""

    distinct: Dict[str, Persona] = {}
    for persona in PERSONAS.values():
        distinct[persona.key] = persona
    return sorted(distinct.values(), key=lambda persona: persona.name.lower())


class ScrollableFrame(tk.Frame):
    """Reusable vertical scroll container based on a canvas."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, bd=0, highlightthickness=0)
        self.canvas = tk.Canvas(
            self,
            bd=0,
            highlightthickness=0,
        )
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bd=0)
        self.inner_id = self.canvas.create_window(
            (0, 0),
            window=self.inner,
            anchor="nw",
        )

        self.inner.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.inner_id, width=event.width),
        )

        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, *_: object) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, *_: object) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            # Windows delta increments of 120; macOS already small.
            delta = -1 * int(event.delta / 120) if event.delta else 0
        if delta:
            self.canvas.yview_scroll(delta, "units")


THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "background": "#1b1f22",
        "surface": "#242a2f",
        "surface_highlight": "#2f353c",
        "surface_muted": "#161a1d",
        "text": "#f4f6f8",
        "text_muted": "#aeb7c4",
        "accent": "#f7a11b",
        "accent_hover": "#ffb54a",
        "accent_alt": "#19b4d8",
    },
    "light": {
        "background": "#edf1f4",
        "surface": "#ffffff",
        "surface_highlight": "#f3f5f8",
        "surface_muted": "#dfe4ea",
        "text": "#1f262d",
        "text_muted": "#5b6978",
        "accent": "#f48f00",
        "accent_hover": "#ffae33",
        "accent_alt": "#1684b2",
    },
}

AI_MODE_STATIC = "Static Banter"
AI_MODE_DYNAMIC = "OpenRouter (API key required)"
AI_MODE_NONE = "No AI (silent mode)"

AI_MODE_LABELS = [
    AI_MODE_STATIC,
    AI_MODE_DYNAMIC,
    AI_MODE_NONE,
]

AUTO_MODEL_LABEL = "Auto (choose first free model)"


class ApertureLauncherGUI(tk.Tk):
    """Main window providing the Portal-inspired launcher experience."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Aperture Science Enrichment Center Launcher")
        self.geometry("1024x640")
        self.minsize(880, 560)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.theme_var = tk.StringVar(value="dark")
        self.ai_mode_var = tk.StringVar(value=AI_MODE_STATIC)
        self._last_ai_mode = self.ai_mode_var.get()
        self.keyring_supported = keyring_available()
        self.openrouter_key_var = tk.StringVar(value=os.getenv("OPENROUTER_API_KEY", ""))
        self.api_key_status_var = tk.StringVar(value=self._initial_api_key_status())
        self.show_key_var = tk.BooleanVar(value=False)

        self.available_models = fetch_free_openrouter_models()
        self.no_models_label = "No free models detected"
        initial_model_selection = self._determine_initial_model_selection()
        if self.available_models:
            self.available_models = sorted(set(self.available_models))
            self.model_choices = [AUTO_MODEL_LABEL] + self.available_models
        else:
            self.model_choices = [self.no_models_label]
        self.model_var = tk.StringVar(value=initial_model_selection)
        self.model_status_var = tk.StringVar()
        self._update_model_status_text()

        personas = unique_personas()
        self.persona_by_name = {persona.name: persona for persona in personas}
        default_persona = PERSONAS[DEFAULT_PERSONA_KEY]
        self.current_persona: Persona = self.persona_by_name[default_persona.name]
        self.persona_var = tk.StringVar(value=self.current_persona.name)
        self.personas = personas

        self.games: List[SteamGame] = []
        self.companion_history: list[tuple[str, str]] = []

        self.companion_display: tk.Text | None = None
        self.companion_entry: tk.Entry | None = None
        self.companion_send_button: ttk.Button | None = None
        self.companion_quick_buttons: list[tk.Button] = []
        self.companion_usage_label: tk.Label | None = None
        self.companion_usage_visible = False

        self._sync_model_to_env(announce=False)
        self._build_layout()
        self._apply_model_widget_state()
        self.apply_theme()
        self._announce_welcome()
        self.refresh_openrouter_usage()

    # ------------------------------------------------------------------ UI setup
    def _build_layout(self) -> None:
        self.header_frame = tk.Frame(self, bd=0)
        self.header_frame.pack(fill="x", padx=28, pady=(26, 8))

        self.title_label = tk.Label(
            self.header_frame,
            text="APERTURE LABORATORIES",
            font=("Segoe UI Semibold", 20),
            anchor="w",
        )
        self.title_label.pack(fill="x")

        self.subtitle_label = tk.Label(
            self.header_frame,
            text="Enrichment Center Launcher Console",
            font=("Segoe UI", 11),
            anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(2, 0))

        self.accent_bar = tk.Frame(self, height=3, bd=0)
        self.accent_bar.pack(fill="x", padx=28, pady=(0, 12))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        self.companion_tab = tk.Frame(self.notebook, bd=0)
        self.games_tab = tk.Frame(self.notebook, bd=0)
        self.settings_tab = tk.Frame(self.notebook, bd=0)

        self.notebook.add(self.companion_tab, text="Companion AI")
        self.notebook.add(self.games_tab, text="Games & Roasts")
        self.notebook.add(self.settings_tab, text="Settings")

        self._build_companion_tab()
        self._build_games_tab()
        self._build_settings_tab()

        self.status_var = tk.StringVar(value="Observation deck ready.")
        self.status_bar = tk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            anchor="w",
            padx=16,
            pady=6,
        )
        self.status_bar.pack(fill="x", side="bottom")

    def _build_companion_tab(self) -> None:
        self.companion_scroll = ScrollableFrame(self.companion_tab)
        self.companion_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        self.companion_container = self.companion_scroll.inner

        self.companion_header = tk.Label(
            self.companion_container,
            textvariable=self.persona_var,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            pady=6,
        )
        self.companion_header.pack(fill="x", pady=(0, 8))

        self.companion_model_frame = tk.Frame(self.companion_container, bd=0)
        self.companion_model_frame.pack(fill="x", pady=(0, 8))

        self.companion_model_label = tk.Label(
            self.companion_model_frame,
            text="OpenRouter model:",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.companion_model_label.pack(side="left")

        model_state = "readonly" if self.available_models else "disabled"
        self.companion_model_combo = ttk.Combobox(
            self.companion_model_frame,
            textvariable=self.model_var,
            values=self.model_choices,
            state=model_state,
            width=42,
        )
        self.companion_model_combo.pack(side="left", padx=(8, 0))
        if self.available_models:
            self.companion_model_combo.bind(
                "<<ComboboxSelected>>", self.on_model_selected
            )

        usage_frame = tk.Frame(self.companion_container, bd=0)
        usage_frame.pack(fill="x")

        self.companion_usage_label = tk.Label(
            usage_frame,
            text="",
            font=("Segoe UI", 9),
            anchor="w",
            pady=2,
        )
        self.companion_usage_visible = False

        self.companion_quick_frame = tk.Frame(self.companion_container, bd=0)
        self.companion_quick_frame.pack(fill="x", pady=(0, 6))

        self.companion_quick_label = tk.Label(
            self.companion_quick_frame,
            text="Quick Responses:",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            pady=2,
        )
        self.companion_quick_label.pack(side="left")

        self.companion_buttons_frame = tk.Frame(
            self.companion_quick_frame, bd=0
        )
        self.companion_buttons_frame.pack(side="left", padx=(8, 0))

        self.companion_quick_buttons = []
        for text in ("Roast Me", "Compliment", "Help"):
            button = ttk.Button(
                self.companion_buttons_frame,
                text=text,
                width=12,
                command=lambda t=text: self.on_companion_reaction(t),
            )
            button.pack(side="left", padx=(0, 6))
            self.companion_quick_buttons.append(button)

        self.companion_text_frame = tk.Frame(self.companion_container, bd=0)
        self.companion_text_frame.pack(fill="both", expand=True)

        self.companion_scrollbar = ttk.Scrollbar(self.companion_text_frame)
        self.companion_scrollbar.pack(side="right", fill="y")

        self.companion_display = tk.Text(
            self.companion_text_frame,
            wrap="word",
            state="disabled",
            yscrollcommand=self.companion_scrollbar.set,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
        )
        self.companion_display.pack(fill="both", expand=True)
        self.companion_scrollbar.config(command=self.companion_display.yview)

        self.companion_display.tag_configure("system", spacing1=2, spacing3=6)
        self.companion_display.tag_configure(
            "system_speaker",
            font=("Segoe UI Semibold", 11),
        )
        self.companion_display.tag_configure("user", spacing1=2, spacing3=6)
        self.companion_display.tag_configure(
            "user_speaker",
            font=("Segoe UI Semibold", 11),
        )
        self.companion_display.tag_configure("persona", spacing1=2, spacing3=6)
        self.companion_display.tag_configure(
            "persona_speaker",
            font=("Segoe UI Semibold", 11),
        )

        self.companion_input_frame = tk.Frame(self.companion_container, bd=0)
        self.companion_input_frame.pack(fill="x", pady=(10, 0))

        self.companion_entry = tk.Entry(
            self.companion_input_frame,
            font=("Segoe UI", 11),
        )
        self.companion_entry.pack(
            fill="x", side="left", expand=True, padx=(0, 10)
        )
        self.companion_entry.bind("<Return>", self.on_send_companion_chat)

        self.companion_send_button = ttk.Button(
            self.companion_input_frame,
            text="Send",
            command=self.on_send_companion_chat,
        )
        self.companion_send_button.pack(side="right")

    def _build_games_tab(self) -> None:
        self.games_scroll = ScrollableFrame(self.games_tab)
        self.games_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        self.games_container = self.games_scroll.inner

        description = (
            "Scan connected Steam libraries and launch installed games without"
            " leaving the Aperture observation deck."
        )
        self.games_description = tk.Label(
            self.games_container,
            text=description,
            font=("Segoe UI", 11),
            justify="left",
            wraplength=620,
            anchor="w",
        )
        self.games_description.pack(fill="x")

        self.scan_button = ttk.Button(
            self.games_container,
            text="Scan Steam Libraries",
            command=self.on_scan_games,
        )
        self.scan_button.pack(anchor="w", pady=(12, 8))

        self.games_tree_frame = tk.Frame(self.games_container, bd=0)
        self.games_tree_frame.pack(fill="both", expand=True)

        self.games_tree = ttk.Treeview(
            self.games_tree_frame,
            columns=("name", "app_id", "library"),
            show="headings",
            selectmode="browse",
        )
        self.games_tree.heading("name", text="Game")
        self.games_tree.heading("app_id", text="App ID")
        self.games_tree.heading("library", text="Library")
        self.games_tree.column("name", width=320, anchor="w")
        self.games_tree.column("app_id", width=80, anchor="center")
        self.games_tree.column("library", width=360, anchor="w")
        self.games_tree.pack(fill="both", expand=True, side="left")

        tree_scroll = ttk.Scrollbar(
            self.games_tree_frame,
            orient="vertical",
            command=self.games_tree.yview,
        )
        tree_scroll.pack(side="right", fill="y")
        self.games_tree.configure(yscrollcommand=tree_scroll.set)

        self.games_controls = tk.Frame(self.games_container, bd=0)
        self.games_controls.pack(fill="x", pady=(12, 0))

        self.launch_button = ttk.Button(
            self.games_controls,
            text="Launch Selected Game",
            command=self.on_launch_game,
        )
        self.launch_button.pack(side="left")

        self.roast_button = ttk.Button(
            self.games_controls,
            text="Roast Selected",
            command=self.on_roast_game,
        )
        self.roast_button.pack(side="left", padx=(12, 0))

        self.games_status = tk.Label(
            self.games_controls,
            text="Awaiting scan...",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.games_status.pack(side="left", padx=(16, 0))

        self.games_roast_frame = tk.LabelFrame(
            self.games_container,
            text="AI Commentary",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        self.games_roast_frame.pack(fill="both", expand=False, pady=(12, 0))

        self.games_roast_text = tk.Text(
            self.games_roast_frame,
            height=6,
            wrap="word",
            state="disabled",
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.games_roast_text.pack(fill="both", expand=True)
        self.display_game_roasts(["Roast results will appear here after a scan."])

    def _build_settings_tab(self) -> None:
        self.settings_scroll = ScrollableFrame(self.settings_tab)
        self.settings_scroll.pack(fill="both", expand=True, padx=12, pady=12)
        self.settings_container = self.settings_scroll.inner

        self.theme_frame = tk.LabelFrame(
            self.settings_container,
            text="Test Chamber Lighting",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        self.theme_frame.pack(fill="x", pady=(0, 12))

        self.theme_dark_rb = tk.Radiobutton(
            self.theme_frame,
            text="Dark (Observation Deck)",
            value="dark",
            variable=self.theme_var,
            command=self.on_theme_change,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.theme_dark_rb.pack(fill="x", pady=2)

        self.theme_light_rb = tk.Radiobutton(
            self.theme_frame,
            text="Light (Test Chamber)",
            value="light",
            variable=self.theme_var,
            command=self.on_theme_change,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.theme_light_rb.pack(fill="x", pady=2)

        self.persona_frame = tk.LabelFrame(
            self.settings_container,
            text="AI Personality Core",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        self.persona_frame.pack(fill="x", pady=(0, 12))

        persona_label = tk.Label(
            self.persona_frame,
            text="Active persona:",
            font=("Segoe UI", 10),
            anchor="w",
        )
        persona_label.pack(fill="x", pady=(0, 4))

        self.persona_combo = ttk.Combobox(
            self.persona_frame,
            textvariable=self.persona_var,
            values=[persona.name for persona in self.personas],
            state="readonly",
        )
        self.persona_combo.pack(fill="x")
        self.persona_combo.bind("<<ComboboxSelected>>", self.on_persona_selected)

        self.persona_intro_label = tk.Label(
            self.persona_frame,
            text=self.current_persona.intro,
            font=("Segoe UI", 10),
            wraplength=540,
            justify="left",
            anchor="w",
            pady=6,
        )
        self.persona_intro_label.pack(fill="x")

        self.ai_mode_frame = tk.LabelFrame(
            self.settings_container,
            text="AI Modes",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        self.ai_mode_frame.pack(fill="x", pady=(0, 12))

        ai_mode_label = tk.Label(
            self.ai_mode_frame,
            text="Response engine:",
            font=("Segoe UI", 10),
            anchor="w",
        )
        ai_mode_label.pack(fill="x", pady=(0, 4))

        self.ai_mode_combo = ttk.Combobox(
            self.ai_mode_frame,
            textvariable=self.ai_mode_var,
            values=AI_MODE_LABELS,
            state="readonly",
        )
        self.ai_mode_combo.pack(fill="x")
        self.ai_mode_combo.bind("<<ComboboxSelected>>", self.on_ai_mode_change)

        self.ai_note_label = tk.Label(
            self.ai_mode_frame,
            text=self._ai_mode_hint(),
            font=("Segoe UI", 10),
            wraplength=540,
            justify="left",
            anchor="w",
            pady=6,
        )
        self.ai_note_label.pack(fill="x")

        self.model_label_settings = tk.Label(
            self.ai_mode_frame,
            text="OpenRouter model:",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.model_label_settings.pack(fill="x", pady=(4, 2))

        settings_state = "readonly" if self.available_models else "disabled"
        self.model_combo_settings = ttk.Combobox(
            self.ai_mode_frame,
            textvariable=self.model_var,
            values=self.model_choices,
            state=settings_state,
        )
        self.model_combo_settings.pack(fill="x")
        if self.available_models:
            self.model_combo_settings.bind(
                "<<ComboboxSelected>>", self.on_model_selected
            )

        self.model_status_label = tk.Label(
            self.ai_mode_frame,
            textvariable=self.model_status_var,
            font=("Segoe UI", 10),
            anchor="w",
            pady=6,
        )
        self.model_status_label.pack(fill="x")

        self.api_key_frame = tk.LabelFrame(
            self.settings_container,
            text="OpenRouter Access",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        self.api_key_frame.pack(fill="x")

        api_key_label = tk.Label(
            self.api_key_frame,
            text="API key (stored for this session only):",
            font=("Segoe UI", 10),
            anchor="w",
        )
        api_key_label.pack(fill="x", pady=(0, 4))

        self.api_key_row = tk.Frame(self.api_key_frame, bd=0)
        self.api_key_row.pack(fill="x")

        self.openrouter_key_entry = tk.Entry(
            self.api_key_row,
            textvariable=self.openrouter_key_var,
            show="\u2022",
            font=("Segoe UI", 10),
        )
        self.openrouter_key_entry.pack(fill="x", side="left", expand=True, padx=(0, 8))

        self.toggle_key_button = ttk.Button(
            self.api_key_row,
            text="Show",
            width=6,
            command=self.on_toggle_key_visibility,
        )
        self.toggle_key_button.pack(side="left")

        self.save_key_button = ttk.Button(
            self.api_key_frame,
            text="Apply Key",
            command=self.on_save_openrouter_key,
        )
        self.save_key_button.pack(anchor="w", pady=(10, 0))

        if self.keyring_supported:
            self.save_key_secure_button = ttk.Button(
                self.api_key_frame,
                text="Save Securely",
                command=self.on_save_openrouter_key_secure,
            )
            self.save_key_secure_button.pack(anchor="w", pady=(6, 0))
        else:
            self.save_key_secure_button = None

        self.api_key_status_label = tk.Label(
            self.api_key_frame,
            textvariable=self.api_key_status_var,
            font=("Segoe UI", 10),
            anchor="w",
            pady=4,
        )
        self.api_key_status_label.pack(fill="x")

        self._apply_model_widget_state()

    # ------------------------------------------------------------------ theme helpers
    def apply_theme(self) -> None:
        palette = THEME_PALETTES[self.theme_var.get()]

        self.configure(bg=palette["background"])
        for widget in (
            self.header_frame,
            self.companion_tab,
            self.games_tab,
            self.settings_tab,
        ):
            widget.configure(bg=palette["background"])

        surface_widgets = [
            self.companion_scroll,
            self.companion_scroll.canvas,
            self.companion_container,
            self.games_scroll,
            self.games_scroll.canvas,
            self.games_container,
            self.settings_scroll,
            self.settings_scroll.canvas,
            self.settings_container,
            self.games_tree_frame,
            self.games_roast_frame,
            self.companion_model_frame,
            self.companion_quick_frame,
            self.companion_buttons_frame,
            self.api_key_row,
            self.companion_text_frame,
            self.companion_input_frame,
            self.games_controls,
        ]
        for widget in surface_widgets:
            widget.configure(bg=palette["surface"])

        self.title_label.configure(bg=palette["background"], fg=palette["accent_alt"])
        self.subtitle_label.configure(bg=palette["background"], fg=palette["text_muted"])
        self.accent_bar.configure(bg=palette["accent"])
        self.status_bar.configure(bg=palette["surface_muted"], fg=palette["text_muted"])

        # Companion widgets
        self.companion_header.configure(
            bg=palette["surface"],
            fg=palette["accent_alt"],
        )
        self.companion_display.configure(
            bg=palette["surface_highlight"],
            fg=palette["text"],
            insertbackground=palette["accent"],
        )
        self.games_roast_text.configure(
            bg=palette["surface_highlight"],
            fg=palette["text"],
            insertbackground=palette["accent"],
        )
        self.companion_display.tag_configure(
            "system", foreground=palette["text_muted"]
        )
        self.companion_display.tag_configure(
            "system_speaker", foreground=palette["accent"]
        )
        self.companion_display.tag_configure("user", foreground=palette["accent"])
        self.companion_display.tag_configure(
            "user_speaker",
            foreground=palette["accent_hover"],
        )
        self.companion_display.tag_configure("persona", foreground=palette["text"])
        self.companion_display.tag_configure(
            "persona_speaker",
            foreground=palette["accent_alt"],
        )
        for entry in (self.companion_entry, self.openrouter_key_entry):
            entry.configure(
                bg=palette["surface_highlight"],
                fg=palette["text"],
                highlightthickness=1,
                highlightbackground=palette["accent"],
                highlightcolor=palette["accent"],
                insertbackground=palette["accent"],
                relief="flat",
            )

        # Treeview styling
        self.style.configure(
            "Aperture.Treeview",
            background=palette["surface_highlight"],
            foreground=palette["text"],
            fieldbackground=palette["surface_highlight"],
            borderwidth=0,
        )
        self.style.map(
            "Aperture.Treeview",
            background=[("selected", palette["accent"])],
            foreground=[("selected", palette["background"])],
        )
        self.style.configure(
            "Aperture.Treeview.Heading",
            background=palette["surface"],
            foreground=palette["text_muted"],
            borderwidth=0,
            padding=6,
        )
        self.games_tree.configure(style="Aperture.Treeview")

        # Buttons
        self.style.configure(
            "Accent.TButton",
            background=palette["accent"],
            foreground=palette["background"],
            borderwidth=0,
            focuscolor=palette["accent"],
            padding=(14, 6),
        )
        self.style.map(
            "Accent.TButton",
            background=[
                ("active", palette["accent_hover"]),
                ("disabled", palette["surface_muted"]),
            ],
            foreground=[("disabled", palette["text_muted"])],
        )
        button_candidates = [
            self.companion_send_button,
            self.scan_button,
            self.launch_button,
            self.roast_button,
            self.toggle_key_button,
            self.save_key_button,
            getattr(self, "save_key_secure_button", None),
        ] + self.companion_quick_buttons
        for button in filter(None, button_candidates):
            button.configure(style="Accent.TButton")

        # Labels
        for label in (
            self.games_description,
            self.games_status,
            self.persona_intro_label,
            self.ai_note_label,
            self.companion_model_label,
            self.companion_quick_label,
            self.companion_usage_label,
            self.model_label_settings,
            self.model_status_label,
            self.api_key_status_label,
        ):
            label.configure(bg=palette["surface"], fg=palette["text_muted"])

        # LabelFrames, radio buttons, etc.
        for frame in (
            self.theme_frame,
            self.persona_frame,
            self.ai_mode_frame,
            self.api_key_frame,
            self.games_roast_frame,
        ):
            frame.configure(
                bg=palette["surface"],
                fg=palette["text"],
                highlightbackground=palette["surface"],
            )
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=palette["surface"], fg=palette["text_muted"])
                elif isinstance(child, tk.Radiobutton):
                    child.configure(
                        bg=palette["surface"],
                        fg=palette["text"],
                        selectcolor=palette["surface_highlight"],
                        activebackground=palette["surface"],
                        activeforeground=palette["text"],
                    )

    # ------------------------------------------------------------------ helpers
    def _initial_api_key_status(self) -> str:
        if os.getenv("OPENROUTER_API_KEY"):
            return "API key loaded from environment."
        if keyring_has_openrouter_secret():
            return "Secure API key available in system keyring."
        return "No API key applied."

    def _determine_initial_model_selection(self) -> str:
        if not self.available_models:
            return self.no_models_label

        env_model = os.getenv("OPENROUTER_MODEL", "").strip()
        if env_model and env_model in self.available_models:
            return env_model

        if env_model:
            resolved = resolve_openrouter_model(env_model)
            if resolved:
                if resolved not in self.available_models:
                    self.available_models.append(resolved)
                return resolved

        return AUTO_MODEL_LABEL

    def _update_model_status_text(self) -> None:
        if not self.available_models:
            self.model_status_var.set("No free OpenRouter models detected.")
            return

        slug = self.current_model
        if slug:
            self.model_status_var.set(f"Current model: {slug}")
        else:
            self.model_status_var.set("Current model: automatic selection.")

    def _apply_model_widget_state(self) -> None:
        if not self.available_models:
            state = "disabled"
        elif self.use_dynamic_ai:
            state = "readonly"
        else:
            state = "disabled"

        self.companion_model_combo.configure(state=state)
        self.model_combo_settings.configure(state=state)

        button_state = "normal" if self.ai_responses_enabled else "disabled"
        self.roast_button.configure(state=button_state)
        for button in self.companion_quick_buttons:
            button.configure(state=button_state)

    def _set_companion_usage_text(self, text: str | None) -> None:
        if text:
            self.companion_usage_label.configure(text=text)
            if not self.companion_usage_visible:
                self.companion_usage_label.pack(fill="x", pady=(0, 6))
                self.companion_usage_visible = True
        else:
            if self.companion_usage_visible:
                self.companion_usage_label.pack_forget()
                self.companion_usage_visible = False

    def refresh_openrouter_usage(self) -> None:
        api_key = get_openrouter_api_key() or ""
        if not api_key.strip():
            self._set_companion_usage_text(None)
            return

        summary = fetch_openrouter_usage_summary(api_key)
        if summary:
            self._set_companion_usage_text(f"OpenRouter usage: {summary}")
        else:
            self._set_companion_usage_text("OpenRouter usage: unavailable.")

    def display_game_roasts(self, lines: Sequence[str]) -> None:
        self.games_roast_text.configure(state="normal")
        self.games_roast_text.delete("1.0", "end")
        for line in lines:
            self.games_roast_text.insert("end", f"{line}\n")
        self.games_roast_text.configure(state="disabled")

    def _sync_model_to_env(self, announce: bool = True) -> None:
        slug = self.current_model
        if slug:
            os.environ["OPENROUTER_MODEL"] = slug
            if announce:
                self.status_var.set(f"OpenRouter model set to {slug}.")
        else:
            os.environ.pop("OPENROUTER_MODEL", None)
            if announce:
                self.status_var.set("OpenRouter model set to automatic selection.")
        self._update_model_status_text()

    def _ai_mode_hint(self) -> str:
        mode = self.ai_mode_var.get()
        if mode == AI_MODE_DYNAMIC:
            return (
                "Dynamic mode uses the OpenRouter API when a key is available,"
                " falling back to local banter otherwise."
            )
        if mode == AI_MODE_STATIC:
            return "Static mode relies on offline banter scripts from each personality core."
        return "No AI mode keeps personas silent while you interact manually."

    def append_companion_message(
        self,
        message: str,
        speaker: str | None = None,
        tag: str = "",
        log: bool = False,
    ) -> None:
        """Insert a new line into the companion chat display."""

        if not self.companion_display:
            return

        self.companion_display.configure(state="normal")
        final_tag = tag or (
            "user"
            if speaker == "Test Subject"
            else ("persona" if speaker == self.current_persona.name else "system")
        )
        if speaker:
            self.companion_display.insert(
                "end",
                f"{speaker}: ",
                (f"{final_tag}_speaker",),
            )
        self.companion_display.insert("end", f"{message}\n", (final_tag,))
        self.companion_display.configure(state="disabled")
        self.companion_display.see("end")
        if log and speaker:
            self.companion_history.append((speaker, message))
            if len(self.companion_history) > 50:
                self.companion_history.pop(0)

    def _announce_welcome(self) -> None:
        welcome = (
            "Aperture Science Enrichment Centre System: Hello and welcome to the"
            " Aperture Science Enrichment Centre Game Launcher."
        )
        self.append_companion_message(
            welcome, speaker="System", tag="system", log=True
        )
        if self.ai_responses_enabled:
            self.append_companion_message(
                self.current_persona.intro,
                speaker=self.current_persona.name,
                tag="persona",
                log=True,
            )
            self.append_companion_message(
                compose_os_roast(
                    self.current_persona,
                    allow_dynamic=self.use_dynamic_ai,
                    model=self.current_model,
                ),
                speaker=self.current_persona.name,
                tag="persona",
                log=True,
            )

    @property
    def use_dynamic_ai(self) -> bool:
        return self.ai_mode_var.get() == AI_MODE_DYNAMIC

    @property
    def ai_responses_enabled(self) -> bool:
        return self.ai_mode_var.get() != AI_MODE_NONE

    @property
    def current_model(self) -> str | None:
        value = self.model_var.get().strip()
        if not value or value in {AUTO_MODEL_LABEL, self.no_models_label}:
            return None
        return value

    # ------------------------------------------------------------------ event handlers
    def process_companion_message(
        self, message: str, *, source: str = "Test Subject"
    ) -> None:
        cleaned = message.strip()
        if not cleaned:
            return

        tag = "user" if source == "Test Subject" else "system"
        self.append_companion_message(cleaned, speaker=source, tag=tag, log=True)

        if not self.ai_responses_enabled:
            return

        reply = compose_chat_reply(
            self.current_persona,
            cleaned,
            allow_dynamic=self.use_dynamic_ai,
            model=self.current_model,
            history=self.companion_history,
        )
        self.append_companion_message(
            reply, speaker=self.current_persona.name, tag="persona", log=True
        )

    def on_send_companion_chat(self, *_: object) -> None:
        if not self.companion_entry:
            return
        message = self.companion_entry.get()
        self.companion_entry.delete(0, tk.END)
        self.process_companion_message(message)

    def on_companion_reaction(self, label: str) -> None:
        prompts = {
            "Roast Me": "Roast me about my test performance.",
            "Compliment": "Give me a quick compliment before I head into the chamber.",
            "Help": "I need help figuring out what to do next.",
        }
        self.process_companion_message(prompts.get(label, label))

    def on_scan_games(self) -> None:
        self.scan_button.configure(state="disabled")
        self.status_var.set("Scanning Steam libraries...")
        self.games_status.configure(text="Scanning...")
        self.update_idletasks()

        try:
            libraries = discover_steam_libraries()
            self.games = find_installed_games(libraries)
        except Exception as exc:  # pragma: no cover
            messagebox.showerror(
                "Scan failed",
                f"Steam library scan failed with error:\n{exc}",
                parent=self,
            )
            self.games_status.configure(text="Scan failed.")
            self.status_var.set("Scan failed. Check console for details.")
        else:
            for item in self.games_tree.get_children():
                self.games_tree.delete(item)

            for index, game in enumerate(self.games):
                self.games_tree.insert(
                    "",
                    "end",
                    iid=str(index),
                    values=(game.name, game.app_id, str(game.library)),
                )

            if self.games:
                self.games_status.configure(
                    text=f"Found {len(self.games)} installation(s).",
                )
                self.status_var.set("Scan complete. Select a game to launch.")
                if self.ai_responses_enabled:
                    roasts = compose_game_roasts(
                        self.current_persona,
                        self.games[:3],
                        allow_dynamic=self.use_dynamic_ai,
                        model=self.current_model,
                    )
                    self.display_game_roasts(roasts)
                else:
                    self.display_game_roasts(
                        ["Enable Static or Dynamic mode to receive roasts."]
                    )
            else:
                self.games_status.configure(text="No games detected.")
                self.status_var.set("No Steam installations detected.")
                self.display_game_roasts(["No games detected."])
        finally:
            self.scan_button.configure(state="normal")

    def on_launch_game(self) -> None:
        selection = self.games_tree.selection()
        if not selection:
            messagebox.showinfo(
                "Select a game",
                "Please pick a game from the list before launching.",
                parent=self,
            )
            return

        index = int(selection[0])
        game = self.games[index]
        launched = launch_game(game)

        if launched:
            self.status_var.set(f"Launch command sent for {game.name}.")
            if self.ai_responses_enabled:
                roasts = compose_game_roasts(
                    self.current_persona,
                    [game],
                    allow_dynamic=self.use_dynamic_ai,
                    model=self.current_model,
                )
                self.display_game_roasts(roasts)
            else:
                self.display_game_roasts(["Enable Static or Dynamic mode to receive roasts."])
        else:
            self.status_var.set("Steam launch command failed.")
            messagebox.showerror(
                "Launch failed",
                (
                    f"Could not launch {game.name} via Steam. "
                    "Check that Steam is installed and the protocol is registered."
                ),
                parent=self,
            )

    def on_roast_game(self) -> None:
        if not self.games:
            self.display_game_roasts(["Run a scan to discover games first."])
            return

        if not self.ai_responses_enabled:
            self.display_game_roasts(["Enable Static or Dynamic mode to receive roasts."])
            return

        selection = self.games_tree.selection()
        games_to_roast: List[SteamGame]
        if selection:
            try:
                index = int(selection[0])
                games_to_roast = [self.games[index]]
            except (ValueError, IndexError):
                games_to_roast = []
        else:
            games_to_roast = self.games[:3]

        if not games_to_roast:
            self.display_game_roasts(["Select a game from the list first."])
            return

        self.status_var.set("Requesting AI roast for the current selection.")
        roasts = compose_game_roasts(
            self.current_persona,
            games_to_roast,
            allow_dynamic=self.use_dynamic_ai,
            model=self.current_model,
        )
        self.display_game_roasts(roasts)

    def on_persona_selected(self, *_: object) -> None:
        selected = self.persona_var.get()
        persona = self.persona_by_name.get(selected)
        if not persona or persona is self.current_persona:
            return

        self.current_persona = persona
        self.persona_intro_label.configure(text=persona.intro)
        self.status_var.set(f"Persona switched to {persona.name}.")
        if self.ai_responses_enabled:
            persona_lines = [
                f"{persona.name}: {persona.intro}",
                f"{persona.name}: "
                + compose_os_roast(
                    persona,
                    allow_dynamic=self.use_dynamic_ai,
                    model=self.current_model,
                ),
            ]
            self.display_game_roasts(persona_lines)
        self.persona_var.set(persona.name)

    def on_theme_change(self) -> None:
        self.apply_theme()
        self.status_var.set(
            f"Lighting adjusted to {self.theme_var.get().capitalize()} mode."
        )

    def on_ai_mode_change(self, *_: object) -> None:
        previous_mode = self._last_ai_mode
        self.ai_note_label.configure(text=self._ai_mode_hint())
        self._apply_model_widget_state()
        mode = self.ai_mode_var.get()
        if mode == AI_MODE_DYNAMIC:
            self.status_var.set("AI mode set to Dynamic.")
        elif mode == AI_MODE_NONE:
            self.status_var.set("AI mode set to No AI (personas muted).")
        else:
            self.status_var.set("AI mode set to Static.")
        if mode == AI_MODE_NONE and previous_mode != AI_MODE_NONE:
            self.display_game_roasts(["AI responses muted. Manual interaction only."])
        if mode != AI_MODE_NONE and previous_mode == AI_MODE_NONE:
            persona_lines = [
                "AI responses re-enabled. Persona coming back online.",
                f"{self.current_persona.name}: {self.current_persona.intro}",
                f"{self.current_persona.name}: "
                + compose_os_roast(
                    self.current_persona,
                    allow_dynamic=self.use_dynamic_ai,
                    model=self.current_model,
                ),
            ]
            self.display_game_roasts(persona_lines)
        self._last_ai_mode = mode

    def on_model_selected(self, *_: object) -> None:
        self._sync_model_to_env()

    def on_toggle_key_visibility(self) -> None:
        self.show_key_var.set(not self.show_key_var.get())
        if self.show_key_var.get():
            self.openrouter_key_entry.configure(show="")
            self.toggle_key_button.configure(text="Hide")
        else:
            self.openrouter_key_entry.configure(show="\u2022")
            self.toggle_key_button.configure(text="Show")

    def on_save_openrouter_key(self) -> None:
        key = self.openrouter_key_var.get().strip()
        if key:
            os.environ["OPENROUTER_API_KEY"] = key
            if self.keyring_supported and keyring_has_openrouter_secret():
                self.api_key_status_var.set(
                    "API key applied for this session (secure copy remains stored)."
                )
            else:
                self.api_key_status_var.set("API key applied for this session.")
            self.status_var.set("OpenRouter API key updated.")
            self.refresh_openrouter_usage()
        else:
            os.environ.pop("OPENROUTER_API_KEY", None)
            removed_secure = False
            if self.keyring_supported and keyring_has_openrouter_secret():
                removed_secure = delete_openrouter_api_key()
            if removed_secure:
                self.api_key_status_var.set(
                    "API key cleared from keyring and environment."
                )
            else:
                self.api_key_status_var.set("API key cleared.")
            self.status_var.set("OpenRouter API key cleared.")
            self.refresh_openrouter_usage()

    def on_save_openrouter_key_secure(self) -> None:
        if not self.keyring_supported:
            messagebox.showinfo(
                "Secure storage unavailable",
                "System keyring support is not available on this platform.",
                parent=self,
            )
            return

        key = self.openrouter_key_var.get().strip()
        if not key:
            messagebox.showinfo(
                "Missing key",
                "Enter an OpenRouter API key before saving it securely.",
                parent=self,
            )
            return

        if store_openrouter_api_key(key):
            os.environ["OPENROUTER_API_KEY"] = key
            self.api_key_status_var.set(
                "API key saved securely to the system keyring."
            )
            self.status_var.set("Secure OpenRouter API key stored.")
            self.refresh_openrouter_usage()
        else:
            messagebox.showerror(
                "Save failed",
                "The API key could not be stored in the system keyring.",
                parent=self,
            )
            self.status_var.set("Secure OpenRouter API key storage failed.")

    # ------------------------------------------------------------------ mainloop
    def run(self) -> None:
        self.mainloop()


def main() -> None:
    gui = ApertureLauncherGUI()
    gui.run()


if __name__ == "__main__":
    main()
