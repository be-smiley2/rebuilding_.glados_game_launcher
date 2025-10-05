"""Persistent storage utilities for the launcher game library."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Tuple

from .config import GAME_DATA_FILE

GameRecord = Dict[str, Any]


class GameDataManager:
    """Handle persistence and simple analytics for the game catalogue."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path or GAME_DATA_FILE
        self._games: Dict[str, GameRecord] = {}
        self.load_game_data()

    # -- Persistence -----------------------------------------------------
    def load_game_data(self) -> None:
        """Load stored game information from disk."""
        self._games = {}
        if not self.storage_path.exists():
            return
        try:
            with self.storage_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            # Corrupt or unreadable file – start with a clean database.
            return

        if not isinstance(data, MutableMapping):
            return

        for raw_game_id, raw_info in data.items():
            if not isinstance(raw_info, MutableMapping):
                continue
            game_id = str(raw_game_id)
            self._games[game_id] = self._coerce_game_record(game_id, dict(raw_info))

    def save_game_data(self) -> None:
        """Persist the current game catalogue to disk."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self.storage_path.open("w", encoding="utf-8") as handle:
                json.dump(self._games, handle, indent=2, ensure_ascii=False)
        except Exception:
            # Persistence errors should not crash the interface – they are logged elsewhere.
            pass

    # -- Game manipulation ------------------------------------------------
    def get_games(self) -> Dict[str, GameRecord]:
        return self._games

    def get_smart_sorted_games(self) -> List[Tuple[str, GameRecord]]:
        """Return games sorted by play frequency, rating and name."""

        def sort_key(item: Tuple[str, GameRecord]) -> Tuple[int, int, str]:
            _, record = item
            play_count = int(record.get("play_count", 0))
            rating = int(record.get("user_rating", 0))
            name = record.get("name", "").lower()
            return (-play_count, -rating, name)

        return sorted(self._games.items(), key=sort_key)

    def update_play_count(self, game_id: str) -> bool:
        record = self._games.get(game_id)
        if not record:
            return False

        record["play_count"] = int(record.get("play_count", 0)) + 1
        record["last_played"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.save_game_data()
        return True

    def add_game(
        self,
        name: str,
        platform: str,
        game_id: str,
        store_url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Register a new game in the catalogue and return its stored ID."""

        for existing_id, record in self._games.items():
            if record.get("name", "").lower() == name.lower() and record.get("platform") == platform:
                return existing_id

        base_id = str(game_id or name or int(time.time()))
        normalized_id = self._ensure_unique_id(base_id.strip().lower().replace(" ", "_"))

        record: GameRecord = {
            "name": name,
            "platform": platform,
            "game_id": game_id,
            "store_url": store_url,
            "protocol_url": metadata.get("protocol_url") if metadata else "",
            "play_count": 0,
            "user_rating": 0,
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }

        if metadata:
            for key, value in metadata.items():
                if key in {"name", "platform"}:
                    continue
                if key == "store_url" and store_url:
                    continue
                record[key] = value

        self._games[normalized_id] = self._coerce_game_record(normalized_id, record)
        self.save_game_data()
        return normalized_id

    def remove_game(self, game_id: str) -> bool:
        if game_id in self._games:
            self._games.pop(game_id)
            self.save_game_data()
            return True
        return False

    def remove_all_games(self) -> bool:
        if not self._games:
            return False
        self._games.clear()
        self.save_game_data()
        return True

    # -- Insights ---------------------------------------------------------
    def get_recommendations(self) -> List[str]:
        games = self._games
        if not games:
            return [
                "No registered subjects. Perform a scan to populate your library.",
                "Use the ADD button to register games manually if scans miss something.",
            ]

        recommendations: List[str] = []

        unplayed = [record for record in games.values() if int(record.get("play_count", 0)) == 0]
        if unplayed:
            sample = sorted(unplayed, key=lambda rec: rec.get("name", "").lower())[:3]
            recommendations.append(
                "Unplayed experiments waiting: "
                + ", ".join(game.get("name", "Unknown") for game in sample)
            )

        high_rated = [
            record for record in games.values() if int(record.get("user_rating", 0)) >= 4
        ]
        if high_rated:
            top = sorted(high_rated, key=lambda rec: int(rec.get("user_rating", 0)), reverse=True)[:3]
            recommendations.append(
                "Favourited subjects to revisit: "
                + ", ".join(f"{game.get('name', 'Unknown')} ({game.get('user_rating', 0)}★)" for game in top)
            )

        recent = sorted(
            games.values(),
            key=lambda rec: rec.get("last_played", ""),
            reverse=True,
        )[:3]
        if recent:
            recommendations.append(
                "Recently evaluated subjects: "
                + ", ".join(game.get("name", "Unknown") for game in recent)
            )

        if not recommendations:
            recommendations.append("Maintain consistent testing schedules to unlock more insights.")

        return recommendations

    # -- Internal helpers -------------------------------------------------
    def _ensure_unique_id(self, base_id: str) -> str:
        candidate = base_id or str(int(time.time()))
        counter = 1
        while candidate in self._games:
            candidate = f"{base_id}-{counter}"
            counter += 1
        return candidate

    def _coerce_game_record(self, game_id: str, record: Dict[str, Any]) -> GameRecord:
        record.setdefault("name", game_id)
        record.setdefault("platform", "unknown")
        record.setdefault("game_id", game_id)
        record.setdefault("store_url", "")
        record.setdefault("protocol_url", "")
        record.setdefault("play_count", 0)
        record.setdefault("user_rating", 0)
        return record


__all__ = ["GameDataManager", "GameRecord"]
