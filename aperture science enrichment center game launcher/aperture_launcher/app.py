"""Tkinter GUI for the Aperture Science Enrichment Center launcher."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List

from steam_scanner import (
    SteamGame,
    discover_steam_libraries,
    find_installed_games,
)

from .constants import (
    CHAT_SPEAKER_COLORS,
    GENERAL_CHAT_MODELS,
    GENERAL_CHAT_PERSONAS,
    ROASTING_PERSONAS,
    THEME_PALETTES,
)
from .openrouter import request_chat_completion, verify_api_key
from .roasting import generate_roast
from .steam_launcher import launch_game


class ApertureLauncherGUI(tk.Tk):
    """Main window providing the Portal-inspired launcher experience."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Aperture Science Enrichment Center Launcher")
        self.geometry("960x600")
        self.minsize(860, 520)

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.theme_var = tk.StringVar(value="dark")
        self.status_var = tk.StringVar(value="Awaiting scan.")
        self.general_status_var = tk.StringVar(value="Apply your OpenRouter key to begin chatting.")
        self.roasting_status_var = tk.StringVar(value="Select a persona to begin the roast.")
        self.api_key_var = tk.StringVar()
        self.general_model_var = tk.StringVar(value=GENERAL_CHAT_MODELS[0])
        self.general_persona_var = tk.StringVar(value=list(GENERAL_CHAT_PERSONAS.keys())[0])
        self.roasting_voice_var = tk.StringVar(value=list(ROASTING_PERSONAS.keys())[0])

        self.games: List[SteamGame] = []
        self._text_widgets: List[tk.Text] = []
        self._rng = random.Random()

        self.general_histories: Dict[str, List[Dict[str, str]]] = {
            persona: [self._system_message(prompt)]
            for persona, prompt in GENERAL_CHAT_PERSONAS.items()
        }
        self._pending_general_persona: str | None = None
        self.general_busy = False
        self.api_key_valid = False
        self._validated_api_key = ""

        self.roasting_histories: Dict[str, List[Dict[str, str]]] = {
            persona: [self._system_message(prompt)] for persona, prompt in ROASTING_PERSONAS.items()
        }
        self.roasting_busy = False

        self._build_ui()
        self._apply_theme()

        self.api_key_var.trace_add("write", self._invalidate_api_key)

    def _build_ui(self) -> None:
        """Create and layout the interface widgets."""

        header = ttk.Frame(self)
        header.pack(fill="x", padx=24, pady=(24, 12))

        title = ttk.Label(
            header,
            text="Aperture Science Enrichment Center",
            font=("Helvetica", 20, "bold"),
        )
        title.pack(side="left")

        header_actions = ttk.Frame(header)
        header_actions.pack(side="right")

        ttk.Label(header_actions, text="Theme:").pack(side="left", padx=(0, 6))
        theme_menu = ttk.OptionMenu(
            header_actions,
            self.theme_var,
            self.theme_var.get(),
            *THEME_PALETTES.keys(),
            command=lambda *_: self._apply_theme(),
        )
        theme_menu.pack(side="left")

        ttk.Button(header_actions, text="Quit", command=self.destroy).pack(side="left", padx=(12, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.launcher_tab = ttk.Frame(self.notebook)
        self.general_chat_tab = ttk.Frame(self.notebook)
        self.roasting_chat_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.launcher_tab, text="Launcher")
        self.notebook.add(self.general_chat_tab, text="General Chat")
        self.notebook.add(self.roasting_chat_tab, text="Roasting Chamber")

        self._build_launcher_tab(self.launcher_tab)
        self._build_general_chat_tab(self.general_chat_tab)
        self._build_roasting_chat_tab(self.roasting_chat_tab)

    def _build_launcher_tab(self, parent: ttk.Frame) -> None:
        """Construct the classic launcher interface inside its tab."""

        controls = ttk.Frame(parent)
        controls.pack(fill="x", padx=24, pady=(24, 0))

        self.scan_button = ttk.Button(controls, text="Scan for Games", command=self.scan_for_games)
        self.scan_button.pack(side="left")

        self.launch_button = ttk.Button(
            controls,
            text="Launch Selected",
            command=self.launch_selected_game,
            state="disabled",
        )
        self.launch_button.pack(side="left", padx=(12, 0))

        content = ttk.Frame(parent)
        content.pack(fill="both", expand=True, padx=24, pady=(12, 12))

        self.tree = ttk.Treeview(
            content,
            columns=("name", "appid", "location"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("name", text="Game")
        self.tree.heading("appid", text="App ID")
        self.tree.heading("location", text="Install Location")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("appid", width=80, anchor="center")
        self.tree.column("location", anchor="w")

        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-Button-1>", lambda event: self.launch_selected_game())
        self.tree.bind("<<TreeviewSelect>>", lambda event: self._update_launch_button_state())

        status_bar = ttk.Frame(parent)
        status_bar.pack(fill="x", padx=24, pady=(0, 24))

        self.status_label = ttk.Label(status_bar, textvariable=self.status_var)
        self.status_label.pack(side="left")

        hint = ttk.Label(
            status_bar,
            text="Double-click a game to launch it once a scan has completed.",
            style="Hint.TLabel",
        )
        hint.pack(side="right")

    def _build_general_chat_tab(self, parent: ttk.Frame) -> None:
        """Create the general-purpose chatbot interface."""

        config = ttk.LabelFrame(parent, text="OpenRouter Configuration")
        config.pack(fill="x", padx=24, pady=(24, 12))
        config.columnconfigure(1, weight=1)

        ttk.Label(config, text="API Key:").grid(row=0, column=0, sticky="w")
        self.api_key_entry = ttk.Entry(config, textvariable=self.api_key_var, show="*", width=52)
        self.api_key_entry.grid(row=0, column=1, sticky="ew")

        self.api_key_apply_button = ttk.Button(
            config,
            text="Apply Key",
            command=self.apply_api_key,
        )
        self.api_key_apply_button.grid(row=0, column=2, padx=(12, 0))

        ttk.Label(
            config,
            text=(
                "Enter your OpenRouter API key (required). The key stays only in memory for this session."
            ),
            wraplength=520,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        options = ttk.Frame(parent)
        options.pack(fill="x", padx=24)

        ttk.Label(options, text="Persona:").pack(side="left")
        persona_menu = ttk.OptionMenu(
            options,
            self.general_persona_var,
            self.general_persona_var.get(),
            *GENERAL_CHAT_PERSONAS.keys(),
            command=lambda value: self._load_general_history(value),
        )
        persona_menu.pack(side="left", padx=(6, 18))

        ttk.Label(options, text="Model:").pack(side="left")
        self.general_model_combo = ttk.Combobox(
            options,
            textvariable=self.general_model_var,
            values=GENERAL_CHAT_MODELS,
            state="readonly",
            width=48,
        )
        self.general_model_combo.pack(side="left", padx=(6, 12))

        self.general_clear_button = ttk.Button(
            options,
            text="Clear Conversation",
            command=self.clear_general_conversation,
        )
        self.general_clear_button.pack(side="right")

        status_bar = ttk.Frame(parent)
        status_bar.pack(fill="x", padx=24, pady=(6, 6))
        self.general_status_label = ttk.Label(status_bar, textvariable=self.general_status_var)
        self.general_status_label.pack(side="left")

        chat_frame = ttk.Frame(parent)
        chat_frame.pack(fill="both", expand=True, padx=24, pady=(6, 6))

        self.general_display = tk.Text(
            chat_frame,
            wrap="word",
            state="disabled",
            height=16,
            relief="flat",
            bd=0,
        )
        self._text_widgets.append(self.general_display)

        general_scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.general_display.yview)
        self.general_display.configure(yscrollcommand=general_scrollbar.set)

        self.general_display.pack(side="left", fill="both", expand=True)
        general_scrollbar.pack(side="right", fill="y")

        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", padx=24, pady=(6, 24))

        self.general_input = tk.Text(input_frame, wrap="word", height=4)
        self.general_input.pack(side="left", fill="both", expand=True)
        self._text_widgets.append(self.general_input)

        self.general_send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_general_message,
        )
        self.general_send_button.pack(side="left", padx=(12, 0))

        self._load_general_history(self.general_persona_var.get())

    def _build_roasting_chat_tab(self, parent: ttk.Frame) -> None:
        """Create the roasting chatbot interface with persona switching."""

        settings = ttk.Frame(parent)
        settings.pack(fill="x", padx=24, pady=(24, 12))

        ttk.Label(settings, text="Persona:").pack(side="left")
        persona_menu = ttk.OptionMenu(
            settings,
            self.roasting_voice_var,
            self.roasting_voice_var.get(),
            *ROASTING_PERSONAS.keys(),
            command=lambda *_: self._load_roasting_history(self.roasting_voice_var.get()),
        )
        persona_menu.pack(side="left", padx=(6, 12))

        self.roasting_clear_button = ttk.Button(
            settings,
            text="Clear Persona History",
            command=self.clear_roasting_conversation,
        )
        self.roasting_clear_button.pack(side="right")

        status_bar = ttk.Frame(parent)
        status_bar.pack(fill="x", padx=24, pady=(6, 6))
        self.roasting_status_label = ttk.Label(status_bar, textvariable=self.roasting_status_var)
        self.roasting_status_label.pack(side="left")

        chat_frame = ttk.Frame(parent)
        chat_frame.pack(fill="both", expand=True, padx=24, pady=(6, 6))

        self.roasting_display = tk.Text(
            chat_frame,
            wrap="word",
            state="disabled",
            height=16,
            relief="flat",
            bd=0,
        )
        self._text_widgets.append(self.roasting_display)

        roast_scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", command=self.roasting_display.yview)
        self.roasting_display.configure(yscrollcommand=roast_scrollbar.set)

        self.roasting_display.pack(side="left", fill="both", expand=True)
        roast_scrollbar.pack(side="right", fill="y")

        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x", padx=24, pady=(6, 24))

        self.roasting_input = tk.Text(input_frame, wrap="word", height=4)
        self.roasting_input.pack(side="left", fill="both", expand=True)
        self._text_widgets.append(self.roasting_input)

        self.roasting_send_button = ttk.Button(
            input_frame,
            text="Roast",
            command=self.send_roasting_message,
        )
        self.roasting_send_button.pack(side="left", padx=(12, 0))

        self._load_roasting_history(self.roasting_voice_var.get())

    def _apply_theme(self) -> None:
        """Update widget colors based on the selected theme."""

        palette = THEME_PALETTES[self.theme_var.get()]

        self.configure(bg=palette["background"])

        style = self.style
        style.configure(
            "TFrame",
            background=palette["background"],
        )
        style.configure(
            "TNotebook",
            background=palette["background"],
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=palette["surface"],
            foreground=palette["text"],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", palette["surface_highlight"])],
            foreground=[("selected", palette["text"])],
        )
        style.configure(
            "Treeview",
            background=palette["surface"],
            fieldbackground=palette["surface"],
            foreground=palette["text"],
            rowheight=28,
        )
        style.configure("Treeview.Heading", background=palette["surface_highlight"], foreground=palette["text"])
        style.configure("TLabel", background=palette["background"], foreground=palette["text"])
        style.configure("Hint.TLabel", background=palette["background"], foreground=palette["text_muted"])
        style.configure(
            "TButton",
            background=palette["accent"],
            foreground=palette["text"],
        )
        style.map(
            "TButton",
            background=[("active", palette["accent_hover"])],
        )
        style.configure(
            "TLabelframe",
            background=palette["surface"],
            foreground=palette["text"],
        )
        style.configure(
            "TLabelframe.Label",
            background=palette["surface"],
            foreground=palette["text"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=palette["surface"],
            foreground=palette["text"],
            background=palette["surface"],
        )
        style.configure(
            "TEntry",
            fieldbackground=palette["surface"],
            foreground=palette["text"],
            background=palette["surface"],
        )

        self.option_add("*TCombobox*Listbox.background", palette["surface"])
        self.option_add("*TCombobox*Listbox.foreground", palette["text"])

        for widget in self._text_widgets:
            state = widget.cget("state")
            if state == "disabled":
                widget.configure(state="normal")
            widget.configure(
                bg=palette["surface"],
                fg=palette["text"],
                insertbackground=palette["text"],
                highlightthickness=1,
                highlightbackground=palette["surface_muted"],
                highlightcolor=palette["accent"],
                selectbackground=palette["accent"],
                selectforeground=palette["text"],
            )
            if state == "disabled":
                widget.configure(state="disabled")

    def _system_message(self, content: str) -> Dict[str, str]:
        """Create a system message payload for OpenRouter."""

        return {"role": "system", "content": content}

    def _append_chat_message(self, widget: tk.Text, speaker: str, message: str) -> None:
        """Append a message to the given chat transcript widget."""

        state = widget.cget("state")
        if state == "disabled":
            widget.configure(state="normal")
        tag = self._ensure_chat_tag(widget, speaker)
        widget.insert(tk.END, f"{speaker}: {message}\n\n", tag)
        if state == "disabled":
            widget.configure(state="disabled")
        widget.see(tk.END)

    def _ensure_chat_tag(self, widget: tk.Text, speaker: str) -> str:
        """Ensure a text tag exists for the speaker and return it."""

        sanitized = "".join(ch if ch.isalnum() else "_" for ch in speaker)
        tag_name = f"speaker_{sanitized or 'unknown'}"
        if tag_name not in widget.tag_names():
            color = CHAT_SPEAKER_COLORS.get(
                speaker,
                CHAT_SPEAKER_COLORS.get("Default", self.style.lookup("TLabel", "foreground")),
            )
            widget.tag_configure(tag_name, foreground=color)
        return tag_name

    def _clear_text_widget(self, widget: tk.Text) -> None:
        """Clear all content from a text widget."""

        state = widget.cget("state")
        if state == "disabled":
            widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        if state == "disabled":
            widget.configure(state="disabled")

    def _reset_text_widget(self, widget: tk.Text, message: str, speaker: str = "System") -> None:
        """Reset a text widget and optionally insert a starter message."""

        self._clear_text_widget(widget)
        if message:
            self._append_chat_message(widget, speaker, message)

    def _set_general_busy(self, busy: bool, status: str | None = None) -> None:
        """Enable or disable general chat controls."""

        self.general_busy = busy
        state = "disabled" if busy else "normal"
        self.general_send_button.configure(state=state)
        self.general_clear_button.configure(state=state)
        self.api_key_apply_button.configure(state=state)

        if status is None:
            persona = self.general_persona_var.get()
            status = (
                f"{persona} is contacting OpenRouter..."
                if busy
                else f"{persona} ready for your next prompt."
            )
        self.general_status_var.set(status)

    def _invalidate_api_key(self, *_: object) -> None:
        """Mark the cached OpenRouter key as invalid when it changes."""

        if self.api_key_valid:
            self.api_key_valid = False
            self._validated_api_key = ""
            if not self.general_busy:
                self.general_status_var.set("API key changed. Click Apply Key to validate.")

    def apply_api_key(self) -> None:
        """Validate the entered OpenRouter key before allowing chat usage."""

        if self.general_busy:
            messagebox.showinfo(
                "General Chat",
                "Please wait for the current operation to finish before applying a new key.",
            )
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("General Chat", "Enter an OpenRouter API key before applying.")
            return

        self._set_general_busy(True, "Validating API key with OpenRouter...")

        def on_complete(error: Exception | None) -> None:
            if error:
                self.api_key_valid = False
                self._validated_api_key = ""
                self._set_general_busy(False, "API key validation failed. See details above.")
                messagebox.showerror(
                    "General Chat",
                    "Could not validate the OpenRouter key. Please verify the key and try again.\n\n"
                    f"Details: {error}",
                )
                return

            self.api_key_valid = True
            self._validated_api_key = api_key
            self._set_general_busy(False, "API key validated. Ready to chat.")

        verify_api_key(api_key, on_complete, scheduler=self.after)

    def _set_roasting_busy(self, busy: bool, status: str | None = None) -> None:
        """Enable or disable roasting chat controls."""

        self.roasting_busy = busy
        state = "disabled" if busy else "normal"
        self.roasting_send_button.configure(state=state)
        self.roasting_clear_button.configure(state=state)

        if status is None:
            persona = self.roasting_voice_var.get()
            status = "Synthesizing a roast..." if busy else f"{persona} ready to roast."
        self.roasting_status_var.set(status)

    def _update_launch_button_state(self) -> None:
        """Enable or disable the launch button based on selection."""

        if self.tree.selection():
            self.launch_button.configure(state="normal")
        else:
            self.launch_button.configure(state="disabled")

    def _set_status(self, message: str) -> None:
        """Update the status bar text."""

        self.status_var.set(message)

    def scan_for_games(self) -> None:
        """Discover Steam games and populate the tree view."""

        self._set_status("Scanning Steam libraries...")
        self.update_idletasks()

        libraries = discover_steam_libraries()
        games = find_installed_games(libraries)
        self.games = games

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not games:
            self._set_status("No Steam games detected. Ensure Steam libraries are accessible.")
            self.launch_button.configure(state="disabled")
            return

        for game in games:
            self.tree.insert(
                "",
                "end",
                iid=game.app_id,
                values=(game.name, game.app_id, str(game.install_dir)),
            )

        self.tree.selection_set(self.tree.get_children()[0])
        self.tree.focus(self.tree.get_children()[0])
        self._update_launch_button_state()
        self._set_status(f"Found {len(games)} game(s). Select one to launch.")

    def launch_selected_game(self) -> None:
        """Launch the currently selected game if possible."""

        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Aperture Launcher", "Select a game to launch after scanning.")
            return

        app_id = selection[0]
        game = next((game for game in self.games if game.app_id == app_id), None)
        if game is None:
            messagebox.showerror("Aperture Launcher", "The selected game could not be resolved.")
            return

        self._set_status(f"Launching {game.name}...")
        self.update_idletasks()

        if not launch_game(game):
            messagebox.showerror(
                "Aperture Launcher",
                "Failed to communicate with Steam. Ensure the client is installed and try again.",
            )
            self._set_status("Launch failed. Please try again.")
            return

        self._set_status(f"Launch command sent for {game.name}. Enjoy your game!")

    def send_general_message(self) -> None:
        """Submit a prompt to the general-purpose chatbot."""

        if self.general_busy:
            messagebox.showinfo(
                "General Chat",
                "Please wait for the current response before sending another message.",
            )
            return

        content = self.general_input.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo("General Chat", "Enter a prompt before sending.")
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("General Chat", "An OpenRouter API key is required.")
            return

        if not self.api_key_valid or api_key != self._validated_api_key:
            messagebox.showerror(
                "General Chat",
                "Apply your OpenRouter API key before chatting. Click the Apply Key button to validate it.",
            )
            if not self.general_busy:
                self.general_status_var.set("Apply your OpenRouter key to begin chatting.")
            return

        model = self.general_model_var.get().strip()
        if not model:
            messagebox.showerror("General Chat", "Select a model before sending.")
            return

        persona = self.general_persona_var.get()
        history = self._current_general_history()
        self.general_input.delete("1.0", tk.END)
        history.append({"role": "user", "content": content})
        self._append_chat_message(self.general_display, "Test Subject", content)
        self._set_general_busy(True, f"{persona} is formulating a response...")

        payload = [dict(message) for message in history]
        self._pending_general_persona = persona
        request_chat_completion(
            api_key,
            model,
            payload,
            self._handle_general_completion,
            scheduler=self.after,
        )

    def _handle_general_completion(self, error: Exception | None, content: str | None) -> None:
        """Handle the result of a general chat request."""

        persona = self._pending_general_persona or self.general_persona_var.get()
        history = self.general_histories.setdefault(
            persona, [self._system_message(GENERAL_CHAT_PERSONAS[persona])]
        )
        self._pending_general_persona = None

        if error:
            if persona == self.general_persona_var.get():
                self._append_chat_message(self.general_display, "System", f"Error: {error}")
            self._set_general_busy(False, "OpenRouter request failed. Try again.")
            return

        if content is None:
            if persona == self.general_persona_var.get():
                self._append_chat_message(
                    self.general_display,
                    "System",
                    "No response received from OpenRouter.",
                )
            self._set_general_busy(False, "Received an empty response.")
            return

        history.append({"role": "assistant", "content": content})
        if persona == self.general_persona_var.get():
            self._append_chat_message(self.general_display, persona, content)
            self._set_general_busy(False, f"{persona} responded. Ready for your next prompt.")
        else:
            self._set_general_busy(False)

    def clear_general_conversation(self) -> None:
        """Reset the general assistant conversation."""

        if self.general_busy:
            messagebox.showinfo(
                "General Chat",
                "Please wait for the current response before clearing the conversation.",
            )
            return

        persona = self.general_persona_var.get()
        self.general_histories[persona] = [
            self._system_message(GENERAL_CHAT_PERSONAS[persona])
        ]
        self._load_general_history(persona)
        self.general_status_var.set("Conversation reset.")
        self.general_input.delete("1.0", tk.END)

    def _current_general_history(self) -> List[Dict[str, str]]:
        """Return the conversation history for the active general persona."""

        persona = self.general_persona_var.get()
        if persona not in self.general_histories:
            self.general_histories[persona] = [
                self._system_message(GENERAL_CHAT_PERSONAS[persona])
            ]
        return self.general_histories[persona]

    def _load_general_history(self, persona: str) -> None:
        """Refresh the general chat transcript for the selected persona."""

        history = self.general_histories.setdefault(
            persona, [self._system_message(GENERAL_CHAT_PERSONAS[persona])]
        )
        self._clear_text_widget(self.general_display)

        if len(history) == 1:
            self._append_chat_message(
                self.general_display,
                "System",
                f"{persona} persona online. Provide a prompt to begin.",
            )
        else:
            for message in history[1:]:
                speaker = "Test Subject" if message["role"] == "user" else persona
                self._append_chat_message(
                    self.general_display,
                    speaker,
                    message["content"],
                )

        if not self.general_busy and self.api_key_valid:
            self.general_status_var.set(f"{persona} ready for conversation.")

    def _current_roasting_history(self) -> List[Dict[str, str]]:
        """Return the conversation history for the active roasting persona."""

        persona = self.roasting_voice_var.get()
        if persona not in self.roasting_histories:
            self.roasting_histories[persona] = [self._system_message(ROASTING_PERSONAS[persona])]
        return self.roasting_histories[persona]

    def send_roasting_message(self) -> None:
        """Submit a prompt to the roasting chatbot."""

        if self.roasting_busy:
            messagebox.showinfo(
                "Roasting Chamber",
                "Please wait for the current response before sending another message.",
            )
            return

        content = self.roasting_input.get("1.0", tk.END).strip()
        if not content:
            messagebox.showinfo(
                "Roasting Chamber", "Provide something for the persona to roast."
            )
            return

        persona = self.roasting_voice_var.get()
        history = self._current_roasting_history()
        history.append({"role": "user", "content": content})
        self._append_chat_message(self.roasting_display, "You", content)
        self.roasting_input.delete("1.0", tk.END)
        self._set_roasting_busy(True, f"{persona} is composing a roast...")

        user_prompt = content

        def finalize_roast() -> None:
            try:
                roast = generate_roast(persona, user_prompt, rng=self._rng)
            except Exception as exc:  # pragma: no cover - defensive
                history.append(
                    {
                        "role": "assistant",
                        "content": f"System error generating roast: {exc}",
                    }
                )
                if persona == self.roasting_voice_var.get():
                    self._append_chat_message(
                        self.roasting_display,
                        "System",
                        "Roast generator malfunctioned. Please try again.",
                    )
                    self._set_roasting_busy(False, "Roast generator unavailable.")
                else:
                    self._set_roasting_busy(False)
                return

            history.append({"role": "assistant", "content": roast})
            if persona == self.roasting_voice_var.get():
                self._append_chat_message(self.roasting_display, persona, roast)
                self._set_roasting_busy(False, f"{persona} delivered a roast. Ready for more.")
            else:
                self._set_roasting_busy(False)

        self.after(120, finalize_roast)

    def clear_roasting_conversation(self) -> None:
        """Reset the active roasting persona's conversation."""

        if self.roasting_busy:
            messagebox.showinfo(
                "Roasting Chamber",
                "Please wait for the current response before clearing the conversation.",
            )
            return

        persona = self.roasting_voice_var.get()
        self.roasting_histories[persona] = [self._system_message(ROASTING_PERSONAS[persona])]
        self._load_roasting_history(persona)
        self.roasting_status_var.set(f"{persona} history cleared. Ready for more roasting.")
        self.roasting_input.delete("1.0", tk.END)

    def _load_roasting_history(self, persona: str) -> None:
        """Refresh the roasting transcript for the selected persona."""

        history = self.roasting_histories.setdefault(
            persona, [self._system_message(ROASTING_PERSONAS[persona])]
        )
        self._clear_text_widget(self.roasting_display)

        if len(history) == 1:
            self._append_chat_message(
                self.roasting_display,
                "System",
                f"{persona} persona armed. Offer something they can mock.",
            )
        else:
            for message in history[1:]:
                speaker = "You" if message["role"] == "user" else persona
                self._append_chat_message(self.roasting_display, speaker, message["content"])

        if not self.roasting_busy:
            self.roasting_status_var.set(f"{persona} ready to roast.")


def main() -> None:
    """Start the Tkinter application."""

    app = ApertureLauncherGUI()
    app.mainloop()
