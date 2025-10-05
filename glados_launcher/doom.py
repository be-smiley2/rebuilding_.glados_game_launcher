"""Arcade-style DOOM 2016 inspired mini-game for the launcher."""
from __future__ import annotations

import math
import random
import time
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from .theme import ApertureTheme
from .achievements import AchievementManager


class Doom2016MiniGame:
    """Small top-down arena shooter inspired by DOOM (2016)."""

    WIDTH = 720
    HEIGHT = 480
    FRAME_MS = 30
    PLAYER_SPEED = 7
    BULLET_SPEED = 18
    DEMON_BASE_SPEED = 3
    FIRE_COOLDOWN = 180  # ms
    SPAWN_INTERVAL = 1200  # ms
    SPAWN_ACCELERATION = 45  # ms faster per threat level
    MAX_ARMOR = 3

    def __init__(
        self,
        root: tk.Tk,
        *,
        on_close: Optional[callable] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        self.root = root
        self.on_close = on_close
        self.achievement_manager = achievement_manager

        self.window = tk.Toplevel(root)
        self.window.title("DOOM 2016 Combat Simulator")
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.geometry(f"{self.WIDTH+40}x{self.HEIGHT+200}")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        header = ttk.Frame(self.window, style="Panel.TFrame")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(
            header,
            text="Rip and Tear Training Protocol",
            style="PanelTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Eliminate waves of holographic demons. Move with WASD/arrow keys, space to fire plasma. Esc exits.",
            style="PanelCaption.TLabel",
            wraplength=self.WIDTH,
        ).pack(anchor="w", pady=(4, 0))

        stats_frame = ttk.Frame(self.window, style="Panel.TFrame")
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.score_var = tk.StringVar(value="Combat Rating: 0")
        self.kills_var = tk.StringVar(value="Demons Eliminated: 0")
        self.threat_var = tk.StringVar(value="Threat Level: 1")
        self.armor_var = tk.StringVar(value="Armor Integrity: ███")

        ttk.Label(stats_frame, textvariable=self.score_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.kills_var, style="Wheatley.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.threat_var, style="Aperture.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.armor_var, style="PanelBody.TLabel").pack(anchor="w")

        arena_frame = ttk.Frame(self.window, style="Panel.TFrame")
        arena_frame.pack(padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(
            arena_frame,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#11151c",
            highlightthickness=0,
        )
        self.canvas.pack()

        ttk.Label(
            self.window,
            text="Tip: Maintain momentum. Armor is lost on contact – lose all armor and the run ends.",
            style="PanelCaption.TLabel",
            wraplength=self.WIDTH,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        control_frame = ttk.Frame(self.window, style="Panel.TFrame")
        control_frame.pack(fill="x", padx=20, pady=(0, 20))

        ttk.Button(
            control_frame,
            text="End Simulation",
            style="Aperture.TButton",
            command=self.close,
            width=18,
        ).pack(anchor="e")

        self.window.bind("<KeyPress>", self._on_key_press)
        self.window.bind("<KeyRelease>", self._on_key_release)
        self.window.bind("<space>", self._on_fire)
        self.window.bind("<Escape>", lambda event: self.close())
        self.window.after(100, self.window.focus_force)

        self._closed = False
        self.running = True

        self.player = {
            "x": 70.0,
            "y": self.HEIGHT / 2,
            "size": 26,
            "armor": self.MAX_ARMOR,
            "id": None,
        }
        self.input_state: Dict[str, bool] = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
        }
        self.last_fire_time = 0.0
        self.bullets: List[Dict[str, float]] = []
        self.demons: List[Dict[str, float]] = []

        self.score = 0
        self.kills = 0
        self.threat_level = 1
        self.loop_handle: Optional[str] = None
        self.spawn_handle: Optional[str] = None
        self.start_time = time.time()
        self._session_recorded = False

        self._draw_player()
        self._schedule_loop()
        self._schedule_spawn()

    @property
    def is_open(self) -> bool:
        return not self._closed and self.window.winfo_exists()

    def focus(self) -> None:
        if self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def close(self) -> None:
        if self._closed:
            return

        aborted = self.running and self.player.get("armor", 0) > 0
        self.running = False

        if self.loop_handle is not None:
            try:
                self.window.after_cancel(self.loop_handle)
            except Exception:
                pass
            self.loop_handle = None

        if self.spawn_handle is not None:
            try:
                self.window.after_cancel(self.spawn_handle)
            except Exception:
                pass
            self.spawn_handle = None

        self._record_session(aborted)

        self._closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window.winfo_exists():
            self.window.destroy()

    # -- Game loop -----------------------------------------------------------------

    def _schedule_loop(self) -> None:
        if not self.running:
            return
        self.loop_handle = self.window.after(self.FRAME_MS, self._game_loop)

    def _schedule_spawn(self) -> None:
        if not self.running:
            return
        interval = max(450, self.SPAWN_INTERVAL - (self.threat_level - 1) * self.SPAWN_ACCELERATION)
        self.spawn_handle = self.window.after(interval, self._spawn_demon)

    def _game_loop(self) -> None:
        if not self.running:
            return

        self._update_player()
        self._update_bullets()
        self._update_demons()
        self._check_collisions()
        self._update_hud()

        self.threat_level = 1 + self.kills // 10
        self._schedule_loop()

    def _spawn_demon(self) -> None:
        if not self.running:
            return

        demon_size = random.randint(24, 40)
        speed = self.DEMON_BASE_SPEED + (self.threat_level - 1) * 0.4 + random.uniform(-0.5, 0.5)
        demon = {
            "x": float(self.WIDTH + demon_size),
            "y": float(random.randint(demon_size, self.HEIGHT - demon_size)),
            "size": float(demon_size),
            "speed": speed,
            "id": None,
        }
        demon["id"] = self.canvas.create_oval(
            demon["x"] - demon_size / 2,
            demon["y"] - demon_size / 2,
            demon["x"] + demon_size / 2,
            demon["y"] + demon_size / 2,
            fill="#aa1b1b",
            outline="#4d0808",
            width=2,
        )
        self.demons.append(demon)
        self._schedule_spawn()

    def _update_player(self) -> None:
        dx = dy = 0.0
        if self.input_state["up"]:
            dy -= self.PLAYER_SPEED
        if self.input_state["down"]:
            dy += self.PLAYER_SPEED
        if self.input_state["left"]:
            dx -= self.PLAYER_SPEED
        if self.input_state["right"]:
            dx += self.PLAYER_SPEED

        if dx and dy:
            length = math.sqrt(dx * dx + dy * dy)
            dx = dx / length * self.PLAYER_SPEED
            dy = dy / length * self.PLAYER_SPEED

        self.player["x"] = min(max(self.player["x"] + dx, 30), self.WIDTH - 30)
        self.player["y"] = min(max(self.player["y"] + dy, 30), self.HEIGHT - 30)
        self._draw_player()

    def _draw_player(self) -> None:
        size = self.player["size"]
        x = self.player["x"]
        y = self.player["y"]
        if self.player["id"] is None:
            self.player["id"] = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, fill="#20d07a", outline="#0f7f45", width=2)
        self.canvas.coords(
            self.player["id"],
            x - size,
            y,
            x - size / 2,
            y - size / 2,
            x + size,
            y,
            x - size / 2,
            y + size / 2,
        )

    def _update_bullets(self) -> None:
        active: List[Dict[str, float]] = []
        for bullet in self.bullets:
            bullet["x"] += self.BULLET_SPEED
            if bullet["x"] > self.WIDTH + 20:
                if bullet.get("id"):
                    self.canvas.delete(bullet["id"])
                continue
            self.canvas.move(bullet["id"], self.BULLET_SPEED, 0)
            active.append(bullet)
        self.bullets = active

    def _update_demons(self) -> None:
        active: List[Dict[str, float]] = []
        for demon in self.demons:
            demon["x"] -= demon["speed"]
            self.canvas.move(demon["id"], -demon["speed"], 0)
            if demon["x"] < -50:
                self.canvas.delete(demon["id"])
                continue
            active.append(demon)
        self.demons = active

    def _check_collisions(self) -> None:
        to_remove_bullets: List[Dict[str, float]] = []
        to_remove_demons: List[Dict[str, float]] = []

        for demon in self.demons:
            demon_box = self.canvas.bbox(demon["id"])
            if not demon_box:
                continue
            for bullet in self.bullets:
                if bullet in to_remove_bullets:
                    continue
                if self._intersects(bullet["id"], demon_box):
                    to_remove_bullets.append(bullet)
                    to_remove_demons.append(demon)
                    break

            if self._player_hit(demon_box):
                to_remove_demons.append(demon)
                self._lose_armor()
                if self.player["armor"] <= 0:
                    self._game_over()
                    return

        if to_remove_bullets or to_remove_demons:
            for bullet in to_remove_bullets:
                if bullet.get("id"):
                    self.canvas.delete(bullet["id"])
            for demon in to_remove_demons:
                if demon.get("id"):
                    self.canvas.delete(demon["id"])
                if demon in self.demons:
                    self.demons.remove(demon)
                    self.score += 50 + int(demon["size"]) * 2
                    self.kills += 1

            self.bullets = [b for b in self.bullets if b not in to_remove_bullets]

    def _intersects(self, bullet_id: int, demon_box: tuple) -> bool:
        bullet_box = self.canvas.bbox(bullet_id)
        if not bullet_box:
            return False
        bx1, by1, bx2, by2 = bullet_box
        dx1, dy1, dx2, dy2 = demon_box
        return not (bx2 < dx1 or bx1 > dx2 or by2 < dy1 or by1 > dy2)

    def _player_hit(self, demon_box: tuple) -> bool:
        player_box = self.canvas.bbox(self.player["id"])
        if not player_box:
            return False
        px1, py1, px2, py2 = player_box
        dx1, dy1, dx2, dy2 = demon_box
        return not (px2 < dx1 or px1 > dx2 or py2 < dy1 or py1 > dy2)

    def _lose_armor(self) -> None:
        if self.player["armor"] > 0:
            self.player["armor"] -= 1
        self._update_hud()

    def _on_key_press(self, event: tk.Event) -> None:
        if event.keysym in ("w", "W", "Up"):
            self.input_state["up"] = True
        if event.keysym in ("s", "S", "Down"):
            self.input_state["down"] = True
        if event.keysym in ("a", "A", "Left"):
            self.input_state["left"] = True
        if event.keysym in ("d", "D", "Right"):
            self.input_state["right"] = True

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym in ("w", "W", "Up"):
            self.input_state["up"] = False
        if event.keysym in ("s", "S", "Down"):
            self.input_state["down"] = False
        if event.keysym in ("a", "A", "Left"):
            self.input_state["left"] = False
        if event.keysym in ("d", "D", "Right"):
            self.input_state["right"] = False

    def _on_fire(self, event: tk.Event) -> None:
        now = time.time() * 1000
        if now - self.last_fire_time < self.FIRE_COOLDOWN:
            return
        self.last_fire_time = now
        bullet = {
            "x": self.player["x"],
            "y": self.player["y"],
            "id": self.canvas.create_rectangle(
                self.player["x"],
                self.player["y"] - 4,
                self.player["x"] + 18,
                self.player["y"] + 4,
                fill="#f9d648",
                outline="#af9400",
            ),
        }
        self.bullets.append(bullet)

    def _update_hud(self) -> None:
        self.score_var.set(f"Combat Rating: {self.score}")
        self.kills_var.set(f"Demons Eliminated: {self.kills}")
        self.threat_var.set(f"Threat Level: {self.threat_level}")
        armor_blocks = "█" * self.player["armor"] + "░" * (self.MAX_ARMOR - self.player["armor"])
        self.armor_var.set(f"Armor Integrity: {armor_blocks}")

    def _game_over(self) -> None:
        if not self.running:
            return
        self.running = False
        messagebox.showinfo(
            "Combat Simulator",
            f"Armor depleted. Final rating {self.score} with {self.kills} demons eliminated.",
        )
        self.close()

    def _record_session(self, aborted: bool) -> None:
        if self._session_recorded or not self.achievement_manager:
            return
        self._session_recorded = True

        duration = time.time() - self.start_time
        unlocked = self.achievement_manager.record_mini_game_session(
            "doom_slayer_training",
            score=self.score,
            lines=self.kills,
            level=self.threat_level,
            duration=duration,
            armor=max(self.player.get("armor", 0), 0),
            aborted=aborted,
        )

        if unlocked:
            summary = "\n".join(f"• {ach['name']}: {ach['description']}" for ach in unlocked)
            messagebox.showinfo("Mini-Game Achievements", f"New achievements unlocked!\n\n{summary}")


__all__ = ["Doom2016MiniGame"]
