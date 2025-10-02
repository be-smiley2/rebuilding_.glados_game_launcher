"""Mini-game shown within the launcher."""
from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import messagebox, ttk

from .theme import ApertureTheme


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

    def __init__(self, root: tk.Tk, on_close: Optional[callable] = None):
        self.root = root
        self.on_close = on_close
        self.window = tk.Toplevel(root)
        self.window.title("Train Yard Simulation")
        self.window.configure(bg=ApertureTheme.PRIMARY_BG)
        self.window.geometry("420x720")
        self.window.transient(root)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        container = ttk.Frame(self.window, style="Panel.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        board_width = self.COLS * self.TILE_SIZE
        board_height = self.ROWS * self.TILE_SIZE

        info_frame = ttk.Frame(container, style="Panel.TFrame")
        info_frame.pack(fill="x", pady=(0, 10))

        self.info_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.next_var = tk.StringVar()

        ttk.Label(info_frame, textvariable=self.info_var, style="GLaDOS.TLabel").pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.status_var, style="Aperture.TLabel", wraplength=board_width).pack(anchor="w", pady=(4, 0))
        ttk.Label(info_frame, textvariable=self.next_var, style="Wheatley.TLabel").pack(anchor="w", pady=(4, 0))

        self.canvas = tk.Canvas(
            container,
            width=board_width,
            height=board_height,
            bg=ApertureTheme.SECONDARY_BG,
            highlightthickness=0,
        )
        self.canvas.pack()

        ttk.Label(
            container,
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

        self.next_piece = self._create_piece()
        self.current_piece = self._take_next_piece()
        if not self._valid_position(self.current_piece):
            self._game_over()
        else:
            self._update_labels()
            self._render()
            self._schedule_tick()

        self.window.bind("<Left>", lambda event: self._attempt_move(-1, 0))
        self.window.bind("<Right>", lambda event: self._attempt_move(1, 0))
        self.window.bind("<Down>", lambda event: self._soft_drop())
        self.window.bind("<Up>", lambda event: self._rotate())
        self.window.bind("<space>", lambda event: self._hard_drop())
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
        self.after_handle = self.window.after(interval, self._tick)

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
        self.status_var.set(f"Derailment detected. Final score: {self.score}.")
        self._update_labels()
        messagebox.showinfo("Train Yard Simulation", f"Derailment detected! Final score: {self.score}")
        self.close()


__all__ = ["TrainTetrisGame"]
