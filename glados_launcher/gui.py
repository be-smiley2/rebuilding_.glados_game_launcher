"""Tkinter based interface for the GLaDOS launcher."""
from __future__ import annotations

import json
import threading
import time
import webbrowser
from typing import Any, Dict, Optional

import platform
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk

from .achievements import AchievementManager
from .config import CURRENT_SCRIPT, CURRENT_VERSION, USER_PREFS_FILE
from .data_manager import GameDataManager
from .launcher import GameLauncher
from .scanner import SmartGameScanner
from .theme import ApertureTheme
from .tetris import TrainTetrisGame
from .doom import Doom2016MiniGame
from .doom_classic import DoomClassicEpisodeIMiniGame, DoomClassicEpisodeIIMiniGame
from .space_invaders import RapidFireSpaceInvaders
from .updates import AutoUpdateManager, UpdateApplyResult, UpdateCheckResult
from .dependencies import REQUESTS_AVAILABLE


class ApertureEnrichmentCenterGUI:
    def __init__(self) -> None:
        print("Initializing ApertureEnrichmentCenterGUI...")

        try:
            self.root = tk.Tk()
            print("Tkinter root window created")

            self.game_manager = GameDataManager()
            print("Game manager initialized")

            self.scanner = SmartGameScanner()
            print("Scanner initialized")

            self.launcher = GameLauncher(self.game_manager)
            self.achievement_manager = AchievementManager()
            self.update_manager = AutoUpdateManager(CURRENT_VERSION, CURRENT_SCRIPT)
            print("Managers initialized")

            self.update_check_in_progress = False
            self.update_install_in_progress = False
            self.update_available = False
            self.last_scan_results: Dict[str, Any] = {}
            self.user_preferences = self.load_preferences()
            self.theme_mode = self.user_preferences.get("theme_mode", ApertureTheme.current_mode)
            if self.theme_mode not in ApertureTheme.get_available_modes():
                self.theme_mode = "dark"
            self.user_preferences["theme_mode"] = self.theme_mode
            ApertureTheme.set_mode(self.theme_mode)
            self.smart_mode = True
            self.commentary_mode = tk.StringVar(value="balanced")
            self.theme_mode_var = tk.StringVar(value=self.theme_mode)
            self.update_status_var = tk.StringVar(value="Status: Idle")
            self.mini_game_summary_var = tk.StringVar(value="Awaiting simulation data.")
            self.mini_game_configs = [
                {"key": "train_tetris", "launcher": self.show_tetris},
                {"key": "space_invaders_rapid_fire", "launcher": self.show_space_invaders},
                {"key": "doom_slayer_training", "launcher": self.show_doom_training},
                {"key": "doom_classic_1", "launcher": self.show_doom_classic_episode_one},
                {"key": "doom_classic_2", "launcher": self.show_doom_classic_episode_two},
            ]
            self.mini_game_stats_vars: Dict[str, Dict[str, tk.StringVar]] = {}
            self.sidebar_notebook: Optional[ttk.Notebook] = None
            self.mini_games_tab: Optional[ttk.Frame] = None
            self.system_tab: Optional[ttk.Frame] = None
            self.check_updates_button: Optional[ttk.Button] = None
            self.apply_update_button: Optional[ttk.Button] = None
            self.tetris: Optional[TrainTetrisGame] = None
            self.space_invaders: Optional[RapidFireSpaceInvaders] = None
            self.doom_training: Optional[Doom2016MiniGame] = None
            self.doom_episode_one: Optional[DoomClassicEpisodeIMiniGame] = None
            self.doom_episode_two: Optional[DoomClassicEpisodeIIMiniGame] = None

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

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Error initializing GUI: {exc}")
            import traceback

            traceback.print_exc()
            raise

    def load_preferences(self) -> Dict[str, Any]:
        try:
            if USER_PREFS_FILE.exists():
                with USER_PREFS_FILE.open("r", encoding="utf-8") as handle:
                    prefs = json.load(handle)
                    if "last_update_check" not in prefs:
                        prefs["last_update_check"] = 0
                    if "theme_mode" not in prefs:
                        prefs["theme_mode"] = "dark"
                    return prefs
        except Exception:
            pass
        return {
            "smart_recommendations": True,
            "auto_sort": True,
            "commentary_level": "balanced",
            "last_update_check": 0,
            "theme_mode": "dark",
        }

    def save_preferences(self) -> None:
        try:
            with USER_PREFS_FILE.open("w", encoding="utf-8") as handle:
                json.dump(self.user_preferences, handle, indent=2)
        except Exception:
            pass

    def _apply_theme_to_root(self) -> None:
        self.root.configure(bg=ApertureTheme.PRIMARY_BG)
        self.root.option_add("*TCombobox*Listbox*Background", ApertureTheme.SECONDARY_BG)
        self.root.option_add("*TCombobox*Listbox*Foreground", ApertureTheme.TEXT_PRIMARY)
        self.root.option_add("*TCombobox*Listbox*Font", ApertureTheme.FONT_BASE)

    def _apply_theme_to_text_widgets(self) -> None:
        try:
            if hasattr(self, "commentary_text"):
                previous_state = self.commentary_text.cget("state")
                if previous_state == "disabled":
                    self.commentary_text.config(state="normal")
                self.commentary_text.configure(
                    bg=ApertureTheme.SECONDARY_BG,
                    fg=ApertureTheme.TEXT_PRIMARY,
                    insertbackground=ApertureTheme.TEXT_PRIMARY,
                )
                if previous_state == "disabled":
                    self.commentary_text.config(state="disabled")
            if hasattr(self, "rec_text"):
                previous_state = self.rec_text.cget("state")
                if previous_state == "disabled":
                    self.rec_text.config(state="normal")
                self.rec_text.configure(
                    bg=ApertureTheme.SECONDARY_BG,
                    fg=ApertureTheme.TEXT_SECONDARY,
                    insertbackground=ApertureTheme.TEXT_PRIMARY,
                )
                if previous_state == "disabled":
                    self.rec_text.config(state="disabled")
        except Exception:
            pass

    def _refresh_theme(self) -> None:
        self._apply_theme_to_root()
        self.setup_styles()
        self._apply_theme_to_text_widgets()
        try:
            self.root.update_idletasks()
        except Exception:
            pass

    def set_theme_mode(self, mode: str) -> None:
        normalized = mode.lower()
        if normalized not in ApertureTheme.get_available_modes():
            return
        if normalized == getattr(self, "theme_mode", ""):
            return

        self.theme_mode = normalized
        self.theme_mode_var.set(normalized)
        self.user_preferences["theme_mode"] = normalized
        self.save_preferences()

        ApertureTheme.set_mode(normalized)
        self._refresh_theme()

    def setup_gui(self) -> None:
        self.root.title(f"Aperture Science Enrichment Center - Game Management v{CURRENT_VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        self._apply_theme_to_root()

        try:
            self.root.iconname("Aperture Science")
        except Exception:
            pass

    def setup_styles(self) -> None:
        if not hasattr(self, "style"):
            self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("Aperture.TFrame", background=ApertureTheme.PRIMARY_BG)
        self.style.configure("Panel.TFrame", background=ApertureTheme.PANEL_BG, borderwidth=1, relief="ridge")
        self.style.configure("Header.TFrame", background=ApertureTheme.ACCENT_BG, borderwidth=0)

        self.style.configure(
            "Hero.TLabel",
            background=ApertureTheme.ACCENT_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_HEADING,
        )
        self.style.configure(
            "Subheading.TLabel",
            background=ApertureTheme.ACCENT_BG,
            foreground=ApertureTheme.WHEATLEY_BLUE,
            font=ApertureTheme.FONT_SUBHEADING,
        )
        self.style.configure(
            "PanelTitle.TLabel",
            background=ApertureTheme.PANEL_BG,
            foreground=ApertureTheme.TEXT_ACCENT,
            font=ApertureTheme.FONT_SUBHEADING,
        )
        self.style.configure(
            "PanelBody.TLabel",
            background=ApertureTheme.PANEL_BG,
            foreground=ApertureTheme.TEXT_SECONDARY,
            font=ApertureTheme.FONT_BASE,
        )
        self.style.configure(
            "PanelCaption.TLabel",
            background=ApertureTheme.PANEL_BG,
            foreground=ApertureTheme.TEXT_MUTED,
            font=ApertureTheme.FONT_SMALL,
        )
        self.style.configure(
            "AccentCaption.TLabel",
            background=ApertureTheme.ACCENT_BG,
            foreground=ApertureTheme.TEXT_MUTED,
            font=ApertureTheme.FONT_SMALL,
        )
        self.style.configure(
            "Aperture.TLabel",
            background=ApertureTheme.PRIMARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BASE,
        )
        self.style.configure(
            "MiniStats.TLabel",
            background=ApertureTheme.PANEL_BG,
            foreground=ApertureTheme.TEXT_SECONDARY,
            font=ApertureTheme.FONT_SMALL,
        )

        self.style.configure(
            "Aperture.TNotebook",
            background=ApertureTheme.PRIMARY_BG,
            borderwidth=0,
        )
        self.style.configure(
            "Aperture.TNotebook.Tab",
            background=ApertureTheme.SECONDARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BASE,
            padding=(12, 6),
        )
        self.style.map(
            "Aperture.TNotebook.Tab",
            background=[("selected", ApertureTheme.ACCENT_BG)],
            foreground=[("selected", ApertureTheme.TEXT_PRIMARY)],
        )

        self.style.configure(
            "Aperture.TButton",
            background=ApertureTheme.BUTTON_NORMAL,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BUTTON,
            padding=(14, 6),
            borderwidth=0,
            focusthickness=0,
        )
        self.style.map(
            "Aperture.TButton",
            background=[("active", ApertureTheme.BUTTON_HOVER), ("pressed", ApertureTheme.BUTTON_ACTIVE)],
            relief=[("pressed", "sunken")],
        )

        self.style.configure(
            "GLaDOS.TButton",
            background=ApertureTheme.GLADOS_ORANGE,
            foreground=ApertureTheme.PRIMARY_BG,
            font=ApertureTheme.FONT_BUTTON,
            padding=(16, 6),
            borderwidth=0,
            focusthickness=0,
        )
        self.style.map(
            "GLaDOS.TButton",
            background=[("active", ApertureTheme.PORTAL_ORANGE), ("pressed", ApertureTheme.PORTAL_ORANGE)],
            relief=[("pressed", "sunken")],
        )

        self.style.configure(
            "Aperture.Treeview",
            background=ApertureTheme.SECONDARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            fieldbackground=ApertureTheme.SECONDARY_BG,
            borderwidth=0,
            rowheight=48,
            font=ApertureTheme.FONT_BASE,
        )
        self.style.configure(
            "Aperture.Treeview.Heading",
            background=ApertureTheme.ACCENT_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BUTTON,
            relief="flat",
        )
        self.style.map(
            "Aperture.Treeview.Heading",
            background=[("active", ApertureTheme.BUTTON_HOVER)],
            relief=[("pressed", "sunken")],
        )

        self.style.configure(
            "Aperture.TCheckbutton",
            background=ApertureTheme.PRIMARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BASE,
        )
        self.style.configure(
            "Aperture.TRadiobutton",
            background=ApertureTheme.PRIMARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BASE,
        )

        self.style.configure("Aperture.TSeparator", background=ApertureTheme.BORDER_LIGHT)
        self.style.configure(
            "TCombobox",
            fieldbackground=ApertureTheme.SECONDARY_BG,
            background=ApertureTheme.SECONDARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            arrowcolor=ApertureTheme.TEXT_PRIMARY,
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", ApertureTheme.SECONDARY_BG)],
            foreground=[("disabled", ApertureTheme.TEXT_MUTED)],
        )
        self.style.configure(
            "TEntry",
            fieldbackground=ApertureTheme.SECONDARY_BG,
            foreground=ApertureTheme.TEXT_PRIMARY,
            insertcolor=ApertureTheme.TEXT_PRIMARY,
        )

    def create_interface(self) -> None:
        main_container = ttk.Frame(self.root, style="Aperture.TFrame")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_header(main_container)

        content_paned = ttk.PanedWindow(main_container, orient="horizontal")
        content_paned.pack(fill="both", expand=True, pady=(10, 0))

        self.create_left_panel(content_paned)
        self.create_right_panel(content_paned)

        content_paned.add(self.left_panel, weight=3)
        content_paned.add(self.right_panel, weight=1)

    def create_header(self, parent: ttk.Frame) -> None:
        header_frame = ttk.Frame(parent, style="Header.TFrame", padding=(24, 18))
        header_frame.pack(fill="x", pady=(0, 12))

        title_frame = ttk.Frame(header_frame, style="Header.TFrame")
        title_frame.pack(fill="x")

        ttk.Label(title_frame, text="Aperture Science Enrichment Center", style="Hero.TLabel").pack(anchor="w")
        ttk.Label(
            title_frame,
            text="Advanced Test Subject Administration v2.5",
            style="AccentCaption.TLabel",
        ).pack(anchor="w", pady=(6, 0))

        ttk.Separator(header_frame, orient="horizontal", style="Aperture.TSeparator").pack(fill="x", pady=(18, 20))

        button_frame = ttk.Frame(header_frame, style="Header.TFrame")
        button_frame.pack(fill="x")

        scan_frame = ttk.Frame(button_frame, style="Header.TFrame")
        scan_frame.pack(side="left")
        ttk.Label(scan_frame, text="Scan Networks", style="AccentCaption.TLabel").pack(anchor="w", pady=(0, 8))

        scan_buttons = ttk.Frame(scan_frame, style="Header.TFrame")
        scan_buttons.pack()

        ttk.Button(scan_buttons, text="Full System Sweep", style="GLaDOS.TButton", command=self.run_smart_scan).pack(side="left", padx=(0, 6))

        platform_buttons = [
            ("Steam", lambda: self.run_platform_scan("steam")),
            ("Epic", lambda: self.run_platform_scan("epic")),
            ("Ubisoft", lambda: self.run_platform_scan("ubisoft")),
            ("GOG", lambda: self.run_platform_scan("gog")),
        ]

        for text, command in platform_buttons:
            ttk.Button(scan_buttons, text=text, style="Aperture.TButton", command=command).pack(side="left", padx=3)

        ttk.Separator(button_frame, orient="vertical", style="Aperture.TSeparator").pack(side="left", fill="y", padx=18)

        quick_action_frame = ttk.Frame(button_frame, style="Header.TFrame")
        quick_action_frame.pack(side="left")
        ttk.Label(quick_action_frame, text="Immediate Actions", style="AccentCaption.TLabel").pack(anchor="w", pady=(0, 8))

        quick_buttons = ttk.Frame(quick_action_frame, style="Header.TFrame")
        quick_buttons.pack()

        ttk.Button(
            quick_buttons,
            text="▶ Launch Test",
            style="GLaDOS.TButton",
            command=self.launch_selected_game,
        ).pack(side="left", padx=4)
        ttk.Button(
            quick_buttons,
            text="Open Store",
            style="Aperture.TButton",
            command=self.open_store_page,
        ).pack(side="left", padx=4)
        ttk.Separator(button_frame, orient="vertical", style="Aperture.TSeparator").pack(side="left", fill="y", padx=18)

        mgmt_frame = ttk.Frame(button_frame, style="Header.TFrame")
        mgmt_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(mgmt_frame, text="Test Subject Controls", style="AccentCaption.TLabel").pack(anchor="w", pady=(0, 8))

        mgmt_buttons = [
            ("Add", self.show_add_dialog),
            ("Remove", self.remove_selected_game),
            ("Purge", self.remove_all_games),
            ("Rate", self.rate_selected_game),
            ("Analysis", self.show_analysis),
            ("Achievements", self.show_achievements),
        ]

        control_row = ttk.Frame(mgmt_frame, style="Header.TFrame")
        control_row.pack(fill="x")

        for text, command in mgmt_buttons:
            ttk.Button(control_row, text=text, style="Aperture.TButton", command=command).pack(side="left", padx=3)

        ttk.Separator(button_frame, orient="vertical", style="Aperture.TSeparator").pack(side="left", fill="y", padx=18)

        system_frame = ttk.Frame(button_frame, style="Header.TFrame")
        system_frame.pack(side="left")
        ttk.Label(system_frame, text="Systems", style="AccentCaption.TLabel").pack(anchor="w", pady=(0, 8))

        system_buttons = ttk.Frame(system_frame, style="Header.TFrame")
        system_buttons.pack()

        ttk.Button(
            system_buttons,
            text="Preferences",
            style="Aperture.TButton",
            command=self.show_preferences,
        ).pack(side="left", padx=4)
        ttk.Button(
            system_buttons,
            text="System Options",
            style="Aperture.TButton",
            command=self.focus_system_options,
        ).pack(side="left", padx=4)

        ttk.Label(system_frame, textvariable=self.update_status_var, style="AccentCaption.TLabel").pack(anchor="w", pady=(8, 0))

    def create_left_panel(self, parent: ttk.PanedWindow) -> None:
        self.left_panel = ttk.Frame(parent, style="Panel.TFrame")

        list_header = ttk.Frame(self.left_panel, style="Panel.TFrame")
        list_header.pack(fill="x", padx=10, pady=10)

        ttk.Label(list_header, text="Test Subject Database", style="PanelTitle.TLabel").pack(side="left")

        self.game_count_label = ttk.Label(list_header, text="0 Subjects", style="PanelCaption.TLabel")
        self.game_count_label.pack(side="right")

        tree_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("ID", "Platform", "Name", "Plays", "Rating", "Last Played")
        self.game_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Aperture.Treeview",
        )

        column_widths = {"ID": 50, "Platform": 80, "Name": 300, "Plays": 60, "Rating": 80, "Last Played": 120}

        for col in columns:
            self.game_tree.heading(col, text=col)
            self.game_tree.column(col, width=column_widths.get(col, 100), minwidth=50)

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.game_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.game_tree.xview)
        self.game_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.game_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")

        self.game_tree.bind("<Double-1>", self.launch_selected_game)
        self.game_tree.bind("<Return>", self.launch_selected_game)

        status_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        status_frame.pack(fill="x", padx=10, pady=(5, 10))

        tips_label = ttk.Label(
            status_frame,
            text="Tip: Double-click a game to launch it | Press Enter for selected game",
            style="PanelCaption.TLabel",
            font=(ApertureTheme.FONT_FAMILY, 9, "italic"),
        )
        tips_label.pack(anchor="w", pady=5)

    def create_right_panel(self, parent: ttk.PanedWindow) -> None:
        self.right_panel = ttk.Frame(parent, style="Panel.TFrame")

        notebook = ttk.Notebook(self.right_panel, style="Aperture.TNotebook")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.sidebar_notebook = notebook

        operations_tab = ttk.Frame(notebook, style="Panel.TFrame")
        notebook.add(operations_tab, text="Control Feed")

        comment_header = ttk.Frame(operations_tab, style="Panel.TFrame")
        comment_header.pack(fill="x", padx=10, pady=10)

        ttk.Label(comment_header, text="AI Commentary System", style="PanelTitle.TLabel").pack()

        comment_frame = ttk.Frame(operations_tab, style="Panel.TFrame")
        comment_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.commentary_text = scrolledtext.ScrolledText(
            comment_frame,
            bg=ApertureTheme.SECONDARY_BG,
            fg=ApertureTheme.TEXT_PRIMARY,
            font=("Courier", 9),
            wrap="word",
            height=15,
            borderwidth=1,
            relief="flat",
            highlightthickness=0,
        )
        self.commentary_text.pack(fill="both", expand=True)
        self.commentary_text.configure(insertbackground=ApertureTheme.TEXT_PRIMARY)

        rec_header = ttk.Frame(operations_tab, style="Panel.TFrame")
        rec_header.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Label(rec_header, text="Acquisition Recommendations", style="PanelBody.TLabel").pack()

        rec_frame = ttk.Frame(operations_tab, style="Panel.TFrame")
        rec_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.rec_text = scrolledtext.ScrolledText(
            rec_frame,
            bg=ApertureTheme.SECONDARY_BG,
            fg=ApertureTheme.TEXT_SECONDARY,
            font=ApertureTheme.FONT_BASE,
            wrap="word",
            height=8,
            state="disabled",
            borderwidth=1,
            relief="flat",
            highlightthickness=0,
        )
        self.rec_text.pack(fill="both", expand=True)
        self.rec_text.configure(insertbackground=ApertureTheme.TEXT_PRIMARY)

        mini_games_tab = ttk.Frame(notebook, style="Panel.TFrame")
        notebook.add(mini_games_tab, text="Mini-Games Lab")
        self.mini_games_tab = mini_games_tab

        lab_header = ttk.Frame(mini_games_tab, style="Panel.TFrame")
        lab_header.pack(fill="x", padx=10, pady=10)

        ttk.Label(lab_header, text="Mini-Game Simulations", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            lab_header,
            text="Train with Aperture-approved simulations to unlock hidden achievements.",
            style="PanelCaption.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Label(lab_header, textvariable=self.mini_game_summary_var, style="PanelBody.TLabel").pack(anchor="w", pady=(8, 0))

        stats_container = ttk.Frame(mini_games_tab, style="Panel.TFrame")
        stats_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        stats_canvas = tk.Canvas(
            stats_container,
            bg=ApertureTheme.PANEL_BG,
            highlightthickness=0,
            relief="flat",
        )
        stats_scrollbar = ttk.Scrollbar(stats_container, orient="vertical", command=stats_canvas.yview)
        stats_canvas.configure(yscrollcommand=stats_scrollbar.set)

        stats_scrollable = ttk.Frame(stats_canvas, style="Panel.TFrame")

        def _sync_scrollregion(event: tk.Event) -> None:
            stats_canvas.configure(scrollregion=stats_canvas.bbox("all"))

        stats_scrollable.bind("<Configure>", _sync_scrollregion)
        stats_canvas.create_window((0, 0), window=stats_scrollable, anchor="nw")

        stats_canvas.pack(side="left", fill="both", expand=True)
        stats_scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event: tk.Event) -> None:
            if event.delta:
                stats_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                stats_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                stats_canvas.yview_scroll(1, "units")

        def _bind_mousewheel(_: tk.Event) -> None:
            stats_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            stats_canvas.bind_all("<Button-4>", _on_mousewheel)
            stats_canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(_: tk.Event) -> None:
            stats_canvas.unbind_all("<MouseWheel>")
            stats_canvas.unbind_all("<Button-4>")
            stats_canvas.unbind_all("<Button-5>")

        stats_scrollable.bind("<Enter>", _bind_mousewheel)
        stats_scrollable.bind("<Leave>", _unbind_mousewheel)

        self.mini_game_stats_vars.clear()
        default_fields = [
            "sessions",
            "best_score",
            "total_lines",
            "highest_level",
            "total_time",
            "last_played",
        ]

        for config in self.mini_game_configs:
            definition = self.achievement_manager.get_mini_game_definition(config["key"])
            card = ttk.Frame(stats_scrollable, style="Panel.TFrame")
            card.pack(fill="x", padx=0, pady=(0, 12))

            ttk.Label(card, text=definition.get("title", config["key"]), style="PanelBody.TLabel").pack(anchor="w")
            description = definition.get("description")
            if description:
                ttk.Label(
                    card,
                    text=description,
                    style="PanelCaption.TLabel",
                    wraplength=520,
                ).pack(anchor="w", pady=(2, 6))

            stats_vars: Dict[str, tk.StringVar] = {}
            stat_fields = definition.get("stat_fields", default_fields)
            stats_labels = definition.get("stats_labels", {})
            for field in stat_fields:
                label_text = stats_labels.get(field, field.replace("_", " ").title())
                var = tk.StringVar(value=f"{label_text}: …")
                stats_vars[field] = var
                ttk.Label(card, textvariable=var, style="MiniStats.TLabel").pack(anchor="w")

            button_row = ttk.Frame(card, style="Panel.TFrame")
            button_row.pack(fill="x", pady=(8, 0))

            ttk.Button(
                button_row,
                text=definition.get("launch_label", "Launch Simulation"),
                style="GLaDOS.TButton",
                command=config["launcher"],
                width=26,
            ).pack(side="left")

            ttk.Button(
                button_row,
                text="View Achievements",
                style="Aperture.TButton",
                command=lambda key=config["key"]: self.show_mini_game_details(key),
                width=22,
            ).pack(side="left", padx=(10, 0))

            self.mini_game_stats_vars[config["key"]] = stats_vars

        action_frame = ttk.Frame(mini_games_tab, style="Panel.TFrame")
        action_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(
            action_frame,
            text="Mini-Game Overview",
            style="Aperture.TButton",
            command=self.show_mini_games,
            width=22,
        ).pack(side="left")

        ttk.Button(
            action_frame,
            text="Back to Control Feed",
            style="Aperture.TButton",
            command=lambda: self.sidebar_notebook.select(operations_tab),
            width=22,
        ).pack(side="left", padx=(10, 0))

        system_tab = ttk.Frame(notebook, style="Panel.TFrame")
        notebook.add(system_tab, text="System Options")
        self.system_tab = system_tab

        system_header = ttk.Frame(system_tab, style="Panel.TFrame")
        system_header.pack(fill="x", padx=10, pady=10)

        ttk.Label(system_header, text="Launcher Maintenance", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            system_header,
            text="Manage diagnostics, updates, and Aperture configuration protocols.",
            style="PanelCaption.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        appearance_panel = ttk.Frame(system_tab, style="Panel.TFrame")
        appearance_panel.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(appearance_panel, text="Appearance", style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(
            appearance_panel,
            text="Toggle between Aperture dark ops and daylight testing interfaces.",
            style="PanelCaption.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        appearance_controls = ttk.Frame(appearance_panel, style="Panel.TFrame")
        appearance_controls.pack(fill="x", pady=(10, 0))

        ttk.Radiobutton(
            appearance_controls,
            text="Dark Mode",
            value="dark",
            variable=self.theme_mode_var,
            command=lambda: self.set_theme_mode("dark"),
            style="Aperture.TRadiobutton",
        ).pack(side="left", padx=(0, 16))

        ttk.Radiobutton(
            appearance_controls,
            text="Light Mode",
            value="light",
            variable=self.theme_mode_var,
            command=lambda: self.set_theme_mode("light"),
            style="Aperture.TRadiobutton",
        ).pack(side="left")

        update_panel = ttk.Frame(system_tab, style="Panel.TFrame")
        update_panel.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(update_panel, text="Software Updates", style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(
            update_panel,
            text="Initiate manual update checks or apply approved builds when available.",
            style="PanelCaption.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        update_controls = ttk.Frame(update_panel, style="Panel.TFrame")
        update_controls.pack(fill="x", pady=(10, 0))

        self.check_updates_button = ttk.Button(
            update_controls,
            text="Check for Updates",
            style="Aperture.TButton",
            command=self.check_for_updates,
        )
        self.check_updates_button.pack(side="left")

        self.apply_update_button = ttk.Button(
            update_controls,
            text="Apply Update",
            style="GLaDOS.TButton",
            command=self.download_and_apply_update,
        )
        self.apply_update_button.state(["disabled"])
        self.apply_update_button.pack(side="left", padx=(10, 0))

        ttk.Label(update_panel, textvariable=self.update_status_var, style="PanelCaption.TLabel").pack(
            anchor="w", pady=(10, 0)
        )

    def initialize_features(self) -> None:
        self.commentary_mode.set(self.user_preferences.get("commentary_level", "balanced"))
        self.update_recommendations()
        self.update_mini_game_panel()

        if not REQUESTS_AVAILABLE:
            self.update_status_var.set("Status: Updates unavailable (missing requests module).")
            self._set_apply_update_enabled(False)
        elif not self.update_manager.is_supported():
            self.update_status_var.set("Status: Updates unavailable in this build.")
            self._set_apply_update_enabled(False)
        else:
            self.update_status_var.set("Status: Ready for diagnostics.")
            self._set_apply_update_enabled(False)

        self._refresh_update_controls()

        self.add_commentary("GLaDOS", "Systems online. Ready for testing protocols.", "success")
        if not self.game_manager.get_games():
            self.add_commentary("Wheatley", "No test subjects detected! Try running a scan to find games.")

        self.schedule_auto_update_check()

    def schedule_auto_update_check(self) -> None:
        if not REQUESTS_AVAILABLE:
            return
        if not self.update_manager.is_supported():
            return

        last_check = self.user_preferences.get("last_update_check", 0)
        now = time.time()
        if now - last_check < 12 * 60 * 60:
            return

        self.user_preferences["last_update_check"] = now
        self.save_preferences()

        self.update_status_var.set("Status: Performing routine update check...")

        def _check() -> None:
            result = self.update_manager.check_for_updates()
            self.root.after(0, lambda: self._handle_update_check_result(result, background=True))

        threading.Thread(target=_check, daemon=True).start()

    def refresh_game_list(self) -> None:
        for item in self.game_tree.get_children():
            self.game_tree.delete(item)

        games = self.game_manager.get_games()

        if self.user_preferences.get("auto_sort", True):
            sorted_games = self.game_manager.get_smart_sorted_games()
        else:
            sorted_games = sorted(games.items(), key=lambda item: item[1]["name"].lower())

        for game_id, game_info in sorted_games:
            platform_name = game_info["platform"].title()
            name = game_info["name"]
            plays = game_info.get("play_count", 0)
            rating = "★" * game_info.get("user_rating", 0) if game_info.get("user_rating", 0) > 0 else "-"
            last_played = game_info.get("last_played", "Never")[:10] if game_info.get("last_played") else "Never"

            self.game_tree.insert("", "end", values=(game_id, platform_name, name, plays, rating, last_played))

        self.game_count_label.config(text=f"{len(games)} Subjects")

    def launch_selected_game(self, event: Optional[Any] = None) -> None:
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a test subject to launch.")
                return

            item = self.game_tree.item(selection[0])
            values = item["values"]

            if len(values) >= 3:
                game_id = values[0]
                platform_name = values[1].lower()
                game_name = values[2]

                games = self.game_manager.get_games()
                if str(game_id) in games:
                    game_info = games[str(game_id)]
                    launch_url = game_info.get("protocol_url", game_info.get("store_url", ""))

                    if self.launcher.launch_game(launch_url, platform_name):
                        self.game_manager.update_play_count(str(game_id))
                        self.refresh_game_list()
                        self.add_commentary("GLaDOS", f"Test subject {game_name} launched successfully.", "success")
                    else:
                        self.add_commentary("GLaDOS", f"Failed to launch {game_name}. Platform may not be running.", "error")

        except Exception as exc:
            self.add_commentary("System", f"Launch error: {exc}", "error")

    def open_store_page(self) -> None:
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a test subject.")
                return

            item = self.game_tree.item(selection[0])
            values = item["values"]

            if len(values) >= 3:
                game_id = values[0]
                games = self.game_manager.get_games()

                if str(game_id) in games:
                    store_url = games[str(game_id)].get("store_url", "")
                    if store_url:
                        webbrowser.open(store_url)
                        self.add_commentary("System", f"Store page opened for {values[2]}.")
                    else:
                        messagebox.showinfo("No Store Page", "No store page available for this game.")

        except Exception as exc:
            messagebox.showerror("Error", f"Failed to open store page: {exc}")

    def run_smart_scan(self) -> None:
        self.add_commentary("Wheatley", "Initiating full spectrum scan. This may take a moment...")

        try:
            scan_buttons = self.root.winfo_children()
            for widget in scan_buttons:
                if hasattr(widget, "winfo_children"):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and "FULL SCAN" in str(child.cget("text")):
                            child.config(state="disabled")
        except Exception:
            pass

        def scan_thread() -> None:
            try:
                results = self.scanner.scan_all_platforms()
                self.last_scan_results = results

                total_found = sum(len(games) for games in results.values())

                added_count = 0
                existing_games = self.game_manager.get_games()

                for platform_name, games in results.items():
                    self.root.after(0, lambda p=platform_name, c=len(games): self.add_commentary("System", f"{p.title()} scan: {c} games found"))

                    for game in games:
                        game_exists = False
                        for existing_game in existing_games.values():
                            if (
                                existing_game.get("name", "").lower() == game["name"].lower()
                                and existing_game.get("platform", "") == platform_name
                            ):
                                game_exists = True
                                break

                        if not game_exists:
                            try:
                                self.game_manager.add_game(
                                    game["name"],
                                    platform_name,
                                    game["game_id"],
                                    game.get("store_url", ""),
                                    game,
                                )
                                added_count += 1
                            except Exception as exc:
                                self.root.after(0, lambda err=str(exc): self.add_commentary("System", f"Error adding game: {err}", "error"))

                self.root.after(0, lambda: self.scan_complete(total_found, added_count))

            except Exception as exc:
                error_msg = f"Scan error: {exc}"
                self.root.after(0, lambda: self.add_commentary("System", error_msg, "error"))
                self.root.after(0, self.re_enable_scan_button)

        threading.Thread(target=scan_thread, daemon=True).start()

    def re_enable_scan_button(self) -> None:
        try:
            scan_buttons = self.root.winfo_children()
            for widget in scan_buttons:
                if hasattr(widget, "winfo_children"):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button) and "FULL SCAN" in str(child.cget("text")):
                            child.config(state="normal")
        except Exception:
            pass

    def scan_complete(self, total_found: int, added_count: int) -> None:
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

            self.re_enable_scan_button()
        except Exception as exc:
            self.add_commentary("System", f"Error completing scan: {exc}", "error")

    def run_platform_scan(self, platform_name: str) -> None:
        self.add_commentary("System", f"Scanning {platform_name.title()} network...")

        def scan_thread() -> None:
            try:
                if platform.system() == "Windows":
                    if platform_name == "steam":
                        games = self.scanner.scan_steam_windows()
                    elif platform_name == "epic":
                        games = self.scanner.scan_epic_windows()
                    elif platform_name == "ubisoft":
                        games = self.scanner.scan_ubisoft_windows()
                    elif platform_name == "gog":
                        games = self.scanner.scan_gog_windows()
                    else:
                        games = []
                else:
                    games = []

                games = self.scanner.apply_smart_filtering(games, platform_name)

                added_count = 0
                existing_games = self.game_manager.get_games()
                for game in games:
                    if not any(
                        g["name"] == game["name"] and g["platform"] == platform_name for g in existing_games.values()
                    ):
                        self.game_manager.add_game(
                            game["name"],
                            platform_name,
                            game["game_id"],
                            game.get("store_url", ""),
                            game,
                        )
                        added_count += 1

                self.root.after(0, self.refresh_game_list)
                self.root.after(0, self.update_recommendations)
                self.root.after(0, lambda: self.add_commentary("System", f"Platform scan complete. {added_count} new subjects added."))

            except Exception as exc:
                self.root.after(0, lambda: self.add_commentary("System", f"Platform scan error: {exc}", "error"))

        threading.Thread(target=scan_thread, daemon=True).start()

    def show_add_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Test Subject")
        dialog.geometry("400x400")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)

        ttk.Label(dialog, text="Subject Name:", style="Aperture.TLabel").pack(pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Platform:", style="Aperture.TLabel").pack(pady=5)
        platform_var = tk.StringVar(value="steam")
        platform_menu = ttk.Combobox(dialog, textvariable=platform_var, values=["steam", "epic", "ubisoft", "gog", "other"])
        platform_menu.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Game ID:", style="Aperture.TLabel").pack(pady=5)
        id_entry = ttk.Entry(dialog)
        id_entry.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Store URL:", style="Aperture.TLabel").pack(pady=5)
        url_entry = ttk.Entry(dialog)
        url_entry.pack(fill="x", padx=20)

        def add_game() -> None:
            name = name_entry.get().strip()
            platform_name = platform_var.get().strip().lower()
            game_id = id_entry.get().strip()
            store_url = url_entry.get().strip()

            if not name or not platform_name:
                messagebox.showwarning("Invalid Input", "Please enter a name and platform.")
                return

            if not game_id:
                game_id = name.lower().replace(" ", "-")

            new_id = self.game_manager.add_game(name, platform_name, game_id, store_url)
            self.refresh_game_list()
            self.update_recommendations()
            self.add_commentary("GLaDOS", f"New test subject {name} registered with ID {new_id}.", "success")
            dialog.destroy()

        ttk.Button(dialog, text="ADD", style="GLaDOS.TButton", command=add_game).pack(pady=10)
        ttk.Button(dialog, text="CANCEL", style="Aperture.TButton", command=dialog.destroy).pack(pady=5)

    def remove_selected_game(self) -> None:
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a subject to terminate.")
                return

            item = self.game_tree.item(selection[0])
            values = item["values"]

            if len(values) >= 3:
                game_id = str(values[0])
                game_name = values[2]

                if messagebox.askyesno("Confirm Termination", f"Terminate test subject {game_name}? This action cannot be undone."):
                    if self.game_manager.remove_game(game_id):
                        self.refresh_game_list()
                        self.update_recommendations()
                        self.add_commentary("System", f"Test subject {game_name} removed from the database.", "warning")
                    else:
                        messagebox.showerror("Error", "Subject termination failed.")

        except Exception as exc:
            messagebox.showerror("Error", f"Termination error: {exc}")

    def remove_all_games(self) -> None:
        try:
            games = self.game_manager.get_games()
            if not games:
                messagebox.showinfo("Remove All Subjects", "There are no test subjects to remove.")
                return

            if not messagebox.askyesno(
                "Remove All Subjects",
                "This will permanently purge every test subject from the database.\n\nProceed?",
            ):
                return

            if self.game_manager.remove_all_games():
                self.refresh_game_list()
                self.update_recommendations()
                self.add_commentary("System", "All test subjects have been purged from the database.", "warning")
            else:
                messagebox.showerror("Remove All Subjects", "Failed to purge test subjects.")
        except Exception as exc:
            messagebox.showerror("Remove All Subjects", f"Unexpected error: {exc}")

    def rate_selected_game(self) -> None:
        try:
            selection = self.game_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a subject for evaluation.")
                return

            item = self.game_tree.item(selection[0])
            values = item["values"]

            if len(values) >= 3:
                game_id = str(values[0])
                game_name = values[2]

                rating = simpledialog.askinteger(
                    "Subject Evaluation",
                    f"Rate test subject {game_name} (1-5 stars):",
                    minvalue=1,
                    maxvalue=5,
                )

                if rating:
                    games = self.game_manager.get_games()
                    if game_id in games:
                        games[game_id]["user_rating"] = rating
                        self.game_manager.save_game_data()
                        self.refresh_game_list()
                        self.add_commentary("GLaDOS", f"Subject {game_name} rated {rating} stars. Your evaluation has been recorded.")

        except Exception as exc:
            messagebox.showerror("Error", f"Evaluation error: {exc}")

    def show_achievements(self) -> None:
        try:
            selection = self.game_tree.selection()
            if not selection:
                self.show_achievement_summary()
                return

            item = self.game_tree.item(selection[0])
            values = item["values"]

            if len(values) >= 3:
                game_id = str(values[0])
                game_name = values[2]

                games = self.game_manager.get_games()
                if game_id in games:
                    game_info = games[game_id]
                    achievements = self.achievement_manager.get_game_achievements(
                        game_info.get("game_id", ""),
                        game_info.get("platform", ""),
                        game_info.get("name", ""),
                    )

                    self.show_game_achievements(game_name, achievements)

        except Exception as exc:
            messagebox.showerror("Error", f"Achievement analysis error: {exc}")

    def show_mini_games(self) -> None:
        self._open_mini_game_dialog()

    def show_mini_game_details(self, game_key: str) -> None:
        self._open_mini_game_dialog(selected_key=game_key)

    def _open_mini_game_dialog(self, selected_key: Optional[str] = None) -> None:
        self.focus_mini_games_lab()
        dialog = tk.Toplevel(self.root)
        dialog.title("Aperture Mini-Games")
        dialog.geometry("680x560")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)

        header_frame = ttk.Frame(dialog, style="Header.TFrame")
        header_frame.pack(fill="x", padx=20, pady=20)

        ttk.Label(header_frame, text="Aperture Mini-Games", style="Hero.TLabel").pack()
        ttk.Label(
            header_frame,
            text="Complete experimental simulations to unlock custom achievements.",
            style="AccentCaption.TLabel",
        ).pack(pady=(6, 0))

        content_frame = ttk.Frame(dialog, style="Panel.TFrame")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        notebook = ttk.Notebook(content_frame, style="Aperture.TNotebook")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        tab_lookup: Dict[str, ttk.Frame] = {}

        for config in self.mini_game_configs:
            key = config["key"]
            definition = self.achievement_manager.get_mini_game_definition(key)
            stats = self.achievement_manager.get_mini_game_stats(key)
            achievements = self.achievement_manager.get_mini_game_achievements(key)

            tab = ttk.Frame(notebook, style="Panel.TFrame")
            notebook.add(tab, text=definition.get("short_title", definition.get("title", key)))
            tab_lookup[key] = tab

            ttk.Label(tab, text=definition.get("title", key), style="PanelTitle.TLabel").pack(anchor="w", padx=15, pady=(12, 4))
            description = definition.get("description")
            if description:
                ttk.Label(
                    tab,
                    text=description,
                    style="PanelCaption.TLabel",
                    wraplength=560,
                ).pack(anchor="w", padx=15)

            stat_fields = definition.get("stat_fields", []) or [
                "sessions",
                "best_score",
                "total_lines",
                "highest_level",
                "total_time",
                "last_played",
            ]
            stats_labels = definition.get("stats_labels", {})

            stats_frame = ttk.Frame(tab, style="Panel.TFrame")
            stats_frame.pack(fill="x", padx=15, pady=(12, 10))
            ttk.Label(stats_frame, text="Simulation Stats", style="PanelBody.TLabel").pack(anchor="w")

            for field in stat_fields:
                label = stats_labels.get(field, field.replace("_", " ").title())
                value = self._format_mini_game_value(field, stats)
                ttk.Label(stats_frame, text=f"{label}: {value}", style="MiniStats.TLabel").pack(anchor="w", pady=(3, 0))

            ach_frame = ttk.Frame(tab, style="Panel.TFrame")
            ach_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            ttk.Label(ach_frame, text="Achievement Protocols", style="PanelBody.TLabel").pack(anchor="w")

            if achievements:
                for achievement in achievements:
                    status = "✔" if achievement.get("earned") else "○"
                    text = f"{status} {achievement['name']}"
                    ttk.Label(ach_frame, text=text, style="PanelBody.TLabel").pack(anchor="w", pady=(6, 0))
                    ttk.Label(
                        ach_frame,
                        text=f"    {achievement['description']}",
                        style="PanelCaption.TLabel" if achievement.get("earned") else "PanelBody.TLabel",
                    ).pack(anchor="w")
            else:
                ttk.Label(
                    ach_frame,
                    text="No experimental achievements defined yet.",
                    style="PanelBody.TLabel",
                ).pack(anchor="w", pady=10)

            button_row = ttk.Frame(tab, style="Panel.TFrame")
            button_row.pack(fill="x", padx=15, pady=(10, 10))

            def launch_game(launcher=config["launcher"], dlg=dialog) -> None:
                if dlg.winfo_exists():
                    dlg.destroy()
                launcher()

            ttk.Button(
                button_row,
                text=definition.get("launch_label", "Launch Simulation"),
                style="GLaDOS.TButton",
                command=launch_game,
                width=28,
            ).pack(side="left", padx=(0, 10))

            ttk.Button(
                button_row,
                text="Close",
                style="Aperture.TButton",
                command=dialog.destroy,
                width=12,
            ).pack(side="left")

        if selected_key and selected_key in tab_lookup:
            notebook.select(tab_lookup[selected_key])


    def show_achievement_summary(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Achievement Analysis")
        dialog.geometry("600x500")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)

        header_frame = ttk.Frame(dialog, style="Header.TFrame")
        header_frame.pack(fill="x", padx=20, pady=20)

        ttk.Label(header_frame, text="Subject Achievement Analysis", style="Hero.TLabel").pack()

        content_frame = ttk.Frame(dialog, style="Panel.TFrame")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        info_text = scrolledtext.ScrolledText(
            content_frame,
            bg=ApertureTheme.SECONDARY_BG,
            fg=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BASE,
            wrap="word",
            state="normal",
            borderwidth=1,
            relief="flat",
            highlightthickness=0,
        )
        info_text.pack(fill="both", expand=True)
        info_text.configure(insertbackground=ApertureTheme.TEXT_PRIMARY)

        games = self.game_manager.get_games()
        summary = self.achievement_manager.get_achievement_summary(games)

        content = f"""APERTURE SCIENCE ACHIEVEMENT REPORT\n{'='*45}\n\nOVERALL STATISTICS:\nTest Subjects with Achievements: {summary['games_with_achievements']}\nTotal Achievement Opportunities: {summary['total_achievements']}\nAchievements Unlocked: {summary['total_unlocked']}\nCompletion Efficiency: {summary['completion_percentage']:.1f}%\n\nDETAILED SUBJECT ANALYSIS:\n{'='*45}\n\n"""

        for game_id, game_info in games.items():
            achievements = self.achievement_manager.get_game_achievements(
                game_info.get("game_id", ""),
                game_info.get("platform", ""),
                game_info.get("name", ""),
            )

            if achievements.get("total", 0) > 0:
                content += f"Subject: {game_info['name']} ({game_info['platform'].title()})\n"
                content += (
                    f"  Achievement Status: {achievements['unlocked']}/{achievements['total']} ({achievements['percentage']:.1f}%)\n"
                )
                content += (
                    "  Performance Rating: "
                    + (
                        "Excellent"
                        if achievements["percentage"] >= 80
                        else "Satisfactory"
                        if achievements["percentage"] >= 50
                        else "Needs Improvement"
                    )
                    + "\n\n"
                )

        content += f"\nReport Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "Aperture Science - We do what we must because we can."

        info_text.insert("1.0", content)
        info_text.config(state="disabled")

        ttk.Button(dialog, text="DISMISS", style="Aperture.TButton", command=dialog.destroy).pack(pady=15)

    def show_game_achievements(self, game_name: str, achievements: Dict[str, Any]) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Achievement Analysis - {game_name}")
        dialog.geometry("700x600")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)

        header_frame = ttk.Frame(dialog, style="Header.TFrame")
        header_frame.pack(fill="x", padx=20, pady=20)

        ttk.Label(
            header_frame,
            text=f"Subject Achievements - {game_name}",
            style="Hero.TLabel",
        ).pack()

        progress_frame = ttk.Frame(dialog, style="Panel.TFrame")
        progress_frame.pack(fill="x", padx=20, pady=(0, 10))

        progress_text = f"Progress: {achievements['unlocked']}/{achievements['total']} ({achievements['percentage']:.1f}%)"
        ttk.Label(progress_frame, text=progress_text, style="PanelBody.TLabel").pack(pady=10)

        list_frame = ttk.Frame(dialog, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ach_tree = ttk.Treeview(
            list_frame,
            columns=("Status", "Name", "Description"),
            show="headings",
            height=18,
            style="Aperture.Treeview",
        )
        ach_tree.heading("Status", text="Status")
        ach_tree.heading("Name", text="Achievement")
        ach_tree.heading("Description", text="Description")

        ach_tree.column("Status", width=80)
        ach_tree.column("Name", width=200)
        ach_tree.column("Description", width=350)

        for achievement in achievements.get("achievements", []):
            status = "✓ UNLOCKED" if achievement.get("unlocked") else "○ LOCKED"
            ach_tree.insert(
                "",
                "end",
                values=(
                    status,
                    achievement.get("name", "Unknown Achievement"),
                    achievement.get("description", "No description available"),
                ),
            )

        scrollbar_ach = ttk.Scrollbar(list_frame, orient="vertical", command=ach_tree.yview)
        ach_tree.configure(yscrollcommand=scrollbar_ach.set)

        ach_tree.pack(side="left", fill="both", expand=True)
        scrollbar_ach.pack(side="right", fill="y")

        ttk.Button(dialog, text="DISMISS", style="Aperture.TButton", command=dialog.destroy).pack(pady=15)

    def show_analysis(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Test Subject Analysis")
        dialog.geometry("700x600")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)

        header_frame = ttk.Frame(dialog, style="Header.TFrame")
        header_frame.pack(fill="x", padx=20, pady=20)

        ttk.Label(header_frame, text="Aperture Behavioral Analysis", style="Hero.TLabel").pack()

        analysis_frame = ttk.Frame(dialog, style="Panel.TFrame")
        analysis_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        analysis_text = scrolledtext.ScrolledText(
            analysis_frame,
            bg=ApertureTheme.SECONDARY_BG,
            fg=ApertureTheme.TEXT_PRIMARY,
            font=ApertureTheme.FONT_BASE,
            wrap="word",
            state="normal",
            borderwidth=1,
            relief="flat",
            highlightthickness=0,
        )
        analysis_text.pack(fill="both", expand=True)
        analysis_text.configure(insertbackground=ApertureTheme.TEXT_PRIMARY)

        games = self.game_manager.get_games()
        if not games:
            content = "No test subjects available for analysis. Please acquire subjects through scanning protocols."
        else:
            total_games = len(games)
            total_plays = sum(game.get("play_count", 0) for game in games.values())
            avg_plays = total_plays / total_games if total_games > 0 else 0

            platform_stats: Dict[str, int] = {}
            for game in games.values():
                platform_name = game["platform"]
                platform_stats[platform_name] = platform_stats.get(platform_name, 0) + 1

            most_played = max(games.values(), key=lambda game: game.get("play_count", 0))

            content = (
                "APERTURE SCIENCE BEHAVIORAL ANALYSIS REPORT\n"
                + "=" * 50
                + "\n\n"
                + f"Total Test Subjects: {total_games}\n"
                + f"Aggregate Play Sessions: {total_plays}\n"
                + f"Average Play Sessions per Subject: {avg_plays:.1f}\n\n"
                + "Platform Distribution:\n"
            )
            for platform_name, count in platform_stats.items():
                content += f"  - {platform_name.title()}: {count} subjects\n"

            content += (
                f"\nMost Utilized Subject: {most_played['name']} ({most_played['platform'].title()})\n"
                f"Play Sessions Recorded: {most_played.get('play_count', 0)}\n"
                "\nRecommendations:\n"
            )
            for rec in self.game_manager.get_recommendations():
                content += f"  - {rec}\n"

        analysis_text.insert("1.0", content)
        analysis_text.config(state="disabled")

        ttk.Button(dialog, text="DISMISS", style="Aperture.TButton", command=dialog.destroy).pack(pady=15)

    def show_preferences(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("System Preferences")
        dialog.geometry("500x450")
        dialog.configure(bg=ApertureTheme.PRIMARY_BG)
        dialog.transient(self.root)

        pref_frame = ttk.Frame(dialog, style="Panel.TFrame")
        pref_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        smart_rec_var = tk.BooleanVar(value=self.user_preferences.get("smart_recommendations", True))
        ttk.Checkbutton(pref_frame, text="Enable Smart Recommendations", variable=smart_rec_var, style="Aperture.TCheckbutton").pack(anchor="w", pady=10)

        auto_sort_var = tk.BooleanVar(value=self.user_preferences.get("auto_sort", True))
        ttk.Checkbutton(pref_frame, text="Auto-sort by Activity", variable=auto_sort_var, style="Aperture.TCheckbutton").pack(anchor="w", pady=5)

        ttk.Label(pref_frame, text="AI Commentary Level:", style="Aperture.TLabel").pack(anchor="w", pady=(20, 10))

        commentary_var = tk.StringVar(value=self.user_preferences.get("commentary_level", "balanced"))
        commentary_frame = ttk.Frame(pref_frame, style="Panel.TFrame")
        commentary_frame.pack(fill="x", pady=(0, 20))

        modes = [
            ("Silent Operation", "minimal"),
            ("GLaDOS Primary", "glados"),
            ("Balanced Mode", "balanced"),
            ("Wheatley Primary", "wheatley"),
        ]

        for text, value in modes:
            ttk.Radiobutton(commentary_frame, text=text, variable=commentary_var, value=value, style="Aperture.TRadiobutton").pack(anchor="w", pady=2)

        button_frame = ttk.Frame(dialog, style="Panel.TFrame")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def save_preferences() -> None:
            self.user_preferences.update(
                {
                    "smart_recommendations": smart_rec_var.get(),
                    "auto_sort": auto_sort_var.get(),
                    "commentary_level": commentary_var.get(),
                }
            )
            self.commentary_mode.set(commentary_var.get())
            self.save_preferences()
            self.add_commentary("System", "Configuration updated successfully.", "success")
            dialog.destroy()

        def reset_preferences() -> None:
            if messagebox.askyesno("Reset Configuration", "Reset all preferences to default values?"):
                smart_rec_var.set(True)
                auto_sort_var.set(True)
                commentary_var.set("balanced")

        ttk.Button(button_frame, text="SAVE CONFIG", style="GLaDOS.TButton", command=save_preferences).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="RESET", style="Aperture.TButton", command=reset_preferences).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="CANCEL", style="Aperture.TButton", command=dialog.destroy).pack(side="left")

    def add_commentary(self, speaker: str, message: str, message_type: str = "info") -> None:
        try:
            self.commentary_text.config(state="normal")
            timestamp = time.strftime("%H:%M:%S")

            colors = {
                "GLaDOS": ApertureTheme.GLADOS_ORANGE,
                "Wheatley": ApertureTheme.WHEATLEY_BLUE,
                "System": ApertureTheme.TEXT_ACCENT,
                "success": ApertureTheme.SUCCESS_GREEN,
                "error": ApertureTheme.ERROR_RED,
                "warning": ApertureTheme.WARNING_YELLOW,
            }

            color = colors.get(message_type, colors.get(speaker, ApertureTheme.TEXT_PRIMARY))

            self.commentary_text.insert("end", f"[{timestamp}] {speaker}: {message}\n\n")
            self.commentary_text.see("end")
            self.commentary_text.config(state="disabled")

            lines = int(self.commentary_text.index("end-1c").split(".")[0])
            if lines > 100:
                self.commentary_text.config(state="normal")
                self.commentary_text.delete("1.0", "10.0")
                self.commentary_text.config(state="disabled")
        except Exception:
            pass

    def update_recommendations(self) -> None:
        try:
            self.rec_text.config(state="normal")
            self.rec_text.delete("1.0", "end")

            recommendations = self.game_manager.get_recommendations()
            for recommendation in recommendations:
                self.rec_text.insert("end", f"• {recommendation}\n")

            self.rec_text.config(state="disabled")
        except Exception:
            pass

    def update_mini_game_panel(self) -> None:
        try:
            summary_parts = []

            for config in self.mini_game_configs:
                key = config["key"]
                stats = self.achievement_manager.get_mini_game_stats(key)
                definition = self.achievement_manager.get_mini_game_definition(key)
                stats_vars = self.mini_game_stats_vars.get(key, {})
                labels = definition.get("stats_labels", {})

                for field, var in stats_vars.items():
                    label = labels.get(field, field.replace("_", " ").title())
                    value = self._format_mini_game_value(field, stats)
                    var.set(f"{label}: {value}")

                summary_parts.append(self.achievement_manager.format_mini_game_summary(key, stats))

            summary_var = getattr(self, "mini_game_summary_var", None)
            if summary_var is not None:
                summary_text = " | ".join(summary_parts).strip()
                if summary_text:
                    summary_var.set(summary_text)
                else:
                    summary_var.set("No simulation data recorded. Launch a training module to begin telemetry.")
        except Exception:
            pass

    def _format_mini_game_value(self, field: str, stats: Dict[str, Any]) -> str:
        if field == "total_time":
            total_minutes = stats.get("total_time", 0.0) / 60.0
            return f"{total_minutes:.1f} min"
        if field == "last_played":
            timestamp = stats.get("last_played")
            if timestamp:
                try:
                    return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
                except Exception:
                    return "Recently"
            return "Never"
        if field in {"sessions", "best_score", "total_lines", "highest_level", "best_armor", "last_lines", "last_level", "last_score", "last_armor"}:
            return str(stats.get(field, 0))
        value = stats.get(field)
        if isinstance(value, float):
            return f"{value:.1f}"
        return str(value) if value is not None else "…"

    def focus_mini_games_lab(self) -> None:
        try:
            if self.sidebar_notebook is not None and self.mini_games_tab is not None:
                self.sidebar_notebook.select(self.mini_games_tab)
        except Exception:
            pass

    def focus_system_options(self) -> None:
        try:
            if self.sidebar_notebook is not None and self.system_tab is not None:
                self.sidebar_notebook.select(self.system_tab)
        except Exception:
            pass

    def show_tetris(self) -> None:
        if hasattr(self, "tetris") and isinstance(self.tetris, TrainTetrisGame) and self.tetris.is_open:
            self.tetris.focus()
            return

        self.tetris = TrainTetrisGame(
            self.root,
            on_close=self._handle_tetris_closed,
            achievement_manager=self.achievement_manager,
        )

    def _handle_tetris_closed(self) -> None:
        self.tetris = None
        self.update_mini_game_panel()

    def show_space_invaders(self) -> None:
        if (
            hasattr(self, "space_invaders")
            and isinstance(self.space_invaders, RapidFireSpaceInvaders)
            and self.space_invaders.is_open
        ):
            self.space_invaders.focus()
            return

        self.space_invaders = RapidFireSpaceInvaders(
            self.root,
            on_close=self._handle_space_invaders_closed,
            achievement_manager=self.achievement_manager,
        )

    def _handle_space_invaders_closed(self) -> None:
        self.space_invaders = None
        self.update_mini_game_panel()

    def show_doom_training(self) -> None:
        if (
            hasattr(self, "doom_training")
            and isinstance(self.doom_training, Doom2016MiniGame)
            and self.doom_training.is_open
        ):
            self.doom_training.focus()
            return

        self.doom_training = Doom2016MiniGame(
            self.root,
            on_close=self._handle_doom_closed,
            achievement_manager=self.achievement_manager,
        )

    def _handle_doom_closed(self) -> None:
        self.doom_training = None
        self.update_mini_game_panel()

    def show_doom_classic_episode_one(self) -> None:
        if (
            hasattr(self, "doom_episode_one")
            and isinstance(self.doom_episode_one, DoomClassicEpisodeIMiniGame)
            and self.doom_episode_one.is_open
        ):
            self.doom_episode_one.focus()
            return

        self.doom_episode_one = DoomClassicEpisodeIMiniGame(
            self.root,
            on_close=self._handle_doom_episode_one_closed,
            achievement_manager=self.achievement_manager,
        )

    def _handle_doom_episode_one_closed(self) -> None:
        self.doom_episode_one = None
        self.update_mini_game_panel()

    def show_doom_classic_episode_two(self) -> None:
        if (
            hasattr(self, "doom_episode_two")
            and isinstance(self.doom_episode_two, DoomClassicEpisodeIIMiniGame)
            and self.doom_episode_two.is_open
        ):
            self.doom_episode_two.focus()
            return

        self.doom_episode_two = DoomClassicEpisodeIIMiniGame(
            self.root,
            on_close=self._handle_doom_episode_two_closed,
            achievement_manager=self.achievement_manager,
        )

    def _handle_doom_episode_two_closed(self) -> None:
        self.doom_episode_two = None
        self.update_mini_game_panel()

    def check_for_updates(self) -> None:
        if self.update_check_in_progress:
            self.update_status_var.set("Status: Update check already running.")
            messagebox.showinfo("Update Check", "An update check is already in progress.")
            return
        if not REQUESTS_AVAILABLE:
            self.update_status_var.set("Status: Updates unavailable (missing requests module).")
            messagebox.showerror("Update Check", "Requests package unavailable; install 'requests' to enable updates.")
            return
        if not self.update_manager.is_supported():
            self.update_status_var.set("Status: Updates unavailable in this build.")
            messagebox.showinfo("Update Check", "Auto-update is available only when running from source builds.")
            return

        self.update_check_in_progress = True
        self.add_commentary("System", "Checking for updates...")
        self.update_status_var.set("Status: Checking for updates...")
        self._refresh_update_controls()

        def _check() -> None:
            result = self.update_manager.check_for_updates()
            self.root.after(0, lambda: self._handle_update_check_result(result))

        threading.Thread(target=_check, daemon=True).start()

    def _handle_update_check_result(self, result: UpdateCheckResult, background: bool = False) -> None:
        self.update_check_in_progress = False

        if result.update_available:
            status_message = f"Update available: v{result.latest_version or '?'}"
        elif result.success:
            status_message = result.message
        else:
            status_message = f"Update check failed: {result.message}"

        self.update_status_var.set(f"Status: {status_message}")

        if not background:
            messagebox.showinfo("Update Check", result.message)

        if result.update_available:
            self._set_apply_update_enabled(True)
            self.add_commentary("System", result.message, "success")
            self.update_available = True
            self._refresh_update_controls()
            if not background:
                if messagebox.askyesno("Update Available", "Update detected. Apply now?"):
                    self.download_and_apply_update()
        elif result.success:
            if not background:
                self.add_commentary("System", result.message)
        else:
            self.add_commentary("System", result.message, "error")

    def download_and_apply_update(self) -> None:
        if self.update_install_in_progress:
            self.update_status_var.set("Status: Update installation already running.")
            messagebox.showinfo("Update Install", "An update installation is already in progress.")
            return
        if not REQUESTS_AVAILABLE:
            self.update_status_var.set("Status: Updates unavailable (missing requests module).")
            messagebox.showerror("Update Install", "Requests package unavailable; install 'requests' to enable updates.")
            return

        self.update_install_in_progress = True
        self.add_commentary("System", "Downloading update payload...")
        self.update_status_var.set("Status: Downloading update payload...")

        def _download() -> None:
            result = self.update_manager.download_and_apply_update()
            self.root.after(0, lambda: self._handle_update_install_result(result))

        threading.Thread(target=_download, daemon=True).start()

    def _handle_update_install_result(self, result: UpdateApplyResult) -> None:
        self.update_install_in_progress = False
        if result.success:
            self.update_status_var.set("Status: Update downloaded. Restart to apply.")
            self.add_commentary("System", result.message, "success")
            messagebox.showinfo("Update Install", result.message + "\nPlease restart the launcher to apply changes.")
            self.update_available = False
        else:
            self.update_status_var.set(f"Status: Update failed - {result.message}")
            self.add_commentary("System", result.message, "error")
            messagebox.showerror("Update Install", result.message)
            self._set_apply_update_enabled(True)

    def _set_apply_update_enabled(self, enabled: bool) -> None:
        if self.apply_update_button is None:
            return

        try:
            if enabled:
                self.apply_update_button.state(["!disabled"])
            else:
                self.apply_update_button.state(["disabled"])
        except Exception:
            pass

        self._refresh_update_controls()

    def _refresh_update_controls(self) -> None:
        if self.check_updates_button is not None:
            try:
                can_check = (
                    REQUESTS_AVAILABLE
                    and self.update_manager.is_supported()
                    and not self.update_install_in_progress
                    and not self.update_check_in_progress
                )
                if can_check:
                    self.check_updates_button.state(["!disabled"])
                else:
                    self.check_updates_button.state(["disabled"])
            except Exception:
                pass

        if self.apply_update_button is not None:
            try:
                apply_enabled = (
                    REQUESTS_AVAILABLE
                    and self.update_manager.is_supported()
                    and self.update_available
                    and not self.update_install_in_progress
                )
                if apply_enabled:
                    self.apply_update_button.state(["!disabled"])
                else:
                    self.apply_update_button.state(["disabled"])
            except Exception:
                pass

    def run(self) -> None:
        try:
            self.add_commentary("System", "Aperture Science Enrichment Center online. Welcome.", "success")
            self.root.mainloop()
        except KeyboardInterrupt:
            self.add_commentary("System", "Emergency shutdown initiated.")
        except Exception as exc:
            messagebox.showerror("Critical System Failure", f"Aperture Science systems failure: {exc}")


__all__ = ["ApertureEnrichmentCenterGUI"]
