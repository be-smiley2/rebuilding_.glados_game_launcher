"""Tkinter GUI for the Aperture Science Enrichment Center launcher."""

from __future__ import annotations

import os
import platform
import random
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, List, Sequence

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
    JELLYFIN_API_KEY_ENV,
    JELLYFIN_SERVER_URL_ENV,
    JELLYFIN_USER_ID_ENV,
    OPENROUTER_API_KEY_ENV,
)
from .jellyfin import fetch_recent_media, fetch_system_info, fetch_user_views
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
        self.general_status_var = tk.StringVar(
            value="Apply your OpenRouter key to enable OpenRouter chat and roasts."
        )
        self.roasting_status_var = tk.StringVar(
            value="Select a persona, choose an OpenRouter model, and optionally pick a Steam game."
        )
        self.media_status_var = tk.StringVar(value="Provide Jellyfin details to connect.")
        self.api_key_var = tk.StringVar(value=os.environ.get(OPENROUTER_API_KEY_ENV, ""))
        self.general_model_var = tk.StringVar(value=GENERAL_CHAT_MODELS[0])
        self.roasting_model_var = tk.StringVar(value=GENERAL_CHAT_MODELS[0])
        self.general_persona_var = tk.StringVar(value=list(GENERAL_CHAT_PERSONAS.keys())[0])
        self.roasting_voice_var = tk.StringVar(value=list(ROASTING_PERSONAS.keys())[0])
        self.roasting_game_var = tk.StringVar(value="")
        self.include_os_var = tk.BooleanVar(value=True)
        self.jellyfin_server_var = tk.StringVar(value=os.environ.get(JELLYFIN_SERVER_URL_ENV, ""))
        self.jellyfin_api_key_var = tk.StringVar(value=os.environ.get(JELLYFIN_API_KEY_ENV, ""))
        self.jellyfin_user_id_var = tk.StringVar(value=os.environ.get(JELLYFIN_USER_ID_ENV, ""))

        self.games: List[SteamGame] = []
        self._text_widgets: List[tk.Text] = []
        self._rng = random.Random()
        self._os_summary = platform.platform() or platform.system() or "Unknown OS"

        self.general_histories: Dict[str, List[Dict[str, str]]] = {
            persona: [self._system_message(prompt)]
            for persona, prompt in GENERAL_CHAT_PERSONAS.items()
        }
        self._pending_general_persona: str | None = None
        self.general_busy = False
        self.api_key_valid = False
        self._validated_api_key = ""
        self._auto_apply_api_key = bool(self.api_key_var.get())

        self.roasting_histories: Dict[str, List[Dict[str, str]]] = {
            persona: [self._system_message(prompt)] for persona, prompt in ROASTING_PERSONAS.items()
        }
        self.roasting_busy = False
        self._pending_roasting_persona: str | None = None
        self._last_roasting_prompt = ""

        self.jellyfin_busy = False
        self.media_action_buttons: List[ttk.Button] = []

        self._build_ui()
        self._apply_theme()

        self.api_key_var.trace_add("write", self._invalidate_api_key)
        if self._auto_apply_api_key:
            self.general_status_var.set("Validating API key from environment...")
            self.after(200, self.apply_api_key)

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
        self.media_server_tab = ttk.Frame(self.notebook)
        self.roasting_chat_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.launcher_tab, text="Launcher")
        self.notebook.add(self.general_chat_tab, text="General Chat")
        self.notebook.add(self.media_server_tab, text="Media Server")
        self.notebook.add(self.roasting_chat_tab, text="Roasting Chamber")

        self._build_launcher_tab(self.launcher_tab)
        self._build_general_chat_tab(self.general_chat_tab)
        self._build_media_tab(self.media_server_tab)
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
        self.tree.bind("<<TreeviewSelect>>", self._handle_game_selection)

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
                "Enter your OpenRouter API key (required for OpenRouter chat and roasts). "
                "The key stays only in memory for this session."
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

    def _build_media_tab(self, parent: ttk.Frame) -> None:
        """Construct the Jellyfin media server interface."""

        config = ttk.LabelFrame(parent, text="Jellyfin Connection")
        config.pack(fill="x", padx=24, pady=(24, 12))
        config.columnconfigure(1, weight=1)

        ttk.Label(config, text="Server URL:").grid(row=0, column=0, sticky="w")
        self.jellyfin_server_entry = ttk.Entry(
            config,
            textvariable=self.jellyfin_server_var,
            width=52,
        )
        self.jellyfin_server_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(config, text="API Key:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.jellyfin_api_key_entry = ttk.Entry(
            config,
            textvariable=self.jellyfin_api_key_var,
            show="*",
            width=52,
        )
        self.jellyfin_api_key_entry.grid(row=1, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(config, text="User ID:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.jellyfin_user_id_entry = ttk.Entry(
            config,
            textvariable=self.jellyfin_user_id_var,
            width=52,
        )
        self.jellyfin_user_id_entry.grid(row=2, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(
            config,
            text=(
                "Values can be pre-filled via the environment variables "
                f"{JELLYFIN_SERVER_URL_ENV}, {JELLYFIN_API_KEY_ENV}, and {JELLYFIN_USER_ID_ENV}."
            ),
            wraplength=520,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=24)

        self.media_action_buttons: List[ttk.Button] = []

        test_button = ttk.Button(actions, text="Test Connection", command=self.test_jellyfin_connection)
        test_button.pack(side="left")
        self.media_action_buttons.append(test_button)

        libraries_button = ttk.Button(
            actions,
            text="Fetch Libraries",
            command=self.fetch_jellyfin_libraries,
        )
        libraries_button.pack(side="left", padx=(12, 0))
        self.media_action_buttons.append(libraries_button)

        recent_button = ttk.Button(
            actions,
            text="Recent Media",
            command=self.fetch_jellyfin_recent_media,
        )
        recent_button.pack(side="left", padx=(12, 0))
        self.media_action_buttons.append(recent_button)

        clear_button = ttk.Button(actions, text="Clear Output", command=self.clear_media_output)
        clear_button.pack(side="right")

        status_bar = ttk.Frame(parent)
        status_bar.pack(fill="x", padx=24, pady=(6, 6))
        self.media_status_label = ttk.Label(status_bar, textvariable=self.media_status_var)
        self.media_status_label.pack(side="left")

        output_frame = ttk.Frame(parent)
        output_frame.pack(fill="both", expand=True, padx=24, pady=(6, 24))

        self.media_output = tk.Text(
            output_frame,
            wrap="word",
            state="disabled",
            height=18,
            relief="flat",
            bd=0,
        )
        self._text_widgets.append(self.media_output)

        media_scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.media_output.yview)
        self.media_output.configure(yscrollcommand=media_scrollbar.set)

        self.media_output.pack(side="left", fill="both", expand=True)
        media_scrollbar.pack(side="right", fill="y")

        self._append_media_output("Awaiting Jellyfin requests.")

    def _build_roasting_chat_tab(self, parent: ttk.Frame) -> None:
        """Create the roasting chatbot interface with persona switching."""

        config = ttk.LabelFrame(parent, text="OpenRouter Configuration")
        config.pack(fill="x", padx=24, pady=(24, 12))
        config.columnconfigure(1, weight=1)

        ttk.Label(config, text="API Key:").grid(row=0, column=0, sticky="w")
        self.roasting_api_key_entry = ttk.Entry(
            config,
            textvariable=self.api_key_var,
            show="*",
            width=52,
        )
        self.roasting_api_key_entry.grid(row=0, column=1, sticky="ew")

        self.roasting_api_key_apply_button = ttk.Button(
            config,
            text="Apply Key",
            command=self.apply_api_key,
        )
        self.roasting_api_key_apply_button.grid(row=0, column=2, padx=(12, 0))

        ttk.Label(
            config,
            text=(
                "Roasting Chamber shares the OpenRouter key with General Chat. "
                "Choose a model before requesting online roasts."
            ),
            wraplength=520,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Label(config, text="Model:").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.roasting_model_combo = ttk.Combobox(
            config,
            textvariable=self.roasting_model_var,
            values=GENERAL_CHAT_MODELS,
            state="readonly",
        )
        self.roasting_model_combo.grid(row=2, column=1, sticky="ew", pady=(12, 0))

        ttk.Label(
            config,
            text="Models are drawn from the shared OpenRouter catalog.",
            wraplength=320,
        ).grid(row=2, column=2, sticky="w", padx=(12, 0), pady=(12, 0))

        controls = ttk.Frame(parent)
        controls.pack(fill="x", padx=24, pady=(0, 12))

        ttk.Label(controls, text="Persona:").pack(side="left")
        persona_menu = ttk.OptionMenu(
            controls,
            self.roasting_voice_var,
            self.roasting_voice_var.get(),
            *ROASTING_PERSONAS.keys(),
            command=lambda *_: self._load_roasting_history(self.roasting_voice_var.get()),
        )
        persona_menu.pack(side="left", padx=(6, 12))

        context = ttk.Frame(parent)
        context.pack(fill="x", padx=24, pady=(0, 12))

        ttk.Label(context, text="Game:").pack(side="left")
        self.roasting_game_combo = ttk.Combobox(
            context,
            textvariable=self.roasting_game_var,
            values=[""],
            width=40,
            state="readonly",
        )
        self.roasting_game_combo.pack(side="left", padx=(6, 12))

        clear_game_button = ttk.Button(
            context,
            text="Clear Game",
            command=lambda: self.roasting_game_var.set(""),
        )
        clear_game_button.pack(side="left")

        os_check = ttk.Checkbutton(
            context,
            text="Include operating system context",
            variable=self.include_os_var,
        )
        os_check.pack(side="left", padx=(18, 0))

        self.roasting_clear_button = ttk.Button(
            controls,
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
        self._refresh_roasting_games()

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

    def _append_media_output(self, message: str) -> None:
        """Append a plain text line to the media server output area."""

        if not hasattr(self, "media_output"):
            return

        widget = self.media_output
        state = widget.cget("state")
        if state == "disabled":
            widget.configure(state="normal")
        widget.insert(tk.END, f"{message.rstrip()}\n")
        if state == "disabled":
            widget.configure(state="disabled")
        widget.see(tk.END)

    def clear_media_output(self) -> None:
        """Clear the media server transcript."""

        if hasattr(self, "media_output"):
            self._clear_text_widget(self.media_output)
        self._append_media_output("Output cleared.")

    def _set_general_busy(self, busy: bool, status: str | None = None) -> None:
        """Enable or disable general chat controls."""

        self.general_busy = busy
        state = "disabled" if busy else "normal"
        self.general_send_button.configure(state=state)
        self.general_clear_button.configure(state=state)
        self.api_key_apply_button.configure(state=state)
        if hasattr(self, "roasting_api_key_apply_button"):
            self.roasting_api_key_apply_button.configure(state=state)

        if status is None:
            persona = self.general_persona_var.get()
            status = (
                f"{persona} is contacting OpenRouter..."
                if busy
                else f"{persona} ready for your next prompt."
            )
        self.general_status_var.set(status)

    def _set_jellyfin_busy(self, busy: bool, status: str | None = None) -> None:
        """Enable or disable Jellyfin controls and update status text."""

        self.jellyfin_busy = busy
        state = "disabled" if busy else "normal"
        for button in self.media_action_buttons:
            button.configure(state=state)

        if status is not None:
            self.media_status_var.set(status)
        elif not busy:
            self.media_status_var.set("Media server idle.")

    def _start_jellyfin_task(
        self,
        description: str,
        worker: Callable[[], tuple[str, Sequence[str]]],
        *,
        pre_message: str | None = None,
        clear_output: bool = False,
    ) -> None:
        """Run a Jellyfin request in the background."""

        if self.jellyfin_busy:
            messagebox.showinfo(
                "Media Server", "A Jellyfin request is already in progress. Please wait."
            )
            return

        if clear_output and hasattr(self, "media_output"):
            self._clear_text_widget(self.media_output)
        if pre_message:
            self._append_media_output(pre_message)

        self._set_jellyfin_busy(True, description)

        def run() -> None:
            try:
                status, lines = worker()
            except Exception as exc:  # pragma: no cover - network dependent
                self.after(0, lambda exc=exc: self._complete_jellyfin_task(error=exc))
                return
            self.after(
                0,
                lambda status=status, lines=list(lines): self._complete_jellyfin_task(
                    status=status, lines=lines
                ),
            )

        threading.Thread(target=run, daemon=True).start()

    def _complete_jellyfin_task(
        self,
        *,
        status: str | None = None,
        lines: Sequence[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        """Finalize a Jellyfin request on the main thread."""

        if error:
            self._append_media_output(f"Error: {error}")
            self._set_jellyfin_busy(False, "Media server request failed.")
            messagebox.showerror("Media Server", f"Jellyfin request failed:\n\n{error}")
            return

        if lines:
            for line in lines:
                self._append_media_output(line)

        final_status = status or "Media server request complete."
        self._set_jellyfin_busy(False, final_status)

    def _sanitize_jellyfin_inputs(self) -> tuple[str, str, str]:
        """Return trimmed Jellyfin credentials."""

        base_url = self.jellyfin_server_var.get().strip()
        api_key = self.jellyfin_api_key_var.get().strip()
        user_id = self.jellyfin_user_id_var.get().strip()
        return base_url, api_key, user_id

    def test_jellyfin_connection(self) -> None:
        """Validate the Jellyfin server connection."""

        base_url, api_key, _ = self._sanitize_jellyfin_inputs()
        if not base_url:
            messagebox.showerror("Media Server", "Enter the Jellyfin server URL before testing.")
            return

        def worker() -> tuple[str, Sequence[str]]:
            info = fetch_system_info(base_url, api_key=api_key or None)
            server_name = info.get("ServerName") or info.get("ProductName") or "Jellyfin"
            version = info.get("Version") or "Unknown version"
            os_name = info.get("OperatingSystem") or "Unknown operating system"
            startup = "Yes" if info.get("StartupWizardCompleted") else "No"
            lines = [
                f"Server Name: {server_name}",
                f"Version: {version}",
                f"Operating System: {os_name}",
                f"Server ID: {info.get('Id', 'n/a')}",
                f"Startup wizard completed: {startup}",
            ]
            return (f"Connected to {server_name}.", lines)

        self._start_jellyfin_task(
            "Testing Jellyfin connection...",
            worker,
            pre_message="Testing Jellyfin connection...",
        )

    def fetch_jellyfin_libraries(self) -> None:
        """Fetch libraries available to the configured Jellyfin user."""

        base_url, api_key, user_id = self._sanitize_jellyfin_inputs()
        if not base_url or not api_key or not user_id:
            messagebox.showerror(
                "Media Server",
                "Provide the Jellyfin server URL, API key, and user ID before fetching libraries.",
            )
            return

        def worker() -> tuple[str, Sequence[str]]:
            views = fetch_user_views(base_url, api_key=api_key, user_id=user_id)
            if not views:
                return ("No libraries returned.", ["No libraries were found for this user."])

            lines = ["Discovered libraries:"]
            for view in views:
                name = view.get("Name") or "Unnamed library"
                collection = view.get("CollectionType") or view.get("MediaType") or "Unknown type"
                view_id = view.get("Id", "n/a")
                lines.append(f"- {name} ({collection}) • Id: {view_id}")

            return (f"Found {len(views)} libraries.", lines)

        self._start_jellyfin_task(
            "Fetching Jellyfin libraries...",
            worker,
            pre_message="Requesting libraries from Jellyfin...",
            clear_output=True,
        )

    def fetch_jellyfin_recent_media(self) -> None:
        """Retrieve recently added media items."""

        base_url, api_key, user_id = self._sanitize_jellyfin_inputs()
        if not base_url or not api_key or not user_id:
            messagebox.showerror(
                "Media Server",
                "Provide the Jellyfin server URL, API key, and user ID before requesting recent media.",
            )
            return

        def worker() -> tuple[str, Sequence[str]]:
            items = fetch_recent_media(base_url, api_key=api_key, user_id=user_id)
            if not items:
                return ("No recent media reported.", ["No recent media items were returned."])

            lines = ["Recently added media:"]
            for item in items:
                name = item.get("Name") or "Unnamed item"
                media_type = item.get("Type") or item.get("MediaType") or "Unknown category"
                series = item.get("SeriesName")
                episode = item.get("IndexNumber")
                season = item.get("ParentIndexNumber")
                created = item.get("DateCreated")
                created_display = (
                    created.replace("T", " ")[:19] if isinstance(created, str) else "Unknown date"
                )

                detail_parts = [media_type]
                if series:
                    detail_parts.append(series)
                if season is not None and episode is not None:
                    detail_parts.append(f"S{season}E{episode}")

                detail = " • ".join(str(part) for part in detail_parts if part)
                lines.append(f"- {name} ({detail}) • Added: {created_display}")

            return (f"Retrieved {len(items)} media items.", lines)

        self._start_jellyfin_task(
            "Fetching recently added media...",
            worker,
            pre_message="Requesting recently added media...",
            clear_output=True,
        )

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
        if not self.roasting_busy:
            self.roasting_status_var.set("Validating OpenRouter API key...")

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
                if not self.roasting_busy:
                    self.roasting_status_var.set(
                        "OpenRouter key invalid. Offline generator remains available."
                    )
                return

            self.api_key_valid = True
            self._validated_api_key = api_key
            self._set_general_busy(False, "API key validated. Ready to chat.")
            if not self.roasting_busy:
                self.roasting_status_var.set(
                    "API key validated. Select a model before requesting online roasts."
                )

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

    def _handle_game_selection(self, event: tk.Event | None = None) -> None:
        """Sync launcher selection with the roasting focus picker."""

        self._update_launch_button_state()

        if not hasattr(self, "roasting_game_var"):
            return

        selection = self.tree.selection()
        if not selection:
            return

        app_id = selection[0]
        game = next((game for game in self.games if game.app_id == app_id), None)
        if game is None:
            return

        self.roasting_game_var.set(game.name)

    def _update_launch_button_state(self) -> None:
        """Enable or disable the launch button based on selection."""

        if self.tree.selection():
            self.launch_button.configure(state="normal")
        else:
            self.launch_button.configure(state="disabled")

    def _set_status(self, message: str) -> None:
        """Update the status bar text."""

        self.status_var.set(message)

    def _refresh_roasting_games(self) -> None:
        """Refresh the roasting game selector with the latest scan results."""

        if not hasattr(self, "roasting_game_combo"):
            return

        names = sorted({game.name for game in self.games})
        values = [""] + names
        self.roasting_game_combo.configure(values=values)

        current = self.roasting_game_var.get()
        if current and current not in names:
            self.roasting_game_var.set("")

    def scan_for_games(self) -> None:
        """Discover Steam games and populate the tree view."""

        self._set_status("Scanning Steam libraries...")
        self.update_idletasks()

        libraries = discover_steam_libraries()
        games = find_installed_games(libraries)
        self.games = games
        self._refresh_roasting_games()

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
        self._handle_game_selection()
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
                self.general_status_var.set(
                    "Apply your OpenRouter key to enable OpenRouter chat and roasts."
                )
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

    def _uses_openrouter_for_roasts(self) -> bool:
        """Return True if OpenRouter should be used for roast generation."""

        model_name = ""
        if hasattr(self, "roasting_model_var"):
            model_name = self.roasting_model_var.get().strip()
        return self.api_key_valid and bool(self._validated_api_key) and bool(model_name)

    def _compose_roast_prompt(self, base_prompt: str) -> str:
        """Combine user input, selected game, and OS details into a single prompt."""

        lines: List[str] = []
        game_name = self.roasting_game_var.get().strip()
        if game_name:
            lines.append(f"Game: {game_name}")
        if self.include_os_var.get():
            lines.append(f"Operating System: {self._os_summary}")
        trimmed = base_prompt.strip()
        if trimmed:
            lines.append(f"Focus: {trimmed}")
        else:
            lines.append("Focus: Deliver a general-purpose roast suitable for the test subject.")

        header = (
            "Roast the subject using the persona's trademark tone. Keep the reply to 3-4 vivid sentences. "
            "Lean into dark humor where appropriate while staying playful."
        )
        context = "\n".join(lines)
        return f"{header}\n\nContext:\n{context}"

    def _prepare_roasting_payload(self, history: Sequence[Dict[str, str]], prompt: str) -> List[Dict[str, str]]:
        """Return a copy of the roasting history with the latest message updated for context."""

        payload = [dict(message) for message in history]
        if payload:
            payload[-1] = dict(payload[-1])
            payload[-1]["content"] = prompt
        return payload

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
            messagebox.showinfo("Roasting Chamber", "Provide something for the persona to roast.")
            return

        persona = self.roasting_voice_var.get()
        history = self._current_roasting_history()
        history.append({"role": "user", "content": content})
        self._append_chat_message(self.roasting_display, "You", content)
        self.roasting_input.delete("1.0", tk.END)
        self._set_roasting_busy(True, f"{persona} is composing a roast...")

        contextual_prompt = self._compose_roast_prompt(content)
        self._last_roasting_prompt = contextual_prompt

        uses_openrouter = self._uses_openrouter_for_roasts()
        if uses_openrouter:
            payload = self._prepare_roasting_payload(history, contextual_prompt)
            model = self.roasting_model_var.get().strip()
            self._pending_roasting_persona = persona
            self.roasting_status_var.set(
                f"{persona} is consulting {model} via OpenRouter for a roast..."
            )
            request_chat_completion(
                self._validated_api_key,
                model,
                payload,
                self._handle_roasting_completion,
                scheduler=self.after,
            )
            return

        if (
            self.api_key_valid
            and bool(self._validated_api_key)
            and not self.roasting_model_var.get().strip()
        ):
            self.roasting_status_var.set(
                "Select an OpenRouter model to enable online roasts. Using offline fallback."
            )

        def finalize_roast() -> None:
            try:
                roast = generate_roast(persona, contextual_prompt, rng=self._rng)
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

    def _handle_roasting_completion(self, error: Exception | None, content: str | None) -> None:
        """Handle the result of an OpenRouter roast request."""

        persona = self._pending_roasting_persona or self.roasting_voice_var.get()
        history = self.roasting_histories.setdefault(
            persona, [self._system_message(ROASTING_PERSONAS[persona])]
        )
        self._pending_roasting_persona = None

        if error or not content:
            try:
                fallback = generate_roast(persona, self._last_roasting_prompt, rng=self._rng)
            except Exception as exc:  # pragma: no cover - defensive
                history.append(
                    {
                        "role": "assistant",
                        "content": f"Roast generation failed entirely: {exc}",
                    }
                )
                if persona == self.roasting_voice_var.get():
                    if error:
                        self._append_chat_message(
                            self.roasting_display,
                            "System",
                            f"OpenRouter roast failed: {error}",
                        )
                    else:
                        self._append_chat_message(
                            self.roasting_display,
                            "System",
                            "OpenRouter returned no roast and the offline fallback also failed.",
                        )
                    self._set_roasting_busy(False, "Roast generation failed.")
                else:
                    self._set_roasting_busy(False)
                return

            history.append({"role": "assistant", "content": fallback})
            if persona == self.roasting_voice_var.get():
                failure_reason = (
                    f"OpenRouter roast failed ({error})." if error else "OpenRouter returned no roast."
                )
                self._append_chat_message(
                    self.roasting_display,
                    "System",
                    f"{failure_reason} Falling back to the offline generator.",
                )
                self._append_chat_message(self.roasting_display, persona, fallback)
                self._set_roasting_busy(False, f"{persona} delivered a fallback roast.")
            else:
                self._set_roasting_busy(False)
            return

        history.append({"role": "assistant", "content": content})
        if persona == self.roasting_voice_var.get():
            self._append_chat_message(self.roasting_display, persona, content)
            self._set_roasting_busy(False, f"{persona} delivered an OpenRouter roast.")
        else:
            self._set_roasting_busy(False)

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
