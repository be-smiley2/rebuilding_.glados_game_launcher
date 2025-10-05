"""Rapid fire Space Invaders mini-game for the launcher."""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from .achievements import AchievementManager
from .theme import ApertureTheme


@dataclass
class Alien:
    item_id: int
    row: int
    col: int


@dataclass
class Projectile:
    item_id: int
    velocity: float


class RapidFireSpaceInvaders:
    """Simple colourful Space Invaders style game with rapid fire."""

    WIDTH = 640
    HEIGHT = 720
    PLAYER_SPEED = 14
    BULLET_SPEED = -16
    ENEMY_SPEED_BASE = 2.4
    ENEMY_DESCENT = 24
    FIRE_COOLDOWN = 0.12
    MAX_SIMULTANEOUS_SHOTS = 6
    UPDATE_MS = 30

    def __init__(
        self,
        root: tk.Tk,
        *,
        on_close: Optional[Callable[[], None]] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        self.root = root
        self.on_close = on_close
        self.achievement_manager = achievement_manager

        self.window = tk.Toplevel(root)
        self.window.title("Orbital Defense Simulation")
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        container = ttk.Frame(self.window, style="Panel.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header = ttk.Frame(container, style="Panel.TFrame")
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header,
            text="Orbital Defense: Rapid Fire Protocol",
            style="PanelTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Use ← → to move the turret, Space to unleash rapid-fire laser bolts, Esc to abort.",
            style="PanelCaption.TLabel",
            wraplength=self.WIDTH - 80,
        ).pack(anchor="w", pady=(4, 0))

        self.canvas = tk.Canvas(
            container,
            width=self.WIDTH - 40,
            height=self.HEIGHT - 200,
            bg=ApertureTheme.SECONDARY_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        status_bar = ttk.Frame(container, style="Panel.TFrame")
        status_bar.pack(fill="x", pady=(12, 0))

        self.score_var = tk.StringVar(value="Score: 0")
        self.wave_var = tk.StringVar(value="Wave: 1")
        self.lives_var = tk.StringVar(value="Shields: 3")
        ttk.Label(status_bar, textvariable=self.score_var, style="GLaDOS.TLabel").pack(side="left")
        ttk.Label(status_bar, textvariable=self.wave_var, style="Aperture.TLabel").pack(side="left", padx=(16, 0))
        ttk.Label(status_bar, textvariable=self.lives_var, style="Wheatley.TLabel").pack(side="left", padx=(16, 0))

        ttk.Label(
            container,
            text="Maintain a constant barrage to keep the invaders at bay.",
            style="PanelCaption.TLabel",
        ).pack(anchor="center", pady=(8, 0))

        self.player: Optional[int] = None
        self.aliens: List[Alien] = []
        self.shots: List[Projectile] = []
        self.enemy_shots: List[Projectile] = []
        self.enemy_direction = 1
        self.enemy_speed = self.ENEMY_SPEED_BASE
        self.shot_timer = 0.0
        self.running = True
        self._closed = False
        self.score = 0
        self.wave = 1
        self.lives = 3
        self.aliens_destroyed = 0
        self.start_time = time.time()
        self.after_handle: Optional[str] = None

        self._create_player()
        self._spawn_wave()
        self._schedule_update()

        self.window.bind("<Left>", lambda _: self._move_player(-self.PLAYER_SPEED))
        self.window.bind("<Right>", lambda _: self._move_player(self.PLAYER_SPEED))
        self.window.bind("<space>", self._handle_fire)
        self.window.bind("<Escape>", lambda _: self.close())
        self.window.after(100, self.window.focus_force)

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
        self.running = False
        if self.after_handle is not None:
            try:
                self.window.after_cancel(self.after_handle)
            except Exception:
                pass
            self.after_handle = None
        self._record_session(aborted=True)
        self._closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window.winfo_exists():
            self.window.destroy()

    def _create_player(self) -> None:
        width = 60
        height = 16
        x = (self.canvas.winfo_reqwidth() // 2) - width // 2
        y = self.canvas.winfo_reqheight() - 60
        self.player = self.canvas.create_polygon(
            x,
            y,
            x + width,
            y,
            x + width // 2,
            y - height,
            fill="#33ccff",
            outline="#116688",
            width=2,
        )

    def _spawn_wave(self) -> None:
        for alien in self.aliens:
            self.canvas.delete(alien.item_id)
        self.aliens.clear()
        columns = 8
        rows = 4
        padding_x = 60
        padding_y = 40
        start_x = 40
        start_y = 60
        palette = ["#ff5555", "#ffaa00", "#55dd55", "#66aaff"]
        for row in range(rows):
            for col in range(columns):
                x = start_x + col * padding_x
                y = start_y + row * padding_y
                color = palette[row % len(palette)]
                alien_id = self.canvas.create_oval(
                    x,
                    y,
                    x + 40,
                    y + 30,
                    fill=color,
                    outline="#111111",
                    width=2,
                )
                self.aliens.append(Alien(alien_id, row, col))
        self.enemy_direction = 1
        self.enemy_speed = self.ENEMY_SPEED_BASE + (self.wave - 1) * 0.35
        self.wave_var.set(f"Wave: {self.wave}")

    def _schedule_update(self) -> None:
        if not self.running:
            return
        self.after_handle = self.window.after(self.UPDATE_MS, self._update)

    def _move_player(self, delta_x: int) -> None:
        if not self.player or not self.running:
            return
        min_x = 10
        max_x = self.canvas.winfo_width() - 70
        current_bbox = self.canvas.bbox(self.player)
        if not current_bbox:
            return
        new_x1 = max(min_x, min(current_bbox[0] + delta_x, max_x))
        delta = new_x1 - current_bbox[0]
        self.canvas.move(self.player, delta, 0)

    def _handle_fire(self, _: tk.Event) -> None:
        if not self.running:
            return
        now = time.time()
        if len(self.shots) >= self.MAX_SIMULTANEOUS_SHOTS and now - self.shot_timer < self.FIRE_COOLDOWN:
            return
        if now - self.shot_timer < self.FIRE_COOLDOWN and len(self.shots) >= 3:
            return
        self.shot_timer = now
        self._spawn_player_shot()

    def _spawn_player_shot(self) -> None:
        if not self.player:
            return
        bbox = self.canvas.bbox(self.player)
        if not bbox:
            return
        x_mid = (bbox[0] + bbox[2]) / 2
        y_top = bbox[1]
        shot = self.canvas.create_rectangle(
            x_mid - 4,
            y_top - 16,
            x_mid + 4,
            y_top,
            fill="#ff66ff",
            outline="",
        )
        self.shots.append(Projectile(shot, self.BULLET_SPEED))

    def _spawn_enemy_shot(self) -> None:
        if not self.aliens:
            return
        shooter = random.choice(self.aliens)
        bbox = self.canvas.bbox(shooter.item_id)
        if not bbox:
            return
        shot = self.canvas.create_rectangle(
            (bbox[0] + bbox[2]) / 2 - 3,
            bbox[3],
            (bbox[0] + bbox[2]) / 2 + 3,
            bbox[3] + 18,
            fill="#ffaa33",
            outline="",
        )
        self.enemy_shots.append(Projectile(shot, abs(self.BULLET_SPEED) * 0.6))

    def _update(self) -> None:
        if not self.running:
            return
        self._move_aliens()
        self._maybe_fire_enemy()
        self._move_shots()
        self._check_collisions()
        self._check_enemy_reach()
        self._schedule_update()

    def _move_aliens(self) -> None:
        if not self.aliens:
            return
        bounds = [self.canvas.bbox(alien.item_id) for alien in self.aliens]
        valid_bounds = [b for b in bounds if b is not None]
        if not valid_bounds:
            return
        min_x = min(b[0] for b in valid_bounds)
        max_x = max(b[2] for b in valid_bounds)
        step = self.enemy_direction * self.enemy_speed
        if min_x + step <= 10 or max_x + step >= self.canvas.winfo_width() - 10:
            self.enemy_direction *= -1
            for alien in self.aliens:
                self.canvas.move(alien.item_id, 0, self.ENEMY_DESCENT)
        else:
            for alien in self.aliens:
                self.canvas.move(alien.item_id, step, 0)

    def _maybe_fire_enemy(self) -> None:
        if not self.aliens:
            return
        probability = min(0.06 + self.wave * 0.01, 0.18)
        if random.random() < probability:
            self._spawn_enemy_shot()

    def _move_shots(self) -> None:
        for shot in list(self.shots):
            self.canvas.move(shot.item_id, 0, shot.velocity)
            bbox = self.canvas.bbox(shot.item_id)
            if not bbox or bbox[1] <= -20:
                self.canvas.delete(shot.item_id)
                self.shots.remove(shot)
        for shot in list(self.enemy_shots):
            self.canvas.move(shot.item_id, 0, shot.velocity)
            bbox = self.canvas.bbox(shot.item_id)
            if not bbox or bbox[3] >= self.canvas.winfo_height() + 20:
                self.canvas.delete(shot.item_id)
                self.enemy_shots.remove(shot)

    def _check_collisions(self) -> None:
        for shot in list(self.shots):
            shot_bbox = self.canvas.bbox(shot.item_id)
            if not shot_bbox:
                continue
            overlapping = self.canvas.find_overlapping(*shot_bbox)
            hits = [alien for alien in self.aliens if alien.item_id in overlapping]
            if hits:
                target = hits[0]
                self.canvas.delete(target.item_id)
                self.canvas.delete(shot.item_id)
                self.aliens.remove(target)
                self.shots.remove(shot)
                self.score += 50 + target.row * 20
                self.aliens_destroyed += 1
                self.score_var.set(f"Score: {self.score}")
                if not self.aliens:
                    self.wave += 1
                    self.wave_var.set(f"Wave: {self.wave}")
                    self._spawn_wave()
                break

        if not self.player:
            return
        player_bbox = self.canvas.bbox(self.player)
        if not player_bbox:
            return
        for shot in list(self.enemy_shots):
            bbox = self.canvas.bbox(shot.item_id)
            if not bbox:
                continue
            if self._bbox_intersect(player_bbox, bbox):
                self.canvas.delete(shot.item_id)
                self.enemy_shots.remove(shot)
                self._handle_player_hit()

    def _bbox_intersect(self, a: tuple, b: tuple) -> bool:
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    def _handle_player_hit(self) -> None:
        self.lives -= 1
        self.lives_var.set(f"Shields: {self.lives}")
        self.canvas.itemconfig(self.player, fill="#ff4444")
        self.window.after(120, lambda: self.canvas.itemconfig(self.player, fill="#33ccff"))
        if self.lives <= 0:
            self._game_over()

    def _check_enemy_reach(self) -> None:
        for alien in self.aliens:
            bbox = self.canvas.bbox(alien.item_id)
            if bbox and bbox[3] >= self.canvas.winfo_height() - 80:
                self._game_over()
                return

    def _game_over(self) -> None:
        if not self.running:
            return
        self.running = False
        duration = max(0.0, time.time() - self.start_time)
        self._record_session(aborted=False, duration=duration)
        messagebox.showinfo(
            "Simulation Complete",
            f"Final score: {self.score}\nWaves survived: {self.wave - 1 if self.aliens else self.wave}\nInvaders neutralized: {self.aliens_destroyed}",
            parent=self.window,
        )
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window.winfo_exists():
            self.window.destroy()
        self._closed = True

    def _record_session(self, aborted: bool, duration: Optional[float] = None) -> None:
        if not self.achievement_manager:
            return
        elapsed = duration if duration is not None else max(0.0, time.time() - self.start_time)
        try:
            self.achievement_manager.record_mini_game_session(
                "space_invaders",
                score=self.score,
                lines=self.aliens_destroyed,
                level=self.wave,
                duration=elapsed,
                armor=self.lives,
                aborted=aborted,
            )
        except Exception:
            pass
