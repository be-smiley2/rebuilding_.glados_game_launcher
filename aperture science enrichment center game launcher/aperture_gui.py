"""Portal-inspired GUI for the Aperture Science Enrichment Center launcher."""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List

from ai_personas import (
    DEFAULT_PERSONA_KEY,
    PERSONAS,
    Persona,
    compose_chat_reply,
    compose_game_roasts,
    compose_os_roast,
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
    return list(distinct.values())


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

AI_MODE_LABELS = [
    "Static Banter",
    "OpenRouter (API key required)",
]


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
        self.ai_mode_var = tk.StringVar(value=AI_MODE_LABELS[0])

        self.personas = sorted(unique_personas(), key=lambda persona: persona.name.lower())
        self.persona_by_name = {persona.name: persona for persona in self.personas}
        self.current_persona: Persona = self.persona_by_name[
            PERSONAS[DEFAULT_PERSONA_KEY].name
        ]
        self.persona_var = tk.StringVar(value=self.current_persona.name)

        self.games: List[SteamGame] = []

        self._build_layout()
        self.apply_theme()
        self._announce_welcome()

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

        self.chat_tab = tk.Frame(self.notebook, bd=0)
        self.games_tab = tk.Frame(self.notebook, bd=0)
        self.settings_tab = tk.Frame(self.notebook, bd=0)

        self.notebook.add(self.chat_tab, text="Chatbot")
        self.notebook.add(self.games_tab, text="Games")
        self.notebook.add(self.settings_tab, text="Settings")

        self._build_chat_tab()
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

    def _build_chat_tab(self) -> None:
        self.chat_container = tk.Frame(self.chat_tab, bd=0)
        self.chat_container.pack(fill="both", expand=True, padx=12, pady=12)

        self.chat_header = tk.Label(
            self.chat_container,
            textvariable=self.persona_var,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
            pady=6,
        )
        self.chat_header.pack(fill="x", pady=(0, 8))

        self.chat_text_frame = tk.Frame(self.chat_container, bd=0)
        self.chat_text_frame.pack(fill="both", expand=True)

        self.chat_scrollbar = ttk.Scrollbar(self.chat_text_frame)
        self.chat_scrollbar.pack(side="right", fill="y")

        self.chat_display = tk.Text(
            self.chat_text_frame,
            wrap="word",
            state="disabled",
            yscrollcommand=self.chat_scrollbar.set,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
        )
        self.chat_display.pack(fill="both", expand=True)
        self.chat_scrollbar.config(command=self.chat_display.yview)

        self.chat_display.tag_configure("system", spacing1=2, spacing3=6)
        self.chat_display.tag_configure("system_speaker", font=("Segoe UI Semibold", 11))
        self.chat_display.tag_configure("user", spacing1=2, spacing3=6)
        self.chat_display.tag_configure("user_speaker", font=("Segoe UI Semibold", 11))
        self.chat_display.tag_configure("persona", spacing1=2, spacing3=6)
        self.chat_display.tag_configure(
            "persona_speaker", font=("Segoe UI Semibold", 11)
        )

        self.chat_input_frame = tk.Frame(self.chat_container, bd=0)
        self.chat_input_frame.pack(fill="x", pady=(10, 0))

        self.chat_entry = tk.Entry(
            self.chat_input_frame,
            font=("Segoe UI", 11),
        )
        self.chat_entry.pack(fill="x", side="left", expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self.on_send_chat)

        self.send_button = ttk.Button(
            self.chat_input_frame,
            text="Send",
            command=self.on_send_chat,
        )
        self.send_button.pack(side="right")

    def _build_games_tab(self) -> None:
        self.games_container = tk.Frame(self.games_tab, bd=0)
        self.games_container.pack(fill="both", expand=True, padx=12, pady=12)

        description = (
            "Scan connected Steam libraries and launch installed games without"
            " leaving the Aperture observation deck."
        )
        self.games_description = tk.Label(
            self.games_container,
            text=description,
            font=("Segoe UI", 11),
            justify="left",
            wraplength=600,
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
        self.games_tree.column("library", width=320, anchor="w")
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

        self.games_status = tk.Label(
            self.games_controls,
            text="Awaiting scan...",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.games_status.pack(side="left", padx=(16, 0))

    def _build_settings_tab(self) -> None:
        self.settings_container = tk.Frame(self.settings_tab, bd=0)
        self.settings_container.pack(fill="both", expand=True, padx=12, pady=12)

        theme_frame = tk.LabelFrame(
            self.settings_container,
            text="Test Chamber Lighting",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        theme_frame.pack(fill="x", pady=(0, 12))

        self.theme_dark_rb = tk.Radiobutton(
            theme_frame,
            text="Dark (Observation Deck)",
            value="dark",
            variable=self.theme_var,
            command=self.on_theme_change,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.theme_dark_rb.pack(fill="x", pady=2)

        self.theme_light_rb = tk.Radiobutton(
            theme_frame,
            text="Light (Test Chamber)",
            value="light",
            variable=self.theme_var,
            command=self.on_theme_change,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.theme_light_rb.pack(fill="x", pady=2)

        persona_frame = tk.LabelFrame(
            self.settings_container,
            text="AI Personality Core",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        persona_frame.pack(fill="x", pady=(0, 12))

        persona_label = tk.Label(
            persona_frame,
            text="Active persona:",
            font=("Segoe UI", 10),
            anchor="w",
        )
        persona_label.pack(fill="x", pady=(0, 4))

        self.persona_combo = ttk.Combobox(
            persona_frame,
            textvariable=self.persona_var,
            values=[persona.name for persona in self.personas],
            state="readonly",
        )
        self.persona_combo.pack(fill="x")
        self.persona_combo.bind("<<ComboboxSelected>>", self.on_persona_selected)

        self.persona_intro_label = tk.Label(
            persona_frame,
            text=self.current_persona.intro,
            font=("Segoe UI", 10),
            wraplength=520,
            justify="left",
            anchor="w",
            pady=6,
        )
        self.persona_intro_label.pack(fill="x")

        ai_mode_frame = tk.LabelFrame(
            self.settings_container,
            text="AI Modes",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
        )
        ai_mode_frame.pack(fill="x")

        ai_mode_label = tk.Label(
            ai_mode_frame,
            text="Response engine:",
            font=("Segoe UI", 10),
            anchor="w",
        )
        ai_mode_label.pack(fill="x", pady=(0, 4))

        self.ai_mode_combo = ttk.Combobox(
            ai_mode_frame,
            textvariable=self.ai_mode_var,
            values=AI_MODE_LABELS,
            state="readonly",
        )
        self.ai_mode_combo.pack(fill="x")
        self.ai_mode_combo.bind("<<ComboboxSelected>>", self.on_ai_mode_change)

        self.ai_note_label = tk.Label(
            ai_mode_frame,
            text=self._ai_mode_hint(),
            font=("Segoe UI", 10),
            wraplength=520,
            justify="left",
            anchor="w",
            pady=6,
        )
        self.ai_note_label.pack(fill="x")

    # ------------------------------------------------------------------ helpers
    def _ai_mode_hint(self) -> str:
        if self.use_dynamic_ai:
            return (
                "Dynamic mode uses the OpenRouter API when configured, falling back"
                " to local banter if no key is present."
            )
        return "Static mode relies on local banter scripts from each personality core."

    def apply_theme(self) -> None:
        palette = THEME_PALETTES[self.theme_var.get()]

        self.configure(bg=palette["background"])
        for widget in (
            self.header_frame,
            self.chat_tab,
            self.games_tab,
            self.settings_tab,
        ):
            widget.configure(bg=palette["background"])
        for widget in (
            self.chat_container,
            self.games_container,
            self.settings_container,
        ):
            widget.configure(bg=palette["surface"])
        self.chat_text_frame.configure(bg=palette["surface_highlight"])
        self.chat_input_frame.configure(bg=palette["surface"])
        self.games_tree_frame.configure(bg=palette["surface_highlight"])
        self.games_controls.configure(bg=palette["surface"])

        self.title_label.configure(bg=palette["background"], fg=palette["accent_alt"])
        self.subtitle_label.configure(bg=palette["background"], fg=palette["text_muted"])
        self.accent_bar.configure(bg=palette["accent"])
        self.status_bar.configure(bg=palette["surface_muted"], fg=palette["text_muted"])

        # Chat widgets
        for widget in (self.chat_header, self.chat_entry):
            widget.configure(bg=palette["surface_highlight"], fg=palette["text"])

        self.chat_display.configure(
            bg=palette["surface_highlight"],
            fg=palette["text"],
            insertbackground=palette["accent"],
        )
        self.chat_display.tag_configure("system", foreground=palette["text_muted"])
        self.chat_display.tag_configure("system_speaker", foreground=palette["accent"])
        self.chat_display.tag_configure("user", foreground=palette["accent"])
        self.chat_display.tag_configure(
            "user_speaker", foreground=palette["accent_hover"]
        )
        self.chat_display.tag_configure("persona", foreground=palette["text"])
        self.chat_display.tag_configure(
            "persona_speaker", foreground=palette["accent_alt"]
        )

        self.chat_entry.configure(
            highlightthickness=1,
            highlightbackground=palette["accent"],
            relief="flat",
            insertbackground=palette["accent"],
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

        # Button styling
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
        for button in (self.send_button, self.scan_button, self.launch_button):
            button.configure(style="Accent.TButton")

        # Label styling for description and status
        for label in (
            self.games_description,
            self.games_status,
            self.persona_intro_label,
            self.ai_note_label,
        ):
            label.configure(bg=palette["surface"], fg=palette["text_muted"])

        # LabelFrames and radio buttons
        for frame in self.settings_container.winfo_children():
            if isinstance(frame, tk.LabelFrame):
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

    def _announce_welcome(self) -> None:
        welcome = (
            "Aperture Science Enrichment Centre System: Hello and welcome to the"
            " Aperture Science Enrichment Centre Game Launcher."
        )
        self.append_chat(welcome, speaker="System")
        self.append_chat(self.current_persona.intro, speaker=self.current_persona.name)
        self.append_chat(
            compose_os_roast(
                self.current_persona,
                allow_dynamic=self.use_dynamic_ai,
            ),
            speaker=self.current_persona.name,
        )

    # ------------------------------------------------------------------ actions
    def append_chat(self, message: str, speaker: str | None = None, tag: str = "") -> None:
        """Insert a new line into the chat display."""

        self.chat_display.configure(state="normal")
        final_tag = tag or (
            "user"
            if speaker == "Test Subject"
            else ("persona" if speaker == self.current_persona.name else "system")
        )
        if speaker:
            self.chat_display.insert(
                "end",
                f"{speaker}: ",
                (f"{final_tag}_speaker",),
            )
        self.chat_display.insert("end", f"{message}\n", (final_tag,))
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    @property
    def use_dynamic_ai(self) -> bool:
        return self.ai_mode_var.get() == AI_MODE_LABELS[1]

    def on_send_chat(self, *_: object) -> None:
        message = self.chat_entry.get().strip()
        if not message:
            return

        self.chat_entry.delete(0, tk.END)
        self.append_chat(message, speaker="Test Subject", tag="user")

        reply = compose_chat_reply(
            self.current_persona,
            message,
            allow_dynamic=self.use_dynamic_ai,
        )
        self.append_chat(reply, speaker=self.current_persona.name, tag="persona")

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
            else:
                self.games_status.configure(text="No games detected.")
                self.status_var.set("No Steam installations detected.")

            roasts = compose_game_roasts(
                self.current_persona,
                self.games[:3],
                allow_dynamic=self.use_dynamic_ai,
            )
            for line in roasts:
                self.append_chat(line, speaker=self.current_persona.name, tag="persona")
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
            roast = compose_game_roasts(
                self.current_persona,
                [game],
                allow_dynamic=self.use_dynamic_ai,
            )[0]
            self.append_chat(roast, speaker=self.current_persona.name, tag="persona")
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

    def on_persona_selected(self, *_: object) -> None:
        selected = self.persona_var.get()
        persona = self.persona_by_name.get(selected)
        if not persona or persona is self.current_persona:
            return

        self.current_persona = persona
        self.persona_intro_label.configure(text=persona.intro)
        self.persona_var.set(persona.name)
        self.append_chat(
            f"Persona switched to {persona.name}.",
            speaker="System",
            tag="system",
        )
        self.append_chat(persona.intro, speaker=persona.name, tag="persona")
        self.persona_header_refresh()

    def persona_header_refresh(self) -> None:
        self.persona_var.set(self.current_persona.name)

    def on_theme_change(self) -> None:
        self.apply_theme()
        self.status_var.set(
            f"Lighting adjusted to {self.theme_var.get().capitalize()} mode."
        )

    def on_ai_mode_change(self, *_: object) -> None:
        self.ai_note_label.configure(text=self._ai_mode_hint())
        mode_label = "Dynamic" if self.use_dynamic_ai else "Static"
        self.status_var.set(f"AI mode set to {mode_label}.")

    # ------------------------------------------------------------------ mainloop
    def run(self) -> None:
        self.mainloop()


def main() -> None:
    gui = ApertureLauncherGUI()
    gui.run()


if __name__ == "__main__":
    main()
