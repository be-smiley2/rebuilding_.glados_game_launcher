"""Persistent storage for game metadata."""
from __future__ import annotations

import json
import time
from typing import Dict, List, Tuple

from .config import GAME_DATA_FILE


class GameDataManager:
    def __init__(self) -> None:
        self.game_data = self.load_game_data()

    def load_game_data(self) -> Dict:
        try:
            if GAME_DATA_FILE.exists():
                with GAME_DATA_FILE.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
        except Exception:
            pass

        return {
            "version": "2.5",
            "games": {},
            "next_id": 1,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def save_game_data(self) -> None:
        try:
            self.game_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with GAME_DATA_FILE.open("w", encoding="utf-8") as handle:
                json.dump(self.game_data, handle, indent=2)
        except Exception:
            pass

    def add_game(self, name: str, platform_name: str, game_id: str, store_url: str = "", search_data: Dict | None = None) -> int:
        game_number = self.game_data["next_id"]

        self.game_data["games"][str(game_number)] = {
            "name": name,
            "platform": platform_name.lower(),
            "game_id": game_id,
            "store_url": store_url,
            "protocol_url": self.generate_protocol_url(platform_name, game_id),
            "added_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "play_count": 0,
            "last_played": None,
            "search_data": search_data or {},
            "user_rating": 0,
        }

        self.game_data["next_id"] += 1
        self.save_game_data()
        return game_number

    def generate_protocol_url(self, platform_name: str, game_id: str) -> str:
        platform_name = platform_name.lower()
        urls = {
            "steam": f"steam://rungameid/{game_id}",
            "ubisoft": f"uplay://launch/{game_id}",
            "epic": f"com.epicgames.launcher://apps/{game_id}?action=launch",
            "gog": f"goggalaxy://openGameView/{game_id}",
        }
        return urls.get(platform_name, game_id)

    def remove_game(self, game_id: str) -> bool:
        try:
            if game_id in self.game_data["games"]:
                del self.game_data["games"][game_id]
                self.save_game_data()
                return True
        except Exception:
            pass
        return False

    def remove_all_games(self) -> bool:
        try:
            if self.game_data.get("games"):
                self.game_data["games"].clear()
                self.game_data["next_id"] = 1
                self.save_game_data()
            return True
        except Exception:
            return False

    def update_play_count(self, game_id: str) -> None:
        try:
            if game_id in self.game_data["games"]:
                self.game_data["games"][game_id]["play_count"] += 1
                self.game_data["games"][game_id]["last_played"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.save_game_data()
        except Exception:
            pass

    def get_games(self) -> Dict:
        return self.game_data.get("games", {})

    def get_smart_sorted_games(self) -> List[Tuple[str, Dict]]:
        games = self.get_games()
        return sorted(
            games.items(),
            key=lambda item: (
                -(item[1].get("play_count", 0)),
                item[1].get("last_played", "1900-01-01"),
                item[1]["name"].lower(),
            ),
        )

    def get_recommendations(self) -> List[str]:
        games = self.get_games()
        if not games:
            return ["Scan for games to get personalized recommendations!"]

        platform_counts: Dict[str, int] = {}
        for game in games.values():
            platform_name = game["platform"]
            plays = game.get("play_count", 0)
            platform_counts[platform_name] = platform_counts.get(platform_name, 0) + plays

        if platform_counts:
            favorite_platform = max(platform_counts.items(), key=lambda item: item[1])[0]
            platform_recs = {
                "steam": ["Try Portal 2 for puzzle excellence", "Half-Life series for FPS mastery"],
                "epic": ["Check weekly free games", "Try Fortnite for battle royale"],
                "ubisoft": ["Assassin's Creed series", "Far Cry for open world"],
                "gog": ["Classic DRM-free games", "Witcher series available"],
            }
            return platform_recs.get(favorite_platform, ["Explore more games on your platform"])

        return ["Build your gaming profile by playing more games!"]


__all__ = ["GameDataManager"]
