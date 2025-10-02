"""Achievement support utilities."""
from __future__ import annotations

import json
from typing import Dict

from .config import ACHIEVEMENT_CACHE_DIR


class AchievementManager:
    """Manage cached achievement information for detected games."""

    def __init__(self) -> None:
        self.achievement_cache: Dict[str, Dict] = {}
        self.user_achievements: Dict = self.load_user_achievements()

    def load_user_achievements(self) -> Dict:
        try:
            cache_file = ACHIEVEMENT_CACHE_DIR / "user_achievements.json"
            if cache_file.exists():
                with cache_file.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
        except Exception:
            pass
        return {}

    def save_user_achievements(self) -> None:
        try:
            cache_file = ACHIEVEMENT_CACHE_DIR / "user_achievements.json"
            with cache_file.open("w", encoding="utf-8") as handle:
                json.dump(self.user_achievements, handle, indent=2)
        except Exception:
            pass

    def get_game_achievements(self, game_id: str, platform_name: str, game_name: str = "") -> Dict:
        cache_key = f"{platform_name}_{game_id}"
        if cache_key in self.achievement_cache:
            return self.achievement_cache[cache_key]

        achievements = self.fetch_platform_achievements(game_id, platform_name, game_name)
        self.achievement_cache[cache_key] = achievements
        return achievements

    def fetch_platform_achievements(self, game_id: str, platform_name: str, game_name: str = "") -> Dict:
        try:
            if platform_name == "steam":
                return self.fetch_steam_achievements(game_id)
            if platform_name == "epic":
                return self.fetch_epic_achievements(game_id, game_name)
            if platform_name == "ubisoft":
                return self.fetch_ubisoft_achievements(game_id, game_name)
            if platform_name == "gog":
                return self.fetch_gog_achievements(game_id, game_name)
            return {
                "total": 0,
                "unlocked": 0,
                "achievements": [],
                "platform": platform_name,
                "percentage": 0,
            }
        except Exception:
            return {
                "total": 0,
                "unlocked": 0,
                "achievements": [],
                "platform": platform_name,
                "error": True,
                "percentage": 0,
            }

    def fetch_steam_achievements(self, app_id: str) -> Dict:
        try:
            achievements = [
                {"name": "First Steps", "description": "Complete the tutorial", "unlocked": True, "icon": ""},
                {"name": "Explorer", "description": "Discover 10 locations", "unlocked": False, "icon": ""},
                {"name": "Master", "description": "Complete the game", "unlocked": False, "icon": ""},
            ]
            unlocked_count = sum(1 for ach in achievements if ach["unlocked"])
            return {
                "total": len(achievements),
                "unlocked": unlocked_count,
                "percentage": (unlocked_count / len(achievements)) * 100 if achievements else 0,
                "achievements": achievements,
                "platform": "steam",
            }
        except Exception:
            return {"total": 0, "unlocked": 0, "achievements": [], "platform": "steam", "error": True, "percentage": 0}

    def fetch_epic_achievements(self, game_id: str, game_name: str) -> Dict:
        try:
            achievements = [
                {"name": "Epic Start", "description": "Begin your journey", "unlocked": True, "icon": ""},
                {"name": "Champion", "description": "Win 5 matches", "unlocked": False, "icon": ""},
            ]
            unlocked_count = sum(1 for ach in achievements if ach["unlocked"])
            return {
                "total": len(achievements),
                "unlocked": unlocked_count,
                "percentage": (unlocked_count / len(achievements)) * 100 if achievements else 0,
                "achievements": achievements,
                "platform": "epic",
            }
        except Exception:
            return {"total": 0, "unlocked": 0, "achievements": [], "platform": "epic", "error": True, "percentage": 0}

    def fetch_ubisoft_achievements(self, game_id: str, game_name: str) -> Dict:
        try:
            achievements = [
                {"name": "Assassin", "description": "Complete first mission", "unlocked": True, "icon": ""},
                {"name": "Legend", "description": "Reach maximum level", "unlocked": False, "icon": ""},
            ]
            unlocked_count = sum(1 for ach in achievements if ach["unlocked"])
            return {
                "total": len(achievements),
                "unlocked": unlocked_count,
                "percentage": (unlocked_count / len(achievements)) * 100 if achievements else 0,
                "achievements": achievements,
                "platform": "ubisoft",
            }
        except Exception:
            return {"total": 0, "unlocked": 0, "achievements": [], "platform": "ubisoft", "error": True, "percentage": 0}

    def fetch_gog_achievements(self, game_id: str, game_name: str) -> Dict:
        try:
            achievements = [
                {"name": "Adventurer", "description": "Start the adventure", "unlocked": True, "icon": ""},
                {"name": "Completionist", "description": "Achieve 100% completion", "unlocked": False, "icon": ""},
            ]
            unlocked_count = sum(1 for ach in achievements if ach["unlocked"])
            return {
                "total": len(achievements),
                "unlocked": unlocked_count,
                "percentage": (unlocked_count / len(achievements)) * 100 if achievements else 0,
                "achievements": achievements,
                "platform": "gog",
            }
        except Exception:
            return {"total": 0, "unlocked": 0, "achievements": [], "platform": "gog", "error": True, "percentage": 0}

    def get_achievement_summary(self, games: Dict) -> Dict:
        total_games_with_achievements = 0
        total_achievements = 0
        total_unlocked = 0

        for game in games.values():
            achievements = self.get_game_achievements(
                game.get("game_id", ""),
                game.get("platform", ""),
                game.get("name", ""),
            )
            if achievements.get("total", 0) > 0:
                total_games_with_achievements += 1
                total_achievements += achievements["total"]
                total_unlocked += achievements["unlocked"]

        return {
            "games_with_achievements": total_games_with_achievements,
            "total_achievements": total_achievements,
            "total_unlocked": total_unlocked,
            "completion_percentage": (total_unlocked / total_achievements) * 100 if total_achievements > 0 else 0,
        }


__all__ = ["AchievementManager"]
