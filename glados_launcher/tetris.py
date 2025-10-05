"""Mini-game shown within the launcher."""
from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from .theme import ApertureTheme
from .achievements import AchievementManager


class TrainTetrisGame:
    TILE_SIZE = 24
    COLS = 10
    ROWS = 20
    BASE_DROP_MS = 900
    LEVEL_DROP_DELTA = 60

    PIECES = [
        {
            "name": "Cube",
            "color": "#ff6600",
            "rotations": [
                [(0, 0), (1, 0), (0, 1), (1, 1)],
            ],
        },
        {
            "name": "Line",
            "color": "#00ccff",
            "rotations": [
                [(-1, 0), (0, 0), (1, 0), (2, 0)],
                [(0, -1), (0, 0), (0, 1), (0, 2)],
            ],
        },
        {
            "name": "L-Car",
            "color": "#ffaa00",
            "rotations": [
                [(0, -1), (0, 0), (0, 1), (1, 1)],
                [(-1, 0), (0, 0), (1, 0), (-1, 1)],
                [(0, -1), (1, -1), (0, 0), (0, 1)],
                [(1, 0), (-1, 0), (0, 0), (1, -1)],
            ],
        },
        {
            "name": "J-Car",
            "color": "#ff8800",
            "rotations": [
                [(0, -1), (0, 0), (0, 1), (-1, 1)],
                [(-1, 0), (-1, -1), (0, 0), (1, 0)],
                [(0, -1), (1, -1), (0, 0), (0, 1)],
                [(-1, 0), (0, 0), (1, 0), (1, 1)],
            ],
        },
        {
            "name": "Corner",
            "color": "#4488ff",
            "rotations": [
                [(0, 0), (1, 0), (0, 1), (-1, 0)],
                [(0, -1), (0, 0), (0, 1), (1, 0)],
                [(0, 0), (1, 0), (0, -1), (-1, 0)],
                [(0, -1), (0, 0), (0, 1), (-1, 0)],
            ],
        },
        {
            "name": "S-Cargo",
            "color": "#44cc44",
            "rotations": [
                [(0, 0), (1, 0), (0, 1), (-1, 1)],
                [(0, -1), (0, 0), (1, 0), (1, 1)],
            ],
        },
        {
            "name": "Z-Cargo",
            "color": "#cc5500",
            "rotations": [
                [(0, 0), (-1, 0), (0, 1), (1, 1)],
                [(1, -1), (1, 0), (0, 0), (0, 1)],
            ],
        },
    ]

    def __init__(
        self,
        root: tk.Tk,
        on_close: Optional[callable] = None,
        achievement_manager: Optional[AchievementManager] = None,
        parent: Optional[tk.Widget] = None,
    ):
        self.root = root
        self.parent = parent
        self.on_close = on_close
        self.achievement_manager = achievement_manager
        self.window: Optional[tk.Toplevel] = None
        self._embedded = parent is not None

        if self._embedded:
            host = parent or root
            self.container = ttk.Frame(host, style="Panel.TFrame")
            self.container.pack(fill="both", expand=True, padx=20, pady=20)
        else:
            self.window = tk.Toplevel(root)
            self.window.title("Train Yard Simulation")
            self.window.configure(bg=ApertureTheme.PRIMARY_BG)
            self.window.geometry("420x720")
            self.window.transient(root)
            self.window.protocol("WM_DELETE_WINDOW", self.close)

            self.container = ttk.Frame(self.window, style="Panel.TFrame")
            self.container.pack(fill="both", expand=True, padx=20, pady=20)

        board_width = self.COLS * self.TILE_SIZE
        board_height = self.ROWS * self.TILE_SIZE

        info_frame = ttk.Frame(self.container, style="Panel.TFrame")
        info_frame.pack(fill="x", pady=(0, 10))

        self.info_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.next_var = tk.StringVar()

        ttk.Label(info_frame, textvariable=self.info_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.status_var, style="Aperture.TLabel", wraplength=board_width).pack(anchor="w", pady=(4, 0))
        ttk.Label(info_frame, textvariable=self.next_var, style="Wheatley.TLabel").pack(anchor="w", pady=(4, 0))

        self.canvas = tk.Canvas(
            self.container,
            width=board_width,
            height=board_height,
            bg=ApertureTheme.SECONDARY_BG,
            highlightthickness=0,
            takefocus=True,
        )
        self.canvas.pack()

        ttk.Label(
            self.container,
            text="Controls: ← → move | ↑ rotate | ↓ nudge down | Space hard drop | Esc exit",
            style="Aperture.TLabel",
        ).pack(anchor="center", pady=(10, 0))

        self.board: List[List[Optional[str]]] = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_piece: Optional[Dict[str, Any]] = None
        self.next_piece: Optional[Dict[str, Any]] = None
        self.after_handle: Optional[str] = None
        self.running = True
        self._closed = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self._derailed = False
        self._session_recorded = False
        self.start_time = time.time()

        self.next_piece = self._create_piece()
        self.current_piece = self._take_next_piece()
        if not self._valid_position(self.current_piece):
            self._game_over()
        else:
            self._update_labels()
            self._render()
            self._schedule_tick()

        bindings = {
            "<Left>": lambda _: self._attempt_move(-1, 0),
            "<Right>": lambda _: self._attempt_move(1, 0),
            "<Down>": lambda _: self._soft_drop(),
            "<Up>": lambda _: self._rotate(),
            "<space>": lambda _: self._hard_drop(),
            "<Escape>": lambda _: self.close(),
        }
        for sequence, handler in bindings.items():
            self.canvas.bind(sequence, handler)

        self.canvas.focus_set()
        if self.window is not None:
            self.window.after(100, self.canvas.focus_set)

    @property
    def is_open(self) -> bool:
        if self._closed:
            return False
        if self.window is not None:
            return self.window.winfo_exists()
        return bool(self.container.winfo_exists())

    def focus(self) -> None:
        if self.window is not None:
            if self.window.winfo_exists():
                self.window.deiconify()
                self.window.lift()
                self.window.focus_force()
        if self.canvas.winfo_exists():
            try:
                self.canvas.focus_set()
            except Exception:
                pass

    def close(self) -> None:
        if self._closed:
            return
        aborted = self.running and not self._derailed
        self._record_session(aborted)
        self.running = False
        if self.after_handle is not None:
            try:
                self.root.after_cancel(self.after_handle)
            except Exception:
                pass
            self.after_handle = None
        self._closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception:
                pass
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        elif self.container.winfo_exists():
            self.container.destroy()

    def _create_piece(self) -> Dict[str, Any]:
        shape = random.choice(self.PIECES)
        piece = {
            "shape": shape,
            "rotation": 0,
            "x": self.COLS // 2 - 2,
            "y": 0,
        }
        return self._adjust_spawn(piece)

    def _adjust_spawn(self, piece: Dict[str, Any]) -> Dict[str, Any]:
        coords = piece["shape"]["rotations"][piece["rotation"]]
        min_x = min(x for x, _ in coords)
        max_x = max(x for x, _ in coords)
        if piece["x"] + min_x < 0:
            piece["x"] -= piece["x"] + min_x
        if piece["x"] + max_x >= self.COLS:
            piece["x"] -= (piece["x"] + max_x) - (self.COLS - 1)
        return piece

    def _take_next_piece(self) -> Dict[str, Any]:
        piece = self.next_piece or self._create_piece()
        self.next_piece = self._create_piece()
        self._update_next_label()
        return piece

    def _update_next_label(self) -> None:
        if self.next_piece:
            self.next_var.set(f"Next consist: {self.next_piece['shape']['name']}")
        else:
            self.next_var.set("")

    def _schedule_tick(self) -> None:
        if not self.running:
            return
        interval = max(120, self.BASE_DROP_MS - (self.level - 1) * self.LEVEL_DROP_DELTA)
        self.after_handle = self.root.after(interval, self._tick)

    def _tick(self) -> None:
        if not self.running:
            return
        if self._valid_position(self.current_piece, offset_y=1):
            self.current_piece["y"] += 1
        else:
            self._lock_piece()
            cleared = self._clear_lines()
            if cleared:
                self._handle_line_clear(cleared)
            self.current_piece = self._take_next_piece()
            if not self._valid_position(self.current_piece):
                self._game_over()
                return
            self.status_var.set(f"{self.current_piece['shape']['name']} inbound. Maintain alignment.")
        self._render()
        self._schedule_tick()

    def _attempt_move(self, dx: int, dy: int) -> None:
        if not self.running:
            return
        if self._valid_position(self.current_piece, offset_x=dx, offset_y=dy):
            self.current_piece["x"] += dx
            self.current_piece["y"] += dy
            self._render()

    def _soft_drop(self) -> None:
        if not self.running:
            return
        if self._valid_position(self.current_piece, offset_y=1):
            self.current_piece["y"] += 1
            self.score += 1
            self._render()
            self._update_labels()
        else:
            self._tick()

    def _hard_drop(self) -> None:
        if not self.running:
            return
        distance = 0
        while self._valid_position(self.current_piece, offset_y=1):
            self.current_piece["y"] += 1
            distance += 1
        if distance:
            self.score += 2 * distance
        self._tick()

    def _rotate(self) -> None:
        if not self.running:
            return
        piece = self.current_piece
        shape = piece["shape"]
        next_rotation = (piece["rotation"] + 1) % len(shape["rotations"])
        if self._valid_position(piece, rotation=next_rotation):
            piece["rotation"] = next_rotation
            self._adjust_spawn(piece)
            self._render()

    def _valid_position(self, piece: Dict[str, Any], offset_x: int = 0, offset_y: int = 0, rotation: Optional[int] = None) -> bool:
        rotation = piece["rotation"] if rotation is None else rotation
        for x, y in piece["shape"]["rotations"][rotation]:
            board_x = piece["x"] + offset_x + x
            board_y = piece["y"] + offset_y + y
            if board_x < 0 or board_x >= self.COLS or board_y >= self.ROWS:
                return False
            if board_y >= 0 and self.board[board_y][board_x] is not None:
                return False
        return True

    def _lock_piece(self) -> None:
        for x, y in self._cells(self.current_piece):
            if 0 <= y < self.ROWS and 0 <= x < self.COLS:
                self.board[y][x] = self.current_piece["shape"]["color"]
        self.score += 10
        self._update_labels()

    def _cells(self, piece: Dict[str, Any]) -> List[Tuple[int, int]]:
        coords = []
        for x, y in piece["shape"]["rotations"][piece["rotation"]]:
            coords.append((piece["x"] + x, piece["y"] + y))
        return coords

    def _clear_lines(self) -> int:
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = self.ROWS - len(remaining)
        if cleared:
            new_rows = [[None for _ in range(self.COLS)] for _ in range(cleared)]
            self.board = new_rows + remaining
        return cleared

    def _handle_line_clear(self, cleared: int) -> None:
        self.lines += cleared
        self.level = 1 + self.lines // 8
        line_scores = {1: 100, 2: 300, 3: 700, 4: 1500}
        self.score += line_scores.get(cleared, 1500) * max(1, self.level)
        messages = {
            1: "Platform cleared. Efficiency improving.",
            2: "Double-line dispatch. Trains on schedule.",
            3: "Triple consist alignment achieved!",
            4: "Perfect quad-stack! GLaDOS is almost impressed.",
        }
        self.status_var.set(messages.get(cleared, "Rail network optimized."))
        self._update_labels()

    def _update_labels(self) -> None:
        self.info_var.set(f"Score: {self.score} | Lines: {self.lines} | Level: {self.level}")

    def _render(self) -> None:
        self.canvas.delete("block")
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self._draw_cell(x, y, color)
        if self.current_piece:
            for x, y in self._cells(self.current_piece):
                if y >= 0:
                    self._draw_cell(x, y, self.current_piece["shape"]["color"], outline=ApertureTheme.PRIMARY_BG)

    def _draw_cell(self, x: int, y: int, color: str, outline: Optional[str] = None) -> None:
        x1 = x * self.TILE_SIZE
        y1 = y * self.TILE_SIZE
        x2 = x1 + self.TILE_SIZE
        y2 = y1 + self.TILE_SIZE
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline=outline or ApertureTheme.SECONDARY_BG,
            width=1,
            tags="block",
        )

    def _game_over(self) -> None:
        self.running = False
        self._derailed = True
        self.status_var.set(f"Derailment detected. Final score: {self.score}.")
        self._update_labels()
        messagebox.showinfo("Train Yard Simulation", f"Derailment detected! Final score: {self.score}")
        self.close()

    def _record_session(self, aborted: bool) -> None:
        if self._session_recorded:
            return
        self._session_recorded = True

        if not self.achievement_manager:
            return

        unlocked = self.achievement_manager.record_mini_game_session(
            "train_tetris",
            score=self.score,
            lines=self.lines,
            level=self.level,
            duration=time.time() - self.start_time,
            aborted=aborted,
        )

        if unlocked:
            summary = "\n".join(f"• {ach['name']}: {ach['description']}" for ach in unlocked)
            messagebox.showinfo("Mini-Game Achievements", f"New achievements unlocked!\n\n{summary}")


__all__ = ["TrainTetrisGame"]
