"""Reporter for knowledge reuse, saturation, and commit outcomes."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.knowledge_optimization.concept_commit_engine import concept_commit_engine
from runtime.knowledge_optimization.memory_confidence_tracker import memory_confidence_tracker
from runtime.knowledge_optimization.strategy_reuse_engine import strategy_reuse_engine


class KnowledgeOptimizationReporter:
    def __init__(self) -> None:
        self.reports: list[dict[str, Any]] = []

    def build_report(
        self,
        metrics: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        commits = concept_commit_engine.commits
        concepts_promoted = sum(1 for item in commits if item.get("promoted") is True)
        concepts_quarantined = sum(1 for item in commits if item.get("action") == "QUARANTINE")
        strategy_hits = int(data.get("strategy_hits", strategy_reuse_engine.strategy_hits))
        strategy_misses = int(data.get("strategy_misses", strategy_reuse_engine.strategy_misses))
        total_strategy = strategy_hits + strategy_misses
        reuse_rate = float(data.get("reuse_rate", strategy_hits / max(1, total_strategy)))
        report = {
            "KNOWLEDGE_OPTIMIZATION_REPORT": {
                "concepts_promoted": concepts_promoted,
                "concepts_quarantined": concepts_quarantined,
                "average_contradiction_score": float(data.get("average_contradiction_score", data.get("contradiction_score", 0.0))),
                "reuse_rate": reuse_rate,
                "strategy_hits": strategy_hits,
                "strategy_misses": strategy_misses,
                "evidence_collection_time": min(3.0, float(data.get("evidence_collection_time", 0.0) or 0.0)),
                "plateau_terminations": int(data.get("plateau_terminations", 0)),
                "memory_confidence_average": memory_confidence_tracker.average_confidence(),
                "thinking_avoidance_rate": float(data.get("thinking_avoidance_rate", reuse_rate)),
            }
        }
        self.reports.append(report)
        return report

    def latest(self) -> dict[str, Any]:
        return self.reports[-1] if self.reports else self.build_report()

    def reset(self) -> None:
        self.reports.clear()


knowledge_optimization_reporter = KnowledgeOptimizationReporter()


__all__ = [
    "KnowledgeOptimizationReporter",
    "knowledge_optimization_reporter",
]
