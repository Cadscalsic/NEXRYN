"""Memory for arena competition outcomes."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter, defaultdict
from typing import Any, Mapping


class ArenaMemory:
    """Store arena outcomes without automatically promoting source weights."""

    system_name = "arena_memory"

    def __init__(self):
        self.competitions: list[dict[str, Any]] = []

    def record_competition(self, report: Mapping[str, Any]) -> dict[str, Any]:
        record = deepcopy(dict(report))
        self.competitions.append(record)
        return {
            "system": self.system_name,
            "arena_memory_operational": True,
            "competition_count": len(self.competitions),
        }

    def retrieve_similar_competitions(self, task_signature: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        if not task_signature:
            return [deepcopy(item) for item in self.competitions[-limit:]]
        matches = [
            item for item in self.competitions
            if item.get("task_signature") == task_signature
        ]
        return [deepcopy(item) for item in matches[-limit:]]

    def get_source_statistics(self) -> dict[str, Any]:
        winners = Counter()
        entrants = Counter()
        for competition in self.competitions:
            winner = competition.get("winner_source")
            if winner:
                winners[winner] += 1
            for source in competition.get("sources_entered", []) or []:
                entrants[source] += 1
        return {"wins": dict(winners), "entries": dict(entrants)}

    def get_operation_statistics(self) -> dict[str, Any]:
        winners = Counter(
            item.get("winner_operation")
            for item in self.competitions
            if item.get("winner_operation")
        )
        return {"winning_operations": dict(winners)}

    def get_program_statistics(self) -> dict[str, Any]:
        signatures = Counter(
            item.get("winner_program_signature")
            for item in self.competitions
            if item.get("winner_program_signature")
        )
        return {"winning_program_signatures": dict(signatures)}


arena_memory = ArenaMemory()

__all__ = ["ArenaMemory", "arena_memory"]
