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
    """Small pseudo-3D combat simulator inspired by DOOM (2016)."""

    WIDTH = 720
    HEIGHT = 480
    FRAME_MS = 30
    PLAYER_SPEED = 0.28  # world units per frame (strafe)
    PLAYER_FORWARD_SPEED = 0.26  # world units per frame (advance/retreat)
    PLAYER_NEAR_LIMIT = 0.65
    PLAYER_FAR_LIMIT = 5.5
    BULLET_SPEED = 0.9  # world units per frame (forward)
    DEMON_BASE_SPEED = 0.065  # world units per frame (towards player)
    FIRE_COOLDOWN = 180  # ms
    SPAWN_INTERVAL = 1200  # ms
    SPAWN_ACCELERATION = 45  # ms faster per threat level
    MAX_ARMOR = 3
    MAX_HEALTH = 100
    HEALTH_PICKUP_AMOUNT = 25
    HEALTH_LOSS_PER_HIT = 34
    PICKUP_DROP_CHANCE = 0.28
    PICKUP_LIFETIME = 9.0  # seconds
    PICKUP_SPEED = 0.04
    POWER_UP_DURATION = 6.0  # seconds
    HASTE_FIRE_RATE_MULTIPLIER = 0.55
    HASTE_BULLET_SPEED_MULTIPLIER = 1.3

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
            text=(
                "Step into a holographic arena and eliminate rushing demons. "
                "Move with WASD/arrow keys, space to fire plasma. Esc exits."
            ),
            style="PanelCaption.TLabel",
            wraplength=self.WIDTH,
        ).pack(anchor="w", pady=(4, 0))

        stats_frame = ttk.Frame(self.window, style="Panel.TFrame")
        stats_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.score_var = tk.StringVar(value="Combat Rating: 0")
        self.kills_var = tk.StringVar(value="Demons Eliminated: 0")
        self.threat_var = tk.StringVar(value="Threat Level: 1")
        self.health_var = tk.StringVar(value="Vital Signs: 100%")
        self.armor_var = tk.StringVar(value="Armor Integrity: ███")
        self.powerup_var = tk.StringVar(value="Power-Up: None")

        ttk.Label(stats_frame, textvariable=self.score_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.kills_var, style="Wheatley.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.threat_var, style="Aperture.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.health_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.armor_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.powerup_var, style="PanelCaption.TLabel").pack(anchor="w")

        arena_frame = ttk.Frame(self.window, style="Panel.TFrame")
        arena_frame.pack(padx=20, pady=(0, 10))

        self.canvas = tk.Canvas(
            arena_frame,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#040608",
            highlightthickness=0,
        )
        self.canvas.pack()

        ttk.Label(
            self.window,
            text="Tip: Maintain your footing. Demons will breach the line if they reach you.",
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
            "x": 0.0,  # horizontal position in world units
            "z": 0.9,  # forward position in world units
            "tilt": 0.0,  # pitch offset for the camera
            "armor": self.MAX_ARMOR,
            "health": self.MAX_HEALTH,
        }
        self.input_state: Dict[str, bool] = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
        }
        self.last_fire_time = 0.0
        self.bullets: List[Dict[str, float]] = []
        self.demons: List[Dict[str, float]] = []
        self.pickups: List[Dict[str, float]] = []

        self.field_of_view = math.radians(72)
        self.projection_plane = (self.WIDTH / 2) / math.tan(self.field_of_view / 2)
        self.horizon_y = self.HEIGHT * 0.38

        self.score = 0
        self.kills = 0
        self.threat_level = 1
        self.fire_cooldown = float(self.FIRE_COOLDOWN)
        self.bullet_speed = float(self.BULLET_SPEED)
        self.active_power_up: Optional[str] = None
        self.power_up_end_time = 0.0
        self.loop_handle: Optional[str] = None
        self.spawn_handle: Optional[str] = None
        self.start_time = time.time()
        self._session_recorded = False

        self._render_scene()
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
        self._update_pickups()
        self._check_collisions()
        if not self.running:
            return
        self._check_pickup_collisions()
        self._update_power_up_state()
        self._update_hud()
        self._render_scene()

        self.threat_level = 1 + self.kills // 10
        self._schedule_loop()

    # -- Entities ------------------------------------------------------------------

    def _spawn_demon(self) -> None:
        if not self.running:
            return

        demon_size = random.uniform(0.6, 1.4)
        base_speed = self.DEMON_BASE_SPEED + (self.threat_level - 1) * 0.01
        demon = {
            "x": random.uniform(-4.0, 4.0),
            "z": random.uniform(8.0, 20.0),
            "size": demon_size,
            "speed": base_speed + random.uniform(-0.01, 0.02),
        }
        self.demons.append(demon)
        self._schedule_spawn()

    def _update_player(self) -> None:
        if self.input_state["left"]:
            self.player["x"] -= self.PLAYER_SPEED
        if self.input_state["right"]:
            self.player["x"] += self.PLAYER_SPEED

        self.player["x"] = max(-4.5, min(4.5, self.player["x"]))

        if self.input_state["forward"]:
            self.player["z"] -= self.PLAYER_FORWARD_SPEED
        if self.input_state["backward"]:
            self.player["z"] += self.PLAYER_FORWARD_SPEED

        self.player["z"] = max(self.PLAYER_NEAR_LIMIT, min(self.PLAYER_FAR_LIMIT, self.player["z"]))

        tilt_target = 0.0
        if self.input_state["forward"]:
            tilt_target = 0.8
        elif self.input_state["backward"]:
            tilt_target = -0.6

        self.player["tilt"] += (tilt_target - self.player["tilt"]) * 0.22

    def _update_bullets(self) -> None:
        active: List[Dict[str, float]] = []
        for bullet in self.bullets:
            bullet["z"] += self.bullet_speed
            if bullet["z"] > 28:
                continue
            active.append(bullet)
        self.bullets = active

    def _update_demons(self) -> None:
        active: List[Dict[str, float]] = []
        for demon in self.demons:
            demon["z"] -= demon["speed"]
            demon["z"] = max(demon["z"], 0.25)
            active.append(demon)
        self.demons = active

    def _update_pickups(self) -> None:
        now = time.time()
        active: List[Dict[str, float]] = []
        for pickup in self.pickups:
            pickup["z"] = max(pickup["z"] - pickup.get("speed", self.PICKUP_SPEED), 0.35)
            if now - pickup.get("spawned", now) > pickup.get("lifetime", self.PICKUP_LIFETIME):
                continue
            active.append(pickup)
        self.pickups = active

    def _check_collisions(self) -> None:
        to_remove_bullets: List[Dict[str, float]] = []
        to_remove_demons: List[Dict[str, float]] = []
        killed_demons: List[Dict[str, float]] = []

        for demon in self.demons:
            if demon in to_remove_demons:
                continue

            for bullet in self.bullets:
                if bullet in to_remove_bullets:
                    continue

                if bullet["z"] >= demon["z"] - 0.45 and abs(bullet["x"] - demon["x"]) <= demon["size"] * 0.55:
                    to_remove_bullets.append(bullet)
                    to_remove_demons.append(demon)
                    killed_demons.append(demon)
                    break

            if demon in to_remove_demons:
                continue

            distance_to_player = demon["z"] - self.player["z"]
            if distance_to_player <= 0.25:
                if abs(demon["x"] - self.player["x"]) <= demon["size"] * 0.65:
                    to_remove_demons.append(demon)
                    if self.player["armor"] > 0:
                        self._lose_armor()
                    else:
                        self._lose_health()
                        if self.player["health"] <= 0:
                            self._game_over()
                            return
                else:
                    to_remove_demons.append(demon)
            elif distance_to_player < -0.35:
                to_remove_demons.append(demon)

        if to_remove_demons:
            for demon in to_remove_demons:
                if demon in self.demons:
                    self.demons.remove(demon)

        if killed_demons:
            for demon in killed_demons:
                self.score += 65 + int(demon["size"] * 55)
                self.kills += 1
                self._maybe_drop_pickup(demon)

        if to_remove_bullets:
            self.bullets = [b for b in self.bullets if b not in to_remove_bullets]

    def _lose_armor(self) -> None:
        if self.player["armor"] > 0:
            self.player["armor"] = max(0, self.player["armor"] - 1)
        self._update_hud()

    def _lose_health(self) -> None:
        if self.player["health"] > 0:
            self.player["health"] = max(0, self.player["health"] - self.HEALTH_LOSS_PER_HIT)
        self._update_hud()

    def _check_pickup_collisions(self) -> None:
        collected: List[Dict[str, float]] = []
        for pickup in self.pickups:
            if (
                abs(pickup["z"] - self.player["z"]) <= 0.45
                and abs(pickup["x"] - self.player["x"]) <= pickup.get("size", 1.0) * 0.7
            ):
                collected.append(pickup)

        if not collected:
            return

        for pickup in collected:
            self._collect_pickup(pickup)

        self.pickups = [p for p in self.pickups if p not in collected]

    def _collect_pickup(self, pickup: Dict[str, float]) -> None:
        pickup_type = pickup.get("type")
        if pickup_type == "health":
            before = self.player["health"]
            self.player["health"] = min(self.MAX_HEALTH, before + self.HEALTH_PICKUP_AMOUNT)
        else:
            self._apply_power_up("Haste")
        self._update_hud()

    def _apply_power_up(self, label: str) -> None:
        if label == "Haste":
            self.fire_cooldown = self.FIRE_COOLDOWN * self.HASTE_FIRE_RATE_MULTIPLIER
            self.bullet_speed = self.BULLET_SPEED * self.HASTE_BULLET_SPEED_MULTIPLIER
        self.active_power_up = label
        self.power_up_end_time = time.time() + self.POWER_UP_DURATION

    def _update_power_up_state(self) -> None:
        if not self.active_power_up:
            return
        if time.time() < self.power_up_end_time:
            return

        self.active_power_up = None
        self.fire_cooldown = float(self.FIRE_COOLDOWN)
        self.bullet_speed = float(self.BULLET_SPEED)
        self.power_up_end_time = 0.0

    def _maybe_drop_pickup(self, demon: Dict[str, float]) -> None:
        if random.random() > self.PICKUP_DROP_CHANCE:
            return

        pickup_type = "health" if random.random() < 0.6 else "haste"
        pickup = {
            "type": pickup_type,
            "x": demon["x"] + random.uniform(-0.6, 0.6),
            "z": max(demon["z"] - 0.5, 2.5),
            "size": random.uniform(0.6, 1.0),
            "speed": random.uniform(self.PICKUP_SPEED * 0.6, self.PICKUP_SPEED * 1.4),
            "spawned": time.time(),
            "lifetime": self.PICKUP_LIFETIME + random.uniform(-1.5, 1.5),
        }
        self.pickups.append(pickup)

    # -- Input ---------------------------------------------------------------------

    def _on_key_press(self, event: tk.Event) -> None:
        if event.keysym in ("w", "W", "Up"):
            self.input_state["forward"] = True
        if event.keysym in ("s", "S", "Down"):
            self.input_state["backward"] = True
        if event.keysym in ("a", "A", "Left"):
            self.input_state["left"] = True
        if event.keysym in ("d", "D", "Right"):
            self.input_state["right"] = True

    def _on_key_release(self, event: tk.Event) -> None:
        if event.keysym in ("w", "W", "Up"):
            self.input_state["forward"] = False
        if event.keysym in ("s", "S", "Down"):
            self.input_state["backward"] = False
        if event.keysym in ("a", "A", "Left"):
            self.input_state["left"] = False
        if event.keysym in ("d", "D", "Right"):
            self.input_state["right"] = False

    def _on_fire(self, event: tk.Event) -> None:
        now = time.time() * 1000
        if now - self.last_fire_time < self.fire_cooldown:
            return
        self.last_fire_time = now
        bullet = {
            "x": self.player["x"],
            "z": self.player["z"] + 0.3,
            "tilt": self.player["tilt"],
        }
        self.bullets.append(bullet)

    # -- Rendering -----------------------------------------------------------------

    def _render_scene(self) -> None:
        self.canvas.delete("all")
        tilt_offset = self.player["tilt"] * 38

        self._draw_background(tilt_offset)
        self._draw_corridor(tilt_offset)

        for demon in sorted(self.demons, key=lambda d: d["z"], reverse=True):
            self._draw_demon(demon, tilt_offset)
        for pickup in sorted(self.pickups, key=lambda p: p["z"], reverse=True):
            self._draw_pickup(pickup, tilt_offset)
        for bullet in sorted(self.bullets, key=lambda b: b["z"], reverse=True):
            self._draw_bullet(bullet, tilt_offset)

        self._draw_crosshair()

    def _draw_background(self, tilt_offset: float) -> None:
        sky_height = self.horizon_y + tilt_offset
        self.canvas.create_rectangle(0, 0, self.WIDTH, sky_height, fill="#0a1a2a", outline="")
        self.canvas.create_rectangle(0, sky_height, self.WIDTH, self.HEIGHT, fill="#1b0d0d", outline="")

    def _draw_corridor(self, tilt_offset: float) -> None:
        horizon = self.horizon_y + tilt_offset
        floor_mid = self.HEIGHT * 0.82 + tilt_offset * 0.6
        self.canvas.create_polygon(
            0,
            self.HEIGHT,
            self.WIDTH,
            self.HEIGHT,
            self.WIDTH * 0.78,
            horizon,
            self.WIDTH * 0.22,
            horizon,
            fill="#2a0f10",
            outline="#391414",
            width=2,
        )

        self.canvas.create_polygon(
            0,
            self.HEIGHT,
            self.WIDTH * 0.22,
            horizon,
            self.WIDTH * 0.32,
            floor_mid,
            self.WIDTH * 0.08,
            self.HEIGHT,
            fill="#1d0507",
            outline="",
        )

        self.canvas.create_polygon(
            self.WIDTH,
            self.HEIGHT,
            self.WIDTH * 0.78,
            horizon,
            self.WIDTH * 0.68,
            floor_mid,
            self.WIDTH * 0.92,
            self.HEIGHT,
            fill="#1d0507",
            outline="",
        )

    def _project(self, x: float, z: float) -> tuple[float, float, float]:
        relative_z = max(z - self.player["z"], 0.3)
        scale = self.projection_plane / relative_z
        screen_x = self.WIDTH / 2 + (x - self.player["x"]) * scale * 42
        return screen_x, scale, relative_z

    def _draw_demon(self, demon: Dict[str, float], tilt_offset: float) -> None:
        screen_x, scale, _ = self._project(demon["x"], demon["z"])
        size = demon["size"] * scale * 120
        bottom = self.HEIGHT * 0.86 + tilt_offset * 0.4
        top = bottom - size

        color = "#d13a3a" if demon["z"] < 4.0 else "#8f2626"
        outline = "#531212"
        width = max(1, int(2 + (1 / max(demon["z"], 1.0))))
        self.canvas.create_rectangle(
            screen_x - size * 0.35,
            top,
            screen_x + size * 0.35,
            bottom,
            fill=color,
            outline=outline,
            width=width,
        )

        glow_radius = max(6, int(18 / max(demon["z"], 1.2)))
        self.canvas.create_oval(
            screen_x - glow_radius,
            top - glow_radius,
            screen_x + glow_radius,
            top + glow_radius,
            outline="#ffdf73",
            width=1,
        )

    def _draw_pickup(self, pickup: Dict[str, float], tilt_offset: float) -> None:
        screen_x, scale, _ = self._project(pickup["x"], pickup["z"])
        size = pickup.get("size", 1.0) * scale * 110
        bottom = self.HEIGHT * 0.86 + tilt_offset * 0.4
        top = bottom - size * 0.8

        if pickup.get("type") == "health":
            fill, outline = "#2cc662", "#0f5226"
        else:
            fill, outline = "#4e7bff", "#1c2e73"

        self.canvas.create_oval(
            screen_x - size * 0.35,
            top,
            screen_x + size * 0.35,
            top + size,
            fill=fill,
            outline=outline,
            width=max(2, int(2 + scale * 0.6)),
        )

        self.canvas.create_text(
            screen_x,
            top + size * 0.5,
            text="✚" if pickup.get("type") == "health" else "⚡",
            fill="#f0f6ff",
            font=("Segoe UI", max(8, int(10 + scale * 1.8)), "bold"),
        )

    def _draw_bullet(self, bullet: Dict[str, float], tilt_offset: float) -> None:
        screen_x, scale, depth = self._project(bullet["x"], bullet["z"])
        top = self.horizon_y + tilt_offset - bullet["tilt"] * 60
        length = 16 + 42 / max(depth, 0.6)
        self.canvas.create_line(
            screen_x,
            top,
            screen_x,
            top + length,
            fill="#fadb5a",
            width=max(2, int(2 + scale * 0.8)),
        )

    def _draw_crosshair(self) -> None:
        cx = self.WIDTH / 2
        cy = self.horizon_y + self.player["tilt"] * 24
        size = 14
        self.canvas.create_line(cx - size, cy, cx + size, cy, fill="#e3f8ff", width=2)
        self.canvas.create_line(cx, cy - size, cx, cy + size, fill="#e3f8ff", width=2)

    # -- HUD -----------------------------------------------------------------------

    def _update_hud(self) -> None:
        self.score_var.set(f"Combat Rating: {self.score}")
        self.kills_var.set(f"Demons Eliminated: {self.kills}")
        self.threat_var.set(f"Threat Level: {self.threat_level}")
        health_percent = int((self.player["health"] / self.MAX_HEALTH) * 100)
        self.health_var.set(f"Vital Signs: {health_percent}%")
        armor_blocks = "█" * self.player["armor"] + "░" * (self.MAX_ARMOR - self.player["armor"])
        self.armor_var.set(f"Armor Integrity: {armor_blocks}")
        if self.active_power_up:
            remaining = max(0.0, self.power_up_end_time - time.time())
            self.powerup_var.set(f"Power-Up: {self.active_power_up} ({remaining:0.1f}s)")
        else:
            self.powerup_var.set("Power-Up: None")

    def _game_over(self) -> None:
        if not self.running:
            return
        self.running = False
        messagebox.showinfo(
            "Combat Simulator",
            f"Vital signs lost. Final rating {self.score} with {self.kills} demons eliminated.",
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
