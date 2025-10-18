"""Tkinter GUI for the Aperture Science Enrichment Center launcher."""

from __future__ import annotations

import multiprocessing as mp
import os
import platform
import queue
import random
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Sequence

import webbrowser

try:  # pragma: no cover - optional dependency
    import webview  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    webview = None


def _run_jellyfin_webview(url: str, width: int, height: int, status_queue: mp.Queue) -> None:
    """Create and manage a pywebview window in a standalone process."""

    if webview is None:
        try:
            status_queue.put_nowait(
                ("error", "Install the 'pywebview' package to enable the embedded Jellyfin portal.")
            )
        finally:
            status_queue.close()
        return

    try:
        webview.create_window(
            "Jellyfin Web UI",
            url,
            width=width,
            height=height,
            resizable=True,
        )
        status_queue.put_nowait(("started", "Embedded Jellyfin portal running."))
        webview.start()
        status_queue.put_nowait(("closed", "Embedded Jellyfin portal closed."))
    except Exception as exc:  # pragma: no cover - platform dependent
        status_queue.put_nowait(("error", str(exc)))
    finally:
        status_queue.close()

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
    JELLYFIN_WEB_UI_URL,
    JELLYFIN_WEB_UI_URL_ENV,
    OPENROUTER_API_KEY_ENV,
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
        self.general_status_var = tk.StringVar(
            value="Apply your OpenRouter key to enable OpenRouter chat and roasts."
        )
        self.roasting_status_var = tk.StringVar(
            value="Select a persona, choose an OpenRouter model, and optionally pick a Steam game."
        )
        self.api_key_var = tk.StringVar(value=os.environ.get(OPENROUTER_API_KEY_ENV, ""))
        self.general_model_var = tk.StringVar(value=GENERAL_CHAT_MODELS[0])
        self.roasting_model_var = tk.StringVar(value=GENERAL_CHAT_MODELS[0])
        self.general_persona_var = tk.StringVar(value=list(GENERAL_CHAT_PERSONAS.keys())[0])
        self.roasting_voice_var = tk.StringVar(value=list(ROASTING_PERSONAS.keys())[0])
        self.roasting_game_var = tk.StringVar(value="")
        self.include_os_var = tk.BooleanVar(value=True)
        self.jellyfin_web_url_var = tk.StringVar(
            value=os.environ.get(JELLYFIN_WEB_UI_URL_ENV, JELLYFIN_WEB_UI_URL)
        )
        self.jellyfin_web_status_var = tk.StringVar(
            value=(
                "Launch the embedded Jellyfin portal or open it in your browser."
                if webview
                else "Open the Jellyfin portal in your browser. Install pywebview for an embedded view."
            )
        )

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

        self._jellyfin_webview_process: mp.Process | None = None
        self._jellyfin_webview_queue: mp.Queue | None = None

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
        self.jellyfin_web_tab = ttk.Frame(self.notebook)
        self.roasting_chat_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.launcher_tab, text="Launcher")
        self.notebook.add(self.general_chat_tab, text="General Chat")
        self.notebook.add(self.jellyfin_web_tab, text="Jellyfin Web")
        self.notebook.add(self.roasting_chat_tab, text="Roasting Chamber")

        self._build_launcher_tab(self.launcher_tab)
        self._build_general_chat_tab(self.general_chat_tab)
        self._build_jellyfin_web_tab(self.jellyfin_web_tab)
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

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        layout = ttk.Frame(parent)
        layout.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        layout.columnconfigure(0, weight=3)
        layout.columnconfigure(1, weight=2)
        layout.rowconfigure(0, weight=1)

        conversation = ttk.Frame(layout)
        conversation.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        conversation.columnconfigure(0, weight=1)
        conversation.rowconfigure(1, weight=1)

        status_bar = ttk.Frame(conversation)
        status_bar.grid(row=0, column=0, sticky="ew")
        status_bar.columnconfigure(0, weight=1)

        self.general_status_label = ttk.Label(status_bar, textvariable=self.general_status_var)
        self.general_status_label.grid(row=0, column=0, sticky="w")

        self.general_clear_button = ttk.Button(
            status_bar,
            text="Clear Conversation",
            command=self.clear_general_conversation,
        )
        self.general_clear_button.grid(row=0, column=1, sticky="e")

        transcript = ttk.Frame(conversation)
        transcript.grid(row=1, column=0, sticky="nsew", pady=(12, 12))
        transcript.columnconfigure(0, weight=1)
        transcript.rowconfigure(0, weight=1)

        self.general_display = tk.Text(
            transcript,
            wrap="word",
            state="disabled",
            height=18,
            relief="flat",
            bd=0,
        )
        self._text_widgets.append(self.general_display)
        self.general_display.grid(row=0, column=0, sticky="nsew")

        general_scrollbar = ttk.Scrollbar(transcript, orient="vertical", command=self.general_display.yview)
        general_scrollbar.grid(row=0, column=1, sticky="ns")
        self.general_display.configure(yscrollcommand=general_scrollbar.set)

        input_frame = ttk.Frame(conversation)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        self.general_input = tk.Text(input_frame, wrap="word", height=4)
        self.general_input.grid(row=0, column=0, sticky="ew")
        self._text_widgets.append(self.general_input)

        self.general_send_button = ttk.Button(
            input_frame,
            text="Send",
            command=self.send_general_message,
        )
        self.general_send_button.grid(row=0, column=1, padx=(12, 0))

        sidebar = ttk.LabelFrame(layout, text="Conversation Setup")
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(sidebar, text="API Key:").grid(row=row, column=0, sticky="w")
        self.api_key_entry = ttk.Entry(sidebar, textvariable=self.api_key_var, show="*", width=28)
        self.api_key_entry.grid(row=row, column=1, sticky="ew")
        self.api_key_apply_button = ttk.Button(
            sidebar,
            text="Apply Key",
            command=self.apply_api_key,
        )
        self.api_key_apply_button.grid(row=row, column=2, padx=(12, 0))
        row += 1

        ttk.Label(
            sidebar,
            text=(
                "Enter your OpenRouter API key to enable cloud conversation features. "
                "The key remains in memory only for this session."
            ),
            wraplength=320,
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 12))
        row += 1

        ttk.Label(sidebar, text="Persona:").grid(row=row, column=0, sticky="w")
        persona_menu = ttk.OptionMenu(
            sidebar,
            self.general_persona_var,
            self.general_persona_var.get(),
            *GENERAL_CHAT_PERSONAS.keys(),
            command=lambda value: self._load_general_history(value),
        )
        persona_menu.grid(row=row, column=1, columnspan=2, sticky="ew", pady=(0, 6))
        row += 1

        ttk.Label(sidebar, text="Model:").grid(row=row, column=0, sticky="w")
        self.general_model_combo = ttk.Combobox(
            sidebar,
            textvariable=self.general_model_var,
            values=GENERAL_CHAT_MODELS,
            state="readonly",
        )
        self.general_model_combo.grid(row=row, column=1, columnspan=2, sticky="ew")
        row += 1

        sidebar.rowconfigure(row, weight=1)

        self._load_general_history(self.general_persona_var.get())

    def _build_jellyfin_web_tab(self, parent: ttk.Frame) -> None:
        """Provide shortcuts for loading the Jellyfin web interface."""

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        header = ttk.Frame(parent)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self.jellyfin_web_status_var).grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(header)
        actions.grid(row=0, column=1, sticky="e")

        if webview is not None:
            ttk.Button(actions, text="Open Embedded View", command=self._launch_embedded_jellyfin).pack(
                side="left"
            )
        ttk.Button(actions, text="Open in Browser", command=self._open_jellyfin_in_browser).pack(
            side="left", padx=(12, 0)
        )

        info = ttk.LabelFrame(parent, text="Jellyfin Portal")
        info.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))
        info.columnconfigure(0, weight=1)

        ttk.Label(
            info,
            text=(
                "Use the embedded view for a browser-like experience without leaving the launcher. "
                "The embedded mode relies on the optional 'pywebview' package; install it to enable the feature."
            ),
            wraplength=520,
        ).grid(row=0, column=0, sticky="w")

        url_frame = ttk.Frame(info)
        url_frame.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        url_frame.columnconfigure(0, weight=1)

        ttk.Label(url_frame, text="Portal URL:").grid(row=0, column=0, sticky="w")

        self.jellyfin_url_entry = ttk.Entry(
            url_frame,
            width=62,
            textvariable=self.jellyfin_web_url_var,
        )
        self.jellyfin_url_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        buttons = ttk.Frame(url_frame)
        buttons.grid(row=1, column=1, sticky="e", padx=(12, 0))

        ttk.Button(buttons, text="Copy", command=self._copy_jellyfin_web_url).pack(side="left")
        ttk.Button(buttons, text="Refresh Status", command=self._refresh_jellyfin_web_status).pack(
            side="left", padx=(12, 0)
        )

    def _get_jellyfin_web_url(self) -> str:
        """Return the trimmed Jellyfin portal URL."""

        return self.jellyfin_web_url_var.get().strip()

    def _require_jellyfin_web_url(self) -> str | None:
        """Validate the Jellyfin web URL field and return it when usable."""

        url = self._get_jellyfin_web_url()
        if not url:
            self.jellyfin_web_status_var.set("Enter the Jellyfin portal address before continuing.")
            messagebox.showerror(
                "Jellyfin Web",
                "Enter the Jellyfin web portal URL you want to use before continuing.",
            )
            return None

        if not url.startswith(("http://", "https://")):
            self.jellyfin_web_status_var.set("Provide a full http(s) Jellyfin web address.")
            messagebox.showerror(
                "Jellyfin Web",
                "Provide a full http:// or https:// address for the Jellyfin web portal.",
            )
            return None

        return url

    def _build_roasting_chat_tab(self, parent: ttk.Frame) -> None:
        """Create the roasting chatbot interface with persona switching."""

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        layout = ttk.Frame(parent)
        layout.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        layout.columnconfigure(0, weight=3)
        layout.columnconfigure(1, weight=2)
        layout.rowconfigure(0, weight=1)

        conversation = ttk.Frame(layout)
        conversation.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        conversation.columnconfigure(0, weight=1)
        conversation.rowconfigure(1, weight=1)

        status_bar = ttk.Frame(conversation)
        status_bar.grid(row=0, column=0, sticky="ew")
        status_bar.columnconfigure(0, weight=1)

        self.roasting_status_label = ttk.Label(status_bar, textvariable=self.roasting_status_var)
        self.roasting_status_label.grid(row=0, column=0, sticky="w")

        self.roasting_clear_button = ttk.Button(
            status_bar,
            text="Clear Persona History",
            command=self.clear_roasting_conversation,
        )
        self.roasting_clear_button.grid(row=0, column=1, sticky="e")

        transcript = ttk.Frame(conversation)
        transcript.grid(row=1, column=0, sticky="nsew", pady=(12, 12))
        transcript.columnconfigure(0, weight=1)
        transcript.rowconfigure(0, weight=1)

        self.roasting_display = tk.Text(
            transcript,
            wrap="word",
            state="disabled",
            height=18,
            relief="flat",
            bd=0,
        )
        self._text_widgets.append(self.roasting_display)
        self.roasting_display.grid(row=0, column=0, sticky="nsew")

        roast_scrollbar = ttk.Scrollbar(transcript, orient="vertical", command=self.roasting_display.yview)
        roast_scrollbar.grid(row=0, column=1, sticky="ns")
        self.roasting_display.configure(yscrollcommand=roast_scrollbar.set)

        input_frame = ttk.Frame(conversation)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)

        self.roasting_input = tk.Text(input_frame, wrap="word", height=4)
        self.roasting_input.grid(row=0, column=0, sticky="ew")
        self._text_widgets.append(self.roasting_input)

        self.roasting_send_button = ttk.Button(
            input_frame,
            text="Roast",
            command=self.send_roasting_message,
        )
        self.roasting_send_button.grid(row=0, column=1, padx=(12, 0))

        sidebar = ttk.LabelFrame(layout, text="Roasting Controls")
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(sidebar, text="API Key:").grid(row=row, column=0, sticky="w")
        self.roasting_api_key_entry = ttk.Entry(sidebar, textvariable=self.api_key_var, show="*", width=28)
        self.roasting_api_key_entry.grid(row=row, column=1, sticky="ew")
        self.roasting_api_key_apply_button = ttk.Button(
            sidebar,
            text="Apply Key",
            command=self.apply_api_key,
        )
        self.roasting_api_key_apply_button.grid(row=row, column=2, padx=(12, 0))
        row += 1

        ttk.Label(
            sidebar,
            text=(
                "Roasting Chamber shares the OpenRouter configuration with General Chat. "
                "Validate your key, then choose a model, persona, and optional game context."
            ),
            wraplength=320,
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 12))
        row += 1

        ttk.Label(sidebar, text="Model:").grid(row=row, column=0, sticky="w")
        self.roasting_model_combo = ttk.Combobox(
            sidebar,
            textvariable=self.roasting_model_var,
            values=GENERAL_CHAT_MODELS,
            state="readonly",
        )
        self.roasting_model_combo.grid(row=row, column=1, columnspan=2, sticky="ew")
        row += 1

        ttk.Label(sidebar, text="Persona:").grid(row=row, column=0, sticky="w", pady=(8, 0))
        persona_menu = ttk.OptionMenu(
            sidebar,
            self.roasting_voice_var,
            self.roasting_voice_var.get(),
            *ROASTING_PERSONAS.keys(),
            command=lambda *_: self._load_roasting_history(self.roasting_voice_var.get()),
        )
        persona_menu.grid(row=row, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        row += 1

        ttk.Label(sidebar, text="Game Context:").grid(row=row, column=0, sticky="w", pady=(8, 0))
        game_row = ttk.Frame(sidebar)
        game_row.grid(row=row, column=1, columnspan=2, sticky="ew", pady=(8, 0))
        game_row.columnconfigure(0, weight=1)

        self.roasting_game_combo = ttk.Combobox(
            game_row,
            textvariable=self.roasting_game_var,
            values=[""],
            state="readonly",
        )
        self.roasting_game_combo.grid(row=0, column=0, sticky="ew")

        ttk.Button(
            game_row,
            text="Clear",
            command=lambda: self.roasting_game_var.set(""),
        ).grid(row=0, column=1, padx=(12, 0))
        row += 1

        ttk.Checkbutton(
            sidebar,
            text="Include operating system context",
            variable=self.include_os_var,
        ).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        sidebar.rowconfigure(row, weight=1)

        self._load_roasting_history(self.roasting_voice_var.get())
        self._refresh_roasting_games()

    def _open_jellyfin_in_browser(self) -> None:
        """Launch the Jellyfin portal in the default system browser."""

        url = self._require_jellyfin_web_url()
        if url is None:
            return

        try:
            if not webbrowser.open(url, new=2, autoraise=True):
                raise RuntimeError("The web browser reported it could not open the URL.")
        except Exception as exc:
            self.jellyfin_web_status_var.set("Failed to launch browser for the Jellyfin portal.")
            messagebox.showerror("Jellyfin Web", f"Unable to open the Jellyfin portal:\n\n{exc}")
            return

        self.jellyfin_web_status_var.set("Opened the Jellyfin portal in your default browser.")

    def _launch_embedded_jellyfin(self) -> None:
        """Launch the Jellyfin portal inside a pywebview window if available."""

        url = self._require_jellyfin_web_url()
        if url is None:
            return

        if webview is None:
            messagebox.showinfo(
                "Jellyfin Web",
                "Install the 'pywebview' package to enable the embedded browser.\n\n"
                "Opening the Jellyfin portal in your web browser instead.",
            )
            self._open_jellyfin_in_browser()
            return

        if self._jellyfin_webview_process and self._jellyfin_webview_process.is_alive():
            self.jellyfin_web_status_var.set("Embedded Jellyfin portal already running.")
            return

        status_queue: mp.Queue = mp.Queue()
        process = mp.Process(
            target=_run_jellyfin_webview,
            args=(url, 1200, 720, status_queue),
            daemon=True,
        )

        try:
            process.start()
        except Exception as exc:  # pragma: no cover - platform dependent
            status_queue.close()
            self._handle_webview_failure(exc)
            return

        self._jellyfin_webview_queue = status_queue
        self._jellyfin_webview_process = process
        self.jellyfin_web_status_var.set("Launching embedded Jellyfin portal...")
        self.after(200, self._poll_jellyfin_webview_status)

    def _poll_jellyfin_webview_status(self) -> None:
        """Monitor the background pywebview process and reflect its state in the UI."""

        process = self._jellyfin_webview_process
        status_queue = self._jellyfin_webview_queue
        if process is None or status_queue is None:
            return

        try:
            while True:
                state, message = status_queue.get_nowait()
                if state == "started":
                    self.jellyfin_web_status_var.set(message)
                elif state == "closed":
                    self._clear_jellyfin_webview_state(closed=True)
                    return
                elif state == "error":
                    self._handle_webview_failure(RuntimeError(message))
                    self._clear_jellyfin_webview_state(closed=False)
                    return
        except queue.Empty:
            pass

        if process.is_alive():
            self.after(250, self._poll_jellyfin_webview_status)
            return

        exit_code = process.exitcode
        if exit_code == 0:
            self._clear_jellyfin_webview_state(closed=True)
        else:
            self._handle_webview_failure(
                RuntimeError("Embedded Jellyfin portal exited unexpectedly.")
            )
            self._clear_jellyfin_webview_state(closed=False)

    def _handle_webview_failure(self, exc: Exception) -> None:
        """Handle failures when starting the embedded Jellyfin window."""

        self.jellyfin_web_status_var.set("Failed to launch the embedded Jellyfin portal.")
        messagebox.showerror(
            "Jellyfin Web",
            "Unable to start the embedded Jellyfin portal window.\n\n"
            f"{exc}",
        )

    def _clear_jellyfin_webview_state(self, *, closed: bool) -> None:
        """Reset embedded Jellyfin window bookkeeping."""

        process = self._jellyfin_webview_process
        status_queue = self._jellyfin_webview_queue

        self._jellyfin_webview_process = None
        self._jellyfin_webview_queue = None

        if status_queue is not None:
            try:
                status_queue.close()
            except Exception:
                pass
            try:
                status_queue.cancel_join_thread()
            except Exception:
                pass

        if process is not None:
            try:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=0.5)
            except Exception:
                pass

        if closed:
            self.jellyfin_web_status_var.set(
                "Embedded Jellyfin portal closed. Launch again or open it in your browser."
            )

    def _copy_jellyfin_web_url(self) -> None:
        """Copy the Jellyfin portal URL to the clipboard."""

        url = self._get_jellyfin_web_url()
        if not url:
            self.jellyfin_web_status_var.set("Enter the Jellyfin portal address before copying.")
            messagebox.showerror(
                "Jellyfin Web",
                "Enter a Jellyfin web portal URL before copying it to the clipboard.",
            )
            return

        try:
            self.clipboard_clear()
            self.clipboard_append(url)
        except Exception as exc:  # pragma: no cover - platform dependent
            self.jellyfin_web_status_var.set("Copy failed. Use the browser button instead.")
            messagebox.showerror("Jellyfin Web", f"Unable to copy the URL:\n\n{exc}")
            return

        self.jellyfin_web_status_var.set("Copied Jellyfin portal address to the clipboard.")

    def _refresh_jellyfin_web_status(self) -> None:
        """Reset the status text for the Jellyfin web tab."""

        self.jellyfin_web_status_var.set(
            "Enter your Jellyfin portal URL, then launch it here or in your browser."
            if webview
            else "Enter your Jellyfin portal URL and open it in your browser. Install pywebview for an embedded view."
        )

    def _apply_theme(self) -> None:
        """Update widget colors based on the selected theme."""

        palette = THEME_PALETTES[self.theme_var.get()]
        selected_tab_text = palette.get("text_on_accent", palette["text"])

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
            tabmargins=(12, 6, 12, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=palette["surface"],
            foreground=palette["text"],
            padding=(16, 8),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", palette["accent"]),
                ("active", palette["surface_highlight"]),
            ],
            foreground=[
                ("selected", selected_tab_text),
                ("active", palette["text"]),
            ],
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
