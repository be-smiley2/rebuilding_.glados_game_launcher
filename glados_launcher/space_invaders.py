"""Rapid-fire Space Invaders inspired mini-game for the launcher."""

from __future__ import annotations

import time
from typing import Dict, List, Optional, TYPE_CHECKING

import tkinter as tk
from tkinter import messagebox, ttk

from .theme import ApertureTheme

if TYPE_CHECKING:
    from .achievements import AchievementManager


class RapidFireSpaceInvaders:
    """Lightweight Space Invaders mini-game with rapid fire."""

    WIDTH = 640
    HEIGHT = 480
    HUD_HEIGHT = 60

    PLAYER_WIDTH = 48
    PLAYER_HEIGHT = 16
    PLAYER_SPEED = 8

    BULLET_WIDTH = 4
    BULLET_HEIGHT = 16
    BULLET_SPEED = 14
    RAPID_FIRE_COOLDOWN = 0.15

    INVADER_ROWS = 4
    INVADER_COLS = 8
    INVADER_WIDTH = 36
    INVADER_HEIGHT = 24
    INVADER_HORIZONTAL_PADDING = 20
    INVADER_VERTICAL_PADDING = 24
    INVADER_VERTICAL_STEP = 18
    INVADER_BASE_SPEED = 2.0

    UPDATE_INTERVAL_MS = 30

    def __init__(
        self,
        root: tk.Tk,
        on_close: Optional[callable] = None,
        achievement_manager: Optional["AchievementManager"] = None,
    ) -> None:
        self.root = root
        self.on_close = on_close
        self.achievement_manager = achievement_manager

        self.window = tk.Toplevel(root)
        self.window.title("Rapid Fire Space Invaders")
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        container = ttk.Frame(self.window, style="Panel.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        hud = ttk.Frame(container, style="Panel.TFrame")
        hud.pack(fill="x")

        self.status_var = tk.StringVar(value="Protect the test facility from colorful invaders.")
        self.score_var = tk.StringVar(value="Score: 0")
        self.wave_var = tk.StringVar(value="Wave: 1")

        ttk.Label(hud, textvariable=self.status_var, style="Aperture.TLabel").pack(anchor="w")
        ttk.Label(hud, textvariable=self.score_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(hud, textvariable=self.wave_var, style="Wheatley.TLabel").pack(anchor="w")

        self.canvas = tk.Canvas(
            container,
            width=self.WIDTH,
            height=self.HEIGHT - self.HUD_HEIGHT,
            bg=ApertureTheme.SECONDARY_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, pady=(12, 0))

        ttk.Label(
            container,
            text="Controls: ← → move | Space rapid fire | Esc abort",
            style="Aperture.TLabel",
        ).pack(anchor="center", pady=(10, 0))

        self.player_x = self.WIDTH // 2
        self.player_y = self.HEIGHT - self.HUD_HEIGHT - 30
        self.player = self.canvas.create_polygon(
            self.player_x,
            self.player_y - self.PLAYER_HEIGHT // 2,
            self.player_x - self.PLAYER_WIDTH // 2,
            self.player_y + self.PLAYER_HEIGHT // 2,
            self.player_x + self.PLAYER_WIDTH // 2,
            self.player_y + self.PLAYER_HEIGHT // 2,
            fill="#5ec8ff",
            outline=ApertureTheme.PRIMARY_BG,
        )

        self.left_pressed = False
        self.right_pressed = False
        self.last_shot_time = 0.0

        self.bullets: List[Dict[str, int]] = []
        self.invaders: List[Dict[str, float]] = []
        self.invader_direction = 1
        self.invader_speed = self.INVADER_BASE_SPEED

        self.score = 0
        self.wave = 1
        self.enemies_destroyed = 0
        self.running = True
        self._closed = False
        self.after_handle: Optional[str] = None
        self.start_time = time.time()
        self._session_recorded = False

        self._spawn_wave(first_wave=True)
        self._update_hud()
        self._schedule_tick()

        self.window.bind("<KeyPress-Left>", lambda event: self._set_direction(left=True, pressed=True))
        self.window.bind("<KeyRelease-Left>", lambda event: self._set_direction(left=True, pressed=False))
        self.window.bind("<KeyPress-Right>", lambda event: self._set_direction(right=True, pressed=True))
        self.window.bind("<KeyRelease-Right>", lambda event: self._set_direction(right=True, pressed=False))
        self.window.bind("<KeyPress-a>", lambda event: self._set_direction(left=True, pressed=True))
        self.window.bind("<KeyRelease-a>", lambda event: self._set_direction(left=True, pressed=False))
        self.window.bind("<KeyPress-d>", lambda event: self._set_direction(right=True, pressed=True))
        self.window.bind("<KeyRelease-d>", lambda event: self._set_direction(right=True, pressed=False))
        self.window.bind("<KeyPress-space>", lambda event: self._fire_bullet())
        self.window.bind("<space>", lambda event: self._fire_bullet())
        self.window.bind("<Escape>", lambda event: self.close())
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
        aborted = self.running
        self._record_session(aborted)
        self.running = False
        if self.after_handle is not None:
            try:
                self.window.after_cancel(self.after_handle)
            except Exception:
                pass
            self.after_handle = None
        self._closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window.winfo_exists():
            self.window.destroy()

    # -- Game setup -----------------------------------------------------------------

    def _spawn_wave(self, *, first_wave: bool = False) -> None:
        self.canvas.delete("invader")
        self.invaders.clear()

        horizontal_space = self.WIDTH - 2 * self.INVADER_HORIZONTAL_PADDING
        step_x = horizontal_space / max(self.INVADER_COLS - 1, 1)

        for row in range(self.INVADER_ROWS):
            color = self._color_for_row(row)
            for col in range(self.INVADER_COLS):
                x = self.INVADER_HORIZONTAL_PADDING + col * step_x
                y = 60 + row * (self.INVADER_HEIGHT + self.INVADER_VERTICAL_PADDING)
                invader_id = self.canvas.create_rectangle(
                    x - self.INVADER_WIDTH / 2,
                    y - self.INVADER_HEIGHT / 2,
                    x + self.INVADER_WIDTH / 2,
                    y + self.INVADER_HEIGHT / 2,
                    fill=color,
                    outline=ApertureTheme.PRIMARY_BG,
                    width=2,
                    tags="invader",
                )
                self.invaders.append({"id": invader_id, "x": x, "y": y})

        if not first_wave:
            self.status_var.set(f"Wave {self.wave} engaged. Rapid fire authorized.")

        self.invader_direction = 1
        self.invader_speed = self.INVADER_BASE_SPEED + (self.wave - 1) * 0.4

    def _color_for_row(self, row: int) -> str:
        palette = ["#ff5e5b", "#f7a400", "#8be000", "#5ec8ff", "#aa55ff"]
        return palette[row % len(palette)]

    # -- Input handling -------------------------------------------------------------

    def _set_direction(self, left: bool = False, right: bool = False, pressed: bool = False) -> None:
        if left:
            self.left_pressed = pressed
        if right:
            self.right_pressed = pressed

    def _fire_bullet(self) -> None:
        if not self.running:
            return
        now = time.time()
        if now - self.last_shot_time < self.RAPID_FIRE_COOLDOWN:
            return
        self.last_shot_time = now
        bullet = self.canvas.create_rectangle(
            self.player_x - self.BULLET_WIDTH // 2,
            self.player_y - self.PLAYER_HEIGHT // 2 - self.BULLET_HEIGHT,
            self.player_x + self.BULLET_WIDTH // 2,
            self.player_y - self.PLAYER_HEIGHT // 2,
            fill="#f7a400",
            outline="",
            tags="bullet",
        )
        self.bullets.append({"id": bullet})

    # -- Game loop ------------------------------------------------------------------

    def _schedule_tick(self) -> None:
        if not self.running:
            return
        self.after_handle = self.window.after(self.UPDATE_INTERVAL_MS, self._tick)

    def _tick(self) -> None:
        if not self.running:
            return

        self._update_player()
        self._update_bullets()
        self._update_invaders()
        self._check_collisions()
        self._check_game_state()
        self._update_hud()

        self._schedule_tick()

    def _update_player(self) -> None:
        direction = 0
        if self.left_pressed and not self.right_pressed:
            direction = -1
        elif self.right_pressed and not self.left_pressed:
            direction = 1

        if direction != 0:
            dx = direction * self.PLAYER_SPEED
            new_x = min(
                max(self.player_x + dx, self.PLAYER_WIDTH // 2),
                self.WIDTH - self.PLAYER_WIDTH // 2,
            )
            dx = new_x - self.player_x
            if dx:
                self.player_x = new_x
                self.canvas.move(self.player, dx, 0)

    def _update_bullets(self) -> None:
        remaining: List[Dict[str, int]] = []
        for bullet in self.bullets:
            bullet_id = bullet["id"]
            self.canvas.move(bullet_id, 0, -self.BULLET_SPEED)
            coords = self.canvas.coords(bullet_id)
            if coords and coords[1] > -self.BULLET_HEIGHT:
                remaining.append(bullet)
            else:
                self.canvas.delete(bullet_id)
        self.bullets = remaining

    def _update_invaders(self) -> None:
        if not self.invaders:
            return

        move_x = self.invader_direction * self.invader_speed
        should_drop = False

        for invader in self.invaders:
            next_left = invader["x"] - self.INVADER_WIDTH / 2 + move_x
            next_right = invader["x"] + self.INVADER_WIDTH / 2 + move_x
            if next_left < 0 or next_right > self.WIDTH:
                should_drop = True
                break

        if should_drop:
            self.invader_direction *= -1
            for invader in self.invaders:
                invader["y"] += self.INVADER_VERTICAL_STEP
                self.canvas.move(invader["id"], 0, self.INVADER_VERTICAL_STEP)
        else:
            for invader in self.invaders:
                invader["x"] += move_x
                self.canvas.move(invader["id"], move_x, 0)

    def _check_collisions(self) -> None:
        if not self.invaders:
            return

        bullets_remaining: List[Dict[str, int]] = []
        destroyed_ids: set[int] = set()

        for bullet in self.bullets:
            bullet_id = bullet["id"]
            bullet_box = self.canvas.bbox(bullet_id)
            if not bullet_box:
                continue
            hit_invader: Optional[Dict[str, float]] = None
            for invader in self.invaders:
                invader_id = invader["id"]
                if invader_id in destroyed_ids:
                    continue
                invader_box = self.canvas.bbox(invader_id)
                if invader_box and self._intersects(bullet_box, invader_box):
                    hit_invader = invader
                    break
            if hit_invader:
                invader_id = hit_invader["id"]
                destroyed_ids.add(invader_id)
                self.canvas.delete(invader_id)
                self.canvas.delete(bullet_id)
                self.score += 100 + (self.wave - 1) * 20
                self.enemies_destroyed += 1
            else:
                bullets_remaining.append(bullet)

        self.bullets = bullets_remaining
        if destroyed_ids:
            self.invaders = [inv for inv in self.invaders if inv["id"] not in destroyed_ids]

        if not self.invaders:
            self.wave += 1
            self._spawn_wave()

    def _check_game_state(self) -> None:
        if not self.invaders:
            return

        player_box = self.canvas.bbox(self.player)
        for invader in self.invaders:
            invader_box = self.canvas.bbox(invader["id"])
            if not invader_box:
                continue
            if invader_box[3] >= self.player_y - self.PLAYER_HEIGHT:
                self._game_over()
                return
            if player_box and self._intersects(player_box, invader_box):
                self._game_over()
                return

    def _intersects(self, box_a: List[float], box_b: List[float]) -> bool:
        return not (
            box_a[2] < box_b[0]
            or box_a[0] > box_b[2]
            or box_a[3] < box_b[1]
            or box_a[1] > box_b[3]
        )

    def _update_hud(self) -> None:
        self.score_var.set(f"Score: {self.score}")
        self.wave_var.set(f"Wave: {self.wave}")

    # -- Session tracking -----------------------------------------------------------

    def _game_over(self) -> None:
        if not self.running:
            return
        self.running = False
        self.status_var.set(f"Containment breached! Final score: {self.score}")
        messagebox.showinfo("Rapid Fire Space Invaders", f"Final score: {self.score}")
        self._record_session(aborted=False)
        self.close()

    def _record_session(self, aborted: bool) -> None:
        if self._session_recorded:
            return
        self._session_recorded = True

        if not self.achievement_manager:
            return

        unlocked = self.achievement_manager.record_mini_game_session(
            "space_invaders_rapid_fire",
            score=self.score,
            lines=self.enemies_destroyed,
            level=self.wave,
            duration=time.time() - self.start_time,
            aborted=aborted,
        )

        if unlocked:
            summary = "\n".join(f"• {ach['name']}: {ach['description']}" for ach in unlocked)
            messagebox.showinfo("Mini-Game Achievements", f"New achievements unlocked!\n\n{summary}")


__all__ = ["RapidFireSpaceInvaders"]
