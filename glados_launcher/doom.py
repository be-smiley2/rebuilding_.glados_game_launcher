"""pyglet-powered DOOM 2016 inspired mini-game."""
from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from .achievements import AchievementManager
from .dependencies import ensure_pyglet
from .theme import ApertureTheme

PYGLET_AVAILABLE = ensure_pyglet(auto_install=True)

if PYGLET_AVAILABLE:  # pragma: no cover - requires OpenGL context
    import pyglet
    from pyglet import gl
    from pyglet.gl import glu
    from pyglet.window import key, mouse
else:  # pragma: no cover - executed when pyglet is missing
    pyglet = None  # type: ignore
    gl = None  # type: ignore
    glu = None  # type: ignore
    key = None  # type: ignore
    mouse = None  # type: ignore


@dataclass
class Vector3:
    """Simple 3D vector helper."""

    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Vector3":
        magnitude = self.length()
        if magnitude <= 0.0001:
            return Vector3(0.0, 0.0, 0.0)
        return self * (1.0 / magnitude)


@dataclass
class Projectile:
    position: Vector3
    velocity: Vector3
    life: float = 0.0
    radius: float = 1.2


@dataclass
class Demon:
    position: Vector3
    velocity: Vector3
    radius: float
    color: tuple
    health: int = 1


@dataclass
class Player:
    position: Vector3
    yaw: float = 0.0
    armor: int = 3
    radius: float = 2.4
    speed: float = 22.0


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


