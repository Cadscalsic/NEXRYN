"""Adaptive reuse report construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReuseStatistics:
    experience_count: int = 0
    retrieval_attempts: int = 0
    retrieval_successes: int = 0
    strategy_hits: int = 0
    program_hits: int = 0
    context_hits: int = 0
    truth_hits: int = 0
    dependency_hits: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    experience_similarity: float = 0.0
    adaptation_operations: list[str] = field(default_factory=list)
    reuse_failures: list[dict[str, Any]] = field(default_factory=list)
    estimated_runtime_saved: float = 0.0
    estimated_compute_saved: float = 0.0
    knowledge_growth: dict[str, Any] = field(default_factory=dict)

    def report(self) -> dict[str, Any]:
        attempts = max(self.retrieval_attempts, 1)
        reuse_events = (
            self.strategy_hits
            + self.program_hits
            + self.context_hits
            + self.truth_hits
            + self.dependency_hits
        )
        self.cache_hits = max(self.cache_hits, reuse_events)
        self.cache_misses = max(self.cache_misses, 0 if reuse_events else 1)
        total = self.cache_hits + self.cache_misses
        return {
            "system": "adaptive_reuse_layer",
            "ADAPTIVE_REUSE_REPORT": True,
            "experience_count": self.experience_count,
            "retrieval_attempts": self.retrieval_attempts,
            "retrieval_successes": self.retrieval_successes,
            "strategy_hits": self.strategy_hits,
            "program_hits": self.program_hits,
            "context_hits": self.context_hits,
            "truth_hits": self.truth_hits,
            "dependency_hits": self.dependency_hits,
            "dependency_snapshot_hits": self.dependency_hits,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hits / max(total, 1), 4),
            "experience_similarity": self.experience_similarity,
            "adaptation_operations": sorted(set(self.adaptation_operations)),
            "reuse_success_rate": round(self.retrieval_successes / attempts, 4),
            "reuse_failures": self.reuse_failures[-10:],
            "estimated_runtime_saved": round(self.estimated_runtime_saved, 4),
            "estimated_compute_saved": round(self.estimated_compute_saved, 4),
            "knowledge_growth": self.knowledge_growth,
        }
