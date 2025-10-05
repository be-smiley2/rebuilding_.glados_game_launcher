"""3D DOOM 2016 inspired combat simulation for the launcher.

This module replaces the previous 2D canvas mini-game with a lightweight engine
simulation that mimics a DOOM (2016) combat encounter.  It is intentionally
stylised so it can run entirely within Tkinter while still exposing
engine/asset management, gameplay state, and session statistics that match the
expectations of the launcher.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from .achievements import AchievementManager
from .theme import ApertureTheme


# ---------------------------------------------------------------------------
# Engine level data classes


@dataclass(frozen=True)
class Vector3:
    """Simple 3D vector used for spatial calculations."""

    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, factor: float) -> "Vector3":
        return Vector3(self.x * factor, self.y * factor, self.z * factor)

    def magnitude(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self) -> "Vector3":
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0.0, 0.0, 0.0)
        return self.scale(1 / mag)


@dataclass(frozen=True)
class LevelAsset:
    """Definition for a combat arena."""

    name: str
    environment: str
    description: str


@dataclass(frozen=True)
class WeaponAsset:
    """Definition for a weapon available to the player."""

    name: str
    damage: float
    fire_cooldown: float
    projectile_speed: float
    spread: float
    description: str


@dataclass(frozen=True)
class EnemyAsset:
    """Definition for an enemy archetype."""

    name: str
    health: float
    speed: float
    attack_damage: int
    score_value: int
    description: str


@dataclass
class EngineConfig:
    """Parameters that control the combat simulation."""

    tick_rate: int = 60
    arena_radius: float = 30.0
    player_speed: float = 18.0
    projectile_lifetime: float = 4.0
    spawn_interval: float = 2.5
    spawn_variance: float = 0.65
    max_enemies: int = 8
    max_armor: int = 3

    @property
    def frame_ms(self) -> int:
        return max(8, int(1000 / max(1, self.tick_rate)))


# ---------------------------------------------------------------------------
# Engine implementation


class Doom3DEngine:
    """Minimal engine facade responsible for loading assets."""

    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        self.config = config or EngineConfig()
        self.level: Optional[LevelAsset] = None
        self.weapons: Dict[str, WeaponAsset] = {}
        self.enemies: Dict[str, EnemyAsset] = {}
        self.initialized = False

    def initialize(self) -> None:
        if self.initialized:
            return
        self._load_level()
        self._load_weapons()
        self._load_enemies()
        self.initialized = True

    def shutdown(self) -> None:
        self.initialized = False
        self.level = None
        self.weapons.clear()
        self.enemies.clear()

    # -- Asset loaders -----------------------------------------------------

    def _load_level(self) -> None:
        self.level = LevelAsset(
            name="Mars Foundry",
            environment="Argent Facility",
            description=(
                "Multi-tiered foundry floor with molten slag pits, service gantries, "
                "and demonic altars. Plenty of space for circle strafing."
            ),
        )

    def _load_weapons(self) -> None:
        self.weapons = {
            "combat_shotgun": WeaponAsset(
                name="Combat Shotgun",
                damage=28.0,
                fire_cooldown=0.45,
                projectile_speed=68.0,
                spread=2.4,
                description="Reliable close-range workhorse with tight spread.",
            ),
            "plasma_rifle": WeaponAsset(
                name="Plasma Rifle",
                damage=18.0,
                fire_cooldown=0.18,
                projectile_speed=90.0,
                spread=1.4,
                description="Rapid-fire bolts for suppressing mid-range threats.",
            ),
            "gauss_cannon": WeaponAsset(
                name="Gauss Cannon",
                damage=90.0,
                fire_cooldown=1.2,
                projectile_speed=150.0,
                spread=0.4,
                description="High-energy precision beam best reserved for elites.",
            ),
        }

    def _load_enemies(self) -> None:
        self.enemies = {
            "imp": EnemyAsset(
                name="Imp",
                health=40.0,
                speed=12.0,
                attack_damage=1,
                score_value=80,
                description="Fast, evasive cannon fodder.",
            ),
            "possessed_soldier": EnemyAsset(
                name="Possessed Soldier",
                health=60.0,
                speed=9.0,
                attack_damage=1,
                score_value=120,
                description="Ranged infantry with plasma rifles.",
            ),
            "hell_knight": EnemyAsset(
                name="Hell Knight",
                health=180.0,
                speed=7.5,
                attack_damage=2,
                score_value=260,
                description="Charging bruiser that shatters armor on contact.",
            ),
            "revenant": EnemyAsset(
                name="Revenant",
                health=110.0,
                speed=10.5,
                attack_damage=2,
                score_value=220,
                description="Jetpack skeleton with micro-missiles.",
            ),
        }


# ---------------------------------------------------------------------------
# Gameplay simulation


@dataclass
class EnemyInstance:
    archetype: EnemyAsset
    position: Vector3
    health: float


@dataclass
class Projectile:
    position: Vector3
    direction: Vector3
    speed: float
    damage: float
    time_alive: float = 0.0


@dataclass
class PlayerState:
    position: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    armor: int = 3
    weapon_key: str = "combat_shotgun"


@dataclass
class SessionSnapshot:
    timestamp: float
    score: int
    kills: int
    threat_level: int
    armor: int
    shots_fired: int
    enemies_active: int
    weapon_name: str


@dataclass
class SessionResult:
    score: int
    kills: int
    threat_level: int
    armor_remaining: int
    shots_fired: int
    enemies_spawned: int
    duration: float
    aborted: bool


class Doom3DSession:
    """Gameplay loop independent from the Tkinter UI."""

    def __init__(
        self,
        engine: Doom3DEngine,
        *,
        on_session_end: Optional[Callable[[SessionResult], None]] = None,
    ) -> None:
        self.engine = engine
        self.config = engine.config
        self.on_session_end = on_session_end

        self.player = PlayerState(armor=self.config.max_armor)
        self.enemies: List[EnemyInstance] = []
        self.projectiles: List[Projectile] = []
        self.input_state: Dict[str, bool] = {
            "forward": False,
            "back": False,
            "left": False,
            "right": False,
        }

        self.spawn_timer = self.config.spawn_interval
        self.fire_cooldown = 0.0

        self.score = 0
        self.kills = 0
        self.shots_fired = 0
        self.enemies_spawned = 0
        self.threat_level = 1

        self.running = False
        self._start_time = 0.0
        self._last_snapshot = SessionSnapshot(
            timestamp=time.time(),
            score=0,
            kills=0,
            threat_level=1,
            armor=self.player.armor,
            shots_fired=0,
            enemies_active=0,
            weapon_name=self.current_weapon.name,
        )
        self._final_result: Optional[SessionResult] = None

    # -- Properties -------------------------------------------------------

    @property
    def current_weapon(self) -> WeaponAsset:
        return self.engine.weapons[self.player.weapon_key]

    # -- Public API -------------------------------------------------------

    def start(self) -> None:
        self.running = True
        self._start_time = time.time()
        self.spawn_timer = self.config.spawn_interval
        self.fire_cooldown = 0.0
        self.score = 0
        self.kills = 0
        self.shots_fired = 0
        self.enemies_spawned = 0
        self.threat_level = 1
        self.enemies.clear()
        self.projectiles.clear()
        self.player = PlayerState(armor=self.config.max_armor)
        self._final_result = None

    def stop(self, aborted: bool = True) -> SessionResult:
        if self._final_result is not None:
            return self._final_result

        duration = max(0.0, time.time() - self._start_time)
        self.running = False

        self._final_result = SessionResult(
            score=self.score,
            kills=self.kills,
            threat_level=self.threat_level,
            armor_remaining=self.player.armor,
            shots_fired=self.shots_fired,
            enemies_spawned=self.enemies_spawned,
            duration=duration,
            aborted=aborted,
        )

        if self.on_session_end is not None:
            try:
                self.on_session_end(self._final_result)
            except Exception:
                pass

        return self._final_result

    def set_input(self, action: str, active: bool) -> None:
        if action in self.input_state:
            self.input_state[action] = active

    def fire_weapon(self) -> bool:
        if not self.running:
            return False
        if self.fire_cooldown > 0.0:
            return False

        weapon = self.current_weapon
        forward = Vector3(0.0, 0.0, 1.0)
        spread = weapon.spread
        random_offset = Vector3(
            random.uniform(-spread, spread) * 0.05,
            random.uniform(-spread, spread) * 0.02,
            1.0,
        ).normalized()
        projectile = Projectile(
            position=self.player.position,
            direction=random_offset,
            speed=weapon.projectile_speed,
            damage=weapon.damage,
        )
        self.projectiles.append(projectile)
        self.shots_fired += 1
        self.fire_cooldown = weapon.fire_cooldown
        return True

    def tick(self, delta: float) -> SessionSnapshot:
        if not self.running:
            return self._last_snapshot

        self._update_player(delta)
        self._update_projectiles(delta)
        self._update_enemies(delta)
        self._handle_spawning(delta)

        self.threat_level = max(1, 1 + self.kills // 6)

        snapshot = SessionSnapshot(
            timestamp=time.time(),
            score=self.score,
            kills=self.kills,
            threat_level=self.threat_level,
            armor=self.player.armor,
            shots_fired=self.shots_fired,
            enemies_active=len(self.enemies),
            weapon_name=self.current_weapon.name,
        )
        self._last_snapshot = snapshot
        return snapshot

    # -- Internal updates -------------------------------------------------

    def _update_player(self, delta: float) -> None:
        dx = float(self.input_state["right"]) - float(self.input_state["left"])
        dz = float(self.input_state["forward"]) - float(self.input_state["back"])

        if dx or dz:
            direction = Vector3(dx, 0.0, dz).normalized()
            displacement = direction.scale(self.config.player_speed * delta)
            tentative = self.player.position + displacement
            if tentative.magnitude() > self.config.arena_radius:
                # Clamp player inside the arena radius
                tentative = tentative.normalized().scale(self.config.arena_radius)
            self.player = PlayerState(
                position=tentative,
                armor=self.player.armor,
                weapon_key=self.player.weapon_key,
            )

        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - delta)

    def _update_projectiles(self, delta: float) -> None:
        active: List[Projectile] = []
        for projectile in self.projectiles:
            new_position = projectile.position + projectile.direction.scale(projectile.speed * delta)
            projectile.position = new_position
            projectile.time_alive += delta
            if projectile.time_alive > self.config.projectile_lifetime:
                continue
            active.append(projectile)
        self.projectiles = active

    def _update_enemies(self, delta: float) -> None:
        survivors: List[EnemyInstance] = []
        for enemy in self.enemies:
            direction = (Vector3(0.0, 0.0, 0.0) - enemy.position).normalized()
            displacement = direction.scale(enemy.archetype.speed * delta)
            enemy.position = enemy.position + displacement

            # Projectile collisions
            hit_projectiles: List[Projectile] = []
            for projectile in self.projectiles:
                if abs(projectile.position.x - enemy.position.x) <= 3.5 and projectile.position.z >= enemy.position.z:
                    enemy.health -= projectile.damage
                    hit_projectiles.append(projectile)

            if hit_projectiles:
                self.projectiles = [p for p in self.projectiles if p not in hit_projectiles]

            if enemy.health <= 0:
                self.score += enemy.archetype.score_value + int(self.threat_level * 15)
                self.kills += 1
                continue

            # Player contact
            if enemy.position.magnitude() <= 1.8:
                self.player.armor = max(0, self.player.armor - enemy.archetype.attack_damage)
                if self.player.armor <= 0:
                    self._finalize(aborted=False)
                    return
                continue

            survivors.append(enemy)

        self.enemies = survivors

    def _handle_spawning(self, delta: float) -> None:
        if len(self.enemies) >= self.config.max_enemies:
            return
        self.spawn_timer -= delta
        if self.spawn_timer > 0:
            return

        archetype = random.choice(list(self.engine.enemies.values()))
        spawn_distance = random.uniform(10.0, 26.0)
        angle = random.uniform(0, math.tau)
        position = Vector3(
            math.cos(angle) * spawn_distance,
            0.0,
            max(4.0, spawn_distance * 0.8),
        )
        self.enemies.append(EnemyInstance(archetype=archetype, position=position, health=archetype.health))
        self.enemies_spawned += 1

        interval = max(
            0.6,
            self.config.spawn_interval - self.threat_level * self.config.spawn_variance * 0.4,
        )
        self.spawn_timer = interval

    def _finalize(self, aborted: bool) -> None:
        if self._final_result is not None:
            return
        self.stop(aborted=aborted)


# ---------------------------------------------------------------------------
# Tkinter integration


class Doom3DMiniGame:
    """Tkinter front-end that wires the engine simulation into the launcher."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        on_close: Optional[Callable[[], None]] = None,
        on_snapshot: Optional[Callable[[SessionSnapshot], None]] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        self.root = root
        self.on_close = on_close
        self.on_snapshot = on_snapshot
        self.achievement_manager = achievement_manager

        self.engine = Doom3DEngine()
        self.engine.initialize()

        self.window = tk.Toplevel(root)
        self.window.title("DOOM 2016 Combat Chamber (3D Simulation)")
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.geometry("960x720")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.session = Doom3DSession(self.engine, on_session_end=self._handle_session_end)
        self.session.start()

        self._loop_handle: Optional[str] = None
        self._last_tick = time.perf_counter()
        self._session_recorded = False
        self._closing = False
        self._final_result: Optional[SessionResult] = None

        self._build_interface()
        self.window.after(100, self.window.focus_force)
        self._bind_inputs()
        self._schedule_loop()

    # -- Window lifecycle -------------------------------------------------

    @property
    def is_open(self) -> bool:
        return not self._closing and self.window.winfo_exists()

    def focus(self) -> None:
        if self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True

        if self._loop_handle is not None:
            try:
                self.window.after_cancel(self._loop_handle)
            except Exception:
                pass
            self._loop_handle = None

        aborted = self.session.running and self.session.player.armor > 0
        result = self.session.stop(aborted=aborted)
        self._record_session(result)

        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass

        if self.window.winfo_exists():
            self.window.destroy()

    # -- UI construction --------------------------------------------------

    def _build_interface(self) -> None:
        header = ttk.Frame(self.window, style="Panel.TFrame")
        header.pack(fill="x", padx=24, pady=(24, 12))

        ttk.Label(
            header,
            text="Rip and Tear: Holographic Combat Scenario",
            style="PanelTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            header,
            text=(
                "WASD to move through the arena, space to fire the combat shotgun. "
                "Enemies spawn dynamically using a simplified 3D combat model."
            ),
            style="PanelCaption.TLabel",
            wraplength=860,
        ).pack(anchor="w", pady=(6, 0))

        stats_frame = ttk.Frame(self.window, style="Panel.TFrame")
        stats_frame.pack(fill="x", padx=24, pady=(0, 12))

        self.score_var = tk.StringVar(value="Combat Rating: 0")
        self.kills_var = tk.StringVar(value="Demons Eliminated: 0")
        self.threat_var = tk.StringVar(value="Threat Level: 1")
        self.armor_var = tk.StringVar(value="Armor Integrity: ███")
        self.shots_var = tk.StringVar(value="Shots Fired: 0")
        self.weapon_var = tk.StringVar(value="Weapon: Combat Shotgun")

        ttk.Label(stats_frame, textvariable=self.score_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.kills_var, style="Wheatley.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.threat_var, style="Aperture.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.armor_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.shots_var, style="PanelBody.TLabel").pack(anchor="w")
        ttk.Label(stats_frame, textvariable=self.weapon_var, style="PanelCaption.TLabel").pack(anchor="w")

        assets_frame = ttk.Frame(self.window, style="Panel.TFrame")
        assets_frame.pack(fill="x", padx=24, pady=(0, 12))

        ttk.Label(assets_frame, text="Loaded Combat Assets", style="PanelTitle.TLabel").pack(anchor="w")
        self.assets_text = tk.Text(
            assets_frame,
            height=8,
            wrap="word",
            bg=ApertureTheme.SECONDARY_BG,
            fg=ApertureTheme.TEXT_PRIMARY,
            relief="flat",
        )
        self.assets_text.pack(fill="x", pady=(6, 0))
        self._render_assets()

        control_frame = ttk.Frame(self.window, style="Panel.TFrame")
        control_frame.pack(fill="x", padx=24, pady=(0, 24))

        ttk.Button(
            control_frame,
            text="Abort Simulation",
            style="Aperture.TButton",
            command=self.close,
            width=18,
        ).pack(side="right")

    def _render_assets(self) -> None:
        if not self.assets_text.winfo_exists():
            return
        self.assets_text.configure(state="normal")
        self.assets_text.delete("1.0", "end")

        level = self.engine.level
        if level:
            self.assets_text.insert("end", f"Arena: {level.name} – {level.environment}\n")
            self.assets_text.insert("end", f"  {level.description}\n\n")

        self.assets_text.insert("end", "Weapons Loaded:\n")
        for weapon in self.engine.weapons.values():
            self.assets_text.insert(
                "end",
                f"  • {weapon.name}: {weapon.description} (Damage {weapon.damage}, cooldown {weapon.fire_cooldown:.2f}s)\n",
            )

        self.assets_text.insert("end", "\nDemonic Threat Profiles:\n")
        for enemy in self.engine.enemies.values():
            self.assets_text.insert(
                "end",
                f"  • {enemy.name}: {enemy.description} (HP {enemy.health}, speed {enemy.speed})\n",
            )

        self.assets_text.configure(state="disabled")

    # -- Input handling ---------------------------------------------------

    def _bind_inputs(self) -> None:
        bindings = {
            "<KeyPress-w>": ("forward", True),
            "<KeyRelease-w>": ("forward", False),
            "<KeyPress-s>": ("back", True),
            "<KeyRelease-s>": ("back", False),
            "<KeyPress-a>": ("left", True),
            "<KeyRelease-a>": ("left", False),
            "<KeyPress-d>": ("right", True),
            "<KeyRelease-d>": ("right", False),
        }

        for sequence, (action, active) in bindings.items():
            self.window.bind(sequence, lambda event, a=action, state=active: self.session.set_input(a, state))

        self.window.bind("<space>", lambda event: self.session.fire_weapon())
        self.window.bind("<Escape>", lambda event: self.close())

    # -- Game loop --------------------------------------------------------

    def _schedule_loop(self) -> None:
        if not self.is_open:
            return
        self._loop_handle = self.window.after(self.engine.config.frame_ms, self._run_loop)

    def _run_loop(self) -> None:
        if not self.is_open:
            return

        now = time.perf_counter()
        delta = now - self._last_tick
        self._last_tick = now

        snapshot = self.session.tick(delta)
        self._update_hud(snapshot)

        if self.on_snapshot is not None:
            try:
                self.on_snapshot(snapshot)
            except Exception:
                pass

        if self.session.running:
            self._schedule_loop()

    def _update_hud(self, snapshot: SessionSnapshot) -> None:
        self.score_var.set(f"Combat Rating: {snapshot.score}")
        self.kills_var.set(f"Demons Eliminated: {snapshot.kills}")
        self.threat_var.set(f"Threat Level: {snapshot.threat_level}")
        armor_blocks = "█" * snapshot.armor + "░" * (self.engine.config.max_armor - snapshot.armor)
        self.armor_var.set(f"Armor Integrity: {armor_blocks}")
        self.shots_var.set(f"Shots Fired: {snapshot.shots_fired}")
        self.weapon_var.set(f"Weapon: {snapshot.weapon_name}")

    # -- Session finalisation --------------------------------------------

    def _handle_session_end(self, result: SessionResult) -> None:
        self._final_result = result
        if not result.aborted:
            messagebox.showinfo(
                "Combat Simulation Complete",
                (
                    f"Armor depleted. Final rating {result.score} with {result.kills} demons down.\n"
                    f"Threat level reached {result.threat_level}."
                ),
            )
        self.close()

    def _record_session(self, result: SessionResult) -> None:
        if self._session_recorded or not self.achievement_manager:
            return
        self._session_recorded = True

        unlocked = self.achievement_manager.record_mini_game_session(
            "doom_slayer_training",
            score=result.score,
            lines=result.kills,
            level=result.threat_level,
            duration=result.duration,
            armor=max(result.armor_remaining, 0),
            aborted=result.aborted,
        )

        if unlocked:
            summary = "\n".join(f"• {ach['name']}: {ach['description']}" for ach in unlocked)
            messagebox.showinfo("Mini-Game Achievements", f"New achievements unlocked!\n\n{summary}")


__all__ = [
    "Doom3DEngine",
    "Doom3DSession",
    "Doom3DMiniGame",
    "EngineConfig",
    "SessionSnapshot",
    "SessionResult",
]

