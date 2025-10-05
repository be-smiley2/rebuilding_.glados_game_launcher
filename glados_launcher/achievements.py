"""Achievement support utilities."""
from __future__ import annotations

import json
import time
from typing import Dict, List

from .config import ACHIEVEMENT_CACHE_DIR


class AchievementManager:
    """Manage cached achievement information for detected games."""

    def __init__(self) -> None:
        self.achievement_cache: Dict[str, Dict] = {}
        self.user_achievements: Dict = self.load_user_achievements()

        # Ensure new structures exist for legacy files
        self.user_achievements.setdefault("mini_games", {})

    MINI_GAME_DEFINITIONS = {
        "train_tetris": {
            "title": "Train Yard Simulation",
            "short_title": "Train Yard",
            "description": "Guide test trains with precision placement to keep the yard operational.",
            "launch_label": "Launch Train Yard Simulation",
            "stat_fields": [
                "sessions",
                "best_score",
                "total_lines",
                "highest_level",
                "total_time",
                "last_played",
            ],
            "stats_labels": {
                "sessions": "Simulation Sessions",
                "best_score": "Best Score",
                "total_lines": "Total Lines Cleared",
                "highest_level": "Highest Level Achieved",
                "total_time": "Lab Time Invested",
                "last_played": "Last Attempt",
            },
            "summary_template": "Train Yard – Best score {best_score} | {total_lines} lines cleared | Last attempt {last_played}",
            "summary_empty": "Train Yard – No simulation data recorded.",
            "achievements": [
                {
                    "id": "first_dispatch",
                    "name": "First Dispatch",
                    "description": "Complete a simulation run of Train Yard.",
                },
                {
                    "id": "rail_engineer",
                    "name": "Rail Engineer",
                    "description": "Score at least 1,000 points in a single session.",
                },
                {
                    "id": "line_specialist",
                    "name": "Line Specialist",
                    "description": "Clear a cumulative total of 25 lines.",
                },
                {
                    "id": "impeccable_alignment",
                    "name": "Impeccable Alignment",
                    "description": "Reach level 5 in any session.",
                },
            ],
        },
        "doom_slayer_training": {
            "title": "DOOM 2016 Combat Simulator",
            "short_title": "DOOM 2016",
            "description": "Rip and tear through a demon gauntlet tuned for the launcher interface.",
            "launch_label": "Launch DOOM Simulator",
            "stat_fields": [
                "sessions",
                "best_score",
                "total_lines",
                "highest_level",
                "best_armor",
                "total_time",
                "last_played",
            ],
            "stats_labels": {
                "sessions": "Combat Runs",
                "best_score": "Best Combat Rating",
                "total_lines": "Total Demons Eliminated",
                "highest_level": "Highest Threat Level",
                "best_armor": "Best Armor Remaining",
                "total_time": "Total Time in Arena",
                "last_played": "Last Attempt",
            },
            "stat_defaults": {
                "best_armor": 0,
                "last_armor": 0,
            },
            "summary_template": "DOOM 2016 – Rating {best_score} | {total_lines} demons eliminated | Last attempt {last_played}",
            "summary_empty": "DOOM 2016 – No combat data recorded.",
            "achievements": [
                {
                    "id": "fresh_meat",
                    "name": "Fresh Meat",
                    "description": "Complete a combat simulator run.",
                },
                {
                    "id": "rip_and_tear",
                    "name": "Rip and Tear",
                    "description": "Eliminate 40 demons across all runs.",
                },
                {
                    "id": "untouchable",
                    "name": "Untouchable",
                    "description": "Finish a run without losing all armor.",
                },
                {
                    "id": "doomslayer_rising",
                    "name": "Doomslayer Rising",
                    "description": "Reach threat level 6 in a single run.",
                },
            ],
        },
        "doom_classic_1": {
            "title": "Classic DOOM – Episode I",
            "short_title": "DOOM I",
            "description": "Secure the Phobos outpost during a wave defence simulation inspired by DOOM (1993).",
            "launch_label": "Launch DOOM I Simulation",
            "stat_fields": [
                "sessions",
                "best_score",
                "total_lines",
                "highest_level",
                "best_armor",
                "total_time",
                "last_played",
            ],
            "stats_labels": {
                "sessions": "Deployment Runs",
                "best_score": "Best Score",
                "total_lines": "Total Demons Purged",
                "highest_level": "Highest Threat Tier",
                "best_armor": "Best Suit Integrity",
                "total_time": "Total Time Defending",
                "last_played": "Last Operation",
            },
            "stat_defaults": {
                "best_armor": 0,
                "last_armor": 0,
            },
            "summary_template": "DOOM I – Score {best_score} | {total_lines} demons purged | Last run {last_played}",
            "summary_empty": "DOOM I – No deployment data recorded.",
            "achievements": [
                {
                    "id": "knee_deep",
                    "name": "Knee-Deep",
                    "description": "Complete a Phobos defence run.",
                },
                {
                    "id": "hangar_cleanser",
                    "name": "Hangar Cleanser",
                    "description": "Eliminate 50 demons across all DOOM I runs.",
                },
                {
                    "id": "phobos_guardian",
                    "name": "Phobos Guardian",
                    "description": "Finish a run with at least 2 suit integrity blocks remaining.",
                },
                {
                    "id": "nightmare_protocol",
                    "name": "Nightmare Protocol",
                    "description": "Reach threat tier 7 in a single run.",
                },
            ],
        },
        "doom_classic_2": {
            "title": "Classic DOOM – Episode II",
            "short_title": "DOOM II",
            "description": "Hold the Earth gateway open while fending off a classic DOOM II demon surge.",
            "launch_label": "Launch DOOM II Simulation",
            "stat_fields": [
                "sessions",
                "best_score",
                "total_lines",
                "highest_level",
                "best_armor",
                "total_time",
                "last_played",
            ],
            "stats_labels": {
                "sessions": "Gateway Runs",
                "best_score": "Best Score",
                "total_lines": "Total Fiends Routed",
                "highest_level": "Highest Threat Tier",
                "best_armor": "Best Suit Integrity",
                "total_time": "Total Containment Time",
                "last_played": "Last Containment",
            },
            "stat_defaults": {
                "best_armor": 0,
                "last_armor": 0,
            },
            "summary_template": "DOOM II – Score {best_score} | {total_lines} fiends routed | Last run {last_played}",
            "summary_empty": "DOOM II – No containment data recorded.",
            "achievements": [
                {
                    "id": "entryway_complete",
                    "name": "Entryway Complete",
                    "description": "Finish a DOOM II containment run.",
                },
                {
                    "id": "hell_on_earth",
                    "name": "Hell on Earth",
                    "description": "Rout 75 fiends across all DOOM II runs.",
                },
                {
                    "id": "cybernetic_resilience",
                    "name": "Cybernetic Resilience",
                    "description": "End a run with full suit integrity.",
                },
                {
                    "id": "icon_smasher",
                    "name": "Icon Smasher",
                    "description": "Reach threat tier 8 in a single run.",
                },
            ],
        },
    }

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

    # -- Mini-game achievement support -------------------------------------------------

    def record_mini_game_session(
        self,
        game_key: str,
        *,
        score: int = 0,
        lines: int = 0,
        level: int = 1,
        duration: float = 0.0,
        armor: int = 0,
        aborted: bool = False,
    ) -> List[Dict]:
        """Record a finished mini-game session and update achievements.

        Returns a list of newly unlocked achievements (may be empty).
        """

        definition = self.MINI_GAME_DEFINITIONS.get(game_key)
        if not definition:
            return []

        mini_games = self.user_achievements.setdefault("mini_games", {})
        defaults = {
            "best_score": 0,
            "total_lines": 0,
            "sessions": 0,
            "highest_level": 1,
            "total_time": 0.0,
            "achievements": [],
        }
        defaults.update(definition.get("stat_defaults", {}))

        stats = mini_games.setdefault(game_key, defaults.copy())

        for key, value in defaults.items():
            stats.setdefault(key, value)

        stats["sessions"] = stats.get("sessions", 0) + 1
        stats["best_score"] = max(stats.get("best_score", 0), score)
        stats["total_lines"] = stats.get("total_lines", 0) + lines
        stats["highest_level"] = max(stats.get("highest_level", 1), level)
        stats["total_time"] = stats.get("total_time", 0.0) + max(duration, 0.0)
        stats["best_armor"] = max(stats.get("best_armor", 0), armor)
        stats["last_score"] = score
        stats["last_lines"] = lines
        stats["last_level"] = level
        stats["last_armor"] = armor
        stats["last_played"] = time.time()
        stats["last_aborted"] = aborted

        earned_ids = set(stats.get("achievements", []))
        unlocked: List[Dict] = []

        for achievement in definition.get("achievements", []):
            achievement_id = achievement["id"]
            if achievement_id in earned_ids:
                continue
            if self._mini_game_condition_met(game_key, achievement_id, stats):
                stats.setdefault("achievements", []).append(achievement_id)
                earned_ids.add(achievement_id)
                unlocked.append(achievement)

        # Persist session metadata and any new achievements
        self.save_user_achievements()

        return unlocked

    def _mini_game_condition_met(self, game_key: str, achievement_id: str, stats: Dict) -> bool:
        if game_key == "train_tetris":
            if achievement_id == "first_dispatch":
                return stats.get("sessions", 0) >= 1 and not stats.get("last_aborted", False)
            if achievement_id == "rail_engineer":
                return stats.get("best_score", 0) >= 1000
            if achievement_id == "line_specialist":
                return stats.get("total_lines", 0) >= 25
            if achievement_id == "impeccable_alignment":
                return stats.get("highest_level", 1) >= 5
        if game_key == "doom_slayer_training":
            if achievement_id == "fresh_meat":
                return stats.get("sessions", 0) >= 1 and not stats.get("last_aborted", False)
            if achievement_id == "rip_and_tear":
                return stats.get("total_lines", 0) >= 40
            if achievement_id == "untouchable":
                return stats.get("best_armor", 0) >= 3 and not stats.get("last_aborted", False)
            if achievement_id == "doomslayer_rising":
                return stats.get("highest_level", 1) >= 6
        if game_key == "doom_classic_1":
            if achievement_id == "knee_deep":
                return stats.get("sessions", 0) >= 1 and not stats.get("last_aborted", False)
            if achievement_id == "hangar_cleanser":
                return stats.get("total_lines", 0) >= 50
            if achievement_id == "phobos_guardian":
                return stats.get("best_armor", 0) >= 2 and not stats.get("last_aborted", False)
            if achievement_id == "nightmare_protocol":
                return stats.get("highest_level", 1) >= 7
        if game_key == "doom_classic_2":
            if achievement_id == "entryway_complete":
                return stats.get("sessions", 0) >= 1 and not stats.get("last_aborted", False)
            if achievement_id == "hell_on_earth":
                return stats.get("total_lines", 0) >= 75
            if achievement_id == "cybernetic_resilience":
                return stats.get("best_armor", 0) >= 3 and not stats.get("last_aborted", False)
            if achievement_id == "icon_smasher":
                return stats.get("highest_level", 1) >= 8
        return False

    def get_mini_game_stats(self, game_key: str) -> Dict:
        definition = self.MINI_GAME_DEFINITIONS.get(game_key, {})
        defaults = {
            "best_score": 0,
            "total_lines": 0,
            "sessions": 0,
            "highest_level": 1,
            "total_time": 0.0,
            "achievements": [],
        }
        defaults.update(definition.get("stat_defaults", {}))
        stats = self.user_achievements.setdefault("mini_games", {}).get(game_key, {})
        combined = {**defaults, **stats}
        combined["title"] = definition.get("title", game_key)
        return combined

    def get_mini_game_definition(self, game_key: str) -> Dict:
        return self.MINI_GAME_DEFINITIONS.get(game_key, {})

    def get_mini_game_definitions(self) -> Dict[str, Dict]:
        return self.MINI_GAME_DEFINITIONS

    def format_mini_game_summary(self, game_key: str, stats: Dict) -> str:
        definition = self.get_mini_game_definition(game_key)
        template = definition.get("summary_template")
        empty_template = definition.get("summary_empty", "No simulation data recorded.")

        sessions = stats.get("sessions", 0)
        if sessions <= 0:
            return empty_template

        formatted = stats.copy()
        timestamp = stats.get("last_played")
        if timestamp:
            try:
                formatted["last_played"] = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
            except Exception:
                formatted["last_played"] = "Recently"
        else:
            formatted["last_played"] = "Never"

        if template:
            try:
                return template.format(**formatted)
            except Exception:
                pass

        return (
            f"{definition.get('short_title', game_key)} – "
            f"Best score {formatted.get('best_score', 0)} | "
            f"Runs {sessions}"
        )

    def get_mini_game_achievements(self, game_key: str) -> List[Dict]:
        definition = self.MINI_GAME_DEFINITIONS.get(game_key, {})
        stats = self.get_mini_game_stats(game_key)
        earned_ids = set(stats.get("achievements", []))
        achievements = []
        for achievement in definition.get("achievements", []):
            achievement_copy = achievement.copy()
            achievement_copy["earned"] = achievement["id"] in earned_ids
            achievements.append(achievement_copy)
        return achievements

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
