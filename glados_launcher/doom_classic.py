"""Classic DOOM inspired mini-games for the launcher."""
from __future__ import annotations

import random
import time
from typing import Callable, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from .achievements import AchievementManager
from .theme import ApertureTheme


class _ClassicDoomMiniGame:
    """Shared implementation for classic DOOM episode mini-games."""

    WIDTH = 640
    HEIGHT = 420
    FRAME_MS = 30
    PLAYER_SPEED = 10
    SHOT_SPEED = 16
    ENEMY_BASE_SPEED = 1.9
    ENEMY_SPEED_SCALING = 0.18
    BASE_SPAWN_INTERVAL = 1100
    MIN_SPAWN_INTERVAL = 320
    FIRE_COOLDOWN = 0.32
    MAX_LIVES = 3

    def __init__(
        self,
        root: tk.Tk,
        *,
        game_key: str,
        episode_title: str,
        episode_caption: str,
        enemy_palette: List[str],
        backdrop_color: str,
        on_close: Optional[Callable[[], None]] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        self.root = root
        self.game_key = game_key
        self.episode_title = episode_title
        self.episode_caption = episode_caption
        self.enemy_palette = enemy_palette
        self.backdrop_color = backdrop_color
        self.on_close = on_close
        self.achievement_manager = achievement_manager

        self.window = tk.Toplevel(root)
        self.window.title(episode_title)
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.geometry(f"{self.WIDTH + 40}x{self.HEIGHT + 220}")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        header = ttk.Frame(self.window, style="Panel.TFrame")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(header, text=episode_title, style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text=episode_caption,
            style="PanelCaption.TLabel",
            wraplength=self.WIDTH,
        ).pack(anchor="w", pady=(4, 0))

        stats_frame = ttk.Frame(self.window, style="Panel.TFrame")
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.score_var = tk.StringVar(value="Combat Score: 0")
        self.kills_var = tk.StringVar(value="Threats Neutralised: 0")
        self.level_var = tk.StringVar(value="Threat Tier: 1")
        self.timer_var = tk.StringVar(value="Operation Time: 0.0s")
        self.lives_var = tk.StringVar(value="Suit Integrity: ███")
        self.combo_var = tk.StringVar(value="Stability: Nominal")

        ttk.Label(stats_frame, textvariable=self.score_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.kills_var, style="Wheatley.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.level_var, style="Aperture.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.timer_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.lives_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.combo_var, style="PanelCaption.TLabel").pack(anchor="w")

        arena_frame = ttk.Frame(self.window, style="Panel.TFrame")
        arena_frame.pack(padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(
            arena_frame,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg=self.backdrop_color,
            highlightthickness=0,
        )
        self.canvas.pack()

        ttk.Label(
            self.window,
            text="Controls: A/Left and D/Right to strafe, Space to fire. Esc exits the simulation.",
            style="PanelCaption.TLabel",
            wraplength=self.WIDTH,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        control_frame = ttk.Frame(self.window, style="Panel.TFrame")
        control_frame.pack(fill="x", padx=20, pady=(0, 20))

        ttk.Button(
            control_frame,
            text="Abort Simulation",
            style="Aperture.TButton",
            command=self.close,
            width=20,
        ).pack(anchor="e")

        self.window.bind("<KeyPress>", self._on_key_press)
        self.window.bind("<KeyRelease>", self._on_key_release)
        self.window.bind("<space>", self._fire)
        self.window.bind("<Escape>", lambda event: self.close())
        self.window.after(100, self.window.focus_force)

        self._closed = False
        self.running = True
        self._session_recorded = False

        self.player_x = self.WIDTH / 2
        self.input_state: Dict[str, bool] = {"left": False, "right": False}
        self.last_fire_time = 0.0
        self.combo = 0
        self.combo_timeout = 0.0

        self.score = 0
        self.kills = 0
        self.threat_level = 1
        self.lives = self.MAX_LIVES

        self.shots: List[Dict[str, float]] = []
        self.enemies: List[Dict[str, float]] = []

        self.spawn_interval = float(self.BASE_SPAWN_INTERVAL)
        self.spawn_timer = 0.0
        self.start_time = time.time()
        self.last_update = time.time()

        self.loop_handle: Optional[str] = None

        self._update_hud()
        self._render()
        self._schedule_loop()

    # -- Properties -----------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return not self._closed and self.window.winfo_exists()

    def focus(self) -> None:
        if self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    # -- Event handling -------------------------------------------------------------

    def _on_key_press(self, event: tk.Event) -> None:
        if event.keysym in {"Left", "a", "A"}:
            self.input_state["left"] = True
        elif event.keysym in {"Right", "d", "D"}:
            self.input_state["right"] = True

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym in {"Left", "a", "A"}:
            self.input_state["left"] = False
        elif event.keysym in {"Right", "d", "D"}:
            self.input_state["right"] = False

    def _fire(self, event: Optional[tk.Event] = None) -> None:
        if not self.running:
            return
        now = time.time()
        if now - self.last_fire_time < self.FIRE_COOLDOWN:
            return
        self.last_fire_time = now
        shot = {"x": self.player_x, "y": self.HEIGHT - 70}
        self.shots.append(shot)

    # -- Game loop ------------------------------------------------------------------

    def _schedule_loop(self) -> None:
        if not self.running:
            return
        self.loop_handle = self.window.after(self.FRAME_MS, self._game_loop)

    def _game_loop(self) -> None:
        if not self.running:
            return

        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        self.spawn_timer += elapsed * 1000

        self._update_player()
        self._update_shots()
        self._update_enemies()
        if not self.running or not self.window.winfo_exists():
            return
        self._handle_collisions()
        self._maybe_spawn_enemy()
        self._decay_combo(elapsed)

        if not self.running or not self.window.winfo_exists():
            return

        self._update_hud()
        self._render()

        self._schedule_loop()

    def _update_player(self) -> None:
        if self.input_state.get("left"):
            self.player_x -= self.PLAYER_SPEED
        if self.input_state.get("right"):
            self.player_x += self.PLAYER_SPEED
        self.player_x = max(36, min(self.WIDTH - 36, self.player_x))

    def _update_shots(self) -> None:
        for shot in self.shots:
            shot["y"] -= self.SHOT_SPEED
        self.shots = [shot for shot in self.shots if shot["y"] > -40]

    def _update_enemies(self) -> None:
        still_active: List[Dict[str, float]] = []
        for enemy in self.enemies:
            enemy["y"] += enemy["speed"]
            if enemy["y"] >= self.HEIGHT - 60:
                self.lives -= 1
                if self.lives <= 0:
                    self.lives = 0
                    self._game_over()
                    return
            else:
                still_active.append(enemy)
        self.enemies = still_active

    def _handle_collisions(self) -> None:
        if not self.enemies or not self.shots:
            return

        remaining_shots: List[Dict[str, float]] = []
        for shot in self.shots:
            hit_enemy = None
            for enemy in self.enemies:
                if abs(shot["x"] - enemy["x"]) <= enemy["size"] and abs(shot["y"] - enemy["y"]) <= enemy["size"]:
                    hit_enemy = enemy
                    break
            if hit_enemy:
                self.enemies.remove(hit_enemy)
                self._on_enemy_destroyed()
            else:
                remaining_shots.append(shot)
        self.shots = remaining_shots

    def _on_enemy_destroyed(self) -> None:
        self.kills += 1
        self.combo += 1
        self.combo_timeout = time.time() + 2.2
        self.threat_level = max(1, 1 + self.kills // 8)
        self.spawn_interval = max(
            self.MIN_SPAWN_INTERVAL,
            self.BASE_SPAWN_INTERVAL - (self.threat_level - 1) * 75,
        )
        self.score += 120 + (self.threat_level * 35) + int(self.combo * 10)

    def _maybe_spawn_enemy(self) -> None:
        if self.spawn_timer < self.spawn_interval:
            return
        self.spawn_timer %= max(1.0, self.spawn_interval)
        color = random.choice(self.enemy_palette)
        size = random.randint(12, 24)
        speed = self.ENEMY_BASE_SPEED + random.uniform(0.0, 0.9) + self.threat_level * self.ENEMY_SPEED_SCALING
        enemy = {"x": random.randint(40, self.WIDTH - 40), "y": -size * 2, "size": size, "color": color, "speed": speed}
        self.enemies.append(enemy)

    def _decay_combo(self, elapsed: float) -> None:
        if self.combo <= 0:
            return
        if time.time() >= self.combo_timeout:
            self.combo = 0

    # -- Rendering ------------------------------------------------------------------

    def _render(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill=self.backdrop_color, outline="")
        self.canvas.create_rectangle(0, self.HEIGHT - 60, self.WIDTH, self.HEIGHT, fill="#1d1f27", outline="")

        # Draw player pod
        base_y = self.HEIGHT - 40
        self.canvas.create_polygon(
            self.player_x - 24,
            base_y + 18,
            self.player_x,
            base_y - 18,
            self.player_x + 24,
            base_y + 18,
            fill="#ffb347",
            outline="#ffd27f",
        )
        self.canvas.create_rectangle(
            self.player_x - 8,
            base_y - 28,
            self.player_x + 8,
            base_y - 12,
            fill="#d1f7ff",
            outline="",
        )

        # Shots
        for shot in self.shots:
            self.canvas.create_rectangle(
                shot["x"] - 3,
                shot["y"] - 18,
                shot["x"] + 3,
                shot["y"],
                fill="#f5ff9c",
                outline="",
            )

        # Enemies
        for enemy in self.enemies:
            self.canvas.create_oval(
                enemy["x"] - enemy["size"],
                enemy["y"] - enemy["size"],
                enemy["x"] + enemy["size"],
                enemy["y"] + enemy["size"],
                fill=enemy["color"],
                outline="#16141f",
                width=2,
            )

        # Combo indicator
        if self.combo > 1:
            self.canvas.create_text(
                self.player_x,
                self.HEIGHT - 90,
                text=f"Combo x{self.combo}",
                fill="#ffec85",
                font=(ApertureTheme.FONT_BASE[0], 12, "bold"),
            )

    # -- HUD -----------------------------------------------------------------------

    def _update_hud(self) -> None:
        elapsed = time.time() - self.start_time
        self.score_var.set(f"Combat Score: {self.score}")
        self.kills_var.set(f"Threats Neutralised: {self.kills}")
        self.level_var.set(f"Threat Tier: {self.threat_level}")
        self.timer_var.set(f"Operation Time: {elapsed:0.1f}s")
        lives_blocks = "█" * self.lives + "░" * (self.MAX_LIVES - self.lives)
        self.lives_var.set(f"Suit Integrity: {lives_blocks}")
        if self.combo > 1:
            self.combo_var.set(f"Stability: Combo x{self.combo}")
        else:
            self.combo_var.set("Stability: Nominal")

    # -- Session handling -----------------------------------------------------------

    def close(self) -> None:
        if self._closed:
            return
        aborted = self.running
        self.running = False
        if self.loop_handle is not None:
            try:
                self.window.after_cancel(self.loop_handle)
            except Exception:
                pass
            self.loop_handle = None
        self._record_session(aborted)
        self._closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window.winfo_exists():
            self.window.destroy()

    def _game_over(self) -> None:
        if not self.running:
            return
        self.running = False
        self._record_session(aborted=False)
        messagebox.showinfo(
            self.episode_title,
            f"Simulation failed. Final score {self.score} with {self.kills} threats neutralised.",
        )
        self.close()

    def _record_session(self, aborted: bool) -> None:
        if self._session_recorded or not self.achievement_manager:
            return
        self._session_recorded = True

        duration = max(0.0, time.time() - self.start_time)
        unlocked = self.achievement_manager.record_mini_game_session(
            self.game_key,
            score=self.score,
            lines=self.kills,
            level=self.threat_level,
            duration=duration,
            armor=self.lives,
            aborted=aborted,
        )

        if unlocked:
            summary = "\n".join(f"• {ach['name']}: {ach['description']}" for ach in unlocked)
            messagebox.showinfo("Mini-Game Achievements", f"New achievements unlocked!\n\n{summary}")


class DoomClassicEpisodeIMiniGame(_ClassicDoomMiniGame):
    """Episode I (Knee-Deep in the Dead) themed mini-game."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        on_close: Optional[Callable[[], None]] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        super().__init__(
            root,
            game_key="doom_classic_1",
            episode_title="Classic DOOM – Episode I",
            episode_caption="Hold the Phobos landing zone by repelling demon charges.",
            enemy_palette=["#ff5e5e", "#e36a3b", "#c94747", "#ff9d5c"],
            backdrop_color="#070b11",
            on_close=on_close,
            achievement_manager=achievement_manager,
        )


class DoomClassicEpisodeIIMiniGame(_ClassicDoomMiniGame):
    """Episode II (Hell on Earth) themed mini-game."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        on_close: Optional[Callable[[], None]] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        super().__init__(
            root,
            game_key="doom_classic_2",
            episode_title="Classic DOOM – Episode II",
            episode_caption="Defend the Mars teleporter relay against relentless hellspawn.",
            enemy_palette=["#8cf7ff", "#6cc1ff", "#9f9aff", "#d87bff"],
            backdrop_color="#0a0614",
            on_close=on_close,
            achievement_manager=achievement_manager,
        )


__all__ = [
    "DoomClassicEpisodeIMiniGame",
    "DoomClassicEpisodeIIMiniGame",
]

