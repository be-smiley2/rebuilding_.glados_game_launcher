"""Portal-inspired GUI for the Aperture Science Enrichment Center launcher."""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List

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


THEME_PALETTES = {
    "dark": {
        "background": "#1b1f22",
        "surface": "#242a2f",
        "surface_highlight": "#2f353c",
        "surface_muted": "#161a1d",
        "text": "#f4f6f8",
        "text_muted": "#aeb7c4",
        "accent": "#f7a11b",
        "accent_hover": "#ffb54a",
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
    },
}


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
        self.games: List[SteamGame] = []

        self._build_ui()
        self._apply_theme()

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

        theme_switch = ttk.Frame(header)
        theme_switch.pack(side="right")

        ttk.Label(theme_switch, text="Theme:").pack(side="left", padx=(0, 6))
        theme_menu = ttk.OptionMenu(
            theme_switch,
            self.theme_var,
            self.theme_var.get(),
            *THEME_PALETTES.keys(),
            command=lambda *_: self._apply_theme(),
        )
        theme_menu.pack(side="left")

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=24)

        self.scan_button = ttk.Button(controls, text="Scan for Games", command=self.scan_for_games)
        self.scan_button.pack(side="left")

        self.launch_button = ttk.Button(
            controls,
            text="Launch Selected",
            command=self.launch_selected_game,
            state="disabled",
        )
        self.launch_button.pack(side="left", padx=(12, 0))

        ttk.Button(controls, text="Quit", command=self.destroy).pack(side="right")

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=24, pady=(12, 24))

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

        status_bar = ttk.Frame(self)
        status_bar.pack(fill="x", padx=24, pady=(0, 24))

        self.status_label = ttk.Label(status_bar, textvariable=self.status_var)
        self.status_label.pack(side="left")

        hint = ttk.Label(
            status_bar,
            text="Double-click a game to launch it once a scan has completed.",
            style="Hint.TLabel",
        )
        hint.pack(side="right")

    def _apply_theme(self) -> None:
        """Update widget colors based on the selected theme."""

        palette = THEME_PALETTES[self.theme_var.get()]

        self.configure(bg=palette["background"])
        for frame in self.winfo_children():
            if isinstance(frame, tk.Frame):
                frame.configure(bg=palette["background"])

        style = self.style
        style.configure(
            "TFrame",
            background=palette["background"],
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


def main() -> None:
    """Start the Tkinter application."""

    app = ApertureLauncherGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