class Doom3DEngineSession:
    """Encapsulates the pyglet rendering and gameplay loop."""

    WINDOW_WIDTH = 960
    WINDOW_HEIGHT = 600
    ARENA_RADIUS = 85.0
    FIRE_COOLDOWN = 0.18
    PROJECTILE_LIFETIME = 3.0
    PROJECTILE_SPEED = 90.0
    DEMON_BASE_SPEED = 12.0
    DEMON_SPAWN_INTERVAL = 3.0
    THREAT_INCREMENT_KILLS = 5
    MAX_ARMOR = 3

    def __init__(self) -> None:
        if not PYGLET_AVAILABLE:  # pragma: no cover - guard for optional dependency
            raise RuntimeError("pyglet is required for the DOOM simulator.")

        self._thread = threading.Thread(target=self._run, name="Doom3DEngine", daemon=True)
        self._stats_lock = threading.Lock()
        self._latest_stats: Dict[str, float] = {}
        self._finished = threading.Event()
        self._stop_requested = threading.Event()
        self._aborted = False
        self._startup_exception: Optional[Exception] = None

        # gameplay state
        self.player = Player(position=Vector3(0.0, 4.0, 0.0), armor=self.MAX_ARMOR)
        self.projectiles: List[Projectile] = []
        self.demons: List[Demon] = []
        self._kills = 0
        self._score = 0
        self._combo = 1
        self._max_combo = 1
        self._threat_level = 1
        self._spawn_timer = 0.0
        self._time_since_fire = 0.0
        self._session_start = time.time()
        self._shots_fired = 0
        self._shots_hit = 0
        self._fire_button = False
        self._pending_mouse_dx = 0.0

        # runtime handles filled in the render thread
        self._window: Optional["pyglet.window.Window"] = None
        self._key_handler: Optional["key.KeyStateHandler"] = None
        self._hud_labels: Dict[str, "pyglet.text.Label"] = {}

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        self._thread.start()
        # give the thread a moment to fail fast if there is a GL issue
        time.sleep(0.05)
        if self._startup_exception:
            raise self._startup_exception

    def request_stop(self, *, abort: bool = False) -> None:
        if abort:
            self._aborted = True
        self._stop_requested.set()

    def join(self, timeout: Optional[float] = None) -> None:
        self._thread.join(timeout=timeout)

    @property
    def finished(self) -> bool:
        return self._finished.is_set()

    @property
    def aborted(self) -> bool:
        return self._aborted

    def get_stats(self) -> Dict[str, float]:
        with self._stats_lock:
            return dict(self._latest_stats)

    # -- engine thread -----------------------------------------------------
    def _run(self) -> None:  # pragma: no cover - requires an OpenGL context
        try:
            config = pyglet.gl.Config(double_buffer=True, depth_size=24)
            self._window = pyglet.window.Window(
                self.WINDOW_WIDTH,
                self.WINDOW_HEIGHT,
                "DOOM 2016 Combat Simulator",
                resizable=False,
                config=config,
            )
            self._key_handler = key.KeyStateHandler()
            self._window.push_handlers(self._key_handler)
            self._window.event(self._on_draw)
            self._window.event(self._on_close)
            self._window.event(self._on_key_press)
            self._window.event(self._on_mouse_motion)
            self._window.event(self._on_mouse_press)
            self._window.event(self._on_mouse_release)
            try:
                self._window.set_exclusive_mouse(True)
            except Exception:
                pass

            pyglet.clock.schedule_interval(self._update, 1 / 120.0)
            pyglet.clock.schedule_interval(self._push_stats, 1 / 10.0)

            self._hud_labels = {
                "score": pyglet.text.Label(
                    "", font_size=12, x=10, y=self.WINDOW_HEIGHT - 10, anchor_x="left", anchor_y="top"
                ),
                "status": pyglet.text.Label(
                    "",
                    font_size=11,
                    x=10,
                    y=10,
                    anchor_x="left",
                    anchor_y="bottom",
                    color=(220, 220, 220, 255),
                ),
            }

            pyglet.app.run()
        except Exception as exc:  # pragma: no cover - defensive
            self._startup_exception = exc
        finally:
            self._finished.set()
            with self._stats_lock:
                stats = dict(self._latest_stats)
                stats.setdefault("duration", time.time() - self._session_start)
                stats.setdefault("score", self._score)
                stats.setdefault("kills", self._kills)
                stats.setdefault("threat", self._threat_level)
                stats.setdefault("armor", self.player.armor)
                stats.setdefault("aborted", self._aborted)
                stats.setdefault("shots_fired", self._shots_fired)
                stats.setdefault("shots_hit", self._shots_hit)
                stats.setdefault("max_combo", self._max_combo)
                stats.setdefault("combo", self._combo)
                self._latest_stats = stats

    # -- pyglet callbacks --------------------------------------------------
    def _on_draw(self) -> None:
        if not self._window:
            return
        self._window.clear()

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glClearColor(0.05, 0.05, 0.08, 1.0)
        gl.glViewport(0, 0, self._window.width, self._window.height)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(78.0, self._window.width / self._window.height, 0.1, 200.0)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        camera_offset = Vector3(
            math.sin(self.player.yaw) * -12.0,
            6.5,
            math.cos(self.player.yaw) * -12.0,
        )
        eye = self.player.position + camera_offset
        center = self.player.position + Vector3(math.sin(self.player.yaw), -0.4, math.cos(self.player.yaw)) * 6.0
        glu.gluLookAt(eye.x, eye.y, eye.z, center.x, center.y, center.z, 0.0, 1.0, 0.0)

        self._draw_floor()
        self._draw_player()
        self._draw_demons()
        self._draw_projectiles()

        # HUD
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluOrtho2D(0, self._window.width, 0, self._window.height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        score_label = self._hud_labels.get("score")
        status_label = self._hud_labels.get("status")
        if score_label:
            stats = self.get_stats()
            score_label.text = (
                f"Rating: {int(stats.get('score', self._score))} | "
                f"Kills: {int(stats.get('kills', self._kills))} | "
                f"Threat: {int(stats.get('threat', self._threat_level))}"
            )
            score_label.draw()
        if status_label:
            armor_blocks = max(0, int(self.player.armor))
            bar = "█" * armor_blocks + "░" * (self.MAX_ARMOR - armor_blocks)
            status_label.text = (
                f"Armor {bar}  |  Combo x{self._combo} (max x{self._max_combo})"
                f"  |  Shots {self._shots_hit}/{self._shots_fired}"
            )
            status_label.draw()

    def _on_close(self) -> None:
        self.request_stop(abort=True)
        pyglet.app.exit()

    def _on_key_press(self, symbol: int, modifiers: int) -> None:
        if symbol == key.ESCAPE:
            self.request_stop(abort=True)
            pyglet.app.exit()

    def _on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == mouse.LEFT:
            self._fire_button = True

    def _on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> None:
        if button == mouse.LEFT:
            self._fire_button = False

    def _on_mouse_motion(self, x: int, y: int, dx: float, dy: float) -> None:
        self._pending_mouse_dx += dx

    # -- drawing -----------------------------------------------------------
    def _draw_floor(self) -> None:
        gl.glColor3f(0.12, 0.12, 0.16)
        gl.glBegin(gl.GL_QUADS)
        gl.glVertex3f(-120.0, 0.0, -120.0)
        gl.glVertex3f(120.0, 0.0, -120.0)
        gl.glVertex3f(120.0, 0.0, 120.0)
        gl.glVertex3f(-120.0, 0.0, 120.0)
        gl.glEnd()

        gl.glColor3f(0.2, 0.2, 0.24)
        gl.glBegin(gl.GL_LINES)
        step = 10
        for axis in range(-12, 13):
            gl.glVertex3f(axis * step, 0.01, -120.0)
            gl.glVertex3f(axis * step, 0.01, 120.0)
            gl.glVertex3f(-120.0, 0.01, axis * step)
            gl.glVertex3f(120.0, 0.01, axis * step)
        gl.glEnd()

    def _draw_cube(self, position: Vector3, size: float, color: tuple) -> None:
        gl.glPushMatrix()
        gl.glTranslatef(position.x, position.y, position.z)
        gl.glScalef(size, size, size)
        r, g, b = color
        gl.glColor3f(r, g, b)

        vertices = (
            -1,
            -1,
            -1,
            1,
            -1,
            -1,
            1,
            1,
            -1,
            -1,
            1,
            -1,
            -1,
            -1,
            1,
            1,
            -1,
            1,
            1,
            1,
            1,
            -1,
            1,
            1,
        )
        indices = (
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            0,
            4,
            7,
            3,
            1,
            5,
            6,
            2,
            3,
            2,
            6,
            7,
            0,
            1,
            5,
            4,
        )

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        vertex_data = (gl.GLfloat * len(vertices))(*vertices)
        index_data = (gl.GLubyte * len(indices))(*indices)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertex_data)
        gl.glDrawElements(gl.GL_QUADS, len(indices), gl.GL_UNSIGNED_BYTE, index_data)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glPopMatrix()

    def _draw_player(self) -> None:
        self._draw_cube(self.player.position + Vector3(0.0, 2.5, 0.0), 1.6, (0.8, 0.2, 0.2))

    def _draw_demons(self) -> None:
        for demon in self.demons:
            self._draw_cube(demon.position + Vector3(0.0, 2.2, 0.0), demon.radius, demon.color)

    def _draw_projectiles(self) -> None:
        for projectile in self.projectiles:
            self._draw_cube(projectile.position + Vector3(0.0, 2.0, 0.0), projectile.radius * 0.6, (0.95, 0.8, 0.2))

    # -- update loop -------------------------------------------------------
    def _update(self, dt: float) -> None:
        if self._stop_requested.is_set():
            pyglet.app.exit()
            return

        if not self._key_handler:
            return

        self._time_since_fire += dt
        self._spawn_timer += dt

        self._update_player(dt)
        self._update_projectiles(dt)
        self._update_demons(dt)
        self._spawn_demons()

        if self.player.armor <= 0 and not self._aborted:
            self._aborted = False
            self._stop_requested.set()
            pyglet.clock.schedule_once(lambda _dt: pyglet.app.exit(), 0.05)

    def _update_player(self, dt: float) -> None:
        assert self._key_handler is not None
        move_direction = Vector3(0.0, 0.0, 0.0)

        if self._key_handler[key.W] or self._key_handler[key.UP]:
            move_direction.z -= 1
        if self._key_handler[key.S] or self._key_handler[key.DOWN]:
            move_direction.z += 1
        if self._key_handler[key.A] or self._key_handler[key.LEFT]:
            move_direction.x -= 1
        if self._key_handler[key.D] or self._key_handler[key.RIGHT]:
            move_direction.x += 1

        if move_direction.length() > 0.0:
            move_direction = move_direction.normalized()
            sin_yaw = math.sin(self.player.yaw)
            cos_yaw = math.cos(self.player.yaw)
            world_direction = Vector3(
                move_direction.x * cos_yaw - move_direction.z * sin_yaw,
                0.0,
                move_direction.x * sin_yaw + move_direction.z * cos_yaw,
            )
            new_position = self.player.position + world_direction * self.player.speed * dt
            distance = Vector3(new_position.x, 0.0, new_position.z).length()
            if distance <= self.ARENA_RADIUS:
                self.player.position = new_position

        mouse_dx = self._pending_mouse_dx
        self._pending_mouse_dx = 0.0
        self.player.yaw += mouse_dx * 0.0035

        if self._fire_button or self._key_handler[key.SPACE]:
            self._try_fire()

    def _try_fire(self) -> None:
        if self._time_since_fire < self.FIRE_COOLDOWN:
            return
        self._time_since_fire = 0.0
        self._shots_fired += 1

        forward = Vector3(math.sin(self.player.yaw), 0.0, math.cos(self.player.yaw))
        spawn_pos = self.player.position + forward * 4.0
        projectile = Projectile(position=spawn_pos, velocity=forward * self.PROJECTILE_SPEED)
        self.projectiles.append(projectile)

    def _update_projectiles(self, dt: float) -> None:
        alive: List[Projectile] = []
        for projectile in self.projectiles:
            projectile.life += dt
            projectile.position = projectile.position + projectile.velocity * dt
            if projectile.life <= self.PROJECTILE_LIFETIME:
                alive.append(projectile)
        self.projectiles = alive

    def _update_demons(self, dt: float) -> None:
        alive: List[Demon] = []
        for demon in self.demons:
            direction = (self.player.position - demon.position).normalized()
            demon.position = demon.position + direction * demon.velocity.length() * dt
            if (self.player.position - demon.position).length() <= (self.player.radius + demon.radius):
                self.player.armor -= 1
                self._combo = 1
                continue

            hit = False
            for projectile in list(self.projectiles):
                if (projectile.position - demon.position).length() <= (projectile.radius + demon.radius):
                    hit = True
                    self.projectiles.remove(projectile)
                    break
            if hit:
                self._shots_hit += 1
                self._kills += 1
                self._combo += 1
                self._max_combo = max(self._max_combo, self._combo)
                demon.health -= 1
                self._score += 120 + int(10 * self._threat_level * self._combo)
                if self._kills % self.THREAT_INCREMENT_KILLS == 0:
                    self._threat_level += 1
                if demon.health > 0:
                    alive.append(demon)
                continue

            alive.append(demon)
        self.demons = alive

    def _spawn_demons(self) -> None:
        spawn_interval = max(0.8, self.DEMON_SPAWN_INTERVAL - self._threat_level * 0.2)
        if self._spawn_timer < spawn_interval:
            return
        self._spawn_timer = 0.0

        angle = random.uniform(0, math.pi * 2)
        distance = self.ARENA_RADIUS - 5
        spawn_pos = Vector3(math.cos(angle) * distance, 4.0, math.sin(angle) * distance)
        speed_multiplier = 1.0 + self._threat_level * 0.15
        velocity = (self.player.position - spawn_pos).normalized() * (self.DEMON_BASE_SPEED * speed_multiplier)
        demon = Demon(
            position=spawn_pos,
            velocity=velocity,
            radius=2.0 + random.uniform(-0.5, 0.8),
            color=(0.7 + random.random() * 0.2, 0.25, 0.25),
            health=1 + self._threat_level // 4,
        )
        self.demons.append(demon)

    def _push_stats(self, dt: float) -> None:
        with self._stats_lock:
            duration = time.time() - self._session_start
            accuracy = 0.0
            if self._shots_fired:
                accuracy = self._shots_hit / float(self._shots_fired)
            self._latest_stats = {
                "score": float(self._score),
                "kills": float(self._kills),
                "threat": float(self._threat_level),
                "armor": float(self.player.armor),
                "combo": float(self._combo),
                "max_combo": float(self._max_combo),
                "duration": float(duration),
                "shots_fired": float(self._shots_fired),
                "shots_hit": float(self._shots_hit),
                "accuracy": accuracy,
                "aborted": self._aborted,
            }


