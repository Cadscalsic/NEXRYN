"""Retrieve and adapt strategies from similar experiences."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.adaptive_reuse.experience_index import ExperienceIndex
from runtime.adaptive_reuse.strategy_adapter import StrategyAdapter
from runtime.adaptive_reuse.strategy_memory import StrategyMemory
from runtime.adaptive_reuse.strategy_ranker import RankedExperience, StrategyRanker


class StrategyRetriever:
    def __init__(
        self,
        experience_index: ExperienceIndex | None = None,
        strategy_memory: StrategyMemory | None = None,
        ranker: StrategyRanker | None = None,
        adapter: StrategyAdapter | None = None,
    ) -> None:
        self.experience_index = experience_index or ExperienceIndex()
        self.strategy_memory = strategy_memory or StrategyMemory()
        self.ranker = ranker or StrategyRanker()
        self.adapter = adapter or StrategyAdapter()

    def retrieve(
        self,
        runtime_context: Mapping[str, Any] | None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        query = self.experience_index.query_signature(runtime_context)
        experiences = self.experience_index.load()
        ranked = self.ranker.rank(query, experiences, top_k=top_k)
        adapted = []
        operations = []
        for item in ranked:
            strategy = _strategy_from_experience(item)
            if not strategy:
                continue
            adapted_strategy = self.adapter.adapt(strategy, runtime_context)
            adapted_strategy["source_experience_id"] = item.experience.experience_id
            adapted_strategy["experience_similarity"] = item.score
            adapted.append(adapted_strategy)
            operations.extend(adapted_strategy.get("adaptation_operations", []))

        if not adapted:
            adapted.extend(self._fallback_strategies(runtime_context, top_k))

        return {
            "retrieval_attempted": True,
            "retrieval_success": bool(adapted),
            "ranked_experiences": [
                {
                    **item.experience.as_dict(),
                    "experience_similarity": item.score,
                    "similarity_components": item.components,
                }
                for item in ranked
            ],
            "experience_similarity": (
                round(sum(item.score for item in ranked) / len(ranked), 4)
                if ranked else 0.0
            ),
            "reused_strategies": adapted,
            "adaptation_operations": sorted(set(operations)),
        }

    def _fallback_strategies(
        self,
        runtime_context: Mapping[str, Any] | None,
        top_k: int,
    ) -> list[dict[str, Any]]:
        query_text = str(runtime_context or {}).lower()
        strategies = []
        for strategy in self.strategy_memory.load():
            concept = str(strategy.get("concept") or strategy.get("type") or "").lower()
            if concept and concept not in query_text:
                continue
            adapted = self.adapter.adapt(strategy, runtime_context)
            adapted["experience_similarity"] = float(strategy.get("confidence", 0.0) or 0.0)
            strategies.append(adapted)
            if len(strategies) >= top_k:
                break
        return strategies


def _strategy_from_experience(item: RankedExperience) -> dict[str, Any]:
    payload = item.experience.payload
    strategy = payload.get("winner_hypothesis") or payload.get("best_evolved_strategy") or {}
    return dict(strategy) if isinstance(strategy, Mapping) else {}
