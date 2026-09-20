"""Counterfactual memory for episodes, assumptions, and residual patterns."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
from typing import Mapping


class CounterfactualMemory:
    system_name = "counterfactual_memory"

    def __init__(self):
        self.episodes: list[dict] = []

    def record_counterfactual_episode(self, episode: Mapping) -> dict:
        self.episodes.append(deepcopy(dict(episode)))
        return {"system": self.system_name, "counterfactual_memory_operational": True, "episode_count": len(self.episodes)}

    def retrieve_similar_counterfactuals(self, task_signature: str | None = None, limit: int = 5) -> list[dict]:
        rows = self.episodes if not task_signature else [row for row in self.episodes if row.get("task_signature") == task_signature]
        return deepcopy(rows[-limit:])

    def get_falsified_assumptions(self) -> list:
        return [item for ep in self.episodes for item in ep.get("failed_assumptions", []) or []]

    def get_stable_assumptions(self) -> list:
        return [item for ep in self.episodes for item in ep.get("surviving_assumptions", []) or []]

    def get_residual_revision_patterns(self) -> dict:
        return dict(Counter(item for ep in self.episodes for item in ep.get("revision_operations", []) or []))

    def get_counterfactual_statistics(self) -> dict:
        return {"episodes": len(self.episodes), "tested_counterfactuals": sum(ep.get("generated_counterfactual_count", 0) for ep in self.episodes)}


counterfactual_memory = CounterfactualMemory()

__all__ = ["CounterfactualMemory", "counterfactual_memory"]