class Doom2016MiniGame:
    """Tkinter wrapper around the pyglet 3D combat simulator."""

    POLL_INTERVAL_MS = 120

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
        self.window.geometry("520x420")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.score_var = tk.StringVar(value="Combat Rating: 0")
        self.kills_var = tk.StringVar(value="Demons Eliminated: 0")
        self.threat_var = tk.StringVar(value="Threat Level: 1")
        self.armor_var = tk.StringVar(value="Armor Integrity: ███")
        self.combo_var = tk.StringVar(value="Current Combo: x1")
        self.time_var = tk.StringVar(value="Simulation Time: 0.0s")
        self.status_var = tk.StringVar(value="Initializing combat simulator...")

        header = ttk.Frame(self.window, style="Panel.TFrame")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ttk.Label(header, text="Rip and Tear Training Protocol", style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text=(
                "A lightweight recreation of DOOM (2016) combat loops. "
                "WASD/arrow keys move, mouse to aim, left click or space to fire. ESC exits."
            ),
            wraplength=460,
            style="PanelCaption.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        stats_frame = ttk.Frame(self.window, style="Panel.TFrame")
        stats_frame.pack(fill="x", padx=20, pady=(0, 12))
        ttk.Label(stats_frame, textvariable=self.score_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.kills_var, style="Wheatley.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.threat_var, style="Aperture.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.armor_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.combo_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.time_var, style="PanelCaption.TLabel").pack(anchor="w")

        ttk.Label(
            self.window,
            textvariable=self.status_var,
            wraplength=460,
            style="PanelCaption.TLabel",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        control_frame = ttk.Frame(self.window, style="Panel.TFrame")
        control_frame.pack(fill="x", padx=20, pady=(0, 20))
        ttk.Button(control_frame, text="End Simulation", style="Aperture.TButton", command=self.close).pack(anchor="e")

        self._closed = False
        self._session_recorded = False
        self._final_stats: Optional[Dict[str, float]] = None
        self._last_stats: Dict[str, float] = {}
        self._engine: Optional[Doom3DEngineSession] = None
        self.running = False
        self.start_time = time.time()

        if not PYGLET_AVAILABLE:
            messagebox.showwarning(
                "Dependency Missing",
                "The pyglet package is required to run the 3D simulator.\n"
                "Install it with 'pip install pyglet' or\n"
                "'python -m pip install -r requirements-3d.txt' and relaunch the mini-game.",
            )
            self.status_var.set("Simulator unavailable: pyglet package not installed.")
            self.window.after(100, self.close)
            return

        try:
            self._engine = Doom3DEngineSession()
            self._engine.start()
            self.running = True
            self.status_var.set("Arena online. A separate window has been opened for combat training.")
            self._schedule_poll()
        except Exception as exc:  # pragma: no cover - defensive
            messagebox.showerror("Simulator Error", f"Failed to start 3D engine: {exc}")
            self.status_var.set("Simulator unavailable due to initialization error.")
            self.window.after(100, self.close)

    # -- public API --------------------------------------------------------
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

        self._closed = True
        aborted = True
        if self._engine and self._engine.finished:
            aborted = self._engine.aborted

        if not self._session_recorded and self.achievement_manager:
            if not self._final_stats:
                snapshot = dict(self._last_stats)
                if "duration" not in snapshot:
                    snapshot["duration"] = time.time() - self.start_time
                snapshot.setdefault("score", 0)
                snapshot.setdefault("kills", 0)
                snapshot.setdefault("threat", 1)
                snapshot.setdefault("armor", Doom3DEngineSession.MAX_ARMOR)
                snapshot["aborted"] = aborted
                self._final_stats = snapshot
            self._record_session(aborted=aborted)
        if self._engine:
            self._engine.request_stop(abort=aborted)
        try:
            if self.window.winfo_exists():
                self.window.destroy()
        except Exception:
            pass

        if self._engine:
            self._engine.join(timeout=2.0)
        if self.on_close:
            self.on_close()

    # -- internal helpers --------------------------------------------------
    def _schedule_poll(self) -> None:
        if not self._closed and self.window.winfo_exists():
            self.window.after(self.POLL_INTERVAL_MS, self._poll_engine)

    def _poll_engine(self) -> None:
        if self._closed or not self._engine:
            return

        stats = self._engine.get_stats()
        if stats:
            self._last_stats = stats
            self._update_hud(stats)

        if self._engine.finished:
            self._finalize_session()
            return

        self._schedule_poll()

    def _update_hud(self, stats: Dict[str, float]) -> None:
        score = int(stats.get("score", 0))
        kills = int(stats.get("kills", 0))
        threat = int(stats.get("threat", 1))
        armor = int(_clamp(stats.get("armor", 0), 0, Doom3DEngineSession.MAX_ARMOR))
        combo = int(max(1, stats.get("combo", 1)))
        duration = stats.get("duration", 0.0)

        armor_blocks = "█" * armor + "░" * (Doom3DEngineSession.MAX_ARMOR - armor)
        self.score_var.set(f"Combat Rating: {score}")
        self.kills_var.set(f"Demons Eliminated: {kills}")
        self.threat_var.set(f"Threat Level: {threat}")
        self.armor_var.set(f"Armor Integrity: {armor_blocks}")
        self.combo_var.set(f"Current Combo: x{combo}")
        self.time_var.set(f"Simulation Time: {duration:.1f}s")

    def _finalize_session(self) -> None:
        if self._final_stats is not None:
            return

        stats = self._last_stats or {}
        stats.setdefault("duration", time.time() - self.start_time)
        stats.setdefault("score", 0)
        stats.setdefault("kills", 0)
        stats.setdefault("threat", 1)
        stats.setdefault("armor", Doom3DEngineSession.MAX_ARMOR)
        stats.setdefault("aborted", True)

        self._final_stats = stats
        self.running = False

        aborted = bool(stats.get("aborted", False))
        if aborted:
            self.status_var.set("Simulation aborted. Session stats recorded where possible.")
        else:
            self.status_var.set("Simulation complete. Preparing debrief...")
            messagebox.showinfo(
                "Combat Simulator",
                (
                    f"Final rating {int(stats['score'])} with {int(stats['kills'])} demons eliminated.\n"
                    f"Peak threat level {int(stats['threat'])} and combo x{int(stats.get('max_combo', 1))}."
                ),
            )

        self._record_session(aborted=aborted)
        self.close()

    def _record_session(self, aborted: bool) -> None:
        if self._session_recorded or not self.achievement_manager:
            return
        self._session_recorded = True

        stats = self._final_stats or self._last_stats or {}
        duration = float(stats.get("duration", 0.0))
        score = int(stats.get("score", 0))
        kills = int(stats.get("kills", 0))
        threat = int(stats.get("threat", 1))
        armor = int(_clamp(stats.get("armor", 0), 0, Doom3DEngineSession.MAX_ARMOR))

        unlocked = self.achievement_manager.record_mini_game_session(
            "doom_slayer_training",
            score=score,
            lines=kills,
            level=threat,
            duration=duration,
            armor=armor,
            aborted=aborted,
        )

        if unlocked:
            summary = "\n".join(f"• {ach['name']}: {ach['description']}" for ach in unlocked)
            messagebox.showinfo("Mini-Game Achievements", f"New achievements unlocked!\n\n{summary}")


__all__ = ["Doom2016MiniGame"]
